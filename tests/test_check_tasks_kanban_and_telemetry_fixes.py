"""Tests for check-tasks Kanban sticky layout, unnumbered stage summaries, and epic-scoped telemetry."""

from __future__ import annotations

import base64
from collections.abc import Iterator
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import threading
import time
from typing import Any
import urllib.request

import pytest

from tests.test_cqra_review_action_e2e import (
    _CdpSession,
    _find_chrome_binary,
    _pick_free_port,
    _wait_for_js_condition,
    tasks_server,
)
from tests.test_ltsp_dashboard_ui import _eval_dashboard_js

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


def test_kanban_sticky_overview_single_scroll_and_long_slug_truncation() -> None:
    """Kanban pins 220px Overview, uses one horizontal scroll track, locks column overflow-x, and truncates long epic slugs."""
    long_slug = "translation_studio_sync_and_standalone_very_long_epic_identifier"
    res = _eval_dashboard_js(
        rf"""
        const ctx = createDashboardContext();
        const repo = {{
          name: 'lyrics-sync',
          path: '/tmp/lyrics-sync',
          active_epic: '{long_slug}',
          active_stage: 'Stage 3 Phase 2 (TDD)',
          task_progress: {{
            total_tasks: 2,
            done_tasks: 1,
            in_progress_tasks: 1,
            todo_tasks: 0,
            percentage: 50.0,
            task_completion_pct: 50.0,
            tasks: [
              {{
                id: 'task_01',
                title: 'Task 1: Unbroken_identifier_token_check_in_kanban_card_title',
                status: 'in-progress',
                priority: 'high',
                epic: '{long_slug}',
                source: 'worktree',
              }},
              {{
                id: 'task_02',
                title: 'Task 2: Completed Wave Item',
                status: 'done',
                priority: 'medium',
                epic: '{long_slug}',
                source: 'worktree',
              }},
            ],
          }},
          epics_summary: {{
            total: 1,
            in_progress: 1,
            completed: 0,
            unstarted: 0,
            abandoned: 0,
            epics: [{{ slug: '{long_slug}', status: 'in_progress', task_count: 2 }}],
          }},
        }};
        const kanbanHtml = ctx.renderKanbanDashboard(repo, 'all');
        const colCardMatches = kanbanHtml.match(/<div class="kanban-col-cards"[^>]*>/g) || [];
        const sigBefore = ctx.buildKanbanSig(repo, 'all');
        repo.epics_summary.epics[0].task_count = 20;
        const sigAfter = ctx.buildKanbanSig(repo, 'all');
        console.log(JSON.stringify({{ kanbanHtml, colCardMatches, sigChanged: sigBefore !== sigAfter }}));
        """
    )
    html = res["kanbanHtml"]
    assert res["sigChanged"] is True
    assert 'class="kanban-board-shell"' in html
    assert "grid-template-columns: 220px minmax(0, 1fr)" in html
    assert 'data-kanban-overview="pinned"' in html
    assert "position: sticky; left: 0; z-index: 3" in html
    assert 'class="kanban-columns-scroll"' in html
    assert "overflow-x: auto; overflow-y: hidden" in html
    assert "grid-template-columns: repeat(5, minmax(210px, 1fr))" in html
    assert "flex-shrink: 0" in html
    col_card_tags = res["colCardMatches"]
    assert len(col_card_tags) == 5
    for tag in col_card_tags:
        assert "overflow-x: hidden" in tag
        assert "overflow-y: auto" in tag
    assert 'class="kanban-epic-link-row"' in html
    assert 'class="kanban-epic-chip"' in html
    assert f"[{long_slug}]" in html
    assert f"🗂 {long_slug}" in html
    assert html.count("text-overflow: ellipsis") >= 3
    dashboard_text = (
        REPO_ROOT
        / "skills"
        / "check-tasks"
        / "resources"
        / "dashboard"
        / "tasks_dashboard.html"
    ).read_text(encoding="utf-8")
    assert ".kanban-board-shell," in dashboard_text
    assert ".kanban-epic-link-row," in dashboard_text
    assert ".kanban-epic-chip {" in dashboard_text
    assert "ensureKanbanHorizontalWheelBridge" in dashboard_text
    assert "overscroll-behavior-x: auto" in dashboard_text
    assert dashboard_text.count("repeat(5, minmax(210px, 1fr))") >= 2


