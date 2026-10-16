#!/usr/bin/env python3
"""Tests for sync_task_status.py.

Run: python3 skills/dev-implementation/resources/scripts/test_sync_task_status.py -v
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sync_task_status import (
    archive_all_done_epics, archive_epic_tasks, archive_superpowers_docs, board_tally, epic_of,
    expected_epic, find_epic_slug, fix_epic_overview_links,
    fix_task_markdown_links, now_iso, parse_frontmatter,
    parse_worktree_list, set_frontmatter_field, sync_epic, sync_task, task_targets,
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


class SyncTaskTests(unittest.TestCase):
    def _two_checkouts(self, tmp: str) -> list[Path]:
        main, wt = Path(tmp) / "main", Path(tmp) / "wt"
        for root in (main, wt):
            make_checkout(root, epic_dir="logging_refactor", epic="logging-refactor",
                          task_id="task_1_setup")
        return [main, wt]

    def test_done_moves_the_features_copy_into_done_in_every_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._two_checkouts(tmp)
            written, _ = sync_task(roots, "task_1_setup", "done")
            for root in roots:
                features = root / ".devtool" / "features"
                moved = features / "done" / "task_1_setup.md"
                mirror = root / ".devtool" / "epic" / "logging_refactor" / "task_1_setup.md"
                self.assertFalse((features / "task_1_setup.md").exists())
                self.assertIn('status: "done"', moved.read_text())
                self.assertIn(moved, written)
                self.assertIn('status: "done"', mirror.read_text())

    def test_leaving_done_moves_the_features_copy_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._two_checkouts(tmp)
            sync_task(roots, "task_1_setup", "done")
            sync_task(roots, "task_1_setup", "in-progress")
            for root in roots:
                features = root / ".devtool" / "features"
                self.assertFalse((features / "done" / "task_1_setup.md").exists())
                self.assertIn('status: "in-progress"', (features / "task_1_setup.md").read_text())

    def test_done_replaces_a_stale_copy_already_in_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._two_checkouts(tmp)
            for root in roots:
                make_task(root / ".devtool" / "features" / "done" / "task_1_setup.md",
                          epic="logging-refactor", status="todo")
            sync_task(roots, "task_1_setup", "done")
            for root in roots:
                features = root / ".devtool" / "features"
                self.assertFalse((features / "task_1_setup.md").exists())
                self.assertIn('status: "done"', (features / "done" / "task_1_setup.md").read_text())

    def test_writes_all_four_copies(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._two_checkouts(tmp)
            written, notes = sync_task(roots, "task_1_setup", "in-progress")
            self.assertEqual(len(written), 4)
            self.assertEqual(notes, [])
            for path in written:
                self.assertIn('status: "in-progress"', path.read_text())

    def test_modified_advances_on_every_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._two_checkouts(tmp)
            written, _ = sync_task(roots, "task_1_setup", "review")
            for path in written:
                self.assertNotIn('modified: "2026-09-01T09:00:00Z"', path.read_text())
                self.assertIn("modified:", path.read_text())

    def test_completed_at_only_on_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._two_checkouts(tmp)
            sync_task(roots, "task_1_setup", "review")
            self.assertIn("completedAt: null",
                          (roots[0] / ".devtool/features/task_1_setup.md").read_text())
            sync_task(roots, "task_1_setup", "done")
            text = (roots[0] / ".devtool/features/done/task_1_setup.md").read_text()
            self.assertNotIn("completedAt: null", text)
            self.assertIn('completedAt: "20', text)

    def test_completed_at_resets_to_null_when_leaving_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._two_checkouts(tmp)
            sync_task(roots, "task_1_setup", "done")
            self.assertNotIn("completedAt: null",
                             (roots[0] / ".devtool/features/done/task_1_setup.md").read_text())
            sync_task(roots, "task_1_setup", "in-progress")
            text = (roots[0] / ".devtool/features/task_1_setup.md").read_text()
            self.assertIn("completedAt: null", text)

    def test_skips_same_task_id_under_a_different_epic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_checkout(root, epic_dir="logging_refactor", epic="logging-refactor",
                          task_id="task_1_setup")
            intruder = root / ".devtool" / "epic" / "payments" / "task_1_setup.md"
            make_task(intruder, epic="payments")
            written, notes = sync_task([root], "task_1_setup", "done")
            self.assertEqual(len(written), 2)
            self.assertNotIn(intruder, written)
            self.assertEqual(len(notes), 1)
            self.assertIn("payments", notes[0])
            self.assertIn('status: "todo"', intruder.read_text())

    def test_checkout_missing_the_task_is_skipped_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            main = Path(tmp) / "main"
            make_checkout(main, epic_dir="logging_refactor", epic="logging-refactor",
                          task_id="task_1_setup")
            written, _ = sync_task([main, Path(tmp) / "empty"], "task_1_setup", "done")
            self.assertEqual(len(written), 2)

    def test_no_copies_anywhere_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            written, notes = sync_task([Path(tmp)], "task_9_absent", "done")
            self.assertEqual(written, [])
            self.assertEqual(notes, [])


class BoardTallyTests(unittest.TestCase):
    def test_counts_by_status_for_one_epic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            features = root / ".devtool" / "features"
            make_task(features / "task_1_a.md", epic="logging-refactor", status="done")
            make_task(features / "task_2_b.md", epic="logging-refactor", status="done")
            make_task(features / "task_3_c.md", epic="logging-refactor", status="in-progress")
            make_task(features / "task_4_d.md", epic="logging-refactor", status="todo")
            make_task(features / "task_5_e.md", epic="payments", status="todo")
            counts = board_tally([root], "logging-refactor")
            self.assertEqual(counts["done"], 2)
            self.assertEqual(counts["in-progress"], 1)
            self.assertEqual(counts["todo"], 1)
            self.assertEqual(counts["backlog"], 0)
            self.assertEqual(counts["review"], 0)

    def test_counts_once_not_per_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = [Path(tmp) / "main", Path(tmp) / "wt"]
            for root in roots:
                make_task(root / ".devtool" / "features" / "task_1_a.md",
                          epic="logging-refactor", status="done")
            self.assertEqual(board_tally(roots, "logging-refactor")["done"], 1)

    def test_unknown_status_value_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_task(root / ".devtool" / "features" / "task_1_a.md",
                      epic="logging-refactor", status="blocked")
            self.assertEqual(sum(board_tally([root], "logging-refactor").values()), 0)


class SyncEpicTests(unittest.TestCase):
    def test_updates_both_en_and_vi_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            epic_dir = root / ".devtool" / "epic" / "logging_refactor"
            epic_dir.mkdir(parents=True, exist_ok=True)
            en_doc = epic_dir / "logging_refactor.en.md"
            vi_doc = epic_dir / "logging_refactor.vi.md"
            en_doc.write_text("# Epic: Logging Refactor\n\n## 1. Meta Data\n- **Status**: Planned\n")
            vi_doc.write_text("# Epic: Tái cấu trúc Logging\n\n## 1. Meta Data\n- **Status**: Planned\n")

            matched, written = sync_epic([root], "logging_refactor", "In Progress")
            self.assertEqual(len(matched), 2)
            self.assertEqual(len(written), 2)
            self.assertIn("- **Status**: In Progress", en_doc.read_text())
            self.assertIn("- **Status**: In Progress", vi_doc.read_text())

    def test_updates_a_status_line_with_the_colon_inside_the_bold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            epic_dir = root / ".devtool" / "epic" / "logging_refactor"
            epic_dir.mkdir(parents=True, exist_ok=True)
            en_doc = epic_dir / "logging_refactor.en.md"
            vi_doc = epic_dir / "logging_refactor.vi.md"
            en_doc.write_text("# Epic: Logging Refactor\n\n- **Epic:** `logging_refactor`\n- **Status:** Planned\n")
            vi_doc.write_text("# Epic: Tái cấu trúc\n\n- **Trạng thái:** Đã lên kế hoạch\n")

            matched, written = sync_epic([root], "logging_refactor", "Done")
            self.assertEqual(len(written), 2)
            self.assertIn("- **Status:** Done", en_doc.read_text())
            self.assertIn("- **Epic:** `logging_refactor`", en_doc.read_text())
            self.assertIn("- **Trạng thái:** Done", vi_doc.read_text())

    def test_handles_vietnamese_meta_data_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            epic_dir = root / ".devtool" / "epic" / "logging_refactor"
            epic_dir.mkdir(parents=True, exist_ok=True)
            vi_doc = epic_dir / "logging_refactor.vi.md"
            vi_doc.write_text("# Epic: Tái cấu trúc\n\n- **Trạng thái**: Đã lên kế hoạch\n")

            matched, written = sync_epic([root], "logging_refactor", "Đang thực hiện")
            self.assertEqual(len(matched), 1)
            self.assertEqual(len(written), 1)
            self.assertIn("- **Trạng thái**: Đang thực hiện", vi_doc.read_text())

    def test_missing_doc_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matched, written = sync_epic([root], "non_existent", "In Progress")
            self.assertEqual(matched, [])
            self.assertEqual(written, [])


class LinkFixTests(unittest.TestCase):
    def test_fix_task_markdown_links(self):
        text = (
            "Epic: [logging-refactor](../epic/logging_refactor/logging_refactor.en.md)\n"
            "- **Blocks**: [Task 2](../../features/task_2_b.md), [Task 3](../../features/done/task_3_c.md).\n"
        )
        out = fix_task_markdown_links(text, "logging_refactor")
        self.assertIn("Epic: [logging-refactor](logging_refactor.en.md)", out)
        self.assertIn("- **Blocks**: [Task 2](task_2_b.md), [Task 3](task_3_c.md).", out)

    def test_fix_epic_overview_links(self):
        text = (
            "## 8. Kanban Tasks Breakdown\n"
            "- [Task 1: Setup](../../features/task_1_setup.md)\n"
            "- [Task 2: Done](../../features/done/task_2_done.md)\n"
        )
        out = fix_epic_overview_links(text)
        self.assertIn("- [Task 1: Setup](task_1_setup.md)", out)
        self.assertIn("- [Task 2: Done](task_2_done.md)", out)


class ArchiveEpicTasksTests(unittest.TestCase):
    def test_archive_done_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            epic_dir = root / ".devtool" / "epic" / "logging_refactor"
            epic_dir.mkdir(parents=True, exist_ok=True)
            en_doc = epic_dir / "logging_refactor.en.md"
            en_doc.write_text(
                "# Logging Refactor\n\n## 1. Meta Data\n- **Epic**: logging-refactor\n- **Status**: In Progress\n\n"
                "## 8. Tasks\n- [Task 1](../../features/task_1_setup.md)\n"
            )

            done_dir = root / ".devtool" / "features" / "done"
            done_dir.mkdir(parents=True, exist_ok=True)
            task_file = done_dir / "task_1_setup.md"
            task_file.write_text(
                '---\nid: "task_1_setup"\nstatus: "done"\nepic: "logging-refactor"\n---\n\n'
                "Epic: [logging-refactor](../epic/logging_refactor/logging_refactor.en.md)\n"
                "- **Blocks**: [Task 2](../../features/task_2_b.md).\n"
            )

            archived, cleaned = archive_epic_tasks([root], "logging_refactor")
            self.assertEqual(len(archived), 1)
            self.assertEqual(len(cleaned), 1)

            dest_task = epic_dir / "task_1_setup.md"
            self.assertTrue(dest_task.is_file())
            self.assertFalse(task_file.exists())
            self.assertTrue((done_dir / ".gitkeep").is_file())

            content = dest_task.read_text()
            self.assertIn("[logging-refactor](logging_refactor.en.md)", content)
            self.assertIn("[Task 2](task_2_b.md)", content)

            # Check overview doc links updated
            self.assertIn("- [Task 1](task_1_setup.md)", en_doc.read_text())

    def test_sync_epic_done_triggers_archival(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            epic_dir = root / ".devtool" / "epic" / "logging_refactor"
            epic_dir.mkdir(parents=True, exist_ok=True)
            en_doc = epic_dir / "logging_refactor.en.md"
            en_doc.write_text(
                "# Logging\n\n## 1. Meta Data\n- **Epic**: logging-refactor\n- **Status**: In Progress\n\n"
                "## 8. Tasks\n- [Task 1](../../features/done/task_1_setup.md)\n"
            )

            done_dir = root / ".devtool" / "features" / "done"
            done_dir.mkdir(parents=True, exist_ok=True)
            task_file = done_dir / "task_1_setup.md"
            task_file.write_text(
                '---\nid: "task_1_setup"\nstatus: "done"\nepic: "logging-refactor"\n---\n'
            )

            matched, written = sync_epic([root], "logging_refactor", "Done")
            self.assertEqual(len(written), 1)
            self.assertTrue((epic_dir / "task_1_setup.md").is_file())
            self.assertFalse(task_file.exists())
            self.assertTrue((done_dir / ".gitkeep").is_file())
            self.assertIn("- [Task 1](task_1_setup.md)", en_doc.read_text())

    def test_archive_superpowers_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            epic_dir = root / ".devtool" / "epic" / "logging_refactor"
            epic_dir.mkdir(parents=True, exist_ok=True)
            sp_plans = root / "docs" / "superpowers" / "plans"
            sp_plans.mkdir(parents=True, exist_ok=True)
            plan_file = sp_plans / "2026-09-14-logging-refactor.md"
            plan_file.write_text("# Old plan\n")

            moved = archive_superpowers_docs(root, "logging_refactor", "logging-refactor")
            self.assertEqual(len(moved), 1)
            self.assertTrue((epic_dir / "2026-09-14-logging-refactor.md").is_file())
            self.assertFalse(plan_file.exists())
            self.assertTrue((sp_plans / ".gitkeep").is_file())

    def test_expected_epic_and_tally_with_archived_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            epic_dir = root / ".devtool" / "epic" / "logging_refactor"
            epic_dir.mkdir(parents=True, exist_ok=True)
            task_file = epic_dir / "task_1_setup.md"
            make_task(task_file, epic="logging-refactor", status="done")

            self.assertEqual(expected_epic([root], "task_1_setup"), "logging-refactor")
            tally = board_tally([root], "logging-refactor")
            self.assertEqual(tally["done"], 1)

    def test_archive_all_done_epics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            epic_dir = root / ".devtool" / "epic" / "logging_refactor"
            epic_dir.mkdir(parents=True, exist_ok=True)
            en_doc = epic_dir / "logging_refactor.en.md"
            en_doc.write_text(
                "# Logging\n\n## 1. Meta Data\n- **Epic**: logging-refactor\n- **Status**: In Progress\n\n"
                "## 8. Tasks\n- [Task 1](../../features/done/task_1_setup.md)\n"
            )

            done_dir = root / ".devtool" / "features" / "done"
            done_dir.mkdir(parents=True, exist_ok=True)
            task_file = done_dir / "task_1_setup.md"
            task_file.write_text(
                '---\nid: "task_1_setup"\nstatus: "done"\nepic: "logging-refactor"\n---\n'
            )

            archived = archive_all_done_epics([root])
            self.assertEqual(archived, ["logging_refactor"])
            self.assertTrue((epic_dir / "task_1_setup.md").is_file())
            self.assertFalse(task_file.exists())
            self.assertTrue((done_dir / ".gitkeep").is_file())
            self.assertIn("Status**: Done", en_doc.read_text())

    def test_archive_all_done_epics_with_backtick_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            epic_dir = root / ".devtool" / "epic" / "logging_refactor"
            epic_dir.mkdir(parents=True, exist_ok=True)
            en_doc = epic_dir / "logging_refactor.en.md"
            en_doc.write_text(
                "# Logging\n\n## 1. Meta Data\n- **Epic**: `logging-refactor`\n- **Status**: In Progress\n\n"
                "## 8. Tasks\n- [Task 1](../../features/done/task_1_setup.md)\n"
            )

            done_dir = root / ".devtool" / "features" / "done"
            done_dir.mkdir(parents=True, exist_ok=True)
            task_file = done_dir / "task_1_setup.md"
            task_file.write_text(
                '---\nid: "task_1_setup"\nstatus: "done"\nepic: "logging-refactor"\n---\n'
            )

            archived = archive_all_done_epics([root])
            self.assertEqual(archived, ["logging_refactor"])
            self.assertTrue((epic_dir / "task_1_setup.md").is_file())
            self.assertFalse(task_file.exists())
            self.assertTrue((done_dir / ".gitkeep").is_file())
            self.assertIn("Status**: Done", en_doc.read_text())

    def test_archive_all_done_epics_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            done_dir = root / ".devtool" / "features" / "done"
            done_dir.mkdir(parents=True, exist_ok=True)
            (done_dir / ".gitkeep").touch()

            archived = archive_all_done_epics([root])
            self.assertEqual(archived, [])




SCRIPTS = Path(__file__).parent
SYNC = SCRIPTS / "sync_task_status.py"
RECORDER = SCRIPTS / "run_task_checks.py"
TICKS = "`" * 3
TASK_ID = "task_1_demo"
MIRROR = f".devtool/epic/demo/{TASK_ID}.md"
FEATURE = f".devtool/features/{TASK_ID}.md"
DONE_FEATURE = f".devtool/features/done/{TASK_ID}.md"
EVIDENCE = f".devtool/epic/demo/evidence/{TASK_ID}.json"
TABLE = (
    "| ID | Phase | Command | Expect | Needs |\n|----|-------|---------|--------|-------|\n"
    "| V1 | RED | `bash check.sh` | exit 1 | — |\n"
    '| V2 | GREEN | `bash check.sh` | exit 0; contains "OK" | — |\n'
    "| V3 | TIER-C | `bash report.sh` | exit 0; results build/r.xml | — |\n"
)
REPORT = ("<testsuite>"
          '<testcase classname="Demo" name="test_demo_hp_01_one"/>'
          '<testcase classname="Demo" name="test_demo_ec_01_two"/>'
          "</testsuite>")


def task_file(verification: bool) -> str:
    text = ('---\nid: "task_1_demo"\nstatus: "in-progress"\nepic: "demo"\ncreated: "2026-01-01T00:00:00Z"\n'
            'modified: "2026-01-01T00:00:00Z"\ncompletedAt: null\n---\n\n# Task 1\n\n'
            "## Files\n\nAllowed files:\n- `feature.txt` (new)\n\n"
            "## BDD\n\nCovers: DEMO-HP-01, DEMO-EC-01\n\n")
    if verification:
        text += f"## Verification\n\n{TABLE}\n"
    return text + "## Definition of Done\n\n- done (V2)\n"


def run_py(script: Path, cwd: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv], cwd=cwd, capture_output=True, text=True)


def git(cwd: Path, *argv: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *argv], capture_output=True, text=True, check=True)


class DoneGateCase(unittest.TestCase):
    """A main checkout plus an epic worktree, with the two CLIs run as subprocesses."""

    def build(self, code_epic: bool = True, verification: bool = True) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        base = Path(directory.name).resolve()
        self.main, self.wt = base / "main", base / "wt"
        self.main.mkdir()
        git(self.main, "init", "-q", "-b", "main")
        git(self.main, "config", "user.email", "demo@example.com")
        git(self.main, "config", "user.name", "Demo")
        overview = "# Demo\n\n- **Epic**: demo\n\n" + ("Integration test roots: tests\n" if code_epic else "")
        files = {
            ".gitignore": "build/\n",
            "check.sh": "[ -f feature.txt ] && echo OK\n",
            "report.sh": f"mkdir -p build && printf '%s' '{REPORT}' > build/r.xml\n",
            ".devtool/epic/demo/demo.en.md": overview,
            ".devtool/epic/demo/bdd_scenarios.en.md": (
                f"{TICKS}gherkin\nScenario: [DEMO-HP-01] One\nScenario: [DEMO-EC-01] Two\n{TICKS}\n"),
            MIRROR: task_file(verification),
            FEATURE: task_file(verification),
        }
        for relative, text in files.items():
            path = self.main / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        git(self.main, "add", "-A")
        git(self.main, "commit", "-q", "-m", "base")
        git(self.main, "worktree", "add", "-q", "-b", "epic/demo", str(self.wt))

    def record(self) -> None:
        mirror = self.wt / MIRROR
        self.assertEqual(run_py(RECORDER, self.wt, "red", str(mirror)).returncode, 0)
        (self.wt / "feature.txt").write_text("done\n", encoding="utf-8")
        self.assertEqual(run_py(RECORDER, self.wt, "verify", str(mirror)).returncode, 0)

    def edit_evidence(self, change) -> None:
        path = self.wt / EVIDENCE
        data = json.loads(path.read_text(encoding="utf-8"))
        change(data["runs"])
        path.write_text(json.dumps(data), encoding="utf-8")

    def copies(self) -> dict[str, str]:
        copies = {}
        for root in (self.main, self.wt):
            feature = FEATURE if (root / FEATURE).exists() else DONE_FEATURE
            for rel in (MIRROR, feature):
                copies[f"{root.name}/{rel}"] = (root / rel).read_text(encoding="utf-8")
        return copies

    def done(self, cwd: Path) -> subprocess.CompletedProcess:
        return run_py(SYNC, cwd, "task", TASK_ID, "done")

    def assert_refused(self, result: subprocess.CompletedProcess, *fragments: str) -> None:
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(f"refused: {TASK_ID} cannot be marked done", result.stderr)
        for fragment in fragments:
            self.assertIn(fragment, result.stderr)

    def refuse_leaves_copies(self, *fragments: str) -> None:
        before = self.copies()
        self.assert_refused(self.done(self.wt), *fragments)
        self.assertEqual(self.copies(), before)


class DoneGateTests(DoneGateCase):
    def test_vth_hp_03_matching_evidence_reaches_done(self):
        self.build()
        self.record()
        status = run_py(RECORDER, self.wt, "status", str(self.wt / MIRROR))
        self.assertEqual(status.returncode, 0, status.stdout)
        self.assertIn("done gate: PASS", status.stdout)
        result = self.done(self.wt)
        self.assertEqual(result.returncode, 0, result.stderr)
        for root in (self.main, self.wt):
            self.assertFalse((root / FEATURE).exists())
            self.assertTrue((root / DONE_FEATURE).exists())
        for text in self.copies().values():
            self.assertIn('status: "done"', text)
            self.assertNotIn('modified: "2026-01-01T00:00:00Z"', text)
            self.assertNotIn("completedAt: null", text)

    def test_vth_st_03_done_without_evidence_is_refused(self):
        self.build()
        self.refuse_leaves_copies("condition 1:", "not found in this checkout",
                                  "run the done gate in the epic worktree")

    def test_vth_st_04_edits_after_verification_are_refused(self):
        self.build()
        self.record()
        (self.wt / "feature.txt").write_text("changed\n", encoding="utf-8")
        self.refuse_leaves_copies("condition 4:")
        (self.wt / "feature.txt").write_text("done\n", encoding="utf-8")
        mirror = self.wt / MIRROR
        mirror.write_text(mirror.read_text(encoding="utf-8").replace(
            'exit 0; contains "OK"', 'exit 0; contains "OK!"'), encoding="utf-8")
        self.refuse_leaves_copies("condition 2:", "row V2: recorded expect differs from the table")

    def test_vth_st_05_red_that_did_not_precede_the_change_is_refused(self):
        self.build()
        self.record()
        recorded = json.loads((self.wt / EVIDENCE).read_text(encoding="utf-8"))["runs"]["red"]["tree"]
        self.edit_evidence(lambda runs: runs["red"].update(tree=runs["verify"]["tree"]))
        self.refuse_leaves_copies("condition 5:", "RED was not recorded before the change")
        self.edit_evidence(lambda runs: runs["red"].update(tree=recorded, finished="2999-01-01T00:00:00Z"))
        self.refuse_leaves_copies("condition 5:", "finished after the verify run started")

    def test_vth_st_06_only_code_epics_are_gated(self):
        self.build(verification=False)
        self.refuse_leaves_copies("retrofit required:", "has no Verification section")
        self.build(code_epic=False, verification=False)
        result = self.done(self.wt)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('status: "done"', (self.wt / DONE_FEATURE).read_text(encoding="utf-8"))

    def test_vth_st_07_covered_identifier_without_a_passing_case_is_refused(self):
        self.build()
        self.record()

        def drop_case(runs):
            row = next(r for r in runs["verify"]["rows"] if r["id"] == "V3")
            row["results"]["digest"]["cases"] = [
                c for c in row["results"]["digest"]["cases"] if "demo_ec_01" not in c["name"]]

        self.edit_evidence(drop_case)
        self.refuse_leaves_copies("condition 6:", "DEMO-EC-01")

    def test_vth_ar_02_gate_from_checkout_without_evidence_writes_nothing(self):
        self.build()
        self.record()
        before = self.copies()
        result = self.done(self.main)
        self.assert_refused(result, "condition 1:", "run the done gate in the epic worktree")
        self.assertEqual(self.copies(), before)

    def test_done_from_a_checkout_lacking_the_task_is_refused(self):
        self.build()
        for rel in (MIRROR, FEATURE):
            (self.main / rel).unlink()
        before = (self.wt / FEATURE).read_text(encoding="utf-8")
        result = self.done(self.main)
        self.assert_refused(result, "run the done gate in the checkout that holds the task and its evidence "
                                    "(the epic worktree)")
        self.assertEqual((self.wt / FEATURE).read_text(encoding="utf-8"), before)

    def test_blocked_row_and_failed_scope_are_refused(self):
        self.build()
        self.record()

        def break_rows(runs):
            rows = {r["id"]: r for r in runs["verify"]["rows"]}
            rows["V3"].update(outcome="BLOCKED", reason="unset: X")
            rows["SCOPE"].update(outcome="FAIL", violations=["outside Allowed files: x"])

        self.edit_evidence(break_rows)
        self.refuse_leaves_copies("condition 3:", "V3", "condition 7:")

    def test_verify_recorded_after_committing_is_refused(self):
        self.build()
        self.record()
        git(self.wt, "add", "-A")
        git(self.wt, "commit", "-q", "-m", "[DEMO] Task 1 committed before the gate")
        self.assertEqual(run_py(RECORDER, self.wt, "verify", str(self.wt / MIRROR)).returncode, 0)
        self.refuse_leaves_copies("condition 4: verify saw no change outside .devtool — record verify before committing",
                                  "condition 5: red and verify were recorded on different commits")

    def test_red_and_verify_on_different_commits_is_refused(self):
        self.build()
        mirror = self.wt / MIRROR
        self.assertEqual(run_py(RECORDER, self.wt, "red", str(mirror)).returncode, 0)
        git(self.wt, "add", "-A")
        git(self.wt, "commit", "-q", "-m", "[DEMO] Unrelated commit between red and verify")
        (self.wt / "feature.txt").write_text("done\n", encoding="utf-8")
        self.assertEqual(run_py(RECORDER, self.wt, "verify", str(mirror)).returncode, 0)
        result = self.done(self.wt)
        self.assert_refused(result, "condition 5: red and verify were recorded on different commits")
        self.assertNotIn("condition 4:", result.stderr)

    def test_failed_row_no_longer_in_the_table_is_refused(self):
        self.build()
        self.record()

        def add_dropped_row(runs):
            runs["verify"]["rows"].append({"id": "V9", "phase": "GREEN", "outcome": "FAIL", "reason": "exit 1"})

        self.edit_evidence(add_dropped_row)
        self.refuse_leaves_copies("condition 2: verify row V9 is FAIL and no longer in the table")


if __name__ == "__main__":
    unittest.main()
