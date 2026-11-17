"""Unit and CLI integration tests for Hybrid dynamic model discovery & argonMode.

Covers BDD scenarios:
- CQRA-HP-01
- CQRA-HP-02
- CQRA-EC-01
- CQRA-ST-01
- CQRA-AR-01
- CQRA-FR-01
"""

from __future__ import annotations

import datetime
import json
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


@pytest.fixture(scope="module")
def ultra_models_stdout() -> str:
    """Return 18-model `agy models` stdout representative of Ultra pooled accounts."""
    return "\n".join(
        [
            "gemini-4-carbon-low",
            "gemini-4-carbon-medium",
            "gemini-4-carbon-high",
            "gemini-4-argon-low",
            "gemini-4-argon-medium",
            "gemini-4-argon-high",
            "gemini-4-hydrogen-low",
            "gemini-4-hydrogen-medium",
            "gemini-4-hydrogen-high",
            "gemini-3.8-flash-low",
            "gemini-3.8-flash-medium",
            "gemini-3.8-flash-high",
            "gemini-pro-orchestrator",
            "gemini-pro-orchestrator-argon",
            "claude-sonnet-4-6",
            "claude-opus-4-6-thinking",
            "gpt-oss-120b-medium",
            "gemini-2.5-flash-lite",
        ]
    )


@pytest.fixture(scope="module")
def pro_separate_models_stdout() -> str:
    """Return `agy models` stdout representative of Pro separate-Argon accounts."""
    return "\n".join(
        [
            "gemini-4-hydrogen-low",
            "gemini-4-hydrogen-high",
            "gemini-3.8-flash-low",
            "gemini-3.8-flash-high",
            "gemini-4-argon-low",
            "gemini-4-argon-high",
            "gemini-pro-orchestrator-g1-pro",
            "claude-opus-5-5-low",
            "claude-sonnet-5-5-medium",
            "gpt-oss-120b-medium",
        ]
    )


def _setup_isolated_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    profiles: list[str],
    initial_cache: dict[str, Any] | None = None,
) -> Path:
    """Create tmp_path-isolated Antigravity homes, DB, and dashboard HTML cache."""
    homes_root = tmp_path / "antigravity_homes"
    homes_root.mkdir(parents=True, exist_ok=True)
    for prof in profiles:
        p_home = homes_root / prof
        tok_file = p_home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
        tok_file.parent.mkdir(parents=True, exist_ok=True)
        tok_file.write_text(
            json.dumps({"token": {"access_token": "ya29.test", "refresh_token": "1//ref"}}),
            encoding="utf-8",
        )

    dash_html = tmp_path / "quota_dashboard.html"
    cache_payload = dict(initial_cache or {})
    dash_html.write_text(
        "<html><script>\nconst PROFILES_DATA = "
        + json.dumps(cache_payload, indent=2)
        + ";\n</script></html>\n",
        encoding="utf-8",
    )

    fake_home = tmp_path / "host_home"
    fake_home.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(agy_quota, "REAL_HOME", str(tmp_path))
    monkeypatch.setattr(agy_quota, "SESSION_STORE_DB", tmp_path / ".session_store.db")
    monkeypatch.setattr(agy_quota, "CACHED_PROFILES_DATA", {})
    monkeypatch.setattr(agy_quota, "get_dashboard_html_path", lambda: dash_html)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    monkeypatch.setattr(agy_quota, "wait_for_launch_lock", lambda *a, **kw: None)
    monkeypatch.setattr(agy_quota.time, "sleep", lambda *_a, **_kw: None)
    monkeypatch.setattr(
        agy_quota,
        "fetch_claude_quota",
        lambda: {"status": "ACTIVE", "isSessionActive": True},
    )
    monkeypatch.setattr(
        agy_quota,
        "fetch_codex_quota",
        lambda: {"status": "ACTIVE", "isSessionActive": True},
    )
    monkeypatch.setattr(
        agy_quota,
        "fetch_kiro_quota",
        lambda: {"status": "ACTIVE", "isCreditOnly": True},
    )
    monkeypatch.setattr(agy_quota, "print_claude_card", lambda *_a, **_kw: None)
    monkeypatch.setattr(agy_quota, "print_codex_card", lambda *_a, **_kw: None)
    monkeypatch.setattr(agy_quota, "print_kiro_card", lambda *_a, **_kw: None)
    return dash_html


