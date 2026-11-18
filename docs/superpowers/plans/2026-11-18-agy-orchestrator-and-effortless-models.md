# Antigravity Orchestrator Aliases and Effortless Model Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use d3nexus:subagent-driven-development (recommended) or d3nexus:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add built-in `carbon`, `orchestrator-carbon`, and `orchestrator-argon` aliases to `scripts/personas.default.json`, support fixed-effort models via sentinel effort `"none"` with `--effort` omitted in `build_dispatch_argv()`, and infer `"none"` cleanly on `dev_config.py set` and `models add`.

**Architecture:** Represent fixed-effort models with `"efforts": ["none"]` in the layered persona config schema so downstream typed fields (`PersonaBinding.effort: str` and `efforts: list[str]`) stay intact across `lifecycle_runner.py`, `agy_profile_pool.py`, `resume_context.py`, and `check_tasks.py`. Validate in `persona_config.py` that `"none"` cannot be mixed with other efforts or paired with `"{effort}"`, omit `--effort` when `effort == "none"` for `agy`, `claude`, and `kiro` in `build_dispatch_argv()`, and infer `"none"` in `dev_config.py` only when the target model declares `efforts == ["none"]`.

**Tech Stack:** Python 3.11+, `pytest`, JSON configuration, Bash (`scripts/verify.sh`).

**Spec:** [2026-11-18-agy-orchestrator-and-effortless-models-design.md](../specs/2026-11-18-agy-orchestrator-and-effortless-models-design.md)

## Table of Contents

