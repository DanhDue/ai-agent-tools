#!/usr/bin/env python3
"""
Antigravity Quota Dashboard with Card-style Progress Bars.

Color Rules:
  >= 50%           : GREEN (#72bc82)
  >= 10% and < 50% : AMBER (#f59e0b)
  < 10%            : RED   (#ef4444)

Usage:
  agy-quota                 # Check current active profile
  agy-quota <profile>       # Check specific profile (e.g. danhdue, mommy)
  agy-quota all             # Check all profiles from ~/.zshrc
  agy-quota all --table     # Compact table summary for all profiles
"""

import sys
import os
import re
import json
import time
import datetime
import subprocess
import signal
import http.server
import socketserver
import urllib.parse
import urllib.request
import sqlite3
import hashlib
import random
import shlex
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ANSI Colors & Styling
GREEN       = "\033[38;2;114;188;130m"      # Soft Green (#72bc82)
AMBER       = "\033[38;2;245;158;11m"       # Amber / Orange (#f59e0b)
RED         = "\033[38;2;239;68;68m"        # Red (#ef4444)
GRAY        = "\033[38;2;148;163;184m"      # Slate / Gray (#94a3b8)
DIM         = "\033[38;2;100;116;139m"      # Slate-500 Dim (#64748b)
BORDER      = "\033[38;2;51;65;85m"         # Border color (#334155)
TRACK_GRAY  = "\033[38;2;30;41;59m"         # Deep Slate (#1e293b)
WHITE       = "\033[1;37m"                  # Bold White
CYAN        = "\033[38;2;56;189;248m"       # Cyan (#38bdf8)
TIMER       = "\033[38;2;251;191;36m"       # Gold / Amber Timer (#fbbf24)
RESET       = "\033[0m"
BOLD        = "\033[1m"

# Model & Status Badges
TAG_PRO      = "\033[48;2;59;102;245m\033[1;37m ◆ PRO \033[0m"
TAG_PRIORITY = "\033[48;2;24;27;38m\033[38;2;160;174;192m Priority: 50 \033[0m"
TAG_ARGON    = "\033[48;2;38;25;56m\033[38;2;192;132;252m ✣ Argon \033[0m"
TAG_HIGH     = "\033[48;2;76;29;149m\033[38;2;216;180;254m High \033[0m"
TAG_MED      = "\033[48;2;30;58;138m\033[38;2;191;219;254m Med \033[0m"
TAG_LOW      = "\033[48;2;15;23;42m\033[38;2;148;163;184m Low \033[0m"
TAG_INACTIVE = "\033[48;2;30;41;59m\033[38;2;148;163;184m INACTIVE \033[0m"

def _derive_real_home() -> str:
    """Host user's real HOME, derived (never hard-coded); strips /antigravity_homes/<profile> when inside a profile."""
    home = os.environ.get("REAL_HOME") or os.path.expanduser("~")
    return home.split("/antigravity_homes")[0] if "/antigravity_homes" in home else home


REAL_HOME = _derive_real_home()
KC_PASS = "H@No!a@12345"
AGY_BIN = "/opt/homebrew/bin/agy"
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


GLOBAL_REFRESH_INTERVAL_SECONDS = 1800  # 30 minutes


def wait_for_launch_lock(timeout: float = 3.0) -> None:
    """Wait if any profile is currently in its 1.5s atomic launch window."""
    lock_dir = "/tmp/ag_launch.lock"
    if os.path.exists(lock_dir):
        start = time.time()
        while os.path.exists(lock_dir) and (time.time() - start < timeout):
            time.sleep(0.1)


def build_clean_host_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Return a clean host environment stripped of leaked IDE, Electron, and profile variables."""
    env = dict(os.environ if base_env is None else base_env)
    env["HOME"] = REAL_HOME
    for exact_key in (
        "AGY_PROFILE",
        "AGY_CLI_MODE",
        "AGY_ENABLE_HUB",
        "TERM_PROGRAM",
        "TERM_PROGRAM_VERSION",
        "TERM_SESSION_ID",
        "TMPDIR",
        "ZDOTDIR",
    ):
        env.pop(exact_key, None)
    for key in list(env.keys()):
        if key.startswith(("VSCODE_", "ANTIGRAVITY_", "ELECTRON_", "CHROME_")):
            env.pop(key, None)
    return env


def init_session_store_db():
    try:
        SESSION_STORE_DB.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(str(SESSION_STORE_DB))
        con.execute("""
        CREATE TABLE IF NOT EXISTS session_store (
            profile_hash TEXT PRIMARY KEY,
            reset_5h INTEGER NOT NULL,
            reset_weekly INTEGER NOT NULL,
            fraction_5h REAL NOT NULL,
            last_checked INTEGER NOT NULL,
            last_ping INTEGER NOT NULL,
            is_active INTEGER NOT NULL
        );
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS system_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)
        con.commit()
        con.close()
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to init session_store.db: {e}\n")


def get_global_meta(key: str, default: str = "") -> str:
    init_session_store_db()
    try:
        con = sqlite3.connect(str(SESSION_STORE_DB), timeout=5.0)
        cur = con.cursor()
        cur.execute("SELECT value FROM system_metadata WHERE key = ?", (key,))
        row = cur.fetchone()
        con.close()
        return row[0] if row else default
    except Exception:
        return default


def set_global_meta(key: str, value: str):
    init_session_store_db()
    try:
        con = sqlite3.connect(str(SESSION_STORE_DB), timeout=5.0)
        cur = con.cursor()
        cur.execute("""
            INSERT INTO system_metadata (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value;
        """, (key, value))
        con.commit()
        con.close()
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to set global meta: {e}\n")


def get_last_refresh_all_time() -> int:
    val = get_global_meta("last_refresh_all_timestamp", "0")
    try:
        return int(val)
    except ValueError:
        return 0


def record_refresh_all_time(ts: int | None = None):
    now = int(ts or time.time())
    set_global_meta("last_refresh_all_timestamp", str(now))


def hash_profile(name: str) -> str:
    return hashlib.sha256(f"{SALT}:{name}".encode("utf-8")).hexdigest()[:24]


def save_session_record(profile: str, reset_5h: int, reset_weekly: int, fraction_5h: float, is_active: bool, last_ping: int | None = None):
    init_session_store_db()
    h = hash_profile(profile)
    now = int(time.time())
    try:
        con = sqlite3.connect(str(SESSION_STORE_DB), timeout=5.0)
        cur = con.cursor()
        cur.execute("""
            INSERT INTO session_store (profile_hash, reset_5h, reset_weekly, fraction_5h, last_checked, last_ping, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(profile_hash) DO UPDATE SET
                reset_5h=excluded.reset_5h,
                reset_weekly=excluded.reset_weekly,
                fraction_5h=excluded.fraction_5h,
                last_checked=excluded.last_checked,
                last_ping=COALESCE(excluded.last_ping, session_store.last_ping),
                is_active=excluded.is_active;
        """, (h, int(reset_5h), int(reset_weekly), float(fraction_5h), now, int(last_ping or now), 1 if is_active else 0))
        con.commit()
        con.close()
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to save session record: {e}\n")


def get_session_record(profile: str) -> dict | None:
    init_session_store_db()
    h = hash_profile(profile)
    try:
        con = sqlite3.connect(str(SESSION_STORE_DB), timeout=5.0)
        cur = con.cursor()
        cur.execute("SELECT reset_5h, reset_weekly, fraction_5h, last_checked, last_ping, is_active FROM session_store WHERE profile_hash = ?", (h,))
        row = cur.fetchone()
        con.close()
        if not row:
            return None
        return {
            "reset_5h": row[0],
            "reset_weekly": row[1],
            "fraction_5h": row[2],
            "last_checked": row[3],
            "last_ping": row[4],
            "is_active": bool(row[5]),
        }
    except Exception:
        return None


def get_color(pct: float) -> str:
    """Return ANSI color based on quota percentage."""
    if pct >= 50.0:
        return GREEN
    elif pct >= 10.0:
        return AMBER
    else:
        return RED


def get_color_pair(pct: float) -> tuple:
    """Return (active_fill_color, consumed_track_color) based on quota percentage."""
    if pct >= 50.0:
        return GREEN, "\033[38;2;22;101;52m"     # Deep Forest Green (#166534)
    elif pct >= 10.0:
        return AMBER, "\033[38;2;120;53;15m"     # Deep Amber (#78350f)
    else:
        return RED, "\033[38;2;127;29;29m"       # Deep Crimson (#7f1d1d)


def str_vis_width(s: str) -> int:
    """Compute visual terminal width ignoring ANSI escape codes."""
    w = 0
    in_esc = False
    for ch in s:
        if ch == "\033":
            in_esc = True
            continue
        if in_esc:
            if ch == "m":
                in_esc = False
            continue
        if ch in ("⏱", "⏳"):
            w += 2
        else:
            w += 1
    return w


def format_countdown(reset_time_str: str) -> str:
    """Calculate remaining time to full reset from now."""
    if not reset_time_str:
        return "⏱ --"
    try:
        dt = datetime.datetime.fromisoformat(reset_time_str.replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = dt - now
        total_seconds = max(0, int(diff.total_seconds()))
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        if days > 0:
            return f"⏱ {days}d {hours}h"
        elif hours > 0:
            return f"⏱ {hours}h {minutes}m"
        elif minutes > 0:
            return f"⏱ {minutes}m"
        else:
            return "⏱ 0m"
    except Exception:
        return "⏱ --"


def render_card(icon: str, icon_color: str, title: str, timer_str: str, fraction: float, width: int = 45, tags: str = None, available: bool = True) -> list:
    """Render a card-style UI box with progress bar matching the reference image."""
    inner_w = width - 2

    # Top border
    top = f"{BORDER}╭" + "─" * inner_w + f"╮{RESET}"
    bot = f"{BORDER}╰" + "─" * inner_w + f"╯{RESET}"

    if not available:
        # Inactive / unavailable model: styled in slate gray with NO right text as requested
        left_styled = f" {DIM}{icon}{RESET} {DIM}{title}{RESET} {TAG_INACTIVE}"
        left_raw = f" {icon} {title}  INACTIVE "

        sp = max(1, inner_w - str_vis_width(left_raw) - 1)
        content = f"{BORDER}│{RESET}{left_styled}{' ' * sp}{BORDER}│{RESET}"
        bar_w = inner_w - 4
        bar_line = f"{BORDER}│{RESET}  [{BORDER}{'░' * bar_w}{RESET}]  {BORDER}│{RESET}"
        return [top, content, bar_line, bot]

    fraction = max(0.0, min(1.0, fraction))
    pct = fraction * 100.0
    color = get_color(pct)

    # Left text (icon + title + tags)
    left_styled = f" {icon_color}{icon}{RESET} {WHITE}{title}{RESET}"
    left_raw = f" {icon} {title}"
    if tags:
        left_styled += f" {tags}"
        left_raw += "  High   Med   Low "

    pct_text = f"{color}{pct:5.1f}%{RESET}"
    pct_raw = f"{pct:5.1f}%"

    timer_styled = f"{TIMER}{timer_str}{RESET}"
    timer_raw = timer_str

    vis_used = str_vis_width(left_raw) + str_vis_width(timer_raw) + str_vis_width(pct_raw)
    sp_total = max(2, inner_w - vis_used - 1)
    sp1 = max(1, sp_total // 2)
    sp2 = max(1, sp_total - sp1)

    content = f"{BORDER}│{RESET}{left_styled}{' ' * sp1}{timer_styled}{' ' * sp2}{pct_text} {BORDER}│{RESET}"

    # Progress bar line
    bar_w = inner_w - 4
    filled = int(round(fraction * bar_w))
    empty = bar_w - filled
    fill_color, track_color = get_color_pair(pct)
    bar_line = f"{BORDER}│{RESET}  [{fill_color}{'█' * filled}{RESET}{track_color}{'░' * empty}{RESET}]  {BORDER}│{RESET}"

    return [top, content, bar_line, bot]


RESERVED_NON_PROFILES = {
    "Library", "System", "Shared", "AllProjects", "Projects", "fvm",
    "claude", "codex", "kiro", "anthropic", "openai", ".gemini", ".antigravity",
    ".antigravity-ide"
}


def is_valid_antigravity_profile(profile_name: str, homes_dir: str | None = None) -> bool:
    """Validate whether a name corresponds to an actual Antigravity profile account."""
    if not profile_name or profile_name.startswith(".") or profile_name.startswith("-"):
        return False
    if profile_name in RESERVED_NON_PROFILES:
        return False
    if not re.match(r"^[a-zA-Z0-9_-]+$", profile_name):
        return False

    h_dir = homes_dir or f"{REAL_HOME}/antigravity_homes"
    ag_home = os.path.join(h_dir, profile_name)

    if not os.path.exists(ag_home) or os.path.islink(ag_home) or not os.path.isdir(ag_home):
        return False

    if profile_name == "default":
        zshrc_path = os.path.expanduser("~/.zshrc")
        if os.path.exists(zshrc_path):
            try:
                with open(zshrc_path, "r", encoding="utf-8", errors="ignore") as f:
                    if "ag_run default" not in f.read():
                        return False
            except Exception:
                return False
        else:
            return False

    has_gemini = os.path.exists(os.path.join(ag_home, ".gemini"))
    has_ag = os.path.exists(os.path.join(ag_home, ".antigravity"))
    has_data = os.path.exists(os.path.join(ag_home, "data"))
    has_kc = os.path.exists(os.path.join(ag_home, "Library/Keychains"))
    return bool(has_gemini or has_ag or has_data or has_kc)


def get_all_profiles() -> list:
    """Discover all actual Antigravity profile accounts directly from antigravity_homes directory."""
    profiles = []
    homes_dir = f"{REAL_HOME}/antigravity_homes"
    if os.path.isdir(homes_dir):
        for d in sorted(os.listdir(homes_dir)):
            if is_valid_antigravity_profile(d, homes_dir=homes_dir):
                profiles.append(d)

    # Also check ~/.zshrc for aliases as fallback or aliases with distinct names
    zshrc_path = os.path.expanduser("~/.zshrc")
    if os.path.exists(zshrc_path):
        try:
            with open(zshrc_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    m = re.search(r"antigravity_homes/([a-zA-Z0-9_-]+)", line)
                    if m:
                        p = m.group(1)
                        if is_valid_antigravity_profile(p, homes_dir=homes_dir) and p not in profiles:
                            profiles.append(p)
                    m2 = re.match(r"^alias\s+([a-zA-Z0-9_-]+)='ag_run\s+([a-zA-Z0-9_-]+)'", line.strip())
                    if m2:
                        p2 = m2.group(2)
                        if is_valid_antigravity_profile(p2, homes_dir=homes_dir) and p2 not in profiles:
                            profiles.append(p2)
        except Exception:
            pass

    return sorted(list(set(profiles)))


def get_profiles_from_zshrc() -> list:
    """Backward compatibility alias to get_all_profiles()."""
    return get_all_profiles()


LAST_BLOCKED_PROBE = {}


def unblock_profile(profile: str):
    """Clear disabled marker, archive historical appeal logs, and update in-memory cache."""
    marker_file = os.path.join(REAL_HOME, "antigravity_homes", profile, ".gemini/antigravity", "tos_disabled.json")
    if os.path.isfile(marker_file):
        try:
            os.remove(marker_file)
        except Exception:
            pass

    log_dir = os.path.join(REAL_HOME, "antigravity_homes", profile, ".gemini/antigravity/log")
    if os.path.isdir(log_dir):
        import glob
        for lf in glob.glob(os.path.join(log_dir, "cli-*.log")):
            try:
                with open(lf, "rb") as f:
                    content = f.read().decode("utf-8", errors="ignore").lower()
                if "submit an appeal" in content or "violation of terms of service" in content:
                    os.rename(lf, lf + ".resolved")
            except Exception:
                pass

    if CACHED_PROFILES_DATA and profile in CACHED_PROFILES_DATA:
        CACHED_PROFILES_DATA[profile]["isAppeal"] = False
        CACHED_PROFILES_DATA[profile]["status"] = "ACTIVE"


def probe_blocked_profile(profile: str) -> dict:
    """Safely test whether an individual blocked profile has been unblocked by Google.
    Includes anti-spam cooldown, randomized humanized jitter, token verification, and real model inference probe.
    """
    now = time.time()
    last_time = LAST_BLOCKED_PROBE.get(profile, 0)
    cooldown = 30  # 30 seconds cooldown per profile to prevent Google WAF rate-limit
    if (now - last_time) < cooldown:
        remaining = int(cooldown - (now - last_time))
        return {
            "profile": profile,
            "success": False,
            "status": "COOLDOWN",
            "cooldown": True,
            "error": f"Vui lòng đợi thêm {remaining}s trước khi kiểm tra lại tài khoản này để bảo vệ khỏi rate limit.",
            "remaining_cooldown": remaining
        }

    # 1. Verify auth token exists in keychain (PREVENTS BROWSER POPUP)
    if not check_profile_auth_token(profile):
        return {
            "profile": profile,
            "success": False,
            "status": "AUTH NEEDED",
            "is_auth_needed": True,
            "error": "Profile chưa có token xác thực trong Keychain. Cần đăng nhập CLI trước."
        }

    LAST_BLOCKED_PROBE[profile] = now

    # 2. Apply randomized humanized jitter (1.8s - 3.2s) to prevent bot detection
    jitter_sec = round(random.uniform(1.8, 3.2), 2)
    time.sleep(jitter_sec)

    ag_home = f"{REAL_HOME}/antigravity_homes/{profile}"
    profile_kc = f"{ag_home}/Library/Keychains/{profile}.keychain-db"
    if os.path.exists(profile_kc):
        subprocess.run(["security", "unlock-keychain", "-p", KC_PASS, profile_kc], capture_output=True)

    env = os.environ.copy()
    env.update({
        "HOME": ag_home,
        "AGY_PROFILE": profile,
        "AGY_CLI_MODE": "1",
        "TMPDIR": f"/tmp/ag_{profile}",
        "BROWSER": "true",
    })

    # 3. CRITICAL: Test real model inference with a lightweight prompt from NATURAL_PROMPTS
    # Google's /usage endpoint does NOT check the ToS model suspension flag!
    # Only sending a real generation prompt reveals whether the Gemini model is still disabled.
    prompt = random.choice(NATURAL_PROMPTS)
    cmd = [AGY_BIN, "-p", prompt]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=25)
        dur = round(time.time() - t0, 2)
        all_out = (proc.stdout or "") + " " + (proc.stderr or "")

        appeal_err_id = check_profile_appeal_status(profile, all_out)
        low_out = all_out.lower()
        is_blocked = (
            bool(appeal_err_id) or
            "submit an appeal" in low_out or
            "violation of terms of service" in low_out or
            "service has been disabled" in low_out or
            proc.returncode != 0
        )

        if is_blocked:
            err_id = appeal_err_id or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
            if not appeal_err_id:
                record_profile_disabled(profile, err_id)
            disabled_data = format_profile_for_dashboard(profile, {
                "success": False,
                "status": "DISABLED",
                "is_appeal": True,
                "error_id": err_id
            })
            update_cached_profile(profile, disabled_data)
            return {
                "profile": profile,
                "success": False,
                "status": "DISABLED",
                "is_appeal": True,
                "error_id": err_id,
                "duration": dur,
                "jitter": jitter_sec,
                "data": disabled_data,
                "error": f"Tài khoản {profile} vẫn đang bị Google tạm ngưng (ToS Violation). Vui lòng gửi đơn kháng nghị (Submit an appeal). Mã lỗi: {err_id}"
            }

        # 4. Prompt succeeded with returncode 0! Verify Argon as well if profile has Argon
        current = load_cached_profiles().get(profile, {})
        has_argon = current.get("hasArgon", False) and not current.get("argonWeekly", {}).get("unavailable", False)
        if has_argon:
            time.sleep(round(random.uniform(1.8, 3.2), 2))
            other_prompts = [p for p in NATURAL_PROMPTS if p != prompt] or NATURAL_PROMPTS
            prompt_argon = random.choice(other_prompts)
            cmd_arg = [AGY_BIN, "--model", "gemini-4-argon-low", "-p", prompt_argon]
            try:
                proc_arg = subprocess.run(cmd_arg, env=env, capture_output=True, text=True, timeout=25)
                all_arg_out = (proc_arg.stdout or "") + " " + (proc_arg.stderr or "")
                appeal_arg_id = check_profile_appeal_status(profile, all_arg_out)
                low_arg_out = all_arg_out.lower()
                is_arg_blocked = (
                    bool(appeal_arg_id) or
                    "submit an appeal" in low_arg_out or
                    "violation of terms of service" in low_arg_out or
                    "service has been disabled" in low_arg_out
                )
                if is_arg_blocked:
                    err_id = appeal_arg_id or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
                    if not appeal_arg_id:
                        record_profile_disabled(profile, err_id)
                    disabled_data = format_profile_for_dashboard(profile, {
                        "success": False,
                        "status": "DISABLED",
                        "is_appeal": True,
                        "error_id": err_id
                    })
                    update_cached_profile(profile, disabled_data)
                    return {
                        "profile": profile,
                        "success": False,
                        "status": "DISABLED",
                        "is_appeal": True,
                        "error_id": err_id,
                        "duration": dur,
                        "jitter": jitter_sec,
                        "data": disabled_data,
                        "error": f"Tài khoản {profile} bị chặn ToS khi gọi mô hình Argon (Submit an appeal). Mã lỗi: {err_id}"
                    }
                if "is not recognized" in low_arg_out or "invalid model selection" in low_arg_out:
                    current["hasArgon"] = False
                    if "argonWeekly" in current:
                        current["argonWeekly"]["unavailable"] = True
                        current["argonWeekly"]["countdown"] = "Unavailable N/A"
                    update_cached_profile(profile, current)
            except Exception:
                pass

        # 5. All model checks passed! Google has truly unblocked the account!
        unblock_profile(profile)
        res = fetch_quota_for_profile(profile, force_probe=True)
        formatted = format_profile_for_dashboard(profile, res)
        update_cached_profile(profile, formatted)
        LAST_BLOCKED_PROBE.pop(profile, None)
        return {
            "profile": profile,
            "success": True,
            "status": "ACTIVE",
            "unblocked": True,
            "duration": dur,
            "jitter": jitter_sec,
            "data": formatted,
            "message": f"🎉 Tuyệt vời! Tài khoản {profile} đã được Google mở khóa thành công!"
        }
    except subprocess.TimeoutExpired:
        return {"profile": profile, "success": False, "status": "ERROR", "duration": 25.0, "error": "Kiểm tra bị quá hạn (25s)"}
    except Exception as e:
        return {"profile": profile, "success": False, "status": "ERROR", "error": str(e)}


def record_profile_disabled(profile: str, error_id: str):
    """Persist disabled/appeal status to disk in profile's .gemini/antigravity/tos_disabled.json."""
    try:
        marker_dir = os.path.join(REAL_HOME, "antigravity_homes", profile, ".gemini/antigravity")
        os.makedirs(marker_dir, exist_ok=True)
        marker_file = os.path.join(marker_dir, "tos_disabled.json")
        with open(marker_file, "w") as f:
            json.dump({
                "profile": profile,
                "error_id": error_id or "856698b5-d43c-4198-962b-4db7fc3c4adb-2",
                "timestamp": time.time(),
                "disabled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "reason": "Violation of Terms of Service (Submit an appeal)"
            }, f, indent=2)
    except Exception:
        pass


def check_profile_appeal_status(profile: str, out_text: str = "") -> str:
    """Check if profile has been disabled for Terms of Service violation (submit an appeal).
    Returns Error ID string if disabled, or empty string '' if not disabled.
    """
    if out_text:
        low = out_text.lower()
        if "submit an appeal" in low or "violation of terms of service" in low or "service has been disabled" in low:
            m = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?:-\d+)?)', out_text)
            err_id = m.group(1) if m else "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
            record_profile_disabled(profile, err_id)
            return err_id
        return ""

    # Check marker file in profile directory (Single Source of Truth)
    marker_file = os.path.join(REAL_HOME, "antigravity_homes", profile, ".gemini/antigravity", "tos_disabled.json")
    if os.path.isfile(marker_file):
        try:
            with open(marker_file, "r") as f:
                data = json.load(f)
                return data.get("error_id") or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
        except Exception:
            pass

    return ""


