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

    @patch("refresh_session.is_target_session_active", return_value=(False, ""))
    @patch("refresh_session.ping_cli")
    def test_main_json_output(self, mock_ping: MagicMock, mock_active: MagicMock) -> None:
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
    @patch("refresh_session.is_target_session_active", return_value=(False, ""))
    @patch("refresh_session.ping_cli", return_value={"cli": "claude", "status": "PASS", "latency_ms": 10.0, "tokens": 1, "error": None})
    def test_main_delay_sleep_invoked(self, mock_ping: MagicMock, mock_active: MagicMock, mock_sleep: MagicMock) -> None:
        """Invokes time.sleep when delay > 0 before pinging."""
        code = refresh_session.main(["claude", "--delay", "30"])
        self.assertEqual(code, 0)
        mock_sleep.assert_called_once_with(30)

    def test_parse_arguments_profile_target(self) -> None:
        """Accepts known profile names as targets."""
        args = refresh_session.parse_args(["danhdue"])
        self.assertEqual(args.target, "danhdue")

    @patch("time.sleep")
    @patch("subprocess.run")
    @patch("os.path.isdir", return_value=True)
    @patch("shutil.which", return_value="/opt/homebrew/bin/agy")
    def test_ping_profile_success(self, mock_which: MagicMock, mock_isdir: MagicMock, mock_run: MagicMock, mock_sleep: MagicMock) -> None:
        """Pings profile using agy and returns PASS when returncode is 0."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"status": "ok"}'
        mock_run.return_value = mock_proc

        res = refresh_session.ping_profile("danhdue")
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["profile"], "danhdue")
        self.assertGreaterEqual(res["tokens"], 1)
        # Ensure both Gemini 5H and Claude 5H were called
        all_cmds = [c[0][0] for c in mock_run.call_args_list]
        gemini_cmds = [c for c in all_cmds if "-p" in c and "claude-sonnet-5-5-low" not in c and "gemini-4-argon-low" not in c]
        claude_cmds = [c for c in all_cmds if "claude-sonnet-5-5-low" in c]
        self.assertTrue(len(gemini_cmds) >= 1)
        self.assertTrue(len(claude_cmds) >= 1)

    @patch("time.sleep")
    @patch("refresh_session.check_profile_has_argon", return_value=True)
    @patch("subprocess.run")
    @patch("os.path.isdir", return_value=True)
    @patch("shutil.which", return_value="/opt/homebrew/bin/agy")
    def test_ping_profile_all_three_models_with_argon(self, mock_which: MagicMock, mock_isdir: MagicMock, mock_run: MagicMock, mock_argon: MagicMock, mock_sleep: MagicMock) -> None:
        """Pings all 3 models (Gemini 5H, Claude 5H, and Argon 7D) when profile has Argon."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"status": "ok"}'
        mock_run.return_value = mock_proc

        res = refresh_session.ping_profile("brother")
        self.assertEqual(res["status"], "PASS")
        self.assertIn("Gemini 5H", res.get("models_pinged", []))
        self.assertIn("Claude 5H", res.get("models_pinged", []))
        self.assertIn("Argon 7D", res.get("models_pinged", []))
        self.assertEqual(res["tokens"], 3)
        self.assertEqual(mock_sleep.call_count, 2)

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


