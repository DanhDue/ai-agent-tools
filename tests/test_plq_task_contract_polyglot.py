"""Integration and unit tests for Task 04: Polyglot Task Contract, Tier C2 Gate, and Compact Output.

Covers BDD Scenarios:
- PLQ-HP-04: Polyglot task contract passes when all touched stacks satisfy Tier B and emits one-line PASS
- PLQ-EC-06: Python tasks retain check_python_tier_b enforcement without python-quality.json or with only non-Python manifests
- PLQ-ST-02: TierCTaxonomy distinguishes explicit Tier C2 missing Needs from heuristic heavy-runtime warning
- PLQ-AR-03: Conditional boundary checks activate only when domain or manifest boundary files change
- PLQ-FR-04: Invalid HLD Integration test roots with path traversal or missing targets fail check_task_contract
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

ISOLATED_GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "PLQ Tester",
    "GIT_AUTHOR_EMAIL": "plq@example.com",
    "GIT_COMMITTER_NAME": "PLQ Tester",
    "GIT_COMMITTER_EMAIL": "plq@example.com",
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


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "plq@example.com")
    _git(repo, "config", "user.name", "PLQ Tester")
    _write(repo, ".gitignore", "build/\n")
    _write(repo, "README.md", "# Demo Repo\n")
    _write(repo, "tool.py", "print('ok')\n")
    _write(repo, "tests/test_smoke.py", "def test_smoke() -> None:\n    assert True\n")


def _commit(repo: Path, msg: str = "commit") -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)


def _write(repo: Path, rel: str, content: str) -> Path:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_json(repo: Path, rel: str, payload: dict[str, Any]) -> Path:
    return _write(repo, rel, json.dumps(payload, indent=2) + "\n")


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
    integration_roots: str | None = "tests",
    env_body: str = "Runs in temporary directories. Variables: PLAYWRIGHT_BROWSER, FLUTTER_DEVICE.",
) -> str:
    roots_line = (
        f"Integration test roots: {integration_roots}\n\n"
        if integration_roots is not None
        else ""
    )
    return (
        "# Demo Epic\n\n"
        "## Integration Test Plan\n\n"
        f"{roots_line}"
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
) -> str:
    allowed_block = "\n".join(_format_allowed_entry(item) for item in allowed)
    rows_block = "\n".join(rows) + "\n"
    return (
        f'---\nstatus: "{status}"\n---\n'
        "# Task\n\n"
        "## Files\n\n"
        f"Allowed files:\n{allowed_block}\n\n"
        "Read-only context:\n- `README.md` — repo note\n\n"
        f"## Verification\n\n{TABLE_HEADER}{rows_block}\n"
        f"## Definition of Done\n\n{dod}\n"
        "## Stop and Report If\n\n- Contract mismatch.\n\n"
        "## Decisions Already Made\n\n- Grounded polyglot verification decision.\n"
    )


def _write_manifest(repo: Path, stack: str) -> None:
    manifests: dict[str, dict[str, Any]] = {
        "rust": {
            "schema_version": 1,
            "capabilities": {
                "format": ["cargo", "fmt", "--all", "--", "--check"],
                "clippy": ["cargo", "clippy", "--all-targets", "--", "-D", "warnings"],
                "architecture": ["cargo", "xtask", "check-arch"],
                "test": ["cargo", "test"],
            },
            "profiles": {
                "pr": ["format", "clippy", "test"],
                "epic": ["format", "clippy", "architecture", "test"],
            },
        },
        "web": {
            "schema_version": 1,
            "capabilities": {
                "lint": ["eslint", "."],
                "type_check": ["tsc", "--noEmit"],
                "test": ["npx", "--no-install", "vitest", "run"],
            },
            "profiles": {
                "pr": ["lint", "type_check", "test"],
                "epic": ["lint", "type_check", "test"],
            },
        },
        "flutter": {
            "schema_version": 1,
            "capabilities": {
                "format": [
                    "dart",
                    "format",
                    "--output=none",
                    "--set-exit-if-changed",
                    ".",
                ],
                "analyze": ["dart", "analyze"],
                "boundaries": ["melos", "run", "boundaries"],
                "test": ["flutter", "test"],
            },
            "profiles": {
                "pr": ["format", "analyze", "test"],
                "epic": ["format", "analyze", "boundaries", "test"],
            },
        },
        "android": {
            "schema_version": 1,
            "capabilities": {
                "format": ["./gradlew", "spotlessCheck"],
                "lint": ["./gradlew", "detekt"],
                "architecture": ["./gradlew", ":konsist-test:test"],
                "test": ["./gradlew", "testDebugUnitTest"],
            },
            "profiles": {
                "pr": ["format", "lint", "test"],
                "epic": ["format", "lint", "architecture", "test"],
            },
        },
        "ios": {
            "schema_version": 1,
            "capabilities": {
                "format": ["swiftformat", "--lint", "."],
                "lint": ["swiftlint", "lint", "--strict"],
                "architecture": ["swift", "test", "--filter", "ArchTests"],
                "test": ["swift", "test"],
            },
            "profiles": {
                "pr": ["format", "lint", "test"],
                "epic": ["format", "lint", "architecture", "test"],
            },
        },
    }
    _write_json(repo, f".agents/quality/{stack}-quality.json", manifests[stack])


def test_plq_hp_04_polyglot_task_passes_with_one_line_pass(tmp_path: Path) -> None:
    """[PLQ-HP-04] [Tier C - Integration] Polyglot task contract passes when all touched stacks satisfy Tier B and emits one-line PASS."""
    repo = tmp_path / "polyglot_repo"
    _init_repo(repo)
    _write_manifest(repo, "rust")
    _write_manifest(repo, "web")
    _write(repo, "crates/core/src/lib.rs", "pub fn answer() -> i32 { 42 }\n")
    _write(repo, "apps/web/src/app.ts", "export const answer: number = 42;\n")

    hld = _write(repo, ".devtool/epic/demo/demo.md", _hld_text())
    task = _write(
        repo,
        ".devtool/epic/demo/task_01_poly.md",
        _task_md(
            allowed=["crates/core/src/lib.rs", "apps/web/src/app.ts"],
            rows=[
                "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                "| V3 | TIER-B | `cargo fmt --check && cargo clippy --all-targets -- -D warnings && eslint apps/web/src/app.ts && tsc --noEmit` | exit 0 | — |",
                "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
            ],
        ),
    )
    _commit(repo, "polyglot base")

    # Default PASS stdout is strictly 1 line: "Result: 0 problems — PASS"
    default_res = _run_contract(
        repo, "--design", "--hld", str(hld), "--tasks", str(task)
    )
    assert default_res.returncode == 0, default_res.stdout + default_res.stderr
    assert default_res.stdout.splitlines() == ["Result: 0 problems — PASS"], (
        f"Expected single-line PASS stdout, got:\n{default_res.stdout!r}"
    )

    # --verbose prints "Implicit protected paths:" before the Result line
    verbose_res = _run_contract(
        repo, "--design", "--verbose", "--hld", str(hld), "--tasks", str(task)
    )
    assert verbose_res.returncode == 0, verbose_res.stdout + verbose_res.stderr
    verbose_lines = verbose_res.stdout.splitlines()
    assert len(verbose_lines) == 2, verbose_lines
    assert verbose_lines[0].startswith("Implicit protected paths: tool.py"), (
        verbose_lines
    )
    assert verbose_lines[1] == "Result: 0 problems — PASS"

    # --json emits structured payload
    json_res = _run_contract(
        repo, "--design", "--json", "--hld", str(hld), "--tasks", str(task)
    )
    assert json_res.returncode == 0, json_res.stdout + json_res.stderr
    payload = json.loads(json_res.stdout)
    assert payload["status"] == "PASS"
    assert payload["problems"] == []
    assert isinstance(payload["warnings"], list)
    assert any(p.startswith("tool.py (") for p in payload["implicit_protected_paths"])

    # Negative check: dropping eslint and tsc fails with both web problems + implicit paths + FAIL
    bad_task = _write(
        repo,
        ".devtool/epic/demo/task_01_poly.md",
        _task_md(
            allowed=["crates/core/src/lib.rs", "apps/web/src/app.ts"],
            rows=[
                "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                "| V3 | TIER-B | `cargo fmt --check && cargo clippy --all-targets -- -D warnings` | exit 0 | — |",
                "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
            ],
        ),
    )
    _commit(repo, "drop web tier-b")

    fail_res = _run_contract(
        repo, "--design", "--hld", str(hld), "--tasks", str(bad_task)
    )
    assert fail_res.returncode == 1, fail_res.stdout
    assert "web task missing TIER-B lint check" in fail_res.stdout
    assert "web task missing TIER-B type-check" in fail_res.stdout
    assert "Implicit protected paths: tool.py" in fail_res.stdout
    assert "Result: 2 problems — FAIL" in fail_res.stdout

    fail_json_res = _run_contract(
        repo, "--design", "--json", "--hld", str(hld), "--tasks", str(bad_task)
    )
    assert fail_json_res.returncode == 1
    fail_payload = json.loads(fail_json_res.stdout)
    assert fail_payload["status"] == "FAIL"
    assert len(fail_payload["problems"]) == 2


class TestPLQTaskContractPolyglot_Integration:
    """Tier C integration suite covering PLQ-HP-04, PLQ-EC-06, PLQ-ST-02, PLQ-AR-03, PLQ-FR-04."""

    def test_plq_hp_04_mixed_python_web_untouched_flutter_and_custom_stack(
        self, tmp_path: Path
    ) -> None:
        """[PLQ-HP-04] Python + non-Python tasks dispatch both adapters independently while skipping untouched stacks and honoring custom extensions."""
        repo = tmp_path / "mixed_repo"
        _init_repo(repo)
        _write_manifest(repo, "web")
        _write_manifest(repo, "flutter")
        _write_json(
            repo,
            ".agents/quality/go-quality.json",
            {
                "schema_version": 1,
                "extensions": [".go"],
                "task_tier_b": {"format_prefixes": ["gofmt -l"]},
            },
        )
        _write(repo, "src/service.py", "def run() -> int:\n    return 1\n")
        _write(repo, "apps/web/src/ui.ts", "export const ok = true;\n")
        _write(repo, "cmd/worker/main.go", "package main\nfunc main() {}\n")

        hld = _write(repo, ".devtool/epic/demo/demo.md", _hld_text())
        task = _write(
            repo,
            ".devtool/epic/demo/task_01_mixed.md",
            _task_md(
                allowed=[
                    "src/service.py",
                    "apps/web/src/ui.ts",
                    "cmd/worker/main.go",
                ],
                rows=[
                    "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                    "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                    "| V3 | TIER-B | `ruff check src/service.py && mypy src/service.py && eslint apps/web/src/ui.ts && tsc --noEmit && gofmt -l cmd/worker/main.go` | exit 0 | — |",
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
            ),
        )
        _commit(repo, "mixed repo base")

        ok = _run_contract(repo, "--design", "--hld", str(hld), "--tasks", str(task))
        assert ok.returncode == 0, ok.stdout + ok.stderr
        assert ok.stdout.splitlines() == ["Result: 0 problems — PASS"]
        assert "flutter" not in ok.stdout.lower()

        # Removing custom stack gofmt fails only go stack
        bad_go = _write(
            repo,
            ".devtool/epic/demo/task_01_mixed.md",
            _task_md(
                allowed=[
                    "src/service.py",
                    "apps/web/src/ui.ts",
                    "cmd/worker/main.go",
                ],
                rows=[
                    "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                    "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                    "| V3 | TIER-B | `ruff check src/service.py && mypy src/service.py && eslint apps/web/src/ui.ts && tsc --noEmit` | exit 0 | — |",
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
            ),
        )
        _commit(repo, "omit gofmt")
        fail = _run_contract(
            repo, "--design", "--hld", str(hld), "--tasks", str(bad_go)
        )
        assert fail.returncode == 1
        assert "go task missing TIER-B format check" in fail.stdout
        assert "flutter" not in fail.stdout.lower()

    def test_plq_ec_06_python_tier_b_enforced_without_python_manifest_or_with_flutter_only(
        self, tmp_path: Path
    ) -> None:
        """[PLQ-EC-06] Python tasks retain check_python_tier_b enforcement without python-quality.json or with only non-Python manifests."""
        for name, with_flutter in (
            ("no_quality_dir", False),
            ("flutter_manifest_only", True),
        ):
            repo = tmp_path / name
            _init_repo(repo)
            if with_flutter:
                _write_manifest(repo, "flutter")
            _write(
                repo,
                "src/app.py",
                "def add(a: int, b: int) -> int:\n    return a + b\n",
            )

            hld = _write(repo, ".devtool/epic/demo/demo.md", _hld_text())
            missing_mypy = _write(
                repo,
                ".devtool/epic/demo/task_01_py.md",
                _task_md(
                    allowed=["src/app.py"],
                    rows=[
                        "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                        "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                        "| V3 | TIER-B | `ruff check src/app.py` | exit 0 | — |",
                        "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                    ],
                ),
            )
            _commit(repo, f"{name} missing mypy")

            res_fail = _run_contract(
                repo, "--design", "--hld", str(hld), "--tasks", str(missing_mypy)
            )
            assert res_fail.returncode == 1, f"{name}:\n{res_fail.stdout}"
            assert "type-check (mypy/pyright/ty)" in res_fail.stdout
            assert "flutter" not in res_fail.stdout.lower()

            # Adding mypy row makes both repos pass cleanly with 1-line PASS
            fixed_task = _write(
                repo,
                ".devtool/epic/demo/task_01_py.md",
                _task_md(
                    allowed=["src/app.py"],
                    rows=[
                        "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                        "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                        "| V3 | TIER-B | `ruff check src/app.py && mypy src/app.py` | exit 0 | — |",
                        "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                    ],
                ),
            )
            _commit(repo, f"{name} fixed")
            res_ok = _run_contract(
                repo, "--design", "--hld", str(hld), "--tasks", str(fixed_task)
            )
            assert res_ok.returncode == 0, f"{name}:\n{res_ok.stdout}\n{res_ok.stderr}"
            assert res_ok.stdout.splitlines() == ["Result: 0 problems — PASS"]

    def test_plq_st_02_tier_c_taxonomy_explicit_c2_and_heuristic_warning(
        self, tmp_path: Path
    ) -> None:
        """[PLQ-ST-02] TierCTaxonomy distinguishes explicit Tier C2 missing Needs from heuristic heavy-runtime warning."""
        repo = tmp_path / "tier_c_repo"
        _init_repo(repo)
        _write_manifest(repo, "web")
        _write(repo, "apps/web/src/page.ts", "export const title = 'ok';\n")
        hld = _write(repo, ".devtool/epic/demo/demo.md", _hld_text())

        # 1. Explicit `# tier: C2` with empty Needs ("—") -> hard FAIL (exit 1)
        explicit_ungated = _write(
            repo,
            ".devtool/epic/demo/task_01_c2_ungated.md",
            _task_md(
                allowed=["apps/web/src/page.ts"],
                rows=[
                    "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                    "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                    "| V3 | TIER-B | `eslint apps/web/src/page.ts && tsc --noEmit` | exit 0 | — |",
                    "| V4 | TIER-C | `npx --no-install playwright test # tier: C2` | exit 0; results build/e2e.xml | — |",
                ],
            ),
        )
        # 2. Unlabeled heavy runtime (`npx --no-install playwright test`) with empty Needs ("—") -> PASS + warning on stderr
        heuristic_ungated = _write(
            repo,
            ".devtool/epic/demo/task_02_playwright_warn.md",
            _task_md(
                allowed=["apps/web/src/page.ts"],
                rows=[
                    "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                    "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                    "| V3 | TIER-B | `eslint apps/web/src/page.ts && tsc --noEmit` | exit 0 | — |",
                    "| V4 | TIER-C | `npx --no-install playwright test` | exit 0; results build/e2e.xml | — |",
                ],
            ),
        )
        # 3. Explicit `# tier: C2` WITH Needs variable declared in Verification Environment -> PASS
        explicit_gated = _write(
            repo,
            ".devtool/epic/demo/task_03_c2_gated.md",
            _task_md(
                allowed=["apps/web/src/page.ts"],
                rows=[
                    "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                    "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                    "| V3 | TIER-B | `eslint apps/web/src/page.ts && tsc --noEmit` | exit 0 | — |",
                    "| V4 | TIER-C | `npx --no-install playwright test # Tier: c2` | exit 0; results build/e2e.xml | PLAYWRIGHT_BROWSER |",
                ],
            ),
        )
        _commit(repo, "tier c tasks")

        res1 = _run_contract(
            repo, "--design", "--hld", str(hld), "--tasks", str(explicit_ungated)
        )
        assert res1.returncode == 1, res1.stdout
        assert "Explicit Tier C2 row V4" in res1.stdout
        assert "Needs" in res1.stdout

        res2 = _run_contract(
            repo, "--design", "--hld", str(hld), "--tasks", str(heuristic_ungated)
        )
        assert res2.returncode == 0, res2.stdout + res2.stderr
        assert res2.stdout.splitlines() == ["Result: 0 problems — PASS"]
        assert "Tier C2" in res2.stderr
        assert "PLAYWRIGHT_BROWSER" in res2.stderr

        res2_json = _run_contract(
            repo,
            "--design",
            "--json",
            "--hld",
            str(hld),
            "--tasks",
            str(heuristic_ungated),
        )
        assert res2_json.returncode == 0
        j2 = json.loads(res2_json.stdout)
        assert j2["status"] == "PASS"
        assert any("PLAYWRIGHT_BROWSER" in w for w in j2["warnings"])

        res3 = _run_contract(
            repo, "--design", "--hld", str(hld), "--tasks", str(explicit_gated)
        )
        assert res3.returncode == 0, res3.stdout + res3.stderr
        assert res3.stdout.splitlines() == ["Result: 0 problems — PASS"]

    def test_plq_ar_03_conditional_boundary_checks_activate_only_for_boundary_files(
        self, tmp_path: Path
    ) -> None:
        """[PLQ-AR-03] Conditional boundary checks activate only when domain or manifest boundary files change."""
        cases = [
            (
                "flutter",
                "packages/core/lib/domain/entity.dart",
                "class Entity {}\n",
                "packages/core/lib/ui/button.dart",
                "class Button {}\n",
                "dart format --output=none --set-exit-if-changed packages/core/lib/domain/entity.dart && dart analyze",
                "dart format --output=none --set-exit-if-changed packages/core/lib/ui/button.dart && dart analyze",
                "melos run boundaries",
            ),
            (
                "rust",
                "crates/domain/Cargo.toml",
                "[package]\nname = 'domain'\n",
                "crates/app/src/main.rs",
                "fn main() {}\n",
                "cargo fmt --check && cargo clippy --all-targets -- -D warnings",
                "cargo fmt --check && cargo clippy --all-targets -- -D warnings",
                "cargo xtask check-arch",
            ),
            (
                "android",
                "feature/wallet/domain/UseCase.kt",
                "class UseCase\n",
                "feature/wallet/ui/Screen.kt",
                "class Screen\n",
                "gradle spotlessCheck detekt",
                "gradle spotlessCheck detekt",
                "gradle :konsist-test:test",
            ),
            (
                "ios",
                "Packages/Core/Package.swift",
                "// swift-tools-version: 5.9\n",
                "Packages/Core/Sources/View.swift",
                "struct View {}\n",
                "swiftformat --lint . && swiftlint lint --strict",
                "swiftformat --lint . && swiftlint lint --strict",
                "swift test --filter ArchTests",
            ),
        ]

        for (
            stack,
            boundary_file,
            boundary_src,
            non_boundary_file,
            non_boundary_src,
            base_tier_b_boundary,
            base_tier_b_ui,
            boundary_cmd,
        ) in cases:
            # Isolated repo per stack (all 4 manifests active) avoids case-insensitive
            # filesystem collisions between `packages/core` and `Packages/Core`.
            repo = tmp_path / f"boundary_repo_{stack}"
            _init_repo(repo)
            for manifest_stack in ("flutter", "rust", "android", "ios"):
                _write_manifest(repo, manifest_stack)
            _write(repo, boundary_file, boundary_src)
            _write(repo, non_boundary_file, non_boundary_src)
            hld = _write(repo, ".devtool/epic/demo/demo.md", _hld_text())
            _commit(repo, f"{stack} boundary base files")

            # 1. Boundary file WITHOUT boundary check -> FAIL
            missing_boundary = _write(
                repo,
                f".devtool/epic/demo/task_{stack}_miss.md",
                _task_md(
                    allowed=[boundary_file],
                    rows=[
                        "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                        "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                        f"| V3 | TIER-B | `{base_tier_b_boundary}` | exit 0 | — |",
                        "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                    ],
                ),
            )
            res_fail = _run_contract(
                repo, "--design", "--hld", str(hld), "--tasks", str(missing_boundary)
            )
            assert res_fail.returncode == 1, (
                f"{stack} missing boundary:\n{res_fail.stdout}"
            )
            assert f"{stack} task touches boundary files" in res_fail.stdout
            assert boundary_file in res_fail.stdout

            # 2. Boundary file WITH boundary check -> PASS
            with_boundary = _write(
                repo,
                f".devtool/epic/demo/task_{stack}_with.md",
                _task_md(
                    allowed=[boundary_file],
                    rows=[
                        "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                        "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                        f"| V3 | TIER-B | `{base_tier_b_boundary} && {boundary_cmd}` | exit 0 | — |",
                        "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                    ],
                ),
            )
            res_with = _run_contract(
                repo, "--design", "--hld", str(hld), "--tasks", str(with_boundary)
            )
            assert res_with.returncode == 0, (
                f"{stack} with boundary:\n{res_with.stdout}\n{res_with.stderr}"
            )
            assert res_with.stdout.splitlines() == ["Result: 0 problems — PASS"]

            # 3. Non-domain presentation/utility file WITHOUT boundary check -> PASS
            ui_task = _write(
                repo,
                f".devtool/epic/demo/task_{stack}_ui.md",
                _task_md(
                    allowed=[non_boundary_file],
                    rows=[
                        "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                        "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                        f"| V3 | TIER-B | `{base_tier_b_ui}` | exit 0 | — |",
                        "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                    ],
                ),
            )
            res_ui = _run_contract(
                repo, "--design", "--hld", str(hld), "--tasks", str(ui_task)
            )
            assert res_ui.returncode == 0, (
                f"{stack} non-boundary:\n{res_ui.stdout}\n{res_ui.stderr}"
            )
            assert res_ui.stdout.splitlines() == ["Result: 0 problems — PASS"]

    def test_plq_fr_04_invalid_hld_integration_test_roots_fail_and_valid_roots_pass(
        self, tmp_path: Path
    ) -> None:
        """[PLQ-FR-04] Invalid HLD Integration test roots with path traversal or missing targets fail check_task_contract."""
        import task_contract as tc

        # Unit coverage of parse_integration_test_roots (ignoring fenced examples and stripping backticks)
        sample_hld = (
            "# Demo\n\n"
            "```markdown\nIntegration test roots: fenced/ignored/\n```\n\n"
            "Integration test roots: `tests`, `apps/web/tests/`\n"
        )
        assert tc.parse_integration_test_roots(sample_hld) == [
            "tests",
            "apps/web/tests/",
        ]
        assert tc.parse_integration_test_roots("# No roots here\n") == []

        repo = tmp_path / "roots_repo"
        _init_repo(repo)
        bad_hld = _write(
            repo,
            ".devtool/epic/demo/demo.md",
            _hld_text(integration_roots="../escape, nonexistent_dir/"),
        )
        task = _write(
            repo,
            ".devtool/epic/demo/task_01_roots.md",
            _task_md(
                allowed=["tool.py"],
                rows=[
                    "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                    "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                    "| V3 | TIER-B | `ruff check tool.py && mypy tool.py` | exit 0 | — |",
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
            ),
        )
        _commit(repo, "invalid roots base")

        res_bad = _run_contract(
            repo, "--design", "--hld", str(bad_hld), "--tasks", str(task)
        )
        assert res_bad.returncode == 1, res_bad.stdout
        assert "../escape" in res_bad.stdout
        assert "path traversal" in res_bad.stdout
        assert "nonexistent_dir/" in res_bad.stdout
        assert "matches no tracked or planned (new) files" in res_bad.stdout

        # Valid bare directory root ("tests") + planned (new) root ("integration_new") + glob ("tests/test_*.py") pass
        good_hld = _write(
            repo,
            ".devtool/epic/demo/demo.md",
            _hld_text(integration_roots="tests, integration_new, tests/test_*.py"),
        )
        (repo / "integration_new").mkdir(exist_ok=True)
        task_with_new = _write(
            repo,
            ".devtool/epic/demo/task_01_roots.md",
            _task_md(
                allowed=["tool.py", "integration_new/test_flow.py (new)"],
                rows=[
                    "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
                    "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                    "| V3 | TIER-B | `ruff check tool.py integration_new/test_flow.py && mypy tool.py integration_new/test_flow.py` | exit 0 | — |",
                    "| V4 | TIER-C | `python3 tool.py int` | exit 0; results build/out.xml | — |",
                ],
            ),
        )
        _commit(repo, "valid roots")

        res_good = _run_contract(
            repo, "--design", "--hld", str(good_hld), "--tasks", str(task_with_new)
        )
        assert res_good.returncode == 0, res_good.stdout + res_good.stderr
        assert res_good.stdout.splitlines() == ["Result: 0 problems — PASS"]
