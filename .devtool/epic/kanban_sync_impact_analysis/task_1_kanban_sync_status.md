---
id: "task_1_kanban_sync_status"
status: "done"
priority: "high"
assignee: null
epic: "kanban-sync-impact-analysis"
dueDate: null
created: "2026-09-15T02:30:00Z"
modified: "2026-09-14T19:45:49Z"
completedAt: "2026-09-14T19:45:49Z"
labels: ["tooling", "kanban", "worktree"]
order: "a1"
---

# Task 1: Complete and Wire Dual-Workspace Status Synchronizer

Epic: [kanban-sync-impact-analysis](kanban_sync_impact_analysis.en.md)

## Requirement Analysis
In an agentic mobile workflow operating within isolated git worktrees, task status tracking faces a fundamental challenge: when an agent updates task markdown files inside `.worktrees/<epic_dir>/.devtool/features/`, the main workspace checkout (`$MAIN_ROOT/.devtool/features/`) remains stale. Developers and external tools inspecting the primary repository cannot observe live progress until the branch is merged.

This task requires completing and hardening `sync_task_status.py` and its comprehensive test suite `test_sync_task_status.py` to:
1. Dynamically discover all active git checkouts (main checkout and all linked worktrees) via `git worktree list --porcelain`.
2. Simultaneously synchronize task status across both primary and worktree locations:
   - Primary features: `<worktree>/.devtool/features/<task_id>.md`
   - Mirrored epic directory: `<worktree>/.devtool/epic/<epic_dir>/<task_id>.md`
   - Main checkout counterparts: `$MAIN_ROOT/.devtool/features/<task_id>.md` and `$MAIN_ROOT/.devtool/epic/<epic_dir>/<task_id>.md`.
3. Manage frontmatter timestamp invariants:
   - Always update `modified:` to the current UTC ISO-8601 timestamp ending in `Z`.
   - Set `completedAt:` to the current UTC timestamp when status transitions to `done`.
   - Reset `completedAt: null` if a task transitions out of `done`.
4. Enforce strict 5-column enum validation (`backlog`, `todo`, `in-progress`, `review`, `done`), rejecting arbitrary strings with exit code 2.
5. Provide epic collision guards, preventing tasks with matching filenames from being mutated if their frontmatter `epic:` does not match the target epic.
6. Support updating Epic Overview files (`kanban_sync_impact_analysis.en.md` and `.vi.md`) keeping both language variants in lockstep.

## Relevant Files & Context Pointers
- `skills/epic-implementation/resources/scripts/sync_task_status.py`: Primary status synchronizer script.
- `skills/epic-implementation/resources/scripts/test_sync_task_status.py`: Comprehensive test suite verifying all synchronization behaviors.
- `.devtool/features/`: Workspace feature tasks directory.
- `.devtool/epic/kanban_sync_impact_analysis/`: Epic design and mirror directory.
- `.devtool/epic/kanban_sync_impact_analysis/bdd_scenarios.md`: BDD contract reference (Scenarios 1.1, 1.2, 1.3, 2.1, 2.2, 2.3).

## Design Rationale
- **Zero Third-Party Dependencies**: The synchronizer uses standard Python 3 libraries (`re`, `subprocess`, `sys`, `pathlib`, `datetime`, `argparse`), ensuring zero installation overhead in any environment (CI/CD, local machine, subagents).
- **Format Preservation**: The script uses non-destructive regex substitution on YAML frontmatter rather than full YAML dumping, guaranteeing that markdown headings, tables, bullet points, comments, and spacing are preserved byte-for-byte.
- **Atomic Operations**: File writes are executed atomically or sequentially with write validation to eliminate partially written files if interrupted.

### BDD SCENARIOS

#### Scenario 1.1: Live Dual-Workspace Status Synchronization across All Checkouts
- **Tag**: `[Tier A - Unit]`
- **Given** an epic task `task_1_setup` exists in both `.devtool/features/` and `.devtool/epic/kanban_sync_impact_analysis/` across a main checkout and an isolated git worktree `.worktrees/kanban_sync_impact_analysis`
- **When** the developer or agent executes `sync_task_status.py task task_1_setup in-progress`
- **Then** all 4 copies of `task_1_setup.md` must have their frontmatter `status:` updated to `"in-progress"`
- **And** all 4 copies must have their `modified:` field updated to the current ISO-8601 UTC timestamp ending in `Z`
- **And** the document body and all unrelated frontmatter keys (`priority`, `assignee`, `labels`, `order`) must remain preserved byte-for-byte
- **And** the script must exit with status code `0` and output the board tally.

