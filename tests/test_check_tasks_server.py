"""Unit and integration tests for check-tasks HTTP daemon server and REST API.

Covers BDD Scenarios:
- CTD-HP-04: Web server daemon starts cleanly and serves REST API
- CTD-AR-01: Daemon server increments port safely on port collision
- CTD-FR-01: Rule 9 launcher enforcement prevents environment contamination
- CTD-FR-02: Server recovers gracefully from stale or orphan PID files
"""

import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, patch
import urllib.error
import urllib.request

SCRIPT_DIR = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "check-tasks"
    / "resources"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from tasks_server import (
        DEFAULT_PORT,
        DEFAULT_QUOTA_PORT,
        TasksHandler,
        TasksServer,
        build_clean_host_env,
        build_cli_launch_command,
        build_ide_launch_command,
        find_available_port,
        find_quota_script,
        get_real_home,
        get_running_pid,
        is_quota_server_alive,
        launch_quota_server,
        parse_review_results,
    )
except ImportError:
    pass


class TestCheckTasksServer_Integration(unittest.TestCase):
    """Integration test suite for HTTP daemon server and REST API."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self.temp_dir.name)
        self.pid_file = self.workspace_root / "tasks_server.pid"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_ctd_hp_04(self) -> None:
        """[CTD-HP-04] [Tier C - Integration] Web server daemon starts cleanly and serves REST API."""
        port = find_available_port(18766)
        server = TasksServer(
            host="127.0.0.1",
            port=port,
            workspace_root=self.workspace_root,
            pid_file=self.pid_file,
        )

        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        time.sleep(0.1)

        try:
            # Check PID file exists
            self.assertTrue(self.pid_file.is_file())
            pid = int(self.pid_file.read_text().strip())
            self.assertGreater(pid, 0)

            # Test GET /api/tasks
            url = f"http://127.0.0.1:{port}/api/tasks"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertIn("repos", data)
                self.assertIn("workspace_root", data)

            # Test POST /api/shutdown
            shutdown_url = f"http://127.0.0.1:{port}/api/shutdown"
            req = urllib.request.Request(
                shutdown_url, data=b"{}", headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(data.get("status"), "shutting_down")

            server_thread.join(timeout=2.0)
            self.assertFalse(self.pid_file.is_file())
        finally:
            server.shutdown()
            server.server_close()

    def test_ctd_ar_01(self) -> None:
        """[CTD-AR-01] [Tier C - Integration] Daemon server increments port safely on port collision."""
        base_port = find_available_port(19766)
        # Bind base port with a raw socket to simulate collision
        blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        blocker.bind(("127.0.0.1", base_port))
        blocker.listen(1)

        try:
            next_port = find_available_port(base_port)
            self.assertEqual(next_port, base_port + 1)

            server = TasksServer(
                host="127.0.0.1",
                port=base_port,
                workspace_root=self.workspace_root,
                pid_file=self.pid_file,
            )
            # Server automatically bumped to base_port + 1
            self.assertEqual(server.server_port, base_port + 1)
            server.server_close()
        finally:
            blocker.close()

    def test_ctd_fr_01(self) -> None:
        """[CTD-FR-01] [Tier A - Unit] Rule 9 launcher enforcement prevents environment contamination."""
        worktree = "/Users/test/workspace/repo"
        profile = "hau"

        cli_cmd = build_cli_launch_command(worktree, profile)
        self.assertEqual(cli_cmd[0], "osascript")
        self.assertIn(f"{profile}-cli", cli_cmd[2])
        self.assertIn(worktree, cli_cmd[2])
        self.assertNotIn("security default-keychain", cli_cmd[2])

        ide_cmd = build_ide_launch_command(worktree, profile)
        self.assertEqual(ide_cmd[0], "zsh")
        self.assertIn("-i", ide_cmd)
        self.assertIn("-c", ide_cmd)
        target_str = ide_cmd[-1]
        self.assertIn(f"{profile} {worktree}", target_str)

        # Shell injection safety test
        malicious_wt = '/Users/test/dir; rm -rf /; echo "pwned"'
        malicious_cli = build_cli_launch_command(malicious_wt, profile)
        self.assertIn(r"'/Users/test/dir; rm -rf /; echo \"pwned\"'", malicious_cli[2])

    def test_ctd_fr_02(self) -> None:
        """[CTD-FR-02] [Tier A - Unit] Server recovers gracefully from stale or orphan PID files."""
        # Write dead PID (e.g. 999999) to PID file
        self.pid_file.write_text("999999\n", encoding="utf-8")
        self.assertTrue(self.pid_file.is_file())

        pid = get_running_pid(self.pid_file)
        # Dead PID should be detected as None, and stale file unlinked
        self.assertIsNone(pid)
        self.assertFalse(self.pid_file.is_file())

    def test_api_review_parsing(self) -> None:
        """Test parsing of review findings and triage table."""
        repo_dir = self.workspace_root / "lyrics-sync"
        epic_dir = repo_dir / ".devtool" / "epic" / "lexical_translation_export"
        epic_dir.mkdir(parents=True, exist_ok=True)

        review_file = epic_dir / "principal_review.md"
        review_content = (
            "# Principal Review\n"
            "- **Candidate Commit SHA**: `777105e`\n"
            "- **Reviewer / Provider**: Claude 3.5 Sonnet\n"
            "- **Overall Verdict**: PASS\n\n"
            "| # | Severity | Location | Problem | Decision |\n"
            "|---|---|---|---|---|\n"
            "| 1 | Minor | src/eval.py:45 | Missing type hint | Accept |\n"
            "| 2 | Important | src/core.py:10 | Race condition | Fix in sha abc |\n\n"
            "```text\nRaw output: Verified clean run\n```\n"
        )
        review_file.write_text(review_content, encoding="utf-8")

        data = parse_review_results(repo_dir, "lexical_translation_export")
        self.assertEqual(data.get("verdict"), "PASS")
        self.assertEqual(data.get("sha"), "777105e")
        self.assertEqual(data.get("reviewer"), "Claude 3.5 Sonnet")
        self.assertEqual(len(data.get("findings", [])), 2)
        self.assertEqual(data["findings"][0]["severity"], "Minor")
        self.assertEqual(data["findings"][1]["severity"], "Important")

    def test_api_review_parsing_standard_headers(self) -> None:
        """Test parsing of review findings with standard bullet headers and multi-round files."""
        repo_dir = self.workspace_root / "test-repo"
        epic_dir = repo_dir / ".devtool" / "epic" / "test_epic"
        epic_dir.mkdir(parents=True, exist_ok=True)

        round2_file = epic_dir / "review_results_round_2.md"
        round2_content = (
            "# External Review Round 2\n"
            "- **SHA**: `abc1234`\n"
            "- **CLI**: Codex\n"
            "- **Model**: gpt-5\n"
            "- **Thinking**: High\n"
            "- **Verdict**: CONVERGED (PASS)\n\n"
            "| # | Severity | Location | Problem | Decision |\n"
            "|---|---|---|---|---|\n"
            "| 1 | Minor | test.py:12 | Unused import | Fixed |\n\n"
            "Raw output:\n\n```text\nClean convergence verified\n```\n"
        )
        round2_file.write_text(round2_content, encoding="utf-8")

        data = parse_review_results(repo_dir, "test_epic", target_round=2)
        self.assertEqual(data.get("verdict"), "CONVERGED (PASS)")
        self.assertEqual(data.get("sha"), "abc1234")
        self.assertEqual(data.get("reviewer"), "Codex")
        self.assertEqual(data.get("model"), "gpt-5")
        self.assertEqual(data.get("thinking"), "High")
        self.assertEqual(data.get("round"), 2)
        self.assertEqual(len(data.get("findings", [])), 1)
        self.assertIn("Clean convergence verified", data.get("raw_output", ""))

    def test_api_review_parsing_ignores_fenced_rounds(self) -> None:
        """Test that round headings inside fenced code blocks are ignored and available_rounds deduplicated."""
        repo_dir = self.workspace_root / "lyrics-repo"
        epic_dir = repo_dir / ".devtool" / "epic" / "my_feature"
        epic_dir.mkdir(parents=True, exist_ok=True)

        review_file = epic_dir / "review_results.md"
        content = (
            "# Cross-Model Review: my_feature\n\n"
            "## Round 1\n"
            "- **SHA**: `5421929`\n"
            "- **Reviewer**: Codex\n"
            "- **Verdict**: CHANGES REQUIRED\n\n"
            "| # | Severity | Location | Problem | Decision |\n"
            "|---|---|---|---|---|\n"
            "| 1 | Important | src/main.py:10 | Bug found | Pending |\n\n"
            "### Raw Output\n"
            "```text\n"
            "Regurgitated prompt output containing:\n"
            "## Round 1\n"
            "## Round 1\n"
            "## Round 2\n"
            "## Round 3\n"
            "```\n"
        )
        review_file.write_text(content, encoding="utf-8")

        data = parse_review_results(repo_dir, "my_feature")
        self.assertEqual(data.get("round"), 1)
        self.assertEqual(data.get("available_rounds"), [1])
        self.assertEqual(len(data.get("findings", [])), 1)

    def test_assign_epic_pic_and_endpoint(self) -> None:
        """Test assigning PIC updates epic HLD, handoff, tasks, and settings."""
        from tasks_server import assign_epic_pic

        repo_dir = self.workspace_root / "my-repo"
        epic_dir = repo_dir / ".devtool" / "epic" / "my_epic"
        epic_dir.mkdir(parents=True, exist_ok=True)

        hld_file = epic_dir / "my_epic.en.md"
        hld_file.write_text(
            "# My Epic\n\n- **Epic name**: `my_epic`\n- **Status**: In Progress\n",
            encoding="utf-8",
        )

        handoff_file = epic_dir / "handoff.md"
        handoff_file.write_text(
            "# Handoff\n\n- **Epic name**: `my_epic`\n", encoding="utf-8"
        )

        task_file = epic_dir / "task_01_core.md"
        task_file.write_text(
            "---\nid: task_01\ntitle: Core task\n---\n# Task 01\n", encoding="utf-8"
        )

        res = assign_epic_pic(
            self.workspace_root, "my-repo", "my_epic", "phungthuy8901"
        )
        self.assertEqual(res.get("status"), "ok")
        self.assertEqual(res.get("pic"), "phungthuy8901")
        self.assertGreater(len(res.get("updated_files", [])), 0)

        self.assertIn(
            "- **PIC**: `phungthuy8901`", hld_file.read_text(encoding="utf-8")
        )
        self.assertIn(
            "- **PIC**: `phungthuy8901`", handoff_file.read_text(encoding="utf-8")
        )
        self.assertIn('pic: "phungthuy8901"', task_file.read_text(encoding="utf-8"))

    def test_build_clean_host_env_and_launch_endpoints_sanitize_env(self) -> None:
        """build_clean_host_env and /api/launch/* sanitize IDE vars and validate profiles."""
        with patch(
            "os.path.expanduser",
            return_value="/Users/danhdueexoictif/antigravity_homes/hau",
        ):
            self.assertEqual(get_real_home(), "/Users/danhdueexoictif")
            cleaned = build_clean_host_env(
                {
                    "HOME": "/Users/danhdueexoictif/antigravity_homes/hau",
                    "PATH": "/opt/homebrew/bin:/usr/bin",
                    "TERM_PROGRAM": "vscode",
                    "VSCODE_PID": "1463",
                    "ELECTRON_RUN_AS_NODE": "1",
                    "ANTIGRAVITY_X": "1",
                    "AGY_PROFILE": "hau",
                    "TMPDIR": "/tmp/ag_hau",
                    "ZDOTDIR": "/tmp/zdot",
                }
            )
            self.assertEqual(cleaned["HOME"], "/Users/danhdueexoictif")
            self.assertEqual(cleaned["PATH"], "/opt/homebrew/bin:/usr/bin")
            for k in (
                "TERM_PROGRAM",
                "VSCODE_PID",
                "ELECTRON_RUN_AS_NODE",
                "ANTIGRAVITY_X",
                "AGY_PROFILE",
                "TMPDIR",
                "ZDOTDIR",
            ):
                self.assertNotIn(k, cleaned)

        handler = TasksHandler.__new__(TasksHandler)
        handler.server = MagicMock()
        handler.headers = {"Content-Length": "40"}  # type: ignore[assignment]
        handler._send_json = MagicMock()  # type: ignore[method-assign]

        dirty = {
            "HOME": "/Users/danhdueexoictif/antigravity_homes/danhdue",
            "TERM_PROGRAM": "vscode",
            "VSCODE_IPC_HOOK": "/tmp/hook",
            "ELECTRON_RUN_AS_NODE": "1",
            "AGY_PROFILE": "danhdue",
            "PATH": "/usr/bin",
        }
        with (
            patch(
                "os.path.expanduser",
                return_value="/Users/danhdueexoictif/antigravity_homes/danhdue",
            ),
            patch.dict("os.environ", dirty, clear=True),
            patch("subprocess.Popen") as mock_popen,
        ):
            # Invalid profile rejected on /api/launch/cli
            handler.path = "/api/launch/cli"
            handler.rfile = MagicMock()
            handler.rfile.read.return_value = json.dumps(
                {"worktree": "/tmp/wt", "profile": "bad;cmd"}
            ).encode("utf-8")
            handler.do_POST()
            mock_popen.assert_not_called()
            self.assertEqual(handler._send_json.call_args[0][0], 400)

            # Valid profile on /api/launch/ide gets clean env & detached session
            handler._send_json.reset_mock()
            handler.path = "/api/launch/ide"
            handler.rfile.read.return_value = json.dumps(
                {"worktree": "/tmp/wt", "profile": "hau"}
            ).encode("utf-8")
            handler.do_POST()
            mock_popen.assert_called_once()
            kwargs = mock_popen.call_args.kwargs
            self.assertTrue(kwargs.get("start_new_session"))
            passed_env = kwargs["env"]
            self.assertEqual(passed_env["HOME"], "/Users/danhdueexoictif")
            self.assertNotIn("TERM_PROGRAM", passed_env)
            self.assertNotIn("VSCODE_IPC_HOOK", passed_env)
            self.assertNotIn("AGY_PROFILE", passed_env)

    def test_api_profiles_endpoint(self) -> None:
        """Test GET /api/profiles returns list of discovered Antigravity profiles."""
        port = find_available_port(18770)
        server = TasksServer(
            host="127.0.0.1",
            port=port,
            workspace_root=self.workspace_root,
            pid_file=self.pid_file,
        )
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        time.sleep(0.1)

        try:
            url = f"http://127.0.0.1:{port}/api/profiles"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertIn("profiles", data)
                self.assertIsInstance(data["profiles"], list)
                self.assertTrue(len(data["profiles"]) > 0)
                self.assertIn("danhdue", data["profiles"])
        finally:
            server.shutdown()
            server.server_close()

    def test_api_launch_quota_endpoint(self) -> None:
        """Test POST /api/launch/quota triggers quota server and returns 200."""
        handler = TasksHandler.__new__(TasksHandler)
        handler.server = MagicMock()
        handler.server.workspace_root = self.workspace_root
        handler.headers = {"Content-Length": "2"}
        handler._send_json = MagicMock()

        with patch("tasks_server.launch_quota_server") as mock_launch:
            mock_launch.return_value = {
                "status": "ok",
                "action": "already_running",
                "url": "http://127.0.0.1:8765",
            }
            handler.path = "/api/launch/quota"
            handler.rfile = MagicMock()
            handler.rfile.read.return_value = b"{}"
            handler.do_POST()

            mock_launch.assert_called_once_with(self.workspace_root, port=8765)
            handler._send_json.assert_called_once_with(
                200,
                {
                    "status": "ok",
                    "action": "already_running",
                    "url": "http://127.0.0.1:8765",
                },
            )

    def test_find_quota_script_and_alive_check(self) -> None:
        """Test finding agy_quota.py script and checking alive status."""
        script = find_quota_script(self.workspace_root)
        self.assertIsNotNone(script)
        self.assertTrue(script.is_file())
        self.assertEqual(script.name, "agy_quota.py")

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_urlopen.return_value = mock_resp
            self.assertTrue(is_quota_server_alive(8765))

        with patch("urllib.request.urlopen", side_effect=Exception("down")):
            self.assertFalse(is_quota_server_alive(8765))

    def test_status_exposes_code_fingerprint_and_meta_sidecar(self) -> None:
        """[CTD-FR-03] /api/status and meta sidecar expose code fingerprint for stale daemon detection."""
        from tasks_server import compute_server_code_fingerprint, pid_meta_path

        port = find_available_port(18790)
        server = TasksServer(
            host="127.0.0.1",
            port=port,
            workspace_root=self.workspace_root,
            pid_file=self.pid_file,
        )
        meta_path = pid_meta_path(self.pid_file)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        time.sleep(0.1)

        try:
            url = f"http://127.0.0.1:{port}/api/status"
            with urllib.request.urlopen(url, timeout=3) as resp:
                self.assertEqual(resp.status, 200)
                status_data = json.loads(resp.read().decode("utf-8"))

            expected_fp = compute_server_code_fingerprint()
            self.assertEqual(status_data.get("code_fingerprint"), expected_fp)
            self.assertTrue(meta_path.is_file())
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            self.assertEqual(meta.get("code_fingerprint"), expected_fp)
            self.assertEqual(meta.get("port"), server.server_port)
            self.assertEqual(
                meta.get("workspace_root"), str(self.workspace_root.resolve())
            )
        finally:
            server.shutdown()
            server.server_close()

        server_thread.join(timeout=2.0)
        self.assertFalse(meta_path.is_file())

    def test_stale_daemon_restarts_automatically_on_launch(self) -> None:
        """[CTD-FR-04] Launching daemon automatically restarts stale server when code/workspace changes."""
        import tasks_server

        meta_path = tasks_server.pid_meta_path(self.pid_file)
        self.pid_file.write_text("424242\n", encoding="utf-8")

        # 1. Missing meta sidecar & unreachable HTTP status -> legacy pre-fingerprint daemon is stale
        self.assertTrue(
            tasks_server.is_running_server_stale(
                424242,
                self.pid_file,
                self.workspace_root,
                port=18799,
                expected_fingerprint="abc123",
            )
        )

        # 2. Matching meta sidecar -> fresh (not stale)
        meta_path.write_text(
            json.dumps(
                {
                    "pid": 424242,
                    "port": 18799,
                    "workspace_root": str(self.workspace_root.resolve()),
                    "code_fingerprint": "abc123",
                }
            ),
            encoding="utf-8",
        )
        self.assertFalse(
            tasks_server.is_running_server_stale(
                424242,
                self.pid_file,
                self.workspace_root,
                port=18799,
                expected_fingerprint="abc123",
            )
        )

        # 3. Mismatched fingerprint -> stale
        self.assertTrue(
            tasks_server.is_running_server_stale(
                424242,
                self.pid_file,
                self.workspace_root,
                port=18799,
                expected_fingerprint="new999",
            )
        )

        # 4. main --daemon restarts stale daemon but reuses fresh daemon unless --restart
        with (
            patch.object(tasks_server, "DEFAULT_PID_FILE", self.pid_file),
            patch("tasks_server.get_running_pid", return_value=424242),
            patch("tasks_server.stop_server", return_value=True) as mock_stop,
            patch(
                "tasks_server.compute_server_code_fingerprint", return_value="new999"
            ),
            patch("tasks_server._wait_for_daemon_ready", return_value=True),
            patch("subprocess.Popen") as mock_popen,
        ):
            mock_popen.return_value.pid = 535353
            rc = tasks_server.main(
                [
                    "--daemon",
                    "--port",
                    "18799",
                    "--workspace-root",
                    str(self.workspace_root),
                ]
            )
            self.assertEqual(rc, 0)
            mock_stop.assert_called_once_with(self.pid_file)
            mock_popen.assert_called_once()

            mock_stop.reset_mock()
            mock_popen.reset_mock()
            with patch(
                "tasks_server.compute_server_code_fingerprint", return_value="abc123"
            ):
                rc_reuse = tasks_server.main(
                    [
                        "--daemon",
                        "--port",
                        "18799",
                        "--workspace-root",
                        str(self.workspace_root),
                    ]
                )
                self.assertEqual(rc_reuse, 0)
                mock_stop.assert_not_called()
                mock_popen.assert_not_called()

                rc_force = tasks_server.main(
                    [
                        "--daemon",
                        "--restart",
                        "--port",
                        "18799",
                        "--workspace-root",
                        str(self.workspace_root),
                    ]
                )
                self.assertEqual(rc_force, 0)
                mock_stop.assert_called_once_with(self.pid_file)
                mock_popen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
