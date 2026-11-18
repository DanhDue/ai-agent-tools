"""Tests for check-tasks Kanban sticky layout, unnumbered stage summaries, and epic-scoped telemetry."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

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
    assert "grid-template-columns: repeat(5, minmax(260px, 1fr))" in html
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
