---
id: "task_2_build_provider_contract_validator"
status: "done"
priority: "high"
assignee: null
epic: "provider_based_quality_check"
dueDate: null
created: "2026-10-11T14:22:20+07:00"
modified: "2026-10-11T17:51:04Z"
completedAt: "2026-10-11T17:51:04Z"
labels: ["quality", "contracts", "python", "tdd"]
order: "a2"
---

# Task 2: Build the Provider Contract Validator

Epic: [provider_based_quality_check](provider_based_quality_check.en.md)

## Requirement Analysis

Define the version-one project registry, normalized invocation, provider result, check, coverage, and
evidence contracts. Implement a standard-library Python validator that converts invalid or missing
required inputs into structured BLOCKED findings. It must reject unknown fields, unsupported
versions, duplicate IDs, empty selections, invalid profiles, unresolved namespaced skills, identity
mismatches, malformed evidence, and invalid NOT_APPLICABLE claims.

The validator is deterministic, read-only, and usable independently by unit tests and the
orchestrator. Contract prose and executable validation must describe the same rules.

## Relevant Files & Context Pointers

- `skills/quality_check/references/provider-registry-contract.md`
- `skills/quality_check/references/provider-result-contract.md`
- `skills/quality_check/resources/schemas/check-quality.schema.json`
- `skills/quality_check/resources/schemas/provider-result.schema.json`
- `skills/quality_check/resources/scripts/validate_quality_contract.py`
- `skills/quality_check/resources/scripts/test_validate_quality_contract.py`
- `skills/quality_check/resources/fixtures/`
- `scripts/verify.sh`

## Design Rationale

A prose-only contract can be interpreted differently under pressure. The validator makes contract
acceptance executable while leaving remediation and provider-specific commands outside the kernel.
Python's standard library matches the kit's existing scripts and avoids introducing a package
bootstrap requirement.

Applicable skills: `d3nexus:test-driven-development`, `d3nexus:writing-skills`, and
`d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `validate_registry`, `normalize_invocation`,
  `validate_provider_result`, schema resources, and contract fixtures.
- **Downstream callers**: Tasks 3 and 4, `scripts/verify.sh`, and every future provider.
- **Cross-platform bridges**: the JSON contract is the bridge between platform-neutral orchestration
  and ecosystem providers; changing it requires a contract-version migration.
- **Target test coverage threshold**: 100% branch coverage for fail-closed contract decisions and
  100% coverage of every schema rule named in the HLD.

## BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] Valid composite registry produces an ordered plan
  Given a version-one registry with two unique providers supporting epic
  When the registry and requested profile are validated
  Then both providers appear once in provider-ID order
  And no platform file heuristic is consulted

Scenario: [Tier A - Unit] Unknown and missing fields fail closed
  Given a registry omits required and adds a misspelled replacement field
  When version-one validation runs
  Then validation returns BLOCKED findings for both defects
  And no provider is selected

Scenario: [Tier A - Unit] Result state is bound to invocation identity
  Given a result uses a different profile or repository SHA from the invocation
  When result validation runs
  Then the result is rejected as stale or mismatched
  And it cannot transition to accepted

Scenario: [Tier A - Unit] Duplicate inputs remain deterministic under arbitrary order
  Given duplicate provider registrations or duplicate result documents
  When validation receives them in different orders
  Then each run returns the same ordered BLOCKED findings
  And no duplicate is chosen arbitrarily

Scenario: [Tier C - Integration] Missing provider result becomes structured BLOCKED evidence
  Given the execution plan requires two providers
  And only one provider result exists
  When the result set is reconciled with the plan
  Then the missing provider receives a synthetic BLOCKED finding
  And the valid provider result remains available
```

## Test & Verification Checklist

- [x] **RED**: Write failing tests for every schema and semantic rule before validator code.
- [x] **GREEN**: Implement the smallest standard-library validator that passes each test.
- [x] **REFACTOR**: separate parsing, schema-shape, semantic, and identity validation without
      changing findings.
- [x] Test unsupported versions, unknown fields, duplicate IDs, invalid profiles, empty provider
      arrays, empty selections, and unresolved skills.
- [x] Test result identity, SHA drift, malformed checks, coverage thresholds, evidence references,
      duration values, and NOT_APPLICABLE reasons.
- [x] Prove input order cannot change normalized plans or finding order.
- [x] **Tier B**: wire schema parsing and unit tests into `scripts/verify.sh`.
- [x] **Tier C**: validate complete valid and invalid fixture repositories through the public script
      interface.

## Definition of Done

- Version-one contracts are documented and represented by checked-in schemas.
- Validator emits stable machine-readable findings and nonzero exit codes for invalid input.
- Every approved contract boundary has a red-first unit test.
- No validator path mutates project files or guesses a platform.
- Unit tests and the full repository verification pass.

## Dependencies & Blockers

- Blocked by [Task 1](task_1_capture_red_behavioral_baseline.md).
- Blocks [Task 3](task_3_build_result_aggregation_engine.md),
  [Task 4](task_4_refactor_quality_check_orchestrator.md), and
  [Task 5](task_5_add_rust_quality_provider.md).

## References & Rollback

- [HLD contracts and state model](provider_based_quality_check.en.md#contracts-and-state-model)
- [Canonical BDD scenarios](bdd_scenarios.en.md)
- **Rollback**: remove the unconsumed version-one schemas, validator, fixtures, and verification
  hook. No consumer behavior should depend on this task before Task 4.

