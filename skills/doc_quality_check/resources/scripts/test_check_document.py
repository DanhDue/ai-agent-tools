#!/usr/bin/env python3
"""Regression tests for lifecycle document contracts."""

import importlib.util
import pathlib
import tempfile
import unittest


MODULE_PATH = pathlib.Path(__file__).with_name("check_document.py")
SPEC = importlib.util.spec_from_file_location("check_document", MODULE_PATH)
CHECK_DOCUMENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK_DOCUMENT)


class DocumentContractTest(unittest.TestCase):
    def test_required_toc_applies_even_to_short_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "short.en.md"
            path.write_text("# Short\n\n## Only section\n\nContent.\n")

            findings = CHECK_DOCUMENT.check_file(path, require_toc=True)

        self.assertTrue(any("table of contents" in finding[2] for finding in findings))

    def test_required_toc_accepts_a_linked_contents_section(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "short.en.md"
            path.write_text(
                "# Short\n\n## Table of Contents\n\n- [Only section](#only-section)\n\n"
                "## Only section\n\nContent.\n"
            )

            findings = CHECK_DOCUMENT.check_file(path, require_toc=True)

        self.assertFalse(any("table of contents" in finding[2] for finding in findings))

    def test_required_toc_accepts_a_decorated_contents_heading(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "decorated.en.md"
            path.write_text(
                "# Short\n\n## 📑 Table of Contents\n\n- [Only section](#only-section)\n\n"
                "## Only section\n\nContent.\n"
            )

            findings = CHECK_DOCUMENT.check_file(path, require_toc=True)

        self.assertFalse(any("no table of contents heading" in finding[2] for finding in findings))

    def test_required_toc_reports_an_unlisted_section(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "incomplete.en.md"
            path.write_text(
                "# Incomplete\n\n## Table of Contents\n\n- [First](#first)\n\n"
                "## First\n\nContent.\n\n## Missing\n\nContent.\n"
            )

            findings = CHECK_DOCUMENT.check_file(path, require_toc=True)

        self.assertTrue(any("## Missing" in finding[2] for finding in findings))

    def test_required_toc_reports_an_unlisted_plan_task(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "plan.en.md"
            path.write_text(
                "# Plan\n\n## Table of Contents\n\n- [Tasks](#tasks)\n\n"
                "## Tasks\n\n### Task 1: Build it\n\nSteps.\n"
            )

            findings = CHECK_DOCUMENT.check_file(path, require_toc=True)

        self.assertTrue(any("### Task 1" in finding[2] for finding in findings))

    def test_bilingual_contract_reports_a_missing_translation(self):
        with tempfile.TemporaryDirectory() as directory:
            english = pathlib.Path(directory) / "design.en.md"
            english.write_text("# Design\n")

            findings = CHECK_DOCUMENT.check_language_pairs([english])

        self.assertTrue(any("design.vi.md" in finding[2] for finding in findings))

    def test_bilingual_contract_accepts_a_complete_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            english = pathlib.Path(directory) / "design.en.md"
            vietnamese = pathlib.Path(directory) / "design.vi.md"
            english.write_text("# Design\n")
            vietnamese.write_text("# Thiết kế\n")

            findings = CHECK_DOCUMENT.check_language_pairs([english, vietnamese])

        self.assertEqual([], findings)

    def test_bilingual_contract_requires_both_variants_in_the_same_check(self):
        with tempfile.TemporaryDirectory() as directory:
            english = pathlib.Path(directory) / "design.en.md"
            vietnamese = pathlib.Path(directory) / "design.vi.md"
            english.write_text("# Design\n")
            vietnamese.write_text("# Thiết kế\n")

            findings = CHECK_DOCUMENT.check_language_pairs([english])

        self.assertTrue(any("not included" in finding[2] for finding in findings))

    def test_bilingual_contract_reports_structural_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            english = pathlib.Path(directory) / "design.en.md"
            vietnamese = pathlib.Path(directory) / "design.vi.md"
            english.write_text("# Design\n\n## Goal\n\n## Risks\n")
            vietnamese.write_text("# Thiết kế\n\n## Mục tiêu\n")

            findings = CHECK_DOCUMENT.check_language_pairs([english, vietnamese])

    def test_mermaid_legacy_graph_syntax_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "doc.en.md"
            path.write_text("# Doc\n\n```mermaid\ngraph TD\n    A --> B\n```\n")
            findings = CHECK_DOCUMENT.check_file(path)
        self.assertTrue(any("legacy Mermaid syntax" in finding[2] for finding in findings))

    def test_modern_mermaid_flowchart_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "doc.en.md"
            path.write_text("# Doc\n\n```mermaid\nflowchart TD\n    A[\"Node A\"] --> B[\"Node B\"]\n```\n")
            findings = CHECK_DOCUMENT.check_file(path)
        self.assertEqual([], findings)

    def test_fenced_code_block_missing_language_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "doc.en.md"
            path.write_text("# Doc\n\n```\necho hello\n```\n")
            findings = CHECK_DOCUMENT.check_file(path)
        self.assertTrue(any("missing language tag" in finding[2] for finding in findings))

    def test_heading_missing_space_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "doc.en.md"
            path.write_text("#Doc\n\nContent\n")
            findings = CHECK_DOCUMENT.check_file(path)
        self.assertTrue(any("no space after '#'" in finding[2] for finding in findings))


if __name__ == "__main__":
    unittest.main()