def test_substeps_and_synthesized_telemetry_strip_stage_index_prefix_preserving_pills() -> (
    None
):
    """Standalone sub-step headers and synthesized summaries omit numeric stage prefixes while 6-stage pills retain 1..6."""
    res = _eval_dashboard_js(
        r"""
        const ctx = createDashboardContext();
        const repo = {
          name: 'lyrics-sync',
          path: '/tmp/lyrics-sync',
          active_epic: 'demo_epic',
          active_stage: 'Stage 3 Phase 2 (TDD)',
          task_progress: { total_tasks: 5, done_tasks: 2, in_progress_tasks: 1, todo_tasks: 2, percentage: 40.0, task_completion_pct: 40.0, tasks: [] },
          epics_summary: { total: 1, in_progress: 1, epics: [{ slug: 'demo_epic', status: 'in_progress', task_count: 5 }] },
        };
        const progState = ctx.computeEpicProgressState(repo, 'demo_epic', 5, 2, repo.epics_summary.epics[0]);
        const synthPt = ctx.synthesizePipelineTelemetry(repo, 'demo_epic', true, progState, 2, 5);
        const pillsHtml = ctx.buildStagePillsHtml(synthPt.stages, 3, false);
        const subStepsTasksHtml = ctx.buildSubStepsHtml(synthPt.stages, 3, null);
        const subStepsQaHtml = ctx.buildSubStepsHtml(synthPt.stages, 4, null);
        const stripped3 = typeof ctx.stripStageIndexPrefix === 'function' ? ctx.stripStageIndexPrefix('3. Tasks') : null;
        console.log(JSON.stringify({
          activeSummary: synthPt.active_sub_step_summary,
          pillsHtml,
          subStepsTasksHtml,
          subStepsQaHtml,
          stripped3,
        }));
        """
    )
    assert res["stripped3"] == "Tasks"
    assert res["activeSummary"] == "Tasks · 2/5 (40%)"
    assert not res["activeSummary"].startswith("3.")
    assert "Tasks:</strong>" in res["subStepsTasksHtml"]
    assert "3. Tasks:" not in res["subStepsTasksHtml"]
    assert "Gate 4 QA:</strong>" in res["subStepsQaHtml"]
    assert "4. Gate 4 QA:" not in res["subStepsQaHtml"]
    for pill_lbl in (
        "1. Spec",
        "2. HLD &amp; Principal",
        "3. Tasks",
        "4. Gate 4 QA",
        "5. Cross-Review",
        "6. Finish",
    ):
        assert pill_lbl in res["pillsHtml"]


