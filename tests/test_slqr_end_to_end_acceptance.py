"""End-to-end acceptance tests for Shift-Left Quality Layer Resolver (Task 05).

Covers: SLQR-HP-05, SLQR-AR-04
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

ALL_PROFILES: tuple[str, ...] = ("pr", "epic", "scheduled", "release")
ALL_STACKS: tuple[str, ...] = ("rust", "web", "python", "flutter", "android", "ios")

UPDATED_SKILL_FILES: tuple[str, ...] = (
    "skills/dev-designer/SKILL.md",
    "skills/dev-designer/references/verification-rows.md",
    "skills/writing-plans/SKILL.md",
    "skills/writing-plans/plan-document-reviewer-prompt.md",
    "skills/finishing-a-development-branch/SKILL.md",
    "skills/quality_check/SKILL.md",
    "skills/setup_quality_check/SKILL.md",
)

SLQR_TEST_SUITES: tuple[str, ...] = (
    "tests/test_slqr_registry_and_schemas.py",
    "tests/test_slqr_receipt_coverage_and_scaffolder.py",
    "tests/test_slqr_quality_plan_resolver.py",
    "tests/test_slqr_task_and_plan_contracts.py",
    "tests/test_slqr_end_to_end_acceptance.py",
)

RETIRED_DESIGNER_SCRIPTS: tuple[str, ...] = (
    "verify_importlinter_coverage.py",
    "pre_review_self_probe.py",
    "verify_bdd_coverage.py",
)

# Constructed without embedding literal machine-specific paths in tracked source.
_PERSONAL_LEAK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile("/" + "Us" + r"ers/[A-Za-z0-9._-]+"),
    re.compile("antigravity" + "_" + r"homes/[A-Za-z0-9._-]+"),
    re.compile(r"[A-Za-z]:\\" + "Us" + r"ers\\"),
)


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _parse_frontmatter_keys(text: str) -> list[str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match is not None, "Expected YAML frontmatter delimited by --- lines"
    return re.findall(r"^([A-Za-z_][\w-]*):", match.group(1), flags=re.MULTILINE)


def _run_git(repo_dir: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_git_repo(repo_dir: Path) -> None:
    repo_dir.mkdir(parents=True, exist_ok=True)
    _run_git(repo_dir, "init", "-b", "develop")
    _run_git(repo_dir, "config", "user.email", "slqr-test@example.com")
    _run_git(repo_dir, "config", "user.name", "SLQR Test")


def _scaffold_repo(repo_dir: Path, platforms: list[str]) -> Path:
    repo_dir.mkdir(parents=True, exist_ok=True)
    scaffolder = (
        REPO_ROOT
        / "skills"
        / "setup_quality_check"
        / "resources"
        / "scripts"
        / "scaffold_quality_manifest.py"
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(scaffolder),
            "--root",
            str(repo_dir),
            "--platform",
            ",".join(platforms),
            "--force",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"scaffolder failed: {proc.stdout}\n{proc.stderr}"
    return repo_dir / ".agents" / "quality"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _build_five_repo_synthetic_ecosystem(eco_root: Path) -> list[Path]:
    """Create 5 polyglot synthetic repositories exercising all 6 stacks and additive fields."""
    repos: list[Path] = []

    # 1. rust+web+python monorepo
    r1 = eco_root / "repo_rust_web_python"
    q1 = _scaffold_repo(r1, ["rust", "web", "python"])
    _write_json(
        q1 / "coverage_floors.json",
        {"python": {"adapters": {"apps/worker/src": 0.85}}, "web_modules": {}},
    )
    for stack_name in ("rust", "web", "python"):
        mf = q1 / f"{stack_name}-quality.json"
        data = json.loads(mf.read_text(encoding="utf-8"))
        data["capabilities"]["cache_enable"] = ["true"]
        data["capabilities"]["cache_purge"] = ["true"]
        if isinstance(data["capabilities"].get("coverage"), dict):
            data["capabilities"]["coverage"]["package_floors"] = (
                ".agents/quality/coverage_floors.json"
            )
        data["test_routing"] = {
            "canonical_test_globs": ["tests/**/*.py"]
            if stack_name == "python"
            else (
                ["apps/web/tests/**/*.test.ts"]
                if stack_name == "web"
                else ["crates/*/tests/**/*.rs"]
            )
        }
        if stack_name == "python":
            data["capabilities"]["lint"] = [
                "uv",
                "--directory",
                "apps/worker",
                "run",
                "ruff",
                "check",
                ".",
            ]
            data["capabilities"]["type_check"] = [
                "uv",
                "--directory",
                "apps/worker",
                "run",
                "mypy",
                "--strict",
                "src",
                "tests",
            ]
        _write_json(mf, data)
    repos.append(r1)

    # 2. python+vanilla-js LCOV repo (also used for clean-shell Pre-Flight execution)
    r2 = eco_root / "repo_python_vanilla_js"
    _init_git_repo(r2)
    q2 = _scaffold_repo(r2, ["python", "web"])
    _write_json(
        q2 / "coverage_floors.json",
        {
            "python": {"adapters": {"src/pkg/align": 0.88}},
            "web_modules": {"src/preview/static/align-studio.js": 0.50},
        },
    )
    py_data = json.loads((q2 / "python-quality.json").read_text(encoding="utf-8"))
    py_data["capabilities"]["lint"] = [
        "uv",
        "run",
        "ruff",
        "check",
        "--extend-select",
        "F821,B904",
        ".",
    ]
    py_data["capabilities"]["type_check"] = [
        "uv",
        "run",
        "mypy",
        "--strict",
        "src",
        "tests",
    ]
    if isinstance(py_data["capabilities"].get("coverage"), dict):
        py_data["capabilities"]["coverage"]["package_floors"] = (
            ".agents/quality/coverage_floors.json"
        )
    py_data["test_routing"] = {
        "canonical_test_globs": ["tests/unit/**/*.py", "tests/integration/**/*.py"],
        "forbidden_test_globs": ["tests/test_*.py", "scripts/test_*.py"],
        "paired_source_globs": ["src/pkg/**/*.py"],
    }
    _write_json(q2 / "python-quality.json", py_data)

    web_data = json.loads((q2 / "web-quality.json").read_text(encoding="utf-8"))
    web_data["capabilities"]["type_check"] = [
        "python3",
        "{skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py",
        "--target-dir",
        "src/preview",
    ]
    web_data["capabilities"]["lint"] = [
        "python3",
        "{skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py",
        "--target-dir",
        "src/preview",
    ]
    web_data["capabilities"]["test_unit"] = [
        "node",
        "--test",
        "--experimental-test-coverage",
        "tests/js/*.test.mjs",
    ]
    web_data["capabilities"]["diff_coverage"] = [
        "python3",
        "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
        "--format",
        "lcov",
        "--diff-base",
        "{base_ref}",
        "--min-diff-coverage",
        "80",
        "--source-ext",
        ".js",
        "--source-ext",
        ".mjs",
        "--package-floors",
        ".agents/quality/coverage_floors.json",
        "coverage/js-lcov.info",
    ]
    if isinstance(web_data["capabilities"].get("coverage"), dict):
        web_data["capabilities"]["coverage"]["package_floors"] = (
            ".agents/quality/coverage_floors.json"
        )
    web_data["test_routing"] = {
        "canonical_test_globs": ["tests/js/**/*.test.mjs", "tests/e2e/**/*.spec.ts"],
        "lcov_unit_test_globs": ["tests/js/**/*.test.mjs"],
        "cache_bust_extensions": [".js", ".css"],
    }
    _write_json(q2 / "web-quality.json", web_data)

    (r2 / "src" / "pkg" / "align").mkdir(parents=True, exist_ok=True)
    (r2 / "src" / "pkg" / "align" / "ctc.py").write_text(
        "def score_frame(value: float) -> float:\n    return value\n",
        encoding="utf-8",
    )
    (r2 / "tests" / "unit" / "align").mkdir(parents=True, exist_ok=True)
    (r2 / "tests" / "unit" / "align" / "test_ctc.py").write_text(
        "def test_score_frame() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    (r2 / "src" / "preview" / "static").mkdir(parents=True, exist_ok=True)
    (r2 / "src" / "preview" / "static" / "align-studio.js").write_text(
        "export function renderWave() { return 1; }\n",
        encoding="utf-8",
    )
    (r2 / "src" / "preview" / "static" / "index.html").write_text(
        '<!doctype html><script src="align-studio.js?v=20261128"></script>\n',
        encoding="utf-8",
    )
    (r2 / "tests" / "js").mkdir(parents=True, exist_ok=True)
    (r2 / "tests" / "js" / "align-studio.test.mjs").write_text(
        "import test from 'node:test';\ntest('smoke', () => {});\n",
        encoding="utf-8",
    )
    _run_git(r2, "add", ".")
    _run_git(r2, "commit", "-m", "[TEST] Seed synthetic python+vanilla-js repo")
    repos.append(r2)

    # 3. flutter+python workspace
    r3 = eco_root / "repo_flutter_python"
    q3 = _scaffold_repo(r3, ["flutter", "python"])
    fl_data = json.loads((q3 / "flutter-quality.json").read_text(encoding="utf-8"))
    fl_data["capabilities"]["architecture"] = ["./scripts/check_architecture.sh"]
    if isinstance(fl_data["capabilities"].get("coverage"), dict):
        fl_data["capabilities"]["coverage"]["package_floors"] = (
            ".agents/quality/coverage_floors.json"
        )
    fl_data["test_routing"] = {
        "canonical_test_globs": ["test/**/*.dart", "integration_test/**/*_test.dart"]
    }
    _write_json(q3 / "flutter-quality.json", fl_data)
    repos.append(r3)

    # 4. android Gradle repo
    r4 = eco_root / "repo_android_gradle"
    q4 = _scaffold_repo(r4, ["android"])
    an_data = json.loads((q4 / "android-quality.json").read_text(encoding="utf-8"))
    if isinstance(an_data["capabilities"].get("coverage"), dict):
        an_data["capabilities"]["coverage"]["package_floors"] = (
            ".agents/quality/coverage_floors.json"
        )
    an_data["test_routing"] = {
        "canonical_test_globs": [
            "app/src/test/**/*Test.kt",
            "feature/*/src/test/**/*Test.kt",
        ]
    }
    _write_json(q4 / "android-quality.json", an_data)
    repos.append(r4)

    # 5. ios Tuist/mise repo
    r5 = eco_root / "repo_ios_tuist_mise"
    q5 = _scaffold_repo(r5, ["ios"])
    ios_data = json.loads((q5 / "ios-quality.json").read_text(encoding="utf-8"))
    ios_data["capabilities"]["lint"] = [
        "mise",
        "exec",
        "--",
        "swiftlint",
        "lint",
        "--config",
        "quality/.swiftlint.yml",
        "--strict",
    ]
    if isinstance(ios_data["capabilities"].get("coverage"), dict):
        ios_data["capabilities"]["coverage"]["package_floors"] = (
            ".agents/quality/coverage_floors.json"
        )
    ios_data["test_routing"] = {
        "canonical_test_globs": [
            "Packages/*/Tests/**/*Tests.swift",
            "App/Tests/**/*Tests.swift",
        ]
    }
    _write_json(q5 / "ios-quality.json", ios_data)
    repos.append(r5)

    return repos


def _validate_ecosystem_root(root_dir: Path) -> int:
    """Validate every discovered check_quality.json & stack manifest under root_dir."""
    registry_validator = (
        REPO_ROOT
        / "skills"
        / "quality_check"
        / "resources"
        / "scripts"
        / "validate_quality_contract.py"
    )
    schemas: dict[str, dict[str, Any]] = {
        stack: json.loads(
            (
                REPO_ROOT
                / "skills"
                / f"{stack}-quality-check"
                / "resources"
                / "schemas"
                / f"{stack}-quality.schema.json"
            ).read_text(encoding="utf-8")
        )
        for stack in ALL_STACKS
    }
    for stack, schema in schemas.items():
        top_props = schema.get("properties", {})
        assert "test_routing" in top_props, (
            f"{stack} schema missing top-level test_routing"
        )
        cov_props = (
            top_props.get("capabilities", {})
            .get("properties", {})
            .get("coverage", {})
            .get("properties", {})
        )
        assert "package_floors" in cov_props, (
            f"{stack} schema missing capabilities.coverage.package_floors"
        )

    discovered_registries: list[Path] = []
    for candidate in sorted(root_dir.glob("*/.agents/quality/check_quality.json")):
        if ".worktrees" not in candidate.parts:
            discovered_registries.append(candidate)
    direct = root_dir / ".agents" / "quality" / "check_quality.json"
    if direct.is_file() and direct not in discovered_registries:
        discovered_registries.append(direct)

    profiles_validated = 0
    for registry_path in discovered_registries:
        repo_dir = registry_path.parent.parent.parent
        reg_data = json.loads(registry_path.read_text(encoding="utf-8"))
        reg_profiles: set[str] = set()
        for provider in reg_data.get("providers", []):
            reg_profiles.update(provider.get("profiles", []))
        assert reg_profiles, f"No profiles declared in {registry_path}"

        for profile in sorted(reg_profiles):
            proc = subprocess.run(
                [
                    sys.executable,
                    str(registry_validator),
                    "registry",
                    str(registry_path),
                    "--profile",
                    profile,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            assert proc.returncode == 0, (
                f"Registry validation failed for {registry_path} [{profile}]: "
                f"{proc.stdout}\n{proc.stderr}"
            )
            payload = json.loads(proc.stdout)
            assert payload.get("status") == "PASS", (
                f"Expected PASS for {registry_path} [{profile}], got {payload}"
            )
            profiles_validated += 1

        qdir = registry_path.parent
        for stack in ALL_STACKS:
            manifest_path = qdir / f"{stack}-quality.json"
            if not manifest_path.is_file():
                continue
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            schema_caps = set(
                schemas[stack]
                .get("properties", {})
                .get("capabilities", {})
                .get("properties", {})
            )
            manifest_caps = set(manifest_data.get("capabilities", {}).keys())
            missing_caps = sorted(manifest_caps - schema_caps)
            assert not missing_caps, (
                f"{manifest_path} capabilities missing from {stack}-quality.schema.json: "
                f"{missing_caps}"
            )

            validator = (
                REPO_ROOT
                / "skills"
                / f"{stack}-quality-check"
                / "resources"
                / "scripts"
                / f"validate_{stack}_quality.py"
            )
            manifest_profiles = sorted(manifest_data.get("profiles", {}).keys())
            assert manifest_profiles, f"No profiles in {manifest_path}"
            for profile in manifest_profiles:
                cmd = [
                    sys.executable,
                    str(validator),
                    str(manifest_path),
                    "--profile",
                    profile,
                    "--json",
                ]
                if stack == "web":
                    cmd.extend(["--repo-root", str(repo_dir)])
                proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
                assert proc.returncode == 0, (
                    f"{stack} validator failed for {manifest_path} [{profile}]: "
                    f"{proc.stdout}\n{proc.stderr}"
                )
                payload = json.loads(proc.stdout)
                assert payload.get("status") == "PASS", (
                    f"Expected PASS for {manifest_path} [{profile}], got {payload}"
                )
                profiles_validated += 1

    return profiles_validated


def _write_valid_standalone_plan(repo_dir: Path) -> Path:
    plan_path = repo_dir / "docs" / "superpowers" / "plans" / "2026-11-28-demo.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        """# Demo Feature Implementation Plan

