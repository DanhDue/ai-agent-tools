#!/usr/bin/env python3
"""TDD & BDD acceptance suite for Task 03 orchestration hardening.

Covers: RSDH-HP-04, RSDH-HP-05, RSDH-EC-03, RSDH-EC-08, RSDH-ST-01, RSDH-ST-03, RSDH-ST-07, RSDH-FR-03
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
FINISH_SCRIPTS_DIR = (
    REPO_ROOT / "skills" / "finishing-a-development-branch" / "resources" / "scripts"
)
RESUME_SCRIPT = REPO_ROOT / "scripts" / "resume_context.py"
PACKAGE_SCRIPT = SCRIPTS_DIR / "package_epic.py"
READINESS_SCRIPT = SCRIPTS_DIR / "check_epic_readiness.py"
CONTRACT_SCRIPT = SCRIPTS_DIR / "check_task_contract.py"
SYNC_SCRIPT = SCRIPTS_DIR / "sync_task_status.py"
POOL_SCRIPT = SCRIPTS_DIR / "manage_worker_pool.py"
INTEGRATE_SCRIPT = FINISH_SCRIPTS_DIR / "integrate_branch.py"

for path_entry in (
    str(REPO_ROOT / "scripts"),
    str(SCRIPTS_DIR),
    str(FINISH_SCRIPTS_DIR),
):
    if path_entry not in sys.path:
        sys.path.insert(0, path_entry)

from test_check_epic_readiness import build_ready_epic  # noqa: E402

ISOLATED_GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test Dev",
    "GIT_AUTHOR_EMAIL": "tester@example.com",
    "GIT_COMMITTER_NAME": "Test Dev",
    "GIT_COMMITTER_EMAIL": "tester@example.com",
}


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    merged = {**os.environ, **ISOLATED_GIT_ENV}
    merged.pop("AGY_PROFILE", None)
    merged.pop("ANTIGRAVITY_PROFILE", None)
    if extra:
        merged.update(extra)
    return merged


def _run(
    cmd: list[str],
    *,
    cwd: Path,
    extra_env: dict[str, str] | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=_env(extra_env),
        capture_output=True,
        text=True,
        check=check,
    )


def _git(cwd: Path, *args: str) -> str:
    proc = _run(["git", "-C", str(cwd), *args], cwd=cwd, check=True)
    return proc.stdout.strip()


def _init_repo(root: Path, branch: str = "develop") -> None:
    _git(root, "init", "-q", "-b", branch)
    _git(root, "config", "user.email", "tester@example.com")
    _git(root, "config", "user.name", "Test Dev")


def _commit_all(root: Path, message: str) -> str:
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _set_task_status(
    root: Path, epic_dir: str, task_name: str, new_status: str
) -> None:
    epic_task = root / ".devtool" / "epic" / epic_dir / task_name
    feat_task = root / ".devtool" / "features" / task_name
    for path in (epic_task, feat_task):
        if path.is_file():
            updated = re.sub(
                r'^status:\s*"[^"]+"',
                f'status: "{new_status}"',
                path.read_text(encoding="utf-8"),
                count=1,
                flags=re.MULTILINE,
            )
            path.write_text(updated, encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _add_epic_files_for_slug(
    root: Path,
    epic_dir: str,
    epic_slug: str,
    task_id: str,
) -> None:
    """Create a second minimal valid epic inside an existing repository."""
    epic_path = root / ".devtool" / "epic" / epic_dir
    features_path = root / ".devtool" / "features"
    epic_path.mkdir(parents=True, exist_ok=True)
    features_path.mkdir(parents=True, exist_ok=True)

    spec_en = (
        f"# {epic_slug} Design\n\n## Table of Contents\n\n- [Overview](#overview)\n\n"
        "## Overview\n\nApproved.\n"
    )
    spec_vi = (
        f"# {epic_slug} Design\n\n## Mục lục\n\n- [Tổng quan](#tổng-quan)\n\n"
        "## Tổng quan\n\nĐã duyệt.\n"
    )
    (epic_path / f"2026-11-13-{epic_slug}-design.en.md").write_text(
        spec_en, encoding="utf-8"
    )
    (epic_path / f"2026-11-13-{epic_slug}-design.vi.md").write_text(
        spec_vi, encoding="utf-8"
    )

    hld_en = f"""# {epic_slug} HLD

## Table of Contents

