#!/usr/bin/env python3
"""Atomic runtime state envelope and dual-root transactional persistence.

Centralizes canonical-root `fcntl.flock` transactions, monotonic `generation`
versioning, sibling-temp `os.replace()` writes, and namespaced domain envelopes
for `.devtool/state/<epic_slug>.heartbeat.json`, `pending_decision.json`, and
`quality_active.json` across primary repository and active worktree roots.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
import contextlib
import copy
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import threading
from typing import Any, TypeVar, cast
import uuid

SCHEMA_VERSION = 1
ENVELOPE_LOCK_NAME = ".state_envelope.lock"
DEFAULT_QUALITY_TTL_SEC = 300
TERMINAL_QUALITY_STATUSES = frozenset({"passed", "failed", "aborted", "stale"})
_SLOT_WORKTREE_RE = re.compile(r"-slot-\d+$")

T = TypeVar("T")

_LOCK_REGISTRY_GUARD = threading.Lock()
_INPROC_PATH_LOCKS: dict[Path, threading.RLock] = {}
_ACTIVE_FLOCKS: dict[Path, tuple[int, Any]] = {}


@contextlib.contextmanager
def _state_lock(primary_devtool_dir: Path) -> Iterator[None]:
    """Acquire a reentrant thread+process exclusive lock on the primary repository's state lock file."""
    state_dir = primary_devtool_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_file = (state_dir / ENVELOPE_LOCK_NAME).resolve()
    with _LOCK_REGISTRY_GUARD:
        rlock = _INPROC_PATH_LOCKS.setdefault(lock_file, threading.RLock())
    rlock.acquire()
    try:
        active = _ACTIVE_FLOCKS.get(lock_file)
        if active is None:
            handle = lock_file.open("a+", encoding="utf-8")
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            except BaseException:
                with contextlib.suppress(OSError):
                    handle.close()
                raise
            _ACTIVE_FLOCKS[lock_file] = (1, handle)
        else:
            depth, handle = active
            _ACTIVE_FLOCKS[lock_file] = (depth + 1, handle)
        try:
            yield
        finally:
            cur_depth, cur_handle = _ACTIVE_FLOCKS[lock_file]
            if cur_depth > 1:
                _ACTIVE_FLOCKS[lock_file] = (cur_depth - 1, cur_handle)
            else:
                _ACTIVE_FLOCKS.pop(lock_file, None)
                with contextlib.suppress(OSError):
                    fcntl.flock(cur_handle.fileno(), fcntl.LOCK_UN)
                with contextlib.suppress(OSError):
                    cur_handle.close()
    finally:
        rlock.release()


