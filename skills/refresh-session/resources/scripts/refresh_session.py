#!/usr/bin/env python3
"""Standalone script to ping Claude Code and Codex CLIs to refresh 5-hour rolling session windows.

Enforces zero skill initialization, zero workspace context, and minimum token consumption
by executing strictly inside an ephemeral isolated temporary directory.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import plistlib
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as _xml_escape

def _derive_real_home() -> str:
    """Host user's real HOME, derived (never hard-coded); strips /antigravity_homes/<profile> when inside a profile."""
    home = os.environ.get("REAL_HOME") or os.path.expanduser("~")
    return home.split("/antigravity_homes")[0] if "/antigravity_homes" in home else home


REAL_HOME = _derive_real_home()
KC_PASS = "H@No!a@12345"
SESSION_STORE_DB = Path(REAL_HOME) / ".devtool" / "state" / ".session_store.db"
SALT = "d3nexus-session-salt-2026"

NATURAL_PROMPTS = [
    "Explain HTTP status 200 in 5 words.",
    "What is POSIX standard?",
    "Python list comprehension syntax.",
    "Bash command for disk free space.",
    "Define idempotent in REST API in 5 words.",
    "What is git commit hash SHA?",
    "Explain difference between TCP and UDP in 1 line.",
    "Write a regex for matching digits in 5 chars.",
]


def hash_profile(name: str) -> str:
    return hashlib.sha256(f"{SALT}:{name}".encode("utf-8")).hexdigest()[:24]


GEMINI_MODEL_CANDIDATES: tuple[str, ...] = (
    "gemini-3.8-flash-low",
    "gemini-4-hydrogen-low",
    "gemini-3.8-flash-medium",
    "gemini-4-hydrogen-medium",
    "gemini-3.8-flash-high",
)
CLAUDE_MODEL_CANDIDATES: tuple[str, ...] = (
    "claude-sonnet-5-5-low",
    "claude-sonnet-4-6",
    "claude-sonnet-5-5-medium",
    "claude-opus-5-5-low",
    "claude-opus-4-6-thinking",
    "gpt-oss-120b-medium",
)
ARGON_MODEL_CANDIDATES: tuple[str, ...] = (
    "gemini-4-argon-low",
    "gemini-4-argon-medium",
    "gemini-4-argon-high",
)


def parse_agy_models_output(stdout: str) -> list[str]:
    """Extract ordered model IDs from `agy models` stdout."""
    models: list[str] = []
    seen: set[str] = set()
    for raw_line in (stdout or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", "-", "=")):
            continue
        token = line.split()[0].strip()
        if not token or token.lower() in ("model", "id", "models", "available"):
            continue
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,}", token) and token not in seen:
            seen.add(token)
            models.append(token)
    return models


def select_model_from_candidates(
    available_models: list[str],
    candidates: tuple[str, ...] | list[str],
    default: str,
) -> str:
    """Choose the first preferred model present in available_models, else fallback safely."""
    if available_models:
        avail_set = set(available_models)
        for cand in candidates:
            if cand in avail_set:
                return cand
    return candidates[0] if candidates else default


def is_bucket_activated(
    bucket: dict[str, Any] | None,
    window_seconds: int,
    now_ts: float | None = None,
    freeze_grace_sec: int = 180,
) -> bool:
    """Return True iff a quota bucket has genuinely started/frozen its window."""
    if not bucket or bucket.get("unavailable"):
        return False
    if "available" in bucket and not bucket.get("available"):
        return False

    frac = bucket.get("fraction")
    if frac is None:
        frac = bucket.get("remaining_fraction")
    if frac is not None:
        try:
            if float(frac) < 0.999:
                return True
        except (TypeError, ValueError):
            pass

    desc = str(bucket.get("description") or "").strip().lower()
    if "used some" in desc:
        return True

    reset_str = str(bucket.get("resetTime") or bucket.get("reset_time") or "").strip()
    if reset_str:
        try:
            dt = datetime.datetime.fromisoformat(reset_str.replace("Z", "+00:00"))
            now = now_ts if now_ts is not None else time.time()
            rem_sec = dt.timestamp() - now
            if 0 < rem_sec < (window_seconds - freeze_grace_sec):
                return True
        except (TypeError, ValueError):
            pass
    return False


def evaluate_claude_5h_session(
    api_data: dict[str, Any] | None,
    now_utc: datetime.datetime | None = None,
) -> tuple[bool, int, int, str]:
    """Evaluate whether Claude 5H rolling window is active.

    Anthropic returns five_hour.resets_at == null when idle and sets a future
    timestamp once a session begins, even when utilization rounds to 0%.
    Returns (is_active, rem_sec_5h, resets_at_ts, local_reset_str).
    """
    data = api_data or {}
    five_h = data.get("five_hour") or {}
    utilization_5h = float(five_h.get("utilization") or 0)
    resets_at_iso = str(five_h.get("resets_at") or "").strip()
    limits = data.get("limits") or []
    session_limit_active = any(
        isinstance(item, dict)
        and item.get("kind") == "session"
        and bool(item.get("is_active"))
        for item in limits
    )
    now_ref = now_utc or datetime.datetime.now(datetime.timezone.utc)
    rem_sec_5h = 0
    resets_at_ts = 0
    local_reset = ""
    if resets_at_iso:
        try:
            dt_5h = datetime.datetime.fromisoformat(resets_at_iso.replace("Z", "+00:00"))
            resets_at_ts = int(dt_5h.timestamp())
            local_reset = dt_5h.astimezone().strftime("%H:%M:%S")
            rem_sec_5h = max(0, int((dt_5h - now_ref).total_seconds()))
        except (TypeError, ValueError):
            pass
    is_active = bool(
        (rem_sec_5h > 0 and (utilization_5h > 0 or session_limit_active or rem_sec_5h <= 5 * 3600 + 60))
        or (session_limit_active and not resets_at_iso)
    )
    return is_active, rem_sec_5h, resets_at_ts, local_reset


def is_codex_5h_active(
    rate_limit: dict[str, Any] | None,
    grace_sec: int = 30,
) -> tuple[bool, int, int, float]:
    """Evaluate whether Codex 5H primary_window is active.

    Idle Codex accounts report used_percent == 0 and reset_after_seconds == limit_window_seconds.
    Returns (is_active, rem_sec, window_sec, used_percent).
    """
    pw = (rate_limit or {}).get("primary_window") or {}
    p_used = float(pw.get("used_percent") or 0)
    p_rem_sec = int(pw.get("reset_after_seconds") or 0)
    p_win_sec = int(pw.get("limit_window_seconds") or 5 * 3600) or (5 * 3600)
    is_active = bool(
        p_rem_sec > 0 and (p_used > 0 or p_rem_sec < max(1, p_win_sec - grace_sec))
    )
    return is_active, p_rem_sec, p_win_sec, p_used


def _get_claude_access_token() -> str | None:
    """Resolve Claude OAuth access token from env, Keychain, or ~/.claude/.credentials.json."""
    env_tok = (os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or "").strip()
    if env_tok:
        return env_tok
    if Path(REAL_HOME).resolve() == Path(_derive_real_home()).resolve():
        try:
            user = os.environ.get("USER", "danhdueexoictif")
            proc = subprocess.run(
                ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            if proc.returncode != 0:
                proc = subprocess.run(
                    ["security", "find-generic-password", "-s", "Claude Code-credentials", "-a", user, "-w"],
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                )
            if proc.returncode == 0 and proc.stdout:
                raw = proc.stdout.strip()
                if raw.startswith("{") and raw.endswith("}"):
                    oauth = json.loads(raw).get("claudeAiOauth", {})
                    tok = (oauth.get("accessToken") or "").strip()
                    exp = oauth.get("expiresAt") or 0
                    if tok and (exp == 0 or exp > int(time.time() * 1000) + 60000):
                        return tok
        except Exception:
            pass
    cred_file = Path(REAL_HOME) / ".claude" / ".credentials.json"
    if cred_file.is_file():
        try:
            oauth = json.loads(cred_file.read_text(encoding="utf-8")).get("claudeAiOauth", {})
            tok = (oauth.get("accessToken") or "").strip()
            if tok:
                return tok
        except Exception:
            pass
    return None


def _fetch_live_claude_usage() -> dict[str, Any] | None:
    """Query Anthropic live OAuth usage API and refresh ~/.claude.json cache when present."""
    token = _get_claude_access_token()
    if not token:
        return None
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "claude-cli/2.1.231",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "anthropic-beta": "claude-code-20250219",
        }
        req = urllib.request.Request("https://api.anthropic.com/api/oauth/usage", headers=headers)
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            if getattr(resp, "status", 200) == 200:
                raw_data = json.loads(resp.read().decode("utf-8"))
                usage = raw_data.get("utilization", raw_data)
                if isinstance(usage, dict):
                    _update_claude_cache_file(usage)
                    return usage
    except Exception:
        pass
    return None


