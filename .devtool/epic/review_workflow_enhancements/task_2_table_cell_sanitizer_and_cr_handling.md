---
id: "task_2_table_cell_sanitizer_and_cr_handling"
status: "todo"
priority: "high"
assignee: null
epic: "review_workflow_enhancements"
dueDate: null
created: "2026-10-18T03:00:00Z"
modified: "2026-10-18T03:00:00Z"
completedAt: null
labels: ["review", "tooling"]
order: "a2"
---

# Task 2: Table Cell Sanitizer and Control Character Handling

Covers: RWE-HP-03, RWE-EC-03

## Overview

### Summary
Update `cell()` in `run_external_review.py` to strip carriage return characters (`\r`), convert embedded newlines (`\n`) into single spaces, strip leading/trailing whitespace, and escape pipe delimiters (`|`). This guarantees that each finding resides on exactly one Markdown table row, preventing `split_row` and `table_findings` from failing with `unreadable findings row`.

### Pre-conditions
- Task 1 completed and passing.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k test_cell_sanitization` | exit non-zero | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k test_cell_sanitization` | exit 0; contains "OK" | — |
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

- Strip `\r` and convert `\n` to single space to keep finding rows single-line.
- Escape `|` as `\|` and strip outer whitespace.

## Dependencies & Blockers

- Blocked by task_1_resilient_verdict_and_finding_parser
