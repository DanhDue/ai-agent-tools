"""Tests for Task 02: Gate 4 receipt hygiene, diff-coverage package floors, and scaffolder deduplication."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VERIFY_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "quality_check"
    / "resources"
    / "scripts"
    / "verify_polyglot_registry.py"
)
DIFF_COV_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "quality_check"
    / "resources"
    / "scripts"
    / "check_diff_coverage.py"
)
SCAFFOLD_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "setup_quality_check"
    / "resources"
    / "scripts"
    / "scaffold_quality_manifest.py"
)
WEB_TEMPLATE_PATH = (
    REPO_ROOT
    / "skills"
    / "setup_quality_check"
    / "resources"
    / "templates"
    / "web-quality.template.json"
)
INTEGRATE_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "finishing-a-development-branch"
    / "resources"
    / "scripts"
    / "integrate_branch.py"
)

ALL_STACKS: tuple[str, ...] = ("flutter", "android", "ios", "rust", "python", "web")


def _load_script_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _run_py(
    script: Path,
    args: list[str],
    *,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _init_git_repo(repo: Path) -> None:
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "slqr@example.com")
    _git(repo, "config", "user.name", "SLQR Test")


def _make_lcov_record(rel_path: str, covered: int, total: int) -> str:
    da_lines = [f"DA:{i},{1 if i <= covered else 0}" for i in range(1, total + 1)]
    return "\n".join(
        [
            "TN:",
            f"SF:{rel_path}",
            *da_lines,
            f"LF:{total}",
            f"LH:{covered}",
            "end_of_record",
            "",
        ]
    )


def _make_cobertura_xml(files: list[tuple[str, int, int]]) -> str:
    classes: list[str] = []
    for rel_path, covered, total in files:
        lines_xml = "\n".join(
            f'          <line number="{i}" hits="{1 if i <= covered else 0}"/>'
            for i in range(1, total + 1)
        )
        classes.append(
            f'        <class name="{Path(rel_path).name}" filename="{rel_path}">\n'
            f"          <lines>\n{lines_xml}\n          </lines>\n"
            "        </class>"
        )
    joined = "\n".join(classes)
    return (
        '<?xml version="1.0" ?>\n'
        '<coverage version="7.6">\n'
        "  <packages>\n"
        '    <package name="pkg">\n'
        "      <classes>\n"
        f"{joined}\n"
        "      </classes>\n"
        "    </package>\n"
        "  </packages>\n"
        "</coverage>\n"
    )


def _init_gate4_repo(repo: Path) -> tuple[Path, Path]:
    """Create a minimal git repo with a controllable Python provider for Gate 4 tests."""
    repo.mkdir(parents=True, exist_ok=True)
    _init_git_repo(repo)

    (repo / "arch_check.py").write_text("print('arch ok')\n", encoding="utf-8")
    (repo / "check_runner.py").write_text(
        "import os, sys\n"
        "code = int(os.environ.get('SLQR_CHECK_EXIT', '0'))\n"
        "print(f'check exit={code}')\n"
        "sys.exit(code)\n",
        encoding="utf-8",
    )
    agents_dir = repo / ".agents" / "quality"
    agents_dir.mkdir(parents=True, exist_ok=True)
    registry = {
        "schema_version": 1,
        "providers": [
            {
                "id": "python-core",
                "skill": "d3nexus:python-quality-check",
                "required": True,
                "profiles": ["pr", "epic", "scheduled", "release"],
            }
        ],
    }
    py_manifest = {
        "schema_version": 1,
        "capabilities": {
            "architecture": [sys.executable, "arch_check.py"],
            "test": [sys.executable, "check_runner.py"],
        },
        "profiles": {
            "pr": ["test"],
            "epic": ["architecture", "test"],
            "scheduled": ["architecture", "test"],
            "release": ["architecture", "test"],
        },
    }
    reg_file = agents_dir / "check_quality.json"
    reg_file.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    (agents_dir / "python-quality.json").write_text(
        json.dumps(py_manifest, indent=2) + "\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Init gate4 fixture")
    return repo, reg_file


def _run_gate4(
    repo: Path,
    reg_file: Path,
    *,
    profile: str,
    check_exit: int,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["SLQR_CHECK_EXIT"] = str(check_exit)
    return subprocess.run(
        [
            sys.executable,
            str(VERIFY_SCRIPT),
            str(reg_file),
            "--profile",
            profile,
            "--execute",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="module")
def scaffolded_all_stacks(
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, dict[str, Any]]:
    """Scaffold all 6 stacks once into a shared read-only temp repo."""
    repo = tmp_path_factory.mktemp("slqr_polyglot_scaffold")
    (repo / "pubspec.yaml").write_text("name: sample_flutter\n", encoding="utf-8")
    (repo / "build.gradle.kts").write_text("// android\n", encoding="utf-8")
    (repo / "Project.swift").write_text("// ios\n", encoding="utf-8")
    (repo / "Cargo.toml").write_text('[package]\nname = "sample"\n', encoding="utf-8")
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "sample"\n', encoding="utf-8"
    )
    (repo / "package.json").write_text('{"name": "sample-web"}\n', encoding="utf-8")

    proc = _run_py(SCAFFOLD_SCRIPT, ["--root", str(repo)], cwd=repo)
    assert proc.returncode == 0, f"Scaffolder failed: {proc.stdout}\n{proc.stderr}"

    manifests: dict[str, dict[str, Any]] = {}
    for stack in ALL_STACKS:
        manifest_path = repo / ".agents" / "quality" / f"{stack}-quality.json"
        assert manifest_path.is_file(), f"Missing scaffolded manifest for {stack}"
        manifests[stack] = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifests["web_template"] = json.loads(
        WEB_TEMPLATE_PATH.read_text(encoding="utf-8")
    )
    return manifests


def test_slqr_st_01_non_passing_epic_or_release_unlinks_stale_gate4_receipt(
    tmp_path: Path,
) -> None:
    """[SLQR-ST-01] [Tier C - Integration] Non-passing epic or release quality run unlinks stale gate4_receipt.json while pr run preserves isolation."""
    repo, reg_file = _init_gate4_repo(tmp_path / "gate4_receipt_repo")
    receipt = repo / "build" / "quality" / "gate4_receipt.json"

    # 1. Passing epic run writes gate4_receipt.json with status PASS.
    pass_proc = _run_gate4(repo, reg_file, profile="epic", check_exit=0)
    assert pass_proc.returncode == 0, pass_proc.stdout
    assert receipt.is_file(), "Expected gate4_receipt.json after passing epic run"
    assert json.loads(receipt.read_text(encoding="utf-8"))["status"] == "PASS"
    original_receipt_text = receipt.read_text(encoding="utf-8")

    # 2. Failing pr and scheduled runs must preserve existing gate4_receipt.json untouched.
    for isolated_profile in ("pr", "scheduled"):
        iso_proc = _run_gate4(repo, reg_file, profile=isolated_profile, check_exit=1)
        assert iso_proc.returncode == 1
        assert receipt.is_file(), (
            f"{isolated_profile} run must not unlink gate4_receipt.json"
        )
        assert receipt.read_text(encoding="utf-8") == original_receipt_text

    # 3. Failing epic run must immediately unlink stale gate4_receipt.json.
    fail_epic = _run_gate4(repo, reg_file, profile="epic", check_exit=1)
    assert fail_epic.returncode == 1
    assert json.loads(fail_epic.stdout)["status"] == "FAIL"
    assert not receipt.exists(), "Stale gate4_receipt.json survived failing epic run"

    # 4. Re-PASS epic, then failing release run must unlink stale gate4_receipt.json.
    assert _run_gate4(repo, reg_file, profile="epic", check_exit=0).returncode == 0
    assert receipt.is_file()
    fail_release = _run_gate4(repo, reg_file, profile="release", check_exit=1)
    assert fail_release.returncode == 1
    assert json.loads(fail_release.stdout)["status"] == "FAIL"
    assert not receipt.exists(), "Stale gate4_receipt.json survived failing release run"

    # 5. Re-PASS release, then provider-level BLOCKED epic run must unlink stale gate4_receipt.json.
    assert _run_gate4(repo, reg_file, profile="release", check_exit=0).returncode == 0
    assert receipt.is_file()
    py_manifest_file = repo / ".agents" / "quality" / "python-quality.json"
    saved_py_manifest = py_manifest_file.read_text(encoding="utf-8")
    py_manifest_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "capabilities": {"test": [sys.executable, "check_runner.py"]},
                "profiles": {"epic": ["test"]},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    blocked_epic = _run_gate4(repo, reg_file, profile="epic", check_exit=0)
    assert blocked_epic.returncode == 1
    assert json.loads(blocked_epic.stdout)["status"] == "BLOCKED"
    assert not receipt.exists(), "Stale gate4_receipt.json survived BLOCKED epic run"
    py_manifest_file.write_text(saved_py_manifest, encoding="utf-8")

    # 6. Registry-level BLOCKED on epic run must also unlink stale gate4_receipt.json.
    assert _run_gate4(repo, reg_file, profile="epic", check_exit=0).returncode == 0
    assert receipt.is_file()
    reg_file.write_text(
        json.dumps({"schema_version": 1, "providers": []}, indent=2) + "\n",
        encoding="utf-8",
    )
    reg_blocked = _run_gate4(repo, reg_file, profile="epic", check_exit=0)
    assert reg_blocked.returncode == 1
    assert json.loads(reg_blocked.stdout)["status"] == "BLOCKED"
    assert not receipt.exists(), (
        "Stale gate4_receipt.json survived registry BLOCKED run"
    )


class TestSLQRReceiptCoverageAndScaffolder_Integration:
    """Tier C integration suite for SLQR Task 02."""

    def test_slqr_st_01_integration(self, tmp_path: Path) -> None:
        """[SLQR-ST-01] [Tier C - Integration] Non-passing epic or release quality run unlinks stale gate4_receipt.json while pr run preserves isolation."""
        test_slqr_st_01_non_passing_epic_or_release_unlinks_stale_gate4_receipt(
            tmp_path
        )

    def test_slqr_fr_02_missing_or_ununlinkable_receipt_does_not_mask_fail_verdict(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """[SLQR-FR-02] [Tier C - Integration] verify_polyglot_registry handles missing or read-only receipt cleanup gracefully without masking FAIL verdict."""
        repo, reg_file = _init_gate4_repo(tmp_path / "gate4_fr02_repo")
        receipt = repo / "build" / "quality" / "gate4_receipt.json"
        assert not receipt.exists()

        # 1. Missing receipt during failing epic run returns FAIL cleanly with no FileNotFoundError.
        fail_proc = _run_gate4(repo, reg_file, profile="epic", check_exit=1)
        assert fail_proc.returncode == 1
        assert "FileNotFoundError" not in fail_proc.stderr
        assert "Traceback" not in fail_proc.stderr
        payload = json.loads(fail_proc.stdout)
        assert payload["status"] == "FAIL"
        assert not receipt.exists()

        # 2. OSError during unlink of an existing receipt does not mask FAIL verdict.
        mod = _load_script_module("verify_polyglot_registry_slqr", VERIFY_SCRIPT)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text('{"status": "PASS"}\n', encoding="utf-8")

        real_unlink = Path.unlink

        def _deny_receipt_unlink(self: Path, *args: Any, **kwargs: Any) -> None:
            if self.name == "gate4_receipt.json":
                raise PermissionError("read-only receipt directory")
            real_unlink(self, *args, **kwargs)

        monkeypatch.setattr(Path, "unlink", _deny_receipt_unlink)
        registry = json.loads(reg_file.read_text(encoding="utf-8"))
        head_sha = _git(repo, "rev-parse", "HEAD")
        res = mod.verify_polyglot_execution(
            registry_data=registry,
            requested_profile="epic",
            repository_sha=head_sha,
            provider_results=[
                {
                    "provider_id": "python-core",
                    "contract_version": 1,
                    "profile": "epic",
                    "repository_sha": head_sha,
                    "status": "FAIL",
                    "checks": [
                        {
                            "id": "test",
                            "category": "test",
                            "status": "FAIL",
                            "source": "check_runner.py",
                            "duration": 0.1,
                            "summary": "failed",
                            "evidence_refs": ["ev-1"],
                        }
                    ],
                    "coverage": {},
                    "evidence": [
                        {
                            "id": "ev-1",
                            "type": "command",
                            "source": "check_runner.py",
                            "location": "build/quality/python-core/test.log",
                        }
                    ],
                    "started_head": head_sha,
                    "finished_head": head_sha,
                    "duration": 0.1,
                    "blockers": ["test failed"],
                    "warnings": [],
                }
            ],
            repo_root=repo,
            execute=False,
        )
        assert res["status"] == "FAIL"

    def test_slqr_st_02_integrate_branch_verify_tier_warns_on_dirty_noop_worktree(
        self,
        tmp_path: Path,
    ) -> None:
        """[SLQR-ST-02] [Tier C - Integration] integrate_branch verify-tier surfaces dirty working tree warning when uncommitted edits exist on a noop branch."""
        repo = tmp_path / "integrate_dirty_repo"
        repo.mkdir()
        _init_git_repo(repo)

        tracked = repo / "src" / "service.py"
        tracked.parent.mkdir(parents=True, exist_ok=True)
        tracked.write_text("VALUE = 1\n", encoding="utf-8")
        _git(repo, "add", "src/service.py")
        _git(repo, "commit", "-q", "-m", "Initial main commit")

        _git(repo, "checkout", "-q", "-b", "feat/slqr-demo")
        tracked.write_text("VALUE = 2\n", encoding="utf-8")
        _git(repo, "add", "src/service.py")
        _git(repo, "commit", "-q", "-m", "[SLQR] Feature change")

        # Establish backup ref matching HEAD via rebase --no-fetch -> tier == "noop".
        rebase_proc = _run_py(
            INTEGRATE_SCRIPT,
            ["rebase", "--base", "main", "--no-fetch", "--format", "json"],
            cwd=repo,
        )
        assert rebase_proc.returncode == 0, rebase_proc.stderr
        assert json.loads(rebase_proc.stdout)["result"] == "noop"

        # Clean worktree has empty warnings.
        clean_proc = _run_py(
            INTEGRATE_SCRIPT,
            ["verify-tier", "--base", "main", "--format", "json"],
            cwd=repo,
        )
        assert clean_proc.returncode == 0, clean_proc.stderr
        clean_report = json.loads(clean_proc.stdout)
        assert clean_report["tier"] == "noop"
        assert clean_report["warnings"] == []

        # Dirty tracked modification surfaces explicit dirty-worktree warning.
        tracked.write_text("VALUE = 3\n", encoding="utf-8")
        dirty_proc = _run_py(
            INTEGRATE_SCRIPT,
            ["verify-tier", "--base", "main", "--format", "json"],
            cwd=repo,
        )
        assert dirty_proc.returncode == 0, dirty_proc.stderr
        dirty_report = json.loads(dirty_proc.stdout)
        assert dirty_report["tier"] == "noop"
        assert dirty_report["warnings"] == ["the worktree has uncommitted changes"]

        # Untracked-only file (with tracked file restored) does not trigger tracked-dirty warning.
        tracked.write_text("VALUE = 2\n", encoding="utf-8")
        (repo / "scratch.tmp").write_text("untracked\n", encoding="utf-8")
        untracked_proc = _run_py(
            INTEGRATE_SCRIPT,
            ["verify-tier", "--base", "main", "--format", "json"],
            cwd=repo,
        )
        assert untracked_proc.returncode == 0, untracked_proc.stderr
        assert json.loads(untracked_proc.stdout)["warnings"] == []

    @pytest.mark.parametrize("manifest_key", [*ALL_STACKS, "web_template"])
    def test_slqr_hp_02_scaffolder_and_web_template_deduplicate_profiles(
        self,
        scaffolded_all_stacks: dict[str, dict[str, Any]],
        manifest_key: str,
    ) -> None:
        """[SLQR-HP-02] [Tier C - Integration] Scaffolder and web template generate deduplicated 4-profile manifests across all 6 stacks."""
        manifest = scaffolded_all_stacks[manifest_key]
        profiles = manifest["profiles"]

        for profile_name, cap_list in profiles.items():
            assert len(cap_list) == len(set(cap_list)), (
                f"{manifest_key}.{profile_name} contains duplicate capabilities: {cap_list}"
            )

        assert "pr_diff_audit" in profiles["pr"]
        assert "pr_impact" in profiles["pr"]
        assert "workspace_audit" not in profiles["pr"]
        assert "workspace_impact" not in profiles["pr"]

        for profile_name in ("epic", "scheduled", "release"):
            caps = profiles[profile_name]
            assert "pr_diff_audit" not in caps, (
                f"{manifest_key}.{profile_name} leaked pr_diff_audit"
            )
            assert "pr_impact" not in caps, (
                f"{manifest_key}.{profile_name} leaked pr_impact"
            )
            assert "workspace_audit" in caps, (
                f"{manifest_key}.{profile_name} missing workspace_audit"
            )
            assert "workspace_impact" in caps, (
                f"{manifest_key}.{profile_name} missing workspace_impact"
            )

        assert set(profiles["epic"]).issubset(set(profiles["release"])), (
            f"{manifest_key} release must remain a superset of epic"
        )

    def test_slqr_hp_02_stack_specific_offline_and_tool_hardening(
        self,
        scaffolded_all_stacks: dict[str, dict[str, Any]],
    ) -> None:
        """[SLQR-HP-02] [Tier C - Integration] Scaffolder and web template enforce npx --no-install, offline Rust security, omitted scheduled test_e2e, and mypy --strict src tests."""
        for key in ("web", "web_template"):
            web_manifest = scaffolded_all_stacks[key]
            caps = web_manifest["capabilities"]
            assert caps["format"][:2] == ["npx", "--no-install"], (
                f"{key} format must use npx --no-install"
            )
            assert caps["test_e2e"][:2] == ["npx", "--no-install"], (
                f"{key} test_e2e must use npx --no-install"
            )
            for cap_name, cap_val in caps.items():
                cmd = (
                    cap_val.get("command", []) if isinstance(cap_val, dict) else cap_val
                )
                if isinstance(cmd, list) and cmd and cmd[0] == "npx":
                    assert len(cmd) >= 2 and cmd[1] == "--no-install", (
                        f"{key}.{cap_name} uses bare npx: {cmd}"
                    )
            assert "test_e2e" not in web_manifest["profiles"]["scheduled"], (
                f"{key} scheduled profile must omit test_e2e"
            )
            assert "test_e2e" in web_manifest["profiles"]["epic"]
            assert "test_e2e" in web_manifest["profiles"]["release"]

        rust_manifest = scaffolded_all_stacks["rust"]
        rust_caps = rust_manifest["capabilities"]
        assert rust_caps["security"] == ["./scripts/check_security.sh"]
        assert rust_caps["security_deps"] == ["cargo", "audit"]
        for offline_profile in ("pr", "epic"):
            for cap_name in rust_manifest["profiles"][offline_profile]:
                cap_val = rust_caps[cap_name]
                cmd = (
                    cap_val.get("command", []) if isinstance(cap_val, dict) else cap_val
                )
                assert cmd[:2] != ["cargo", "audit"], (
                    f"rust.{offline_profile}.{cap_name} must not invoke online cargo audit"
                )
        assert "security_deps" in rust_manifest["profiles"]["scheduled"]
        assert "security_deps" in rust_manifest["profiles"]["release"]

        py_manifest = scaffolded_all_stacks["python"]
        assert py_manifest["capabilities"]["type_check"] == [
            "uv",
            "run",
            "mypy",
            "--strict",
            "src",
            "tests",
        ]

    @pytest.mark.parametrize(
        ("align_covered", "studio_covered", "expected_rc", "expected_token"),
        [
            (9, 11, 0, "PASS:"),
            (8, 11, 1, "src/pkg/align"),
            (9, 9, 1, "src/web/studio.js"),
        ],
    )
    def test_slqr_hp_02_check_diff_coverage_package_floors_ratchets(
        self,
        tmp_path: Path,
        align_covered: int,
        studio_covered: int,
        expected_rc: int,
        expected_token: str,
    ) -> None:
        """[SLQR-HP-02] [Tier C - Integration] check_diff_coverage enforces adapter and module ratchets from coverage_floors.json across LCOV and Cobertura."""
        repo = tmp_path / f"cov_{align_covered}_{studio_covered}"
        repo.mkdir()
        floors_path = repo / ".agents" / "quality" / "coverage_floors.json"
        floors_path.parent.mkdir(parents=True, exist_ok=True)
        floors_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "description": "Monotonic adapter and web module floors",
                    "default_core_floor": 0.9,
                    "python": {
                        "adapters": {
                            "src/pkg/align": 0.88,
                        }
                    },
                    "web_modules": {
                        "src/web/studio.js": {"floor": 0.50},
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        lcov_path = repo / "coverage" / "lcov.info"
        lcov_path.parent.mkdir(parents=True, exist_ok=True)
        lcov_path.write_text(
            _make_lcov_record("src/web/studio.js", studio_covered, 20),
            encoding="utf-8",
        )
        cobertura_path = repo / "coverage.xml"
        cobertura_path.write_text(
            _make_cobertura_xml([("src/pkg/align/ctc.py", align_covered, 10)]),
            encoding="utf-8",
        )

        proc = _run_py(
            DIFF_COV_SCRIPT,
            [
                str(lcov_path),
                str(cobertura_path),
                "--repo-root",
                str(repo),
                "--min-package-coverage",
                "0.70",
                "--package-floors",
                ".agents/quality/coverage_floors.json",
            ],
            cwd=repo,
        )
        assert proc.returncode == expected_rc, (
            f"stdout={proc.stdout}\nstderr={proc.stderr}"
        )
        assert expected_token in proc.stdout

        json_proc = _run_py(
            DIFF_COV_SCRIPT,
            [
                str(lcov_path),
                str(cobertura_path),
                "--repo-root",
                str(repo),
                "--min-package-coverage",
                "0.70",
                "--package-floors",
                str(floors_path),
                "--json",
            ],
            cwd=repo,
        )
        assert json_proc.returncode == expected_rc
        payload = json.loads(json_proc.stdout)
        assert payload["status"] == ("PASS" if expected_rc == 0 else "FAIL")
        if expected_rc == 1:
            assert any(expected_token in failure for failure in payload["failures"])

    def test_slqr_hp_02_package_floors_flat_packages_and_basename_matching(
        self,
        tmp_path: Path,
    ) -> None:
        """[SLQR-HP-02] [Tier C - Integration] check_diff_coverage supports packages, flat keys, percentage floors, multi-file prefix aggregation, and unique basename matching."""
        repo = tmp_path / "cov_formats"
        repo.mkdir()
        floors_path = repo / "floors.json"
        floors_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "packages": {"packages/net": {"floor": 80}},
                    "web_modules": {"studio.js": 50},
                    "src/flat_adapter": 0.75,
                }
            ),
            encoding="utf-8",
        )
        lcov_path = repo / "lcov.info"
        lcov_path.write_text(
            "".join(
                [
                    _make_lcov_record("packages/net/client.py", 9, 10),
                    _make_lcov_record("packages/net/retry.py", 7, 10),
                    _make_lcov_record("src/preview/static/studio.js", 10, 20),
                    _make_lcov_record("src/flat_adapter/mod.py", 3, 4),
                ]
            ),
            encoding="utf-8",
        )
        ok_proc = _run_py(
            DIFF_COV_SCRIPT,
            [
                str(lcov_path),
                "--repo-root",
                str(repo),
                "--min-package-coverage",
                "0.70",
                "--package-floors",
                str(floors_path),
            ],
            cwd=repo,
        )
        assert ok_proc.returncode == 0, ok_proc.stdout

        lcov_path.write_text(
            "".join(
                [
                    _make_lcov_record("packages/net/client.py", 8, 10),
                    _make_lcov_record("packages/net/retry.py", 7, 10),
                    _make_lcov_record("src/preview/static/studio.js", 10, 20),
                    _make_lcov_record("src/flat_adapter/mod.py", 3, 4),
                ]
            ),
            encoding="utf-8",
        )
        fail_proc = _run_py(
            DIFF_COV_SCRIPT,
            [
                str(lcov_path),
                "--repo-root",
                str(repo),
                "--package-floors",
                str(floors_path),
            ],
            cwd=repo,
        )
        assert fail_proc.returncode == 1
        assert "packages/net" in fail_proc.stdout

    @pytest.mark.parametrize(
        ("case_name", "floors_content"),
        [
            ("missing", None),
            ("corrupt_json", "{not valid json"),
            ("non_object_json", "[0.8, 0.9]"),
            ("negative_floor", json.dumps({"python": {"adapters": {"src/a": -0.1}}})),
            ("over_100_floor", json.dumps({"web_modules": {"src/a.js": 101}})),
            ("bool_floor", json.dumps({"packages": {"src/a": True}})),
            ("string_floor", json.dumps({"src/a": "80%"})),
            (
                "dict_without_floor",
                json.dumps({"web_modules": {"src/a.js": {"note": "x"}}}),
            ),
            ("bad_python_section", json.dumps({"python": "invalid"})),
            ("bad_adapters_section", json.dumps({"python": {"adapters": ["src/a"]}})),
            ("bad_web_modules_section", json.dumps({"web_modules": 42})),
            ("bad_packages_section", json.dumps({"packages": "none"})),
            ("traversal_key", json.dumps({"packages": {"../outside": 0.8}})),
        ],
    )
    def test_slqr_ec_02_invalid_or_missing_package_floors_returns_blocked_exit_2(
        self,
        tmp_path: Path,
        case_name: str,
        floors_content: str | None,
    ) -> None:
        """[SLQR-EC-02] [Tier C - Integration] check_diff_coverage handles missing or malformed package_floors file as exit 2 BLOCKED and exempts unmeasured files cleanly."""
        repo = tmp_path / f"ec02_{case_name}"
        repo.mkdir()
        lcov_path = repo / "lcov.info"
        lcov_path.write_text(
            _make_lcov_record("src/core/service.py", 19, 20),
            encoding="utf-8",
        )

        floors_path = repo / "missing_floors.json"
        if floors_content is not None:
            floors_path = repo / "floors.json"
            floors_path.write_text(floors_content, encoding="utf-8")

        proc = _run_py(
            DIFF_COV_SCRIPT,
            [
                str(lcov_path),
                "--repo-root",
                str(repo),
                "--package-floors",
                str(floors_path),
                "--json",
            ],
            cwd=repo,
        )
        assert proc.returncode == 2, (
            f"{case_name}: stdout={proc.stdout}\nstderr={proc.stderr}"
        )
        assert "Traceback" not in proc.stdout
        assert "Traceback" not in proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["status"] == "BLOCKED"
        assert payload["failures"]

    def test_slqr_ec_02_unmeasured_package_floors_exempted_cleanly(
        self,
        tmp_path: Path,
    ) -> None:
        """[SLQR-EC-02] [Tier C - Integration] check_diff_coverage exempts unmeasured adapter prefixes and web modules cleanly."""
        repo = tmp_path / "ec02_unmeasured"
        repo.mkdir()
        lcov_path = repo / "lcov.info"
        lcov_path.write_text(
            _make_lcov_record("src/core/service.py", 19, 20),
            encoding="utf-8",
        )
        floors_path = repo / "coverage_floors.json"
        floors_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "python": {"adapters": {"src/pkg/unmeasured_adapter": 0.99}},
                    "web_modules": {"src/web/unmeasured_studio.js": 0.99},
                    "packages": {"packages/absent": 0.99},
                }
            ),
            encoding="utf-8",
        )

        proc = _run_py(
            DIFF_COV_SCRIPT,
            [
                str(lcov_path),
                "--repo-root",
                str(repo),
                "--min-coverage",
                "0.90",
                "--package-floors",
                str(floors_path),
                "--json",
            ],
            cwd=repo,
        )
        assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
        payload = json.loads(proc.stdout)
        assert payload["status"] == "PASS"
        assert payload["failures"] == []
