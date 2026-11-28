"""Tests for Antigravity orchestrator aliases and effortless model support."""

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


def _load_module(name: str, path: Path) -> ModuleType:
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _make_stub_bin(bin_dir: Path, names: tuple[str, ...]) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        exe = bin_dir / name
        exe.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        exe.chmod(0o755)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


EXPECTED_PRESETS: dict[str, dict[str, dict[str, str]]] = {
    "default": {
        "ai_architect_reviewer": {
            "model": "argon",
            "effort": "high",
            "fallback_model": "claude-opus",
        },
        "orchestrator": {
            "model": "hydrogen",
            "effort": "high",
            "fallback_model": "claude-sonnet",
        },
        "programmer": {
            "model": "hydrogen",
            "effort": "xhigh",
            "fallback_model": "claude-sonnet",
        },
    },
    "gemini-saver": {
        "ai_architect_reviewer": {
            "model": "argon",
            "effort": "medium",
            "fallback_model": "claude-opus",
        },
        "orchestrator": {
            "model": "hydrogen",
            "effort": "medium",
            "fallback_model": "claude-sonnet",
        },
        "programmer": {
            "model": "hydrogen",
            "effort": "high",
            "fallback_model": "claude-sonnet",
        },
    },
    "claude-hybrid": {
        "ai_architect_reviewer": {
            "model": "claude-opus",
            "effort": "high",
            "fallback_model": "argon",
        },
        "orchestrator": {
            "model": "hydrogen",
            "effort": "high",
            "fallback_model": "claude-sonnet",
        },
        "programmer": {
            "model": "hydrogen",
            "effort": "xhigh",
            "fallback_model": "claude-sonnet",
        },
    },
    "all-hydrogen": {
        "ai_architect_reviewer": {
            "model": "hydrogen",
            "effort": "xhigh",
            "fallback_model": "claude-opus",
        },
        "orchestrator": {
            "model": "hydrogen",
            "effort": "high",
            "fallback_model": "claude-sonnet",
        },
        "programmer": {
            "model": "hydrogen",
            "effort": "xhigh",
            "fallback_model": "claude-sonnet",
        },
    },
    "codex-kiro": {
        "ai_architect_reviewer": {
            "model": "kiro-opus",
            "effort": "high",
            "fallback_model": "claude-opus",
        },
        "orchestrator": {
            "model": "codex-gpt",
            "effort": "medium",
            "fallback_model": "claude-sonnet",
        },
        "programmer": {
            "model": "codex-gpt",
            "effort": "xhigh",
            "fallback_model": "claude-sonnet",
        },
    },
    "all-claude": {
        "ai_architect_reviewer": {"model": "claude-opus", "effort": "high"},
        "orchestrator": {"model": "claude-sonnet", "effort": "high"},
        "programmer": {"model": "claude-sonnet", "effort": "high"},
    },
    "all-codex": {
        "ai_architect_reviewer": {"model": "codex-gpt", "effort": "high"},
        "orchestrator": {"model": "codex-terra", "effort": "medium"},
        "programmer": {"model": "codex-terra", "effort": "medium"},
    },
}


@pytest.mark.parametrize(
    ("alias", "expected_id", "expected_efforts", "expected_pool"),
    [
        (
            "neon",
            "gemini-4-neon-{effort}",
            ["low", "medium", "high", "xhigh"],
            "gemini5h",
        ),
        ("orchestrator-neon", "gemini-pro-orchestrator-neon", ["none"], "gemini5h"),
        (
            "orchestrator-argon",
            "gemini-pro-orchestrator-g1-pro",
            ["none"],
            "argonWeekly",
        ),
    ],
)
def test_kit_defaults_include_neon_and_orchestrator_aliases(
    tmp_path: Path,
    alias: str,
    expected_id: str,
    expected_efforts: list[str],
    expected_pool: str,
) -> None:
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    project.mkdir()

    cfg = pc.load_persona_config(project, real_home=real_home)
    assert cfg["presets"] == EXPECTED_PRESETS
    entry = cfg["models"][alias]
    assert entry["cli"] == "agy"
    assert entry["id"] == expected_id
    assert entry["efforts"] == expected_efforts
    assert pc.derive_quota_pool(entry, alias) == expected_pool