def check_profile_auth_token(profile: str) -> bool:
    """Check in ~8ms whether profile has an active gemini token in its keychain.
    CRITICAL: If False, running agy will attempt to open the web browser for OAuth!
    We MUST NOT execute agy when this returns False.
    """
    wait_for_launch_lock()
    kc = os.path.join(REAL_HOME, "antigravity_homes", profile, "Library/Keychains", f"{profile}.keychain-db")
    if not os.path.isfile(kc):
        return False
    subprocess.run(["security", "unlock-keychain", "-p", KC_PASS, kc], capture_output=True)
    res = subprocess.run(["security", "find-generic-password", "-s", "gemini", "-a", "antigravity", kc], capture_output=True)
    return res.returncode == 0


def fetch_quota_for_profile(profile: str, force_probe: bool = False) -> dict:
    """Execute agy --output-format json -p '/usage' for a given profile."""
    ag_home = f"{REAL_HOME}/antigravity_homes/{profile}"
    if not os.path.isdir(ag_home):
        return {"profile": profile, "success": False, "error": f"Profile home not found: {ag_home}"}

    # 1. Fast check if account was disabled for ToS violation (submit an appeal)
    if not force_probe:
        appeal_err_id = check_profile_appeal_status(profile)
        if appeal_err_id:
            return {
                "profile": profile,
                "success": False,
                "status": "DISABLED",
                "is_appeal": True,
                "error_id": appeal_err_id,
                "duration": 0.05,
                "error": "Tài khoản bị vô hiệu hóa do vi phạm Điều khoản (Terms of Service / Submit an appeal)"
            }

    # 2. Fast check if account has CLI auth token in Keychain (PREVENTS agy FROM OPENING BROWSER!)
    if not check_profile_auth_token(profile):
        return {
            "profile": profile,
            "success": False,
            "status": "AUTH NEEDED",
            "is_appeal": False,
            "duration": 0.05,
            "error": "Profile chưa đăng nhập CLI. Cần đăng nhập bằng Terminal trước khi lấy Quota."
        }

    # 3. Unlock Keychain
    profile_kc = f"{ag_home}/Library/Keychains/{profile}.keychain-db"
    if os.path.exists(profile_kc):
        subprocess.run(["security", "unlock-keychain", "-p", KC_PASS, profile_kc], capture_output=True)

    # 4. Build isolated environment
    env = os.environ.copy()
    env.update({
        "HOME": ag_home,
        "AGY_PROFILE": profile,
        "AGY_CLI_MODE": "1",
        "TMPDIR": f"/tmp/ag_{profile}",
        "BROWSER": "true",  # Safeguard against browser launch
    })

    cmd = [AGY_BIN, "--output-format", "json", "-p", "/usage"]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=25)
        duration = time.time() - t0
        all_out = (proc.stdout or "") + " " + (proc.stderr or "")

        appeal_out_id = check_profile_appeal_status(profile, all_out)
        if appeal_out_id:
            return {
                "profile": profile,
                "success": False,
                "status": "DISABLED",
                "is_appeal": True,
                "error_id": appeal_out_id,
                "duration": duration,
                "error": "Tài khoản bị vô hiệu hóa do vi phạm Điều khoản (Terms of Service / Submit an appeal)"
            }

        if proc.returncode != 0:
            return {
                "profile": profile,
                "success": False,
                "duration": duration,
                "error": proc.stderr.strip() or f"Process exited with code {proc.returncode}"
            }

        stdout = proc.stdout.strip()
        data = json.loads(stdout)
        cmd_data = data.get("command", {}).get("data", {})
        groups = cmd_data.get("groups", [])
        return {
            "profile": profile,
            "success": True,
            "duration": duration,
            "groups": groups,
        }
    except subprocess.TimeoutExpired:
        return {"profile": profile, "success": False, "duration": 25.0, "error": "Request timed out (25s)"}
    except Exception as e:
        return {"profile": profile, "success": False, "error": str(e)}


def parse_quota_items(groups: list) -> dict:
    """Extract standard buckets into a structured dictionary."""
    items = {
        "gem_5h": {"fraction": 1.0, "reset_time": "", "available": False},
        "gem_weekly": {"fraction": 1.0, "reset_time": "", "available": False},
        "cld_5h": {"fraction": 1.0, "reset_time": "", "available": False},
        "cld_weekly": {"fraction": 1.0, "reset_time": "", "available": False},
        "argon_5h": None,
        "argon_weekly": {"fraction": 0.0, "reset_time": "", "available": False},
    }

    for g in groups:
        g_name = g.get("name", "").lower()
        if "gemini models" in g_name:
            for b in g.get("buckets", []):
                if b.get("window") == "5h":
                    items["gem_5h"] = {"fraction": b.get("remaining_fraction", 1.0), "reset_time": b.get("reset_time", ""), "available": True}
                elif b.get("window") == "weekly":
                    items["gem_weekly"] = {"fraction": b.get("remaining_fraction", 1.0), "reset_time": b.get("reset_time", ""), "available": True}
        elif "claude" in g_name:
            for b in g.get("buckets", []):
                if b.get("window") == "5h":
                    items["cld_5h"] = {"fraction": b.get("remaining_fraction", 1.0), "reset_time": b.get("reset_time", ""), "available": True}
                elif b.get("window") == "weekly":
                    items["cld_weekly"] = {"fraction": b.get("remaining_fraction", 1.0), "reset_time": b.get("reset_time", ""), "available": True}
        elif "argon" in g_name:
            for b in g.get("buckets", []):
                if b.get("window") == "5h":
                    items["argon_5h"] = {"fraction": b.get("remaining_fraction", 1.0), "reset_time": b.get("reset_time", ""), "available": True}
                elif b.get("window") == "weekly":
                    items["argon_weekly"] = {"fraction": b.get("remaining_fraction", 1.0), "reset_time": b.get("reset_time", ""), "available": True}

    return items


def print_dashboard_cards(result: dict):
    """Render the full Dashboard matching the user's reference image."""
    profile = result["profile"]
    if not result.get("success"):
        if result.get("is_appeal") or result.get("status") == "DISABLED":
            print(f"\n{BOLD}{RED}❌ PROFILE: {profile}{RESET}  \033[48;2;127;29;29m\033[1;37m 🚫 BỊ KHÓA (APPEAL NEEDED) \033[0m")
            print(f"  {RED}Trạng thái: Tài khoản bị Google vô hiệu hóa do vi phạm Điều khoản dịch vụ!{RESET}")
            print(f"  {AMBER}Chi tiết lỗi: This service has been disabled in this account for violation of Terms of Service.{RESET}")
            print(f"  {CYAN}👉 Cần gửi đơn kháng nghị (Submit an appeal) tới Google để khôi phục tài khoản:{RESET}")
            print(f"     {BOLD}{WHITE}https://docs.google.com/forms/d/e/1FAIpQLScOJWibQ_-hYuVv63kJTgEqlgAaOwRLGFTbXm-QY1gz8U0CGA/viewform{RESET}\n")
            return

        print(f"\n{BOLD}{RED}❌ PROFILE: {profile}{RESET}  \033[38;2;245;158;11m🔑 AUTH NEEDED\033[0m")
        print(f"  {RED}Trạng thái: Chưa xác thực CLI ({result.get('error', 'Authentication or timeout')}){RESET}")
        print(f"  {CYAN}👉 Để đăng nhập CLI cho profile này, hãy chạy lệnh:{RESET}")
        print(f"     {BOLD}{WHITE}{profile}-cli{RESET}\n")
        return

    items = parse_quota_items(result.get("groups", []))

    # Determine status tag based only on available buckets
    avail_fractions = [
        item["fraction"] for k, item in items.items()
        if item and item.get("available")
    ]
    if not avail_fractions or min(avail_fractions) <= 0.0:
        status_tag = f"\033[38;2;239;68;68m🔴 EXHAUSTED\033[0m"
    else:
        status_tag = f"\033[38;2;114;188;130m🟢 ACTIVE\033[0m"

    has_argon = items["argon_weekly"].get("available", False)
    argon_tag_str = f"  {TAG_ARGON}" if has_argon else ""

    has_5h = items["gem_5h"].get("available", False) or items["cld_5h"].get("available", False)
    if has_5h:
        tier_tag = TAG_PRO
        priority_tag = TAG_PRIORITY
    else:
        tier_tag = "\033[48;2;217;119;6m\033[1;37m FREE \033[0m"
        priority_tag = "\033[48;2;24;27;38m\033[38;2;160;174;192m Priority: 20 \033[0m"

    print(f"\n{BOLD}{WHITE}✦ Profile: {CYAN}{profile}{RESET}  {tier_tag}  {priority_tag}{argon_tag_str}  {status_tag}")

    # Row 1: Gemini 5H  &  Claude 5H
    gem_5h_time = format_countdown(items["gem_5h"]["reset_time"])
    cld_5h_time = format_countdown(items["cld_5h"]["reset_time"])
    c1 = render_card("✦", CYAN, "Gemini 3.8 / Pro 5H", gem_5h_time, items["gem_5h"]["fraction"], width=45, available=items["gem_5h"]["available"])
    c2 = render_card("✺", "\033[38;2;251;146;60m", "Claude 5.5 / GPT 5H", cld_5h_time, items["cld_5h"]["fraction"], width=45, available=items["cld_5h"]["available"])
    for l1, l2 in zip(c1, c2):
        print(l1 + "  " + l2)

    # Row 2: Gemini Weekly  &  Claude Weekly
    gem_w_time = format_countdown(items["gem_weekly"]["reset_time"])
    cld_w_time = format_countdown(items["cld_weekly"]["reset_time"])
    c3 = render_card("✦", CYAN, "Gemini Weekly", gem_w_time, items["gem_weekly"]["fraction"], width=45, available=items["gem_weekly"]["available"])
    c4 = render_card("✺", "\033[38;2;251;146;60m", "Claude Weekly", cld_w_time, items["cld_weekly"]["fraction"], width=45, available=items["cld_weekly"]["available"])
    for l3, l4 in zip(c3, c4):
        print(l3 + "  " + l4)

    # Row 3: Argon 5H (if present)
    if items["argon_5h"] is not None:
        arg_5h_time = format_countdown(items["argon_5h"]["reset_time"])
        c5_5h = render_card("✦", CYAN, "Gemini 4 Argon 5H", arg_5h_time, items["argon_5h"]["fraction"], width=92, available=items["argon_5h"]["available"])
        for l in c5_5h:
            print(l)

    # Row 4: Argon Weekly (Full width card with High/Med/Low tags or INACTIVE tag)
    arg_w_time = format_countdown(items["argon_weekly"]["reset_time"])
    tags_str = f"{TAG_HIGH} {TAG_MED} {TAG_LOW}" if items["argon_weekly"]["available"] else None
    c5 = render_card("✦", CYAN, "Gemini 4 Argon Weekly", arg_w_time, items["argon_weekly"]["fraction"], width=92, tags=tags_str, available=items["argon_weekly"]["available"])
    for l in c5:
        print(l)

    # Actions footer matching /refresh-session: Refresh nhanh, Kích hoạt & Lên lịch
    print(f" {DIM}⚙️  Actions:{RESET}")
    print(f"   \033[38;2;56;189;248m⚡ Refresh nhanh\033[0m : {DIM}check-quota refresh {profile}{RESET}")
    print(f"   \033[38;2;114;188;130m🎯 Kích hoạt\033[0m     : {DIM}check-quota ping {profile}{RESET}")
    print(f"   \033[38;2;192;132;252m⏰ Lên lịch\033[0m      : {DIM}/refresh-session schedule --time 07:00 --delay 30{RESET}\n")


