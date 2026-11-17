#!/usr/bin/env python3
"""Global Antigravity profile pool, exclusive lease management, and exhaustion reporting."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import errno
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
from types import ModuleType
from typing import TYPE_CHECKING, Any
import uuid

if TYPE_CHECKING:
    from persona_config import PersonaBinding

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _load_module_by_path(name: str, path: Path) -> ModuleType:
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    if not path.is_file():
        raise RuntimeError(f"Required module file not found: {path}")
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to create module spec for {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


_pc = _load_module_by_path("persona_config", _SCRIPTS_DIR / "persona_config.py")

POOL_SCHEMA_VERSION: int = 1
DEFAULT_LEASE_TTL_SECONDS: int = 180
DEFAULT_HEARTBEAT_SECONDS: int = 30
DEFAULT_EXHAUSTED_RECHECK_SECONDS: int = 600
DEFAULT_MAX_CONCURRENT: int = 2
QUOTA_CACHE_TTL_SECONDS: int = 120

PROFILE_NAME_RE: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9_-]+$")
_ALLOWED_CONFIG_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "pool",
        "lease_ttl_seconds",
        "heartbeat_seconds",
        "exhausted_recheck_seconds",
        "agy_extra_args",
    }
)
_ALLOWED_POOL_ENTRY_KEYS: frozenset[str] = frozenset(
    {"profile", "priority", "max_concurrent"}
)
_ALLOWED_ROLES: frozenset[str] = frozenset({"orchestrator", "runner"})
_NON_AGY_SWITCH_ORDER: tuple[str, ...] = ("codex", "kiro", "claude")
_QUOTA_WINDOW_KEYS: tuple[str, ...] = ("gemini5h", "geminiWeekly", "argonWeekly")
DEFAULT_QUOTA_THRESHOLDS: dict[str, float] = {
    "5h_min_fraction": 0.15,
    "7d_min_fraction": 0.02,
    "agy_argon_min_fraction": 0.10,
}


class AgyPoolError(ValueError):
    """Raised when agy pool configuration or lease operations fail validation."""


@dataclass(frozen=True)
class QuotaVerdict:
    """Result of evaluating an agy quota payload against configured thresholds."""

    sufficient: bool
    failing: list[dict[str, Any]]


@dataclass(frozen=True)
class Acquisition:
    """Result of acquiring (or failing to acquire) an agy profile lease."""

    profile: str | None
    via_ag_run: bool
    owner_id: str
    skipped: dict[str, str]
    reason: str | None


def profiles_config_path(real_home: Path | str | None = None) -> Path:
    """Return path to global agy_profiles.json under REAL_HOME."""
    return _pc.get_real_home(real_home) / ".d3nexus" / "agy_profiles.json"


def leases_file_path(real_home: Path | str | None = None) -> Path:
    """Return path to global agy_profile_leases.json under REAL_HOME."""
    return _pc.get_real_home(real_home) / ".d3nexus" / "agy_profile_leases.json"


def detect_host_profile(env: Mapping[str, str] | None = None) -> str | None:
    """Return the Antigravity profile hosting the current process, or None."""
    env_map = os.environ if env is None else env
    agy_profile = str(env_map.get("AGY_PROFILE", "") or "").strip()
    if agy_profile:
        return agy_profile
    home_val = str(env_map.get("HOME", "") or "")
    if "/antigravity_homes/" in home_val:
        tail = home_val.split("/antigravity_homes/", 1)[1]
        candidate = tail.split("/", 1)[0].strip()
        if candidate:
            return candidate
    return None


def _coerce_now(now: datetime | None = None) -> datetime:
    current = now if now is not None else datetime.now(timezone.utc)
    if current.tzinfo is None:
        return current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc)


def _format_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_utc(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _normalize_iso_or_raw(raw: Any) -> str:
    parsed = _parse_utc(raw)
    if parsed is not None:
        return _format_utc(parsed)
    return str(raw) if raw is not None else "unknown"


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AgyPoolError(f"Failed to read '{path}': {exc}") from exc
    if not isinstance(raw, dict):
        raise AgyPoolError(f"Configuration '{path}' must be a JSON object")
    return raw


def _with_file_lock(
    target_path: Path,
    callback: Callable[[], Any],
) -> Any:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = target_path.with_name(f"{target_path.name}.lock")
    with open(lock_path, "a", encoding="utf-8") as lock_fh:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        try:
            return callback()
        finally:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)


def _validate_positive_number(value: Any, key: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise AgyPoolError(
            f"Invalid '{key}' value '{value}'; expected a positive number"
        )
    return float(value)


def _validate_positive_int(value: Any, key: str) -> int:
    if type(value) is not int or value < 1:
        raise AgyPoolError(f"Invalid '{key}' value '{value}'; expected integer >= 1")
    return value


def validate_profile_name(name: Any) -> str:
    """Validate profile name format without touching filesystem."""
    if not isinstance(name, str) or not PROFILE_NAME_RE.fullmatch(name):
        raise AgyPoolError(
            f"Invalid profile name '{name}'; expected characters matching ^[a-zA-Z0-9_-]+$"
        )
    return name


def validate_profile_dir(name: str, real_home: Path | str | None = None) -> Path:
    """Verify profile exists as a real directory (not symlink) under antigravity_homes."""
    validate_profile_name(name)
    profile_dir = _pc.get_real_home(real_home) / "antigravity_homes" / name
    if profile_dir.is_symlink():
        raise AgyPoolError(
            f"Profile '{name}' directory '{profile_dir}' must not be a symlink"
        )
    if not profile_dir.is_dir():
        raise AgyPoolError(f"Profile '{name}' directory does not exist: {profile_dir}")
    return profile_dir


def _default_pool_config() -> dict[str, Any]:
    return {
        "schema_version": POOL_SCHEMA_VERSION,
        "pool": [],
        "lease_ttl_seconds": DEFAULT_LEASE_TTL_SECONDS,
        "heartbeat_seconds": DEFAULT_HEARTBEAT_SECONDS,
        "exhausted_recheck_seconds": DEFAULT_EXHAUSTED_RECHECK_SECONDS,
        "agy_extra_args": [],
    }


def validate_pool_config(raw: Any) -> dict[str, Any]:
    """Validate and normalize an agy_profiles.json mapping."""
    if not isinstance(raw, Mapping):
        raise AgyPoolError(
            f"Invalid agy_profiles.json root '{raw}'; expected JSON object"
        )

    unknown_top = set(raw) - _ALLOWED_CONFIG_KEYS
    if unknown_top:
        bad = min(unknown_top)
        raise AgyPoolError(f"Unknown key '{bad}' in agy_profiles.json")

    sv = raw.get("schema_version")
    if type(sv) is not int or sv != POOL_SCHEMA_VERSION:
        raise AgyPoolError(
            f"Unsupported schema_version '{sv}' in agy_profiles.json; expected {POOL_SCHEMA_VERSION}"
        )

    lease_ttl = _validate_positive_number(
        raw.get("lease_ttl_seconds", DEFAULT_LEASE_TTL_SECONDS),
        "lease_ttl_seconds",
    )
    heartbeat_sec = _validate_positive_number(
        raw.get("heartbeat_seconds", DEFAULT_HEARTBEAT_SECONDS),
        "heartbeat_seconds",
    )
    recheck_sec = _validate_positive_number(
        raw.get("exhausted_recheck_seconds", DEFAULT_EXHAUSTED_RECHECK_SECONDS),
        "exhausted_recheck_seconds",
    )

    extra_args_raw = raw.get("agy_extra_args", [])
    if not isinstance(extra_args_raw, list) or any(
        not isinstance(item, str) for item in extra_args_raw
    ):
        raise AgyPoolError(
            f"Invalid 'agy_extra_args' value '{extra_args_raw}'; expected list of strings"
        )

    pool_raw = raw.get("pool", [])
    if not isinstance(pool_raw, list):
        raise AgyPoolError(f"Invalid 'pool' value '{pool_raw}'; expected list")

    seen_profiles: set[str] = set()
    normalized_pool: list[dict[str, Any]] = []
    for entry in pool_raw:
        if not isinstance(entry, Mapping):
            raise AgyPoolError(f"Invalid pool entry '{entry}'; expected object")
        unknown_entry = set(entry) - _ALLOWED_POOL_ENTRY_KEYS
        if unknown_entry:
            bad = min(unknown_entry)
            raise AgyPoolError(f"Unknown key '{bad}' in pool entry")
        profile_name = validate_profile_name(entry.get("profile"))
        if profile_name in seen_profiles:
            raise AgyPoolError(f"Duplicate profile '{profile_name}' in pool")
        seen_profiles.add(profile_name)
        priority = _validate_positive_int(entry.get("priority"), "priority")
        max_conc = _validate_positive_int(
            entry.get("max_concurrent", DEFAULT_MAX_CONCURRENT),
            "max_concurrent",
        )
        normalized_pool.append(
            {
                "profile": profile_name,
                "priority": priority,
                "max_concurrent": max_conc,
            }
        )

    normalized_pool.sort(key=lambda item: (int(item["priority"]), str(item["profile"])))
    return {
        "schema_version": POOL_SCHEMA_VERSION,
        "pool": normalized_pool,
        "lease_ttl_seconds": int(lease_ttl) if lease_ttl.is_integer() else lease_ttl,
        "heartbeat_seconds": int(heartbeat_sec)
        if heartbeat_sec.is_integer()
        else heartbeat_sec,
        "exhausted_recheck_seconds": int(recheck_sec)
        if recheck_sec.is_integer()
        else recheck_sec,
        "agy_extra_args": list(extra_args_raw),
    }


def load_pool_config(real_home: Path | str | None = None) -> dict[str, Any]:
    """Load and validate agy_profiles.json, returning empty defaults when absent."""
    path = profiles_config_path(real_home)
    raw = _read_json_object(path)
    if raw is None:
        return _default_pool_config()
    return validate_pool_config(raw)


def _empty_profile_record() -> dict[str, Any]:
    return {
        "leases": [],
        "exhausted_until": None,
        "exhausted_checked_at": None,
        "exhausted_reason": None,
        "quota": None,
    }


def _load_or_init_leases_doc(path: Path) -> dict[str, Any]:
    raw = _read_json_object(path)
    if raw is None:
        return {"schema_version": POOL_SCHEMA_VERSION, "profiles": {}}
    sv = raw.get("schema_version")
    if type(sv) is not int or sv != POOL_SCHEMA_VERSION:
        raise AgyPoolError(
            f"Unsupported schema_version '{sv}' in '{path}'; expected {POOL_SCHEMA_VERSION}"
        )
    profiles = raw.get("profiles", {})
    if not isinstance(profiles, dict):
        raise AgyPoolError(f"Invalid 'profiles' mapping in '{path}'")
    normalized_profiles: dict[str, dict[str, Any]] = {}
    for prof_name, rec in profiles.items():
        if not isinstance(rec, Mapping):
            continue
        leases = rec.get("leases", [])
        normalized_profiles[str(prof_name)] = {
            "leases": list(leases) if isinstance(leases, list) else [],
            "exhausted_until": rec.get("exhausted_until"),
            "exhausted_checked_at": rec.get("exhausted_checked_at"),
            "exhausted_reason": rec.get("exhausted_reason"),
            "quota": dict(rec["quota"])
            if isinstance(rec.get("quota"), Mapping)
            else None,
        }
    return {"schema_version": POOL_SCHEMA_VERSION, "profiles": normalized_profiles}


def _ensure_profile_record(leases_doc: dict[str, Any], profile: str) -> dict[str, Any]:
    profiles: dict[str, dict[str, Any]] = leases_doc.setdefault("profiles", {})
    rec = profiles.get(profile)
    if not isinstance(rec, dict):
        rec = _empty_profile_record()
        profiles[profile] = rec
    else:
        rec.setdefault("leases", [])
        rec.setdefault("exhausted_until", None)
        rec.setdefault("exhausted_checked_at", None)
        rec.setdefault("exhausted_reason", None)
        rec.setdefault("quota", None)
    return rec


def _pid_alive(pid: Any) -> bool:
    if type(pid) is not int or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as exc:
        return exc.errno != errno.ESRCH
    return True


def _is_lease_stale(
    lease: Mapping[str, Any],
    *,
    now: datetime,
    lease_ttl_seconds: float,
    current_host: str,
) -> bool:
    hb_dt = _parse_utc(lease.get("heartbeat_at"))
    if hb_dt is None:
        return True
    if (now - hb_dt).total_seconds() > lease_ttl_seconds:
        return True
    return str(lease.get("host", "")) == current_host and not _pid_alive(
        lease.get("pid")
    )


def _purge_stale_leases(
    leases_doc: dict[str, Any],
    *,
    now: datetime,
    lease_ttl_seconds: float,
    current_host: str,
) -> bool:
    changed = False
    profiles = leases_doc.get("profiles", {})
    if not isinstance(profiles, dict):
        return False
    for rec in profiles.values():
        leases = rec.get("leases", [])
        if not isinstance(leases, list) or not leases:
            continue
        live = [
            lease
            for lease in leases
            if isinstance(lease, dict)
            and not _is_lease_stale(
                lease,
                now=now,
                lease_ttl_seconds=lease_ttl_seconds,
                current_host=current_host,
            )
        ]
        if len(live) != len(leases):
            rec["leases"] = live
            changed = True
    return changed


def _has_capacity(
    leases: Sequence[Mapping[str, Any]],
    *,
    is_host_profile: bool,
    max_concurrent: int,
) -> bool:
    if is_host_profile:
        if any(lease.get("launch") == "ag_run" for lease in leases):
            return False
        direct_count = sum(1 for lease in leases if lease.get("launch") == "direct")
        return direct_count < max_concurrent
    return len(leases) == 0


def _sanitize_quota_payload(
    payload: Mapping[str, Any] | None,
    *,
    fetched_at: datetime | None = None,
) -> dict[str, Any] | None:
    if not isinstance(payload, Mapping):
        return None
    clean: dict[str, Any] = {}
    if "status" in payload and payload["status"] is not None:
        clean["status"] = str(payload["status"])
    for key in _QUOTA_WINDOW_KEYS:
        pool_raw = payload.get(key)
        if not isinstance(pool_raw, Mapping):
            continue
        pool_clean: dict[str, Any] = {}
        if "fraction" in pool_raw and pool_raw["fraction"] is not None:
            pool_clean["fraction"] = float(pool_raw["fraction"])
        if "resetTime" in pool_raw and pool_raw["resetTime"] is not None:
            pool_clean["resetTime"] = str(pool_raw["resetTime"])
        if pool_clean:
            clean[key] = pool_clean
    if fetched_at is not None:
        clean["fetched_at"] = _format_utc(fetched_at)
    return clean if clean else None


def evaluate_agy_quota(
    payload: Mapping[str, Any],
    quota_pool: str,
    thresholds: Mapping[str, float],
) -> QuotaVerdict:
    """Judge an agy quota payload for gemini5h (both 5h and weekly windows) or argonWeekly."""
    if not payload:
        return QuotaVerdict(sufficient=True, failing=[])

    failing: list[dict[str, Any]] = []
    if quota_pool == "argonWeekly":
        argon = payload.get("argonWeekly")
        if isinstance(argon, Mapping) and argon.get("fraction") is not None:
            frac = float(argon["fraction"])
            thresh = float(thresholds["agy_argon_min_fraction"])
            if frac < thresh:
                failing.append(
                    {
                        "window": "argonWeekly",
                        "fraction": frac,
                        "threshold": thresh,
                        "reset_at": argon.get("resetTime"),
                    }
                )
        return QuotaVerdict(sufficient=not failing, failing=failing)

    g5h = payload.get("gemini5h")
    if isinstance(g5h, Mapping) and g5h.get("fraction") is not None:
        frac_5h = float(g5h["fraction"])
        thresh_5h = float(thresholds["5h_min_fraction"])
        if frac_5h < thresh_5h:
            failing.append(
                {
                    "window": "5h",
                    "fraction": frac_5h,
                    "threshold": thresh_5h,
                    "reset_at": g5h.get("resetTime"),
                }
            )

    g7d = payload.get("geminiWeekly")
    if isinstance(g7d, Mapping) and g7d.get("fraction") is not None:
        frac_7d = float(g7d["fraction"])
        thresh_7d = float(thresholds["7d_min_fraction"])
        if frac_7d <= thresh_7d:
            failing.append(
                {
                    "window": "weekly",
                    "fraction": frac_7d,
                    "threshold": thresh_7d,
                    "reset_at": g7d.get("resetTime"),
                }
            )

    return QuotaVerdict(sufficient=not failing, failing=failing)


def default_fetcher(profile: str) -> dict[str, Any]:
    """Load scripts/agy_quota.py by path and return sanitized dashboard-shaped quota."""
    quota_path = _SCRIPTS_DIR / "agy_quota.py"
    if not quota_path.is_file():
        return {}
    try:
        mod = _load_module_by_path("agy_quota", quota_path)
        raw = mod.fetch_quota_for_profile(profile)
        formatted = mod.format_profile_for_dashboard(profile, raw)
    except Exception:
        return {}
    return _sanitize_quota_payload(formatted) or {}


def default_resident_probe(profile: str) -> bool:
    """Return True when pgrep finds a running process for antigravity_homes/<profile>/."""
    try:
        proc = subprocess.run(
            ["pgrep", "-f", f"antigravity_homes/{profile}/"],
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode == 0
    except OSError:
        return False


def _normalize_owner(
    owner: Mapping[str, Any] | str,
    *,
    launch: str,
    now: datetime,
) -> dict[str, Any]:
    if isinstance(owner, str):
        owner_id = owner.strip() or uuid.uuid4().hex
        return {
            "owner_id": owner_id,
            "repo": "",
            "epic": owner_id,
            "task": "",
            "slot": None,
            "role": "orchestrator",
            "launch": launch,
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "acquired_at": _format_utc(now),
            "heartbeat_at": _format_utc(now),
        }

    role = str(owner.get("role") or "orchestrator")
    if role not in _ALLOWED_ROLES:
        raise AgyPoolError(
            f"Invalid lease role '{role}'; expected 'orchestrator' or 'runner'"
        )
    owner_id = str(owner.get("owner_id") or "").strip() or uuid.uuid4().hex
    raw_pid = owner.get("pid")
    pid = (
        int(raw_pid)
        if isinstance(raw_pid, int) and not isinstance(raw_pid, bool)
        else os.getpid()
    )
    host = str(owner.get("host") or "").strip() or socket.gethostname()
    slot_val = owner.get("slot")
    ts = _format_utc(now)
    return {
        "owner_id": owner_id,
        "repo": str(owner.get("repo") or ""),
        "epic": str(owner.get("epic") or ""),
        "task": str(owner.get("task") or ""),
        "slot": slot_val,
        "role": role,
        "launch": launch,
        "pid": pid,
        "host": host,
        "acquired_at": ts,
        "heartbeat_at": ts,
    }


def _is_exhausted_skip(
    rec: Mapping[str, Any],
    *,
    now: datetime,
    recheck_seconds: float,
) -> tuple[bool, bool]:
    """Return (should_skip_as_exhausted, recheck_interval_elapsed)."""
    until_dt = _parse_utc(rec.get("exhausted_until"))
    if until_dt is None or until_dt <= now:
        return False, False
    checked_dt = _parse_utc(rec.get("exhausted_checked_at"))
    if checked_dt is None:
        return True, False
    if (now - checked_dt).total_seconds() < recheck_seconds:
        return True, False
    return False, True


def _failing_reason_and_reset(
    failing: Sequence[Mapping[str, Any]],
    *,
    now: datetime,
    recheck_seconds: float,
) -> tuple[str, str]:
    windows = {str(item.get("window")) for item in failing}
    has_5h = "5h" in windows
    has_weekly = "weekly" in windows or "argonWeekly" in windows
    if has_5h and has_weekly:
        reason = "5h+weekly"
    elif has_weekly:
        reason = "weekly"
    else:
        reason = "5h"

    reset_dts = [
        parsed
        for item in failing
        if (parsed := _parse_utc(item.get("reset_at"))) is not None
    ]
    if reset_dts:
        until_dt = max(reset_dts)
    else:
        until_dt = now + timedelta(seconds=recheck_seconds)
    return reason, _format_utc(until_dt)


def _pool_failure_reason(
    pool: Sequence[Mapping[str, Any]], skipped: Mapping[str, str]
) -> str:
    if not pool:
        return "pool_empty"
    if any(reason in ("leased", "resident_process") for reason in skipped.values()):
        return "pool_busy"
    return "pool_exhausted"


def _claim_tentative_lease(
    leases_path: Path,
    *,
    profile: str,
    lease_entry: dict[str, Any],
    is_host_profile: bool,
    max_concurrent: int,
    recheck_seconds: float,
    lease_ttl_seconds: float,
    current_host: str,
    now: datetime,
    dry_run: bool,
) -> tuple[str | None, dict[str, Any] | None, bool]:
    """Purge stale leases and tentatively claim `profile` under lock; returns (skip_reason, cached_quota, recheck_due)."""

    def _op() -> tuple[str | None, dict[str, Any] | None, bool]:
        doc = _load_or_init_leases_doc(leases_path)
        purged = _purge_stale_leases(
            doc,
            now=now,
            lease_ttl_seconds=lease_ttl_seconds,
            current_host=current_host,
        )
        rec = _ensure_profile_record(doc, profile)
        skip_exhausted, recheck_due = _is_exhausted_skip(
            rec,
            now=now,
            recheck_seconds=recheck_seconds,
        )
        if skip_exhausted:
            if purged and not dry_run:
                _pc._atomic_write_json(leases_path, doc)
            return "exhausted", None, False
        if not _has_capacity(
            rec["leases"],
            is_host_profile=is_host_profile,
            max_concurrent=max_concurrent,
        ):
            if purged and not dry_run:
                _pc._atomic_write_json(leases_path, doc)
            return "leased", None, False

        cached_quota = (
            dict(rec["quota"]) if isinstance(rec.get("quota"), Mapping) else None
        )
        if not dry_run:
            rec["leases"].append(lease_entry)
            _pc._atomic_write_json(leases_path, doc)
        return None, cached_quota, recheck_due

    return _with_file_lock(leases_path, _op)


def _finalize_claim(
    leases_path: Path,
    *,
    profile: str,
    owner_id: str,
    passed: bool,
    sanitized_quota: dict[str, Any] | None,
    exhausted_until: str | None,
    exhausted_reason: str | None,
    now: datetime,
) -> None:
    def _op() -> None:
        doc = _load_or_init_leases_doc(leases_path)
        rec = _ensure_profile_record(doc, profile)
        if passed:
            rec["exhausted_until"] = None
            rec["exhausted_checked_at"] = None
            rec["exhausted_reason"] = None
        else:
            rec["leases"] = [
                lease
                for lease in rec["leases"]
                if not (
                    isinstance(lease, Mapping) and lease.get("owner_id") == owner_id
                )
            ]
            rec["exhausted_until"] = exhausted_until
            rec["exhausted_checked_at"] = _format_utc(now)
            rec["exhausted_reason"] = exhausted_reason
        if sanitized_quota is not None:
            rec["quota"] = sanitized_quota
        _pc._atomic_write_json(leases_path, doc)

    _with_file_lock(leases_path, _op)


def _snapshot_for_acquire(
    leases_path: Path,
    *,
    now: datetime,
    lease_ttl_seconds: float,
    current_host: str,
    dry_run: bool,
) -> dict[str, Any]:
    def _op() -> dict[str, Any]:
        doc = _load_or_init_leases_doc(leases_path)
        purged = _purge_stale_leases(
            doc,
            now=now,
            lease_ttl_seconds=lease_ttl_seconds,
            current_host=current_host,
        )
        if purged and not dry_run:
            _pc._atomic_write_json(leases_path, doc)
        return doc

    return _with_file_lock(leases_path, _op)


def _get_quota_for_candidate(
    profile: str,
    *,
    cached_quota: dict[str, Any] | None,
    recheck_due: bool,
    fetcher: Callable[[str], Mapping[str, Any]],
    now: datetime,
) -> tuple[Mapping[str, Any], bool]:
    if not recheck_due and isinstance(cached_quota, Mapping):
        fetched_dt = _parse_utc(cached_quota.get("fetched_at"))
        if (
            fetched_dt is not None
            and (now - fetched_dt).total_seconds() < QUOTA_CACHE_TTL_SECONDS
        ):
            return cached_quota, True
    try:
        fresh = fetcher(profile)
        return (fresh if isinstance(fresh, Mapping) else {}), False
    except Exception:
        return {}, False


def _preferred_first(
    pool: list[dict[str, Any]],
    preferred_profile: str | None,
) -> list[dict[str, Any]]:
    """Move the preferred pool entry to the front; ignore a name that is not in the pool."""
    if preferred_profile is None:
        return pool
    preferred = [entry for entry in pool if entry["profile"] == preferred_profile]
    others = [entry for entry in pool if entry["profile"] != preferred_profile]
    return preferred + others


def _attempt_acquire_once(
    owner: Mapping[str, Any] | str,
    *,
    cfg: Mapping[str, Any],
    leases_path: Path,
    host_profile: str | None,
    quota_pool: str,
    thresholds: Mapping[str, float],
    fetcher: Callable[[str], Mapping[str, Any]],
    resident_probe: Callable[[str], bool],
    now: datetime,
    current_host: str,
    owner_id: str,
    dry_run: bool,
    preferred_profile: str | None = None,
) -> tuple[Acquisition | None, dict[str, str]]:
    pool: list[dict[str, Any]] = _preferred_first(list(cfg["pool"]), preferred_profile)
    lease_ttl = float(cfg["lease_ttl_seconds"])
    recheck_sec = float(cfg["exhausted_recheck_seconds"])
    skipped: dict[str, str] = {}

    snapshot = _snapshot_for_acquire(
        leases_path,
        now=now,
        lease_ttl_seconds=lease_ttl,
        current_host=current_host,
        dry_run=dry_run,
    )
    snap_profiles = snapshot.get("profiles", {})

    for entry in pool:
        profile = str(entry["profile"])
        max_conc = int(entry["max_concurrent"])
        is_host = host_profile is not None and profile == host_profile
        via_ag_run = not is_host
        launch = "direct" if is_host else "ag_run"

        rec = snap_profiles.get(profile, _empty_profile_record())
        skip_exhausted, _ = _is_exhausted_skip(
            rec, now=now, recheck_seconds=recheck_sec
        )
        if skip_exhausted:
            skipped[profile] = "exhausted"
            continue
        if not _has_capacity(
            rec.get("leases", []), is_host_profile=is_host, max_concurrent=max_conc
        ):
            skipped[profile] = "leased"
            continue
        if not is_host and resident_probe(profile):
            skipped[profile] = "resident_process"
            continue

        owner_seed: Mapping[str, Any] | str
        if isinstance(owner, Mapping):
            owner_dict = dict(owner)
            owner_dict["owner_id"] = owner_id
            owner_seed = owner_dict
        else:
            owner_seed = owner_id
        lease_entry = _normalize_owner(owner_seed, launch=launch, now=now)

        claim_skip, cached_quota, recheck_due = _claim_tentative_lease(
            leases_path,
            profile=profile,
            lease_entry=lease_entry,
            is_host_profile=is_host,
            max_concurrent=max_conc,
            recheck_seconds=recheck_sec,
            lease_ttl_seconds=lease_ttl,
            current_host=current_host,
            now=now,
            dry_run=dry_run,
        )
        if claim_skip is not None:
            skipped[profile] = claim_skip
            continue

        payload, from_cache = _get_quota_for_candidate(
            profile,
            cached_quota=cached_quota,
            recheck_due=recheck_due,
            fetcher=fetcher,
            now=now,
        )
        sanitized = (
            _sanitize_quota_payload(payload, fetched_at=now)
            if not from_cache and payload
            else None
        )

        raw_status = payload.get("status") if isinstance(payload, Mapping) else None
        if isinstance(raw_status, str) and raw_status and raw_status != "ACTIVE":
            status_tag = f"status:{raw_status}"
            skipped[profile] = status_tag
            if not dry_run:
                _finalize_claim(
                    leases_path,
                    profile=profile,
                    owner_id=owner_id,
                    passed=False,
                    sanitized_quota=sanitized,
                    exhausted_until=_format_utc(now + timedelta(seconds=recheck_sec)),
                    exhausted_reason=status_tag,
                    now=now,
                )
            continue

        verdict = evaluate_agy_quota(payload, quota_pool, thresholds)
        if not verdict.sufficient:
            ex_reason, ex_until = _failing_reason_and_reset(
                verdict.failing,
                now=now,
                recheck_seconds=recheck_sec,
            )
            skipped[profile] = "quota"
            if not dry_run:
                _finalize_claim(
                    leases_path,
                    profile=profile,
                    owner_id=owner_id,
                    passed=False,
                    sanitized_quota=sanitized,
                    exhausted_until=ex_until,
                    exhausted_reason=ex_reason,
                    now=now,
                )
            continue

        if not dry_run:
            _finalize_claim(
                leases_path,
                profile=profile,
                owner_id=owner_id,
                passed=True,
                sanitized_quota=sanitized,
                exhausted_until=None,
                exhausted_reason=None,
                now=now,
            )
        return (
            Acquisition(
                profile=profile,
                via_ag_run=via_ag_run,
                owner_id=owner_id,
                skipped=skipped,
                reason=None,
            ),
            skipped,
        )

    return None, skipped


def acquire(
    owner: Mapping[str, Any] | str,
    *,
    real_home: Path | str | None = None,
    host_profile: str | None = None,
    quota_pool: str = "gemini5h",
    thresholds: Mapping[str, float] | None = None,
    fetcher: Callable[[str], Mapping[str, Any]] | None = None,
    resident_probe: Callable[[str], bool] | None = None,
    wait_seconds: float = 0,
    poll_seconds: float = 15,
    now: datetime | None = None,
    dry_run: bool = False,
    preferred_profile: str | None = None,
) -> Acquisition:
    """Acquire the highest-priority usable agy profile lease, or return skip details.

    A `preferred_profile` that names a pool entry is tried first and the others follow in
    (priority, profile) order; an unusable preferred profile is skipped with its normal reason.
    """
    owner_id = (
        str(owner.get("owner_id") or "").strip()
        if isinstance(owner, Mapping)
        else owner.strip()
    ) or uuid.uuid4().hex
    cfg = load_pool_config(real_home=real_home)
    if not cfg["pool"]:
        return Acquisition(
            profile=None,
            via_ag_run=False,
            owner_id=owner_id,
            skipped={},
            reason="pool_empty",
        )

    active_thresholds = (
        thresholds if thresholds is not None else DEFAULT_QUOTA_THRESHOLDS
    )
    active_fetcher = fetcher if fetcher is not None else default_fetcher
    active_probe = (
        resident_probe if resident_probe is not None else default_resident_probe
    )
    leases_path = leases_file_path(real_home)
    current_host = (
        str(owner.get("host") or "").strip() if isinstance(owner, Mapping) else ""
    ) or socket.gethostname()

    deadline = time.monotonic() + max(0.0, float(wait_seconds))
    while True:
        current_now = _coerce_now(now)
        acq, skipped = _attempt_acquire_once(
            owner,
            cfg=cfg,
            leases_path=leases_path,
            host_profile=host_profile,
            quota_pool=quota_pool,
            thresholds=active_thresholds,
            fetcher=active_fetcher,
            resident_probe=active_probe,
            now=current_now,
            current_host=current_host,
            owner_id=owner_id,
            dry_run=dry_run,
            preferred_profile=preferred_profile,
        )
        if acq is not None:
            return acq

        failure_reason = _pool_failure_reason(cfg["pool"], skipped)
        if dry_run or failure_reason == "pool_exhausted" or wait_seconds <= 0:
            return Acquisition(
                profile=None,
                via_ag_run=False,
                owner_id=owner_id,
                skipped=skipped,
                reason=failure_reason,
            )

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return Acquisition(
                profile=None,
                via_ag_run=False,
                owner_id=owner_id,
                skipped=skipped,
                reason=failure_reason,
            )
        time.sleep(min(max(0.05, float(poll_seconds)), remaining))


def heartbeat(
    owner_id: str,
    *,
    real_home: Path | str | None = None,
    now: datetime | None = None,
) -> bool:
    """Refresh heartbeat_at for the lease matching `owner_id`."""
    current_now = _coerce_now(now)
    leases_path = leases_file_path(real_home)

    def _op() -> bool:
        if not leases_path.is_file():
            return False
        doc = _load_or_init_leases_doc(leases_path)
        updated = False
        ts = _format_utc(current_now)
        for rec in doc.get("profiles", {}).values():
            for lease in rec.get("leases", []):
                if isinstance(lease, dict) and lease.get("owner_id") == owner_id:
                    lease["heartbeat_at"] = ts
                    updated = True
        if updated:
            _pc._atomic_write_json(leases_path, doc)
        return updated

    return bool(_with_file_lock(leases_path, _op))


def release(
    owner_id: str,
    *,
    real_home: Path | str | None = None,
    now: datetime | None = None,
) -> bool:
    """Purge stale leases and release the lease belonging to `owner_id` (no-op if absent)."""
    current_now = _coerce_now(now)
    cfg = load_pool_config(real_home=real_home)
    lease_ttl = float(cfg["lease_ttl_seconds"])
    leases_path = leases_file_path(real_home)
    current_host = socket.gethostname()

    def _op() -> bool:
        if not leases_path.is_file():
            return False
        doc = _load_or_init_leases_doc(leases_path)
        purged = _purge_stale_leases(
            doc,
            now=current_now,
            lease_ttl_seconds=lease_ttl,
            current_host=current_host,
        )
        removed = False
        for rec in doc.get("profiles", {}).values():
            leases = rec.get("leases", [])
            kept = [
                lease
                for lease in leases
                if not (
                    isinstance(lease, Mapping) and lease.get("owner_id") == owner_id
                )
            ]
            if len(kept) != len(leases):
                rec["leases"] = kept
                removed = True
        if purged or removed:
            _pc._atomic_write_json(leases_path, doc)
        return removed

    return bool(_with_file_lock(leases_path, _op))


def mark_exhausted(
    profile: str,
    until: datetime | str | None = None,
    *,
    reason: str | None = None,
    quota: Mapping[str, Any] | None = None,
    real_home: Path | str | None = None,
    now: datetime | None = None,
) -> None:
    """Record exhaustion timestamp (and optional reason/quota) without touching leases."""
    validate_profile_name(profile)
    current_now = _coerce_now(now)
    cfg = load_pool_config(real_home=real_home)
    recheck_sec = float(cfg["exhausted_recheck_seconds"])

    if until is None:
        until_iso = _format_utc(current_now + timedelta(seconds=recheck_sec))
    elif isinstance(until, datetime):
        until_iso = _format_utc(until)
    else:
        until_iso = _normalize_iso_or_raw(until)

    leases_path = leases_file_path(real_home)

    def _op() -> None:
        doc = _load_or_init_leases_doc(leases_path)
        rec = _ensure_profile_record(doc, profile)
        rec["exhausted_until"] = until_iso
        rec["exhausted_checked_at"] = _format_utc(current_now)
        if reason is not None:
            rec["exhausted_reason"] = reason
        if quota is not None:
            rec["quota"] = _sanitize_quota_payload(quota, fetched_at=current_now)
        _pc._atomic_write_json(leases_path, doc)

    _with_file_lock(leases_path, _op)


def clear_exhausted(
    profile: str | None = None,
    *,
    real_home: Path | str | None = None,
) -> list[str]:
    """Clear exhaustion timestamps and cached quota without modifying active leases."""
    cfg = load_pool_config(real_home=real_home)
    pool_names = {entry["profile"] for entry in cfg["pool"]}
    leases_path = leases_file_path(real_home)

    def _op() -> list[str]:
        if not leases_path.is_file():
            if profile is not None and profile not in pool_names:
                raise AgyPoolError(f"Profile '{profile}' is not in the pool")
            return []
        doc = _load_or_init_leases_doc(leases_path)
        profiles_map = doc.get("profiles", {})
        if profile is not None:
            if profile not in pool_names and profile not in profiles_map:
                raise AgyPoolError(f"Profile '{profile}' is not in the pool")
            targets = [profile] if profile in profiles_map else []
        else:
            targets = list(profiles_map.keys())
        cleared: list[str] = []
        for target in targets:
            rec = profiles_map[target]
            rec["exhausted_until"] = None
            rec["exhausted_checked_at"] = None
            rec["exhausted_reason"] = None
            rec["quota"] = None
            cleared.append(target)
        _pc._atomic_write_json(leases_path, doc)
        return cleared

    return list(_with_file_lock(leases_path, _op))


def _format_lease_owner_desc(lease: Mapping[str, Any]) -> str:
    owner_id = str(lease.get("owner_id") or "unknown")
    parts = [
        str(part)
        for part in (lease.get("epic"), lease.get("task"))
        if isinstance(part, str) and part
    ]
    slot = lease.get("slot")
    if slot is not None:
        parts.append(f"slot {slot}")
    detail = "/".join(parts)
    return f"{owner_id} ({detail})" if detail else owner_id


def add_profile(
    name: str,
    *,
    priority: int = 1,
    max_concurrent: int = DEFAULT_MAX_CONCURRENT,
    real_home: Path | str | None = None,
) -> dict[str, Any]:
    """Validate and add a profile to global agy_profiles.json under lock."""
    validate_profile_dir(name, real_home=real_home)
    _validate_positive_int(priority, "priority")
    _validate_positive_int(max_concurrent, "max_concurrent")
    cfg_path = profiles_config_path(real_home)

    def _op() -> dict[str, Any]:
        raw = _read_json_object(cfg_path)
        cfg = _default_pool_config() if raw is None else validate_pool_config(raw)
        if any(entry["profile"] == name for entry in cfg["pool"]):
            raise AgyPoolError(f"Profile '{name}' is already in the pool")
        cfg["pool"].append(
            {"profile": name, "priority": priority, "max_concurrent": max_concurrent}
        )
        validated = validate_pool_config(cfg)
        _pc._atomic_write_json(cfg_path, validated)
        return validated

    return dict(_with_file_lock(cfg_path, _op))


def remove_profile(
    name: str,
    *,
    real_home: Path | str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Remove a profile from agy_profiles.json; refuses while any live lease exists."""
    validate_profile_name(name)
    current_now = _coerce_now(now)
    cfg_path = profiles_config_path(real_home)
    leases_path = leases_file_path(real_home)
    current_host = socket.gethostname()

    def _op_cfg() -> dict[str, Any]:
        raw = _read_json_object(cfg_path)
        cfg = _default_pool_config() if raw is None else validate_pool_config(raw)
        if not any(entry["profile"] == name for entry in cfg["pool"]):
            raise AgyPoolError(f"Profile '{name}' is not in the pool")
        lease_ttl = float(cfg["lease_ttl_seconds"])

        def _check_leases() -> None:
            if not leases_path.is_file():
                return
            doc = _load_or_init_leases_doc(leases_path)
            purged = _purge_stale_leases(
                doc,
                now=current_now,
                lease_ttl_seconds=lease_ttl,
                current_host=current_host,
            )
            if purged:
                _pc._atomic_write_json(leases_path, doc)
            live_leases = doc.get("profiles", {}).get(name, {}).get("leases", [])
            if live_leases:
                owners = ", ".join(
                    _format_lease_owner_desc(lease) for lease in live_leases
                )
                raise AgyPoolError(
                    f"Cannot remove profile '{name}': held by live lease(s) [{owners}]"
                )

        _with_file_lock(leases_path, _check_leases)
        cfg["pool"] = [entry for entry in cfg["pool"] if entry["profile"] != name]
        validated = validate_pool_config(cfg)
        _pc._atomic_write_json(cfg_path, validated)
        return validated

    return dict(_with_file_lock(cfg_path, _op_cfg))


