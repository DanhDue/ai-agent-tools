"""Unit and integration tests for Task 03: On-Demand File-Scoped Quality Plan Resolver.

Covers BDD Scenarios:
- SLQR-HP-03: d3nexus resolve-quality emits compact file-scoped guidance within latency budgets
- SLQR-AR-01: Stack lifecycle registry and quality plan resolver maintain zero circular
  imports and Python 3 stdlib purity
- SLQR-AR-02: Single-stack Python invocation of resolve-quality emits zero lines mentioning
  Web, Flutter, Android, iOS, or Rust
- SLQR-FR-03: resolve_task_quality_plan exits 2 with clear diagnostic on malformed quality
  manifest JSON
"""

from __future__ import annotations

import ast
import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
IMPL_SCRIPTS_DIR = SKILLS_DIR / "dev-implementation" / "resources" / "scripts"
D3NEXUS_BIN = REPO_ROOT / "bin" / "d3nexus"

if str(IMPL_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(IMPL_SCRIPTS_DIR))


def _load_resolver_module() -> Any:
    return importlib.import_module("resolve_task_quality_plan")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run_d3nexus(
    args: list[str],
    *,
    cwd: Path,
) -> tuple[subprocess.CompletedProcess[str], float]:
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(D3NEXUS_BIN), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - start
    return proc, elapsed


