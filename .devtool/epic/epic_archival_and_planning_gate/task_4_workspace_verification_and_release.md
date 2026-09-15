---
id: "task_4_workspace_verification_and_release"
status: "todo"
priority: "high"
assignee: null
epic: "epic-archival-and-planning-gate"
dueDate: null
created: "2026-09-15T04:50:00Z"
modified: "2026-09-15T04:50:00Z"
completedAt: null
labels: ["verification", "release", "quality-check"]
order: "a4"
---

# Task 4: Complete Workspace Archival, Kit Verification, and Release

Epic: [epic-archival-and-planning-gate](epic_archival_and_planning_gate.en.md)

## Requirement Analysis
Once all implementation and documentation tasks are completed, verify the entire kit with automated test suites (`test_sync_task_status.py`) and verification scripts (`verify.sh`). Then trigger epic completion archival for `epic_archival_and_planning_gate`, ensuring zero leftover files in `.devtool/features/` or `.devtool/features/done/`, and release version v1.0.15 via `scripts/release.sh`.

## Relevant Files & Context Pointers
- `scripts/verify.sh`: Comprehensive kit verification script.
- `scripts/release.sh`: Release management script.
- `~/.gemini/config/plugins/d3nexus`: Local plugin installation target.

## Design Rationale
Follow strict quality check gate standards:
1. Run unit test suite: `python3 test_sync_task_status.py -v` (39 tests pass).
2. Run kit verification: `bash scripts/verify.sh` (pass 100%).
3. Run `sync_task_status.py epic epic_archival_and_planning_gate Done` to archive all completed tasks of this epic.
4. Execute `bash scripts/release.sh` to increment plugin version to v1.0.15, create git tag, push to origin, and refresh local plugin installation.

## Impact Analysis & Blast Radius
- **Target Files & Symbols**: Whole repository, `package.json` / plugin metadata, local d3nexus installation.
- **Downstream Callers**: All consumer projects utilizing d3nexus.
- **Target Test Coverage Threshold**: 100% tests passing, 0 verification warnings/errors.

### BDD SCENARIOS

#### [Tier A - Integration & Release]
- **Scenario 1**: All 39 unit tests pass in `test_sync_task_status.py`.
- **Scenario 2**: `bash scripts/verify.sh` passes with zero errors.
- **Scenario 3**: `sync_task_status.py epic epic_archival_and_planning_gate Done` archives all tasks into `.devtool/epic/epic_archival_and_planning_gate/`.
- **Scenario 4**: `scripts/release.sh` successfully packages v1.0.15 and updates `~/.gemini/config/plugins/d3nexus`.

## Test & Verification Checklist
- [ ] **RED**: Confirm all previous tasks are done before attempting release.
- [ ] **GREEN**: Execute tests, kit verification, and archival.
- [ ] **REFACTOR**: Execute release and verify local installation sync.

## Definition of Done (DoD)
- 39 unit tests pass.
- `verify.sh` passes 100%.
- Workspace is clean: `.devtool/features/done/` contains only `.gitkeep`.
- v1.0.15 released and synced to `~/.gemini/config/plugins/d3nexus`.

## Dependencies & Blockers
- **Blocked by**: [Task 1](task_1_archival_engine_and_link_rewriter.md), [Task 2](task_2_antigravity_planning_gate.md), [Task 3](task_3_workflow_skills_documentation.md).
- **Blocks**: None (Final Epic Completion Task).

## References & Rollback
- Reference: [HLD Section 4: Architecture & Technical Design](epic_archival_and_planning_gate.en.md#4-architecture--technical-design)
- Rollback Strategy: Revert release commit and git tag if verification fails.