def render_mini_bar(item: dict, width: int = 14) -> str:
    """Render a compact progress bar for tabular summary with unified consumed track color.
    When inactive, renders a muted gray bar with no text as requested."""
    if not item or not item.get("available", True):
        return f"{GRAY}[{'░' * width}]{RESET}       "
    fraction = max(0.0, min(1.0, item["fraction"]))
    pct = fraction * 100.0
    fill_color, track_color = get_color_pair(pct)
    filled = int(round(fraction * width))
    empty = width - filled
    return f"[{fill_color}{'█' * filled}{RESET}{track_color}{'░' * empty}{RESET}] {fill_color}{pct:5.1f}%{RESET}"


def print_all_summary(results: list, show_providers: bool = True):
    """Print an executive multi-profile summary table strictly aligned to 122 chars."""
    table_w = 122
    if show_providers:
        print(f"\n{BOLD}{CYAN}=== AI AGENT PROVIDERS (CLAUDE, CODEX, KIRO) ==={RESET}")
        try:
            c_data = fetch_claude_quota()
            print_claude_card(c_data)
        except Exception:
            pass
        try:
            o_data = fetch_codex_quota()
            print_codex_card(o_data)
        except Exception:
            pass
        try:
            k_data = fetch_kiro_quota()
            print_kiro_card(k_data)
        except Exception:
            pass
    print(f"\n{BOLD}{WHITE}{'=' * table_w}{RESET}")
    print(f"{BOLD}{CYAN}                      ANTIGRAVITY ACCOUNTS QUOTA DASHBOARD (ALL PROFILES){RESET}")
    print(f"{BOLD}{WHITE}{'=' * table_w}{RESET}")
    print(f"{BOLD}{'Profile':<18} | {'Gemini Weekly':<23} | {'Gemini 5H':<23} | {'Claude Weekly':<23} | {'Argon Weekly':<23}{RESET}")
    print(f"{DIM}{'-' * table_w}{RESET}")

    cols_w = 23 * 4 + 3 * 3  # 101 chars across the 4 quota columns

    for res in results:
        profile = res["profile"]
        if not res.get("success"):
            if res.get("is_appeal") or res.get("status") == "DISABLED":
                err_msg = "Vi phạm ToS / Cần kháng nghị (Submit Appeal)"
                msg = f"  \033[38;2;239;68;68m🚫 DISABLED\033[0m - {RED}{err_msg}{RESET}"
                pad = max(1, cols_w - str_vis_width(msg))
                print(f"{BOLD}{profile:<18}{RESET} |{msg}{' ' * pad}|")
                continue

            err_msg = "Chưa đăng nhập CLI"
            msg = f"  \033[38;2;245;158;11m🔑 AUTH NEEDED\033[0m - {RED}{err_msg}{RESET} {DIM}({profile}-cli){RESET}"
            pad = max(1, cols_w - str_vis_width(msg))
            print(f"{BOLD}{profile:<18}{RESET} |{msg}{' ' * pad}|")
            continue

        items = parse_quota_items(res.get("groups", []))
        bar_gem_w = render_mini_bar(items["gem_weekly"])
        bar_gem_5h = render_mini_bar(items["gem_5h"])
        bar_cld_w = render_mini_bar(items["cld_weekly"])
        bar_arg_w = render_mini_bar(items["argon_weekly"])

        print(f"{BOLD}{profile:<18}{RESET} | {bar_gem_w} | {bar_gem_5h} | {bar_cld_w} | {bar_arg_w}")

    print(f"{BOLD}{WHITE}{'=' * table_w}{RESET}\n")


def get_dashboard_html_path() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent / "skills" / "check-quota" / "resources" / "dashboard" / "quota_dashboard.html",
        Path(REAL_HOME) / "AllProjects/ai-agent-tools/skills/check-quota/resources/dashboard/quota_dashboard.html",
        Path(REAL_HOME) / "Projects/ai-agent-tools/skills/check-quota/resources/dashboard/quota_dashboard.html",
        Path(REAL_HOME) / "antigravity_homes/huynhminhtien0510/.gemini/antigravity/brain/faba533a-ed61-4a6e-8b53-bfbf7926cccf/quota_dashboard.html",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return candidates[0]


CACHED_PROFILES_DATA: dict = {}


def get_claude_oauth_token() -> tuple[str | None, str | None, bool]:
    """Retrieve Claude Code OAuth access token.

    Returns (token, email, is_logged_in).
    Checks:
    1. Environment variable CLAUDE_CODE_OAUTH_TOKEN
    2. macOS Keychain item 'Claude Code-credentials'
       - If access token is empty or expired but refresh token exists, auto-refreshes via platform.claude.com/v1/oauth/token
    3. Plaintext fallback ~/.claude/.credentials.json
    """
    # 1. Environment variable
    env_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if env_token and env_token.strip():
        return env_token.strip(), None, True

    # 2. macOS Keychain
    try:
        user = os.environ.get("USER", "danhdueexoictif")
        cmd = ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=2.0)
        if proc.returncode != 0:
            proc = subprocess.run(
                ["security", "find-generic-password", "-s", "Claude Code-credentials", "-a", user, "-w"],
                capture_output=True, text=True, timeout=2.0
            )

        if proc.returncode == 0 and proc.stdout:
            stdout_clean = proc.stdout.strip()
            if stdout_clean.startswith("{") and stdout_clean.endswith("}"):
                data = json.loads(stdout_clean)
                oauth = data.get("claudeAiOauth", {})
                access_token = (oauth.get("accessToken") or "").strip()
                refresh_token = (oauth.get("refreshToken") or "").strip()
                expires_at = oauth.get("expiresAt") or 0
                now_ms = int(time.time() * 1000)

                # Valid unexpired access token
                if access_token and (expires_at == 0 or expires_at > now_ms + 60000):
                    return access_token, None, True

                # Expired or empty access token, but refresh token exists
                if refresh_token:
                    try:
                        refresh_url = "https://platform.claude.com/v1/oauth/token"
                        payload = json.dumps({
                            "grant_type": "refresh_token",
                            "refresh_token": refresh_token,
                            "client_id": "9d1c250a-e61b-44d9-88ed-5944d1962f5e",
                        }).encode("utf-8")
                        req = urllib.request.Request(
                            refresh_url,
                            data=payload,
                            headers={
                                "Content-Type": "application/json",
                                "User-Agent": "claude-cli/2.1.231",
                                "Accept": "application/json",
                            }
                        )
                        with urllib.request.urlopen(req, timeout=5.0) as r_resp:
                            if r_resp.status == 200:
                                r_data = json.loads(r_resp.read().decode("utf-8"))
                                new_acc = r_data.get("access_token")
                                new_ref = r_data.get("refresh_token") or refresh_token
                                exp_in = r_data.get("expires_in", 3600)
                                if new_acc:
                                    data["claudeAiOauth"]["accessToken"] = new_acc
                                    data["claudeAiOauth"]["refreshToken"] = new_ref
                                    data["claudeAiOauth"]["expiresAt"] = now_ms + (exp_in * 1000)
                                    try:
                                        subprocess.run(
                                            ["security", "add-generic-password", "-U", "-s", "Claude Code-credentials",
                                             "-a", user, "-w", json.dumps(data)],
                                            capture_output=True, timeout=2.0
                                        )
                                    except Exception:
                                        pass
                                    return new_acc, None, True
                    except Exception as ref_err:
                        sys.stderr.write(f"Warning: Claude token auto-refresh failed: {ref_err}\n")
    except Exception as kc_err:
        sys.stderr.write(f"Warning: Keychain read for Claude failed: {kc_err}\n")

    # 3. Plaintext fallback credentials
    cred_file = Path(REAL_HOME) / ".claude" / ".credentials.json"
    if cred_file.is_file():
        try:
            with open(cred_file, "r", encoding="utf-8") as f:
                c_json = json.load(f)
            oauth = c_json.get("claudeAiOauth", {})
            token = (oauth.get("accessToken") or "").strip()
            if token:
                return token, None, True
        except Exception:
            pass

    return None, None, False