def _update_claude_cache_file(usage: dict[str, Any]) -> None:
    """Persist live Claude usage into ~/.claude.json cachedUsageUtilization if file exists."""
    claude_json = Path(REAL_HOME) / ".claude.json"
    if not claude_json.is_file():
        return
    try:
        data = json.loads(claude_json.read_text(encoding="utf-8"))
        uuid = data.get("oauthAccount", {}).get("accountUuid", "")
        data["cachedUsageUtilization"] = {
            "fetchedAtMs": int(time.time() * 1000),
            "accountUuid": uuid,
            "utilization": usage,
        }
        claude_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def _fetch_live_codex_usage() -> dict[str, Any] | None:
    """Query ChatGPT Codex wham/usage endpoint; return rate_limit dict or None on failure."""
    auth_json = Path(REAL_HOME) / ".codex" / "auth.json"
    if not auth_json.is_file():
        return None
    try:
        tokens = json.loads(auth_json.read_text(encoding="utf-8")).get("tokens", {})
        token = tokens.get("access_token")
        account_id = tokens.get("account_id")
        if not token:
            return None
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "codex/0.167.0",
            "Accept": "application/json",
        }
        if account_id:
            headers["ChatGPT-Account-ID"] = account_id
        req = urllib.request.Request("https://chatgpt.com/backend-api/wham/usage", headers=headers)
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            api_data = json.loads(resp.read().decode("utf-8"))
            rl = api_data.get("rate_limit")
            return rl if isinstance(rl, dict) else None
    except Exception:
        return None


