---
id: "task_4_done_gate_and_evidence_status"
status: "done"
priority: "high"
assignee: null
epic: "verifiable_task_handoff"
dueDate: null
created: "2026-10-16T06:53:44Z"
modified: "2026-10-16T07:51:35Z"
completedAt: "2026-10-16T07:51:35Z"
labels: ["scripts", "gate"]
order: "a4"
---

# Task 4: Done gate and evidence status

Epic: [verifiable_task_handoff](../epic/verifiable_task_handoff/verifiable_task_handoff.en.md)

## Requirement Analysis

Make `sync_task_status.py task <id> done` refuse a task of a code epic unless its recorded evidence
matches, and give the recorder a read-only `status` command that reports the same verdict.
Authority: source spec section 9, and HLD section 4.5 item 1.

### evaluate_done_gate (task_contract.py)

`evaluate_done_gate(task_file: Path) -> list[str]` returns one message per failed condition, and an
empty list when the gate passes. `task_file` is the task's mirror; the evidence is read from
`epic_layout(task_file).evidence` in the same checkout. Messages start `condition <n>: `:

1. The evidence file is missing; or the `red` run is missing although the task has RED rows; or the
   `verify` run is missing. The missing-file message says:
   `evidence <path> not found in this checkout — record it with run_task_checks.py and run the done gate in the epic worktree`.
2. A row of the current Verification table has no `PASS` result in the evidence, or its recorded
   `command` or `expect` differs from the table (`row V2: recorded expect differs from the table`).
3. Any recorded row is `BLOCKED`.
4. The `verify` run's `tree` differs from `fingerprint(root)[0]`.
5. For a task with RED rows: the `red` run's `tree` equals the `verify` run's `tree`, or `red`
   `finished` later than `verify` `started`.
6. For each identifier on the task's `Covers:` line, `verdicts` (from `result_reports.py`) over the
   cases of every `TIER-C` row's `results.digest` must pass; each failure is named.
7. The `SCOPE` row is not `PASS`.

`is_code_epic(hld_path) -> bool`: the HLD has a line starting with `Integration test roots:`.

### sync_task_status.py task <id> done

Before `sync_task` writes anything for the status `done`:

1. Root is `git rev-parse --show-toplevel` of the working directory.
2. Read `epic:` from this checkout's `.devtool/features/<id>.md`, or `.devtool/features/done/<id>.md`,
   and find the epic directory with the existing `find_epic_dir_for_slug(root, slug)`.
3. If the overview `.devtool/epic/<epic_dir>/<epic_dir>.en.md` is not a code epic (`is_code_epic` is
   false), or no checkout holds the task, the gate does not apply and the command behaves as today.
   When this checkout lacks the task but another checkout holds it under a code epic, refuse with
   `run the done gate in the checkout that holds the task and its evidence (the epic worktree)`.
4. If the mirror `.devtool/epic/<epic_dir>/<id>.md` has no `## Verification` section, refuse with
   `retrofit required: <mirror> has no Verification section — retrofit it through dev-designer's Updating an Existing Epic`.
5. Otherwise call `evaluate_done_gate(mirror)`. On failures, print each to stderr after
   `refused: <id> cannot be marked done`, exit 1 and write nothing in any checkout.

Every other status, and every other subcommand, is unchanged. The existing unit tests call
`sync_task()` directly and must keep passing.

### run_task_checks.py status

```bash
python3 skills/dev-implementation/resources/scripts/run_task_checks.py status <task mirror>
```

Read-only. Print each recorded run (kind, `head`, `tree`, rows with outcomes), then either
`done gate: PASS` or `done gate: FAIL` followed by the messages of `evaluate_done_gate`. Exit 0 or
1 accordingly; 2 for usage errors.

### Also

`scripts/verify.sh`, section 11: add
`python3 -m unittest skills/dev-implementation/resources/scripts/test_sync_task_status.py || FAILED=1`,
which `verify.sh` does not run today.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/task_contract.py`
- `skills/dev-implementation/resources/scripts/run_task_checks.py`
- `skills/dev-implementation/resources/scripts/test_run_task_checks.py`
- `skills/dev-implementation/resources/scripts/sync_task_status.py`
- `skills/dev-implementation/resources/scripts/test_sync_task_status.py`
- `scripts/verify.sh`

Read-only context:
- `skills/dev-implementation/resources/scripts/result_reports.py` — `verdicts` from Task 2
- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` — `covers_of`
- `skills/doc-implementation/SKILL.md` — calls `task <id> done` for document sections, which must stay ungated

## Design Rationale

- The gate sits in the CLI path of `sync_task_status.py`, so the existing `sync_task()` tests and the
  document lifecycle are untouched.
- Evidence is read only from the checkout the command runs in; mirrors in other checkouts never
  stand in for it.
- Tests build a main checkout plus an epic worktree (`git worktree add`), record evidence with the
  real recorder, and edit files or evidence JSON to reach each refusing condition.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `sync_task_status.main`; `task_contract.evaluate_done_gate`,
  `is_code_epic`; `run_task_checks.py status`.
