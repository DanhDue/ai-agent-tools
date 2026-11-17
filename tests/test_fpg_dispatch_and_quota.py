"""Tests for dispatch argv/env builders, failure classification, and automatic quota gate.

Covers BDD Scenarios:
- FPG-HP-03: Dispatch argv and environment preserve the bound model and effort per CLI and mode
- FPG-FR-01: The quota gate stops on insufficient quota and tolerates unknown quota
- FPG-FR-02: Dispatch failures are classified as model failures only for quota, auth and missing CLI
"""

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


def test_fpg_hp_03_dispatch_argv_per_cli_and_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FPG-HP-03: Dispatch argv and environment preserve bound model and effort per CLI and mode."""
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)

    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    for exe_name in ("agy", "claude", "codex", "kiro-cli"):
        exe = bin_dir / exe_name
        exe.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        exe.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    _write_json(
        project / ".agents" / "config" / "personas.json",
        {
            "models": {
                "claude-custom": {
                    "cli": "claude",
                    "id": "claude-opus-4-custom",
                    "efforts": ["medium", "high"],
                }
            }
        },
    )

    prog_hydrogen = pc.resolve_persona("programmer", project, real_home=real_home)
    assert pc.build_dispatch_argv(prog_hydrogen, "write") == [
        "agy",
        "--model",
        "gemini-4-hydrogen-xhigh",
        "--effort",
        "xhigh",
        "--mode",
        "auto",
    ]

    arch_argon = pc.resolve_persona("ai_architect_reviewer", project, real_home=real_home)
    assert pc.build_dispatch_argv(arch_argon, "read-only") == [
        "agy",
        "--sandbox",
        "--mode",
        "plan",
        "--model",
        "gemini-4-argon-high",
        "--effort",
        "high",
    ]

    claude_custom = pc.resolve_persona(
        "ai_architect_reviewer",
        project,
        cli_overrides={"model": "claude-custom", "effort": "medium"},
        real_home=real_home,
    )
    claude_ro = pc.build_dispatch_argv(claude_custom, "read-only")
    assert "--model" in claude_ro
    assert claude_ro[claude_ro.index("--model") + 1] == "claude-opus-4-custom"
    assert "--effort" in claude_ro
    assert claude_ro[claude_ro.index("--effort") + 1] == "medium"
    assert "--permission-mode" in claude_ro
    assert claude_ro[claude_ro.index("--permission-mode") + 1] == "plan"
    assert "--dangerously-skip-permissions" not in claude_ro

    claude_rw = pc.build_dispatch_argv(claude_custom, "write")
    assert "--dangerously-skip-permissions" in claude_rw
    assert "--permission-mode" not in claude_rw

    codex_binding = pc.resolve_persona(
        "programmer",
        project,
        cli_overrides={"model": "codex-gpt", "effort": "xhigh"},
        real_home=real_home,
    )
    codex_rw = pc.build_dispatch_argv(codex_binding, "write")
    assert codex_rw[codex_rw.index("--sandbox") + 1] == "workspace-write"
    assert codex_rw[codex_rw.index("--model") + 1] == "gpt-6.1-sol"
    assert "model_reasoning_effort=extra-high" in codex_rw

    codex_ro = pc.build_dispatch_argv(codex_binding, "read-only")
    assert codex_ro[codex_ro.index("--sandbox") + 1] == "read-only"

    kiro_binding = pc.resolve_persona(
        "programmer",
        project,
        cli_overrides={"model": "kiro-opus", "effort": "high"},
        real_home=real_home,
    )
    kiro_rw = pc.build_dispatch_argv(kiro_binding, "write")
    assert kiro_rw[0] == "kiro-cli"
    assert "--trust-all-tools" in kiro_rw
    assert kiro_rw[kiro_rw.index("--model") + 1] == "claude-opus-5.5"
    assert kiro_rw[kiro_rw.index("--effort") + 1] == "high"
    assert pc.build_dispatch_argv(kiro_binding, "read-only") == kiro_rw

    # Check kiro binary fallback when only "kiro" is on PATH.
    (bin_dir / "kiro-cli").unlink()
    kiro_exe = bin_dir / "kiro"
    kiro_exe.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    kiro_exe.chmod(0o755)
    assert pc.build_dispatch_argv(kiro_binding, "write")[0] == "kiro"

    # build_dispatch_env: Kiro restores real HOME when .kiro exists; agy leaves env unchanged.
    kiro_real_home = tmp_path / "kiro_user"
    (kiro_real_home / ".kiro").mkdir(parents=True)
    base_env = {"HOME": str(kiro_real_home / "antigravity_homes" / "p1"), "PATH": str(bin_dir)}
    kiro_env = pc.build_dispatch_env(kiro_rw, base_env)
    assert kiro_env["HOME"] == str(kiro_real_home)

    agy_env = pc.build_dispatch_env(
        pc.build_dispatch_argv(prog_hydrogen, "write"),
        base_env,
    )
    assert agy_env == base_env
    assert agy_env["HOME"] == base_env["HOME"]


def test_fpg_fr_01_quota_gate_stops_on_insufficient_and_tolerates_unknown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """FPG-FR-01: Quota gate stops on insufficient quota and tolerates unknown quota."""
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    dc = _load_module("dev_config", DEV_CONFIG_SCRIPT)

    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    _write_json(
        project / ".agents" / "config" / "personas.json",
        {
            "overrides": {
                "programmer": {"model": "hydrogen", "effort": "xhigh"},
                "ai_architect_reviewer": {"model": "claude-opus", "effort": "high"},
            }
        },
    )

    healthy_claude = {
        "status": "ACTIVE",
        "gemini5h": {"fraction": 0.8},
        "geminiWeekly": {"fraction": 0.5},
    }

    # Case 1: programmer on agy hydrogen with 5H=12.0%, claude healthy -> exit 2
    def fetcher_low_5h(cli: str) -> dict[str, Any]:
        if cli == "agy":
            return {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.12},
                "argonWeekly": {"fraction": 0.05},
            }
        if cli == "claude":
            return healthy_claude
        return {}

    rc1 = dc.cmd_quota_check(
        project,
        personas=("programmer", "ai_architect_reviewer"),
        json_output=True,
        fetcher=fetcher_low_5h,
        real_home=real_home,
    )
    assert rc1 == 2
    out1 = json.loads(capsys.readouterr().out)
    assert out1["sufficient"] is False
    by_p1 = {p["persona"]: p for p in out1["personas"]}
    assert by_p1["programmer"]["sufficient"] is False
    assert "5H=12.0%" in by_p1["programmer"]["quota_line"]
    assert by_p1["ai_architect_reviewer"]["sufficient"] is True

    # Case 2: programmer on hydrogen (5H=0.0% -> insufficient), architect on argon (Argon=90.0% -> sufficient)
    _write_json(
        project / ".agents" / "config" / "personas.json",
        {
            "overrides": {
                "programmer": {"model": "hydrogen", "effort": "xhigh"},
                "ai_architect_reviewer": {"model": "argon", "effort": "high"},
            }
        },
    )

    def fetcher_argon_healthy(cli: str) -> dict[str, Any]:
        if cli == "agy":
            return {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.0},
                "argonWeekly": {"fraction": 0.9},
            }
        return {}

    rc2 = dc.cmd_quota_check(
        project,
        personas=("programmer", "ai_architect_reviewer"),
        json_output=True,
        fetcher=fetcher_argon_healthy,
        real_home=real_home,
    )
    assert rc2 == 2
    out2 = json.loads(capsys.readouterr().out)
    by_p2 = {p["persona"]: p for p in out2["personas"]}
    assert by_p2["programmer"]["sufficient"] is False
    assert by_p2["programmer"]["quota_line"] == "5H=0.0%"
    assert by_p2["ai_architect_reviewer"]["sufficient"] is True
    assert by_p2["ai_architect_reviewer"]["quota_line"] == "Argon=90.0%"

    # Case 3: custom catalogue alias "my-argon" without explicit quota_pool derives argonWeekly from id
    _write_json(
        project / ".agents" / "config" / "personas.json",
        {
            "models": {
                "my-argon": {
                    "cli": "agy",
                    "id": "gemini-4-argon-{effort}",
                    "efforts": ["high"],
                }
            },
            "overrides": {
                "programmer": {"model": "my-argon", "effort": "high"},
                "ai_architect_reviewer": {"model": "argon", "effort": "high"},
            },
        },
    )
    prog_my_argon = pc.resolve_persona("programmer", project, real_home=real_home)
    assert pc.quota_pool_for(prog_my_argon) == "argonWeekly"
    rc3 = dc.cmd_quota_check(
        project,
        personas=("programmer",),
        json_output=True,
        fetcher=fetcher_argon_healthy,
        real_home=real_home,
    )
    assert rc3 == 0
    out3 = json.loads(capsys.readouterr().out)
    assert out3["personas"][0]["sufficient"] is True
    assert out3["personas"][0]["quota_line"] == "Argon=90.0%"

    # Case 4: project replaces built-in "hydrogen" with explicit quota_pool="argonWeekly"
    _write_json(
        project / ".agents" / "config" / "personas.json",
        {
            "models": {
                "hydrogen": {
                    "cli": "agy",
                    "id": "gemini-4-hydrogen-{effort}",
                    "efforts": ["high", "xhigh"],
                    "quota_pool": "argonWeekly",
                }
            },
            "overrides": {
                "programmer": {"model": "hydrogen", "effort": "xhigh"},
            },
        },
    )
    prog_override_pool = pc.resolve_persona("programmer", project, real_home=real_home)
    assert pc.quota_pool_for(prog_override_pool) == "argonWeekly"
    rc4 = dc.cmd_quota_check(
        project,
        personas=("programmer",),
        json_output=True,
        fetcher=fetcher_argon_healthy,
        real_home=real_home,
    )
    assert rc4 == 0
    out4 = json.loads(capsys.readouterr().out)
    assert out4["personas"][0]["sufficient"] is True
    assert out4["personas"][0]["quota_line"] == "Argon=90.0%"

    # Case 5: empty fetcher payload for every CLI -> exit 0 and warning "quota_unknown"
    rc5 = dc.cmd_quota_check(
        project,
        json_output=True,
        fetcher=lambda _cli: {},
        real_home=real_home,
    )
    assert rc5 == 0
    out5 = json.loads(capsys.readouterr().out)
    assert out5["sufficient"] is True
    assert len(out5["personas"]) == 3
    assert all(
        entry["sufficient"] is True and entry["warning"] == "quota_unknown"
        for entry in out5["personas"]
    )


@pytest.mark.parametrize(
    ("exit_code", "stdout", "stderr", "expected"),
    [
        (1, "", "HTTP 429 Too Many Requests", "model_unavailable"),
        (1, "", "RESOURCE_EXHAUSTED: quota exceeded", "model_unavailable"),
        (1, "", "ResourceExhausted from backend", "model_unavailable"),
        (1, "", "CLI binary 'agy' not found on PATH", "model_unavailable"),
        (127, "", "agy: command not found", "model_unavailable"),
        (1, "", "401 Unauthorized: please log in", "model_unavailable"),
        (1, "", "403 Forbidden: access denied", "model_unavailable"),
        (1, "", "Failed to spawn process: permission denied", "model_unavailable"),
        (1, "", "Error: usage limit reached; login required", "model_unavailable"),
        (1, "", "not authenticated; please sign in", "model_unavailable"),
        (1, "3 failed, 10 passed", "", "task_failure"),
        (1, "401 failed, 403 passed", "", "task_failure"),
        (1, "FAILED tests/test_x.py::test_quota_check", "", "task_failure"),
        (1, "HTTP 429 Too Many Requests", "AssertionError: boom", "task_failure"),
        (0, "rate limit handled", "", None),
        (0, "", "HTTP 429 Too Many Requests", None),
    ],
)
def test_fpg_fr_02_dispatch_failure_classification(
    exit_code: int, stdout: str, stderr: str, expected: str | None
) -> None:
    """FPG-FR-02: Dispatch failures classify as model_unavailable only for quota, auth and missing CLI."""
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    assert pc.classify_dispatch_failure(exit_code, stdout, stderr) == expected


@pytest.mark.parametrize(
    ("alias", "cli", "model_id", "effort", "mode", "expected_argv"),
    [
        (
            "argon",
            "agy",
            "gemini-4-argon-high",
            "high",
            "read-only",
            ["agy", "--sandbox", "--mode", "plan", "--model", "gemini-4-argon-high", "--effort", "high"],
        ),
        (
            "hydrogen",
            "agy",
            "gemini-4-hydrogen-xhigh",
            "xhigh",
            "write",
            ["agy", "--model", "gemini-4-hydrogen-xhigh", "--effort", "xhigh", "--mode", "auto"],
        ),
        (
            "claude-opus",
            "claude",
            "opus",
            "high",
            "read-only",
            ["claude", "-p", "--model", "opus", "--effort", "high", "--permission-mode", "plan"],
        ),
        (
            "claude-sonnet",
            "claude",
            "sonnet",
            "medium",
            "write",
            ["claude", "-p", "--model", "sonnet", "--effort", "medium", "--dangerously-skip-permissions"],
        ),
        (
            "codex-gpt",
            "codex",
            "gpt-6.1-sol",
            "medium",
            "read-only",
            [
                "codex",
                "exec",
                "--sandbox",
                "read-only",
                "--model",
                "gpt-6.1-sol",
                "-c",
                "model_reasoning_effort=medium",
                "-",
            ],
        ),
        (
            "codex-gpt",
            "codex",
            "gpt-6.1-sol",
            "xhigh",
            "write",
            [
                "codex",
                "exec",
                "--sandbox",
                "workspace-write",
                "--model",
                "gpt-6.1-sol",
                "-c",
                "model_reasoning_effort=extra-high",
                "-",
            ],
        ),
        (
            "kiro-opus",
            "kiro",
            "claude-opus-5.5",
            "high",
            "read-only",
            [
                "kiro-cli",
                "chat",
                "--no-interactive",
                "--trust-all-tools",
                "--wrap",
                "never",
                "--model",
                "claude-opus-5.5",
                "--effort",
                "high",
            ],
        ),
        (
            "kiro-opus",
            "kiro",
            "claude-opus-5.5",
            "high",
            "write",
            [
                "kiro-cli",
                "chat",
                "--no-interactive",
                "--trust-all-tools",
                "--wrap",
                "never",
                "--model",
                "claude-opus-5.5",
                "--effort",
                "high",
            ],
        ),
    ],
)
def test_fpg_hp_03_all_cli_mode_pairs_and_env_edge_cases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    alias: str,
    cli: str,
    model_id: str,
    effort: str,
    mode: str,
    expected_argv: list[str],
) -> None:
    """FPG-HP-03: Every CLI x mode pair produces exact expected argv and build_dispatch_env edge cases."""
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    for exe_name in ("agy", "claude", "codex", "kiro-cli"):
        exe = bin_dir / exe_name
        exe.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        exe.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    binding = pc.PersonaBinding(
        persona="programmer",
        alias=alias,
        cli=cli,
        model_id=model_id,
        effort=effort,
        quota_pool="provider",
        fallback_alias=None,
        sources={"model": "kit", "effort": "kit", "fallback_model": "kit"},
    )
    assert pc.build_dispatch_argv(binding, mode) == expected_argv

    if cli == "kiro":
        app_support_home = tmp_path / "app_home"
        (app_support_home / "Library" / "Application Support" / "kiro-cli").mkdir(parents=True)
        env_app = pc.build_dispatch_env(
            expected_argv,
            {"HOME": str(app_support_home / "antigravity_homes" / "p1")},
        )
        assert env_app["HOME"] == str(app_support_home)

        no_kiro_home = tmp_path / "empty_home"
        no_kiro_home.mkdir()
        raw_env = {"HOME": str(no_kiro_home / "antigravity_homes" / "p1")}
        assert pc.build_dispatch_env(expected_argv, raw_env) == raw_env


@pytest.mark.parametrize(
    ("model_alias", "payload", "expected_rc", "expected_ok", "expected_line_substr", "expected_warn"),
    [
        (
            "codex-gpt",
            {"status": "ACTIVE", "gemini5h": {"fraction": 0.5}, "geminiWeekly": {"fraction": 0.1}},
            0,
            True,
            "5H=50.0%, 7D=10.0%, status=ACTIVE",
            None,
        ),
        (
            "codex-gpt",
            {"status": "ACTIVE", "gemini5h": {"fraction": 0.14}, "geminiWeekly": {"fraction": 0.5}},
            2,
            False,
            "5H=14.0%",
            None,
        ),
        (
            "codex-gpt",
            {"status": "ACTIVE", "gemini5h": {"fraction": 0.5}, "geminiWeekly": {"fraction": 0.02}},
            2,
            False,
            "7D=2.0%",
            None,
        ),
        (
            "kiro-opus",
            {"status": "ACTIVE", "creditsPool": {"fraction": 0.2, "limit": 1000.0, "remaining": 200.0}},
            0,
            True,
            "monthly=20.0% (200.0 credits)",
            None,
        ),
        (
            "kiro-opus",
            {"status": "ACTIVE", "creditsPool": {"fraction": 0.5, "limit": 100.0, "remaining": 10.0}},
            2,
            False,
            "10.0 credits",
            None,
        ),
        (
            "hydrogen",
            {"success": False, "error": "network timeout"},
            0,
            True,
            "",
            "quota_unknown",
        ),
    ],
)
def test_fpg_fr_01_provider_and_error_payloads(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    model_alias: str,
    payload: dict[str, Any],
    expected_rc: int,
    expected_ok: bool,
    expected_line_substr: str,
    expected_warn: str | None,
) -> None:
    """FPG-FR-01: Provider quota thresholds (codex, kiro) and error payloads behave accurately."""
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    dc = _load_module("dev_config", DEV_CONFIG_SCRIPT)

    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    _write_json(
        project / ".agents" / "config" / "personas.json",
        {"overrides": {"programmer": {"model": model_alias, "effort": "high"}}},
    )

    rc = dc.cmd_quota_check(
        project,
        personas=("programmer",),
        json_output=True,
        fetcher=lambda _cli: payload,
        real_home=real_home,
    )
    assert rc == expected_rc
    out = json.loads(capsys.readouterr().out)
    entry = out["personas"][0]
    assert entry["sufficient"] is expected_ok
    assert expected_line_substr in entry["quota_line"]
    assert entry["warning"] == expected_warn

    # Verify quota_pool_for ignores alias names and uses resolved quota_pool only.
    swapped = pc.PersonaBinding(
        persona="programmer",
        alias="hydrogen",
        cli="agy",
        model_id="gemini-4-argon-high",
        effort="high",
        quota_pool="argonWeekly",
        fallback_alias=None,
        sources={},
    )
    assert pc.quota_pool_for(swapped) == "argonWeekly"


def test_fpg_fr_02_additional_stderr_signatures() -> None:
    """FPG-FR-02: Additional case-insensitive quota and rate-limit stderr signatures classify properly."""
    pc = _load_module("persona_config", PERSONA_CONFIG_SCRIPT)
    for err in (
        "Quota Exhausted for project",
        "Rate limit exceeded; retry later",
        "Rate-limited exceeded",
    ):
        assert pc.classify_dispatch_failure(1, "", err) == "model_unavailable"


def test_fpg_fr_01_review_config_thresholds_and_default_fetcher_hook(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """FPG-FR-01: .devtool/review_config.json quota_thresholds and _default_quota_fetcher wiring."""
    dc = _load_module("dev_config", DEV_CONFIG_SCRIPT)
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    _write_json(
        project / ".devtool" / "review_config.json",
        {"quota_thresholds": {"5h_min_fraction": 0.9}},
    )

    review_mod = dc._load_external_review_module()
    monkeypatch.setattr(
        review_mod,
        "_default_quota_fetcher",
        lambda _cli: {"status": "ACTIVE", "gemini5h": {"fraction": 0.8}},
    )
    rc = dc.cmd_quota_check(
        project,
        personas=("programmer",),
        json_output=True,
        fetcher=None,
        real_home=real_home,
    )
    assert rc == 2
    out = json.loads(capsys.readouterr().out)
    assert out["personas"][0]["sufficient"] is False
    assert out["personas"][0]["quota_line"] == "5H=80.0%"

    # CLI quota-check with invalid persona exits 1
    assert (
        dc.main(["--project-root", str(project), "quota-check", "--personas", "reviewer"])
        == 1
    )
