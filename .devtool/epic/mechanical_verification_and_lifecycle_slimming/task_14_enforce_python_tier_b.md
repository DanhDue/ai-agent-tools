---
id: "task_14_enforce_python_tier_b"
status: "done"
priority: "high"
assignee: null
epic: "mechanical_verification_and_lifecycle_slimming"
dueDate: null
created: "2026-10-19T11:50:01Z"
modified: "2026-10-19T13:58:10Z"
completedAt: "2026-10-19T13:58:10Z"
labels: ["python", "contracts", "governance"]
order: "a14"
---

# Task 14: Enforce Python TIER-B Lint and Type Checking

Epic: [mechanical_verification_and_lifecycle_slimming](mechanical_verification_and_lifecycle_slimming.en.md)

## Requirement Analysis

Extend `check_task_contract.py` so a task-local Python signal, or any TIER-B ruff invocation,
requires the task's TIER-B rows to directly invoke both lint and type-check capabilities. Prefer a
valid registered Python capability manifest; otherwise recognize ruff plus mypy, pyright, or ty.
Additionally, `check_task_contract.py` implements deterministic fast-model contract checks:
1) Reject pytest commands that use generic `-k` expressions without an exact node ID (`path/test_file.py::test_name`).
2) Reject weak or vague assertions in BDD scenarios (such as `should be truthy`, `is valid`, `should work`, `returns non-empty`).
3) Require that tasks with executable changes (RED or GREEN rows) have a non-empty `## Decisions Already Made` section that does not say `None`.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`

Read-only context:
- `skills/dev-implementation/resources/scripts/task_contract.py` — verification-row parser
- `skills/python-quality-check/references/python-capability-contract.md` — provider capability contract
- `.devtool/epic/mechanical_verification_and_lifecycle_slimming/bdd_scenarios.en.md` — canonical scenarios

## Design Rationale

Classify from Allowed files and verification rows, never repository presence alone. Normalize shell
tokens and require direct capability argument sequences; do not infer the contents of opaque scripts.
Malformed registered JSON fails closed. Fast-model deterministic checks run without AST parsing across
foreign languages by enforcing explicit token, regex, and task section rules.
Applicable skills: `d3nexus:test-driven-development` and `d3nexus:python-quality-check`; tools are `unittest`, `ruff`, and `mypy`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: task-local language detection, provider-manifest loading, TIER-B checks, and fast-model deterministic contract checks (`Decisions Already Made`, node ID validation, BDD assertion rigor).
- **Downstream callers**: `dev-designer` Step 3 and `dev-implementation` Gate 3 preflight.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: At least 85% across fallback, provider, malformed, and polyglot branches.

### BDD SCENARIOS

Covers: MVLS-HP-03, MVLS-EC-03, MVLS-EC-07, MVLS-FR-03

```gherkin
Scenario: Complete Python TIER-B passes
  Given task-local Python evidence and direct lint plus type-check commands
  When the task contract is checked
  Then fallback or registered capabilities satisfy the contract

Scenario: Classification and manifests fail safely
  Given a non-Python polyglot task or a malformed registered Python manifest
  When the contract is checked
  Then the first avoids Python false positives and the second reports a contract failure

Scenario: Reject non-node-id pytest expressions, weak BDD assertions, or empty decisions
  Given a task contract undergoing design or implementation verification
  When `check_task_contract.py` checks pytest RED rows, BDD scenario assertions, or `Decisions Already Made`
  Then a generic `-k` pytest command without an exact node ID is rejected
  And weak assertions such as "should be truthy", "is valid", or "returns non-empty" are rejected
  And an empty or missing `Decisions Already Made` section on a task with executable changes is rejected
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_14.xml skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0; results build/test-results/task_14.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.
- Supporting a provider command would require executing an opaque script during design validation.

## Decisions Already Made

- Task-local evidence controls Python classification; any ruff TIER-B row activates type checking.
- Registered `lint` and `type_check` commands take precedence; malformed registration fails closed.

## Definition of Done

- All four assigned BDD IDs appear in automated tests and the JUnit report. (V2, V5)
- Ruff-only tasks fail; ruff with mypy, pyright, ty, or valid registered capabilities passes. (V2)
- Deterministic fast-model checks reject pytest `-k` without node ID, weak BDD assertions, and empty `Decisions Already Made` on executable tasks. (V2)
- Polyglot false positives and malformed manifests are covered. (V2)
- Lint and strict type checking report zero issues. (V3, V4)

## Dependencies & Blockers

None. Blocks [Task 16](task_16_lifecycle_docs_and_acceptance.md).

## References & Rollback

- [Epic HLD](mechanical_verification_and_lifecycle_slimming.en.md)
- **Rollback**: Revert checker and tests together; do not weaken provider manifests.