@pytest.mark.parametrize(
    ("entry", "alias", "expected_pool"),
    [
        (
            {"cli": "agy", "id": "gemini-pro-orchestrator-g1-pro", "efforts": ["none"]},
            "orchestrator-argon",
            "argonWeekly",
        ),
        (
            {"cli": "agy", "id": "gemini-pro-orchestrator-neon", "efforts": ["none"]},
            "orchestrator-neon",
            "gemini5h",
        ),
        (
            {
                "cli": "agy",
                "id": "gemini-4-neon-{effort}",
                "efforts": ["low", "medium", "high", "xhigh"],
            },
            "neon",
            "gemini5h",
        ),
    ],
)
def test_derive_quota_pool_infers_g1_pro_as_argon_weekly(
    entry: dict[str, Any],
    alias: str,
    expected_pool: str,
) -> None:
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    assert pc.derive_quota_pool(entry, alias) == expected_pool


@pytest.mark.parametrize(
    ("exit_code", "stderr", "expected_status"),
    [
        (
            1,
            'error: invalid model selection (--model "gemini-pro-orchestrator-argon" --effort ""): model gemini-pro-orchestrator-argon is not recognized as a known model or custom model in settings',
            "model_unavailable",
        ),
        (
            1,
            "model foo is not recognized as a known model",
            "model_unavailable",
        ),
        (
            1,
            "AssertionError: test failed",
            "task_failure",
        ),
    ],
)
def test_classify_dispatch_failure_recognizes_invalid_model_selection(
    exit_code: int,
    stderr: str,
    expected_status: str,
) -> None:
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    assert pc.classify_dispatch_failure(exit_code, "", stderr) == expected_status


@pytest.mark.parametrize(
    ("model_entry", "error_fragment"),
    [
        (
            {
                "cli": "agy",
                "id": "gemini-pro-orchestrator-neon",
                "efforts": ["none", "high"],
            },
            "cannot be combined",
        ),
        (
            {
                "cli": "agy",
                "id": "gemini-pro-orchestrator-neon",
                "efforts": ["low", "none"],
            },
            "cannot be combined",
        ),
        (
            {"cli": "agy", "id": "gemini-pro-{effort}", "efforts": ["none"]},
            "{effort}",
        ),
    ],
)
def test_validate_model_entry_rejects_invalid_none_combinations(
    tmp_path: Path,
    model_entry: dict[str, Any],
    error_fragment: str,
) -> None:
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    _write_json(
        project / ".agents" / "config" / "personas.json",
        {"schema_version": 1, "models": {"bad-model": model_entry}},
    )

    with pytest.raises(pc.PersonaConfigError) as exc_info:
        pc.load_persona_config(project, real_home=real_home)
    assert error_fragment in str(exc_info.value)