@pytest.fixture(scope="module")
def hp03_polyglot_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Read-only polyglot repo matching SLQR-HP-03 (Python + Web LCOV + floors + ?v= template)."""
    root = tmp_path_factory.mktemp("slqr_hp03_repo")
    quality_dir = root / ".agents" / "quality"

    _write_json(
        quality_dir / "check_quality.json",
        {
            "schema_version": 1,
            "providers": {
                "python": {"config": ".agents/quality/python-quality.json"},
                "web": {"config": ".agents/quality/web-quality.json"},
            },
        },
    )
    _write_json(
        quality_dir / "python-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "format": ["uv", "run", "ruff", "format", "--check", "."],
                "lint": [
                    "uv",
                    "run",
                    "ruff",
                    "check",
                    "--extend-select",
                    "F821,B904",
                    ".",
                ],
                "type_check": ["uv", "run", "mypy", "--strict", "src", "tests"],
                "test": ["uv", "run", "pytest", "-q"],
                "coverage": {
                    "command": ["uv", "run", "pytest", "--cov=src"],
                    "threshold": 0.80,
                    "min_package_coverage": 0.82,
                    "min_diff_coverage": 0.85,
                    "package_floors": ".agents/quality/coverage_floors.json",
                },
                "diff_coverage": [
                    "python3",
                    "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                    "--base-ref",
                    "{base_ref}",
                    "--min-diff-coverage",
                    "0.85",
                ],
            },
            "profiles": {
                "pr": ["format", "lint", "type_check", "test"],
                "epic": ["format", "lint", "type_check", "test", "coverage"],
            },
        },
    )
    _write_json(
        quality_dir / "web-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "lint": [
                    "python3",
                    "{skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py",
                    "--target-dir",
                    "src/preview",
                    "--base-ref",
                    "{base_ref}",
                ],
                "type_check": [
                    "python3",
                    "{skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py",
                    "--target-dir",
                    "src/preview",
                    "--base-ref",
                    "{base_ref}",
                ],
                "test_unit": [
                    "node",
                    "--test",
                    "--experimental-test-coverage",
                    "--test-reporter=lcov",
                    "--test-reporter-destination=build/js-lcov.info",
                    "tests/js/*.test.mjs",
                ],
                "test_e2e": ["npx", "--no-install", "playwright", "test", "tests/e2e/"],
                "diff_coverage": [
                    "python3",
                    "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                    "--lcov",
                    "build/js-lcov.info",
                    "--source-ext",
                    ".js,.mjs",
                    "--min-diff-coverage",
                    "0.80",
                ],
                "ui_review": [
                    "python3",
                    "{skills_dir}/web-quality-check/resources/scripts/audit_ui_state_and_styles.py",
                    "--base-ref",
                    "{base_ref}",
                ],
            },
            "profiles": {
                "pr": ["lint", "type_check", "test_unit"],
                "epic": [
                    "lint",
                    "type_check",
                    "test_unit",
                    "test_e2e",
                    "diff_coverage",
                    "ui_review",
                ],
            },
        },
    )
    _write_json(
        quality_dir / "coverage_floors.json",
        {
            "python": {
                "adapters": {
                    "src/lyrics_sync": 0.78,
                    "src/lyrics_sync/align": 0.88,
                    "src/lyrics_sync/other": 0.91,
                }
            },
            "web_modules": {
                "src/preview/static/align-studio.js": 0.50,
                "src/preview/static/untouched.js": 0.65,
            },
        },
    )
    _write_text(
        root / "src" / "lyrics_sync" / "align" / "ctc.py",
        "def align() -> int:\n    return 1\n",
    )
    _write_text(
        root / "src" / "preview" / "static" / "align-studio.js",
        "export function renderStudio() { return true; }\n",
    )
    _write_text(
        root / "src" / "preview" / "static" / "index.html",
        '<!doctype html><html><head><script src="/static/align-studio.js?v=20261128"></script></head></html>\n',
    )
    _write_text(
        root / "node_modules" / "ignored-pkg" / "index.html",
        '<script src="align-studio.js?v=0"></script>\n',
    )
    return root


@pytest.fixture(scope="module")
def six_stack_polyglot_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Read-only 6-stack polyglot repo matching SLQR-AR-02."""
    root = tmp_path_factory.mktemp("slqr_six_stack_repo")
    quality_dir = root / ".agents" / "quality"

    _write_json(
        quality_dir / "python-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "format": ["uv", "run", "ruff", "format", "--check", "."],
                "lint": ["uv", "run", "ruff", "check", "."],
                "type_check": ["uv", "run", "mypy", "--strict", "src", "tests"],
                "coverage": {
                    "command": ["uv", "run", "pytest", "--cov=src"],
                    "threshold": 0.80,
                    "min_diff_coverage": 0.85,
                },
            },
            "profiles": {"pr": ["format", "lint", "type_check"]},
        },
    )
    _write_json(
        quality_dir / "web-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "lint": ["npx", "--no-install", "eslint", "."],
                "type_check": ["npx", "--no-install", "tsc", "--noEmit"],
                "test_e2e": ["npx", "--no-install", "playwright", "test"],
                "diff_coverage": [
                    "python3",
                    "check_diff_coverage.py",
                    "--lcov",
                    "coverage/js-lcov.info",
                    "--source-ext",
                    ".js,.mjs",
                ],
                "ui_review": ["python3", "audit_ui_state_and_styles.py"],
            },
            "profiles": {"pr": ["lint", "type_check"]},
        },
    )
    _write_json(
        quality_dir / "flutter-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "format": [
                    "dart",
                    "format",
                    "--output=none",
                    "--set-exit-if-changed",
                    ".",
                ],
                "analyze": ["flutter", "analyze"],
                "test": ["flutter", "test"],
            },
            "profiles": {"pr": ["format", "analyze", "test"]},
        },
    )
    _write_json(
        quality_dir / "android-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "format": ["./gradlew", "spotlessCheck"],
                "lint": ["./gradlew", "detekt"],
                "test": ["./gradlew", "testDebugUnitTest"],
            },
            "profiles": {"pr": ["format", "lint", "test"]},
        },
    )
    _write_json(
        quality_dir / "ios-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "format": ["swiftformat", "--lint", "."],
                "lint": ["swiftlint", "lint", "--strict"],
                "test": ["swift", "test"],
            },
            "profiles": {"pr": ["format", "lint", "test"]},
        },
    )
    _write_json(
        quality_dir / "rust-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "format": ["cargo", "fmt", "--check"],
                "clippy": ["cargo", "clippy", "--all-targets", "--", "-D", "warnings"],
                "test": ["cargo", "test"],
            },
            "profiles": {"pr": ["format", "clippy", "test"]},
        },
    )
    _write_json(
        quality_dir / "coverage_floors.json",
        {
            "python": {"adapters": {"src/worker": 0.90}},
            "web_modules": {"src/web/app.js": 0.55},
        },
    )
    return root


