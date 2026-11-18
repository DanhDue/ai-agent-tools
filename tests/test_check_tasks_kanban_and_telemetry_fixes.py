"""Tests for check-tasks Kanban sticky layout, unnumbered stage summaries, and epic-scoped telemetry."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECK_TASKS_PATH = (
    REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts" / "check_tasks.py"
)


@pytest.fixture(scope="module")
def check_tasks_mod():
    spec = importlib.util.spec_from_file_location(
        "check_tasks_under_test", CHECK_TASKS_PATH
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_task(path: Path, epic: str, status: str, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'---\nepic: "{epic}"\nstatus: "{status}"\npriority: "medium"\n---\n\n# {title}\n',
        encoding="utf-8",
    )


def test_multi_epic_repo_isolates_active_epic_telemetry_and_colliding_stems(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, check_tasks_mod
) -> None:
    """Active epic with 5/5 done tasks must not inherit 16 backlog tasks from another epic, even with matching task_01 stems."""
    repo = tmp_path / "lyrics-sync"
    (repo / ".git").mkdir(parents=True)
    wt = repo / ".worktrees" / "translation_studio_sync_and_standalone"
    wt.mkdir(parents=True)

    # Second backlog epic directory in root .devtool/epic/
    backlog_epic_dir = repo / ".devtool" / "epic" / "mac_mini_to_cloud_roadmap"
    backlog_epic_dir.mkdir(parents=True)
    (backlog_epic_dir / "mac_mini_to_cloud_roadmap.md").write_text(
        "# Doc Epic: Mac Mini to Cloud\n\n- **Status**: Draft\n",
        encoding="utf-8",
    )

    # Active epic: 4 done tasks (task_02..task_05) + 1 colliding task_01_shared.md = 5 done tasks in worktree
    for idx in range(2, 6):
        _write_task(
            wt / ".devtool" / "features" / "done" / f"task_0{idx}_active.md",
            epic="translation_studio_sync_and_standalone",
            status="done",
            title=f"Task {idx}: Active Wave Item",
        )
    _write_task(
        wt / ".devtool" / "features" / "done" / "task_01_shared.md",
        epic="translation_studio_sync_and_standalone",
        status="done",
        title="Task 1 Shared Stem Active",
    )
    _write_task(
        repo / ".devtool" / "features" / "task_01_shared.md",
        epic="mac_mini_to_cloud_roadmap",
        status="backlog",
        title="Task 1 Shared Stem Backlog",
    )
    for idx in range(2, 17):
        _write_task(
            repo / ".devtool" / "features" / f"task_{idx:02d}_doc.md",
            epic="mac_mini_to_cloud_roadmap",
            status="backlog",
            title=f"Task {idx}: Doc Backlog",
        )

    epic_dir = wt / ".devtool" / "epic" / "translation_studio_sync_and_standalone"
    epic_dir.mkdir(parents=True)
    (epic_dir / "translation_studio_sync_and_standalone.md").write_text(
        "# Epic: Translation Studio\n\n- **Status**: In Progress\n",
        encoding="utf-8",
    )
    state_dir = repo / ".devtool"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "assistant_state.md").write_text(
        "# Assistant State\n\n- **Active Epic**: `translation_studio_sync_and_standalone`\n- **Stage**: `Stage 3 Phase 4 (Review)`\n",
        encoding="utf-8",
    )
    (state_dir / "GATE_LEDGER.md").write_text(
        "| Timestamp | Epic | Gate | Commit | Approved | Deviations | By |\n"
        "|---|---|---|---|---|---|---|\n"
        "| 2026-11-18T00:00:00Z | translation_studio_sync_and_standalone | 1 | abc1234 | Spec | | dev |\n"
        "| 2026-11-18T00:05:00Z | translation_studio_sync_and_standalone | 2 | abc1234 | HLD | | dev |\n"
        "| 2026-11-18T00:10:00Z | translation_studio_sync_and_standalone | 3 | abc1234 | Auto | | dev |\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        check_tasks_mod,
        "_collect_matching_worktrees",
        lambda rp, slug=None: (
            [wt] if slug is None or "translation_studio" in str(slug) else []
        ),
    )
    monkeypatch.setattr(
        check_tasks_mod,
        "scan_worktrees",
        lambda rp: [
            check_tasks_mod.WorktreeMetadata(
                path=str(rp),
                branch="main",
                head_sha="abc1234",
                is_dirty=False,
                dirty_file_count=0,
                is_detached=False,
            ),
            check_tasks_mod.WorktreeMetadata(
                path=str(wt),
                branch="epic/translation_studio_sync_and_standalone",
                head_sha="def5678",
                is_dirty=False,
                dirty_file_count=0,
                is_detached=False,
            ),
        ],
    )

    progress = check_tasks_mod.extract_task_progress(
        repo, "translation_studio_sync_and_standalone"
    )
    assert progress.total_tasks == 21

    repo_meta = check_tasks_mod.scan_repo(repo)
    pt = repo_meta.pipeline_telemetry
    assert pt is not None
    assert pt["task_completion_pct"] == 100.0
    assert pt["done_tasks"] == 5
    assert pt["total_tasks"] == 5
    tasks_stage = next(s for s in pt["stages"] if s["id"] == "tasks")
    assert tasks_stage["label"] == "3. Tasks"
    assert tasks_stage["summary"] == "5/5 (100%)"
    assert tasks_stage["done_tasks"] == 5
    assert tasks_stage["total_tasks"] == 5
    assert not pt["active_sub_step_summary"].startswith(
        ("1.", "2.", "3.", "4.", "5.", "6.")
    )


def test_multi_wave_packaged_epic_uses_epic_dir_total_count(
    tmp_path: Path, check_tasks_mod
) -> None:
    """When Wave 1 promoted 4 tasks to .devtool/features/done/ while 20 task_*.md exist in .devtool/epic/<slug>/, telemetry reports 4/20 (20%)."""
    repo = tmp_path / "wave-repo"
    (repo / ".git").mkdir(parents=True)
    epic_slug = "multi_wave_epic"
    epic_dir = repo / ".devtool" / "epic" / epic_slug
    epic_dir.mkdir(parents=True)
    (epic_dir / f"{epic_slug}.md").write_text(
        "# Epic\n\n- **Status**: In Progress\n", encoding="utf-8"
    )

    for idx in range(1, 21):
        _write_task(
            epic_dir / f"task_{idx:02d}_packaged.md",
            epic=epic_slug,
            status="done" if idx <= 4 else "backlog",
            title=f"Task {idx}",
        )
    for idx in range(1, 5):
        _write_task(
            repo / ".devtool" / "features" / "done" / f"task_{idx:02d}_packaged.md",
            epic=epic_slug,
            status="done",
            title=f"Task {idx}",
        )

    pt = check_tasks_mod.build_epic_pipeline_telemetry(
        repo,
        epic_slug,
        done_tasks=4,
        total_tasks=4,
    )
    assert pt["task_completion_pct"] == 20.0
    assert pt["done_tasks"] == 4
    assert pt["total_tasks"] == 20
    tasks_stage = next(s for s in pt["stages"] if s["id"] == "tasks")
    assert tasks_stage["summary"] == "4/20 (20%)"
    assert tasks_stage["done_tasks"] == 4
    assert tasks_stage["total_tasks"] == 20
    assert pt["active_sub_step_summary"] == "Tasks · 4/20 (20%)"


def test_multi_wave_lifecycle_state_and_worktree_packaged_overview(
    tmp_path: Path, check_tasks_mod
) -> None:
    """Wave 1 (4/20) must stay in TDD rather than Gate 4, worktree-packaged epics report max task_count, and root feature-only backlog epics register."""
    repo = tmp_path / "wt-wave-repo"
    (repo / ".git").mkdir(parents=True)
    epic_slug = "wt_packaged_epic"

    # Root epic dir has HLD stub only (0 packaged task_*.md), while worktree epic dir has 20 packaged tasks
    root_epic_dir = repo / ".devtool" / "epic" / epic_slug
    root_epic_dir.mkdir(parents=True)
    (root_epic_dir / f"{epic_slug}.md").write_text(
        "# Epic: Worktree Packaged\n\n- **Status**: In Progress\n", encoding="utf-8"
    )

    wt = repo / ".worktrees" / epic_slug
    wt_epic_dir = wt / ".devtool" / "epic" / epic_slug
    wt_epic_dir.mkdir(parents=True)
    (wt_epic_dir / f"{epic_slug}.md").write_text(
        "# Epic: Worktree Packaged\n\n- **Status**: In Progress\n", encoding="utf-8"
    )
    for idx in range(1, 21):
        _write_task(
            wt_epic_dir / f"task_{idx:02d}_wave.md",
            epic=epic_slug,
            status="done" if idx <= 4 else "backlog",
            title=f"Wave Task {idx}",
        )

    # Simulate a repo where extract_task_progress only sees the 4 promoted tasks in features/done (e.g. root promoted wave)
    root_wave_repo = tmp_path / "root-wave-lifecycle"
    (root_wave_repo / ".git").mkdir(parents=True)
    rw_epic_dir = root_wave_repo / ".devtool" / "epic" / epic_slug
    rw_epic_dir.mkdir(parents=True)
    (rw_epic_dir / f"{epic_slug}.md").write_text(
        "# Epic: Root Wave\n\n- **Status**: In Progress\n", encoding="utf-8"
    )
    for idx in range(1, 21):
        _write_task(
            rw_epic_dir / f"task_{idx:02d}_wave.md",
            epic=epic_slug,
            status="done" if idx <= 4 else "backlog",
            title=f"Wave Task {idx}",
        )
    for idx in range(1, 5):
        _write_task(
            root_wave_repo
            / ".devtool"
            / "features"
            / "done"
            / f"task_{idx:02d}_wave.md",
            epic=epic_slug,
            status="done",
            title=f"Wave Task {idx}",
        )
    # Also add a root feature task for a backlog epic that has NO .devtool/epic/<slug>/ directory yet
    _write_task(
        root_wave_repo / ".devtool" / "features" / "task_01_unfoldered_backlog.md",
        epic="unfoldered_backlog_epic",
        status="backlog",
        title="Unfoldered Backlog Task",
    )
    (root_wave_repo / ".devtool" / "GATE_LEDGER.md").write_text(
        "| Timestamp | Epic | Gate | Commit | Approved | Deviations | By |\n"
        "|---|---|---|---|---|---|---|\n"
        f"| 2026-11-18T00:00:00Z | {epic_slug} | 1 | abc1234 | Spec | | dev |\n"
        f"| 2026-11-18T00:05:00Z | {epic_slug} | 2 | abc1234 | HLD | | dev |\n"
        f"| 2026-11-18T00:10:00Z | {epic_slug} | 3 | abc1234 | Auto | | dev |\n",
        encoding="utf-8",
    )

    # 1. Unfoldered backlog epic task in root .devtool/features/ is preserved alongside active epic
    rw_prog = check_tasks_mod.extract_task_progress(root_wave_repo, epic_slug)
    assert any(t["epic"] == "unfoldered_backlog_epic" for t in rw_prog.tasks)

    # 2. Wave 1 (4/20) must NOT report "Tasks Done (Running Gate 4 Verification)"
    decision = check_tasks_mod.derive_lifecycle_state(root_wave_repo, epic_slug)
    assert decision.gate_status == "Gate 3 PASS"
    assert (
        decision.stage_name == check_tasks_mod.LifecycleStage.STAGE_3_PHASE_2_TDD.value
    )

    # 3. harvest_epics_overview inspects matching worktree epic dirs for task_count
    overview = check_tasks_mod.harvest_epics_overview(repo)
    ep_item = next(e for e in overview.epics if e["slug"] == epic_slug)
    assert ep_item["task_count"] == 20

    # 4. _strip_stage_index_prefix strips leading numeric prefixes while preserving stepper labels
    assert check_tasks_mod._strip_stage_index_prefix("1. Spec") == "Spec"
    assert check_tasks_mod._strip_stage_index_prefix("4. Gate 4 QA") == "Gate 4 QA"
    pt = check_tasks_mod.build_epic_pipeline_telemetry(
        root_wave_repo, epic_slug, done_tasks=4, total_tasks=4
    )
    assert [s["label"] for s in pt["stages"]] == [
        "1. Spec",
        "2. HLD & Principal",
        "3. Tasks",
        "4. Gate 4 QA",
        "5. Cross-Review",
        "6. Finish",
    ]
