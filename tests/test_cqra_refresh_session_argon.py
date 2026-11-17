"""Unit tests for refresh_session shared-pool Argon ping suppression guard.

Covers: CQRA-ST-02, CQRA-FR-02
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest  # type: ignore[import-not-found]

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "refresh-session"
    / "resources"
    / "scripts"
    / "refresh_session.py"
)
_SPEC = importlib.util.spec_from_file_location("refresh_session", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
refresh_session: Any = importlib.util.module_from_spec(_SPEC)
sys.modules["refresh_session"] = refresh_session
_SPEC.loader.exec_module(refresh_session)


@pytest.fixture(scope="module")
def usage_snapshots() -> dict[str, dict[str, Any]]:
    """Read-only `/usage` payload fixtures for shared_gemini, separate, and none profiles."""
    return {
        "ultra_shared_active": {
            "plan_name": "g1-ultra-tier",
            "groups": [
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
                            "description": "Used some quota",
                        },
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.85,
                            "reset_time": "2026-11-24T00:00:00Z",
                            "description": "Used some quota",
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
                            "description": "Used some quota",
                        }
                    ],
                },
            ],
        },
        "ultra_shared_inactive_gem": {
            "plan_name": "g1-ultra-tier",
            "groups": [
                {
                    "name": "Gemini Models",
                    "description": (
                        "Gemini 4 Carbon, Gemini 4 Argon, Gemini 4 Hydrogen, "
                        "Orchestrator (Carbon), Orchestrator (Argon), Gemini 3.8 Flash"
                    ),
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 1.0,
                            "reset_time": "",
                            "description": "",
                        }
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
                            "description": "Used some quota",
                        }
                    ],
                },
            ],
        },
        "pro_sep_inactive_argon": {
            "plan_name": "g1-pro-tier",
            "groups": [
                {
                    "name": "Gemini Models",
                    "description": "Gemini 4 Hydrogen, Gemini 3.8 Flash",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 0.80,
                            "reset_time": "2026-11-18T10:00:00Z",
                            "description": "Used some quota",
                        }
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
                            "description": "Used some quota",
                        }
                    ],
                },
                {
                    "name": "Gemini 4 Argon",
                    "description": "gemini-argon-wtu-weekly",
                    "buckets": [
                        {
                            "window": "weekly",
                            "remaining_fraction": 1.0,
                            "reset_time": "",
                            "description": "",
                        }
                    ],
                },
            ],
        },
        "pro_sep_active_argon": {
            "plan_name": "g1-pro-tier",
            "groups": [
                {
                    "name": "Gemini Models",
                    "description": "Gemini 4 Hydrogen, Gemini 3.8 Flash",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 0.80,
                            "reset_time": "2026-11-18T10:00:00Z",
                            "description": "Used some quota",
                        }
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
                            "description": "Used some quota",
                        }
                    ],
                },
                {
                    "name": "Gemini 4 Argon",
                    "description": "gemini-argon-wtu-weekly",
                    "buckets": [
                        {
                            "window": "weekly",
                            "remaining_fraction": 0.45,
                            "reset_time": "2026-11-22T00:00:00Z",
                            "description": "Used some quota",
                        }
                    ],
                },
            ],
        },
        "no_argon": {
            "plan_name": "g1-pro-tier",
            "groups": [
                {
                    "name": "Gemini Models",
                    "description": "Gemini 4 Hydrogen, Gemini 3.8 Flash",
                    "buckets": [
                        {
                            "window": "5h",
                            "remaining_fraction": 0.90,
                            "reset_time": "2026-11-18T10:00:00Z",
                            "description": "Used some quota",
                        }
                    ],
                }
            ],
        },
    }


@pytest.fixture(scope="module")
def dashboard_cache_payload() -> dict[str, Any]:
    """Read-only PROFILES_DATA payload covering shared_gemini, separate, legacy, and none modes."""
    return {
        "shared_cached": {
            "hasArgon": True,
            "capabilities": {"argonMode": "shared_gemini"},
            "argonWeekly": {"unavailable": False, "sharedPool": True},
        },
        "legacy_shared": {
            "hasArgon": True,
            "argonWeekly": {"unavailable": False, "sharedPool": True},
        },
        "none_cached": {
            "hasArgon": False,
            "capabilities": {"argonMode": "none"},
            "argonWeekly": {"unavailable": True, "sharedPool": False},
        },
        "separate_cached": {
            "hasArgon": True,
            "capabilities": {"argonMode": "separate"},
            "argonWeekly": {"unavailable": False, "sharedPool": False},
        },
        "legacy_separate": {
            "hasArgon": True,
            "argonWeekly": {"unavailable": False},
        },
    }


def _setup_isolated_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    profiles: list[str],
    dashboard_data: dict[str, Any] | None = None,
) -> Path:
    """Configure tmp_path-isolated profile homes, fake agy binary, and dashboard HTML candidate."""
    real_home = tmp_path / "host_home"
    real_home.mkdir(parents=True, exist_ok=True)
    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir(parents=True, exist_ok=True)
    fake_agy = fake_bin_dir / "agy"
    fake_agy.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_agy.chmod(0o755)

    for prof in profiles:
        token_file = (
            real_home
            / "antigravity_homes"
            / prof
            / ".gemini"
            / "antigravity-cli"
            / "antigravity-oauth-token"
        )
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(
            json.dumps({"token": {"access_token": f"tok-{prof}"}}),
            encoding="utf-8",
        )

    dashboard_html = tmp_path / "quota_dashboard.html"
    if dashboard_data is not None:
        raw_json = json.dumps(dashboard_data, indent=2)
        dashboard_html.write_text(
            f"<html><script>\nconst PROFILES_DATA = {raw_json};\n</script></html>\n",
            encoding="utf-8",
        )

    monkeypatch.setattr(refresh_session, "REAL_HOME", str(real_home))
    monkeypatch.setattr(refresh_session, "REAL_HOME_DIR", real_home)
    monkeypatch.setattr(
        refresh_session,
        "SESSION_STORE_DB",
        real_home / ".devtool" / "state" / ".session_store.db",
    )
    monkeypatch.setattr(refresh_session, "_DASHBOARD_HTML_CANDIDATES", [dashboard_html])
    monkeypatch.setattr(refresh_session.shutil, "which", lambda _name: str(fake_agy))
    monkeypatch.setattr(refresh_session.time, "sleep", lambda _sec: None)
    return dashboard_html


def _cleanup_tmp_profiles(profiles: list[str]) -> None:
    """Remove synthetic `/tmp/ag_<profile>` directories created during unit tests."""
    for prof in profiles:
        shutil.rmtree(f"/tmp/ag_{prof}", ignore_errors=True)


@pytest.mark.parametrize(
    ("snapshot_key", "extra_models", "expected_mode", "expected_dedicated", "expected_gem_active"),
    [
        ("ultra_shared_active", [], "shared_gemini", False, True),
        ("ultra_shared_inactive_gem", [], "shared_gemini", False, False),
        ("pro_sep_inactive_argon", [], "separate", True, True),
        ("no_argon", ["gemini-4-argon-high"], "shared_gemini", False, True),
        ("no_argon", ["gemini-3.8-flash-low"], "none", False, True),
    ],
)
def test_cqra_st_02_extract_usage_buckets_argon_mode(
    usage_snapshots: dict[str, dict[str, Any]],
    snapshot_key: str,
    extra_models: list[str],
    expected_mode: str,
    expected_dedicated: bool,
    expected_gem_active: bool,
) -> None:
    """[CQRA-ST-02] Verify _extract_usage_buckets classifies argonMode and group metadata."""
    cmd_data = dict(usage_snapshots[snapshot_key])
    if extra_models:
        cmd_data["available_models"] = extra_models
    buckets = refresh_session._extract_usage_buckets(cmd_data)
    assert buckets.get("argonMode") == expected_mode
    assert buckets.get("has_dedicated_argon_group") is expected_dedicated
    assert buckets.get("gemini_group_active") is expected_gem_active


@pytest.mark.parametrize(
    ("ultra_snapshot_key", "pro_snapshot_key", "expected_ultra_pinged", "expected_pro_argon_pings"),
    [
        ("ultra_shared_active", "pro_sep_inactive_argon", [], 1),
        ("ultra_shared_inactive_gem", "pro_sep_active_argon", ["Gemini 5H"], 0),
    ],
)
def test_cqra_st_02_suppresses_argon_ping_for_shared_gemini(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    usage_snapshots: dict[str, dict[str, Any]],
    ultra_snapshot_key: str,
    pro_snapshot_key: str,
    expected_ultra_pinged: list[str],
    expected_pro_argon_pings: int,
) -> None:
    """[CQRA-ST-02] Suppress Argon 7D ping on shared_gemini while preserving ping on inactive separate Argon."""
    _setup_isolated_env(tmp_path, monkeypatch, profiles=["ultra_shared", "pro_sep"])

    ultra_models_stdout = "\n".join(
        [
            "gemini-4-carbon-high",
            "gemini-4-argon-low",
            "gemini-4-argon-high",
            "gemini-pro-orchestrator",
            "gemini-pro-orchestrator-argon",
            "gemini-3.8-flash-low",
            "claude-sonnet-4-6",
        ]
    )
    pro_models_stdout = "\n".join(
        [
            "gemini-3.8-flash-low",
            "claude-sonnet-5-5-low",
            "gemini-4-argon-low",
            "gemini-pro-orchestrator-g1-pro",
        ]
    )

    def fake_subprocess_run(cmd: list[str], *args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        env = kwargs.get("env") or {}
        prof = env.get("AGY_PROFILE", "")
        if "/usage" in cmd:
            payload = (
                usage_snapshots[ultra_snapshot_key]
                if prof == "ultra_shared"
                else usage_snapshots[pro_snapshot_key]
            )
            return subprocess.CompletedProcess(
                cmd, 0, stdout=json.dumps({"command": {"data": payload}}), stderr=""
            )
        if "models" in cmd:
            out = ultra_models_stdout if prof == "ultra_shared" else pro_models_stdout
            return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    dispatched_pings: dict[str, list[str]] = {"ultra_shared": [], "pro_sep": []}

    def fake_isolated_ping(
        _agy_bin: str,
        model_id: str,
        prompt: str,
        env: dict[str, str],
        cwd: str,
        timeout: int,
    ) -> tuple[bool, bool, str]:
        assert prompt and cwd and timeout > 0
        prof = env["AGY_PROFILE"]
        dispatched_pings[prof].append(model_id)
        return True, False, ""

    monkeypatch.setattr(refresh_session.subprocess, "run", fake_subprocess_run)
    monkeypatch.setattr(refresh_session, "_run_isolated_agy_model_ping", fake_isolated_ping)

    ultra_res = refresh_session.ping_profile("ultra_shared")
    pro_res = refresh_session.ping_profile("pro_sep")
    _cleanup_tmp_profiles(["ultra_shared", "pro_sep"])

    ultra_argon_models = [m for m in dispatched_pings["ultra_shared"] if "argon" in m]
    assert ultra_argon_models == []
    assert "Argon 7D" not in ultra_res["models_pinged"]
    assert "Argon 7D" not in ultra_res["details"]
    assert ultra_res["status"] != "FAIL"
    assert ultra_res["models_pinged"] == expected_ultra_pinged

    pro_argon_models = [m for m in dispatched_pings["pro_sep"] if "argon" in m]
    assert len(pro_argon_models) == expected_pro_argon_pings
    if expected_pro_argon_pings == 1:
        assert pro_argon_models == ["gemini-4-argon-low"]
        assert pro_res["models_pinged"] == ["Argon 7D"]
        assert pro_res["status"] == "PASS"
    else:
        assert pro_res["status"] == "SKIPPED"


@pytest.mark.parametrize(
    ("profile_name", "expected_has_argon"),
    [
        ("shared_cached", False),
        ("legacy_shared", False),
        ("none_cached", False),
        ("corrupt_probe", False),
        ("separate_cached", True),
        ("legacy_separate", True),
    ],
)
def test_cqra_fr_02_check_profile_has_argon_cache_modes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dashboard_cache_payload: dict[str, Any],
    profile_name: str,
    expected_has_argon: bool,
) -> None:
    """[CQRA-FR-02] Gate check_profile_has_argon strictly on separate Argon mode."""
    _setup_isolated_env(
        tmp_path,
        monkeypatch,
        profiles=[profile_name],
        dashboard_data=dashboard_cache_payload,
    )
    assert refresh_session.check_profile_has_argon(profile_name) is expected_has_argon


@pytest.mark.parametrize(
    ("profile_name", "mock_probe_return", "corrupt_html", "expected_argon_pings"),
    [
        ("shared_cached", ({}, ["gemini-4-argon-low", "gemini-3.8-flash-low"], False), False, 0),
        ("shared_cached", ({}, None, False), False, 0),
        ("corrupt_probe", ({}, None, False), False, 0),
        ("corrupt_probe", (None, [], False), False, 0),
        ("corrupt_probe", None, True, 0),
        ("separate_cached", ({}, ["gemini-4-argon-low"], False), False, 1),
    ],
)
def test_cqra_fr_02_corrupted_probe_and_shared_cache_fallback_zero_argon_pings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dashboard_cache_payload: dict[str, Any],
    profile_name: str,
    mock_probe_return: Any,
    corrupt_html: bool,
    expected_argon_pings: int,
) -> None:
    """[CQRA-FR-02] Shared-gemini cache fallback and corrupted usage probes emit 0 Argon 7D pings."""
    html_path = _setup_isolated_env(
        tmp_path,
        monkeypatch,
        profiles=["shared_cached", "corrupt_probe", "separate_cached"],
        dashboard_data=dashboard_cache_payload,
    )
    if corrupt_html:
        html_path.write_text("<html><script>const PROFILES_DATA = {broken;</script>", encoding="utf-8")

    assert refresh_session.check_profile_has_argon("shared_cached") is False
    assert refresh_session.check_profile_has_argon("corrupt_probe") is False

    pinged_models: list[str] = []

    def fake_isolated_ping(
        _agy_bin: str,
        model_id: str,
        prompt: str,
        env: dict[str, str],
        cwd: str,
        timeout: int,
    ) -> tuple[bool, bool, str]:
        assert prompt and env and cwd and timeout > 0
        pinged_models.append(model_id)
        return True, False, ""

    monkeypatch.setattr(
        refresh_session,
        "_probe_profile_usage_and_models",
        lambda *_args, **_kwargs: mock_probe_return,
    )
    monkeypatch.setattr(refresh_session, "_run_isolated_agy_model_ping", fake_isolated_ping)

    res = refresh_session.ping_profile(profile_name)
    _cleanup_tmp_profiles(["shared_cached", "corrupt_probe", "separate_cached"])
    argon_pings = [m for m in pinged_models if "argon" in m]
    assert len(argon_pings) == expected_argon_pings
    if expected_argon_pings == 0:
        assert "Argon 7D" not in res["models_pinged"]
        assert "Argon 7D" not in res["details"]
    else:
        assert "Argon 7D" in res["models_pinged"]
    assert res["status"] == "PASS"


@pytest.mark.parametrize(
    ("usage_stdout", "models_stdout"),
    [
        ("{}", ""),
        ("null", ""),
        ('{"command": null}', "# header\n---"),
        ("{truncated-json", ""),
    ],
)
def test_cqra_fr_02_probe_profile_usage_and_models_malformed_cli_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    usage_stdout: str,
    models_stdout: str,
) -> None:
    """[CQRA-FR-02] Degrade softly when live `/usage` or `agy models` emits empty or malformed JSON."""

    def fake_run(cmd: list[str], *_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        out = usage_stdout if "/usage" in cmd else models_stdout
        return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")

    monkeypatch.setattr(refresh_session.subprocess, "run", fake_run)
    buckets, models, is_appeal = refresh_session._probe_profile_usage_and_models(
        "/usr/bin/true",
        env={},
        cwd=str(tmp_path),
        timeout=5,
    )
    assert buckets == {"has_groups": False}
    assert models == []
    assert is_appeal is False
