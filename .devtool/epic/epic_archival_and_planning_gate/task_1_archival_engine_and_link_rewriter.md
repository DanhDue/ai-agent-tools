---
id: "task_1_archival_engine_and_link_rewriter"
status: "done"
priority: "high"
assignee: null
epic: "epic-archival-and-planning-gate"
dueDate: null
created: "2026-09-15T04:50:00Z"
modified: "2026-09-15T04:51:41Z"
completedAt: "2026-09-15T04:51:41Z"
labels: ["tooling", "archival", "sync", "kanban"]
order: "a1"
---

# Task 1: Complete Archival Engine and Link Rewriter in sync_task_status.py

Epic: [epic-archival-and-planning-gate](epic_archival_and_planning_gate.en.md)

## Requirement Analysis
In an agentic mobile engineering workflow, completed tasks often linger in `.devtool/features/done/`, and draft artifacts clutter `docs/superpowers/`. When an epic completes, all finished `task_*.md` files must be relocated to `.devtool/epic/<epic_dir>/`, and their internal relative markdown links (`Epic:`, `Blocks:`, `Blocked by:`, `Reference:`) as well as the links in Section 8 of the parent Epic Overviews must be rewritten to point locally.

## Relevant Files & Context Pointers
- `skills/epic-implementation/resources/scripts/sync_task_status.py`: Archival engine, link rewriter, and CLI parser.
- `skills/epic-implementation/resources/scripts/test_sync_task_status.py`: Unit test suite covering all archival and rewrite functions.

## Design Rationale
Keep the solution stdlib-only using regex and `pathlib.Path`. Implement `archive_epic_tasks` to handle multi-checkout discovery, link rewriting, and `.gitkeep` retention. Automatically invoke archival inside `sync_epic` when status transitions to `Done` or `Hoàn thành`, and expose `archive-epic` as a standalone CLI sub-command.

## Impact Analysis & Blast Radius
- **Target Files & Symbols**: `sync_task_status.py` (`archive_epic_tasks`, `archive_superpowers_docs`, `find_epic_slug`, `fix_task_markdown_links`, `fix_epic_overview_links`).
- **Downstream Callers**: `epic-implementation` Phase 4.1, manual developer CLI execution.
- **Target Test Coverage Threshold**: 100% line coverage for new archival logic.

### BDD SCENARIOS

#### [Tier A - Unit]
- **Scenario 1**: Task markdown link rewriter replaces parent epic paths `](../epic/<epic_dir>/<file>)` with `](<file>)` and features paths `](../../features/(?:done/)?(task_*.md))` with `]($1)`.
- **Scenario 2**: Epic overview Section 8 link rewriter replaces `](../../features/(?:done/)?(task_*.md))` with `]($1)`.
- **Scenario 3**: `archive_superpowers_docs` moves matching specs/plans from `docs/superpowers/(plans|specs)/` into `.devtool/epic/<epic_dir>/` and preserves `.gitkeep`.
- **Scenario 4**: `archive_epic_tasks` moves task files from `.devtool/features/done/` into `.devtool/epic/<epic_dir>/`, cleans up sources, creates `.gitkeep`, and updates overview Section 8 links.
- **Scenario 5**: `sync_epic` automatically triggers `archive_epic_tasks` when called with `Done`.
- **Scenario 6**: `expected_epic` and `board_tally` continue to resolve and tally archived tasks located in `.devtool/epic/<epic_dir>/`.

## Test & Verification Checklist
- [ ] **RED**: Add unit tests in `test_sync_task_status.py` verifying link rewriting, task archival, superpowers archival, and tallying of archived tasks.
- [ ] **GREEN**: Implement `archive_epic_tasks`, `archive_superpowers_docs`, `find_epic_slug`, `fix_task_markdown_links`, `fix_epic_overview_links`, and CLI parser in `sync_task_status.py`.
- [ ] **REFACTOR**: Ensure zero regressions on existing 33 tests; verify all 39 tests pass cleanly.

## Definition of Done (DoD)
- All 39 unit tests pass in `test_sync_task_status.py`.
- `sync_task_status.py archive-epic <epic_dir>` functions from the command line.

## Dependencies & Blockers
- **Blocked by**: None (Foundation Task).
- **Blocks**: [Task 3](task_3_workflow_skills_documentation.md), [Task 4](task_4_workspace_verification_and_release.md).

## References & Rollback
- Reference: [HLD Section 4: Architecture & Technical Design](epic_archival_and_planning_gate.en.md#4-architecture--technical-design)
- Rollback Strategy: Revert edits to `sync_task_status.py` and `test_sync_task_status.py` via git checkout.