def test_slqr_hp_03_resolve_quality_cli_emits_compact_scoped_lines_within_budget(
    hp03_polyglot_repo: Path,
) -> None:
    """[SLQR-HP-03] d3nexus resolve-quality emits compact file-scoped guidance within latency budgets."""
    resolver = _load_resolver_module()
    planned = [
        "src/lyrics_sync/align/ctc.py",
        "src/preview/static/align-studio.js",
    ]

    timings: list[float] = []
    plan: Any = None
    for _ in range(3):
        t0 = time.perf_counter()
        plan = resolver.resolve_quality_plan(
            hp03_polyglot_repo, planned, base_ref="develop"
        )
        timings.append(time.perf_counter() - t0)

    best_in_process = min(timings)
    assert best_in_process < 0.10, (
        f"resolve_quality_plan exceeded 0.10s budget: {best_in_process:.4f}s"
    )
    assert set(plan.active_stacks) == {"python", "web"}
    assert plan.cache_bust_templates == ("src/preview/static/index.html",)

    proc, cli_elapsed = _run_d3nexus(
        [
            "resolve-quality",
            "--files",
            "src/lyrics_sync/align/ctc.py",
            "src/preview/static/align-studio.js",
            "--base-ref",
            "develop",
        ],
        cwd=hp03_polyglot_repo,
    )
    assert proc.returncode == 0, f"CLI failed ({proc.returncode}): {proc.stderr}"
    assert cli_elapsed < 1.0, f"CLI exceeded 1.0s budget: {cli_elapsed:.4f}s"

    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert 5 <= len(lines) <= 10, (
        f"Expected 5-10 compact lines, got {len(lines)}:\n{proc.stdout}"
    )

    out = proc.stdout
    # Canonical Python test roots
    assert "tests/unit/**/test_*.py" in out
    assert "tests/integration/test_*.py" in out
    # Dual Web LCOV unit + Playwright Tier C2
    assert "DUAL REQUIRED -> unit LCOV in tests/js/*.test.mjs" in out
    assert "# tier: C2" in out
    assert "PLAYWRIGHT_BROWSER" in out
    # Matched floors from coverage_floors.json (and untouched adapter/module absent)
    assert "src/lyrics_sync/align" in out
    assert "88%" in out
    assert "src/preview/static/align-studio.js" in out
    assert "50%" in out
    assert "src/lyrics_sync/other" not in out
    assert "untouched.js" not in out
    # Cache-bust template
    assert "src/preview/static/index.html" in out
    assert "?v=" in out
    # Interpolated $D3NEXUS_KIT/skills and scoped TIER-B commands (no unexpanded placeholders)
    assert "$D3NEXUS_KIT/skills" in out
    assert "{skills_dir}" not in out
    assert "{base_ref}" not in out
    assert "src/lyrics_sync/align/ctc.py" in out
    assert "<test_files>" in out
    assert "--base-ref develop" in out


