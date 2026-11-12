#!/usr/bin/env python3
"""Tests for compute_execution_order.py.

Run: python3 .agents/skills/dev-implementation/resources/scripts/test_compute_execution_order.py -v
"""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compute_execution_order import (
    compute_layers,
    compute_parallel_batches,
    load_tasks,
    main,
    parse_allowed_files,
    parse_blockers,
    parse_soft_notes,
    scan_tasks,
)


def write_task(
    directory: Path,
    filename: str,
    *,
    epic: str,
    priority: str,
    title: str,
    dependencies_body: str,
    allowed_files: list[str] | None = None,
) -> None:
    files_section = ""
    if allowed_files is not None:
        files_section = "\n## Files\n\nAllowed files:\n" + "\n".join(f"- `{f}`" for f in allowed_files) + "\n"
    (directory / filename).write_text(
        f'---\nid: "{filename[:-3]}"\nstatus: "todo"\npriority: "{priority}"\nepic: "{epic}"\n---\n'
        f"# {title}\n\n## Dependencies & Blockers\n{dependencies_body}\n{files_section}"
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


    def test_scan_tasks_matches_formatted_epic_slug(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_task(directory, "task_1_a.md", epic="`demo`", priority="high", title="Task 1: A",
                       dependencies_body="- **Dependencies**: None.")
            write_task(directory, "task_2_b.md", epic="'demo'", priority="high", title="Task 2: B",
                       dependencies_body="- **Dependencies**: Blocked by [Task 1](task_1_a.md).")
            # Query with backtick-wrapped epic
            tasks, scanned, skipped = scan_tasks(directory, "`demo`")
            self.assertEqual(len(scanned), 2)
            self.assertEqual(len(tasks), 2)
            self.assertEqual(len(skipped), 0)


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


class ParseAllowedFilesTests(unittest.TestCase):
    def test_parse_allowed_files_single_and_multiple(self):
        text = "## Files\n\nAllowed files:\n- `src/core.py`\n- `tests/test_core.py` (new)\n\nRead-only context:\n- `src/base.py`\n"
        files = parse_allowed_files(text)
        self.assertEqual(files, ["src/core.py", "tests/test_core.py"])

    def test_parse_allowed_files_empty_when_no_section(self):
        text = "# Task 1: Demo\n\n## Summary\nJust a task\n"
        self.assertEqual(parse_allowed_files(text), [])


class ComputeParallelBatchesTests(unittest.TestCase):
    def test_disjoint_tasks_batched_together(self):
        tasks = {
            "task_1": {
                "id": "task_1",
                "priority": "high",
                "allowed_files": ["src/a.py"],
            },
            "task_2": {
                "id": "task_2",
                "priority": "medium",
                "allowed_files": ["src/b.py"],
            },
        }
        layers = [["task_1", "task_2"]]
        batches = compute_parallel_batches(layers, tasks, pool_size=2)
        # Both tasks should be in the same batch since files are disjoint and pool_size is 2
        self.assertEqual(batches, [[["task_1", "task_2"]]])

    def test_conflicting_tasks_split_into_separate_batches(self):
        tasks = {
            "task_1": {
                "id": "task_1",
                "priority": "high",
                "allowed_files": ["src/shared.py", "src/a.py"],
            },
            "task_2": {
                "id": "task_2",
                "priority": "medium",
                "allowed_files": ["src/shared.py", "src/b.py"],
            },
        }
        layers = [["task_1", "task_2"]]
        batches = compute_parallel_batches(layers, tasks, pool_size=2)
        # Even though they are in the same layer, file conflict forces separate sequential batches
        self.assertEqual(batches, [[["task_1"], ["task_2"]]])

    def test_pool_size_limits_batch_size(self):
        tasks = {
            "task_1": {"id": "task_1", "priority": "high", "allowed_files": ["src/a.py"]},
            "task_2": {"id": "task_2", "priority": "high", "allowed_files": ["src/b.py"]},
            "task_3": {"id": "task_3", "priority": "medium", "allowed_files": ["src/c.py"]},
        }
        layers = [["task_1", "task_2", "task_3"]]
        batches = compute_parallel_batches(layers, tasks, pool_size=2)
        self.assertEqual(batches, [[["task_1", "task_2"], ["task_3"]]])


class MainParallelCliTests(unittest.TestCase):
    def test_cli_parallel_and_json_modes(self):
        import io
        import json
        from contextlib import redirect_stdout

        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_task(directory, "task_1_a.md", epic="demo", priority="high", title="Task 1: A",
                       dependencies_body="- **Dependencies**: None.", allowed_files=["src/a.py"])
            write_task(directory, "task_2_b.md", epic="demo", priority="high", title="Task 2: B",
                       dependencies_body="- **Dependencies**: None.", allowed_files=["src/b.py"])

            # Test JSON mode
            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = main(["demo", "--json", "--features-dir", str(directory)])
            self.assertEqual(exit_code, 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(data["epic"], "demo")
            self.assertEqual(data["tasks_count"], 2)
            self.assertEqual(data["parallel_batches"], [[["task_1_a", "task_2_b"]]])

            # Test Parallel text mode
            buf_text = io.StringIO()
            with redirect_stdout(buf_text):
                exit_code = main(["demo", "--parallel", "--features-dir", str(directory)])
            self.assertEqual(exit_code, 0)
            text_output = buf_text.getvalue()
            self.assertIn("Parallel execution plan for epic 'demo'", text_output)
            self.assertIn("Parallel (Slots 1-2)", text_output)


class RealLoggingRefactorEpicTests(unittest.TestCase):
    def setUp(self):
        if not self.FEATURES_DIR.is_dir() or not any("task_7_native_bridge" in p.name for p in self.FEATURES_DIR.glob("*.md")):
            self.skipTest("logging-refactor tasks not present in features directory")
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