def _utc_now_iso() -> str:
    """Return current UTC ISO-8601 timestamp with seconds precision."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_iso_datetime(raw: object) -> datetime | None:
    """Parse an ISO-8601 timestamp string into a UTC-aware datetime."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _safe_int(value: object, default: int = 0) -> int:
    """Return value when it is an exact integer (excluding bool), else default."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return default


def _validate_state_filename(filename: str) -> str:
    """Validate a state filename as a safe single relative basename."""
    if not filename or filename in {".", ".."} or Path(filename).name != filename:
        raise ValueError(f"Invalid state filename: {filename!r}")
    return filename


def _sanitize_epic_slug(epic_slug: str) -> str:
    """Return a filesystem-safe epic slug without path separators."""
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", epic_slug.strip()).strip("-.")
    return cleaned or "general"


def _run_git(cwd: Path, *args: str) -> str | None:
    """Run a git command inside cwd and return stripped stdout on success."""
    try:
        res = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):
        return None
    if res.returncode != 0:
        return None
    out = res.stdout.strip()
    return out or None


def _resolve_git_path(cwd: Path, flag: str) -> Path | None:
    """Resolve a path returned by `git rev-parse <flag>` relative to cwd."""
    raw = _run_git(cwd, "rev-parse", flag)
    if raw is None:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    return candidate.resolve()


def _existing_anchor(path: Path) -> Path | None:
    """Return path or its nearest existing directory ancestor."""
    current = path
    if current.is_file():
        current = current.parent
    while not current.exists():
        parent = current.parent
        if parent == current:
            return None
        current = parent
    return current if current.is_dir() else current.parent


def _is_slot_worktree(path: Path) -> bool:
    """Return True when path is an ephemeral worker-pool slot worktree."""
    return path.parent.name == ".worktrees" and bool(
        _SLOT_WORKTREE_RE.search(path.name)
    )


def _parse_worktree_branches(output: str) -> list[tuple[Path, str | None]]:
    """Parse `(worktree_path, branch_ref)` entries from `git worktree list --porcelain`."""
    entries: list[tuple[Path, str | None]] = []
    current_path: Path | None = None
    current_branch: str | None = None
    for line in output.splitlines():
        if line.startswith("worktree "):
            if current_path is not None:
                entries.append((current_path, current_branch))
            current_path = Path(line[len("worktree ") :])
            current_branch = None
        elif line.startswith("branch "):
            current_branch = line[len("branch ") :]
        elif line == "detached":
            current_branch = None
    if current_path is not None:
        entries.append((current_path, current_branch))
    return entries


def resolve_shared_devtool_dirs(start_path: Path | None = None) -> list[Path]:
    """Return deduplicated `.devtool/` directories ordered primary repo first, worktree second."""
    target = Path(start_path) if start_path is not None else Path.cwd()
    if target.name == ".devtool":
        target = target.parent
    anchor = _existing_anchor(target)
    if anchor is None:
        return [(target.resolve() / ".devtool")]

    common_dir = _resolve_git_path(anchor, "--git-common-dir")
    worktree_root = _resolve_git_path(anchor, "--show-toplevel")
    primary_root = common_dir.parent if common_dir is not None else None

    ordered: list[Path] = []
    seen: set[Path] = set()
    for root in (primary_root, worktree_root):
        if root is None:
            continue
        devtool_dir = (root / ".devtool").resolve()
        if devtool_dir not in seen:
            seen.add(devtool_dir)
            ordered.append(devtool_dir)

    if not ordered:
        base = target.parent if target.is_file() else target
        ordered.append((base / ".devtool").resolve())
    return ordered


def _normalize_devtool_dir(path: Path) -> Path:
    """Normalize either a checkout root or a `.devtool` path into a resolved `.devtool` dir."""
    resolved = Path(path).resolve()
    return (
        resolved if resolved.name == ".devtool" else (resolved / ".devtool").resolve()
    )


def _discover_active_mirror_dirs(primary_root: Path, filename: str) -> list[Path]:
    """Find existing linked non-slot worktree `.devtool` dirs tracking this state file."""
    porcelain = _run_git(primary_root, "worktree", "list", "--porcelain")
    if not porcelain:
        return []

    epic_slug: str | None = None
    epic_names: set[str] = set()
    if filename.endswith(".heartbeat.json"):
        epic_slug = filename[: -len(".heartbeat.json")]
        epic_names = {
            epic_slug,
            epic_slug.replace("-", "_"),
            epic_slug.replace("_", "-"),
        }

    mirrors: list[Path] = []
    primary_resolved = primary_root.resolve()
    for wt_path, branch in _parse_worktree_branches(porcelain):
        wt_resolved = wt_path.resolve()
        if wt_resolved == primary_resolved or _is_slot_worktree(wt_resolved):
            continue
        wt_devtool = (wt_resolved / ".devtool").resolve()
        if not wt_devtool.is_dir():
            continue
        state_file = wt_devtool / "state" / filename
        is_matching_epic = epic_slug is not None and (
            branch == f"refs/heads/epic/{epic_slug}" or wt_resolved.name in epic_names
        )
        if state_file.is_file() or is_matching_epic:
            mirrors.append(wt_devtool)
    return mirrors


def _collect_target_devtool_dirs(
    start_path: Path | None,
    filename: str,
    extra_devtool_dirs: Sequence[Path] | None = None,
) -> list[Path]:
    """Assemble deduplicated target `.devtool` dirs with primary root first."""
    ordered: list[Path] = []
    seen: set[Path] = set()

    def _add(devtool_dir: Path) -> None:
        resolved = devtool_dir.resolve()
        if resolved not in seen:
            seen.add(resolved)
            ordered.append(resolved)

    shared = resolve_shared_devtool_dirs(start_path)
    for d in shared:
        _add(d)
    for d in _discover_active_mirror_dirs(shared[0].parent, filename):
        _add(d)
    if extra_devtool_dirs:
        for extra in extra_devtool_dirs:
            _add(_normalize_devtool_dir(extra))
    return ordered


def read_json_safe(path: Path, default: T) -> T:
    """Read JSON from path, returning a deep copy of default on missing, empty, or corrupt data."""
    try:
        if not path.is_file():
            return copy.deepcopy(default)
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return copy.deepcopy(default)
        parsed = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return copy.deepcopy(default)

    if isinstance(default, dict) and not isinstance(parsed, dict):
        return copy.deepcopy(default)
    if isinstance(default, list) and not isinstance(parsed, list):
        return copy.deepcopy(default)
    return cast(T, parsed)


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    """Atomically write JSON payload via sibling temporary file, fsync, and `os.replace()`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(dict(payload), indent=2, ensure_ascii=False) + "\n"
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        tmp_path = None
    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
    return path