## Table of Contents

- [Task 1: Align Studio Update](#task-1-align-studio-update)

### Task 1: Align Studio Update

**Files:**
- Modify: `src/pkg/align/ctc.py`
- Modify: `src/preview/static/align-studio.js`
- Modify: `src/preview/static/index.html`
- Test: `tests/unit/align/test_ctc.py`
- Test: `tests/js/align-studio.test.mjs`

- [ ] **Step 1: Run scoped static checks and unit tests**

```bash
uv run ruff check --extend-select F821,B904 src/pkg/align/ctc.py tests/unit/align/test_ctc.py
uv run mypy --strict src/pkg/align/ctc.py tests/unit/align/test_ctc.py
python3 "$D3NEXUS_KIT/skills/web-quality-check/resources/scripts/check_vanilla_js.py" --target-dir src/preview
node --test --experimental-test-coverage tests/js/align-studio.test.mjs
```
""",
        encoding="utf-8",
    )
    return plan_path


def test_slqr_hp_05_skills_pass_caps_preflight_and_ecosystem_parity(
    tmp_path: Path,
) -> None:
    """[SLQR-HP-05] Updated skills pass byte caps, clean-shell Pre-Flight, doc checks, and 5-repo parity."""
    # 1. Byte cap & retired script cleanup in dev-designer
    dev_designer_path = REPO_ROOT / "skills/dev-designer/SKILL.md"
    dev_designer_bytes = dev_designer_path.read_bytes()
    assert len(dev_designer_bytes) <= 22528, (
        f"skills/dev-designer/SKILL.md exceeds 22528 bytes: {len(dev_designer_bytes)}"
    )
    dev_designer = dev_designer_bytes.decode("utf-8")
    verification_rows = _read("skills/dev-designer/references/verification-rows.md")
    assert "-q --tb=short --maxfail=3" in verification_rows

    for retired in RETIRED_DESIGNER_SCRIPTS:
        assert retired not in dev_designer, (
            f"Retired script {retired!r} still appears in skills/dev-designer/SKILL.md"
        )
        assert retired not in verification_rows, (
            f"Retired script {retired!r} still appears in verification-rows.md"
        )

    # 2. Frontmatter purity & zero personal-path leaks across updated docs & this suite
    for rel_path in UPDATED_SKILL_FILES:
        text = _read(rel_path)
        if rel_path.endswith("/SKILL.md"):
            assert _parse_frontmatter_keys(text) == ["name", "description"], (
                f"Unexpected frontmatter keys in {rel_path}"
            )
        for pat in _PERSONAL_LEAK_PATTERNS:
            assert pat.search(text) is None, (
                f"Personal path leak {pat.pattern!r} in {rel_path}"
            )

    this_file_text = Path(__file__).read_text(encoding="utf-8")
    for pat in _PERSONAL_LEAK_PATTERNS:
        assert pat.search(this_file_text) is None, (
            f"Personal path leak {pat.pattern!r} in test_slqr_end_to_end_acceptance.py"
        )

    # 3. Documented contracts in finishing-a-development-branch, quality_check, setup_quality_check
    finishing = _read("skills/finishing-a-development-branch/SKILL.md")
    assert (
        "uncommitted" in finishing.lower() or "clean working tree" in finishing.lower()
    )
    assert "gate4_receipt.json" in finishing

    quality_check = _read("skills/quality_check/SKILL.md")
    assert "gate4_receipt.json" in quality_check
    assert "--package-floors" in quality_check or "package_floors" in quality_check
    assert "test_routing" in quality_check

    setup_qc = _read("skills/setup_quality_check/SKILL.md")
    assert "test_routing" in setup_qc
    assert "package_floors" in setup_qc or "--package-floors" in setup_qc
    assert "workspace_audit" in setup_qc and "pr_diff_audit" in setup_qc

    # 4. scripts/verify.sh registers all 5 SLQR suites
    verify_sh = _read("scripts/verify.sh")
    for suite in SLQR_TEST_SUITES:
        assert suite in verify_sh, f"scripts/verify.sh missing SLQR suite {suite!r}"

    # 5. check_document.py validation (including --require-toc on verification-rows.md)
    check_doc_script = (
        REPO_ROOT
        / "skills"
        / "doc_quality_check"
        / "resources"
        / "scripts"
        / "check_document.py"
    )
    doc_proc = subprocess.run(
        [sys.executable, str(check_doc_script), *UPDATED_SKILL_FILES],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert doc_proc.returncode == 0, (
        f"check_document.py failed:\n{doc_proc.stdout}{doc_proc.stderr}"
    )

    toc_proc = subprocess.run(
        [
            sys.executable,
            str(check_doc_script),
            "--require-toc",
            "skills/dev-designer/references/verification-rows.md",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert toc_proc.returncode == 0, (
        f"check_document.py --require-toc failed:\n{toc_proc.stdout}{toc_proc.stderr}"
    )

    # 6. Synthetic 5-repo polyglot ecosystem profile + schema-vs-validator parity
    eco_root = tmp_path / "synthetic_ecosystem"
    repos = _build_five_repo_synthetic_ecosystem(eco_root)
    assert len(repos) == 5
    synthetic_validated = _validate_ecosystem_root(eco_root)
    assert synthetic_validated >= 40, (
        f"Expected >= 40 validated profiles across 5 repos / 6 stacks, got {synthetic_validated}"
    )

    # 7. Clean-shell Pre-Flight execution of embedded CLI commands
    preflight_repo = eco_root / "repo_python_vanilla_js"
    plan_path = _write_valid_standalone_plan(preflight_repo)
    clean_env = {
        "PATH": os.environ["PATH"],
        "HOME": str(tmp_path / "clean_home"),
        "D3NEXUS_KIT": str(REPO_ROOT),
    }
    Path(clean_env["HOME"]).mkdir(parents=True, exist_ok=True)

    resolve_proc = subprocess.run(
        [
            str(REPO_ROOT / "bin" / "d3nexus"),
            "resolve-quality",
            "--files",
            "src/pkg/align/ctc.py",
            "src/preview/static/align-studio.js",
            "--base-ref",
            "develop",
        ],
        cwd=preflight_repo,
        env=clean_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resolve_proc.returncode == 0, (
        f"Clean-shell resolve-quality failed:\n{resolve_proc.stdout}\n{resolve_proc.stderr}"
    )
    resolve_lines = [ln for ln in resolve_proc.stdout.splitlines() if ln.strip()]
    assert 5 <= len(resolve_lines) <= 10, (
        f"Expected 5-10 compact lines from resolve-quality, got {len(resolve_lines)}:\n"
        f"{resolve_proc.stdout}"
    )
    assert "index.html" in resolve_proc.stdout
    assert "$D3NEXUS_KIT/skills" in resolve_proc.stdout

    check_plan_cmd = (
        'python3 "$D3NEXUS_KIT/skills/dev-implementation/resources/scripts/check_task_contract.py"'
        f" --check-plan {plan_path.relative_to(preflight_repo)}"
    )
    plan_proc = subprocess.run(
        ["bash", "-c", check_plan_cmd],
        cwd=preflight_repo,
        env=clean_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert plan_proc.returncode == 0, (
        f"Clean-shell --check-plan failed:\n{plan_proc.stdout}\n{plan_proc.stderr}"
    )
    assert "Result: 0 problems — PASS" in plan_proc.stdout

    # 8. Optional real ecosystem validation when SLQR_ECOSYSTEM_ROOT is set
    optional_root = os.environ.get("SLQR_ECOSYSTEM_ROOT", "").strip()
    if optional_root:
        eco_path = Path(optional_root)
        assert eco_path.is_dir(), (
            f"SLQR_ECOSYSTEM_ROOT is not a directory: {optional_root}"
        )
        live_validated = _validate_ecosystem_root(eco_path)
        assert live_validated > 0, (
            f"SLQR_ECOSYSTEM_ROOT={optional_root!r} discovered 0 quality profiles"
        )


def test_slqr_hp_05_optional_ecosystem_root_env_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """[SLQR-HP-05] SLQR_ECOSYSTEM_ROOT discovery validates all profiles under an external root."""
    eco_root = tmp_path / "env_ecosystem"
    _build_five_repo_synthetic_ecosystem(eco_root)
    monkeypatch.setenv("SLQR_ECOSYSTEM_ROOT", str(eco_root))
    env_root = Path(os.environ["SLQR_ECOSYSTEM_ROOT"])
    validated = _validate_ecosystem_root(env_root)
    assert validated >= 40


def test_slqr_ar_04_authoring_skills_integrate_cli_resolver_without_prose_matrices() -> (
    None
):
    """[SLQR-AR-04] Authoring skills integrate resolve-quality and --check-plan concisely without coverage tables."""
    dev_designer = _read("skills/dev-designer/SKILL.md")
    writing_plans = _read("skills/writing-plans/SKILL.md")
    reviewer_prompt = _read("skills/writing-plans/plan-document-reviewer-prompt.md")
    verification_rows = _read("skills/dev-designer/references/verification-rows.md")

    for label, text in (
        ("skills/dev-designer/SKILL.md", dev_designer),
        ("skills/writing-plans/SKILL.md", writing_plans),
        ("skills/dev-designer/references/verification-rows.md", verification_rows),
    ):
        assert "resolve-quality" in text or "resolve_task_quality_plan.py" in text, (
            f"{label} must reference resolve-quality or resolve_task_quality_plan.py"
        )

    for label, text in (
        ("skills/writing-plans/SKILL.md", writing_plans),
        ("skills/writing-plans/plan-document-reviewer-prompt.md", reviewer_prompt),
    ):
        assert "--check-plan" in text, f"{label} must reference --check-plan"

    # Neither authoring SKILL.md may embed a multi-stack coverage floor matrix table.
    coverage_table_header = re.compile(
        r"^\|\s*(?:Stack|Platform)\s*\|.*(?:Floor|Coverage|LCOV|Cobertura)",
        flags=re.IGNORECASE | re.MULTILINE,
    )
    for label, text in (
        ("skills/dev-designer/SKILL.md", dev_designer),
        ("skills/writing-plans/SKILL.md", writing_plans),
    ):
        assert coverage_table_header.search(text) is None, (
            f"{label} must not embed a multi-stack coverage floor table"
        )

    # Confirm compact integration footprint.
    assert len(dev_designer.encode("utf-8")) <= 22528
    assert len(writing_plans.splitlines()) <= 280


class TestSLQREndToEndAcceptance_Integration:
    """Integration provenance wrapper for Tier C scenarios SLQR-HP-05 and SLQR-AR-04."""

    def test_slqr_hp_05_integration(self, tmp_path: Path) -> None:
        """[SLQR-HP-05] Tier C integration verification of skill caps, Pre-Flight, and 5-repo parity."""
        test_slqr_hp_05_skills_pass_caps_preflight_and_ecosystem_parity(tmp_path)

    def test_slqr_ar_04_integration(self) -> None:
        """[SLQR-AR-04] Tier C integration verification of lean resolver hooks in authoring skills."""
        test_slqr_ar_04_authoring_skills_integrate_cli_resolver_without_prose_matrices()