@pytest.mark.parametrize(
    ("cli", "model_id", "effort", "mode", "expected_argv"),
    [
        (
            "agy",
            "gemini-pro-orchestrator-g1-pro",
            "none",
            "read-only",
            [
                "agy",
                "--sandbox",
                "--mode",
                "plan",
                "--model",
                "gemini-pro-orchestrator-g1-pro",
            ],
        ),
        (
            "agy",
            "gemini-pro-orchestrator-g1-pro",
            "none",
            "write",
            [
                "agy",
                "--model",
                "gemini-pro-orchestrator-g1-pro",
                "--mode",
                "auto",
            ],
        ),
        (
            "agy",
            "gemini-pro-orchestrator-neon",
            "none",
            "read-only",
            [
                "agy",
                "--sandbox",
                "--mode",
                "plan",
                "--model",
                "gemini-pro-orchestrator-neon",
            ],
        ),
        (
            "agy",
            "gemini-4-neon-high",
            "high",
            "read-only",
            [
                "agy",
                "--sandbox",
                "--mode",
                "plan",
                "--model",
                "gemini-4-neon-high",
                "--effort",
                "high",
            ],
        ),
        (
            "agy",
            "gemini-4-neon-high",
            "high",
            "write",
            [
                "agy",
                "--model",
                "gemini-4-neon-high",
                "--effort",
                "high",
                "--mode",
                "auto",
            ],
        ),
        (
            "claude",
            "opus",
            "none",
            "read-only",
            ["claude", "-p", "--model", "opus", "--permission-mode", "plan"],
        ),
        (
            "claude",
            "opus",
            "none",
            "write",
            ["claude", "-p", "--model", "opus", "--dangerously-skip-permissions"],
        ),
        (
            "kiro",
            "claude-sonnet-5.5",
            "none",
            "write",
            [
                "kiro-cli",
                "chat",
                "--no-interactive",
                "--trust-all-tools",
                "--wrap",
                "never",
                "--model",
                "claude-sonnet-5.5",
            ],
        ),
        (
            "codex",
            "gpt-6.1-sol",
            "none",
            "read-only",
            [
                "codex",
                "exec",
                "--sandbox",
                "read-only",
                "--model",
                "gpt-6.1-sol",
                "-c",
                "model_reasoning_effort=none",
                "-",
            ],
        ),
    ],
)
def test_build_dispatch_argv_handles_effort_none_per_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cli: str,
    model_id: str,
    effort: str,
    mode: str,
    expected_argv: list[str],
) -> None:
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    bin_dir = tmp_path / "bin"
    _make_stub_bin(bin_dir, ("agy", "claude", "codex", "kiro-cli"))
    monkeypatch.setenv("PATH", str(bin_dir))

    binding = pc.PersonaBinding(
        persona="orchestrator",
        alias="test-alias",
        cli=cli,
        model_id=model_id,
        effort=effort,
        quota_pool="gemini5h",
        fallback_alias=None,
        sources={"model": "global", "effort": "global", "fallback_model": "kit"},
    )
    argv = pc.build_dispatch_argv(binding, mode)
    assert argv == expected_argv
    if cli in ("agy", "claude", "kiro") and effort == "none":
        assert "--effort" not in argv