def _read_highest_snapshot(
    devtool_dirs: Sequence[Path],
    filename: str,
    default: Mapping[str, Any],
) -> tuple[dict[str, Any], int]:
    """Select the highest-generation valid snapshot across mirrors merged with default."""
    best_snapshot: dict[str, Any] = {}
    best_gen = -1
    for devtool_dir in devtool_dirs:
        empty_snap: dict[str, Any] = {}
        candidate = read_json_safe(devtool_dir / "state" / filename, empty_snap)
        if not candidate:
            continue
        gen = _safe_int(candidate.get("generation"), 0)
        if gen > best_gen:
            best_gen = gen
            best_snapshot = candidate

    merged = copy.deepcopy(dict(default))
    if best_snapshot:
        for key, value in best_snapshot.items():
            merged[key] = copy.deepcopy(value)
    return merged, max(best_gen, 0)


def _write_versioned_mirror(path: Path, payload: Mapping[str, Any]) -> None:
    """Write payload atomically after verifying target does not already hold a newer generation."""
    empty_existing: dict[str, Any] = {}
    existing = read_json_safe(path, empty_existing)
    existing_gen = _safe_int(existing.get("generation"), 0) if existing else 0
    incoming_gen = _safe_int(payload.get("generation"), 0)
    if existing and incoming_gen < existing_gen:
        raise ValueError(
            f"Refusing stale state write generation {incoming_gen} < {existing_gen} at {path}"
        )
    atomic_write_json(path, payload)


def run_state_transaction(
    start_path: Path | None,
    filename: str,
    mutator: Callable[[dict[str, Any]], Mapping[str, Any] | None],
    default: Mapping[str, Any] | None = None,
    *,
    extra_devtool_dirs: Sequence[Path] | None = None,
) -> dict[str, Any]:
    """Execute a locked read-modify-write state transaction with monotonic generation mirrors."""
    safe_filename = _validate_state_filename(filename)
    base_default = dict(default) if default is not None else {}
    target_dirs = _collect_target_devtool_dirs(
        start_path, safe_filename, extra_devtool_dirs
    )

    with _state_lock(target_dirs[0]):
        working, current_gen = _read_highest_snapshot(
            target_dirs, safe_filename, base_default
        )
        working["generation"] = current_gen
        mutated = mutator(working)
        next_state = (
            copy.deepcopy(working) if mutated is None else copy.deepcopy(dict(mutated))
        )

        if "generation" in next_state:
            requested_gen = _safe_int(next_state.get("generation"), current_gen)
            if requested_gen < current_gen:
                raise ValueError(
                    f"Stale state generation {requested_gen} < {current_gen} for {safe_filename}"
                )

        next_gen = current_gen + 1
        schema_ver = _safe_int(next_state.get("schema_version"), SCHEMA_VERSION)
        next_state["schema_version"] = schema_ver if schema_ver > 0 else SCHEMA_VERSION
        next_state["generation"] = next_gen

        for devtool_dir in target_dirs:
            _write_versioned_mirror(devtool_dir / "state" / safe_filename, next_state)

        return copy.deepcopy(next_state)


