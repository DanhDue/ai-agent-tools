"""Integration tests for run_external_review layered config, per-kind caps, thresholds, and runtime state.

Covers BDD scenarios:
- URC-HP-04: run_external_review applies separate principal and cross-model pass limits and shared global provider_priority
- URC-EC-04: Custom layered quota_thresholds control select_provider_by_quota decisions in run_external_review
- URC-ST-03: update_sticky_review_config persists last_used_provider to .devtool/state/review_runtime.json without mutating .devtool/review_config.json
- URC-AR-02: run_external_review loads persona_config relative to its plugin install path when run inside a satellite repository
- URC-FR-03: Corrupted legacy .devtool/review_config.json and .devtool/state/review_runtime.json fall back cleanly without crashing external review
"""

from __future__ import annotations

import contextlib
from datetime import datetime
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
EXT_REVIEW_DIR = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
EXT_REVIEW_PATH = EXT_REVIEW_DIR / "run_external_review.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import persona_config  # noqa: E402


def _load_external_review_module() -> ModuleType:
    if str(EXT_REVIEW_DIR) not in sys.path:
        sys.path.insert(0, str(EXT_REVIEW_DIR))
    existing = sys.modules.get("run_external_review")
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(
        "run_external_review", EXT_REVIEW_PATH
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_external_review"] = mod
    spec.loader.exec_module(mod)
    return mod


rer: Any = _load_external_review_module()


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _init_git_repo(repo: Path) -> str:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "urc@example.com")
    _git(repo, "config", "user.name", "URC Test")
    (repo / "README.md").write_text("# URC Test Repo\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Base commit")
    return _git(repo, "rev-parse", "HEAD")


def _two_completed_rounds_markdown(title: str, kind_line: str) -> str:
    return (
        f"# {title}: demo\n\n"
        "## Round 1\n\n"
        "- **SHA**: 1111111\n"
        "- **CLI**: codex\n"
        "- **Model**: gpt-6.1-sol\n"
        "- **Thinking**: high\n"
        f"{kind_line}"
        "- **Status**: completed\n"
        "- **Verdict**: CHANGES REQUIRED\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "|---|----------|----------|---------|----------|\n"
        "| 1 | Important | src/a.py:10 | gap one | fixed in 2222222 |\n\n"
        "Raw output:\n\n```text\nVerdict: CHANGES REQUIRED\n```\n\n"
        "## Round 2\n\n"
        "- **SHA**: 2222222\n"
        "- **CLI**: codex\n"
        "- **Model**: gpt-6.1-sol\n"
        "- **Thinking**: high\n"
        f"{kind_line}"
        "- **Status**: completed\n"
        "- **Verdict**: CHANGES REQUIRED\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "|---|----------|----------|---------|----------|\n"
        "| 1 | Critical | src/b.py:20 | still broken |  |\n\n"
        "Raw output:\n\n```text\nVerdict: CHANGES REQUIRED\n```\n"
    )


def _require_urc_api() -> tuple[Any, Any, Any]:
    resolve_max_rounds = getattr(rer, "resolve_effective_max_rounds", None)
    load_runtime = getattr(rer, "load_review_runtime", None)
    save_runtime = getattr(rer, "save_review_runtime", None)
    if resolve_max_rounds is None:
        pytest.fail(
            "run_external_review.resolve_effective_max_rounds is not implemented yet"
        )
    if load_runtime is None or save_runtime is None:
        pytest.fail("run_external_review runtime state helpers are not implemented yet")
    return resolve_max_rounds, load_runtime, save_runtime


