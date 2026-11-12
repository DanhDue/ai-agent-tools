"""End-to-End acceptance integration test suite for Check Tasks Dashboard.

Covers: [CTD-HP-05] Interactive web dashboard displays project cards and review modal
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

SCRIPT_DIR = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "check-tasks"
    / "resources"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from tasks_server import (  # type: ignore[import-not-found]
        TasksHandler,
        find_available_port,
    )
except ImportError:
    pass


class TestCheckTasksE2E_Integration(unittest.TestCase):
    """Tier C Integration test suite for end-to-end dashboard and server acceptance."""

    repo_root: Path
    dashboard_html_path: Path
    skill_md_path: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parent.parent
        cls.dashboard_html_path = (
            cls.repo_root
            / "skills"
            / "check-tasks"
            / "resources"
            / "dashboard"
            / "tasks_dashboard.html"
        )
        cls.skill_md_path = cls.repo_root / "skills" / "check-tasks" / "SKILL.md"

    def test_ctd_hp_05(self) -> None:
        """Scenario: [CTD-HP-05] [Tier C - Integration] Interactive web dashboard displays project cards and review modal."""
        # 1. Given the web server is running and serving tasks_dashboard.html
        self.assertTrue(
            self.dashboard_html_path.is_file(),
            f"Expected {self.dashboard_html_path} to exist and be served",
        )
        html_content = self.dashboard_html_path.read_text(encoding="utf-8")

        # 2. When the user accesses the dashboard in a browser
        # Then the interface renders dark mode cards for all repositories
        self.assertIn("repos-container", html_content)
        self.assertIn("repo-card", html_content)
        self.assertIn("antigravity-note-container", html_content)
        self.assertIn("handleAntigravityNoteKeydown", html_content)
        self.assertIn("pinRepoToTop", html_content)

        # 3. And clicking a review button opens a modal displaying the candidate SHA,
        #    reviewer model, the persisted 5-column triage table, and the evidence drawer
        self.assertIn("modal-cross-review", html_content)
        self.assertIn("modal-kanban", html_content)
        self.assertIn("modal-context", html_content)
        self.assertIn("Candidate Commit SHA", html_content)
        self.assertIn("Reviewer / Provider", html_content)
        self.assertIn("Evidence / Raw Output", html_content)

        # 4. And clicking an IDE launch button triggers a POST request to /api/launch/ide without throwing errors
        mock_server = MagicMock()
        mock_server.workspace_root = self.repo_root
        mock_server.server_port = 49520
        mock_server.pid_file = Path("/tmp/test_tasks_server.pid")

        handler = TasksHandler.__new__(TasksHandler)
        handler.server = mock_server
        handler.headers = {"Content-Length": "34"}  # type: ignore[assignment]
        payload = json.dumps({"worktree": "/tmp/test", "profile": "default"}).encode(
            "utf-8"
        )
        handler.rfile = MagicMock()
        handler.rfile.read.return_value = payload
        handler._send_json = MagicMock()  # type: ignore[method-assign]
        handler.path = "/api/launch/ide"

        with patch("subprocess.Popen", return_value=MagicMock()):
            handler.do_POST()
            handler._send_json.assert_called_with(
                200,
                {
                    "status": "ok",
                    "action": "launched",
                    "command": [
                        "zsh",
                        "-i",
                        "-c",
                        "antigravity /tmp/test",
                    ],
                },
            )

    def test_tasks_server_serves_html_root(self) -> None:
        """Verify GET / on TasksHandler serves tasks_dashboard.html with HTTP 200."""
        mock_server = MagicMock()
        mock_server.workspace_root = self.repo_root
        mock_server.server_port = 49520

        handler = TasksHandler.__new__(TasksHandler)
        handler.server = mock_server
        handler.path = "/"
        handler.send_response = MagicMock()  # type: ignore[method-assign]
        handler.send_header = MagicMock()  # type: ignore[method-assign]
        handler.end_headers = MagicMock()  # type: ignore[method-assign]
        handler.wfile = MagicMock()

        handler.do_GET()

        handler.send_response.assert_called_with(200)
        handler.send_header.assert_any_call("Content-Type", "text/html; charset=utf-8")
        handler.end_headers.assert_called_once()
        handler.wfile.write.assert_called_once()
        written = handler.wfile.write.call_args[0][0]
        self.assertIn(b"Cross-Repo Tasks & Context Dashboard", written)

    def test_cli_launch_endpoint(self) -> None:
        """Verify POST /api/launch/cli executes cleanly with AppleScript command."""
        mock_server = MagicMock()
        mock_server.workspace_root = self.repo_root

        handler = TasksHandler.__new__(TasksHandler)
        handler.server = mock_server
        handler.headers = {"Content-Length": "34"}  # type: ignore[assignment]
        payload = json.dumps({"worktree": "/tmp/test_wt", "profile": "hau"}).encode(
            "utf-8"
        )
        handler.rfile = MagicMock()
        handler.rfile.read.return_value = payload
        handler._send_json = MagicMock()  # type: ignore[method-assign]
        handler.path = "/api/launch/cli"

        with patch("subprocess.Popen", return_value=MagicMock()):
            handler.do_POST()
            handler._send_json.assert_called_with(
                200,
                {
                    "status": "ok",
                    "command": [
                        "osascript",
                        "-e",
                        'tell application "Terminal" to do script "cd /tmp/test_wt && hau-cli"',
                    ],
                },
            )

    def test_ui_components_and_modals(self) -> None:
        """Verify HTML contains all required UI components, modals, and interaction handlers."""
        html_content = self.dashboard_html_path.read_text(encoding="utf-8")
        # Antigravity input box tokens
        self.assertIn("antigravity-note-container", html_content)
        self.assertIn("autoResizeTextarea", html_content)
        self.assertIn("copyRepoNoteText", html_content)
        self.assertIn("clearRepoNoteText", html_content)
        self.assertIn("saveRepoNoteText", html_content)

        # Drag and drop and pin to top tokens
        self.assertIn("initDragAndDrop", html_content)
        self.assertIn("pinRepoToTop", html_content)
        self.assertIn("saveReposOrder", html_content)
        self.assertIn("restoreReposOrder", html_content)

        # Modal dialogs and backdrop
        self.assertIn("modal-kanban", html_content)
        self.assertIn("modal-context", html_content)
        self.assertIn("modal-cross-review", html_content)
        self.assertIn("modal-principal-review", html_content)
        self.assertIn("initModalClickOutside", html_content)

    def test_skill_md_specification(self) -> None:
        """Verify SKILL.md adheres strictly to AGENTS.md rules and d3nexus naming."""
        self.assertTrue(self.skill_md_path.is_file(), f"Missing {self.skill_md_path}")
        content = self.skill_md_path.read_text(encoding="utf-8")

        # AGENTS.md rule: frontmatter is exactly name + description
        lines = content.strip().splitlines()
        self.assertEqual(lines[0], "---")
        frontmatter_lines = []
        for line in lines[1:]:
            if line == "---":
                break
            frontmatter_lines.append(line)

        frontmatter_keys = [
            line.split(":")[0].strip() for line in frontmatter_lines if ":" in line
        ]
        self.assertEqual(sorted(frontmatter_keys), ["description", "name"])
        self.assertIn("check-tasks", content)
        self.assertIn("/check-tasks", content)


if __name__ == "__main__":
    unittest.main()
