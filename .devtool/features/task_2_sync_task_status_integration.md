---
id: "task_2_sync_task_status_integration"
status: "todo"
priority: "high"
assignee: null
epic: "epic_slug_sanitization"
dueDate: null
created: "2026-09-15T12:00:00Z"
modified: "2026-09-15T12:00:00Z"
completedAt: null
labels: ["tooling", "python", "archival"]
order: "b1"
---

# Task 2: Upgrade sync_task_status.py with Robust Slug Normalization

## Description
Integrate `slug_utils` into `skills/epic-implementation/resources/scripts/sync_task_status.py`. Use `sanitize_slug` across `find_epic_slug`, `epic_of`, and `expected_epic` to ensure that overview headers formatted with backticks or markdown links correctly match task frontmatter. Add test cases in `test_sync_task_status.py` validating that archival (`archive-done` and `archive-epic`) succeeds when HLD overviews contain markdown formatting.

## Dependencies & Blockers
- Blocked by [Task 1](task_1_slug_utils_and_tests.md)

## Acceptance Criteria
- `sync_task_status.py` imports `sanitize_slug` and `parse_frontmatter` from `slug_utils`.
- `find_epic_slug` returns sanitized slugs for `.en.md` and `.vi.md` documents.
- `epic_of` returns sanitized slugs from task frontmatter.
- `test_sync_task_status.py` passes all existing and new multi-format tests.
