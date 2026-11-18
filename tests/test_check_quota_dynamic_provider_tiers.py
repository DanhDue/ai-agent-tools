"""Unit tests for dynamic 4-provider account tiers, priorities, AccountMeta, and daemon hot-reload."""

from __future__ import annotations

import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
import urllib.parse
import urllib.request

import pytest  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
TYPES_FILE = SCRIPTS_DIR / "types" / "quota_dashboard.types.ts"
DASHBOARD_HTML_PATH = (
    REPO_ROOT
    / "skills"
    / "check-quota"
    / "resources"
    / "dashboard"
    / "quota_dashboard.html"
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import agy_quota  # type: ignore[import-not-found]  # noqa: E402
from tests.test_cqra_review_action_e2e import (  # noqa: E402
    _CdpSession,
    _find_chrome_binary,
    _pick_free_port,
)


def _make_jwt(claims: dict[str, Any]) -> str:
    """Create a synthetic unsigned base64url JWT for offline claim parsing tests."""
    header = (
        base64.urlsafe_b64encode(b'{"alg":"RS256","typ":"JWT"}')
        .decode("ascii")
        .rstrip("=")
    )
    body = (
        base64.urlsafe_b64encode(json.dumps(claims).encode("utf-8"))
        .decode("ascii")
        .rstrip("=")
    )
    return f"{header}.{body}.synthetic_signature_payload"


def _setup_isolated_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    profiles: list[str] | None = None,
    initial_cache: dict[str, Any] | None = None,
) -> Path:
    """Isolate REAL_HOME, SQLite session store, and dashboard HTML cache under tmp_path."""
    homes_root = tmp_path / "antigravity_homes"
    homes_root.mkdir(parents=True, exist_ok=True)
    for prof in profiles or []:
        p_home = homes_root / prof
        tok_file = p_home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
        tok_file.parent.mkdir(parents=True, exist_ok=True)
        tok_file.write_text(
            json.dumps(
                {
                    "token": {
                        "access_token": "ya29.secret_agy_access",
                        "refresh_token": "1//secret_agy_refresh",
                    }
                }
            ),
            encoding="utf-8",
        )

    dash_html = tmp_path / "quota_dashboard.html"
    cache_payload = dict(initial_cache or {})
    serialized_cache = json.dumps(cache_payload, indent=2) if cache_payload else "{\n}"
    dash_html.write_text(
        "<html><script>\nconst PROFILES_DATA = "
        + serialized_cache
        + ";\n</script></html>\n",
        encoding="utf-8",
    )

    fake_home = tmp_path / "host_home"
    fake_home.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(agy_quota, "REAL_HOME", str(tmp_path))
    monkeypatch.setattr(agy_quota, "SESSION_STORE_DB", tmp_path / ".session_store.db")
    monkeypatch.setattr(agy_quota, "CACHED_PROFILES_DATA", {})
    if hasattr(agy_quota, "CACHED_HTML_MTIME"):
        monkeypatch.setattr(agy_quota, "CACHED_HTML_MTIME", 0.0)
    monkeypatch.setattr(agy_quota, "get_dashboard_html_path", lambda: dash_html)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    monkeypatch.setattr(agy_quota, "wait_for_launch_lock", lambda *_a, **_kw: None)
    monkeypatch.setattr(agy_quota.time, "sleep", lambda *_a, **_kw: None)
    return dash_html


def _assert_zero_secret_leakage(payload: Any, forbidden_values: list[str]) -> None:
    """Assert serialized payload contains zero raw tokens or secret keys."""
    serialized = json.dumps(payload, ensure_ascii=False)
    for secret in forbidden_values:
        assert secret not in serialized, f"Secret token leaked into payload: {secret!r}"
    for bad_key in (
        "accessToken",
        "refreshToken",
        "access_token",
        "refresh_token",
        "id_token",
        "kas_token",
    ):
        assert f'"{bad_key}"' not in serialized, (
            f"Forbidden secret key {bad_key!r} present in payload"
        )


def test_parse_usage_group_models_strips_live_prefix_and_skips_argon_prose() -> None:
    """Strip 'Models within this group:' prefix and skip prose descriptions on Pro Argon groups."""
    ultra_groups = [
        {
            "name": "Gemini Models",
            "description": (
                "Models within this group: Gemini 4 Carbon, Gemini 4 Argon, "
                "Gemini 4 Hydrogen, Orchestrator (Carbon), Orchestrator (Argon), Gemini 3.8 Flash"
            ),
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 0.9,
                    "reset_time": "2026-11-18T10:00:00Z",
                }
            ],
        },
        {
            "name": "Claude and GPT models",
            "description": "Models within this group: Claude Sonnet 4.6, Claude Opus 4.6, GPT-OSS 120B",
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 0.8,
                    "reset_time": "2026-11-18T10:00:00Z",
                }
            ],
        },
    ]
    parsed_ultra = agy_quota.parse_usage_group_models(ultra_groups)
    assert parsed_ultra["groupModels"]["gemini"] == [
        "Gemini 4 Carbon",
        "Gemini 4 Argon",
        "Gemini 4 Hydrogen",
        "Orchestrator (Carbon)",
        "Orchestrator (Argon)",
        "Gemini 3.8 Flash",
    ]
    assert parsed_ultra["groupModels"]["claude"][0] == "Claude Sonnet 4.6"
    assert all(
        "models within this group" not in m.lower()
        for fam in ("gemini", "claude", "argon")
        for m in parsed_ultra["groupModels"][fam]
    )

    pro_argon_prose = (
        "For paid Pro plans, Argon quota is separate. Higher Argon quota "
        "(included as part of the larger Gemini quota bucket) is available on Ultra plans."
    )
    pro_groups = [
        {
            "name": "Gemini Models",
            "description": "Models within this group: Gemini 4 Hydrogen, Gemini 3.8 Flash",
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 1.0,
                    "reset_time": "2026-11-18T10:00:00Z",
                }
            ],
        },
        {
            "name": "Gemini 4 Argon",
            "description": pro_argon_prose,
            "buckets": [
                {
                    "window": "weekly",
                    "remaining_fraction": 0.65,
                    "reset_time": "2026-11-24T00:00:00Z",
                }
            ],
        },
    ]
    parsed_pro = agy_quota.parse_usage_group_models(pro_groups)
    assert parsed_pro["hasDedicatedArgonGroup"] is True
    assert parsed_pro["groupDescriptions"]["argon"] == pro_argon_prose
    assert parsed_pro["groupDescSig"] != ""
    assert parsed_pro["groupModels"]["argon"] == []

    reconciled = agy_quota._reconcile_group_models(parsed_pro, [])
    assert reconciled["argon"] == ["Gemini 4 Argon"]
    assert all(
        "for paid" not in m.lower() and "quota is" not in m.lower()
        for m in reconciled["argon"]
    )