class TestMultiScheduleAndAntigravityPing(unittest.TestCase):
    """Tests REAL_HOME macOS LaunchAgents multi-schedule & Antigravity model discovery."""

    def test_resolve_darwin_dirs_uses_real_home_not_sandboxed_home(self) -> None:
        """DARWIN_PLIST_DIR and LOG_DIR must point under REAL_HOME, never antigravity_homes/<p>."""
        plist_dir, log_dir = refresh_session._resolve_darwin_dirs("/Users/realuser")
        self.assertEqual(plist_dir, Path("/Users/realuser/Library/LaunchAgents"))
        self.assertEqual(log_dir, Path("/Users/realuser/.devtool/logs"))
        # Module constants must never resolve under antigravity_homes/
        self.assertNotIn("antigravity_homes", str(refresh_session.DARWIN_PLIST_DIR))
        self.assertNotIn("antigravity_homes", str(refresh_session.LOG_DIR))

    def test_check_profile_has_argon_handles_trailing_semicolon_js(self) -> None:
        """check_profile_has_argon parses const PROFILES_DATA = {...}; even with trailing semicolon."""
        import tempfile

        html = (
            "<html><script>\n"
            'const PROFILES_DATA = {\n  "brother": {"hasArgon": true},\n  "mau": {"hasArgon": false}\n};\n'
            "</script></html>"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "quota_dashboard.html"
            html_path.write_text(html, encoding="utf-8")
            with patch.object(refresh_session, "_DASHBOARD_HTML_CANDIDATES", [html_path]):
                self.assertTrue(refresh_session.check_profile_has_argon("brother"))
                self.assertFalse(refresh_session.check_profile_has_argon("mau"))

    def test_multi_schedule_darwin_preserves_independent_slots_and_profiles(self) -> None:
        """Installing multiple time slots / targets keeps independent LaunchAgents and cleans broken symlinks."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            plist_dir = Path(tmpdir) / "LaunchAgents"
            log_dir = Path(tmpdir) / "logs"
            plist_dir.mkdir(parents=True)
            log_dir.mkdir(parents=True)

            # Create a broken symlink (mimics stale /Users/danhdueexoictif/Library/LaunchAgents/com.d3nexus.refresh-session.plist)
            broken = plist_dir / f"{refresh_session.DARWIN_LABEL}.plist"
            broken.symlink_to("/nonexistent/antigravity_homes/huynhminhtien0510/Library/LaunchAgents/com.d3nexus.refresh-session.plist")
            self.assertTrue(broken.is_symlink())

            loaded_labels: set[str] = set()

            def fake_run(cmd, **kwargs):
                proc = MagicMock(returncode=0, stdout="", stderr="")
                if cmd[:2] == ["launchctl", "bootstrap"]:
                    plist_file = Path(cmd[3])
                    for match in __import__("re").findall(
                        r"<key>Label</key>\s*<string>([^<]+)</string>",
                        plist_file.read_text(encoding="utf-8"),
                    ):
                        loaded_labels.add(match)
                elif cmd[:2] == ["launchctl", "bootout"]:
                    svc = cmd[2]
                    if "/" in svc:
                        loaded_labels.discard(svc.rsplit("/", 1)[-1])
                elif cmd[:2] == ["launchctl", "list"]:
                    proc.stdout = "\n".join(f"123\t0\t{lbl}" for lbl in sorted(loaded_labels))
                return proc

            with (
                patch.object(refresh_session, "DARWIN_PLIST_DIR", plist_dir),
                patch.object(refresh_session, "DARWIN_PLIST_PATH", broken),
                patch.object(refresh_session, "LOG_DIR", log_dir),
                patch.object(refresh_session, "REAL_HOME_DIR", Path(tmpdir)),
                patch("subprocess.run", side_effect=fake_run),
            ):
                # Slot 1: brother at 05:00
                r1 = refresh_session.install_schedule_darwin(5, 0, target="brother", delay=30)
                self.assertTrue(r1["success"])
                self.assertFalse(broken.is_symlink())

                # Slot 2: hau & danhdue at 07:00
                r2 = refresh_session.install_schedule_darwin(7, 0, target="hau,danhdue", delay=15)
                self.assertTrue(r2["success"])

                # Slot 3: same profile brother ALSO at 12:30 (multi-time-slot!)
                r3 = refresh_session.install_schedule_darwin(12, 30, target="brother", delay=30)
                self.assertTrue(r3["success"])

                status = refresh_session.get_schedule_status_darwin()
                self.assertTrue(status["installed"])
                self.assertEqual(len(status["schedules"]), 3)
                self.assertEqual(len(status["by_profile"]["brother"]), 2)
                self.assertEqual(
                    {s["time"] for s in status["by_profile"]["brother"]},
                    {"05:00", "12:30"},
                )
                self.assertEqual(
                    {s["time"] for s in status["by_profile"]["hau"]},
                    {"07:00"},
                )

                # Verify clean HOME & no antigravity_homes in PATH inside generated plist
                sample_plist = Path(status["schedules"][0]["plist_path"]).read_text(encoding="utf-8")
                self.assertIn("<key>EnvironmentVariables</key>", sample_plist)
                self.assertIn(f"<string>{tmpdir}</string>", sample_plist)
                self.assertNotIn("antigravity_homes", sample_plist)

                # Remove brother ONLY from 05:00 -> keeps 12:30 and 07:00
                u1 = refresh_session.uninstall_schedule_darwin(target="brother", time_str="05:00")
                self.assertTrue(u1["success"])
                status_after = refresh_session.get_schedule_status_darwin()
                self.assertEqual(len(status_after["schedules"]), 2)
                self.assertEqual([s["time"] for s in status_after["by_profile"]["brother"]], ["12:30"])

                # Remove hau from 07:00 -> 07:00 plist stays alive for danhdue only!
                u2 = refresh_session.uninstall_schedule_darwin(target="hau")
                self.assertTrue(u2["success"])
                status_after2 = refresh_session.get_schedule_status_darwin()
                self.assertEqual(len(status_after2["schedules"]), 2)
                self.assertNotIn("hau", status_after2["by_profile"])
                self.assertEqual([s["time"] for s in status_after2["by_profile"]["danhdue"]], ["07:00"])

    def test_install_schedule_darwin_fails_when_launchctl_fails(self) -> None:
        """If launchctl bootstrap and load both fail, install_schedule_darwin returns success=False."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            plist_dir = Path(tmpdir) / "LaunchAgents"
            log_dir = Path(tmpdir) / "logs"
            plist_dir.mkdir(parents=True)
            log_dir.mkdir(parents=True)

            def fake_fail(cmd, **kwargs):
                if cmd[:2] in (["launchctl", "bootstrap"], ["launchctl", "load"]):
                    return MagicMock(returncode=5, stdout="", stderr="Bootstrap failed: Input/output error")
                return MagicMock(returncode=0, stdout="", stderr="")

            with (
                patch.object(refresh_session, "DARWIN_PLIST_DIR", plist_dir),
                patch.object(refresh_session, "DARWIN_PLIST_PATH", plist_dir / "com.d3nexus.refresh-session.plist"),
                patch.object(refresh_session, "LOG_DIR", log_dir),
                patch.object(refresh_session, "REAL_HOME_DIR", Path(tmpdir)),
                patch("subprocess.run", side_effect=fake_fail),
            ):
                res = refresh_session.install_schedule_darwin(7, 0, target="brother", delay=30)
                self.assertFalse(res["success"])
                self.assertIn("error", res)

    def test_ping_profile_uses_discovered_claude_4_6_and_reports_argon_failure(self) -> None:
        """ping_profile uses explicit --model for Gemini, selects claude-sonnet-4-6 when 5.5 absent, and surfaces Argon error."""
        now_utc = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        fresh_5h = (now_utc + __import__("datetime").timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        fresh_7d = (now_utc + __import__("datetime").timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        usage_json = json.dumps({
            "command": {
                "data": {
                    "plan_name": "PRO",
                    "groups": [
                        {"name": "Gemini Models", "buckets": [{"window": "5h", "remaining_fraction": 1.0, "reset_time": fresh_5h}]},
                        {"name": "Claude and GPT models", "buckets": [{"window": "5h", "remaining_fraction": 1.0, "reset_time": fresh_5h}]},
                        {"name": "Argon", "buckets": [{"window": "weekly", "remaining_fraction": 1.0, "reset_time": fresh_7d}]},
                    ],
                }
            }
        })

        def fake_run(cmd, **kwargs):
            if cmd[1:2] == ["models"]:
                return MagicMock(
                    returncode=0,
                    stdout="gemini-3.8-flash-low\tGemini\nclaude-sonnet-4-6\tClaude 4.6\ngemini-4-argon-low\tArgon\n",
                    stderr="",
                )
            if "/usage" in cmd:
                return MagicMock(returncode=0, stdout=usage_json, stderr="")
            if "gemini-4-argon-low" in cmd:
                return MagicMock(returncode=1, stdout="", stderr="Timeout error on argon")
            return MagicMock(returncode=0, stdout="OK", stderr="")

        import tempfile

        with (
            tempfile.TemporaryDirectory() as db_tmp,
            patch.object(refresh_session, "REAL_HOME", db_tmp),
            patch("shutil.which", return_value="/usr/local/bin/agy"),
            patch("os.path.exists", side_effect=lambda p: str(p) == "/usr/local/bin/agy"),
            patch("os.path.isdir", return_value=True),
            patch("os.makedirs"),
            patch.object(refresh_session, "SESSION_STORE_DB", Path(db_tmp) / ".session_store.db"),
            patch("refresh_session.check_profile_auth_token", return_value=True),
            patch("subprocess.run", side_effect=fake_run) as mock_run,
            patch("time.sleep"),
        ):
            res = refresh_session.ping_profile("d3molt")
            self.assertEqual(res["status"], "FAIL")
            self.assertIn("Argon", res["error"])
            ping_cmds = [c.args[0] for c in mock_run.call_args_list if "-p" in c.args[0] and "/usage" not in c.args[0]]
            self.assertEqual(len(ping_cmds), 3)
            self.assertIn("gemini-3.8-flash-low", ping_cmds[0])
            self.assertIn("claude-sonnet-4-6", ping_cmds[1])
            self.assertIn("gemini-4-argon-low", ping_cmds[2])
            for c in mock_run.call_args_list:
                if "-p" in c.args[0] and "/usage" not in c.args[0]:
                    self.assertGreaterEqual(c.kwargs.get("timeout", 0), 45)
                    self.assertIsNotNone(c.kwargs.get("cwd"))

    def test_is_target_session_active_claude_uses_live_api_and_zero_util(self) -> None:
        """is_target_session_active('claude') queries live API first and catches 0% active 5H sessions."""
        import os
        import tempfile
        import urllib.request

        now_utc = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        active_4h = (now_utc + __import__("datetime").timedelta(hours=4)).isoformat()
        idle_payload = {
            "five_hour": {"utilization": 0.0, "resets_at": None},
            "seven_day": {"utilization": 66.0, "resets_at": active_4h},
            "limits": [{"kind": "session", "is_active": False, "resets_at": None}],
        }
        active_payload = {
            "five_hour": {"utilization": 0.0, "resets_at": active_4h},
            "seven_day": {"utilization": 66.0, "resets_at": active_4h},
            "limits": [{"kind": "session", "is_active": True, "resets_at": active_4h}],
        }

        def make_resp(payload: dict) -> MagicMock:
            m = MagicMock()
            m.status = 200
            m.read.return_value = json.dumps(payload).encode("utf-8")
            m.__enter__.return_value = m
            return m

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch.object(refresh_session, "REAL_HOME", tmpdir),
                patch.object(refresh_session, "REAL_HOME_DIR", Path(tmpdir)),
                patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "tok-test"}, clear=False),
                patch.object(
                    urllib.request,
                    "urlopen",
                    side_effect=[make_resp(idle_payload), make_resp(active_payload)],
                ),
            ):
                is_act_idle, _ = refresh_session.is_target_session_active("claude")
                self.assertFalse(is_act_idle)

                is_act_running, msg = refresh_session.is_target_session_active("claude")
                self.assertTrue(is_act_running)
                self.assertIn("Session active", msg)

    def test_is_target_session_active_codex_uses_live_api_and_falls_back_to_sqlite(self) -> None:
        """is_target_session_active('codex') prefers live wham/usage over SQLite and skips ticking 0% 5H."""
        import sqlite3
        import tempfile
        import time
        import urllib.request

        with tempfile.TemporaryDirectory() as tmpdir:
            codex_dir = Path(tmpdir) / ".codex"
            codex_dir.mkdir(parents=True)
            (codex_dir / "auth.json").write_text(
                json.dumps({"tokens": {"access_token": "codex-tok", "account_id": "acc"}}),
                encoding="utf-8",
            )
            db_path = codex_dir / "logs_2.sqlite"
            con = sqlite3.connect(str(db_path))
            con.execute("CREATE TABLE logs (ts INTEGER);")
            con.execute("INSERT INTO logs (ts) VALUES (?);", (int(time.time()) - 1000,))
            con.commit()
            con.close()

            idle_rl = {
                "rate_limit": {
                    "primary_window": {
                        "used_percent": 0,
                        "limit_window_seconds": 18000,
                        "reset_after_seconds": 18000,
                    }
                }
            }
            ticking_rl = {
                "rate_limit": {
                    "primary_window": {
                        "used_percent": 0,
                        "limit_window_seconds": 18000,
                        "reset_after_seconds": 17500,
                    }
                }
            }

            def make_resp(payload: dict) -> MagicMock:
                m = MagicMock()
                m.status = 200
                m.read.return_value = json.dumps(payload).encode("utf-8")
                m.__enter__.return_value = m
                return m

            with (
                patch.object(refresh_session, "REAL_HOME", tmpdir),
                patch.object(refresh_session, "REAL_HOME_DIR", Path(tmpdir)),
                patch.object(
                    urllib.request,
                    "urlopen",
                    side_effect=[
                        make_resp(idle_rl),
                        make_resp(ticking_rl),
                        OSError("network down"),
                    ],
                ),
            ):
                # 1. Live API explicitly IDLE must win even if SQLite has recent ts
                act1, _ = refresh_session.is_target_session_active("codex")
                self.assertFalse(act1)

                # 2. Live API ticking (< 18000 - 30) skips even when used_percent == 0
                act2, msg2 = refresh_session.is_target_session_active("codex")
                self.assertTrue(act2)
                self.assertIn("Session active", msg2)

                # 3. Offline Live API -> SQLite fallback detects < 5h log
                act3, msg3 = refresh_session.is_target_session_active("codex")
                self.assertTrue(act3)
                self.assertIn("Session active", msg3)

    def test_check_profile_auth_token_uses_fallback_oauth_file(self) -> None:
        """Fallback OAuth token files keep profile authenticated when Keychain lacks item."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            profile_home = Path(tmpdir) / "antigravity_homes" / "duedd"
            kc_path = profile_home / "Library" / "Keychains" / "duedd.keychain-db"
            kc_path.parent.mkdir(parents=True)
            kc_path.write_bytes(b"placeholder")
            cli_tok = profile_home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
            cli_tok.parent.mkdir(parents=True)
            cli_tok.write_text(
                json.dumps({"token": {"access_token": "ya29.ok", "refresh_token": "1//ok"}}),
                encoding="utf-8",
            )

            missing_kc = MagicMock(returncode=44, stdout="", stderr="")
            with (
                patch.object(refresh_session, "REAL_HOME", tmpdir),
                patch("subprocess.run", return_value=missing_kc),
            ):
                self.assertTrue(refresh_session.check_profile_auth_token("duedd"))

                cli_tok.write_text("{}", encoding="utf-8")
                self.assertFalse(refresh_session.check_profile_auth_token("duedd"))


if __name__ == "__main__":
    unittest.main()
