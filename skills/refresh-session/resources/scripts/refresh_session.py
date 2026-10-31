#!/usr/bin/env python3
"""Standalone script to ping Claude Code and Codex CLIs to refresh 5-hour rolling session windows.

Enforces zero skill initialization, zero workspace context, and minimum token consumption
by executing strictly inside an ephemeral isolated temporary directory.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SUPPORTED_TARGETS = ("claude", "codex", "all")

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


def build_darwin_plist(script_path: str, hour: int, minute: int, target: str = "all") -> str:
    """Generate launchd plist XML for macOS with absolute paths and full PATH environment."""
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
        <string>{target}</string>
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
    hour: int, minute: int, target: str = "all", script_path: str | None = None
) -> dict[str, Any]:
    """Install launchd agent on macOS."""
    if script_path is None:
        script_path = str(Path(__file__).resolve())

    DARWIN_PLIST_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    plist_content = build_darwin_plist(script_path, hour=hour, minute=minute, target=target)
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

    target_match = re.search(r"<string>(all|claude|codex)</string>", content)
    target = target_match.group(1) if target_match else "all"

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
    hour: int, minute: int, target: str = "all", script_path: str | None = None
) -> dict[str, Any]:
    """Install user crontab job on Linux."""
    if script_path is None:
        script_path = str(Path(__file__).resolve())
    python_bin = sys.executable or "/usr/bin/python3"
    log_file = LOG_DIR / "refresh_session_daemon.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    cron_line = f"{minute} {hour} * * * {python_bin} {script_path} {target} >> {log_file} 2>&1"

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
        }

    pattern = rf"{re.escape(CRON_START_MARKER)}\n(\d+)\s+(\d+)\s+\*\s+\*\s+\*\s+.*?(all|claude|codex)?\s*>>"
    match = re.search(pattern, cur_proc.stdout)
    if match:
        minute = int(match.group(1))
        hour = int(match.group(2))
        target = match.group(3) or "all"
        return {
            "installed": True,
            "loaded": True,
            "hour": hour,
            "minute": minute,
            "target": target,
        }
    return {
        "installed": True,
        "loaded": True,
        "hour": None,
        "minute": None,
        "target": "all",
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


def install_schedule(hour: int, minute: int, target: str = "all") -> dict[str, Any]:
    """Install daily schedule dispatching to darwin or linux."""
    if sys.platform == "darwin":
        return install_schedule_darwin(hour, minute, target=target)
    return install_schedule_linux(hour, minute, target=target)


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
            choices=SUPPORTED_TARGETS,
            default="all",
            help="Target CLI to schedule: 'claude', 'codex', or 'all' (default: 'all')",
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
        return parsed

    parser = argparse.ArgumentParser(
        description="Ping Claude Code or Codex CLI with minimal token consumption to refresh 5-hour rolling session windows.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="all",
        choices=SUPPORTED_TARGETS,
        help="Target CLI to ping: 'claude', 'codex', or 'all' (default: 'all')",
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
    parsed = parser.parse_args(argv)
    parsed.command = "refresh"
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

            res = install_schedule(hour, minute, target=args.target)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                if res.get("success"):
                    print(
                        f"Successfully scheduled daily refresh at {hour:02d}:{minute:02d} "
                        f"for '{args.target}' ({res.get('platform')})."
                    )
                    if "plist_path" in res:
                        print(f"  • Plist: {res['plist_path']}")
                else:
                    print(f"Failed to install schedule: {res.get('error')}", file=sys.stderr)
            return 0 if res.get("success", False) else 1

        # If none of the schedule flags provided, show error
        print(
            "Usage: refresh_session.py schedule (--time TIME | --status | --uninstall) "
            "[--target TARGET] [--json]",
            file=sys.stderr,
        )
        return 1

    targets = ["claude", "codex"] if args.target == "all" else [args.target]
    results: list[dict[str, Any]] = []

    for target in targets:
        if not args.json:
            print(f"Pinging {target.title()} CLI in isolated sandbox...")
        res = ping_cli(target, timeout=args.timeout)
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
            cli_name = r["cli"].title()
            status = r["status"]
            latency = f"{r['latency_ms']:.1f}ms"
            tokens = f"{r['tokens']} tokens" if r["tokens"] is not None else "minimal tokens"

            if status == "PASS":
                print(f"  • {cli_name}: PASS ({latency}, {tokens})")
            elif status == "SKIPPED":
                print(f"  • {cli_name}: SKIPPED ({r.get('error')})")
            else:
                print(f"  • {cli_name}: FAIL ({r.get('error')})")

        if not has_fail:
            print("\nSession refresh complete. 5-hour rolling quota window is active.")

    return 1 if has_fail else 0


if __name__ == "__main__":
    sys.exit(main())
