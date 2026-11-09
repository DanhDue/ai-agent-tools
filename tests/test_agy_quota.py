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
        with patch.object(agy_quota, "PID_FILE", mock_file):
            with patch("subprocess.check_output", return_value=""):
                self.assertIsNone(agy_quota.get_server_pid(port=59998))

    def test_get_server_pid_reads_valid_pid(self):
        """get_server_pid parses PID file integer when process is alive."""
        mock_file = MagicMock()
        mock_file.is_file.return_value = True
        mock_file.read_text.return_value = "12345"
        with patch.object(agy_quota, "PID_FILE", mock_file):
            with patch("os.kill", return_value=None):
                self.assertEqual(agy_quota.get_server_pid(port=59998), 12345)

    def test_stop_server_when_not_running(self):
        """stop_server gracefully returns False when server is not running."""
        with patch("agy_quota.get_server_pid", return_value=None):
            with patch("agy_quota.is_server_alive", return_value=False):
                res = agy_quota.stop_server(port=59998)
                self.assertFalse(res)

    def test_cli_help_includes_daemon_options(self):
        """Help screen displays --ui, --stop, and --status options."""
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            with patch("sys.argv", ["agy_quota.py", "--help"]):
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
            agy_quota.QuotaDashboardHandler.log_message(mock_handler, "%s", "GET /api/status", "200")

    def test_argon_ping_skipped_when_already_activated(self):
        """Argon must NOT be pinged when it is already activated and counting down."""
        mock_cached = {
            "test_prof": {
                "hasArgon": True,
                "argonWeekly": {
                    "fraction": 0.45,
                    "resetTime": "2026-11-14T05:00:00Z",
                    "unavailable": False,
                }
            }
        }
        with patch("os.path.isdir", return_value=True):
            with patch("agy_quota.check_profile_appeal_status", return_value=None):
                with patch("agy_quota.check_profile_auth_token", return_value=True):
                    with patch("agy_quota.load_cached_profiles", return_value=mock_cached):
                        with patch("agy_quota.get_session_record", return_value={"is_active": True, "reset_5h": 9999999999}):
                            res = agy_quota.execute_ping_profile("test_prof")
                            self.assertTrue(res.get("skipped"))
                            self.assertIn("Argon đã kích hoạt", res.get("message", ""))

    def test_argon_ping_skipped_when_near_reset(self):
        """Argon must NOT be pinged when reset time is less than 7 hours away."""
        now_utc = agy_quota.datetime.datetime.now(agy_quota.datetime.timezone.utc)
        soon_reset = (now_utc + agy_quota.datetime.timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
        mock_cached = {
            "test_prof": {
                "hasArgon": True,
                "argonWeekly": {
                    "fraction": 0.20,
                    "resetTime": soon_reset,
                    "unavailable": False,
                }
            }
        }
        with patch("os.path.isdir", return_value=True):
            with patch("agy_quota.check_profile_appeal_status", return_value=None):
                with patch("agy_quota.check_profile_auth_token", return_value=True):
                    with patch("agy_quota.load_cached_profiles", return_value=mock_cached):
                        with patch("agy_quota.get_session_record", return_value={"is_active": True, "reset_5h": 9999999999}):
                            res = agy_quota.execute_ping_profile("test_prof")
                            self.assertTrue(res.get("skipped"))
                            self.assertIn("Argon < 7h", res.get("message", ""))


    def test_argon_ping_triggered_when_max_7d(self):
        """Argon MUST be pinged with jitter when it is at max 7D."""
        now_utc = agy_quota.datetime.datetime.now(agy_quota.datetime.timezone.utc)
        max_7d_reset = (now_utc + agy_quota.datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        mock_cached = {
            "test_prof": {
                "hasArgon": True,
                "argonWeekly": {
                    "fraction": 1.0,
                    "resetTime": max_7d_reset,
                    "unavailable": False,
                }
            }
        }
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "OK"
        mock_res.stderr = ""

        with patch("os.path.isdir", return_value=True):
            with patch("agy_quota.check_profile_appeal_status", return_value=None):
                with patch("agy_quota.check_profile_auth_token", return_value=True):
                    with patch("agy_quota.load_cached_profiles", return_value=mock_cached):
                        with patch("agy_quota.get_session_record", return_value=None):
                            with patch("subprocess.run", return_value=mock_res) as mock_run:
                                with patch("agy_quota.fetch_quota_for_profile", return_value={"success": True}):
                                    with patch("agy_quota.format_profile_for_dashboard", return_value={}):
                                        with patch("agy_quota.update_cached_profile"):
                                            with patch("time.sleep") as mock_sleep:
                                                res = agy_quota.execute_ping_profile("test_prof")
                                                self.assertTrue(res.get("success"))
                                                self.assertTrue(res.get("pinged_argon"))
                                                self.assertTrue(res.get("pinged_gemini"))
                                                self.assertIn("Argon 7D", res.get("message", ""))
                                                # Jitter sleep was called
                                                mock_sleep.assert_called_once()
                                                sleep_val = mock_sleep.call_args[0][0]
                                                self.assertGreaterEqual(sleep_val, 1.8)
                                                self.assertLessEqual(sleep_val, 3.5)
                                                # Subprocess called with gemini-4-argon-low
                                                argon_calls = [
                                                    c for c in mock_run.call_args_list
                                                    if "gemini-4-argon-low" in c[0][0]
                                                ]
                                                self.assertEqual(len(argon_calls), 1)

    def test_probe_blocked_profile_unblocked_success(self):
        """When probe returns 0 and valid quota, account is unblocked with jitter."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps({"command": {"data": {"groups": []}}})
        mock_proc.stderr = ''

        agy_quota.LAST_BLOCKED_PROBE.clear()
        with patch("os.path.isdir", return_value=True):
            with patch("agy_quota.check_profile_auth_token", return_value=True):
                with patch("subprocess.run", return_value=mock_proc):
                    with patch("agy_quota.unblock_profile") as mock_unblock:
                        with patch("agy_quota.format_profile_for_dashboard", return_value={"status": "ACTIVE"}):
                            with patch("agy_quota.update_cached_profile"):
                                with patch("time.sleep") as mock_sleep:
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
        mock_proc.stdout = ''
        mock_proc.stderr = 'This service has been disabled. Please submit an appeal (err: 12345678-1234-1234-1234-123456789abc).'

        agy_quota.LAST_BLOCKED_PROBE.clear()
        with patch("os.path.isdir", return_value=True):
            with patch("agy_quota.check_profile_auth_token", return_value=True):
                with patch("subprocess.run", return_value=mock_proc):
                    with patch("agy_quota.record_profile_disabled") as mock_record:
                        with patch("time.sleep"):
                            res = agy_quota.probe_blocked_profile("test_still_blocked")
                            self.assertFalse(res.get("success"))
                            self.assertEqual(res.get("status"), "DISABLED")
                            self.assertTrue(res.get("is_appeal"))
                            mock_record.assert_called_once()


if __name__ == "__main__":
    unittest.main()

