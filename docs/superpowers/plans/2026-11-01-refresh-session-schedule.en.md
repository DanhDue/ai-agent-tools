# Refresh Session Schedule & Daemon Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use d3nexus:subagent-driven-development (recommended) or d3nexus:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `refresh_session.py` and `skills/refresh-session/SKILL.md` to support automated daily scheduling via macOS `launchd` (with Linux `crontab` fallback), enabling developers to stagger 5-hour rolling session windows (e.g., at 05:00 AM or 06:00 AM) while maintaining 100% backward compatibility for manual instant pings.

**Architecture:** A new `schedule` subcommand in `skills/refresh-session/resources/scripts/refresh_session.py` parses flexible time representations (`05:00`, `5h`, `6am`), generates and registers native system daemons (`~/Library/LaunchAgents/com.d3nexus.refresh-session.plist` via `launchctl` on macOS, user crontab on Linux), queries active daemon status, and uninstalls schedules cleanly. All manual execution pathways remain untouched.

**Tech Stack:** Python 3.10+ (Standard Library: `argparse`, `pathlib`, `re`, `subprocess`, `sys`, `unittest`), macOS `launchd`, Linux `cron`, bash, markdown.

**Spec:** [2026-11-01-refresh-session-schedule-design.en.md](../specs/2026-11-01-refresh-session-schedule-design.en.md)  
**Quick-Guide:** [docs/refresh-session-quick-guide.en.md](../../refresh-session-quick-guide.en.md)

## Table of Contents

