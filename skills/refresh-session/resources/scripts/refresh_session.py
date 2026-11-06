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
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REAL_HOME = "/Users/danhdueexoictif"
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


def is_target_session_active(target_name: str) -> tuple[bool, str]:
    """Check if session is currently active. Returns (is_active, message)."""
    now_ts = int(time.time())

    # 1. Claude check
    if target_name == "claude":
        claude_json = Path(REAL_HOME) / ".claude.json"
        if claude_json.is_file():
            try:
                with open(claude_json, "r", encoding="utf-8") as f:
                    c = json.load(f)
                five_h = c.get("cachedUsageUtilization", {}).get("utilization", {}).get("five_hour") or {}
                resets_at = five_h.get("resets_at")
                util = five_h.get("utilization", 0)
                if resets_at and util > 0:
                    dt = datetime.datetime.fromisoformat(resets_at.replace("Z", "+00:00"))
                    now_utc = datetime.datetime.now(datetime.timezone.utc)
                    rem = int((dt - now_utc).total_seconds())
                    if rem > 0:
                        loc = dt.astimezone().strftime("%H:%M:%S")
                        return True, f"Session active ({rem // 3600}h {(rem % 3600) // 60}m remaining, reset at {loc})"
            except Exception:
                pass

    # 2. Codex check
    if target_name == "codex":
        codex_sqlite = Path(REAL_HOME) / ".codex" / "logs_2.sqlite"
        if codex_sqlite.is_file():
            try:
                con = sqlite3.connect(str(codex_sqlite), timeout=2.0)
                cur = con.cursor()
                cur.execute("SELECT max(ts) FROM logs;")
                row = cur.fetchone()
                con.close()
                if row and row[0]:
                    max_ts = row[0]
                    delta = now_ts - max_ts
                    if delta < 5 * 3600:
                        rem = 5 * 3600 - delta
                        loc = datetime.datetime.fromtimestamp(max_ts + 5 * 3600).strftime("%H:%M:%S")
                        return True, f"Session active ({rem // 3600}h {(rem % 3600) // 60}m remaining, reset at {loc})"
            except Exception:
                pass

    # 3. Check .session_store.db for Antigravity or any target
    if SESSION_STORE_DB.is_file():
        try:
            con = sqlite3.connect(str(SESSION_STORE_DB), timeout=2.0)
            cur = con.cursor()
            cur.execute("SELECT reset_5h, is_active FROM session_store WHERE profile_hash = ?", (hash_profile(target_name),))
            row = cur.fetchone()
            con.close()
            if row and row[1] and row[0] > now_ts:
                rem = row[0] - now_ts
                loc = datetime.datetime.fromtimestamp(row[0]).strftime("%H:%M:%S")
                return True, f"Session active ({rem // 3600}h {(rem % 3600) // 60}m remaining, reset at {loc})"
        except Exception:
            pass

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
    known = set(SUPPORTED_TARGETS)
    for t in tokens:
        if t not in known:
            raise argparse.ArgumentTypeError(
                f"Unknown target '{t}'. Supported targets: {', '.join(sorted(known))}"
            )
    return ",".join(tokens)

DARWIN_LABEL = "com.d3nexus.refresh-session"
DARWIN_PLIST_DIR = Path.home() / "Library" / "LaunchAgents"
DARWIN_PLIST_PATH = DARWIN_PLIST_DIR / f"{DARWIN_LABEL}.plist"
LOG_DIR = Path.home() / ".devtool" / "logs"
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