def update_claude_json_cache(u: dict, account_uuid: str = ""):
    """Synchronize freshly fetched live usage into ~/.claude.json cachedUsageUtilization."""
    claude_json_path = Path(REAL_HOME) / ".claude.json"
    if claude_json_path.is_file():
        try:
            with open(claude_json_path, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            if not account_uuid:
                account_uuid = c_data.get("oauthAccount", {}).get("accountUuid", "")
            c_data["cachedUsageUtilization"] = {
                "fetchedAtMs": int(time.time() * 1000),
                "accountUuid": account_uuid,
                "utilization": u,
            }
            with open(claude_json_path, "w", encoding="utf-8") as f:
                json.dump(c_data, f, indent=2)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to update .claude.json cache: {e}\n")


def fetch_claude_quota() -> dict:
    claude_json_path = Path(REAL_HOME) / ".claude.json"
    email = "Anthropic Claude Pro / Team"
    account_uuid = ""
    c_data = {}
    if claude_json_path.is_file():
        try:
            with open(claude_json_path, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            oauth_acc = c_data.get("oauthAccount", {})
            if oauth_acc.get("emailAddress"):
                email = oauth_acc["emailAddress"]
            account_uuid = oauth_acc.get("accountUuid", "")
        except Exception as e:
            sys.stderr.write(f"Error reading .claude.json: {e}\n")

    token, token_email, is_logged_in = get_claude_oauth_token()
    if token_email:
        email = token_email

    api_data = None
    is_live = False

    # 1. Primary: Query Anthropic Live API if token is available
    if token:
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
                if resp.status == 200:
                    raw_data = json.loads(resp.read().decode("utf-8"))
                    api_data = raw_data.get("utilization", raw_data)
                    is_live = True
                    update_claude_json_cache(api_data, account_uuid)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to fetch live Claude quota from Anthropic API: {e}\n")

    # 2. Fallback: cachedUsageUtilization from .claude.json
    if not api_data:
        api_data = c_data.get("cachedUsageUtilization", {}).get("utilization", {})

    five_h = api_data.get("five_hour") or {}
    utilization_5h = five_h.get("utilization", 0)
    resets_at_5h_iso = five_h.get("resets_at", "")

    seven_d = api_data.get("seven_day") or {}
    utilization_7d = seven_d.get("utilization", 0)
    resets_at_7d_iso = seven_d.get("resets_at", "")

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    is_active_5h = False
    rem_sec_5h = 0
    resets_at_5h_ts = 0
    local_reset_5h = ""
    if resets_at_5h_iso:
        try:
            dt_5h = datetime.datetime.fromisoformat(resets_at_5h_iso.replace("Z", "+00:00"))
            resets_at_5h_ts = int(dt_5h.timestamp())
            local_reset_5h = dt_5h.astimezone().strftime("%H:%M:%S")
            rem_sec_5h = max(0, int((dt_5h - now_utc).total_seconds()))
            if rem_sec_5h > 0 and utilization_5h > 0:
                is_active_5h = True
        except Exception:
            pass

    rem_sec_7d = 0
    resets_at_7d_ts = 0
    local_reset_7d = ""
    if resets_at_7d_iso:
        try:
            dt_7d = datetime.datetime.fromisoformat(resets_at_7d_iso.replace("Z", "+00:00"))
            resets_at_7d_ts = int(dt_7d.timestamp())
            local_reset_7d = dt_7d.astimezone().strftime("%d/%m %H:%M")
            rem_sec_7d = max(0, int((dt_7d - now_utc).total_seconds()))
        except Exception:
            pass

    # Strictly calculate REMAINING percentage (100% - utilization%)
    fraction_5h = max(0.0, min(1.0, (100.0 - float(utilization_5h)) / 100.0))
    fraction_7d = max(0.0, min(1.0, (100.0 - float(utilization_7d)) / 100.0))

    countdown_5h = f"⏱ {rem_sec_5h // 3600}h {(rem_sec_5h % 3600) // 60}m" if rem_sec_5h > 0 else "⏱ 5h 00m (Reset xong)"
    if local_reset_5h and rem_sec_5h > 0:
        countdown_5h += f" ({local_reset_5h})"

    days_7d = rem_sec_7d // 86400
    hours_7d = (rem_sec_7d % 86400) // 3600
    countdown_7d = f"⏱ {days_7d}d {hours_7d}h" if rem_sec_7d > 0 else "⏱ 7d 00h (Reset xong)"
    if local_reset_7d and rem_sec_7d > 0:
        countdown_7d += f" ({local_reset_7d})"

    # Status handling
    if not is_logged_in and not is_live:
        status = "NEED_LOGIN"
        email_display = f"{email} (Chưa đăng nhập CLI - Run 'claude auth login')"
        countdown_5h_card = "Cần đăng nhập"
    elif is_active_5h or fraction_5h > 0:
        status = "ACTIVE"
        email_display = email
        countdown_5h_card = countdown_5h
    else:
        status = "IDLE"
        email_display = email
        countdown_5h_card = countdown_5h

    # Save to hashed SQLite session store
    save_session_record("claude", resets_at_5h_ts, resets_at_7d_ts, fraction_5h, is_active_5h)

    return {
        "profile": "claude",
        "displayName": "Claude Code",
        "isProvider": True,
        "providerType": "claude",
        "tier": "ANTHROPIC",
        "priority": 100,
        "email": email_display,
        "status": status,
        "isSessionActive": is_active_5h,
        "resetTime": resets_at_5h_iso,
        "resetTimeLocal": local_reset_5h,
        "remainingCountdown": countdown_5h_card,
        "hasArgon": True,
        "gemini5h": {
            "name": "Claude 5H Session Window",
            "fraction": fraction_5h,
            "countdown": countdown_5h,
            "resetTime": resets_at_5h_iso,
            "resetTimeLocal": local_reset_5h,
            "unavailable": False,
            "isLive": is_live,
        },
        "claude5h": {
            "name": "Claude Session Tier",
            "fraction": 1.0,
            "countdown": "Anthropic Live API" if is_live else "Local Cache",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": False,
        },
        "geminiWeekly": {
            "name": "Claude 7D Weekly Remaining",
            "fraction": fraction_7d,
            "countdown": countdown_7d,
            "resetTime": resets_at_7d_iso,
            "resetTimeLocal": local_reset_7d,
            "unavailable": False,
        },
        "claudeWeekly": {
            "name": "Anthropic Rate Limit Scope",
            "fraction": 1.0,
            "countdown": "Normal Severity",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": False,
        },
        "argonWeekly": {
            "name": "Anthropic Model Roster (Claude 3.7 Sonnet / Opus 3.5)",
            "fraction": 1.0,
            "countdown": "Sẵn sàng",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": False,
            "tags": True,
        },
    }


def fetch_codex_quota() -> dict:
    # 1. Primary: Query real-time Plan limits from OpenAI backend API
    auth_json_path = Path(REAL_HOME) / ".codex" / "auth.json"
    if auth_json_path.is_file():
        try:
            with open(auth_json_path, "r", encoding="utf-8") as f:
                auth = json.load(f)
            tokens = auth.get("tokens", {})
            token = tokens.get("access_token")
            account_id = tokens.get("account_id")

            if token:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "codex/0.167.0",
                    "Accept": "application/json",
                }
                if account_id:
                    headers["ChatGPT-Account-ID"] = account_id

                req = urllib.request.Request("https://chatgpt.com/backend-api/wham/usage", headers=headers)
                with urllib.request.urlopen(req, timeout=4.0) as resp:
                    api_data = json.loads(resp.read().decode())

                rl = api_data.get("rate_limit", {})
                pw = rl.get("primary_window", {})
                sw = rl.get("secondary_window", {})

                p_used = pw.get("used_percent", 0)
                p_rem_sec = pw.get("reset_after_seconds", 0)
                p_reset_ts = pw.get("reset_at", 0)

                s_used = sw.get("used_percent", 0)
                s_rem_sec = sw.get("reset_after_seconds", 0)
                s_reset_ts = sw.get("reset_at", 0)

                credits_count = api_data.get("rate_limit_reset_credits", {}).get("available_count", 0)

                fraction_5h = max(0.0, min(1.0, (100.0 - float(p_used)) / 100.0))
                fraction_7d = max(0.0, min(1.0, (100.0 - float(s_used)) / 100.0))

                dt_5h = datetime.datetime.fromtimestamp(p_reset_ts) if p_reset_ts else None
                local_reset_5h = dt_5h.strftime("%H:%M:%S") if dt_5h else ""
                iso_reset_5h = dt_5h.astimezone(datetime.timezone.utc).isoformat() if dt_5h else ""

                dt_7d = datetime.datetime.fromtimestamp(s_reset_ts) if s_reset_ts else None
                local_reset_7d = dt_7d.strftime("%d/%m %H:%M") if dt_7d else ""
                iso_reset_7d = dt_7d.astimezone(datetime.timezone.utc).isoformat() if dt_7d else ""

                countdown_5h = f"⏱ {p_rem_sec // 3600}h {(p_rem_sec % 3600) // 60}m ({local_reset_5h})" if p_rem_sec > 0 else "⏱ 5h 00m (Reset xong)"
                countdown_7d = f"⏱ {s_rem_sec // 86400}d {(s_rem_sec % 86400) // 3600}h ({local_reset_7d})" if s_rem_sec > 0 else "⏱ 7d 00h (Reset xong)"

                is_active = p_rem_sec > 0 and p_used > 0
                status = "ACTIVE" if rl.get("allowed", True) else "EXHAUSTED"

                # Save to hashed SQLite session store
                save_session_record("codex", p_reset_ts, s_reset_ts, fraction_5h, is_active)

                return {
                    "profile": "codex",
                    "displayName": "OpenAI Codex",
                    "isProvider": True,
                    "providerType": "codex",
                    "tier": "OPENAI",
                    "priority": 95,
                    "email": api_data.get("email") or "OpenAI Codex (ChatGPT Plus)",
                    "status": status,
                    "isSessionActive": is_active,
                    "resetTime": iso_reset_5h,
                    "resetTimeLocal": local_reset_5h,
                    "remainingCountdown": countdown_5h,
                    "hasArgon": True,
                    "resetCredits": credits_count,
                    "gemini5h": {
                        "name": "Codex 5-Hour Limit",
                        "fraction": fraction_5h,
                        "countdown": countdown_5h,
                        "resetTime": iso_reset_5h,
                        "resetTimeLocal": local_reset_5h,
                        "unavailable": False,
                    },
                    "claude5h": {
                        "name": "Codex Reasoning Effort",
                        "fraction": 1.0,
                        "countdown": "Low / Med / High",
                        "resetTime": "",
                        "resetTimeLocal": "",
                        "unavailable": False,
                    },
                    "geminiWeekly": {
                        "name": "Codex Weekly Limit",
                        "fraction": fraction_7d,
                        "countdown": countdown_7d,
                        "resetTime": iso_reset_7d,
                        "resetTimeLocal": local_reset_7d,
                        "unavailable": False,
                    },
                    "claudeWeekly": {
                        "name": "OpenAI Reset Credits",
                        "fraction": 1.0,
                        "countdown": f"{credits_count} Available",
                        "resetTime": "",
                        "resetTimeLocal": "",
                        "unavailable": False,
                    },
                    "argonWeekly": {
                        "name": "OpenAI Model Roster (gpt-4.5 / o3-mini)",
                        "fraction": 1.0,
                        "countdown": "Sẵn sàng",
                        "resetTime": "",
                        "resetTimeLocal": "",
                        "unavailable": False,
                        "tags": True,
                    },
                }
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to fetch online OpenAI Codex quota: {e}\n")

    # 2. Fallback: local logs_2.sqlite
    sqlite_path = Path(REAL_HOME) / ".codex" / "logs_2.sqlite"
    max_ts = 0
    if sqlite_path.is_file():
        try:
            con = sqlite3.connect(str(sqlite_path), timeout=3.0)
            cur = con.cursor()
            cur.execute("SELECT max(ts) FROM logs;")
            row = cur.fetchone()
            con.close()
            if row and row[0]:
                max_ts = row[0]
        except Exception as e:
            sys.stderr.write(f"Error reading codex logs_2.sqlite: {e}\n")

    now_ts = int(time.time())
    delta_sec = now_ts - max_ts if max_ts > 0 else 999999
    window_sec = 5 * 3600

    if delta_sec < window_sec:
        rem_sec = window_sec - delta_sec
        reset_ts = max_ts + window_sec
        local_reset_5h = datetime.datetime.fromtimestamp(reset_ts).strftime("%H:%M:%S")
        reset_iso = datetime.datetime.fromtimestamp(reset_ts, tz=datetime.timezone.utc).isoformat()
        fraction_5h = rem_sec / window_sec
        countdown_5h = f"⏱ {rem_sec // 3600}h {(rem_sec % 3600) // 60}m ({local_reset_5h})"
        is_active = True
        status = "ACTIVE"
    else:
        rem_sec = 0
        reset_ts = now_ts
        local_reset_5h = "Reset xong"
        reset_iso = ""
        fraction_5h = 1.0
        countdown_5h = "⏱ 5h 00m (Reset xong)"
        is_active = False
        status = "IDLE"

    # Save to hashed SQLite session store
    save_session_record("codex", reset_ts, 0, fraction_5h, is_active)

    return {
        "profile": "codex",
        "displayName": "OpenAI Codex",
        "isProvider": True,
        "providerType": "codex",
        "tier": "OPENAI",
        "priority": 95,
        "email": "OpenAI Codex CLI (ChatGPT Plus/Team)",
        "status": status,
        "isSessionActive": is_active,
        "resetTime": reset_iso,
        "resetTimeLocal": local_reset_5h,
        "remainingCountdown": countdown_5h,
        "hasArgon": True,
        "gemini5h": {
            "name": "Codex 5H Rolling Session",
            "fraction": fraction_5h,
            "countdown": countdown_5h,
            "resetTime": reset_iso,
            "resetTimeLocal": local_reset_5h,
            "unavailable": False,
        },
        "claude5h": {
            "name": "Codex Reasoning Effort",
            "fraction": 1.0,
            "countdown": "Low / Med / High",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": False,
        },
        "geminiWeekly": {
            "name": "OpenAI Weekly Limit (Chỉ trượt 5H Session)",
            "fraction": 1.0,
            "countdown": "Không áp dụng",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": False,
        },
        "claudeWeekly": {
            "name": "OpenAI Auth Session",
            "fraction": 1.0,
            "countdown": "OAuth Active",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": False,
        },
        "argonWeekly": {
            "name": "OpenAI Model Roster (gpt-4.5 / o3-mini)",
            "fraction": 1.0,
            "countdown": "Sẵn sàng",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": False,
            "tags": True,
        },
    }


def get_kiro_bin_path() -> str | None:
    candidate = shutil.which("kiro-cli") or shutil.which("kiro")
    if candidate and os.path.isfile(candidate):
        return candidate
    local_bin = os.path.join(REAL_HOME, ".local", "bin", "kiro-cli")
    if os.path.isfile(local_bin):
        return local_bin
    return None


def parse_kiro_whoami_email(output: str) -> str | None:
    if not output or "not logged in" in output.lower():
        return None
    m = re.search(r"Email:\s*([^\s\r\n]+)", output)
    if m:
        return m.group(1).strip()
    return None


def parse_kiro_usage_limits(api_data: dict, email: str = "") -> dict:
    sub_info = api_data.get("subscriptionInfo", {})
    tier = sub_info.get("subscriptionTitle", "KIRO STUDENT")
    overage_cfg = api_data.get("overageConfiguration", {})
    overage_status = overage_cfg.get("overageStatus", "DISABLED")

    used = 0.0
    limit = 1000.0
    breakdowns = api_data.get("usageBreakdownList", [])
    if breakdowns:
        b0 = breakdowns[0]
        used = float(b0.get("currentUsageWithPrecision", b0.get("currentUsage", 0.0)))
        limit = float(b0.get("usageLimitWithPrecision", b0.get("usageLimit", 1000.0)))

    remaining = max(0.0, limit - used)
    fraction = max(0.0, min(1.0, remaining / limit)) if limit > 0 else 0.0

    next_date_reset = float(api_data.get("nextDateReset", 0.0))
    now_ts = time.time()
    reset_iso = ""
    local_reset = ""
    countdown = "⏱ Hết hạn"

    if next_date_reset > 0:
        dt_reset = datetime.datetime.fromtimestamp(next_date_reset, tz=datetime.timezone.utc)
        reset_iso = dt_reset.isoformat()
        local_reset = dt_reset.astimezone().strftime("%d/%m")
        rem_sec = max(0, int(next_date_reset - now_ts))
        days = rem_sec // 86400
        hours = (rem_sec % 86400) // 3600
        countdown = f"⏱ {days}d {hours:02d}h ({local_reset})"

    status = "ACTIVE"
    if fraction <= 0.0 and overage_status == "DISABLED":
        status = "EXHAUSTED"

    # Save to hashed SQLite session store
    save_session_record("kiro", int(next_date_reset), int(next_date_reset), fraction, True)

    return {
        "profile": "kiro",
        "displayName": "Kiro CLI",
        "isProvider": True,
        "providerType": "kiro",
        "tier": tier,
        "priority": 90,
        "email": email or "Kiro CLI User",
        "status": status,
        "success": True,
        "isSessionActive": True,
        "resetTime": reset_iso,
        "resetTimeLocal": local_reset,
        "remainingCountdown": countdown,
        "hasArgon": False,
        "isCreditOnly": True,
        "creditsPool": {
            "name": "Monthly Credits Pool",
            "used": round(used, 2),
            "limit": round(limit, 2),
            "remaining": round(remaining, 2),
            "fraction": fraction,
            "countdown": countdown,
            "resetDate": local_reset,
            "unavailable": False,
        },
        "gemini5h": {
            "name": "Monthly Credits Pool",
            "fraction": fraction,
            "countdown": countdown,
            "resetTime": reset_iso,
            "resetTimeLocal": local_reset,
            "unavailable": False,
        },
        "claude5h": None,
        "geminiWeekly": None,
        "overageStatus": overage_status,
        "defaultModel": "auto (1.0x)",
    }


def fetch_kiro_quota() -> dict:
    kiro_bin = get_kiro_bin_path()
    if not kiro_bin:
        return {
            "profile": "kiro",
            "displayName": "Kiro CLI",
            "isProvider": True,
            "providerType": "kiro",
            "tier": "KIRO",
            "priority": 90,
            "email": "Kiro CLI (Not Installed)",
            "status": "UNAVAILABLE",
            "success": False,
            "isSessionActive": False,
            "resetTime": "",
            "resetTimeLocal": "",
            "remainingCountdown": "Unavailable",
            "hasArgon": False,
            "isCreditOnly": True,
            "gemini5h": {
                "name": "Monthly Credits Pool",
                "fraction": 0.0,
                "countdown": "N/A",
                "resetTime": "",
                "resetTimeLocal": "",
                "unavailable": True,
            },
        }

    env = {
        "HOME": REAL_HOME,
        "PATH": f"{REAL_HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin",
    }

    # 1. Check whoami
    email = ""
    try:
        whoami_proc = subprocess.run([kiro_bin, "whoami"], env=env, capture_output=True, text=True, timeout=3.0)
        email = parse_kiro_whoami_email(whoami_proc.stdout) or ""
        if whoami_proc.returncode != 0 or not email:
            return {
                "profile": "kiro",
                "displayName": "Kiro CLI",
                "isProvider": True,
                "providerType": "kiro",
                "tier": "KIRO",
                "priority": 90,
                "email": "Chưa đăng nhập (Run 'kiro-cli login')",
                "status": "NOT LOGGED IN",
                "success": False,
                "isSessionActive": False,
                "resetTime": "",
                "resetTimeLocal": "",
                "remainingCountdown": "Chưa đăng nhập",
                "hasArgon": False,
                "isCreditOnly": True,
                "gemini5h": {
                    "name": "Monthly Credits Pool",
                    "fraction": 0.0,
                    "countdown": "Chưa đăng nhập",
                    "resetTime": "",
                    "resetTimeLocal": "",
                    "unavailable": True,
                },
            }
    except Exception as e:
        sys.stderr.write(f"Warning: kiro-cli whoami error: {e}\n")

    # 2. Query GetUsageLimits via KAS token
    try:
        kas_proc = subprocess.run([kiro_bin, "chat", "_", "get-kas-token"], env=env, capture_output=True, text=True, timeout=4.0)
        if kas_proc.returncode == 0 and kas_proc.stdout:
            kas_json = json.loads(kas_proc.stdout)
            kas_data = kas_json.get("data", {})
            token = kas_data.get("accessToken")
            profile_arn = kas_data.get("profileArn")

            if token and profile_arn:
                req = urllib.request.Request(
                    "https://q.us-east-1.amazonaws.com",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/x-amz-json-1.0",
                        "x-amz-target": "AmazonCodeWhispererService.GetUsageLimits",
                        "User-Agent": "kiro-cli/3.1.0",
                    },
                    data=json.dumps({"profileArn": profile_arn}).encode("utf-8"),
                )
                with urllib.request.urlopen(req, timeout=4.0) as resp:
                    api_data = json.loads(resp.read().decode("utf-8"))
                    return parse_kiro_usage_limits(api_data, email=email)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to fetch online Kiro quota: {e}\n")

    # 3. Fallback: session store cached snapshot
    cached = get_session_record("kiro")
    if cached:
        fraction = cached.get("fraction_5h", 1.0)
        reset_ts = cached.get("reset_5h", 0)
        now_ts = time.time()
        rem_sec = max(0, int(reset_ts - now_ts))
        days = rem_sec // 86400
        hours = (rem_sec % 86400) // 3600
        local_date = datetime.datetime.fromtimestamp(reset_ts).strftime("%d/%m") if reset_ts > 0 else ""
        countdown = f"⏱ {days}d {hours:02d}h ({local_date})" if reset_ts > 0 else "⏱ Cached"
        return {
            "profile": "kiro",
            "displayName": "Kiro CLI",
            "isProvider": True,
            "providerType": "kiro",
            "tier": "KIRO",
            "priority": 90,
            "email": email or "Kiro CLI User",
            "status": "ACTIVE (Cached)",
            "success": True,
            "isSessionActive": True,
            "resetTime": "",
            "resetTimeLocal": local_date,
            "remainingCountdown": countdown,
            "hasArgon": False,
            "isCreditOnly": True,
            "creditsPool": {
                "name": "Monthly Credits Pool",
                "used": 0.0,
                "limit": 1000.0,
                "remaining": round(fraction * 1000.0, 2),
                "fraction": fraction,
                "countdown": countdown,
                "resetDate": local_date,
                "unavailable": False,
            },
            "gemini5h": {
                "name": "Monthly Credits Pool",
                "fraction": fraction,
                "countdown": countdown,
                "resetTime": "",
                "resetTimeLocal": local_date,
                "unavailable": False,
            },
        }

    return {
        "profile": "kiro",
        "displayName": "Kiro CLI",
        "isProvider": True,
        "providerType": "kiro",
        "tier": "KIRO",
        "priority": 90,
        "email": email or "Kiro CLI User",
        "status": "IDLE",
        "success": False,
        "isSessionActive": False,
        "resetTime": "",
        "resetTimeLocal": "",
        "remainingCountdown": "Unknown",
        "hasArgon": False,
        "isCreditOnly": True,
        "gemini5h": {
            "name": "Monthly Credits Pool",
            "fraction": 0.0,
            "countdown": "N/A",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": True,
        },
    }


def print_claude_card(data: dict):
    tier = data.get("tier", "ANTHROPIC")
    email = data.get("email", "")
    status = data.get("status", "ACTIVE")
    g5h = data.get("gemini5h", {})
    g7d = data.get("geminiWeekly", {})
    frac_5h = g5h.get("fraction", 1.0)
    frac_7d = g7d.get("fraction", 1.0)
    cd_5h = g5h.get("countdown", "")
    cd_7d = g7d.get("countdown", "")
    is_live = g5h.get("isLive", False)

    if status == "ACTIVE":
        status_tag = f"\033[38;2;114;188;130m🟢 {status}\033[0m"
    elif status in ("NEED_LOGIN", "AUTH NEEDED"):
        status_tag = f"\033[38;2;245;158;11m🔑 NEED LOGIN\033[0m"
    else:
        status_tag = f"\033[38;2;239;68;68m🔴 {status}\033[0m"

    tier_tag = f"\033[48;2;194;65;12m\033[1;38;2;254;215;170m ✺ {tier} \033[0m"
    tag_priority = "\033[48;2;24;27;38m\033[38;2;160;174;192m Priority: 100 \033[0m"
    api_source_tag = "\033[38;2;56;189;248m[Live API]\033[0m" if is_live else "\033[38;2;156;163;175m[Local Cache]\033[0m"

    print(f"\n{BOLD}{WHITE}✦ Provider: \033[38;2;251;146;60m✺ Claude Code{RESET}  {tier_tag}  {tag_priority}  {api_source_tag}  {status_tag}")
    if email:
        print(f"  {DIM}Account: {email}{RESET}")

    c1 = render_card("✺", "\033[38;2;251;146;60m", "Claude 5H Session Window", cd_5h, frac_5h, width=45)
    c2 = render_card("✺", "\033[38;2;251;146;60m", "Claude 7D Weekly Remaining", cd_7d, frac_7d, width=45)
    for l1, l2 in zip(c1, c2):
        print(l1 + "  " + l2)

    print(f" {DIM}⚙️  Actions:{RESET}")
    print(f"   \033[38;2;56;189;248m⚡ Refresh nhanh\033[0m : {DIM}check-quota refresh claude{RESET}")
    print(f"   \033[38;2;114;188;130m🎯 Đăng nhập CLI\033[0m : {DIM}claude auth login{RESET}\n")