@pytest.mark.parametrize(
    (
        "profile",
        "plan_name",
        "groups",
        "expected_tier",
        "expected_priority",
        "expected_argon_name",
    ),
    [
        (
            "nguyenhieu000690",
            "Google AI Ultra",
            [
                {
                    "name": "Gemini Models",
                    "description": (
                        "Models within this group: Gemini 4 Carbon, Gemini 4 Argon, "
                        "Gemini 4 Hydrogen, Orchestrator (Carbon), Orchestrator (Argon), Gemini 3.8 Flash"
                    ),
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 0.90,
                            "reset_time": "2026-11-18T10:00:00Z",
                        },
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.85,
                            "reset_time": "2026-11-24T00:00:00Z",
                        },
                    ],
                },
                {
                    "name": "Claude and GPT models",
                    "description": "Models within this group: Claude Sonnet 4.6, Claude Opus 4.6, GPT-OSS 120B",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 0.80,
                            "reset_time": "2026-11-18T10:00:00Z",
                        },
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.75,
                            "reset_time": "2026-11-24T00:00:00Z",
                        },
                    ],
                },
            ],
            "ULTRA",
            80,
            "Gemini 4 Carbon & Argon Weekly",
        ),
        (
            "danhdue",
            "Google AI Pro",
            [
                {
                    "name": "Gemini Models",
                    "description": "Models within this group: Gemini 4 Hydrogen, Gemini 3.8 Flash",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 1.0,
                            "reset_time": "2026-11-18T10:00:00Z",
                        },
                        {
                            "window": "weekly",
                            "remaining_fraction": 1.0,
                            "reset_time": "2026-11-24T00:00:00Z",
                        },
                    ],
                },
                {
                    "name": "Claude and GPT models",
                    "description": "Models within this group: Claude Opus 4.6, Claude Sonnet 4.6, GPT-OSS 120B",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 0.85,
                            "reset_time": "2026-11-18T10:00:00Z",
                        },
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.80,
                            "reset_time": "2026-11-24T00:00:00Z",
                        },
                    ],
                },
                {
                    "name": "Gemini 4 Argon",
                    "description": (
                        "For paid Pro plans, Argon quota is separate. Higher Argon quota "
                        "(included as part of the larger Gemini quota bucket) is available on Ultra plans."
                    ),
                    "buckets": [
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.50,
                            "reset_time": "2026-11-24T00:00:00Z",
                        }
                    ],
                },
            ],
            "PRO",
            60,
            "Gemini 4 Argon Weekly",
        ),
        (
            "d3molt",
            "Google AI Pro",
            [
                {
                    "name": "Gemini Models",
                    "description": "Models within this group: Gemini 4 Hydrogen, Gemini 3.8 Flash",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 1.0,
                            "reset_time": "2026-11-18T10:00:00Z",
                        },
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.92,
                            "reset_time": "2026-11-24T00:00:00Z",
                        },
                    ],
                },
                {
                    "name": "Claude and GPT models",
                    "description": "Models within this group: Claude Sonnet 4.6, GPT-OSS 120B",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 1.0,
                            "reset_time": "2026-11-18T10:00:00Z",
                        },
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.90,
                            "reset_time": "2026-11-24T00:00:00Z",
                        },
                    ],
                },
            ],
            "PRO",
            50,
            "Gemini 4 Argon Weekly",
        ),
        (
            "buivantrong8901",
            "",
            [
                {
                    "name": "Gemini Models",
                    "description": "Models within this group: Gemini 3.8 Flash",
                    "buckets": [
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.70,
                            "reset_time": "2026-11-24T00:00:00Z",
                        }
                    ],
                },
                {
                    "name": "Claude and GPT models",
                    "description": "Models within this group: Claude Sonnet 4.6",
                    "buckets": [
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.60,
                            "reset_time": "2026-11-24T00:00:00Z",
                        }
                    ],
                },
            ],
            "FREE",
            20,
            "Gemini 4 Argon Weekly",
        ),
    ],
)
def test_antigravity_tier_and_priority_matrix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    profile: str,
    plan_name: str,
    groups: list[dict[str, Any]],
    expected_tier: str,
    expected_priority: int,
    expected_argon_name: str,
) -> None:
    """Verify Antigravity ULTRA (80), PRO+Argon (60), PRO (50), and FREE (20) normalization."""
    _setup_isolated_env(tmp_path, monkeypatch, [profile])

    # Populate state.vscdb email to verify read-only SQLite extraction
    vscdb_path = (
        tmp_path
        / "antigravity_homes"
        / profile
        / "Library"
        / "Application Support"
        / "Antigravity"
        / "User"
        / "globalStorage"
        / "state.vscdb"
    )
    vscdb_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(vscdb_path))
    con.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT);")
    con.execute(
        "INSERT INTO ItemTable (key, value) VALUES (?, ?);",
        (
            "antigravityAuthStatus",
            json.dumps(
                {
                    "email": f"{profile}.verified@workspace.dev",
                    "apiKey": "secret-vscdb-key",
                }
            ),
        ),
    )
    con.commit()
    con.close()

    assert (
        agy_quota.read_antigravity_vscdb_email(profile)
        == f"{profile}.verified@workspace.dev"
    )

    usage_stdout = json.dumps(
        {
            "command": {
                "data": {
                    "groups": groups,
                    **({"plan_name": plan_name} if plan_name else {}),
                }
            }
        }
    )

    def fake_run(cmd: list[str], **_kw: Any) -> MagicMock:
        if cmd and cmd[0] == "security":
            return MagicMock(returncode=0, stdout="", stderr="")
        if len(cmd) >= 2 and cmd[1] == "models":
            return MagicMock(returncode=0, stdout="", stderr="")
        if "/usage" in cmd:
            return MagicMock(returncode=0, stdout=usage_stdout, stderr="")
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    live_res = agy_quota.fetch_quota_for_profile(profile)
    assert live_res["success"] is True
    assert live_res["tier"] == expected_tier

    formatted = agy_quota.format_profile_for_dashboard(profile, live_res)
    assert formatted["tier"] == expected_tier
    assert formatted["planLabel"] == expected_tier
    assert formatted["vendorLabel"] == "GOOGLE"
    assert formatted["priority"] == expected_priority
    assert formatted["email"] == f"{profile}.verified@workspace.dev"
    assert formatted["argonWeekly"]["name"] == expected_argon_name
    assert formatted["accountMeta"]["provider"] == "antigravity"
    assert formatted["accountMeta"]["vendorLabel"] == "GOOGLE"
    assert formatted["accountMeta"]["cliCommand"] == f"{profile}-cli"
    assert formatted["accountMeta"]["configPath"] == f"~/antigravity_homes/{profile}"
    _assert_zero_secret_leakage(
        formatted,
        ["ya29.secret_agy_access", "1//secret_agy_refresh", "secret-vscdb-key"],
    )


