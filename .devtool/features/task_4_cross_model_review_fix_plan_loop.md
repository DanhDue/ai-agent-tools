---
id: "task_4_cross_model_review_fix_plan_loop"
status: "todo"
priority: "high"
assignee: null
epic: "autonomous_lifecycle_runner"
dueDate: null
created: "2026-11-10T19:16:00Z"
modified: "2026-11-10T19:16:00Z"
completedAt: null
labels: ["lifecycle", "cross-model-review", "fix-plan"]
order: "a4"
---

# Task 4: Cross-Model Review Fix Plan Loop and Assistant Evaluator

Epic: [autonomous_lifecycle_runner](../epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md)

## Requirement Analysis

Implement Stage 3 Cross-Model Review fix-and-verify loop with AI Assistant fix plan evaluation in `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`:
1. Implement `LifecycleRunner.step_cross_model_review`:
   - Runs `run_external_review.py run --kind code --epic-dir <epic> --base <base> --auto-quota`.
   - Evaluates Circuit Breakers: halts with `CIRCUIT_BREAKER_HALT (FIX_LOOP)` if a finding reoccurs on an already-fixed file path, or `CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)` if Round 3 ends with Critical findings unresolved.
   - Fix plan drafting: when review findings require changes, dispatches the AI Programmer (`--model <programmer-model>` default `gemini-3.8-flash --effort high --mode auto`) to draft `.devtool/epic/<epic>/fix_plan_round<N>.md`.
   - Fix plan evaluation (`evaluate_programmer_fix_plan`): dispatches the AI Assistant to inspect the fix plan against the approved HLD and emit one of three verdicts: `APPROVED`, `ADJUSTED`, or `CRITICAL_CONFLICT`.
   - Critical conflict halt: if the Assistant detects an unapproved architectural change or contract violation (`CRITICAL_CONFLICT`), the pipeline halts immediately and alerts the Human Architect.
   - Automated fix application: if `APPROVED` or `ADJUSTED`, the AI Programmer applies the fixes, the runner commits the code fixes (`[AUTONOMOUS_LIFECYCLE_RUNNER] Apply code fixes for Cross-Model Review round N`), records decision cells (`fixed in <sha>`) in `review_results.md`, commits the decisions (`[AUTONOMOUS_LIFECYCLE_RUNNER] Record review decisions for round N`), executes Gate 4 in full on the clean candidate SHA (passing `run_external_review.py check`), and advances to the next review round (Round N+1, up to max 3 rounds) or completes Stage 3 if converged.
2. Implement unit and integration tests in `tests/test_lifecycle_runner.py` covering `ALR-HP-04`, `ALR-EC-03`, `ALR-FR-02`, and `ALR-FR-04`.

## Files

Allowed files:
- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (new)
- `tests/test_lifecycle_runner.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/run_external_review.py` — review execution and triage
- `.devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md` — Module Contracts
- `.agents/quality/python-quality.json` — registered capabilities

## Design Rationale

During Cross-Model Review, the Human Architect should not be interrupted for routine code fixes that align with the approved design. Having the AI Assistant evaluate the Programmer's fix plan provides architectural supervision: safe fixes proceed automatically, while architectural deviations trigger an immediate `CRITICAL_CONFLICT` halt. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`LifecycleRunner.step_cross_model_review`, `LifecycleRunner.evaluate_programmer_fix_plan`).
- **Downstream callers**: Stage 3 review convergence loop.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: 100% of fix plan evaluation branches and circuit breakers.

### BDD SCENARIOS

Covers: ALR-HP-04, ALR-EC-03, ALR-FR-02, ALR-FR-04

```gherkin
Scenario: [ALR-HP-04] [Tier C - Integration] AI Assistant approves AI Programmer fix plan in Cross-Model Review without Human stop

Given Cross-Model Review returns review findings requiring code adjustments in Round 1
When the AI Programmer drafts a proposed fix plan in fix_plan_round1.md
Then the AI Assistant evaluates the fix plan against the approved HLD and emits verdict "APPROVED"
And the AI Programmer applies the approved code changes and re-runs Phase 4 Gate 4
And the cycle proceeds to Round 2 without prompting the Human Architect for intermediate confirmation

Scenario: [ALR-EC-03] [Tier C - Integration] AI Assistant adjusts AI Programmer fix plan without rejecting

Given the AI Programmer proposes a fix plan that omits a required edge-case assertion
When the AI Assistant reviews the fix plan in Cross-Model Review
Then the Assistant returns verdict "ADJUSTED" along with the amended fix plan text
And the AI Programmer receives the adjusted plan, applies the combined patch, and triggers Gate 4 re-verification

Scenario: [ALR-FR-02] [Tier C - Integration] Circuit Breaker halts immediately on repeated fix loop

Given a finding in Round N touches the identical file path previously marked as fixed in Round N-1
When evaluate_circuit_breakers evaluates the round comparison
Then the runner triggers CIRCUIT_BREAKER_HALT (FIX_LOOP)
And the pipeline stops calling tools and presents the recurrent finding to the Human Architect

Scenario: [ALR-FR-04] [Tier C - Integration] AI Assistant rejects fix plan with CRITICAL_CONFLICT and halts pipeline

Given the AI Programmer drafts a fix plan that attempts to unilaterally revert an approved architectural decision
When the AI Assistant evaluates the fix plan
Then the Assistant returns verdict "CRITICAL_CONFLICT" with detailed rationale
And lifecycle_runner.py halts immediately, preventing the Programmer from modifying source code
And an alert is displayed to the Human Architect highlighting the architectural conflict
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest tests/test_lifecycle_runner.py -k test_alr_hp_04` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest tests/test_lifecycle_runner.py -k test_alr_hp_04` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest tests/test_lifecycle_runner.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_lifecycle_runner.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_lifecycle_runner.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_4.xml tests/test_lifecycle_runner.py` | exit 0; results build/test-results/task_4.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Fix plan verdict cannot be parsed from the Assistant output.

## Decisions Already Made

- Cross-Model Review invocation uses `run_external_review.py run --kind code --epic-dir <epic> --base <base> --auto-quota` and evaluates `run_external_review.py triage`.
- Fix plan file is stored at `.devtool/epic/<epic>/fix_plan_round<N>.md`.
- Assistant evaluation outputs one verdict token on the first line: `APPROVED`, `ADJUSTED`, or `CRITICAL_CONFLICT`.
- Review loop return path: after fixes are applied, the runner commits the code fixes, writes decision cells (`fixed in <sha>`) into `review_results.md`, commits the decisions, and runs Gate 4 in full. Because decisions are recorded and committed, `run_external_review.py check` passes and certifies the clean candidate commit.
- Clean working tree discipline: code fixes and review decisions are committed before invoking subsequent review rounds.

## Definition of Done

- Scenarios ALR-HP-04, ALR-EC-03, ALR-FR-02, ALR-FR-04 are covered and pass in the test suite. (V2, V3, V6)
- Python quality checks (lint and type check) pass cleanly. (V4, V5)
- Assistant evaluation cleanly prevents unauthorized design reversions. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 1](task_1_pipeline_state_machine_and_probing.md), [Task 2](task_2_subprocess_dispatcher_and_headless_agy.md), and [Task 3](task_3_principal_review_automation_and_checkpoint.md).
- Blocks [Task 5](task_5_orchestrator_cli_and_governance_rules.md).

## References & Rollback

- [Epic HLD](../epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md), Module Contracts.
- **Rollback**: Revert task commit; fix plan evaluation logic removed.
