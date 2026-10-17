---
id: "task_1_resilient_verdict_and_finding_parser"
status: "todo"
priority: "high"
assignee: null
epic: "review_workflow_enhancements"
dueDate: null
created: "2026-10-18T03:00:00Z"
modified: "2026-10-18T03:00:00Z"
completedAt: null
labels: ["review", "tooling"]
order: "a1"
---

# Task 1: Resilient Verdict and Finding Parsing

Covers: RWE-HP-01, RWE-HP-02, RWE-EC-01, RWE-EC-02

## Overview

### Summary
Update `run_external_review.py` regular expressions to parse model verdicts that include Markdown bolding (`**`), Markdown headers (`#`, `##`, `###`), and case variations. Constrain `UNPARSED_BLOCKING` to lines formatted as list items or bullets to prevent false-positive blocking defects triggered by conversational summary sentences.

### Pre-conditions
- Existing 213 unit tests pass cleanly.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k test_resilient_verdict_parsing` | exit non-zero | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k test_resilient_verdict_parsing` | exit 0; contains "OK" | — |
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

- Follow standard library Python 3 regex conventions without adding third-party dependencies.
- `VERDICT` regex matches optional markdown header hashes (`#`), optional bold asterisks (`**`), and case insensitivity.
- `UNPARSED_BLOCKING` is restricted to bullet/numbered lines or ignored if verdict is PASS and no standard findings are present.

## Dependencies & Blockers

- None.