- [Global Constraints](#global-constraints)
- [File Structure](#file-structure)
- [Implementation Tasks](#implementation-tasks)
  - [Task 1: Default Catalogue Aliases Effortless Validation and Dispatch Argv Omission](#task-1-default-catalogue-aliases-effortless-validation-and-dispatch-argv-omission)
  - [Task 2: Optional Effort CLI Commands Skill Documentation and End-to-End Verification](#task-2-optional-effort-cli-commands-skill-documentation-and-end-to-end-verification)

## Global Constraints

- Execute inside an isolated git worktree created via `d3nexus:using-git-worktrees` off `main` (for example `.worktrees/agy_orchestrator_and_effortless_models`) so the packaged `review_cap_and_risk_triage` epic worktrees remain untouched.
- Always invoke `pytest` as `python3 -m pytest` from the active worktree root so `tests/...` imports and script paths resolve cleanly.
- Keep all seven existing presets (`default`, `gemini-saver`, `claude-hybrid`, `all-hydrogen`, `codex-kiro`, `all-claude`, `all-codex`) in `scripts/personas.default.json` unchanged.
- Do NOT touch `_validate_policy_and_low_quota` or `cmd_status` (reserved for `review_cap_and_risk_triage` Task 1) so merges remain conflict-free.
- Follow Universal Commit Message Format (`[DEV_CONFIG] Imperative title` plus `- <bullet>` lines, zero `Co-Authored-By:` or tool attribution trailers). Never run `git push`.
- Never open, grep, glob, or edit `*.vi.md` files (Rule 11) or `docs/dev-config-quick-guide.en.md`.

---

## File Structure

- Modify: `scripts/personas.default.json` — add `carbon`, `orchestrator-carbon`, and `orchestrator-argon` under `"models"`.
- Modify: `scripts/persona_config.py` — enforce sole-`"none"` and no-`"{effort}"` validation in `_validate_model_entry()`, and omit `--effort` when `binding.effort == "none"` in `build_dispatch_argv()`.
- Modify: `scripts/dev_config.py` — default `--efforts` to `"none"` on `models add` and infer `effort = "none"` when omitted on `set` strictly for models whose `efforts == ["none"]`.
- Modify: `skills/dev-config/SKILL.md` — document built-in `carbon`, `orchestrator-carbon`, `orchestrator-argon` aliases and optional-effort `models add` / `set` usage.
- Modify: `scripts/verify.sh` — register `tests/test_agy_effortless_models.py` in Section 11.
- Create: `tests/test_agy_effortless_models.py` — parametrized unit, CLI integration, and boundary edge-case tests.

## Implementation Tasks

### Task 1: Default Catalogue Aliases Effortless Validation and Dispatch Argv Omission

**Files:**
- Modify: `scripts/personas.default.json:4-45`
- Modify: `scripts/persona_config.py:204-226`
- Modify: `scripts/persona_config.py:585-639`
- Create: `tests/test_agy_effortless_models.py`

**Interfaces:**
- Consumes: `derive_quota_pool`, `load_persona_config`, `resolve_persona`, `PersonaBinding`, `PersonaConfigError` in `scripts/persona_config.py`.
- Produces: Built-in `carbon`, `orchestrator-carbon`, `orchestrator-argon` aliases in `scripts/personas.default.json`; `_validate_model_entry` sole-`"none"` invariant; `build_dispatch_argv` omitting `--effort` when `binding.effort == "none"` for `agy`, `claude`, and `kiro` while keeping `-c model_reasoning_effort=none` for `codex`.

- [ ] **Step 1: Write the failing unit and boundary tests for Task 1**

Create `tests/test_agy_effortless_models.py`:

```python
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
```

- [ ] **Step 2: Run the Task 1 tests to verify they fail (RED)**

Run: `python3 -m pytest tests/test_agy_effortless_models.py -v`
Expected: FAIL (`KeyError: 'carbon'`, missing `"cannot be combined"` / `"{effort}"` `PersonaConfigError`, and `"--effort" in argv` for `"none"`).

- [ ] **Step 3: Implement default aliases and effortless dispatch/validation in `scripts/personas.default.json` and `scripts/persona_config.py`**

1. Add `carbon`, `orchestrator-carbon`, and `orchestrator-argon` inside `"models"` in `scripts/personas.default.json` (preserving all existing models and all seven `"presets"` unchanged):

```json
    "carbon": {
      "cli": "agy",
      "id": "gemini-4-carbon-{effort}",
      "efforts": ["low", "medium", "high"]
    },
    "orchestrator-carbon": {
      "cli": "agy",
      "id": "gemini-pro-orchestrator",
      "efforts": ["none"]
    },
    "orchestrator-argon": {
      "cli": "agy",
      "id": "gemini-pro-orchestrator-argon",
      "efforts": ["none"]
    }
```

2. Update `_validate_model_entry` (`scripts/persona_config.py:218-226`) right before `derive_quota_pool(entry, alias)`:

```python
    if "none" in efforts:
        if len(efforts) > 1:
            raise PersonaConfigError(
                f"Invalid efforts '{efforts}' for model '{alias}': "
                "'none' cannot be combined with other efforts"
            )
        if "{effort}" in model_id:
            raise PersonaConfigError(
                f"Invalid model id '{model_id}' for model '{alias}': "
                "'{effort}' placeholder is not allowed when efforts is ['none']"
            )
```

3. Update `build_dispatch_argv` (`scripts/persona_config.py:591-638`) to omit `["--effort", effort]` whenever `effort == "none"` for `agy`, `claude`, and `kiro` while leaving `codex` unchanged:

```python
    cli = binding.cli
    model_id = binding.model_id
    effort = binding.effort
    effort_args = [] if effort == "none" else ["--effort", effort]

    if cli == "agy":
        if mode == "read-only":
            return ["agy", "--sandbox", "--mode", "plan", "--model", model_id, *effort_args]
        return ["agy", "--model", model_id, *effort_args, "--mode", "auto"]
    if cli == "claude":
        perm_flags = (
            ["--permission-mode", "plan"]
            if mode == "read-only"
            else ["--dangerously-skip-permissions"]
        )
        return ["claude", "-p", "--model", model_id, *effort_args, *perm_flags]
    if cli == "codex":
        sandbox = "read-only" if mode == "read-only" else "workspace-write"
        mapped_effort = _CODEX_EFFORT_MAP.get(effort.lower(), effort)
        return [
            "codex",
            "exec",
            "--sandbox",
            sandbox,
            "--model",
            model_id,
            "-c",
            f"model_reasoning_effort={mapped_effort}",
            "-",
        ]
    if cli == "kiro":
        kiro_bin = (
            "kiro-cli"
            if shutil.which("kiro-cli") or not shutil.which("kiro")
            else "kiro"
        )
        return [
            kiro_bin,
            "chat",
            "--no-interactive",
            "--trust-all-tools",
            "--wrap",
            "never",
            "--model",
            model_id,
            *effort_args,
        ]
    raise PersonaConfigError(f"Unsupported cli '{cli}'")
```

- [ ] **Step 4: Run Task 1 unit, formatting, lint, and regression tests to verify PASS (GREEN)**

Run:

```bash
python3 -m pytest tests/test_agy_effortless_models.py tests/test_fpg_persona_config.py tests/test_fpg_dispatch_and_quota.py -v
ruff format --check tests/test_agy_effortless_models.py
ruff check tests/test_agy_effortless_models.py
```

Expected: PASS (0 failures, 0 skipped, 0 format/lint issues).

- [ ] **Step 5: Commit Task 1 changes**

```bash
git add scripts/personas.default.json scripts/persona_config.py tests/test_agy_effortless_models.py
git commit -m "[DEV_CONFIG] Add orchestrator aliases and effortless dispatch support" \
  -m "- add default carbon, orchestrator-carbon, and orchestrator-argon aliases" \
  -m "- validate sole none effort and omit --effort in build_dispatch_argv"
```

---

### Task 2: Optional Effort CLI Commands Skill Documentation and End-to-End Verification

**Files:**
- Modify: `scripts/dev_config.py:586-683`
- Modify: `scripts/dev_config.py:1321-1328`
- Modify: `skills/dev-config/SKILL.md:18-95`
- Modify: `scripts/verify.sh:393-406`
- Modify: `tests/test_agy_effortless_models.py`

**Interfaces:**
- Consumes: `load_persona_config`, `build_dispatch_argv`, `PersonaConfigError` from `scripts/persona_config.py`.
- Produces: Default `--efforts none` on `models add`; effortless inference in `dev_config.py set` strictly when the matched catalogue entry defines `efforts == ["none"]`; updated `skills/dev-config/SKILL.md`; registered `tests/test_agy_effortless_models.py` in `scripts/verify.sh`.

- [ ] **Step 1: Add failing CLI integration and boundary edge-case tests to `tests/test_agy_effortless_models.py`**

1. Update the imports and constants at the top of `tests/test_agy_effortless_models.py` (inserting `hashlib`, `os`, `subprocess`, `DEV_CONFIG_SCRIPT`, and `_sha256`):

```python
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
```

```python
def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
```

2. Append the CLI helper and integration/boundary tests to `tests/test_agy_effortless_models.py`:

```python
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
            "gemini-pro-orchestrator-argon",
            "argonWeekly",
        ),
        (
            ["set", "orchestrator", "orchestrator-argon", "none"],
            "orchestrator-argon",
            "gemini-pro-orchestrator-argon",
            "argonWeekly",
        ),
        (
            ["set", "orchestrator", "gemini-pro-orchestrator-argon"],
            "orchestrator-argon",
            "gemini-pro-orchestrator-argon",
            "argonWeekly",
        ),
        (
            ["set", "orchestrator", "orchestrator-carbon"],
            "orchestrator-carbon",
            "gemini-pro-orchestrator",
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
            "gemini-pro-orchestrator-argon",
            "argonWeekly",
        ),
        (
            [
                "set",
                "orchestrator",
                "--provider",
                "agy",
                "--model",
                "gemini-pro-orchestrator-argon",
            ],
            "orchestrator-argon",
            "gemini-pro-orchestrator-argon",
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


def test_cli_set_effortless_with_profile_preference_and_models_add_default(
    tmp_path: Path,
) -> None:
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    (real_home / "antigravity_homes" / "p1").mkdir(parents=True)
    project.mkdir()
    _make_stub_bin(bin_dir, ("agy",))

    assert (
        _run_cli(
            ["profiles", "add", "p1"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        ).returncode
        == 0
    )

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
            "--profile",
            "p1",
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
    assert resolved["profile"] == "p1"


@pytest.mark.parametrize(
    ("bad_args", "expected_fragment"),
    [
        (["set", "orchestrator", "orchestrator-argon", "high"], "allowed: none"),
        (["set", "programmer", "carbon"], "required: model, effort"),
        (
            ["set", "programmer", "--model", "carbon"],
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
```

- [ ] **Step 2: Run the Task 2 tests to verify they fail (RED)**

Run: `python3 -m pytest tests/test_agy_effortless_models.py -v`
Expected: FAIL on the new CLI tests (`--efforts` required on `models add` and `set` rejecting omitted effort on `orchestrator-argon` / `orchestrator-carbon`).

- [ ] **Step 3: Implement optional `--efforts` and effortless `set` inference in `scripts/dev_config.py`, update `skills/dev-config/SKILL.md`, and register in `scripts/verify.sh`**

1. In `scripts/dev_config.py`, add `_is_effortless_target()` right after `_resolve_catalogue_alias()` (`scripts/dev_config.py:611`):

```python
def _is_effortless_target(
    models: Mapping[str, Any],
    raw_model: str,
    provider: str | None,
) -> bool:
    """Return True when raw_model resolves uniquely to a model with efforts == ['none']."""
    if raw_model in models:
        return list(models[raw_model].get("efforts", [])) == ["none"]
    matches = [
        entry
        for entry in models.values()
        if (provider is None or entry.get("cli") == provider)
        and str(entry.get("id", "")) == raw_model
    ]
    return len(matches) == 1 and list(matches[0].get("efforts", [])) == ["none"]
```

2. Update `_resolve_set_request()` (`scripts/dev_config.py:637-683`) so omitted effort infers `"none"` strictly when `_is_effortless_target()` returns `True`, while preserving all existing validation and fast-path errors:

```python
def _resolve_set_request(
    project_root: Path,
    *,
    model: str | None,
    effort: str | None,
    provider: str | None,
    flag_model: str | None,
    flag_effort: str | None,
    profile: str | None,
    real_home: Path | None,
) -> tuple[str, str, str | None]:
    """Turn the `set` arguments into a checked (alias, effort, profile) triple."""
    flagged = flag_model is not None or flag_effort is not None
    if flagged and (model is not None or effort is not None):
        raise PersonaConfigError(
            "Cannot mix the positional MODEL EFFORT form with --model/--effort; use one form"
        )
    if provider is not None and provider not in ALLOWED_CLIS:
        raise PersonaConfigError(
            f"Unknown provider '{provider}'; expected one of {', '.join(sorted(ALLOWED_CLIS))}"
        )

    models: Mapping[str, Any] | None = None
    inferred_effortless = False
    if flagged:
        if flag_model is None:
            raise PersonaConfigError("--model and --effort are both required when using flags")
        if flag_effort is None:
            models = _pc.load_persona_config(project_root, real_home=real_home)["models"]
            if not _is_effortless_target(models, flag_model, provider):
                raise PersonaConfigError(
                    "--model and --effort are both required when using flags"
                )
            flag_effort = "none"
            inferred_effortless = True
        model, effort = flag_model, flag_effort
    elif model is None:
        raise PersonaConfigError(
            "the following arguments are required: model, effort "
            "(or use --model and --effort)"
        )
    elif effort is None:
        models = _pc.load_persona_config(project_root, real_home=real_home)["models"]
        if not _is_effortless_target(models, model, provider):
            raise PersonaConfigError(
                "the following arguments are required: model, effort "
                "(or use --model and --effort)"
            )
        effort = "none"
        inferred_effortless = True

    if (
        not flagged
        and provider is None
        and (profile is None or profile == "auto")
        and not inferred_effortless
    ):
        return model, effort, None

    if models is None:
        models = _pc.load_persona_config(project_root, real_home=real_home)["models"]
    alias = _resolve_catalogue_alias(models, model, effort, provider)
    entry = models[alias]
    if provider is not None and entry["cli"] != provider:
        raise PersonaConfigError(f"{model} is not a {provider} model")
    allowed_efforts = list(entry["efforts"])
    if effort not in allowed_efforts:
        raise PersonaConfigError(
            f"Unsupported effort '{effort}' for model '{alias}'; "
            f"allowed: {', '.join(allowed_efforts)}"
        )
    checked = _checked_set_profile(profile, alias=alias, cli=str(entry["cli"]), real_home=real_home)
    return alias, effort, checked
```

3. Update `p_madd.add_argument("--efforts", required=True)` (`scripts/dev_config.py:1325`) to:

```python
    p_madd.add_argument("--efforts", default="none")
```

4. Update `skills/dev-config/SKILL.md`:
   - In the `Invocation Mapping` table:
     - `models add ALIAS --cli CLI --id ID [--efforts E1,E2|none] [--quota-pool POOL] [--scope global\|project]` — document `--efforts` defaulting to `none` for fixed-effort models.
     - `set PERSONA MODEL [EFFORT] [--fallback MODEL] [--scope global\|project]` — note `EFFORT` may be omitted for fixed-effort models (`efforts: ["none"]`).
     - `set PERSONA [--provider agy\|claude\|codex\|kiro] --model M [--effort E] [--profile NAME\|auto] [--fallback MODEL] [--scope global\|project]` — note `--effort` may be omitted for fixed-effort models.
   - In `## Setting a Provider, Model, Effort and Preferred Profile`:
     - Add example commands for `orchestrator-argon` (`set orchestrator orchestrator-argon` and `set orchestrator --provider agy --model gemini-pro-orchestrator-argon`), clarify that `--effort` / `EFFORT` is required for selectable-effort models (`hydrogen`, `argon`, `carbon`, etc.) and defaults to `none` (omitting `--effort` on headless CLI dispatch) only when `efforts` is `["none"]`.
   - In `## Presets and Quota Pools`:
     - Document the built-in `carbon` (`gemini-4-carbon-{effort}`, `gemini5h`), `orchestrator-carbon` (`gemini-pro-orchestrator`, `efforts: ["none"]`, `gemini5h`), and `orchestrator-argon` (`gemini-pro-orchestrator-argon`, `efforts: ["none"]`, `argonWeekly`) aliases.

5. Register `tests/test_agy_effortless_models.py` in `scripts/verify.sh` Section 11 right after `tests/test_fpg_acceptance.py`:

```python
    ("11", "pytest",   "tests/test_agy_effortless_models.py", 15, False),
```

- [ ] **Step 4: Run full unit, integration, regression, quality gate, and doc checks (GREEN)**

Run:

```bash
python3 -m pytest tests/test_agy_effortless_models.py tests/test_fpg_*.py -v
ruff format --check tests
ruff check tests
./scripts/verify.sh
python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-config/SKILL.md
```

Also invoke `@quality_check` (`python-quality-check`, `epic` profile against `main`) after committing to confirm `format`, `lint`, `type_check`, `test`, and `architecture` all report `PASS`.

Expected: All test suites exit `0` (`0` failures, `0` skipped), `ruff format --check` / `ruff check` / `@quality_check` pass cleanly, and `check_document.py` reports `0 findings`.

- [ ] **Step 5: Commit Task 2 changes**

```bash
git add scripts/dev_config.py skills/dev-config/SKILL.md scripts/verify.sh tests/test_agy_effortless_models.py
git commit -m "[DEV_CONFIG] Support effortless set and models add defaults" \
  -m "- default models add --efforts to none and infer none for fixed-effort models on set" \
  -m "- document built-in carbon and orchestrator aliases and register test suite in verify.sh"
```
