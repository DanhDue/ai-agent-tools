#!/usr/bin/env python3
"""Tests for sync_task_status.py.

Run: python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py -v
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sync_task_status import (
    epic_of, expected_epic, now_iso, parse_frontmatter, parse_worktree_list,
    set_frontmatter_field, task_targets,
)

TASK_TEXT = '''---
id: "task_1_setup"
status: "todo"
priority: "high"
assignee: null
epic: "logging-refactor"
dueDate: null
created: "2026-09-01T09:00:00Z"
modified: "2026-09-01T09:00:00Z"
completedAt: null
labels: ["architecture"]
order: "a1"
---

# Task 1: Setup

## Dependencies & Blockers
- None.
'''


class SetFrontmatterFieldTests(unittest.TestCase):
    def test_replaces_existing_key(self):
        out = set_frontmatter_field(TASK_TEXT, "status", "in-progress")
        self.assertIn('status: "in-progress"', out)
        self.assertNotIn('status: "todo"', out)

    def test_preserves_every_other_key(self):
        out = set_frontmatter_field(TASK_TEXT, "status", "done")
        for line in ('id: "task_1_setup"', 'priority: "high"', 'assignee: null',
                     'epic: "logging-refactor"', 'labels: ["architecture"]', 'order: "a1"'):
            self.assertIn(line, out)

    def test_preserves_body_byte_for_byte(self):
        out = set_frontmatter_field(TASK_TEXT, "status", "review")
        body = out.split("---\n", 2)[2]
        self.assertEqual(body, TASK_TEXT.split("---\n", 2)[2])

    def test_inserts_missing_key_after_status(self):
        text = '---\nid: "t"\nstatus: "todo"\n---\n\n# T\n'
        out = set_frontmatter_field(text, "completedAt", "2026-09-14T10:00:00Z")
        self.assertIn('status: "todo"\ncompletedAt: "2026-09-14T10:00:00Z"', out)

    def test_file_without_frontmatter_is_untouched(self):
        text = "# Just a heading\n\nSome prose.\n"
        self.assertEqual(set_frontmatter_field(text, "status", "done"), text)

    def test_does_not_touch_body_occurrences_of_the_key(self):
        text = '---\nstatus: "todo"\n---\n\nThe status: "todo" shown above is the source of truth.\n'
        out = set_frontmatter_field(text, "status", "done")
        self.assertIn('The status: "todo" shown above', out)


class NowIsoTests(unittest.TestCase):
    def test_utc_zulu_seconds_precision(self):
        stamp = now_iso()
        self.assertTrue(stamp.endswith("Z"), stamp)
        self.assertNotIn("+00:00", stamp)
        self.assertEqual(len(stamp), 20, stamp)  # 2026-09-14T10:23:45Z


class ParseFrontmatterTests(unittest.TestCase):
    def test_reads_quoted_values(self):
        self.assertEqual(parse_frontmatter(TASK_TEXT)["epic"], "logging-refactor")

    def test_missing_frontmatter_is_empty(self):
        self.assertEqual(parse_frontmatter("# Nope\n"), {})


WORKTREE_LIST = '''worktree /Users/dev/project
HEAD 1111111111111111111111111111111111111111
branch refs/heads/develop

worktree /Users/dev/project/.worktrees/logging_refactor
HEAD 2222222222222222222222222222222222222222
branch refs/heads/epic/logging-refactor
'''


def make_task(path: Path, *, epic: str, status: str = "todo") -> None:
    """Write a minimal but realistic task file at `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'---\nid: "{path.stem}"\nstatus: "{status}"\npriority: "high"\n'
        f'epic: "{epic}"\nmodified: "2026-09-01T09:00:00Z"\ncompletedAt: null\n---\n\n'
        f"# {path.stem}\n"
    )


def make_checkout(root: Path, *, epic_dir: str, epic: str, task_id: str, status: str = "todo") -> None:
    """Create both copies of one task inside one checkout root."""
    make_task(root / ".devtool" / "features" / f"{task_id}.md", epic=epic, status=status)
    make_task(root / ".devtool" / "epic" / epic_dir / f"{task_id}.md", epic=epic, status=status)


class ParseWorktreeListTests(unittest.TestCase):
    def test_extracts_roots_in_git_order(self):
        roots = parse_worktree_list(WORKTREE_LIST)
        self.assertEqual(
            roots,
            [Path("/Users/dev/project"), Path("/Users/dev/project/.worktrees/logging_refactor")],
        )

    def test_main_worktree_is_first(self):
        self.assertEqual(parse_worktree_list(WORKTREE_LIST)[0], Path("/Users/dev/project"))

    def test_single_checkout(self):
        self.assertEqual(parse_worktree_list("worktree /solo\nHEAD abc\n"), [Path("/solo")])

    def test_empty_output(self):
        self.assertEqual(parse_worktree_list(""), [])

    def test_path_containing_spaces(self):
        self.assertEqual(parse_worktree_list("worktree /Users/dev/My Project\n"),
                         [Path("/Users/dev/My Project")])


class TaskTargetsTests(unittest.TestCase):
    def test_finds_both_copies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_checkout(root, epic_dir="logging_refactor", epic="logging-refactor", task_id="task_1_setup")
            found = task_targets(root, "task_1_setup")
            self.assertEqual(len(found), 2)
            self.assertIn(root / ".devtool" / "features" / "task_1_setup.md", found)
            self.assertIn(root / ".devtool" / "epic" / "logging_refactor" / "task_1_setup.md", found)

    def test_missing_task_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(task_targets(Path(tmp), "task_9_absent"), [])

    def test_matches_same_task_id_under_two_epics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_checkout(root, epic_dir="logging_refactor", epic="logging-refactor", task_id="task_1_setup")
            make_task(root / ".devtool" / "epic" / "payments" / "task_1_setup.md", epic="payments")
            self.assertEqual(len(task_targets(root, "task_1_setup")), 3)


class ExpectedEpicTests(unittest.TestCase):
    def test_reads_epic_from_features_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_checkout(root, epic_dir="logging_refactor", epic="logging-refactor", task_id="task_1_setup")
            self.assertEqual(expected_epic([root], "task_1_setup"), "logging-refactor")

    def test_returns_none_when_no_features_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(expected_epic([Path(tmp)], "task_1_setup"))

    def test_epic_of_reads_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task_1_setup.md"
            make_task(path, epic="payments")
            self.assertEqual(epic_of(path), "payments")


if __name__ == "__main__":
    unittest.main()
