---
id: "task_01_harvester_engine_and_data_models"
status: "todo"
priority: "high"
assignee: null
epic: "check_tasks_dashboard"
dueDate: null
created: "2026-11-11T08:30:00Z"
modified: "2026-11-11T08:30:00Z"
completedAt: null
labels: ["harvester", "scanner", "data-models"]
order: "a1"
---

# Task 1: Multi-Repo Harvester Engine and Data Models

Epic: [check_tasks_dashboard](check_tasks_dashboard.en.md)

## Requirement Analysis

Implement the foundational scanning and data model infrastructure for `check-tasks`:
1. Core dataclasses in `skills/check-tasks/resources/scripts/check_tasks.py`:
   - `WorktreeMetadata`: path, branch, head_sha, is_dirty, dirty_file_count, is_detached.
   - `TaskProgress`: total_tasks, done_tasks, in_progress_tasks, todo_tasks, percentage, active_task_name.
   - `TwoTierMemory`: project_ledger_path, total_milestones, last_milestone, assistant_state_role, assistant_state_status.
   - `RepoMetadata`: name, path, theme_color, window_title, active_epic, active_stage, worktrees, task_progress, memory, contract_status.
   - `DashboardGraph`: workspace_root, scanned_at, repos.
2. Harvester engine functions:
   - `scan_worktrees(repo_path: Path) -> list[WorktreeMetadata]`: executes `git worktree list --porcelain` and parses paths, heads, and branch names.
   - `extract_vscode_styling(repo_path: Path) -> tuple[str, str]`: parses `.vscode/settings.json` for `workbench.colorCustomizations` and `window.title`, falling back to canonical repository signatures (`#b45309`, `#7f1d1d`, `#0d47a1`, `#065f46`) or deterministic hash palettes.
   - `extract_task_progress(repo_path: Path, active_epic: str | None) -> TaskProgress`: inspects `.devtool/features/task_*.md` and `.devtool/epic/<epic>/` for task states.
   - `extract_two_tier_memory(repo_path: Path) -> TwoTierMemory`: parses `.devtool/PROJECT_LEDGER.md` for milestones and `.devtool/assistant_state.md` for snapshot roles.
   - `harvest_dashboard_graph(root_path: Path, max_workers: int = 4) -> DashboardGraph`: scans all child directories in `/Users/danhdueexoictif/AllProjects` in parallel via `concurrent.futures.ThreadPoolExecutor`.
3. Unit test suite `tests/test_check_tasks_harvester.py` verifying data modeling, worktree parsing, missing file fallbacks, and multi-repo harvesting.

## Files

Allowed files:
- `skills/check-tasks/resources/scripts/check_tasks.py` (new)
- `tests/test_check_tasks_harvester.py` (new)

Read-only context:
- `scripts/resume_context.py` — state persistence patterns, gate hydration, and Gate Ledger formatting
- `scripts/agy_quota.py` — terminal formatting patterns and scanning heuristics
- `.devtool/epic/check_tasks_dashboard/check_tasks_dashboard.en.md` — HLD and Architecture Contracts

## Design Rationale

Using dataclasses with standard serialization ensures compatibility with both the CLI formatter and the HTTP JSON daemon. Parallel scanning via `ThreadPoolExecutor` ensures sub-100ms discovery across all repositories. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `skills/check-tasks/resources/scripts/check_tasks.py` (`WorktreeMetadata`, `TaskProgress`, `RepoMetadata`, `DashboardGraph`, `scan_worktrees`, `extract_vscode_styling`, `harvest_dashboard_graph`).
- **Downstream callers**: Tasks 2 through 5 consume these data models.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: 100% of parser branches and fallback handlers.

### BDD SCENARIOS

Covers: CTD-HP-01, CTD-EC-01, CTD-EC-02, CTD-EC-03

```gherkin
Scenario: [CTD-HP-01] [Tier C - Integration] Multi-repo harvesting discovers all projects, worktrees, and styling metadata

Given a root directory containing multiple repositories "ai-agent-tools", "lyrics-sync", "nexus", and "D3Nexus"
And each repository contains .vscode/settings.json with window.title and workbench.colorCustomizations
When the harvester scans the workspace root via harvest_dashboard_graph
Then the returned graph contains metadata objects for all 4 repositories
And each repository correctly reflects its theme colors, active worktrees, and git branches
And task progress counts for done, in_progress, and todo match the filesystem state

Scenario: [CTD-EC-01] [Tier A - Unit] Graceful fallback when .vscode/settings.json is absent

Given a repository directory that lacks a .vscode/settings.json file
When scan_repo collects metadata for this repository
Then the repository theme color falls back to the deterministic palette signature
And window title defaults to the repository folder basename
And scanning completes without raising FileNotFoundError

Scenario: [CTD-EC-02] [Tier A - Unit] Graceful handling of repositories without active epics

Given a repository with a clean working tree and no .devtool/epic/ directory
When the harvester collects metadata for this repository
Then the active epic name is reported as "None"
And the Kanban task count is 0 of 0 with 100% idle status
And the lifecycle stage is reported as "Idle"

Scenario: [CTD-EC-03] [Tier A - Unit] Parsing dirty worktrees and detached HEAD commits

Given a git worktree operating on a detached HEAD commit with unstaged file modifications
When scan_repo executes git worktree parsing
Then the worktree metadata records the abbreviated commit SHA
And the dirty flag is correctly set to true with the count of modified files
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest tests/test_check_tasks_harvester.py -k test_ctd_hp_01` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest tests/test_check_tasks_harvester.py -k test_ctd_hp_01` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest tests/test_check_tasks_harvester.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/check-tasks/resources/scripts/check_tasks.py tests/test_check_tasks_harvester.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/check-tasks/resources/scripts/check_tasks.py tests/test_check_tasks_harvester.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_1.xml tests/test_check_tasks_harvester.py` | exit 0; results build/test-results/task_1.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.
- Parallel directory scanning crashes on non-standard macOS permission flags.

## Decisions Already Made

- Core models are defined with Python standard `@dataclass` without Pydantic dependencies to preserve lightweight standalone execution.
- Worktree discovery uses `git worktree list --porcelain` rather than custom parsing to maintain 100% fidelity with git porcelain contracts.
- Missing `.vscode/settings.json` gracefully falls back to deterministic palette signatures (`#b45309`, `#7f1d1d`, `#0d47a1`, `#065f46`).
- Task progress counts are extracted from `.devtool/features/` and verified against `.devtool/epic/<epic>/`.
- Parallel scanning uses standard `ThreadPoolExecutor` with a default of 4 workers.

## Definition of Done

- Scenarios CTD-HP-01, CTD-EC-01, CTD-EC-02, and CTD-EC-03 are covered and pass in the test suite. (V2, V3, V6)
- Python quality checks (lint and type check) pass cleanly. (V4, V5)
- All repositories and worktrees in `/Users/danhdueexoictif/AllProjects` are discovered and structured properly. (Gate 5)

## Dependencies & Blockers

None. Blocks [Task 2](task_02_deterministic_lifecycle_fsm_engine.md), [Task 3](task_03_terminal_cli_and_ansi_reporter.md), [Task 4](task_04_http_daemon_server_and_rest_api.md), and [Task 5](task_05_interactive_web_dashboard_and_skill.md).

## References & Rollback

- [Epic HLD](check_tasks_dashboard.en.md), Module Contracts.
- **Rollback**: Revert task commit; deletes `skills/check-tasks/resources/scripts/check_tasks.py` and `tests/test_check_tasks_harvester.py`.
