#!/usr/bin/env python3
"""Unit tests for refresh_session.py engine and CLI commands."""

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path to import refresh_session
sys.path.insert(0, str(Path(__file__).parent))

import refresh_session


class TestRefreshSession(unittest.TestCase):
    def test_parse_arguments_default(self) -> None:
        """Target defaults to 'all', timeout to 60, json to False."""
        args = refresh_session.parse_args([])
        self.assertEqual(args.target, "all")
        self.assertEqual(args.timeout, 60)
        self.assertFalse(args.json)

    def test_parse_arguments_targets(self) -> None:
        """Parses valid target arguments: claude, codex, and all."""
        for target in ("claude", "codex", "all"):
            args = refresh_session.parse_args([target])
            self.assertEqual(args.target, target)

    def test_parse_arguments_options(self) -> None:
        """Parses optional --timeout and --json flags."""
        args = refresh_session.parse_args(["claude", "--timeout", "30", "--json"])
        self.assertEqual(args.target, "claude")
        self.assertEqual(args.timeout, 30)
        self.assertTrue(args.json)

    def test_parse_arguments_invalid_target(self) -> None:
        """Rejects unknown target choices."""
        import io
        from contextlib import redirect_stderr

        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            refresh_session.parse_args(["unknown-cli"])

    def test_build_claude_command(self) -> None:
        """Builds sandboxed Claude command with zero-skill flags and model haiku."""
        cmd = refresh_session.build_claude_command(prompt="1", model="haiku")
        expected = [
            "claude",
            "--safe-mode",
            "--disable-slash-commands",
            "--tools",
            "",
            "--model",
            "haiku",
            "-p",
            "1",
        ]
        self.assertEqual(cmd, expected)

    def test_build_codex_command(self) -> None:
        """Builds sandboxed Codex command disabling plugins, apps, hooks, and rules."""
        cmd = refresh_session.build_codex_command(prompt="1", reasoning_effort="low")
        expected = [
            "codex",
            "exec",
            "--disable",
            "plugins",
            "--disable",
            "apps",
            "--disable",
            "hooks",
            "--ephemeral",
            "--skip-git-repo-check",
            "--ignore-user-config",
            "--ignore-rules",
            "-c",
            "model_reasoning_effort=low",
            "1",
        ]
        self.assertEqual(cmd, expected)

    def test_extract_token_usage(self) -> None:
        """Extracts token usage integer from typical CLI outputs."""
        codex_output = "OpenAI Codex v0.162.1\nuser\n1\ncodex\nHello\ntokens used\n1,695\n"
        self.assertEqual(refresh_session.extract_tokens(codex_output), 1695)

        alt_output = "Summary\nTokens: 42\nDone"
        self.assertEqual(refresh_session.extract_tokens(alt_output), 42)

        no_tokens = "Simple response with no token metadata"
        self.assertIsNone(refresh_session.extract_tokens(no_tokens))

    @patch("shutil.which", return_value=None)
    def test_run_ping_missing_cli(self, mock_which: MagicMock) -> None:
        """Gracefully reports SKIPPED when target executable is missing from PATH."""
        res = refresh_session.ping_cli("claude")
        self.assertEqual(res["cli"], "claude")
        self.assertEqual(res["status"], "SKIPPED")
        self.assertIn("not found in PATH", res.get("error", ""))

    @patch("shutil.which", return_value="/opt/homebrew/bin/claude")
    @patch("subprocess.run")
    def test_run_ping_claude_success_mocked(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Successfully executes Claude in a clean temp directory."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["claude"],
            returncode=0,
            stdout="Hi! Ready to help.\ntokens used\n25\n",
            stderr="",
        )
        res = refresh_session.ping_cli("claude", timeout=10)
        self.assertEqual(res["cli"], "claude")
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["tokens"], 25)
        self.assertGreaterEqual(res["latency_ms"], 0.0)
        self.assertIsNone(res.get("error"))

        # Verify cwd was set to a temporary directory outside current repository
        cwd_arg = mock_run.call_args[1].get("cwd")
        self.assertIsNotNone(cwd_arg)
        self.assertFalse(str(cwd_arg).startswith(str(Path.cwd())))

    @patch("shutil.which", return_value="/opt/homebrew/bin/codex")
    @patch("subprocess.run")
    def test_run_ping_codex_success_mocked(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Successfully executes Codex in a clean temp directory."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout="codex\nOK\ntokens used\n1,697\n",
            stderr="",
        )
        res = refresh_session.ping_cli("codex", timeout=10)
        self.assertEqual(res["cli"], "codex")
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["tokens"], 1697)
        self.assertIsNone(res.get("error"))

    @patch("shutil.which", return_value="/opt/homebrew/bin/claude")
    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["claude"], timeout=5))
    def test_run_ping_timeout_mocked(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Reports TIMEOUT and status FAIL on subprocess timeout."""
        res = refresh_session.ping_cli("claude", timeout=5)
        self.assertEqual(res["cli"], "claude")
        self.assertEqual(res["status"], "FAIL")
        self.assertIn("Timed out", res.get("error", ""))

    @patch("shutil.which", return_value="/opt/homebrew/bin/claude")
    @patch("subprocess.run")
    def test_run_ping_error_exit(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Reports FAIL when subprocess exits with non-zero returncode."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["claude"],
            returncode=1,
            stdout="",
            stderr="Authentication required",
        )
        res = refresh_session.ping_cli("claude", timeout=10)
        self.assertEqual(res["cli"], "claude")
        self.assertEqual(res["status"], "FAIL")
        self.assertIn("Authentication required", res.get("error", ""))

    @patch("refresh_session.ping_cli")
    def test_main_json_output(self, mock_ping: MagicMock) -> None:
        """Formats output as structured JSON on --json flag."""
        mock_ping.return_value = {
            "cli": "claude",
            "status": "PASS",
            "latency_ms": 1250.0,
            "tokens": 25,
            "error": None,
        }
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            code = refresh_session.main(["claude", "--json"])

        self.assertEqual(code, 0)
        data = json.loads(out.getvalue())
        self.assertIn("results", data)
        self.assertEqual(data["overall_status"], "PASS")
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["cli"], "claude")

    def test_parse_flexible_time_24h(self) -> None:
        """Parses standard 24-hour time strings."""
        self.assertEqual(refresh_session.parse_flexible_time("05:00"), (5, 0))
        self.assertEqual(refresh_session.parse_flexible_time("5:00"), (5, 0))
        self.assertEqual(refresh_session.parse_flexible_time("14:30"), (14, 30))
        self.assertEqual(refresh_session.parse_flexible_time("9:15"), (9, 15))
        self.assertEqual(refresh_session.parse_flexible_time("00:00"), (0, 0))
        self.assertEqual(refresh_session.parse_flexible_time("23:59"), (23, 59))

    def test_parse_flexible_time_short(self) -> None:
        """Parses short hour formats like 5h, 6h, 5, 6."""
        self.assertEqual(refresh_session.parse_flexible_time("5h"), (5, 0))
        self.assertEqual(refresh_session.parse_flexible_time("6H"), (6, 0))
        self.assertEqual(refresh_session.parse_flexible_time("14h"), (14, 0))
        self.assertEqual(refresh_session.parse_flexible_time("5"), (5, 0))
        self.assertEqual(refresh_session.parse_flexible_time("6"), (6, 0))

    def test_parse_flexible_time_ampm(self) -> None:
        """Parses 12-hour AM/PM formats."""
        self.assertEqual(refresh_session.parse_flexible_time("5am"), (5, 0))
        self.assertEqual(refresh_session.parse_flexible_time("5:30am"), (5, 30))
        self.assertEqual(refresh_session.parse_flexible_time("6pm"), (18, 0))
        self.assertEqual(refresh_session.parse_flexible_time("12pm"), (12, 0))
        self.assertEqual(refresh_session.parse_flexible_time("12am"), (0, 0))

    def test_parse_flexible_time_invalid(self) -> None:
        """Rejects out of range or malformed time values."""
        for invalid in ("25:00", "-1h", "abc", "", "5:65", "24:00", "13pm"):
            with self.assertRaises(ValueError):
                refresh_session.parse_flexible_time(invalid)

    def test_build_darwin_plist(self) -> None:
        """Generates launchd plist XML with correct paths, schedule, and environment."""
        plist = refresh_session.build_darwin_plist(
            script_path="/path/to/refresh_session.py",
            hour=5,
            minute=0,
            target="all",
        )
        self.assertIn("<key>Label</key>", plist)
        self.assertIn("<string>com.d3nexus.refresh-session</string>", plist)
        self.assertIn("<key>Hour</key>", plist)
        self.assertIn("<integer>5</integer>", plist)
        self.assertIn("<key>Minute</key>", plist)
        self.assertIn("<integer>0</integer>", plist)
        self.assertIn("/path/to/refresh_session.py", plist)
        self.assertIn("<key>EnvironmentVariables</key>", plist)
        self.assertIn("<key>PATH</key>", plist)
        self.assertIn("refresh_session_daemon.log", plist)

    @patch("subprocess.run")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.write_text")
    def test_schedule_install_darwin(
        self, mock_write: MagicMock, mock_mkdir: MagicMock, mock_run: MagicMock
    ) -> None:
        """Installs launchd plist and loads it via launchctl."""
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        res = refresh_session.install_schedule_darwin(5, 0, target="all")
        self.assertTrue(res["success"])
        self.assertEqual(res["hour"], 5)
        self.assertEqual(res["minute"], 0)
        self.assertEqual(mock_run.call_count, 2)  # unload and load

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.read_text", return_value="<integer>5</integer><integer>30</integer>")
    @patch("subprocess.run")
    def test_schedule_status_darwin_active(
        self, mock_run: MagicMock, mock_read: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Reports active status when plist exists and daemon is loaded."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="com.d3nexus.refresh-session\n"
        )
        status = refresh_session.get_schedule_status_darwin()
        self.assertTrue(status["installed"])
        self.assertTrue(status["loaded"])
        self.assertEqual(status["hour"], 5)
        self.assertEqual(status["minute"], 30)

    @patch("pathlib.Path.exists", return_value=False)
    @patch("subprocess.run")
    def test_schedule_status_darwin_inactive(
        self, mock_run: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Reports inactive status when plist does not exist."""
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=1, stdout="")
        status = refresh_session.get_schedule_status_darwin()
        self.assertFalse(status["installed"])
        self.assertFalse(status["loaded"])

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.unlink")
    @patch("subprocess.run")
    def test_schedule_uninstall_darwin(
        self, mock_run: MagicMock, mock_unlink: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Unloads launchd service and removes plist file."""
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        res = refresh_session.uninstall_schedule_darwin()
        self.assertTrue(res["success"])
        mock_unlink.assert_called_once()
        mock_run.assert_called_once()

    def test_parse_arguments_schedule_subcommand(self) -> None:
        """Parses schedule subcommand arguments including --time, --target, and --status."""
        args_inst = refresh_session.parse_args(["schedule", "--time", "05:00", "--target", "claude"])
        self.assertEqual(args_inst.command, "schedule")
        self.assertEqual(args_inst.time, "05:00")
        self.assertEqual(args_inst.target, "claude")

        args_status = refresh_session.parse_args(["schedule", "--status"])
        self.assertEqual(args_status.command, "schedule")
        self.assertTrue(args_status.status)

        args_uninst = refresh_session.parse_args(["schedule", "--uninstall"])
        self.assertEqual(args_uninst.command, "schedule")
        self.assertTrue(args_uninst.uninstall)

        args_rem = refresh_session.parse_args(["schedule", "--remove"])
        self.assertEqual(args_rem.command, "schedule")
        self.assertTrue(args_rem.uninstall)

    @patch("refresh_session.install_schedule", return_value={"success": True, "platform": "darwin"})
    def test_main_schedule_install(self, mock_install: MagicMock) -> None:
        """Main dispatches schedule install and returns exit code 0."""
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            code = refresh_session.main(["schedule", "--time", "05:00", "--target", "codex"])
        self.assertEqual(code, 0)
        mock_install.assert_called_once_with(5, 0, target="codex")

    @patch("refresh_session.get_schedule_status", return_value={"installed": True, "loaded": True, "hour": 5, "minute": 0, "target": "all"})
    def test_main_schedule_status(self, mock_status: MagicMock) -> None:
        """Main queries schedule status and outputs details."""
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            code = refresh_session.main(["schedule", "--status"])
        self.assertEqual(code, 0)
        self.assertIn("ACTIVE", out.getvalue())
        self.assertIn("05:00", out.getvalue())

    @patch("refresh_session.uninstall_schedule", return_value={"success": True, "platform": "darwin"})
    def test_main_schedule_uninstall(self, mock_uninst: MagicMock) -> None:
        """Main dispatches uninstall and returns exit code 0."""
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            code = refresh_session.main(["schedule", "--uninstall"])
        self.assertEqual(code, 0)
        mock_uninst.assert_called_once()

    def test_main_schedule_no_args_error(self) -> None:
        """Main exits with code 1 when schedule subcommand has no action flags."""
        import io
        from contextlib import redirect_stderr

        err = io.StringIO()
        with redirect_stderr(err):
            code = refresh_session.main(["schedule"])
        self.assertEqual(code, 1)
        self.assertIn("Usage:", err.getvalue())


if __name__ == "__main__":
    unittest.main()
