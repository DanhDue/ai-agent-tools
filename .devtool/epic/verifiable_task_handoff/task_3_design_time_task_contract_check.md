---
id: "task_3_design_time_task_contract_check"
status: "done"
priority: "high"
assignee: null
epic: "verifiable_task_handoff"
dueDate: null
created: "2026-10-16T06:53:44Z"
modified: "2026-10-16T07:44:01Z"
completedAt: "2026-10-16T07:44:01Z"
labels: ["scripts", "design-time"]
order: "a3"
---

# Task 3: Design-time task contract check

Epic: [verifiable_task_handoff](../epic/verifiable_task_handoff/verifiable_task_handoff.en.md)

## Requirement Analysis

Check what a designer wrote before Gate 2 closes, and make each scenario identifier belong to
exactly one task. Authority: source spec sections 5, 6 and 7.

### check_task_contract.py (new)

```bash
python3 skills/dev-implementation/resources/scripts/check_task_contract.py [--design] \
  --hld .devtool/epic/<epic_dir>/<epic_dir>.en.md --tasks <task mirror> [<task mirror> ...]
```

Root is `git rev-parse --show-toplevel` of the working directory. Problems print as
`<task stem>:<row or section>: <problem>`, or `<hld file name>: <problem>`. Then
`Implicit protected paths: <a>, <b>` (or `none`), then `Result: <n> problems — PASS` or `— FAIL`.
Exit 0 with no problem, 1 with problems, 2 for usage errors: outside a git repository, an unreadable
file, or a missing argument.

**Structure**, for every task:

- The sections `## Files`, `## Verification`, `## Definition of Done`, `## Stop and Report If` and
  `## Decisions Already Made` exist; `Allowed files:` has at least one entry.
- `parse_verification` succeeds; a `ContractError` becomes a problem, not exit 2.
- There is a RED row, or a `RED: n/a — <reason>` line with a non-empty reason.
- `results` appears only on `TIER-C` rows.
- A task with a `Covers:` line (use `covers_of` from `check_bdd_traceability.py`) has a `TIER-C` row
  with `results`.
- Every bullet of `## Definition of Done` ends with `(V<n>[, V<n>…])` naming existing rows, or with
  `(Gate 5)`; a trailing period is allowed.

**Grounding**, skipped for a task whose frontmatter `status` is `done` unless `--design` is given:

- An Allowed files entry without `(new)` is tracked (`git ls-files`); a glob matches at least one
  tracked file. Bare directories are a problem.
- With `--design` only: a `(new)` path does not exist yet, and its parent directory exists or its
  grandparent does (one new directory level).
- Every Read-only context path exists, or is `(new)` in some task of the epic.
- In every Command, each shell token containing `/` — the value part of `--name=value` included,
  tokens starting with `-` or containing `*` or `://` excluded — exists, is ignored by git (an output
  path), or is `(new)` in some task of the epic. An executable not on `PATH` is printed as a warning,
  never a problem.

**HLD declarations:**

- A line starting `Protected paths:`; at least one line starting `Integration results:` of the form
  `<command> -> <path>`; a `## Verification Environment` heading, optionally numbered
  (`## 6. Verification Environment`), with a non-empty body.
- Every `Needs` name appears in that section's body.
- Every `results` path and every Integration results path is ignored by git (`git check-ignore -q`).

Add to `task_contract.py` the helpers this needs, for example `parse_integration_results(hld_text)`,
`verification_environment(hld_text)`, `parse_read_only_context(task_text)` and
`dod_bullets(task_text)`.

### plan: exactly one owner

`check_plan` in `check_bdd_traceability.py` adds a problem
`<ID> is on the Covers lines of <task a> and <task b>` when an identifier appears in more than one
task. Everything else in `plan` is unchanged.

### Also

`scripts/verify.sh`, section 11: add
`python3 -m unittest skills/dev-implementation/resources/scripts/test_check_task_contract.py || FAILED=1`.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/check_task_contract.py` (new)
- `skills/dev-implementation/resources/scripts/test_check_task_contract.py` (new)
- `skills/dev-implementation/resources/scripts/task_contract.py`
- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`
- `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`
- `scripts/verify.sh`

Read-only context:
- `.devtool/epic/verifiable_task_handoff/2026-10-16-verifiable-task-handoff-design.en.md` — sections 5, 6 and 7
- `.devtool/epic/verifiable_task_handoff/verifiable_task_handoff.en.md` — a real HLD with all three declarations

## Design Rationale

- The checker reuses `task_contract.py`, so it accepts exactly what the recorder can run.
- "One new directory level" is how this task reads the spec's "its parent directory exists or is
  itself `(new)`": a typo higher up the path is still caught.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `check_task_contract.py`; new helpers in `task_contract.py`;
  `check_bdd_traceability.check_plan`.
- **Downstream callers**: `dev-designer` Step 3, the `dev-lifecycle` packaging preflight and
  `dev-implementation` Phase 1 run `plan`. The existing tests in `test_check_bdd_traceability.py`
  give no identifier to two tasks, so they keep passing.
