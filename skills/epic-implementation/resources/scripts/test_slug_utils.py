#!/usr/bin/env python3
"""Tests for slug_utils.py."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from slug_utils import parse_frontmatter, sanitize_slug


class SanitizeSlugTests(unittest.TestCase):
    def test_handles_backticks(self):
        self.assertEqual(sanitize_slug("`flutter_super_app_template`"), "flutter_super_app_template")

    def test_handles_double_and_single_quotes(self):
        self.assertEqual(sanitize_slug('"logging-refactor"'), "logging-refactor")
        self.assertEqual(sanitize_slug("'logging-refactor'"), "logging-refactor")

    def test_handles_curly_smart_quotes(self):
        self.assertEqual(sanitize_slug("“super_app_governance”"), "super_app_governance")
        self.assertEqual(sanitize_slug("‘super_app_governance’"), "super_app_governance")

    def test_handles_markdown_bold_and_italics(self):
        self.assertEqual(sanitize_slug("**`flutter_super_app_template`**"), "flutter_super_app_template")
        self.assertEqual(sanitize_slug("*flutter_super_app_template*"), "flutter_super_app_template")

    def test_handles_markdown_links(self):
        self.assertEqual(
            sanitize_slug("[flutter_super_app_template](file:///path/to/hld.md)"),
            "flutter_super_app_template",
        )
        self.assertEqual(
            sanitize_slug("[`flutter_super_app_template`](file:///path/to/hld.md)"),
            "flutter_super_app_template",
        )

    def test_handles_html_tags_and_comments(self):
        self.assertEqual(
            sanitize_slug("<code>flutter_super_app_template</code>"),
            "flutter_super_app_template",
        )
        self.assertEqual(
            sanitize_slug("flutter_super_app_template <!-- epic identifier -->"),
            "flutter_super_app_template",
        )

    def test_handles_trailing_annotations_and_punctuation(self):
        self.assertEqual(
            sanitize_slug("flutter_super_app_template (Flutter Super App)"),
            "flutter_super_app_template",
        )
        self.assertEqual(
            sanitize_slug("`flutter_super_app_template`:"),
            "flutter_super_app_template",
        )
        self.assertEqual(
            sanitize_slug("`flutter_super_app_template`,"),
            "flutter_super_app_template",
        )

    def test_empty_or_none(self):
        self.assertIsNone(sanitize_slug(None))
        self.assertIsNone(sanitize_slug(""))
        self.assertIsNone(sanitize_slug("   "))


class ParseFrontmatterTests(unittest.TestCase):
    def test_parses_unquoted_and_quoted_values(self):
        text = '''---
id: "task_1"
epic: 'my-epic'
tag: `custom_tag`
unquoted: simple_val
---
# Content
'''
        fm = parse_frontmatter(text)
        self.assertEqual(fm["id"], "task_1")
        self.assertEqual(fm["epic"], "my-epic")
        self.assertEqual(fm["tag"], "custom_tag")
        self.assertEqual(fm["unquoted"], "simple_val")

    def test_missing_frontmatter(self):
        self.assertEqual(parse_frontmatter("# No frontmatter"), {})


if __name__ == "__main__":
    unittest.main()
