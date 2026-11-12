"""Unit and integration tests for check-tasks terminal CLI and ANSI reporter.

Covers BDD Scenarios:
- CTD-HP-03: Terminal CLI renders rich ANSI colored multi-repo overview
- CTD-EC-04: Terminal CLI falls back to plain text when stdout is redirected
"""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

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
        DashboardGraph,
        RepoMetadata,
        TaskProgress,
        WorktreeMetadata,
        main,
        render_progress_bar,
        render_single_repo,
        render_terminal_table,
        strip_ansi,
    )
except ImportError:
    pass


class TestCheckTasksCLI_Integration(unittest.TestCase):
    """Test suite for terminal CLI and rich ANSI reporter."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self.temp_dir.name)

        # Mock repository metadata
        self.sample_repos = [
            RepoMetadata(
                name="ai-agent-tools",
                path=str(self.workspace_root / "ai-agent-tools"),
                theme_color="#b45309",
                window_title="🟠 [AI-AGENT-TOOLS] [@hau] check_tasks_dashboard",
                active_epic="check_tasks_dashboard",
                active_stage="Stage 3 Phase 2 (TDD)",
                worktrees=[
                    WorktreeMetadata(
                        path=str(
                            self.workspace_root
                            / "ai-agent-tools"
                            / ".worktrees"
                            / "check_tasks_dashboard"
                        ),
                        branch="epic/check_tasks_dashboard",
                        head_sha="a13bb3b",
                        is_dirty=False,
                        dirty_file_count=0,
                        is_detached=False,
                    )
                ],
                task_progress=TaskProgress(
                    total_tasks=5,
                    done_tasks=2,
                    in_progress_tasks=1,
                    todo_tasks=2,
                    percentage=40.0,
                    active_task_name="task_04_http_daemon_server_and_rest_api",
                ),
            ),
            RepoMetadata(
                name="lyrics-sync",
                path=str(self.workspace_root / "lyrics-sync"),
                theme_color="#7f1d1d",
                window_title="🔴 [LYRICS-SYNC] [@buivantrong8901] lexical_translation_export",
                active_epic="lexical_translation_export",
                active_stage="Stage 3 Phase 2 (TDD)",
                worktrees=[],
                task_progress=TaskProgress(
                    total_tasks=9,
                    done_tasks=6,
                    in_progress_tasks=1,
                    todo_tasks=2,
                    percentage=66.7,
                    active_task_name="task_7_benchmark",
                ),
            ),
        ]
        self.graph = DashboardGraph(
            workspace_root=str(self.workspace_root),
            scanned_at="2026-11-11T08:00:00Z",
            repos=self.sample_repos,
            metrics_row={
                "total_repos": 2,
                "active_epics": 2,
                "total_tasks": 14,
                "done_tasks": 8,
            },
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_ctd_hp_03(self) -> None:
        """[CTD-HP-03] [Tier C - Integration] Terminal CLI renders rich ANSI colored multi-repo overview."""
        output = render_terminal_table(self.graph, use_color=True)
        # Verify colored ANSI codes present
        self.assertIn("\033[", output)
        # Verify repo names present
        self.assertIn("ai-agent-tools", output)
        self.assertIn("lyrics-sync", output)
        # Verify active epics present
        self.assertIn("check_tasks_dashboard", output)
        self.assertIn("lexical_translation_export", output)
        # Verify progress percentage present
        self.assertIn("40%", output)
        self.assertIn("66%", output)

    def test_ctd_ec_04(self) -> None:
        """[CTD-EC-04] [Tier A - Unit] Terminal CLI falls back to plain text when stdout is redirected."""
        output = render_terminal_table(self.graph, use_color=False)
        # Verify no ANSI codes present
        self.assertNotIn("\033[", output)
        # Plain text should contain neat table rows
        self.assertIn("ai-agent-tools", output)
        self.assertIn("lyrics-sync", output)
        self.assertIn("40%", output)

    def test_strip_ansi(self) -> None:
        """Test ANSI escape code stripping utility."""
        colored_text = "\033[38;2;180;83;9m[AI-AGENT-TOOLS]\033[0m"
        clean = strip_ansi(colored_text)
        self.assertEqual(clean, "[AI-AGENT-TOOLS]")

    def test_render_progress_bar(self) -> None:
        """Test rendering visual progress bar."""
        bar = render_progress_bar(50.0, width=10, use_color=False)
        self.assertEqual(bar, "[█████░░░░░]")

    def test_render_single_repo(self) -> None:
        """Test detailed inspection card for a single repository."""
        repo = self.sample_repos[0]
        card = render_single_repo(repo, use_color=False)
        self.assertIn("ai-agent-tools", card)
        self.assertIn("check_tasks_dashboard", card)
        self.assertIn("epic/check_tasks_dashboard", card)
        self.assertIn("40%", card)

    def test_wrapper_entrypoint_status_does_not_hit_shadowed_tasks_server(self) -> None:
        """scripts/check_tasks.py --status must work (scripts/tasks_server.py wrapper shadows the real module)."""
        wrapper = Path(__file__).resolve().parent.parent / "scripts" / "check_tasks.py"
        proc = subprocess.run(
            [sys.executable, str(wrapper), "--status"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertNotIn("ImportError", proc.stderr)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