def test_urc_hp_04_per_kind_pass_limits_and_global_priority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """[URC-HP-04] run_external_review applies separate principal/cross-model pass limits and global priority."""
    resolve_max_rounds, _, _ = _require_urc_api()

    fake_home = tmp_path / "home"
    repo = tmp_path / "repo"
    fake_home.mkdir()
    base_sha = _init_git_repo(repo)

    _write_json(
        fake_home / ".d3nexus" / "personas.json",
        {
            "schema_version": 1,
            "max_principal_review_passes": 2,
            "max_cross_model_review_passes": 4,
            "review": {
                "provider_priority": ["codex", "claude", "kiro", "agy"],
            },
        },
    )

    assert resolve_max_rounds(repo, "principal", None, real_home=fake_home) == 2
    assert resolve_max_rounds(repo, "code", None, real_home=fake_home) == 4
    assert resolve_max_rounds(repo, "epic", None, real_home=fake_home) == 4

    cfg = rer.load_review_config(repo, real_home=fake_home)
    assert cfg["provider_priority"] == ["codex", "claude", "kiro", "agy"]
    assert cfg["max_principal_review_passes"] == 2
    assert cfg["max_cross_model_review_passes"] == 4
    assert cfg["max_rounds"] == 4
    assert cfg["providers"]["claude"]["model"] == "opus"
    assert cfg["providers"]["claude"]["effort"] == "high"
    assert cfg["providers"]["claude"]["thinking_level"] == "high"
    assert cfg["providers"]["ollama"]["host"] == "http://localhost:11434"
    assert not (repo / ".devtool" / "review_config.json").exists()

    # Explicit CLI --max-rounds overrides both review kinds
    assert resolve_max_rounds(repo, "principal", 5, real_home=fake_home) == 5
    assert resolve_max_rounds(repo, "code", 5, real_home=fake_home) == 5
    assert resolve_max_rounds(repo, "epic", 5, real_home=fake_home) == 5

    # CLI wiring: triage, status, and run honor kind-specific caps when --max-rounds is omitted
    epic_dir = repo / ".devtool" / "epic" / "demo"
    epic_dir.mkdir(parents=True)
    (epic_dir / "principal_review.md").write_text(
        _two_completed_rounds_markdown("Principal Review", "- **Kind**: principal\n"),
        encoding="utf-8",
    )
    (epic_dir / "review_results.md").write_text(
        _two_completed_rounds_markdown("Cross-Model Review", ""),
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Add review rounds")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for tool in ("git", "bash"):
        found = shutil.which(tool)
        if found is not None:
            (bin_dir / tool).symlink_to(found)
    fake_codex = bin_dir / "codex"
    fake_codex.write_text("#!/bin/bash\necho 'Verdict: PASS'\n", encoding="utf-8")
    fake_codex.chmod(0o755)

    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("REAL_HOME", str(fake_home))
    monkeypatch.setenv("PATH", str(bin_dir))
    monkeypatch.chdir(repo)

    pr_out = io.StringIO()
    with contextlib.redirect_stdout(pr_out):
        assert rer.main(["triage", "--kind", "principal", "--epic-dir", "demo"]) == 0
    assert "- **Round**: 2 / 2" in pr_out.getvalue()
    assert "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)" in pr_out.getvalue()

    code_out = io.StringIO()
    with contextlib.redirect_stdout(code_out):
        assert rer.main(["triage", "--kind", "code", "--epic-dir", "demo"]) == 0
    assert "- **Round**: 2 / 4" in code_out.getvalue()
    assert "AUTO_FIX_ELIGIBLE" in code_out.getvalue()

    override_out = io.StringIO()
    with contextlib.redirect_stdout(override_out):
        assert (
            rer.main(
                [
                    "triage",
                    "--kind",
                    "principal",
                    "--epic-dir",
                    "demo",
                    "--max-rounds",
                    "5",
                ]
            )
            == 0
        )
    assert "- **Round**: 2 / 5" in override_out.getvalue()

    # status subcommand writes kind-specific max_rounds into heartbeat
    assert (
        rer.main(
            [
                "status",
                "--kind",
                "principal",
                "--epic-dir",
                "demo",
                "--phase",
                "fixing",
            ]
        )
        == 0
    )
    hb_path = repo / ".devtool" / "state" / "demo.heartbeat.json"
    assert hb_path.is_file()
    hb_data = json.loads(hb_path.read_text(encoding="utf-8"))
    assert hb_data["review_state"]["max_rounds"] == 2

    # Commit heartbeat state before testing `run` clean-tree check
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Record heartbeat before run")

    # run --kind principal halts at 2 completed rounds (principal cap = 2, not hardcoded 3)
    run_err = io.StringIO()
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(run_err),
    ):
        rc = rer.main(
            [
                "run",
                "--kind",
                "principal",
                "--epic-dir",
                "demo",
                "--base",
                base_sha,
                "--cli",
                "codex",
            ]
        )
    assert rc == 2
    assert "Max review rounds (2) reached" in run_err.getvalue()