def _verify_slqr_ar_01_stdlib_purity_and_no_circular_imports() -> None:
    """[SLQR-AR-01] Stack lifecycle registry and quality plan resolver maintain zero circular imports and Python 3 stdlib purity."""
    forbidden = {"check_task_contract", "manage_worker_pool"}
    allowed_local = {"_stack_lifecycle_registry"}
    target_scripts = (
        IMPL_SCRIPTS_DIR / "_stack_lifecycle_registry.py",
        IMPL_SCRIPTS_DIR / "resolve_task_quality_plan.py",
    )

    for script_path in target_scripts:
        assert script_path.is_file(), f"Missing script: {script_path}"
        tree = ast.parse(
            script_path.read_text(encoding="utf-8"), filename=str(script_path)
        )
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])

        assert forbidden.isdisjoint(imported), (
            f"{script_path.name} has forbidden imports: {sorted(forbidden & imported)}"
        )
        non_stdlib = sorted(
            mod
            for mod in imported
            if mod not in sys.stdlib_module_names and mod not in allowed_local
        )
        assert non_stdlib == [], (
            f"{script_path.name} imports non-stdlib modules: {non_stdlib}"
        )

    # Import both modules in an isolated stdlib-only Python subprocess (-S disables site-packages)
    probe = (
        "import sys; "
        f"sys.path.insert(0, {str(IMPL_SCRIPTS_DIR)!r}); "
        "import _stack_lifecycle_registry, resolve_task_quality_plan; "
        "assert hasattr(resolve_task_quality_plan, 'resolve_quality_plan')"
    )
    clean_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    proc = subprocess.run(
        [sys.executable, "-S", "-c", probe],
        env=clean_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"Isolated stdlib import failed:\n{proc.stderr}"


def _verify_slqr_ar_02_single_stack_python_zero_untouched_noise(
    six_stack_polyglot_repo: Path,
) -> None:
    """[SLQR-AR-02] Single-stack Python invocation of resolve-quality emits zero lines mentioning Web, Flutter, Android, iOS, or Rust."""
    proc, _ = _run_d3nexus(
        [
            "resolve-quality",
            "--files",
            "src/worker/pipeline.py",
            "tests/unit/worker/test_pipeline.py",
        ],
        cwd=six_stack_polyglot_repo,
    )
    assert proc.returncode == 0, f"CLI failed: {proc.stderr}"
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert 5 <= len(lines) <= 10, (
        f"Expected 5-10 lines, got {len(lines)}:\n{proc.stdout}"
    )

    out = proc.stdout
    lowered = out.lower()
    assert "tests/unit/**/test_*.py" in out
    assert "src/worker" in out
    assert "90%" in out
    assert "src/worker/pipeline.py" in out
    assert "tests/unit/worker/test_pipeline.py" in out
    assert "<test_files>" not in out

    for forbidden_term in (
        "playwright",
        "lcov",
        "flutter",
        "gradlew",
        "swiftlint",
        "clippy",
    ):
        assert forbidden_term not in lowered, (
            f"Untouched stack term {forbidden_term!r} leaked into Python-only output:\n{out}"
        )


def _verify_slqr_fr_03_malformed_manifest_exits_2(tmp_path: Path) -> None:
    """[SLQR-FR-03] resolve_task_quality_plan exits 2 with clear diagnostic on malformed quality manifest JSON."""
    _write_text(
        tmp_path / ".agents" / "quality" / "web-quality.json",
        '{"schema_version": 1, "capabilities": {"lint": ["eslint", "."]',
    )
    proc, _ = _run_d3nexus(
        ["resolve-quality", "--files", "src/web/app.js"],
        cwd=tmp_path,
    )
    assert proc.returncode == 2, (
        f"Expected exit 2, got {proc.returncode}; stderr={proc.stderr!r}"
    )
    assert "web-quality.json" in proc.stderr


class TestSlqrQualityPlanResolver_Integration:
    """Tier C integration suite providing integration provenance for SLQR Task 03 scenarios."""

    def test_slqr_hp_03_resolve_quality_cli_emits_compact_scoped_lines_within_budget(
        self,
        hp03_polyglot_repo: Path,
    ) -> None:
        """[SLQR-HP-03] d3nexus resolve-quality emits compact file-scoped guidance within latency budgets."""
        test_slqr_hp_03_resolve_quality_cli_emits_compact_scoped_lines_within_budget(
            hp03_polyglot_repo
        )

    def test_slqr_ar_01_stdlib_purity_and_no_circular_imports(self) -> None:
        """[SLQR-AR-01] Stack lifecycle registry and quality plan resolver maintain zero circular imports and Python 3 stdlib purity."""
        _verify_slqr_ar_01_stdlib_purity_and_no_circular_imports()

    def test_slqr_ar_02_single_stack_python_zero_untouched_noise(
        self,
        six_stack_polyglot_repo: Path,
    ) -> None:
        """[SLQR-AR-02] Single-stack Python invocation of resolve-quality emits zero lines mentioning Web, Flutter, Android, iOS, or Rust."""
        _verify_slqr_ar_02_single_stack_python_zero_untouched_noise(
            six_stack_polyglot_repo
        )

    def test_slqr_fr_03_malformed_manifest_exits_2(self, tmp_path: Path) -> None:
        """[SLQR-FR-03] resolve_task_quality_plan exits 2 with clear diagnostic on malformed quality manifest JSON."""
        _verify_slqr_fr_03_malformed_manifest_exits_2(tmp_path)


# ---------------------------------------------------------------------------
# Unit tests for web_requires_lcov_unit_tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("manifest", "expected_required", "expected_globs"),
    [
        pytest.param(
            {
                "capabilities": {
                    "diff_coverage": [
                        "python3",
                        "check_diff_coverage.py",
                        "--lcov",
                        "build/js-lcov.info",
                        "--source-ext",
                        ".js,.mjs",
                    ]
                }
            },
            True,
            ("tests/js/*.test.mjs", "*.test.mjs", "*.test.js", "*.test.ts"),
            id="diff_coverage_lcov_js_mjs",
        ),
        pytest.param(
            {
                "capabilities": {
                    "diff_coverage": [
                        "python3",
                        "check_diff_coverage.py",
                        "--lcov=build/lcov.info",
                    ]
                },
                "test_routing": {"lcov_unit_test_globs": ["web/unit/*.test.mjs"]},
            },
            True,
            ("web/unit/*.test.mjs",),
            id="custom_lcov_globs_no_source_ext",
        ),
        pytest.param(
            {
                "capabilities": {
                    "test_unit": [
                        "node",
                        "--test",
                        "--test-reporter-destination=coverage/js.info",
                    ]
                }
            },
            True,
            ("tests/js/*.test.mjs", "*.test.mjs", "*.test.js", "*.test.ts"),
            id="test_unit_info_only",
        ),
        pytest.param(
            {
                "capabilities": {
                    "coverage": {
                        "command": ["vitest", "run", "--lcov", "coverage/lcov.info"],
                    }
                }
            },
            True,
            ("tests/js/*.test.mjs", "*.test.mjs", "*.test.js", "*.test.ts"),
            id="coverage_command_lcov",
        ),
        pytest.param(
            {
                "capabilities": {
                    "diff_coverage": [
                        "python3",
                        "check_diff_coverage.py",
                        "--lcov",
                        "build/ts-lcov.info",
                        "--source-ext",
                        ".ts,.tsx",
                    ]
                }
            },
            False,
            (),
            id="source_ext_excludes_js_mjs",
        ),
        pytest.param(
            {
                "capabilities": {
                    "lint": ["eslint", "."],
                    "test_unit": ["vitest", "run"],
                }
            },
            False,
            (),
            id="no_lcov_or_info",
        ),
        pytest.param(
            {"capabilities": {}},
            False,
            (),
            id="empty_capabilities",
        ),
        pytest.param(
            {"capabilities": "invalid"},
            False,
            (),
            id="non_mapping_capabilities",
        ),
    ],
)
def test_web_requires_lcov_unit_tests_variants(
    manifest: dict[str, Any],
    expected_required: bool,
    expected_globs: tuple[str, ...],
) -> None:
    """Verify web_requires_lcov_unit_tests covers diff_coverage, test_unit, coverage.command, and --source-ext."""
    resolver = _load_resolver_module()
    required, globs = resolver.web_requires_lcov_unit_tests(manifest)
    assert required is expected_required
    assert globs == expected_globs
    assert resolver.web_requires_lcov_unit_tests("not-a-dict") == (False, ())


