---
id: "task_04_http_daemon_server_and_rest_api"
status: "todo"
priority: "high"
assignee: null
epic: "check_tasks_dashboard"
dueDate: null
created: "2026-11-11T08:30:00Z"
modified: "2026-11-11T08:30:00Z"
completedAt: null
labels: ["daemon", "server", "rest-api"]
order: "a4"
---

# Task 4: HTTP Daemon Server, Port Collision Protection, and REST API

Epic: [check_tasks_dashboard](check_tasks_dashboard.en.md)

## Requirement Analysis

Implement the background HTTP server daemon and REST API engine in `skills/check-tasks/resources/scripts/tasks_server.py`:
1. Core server daemon infrastructure:
   - Uses Python standard library `http.server.HTTPServer` with `ThreadingMixIn`.
   - PID guard management at `/tmp/agy_tasks_server.pid`.
   - Stale PID verification via `os.kill(pid, 0)` with safe replacement of dead PIDs.
   - Port binding on `localhost:8766` with automated safe port increment to `8767` if occupied by a foreign process.
   - Command flags: `--daemon` (forks background daemon), `--stop` (sends SIGTERM to running PID), `--status` (checks running status), `--port <int>` (overrides default port).
2. REST API Endpoints:
   - `GET /api/tasks`: invokes `harvest_dashboard_graph` and returns serialized JSON graph.
   - `GET /api/review?repo=<name>&round=<N>`: parses `review_results.md` or `principal_review.md` in the target repository and returns the persisted 5-column triage findings (`#`, `Severity`, `Location`, `Problem`, `Decision`), parsing raw evidence from the `Raw output:` fence, along with candidate SHA, model, thinking level, and verdict.
   - `POST /api/launch/cli`: accepts `{"repo": str, "worktree": str, "profile": str}` and spawns terminal subshell using `ag_run <profile>` without mutating host OS keychain or `$HOME` (Rule 9).
   - `POST /api/launch/ide`: accepts `{"repo": str, "worktree": str, "profile": str}` and spawns Antigravity IDE targeting the worktree directory via `ag_run <profile> ide <path>` with IPC handles stripped (`-u ELECTRON_RUN_AS_NODE -u VSCODE_GIT_IPC_HANDLE`).
   - `POST /api/shutdown`: triggers graceful server shutdown and unlinks PID file.
   - `GET /`: serves `skills/check-tasks/resources/dashboard/tasks_dashboard.html`.
3. Create standalone runner `scripts/tasks_server.py`.
4. Unit and integration test suite `tests/test_check_tasks_server.py` verifying API endpoints, PID guard lifecycle, port collision bump, and launcher safety.

## Files

Allowed files:
- `skills/check-tasks/resources/scripts/tasks_server.py` (new)
- `scripts/tasks_server.py` (new)
- `tests/test_check_tasks_server.py` (new)

Read-only context:
- `scripts/agy_quota.py` — daemon architecture, PID file handling, and port collision patterns
- `.devtool/epic/check_tasks_dashboard/check_tasks_dashboard.en.md` — Server & API Specification

## Design Rationale

Built with standard library HTTP server to eliminate heavy external web framework dependencies, ensuring immediate startup (< 50ms) and zero memory bloat (< 15MB RSS). Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `skills/check-tasks/resources/scripts/tasks_server.py` (`TasksServer`, `TasksHandler`, `start_server`, `stop_server`), `scripts/tasks_server.py`.
- **Downstream callers**: Dashboard browser frontend and CLI `--ui` / `--stop` commands.
- **Cross-platform bridges**: Local process execution (`ag_run`).
- **Target test coverage threshold**: 100% of API routes and error handler paths.

### BDD SCENARIOS

Covers: CTD-HP-04, CTD-AR-01, CTD-FR-01, CTD-FR-02

```gherkin
Scenario: [CTD-HP-04] [Tier C - Integration] Web server daemon starts cleanly and serves REST API

Given an unoccupied port 8766
When tasks_server.py starts with argument "--daemon"
Then the process writes its PID to /tmp/agy_tasks_server.pid
And a GET request to http://localhost:8766/api/tasks returns HTTP 200 with valid JSON graph data
And a POST request to http://localhost:8766/api/shutdown terminates the server and removes the PID file

Scenario: [CTD-AR-01] [Tier C - Integration] Daemon server increments port safely on port collision

Given port 8766 is already bound by an unrelated third-party process
When tasks_server.py attempts to start the dashboard service
Then the server detects that port 8766 is occupied by an alien PID
And the server safely increments the listening port to 8767
And the server updates the PID file and prints the active listening URL on port 8767

Scenario: [CTD-FR-01] [Tier A - Unit] Rule 9 launcher enforcement prevents environment contamination

Given a request to launch the CLI or IDE targeting an Antigravity profile "hau"
When tasks_server.py constructs the launch command
Then the command prefixes execution with localized subshell invocation "ag_run hau"
And the command strips VSCODE_GIT_IPC_HANDLE and ELECTRON_RUN_AS_NODE environment variables
And the command never executes security default-keychain or modifies global ~/.zshrc

Scenario: [CTD-FR-02] [Tier A - Unit] Server recovers gracefully from stale or orphan PID files

Given a stale PID file /tmp/agy_tasks_server.pid referencing a dead process
When tasks_server.py checks daemon status or initiates startup
Then verify_pid detects that the process is no longer alive via signal 0
And the stale PID file is safely unlinked and replaced with the new process PID
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest tests/test_check_tasks_server.py -k test_ctd_hp_04` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest tests/test_check_tasks_server.py -k test_ctd_hp_04` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest tests/test_check_tasks_server.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/check-tasks/resources/scripts/tasks_server.py scripts/tasks_server.py tests/test_check_tasks_server.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/check-tasks/resources/scripts/tasks_server.py scripts/tasks_server.py tests/test_check_tasks_server.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_4.xml tests/test_check_tasks_server.py` | exit 0; results build/test-results/task_4.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.
- Background process spawning mutates the parent process environment or global Keychain.

## Decisions Already Made

- The server uses standard library `http.server.HTTPServer` with `ThreadingMixIn` to handle concurrent API requests.
- PID files are locked with exclusive file creation (`os.O_CREAT | os.O_EXCL`) to eliminate race conditions during startup.
- If port 8766 is occupied by an unrelated process, the daemon increments to 8767 without crashing.
- `/api/review` response models the canonical persisted 5-column review table (`#`, `Severity`, `Location`, `Problem`, `Decision`) with evidence parsed from the round's raw markdown output block.
- Launcher dispatch strictly complies with `CRITICAL_RULES.md` Rule 9, using localized subshells and stripping IPC variables.

## Definition of Done

- Scenarios CTD-HP-04, CTD-AR-01, CTD-FR-01, and CTD-FR-02 are covered and pass in the test suite. (V2, V3, V6)
- Python quality checks (lint and type check) pass cleanly. (V4, V5)
- Server responds to REST API requests and terminates cleanly on shutdown. (Gate 5)

## Dependencies & Blockers

Requires [Task 1](task_01_harvester_engine_and_data_models.md) and [Task 2](task_02_deterministic_lifecycle_fsm_engine.md). Blocks [Task 5](task_05_interactive_web_dashboard_and_skill.md).

## References & Rollback

- [Epic HLD](check_tasks_dashboard.en.md), HTTP Server & API Specification.
- **Rollback**: Revert task commit; deletes `skills/check-tasks/resources/scripts/tasks_server.py`, `scripts/tasks_server.py`, and `tests/test_check_tasks_server.py`.