def test_urc_ec_04_custom_layered_quota_thresholds_control_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """[URC-EC-04] Custom layered quota_thresholds control select_provider_by_quota decisions."""
    _require_urc_api()

    fake_home = tmp_path / "home"
    repo = tmp_path / "repo"
    fake_home.mkdir()
    repo.mkdir()

    _write_json(
        fake_home / ".d3nexus" / "personas.json",
        {
            "schema_version": 1,
            "review": {
                "provider_priority": ["claude", "codex"],
                "quota_thresholds": {"5h_min_fraction": 0.50},
            },
        },
    )

    quotas: dict[str, dict[str, Any]] = {
        "claude": {
            "status": "ACTIVE",
            "gemini5h": {"fraction": 0.35},
            "geminiWeekly": {"fraction": 0.80},
        },
        "codex": {
            "status": "ACTIVE",
            "gemini5h": {"fraction": 0.70},
            "geminiWeekly": {"fraction": 0.80},
        },
    }

    # Default threshold (0.15) would admit claude, whereas resolved 0.50 skips claude
    assert rer.evaluate_provider_quota("claude", quotas["claude"])[0] is True
    assert (
        rer.evaluate_provider_quota(
            "claude", quotas["claude"], thresholds={"5h_min_fraction": 0.50}
        )[0]
        is False
    )

    # Kiro and agy thresholds also honor dynamic overrides
    kiro_mid = {
        "status": "ACTIVE (KIRO PRO+)",
        "creditsPool": {"fraction": 0.08, "limit": 1000.0, "remaining": 20.0},
    }
    assert rer.evaluate_provider_quota("kiro", kiro_mid)[0] is True
    assert (
        rer.evaluate_provider_quota(
            "kiro",
            kiro_mid,
            thresholds={"kiro_min_fraction": 0.03, "kiro_min_credits": 25.0},
        )[0]
        is False
    )
    agy_mid = {
        "status": "ACTIVE",
        "argonWeekly": {"fraction": 0.20},
        "gemini5h": {"fraction": 0.10},
    }
    assert rer.evaluate_provider_quota("agy", agy_mid)[0] is True
    assert (
        rer.evaluate_provider_quota(
            "agy",
            agy_mid,
            thresholds={"agy_argon_min_fraction": 0.30, "5h_min_fraction": 0.50},
        )[0]
        is False
    )

    chosen_direct, diag_direct = rer.select_provider_by_quota(
        quota_fetcher=lambda p: quotas[p],
        binary_resolver=lambda _p: "/usr/bin/fake",
        priority=["claude", "codex"],
        thresholds={"5h_min_fraction": 0.50},
    )
    assert chosen_direct == "codex"
    assert any("claude: SKIPPED" in line for line in diag_direct)
    assert any("codex: ELIGIBLE" in line for line in diag_direct)

    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("REAL_HOME", str(fake_home))
    monkeypatch.setattr(rer, "resolve_cli_binary", lambda _p: "/usr/bin/fake")
    monkeypatch.setattr(rer, "_default_quota_fetcher", lambda p: quotas[p])

    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        cli, model, thinking = rer.resolve_review_settings(
            root=repo,
            epic_dir=None,
            kind="code",
            cli_arg=None,
            model_arg=None,
            thinking_arg=None,
            auto_quota=True,
        )
    assert cli == "codex"
    assert model == "gpt-6.1-sol"
    assert thinking == "high"
    assert "claude: SKIPPED" in err.getvalue()
    assert "codex: ELIGIBLE" in err.getvalue()


