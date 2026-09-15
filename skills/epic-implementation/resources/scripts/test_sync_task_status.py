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
    archive_epic_tasks, archive_superpowers_docs, board_tally, epic_of,
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
            text = (roots[0] / ".devtool/features/task_1_setup.md").read_text()
            self.assertNotIn("completedAt: null", text)
            self.assertIn('completedAt: "20', text)

    def test_completed_at_resets_to_null_when_leaving_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._two_checkouts(tmp)
            sync_task(roots, "task_1_setup", "done")
            self.assertNotIn("completedAt: null",
                             (roots[0] / ".devtool/features/task_1_setup.md").read_text())
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


if __name__ == "__main__":
    unittest.main()
