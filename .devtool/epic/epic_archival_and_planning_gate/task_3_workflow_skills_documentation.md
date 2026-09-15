---
id: "task_3_workflow_skills_documentation"
status: "todo"
priority: "medium"
assignee: null
epic: "epic-archival-and-planning-gate"
dueDate: null
created: "2026-09-15T04:50:00Z"
modified: "2026-09-15T04:50:00Z"
completedAt: null
labels: ["documentation", "skills", "lifecycle", "designer"]
order: "a3"
---

# Task 3: Update Workflow Skills Documentation

Epic: [epic-archival-and-planning-gate](epic_archival_and_planning_gate.en.md)

## Requirement Analysis
With automated archival on epic completion in place, the core skills `epic-designer`, `epic-implementation`, and `epic-lifecycle` must clearly document the full lifecycle of task files and draft design documents. Developers and agents reading these skills must understand that `.devtool/features/done/` is an ephemeral development holding area, and upon epic completion, all tasks and draft superpowers documents are archived directly into `.devtool/epic/<epic_dir>/`.

## Relevant Files & Context Pointers
- `skills/epic-designer/SKILL.md`: Task generation and placement instructions.
- `skills/epic-implementation/SKILL.md`: Execution workflow and Step 4.1 epic sync & archival instructions.
- `skills/epic-lifecycle/SKILL.md`: Gate 4 verification and archival completion.

## Design Rationale
Update skill instructions with concise, accurate descriptions of the archival process:
1. `epic-designer`: Document that tasks are created in `.devtool/features/` (and mirrored in `.devtool/epic/<epic_dir>/`).
2. `epic-implementation`: Detail Step 4.1 automated archival, explaining that when `sync_task_status.py epic <epic_dir> Done` runs, tasks move from `.devtool/features/done/` to `.devtool/epic/<epic_dir>/`, links are rewritten, and superpowers drafts are relocated.
3. `epic-lifecycle`: Update Gate 4 exit criteria to mandate clean `.devtool/features/done/` with zero residue.

## Impact Analysis & Blast Radius
- **Target Files & Symbols**: `skills/epic-designer/SKILL.md`, `skills/epic-implementation/SKILL.md`, `skills/epic-lifecycle/SKILL.md`.
- **Downstream Callers**: Agent workflows executing epic design and implementation.
- **Target Test Coverage Threshold**: Verified via `bash scripts/verify.sh`.

### BDD SCENARIOS

#### [Tier A - Integration]
- **Scenario 1**: `skills/epic-designer/SKILL.md` explains task creation and future archival lifecycle.
- **Scenario 2**: `skills/epic-implementation/SKILL.md` describes automated archival on `sync_epic Done`.
- **Scenario 3**: `skills/epic-lifecycle/SKILL.md` defines Gate 4 clean workspace criteria.
- **Scenario 4**: `bash scripts/verify.sh` verifies markdown formatting, frontmatter, and links across all skills.

## Test & Verification Checklist
- [ ] **RED**: Check `skills/epic-designer/SKILL.md`, `skills/epic-implementation/SKILL.md`, and `skills/epic-lifecycle/SKILL.md` for outdated or missing task lifecycle references.
- [ ] **GREEN**: Update skill files with accurate documentation and instructions.
- [ ] **REFACTOR**: Run `bash scripts/verify.sh` to verify markdown links, anchor tags, and TOC consistency.

## Definition of Done (DoD)
- Documentation across all 3 skills accurately reflects the archival engine and gate requirements.
- `bash scripts/verify.sh` passes cleanly.

## Dependencies & Blockers
- **Blocked by**: [Task 1](task_1_archival_engine_and_link_rewriter.md), [Task 2](task_2_antigravity_planning_gate.md).
- **Blocks**: [Task 4](task_4_workspace_verification_and_release.md).

## References & Rollback
- Reference: [HLD Section 4: Architecture & Technical Design](epic_archival_and_planning_gate.en.md#4-architecture--technical-design)
- Rollback Strategy: Revert skill documentation updates via git checkout.
