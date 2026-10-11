---
id: "task_1_capture_red_behavioral_baseline"
status: "done"
priority: "high"
assignee: null
epic: "provider_based_quality_check"
dueDate: null
created: "2026-10-11T14:22:20+07:00"
modified: "2026-10-11T12:55:19Z"
completedAt: "2026-10-11T12:55:19Z"
labels: ["quality", "evals", "tdd"]
order: "a1"
---

# Task 1: Capture the Red Behavioral Baseline

Epic: [provider_based_quality_check](provider_based_quality_check.en.md)

## Requirement Analysis

Evaluate the current skills against the five adversarial behaviors identified by the approved design
before writing the new provider instructions. Add stable evaluation prompts, expected invariants,
raw baseline outputs, and a concise failure/rationalization record. The baseline must exercise
first-match routing, missing-tool skip-as-pass, profile downgrade, incorrect status precedence, and
stale-SHA approval.

Acceptance requires all five frozen scenarios to be executed and graded, with at least one honestly
demonstrated primary failure. Preserve primary passes as regression controls; do not require every
probe to fail or revise its rubric after observing results.

This task creates evidence only. It must not modify quality orchestration or introduce the desired
answers into the prompts.

## Relevant Files & Context Pointers

- `.devtool/epic/provider_based_quality_check/bdd_scenarios.en.md`
- `evals/protocol.md`
- `evals/provider_based_quality_check/` — new scenarios, baseline outputs, and grading records
- `skills/writing-skills/SKILL.md`
- `skills/quality_check/SKILL.md` — read-only baseline subject

## Design Rationale

The skill-authoring workflow requires a real RED phase. Without it, later passing examples cannot
show that the new skill changed agent behavior. Prompts describe repository facts and pressures but
do not disclose expected implementation wording. A separate rubric grades contract invariants.

Applicable skills: `d3nexus:writing-skills`, `d3nexus:test-driven-development`, and
`d3nexus:task-observer`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: evaluation scenarios and the five named behavioral invariants.
- **Downstream callers**: Tasks 2–5 use observed failures as RED evidence and passes as regression controls.
- **Cross-platform bridges**: none; fixture descriptions may model multiple platforms without
  invoking their toolchains.
- **Target test coverage threshold**: 100% of the five approved pressure scenarios executed and
  graded; no scenario may lack a captured baseline result.

## BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] Happy baseline harness records an agent response
  Given a versioned scenario, an isolated prompt, and an invariant rubric
  When the baseline agent response is captured
  Then the response and grade are stored with the scenario identity
  And another reviewer can reproduce the grading decision

Scenario: [Tier A - Unit] Edge case prevents expected answers leaking into prompts
  Given a pressure scenario intended to test fail-closed behavior
  When its prompt fixture is inspected
  Then it contains repository facts and operating pressure
  But it does not state the expected verdict or prescribed solution

Scenario: [Tier A - Unit] State records RED rather than rewriting history
  Given the current skill violates an invariant
  When the result is graded
  Then the evaluation records the observed failure and rationalization
  And it does not alter the output to resemble a pass

Scenario: [Tier C - Integration] Independent scenarios can run concurrently
  Given scenarios do not share output files or agent state
  When multiple baseline runs execute in parallel
  Then each result is attributed to the correct scenario
  And no result overwrites another

Scenario: [Tier C - Integration] Missing baseline evidence blocks implementation
  Given one approved pressure scenario has no captured result
  When baseline completeness is checked
  Then the task remains incomplete
  And provider skill authoring does not begin
```

## Test & Verification Checklist

- [ ] **RED**: Run all five scenarios against the current quality and lifecycle instructions.
- [ ] Confirm at least one specified primary invariant failure is observable across the five scenarios;
      retain passing scenarios as regression controls and record additional failures without changing
      the rubric after seeing the output.
- [ ] Record the agent's rationalization language for later anti-rationalization guidance.
- [ ] Verify prompts do not contain the expected result or new provider contract.
- [ ] Verify every result records scenario ID, source revision, agent context, output, grade, and
      grader rationale.
- [ ] **Tier B**: add an evaluation-local verification check that every declared baseline scenario has its
      required artifacts.
- [ ] **Tier C**: run the entire baseline suite from a clean checkout and confirm deterministic file
      naming and no source mutation.

## Definition of Done

- Five approved pressure scenarios have complete, frozen, reviewable baseline evidence and grades.
- At least one primary invariant has honest RED evidence; every primary pass remains a regression control.
- Baseline prompts remain independent from the future implementation.
- Failures and rationalizations are summarized for Tasks 4 and 5.
- The evaluation completeness check and targeted RED evidence validation pass; replay leaves a clean checkout unchanged.

For the captured run, acceptance is checked with
`python3 -B evals/provider_based_quality_check/check_baseline.py --require-failure status-precedence`.
It reports 5/5 complete and 1/5 primary failures. The optional `--require-red` all-five diagnostic
remains negative and is not the task acceptance gate.

## Dependencies & Blockers

- No task dependency.
- Blocks [Task 2](task_2_build_provider_contract_validator.md),
  [Task 4](task_4_refactor_quality_check_orchestrator.md), and
  [Task 5](task_5_add_rust_quality_provider.md).

## References & Rollback

- [BDD contract](bdd_scenarios.en.md)
- [Approved source design](2026-10-11-provider-based-quality-check-design.en.md)
- **Rollback**: remove the new evaluation directory. No runtime or skill behavior changes in this
  task.