def update_epic_heartbeat(
    start_path: Path | None,
    epic_slug: str,
    *,
    stage: str | None = None,
    active_wave: int | None = None,
    active_tasks: Sequence[str] | None = None,
    slots: Mapping[str, Any] | None = None,
    slot_updates: Mapping[str, Any] | None = None,
    remove_slots: Sequence[str] | None = None,
    replace_slots: bool = False,
    last_event: str | None = None,
    updated_at: str | None = None,
    pic: str | None = None,
    tally: Mapping[str, int] | None = None,
    extra_devtool_dirs: Sequence[Path] | None = None,
) -> dict[str, Any]:
    """Transactionally update `<epic_slug>.heartbeat.json` across shared devtool mirrors."""
    safe_slug = _sanitize_epic_slug(epic_slug)
    filename = f"{safe_slug}.heartbeat.json"
    default_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generation": 0,
        "epic_slug": epic_slug,
        "stage": "",
        "active_wave": None,
        "active_tasks": [],
        "slots": {},
        "last_event": "",
        "updated_at": _utc_now_iso(),
    }

    def _mutate(state: dict[str, Any]) -> None:
        state["epic_slug"] = epic_slug
        if stage is not None:
            state["stage"] = stage
        if active_wave is not None:
            state["active_wave"] = active_wave
        if active_tasks is not None:
            state["active_tasks"] = list(
                dict.fromkeys(str(t) for t in active_tasks if str(t))
            )
        if pic is not None:
            state["pic"] = pic
        if tally is not None:
            state["tally"] = dict(tally)
        if last_event is not None:
            state["last_event"] = last_event
        state["updated_at"] = updated_at or _utc_now_iso()

        current_slots = state.get("slots")
        merged_slots = (
            dict(current_slots)
            if isinstance(current_slots, dict) and not replace_slots
            else {}
        )
        for patch in (slots, slot_updates):
            if patch is None:
                continue
            for slot_key, slot_val in patch.items():
                key_str = str(slot_key)
                if slot_val is None:
                    merged_slots.pop(key_str, None)
                else:
                    merged_slots[key_str] = copy.deepcopy(slot_val)
        if remove_slots:
            for slot_key in remove_slots:
                merged_slots.pop(str(slot_key), None)
        state["slots"] = merged_slots

    return run_state_transaction(
        start_path,
        filename,
        _mutate,
        default=default_payload,
        extra_devtool_dirs=extra_devtool_dirs,
    )


def _sync_pending_decision_summary(state: dict[str, Any]) -> None:
    """Recompute top-level compatibility fields from active entries in `decisions`."""
    decisions = state.get("decisions")
    if not isinstance(decisions, dict):
        decisions = {}
        state["decisions"] = decisions

    active_entries: list[tuple[str, dict[str, Any]]] = [
        (epic_key, entry)
        for epic_key, entry in decisions.items()
        if isinstance(entry, dict) and entry.get("active", True)
    ]
    if not active_entries:
        state["active"] = False
        state["epic"] = None
        state["decision_id"] = None
        return

    active_entries.sort(key=lambda item: (str(item[1].get("created_at", "")), item[0]))
    latest_epic, latest_entry = active_entries[-1]
    state["active"] = True
    state["epic"] = latest_entry.get("epic", latest_epic)
    state["decision_id"] = latest_entry.get("decision_id")


def record_pending_decision(
    start_path: Path | None,
    epic_slug: str,
    reason: str,
    *,
    kind: str = "approval",
    decision_id: str | None = None,
    stage: str = "",
    worktree: str | Path | None = None,
    extra_devtool_dirs: Sequence[Path] | None = None,
) -> dict[str, Any]:
    """Record an epic-namespaced pending human decision in `pending_decision.json`."""
    now_iso = _utc_now_iso()
    dec_id = decision_id or (
        f"dec-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:4]}"
    )
    wt_value = (
        str(Path(worktree).resolve())
        if worktree is not None
        else str(resolve_shared_devtool_dirs(start_path)[-1].parent)
    )
    default_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generation": 0,
        "active": False,
        "epic": None,
        "decision_id": None,
        "decisions": {},
    }

    def _mutate(state: dict[str, Any]) -> None:
        decisions = state.get("decisions")
        if not isinstance(decisions, dict):
            decisions = {}
            state["decisions"] = decisions
        decisions[epic_slug] = {
            "decision_id": dec_id,
            "active": True,
            "epic": epic_slug,
            "kind": kind,
            "reason": reason,
            "stage": stage,
            "worktree": wt_value,
            "created_at": now_iso,
        }
        _sync_pending_decision_summary(state)

    return run_state_transaction(
        start_path,
        "pending_decision.json",
        _mutate,
        default=default_payload,
        extra_devtool_dirs=extra_devtool_dirs,
    )


