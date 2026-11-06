#!/usr/bin/env python3
"""End-to-End Acceptance Verification for Multi-Epic Orchestration and Governance.

Covers: MEO-AR-02, MEO-HP-01, MEO-HP-02, MEO-HP-03, MEO-HP-04
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
RESUME_SCRIPT = REPO_ROOT / "scripts" / "resume_context.py"
SYNC_SCRIPT = SCRIPTS_DIR / "sync_task_status.py"
PACKAGE_SCRIPT = SCRIPTS_DIR / "package_epic.py"
READINESS_SCRIPT = SCRIPTS_DIR / "check_epic_readiness.py"
sys.path.insert(0, str(SCRIPTS_DIR))

from test_check_epic_readiness import build_ready_epic


def git_cmd(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def init_git_repo(root: Path) -> None:
    git_cmd(root, "init", "-q")
    git_cmd(root, "config", "user.email", "tester@example.com")
    git_cmd(root, "config", "user.name", "Tester")
    (root / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    git_cmd(root, "add", "README.md")
    git_cmd(root, "commit", "-m", "Initial commit", "-q")


def test_MEO_AR_02_bulk_promotion_synchronization(tmp_path: Path) -> None:
    """[MEO-AR-02] [Tier C - Integration] sync_task_status.py promote synchronizes task status across epic directory and features mirrors in all checkouts."""
    init_git_repo(tmp_path)
    build_ready_epic(tmp_path)

    epic_path = tmp_path / ".devtool" / "epic" / "demo_epic"
    features_path = tmp_path / ".devtool" / "features"

    # Set all demo_epic tasks to backlog initially
    for tf in epic_path.glob("task_*.md"):
        txt = tf.read_text(encoding="utf-8")
        txt = txt.replace('status: "todo"', 'status: "backlog"')
        tf.write_text(txt, encoding="utf-8")
        feat_f = features_path / tf.name
        feat_f.write_text(txt, encoding="utf-8")

    # Add a third task
    task_3_text = (epic_path / "task_1.md").read_text(encoding="utf-8")
    task_3_text = task_3_text.replace('id: "task_1"', 'id: "task_3"')
    task_3_text = task_3_text.replace("# Task 1", "# Task 3")
    (epic_path / "task_3.md").write_text(task_3_text, encoding="utf-8")
    (features_path / "task_3.md").write_text(task_3_text, encoding="utf-8")

    # Commit baseline
    git_cmd(tmp_path, "add", ".")
    git_cmd(tmp_path, "commit", "-m", "Setup 3 backlog tasks", "-q")

    # Execute promote
    res = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "promote", "demo_epic"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Promote failed: {res.stderr}"

    # Verify all 6 task files (3 in epic, 3 in features) are updated to todo
    for i in (1, 2, 3):
        ep_file = epic_path / f"task_{i}.md"
        feat_file = features_path / f"task_{i}.md"
        assert ep_file.is_file()
        assert feat_file.is_file()
        assert 'status: "todo"' in ep_file.read_text(encoding="utf-8")
        assert 'status: "todo"' in feat_file.read_text(encoding="utf-8")


def test_MEO_HP_01_to_04_end_to_end_multi_epic_governance(tmp_path: Path) -> None:
    """[Tier C - Integration] End-to-end multi-epic orchestration and governance lifecycle covering MEO-HP-01..MEO-HP-04."""
    init_git_repo(tmp_path)
    build_ready_epic(tmp_path)

    # Commit initial state
    git_cmd(tmp_path, "add", ".")
    git_cmd(tmp_path, "commit", "-m", "Initial ready epic", "-q")
    head_1 = git_cmd(tmp_path, "rev-parse", "--short", "HEAD").stdout.strip()
    assert head_1

    # 1. [MEO-HP-04] Gate 1 & Gate 2 structured approvals
    res_g1 = subprocess.run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--gate",
            "1",
            "--epic",
            "demo-epic",
            "--approved",
            "Market discovery and product spec",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_g1.returncode == 0
    res_g2 = subprocess.run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--gate",
            "2",
            "--epic",
            "demo-epic",
            "--approved",
            "HLD and 2 Kanban tasks",
            "--deviations",
            "SE-01",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_g2.returncode == 0

    # Verify gate query
    res_chk = subprocess.run(
        [sys.executable, str(RESUME_SCRIPT), "--check-gate", "2", "--epic", "demo-epic"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_chk.returncode == 0
    gate_data = json.loads(res_chk.stdout.strip())
    assert gate_data["gate"] == 2
    assert gate_data["deviations"] == "SE-01"

    # 2. [MEO-HP-03] Package epic with Spec Errata and verify handoff.md
    epic_path = tmp_path / ".devtool" / "epic" / "demo_epic"
    hld_en_file = epic_path / "demo_epic.en.md"
    hld_vi_file = epic_path / "demo_epic.vi.md"

    hld_en = hld_en_file.read_text(encoding="utf-8").replace(
        "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n",
        "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n- [Spec Errata](#spec-errata)\n",
    ) + "\n## Spec Errata\n\n- **[SE-01] Architecture**: Refine worker sync contract\n"
    hld_en_file.write_text(hld_en, encoding="utf-8")

    hld_vi = hld_vi_file.read_text(encoding="utf-8").replace(
        "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n",
        "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n- [Đính chính Đặc tả (Spec Errata)](#đính-chính-đặc-tả-spec-errata)\n",
    ) + "\n## Đính chính Đặc tả (Spec Errata)\n\n- **[SE-01] Kiến trúc**: Tinh chỉnh hợp đồng đồng bộ worker\n"
    hld_vi_file.write_text(hld_vi, encoding="utf-8")

    git_cmd(tmp_path, "add", ".")
    git_cmd(tmp_path, "commit", "-m", "Add Spec Errata to demo epic", "-q")
    head_2 = git_cmd(tmp_path, "rev-parse", "--short", "HEAD").stdout.strip()

    res_pkg = subprocess.run(
        [sys.executable, str(PACKAGE_SCRIPT), "demo_epic"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_pkg.returncode == 0, f"Package failed: {res_pkg.stderr}"

    handoff_path = epic_path / "handoff.md"
    assert handoff_path.is_file()
    assert f"- **Design commit**: `{head_2}`" in handoff_path.read_text(encoding="utf-8")

    # Re-anchor handoff via --revise
    (tmp_path / "note.txt").write_text("update", encoding="utf-8")
    git_cmd(tmp_path, "add", ".")
    git_cmd(tmp_path, "commit", "-m", "Post packaging tweak", "-q")
    head_3 = git_cmd(tmp_path, "rev-parse", "--short", "HEAD").stdout.strip()

    res_rev = subprocess.run(
        [
            sys.executable,
            str(PACKAGE_SCRIPT),
            "demo_epic",
            "--revise",
            "--reason",
            "Incorporate SE-01 refinement",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_rev.returncode == 0
    rev_content = handoff_path.read_text(encoding="utf-8")
    assert f"- **Design commit**: `{head_3}`" in rev_content
    assert f"(`{head_2}` -> `{head_3}`)" in rev_content
    assert "Incorporate SE-01 refinement" in rev_content

    # 3. [MEO-HP-01] Create dependent child epic and verify check-prereqs
    child_epic_path = tmp_path / ".devtool" / "epic" / "child_epic"
    child_epic_path.mkdir(parents=True, exist_ok=True)
    child_hld = """# Child Epic High-Level Design