- **Downstream callers**: `dev-implementation` Phase 2 step 4 and `doc-implementation` Phase 2
  step 4 run `task <id> done`; `finishing-a-development-branch` runs `archive-done`.
- **Cross-platform bridges**: none.
- **Target test coverage threshold**: each of the seven conditions refused at least once.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: VTH-HP-03, VTH-ST-03, VTH-ST-04, VTH-ST-05, VTH-ST-06, VTH-ST-07, VTH-AR-02

Test methods `test_vth_hp_03_…`, `test_vth_st_03_…` to `test_vth_st_07_…` and `test_vth_ar_02_…` go
in `test_sync_task_status.py` and run both CLIs as subprocesses.

```gherkin
Scenario: [VTH-HP-03] [Tier C - Integration] Matching evidence lets the task reach done
  Given a task of a code epic whose red and verify runs are recorded and match the current tree
  When run_task_checks.py status runs
  Then it reports that the done gate would pass and exits 0
  When sync_task_status.py task done runs in the epic worktree
  Then the status, modified and completedAt fields are written in every checkout

Scenario: [VTH-ST-03] [Tier C - Integration] Done without evidence is refused
  Given a task of a code epic with no evidence file
  When sync_task_status.py task done runs
  Then it exits 1 naming the missing evidence
  And the task's status is unchanged in every checkout

Scenario: [VTH-ST-04] [Tier C - Integration] Edits after verification are refused
  Given a task whose verify run passed
  When a source file is changed afterwards and sync_task_status.py task done runs
  Then it exits 1 because the verify tree differs from the current tree
  When instead the Expect of row V2 is changed afterwards and sync_task_status.py task done runs
  Then it exits 1 because the recorded expect of V2 differs from the table

Scenario: [VTH-ST-05] [Tier C - Integration] A RED run that did not precede the change is refused
  Given a task whose red run was recorded on the same tree as its verify run
  When sync_task_status.py task done runs
  Then it exits 1 naming the RED ordering condition
  And the same holds when the red run finished after the verify run started

Scenario: [VTH-ST-06] [Tier C - Integration] Only code epics are gated
  Given a task of a code epic whose overview declares "Integration test roots:" and whose file has no Verification section
  When sync_task_status.py task done runs
  Then it exits 1 with "retrofit required"
  Given instead a task of a document epic whose overview declares no "Integration test roots:"
  When sync_task_status.py task done runs
  Then the status is written as before

Scenario: [VTH-ST-07] [Tier C - Integration] A covered identifier without a passing case is refused
  Given a task whose Covers line names VTH-HP-01 and VTH-EC-01
  And evidence whose results digest has a passed case for VTH-HP-01 only
  When sync_task_status.py task done runs
  Then it exits 1 naming VTH-EC-01

Scenario: [VTH-AR-02] [Tier C - Integration] The gate run from a checkout without the evidence writes nothing
  Given a main checkout and an epic worktree, with the evidence only in the worktree
  When sync_task_status.py task done runs from the main checkout
  Then it exits 1 saying the gate must run in the epic worktree
  And no checkout's copy of the task changes
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest -k vth skills/dev-implementation/resources/scripts/test_sync_task_status.py` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_sync_task_status.py skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0; contains "OK" | — |
| V3 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
| V4 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_4.xml skills/dev-implementation/resources/scripts/test_sync_task_status.py` | exit 0; results build/test-results/task_4.xml | — |
| V5 | TIER-C | `python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py tests --scenarios .devtool/epic/verifiable_task_handoff/bdd_scenarios.en.md --roots skills/dev-implementation/resources/scripts/ --results build/test-results/task_4.xml --ids VTH-HP-03 VTH-ST-03 VTH-ST-04 VTH-ST-05 VTH-ST-06 VTH-ST-07 VTH-AR-02` | exit 0; contains "Result: 7/7 covered — PASS" | — |

## Definition of Done

- The gate refuses each of the seven conditions and passes matching evidence, and the seven covered scenarios pass (V2, V4, V5).
- Document-epic tasks and every other subcommand behave as before (V2).
- `scripts/verify.sh` passes, now running `test_sync_task_status.py` (V3).
- This task itself reached `done` through the gate it built, run in the epic worktree (Gate 5).

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- An existing test in `test_sync_task_status.py` fails after the gate is added.

## Decisions Already Made

- The gate applies only when the epic overview has a line starting `Integration test roots:`.
- No waiver: a `BLOCKED` row always refuses.
- The gate never reads evidence from another checkout.
- Test fixtures use identifiers with the `DEMO-` prefix; only test method names carry `VTH-` identifiers.

## Dependencies & Blockers

- Blocked by [Task 1](task_1_verification_table_parser_and_evidence_recorder.md), [Task 2](task_2_test_result_reports_and_result_based_traceability.md)

## References & Rollback

- Source spec section 9; HLD section 4.5 item 1.
- Rollback: revert this task's commit; `task <id> done` writes without checking, as before.
