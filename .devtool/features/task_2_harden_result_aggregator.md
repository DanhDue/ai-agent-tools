---
id: "task_2_harden_result_aggregator"
status: "todo"
priority: "high"
assignee: null
epic: "mobile_quality_providers_and_contract_hardening"
dueDate: null
created: "2026-10-12T12:30:00Z"
modified: "2026-10-12T12:30:00Z"
completedAt: null
labels: ["aggregator", "precedence", "engine", "python"]
order: "a2"
---

# Task 2: Harden Result Aggregator Engine and Precedence

Epic: [mobile_quality_providers_and_contract_hardening](../epic/mobile_quality_providers_and_contract_hardening/mobile_quality_providers_and_contract_hardening.en.md)

## Requirement Analysis

The result aggregation engine in `skills/quality_check/resources/scripts/aggregate_quality_results.py` reduces multiple validated provider results into a single deterministic Gate 4 verdict.
To ensure mathematical integrity across complex multi-provider and polyglot super-app workspaces:
1. **Strict Precedence Enforcement**:
   $$\text{FAIL} > \text{BLOCKED} > \text{PASS}$$
   If any required provider reports `FAIL`, the overall verdict must remain `FAIL` even when other providers return `BLOCKED`. A blocker must never hide an active product defect.
2. **Missing Provider Detection**: If a required provider from the execution plan is absent from the result set, the aggregator must synthesize an explicit `BLOCKED` entry for that provider.
3. **Contradictory Result Handing**: If an unvalidated or contradictory provider result bypasses the CLI and reaches the aggregator, the aggregator must verify internal check consistency and demote `PASS` to `BLOCKED`.
4. **Deterministic Report Rendering**: The executive report must consistently sort providers and checks alphabetically by `id`, providing transparent evidence links for all defects.

## Relevant Files & Context Pointers

- `skills/quality_check/resources/scripts/aggregate_quality_results.py`: Core aggregation engine.
- `skills/quality_check/resources/scripts/test_aggregate_quality_results.py`: Unittest suite for aggregation logic.
- `skills/quality_check/references/aggregation-contract.md`: Specification for reduction precedence rules.
- `skills/quality_check/references/executive-report-format.md`: Specification for executive report markdown rendering.
- `.devtool/epic/mobile_quality_providers_and_contract_hardening/bdd_scenarios.en.md`: Scenarios under Use Case 4.

## Design Rationale

The aggregation engine represents the final reduction step before Gate 4 certification. It must be resilient against partial inputs and conflicting statuses:
- Input plan JSON is reconciled with all supplied provider result files.
- Each provider is verified against its `required` flag in the plan.
- Provider statuses are reduced:
  - Any `FAIL` in required or optional providers with defects forces overall `FAIL`.
  - If no `FAIL`, any `BLOCKED` in a required provider yields `BLOCKED`.
  - Only when all required providers achieve `PASS` on the identical candidate SHA is the overall verdict granted as `PASS`.
- Markdown report generator renders defect details, blockers, coverage summaries, and exact evidence paths.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/quality_check/resources/scripts/aggregate_quality_results.py`: `aggregate_results()`, `render_markdown_report()`.
  - `skills/quality_check/resources/scripts/test_aggregate_quality_results.py`: Added edge case tests for conflicting statuses and synthetic blockers.
- **Downstream Callers**:
  - `skills/quality_check/SKILL.md` (Step 5).
  - `skills/dev-implementation/SKILL.md` (Phase 4).
  - `skills/pr_review/SKILL.md`.
- **Cross-Platform Bridges**: None (Standard Library Python 3.10+).
- **Target Test Coverage Threshold**: 100% path coverage for status reduction functions.

### BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] Aggregation handles conflicting provider results deterministically
  Given Provider A reports FAIL on unit tests
  And Provider B reports BLOCKED due to a missing optional tool
  When aggregate_quality_results.py reduces the verdicts
  Then overall status is FAIL because FAIL outranks BLOCKED
  And both the test failure and the missing tool blocker remain visible in the report

Scenario: [Tier A - Unit] Missing required provider generates synthetic BLOCKED entry
  Given an execution plan declaring required provider "android-core"
  When aggregate_quality_results.py runs without a result file for "android-core"
  Then the engine synthesizes a BLOCKED provider entry for "android-core"
  And the overall verdict is BLOCKED with finding "missing_provider_result"

Scenario: [Tier A - Unit] Consensus requires 100% PASS across all required providers
  Given Provider A reports PASS
  And Provider B reports PASS
  And both providers verify the identical candidate SHA "3333333"
  When aggregate_quality_results.py reduces the results
  Then overall status is PASS
```

## Test & Verification Checklist

- [ ] **RED**: Add failing unit test cases in `test_aggregate_quality_results.py` asserting that FAIL outranks BLOCKED, missing required providers generate synthetic blockers, and conflicting statuses are surfaced cleanly. Confirm tests fail.
- [ ] **GREEN**: Implement status reduction logic in `aggregate_quality_results.py` ensuring strict precedence, deterministic provider ordering, and complete executive markdown rendering.
- [ ] **REFACTOR**: Validate report formatting against `executive-report-format.md` standards.
- [ ] **Tier A Verification**: Run `python3 -B skills/quality_check/resources/scripts/test_aggregate_quality_results.py` and confirm 100% pass.

## Definition of Done (DoD)

- All 3 BDD unit scenarios pass with zero regressions.
- Existing 7 unit tests in `test_aggregate_quality_results.py` pass cleanly.
- Aggregation engine output is mathematically deterministic across repeated executions.
- `git status` shows clean, targeted changes.

## Dependencies & Blockers

- Blocked by: [Task 1](task_1_harden_contract_validator.md).
- Blocks: [Task 7](task_7_run_e2e_acceptance_and_release.md).

## References & Rollback

- Reference: [Aggregation Contract](../../../skills/quality_check/references/aggregation-contract.md).
- Rollback: Revert changes to `aggregate_quality_results.py` and its test suite.
