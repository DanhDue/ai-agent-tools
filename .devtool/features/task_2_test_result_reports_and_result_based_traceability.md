---
id: "task_2_test_result_reports_and_result_based_traceability"
status: "done"
priority: "high"
assignee: null
epic: "verifiable_task_handoff"
dueDate: null
created: "2026-10-16T06:53:44Z"
modified: "2026-10-16T07:37:35Z"
completedAt: "2026-10-16T07:37:35Z"
labels: ["scripts", "traceability"]
order: "a2"
---

# Task 2: Test result reports and result-based traceability

Epic: [verifiable_task_handoff](../epic/verifiable_task_handoff/verifiable_task_handoff.en.md)

## Requirement Analysis

Make traceability prove that each identifier's test ran and passed, from JUnit XML or Dart JSON
reports, and let the recorder store a digest of every report it checks. Authority: source spec
section 10.

### result_reports.py (new)

`skills/dev-implementation/resources/scripts/result_reports.py`, standard library only:

- `ReportError(Exception)`: a path that is missing, or a file in neither format.
- `Case` frozen dataclass: `name: str`, `classname: str`, `status` — `"passed"`, `"failed"` or
  `"skipped"`.
- `load_reports(paths: list[str], root: Path) -> list[Case]`: each path, relative to `root`, is a
  file, a directory (every `*.xml` and `*.json` under it, recursively) or a glob. The format comes
  from the first non-space character: `<` is JUnit, `{` is Dart; anything else raises `ReportError`
  naming the file.
- `parse_junit(text)`: every `testcase` element at any depth; a `failure` or `error` child means
  failed, a `skipped` child means skipped, otherwise passed.
- `parse_dart(text)`: newline-delimited JSON events. A `testStart` event gives `test.id` and
  `test.name`; the matching `testDone` gives `result` (`success` means passed, anything else failed),
  `skipped` (true means skipped) and `hidden` (true means ignore the test). `classname` is `""`.
- `reference_pattern(identifier)`: moved here unchanged from `check_bdd_traceability.py`, which now
  imports it from this module.
- `verdicts(ids, cases) -> dict[str, tuple[bool, str]]`: a case belongs to an identifier when
  `reference_pattern` finds it in `name` or `classname`. Per identifier: any failed case gives
  `(False, "failed in <case>")`; otherwise any passed case gives `(True, <case>)`; otherwise skipped
  cases give `(False, "skipped")`; otherwise `(False, "no test case in results")`.
- `digest(cases, ids) -> dict`:
  `{"totals": {"passed": n, "failed": n, "skipped": n}, "cases": [{"name", "classname", "status"}]}`,
  listing only the cases that belong to one of `ids`.

### check_bdd_traceability.py tests --results

- `tests` gains `--results` (`nargs="+"`). With it, coverage comes only from `verdicts` over
  `load_reports`. Each selected identifier prints `<ID>    PASS <case>` or `<ID>    FAIL <reason>`,
  then `Result: <n>/<m> covered — PASS` or `— FAIL`. The stale-reference check runs over the files
  under `--roots`, as today, and over case names.
- A `ReportError` exits 2 with `error: <message>` on stderr.
- Without `--results`, the mode behaves exactly as today.

### Recorder digest

In `run_task_checks.py`, a fresh `results` path is loaded with `load_reports`. The row's `results`
object gains `"digest": digest(cases, ids)`, where `ids` are the identifiers of the epic's
`bdd_scenarios.en.md` (use `load_scenarios` from `check_bdd_traceability.py`). A `ReportError` makes
the row `FAIL` with `reason: "results in neither format"`.

### Also

`scripts/verify.sh`, section 11: add
`python3 -m unittest skills/dev-implementation/resources/scripts/test_result_reports.py || FAILED=1`.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/result_reports.py` (new)
- `skills/dev-implementation/resources/scripts/test_result_reports.py` (new)
- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`
- `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`
- `skills/dev-implementation/resources/scripts/run_task_checks.py`
- `skills/dev-implementation/resources/scripts/test_run_task_checks.py`
- `scripts/verify.sh`

