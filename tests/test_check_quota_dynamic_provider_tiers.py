"""Unit tests for dynamic 4-provider account tiers, priorities, AccountMeta, and daemon hot-reload."""

from __future__ import annotations

import base64
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
TYPES_FILE = SCRIPTS_DIR / "types" / "quota_dashboard.types.ts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import agy_quota  # type: ignore[import-not-found]  # noqa: E402


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
