"""Tests for Antigravity orchestrator aliases and effortless model support."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONA_CONFIG_SCRIPT = REPO_ROOT / "scripts" / "persona_config.py"


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
        ("carbon", "gemini-4-carbon-{effort}", ["low", "medium", "high"], "gemini5h"),
        ("orchestrator-carbon", "gemini-pro-orchestrator", ["none"], "gemini5h"),
        (
            "orchestrator-argon",
            "gemini-pro-orchestrator-argon",
            ["none"],
            "argonWeekly",
        ),
    ],
)
def test_kit_defaults_include_carbon_and_orchestrator_aliases(
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
    ("model_entry", "error_fragment"),
    [
        (
            {
                "cli": "agy",
                "id": "gemini-pro-orchestrator",
                "efforts": ["none", "high"],
            },
            "cannot be combined",
        ),
        (
            {
                "cli": "agy",
                "id": "gemini-pro-orchestrator",
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
            "gemini-pro-orchestrator-argon",
            "none",
            "read-only",
            [
                "agy",
                "--sandbox",
                "--mode",
                "plan",
                "--model",
                "gemini-pro-orchestrator-argon",
            ],
        ),
        (
            "agy",
            "gemini-pro-orchestrator-argon",
            "none",
            "write",
            [
                "agy",
                "--model",
                "gemini-pro-orchestrator-argon",
                "--mode",
                "auto",
            ],
        ),
        (
            "agy",
            "gemini-pro-orchestrator",
            "none",
            "read-only",
            [
                "agy",
                "--sandbox",
                "--mode",
                "plan",
                "--model",
                "gemini-pro-orchestrator",
            ],
        ),
        (
            "agy",
            "gemini-4-carbon-high",
            "high",
            "read-only",
            [
                "agy",
                "--sandbox",
                "--mode",
                "plan",
                "--model",
                "gemini-4-carbon-high",
                "--effort",
                "high",
            ],
        ),
        (
            "agy",
            "gemini-4-carbon-high",
            "high",
            "write",
            [
                "agy",
                "--model",
                "gemini-4-carbon-high",
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
