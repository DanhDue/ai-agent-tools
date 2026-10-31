# Release Notes: d3nexus v1.20.0

**Release Date:** November 01, 2026  
**Version:** `1.20.0`  
**Git Tag:** `v1.20.0`, `d3nexus--v1.20.0`

---

## Executive Summary

`v1.20.0` enhances the **Session Refresh Engine** (`refresh-session`) with **Automated Daily Scheduling (Shift-Left Quota Staggering)**. Developers can now schedule automatic early-morning session pre-warming (e.g. at 5:00 AM or 6:00 AM) using OS native daemons (`launchd` on macOS, `crontab` on Linux) with zero third-party dependencies. This ensures that the initial 5-hour rolling rate-limit window resets just as deep work begins (e.g. 8:00 AM – 10:00 AM), granting an unbroken 7-hour full-quota development block. This release also introduces comprehensive bilingual quick-guides and expands the automated unit test suite to 27 tests.

---

## Key Highlights

### 1. Daily Daemon Scheduling Engine (`skills/refresh-session/`)
- **Native OS Automation**:
  - **macOS `launchd`**: Generates and manages `~/Library/LaunchAgents/com.d3nexus.refresh-session.plist` with full runtime `PATH` injection (`/opt/homebrew/bin`, `~/.local/bin`, etc.) and dedicated log routing (`~/.devtool/logs/refresh_session_daemon.{log,err}`).
  - **Linux `crontab`**: Seamlessly manages user cron jobs using idempotent demarcated blocks (`# BEGIN d3nexus-refresh-session`).
- **Flexible Natural Time Parsing**: Accepts standard 24-hour time (`05:00`, `14:30`), short hours (`5h`, `6h`, `5`), and 12-hour AM/PM (`5am`, `5:30am`, `6pm`, `12pm`).
- **Complete CLI & Natural Language Controls**:
  - Install: `schedule --time <time> [--target <target>]`
  - Status: `schedule --status [--json]`
  - Uninstall: `schedule --uninstall` (or `--remove`)
- **100% Backward Compatibility**: Instant on-demand pings (`/refresh-session [claude|codex|all]`) remain fully functional and unchanged.

### 2. Comprehensive Bilingual Quick Guides
- **Vietnamese Guide**: [`docs/refresh-session-quick-guide.vi.md`](docs/refresh-session-quick-guide.vi.md)
- **English Guide**: [`docs/refresh-session-quick-guide.en.md`](docs/refresh-session-quick-guide.en.md)
- Includes full command lookup cheat-sheets, Shift-Left Quota Staggering timelines, macOS daemon verification tips, and structured JSON telemetry examples.

### 3. Expanded Unit Testing & Release Verification
- **27 Unit Tests**: Comprehensive coverage in [`test_refresh_session.py`](skills/refresh-session/resources/scripts/test_refresh_session.py) verifying time parsing, plist generation, daemon lifecycle, argument parsing, sandboxed directory isolation, and error handling.
- **Section 16 Invariant**: Full suite verified in [`scripts/verify.sh`](scripts/verify.sh) Section 16.

---

## Verifications & Quality Gates Passed

- `skills/refresh-session/resources/scripts/test_refresh_session.py`: 🟢 **PASS** (27/27 tests green)
- `ruff check`: 🟢 **PASS** (0 errors, 100% compliant)
- `scripts/verify.sh`: 🟢 **PASS — safe to publish** (16/16 sections green)
