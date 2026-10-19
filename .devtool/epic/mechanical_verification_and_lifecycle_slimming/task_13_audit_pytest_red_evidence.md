---
id: "task_13_audit_pytest_red_evidence"
status: "todo"
priority: "high"
assignee: null
epic: "mechanical_verification_and_lifecycle_slimming"
dueDate: null
created: "2026-10-19T11:50:01Z"
modified: "2026-10-19T11:50:01Z"
completedAt: null
labels: ["python", "audit", "verification"]
order: "a13"
---

# Task 13: Re-Audit Pytest RED Evidence at Gate 4

Epic: [mechanical_verification_and_lifecycle_slimming](mechanical_verification_and_lifecycle_slimming.en.md)

## Requirement Analysis

Gate 4 must not trust a stored `outcome: PASS`. For every pytest RED row, `audit_epic.py` must read
the committed command, exit code, and output tail, invoke Task 12's shared validator, and fail the
Evidence section and aggregate verdict when the semantics are invalid.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/audit_epic.py`
- `skills/dev-implementation/resources/scripts/test_audit_epic.py`

Read-only context:
- `skills/dev-implementation/resources/scripts/run_task_checks.py` — shared RED validator from Task 12
- `skills/dev-implementation/resources/scripts/task_contract.py` — row and evidence contracts
- `.devtool/epic/mechanical_verification_and_lifecycle_slimming/bdd_scenarios.en.md` — canonical behavior contract

## Design Rationale

Reuse the recorder's pure validator so recording and auditing cannot drift. Preserve audit precedence
`FAIL > BLOCKED > PASS`, associate each finding with its task and row, and make traversal order
irrelevant. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`,
and `d3nexus:verification-before-completion`; tools are `unittest`, `ruff`, and `mypy`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: evidence-row audit and aggregate verdict in `audit_epic.py`.
- **Downstream callers**: `dev-implementation` Gate 4 and lifecycle Gate 4 acceptance.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: At least 85% on new audit branches, including edited evidence
  and multi-task ordering.

### BDD SCENARIOS

Covers: MVLS-HP-02, MVLS-ST-02, MVLS-AR-02

```gherkin
Scenario: Gate 4 recomputes RED semantics
  Given committed pytest RED evidence contains command, exit, and output data
  When the candidate SHA is audited
  Then valid evidence passes and invalid evidence fails independently of its stored outcome

Scenario: Multi-task auditing is deterministic
  Given several evidence records have mixed validity
  When they are audited repeatedly in different traversal orders
  Then findings remain attached to the correct rows and FAIL keeps highest precedence
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_audit_epic.py` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_audit_epic.py` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/audit_epic.py skills/dev-implementation/resources/scripts/test_audit_epic.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict skills/dev-implementation/resources/scripts/audit_epic.py skills/dev-implementation/resources/scripts/test_audit_epic.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_13.xml skills/dev-implementation/resources/scripts/test_audit_epic.py` | exit 0; results build/test-results/task_13.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Committed evidence lacks the exit code or output needed for semantic recomputation.

## Decisions Already Made

- The auditor reuses Task 12's validator and does not duplicate its patterns.
- Stored PASS cannot override invalid pytest semantics.
- The required failure reason and fail-closed rules are fixed by the HLD.

## Definition of Done

- All three assigned BDD IDs appear in automated audit tests and the JUnit report. (V2, V5)
- Valid committed pytest RED evidence passes semantic recomputation. (V2)
- Edited PASS evidence and mixed multi-task evidence produce deterministic FAIL findings. (V2)
- Lint and strict type checking report zero issues. (V3, V4)
- Gate 4 precedence and unrelated audit behavior remain green. (V2, V5)

## Dependencies & Blockers

Blocked by [Task 12](task_12_harden_pytest_red_recording.md).

Blocks [Task 16](task_16_lifecycle_docs_and_acceptance.md).

## References & Rollback

- [Epic HLD](mechanical_verification_and_lifecycle_slimming.en.md)
- [Canonical BDD scenarios](bdd_scenarios.en.md)
- **Rollback**: Revert the audit and its tests together; Task 12 may remain independently useful.