#### Scenario 1.2: CompletedAt Timestamp Invariant on Done
- **Tag**: `[Tier A - Unit]`
- **Given** an epic task is in `"review"` with `completedAt: null`
- **When** the reviewer approves and executes `sync_task_status.py task task_1_setup done`
- **Then** `status:` becomes `"done"`
- **And** `completedAt:` must be populated with the current ISO-8601 UTC timestamp
- **And** `modified:` must match the same current timestamp.

#### Scenario 1.3: Epic Overview Status Synchronization
- **Tag**: `[Tier A - Unit]`
- **Given** both `kanban_sync_impact_analysis.en.md` and `kanban_sync_impact_analysis.vi.md` exist with `Status: Planned`
- **When** `sync_task_status.py epic kanban_sync_impact_analysis "In Progress"` is executed
- **Then** the Meta Data `Status:` line in both the `.en.md` and `.vi.md` files must be updated to `"In Progress"`
- **And** neither language variant may diverge from the other.

#### Scenario 2.1: Rejection of Invalid Status Enumerations
- **Tag**: `[Tier A - Unit]`
- **Given** a user or agent invokes `sync_task_status.py task task_1_setup blocked`
- **When** the status argument is evaluated against the 5-column enum (`backlog`, `todo`, `in-progress`, `review`, `done`)
- **Then** the script must refuse to write to any file
- **And** print an error to stderr stating `Invalid status 'blocked'. Expected one of: backlog, todo, in-progress, review, done`
- **And** exit with code `2`.

#### Scenario 2.2: Epic Collision Guard across Duplicate Task IDs
- **Tag**: `[Tier A - Unit]`
- **Given** a task `task_1_setup` exists under `epic: "kanban-sync-impact-analysis"` in `.devtool/features/`
- **And** a different task with the same filename `task_1_setup.md` exists under `.devtool/epic/payments/` with `epic: "payments"`
- **When** `sync_task_status.py task task_1_setup in-progress` is invoked
- **Then** the file under `payments/` must be skipped
- **And** a warning note must be printed reporting the epic mismatch
- **And** only the copies belonging to `"kanban-sync-impact-analysis"` may be updated.

#### Scenario 2.3: Insertion of Absent Frontmatter Keys
- **Tag**: `[Tier A - Unit]`
- **Given** a legacy task file created without `modified:` or `completedAt:` fields
- **When** `sync_task_status.py task legacy_task done` is invoked
- **Then** `modified:` and `completedAt:` must be inserted directly following `status:`
- **And** existing keys and markdown body must not be corrupted.

## Test & Verification Checklist
- [ ] **RED**: Run `python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py` and ensure tests fail for newly specified edge conditions (such as resetting `completedAt` to `null` when rolling back from `done`, or handling detached HEAD checkouts).
- [ ] **GREEN**: Refine `sync_task_status.py` to satisfy all test cases with clean stdout/stderr reporting.
- [ ] **REFACTOR**: Ensure clean code standards (functions < 25 lines, single responsibility, type annotations), format with standard linter/formatter.
- [ ] **Tier C (Integration)**: Execute `sync_task_status.py` against live dummy tasks in simulated main and worktree checkouts, asserting byte integrity of surrounding Markdown body.

## Definition of Done (DoD)
- `sync_task_status.py` successfully handles task and epic status changes.
- All unit tests in `test_sync_task_status.py` pass 100% with zero warnings or errors.
- Frontmatter timestamps (`modified` and `completedAt`) adhere to UTC ISO-8601 formatting (`YYYY-MM-DDTHH:MM:SSZ`).
- Strict 5-column enum validation prevents corruption of status boards.

## Dependencies & Blockers
- **Blocked by**: None (Foundation Task).
- **Blocks**: [Task 4](../../features/task_4_workflow_integration.md).

## References & Rollback
- Reference: [HLD Section 4: Dual-Workspace Kanban Synchronization](kanban_sync_impact_analysis.en.md#4-dual-workspace-kanban-synchronization)
- Rollback Strategy: Revert changes to `sync_task_status.py` and `test_sync_task_status.py` via git checkout.