- **Cross-platform bridges**: none.
- **Target test coverage threshold**: every problem message produced at least once.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: VTH-HP-01, VTH-EC-01, VTH-EC-02, VTH-EC-03, VTH-EC-04, VTH-ST-01, VTH-FR-04

`test_vth_hp_01_…`, `test_vth_ec_01_…` to `test_vth_ec_04_…` and `test_vth_fr_04_…` go in
`test_check_task_contract.py`; `test_vth_st_01_…` goes in `test_check_bdd_traceability.py`.

```gherkin
Scenario: [VTH-HP-01] [Tier C - Integration] A compliant epic passes the design-time contract check
  Given a git repository with an HLD declaring Protected paths, Integration results and a Verification Environment
  And two task files whose Files, Verification, Definition of Done, Stop and Report If and Decisions Already Made sections are complete
  When check_task_contract.py runs with --design
  Then it exits 0
  And it prints the tracked programs the Verification rows run as implicit protected paths

Scenario: [VTH-EC-01] [Tier C - Integration] Paths that do not match the repository are named
  Given a task whose Allowed files lists an untracked path without "(new)"
  And a "(new)" path that already exists
  And a Read-only context path that does not exist
  And a Command naming a repository path that no task creates
  When check_task_contract.py runs with --design
  Then it exits 1 and names each path with its task
  And without --design the existing "(new)" path of a task already done is not reported

Scenario: [VTH-EC-02] [Tier C - Integration] A Definition of Done item with no command is rejected
  Given a Definition of Done bullet ending with neither a row reference nor "(Gate 5)"
  And a bullet referencing row V9 that the table does not contain
  When check_task_contract.py runs
  Then it exits 1 and names both bullets

Scenario: [VTH-EC-03] [Tier C - Integration] A malformed Verification table is rejected row by row
  Given a table with a duplicate ID, an unknown phase, an Expect clause outside the grammar and "results" on a GREEN row
  And a task with neither a RED row nor a "RED: n/a" reason
  And a task with a Covers line but no TIER-C row carrying "results"
  When check_task_contract.py runs
  Then it exits 1 and names every problem as "<task>:<row>: <problem>"

Scenario: [VTH-EC-04] [Tier C - Integration] Missing HLD declarations are rejected
  Given an HLD without a Protected paths line, without an Integration results line or with an empty Verification Environment section
  And a Needs variable the Verification Environment does not name
  And a results path that git does not ignore
  When check_task_contract.py runs
  Then it exits 1 and names each missing or invalid declaration

Scenario: [VTH-ST-01] [Tier C - Integration] An identifier owned by two tasks fails the plan
  Given a scenario document with VTH-HP-01
  And two task files whose Covers lines both name VTH-HP-01
  When check_bdd_traceability.py plan runs
  Then it exits 1 and names both tasks for VTH-HP-01

Scenario: [VTH-FR-04] [Tier C - Integration] The contract check reports usage errors with exit 2
  Given a task file that cannot be read, or a working directory outside any git repository
  When check_task_contract.py runs
  Then it exits 2 with the reason on stderr
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 1; contains "ModuleNotFoundError" | — |
| V2 | RED | `python3 -m unittest -k vth_st_01 skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py` | exit 1; contains "FAILED" | — |
| V3 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_task_contract.py skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_3.xml skills/dev-implementation/resources/scripts/test_check_task_contract.py skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py` | exit 0; results build/test-results/task_3.xml | — |
| V6 | TIER-C | `python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py tests --scenarios .devtool/epic/verifiable_task_handoff/bdd_scenarios.en.md --roots skills/dev-implementation/resources/scripts/ --results build/test-results/task_3.xml --ids VTH-HP-01 VTH-EC-01 VTH-EC-02 VTH-EC-03 VTH-EC-04 VTH-ST-01 VTH-FR-04` | exit 0; contains "Result: 7/7 covered — PASS" | — |
| V7 | TIER-C | `python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py plan --scenarios .devtool/epic/verifiable_task_handoff/bdd_scenarios.en.md --tasks .devtool/epic/verifiable_task_handoff/task_*.md` | exit 0; contains "Result: 41/41 covered — PASS" | — |

## Definition of Done

- `check_task_contract.py` reports every structure, grounding and declaration problem of the spec, and the six covered contract scenarios pass (V3, V5, V6).
- `plan` fails an identifier owned by two tasks, and this epic's own plan still passes (V3, V6, V7).
- `scripts/verify.sh` passes with the new test file wired in (V4).

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- An existing `plan` test expects an identifier shared by two tasks to pass.

## Decisions Already Made

- Exactly one task owns each identifier; each identifier still needs at least one test.
- Without `--design`, grounding skips `done` tasks and never checks `(new)` paths.
- A missing executable is a warning, never a problem.
- Test fixtures use identifiers with the `DEMO-` prefix; only test method names carry `VTH-` identifiers.

## Dependencies & Blockers

- Blocked by [Task 1](task_1_verification_table_parser_and_evidence_recorder.md)

## References & Rollback

- Source spec sections 5, 6 and 7; HLD sections 5 and 6 as a real example.
- Rollback: revert this task's commit; `plan` returns to "at least one task".