def release_profile_leases(
    name: str,
    *,
    force: bool = False,
    real_home: Path | str | None = None,
    now: datetime | None = None,
) -> int:
    """Release leases for `name`, refusing live leases unless `force` is True."""
    validate_profile_name(name)
    current_now = _coerce_now(now)
    cfg = load_pool_config(real_home=real_home)
    lease_ttl = float(cfg["lease_ttl_seconds"])
    leases_path = leases_file_path(real_home)
    current_host = socket.gethostname()
    in_pool = any(entry["profile"] == name for entry in cfg["pool"])

    def _op() -> int:
        if not leases_path.is_file():
            if not in_pool:
                raise AgyPoolError(f"Profile '{name}' is not in the pool")
            return 0
        doc = _load_or_init_leases_doc(leases_path)
        purged = _purge_stale_leases(
            doc,
            now=current_now,
            lease_ttl_seconds=lease_ttl,
            current_host=current_host,
        )
        profiles_map = doc.get("profiles", {})
        if not in_pool and name not in profiles_map:
            if purged:
                _pc._atomic_write_json(leases_path, doc)
            raise AgyPoolError(f"Profile '{name}' is not in the pool")
        rec = profiles_map.get(name)
        live_leases = rec.get("leases", []) if isinstance(rec, dict) else []
        if not live_leases:
            if purged:
                _pc._atomic_write_json(leases_path, doc)
            return 0
        if not force:
            owners = ", ".join(_format_lease_owner_desc(lease) for lease in live_leases)
            raise AgyPoolError(
                f"Cannot release profile '{name}' without --force: held by {owners}"
            )
        count = len(live_leases)
        if isinstance(rec, dict):
            rec["leases"] = []
        _pc._atomic_write_json(leases_path, doc)
        return count

    return int(_with_file_lock(leases_path, _op))