# ---------------------------------------------------------------------------
# Unit tests for find_cache_bust_templates
# ---------------------------------------------------------------------------


def test_find_cache_bust_templates_discovers_templates_and_ignores_es_imports_and_ignored_dirs(
    tmp_path: Path,
) -> None:
    """Verify find_cache_bust_templates matches src/href templates only, skips ignored dirs, and ignores ES imports."""
    resolver = _load_resolver_module()

    _write_text(
        tmp_path / "templates" / "index.html",
        '<script src="/static/studio.js?v=1"></script>\n',
    )
    _write_text(
        tmp_path / "pages" / "view.astro",
        '---\nimport { helper } from "../src/helper.js";\n---\n<link rel="stylesheet" href="/assets/theme.css?v=2" />\n',
    )
    _write_text(
        tmp_path / "views" / "page.jinja2",
        '<script src="/js/studio.js"></script>\n',
    )
    _write_text(
        tmp_path / "views" / "es_only.html",
        '<script type="module">import { x } from "./helper.js";</script>\n',
    )
    # Non-UTF8 template is skipped gracefully without failing
    binary_tpl = tmp_path / "views" / "corrupt.html"
    binary_tpl.parent.mkdir(parents=True, exist_ok=True)
    binary_tpl.write_bytes(b"\xff\xfe\x00\x01")
    # Ignored directories must never be scanned
    for ignored_dir in ("node_modules", ".worktrees", "build", "dist", ".venv", ".git"):
        _write_text(
            tmp_path / ignored_dir / "leak.html",
            '<script src="studio.js?v=99"></script>\n',
        )

    web_manifest_ui = {"capabilities": {"ui_review": ["python3", "audit.py"]}}
    found_studio = resolver.find_cache_bust_templates(
        tmp_path,
        [
            "",
            "tests/js/studio.test.mjs",
            "src/static/studio.js (new)",
            "src/static/theme.css:L1-L20",
        ],
        web_manifest_ui,
    )
    assert found_studio == [
        "pages/view.astro",
        "templates/index.html",
        "views/page.jinja2",
    ]

    # ES module import without src=/href= attribute must NEVER match
    found_helper = resolver.find_cache_bust_templates(
        tmp_path, ["src/helper.js"], web_manifest_ui
    )
    assert found_helper == []

    # Missing repo root or only test/non-asset files returns empty list
    assert (
        resolver.find_cache_bust_templates(
            tmp_path / "does_not_exist", ["src/static/studio.js"], web_manifest_ui
        )
        == []
    )
    assert (
        resolver.find_cache_bust_templates(
            tmp_path, ["tests/js/studio.test.mjs", "src/mod.py"], web_manifest_ui
        )
        == []
    )

    # Disabled when manifest has neither ui_review nor cache_bust_extensions
    assert (
        resolver.find_cache_bust_templates(
            tmp_path, ["src/static/studio.js"], {"capabilities": {"lint": ["eslint"]}}
        )
        == []
    )
    assert (
        resolver.find_cache_bust_templates(tmp_path, ["src/static/studio.js"], None)
        == []
    )

    # Custom test_routing.cache_bust_extensions activates discovery without ui_review
    custom_manifest = {
        "capabilities": {"lint": ["eslint"]},
        "test_routing": {"cache_bust_extensions": [".css"]},
    }
    assert resolver.find_cache_bust_templates(
        tmp_path, ["src/static/studio.js", "src/static/theme.css"], custom_manifest
    ) == ["pages/view.astro"]


