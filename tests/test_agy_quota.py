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
        far_reset = (now_utc + agy_quota.datetime.timedelta(days=2)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        mock_cached = {
            "test_prof": {
                "hasArgon": True,
                "argonWeekly": {
                    "fraction": 0.45,
                    "resetTime": far_reset,
                    "unavailable": False,
                },
            }
        }
        with (
            patch("os.path.isdir", return_value=True),
            patch("agy_quota.check_profile_appeal_status", return_value=None),
            patch("agy_quota.check_profile_auth_token", return_value=True),
            patch("agy_quota.load_cached_profiles", return_value=mock_cached),
            patch(
                "agy_quota.get_session_record",
                return_value={"is_active": True, "reset_5h": 9999999999},
            ),
        ):
            res = agy_quota.execute_ping_profile("test_prof")
            self.assertTrue(res.get("skipped"))
            self.assertIn("Argon đã kích hoạt", res.get("message", ""))

    def test_argon_ping_skipped_when_near_reset(self):
        """Argon must NOT be pinged when reset time is less than 7 hours away."""
        now_utc = agy_quota.datetime.datetime.now(agy_quota.datetime.timezone.utc)
        soon_reset = (now_utc + agy_quota.datetime.timedelta(hours=3)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        mock_cached = {
            "test_prof": {
                "hasArgon": True,
                "argonWeekly": {
                    "fraction": 0.20,
                    "resetTime": soon_reset,
                    "unavailable": False,
                },
            }
        }
        with (
            patch("os.path.isdir", return_value=True),
            patch("agy_quota.check_profile_appeal_status", return_value=None),
            patch("agy_quota.check_profile_auth_token", return_value=True),
            patch("agy_quota.load_cached_profiles", return_value=mock_cached),
            patch(
                "agy_quota.get_session_record",
                return_value={"is_active": True, "reset_5h": 9999999999},
            ),
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


if __name__ == "__main__":
    unittest.main()
