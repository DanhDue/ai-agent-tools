"""Unit tests for check-tasks harvester engine and data models.

Covers BDD Scenarios:
- CTD-HP-01: Multi-repo harvesting discovers all projects, worktrees, and styling metadata
- CTD-EC-01: Graceful fallback when .vscode/settings.json is absent
- CTD-EC-02: Graceful handling of repositories without active epics
- CTD-EC-03: Parsing dirty worktrees and detached HEAD commits
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

# Ensure skills/check-tasks/resources/scripts is on sys.path
SCRIPT_DIR = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "check-tasks"
    / "resources"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from check_tasks import (
        CANONICAL_SIGNATURES,
        DashboardGraph,
        RepoMetadata,
        TaskProgress,
        TwoTierMemory,
        WorktreeMetadata,
        extract_task_progress,
        extract_two_tier_memory,
        extract_vscode_styling,
        harvest_dashboard_graph,
        normalize_task_status,
        resolve_active_epic,
        scan_worktrees,
    )
except ImportError:
    # During RED phase, check_tasks may not exist yet
    pass


class TestCheckTasksHarvester_Integration(unittest.TestCase):
    """Test suite for data models and harvester functions."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_ctd_hp_01(self) -> None:
        """[CTD-HP-01] Multi-repo harvesting discovers all projects, worktrees, and styling metadata."""
        # Create 4 mock repos
        repo_names = ["ai-agent-tools", "lyrics-sync", "nexus", "D3Nexus"]
        for name in repo_names:
            repo_path = self.workspace_root / name
            repo_path.mkdir(parents=True)
            # Init git
            subprocess.run(
                ["git", "init", "-b", "main"],
                cwd=str(repo_path),
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "test@test.local"],
                cwd=str(repo_path),
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=str(repo_path),
                check=True,
            )
            # Create a commit
            (repo_path / "README.md").write_text(f"# {name}\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=str(repo_path), check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=str(repo_path),
                check=True,
            )

            # Setup .vscode/settings.json
            vscode_dir = repo_path / ".vscode"
            vscode_dir.mkdir(parents=True)
            color = CANONICAL_SIGNATURES.get(name, "#333333")
            settings = {
                "workbench.colorCustomizations": {
                    "titleBar.activeBackground": color,
                    "statusBar.background": color,
                },
                "window.title": f"[{name.upper()}] [@testuser] Epic: Test Epic - Stage 3",
            }
            (vscode_dir / "settings.json").write_text(
                json.dumps(settings), encoding="utf-8"
            )

            # Setup .devtool/features with tasks
            features_dir = repo_path / ".devtool" / "features"
            features_dir.mkdir(parents=True)
            (features_dir / "task_01.md").write_text(
                '---\nid: "task_01"\nstatus: "done"\nepic: "test-epic"\n---\n# Task 1\n',
                encoding="utf-8",
            )
            (features_dir / "task_02.md").write_text(
                '---\nid: "task_02"\nstatus: "in-progress"\nepic: "test-epic"\n---\n# Task 2\n',
                encoding="utf-8",
            )
            (features_dir / "task_03.md").write_text(
                '---\nid: "task_03"\nstatus: "todo"\nepic: "test-epic"\n---\n# Task 3\n',
                encoding="utf-8",
            )

        graph = harvest_dashboard_graph(self.workspace_root, max_workers=2)
        self.assertIsInstance(graph, DashboardGraph)
        self.assertEqual(len(graph.repos), 4)
        repo_map = {r.name: r for r in graph.repos}
        for name in repo_names:
            self.assertIn(name, repo_map)
            r = repo_map[name]
            self.assertEqual(r.theme_color, CANONICAL_SIGNATURES[name])
            self.assertIn("@testuser", r.window_title)
            self.assertEqual(r.task_progress.total_tasks, 3)
            self.assertEqual(r.task_progress.done_tasks, 1)
            self.assertEqual(r.task_progress.in_progress_tasks, 1)
            self.assertEqual(r.task_progress.todo_tasks, 1)
            self.assertAlmostEqual(r.task_progress.percentage, 33.3, places=1)

    def test_ctd_ec_01(self) -> None:
        """[CTD-EC-01] Graceful fallback when .vscode/settings.json is absent."""
        repo_path = self.workspace_root / "lyrics-sync"
        repo_path.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
        )

        color, title = extract_vscode_styling(repo_path)
        self.assertEqual(color, CANONICAL_SIGNATURES["lyrics-sync"])
        self.assertEqual(title, "lyrics-sync")

        # Unknown repo fallback
        unknown_path = self.workspace_root / "unknown_project"
        unknown_path.mkdir(parents=True)
        color_u, title_u = extract_vscode_styling(unknown_path)
        self.assertTrue(color_u.startswith("#"))
        self.assertEqual(title_u, "unknown_project")

    def test_ctd_ec_02(self) -> None:
        """[CTD-EC-02] Graceful handling of repositories without active epics."""
        repo_path = self.workspace_root / "empty-repo"
        repo_path.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
        )

        active_epic = resolve_active_epic(repo_path)
        self.assertIsNone(active_epic)

        progress = extract_task_progress(repo_path, active_epic)
        self.assertEqual(progress.total_tasks, 0)
        self.assertEqual(progress.done_tasks, 0)
        self.assertEqual(progress.in_progress_tasks, 0)
        self.assertEqual(progress.todo_tasks, 0)
        self.assertEqual(progress.percentage, 0.0)
        self.assertIsNone(progress.active_task_name)

    def test_ctd_ec_03(self) -> None:
        """[CTD-EC-03] Parsing dirty worktrees and detached HEAD commits."""
        repo_path = self.workspace_root / "dirty-repo"
        repo_path.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.local"],
            cwd=str(repo_path),
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=str(repo_path), check=True
        )

        (repo_path / "file1.txt").write_text("commit 1", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(repo_path), check=True)
        subprocess.run(
            ["git", "commit", "-m", "First commit"], cwd=str(repo_path), check=True
        )

        # Checkout detached HEAD
        head_rev = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        subprocess.run(
            ["git", "checkout", head_rev],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
        )

        # Modify a file to make it dirty
        (repo_path / "file2.txt").write_text("unstaged change", encoding="utf-8")

        worktrees = scan_worktrees(repo_path)
        self.assertEqual(len(worktrees), 1)
        wt = worktrees[0]
        self.assertTrue(wt.is_detached)
        self.assertTrue(wt.is_dirty)
        self.assertGreaterEqual(wt.dirty_file_count, 1)
        self.assertEqual(wt.head_sha, head_rev)

    def test_normalize_task_status(self) -> None:
        """Test normalization of status strings from underscore to hyphen."""
        self.assertEqual(normalize_task_status("in_progress"), "in-progress")
        self.assertEqual(normalize_task_status("in-progress"), "in-progress")
        self.assertEqual(normalize_task_status("done"), "done")
        self.assertEqual(normalize_task_status("todo"), "todo")
        self.assertEqual(normalize_task_status("backlog"), "backlog")
        self.assertEqual(normalize_task_status("review"), "review")
        self.assertEqual(normalize_task_status("UNKNOWN_VAL"), "backlog")

    def test_two_tier_memory_extraction(self) -> None:
        """Test extraction of Two-Tier Memory."""
        repo_path = self.workspace_root / "mem-repo"
        repo_path.mkdir(parents=True)
        devtool_dir = repo_path / ".devtool"
        devtool_dir.mkdir(parents=True)

        ledger_content = (
            "# Project Architectural Ledger\n\n"
            "## 2. Completed Epics & Architectural Milestones\n"
            "- **[2026-10-31] `context_memory_management`**: Delivered Two-Tier Project Memory\n"
            "- **[2026-11-11] `autonomous_lifecycle_runner`**: Complete Autonomous Lifecycle Runner\n"
        )
        (devtool_dir / "PROJECT_LEDGER.md").write_text(ledger_content, encoding="utf-8")

        assistant_state = (
            "# Active Epic: test_epic\n"
            "- Role: programmer | Updated: 2026-11-11 08:41\n\n"
            "## Repo/Task Status:\n"
            "- In Progress\n"
        )
        (devtool_dir / "assistant_state.md").write_text(
            assistant_state, encoding="utf-8"
        )

        memory = extract_two_tier_memory(repo_path)
        self.assertIsInstance(memory, TwoTierMemory)
        self.assertEqual(memory.total_milestones, 2)
        self.assertIsNotNone(memory.last_milestone)
        assert memory.last_milestone is not None
        self.assertIn("autonomous_lifecycle_runner", memory.last_milestone)
        self.assertEqual(memory.assistant_state_role, "programmer")
        self.assertEqual(memory.assistant_state_status, "In Progress")


if __name__ == "__main__":
    unittest.main()
