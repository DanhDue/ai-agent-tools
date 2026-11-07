"""Unit tests for Kiro Quota Provider integration."""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import agy_quota  # noqa: E402


class TestKiroQuotaProvider(unittest.TestCase):
    """Test suite verifying Kiro CLI quota extraction, parsing, and resilience."""

    def test_kiro_whoami_parsing_logged_in(self):
        """Extract email and login status from kiro-cli whoami output."""
        output = "Logged in with Builder ID\nEmail: Elenor.Zulaufell001@mymdc.net\n"
        email = agy_quota.parse_kiro_whoami_email(output)
        self.assertEqual(email, "Elenor.Zulaufell001@mymdc.net")

    def test_kiro_whoami_parsing_not_logged_in(self):
        """Return None when kiro-cli whoami indicates unauthenticated session."""
        output = "Not logged in. Run 'kiro-cli login' to authenticate.\n"
        email = agy_quota.parse_kiro_whoami_email(output)
        self.assertIsNone(email)

    def test_kiro_api_response_parsing(self):
        """Parse AWS CodeWhisperer GetUsageLimits response accurately into credits."""
        api_data = {
            "daysUntilReset": 0,
            "nextDateReset": 1796083200.0,
            "overageConfiguration": {
                "overageStatus": "DISABLED"
            },
            "subscriptionInfo": {
                "subscriptionTitle": "KIRO STUDENT",
                "type": "Q_DEVELOPER_STANDALONE_STUDENT"
            },
            "usageBreakdownList": [
                {
                    "currentUsageWithPrecision": 7.22,
                    "usageLimitWithPrecision": 1000.0,
                    "resourceType": "CREDIT"
                }
            ]
        }
        res = agy_quota.parse_kiro_usage_limits(api_data, email="Elenor.Zulaufell001@mymdc.net")
        self.assertEqual(res["profile"], "kiro")
        self.assertEqual(res["tier"], "KIRO STUDENT")
        self.assertEqual(res["email"], "Elenor.Zulaufell001@mymdc.net")
        self.assertEqual(res["status"], "ACTIVE")
        self.assertTrue(res["isCreditOnly"])
        self.assertAlmostEqual(res["creditsPool"]["used"], 7.22)
        self.assertAlmostEqual(res["creditsPool"]["limit"], 1000.0)
        self.assertAlmostEqual(res["creditsPool"]["remaining"], 992.78)
        self.assertAlmostEqual(res["creditsPool"]["fraction"], 0.9928, places=4)
        self.assertIn("01/12", res["creditsPool"]["countdown"])

    def test_kiro_color_thresholds(self):
        """Verify green at >= 50%, amber at 10-49%, red at < 10%."""
        self.assertEqual(agy_quota.get_color(75.0), agy_quota.GREEN)
        self.assertEqual(agy_quota.get_color(50.0), agy_quota.GREEN)
        self.assertEqual(agy_quota.get_color(49.9), agy_quota.AMBER)
        self.assertEqual(agy_quota.get_color(10.0), agy_quota.AMBER)
        self.assertEqual(agy_quota.get_color(9.9), agy_quota.RED)
        self.assertEqual(agy_quota.get_color(0.0), agy_quota.RED)

    @patch("agy_quota.shutil.which")
    def test_fetch_kiro_quota_when_cli_missing(self, mock_which):
        """Return unavailable status when kiro-cli binary is not found."""
        mock_which.return_value = None
        with patch("os.path.isfile", return_value=False):
            res = agy_quota.fetch_kiro_quota()
            self.assertEqual(res["status"], "UNAVAILABLE")
            self.assertFalse(res["success"])

    @patch("agy_quota.get_kiro_bin_path")
    @patch("agy_quota.subprocess.run")
    def test_fetch_kiro_quota_when_not_logged_in(self, mock_run, mock_get_bin):
        """Return NOT LOGGED IN when whoami returns unauthenticated."""
        mock_get_bin.return_value = "/usr/local/bin/kiro-cli"
        whoami_res = MagicMock()
        whoami_res.returncode = 1
        whoami_res.stdout = "Not logged in"
        whoami_res.stderr = ""
        mock_run.return_value = whoami_res

        res = agy_quota.fetch_kiro_quota()
        self.assertEqual(res["status"], "NOT LOGGED IN")
        self.assertEqual(res["tier"], "KIRO")
        self.assertEqual(res["gemini5h"]["fraction"], 0.0)

    @patch("agy_quota.get_kiro_bin_path")
    @patch("agy_quota.subprocess.run")
    @patch("urllib.request.urlopen")
    def test_fetch_kiro_quota_success(self, mock_urlopen, mock_run, mock_get_bin):
        """Mock successful end-to-end token acquisition and AWS API response."""
        mock_get_bin.return_value = "/Users/danhdueexoictif/.local/bin/kiro-cli"

        # Mock whoami
        whoami_proc = MagicMock()
        whoami_proc.returncode = 0
        whoami_proc.stdout = "Logged in with Builder ID\nEmail: test@example.com\n"

        # Mock get-kas-token
        kas_proc = MagicMock()
        kas_proc.returncode = 0
        kas_proc.stdout = json.dumps({
            "kind": "getKasToken",
            "data": {
                "accessToken": "mock-token",
                "profileArn": "arn:aws:codewhisperer:us-east-1:12345:profile/TEST"
            }
        })

        mock_run.side_effect = [whoami_proc, kas_proc]

        # Mock AWS API
        api_data = {
            "daysUntilReset": 0,
            "nextDateReset": 1796083200.0,
            "overageConfiguration": {"overageStatus": "DISABLED"},
            "subscriptionInfo": {"subscriptionTitle": "KIRO PRO"},
            "usageBreakdownList": [
                {
                    "currentUsageWithPrecision": 50.0,
                    "usageLimitWithPrecision": 1000.0,
                    "resourceType": "CREDIT"
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(api_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = agy_quota.fetch_kiro_quota()
        self.assertTrue(res["success"])
        self.assertEqual(res["profile"], "kiro")
        self.assertEqual(res["tier"], "KIRO PRO")
        self.assertEqual(res["email"], "test@example.com")
        self.assertAlmostEqual(res["creditsPool"]["remaining"], 950.0)
        self.assertAlmostEqual(res["creditsPool"]["fraction"], 0.95)

    @patch("agy_quota.subprocess.run")
    def test_open_cli_kiro_executes_kiro_cli(self, mock_run):
        """Verify /api/open-cli opens kiro-cli in Terminal instead of agy."""
        handler = MagicMock()
        handler.path = "/api/open-cli?profile=kiro"
        handler.send_json = MagicMock()
        agy_quota.QuotaDashboardHandler.do_GET(handler)
        self.assertEqual(mock_run.call_count, 1)
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], "osascript")
        script_arg = call_args[2]
        self.assertIn('do script "kiro-cli"', script_arg)
        self.assertNotIn('ag_run', script_arg)

    @patch("agy_quota.subprocess.run")
    def test_login_kiro_executes_kiro_cli_login(self, mock_run):
        """Verify /api/login executes kiro-cli login for Kiro profile."""
        handler = MagicMock()
        handler.path = "/api/login?profile=kiro"
        handler.send_json = MagicMock()
        agy_quota.QuotaDashboardHandler.do_GET(handler)
        self.assertEqual(mock_run.call_count, 1)
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], "osascript")
        script_arg = call_args[2]
        self.assertIn('do script "kiro-cli login"', script_arg)

    def test_quota_dashboard_html_excludes_kiro_schedule_and_activate(self):
        """Ensure dashboard HTML does not render activate or schedule buttons for kiro."""
        html_path = agy_quota.get_dashboard_html_path()
        self.assertTrue(html_path.is_file())
        content = html_path.read_text(encoding="utf-8")
        # Ensure activate & schedule are wrapped to exclude kiro
        self.assertIn("${(profile !== 'kiro' && !data.isCreditOnly) ? `", content)
        # Ensure batch checkbox excludes kiro
        self.assertIn("const canSchedule = canOperateQuota && profile !== 'kiro' && !data.isCreditOnly;", content)
        # Ensure selectAll excludes kiro
        self.assertIn("p !== 'kiro' && !d.isCreditOnly", content)


if __name__ == "__main__":
    unittest.main()