def clear_pending_decision(
    start_path: Path | None,
    epic_slug: str,
    decision_id: str | None = None,
    *,
    extra_devtool_dirs: Sequence[Path] | None = None,
) -> dict[str, Any]:
    """Clear only the matching epic (and optional decision_id) from `pending_decision.json`."""
    default_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generation": 0,
        "active": False,
        "epic": None,
        "decision_id": None,
        "decisions": {},
    }
    target_dirs = _collect_target_devtool_dirs(
        start_path, "pending_decision.json", extra_devtool_dirs
    )
    if not any((d / "state" / "pending_decision.json").is_file() for d in target_dirs):
        return copy.deepcopy(default_payload)

    def _mutate(state: dict[str, Any]) -> None:
        decisions = state.get("decisions")
        if not isinstance(decisions, dict):
            decisions = {}
            state["decisions"] = decisions
        entry = decisions.get(epic_slug)
        if isinstance(entry, dict):
            if decision_id is None or entry.get("decision_id") == decision_id:
                decisions.pop(epic_slug, None)
        elif not decisions and state.get("epic") == epic_slug:
            if decision_id is None or state.get("decision_id") == decision_id:
                state["active"] = False
                state["epic"] = None
                state["decision_id"] = None
        _sync_pending_decision_summary(state)

    return run_state_transaction(
        start_path,
        "pending_decision.json",
        _mutate,
        default=default_payload,
        extra_devtool_dirs=extra_devtool_dirs,
    )


def _sync_quality_summary(state: dict[str, Any], preferred_run_id: str) -> None:
    """Keep top-level `quality_active.json` summary synced with active or latest run."""
    runs = state.get("runs")
    if not isinstance(runs, dict) or not runs:
        return
    running_entries = [
        entry
        for entry in runs.values()
        if isinstance(entry, dict) and entry.get("status") == "running"
    ]
    if running_entries:
        preferred = runs.get(preferred_run_id)
        chosen = (
            preferred
            if isinstance(preferred, dict) and preferred.get("status") == "running"
            else max(running_entries, key=lambda e: str(e.get("updated_at", "")))
        )
    else:
        preferred = runs.get(preferred_run_id)
        chosen = (
            preferred
            if isinstance(preferred, dict)
            else max(
                (e for e in runs.values() if isinstance(e, dict)),
                key=lambda e: str(e.get("updated_at", "")),
            )
        )
    state["run_id"] = chosen.get("run_id")
    state["profile"] = chosen.get("profile", "")
    state["status"] = chosen.get("status", "")
    if chosen.get("epic_slug"):
        state["epic_slug"] = chosen.get("epic_slug")
    state["updated_at"] = chosen.get("updated_at", _utc_now_iso())