def test_antigravity_disabled_preservation_and_ultra_ping_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preserve cached ULTRA tier/priority/accountMeta on DISABLED/AUTH NEEDED and allow ULTRA 5H ping fallback."""
    cached_ultra = {
        "nguyenhieu000690": {
            "email": "nguyenhieu000690@gmail.com",
            "tier": "ULTRA",
            "planLabel": "ULTRA",
            "vendorLabel": "GOOGLE",
            "priority": 80,
            "status": "ACTIVE",
            "hasArgon": True,
            "capabilities": {
                "tier": "ULTRA",
                "hasCarbon": True,
                "hasArgon": True,
                "argonMode": "shared_gemini",
                "hasOrchestrator": True,
                "badges": ["ULTRA", "Carbon", "Argon", "Orchestrator"],
            },
            "accountMeta": {
                "provider": "antigravity",
                "vendorLabel": "GOOGLE",
                "planType": "ultra",
                "planLabel": "ULTRA",
                "cliCommand": "nguyenhieu000690-cli",
                "configPath": "~/antigravity_homes/nguyenhieu000690",
            },
            "gemini5h": {
                "name": "Gemini 3.8 / Pro 5H",
                "fraction": 1.0,
                "resetTime": "",
            },
            "claude5h": {
                "name": "Claude 5.5 / GPT 5H",
                "fraction": 1.0,
                "resetTime": "",
            },
        }
    }
    _setup_isolated_env(
        tmp_path, monkeypatch, ["nguyenhieu000690"], initial_cache=cached_ultra
    )
    monkeypatch.setattr(
        agy_quota, "check_profile_appeal_status", lambda *_a, **_kw: None
    )

    disabled = agy_quota.format_profile_for_dashboard(
        "nguyenhieu000690", {"success": False, "status": "DISABLED", "is_appeal": True}
    )
    assert disabled["status"] == "DISABLED"
    assert disabled["tier"] == "ULTRA"
    assert disabled["planLabel"] == "ULTRA"
    assert disabled["vendorLabel"] == "GOOGLE"
    assert disabled["priority"] == 80
    assert disabled["accountMeta"]["planLabel"] == "ULTRA"

    auth_needed = agy_quota.format_profile_for_dashboard(
        "nguyenhieu000690", {"success": False, "error": "OAuth expired"}
    )
    assert auth_needed["status"] == "AUTH NEEDED"
    assert auth_needed["tier"] == "ULTRA"
    assert auth_needed["priority"] == 80
    assert auth_needed["accountMeta"]["planLabel"] == "ULTRA"

    # Transient live /usage failure with cached ULTRA entry omitting `unavailable` on 5H buckets
    monkeypatch.setattr(
        agy_quota,
        "fetch_quota_for_profile",
        lambda p, *_a, **_kw: {
            "profile": p,
            "success": False,
            "error": "network timeout",
        },
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_a, **_kw: MagicMock(returncode=0, stdout="OK", stderr=""),
    )
    monkeypatch.setattr(agy_quota, "update_cached_profile", lambda *_a, **_kw: None)

    ping_res = agy_quota.execute_ping_profile("nguyenhieu000690", force=True)
    assert ping_res["success"] is True
    assert ping_res["pinged_gemini"] is True
    assert ping_res["pinged_claude"] is True
    assert ping_res["pinged_argon"] is False


@pytest.mark.parametrize(
    ("oauth_hints", "oauth_acc", "expected_tier", "expected_priority"),
    [
        (
            {"subscriptionType": "max", "rateLimitTier": "default_claude_max_20x"},
            {"emailAddress": "max20@example.com"},
            "CLAUDE MAX 20X",
            110,
        ),
        (
            {"subscriptionType": "max", "rateLimitTier": "default_claude_max_5x"},
            {"emailAddress": "max5@example.com"},
            "CLAUDE MAX 5X",
            105,
        ),
        (
            {"subscriptionType": "max"},
            {"emailAddress": "max@example.com"},
            "CLAUDE MAX",
            105,
        ),
        (
            {},
            {
                "emailAddress": "ent@example.com",
                "organizationType": "claude_enterprise",
            },
            "CLAUDE ENTERPRISE",
            105,
        ),
        (
            {},
            {"emailAddress": "team@example.com", "organizationType": "claude_team"},
            "CLAUDE TEAM",
            102,
        ),
        (
            {"subscriptionType": "pro"},
            {
                "emailAddress": "pro@example.com",
                "organizationType": "claude_pro",
                "organizationName": "Acme AI Lab",
                "billingType": "stripe_subscription",
            },
            "CLAUDE PRO",
            100,
        ),
        (
            {},
            {
                "emailAddress": "api@example.com",
                "billingType": "prepaid_api",
                "organizationType": "api",
            },
            "CLAUDE API",
            98,
        ),
        (
            {"subscriptionType": "free"},
            {"emailAddress": "free@example.com"},
            "CLAUDE FREE",
            40,
        ),
    ],
)
def test_claude_tier_and_priority_matrix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    oauth_hints: dict[str, Any],
    oauth_acc: dict[str, Any],
    expected_tier: str,
    expected_priority: int,
) -> None:
    """Verify Claude tier normalization, priorities, organization metadata, and zero token leakage."""
    _setup_isolated_env(tmp_path, monkeypatch)

    norm = agy_quota.normalize_claude_account(
        oauth_hints,
        oauth_acc,
        {
            "extra_usage": {
                "is_enabled": True,
                "used_credits": 12.5,
                "monthly_limit": 100,
            }
        },
        is_live=True,
    )
    assert norm["tier"] == expected_tier
    assert norm["planLabel"] == expected_tier
    assert norm["vendorLabel"] == "ANTHROPIC"
    assert norm["priority"] == expected_priority
    assert (
        isinstance(norm["availableModels"], list) and len(norm["availableModels"]) >= 2
    )
    if oauth_acc.get("organizationName"):
        assert norm["accountMeta"]["organizationName"] == "Acme AI Lab"

    # End-to-end fetch_claude_quota integration with credentials file containing secret tokens
    cred_dir = tmp_path / ".claude"
    cred_dir.mkdir(parents=True, exist_ok=True)
    (cred_dir / ".credentials.json").write_text(
        json.dumps(
            {
                "claudeAiOauth": {
                    "accessToken": "sk-ant-oat01-SUPER-SECRET-TOKEN",
                    "refreshToken": "sk-ant-ort01-SUPER-SECRET-REFRESH",
                    **oauth_hints,
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / ".claude.json").write_text(
        json.dumps({"oauthAccount": oauth_acc}),
        encoding="utf-8",
    )

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(
        {
            "five_hour": {"utilization": 20, "resets_at": "2026-11-18T10:00:00Z"},
            "seven_day": {"utilization": 45, "resets_at": "2026-11-24T00:00:00Z"},
        }
    ).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_a, **_kw: MagicMock(returncode=44, stdout="", stderr=""),
    )
    monkeypatch.setattr(
        agy_quota.urllib.request, "urlopen", lambda *_a, **_kw: mock_resp
    )

    full_claude = agy_quota.fetch_claude_quota()
    assert full_claude["tier"] == expected_tier
    assert full_claude["planLabel"] == expected_tier
    assert full_claude["vendorLabel"] == "ANTHROPIC"
    assert full_claude["priority"] == expected_priority
    _assert_zero_secret_leakage(
        full_claude,
        ["sk-ant-oat01-SUPER-SECRET-TOKEN", "sk-ant-ort01-SUPER-SECRET-REFRESH"],
    )


@pytest.mark.parametrize(
    ("api_data", "auth_data", "expected_tier", "expected_priority", "expected_models"),
    [
        ({"plan_type": "pro", "email": "pro@openai.com"}, {}, "CHATGPT PRO", 98, []),
        (
            {"plan_type": "enterprise", "email": "ent@openai.com"},
            {},
            "CHATGPT ENTERPRISE",
            98,
            [],
        ),
        ({"plan_type": "team", "email": "team@openai.com"}, {}, "CHATGPT TEAM", 96, []),
        ({"plan_type": "edu", "email": "edu@openai.com"}, {}, "CHATGPT EDU", 96, []),
        (
            {
                "plan_type": "plus",
                "email": "plus@openai.com",
                "model_usage": {
                    "gpt-6-astra": {"available": True},
                    "o4-retired": {"available": False},
                },
            },
            {},
            "CHATGPT PLUS",
            95,
            ["gpt-6-astra"],
        ),
        (
            {},
            {"auth_mode": "apikey", "OPENAI_API_KEY": "sk-proj-secret"},
            "OPENAI API",
            92,
            [],
        ),
        ({"plan_type": "free", "email": "free@openai.com"}, {}, "CHATGPT FREE", 35, []),
    ],
)
def test_codex_online_and_offline_jwt_tier_matrix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    api_data: dict[str, Any],
    auth_data: dict[str, Any],
    expected_tier: str,
    expected_priority: int,
    expected_models: list[str],
) -> None:
    """Verify Codex online wham/usage tiers, model_usage extraction, and offline JWT decoding."""
    _setup_isolated_env(tmp_path, monkeypatch)

    norm = agy_quota.normalize_codex_account(api_data, auth_data)
    assert norm["tier"] == expected_tier
    assert norm["planLabel"] == expected_tier
    assert norm["vendorLabel"] == "OPENAI"
    assert norm["priority"] == expected_priority
    assert norm["availableModels"] == expected_models
    _assert_zero_secret_leakage(norm, ["sk-proj-secret"])

    # Offline fallback with synthetic base64url JWT in ~/.codex/auth.json
    synthetic_jwt = _make_jwt(
        {
            "email": "dev@example.com",
            "https://api.openai.com/auth": {"chatgpt_plan_type": "pro"},
        }
    )
    codex_dir = tmp_path / ".codex"
    codex_dir.mkdir(parents=True, exist_ok=True)
    (codex_dir / "auth.json").write_text(
        json.dumps(
            {
                "tokens": {
                    "id_token": synthetic_jwt,
                    "refresh_token": "rt_secret_codex_refresh",
                }
            }
        ),
        encoding="utf-8",
    )

    def forbid_network(*_a: Any, **_kw: Any) -> Any:
        raise AssertionError("Offline JWT fallback must not perform network calls")

    monkeypatch.setattr(agy_quota.urllib.request, "urlopen", forbid_network)

    offline_res = agy_quota.fetch_codex_quota()
    assert offline_res["email"] == "dev@example.com"
    assert offline_res["tier"] == "CHATGPT PRO"
    assert offline_res["planLabel"] == "CHATGPT PRO"
    assert offline_res["vendorLabel"] == "OPENAI"
    assert offline_res["priority"] == 98
    assert offline_res["accountMeta"]["cliCommand"] == "codex"
    assert offline_res["accountMeta"]["configPath"] == "~/.codex/auth.json"
    _assert_zero_secret_leakage(offline_res, [synthetic_jwt, "rt_secret_codex_refresh"])


@pytest.mark.parametrize(
    ("title", "sub_type", "limit", "expected_tier", "expected_priority"),
    [
        ("KIRO POWER", "Q_DEVELOPER_STANDALONE_POWER", 10000.0, "KIRO POWER", 94),
        ("KIRO PRO+", "Q_DEVELOPER_STANDALONE_PRO_PLUS", 2000.0, "KIRO PRO+", 92),
        ("KIRO PRO", "Q_DEVELOPER_STANDALONE_PRO", 1000.0, "KIRO PRO", 90),
        ("KIRO STUDENT", "Q_DEVELOPER_STANDALONE_STUDENT", 1000.0, "KIRO STUDENT", 90),
        ("KIRO FREE", "Q_DEVELOPER_STANDALONE_FREE", 50.0, "KIRO FREE", 30),
    ],
)
def test_kiro_tier_matrix_and_offline_cache_preservation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    title: str,
    sub_type: str,
    limit: float,
    expected_tier: str,
    expected_priority: int,
) -> None:
    """Verify Kiro tier priorities (94/92/90/30) and offline cache preservation."""
    cached_kiro = {
        "kiro": {
            "profile": "kiro",
            "tier": "KIRO STUDENT",
            "planLabel": "KIRO STUDENT",
            "vendorLabel": "KIRO",
            "priority": 90,
            "email": "Elenor.Zulaufell001@mymdc.net",
            "status": "ACTIVE",
            "isCreditOnly": True,
            "creditsPool": {
                "name": "Monthly Credits Pool",
                "used": 988.32,
                "limit": 1000.0,
                "remaining": 11.68,
                "fraction": 0.01168,
                "countdown": "⏱ 12d 04h (01/12)",
                "resetDate": "01/12",
                "unavailable": False,
            },
        }
    }
    _setup_isolated_env(tmp_path, monkeypatch, initial_cache=cached_kiro)

    api_data = {
        "nextDateReset": 1796083200.0,
        "overageConfiguration": {"overageStatus": "DISABLED"},
        "subscriptionInfo": {"subscriptionTitle": title, "type": sub_type},
        "usageBreakdownList": [
            {
                "currentUsageWithPrecision": 10.0,
                "usageLimitWithPrecision": limit,
                "overageRate": 0.04,
                "currency": "USD",
                "bonuses": [{"usageLimit": 100.0}],
            }
        ],
    }
    parsed = agy_quota.parse_kiro_usage_limits(api_data, email="user@kiro.dev")
    assert parsed["tier"] == expected_tier
    assert parsed["planLabel"] == expected_tier
    assert parsed["vendorLabel"] == "KIRO"
    assert parsed["priority"] == expected_priority
    assert parsed["accountMeta"]["cliCommand"] == "kiro-cli"

    # Offline API failure preserves cached tier, email, and creditsPool
    monkeypatch.setattr(
        agy_quota, "get_kiro_bin_path", lambda: "/usr/local/bin/kiro-cli"
    )
    whoami_ok = MagicMock(
        returncode=0,
        stdout="Logged in with Builder ID\nEmail: Elenor.Zulaufell001@mymdc.net\n",
        stderr="",
    )
    kas_ok = MagicMock(
        returncode=0,
        stdout=json.dumps(
            {
                "data": {
                    "accessToken": "kas-super-secret-token",
                    "profileArn": "arn:aws:codewhisperer:us-east-1:12345:profile/STUDENT",
                }
            }
        ),
        stderr="",
    )
    monkeypatch.setattr(subprocess, "run", MagicMock(side_effect=[whoami_ok, kas_ok]))
    monkeypatch.setattr(
        agy_quota.urllib.request,
        "urlopen",
        MagicMock(side_effect=OSError("network unreachable")),
    )

    offline_kiro = agy_quota.fetch_kiro_quota()
    assert offline_kiro["tier"] == "KIRO STUDENT"
    assert offline_kiro["priority"] == 90
    assert offline_kiro["email"] == "Elenor.Zulaufell001@mymdc.net"
    assert offline_kiro["creditsPool"]["used"] == pytest.approx(988.32)
    assert offline_kiro["creditsPool"]["limit"] == pytest.approx(1000.0)
    _assert_zero_secret_leakage(offline_kiro, ["kas-super-secret-token"])


def test_types_file_declares_account_meta_and_daemon_mtime_sync(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify AccountMeta TypeScript contract, dynamic CLI priority tag, and daemon mtime reload."""
    ts_source = TYPES_FILE.read_text(encoding="utf-8")
    assert "export interface AccountMeta" in ts_source
    assert "accountMeta?: AccountMeta;" in ts_source
    assert "planLabel?: string;" in ts_source
    assert "vendorLabel?: string;" in ts_source

    assert "Priority: 80" in agy_quota.format_priority_tag(80)
    assert "Priority: 110" in agy_quota.format_priority_tag(110)

    # Verify /api/status exposes server_code_mtime and external HTML mtime reloads cache
    dash_html = _setup_isolated_env(
        tmp_path,
        monkeypatch,
        initial_cache={
            "claude": {"status": "ACTIVE", "tier": "CLAUDE PRO", "priority": 100}
        },
    )
    monkeypatch.setattr(
        agy_quota,
        "fetch_codex_quota",
        lambda: {"status": "ACTIVE", "tier": "CHATGPT PLUS"},
    )
    monkeypatch.setattr(
        agy_quota,
        "fetch_kiro_quota",
        lambda: {"status": "ACTIVE", "tier": "KIRO STUDENT"},
    )

    loaded_v1 = agy_quota.load_cached_profiles()
    assert loaded_v1["claude"]["tier"] == "CLAUDE PRO"

    # Simulate external process updating quota_dashboard.html with newer mtime
    updated_cache = {
        "claude": {"status": "ACTIVE", "tier": "CLAUDE MAX 20X", "priority": 110},
        "codex": {"status": "ACTIVE", "tier": "CHATGPT PRO", "priority": 98},
        "kiro": {"status": "ACTIVE", "tier": "KIRO POWER", "priority": 94},
    }
    dash_html.write_text(
        "<html><script>\nconst PROFILES_DATA = "
        + json.dumps(updated_cache, indent=2)
        + ";\n</script></html>\n",
        encoding="utf-8",
    )
    import os as _os

    st = dash_html.stat()
    _os.utime(dash_html, (st.st_atime + 5, st.st_mtime + 5))

    loaded_v2 = agy_quota.load_cached_profiles()
    assert loaded_v2["claude"]["tier"] == "CLAUDE MAX 20X"

    # Verify /api/status payload includes server_code_mtime
    captured_status: list[dict[str, Any]] = []
    handler = MagicMock()
    handler.path = "/api/status"
    handler._safe_schedule_status.return_value = {"schedules": [], "by_profile": {}}
    handler.send_json.side_effect = lambda payload, status=200: captured_status.append(
        payload
    )
    agy_quota.QuotaDashboardHandler.do_GET(handler)
    assert len(captured_status) == 1
    assert captured_status[0]["server_code_mtime"] == agy_quota.SERVER_STARTUP_MTIME

    # Verify start_server_daemon restarts stale daemon when server_code_mtime mismatches
    alive_Sequence = iter([True, True])
    monkeypatch.setattr(
        agy_quota, "is_server_alive", lambda _port=8765: next(alive_Sequence, True)
    )
    monkeypatch.setattr(agy_quota, "PID_FILE", tmp_path / "quota.pid")
    monkeypatch.setattr(agy_quota, "LOG_FILE", tmp_path / "quota.log")

    stale_status_resp = MagicMock()
    stale_status_resp.status = 200
    stale_status_resp.read.return_value = json.dumps(
        {"server_code_mtime": 12345}
    ).encode("utf-8")
    stale_status_resp.__enter__.return_value = stale_status_resp
    monkeypatch.setattr(
        agy_quota.urllib.request, "urlopen", lambda *_a, **_kw: stale_status_resp
    )

    stopped_ports: list[int] = []
    monkeypatch.setattr(
        agy_quota, "stop_server", lambda p=8765: stopped_ports.append(p) or True
    )
    fake_proc = MagicMock(pid=42424, poll=lambda: None)
    monkeypatch.setattr(subprocess, "Popen", lambda *_a, **_kw: fake_proc)

    agy_quota.start_server_daemon(port=18765, auto_open=False)
    assert stopped_ports == [18765]

    # Verify CLI cards render dynamic priority and Carbon & Argon Weekly title
    import io
    import socketserver

    buf = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    agy_quota.print_dashboard_cards(
        {
            "profile": "nguyenhieu000690",
            "success": True,
            "tier": "ULTRA",
            "priority": 80,
            "argonMode": "shared_gemini",
            "capabilities": {
                "tier": "ULTRA",
                "hasCarbon": True,
                "hasArgon": True,
                "argonMode": "shared_gemini",
                "hasOrchestrator": True,
            },
            "groups": [
                {
                    "name": "Gemini Models",
                    "description": "Models within this group: Gemini 4 Carbon, Gemini 4 Argon",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 0.9,
                            "reset_time": "2026-11-18T10:00:00Z",
                        },
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.85,
                            "reset_time": "2026-11-24T00:00:00Z",
                        },
                    ],
                }
            ],
        }
    )
    agy_quota.print_claude_card(
        {"tier": "CLAUDE MAX 20X", "priority": 110, "status": "ACTIVE"}
    )
    agy_quota.print_codex_card(
        {"tier": "CHATGPT PRO", "priority": 98, "status": "ACTIVE"}
    )
    agy_quota.print_kiro_card(
        {"tier": "KIRO POWER", "priority": 94, "status": "ACTIVE"}
    )
    cli_out = buf.getvalue()
    assert "Priority: 80" in cli_out
    assert "Gemini 4 Carbon & Argon Weekly (Shared Gemini)" in cli_out
    assert "Priority: 110" in cli_out
    assert "Priority: 98" in cli_out
    assert "Priority: 94" in cli_out

    # Verify active _serve hot-reload schedules server.shutdown when agy_quota.py mtime changes
    shutdown_called: list[bool] = []

    class _DummyServer(socketserver.BaseServer):
        def __init__(self) -> None:
            pass

        def shutdown(self) -> None:
            shutdown_called.append(True)

    monkeypatch.setattr(agy_quota, "_RELOAD_PENDING", False)
    monkeypatch.setattr(agy_quota, "SERVER_STARTUP_MTIME", 1)
    agy_quota._check_and_schedule_hot_reload(_DummyServer())
    # Give background daemon thread a brief tick if needed
    for _ in range(20):
        if shutdown_called:
            break
    assert agy_quota._RELOAD_PENDING is True
    assert shutdown_called == [True]