- [Meta Data](#meta-data)
- [Verification Environment](#verification-environment)

## Meta Data

- **Status**: Draft (Gate 2 Pending)

## Verification Environment

Protected paths: scripts/verify.sh
Integration results: python3 -c "print('ok')" -> build/{epic_slug}.log
"""
    hld_vi = f"""# {epic_slug} HLD

## Mục lục

- [Dữ liệu mô tả](#dữ-liệu-mô-tả)

## Dữ liệu mô tả

- **Trạng thái**: Draft
"""
    (epic_path / f"{epic_dir}.en.md").write_text(hld_en, encoding="utf-8")
    (epic_path / f"{epic_dir}.vi.md").write_text(hld_vi, encoding="utf-8")

    task_md = f"""---
id: "{task_id}"
epic: "{epic_slug}"
status: "todo"
wave: 1
depends_on: []
---

# {task_id}

## Description
Sample task for {epic_slug}.

## Files Allowed
- `tool.py`

## Verification

| ID | Check | Command | Expect |
|---|---|---|---|
| V1 | Run | `python3 -c "import tool"` | exit 0 |
"""
    (epic_path / f"{task_id}.md").write_text(task_md, encoding="utf-8")
    (features_path / f"{task_id}.md").write_text(task_md, encoding="utf-8")


# ---------------------------------------------------------------------------
# [RSDH-HP-04] Wave-parallel handoff prompt & creator profile PIC stamping
# ---------------------------------------------------------------------------


def test_rsdh_hp_04_wave_parallel_handoff_and_creator_pic(tmp_path: Path) -> None:
    """[RSDH-HP-04] package_epic stamps creator PIC cleanly and handoff/emit-prompt enforce wave-parallel orchestration."""
    _init_repo(tmp_path)
    build_ready_epic(tmp_path)
    _commit_all(tmp_path, "Add demo epic")

    prof_home = tmp_path / "antigravity_homes" / "brother"
    prof_home.mkdir(parents=True)
    extra_env = {
        "HOME": str(prof_home),
        "ANTIGRAVITY_PROFILE": "brother",
        "USER": "nobody",
    }

    g1 = _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--gate",
            "1",
            "--epic",
            "demo-epic",
            "--approved",
            "Spec approved",
        ],
        cwd=tmp_path,
        extra_env=extra_env,
    )
    assert g1.returncode == 0, g1.stderr
    g2 = _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--gate",
            "2",
            "--epic",
            "demo-epic",
            "--approved",
            "HLD approved",
        ],
        cwd=tmp_path,
        extra_env=extra_env,
    )
    assert g2.returncode == 0, g2.stderr

    pkg = _run(
        [sys.executable, str(PACKAGE_SCRIPT), "demo_epic"],
        cwd=tmp_path,
        extra_env=extra_env,
    )
    assert pkg.returncode == 0, f"package_epic failed:\n{pkg.stdout}\n{pkg.stderr}"

    handoff_path = tmp_path / ".devtool" / "epic" / "demo_epic" / "handoff.md"
    handoff_text = handoff_path.read_text(encoding="utf-8")
    assert "<profile_account_id>" not in handoff_text
    assert re.search(r"PIC / Assigned Profile\*\*:\s*`?@?brother`?", handoff_text), (
        f"Expected stamped creator profile 'brother' in handoff.md, got:\n{handoff_text[:400]}"
    )
    for required_token in (
        "compute_execution_order.py",
        "--parallel",
        "python3 scripts/estimate_heartbeat.py",
        "manage_worker_pool.py",
        "cleanup",
        "English",
    ):
        assert required_token in handoff_text, (
            f"Missing '{required_token}' in rendered handoff.md"
        )
    assert (
        "skills/dev-implementation/resources/scripts/estimate_heartbeat.py"
        not in handoff_text
    )
    assert (REPO_ROOT / "scripts" / "estimate_heartbeat.py").is_file()
    assert "Sequentially execute each Kanban task" not in handoff_text

    emitted = _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--emit-prompt",
            "implement",
            "--epic",
            "demo-epic",
        ],
        cwd=tmp_path,
        extra_env=extra_env,
    )
    assert emitted.returncode == 0, emitted.stderr
    for required_token in (
        "compute_execution_order.py",
        "--parallel",
        "python3 scripts/estimate_heartbeat.py",
        "manage_worker_pool.py",
        "cleanup",
        "English",
        "Cross-Model Review",
    ):
        assert required_token in emitted.stdout, (
            f"Missing '{required_token}' in --emit-prompt implement output:\n{emitted.stdout}"
        )
    assert (
        "skills/dev-implementation/resources/scripts/estimate_heartbeat.py"
        not in emitted.stdout
    )
    assert "Sequentially execute each Kanban task" not in emitted.stdout

    tpl_text = (
        REPO_ROOT / "skills" / "dev-lifecycle" / "references" / "handoff-template.md"
    ).read_text(encoding="utf-8")
    assert (
        "workspace:" in tpl_text
        or 'workspace:"share"' in tpl_text
        or "share" in tpl_text
    )
    assert "--parallel" in tpl_text
    assert "python3 scripts/estimate_heartbeat.py" in tpl_text
    assert (
        "skills/dev-implementation/resources/scripts/estimate_heartbeat.py"
        not in tpl_text
    )
    assert "manage_worker_pool.py" in tpl_text
    assert "cleanup" in tpl_text
    assert "Sequentially execute each Kanban task" not in tpl_text


# ---------------------------------------------------------------------------
# [RSDH-EC-08] Profile folder name precedence & creator PIC auto-stamping
# ---------------------------------------------------------------------------


def test_rsdh_ec_08_creator_profile_auto_detection_and_pic_stamping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """[RSDH-EC-08] detect_current_profile prioritizes env/folder name over email ID and sync_window_title normalizes -/_."""
    import resume_context  # noqa: E402

    _init_repo(tmp_path)
    epic_dir = "runtime_sync_and_dashboard_hardening"
    epic_slug = "runtime-sync-and-dashboard-hardening"
    _add_epic_files_for_slug(tmp_path, epic_dir, epic_slug, "task_01_sample")
    (tmp_path / ".devtool" / "epic" / epic_dir / "handoff.md").write_text(
        "# Handoff\n\n- **PIC / Assigned Profile**: `epic_owner` (active)\n",
        encoding="utf-8",
    )
    _commit_all(tmp_path, "Add hyphenated-slug epic with underscore dir")

    # Even if email metadata exists inside the profile directory, folder name wins.
    prof_home = tmp_path / "antigravity_homes" / "brother"
    vsc_dir = prof_home / "User" / "globalStorage"
    vsc_dir.mkdir(parents=True)
    (prof_home / ".email").write_text("other@example.com\n", encoding="utf-8")

    res_folder = _run(
        [sys.executable, str(RESUME_SCRIPT), "--detect-profile"],
        cwd=tmp_path,
        extra_env={"HOME": str(prof_home), "USER": "fallback_os_user"},
    )
    assert res_folder.returncode == 0, res_folder.stderr
    assert res_folder.stdout.strip() == "brother"

    # Explicit AGY_PROFILE / ANTIGRAVITY_PROFILE overrides folder name.
    res_env = _run(
        [sys.executable, str(RESUME_SCRIPT), "--detect-profile"],
        cwd=tmp_path,
        extra_env={
            "HOME": str(prof_home),
            "ANTIGRAVITY_PROFILE": "ci-profile",
            "USER": "fallback_os_user",
        },
    )
    assert res_env.returncode == 0, res_env.stderr
    assert res_env.stdout.strip() == "ci-profile"

    # Fallback to .vscode/settings.json [@profile] when env & antigravity_homes are absent.
    plain_home = tmp_path / "plain_home"
    plain_home.mkdir()
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir()
    (vscode_dir / "settings.json").write_text(
        json.dumps({"window.title": f"{tmp_path.name} | other [@alice]"}),
        encoding="utf-8",
    )
    res_vscode = _run(
        [sys.executable, str(RESUME_SCRIPT), "--detect-profile"],
        cwd=tmp_path,
        extra_env={"HOME": str(plain_home), "USER": "fallback_os_user"},
    )
    assert res_vscode.returncode == 0, res_vscode.stderr
    assert res_vscode.stdout.strip() == "alice"

    # Direct function call & sync_window_title -/_ candidate lookup.
    monkeypatch.setenv("HOME", str(prof_home))
    monkeypatch.delenv("AGY_PROFILE", raising=False)
    monkeypatch.delenv("ANTIGRAVITY_PROFILE", raising=False)
    assert resume_context.detect_current_profile(tmp_path) == "brother"

    resume_context.sync_window_title(tmp_path, epic_slug=epic_slug)
    settings_data = _read_json(vscode_dir / "settings.json")
    assert "[@epic_owner]" in settings_data["window.title"]


# ---------------------------------------------------------------------------
# [RSDH-EC-03] Stage 3 --revise contract compatibility vs Stage 2 strictness
# ---------------------------------------------------------------------------


def test_rsdh_ec_03_stage3_revise_vs_stage2_strict(tmp_path: Path) -> None:
    """[RSDH-EC-03] Stage 3 --revise allows existing (new) paths owned by done/review/in-progress tasks while keeping todo collisions and duplicates strict."""
    _init_repo(tmp_path)
    build_ready_epic(tmp_path)

    epic_path = tmp_path / ".devtool" / "epic" / "demo_epic"
    hld_en_file = epic_path / "demo_epic.en.md"
    hld_vi_file = epic_path / "demo_epic.vi.md"

    # Update task_1 to declare src/done_mod.py (new) and evidence/done_report.json (new),
    # and task_2 (todo) to declare src/future_mod.py (new).
    for prefix_path in (
        epic_path / "task_1.md",
        tmp_path / ".devtool" / "features" / "task_1.md",
    ):
        txt = prefix_path.read_text(encoding="utf-8")
        txt = txt.replace(
            "`tool.py`",
            "`tool.py`\n- `src/done_mod.py` (new)\n- `.devtool/epic/demo_epic/evidence/done_report.json` (new)",
        )
        prefix_path.write_text(txt, encoding="utf-8")

    for prefix_path in (
        epic_path / "task_2.md",
        tmp_path / ".devtool" / "features" / "task_2.md",
    ):
        txt = prefix_path.read_text(encoding="utf-8")
        txt = txt.replace(
            "`tool.py`",
            "`tool.py`\n- `src/future_mod.py` (new)",
        )
        prefix_path.write_text(txt, encoding="utf-8")

    _commit_all(tmp_path, "Stage 2 ready epic before packaging")

    # Stage 2 initial packaging succeeds cleanly before (new) files are created.
    g1 = _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--gate",
            "1",
            "--epic",
            "demo-epic",
            "--approved",
            "G1",
        ],
        cwd=tmp_path,
    )
    assert g1.returncode == 0
    g2 = _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--gate",
            "2",
            "--epic",
            "demo-epic",
            "--approved",
            "G2",
        ],
        cwd=tmp_path,
    )
    assert g2.returncode == 0
    init_pkg = _run(
        [sys.executable, str(PACKAGE_SCRIPT), "demo_epic"],
        cwd=tmp_path,
        extra_env={"ANTIGRAVITY_PROFILE": "brother"},
    )
    assert init_pkg.returncode == 0, (
        f"Initial package failed:\n{init_pkg.stdout}\n{init_pkg.stderr}"
    )
    _commit_all(tmp_path, "Package initial handoff")

    # Now create task_1's artifacts while task_1 is still `todo` -> Stage 2 strict check MUST fail!
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "done_mod.py").write_text("VALUE = 1\n", encoding="utf-8")
    ev_dir = epic_path / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)
    (ev_dir / "done_report.json").write_text('{"ok": true}\n', encoding="utf-8")
    _commit_all(tmp_path, "Create task_1 artifacts")

    # Stage 2 baseline check MUST fail when (new) file already exists without --allow-existing-done-new.
    contract_stage2 = _run(
        [
            sys.executable,
            str(CONTRACT_SCRIPT),
            "--design",
            "--hld",
            str(hld_en_file),
            "--tasks",
            str(epic_path / "task_1.md"),
            str(epic_path / "task_2.md"),
        ],
        cwd=tmp_path,
    )
    assert contract_stage2.returncode != 0
    assert "marked (new) but already exists" in contract_stage2.stdout

    readiness_stage2 = _run(
        [sys.executable, str(READINESS_SCRIPT), "demo_epic"],
        cwd=tmp_path,
    )
    assert readiness_stage2.returncode != 0

    # Transition task_1 through done/review/in-progress -> Stage 3 allows existing (new) paths owned by those tasks.
    for allowed_status in ("done", "review", "in-progress"):
        _set_task_status(tmp_path, "demo_epic", "task_1.md", allowed_status)
        contract_stage3 = _run(
            [
                sys.executable,
                str(CONTRACT_SCRIPT),
                "--design",
                "--allow-existing-done-new",
                "--hld",
                str(hld_en_file),
                "--tasks",
                str(epic_path / "task_1.md"),
                str(epic_path / "task_2.md"),
            ],
            cwd=tmp_path,
        )
        assert contract_stage3.returncode == 0, (
            f"Expected --allow-existing-done-new PASS for {allowed_status}:\n{contract_stage3.stdout}"
        )

    _set_task_status(tmp_path, "demo_epic", "task_1.md", "done")
    _commit_all(tmp_path, "Mark task_1 done")

    # check_epic_readiness --post-design passes in Stage 3.
    readiness_stage3 = _run(
        [sys.executable, str(READINESS_SCRIPT), "--post-design", "demo_epic"],
        cwd=tmp_path,
    )
    assert readiness_stage3.returncode == 0, (
        f"Expected readiness --post-design PASS:\n{readiness_stage3.stdout}"
    )

    # Seed Gate 3 approval, Spec Errata, and pending_decision on demo-epic.
    g3 = _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--gate",
            "3",
            "--epic",
            "demo-epic",
            "--approved",
            "Execution started",
        ],
        cwd=tmp_path,
    )
    assert g3.returncode == 0, g3.stderr

    pd = _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--pending-decision",
            "Approve Stage 3 revision",
            "--decision-kind",
            "revise",
            "--epic",
            "demo-epic",
        ],
        cwd=tmp_path,
    )
    assert pd.returncode == 0, pd.stderr

    hld_en_file.write_text(
        hld_en_file.read_text(encoding="utf-8").replace(
            "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n",
            "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n- [Spec Errata](#spec-errata)\n",
        )
        + "\n## Spec Errata\n\n- **[SE-01] Scope**: Stage 3 revision\n",
        encoding="utf-8",
    )
    hld_vi_file.write_text(
        hld_vi_file.read_text(encoding="utf-8").replace(
            "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n",
            "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n- [Đính chính Đặc tả (Spec Errata)](#đính-chính-đặc-tả-spec-errata)\n",
        )
        + "\n## Đính chính Đặc tả (Spec Errata)\n\n- **[SE-01] Phạm vi**: Đính chính Stage 3\n",
        encoding="utf-8",
    )
    _commit_all(tmp_path, "Stage 3 revision ready")

    revise_proc = _run(
        [
            sys.executable,
            str(PACKAGE_SCRIPT),
            "--revise",
            "--reason",
            "Stage 3 revision",
            "demo_epic",
        ],
        cwd=tmp_path,
        extra_env={"ANTIGRAVITY_PROFILE": "brother"},
    )
    assert revise_proc.returncode == 0, (
        f"--revise failed:\n{revise_proc.stdout}\n{revise_proc.stderr}"
    )
    pd_data = _read_json(tmp_path / ".devtool" / "state" / "pending_decision.json")
    assert "demo-epic" not in pd_data.get("decisions", {})

    # Still STRICT when a `todo` task claims an already-existing (new) path.
    (tmp_path / "src" / "future_mod.py").write_text(
        "COLLISION = True\n", encoding="utf-8"
    )
    _commit_all(tmp_path, "Create todo collision file")
    todo_collision = _run(
        [
            sys.executable,
            str(CONTRACT_SCRIPT),
            "--design",
            "--allow-existing-done-new",
            "--hld",
            str(hld_en_file),
            "--tasks",
            str(epic_path / "task_1.md"),
            str(epic_path / "task_2.md"),
        ],
        cwd=tmp_path,
    )
    assert todo_collision.returncode != 0
    assert "marked (new) but already exists" in todo_collision.stdout

    # Still STRICT when two tasks duplicate the same (new) claim.
    (tmp_path / "src" / "future_mod.py").unlink()
    _commit_all(tmp_path, "Remove collision file")
    for p in (
        epic_path / "task_2.md",
        tmp_path / ".devtool" / "features" / "task_2.md",
    ):
        p.write_text(
            p.read_text(encoding="utf-8").replace(
                "`src/future_mod.py` (new)", "`src/done_mod.py` (new)"
            ),
            encoding="utf-8",
        )
    dup_claim = _run(
        [
            sys.executable,
            str(CONTRACT_SCRIPT),
            "--design",
            "--allow-existing-done-new",
            "--hld",
            str(hld_en_file),
            "--tasks",
            str(epic_path / "task_1.md"),
            str(epic_path / "task_2.md"),
        ],
        cwd=tmp_path,
    )
    assert dup_claim.returncode != 0
    assert (
        "duplicate" in dup_claim.stdout.lower()
        or "multiple tasks" in dup_claim.stdout.lower()
    )


# ---------------------------------------------------------------------------
# [RSDH-ST-07] Worker pool cleanup preservation of dirty/unmerged/missing worktrees
# ---------------------------------------------------------------------------


def test_rsdh_st_07_pool_cleanup_preserves_dirty_unmerged_and_missing_wt(
    tmp_path: Path,
) -> None:
    """[RSDH-ST-07] cleanup preserves dirty worktrees, unmerged commits, and missing-worktree unmerged branches until --discard-unmerged."""
    _init_repo(tmp_path, branch="develop")
    (tmp_path / "app.py").write_text("v = 0\n", encoding="utf-8")
    _commit_all(tmp_path, "Base commit on develop")

    # Create epic worktree on epic/demo-epic so develop stays checked out in tmp_path.
    epic_wt = tmp_path / ".worktrees" / "demo_epic"
    _git(
        tmp_path,
        "worktree",
        "add",
        "-q",
        str(epic_wt),
        "-b",
        "epic/demo-epic",
        "develop",
    )
    (epic_wt / "app.py").write_text("v = 1\n", encoding="utf-8")
    _commit_all(epic_wt, "Epic base commit")

    init_res = _run(
        [sys.executable, str(POOL_SCRIPT), "init", "demo_epic", "--pool-size", "2"],
        cwd=epic_wt,
    )
    assert init_res.returncode == 0, init_res.stderr

    slot1_wt = tmp_path / ".worktrees" / "demo_epic-slot-1"
    slot2_wt = tmp_path / ".worktrees" / "demo_epic-slot-2"
    assert slot1_wt.is_dir() and slot2_wt.is_dir()

    # 1. Dirty slot-1 preserved while clean merged slot-2 is cleaned.
    (slot1_wt / "untracked.txt").write_text("unsaved work\n", encoding="utf-8")
    dirty_cleanup = _run(
        [sys.executable, str(POOL_SCRIPT), "cleanup", "demo_epic", "--pool-size", "2"],
        cwd=epic_wt,
    )
    assert dirty_cleanup.returncode != 0
    assert slot1_wt.is_dir()
    assert not slot2_wt.is_dir()
    hb = _read_json(tmp_path / ".devtool" / "state" / "demo-epic.heartbeat.json")
    assert "slot-1" in hb.get("slots", {})
    assert "slot-2" not in hb.get("slots", {})

    # 2. Unmerged commit inside clean slot-1 preserved by default.
    (slot1_wt / "untracked.txt").unlink()
    (slot1_wt / "feature_unmerged.py").write_text("ready = False\n", encoding="utf-8")
    _commit_all(slot1_wt, "Unmerged work in slot-1")
    unmerged_cleanup = _run(
        [sys.executable, str(POOL_SCRIPT), "cleanup", "demo_epic", "--pool-size", "2"],
        cwd=epic_wt,
    )
    assert unmerged_cleanup.returncode != 0
    assert slot1_wt.is_dir()

    # 3. Missing worktree dir + unmerged orphan branch worker/<epic>/slot-3 preserved;
    #    merged orphan worker/<epic>/slot-4 cleaned; --stale-only handles stale metadata cleanly.
    _git(epic_wt, "branch", "worker/demo-epic/slot-4", "epic/demo-epic")
    shutil.rmtree(slot1_wt)
    # Create unmerged orphan worker/demo-epic/slot-3 off detached branch commit
    _git(
        tmp_path,
        "checkout",
        "-q",
        "-b",
        "worker/demo-epic/slot-3",
        "epic/demo-epic-slot-1",
    )
    _git(tmp_path, "checkout", "-q", "develop")

    stale_res = _run(
        [
            sys.executable,
            str(POOL_SCRIPT),
            "cleanup",
            "demo_epic",
            "--pool-size",
            "2",
            "--stale-only",
        ],
        cwd=epic_wt,
    )
    assert stale_res.returncode != 0
    branches_after_stale = _git(epic_wt, "branch", "--list")
    assert "epic/demo-epic-slot-1" in branches_after_stale
    assert "worker/demo-epic/slot-3" in branches_after_stale
    assert "worker/demo-epic/slot-4" not in branches_after_stale

    # Force discard removes preserved unmerged slot & orphan branch cleanly.
    force_res = _run(
        [
            sys.executable,
            str(POOL_SCRIPT),
            "cleanup",
            "demo_epic",
            "--pool-size",
            "2",
            "--discard-unmerged",
        ],
        cwd=epic_wt,
    )
    assert force_res.returncode == 0, (
        f"Forced cleanup failed:\n{force_res.stdout}\n{force_res.stderr}"
    )
    branches_after_force = _git(epic_wt, "branch", "--list")
    assert "epic/demo-epic-slot-1" not in branches_after_force
    assert "worker/demo-epic/slot-3" not in branches_after_force


# ---------------------------------------------------------------------------
# [RSDH-ST-03] Stale worker pool pruning & branch landing orphan cleanup
# ---------------------------------------------------------------------------


def test_rsdh_st_03_stale_pool_pruning_and_branch_landing(tmp_path: Path) -> None:
    """[RSDH-ST-03] First-pass stale cleanup prunes missing merged slot worktrees/branches and land removes merged orphans."""
    _init_repo(tmp_path, branch="develop")
    (tmp_path / "app.py").write_text("v = 0\n", encoding="utf-8")
    _commit_all(tmp_path, "Base commit on develop")

    epic_wt = tmp_path / ".worktrees" / "demo_epic"
    _git(
        tmp_path,
        "worktree",
        "add",
        "-q",
        str(epic_wt),
        "-b",
        "epic/demo-epic",
        "develop",
    )
    (epic_wt / "app.py").write_text("v = 1\n", encoding="utf-8")
    _commit_all(epic_wt, "Epic base commit")

    init_res = _run(
        [sys.executable, str(POOL_SCRIPT), "init", "demo_epic", "--pool-size", "2"],
        cwd=epic_wt,
    )
    assert init_res.returncode == 0, init_res.stderr
    slot1_wt = tmp_path / ".worktrees" / "demo_epic-slot-1"
    slot2_wt = tmp_path / ".worktrees" / "demo_epic-slot-2"
    assert slot1_wt.is_dir() and slot2_wt.is_dir()

    # Delete merged slot-1 worktree dir manually WITHOUT prior prune; first-pass cleanup must prune and delete branch cleanly.
    shutil.rmtree(slot1_wt)
    first_pass = _run(
        [
            sys.executable,
            str(POOL_SCRIPT),
            "cleanup",
            "demo_epic",
            "--pool-size",
            "2",
            "--stale-only",
        ],
        cwd=epic_wt,
    )
    assert first_pass.returncode == 0, (
        f"First-pass stale cleanup failed:\n{first_pass.stdout}\n{first_pass.stderr}"
    )
    assert "epic/demo-epic-slot-1" not in _git(epic_wt, "branch", "--list")
    assert "demo_epic-slot-1" not in _git(epic_wt, "worktree", "list")
    assert slot2_wt.is_dir()  # Live slot-2 left intact in --stale-only mode

    full_clean = _run(
        [sys.executable, str(POOL_SCRIPT), "cleanup", "demo_epic", "--pool-size", "2"],
        cwd=epic_wt,
    )
    assert full_clean.returncode == 0, full_clean.stderr

    # integrate_branch.py land cleans merged worker/demo-epic/slot-5 while preserving unmerged worker/demo-epic/slot-6.
    _git(epic_wt, "branch", "worker/demo-epic/slot-5", "epic/demo-epic")
    _git(epic_wt, "branch", "worker/demo-epic/slot-6", "epic/demo-epic")
    slot6_wt = tmp_path / ".worktrees" / "slot6"
    _git(tmp_path, "worktree", "add", "-q", str(slot6_wt), "worker/demo-epic/slot-6")
    (slot6_wt / "extra_unmerged.py").write_text("keep = True\n", encoding="utf-8")
    _commit_all(slot6_wt, "Unmerged orphan work")
    _git(tmp_path, "worktree", "remove", str(slot6_wt))

    verified_sha = _git(epic_wt, "rev-parse", "HEAD")
    land_res = _run(
        [
            sys.executable,
            str(INTEGRATE_SCRIPT),
            "land",
            "--base",
            "develop",
            "--no-fetch",
            "--verified",
            verified_sha,
            "--title",
            "[DEMO_EPIC] Land demo epic",
            "--format",
            "json",
        ],
        cwd=epic_wt,
    )
    assert land_res.returncode == 0, (
        f"integrate_branch land failed:\n{land_res.stdout}\n{land_res.stderr}"
    )
    branches_after_land = _git(tmp_path, "branch", "--list")
    assert "worker/demo-epic/slot-5" not in branches_after_land
    assert "worker/demo-epic/slot-6" in branches_after_land


def test_round1_pool_cleanup_fails_closed_on_status_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """cleanup_slots_report must fail closed (treat as dirty) when git status --porcelain errors."""
    import manage_worker_pool  # noqa: E402

    _init_repo(tmp_path, branch="develop")
    (tmp_path / "app.py").write_text("v = 0\n", encoding="utf-8")
    _commit_all(tmp_path, "Base commit on develop")
    epic_wt = tmp_path / ".worktrees" / "demo_epic"
    _git(
        tmp_path,
        "worktree",
        "add",
        "-q",
        str(epic_wt),
        "-b",
        "epic/demo-epic",
        "develop",
    )
    init_res = _run(
        [sys.executable, str(POOL_SCRIPT), "init", "demo_epic", "--pool-size", "1"],
        cwd=epic_wt,
    )
    assert init_res.returncode == 0, init_res.stderr

    slot1_wt = tmp_path / ".worktrees" / "demo_epic-slot-1"
    real_run = subprocess.run
    rm_called: list[list[str]] = []

    def _mock_run(cmd: list[str], *args: Any, **kwargs: Any) -> Any:
        if (
            cmd[:3] == ["git", "status", "--porcelain"]
            and kwargs.get("cwd") == slot1_wt
        ):
            return subprocess.CompletedProcess(
                cmd, returncode=128, stdout="", stderr="fatal: index corrupt"
            )
        if cmd[:3] == ["git", "worktree", "remove"]:
            rm_called.append(cmd)
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(manage_worker_pool.subprocess, "run", _mock_run)
    report = manage_worker_pool.cleanup_slots_report(
        tmp_path,
        tmp_path / ".devtool" / "epic" / "demo_epic",
        "demo_epic",
        pool_size=1,
    )
    assert report["ok"] is False
    assert "epic/demo-epic-slot-1" in report["preserved_dirty"]
    assert slot1_wt.is_dir()
    assert not rm_called


# ---------------------------------------------------------------------------
# [RSDH-ST-01] Per-epic pending_decision isolation & cross-worktree clear
# ---------------------------------------------------------------------------


def test_rsdh_st_01_pending_decision_per_epic_isolation_and_clear(
    tmp_path: Path,
) -> None:
    """[RSDH-ST-01] Concurrent epics keep isolated pending_decision entries across root and worktree."""
    _init_repo(tmp_path, branch="develop")
    (tmp_path / "tool.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Root\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "verify.sh").write_text(
        "#!/bin/sh\nexit 0\n", encoding="utf-8"
    )
    _add_epic_files_for_slug(tmp_path, "epic_a", "epic-a", "task_a1")
    _add_epic_files_for_slug(tmp_path, "epic_b", "epic-b", "task_b1")
    _commit_all(tmp_path, "Setup epic-a and epic-b")

    wt = tmp_path / ".worktrees" / "epic_b"
    _git(tmp_path, "worktree", "add", "-q", str(wt), "-b", "epic/epic-b", "develop")

    # Pause both epics via CLI producer flags.
    p_a = _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--pending-decision",
            "Approve Gate 2 for A",
            "--decision-kind",
            "gate_2",
            "--decision-id",
            "dec-a",
            "--epic",
            "epic-a",
        ],
        cwd=tmp_path,
    )
    assert p_a.returncode == 0, p_a.stderr

    p_b = _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--pending-decision",
            "Approve Gate 2 for B",
            "--decision-kind",
            "gate_2",
            "--decision-id",
            "dec-b",
            "--epic",
            "epic-b",
        ],
        cwd=wt,
    )
    assert p_b.returncode == 0, p_b.stderr

    pd_file = tmp_path / ".devtool" / "state" / "pending_decision.json"
    pd_data = _read_json(pd_file)
    assert set(pd_data["decisions"].keys()) == {"epic-a", "epic-b"}
    assert pd_data["decisions"]["epic-a"]["decision_id"] == "dec-a"
    assert pd_data["decisions"]["epic-b"]["decision_id"] == "dec-b"

    # Paused --state keeps epic-a pending decision intact.
    paused_state = _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--epic",
            "epic-a",
            "--state",
            "--status",
            "Waiting for Gate 2 approval",
        ],
        cwd=tmp_path,
    )
    assert paused_state.returncode == 0, paused_state.stderr
    assert "epic-a" in _read_json(pd_file)["decisions"]

    # Wrong decision_id does NOT clear dec-a.
    wrong_clear = _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--clear-decision",
            "--decision-id",
            "wrong-id",
            "--epic",
            "epic-a",
        ],
        cwd=tmp_path,
    )
    assert wrong_clear.returncode == 0
    assert "epic-a" in _read_json(pd_file)["decisions"]

    # sync_task_status.py marks epic-b task in-progress -> clears ONLY epic-b.
    sync_b = _run(
        [sys.executable, str(SYNC_SCRIPT), "task", "task_b1", "in-progress"],
        cwd=wt,
    )
    assert sync_b.returncode == 0, sync_b.stderr
    after_sync = _read_json(pd_file)["decisions"]
    assert "epic-b" not in after_sync
    assert "epic-a" in after_sync

    # Re-pause epic-b and verify --gate clears ONLY epic-b while keeping epic-a.
    _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--pending-decision",
            "Approve Gate 2 again",
            "--epic",
            "epic-b",
        ],
        cwd=tmp_path,
    )
    g_b = _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--gate",
            "2",
            "--epic",
            "epic-b",
            "--approved",
            "Approved B",
        ],
        cwd=wt,
    )
    assert g_b.returncode == 0, g_b.stderr
    after_gate = _read_json(pd_file)["decisions"]
    assert "epic-b" not in after_gate
    assert "epic-a" in after_gate

    # Clear epic-a cleanly with matching decision_id from worktree.
    clear_a = _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--clear-decision",
            "--decision-id",
            "dec-a",
            "--epic",
            "epic-a",
        ],
        cwd=wt,
    )
    assert clear_a.returncode == 0, clear_a.stderr
    assert _read_json(pd_file)["decisions"] == {}


# ---------------------------------------------------------------------------
# [RSDH-HP-05] Worker pool live slot & wave heartbeat updates + clean cleanup
# ---------------------------------------------------------------------------


def test_rsdh_hp_05_worker_pool_slot_and_wave_heartbeat_updates(tmp_path: Path) -> None:
    """[RSDH-HP-05] manage_worker_pool init/sync/merge/cleanup and resume_context --wave update per-epic heartbeat.json."""
    import manage_worker_pool  # noqa: E402

    assert manage_worker_pool.get_slot_branch("demo-epic", 1) == "epic/demo-epic-slot-1"

    _init_repo(tmp_path, branch="develop")
    (tmp_path / "src.py").write_text("ok = True\n", encoding="utf-8")
    _commit_all(tmp_path, "Initial")

    epic_wt = tmp_path / ".worktrees" / "demo_epic"
    _git(
        tmp_path,
        "worktree",
        "add",
        "-q",
        str(epic_wt),
        "-b",
        "epic/demo-epic",
        "develop",
    )

    hb_path = tmp_path / ".devtool" / "state" / "demo-epic.heartbeat.json"

    init_res = _run(
        [sys.executable, str(POOL_SCRIPT), "init", "demo_epic", "--pool-size", "2"],
        cwd=epic_wt,
    )
    assert init_res.returncode == 0, init_res.stderr
    hb_init = _read_json(hb_path)
    assert hb_init["slots"]["slot-1"]["status"] == "idle"
    assert hb_init["slots"]["slot-2"]["status"] == "idle"

    sync_res = _run(
        [
            sys.executable,
            str(POOL_SCRIPT),
            "sync",
            "demo_epic",
            "--slot",
            "1",
            "--task",
            "task_01",
            "--wave",
            "2",
        ],
        cwd=epic_wt,
    )
    assert sync_res.returncode == 0, sync_res.stderr
    hb_sync = _read_json(hb_path)
    assert hb_sync["active_wave"] == 2
    assert hb_sync["slots"]["slot-1"]["status"] == "working"
    assert hb_sync["slots"]["slot-1"]["task_id"] == "task_01"
    assert "task_01" in hb_sync["active_tasks"]

    wave_res = _run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--epic",
            "demo-epic",
            "--wave",
            "3",
            "--state",
            "--status",
            "Implementing wave 3",
        ],
        cwd=epic_wt,
    )
    assert wave_res.returncode == 0, wave_res.stderr
    hb_wave = _read_json(hb_path)
    assert hb_wave["active_wave"] == 3

    slot1_wt = tmp_path / ".worktrees" / "demo_epic-slot-1"
    (slot1_wt / "src.py").write_text("ok = 'merged'\n", encoding="utf-8")
    _commit_all(slot1_wt, "Slot 1 work")

    merge_res = _run(
        [sys.executable, str(POOL_SCRIPT), "merge", "demo_epic", "--slot", "1"],
        cwd=epic_wt,
    )
    assert merge_res.returncode == 0, merge_res.stderr
    hb_merge = _read_json(hb_path)
    assert hb_merge["slots"]["slot-1"]["status"] == "idle"

    clean_res = _run(
        [sys.executable, str(POOL_SCRIPT), "cleanup", "demo_epic", "--pool-size", "2"],
        cwd=epic_wt,
    )
    assert clean_res.returncode == 0, clean_res.stderr
    hb_clean = _read_json(hb_path)
    assert hb_clean.get("slots", {}) == {}


# ---------------------------------------------------------------------------
# [RSDH-FR-03] Governance docs, byte caps & frontmatter contracts
# ---------------------------------------------------------------------------


def _parse_frontmatter_keys(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].strip() == "---", f"{path} missing frontmatter"
    keys: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:", line)
        if m:
            keys.append(m.group(1))
    return keys


def test_rsdh_fr_03_governance_docs_caps_and_orchestration_parity() -> None:
    """[RSDH-FR-03] Critical governance docs stay within byte/word caps, preserve frontmatter, and reflect Choice A / wave-parallel / PIC / English rules."""
    cr_path = REPO_ROOT / "rules" / "CRITICAL_RULES.md"
    cr_bytes = len(cr_path.read_bytes())
    assert cr_bytes <= 8192, f"CRITICAL_RULES.md exceeded 8192 bytes: {cr_bytes}"
    cr_text = cr_path.read_text(encoding="utf-8")
    assert "--pending-decision" in cr_text
    assert "--parallel" in cr_text or "wave-parallel" in cr_text.lower()
    assert "English" in cr_text

    dd_path = REPO_ROOT / "skills" / "dev-designer" / "SKILL.md"
    dd_bytes = len(dd_path.read_bytes())
    assert dd_bytes <= 22528, f"dev-designer/SKILL.md exceeded 22528 bytes: {dd_bytes}"
    dd_text = dd_path.read_text(encoding="utf-8")
    assert "detect-profile" in dd_text or "PIC" in dd_text
    assert "--parallel" in dd_text
    assert "English" in dd_text

    di_path = REPO_ROOT / "skills" / "dev-implementation" / "SKILL.md"
    di_text = di_path.read_text(encoding="utf-8")
    assert len(di_text.split()) <= 4500
    for token in (
        "compute_execution_order.py",
        "--parallel",
        "estimate_heartbeat.py",
        "manage_worker_pool.py",
        "--revise",
        "--pending-decision",
    ):
        assert token in di_text, f"Missing '{token}' in dev-implementation/SKILL.md"

    for skill_rel, expected_tokens in (
        ("skills/dev-brainstorming/SKILL.md", ("PIC", "--pending-decision")),
        (
            "skills/principal-review/SKILL.md",
            ("--pending-decision", "CRITICAL_CONFLICT"),
        ),
        (
            "skills/cross-model-review/SKILL.md",
            ("--pending-decision", "CRITICAL_CONFLICT"),
        ),
        (
            "skills/finishing-a-development-branch/SKILL.md",
            ("--pending-decision", "cleanup"),
        ),
    ):
        path = REPO_ROOT / skill_rel
        assert set(_parse_frontmatter_keys(path)) == {"name", "description"}, (
            f"Frontmatter keys violated in {skill_rel}"
        )
        content = path.read_text(encoding="utf-8")
        for tok in expected_tokens:
            assert tok in content, f"Missing '{tok}' in {skill_rel}"


# ---------------------------------------------------------------------------
# [RSDH-FR-03] End-to-end single-terminal developer lifecycle
# ---------------------------------------------------------------------------


def test_rsdh_fr_03_end_to_end_single_terminal_flow(tmp_path: Path) -> None:
    """[RSDH-FR-03] End-to-end flow: detect profile -> package -> wave prompt -> pool slots -> --pending-decision -> --revise -> cleanup -> land."""
    _init_repo(tmp_path, branch="develop")
    build_ready_epic(tmp_path)
    (tmp_path / ".gitignore").write_text("build/\n.devtool/state/\n", encoding="utf-8")
    _commit_all(tmp_path, "Initial demo epic")

    prof_home = tmp_path / "antigravity_homes" / "personal"
    prof_home.mkdir(parents=True)
    prof_env = {
        "HOME": str(prof_home),
        "ANTIGRAVITY_PROFILE": "personal",
        "USER": "nobody",
    }

    assert (
        _run(
            [sys.executable, str(RESUME_SCRIPT), "--detect-profile"],
            cwd=tmp_path,
            extra_env=prof_env,
        ).stdout.strip()
        == "personal"
    )
    assert (
        _run(
            [
                sys.executable,
                str(RESUME_SCRIPT),
                "--gate",
                "1",
                "--epic",
                "demo-epic",
                "--approved",
                "G1",
            ],
            cwd=tmp_path,
            extra_env=prof_env,
        ).returncode
        == 0
    )
    assert (
        _run(
            [
                sys.executable,
                str(RESUME_SCRIPT),
                "--gate",
                "2",
                "--epic",
                "demo-epic",
                "--approved",
                "G2",
            ],
            cwd=tmp_path,
            extra_env=prof_env,
        ).returncode
        == 0
    )
    assert (
        _run(
            [sys.executable, str(PACKAGE_SCRIPT), "demo_epic"],
            cwd=tmp_path,
            extra_env=prof_env,
        ).returncode
        == 0
    )
    handoff_text = (
        tmp_path / ".devtool" / "epic" / "demo_epic" / "handoff.md"
    ).read_text(encoding="utf-8")
    assert "<profile_account_id>" not in handoff_text
    assert "personal" in handoff_text

    # Epic worktree + wave pool run
    _commit_all(tmp_path, "Commit initial package")
    epic_wt = tmp_path / ".worktrees" / "demo_epic"
    _git(
        tmp_path,
        "worktree",
        "add",
        "-q",
        str(epic_wt),
        "-b",
        "epic/demo-epic",
        "develop",
    )

    assert (
        _run(
            [sys.executable, str(POOL_SCRIPT), "init", "demo_epic", "--pool-size", "1"],
            cwd=epic_wt,
        ).returncode
        == 0
    )
    assert (
        _run(
            [
                sys.executable,
                str(POOL_SCRIPT),
                "sync",
                "demo_epic",
                "--slot",
                "1",
                "--task",
                "task_1",
                "--wave",
                "1",
            ],
            cwd=epic_wt,
        ).returncode
        == 0
    )

    slot1_wt = tmp_path / ".worktrees" / "demo_epic-slot-1"
    (slot1_wt / "src").mkdir(exist_ok=True)
    (slot1_wt / "src" / "impl.py").write_text("done = True\n", encoding="utf-8")
    _commit_all(slot1_wt, "Implement task_1")

    assert (
        _run(
            [sys.executable, str(POOL_SCRIPT), "merge", "demo_epic", "--slot", "1"],
            cwd=epic_wt,
        ).returncode
        == 0
    )
    assert (
        _run(
            [
                sys.executable,
                str(POOL_SCRIPT),
                "cleanup",
                "demo_epic",
                "--pool-size",
                "1",
            ],
            cwd=epic_wt,
        ).returncode
        == 0
    )

    # Gate 5 pause then clear via revise / clear-decision before landing
    assert (
        _run(
            [
                sys.executable,
                str(RESUME_SCRIPT),
                "--pending-decision",
                "Confirm Stage 4 landing",
                "--decision-kind",
                "finish",
                "--epic",
                "demo-epic",
            ],
            cwd=epic_wt,
        ).returncode
        == 0
    )
    assert (
        _run(
            [
                sys.executable,
                str(PACKAGE_SCRIPT),
                "--revise",
                "--reason",
                "Stage 3 revision",
                "demo_epic",
            ],
            cwd=epic_wt,
            extra_env=prof_env,
        ).returncode
        == 0
    )
    _commit_all(epic_wt, "Commit revised handoff")
    verified_sha = _git(epic_wt, "rev-parse", "HEAD")

    land_res = _run(
        [
            sys.executable,
            str(INTEGRATE_SCRIPT),
            "land",
            "--base",
            "develop",
            "--no-fetch",
            "--verified",
            verified_sha,
            "--title",
            "[DEMO_EPIC] Complete epic",
            "--format",
            "json",
        ],
        cwd=epic_wt,
    )
    assert land_res.returncode == 0, (
        f"land failed:\n{land_res.stdout}\n{land_res.stderr}"
    )


class TestRSDHOrchestration_Integration:
    """[Tier C - Integration] Integration runner provenance suite for Task 03 scenarios."""

    def test_RSDH_HP_04_integration(self, tmp_path: Path) -> None:
        """[RSDH-HP-04] Integration check for wave-parallel handoff and creator PIC stamping."""
        test_rsdh_hp_04_wave_parallel_handoff_and_creator_pic(tmp_path)

    def test_RSDH_HP_05_integration(self, tmp_path: Path) -> None:
        """[RSDH-HP-05] Integration check for worker pool live slot, wave heartbeat updates, and clean slot cleanup."""
        test_rsdh_hp_05_worker_pool_slot_and_wave_heartbeat_updates(tmp_path)

    def test_RSDH_EC_03_integration(self, tmp_path: Path) -> None:
        """[RSDH-EC-03] Integration check for Stage 3 package --revise vs strict Stage 2 ownership."""
        test_rsdh_ec_03_stage3_revise_vs_stage2_strict(tmp_path)

    def test_RSDH_EC_08_integration(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """[RSDH-EC-08] Integration check for automatic creator profile detection and PIC stamping."""
        test_rsdh_ec_08_creator_profile_auto_detection_and_pic_stamping(
            tmp_path, monkeypatch
        )

    def test_RSDH_ST_01_integration(self, tmp_path: Path) -> None:
        """[RSDH-ST-01] Integration check for multi-epic Choice A pending-decision isolation."""
        test_rsdh_st_01_pending_decision_per_epic_isolation_and_clear(tmp_path)

    def test_RSDH_ST_03_integration(self, tmp_path: Path) -> None:
        """[RSDH-ST-03] Integration check for stale worker pool pruning and branch landing orphan cleanup."""
        test_rsdh_st_03_stale_pool_pruning_and_branch_landing(tmp_path)

    def test_RSDH_ST_07_integration(self, tmp_path: Path) -> None:
        """[RSDH-ST-07] Integration check for pool cleanup preserving dirty, unmerged, and missing-wt branches."""
        test_rsdh_st_07_pool_cleanup_preserves_dirty_unmerged_and_missing_wt(tmp_path)

    def test_RSDH_FR_03_integration(self, tmp_path: Path) -> None:
        """[RSDH-FR-03] Integration check for CRITICAL_RULES byte cap, orchestration parity, and end-to-end flow."""
        test_rsdh_fr_03_governance_docs_caps_and_orchestration_parity()
        test_rsdh_fr_03_end_to_end_single_terminal_flow(tmp_path)
