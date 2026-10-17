---
id: "task_3_facts_timeout_isolation_and_fail_fast"
status: "done"
priority: "high"
assignee: null
epic: "review_workflow_enhancements"
dueDate: null
created: "2026-10-18T03:00:00Z"
modified: "2026-10-17T20:42:49Z"
completedAt: "2026-10-17T20:42:49Z"
labels: ["review", "tooling"]
order: "a3"
---

# Task 3: Facts Timeout Isolation and Fail-Fast Preconditions

Covers: RWE-HP-04, RWE-EC-04, RWE-FR-01, RWE-FR-02

## Overview

### Summary
Update `collect_facts()` in `run_external_review.py` to enforce a fail-fast policy before invoking external AI CLIs: if `audit_epic.py` exits with non-zero or an integration test encounters a timeout (`code is None`), abort immediately. Add a dedicated `--facts-timeout` argument (defaulting to 300 seconds) so fact commands do not monopolize the overall review timeout.

### Pre-conditions
- Tasks 1 and 2 completed.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 skills/dev-implementation/resources/scripts/test_run_external_review.py RunExternalReviewTest.test_rwe_fr_01_fail_fast_aborts_on_audit_failure` | exit non-zero | — |
| V2 | GREEN | `python3 skills/dev-implementation/resources/scripts/test_run_external_review.py RunExternalReviewTest.test_rwe_fr_01_fail_fast_aborts_on_audit_failure` | exit 0; contains "OK" | — |
| V3 | TIER-B | `python3 -m unittest discover -s skills/dev-implementation/resources/scripts` | exit 0 | — |
| V4 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/unit.xml skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; results build/test-results/unit.xml | — |

## Definition of Done

- The task's focused test proves the intended behaviour through a RED then GREEN cycle. (V1, V2)
- Repository architecture boundaries remain valid. (V3)
- Every scenario named by the Covers line appears in the passing integration result report. (V4)
- The implementation matches the frozen HLD decisions and the developer accepts the task on the Kanban board. (Gate 5)

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.

## Decisions Already Made

- Fail-fast immediately aborts with exit code 2 if `audit_epic.py` fails or tests timeout before calling `cli_command`.
- Default facts timeout is 300 seconds per command, configurable via `--facts-timeout`.

## Dependencies & Blockers

- Blocked by task_2_table_cell_sanitizer_and_cr_handling
