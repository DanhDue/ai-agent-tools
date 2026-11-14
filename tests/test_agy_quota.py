"""Unit tests for Antigravity Quota Dashboard & Web Server Daemon."""

from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import agy_quota  # noqa: E402


class TestAgyQuotaServer(unittest.TestCase):
    """Test suite verifying Quota Server daemon, PID handling, and CLI commands."""

    def test_is_server_alive_false_on_closed_port(self):
        """is_server_alive returns False when port has no HTTP listener."""
        self.assertFalse(agy_quota.is_server_alive(port=59998))

    def test_get_server_pid_empty_when_no_file(self):
        """get_server_pid returns None when PID file does not exist."""
        mock_file = MagicMock()
        mock_file.is_file.return_value = False
        with (
            patch.object(agy_quota, "PID_FILE", mock_file),
            patch("subprocess.check_output", return_value=""),
        ):
            self.assertIsNone(agy_quota.get_server_pid(port=59998))

    def test_get_server_pid_reads_valid_pid(self):
        """get_server_pid parses PID file integer when process is alive."""
        mock_file = MagicMock()
        mock_file.is_file.return_value = True
        mock_file.read_text.return_value = "12345"
        with (
            patch.object(agy_quota, "PID_FILE", mock_file),
            patch("os.kill", return_value=None),
        ):
            self.assertEqual(agy_quota.get_server_pid(port=59998), 12345)

    def test_stop_server_when_not_running(self):
        """stop_server gracefully returns False when server is not running."""
        with (
            patch("agy_quota.get_server_pid", return_value=None),
            patch("agy_quota.is_server_alive", return_value=False),
        ):
            res = agy_quota.stop_server(port=59998)
            self.assertFalse(res)

    def test_cli_help_includes_daemon_options(self):
        """Help screen displays --ui, --stop, and --status options."""
        captured = io.StringIO()
        with (
            patch("sys.stdout", captured),
            patch("sys.argv", ["agy_quota.py", "--help"]),
        ):
            agy_quota.main()
        output = captured.getvalue()
        self.assertIn("check-quota --ui", output)
        self.assertIn("check-quota --stop", output)
        self.assertIn("check-quota --status", output)

    def test_log_message_resilient_to_broken_pipe(self):
        """Handler log_message must never crash even if stdout raises BrokenPipeError."""
        mock_handler = MagicMock()
        mock_handler.path = "/api/status"
        mock_handler.command = "GET"
        with patch("sys.stdout.write", side_effect=BrokenPipeError("Broken pipe")):
            # Must not raise exception
            agy_quota.QuotaDashboardHandler.log_message(
                mock_handler, "%s", "GET /api/status", "200"
            )

    def test_argon_ping_skipped_when_already_activated(self):
        """Argon must NOT be pinged when it is already activated and counting down."""
        now_utc = agy_quota.datetime.datetime.now(agy_quota.datetime.timezone.utc)
        active_3h = (now_utc + agy_quota.datetime.timedelta(hours=3)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        far_reset = (now_utc + agy_quota.datetime.timedelta(days=2)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        live_quota = {
            "success": True,
            "tier": "PRO",
            "groups": [
                {
                    "name": "Gemini Models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 0.85,
                            "reset_time": active_3h,
                            "description": "You have used some of your Gemini limit.",
                        }
                    ],
                },
                {
                    "name": "Claude and GPT models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 0.90,
                            "reset_time": active_3h,
                            "description": "You have used some of your Claude limit.",
                        }
                    ],
                },
                {
                    "name": "Argon",
                    "buckets": [
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.45,
                            "reset_time": far_reset,
                        }
                    ],
                },
            ],
        }
        with (
            patch("os.path.isdir", return_value=True),
            patch("agy_quota.check_profile_appeal_status", return_value=None),
            patch("agy_quota.check_profile_auth_token", return_value=True),
            patch("agy_quota.load_cached_profiles", return_value={}),
            patch("agy_quota.fetch_quota_for_profile", return_value=live_quota),
        ):
            res = agy_quota.execute_ping_profile("test_prof")
            self.assertTrue(res.get("skipped"))
            self.assertIn("Argon đã kích hoạt", res.get("message", ""))

    def test_argon_ping_skipped_when_near_reset(self):
        """Argon must NOT be pinged when reset time is less than 7 hours away."""
        now_utc = agy_quota.datetime.datetime.now(agy_quota.datetime.timezone.utc)
        active_3h = (now_utc + agy_quota.datetime.timedelta(hours=3)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        soon_reset = (now_utc + agy_quota.datetime.timedelta(hours=3)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        live_quota = {
            "success": True,
            "tier": "PRO",
            "groups": [
                {
                    "name": "Gemini Models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 0.85,
                            "reset_time": active_3h,
                        }
                    ],
                },
                {
                    "name": "Claude and GPT models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 0.90,
                            "reset_time": active_3h,
                        }
                    ],
                },
                {
                    "name": "Argon",
                    "buckets": [
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.20,
                            "reset_time": soon_reset,
                        }
                    ],
                },
            ],
        }
        with (
            patch("os.path.isdir", return_value=True),
            patch("agy_quota.check_profile_appeal_status", return_value=None),
            patch("agy_quota.check_profile_auth_token", return_value=True),
            patch("agy_quota.load_cached_profiles", return_value={}),
            patch("agy_quota.fetch_quota_for_profile", return_value=live_quota),
        ):
            res = agy_quota.execute_ping_profile("test_prof")
            self.assertTrue(res.get("skipped"))
            self.assertIn("Argon < 7h", res.get("message", ""))

    def test_argon_ping_triggered_when_max_7d(self):
        """Argon MUST be pinged with jitter when it is at max 7D."""
        now_utc = agy_quota.datetime.datetime.now(agy_quota.datetime.timezone.utc)
        max_7d_reset = (now_utc + agy_quota.datetime.timedelta(days=7)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        mock_cached = {
            "test_prof": {
                "hasArgon": True,
                "argonWeekly": {
                    "fraction": 1.0,
                    "resetTime": max_7d_reset,
                    "unavailable": False,
                },
            }
        }
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "OK"
        mock_res.stderr = ""

        with (
            patch("os.path.isdir", return_value=True),
            patch("agy_quota.check_profile_appeal_status", return_value=None),
            patch("agy_quota.check_profile_auth_token", return_value=True),
            patch("agy_quota.load_cached_profiles", return_value=mock_cached),
            patch("agy_quota.get_session_record", return_value=None),
            patch("subprocess.run", return_value=mock_res) as mock_run,
            patch("agy_quota.fetch_quota_for_profile", return_value={"success": True}),
            patch("agy_quota.format_profile_for_dashboard", return_value={}),
            patch("agy_quota.update_cached_profile"),
            patch("time.sleep") as mock_sleep,
        ):
            res = agy_quota.execute_ping_profile("test_prof")
            self.assertTrue(res.get("success"))
            self.assertTrue(res.get("pinged_argon"))
            self.assertTrue(res.get("pinged_claude"))
            self.assertTrue(res.get("pinged_gemini"))
            self.assertIn("Claude 5.5", res.get("message", ""))
            self.assertIn("Argon 7D", res.get("message", ""))
            # Jitter sleep was called for Claude and Argon
            self.assertEqual(mock_sleep.call_count, 2)
            sleep_val = mock_sleep.call_args[0][0]
            self.assertGreaterEqual(sleep_val, 1.8)
            self.assertLessEqual(sleep_val, 3.5)
            # Subprocess called with default gemini (-p), claude-sonnet-5-5-low and gemini-4-argon-low
            gemini_calls = [
                c
                for c in mock_run.call_args_list
                if "-p" in c[0][0]
                and "claude-sonnet-5-5-low" not in c[0][0]
                and "gemini-4-argon-low" not in c[0][0]
            ]
            self.assertEqual(len(gemini_calls), 1)
            claude_calls = [
                c for c in mock_run.call_args_list if "claude-sonnet-5-5-low" in c[0][0]
            ]
            self.assertEqual(len(claude_calls), 1)
            argon_calls = [
                c for c in mock_run.call_args_list if "gemini-4-argon-low" in c[0][0]
            ]
            self.assertEqual(len(argon_calls), 1)

    def test_probe_blocked_profile_unblocked_success(self):
        """When probe returns 0 and valid quota, account is unblocked with jitter."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps({"command": {"data": {"groups": []}}})
        mock_proc.stderr = ""

        agy_quota.LAST_BLOCKED_PROBE.clear()
        with (
            patch("os.path.isdir", return_value=True),
            patch("agy_quota.check_profile_auth_token", return_value=True),
            patch("subprocess.run", return_value=mock_proc),
            patch("agy_quota.unblock_profile") as mock_unblock,
            patch(
                "agy_quota.format_profile_for_dashboard",
                return_value={"status": "ACTIVE"},
            ),
            patch("agy_quota.update_cached_profile"),
            patch("time.sleep") as mock_sleep,
        ):
            res = agy_quota.probe_blocked_profile("test_blocked")
            self.assertTrue(res.get("success"))
            self.assertTrue(res.get("unblocked"))
            self.assertEqual(res.get("status"), "ACTIVE")
            mock_unblock.assert_called_once_with("test_blocked")
            mock_sleep.assert_called_once()
            sleep_sec = mock_sleep.call_args[0][0]
            self.assertGreaterEqual(sleep_sec, 1.8)
            self.assertLessEqual(sleep_sec, 3.2)

    def test_probe_blocked_profile_cooldown_rejection(self):
        """Probing the same profile within cooldown period must be rejected."""
        agy_quota.LAST_BLOCKED_PROBE["test_cooldown"] = agy_quota.time.time()
        res = agy_quota.probe_blocked_profile("test_cooldown")
        self.assertFalse(res.get("success"))
        self.assertTrue(res.get("cooldown"))
        self.assertIn("Vui lòng đợi thêm", res.get("error", ""))

    def test_probe_blocked_profile_still_disabled(self):
        """When Google returns 'submit an appeal', profile remains DISABLED."""
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "This service has been disabled. Please submit an appeal (err: 12345678-1234-1234-1234-123456789abc)."

        agy_quota.LAST_BLOCKED_PROBE.clear()
        with (
            patch("os.path.isdir", return_value=True),
            patch("agy_quota.check_profile_auth_token", return_value=True),
            patch("subprocess.run", return_value=mock_proc),
            patch("agy_quota.record_profile_disabled") as mock_record,
            patch("agy_quota.update_cached_profile"),
            patch("time.sleep"),
        ):
            res = agy_quota.probe_blocked_profile("test_still_blocked")
            self.assertFalse(res.get("success"))
            self.assertEqual(res.get("status"), "DISABLED")
            self.assertTrue(res.get("is_appeal"))
            mock_record.assert_called_once()

    def test_format_profile_without_argon_group_has_argon_false(self):
        """When quota groups do NOT include Argon, hasArgon must be False and unavailable True."""
        mock_cached = {
            "mau": {
                "email": "mau492974@gmail.com",
                "hasArgon": True,  # Stale cache had True
            }
        }
        res_data = {
            "success": True,
            "groups": [
                {
                    "name": "Gemini Models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 1.0,
                            "reset_time": "2026-11-09T15:00:00Z",
                        },
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.8,
                            "reset_time": "2026-11-14T15:00:00Z",
                        },
                    ],
                },
                {
                    "name": "Claude and GPT models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 1.0,
                            "reset_time": "2026-11-09T15:00:00Z",
                        },
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.9,
                            "reset_time": "2026-11-16T15:00:00Z",
                        },
                    ],
                },
            ],
        }
        with patch("agy_quota.load_cached_profiles", return_value=mock_cached):
            formatted = agy_quota.format_profile_for_dashboard("mau", res_data)
            self.assertFalse(formatted["hasArgon"])
            self.assertTrue(formatted["argonWeekly"]["unavailable"])
            self.assertEqual(formatted["argonWeekly"]["countdown"], "Unavailable N/A")

    def test_probe_blocked_profile_skips_argon_when_has_argon_false(self):
        """When profile hasArgon is False, probe_blocked_profile must not call Argon."""
        mock_cached = {"mau": {"hasArgon": False, "argonWeekly": {"unavailable": True}}}
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps({"command": {"data": {"groups": []}}})
        mock_proc.stderr = ""

        agy_quota.LAST_BLOCKED_PROBE.clear()
        with (
            patch("os.path.isdir", return_value=True),
            patch("agy_quota.check_profile_auth_token", return_value=True),
            patch("agy_quota.load_cached_profiles", return_value=mock_cached),
            patch("subprocess.run", return_value=mock_proc) as mock_run,
            patch("agy_quota.unblock_profile"),
            patch("agy_quota.fetch_quota_for_profile", return_value={"success": True}),
            patch(
                "agy_quota.format_profile_for_dashboard",
                return_value={"status": "ACTIVE"},
            ),
            patch("agy_quota.update_cached_profile"),
            patch("time.sleep"),
        ):
            res = agy_quota.probe_blocked_profile("mau")
            self.assertTrue(res.get("success"))
            # Check that gemini-4-argon-low was NEVER called
            for call_item in mock_run.call_args_list:
                cmd = call_item[0][0]
                self.assertNotIn("gemini-4-argon-low", cmd)

    def test_build_clean_host_env_strips_ide_and_profile_vars(self):
        """build_clean_host_env strips all leaked IDE/profile variables and restores REAL_HOME."""
        dirty = {
            "HOME": "/Users/danhdueexoictif/antigravity_homes/hau",
            "PATH": "/opt/homebrew/bin:/usr/bin",
            "TERM_PROGRAM": "vscode",
            "TERM_PROGRAM_VERSION": "1.99.0",
            "TERM_SESSION_ID": "abc",
            "TMPDIR": "/tmp/ag_hau",
            "ZDOTDIR": "/tmp/zdot",
            "AGY_PROFILE": "hau",
            "AGY_CLI_MODE": "1",
            "AGY_ENABLE_HUB": "1",
            "VSCODE_PID": "1463",
            "VSCODE_IPC_HOOK": "/tmp/sock",
            "VSCODE_RESOLVING_ENVIRONMENT": "1",
            "ANTIGRAVITY_AGENT": "1",
            "ELECTRON_RUN_AS_NODE": "1",
            "CHROME_DESKTOP": "Antigravity.desktop",
        }
        cleaned = agy_quota.build_clean_host_env(dirty)
        self.assertEqual(cleaned["HOME"], agy_quota.REAL_HOME)
        self.assertEqual(cleaned["PATH"], "/opt/homebrew/bin:/usr/bin")
        for leaked_key in (
            "TERM_PROGRAM",
            "TERM_PROGRAM_VERSION",
            "TERM_SESSION_ID",
            "TMPDIR",
            "ZDOTDIR",
            "AGY_PROFILE",
            "AGY_CLI_MODE",
            "AGY_ENABLE_HUB",
            "VSCODE_PID",
            "VSCODE_IPC_HOOK",
            "VSCODE_RESOLVING_ENVIRONMENT",
            "ANTIGRAVITY_AGENT",
            "ELECTRON_RUN_AS_NODE",
            "CHROME_DESKTOP",
        ):
            self.assertNotIn(leaked_key, cleaned)

    def test_start_server_daemon_uses_clean_host_env(self):
        """start_server_daemon passes sanitized host env to detached server process."""
        dirty_env = {
            "HOME": "/Users/danhdueexoictif/antigravity_homes/danhdue",
            "TERM_PROGRAM": "vscode",
            "VSCODE_PID": "1463",
            "ELECTRON_RUN_AS_NODE": "1",
            "AGY_PROFILE": "danhdue",
            "PATH": "/usr/bin",
        }
        mock_proc = MagicMock()
        mock_proc.pid = 99999
        mock_proc.poll.return_value = None

        with (
            patch.dict("os.environ", dirty_env, clear=True),
            patch("agy_quota.is_server_alive", side_effect=[False, True]),
            patch("agy_quota.get_server_pid", return_value=None),
            patch.object(agy_quota, "PID_FILE", MagicMock()) as mock_pid_file,
        ):
            mock_pid_file.is_file.return_value = False
            with (
                patch("builtins.open", MagicMock()),
                patch("subprocess.Popen", return_value=mock_proc) as mock_popen,
                patch("time.sleep"),
            ):
                agy_quota.start_server_daemon(port=59999, auto_open=False)
                mock_popen.assert_called_once()
                kwargs = mock_popen.call_args.kwargs
                self.assertTrue(kwargs.get("start_new_session"))
                self.assertEqual(kwargs.get("stdin"), agy_quota.subprocess.DEVNULL)
                passed_env = kwargs["env"]
                self.assertEqual(passed_env["HOME"], agy_quota.REAL_HOME)
                self.assertNotIn("TERM_PROGRAM", passed_env)
                self.assertNotIn("VSCODE_PID", passed_env)
                self.assertNotIn("ELECTRON_RUN_AS_NODE", passed_env)
                self.assertNotIn("AGY_PROFILE", passed_env)

    def test_open_ide_endpoint_sanitizes_env_and_validates_profile(self):
        """/api/open-ide must reject bad profile names and launch IDE cleanly."""
        handler = agy_quota.QuotaDashboardHandler.__new__(
            agy_quota.QuotaDashboardHandler
        )
        handler.send_json = MagicMock()

        dirty_env = {
            "HOME": "/Users/danhdueexoictif/antigravity_homes/danhdue",
            "TERM_PROGRAM": "vscode",
            "VSCODE_IPC_HOOK": "/tmp/hook",
            "ELECTRON_RUN_AS_NODE": "1",
            "ANTIGRAVITY_FOO": "bar",
            "AGY_PROFILE": "danhdue",
            "TMPDIR": "/tmp/ag_danhdue",
            "PATH": "/usr/bin",
        }
        with (
            patch.dict("os.environ", dirty_env, clear=True),
            patch("subprocess.Popen") as mock_popen,
        ):
            handler.path = "/api/open-ide?profile=bad;rm"
            handler.do_GET()
            mock_popen.assert_not_called()
            self.assertEqual(handler.send_json.call_args[0][1], 400)

            handler.send_json.reset_mock()
            handler.path = "/api/open-ide?profile=hau"
            handler.do_GET()
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertEqual(args[0][:2], ["zsh", "-ic"])
            self.assertTrue(kwargs.get("start_new_session"))
            self.assertEqual(kwargs.get("stdin"), agy_quota.subprocess.DEVNULL)
            passed_env = kwargs["env"]
            self.assertEqual(passed_env["HOME"], agy_quota.REAL_HOME)
            self.assertNotIn("TERM_PROGRAM", passed_env)
            self.assertNotIn("VSCODE_IPC_HOOK", passed_env)
            self.assertNotIn("ANTIGRAVITY_FOO", passed_env)
            self.assertNotIn("TMPDIR", passed_env)

    def test_is_bucket_activated_distinguishes_unactivated_max_and_frozen(self):
        """Fresh 100% bucket with un-frozen reset_time must NOT count as activated."""
        now_ts = 1_700_000_000.0
        fresh_reset = agy_quota.datetime.datetime.fromtimestamp(
            now_ts + 5 * 3600 - 2, tz=agy_quota.datetime.timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        frozen_reset = agy_quota.datetime.datetime.fromtimestamp(
            now_ts + 4 * 3600 + 50 * 60, tz=agy_quota.datetime.timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        unactivated = {"fraction": 1.0, "resetTime": fresh_reset, "description": ""}
        self.assertFalse(
            agy_quota.is_bucket_activated(unactivated, 5 * 3600, now_ts=now_ts)
        )

        frozen = {"fraction": 1.0, "resetTime": frozen_reset, "description": ""}
        self.assertTrue(agy_quota.is_bucket_activated(frozen, 5 * 3600, now_ts=now_ts))

        desc_used = {
            "fraction": 1.0,
            "resetTime": fresh_reset,
            "description": "You have used some of your Gemini Pro 5h limit.",
        }
        self.assertTrue(
            agy_quota.is_bucket_activated(desc_used, 5 * 3600, now_ts=now_ts)
        )

    def test_execute_ping_profile_pings_all_three_independent_buckets(self):
        """Unactivated Gemini 5H, Argon 7D, and Claude 5H all get pinged with explicit --model."""
        now_utc = agy_quota.datetime.datetime.now(agy_quota.datetime.timezone.utc)
        fresh_5h = (now_utc + agy_quota.datetime.timedelta(hours=5)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        fresh_7d = (now_utc + agy_quota.datetime.timedelta(days=7)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        live_quota = {
            "success": True,
            "tier": "PRO",
            "groups": [
                {
                    "name": "Gemini Models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 1.0,
                            "reset_time": fresh_5h,
                        }
                    ],
                },
                {
                    "name": "Claude and GPT models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 1.0,
                            "reset_time": fresh_5h,
                        }
                    ],
                },
                {
                    "name": "Argon",
                    "buckets": [
                        {
                            "window": "weekly",
                            "remaining_fraction": 1.0,
                            "reset_time": fresh_7d,
                        }
                    ],
                },
            ],
        }
        models_proc = MagicMock(
            returncode=0,
            stdout=(
                "gemini-3.8-flash-low\tGemini 3.8 Flash (Low)\n"
                "claude-sonnet-5-5-low\tClaude Sonnet 5.5 (Low)\n"
                "gemini-4-argon-low\tGemini 4 Argon (Low)\n"
            ),
            stderr="",
        )
        ping_ok = MagicMock(returncode=0, stdout="OK", stderr="")

        def fake_run(cmd, **kwargs):
            if len(cmd) >= 2 and cmd[1] == "models":
                return models_proc
            return ping_ok

        with (
            patch("agy_quota.REAL_HOME", "/tmp/mock_ag_real_home"),
            patch("os.path.isdir", return_value=True),
            patch("os.makedirs"),
            patch("agy_quota.load_cached_profiles", return_value={}),
            patch("agy_quota.update_cached_profile"),
            patch("agy_quota.check_profile_appeal_status", return_value=None),
            patch("agy_quota.check_profile_auth_token", return_value=True),
            patch("agy_quota.fetch_quota_for_profile", return_value=live_quota),
            patch("agy_quota.get_session_record", return_value=None),
            patch("agy_quota.save_session_record"),
            patch("subprocess.run", side_effect=fake_run) as mock_run,
            patch("time.sleep"),
        ):
            res = agy_quota.execute_ping_profile("brother")
            self.assertTrue(res.get("success"))
            self.assertTrue(res.get("pinged_gemini"))
            self.assertTrue(res.get("pinged_claude"))
            self.assertTrue(res.get("pinged_argon"))
            ping_cmds = [
                c.args[0]
                for c in mock_run.call_args_list
                if len(c.args[0]) > 2
                and c.args[0][0] == agy_quota.AGY_BIN
                and "-p" in c.args[0]
            ]
            self.assertEqual(len(ping_cmds), 3)
            for cmd in ping_cmds:
                self.assertIn("--model", cmd)
                self.assertIn("--disable-slash-commands", cmd)
            # Isolated sandbox cwd must be passed (never repo root)
            for c in mock_run.call_args_list:
                if (
                    len(c.args[0]) > 2
                    and c.args[0][0] == agy_quota.AGY_BIN
                    and "-p" in c.args[0]
                ):
                    self.assertIsNotNone(c.kwargs.get("cwd"))
                    self.assertGreaterEqual(c.kwargs.get("timeout", 0), 45)

    def test_execute_ping_profile_standard_pro_uses_claude_4_6_and_skips_active_gemini(
        self,
    ):
        """When Gemini 5H is active and profile lacks 5.5, Claude 5H uses claude-sonnet-4-6."""
        now_utc = agy_quota.datetime.datetime.now(agy_quota.datetime.timezone.utc)
        active_3h = (now_utc + agy_quota.datetime.timedelta(hours=3)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        fresh_5h = (now_utc + agy_quota.datetime.timedelta(hours=5)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        live_quota = {
            "success": True,
            "tier": "PRO",
            "groups": [
                {
                    "name": "Gemini Models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 0.85,
                            "reset_time": active_3h,
                            "description": "You have used some of your Gemini limit.",
                        }
                    ],
                },
                {
                    "name": "Claude and GPT models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 1.0,
                            "reset_time": fresh_5h,
                        }
                    ],
                },
            ],
        }
        models_proc = MagicMock(
            returncode=0,
            stdout=(
                "gemini-3.8-flash-low\tGemini 3.8 Flash (Low)\n"
                "claude-sonnet-4-6\tClaude Sonnet 4.6\n"
            ),
            stderr="",
        )
        ping_ok = MagicMock(returncode=0, stdout="OK", stderr="")

        def fake_run(cmd, **kwargs):
            if len(cmd) >= 2 and cmd[1] == "models":
                return models_proc
            return ping_ok

        with (
            patch("agy_quota.REAL_HOME", "/tmp/mock_ag_real_home"),
            patch("os.path.isdir", return_value=True),
            patch("os.makedirs"),
            patch("agy_quota.load_cached_profiles", return_value={}),
            patch("agy_quota.update_cached_profile"),
            patch("agy_quota.check_profile_appeal_status", return_value=None),
            patch("agy_quota.check_profile_auth_token", return_value=True),
            patch("agy_quota.fetch_quota_for_profile", return_value=live_quota),
            # Legacy stale session record claiming active 5h globally must NOT suppress Claude
            patch(
                "agy_quota.get_session_record",
                return_value={"is_active": True, "reset_5h": 9999999999},
            ),
            patch("agy_quota.save_session_record"),
            patch("subprocess.run", side_effect=fake_run) as mock_run,
            patch("time.sleep"),
        ):
            res = agy_quota.execute_ping_profile("d3molt")
            self.assertTrue(res.get("success"))
            self.assertFalse(res.get("pinged_gemini"))
            self.assertTrue(res.get("pinged_claude"))
            self.assertFalse(res.get("pinged_argon"))
            ping_cmds = [
                c.args[0]
                for c in mock_run.call_args_list
                if len(c.args[0]) > 2
                and c.args[0][0] == agy_quota.AGY_BIN
                and "-p" in c.args[0]
            ]
            self.assertEqual(len(ping_cmds), 1)
            self.assertIn("claude-sonnet-4-6", ping_cmds[0])

    def test_execute_ping_profile_rejects_free_and_reports_partial_failures(self):
        """FREE accounts fail/skip cleanly without pinging; partial failures surface error."""
        free_quota = {
            "success": True,
            "tier": "FREE",
            "groups": [
                {
                    "name": "Gemini Models",
                    "buckets": [{"window": "weekly", "remaining_fraction": 1.0}],
                }
            ],
        }
        with (
            patch("agy_quota.REAL_HOME", "/tmp/mock_ag_real_home"),
            patch("os.path.isdir", return_value=True),
            patch("agy_quota.load_cached_profiles", return_value={}),
            patch("agy_quota.check_profile_appeal_status", return_value=None),
            patch("agy_quota.check_profile_auth_token", return_value=True),
            patch("agy_quota.fetch_quota_for_profile", return_value=free_quota),
            patch("subprocess.run") as mock_run,
        ):
            res = agy_quota.execute_ping_profile("buivantrong8901")
            self.assertFalse(res.get("success"))
            self.assertIn("FREE", res.get("error", ""))
            mock_run.assert_not_called()

    def test_execute_ping_profile_reports_partial_argon_failure_and_api_ping_error(
        self,
    ):
        """Partial failure (e.g. Argon times out) must return success=False and surface error via /api/ping."""
        now_utc = agy_quota.datetime.datetime.now(agy_quota.datetime.timezone.utc)
        fresh_5h = (now_utc + agy_quota.datetime.timedelta(hours=5)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        fresh_7d = (now_utc + agy_quota.datetime.timedelta(days=7)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        live_quota = {
            "success": True,
            "tier": "PRO",
            "groups": [
                {
                    "name": "Gemini Models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 1.0,
                            "reset_time": fresh_5h,
                        }
                    ],
                },
                {
                    "name": "Claude and GPT models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 1.0,
                            "reset_time": fresh_5h,
                        }
                    ],
                },
                {
                    "name": "Argon",
                    "buckets": [
                        {
                            "window": "weekly",
                            "remaining_fraction": 1.0,
                            "reset_time": fresh_7d,
                        }
                    ],
                },
            ],
        }
        models_proc = MagicMock(
            returncode=0,
            stdout="gemini-3.8-flash-low\tGemini\nclaude-sonnet-5-5-low\tClaude\ngemini-4-argon-low\tArgon\n",
            stderr="",
        )

        def fake_run(cmd, **kwargs):
            if cmd[1:2] == ["models"]:
                return models_proc
            if "gemini-4-argon-low" in cmd:
                raise agy_quota.subprocess.TimeoutExpired(cmd=cmd, timeout=50)
            return MagicMock(returncode=0, stdout="OK", stderr="")

        with (
            patch("agy_quota.REAL_HOME", "/tmp/mock_ag_real_home"),
            patch("os.path.isdir", return_value=True),
            patch("os.makedirs"),
            patch("agy_quota.load_cached_profiles", return_value={}),
            patch("agy_quota.update_cached_profile"),
            patch("agy_quota.check_profile_appeal_status", return_value=None),
            patch("agy_quota.check_profile_auth_token", return_value=True),
            patch("agy_quota.fetch_quota_for_profile", return_value=live_quota),
            patch("agy_quota.get_session_record", return_value=None),
            patch("agy_quota.save_session_record"),
            patch("subprocess.run", side_effect=fake_run),
            patch("time.sleep"),
        ):
            res = agy_quota.execute_ping_profile("brother")
            self.assertFalse(res.get("success"))
            self.assertIn("Argon", res.get("error", ""))

        # Verify /api/ping exposes error cleanly
        handler = agy_quota.QuotaDashboardHandler.__new__(
            agy_quota.QuotaDashboardHandler
        )
        handler.send_json = MagicMock()
        with (
            patch(
                "agy_quota.execute_ping_profile",
                return_value={
                    "success": False,
                    "error": "Argon 7D Timeout",
                    "duration_ms": 100,
                },
            ),
            patch("agy_quota.fetch_quota_for_profile", return_value=live_quota),
            patch(
                "agy_quota.format_profile_for_dashboard",
                return_value={"status": "ACTIVE"},
            ),
            patch("agy_quota.update_cached_profile"),
        ):
            handler.path = "/api/ping?profile=brother"
            handler.command = "GET"
            handler.do_GET()
            resp = handler.send_json.call_args[0][0]
            self.assertFalse(resp["success"])
            self.assertEqual(resp["error"], "Argon 7D Timeout")

    def test_api_schedule_endpoints_and_free_tier_rejection(self):
        """/api/schedule supports multi-schedule CRUD and rejects FREE tier and bad hours."""
        handler = agy_quota.QuotaDashboardHandler.__new__(
            agy_quota.QuotaDashboardHandler
        )
        handler.send_json = MagicMock()
        handler.headers = {}
        handler.rfile = io.BytesIO(b"")

        fake_status = {
            "success": True,
            "platform": "darwin",
            "schedules": [
                {
                    "label": "com.d3nexus.refresh-session.0700-d30",
                    "time": "07:00",
                    "hour": 7,
                    "minute": 0,
                    "delay": 30,
                    "target": "brother",
                    "targets": ["brother"],
                    "loaded": True,
                }
            ],
            "by_profile": {
                "brother": [
                    {
                        "label": "com.d3nexus.refresh-session.0700-d30",
                        "time": "07:00",
                        "hour": 7,
                        "minute": 0,
                        "delay": 30,
                        "loaded": True,
                    }
                ]
            },
        }
        mock_mod = MagicMock()
        mock_mod.get_schedule_status.return_value = fake_status
        mock_mod.install_schedule.return_value = {"success": True}
        mock_mod.uninstall_schedule.return_value = {"success": True}
        mock_mod.parse_flexible_time.side_effect = lambda s: (
            (int(s.split(":")[0]), int(s.split(":")[1]))
            if ":" in s
            and 0 <= int(s.split(":")[0]) <= 23
            and 0 <= int(s.split(":")[1]) <= 59
            else (_ for _ in ()).throw(ValueError("bad time"))
        )

        cached = {
            "brother": {"tier": "PRO"},
            "buivantrong8901": {"tier": "FREE"},
        }

        with (
            patch("agy_quota._load_refresh_session_module", return_value=mock_mod),
            patch("agy_quota.load_cached_profiles", return_value=cached),
        ):
            handler.path = "/api/schedule"
            handler.command = "GET"
            handler.do_GET()
            handler.send_json.assert_called_once()
            self.assertEqual(
                handler.send_json.call_args[0][0]["schedules"], fake_status["schedules"]
            )

            # Reject FREE tier
            handler.send_json.reset_mock()
            payload = json.dumps(
                {
                    "action": "set",
                    "profiles": ["buivantrong8901"],
                    "time": "07:00",
                    "delay": 30,
                }
            ).encode()
            handler.headers = {"Content-Length": str(len(payload))}
            handler.rfile = io.BytesIO(payload)
            handler.command = "POST"
            handler.do_POST()
            self.assertEqual(
                handler.send_json.call_args[1].get("status")
                or handler.send_json.call_args[0][1],
                400,
            )
            self.assertFalse(handler.send_json.call_args[0][0]["success"])

            # Valid multi-schedule upsert
            handler.send_json.reset_mock()
            payload2 = json.dumps(
                {"action": "set", "profiles": ["brother"], "time": "07:00", "delay": 30}
            ).encode()
            handler.headers = {"Content-Length": str(len(payload2))}
            handler.rfile = io.BytesIO(payload2)
            handler.do_POST()
            mock_mod.install_schedule.assert_called_once()
            self.assertTrue(handler.send_json.call_args[0][0]["success"])

    def test_argon_ping_not_blocked_when_reset_time_expired(self):
        """Expired Argon reset_time (<= 0s remaining, fraction=1.0) must not be misclassified as < 7h near-reset."""
        now_utc = agy_quota.datetime.datetime.now(agy_quota.datetime.timezone.utc)
        expired_reset = (now_utc - agy_quota.datetime.timedelta(minutes=2)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        active_3h = (now_utc + agy_quota.datetime.timedelta(hours=3)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        live_quota = {
            "success": True,
            "tier": "PRO",
            "groups": [
                {
                    "name": "Gemini Models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 0.85,
                            "reset_time": active_3h,
                        }
                    ],
                },
                {
                    "name": "Claude and GPT models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 0.90,
                            "reset_time": active_3h,
                        }
                    ],
                },
                {
                    "name": "Argon",
                    "buckets": [
                        {
                            "window": "weekly",
                            "remaining_fraction": 1.0,
                            "reset_time": expired_reset,
                        }
                    ],
                },
            ],
        }
        mock_proc = MagicMock(returncode=0, stdout="gemini-4-argon-low\n", stderr="")
        with (
            patch("os.path.isdir", return_value=True),
            patch("os.makedirs"),
            patch("agy_quota.wait_for_launch_lock"),
            patch("agy_quota.check_profile_appeal_status", return_value=None),
            patch("agy_quota.check_profile_auth_token", return_value=True),
            patch("agy_quota.load_cached_profiles", return_value={}),
            patch("agy_quota.fetch_quota_for_profile", return_value=live_quota),
            patch("agy_quota.update_cached_profile"),
            patch("subprocess.run", return_value=mock_proc) as mock_run,
        ):
            res = agy_quota.execute_ping_profile("test_prof")
            self.assertTrue(res.get("success"))
            self.assertFalse(res.get("skipped"))
            self.assertTrue(res.get("pinged_argon"))
            self.assertTrue(
                any(
                    "gemini-4-argon-low" in c.args[0]
                    for c in mock_run.call_args_list
                    if isinstance(c.args[0], list)
                )
            )

    def test_claude_5h_active_when_reset_in_future_even_at_zero_percent_util(self):
        """Claude 5H must be marked active when resets_at is in future even if utilization rounds to 0."""
        now_utc = agy_quota.datetime.datetime.now(agy_quota.datetime.timezone.utc)
        active_4h = (now_utc + agy_quota.datetime.timedelta(hours=4)).isoformat()
        idle_payload = {
            "five_hour": {"utilization": 0.0, "resets_at": None},
            "seven_day": {"utilization": 66.0, "resets_at": active_4h},
            "limits": [{"kind": "session", "is_active": False, "resets_at": None}],
        }
        active_zero_util_payload = {
            "five_hour": {"utilization": 0.0, "resets_at": active_4h},
            "seven_day": {"utilization": 66.0, "resets_at": active_4h},
            "limits": [{"kind": "session", "is_active": True, "resets_at": active_4h}],
        }

        def make_resp(payload):
            m = MagicMock()
            m.status = 200
            m.read.return_value = json.dumps(payload).encode("utf-8")
            m.__enter__.return_value = m
            return m

        with (
            patch(
                "agy_quota.get_claude_oauth_token",
                return_value=("tok", "user@anthropic.com", True),
            ),
            patch("agy_quota.update_claude_json_cache"),
            patch("agy_quota.save_session_record"),
            patch(
                "urllib.request.urlopen",
                side_effect=[
                    make_resp(idle_payload),
                    make_resp(active_zero_util_payload),
                ],
            ),
        ):
            idle_q = agy_quota.fetch_claude_quota()
            self.assertFalse(idle_q["isSessionActive"])

            active_q = agy_quota.fetch_claude_quota()
            self.assertTrue(active_q["isSessionActive"])

    def test_codex_5h_active_when_clock_ticking_even_at_zero_percent_used(self):
        """Codex 5H must skip when reset_after_seconds < limit_window_seconds - 30 even at 0% used."""
        idle_payload = {
            "rate_limit": {
                "allowed": True,
                "primary_window": {
                    "used_percent": 0,
                    "limit_window_seconds": 18000,
                    "reset_after_seconds": 18000,
                    "reset_at": int(agy_quota.time.time()) + 18000,
                },
                "secondary_window": {
                    "used_percent": 84,
                    "limit_window_seconds": 604800,
                    "reset_after_seconds": 280000,
                    "reset_at": int(agy_quota.time.time()) + 280000,
                },
            }
        }
        ticking_payload = {
            "rate_limit": {
                "allowed": True,
                "primary_window": {
                    "used_percent": 0,
                    "limit_window_seconds": 18000,
                    "reset_after_seconds": 17500,
                    "reset_at": int(agy_quota.time.time()) + 17500,
                },
                "secondary_window": idle_payload["rate_limit"]["secondary_window"],
            }
        }

        def make_resp(payload):
            m = MagicMock()
            m.read.return_value = json.dumps(payload).encode("utf-8")
            m.__enter__.return_value = m
            return m

        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            auth_dir = agy_quota.Path(tmpdir) / ".codex"
            auth_dir.mkdir(parents=True)
            (auth_dir / "auth.json").write_text(
                json.dumps({"tokens": {"access_token": "tok", "account_id": "acc"}}),
                encoding="utf-8",
            )
            with (
                patch.object(agy_quota, "REAL_HOME", tmpdir),
                patch("agy_quota.save_session_record"),
                patch(
                    "urllib.request.urlopen",
                    side_effect=[make_resp(idle_payload), make_resp(ticking_payload)],
                ),
            ):
                idle_q = agy_quota.fetch_codex_quota()
                self.assertFalse(idle_q["isSessionActive"])

                ticking_q = agy_quota.fetch_codex_quota()
                self.assertTrue(ticking_q["isSessionActive"])

    def test_execute_ping_profile_preserves_target_home_and_path(self):
        """execute_ping_profile must isolate target profile HOME/AGY_PROFILE and preserve PATH."""
        now_utc = agy_quota.datetime.datetime.now(agy_quota.datetime.timezone.utc)
        fresh_5h = (now_utc + agy_quota.datetime.timedelta(hours=5)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        live_quota = {
            "success": True,
            "tier": "PRO",
            "groups": [
                {
                    "name": "Gemini Models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 1.0,
                            "reset_time": fresh_5h,
                        }
                    ],
                },
                {
                    "name": "Claude and GPT models",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 1.0,
                            "reset_time": fresh_5h,
                        }
                    ],
                },
            ],
        }
        dirty_env = {
            "PATH": "/opt/homebrew/bin:/usr/bin",
            "HOME": "/Users/danhdueexoictif",
            "VSCODE_PID": "999",
            "ANTIGRAVITY_AGENT": "1",
            "AGY_PROFILE": "phungthuy8901",
            "ELECTRON_RUN_AS_NODE": "1",
        }
        captured_envs = []

        def fake_run(cmd, **kwargs):
            if cmd[0] == agy_quota.AGY_BIN:
                captured_envs.append((list(cmd), dict(kwargs.get("env") or {})))
            if cmd[1:2] == ["models"]:
                return MagicMock(
                    returncode=0,
                    stdout="gemini-3.8-flash-low\nclaude-sonnet-5-5-low\n",
                    stderr="",
                )
            return MagicMock(returncode=0, stdout="OK", stderr="")

        with (
            patch.dict("os.environ", dirty_env, clear=True),
            patch("os.path.isdir", return_value=True),
            patch("os.makedirs"),
            patch("agy_quota.wait_for_launch_lock"),
            patch("agy_quota.check_profile_appeal_status", return_value=None),
            patch("agy_quota.check_profile_auth_token", return_value=True),
            patch("agy_quota.load_cached_profiles", return_value={}),
            patch("agy_quota.fetch_quota_for_profile", return_value=live_quota),
            patch("agy_quota.update_cached_profile"),
            patch("subprocess.run", side_effect=fake_run),
            patch("time.sleep"),
        ):
            res = agy_quota.execute_ping_profile("hau")
            self.assertTrue(res.get("success"))
            self.assertTrue(res.get("pinged_claude"))
            self.assertTrue(captured_envs)
            expected_home = f"{agy_quota.REAL_HOME}/antigravity_homes/hau"
            for _, env in captured_envs:
                self.assertEqual(env.get("HOME"), expected_home)
                self.assertEqual(env.get("AGY_PROFILE"), "hau")
                self.assertEqual(env.get("AGY_CLI_MODE"), "1")
                self.assertEqual(env.get("PATH"), "/opt/homebrew/bin:/usr/bin")
                self.assertNotIn("VSCODE_PID", env)
                self.assertNotIn("ANTIGRAVITY_AGENT", env)
                self.assertNotIn("ELECTRON_RUN_AS_NODE", env)

    def test_api_ping_returns_formatted_post_quota_directly(self):
        """/api/ping uses formatted post_quota directly instead of falling back to stale cache."""
        handler = agy_quota.QuotaDashboardHandler.__new__(
            agy_quota.QuotaDashboardHandler
        )
        handler.send_json = MagicMock()
        fresh_formatted = {
            "profile": "hau",
            "success": True,
            "status": "ACTIVE",
            "claude5h": {
                "name": "Claude 5.5 / GPT 5H",
                "fraction": 0.96,
                "countdown": "⏱ 4h 59m (03:09:32)",
            },
        }
        stale_cache = {
            "hau": {
                "profile": "hau",
                "success": True,
                "status": "ACTIVE",
                "claude5h": {
                    "name": "Claude 5.5 / GPT 5H",
                    "fraction": 1.0,
                    "countdown": "⏱ 4h 59m (stale)",
                },
            }
        }
        with (
            patch(
                "agy_quota.execute_ping_profile",
                return_value={
                    "profile": "hau",
                    "success": True,
                    "duration_ms": 120,
                    "message": "ok",
                    "post_quota": fresh_formatted,
                },
            ),
            patch("agy_quota.load_cached_profiles", return_value=stale_cache),
            patch("agy_quota.update_cached_profile") as mock_update,
        ):
            handler.path = "/api/ping?profile=hau"
            handler.command = "GET"
            handler.do_GET()
            resp = handler.send_json.call_args[0][0]
            self.assertTrue(resp["success"])
            self.assertEqual(resp["data"]["claude5h"]["fraction"], 0.96)
            mock_update.assert_called_once_with("hau", fresh_formatted)


if __name__ == "__main__":
    unittest.main()
