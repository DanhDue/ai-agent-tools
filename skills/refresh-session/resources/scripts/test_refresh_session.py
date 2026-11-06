#!/usr/bin/env python3
"""Unit tests for refresh_session.py engine and CLI commands."""
from __future__ import annotations

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
        """Target defaults to 'providers' (Claude & Codex only), timeout to 60, json to False."""
        args = refresh_session.parse_args([])
        self.assertEqual(args.target, "providers")
        self.assertEqual(args.timeout, 60)
        self.assertFalse(args.json)

    def test_parse_arguments_targets(self) -> None:
        """Parses valid target arguments: claude, codex, providers, and all."""
        for target in ("claude", "codex", "providers", "all"):
            args = refresh_session.parse_args([target])
            self.assertEqual(args.target, target)

    def test_parse_arguments_multi_targets(self) -> None:
        """Parses comma-separated and space-separated target combinations."""
        args = refresh_session.parse_args(["claude,codex,danhdue"])
        self.assertEqual(args.target, "claude,codex,danhdue")

        args_space = refresh_session.parse_args(["claude", "codex", "danhdue"])
        self.assertEqual(args_space.target, "claude,codex,danhdue")

        args_sched = refresh_session.parse_args(["schedule", "--time", "05:30", "--target", "claude,codex,danhdue,hau"])
        self.assertEqual(args_sched.target, "claude,codex,danhdue,hau")

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
        mock_install.assert_called_once_with(5, 0, target="codex", delay=30)

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

    def test_parse_arguments_delay_defaults(self) -> None:
        """On-demand pings default to delay 0; schedule subcommand defaults to delay 30."""
        args_ping = refresh_session.parse_args(["claude"])
        self.assertEqual(args_ping.delay, 0)

        args_sched = refresh_session.parse_args(["schedule", "--time", "05:00"])
        self.assertEqual(args_sched.delay, 30)

    def test_parse_arguments_delay_custom(self) -> None:
        """Accepts custom --delay and --offset across root and schedule subparsers."""
        args_delay = refresh_session.parse_args(["claude", "--delay", "45"])
        self.assertEqual(args_delay.delay, 45)

        args_offset = refresh_session.parse_args(["schedule", "--time", "05:00", "--offset", "15"])
        self.assertEqual(args_offset.delay, 15)

    def test_build_darwin_plist_with_delay(self) -> None:
        """Builds launchd plist including --delay argument when delay > 0."""
        plist = refresh_session.build_darwin_plist("/path/to/script.py", 5, 0, target="all", delay=30)
        self.assertIn("<string>--delay</string>", plist)
        self.assertIn("<string>30</string>", plist)

    @patch("time.sleep")
    @patch("refresh_session.ping_cli", return_value={"cli": "claude", "status": "PASS", "latency_ms": 10.0, "tokens": 1, "error": None})
    def test_main_delay_sleep_invoked(self, mock_ping: MagicMock, mock_sleep: MagicMock) -> None:
        """Invokes time.sleep when delay > 0 before pinging."""
        code = refresh_session.main(["claude", "--delay", "30"])
        self.assertEqual(code, 0)
        mock_sleep.assert_called_once_with(30)

    def test_parse_arguments_profile_target(self) -> None:
        """Accepts known profile names as targets."""
        args = refresh_session.parse_args(["danhdue"])
        self.assertEqual(args.target, "danhdue")

    @patch("subprocess.run")
    @patch("os.path.isdir", return_value=True)
    @patch("shutil.which", return_value="/opt/homebrew/bin/agy")
    def test_ping_profile_success(self, mock_which: MagicMock, mock_isdir: MagicMock, mock_run: MagicMock) -> None:
        """Pings profile using agy and returns PASS when returncode is 0."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"status": "ok"}'
        mock_run.return_value = mock_proc

        res = refresh_session.ping_profile("danhdue")
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["profile"], "danhdue")
        self.assertIn(res["tokens"], (0, 1))

    @patch("refresh_session.ping_profile", return_value={"cli": "agy (danhdue)", "profile": "danhdue", "status": "PASS", "latency_ms": 110.0, "tokens": 0, "error": None})
    def test_main_profile_dispatch(self, mock_ping_prof: MagicMock) -> None:
        """Dispatches to ping_profile when target is an Antigravity profile."""
        code = refresh_session.main(["danhdue", "--force"])
        self.assertEqual(code, 0)
        mock_ping_prof.assert_called_once_with("danhdue", timeout=60)

    @patch("refresh_session.get_known_profiles", return_value=["danhdue"])
    @patch("refresh_session.ping_profile", return_value={"cli": "agy (danhdue)", "profile": "danhdue", "status": "PASS", "latency_ms": 10.0, "tokens": 0, "error": None})
    @patch("refresh_session.ping_cli", return_value={"cli": "claude", "status": "PASS", "latency_ms": 10.0, "tokens": 1, "error": None})
    def test_main_all_dispatches_clis_and_profiles(self, mock_ping_cli: MagicMock, mock_ping_prof: MagicMock, mock_known: MagicMock) -> None:
        """Target 'all' must ping Claude, Codex, and all known profiles."""
        code = refresh_session.main(["all", "--force"])
        self.assertEqual(code, 0)
        self.assertEqual(mock_ping_cli.call_count, 2)
        mock_ping_prof.assert_called_once_with("danhdue", timeout=60)

    @patch("refresh_session.ping_cli", return_value={"cli": "claude", "status": "PASS", "latency_ms": 10.0, "tokens": 1, "error": None})
    def test_main_clis_dispatches_claude_and_codex(self, mock_ping_cli: MagicMock) -> None:
        """Target 'clis' must ping Claude and Codex."""
        code = refresh_session.main(["clis", "--force"])
        self.assertEqual(code, 0)
        self.assertEqual(mock_ping_cli.call_count, 2)

    @patch("refresh_session.get_known_profiles", return_value=["danhdue", "hau"])
    @patch("refresh_session.ping_profile", return_value={"cli": "agy", "profile": "danhdue", "status": "PASS", "latency_ms": 10.0, "tokens": 0, "error": None})
    @patch("refresh_session.ping_cli", return_value={"cli": "claude", "status": "PASS", "latency_ms": 10.0, "tokens": 1, "error": None})
    def test_main_multi_targets_combination(self, mock_ping_cli: MagicMock, mock_ping_prof: MagicMock, mock_known: MagicMock) -> None:
        """Comma-separated target list dispatches exact subset specified."""
        code = refresh_session.main(["claude,codex,danhdue,hau", "--force"])
        self.assertEqual(code, 0)
        self.assertEqual(mock_ping_cli.call_count, 2)  # claude and codex
        self.assertEqual(mock_ping_prof.call_count, 2)  # danhdue and hau

    @patch("refresh_session.is_target_session_active", return_value=(True, "Session active (3h remaining)"))
    def test_main_skips_when_session_active(self, mock_check: MagicMock) -> None:
        """When session is active and no --force, ping is skipped."""
        code = refresh_session.main(["claude"])
        self.assertEqual(code, 0)
        mock_check.assert_called_with("claude")


if __name__ == "__main__":
    unittest.main()