def test_frontend_reconciles_multi_wave_and_multi_epic_task_counts() -> None:
    """Multi-wave 4/20 epic renders 4 / 20 Completed (20%) & Promoting next wave tasks...; multi-epic 4/4 active epic renders 100% alongside 16 backlog tasks."""
    res = _eval_dashboard_js(
        r"""
        const ctx = createDashboardContext();
        const waveTasks = Array.from({ length: 4 }, (_, i) => ({
          id: `task_0${i + 1}`,
          title: `Wave 1 Task ${i + 1}`,
          status: 'done',
          priority: 'high',
          epic: 'multi_wave_epic',
        }));
        const waveRepo = {
          name: 'wave-repo',
          path: '/tmp/wave-repo',
          active_epic: 'multi_wave_epic',
          active_stage: 'Stage 3 Phase 2 (TDD)',
          worktrees: [{ path: '/tmp/wave-repo/.worktrees/multi_wave_epic', branch: 'epic/multi_wave_epic', is_dirty: false, dirty_file_count: 0 }],
          task_progress: {
            total_tasks: 4,
            done_tasks: 4,
            in_progress_tasks: 0,
            todo_tasks: 0,
            percentage: 96.0,
            task_completion_pct: 100.0,
            tasks: waveTasks,
          },
          epics_summary: {
            total: 1,
            in_progress: 1,
            completed: 0,
            unstarted: 0,
            abandoned: 0,
            epics: [{
              slug: 'multi_wave_epic',
              status: 'in_progress',
              task_count: 20,
              pipeline_telemetry: {
                epic_slug: 'multi_wave_epic',
                done_tasks: 4,
                total_tasks: 20,
                task_completion_pct: 20.0,
                lifecycle_progress_pct: 36.0,
                current_stage_index: 3,
                active_sub_step_summary: 'Tasks · 4/20 (20%)',
                stages: [
                  { id: 'spec', index: 1, label: '1. Spec', status: 'done', summary: 'Gate 1 PASS', sub_steps: [] },
                  { id: 'hld_principal', index: 2, label: '2. HLD & Principal', status: 'done', summary: 'Gate 2 PASS', sub_steps: [] },
                  { id: 'tasks', index: 3, label: '3. Tasks', status: 'running', summary: '4/20 (20%)', done_tasks: 4, total_tasks: 20, sub_steps: [] },
                  { id: 'gate4_quality', index: 4, label: '4. Gate 4 QA', status: 'pending', summary: 'Pending', sub_steps: [] },
                  { id: 'cross_review', index: 5, label: '5. Cross-Review', status: 'pending', summary: 'Pending', sub_steps: [] },
                  { id: 'finish', index: 6, label: '6. Finish', status: 'pending', summary: 'Pending', sub_steps: [] },
                ],
                events: [],
              },
            }],
          },
        };

        const activeFour = Array.from({ length: 4 }, (_, i) => ({
          id: `task_0${i + 1}_active`,
          title: `Active Epic Task ${i + 1}`,
          status: 'done',
          priority: 'high',
          epic: 'active_four_epic',
        }));
        const secondSixteen = Array.from({ length: 16 }, (_, i) => ({
          id: `task_${String(i + 1).padStart(2, '0')}_backlog`,
          title: `Second Backlog Task ${i + 1}`,
          status: 'backlog',
          priority: 'medium',
          epic: 'second_backlog_epic',
        }));
        const multiRepo = {
          name: 'lyrics-sync',
          path: '/tmp/lyrics-sync',
          active_epic: 'active_four_epic',
          active_stage: 'Stage 3 Phase 4 (Review)',
          worktrees: [{ path: '/tmp/lyrics-sync/.worktrees/active_four_epic', branch: 'epic/active_four_epic', is_dirty: false, dirty_file_count: 0 }],
          task_progress: {
            total_tasks: 20,
            done_tasks: 4,
            in_progress_tasks: 0,
            todo_tasks: 0,
            backlog_tasks: 16,
            percentage: 20.0,
            task_completion_pct: 20.0,
            active_task_name: 'Second Backlog Task 1',
            tasks: [...activeFour, ...secondSixteen],
          },
          epics_summary: {
            total: 2,
            in_progress: 1,
            completed: 0,
            unstarted: 1,
            abandoned: 0,
            epics: [
              { slug: 'active_four_epic', status: 'in_progress', task_count: 4 },
              { slug: 'second_backlog_epic', status: 'unstarted', task_count: 16 },
            ],
          },
        };

        console.log(JSON.stringify({
          waveExecHtml: ctx.renderExecutionEpics(waveRepo),
          waveKanbanHtml: ctx.renderKanbanDashboard(waveRepo, 'all'),
          multiExecHtml: ctx.renderExecutionEpics(multiRepo),
          multiKanbanHtml: ctx.renderKanbanDashboard(multiRepo, 'all'),
        }));
        """
    )
    assert "4 / 20 Completed (20%)" in res["waveExecHtml"]
    assert "Promoting next wave tasks..." in res["waveExecHtml"]
    assert "4 / 4 Completed" not in res["waveExecHtml"]
    assert "All tasks completed ✓" not in res["waveExecHtml"]
    assert "4/20 Tasks (20%)" in res["waveKanbanHtml"]
    assert "4/4 Tasks" not in res["waveKanbanHtml"]

    assert "4 / 4 Completed (100%" in res["multiExecHtml"]
    assert "All tasks completed ✓" in res["multiExecHtml"]
    assert "Second Backlog Task 1" not in res["multiExecHtml"]
    assert "4 / 4 Completed (20%)" not in res["multiExecHtml"]
    assert "4/4 Tasks (100%)" in res["multiKanbanHtml"]
    assert "0/16 Tasks (0%)" in res["multiKanbanHtml"]


