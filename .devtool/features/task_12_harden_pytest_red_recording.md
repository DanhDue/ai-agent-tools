---
id: "task_12_harden_pytest_red_recording"
status: "todo"
priority: "high"
assignee: null
epic: "mechanical_verification_and_lifecycle_slimming"
dueDate: null
created: "2026-10-19T11:50:01Z"
modified: "2026-10-19T11:50:01Z"
completedAt: null
labels: ["python", "verification", "security"]
order: "a12"
---

# Task 12: Harden Pytest RED Recording Semantics

Epic: [mechanical_verification_and_lifecycle_slimming](../epic/mechanical_verification_and_lifecycle_slimming/mechanical_verification_and_lifecycle_slimming.en.md)

## Requirement Analysis

`run_task_checks.py` must reject pytest RED rows that fail because the file is missing, no tests
were selected, or the process produced no positive failed/error summary. Supported direct and
wrapped pytest commands are recognized from shell tokens, not substring matches. Recording an
invalid pytest RED writes a FAIL outcome, prints the exact required reason, and exits non-zero.
`run_task_checks.py` also implements the runtime task tamper-proof guard: before executing any command
row, it validates the active task in `.devtool/features/` against the committed HEAD state or parent
mirror in `.devtool/epic/<epic_dir>/task_*.md`. If core sections (`Files`, `Verification`,
`Definition of Done`, or `Covers`) were altered, it aborts immediately with a `TASK_TAMPERED_ERROR`
and commits no verification evidence.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/run_task_checks.py`
- `skills/dev-implementation/resources/scripts/test_run_task_checks.py`

Read-only context:
- `skills/dev-implementation/resources/scripts/task_contract.py` — shared task-row parser
- `.devtool/epic/mechanical_verification_and_lifecycle_slimming/mechanical_verification_and_lifecycle_slimming.en.md` — architecture and decision rules
- `.devtool/epic/mechanical_verification_and_lifecycle_slimming/bdd_scenarios.en.md` — canonical behavior contract

## Design Rationale

Implement one pure semantic validator that accepts command tokens, exit code, and merged output.
Only exits 1 and 2 may qualify; forbidden markers override the exit code; a positive non-zero
failed/error summary is mandatory. Keep the logic in production code and import it from tests.
Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, and
`d3nexus:verification-before-completion`; tools are `unittest`, `ruff`, and `mypy`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: RED-row execution, evidence verdict logic, and task contract tamper detection in
  `run_task_checks.py`; adjacent recorder tests.
- **Downstream callers**: `audit_epic.py`, `scripts/test_verifiable_handoff.py`, task execution in
  `dev-implementation`, and any consumer of committed verification evidence.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: At least 85% for new validator branches; every listed BDD ID
  has an automated test using the real recorder boundary.

### BDD SCENARIOS

Covers: MVLS-HP-01, MVLS-EC-01, MVLS-EC-02, MVLS-EC-04, MVLS-ST-01, MVLS-AR-01, MVLS-FR-01, MVLS-FR-02, MVLS-FR-06

```gherkin
Scenario: A collected pytest failure is valid
  Given a supported pytest command exits 1 or 2 with a positive failure summary
  When the recorder evaluates the RED row
  Then the expected RED outcome is PASS

Scenario: A non-behavioral pytest failure is invalid
  Given pytest reports a missing file, zero collection, zero selection, or no positive summary
  When the recorder evaluates the RED row, including through an exit-rewriting wrapper
  Then it records FAIL with the exact required reason

Scenario: Row evaluation is token-aware and isolated
  Given valid and invalid rows appear in either order
  When supported wrappers and unrelated `echo pytest` text are classified
  Then only direct pytest invocations are checked and no row inherits another row's output

Scenario: Fail when active task core sections are tampered
  Given an active task file in `.devtool/features/` with modified core sections
  When `run_task_checks.py` validates task integrity before running verification commands
  Then it aborts with a task tampered error and commits no evidence
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_12.xml skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0; results build/test-results/task_12.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Standard pytest output cannot distinguish a collected failing test from an empty selection.
- The validator would need to execute an opaque wrapper script to infer its behavior.

## Decisions Already Made

- Only pytest exits 1 and 2 can qualify as RED.
- The required failure reason is fixed verbatim in the HLD.
- A collection-time import failure with zero collected tests is invalid; import behavior must be
  exercised inside a collected test.

## Definition of Done

- All nine assigned BDD IDs appear in automated recorder tests and the JUnit report. (V2, V5)
- Exit 4/5, every forbidden marker, exit rewriting, ambiguous exit 1, and valid exit 1/2 are covered. (V2)
- Token-aware recognition accepts supported wrappers and rejects unrelated text. (V2)
- Runtime task tamper-proof guard prevents execution and evidence recording when core task sections are modified. (V2)
- Lint and strict type checking report zero issues. (V3, V4)
- The implementation changes only Allowed files and is ready for task commit. (V2, V5)

## Dependencies & Blockers

None.

Blocks [Task 13](../epic/mechanical_verification_and_lifecycle_slimming/task_13_audit_pytest_red_evidence.md).

## References & Rollback

- [Epic HLD](../epic/mechanical_verification_and_lifecycle_slimming/mechanical_verification_and_lifecycle_slimming.en.md)
- [Canonical BDD scenarios](../epic/mechanical_verification_and_lifecycle_slimming/bdd_scenarios.en.md)
- **Rollback**: Revert this task's production and test commit together; do not retain tests that
  assert semantics the recorder no longer implements.
