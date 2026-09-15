---
id: "task_4_workflow_integration"
status: "done"
priority: "high"
assignee: null
epic: "kanban-sync-impact-analysis"
dueDate: null
created: "2026-09-15T02:30:00Z"
modified: "2026-09-14T19:53:33Z"
completedAt: "2026-09-14T19:53:33Z"
labels: ["skills", "workflow", "epic-designer", "epic-implementation"]
order: "a4"
---

# Task 4: Integrate Workflow Gates in Epic Designer and Epic Implementation

Epic: [kanban-sync-impact-analysis](kanban_sync_impact_analysis.en.md)

## Requirement Analysis
The tooling developed in Tasks 1 and 2 must be seamlessly wired into the primary agent workflows to enforce automated governance without requiring manual developer intervention.

This task integrates the tools and gates into `epic-designer` and `epic-implementation`:
1. **`skills/epic-designer/SKILL.md` Updates**:
   - **Check 1 (Shift-Left Impact Analysis)**: Add an explicit requirement during Step 1 and Step 2 to execute `check_code_impact.py` on the architectural touchpoints.
   - **Task File Template Enrichment**: Add a mandatory section `### Impact Analysis & Blast Radius` to every generated task file, detailing target files, blast radius, bridge contracts, and expected test coverage thresholds.
2. **`skills/epic-implementation/SKILL.md` Updates**:
   - **Phase 2 Step 0 (Pre-Edit Verification)**: Before modifying any source file in a task, run `check_code_impact.py`. If upstream divergence is detected on `<base_ref>`, halt and alert the developer.
   - **Live Dual-Workspace Kanban Synchronization**: At every task state transition (`todo` -> `in-progress` -> `review` -> `done`), execute `python3 skills/epic-implementation/resources/scripts/sync_task_status.py task <task_id> <status>`.
   - **Phase 4 Step 5 (Clean Merge Invariant)**: Before merging the branch back into `<base_ref>`, run `git -C "$MAIN_ROOT" restore -- .devtool/features/ .devtool/epic/<epic_dir>/` to ensure the main checkout's working tree is 100% clean, avoiding merge aborts.

## Relevant Files & Context Pointers
- `skills/epic-designer/SKILL.md`: Epic design workflow instructions.
- `skills/epic-implementation/SKILL.md`: Epic implementation workflow instructions.
- `skills/epic-implementation/resources/scripts/sync_task_status.py`: Integrated status synchronizer.
- `skills/impact-analysis/resources/scripts/check_code_impact.py`: Integrated impact analyzer.
- `.devtool/epic/kanban_sync_impact_analysis/bdd_scenarios.md`: BDD Scenario 5.2.

## Design Rationale
- **Deterministic Gates**: Explicit numbered steps prevent agents from skipping pre-edit impact checks or forgetting to mirror status changes to the main checkout.
- **Fail-Safe Merges**: Reverting the main checkout's mirrored files right before git merge ensures that git never flags working tree overwrite errors during checkout/merge operations.

### BDD SCENARIOS

#### Scenario 5.2: Main Checkout Mirror Reversion before Merge
- **Tag**: `[Tier C - Integration]`
- **Given** the main checkout contains mirrored `.devtool/features/*.md` files updated during task execution
- **When** Phase 4 executes `git -C "$MAIN_ROOT" restore -- .devtool/features/ .devtool/epic/<epic_dir>/`
- **Then** `git -C "$MAIN_ROOT" status --porcelain` must be completely clean
- **And** merging the epic branch into `<base_ref>` must execute with zero git working tree collision.

## Test & Verification Checklist
- [ ] **RED**: Review current `epic-designer/SKILL.md` and `epic-implementation/SKILL.md` to confirm absence of Step 0 Pre-Edit impact checks and live `sync_task_status.py` calls.
- [ ] **GREEN**: Update `skills/epic-designer/SKILL.md` and `skills/epic-implementation/SKILL.md` with explicit instructions, bash command blocks, and gate requirements.
- [ ] **REFACTOR**: Verify markdown formatting, checklist syntax, and diagram consistency across skills.
- [ ] **Tier C (Integration)**: Perform a dry-run simulating an agent moving through Phase 2 Step 0, executing `sync_task_status.py`, and verifying main checkout state.

## Definition of Done (DoD)
- `epic-designer/SKILL.md` mandates Check 1 (Shift-Left) and enriches task templates with `### Impact Analysis & Blast Radius`.
- `epic-implementation/SKILL.md` includes Step 0 Pre-Edit Verification, live dual-workspace status calls, and Phase 4 main checkout clean-up.
- Markdown links between skills and tools are validated.

## Dependencies & Blockers
- **Blocked by**: [Task 1](task_1_kanban_sync_status.md), [Task 2](task_2_pre_edit_impact_checker.md), [Task 3](task_3_impact_analysis_skill.md).
- **Blocks**: None.

## References & Rollback
- Reference: [HLD Section 5: Skill Integrations & Quality Gates](kanban_sync_impact_analysis.en.md#5-skill-integrations--quality-gates)
- Rollback Strategy: Restore previous versions of `epic-designer/SKILL.md` and `epic-implementation/SKILL.md` via git.