def _clean_host_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Build a sanitized environment free of leaked IDE/profile IPC variables."""
    env = (base_env if base_env is not None else os.environ).copy()
    strip_exact = {
        "AGY_PROFILE",
        "AGY_CLI_MODE",
        "AGY_ENABLE_HUB",
        "ANTIGRAVITY_AGENT",
        "ELECTRON_RUN_AS_NODE",
        "CHROME_DESKTOP",
        "TERM_PROGRAM",
        "TERM_PROGRAM_VERSION",
        "TERM_SESSION_ID",
        "TMPDIR",
        "ZDOTDIR",
    }
    for k in list(env.keys()):
        if k in strip_exact or k.startswith(("VSCODE_", "ANTIGRAVITY_")):
            env.pop(k, None)
    env["HOME"] = REAL_HOME
    env["REAL_HOME"] = REAL_HOME
    return env


def _clean_host_path(raw_path: str | None = None) -> str:
    """Return a clean PATH stripped of sandboxed antigravity_homes/<profile> segments."""
    required = [
        "/opt/homebrew/bin",
        "/usr/local/bin",
        str(REAL_HOME_DIR / ".local" / "bin"),
        "/usr/bin",
        "/bin",
        "/usr/sbin",
        "/sbin",
    ]
    parts = [p for p in (raw_path or "").split(":") if p and "/antigravity_homes/" not in p]
    ordered: list[str] = []
    for p in required + parts:
        if p and p not in ordered:
            ordered.append(p)
    return ":".join(ordered)


def is_target_session_active(target_name: str) -> tuple[bool, str]:
    """Check if session is currently active. Returns (is_active, message)."""
    now_ts = int(time.time())

    # 1. Claude check (Live API first, fallback to ~/.claude.json cachedUsageUtilization)
    if target_name == "claude":
        usage = _fetch_live_claude_usage()
        if usage is None:
            claude_json = Path(REAL_HOME) / ".claude.json"
            if claude_json.is_file():
                try:
                    c = json.loads(claude_json.read_text(encoding="utf-8"))
                    cached_u = c.get("cachedUsageUtilization", {}).get("utilization")
                    if isinstance(cached_u, dict):
                        usage = cached_u
                except Exception:
                    pass
        if isinstance(usage, dict):
            is_act, rem, _, loc = evaluate_claude_5h_session(usage)
            if is_act:
                loc_str = f", reset at {loc}" if loc else ""
                return True, f"Session active ({rem // 3600}h {(rem % 3600) // 60}m remaining{loc_str})"

    # 2. Codex check (Live wham/usage API authoritative when reachable; SQLite fallback when offline)
    if target_name == "codex":
        rate_limit = _fetch_live_codex_usage()
        if rate_limit is not None:
            is_act, rem, _, _ = is_codex_5h_active(rate_limit)
            if is_act:
                loc = datetime.datetime.fromtimestamp(now_ts + rem).strftime("%H:%M:%S")
                return True, f"Session active ({rem // 3600}h {(rem % 3600) // 60}m remaining, reset at {loc})"
            return False, ""

        codex_sqlite = Path(REAL_HOME) / ".codex" / "logs_2.sqlite"
        if codex_sqlite.is_file():
            con = None
            try:
                con = sqlite3.connect(str(codex_sqlite), timeout=2.0)
                cur = con.cursor()
                cur.execute("SELECT max(ts) FROM logs;")
                row = cur.fetchone()
                if row and row[0]:
                    max_ts = row[0]
                    delta = now_ts - max_ts
                    if delta < 5 * 3600:
                        rem = 5 * 3600 - delta
                        loc = datetime.datetime.fromtimestamp(max_ts + 5 * 3600).strftime("%H:%M:%S")
                        return True, f"Session active ({rem // 3600}h {(rem % 3600) // 60}m remaining, reset at {loc})"
            except Exception:
                pass
            finally:
                if con is not None:
                    con.close()

    return False, ""


def get_known_profiles() -> list[str]:
    """Discover all Antigravity profile accounts from antigravity_homes or ~/.zshrc."""
    profiles: list[str] = []
    homes_dir = Path(REAL_HOME) / "antigravity_homes"
    if homes_dir.is_dir():
        for d in homes_dir.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                profiles.append(d.name)
    zshrc_path = Path(REAL_HOME) / ".zshrc"
    if zshrc_path.is_file():
        try:
            content = zshrc_path.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                m = re.match(r"^alias\s+([a-zA-Z0-9_-]+)=.*antigravity_homes", line)
                if m:
                    p = m.group(1)
                    if p not in profiles:
                        profiles.append(p)
        except Exception:
            pass
    return sorted(profiles)


SUPPORTED_TARGETS = tuple(["claude", "codex", "all", "clis", "providers", "profiles"] + get_known_profiles())


def validate_target(target_val: str | list[str]) -> str:
    """Validate single target or comma/space-separated list of targets."""
    if isinstance(target_val, list):
        target_val = ",".join(target_val)
    s = target_val.strip()
    if not s:
        return "providers"
    tokens = [t.strip() for t in re.split(r"[\s,]+", s) if t.strip()]
    known = set(SUPPORTED_TARGETS) | set(get_known_profiles())
    for t in tokens:
        if t not in known:
            raise argparse.ArgumentTypeError(
                f"Unknown target '{t}'. Supported targets: {', '.join(sorted(known))}"
            )
    return ",".join(tokens)

def _resolve_darwin_dirs(real_home: str | Path | None = None) -> tuple[Path, Path]:
    """Resolve LaunchAgents and log directories under real user HOME (never sandboxed HOME)."""
    base = Path(real_home) if real_home else Path(_derive_real_home())
    return base / "Library" / "LaunchAgents", base / ".devtool" / "logs"


def _default_dashboard_html_candidates() -> list[Path]:
    """Return candidate paths to quota_dashboard.html in priority order."""
    script_dir = Path(__file__).resolve()
    candidates = [
        script_dir.parents[3] / "check-quota" / "resources" / "dashboard" / "quota_dashboard.html",
        REAL_HOME_DIR / ".gemini" / "config" / "plugins" / "d3nexus" / "skills" / "check-quota" / "resources" / "dashboard" / "quota_dashboard.html",
        REAL_HOME_DIR / "Projects" / "ai-agent-tools" / "skills" / "check-quota" / "resources" / "dashboard" / "quota_dashboard.html",
    ]
    return candidates


REAL_HOME_DIR = Path(_derive_real_home())
DARWIN_LABEL = "com.d3nexus.refresh-session"
DARWIN_PLIST_DIR, LOG_DIR = _resolve_darwin_dirs(REAL_HOME_DIR)
DARWIN_PLIST_PATH = DARWIN_PLIST_DIR / f"{DARWIN_LABEL}.plist"
SESSION_DB_PATH = REAL_HOME_DIR / ".gemini" / "antigravity" / ".session_store.db"
_DASHBOARD_HTML_CANDIDATES = _default_dashboard_html_candidates()
CRON_START_MARKER = "# BEGIN d3nexus-refresh-session"
CRON_END_MARKER = "# END d3nexus-refresh-session"


def parse_flexible_time(time_str: str) -> tuple[int, int]:
    """Parse flexible time strings into (hour, minute) in 24-hour time.

    Accepts:
    - 24-hour time: "05:00", "5:00", "14:30", "9:15", "00:00", "23:59"
    - Short hours: "5h", "6H", "14h", "5", "6"
    - 12-hour AM/PM: "5am", "5:30am", "6pm", "12pm", "12am"
    """
    s = time_str.strip()
    if not s:
        raise ValueError("Empty time string provided")

    # 1. 12-hour AM/PM format (e.g. "5am", "5:30am", "12pm", "6:15pm")
    ampm_match = re.match(r"^([1-9]|1[0-2])(?::([0-5][0-9]))?\s*([aApP][mM])$", s)
    if ampm_match:
        raw_h = int(ampm_match.group(1))
        raw_m = int(ampm_match.group(2) or 0)
        period = ampm_match.group(3).lower()
        if period == "pm" and raw_h != 12:
            raw_h += 12
        elif period == "am" and raw_h == 12:
            raw_h = 0
        return raw_h, raw_m

    # 2. 24-hour HH:MM format (e.g. "05:00", "5:00", "14:30")
    colon_match = re.match(r"^([0-9]{1,2}):([0-9]{2})$", s)
    if colon_match:
        raw_h = int(colon_match.group(1))
        raw_m = int(colon_match.group(2))
        if 0 <= raw_h <= 23 and 0 <= raw_m <= 59:
            return raw_h, raw_m
        raise ValueError(f"Time out of 24-hour range: '{s}'")

    # 3. Short hour format with 'h' (e.g. "5h", "6H", "14h")
    h_match = re.match(r"^([0-9]{1,2})[hH]$", s)
    if h_match:
        raw_h = int(h_match.group(1))
        if 0 <= raw_h <= 23:
            return raw_h, 0
        raise ValueError(f"Hour out of 24-hour range: '{s}'")

    # 4. Single or double digit hour integer (e.g. "5", "6", "14")
    int_match = re.match(r"^([0-9]{1,2})$", s)
    if int_match:
        raw_h = int(int_match.group(1))
        if 0 <= raw_h <= 23:
            return raw_h, 0
        raise ValueError(f"Hour out of 24-hour range: '{s}'")

    raise ValueError(
        f"Invalid time format '{time_str}'. Expected '05:00', '5h', '6am', or '14:30'."
    )


def _slot_label(hour: int, minute: int, delay: int = 30) -> str:
    """Return unique LaunchAgent label for a schedule time slot + delay."""
    return f"{DARWIN_LABEL}.{hour:02d}{minute:02d}-d{delay}"


def _clean_broken_launchagent_symlinks(plist_dir: Path) -> None:
    """Remove broken symlinks under LaunchAgents belonging to refresh-session."""
    if not plist_dir.is_dir():
        return
    try:
        for entry in plist_dir.glob(f"{DARWIN_LABEL}*.plist"):
            if entry.is_symlink() and not entry.exists():
                entry.unlink(missing_ok=True)
    except OSError:
        pass


def _iter_managed_plist_paths() -> list[Path]:
    """Return all existing managed LaunchAgent plist files on disk cleanly."""
    candidates: list[Path] = []
    seen_keys: set[str] = set()
    if DARWIN_PLIST_DIR.is_dir():
        for entry in sorted(DARWIN_PLIST_DIR.glob(f"{DARWIN_LABEL}*.plist")):
            if entry.exists() and not (entry.is_symlink() and not entry.exists()):
                candidates.append(entry)
                seen_keys.add(str(entry))
    if DARWIN_PLIST_PATH.exists() and str(DARWIN_PLIST_PATH) not in seen_keys:
        candidates.append(DARWIN_PLIST_PATH)
    return candidates


def _parse_plist_targets(items: list[str]) -> tuple[str, int]:
    """Extract target string and delay integer from ProgramArguments items."""
    target = "providers"
    delay = 30
    pos_args: list[str] = []
    i = 2
    while i < len(items):
        arg = items[i]
        if arg in ("--delay", "--offset") and i + 1 < len(items):
            try:
                delay = int(items[i + 1])
            except ValueError:
                pass
            i += 2
            continue
        if arg == "--target" and i + 1 < len(items):
            target = items[i + 1]
            i += 2
            continue
        pos_args.append(arg)
        i += 1
    if pos_args and target == "providers":
        target = pos_args[0]
    return target, delay


def _parse_plist_schedule(plist_path: Path) -> dict[str, Any]:
    """Parse LaunchAgent plist metadata using plistlib with minimal-XML regex fallback."""
    try:
        content = plist_path.read_text(encoding="utf-8", errors="ignore") if plist_path.exists() else ""
    except OSError:
        content = ""
    raw_bytes = content.encode("utf-8", errors="ignore")
    label = plist_path.stem
    hour: int | None = None
    minute: int | None = None
    target = "providers"
    delay = 30

    try:
        parsed = plistlib.loads(raw_bytes)
        if isinstance(parsed, dict):
            label = str(parsed.get("Label") or label)
            cal = parsed.get("StartCalendarInterval")
            if isinstance(cal, dict):
                hour = int(cal["Hour"]) if "Hour" in cal else None
                minute = int(cal.get("Minute", 0))
            prog = parsed.get("ProgramArguments")
            if isinstance(prog, list):
                target, delay = _parse_plist_targets([str(x) for x in prog])
    except Exception:
        h_match = re.search(r"<key>Hour</key>\s*<integer>(\d+)</integer>", content)
        m_match = re.search(r"<key>Minute</key>\s*<integer>(\d+)</integer>", content)
        if not h_match:
            int_matches = re.findall(r"<integer>(\d+)</integer>", content)
            hour = int(int_matches[0]) if len(int_matches) >= 1 else None
            minute = int(int_matches[1]) if len(int_matches) >= 2 else None
        else:
            hour = int(h_match.group(1))
            minute = int(m_match.group(1)) if m_match else 0

        lbl_match = re.search(r"<key>Label</key>\s*<string>(.*?)</string>", content)
        if lbl_match:
            label = lbl_match.group(1).strip()

        args_block = re.search(r"<key>ProgramArguments</key>\s*<array>(.*?)</array>", content, re.DOTALL)
        if args_block:
            items = re.findall(r"<string>(.*?)</string>", args_block.group(1))
            target, delay = _parse_plist_targets(items)
        else:
            delay_match = re.search(r"<string>--(?:delay|offset)</string>\s*<string>(\d+)</string>", content)
            delay = int(delay_match.group(1)) if delay_match else (30 if "<key>Hour</key>" in content else 0)

    targets_list = [t.strip() for t in re.split(r"[\s,]+", target) if t.strip()]
    return {
        "label": label,
        "plist_path": str(plist_path),
        "hour": hour,
        "minute": minute if minute is not None else 0,
        "time": f"{hour:02d}:{(minute or 0):02d}" if hour is not None else None,
        "delay": delay,
        "target": ",".join(targets_list) if targets_list else target,
        "targets": targets_list,
    }


def build_darwin_plist(
    script_path: str,
    hour: int,
    minute: int,
    target: str = "providers",
    delay: int = 30,
    label: str = DARWIN_LABEL,
) -> str:
    """Generate launchd plist XML for macOS with sanitized REAL_HOME environment and clean PATH."""
    resolved_script = str(Path(script_path).resolve())
    python_bin = sys.executable or "/usr/bin/python3"
    log_out = str((LOG_DIR / "refresh_session_daemon.log").resolve())
    log_err = str((LOG_DIR / "refresh_session_daemon.err").resolve())
    real_home_str = str(REAL_HOME_DIR)
    env_path = _clean_host_path(os.environ.get("PATH"))

    delay_xml = (
        f"""\n        <string>--delay</string>\n        <string>{delay}</string>"""
        if delay > 0
        else ""
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{_xml_escape(label)}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{_xml_escape(python_bin)}</string>
        <string>{_xml_escape(resolved_script)}</string>
        <string>{_xml_escape(target)}</string>{delay_xml}
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>HOME</key>
        <string>{_xml_escape(real_home_str)}</string>
        <key>REAL_HOME</key>
        <string>{_xml_escape(real_home_str)}</string>
        <key>PATH</key>
        <string>{_xml_escape(env_path)}</string>
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>{minute}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{_xml_escape(log_out)}</string>
    <key>StandardErrorPath</key>
    <string>{_xml_escape(log_err)}</string>
</dict>
</plist>
"""


