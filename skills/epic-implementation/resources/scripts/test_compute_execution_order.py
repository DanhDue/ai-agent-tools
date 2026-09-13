#!/usr/bin/env python3
"""Tests for compute_execution_order.py.

Run: python3 .agents/skills/epic-implementation/resources/scripts/test_compute_execution_order.py -v
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compute_execution_order import compute_layers, load_tasks, parse_blockers, parse_soft_notes, scan_tasks


def write_task(directory: Path, filename: str, *, epic: str, priority: str, title: str, dependencies_body: str) -> None:
    (directory / filename).write_text(
        f'---\nid: "{filename[:-3]}"\nstatus: "todo"\npriority: "{priority}"\nepic: "{epic}"\n---\n'
        f"# {title}\n\n## Dependencies & Blockers\n{dependencies_body}\n"
    )


class ParseBlockersTests(unittest.TestCase):
    def test_single_blocker(self):
        section = "- **Dependencies**: Blocked by [Task 2](task_2_core_interfaces.md) (needs interfaces)."
        self.assertEqual(parse_blockers(section), ["task_2_core_interfaces"])

    def test_two_blockers_on_one_line(self):
        section = (
            "- **Dependencies**: Blocked by [Task 4](task_4_appenders_di.md) "
            "(reason) and [Task 5](task_5_network_tracing.md) (reason)."
        )
        self.assertEqual(parse_blockers(section), ["task_4_appenders_di", "task_5_network_tracing"])

    def test_no_blockers(self):
        self.assertEqual(parse_blockers("- **Dependencies**: None.\n- **Blockers**: None."), [])

    def test_link_without_blocked_by_is_ignored(self):
        section = "- **New dependency**: confirm the key used by [Task 6](task_6_settings_ui.md)."
        self.assertEqual(parse_blockers(section), [])


class ParseSoftNotesTests(unittest.TestCase):
    def test_recommended_note_captured(self):
        section = (
            "- **Dependencies**: Blocked by [Task 2](task_2_core_interfaces.md). "
            "Recommended to do after the core Flutter-side tasks (1-4) are complete."
        )
        notes = parse_soft_notes(section)
        self.assertEqual(len(notes), 1)
        self.assertIn("Recommended to do after the core Flutter-side tasks (1-4)", notes[0])

    def test_new_dependency_note_captured(self):
        section = (
            "- **New dependency**: the exact `shared_preferences` key/encoding "
            "[Task 6](task_6_settings_ui.md) uses for `logging.appender_toggles` must be confirmed."
        )
        notes = parse_soft_notes(section)
        self.assertEqual(len(notes), 1)
        self.assertIn("New dependency", notes[0])

    def test_no_note_when_absent(self):
        self.assertEqual(parse_soft_notes("- **Dependencies**: Blocked by [Task 1](task_1.md)."), [])


class ScanTasksTests(unittest.TestCase):
    """The scan report is what stops an unparseable task file from vanishing silently."""

    def test_reports_scanned_matched_and_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_task(directory, "task_1_a.md", epic="demo", priority="high", title="Task 1: A",
                       dependencies_body="- **Dependencies**: None.")
            write_task(directory, "task_9_other.md", epic="other-epic", priority="high", title="Task 9: Other",
                       dependencies_body="- **Dependencies**: None.")
            (directory / "task_2_broken.md").write_text("no frontmatter at all\n# Task 2: Broken\n")

            tasks, scanned, skipped = scan_tasks(directory, "demo")
            self.assertEqual(list(tasks.keys()), ["task_1_a"])
            self.assertEqual(len(scanned), 3)
            self.assertEqual(
                sorted(p.name for p in skipped),
                ["task_2_broken.md", "task_9_other.md"],
            )

    def test_load_tasks_matches_scan_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_task(directory, "task_1_a.md", epic="demo", priority="high", title="Task 1: A",
                       dependencies_body="- **Dependencies**: None.")
            self.assertEqual(load_tasks(directory, "demo"), scan_tasks(directory, "demo")[0])


class ComputeLayersTests(unittest.TestCase):
    def test_linear_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_task(directory, "task_1_a.md", epic="demo", priority="high", title="Task 1: A",
                       dependencies_body="- **Dependencies**: None.")
            write_task(directory, "task_2_b.md", epic="demo", priority="high", title="Task 2: B",
                       dependencies_body="- **Dependencies**: Blocked by [Task 1](task_1_a.md).")
            tasks = load_tasks(directory, "demo")
            self.assertEqual(compute_layers(tasks), [["task_1_a"], ["task_2_b"]])

    def test_independent_tasks_share_a_layer_and_sort_by_priority_then_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_task(directory, "task_1_a.md", epic="demo", priority="high", title="Task 1: A",
                       dependencies_body="- **Dependencies**: None.")
            write_task(directory, "task_2_b.md", epic="demo", priority="medium", title="Task 2: B",
                       dependencies_body="- **Dependencies**: Blocked by [Task 1](task_1_a.md).")
            write_task(directory, "task_3_c.md", epic="demo", priority="high", title="Task 3: C",
                       dependencies_body="- **Dependencies**: Blocked by [Task 1](task_1_a.md).")
            tasks = load_tasks(directory, "demo")
            layers = compute_layers(tasks)
            self.assertEqual(layers[0], ["task_1_a"])
            self.assertEqual(layers[1], ["task_3_c", "task_2_b"])

    def test_ignores_tasks_from_other_epics(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_task(directory, "task_1_a.md", epic="demo", priority="high", title="Task 1: A",
                       dependencies_body="- **Dependencies**: None.")
            write_task(directory, "task_9_other.md", epic="other-epic", priority="high", title="Task 9: Other",
                       dependencies_body="- **Dependencies**: None.")
            tasks = load_tasks(directory, "demo")
            self.assertEqual(list(tasks.keys()), ["task_1_a"])

    def test_cycle_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_task(directory, "task_1_a.md", epic="demo", priority="high", title="Task 1: A",
                       dependencies_body="- **Dependencies**: Blocked by [Task 2](task_2_b.md).")
            write_task(directory, "task_2_b.md", epic="demo", priority="high", title="Task 2: B",
                       dependencies_body="- **Dependencies**: Blocked by [Task 1](task_1_a.md).")
            tasks = load_tasks(directory, "demo")
            with self.assertRaises(ValueError):
                compute_layers(tasks)

    def test_missing_dependency_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_task(directory, "task_1_a.md", epic="demo", priority="high", title="Task 1: A",
                       dependencies_body="- **Dependencies**: Blocked by [Task 9](task_9_missing.md).")
            tasks = load_tasks(directory, "demo")
            with self.assertRaises(ValueError):
                compute_layers(tasks)


class RealLoggingRefactorEpicTests(unittest.TestCase):
    """Integration test against this repo's actual logging-refactor tasks.

    Pins the CURRENT state of `.devtool/features/task_*.md` for the
    `logging-refactor` epic. If a task's priority or "Blocked by" line
    changes later, update the expected layers below to match -- that is
    expected maintenance, not a bug in the script.
    """

    FEATURES_DIR = Path(__file__).resolve().parents[5] / ".devtool" / "features"

    def test_computed_layers_match_current_epic_state(self):
        tasks = load_tasks(self.FEATURES_DIR, "logging-refactor")
        layers = compute_layers(tasks)
        self.assertEqual(
            layers,
            [
                ["task_1_create_package"],
                ["task_2_core_interfaces"],
                ["task_3_log_manager", "task_5_network_tracing", "task_7_native_bridge"],
                ["task_4_appenders_di", "task_6_settings_ui"],
                ["task_8_refactor_codebase"],
            ],
        )

    def test_task_7_recommended_note_is_surfaced_not_silently_applied(self):
        tasks = load_tasks(self.FEATURES_DIR, "logging-refactor")
        notes = tasks["task_7_native_bridge"]["soft_notes"]
        self.assertTrue(any("Recommended to do after the core Flutter-side tasks (1-4)" in n for n in notes))

    def test_task_7_new_dependency_note_is_captured(self):
        tasks = load_tasks(self.FEATURES_DIR, "logging-refactor")
        notes = tasks["task_7_native_bridge"]["soft_notes"]
        self.assertTrue(any("New dependency" in n for n in notes))


if __name__ == "__main__":
    unittest.main()
