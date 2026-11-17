"""Tests for layered persona configuration, dev_config CLI, low-quota, and concurrency.

Covers BDD Scenarios:
- FPG-HP-01: Layered persona resolution reports value and source layer per field
- FPG-HP-02: dev-config models lists the catalogue and a newly added alias becomes bindable
- FPG-EC-01: Invalid writes are rejected and leave the configuration file unchanged
- FPG-EC-02: Legacy model settings are ignored and reported
- FPG-ST-01: Low-quota mode is per profile, expires, and halves the turn budget
- FPG-AR-05: Concurrent writers to the global persona file never lose updates
"""

from __future__ import annotations

from datetime import datetime, timezone
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
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


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
    extra_env: dict[str, str] | None = None,
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
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(DEV_CONFIG_SCRIPT), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_fpg_hp_01_layered_resolution_reports_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FPG-HP-01: Layered persona resolution reports value and source layer per field."""
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)

    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    project.mkdir(parents=True)

    _write_json(
        real_home / ".d3nexus" / "personas.json",
        {"active_preset": "claude-hybrid"},
    )
    _write_json(
        project / ".agents" / "config" / "personas.json",
        {"overrides": {"programmer": {"model": "hydrogen", "effort": "high"}}},
    )

    arch = pc.resolve_persona("ai_architect_reviewer", project, real_home=real_home)
    assert arch.persona == "ai_architect_reviewer"
    assert arch.alias == "claude-opus"
    assert arch.cli == "claude"
    assert arch.model_id == "opus"
    assert arch.effort == "high"
    assert arch.quota_pool == "provider"
    assert arch.sources["model"] == "global"

    orch = pc.resolve_persona("orchestrator", project, real_home=real_home)
    assert orch.alias == "hydrogen"
    assert orch.cli == "agy"
    assert orch.model_id == "gemini-4-hydrogen-high"
    assert orch.effort == "high"
    assert orch.quota_pool == "gemini5h"

    prog = pc.resolve_persona("programmer", project, real_home=real_home)
    assert prog.model_id == "gemini-4-hydrogen-high"
    assert prog.effort == "high"
    assert prog.sources["model"] == "project"
    assert prog.sources["effort"] == "project"

    prog_cli = pc.resolve_persona(
        "programmer",
        project,
        cli_overrides={"effort": "xhigh"},
        real_home=real_home,
    )
    assert prog_cli.model_id == "gemini-4-hydrogen-xhigh"
    assert prog_cli.effort == "xhigh"
    assert prog_cli.sources["effort"] == "cli"
    assert prog_cli.sources["model"] == "project"

    # Also verify antigravity_homes splitting when real_home is not passed explicitly.
    monkeypatch.setenv("HOME", str(real_home / "antigravity_homes" / "p1"))
    monkeypatch.delenv("REAL_HOME", raising=False)
    loaded = pc.load_persona_config(project)
    assert loaded["schema_version"] == 1
    assert loaded["active_preset"] == "claude-hybrid"
    assert (
        pc.resolve_persona("ai_architect_reviewer", project).sources["model"]
        == "global"
    )


class Test_Integration:
    """[Tier C - Integration] Subprocess CLI integration tests for dev_config.py."""

    def test_fpg_hp_02_dev_config_models_and_bindable_alias(
        self, tmp_path: Path
    ) -> None:
        """FPG-HP-02: dev-config models lists catalogue and newly added alias becomes bindable."""
        real_home = tmp_path / "real_home"
        project = tmp_path / "project"
        bin_dir = tmp_path / "bin"
        real_home.mkdir()
        project.mkdir()
        _make_stub_bin(bin_dir, ("agy", "claude"))

        res_list = _run_cli(
            ["models", "--json"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_list.returncode == 0, res_list.stderr
        payload = json.loads(res_list.stdout)
        by_alias = {entry["alias"]: entry for entry in payload["models"]}
        assert set(by_alias) >= {
            "argon",
            "hydrogen",
            "claude-opus",
            "claude-sonnet",
            "codex-gpt",
            "kiro-sonnet",
            "kiro-opus",
        }
        assert by_alias["codex-gpt"]["cli_on_path"] is False
        assert by_alias["kiro-sonnet"]["cli_on_path"] is False
        assert by_alias["kiro-opus"]["cli_on_path"] is False
        assert by_alias["argon"]["cli_on_path"] is True
        assert by_alias["argon"]["used_by"] == ["ai_architect_reviewer"]

        res_add = _run_cli(
            [
                "models",
                "add",
                "gpt-next",
                "--cli",
                "codex",
                "--id",
                "gpt-7",
                "--efforts",
                "medium,high",
                "--scope",
                "global",
            ],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_add.returncode == 0, res_add.stderr

        res_set = _run_cli(
            ["set", "programmer", "gpt-next", "high"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_set.returncode == 0, res_set.stderr

        res_resolve = _run_cli(
            ["resolve", "programmer", "--format", "json"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_resolve.returncode == 0, res_resolve.stderr
        resolved = json.loads(res_resolve.stdout)
        assert resolved["model_id"] == "gpt-7"
        assert resolved["cli"] == "codex"
        assert resolved["quota_pool"] == "provider"

        # Removing a bound alias is refused; after reset it succeeds.
        res_rm_bound = _run_cli(
            ["models", "remove", "gpt-next", "--scope", "global"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_rm_bound.returncode == 1
        assert "gpt-next" in (res_rm_bound.stdout + res_rm_bound.stderr)

        res_reset = _run_cli(
            ["reset", "programmer", "--scope", "global"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_reset.returncode == 0, res_reset.stderr

        res_rm_free = _run_cli(
            ["models", "remove", "gpt-next", "--scope", "global"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_rm_free.returncode == 0, res_rm_free.stderr

    def test_fpg_hp_02_cli_subcommands_aliases_and_fallback_guard(
        self, tmp_path: Path
    ) -> None:
        """FPG-HP-02: Covers remaining subcommands (--models, status, preset, reset, checkpoint, resolve)."""
        pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
        real_home = tmp_path / "real_home"
        project = tmp_path / "project"
        bin_dir = tmp_path / "bin"
        real_home.mkdir()
        project.mkdir()
        _make_stub_bin(bin_dir, ("agy",))

        res_models_alias = _run_cli(
            ["--models", "--persona", "programmer", "--json"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_models_alias.returncode == 0, res_models_alias.stderr
        models_payload = json.loads(res_models_alias.stdout)
        assert models_payload["persona"] == "programmer"
        assert models_payload["current_alias"] == "hydrogen"
        assert models_payload["models"][0]["alias"] == "hydrogen"

        assert (
            _run_cli(
                [
                    "models",
                    "add",
                    "fb-only",
                    "--cli",
                    "codex",
                    "--id",
                    "gpt-fb",
                    "--efforts",
                    "high",
                    "--scope",
                    "global",
                ],
                cwd=project,
                real_home=real_home,
                path_dir=bin_dir,
            ).returncode
            == 0
        )
        assert (
            _run_cli(
                [
                    "set",
                    "programmer",
                    "hydrogen",
                    "high",
                    "--fallback",
                    "fb-only",
                    "--scope",
                    "global",
                ],
                cwd=project,
                real_home=real_home,
                path_dir=bin_dir,
            ).returncode
            == 0
        )
        res_rm_fb = _run_cli(
            ["models", "remove", "fb-only", "--scope", "global"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_rm_fb.returncode == 1
        assert "fb-only" in (res_rm_fb.stdout + res_rm_fb.stderr)

        assert (
            _run_cli(
                ["reset", "--scope", "global"],
                cwd=project,
                real_home=real_home,
                path_dir=bin_dir,
            ).returncode
            == 0
        )
        assert (
            _run_cli(
                ["models", "remove", "fb-only", "--scope", "global"],
                cwd=project,
                real_home=real_home,
                path_dir=bin_dir,
            ).returncode
            == 0
        )

        assert (
            _run_cli(
                ["preset", "all-hydrogen", "--scope", "project"],
                cwd=project,
                real_home=real_home,
                path_dir=bin_dir,
            ).returncode
            == 0
        )
        res_preset_masked = _run_cli(
            ["preset", "claude-hybrid", "--scope", "global"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_preset_masked.returncode == 0
        assert "all-hydrogen" in res_preset_masked.stderr

        assert (
            _run_cli(
                ["checkpoint", "--turns", "3", "--scope", "project"],
                cwd=project,
                real_home=real_home,
                path_dir=bin_dir,
            ).returncode
            == 0
        )
        assert (
            _run_cli(
                ["low-quota", "on", "--profile", "p1"],
                cwd=project,
                real_home=real_home,
                path_dir=bin_dir,
            ).returncode
            == 0
        )
        assert pc.effective_turn_budget(project, "p1", real_home=real_home) == 1

        res_argv = _run_cli(
            [
                "resolve",
                "ai_architect_reviewer",
                "--format",
                "argv",
                "--mode",
                "read-only",
            ],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_argv.returncode == 0, res_argv.stderr
        assert (
            res_argv.stdout.strip()
            == "agy --sandbox --mode plan --model gemini-4-hydrogen-xhigh --effort xhigh"
        )

        res_status = _run_cli(
            ["status"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_status.returncode == 0
        assert "Active preset: all-hydrogen" in res_status.stdout


@pytest.mark.parametrize(
    ("args", "rejected"),
    [
        (["set", "programmer", "argon", "xhigh", "--scope", "project"], "xhigh"),
        (
            ["set", "programmer", "nosuchmodel", "high", "--scope", "project"],
            "nosuchmodel",
        ),
        (["set", "reviewer", "argon", "high", "--scope", "project"], "reviewer"),
        (
            [
                "models",
                "add",
                "ollama-x",
                "--cli",
                "ollama",
                "--id",
                "gemma",
                "--efforts",
                "high",
                "--scope",
                "project",
            ],
            "ollama",
        ),
        (
            [
                "models",
                "add",
                "fast",
                "--cli",
                "agy",
                "--id",
                "gemini-4-flash",
                "--efforts",
                "high",
                "--quota-pool",
                "provider",
                "--scope",
                "project",
            ],
            "provider",
        ),
        (
            [
                "models",
                "add",
                "bad-claude",
                "--cli",
                "claude",
                "--id",
                "opus",
                "--efforts",
                "high",
                "--quota-pool",
                "gemini5h",
                "--scope",
                "project",
            ],
            "gemini5h",
        ),
        (["preset", "nosuchpreset", "--scope", "project"], "nosuchpreset"),
        (["checkpoint", "--turns", "0", "--scope", "project"], "0"),
    ],
)
def test_fpg_ec_01_invalid_writes_rejected_file_unchanged(
    tmp_path: Path, args: list[str], rejected: str
) -> None:
    """FPG-EC-01: Invalid writes are rejected and leave the configuration file unchanged."""
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    proj_cfg = project / ".agents" / "config" / "personas.json"
    _write_json(proj_cfg, {"schema_version": 1, "overrides": {}})
    before_sha = _sha256(proj_cfg)

    res = _run_cli(args, cwd=project, real_home=real_home)
    assert res.returncode == 1
    combined = res.stdout + res.stderr
    assert rejected in combined
    assert _sha256(proj_cfg) == before_sha


def test_fpg_ec_01_validation_rejects_bad_schema_and_file(tmp_path: Path) -> None:
    """FPG-EC-01: Direct config loading rejects invalid schema_version and unknown personas."""
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    _write_json(
        project / ".agents" / "config" / "personas.json", {"schema_version": 99}
    )
    with pytest.raises(pc.PersonaConfigError, match="schema_version"):
        pc.load_persona_config(project, real_home=real_home)

    _write_json(
        project / ".agents" / "config" / "personas.json",
        {
            "schema_version": 1,
            "overrides": {"reviewer": {"model": "argon", "effort": "high"}},
        },
    )
    with pytest.raises(pc.PersonaConfigError, match="reviewer"):
        pc.load_persona_config(project, real_home=real_home)


def test_fpg_ec_02_legacy_model_settings_ignored_and_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FPG-EC-02: Legacy model settings are ignored and reported in status warnings."""
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    _write_json(
        project / ".devtool" / "review_config.json",
        {
            "providers": {
                "programmer": {"model": "gemini-3.8-flash", "thinking_level": "high"},
                "assistant": {
                    "model": "claude-opus-5-5-high",
                    "thinking_level": "high",
                },
            }
        },
    )

    monkeypatch.setenv("AGY_PROGRAMMER_MODEL", "legacy-x")
    monkeypatch.setenv("AGY_PROGRAMMER_EFFORT", "low")
    monkeypatch.setenv("AGY_ASSISTANT_MODEL", "legacy-a")

    binding = pc.resolve_persona("programmer", project, real_home=real_home)
    assert binding.model_id == "gemini-4-hydrogen-xhigh"
    assert binding.effort == "xhigh"

    res = _run_cli(
        ["status", "--json"],
        cwd=project,
        real_home=real_home,
        extra_env={
            "AGY_PROGRAMMER_MODEL": "legacy-x",
            "AGY_PROGRAMMER_EFFORT": "low",
            "AGY_ASSISTANT_MODEL": "legacy-a",
        },
    )
    assert res.returncode == 0, res.stderr
    status_payload = json.loads(res.stdout)
    warnings_joined = "\n".join(status_payload["warnings"])
    assert "providers.programmer" in warnings_joined
    assert "providers.assistant" in warnings_joined
    assert "AGY_PROGRAMMER_MODEL" in warnings_joined
    assert "AGY_PROGRAMMER_EFFORT" in warnings_joined
    assert "AGY_ASSISTANT_MODEL" in warnings_joined


