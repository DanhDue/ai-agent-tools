"""Tier C integration tests for Task 01: Worktree task sync isolation and worker pool slot staging.

Covers BDD Scenarios:
- OHK-HP-01: Promote epic tasks inside an isolated worktree without mutating primary checkout
- OHK-EC-01: Finalize worker slot succeeds with gitignored .venv symlink and preserves tracked shared-contracts symlink
- OHK-ST-01: Archiving or promoting Epic A never dirties concurrent sibling Epic B worktree even with inherited Epic A files
- OHK-FR-01: archive-epic called for Epic A skips unrelated Epic B worktrees even when run from primary checkout
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
SYNC_SCRIPT = SCRIPTS_DIR / "sync_task_status.py"
POOL_SCRIPT = SCRIPTS_DIR / "manage_worker_pool.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import manage_worker_pool  # noqa: E402
import sync_task_status  # noqa: E402

STANDARD_GITIGNORE = (
    ".worktrees/\n"
    ".devtool/.memory.lock\n"
    ".devtool/assistant_state.md\n"
    ".devtool/activity_stream.log\n"
    ".devtool/state/\n"
    ".devtool/logs/\n"
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


def _isolated_env(home: Path, cwd: Path) -> dict[str, str]:
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
    return env


def _run_script(
    script: Path, cwd: Path, args: list[str], *, home: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(script), *args],
        cwd=cwd,
        env=_isolated_env(home, cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def _init_repo(
    tmp_path: Path,
    *,
    branch: str = "develop",
    extra_gitignore: str = "",
) -> tuple[Path, Path]:
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)

    _git(repo, "init", "-q", "-b", branch)
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / ".gitignore").write_text(
        STANDARD_GITIGNORE + extra_gitignore, encoding="utf-8"
    )
    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Initial commit")
    return repo, home


def _write_epic_and_task(
    root: Path,
    *,
    epic_dir: str,
    epic_slug: str,
    task_id: str,
    task_status: str,
    epic_status: str = "Queued (backlog)",
    allowed_file: str = "src/module.py",
) -> tuple[Path, Path]:
    epic_root = root / ".devtool" / "epic" / epic_dir
    epic_root.mkdir(parents=True, exist_ok=True)
    hld_path = epic_root / f"{epic_dir}.md"
    hld_path.write_text(
        f"# Epic: {epic_slug}\n\n"
        "## Meta Data\n\n"
        f"- **Epic**: `{epic_slug}`\n"
        f"- **Status**: {epic_status}\n"
        "- **Depends on epic**: none\n\n"
        "## Kanban Tasks Breakdown\n\n"
        f"- [Task](../../features/done/{task_id}.md)\n",
        encoding="utf-8",
    )

    task_md = (
        f'---\nid: "{task_id}"\nstatus: "{task_status}"\npriority: "high"\n'
        f'assignee: null\nepic: "{epic_slug}"\ndueDate: null\n'
        'created: "2026-11-26T00:00:00Z"\nmodified: "2026-11-26T00:00:00Z"\n'
        'completedAt: null\nlabels: ["architecture"]\norder: "a1"\n---\n\n'
        f"# Task: {task_id}\n\n"
        f"Epic: [{epic_slug}]({epic_dir}.md)\n\n"
        "## Files\n\n"
        "Allowed files:\n"
        f"- `{allowed_file}`\n\n"
        "## Verification\n\n"
        "| ID | Phase | Command | Expect | Needs |\n"
        "|---|---|---|---|---|\n"
        "| V1 | GREEN | `true` | exit 0 | — |\n"
    )
    epic_task = epic_root / f"{task_id}.md"
    epic_task.write_text(task_md, encoding="utf-8")

    if task_status == "done":
        done_dir = root / ".devtool" / "features" / "done"
        done_dir.mkdir(parents=True, exist_ok=True)
        mirror = done_dir / f"{task_id}.md"
        mirror.write_text(
            task_md.replace(
                f"({epic_dir}.md)", f"(../../epic/{epic_dir}/{epic_dir}.md)"
            ),
            encoding="utf-8",
        )
    else:
        feat_dir = root / ".devtool" / "features"
        feat_dir.mkdir(parents=True, exist_ok=True)
        mirror = feat_dir / f"{task_id}.md"
        mirror.write_text(
            task_md.replace(f"({epic_dir}.md)", f"(../epic/{epic_dir}/{epic_dir}.md)"),
            encoding="utf-8",
        )
    return epic_task, mirror


def _snapshot_tree(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if rel == ".git" or rel.startswith(".git/"):
            continue
        if path.is_symlink():
            snapshot[rel] = f"symlink:{os.readlink(path)}"
        elif path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            snapshot[rel] = f"file:{digest}"
        elif path.is_dir():
            snapshot[rel] = "dir"
    return snapshot


def test_ohk_hp_01_promote_in_isolated_worktree(tmp_path: Path) -> None:
    """[OHK-HP-01] [Tier C - Integration] Promote epic tasks inside an isolated worktree without mutating primary checkout."""
    repo, home = _init_repo(tmp_path, branch="develop")

    wt_iso = repo / ".worktrees" / "iso_epic"
    wt_iso.parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "worktree", "add", "-q", str(wt_iso), "-b", "epic/iso-epic", "develop")

    epic_task, feat_task = _write_epic_and_task(
        wt_iso,
        epic_dir="iso_epic",
        epic_slug="iso-epic",
        task_id="task_01_iso",
        task_status="backlog",
        epic_status="Queued (backlog)",
        allowed_file="src/iso.py",
    )
    _git(wt_iso, "add", "-A")
    _git(wt_iso, "commit", "-q", "-m", "Add iso_epic backlog task")

    res = _run_script(SYNC_SCRIPT, wt_iso, ["promote", "iso_epic"], home=home)
    assert res.returncode == 0, f"stderr={res.stderr}\nstdout={res.stdout}"
    assert "Promoted" in res.stdout

    assert 'status: "todo"' in epic_task.read_text(encoding="utf-8")
    assert 'status: "todo"' in feat_task.read_text(encoding="utf-8")
    assert _git(repo, "status", "--porcelain") == ""
    assert not (repo / ".devtool" / "epic" / "iso_epic").exists()
    assert not (repo / ".devtool" / "features").exists()


class Test_Integration:
    """[Tier C - Integration] Integration suite with runner provenance for OHK Cluster 1."""

    def test_ohk_hp_01_promote_in_isolated_worktree_integration(
        self, tmp_path: Path
    ) -> None:
        """[OHK-HP-01] [Tier C - Integration] Promote epic tasks inside an isolated worktree without mutating primary checkout."""
        test_ohk_hp_01_promote_in_isolated_worktree(tmp_path)

    def test_ohk_ec_01_finalize_slot_gitignored_venv_and_shared_contracts_symlink(
        self,
        tmp_path: Path,
    ) -> None:
        """[OHK-EC-01] [Tier C - Integration] Finalize worker slot succeeds with gitignored .venv symlink and preserves tracked shared-contracts symlink."""
        repo, home = _init_repo(
            tmp_path, branch="main", extra_gitignore=".venv\n.venv/\n"
        )

        contracts_hub = tmp_path / "shared_contracts_hub"
        contracts_hub.mkdir(parents=True, exist_ok=True)
        (contracts_hub / "api_contract.md").write_text(
            "# API Contract\n", encoding="utf-8"
        )
        (repo / "shared-contracts").symlink_to("../shared_contracts_hub")
        (repo / "src").mkdir(parents=True, exist_ok=True)
        (repo / "src" / "__init__.py").write_text("", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Track shared-contracts symlink")

        epic_dir = "pool_iso"
        epic_slug = "pool-iso"
        task_id = "task_01_pool"
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
        )

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
            "Scenario: [OHK-EC-01] [Tier C - Integration] Finalize slot\n"
            "Given a slot\nWhen finalize runs\nThen it succeeds\n"
            "```\n",
            encoding="utf-8",
        )
        task_md = (
            f'---\nid: "{task_id}"\nstatus: "in-progress"\nepic: "{epic_slug}"\n'
            'completedAt: null\nmodified: "2026-11-26T00:00:00Z"\n---\n\n'
            f"# {task_id}\n\nCovers: OHK-EC-01\n\n"
            "## Verification\n\n| ID | Phase | Command | Expect | Needs |\n"
            "|---|---|---|---|---|\n| V1 | GREEN | `true` | exit 0 | — |\n"
        )
        (epic_root / f"{task_id}.md").write_text(task_md, encoding="utf-8")
        (features_dir / f"{task_id}.md").write_text(task_md, encoding="utf-8")
        (main_wt / "tests").mkdir(parents=True, exist_ok=True)
        (main_wt / "tests" / f"test_{task_id}.py").write_text(
            "# Covers OHK-EC-01\ndef test_ok():\n    assert True\n", encoding="utf-8"
        )

        scripts_stub = (
            main_wt / "skills" / "dev-implementation" / "resources" / "scripts"
        )
        scripts_stub.mkdir(parents=True, exist_ok=True)
        (scripts_stub / "run_task_checks.py").write_text(
            "import sys\nprint('done gate: PASS')\nsys.exit(0)\n", encoding="utf-8"
        )
        (scripts_stub / "check_bdd_traceability.py").write_text(
            "import sys\nprint('PASS')\nsys.exit(0)\n", encoding="utf-8"
        )
        (scripts_stub / "sync_task_status.py").write_text(
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
        _git(main_wt, "add", "-A")
        _git(main_wt, "commit", "-q", "-m", "Seed pool epic")

        # Create gitignored .venv in main_wt so init_slots symlinks it into slot 1
        (main_wt / ".venv" / "bin").mkdir(parents=True, exist_ok=True)
        (main_wt / ".venv" / "bin" / "python").write_text(
            "#!/bin/sh\n", encoding="utf-8"
        )

        init_res = _run_script(
            POOL_SCRIPT, main_wt, ["init", epic_dir, "--pool-size", "1"], home=home
        )
        assert init_res.returncode == 0, init_res.stderr

        slot1 = manage_worker_pool.get_slot_path(repo, epic_dir, 1)
        assert (slot1 / ".venv").is_symlink()
        assert (slot1 / "shared-contracts").is_symlink()

        # Valid code edit + leftover review_audit_notes file that must be excluded
        (slot1 / "src" / "feature.py").write_text("VALUE = 42\n", encoding="utf-8")
        (
            slot1 / ".devtool" / "epic" / epic_dir / "review_audit_notes.jsonl"
        ).write_text('{"stale": true}\n', encoding="utf-8")

        fin_res = _run_script(
            POOL_SCRIPT,
            main_wt,
            [
                "finalize-slot",
                epic_dir,
                "--slot",
                "1",
                "--task",
                task_id,
                "--mode",
                "pass1-approved",
            ],
            home=home,
        )
        assert fin_res.returncode == 0, (
            f"stderr={fin_res.stderr}\nstdout={fin_res.stdout}"
        )
        assert "ignored by one of your .gitignore files" not in fin_res.stderr
        payload = json.loads(fin_res.stdout)
        assert payload["ok"] is True
        assert payload["merged"] is True

        committed_files = _git(
            main_wt, "show", "--pretty=format:", "--name-only", "HEAD"
        ).splitlines()
        assert "src/feature.py" in committed_files
        assert ".venv" not in committed_files
        assert not any("review_audit_notes" in name for name in committed_files)

        # Tracked shared-contracts symlink stays intact in HEAD and on disk; .venv symlink untouched on disk
        sc_entry = _git(main_wt, "ls-tree", "HEAD", "shared-contracts")
        assert sc_entry.startswith("120000 "), (
            f"Expected git symlink entry, got {sc_entry!r}"
        )
        assert (main_wt / "shared-contracts").is_symlink()
        assert (slot1 / "shared-contracts").is_symlink()
        assert (slot1 / ".venv").is_symlink()
        assert _git(main_wt, "ls-files", ".venv") == ""

    def test_ohk_st_01_archive_done_and_promote_isolate_sibling_epic_worktrees(
        self,
        tmp_path: Path,
    ) -> None:
        """[OHK-ST-01] [Tier C - Integration] Archiving or promoting Epic A never dirties concurrent sibling Epic B worktree even with inherited Epic A files."""
        repo, home = _init_repo(tmp_path, branch="develop")

        # Seed Epic A on develop so Epic B inherits .devtool/epic/epic_a/ from develop
        _write_epic_and_task(
            repo,
            epic_dir="epic_a",
            epic_slug="epic-a",
            task_id="task_01_a",
            task_status="backlog",
            epic_status="Queued (backlog)",
            allowed_file="src/a.py",
        )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Seed epic_a on develop")

        wt_a = repo / ".worktrees" / "epic_a"
        wt_b = repo / ".worktrees" / "epic_b"
        wt_a.parent.mkdir(parents=True, exist_ok=True)
        _git(repo, "worktree", "add", "-q", str(wt_a), "-b", "epic/epic-a", "develop")
        _git(repo, "worktree", "add", "-q", str(wt_b), "-b", "epic/epic-b", "develop")

        # Commit clean tracked Epic B tasks inside .worktrees/epic_b (which also inherited epic_a)
        _write_epic_and_task(
            wt_b,
            epic_dir="epic_b",
            epic_slug="epic-b",
            task_id="task_01_b",
            task_status="in-progress",
            epic_status="In Progress",
            allowed_file="src/b.py",
        )
        _git(wt_b, "add", "-A")
        _git(wt_b, "commit", "-q", "-m", "Seed epic_b tasks")
        assert _git(wt_b, "status", "--porcelain") == ""
        wt_b_before = _snapshot_tree(wt_b)

        # Mark Epic A task done in .worktrees/epic_a/.devtool/features/done/
        (wt_a / ".devtool" / "features" / "task_01_a.md").unlink()
        _write_epic_and_task(
            wt_a,
            epic_dir="epic_a",
            epic_slug="epic-a",
            task_id="task_01_a",
            task_status="done",
            epic_status="In Progress",
            allowed_file="src/a.py",
        )

        res_arch = _run_script(SYNC_SCRIPT, wt_a, ["archive-done"], home=home)
        assert res_arch.returncode == 0, (
            f"stderr={res_arch.stderr}\nstdout={res_arch.stdout}"
        )

        assert (wt_a / ".devtool" / "epic" / "epic_a" / "task_01_a.md").is_file()
        assert not (wt_a / ".devtool" / "features" / "done" / "task_01_a.md").exists()
        assert "**Status**: Done" in (
            wt_a / ".devtool" / "epic" / "epic_a" / "epic_a.md"
        ).read_text(encoding="utf-8")
        assert _git(wt_b, "status", "--porcelain") == ""
        assert _snapshot_tree(wt_b) == wt_b_before

        # Invoking epic_checkout_roots("epic_a") and `promote epic_a` from inside .worktrees/epic_b
        prev_cwd = Path.cwd()
        try:
            os.chdir(wt_b)
            resolved_roots = [
                p.resolve() for p in sync_task_status.epic_checkout_roots("epic_a")
            ]
        finally:
            os.chdir(prev_cwd)
        assert wt_b.resolve() not in resolved_roots
        assert wt_a.resolve() in resolved_roots

        res_prom = _run_script(SYNC_SCRIPT, wt_b, ["promote", "epic_a"], home=home)
        assert res_prom.returncode == 0, (
            f"stderr={res_prom.stderr}\nstdout={res_prom.stdout}"
        )
        assert _git(wt_b, "status", "--porcelain") == ""
        assert _snapshot_tree(wt_b) == wt_b_before
        assert 'status: "backlog"' in (
            wt_b / ".devtool" / "epic" / "epic_a" / "task_01_a.md"
        ).read_text(encoding="utf-8")

    def test_ohk_fr_01_archive_epic_from_primary_skips_sibling_epic_worktrees(
        self,
        tmp_path: Path,
    ) -> None:
        """[OHK-FR-01] [Tier C - Integration] archive-epic called for Epic A skips unrelated Epic B worktrees even when run from primary checkout."""
        repo, home = _init_repo(tmp_path, branch="develop")

        wt_b = repo / ".worktrees" / "epic_b"
        wt_b.parent.mkdir(parents=True, exist_ok=True)
        _git(repo, "worktree", "add", "-q", str(wt_b), "-b", "epic/epic-b", "develop")
        _write_epic_and_task(
            wt_b,
            epic_dir="epic_b",
            epic_slug="epic-b",
            task_id="task_01_b",
            task_status="in-progress",
            epic_status="In Progress",
            allowed_file="src/b.py",
        )
        _git(wt_b, "add", "-A")
        _git(wt_b, "commit", "-q", "-m", "Add epic_b work")
        wt_b_before = _snapshot_tree(wt_b)

        # Primary checkout on develop has Epic A done tasks
        _write_epic_and_task(
            repo,
            epic_dir="epic_a",
            epic_slug="epic-a",
            task_id="task_01_a",
            task_status="done",
            epic_status="In Progress",
            allowed_file="src/a.py",
        )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Add epic_a done task on develop")

        res = _run_script(SYNC_SCRIPT, repo, ["archive-epic", "epic_a"], home=home)
        assert res.returncode == 0, f"stderr={res.stderr}\nstdout={res.stdout}"
        assert (repo / ".devtool" / "epic" / "epic_a" / "task_01_a.md").is_file()
        assert not (repo / ".devtool" / "features" / "done" / "task_01_a.md").exists()

        assert _snapshot_tree(wt_b) == wt_b_before
        assert _git(wt_b, "status", "--porcelain") == ""
        assert not (wt_b / ".devtool" / "epic" / "epic_a").exists()