@pytest.fixture(scope="module")
def kanban_e2e_workspace(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[dict[str, Any]]:
    """Spin up TasksServer on an ephemeral port against a multi-epic lyrics-sync git workspace."""
    ws_root = tmp_path_factory.mktemp("kanban_cdp_ws")
    repo = ws_root / "lyrics-sync"
    repo.mkdir(parents=True)

    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Test Bot",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test Bot",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repo,
        env=git_env,
        check=True,
        capture_output=True,
    )

    backlog_epic_dir = repo / ".devtool" / "epic" / "mac_mini_to_cloud_roadmap"
    backlog_epic_dir.mkdir(parents=True)
    (backlog_epic_dir / "mac_mini_to_cloud_roadmap.md").write_text(
        "# Doc Epic: Mac Mini to Cloud\n\n- **Status**: Draft\n",
        encoding="utf-8",
    )
    for idx in range(1, 17):
        _write_task(
            repo / ".devtool" / "features" / f"task_{idx:02d}_doc.md",
            epic="mac_mini_to_cloud_roadmap",
            status="backlog",
            title=f"Task {idx}: Unbroken_identifier_token_for_mac_mini_to_cloud_roadmap_stream_{idx:02d}",
        )

    subprocess.run(
        ["git", "add", "."],
        cwd=repo,
        env=git_env,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "[INIT] Seed backlog epic"],
        cwd=repo,
        env=git_env,
        check=True,
        capture_output=True,
    )

    wt_rel = Path(".worktrees") / "translation_studio_sync_and_standalone"
    subprocess.run(
        [
            "git",
            "worktree",
            "add",
            "-b",
            "epic/translation_studio_sync_and_standalone",
            str(wt_rel),
        ],
        cwd=repo,
        env=git_env,
        check=True,
        capture_output=True,
    )
    wt = repo / wt_rel
    active_epic_dir = (
        wt / ".devtool" / "epic" / "translation_studio_sync_and_standalone"
    )
    active_epic_dir.mkdir(parents=True)
    (active_epic_dir / "translation_studio_sync_and_standalone.md").write_text(
        "# Epic: Translation Studio\n\n- **Status**: In Progress\n- **PIC**: `nguyenhieu000690`\n",
        encoding="utf-8",
    )
    for idx in range(1, 5):
        _write_task(
            wt / ".devtool" / "features" / "done" / f"task_{idx:02d}_active.md",
            epic="translation_studio_sync_and_standalone",
            status="done",
            title=f"Active_translation_studio_sync_and_standalone_unbroken_wave_item_{idx:02d}",
        )
    subprocess.run(
        ["git", "add", "."],
        cwd=wt,
        env=git_env,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "[EPIC] Complete 4 active tasks"],
        cwd=wt,
        env=git_env,
        check=True,
        capture_output=True,
    )

    state_dir = repo / ".devtool"
    (state_dir / "assistant_state.md").write_text(
        "# Assistant State\n\n"
        "- **Active Epic**: `translation_studio_sync_and_standalone`\n"
        "- **Stage**: `Stage 3 Phase 3 (Quality Check)`\n",
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

    pid_file = ws_root / "kanban_e2e_tasks_server.pid"
    port = _pick_free_port()
    server = tasks_server.TasksServer(
        host="127.0.0.1",
        port=port,
        workspace_root=ws_root,
        pid_file=pid_file,
    )
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True
    )
    thread.start()

    base_url = f"http://127.0.0.1:{server.server_port}"
    ready = False
    for _ in range(50):
        try:
            with urllib.request.urlopen(f"{base_url}/api/status", timeout=0.5) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except OSError:
            time.sleep(0.05)
    assert ready, "TasksServer failed to start on isolated localhost port"

    try:
        yield {"base_url": base_url, "port": server.server_port, "ws_root": ws_root}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3.0)


