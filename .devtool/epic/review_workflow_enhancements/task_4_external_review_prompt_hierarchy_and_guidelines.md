---
id: "task_4_external_review_prompt_hierarchy_and_guidelines"
status: "todo"
priority: "high"
assignee: null
epic: "review_workflow_enhancements"
dueDate: null
created: "2026-10-18T03:00:00Z"
modified: "2026-10-18T03:00:00Z"
completedAt: null
labels: ["review", "tooling"]
order: "a4"
---

# Task 4: External Review Prompt Hierarchy and Test Quality Guidelines

Covers: RWE-ST-01, RWE-ST-02

## Overview

### Summary
Update `skills/dev-implementation/references/external-review-prompt.md` to instruct reviewers on verification hierarchy (Task-level scope vs Gate 4 workspace quality orchestrator), compiled language TDD RED semantics, code diff inspection (`git diff $base...$sha`), and build artifact budget assertion guidelines. Document the anti-pattern rule prohibiting uncounted test iteration loops on build artifacts in `skills/code-health-audit/SKILL.md` and `skills/dev-implementation/SKILL.md`.

### Pre-conditions
- Tasks 1, 2, and 3 completed.

## Files

Allowed files:
- `skills/dev-implementation/references/external-review-prompt.md`
- `skills/code-health-audit/SKILL.md`
- `skills/dev-implementation/SKILL.md`

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | TIER-B | `python3 skills/dev-implementation/resources/scripts/run_external_review.py --help` | exit 0; contains "run" | — |
| V2 | TIER-B | `python3 -m unittest discover -s skills/dev-implementation/resources/scripts` | exit 0; contains "OK" | — |
| V3 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/unit.xml skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; results build/test-results/unit.xml | — |

RED: n/a — prompt template, documentation, and quality rule publication; behavioural tests belong to Tasks 1–3.

## Definition of Done

- The prompt template and documentation checks pass cleanly. (V1, V2)
- Repository architecture boundaries remain valid. (V2)
- The complete test suite across dev-implementation passes. (V3)
- Gate 4 evidence is bound to the immutable candidate SHA and all human-only acceptance items remain for Gate 5. (Gate 5)

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.

## Decisions Already Made

- Prompt explicitly clarifies that workspace capabilities belong to Gate 4 quality orchestrator on the final candidate SHA.
- TDD RED for compiled languages is explicitly acknowledged.
- Code health audit rules prohibit candidate loop assertions without verifying evaluated element counts.

## Dependencies & Blockers

- Blocked by task_3_facts_timeout_isolation_and_fail_fast