def _build_dynamic_4provider_profiles() -> dict[str, dict[str, Any]]:
    """Build realistic 4-provider + Antigravity tier fixtures using Task 1 normalizers."""
    claude_norm = agy_quota.normalize_claude_account(
        {"subscriptionType": "pro", "rateLimitTier": "default_claude_pro"},
        {
            "emailAddress": "danhdue@anthropic.dev",
            "organizationType": "claude_pro",
            "organizationName": "Acme AI Lab",
            "billingType": "stripe_subscription",
        },
        {
            "extra_usage": {
                "is_enabled": True,
                "used_credits": 12.5,
                "monthly_limit": 100.0,
            }
        },
        is_live=True,
    )
    claude_entry: dict[str, Any] = {
        "profile": "claude",
        "displayName": "Claude Code",
        "isProvider": True,
        "providerType": "claude",
        "email": "danhdue@anthropic.dev",
        "status": "ACTIVE",
        **claude_norm,
        "gemini5h": {
            "name": "Claude 5H Session Window",
            "fraction": 0.78,
            "countdown": "⏱ 3h 40m",
            "unavailable": False,
        },
        "geminiWeekly": {
            "name": "Claude 7D Weekly Remaining",
            "fraction": 0.64,
            "countdown": "⏱ 4d 12h",
            "unavailable": False,
        },
        "quotaBuckets": [
            {
                "id": "session",
                "name": "Claude 5H Session Window",
                "group": "session",
                "kind": "session",
                "scopeLabel": "",
                "fraction": 0.78,
                "utilization": 22.0,
                "countdown": "⏱ 3h 40m",
                "unavailable": False,
            },
            {
                "id": "weekly_all",
                "name": "Claude 7D Weekly Remaining",
                "group": "weekly",
                "kind": "weekly_all",
                "scopeLabel": "",
                "fraction": 0.64,
                "utilization": 36.0,
                "countdown": "⏱ 4d 12h",
                "unavailable": False,
            },
        ],
    }

    codex_norm = agy_quota.normalize_codex_account(
        {
            "plan_type": "plus",
            "email": "danhdue@openai.dev",
            "rate_limit_reset_credits": {"available_count": 1},
            "model_usage": {"gpt-6-astra": {"available": True}},
        },
        {},
    )
    codex_entry: dict[str, Any] = {
        "profile": "codex",
        "displayName": "OpenAI Codex",
        "isProvider": True,
        "providerType": "codex",
        "email": "danhdue@openai.dev",
        "status": "ACTIVE",
        **codex_norm,
        "gemini5h": {
            "name": "Codex 5-Hour Limit",
            "fraction": 0.88,
            "countdown": "⏱ 4h 15m",
            "unavailable": False,
        },
        "geminiWeekly": {
            "name": "Codex Weekly Limit",
            "fraction": 0.72,
            "countdown": "⏱ 5d 02h",
            "unavailable": False,
        },
    }

    kiro_parsed = agy_quota.parse_kiro_usage_limits(
        {
            "nextDateReset": 1796083200.0,
            "overageConfiguration": {"overageStatus": "DISABLED"},
            "subscriptionInfo": {
                "subscriptionTitle": "KIRO STUDENT",
                "type": "Q_DEVELOPER_STANDALONE_STUDENT",
            },
            "usageBreakdownList": [
                {
                    "currentUsageWithPrecision": 18.5,
                    "usageLimitWithPrecision": 1000.0,
                    "currency": "USD",
                }
            ],
        },
        email="student@kiro.dev",
    )
    kiro_entry: dict[str, Any] = {
        "profile": "kiro",
        "displayName": "Kiro CLI",
        "isProvider": True,
        "providerType": "kiro",
        "isCreditOnly": True,
        "status": "ACTIVE",
        **kiro_parsed,
    }

    ultra_groups = [
        {
            "name": "Gemini Models",
            "description": (
                "Models within this group: Gemini 4 Carbon, Gemini 4 Argon, "
                "Gemini 4 Hydrogen, Orchestrator (Carbon), Orchestrator (Argon), Gemini 3.8 Flash"
            ),
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 0.90,
                    "reset_time": "2026-11-18T10:00:00Z",
                },
                {
                    "window": "weekly",
                    "remaining_fraction": 0.85,
                    "reset_time": "2026-11-24T00:00:00Z",
                },
            ],
        },
        {
            "name": "Claude and GPT models",
            "description": "Models within this group: Claude Sonnet 4.6, Claude Opus 4.6, GPT-OSS 120B",
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 0.92,
                    "reset_time": "2026-11-18T10:00:00Z",
                },
                {
                    "window": "weekly",
                    "remaining_fraction": 0.88,
                    "reset_time": "2026-11-24T00:00:00Z",
                },
            ],
        },
    ]
    ultra_parsed = agy_quota.parse_usage_group_models(ultra_groups)
    ultra_catalog = agy_quota.parse_agy_models_catalog(
        "\n".join(
            [
                "gemini-4-carbon-high",
                "gemini-4-argon-high",
                "gemini-pro-orchestrator",
                "gemini-pro-orchestrator-argon",
            ]
        )
    )
    nguyenhieu_entry = agy_quota.format_profile_for_dashboard(
        "nguyenhieu000690",
        {
            "success": True,
            "email": "nguyenhieu000690@gmail.com",
            "plan_name": "Google AI Ultra",
            "groups": ultra_groups,
            "items": agy_quota.parse_quota_items(ultra_groups),
            "groupModels": ultra_parsed["groupModels"],
            "groupDescSig": ultra_parsed["groupDescSig"],
            "availableModels": [
                "gemini-4-carbon-high",
                "gemini-4-argon-high",
                "gemini-pro-orchestrator",
                "gemini-pro-orchestrator-argon",
            ],
            "modelCatalog": ultra_catalog,
            "modelsFetchedAt": "2026-11-18T00:00:00Z",
        },
    )

    pro_argon_groups = [
        {
            "name": "Gemini Models",
            "description": "Models within this group: Gemini 4 Hydrogen, Gemini 3.8 Flash",
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 1.0,
                    "reset_time": "2026-11-18T10:00:00Z",
                },
                {
                    "window": "weekly",
                    "remaining_fraction": 1.0,
                    "reset_time": "2026-11-24T00:00:00Z",
                },
            ],
        },
        {
            "name": "Claude and GPT models",
            "description": "Models within this group: Claude Opus 4.6, Claude Sonnet 4.6, GPT-OSS 120B",
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 0.85,
                    "reset_time": "2026-11-18T10:00:00Z",
                },
                {
                    "window": "weekly",
                    "remaining_fraction": 0.80,
                    "reset_time": "2026-11-24T00:00:00Z",
                },
            ],
        },
        {
            "name": "Gemini 4 Argon",
            "description": (
                "For paid Pro plans, Argon quota is separate. Higher Argon quota "
                "(included as part of the larger Gemini quota bucket) is available on Ultra plans."
            ),
            "buckets": [
                {
                    "window": "weekly",
                    "remaining_fraction": 1.0,
                    "reset_time": "2026-11-24T00:00:00Z",
                }
            ],
        },
    ]
    pro_argon_parsed = agy_quota.parse_usage_group_models(pro_argon_groups)
    pro_argon_models = agy_quota._reconcile_group_models(pro_argon_parsed, [])
    danhdue_entry = agy_quota.format_profile_for_dashboard(
        "danhdue",
        {
            "success": True,
            "email": "danhdue@gmail.com",
            "plan_name": "Google AI Pro",
            "groups": pro_argon_groups,
            "items": agy_quota.parse_quota_items(pro_argon_groups),
            "groupModels": pro_argon_models,
            "groupDescSig": pro_argon_parsed["groupDescSig"],
            "availableModels": ["gemini-4-hydrogen-high", "gemini-4-argon-high"],
            "modelCatalog": agy_quota.parse_agy_models_catalog(
                "gemini-4-hydrogen-high\ngemini-4-argon-high"
            ),
            "modelsFetchedAt": "2026-11-18T01:00:00Z",
        },
    )

    pro_plain_groups = [
        {
            "name": "Gemini Models",
            "description": "Models within this group: Gemini 4 Hydrogen, Gemini 3.8 Flash",
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 1.0,
                    "reset_time": "2026-11-18T10:00:00Z",
                },
                {
                    "window": "weekly",
                    "remaining_fraction": 0.92,
                    "reset_time": "2026-11-24T00:00:00Z",
                },
            ],
        },
        {
            "name": "Claude and GPT models",
            "description": "Models within this group: Claude Sonnet 4.6, GPT-OSS 120B",
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 1.0,
                    "reset_time": "2026-11-18T10:00:00Z",
                },
                {
                    "window": "weekly",
                    "remaining_fraction": 0.90,
                    "reset_time": "2026-11-24T00:00:00Z",
                },
            ],
        },
    ]
    pro_plain_parsed = agy_quota.parse_usage_group_models(pro_plain_groups)
    d3molt_entry = agy_quota.format_profile_for_dashboard(
        "d3molt",
        {
            "success": True,
            "email": "d3molt@gmail.com",
            "plan_name": "Google AI Pro",
            "groups": pro_plain_groups,
            "items": agy_quota.parse_quota_items(pro_plain_groups),
            "groupModels": pro_plain_parsed["groupModels"],
            "groupDescSig": pro_plain_parsed["groupDescSig"],
            "modelsFetchedAt": "2026-11-18T01:30:00Z",
        },
    )

    free_groups = [
        {
            "name": "Gemini Models",
            "description": "Models within this group: Gemini 3.8 Flash",
            "buckets": [
                {
                    "window": "weekly",
                    "remaining_fraction": 0.70,
                    "reset_time": "2026-11-24T00:00:00Z",
                }
            ],
        },
        {
            "name": "Claude and GPT models",
            "description": "Models within this group: Claude Sonnet 4.6",
            "buckets": [
                {
                    "window": "weekly",
                    "remaining_fraction": 0.60,
                    "reset_time": "2026-11-24T00:00:00Z",
                }
            ],
        },
    ]
    free_parsed = agy_quota.parse_usage_group_models(free_groups)
    buivantrong_entry = agy_quota.format_profile_for_dashboard(
        "buivantrong8901",
        {
            "success": True,
            "email": "buivantrong8901@gmail.com",
            "plan_name": "",
            "groups": free_groups,
            "items": agy_quota.parse_quota_items(free_groups),
            "groupModels": free_parsed["groupModels"],
            "groupDescSig": free_parsed["groupDescSig"],
            "modelsFetchedAt": "2026-11-18T02:00:00Z",
        },
    )

    # Deliberately insert keys in unsorted order so DEFAULT sort must reorder them
    return {
        "buivantrong8901": buivantrong_entry,
        "d3molt": d3molt_entry,
        "kiro": kiro_entry,
        "danhdue": danhdue_entry,
        "codex": codex_entry,
        "nguyenhieu000690": nguyenhieu_entry,
        "claude": claude_entry,
    }