def print_codex_card(data: dict):
    tier = data.get("tier", "OPENAI")
    email = data.get("email", "")
    status = data.get("status", "ACTIVE")
    g5h = data.get("gemini5h", {})
    g7d = data.get("geminiWeekly", {})
    frac_5h = g5h.get("fraction", 1.0)
    frac_7d = g7d.get("fraction", 1.0)
    cd_5h = g5h.get("countdown", "")
    cd_7d = g7d.get("countdown", "")

    if status == "ACTIVE":
        status_tag = f"\033[38;2;114;188;130m🟢 {status}\033[0m"
    elif status in ("NEED_LOGIN", "AUTH NEEDED"):
        status_tag = f"\033[38;2;245;158;11m🔑 NEED LOGIN\033[0m"
    else:
        status_tag = f"\033[38;2;239;68;68m🔴 {status}\033[0m"

    tier_tag = f"\033[48;2;16;185;129m\033[1;38;2;209;250;229m 🟢 {tier} \033[0m"
    tag_priority = "\033[48;2;24;27;38m\033[38;2;160;174;192m Priority: 95 \033[0m"

    print(f"\n{BOLD}{WHITE}✦ Provider: \033[38;2;52;211;153m🟢 OpenAI Codex{RESET}  {tier_tag}  {tag_priority}  {status_tag}")
    if email:
        print(f"  {DIM}Account: {email}{RESET}")

    c1 = render_card("✦", "\033[38;2;52;211;153m", "Codex 5-Hour Limit", cd_5h, frac_5h, width=45)
    c2 = render_card("✦", "\033[38;2;52;211;153m", "Codex Weekly Limit", cd_7d, frac_7d, width=45)
    for l1, l2 in zip(c1, c2):
        print(l1 + "  " + l2)

    print(f" {DIM}⚙️  Actions:{RESET}")
    print(f"   \033[38;2;56;189;248m⚡ Refresh nhanh\033[0m : {DIM}check-quota refresh codex{RESET}")
    print(f"   \033[38;2;114;188;130m🎯 Đăng nhập CLI\033[0m : {DIM}codex auth login{RESET}\n")


def print_kiro_card(data: dict):
    tier = data.get("tier", "KIRO")
    email = data.get("email", "")
    status = data.get("status", "ACTIVE")
    cp = data.get("creditsPool", {})
    used = cp.get("used", 0.0)
    limit = cp.get("limit", 1000.0)
    remaining = cp.get("remaining", limit - used)
    fraction = cp.get("fraction", 1.0)
    pct = fraction * 100.0
    countdown = cp.get("countdown", "")

    if status == "ACTIVE":
        status_tag = f"\033[38;2;114;188;130m🟢 {status}\033[0m"
    elif status == "NOT LOGGED IN":
        status_tag = f"\033[38;2;245;158;11m🔑 {status}\033[0m"
    else:
        status_tag = f"\033[38;2;239;68;68m🔴 {status}\033[0m"

    tier_tag = f"\033[48;2;88;28;135m\033[1;38;2;216;180;254m 👻 {tier} \033[0m"
    tag_priority = "\033[48;2;24;27;38m\033[38;2;160;174;192m Priority: 90 \033[0m"

    print(f"\n{BOLD}{WHITE}✦ Provider: \033[38;2;192;132;252m👻 Kiro CLI{RESET}  {tier_tag}  {tag_priority}  {status_tag}")
    if email:
        print(f"  {DIM}Email: {email}{RESET}")

    fill_col, track_col = get_color_pair(pct)
    bar_w = 40
    filled = int(round(fraction * bar_w))
    empty = bar_w - filled
    bar_str = f"[{fill_col}{'█' * filled}{RESET}{track_col}{'░' * empty}{RESET}] {fill_col}{pct:5.1f}% remaining{RESET}"

    w = 72
    print(f" ┌{'─' * w}┐")
    print(f" │  {BOLD}Monthly Credits Pool{RESET}{' ' * (w - 22)}│")
    print(f" │  {bar_str}{' ' * max(0, w - str_vis_width(bar_str) - 2)}│")
    sub_text = f"{remaining:,.2f} / {limit:,.1f} credits (Used: {used:,.2f})   {countdown}"
    print(f" │  {DIM}{sub_text}{RESET}{' ' * max(0, w - str_vis_width(sub_text) - 2)}│")
    print(f" ├{'─' * w}┤")
    footer_text = f"Default Model: auto (1.0x)   •   Overages: {data.get('overageStatus', 'Disabled')}"
    print(f" │  {DIM}{footer_text}{RESET}{' ' * max(0, w - str_vis_width(footer_text) - 2)}│")
    print(f" └{'─' * w}┘")
    print(f" {DIM}⚙️  Actions:{RESET}")
    print(f"   \033[38;2;56;189;248m⚡ Refresh nhanh\033[0m : {DIM}check-quota refresh kiro{RESET}")
    print(f"   \033[38;2;114;188;130m🎯 Quản lý account\033[0m: {DIM}kiro-cli whoami{RESET}\n")


def load_cached_profiles() -> dict:
    global CACHED_PROFILES_DATA
    if CACHED_PROFILES_DATA:
        if "claude" not in CACHED_PROFILES_DATA:
            CACHED_PROFILES_DATA["claude"] = fetch_claude_quota()
        if "codex" not in CACHED_PROFILES_DATA:
            CACHED_PROFILES_DATA["codex"] = fetch_codex_quota()
        if "kiro" not in CACHED_PROFILES_DATA:
            CACHED_PROFILES_DATA["kiro"] = fetch_kiro_quota()
        return CACHED_PROFILES_DATA
    p = get_dashboard_html_path()
    if p.is_file():
        try:
            content = p.read_text(encoding="utf-8")
            marker = "const PROFILES_DATA ="
            end_marker = "\n};"
            idx1 = content.find(marker)
            if idx1 != -1:
                idx2 = content.find(end_marker, idx1)
                if idx2 != -1:
                    raw_json = content[idx1 + len(marker):idx2 + len(end_marker)].strip()
                    if raw_json.endswith(";"):
                        raw_json = raw_json[:-1].strip()
                    CACHED_PROFILES_DATA = json.loads(raw_json)
                    allowed_providers = {"claude", "codex", "kiro"}
                    purged_keys = [k for k in list(CACHED_PROFILES_DATA.keys()) if k not in allowed_providers and not is_valid_antigravity_profile(k)]
                    if purged_keys:
                        for k in purged_keys:
                            del CACHED_PROFILES_DATA[k]
                        try:
                            formatted_json = json.dumps(CACHED_PROFILES_DATA, indent=2, ensure_ascii=False)
                            new_content = content[:idx1 + len(marker)] + " " + formatted_json + ";" + content[idx2 + len(end_marker):]
                            p.write_text(new_content, encoding="utf-8")
                            sync_copies = [
                                Path.home() / ".gemini/config/plugins/d3nexus/skills/check-quota/resources/dashboard/quota_dashboard.html",
                                Path(REAL_HOME) / ".gemini/config/plugins/d3nexus/skills/check-quota/resources/dashboard/quota_dashboard.html",
                                Path(REAL_HOME) / "antigravity_homes/huynhminhtien0510/.gemini/config/plugins/d3nexus/skills/check-quota/resources/dashboard/quota_dashboard.html",
                                Path(REAL_HOME) / "antigravity_homes/huynhminhtien0510/.gemini/antigravity/brain/faba533a-ed61-4a6e-8b53-bfbf7926cccf/quota_dashboard.html",
                            ]
                            for sc in sync_copies:
                                if sc.is_file() and sc != p:
                                    try:
                                        sc.write_text(new_content, encoding="utf-8")
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                    if "claude" not in CACHED_PROFILES_DATA:
                        CACHED_PROFILES_DATA["claude"] = fetch_claude_quota()
                    if "codex" not in CACHED_PROFILES_DATA:
                        CACHED_PROFILES_DATA["codex"] = fetch_codex_quota()
                    if "kiro" not in CACHED_PROFILES_DATA:
                        CACHED_PROFILES_DATA["kiro"] = fetch_kiro_quota()
                    return CACHED_PROFILES_DATA
        except Exception as e:
            sys.stderr.write(f"Failed to load cached profiles: {e}\n")
    CACHED_PROFILES_DATA = {
        "claude": fetch_claude_quota(),
        "codex": fetch_codex_quota(),
        "kiro": fetch_kiro_quota(),
    }
    return CACHED_PROFILES_DATA


def update_cached_profile(profile: str, data: dict):
    global CACHED_PROFILES_DATA
    if not CACHED_PROFILES_DATA:
        load_cached_profiles()
    CACHED_PROFILES_DATA[profile] = data
    try:
        p = get_dashboard_html_path()
        if p.is_file():
            content = p.read_text(encoding="utf-8")
            marker = "const PROFILES_DATA ="
            end_marker = "\n};"
            idx1 = content.find(marker)
            if idx1 != -1:
                idx2 = content.find(end_marker, idx1)
                if idx2 != -1:
                    formatted_json = json.dumps(CACHED_PROFILES_DATA, indent=2, ensure_ascii=False)
                    new_content = content[:idx1 + len(marker)] + " " + formatted_json + ";" + content[idx2 + len(end_marker):]
                    p.write_text(new_content, encoding="utf-8")
                    sync_copies = [
                        Path.home() / ".gemini/config/plugins/d3nexus/skills/check-quota/resources/dashboard/quota_dashboard.html",
                        Path(REAL_HOME) / ".gemini/config/plugins/d3nexus/skills/check-quota/resources/dashboard/quota_dashboard.html",
                        Path(REAL_HOME) / "antigravity_homes/huynhminhtien0510/.gemini/config/plugins/d3nexus/skills/check-quota/resources/dashboard/quota_dashboard.html",
                        Path(REAL_HOME) / "antigravity_homes/huynhminhtien0510/.gemini/antigravity/brain/faba533a-ed61-4a6e-8b53-bfbf7926cccf/quota_dashboard.html",
                    ]
                    for sc in sync_copies:
                        if sc.is_file() and sc != p:
                            try:
                                sc.write_text(new_content, encoding="utf-8")
                            except Exception:
                                pass
    except Exception as e:
        sys.stderr.write(f"Failed to persist updated cache to HTML: {e}\n")


