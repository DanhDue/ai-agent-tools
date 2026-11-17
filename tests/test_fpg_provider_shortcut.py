"""Tests for the dev-config --provider quick-setup shortcut and validation.

Covers BDD Scenarios:
- FPG-HP-10: dev-config --provider binds all three personas to one provider's models
- FPG-EC-06: Invalid --provider use is rejected and an override that masks the provider is reported
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONA_CONFIG_SCRIPT = REPO_ROOT / "scripts" / "persona_config.py"
DEV_CONFIG_SCRIPT = REPO_ROOT / "scripts" / "dev_config.py"

_EXPECTED_PROVIDERS: list[
    tuple[str, str, dict[str, tuple[str, str, str, str, str | None]]]
] = [
    (
        "claude",
        "all-claude",
        {
            "ai_architect_reviewer": ("claude-opus", "claude", "opus", "high", None),
            "orchestrator": ("claude-sonnet", "claude", "sonnet", "high", None),
            "programmer": ("claude-sonnet", "claude", "sonnet", "high", None),
        },
    ),
    (
        "codex",
        "all-codex",
        {
            "ai_architect_reviewer": (
                "codex-gpt",
                "codex",
                "gpt-6.1-sol",
                "high",
                None,
            ),
            "orchestrator": ("codex-terra", "codex", "gpt-6.1-terra", "medium", None),
            "programmer": ("codex-terra", "codex", "gpt-6.1-terra", "medium", None),
        },
    ),
    (
        "agy",
        "default",
        {
            "ai_architect_reviewer": (
                "argon",
                "agy",
                "gemini-4-argon-high",
                "high",
                "claude-opus",
            ),
            "orchestrator": (
                "hydrogen",
                "agy",
                "gemini-4-hydrogen-high",
                "high",
                "claude-sonnet",
            ),
            "programmer": (
                "hydrogen",
                "agy",
                "gemini-4-hydrogen-xhigh",
                "xhigh",
                "claude-sonnet",
            ),
        },
    ),
]


def _load_module(name: str, path: Path) -> ModuleType:
    """Load a module by path via importlib so RED phase fails as test failure."""
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    if not path.is_file():
        pytest.fail(f"Expected module does not exist yet: {path}")
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        pytest.fail(f"Failed to create module spec for {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def pc_mod() -> ModuleType:
    """Load persona_config module dynamically."""
    return _load_module("persona_config", PERSONA_CONFIG_SCRIPT)


@pytest.fixture(scope="module")
def dc_mod() -> ModuleType:
    """Load dev_config module dynamically."""
    return _load_module("dev_config", DEV_CONFIG_SCRIPT)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_stub_bin(bin_dir: Path, names: tuple[str, ...]) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        exe = bin_dir / name
        exe.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        exe.chmod(0o755)


def _run_cli(
    args: list[str],
    *,
    cwd: Path,
    real_home: Path,
    path_dir: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    if not DEV_CONFIG_SCRIPT.is_file():
        pytest.fail(f"Expected CLI script does not exist yet: {DEV_CONFIG_SCRIPT}")
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
    if path_dir is not None:
        env["PATH"] = str(path_dir)
    return subprocess.run(
        [sys.executable, str(DEV_CONFIG_SCRIPT), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _setup_workspace(tmp_path: Path) -> tuple[Path, Path, Path]:
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    real_home.mkdir()
    project.mkdir()
    _make_stub_bin(bin_dir, ("agy", "claude", "codex"))
    return real_home, project, bin_dir


@pytest.mark.parametrize(
    ("provider", "expected_preset", "expected_bindings"),
    _EXPECTED_PROVIDERS,
    ids=[item[0] for item in _EXPECTED_PROVIDERS],
)
def test_fpg_hp_10_provider_shortcut_binds_all_personas(
    tmp_path: Path,
    dc_mod: ModuleType,
    provider: str,
    expected_preset: str,
    expected_bindings: dict[str, tuple[str, str, str, str, str | None]],
) -> None:
    """FPG-HP-10: dev-config --provider binds all three personas in global and project scope."""
    assert hasattr(dc_mod, "PROVIDER_PRESETS")
    assert dc_mod.PROVIDER_PRESETS[provider] == expected_preset

    real_home, project, bin_dir = _setup_workspace(tmp_path)

    res = _run_cli(
        ["--provider", provider],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res.returncode == 0, res.stderr
    assert res.stderr == ""

    expected_lines = [f"active_preset: {expected_preset} (global)"]
    for persona in ("ai_architect_reviewer", "orchestrator", "programmer"):
        _, cli, model_id, effort, _ = expected_bindings[persona]
        expected_lines.append(f"{persona}: {cli} {model_id} {effort}")
    assert res.stdout.splitlines() == expected_lines

    global_cfg_path = real_home / ".d3nexus" / "personas.json"
    global_data = json.loads(global_cfg_path.read_text(encoding="utf-8"))
    assert global_data == {"schema_version": 1, "active_preset": expected_preset}

    for persona, (alias, cli, model_id, effort, fallback) in expected_bindings.items():
        res_resolve = _run_cli(
            ["resolve", persona, "--format", "json"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_resolve.returncode == 0, res_resolve.stderr
        resolved = json.loads(res_resolve.stdout)
        assert resolved["alias"] == alias
        assert resolved["cli"] == cli
        assert resolved["model_id"] == model_id
        assert resolved["effort"] == effort
        assert resolved["fallback_alias"] == fallback
        assert resolved["sources"]["model"] == "global"
        assert resolved["sources"]["effort"] == "global"

    # Now switch global to a distinct baseline preset and test --scope project isolation.
    baseline_provider = "agy" if provider != "agy" else "claude"
    baseline_preset = dc_mod.PROVIDER_PRESETS[baseline_provider]
    assert (
        _run_cli(
            ["--provider", baseline_provider],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        ).returncode
        == 0
    )

    res_proj = _run_cli(
        ["--provider", provider, "--scope", "project"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res_proj.returncode == 0, res_proj.stderr
    assert (
        res_proj.stdout.splitlines()[0] == f"active_preset: {expected_preset} (project)"
    )

    project_data = json.loads(
        (project / ".agents" / "config" / "personas.json").read_text(encoding="utf-8")
    )
    global_after = json.loads(global_cfg_path.read_text(encoding="utf-8"))
    assert project_data == {"schema_version": 1, "active_preset": expected_preset}
    assert global_after == {"schema_version": 1, "active_preset": baseline_preset}


class Test_Integration:
    """[Tier C - Integration] Subprocess CLI integration tests for dev_config.py --provider."""

    def test_fpg_hp_10_sequential_provider_switches_and_catalogue(
        self, tmp_path: Path
    ) -> None:
        """FPG-HP-10: Sequential --provider switches, project scope, models and status integration."""
        real_home, project, bin_dir = _setup_workspace(tmp_path)

        res_models = _run_cli(
            ["models", "--json"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_models.returncode == 0, res_models.stderr
        by_alias = {
            item["alias"]: item for item in json.loads(res_models.stdout)["models"]
        }
        assert by_alias["codex-terra"]["cli"] == "codex"
        assert by_alias["codex-terra"]["id"] == "gpt-6.1-terra"
        assert by_alias["codex-terra"]["efforts"] == ["medium", "high", "xhigh"]
        assert by_alias["codex-terra"]["quota_pool"] == "provider"

        for prov, preset, checks in _EXPECTED_PROVIDERS:
            res = _run_cli(
                ["--provider", prov], cwd=project, real_home=real_home, path_dir=bin_dir
            )
            assert res.returncode == 0, res.stderr
            assert (
                json.loads(
                    (real_home / ".d3nexus" / "personas.json").read_text(
                        encoding="utf-8"
                    )
                )["active_preset"]
                == preset
            )
            for persona, (_, cli, model_id, effort, _) in checks.items():
                resolved = json.loads(
                    _run_cli(
                        ["resolve", persona, "--format", "json"],
                        cwd=project,
                        real_home=real_home,
                        path_dir=bin_dir,
                    ).stdout
                )
                assert resolved["cli"] == cli
                assert resolved["model_id"] == model_id
                assert resolved["effort"] == effort

        # With global at 'default' (agy), setting --provider claude --scope project keeps global untouched.
        res_proj = _run_cli(
            ["--provider", "claude", "--scope", "project"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_proj.returncode == 0, res_proj.stderr
        assert (
            json.loads(
                (project / ".agents" / "config" / "personas.json").read_text(
                    encoding="utf-8"
                )
            )["active_preset"]
            == "all-claude"
        )
        assert (
            json.loads(
                (real_home / ".d3nexus" / "personas.json").read_text(encoding="utf-8")
            )["active_preset"]
            == "default"
        )

        res_status = _run_cli(
            ["status", "--json"], cwd=project, real_home=real_home, path_dir=bin_dir
        )
        assert res_status.returncode == 0, res_status.stderr
        status_payload = json.loads(res_status.stdout)
        assert status_payload["active_preset"] == "all-claude"
        assert set(status_payload["presets"]) >= {"default", "all-claude", "all-codex"}


def test_fpg_ec_06_invalid_provider_use_and_masked_override_warning(
    tmp_path: Path, pc_mod: ModuleType
) -> None:
    """FPG-EC-06: Invalid --provider use is rejected and masked override prints a warning."""
    real_home, project, bin_dir = _setup_workspace(tmp_path)
    global_cfg = real_home / ".d3nexus" / "personas.json"
    project_cfg = project / ".agents" / "config" / "personas.json"
    _write_json(global_cfg, {"schema_version": 1, "active_preset": "default"})
    _write_json(
        project_cfg,
        {
            "schema_version": 1,
            "overrides": {"programmer": {"model": "hydrogen", "effort": "high"}},
        },
    )
    before_global_sha = _sha256(global_cfg)
    before_project_sha = _sha256(project_cfg)

    for bad_args, expected_token in [
        (["--provider", "gemini"], "gemini"),
        (["--provider", "claude", "status"], "status"),
    ]:
        res_bad = _run_cli(bad_args, cwd=project, real_home=real_home, path_dir=bin_dir)
        assert res_bad.returncode == 1
        assert expected_token in (res_bad.stdout + res_bad.stderr)
        assert _sha256(global_cfg) == before_global_sha
        assert _sha256(project_cfg) == before_project_sha

    res_masked = _run_cli(
        ["--provider", "claude"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res_masked.returncode == 0, res_masked.stderr
    assert res_masked.stdout.splitlines() == [
        "active_preset: all-claude (global)",
        "ai_architect_reviewer: claude opus high",
        "orchestrator: claude sonnet high",
        "programmer: agy gemini-4-hydrogen-high high",
    ]
    assert (
        'warning: programmer is still bound to hydrogen high by the project layer; run "dev_config.py reset programmer --scope project"'
        in res_masked.stderr
    )

    prog = pc_mod.resolve_persona("programmer", project, real_home=real_home)
    assert prog.model_id == "gemini-4-hydrogen-high"
    assert prog.sources["effort"] == "project"

    arch = pc_mod.resolve_persona("ai_architect_reviewer", project, real_home=real_home)
    assert arch.model_id == "opus"


@pytest.mark.parametrize(
    ("args", "rejected_token"),
    [
        (["--provider", "kiro"], "kiro"),
        (["--provider", "status"], "status"),
        (["--provider", "claude", "--models"], "models"),
        (["--provider", "claude", "--low-quota", "on"], "low-quota"),
        (["--provider", "claude", "resolve", "programmer"], "resolve"),
        (["--provider", "claude", "--scope", "workspace"], "workspace"),
        (["--provider"], "--provider"),
    ],
)
def test_fpg_ec_06_rejected_provider_invocations_leave_files_unchanged(
    tmp_path: Path, args: list[str], rejected_token: str
) -> None:
    """FPG-EC-06: All invalid --provider forms exit 1 without mutating configuration."""
    real_home, project, bin_dir = _setup_workspace(tmp_path)
    global_cfg = real_home / ".d3nexus" / "personas.json"
    _write_json(global_cfg, {"schema_version": 1, "active_preset": "default"})
    before_sha = _sha256(global_cfg)

    res = _run_cli(args, cwd=project, real_home=real_home, path_dir=bin_dir)
    assert res.returncode == 1
    assert rejected_token in (res.stdout + res.stderr)
    assert _sha256(global_cfg) == before_sha


def test_fpg_ec_06_preserves_other_sections_and_warns_for_preset_or_effort_masking(
    tmp_path: Path, dc_mod: ModuleType, pc_mod: ModuleType
) -> None:
    """FPG-EC-06: --provider preserves non-preset fields and warns on higher-layer active_preset/effort masks."""
    real_home, project, bin_dir = _setup_workspace(tmp_path)
    global_cfg = real_home / ".d3nexus" / "personas.json"
    _write_json(
        global_cfg,
        {
            "schema_version": 1,
            "active_preset": "default",
            "models": {
                "custom-codex": {
                    "cli": "codex",
                    "id": "gpt-custom",
                    "efforts": ["high"],
                }
            },
            "overrides": {"orchestrator": {"model": "argon", "effort": "medium"}},
            "checkpoint_policy": {"max_orchestrator_turns_before_checkpoint": 6},
            "low_quota": {
                "p1": {"enabled": True, "expires_at": "2099-01-01T00:00:00Z"}
            },
        },
    )

    with pytest.raises(pc_mod.PersonaConfigError, match="gemini"):
        dc_mod.cmd_provider(project, provider="gemini", real_home=real_home)

    # Global override masks orchestrator when applying --provider claude globally; other fields stay intact.
    res_global_mask = _run_cli(
        ["--provider", "claude"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res_global_mask.returncode == 0, res_global_mask.stderr
    assert (
        'warning: orchestrator is still bound to argon medium by the global layer; run "dev_config.py reset orchestrator --scope global"'
        in res_global_mask.stderr
    )
    global_after = json.loads(global_cfg.read_text(encoding="utf-8"))
    assert global_after["active_preset"] == "all-claude"
    assert global_after["models"] == {
        "custom-codex": {"cli": "codex", "id": "gpt-custom", "efforts": ["high"]}
    }
    assert global_after["overrides"] == {
        "orchestrator": {"model": "argon", "effort": "medium"}
    }
    assert global_after["checkpoint_policy"] == {
        "max_orchestrator_turns_before_checkpoint": 6
    }
    assert global_after["low_quota"] == {
        "p1": {"enabled": True, "expires_at": "2099-01-01T00:00:00Z"}
    }

    # Project active_preset masking global --provider codex warns for all three personas.
    _write_json(global_cfg, {"schema_version": 1, "active_preset": "default"})
    _write_json(
        project / ".agents" / "config" / "personas.json",
        {"schema_version": 1, "active_preset": "all-hydrogen"},
    )
    res_proj_preset_mask = _run_cli(
        ["--provider", "codex"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res_proj_preset_mask.returncode == 0, res_proj_preset_mask.stderr
    for persona, alias, effort in (
        ("ai_architect_reviewer", "hydrogen", "xhigh"),
        ("orchestrator", "hydrogen", "high"),
        ("programmer", "hydrogen", "xhigh"),
    ):
        assert (
            f"warning: {persona} is still bound to {alias} {effort} by the project layer; "
            f'run "dev_config.py reset {persona} --scope project"'
        ) in res_proj_preset_mask.stderr

    # Effort-only global override masking --provider claude --scope project reports the 'global' layer.
    _write_json(
        global_cfg,
        {"schema_version": 1, "overrides": {"programmer": {"effort": "medium"}}},
    )
    _write_json(
        project / ".agents" / "config" / "personas.json",
        {"schema_version": 1},
    )
    res_effort_mask = _run_cli(
        ["--provider", "claude", "--scope", "project"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res_effort_mask.returncode == 0, res_effort_mask.stderr
    assert (
        'warning: programmer is still bound to claude-sonnet medium by the global layer; run "dev_config.py reset programmer --scope global"'
        in res_effort_mask.stderr
    )
