"""Tier C end-to-end acceptance tests for unified review config, docs, and verify.sh registry.

Covers BDD scenarios:
- URC-HP-06: End-to-end dev-config changes propagate cleanly to external review, runner, docs, and verify.sh registry
- URC-EC-05: Fixed-effort catalogue alias in review.providers resolves effort to "none" and preserves zero-cap fix passes
- URC-FR-04: Running dev_config limits or review commands on missing directories creates parent folders atomically without leaving .tmp artifacts
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
DEV_CONFIG_SCRIPT = SCRIPTS_DIR / "dev_config.py"
EXT_REVIEW_DIR = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
EXT_REVIEW_PATH = EXT_REVIEW_DIR / "run_external_review.py"
RUNNER_SCRIPTS_DIR = REPO_ROOT / "skills" / "dev-lifecycle" / "resources" / "scripts"

for _extra_dir in (SCRIPTS_DIR, RUNNER_SCRIPTS_DIR):
    if str(_extra_dir) not in sys.path:
        sys.path.insert(0, str(_extra_dir))

import agy_dispatch  # noqa: E402
import dev_config  # noqa: E402
from lifecycle_runner import LifecycleRunner, RunnerConfig  # noqa: E402
import persona_config  # noqa: E402

EXPECTED_URC_SUITES: tuple[tuple[str, str, str, int, bool], ...] = (
    ("26", "pytest", "tests/test_urc_persona_review_config.py", 15, False),
    ("26", "pytest", "tests/test_urc_dev_config_cli.py", 15, False),
    ("26", "pytest", "tests/test_urc_external_review_integration.py", 15, False),
    ("26", "pytest", "tests/test_urc_lifecycle_runner_review_config.py", 15, False),
    ("26", "pytest", "tests/test_urc_end_to_end_acceptance.py", 15, True),
)


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


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _parse_frontmatter_keys(text: str) -> list[str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match is not None, "Expected YAML frontmatter delimited by --- lines"
    return [
        line.split(":", 1)[0].strip()
        for line in match.group(1).splitlines()
        if re.match(r"^[A-Za-z0-9_-]+:", line)
    ]


def _parse_verify_suites(verify_text: str) -> list[tuple[str, str, str, int, bool]]:
    match = re.search(
        r"^SUITES\s*=\s*(\[.*?\n\])", verify_text, flags=re.MULTILINE | re.DOTALL
    )
    assert match is not None, "Could not locate SUITES = [...] in scripts/verify.sh"
    parsed = ast.literal_eval(match.group(1))
    assert isinstance(parsed, list)
    return [
        (str(item[0]), str(item[1]), str(item[2]), int(item[3]), bool(item[4]))
        for item in parsed
    ]


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


def _assert_docs_and_verify_registry() -> None:
    # 1. skills/dev-config/SKILL.md
    dev_cfg_skill = _read("skills/dev-config/SKILL.md")
    assert _parse_frontmatter_keys(dev_cfg_skill) == ["name", "description"]
    assert "superpowers:" not in dev_cfg_skill
    for token in (
        "limits [--json]",
        "limits reset",
        "review status",
        "review priority",
        "review set",
        "review thresholds",
        "review reset",
        "max_principal_review_passes",
        "max_cross_model_review_passes",
        ".devtool/state/review_runtime.json",
        ".devtool/review_config.json",
    ):
        assert token in dev_cfg_skill, f"skills/dev-config/SKILL.md missing {token!r}"

    # 2. skills/principal-review/SKILL.md
    pr_skill = _read("skills/principal-review/SKILL.md")
    assert _parse_frontmatter_keys(pr_skill) == ["name", "description"]
    assert "superpowers:" not in pr_skill
    for token in (
        "/d3nexus:dev-config review",
        "max_principal_review_passes",
        ".devtool/state/review_runtime.json",
        ".devtool/review_config.json",
    ):
        assert token in pr_skill, f"skills/principal-review/SKILL.md missing {token!r}"

    # 3. skills/cross-model-review/SKILL.md
    cmr_skill = _read("skills/cross-model-review/SKILL.md")
    assert _parse_frontmatter_keys(cmr_skill) == ["name", "description"]
    assert "superpowers:" not in cmr_skill
    for token in (
        "/d3nexus:dev-config review",
        "max_cross_model_review_passes",
        ".devtool/state/review_runtime.json",
        ".devtool/review_config.json",
    ):
        assert token in cmr_skill, (
            f"skills/cross-model-review/SKILL.md missing {token!r}"
        )

    # 4. skills/dev-lifecycle/SKILL.md
    lc_skill = _read("skills/dev-lifecycle/SKILL.md")
    assert _parse_frontmatter_keys(lc_skill) == ["name", "description"]
    assert "superpowers:" not in lc_skill
    lc_words = len(lc_skill.split())
    assert lc_words <= 2500, (
        f"skills/dev-lifecycle/SKILL.md exceeds 2500 words: {lc_words}"
    )
    for token in (
        "/d3nexus:dev-config review",
        "/d3nexus:dev-config limits",
        ".devtool/review_config.json",
    ):
        assert token in lc_skill, f"skills/dev-lifecycle/SKILL.md missing {token!r}"

    # 5. rules/CRITICAL_RULES.md (word cap <= 1000, byte cap <= 8192)
    critical_rules = _read("rules/CRITICAL_RULES.md")
    assert critical_rules.startswith("---\ntrigger: always_on\n---")
    assert "superpowers:" not in critical_rules
    cr_words = len(critical_rules.split())
    cr_bytes = len(critical_rules.encode("utf-8"))
    assert cr_words <= 1000, f"rules/CRITICAL_RULES.md exceeds 1000 words: {cr_words}"
    assert cr_bytes <= 8192, f"rules/CRITICAL_RULES.md exceeds 8192 bytes: {cr_bytes}"
    for token in (
        "/d3nexus:dev-config review",
        "/d3nexus:dev-config limits",
        ".devtool/review_config.json",
    ):
        assert token in critical_rules, f"rules/CRITICAL_RULES.md missing {token!r}"

    # 6. docs/dev-config-quick-guide.en.md
    quick_guide = _read("docs/dev-config-quick-guide.en.md")
    for token in (
        "dev-config limits",
        "dev-config review",
        "max_principal_review_passes",
        "max_cross_model_review_passes",
        "provider_priority",
        ".devtool/state/review_runtime.json",
        ".devtool/review_config.json",
        "read-only",
    ):
        assert token in quick_guide, (
            f"docs/dev-config-quick-guide.en.md missing {token!r}"
        )

    # 7. scripts/verify.sh section 26 suite registration
    verify_text = _read("scripts/verify.sh")
    assert "# 26. Unified Review Config suites" in verify_text
    suites = _parse_verify_suites(verify_text)
    by_path = {entry[2]: entry for entry in suites}
    counts: dict[str, int] = {}
    for entry in suites:
        counts[entry[2]] = counts.get(entry[2], 0) + 1

    for expected in EXPECTED_URC_SUITES:
        suite_rel = expected[2]
        assert (REPO_ROOT / suite_rel).is_file(), f"Missing URC suite: {suite_rel}"
        assert counts.get(suite_rel, 0) == 1, (
            f"Expected {suite_rel} registered once in scripts/verify.sh, got {counts.get(suite_rel, 0)}"
        )
        assert by_path[suite_rel] == expected, (
            f"Unexpected verify.sh entry for {suite_rel}: {by_path[suite_rel]!r} != {expected!r}"
        )


def _assert_urc_hp_06(tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    repo = tmp_path / "repo"
    fake_home.mkdir()
    (repo / ".devtool" / "epic" / "demo").mkdir(parents=True)
    (repo / ".devtool" / "state").mkdir(parents=True)

    # Write global and project settings exclusively via dev_config.py CLI
    cli_steps = [
        [
            "limits",
            "--task-review",
            "3",
            "--fix",
            "2",
            "--principal-review",
            "2",
            "--cross-model-review",
            "4",
            "--scope",
            "global",
        ],
        ["review", "priority", "codex,claude,kiro,agy", "--scope", "global"],
        [
            "review",
            "set",
            "agy",
            "--model",
            "argon",
            "--effort",
            "medium",
            "--scope",
            "global",
        ],
        [
            "review",
            "set",
            "claude",
            "--model",
            "claude-sonnet-4-6",
            "--effort",
            "low",
            "--scope",
            "global",
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
        [
            "limits",
            "--cross-model-review",
            "5",
            "--fix",
            "0",
            "--scope",
            "project",
        ],
        ["review", "priority", "kiro,codex,claude,agy", "--scope", "project"],
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
        ["review", "thresholds", "--7d", "0.05", "--scope", "project"],
    ]
    for argv in cli_steps:
        res = _run_dev_config(argv, cwd=repo, real_home=fake_home)
        assert res.returncode == 0, f"{argv} failed: {res.stderr}"

    expected_priority = ["kiro", "codex", "claude", "agy"]
    expected_thresholds = {
        "5h_min_fraction": 0.25,
        "7d_min_fraction": 0.05,
        "kiro_min_fraction": 0.03,
        "kiro_min_credits": 25.0,
        "agy_argon_min_fraction": 0.10,
    }
    expected_model_ids = {
        "claude": ("claude-sonnet-4-6", "low"),
        "codex": ("gpt-6.1-sol", "high"),
        "kiro": ("claude-opus-5.5", "high"),
        "agy": ("gemini-4-argon-medium", "medium"),
        "ollama": ("qwen2.5-coder:32b", "high"),
    }

    # 1. dev_config.py status --json
    res_status = _run_dev_config(["status", "--json"], cwd=repo, real_home=fake_home)
    assert res_status.returncode == 0, res_status.stderr
    status_payload = json.loads(res_status.stdout)
    assert status_payload["task_review_limits"] == {
        "max_task_review_passes": 3,
        "max_fix_passes": 0,
    }
    assert status_payload["review_limits"] == {
        "max_task_review_passes": 3,
        "max_fix_passes": 0,
        "max_principal_review_passes": 2,
        "max_cross_model_review_passes": 5,
        "sources": {
            "max_task_review_passes": "global",
            "max_fix_passes": "project",
            "max_principal_review_passes": "global",
            "max_cross_model_review_passes": "project",
        },
    }
    assert status_payload["review"]["provider_priority"] == expected_priority
    assert status_payload["review"]["quota_thresholds"] == expected_thresholds
    for cli_name, (exp_id, exp_effort) in expected_model_ids.items():
        assert status_payload["review"]["providers"][cli_name]["model_id"] == exp_id
        assert status_payload["review"]["providers"][cli_name]["effort"] == exp_effort
    assert (
        status_payload["review"]["providers"]["ollama"]["host"]
        == "http://127.0.0.1:11434"
    )

    # 2. persona_config, dev_config thresholds, and agy_dispatch thresholds
    resolved = persona_config.resolve_review_config(repo, real_home=fake_home)
    assert list(resolved.provider_priority) == expected_priority
    assert resolved.quota_thresholds == expected_thresholds
    assert resolved.limits.max_task_review_passes == 3
    assert resolved.limits.max_fix_passes == 0
    assert resolved.limits.max_principal_review_passes == 2
    assert resolved.limits.max_cross_model_review_passes == 5
    assert dev_config._load_quota_thresholds(repo, real_home=fake_home) == (
        expected_thresholds
    )
    assert agy_dispatch._load_thresholds(repo, real_home=fake_home) == (
        expected_thresholds
    )

    # 3. run_external_review.load_review_config & resolve_effective_max_rounds
    ext_cfg = rer.load_review_config(repo, real_home=fake_home)
    assert ext_cfg["provider_priority"] == expected_priority
    assert ext_cfg["quota_thresholds"] == expected_thresholds
    assert ext_cfg["max_principal_review_passes"] == 2
    assert ext_cfg["max_cross_model_review_passes"] == 5
    for cli_name, (exp_id, exp_effort) in expected_model_ids.items():
        assert ext_cfg["providers"][cli_name]["model"] == exp_id
        assert ext_cfg["providers"][cli_name]["effort"] == exp_effort
    assert ext_cfg["providers"]["ollama"]["host"] == "http://127.0.0.1:11434"
    assert (
        rer.resolve_effective_max_rounds(repo, "principal", None, real_home=fake_home)
        == 2
    )
    assert (
        rer.resolve_effective_max_rounds(repo, "code", None, real_home=fake_home) == 5
    )
    assert (
        rer.resolve_effective_max_rounds(repo, "epic", None, real_home=fake_home) == 5
    )
    assert not (repo / ".devtool" / "review_config.json").exists()

    # 4. LifecycleRunner resolves identical per-kind caps & provider_priority
    runner = LifecycleRunner(
        root=repo, epic_slug="demo", config=RunnerConfig(real_home=fake_home)
    )
    assert runner._resolve_external_review_bounds("principal") == 2
    assert runner._resolve_external_review_bounds("code") == 5
    assert runner._resolve_review_provider_priority() == expected_priority

    # 5. Documentation, rules caps, quick guide, and scripts/verify.sh §26 registry
    _assert_docs_and_verify_registry()


def test_urc_hp_06_end_to_end_cli_propagation_and_docs_registry(
    tmp_path: Path,
) -> None:
    """[URC-HP-06] Top-level entry point for V1 RED and end-to-end propagation/docs verification."""
    _assert_urc_hp_06(tmp_path)


class Test_Integration:
    """[Tier C - Integration] End-to-end acceptance tests for unified review configuration."""

    def test_urc_hp_06_end_to_end_cli_propagation_and_docs_registry(
        self, tmp_path: Path
    ) -> None:
        """[URC-HP-06] CLI changes propagate to external review & runner, and docs/verify.sh are registered."""
        _assert_urc_hp_06(tmp_path)

    def test_urc_ec_05_fixed_effort_alias_and_zero_fix_passes(
        self, tmp_path: Path
    ) -> None:
        """[URC-EC-05] Fixed-effort catalogue alias resolves effort='none' and preserves max_fix_passes=0."""
        fake_home = tmp_path / "home"
        repo = tmp_path / "repo"
        fake_home.mkdir()
        repo.mkdir()

        _write_json(
            fake_home / ".d3nexus" / "personas.json",
            {
                "schema_version": 1,
                "max_fix_passes": 0,
                "review": {
                    "providers": {
                        "agy": {"model": "orchestrator-argon"},
                    }
                },
            },
        )

        resolved = persona_config.resolve_review_config(repo, real_home=fake_home)
        assert resolved.providers["agy"].model == "orchestrator-argon"
        assert resolved.providers["agy"].model_id == "gemini-pro-orchestrator-g1-pro"
        assert resolved.providers["agy"].effort == "none"
        assert resolved.providers["agy"].source == "global"
        assert resolved.limits.max_fix_passes == 0
        assert resolved.limits.sources["max_fix_passes"] == "global"

        res_limits = _run_dev_config(
            ["limits", "--json"], cwd=repo, real_home=fake_home
        )
        assert res_limits.returncode == 0, res_limits.stderr
        limits_payload = json.loads(res_limits.stdout)
        assert limits_payload["max_fix_passes"] == 0
        assert limits_payload["sources"]["max_fix_passes"] == "global"

        res_review = _run_dev_config(
            ["review", "status", "--json"], cwd=repo, real_home=fake_home
        )
        assert res_review.returncode == 0, res_review.stderr
        review_payload = json.loads(res_review.stdout)
        assert (
            review_payload["providers"]["agy"]["model_id"]
            == "gemini-pro-orchestrator-g1-pro"
        )
        assert review_payload["providers"]["agy"]["effort"] == "none"

        ext_cfg = rer.load_review_config(repo, real_home=fake_home)
        assert ext_cfg["providers"]["agy"]["model"] == "gemini-pro-orchestrator-g1-pro"
        assert ext_cfg["providers"]["agy"]["effort"] == "none"

    def test_urc_fr_04_missing_parent_dirs_atomic_write_no_tmp(
        self, tmp_path: Path
    ) -> None:
        """[URC-FR-04] Writing limits/review on missing parent dirs creates them atomically without .tmp artifacts."""
        fake_home = tmp_path / "home"
        repo = tmp_path / "repo"
        fake_home.mkdir()
        repo.mkdir()

        global_dir = fake_home / ".d3nexus"
        project_dir = repo / ".agents" / "config"
        assert not global_dir.exists()
        assert not (repo / ".agents").exists()

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
            cwd=repo,
            real_home=fake_home,
        )
        assert res_global.returncode == 0, res_global.stderr

        res_project = _run_dev_config(
            ["review", "priority", "codex,claude,kiro,agy", "--scope", "project"],
            cwd=repo,
            real_home=fake_home,
        )
        assert res_project.returncode == 0, res_project.stderr

        global_file = global_dir / "personas.json"
        project_file = project_dir / "personas.json"
        assert global_file.is_file()
        assert project_file.is_file()

        global_data = json.loads(global_file.read_text(encoding="utf-8"))
        project_data = json.loads(project_file.read_text(encoding="utf-8"))
        assert global_data["schema_version"] == 1
        assert global_data["max_principal_review_passes"] == 2
        assert global_data["max_cross_model_review_passes"] == 4
        assert project_data["schema_version"] == 1
        assert project_data["review"]["provider_priority"] == [
            "codex",
            "claude",
            "kiro",
            "agy",
        ]

        assert list(global_dir.rglob("*.tmp")) == []
        assert list(project_dir.rglob("*.tmp")) == []