# ---------------------------------------------------------------------------
# Unit tests for --directory / --project / --prefix path rewriting & annotations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cap_lint", "planned_files", "expected_fragment", "unexpected_fragment"),
    [
        pytest.param(
            ["uv", "--directory", "apps/align-worker", "run", "ruff", "check", "."],
            ["apps/align-worker/src/mod.py (new)"],
            "uv --directory apps/align-worker run ruff check src/mod.py <test_files>",
            "apps/align-worker/src/mod.py",
            id="uv_directory_rewrites_and_adds_test_placeholder",
        ),
        pytest.param(
            [
                "uv",
                "--project=apps/align-worker",
                "run",
                "mypy",
                "--strict",
                "src",
                "tests",
            ],
            [
                "apps/align-worker/src/mod.py:L10-L45",
                "apps/align-worker/tests/unit/test_mod.py (L1-L20)",
            ],
            "uv --project=apps/align-worker run mypy --strict src/mod.py tests/unit/test_mod.py",
            "<test_files>",
            id="uv_project_rewrites_both_src_and_test",
        ),
        pytest.param(
            [
                "uv",
                "--directory",
                "apps/align-worker",
                "run",
                "ruff",
                "format",
                "--check",
                ".",
            ],
            ["apps/align-worker/src/a.py"],
            "uv --directory apps/align-worker run ruff format --check src/a.py <test_files>",
            "apps/align-worker/src/a.py",
            id="uv_directory_ruff_format",
        ),
    ],
)
def test_scoped_tier_b_monorepo_directory_rewriting(
    tmp_path: Path,
    cap_lint: list[str],
    planned_files: list[str],
    expected_fragment: str,
    unexpected_fragment: str,
) -> None:
    """Verify --directory / --project / --prefix strips wrapper prefix from scoped targets and handles annotations."""
    resolver = _load_resolver_module()
    _write_json(
        tmp_path / ".agents" / "quality" / "python-quality.json",
        {
            "schema_version": 1,
            "capabilities": {"lint": cap_lint},
            "profiles": {"pr": ["lint"]},
        },
    )
    plan = resolver.resolve_quality_plan(tmp_path, planned_files)
    joined = " && ".join(plan.scoped_tier_b_commands)
    assert expected_fragment in joined
    assert unexpected_fragment not in joined


def test_scoped_tier_b_npm_prefix_rewriting(tmp_path: Path) -> None:
    """Verify --prefix <dir> rewrites relative targets on file-scoping tools."""
    resolver = _load_resolver_module()
    _write_json(
        tmp_path / ".agents" / "quality" / "flutter-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "format": [
                    "npm",
                    "--prefix",
                    "apps/mobile",
                    "exec",
                    "--",
                    "dart",
                    "format",
                    "--output=none",
                    "--set-exit-if-changed",
                    ".",
                ],
            },
            "profiles": {"pr": ["format"]},
        },
    )
    plan = resolver.resolve_quality_plan(
        tmp_path, ["apps/mobile/lib/main.dart", "apps/mobile/test/main_test.dart"]
    )
    joined = " && ".join(plan.scoped_tier_b_commands)
    assert "lib/main.dart test/main_test.dart" in joined
    assert "apps/mobile/lib/main.dart" not in joined


# ---------------------------------------------------------------------------
# Unit tests for is_full_repo_python_tier_b_subcommand
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("sub", "cap", "expected"),
    [
        pytest.param(
            ["uv", "run", "mypy", "--strict", "src", "tests"],
            ["uv", "run", "mypy", "--strict", "src", "tests"],
            True,
            id="mypy_src_tests_matches_cap",
        ),
        pytest.param(
            ["uv", "run", "mypy", "--strict", "src/pkg/a.py", "tests/unit/test_a.py"],
            ["uv", "run", "mypy", "--strict", "src", "tests"],
            False,
            id="mypy_scoped_files_passes",
        ),
        pytest.param(
            ["uv", "run", "ruff", "check", "--extend-select", "F821,B904", "."],
            ["uv", "run", "ruff", "check", "."],
            True,
            id="ruff_check_dot",
        ),
        pytest.param(
            [
                "uv",
                "--directory",
                "apps/worker",
                "run",
                "ruff",
                "format",
                "--check",
                ".",
            ],
            [
                "uv",
                "--directory",
                "apps/worker",
                "run",
                "ruff",
                "format",
                "--check",
                ".",
            ],
            True,
            id="uv_directory_ruff_format_dot",
        ),
        pytest.param(
            ["python3", "-m", "pyright", "src", "tests"],
            None,
            True,
            id="pyright_python_m_no_cap",
        ),
        pytest.param(
            ["ty", "check", "."],
            None,
            True,
            id="ty_check_dot_no_cap",
        ),
        pytest.param(
            ["uv", "run", "mypy", "--strict", "src", "tests"],
            ["uv", "run", "mypy", "skills/foo.py", "tests/test_foo.py"],
            False,
            id="cap_not_full_repo_exempt",
        ),
        pytest.param(
            ["uv", "run", "ruff", "check", "--config", "ruff.toml", "src/mod.py"],
            ["uv", "run", "ruff", "check", "."],
            False,
            id="ruff_scoped_with_config_flag",
        ),
        pytest.param(
            ["uv", "run", "pytest", "."],
            None,
            False,
            id="non_static_tool_pytest",
        ),
    ],
)
def test_is_full_repo_python_tier_b_subcommand(
    sub: list[str],
    cap: list[str] | None,
    expected: bool,
) -> None:
    """Verify is_full_repo_python_tier_b_subcommand detects full-repo Python checks accurately."""
    resolver = _load_resolver_module()
    assert resolver.is_full_repo_python_tier_b_subcommand(sub, cap) is expected