def test_urc_st_03_sticky_runtime_state_isolated_from_review_config(
    tmp_path: Path,
) -> None:
    """[URC-ST-03] update_sticky_review_config persists last_used_provider to review_runtime.json without mutating review_config.json."""
    _, load_runtime, _ = _require_urc_api()

    fake_home = tmp_path / "home"
    repo = tmp_path / "repo"
    fake_home.mkdir()
    repo.mkdir()

    cfg_path = repo / ".devtool" / "review_config.json"
    _write_json(
        cfg_path,
        {
            "last_used_provider": "claude",
            "providers": {
                "codex": {"model": "gpt-configured", "thinking_level": "high"},
            },
        },
    )
    bytes_before = cfg_path.read_bytes()

    initial_loaded = rer.load_review_config(repo, real_home=fake_home)
    assert cfg_path.read_bytes() == bytes_before
    assert initial_loaded["last_used_provider"] == "claude"
    assert initial_loaded["providers"]["codex"]["model"] == "gpt-configured"

    rer.update_sticky_review_config(repo, "codex", "gpt-custom", "medium")

    # .devtool/review_config.json must stay byte-identical
    assert cfg_path.read_bytes() == bytes_before

    runtime_path = repo / rer.REVIEW_RUNTIME_FILE
    assert runtime_path == repo / ".devtool" / "state" / "review_runtime.json"
    assert runtime_path.is_file()
    assert not list(runtime_path.parent.glob("*.tmp"))

    runtime_data = load_runtime(repo)
    assert runtime_data["last_used_provider"] == "codex"
    assert isinstance(runtime_data.get("updated_at"), str)
    datetime.fromisoformat(runtime_data["updated_at"])
    assert "providers" not in runtime_data
    assert "model" not in runtime_data

    # Subsequent load sees last_used_provider="codex" while preserving configured provider models
    reloaded = rer.load_review_config(repo, real_home=fake_home)
    assert reloaded["last_used_provider"] == "codex"
    assert reloaded["providers"]["codex"]["model"] == "gpt-configured"
    assert reloaded["providers"]["codex"]["thinking_level"] == "high"
    assert cfg_path.read_bytes() == bytes_before

    # Clean repository with no .devtool/review_config.json never auto-creates one
    clean_repo = tmp_path / "clean_repo"
    clean_repo.mkdir()
    rer.load_review_config(clean_repo, real_home=fake_home)
    rer.update_sticky_review_config(clean_repo, "kiro", "custom-kiro", "low")
    assert not (clean_repo / ".devtool" / "review_config.json").exists()
    assert (
        rer.load_review_config(clean_repo, real_home=fake_home)["last_used_provider"]
        == "kiro"
    )


