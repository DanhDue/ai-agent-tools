"""Tier C integration and unit tests for Task 05: Worker pool COW mounts and suffix-scoped triage.

Covers BDD Scenarios:
- PLQ-HP-05: Worker pool materializes symlink caches and APFS/copytree COW trees without symlinking .dart_tool
- PLQ-ST-03: Repeated sync_slot preserves COW mounts and never deletes them during git clean
- PLQ-ST-04: finalize_slot unstages ignored mounts while committing edits to tracked xcconfig files
- PLQ-AR-04: Polyglot _is_test_file classifies test files and assertion weakening accurately per language
- PLQ-FR-05: APFS copy-on-write failure gracefully falls back to shutil.copytree on non-APFS or Linux hosts
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
POOL_SCRIPT = SCRIPTS_DIR / "manage_worker_pool.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import _stack_lifecycle_registry as stack_registry  # noqa: E402
import manage_worker_pool  # noqa: E402


BASE_GITIGNORE = (
    ".worktrees/\n"
    ".devtool/.memory.lock\n"
    ".devtool/state/\n"
    ".devtool/logs/\n"
    "target\n"
    "node_modules\n"
    ".dart_tool/\n"
    "packages/*/.dart_tool/\n"
    "features/*/.dart_tool/\n"
    "bricks/*/hooks/.dart_tool/\n"
    "secureFiles/\n"
    "android/local.properties\n"
    "ios/Flutter/Secret.xcconfig\n"
    "custom_secrets/\n"
)


def _git(cwd: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _init_polyglot_pool_repo(
    tmp_path: Path,
    *,
    epic_dir: str = "plq_pool_demo",
    epic_slug: str = "plq-pool-demo",
    gitignore: str = BASE_GITIGNORE,
) -> tuple[Path, Path, Path]:
    """Create an isolated git repo with an epic worktree and isolated HOME/REAL_HOME."""
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)

    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "PLQ Test User")
    _git(repo, "config", "user.email", "plq@example.invalid")

    (repo / ".gitignore").write_text(gitignore, encoding="utf-8")
    (repo / "README.md").write_text("# Polyglot Pool Repo\n", encoding="utf-8")
    (repo / "src").mkdir(parents=True, exist_ok=True)
    (repo / "src" / "__init__.py").write_text("", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Initial commit")

    main_wt = repo / ".worktrees" / epic_dir
    main_wt.parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "worktree", "add", "-q", str(main_wt), "-b", f"epic/{epic_slug}", "main")
    return repo, main_wt, home


def _run_pool_cli(
    cwd: Path,
    args: list[str],
    *,
    home: Path,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["REAL_HOME"] = str(home)
    env["WORKSPACE_ROOT"] = str(cwd)
    for key in (
        "AGY_PROFILE",
        "ANTIGRAVITY_PROFILE",
        "AGY_PROGRAMMER_MODEL",
        "AGY_PROGRAMMER_EFFORT",
    ):
        env.pop(key, None)
    return subprocess.run(
        [sys.executable, "-B", str(POOL_SCRIPT), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _seed_finalize_stubs(
    main_wt: Path,
    epic_dir: str,
    epic_slug: str,
    task_id: str,
    *,
    scenario_id: str,
) -> None:
    """Seed minimal task mirrors, HLD, BDD file, and deterministic gate stubs."""
    epic_root = main_wt / ".devtool" / "epic" / epic_dir
    features_dir = main_wt / ".devtool" / "features"
    epic_root.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)

    (epic_root / f"{epic_dir}.md").write_text(
        f"# Epic {epic_dir}\n\nIntegration test roots: tests\n",
        encoding="utf-8",
    )
    (epic_root / "bdd_scenarios.md").write_text(
        "# BDD\n\n```gherkin\n"
        f"Scenario: [{scenario_id}] [Tier C - Integration] Stub scenario\n"
        "Given a repo\nWhen it runs\nThen it passes\n"
        "```\n",
        encoding="utf-8",
    )
    task_md = (
        f'---\nid: "{task_id}"\nstatus: "in-progress"\nepic: "{epic_slug}"\n'
        'completedAt: null\nmodified: "2026-11-27T00:00:00Z"\n---\n\n'
        f"# {task_id}\n\nCovers: {scenario_id}\n\n"
        "## Verification\n\n| ID | Phase | Command | Expect | Needs |\n"
        "|---|---|---|---|---|\n| V1 | GREEN | `true` | exit 0 | — |\n"
    )
    (epic_root / f"{task_id}.md").write_text(task_md, encoding="utf-8")
    (features_dir / f"{task_id}.md").write_text(task_md, encoding="utf-8")

    (main_wt / "tests").mkdir(parents=True, exist_ok=True)
    (main_wt / "tests" / f"test_{task_id}.py").write_text(
        f"# Covers {scenario_id}\ndef test_{task_id}():\n    assert True\n",
        encoding="utf-8",
    )

    scripts_dir = main_wt / "skills" / "dev-implementation" / "resources" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "run_task_checks.py").write_text(
        "import sys\nprint('done gate: PASS')\nsys.exit(0)\n",
        encoding="utf-8",
    )
    (scripts_dir / "check_bdd_traceability.py").write_text(
        "import sys\nprint('PASS')\nsys.exit(0)\n",
        encoding="utf-8",
    )
    (scripts_dir / "sync_task_status.py").write_text(
        "import pathlib, re, sys\n"
        "task_id, new_status = sys.argv[2], sys.argv[3]\n"
        "root = pathlib.Path.cwd()\n"
        "for p in list(root.glob(f'.devtool/epic/*/{task_id}.md')):\n"
        "    t = re.sub(r'^status:.*$', f'status: \"{new_status}\"', p.read_text(encoding='utf-8'), flags=re.M)\n"
        "    p.write_text(t, encoding='utf-8')\n"
        "feat = root / '.devtool' / 'features' / f'{task_id}.md'\n"
        "if feat.is_file():\n"
        "    t = re.sub(r'^status:.*$', f'status: \"{new_status}\"', feat.read_text(encoding='utf-8'), flags=re.M)\n"
        "    done_dir = root / '.devtool' / 'features' / 'done'\n"
        "    done_dir.mkdir(parents=True, exist_ok=True)\n"
        "    (done_dir / f'{task_id}.md').write_text(t, encoding='utf-8')\n"
        "    feat.unlink()\n",
        encoding="utf-8",
    )


def _setup_slot_in_fix_pass_1(
    tmp_path: Path,
    *,
    initial_files: dict[str, str],
    epic_dir: str = "plq_triage",
    epic_slug: str = "plq-triage",
    task_id: str = "task_05",
) -> tuple[Path, Path, Path, Path]:
    """Initialize a slot at Fix Pass 1 (review_passes_used=1, fix_passes_used=1)."""
    repo, main_wt, home = _init_polyglot_pool_repo(
        tmp_path, epic_dir=epic_dir, epic_slug=epic_slug
    )
    for rel, content in initial_files.items():
        target = main_wt / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    _git(main_wt, "add", "-A")
    _git(main_wt, "commit", "-q", "-m", "Seed initial files for triage")

    init_res = _run_pool_cli(main_wt, ["init", epic_dir, "--pool-size", "1"], home=home)
    assert init_res.returncode == 0, init_res.stderr

    w1 = _run_pool_cli(
        main_wt,
        ["sync", epic_dir, "--slot", "1", "--task", task_id, "--status", "working"],
        home=home,
    )
    assert w1.returncode == 0, w1.stderr

    r1 = _run_pool_cli(
        main_wt,
        ["sync", epic_dir, "--slot", "1", "--task", task_id, "--status", "review"],
        home=home,
    )
    assert r1.returncode == 0, r1.stderr

    blockers_file = _write_json(
        tmp_path / "blockers.json",
        [
            {
                "id": "BLK-1",
                "category": "BDD_VIOLATION",
                "file": next(iter(initial_files)),
                "summary": "Fix issue",
            }
        ],
    )
    fix1 = _run_pool_cli(
        main_wt,
        [
            "sync",
            epic_dir,
            "--slot",
            "1",
            "--status",
            "working",
            "--no-reset",
            "--blockers-file",
            str(blockers_file),
        ],
        home=home,
    )
    assert fix1.returncode == 0, fix1.stderr

    slot1 = manage_worker_pool.get_slot_path(repo, epic_dir, 1)
    return repo, main_wt, home, slot1


def test_plq_hp_05_worker_pool_symlink_and_cow_mounts(tmp_path: Path) -> None:
    """[PLQ-HP-05] Worker pool materializes symlink caches and APFS/copytree COW trees without symlinking .dart_tool."""
    # Verify symlink-only CACHE_DIR_CANDIDATES omits .dart_tool and includes .astro
    assert ".dart_tool" not in manage_worker_pool.CACHE_DIR_CANDIDATES
    for expected_symlink_cache in (
        "target",
        "node_modules",
        ".astro",
        ".venv",
        ".gradle",
        ".build",
        "Pods",
    ):
        assert expected_symlink_cache in manage_worker_pool.CACHE_DIR_CANDIDATES

    repo, main_wt, home = _init_polyglot_pool_repo(tmp_path)

    # Populate main_wt with symlink caches + nested .dart_tool trees + gitignored secrets
    (main_wt / "target" / "debug").mkdir(parents=True)
    (main_wt / "target" / "debug" / "artifact.bin").write_text("bin", encoding="utf-8")
    (main_wt / "node_modules" / "pkg").mkdir(parents=True)
    (main_wt / "node_modules" / "pkg" / "index.js").write_text(
        "module.exports = 1;\n", encoding="utf-8"
    )
    (main_wt / ".dart_tool").mkdir()
    (main_wt / ".dart_tool" / "package_config.json").write_text(
        '{"root": true}\n', encoding="utf-8"
    )
    (main_wt / "packages" / "core" / ".dart_tool").mkdir(parents=True)
    (main_wt / "packages" / "core" / ".dart_tool" / "package_config.json").write_text(
        '{"pkg": "core"}\n', encoding="utf-8"
    )
    (main_wt / "features" / "home" / ".dart_tool").mkdir(parents=True)
    (main_wt / "features" / "home" / ".dart_tool" / "package_config.json").write_text(
        '{"feat": "home"}\n', encoding="utf-8"
    )
    (main_wt / "bricks" / "feat" / "hooks" / ".dart_tool").mkdir(parents=True)
    (
        main_wt / "bricks" / "feat" / "hooks" / ".dart_tool" / "package_config.json"
    ).write_text('{"brick": "feat"}\n', encoding="utf-8")
    (main_wt / "secureFiles").mkdir()
    (main_wt / "secureFiles" / "dev.json").write_text(
        '{"apiKey": "secret-dev"}\n', encoding="utf-8"
    )
    (main_wt / "android").mkdir(parents=True, exist_ok=True)
    (main_wt / "android" / "local.properties").write_text(
        "sdk.dir=/Users/dev/Android/sdk\n", encoding="utf-8"
    )

    init_res = _run_pool_cli(
        main_wt, ["init", "plq_pool_demo", "--pool-size", "1"], home=home
    )
    assert init_res.returncode == 0, init_res.stderr

    sync_res = _run_pool_cli(
        main_wt,
        [
            "sync",
            "plq_pool_demo",
            "--slot",
            "1",
            "--task",
            "task_05",
            "--status",
            "working",
        ],
        home=home,
    )
    assert sync_res.returncode == 0, sync_res.stderr

    slot1 = manage_worker_pool.get_slot_path(repo, "plq_pool_demo", 1)

    # Heavy binary/package caches are O(1) symlinks pointing to main_wt
    for sym_rel in ("target", "node_modules"):
        dst = slot1 / sym_rel
        assert dst.is_symlink(), f"{sym_rel} must be a symlink in slot 1"
        assert dst.resolve() == (main_wt / sym_rel).resolve()

    # .dart_tool trees and gitignored secrets/configs are real non-symlink copies
    expected_cow_files: dict[str, str] = {
        ".dart_tool/package_config.json": '{"root": true}\n',
        "packages/core/.dart_tool/package_config.json": '{"pkg": "core"}\n',
        "features/home/.dart_tool/package_config.json": '{"feat": "home"}\n',
        "bricks/feat/hooks/.dart_tool/package_config.json": '{"brick": "feat"}\n',
        "secureFiles/dev.json": '{"apiKey": "secret-dev"}\n',
        "android/local.properties": "sdk.dir=/Users/dev/Android/sdk\n",
    }
    for mount_root in (
        ".dart_tool",
        "packages/core/.dart_tool",
        "features/home/.dart_tool",
        "bricks/feat/hooks/.dart_tool",
        "secureFiles",
        "android/local.properties",
    ):
        dst = slot1 / mount_root
        assert dst.exists(), f"Expected cow_copy mount {mount_root} in slot 1"
        assert not dst.is_symlink(), f"{mount_root} MUST NOT be a symlink"

    for rel_file, expected_text in expected_cow_files.items():
        assert (slot1 / rel_file).read_text(encoding="utf-8") == expected_text

    # git status --porcelain inside slot 1 remains completely clean
    assert _git(slot1, "status", "--porcelain") == ""


def _verify_plq_st_03_repeated_sync_slot_preserves_cow_mounts(tmp_path: Path) -> None:
    """[PLQ-ST-03] Repeated sync_slot preserves COW mounts and never deletes them during git clean."""
    repo, main_wt, home = _init_polyglot_pool_repo(
        tmp_path, epic_dir="plq_st03", epic_slug="plq-st03"
    )

    (main_wt / ".dart_tool").mkdir()
    (main_wt / ".dart_tool" / "package_config.json").write_text(
        '{"root": 1}\n', encoding="utf-8"
    )
    (main_wt / "packages" / "core" / ".dart_tool").mkdir(parents=True)
    (main_wt / "packages" / "core" / ".dart_tool" / "package_config.json").write_text(
        '{"pkg": "core"}\n', encoding="utf-8"
    )
    (main_wt / "secureFiles").mkdir()
    (main_wt / "secureFiles" / "dev.json").write_text(
        '{"env": "dev"}\n', encoding="utf-8"
    )

    assert (
        _run_pool_cli(
            main_wt, ["init", "plq_st03", "--pool-size", "1"], home=home
        ).returncode
        == 0
    )
    slot1 = manage_worker_pool.get_slot_path(repo, "plq_st03", 1)

    # Plant slot-local sentinels inside COW mounts to prove git clean -fd never deletes them
    (slot1 / ".dart_tool" / "slot_sentinel.txt").write_text(
        "keep-1\n", encoding="utf-8"
    )
    (slot1 / "packages" / "core" / ".dart_tool" / "slot_sentinel.txt").write_text(
        "keep-2\n", encoding="utf-8"
    )
    (slot1 / "secureFiles" / "slot_sentinel.json").write_text(
        '{"keep": 3}\n', encoding="utf-8"
    )

    for cycle in range(1, 3):
        (slot1 / "scratch.tmp").write_text(f"stale-{cycle}\n", encoding="utf-8")
        (slot1 / "packages" / "core" / "stale.tmp").write_text(
            f"nested-stale-{cycle}\n", encoding="utf-8"
        )
        ok = manage_worker_pool.sync_slot(
            repo,
            "plq_st03",
            "plq-st03",
            slot=1,
            task_id="task_05",
            status="working",
            reset_worktree=True,
        )
        assert ok is True

        assert not (slot1 / "scratch.tmp").exists(), f"cycle {cycle}: scratch.tmp left"
        assert not (slot1 / "packages" / "core" / "stale.tmp").exists()

        for mount in (".dart_tool", "packages/core/.dart_tool", "secureFiles"):
            dst = slot1 / mount
            assert dst.is_dir() and not dst.is_symlink(), f"cycle {cycle}: {mount}"

        assert (slot1 / ".dart_tool" / "slot_sentinel.txt").read_text(
            encoding="utf-8"
        ) == "keep-1\n"
        assert (
            slot1 / "packages" / "core" / ".dart_tool" / "slot_sentinel.txt"
        ).read_text(encoding="utf-8") == "keep-2\n"
        assert (slot1 / "secureFiles" / "dev.json").read_text(
            encoding="utf-8"
        ) == '{"env": "dev"}\n'
        assert (slot1 / "secureFiles" / "slot_sentinel.json").read_text(
            encoding="utf-8"
        ) == '{"keep": 3}\n'
        assert _git(slot1, "status", "--porcelain") == ""


def _verify_plq_st_04_finalize_slot_unstages_ignored_mounts_and_commits_tracked_xcconfig(
    tmp_path: Path,
) -> None:
    """[PLQ-ST-04] finalize_slot unstages ignored mounts while committing edits to tracked xcconfig files."""
    repo, main_wt, home = _init_polyglot_pool_repo(
        tmp_path, epic_dir="plq_st04", epic_slug="plq-st04"
    )
    task_id = "task_05_stage"
    _seed_finalize_stubs(
        main_wt, "plq_st04", "plq-st04", task_id, scenario_id="PLQ-ST-04"
    )

    # Track ios/Flutter/Debug.xcconfig and register a custom gitignored pool_mounts cow_copy entry
    tracked_xcconfig = main_wt / "ios" / "Flutter" / "Debug.xcconfig"
    tracked_xcconfig.parent.mkdir(parents=True, exist_ok=True)
    tracked_xcconfig.write_text('#include "Generated.xcconfig"\n', encoding="utf-8")
    _write_json(
        main_wt / ".agents" / "quality" / "check_quality.json",
        {
            "schema_version": 1,
            "pool_mounts": [{"path": "custom_secrets", "mode": "cow_copy"}],
        },
    )
    _git(main_wt, "add", "-A")
    _git(main_wt, "commit", "-q", "-m", "Seed tracked Debug.xcconfig and pool_mounts")

    # Populate gitignored mounts in main_wt
    (main_wt / ".dart_tool").mkdir()
    (main_wt / ".dart_tool" / "package_config.json").write_text("{}", encoding="utf-8")
    (main_wt / "secureFiles").mkdir()
    (main_wt / "secureFiles" / "dev.json").write_text(
        '{"token": "top-secret"}\n', encoding="utf-8"
    )
    (main_wt / "android").mkdir(parents=True, exist_ok=True)
    (main_wt / "android" / "local.properties").write_text(
        "sdk.dir=/sdk\n", encoding="utf-8"
    )
    (main_wt / "ios" / "Flutter" / "Secret.xcconfig").write_text(
        "API_SECRET = nope\n", encoding="utf-8"
    )
    (main_wt / "custom_secrets").mkdir()
    (main_wt / "custom_secrets" / "api.key").write_text(
        "super-secret-key\n", encoding="utf-8"
    )

    assert (
        _run_pool_cli(
            main_wt, ["init", "plq_st04", "--pool-size", "1"], home=home
        ).returncode
        == 0
    )
    slot1 = manage_worker_pool.get_slot_path(repo, "plq_st04", 1)

    for cow_rel in (
        ".dart_tool",
        "secureFiles",
        "android/local.properties",
        "ios/Flutter/Secret.xcconfig",
        "custom_secrets",
    ):
        assert (slot1 / cow_rel).exists() and not (slot1 / cow_rel).is_symlink()

    # Legitimate source edit + edit to git-tracked ios/Flutter/Debug.xcconfig
    (slot1 / "src" / "feature.py").write_text(
        "FEATURE_READY = True\n", encoding="utf-8"
    )
    slot_xcconfig = slot1 / "ios" / "Flutter" / "Debug.xcconfig"
    slot_xcconfig.write_text(
        '#include "Generated.xcconfig"\nENABLE_BITCODE = NO\n',
        encoding="utf-8",
    )

    # Even if an agent accidentally force-stages ignored secrets, capture + finalize must exclude them
    _git(
        slot1,
        "add",
        "-f",
        "secureFiles/dev.json",
        "custom_secrets/api.key",
        "android/local.properties",
        ".dart_tool/package_config.json",
    )

    tree_sha = manage_worker_pool.capture_slot_tree_sha(slot1, "plq_st04")
    tree_files = _git(slot1, "ls-tree", "-r", "--name-only", tree_sha).splitlines()
    assert "src/feature.py" in tree_files
    assert "ios/Flutter/Debug.xcconfig" in tree_files
    for forbidden in (
        ".dart_tool",
        "secureFiles",
        "android/local.properties",
        "ios/Flutter/Secret.xcconfig",
        "custom_secrets",
    ):
        assert not any(
            entry == forbidden or entry.startswith(forbidden + "/")
            for entry in tree_files
        ), f"Tree snapshot leaked excluded mount {forbidden}: {tree_files}"

    report = manage_worker_pool.finalize_slot(
        repo,
        "plq_st04",
        "plq-st04",
        slot=1,
        task_id=task_id,
        mode="pass1-approved",
    )
    assert report.get("ok") is True, report
    assert report.get("merged") is True, report

    show_stat = _git(main_wt, "show", "--stat", "HEAD")
    committed_names = _git(
        main_wt, "show", "--pretty=format:", "--name-only", "HEAD"
    ).splitlines()
    assert "src/feature.py" in committed_names
    assert "ios/Flutter/Debug.xcconfig" in committed_names
    assert "ENABLE_BITCODE = NO" in tracked_xcconfig.read_text(encoding="utf-8")

    for forbidden in (
        ".dart_tool",
        "secureFiles",
        "android/local.properties",
        "ios/Flutter/Secret.xcconfig",
        "custom_secrets",
    ):
        assert forbidden not in show_stat, (
            f"Committed HEAD leaked excluded mount {forbidden}:\n{show_stat}"
        )
        assert not any(
            entry == forbidden or entry.startswith(forbidden + "/")
            for entry in committed_names
        )


def _verify_plq_ar_04_polyglot_is_test_file_and_assertion_weakening(
    tmp_path: Path,
) -> None:
    """[PLQ-AR-04] Polyglot _is_test_file classifies test files and assertion weakening accurately per language."""
    # Direct _is_test_file verification across all 6 stacks
    for test_path in (
        "test/calc_test.dart",
        "lib/calc_test.dart",
        "crates/core/src/calc_test.rs",
        "apps/web/src/calc.spec.ts",
        "feature/wallet/CalcTest.kt",
        "Sources/WalletTests.swift",
        "tests/test_calc.py",
    ):
        assert manage_worker_pool._is_test_file(test_path) is True, test_path

    for non_test_path in (
        "lib/calc.dart",
        "crates/core/src/calc.rs",
        "apps/web/src/calc.ts",
        "feature/wallet/Calc.kt",
        "Sources/Wallet.swift",
        "src/calc.py",
    ):
        assert manage_worker_pool._is_test_file(non_test_path) is False, non_test_path

    cases: tuple[tuple[str, str, str, str], ...] = (
        (
            "dart_remove_expect",
            "packages/core/test/calc_test.dart",
            "void main() {\n  test('adds', () {\n    expect(1 + 1, equals(2));\n  });\n}\n",
            "void main() {\n  test('adds', () {\n    final _ = 1 + 1;\n  });\n}\n",
        ),
        (
            "dart_add_skip_true",
            "lib/calc_test.dart",
            "void main() {\n  test('adds', () {\n    expect(1 + 1, equals(2));\n  });\n}\n",
            "void main() {\n  test('adds', () {\n    expect(1 + 1, equals(2));\n  }, skip: true);\n}\n",
        ),
        (
            "rust_add_ignore",
            "crates/core/src/calc_test.rs",
            "#[test]\nfn adds() {\n    assert_eq!(1 + 1, 2);\n}\n",
            "#[test]\n#[ignore]\nfn adds() {\n    assert_eq!(1 + 1, 2);\n}\n",
        ),
        (
            "ts_add_dot_skip",
            "apps/web/src/calc.spec.ts",
            "it('adds', () => {\n  expect(1 + 1).toBe(2);\n});\n",
            "it.skip('adds', () => {\n  expect(1 + 1).toBe(2);\n});\n",
        ),
        (
            "kotlin_add_ignore",
            "feature/wallet/CalcTest.kt",
            "class CalcTest {\n    @Test\n    fun adds() {\n        assertEquals(2, 1 + 1)\n    }\n}\n",
            "class CalcTest {\n    @Ignore\n    @Test\n    fun adds() {\n        assertEquals(2, 1 + 1)\n    }\n}\n",
        ),
        (
            "swift_add_xctskip",
            "Sources/WalletTests.swift",
            "final class WalletTests: XCTestCase {\n    func testAdds() {\n        XCTAssertEqual(1 + 1, 2)\n    }\n}\n",
            'final class WalletTests: XCTestCase {\n    func testAdds() throws {\n        throw XCTSkip("flaky")\n        XCTAssertEqual(1 + 1, 2)\n    }\n}\n',
        ),
        (
            "python_add_inline_pytest_skip",
            "tests/test_calc.py",
            "import pytest\n\n\ndef test_adds() -> None:\n    assert 1 + 1 == 2\n",
            'import pytest\n\n\ndef test_adds() -> None:\n    pytest.skip("flaky")\n    assert 1 + 1 == 2\n',
        ),
    )

    for case_name, rel_path, before_text, after_text in cases:
        case_dir = tmp_path / case_name
        repo, main_wt, _home, slot1 = _setup_slot_in_fix_pass_1(
            case_dir,
            initial_files={rel_path: before_text},
            epic_dir=f"plq_{case_name}",
            epic_slug=f"plq-{case_name.replace('_', '-')}",
        )
        (slot1 / rel_path).write_text(after_text, encoding="utf-8")

        report = manage_worker_pool.triage_fix_slot(
            repo,
            f"plq_{case_name}",
            f"plq-{case_name.replace('_', '-')}",
            slot=1,
            task_id="task_05",
            epic_worktree_root=main_wt,
        )
        assert report["non_test_changed_lines"] == 0, f"{case_name}: {report}"
        assert report["test_changed_lines"] > 0, f"{case_name}: {report}"
        assert "TEST_ASSERTION_WEAKENED" in report["triggers"], f"{case_name}: {report}"
        assert report["tier1_status"] == "HIGH_RISK", f"{case_name}: {report}"
        assert report["bounded_diff"] is None, f"{case_name}: {report}"


def _verify_plq_fr_05_apfs_cow_failure_falls_back_to_shutil_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """[PLQ-FR-05] APFS copy-on-write failure gracefully falls back to shutil.copytree on non-APFS or Linux hosts."""
    repo, main_wt, _home = _init_polyglot_pool_repo(
        tmp_path / "darwin_fallback", epic_dir="plq_fr05", epic_slug="plq-fr05"
    )
    (main_wt / ".dart_tool" / "nested").mkdir(parents=True)
    (main_wt / ".dart_tool" / "package_config.json").write_text(
        '{"formatVersion": 2}\n', encoding="utf-8"
    )
    (main_wt / ".dart_tool" / "nested" / "build.txt").write_text(
        "nested-ok\n", encoding="utf-8"
    )
    (main_wt / "secureFiles").mkdir()
    (main_wt / "secureFiles" / "dev.json").write_text(
        '{"secret": "fallback-ok"}\n', encoding="utf-8"
    )
    (main_wt / "android").mkdir(parents=True, exist_ok=True)
    (main_wt / "android" / "local.properties").write_text(
        "sdk.dir=/opt/android\n", encoding="utf-8"
    )

    real_run = stack_registry.subprocess.run
    cp_calls: list[list[str]] = []

    def failing_cp_run(
        cmd: Any, *args: Any, **kwargs: Any
    ) -> subprocess.CompletedProcess[Any]:
        if isinstance(cmd, list) and cmd[:3] == ["cp", "-c", "-R"]:
            cp_calls.append(list(cmd))
            return subprocess.CompletedProcess(
                cmd, 1, b"", b"cp: -c: cross-device link / unsupported filesystem"
            )
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(stack_registry.sys, "platform", "darwin")
    monkeypatch.setattr(stack_registry.subprocess, "run", failing_cp_run)

    created = manage_worker_pool.init_slots(
        repo, "plq_fr05", "plq-fr05", pool_size=1, epic_worktree_root=main_wt
    )
    slot1 = created[0]

    assert len(cp_calls) >= 3, f"Expected cp -c -R fallback attempts, got {cp_calls}"
    for rel_dir in (".dart_tool", "secureFiles"):
        dst = slot1 / rel_dir
        assert dst.is_dir() and not dst.is_symlink()
    assert (slot1 / ".dart_tool" / "package_config.json").read_text(
        encoding="utf-8"
    ) == '{"formatVersion": 2}\n'
    assert (slot1 / ".dart_tool" / "nested" / "build.txt").read_text(
        encoding="utf-8"
    ) == "nested-ok\n"
    assert (slot1 / "secureFiles" / "dev.json").read_text(
        encoding="utf-8"
    ) == '{"secret": "fallback-ok"}\n'
    assert (slot1 / "android" / "local.properties").is_file()
    assert not (slot1 / "android" / "local.properties").is_symlink()
    assert (slot1 / "android" / "local.properties").read_text(
        encoding="utf-8"
    ) == "sdk.dir=/opt/android\n"

    # Also verify Linux host skips cp -c -R directly and uses shutil.copytree / shutil.copy2
    repo_lin, main_lin, _ = _init_polyglot_pool_repo(
        tmp_path / "linux_host", epic_dir="plq_fr05_lin", epic_slug="plq-fr05-lin"
    )
    (main_lin / ".dart_tool").mkdir()
    (main_lin / ".dart_tool" / "package_config.json").write_text(
        '{"linux": true}\n', encoding="utf-8"
    )
    (main_lin / "secureFiles").mkdir()
    (main_lin / "secureFiles" / "dev.json").write_text(
        '{"linux": "ok"}\n', encoding="utf-8"
    )
    cp_calls.clear()
    monkeypatch.setattr(stack_registry.sys, "platform", "linux")
    slot_lin = manage_worker_pool.init_slots(
        repo_lin,
        "plq_fr05_lin",
        "plq-fr05-lin",
        pool_size=1,
        epic_worktree_root=main_lin,
    )[0]
    assert cp_calls == []
    assert (slot_lin / ".dart_tool").is_dir() and not (
        slot_lin / ".dart_tool"
    ).is_symlink()
    assert (slot_lin / "secureFiles" / "dev.json").read_text(
        encoding="utf-8"
    ) == '{"linux": "ok"}\n'


def test_plq_triage_fix_suffix_isolation_manifest_override_and_mount_exclusion(
    tmp_path: Path,
) -> None:
    """triage_fix_slot enforces suffix isolation, honors repo triage_surfaces overrides, and excludes mounts."""
    repo, main_wt, _home, slot1 = _setup_slot_in_fix_pass_1(
        tmp_path,
        initial_files={
            "lib/service.dart": "String greeting() {\n  return 'hi';\n}\n",
            "feature/wallet/Helper.kt": "private fun helper(): Int = 1\n",
            ".agents/quality/flutter-quality.json": json.dumps(
                {
                    "schema_version": 1,
                    "triage_surfaces": {
                        "signature": ["CustomBridgeChannel"],
                    },
                },
                indent=2,
            )
            + "\n",
        },
        epic_dir="plq_iso",
        epic_slug="plq-iso",
    )

    # Materialize ignored .dart_tool and secureFiles in slot1 and mutate them during Fix Pass 1
    (main_wt / ".dart_tool").mkdir(exist_ok=True)
    (main_wt / ".dart_tool" / "package_config.json").write_text("{}", encoding="utf-8")
    (main_wt / "secureFiles").mkdir(exist_ok=True)
    (main_wt / "secureFiles" / "dev.json").write_text("{}", encoding="utf-8")
    materialized = manage_worker_pool.link_shared_caches(main_wt, slot1)
    assert ".dart_tool" in materialized
    assert "secureFiles" in materialized
    (slot1 / ".dart_tool" / "package_config.json").write_text(
        '{"changed": true}\n', encoding="utf-8"
    )
    (slot1 / "secureFiles" / "dev.json").write_text(
        '{"changed": "secret"}\n', encoding="utf-8"
    )

    # 1. Cross-language strings (Rust tokens in Dart, private fun in Kotlin) produce zero false positives
    (slot1 / "lib" / "service.dart").write_text(
        "String greeting() {\n  // unsafe fn tokio::spawn\n  return 'hello';\n}\n",
        encoding="utf-8",
    )
    (slot1 / "feature" / "wallet" / "Helper.kt").write_text(
        "private fun helper(): Int = 2\n", encoding="utf-8"
    )

    low_risk = manage_worker_pool.triage_fix_slot(
        repo,
        "plq_iso",
        "plq-iso",
        slot=1,
        task_id="task_05",
        epic_worktree_root=main_wt,
    )
    assert low_risk["tier1_status"] == "ELIGIBLE_FOR_SHORT_CIRCUIT", low_risk
    assert low_risk["triggers"] == []
    assert ".dart_tool/package_config.json" not in low_risk["changed_files"]
    assert "secureFiles/dev.json" not in low_risk["changed_files"]

    # 2. Manifest triage_surfaces override in flutter-quality.json triggers PUBLIC_SIGNATURE_CHANGED
    (slot1 / "lib" / "service.dart").write_text(
        "String greeting() {\n  final ch = CustomBridgeChannel();\n  return ch.toString();\n}\n",
        encoding="utf-8",
    )
    high_risk = manage_worker_pool.triage_fix_slot(
        repo,
        "plq_iso",
        "plq-iso",
        slot=1,
        task_id="task_05",
        epic_worktree_root=main_wt,
    )
    assert high_risk["tier1_status"] == "HIGH_RISK", high_risk
    assert "PUBLIC_SIGNATURE_CHANGED" in high_risk["triggers"]
    assert high_risk["bounded_diff"] is None


def test_plq_classify_tier1_diff_default_and_custom_registry() -> None:
    """_classify_tier1_diff preserves its 2-arg call signature (default registry) and supports custom registry."""
    numstat = b"1\t0\tmigrations/001_init.sql\x001\t0\tlib/bridge.dart\x00"
    unified = (
        "diff --git a/migrations/001_init.sql b/migrations/001_init.sql\n"
        "--- a/migrations/001_init.sql\n"
        "+++ b/migrations/001_init.sql\n"
        "@@ -0,0 +1 @@\n"
        "+ALTER TABLE users ADD COLUMN role TEXT;\n"
        "diff --git a/lib/bridge.dart b/lib/bridge.dart\n"
        "--- a/lib/bridge.dart\n"
        "+++ b/lib/bridge.dart\n"
        "@@ -0,0 +1 @@\n"
        "+final ch = MethodChannel('wallet');\n"
    )
    triggers, non_test, test_lines, files, bounded = (
        manage_worker_pool._classify_tier1_diff(numstat, unified)
    )
    assert triggers == ["PUBLIC_SIGNATURE_CHANGED", "DB_OR_PERSISTENCE_CHANGED"]
    assert non_test == 2
    assert test_lines == 0
    assert files == ["lib/bridge.dart", "migrations/001_init.sql"]
    assert bounded is None

    # link_shared_caches handles missing directories gracefully
    assert (
        manage_worker_pool.link_shared_caches(
            Path("/nonexistent/main"), Path("/nonexistent/slot")
        )
        == []
    )


class TestPlqWorkerPoolPolyglot_Integration:
    """Tier C integration suite providing provenance for all 5 assigned Task 05 scenarios."""

    def test_plq_hp_05_worker_pool_symlink_and_cow_mounts(self, tmp_path: Path) -> None:
        """[PLQ-HP-05] Worker pool materializes symlink caches and APFS/copytree COW trees without symlinking .dart_tool."""
        test_plq_hp_05_worker_pool_symlink_and_cow_mounts(tmp_path)

    def test_plq_st_03_repeated_sync_slot_preserves_cow_mounts(
        self, tmp_path: Path
    ) -> None:
        """[PLQ-ST-03] Repeated sync_slot preserves COW mounts and never deletes them during git clean."""
        _verify_plq_st_03_repeated_sync_slot_preserves_cow_mounts(tmp_path)

    def test_plq_st_04_finalize_slot_unstages_ignored_mounts_and_commits_tracked_xcconfig(
        self, tmp_path: Path
    ) -> None:
        """[PLQ-ST-04] finalize_slot unstages ignored mounts while committing edits to tracked xcconfig files."""
        _verify_plq_st_04_finalize_slot_unstages_ignored_mounts_and_commits_tracked_xcconfig(
            tmp_path
        )

    def test_plq_ar_04_polyglot_is_test_file_and_assertion_weakening(
        self, tmp_path: Path
    ) -> None:
        """[PLQ-AR-04] Polyglot _is_test_file classifies test files and assertion weakening accurately per language."""
        _verify_plq_ar_04_polyglot_is_test_file_and_assertion_weakening(tmp_path)

    def test_plq_fr_05_apfs_cow_failure_falls_back_to_shutil_copy(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """[PLQ-FR-05] APFS copy-on-write failure gracefully falls back to shutil.copytree on non-APFS or Linux hosts."""
        _verify_plq_fr_05_apfs_cow_failure_falls_back_to_shutil_copy(
            tmp_path, monkeypatch
        )
