---
id: "task_1_slug_utils_and_tests"
status: "done"
priority: "high"
assignee: null
epic: "epic_slug_sanitization"
dueDate: null
created: "2026-09-15T12:00:00Z"
modified: "2026-09-15T12:34:43Z"
completedAt: "2026-09-15T12:34:43Z"
labels: ["tooling", "python", "sanitization"]
order: "a1"
---

# Task 1: Shared Slug Sanitizer and Frontmatter Module (slug_utils.py)

## Description
Create `skills/epic-implementation/resources/scripts/slug_utils.py` with standard library implementations of `sanitize_slug(raw: str | None) -> str | None` and `parse_frontmatter(text: str) -> dict`. Provide dedicated unit tests in `test_slug_utils.py` verifying that all formatting styles (backticks, straight & smart quotes, markdown links, HTML tags/comments, annotations, and trailing punctuation) are properly normalized to clean slug strings.

## Dependencies & Blockers
- None.

## Acceptance Criteria
- `skills/epic-implementation/resources/scripts/slug_utils.py` exists with `sanitize_slug` and `parse_frontmatter`.
- `sanitize_slug` handles backticks, single/double quotes, curly quotes (`“`, `”`, `‘`, `’`), markdown links, HTML tags, and trailing punctuation.
- `parse_frontmatter` strips double quotes, single quotes, and backticks.
- `test_slug_utils.py` passes 100% of unit test assertions.