def probe_profiles(
    profile: str | None = None,
    *,
    fetcher: Callable[[str], Mapping[str, Any]] | None = None,
    real_home: Path | str | None = None,
    now: datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """Call `fetcher` for `profile` (or every pool profile) and refresh quota cache."""
    current_now = _coerce_now(now)
    cfg = load_pool_config(real_home=real_home)
    pool_names = [str(entry["profile"]) for entry in cfg["pool"]]
    if profile is not None:
        validate_profile_name(profile)
        if profile not in pool_names:
            raise AgyPoolError(f"Profile '{profile}' is not in the pool")
        targets = [profile]
    else:
        targets = pool_names

    active_fetcher = fetcher if fetcher is not None else default_fetcher
    probed: dict[str, dict[str, Any]] = {}
    for name in targets:
        payload = active_fetcher(name)
        sanitized = _sanitize_quota_payload(payload, fetched_at=current_now)
        probed[name] = sanitized or {}

    if targets:
        leases_path = leases_file_path(real_home)

        def _store() -> None:
            doc = _load_or_init_leases_doc(leases_path)
            for name, sanitized in probed.items():
                rec = _ensure_profile_record(doc, name)
                if sanitized:
                    rec["quota"] = sanitized
            _pc._atomic_write_json(leases_path, doc)

        _with_file_lock(leases_path, _store)
    return probed


def pool_status(
    real_home: Path | str | None = None,
    *,
    now: datetime | None = None,
    host_profile: str | None = None,
) -> dict[str, Any]:
    """Return overall pool state, per-profile lease/exhaustion info, and earliest reset."""
    current_now = _coerce_now(now)
    cfg = load_pool_config(real_home=real_home)
    pool: list[dict[str, Any]] = list(cfg["pool"])
    if not pool:
        return {"state": "empty", "profiles": [], "earliest_reset": None}

    leases_path = leases_file_path(real_home)
    lease_ttl = float(cfg["lease_ttl_seconds"])
    current_host = socket.gethostname()
    resolved_host = host_profile if host_profile is not None else detect_host_profile()

    def _read_and_purge() -> dict[str, Any]:
        if not leases_path.is_file():
            return {"schema_version": POOL_SCHEMA_VERSION, "profiles": {}}
        doc = _load_or_init_leases_doc(leases_path)
        purged = _purge_stale_leases(
            doc,
            now=current_now,
            lease_ttl_seconds=lease_ttl,
            current_host=current_host,
        )
        if purged:
            _pc._atomic_write_json(leases_path, doc)
        return doc

    leases_doc = _with_file_lock(leases_path, _read_and_purge)
    profiles_map = leases_doc.get("profiles", {})

    entries: list[dict[str, Any]] = []
    future_resets: list[datetime] = []
    all_exhausted = True
    any_non_exhausted_has_capacity = False

    for item in pool:
        p_name = str(item["profile"])
        max_conc = int(item["max_concurrent"])
        rec = profiles_map.get(p_name, _empty_profile_record())
        raw_leases = [l for l in rec.get("leases", []) if isinstance(l, Mapping)]
        leased_by = [
            {
                "epic": str(lease.get("epic") or ""),
                "task": str(lease.get("task") or ""),
                "slot": lease.get("slot"),
                "role": str(lease.get("role") or ""),
                "repo": str(lease.get("repo") or ""),
            }
            for lease in raw_leases
        ]

        ex_until_raw = rec.get("exhausted_until")
        ex_until_dt = _parse_utc(ex_until_raw)
        is_exhausted = ex_until_dt is not None and ex_until_dt > current_now
        if is_exhausted and ex_until_dt is not None:
            future_resets.append(ex_until_dt)
        else:
            all_exhausted = False
            is_host = resolved_host is not None and p_name == resolved_host
            if _has_capacity(
                raw_leases, is_host_profile=is_host, max_concurrent=max_conc
            ):
                any_non_exhausted_has_capacity = True

        entries.append(
            {
                "profile": p_name,
                "priority": int(item["priority"]),
                "max_concurrent": max_conc,
                "leased_by": leased_by,
                "exhausted_until": ex_until_raw,
                "exhausted_reason": rec.get("exhausted_reason"),
                "quota": rec.get("quota"),
            }
        )

    if all_exhausted:
        state = "exhausted"
    elif not any_non_exhausted_has_capacity:
        state = "busy"
    else:
        state = "ok"

    earliest_reset = _format_utc(min(future_resets)) if future_resets else None
    return {
        "state": state,
        "profiles": entries,
        "earliest_reset": earliest_reset,
    }


def _human_exhausted_reason(reason: Any) -> str:
    if reason == "5h":
        return "5-hour limit reached"
    if reason == "weekly":
        return "weekly limit reached"
    if reason == "5h+weekly":
        return "5-hour and weekly limits reached"
    if isinstance(reason, str) and reason.startswith("status:"):
        status_val = reason.split(":", 1)[1]
        return f"account status {status_val}"
    return "quota limit reached"


def exhaustion_report(
    status: Mapping[str, Any],
    *,
    catalogue: Mapping[str, Any],
    programmer_binding: PersonaBinding,
    which: Callable[[str], str | None] = shutil.which,
    fetcher: Callable[[str], Mapping[str, Any]] | None = None,
    wait_seconds: float = 0,
) -> list[str]:
    """Format actionable exhaustion or busy-pool recovery lines for Role 1.0."""
    _ = fetcher
    state = str(status.get("state") or "")
    profiles = list(status.get("profiles") or [])

    if state == "busy":
        wait_val = status.get("wait_seconds", wait_seconds)
        wait_display = (
            int(wait_val)
            if isinstance(wait_val, (int, float)) and float(wait_val).is_integer()
            else wait_val
        )
        lines = [
            f"Stopped: every agy profile stayed in use for {wait_display} seconds."
        ]
        for entry in profiles:
            p_name = str(entry.get("profile") or "")
            for holder in entry.get("leased_by") or []:
                epic = str(holder.get("epic") or "unknown")
                task = str(holder.get("task") or "unknown")
                slot = holder.get("slot")
                slot_str = str(slot) if slot is not None else "?"
                lines.append(f"- {p_name} is held by {epic}/{task}/slot {slot_str}")
        return lines

    lines = ["Stopped: all agy profiles are out of quota."]
    for entry in profiles:
        p_name = str(entry.get("profile") or "")
        reason_text = _human_exhausted_reason(entry.get("exhausted_reason"))
        reset_text = _normalize_iso_or_raw(entry.get("exhausted_until"))
        lines.append(f"- {p_name}: {reason_text} (resets {reset_text})")

    earliest_raw = status.get("earliest_reset")
    earliest_text = _normalize_iso_or_raw(earliest_raw) if earliest_raw else "unknown"
    lines.append(f"Earliest reset: {earliest_text}.")
    lines.append("Options:")
    lines.append(
        "- wait for the reset or top up the quota of a profile, "
        'then run "/d3nexus:dev-config profiles clear" and resume'
    )

    for cli in _NON_AGY_SWITCH_ORDER:
        match: tuple[str, Mapping[str, Any]] | None = None
        for alias, meta in catalogue.items():
            if isinstance(meta, Mapping) and meta.get("cli") == cli:
                match = (str(alias), meta)
                break
        if match is None:
            continue
        alias_name, meta = match
        efforts = [str(e) for e in meta.get("efforts", []) if isinstance(e, str)]
        if programmer_binding.effort in efforts:
            chosen_effort = programmer_binding.effort
        elif efforts:
            chosen_effort = efforts[-1]
        else:
            chosen_effort = programmer_binding.effort

        if cli == "kiro":
            cli_present = (which("kiro-cli") or which("kiro")) is not None
        else:
            cli_present = which(cli) is not None
        suffix = "" if cli_present else f' ("{cli}" CLI not on PATH)'
        lines.append(
            f"- switch the programmer: /d3nexus:dev-config set programmer {alias_name} {chosen_effort}{suffix}"
        )
    return lines