def update_quality_run(
    start_path: Path | None,
    run_id: str,
    *,
    epic_slug: str | None = None,
    profile: str | None = None,
    status: str = "running",
    provider: str | None = None,
    capability: str | None = None,
    step_index: int | None = None,
    step_total: int | None = None,
    pid: int | None = None,
    host: str | None = None,
    ttl_sec: float | None = None,
    started_at: str | None = None,
    updated_at: str | None = None,
    finished_at: str | None = None,
    elapsed_sec: float | None = None,
    extra_devtool_dirs: Sequence[Path] | None = None,
) -> dict[str, Any]:
    """Transactionally create or update `runs[run_id]` in `quality_active.json`."""
    now_iso = updated_at or _utc_now_iso()
    default_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generation": 0,
        "run_id": run_id,
        "profile": profile or "",
        "status": status,
        "runs": {},
    }

    def _mutate(state: dict[str, Any]) -> None:
        runs = state.get("runs")
        if not isinstance(runs, dict):
            runs = {}
            state["runs"] = runs
        existing = runs.get(run_id)
        entry: dict[str, Any] = (
            copy.deepcopy(existing) if isinstance(existing, dict) else {}
        )

        entry["run_id"] = run_id
        if epic_slug is not None:
            entry["epic_slug"] = epic_slug
        else:
            entry.setdefault("epic_slug", "")
        if profile is not None:
            entry["profile"] = profile
        else:
            entry.setdefault("profile", "")
        entry["status"] = status
        if provider is not None:
            entry["provider"] = provider
        else:
            entry.setdefault("provider", "")
        if capability is not None:
            entry["capability"] = capability
        else:
            entry.setdefault("capability", "")
        if step_index is not None:
            entry["step_index"] = step_index
        else:
            entry.setdefault("step_index", 0)
        if step_total is not None:
            entry["step_total"] = step_total
        else:
            entry.setdefault("step_total", 0)
        entry["pid"] = pid if pid is not None else entry.get("pid", os.getpid())
        entry["host"] = (
            host if host is not None else entry.get("host", socket.gethostname())
        )
        entry["ttl_sec"] = (
            ttl_sec
            if ttl_sec is not None
            else entry.get("ttl_sec", DEFAULT_QUALITY_TTL_SEC)
        )
        entry["started_at"] = started_at or entry.get("started_at") or now_iso
        entry["updated_at"] = now_iso
        if status in TERMINAL_QUALITY_STATUSES:
            entry["finished_at"] = finished_at or entry.get("finished_at") or now_iso
        else:
            entry["finished_at"] = finished_at
        if elapsed_sec is not None:
            entry["elapsed_sec"] = elapsed_sec
        else:
            entry.setdefault("elapsed_sec", 0.0)

        runs[run_id] = entry
        _sync_quality_summary(state, run_id)

    return run_state_transaction(
        start_path,
        "quality_active.json",
        _mutate,
        default=default_payload,
        extra_devtool_dirs=extra_devtool_dirs,
    )


def _is_local_pid_alive(pid: int) -> bool:
    """Return True if local OS reports process `pid` exists."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _expire_stale_quality_entry(
    entry: dict[str, Any],
    *,
    now: datetime,
    local_host: str,
) -> dict[str, Any]:
    """Transition a running quality entry to `stale` when TTL expired or local PID died."""
    result = copy.deepcopy(entry)
    if result.get("status") != "running":
        return result

    ttl_raw = result.get("ttl_sec")
    ttl_sec = (
        float(ttl_raw)
        if isinstance(ttl_raw, (int, float)) and not isinstance(ttl_raw, bool)
        else 0.0
    )
    updated_dt = _parse_iso_datetime(
        result.get("updated_at") or result.get("started_at")
    )
    if ttl_sec > 0 and updated_dt is not None:
        if (now - updated_dt).total_seconds() > ttl_sec:
            result["status"] = "stale"
            result["stale_reason"] = "ttl_expired"
            return result

    entry_host = str(result.get("host") or "").strip()
    pid_raw = result.get("pid")
    if (
        (not entry_host or entry_host == local_host)
        and isinstance(pid_raw, int)
        and not isinstance(pid_raw, bool)
    ):
        if not _is_local_pid_alive(pid_raw):
            result["status"] = "stale"
            result["stale_reason"] = "dead_pid"
            return result

    return result


def read_quality_runs(
    start_path: Path | None = None,
    *,
    expire_stale: bool = True,
    now_ts: datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """Read `quality_active.json` runs map across shared devtool dirs and expire stale runs."""
    target_dirs = _collect_target_devtool_dirs(start_path, "quality_active.json")
    snapshot, _ = _read_highest_snapshot(target_dirs, "quality_active.json", {})
    if not snapshot:
        return {}

    raw_runs = snapshot.get("runs")
    runs_map: dict[str, dict[str, Any]] = {}
    if isinstance(raw_runs, dict):
        for run_id, entry in raw_runs.items():
            if isinstance(entry, dict):
                runs_map[str(run_id)] = copy.deepcopy(entry)
    elif isinstance(snapshot.get("run_id"), str) and snapshot["run_id"]:
        runs_map[snapshot["run_id"]] = copy.deepcopy(snapshot)

    if not expire_stale:
        return runs_map

    now = (now_ts or datetime.now(timezone.utc)).astimezone(timezone.utc)
    local_host = socket.gethostname()
    return {
        run_id: _expire_stale_quality_entry(entry, now=now, local_host=local_host)
        for run_id, entry in runs_map.items()
    }
