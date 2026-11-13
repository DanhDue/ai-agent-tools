"""Unit tests for Claude Quota Provider integration and Anthropic Live API query."""

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


class TestClaudeQuotaProvider(unittest.TestCase):
    """Test suite verifying Claude Code token extraction, live Anthropic API query, and cache fallback."""

    def test_token_from_env_variable(self):
        """Token provided via CLAUDE_CODE_OAUTH_TOKEN takes immediate precedence."""
        with patch.dict(
            os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "test-env-token-12345"}
        ):
            token, email, is_logged_in = agy_quota.get_claude_oauth_token()
            self.assertEqual(token, "test-env-token-12345")
            self.assertTrue(is_logged_in)

    def test_token_from_keychain_valid(self):
        """Valid unexpired token is extracted from macOS Keychain."""
        kc_json = json.dumps(
            {
                "claudeAiOauth": {
                    "accessToken": "sk-ant-test-access-token",
                    "refreshToken": "test-refresh-token",
                    "expiresAt": 9999999999000,
                }
            }
        )
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = kc_json

        with patch.dict(os.environ, {}, clear=False):
            if "CLAUDE_CODE_OAUTH_TOKEN" in os.environ:
                del os.environ["CLAUDE_CODE_OAUTH_TOKEN"]
            with patch("subprocess.run", return_value=mock_proc):
                token, email, is_logged_in = agy_quota.get_claude_oauth_token()
                self.assertEqual(token, "sk-ant-test-access-token")
                self.assertTrue(is_logged_in)

    def test_token_from_keychain_logged_out(self):
        """Empty tokens in Keychain return is_logged_in=False."""
        kc_json = json.dumps(
            {
                "claudeAiOauth": {
                    "accessToken": "",
                    "refreshToken": "",
                    "expiresAt": 0,
                }
            }
        )
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = kc_json

        with patch.dict(os.environ, {}, clear=False):
            if "CLAUDE_CODE_OAUTH_TOKEN" in os.environ:
                del os.environ["CLAUDE_CODE_OAUTH_TOKEN"]
            with patch("subprocess.run", return_value=mock_proc):
                token, email, is_logged_in = agy_quota.get_claude_oauth_token()
                self.assertIsNone(token)
                self.assertFalse(is_logged_in)

    def test_fetch_claude_quota_live_api_success(self):
        """When token is available, query live API and parse five_hour & seven_day utilization."""
        live_api_response = {
            "five_hour": {"utilization": 25, "resets_at": "2026-11-08T05:00:00Z"},
            "seven_day": {"utilization": 60, "resets_at": "2026-11-14T23:59:59Z"},
        }
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(live_api_response).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp

        with (
            patch(
                "agy_quota.get_claude_oauth_token",
                return_value=("sk-ant-live-token", "user@anthropic.com", True),
            ),
            patch("urllib.request.urlopen", return_value=mock_resp),
            patch("agy_quota.update_claude_json_cache") as mock_cache_update,
        ):
            data = agy_quota.fetch_claude_quota()
            self.assertEqual(data["profile"], "claude")
            self.assertEqual(data["tier"], "ANTHROPIC")
            self.assertEqual(data["status"], "ACTIVE")
            self.assertTrue(data["gemini5h"]["isLive"])
            # Remaining 5h: 100% - 25% = 75%
            self.assertAlmostEqual(data["gemini5h"]["fraction"], 0.75)
            # Remaining 7d: 100% - 60% = 40%
            self.assertAlmostEqual(data["geminiWeekly"]["fraction"], 0.40)
            mock_cache_update.assert_called_once()

    def test_fetch_claude_quota_offline_fallback(self):
        """When unauthenticated and API fails, fall back to cachedUsageUtilization with NEED_LOGIN status."""
        cached_json = {
            "oauthAccount": {
                "emailAddress": "danhdue@gmail.com",
                "accountUuid": "acc-12345",
            },
            "cachedUsageUtilization": {
                "utilization": {
                    "five_hour": {
                        "utilization": 15,
                        "resets_at": "2026-11-08T00:49:59Z",
                    },
                    "seven_day": {
                        "utilization": 88,
                        "resets_at": "2026-11-10T23:59:59Z",
                    },
                }
            },
        }
        with (
            patch("agy_quota.get_claude_oauth_token", return_value=(None, None, False)),
            patch("pathlib.Path.is_file", return_value=True),
            patch(
                "builtins.open",
                unittest.mock.mock_open(read_data=json.dumps(cached_json)),
            ),
        ):
            data = agy_quota.fetch_claude_quota()
            self.assertEqual(data["profile"], "claude")
            self.assertEqual(data["status"], "NEED_LOGIN")
            self.assertFalse(data["gemini5h"]["isLive"])
            self.assertIn("Chưa đăng nhập", data["email"])
            self.assertEqual(data["remainingCountdown"], "Cần đăng nhập")
            # 100% - 15% = 85%
            self.assertAlmostEqual(data["gemini5h"]["fraction"], 0.85)
            # 100% - 88% = 12%
            self.assertAlmostEqual(data["geminiWeekly"]["fraction"], 0.12)

    def test_print_claude_card(self):
        """Verify print_claude_card renders without errors."""
        sample_data = {
            "tier": "ANTHROPIC",
            "email": "danhdue@gmail.com",
            "status": "ACTIVE",
            "gemini5h": {
                "name": "Claude 5H Session Window",
                "fraction": 0.85,
                "countdown": "⏱ 4h 30m",
                "isLive": True,
            },
            "geminiWeekly": {
                "name": "Claude 7D Weekly Remaining",
                "fraction": 0.12,
                "countdown": "⏱ 3d 2h",
            },
        }
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            agy_quota.print_claude_card(sample_data)
        out = captured.getvalue()
        self.assertIn("Claude Code", out)
        self.assertIn("Live API", out)
        self.assertIn("Claude 5H Session Window", out)
        self.assertIn("Claude 7D Weekly Remaining", out)
        self.assertIn("claude auth login", out)


if __name__ == "__main__":
    unittest.main()