def _make_usage_json(
    groups: list[dict[str, Any]],
    plan_name: str = "",
) -> str:
    data: dict[str, Any] = {"groups": groups}
    if plan_name:
        data["plan_name"] = plan_name
    return json.dumps({"command": {"data": data}})


def _read_cached_html(dash_html: Path) -> dict[str, Any]:
    text = dash_html.read_text(encoding="utf-8")
    marker = "const PROFILES_DATA ="
    idx1 = text.index(marker) + len(marker)
    idx2 = text.index("\n};", idx1) + len("\n}")
    raw = text[idx1:idx2].strip()
    if raw.endswith(";"):
        raw = raw[:-1].strip()
    parsed: dict[str, Any] = json.loads(raw)
    return parsed


def test_cqra_hp_01_ultra_shared_pool_discovery_and_mirror(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ultra_models_stdout: str,
) -> None:
    """[CQRA-HP-01] Ultra shared-pool profile discovers dynamic models, capabilities, and mirrors Gemini Weekly onto Argon."""
    _setup_isolated_env(tmp_path, monkeypatch, ["nguyenhieu000690"])
    usage_stdout = _make_usage_json(
        [
            {
                "name": "Gemini Models",
                "description": (
                    "Gemini 4 Carbon, Gemini 4 Argon, Gemini 4 Hydrogen, "
                    "Orchestrator (Carbon), Orchestrator (Argon), Gemini 3.8 Flash"
                ),
                "buckets": [
                    {
                        "window": "5h",
                        "remaining_fraction": 0.85,
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
                "description": "Claude Sonnet 4.6, Claude Opus 4.6, GPT-OSS 120B",
                "buckets": [
                    {
                        "window": "5h",
                        "remaining_fraction": 0.90,
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
    )

    def fake_run(cmd: list[str], **_kwargs: Any) -> MagicMock:
        if cmd and cmd[0] == "security":
            return MagicMock(returncode=44, stdout="", stderr="")
        if len(cmd) >= 2 and cmd[1] == "models":
            return MagicMock(returncode=0, stdout=ultra_models_stdout, stderr="")
        if "/usage" in cmd:
            return MagicMock(returncode=0, stdout=usage_stdout, stderr="")
        raise AssertionError(f"Unexpected subprocess command: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = agy_quota.fetch_quota_for_profile("nguyenhieu000690")
    assert result["success"] is True
    assert "plan_name" in result

    formatted = agy_quota.format_profile_for_dashboard("nguyenhieu000690", result)

    assert formatted["groupModels"]["gemini"] == [
        "Gemini 4 Carbon",
        "Gemini 4 Argon",
        "Gemini 4 Hydrogen",
        "Orchestrator (Carbon)",
        "Orchestrator (Argon)",
        "Gemini 3.8 Flash",
    ]
    assert formatted["groupModels"]["claude"] == [
        "Claude Sonnet 4.6",
        "Claude Opus 4.6",
        "GPT-OSS 120B",
    ]
    caps = formatted["capabilities"]
    assert caps["argonMode"] == "shared_gemini"
    assert caps["tier"] == "ULTRA"
    assert caps["hasCarbon"] is True
    assert caps["hasArgon"] is True
    assert caps["hasOrchestrator"] is True
    for expected_badge in ("ULTRA", "Carbon", "Argon", "Orchestrator"):
        assert expected_badge in caps["badges"]

    assert formatted["tier"] == "PRO"
    assert formatted["hasArgon"] is True

    argon_w = formatted["argonWeekly"]
    assert argon_w["sharedPool"] is True
    assert argon_w["mode"] == "shared_gemini"
    assert argon_w["fraction"] == pytest.approx(0.85)
    assert argon_w["resetTime"] == "2026-11-24T00:00:00Z"
    assert argon_w["unavailable"] is False
    assert argon_w["countdown"] == formatted["geminiWeekly"]["countdown"]
    assert len(formatted["availableModels"]) == 18


@pytest.mark.parametrize(
    ("plan_name", "expected_cap_tier"),
    [
        ("", "PRO"),
        ("Google AI Pro", "PRO"),
        ("Google AI Ultra", "ULTRA"),
    ],
)
def test_cqra_hp_02_pro_separate_argon_merges_catalog_and_preserves_labels(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    pro_separate_models_stdout: str,
    plan_name: str,
    expected_cap_tier: str,
) -> None:
    """[CQRA-HP-02] Pro separate-Argon profile merges agy models catalog with /usage descriptions and preserves Claude 5.5 labels."""
    _setup_isolated_env(tmp_path, monkeypatch, ["danhdue"])
    usage_stdout = _make_usage_json(
        [
            {
                "name": "Gemini Models",
                "description": "Gemini 4 Hydrogen, Gemini 3.8 Flash",
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
                "description": "Claude Opus 5.5, Claude Sonnet 5.5, GPT-OSS 120B",
                "buckets": [
                    {
                        "window": "5h",
                        "remaining_fraction": 0.80,
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
                "description": "gemini-argon-wtu-weekly",
                "buckets": [
                    {
                        "window": "weekly",
                        "remaining_fraction": 0.45,
                        "reset_time": "2026-11-23T00:00:00Z",
                    }
                ],
            },
        ],
        plan_name=plan_name,
    )

    def fake_run(cmd: list[str], **_kwargs: Any) -> MagicMock:
        if cmd and cmd[0] == "security":
            return MagicMock(returncode=44, stdout="", stderr="")
        if len(cmd) >= 2 and cmd[1] == "models":
            return MagicMock(returncode=0, stdout=pro_separate_models_stdout, stderr="")
        if "/usage" in cmd:
            return MagicMock(returncode=0, stdout=usage_stdout, stderr="")
        raise AssertionError(f"Unexpected subprocess command: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    # Preserve legacy parse_agy_models_output return contract (list[str])
    legacy_ids = agy_quota.parse_agy_models_output(pro_separate_models_stdout)
    assert isinstance(legacy_ids, list)
    assert all(isinstance(x, str) for x in legacy_ids)
    assert "gemini-pro-orchestrator-g1-pro" in legacy_ids

    result = agy_quota.fetch_quota_for_profile("danhdue")
    formatted = agy_quota.format_profile_for_dashboard("danhdue", result)

    caps = formatted["capabilities"]
    assert caps["argonMode"] == "separate"
    assert caps["tier"] == expected_cap_tier
    assert caps["hasOrchestrator"] is True
    assert formatted["tier"] == "PRO"
    assert formatted["groupModels"]["claude"] == [
        "Claude Opus 5.5",
        "Claude Sonnet 5.5",
        "GPT-OSS 120B",
    ]
    assert "Orchestrator (Argon)" in formatted["groupModels"]["argon"]

    argon_w = formatted["argonWeekly"]
    assert argon_w["sharedPool"] is False
    assert argon_w["mode"] == "separate"
    assert argon_w["fraction"] == pytest.approx(0.45)

    catalog_by_id = {entry["id"]: entry for entry in formatted["modelCatalog"]}
    assert "gemini-pro-orchestrator-g1-pro" in catalog_by_id
    orch_entry = catalog_by_id["gemini-pro-orchestrator-g1-pro"]
    assert "orchestrator" in orch_entry["tags"]
    assert "g1-pro" in orch_entry["tags"]


def test_cqra_ec_01_auth_needed_and_disabled_never_invoke_agy_models(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[CQRA-EC-01] Auth-needed and disabled profiles never invoke agy models subprocesses."""
    initial_cache = {
        "banned_acct": {
            "email": "banned_acct@gmail.com",
            "tier": "PRO",
            "status": "DISABLED",
            "isAppeal": True,
            "availableModels": ["gemini-4-hydrogen-high"],
            "modelCatalog": [
                {
                    "id": "gemini-4-hydrogen-high",
                    "label": "Gemini 4 Hydrogen",
                    "quotaFamily": "gemini",
                    "tags": ["hydrogen"],
                }
            ],
            "groupModels": {"gemini": ["Gemini 4 Hydrogen"], "claude": [], "argon": []},
        }
    }
    dash_html = _setup_isolated_env(
        tmp_path,
        monkeypatch,
        ["broken_auth", "banned_acct"],
        initial_cache=initial_cache,
    )

    # broken_auth has no valid token
    broken_tok = (
        tmp_path
        / "antigravity_homes"
        / "broken_auth"
        / ".gemini"
        / "antigravity-cli"
        / "antigravity-oauth-token"
    )
    broken_tok.unlink()

    # banned_acct has tos_disabled.json marker
    tos_dir = tmp_path / "antigravity_homes" / "banned_acct" / ".gemini" / "antigravity"
    tos_dir.mkdir(parents=True, exist_ok=True)
    (tos_dir / "tos_disabled.json").write_text(
        json.dumps({"profile": "banned_acct", "error_id": "11111111-2222-3333-4444-555555555555"}),
        encoding="utf-8",
    )

    models_calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs: Any) -> MagicMock:
        if len(cmd) >= 2 and cmd[1] == "models":
            models_calls.append(list(cmd))
        return MagicMock(returncode=44, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(agy_quota, "get_all_profiles", lambda: ["broken_auth", "banned_acct"])

    res_auth = agy_quota.fetch_quota_for_profile("broken_auth")
    res_dis = agy_quota.fetch_quota_for_profile("banned_acct")
    assert res_auth["status"] == "AUTH NEEDED"
    assert res_dis["status"] == "DISABLED"
    assert len(models_calls) == 0

    monkeypatch.setattr(sys, "argv", ["agy_quota.py", "all"])
    agy_quota.main()

    assert len(models_calls) == 0
    persisted = _read_cached_html(dash_html)
    assert persisted["banned_acct"]["availableModels"] == ["gemini-4-hydrogen-high"]


def test_cqra_st_01_hybrid_cache_transitions_and_single_profile_refresh(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ultra_models_stdout: str,
) -> None:
    """[CQRA-ST-01] Hybrid cache refreshes agy models on miss, signature change, 24h expiry, and single-profile refresh while skipping warm batch hits."""
    groups_v1 = [
        {
            "name": "Gemini Models",
            "description": "Gemini 4 Carbon, Gemini 4 Argon, Gemini 4 Hydrogen",
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 0.90,
                    "reset_time": "2026-11-18T10:00:00Z",
                },
                {
                    "window": "weekly",
                    "remaining_fraction": 0.90,
                    "reset_time": "2026-11-24T00:00:00Z",
                },
            ],
        },
        {
            "name": "Claude and GPT models",
            "description": "Claude Sonnet 4.6, GPT-OSS 120B",
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 0.90,
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
    sig_v1 = agy_quota.parse_usage_group_models(groups_v1)["groupDescSig"]
    two_hours_ago = (
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    initial_cache = {
        "nguyenhieu000690": {
            "email": "nguyenhieu000690@gmail.com",
            "tier": "PRO",
            "status": "ACTIVE",
            "hasArgon": True,
            "availableModels": agy_quota.parse_agy_models_output(ultra_models_stdout),
            "modelCatalog": agy_quota.parse_agy_models_catalog(ultra_models_stdout),
            "groupModels": {
                "gemini": ["Gemini 4 Carbon", "Gemini 4 Argon", "Gemini 4 Hydrogen"],
                "claude": ["Claude Sonnet 4.6", "GPT-OSS 120B"],
                "argon": ["Gemini 4 Argon"],
            },
            "modelsFetchedAt": two_hours_ago,
            "groupDescSig": sig_v1,
        }
    }
    dash_html = _setup_isolated_env(
        tmp_path,
        monkeypatch,
        ["nguyenhieu000690"],
        initial_cache=initial_cache,
    )
    monkeypatch.setattr(agy_quota, "get_all_profiles", lambda: ["nguyenhieu000690"])

    current_groups: list[dict[str, Any]] = groups_v1
    models_call_count = 0

    def fake_run(cmd: list[str], **_kwargs: Any) -> MagicMock:
        nonlocal models_call_count
        if cmd and cmd[0] == "security":
            return MagicMock(returncode=44, stdout="", stderr="")
        if len(cmd) >= 2 and cmd[1] == "models":
            models_call_count += 1
            return MagicMock(returncode=0, stdout=ultra_models_stdout, stderr="")
        if "/usage" in cmd:
            return MagicMock(returncode=0, stdout=_make_usage_json(current_groups), stderr="")
        raise AssertionError(f"Unexpected subprocess command: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    # Batch run 1: warm cache (2h old, matching groupDescSig) -> 0 agy models calls
    monkeypatch.setattr(sys, "argv", ["agy_quota.py", "all", "--table"])
    agy_quota.main()
    assert models_call_count == 0

    # Batch run 2: description changes groupDescSig -> 1 agy models call + updated groupDescSig
    groups_v2 = [
        {
            **groups_v1[0],
            "description": (
                "Gemini 4 Carbon, Gemini 4 Argon, Gemini 4 Hydrogen, Gemini 3.8 Flash"
            ),
        },
        groups_v1[1],
    ]
    current_groups = groups_v2
    sig_v2 = agy_quota.parse_usage_group_models(groups_v2)["groupDescSig"]
    assert sig_v2 != sig_v1

    agy_quota.main()
    assert models_call_count == 1
    persisted_after_v2 = _read_cached_html(dash_html)
    assert persisted_after_v2["nguyenhieu000690"]["groupDescSig"] == sig_v2

    # Batch run 3: age modelsFetchedAt past 24 hours -> 1 agy models call + refreshed modelsFetchedAt
    stale_ts = (
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=25)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    agy_quota.CACHED_PROFILES_DATA["nguyenhieu000690"]["modelsFetchedAt"] = stale_ts
    agy_quota.update_cached_profile(
        "nguyenhieu000690", agy_quota.CACHED_PROFILES_DATA["nguyenhieu000690"]
    )

    agy_quota.main()
    assert models_call_count == 2
    persisted_after_ttl = _read_cached_html(dash_html)
    assert persisted_after_ttl["nguyenhieu000690"]["modelsFetchedAt"] != stale_ts

    # Single-profile CLI refresh: invokes agy models 1 time even on warm cache and persists to tmp_path
    current_groups = [
        {
            **groups_v2[0],
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 0.72,
                    "reset_time": "2026-11-18T10:00:00Z",
                },
                {
                    "window": "weekly",
                    "remaining_fraction": 0.72,
                    "reset_time": "2026-11-24T00:00:00Z",
                },
            ],
        },
        groups_v2[1],
    ]
    monkeypatch.setattr(sys, "argv", ["agy_quota.py", "refresh", "nguyenhieu000690"])
    agy_quota.main()
    assert models_call_count == 3

    persisted_after_refresh = _read_cached_html(dash_html)
    assert persisted_after_refresh["nguyenhieu000690"]["geminiWeekly"]["fraction"] == pytest.approx(
        0.72
    )
    assert persisted_after_refresh["nguyenhieu000690"]["argonWeekly"]["fraction"] == pytest.approx(
        0.72
    )


def test_cqra_ar_01_strict_per_profile_isolation_ping_suppression_and_cli_views(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    ultra_models_stdout: str,
) -> None:
    """[CQRA-AR-01] Strictly independent per-profile quota isolation, ping suppression, and CLI table formatting."""
    profiles = ["hoangcongtam690", "nguyenhieu000690"]
    _setup_isolated_env(tmp_path, monkeypatch, profiles)

    shared_reset = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=6)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    active_5h = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    fractions_by_profile = {
        "hoangcongtam690": 0.85,
        "nguyenhieu000690": 0.62,
    }
    invoked_cmds: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> MagicMock:
        invoked_cmds.append(list(cmd))
        env = kwargs.get("env") or {}
        prof = env.get("AGY_PROFILE", "hoangcongtam690")
        frac = fractions_by_profile.get(prof, 0.85)
        if cmd and cmd[0] == "security":
            return MagicMock(returncode=44, stdout="", stderr="")
        if len(cmd) >= 2 and cmd[1] == "models":
            return MagicMock(returncode=0, stdout=ultra_models_stdout, stderr="")
        if "/usage" in cmd:
            payload = _make_usage_json(
                [
                    {
                        "name": "Gemini Models",
                        "description": (
                            "Gemini 4 Carbon, Gemini 4 Argon, Gemini 4 Hydrogen, "
                            "Orchestrator (Carbon), Orchestrator (Argon), Gemini 3.8 Flash"
                        ),
                        "buckets": [
                            {
                                "window": "5h",
                                "remaining_fraction": frac,
                                "reset_time": active_5h,
                            },
                            {
                                "window": "weekly",
                                "remaining_fraction": frac,
                                "reset_time": shared_reset,
                            },
                        ],
                    },
                    {
                        "name": "Claude and GPT models",
                        "description": "Claude Sonnet 4.6, Claude Opus 4.6, GPT-OSS 120B",
                        "buckets": [
                            {
                                "window": "5h",
                                "remaining_fraction": 0.90,
                                "reset_time": active_5h,
                            },
                            {
                                "window": "weekly",
                                "remaining_fraction": 0.90,
                                "reset_time": shared_reset,
                            },
                        ],
                    },
                ]
            )
            return MagicMock(returncode=0, stdout=payload, stderr="")
        # Model ping prompt execution
        return MagicMock(returncode=0, stdout="OK", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    results = [agy_quota.fetch_quota_for_profile(p) for p in profiles]
    formatted_map = {
        p: agy_quota.format_profile_for_dashboard(p, r)
        for p, r in zip(profiles, results, strict=True)
    }

    # Strict per-profile isolation: zero retrieveUserQuotaSummary calls or cross-profile linkage keys
    assert not any("retrieveUserQuotaSummary" in " ".join(c) for c in invoked_cmds)
    forbidden_pool_keys = {"poolId", "sharedPoolId", "linkedProfiles", "sharedAccounts"}
    for p, f_data in formatted_map.items():
        assert forbidden_pool_keys.isdisjoint(f_data.keys())
        agy_quota.update_cached_profile(p, f_data)

    assert formatted_map["hoangcongtam690"]["argonWeekly"]["fraction"] == pytest.approx(0.85)
    assert formatted_map["nguyenhieu000690"]["argonWeekly"]["fraction"] == pytest.approx(0.62)

    # Ping suppression on both live (force=True) and cached-fallback paths + probe_blocked_profile
    for p in profiles:
        ping_res = agy_quota.execute_ping_profile(p, force=True)
        assert ping_res["pinged_argon"] is False
    assert not any(
        "--model" in c and any("argon" in part.lower() for part in c) for c in invoked_cmds
    )

    # Cached-fallback branch in execute_ping_profile & probe_blocked_profile
    invoked_cmds.clear()
    monkeypatch.setattr(
        agy_quota,
        "fetch_quota_for_profile",
        lambda p, **_kw: {"profile": p, "success": False, "error": "transient failure"},
    )
    cached_ping = agy_quota.execute_ping_profile("hoangcongtam690", force=True)
    assert cached_ping["pinged_argon"] is False
    agy_quota.LAST_BLOCKED_PROBE.clear()
    probe_res = agy_quota.probe_blocked_profile("hoangcongtam690")
    assert probe_res["success"] is True
    assert not any(
        "--model" in c and any("argon" in part.lower() for part in c) for c in invoked_cmds
    )

    # CLI cards and --table summary output
    capsys.readouterr()
    for r in results:
        agy_quota.print_dashboard_cards(r)
    cards_out = capsys.readouterr().out
    assert "Gemini 4 Carbon" in cards_out
    assert "Claude Sonnet 4.6" in cards_out
    assert "Shared Gemini" in cards_out

    agy_quota.print_all_summary(results, show_providers=True)
    table_out = capsys.readouterr().out
    assert table_out.count("(Shared Gemini)") >= 2
    assert "85.0%" in table_out
    assert "62.0%" in table_out


@pytest.mark.parametrize(
    ("cached_state", "expected_mode", "expected_gemini_models"),
    [
        ({}, "none", []),
        (
            {
                "corrupt_prof": {
                    "email": "corrupt_prof@gmail.com",
                    "tier": "PRO",
                    "status": "ACTIVE",
                    "hasArgon": True,
                    "groupModels": {
                        "gemini": ["Gemini 4 Carbon", "Gemini 4 Argon"],
                        "claude": [],
                        "argon": ["Gemini 4 Argon"],
                    },
                    "capabilities": {
                        "tier": "ULTRA",
                        "hasCarbon": True,
                        "hasArgon": True,
                        "argonMode": "shared_gemini",
                        "hasOrchestrator": False,
                        "badges": ["ULTRA", "Carbon", "Argon"],
                    },
                }
            },
            "shared_gemini",
            ["Gemini 4 Carbon", "Gemini 4 Argon"],
        ),
    ],
)
def test_cqra_fr_01_malformed_descriptions_and_models_timeout_degrade_softly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cached_state: dict[str, Any],
    expected_mode: str,
    expected_gemini_models: list[str],
) -> None:
    """[CQRA-FR-01] Malformed /usage group descriptions or agy models timeout degrade softly without crashing quota fetch."""
    _setup_isolated_env(
        tmp_path,
        monkeypatch,
        ["corrupt_prof"],
        initial_cache=cached_state,
    )
    usage_stdout = _make_usage_json(
        [
            {
                "name": "Gemini Models",
                "description": None,
                "buckets": [
                    {
                        "window": "5h",
                        "remaining_fraction": 0.77,
                        "reset_time": "2026-11-18T10:00:00Z",
                    },
                    {
                        "window": "weekly",
                        "remaining_fraction": 0.77,
                        "reset_time": "2026-11-24T00:00:00Z",
                    },
                ],
            }
        ]
    )

    def fake_run(cmd: list[str], **_kwargs: Any) -> MagicMock:
        if cmd and cmd[0] == "security":
            return MagicMock(returncode=44, stdout="", stderr="")
        if len(cmd) >= 2 and cmd[1] == "models":
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=25)
        if "/usage" in cmd:
            return MagicMock(returncode=0, stdout=usage_stdout, stderr="")
        raise AssertionError(f"Unexpected subprocess command: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    res = agy_quota.fetch_quota_for_profile("corrupt_prof")
    assert res["success"] is True
    assert res["argonMode"] == expected_mode
    assert res["groupModels"]["gemini"] == expected_gemini_models

    formatted = agy_quota.format_profile_for_dashboard("corrupt_prof", res)
    assert formatted["gemini5h"]["unavailable"] is False
    assert formatted["gemini5h"]["fraction"] == pytest.approx(0.77)
    assert formatted["capabilities"]["argonMode"] == expected_mode


@pytest.mark.parametrize(
    "expected_snippet",
    [
        "export type ArgonMode = 'separate' | 'shared_gemini' | 'none';",
        "export interface ModelCatalogEntry",
        "export interface ProfileCapabilities",
        "sharedPool?: boolean;",
        "mode?: ArgonMode;",
        "availableModels?: string[];",
        "modelCatalog?: ModelCatalogEntry[];",
        "groupModels?:",
        "capabilities?: ProfileCapabilities;",
        "modelsFetchedAt?: string;",
        "groupDescSig?: string;",
    ],
)
def test_typescript_schema_exports_dynamic_models_and_argon_mode(
    expected_snippet: str,
) -> None:
    """Verify quota_dashboard.types.ts exports ArgonMode, ModelCatalogEntry, ProfileCapabilities, and aligned QuotaBucket/ProfileQuotaState fields."""
    ts_content = TYPES_FILE.read_text(encoding="utf-8")
    assert expected_snippet in ts_content