## Table of Contents
- [Meta Data](#meta-data)
- [Requirements](#requirements)

## Meta Data
- **Epic**: `child-epic`
- **Status**: Draft
- **Depends on epic**: `demo-epic`

## Requirements
Child requirements.
"""
    (child_epic_path / "child_epic.en.md").write_text(child_hld, encoding="utf-8")
    (child_epic_path / "child_epic.vi.md").write_text(child_hld, encoding="utf-8")

    # demo-epic is Packaged (not Done), so check-prereqs should report blocker
    res_prereq_block = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "check-prereqs", "child_epic"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_prereq_block.returncode == 1
    assert "prerequisite epic 'demo_epic' is not Done" in res_prereq_block.stderr

    # 4. [MEO-HP-02] Check conflicts against disjoint queued epic
    disjoint_epic_path = tmp_path / ".devtool" / "epic" / "disjoint_epic"
    disjoint_epic_path.mkdir(parents=True, exist_ok=True)
    disjoint_hld = """# Disjoint Epic

## Table of Contents
- [Meta Data](#meta-data)
- [Requirements](#requirements)

## Meta Data
- **Epic**: `disjoint-epic`
- **Status**: Queued (backlog)
- **Depends on epic**: none

## Requirements
Disjoint.
"""
    (disjoint_epic_path / "disjoint_epic.en.md").write_text(disjoint_hld, encoding="utf-8")
    (disjoint_epic_path / "disjoint_epic.vi.md").write_text(disjoint_hld, encoding="utf-8")

    # Add task touching distinct file
    task_d = """---
id: "task_01_disjoint"
status: "backlog"
epic: "disjoint-epic"
order: "c1"
---

# Task 01: Disjoint

## Files
Allowed files:
- `src/distinct.py`
"""
    (disjoint_epic_path / "task_01_disjoint.md").write_text(task_d, encoding="utf-8")
    (tmp_path / ".devtool" / "features" / "task_01_disjoint.md").write_text(task_d, encoding="utf-8")

    res_conf = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "check-conflicts", "disjoint_epic"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_conf.returncode == 0
    assert "0 conflicts — safe for concurrent execution" in res_conf.stdout

    res_prom = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "promote", "disjoint_epic"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_prom.returncode == 0
    assert 'status: "todo"' in (disjoint_epic_path / "task_01_disjoint.md").read_text(encoding="utf-8")


class Test_Integration:
    """[Tier C - Integration] Test suite with integration runner provenance."""

    def test_MEO_AR_02_integration(self, tmp_path: Path) -> None:
        test_MEO_AR_02_bulk_promotion_synchronization(tmp_path)

    def test_MEO_HP_01_to_04_integration(self, tmp_path: Path) -> None:
        test_MEO_HP_01_to_04_end_to_end_multi_epic_governance(tmp_path)
