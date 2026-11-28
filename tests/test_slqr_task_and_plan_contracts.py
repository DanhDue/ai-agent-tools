"""Integration and contract tests for Task 04: Fail-Closed Task and Plan Contract Guards.

Covers BDD Scenarios:
- SLQR-HP-04: check_task_contract validates multi-target mypy and skills_dir commands in both --design and --check-plan modes
- SLQR-EC-03: Bundled ES module imports without src/href template attributes do not trigger false-positive cache-bust template requirements
- SLQR-EC-04: Final epic task (Task N) and pyproject.toml edits are permitted to run workspace-wide Python static checks
- SLQR-ST-03: Fixing violations in a standalone Markdown plan transitions check_task_contract --check-plan from exit 1 FAIL to exit 0 PASS idempotently
- SLQR-AR-03: Repositories without .agents/quality manifests bypass manifest-only Shift-Left guards without false positives
- SLQR-FR-04: check_task_contract --design fails closed on each independent Shift-Left violation with distinct guard diagnostics
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
CHECK_CONTRACT_SCRIPT = SCRIPTS_DIR / "check_task_contract.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import resolve_task_quality_plan as rtqp  # noqa: E402

ISOLATED_GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "SLQR Tester",
    "GIT_AUTHOR_EMAIL": "slqr@example.com",
    "GIT_COMMITTER_NAME": "SLQR Tester",
    "GIT_COMMITTER_EMAIL": "slqr@example.com",
}

TABLE_HEADER = (
    "| ID | Phase | Command | Expect | Needs |\n"
    "|----|-------|---------|--------|-------|\n"
)


def _git_env() -> dict[str, str]:
    merged = dict(os.environ)
    merged.update(ISOLATED_GIT_ENV)
    return merged


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        env=_git_env(),
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _write(repo: Path, rel: str, content: str) -> Path:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_json(repo: Path, rel: str, payload: dict[str, Any]) -> Path:
    return _write(repo, rel, json.dumps(payload, indent=2) + "\n")


def _commit(repo: Path, msg: str = "commit") -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "slqr@example.com")
    _git(repo, "config", "user.name", "SLQR Tester")
    _write(repo, ".gitignore", "build/\n")
    _write(repo, "README.md", "# Demo Repo\n")
    _write(repo, "tool.py", "print('ok')\n")
    _write(
        repo,
        "tests/unit/test_smoke.py",
        "def test_smoke() -> None:\n    assert True\n",
    )


def _run_contract(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK_CONTRACT_SCRIPT), *args],
        cwd=str(repo),
        env=_git_env(),
        capture_output=True,
        text=True,
        check=False,
    )


def _hld_text(
    *,
    integration_roots: str = "tests",
    env_body: str = "Runs in temp dirs. Variables: PLAYWRIGHT_BROWSER.",
) -> str:
    return (
        "# Demo Epic\n\n"
        "## Integration Test Plan\n\n"
        f"Integration test roots: {integration_roots}\n\n"
        "Protected paths: README.md\n\n"
        "Integration results: python3 tool.py all -> build/all.xml\n\n"
        "## Verification Environment\n\n"
        f"{env_body}\n"
    )


def _format_allowed_entry(item: str) -> str:
    if item.endswith(" (new)"):
        return f"- `{item[:-6]}` (new)"
    return f"- `{item}`"


def _task_md(
    *,
    allowed: list[str],
    rows: list[str],
    dod: str = "- [ ] All checks pass (V2, V3, V4)\n",
    status: str = "todo",
    order: str | None = None,
    dependencies: str = "",
) -> str:
    allowed_block = "\n".join(_format_allowed_entry(item) for item in allowed)
    rows_block = "\n".join(rows) + "\n"
    order_line = f'order: "{order}"\n' if order else ""
    dep_sec = (
        f"\n## Dependencies & Blockers\n\n{dependencies}\n" if dependencies else ""
    )
    return (
        f'---\nstatus: "{status}"\n{order_line}---\n'
        "# Task\n\n"
        "## Files\n\n"
        f"Allowed files:\n{allowed_block}\n\n"
        "Read-only context:\n- `README.md` — repo note\n\n"
        f"## Verification\n\n{TABLE_HEADER}{rows_block}\n"
        f"## Definition of Done\n\n{dod}\n"
        "## Stop and Report If\n\n- Contract mismatch.\n\n"
        "## Decisions Already Made\n\n- Grounded shift-left contract decision.\n"
        f"{dep_sec}"
    )


def _write_polyglot_manifests(
    repo: Path,
    *,
    python_test_routing: dict[str, Any] | None = None,
    web_test_routing: dict[str, Any] | None = None,
    web_target_dir: str = "src/preview",
) -> None:
    py_manifest: dict[str, Any] = {
        "schema_version": 1,
        "capabilities": {
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
        },
        "profiles": {
            "pr": ["lint", "type_check"],
            "epic": ["lint", "type_check"],
        },
    }
    if python_test_routing is not None:
        py_manifest["test_routing"] = python_test_routing

    web_manifest: dict[str, Any] = {
        "schema_version": 1,
        "capabilities": {
            "type_check": [
                "python3",
                "{skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py",
                "--target-dir",
                web_target_dir,
            ],
            "diff_coverage": [
                "python3",
                "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                "--lcov",
                "build/js-lcov.info",
                "--source-ext",
                ".js,.mjs",
                "--base-ref",
                "{base_ref}",
            ],
            "ui_review": [
                "python3",
                "{skills_dir}/web-quality-check/resources/scripts/run_playwright_harness.py",
            ],
        },
        "profiles": {
            "pr": ["type_check", "diff_coverage"],
            "epic": ["type_check", "diff_coverage", "ui_review"],
        },
    }
    if web_test_routing is not None:
        web_manifest["test_routing"] = web_test_routing

    _write_json(repo, ".agents/quality/python-quality.json", py_manifest)
    _write_json(repo, ".agents/quality/web-quality.json", web_manifest)


def test_slqr_hp_04_multi_target_mypy_and_skills_dir_pass_design_and_check_plan(
    tmp_path: Path,
) -> None:
    """[SLQR-HP-04] [Tier C - Integration] check_task_contract validates multi-target mypy and skills_dir commands in both --design and --check-plan modes."""
    repo = tmp_path / "hp04_repo"
    _init_repo(repo)
    _write_polyglot_manifests(repo, web_target_dir="src/preview")
    _write(
        repo, "src/pkg/service.py", "def compute(x: int) -> int:\n    return x + 1\n"
    )
    _write(
        repo,
        "tests/unit/test_service.py",
        "def test_compute() -> None:\n    assert True\n",
    )
    _write(repo, "src/preview/static/app.js", "export function boot() { return 1; }\n")
    _write(
        repo,
        "src/preview/static/index.html",
        '<!doctype html><html><head><script src="/static/app.js?v=20261128"></script></head></html>\n',
    )
    _write(
        repo,
        "tests/js/app.test.mjs",
        "import test from 'node:test';\ntest('boot', () => {});\n",
    )

    hld = _write(repo, ".devtool/epic/demo/demo.md", _hld_text())
    task = _write(
        repo,
        ".devtool/epic/demo/task_01_poly.md",
        _task_md(
            allowed=[
                "src/pkg/service.py",
                "tests/unit/test_service.py",
                "src/preview/static/app.js",
                "src/preview/static/index.html",
                "tests/js/app.test.mjs",
            ],
            rows=[
                "| V1 | RED | `python3 -m pytest tests/unit/test_service.py::test_compute` | exit 1 | — |",
                "| V2 | GREEN | `python3 -m pytest tests/unit/test_service.py && node --test tests/js/app.test.mjs` | exit 0 | — |",
                '| V3 | TIER-B | `uv run ruff check --extend-select F821,B904 src/pkg/service.py tests/unit/test_service.py && uv run mypy --strict src/pkg/service.py tests/unit/test_service.py && python3 "$D3NEXUS_KIT/skills/web-quality-check/resources/scripts/check_vanilla_js.py" --target-dir src/preview` | exit 0 | — |',
                "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
            ],
        ),
    )
    plan = _write(
        repo,
        "docs/superpowers/plans/2026-11-28-poly.md",
        "# Polyglot Plan\n\n"
        "### Task 1: Update Python service and Web preview\n\n"
        "**Files:**\n"
        "- Modify: `src/pkg/service.py:1-5`\n"
        "- Modify: `src/preview/static/app.js`\n"
        "- Modify: `src/preview/static/index.html`\n"
        "- Test: `tests/unit/test_service.py`\n"
        "- Test: `tests/js/app.test.mjs`\n\n"
        "Run: `uv run ruff check --extend-select F821,B904 src/pkg/service.py tests/unit/test_service.py`\n"
        "Run: `uv run mypy --strict src/pkg/service.py tests/unit/test_service.py`\n"
        'Run: `python3 "$D3NEXUS_KIT/skills/web-quality-check/resources/scripts/check_vanilla_js.py" --target-dir src/preview`\n'
        "Run: `node --test tests/js/app.test.mjs`\n",
    )
    _commit(repo, "hp04 base")

    design_res = _run_contract(
        repo, "--design", "--hld", str(hld), "--tasks", str(task)
    )
    assert design_res.returncode == 0, design_res.stdout + design_res.stderr
    assert design_res.stdout.splitlines() == ["Result: 0 problems — PASS"]

    plan_res = _run_contract(repo, "--check-plan", str(plan))
    assert plan_res.returncode == 0, plan_res.stdout + plan_res.stderr
    assert plan_res.stdout.splitlines() == ["Result: 0 problems — PASS"]

    # --check-plan --json and --verbose parity
    plan_json_res = _run_contract(repo, "--check-plan", str(plan), "--json")
    assert plan_json_res.returncode == 0, plan_json_res.stdout + plan_json_res.stderr
    payload = json.loads(plan_json_res.stdout)
    assert payload["status"] == "PASS"
    assert payload["problems"] == []

    plan_verbose_res = _run_contract(repo, "--check-plan", str(plan), "--verbose")
    assert plan_verbose_res.returncode == 0
    assert plan_verbose_res.stdout.splitlines()[-1] == "Result: 0 problems — PASS"


class TestSLQRTaskAndPlanContracts_Integration:
    """Tier C integration suite covering SLQR-HP-04, SLQR-EC-03, SLQR-EC-04, SLQR-ST-03, SLQR-AR-03, SLQR-FR-04."""

    def test_slqr_hp_04_integration_design_and_check_plan(self, tmp_path: Path) -> None:
        """[SLQR-HP-04] Integration runner provenance for multi-target mypy and skills_dir commands."""
        test_slqr_hp_04_multi_target_mypy_and_skills_dir_pass_design_and_check_plan(
            tmp_path
        )

    def test_slqr_ec_03_es_module_imports_do_not_trigger_cache_bust_templates(
        self, tmp_path: Path
    ) -> None:
        """[SLQR-EC-03] [Tier C - Integration] Bundled ES module imports without src/href template attributes do not trigger false-positive cache-bust template requirements."""
        repo = tmp_path / "ec03_repo"
        _init_repo(repo)
        _write_json(
            repo,
            ".agents/quality/web-quality.json",
            {
                "schema_version": 1,
                "capabilities": {
                    "lint": ["eslint", "."],
                    "type_check": ["tsc", "--noEmit"],
                    "diff_coverage": [
                        "python3",
                        "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                        "--lcov",
                        "build/js-lcov.info",
                        "--source-ext",
                        ".js,.mjs",
                    ],
                    "ui_review": [
                        "python3",
                        "{skills_dir}/web-quality-check/resources/scripts/run_playwright_harness.py",
                    ],
                },
                "profiles": {
                    "pr": ["lint", "type_check"],
                    "epic": ["lint", "type_check"],
                },
            },
        )
        _write(repo, "apps/web/src/store.ts", "export const state = { ready: true };\n")
        _write(
            repo,
            "apps/web/src/helper.js",
            "import { state } from './store';\nexport function label() { return String(state.ready); }\n",
        )
        _write(
            repo,
            "apps/web/tests/helper.test.mjs",
            "import test from 'node:test';\ntest('label', () => {});\n",
        )
        _write(
            repo,
            "apps/web/src/pages/index.astro",
            "---\nimport { state } from '../store';\nimport { label } from '../helper.js';\n---\n"
            "<html><body><script>import { label } from '../helper.js'; console.log(label());</script></body></html>\n",
        )
        _write(
            repo,
            "apps/web/public/layout.html",
            "<!doctype html><html><body><script type='module'>import '../src/helper.js';</script></body></html>\n",
        )

        hld = _write(repo, ".devtool/epic/demo/demo.md", _hld_text())
        task = _write(
            repo,
            ".devtool/epic/demo/task_01_es_mod.md",
            _task_md(
                allowed=[
                    "apps/web/src/helper.js",
                    "apps/web/tests/helper.test.mjs",
                ],
                rows=[
                    "| V1 | RED | `node --test apps/web/tests/helper.test.mjs` | exit 1 | — |",
                    "| V2 | GREEN | `node --test apps/web/tests/helper.test.mjs` | exit 0 | — |",
                    "| V3 | TIER-B | `eslint apps/web/src/helper.js && tsc --noEmit` | exit 0 | — |",
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
            ),
        )
        _commit(repo, "ec03 es module imports")

        plan = rtqp.resolve_quality_plan(
            repo, ["apps/web/src/helper.js", "apps/web/tests/helper.test.mjs"]
        )
        assert plan.cache_bust_templates == ()

        res = _run_contract(repo, "--design", "--hld", str(hld), "--tasks", str(task))
        assert res.returncode == 0, res.stdout + res.stderr
        assert res.stdout.splitlines() == ["Result: 0 problems — PASS"]

    def test_slqr_ec_04_final_task_and_pyproject_allow_full_repo_while_intermediate_fails(
        self, tmp_path: Path
    ) -> None:
        """[SLQR-EC-04] [Tier C - Integration] Final epic task (Task N) and pyproject.toml edits are permitted to run workspace-wide Python static checks."""
        repo = tmp_path / "ec04_repo"
        _init_repo(repo)
        _write_json(
            repo,
            ".agents/quality/python-quality.json",
            {
                "schema_version": 1,
                "capabilities": {
                    "lint": ["uv", "run", "ruff", "check", "."],
                    "type_check": ["uv", "run", "mypy", "--strict", "src", "tests"],
                },
                "profiles": {
                    "pr": ["lint", "type_check"],
                    "epic": ["lint", "type_check"],
                },
            },
        )
        _write(repo, "pyproject.toml", "[project]\nname = 'demo'\n")
        _write(repo, "src/pkg/a.py", "def a() -> int:\n    return 1\n")
        _write(repo, "src/pkg/b.py", "def b() -> int:\n    return 2\n")
        hld = _write(repo, ".devtool/epic/demo/demo.md", _hld_text())

        # 1. Task 1 (intermediate) runs full-repo `mypy --strict src tests` -> MUST FAIL
        t1_full = _write(
            repo,
            ".devtool/epic/demo/task_01_a.md",
            _task_md(
                allowed=["src/pkg/a.py"],
                rows=[
                    "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                    "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                    "| V3 | TIER-B | `uv run ruff check src/pkg/a.py && uv run mypy --strict src tests` | exit 0 | — |",
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
                order="a01",
            ),
        )
        t2_final = _write(
            repo,
            ".devtool/epic/demo/task_02_b.md",
            _task_md(
                allowed=["src/pkg/b.py"],
                rows=[
                    "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                    "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                    "| V3 | TIER-B | `uv run ruff check . && uv run mypy --strict src tests` | exit 0 | — |",
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
                order="a02",
            ),
        )
        _commit(repo, "ec04 intermediate fail")

        fail_res = _run_contract(
            repo, "--design", "--hld", str(hld), "--tasks", str(t1_full), str(t2_final)
        )
        assert fail_res.returncode == 1, fail_res.stdout
        problem_lines = [
            line
            for line in fail_res.stdout.splitlines()
            if not line.startswith(("Implicit protected paths:", "Result:"))
        ]
        assert len(problem_lines) == 1, problem_lines
        assert "task_01_a:V3:" in problem_lines[0]
        assert "intermediate task" in problem_lines[0]
        assert not any(line.startswith("task_02_b:") for line in problem_lines)
        assert "Result: 1 problems — FAIL" in fail_res.stdout

        # 2. Task 1 scoped + Task 2 (final) workspace-wide -> PASS
        t1_scoped = _write(
            repo,
            ".devtool/epic/demo/task_01_a.md",
            _task_md(
                allowed=["src/pkg/a.py"],
                rows=[
                    "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                    "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                    "| V3 | TIER-B | `uv run ruff check src/pkg/a.py && uv run mypy --strict src/pkg/a.py` | exit 0 | — |",
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
                order="a01",
            ),
        )
        _commit(repo, "ec04 scoped t1")

        pass_res = _run_contract(
            repo,
            "--design",
            "--hld",
            str(hld),
            "--tasks",
            str(t1_scoped),
            str(t2_final),
        )
        assert pass_res.returncode == 0, pass_res.stdout + pass_res.stderr
        assert pass_res.stdout.splitlines() == ["Result: 0 problems — PASS"]

        # 3. Task 1 modifying pyproject.toml + src/pkg/a.py with workspace-wide mypy -> PASS
        t1_pyproject = _write(
            repo,
            ".devtool/epic/demo/task_01_a.md",
            _task_md(
                allowed=["src/pkg/a.py", "pyproject.toml"],
                rows=[
                    "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                    "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                    "| V3 | TIER-B | `uv run ruff check . && uv run mypy --strict src tests` | exit 0 | — |",
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
                order="a01",
            ),
        )
        _commit(repo, "ec04 pyproject allowed")

        pass_pyproj = _run_contract(
            repo,
            "--design",
            "--hld",
            str(hld),
            "--tasks",
            str(t1_pyproject),
            str(t2_final),
        )
        assert pass_pyproj.returncode == 0, pass_pyproj.stdout + pass_pyproj.stderr
        assert pass_pyproj.stdout.splitlines() == ["Result: 0 problems — PASS"]

    def test_slqr_st_03_check_plan_fail_to_pass_idempotently(
        self, tmp_path: Path
    ) -> None:
        """[SLQR-ST-03] [Tier C - Integration] Fixing violations in a standalone Markdown plan transitions check_task_contract --check-plan from exit 1 FAIL to exit 0 PASS idempotently."""
        repo = tmp_path / "st03_repo"
        _init_repo(repo)
        _write_polyglot_manifests(repo, web_target_dir="src/preview")
        _write(repo, "src/preview/static/app.js", "export const v = 1;\n")
        _write(
            repo,
            "src/preview/static/index.html",
            '<!doctype html><html><head><script src="/static/app.js?v=1"></script></head></html>\n',
        )
        _write(
            repo,
            "tests/js/app.test.mjs",
            "import test from 'node:test';\ntest('ok', () => {});\n",
        )

        plan_rel = "docs/superpowers/plans/2026-11-28-demo.md"
        broken_plan = _write(
            repo,
            plan_rel,
            "# Demo Standalone Plan\n\n"
            "### Task 1: Update preview asset\n\n"
            "**Files:**\n"
            "- Modify: `src/preview/static/app.js:1-1`\n\n"
            "```bash\n"
            "python3 {skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py --target-dir src/preview\n"
            "npx playwright test tests/e2e/studio.spec.js\n"
            "```\n",
        )
        _commit(repo, "st03 broken plan")

        fail_res = _run_contract(repo, "--check-plan", str(broken_plan))
        assert fail_res.returncode == 1, fail_res.stdout + fail_res.stderr
        assert "unexpanded manifest placeholder '{skills_dir}'" in fail_res.stdout
        assert "bare 'npx'" in fail_res.stdout
        assert "LCOV" in fail_res.stdout
        assert "src/preview/static/index.html" in fail_res.stdout
        assert "Result: 4 problems — FAIL" in fail_res.stdout

        # Remediate all four defects
        fixed_plan = _write(
            repo,
            plan_rel,
            "# Demo Standalone Plan\n\n"
            "### Task 1: Update preview asset\n\n"
            "**Files:**\n"
            "- Modify: `src/preview/static/app.js:1-1`\n"
            "- Modify: `src/preview/static/index.html`\n"
            "- Test: `tests/js/app.test.mjs`\n\n"
            "```bash\n"
            'python3 "$D3NEXUS_KIT/skills/web-quality-check/resources/scripts/check_vanilla_js.py" --target-dir src/preview\n'
            "node --test tests/js/app.test.mjs\n"
            "npx --no-install playwright test tests/e2e/studio.spec.js\n"
            "```\n",
        )
        _commit(repo, "st03 fixed plan")

        pass_1 = _run_contract(repo, "--check-plan", str(fixed_plan))
        pass_2 = _run_contract(repo, "--check-plan", str(fixed_plan))
        assert pass_1.returncode == 0, pass_1.stdout + pass_1.stderr
        assert pass_2.returncode == 0, pass_2.stdout + pass_2.stderr
        assert pass_1.stdout.splitlines() == ["Result: 0 problems — PASS"]
        assert pass_2.stdout == pass_1.stdout

    def test_slqr_ar_03_repo_without_quality_manifests_bypasses_manifest_guards(
        self, tmp_path: Path
    ) -> None:
        """[SLQR-AR-03] [Tier C - Integration] Repositories without .agents/quality manifests bypass manifest-only Shift-Left guards without false positives."""
        repo = tmp_path / "ar03_minimal_repo"
        _init_repo(repo)
        assert not (repo / ".agents" / "quality").exists()

        _write(repo, "src/core.py", "def run() -> int:\n    return 42\n")
        _write(repo, "src/web/app.js", "export const x = 1;\n")
        _write(
            repo,
            "src/web/index.html",
            '<!doctype html><script src="/app.js?v=1"></script>\n',
        )
        _write(
            repo, "tests/test_root.py", "def test_root() -> None:\n    assert True\n"
        )
        hld = _write(repo, ".devtool/epic/demo/demo.md", _hld_text())
        task = _write(
            repo,
            ".devtool/epic/demo/task_01_minimal.md",
            _task_md(
                allowed=[
                    "src/core.py",
                    "src/web/app.js",
                    "tests/test_root.py",
                ],
                rows=[
                    "| V1 | RED | `python3 -m pytest tests/test_root.py::test_root` | exit 1 | — |",
                    "| V2 | GREEN | `python3 -m pytest tests/test_root.py` | exit 0 | — |",
                    "| V3 | TIER-B | `ruff check src/core.py tests/test_root.py && mypy --strict src/core.py tests/test_root.py` | exit 0 | — |",
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
            ),
        )
        _commit(repo, "ar03 minimal repo")

        res = _run_contract(repo, "--design", "--hld", str(hld), "--tasks", str(task))
        assert res.returncode == 0, res.stdout + res.stderr
        assert res.stdout.splitlines() == ["Result: 0 problems — PASS"]

    def test_slqr_fr_04_design_fails_closed_on_each_independent_shift_left_violation(
        self, tmp_path: Path
    ) -> None:
        """[SLQR-FR-04] [Tier C - Integration] check_task_contract --design fails closed on each independent Shift-Left violation with distinct guard diagnostics."""
        repo = tmp_path / "fr04_repo"
        _init_repo(repo)
        _write_polyglot_manifests(
            repo,
            python_test_routing={
                "canonical_test_globs": [
                    "tests/unit/**/test_*.py",
                    "tests/integration/test_*.py",
                ],
                "forbidden_test_globs": ["tests/test_*.py", "scripts/test_*.py"],
                "paired_source_globs": ["src/api/**/*.py"],
            },
            web_test_routing={
                "canonical_test_globs": ["tests/js/*.test.mjs", "tests/e2e/"],
                "lcov_unit_test_globs": ["tests/js/*.test.mjs"],
                "cache_bust_extensions": [".js", ".css"],
            },
            web_target_dir="src/static",
        )
        _write(repo, "src/api/__init__.py", "")
        _write(repo, "src/static/app.js", "export function render() { return 'ok'; }\n")
        _write(
            repo,
            "src/static/index.html",
            '<!doctype html><html><head><script src="/static/app.js?v=20261128"></script></head></html>\n',
        )
        _write(
            repo,
            "tests/js/app.test.mjs",
            "import test from 'node:test';\ntest('render', () => {});\n",
        )
        _write(
            repo,
            "tests/e2e/app.spec.js",
            "console.log('e2e');\n",
        )
        hld = _write(repo, ".devtool/epic/demo/demo.md", _hld_text())
        _commit(repo, "fr04 base")

        # (1) Playwright-only Web task touching src/static/app.js without a JS unit test
        t_lcov = _write(
            repo,
            ".devtool/epic/demo/task_01_lcov.md",
            _task_md(
                allowed=["src/static/app.js", "src/static/index.html"],
                rows=[
                    "| V1 | RED | `npx --no-install playwright test tests/e2e/app.spec.js` | exit 1 | PLAYWRIGHT_BROWSER |",
                    "| V2 | GREEN | `npx --no-install playwright test tests/e2e/app.spec.js` | exit 0 | PLAYWRIGHT_BROWSER |",
                    '| V3 | TIER-B | `python3 "$D3NEXUS_KIT/skills/web-quality-check/resources/scripts/check_vanilla_js.py" --target-dir src/static` | exit 0 | — |',
                    "| V4 | TIER-C | `npx --no-install playwright test tests/e2e/app.spec.js # tier: C2` | exit 0; results build/e2e.xml | PLAYWRIGHT_BROWSER |",
                ],
            ),
        )
        r1 = _run_contract(repo, "--design", "--hld", str(hld), "--tasks", str(t_lcov))
        assert r1.returncode == 1, r1.stdout
        assert "LCOV" in r1.stdout
        assert "src/static/app.js" in r1.stdout
        assert "Result: 1 problems — FAIL" in r1.stdout

        # (2) New test placed at forbidden tests/test_rogue.py
        t_forbid = _write(
            repo,
            ".devtool/epic/demo/task_02_forbid.md",
            _task_md(
                allowed=["tests/test_rogue.py (new)"],
                rows=[
                    "| V1 | RED | `python3 -m pytest tests/test_rogue.py::test_rogue` | exit 1 | — |",
                    "| V2 | GREEN | `python3 -m pytest tests/test_rogue.py` | exit 0 | — |",
                    "| V3 | TIER-B | `uv run ruff check --extend-select F821,B904 tests/test_rogue.py && uv run mypy --strict tests/test_rogue.py` | exit 0 | — |",
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
            ),
        )
        r2 = _run_contract(
            repo, "--design", "--hld", str(hld), "--tasks", str(t_forbid)
        )
        assert r2.returncode == 1, r2.stdout
        assert "forbidden_test_globs" in r2.stdout
        assert "tests/test_rogue.py" in r2.stdout
        assert "tests/test_*.py" in r2.stdout
        assert "Result: 1 problems — FAIL" in r2.stdout

        # (3) New src/api/routes.py missing a paired unit test
        t_paired = _write(
            repo,
            ".devtool/epic/demo/task_03_paired.md",
            _task_md(
                allowed=["src/api/routes.py (new)"],
                rows=[
                    "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                    "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                    "| V3 | TIER-B | `uv run ruff check --extend-select F821,B904 src/api/routes.py && uv run mypy --strict src/api/routes.py` | exit 0 | — |",
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
            ),
        )
        r3 = _run_contract(
            repo, "--design", "--hld", str(hld), "--tasks", str(t_paired)
        )
        assert r3.returncode == 1, r3.stdout
        assert "paired_source_globs" in r3.stdout
        assert "src/api/routes.py" in r3.stdout
        assert "Result: 1 problems — FAIL" in r3.stdout

        # (4) Modified src/static/app.js omitting referencing src/static/index.html (?v=)
        t_cache = _write(
            repo,
            ".devtool/epic/demo/task_04_cache.md",
            _task_md(
                allowed=["src/static/app.js", "tests/js/app.test.mjs"],
                rows=[
                    "| V1 | RED | `node --test tests/js/app.test.mjs` | exit 1 | — |",
                    "| V2 | GREEN | `node --test tests/js/app.test.mjs` | exit 0 | — |",
                    '| V3 | TIER-B | `python3 "$D3NEXUS_KIT/skills/web-quality-check/resources/scripts/check_vanilla_js.py" --target-dir src/static` | exit 0 | — |',
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
            ),
        )
        r4 = _run_contract(repo, "--design", "--hld", str(hld), "--tasks", str(t_cache))
        assert r4.returncode == 1, r4.stdout
        assert "cache-bust" in r4.stdout
        assert "src/static/index.html" in r4.stdout
        assert "Result: 1 problems — FAIL" in r4.stdout

        # (5) Unexpanded {skills_dir} in TIER-B
        t_placeholder = _write(
            repo,
            ".devtool/epic/demo/task_05_placeholder.md",
            _task_md(
                allowed=[
                    "src/static/app.js",
                    "src/static/index.html",
                    "tests/js/app.test.mjs",
                ],
                rows=[
                    "| V1 | RED | `node --test tests/js/app.test.mjs` | exit 1 | — |",
                    "| V2 | GREEN | `node --test tests/js/app.test.mjs` | exit 0 | — |",
                    "| V3 | TIER-B | `python3 {skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py --target-dir src/static` | exit 0 | — |",
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
            ),
        )
        r5 = _run_contract(
            repo, "--design", "--hld", str(hld), "--tasks", str(t_placeholder)
        )
        assert r5.returncode == 1, r5.stdout
        assert "unexpanded manifest placeholder '{skills_dir}'" in r5.stdout
        assert "Result: 1 problems — FAIL" in r5.stdout


def test_single_file_python_task_rejects_unrelated_mypy_target(tmp_path: Path) -> None:
    """Single-file Python tasks running `uv run mypy --strict unrelated.py` must fail closed."""
    for label, type_check_cap in (
        ("multi_target", ["uv", "run", "mypy", "--strict", "src", "tests"]),
        ("single_target", ["uv", "run", "mypy", "--strict", "src"]),
    ):
        repo = tmp_path / f"unrelated_{label}"
        _init_repo(repo)
        _write_json(
            repo,
            ".agents/quality/python-quality.json",
            {
                "schema_version": 1,
                "capabilities": {
                    "lint": ["uv", "run", "ruff", "check", "."],
                    "type_check": type_check_cap,
                },
                "profiles": {
                    "pr": ["lint", "type_check"],
                    "epic": ["lint", "type_check"],
                },
            },
        )
        _write(repo, "src/pkg/target.py", "def target() -> int:\n    return 1\n")
        _write(repo, "unrelated.py", "def other() -> int:\n    return 2\n")
        hld = _write(repo, ".devtool/epic/demo/demo.md", _hld_text())
        task = _write(
            repo,
            ".devtool/epic/demo/task_01_single.md",
            _task_md(
                allowed=["src/pkg/target.py"],
                rows=[
                    "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                    "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                    "| V3 | TIER-B | `uv run ruff check src/pkg/target.py && uv run mypy --strict unrelated.py` | exit 0 | — |",
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
            ),
        )
        _commit(repo, f"unrelated {label}")

        res = _run_contract(repo, "--design", "--hld", str(hld), "--tasks", str(task))
        assert res.returncode == 1, f"{label}:\n{res.stdout}"
        assert "missing registered type_check capability" in res.stdout
        assert "missing registered lint capability" not in res.stdout


def test_canonical_test_glob_base_ref_historical_done_and_check_plan_edge_cases(
    tmp_path: Path,
) -> None:
    """Verify canonical_test_globs, {base_ref}, historical done exemption, and --check-plan CLI edges."""
    repo = tmp_path / "edge_cases_repo"
    _init_repo(repo)
    _write_polyglot_manifests(
        repo,
        python_test_routing={
            "canonical_test_globs": ["tests/unit/**/test_*.py"],
            "forbidden_test_globs": ["tests/test_*.py"],
            "paired_source_globs": ["src/api/**/*.py"],
        },
        web_target_dir="src/preview",
    )
    _write(repo, "src/api/__init__.py", "")
    _write(repo, "src/pkg/mod.py", "def mod() -> int:\n    return 1\n")
    _write(repo, "misc/__init__.py", "")
    _write(repo, "src/preview/static/app.js", "export const x = 1;\n")
    _write(
        repo,
        "src/preview/static/index.html",
        '<!doctype html><script src="/app.js?v=1"></script>\n',
    )
    hld = _write(repo, ".devtool/epic/demo/demo.md", _hld_text())
    _commit(repo, "edge base")

    # 1. Outside canonical_test_globs (not matching forbidden_test_globs) + {base_ref}
    t_canon = _write(
        repo,
        ".devtool/epic/demo/task_01_canon.md",
        _task_md(
            allowed=["misc/test_stray.py (new)"],
            rows=[
                "| V1 | RED | `python3 -m pytest misc/test_stray.py::test_x` | exit 1 | — |",
                "| V2 | GREEN | `python3 -m pytest misc/test_stray.py` | exit 0 | — |",
                "| V3 | TIER-B | `uv run ruff check --extend-select F821,B904 misc/test_stray.py && uv run mypy --strict misc/test_stray.py` | exit 0 | — |",
                "| V4 | TIER-C | `python3 tool.py --base-ref {base_ref}` | exit 0; results build/out.xml | — |",
            ],
        ),
    )
    res_canon = _run_contract(
        repo, "--design", "--hld", str(hld), "--tasks", str(t_canon)
    )
    assert res_canon.returncode == 1, res_canon.stdout
    assert "canonical_test_globs" in res_canon.stdout
    assert "unexpanded manifest placeholder '{base_ref}'" in res_canon.stdout

    # 2. Historical done task skips all new Shift-Left guards cleanly
    t_done = _write(
        repo,
        ".devtool/epic/demo/task_02_hist_done.md",
        _task_md(
            allowed=["src/preview/static/app.js"],
            rows=[
                "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                '| V3 | TIER-B | `python3 "$D3NEXUS_KIT/skills/web-quality-check/resources/scripts/check_vanilla_js.py" --target-dir src/preview` | exit 0 | — |',
                "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
            ],
            dod="- [x] Historical done task (V2, V3, V4)\n",
            status="done",
        ),
    )
    res_done = _run_contract(
        repo,
        "--design",
        "--allow-existing-done-new",
        "--hld",
        str(hld),
        "--tasks",
        str(t_done),
    )
    assert res_done.returncode == 0, res_done.stdout + res_done.stderr

    # 3. --check-plan mutual exclusivity & missing file -> exit 2
    res_mutex = _run_contract(
        repo,
        "--check-plan",
        "docs/plan.md",
        "--hld",
        str(hld),
        "--tasks",
        str(t_done),
    )
    assert res_mutex.returncode == 2
    assert "--check-plan" in res_mutex.stderr

    res_missing = _run_contract(repo, "--check-plan", "docs/nonexistent_plan.md")
    assert res_missing.returncode == 2
    assert "nonexistent_plan.md" in res_missing.stderr

    # 4. --check-plan with 0 task sections -> exit 1
    empty_plan = _write(repo, "docs/empty_plan.md", "# Just prose\n\nNo tasks here.\n")
    res_empty = _run_contract(repo, "--check-plan", str(empty_plan))
    assert res_empty.returncode == 1
    assert "no '### Task N' sections" in res_empty.stdout

    # 5. --check-plan multi-task: intermediate full-repo Python + missing paired test + missing lint/type_check
    multi_bad_plan = _write(
        repo,
        "docs/multi_bad_plan.md",
        "# Multi Plan\n\n"
        "### Task 1: Create API route\n\n"
        "- Create: `src/api/routes.py`\n"
        "Run: `uv run mypy --strict src tests`\n\n"
        "### Task 2: Final task\n\n"
        "- Modify: `src/pkg/mod.py`\n"
        "Run: `uv run mypy --strict src tests`\n",
    )
    res_multi = _run_contract(repo, "--check-plan", str(multi_bad_plan))
    assert res_multi.returncode == 1, res_multi.stdout
    assert "intermediate task" in res_multi.stdout
    assert "paired_source_globs" in res_multi.stdout
    assert "missing registered lint capability" in res_multi.stdout


def test_cap_tool_prefix_wrappers_flags_and_explicit_manifest_non_false_positive(
    tmp_path: Path,
) -> None:
    """Verify _cap_tool_prefix handles monorepo wrappers, value flags, and explicit-path manifests."""
    import check_task_contract as ctc

    assert ctc._cap_tool_prefix(
        [
            "uv",
            "--directory",
            "apps/worker",
            "run",
            "ruff",
            "check",
            "--extend-select",
            "F821,B904",
            "--per-file-ignores",
            "tests/*:S101",
            "--line-length",
            "100",
            "--target-version",
            "py312",
            ".",
        ]
    ) == [
        "uv",
        "--directory",
        "apps/worker",
        "run",
        "ruff",
        "check",
        "--extend-select",
        "F821,B904",
        "--per-file-ignores",
        "tests/*:S101",
        "--line-length",
        "100",
        "--target-version",
        "py312",
    ]
    assert ctc._cap_tool_prefix(
        [
            "python3",
            "-m",
            "mypy",
            "--config-file",
            "mypy.ini",
            "--python-version",
            "3.12",
            "--strict",
            "src",
            "tests",
        ]
    ) == [
        "python3",
        "-m",
        "mypy",
        "--config-file",
        "mypy.ini",
        "--python-version",
        "3.12",
        "--strict",
    ]

    # Explicit-path python-quality.json (like ai-agent-tools) must never false-flag intermediate tasks
    repo = tmp_path / "explicit_manifest_repo"
    _init_repo(repo)
    _write_json(
        repo,
        ".agents/quality/python-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "lint": ["ruff", "check", "scripts/a.py", "tests"],
                "type_check": [
                    "mypy",
                    "scripts/a.py",
                    "--ignore-missing-imports",
                    "--follow-imports=silent",
                ],
            },
            "profiles": {"pr": ["lint", "type_check"], "epic": ["lint", "type_check"]},
        },
    )
    _write(repo, "scripts/a.py", "def a() -> int:\n    return 1\n")
    _write(repo, "scripts/b.py", "def b() -> int:\n    return 2\n")
    hld = _write(repo, ".devtool/epic/demo/demo.md", _hld_text())
    t1 = _write(
        repo,
        ".devtool/epic/demo/task_01_explicit.md",
        _task_md(
            allowed=["scripts/a.py"],
            rows=[
                "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                "| V3 | TIER-B | `ruff check scripts/a.py tests && mypy scripts/a.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |",
                "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
            ],
            order="a01",
        ),
    )
    t2 = _write(
        repo,
        ".devtool/epic/demo/task_02_explicit.md",
        _task_md(
            allowed=["scripts/b.py"],
            rows=[
                "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                "| V3 | TIER-B | `ruff check scripts/a.py tests scripts/b.py && mypy scripts/a.py scripts/b.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |",
                "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
            ],
            order="a02",
        ),
    )
    _commit(repo, "explicit paths")
    res = _run_contract(
        repo, "--design", "--hld", str(hld), "--tasks", str(t1), str(t2)
    )
    assert res.returncode == 0, res.stdout + res.stderr

    # Verify npx --yes --package is allowed while npx -y <bin> without --package is rejected
    plan_npx = _write(
        repo,
        "docs/npx_plan.md",
        "# NPX Plan\n\n"
        "### Task 1: Run tools\n\n"
        "- Modify: `README.md`\n"
        "Run: `npx --yes --package cowsay cowsay hi`\n"
        "Run: `npx -y playwright test`\n",
    )
    res_npx = _run_contract(repo, "--check-plan", str(plan_npx))
    assert res_npx.returncode == 1, res_npx.stdout
    assert "bare 'npx'" in res_npx.stdout
    assert "Result: 1 problems — FAIL" in res_npx.stdout
