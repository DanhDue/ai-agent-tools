---
id: "task_1_harden_contract_validator"
status: "done"
priority: "high"
assignee: null
epic: "mobile_quality_providers_and_contract_hardening"
dueDate: null
created: "2026-10-12T12:30:00Z"
modified: "2026-10-12T05:41:14Z"
completedAt: "2026-10-12T05:41:14Z"
labels: ["validator", "contracts", "anti-false-pass", "python"]
order: "a1"
---

# Task 1: Harden Quality Contract Validator and Reconcile Engine

Epic: [mobile_quality_providers_and_contract_hardening](../epic/mobile_quality_providers_and_contract_hardening/mobile_quality_providers_and_contract_hardening.en.md)

## Requirement Analysis

The current contract validator in `skills/quality_check/resources/scripts/validate_quality_contract.py` possesses critical vulnerabilities identified during integration review (F1–F3 / C1–C7):
1. **False-PASS Vulnerability (C4)**: A provider result reporting top-level `status: PASS` while containing individual checks with `status: FAIL` or `measured` coverage below configured `threshold` is accepted as valid. This allows defective code to pass Gate 4.
2. **Reconciliation Bypass (C3)**: The `reconcile` CLI subcommand does not invoke schema or internal consistency validation on individual result files, and fails to reject stale `started_head` or `finished_head` commits that diverge from the requested SHA.
3. **Lenient Capability Manifests (C1, C2)**: Manifest validators accept empty profile capability mappings, empty command arrays `[]`, and duplicate capability identifiers.

This task hardens `validate_quality_contract.py` and its test suite to strictly enforce internal consistency, reject any contradictory provider results, validate execution plans against actual results, and mandate positive proof for all required capabilities.

## Relevant Files & Context Pointers

- `skills/quality_check/resources/scripts/validate_quality_contract.py`: Core contract validation engine and CLI.
- `skills/quality_check/resources/scripts/test_validate_quality_contract.py`: Comprehensive unittest suite for contract validation.
- `skills/quality_check/resources/schemas/provider-result.schema.json`: Schema specification for provider result documents.
- `skills/quality_check/resources/schemas/check-quality.schema.json`: Schema specification for project provider registries.
- `.devtool/epic/mobile_quality_providers_and_contract_hardening/bdd_scenarios.en.md`: Scenarios under Use Case 4.

## Design Rationale

Validation follows strict fail-closed contract governance (Saltzer & Schroeder). Rather than trusting top-level status strings emitted by providers, `validate_quality_contract.py` performs deep structural and semantic audits:
- If `status == "PASS"`, every check in `checks` must have `status == "PASS"`. Any check with `status == "FAIL"` or `status == "BLOCKED"` triggers a `CONTRACT_VIOLATION` validation error.
- If `coverage.line` or `coverage.branch` declares a `threshold` and `measured < threshold`, top-level status cannot be `PASS`. Any contradictory PASS result is converted to `COVERAGE_DEFICIT`.
- During reconciliation, every planned required provider must have exactly one corresponding result file. Stale SHA values trigger immediate `SHA_MISMATCH` rejection.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/quality_check/resources/scripts/validate_quality_contract.py`: `validate_result()`, `validate_reconciliation()`, `validate_capability_manifest()`.
  - `skills/quality_check/resources/scripts/test_validate_quality_contract.py`: Added negative test cases for False-PASS, stale SHA, and empty capability arrays.
- **Downstream Callers**:
  - `skills/quality_check/SKILL.md` (Step 1, Step 4).
  - `skills/quality_check/resources/scripts/aggregate_quality_results.py`.
- **Cross-Platform Bridges**: None (Standard Library Python 3.10+).
- **Target Test Coverage Threshold**: 100% path coverage across all validation branches.

### BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] Anti-False-PASS: Provider PASS with contained check FAIL is strictly rejected
  Given a provider result declaring top-level status="PASS"
  But one check inside checks array reports status="FAIL"
  When validate_quality_contract.py validates the result document
  Then validation rejects the document with error "CONTRACT_VIOLATION"
  And exit code is non-zero

Scenario: [Tier A - Unit] Anti-False-PASS: Provider PASS with sub-threshold coverage is strictly rejected
  Given a provider result declaring top-level status="PASS"
  And coverage threshold is configured as 0.85
  But measured coverage is reported as 0.10
  When validate_quality_contract.py validates the result document
  Then validation rejects the document with error "COVERAGE_DEFICIT"
  And exit code is non-zero

Scenario: [Tier A - Unit] Reconcile CLI rejects stale commit SHA in result documents
  Given an execution plan targeting candidate SHA "aaaaaaa"
  When reconcile is invoked with a result document containing started_head="bbbbbbb"
  Then reconcile halts with error "SHA_MISMATCH" and non-zero exit code

Scenario: [Tier A - Unit] Capability schema rejects empty command array
  Given a capability JSON declaring capability "test" with an empty command array []
  When validate_quality_contract.py validates the capability manifest
  Then validation halts with schema error "COMMAND_ARRAY_EMPTY"
```

## Test & Verification Checklist

- [x] **RED**: Add failing unit test cases in `test_validate_quality_contract.py` asserting rejection of top-level PASS with failing checks, sub-threshold coverage, stale reconcile SHAs, and empty command arrays. Confirm tests fail.
- [x] **GREEN**: Implement validation logic in `validate_quality_contract.py` to enforce consistency, check coverage thresholds, validate result schemas inside reconcile CLI, and reject empty capability arrays.
- [x] **REFACTOR**: Ensure clean error formatting, deterministic JSON error reporting, and zero external dependencies outside standard library.
- [x] **Tier A Verification**: Run `python3 -B skills/quality_check/resources/scripts/test_validate_quality_contract.py` and confirm 100% pass.

## Definition of Done (DoD)

- All 4 BDD unit scenarios pass with zero regressions.
- Existing 17 unit tests in `test_validate_quality_contract.py` pass cleanly.
- `python3 -B skills/quality_check/resources/scripts/validate_quality_contract.py` exits with non-zero on contradictory results.
- `git status` shows clean, targeted changes.

## Dependencies & Blockers

- Blocked by: None (First task in epic).
- Blocks: [Task 2](task_2_harden_result_aggregator.md), [Task 7](task_7_run_e2e_acceptance_and_release.md).

## References & Rollback

- Reference: [Acceptance Criteria C1–C7 in quality_check_comparison.vi.md](../../../D3Nexus/.devtool/epic/rust_quality_provider_adoption/quality_check_comparison.vi.md).
- Rollback: Revert modifications to `validate_quality_contract.py` and test file.