# ---------------------------------------------------------------------------
# Additional edge-case tests: fallback without .agents/quality, --json, test_routing, CLI errors
# ---------------------------------------------------------------------------


def test_builtin_stack_fallback_and_json_mode_and_test_routing(tmp_path: Path) -> None:
    """Verify fallback to BUILTIN_STACKS when .agents/quality is absent, plus --json output and test_routing."""
    resolver = _load_resolver_module()

    # 1. Fallback without .agents/quality/
    fallback_plan = resolver.resolve_quality_plan(
        tmp_path, ["src/app/service.py", "tests/unit/test_service.py"]
    )
    assert fallback_plan.active_stacks == ("python",)
    compact = resolver.format_compact_plan(fallback_plan)
    assert "tests/unit/**/test_*.py" in compact
    assert "ruff check src/app/service.py tests/unit/test_service.py" in compact

    # 2. Explicit test_routing (forbidden_test_globs + paired_source_globs) + unique basename web floor + --json
    _write_json(
        tmp_path / ".agents" / "quality" / "python-quality.json",
        {
            "schema_version": 1,
            "test_routing": {
                "canonical_test_globs": ["tests/unit/**/test_*.py"],
                "forbidden_test_globs": ["tests/test_*.py", "scripts/test_*.py"],
                "paired_source_globs": ["src/api/**/*.py"],
            },
            "capabilities": {"lint": ["ruff", "check", "."]},
            "profiles": {"pr": ["lint"]},
        },
    )
    _write_json(
        tmp_path / ".agents" / "quality" / "web-quality.json",
        {
            "schema_version": 1,
            "capabilities": {"lint": ["npx", "--no-install", "eslint", "."]},
            "profiles": {"pr": ["lint"]},
        },
    )
    _write_json(
        tmp_path / ".agents" / "quality" / "coverage_floors.json",
        {
            "web_modules": {
                "widget.js": 0.60,
                "a/dup.js": 0.40,
                "b/dup.js": 0.50,
            }
        },
    )

    proc, _ = _run_d3nexus(
        [
            "resolve-quality",
            "--repo-root",
            str(tmp_path),
            "--files",
            "src/api/routes.py",
            "web/src/widget.js",
            "web/src/dup.js",
            "--json",
        ],
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert set(payload["active_stacks"]) == {"python", "web"}
    py_entry = next(s for s in payload["stack_plans"] if s["stack_id"] == "python")
    assert py_entry["forbidden_test_globs"] == ["tests/test_*.py", "scripts/test_*.py"]
    assert py_entry["paired_source_matches"] == ["src/api/routes.py"]
    web_entry = next(s for s in payload["stack_plans"] if s["stack_id"] == "web")
    web_floors = dict(web_entry["coverage_floors"])
    assert web_floors.get("widget.js") == pytest.approx(0.60)
    assert "a/dup.js" not in web_floors
    assert "b/dup.js" not in web_floors


@pytest.mark.parametrize(
    ("bad_file", "bad_content", "expected_err_substr"),
    [
        pytest.param(
            "check_quality.json",
            "{bad json",
            "check_quality.json",
            id="malformed_check_quality",
        ),
        pytest.param(
            "coverage_floors.json",
            "[1, 2, 3]",
            "coverage_floors.json",
            id="non_object_coverage_floors",
        ),
    ],
)
def test_cli_exits_2_on_missing_files_or_corrupt_auxiliary_json(
    tmp_path: Path,
    bad_file: str,
    bad_content: str,
    expected_err_substr: str,
) -> None:
    """Verify CLI exits 2 on missing --files or malformed check_quality.json / coverage_floors.json."""
    proc_missing, _ = _run_d3nexus(["resolve-quality"], cwd=tmp_path)
    assert proc_missing.returncode == 2
    assert proc_missing.stderr.strip()

    _write_text(tmp_path / ".agents" / "quality" / bad_file, bad_content)
    proc_bad, _ = _run_d3nexus(["resolve-quality", "--files", "src/a.py"], cwd=tmp_path)
    assert proc_bad.returncode == 2
    assert expected_err_substr in proc_bad.stderr


def test_in_process_main_unmatched_floors_and_edge_branches(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exercise main() in-process, unmatched files, rich coverage_floors schemas, and edge branches."""
    resolver = _load_resolver_module()

    # Missing/empty --files exit 2
    assert resolver.main([]) == 2
    assert resolver.main(["--files", "   "]) == 2
    assert "resolve-quality error" in capsys.readouterr().err

    # Unmatched file (e.g. README.md) exits 0 with concise note
    assert resolver.main(["--repo-root", str(tmp_path), "--files", "./README.md"]) == 0
    unmatched_out = capsys.readouterr().out
    assert "stacks: none" in unmatched_out
    assert "README.md" in unmatched_out

    # Rich coverage_floors schemas: dict floor, percentage > 1, src-stripped adapter, packages, flat prefix, unique basename
    _write_json(
        tmp_path / ".agents" / "quality" / "python-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "lint": ["ruff", "check", "."],
                "boundaries": ["lint-imports"],
                "coverage": {
                    "command": ["pytest", "--cov=src"],
                    "package_floors": ".agents/quality/extra_floors.json",
                },
            },
            "profiles": {"pr": ["lint"]},
        },
    )
    _write_json(
        tmp_path / ".agents" / "quality" / "web-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "lint": ["npx", "--no-install", "eslint", "."],
                "ui_review": ["python3", "audit_ui_state_and_styles.py"],
            },
            "profiles": {"pr": ["lint"]},
        },
    )
    _write_json(
        tmp_path / ".agents" / "quality" / "extra_floors.json",
        {
            "python": {
                "adapters": {
                    "pkg/core": {"floor": 85.5},
                    "bad_bool": True,
                    "bad_str": "n/a",
                }
            },
            "web_modules": {
                "deep/path/solo.js": {"min_coverage": 62},
            },
            "packages": {"packages/shared": 0.77},
            "src/pkg/flat": 92,
        },
    )
    _write_text(
        tmp_path / "templates" / "base.jinja",
        '<link rel="stylesheet" href="/static/theme.css?v=1">\n',
    )

    rc_json = resolver.main(
        [
            "--repo-root",
            str(tmp_path),
            "--files",
            "src/pkg/core/engine.py",
            "src/pkg/flat/util.py",
            "pyproject.toml",
            "assets/solo.js",
            "assets/theme.css",
            "--json",
        ]
    )
    assert rc_json == 0
    data = json.loads(capsys.readouterr().out)
    py_plan = next(s for s in data["stack_plans"] if s["stack_id"] == "python")
    py_floors = dict(py_plan["coverage_floors"])
    assert py_floors["pkg/core"] == pytest.approx(0.855)
    assert py_floors["src/pkg/flat"] == pytest.approx(0.92)
    assert "lint-imports" in py_plan["scoped_tier_b_commands"]
    web_plan = next(s for s in data["stack_plans"] if s["stack_id"] == "web")
    assert dict(web_plan["coverage_floors"])["deep/path/solo.js"] == pytest.approx(0.62)
    assert data["cache_bust_templates"] == ["templates/base.jinja"]

    # Format compact output renders fractional percentages cleanly (85.5%)
    rc_text = resolver.main(
        [
            "--repo-root",
            str(tmp_path),
            "--files",
            "src/pkg/core/engine.py",
        ]
    )
    assert rc_text == 0
    assert "85.5%" in capsys.readouterr().out

    # Malformed manifest in-process returns exit 2
    _write_text(tmp_path / ".agents" / "quality" / "rust-quality.json", "{broken")
    assert resolver.main(["--repo-root", str(tmp_path), "--files", "src/lib.rs"]) == 2
    assert "rust-quality.json" in capsys.readouterr().err

    # Edge inputs for is_full_repo_python_tier_b_subcommand
    assert resolver.is_full_repo_python_tier_b_subcommand([]) is False
    assert (
        resolver.is_full_repo_python_tier_b_subcommand(["ruff", "check", "."], [])
        is False
    )
    assert (
        resolver.is_full_repo_python_tier_b_subcommand(["ruff", "check", "--", "."])
        is True
    )
    assert (
        resolver.is_full_repo_python_tier_b_subcommand(["mypy", "--strict", "src/a.py"])
        is False
    )
