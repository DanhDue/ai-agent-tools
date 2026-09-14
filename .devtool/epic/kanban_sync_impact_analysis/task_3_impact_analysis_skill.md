---
id: "task_3_impact_analysis_skill"
status: "done"
priority: "high"
assignee: null
epic: "kanban-sync-impact-analysis"
dueDate: null
created: "2026-09-15T02:30:00Z"
modified: "2026-09-14T19:50:24Z"
completedAt: "2026-09-14T19:50:24Z"
labels: ["documentation", "skill", "architecture", "double-check"]
order: "a3"
---

# Task 3: Author Dedicated Impact Analysis Skill and Reference Manual

Epic: [kanban-sync-impact-analysis](kanban_sync_impact_analysis.en.md)

## Requirement Analysis
Automated tooling is ineffective if autonomous agents and human developers lack standardized operating procedures to interpret results, make decisions, and resolve flagged issues.

This task creates the dedicated `impact-analysis` agent skill and reference manual:
1. `skills/impact-analysis/SKILL.md`:
   - Skill metadata and trigger conditions (invoked during `brainstorming`, `epic-designer`, pre-edit tasks in `epic-implementation`, and final acceptance in `quality_check`).
   - Detailed workflow for running `check_code_impact.py`.
   - Decision trees for handling `DIVERGENCE DETECTED`, `NATIVE BRIDGE DETECTED`, and `UNPROTECTED CODE`.
2. `skills/impact-analysis/references/impact-mechanisms.md`:
   - Comprehensive technical explanation of the **Double-Check (Bookend Verification)** mechanism.
   - Comparative analysis: Why single-point checking fails (Shift-Left alone misses implementation drift; Shift-Right alone causes expensive rework at PR review).
   - The 4-Layer Impact Pipeline details and underlying regex/AST algorithms.
   - Concrete examples across Flutter, Android Native, and iOS Native architectures.
   - Failure modes, false positive handling, and escalation playbooks.

## Relevant Files & Context Pointers
- `skills/impact-analysis/SKILL.md`: Main skill instruction document with YAML frontmatter.
- `skills/impact-analysis/references/impact-mechanisms.md`: Deep technical reference on double-check philosophy and impact layers.
- `skills/impact-analysis/resources/scripts/check_code_impact.py`: Supporting CLI tool built in Task 2.
- `.devtool/epic/kanban_sync_impact_analysis/kanban_sync_impact_analysis.en.md`: HLD Section 5.4 reference.

## Design Rationale
- **Self-Contained Skill**: Packaging the tool and documentation inside `skills/impact-analysis/` ensures modularity and ease of maintenance.
- **Explicit Agent Directives**: The skill provides unambiguous behavioral instructions so LLM agents know exactly what CLI commands to invoke and how to halt work if high-risk divergence is detected.

### BDD SCENARIOS

#### Scenario 3.4: Agent Skill Invocation during Brainstorming & Design (Check 1)
- **Tag**: `[Tier A - Unit]`
- **Given** an agent is designing an epic touching core authentication tokens
- **When** the agent invokes `impact-analysis` during `epic-designer`
- **Then** the skill instructions guide the agent to run `check_code_impact.py --files <auth_files> --symbols AuthToken`
- **And** the output maps the blast radius across dependent feature modules
- **And** requires adding integration tests in the Kanban task breakdown.

#### Scenario 3.5: Agent Pre-Edit Halt Behavior on Upstream Divergence
- **Tag**: `[Tier A - Unit]`
- **Given** an implementation subagent picks up a task and runs `check_code_impact.py`
- **When** the tool flags `Git Conflict: 🔴 DIVERGENCE DETECTED`
- **Then** following `SKILL.md`, the subagent must immediately halt execution
- **And** output an alert requesting a git rebase against the updated `<base_ref>` before writing any code.

## Test & Verification Checklist
- [ ] **RED**: Verify that invoking or referencing `skills/impact-analysis/SKILL.md` fails or is absent prior to file creation.
- [ ] **GREEN**: Create `skills/impact-analysis/SKILL.md` and `skills/impact-analysis/references/impact-mechanisms.md` with complete YAML frontmatter, markdown sections, and flowcharts.
- [ ] **REFACTOR**: Ensure cross-references between the skill, the reference manual, and the HLD are valid markdown links (`file:///...`).
- [ ] **Tier C (Integration)**: Verify that the skill is discoverable by inspecting plugin and skill registries and reviewing lint/formatting.

## Definition of Done (DoD)
- `skills/impact-analysis/SKILL.md` is authored with YAML frontmatter adhering to Antigravity skill conventions.
- `references/impact-mechanisms.md` provides in-depth rationale, architecture diagrams, and the Double-Check justification.
- All code snippets and command examples match the CLI interface created in Task 2.

## Dependencies & Blockers
- **Blocked by**: [Task 2](../../features/task_2_pre_edit_impact_checker.md).
- **Blocks**: [Task 4](../../features/task_4_workflow_integration.md), [Task 5](../../features/task_5_quality_check_coverage_gate.md).

## References & Rollback
- Reference: [HLD Section 5.4: Double-Check Mechanism (Bookend Verification)](kanban_sync_impact_analysis.en.md#54-double-check-mechanism-bookend-verification)
- Rollback Strategy: Delete created skill folder `skills/impact-analysis/`.
