#!/usr/bin/env python3
"""Tests for conflict-aware concurrent epic backlog and bulk task promotion.

Covers: MEO-HP-02, MEO-EC-02, MEO-ST-01
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SYNC_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "dev-implementation"
    / "resources"
    / "scripts"
    / "sync_task_status.py"
)
sys.path.insert(0, str(SYNC_SCRIPT.parent))

from sync_task_status import (
    check_epic_file_conflicts,
    check_epic_prerequisites,
    promote_epic_tasks,
)


def git_cmd(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def init_git_repo(root: Path) -> None:
    git_cmd(root, "init")
    git_cmd(root, "config", "user.email", "test@example.com")
    git_cmd(root, "config", "user.name", "Test Runner")
    (root / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    git_cmd(root, "add", "README.md")
    git_cmd(root, "commit", "-m", "Initial commit")


def setup_epic_with_task(
    root: Path,
    epic_dir: str,
    epic_slug: str,
    task_name: str,
    task_status: str,
    allowed_files: list[str],
    *,
    depends_on: str = "none",
    epic_status: str = "In Progress",
) -> Path:
    epic_path = root / ".devtool" / "epic" / epic_dir
    epic_path.mkdir(parents=True, exist_ok=True)
    features_dir = root / ".devtool" / "features"
    features_dir.mkdir(parents=True, exist_ok=True)

    hld_en = f"""# Epic: {epic_slug}

## Meta Data

- **Epic**: `{epic_slug}`
- **Status**: {epic_status}
- **Depends on epic**: {depends_on}
"""
    (epic_path / f"{epic_dir}.en.md").write_text(hld_en, encoding="utf-8")
    (epic_path / f"{epic_dir}.vi.md").write_text(hld_en, encoding="utf-8")

    allowed_bullets = "\n".join(f"- `{f}`" for f in allowed_files)
    task_content = f"""---
id: "{task_name}"
status: "{task_status}"
epic: "{epic_slug}"
order: "c1"
---

# Task: {task_name}

## Files

Allowed files:
{allowed_bullets}

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | GREEN | echo ok | exit 0 | — |
"""
    task_epic_path = epic_path / f"{task_name}.md"
    task_epic_path.write_text(task_content, encoding="utf-8")

    # In features mirror
    if task_status == "done":
        done_dir = features_dir / "done"
        done_dir.mkdir(parents=True, exist_ok=True)
        (done_dir / f"{task_name}.md").write_text(task_content, encoding="utf-8")
    else:
        (features_dir / f"{task_name}.md").write_text(task_content, encoding="utf-8")

    return task_epic_path


def test_MEO_HP_02_check_conflicts_and_promote(tmp_path: Path) -> None:
    """[MEO-HP-02] [Tier C - Integration] Conflict-aware check-conflicts and promote transition a disjoint epic from backlog to todo."""
    init_git_repo(tmp_path)

    # epic_alpha: active epic with tasks in todo touching src/alpha.py
    setup_epic_with_task(
        tmp_path,
        "epic_alpha",
        "epic-alpha",
        "task_01_alpha",
        "todo",
        ["src/alpha.py"],
    )

    # epic_gamma: queued epic with tasks in backlog touching src/gamma.py, depends on none
    setup_epic_with_task(
        tmp_path,
        "epic_gamma",
        "epic-gamma",
        "task_01_gamma",
        "backlog",
        ["src/gamma.py"],
        depends_on="none",
        epic_status="Queued (backlog)",
    )

    # 1. check-conflicts CLI
    res_conflicts = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "check-conflicts", "epic_gamma"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_conflicts.returncode == 0, f"Stderr: {res_conflicts.stderr}"
    assert "0 conflicts — safe for concurrent execution" in res_conflicts.stdout

    # 2. promote CLI
    res_promote = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "promote", "epic_gamma"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_promote.returncode == 0, f"Stderr: {res_promote.stderr}"

    # Verify task in epic and features is now 'todo'
    epic_task = tmp_path / ".devtool" / "epic" / "epic_gamma" / "task_01_gamma.md"
    feat_task = tmp_path / ".devtool" / "features" / "task_01_gamma.md"
    assert 'status: "todo"' in epic_task.read_text(encoding="utf-8")
    assert 'status: "todo"' in feat_task.read_text(encoding="utf-8")


def test_MEO_EC_02_check_file_conflicts_glob_and_ignores_done(tmp_path: Path) -> None:
    """[MEO-EC-02] [Tier A - Unit] check_epic_file_conflicts ignores done tasks while detecting glob overlaps on active tasks."""
    init_git_repo(tmp_path)

    # epic_done: has only done tasks touching src/shared/core.py
    setup_epic_with_task(
        tmp_path,
        "epic_done",
        "epic-done",
        "task_01_done",
        "done",
        ["src/shared/core.py"],
        epic_status="Done",
    )

    # epic_active: has in-progress task with glob src/shared/*.py
    setup_epic_with_task(
        tmp_path,
        "epic_active",
        "epic-active",
        "task_01_active",
        "in-progress",
        ["src/shared/*.py"],
        epic_status="In Progress",
    )

    # epic_candidate: touches src/shared/core.py
    setup_epic_with_task(
        tmp_path,
        "epic_candidate",
        "epic-candidate",
        "task_01_candidate",
        "backlog",
        ["src/shared/core.py"],
    )

    conflicts = check_epic_file_conflicts(tmp_path, "epic_candidate")
    assert "epic-done" not in conflicts
    assert "epic-active" in conflicts
    assert "src/shared/core.py" in conflicts["epic-active"]


def test_MEO_ST_01_promote_blocks_on_prereqs_unless_forced(tmp_path: Path) -> None:
    """[MEO-ST-01] [Tier A - Unit] promote blocks on unfinished prerequisites unless --force is supplied."""
    init_git_repo(tmp_path)

    # epic_alpha: in progress
    setup_epic_with_task(
        tmp_path,
        "epic_alpha",
        "epic-alpha",
        "task_01_alpha",
        "in-progress",
        ["src/alpha.py"],
        epic_status="In Progress",
    )

    # epic_beta: depends on epic_alpha
    setup_epic_with_task(
        tmp_path,
        "epic_beta",
        "epic-beta",
        "task_01_beta",
        "backlog",
        ["src/beta.py"],
        depends_on="`epic_alpha`",
        epic_status="Queued (backlog)",
    )

    # 1. Promote without --force fails
    res_blocked = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "promote", "epic_beta"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_blocked.returncode == 1
    assert "prerequisite epic 'epic_alpha' is not Done" in res_blocked.stderr
    task_beta = tmp_path / ".devtool" / "epic" / "epic_beta" / "task_01_beta.md"
    assert 'status: "backlog"' in task_beta.read_text(encoding="utf-8")

    # 2. Promote with --force succeeds
    res_forced = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "promote", "epic_beta", "--force"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_forced.returncode == 0
    assert 'status: "todo"' in task_beta.read_text(encoding="utf-8")


class Test_Integration:
    """[Tier C - Integration] Test suite with integration runner provenance."""

    def test_MEO_HP_02_integration(self, tmp_path: Path) -> None:
        test_MEO_HP_02_check_conflicts_and_promote(tmp_path)