def _run_cli(
    args: list[str],
    *,
    cwd: Path,
    real_home: Path,
    path_dir: Path | None = None,
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


@pytest.mark.parametrize(
    ("set_args", "expected_alias", "expected_model_id", "expected_pool"),
    [
        (
            ["set", "orchestrator", "orchestrator-argon"],
            "orchestrator-argon",
            "gemini-pro-orchestrator-g1-pro",
            "argonWeekly",
        ),
        (
            ["set", "orchestrator", "orchestrator-argon", "none"],
            "orchestrator-argon",
            "gemini-pro-orchestrator-g1-pro",
            "argonWeekly",
        ),
        (
            ["set", "orchestrator", "gemini-pro-orchestrator-g1-pro"],
            "orchestrator-argon",
            "gemini-pro-orchestrator-g1-pro",
            "argonWeekly",
        ),
        (
            ["set", "orchestrator", "orchestrator-neon"],
            "orchestrator-neon",
            "gemini-pro-orchestrator-neon",
            "gemini5h",
        ),
        (
            [
                "set",
                "orchestrator",
                "--provider",
                "agy",
                "--model",
                "orchestrator-argon",
            ],
            "orchestrator-argon",
            "gemini-pro-orchestrator-g1-pro",
            "argonWeekly",
        ),
        (
            [
                "set",
                "orchestrator",
                "--provider",
                "agy",
                "--model",
                "gemini-pro-orchestrator-g1-pro",
            ],
            "orchestrator-argon",
            "gemini-pro-orchestrator-g1-pro",
            "argonWeekly",
        ),
    ],
)
def test_cli_set_and_resolve_effortless_models_end_to_end(
    tmp_path: Path,
    set_args: list[str],
    expected_alias: str,
    expected_model_id: str,
    expected_pool: str,
) -> None:
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    real_home.mkdir()
    project.mkdir()
    _make_stub_bin(bin_dir, ("agy", "claude", "codex", "kiro-cli"))

    res_set = _run_cli(set_args, cwd=project, real_home=real_home, path_dir=bin_dir)
    assert res_set.returncode == 0, res_set.stderr

    res_json = _run_cli(
        ["resolve", "orchestrator", "--format", "json"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res_json.returncode == 0, res_json.stderr
    resolved = json.loads(res_json.stdout)
    assert resolved["alias"] == expected_alias
    assert resolved["model_id"] == expected_model_id
    assert resolved["effort"] == "none"
    assert resolved["quota_pool"] == expected_pool

    for mode in ("read-only", "write"):
        res_argv = _run_cli(
            ["resolve", "orchestrator", "--format", "argv", "--mode", mode],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_argv.returncode == 0, res_argv.stderr
        assert "--effort" not in res_argv.stdout
        assert expected_model_id in res_argv.stdout


def test_custom_effortless_alias_set_and_resolve(
    tmp_path: Path,
) -> None:
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    real_home.mkdir()
    project.mkdir()
    _make_stub_bin(bin_dir, ("agy",))

    res_add = _run_cli(
        ["models", "add", "custom-orch", "--cli", "agy", "--id", "gemini-pro-custom"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res_add.returncode == 0, res_add.stderr

    res_set = _run_cli(
        [
            "set",
            "orchestrator",
            "--provider",
            "agy",
            "--model",
            "custom-orch",
        ],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res_set.returncode == 0, res_set.stderr

    res_json = _run_cli(
        ["resolve", "orchestrator", "--format", "json"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res_json.returncode == 0, res_json.stderr
    resolved = json.loads(res_json.stdout)
    assert resolved["alias"] == "custom-orch"
    assert resolved["model_id"] == "gemini-pro-custom"
    assert resolved["effort"] == "none"
    assert resolved["profile"] is None


@pytest.mark.parametrize(
    ("bad_args", "expected_fragment"),
    [
        (["set", "orchestrator", "orchestrator-argon", "high"], "allowed: none"),
        (["set", "programmer", "neon"], "required: model, effort"),
        (
            ["set", "programmer", "--model", "neon"],
            "--model and --effort are both required",
        ),
        (["set", "programmer", "no-such-model"], "required: model, effort"),
        (
            [
                "set",
                "programmer",
                "--provider",
                "kiro",
                "--model",
                "orchestrator-argon",
            ],
            "not a kiro model",
        ),
        (
            [
                "models",
                "add",
                "bad-empty",
                "--cli",
                "agy",
                "--id",
                "x",
                "--efforts",
                "",
            ],
            "Invalid efforts",
        ),
        (
            [
                "models",
                "add",
                "bad-mix",
                "--cli",
                "agy",
                "--id",
                "x",
                "--efforts",
                "none,high",
            ],
            "cannot be combined",
        ),
        (
            [
                "models",
                "add",
                "bad-tpl",
                "--cli",
                "agy",
                "--id",
                "gemini-pro-{effort}",
            ],
            "{effort}",
        ),
    ],
)
def test_cli_effortless_boundary_rejections_preserve_config_unchanged(
    tmp_path: Path,
    bad_args: list[str],
    expected_fragment: str,
) -> None:
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    real_home.mkdir()
    _make_stub_bin(bin_dir, ("agy", "claude", "codex", "kiro-cli"))
    project_cfg = project / ".agents" / "config" / "personas.json"
    _write_json(
        project_cfg,
        {
            "schema_version": 1,
            "overrides": {"programmer": {"model": "hydrogen", "effort": "xhigh"}},
        },
    )
    before = _sha256(project_cfg)

    res = _run_cli(
        [*bad_args, "--scope", "project"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res.returncode == 1, (res.stdout, res.stderr)
    assert expected_fragment in res.stderr, res.stderr
    assert _sha256(project_cfg) == before