- [Global Constraints](#global-constraints)
- [File Structure](#file-structure)
- [Tasks](#tasks)
  - [Task 1: Flexible Time Parser, Service Generation, and Comprehensive Unit Tests](#task-1-flexible-time-parser-service-generation-and-comprehensive-unit-tests)
  - [Task 2: Skill Definition Update and Live Verification](#task-2-skill-definition-update-and-live-verification)
- [Final Verification](#final-verification)

---

## Global Constraints

- **100% Backward Compatibility**: All existing invocations (`refresh_session.py [all|claude|codex]`, `--json`, `--timeout`) MUST continue to work without modification.
- **Python Standard Library Only**: No external pip dependencies.
- **Native OS Init Systems**: Use `~/Library/LaunchAgents/com.d3nexus.refresh-session.plist` with `launchctl` on macOS (`darwin`); use user `crontab` on Linux (`linux`).
- **Zero Sudo Requirement**: Must run entirely in user space without requiring elevated permissions.
- **Canonical Path Resolution**: Daemon definitions must resolve canonical absolute paths (`pathlib.Path(__file__).resolve()`) so execution succeeds regardless of working directory.
- **SKILL.md Frontmatter Standard**:
  - Exactly two keys: `name` and `description` (no extra keys).
  - `name`: `refresh-session`.
- **Commit Formatting**:
  - Commit message format: `[REFRESH_SESSION] <title>` with a bullet list of changes.
  - Never append trailer lines or tool attributions (`Co-Authored-By:`, `Generated with`).
- **Verification Gate**:
  - All tests must pass via `scripts/verify.sh`.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `skills/refresh-session/resources/scripts/refresh_session.py` | Modify | Implement `parse_flexible_time`, `build_darwin_plist`, schedule install/status/uninstall handlers, and `schedule` CLI parser. |
| `skills/refresh-session/resources/scripts/test_refresh_session.py` | Modify | Add comprehensive unit tests for time parsing, plist generation, schedule installation, status inspection, and uninstallation. |
| `skills/refresh-session/SKILL.md` | Modify | Document the `schedule` subcommand, parameters, and natural language prompts. |

---

## Tasks

### Task 1: Flexible Time Parser, Service Generation, and Comprehensive Unit Tests

**Files:**
- Modify: `skills/refresh-session/resources/scripts/test_refresh_session.py`
- Modify: `skills/refresh-session/resources/scripts/refresh_session.py`

- [ ] **Step 1: Write failing unit tests for scheduling functionality (RED)**
  Add test cases in `skills/refresh-session/resources/scripts/test_refresh_session.py`:
  - `test_parse_flexible_time_24h`: Verifies `"05:00" -> (5, 0)`, `"14:30" -> (14, 30)`, `"9:15" -> (9, 15)`.
  - `test_parse_flexible_time_short`: Verifies `"5h" -> (5, 0)`, `"6h" -> (6, 0)`, `"14h" -> (14, 0)`, `"5" -> (5, 0)`.
  - `test_parse_flexible_time_ampm`: Verifies `"5am" -> (5, 0)`, `"5:30am" -> (5, 30)`, `"6pm" -> (18, 0)`, `"12pm" -> (12, 0)`, `"12am" -> (0, 0)`.
  - `test_parse_flexible_time_invalid`: Asserts `ValueError` for `"25:00"`, `"-1h"`, `"abc"`, `""`, `"5:65"`.
  - `test_build_darwin_plist`: Verifies generated XML contains label `com.d3nexus.refresh-session`, correct hour, minute, python executable, script path, and log file paths.
  - `test_schedule_install_darwin`: Mocks `subprocess.run` and filesystem to test plist writing and `launchctl load`.
  - `test_schedule_status_darwin_active`: Tests status reporting when plist exists and `launchctl list` finds the label.
  - `test_schedule_status_darwin_inactive`: Tests status reporting when no schedule is installed.
  - `test_schedule_uninstall_darwin`: Tests `launchctl unload` call and plist file removal.
  - `test_parse_arguments_schedule_subcommand`: Tests CLI parsing of `schedule --time 05:00`, `schedule --status`, and `schedule --uninstall`.

- [ ] **Step 2: Run tests to confirm failures (RED)**
  Run: `python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py`
  Confirm that the new test methods fail.

- [ ] **Step 3: Implement time parsing, daemon generators, and CLI handlers (GREEN)**
  In `skills/refresh-session/resources/scripts/refresh_session.py`:
  - Implement `parse_flexible_time(time_str: str) -> tuple[int, int]`:
    - Support regex patterns for `HH:MM`, `Hh`, `H`, `H[:MM]am|pm`.
    - Validate `0 <= hour <= 23` and `0 <= minute <= 59`.
  - Implement `build_darwin_plist(script_path: str, hour: int, minute: int, target: str) -> str`:
    - Expand `~` to absolute canonical path via `Path.home()` (launchd does not expand tildes).
    - Ensure parent directories `~/.devtool/logs` and `~/Library/LaunchAgents` are created.
    - Inject `<key>EnvironmentVariables</key><dict><key>PATH</key><string>...</string></dict>` using `os.environ.get("PATH")` or standard PATH entries (`/opt/homebrew/bin:/usr/local/bin:~/.local/bin:/usr/bin:/bin`) so `claude` and `codex` are discoverable by `shutil.which()`.
    - Generate standard launchd XML with `StartCalendarInterval`, logging to `{HOME}/.devtool/logs/refresh_session_daemon.{log,err}`.
  - Implement `install_schedule(hour: int, minute: int, target: str) -> dict[str, Any]`:
    - If `darwin`: Write plist to `~/Library/LaunchAgents/com.d3nexus.refresh-session.plist`, execute `launchctl unload` if existing, then `launchctl load`.
    - If `linux`: Manage crontab entries with delimiter markers.
  - Implement `get_schedule_status() -> dict[str, Any]`:
    - Check plist / crontab presence and `launchctl list` state.
  - Implement `uninstall_schedule() -> dict[str, Any]`:
    - Unload and remove plist / delete crontab block.
  - Update `parse_args()`:
    - Use `argparse` subparsers or optional positional command to maintain backward compatibility for `refresh_session.py [target]` while supporting `refresh_session.py schedule [...]`.
    - Support `--remove` as alias for `--uninstall`, and `--target [all|claude|codex]` flag under `schedule`.
  - Update `main()`:
    - Dispatch `schedule` actions or fall through to `run_refresh()` for on-demand targets.

- [ ] **Step 4: Run unit tests to verify green (GREEN)**
  Run: `python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py`
  Verify that all tests pass.

- [ ] **Step 5: Code quality, type checking, and linting**
  - Run `ruff check skills/refresh-session/resources/scripts/` (or `~/.local/bin/ruff check`)
  - Ensure zero warnings or style issues.

- [ ] **Step 6: Commit Task 1 changes**
  ```bash
  git add skills/refresh-session/resources/scripts/
  git commit -m "[REFRESH_SESSION] Implement flexible scheduling engine and unit tests" -m "- Add flexible time parser supporting 24h, short hour, and am/pm formats
  - Add native macOS launchd plist generation, installation, status, and uninstall handlers
  - Add unit tests covering time parsing, plist building, and lifecycle management"
  ```

---

### Task 2: Skill Definition Update and Live Verification

**Files:**
- Modify: `skills/refresh-session/SKILL.md`

- [ ] **Step 1: Update skill documentation**
  Update `skills/refresh-session/SKILL.md` to:
  - Document the updated command table with both manual and scheduled invocations.
  - Explain the 05:00 AM staggered rolling window strategy.
  - Provide natural language interaction examples.
  - Reference `docs/refresh-session-quick-guide.en.md` and `.vi.md`.
  - Verify frontmatter retains strictly `name` and `description` keys.

- [ ] **Step 2: Live host smoke test**
  - Test schedule install: `python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --time 05:00`
  - Verify status output: `python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --status`
  - Verify plist existence: `test -f ~/Library/LaunchAgents/com.d3nexus.refresh-session.plist`
  - Test schedule uninstall: `python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --uninstall`
  - Verify plist removed: `! test -f ~/Library/LaunchAgents/com.d3nexus.refresh-session.plist`
  - Verify on-demand manual execution still works: `python3 skills/refresh-session/resources/scripts/refresh_session.py --json`

- [ ] **Step 3: Run repository verification harness**
  Run: `bash scripts/verify.sh`
  Confirm all 16 sections pass cleanly.

- [ ] **Step 4: Commit Task 2 changes**
  ```bash
  git add skills/refresh-session/SKILL.md
  git commit -m "[REFRESH_SESSION] Update skill documentation with scheduling reference" -m "- Document schedule subcommand in SKILL.md
  - Add natural language prompts and quick-guide references
  - Pass all 16 sections in verify.sh"
  ```

---

## Final Verification

1. `python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py` $\rightarrow$ All tests pass.
2. `bash scripts/verify.sh` $\rightarrow$ `PASS — safe to publish`.
3. Manual ping `python3 skills/refresh-session/resources/scripts/refresh_session.py claude` $\rightarrow$ Works as expected.
4. Schedule install / status / uninstall workflow $\rightarrow$ Works seamlessly on macOS.