def format_profile_for_dashboard(profile: str, result: dict) -> dict:
    if profile == "claude":
        return fetch_claude_quota()
    if profile == "codex":
        return fetch_codex_quota()
    if profile == "kiro":
        return fetch_kiro_quota()

    current = load_cached_profiles().get(profile, {})
    email = current.get("email") or f"{profile}@gmail.com"
    tier = current.get("tier", "PRO")
    priority = current.get("priority", 50)

    if result.get("is_appeal") or result.get("status") == "DISABLED":
        appeal_err_id = result.get("error_id") or check_profile_appeal_status(profile) or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
        return {
            "email": email,
            "tier": tier,
            "priority": priority,
            "status": "DISABLED",
            "isAppeal": True,
            "appealReason": "This service has been disabled in this account for violation of Terms of Service. Please submit an appeal to continue using this product.",
            "errorId": appeal_err_id,
            "hasArgon": current.get("hasArgon", False),
            "gemini5h": {"name": "Gemini 3.8 / Pro 5H", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
            "claude5h": {"name": "Claude 5.5 / GPT 5H", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
            "geminiWeekly": {"name": "Gemini Weekly", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
            "claudeWeekly": {"name": "Claude Weekly", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
            "argonWeekly": {"name": "Gemini 4 Argon Weekly", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True, "tags": True},
        }

    if not result.get("success"):
        appeal_err_id = check_profile_appeal_status(profile)
        if appeal_err_id:
            return {
                "email": email,
                "tier": tier,
                "priority": priority,
                "status": "DISABLED",
                "isAppeal": True,
                "appealReason": "This service has been disabled in this account for violation of Terms of Service. Please submit an appeal to continue using this product.",
                "errorId": appeal_err_id,
                "hasArgon": current.get("hasArgon", False),
                "gemini5h": {"name": "Gemini 3.8 / Pro 5H", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
                "claude5h": {"name": "Claude 5.5 / GPT 5H", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
                "geminiWeekly": {"name": "Gemini Weekly", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
                "claudeWeekly": {"name": "Claude Weekly", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
                "argonWeekly": {"name": "Gemini 4 Argon Weekly", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True, "tags": True},
            }
        return {
            "email": email,
            "tier": tier,
            "priority": priority,
            "status": "AUTH NEEDED",
            "isAppeal": False,
            "hasArgon": current.get("hasArgon", False),
            "gemini5h": {"name": "Gemini 3.8 / Pro 5H", "fraction": 1.0, "countdown": "⏱ Auth needed", "unavailable": True},
            "claude5h": {"name": "Claude 5.5 / GPT 5H", "fraction": 1.0, "countdown": "⏱ Auth needed", "unavailable": True},
            "geminiWeekly": {"name": "Gemini Weekly", "fraction": 1.0, "countdown": "⏱ Auth needed", "unavailable": True},
            "claudeWeekly": {"name": "Claude Weekly", "fraction": 1.0, "countdown": "⏱ Auth needed", "unavailable": True},
            "argonWeekly": {"name": "Gemini 4 Argon Weekly", "fraction": 0.0, "countdown": "⏱ Auth needed", "unavailable": True, "tags": True},
        }

    groups = result.get("groups", [])
    items = parse_quota_items(groups)

    has_argon = items["argon_weekly"]["available"]
    has_5h = items["gem_5h"]["available"] or items["cld_5h"]["available"]
    tier = "PRO" if has_5h else "FREE"
    priority = 50 if has_5h else 20

    is_exhausted = (
        items["gem_5h"]["fraction"] == 0 and
        items["cld_5h"]["fraction"] == 0 and
        items["gem_weekly"]["fraction"] == 0 and
        items["cld_weekly"]["fraction"] == 0
    )
    status = "EXHAUSTED" if is_exhausted else "ACTIVE"

    gem_5h_reset = items["gem_5h"]["reset_time"]
    gem_w_reset = items["gem_weekly"]["reset_time"]

    # Compute exact local reset time and accurate real-time countdown
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    gem_5h_ts = 0
    local_5h_reset = ""
    is_5h_active = False

    if gem_5h_reset:
        try:
            dt_5h = datetime.datetime.fromisoformat(gem_5h_reset.replace("Z", "+00:00"))
            gem_5h_ts = int(dt_5h.timestamp())
            local_5h_reset = dt_5h.astimezone().strftime("%H:%M:%S")
            rem_sec_5h = int((dt_5h - now_utc).total_seconds())
            if 0 < rem_sec_5h < 5 * 3600 and items["gem_5h"]["fraction"] < 1.0:
                is_5h_active = True
        except Exception:
            pass

    gem_w_ts = 0
    local_w_reset = ""
    if gem_w_reset:
        try:
            dt_w = datetime.datetime.fromisoformat(gem_w_reset.replace("Z", "+00:00"))
            gem_w_ts = int(dt_w.timestamp())
            local_w_reset = dt_w.astimezone().strftime("%d/%m %H:%M")
        except Exception:
            pass

    # Save to hashed SQLite session store!
    save_session_record(profile, gem_5h_ts, gem_w_ts, items["gem_5h"]["fraction"], is_5h_active)

    countdown_5h_str = format_countdown(gem_5h_reset) if gem_5h_reset else "⏱ 4h 59m"
    if local_5h_reset and countdown_5h_str != "⏱ --":
        countdown_5h_str += f" ({local_5h_reset})"

    countdown_cld_str = format_countdown(items["cld_5h"]["reset_time"]) if items["cld_5h"]["reset_time"] else "⏱ 4h 59m"
    if items["cld_5h"]["reset_time"]:
        try:
            dt_cld = datetime.datetime.fromisoformat(items["cld_5h"]["reset_time"].replace("Z", "+00:00"))
            countdown_cld_str += f" ({dt_cld.astimezone().strftime('%H:%M:%S')})"
        except Exception:
            pass

    countdown_w_str = format_countdown(gem_w_reset) if gem_w_reset else "⏱ 6d 20h"
    if local_w_reset and countdown_w_str != "⏱ --":
        countdown_w_str += f" ({local_w_reset})"

    countdown_cld_w_str = format_countdown(items["cld_weekly"]["reset_time"]) if items["cld_weekly"]["reset_time"] else "⏱ 6d 20h"
    countdown_arg_str = format_countdown(items["argon_weekly"]["reset_time"]) if items["argon_weekly"]["reset_time"] else ("⏱ 6d 20h" if has_argon else "Unavailable N/A")

    return {
        "email": email,
        "tier": tier,
        "priority": priority,
        "status": status,
        "isAppeal": False,
        "isSessionActive": is_5h_active,
        "resetTime": gem_5h_reset,
        "resetTimeLocal": local_5h_reset,
        "hasArgon": has_argon,
        "gemini5h": {
            "name": "Gemini 3.8 / Pro 5H",
            "fraction": items["gem_5h"]["fraction"],
            "countdown": countdown_5h_str,
            "resetTime": gem_5h_reset,
            "resetTimeLocal": local_5h_reset,
            "unavailable": not items["gem_5h"]["available"],
        },
        "claude5h": {
            "name": "Claude 5.5 / GPT 5H",
            "fraction": items["cld_5h"]["fraction"],
            "countdown": countdown_cld_str,
            "resetTime": items["cld_5h"]["reset_time"],
            "unavailable": not items["cld_5h"]["available"],
        },
        "geminiWeekly": {
            "name": "Gemini Weekly",
            "fraction": items["gem_weekly"]["fraction"],
            "countdown": countdown_w_str,
            "resetTime": gem_w_reset,
            "resetTimeLocal": local_w_reset,
            "unavailable": not items["gem_weekly"]["available"],
        },
        "claudeWeekly": {
            "name": "Claude Weekly",
            "fraction": items["cld_weekly"]["fraction"],
            "countdown": countdown_cld_w_str,
            "resetTime": items["cld_weekly"]["reset_time"],
            "unavailable": not items["cld_weekly"]["available"],
        },
        "argonWeekly": {
            "name": "Gemini 4 Argon Weekly",
            "fraction": items["argon_weekly"]["fraction"] if items["argon_weekly"]["available"] else 0.0,
            "countdown": countdown_arg_str,
            "resetTime": items["argon_weekly"]["reset_time"],
            "unavailable": not has_argon,
            "tags": True,
        },
    }


def execute_ping_profile(profile: str, force: bool = False) -> dict:
    # 1. Provider: Claude Code
    if profile == "claude":
        claude_quota = fetch_claude_quota()
        if claude_quota.get("isSessionActive") and not force:
            rem = claude_quota.get("remainingCountdown", "5h")
            msg = f"Phiên Claude 5H đang active ({rem}). Bỏ qua ping."
            return {
                "profile": "claude",
                "success": True,
                "status": "ACTIVE",
                "isSessionActive": True,
                "skipped": True,
                "duration_ms": 5,
                "message": msg,
            }
        t0 = time.time()
        try:
            env = os.environ.copy()
            env["HOME"] = REAL_HOME
            claude_bin = shutil.which("claude") or "/usr/local/bin/claude"
            cmd = [
                claude_bin,
                "--safe-mode",
                "--disable-slash-commands",
                "--tools", "",
                "--model", "haiku",
                "-p", "1"
            ]
            res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=25)
            dur = int((time.time() - t0) * 1000)
            if res.returncode == 0:
                fetch_claude_quota()  # update session store
                return {"profile": "claude", "success": True, "duration_ms": dur, "message": f"Kích hoạt Claude thành công ({dur}ms)"}
            return {"profile": "claude", "success": False, "duration_ms": dur, "error": res.stderr.strip() or f"Code {res.returncode}"}
        except subprocess.TimeoutExpired:
            return {"profile": "claude", "success": False, "duration_ms": 25000, "error": "Request timed out (25s)"}
        except Exception as e:
            return {"profile": "claude", "success": False, "duration_ms": 50, "error": str(e)}

    # 2. Provider: OpenAI Codex
    if profile == "codex":
        codex_quota = fetch_codex_quota()
        if codex_quota.get("isSessionActive") and not force:
            rem = codex_quota.get("remainingCountdown", "5h")
            msg = f"Phiên Codex 5H đang active ({rem}). Bỏ qua ping."
            return {
                "profile": "codex",
                "success": True,
                "status": "ACTIVE",
                "isSessionActive": True,
                "skipped": True,
                "duration_ms": 5,
                "message": msg,
            }
        t0 = time.time()
        try:
            env = os.environ.copy()
            env["HOME"] = REAL_HOME
            codex_bin = shutil.which("codex") or "/usr/local/bin/codex"
            cmd = [
                codex_bin,
                "exec",
                "1",
                "--ephemeral",
                "--skip-git-repo-check",
            ]
            res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=25)
            dur = int((time.time() - t0) * 1000)
            if res.returncode == 0:
                fetch_codex_quota()  # update session store
                return {"profile": "codex", "success": True, "duration_ms": dur, "message": f"Kích hoạt Codex thành công ({dur}ms)"}
            return {"profile": "codex", "success": False, "duration_ms": dur, "error": res.stderr.strip() or f"Code {res.returncode}"}
        except subprocess.TimeoutExpired:
            return {"profile": "codex", "success": False, "duration_ms": 25000, "error": "Request timed out (25s)"}
        except Exception as e:
            return {"profile": "codex", "success": False, "duration_ms": 50, "error": str(e)}

    # 3. Provider: Kiro CLI
    if profile == "kiro":
        k_data = fetch_kiro_quota()
        update_cached_profile("kiro", k_data)
        rem = k_data.get("remainingCountdown", "")
        return {
            "profile": "kiro",
            "success": True,
            "duration_ms": 150,
            "message": f"Kiro Quota đã được đồng bộ ({rem})"
        }

    # 4. Antigravity profile:
    ag_home = f"{REAL_HOME}/antigravity_homes/{profile}"
    if not os.path.isdir(ag_home):
        return {"profile": profile, "success": False, "error": f"Profile home not found: {ag_home}"}

    appeal_err_id = check_profile_appeal_status(profile)
    if appeal_err_id:
        return {
            "profile": profile,
            "success": False,
            "status": "DISABLED",
            "is_appeal": True,
            "error_id": appeal_err_id,
            "duration_ms": 50,
            "error": "Tài khoản bị vô hiệu hóa do vi phạm Điều khoản (Terms of Service / Submit an appeal)"
        }

    if not check_profile_auth_token(profile):
        return {
            "profile": profile,
            "success": False,
            "status": "AUTH NEEDED",
            "is_appeal": False,
            "duration_ms": 50,
            "error": "Profile chưa đăng nhập CLI. Cần đăng nhập bằng Terminal trước khi ping."
        }

    # Inspect current Argon state for this profile:
    cached_profiles = load_cached_profiles()
    cached_p = cached_profiles.get(profile, {})

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_ts = int(time.time())
    sec_rec = get_session_record(profile)
    is_5h_session_active = bool(
        sec_rec
        and sec_rec.get("is_active")
        and sec_rec.get("reset_5h", 0) > now_ts
    )

    # 1. Gemini 5H status:
    gemini_info = cached_p.get("gemini5h")
    gemini_available = (gemini_info is not None and not gemini_info.get("unavailable", False))
    if gemini_info is None:
        gemini_available = (cached_p.get("tier", "PRO") == "PRO")
    gem_rem_sec = 0
    if gemini_info and gemini_info.get("resetTime"):
        try:
            dt_g = datetime.datetime.fromisoformat(gemini_info["resetTime"].replace("Z", "+00:00"))
            gem_rem_sec = (dt_g - now_utc).total_seconds()
        except Exception:
            pass
    is_gemini_active = (gem_rem_sec > 60) or is_5h_session_active
    should_ping_gemini = gemini_available and (force or not is_gemini_active)

    # 2. Claude 5H status:
    claude_info = cached_p.get("claude5h")
    claude_available = (claude_info is not None and not claude_info.get("unavailable", False))
    if claude_info is None:
        claude_available = (cached_p.get("tier", "PRO") == "PRO")
    cld_rem_sec = 0
    if claude_info and claude_info.get("resetTime"):
        try:
            dt_c = datetime.datetime.fromisoformat(claude_info["resetTime"].replace("Z", "+00:00"))
            cld_rem_sec = (dt_c - now_utc).total_seconds()
        except Exception:
            pass
    is_claude_active = (cld_rem_sec > 60) or is_5h_session_active
    should_ping_claude = claude_available and (force or not is_claude_active)

    # 3. Argon status:
    has_argon = cached_p.get("hasArgon", False)
    argon_info = cached_p.get("argonWeekly", {})
    argon_unavailable = argon_info.get("unavailable", False)
    argon_fraction = argon_info.get("fraction", 0.0)
    argon_reset = argon_info.get("resetTime", "")

    argon_rem_sec = 7 * 86400
    if argon_reset:
        try:
            dt_a = datetime.datetime.fromisoformat(argon_reset.replace("Z", "+00:00"))
            argon_rem_sec = (dt_a - now_utc).total_seconds()
        except Exception:
            pass

    # Argon Activation Rules:
    # 1. Tự động kích hoạt nếu vẫn max 7D: fraction >= 0.999 VÀ rem_sec >= (7*86400 - 3600)
    # 2. Nếu đã kích hoạt, reset time < 7h (rem_sec < 7 * 3600): TUYỆT ĐỐI KHÔNG GỬI
    # 3. Nếu đã kích hoạt (chu kỳ đang chạy): KHÔNG GỬI
    is_argon_max_7d = (argon_fraction >= 0.999) and (argon_rem_sec >= (7 * 86400 - 3600))
    is_argon_near_reset = (argon_rem_sec < 7 * 3600)  # reset time < 7h

    should_ping_argon = (
        has_argon
        and not argon_unavailable
        and not is_argon_near_reset
        and (force or is_argon_max_7d)
    )

    # If all models are already active, skip cleanly
    if not should_ping_gemini and not should_ping_claude and not should_ping_argon:
        active_parts = []
        if gemini_available:
            active_parts.append(f"Gemini 5H ({int(gem_rem_sec // 3600)}h {int((gem_rem_sec % 3600) // 60)}m)")
        if claude_available:
            cld_str = f"{int(cld_rem_sec // 3600)}h {int((cld_rem_sec % 3600) // 60)}m" if cld_rem_sec > 60 else (
                f"{(sec_rec['reset_5h'] - now_ts) // 3600}h {((sec_rec['reset_5h'] - now_ts) % 3600) // 60}m" if sec_rec else "5h"
            )
            active_parts.append(f"Claude 5H ({cld_str})")
        if has_argon and not argon_unavailable:
            if is_argon_near_reset:
                active_parts.append("Argon < 7h (bỏ qua)")
            else:
                active_parts.append("Argon đã kích hoạt")
        elif not has_argon or argon_unavailable:
            active_parts.append("Không hỗ trợ Argon")

        msg = f"Tất cả models đang trong phiên hoạt động ({', '.join(active_parts)}). Bỏ qua ping."
        return {
            "profile": profile,
            "success": True,
            "status": "ACTIVE",
            "isSessionActive": True,
            "skipped": True,
            "duration_ms": 5,
            "message": msg,
            "pinged_gemini": False,
            "pinged_claude": False,
            "pinged_argon": False,
        }

    # Unlock keychain if needed
    wait_for_launch_lock()
    profile_kc = f"{ag_home}/Library/Keychains/{profile}.keychain-db"
    if os.path.exists(profile_kc):
        subprocess.run(["security", "unlock-keychain", "-p", KC_PASS, profile_kc], capture_output=True)

    env = os.environ.copy()
    env.update({
        "HOME": ag_home,
        "AGY_PROFILE": profile,
        "AGY_CLI_MODE": "1",
        "TMPDIR": f"/tmp/ag_{profile}",
        "BROWSER": "true",
    })

    t0 = time.time()
    pinged_gemini = False
    pinged_claude = False
    pinged_argon = False
    jitter_applied = 0.0
    prompt_gem = ""
    prompt_cld = ""
    prompt_arg = ""

    # 1. Ping Gemini 5H (if needed)
    if should_ping_gemini:
        prompt_gem = random.choice(NATURAL_PROMPTS)
        try:
            res_gem = subprocess.run([AGY_BIN, "-p", prompt_gem], env=env, capture_output=True, text=True, timeout=25)
            out_all = (res_gem.stdout or "") + " " + (res_gem.stderr or "")
            appeal_out_id = check_profile_appeal_status(profile, out_all)
            low_out = out_all.lower()
            if appeal_out_id or "submit an appeal" in low_out or "violation of terms of service" in low_out or "service has been disabled" in low_out:
                err_id = appeal_out_id or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
                record_profile_disabled(profile, err_id)
                disabled_data = format_profile_for_dashboard(profile, {
                    "success": False,
                    "status": "DISABLED",
                    "is_appeal": True,
                    "error_id": err_id
                })
                update_cached_profile(profile, disabled_data)
                return {
                    "profile": profile,
                    "success": False,
                    "status": "DISABLED",
                    "is_appeal": True,
                    "error_id": err_id,
                    "duration_ms": int((time.time() - t0) * 1000),
                    "error": f"Tài khoản bị vô hiệu hóa do vi phạm Điều khoản (Terms of Service / Submit an appeal). Mã lỗi: {err_id}"
                }
            if res_gem.returncode == 0:
                pinged_gemini = True
            else:
                return {
                    "profile": profile,
                    "success": False,
                    "duration_ms": int((time.time() - t0) * 1000),
                    "error": res_gem.stderr.strip() or f"Gemini ping exited with code {res_gem.returncode}"
                }
        except subprocess.TimeoutExpired:
            return {"profile": profile, "success": False, "duration_ms": 25000, "error": "Gemini ping timed out (25s)"}
        except Exception as e:
            return {"profile": profile, "success": False, "duration_ms": 50, "error": str(e)}

    # 2. Ping Claude (claude-sonnet-5-5-low) model (if needed)
    if should_ping_claude:
        if pinged_gemini:
            j = round(random.uniform(1.5, 2.5), 2)
            jitter_applied += j
            time.sleep(j)

        other_cld = [p for p in NATURAL_PROMPTS if p != prompt_gem] or NATURAL_PROMPTS
        prompt_cld = random.choice(other_cld)
        try:
            res_cld = subprocess.run([AGY_BIN, "--model", "claude-sonnet-5-5-low", "-p", prompt_cld], env=env, capture_output=True, text=True, timeout=25)
            out_all = (res_cld.stdout or "") + " " + (res_cld.stderr or "")
            appeal_out_id = check_profile_appeal_status(profile, out_all)
            low_out = out_all.lower()
            if appeal_out_id or "submit an appeal" in low_out or "violation of terms of service" in low_out or "service has been disabled" in low_out:
                err_id = appeal_out_id or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
                record_profile_disabled(profile, err_id)
                disabled_data = format_profile_for_dashboard(profile, {
                    "success": False,
                    "status": "DISABLED",
                    "is_appeal": True,
                    "error_id": err_id
                })
                update_cached_profile(profile, disabled_data)
                return {
                    "profile": profile,
                    "success": False,
                    "status": "DISABLED",
                    "is_appeal": True,
                    "error_id": err_id,
                    "duration_ms": int((time.time() - t0) * 1000),
                    "error": f"Tài khoản bị vô hiệu hóa do vi phạm Điều khoản (Terms of Service / Submit an appeal). Mã lỗi: {err_id}"
                }
            if res_cld.returncode == 0:
                pinged_claude = True
            else:
                return {
                    "profile": profile,
                    "success": False,
                    "duration_ms": int((time.time() - t0) * 1000),
                    "error": res_cld.stderr.strip() or f"Claude ping exited with code {res_cld.returncode}"
                }
        except subprocess.TimeoutExpired:
            return {"profile": profile, "success": False, "duration_ms": 25000, "error": "Claude ping timed out (25s)"}
        except Exception as e:
            return {"profile": profile, "success": False, "duration_ms": 50, "error": str(e)}

    # 3. Ping Argon (if max 7D and not near reset)
    if should_ping_argon:
        # Mandatory humanized jitter between requests to eliminate bot flags
        if pinged_gemini or pinged_claude:
            j = round(random.uniform(1.8, 3.0), 2)
            jitter_applied += j
            time.sleep(j)

        other_arg = [p for p in NATURAL_PROMPTS if p not in (prompt_gem, prompt_cld)] or NATURAL_PROMPTS
        prompt_argon = random.choice(other_arg)
        try:
            res_arg = subprocess.run(
                [AGY_BIN, "--model", "gemini-4-argon-low", "-p", prompt_argon],
                env=env,
                capture_output=True,
                text=True,
                timeout=25
            )
            out_all = (res_arg.stdout or "") + " " + (res_arg.stderr or "")
            appeal_out_id = check_profile_appeal_status(profile, out_all)
            low_out = out_all.lower()
            if appeal_out_id or "submit an appeal" in low_out or "violation of terms of service" in low_out or "service has been disabled" in low_out:
                err_id = appeal_out_id or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
                record_profile_disabled(profile, err_id)
                disabled_data = format_profile_for_dashboard(profile, {
                    "success": False,
                    "status": "DISABLED",
                    "is_appeal": True,
                    "error_id": err_id
                })
                update_cached_profile(profile, disabled_data)
                return {
                    "profile": profile,
                    "success": False,
                    "status": "DISABLED",
                    "is_appeal": True,
                    "error_id": err_id,
                    "duration_ms": int((time.time() - t0) * 1000),
                    "error": f"Tài khoản bị vô hiệu hóa do vi phạm Điều khoản (Terms of Service / Submit an appeal). Mã lỗi: {err_id}"
                }
            if "is not recognized" in low_out or "invalid model selection" in low_out:
                cached_p["hasArgon"] = False
                if "argonWeekly" in cached_p:
                    cached_p["argonWeekly"]["unavailable"] = True
                    cached_p["argonWeekly"]["countdown"] = "Unavailable N/A"
                update_cached_profile(profile, cached_p)
            elif res_arg.returncode == 0:
                pinged_argon = True
        except Exception:
            pass  # Argon failure does not abort if Claude succeeded

    total_dur = int((time.time() - t0) * 1000)
    jitter_applied = round(jitter_applied, 2)

    # Post-ping quota refresh to update dashboard immediately
    post_q = fetch_quota_for_profile(profile)
    if post_q.get("success"):
        f_data = format_profile_for_dashboard(profile, post_q)
        update_cached_profile(profile, f_data)

    # Build detailed success message
    act_names = []
    if pinged_gemini:
        act_names.append("Gemini 3.8 / Pro 5H")
    if pinged_claude:
        act_names.append("Claude 5.5")
    if pinged_argon:
        act_names.append("Argon 7D")

    if act_names:
        act_str = " & ".join(act_names)
        jitter_str = f", Jitter {jitter_applied}s" if jitter_applied > 0 else ""
        msg = f"Kích hoạt thành công {act_str}{jitter_str} ({total_dur}ms)"
    else:
        msg = f"Đã kiểm tra phiên làm việc của {profile} ({total_dur}ms)"

    return {
        "profile": profile,
        "success": True,
        "duration_ms": total_dur,
        "message": msg,
        "pinged_gemini": pinged_gemini,
        "pinged_claude": pinged_claude,
        "pinged_argon": pinged_argon,
        "jitter_seconds": jitter_applied,
    }


def scan_all_profiles_parallel(profiles: list) -> list:
    results = []
    # Use max_workers=3 and staggered submission to eliminate burst traffic to Google Cloud endpoints
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_profile = {}
        for p in profiles:
            future_to_profile[executor.submit(fetch_quota_for_profile, p)] = p
            time.sleep(0.2)
        for future in as_completed(future_to_profile):
            try:
                res = future.result()
                results.append(res)
            except Exception as e:
                p = future_to_profile[future]
                results.append({"profile": p, "success": False, "error": str(e)})
    results.sort(key=lambda x: profiles.index(x["profile"]) if x["profile"] in profiles else 999)
    return results


class QuotaDashboardHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if "/favicon.ico" in self.path:
            return
        try:
            code = args[1] if len(args) > 1 else "-"
            color = GREEN if str(code).startswith("2") else (AMBER if str(code).startswith("3") else RED)
            sys.stdout.write(f"  {GRAY}[{time.strftime('%H:%M:%S')}]{RESET} {CYAN}{self.command}{RESET} {self.path} {color}{code}{RESET}\n")
            sys.stdout.flush()
        except Exception:
            pass

    def send_json(self, data, status=200):
        try:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            pass

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_POST(self):
        self.do_GET()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        if path in ("/", "/index.html", "/quota_dashboard.html"):
            html_p = get_dashboard_html_path()
            if html_p.is_file():
                content = html_p.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Dashboard HTML not found")
            return

        if path == "/api/status":
            last_rf = get_last_refresh_all_time()
            now = int(time.time())
            if last_rf == 0:
                last_rf = now
                record_refresh_all_time(last_rf)
            elapsed = max(0, now - last_rf)
            can_auto = elapsed >= GLOBAL_REFRESH_INTERVAL_SECONDS
            self.send_json({
                "success": True,
                "profiles": load_cached_profiles(),
                "last_refresh_all": last_rf,
                "elapsed_seconds": elapsed,
                "can_auto_refresh": can_auto,
                "interval_seconds": GLOBAL_REFRESH_INTERVAL_SECONDS
            })
            return

        if path == "/api/check-blocked":
            profile = query.get("profile", [""])[0]
            if not profile:
                self.send_json({"success": False, "error": "Thiếu tham số profile"}, status=400)
                return
            res = probe_blocked_profile(profile)
            self.send_json(res)
            return

        if path == "/api/refresh":
            profile = query.get("profile", ["danhdue"])[0]
            if query.get("check_blocked", ["0"])[0] in ("1", "true", "True") or query.get("check_appeal", ["0"])[0] in ("1", "true", "True"):
                res = probe_blocked_profile(profile)
                self.send_json(res)
                return
            if profile == "claude":
                f_data = fetch_claude_quota()
                update_cached_profile("claude", f_data)
                self.send_json({"success": True, "profile": "claude", "duration_ms": 5, "data": f_data, "error": None})
                return
            if profile == "codex":
                f_data = fetch_codex_quota()
                update_cached_profile("codex", f_data)
                self.send_json({"success": True, "profile": "codex", "duration_ms": 5, "data": f_data, "error": None})
                return
            if profile == "kiro":
                f_data = fetch_kiro_quota()
                update_cached_profile("kiro", f_data)
                self.send_json({"success": True, "profile": "kiro", "duration_ms": 5, "data": f_data, "error": None})
                return

            cached = load_cached_profiles().get(profile, {})
            was_auth_needed = not cached or cached.get("status") == "AUTH NEEDED"
            has_auth = check_profile_auth_token(profile)

            # Post-login validation probe:
            if has_auth and was_auth_needed:
                ping_res = execute_ping_profile(profile)
                if ping_res.get("is_appeal") or ping_res.get("status") == "DISABLED":
                    err_id = ping_res.get("error_id") or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
                    record_profile_disabled(profile, err_id)
                    formatted = format_profile_for_dashboard(profile, ping_res)
                    update_cached_profile(profile, formatted)
                    self.send_json({
                        "success": False,
                        "isAppeal": True,
                        "status": "DISABLED",
                        "profile": profile,
                        "data": formatted,
                        "error": ping_res.get("error", "Tài khoản bị vô hiệu hóa (Submit an appeal)")
                    })
                    return

            result = fetch_quota_for_profile(profile)
            formatted = format_profile_for_dashboard(profile, result)
            update_cached_profile(profile, formatted)
            if result.get("is_appeal") or result.get("status") == "DISABLED":
                self.send_json({
                    "success": False,
                    "isAppeal": True,
                    "status": "DISABLED",
                    "profile": profile,
                    "data": formatted,
                    "error": result.get("error", "Tài khoản bị vô hiệu hóa (Submit an appeal)")
                })
                return
            if result.get("status") == "AUTH NEEDED" or not result.get("success"):
                self.send_json({
                    "success": False,
                    "isAuthNeeded": True,
                    "status": "AUTH NEEDED",
                    "profile": profile,
                    "data": formatted,
                    "error": result.get("error", "Profile chưa đăng nhập CLI")
                })
                return
            self.send_json({
                "success": True,
                "profile": profile,
                "duration_ms": int(result.get("duration", 0) * 1000),
                "data": formatted,
                "error": None
            })
            return

        if path == "/api/ping":
            profile = query.get("profile", ["danhdue"])[0]
            force = query.get("force", ["0"])[0] in ("1", "true", "True")
            ping_res = execute_ping_profile(profile, force=force)
            if profile == "claude":
                f_data = fetch_claude_quota()
                update_cached_profile("claude", f_data)
                self.send_json({
                    "success": ping_res.get("success", False),
                    "profile": "claude",
                    "duration_ms": ping_res.get("duration_ms", 10),
                    "data": f_data,
                    "message": ping_res.get("message"),
                    "skipped": ping_res.get("skipped", False)
                })
                return
            if profile == "codex":
                f_data = fetch_codex_quota()
                update_cached_profile("codex", f_data)
                self.send_json({
                    "success": ping_res.get("success", False),
                    "profile": "codex",
                    "duration_ms": ping_res.get("duration_ms", 10),
                    "data": f_data,
                    "message": ping_res.get("message"),
                    "skipped": ping_res.get("skipped", False)
                })
                return
            if profile == "kiro":
                f_data = fetch_kiro_quota()
                update_cached_profile("kiro", f_data)
                self.send_json({
                    "success": ping_res.get("success", False),
                    "profile": "kiro",
                    "duration_ms": ping_res.get("duration_ms", 10),
                    "data": f_data,
                    "message": ping_res.get("message"),
                    "skipped": ping_res.get("skipped", False)
                })
                return

            if ping_res.get("is_appeal") or ping_res.get("status") == "DISABLED":
                err_id = ping_res.get("error_id") or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
                record_profile_disabled(profile, err_id)
                formatted = format_profile_for_dashboard(profile, ping_res)
                update_cached_profile(profile, formatted)
                self.send_json({
                    "success": False,
                    "isAppeal": True,
                    "status": "DISABLED",
                    "profile": profile,
                    "data": formatted,
                    "error": ping_res.get("error", "Tài khoản bị vô hiệu hóa (Submit an appeal)")
                })
                return
            result = fetch_quota_for_profile(profile)
            formatted = format_profile_for_dashboard(profile, result)
            update_cached_profile(profile, formatted)
            self.send_json({
                "success": ping_res.get("success", False) and (result.get("success", False) or ping_res.get("skipped", False)),
                "profile": profile,
                "duration_ms": ping_res.get("duration_ms", 500),
                "data": formatted,
                "message": ping_res.get("message"),
                "skipped": ping_res.get("skipped", False)
            })
            return

        if path == "/api/refresh-all":
            is_auto = query.get("auto", ["0"])[0] in ("1", "true", "True")
            now = int(time.time())
            last_rf = get_last_refresh_all_time()
            if last_rf == 0:
                last_rf = now
                record_refresh_all_time(last_rf)
            elapsed = max(0, now - last_rf)

            # 30-Minute guard for automated init & reload triggers:
            if is_auto and elapsed < GLOBAL_REFRESH_INTERVAL_SECONDS:
                self.send_json({
                    "success": True,
                    "skipped": True,
                    "reason": f"Throttled: last refresh was {elapsed // 60}m ago (< 30m). Manual refresh required.",
                    "profiles": load_cached_profiles(),
                    "last_refresh_all": last_rf,
                    "elapsed_seconds": elapsed,
                    "can_auto_refresh": False,
                    "interval_seconds": GLOBAL_REFRESH_INTERVAL_SECONDS
                })
                return

            formatted_all = {}
            # 1. AI Providers: Claude, Codex & Kiro
            c_data = fetch_claude_quota()
            formatted_all["claude"] = c_data
            update_cached_profile("claude", c_data)

            x_data = fetch_codex_quota()
            formatted_all["codex"] = x_data
            update_cached_profile("codex", x_data)

            k_data = fetch_kiro_quota()
            formatted_all["kiro"] = k_data
            update_cached_profile("kiro", k_data)

            # 2. Antigravity Profiles
            profiles = get_all_profiles()
            results = scan_all_profiles_parallel(profiles)
            for r in results:
                p = r["profile"]
                f_data = format_profile_for_dashboard(p, r)
                formatted_all[p] = f_data
                update_cached_profile(p, f_data)

            record_refresh_all_time(now)
            self.send_json({
                "success": True,
                "skipped": False,
                "profiles": formatted_all,
                "last_refresh_all": now,
                "elapsed_seconds": 0,
                "can_auto_refresh": False,
                "interval_seconds": GLOBAL_REFRESH_INTERVAL_SECONDS
            })
            return

        if path == "/api/login":
            profile = query.get("profile", [""])[0]
            if not profile or not re.fullmatch(r"[a-zA-Z0-9_-]+", profile):
                self.send_json({"success": False, "error": "Invalid profile name"}, 400)
                return
            if profile == "claude":
                cli_cmd = "claude auth login"
            elif profile == "codex":
                cli_cmd = "codex auth login"
            elif profile == "kiro":
                cli_cmd = "kiro-cli login"
            else:
                cli_cmd = f"{profile}-cli"
            osa = f'''tell application "Terminal"
                activate
                do script "{cli_cmd}"
            end tell'''
            subprocess.run(["osascript", "-e", osa], env=build_clean_host_env(), capture_output=True)
            self.send_json({"success": True, "message": f"Terminal opened for {profile} login"})
            return

        if path == "/api/open-cli":
            profile = query.get("profile", ["danhdue"])[0]
            if not profile or not re.fullmatch(r"[a-zA-Z0-9_-]+", profile):
                self.send_json({"success": False, "error": "Invalid profile name"}, 400)
                return
            if profile == "claude":
                cli_cmd = "claude"
            elif profile == "codex":
                cli_cmd = "codex"
            elif profile == "kiro":
                cli_cmd = "kiro-cli"
            else:
                target_profile = "danhdue" if profile == "default" else profile
                cli_cmd = f"source ~/.zshrc && ag_run {shlex.quote(target_profile)} cli"
            osa = f'''tell application "Terminal"
                activate
                do script "{cli_cmd}"
            end tell'''
            subprocess.run(["osascript", "-e", osa], env=build_clean_host_env(), capture_output=True)
            self.send_json({"success": True, "message": f"Terminal opened for {profile} CLI"})
            return

        if path == "/api/open-ide":
            profile = query.get("profile", ["danhdue"])[0]
            if not profile or not re.fullmatch(r"[a-zA-Z0-9_-]+", profile):
                self.send_json({"success": False, "error": "Invalid profile name"}, 400)
                return

            target_profile = "danhdue" if profile == "default" else profile
            clean_env = build_clean_host_env()

            # Trigger profile CLI command directly (e.g. 'danhdue', 'hau') from a sanitized host environment
            cmd = (
                "unset ELECTRON_RUN_AS_NODE ELECTRON_NO_ASAR TERM_PROGRAM TERM_PROGRAM_VERSION "
                "TERM_SESSION_ID AGY_PROFILE AGY_CLI_MODE ZDOTDIR VSCODE_GIT_IPC_HANDLE "
                "VSCODE_IPC_HOOK_CLI VSCODE_RESOLVING_ENVIRONMENT; "
                f"if type {target_profile} >/dev/null 2>&1; then {target_profile}; "
                f"else ag_run {shlex.quote(target_profile)}; fi"
            )
            subprocess.Popen(
                ["zsh", "-ic", cmd],
                env=clean_env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )
            self.send_json({"success": True, "message": f"Đã kích hoạt lệnh '{target_profile}' mở Antigravity IDE"})
            return

        self.send_error(404, "API endpoint not found")


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


PID_FILE = Path("/tmp/agy_quota_server.pid")
LOG_FILE = Path("/tmp/agy_quota_server.log")


def is_server_alive(port: int = 8765) -> bool:
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status", timeout=1.5)
        return req.status == 200
    except Exception:
        return False


def get_server_pid(port: int = 8765) -> int | None:
    if PID_FILE.is_file():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            return pid
        except Exception:
            try:
                PID_FILE.unlink(missing_ok=True)
            except Exception:
                pass
    try:
        out = subprocess.check_output(["lsof", "-ti", f":{port}"], text=True, stderr=subprocess.DEVNULL).strip()
        if out:
            pids = [int(p) for p in out.split() if p.isdigit()]
            if pids:
                return pids[0]
    except Exception:
        pass
    return None


def stop_server(port: int = 8765) -> bool:
    pid = get_server_pid(port)
    alive = is_server_alive(port)
    if not pid and not alive:
        print(f"\n{AMBER}ℹ️ Quota Web Server hiện không chạy trên cổng {port}.{RESET}\n")
        return False

    print(f"\n{CYAN}🛑 Đang dừng Quota Web Server (PID {pid or 'unknown'})...{RESET}")
    killed = False
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            for _ in range(25):
                time.sleep(0.1)
                try:
                    os.kill(pid, 0)
                except OSError:
                    killed = True
                    break
            if not killed:
                os.kill(pid, signal.SIGKILL)
                killed = True
        except Exception:
            pass

    try:
        out = subprocess.check_output(["lsof", "-ti", f":{port}"], text=True, stderr=subprocess.DEVNULL).strip()
        for p in out.split():
            if p.isdigit():
                try:
                    os.kill(int(p), signal.SIGKILL)
                    killed = True
                except Exception:
                    pass
    except Exception:
        pass

    PID_FILE.unlink(missing_ok=True)
    print(f"{BOLD}{GREEN}✅ Đã dừng Quota Web Server thành công.{RESET}\n")
    return True


def status_server(port: int = 8765):
    alive = is_server_alive(port)
    pid = get_server_pid(port)
    if alive:
        pid_str = f" (PID {pid})" if pid else ""
        print(f"\n{BOLD}{GREEN}⚡ Quota Web Server đang HOẠT ĐỘNG{pid_str}:{RESET}")
        print(f"     URL : {WHITE}http://127.0.0.1:{port}{RESET}")
        print(f"     Logs: {GRAY}{LOG_FILE}{RESET}")
        print(f"  💡 Mở dashboard: {CYAN}check-quota --ui{RESET}")
        print(f"  🛑 Dừng server : {AMBER}check-quota --stop{RESET}\n")
    else:
        print(f"\n{GRAY}ℹ️ Quota Web Server hiện KHÔNG HOẠT ĐỘNG.{RESET}")
        print(f"  🚀 Chạy {CYAN}check-quota --ui{RESET} để khởi động ngầm.\n")


def start_server_daemon(port: int = 8765, auto_open: bool = True):
    if is_server_alive(port):
        pid = get_server_pid(port)
        pid_str = f" (PID {pid})" if pid else ""
        print(f"\n{BOLD}{GREEN}⚡ Quota Web Server đã đang hoạt động{pid_str} tại:{RESET} {WHITE}http://127.0.0.1:{port}{RESET}")
        if auto_open:
            print(f"  {CYAN}🌐 Đang mở Quota Dashboard trong trình duyệt...{RESET}\n")
            subprocess.run(["open", f"http://127.0.0.1:{port}"])
        print(f"  {GRAY}💡 Dừng server bất cứ lúc nào bằng lệnh: {WHITE}check-quota --stop{RESET}\n")
        return

    # Cleanup any stuck PID/port
    if PID_FILE.is_file() or get_server_pid(port):
        stop_server(port)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log_fp = open(LOG_FILE, "a", encoding="utf-8")
    log_fp.write(f"\n--- Quota Server daemon starting at {datetime.datetime.now().isoformat()} ---\n")
    log_fp.flush()

    script_path = str(Path(__file__).resolve())
    cmd = [sys.executable, script_path, "_serve", "--port", str(port)]
    proc = subprocess.Popen(
        cmd,
        env=build_clean_host_env(),
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=log_fp,
        stderr=log_fp,
        close_fds=True
    )
    PID_FILE.write_text(str(proc.pid))

    ready = False
    for _ in range(35):
        time.sleep(0.1)
        if is_server_alive(port):
            ready = True
            break
        if proc.poll() is not None:
            break

    if not ready:
        print(f"\n{RED}❌ Không thể khởi động Quota Web Server ngầm.{RESET}")
        print(f"  Vui lòng xem chi tiết lỗi tại: {WHITE}{LOG_FILE}{RESET}\n")
        return

    url = f"http://127.0.0.1:{port}"
    print(f"\n{BOLD}{CYAN}{'='*86}{RESET}")
    print(f"{BOLD}{GREEN}  🚀 AI MULTI-PROFILE QUOTA LIVE WEB SERVER (DAEMON){RESET}")
    print(f"     URL : {WHITE}{url}{RESET}")
    print(f"     PID : {WHITE}{proc.pid}{RESET}  |  Logs: {GRAY}{LOG_FILE}{RESET}")
    print(f"{BOLD}{CYAN}{'='*86}{RESET}")
    print(f"  ✨ {BOLD}Chạy ngầm độc lập (Detached Process):{RESET}")
    print(f"     • Bạn có thể {BOLD}{GREEN}tắt Terminal này hoàn toàn{RESET}, web vẫn tiếp tục hoạt động!")
    print(f"     • Tự động kết nối và tương tác Live Refresh với 23 profiles.")
    print(f"     • Dừng server khi cần bằng lệnh: {BOLD}{AMBER}check-quota --stop{RESET}\n")

    if auto_open:
        print(f"  {CYAN}🌐 Đang mở Quota Dashboard trong trình duyệt mặc định...{RESET}\n")
        subprocess.run(["open", url])


def run_internal_serve(port: int = 8765):
    # Ignore SIGHUP so terminal closing never kills the daemon
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, signal.SIG_IGN)

    def handle_term(signum, frame):
        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_term)
    signal.signal(signal.SIGINT, handle_term)

    PID_FILE.write_text(str(os.getpid()))

    httpd = None
    for p in range(port, port + 10):
        try:
            httpd = ThreadingTCPServer(("127.0.0.1", p), QuotaDashboardHandler)
            port = p
            break
        except OSError:
            continue

    if not httpd:
        sys.stderr.write(f"Cannot bind to port {port}..{port+9}\n")
        sys.exit(1)

    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
        PID_FILE.unlink(missing_ok=True)


def run_quota_web_server(port: int = 8765, auto_open: bool = True):
    if is_server_alive(port):
        pid = get_server_pid(port)
        pid_str = f" (PID {pid})" if pid else ""
        print(f"\n{BOLD}{GREEN}⚡ Quota Web Server đã đang hoạt động{pid_str} tại:{RESET} {WHITE}http://127.0.0.1:{port}{RESET}")
        if auto_open:
            print(f"  {CYAN}🌐 Đang mở Quota Dashboard trong trình duyệt...{RESET}\n")
            subprocess.run(["open", f"http://127.0.0.1:{port}"])
        print(f"  {GRAY}💡 Dừng server bất cứ lúc nào bằng lệnh: {WHITE}check-quota --stop{RESET}\n")
        return

    httpd = None
    for p in range(port, port + 10):
        try:
            httpd = ThreadingTCPServer(("127.0.0.1", p), QuotaDashboardHandler)
            port = p
            break
        except OSError:
            continue

    if not httpd:
        print(f"\n{RED}❌ Không thể bind cổng từ {port} đến {port + 9}. Vui lòng thử lại.{RESET}\n")
        return

    PID_FILE.write_text(str(os.getpid()))
    url = f"http://127.0.0.1:{port}"
    print(f"\n{BOLD}{CYAN}{'='*86}{RESET}")
    print(f"{BOLD}{GREEN}  🚀 AI MULTI-PROFILE QUOTA LIVE WEB SERVER (FOREGROUND){RESET}")
    print(f"     URL: {WHITE}{url}{RESET}")
    print(f"{BOLD}{CYAN}{'='*86}{RESET}")
    print(f"  ⚡ {BOLD}Tính năng tương tác trực tiếp (Interactive Endpoints):{RESET}")
    print(f"     • {CYAN}GET  /api/status{RESET}            : Xem quota tất cả 23 profiles")
    print(f"     • {CYAN}GET  /api/refresh?profile=p{RESET} : Live Refresh 110ms cho profile p")
    print(f"     • {CYAN}GET  /api/ping?profile=p{RESET}    : Gửi 1-token kích hoạt countdown 5H & tuần")
    print(f"     • {CYAN}GET  /api/refresh-all{RESET}       : Quét song song và cập nhật toàn bộ profiles")
    print(f"     • {CYAN}GET  /api/login?profile=p{RESET}   : Mở Terminal thực hiện p-cli để đăng nhập")
    print(f"     • {CYAN}GET  /api/open-cli?profile=p{RESET}: Mở Terminal chạy CLI cho profile p")
    print(f"     • {CYAN}GET  /api/open-ide?profile=p{RESET}: Mở Antigravity IDE (GUI) cho profile p")
    print(f"\n  🌐 Đang mở Quota Dashboard trên trình duyệt mặc định...")
    print(f"  💡 Nhấn {AMBER}Ctrl + C{RESET} trong Terminal để dừng server bất kỳ lúc nào.\n")

    if auto_open:
        subprocess.run(["open", url])

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{AMBER}🛑 Server đã dừng an toàn (Ctrl+C). Tạm biệt!{RESET}\n")
    finally:
        httpd.server_close()
        PID_FILE.unlink(missing_ok=True)


def main():
    args = sys.argv[1:]
    target = args[0] if args else None

    # Handle internal server runner
    if target == "_serve":
        port = 8765
        if "--port" in args:
            idx = args.index("--port")
            if idx + 1 < len(args) and args[idx + 1].isdigit():
                port = int(args[idx + 1])
        run_internal_serve(port=port)
        return

    # Handle stop
    if target in ("--stop", "stop", "-k", "--kill"):
        stop_server(port=8765)
        return

    # Handle status
    if target in ("--status", "status"):
        status_server(port=8765)
        return

    # Handle help
    if target in ("-h", "--help", "help"):
        print(f"\n{BOLD}{CYAN}Antigravity Quota CLI (check-quota / agy-quota){RESET}")
        print("Usage:")
        print("  check-quota                     Xem quota cho profile hiện tại")
        print("  check-quota <profile>           Xem quota cho profile cụ thể (e.g. danhdue, tess)")
        print("  check-quota all                 Quét và hiển thị chi tiết tất cả profiles")
        print("  check-quota all --table         Bảng tóm tắt gọn gàng 122 ký tự cho tất cả profiles")
        print("  check-quota ping <profile>      Gửi 1-token kích hoạt countdown 5H & tuần (Ping Model)")
        print("  check-quota refresh <profile>   Làm mới quota và đồng bộ session qua /usage")
        print("  check-quota --ui                Mở Quota Dashboard trực quan (chạy ngầm, tắt terminal thoải mái)")
        print("  check-quota --ui -f             Chạy Quota Dashboard ở foreground terminal (dành cho debug)")
        print("  check-quota --stop              Dừng Quota Dashboard Web Server đang chạy ngầm")
        print("  check-quota --status            Kiểm tra trạng thái Quota Web Server\n")
        return

    # Handle UI/Web Dashboard
    if target in ("--web", "--ui", "dashboard", "--dashboard", "web", "ui"):
        auto_open = "--no-open" not in args
        if "--static" in args or "--file" in args:
            found_dash = get_dashboard_html_path()
            if found_dash.is_file():
                print(f"\n{GREEN}🌐 Opening Quota Dashboard file in browser: {found_dash}{RESET}\n")
                subprocess.run(["open", str(found_dash)])
            else:
                print(f"\n{RED}❌ Quota dashboard file not found.{RESET}\n")
            return
        if "--foreground" in args or "-f" in args:
            run_quota_web_server(port=8765, auto_open=auto_open)
        else:
            start_server_daemon(port=8765, auto_open=auto_open)
        return

    # Detect default profile if none specified
    if not target or target == "current":
        env_profile = os.environ.get("AGY_PROFILE")
        if not env_profile:
            home = os.environ.get("HOME", "")
            if "antigravity_homes" in home:
                env_profile = os.path.basename(home)
            else:
                env_profile = "danhdue"
        target = env_profile

    if target in ("ping", "activate"):
        sub_target = args[1] if len(args) > 1 and not args[1].startswith("-") else "danhdue"
        force = "--force" in args or "-f" in args
        print(f"\n{CYAN}🎯 Kích hoạt phiên làm việc cho '{sub_target}' (force={force})...{RESET}")
        res = execute_ping_profile(sub_target, force=force)
        if res.get("skipped"):
            print(f"{AMBER}⏭️  {res.get('message')}{RESET}\n")
            return
        if res.get("success"):
            print(f"{GREEN}✅ {res.get('message')}{RESET}\n")
        else:
            print(f"{RED}❌ {res.get('error')}{RESET}\n")
        return

    if target in ("check-blocked", "test-blocked"):
        sub_target = args[1] if len(args) > 1 else "d3molt"
        print(f"\n{CYAN}⚡ Kiểm tra trạng thái tài khoản bị khóa '{sub_target}' (kèm Anti-Bot Jitter)...{RESET}")
        res = probe_blocked_profile(sub_target)
        if res.get("unblocked"):
            print(f"{BOLD}{GREEN}{res.get('message')}{RESET}\n")
        elif res.get("cooldown"):
            print(f"{AMBER}⏳ {res.get('error')}{RESET}\n")
        elif res.get("is_appeal"):
            print(f"{RED}🚫 {res.get('error')}{RESET}\n")
        else:
            print(f"{RED}❌ {res.get('error', 'Lỗi kiểm tra')}{RESET}\n")
        return

    if target == "refresh":
        sub_target = args[1] if len(args) > 1 else "danhdue"
        print(f"\n{CYAN}⚡ Running quick refresh for '{sub_target}'...{RESET}")
        if sub_target == "claude":
            c_data = fetch_claude_quota()
            update_cached_profile("claude", c_data)
            print(f"{GREEN}✅ Claude Code refreshed successfully!{RESET}\n")
            return
        if sub_target == "codex":
            x_data = fetch_codex_quota()
            update_cached_profile("codex", x_data)
            print(f"{GREEN}✅ OpenAI Codex refreshed successfully!{RESET}\n")
            return
        if sub_target == "kiro":
            k_data = fetch_kiro_quota()
            update_cached_profile("kiro", k_data)
            print(f"{GREEN}✅ Kiro CLI refreshed successfully!{RESET}\n")
            return
        ag_home = f"{REAL_HOME}/antigravity_homes/{sub_target}"
        if not os.path.isdir(ag_home):
            print(f"{RED}❌ Profile home not found: {ag_home}{RESET}\n")
            return
        if not check_profile_auth_token(sub_target):
            print(f"{AMBER}⚠️ Profile '{sub_target}' chưa đăng nhập CLI. Vui lòng chạy '{sub_target}-cli' trong Terminal để đăng nhập trước.{RESET}\n")
            return
        # Unlock Keychain if exists
        profile_kc = f"{ag_home}/Library/Keychains/{sub_target}.keychain-db"
        if os.path.exists(profile_kc):
            subprocess.run(["security", "unlock-keychain", "-p", KC_PASS, profile_kc], capture_output=True)
        env = os.environ.copy()
        env.update({"HOME": ag_home, "AGY_PROFILE": sub_target, "AGY_CLI_MODE": "1", "TMPDIR": f"/tmp/ag_{sub_target}", "BROWSER": "true"})
        t0 = time.time()
        try:
            res = subprocess.run([AGY_BIN, "--output-format", "json", "-p", "/usage"], env=env, capture_output=True, text=True, timeout=25)
            dur = int((time.time() - t0) * 1000)
            out_all = (res.stdout or "") + " " + (res.stderr or "")

            if check_profile_appeal_status(sub_target, out_all):
                print(f"\n{RED}🚫 LỖI: Tài khoản '{sub_target}' đã bị VÔ HIỆU HÓA do vi phạm Điều khoản dịch vụ!{RESET}")
                print(f"  {AMBER}Thông báo từ Google: This service has been disabled in this account for violation of Terms of Service.{RESET}")
                print(f"  {CYAN}👉 Vui lòng gửi đơn kháng nghị (Submit an appeal) tới Google để tiếp tục sử dụng:{RESET}")
                print(f"     {WHITE}https://docs.google.com/forms/d/e/1FAIpQLScOJWibQ_-hYuVv63kJTgEqlgAaOwRLGFTbXm-QY1gz8U0CGA/viewform{RESET}\n")
                return

            if res.returncode == 0:
                post_q = fetch_quota_for_profile(sub_target)
                if post_q.get("success"):
                    format_profile_for_dashboard(sub_target, post_q)
                print(f"{GREEN}✅ Refreshed profile '{sub_target}' in {dur}ms! Session quota synchronized.{RESET}\n")
            else:
                print(f"{RED}❌ Refresh failed ({dur}ms): {res.stderr.strip()}{RESET}\n")
        except subprocess.TimeoutExpired:
            print(f"{RED}❌ Refresh timed out (25s){RESET}\n")
        except Exception as e:
            print(f"{RED}❌ Error: {str(e)}{RESET}\n")
        return

    if target == "all":
        filter_providers = "--providers" in args
        filter_active = "--active" in args
        filter_login = "--login" in args or "--auth-needed" in args
        filter_blocked = "--blocked" in args or "--disabled" in args

        if filter_providers:
            print(f"\n{BOLD}{CYAN}=== AI AGENT PROVIDERS (CLAUDE, CODEX, KIRO) ==={RESET}")
            try:
                c_data = fetch_claude_quota()
                print_claude_card(c_data)
            except Exception:
                pass
            try:
                o_data = fetch_codex_quota()
                print_codex_card(o_data)
            except Exception:
                pass
            try:
                k_data = fetch_kiro_quota()
                print_kiro_card(k_data)
            except Exception:
                pass
            return

        profiles = get_all_profiles()

        print(f"{CYAN}Scanning quota for {len(profiles)} profiles in parallel...{RESET}")
        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_profile = {}
            for p in profiles:
                future_to_profile[executor.submit(fetch_quota_for_profile, p)] = p
                time.sleep(0.2)
            for future in as_completed(future_to_profile):
                res = future.result()
                results.append(res)
                print(f"  • {res['profile']}: {'DONE' if res.get('success') else 'FAILED'}")

        results.sort(key=lambda x: profiles.index(x["profile"]) if x["profile"] in profiles else 999)

        if filter_active:
            results = [r for r in results if r.get("success")]
        elif filter_login:
            results = [r for r in results if not r.get("success") and not r.get("is_appeal") and r.get("status") != "DISABLED"]
        elif filter_blocked:
            results = [r for r in results if r.get("is_appeal") or r.get("status") == "DISABLED"]

        if "--table" in args:
            print_all_summary(results, show_providers=(not filter_active and not filter_login and not filter_blocked))
        else:
            if not filter_active and not filter_login and not filter_blocked:
                try:
                    c_data = fetch_claude_quota()
                    print_claude_card(c_data)
                except Exception:
                    pass
                try:
                    o_data = fetch_codex_quota()
                    print_codex_card(o_data)
                except Exception:
                    pass
                try:
                    k_data = fetch_kiro_quota()
                    print_kiro_card(k_data)
                except Exception:
                    pass
            for r in results:
                print_dashboard_cards(r)
    elif target in ("claude", "anthropic"):
        result = fetch_claude_quota()
        print_claude_card(result)
    elif target in ("codex", "openai"):
        result = fetch_codex_quota()
        print_codex_card(result)
    elif target == "kiro":
        result = fetch_kiro_quota()
        print_kiro_card(result)
    else:
        if target.startswith("-"):
            print(f"\n{RED}❌ Lỗi: Đối số hoặc cờ không hợp lệ: '{target}'. Gõ 'check-quota --help' để xem hướng dẫn.{RESET}\n")
            return
        if not is_valid_antigravity_profile(target):
            print(f"\n{RED}❌ Lỗi: Profile '{target}' không tồn tại hoặc không phải là profile Antigravity hợp lệ.{RESET}\n")
            return
        # Single profile dashboard
        result = fetch_quota_for_profile(target)
        print_dashboard_cards(result)


if __name__ == "__main__":
    main()
