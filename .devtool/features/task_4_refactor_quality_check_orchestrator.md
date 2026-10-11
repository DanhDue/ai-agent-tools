---
id: "task_4_refactor_quality_check_orchestrator"
status: "todo"
priority: "high"
assignee: null
epic: "provider_based_quality_check"
dueDate: null
created: "2026-10-11T14:22:20+07:00"
modified: "2026-10-11T14:22:20+07:00"
completedAt: null
labels: ["quality", "orchestration", "skill", "breaking-change"]
order: "a4"
---

# Task 4: Refactor the Quality Check Orchestrator

Epic: [provider_based_quality_check](../epic/provider_based_quality_check/provider_based_quality_check.en.md)

## Requirement Analysis

Rewrite `quality_check` as a thin, platform-neutral kernel. It normalizes caller inputs, loads the
project registry, validates and resolves all providers selected for the profile, invokes them with
the same immutable request, verifies final HEAD, validates results, calls the aggregation engine,
and renders the unified report.

Remove mobile command matrices, file-based platform detection, thresholds, auto-fix behavior, and
first-match routing. A missing registry, unresolved provider, empty selection, invocation failure,
timeout, missing result, invalid result, or SHA drift must produce BLOCKED.

## Relevant Files & Context Pointers

- `skills/quality_check/SKILL.md`
- `skills/quality_check/references/provider-registry-contract.md`
- `skills/quality_check/references/provider-result-contract.md`
- `skills/quality_check/references/aggregation-contract.md`
- `skills/quality_check/references/executive-report-format.md`
- `skills/quality_check/resources/scripts/`
- `evals/provider_based_quality_check/`
- `scripts/verify.sh`

## Design Rationale

The registry is the dependency-injection boundary. The orchestrator knows provider contracts, not
ecosystems. This permits a super app or microservice monorepo to compose multiple checks and lets a
new provider ship without editing a platform switch. Read-only execution preserves the SHA being
certified.

Applicable skills: `d3nexus:writing-skills`, `d3nexus:test-driven-development`,
`d3nexus:impact-analysis`, and `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: the full `quality_check` workflow, provider selection, report format,
  and activation description.
- **Downstream callers**: `dev-lifecycle`, `dev-implementation`, `pr_review`, branch finishing,
  and all consumer repositories.
- **Cross-platform bridges**: existing embedded mobile behavior is removed; later mobile providers
  must restore that capability through registration.
- **Target test coverage threshold**: 100% of the orchestrator behavioral contract and all five
  pressure-test regressions; no untested path may emit LGTM.

## BDD SCENARIOS

```gherkin
Scenario: [Tier C - Integration] Composite repository invokes every selected provider
  Given a valid registry selects two providers for epic
  When quality_check runs
  Then both providers receive the identical normalized request
  And both validated results appear in the report

Scenario: [Tier C - Integration] Missing registry fails closed
  Given a repository has recognizable mobile or Rust files
  But it has no quality registry
  When quality_check starts
  Then the verdict is BLOCKED
  And no platform fallback is attempted

Scenario: [Tier A - Unit] Orchestration state cannot pass before final HEAD validation
  Given all providers return PASS
  When final HEAD differs from repository_sha
  Then their results are stale
  And the verdict is BLOCKED instead of PASS

Scenario: [Tier C - Integration] Parallel fan-out remains deterministic
  Given independent providers are safe to run concurrently
  When completion order changes
  Then result validation and report ordering remain stable
  And every selected provider is accounted for

Scenario: [Tier C - Integration] Provider invocation failure preserves other evidence
  Given one provider cannot be invoked
  And another provider returns a valid FAIL result
  When aggregation completes
  Then the invocation problem appears as BLOCKED
  And the overall verdict is FAIL with both findings visible
```

## Test & Verification Checklist

- [ ] **RED**: rerun the relevant Task 1 scenarios and confirm current behavior still violates them.
- [ ] **GREEN**: replace platform branching with the minimum registry-driven orchestration.
- [ ] **REFACTOR**: keep `SKILL.md` concise and move contract detail into referenced resources.
- [ ] Confirm direct invocation defaults only to `pr`; formal callers must pass a profile.
- [ ] Confirm all matching providers run and no repository file heuristic selects one.
- [ ] Confirm no auto-fix or source mutation instruction remains.
- [ ] Confirm missing and malformed dependencies become BLOCKED.
- [ ] Confirm final report includes invocation identity, registry digest, providers, checks, coverage,
      blockers, warnings, evidence, and decision trace.
- [ ] **Tier B**: add verification that the orchestrator contains no platform commands, thresholds,
      or hardcoded provider list.
- [ ] **Tier C**: rerun all five pressure scenarios and record the GREEN delta.

## Definition of Done

- `quality_check` is a thin provider orchestrator with exact two-field skill frontmatter.
- All selected providers are invoked and reconciled.
- Only an aggregate PASS bound to the requested SHA can render LGTM.
- The five baseline failures are corrected without introducing auto-fix behavior.
- Skill checks, behavioral evaluations, and full repository verification pass.

## Dependencies & Blockers

- Blocked by [Task 1](task_1_capture_red_behavioral_baseline.md),
  [Task 2](task_2_build_provider_contract_validator.md), and
  [Task 3](task_3_build_result_aggregation_engine.md).
- Blocks [Task 6](task_6_integrate_lifecycle_consumers.md),
  [Task 7](task_7_publish_provider_architecture_docs.md), and
  [Task 8](task_8_run_end_to_end_acceptance.md).

## References & Rollback

- [Approved source design](../epic/provider_based_quality_check/2026-10-11-provider-based-quality-check-design.en.md)
- [HLD architecture](../epic/provider_based_quality_check/provider_based_quality_check.en.md#architecture-and-technical-design)
- **Rollback**: revert the orchestrator change together with any consumer caller changes. Do not keep
  a half-migrated lifecycle that expects provider results from the legacy skill.

