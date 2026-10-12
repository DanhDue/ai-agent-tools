---
id: "task_7_run_e2e_acceptance_and_release"
status: "done"
priority: "high"
assignee: null
epic: "mobile_quality_providers_and_contract_hardening"
dueDate: null
created: "2026-10-12T12:30:00Z"
modified: "2026-10-12T06:00:34Z"
completedAt: "2026-10-12T06:00:34Z"
labels: ["e2e", "acceptance", "release", "quality_check"]
order: "a7"
---

# Task 7: Run End-to-End Acceptance and Release v1.6.0

Epic: [mobile_quality_providers_and_contract_hardening](mobile_quality_providers_and_contract_hardening.en.md)

## Requirement Analysis

Conduct end-to-end multi-provider acceptance testing, regression suite execution, and release preparation for `d3nexus v1.6.0`:
1. **End-to-End Simulation Test Suite**:
   - Create comprehensive E2E test `skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`.
   - Simulate complete runs across 4 distinct project structures:
     - Pure Rust codebase (`rust-quality.json`).
     - Pure Flutter codebase (`flutter-quality.json` modeled after `bloc_digital_wallet`).
     - Pure Android codebase (`android-quality.json` modeled after `android_digital_wallet`).
     - Pure iOS codebase (`ios-quality.json` modeled after `ios_digital_wallet`).
     - Composite Polyglot repository (Rust + Android).
2. **False-PASS Guard Verification (F1–F3)**:
   - Prove via integration tests that an exit code 0 run with a failing check or below-threshold coverage is blocked with `CONTRACT_VIOLATION`.
   - Prove that `reconcile_quality_results.py` validates all result files and rejects stale candidate SHAs.
   - Prove that capability manifests with empty command arrays `[]` are rejected.
3. **Repository Verification**:
   - Execute root verification harness `./scripts/verify.sh` ensuring all test suites and linters pass cleanly.
4. **Version Bump & Distribution**:
   - Update `plugin.json` to version `1.6.0`.
   - Update `CHANGELOG.md` with mobile providers, contract hardening, and scaffolding additions.

## Relevant Files & Context Pointers

- Target Test: `skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`.
- Harness Script: `./scripts/verify.sh`.
- Plugin Manifest: `plugin.json`.
- Release Notes: `CHANGELOG.md`.
- Canonical Template References:
  - `digital_wallet/bloc_digital_wallet`
  - `digital_wallet/android_digital_wallet`
  - `digital_wallet/ios_digital_wallet`

## Design Rationale

Before releasing `d3nexus 1.6.0`, we must have automated proof that all 4 providers work in harmony with the aggregator, that contract validator guarantees are strictly enforced, and that no legacy monolithic code paths remain.
- Multi-process simulation harnesses.
- Standard Library Python 3.10+ execution.
- Deterministic verification without external network access.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`: E2E test harness.
  - `plugin.json`: Version bump `1.5.0` -> `1.6.0`.
- **Downstream Callers**: All AI agents and developers across all supported platforms.
- **Cross-Platform Bridges**: Verifies all provider outputs on macOS and Linux.
- **Target Test Coverage Threshold**: 100% acceptance suite pass rate.

### BDD SCENARIOS

```gherkin
Scenario: [Tier C - Integration] Execute end-to-end multi-platform quality aggregation
  Given mock workspaces for Flutter, Android, iOS, and Rust
  When quality_check executes across each workspace
  Then all provider manifests pass validation
  And aggregated results correctly summarize status and coverage
  And zero False-PASS conditions are permitted

Scenario: [Tier A - Unit] Verify plugin version alignment
  Given plugin.json
  When inspect version attribute
  Then version equals "1.6.0"
  And all registered provider skills are present in the plugin manifest
```

## Test & Verification Checklist

- [x] **RED**: Create `test_quality_provider_acceptance.py` asserting multi-provider aggregation and False-PASS rejection. Confirm failures before wiring.
- [x] **GREEN**: Wire full aggregation simulation, update `plugin.json` and release metadata.
- [x] **REFACTOR**: Clean up test fixtures and ensure atomic temporary directory teardown.
- [x] **Tier A Verification**: Run `python3 -B skills/quality_check/resources/scripts/test_quality_provider_acceptance.py` and confirm 100% pass.
- [x] **Tier B Verification**: Run `./scripts/verify.sh` and confirm all 13+ suite checks PASS.
- [x] **Tier C Verification**: Verify `git diff` shows clean version bump and documentation alignment.

## Definition of Done (DoD)

- `test_quality_provider_acceptance.py` created and passing 100%.
- `./scripts/verify.sh` passes 100% without warnings or failures.
- `plugin.json` bumped to `1.6.0` with all new skills registered.
- Ready for Gate 4 / Gate 5 review.

## Dependencies & Blockers

- Blocked by: [Task 1](task_1_harden_contract_validator.md), [Task 2](task_2_harden_result_aggregator.md), [Task 3](task_3_build_flutter_quality_provider.md), [Task 4](task_4_build_android_quality_provider.md), [Task 5](task_5_build_ios_quality_provider.md), [Task 6](task_6_build_scaffolding_skill.md).
- Blocks: Epic Completion (Gate 4 & Gate 5).

## References & Rollback

- Reference: [Acceptance Criteria in HLD §6](mobile_quality_providers_and_contract_hardening.en.md#6-testing-strategy).
- Rollback: Revert version bump and acceptance test script.
