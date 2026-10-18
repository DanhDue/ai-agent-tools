---
id: "task_5_smart_hybrid_diff_inlining"
status: "todo"
priority: "high"
assignee: null
epic: "review_workflow_enhancements"
dueDate: null
created: "2026-10-18T08:30:00Z"
modified: "2026-10-18T08:30:00Z"
completedAt: null
labels: ["review", "prompt", "optimization"]
order: "a5"
---

# Task 5: Smart Hybrid Diff Inlining in Prompt

Covers: RWE-HP-05, RWE-EC-05

## Overview

### Summary
Update `run_external_review.py` and `external-review-prompt.md` to implement a smart hybrid diff inlining strategy:
1. Extract `git diff $base...$sha` excluding lock files (`*.lock`) and build outputs (`build/**`).
2. If diff length is within the line budget (default 1,500 lines, configurable via `--diff-limit`), inline the entire git diff directly into the prompt in a dedicated `## Code Changes` block.
3. If diff length exceeds the line budget, inline `git diff --stat` and instruct the model that the diff is large, so it can selectively inspect files using tools.
This saves 40%–60% of review token costs and round-trips by turning common reviews into single-turn executions while preventing prompt blowout on large diffs.

### Pre-conditions
- Tasks 1 through 4 completed.

## Files

Allowed files:
- `skills/dev-implementation/references/external-review-prompt.md`
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 skills/dev-implementation/resources/scripts/test_run_external_review.py RunExternalReviewTest.test_rwe_hp_05_inlined_code_diff` | exit non-zero | — |
| V2 | GREEN | `python3 skills/dev-implementation/resources/scripts/test_run_external_review.py RunExternalReviewTest.test_rwe_hp_05_inlined_code_diff` | exit 0; contains "OK" | — |
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

- Default line limit is 1,500 lines, configurable via `--diff-limit`.
- Path exclusion: excludes `*.lock` and `build/**`.
- Prompt template carries `$code_changes` placeholder containing either full diff or summary stat.

## Dependencies & Blockers

- Blocked by task_4_external_review_prompt_hierarchy_and_guidelines
