---
id: "task_2_antigravity_planning_gate"
status: "done"
priority: "high"
assignee: null
epic: "epic-archival-and-planning-gate"
dueDate: null
created: "2026-09-15T04:50:00Z"
modified: "2026-09-15T04:52:34Z"
completedAt: "2026-09-15T04:52:34Z"
labels: ["rules", "hooks", "antigravity", "planning-gate"]
order: "a2"
---

# Task 2: Implement Antigravity Planning Gate in CRITICAL_RULES and Hook

Epic: [epic-archival-and-planning-gate](epic_archival_and_planning_gate.en.md)

## Requirement Analysis
Antigravity IDE dynamically injects a `<planning_mode>` section into the agent system prompt when it perceives a request warrants a plan. This directs the agent to generate `<appDataDir>/brain/<conversation-id>/implementation_plan.md` using native planning mode rather than invoking the `d3nexus:brainstorming` or `d3nexus:epic-lifecycle` workflow skills. Because `<user_rules>` in Antigravity has supreme priority that explicitly overrides subsequent instructions, adding a strict gate in `rules/CRITICAL_RULES.md` and reinforcing it in `hooks/session-start` ensures the agent stays strictly on the d3nexus workflow.

## Relevant Files & Context Pointers
- `rules/CRITICAL_RULES.md`: Mandatory rules loaded into `<user_rules>`.
- `hooks/session-start`: PreInvocation hook executed on turn 0 (`invocationNum == 0`).

## Design Rationale
Implement a dual-layer interception:
1. `rules/CRITICAL_RULES.md`: Explicitly prohibit writing to `implementation_plan.md` when planning or designing features, mandating invocation of `d3nexus:brainstorming` (for single features) or `d3nexus:epic-lifecycle` (for epic-scale work).
2. `hooks/session-start`: Add turn-0 reminder context regarding planning mode interception in the injected ephemeral payload.

## Impact Analysis & Blast Radius
- **Target Files & Symbols**: `rules/CRITICAL_RULES.md`, `hooks/session-start`.
- **Downstream Callers**: All AI agents running with d3nexus plugin in Antigravity or Claude Code.
- **Target Test Coverage Threshold**: Verified via `bash scripts/verify.sh` and BDD scenarios.

### BDD SCENARIOS

#### [Tier A - Integration]
- **Scenario 1**: In Antigravity IDE, `rules/CRITICAL_RULES.md` mandates that when a task requires planning, the agent invokes `d3nexus:brainstorming` or `d3nexus:epic-lifecycle` rather than generating `implementation_plan.md`.
- **Scenario 2**: In `hooks/session-start`, turn-0 message injection includes planning mode interception guidance alongside `using-superpowers`.
- **Scenario 3**: `bash scripts/verify.sh` verifies hook JSON output and rule syntax cleanly.

## Test & Verification Checklist
- [ ] **RED**: Inspect `rules/CRITICAL_RULES.md` and `hooks/session-start` to identify missing planning gate instructions.
- [ ] **GREEN**: Add mandatory Planning Mode Interception section to `rules/CRITICAL_RULES.md` and update `hooks/session-start`.
- [ ] **REFACTOR**: Execute `bash scripts/verify.sh` to ensure hook validity and rule integrity.

## Definition of Done (DoD)
- `rules/CRITICAL_RULES.md` contains the mandatory Antigravity Planning Mode Interception rule.
- `hooks/session-start` contains the planning gate prompt injection.
- `bash scripts/verify.sh` passes 100%.

## Dependencies & Blockers
- **Blocked by**: None.
- **Blocks**: [Task 3](task_3_workflow_skills_documentation.md), [Task 4](task_4_workspace_verification_and_release.md).

## References & Rollback
- Reference: [HLD Section 4: Architecture & Technical Design](epic_archival_and_planning_gate.en.md#4-architecture--technical-design)
- Rollback Strategy: Revert edits to `rules/CRITICAL_RULES.md` and `hooks/session-start` via git checkout.
