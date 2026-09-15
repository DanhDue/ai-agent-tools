---
id: "task_3_compute_execution_order_integration"
status: "done"
priority: "high"
assignee: null
epic: "epic_slug_sanitization"
dueDate: null
created: "2026-09-15T12:00:00Z"
modified: "2026-09-15T12:43:44Z"
completedAt: "2026-09-15T12:43:44Z"
labels: ["tooling", "python", "ordering"]
order: "b2"
---

# Task 3: Upgrade compute_execution_order.py with Slug Normalization

## Description
Integrate `slug_utils` into `skills/epic-implementation/resources/scripts/compute_execution_order.py`. Sanitize the CLI argument (`args.epic`) and task frontmatter (`fm.get("epic")`) inside `scan_tasks` so that tasks are accurately matched even if the caller or task frontmatter passes a formatted slug. Update `test_compute_execution_order.py` with multi-format test cases.

## Dependencies & Blockers
- Blocked by [Task 1](task_1_slug_utils_and_tests.md)

## Acceptance Criteria
- `compute_execution_order.py` imports `sanitize_slug` and `parse_frontmatter` from `slug_utils`.
- `scan_tasks` compares sanitized `fm.get("epic")` against sanitized `epic`.
- CLI invocation works with backticks (e.g. `compute_execution_order.py \`my_epic\``) without skipping tasks.
- `test_compute_execution_order.py` passes all tests.