def _darwin_reload_plist(label: str, plist_path: Path) -> str | None:
    """Unload existing label (best-effort) and bootstrap plist into gui/<uid>. Returns error or None."""
    domain = f"gui/{os.getuid()}"
    subprocess.run(
        ["launchctl", "bootout", f"{domain}/{label}"],
        capture_output=True,
        check=False,
        text=True,
    )
    boot_proc = subprocess.run(
        ["launchctl", "bootstrap", domain, str(plist_path)],
        capture_output=True,
        check=False,
        text=True,
    )
    if boot_proc.returncode == 0:
        return None
    load_proc = subprocess.run(
        ["launchctl", "load", "-w", str(plist_path)],
        capture_output=True,
        check=False,
        text=True,
    )
    if load_proc.returncode == 0:
        return None
    return (boot_proc.stderr or load_proc.stderr or boot_proc.stdout or f"launchctl failed ({boot_proc.returncode})").strip()


def _darwin_bootout_plist(label: str, plist_path: Path) -> None:
    """Unload a LaunchAgent from gui/<uid> with legacy fallback on genuine errors."""
    domain = f"gui/{os.getuid()}"
    proc = subprocess.run(
        ["launchctl", "bootout", f"{domain}/{label}"],
        capture_output=True,
        check=False,
        text=True,
    )
    err_low = (proc.stderr or "").lower()
    if proc.returncode != 0 and "could not find" not in err_low and "no such process" not in err_low:
        subprocess.run(
            ["launchctl", "unload", str(plist_path)],
            capture_output=True,
            check=False,
        )


def install_schedule_darwin(
    hour: int,
    minute: int,
    target: str = "providers",
    delay: int = 30,
    script_path: str | None = None,
    merge: bool = True,
) -> dict[str, Any]:
    """Install or update a per-slot LaunchAgent on macOS supporting multi-schedule targets."""
    if script_path is None:
        script_path = str(Path(__file__).resolve())

    DARWIN_PLIST_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _clean_broken_launchagent_symlinks(DARWIN_PLIST_DIR)

    label = _slot_label(hour, minute, delay)
    plist_path = DARWIN_PLIST_DIR / f"{label}.plist"

    incoming = [t.strip() for t in re.split(r"[\s,]+", str(target)) if t.strip()] or ["providers"]
    existing_targets: list[str] = []
    if merge and plist_path.exists():
        try:
            existing_targets = _parse_plist_schedule(plist_path).get("targets", [])
        except Exception:
            existing_targets = []
    merged_list = list(dict.fromkeys(existing_targets + incoming))
    merged_target = ",".join(merged_list)

    plist_content = build_darwin_plist(
        script_path,
        hour=hour,
        minute=minute,
        target=merged_target,
        delay=delay,
        label=label,
    )
    plist_path.write_text(plist_content, encoding="utf-8")
    try:
        if plist_path.exists():
            os.chmod(plist_path, 0o644)
    except OSError:
        pass

    error_msg = _darwin_reload_plist(label, plist_path)
    return {
        "success": error_msg is None,
        "platform": "darwin",
        "label": label,
        "hour": hour,
        "minute": minute,
        "time": f"{hour:02d}:{minute:02d}",
        "target": merged_target,
        "targets": merged_list,
        "delay": delay,
        "plist_path": str(plist_path),
        "error": error_msg,
    }


def get_schedule_status_darwin() -> dict[str, Any]:
    """Get multi-schedule status of all managed LaunchAgents on macOS."""
    _clean_broken_launchagent_symlinks(DARWIN_PLIST_DIR)
    plist_paths = _iter_managed_plist_paths()
    if not plist_paths:
        return {
            "success": True,
            "platform": "darwin",
            "installed": False,
            "loaded": False,
            "hour": None,
            "minute": None,
            "target": None,
            "delay": None,
            "plist_path": str(DARWIN_PLIST_PATH),
            "schedules": [],
            "by_profile": {},
        }

    check_proc = subprocess.run(
        ["launchctl", "list"], capture_output=True, text=True, check=False
    )
    loaded_labels: set[str] = set()
    if check_proc.returncode == 0:
        for line in (check_proc.stdout or "").splitlines():
            cols = line.strip().split()
            if cols and cols[-1].startswith(DARWIN_LABEL):
                loaded_labels.add(cols[-1])

    schedules: list[dict[str, Any]] = []
    by_profile: dict[str, list[dict[str, Any]]] = {}
    for plist_path in plist_paths:
        info = _parse_plist_schedule(plist_path)
        lbl = info["label"]
        info["loaded"] = lbl in loaded_labels or (lbl == DARWIN_LABEL and DARWIN_LABEL in (check_proc.stdout or ""))
        schedules.append(info)
        for prof in info.get("targets", []):
            by_profile.setdefault(prof, []).append({
                "label": lbl,
                "time": info["time"],
                "hour": info["hour"],
                "minute": info["minute"],
                "delay": info["delay"],
                "plist_path": info["plist_path"],
                "loaded": info["loaded"],
            })

    schedules.sort(key=lambda s: ((s["hour"] if s["hour"] is not None else 99), s["minute"], s["delay"], s["label"]))
    first = schedules[0]
    return {
        "success": True,
        "platform": "darwin",
        "installed": True,
        "loaded": any(s["loaded"] for s in schedules),
        "hour": first["hour"],
        "minute": first["minute"],
        "target": first["target"],
        "delay": first["delay"],
        "plist_path": first["plist_path"],
        "schedules": schedules,
        "by_profile": by_profile,
    }


