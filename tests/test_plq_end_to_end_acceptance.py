"""Tier C end-to-end acceptance tests for Task 06: Lifecycle docs, provider skills, verify.sh, and polyglot pipeline.

Covers BDD Scenarios:
- PLQ-HP-06: Lifecycle docs, provider skills, and verify.sh registry pass full structural and word-cap checks
- PLQ-ST-05: End-to-end polyglot lifecycle pipeline transitions cleanly from scaffold to contract check to pool triage
- PLQ-AR-05: Documentation cross-references obey d3nexus namespace and exclude forbidden prefixes
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"

CHECK_DOC_SCRIPT = (
    SKILLS_DIR / "doc_quality_check" / "resources" / "scripts" / "check_document.py"
)
SCAFFOLD_SCRIPT = (
    SKILLS_DIR
    / "setup_quality_check"
    / "resources"
    / "scripts"
    / "scaffold_quality_manifest.py"
)
VALIDATE_QC_SCRIPT = (
    SKILLS_DIR
    / "quality_check"
    / "resources"
    / "scripts"
    / "validate_quality_contract.py"
)
DIFF_COVERAGE_SCRIPT = (
    SKILLS_DIR / "quality_check" / "resources" / "scripts" / "check_diff_coverage.py"
)
CHECK_TASK_CONTRACT_SCRIPT = (
    SKILLS_DIR
    / "dev-implementation"
    / "resources"
    / "scripts"
    / "check_task_contract.py"
)
WORKER_POOL_SCRIPT = (
    SKILLS_DIR
    / "dev-implementation"
    / "resources"
    / "scripts"
    / "manage_worker_pool.py"
)

PLQ_SUITES: tuple[str, ...] = (
    "tests/test_stack_lifecycle_registry.py",
    "tests/test_check_diff_coverage.py",
    "tests/test_plq_quality_contracts_and_scaffolder.py",
    "tests/test_plq_task_contract_polyglot.py",
    "tests/test_plq_worker_pool_polyglot.py",
    "tests/test_plq_end_to_end_acceptance.py",
)

MODIFIED_MARKDOWN_FILES: tuple[str, ...] = (
    "skills/dev-designer/SKILL.md",
    "skills/dev-designer/references/verification-rows.md",
    "skills/dev-designer/references/verification-row-grammar.md",
    "skills/dev-implementation/SKILL.md",
    "skills/dev-implementation/references/worker-execution-rules.md",
    "skills/quality_check/SKILL.md",
    "skills/setup_quality_check/SKILL.md",
    "skills/flutter-quality-check/SKILL.md",
    "skills/rust-quality-check/SKILL.md",
    "skills/web-quality-check/SKILL.md",
    "skills/python-quality-check/SKILL.md",
    "skills/android-quality-check/SKILL.md",
    "skills/ios-quality-check/SKILL.md",
)

PROVIDER_SKILL_FILES: tuple[str, ...] = (
    "skills/flutter-quality-check/SKILL.md",
    "skills/rust-quality-check/SKILL.md",
    "skills/web-quality-check/SKILL.md",
    "skills/python-quality-check/SKILL.md",
    "skills/android-quality-check/SKILL.md",
    "skills/ios-quality-check/SKILL.md",
)

NEW_SKILL_FILES: tuple[str, ...] = (
    "skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py",
    "skills/quality_check/resources/scripts/_provider_manifest_common.py",
    "skills/quality_check/resources/scripts/check_diff_coverage.py",
    "skills/web-quality-check/resources/schemas/web-quality.schema.json",
)

ALL_PROFILES: tuple[str, ...] = ("pr", "epic", "scheduled", "release")
UNIFIED_CAPABILITIES: tuple[str, ...] = (
    "anti_stub",
    "security",
    "security_deps",
    "pr_diff_audit",
    "workspace_audit",
    "pr_impact",
    "workspace_impact",
    "license",
)
ALL_STACKS: tuple[str, ...] = ("python", "flutter", "rust", "web", "android", "ios")

ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".pdf"}
LEGAL_PREFIXES = ("LICENSE", "COPYING", "NOTICE")
TEXT_SUFFIXES = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ""}

PERSONAL_LEAK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"/Users/[A-Za-z0-9._-]+"),
    re.compile(r"antigravity_homes/[A-Za-z0-9._-]+"),
    re.compile(r"\bdanhdue", re.IGNORECASE),
)

ISOLATED_GIT_ENV: dict[str, str] = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "PLQ Acceptance",
    "GIT_AUTHOR_EMAIL": "plq-acceptance@example.invalid",
    "GIT_COMMITTER_NAME": "PLQ Acceptance",
    "GIT_COMMITTER_EMAIL": "plq-acceptance@example.invalid",
}


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _strip_fences_and_inline_code(text: str) -> str:
    no_fences = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`\n]*`", "", no_fences)


def _heading_anchor(heading: str) -> str:
    lowered = heading.lower()
    cleaned = re.sub(r"[^\w\s-]", "", lowered)
    return "#" + cleaned.replace(" ", "-")


def _run_py(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _git(repo: Path, *args: str, env: dict[str, str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _write(root: Path, rel_path: str, content: str) -> Path:
    target = root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def _isolated_env(home: Path, workspace_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update(ISOLATED_GIT_ENV)
    env["HOME"] = str(home)
    env["REAL_HOME"] = str(home)
    env["WORKSPACE_ROOT"] = str(workspace_root)
    for key in (
        "AGY_PROFILE",
        "ANTIGRAVITY_PROFILE",
        "AGY_PROGRAMMER_MODEL",
        "AGY_PROGRAMMER_EFFORT",
    ):
        env.pop(key, None)
    return env


def _is_skill_supporting_file(path: Path) -> bool:
    if path.name == "SKILL.md" or "__pycache__" in path.parts:
        return False
    if path.suffix.lower() in ASSET_SUFFIXES:
        return False
    if path.name.upper().startswith(LEGAL_PREFIXES):
        return False
    return not any(part.startswith(".") for part in path.parts)


def test_plq_hp_06_docs_caps_reachability_and_verify_registration() -> None:
    """[PLQ-HP-06] [Tier C - Integration] Lifecycle docs, provider skills, and verify.sh registry pass full structural and word-cap checks."""
    # 1. Word and byte cap enforcement
    dev_impl = _read("skills/dev-implementation/SKILL.md")
    impl_words = len(dev_impl.split())
    assert impl_words <= 4500, (
        f"skills/dev-implementation/SKILL.md exceeds 4500-word cap: {impl_words}"
    )

    dev_designer = _read("skills/dev-designer/SKILL.md")
    designer_bytes = len(dev_designer.encode("utf-8"))
    assert designer_bytes <= 22528, (
        f"skills/dev-designer/SKILL.md exceeds 22528-byte cap: {designer_bytes}"
    )

    # 2. dev-implementation/SKILL.md removes hardcoded uv run pytest and references registry contracts
    assert "uv run pytest" not in dev_impl, (
        "skills/dev-implementation/SKILL.md must replace hardcoded 'uv run pytest' with pointer to worker-execution-rules.md"
    )
    for token in (
        "references/worker-execution-rules.md",
        "_stack_lifecycle_registry.py",
        "TierBContractAdapter",
        "PoolWorkspaceStrategy",
        "TriageSurfaceRegistry",
        "TierCTaxonomy",
    ):
        assert token in dev_impl, (
            f"skills/dev-implementation/SKILL.md missing required token {token!r}"
        )

    # 3. worker-execution-rules.md provides 6-stack platform-mapped command table and Tier C1 vs Tier C2 discipline
    worker_rules = _read(
        "skills/dev-implementation/references/worker-execution-rules.md"
    )
    worker_rules_lower = worker_rules.lower()
    for stack in ALL_STACKS:
        assert stack in worker_rules_lower, (
            f"worker-execution-rules.md missing stack {stack!r} in 6-stack command table"
        )
    for token in (
        "Tier C1",
        "Tier C2",
        "test/integration/",
        "cargo nextest",
        "vitest",
        "tests/integration/",
        "FlowTest",
        "FlowTests",
        "# tier: C2",
    ):
        assert token in worker_rules, (
            f"worker-execution-rules.md missing Tier C1/C2 token {token!r}"
        )

    # 4. dev-designer/SKILL.md, verification-rows.md, and verification-row-grammar.md contracts
    for token in ("Tier C1", "Tier C2", "# tier: C2", "check_diff_coverage.py"):
        assert token in dev_designer, (
            f"skills/dev-designer/SKILL.md missing token {token!r}"
        )

    verification_rows = _read("skills/dev-designer/references/verification-rows.md")
    assert "-q --tb=short --maxfail=3" in verification_rows
    for token in (
        "Tier C1",
        "Tier C2",
        "# tier: C2",
        "test/integration/",
        "cargo nextest",
        "vitest",
        "tests/integration/",
        "FlowTest",
        "FlowTests",
        "playwright test",
    ):
        assert token in verification_rows, (
            f"verification-rows.md missing required token {token!r}"
        )

    grammar = _read("skills/dev-designer/references/verification-row-grammar.md")
    for token in (
        "Result: 0 problems — PASS",
        "--verbose",
        "--json",
        "# tier: C2",
        "TierCTaxonomy",
    ):
        assert token in grammar, (
            f"verification-row-grammar.md missing required token {token!r}"
        )

    # 5. quality_check, setup_quality_check, and all 6 *-quality-check SKILL.md docs
    quality_check = _read("skills/quality_check/SKILL.md")
    for token in (
        "_provider_manifest_common.py",
        "check_diff_coverage.py",
        "standards_catalog.json",
        "pool_mounts",
        "--compact",
        "--verbose",
        "--json",
        *ALL_PROFILES,
        *UNIFIED_CAPABILITIES,
    ):
        assert token in quality_check, (
            f"skills/quality_check/SKILL.md missing token {token!r}"
        )

    setup_qc = _read("skills/setup_quality_check/SKILL.md")
    assert "pkill -9 java" not in setup_qc, (
        "skills/setup_quality_check/SKILL.md must remove 'pkill -9 java'"
    )
    for token in (
        "standards_catalog.json",
        "pool_mounts",
        "check_diff_coverage.py",
        "web-quality-check/SKILL.md",
        *ALL_PROFILES,
        *UNIFIED_CAPABILITIES,
    ):
        assert token in setup_qc, (
            f"skills/setup_quality_check/SKILL.md missing token {token!r}"
        )

    android_qc = _read("skills/android-quality-check/SKILL.md")
    assert "pkill -9 java" not in android_qc, (
        "skills/android-quality-check/SKILL.md must remove 'pkill -9 java'"
    )

    web_qc = _read("skills/web-quality-check/SKILL.md")
    assert "resources/schemas/web-quality.schema.json" in web_qc, (
        "skills/web-quality-check/SKILL.md must link resources/schemas/web-quality.schema.json"
    )

    for rel_path in PROVIDER_SKILL_FILES:
        text = _read(rel_path)
        for token in (
            "standards_catalog.json",
            "task_tier_b",
            "triage_surfaces",
            "check_diff_coverage.py",
            "--verbose",
            "--json",
            *ALL_PROFILES,
            *UNIFIED_CAPABILITIES,
        ):
            assert token in text, f"{rel_path} missing required token {token!r}"

    # 6. Reachability of all new scripts & schemas under skills/ (verify.sh §8 parity)
    for rel_path in NEW_SKILL_FILES:
        assert (REPO_ROOT / rel_path).is_file(), (
            f"Expected new file missing: {rel_path}"
        )

    tracked_output = subprocess.check_output(
        ["git", "ls-files"], cwd=str(REPO_ROOT), text=True
    )
    tracked = [Path(line) for line in tracked_output.splitlines() if line.strip()]
    corpus = [
        REPO_ROOT / p
        for p in tracked
        if (REPO_ROOT / p).is_file() and p.suffix in TEXT_SUFFIXES
    ]
    texts = {c: c.read_text(encoding="utf-8", errors="ignore") for c in corpus}

    for rel_path in NEW_SKILL_FILES:
        target = REPO_ROOT / rel_path
        name = target.name
        assert any(other != target and name in body for other, body in texts.items()), (
            f"New skill file {rel_path} is not referenced by any tracked file"
        )

    # Explicit skill-doc links for the 4 new skill files
    assert "_stack_lifecycle_registry.py" in dev_impl
    assert "_provider_manifest_common.py" in quality_check
    assert "check_diff_coverage.py" in quality_check
    assert "web-quality.schema.json" in web_qc

    # Full §8 check over tracked supporting skill files
    supporting = [
        REPO_ROOT / p
        for p in tracked
        if len(p.parts) >= 3
        and p.parts[0] == "skills"
        and (REPO_ROOT / p).is_file()
        and _is_skill_supporting_file(p)
    ]
    unreferenced = [
        f.relative_to(REPO_ROOT).as_posix()
        for f in sorted(supporting)
        if not any(other != f and f.name in body for other, body in texts.items())
    ]
    assert not unreferenced, f"Unreferenced skill files (§8): {unreferenced}"

    # 7. scripts/verify.sh SUITES registration for all 6 new polyglot test suites
    verify_sh = _read("scripts/verify.sh")
    suites_block = verify_sh.split("SUITES = [", 1)[1].split("]\n", 1)[0]
    for suite_rel in PLQ_SUITES:
        assert (REPO_ROOT / suite_rel).is_file(), f"Missing PLQ test suite: {suite_rel}"
        assert f'"{suite_rel}"' in suites_block, (
            f"scripts/verify.sh SUITES missing registration for {suite_rel}"
        )
    assert '"25"' in suites_block, (
        "scripts/verify.sh SUITES must register PLQ suites under Section 25"
    )


def _verify_plq_st_05_end_to_end_polyglot_lifecycle_pipeline(tmp_path: Path) -> None:
    """[PLQ-ST-05] [Tier C - Integration] End-to-end polyglot lifecycle pipeline transitions cleanly from scaffold to contract check to pool triage."""
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    repo = tmp_path / "polyglot_repo"
    repo.mkdir(parents=True, exist_ok=True)
    env = _isolated_env(home, repo)

    # Initialize synthetic Flutter + Rust + Python polyglot repo
    _git(repo, "init", "-q", "-b", "main", env=env)
    _git(repo, "config", "user.name", "PLQ Acceptance", env=env)
    _git(repo, "config", "user.email", "plq-acceptance@example.invalid", env=env)

    _write(
        repo,
        ".gitignore",
        "\n".join(
            [
                "build/",
                ".worktrees/",
                ".devtool/.memory.lock",
                ".devtool/state/",
                ".devtool/logs/",
                "target/",
                ".venv/",
                ".dart_tool/",
                "packages/*/.dart_tool/",
                "secureFiles/",
                "coverage_report/",
                "coverage.xml",
            ]
        )
        + "\n",
    )
    _write(repo, "pubspec.yaml", "name: polyglot_demo\n")
    _write(repo, "Cargo.toml", '[package]\nname = "core"\nversion = "0.1.0"\n')
    _write(repo, "pyproject.toml", '[project]\nname = "polyglot-demo"\n')
    _write(repo, "README.md", "# Synthetic Polyglot Repo\n")

    # Stage 1: Scaffold quality manifests for Flutter + Rust + Python
    scaff = _run_py([str(SCAFFOLD_SCRIPT), "--root", str(repo)], cwd=repo, env=env)
    assert scaff.returncode == 0, f"scaffold failed:\n{scaff.stdout}\n{scaff.stderr}"

    quality_dir = repo / ".agents" / "quality"
    registry_path = quality_dir / "check_quality.json"
    assert registry_path.is_file()
    assert (quality_dir / "standards_catalog.json").is_file()
    for stack in ("flutter", "rust", "python"):
        assert (quality_dir / f"{stack}-quality.json").is_file()

    # Validate registry (default JSON + opt-in --compact 1-line PASS)
    reg_json_proc = _run_py(
        [str(VALIDATE_QC_SCRIPT), "registry", str(registry_path), "--profile", "epic"],
        cwd=repo,
        env=env,
    )
    assert reg_json_proc.returncode == 0, reg_json_proc.stdout + reg_json_proc.stderr
    reg_payload: dict[str, Any] = json.loads(reg_json_proc.stdout)
    assert reg_payload["status"] == "PASS"
    assert len(reg_payload["providers"]) == 3

    reg_compact_proc = _run_py(
        [
            str(VALIDATE_QC_SCRIPT),
            "registry",
            str(registry_path),
            "--profile",
            "epic",
            "--compact",
        ],
        cwd=repo,
        env=env,
    )
    assert reg_compact_proc.returncode == 0
    reg_compact_lines = reg_compact_proc.stdout.strip().splitlines()
    assert len(reg_compact_lines) == 1
    assert reg_compact_lines[0].startswith("PASS:")

    # Validate each scaffolded stack manifest (compact 1-line PASS default)
    for stack in ("flutter", "rust", "python"):
        validator = (
            SKILLS_DIR
            / f"{stack}-quality-check"
            / "resources"
            / "scripts"
            / f"validate_{stack}_quality.py"
        )
        val_proc = _run_py(
            [
                str(validator),
                str(quality_dir / f"{stack}-quality.json"),
                "--profile",
                "epic",
            ],
            cwd=repo,
            env=env,
        )
        assert val_proc.returncode == 0, (
            f"{stack} validator failed: {val_proc.stdout}\n{val_proc.stderr}"
        )
        val_lines = val_proc.stdout.strip().splitlines()
        assert len(val_lines) == 1, (
            f"{stack} expected 1 line PASS, got: {val_proc.stdout!r}"
        )
        assert val_lines[0].startswith("PASS:"), val_lines[0]

    # Stage 2: Author polyglot source/test files + HLD + Task and run check_task_contract.py
    _write(
        repo,
        "packages/core/lib/calc.dart",
        "\n".join(
            [
                "int addDart(int a, int b) {",
                "  final step1 = a + b;",
                "  final step2 = step1 + 0;",
                "  final step3 = step2 * 1;",
                "  final step4 = step3 - 0;",
                "  final step5 = step4 + 0;",
                "  final step6 = step5 * 1;",
                "  final step7 = step6 - 0;",
                "  final step8 = step7 + 0;",
                "  return step8;",
                "}",
            ]
        )
        + "\n",
    )
    _write(
        repo,
        "crates/core/src/calc.rs",
        "pub fn add_rust(a: i32, b: i32) -> i32 {\n    let total = a + b;\n    total\n}\n",
    )
    _write(
        repo,
        "src/calc.py",
        "\n".join(
            [
                "def add_py(a: int, b: int) -> int:",
                "    step1 = a + b",
                "    step2 = step1 + 0",
                "    step3 = step2 * 1",
                "    step4 = step3 - 0",
                "    step5 = step4 + 0",
                "    step6 = step5 * 1",
                "    step7 = step6 - 0",
                "    step8 = step7 + 0",
                "    return step8",
            ]
        )
        + "\n",
    )
    _write(
        repo,
        "tests/integration/test_polyglot.py",
        "from src.calc import add_py\n\n\ndef test_polyglot_add() -> None:\n    assert add_py(2, 3) == 5\n",
    )
    _write(
        repo,
        "tests/unit/test_calc.py",
        "def test_calc_unit() -> None:\n    assert True\n",
    )

    epic_dir = "plq_e2e_demo"
    epic_slug = "plq-e2e-demo"
    hld_rel = f".devtool/epic/{epic_dir}/{epic_dir}.md"
    task_rel = f".devtool/epic/{epic_dir}/task_01_polyglot_change.md"
    feat_rel = ".devtool/features/task_01_polyglot_change.md"

    _write(
        repo,
        hld_rel,
        "# Polyglot E2E Demo\n\n"
        "## Integration Test Plan\n\n"
        "Integration test roots: tests/integration\n\n"
        "Protected paths: .agents/quality/**\n\n"
        "Integration results: python3 -m pytest -q --tb=short --maxfail=3 tests/integration/test_polyglot.py --junitxml=build/test-results/e2e.xml -> build/test-results/e2e.xml\n\n"
        "## Verification Environment\n\n"
        "Runs inside temporary repositories with zero external services.\n",
    )
    task_content = (
        "---\n"
        'id: "task_01_polyglot_change"\n'
        'status: "todo"\n'
        'epic: "plq-e2e-demo"\n'
        'review_tier: "full"\n'
        "---\n\n"
        "# Task 01: Polyglot Change\n\n"
        "## Requirement Analysis\n\n"
        "Update Dart, Rust, and Python calc helpers together.\n\n"
        "## Files\n\n"
        "Allowed files:\n"
        "- `packages/core/lib/calc.dart`\n"
        "- `crates/core/src/calc.rs`\n"
        "- `src/calc.py`\n"
        "- `tests/integration/test_polyglot.py`\n\n"
        "## Verification\n\n"
        "| ID | Phase | Command | Expect | Needs |\n"
        "|----|-------|---------|--------|-------|\n"
        '| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/integration/test_polyglot.py::test_polyglot_add` | exit 1; contains "FAILED" | — |\n'
        '| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/integration/test_polyglot.py` | exit 0; contains "passed" | — |\n'
        '| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 tests/unit/test_calc.py tests/integration/test_polyglot.py` | exit 0; contains "passed" | — |\n'
        "| V4 | TIER-B | `dart format --output=none --set-exit-if-changed packages/core/lib/calc.dart && dart analyze && cargo fmt --check && cargo clippy --all-targets -- -D warnings && uv run ruff check src/calc.py tests/integration/test_polyglot.py && uv run ruff format --check src/calc.py tests/integration/test_polyglot.py && uv run mypy --strict src/calc.py tests/integration/test_polyglot.py` | exit 0 | — |\n"
        "| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/integration/test_polyglot.py --junitxml=build/test-results/task_01.xml` | exit 0; results build/test-results/task_01.xml | — |\n\n"
        "## Stop and Report If\n\n"
        "- A verification row fails unexpectedly.\n\n"
        "## Decisions Already Made\n\n"
        "- Source (`src/calc.py::add_py`, `crates/core/src/calc.rs::add_rust`, `packages/core/lib/calc.dart::addDart`): return `a + b`.\n\n"
        "## Definition of Done\n\n"
        "- [ ] Polyglot task checks pass (V2, V3, V4, V5)\n"
    )
    _write(repo, task_rel, task_content)
    _write(repo, feat_rel, task_content)

    _git(repo, "add", "-A", env=env)
    _git(repo, "commit", "-q", "-m", "Initial polyglot commit", env=env)

    contract_proc = _run_py(
        [
            str(CHECK_TASK_CONTRACT_SCRIPT),
            "--design",
            "--hld",
            hld_rel,
            "--tasks",
            task_rel,
        ],
        cwd=repo,
        env=env,
    )
    assert contract_proc.returncode == 0, (
        f"check_task_contract failed:\n{contract_proc.stdout}\n{contract_proc.stderr}"
    )
    assert contract_proc.stdout.strip().splitlines() == ["Result: 0 problems — PASS"]

    contract_verbose = _run_py(
        [
            str(CHECK_TASK_CONTRACT_SCRIPT),
            "--design",
            "--verbose",
            "--hld",
            hld_rel,
            "--tasks",
            task_rel,
        ],
        cwd=repo,
        env=env,
    )
    assert contract_verbose.returncode == 0
    assert "Implicit protected paths:" in contract_verbose.stdout
    assert "Result: 0 problems — PASS" in contract_verbose.stdout

    # Stage 3: Worker pool init, COW/symlink mount sync, and low-risk Fix Pass 1 triage
    main_wt = repo / ".worktrees" / epic_dir
    main_wt.parent.mkdir(parents=True, exist_ok=True)
    _git(
        repo,
        "worktree",
        "add",
        "-q",
        str(main_wt),
        "-b",
        f"epic/{epic_slug}",
        "main",
        env=env,
    )

    _write(main_wt, "target/debug/marker", "rust-cache\n")
    _write(main_wt, ".venv/bin/python", "#!/bin/sh\n")
    _write(main_wt, ".dart_tool/package_config.json", '{"formatVersion": 2}\n')
    _write(
        main_wt,
        "packages/core/.dart_tool/package_config.json",
        '{"formatVersion": 2}\n',
    )
    _write(main_wt, "secureFiles/dev.json", '{"env": "dev"}\n')

    pool_init = _run_py(
        [
            str(WORKER_POOL_SCRIPT),
            "init",
            "--epic-dir",
            epic_dir,
            "--epic-slug",
            epic_slug,
            "--pool-size",
            "1",
        ],
        cwd=repo,
        env=env,
    )
    assert pool_init.returncode == 0, pool_init.stdout + pool_init.stderr

    pool_sync_work = _run_py(
        [
            str(WORKER_POOL_SCRIPT),
            "sync",
            "--epic-dir",
            epic_dir,
            "--epic-slug",
            epic_slug,
            "--slot",
            "1",
            "--task",
            "task_01_polyglot_change",
            "--status",
            "working",
        ],
        cwd=repo,
        env=env,
    )
    assert pool_sync_work.returncode == 0, pool_sync_work.stdout + pool_sync_work.stderr

    slot1 = repo / ".worktrees" / f"{epic_dir}-slot-1"
    assert (slot1 / "target").is_symlink()
    assert (slot1 / ".venv").is_symlink()
    for cow_rel in (".dart_tool", "packages/core/.dart_tool", "secureFiles"):
        cow_path = slot1 / cow_rel
        assert cow_path.is_dir() and not cow_path.is_symlink(), (
            f"{cow_rel} must be COW copy"
        )

    # Pass 1 work -> transition to review (captures pass1_tree_sha) -> Fix Pass 1 low-risk edit
    _write(
        slot1,
        "crates/core/src/calc.rs",
        "pub fn add_rust(a: i32, b: i32) -> i32 {\n    let sum = a + b;\n    sum\n}\n",
    )
    review_json = tmp_path / "pass1_review.json"
    review_json.write_text(
        json.dumps(
            {
                "verdict": "CHANGES_REQUESTED",
                "blockers": [
                    {
                        "id": "B1",
                        "severity": "BLOCKER",
                        "file": "crates/core/src/calc.rs",
                        "summary": "Clarify local variable name",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    pool_review = _run_py(
        [
            str(WORKER_POOL_SCRIPT),
            "sync",
            "--epic-dir",
            epic_dir,
            "--epic-slug",
            epic_slug,
            "--slot",
            "1",
            "--task",
            "task_01_polyglot_change",
            "--status",
            "review",
        ],
        cwd=repo,
        env=env,
    )
    assert pool_review.returncode == 0, pool_review.stdout + pool_review.stderr

    pool_fix = _run_py(
        [
            str(WORKER_POOL_SCRIPT),
            "sync",
            "--epic-dir",
            epic_dir,
            "--epic-slug",
            epic_slug,
            "--slot",
            "1",
            "--task",
            "task_01_polyglot_change",
            "--status",
            "working",
            "--no-reset",
            "--review-file",
            str(review_json),
        ],
        cwd=repo,
        env=env,
    )
    assert pool_fix.returncode == 0, pool_fix.stdout + pool_fix.stderr

    _write(
        slot1,
        "crates/core/src/calc.rs",
        "pub fn add_rust(a: i32, b: i32) -> i32 {\n    let computed_sum = a + b;\n    computed_sum\n}\n",
    )
    triage_proc = _run_py(
        [
            str(WORKER_POOL_SCRIPT),
            "triage-fix",
            "--epic-dir",
            epic_dir,
            "--epic-slug",
            epic_slug,
            "--slot",
            "1",
            "--task",
            "task_01_polyglot_change",
        ],
        cwd=repo,
        env=env,
    )
    assert triage_proc.returncode == 0, triage_proc.stdout + triage_proc.stderr
    triage_payload: dict[str, Any] = json.loads(triage_proc.stdout)
    assert triage_payload["tier1_status"] == "ELIGIBLE_FOR_SHORT_CIRCUIT", (
        triage_payload
    )
    assert triage_payload["triggers"] == [], triage_payload
    assert triage_payload["non_test_changed_lines"] <= 30

    # Stage 4: Portable multi-format diff-coverage (LCOV + Cobertura XML)
    lcov_path = _write(
        repo,
        "coverage_report/lcov.info",
        "\n".join(
            [
                "TN:",
                "SF:packages/core/lib/calc.dart",
                *[f"DA:{i},{1 if i <= 9 else 0}" for i in range(1, 11)],
                "LF:10",
                "LH:9",
                "end_of_record",
            ]
        )
        + "\n",
    )
    cobertura_path = _write(
        repo,
        "coverage.xml",
        '<?xml version="1.0" ?>\n'
        '<coverage version="7.6">\n'
        "  <packages>\n"
        '    <package name="src">\n'
        "      <classes>\n"
        '        <class name="calc.py" filename="src/calc.py">\n'
        "          <lines>\n"
        + "\n".join(
            f'            <line number="{i}" hits="{1 if i <= 9 else 0}"/>'
            for i in range(1, 11)
        )
        + "\n          </lines>\n"
        "        </class>\n"
        "      </classes>\n"
        "    </package>\n"
        "  </packages>\n"
        "</coverage>\n",
    )

    diff_cov = _run_py(
        [
            str(DIFF_COVERAGE_SCRIPT),
            str(lcov_path),
            str(cobertura_path),
            "--repo-root",
            str(repo),
            "--format",
            "auto",
            "--min-coverage",
            "75",
            "--min-package-coverage",
            "60",
            "--diff-files",
            "packages/core/lib/calc.dart",
            "--diff-files",
            "src/calc.py",
            "--min-diff-coverage",
            "80",
        ],
        cwd=repo,
        env=env,
    )
    assert diff_cov.returncode == 0, (
        f"check_diff_coverage failed:\n{diff_cov.stdout}\n{diff_cov.stderr}"
    )
    cov_lines = diff_cov.stdout.strip().splitlines()
    assert len(cov_lines) == 1, (
        f"Expected compact 1-line PASS, got: {diff_cov.stdout!r}"
    )
    assert cov_lines[0].startswith("PASS:"), cov_lines[0]
    assert "coverage=90.0%" in cov_lines[0]
    assert "diff=90.0%" in cov_lines[0]


def _verify_plq_ar_05_docs_frontmatter_namespace_and_markdown_lint() -> None:
    """[PLQ-AR-05] [Tier C - Integration] Documentation cross-references obey d3nexus namespace and exclude forbidden prefixes."""
    # 1. check_document.py mechanical markdown/link/mermaid lint across all 13 modified docs
    doc_check = _run_py(
        [
            str(CHECK_DOC_SCRIPT),
            *[str(REPO_ROOT / rel) for rel in MODIFIED_MARKDOWN_FILES],
        ],
        cwd=REPO_ROOT,
    )
    assert doc_check.returncode == 0, (
        f"check_document.py failed:\n{doc_check.stdout}\n{doc_check.stderr}"
    )

    # 2. Every SKILL.md under skills/ has exclusively name + description frontmatter
    skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    assert skill_files, "Expected skills/*/SKILL.md files"
    for skill_path in skill_files:
        text = skill_path.read_text(encoding="utf-8")
        fm = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        assert fm is not None, f"{skill_path}: missing YAML frontmatter"
        keys = re.findall(r"^([A-Za-z_][\w-]*):", fm.group(1), flags=re.MULTILINE)
        assert keys == ["name", "description"], (
            f"{skill_path}: frontmatter keys {keys!r} must be exclusively ['name', 'description']"
        )

    # 3. Zero files under skills/ contain forbidden 'superpowers:' prefix
    superpowers_hits: list[str] = []
    for path in sorted(SKILLS_DIR.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix not in TEXT_SUFFIXES:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        if "superpowers:" in content:
            superpowers_hits.append(path.relative_to(REPO_ROOT).as_posix())
    assert not superpowers_hits, (
        f"Forbidden 'superpowers:' prefix found under skills/: {superpowers_hits}"
    )

    # 4. Relative links, ToC anchors, and confidentiality across all 13 modified docs
    for rel_path in MODIFIED_MARKDOWN_FILES:
        doc_path = REPO_ROOT / rel_path
        text = doc_path.read_text(encoding="utf-8")
        for pat in PERSONAL_LEAK_PATTERNS:
            assert pat.search(text) is None, (
                f"{rel_path} leaked personal pattern {pat.pattern!r}"
            )

        in_fence = False
        anchors: set[str] = set()
        for line in text.splitlines():
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if not in_fence and re.match(r"^#{2,6} ", line):
                anchors.add(_heading_anchor(re.sub(r"^#+ ", "", line).rstrip()))
        for anchor_link in re.findall(
            r"\]\((#[^)]+)\)", _strip_fences_and_inline_code(text)
        ):
            assert anchor_link.lower() in anchors, (
                f"{rel_path}: broken internal anchor {anchor_link!r}"
            )

        for link in re.findall(
            r"\]\(([^)#][^)]*)\)", _strip_fences_and_inline_code(text)
        ):
            if link.startswith(("http://", "https://", "mailto:")) or "<" in link:
                continue
            target = doc_path.parent / link.split("#", 1)[0]
            assert target.exists(), f"{rel_path}: broken relative link {link!r}"

    # 5. verification-rows.md preserves pytest default flags alongside 6-stack Tier C1/Tier C2 examples
    verification_rows = _read("skills/dev-designer/references/verification-rows.md")
    assert "-q --tb=short --maxfail=3" in verification_rows
    for section in (
        "## Python",
        "## Android",
        "## Web",
        "## iOS",
        "## Rust",
        "## Flutter",
    ):
        assert section in verification_rows, (
            f"verification-rows.md missing platform section {section!r}"
        )
    assert "Tier C1" in verification_rows and "Tier C2" in verification_rows
    assert "# tier: C2" in verification_rows


class TestPLQEndToEndAcceptance_Integration:
    """Tier C integration provenance suite for all 3 assigned Task 06 BDD scenarios."""

    def test_plq_hp_06_integration(self) -> None:
        """[PLQ-HP-06] [Tier C - Integration] Lifecycle docs, provider skills, and verify.sh registry pass full structural and word-cap checks."""
        test_plq_hp_06_docs_caps_reachability_and_verify_registration()

    def test_plq_st_05_end_to_end_polyglot_lifecycle_pipeline(
        self, tmp_path: Path
    ) -> None:
        """[PLQ-ST-05] [Tier C - Integration] End-to-end polyglot lifecycle pipeline transitions cleanly from scaffold to contract check to pool triage."""
        _verify_plq_st_05_end_to_end_polyglot_lifecycle_pipeline(tmp_path)

    def test_plq_ar_05_docs_frontmatter_namespace_and_markdown_lint(self) -> None:
        """[PLQ-AR-05] [Tier C - Integration] Documentation cross-references obey d3nexus namespace and exclude forbidden prefixes."""
        _verify_plq_ar_05_docs_frontmatter_namespace_and_markdown_lint()
