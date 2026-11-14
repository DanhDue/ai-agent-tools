"""Unit tests for Claude Quota Provider integration and Anthropic Live API query."""

from __future__ import annotations

import datetime
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
REFRESH_SCRIPTS_DIR = REPO_ROOT / "skills" / "refresh-session" / "resources" / "scripts"
QUOTA_DASHBOARD_HTML = (
    REPO_ROOT
    / "skills"
    / "check-quota"
    / "resources"
    / "dashboard"
    / "quota_dashboard.html"
)

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(REFRESH_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(REFRESH_SCRIPTS_DIR))

import agy_quota  # noqa: E402
import refresh_session  # noqa: E402


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

    def test_build_claude_quota_buckets_limits_with_fable_and_shares(self):
        """build_claude_quota_buckets extracts session, weekly_all, and scoped Fable + shares without duplicates."""
        now_utc = datetime.datetime(
            2026, 11, 14, 20, 45, 0, tzinfo=datetime.timezone.utc
        )
        api_data = {
            "five_hour": {
                "utilization": 100.0,
                "resets_at": "2026-11-14T21:40:00Z",
            },
            "seven_day": {
                "utilization": 14.0,
                "resets_at": "2026-11-18T00:00:00Z",
            },
            "limits": [
                {
                    "kind": "session",
                    "group": "session",
                    "percent": 100,
                    "severity": "critical",
                    "resets_at": "2026-11-14T21:40:00Z",
                    "scope": None,
                    "is_active": True,
                },
                {
                    "kind": "weekly_all",
                    "group": "weekly",
                    "percent": 14,
                    "severity": "normal",
                    "resets_at": "2026-11-18T00:00:00Z",
                    "scope": None,
                    "is_active": False,
                },
                {
                    "kind": "weekly_scoped",
                    "group": "weekly",
                    "percent": 27,
                    "severity": "normal",
                    "resets_at": "2026-11-18T00:00:00Z",
                    "scope": {
                        "model": {"id": None, "display_name": "Fable"},
                        "surface": None,
                    },
                    "is_active": False,
                },
            ],
            "weekly_scoped_shares": [
                {
                    "limit_index": 2,
                    "used_percent_of_weekly": 14,
                    "allowance_percent_of_weekly": 50,
                }
            ],
        }

        buckets = agy_quota.build_claude_quota_buckets(
            api_data, now_utc=now_utc, is_live=True
        )
        self.assertEqual(len(buckets), 3)

        b_5h, b_7d, b_fable = buckets
        self.assertEqual(b_5h["id"], "session")
        self.assertEqual(b_5h["name"], "Claude 5H Session Window")
        self.assertEqual(b_5h["group"], "session")
        self.assertEqual(b_5h["kind"], "session")
        self.assertAlmostEqual(b_5h["fraction"], 0.0)
        self.assertAlmostEqual(b_5h["utilization"], 100.0)
        self.assertEqual(b_5h["severity"], "critical")
        self.assertTrue(b_5h["isActive"])
        self.assertTrue(b_5h["isLive"])
        self.assertIsNone(b_5h["shareInfo"])
        self.assertFalse(b_5h["unavailable"])

        self.assertEqual(b_7d["id"], "weekly_all")
        self.assertEqual(b_7d["name"], "Claude 7D Weekly Remaining")
        self.assertEqual(b_7d["group"], "weekly")
        self.assertAlmostEqual(b_7d["fraction"], 0.86)
        self.assertAlmostEqual(b_7d["utilization"], 14.0)
        self.assertIsNone(b_7d["shareInfo"])

        self.assertEqual(b_fable["kind"], "weekly_scoped")
        self.assertEqual(b_fable["group"], "weekly")
        self.assertEqual(b_fable["scopeLabel"], "Fable")
        self.assertEqual(b_fable["name"], "Claude 7D — Fable")
        self.assertAlmostEqual(b_fable["fraction"], 0.73)
        self.assertAlmostEqual(b_fable["utilization"], 27.0)
        self.assertIsInstance(b_fable["shareInfo"], dict)
        self.assertEqual(b_fable["shareInfo"]["limitIndex"], 2)
        self.assertEqual(b_fable["shareInfo"]["usedPercentOfWeekly"], 14)
        self.assertEqual(b_fable["shareInfo"]["allowancePercentOfWeekly"], 50)
        self.assertIn("50%", b_fable["shareInfo"]["label"])

    def test_build_claude_quota_buckets_future_scopes_and_seven_day_fallbacks(self):
        """Handles future unknown model/surface scopes, partial limits, seven_day_* fallback, and empty payloads."""
        now_utc = datetime.datetime(
            2026, 11, 14, 20, 45, 0, tzinfo=datetime.timezone.utc
        )
        cases = [
            (
                "future_model_and_surface",
                {
                    "limits": [
                        {
                            "kind": "session",
                            "group": "session",
                            "percent": 10,
                            "resets_at": "2026-11-14T23:00:00Z",
                            "scope": None,
                            "is_active": True,
                        },
                        {
                            "kind": "weekly_all",
                            "group": "weekly",
                            "percent": 20,
                            "resets_at": "2026-11-18T00:00:00Z",
                            "scope": None,
                            "is_active": False,
                        },
                        {
                            "kind": "weekly_scoped",
                            "group": "weekly",
                            "percent": 40,
                            "resets_at": "2026-11-18T00:00:00Z",
                            "scope": {
                                "model": {"id": "sonnet-x", "display_name": "Sonnet X"},
                                "surface": "cowork",
                            },
                            "is_active": False,
                        },
                    ]
                },
                [
                    "Claude 5H Session Window",
                    "Claude 7D Weekly Remaining",
                    "Claude 7D — Sonnet X · Cowork",
                ],
                [0.9, 0.8, 0.6],
            ),
            (
                "model_id_fallback_and_surface_only",
                {
                    "limits": [
                        {
                            "kind": "weekly_scoped",
                            "group": "weekly",
                            "percent": 30,
                            "resets_at": "2026-11-18T00:00:00Z",
                            "scope": {
                                "model": {
                                    "id": "claude-opus-4-6",
                                    "display_name": None,
                                },
                                "surface": None,
                            },
                            "is_active": False,
                        },
                        {
                            "kind": "promo_surface",
                            "group": "weekly",
                            "percent": 50,
                            "resets_at": "2026-11-18T00:00:00Z",
                            "scope": {"model": None, "surface": "cowork"},
                            "is_active": False,
                        },
                    ],
                    "five_hour": {
                        "utilization": 0,
                        "resets_at": "2026-11-14T23:00:00Z",
                    },
                    "seven_day": {
                        "utilization": 5,
                        "resets_at": "2026-11-18T00:00:00Z",
                    },
                },
                [
                    "Claude 7D — claude-opus-4-6",
                    "Claude 7D — Cowork",
                    "Claude 5H Session Window",
                    "Claude 7D Weekly Remaining",
                ],
                [0.7, 0.5, 1.0, 0.95],
            ),
            (
                "seven_day_fallback_without_limits",
                {
                    "five_hour": {
                        "utilization": 25,
                        "resets_at": "2026-11-14T23:00:00Z",
                    },
                    "seven_day": {
                        "utilization": 10,
                        "resets_at": "2026-11-18T00:00:00Z",
                    },
                    "seven_day_sonnet": {
                        "utilization": 35,
                        "resets_at": "2026-11-18T00:00:00Z",
                    },
                    "seven_day_opus": {
                        "utilization": 60,
                        "resets_at": "2026-11-18T00:00:00Z",
                    },
                    "seven_day_cowork": None,
                    "seven_day_omelette": {
                        "utilization": 15,
                        "resets_at": "2026-11-18T00:00:00Z",
                    },
                    "seven_day_breakdown": {
                        "rows": [{"key": "claude_code", "percent": 100}]
                    },
                },
                [
                    "Claude 5H Session Window",
                    "Claude 7D Weekly Remaining",
                    "Claude 7D — Sonnet",
                    "Claude 7D — Opus",
                    "Claude 7D — Omelette",
                ],
                [0.75, 0.90, 0.65, 0.40, 0.85],
            ),
            (
                "partial_limits_dedup_against_seven_day_keys",
                {
                    "limits": [
                        {
                            "kind": "session",
                            "group": "session",
                            "percent": 15,
                            "resets_at": "2026-11-14T23:00:00Z",
                            "scope": None,
                            "is_active": True,
                        },
                        {
                            "kind": "weekly_all",
                            "group": "weekly",
                            "percent": 12,
                            "resets_at": "2026-11-18T00:00:00Z",
                            "scope": None,
                            "is_active": False,
                        },
                        {
                            "kind": "weekly_scoped",
                            "group": "weekly",
                            "percent": 22,
                            "resets_at": "2026-11-18T00:00:00Z",
                            "scope": {
                                "model": {"id": None, "display_name": "Sonnet"},
                                "surface": None,
                            },
                            "is_active": False,
                        },
                    ],
                    "five_hour": {
                        "utilization": 15,
                        "resets_at": "2026-11-14T23:00:00Z",
                    },
                    "seven_day": {
                        "utilization": 12,
                        "resets_at": "2026-11-18T00:00:00Z",
                    },
                    "seven_day_sonnet": {
                        "utilization": 22,
                        "resets_at": "2026-11-18T00:00:00Z",
                    },
                    "seven_day_opus": {
                        "utilization": 45,
                        "resets_at": "2026-11-18T00:00:00Z",
                    },
                },
                [
                    "Claude 5H Session Window",
                    "Claude 7D Weekly Remaining",
                    "Claude 7D — Sonnet",
                    "Claude 7D — Opus",
                ],
                [0.85, 0.88, 0.78, 0.55],
            ),
            (
                "empty_payload_graceful_fallback",
                {},
                ["Claude 5H Session Window", "Claude 7D Weekly Remaining"],
                [1.0, 1.0],
            ),
        ]

        for label, payload, expected_names, expected_fractions in cases:
            with self.subTest(label=label):
                buckets = agy_quota.build_claude_quota_buckets(payload, now_utc=now_utc)
                self.assertEqual([b["name"] for b in buckets], expected_names)
                for b, exp_frac in zip(buckets, expected_fractions):
                    self.assertAlmostEqual(b["fraction"], exp_frac)

    def test_fetch_claude_quota_and_cache_merge_preserves_richer_fields(self):
        """fetch_claude_quota attaches quotaBuckets and cache updaters do not clobber limits on narrow responses."""
        rich_initial = {
            "oauthAccount": {
                "emailAddress": "danhdue@gmail.com",
                "accountUuid": "acc-uuid-1",
            },
            "cachedUsageUtilization": {
                "fetchedAtMs": 1000,
                "accountUuid": "acc-uuid-1",
                "utilization": {
                    "five_hour": {
                        "utilization": 10.0,
                        "resets_at": "2026-11-14T21:00:00Z",
                    },
                    "seven_day": {
                        "utilization": 5.0,
                        "resets_at": "2026-11-18T00:00:00Z",
                    },
                    "limits": [
                        {
                            "kind": "session",
                            "group": "session",
                            "percent": 10,
                            "resets_at": "2026-11-14T21:00:00Z",
                            "scope": None,
                            "is_active": True,
                        },
                        {
                            "kind": "weekly_all",
                            "group": "weekly",
                            "percent": 5,
                            "resets_at": "2026-11-18T00:00:00Z",
                            "scope": None,
                            "is_active": False,
                        },
                        {
                            "kind": "weekly_scoped",
                            "group": "weekly",
                            "percent": 27,
                            "resets_at": "2026-11-18T00:00:00Z",
                            "scope": {
                                "model": {"id": None, "display_name": "Fable"},
                                "surface": None,
                            },
                            "is_active": False,
                        },
                    ],
                    "weekly_scoped_shares": [
                        {
                            "limit_index": 2,
                            "used_percent_of_weekly": 5,
                            "allowance_percent_of_weekly": 50,
                        }
                    ],
                },
            },
        }
        narrow_live = {
            "five_hour": {"utilization": 42.0, "resets_at": "2026-11-14T22:00:00Z"},
            "seven_day": {"utilization": 18.0, "resets_at": "2026-11-18T00:00:00Z"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            claude_json = Path(tmpdir) / ".claude.json"
            claude_json.write_text(json.dumps(rich_initial), encoding="utf-8")

            with patch.object(agy_quota, "REAL_HOME", tmpdir):
                agy_quota.update_claude_json_cache(
                    narrow_live, account_uuid="acc-uuid-1"
                )
            updated = json.loads(claude_json.read_text(encoding="utf-8"))
            util = updated["cachedUsageUtilization"]["utilization"]
            self.assertEqual(len(util["limits"]), 3)
            self.assertEqual(util["limits"][0]["percent"], 42.0)
            self.assertEqual(util["limits"][1]["percent"], 18.0)
            self.assertEqual(
                util["limits"][2]["scope"]["model"]["display_name"], "Fable"
            )
            self.assertEqual(len(util["weekly_scoped_shares"]), 1)

            # Reset and verify refresh_session._update_claude_cache_file too
            claude_json.write_text(json.dumps(rich_initial), encoding="utf-8")
            with patch.object(refresh_session, "REAL_HOME", tmpdir):
                refresh_session._update_claude_cache_file(narrow_live)
            updated_rs = json.loads(claude_json.read_text(encoding="utf-8"))
            util_rs = updated_rs["cachedUsageUtilization"]["utilization"]
            self.assertEqual(len(util_rs["limits"]), 3)
            self.assertEqual(util_rs["limits"][0]["percent"], 42.0)
            self.assertEqual(len(util_rs["weekly_scoped_shares"]), 1)

            # When live API explicitly returns an updated limits array (e.g. promo ended), it replaces limits
            promo_ended_live = {
                "five_hour": {"utilization": 50.0, "resets_at": "2026-11-14T22:00:00Z"},
                "seven_day": {"utilization": 20.0, "resets_at": "2026-11-18T00:00:00Z"},
                "limits": [
                    {
                        "kind": "session",
                        "group": "session",
                        "percent": 50,
                        "resets_at": "2026-11-14T22:00:00Z",
                        "scope": None,
                        "is_active": True,
                    },
                    {
                        "kind": "weekly_all",
                        "group": "weekly",
                        "percent": 20,
                        "resets_at": "2026-11-18T00:00:00Z",
                        "scope": None,
                        "is_active": False,
                    },
                ],
                "weekly_scoped_shares": [],
            }
            with patch.object(agy_quota, "REAL_HOME", tmpdir):
                agy_quota.update_claude_json_cache(
                    promo_ended_live, account_uuid="acc-uuid-1"
                )
            ended = json.loads(claude_json.read_text(encoding="utf-8"))
            self.assertEqual(
                len(ended["cachedUsageUtilization"]["utilization"]["limits"]), 2
            )
            self.assertEqual(
                ended["cachedUsageUtilization"]["utilization"]["weekly_scoped_shares"],
                [],
            )

            # Different accountUuid must reset rather than inheriting another account's limits[]
            claude_json.write_text(json.dumps(rich_initial), encoding="utf-8")
            with patch.object(agy_quota, "REAL_HOME", tmpdir):
                agy_quota.update_claude_json_cache(
                    narrow_live, account_uuid="acc-uuid-2"
                )
            switched = json.loads(claude_json.read_text(encoding="utf-8"))
            self.assertEqual(
                switched["cachedUsageUtilization"]["accountUuid"], "acc-uuid-2"
            )
            self.assertNotIn(
                "limits", switched["cachedUsageUtilization"]["utilization"]
            )
            self.assertNotIn(
                "weekly_scoped_shares",
                switched["cachedUsageUtilization"]["utilization"],
            )

        # End-to-end fetch_claude_quota() populates quotaBuckets
        live_full = {
            "five_hour": {"utilization": 100.0, "resets_at": "2026-11-14T21:40:00Z"},
            "seven_day": {"utilization": 14.0, "resets_at": "2026-11-18T00:00:00Z"},
            "limits": rich_initial["cachedUsageUtilization"]["utilization"]["limits"],
            "weekly_scoped_shares": rich_initial["cachedUsageUtilization"][
                "utilization"
            ]["weekly_scoped_shares"],
        }
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(live_full).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        with (
            patch(
                "agy_quota.get_claude_oauth_token",
                return_value=("sk-ant-live", "user@anthropic.com", True),
            ),
            patch("urllib.request.urlopen", return_value=mock_resp),
            patch("agy_quota.update_claude_json_cache"),
            patch("agy_quota.save_session_record"),
        ):
            data = agy_quota.fetch_claude_quota()
            self.assertIn("quotaBuckets", data)
            self.assertEqual(len(data["quotaBuckets"]), 3)
            self.assertEqual(data["quotaBuckets"][2]["name"], "Claude 7D — Fable")
            self.assertIn("gemini5h", data)
            self.assertIn("geminiWeekly", data)

    def test_print_claude_card_renders_three_plus_buckets(self):
        """print_claude_card renders all dynamic buckets including odd 3rd card (Fable) and 4-card grids."""
        three_buckets = {
            "tier": "ANTHROPIC",
            "email": "danhdue@gmail.com",
            "status": "ACTIVE",
            "gemini5h": {
                "name": "Claude 5H Session Window",
                "fraction": 0.0,
                "countdown": "⏱ 2h 10m",
                "isLive": True,
            },
            "geminiWeekly": {
                "name": "Claude 7D Weekly Remaining",
                "fraction": 0.86,
                "countdown": "⏱ 3d 4h",
            },
            "quotaBuckets": [
                {
                    "name": "Claude 5H Session Window",
                    "fraction": 0.0,
                    "countdown": "⏱ 2h 10m",
                    "isLive": True,
                    "unavailable": False,
                },
                {
                    "name": "Claude 7D Weekly Remaining",
                    "fraction": 0.86,
                    "countdown": "⏱ 3d 4h",
                    "unavailable": False,
                },
                {
                    "name": "Claude 7D — Fable",
                    "scopeLabel": "Fable",
                    "fraction": 0.73,
                    "countdown": "⏱ 3d 4h",
                    "unavailable": False,
                    "shareInfo": {
                        "limitIndex": 2,
                        "usedPercentOfWeekly": 14,
                        "allowancePercentOfWeekly": 50,
                        "label": "Allowance: 50% of weekly (used 14%)",
                    },
                },
            ],
        }
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            agy_quota.print_claude_card(three_buckets)
        out = captured.getvalue()
        self.assertIn("Claude 5H Session Window", out)
        self.assertIn("Claude 7D Weekly Remaining", out)
        self.assertIn("Claude 7D — Fable", out)
        self.assertIn("73.0%", out)
        self.assertIn("Allowance: 50% of weekly", out)

        with self.subTest("four_buckets_and_terminal_sanitization"):
            four_buckets = {
                "tier": "ANTHROPIC",
                "email": "danhdue@gmail.com",
                "status": "ACTIVE",
                "quotaBuckets": [
                    *three_buckets["quotaBuckets"],
                    {
                        "name": "Claude 7D — \x1b[31mSonnetX\x1b[0m\nFake",
                        "scopeLabel": "SonnetX",
                        "fraction": 0.40,
                        "countdown": "⏱ 1d 2h",
                        "unavailable": False,
                    },
                ],
            }
            captured_four = io.StringIO()
            with patch("sys.stdout", captured_four):
                agy_quota.print_claude_card(four_buckets)
            out_four = captured_four.getvalue()
            self.assertIn("Claude 7D — SonnetX Fake", out_four)
            self.assertIn("40.0%", out_four)
            self.assertNotIn("\x1b[31m", out_four)

    def test_quota_dashboard_html_renders_dynamic_buckets_escapes_xss_and_falls_back(
        self,
    ):
        """quota_dashboard.html renders dynamic Claude quotaBuckets, escapes XSS payloads, and falls back cleanly."""
        node_bin = shutil.which("node")
        if node_bin is None:
            self.skipTest(
                "Node.js binary is required for quota_dashboard.html VM harness"
            )

        script = r"""
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const html = fs.readFileSync(__HTML_PATH__, 'utf8');
const scriptMatches = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(scriptMatches.length, 1, 'Expected single inline <script>');
const quotaScript = scriptMatches[0][1];

function createClassList() {
  const classes = new Set();
  return {
    add(...items) { items.forEach((c) => classes.add(c)); },
    remove(...items) { items.forEach((c) => classes.delete(c)); },
    contains(c) { return classes.has(c); },
    toggle(c, f) { if (f === true) { classes.add(c); return true; } if (f === false) { classes.delete(c); return false; } return classes.has(c) ? (classes.delete(c), false) : (classes.add(c), true); },
    toString() { return [...classes].join(' '); },
  };
}

class FakeElement {
  constructor(tag = 'div', id = '') {
    this.tagName = tag.toUpperCase();
    this.id = id;
    this.style = { display: '', overflow: '' };
    this.classList = createClassList();
    this.innerHTML = '';
    this.value = '';
    this.textContent = '';
    this.children = [];
  }
  setAttribute() {}
  getAttribute() { return null; }
  addEventListener() {}
  querySelectorAll() { return []; }
  querySelector() { return null; }
  appendChild(ch) { this.children.push(ch); return ch; }
}

const byId = new Map();
for (const id of ['profilesGrid', 'gridCol1', 'gridCol2', 'searchInput', 'statusFilter', 'sortOrderSelect', 'statActive', 'statDisabled', 'statAuth', 'statExhausted', 'statProviders', 'statProfiles', 'statArgon']) {
  byId.set(id, new FakeElement('div', id));
}

const doc = {
  body: new FakeElement('body'),
  documentElement: new FakeElement('html'),
  getElementById(id) { return byId.get(id) || null; },
  createElement(tag) { return new FakeElement(tag); },
  querySelectorAll() { return []; },
  querySelector() { return null; },
  addEventListener() {},
};

const win = {
  location: { protocol: 'http:', origin: 'http://127.0.0.1:8765', host: '127.0.0.1:8765', search: '?no-auto-refresh=1' },
  innerWidth: 1280,
  innerHeight: 800,
  addEventListener() {},
};
win.parent = win;

const consoleErrors = [];
const sandbox = {
  window: win,
  document: doc,
  localStorage: { getItem() { return null; }, setItem() {}, removeItem() {} },
  navigator: { clipboard: { writeText: async () => {} } },
  fetch: async () => ({ async json() { return { success: false }; } }),
  alert() {},
  confirm() { return true; },
  console: { log() {}, warn() {}, error(...args) { consoleErrors.push(args.join(' ')); } },
  URLSearchParams,
  URL,
  Event: class Event { constructor(t) { this.type = t; } },
  requestAnimationFrame: (fn) => { if (typeof fn === 'function') fn(); return 0; },
  setTimeout: () => 0,
  clearTimeout: () => {},
  setInterval: () => 0,
  clearInterval: () => {},
};
sandbox.globalThis = sandbox;
sandbox.self = win;
vm.createContext(sandbox);
new vm.Script(quotaScript, { filename: 'quota_dashboard.html' }).runInContext(sandbox);

// 1. Dynamic quotaBuckets with Fable + XSS attempt
const claudeWithBuckets = {
  profile: 'claude',
  displayName: 'Claude Code',
  isProvider: true,
  providerType: 'claude',
  tier: 'ANTHROPIC',
  priority: 100,
  email: 'danhdue@gmail.com',
  status: 'ACTIVE',
  gemini5h: { name: 'Claude 5H Session Window', fraction: 0.0, countdown: '⏱ 2h 0m', unavailable: false },
  geminiWeekly: { name: 'Claude 7D Weekly Remaining', fraction: 0.86, countdown: '⏱ 3d 4h', unavailable: false },
  quotaBuckets: [
    { id: 'session', name: 'Claude 5H Session Window', group: 'session', kind: 'session', scopeLabel: '', fraction: 0.0, utilization: 100.0, countdown: '⏱ 2h 0m', unavailable: false },
    { id: 'weekly_all', name: 'Claude 7D Weekly Remaining', group: 'weekly', kind: 'weekly_all', scopeLabel: '', fraction: 0.86, utilization: 14.0, countdown: '⏱ 3d 4h', unavailable: false },
    { id: 'weekly_scoped_fable', name: 'Claude 7D — Fable', group: 'weekly', kind: 'weekly_scoped', scopeLabel: 'Fable', fraction: 0.73, utilization: 27.0, countdown: '⏱ 3d 4h', shareInfo: { label: 'Allowance: 50% of weekly (used 14%)' }, unavailable: false },
    { id: 'weekly_scoped_xss', name: 'Claude 7D — <img src=x onerror=alert(1)>', group: 'weekly', kind: 'weekly_scoped', scopeLabel: '<img src=x onerror=alert(1)>', fraction: 0.50, utilization: 50.0, countdown: '⏱ <script>evil()</script>', unavailable: false },
  ],
};

const cardHtml = sandbox.renderProfileCard('claude', claudeWithBuckets);
assert.ok(cardHtml.includes('Claude 5H Session Window'), 'Renders 5H bucket');
assert.ok(cardHtml.includes('Claude 7D Weekly Remaining'), 'Renders 7D bucket');
assert.ok(cardHtml.includes('Claude 7D — Fable'), 'Renders Fable bucket');
assert.ok(cardHtml.includes('73.0%'), 'Renders Fable percentage');
assert.ok(cardHtml.includes('Allowance: 50% of weekly'), 'Renders shareInfo badge');
assert.ok(!cardHtml.includes('<img src=x'), 'XSS img tag must be HTML-escaped');
assert.ok(!cardHtml.includes('<script>evil()'), 'XSS script tag must be HTML-escaped');
assert.ok(cardHtml.includes('&lt;img src=x onerror=alert(1)&gt;'), 'Escaped XSS string preserved visibly');

// 2. Fallback when quotaBuckets is absent
const legacyClaude = {
  profile: 'claude',
  displayName: 'Claude Code',
  isProvider: true,
  tier: 'ANTHROPIC',
  status: 'ACTIVE',
  gemini5h: { name: 'Claude 5H Session Window', fraction: 0.5, countdown: '⏱ 3h 0m', unavailable: false },
  geminiWeekly: { name: 'Claude 7D Weekly Remaining', fraction: 0.9, countdown: '⏱ 5d 0h', unavailable: false },
};
const fallbackHtml = sandbox.renderProfileCard('claude', legacyClaude);
assert.ok(fallbackHtml.includes('Claude 5H Session Window'));
assert.ok(fallbackHtml.includes('Claude 7D Weekly Remaining'));
assert.ok(!fallbackHtml.includes('undefined'));

// 3. Search filter matches Fable in quotaBuckets
vm.runInContext(`PROFILES_DATA.claude = ${JSON.stringify(claudeWithBuckets)};`, sandbox);
byId.get('searchInput').value = 'fable';
sandbox.renderAllProfiles();
assert.ok(byId.get('gridCol1').innerHTML.includes('Claude 7D — Fable'), 'Search for fable finds Claude card');

// 4. Score calculation handles quotaBuckets safely
const score = sandbox.getProfileQuotaScore('claude');
assert.ok(Number.isFinite(score) && score > 0);
assert.equal(consoleErrors.length, 0, 'No console errors expected');
console.log(JSON.stringify({ ok: true, score }));
""".replace("__HTML_PATH__", json.dumps(str(QUOTA_DASHBOARD_HTML)))

        proc = subprocess.run(
            [node_bin, "--input-type=module", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(
            proc.returncode,
            0,
            f"Node VM check failed (rc={proc.returncode}):\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
        )
        res = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertTrue(res.get("ok"))


if __name__ == "__main__":
    unittest.main()
