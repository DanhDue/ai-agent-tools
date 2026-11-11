---
id: "task_3_principal_review_automation_and_checkpoint"
status: "done"
priority: "high"
assignee: null
epic: "autonomous_lifecycle_runner"
dueDate: null
created: "2026-11-10T19:16:00Z"
modified: "2026-11-11T00:05:18Z"
completedAt: "2026-11-11T00:05:18Z"
labels: ["lifecycle", "principal-review", "human-checkpoint"]
order: "a3"
---

# Task 3: Principal Review Automation and Human Checkpoint

Epic: [autonomous_lifecycle_runner](autonomous_lifecycle_runner.en.md)

## Requirement Analysis

Implement Stage 2 Principal Review automation with the mandatory Human confirmation checkpoint in `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`:
1. Implement `LifecycleRunner.step_principal_review`:
   - Triggers `run_external_review.py run --kind principal --epic-dir <epic> --base <base> --auto-quota` with provider auto-quota prioritization.
   - Evaluates triage results and Action from `run_external_review.py triage`:
     - `AUTO_PASS_CLEAN`: 0 findings -> directly transitions to `StageName.IMPLEMENTATION`.
     - `AUTO_PASS_FINAL_MINOR_SWEEP`: 0 Critical/Important, only Minor -> AI Assistant executes single minor fix sweep, commits revisions, records decisions, runs `package_epic.py <epic> --revise`, and advances to Stage 3 without an additional external review round.
     - `AUTO_FIX_ELIGIBLE`: AI Assistant auto-applies aligned revisions, commits them, records decision cells (`fixed in <sha>`) in `principal_review.md`, commits decisions, executes `package_epic.py <epic> --revise`, commits handoff re-anchor, and advances to the next review round.
     - Human stop condition: if findings involve high-risk critical issues, business/domain requirement conflicts, unaligned source conflicts, or `SHARED_CONTRACT_CONFLICT`, the runner transitions to `StageName.AWAITING_PRINCIPAL_CONFIRMATION`, writes `.devtool/epic/<epic>/principal_fix_proposal_round<N>.md`, and prompts the Human Architect (`prompt_human_principal_fixes`) or halts for `--confirm-fixes`.
     - `AUTO_PASS_FINAL_SWEEP`: on Round 3 with 0 Critical, executes final fix sweep, commits, records decisions, runs `package_epic.py --revise`, and advances to Stage 3 without a 4th round.
     - `CIRCUIT_BREAKER_HALT`: halts immediately on `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, or `MAX_ROUNDS_CRITICAL_REMAINING`.
2. Implement unit and integration tests in `tests/test_lifecycle_runner.py` covering `ALR-HP-03`, `ALR-EC-01`, `ALR-EC-02`, and `ALR-FR-01`.

## Files

Allowed files:
- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (new)
- `tests/test_lifecycle_runner.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/run_external_review.py` — external review runner and triage
- `skills/dev-implementation/resources/scripts/package_epic.py` — epic packaging script
- `scripts/resume_context.py` — gate approval recording
- `.devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md` — Module Contracts
- `.agents/quality/python-quality.json` — registered capabilities

## Design Rationale

While the overall lifecycle is autonomous, architectural design changes identified during Principal Review must be vetted by the Human Architect before modifying HLD specifications. Halting to batch-confirm fixes prevents architectural drift while eliminating unnecessary intermediate pauses on zero-finding passes. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`LifecycleRunner.step_principal_review`, `LifecycleRunner.prompt_human_principal_fixes`, `LifecycleRunner.evaluate_circuit_breakers`).
- **Downstream callers**: Runner pipeline loop.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: 100% of Principal Review state transitions, circuit breakers, and confirmation branches.

### BDD SCENARIOS

Covers: ALR-HP-03, ALR-EC-01, ALR-EC-02, ALR-FR-01

```gherkin
Scenario: [ALR-HP-03] [Tier C - Integration] AI Assistant auto-applies aligned Principal Review fixes and prompts Human confirmation only on critical or domain conflicts