Read-only context:
- `skills/dev-implementation/resources/scripts/task_contract.py` — the evidence row layout from Task 1
- `.devtool/epic/verifiable_task_handoff/2026-10-16-verifiable-task-handoff-design.en.md` — section 10

## Design Rationale

- `reference_pattern` moves into `result_reports.py` so that the CLI, the recorder and the `done`
  gate (Task 4) share one matching rule without a circular import.
- Fixtures are inline strings: one JUnit file shaped like pytest's, a directory of two JUnit files
  shaped like Gradle's, and a Dart NDJSON stream with a group.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `result_reports.py`; `check_bdd_traceability.main`, `check_tests`,
  `reference_pattern`; the recorder's results handling.
- **Downstream callers**: `dev-implementation` Phase 2 and Phase 4, `dev-lifecycle` packaging and
  Gate 4 call `tests` without `--results`; their behaviour must not change.
- **Cross-platform bridges**: none.
- **Target test coverage threshold**: every verdict branch and both formats exercised.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: VTH-HP-04, VTH-EC-06, VTH-FR-02

Test methods `test_vth_hp_04_…`, `test_vth_ec_06_…` and `test_vth_fr_02_…` go in
`test_check_bdd_traceability.py` and drive `main()`. Parser unit tests go in `test_result_reports.py`.

```gherkin
Scenario: [VTH-HP-04] [Tier C - Integration] JUnit and Dart reports prove every identifier
  Given a JUnit file with a passed case "test_vth_hp_01_compliant_epic"
  And a Gradle-style directory of JUnit files with a passed case for VTH-EC-01
  And a Dart JSON reporter file with a passed test "[VTH-ST-01] plan rejects" inside a group
  When the tests mode runs with --results naming the file, the directory and the Dart file
  Then every selected identifier passes and the run exits 0

Scenario: [VTH-EC-06] [Tier C - Integration] Misleading coverage is rejected with its reason
  Given an identifier that appears only in a comment of a test file
  And an identifier whose only case is skipped
  And an identifier with one passed and one failed case
  When the tests mode runs with --results
  Then the first fails with "no test case in results", the second with "skipped" and the third with "failed in"
  And the run exits 1

Scenario: [VTH-FR-02] [Tier C - Integration] A report in neither format is a usage error
  Given a results file that starts with neither "<" nor "{"
  When the tests mode runs with --results naming it
  Then it exits 2 naming the file
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest -k vth skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py` | exit 1; contains "FAILED" | — |
| V2 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_result_reports.py` | exit 1; contains "ModuleNotFoundError" | — |
| V3 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py skills/dev-implementation/resources/scripts/test_result_reports.py skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py` | exit 0; results build/test-results/task_2.xml | — |
| V6 | TIER-C | `python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py tests --scenarios .devtool/epic/verifiable_task_handoff/bdd_scenarios.en.md --roots skills/dev-implementation/resources/scripts/ --results build/test-results/task_2.xml --ids VTH-HP-04 VTH-EC-06 VTH-FR-02` | exit 0; contains "Result: 3/3 covered — PASS" | — |

## Definition of Done

- `tests --results` reads JUnit and Dart reports and gives the four verdicts of the spec, and the three covered scenarios pass (V3, V5, V6).
- The recorder stores a digest for every fresh report, and a report in neither format fails its row (V3).
- Every existing caller of `tests` without `--results` behaves as before, and `scripts/verify.sh` passes (V3, V4).

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- An existing test in `test_check_bdd_traceability.py` fails after `reference_pattern` moves.

## Decisions Already Made

- JUnit XML and the Dart JSON reporter are the only formats; nothing else is detected.
- A failed case for an identifier fails it even when another case passed.
- Without `--results`, `tests` is unchanged.
- Test fixtures use identifiers with the `DEMO-` prefix; only test method names carry `VTH-` identifiers.

## Dependencies & Blockers

- Blocked by [Task 1](task_1_verification_table_parser_and_evidence_recorder.md)

## References & Rollback

- Source spec section 10; HLD section 5.
- Rollback: revert this task's commit; `tests` without `--results` is untouched.
