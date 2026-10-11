---
id: "task_3_build_result_aggregation_engine"
status: "todo"
priority: "high"
assignee: null
epic: "provider_based_quality_check"
dueDate: null
created: "2026-10-11T14:22:20+07:00"
modified: "2026-10-11T14:22:20+07:00"
completedAt: null
labels: ["quality", "aggregation", "python", "tdd"]
order: "a3"
---

# Task 3: Build the Result Aggregation Engine

Epic: [provider_based_quality_check](provider_based_quality_check.en.md)

## Requirement Analysis

Implement deterministic reduction of validated provider results into a unified decision model and
report payload. The engine must preserve every defect and blocker, apply precedence
FAIL over BLOCKED over PASS, handle optional NOT_APPLICABLE results only with valid applicability
evidence, reject an all-NOT_APPLICABLE required provider, and record the decision trace.

The engine consumes only validated normalized data. It does not run providers, inspect platforms,
or render platform-specific prose.

## Relevant Files & Context Pointers

- `skills/quality_check/resources/scripts/aggregate_quality_results.py`
- `skills/quality_check/resources/scripts/test_aggregate_quality_results.py`
- `skills/quality_check/references/aggregation-contract.md`
- `skills/quality_check/references/executive-report-format.md`
- `skills/quality_check/resources/fixtures/`
- `scripts/verify.sh`

## Design Rationale

Status reduction is safety-critical policy and should not depend on an agent reading a table
correctly. Keeping aggregation separate from validation makes each failure source observable and
lets provider execution remain replaceable. A normalized report payload also keeps Markdown
rendering from changing the verdict.

Applicable skills: `d3nexus:test-driven-development`,
`d3nexus:verification-before-completion`, and `d3nexus:impact-analysis`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `aggregate_results`, `normalize_checks`,
  `build_decision_trace`, and report payload structures.
- **Downstream callers**: the refactored orchestrator, lifecycle Gate 4 reports, PR review, and Tier C
  acceptance fixtures.
- **Cross-platform bridges**: common result semantics affect every future platform provider.
- **Target test coverage threshold**: 100% branch coverage for precedence, requiredness,
  NOT_APPLICABLE, duplicates, empty result sets, and deterministic ordering.

## BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] All required providers pass
  Given every required selected provider has a valid PASS result
  When results are aggregated
  Then the overall verdict is PASS
  And the decision trace names every provider

Scenario: [Tier A - Unit] Failure outranks infrastructure blockage
  Given one valid provider returns FAIL
  And another valid provider returns BLOCKED
  When results are reduced
  Then the overall verdict is FAIL
  And both details remain in the report payload

Scenario: [Tier A - Unit] Required not-applicable state is blocked
  Given a required provider contains only NOT_APPLICABLE checks
  When requiredness is evaluated
  Then the provider contributes BLOCKED
  And the overall verdict cannot be PASS

Scenario: [Tier A - Unit] Completion order cannot alter output
  Given the same provider results arrive in several permutations
  When each permutation is aggregated
  Then serialized report payloads have identical provider and check ordering
  And all verdicts match

Scenario: [Tier C - Integration] Missing and corrupt results remain distinguishable
  Given one provider result is absent and another cannot be parsed
  When validation findings are aggregated
  Then both providers contribute separate BLOCKED entries
  And the executive payload identifies each root cause
```

## Test & Verification Checklist

- [ ] **RED**: Add failing table-driven tests for the complete status truth table.
- [ ] **GREEN**: Implement minimal pure aggregation functions.
- [ ] **REFACTOR**: keep ordering, reduction, and report-payload construction separate.
- [ ] Test PASS-only, FAIL-only, BLOCKED-only, mixed, empty, optional, and required result sets.
- [ ] Test all valid and invalid NOT_APPLICABLE combinations.
- [ ] Test provider and check permutations for byte-stable normalized JSON.
- [ ] Confirm warnings do not change status and blockers cannot be hidden.
- [ ] **Tier B**: wire aggregation tests and contract-reference checks into `scripts/verify.sh`.
- [ ] **Tier C**: aggregate a multi-provider fixture containing PASS, FAIL, and BLOCKED evidence.

## Definition of Done

- The complete reduction policy is executable and documented.
- A decision trace explains why the overall verdict was selected.
- Output ordering is deterministic regardless of provider completion order.
- Aggregation does not inspect the repository or invoke commands.
- Unit tests and full repository verification pass.

## Dependencies & Blockers

- Blocked by [Task 2](task_2_build_provider_contract_validator.md).
- Blocks [Task 4](task_4_refactor_quality_check_orchestrator.md),
  [Task 5](task_5_add_rust_quality_provider.md),
  [Task 6](task_6_integrate_lifecycle_consumers.md), and
  [Task 8](task_8_run_end_to_end_acceptance.md).

## References & Rollback

- [HLD verification strategy](provider_based_quality_check.en.md#verification-strategy)
- [BDD aggregation scenarios](bdd_scenarios.en.md#uc6-provider-authoring-and-aggregation)
- **Rollback**: remove the aggregation module and its references before the orchestrator consumes it.