def test_urc_ar_02_satellite_repo_loads_persona_config_relative_to_plugin(
    tmp_path: Path,
) -> None:
    """[URC-AR-02] run_external_review loads persona_config relative to its plugin install path inside a satellite repo."""
    _require_urc_api()

    fake_home = tmp_path / "home"
    satellite_repo = tmp_path / "satellite_repo"
    fake_home.mkdir()
    _init_git_repo(satellite_repo)

    assert not (satellite_repo / "scripts" / "persona_config.py").exists()

    _write_json(
        fake_home / ".d3nexus" / "personas.json",
        {
            "schema_version": 1,
            "max_principal_review_passes": 2,
            "max_cross_model_review_passes": 4,
            "review": {
                "provider_priority": ["kiro", "claude"],
            },
        },
    )
    _write_json(
        satellite_repo / ".agents" / "config" / "personas.json",
        {
            "schema_version": 1,
            "max_cross_model_review_passes": 5,
        },
    )

    probe = (
        "import importlib.util, json, sys\n"
        "from pathlib import Path\n"
        f"script = Path({str(EXT_REVIEW_PATH)!r})\n"
        "spec = importlib.util.spec_from_file_location('run_external_review', script)\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "sys.modules['run_external_review'] = mod\n"
        "spec.loader.exec_module(mod)\n"
        "root = Path.cwd()\n"
        "cfg = mod.load_review_config(root)\n"
        "print(json.dumps({\n"
        "  'provider_priority': cfg['provider_priority'],\n"
        "  'principal_rounds': mod.resolve_effective_max_rounds(root, 'principal', None),\n"
        "  'code_rounds': mod.resolve_effective_max_rounds(root, 'code', None),\n"
        "  'review_config_exists': (root / '.devtool' / 'review_config.json').exists(),\n"
        "}))\n"
    )
    env = dict(os.environ)
    env["HOME"] = str(fake_home)
    env["REAL_HOME"] = str(fake_home)
    env.pop("PYTHONPATH", None)

    proc = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=satellite_repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"stderr: {proc.stderr}\nstdout: {proc.stdout}"
    payload = json.loads(proc.stdout.strip())
    assert payload["provider_priority"] == ["kiro", "claude"]
    assert payload["principal_rounds"] == 2
    assert payload["code_rounds"] == 5
    assert payload["review_config_exists"] is False


def test_urc_fr_03_corrupted_legacy_and_runtime_json_fallback_cleanly(
    tmp_path: Path,
) -> None:
    """[URC-FR-03] Corrupted legacy review_config.json and review_runtime.json fall back cleanly without crashing."""
    _, load_runtime, _ = _require_urc_api()

    fake_home = tmp_path / "home"
    repo = tmp_path / "repo"
    fake_home.mkdir()
    repo.mkdir()

    legacy_path = repo / ".devtool" / "review_config.json"
    runtime_path = repo / ".devtool" / "state" / "review_runtime.json"
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_path.parent.mkdir(parents=True, exist_ok=True)

    # Truncated invalid JSON in both files
    legacy_path.write_text('{"provider_priority": ["codex"', encoding="utf-8")
    runtime_path.write_text('{"last_used_provider": "kiro"', encoding="utf-8")

    resolved_pc = persona_config.resolve_review_config(repo, real_home=fake_home)
    assert resolved_pc.provider_priority == ("claude", "codex", "kiro", "agy")
    assert resolved_pc.limits.max_principal_review_passes == 3
    assert resolved_pc.limits.max_cross_model_review_passes == 3

    assert load_runtime(repo) == {}
    loaded = rer.load_review_config(repo, real_home=fake_home)
    assert loaded["last_used_provider"] == "claude"
    assert loaded["provider_priority"] == ["claude", "codex", "kiro", "agy"]
    assert loaded["max_rounds"] == 3
    assert loaded["max_principal_review_passes"] == 3
    assert loaded["max_cross_model_review_passes"] == 3

    # Non-UTF-8 bytes and non-dict JSON also fall back cleanly to global layer when present
    _write_json(
        fake_home / ".d3nexus" / "personas.json",
        {
            "schema_version": 1,
            "max_principal_review_passes": 2,
            "review": {"provider_priority": ["codex", "kiro"]},
        },
    )
    legacy_path.write_bytes(b"\xff\xfe\x00\x00")
    runtime_path.write_text("[]", encoding="utf-8")

    assert load_runtime(repo) == {}
    loaded_global = rer.load_review_config(repo, real_home=fake_home)
    assert loaded_global["last_used_provider"] == "claude"
    assert loaded_global["provider_priority"] == ["codex", "kiro"]
    assert loaded_global["max_principal_review_passes"] == 2
    assert loaded_global["max_cross_model_review_passes"] == 3