def test_fpg_st_01_low_quota_per_profile_expiry_and_turn_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FPG-ST-01: Low-quota mode is per profile, expires, and halves the turn budget."""
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    dc = _load_module("dev_config", DEV_CONFIG_SCRIPT)

    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    project.mkdir()

    t_1000 = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)
    t_1100 = datetime(2026, 11, 17, 11, 0, tzinfo=timezone.utc)
    t_1159 = datetime(2026, 11, 17, 11, 59, tzinfo=timezone.utc)
    t_1201 = datetime(2026, 11, 17, 12, 1, tzinfo=timezone.utc)

    monkeypatch.setenv("REAL_HOME", str(real_home))
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.setenv("AGY_PROFILE", "danhdue")

    rc_on = dc.cmd_low_quota(
        project,
        action="on",
        hours=2.0,
        profile="danhdue",
        now=t_1000,
        real_home=real_home,
    )
    assert rc_on == 0

    state_before_exp = pc.low_quota_state(
        project, "danhdue", now=t_1159, real_home=real_home
    )
    assert state_before_exp is not None
    assert state_before_exp["enabled"] is True
    assert (
        pc.effective_turn_budget(project, "danhdue", now=t_1159, real_home=real_home)
        == 4
    )

    assert (
        pc.low_quota_state(project, "danhdue", now=t_1201, real_home=real_home) is None
    )
    assert (
        pc.effective_turn_budget(project, "danhdue", now=t_1201, real_home=real_home)
        == 8
    )
    assert (
        pc.low_quota_state(project, "other_profile", now=t_1100, real_home=real_home)
        is None
    )

    rc_off = dc.cmd_low_quota(
        project,
        action="off",
        profile="danhdue",
        now=t_1100,
        real_home=real_home,
    )
    assert rc_off == 0
    assert (
        pc.low_quota_state(project, "danhdue", now=t_1100, real_home=real_home) is None
    )

    # Also test --low-quota CLI alias end to end.
    res_alias = _run_cli(
        ["--low-quota", "on", "--for", "2"],
        cwd=project,
        real_home=real_home,
        extra_env={"AGY_PROFILE": "danhdue"},
    )
    assert res_alias.returncode == 0, res_alias.stderr
    assert pc.low_quota_state(project, "danhdue", real_home=real_home) is not None


def test_fpg_ar_05_concurrent_writers_never_lose_updates(tmp_path: Path) -> None:
    """FPG-AR-05: Concurrent writers to the global persona file never lose updates."""
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    project.mkdir()

    base_env = dict(os.environ)
    base_env["HOME"] = str(real_home)
    base_env["REAL_HOME"] = str(real_home)
    base_env.pop("AGY_PROFILE", None)
    base_env.pop("ANTIGRAVITY_PROFILE", None)

    cmds = [
        [
            sys.executable,
            str(DEV_CONFIG_SCRIPT),
            "set",
            "programmer",
            "hydrogen",
            "high",
        ],
        [
            sys.executable,
            str(DEV_CONFIG_SCRIPT),
            "set",
            "ai_architect_reviewer",
            "argon",
            "medium",
        ],
        [
            sys.executable,
            str(DEV_CONFIG_SCRIPT),
            "low-quota",
            "on",
            "--profile",
            "p1",
        ],
        [
            sys.executable,
            str(DEV_CONFIG_SCRIPT),
            "low-quota",
            "on",
            "--profile",
            "p2",
        ],
    ]

    procs = [
        subprocess.Popen(
            cmd,
            cwd=project,
            env=base_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for cmd in cmds
    ]
    results = [p.communicate(timeout=20) + (p.returncode,) for p in procs]
    for out, err, rc in results:
        assert rc == 0, f"Concurrent writer failed (rc={rc}): {out}\n{err}"

    global_data = json.loads(
        (real_home / ".d3nexus" / "personas.json").read_text(encoding="utf-8")
    )
    assert global_data["overrides"]["programmer"] == {
        "model": "hydrogen",
        "effort": "high",
    }
    assert global_data["overrides"]["ai_architect_reviewer"] == {
        "model": "argon",
        "effort": "medium",
    }
    assert global_data["low_quota"]["p1"]["enabled"] is True
    assert global_data["low_quota"]["p2"]["enabled"] is True


@pytest.mark.parametrize(
    ("preset", "expected"),
    [
        (
            "default",
            {
                "ai_architect_reviewer": (
                    "argon",
                    "high",
                    "gemini-4-argon-high",
                    "argonWeekly",
                ),
                "orchestrator": (
                    "hydrogen",
                    "high",
                    "gemini-4-hydrogen-high",
                    "gemini5h",
                ),
                "programmer": (
                    "hydrogen",
                    "xhigh",
                    "gemini-4-hydrogen-xhigh",
                    "gemini5h",
                ),
            },
        ),
        (
            "gemini-saver",
            {
                "ai_architect_reviewer": (
                    "argon",
                    "medium",
                    "gemini-4-argon-medium",
                    "argonWeekly",
                ),
                "orchestrator": (
                    "hydrogen",
                    "medium",
                    "gemini-4-hydrogen-medium",
                    "gemini5h",
                ),
                "programmer": (
                    "hydrogen",
                    "high",
                    "gemini-4-hydrogen-high",
                    "gemini5h",
                ),
            },
        ),
        (
            "claude-hybrid",
            {
                "ai_architect_reviewer": ("claude-opus", "high", "opus", "provider"),
                "orchestrator": (
                    "hydrogen",
                    "high",
                    "gemini-4-hydrogen-high",
                    "gemini5h",
                ),
                "programmer": (
                    "hydrogen",
                    "xhigh",
                    "gemini-4-hydrogen-xhigh",
                    "gemini5h",
                ),
            },
        ),
        (
            "all-hydrogen",
            {
                "ai_architect_reviewer": (
                    "hydrogen",
                    "xhigh",
                    "gemini-4-hydrogen-xhigh",
                    "gemini5h",
                ),
                "orchestrator": (
                    "hydrogen",
                    "high",
                    "gemini-4-hydrogen-high",
                    "gemini5h",
                ),
                "programmer": (
                    "hydrogen",
                    "xhigh",
                    "gemini-4-hydrogen-xhigh",
                    "gemini5h",
                ),
            },
        ),
        (
            "codex-kiro",
            {
                "ai_architect_reviewer": (
                    "kiro-opus",
                    "high",
                    "claude-opus-5.5",
                    "provider",
                ),
                "orchestrator": ("codex-gpt", "medium", "gpt-6.1-sol", "provider"),
                "programmer": ("codex-gpt", "xhigh", "gpt-6.1-sol", "provider"),
            },
        ),
    ],
)
def test_fpg_hp_01_all_five_presets_resolve(
    tmp_path: Path,
    preset: str,
    expected: dict[str, tuple[str, str, str, str]],
) -> None:
    """FPG-HP-01: All five kit presets bind all three personas accurately."""
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    project.mkdir()
    _write_json(real_home / ".d3nexus" / "personas.json", {"active_preset": preset})

    for persona, (alias, effort, model_id, pool) in expected.items():
        binding = pc.resolve_persona(persona, project, real_home=real_home)
        assert binding.alias == alias
        assert binding.effort == effort
        assert binding.model_id == model_id
        assert binding.quota_pool == pool


@pytest.mark.parametrize(
    ("layer_payload", "match"),
    [
        ({"schema_version": True}, "schema_version"),
        ({"unknown_top": 1}, "unknown_top"),
        ({"active_preset": "missing-preset"}, "missing-preset"),
        (
            {
                "presets": {
                    "bad": {
                        "ai_architect_reviewer": {"model": "argon", "effort": "high"}
                    }
                }
            },
            "orchestrator",
        ),
        (
            {
                "presets": {
                    "bad": {
                        "ai_architect_reviewer": {"model": "argon", "effort": "high"},
                        "orchestrator": {"model": "hydrogen", "effort": "high"},
                        "programmer": {"model": "hydrogen", "effort": "xhigh"},
                        "reviewer": {"model": "argon", "effort": "high"},
                    }
                }
            },
            "reviewer",
        ),
        (
            {
                "overrides": {
                    "programmer": {"model": "hydrogen", "effort": "high", "extra": 1}
                }
            },
            "extra",
        ),
        (
            {
                "overrides": {
                    "programmer": {
                        "model": "hydrogen",
                        "effort": "high",
                        "fallback_model": "ghost",
                    }
                }
            },
            "ghost",
        ),
        (
            {"models": {"bad": {"cli": "ollama", "id": "x", "efforts": ["high"]}}},
            "ollama",
        ),
        (
            {"models": {"bad": {"cli": "agy", "id": "x", "efforts": []}}},
            "efforts",
        ),
        (
            {
                "models": {
                    "bad": {
                        "cli": "codex",
                        "id": "gpt",
                        "efforts": ["high"],
                        "quota_pool": "argonWeekly",
                    }
                }
            },
            "argonWeekly",
        ),
        (
            {
                "models": {
                    "bad": {
                        "cli": "agy",
                        "id": "x",
                        "efforts": ["high"],
                        "quota_pool": "monthly",
                    }
                }
            },
            "monthly",
        ),
        (
            {"checkpoint_policy": {"max_orchestrator_turns_before_checkpoint": True}},
            "True",
        ),
        ({"checkpoint_policy": {"max_orchestrator_turns_before_checkpoint": -2}}, "-2"),
        ({"low_quota": {"p1": {"enabled": "yes"}}}, "enabled"),
        (
            {"low_quota": {"p1": {"enabled": True, "expires_at": "not-a-date"}}},
            "not-a-date",
        ),
    ],
)
def test_fpg_ec_01_validation_branches(
    tmp_path: Path, layer_payload: dict[str, Any], match: str
) -> None:
    """FPG-EC-01: Every schema validation branch raises PersonaConfigError naming bad value."""
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    _write_json(project / ".agents" / "config" / "personas.json", layer_payload)
    with pytest.raises(pc.PersonaConfigError, match=match):
        pc.load_persona_config(project, real_home=real_home)


def test_fpg_ec_01_corrupt_json_and_cli_usage_errors(tmp_path: Path) -> None:
    """FPG-EC-01: Corrupt JSON, bad low-quota/remove args, and argparse errors exit 1."""
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    cfg_path = project / ".agents" / "config" / "personas.json"
    cfg_path.parent.mkdir(parents=True)

    cfg_path.write_text("{broken json", encoding="utf-8")
    with pytest.raises(pc.PersonaConfigError):
        pc.load_persona_config(project, real_home=real_home)

    cfg_path.write_text("[]", encoding="utf-8")
    with pytest.raises(pc.PersonaConfigError):
        pc.load_persona_config(project, real_home=real_home)

    cfg_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(pc.PersonaConfigError, match="bogus"):
        pc.resolve_persona("bogus", project, real_home=real_home)
    with pytest.raises(pc.PersonaConfigError, match="extra"):
        pc.resolve_persona(
            "programmer", project, cli_overrides={"extra": "1"}, real_home=real_home
        )
    with pytest.raises(pc.PersonaConfigError, match="bogus"):
        pc.build_dispatch_argv(
            pc.resolve_persona("programmer", project, real_home=real_home),
            "bogus",
        )

    for bad_args, token in [
        (["low-quota", "on", "--for", "0"], "0"),
        (["low-quota", "bogus"], "bogus"),
        (["models", "remove", "nonexistent", "--scope", "global"], "nonexistent"),
        (["models", "remove", "argon", "--scope", "global"], "argon"),
        (["set", "programmer"], "arguments"),
    ]:
        res = _run_cli(bad_args, cwd=project, real_home=real_home)
        assert res.returncode == 1
        assert token in (res.stdout + res.stderr)
