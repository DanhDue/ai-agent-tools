"""Integration and unit tests for dev-config limits/review CLI and quota thresholds.

Covers BDD scenarios:
- URC-HP-02: dev-config limits independently reads and updates all four pass caps across global and project scopes
- URC-HP-03: dev-config review configures shared priority, provider models, and quota thresholds across global and project scopes
- URC-EC-03: Global write emits masking warning when project personas.json overrides the same review or limit key
- URC-ST-01: Resetting project review or limit overrides restores global layer without disturbing sibling keys
- URC-ST-02: Resetting all review overrides in a scope prunes empty review objects cleanly
- URC-FR-02: dev_config models remove refuses deleting an alias referenced by review.providers and rejects invalid CLI flags atomically
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
DEV_CONFIG_SCRIPT = SCRIPTS_DIR / "dev_config.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import agy_dispatch  # noqa: E402
import dev_config  # noqa: E402
import persona_config  # noqa: E402


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _run_dev_config(
    args: list[str],
    *,
    cwd: Path,
    real_home: Path,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["HOME"] = str(real_home)
    env["REAL_HOME"] = str(real_home)
    for key in (
        "AGY_PROFILE",
        "ANTIGRAVITY_PROFILE",
        "AGY_PROGRAMMER_MODEL",
        "AGY_PROGRAMMER_EFFORT",
        "AGY_ASSISTANT_MODEL",
    ):
        env.pop(key, None)
    return subprocess.run(
        [sys.executable, str(DEV_CONFIG_SCRIPT), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _assert_urc_hp_02(tmp_path: Path) -> None:
    real_home = tmp_path / "home"
    project = tmp_path / "repo"
    real_home.mkdir()
    project.mkdir()

    res_global = _run_dev_config(
        [
            "limits",
            "--principal-review",
            "2",
            "--cross-model-review",
            "4",
            "--scope",
            "global",
        ],
        cwd=project,
        real_home=real_home,
    )
    assert res_global.returncode == 0, res_global.stderr

    res_project = _run_dev_config(
        ["limits", "--task-review", "3", "--fix", "0", "--scope", "project"],
        cwd=project,
        real_home=real_home,
    )
    assert res_project.returncode == 0, res_project.stderr

    global_data = json.loads(
        (real_home / ".d3nexus" / "personas.json").read_text(encoding="utf-8")
    )
    assert global_data["max_principal_review_passes"] == 2
    assert global_data["max_cross_model_review_passes"] == 4
    assert "max_task_review_passes" not in global_data
    assert "max_fix_passes" not in global_data

    project_data = json.loads(
        (project / ".agents" / "config" / "personas.json").read_text(encoding="utf-8")
    )
    assert project_data["max_task_review_passes"] == 3
    assert project_data["max_fix_passes"] == 0
    assert "max_principal_review_passes" not in project_data
    assert "max_cross_model_review_passes" not in project_data

    res_limits_json = _run_dev_config(
        ["limits", "--json"], cwd=project, real_home=real_home
    )
    assert res_limits_json.returncode == 0, res_limits_json.stderr
    limits_payload = json.loads(res_limits_json.stdout)
    assert limits_payload == {
        "max_task_review_passes": 3,
        "max_fix_passes": 0,
        "max_principal_review_passes": 2,
        "max_cross_model_review_passes": 4,
        "sources": {
            "max_task_review_passes": "project",
            "max_fix_passes": "project",
            "max_principal_review_passes": "global",
            "max_cross_model_review_passes": "global",
        },
    }

    res_limits_text = _run_dev_config(["limits"], cwd=project, real_home=real_home)
    assert res_limits_text.returncode == 0, res_limits_text.stderr
    assert "max_task_review_passes" in res_limits_text.stdout
    assert "max_principal_review_passes" in res_limits_text.stdout
    assert "global" in res_limits_text.stdout
    assert "project" in res_limits_text.stdout

    res_status_json = _run_dev_config(
        ["status", "--json"], cwd=project, real_home=real_home
    )
    assert res_status_json.returncode == 0, res_status_json.stderr
    status_payload = json.loads(res_status_json.stdout)
    assert status_payload["task_review_limits"] == {
        "max_task_review_passes": 3,
        "max_fix_passes": 0,
    }
    assert status_payload["review_limits"] == limits_payload
    assert status_payload["review"]["provider_priority"] == [
        "claude",
        "codex",
        "kiro",
        "agy",
    ]
    assert status_payload["review"]["last_used_provider"] == "claude"
    assert "providers" in status_payload["review"]
    assert "quota_thresholds" in status_payload["review"]
    assert "sources" in status_payload["review"]

    res_status_text = _run_dev_config(["status"], cwd=project, real_home=real_home)
    assert res_status_text.returncode == 0, res_status_text.stderr
    assert "max_task_review_passes=3" in res_status_text.stdout
    assert "max_fix_passes=0" in res_status_text.stdout
    assert "max_principal_review_passes=2" in res_status_text.stdout
    assert "max_cross_model_review_passes=4" in res_status_text.stdout
    assert "External review priority:" in res_status_text.stdout


def test_urc_hp_02_limits_subcommand_global_and_project(tmp_path: Path) -> None:
    """URC-HP-02: Top-level entry point for V1 RED and limits CLI verification."""
    _assert_urc_hp_02(tmp_path)


class Test_Integration:
    """[Tier C - Integration] Subprocess CLI and threshold tests for dev_config and agy_dispatch."""

    def test_urc_hp_02_limits_subcommand_global_and_project(
        self, tmp_path: Path
    ) -> None:
        """URC-HP-02: dev-config limits independently reads and updates all four pass caps."""
        _assert_urc_hp_02(tmp_path)

    def test_urc_hp_03_review_subcommand_priority_models_and_thresholds(
        self, tmp_path: Path
    ) -> None:
        """URC-HP-03: dev-config review configures priority, provider models, and quota thresholds."""
        real_home = tmp_path / "home"
        project = tmp_path / "repo"
        real_home.mkdir()
        project.mkdir()

        steps = [
            ["review", "priority", "codex,claude,kiro,agy", "--scope", "global"],
            [
                "review",
                "set",
                "agy",
                "--model",
                "gemini-4-carbon-high",
                "--effort",
                "high",
                "--scope",
                "global",
            ],
            [
                "review",
                "set",
                "ollama",
                "--model",
                "qwen2.5-coder:32b",
                "--host",
                "http://127.0.0.1:11434",
                "--scope",
                "project",
            ],
            [
                "review",
                "thresholds",
                "--5h",
                "0.25",
                "--kiro-credits",
                "25.0",
                "--scope",
                "global",
            ],
        ]
        for argv in steps:
            res = _run_dev_config(argv, cwd=project, real_home=real_home)
            assert res.returncode == 0, f"{argv}: {res.stderr}"

        res_status = _run_dev_config(
            ["review", "status", "--json"], cwd=project, real_home=real_home
        )
        assert res_status.returncode == 0, res_status.stderr
        payload = json.loads(res_status.stdout)

        assert payload["provider_priority"] == ["codex", "claude", "kiro", "agy"]
        assert payload["sources"]["provider_priority"] == "global"

        assert payload["providers"]["agy"] == {
            "model": "gemini-4-carbon-high",
            "model_id": "gemini-4-carbon-high",
            "effort": "high",
            "source": "global",
        }
        assert payload["providers"]["ollama"] == {
            "model": "qwen2.5-coder:32b",
            "model_id": "qwen2.5-coder:32b",
            "effort": "high",
            "host": "http://127.0.0.1:11434",
            "source": "project",
        }

        assert payload["quota_thresholds"]["5h_min_fraction"] == 0.25
        assert payload["quota_thresholds"]["kiro_min_credits"] == 25.0
        assert payload["sources"]["quota_thresholds.5h_min_fraction"] == "global"
        assert payload["sources"]["quota_thresholds.kiro_min_credits"] == "global"
        assert payload["sources"]["quota_thresholds.7d_min_fraction"] == "kit"

        dev_th = dev_config._load_quota_thresholds(project, real_home=real_home)
        disp_th = agy_dispatch._load_thresholds(project, real_home=real_home)
        assert dev_th["5h_min_fraction"] == 0.25
        assert dev_th["kiro_min_credits"] == 25.0
        assert disp_th["5h_min_fraction"] == 0.25
        assert disp_th["kiro_min_credits"] == 25.0

        # Verify multi-token priority syntax, fixed-effort alias, additional thresholds, and runtime last_used_provider
        res_multi = _run_dev_config(
            ["review", "priority", "kiro", "codex", "claude", "--scope", "project"],
            cwd=project,
            real_home=real_home,
        )
        assert res_multi.returncode == 0, res_multi.stderr

        res_fixed = _run_dev_config(
            [
                "review",
                "set",
                "agy",
                "--model",
                "orchestrator-argon",
                "--scope",
                "project",
            ],
            cwd=project,
            real_home=real_home,
        )
        assert res_fixed.returncode == 0, res_fixed.stderr

        res_more_th = _run_dev_config(
            [
                "review",
                "thresholds",
                "--7d",
                "0.05",
                "--kiro-frac",
                "0.08",
                "--argon",
                "0.12",
                "--scope",
                "project",
            ],
            cwd=project,
            real_home=real_home,
        )
        assert res_more_th.returncode == 0, res_more_th.stderr

        _write_json(
            project / ".devtool" / "state" / "review_runtime.json",
            {"last_used_provider": "codex"},
        )

        res_status2 = _run_dev_config(
            ["review", "status", "--json"], cwd=project, real_home=real_home
        )
        assert res_status2.returncode == 0, res_status2.stderr
        payload2 = json.loads(res_status2.stdout)
        assert payload2["provider_priority"] == ["kiro", "codex", "claude"]
        assert payload2["sources"]["provider_priority"] == "project"
        assert (
            payload2["providers"]["agy"]["model_id"] == "gemini-pro-orchestrator-g1-pro"
        )
        assert payload2["providers"]["agy"]["effort"] == "none"
        assert payload2["quota_thresholds"]["7d_min_fraction"] == 0.05
        assert payload2["quota_thresholds"]["kiro_min_fraction"] == 0.08
        assert payload2["quota_thresholds"]["agy_argon_min_fraction"] == 0.12
        assert payload2["last_used_provider"] == "codex"

        res_text = _run_dev_config(["review"], cwd=project, real_home=real_home)
        assert res_text.returncode == 0, res_text.stderr
        assert "External review priority:" in res_text.stdout
        assert "Quota thresholds:" in res_text.stdout
        assert "last_used=codex" in res_text.stdout

        # Ollama update without --host preserves existing host in same scope
        res_ollama_keep = _run_dev_config(
            ["review", "set", "ollama", "--model", "llama3:8b", "--scope", "project"],
            cwd=project,
            real_home=real_home,
        )
        assert res_ollama_keep.returncode == 0, res_ollama_keep.stderr
        resolved_after = persona_config.resolve_review_config(
            project, real_home=real_home
        )
        assert resolved_after.providers["ollama"].model_id == "llama3:8b"
        assert resolved_after.providers["ollama"].host == "http://127.0.0.1:11434"

    def test_urc_ec_03_global_write_emits_masking_warning_on_project_override(
        self, tmp_path: Path
    ) -> None:
        """URC-EC-03: Global write warns to stderr when project personas.json masks the same key."""
        real_home = tmp_path / "home"
        project = tmp_path / "repo"
        real_home.mkdir()
        project.mkdir()

        _write_json(
            project / ".agents" / "config" / "personas.json",
            {
                "schema_version": 1,
                "max_principal_review_passes": 1,
                "review": {
                    "provider_priority": ["kiro", "claude"],
                    "providers": {"agy": {"model": "argon", "effort": "low"}},
                    "quota_thresholds": {"5h_min_fraction": 0.40},
                },
            },
        )

        res_lim = _run_dev_config(
            ["limits", "--principal-review", "4", "--scope", "global"],
            cwd=project,
            real_home=real_home,
        )
        assert res_lim.returncode == 0, res_lim.stderr
        assert ".agents/config/personas.json" in res_lim.stderr
        assert "max_principal_review_passes" in res_lim.stderr

        res_prio = _run_dev_config(
            ["review", "priority", "codex,claude", "--scope", "global"],
            cwd=project,
            real_home=real_home,
        )
        assert res_prio.returncode == 0, res_prio.stderr
        assert ".agents/config/personas.json" in res_prio.stderr
        assert "provider_priority" in res_prio.stderr

        res_prov = _run_dev_config(
            [
                "review",
                "set",
                "agy",
                "--model",
                "argon",
                "--effort",
                "high",
                "--scope",
                "global",
            ],
            cwd=project,
            real_home=real_home,
        )
        assert res_prov.returncode == 0, res_prov.stderr
        assert ".agents/config/personas.json" in res_prov.stderr
        assert "review.providers.agy" in res_prov.stderr

        res_th = _run_dev_config(
            ["review", "thresholds", "--5h", "0.25", "--scope", "global"],
            cwd=project,
            real_home=real_home,
        )
        assert res_th.returncode == 0, res_th.stderr
        assert ".agents/config/personas.json" in res_th.stderr
        assert "5h_min_fraction" in res_th.stderr

        global_data = json.loads(
            (real_home / ".d3nexus" / "personas.json").read_text(encoding="utf-8")
        )
        assert global_data["max_principal_review_passes"] == 4
        assert global_data["review"]["provider_priority"] == ["codex", "claude"]

        effective = persona_config.resolve_review_config(project, real_home=real_home)
        assert effective.limits.max_principal_review_passes == 1
        assert effective.limits.sources["max_principal_review_passes"] == "project"
        assert effective.provider_priority == ("kiro", "claude")
        assert effective.sources["provider_priority"] == "project"

    def test_urc_st_01_reset_project_overrides_restores_global_without_disturbing_siblings(
        self, tmp_path: Path
    ) -> None:
        """URC-ST-01: Resetting targeted project overrides restores global while leaving siblings intact."""
        real_home = tmp_path / "home"
        project = tmp_path / "repo"
        real_home.mkdir()
        project.mkdir()

        _write_json(
            real_home / ".d3nexus" / "personas.json",
            {
                "schema_version": 1,
                "max_principal_review_passes": 2,
                "review": {
                    "provider_priority": ["codex", "claude"],
                    "providers": {
                        "claude": {"model": "claude-sonnet", "effort": "high"},
                    },
                    "quota_thresholds": {"5h_min_fraction": 0.22},
                },
            },
        )
        _write_json(
            project / ".agents" / "config" / "personas.json",
            {
                "schema_version": 1,
                "max_principal_review_passes": 1,
                "max_fix_passes": 0,
                "review": {
                    "provider_priority": ["kiro", "agy"],
                    "providers": {
                        "claude": {"model": "claude-opus", "effort": "medium"},
                        "codex": {"model": "gpt-custom", "effort": "low"},
                    },
                    "quota_thresholds": {"5h_min_fraction": 0.35},
                },
            },
        )

        res_lim = _run_dev_config(
            ["limits", "reset", "principal", "--scope", "project"],
            cwd=project,
            real_home=real_home,
        )
        assert res_lim.returncode == 0, res_lim.stderr

        res_prio = _run_dev_config(
            ["review", "reset", "priority", "--scope", "project"],
            cwd=project,
            real_home=real_home,
        )
        assert res_prio.returncode == 0, res_prio.stderr

        cfg = persona_config.resolve_review_config(project, real_home=real_home)
        assert cfg.limits.max_principal_review_passes == 2
        assert cfg.limits.sources["max_principal_review_passes"] == "global"
        assert cfg.limits.max_fix_passes == 0
        assert cfg.limits.sources["max_fix_passes"] == "project"
        assert cfg.provider_priority == ("codex", "claude")
        assert cfg.sources["provider_priority"] == "global"

        # Reset single provider, remaining providers, thresholds, and all limits
        res_one_prov = _run_dev_config(
            ["review", "reset", "claude", "--scope", "project"],
            cwd=project,
            real_home=real_home,
        )
        assert res_one_prov.returncode == 0, res_one_prov.stderr
        cfg_prov = persona_config.resolve_review_config(project, real_home=real_home)
        assert cfg_prov.providers["claude"].model_id == "sonnet"
        assert cfg_prov.providers["claude"].source == "global"
        assert cfg_prov.providers["codex"].model_id == "gpt-custom"
        assert cfg_prov.providers["codex"].source == "project"

        res_all_provs = _run_dev_config(
            ["review", "reset", "providers", "--scope", "project"],
            cwd=project,
            real_home=real_home,
        )
        assert res_all_provs.returncode == 0, res_all_provs.stderr
        res_th = _run_dev_config(
            ["review", "reset", "thresholds", "--scope", "project"],
            cwd=project,
            real_home=real_home,
        )
        assert res_th.returncode == 0, res_th.stderr
        cfg_clean = persona_config.resolve_review_config(project, real_home=real_home)
        assert cfg_clean.providers["codex"].source == "kit"
        assert cfg_clean.quota_thresholds["5h_min_fraction"] == 0.22
        assert cfg_clean.sources["quota_thresholds.5h_min_fraction"] == "global"
        proj_json = json.loads(
            (project / ".agents" / "config" / "personas.json").read_text(
                encoding="utf-8"
            )
        )
        assert "review" not in proj_json

        res_lim_all = _run_dev_config(
            ["limits", "reset", "all", "--scope", "project"],
            cwd=project,
            real_home=real_home,
        )
        assert res_lim_all.returncode == 0, res_lim_all.stderr
        limits_after = persona_config.resolve_review_limits(
            project, real_home=real_home
        )
        assert limits_after.max_fix_passes == 1
        assert limits_after.sources["max_fix_passes"] == "kit"

    def test_urc_st_02_reset_all_review_prunes_empty_objects_idempotently(
        self, tmp_path: Path
    ) -> None:
        """URC-ST-02: Resetting all review overrides prunes empty review object idempotently."""
        real_home = tmp_path / "home"
        project = tmp_path / "repo"
        real_home.mkdir()
        project.mkdir()

        proj_file = project / ".agents" / "config" / "personas.json"
        _write_json(
            proj_file,
            {
                "schema_version": 1,
                "active_preset": "default",
                "review": {
                    "provider_priority": ["kiro", "claude"],
                    "providers": {
                        "claude": {"model": "claude-sonnet", "effort": "medium"}
                    },
                    "quota_thresholds": {"5h_min_fraction": 0.30},
                },
            },
        )

        res1 = _run_dev_config(
            ["review", "reset", "all", "--scope", "project"],
            cwd=project,
            real_home=real_home,
        )
        assert res1.returncode == 0, res1.stderr
        data1 = json.loads(proj_file.read_text(encoding="utf-8"))
        assert "review" not in data1
        assert data1["active_preset"] == "default"

        res2 = _run_dev_config(
            ["review", "reset", "all", "--scope", "project"],
            cwd=project,
            real_home=real_home,
        )
        assert res2.returncode == 0, res2.stderr
        data2 = json.loads(proj_file.read_text(encoding="utf-8"))
        assert data2 == data1

        # Resetting a non-existent scope file is also idempotent and creates no file
        res_missing_rev = _run_dev_config(
            ["review", "reset", "all", "--scope", "global"],
            cwd=project,
            real_home=real_home,
        )
        assert res_missing_rev.returncode == 0, res_missing_rev.stderr
        assert not (real_home / ".d3nexus" / "personas.json").exists()

        res_missing_lim = _run_dev_config(
            ["limits", "reset", "all", "--scope", "global"],
            cwd=project,
            real_home=real_home,
        )
        assert res_missing_lim.returncode == 0, res_missing_lim.stderr
        assert not (real_home / ".d3nexus" / "personas.json").exists()

    def test_urc_fr_02_models_remove_guard_and_atomic_validation_rejection(
        self, tmp_path: Path
    ) -> None:
        """URC-FR-02: models remove blocks aliases referenced by review.providers and invalid CLI flags fail atomically."""
        real_home = tmp_path / "home"
        project = tmp_path / "repo"
        real_home.mkdir()
        project.mkdir()

        res_add = _run_dev_config(
            [
                "models",
                "add",
                "custom-claude",
                "--cli",
                "claude",
                "--id",
                "claude-custom-1",
                "--efforts",
                "medium,high",
                "--scope",
                "global",
            ],
            cwd=project,
            real_home=real_home,
        )
        assert res_add.returncode == 0, res_add.stderr

        res_set = _run_dev_config(
            [
                "review",
                "set",
                "claude",
                "--model",
                "custom-claude",
                "--effort",
                "high",
                "--scope",
                "global",
            ],
            cwd=project,
            real_home=real_home,
        )
        assert res_set.returncode == 0, res_set.stderr

        global_file = real_home / ".d3nexus" / "personas.json"
        before_bytes = global_file.read_bytes()

        res_rm = _run_dev_config(
            ["models", "remove", "custom-claude", "--scope", "global"],
            cwd=project,
            real_home=real_home,
        )
        assert res_rm.returncode == 1
        assert "review.providers.claude.model" in res_rm.stderr
        assert global_file.read_bytes() == before_bytes

        invalid_invocations = [
            [
                "review",
                "set",
                "ollama",
                "--model",
                "gemma4",
                "--host",
                "ftp://bad-host",
                "--scope",
                "global",
            ],
            [
                "review",
                "set",
                "claude",
                "--model",
                "opus",
                "--host",
                "http://localhost:11434",
                "--scope",
                "global",
            ],
            [
                "review",
                "set",
                "claude",
                "--model",
                "codex-gpt",
                "--effort",
                "high",
                "--scope",
                "global",
            ],
            [
                "review",
                "set",
                "agy",
                "--model",
                "argon",
                "--effort",
                "bogus",
                "--scope",
                "global",
            ],
            [
                "review",
                "set",
                "agy",
                "--model",
                "orchestrator-argon",
                "--effort",
                "high",
                "--scope",
                "global",
            ],
            [
                "review",
                "set",
                "unknown-provider",
                "--model",
                "foo",
                "--scope",
                "global",
            ],
            ["review", "priority", "claude,claude", "--scope", "global"],
            ["review", "priority", "ollama", "--scope", "global"],
            ["review", "thresholds", "--scope", "global"],
            ["review", "thresholds", "--5h", "1.5", "--scope", "global"],
            ["review", "thresholds", "--kiro-credits", "-1", "--scope", "global"],
            ["review", "reset", "bogus", "--scope", "global"],
            ["review", "status", "--scope", "global"],
            ["limits", "--principal-review", "0", "--scope", "global"],
            ["limits", "--cross-model-review", "0", "--scope", "global"],
            ["limits", "--task-review", "0", "--scope", "global"],
            ["limits", "--fix", "-1", "--scope", "global"],
            ["limits", "--json", "--scope", "project"],
            ["limits", "--principal-review", "2", "--json"],
            ["limits", "reset", "bogus", "--scope", "global"],
        ]
        for bad_argv in invalid_invocations:
            res_bad = _run_dev_config(bad_argv, cwd=project, real_home=real_home)
            assert res_bad.returncode == 1, f"Expected exit 1 for {bad_argv}"
            assert global_file.read_bytes() == before_bytes, (
                f"Global file mutated on invalid argv {bad_argv}"
            )
            assert list((real_home / ".d3nexus").glob("*.tmp")) == []

        # Removing the reference allows models remove to succeed
        res_unpin = _run_dev_config(
            ["review", "reset", "claude", "--scope", "global"],
            cwd=project,
            real_home=real_home,
        )
        assert res_unpin.returncode == 0, res_unpin.stderr
        res_rm_ok = _run_dev_config(
            ["models", "remove", "custom-claude", "--scope", "global"],
            cwd=project,
            real_home=real_home,
        )
        assert res_rm_ok.returncode == 0, res_rm_ok.stderr


def test_direct_module_helpers_and_legacy_runtime_fallback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Direct module unit tests for coverage on dev_config handlers and agy_dispatch._load_thresholds."""
    real_home = tmp_path / "home"
    project = tmp_path / "repo"
    real_home.mkdir()
    project.mkdir()

    # Legacy review_config.json last_used_provider fallback when review_runtime.json absent
    _write_json(
        project / ".devtool" / "review_config.json",
        {"last_used_provider": "kiro", "quota_thresholds": {"5h_min_fraction": 0.33}},
    )
    assert dev_config.cmd_status(project, json_output=True, real_home=real_home) == 0
    status_out = json.loads(capsys.readouterr().out)
    assert status_out["review"]["last_used_provider"] == "kiro"
    assert status_out["review"]["quota_thresholds"]["5h_min_fraction"] == 0.33
    assert status_out["warnings"]

    assert (
        dev_config._load_quota_thresholds(project, None, real_home=real_home)[
            "5h_min_fraction"
        ]
        == 0.33
    )
    assert (
        agy_dispatch._load_thresholds(project, real_home=real_home)["5h_min_fraction"]
        == 0.33
    )

    # Corrupted review_runtime.json falls back cleanly to legacy review_config.json
    rt_file = project / ".devtool" / "state" / "review_runtime.json"
    rt_file.parent.mkdir(parents=True, exist_ok=True)
    rt_file.write_text("{broken", encoding="utf-8")
    assert (
        dev_config.cmd_review_status(project, json_output=True, real_home=real_home)
        == 0
    )
    rev_out = json.loads(capsys.readouterr().out)
    assert rev_out["last_used_provider"] == "kiro"

    # Direct calls to cmd_limits, cmd_limits_reset, cmd_review_* handlers
    assert (
        dev_config.cmd_limits(
            project,
            principal_review=2,
            cross_model_review=4,
            scope="global",
            real_home=real_home,
        )
        == 0
    )
    capsys.readouterr()
    assert dev_config.cmd_limits(project, json_output=True, real_home=real_home) == 0
    lim_json = json.loads(capsys.readouterr().out)
    assert lim_json["max_principal_review_passes"] == 2
    assert lim_json["max_cross_model_review_passes"] == 4

    assert (
        dev_config.cmd_review_priority(
            project,
            providers=["codex", "claude"],
            scope="global",
            real_home=real_home,
        )
        == 0
    )
    assert (
        dev_config.cmd_review_set(
            project,
            provider="agy",
            model="argon",
            effort="medium",
            scope="global",
            real_home=real_home,
        )
        == 0
    )
    assert (
        dev_config.cmd_review_thresholds(
            project,
            five_h=0.2,
            seven_d=0.04,
            kiro_frac=0.06,
            kiro_credits=20.0,
            argon=0.15,
            scope="global",
            real_home=real_home,
        )
        == 0
    )
    capsys.readouterr()
    assert (
        dev_config._load_quota_thresholds(project, real_home=real_home)[
            "5h_min_fraction"
        ]
        == 0.2
    )
    assert (
        agy_dispatch._load_thresholds(project, real_home=real_home)[
            "agy_argon_min_fraction"
        ]
        == 0.15
    )

    assert (
        dev_config.cmd_limits_reset(
            project, target="principal", scope="global", real_home=real_home
        )
        == 0
    )
    assert (
        dev_config.cmd_review_reset(
            project, target="all", scope="global", real_home=real_home
        )
        == 0
    )
    capsys.readouterr()