Given Principal Review returns findings on candidate HLD specifications
When the AI Assistant triages the findings in step_principal_review
Then aligned technical findings are auto-applied, committed, and packaged via package_epic.py --revise without human interruption
And lifecycle_runner.py transitions to AWAITING_PRINCIPAL_CONFIRMATION only if findings involve critical risks, business requirement conflicts, or SHARED_CONTRACT_CONFLICT
And upon Human confirmation of the conflict proposal, the pipeline resumes and advances to the next review round

Scenario: [ALR-EC-01] [Tier C - Integration] Zero findings in Principal Review bypasses Human confirmation

Given Principal Review completes Round 1 with verdict PASS and 0 findings
When step_principal_review processes the review results
Then the runner logs "AUTO_PASS_CLEAN: 0 findings"
And the runner bypasses the Human confirmation prompt completely
And the pipeline state advances directly to Stage 3 Implementation

Scenario: [ALR-EC-02] [Tier C - Integration] Minor-only findings in Principal Review swept in single pass without Human halt

Given Principal Review Round 1 returns 0 Critical, 0 Important, and 2 Minor formatting findings
When step_principal_review evaluates the triage report
Then the runner triggers AUTO_PASS_FINAL_MINOR_SWEEP
And the Minor findings are swept, committed, and packaged in a single pass without stopping for Human confirmation
And the pipeline advances directly to Stage 3 Implementation

Scenario: [ALR-FR-01] [Tier C - Integration] Circuit Breaker halts immediately on Shared Contract conflict

Given an external review round reports a finding conflicting with shared-contracts/
When evaluate_circuit_breakers inspects the triage report
Then the runner triggers CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)
And the pipeline halts immediately, preserving all logs and state
And the console displays the executive warning banner instructing the developer to consult the Human Architect
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest tests/test_lifecycle_runner.py -k test_alr_hp_03` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest tests/test_lifecycle_runner.py -k test_alr_hp_03` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest tests/test_lifecycle_runner.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_lifecycle_runner.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_lifecycle_runner.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_3.xml tests/test_lifecycle_runner.py` | exit 0; results build/test-results/task_3.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- An unhandled exception occurs while running `run_external_review.py triage`.

## Decisions Already Made

- Principal Review invocation uses `run_external_review.py run --kind principal --epic-dir <epic> --base <base> --auto-quota` and evaluates `run_external_review.py triage`.
- Principal Review is capped at 3 rounds.
- Auto-Triage Gate actions map to deterministic transitions: `AUTO_PASS_CLEAN` advances to implementation; `AUTO_PASS_FINAL_MINOR_SWEEP` sweeps minor fixes and advances to implementation without an extra review round; `AUTO_FIX_ELIGIBLE` auto-applies aligned revisions; `AUTO_PASS_FINAL_SWEEP` executes final design-anchored sweep and finishes Stage 2.
- The runner transitions to `AWAITING_PRINCIPAL_CONFIRMATION` only when findings involve high-risk critical issues, business/domain requirement conflicts, unaligned source conflicts, or `SHARED_CONTRACT_CONFLICT`.
- Clean working tree discipline: edits, decision records (`fixed in <sha>` in `principal_review.md`), and `package_epic.py <epic> --revise` are committed in sequence before dispatching the next review round.

## Definition of Done

- Scenarios ALR-HP-03, ALR-EC-01, ALR-EC-02, ALR-FR-01 are covered and pass in the test suite. (V2, V3, V6)
- Python quality checks (lint and type check) pass cleanly. (V4, V5)
- Human confirmation prompt and circuit breaker halts function deterministically. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 1](task_1_pipeline_state_machine_and_probing.md) and [Task 2](task_2_subprocess_dispatcher_and_headless_agy.md).
- Blocks [Task 4](task_4_cross_model_review_fix_plan_loop.md) and [Task 5](task_5_orchestrator_cli_and_governance_rules.md).

## References & Rollback

- [Epic HLD](autonomous_lifecycle_runner.en.md), Module Contracts.
- **Rollback**: Revert task commit; Principal Review integration removed.