def build_darwin_plist(
    script_path: str, hour: int, minute: int, target: str = "providers", delay: int = 30
) -> str:
    """Generate launchd plist XML for macOS with absolute paths, delay buffer, and full PATH environment."""
    resolved_script = str(Path(script_path).resolve())
    python_bin = sys.executable or "/usr/bin/python3"
    log_out = str((LOG_DIR / "refresh_session_daemon.log").resolve())
    log_err = str((LOG_DIR / "refresh_session_daemon.err").resolve())

    standard_paths = [
        "/opt/homebrew/bin",
        "/usr/local/bin",
        str(Path.home() / ".local" / "bin"),
        "/usr/bin",
        "/bin",
        "/usr/sbin",
        "/sbin",
    ]
    env_path = os.environ.get("PATH", ":".join(standard_paths))
    for p in standard_paths:
        if p not in env_path:
            env_path = f"{p}:{env_path}"

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
    <string>{DARWIN_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_bin}</string>
        <string>{resolved_script}</string>
        <string>{target}</string>{delay_xml}
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>{env_path}</string>
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>{minute}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{log_out}</string>
    <key>StandardErrorPath</key>
    <string>{log_err}</string>
</dict>
</plist>
"""


def install_schedule_darwin(
    hour: int,
    minute: int,
    target: str = "providers",
    delay: int = 30,
    script_path: str | None = None,
) -> dict[str, Any]:
    """Install launchd agent on macOS with safety delay buffer."""
    if script_path is None:
        script_path = str(Path(__file__).resolve())

    DARWIN_PLIST_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    plist_content = build_darwin_plist(
        script_path, hour=hour, minute=minute, target=target, delay=delay
    )
    DARWIN_PLIST_PATH.write_text(plist_content)

    subprocess.run(
        ["launchctl", "unload", str(DARWIN_PLIST_PATH)],
        capture_output=True,
        check=False,
    )
    load_proc = subprocess.run(
        ["launchctl", "load", str(DARWIN_PLIST_PATH)],
        capture_output=True,
        check=False,
        text=True,
    )

    success = load_proc.returncode == 0
    error_msg = load_proc.stderr.strip() if not success else None
    return {
        "success": success,
        "platform": "darwin",
        "hour": hour,
        "minute": minute,
        "target": target,
        "delay": delay,
        "plist_path": str(DARWIN_PLIST_PATH),
        "error": error_msg,
    }


def get_schedule_status_darwin() -> dict[str, Any]:
    """Get status of launchd agent on macOS."""
    if not DARWIN_PLIST_PATH.exists():
        return {
            "installed": False,
            "loaded": False,
            "hour": None,
            "minute": None,
            "target": None,
            "delay": None,
            "plist_path": str(DARWIN_PLIST_PATH),
        }

    content = DARWIN_PLIST_PATH.read_text()
    h_match = re.search(r"<key>Hour</key>\s*<integer>(\d+)</integer>", content)
    m_match = re.search(r"<key>Minute</key>\s*<integer>(\d+)</integer>", content)

    if not h_match:
        int_matches = re.findall(r"<integer>(\d+)</integer>", content)
        hour = int(int_matches[0]) if len(int_matches) >= 1 else None
        minute = int(int_matches[1]) if len(int_matches) >= 2 else None
    else:
        hour = int(h_match.group(1)) if h_match else None
        minute = int(m_match.group(1)) if m_match else 0

    args_block = re.search(r"<key>ProgramArguments</key>\s*<array>(.*?)</array>", content, re.DOTALL)
    if args_block:
        items = re.findall(r"<string>(.*?)</string>", args_block.group(1))
        target = items[2] if len(items) >= 3 else "providers"
    else:
        target_match = re.search(r"<string>([a-zA-Z0-9_-]+)</string>", content)
        target = target_match.group(1) if target_match else "providers"

    delay_match = re.search(
        r"<string>--(?:delay|offset)</string>\s*<string>(\d+)</string>", content
    )
    delay = int(delay_match.group(1)) if delay_match else (30 if "<key>Hour</key>" in content else 0)

    check_proc = subprocess.run(
        ["launchctl", "list"], capture_output=True, text=True, check=False
    )
    loaded = check_proc.returncode == 0 and DARWIN_LABEL in (check_proc.stdout or "")

    return {
        "installed": True,
        "loaded": loaded,
        "hour": hour,
        "minute": minute,
        "target": target,
        "delay": delay,
        "plist_path": str(DARWIN_PLIST_PATH),
    }


def uninstall_schedule_darwin() -> dict[str, Any]:
    """Uninstall launchd agent on macOS."""
    subprocess.run(
        ["launchctl", "unload", str(DARWIN_PLIST_PATH)],
        capture_output=True,
        check=False,
    )
    if DARWIN_PLIST_PATH.exists():
        DARWIN_PLIST_PATH.unlink()
    return {
        "success": True,
        "platform": "darwin",
        "plist_path": str(DARWIN_PLIST_PATH),
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


def uninstall_schedule() -> dict[str, Any]:
    """Uninstall daily schedule dispatching to darwin or linux."""
    if sys.platform == "darwin":
        return uninstall_schedule_darwin()
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


def ping_profile(profile_name: str, timeout: int = 25) -> dict[str, Any]:
    """Execute sandboxed minimal 1-token / usage ping for an Antigravity profile.

    Sets isolated HOME, AGY_PROFILE, TMPDIR, and unlocks profile keychain.
    """
    result: dict[str, Any] = {
        "cli": f"agy ({profile_name})",
        "profile": profile_name,
        "status": "FAIL",
        "latency_ms": 0.0,
        "tokens": 0,
        "error": None,
    }
    ag_home = f"{REAL_HOME}/antigravity_homes/{profile_name}"
    if not os.path.isdir(ag_home):
        result["status"] = "SKIPPED"
        result["error"] = f"Profile directory not found: {ag_home}"
        return result

    # Prevent agy from opening browser if profile has no CLI auth token
    if not check_profile_auth_token(profile_name):
        result["status"] = "SKIPPED"
        result["error"] = "Profile is not authenticated in CLI keychain"
        return result

    # Fast skip if profile was disabled for Terms of Service violation (submit an appeal)
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
                    content = f.read().decode("utf-8", errors="ignore").lower()
                    if "submit an appeal" in content or "violation of terms of service" in content:
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

    env = os.environ.copy()
    env.update({
        "HOME": ag_home,
        "AGY_PROFILE": profile_name,
        "AGY_CLI_MODE": "1",
        "TMPDIR": f"/tmp/ag_{profile_name}",
    })

    start_time = time.perf_counter()
    prompt = random.choice(NATURAL_PROMPTS)
    try:
        proc = subprocess.run(
            [agy_bin, "-p", prompt],
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        result["latency_ms"] = round(elapsed_ms, 2)
        if proc.returncode == 0:
            result["status"] = "PASS"
            result["tokens"] = 1
            # Update session store
            try:
                con = sqlite3.connect(str(SESSION_STORE_DB), timeout=2.0)
                now_ts = int(time.time())
                con.execute("""
                    INSERT INTO session_store (profile_hash, reset_5h, reset_weekly, fraction_5h, last_checked, last_ping, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(profile_hash) DO UPDATE SET
                        reset_5h=excluded.reset_5h,
                        last_checked=excluded.last_checked,
                        last_ping=excluded.last_ping,
                        is_active=excluded.is_active;
                """, (hash_profile(profile_name), now_ts + 18000, 0, 1.0, now_ts, now_ts, 1))
                con.commit()
                con.close()
            except Exception:
                pass
        else:
            err_msg = (proc.stderr or proc.stdout or "").strip()
            result["error"] = err_msg or f"Exited with return code {proc.returncode}"
    except subprocess.TimeoutExpired:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        result["latency_ms"] = round(elapsed_ms, 2)
        result["status"] = "FAIL"
        result["error"] = f"Timed out after {timeout} seconds"
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        result["latency_ms"] = round(elapsed_ms, 2)
        result["status"] = "FAIL"
        result["error"] = str(exc)

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
                    h = status.get("hour")
                    m = status.get("minute", 0)
                    time_display = f"{h:02d}:{m:02d}" if h is not None else "Unknown"
                    target_display = status.get("target") or "all"
                    loaded_str = (
                        "loaded & active"
                        if status.get("loaded")
                        else "installed but not loaded"
                    )
                    print(f"Scheduled daemon: ACTIVE ({loaded_str})")
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