def uninstall_schedule_darwin(
    target: str | None = None,
    time_str: str | None = None,
    delay: int | None = None,
) -> dict[str, Any]:
    """Uninstall all managed LaunchAgents or surgically remove target(s)/time slot(s)."""
    _clean_broken_launchagent_symlinks(DARWIN_PLIST_DIR)
    filter_hm: tuple[int, int] | None = None
    if time_str:
        filter_hm = parse_flexible_time(time_str)

    drop_targets = (
        {t.strip() for t in re.split(r"[\s,]+", str(target)) if t.strip()}
        if target
        else set()
    )

    removed: list[str] = []
    updated: list[str] = []
    script_path = str(Path(__file__).resolve())

    for plist_path in _iter_managed_plist_paths():
        info = _parse_plist_schedule(plist_path)
        if filter_hm is not None and (info["hour"], info["minute"]) != filter_hm:
            continue
        if delay is not None and info["delay"] != delay:
            continue

        lbl = info["label"]
        if drop_targets:
            current_targets = info.get("targets", [])
            remaining = [t for t in current_targets if t not in drop_targets]
            if len(remaining) == len(current_targets):
                continue
            if remaining and info["hour"] is not None:
                new_target = ",".join(remaining)
                new_xml = build_darwin_plist(
                    script_path,
                    hour=int(info["hour"]),
                    minute=int(info["minute"] or 0),
                    target=new_target,
                    delay=int(info["delay"] or 0),
                    label=lbl,
                )
                plist_path.write_text(new_xml, encoding="utf-8")
                _darwin_reload_plist(lbl, plist_path)
                updated.append(lbl)
                continue

        _darwin_bootout_plist(lbl, plist_path)
        if plist_path.exists() or plist_path.is_symlink():
            plist_path.unlink(missing_ok=True)
        removed.append(lbl)

    return {
        "success": True,
        "platform": "darwin",
        "plist_path": str(DARWIN_PLIST_PATH),
        "removed": removed,
        "updated": updated,
    }


def install_schedule_linux(
    hour: int,
    minute: int,
    target: str = "providers",
    delay: int = 30,
    script_path: str | None = None,
) -> dict[str, Any]:
    """Install user crontab job on Linux with safety delay buffer."""
    if script_path is None:
        script_path = str(Path(__file__).resolve())
    python_bin = sys.executable or "/usr/bin/python3"
    log_file = LOG_DIR / "refresh_session_daemon.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    delay_arg = f" --delay {delay}" if delay > 0 else ""
    cron_line = f"{minute} {hour} * * * {python_bin} {script_path} {target}{delay_arg} >> {log_file} 2>&1"

    cur_proc = subprocess.run(
        ["crontab", "-l"], capture_output=True, text=True, check=False
    )
    cur_cron = cur_proc.stdout if cur_proc.returncode == 0 else ""

    pattern = rf"{re.escape(CRON_START_MARKER)}.*?{re.escape(CRON_END_MARKER)}\n?"
    cleaned_cron = re.sub(pattern, "", cur_cron, flags=re.DOTALL).rstrip()

    new_block = (
        f"\n{CRON_START_MARKER}\n{cron_line}\n{CRON_END_MARKER}\n"
        if cleaned_cron
        else f"{CRON_START_MARKER}\n{cron_line}\n{CRON_END_MARKER}\n"
    )
    full_cron = (cleaned_cron + new_block).strip() + "\n"

    set_proc = subprocess.run(
        ["crontab", "-"], input=full_cron, text=True, capture_output=True, check=False
    )
    return {
        "success": set_proc.returncode == 0,
        "platform": "linux",
        "hour": hour,
        "minute": minute,
        "target": target,
        "delay": delay,
        "error": set_proc.stderr.strip() if set_proc.returncode != 0 else None,
    }


def get_schedule_status_linux() -> dict[str, Any]:
    """Check status of crontab job on Linux."""
    cur_proc = subprocess.run(
        ["crontab", "-l"], capture_output=True, text=True, check=False
    )
    if cur_proc.returncode != 0 or CRON_START_MARKER not in cur_proc.stdout:
        return {
            "installed": False,
            "loaded": False,
            "hour": None,
            "minute": None,
            "target": None,
            "delay": None,
        }

    pattern = (
        rf"{re.escape(CRON_START_MARKER)}\n(\d+)\s+(\d+)\s+\*\s+\*\s+\*\s+"
        rf".*?([a-zA-Z0-9_-]+)?(?:\s+--(?:delay|offset)\s+(\d+))?\s*>>"
    )
    match = re.search(pattern, cur_proc.stdout)
    if match:
        minute = int(match.group(1))
        hour = int(match.group(2))
        target = match.group(3) or "providers"
        delay = int(match.group(4)) if match.group(4) else 30
        return {
            "installed": True,
            "loaded": True,
            "hour": hour,
            "minute": minute,
            "target": target,
            "delay": delay,
        }
    return {
        "installed": True,
        "loaded": True,
        "hour": None,
        "minute": None,
        "target": "providers",
        "delay": 30,
    }


def uninstall_schedule_linux() -> dict[str, Any]:
    """Remove user crontab job on Linux."""
    cur_proc = subprocess.run(
        ["crontab", "-l"], capture_output=True, text=True, check=False
    )
    if cur_proc.returncode == 0 and CRON_START_MARKER in cur_proc.stdout:
        pattern = rf"{re.escape(CRON_START_MARKER)}.*?{re.escape(CRON_END_MARKER)}\n?"
        cleaned = re.sub(pattern, "", cur_proc.stdout, flags=re.DOTALL).rstrip() + "\n"
        subprocess.run(
            ["crontab", "-"], input=cleaned, text=True, capture_output=True, check=False
        )
    return {"success": True, "platform": "linux"}


def install_schedule(
    hour: int, minute: int, target: str = "providers", delay: int = 30
) -> dict[str, Any]:
    """Install daily schedule dispatching to darwin or linux with delay buffer."""
    if sys.platform == "darwin":
        return install_schedule_darwin(hour, minute, target=target, delay=delay)
    return install_schedule_linux(hour, minute, target=target, delay=delay)


def get_schedule_status() -> dict[str, Any]:
    """Query daily schedule status dispatching to darwin or linux."""
    if sys.platform == "darwin":
        return get_schedule_status_darwin()
    return get_schedule_status_linux()


def uninstall_schedule(
    target: str | None = None, time_str: str | None = None, delay: int | None = None
) -> dict[str, Any]:
    """Uninstall daily schedule dispatching to darwin or linux."""
    if sys.platform == "darwin":
        return uninstall_schedule_darwin(target=target, time_str=time_str, delay=delay)
    return uninstall_schedule_linux()


def build_claude_command(prompt: str = "1", model: str = "haiku") -> list[str]:
    """Construct minimal sandboxed Claude Code CLI command.

    Disables CLAUDE.md, skills, plugins, tools, and hooks while preserving OAuth auth.
    """
    return [
        "claude",
        "--safe-mode",
        "--disable-slash-commands",
        "--tools",
        "",
        "--model",
        model,
        "-p",
        prompt,
    ]


def build_codex_command(prompt: str = "1", reasoning_effort: str = "low") -> list[str]:
    """Construct minimal sandboxed Codex CLI command.

    Bypasses git repository checks, user configs, plugins, and custom rules.
    """
    return [
        "codex",
        "exec",
        "--disable",
        "plugins",
        "--disable",
        "apps",
        "--disable",
        "hooks",
        "--ephemeral",
        "--skip-git-repo-check",
        "--ignore-user-config",
        "--ignore-rules",
        "-c",
        f"model_reasoning_effort={reasoning_effort}",
        prompt,
    ]