def test_quota_dashboard_ui_4provider_headers_modal_sort_and_search() -> None:
    """Verify 4-provider dynamic headers, Ultra Carbon+Argon row, DEFAULT priority sort, modal, and search in Node VM."""
    node_bin = shutil.which("node")
    if node_bin is None:
        pytest.skip("Node.js binary is required for quota_dashboard.html VM harness")

    profiles_fixture = _build_dynamic_4provider_profiles()
    script = r"""
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const html = fs.readFileSync(__HTML_PATH__, 'utf8');
const scriptMatches = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(scriptMatches.length, 1, 'Expected single inline <script>');
const quotaScript = scriptMatches[0][1];

// Ensure modal HTML contains the required wrapper IDs
for (const modalWrapperId of [
  'infoModalEmailLabel',
  'infoModalArgonMetaRow',
  'infoModalGeminiGroupLabel',
  'infoModalClaudeModelsRow',
  'infoModalArgonModelsRow',
  'infoModalHomeLabel',
  'infoModalKeychainRow',
]) {
  assert.ok(html.includes(`id="${modalWrapperId}"`), `Missing wrapper id="${modalWrapperId}" in quota_dashboard.html`);
}

function createClassList(initial = []) {
  const classes = new Set(initial);
  return {
    add(...items) { items.forEach((c) => classes.add(c)); },
    remove(...items) { items.forEach((c) => classes.delete(c)); },
    contains(c) { return classes.has(c); },
    toggle(c, f) {
      if (f === true) { classes.add(c); return true; }
      if (f === false) { classes.delete(c); return false; }
      return classes.has(c) ? (classes.delete(c), false) : (classes.add(c), true);
    },
    toString() { return [...classes].join(' '); },
  };
}

class FakeElement {
  constructor(tag = 'div', id = '', initialClasses = []) {
    this.tagName = tag.toUpperCase();
    this.id = id;
    this.dataset = {};
    this.style = { display: '', overflow: '' };
    this.classList = createClassList(initialClasses);
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
for (const id of [
  'profilesGrid', 'gridCol1', 'gridCol2', 'searchInput', 'statusFilter', 'sortOrderSelect',
  'statActive', 'statDisabled', 'statAuth', 'statExhausted', 'statProviders', 'statProfiles', 'statArgon',
  'profileInfoModal', 'profile-info-modal', 'scheduleModal', 'loginModal', 'appealDetailModal',
  'infoModalProfile', 'infoModalEmailLabel', 'infoModalEmail', 'infoModalStatus', 'infoModalTier',
  'infoModalBadges', 'infoModalArgonMetaRow', 'infoModalArgonMode', 'infoModalModelsFetchedAt',
  'infoModalGroupDescSig', 'infoModalGeminiGroupLabel', 'infoModalGeminiModels',
  'infoModalClaudeModelsRow', 'infoModalClaudeModels', 'infoModalArgonModelsRow', 'infoModalArgonModels',
  'infoModalCliCmd', 'infoModalHomeLabel', 'infoModalHomePath', 'infoModalKeychainRow', 'infoModalKeychainPath',
  'copyEmailText', 'copyCliText',
]) {
  const initCls = ['profileInfoModal', 'scheduleModal', 'loginModal', 'appealDetailModal'].includes(id)
    ? ['hidden']
    : [];
  byId.set(id, new FakeElement('div', id, initCls));
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
  innerWidth: 1440,
  innerHeight: 1000,
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

assert.equal(typeof sandbox.getProviderHeaderBadgesHTML, 'function', 'getProviderHeaderBadgesHTML must exist');
assert.equal(typeof sandbox.getProviderPlanBadgeHTML, 'function', 'getProviderPlanBadgeHTML must exist');
assert.equal(typeof sandbox.getCarbonArgonOrchestratorModels, 'function', 'getCarbonArgonOrchestratorModels must exist');

const fixture = __FIXTURE_JSON__;
vm.runInContext(`Object.keys(PROFILES_DATA).forEach(k => delete PROFILES_DATA[k]); Object.assign(PROFILES_DATA, ${JSON.stringify(fixture)});`, sandbox);

// 1. Provider cards render vendor pill, dynamic plan badge, dynamic priority, info modal button, subtitles, and clean reset credit tooltip
const claudeCard = sandbox.renderProfileCard('claude', fixture.claude);
assert.ok(claudeCard.includes('ANTHROPIC'), 'Claude card must show ANTHROPIC vendor pill');
assert.ok(claudeCard.includes('data-tier-badge="CLAUDE PRO"'), 'Claude card must show CLAUDE PRO plan badge');
assert.ok(claudeCard.includes('Priority: 100'), 'Claude card must show Priority: 100');
assert.ok(claudeCard.includes("openProfileInfoModal('claude')"), 'Claude card must render ℹ info modal button');
assert.ok(claudeCard.includes('Extra usage: 12.5 / 100.0'), 'Claude card must render extraUsageSummary subtitle');

const claudeMaxCard = sandbox.renderProfileCard('claude', {
  ...fixture.claude,
  tier: 'CLAUDE MAX 20X',
  planLabel: 'CLAUDE MAX 20X',
  priority: 110,
});
assert.ok(claudeMaxCard.includes('data-tier-badge="CLAUDE MAX 20X"'));
assert.ok(claudeMaxCard.includes('Priority: 110'));

const codexCard = sandbox.renderProfileCard('codex', fixture.codex);
assert.ok(codexCard.includes('OPENAI'), 'Codex card must show OPENAI vendor pill');
assert.ok(codexCard.includes('data-tier-badge="CHATGPT PLUS"'), 'Codex card must show CHATGPT PLUS plan badge');
assert.ok(codexCard.includes('Priority: 95'), 'Codex card must show Priority: 95');
assert.ok(codexCard.includes("openProfileInfoModal('codex')"), 'Codex card must render ℹ info modal button');
assert.ok(codexCard.includes('Available models: gpt-6-astra'), 'Codex card must render dynamic model subtitle');
assert.ok(codexCard.includes('Có 1 vé Full Reset khả dụng'), 'Codex card must render reset credit tooltip');
assert.ok(!codexCard.includes('02/12'), 'Codex reset credit tooltip must NOT hardcode 02/12');

const codexProCard = sandbox.renderProfileCard('codex', {
  ...fixture.codex,
  tier: 'CHATGPT PRO',
  planLabel: 'CHATGPT PRO',
  priority: 98,
});
assert.ok(codexProCard.includes('data-tier-badge="CHATGPT PRO"'));
assert.ok(codexProCard.includes('Priority: 98'));

const kiroCard = sandbox.renderProfileCard('kiro', fixture.kiro);
assert.ok(kiroCard.includes('KIRO'), 'Kiro card must show KIRO vendor pill');
assert.ok(kiroCard.includes('data-tier-badge="KIRO STUDENT"'), 'Kiro card must show KIRO STUDENT plan badge');
assert.ok(kiroCard.includes('Priority: 90'), 'Kiro card must show Priority: 90');
assert.ok(kiroCard.includes("openProfileInfoModal('kiro')"), 'Kiro card must render ℹ info modal button');
assert.ok(kiroCard.includes('Used: 18.50 / 1,000.0 credits'), 'Kiro card must render creditsSummary');
assert.ok(kiroCard.includes('Overages: DISABLED'), 'Kiro card must render Overages status');

const kiroProPlusCard = sandbox.renderProfileCard('kiro', {
  ...fixture.kiro,
  tier: 'KIRO PRO+',
  planLabel: 'KIRO PRO+',
  priority: 92,
});
assert.ok(kiroProPlusCard.includes('data-tier-badge="KIRO PRO+"'));
assert.ok(kiroProPlusCard.includes('Priority: 92'));

// Legacy backward-compatibility fallback when planLabel & accountMeta are absent
const legacyClaude = sandbox.renderProfileCard('claude', {
  isProvider: true,
  tier: 'ANTHROPIC',
  status: 'ACTIVE',
  gemini5h: fixture.claude.gemini5h,
  geminiWeekly: fixture.claude.geminiWeekly,
});
assert.ok(legacyClaude.includes('ANTHROPIC') && legacyClaude.includes('CLAUDE PRO'));
const legacyCodex = sandbox.renderProfileCard('codex', {
  isProvider: true,
  tier: 'OPENAI',
  status: 'ACTIVE',
  gemini5h: fixture.codex.gemini5h,
  geminiWeekly: fixture.codex.geminiWeekly,
});
assert.ok(legacyCodex.includes('OPENAI') && legacyCodex.includes('CHATGPT PLUS'));
const legacyKiro = sandbox.renderProfileCard('kiro', {
  isProvider: true,
  tier: 'KIRO',
  isCreditOnly: true,
  status: 'ACTIVE',
  gemini5h: fixture.kiro.gemini5h,
});
assert.ok(legacyKiro.includes('KIRO') && legacyKiro.includes('KIRO STUDENT'));

// 2. Antigravity ULTRA profile renders ULTRA, Priority: 80, Carbon/Argon/Orchestrator, Gemini Weekly subtitle, and Gemini 4 Carbon & Argon Weekly shared row
const ultraModels = Array.from(sandbox.getCarbonArgonOrchestratorModels(fixture.nguyenhieu000690));
assert.ok(ultraModels.includes('Gemini 4 Carbon'), 'Carbon model must be in shared Ultra roster');
assert.ok(ultraModels.includes('Gemini 4 Argon'), 'Argon model must be in shared Ultra roster');
assert.ok(ultraModels.some((m) => m.includes('Orchestrator')), 'Orchestrator model must be in shared Ultra roster');

const ultraCard = sandbox.renderProfileCard('nguyenhieu000690', fixture.nguyenhieu000690);
assert.ok(ultraCard.includes('data-tier-badge="ULTRA"'), 'Ultra card must show ULTRA badge');
assert.ok(ultraCard.includes('Priority: 80'), 'Ultra card must show Priority: 80');
assert.ok(ultraCard.includes('data-capability-badge="Carbon"'), 'Ultra card must show Carbon badge');
assert.ok(ultraCard.includes('data-capability-badge="Argon"'), 'Ultra card must show Argon badge');
assert.ok(ultraCard.includes('data-capability-badge="Orchestrator"'), 'Ultra card must show Orchestrator badge');
assert.ok(ultraCard.includes('Gemini 4 Carbon &amp; Argon Weekly'), 'Ultra card Row 3 must be titled Gemini 4 Carbon & Argon Weekly');
assert.ok(ultraCard.includes('Shared w/ Gemini Pool'), 'Ultra card Row 3 must show Shared w/ Gemini Pool');
const rosterMatches = [...ultraCard.matchAll(/data-model-roster="true"/g)];
assert.ok(rosterMatches.length >= 4, `Expected roster subtitles on Gemini 5H, Claude 5H, Gemini Weekly, and Carbon+Argon Row 3 (got ${rosterMatches.length})`);
assert.ok(!ultraCard.toLowerCase().includes('models within this group'), 'Zero raw prefix leakage');

// 3. DEFAULT sort orders claude -> codex -> kiro, then satellites by priority DESC, A-Z tie-breaker
const orderedDefault = Array.from(sandbox.getOrderedProfiles());
assert.deepEqual(orderedDefault, [
  'claude',
  'codex',
  'kiro',
  'nguyenhieu000690',
  'danhdue',
  'd3molt',
  'buivantrong8901',
]);

// Verify A-Z tie-breaking within same priority (50) and NAME_ASC preservation
vm.runInContext(`PROFILES_DATA.alpha_pro = { ...PROFILES_DATA.d3molt, priority: 50 };`, sandbox);
const orderedTieBreak = Array.from(sandbox.getOrderedProfiles());
assert.equal(orderedTieBreak.indexOf('alpha_pro') + 1, orderedTieBreak.indexOf('d3molt'), 'Same priority ties must break A-Z');
vm.runInContext(`currentSortOrder = 'NAME_ASC';`, sandbox);
const orderedNameAsc = Array.from(sandbox.getOrderedProfiles());
assert.deepEqual(orderedNameAsc.slice(3), ['alpha_pro', 'buivantrong8901', 'd3molt', 'danhdue', 'nguyenhieu000690']);
vm.runInContext(`delete PROFILES_DATA.alpha_pro; currentSortOrder = 'DEFAULT';`, sandbox);

// Verify isProfileFreeTier handles both tier === 'FREE' and accountMeta.planType === 'free'
assert.equal(sandbox.isProfileFreeTier(fixture.buivantrong8901), true);
assert.equal(sandbox.isProfileFreeTier({ tier: 'CLAUDE FREE', accountMeta: { planType: 'free' } }), true);
assert.equal(sandbox.isProfileFreeTier(fixture.claude), false);

// 4. Provider-aware openProfileInfoModal & searchInput matching
sandbox.openProfileInfoModal('claude');
assert.equal(byId.get('infoModalEmailLabel').textContent, 'Tài khoản Provider (Email)');
assert.equal(byId.get('infoModalEmail').textContent, 'danhdue@anthropic.dev');
assert.ok(byId.get('infoModalTier').textContent.includes('CLAUDE PRO (Priority 100)'));
assert.ok(byId.get('infoModalTier').textContent.includes('Acme AI Lab'));
assert.equal(byId.get('infoModalCliCmd').textContent, 'claude');
assert.equal(byId.get('infoModalHomeLabel').textContent, 'Tệp cấu hình / Xác thực:');
assert.equal(byId.get('infoModalHomePath').textContent, '~/.claude.json');
assert.equal(byId.get('infoModalGeminiGroupLabel').textContent, 'Available Models & Quota Scopes');
assert.equal(byId.get('infoModalArgonMetaRow').classList.contains('hidden'), true);
assert.equal(byId.get('infoModalClaudeModelsRow').classList.contains('hidden'), true);
assert.equal(byId.get('infoModalArgonModelsRow').classList.contains('hidden'), true);
assert.equal(byId.get('infoModalKeychainRow').classList.contains('hidden'), true);

sandbox.openProfileInfoModal('codex');
assert.equal(byId.get('infoModalEmail').textContent, 'danhdue@openai.dev');
assert.ok(byId.get('infoModalTier').textContent.includes('CHATGPT PLUS (Priority 95)'));
assert.ok(byId.get('infoModalTier').textContent.includes('1 reset credits available'));
assert.equal(byId.get('infoModalCliCmd').textContent, 'codex');
assert.equal(byId.get('infoModalHomePath').textContent, '~/.codex/auth.json');
assert.ok(byId.get('infoModalGeminiModels').innerHTML.includes('gpt-6-astra'));
assert.equal(byId.get('infoModalKeychainRow').classList.contains('hidden'), true);

// Opening Antigravity profile restores Antigravity-only rows
sandbox.openProfileInfoModal('nguyenhieu000690');
assert.equal(byId.get('infoModalEmailLabel').textContent, 'Tài khoản Google (Email)');
assert.equal(byId.get('infoModalHomeLabel').textContent, 'Thư mục Home độc lập:');
assert.equal(byId.get('infoModalGeminiGroupLabel').textContent, 'Gemini Models');
assert.equal(byId.get('infoModalArgonMetaRow').classList.contains('hidden'), false);
assert.equal(byId.get('infoModalClaudeModelsRow').classList.contains('hidden'), false);
assert.equal(byId.get('infoModalArgonModelsRow').classList.contains('hidden'), false);
assert.equal(byId.get('infoModalKeychainRow').classList.contains('hidden'), false);

// Search matching for plan labels, tiers, organizationName, and availableModels
for (const [query, expectedId] of [
  ['chatgpt plus', 'card-codex'],
  ['claude pro', 'card-claude'],
  ['acme ai lab', 'card-claude'],
  ['ultra', 'card-nguyenhieu000690'],
  ['gpt-6-astra', 'card-codex'],
]) {
  byId.get('searchInput').value = query;
  sandbox.renderAllProfiles();
  const combinedHTML = byId.get('gridCol1').innerHTML + byId.get('gridCol2').innerHTML;
  assert.ok(combinedHTML.includes(expectedId), `Search "${query}" must match ${expectedId}`);
}

assert.equal(consoleErrors.length, 0, `Unexpected console errors: ${consoleErrors.join('; ')}`);
console.log(JSON.stringify({ ok: true }));
""".replace("__HTML_PATH__", json.dumps(str(DASHBOARD_HTML_PATH))).replace(
        "__FIXTURE_JSON__", json.dumps(profiles_fixture)
    )

    proc = subprocess.run(
        [node_bin, "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, (
        f"Node VM UI test failed (rc={proc.returncode}):\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    assert json.loads(proc.stdout.strip().splitlines()[-1])["ok"] is True


def test_e2e_chrome_cdp_quota_provider_tiers_modal_and_sort(
    tmp_path: Path,
) -> None:
    """Headless Google Chrome CDP E2E verification of 4-provider tiers, modal visibility, priority sort, and screenshot."""
    chrome_bin = _find_chrome_binary()
    raw_html = DASHBOARD_HTML_PATH.read_text(encoding="utf-8")
    repo_sha_before = hashlib.sha256(raw_html.encode("utf-8")).hexdigest()

    profiles = _build_dynamic_4provider_profiles()
    safe_profiles_js = json.dumps(profiles, ensure_ascii=False, indent=2).replace(
        "</", "<\\/"
    )
    seeded_html, count = re.subn(
        r"const PROFILES_DATA = \{.*?\n\};",
        f"const PROFILES_DATA = {safe_profiles_js}\n;",
        raw_html,
        count=1,
        flags=re.DOTALL,
    )
    assert count == 1, "Failed to seed PROFILES_DATA into isolated quota_dashboard.html"

    html_bytes = seeded_html.encode("utf-8")
    status_bytes = json.dumps(
        {
            "success": True,
            "profiles": profiles,
            "schedules_by_profile": {},
            "can_auto_refresh": False,
            "last_refresh_all": 1763424000,
        },
        ensure_ascii=False,
    ).encode("utf-8")

    class _QuotaE2EHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path in ("/", "/quota_dashboard.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html_bytes)))
                self.end_headers()
                self.wfile.write(html_bytes)
                return
            if parsed.path == "/api/status":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(status_bytes)))
                self.end_headers()
                self.wfile.write(status_bytes)
                return
            if parsed.path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

    http_port = _pick_free_port()
    server = ThreadingHTTPServer(("127.0.0.1", http_port), _QuotaE2EHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    cdp_port = _pick_free_port()
    chrome_profile_dir = tmp_path / "chrome_cdp_profile"
    chrome_profile_dir.mkdir(parents=True, exist_ok=True)
    chrome_proc = subprocess.Popen(
        [
            chrome_bin,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--window-size=1440,1000",
            f"--user-data-dir={chrome_profile_dir}",
            f"--remote-debugging-port={cdp_port}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    cdp: _CdpSession | None = None
    try:
        ws_url = ""
        deadline = time.monotonic() + 12.0
        while time.monotonic() < deadline:
            try:
                raw_targets = urllib.request.urlopen(
                    f"http://127.0.0.1:{cdp_port}/json/list", timeout=1.0
                ).read()
                targets = json.loads(raw_targets.decode("utf-8"))
                pages = [
                    t
                    for t in targets
                    if t.get("type") == "page" and t.get("webSocketDebuggerUrl")
                ]
                if pages:
                    ws_url = str(pages[0]["webSocketDebuggerUrl"])
                    break
            except Exception:
                time.sleep(0.15)
        assert ws_url, "Timed out waiting for Headless Chrome CDP page target"

        cdp = _CdpSession(ws_url)
        cdp.call("Network.enable")
        cdp.call("Network.setBlockedURLs", {"urls": ["https://www.gstatic.com/*"]})
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        cdp.call("DOM.enable")

        target_url = (
            f"http://127.0.0.1:{http_port}/quota_dashboard.html?no-auto-refresh=1"
        )
        cdp.call("Page.navigate", {"url": target_url})

        ready = False
        nav_deadline = time.monotonic() + 10.0
        while time.monotonic() < nav_deadline:
            is_ready = cdp.eval_js(
                "document.readyState === 'complete' "
                "&& Boolean(document.getElementById('card-claude')) "
                "&& Boolean(document.getElementById('card-nguyenhieu000690'))"
            )
            if is_ready is True:
                ready = True
                break
            time.sleep(0.15)
        assert ready, "Quota dashboard failed to finish rendering cards in Chrome"

        snapshot: dict[str, Any] = cdp.eval_js(
            """(() => {
              const col1Cards = Array.from(document.querySelectorAll('#gridCol1 > [id^="card-"]'))
                .map((el) => el.id.replace(/^card-/, ''));
              const col2Cards = Array.from(document.querySelectorAll('#gridCol2 > [id^="card-"]'))
                .map((el) => el.id.replace(/^card-/, ''));
              const visualOrder = [];
              const maxLen = Math.max(col1Cards.length, col2Cards.length);
              for (let i = 0; i < maxLen; i += 1) {
                if (i < col1Cards.length) visualOrder.push(col1Cards[i]);
                if (i < col2Cards.length) visualOrder.push(col2Cards[i]);
              }

              const cardInfo = (key) => {
                const el = document.getElementById('card-' + key);
                if (!el) return null;
                const rosters = Array.from(el.querySelectorAll('[data-model-roster="true"]'))
                  .map((r) => r.textContent.trim());
                const titles = Array.from(el.querySelectorAll('[title]'))
                  .map((t) => t.getAttribute('title') || '');
                return {
                  text: el.textContent || '',
                  rosters,
                  titles,
                };
              };

              openProfileInfoModal('claude');
              const modalEl = document.getElementById('profileInfoModal');
              const argonMetaEl = document.getElementById('infoModalArgonMetaRow');
              const keychainRowEl = document.getElementById('infoModalKeychainRow');
              const claudeModal = {
                modalDisplay: modalEl ? window.getComputedStyle(modalEl).display : 'missing',
                tierText: document.getElementById('infoModalTier')?.textContent || '',
                cliText: document.getElementById('infoModalCliCmd')?.textContent || '',
                homeText: document.getElementById('infoModalHomePath')?.textContent || '',
                argonMetaDisplay: argonMetaEl ? window.getComputedStyle(argonMetaEl).display : 'missing',
                keychainRowDisplay: keychainRowEl ? window.getComputedStyle(keychainRowEl).display : 'missing',
              };
              closeProfileInfoModal();

              openProfileInfoModal('nguyenhieu000690');
              const agyModal = {
                argonMetaDisplay: argonMetaEl ? window.getComputedStyle(argonMetaEl).display : 'missing',
                keychainRowDisplay: keychainRowEl ? window.getComputedStyle(keychainRowEl).display : 'missing',
              };
              closeProfileInfoModal();

              return {
                orderedProfiles: getOrderedProfiles(),
                visualOrder,
                claude: cardInfo('claude'),
                codex: cardInfo('codex'),
                kiro: cardInfo('kiro'),
                ultra: cardInfo('nguyenhieu000690'),
                danhdue: cardInfo('danhdue'),
                claudeModal,
                agyModal,
              };
            })()"""
        )

        expected_order = [
            "claude",
            "codex",
            "kiro",
            "nguyenhieu000690",
            "danhdue",
            "d3molt",
            "buivantrong8901",
        ]
        assert snapshot["orderedProfiles"] == expected_order
        assert snapshot["visualOrder"] == expected_order

        # Provider card checks
        assert "ANTHROPIC" in snapshot["claude"]["text"]
        assert "CLAUDE PRO" in snapshot["claude"]["text"]
        assert "Priority: 100" in snapshot["claude"]["text"]

        assert "OPENAI" in snapshot["codex"]["text"]
        assert "CHATGPT PLUS" in snapshot["codex"]["text"]
        assert "Priority: 95" in snapshot["codex"]["text"]
        assert "Available models: gpt-6-astra" in snapshot["codex"]["rosters"]
        reset_titles = [t for t in snapshot["codex"]["titles"] if "Full Reset" in t]
        assert len(reset_titles) == 1
        assert "02/12" not in reset_titles[0]

        assert "KIRO" in snapshot["kiro"]["text"]
        assert "KIRO STUDENT" in snapshot["kiro"]["text"]
        assert "Priority: 90" in snapshot["kiro"]["text"]

        # Antigravity ULTRA checks
        ultra_text = snapshot["ultra"]["text"]
        for expected_ultra_token in (
            "ULTRA",
            "Priority: 80",
            "Carbon",
            "Argon",
            "Orchestrator",
            "Gemini Models 5H",
            "Gemini Weekly",
            "Gemini 4 Carbon & Argon Weekly",
            "Shared w/ Gemini Pool",
        ):
            assert expected_ultra_token in ultra_text
        assert len(snapshot["ultra"]["rosters"]) >= 4
        assert "models within this group" not in ultra_text.lower()

        # Antigravity PRO + separate Argon checks
        danhdue_text = snapshot["danhdue"]["text"]
        for expected_pro_token in ("PRO", "Priority: 60", "Argon", "100%"):
            assert expected_pro_token in danhdue_text
        assert "for paid pro plans" not in danhdue_text.lower()

        # Modal checks
        assert snapshot["claudeModal"]["modalDisplay"] != "none"
        assert "CLAUDE PRO (Priority 100)" in snapshot["claudeModal"]["tierText"]
        assert snapshot["claudeModal"]["cliText"] == "claude"
        assert snapshot["claudeModal"]["homeText"] == "~/.claude.json"
        assert snapshot["claudeModal"]["argonMetaDisplay"] == "none"
        assert snapshot["claudeModal"]["keychainRowDisplay"] == "none"

        assert snapshot["agyModal"]["argonMetaDisplay"] != "none"
        assert snapshot["agyModal"]["keychainRowDisplay"] != "none"

        # Capture screenshot artifact
        save_dir_env = os.environ.get("SAVE_E2E_SCREENSHOT_DIR", "").strip()
        screenshot_dir = Path(save_dir_env) if save_dir_env else tmp_path
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = screenshot_dir / "verify_check_quota_dynamic_tiers.png"
        shot = cdp.call("Page.captureScreenshot", {"format": "png"})
        png_bytes = base64.b64decode(shot["data"])
        screenshot_path.write_bytes(png_bytes)
        assert screenshot_path.is_file() and screenshot_path.stat().st_size > 10_000

        assert cdp.console_errors == []
        assert cdp.uncaught_exceptions == []

        repo_sha_after = hashlib.sha256(DASHBOARD_HTML_PATH.read_bytes()).hexdigest()
        assert repo_sha_after == repo_sha_before, (
            "Repo-tracked quota_dashboard.html was mutated during E2E test"
        )
    finally:
        if cdp is not None:
            cdp.close()
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            chrome_proc.kill()
        server.shutdown()
        server.server_close()
