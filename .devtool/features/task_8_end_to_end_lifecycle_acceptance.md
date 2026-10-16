---
id: "task_8_end_to_end_lifecycle_acceptance"
status: "done"
priority: "high"
assignee: null
epic: "verifiable_task_handoff"
dueDate: null
created: "2026-10-16T06:53:44Z"
modified: "2026-10-16T08:25:24Z"
completedAt: "2026-10-16T08:25:24Z"
labels: ["tests", "acceptance"]
order: "a8"
---

# Task 8: End-to-end lifecycle acceptance

Epic: [verifiable_task_handoff](../epic/verifiable_task_handoff/verifiable_task_handoff.en.md)

## Requirement Analysis

The final Tier C task. Prove one task can travel the whole lifecycle on a throwaway repository, and
run this epic's own Gate 4 machinery on itself. Authority: source spec section 16 (Testing) and HLD
section 5.

### scripts/test_verifiable_handoff.py (new)

`test_vth_hp_11_design_to_audit_every_step_exits_0` builds a throwaway git repository on a `main`
branch with:

- `.devtool/epic/demo/demo.en.md`: `Integration test roots: tests/`,
  `Protected paths: .agents/quality/**`,
  `Integration results: python3 <kit>/scripts/run_unittest_junit.py --junitxml build/r.xml tests/test_demo.py -> build/r.xml`,
  and a `## Verification Environment` section;
- `.devtool/epic/demo/bdd_scenarios.en.md` with one scenario, `DEMO-HP-01`;
- `.gitignore` holding `build/`;
- a task mirror `.devtool/epic/demo/task_1_demo.md` and its copy in `.devtool/features/`, with all
  five contract sections, `Covers: DEMO-HP-01`, a RED row that fails before `feature.txt` exists, a
  GREEN row, and a TIER-C row running the kit's JUnit runner on `tests/test_demo.py`, whose
  `test_demo_hp_01_…` passes once `feature.txt` exists.

Then, branching `epic/demo` from `main` and running every script of the kit as a subprocess, in this
order: `check_task_contract.py --design`, `check_bdd_traceability.py plan`,
`run_task_checks.py red`, create `feature.txt`, `run_task_checks.py verify`,
`sync_task_status.py task task_1_demo done`, commit the code, the task files and the evidence,
`audit_epic.py --epic-dir demo --base main`. Every command must exit 0.

### Also

`scripts/verify.sh`, section 11: add `python3 -m unittest scripts/test_verifiable_handoff.py || FAILED=1`.

## Files

Allowed files:
- `scripts/test_verifiable_handoff.py` (new)
- `scripts/verify.sh`

Read-only context:
- `scripts/test_lifecycle_signals.py` — style for subprocess tests over throwaway repositories
- `.devtool/epic/verifiable_task_handoff/verifiable_task_handoff.en.md` — section 5, the Integration results line V3 runs

## Design Rationale

- The test calls the scripts exactly as the skills tell an agent to, so a broken hand-off between them
  fails here.
- V3 to V7 run this epic's own Gate 4 machinery on its own branch: dogfood, not a substitute for
  Phase 4.
- Applicable skills: `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: the new test file and `scripts/verify.sh`.
- **Downstream callers**: none.
- **Cross-platform bridges**: none.
- **Target test coverage threshold**: every script of the epic invoked once, in lifecycle order.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: VTH-HP-11

```gherkin
Scenario: [VTH-HP-11] [Tier C - Integration] Design to audit, every step exits 0
  Given a throwaway git repository with an HLD and one compliant task file
  When check_task_contract.py --design and plan run
  And run_task_checks.py red runs, the change is made and run_task_checks.py verify runs
  And sync_task_status.py task done runs and the task is committed with its evidence
  And audit_epic.py runs against the base branch
  Then every command exits 0
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | GREEN | `python3 -m unittest scripts/test_verifiable_handoff.py` | exit 0; contains "OK" | — |
| V2 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
| V3 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/vth.xml skills/dev-implementation/resources/scripts/test_run_task_checks.py skills/dev-implementation/resources/scripts/test_result_reports.py skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py skills/dev-implementation/resources/scripts/test_check_task_contract.py skills/dev-implementation/resources/scripts/test_sync_task_status.py skills/dev-implementation/resources/scripts/test_audit_epic.py skills/dev-implementation/resources/scripts/test_run_external_review.py scripts/test_verifiable_handoff_text.py scripts/test_verifiable_handoff.py` | exit 0; results build/test-results/vth.xml | — |
| V4 | TIER-C | `python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py tests --scenarios .devtool/epic/verifiable_task_handoff/bdd_scenarios.en.md --roots skills/dev-implementation/resources/scripts/ scripts/ --results build/test-results/vth.xml` | exit 0; contains "Result: 41/41 covered — PASS" | — |
| V5 | TIER-C | `python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py plan --scenarios .devtool/epic/verifiable_task_handoff/bdd_scenarios.en.md --tasks .devtool/epic/verifiable_task_handoff/task_*.md` | exit 0; contains "Result: 41/41 covered — PASS" | — |
| V6 | TIER-C | `python3 skills/dev-implementation/resources/scripts/check_task_contract.py --hld .devtool/epic/verifiable_task_handoff/verifiable_task_handoff.en.md --tasks .devtool/epic/verifiable_task_handoff/task_*.md` | exit 0; contains "PASS" | — |
| V7 | TIER-C | `python3 skills/dev-implementation/resources/scripts/audit_epic.py --epic-dir verifiable_task_handoff --base main` | exit 0; contains "Result: PASS" | — |

RED: n/a — acceptance task: the behaviour under test exists after Tasks 1 to 7, so the new test is expected to pass on its first run.

## Definition of Done

- One compliant task travels design, red, verify, done, commit and audit with every script exiting 0 (V1).
- All 41 scenarios of this epic pass in one JUnit report, the plan and contract checks pass on this epic's own tasks, and its audit passes (V3, V4, V5, V6, V7).
- `scripts/verify.sh` passes with the new test file wired in (V2).
- A small fixture epic, packaged and handed to a lower-tier model, reaches `done` only through recorded evidence (Gate 5).

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Any script needs a change for the end-to-end test to pass; report the failure and the script
  instead of changing it in this task.

## Decisions Already Made

- This task changes no script; a defect it finds goes back to the task that owns the script.
- The fixture repository uses the `DEMO-` prefix; only the test method name carries `VTH-HP-11`.
- `main` is this repository's base branch.

## Dependencies & Blockers

- Blocked by [Task 1](task_1_verification_table_parser_and_evidence_recorder.md), [Task 2](task_2_test_result_reports_and_result_based_traceability.md), [Task 3](task_3_design_time_task_contract_check.md), [Task 4](task_4_done_gate_and_evidence_status.md), [Task 5](task_5_gate_4_epic_audit.md), [Task 6](task_6_cross_model_review_runner.md), [Task 7](task_7_skill_prompt_and_reference_text.md)

## References & Rollback

- Source spec section 16; HLD section 5.
- Rollback: revert this task's commit; it adds only a test.