def extract_tokens(output: str) -> int | None:
    """Extract token count from CLI output if reported."""
    patterns = [
        r"tokens used\s*\n\s*([0-9,]+)",
        r"(?:Tokens|tokens):\s*([0-9,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            clean_str = match.group(1).replace(",", "")
            try:
                return int(clean_str)
            except ValueError:
                pass
    return None


def ping_cli(cli_name: str, timeout: int = 60) -> dict[str, Any]:
    """Execute sandboxed minimal ping against the specified CLI inside an ephemeral directory.

    Returns a standardized dictionary matching:
    {"cli": str, "status": "PASS" | "SKIPPED" | "FAIL", "latency_ms": float, "tokens": int | None, "error": str | None}
    """
    result: dict[str, Any] = {
        "cli": cli_name,
        "status": "FAIL",
        "latency_ms": 0.0,
        "tokens": None,
        "error": None,
    }

    executable = shutil.which(cli_name)
    if not executable:
        result["status"] = "SKIPPED"
        result["error"] = f"Executable '{cli_name}' not found in PATH."
        return result

    if cli_name == "claude":
        cmd = build_claude_command(prompt="1", model="haiku")
    elif cli_name == "codex":
        cmd = build_codex_command(prompt="1", reasoning_effort="low")
    else:
        result["error"] = f"Unsupported CLI '{cli_name}'."
        return result

    start_time = time.perf_counter()
    with tempfile.TemporaryDirectory() as sandbox_dir:
        try:
            proc = subprocess.run(
                cmd,
                cwd=sandbox_dir,
                capture_output=True,
                check=False,
                text=True,
                timeout=timeout,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result["latency_ms"] = round(elapsed_ms, 2)

            combined_output = (proc.stdout or "") + "\n" + (proc.stderr or "")
            tokens = extract_tokens(combined_output)
            result["tokens"] = tokens

            if proc.returncode == 0:
                result["status"] = "PASS"
            else:
                err_msg = (proc.stderr or proc.stdout or "").strip()
                result["error"] = err_msg or f"Exited with return code {proc.returncode}"

        except subprocess.TimeoutExpired:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result["latency_ms"] = round(elapsed_ms, 2)
            result["status"] = "FAIL"
            result["error"] = f"Timed out after {timeout} seconds"
        except OSError as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result["latency_ms"] = round(elapsed_ms, 2)
            result["status"] = "FAIL"
            result["error"] = str(exc)

    return result


def check_profile_auth_token(profile: str) -> bool:
    """Check in ~8ms whether profile has an active gemini token in its keychain.
    If False, running agy will attempt to open web browser for OAuth!
    """
    kc = os.path.join(REAL_HOME, "antigravity_homes", profile, "Library/Keychains", f"{profile}.keychain-db")
    if not os.path.isfile(kc):
        return False
    subprocess.run(["security", "unlock-keychain", "-p", KC_PASS, kc], capture_output=True)
    res = subprocess.run(["security", "find-generic-password", "-s", "gemini", "-a", "antigravity", kc], capture_output=True)
    return res.returncode == 0


def check_profile_has_argon(profile: str) -> bool:
    """Check whether an Antigravity profile supports Argon model from cached dashboard data."""
    for p in _DASHBOARD_HTML_CANDIDATES:
        if p.is_file():
            try:
                content = p.read_text(encoding="utf-8")
                marker = "const PROFILES_DATA ="
                end_marker = "\n};"
                i1 = content.find(marker)
                if i1 != -1:
                    i2 = content.find(end_marker, i1)
                    if i2 != -1:
                        raw_json = content[i1 + len(marker):i2 + len(end_marker)].strip().rstrip(";")
                        data = json.loads(raw_json)
                        prof_data = data.get(profile, {})
                        return bool(prof_data.get("hasArgon") and not prof_data.get("argonWeekly", {}).get("unavailable", False))
            except Exception:
                pass
    return False


def _extract_usage_buckets(cmd_data: dict[str, Any]) -> dict[str, Any]:
    """Parse `/usage` command payload into normalized per-bucket state."""
    plan_raw = str(cmd_data.get("plan_name") or cmd_data.get("tier") or "").strip().upper()
    groups = cmd_data.get("groups") or []
    buckets: dict[str, Any] = {
        "has_groups": bool(groups),
        "tier": "FREE" if "FREE" in plan_raw else ("PRO" if groups else plan_raw or "PRO"),
        "gem_5h": {"available": False, "fraction": 1.0, "reset_time": "", "description": ""},
        "cld_5h": {"available": False, "fraction": 1.0, "reset_time": "", "description": ""},
        "argon_weekly": {"available": False, "fraction": 1.0, "reset_time": "", "description": ""},
    }
    for grp in groups:
        g_name = str(grp.get("name") or "").lower()
        for b in grp.get("buckets") or []:
            win = b.get("window")
            entry = {
                "available": True,
                "fraction": float(b.get("remaining_fraction", 1.0)),
                "reset_time": str(b.get("reset_time") or ""),
                "description": str(b.get("description") or ""),
            }
            if "gemini models" in g_name and win == "5h":
                buckets["gem_5h"] = entry
            elif "claude" in g_name and win == "5h":
                buckets["cld_5h"] = entry
            elif "argon" in g_name and win == "weekly":
                buckets["argon_weekly"] = entry

    has_5h = buckets["gem_5h"]["available"] or buckets["cld_5h"]["available"]
    if groups and not has_5h:
        buckets["tier"] = "FREE"
    return buckets


def _detect_appeal_in_output(text: str) -> bool:
    """Return True if agy CLI output indicates Terms of Service account disablement."""
    low = (text or "").lower()
    return (
        "submit an appeal" in low
        or "violation of terms of service" in low
        or "service has been disabled" in low
    )


def _probe_profile_usage_and_models(
    agy_bin: str,
    env: dict[str, str],
    cwd: str,
    timeout: int,
) -> tuple[dict[str, Any], list[str], bool]:
    """Query live `/usage` and `agy models` inside isolated cwd cleanly."""
    usage_buckets: dict[str, Any] = {"has_groups": False}
    available_models: list[str] = []
    is_appeal = False

    try:
        proc_usage = subprocess.run(
            [agy_bin, "--output-format", "json", "-p", "/usage"],
            env=env,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        combined = f"{proc_usage.stdout or ''}\n{proc_usage.stderr or ''}"
        if _detect_appeal_in_output(combined):
            return usage_buckets, available_models, True
        if proc_usage.returncode == 0 and proc_usage.stdout:
            try:
                parsed = json.loads(proc_usage.stdout.strip())
                cmd_data = parsed.get("command", {}).get("data", {})
                if isinstance(cmd_data, dict) and cmd_data.get("groups"):
                    usage_buckets = _extract_usage_buckets(cmd_data)
            except (TypeError, ValueError):
                pass
    except Exception:
        pass

    try:
        proc_models = subprocess.run(
            [agy_bin, "models"],
            env=env,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=min(timeout, 25),
        )
        if _detect_appeal_in_output(f"{proc_models.stdout or ''}\n{proc_models.stderr or ''}"):
            return usage_buckets, available_models, True
        if proc_models.returncode == 0 and proc_models.stdout:
            available_models = parse_agy_models_output(proc_models.stdout)
    except Exception:
        pass

    return usage_buckets, available_models, is_appeal


def _record_bucket_session(profile_name: str, bucket_suffix: str, window_seconds: int) -> None:
    """Persist per-bucket ping timestamp in SESSION_STORE_DB for propagation-lag tracing."""
    if not SESSION_STORE_DB.parent.is_dir():
        return
    con = None
    try:
        con = sqlite3.connect(str(SESSION_STORE_DB), timeout=2.0)
        now_ts = int(time.time())
        con.execute(
            """
            INSERT INTO session_store (profile_hash, reset_5h, reset_weekly, fraction_5h, last_checked, last_ping, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(profile_hash) DO UPDATE SET
                reset_5h=excluded.reset_5h,
                last_checked=excluded.last_checked,
                last_ping=excluded.last_ping,
                is_active=excluded.is_active;
            """,
            (hash_profile(f"{profile_name}:{bucket_suffix}"), now_ts + window_seconds, 0, 1.0, now_ts, now_ts, 1),
        )
        con.commit()
    except Exception:
        pass
    finally:
        if con is not None:
            con.close()


def _run_isolated_agy_model_ping(
    agy_bin: str,
    model_id: str,
    prompt: str,
    env: dict[str, str],
    cwd: str,
    timeout: int,
) -> tuple[bool, bool, str]:
    """Execute one sandboxed agy model ping. Returns (ok, is_appeal, error_msg)."""
    try:
        proc = subprocess.run(
            [agy_bin, "--disable-slash-commands", "--model", model_id, "-p", prompt],
            env=env,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        combined = f"{proc.stdout or ''}\n{proc.stderr or ''}"
        if _detect_appeal_in_output(combined):
            return False, True, "Profile is disabled for Terms of Service (Appeal needed)"
        if proc.returncode == 0:
            return True, False, ""
        err = (proc.stderr or proc.stdout or f"Exited with return code {proc.returncode}").strip()
        return False, False, err
    except subprocess.TimeoutExpired:
        return False, False, f"Timed out after {timeout}s ({model_id})"
    except Exception as exc:
        return False, False, str(exc)


def ping_profile(profile_name: str, timeout: int = 50) -> dict[str, Any]:
    """Check live quota & models and ping unactivated Gemini 5H, Claude 5H, and Argon 7D independently."""
    result: dict[str, Any] = {
        "cli": f"agy ({profile_name})",
        "profile": profile_name,
        "status": "FAIL",
        "latency_ms": 0.0,
        "tokens": 0,
        "error": None,
        "models_pinged": [],
        "details": {},
    }
    ag_home = f"{REAL_HOME}/antigravity_homes/{profile_name}"
    if not os.path.isdir(ag_home):
        result["status"] = "SKIPPED"
        result["error"] = f"Profile directory not found: {ag_home}"
        return result

    if not check_profile_auth_token(profile_name):
        result["status"] = "SKIPPED"
        result["error"] = "Profile is not authenticated in CLI keychain"
        return result

    marker_file = os.path.join(ag_home, ".gemini/antigravity/tos_disabled.json")
    if os.path.isfile(marker_file):
        result["status"] = "SKIPPED"
        result["error"] = "Profile is disabled for Terms of Service (Appeal needed)"
        return result

    log_dir = os.path.join(ag_home, ".gemini/antigravity/log")
    if os.path.isdir(log_dir):
        import glob
        logs = sorted(glob.glob(os.path.join(log_dir, "cli-*.log")), key=os.path.getmtime, reverse=True)
        for log_file in logs[:2]:
            try:
                with open(log_file, "rb") as f:
                    if _detect_appeal_in_output(f.read().decode("utf-8", errors="ignore")):
                        result["status"] = "SKIPPED"
                        result["error"] = "Profile is disabled for Terms of Service (Appeal needed)"
                        return result
            except Exception:
                pass

    profile_kc = f"{ag_home}/Library/Keychains/{profile_name}.keychain-db"
    if os.path.exists(profile_kc):
        subprocess.run(
            ["security", "unlock-keychain", "-p", KC_PASS, profile_kc],
            capture_output=True,
            check=False,
        )

    agy_bin = shutil.which("agy") or "/opt/homebrew/bin/agy"
    if not os.path.exists(agy_bin):
        result["status"] = "SKIPPED"
        result["error"] = "Antigravity CLI (agy) binary not found."
        return result

    tmpdir_path = f"/tmp/ag_{profile_name}"
    os.makedirs(tmpdir_path, exist_ok=True)
    env = _clean_host_env()
    env.update({
        "HOME": ag_home,
        "AGY_PROFILE": profile_name,
        "AGY_CLI_MODE": "1",
        "TMPDIR": tmpdir_path,
        "BROWSER": "true",
    })

    start_time = time.perf_counter()
    models_pinged: list[str] = []
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix=f"agy_ping_{profile_name}_") as sandbox_cwd:
        usage_buckets, available_models, appeal_detected = _probe_profile_usage_and_models(
            agy_bin, env=env, cwd=sandbox_cwd, timeout=min(timeout, 45)
        )
        if appeal_detected:
            result["status"] = "SKIPPED"
            result["error"] = "Profile is disabled for Terms of Service (Appeal needed)"
            return result

        if usage_buckets.get("has_groups") and usage_buckets.get("tier") == "FREE":
            result["status"] = "SKIPPED"
            result["error"] = "Profile is FREE tier (no 5H or Argon buckets)"
            result["latency_ms"] = round((time.perf_counter() - start_time) * 1000.0, 2)
            return result

        has_live = bool(usage_buckets.get("has_groups"))
        now_ts = time.time()

        gem_bucket = usage_buckets.get("gem_5h") if has_live else {"available": True}
        cld_bucket = usage_buckets.get("cld_5h") if has_live else {"available": True}
        if has_live:
            argon_bucket = usage_buckets["argon_weekly"]
            has_argon = bool(argon_bucket.get("available")) or any("argon" in m for m in available_models)
        else:
            has_argon = check_profile_has_argon(profile_name) or any("argon" in m for m in available_models)
            argon_bucket = {"available": has_argon}

        should_gem = bool(gem_bucket.get("available")) and not (has_live and is_bucket_activated(gem_bucket, 5 * 3600, now_ts=now_ts))
        should_cld = bool(cld_bucket.get("available")) and not (has_live and is_bucket_activated(cld_bucket, 5 * 3600, now_ts=now_ts))

        argon_near_reset = False
        if has_argon and has_live and argon_bucket.get("reset_time"):
            try:
                dt_a = datetime.datetime.fromisoformat(argon_bucket["reset_time"].replace("Z", "+00:00"))
                rem_a = dt_a.timestamp() - now_ts
                argon_near_reset = 0 < rem_a < 7 * 3600
            except Exception:
                pass
        should_argon = (
            has_argon
            and not argon_near_reset
            and not (has_live and is_bucket_activated(argon_bucket, 7 * 86400, now_ts=now_ts))
        )

        if not should_gem and not should_cld and not should_argon:
            result["status"] = "SKIPPED"
            result["error"] = "All eligible sessions already active (Gemini 5H / Claude 5H / Argon 7D)"
            result["latency_ms"] = round((time.perf_counter() - start_time) * 1000.0, 2)
            return result

        gem_model = select_model_from_candidates(available_models, GEMINI_MODEL_CANDIDATES, "gemini-3.8-flash-low")
        cld_model = select_model_from_candidates(available_models, CLAUDE_MODEL_CANDIDATES, "claude-sonnet-5-5-low")
        arg_model = select_model_from_candidates(available_models, ARGON_MODEL_CANDIDATES, "gemini-4-argon-low")

        targets_plan: list[tuple[str, str, str, int, tuple[float, float] | None]] = []
        if should_gem:
            targets_plan.append(("Gemini 5H", gem_model, "gem5h", 18000, None))
        if should_cld:
            targets_plan.append(("Claude 5H", cld_model, "cld5h", 18000, (1.5, 2.5)))
        if should_argon:
            targets_plan.append(("Argon 7D", arg_model, "argon7d", 7 * 86400, (1.8, 3.0)))

        used_prompts: set[str] = set()
        for idx, (label, model_id, store_key, store_win, jitter_range) in enumerate(targets_plan):
            if idx > 0 and jitter_range:
                time.sleep(round(random.uniform(*jitter_range), 2))
            prompt_pool = [p for p in NATURAL_PROMPTS if p not in used_prompts] or NATURAL_PROMPTS
            prompt = random.choice(prompt_pool)
            used_prompts.add(prompt)

            ok, is_appeal, err_msg = _run_isolated_agy_model_ping(
                agy_bin, model_id=model_id, prompt=prompt, env=env, cwd=sandbox_cwd, timeout=timeout
            )
            if is_appeal:
                result["status"] = "FAIL"
                result["error"] = err_msg
                result["latency_ms"] = round((time.perf_counter() - start_time) * 1000.0, 2)
                return result
            result["details"][label] = {"model": model_id, "ok": ok, "error": err_msg or None}
            if ok:
                models_pinged.append(label)
                _record_bucket_session(profile_name, store_key, store_win)
            else:
                failures.append(f"{label} ({model_id}): {err_msg}")

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    result["latency_ms"] = round(elapsed_ms, 2)
    result["models_pinged"] = models_pinged
    result["tokens"] = len(models_pinged)

    if failures:
        result["status"] = "FAIL"
        result["error"] = "; ".join(failures)
    elif len(models_pinged) > 0:
        result["status"] = "PASS"
    else:
        result["error"] = "No models pinged"

    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] == "schedule":
        sched_parser = argparse.ArgumentParser(
            prog="refresh_session.py schedule",
            description="Manage daily scheduled session pre-warming daemons.",
        )
        sched_parser.add_argument(
            "--time",
            type=str,
            help="Daily trigger time (e.g. '05:00', '5h', '6am', '14:30')",
        )
        sched_parser.add_argument(
            "--target",
            type=validate_target,
            default="providers",
            help="Target to schedule: 'providers' (default - Claude & Codex), 'profiles', 'all', or comma-separated list (e.g. 'danhdue,claude,codex')",
        )
        sched_parser.add_argument(
            "--delay",
            "--offset",
            dest="delay",
            type=int,
            default=30,
            help="Delay in seconds after the scheduled minute before pinging (default: 30)",
        )
        sched_parser.add_argument(
            "--status",
            action="store_true",
            help="Check active schedule status",
        )
        sched_parser.add_argument(
            "--uninstall",
            "--remove",
            dest="uninstall",
            action="store_true",
            help="Uninstall scheduled daemon",
        )
        sched_parser.add_argument(
            "--json",
            action="store_true",
            help="Emit structured JSON output",
        )
        parsed = sched_parser.parse_args(argv[1:])
        parsed.command = "schedule"
        try:
            parsed.target_explicit = any(
                a == "--target" or a.startswith("--target=") for a in argv[1:]
            )
            parsed.target = validate_target(parsed.target)
        except argparse.ArgumentTypeError as exc:
            sched_parser.error(str(exc))
        return parsed

    parser = argparse.ArgumentParser(
        description="Ping Claude Code or Codex CLI with minimal token consumption to refresh 5-hour rolling session windows.",
    )
    parser.add_argument(
        "target",
        nargs="*",
        default=["providers"],
        help="Target to ping: 'providers' (default - Claude & Codex), 'profiles', 'all', or comma/space-separated list (e.g. 'danhdue,claude,codex')",
    )
    parser.add_argument(
        "--delay",
        "--offset",
        dest="delay",
        type=int,
        default=0,
        help="Seconds to delay before pinging (default: 0)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds per CLI call (default: 60)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON output",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force session pre-warm even if session is already active",
    )
    parsed = parser.parse_args(argv)
    parsed.command = "refresh"
    try:
        raw_val = parsed.target if parsed.target else ["providers"]
        parsed.target = validate_target(raw_val)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    return parsed


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint."""
    args = parse_args(argv)

    if args.command == "schedule":
        if args.uninstall:
            has_explicit_target = getattr(args, "target_explicit", False)
            if has_explicit_target or args.time:
                res = uninstall_schedule(
                    target=args.target if has_explicit_target else None,
                    time_str=args.time,
                    delay=args.delay if args.delay != 30 else None,
                )
            else:
                res = uninstall_schedule()
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"Schedule daemon uninstalled successfully ({res.get('platform')}).")
            return 0 if res.get("success", False) else 1

        if args.status:
            status = get_schedule_status()
            if args.json:
                print(json.dumps(status, indent=2))
            else:
                if status.get("installed"):
                    schedules = status.get("schedules") or []
                    loaded_str = (
                        "loaded & active"
                        if status.get("loaded")
                        else "installed but not loaded"
                    )
                    print(f"Scheduled daemon: ACTIVE ({loaded_str})")
                    if len(schedules) > 1:
                        for item in schedules:
                            st = "LOADED" if item.get("loaded") else "NOT LOADED"
                            print(
                                f"  • {item.get('time')} daily (+{item.get('delay', 0)}s) | "
                                f"Target: {item.get('target')} | {st} ({item.get('label')})"
                            )
                    else:
                        h = status.get("hour")
                        m = status.get("minute", 0)
                        time_display = f"{h:02d}:{m:02d}" if h is not None else "Unknown"
                        target_display = status.get("target") or "all"
                        print(f"  • Trigger time: {time_display} daily")
                        print(f"  • Target:       {target_display}")
                        delay_val = status.get("delay")
                        if delay_val is not None:
                            print(f"  • Delay buffer: {delay_val}s")
                        if "plist_path" in status:
                            print(f"  • Config:       {status['plist_path']}")
                else:
                    print("Scheduled daemon: INACTIVE (No schedule configured)")
            return 0

        if args.time:
            try:
                hour, minute = parse_flexible_time(args.time)
            except ValueError as exc:
                if args.json:
                    print(json.dumps({"success": False, "error": str(exc)}, indent=2))
                else:
                    print(f"Error: {exc}", file=sys.stderr)
                return 1

            res = install_schedule(hour, minute, target=args.target, delay=args.delay)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                if res.get("success"):
                    print(
                        f"Successfully scheduled daily refresh at {hour:02d}:{minute:02d} "
                        f"(delay: {args.delay}s) for '{args.target}' ({res.get('platform')})."
                    )
                    if "plist_path" in res:
                        print(f"  • Plist: {res['plist_path']}")
                else:
                    print(f"Failed to install schedule: {res.get('error')}", file=sys.stderr)
            return 0 if res.get("success", False) else 1

        # If none of the schedule flags provided, show error
        print(
            "Usage: refresh_session.py schedule (--time TIME | --status | --uninstall) "
            "[--target TARGET] [--delay SECONDS] [--json]",
            file=sys.stderr,
        )
        return 1

    if args.delay > 0:
        if not args.json:
            print(f"Waiting {args.delay}s delay buffer after reset minute...")
        time.sleep(args.delay)

    known_profiles = get_known_profiles()
    raw_target_str = ",".join(args.target) if isinstance(args.target, list) else str(args.target)
    validated_str = validate_target(raw_target_str)
    raw_targets = [t.strip() for t in validated_str.split(",") if t.strip()]
    targets_to_ping: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add_target(kind: str, name: str):
        if (kind, name) not in seen:
            seen.add((kind, name))
            targets_to_ping.append((kind, name))

    for t in raw_targets:
        if t == "all":
            add_target("cli", "claude")
            add_target("cli", "codex")
            for p in known_profiles:
                add_target("profile", p)
        elif t in ("providers", "clis"):
            add_target("cli", "claude")
            add_target("cli", "codex")
        elif t == "profiles":
            for p in known_profiles:
                add_target("profile", p)
        elif t in ("claude", "codex"):
            add_target("cli", t)
        elif t in known_profiles:
            add_target("profile", t)

    results: list[dict[str, Any]] = []

    for kind, target_name in targets_to_ping:
        if not args.json:
            display_name = target_name if kind == "profile" else target_name.title()
            print(f"Pinging {display_name} in isolated environment...")

        if not getattr(args, "force", False):
            is_active, active_msg = is_target_session_active(target_name)
            if is_active:
                results.append({
                    "cli": f"agy ({target_name})" if kind == "profile" else target_name,
                    "profile": target_name if kind == "profile" else None,
                    "status": "SKIPPED",
                    "latency_ms": 1.0,
                    "tokens": 0,
                    "error": active_msg,
                })
                continue

        if kind == "profile":
            res = ping_profile(target_name, timeout=args.timeout)
        else:
            res = ping_cli(target_name, timeout=args.timeout)
            if res.get("status") == "PASS":
                _record_bucket_session(target_name, "5h", 18000)
        results.append(res)

    has_fail = any(r["status"] == "FAIL" for r in results)
    overall_status = "FAIL" if has_fail else "PASS"

    if args.json:
        report = {
            "overall_status": overall_status,
            "results": results,
        }
        print(json.dumps(report, indent=2))
    else:
        print("\nSession Refresh Summary:")
        for r in results:
            name = r.get("profile") or r["cli"].title()
            status = r["status"]
            latency = f"{r['latency_ms']:.1f}ms"
            tokens = f"{r['tokens']} tokens" if r["tokens"] is not None else "minimal tokens"

            if status == "PASS":
                print(f"  • {name}: PASS ({latency}, {tokens})")
            elif status == "SKIPPED":
                print(f"  • {name}: SKIPPED ({r.get('error')})")
            else:
                print(f"  • {name}: FAIL ({r.get('error')})")

        if not has_fail:
            print("\nSession refresh complete. 5-hour rolling quota window is active.")

    return 1 if has_fail else 0


if __name__ == "__main__":
    sys.exit(main())
