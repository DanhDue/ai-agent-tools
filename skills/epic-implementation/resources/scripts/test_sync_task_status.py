#!/usr/bin/env python3
"""Tests for sync_task_status.py.

Run: python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py -v
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sync_task_status import now_iso, parse_frontmatter, set_frontmatter_field

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


if __name__ == "__main__":
    unittest.main()
