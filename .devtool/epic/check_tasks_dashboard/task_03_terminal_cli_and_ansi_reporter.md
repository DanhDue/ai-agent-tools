---
id: "task_03_terminal_cli_and_ansi_reporter"
status: "done"
priority: "high"
assignee: null
epic: "check_tasks_dashboard"
dueDate: null
created: "2026-11-11T08:30:00Z"
modified: "2026-11-11T06:53:08Z"
completedAt: "2026-11-11T06:53:08Z"
labels: ["cli", "ansi", "reporter"]
order: "a3"
---

# Task 3: Terminal CLI Formatter and Rich ANSI Reporter

Epic: [check_tasks_dashboard](check_tasks_dashboard.en.md)

## Requirement Analysis

Implement the command-line interface and terminal formatting engine in `skills/check-tasks/resources/scripts/check_tasks.py`:
1. Argument parser supporting:
   - `check-tasks` (no args): inspects current directory or worktree, rendering a compact single-repo summary card.
   - `check-tasks all`: scans all repositories in `/Users/danhdueexoictif/AllProjects`, rendering an executive ANSI table.
   - `check-tasks <repo>`: renders deep inspection card for the specified repository (active worktrees, Kanban tasks breakdown, Two-Tier Memory, Gate history).
   - `--ui`: starts background HTTP server daemon and opens dashboard in browser.
   - `--stop`: terminates running tasks server daemon PID.
   - `--status`: displays HTTP server daemon status and port.
   - `--json`: outputs raw JSON representation of `DashboardGraph` for scripting.
   - `--no-color`: strips ANSI formatting regardless of TTY status.
2. Rich ANSI formatting engine:
   - Dynamic terminal width calculation via `shutil.get_terminal_size()`.
   - Color styling mapping each repository to its canonical signature:
     - `ai-agent-tools`: Warm Amber (`\033[38;2;180;83;9m`).
     - `lyrics-sync`: Crimson Red (`\033[38;2;127;29;29m`).
     - `nexus`: Royal Blue (`\033[38;2;13;71;161m`).
     - `D3Nexus`: Emerald Green (`\033[38;2;6;95;70m`).
   - TTY detection via `sys.stdout.isatty()` with automated escape code stripping on pipe/redirection.
   - Visual progress bars (e.g. `[████████░░] 80% (4/5 done)`).
3. Create standalone wrapper script `scripts/check_tasks.py` and executable PATH shim `bin/check-tasks` delegating to the skill resource.
4. Unit test suite `tests/test_check_tasks_cli.py` verifying command parsing, ANSI table generation, and plain-text stripping.

## Files

Allowed files:
- `skills/check-tasks/resources/scripts/check_tasks.py` (new)
- `scripts/check_tasks.py` (new)
- `bin/check-tasks` (new)
- `tests/test_check_tasks_cli.py` (new)

Read-only context:
- `scripts/agy_quota.py` — terminal table formatting and ANSI color patterns
- `.devtool/epic/check_tasks_dashboard/check_tasks_dashboard.en.md` — CLI Specification

## Design Rationale

Providing an executive terminal summary ensures developers can instantly check workspace status from any shell without opening a browser window. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `skills/check-tasks/resources/scripts/check_tasks.py` (`render_terminal_table`, `render_single_repo`, `main`), `scripts/check_tasks.py`.
- **Downstream callers**: Terminal users, git hook scripts, and CLI aliases.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: 100% of formatting, width adjustment, and plain-text fallback branches.

### BDD SCENARIOS

Covers: CTD-HP-03, CTD-EC-04

```gherkin
Scenario: [CTD-HP-03] [Tier C - Integration] Terminal CLI renders rich ANSI colored multi-repo overview

Given multiple discovered repositories with varying Kanban progress
When a developer executes check_tasks.py with argument "all"
Then the CLI prints a formatted ANSI table with repository color badges
And the output displays repository name, active branch or worktree, active epic, and task progress percentages
And the next immediate step for each active epic is clearly visible in the table

Scenario: [CTD-EC-04] [Tier A - Unit] Terminal CLI falls back to plain text when stdout is redirected

Given stdout is redirected to a non-TTY pipe or file
When check_tasks.py formats the output table
Then all ANSI escape codes are stripped from the output
And the output remains cleanly aligned plain text
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest tests/test_check_tasks_cli.py -k test_ctd_hp_03` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest tests/test_check_tasks_cli.py -k test_ctd_hp_03` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest tests/test_check_tasks_cli.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/check-tasks/resources/scripts/check_tasks.py scripts/check_tasks.py tests/test_check_tasks_cli.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/check-tasks/resources/scripts/check_tasks.py scripts/check_tasks.py tests/test_check_tasks_cli.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_3.xml tests/test_check_tasks_cli.py` | exit 0; results build/test-results/task_3.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.
- Terminal control codes fail to render on macOS Terminal or iTerm2.

## Decisions Already Made

- Terminal widths adapt dynamically via `shutil.get_terminal_size()` with fallback to 100 columns.
- Redirected stdout automatically strips ANSI escape sequences via regular expression.
- Repository colors strictly respect the repository signatures in `CRITICAL_RULES.md` Rule 8.
- Flags `--ui`, `--stop`, and `--status` delegate daemon management to `skills/check-tasks/resources/scripts/tasks_server.py` (`start_server`, `stop_server`, `server_status`) loaded via `importlib.util.spec_from_file_location` rather than re-implementing PID handling.
- CLI wrapper at `scripts/check_tasks.py` loads `skills/check-tasks/resources/scripts/check_tasks.py` via `importlib.util.spec_from_file_location` or a clean launcher shim to avoid module name stem collision.

## Definition of Done

- Scenarios CTD-HP-03 and CTD-EC-04 are covered and pass in the test suite. (V2, V3, V6)
- Python quality checks (lint and type check) pass cleanly. (V4, V5)
- Terminal output renders readable tables with colors and proper alignment. (Gate 5)

## Dependencies & Blockers

Requires [Task 1](task_01_harvester_engine_and_data_models.md), [Task 2](task_02_deterministic_lifecycle_fsm_engine.md), and [Task 4](task_04_http_daemon_server_and_rest_api.md). Blocks [Task 5](task_05_interactive_web_dashboard_and_skill.md).

## References & Rollback

- [Epic HLD](check_tasks_dashboard.en.md), Terminal CLI Specification.
- **Rollback**: Revert task commit; deletes `scripts/check_tasks.py` and `tests/test_check_tasks_cli.py`.
