---
id: "task_6_integrate_lifecycle_consumers"
status: "done"
priority: "high"
assignee: null
epic: "provider_based_quality_check"
dueDate: null
created: "2026-10-11T14:22:20+07:00"
modified: "2026-10-11T18:14:59Z"
completedAt: "2026-10-11T18:14:59Z"
labels: ["quality", "lifecycle", "integration", "skill"]
order: "a6"
---

# Task 6: Integrate Lifecycle Consumers

Epic: [provider_based_quality_check](../epic/provider_based_quality_check/provider_based_quality_check.en.md)

## Requirement Analysis

Update `dev-implementation`, `dev-lifecycle`, and `pr_review` to invoke and consume the common
provider-based quality contract. Gate 4 must pass profile `epic`, the base reference, and the
candidate SHA explicitly. PR review must pass `pr`. All consumers must treat PASS as the only
LGTM-capable verdict and route FAIL or BLOCKED back with the complete actionable report.

Remove end-of-epic platform detection and embedded command assumptions only where quality
orchestration is concerned. Platform-specific implementation guidance outside the gate remains
unchanged.

## Relevant Files & Context Pointers

- `skills/dev-implementation/SKILL.md`
- `skills/dev-lifecycle/SKILL.md`
- `skills/pr_review/SKILL.md`
- `skills/quality_check/SKILL.md`
- `skills/quality_check/references/executive-report-format.md`
- `scripts/verify.sh`
- `evals/provider_based_quality_check/`

## Design Rationale

Consumers state intent and identity; they do not select ecosystems. This keeps Gate 4 stable for
super apps and microservices and prevents a cheaper direct default from satisfying epic
certification. A verdict belongs to one SHA, so any later change requires a fresh gate.

Applicable skills: `d3nexus:dev-lifecycle`, `d3nexus:dev-implementation`,
`d3nexus:writing-skills`, and `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: Gate 4 entry/exit criteria, end-of-epic invocation, PR review
  invocation, report handoff, and stale-verdict language.
- **Downstream callers**: every epic and PR workflow using the agent kit.
- **Cross-platform bridges**: no direct bridge; mobile command ownership moves behind future
  providers, making project registration a prerequisite.
- **Target test coverage threshold**: 100% of formal caller paths must assert explicit profile and
  SHA behavior; every Gate 4 transition has a lifecycle contract test.

## BDD SCENARIOS

```gherkin
Scenario: [Tier C - Integration] Gate 4 sends an explicit epic request
  Given every epic task is done and a candidate SHA is resolved
  When dev-implementation invokes quality_check
  Then profile epic, base_ref, and repository_sha are explicit
  And a direct default is not relied upon

Scenario: [Tier C - Integration] PR review sends an explicit PR request
  Given a PR diff and base reference
  When pr_review delegates quality
  Then it requests profile pr
  And it consumes the normalized provider report

Scenario: [Tier A - Unit] BLOCKED cannot transition Gate 4 to approved
  Given the aggregated provider verdict is BLOCKED
  When dev-lifecycle evaluates Gate 4
  Then it routes back to implementation with blockers
  And LGTM is not rendered

Scenario: [Tier C - Integration] Parallel providers remain one lifecycle gate
  Given multiple providers execute for an epic
  When their unified report is returned
  Then the lifecycle waits for the complete aggregate verdict
  And it does not approve on the first provider to pass

Scenario: [Tier C - Integration] Candidate mutation invalidates prior approval
  Given Gate 4 passed for one SHA
  When any later commit changes the candidate
  Then the old verdict is stale
  And the lifecycle requires a new epic quality run
```

## Test & Verification Checklist

- [x] **RED**: add or update lifecycle contract tests that fail while callers omit provider inputs.
- [x] **GREEN**: minimally update the three consumer skills.
- [x] **REFACTOR**: remove duplicated platform quality wording without disturbing task
      implementation guidance.
- [x] Verify Gate 4 explicitly requests `epic`, base reference, and candidate SHA.
- [x] Verify PR review explicitly requests `pr`.
- [x] Verify PASS is the only LGTM path and FAIL/BLOCKED return complete findings.
- [x] Verify stale SHA language remains consistent with branch integration rules.
- [x] **Tier B**: extend lifecycle document contract checks to reject platform command matrices and
      implicit profiles in these consumer sections.
- [x] **Tier C**: exercise PASS, FAIL, BLOCKED, multi-provider, and post-verdict SHA-change flows.

## Definition of Done

- Formal lifecycle and PR callers pass explicit normalized inputs.
- Gate 4 accepts only aggregate PASS for the candidate SHA.
- No consumer embeds Rust commands or provider-selection logic.
- Existing non-quality implementation guidance remains intact.
- Lifecycle contract tests and full repository verification pass.

## Dependencies & Blockers

- Blocked by [Task 3](task_3_build_result_aggregation_engine.md),
  [Task 4](task_4_refactor_quality_check_orchestrator.md), and
  [Task 5](task_5_add_rust_quality_provider.md).
- Blocks [Task 7](task_7_publish_provider_architecture_docs.md) and
  [Task 8](task_8_run_end_to_end_acceptance.md).

## References & Rollback

- [HLD primary sequence](../epic/provider_based_quality_check/provider_based_quality_check.en.md#primary-sequence)
- [Epic Gate BDD scenarios](../epic/provider_based_quality_check/bdd_scenarios.en.md#uc2-epic-gate-certification)
- **Rollback**: revert the caller changes and orchestrator refactor as one compatibility unit. Never
  leave callers expecting a result contract the active quality skill does not provide.