@pytest.fixture(scope="module")
def kanban_chrome_cdp(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[_CdpSession]:
    """Launch headless Google Chrome at 1280x900 on an isolated user-data-dir."""
    chrome_bin = _find_chrome_binary()
    user_data_dir = tmp_path_factory.mktemp("kanban_chrome_profile")
    debug_port = _pick_free_port()

    proc = subprocess.Popen(
        [
            chrome_bin,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--window-size=1280,900",
            f"--user-data-dir={user_data_dir}",
            f"--remote-debugging-port={debug_port}",
            "--remote-allow-origins=*",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    ws_url = ""
    for _ in range(80):
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{debug_port}/json/list", timeout=0.5
            ) as resp:
                targets = json.loads(resp.read().decode("utf-8"))
                page_targets = [
                    t
                    for t in targets
                    if t.get("type") == "page" and t.get("webSocketDebuggerUrl")
                ]
                if page_targets:
                    ws_url = str(page_targets[0]["webSocketDebuggerUrl"])
                    break
        except Exception:
            time.sleep(0.1)

    if not ws_url:
        proc.terminate()
        proc.wait(timeout=5)
        raise RuntimeError(
            "Timed out waiting for headless Chrome /json/list page target"
        )

    session = _CdpSession(ws_url)
    session.call("Page.enable")
    session.call("Runtime.enable")
    session.call(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False},
    )
    try:
        yield session
    finally:
        with contextlib.suppress(Exception):
            session.call("Browser.close")
        session.close()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_live_chrome_cdp_kanban_sticky_scroll_and_unnumbered_stage_titles(
    kanban_e2e_workspace: dict[str, Any],
    kanban_chrome_cdp: _CdpSession,
    tmp_path: Path,
) -> None:
    """Real Headless Chrome CDP E2E: sticky 220px Overview, single 5-column scroll track, overflow-x hidden columns, unnumbered sub-step headers, and 4/4 active epic isolation."""
    base_url = kanban_e2e_workspace["base_url"]
    cdp = kanban_chrome_cdp
    cdp.console_errors.clear()
    cdp.uncaught_exceptions.clear()

    cdp.call("Page.navigate", {"url": f"{base_url}/"})
    _wait_for_js_condition(
        cdp,
        """Boolean(
            document.getElementById('kanban-dashboard-wrapper-lyrics-sync')
            && document.querySelector('#kanban-dashboard-wrapper-lyrics-sync [data-kanban-overview="pinned"]')
            && document.querySelector('.epic-execution-item')
        )""",
        timeout=8.0,
    )

    # 1. Narrow laptop/split viewport (1180x900) where 5 * 210px = 1050px > right-pane width (~866px)
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1180, "height": 900, "deviceScaleFactor": 1, "mobile": False},
    )
    cdp.eval_js(
        """(() => {
            const w = document.getElementById('kanban-dashboard-wrapper-lyrics-sync');
            w.scrollIntoView({ block: 'start' });
            window.scrollBy(0, -100);
            w.querySelector('.kanban-columns-scroll').scrollLeft = 0;
            return true;
        })()"""
    )
    time.sleep(0.1)

    pre_wheel = cdp.eval_js(
        """
        (() => {
          const wrapper = document.getElementById('kanban-dashboard-wrapper-lyrics-sync');
          const overview = wrapper.querySelector('[data-kanban-overview="pinned"]');
          const scrollTrack = wrapper.querySelector('.kanban-columns-scroll');
          const backlogCol = wrapper.querySelector('[data-scroll-id="kanban-col-lyrics-sync-backlog"]');
          const todoCol = wrapper.querySelector('[data-scroll-id="kanban-col-lyrics-sync-todo"]');
          const colEls = Array.from(wrapper.querySelectorAll('.kanban-col'));
          const colCards = Array.from(wrapper.querySelectorAll('.kanban-col-cards'));

          const overviewStyle = window.getComputedStyle(overview);
          const beforeRect = overview.getBoundingClientRect();
          const trackStyle = window.getComputedStyle(scrollTrack);
          const backlogStyle = window.getComputedStyle(backlogCol);

          const colWidths = colEls.map(c => Math.round(c.getBoundingClientRect().width));
          const colStats = colCards.map(col => ({
            overflowX: window.getComputedStyle(col).overflowX,
            overscrollX: window.getComputedStyle(col).overscrollBehaviorX,
            overscrollY: window.getComputedStyle(col).overscrollBehaviorY,
            scrollWidth: col.scrollWidth,
            clientWidth: col.clientWidth,
          }));

          const cardBounds = Array.from(wrapper.querySelectorAll('.kanban-task-card')).map(card => {
            const cardRect = card.getBoundingClientRect();
            const cardStyle = window.getComputedStyle(card);
            const titleEl = card.querySelector('div > strong');
            const priBadge = card.querySelector('div > strong + span');
            const linkRow = card.querySelector('.kanban-epic-link-row');
            const chip = card.querySelector('.kanban-epic-chip');
            const titleStyle = titleEl ? window.getComputedStyle(titleEl) : null;
            const priStyle = priBadge ? window.getComputedStyle(priBadge) : null;
            const chipStyle = chip ? window.getComputedStyle(chip) : null;
            const childRows = Array.from(card.children).map(ch => {
              const r = ch.getBoundingClientRect();
              return {
                height: r.height,
                bottomDelta: r.bottom - cardRect.bottom,
                flexShrink: window.getComputedStyle(ch).flexShrink,
              };
            });
            return {
              cardHeight: cardRect.height,
              cardFlexShrink: cardStyle.flexShrink,
              childRows,
              cardRight: cardRect.right,
              priRight: priBadge ? priBadge.getBoundingClientRect().right : cardRect.right,
              linkRight: linkRow ? linkRow.getBoundingClientRect().right : cardRect.right,
              chipRight: chip ? chip.getBoundingClientRect().right : cardRect.right,
              titleFlexGrow: titleStyle ? titleStyle.flexGrow : '',
              titleFlexBasis: titleStyle ? titleStyle.flexBasis : '',
              priWhiteSpace: priStyle ? priStyle.whiteSpace : '',
              chipBoxSizing: chipStyle ? chipStyle.boxSizing : '',
            };
          });

          const backlogCards = Array.from(backlogCol.querySelectorAll('.kanban-task-card'));
          const secondCardRect = backlogCards[1].getBoundingClientRect();
          const todoRect = todoCol.getBoundingClientRect();

          const subStepsTexts = Array.from(document.querySelectorAll('[data-telemetry="sub-steps"]')).map(el => el.textContent.trim());
          const kanbanStageTexts = Array.from(wrapper.querySelectorAll('[data-telemetry="kanban-epic-stage"]')).map(el => el.textContent.trim());

          const execItem = document.querySelector('.epic-execution-item');
          const execText = execItem ? execItem.textContent : '';
          const stagePillLabels = execItem
            ? Array.from(execItem.querySelectorAll('[data-stage-id]')).map(el => el.textContent.trim())
            : [];

          return {
            overviewPosition: overviewStyle.position,
            overviewWidth: beforeRect.width,
            beforeLeft: beforeRect.left,
            trackOverflowX: trackStyle.overflowX,
            trackOverflowY: trackStyle.overflowY,
            trackOverscrollX: trackStyle.overscrollBehaviorX,
            trackScrollWidth: scrollTrack.scrollWidth,
            trackClientWidth: scrollTrack.clientWidth,
            backlogClientHeight: backlogCol.clientHeight,
            backlogScrollHeight: backlogCol.scrollHeight,
            backlogOverscrollX: backlogStyle.overscrollBehaviorX,
            colWidths,
            colStats,
            cardBounds,
            secondCardCenter: {
              x: Math.round(secondCardRect.left + secondCardRect.width / 2),
              y: Math.round(secondCardRect.top + secondCardRect.height / 2),
            },
            backlogLeftPoint: {
              x: Math.round(secondCardRect.left + 40),
              y: Math.round(secondCardRect.top + 40),
            },
            todoCenter: {
              x: Math.round(todoRect.left + todoRect.width / 2),
              y: Math.round(todoRect.top + 120),
            },
            subStepsTexts,
            kanbanStageTexts,
            execText,
            stagePillLabels,
          };
        })()
        """
    )

    assert pre_wheel["overviewPosition"] == "sticky"
    assert abs(float(pre_wheel["overviewWidth"]) - 220.0) <= 1.0
    assert pre_wheel["trackOverflowX"] == "auto"
    assert pre_wheel["trackOverflowY"] == "hidden"
    assert pre_wheel["trackOverscrollX"] == "contain"
    assert pre_wheel["trackScrollWidth"] > pre_wheel["trackClientWidth"]
    assert pre_wheel["colWidths"] == [210, 210, 210, 210, 210]
    assert pre_wheel["backlogScrollHeight"] > pre_wheel["backlogClientHeight"] + 500
    assert pre_wheel["backlogOverscrollX"] == "auto"

    assert len(pre_wheel["colStats"]) == 5
    for col_stat in pre_wheel["colStats"]:
        assert col_stat["overflowX"] == "hidden"
        assert col_stat["overscrollX"] == "auto"
        assert col_stat["overscrollY"] == "contain"
        assert col_stat["scrollWidth"] <= col_stat["clientWidth"] + 1

    assert len(pre_wheel["cardBounds"]) == 20
    for cb in pre_wheel["cardBounds"]:
        assert cb["cardHeight"] >= 100.0, cb
        assert cb["cardFlexShrink"] == "0", cb
        assert len(cb["childRows"]) == 4, cb
        for row in cb["childRows"]:
            assert row["height"] >= 12.0, row
            assert row["bottomDelta"] <= 1.0, row
            assert row["flexShrink"] == "0", row
        assert cb["priRight"] <= cb["cardRight"] - 6, cb
        assert cb["linkRight"] <= cb["cardRight"] - 6, cb
        assert cb["chipRight"] <= cb["cardRight"] - 6, cb
        assert cb["titleFlexGrow"] == "1", cb
        assert cb["titleFlexBasis"] == "0%", cb
        assert cb["priWhiteSpace"] == "nowrap", cb
        assert cb["chipBoxSizing"] == "border-box", cb

    # 2. Real diagonal trackpad horizontal wheel gesture over 16-card Backlog item
    cdp.call(
        "Input.dispatchMouseEvent",
        {
            "type": "mouseWheel",
            "x": pre_wheel["secondCardCenter"]["x"],
            "y": pre_wheel["secondCardCenter"]["y"],
            "deltaX": 140,
            "deltaY": 10,
        },
    )
    time.sleep(0.1)
    after_diag_wheel = cdp.eval_js(
        """(() => {
          const w = document.getElementById('kanban-dashboard-wrapper-lyrics-sync');
          return {
            scrollLeft: w.querySelector('.kanban-columns-scroll').scrollLeft,
            backlogTop: w.querySelector('[data-scroll-id="kanban-col-lyrics-sync-backlog"]').scrollTop,
            overviewLeft: w.querySelector('[data-kanban-overview="pinned"]').getBoundingClientRect().left,
          };
        })()"""
    )
    assert after_diag_wheel["scrollLeft"] >= 130
    assert after_diag_wheel["backlogTop"] == 0
    assert after_diag_wheel["overviewLeft"] == pre_wheel["beforeLeft"]

    # 3. Real Shift+Wheel horizontal gesture over empty To Do column
    cdp.call(
        "Input.dispatchMouseEvent",
        {
            "type": "mouseWheel",
            "x": pre_wheel["todoCenter"]["x"],
            "y": pre_wheel["todoCenter"]["y"],
            "deltaX": 120,
            "deltaY": 0,
        },
    )
    time.sleep(0.1)
    after_todo_wheel = cdp.eval_js(
        """(() => {
          const w = document.getElementById('kanban-dashboard-wrapper-lyrics-sync');
          return {
            scrollLeft: w.querySelector('.kanban-columns-scroll').scrollLeft,
            overviewLeft: w.querySelector('[data-kanban-overview="pinned"]').getBoundingClientRect().left,
          };
        })()"""
    )
    assert after_todo_wheel["scrollLeft"] > after_diag_wheel["scrollLeft"]
    assert after_todo_wheel["overviewLeft"] == pre_wheel["beforeLeft"]

    shot_scrolled = cdp.call("Page.captureScreenshot", {"format": "png"})
    png_scrolled = base64.b64decode(shot_scrolled["data"])

    # 4. Reset scrollLeft=0 and verify vertical scrolling inside 16-card Backlog column still works
    cdp.eval_js(
        "document.querySelector('#kanban-dashboard-wrapper-lyrics-sync .kanban-columns-scroll').scrollLeft = 0; true;"
    )
    time.sleep(0.05)
    cdp.call(
        "Input.dispatchMouseEvent",
        {
            "type": "mouseWheel",
            "x": pre_wheel["backlogLeftPoint"]["x"],
            "y": pre_wheel["backlogLeftPoint"]["y"],
            "deltaX": 6,
            "deltaY": 220,
        },
    )
    time.sleep(0.1)
    after_vert_wheel = cdp.eval_js(
        """(() => {
          const w = document.getElementById('kanban-dashboard-wrapper-lyrics-sync');
          const res = {
            scrollLeft: w.querySelector('.kanban-columns-scroll').scrollLeft,
            backlogTop: w.querySelector('[data-scroll-id="kanban-col-lyrics-sync-backlog"]').scrollTop,
          };
          w.querySelector('[data-scroll-id="kanban-col-lyrics-sync-backlog"]').scrollTop = 0;
          return res;
        })()"""
    )
    assert after_vert_wheel["backlogTop"] >= 180
    assert after_vert_wheel["scrollLeft"] == 0

    # 5. Standard laptop viewport (1366x900): all 5 compact 210px columns + 220px Overview fit side-by-side
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {"width": 1366, "height": 900, "deviceScaleFactor": 1, "mobile": False},
    )
    cdp.eval_js(
        """(() => {
            document.getElementById('kanban-dashboard-wrapper-lyrics-sync').scrollIntoView({ block: 'start' });
            window.scrollBy(0, -100);
            return true;
        })()"""
    )
    time.sleep(0.1)
    wide_fit = cdp.eval_js(
        """(() => {
          const sc = document.querySelector('#kanban-dashboard-wrapper-lyrics-sync .kanban-columns-scroll');
          return { scrollW: sc.scrollWidth, clientW: sc.clientWidth };
        })()"""
    )
    assert wide_fit["scrollW"] <= wide_fit["clientW"] + 2

    assert len(pre_wheel["subStepsTexts"]) >= 1
    for txt in pre_wheel["subStepsTexts"]:
        assert not txt.startswith(("1.", "2.", "3.", "4.", "5.", "6.")), txt
    assert len(pre_wheel["kanbanStageTexts"]) >= 1
    for txt in pre_wheel["kanbanStageTexts"]:
        assert not txt.startswith(("1.", "2.", "3.", "4.", "5.", "6.")), txt

    joined_pills = "\n".join(pre_wheel["stagePillLabels"])
    for expected_pill in (
        "1. Spec",
        "2. HLD & Principal",
        "3. Tasks",
        "4. Gate 4 QA",
        "5. Cross-Review",
        "6. Finish",
    ):
        assert expected_pill in joined_pills

    assert "4 / 4 Completed (100% ✓)" in pre_wheel["execText"]
    assert "4 / 20" not in pre_wheel["execText"]
    assert "4/20" not in pre_wheel["execText"]
    assert "20%" not in pre_wheel["execText"]

    assert cdp.console_errors == []
    assert cdp.uncaught_exceptions == []

    shot = cdp.call("Page.captureScreenshot", {"format": "png"})
    png_bytes = base64.b64decode(shot["data"])
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(png_bytes) > 1024

    save_dir_env = os.environ.get("SAVE_E2E_SCREENSHOT_DIR", "").strip()
    out_dir = Path(save_dir_env) if save_dir_env else tmp_path
    out_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = out_dir / "verify_check_tasks_kanban.png"
    screenshot_path.write_bytes(png_bytes)
    scrolled_path = out_dir / "verify_check_tasks_kanban_scrolled.png"
    scrolled_path.write_bytes(png_scrolled)
    assert screenshot_path.is_file() and screenshot_path.stat().st_size > 1024
    assert scrolled_path.is_file() and scrolled_path.stat().st_size > 1024
