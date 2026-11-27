"""Tests for standalone plans discovery, PROJECT_LEDGER milestones, and Top-10 Done Kanban tab in check-tasks."""

from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECK_TASKS_SCRIPT_DIR = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"
if str(CHECK_TASKS_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(CHECK_TASKS_SCRIPT_DIR))

import check_tasks  # type: ignore[import-not-found]  # noqa: E402
from check_tasks import (  # type: ignore[import-not-found]  # noqa: E402
    WorktreeMetadata,
    _discover_standalone_plans,
    extract_task_progress,
    harvest_epics_overview,
)
from tests.test_ltsp_dashboard_ui import _eval_dashboard_js  # noqa: E402


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_harvest_discovers_standalone_plans_sdd_progress_ledger_and_excludes_vi_mirrors(
    tmp_path: Path,
) -> None:
    """Harvester discovers standalone plans, SDD progress.md, and PROJECT_LEDGER milestones while deduplicating epics and excluding *.vi.md."""
    repo = tmp_path / "demo-repo"
    repo.mkdir()

    # 1. Real .devtool/epic/core_epic/ (done) + same-slug plan (must deduplicate and keep source_kind == "epic")
    _write(
        repo / ".devtool" / "epic" / "core_epic" / "core_epic.md",
        "# Epic: Core Epic\n\n- **Status**: Done\n",
    )
    _write(
        repo / ".devtool" / "epic" / "core_epic" / "task_01.md",
        "---\nstatus: done\nepic: core_epic\npriority: high\n---\n# Task 1: Core architecture\n",
    )
    _write(
        repo / "docs" / "superpowers" / "plans" / "2026-11-20-core-epic.md",
        "# Core Epic Implementation Plan\n\n### Task 1: Duplicate plan task\n",
    )

    # 2. Active standalone plan with 3 tasks + SDD progress.md
    _write(
        repo / "docs" / "superpowers" / "plans" / "2026-11-26-live-feature.md",
        (
            "# Live Feature Implementation Plan\n\n"
            "### Task 1: Build parser\n\n"
            "### Task 2: Wire endpoint\n\n"
            "### Task 3: Add UI\n"
        ),
    )
    _write(
        repo / ".superpowers" / "sdd" / "2026-11-26-live-feature" / "progress.md",
        (
            "Task 1: complete (commits abc1234..def5678)\n"
            "Task 2: fix round 1/1 (addressing review comments)\n"
        ),
    )

    # 3. Completed standalone plan recorded in PROJECT_LEDGER.md
    _write(
        repo / "docs" / "superpowers" / "plans" / "2026-11-25-preview-subheader.md",
        (
            "# Preview Subheader Implementation Plan\n\n"
            "### Task 1: Render header\n\n"
            "### Task 2: Style subheader\n"
        ),
    )

    # 4. Vietnamese mirror — strictly ignored per Rule 11
    _write(
        repo / "docs" / "superpowers" / "plans" / "2026-11-26-vi-only-secret.vi.md",
        "# Secret VI Mirror\n\n### Task 1: Hidden Vietnamese task\n",
    )

    # 5. PROJECT_LEDGER.md with epic, completed standalone plan, and ledger-only milestone
    _write(
        repo / ".devtool" / "PROJECT_LEDGER.md",
        (
            "# Project Architectural Ledger\n\n"
            "## 2. Completed Epics & Architectural Milestones\n"
            "- **[2026-11-20] `core_epic`**: Delivered core architecture\n"
            "- **[2026-11-24] `ledger-only-hotfix`**: Shipped direct hotfix\n"
            "- **[2026-11-25] `preview-subheader`**: Completed preview subheader\n"
        ),
    )

    summary = harvest_epics_overview(repo)
    by_slug = {ep["slug"]: ep for ep in summary.epics}

    # Strictly excludes *.vi.md mirror
    assert not any("vi-only-secret" in s or "vi_only_secret" in s for s in by_slug)

    # Same-slug plan deduplicated under real epic
    assert "core_epic" in by_slug
    assert "core-epic" not in by_slug
    assert by_slug["core_epic"]["source_kind"] == "epic"
    assert by_slug["core_epic"]["status"] == "done"
    assert by_slug["core_epic"]["completed_date"] == "2026-11-20"
    assert by_slug["core_epic"]["milestone_summary"] == "Delivered core architecture"

    # Active standalone plan
    live = by_slug["live-feature"]
    assert live["status"] == "in_progress"
    assert live["source_kind"] == "plan"
    assert live["task_count"] == 3
    assert live["title"] == "Live Feature"
    assert live.get("plan_path")

    # Completed standalone plan
    preview = by_slug["preview-subheader"]
    assert preview["status"] == "done"
    assert preview["source_kind"] == "plan"
    assert preview["task_count"] == 2
    assert preview["completed_date"] == "2026-11-25"
    assert preview["milestone_summary"] == "Completed preview subheader"

    # Ledger-only milestone
    hotfix = by_slug["ledger-only-hotfix"]
    assert hotfix["status"] == "done"
    assert hotfix["source_kind"] == "ledger"
    assert hotfix["task_count"] == 0
    assert hotfix["completed_date"] == "2026-11-24"
    assert hotfix["milestone_summary"] == "Shipped direct hotfix"

    # Task progress: active tasks include only live-feature; completed_tasks includes completed plans & epics
    tp = extract_task_progress(repo, active_epic=None)
    assert tp.total_tasks == 3
    assert tp.done_tasks == 1
    assert tp.in_progress_tasks == 1
    assert tp.todo_tasks == 1

    active_live = [t for t in tp.tasks if t["epic"] == "live-feature"]
    assert len(active_live) == 3
    assert [t["status"] for t in active_live] == ["done", "in-progress", "todo"]
    assert all(t["labels"] == ["plan"] for t in active_live)
    assert all(t["source"] == "plan" for t in active_live)
    assert all(t["epic"] != "preview-subheader" for t in tp.tasks)
    assert all("vi-only-secret" not in str(t["epic"]) for t in tp.tasks)

    assert hasattr(tp, "completed_tasks")
    preview_completed = [
        t for t in tp.completed_tasks if t["epic"] == "preview-subheader"
    ]
    assert len(preview_completed) == 2
    assert all(t["status"] == "done" for t in preview_completed)
    assert all(t["source"] == "plan" for t in preview_completed)
    assert all(t["labels"] == ["plan"] for t in preview_completed)

    core_completed = [t for t in tp.completed_tasks if t["epic"] == "core_epic"]
    assert len(core_completed) == 1
    assert core_completed[0]["status"] == "done"
    assert core_completed[0]["source"] == "root"
    assert all("vi-only-secret" not in str(t["epic"]) for t in tp.completed_tasks)


def test_harvest_discovers_worktree_only_standalone_plan(tmp_path: Path) -> None:
    """Standalone plan living only inside a worktree is discovered as in_progress with active tasks."""
    repo = tmp_path / "wt-repo"
    repo.mkdir()

    _write(
        repo
        / ".worktrees"
        / "wt_plan_feature"
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-11-27-wt-plan-feature.md",
        (
            "# Worktree Plan Feature Implementation Plan\n\n"
            "### Task 1: Scaffold module\n\n"
            "### Task 2: Verify integration\n"
        ),
    )

    summary = harvest_epics_overview(repo)
    by_slug = {ep["slug"]: ep for ep in summary.epics}
    assert "wt-plan-feature" in by_slug
    wt_plan = by_slug["wt-plan-feature"]
    assert wt_plan["status"] == "in_progress"
    assert wt_plan["source_kind"] == "plan"
    assert wt_plan["task_count"] == 2
    assert wt_plan["has_worktree"] is True

    tp = extract_task_progress(repo, active_epic=None)
    assert tp.total_tasks == 2
    assert tp.todo_tasks == 2
    assert [t["epic"] for t in tp.tasks] == ["wt-plan-feature", "wt-plan-feature"]
    assert all(t["labels"] == ["plan"] for t in tp.tasks)
    assert all(t["source"] == "worktree" for t in tp.tasks)


def test_owning_worktree_plan_beats_newer_unrelated_worktree_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An owning slug-matching worktree (by dir or branch) beats a newer unrelated worktree copy instead of falling back to main."""
    base_plan = "# Shared Plan Implementation Plan\n\n### Task 1: Baseline task\n"
    edited_plan = (
        "# Shared Plan Implementation Plan\n\n"
        "### Task 1: Baseline task\n\n"
        "### Task 2: Owning worktree edit\n"
    )

    # Case 1: Owning worktree matches by directory name (wt_a = alpha_plan) vs newer unrelated wt_b
    repo_dir = tmp_path / "wt-dir-match"
    repo_dir.mkdir()
    rel_plan = Path("docs/superpowers/plans/2026-11-27-alpha-plan.md")
    main_plan = repo_dir / rel_plan
    wt_a_plan = repo_dir / ".worktrees" / "alpha_plan" / rel_plan
    wt_b_plan = repo_dir / ".worktrees" / "z_unrelated_wt" / rel_plan
    _write(main_plan, base_plan)
    _write(wt_a_plan, edited_plan)
    _write(wt_b_plan, base_plan)
    os.utime(main_plan, (1000.0, 1000.0))
    os.utime(wt_a_plan, (1100.0, 1100.0))
    os.utime(wt_b_plan, (1200.0, 1200.0))

    discovered_dir = _discover_standalone_plans(repo_dir)
    assert len(discovered_dir) == 1
    assert discovered_dir[0]["from_worktree"] is True
    assert [t["title"] for t in discovered_dir[0]["tasks"]] == [
        "Task 1: Baseline task",
        "Task 2: Owning worktree edit",
    ]

    tp_dir = extract_task_progress(repo_dir, active_epic=None)
    assert tp_dir.total_tasks == 2
    assert [t["title"] for t in tp_dir.tasks] == [
        "Task 1: Baseline task",
        "Task 2: Owning worktree edit",
    ]
    assert all(t["source"] == "worktree" for t in tp_dir.tasks)

    # Case 2: Owning worktree matches by git branch `feat/<slug>` (dir `wt_a`) vs newer unrelated `wt_b`
    repo_br = tmp_path / "wt-branch-match"
    repo_br.mkdir()
    rel_br_plan = Path("docs/superpowers/plans/2026-11-27-beta-plan.md")
    main_br_plan = repo_br / rel_br_plan
    wt_a_root = repo_br / ".worktrees" / "wt_a"
    wt_b_root = repo_br / ".worktrees" / "wt_b"
    wt_a_br_plan = wt_a_root / rel_br_plan
    wt_b_br_plan = wt_b_root / rel_br_plan
    _write(main_br_plan, base_plan)
    _write(wt_a_br_plan, edited_plan)
    _write(wt_b_br_plan, base_plan)
    os.utime(main_br_plan, (1000.0, 1000.0))
    os.utime(wt_a_br_plan, (1100.0, 1100.0))
    os.utime(wt_b_br_plan, (1200.0, 1200.0))

    monkeypatch.setattr(
        check_tasks,
        "scan_worktrees",
        lambda _p: [
            WorktreeMetadata(
                path=str(wt_a_root),
                branch="feat/beta-plan",
                head_sha="abc1234",
                is_dirty=True,
                dirty_file_count=1,
                is_detached=False,
            ),
            WorktreeMetadata(
                path=str(wt_b_root),
                branch="feat/unrelated-branch",
                head_sha="def5678",
                is_dirty=False,
                dirty_file_count=0,
                is_detached=False,
            ),
        ],
    )

    discovered_br = _discover_standalone_plans(repo_br)
    assert len(discovered_br) == 1
    assert discovered_br[0]["from_worktree"] is True
    assert [t["title"] for t in discovered_br[0]["tasks"]] == [
        "Task 1: Baseline task",
        "Task 2: Owning worktree edit",
    ]

    tp_br = extract_task_progress(repo_br, active_epic=None)
    assert tp_br.total_tasks == 2
    assert [t["title"] for t in tp_br.tasks] == [
        "Task 1: Baseline task",
        "Task 2: Owning worktree edit",
    ]
    assert all(t["source"] == "worktree" for t in tp_br.tasks)


def test_completed_tasks_caps_to_top_10_newest_and_preserves_active_metrics(
    tmp_path: Path,
) -> None:
    """completed_tasks caps to the top 10 newest completed plans while keeping active task metrics untouched."""
    repo = tmp_path / "cap-repo"
    repo.mkdir()

    # Seed 1 active epic with 2 tasks (1 done, 1 todo)
    _write(
        repo / ".devtool" / "epic" / "active_epic" / "active_epic.md",
        "# Epic: Active Epic\n\n- **Status**: In Progress\n",
    )
    _write(
        repo / ".devtool" / "features" / "task_01.md",
        "---\nstatus: done\nepic: active_epic\n---\n# Task 1: Done work\n",
    )
    _write(
        repo / ".devtool" / "features" / "task_02.md",
        "---\nstatus: todo\nepic: active_epic\n---\n# Task 2: Pending work\n",
    )

    # Seed 12 completed standalone plans across 2026-11-01..2026-11-12
    # Write files in reverse order to prove ordering follows ledger completion dates, not file write order.
    ledger_lines = [
        "# Project Architectural Ledger",
        "",
        "## 2. Completed Epics & Architectural Milestones",
    ]
    for day in range(12, 0, -1):
        date_str = f"2026-11-{day:02d}"
        slug = f"plan-{day:02d}"
        _write(
            repo / "docs" / "superpowers" / "plans" / f"{date_str}-{slug}.md",
            f"# Plan {day:02d} Implementation Plan\n\n### Task 1: Ship plan {day:02d}\n",
        )
    for day in range(1, 13):
        date_str = f"2026-11-{day:02d}"
        slug = f"plan-{day:02d}"
        ledger_lines.append(f"- **[{date_str}] `{slug}`**: Completed plan {day:02d}")
    _write(repo / ".devtool" / "PROJECT_LEDGER.md", "\n".join(ledger_lines) + "\n")

    summary = harvest_epics_overview(repo)
    assert summary.completed == 12

    tp = extract_task_progress(repo, active_epic="active_epic")
    assert tp.total_tasks == 2
    assert tp.done_tasks == 1
    assert tp.todo_tasks == 1

    completed_epics = {t["epic"] for t in tp.completed_tasks}
    assert len(completed_epics) == 10
    expected_top_10 = {f"plan-{day:02d}" for day in range(3, 13)}
    assert completed_epics == expected_top_10
    assert "plan-01" not in completed_epics
    assert "plan-02" not in completed_epics


def test_kanban_dashboard_done_tab_top_10_cap_badges_and_plan_tasks_vm() -> None:
    """Node.js vm test for 4-tab Kanban Done filter, top-10 cap, badges, milestone synthesis, filter reset, roadmap badges, and signatures."""
    res = _eval_dashboard_js(
        r"""
        const ctx = createDashboardContext();

        const doneEpics = [
          {
            slug: 'done-ledger-newest',
            title: 'Direct ledger hotfix',
            status: 'done',
            source_kind: 'ledger',
            task_count: 0,
            completed_date: '2026-11-27',
            milestone_summary: 'Direct ledger hotfix',
            mtime: 1200,
            last_updated_human: '1h',
          },
          {
            slug: 'done-plan-second',
            title: 'Completed Standalone Plan',
            status: 'done',
            source_kind: 'plan',
            task_count: 2,
            completed_date: '2026-11-26',
            milestone_summary: 'Completed standalone plan summary',
            mtime: 1100,
            last_updated_human: '1d',
          },
          {
            slug: 'done-epic-third',
            title: 'Completed Classic Epic',
            status: 'done',
            source_kind: 'epic',
            task_count: 1,
            completed_date: '2026-11-25',
            milestone_summary: 'Completed classic epic summary',
            mtime: 1000,
            last_updated_human: '2d',
          },
        ];
        for (let i = 4; i <= 12; i++) {
          const pad = String(i).padStart(2, '0');
          doneEpics.push({
            slug: `done-item-${pad}`,
            title: `Completed Item ${pad}`,
            status: 'done',
            source_kind: 'plan',
            task_count: 5,
            completed_date: `2026-11-${String(25 - i).padStart(2, '0')}`,
            milestone_summary: `Shipped item ${pad}`,
            mtime: 1300 - i * 100,
            last_updated_human: `${i}d`,
          });
        }

        const repo = {
          name: 'demo-repo',
          path: '/tmp/demo-repo',
          active_epic: 'active-epic',
          active_stage: 'Stage 3 Phase 2 (TDD)',
          task_progress: {
            total_tasks: 1,
            done_tasks: 0,
            in_progress_tasks: 1,
            todo_tasks: 0,
            percentage: 0.0,
            task_completion_pct: 0.0,
            tasks: [
              {
                id: 'task_01',
                title: 'Task 1: Active epic task',
                status: 'in-progress',
                priority: 'high',
                epic: 'active-epic',
                source: 'worktree',
                labels: ['core'],
              },
            ],
            completed_tasks: [
              {
                id: 'task_01',
                title: 'Task 1: Build plan parser',
                status: 'done',
                priority: 'medium',
                epic: 'done-plan-second',
                source: 'plan',
                labels: ['plan'],
                time: '2026-11-26',
              },
              {
                id: 'task_02',
                title: 'Task 2: Ship plan UI',
                status: 'done',
                priority: 'medium',
                epic: 'done-plan-second',
                source: 'plan',
                labels: ['plan'],
                time: '2026-11-26',
              },
              {
                id: 'task_01',
                title: 'Task 1: Classic epic done task',
                status: 'done',
                priority: 'medium',
                epic: 'done-epic-third',
                source: 'root',
                labels: [],
                time: '2026-11-25',
              },
            ],
          },
          epics_summary: {
            total: 13,
            in_progress: 1,
            completed: 12,
            unstarted: 0,
            abandoned: 0,
            epics: [
              {
                slug: 'active-epic',
                title: 'Active Epic',
                status: 'in_progress',
                source_kind: 'epic',
                task_count: 1,
                mtime: 2000,
              },
              ...doneEpics,
            ],
          },
        };

        ctx.__testRepo = repo;
        vm.runInContext('currentReposData = [__testRepo];', ctx);
        const wrapper = ctx.document.createElement('div');
        wrapper.id = 'kanban-dashboard-wrapper-' + repo.name;
        wrapper.querySelector = () => null;
        ctx.document.body.appendChild(wrapper);

        // Initial Doing tab render
        const doingHtml = ctx.renderKanbanDashboard(repo, 'all');

        // Switch to Done tab via setKanbanExecutionFilter
        ctx.setKanbanExecutionFilter(repo.name, 'done');
        const doneHtml = wrapper.innerHTML;

        // Extract sidebar epic item order via onclick slugs
        const sidebarMatches = [...doneHtml.matchAll(/class="epic-progress-item"[\s\S]*?onclick="onFilterKanbanBoard\('demo-repo',\s*'([^']+)'\)"/g)].map(m => m[1]);

        // Select completed standalone plan on Done tab
        ctx.onFilterKanbanBoard(repo.name, 'done-plan-second');
        const selectedPlanHtml = wrapper.innerHTML;
        const filterAfterSelectPlan = vm.runInContext("currentKanbanFilter['demo-repo']", ctx);

        // Re-click Done tab -> preserves selected completed slug
        ctx.setKanbanExecutionFilter(repo.name, 'done');
        const filterAfterReclickDone = vm.runInContext("currentKanbanFilter['demo-repo']", ctx);

        // Select ledger-only milestone on Done tab -> synthesized milestone card
        ctx.onFilterKanbanBoard(repo.name, 'done-ledger-newest');
        const selectedLedgerHtml = wrapper.innerHTML;

        // Switch back to Doing -> resets filter to 'all'
        ctx.setKanbanExecutionFilter(repo.name, 'doing');
        const filterAfterSwitchDoing = vm.runInContext("currentKanbanFilter['demo-repo']", ctx);

        // Roadmap rows and signature checks
        const roadmapHtml = ctx.renderRoadmapTableRows(repo);
        const roadmapSigBefore = ctx.buildRoadmapSig(repo);
        repo.epics_summary.epics[2].source_kind = 'epic';
        const roadmapSigAfter = ctx.buildRoadmapSig(repo);
        repo.epics_summary.epics[2].source_kind = 'plan';

        // Kanban sig changes when completed_tasks, milestone_summary, or mtime changes
        const kanbanSigBefore = ctx.buildKanbanSig(repo, 'all');
        repo.task_progress.completed_tasks.push({
          id: 'task_03',
          title: 'Task 3: Extra completed item',
          status: 'done',
          priority: 'low',
          epic: 'done-plan-second',
          source: 'plan',
          labels: ['plan'],
        });
        const kanbanSigAfter = ctx.buildKanbanSig(repo, 'all');

        const kanbanSigBeforeMilestone = ctx.buildKanbanSig(repo, 'all');
        repo.epics_summary.epics[1].milestone_summary = 'Updated ledger hotfix summary';
        const kanbanSigAfterMilestone = ctx.buildKanbanSig(repo, 'all');
        repo.epics_summary.epics[1].milestone_summary = 'Direct ledger hotfix';

        const kanbanSigBeforeMtime = ctx.buildKanbanSig(repo, 'all');
        repo.epics_summary.epics[1].mtime = 1250;
        const kanbanSigAfterMtime = ctx.buildKanbanSig(repo, 'all');
        repo.epics_summary.epics[1].mtime = 1200;

        // Overview header hint
        const overviewHtml = ctx.renderEpicsOverviewAndApprovalGate(repo);

        console.log(JSON.stringify({
          doingHtml,
          doneHtml,
          sidebarMatches,
          selectedPlanHtml,
          selectedLedgerHtml,
          filterAfterSelectPlan,
          filterAfterReclickDone,
          filterAfterSwitchDoing,
          roadmapHtml,
          roadmapSigChanged: roadmapSigBefore !== roadmapSigAfter,
          kanbanSigChanged: kanbanSigBefore !== kanbanSigAfter,
          kanbanSigMilestoneChanged: kanbanSigBeforeMilestone !== kanbanSigAfterMilestone,
          kanbanSigMtimeChanged: kanbanSigBeforeMtime !== kanbanSigAfterMtime,
          overviewHtml,
        }));
        """
    )

    doing_html = res["doingHtml"]
    for tab in ("doing", "pending", "cancelled", "done"):
        assert f'data-kanban-exec-filter="{tab}"' in doing_html
    assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in doing_html

    done_html = res["doneHtml"]
    assert "RECENTLY COMPLETED" in done_html
    assert "10/12" in done_html

    # Top-10 cap in newest-first mtime order (NOT re-sorted by task_count or done/total)
    sidebar_slugs = res["sidebarMatches"]
    assert len(sidebar_slugs) == 10
    assert sidebar_slugs[0] == "done-ledger-newest"
    assert sidebar_slugs[1] == "done-plan-second"
    assert sidebar_slugs[2] == "done-epic-third"
    assert "done-item-11" not in sidebar_slugs
    assert "done-item-12" not in sidebar_slugs

    # Badges rendered for Plan, Epic, and Ledger
    assert ">Plan<" in done_html or "Plan</span>" in done_html
    assert ">Epic<" in done_html or "Epic</span>" in done_html
    assert ">Ledger<" in done_html or "Ledger</span>" in done_html

    # 0-task ledger entry renders Milestone + completed_date instead of 0/0 Tasks
    assert "Milestone · 2026-11-27" in done_html
    assert "0/0 Tasks" not in done_html

    # Selecting completed standalone plan shows its completed_tasks cards with Plan source footer and no bogus .en.md
    selected_plan_html = res["selectedPlanHtml"]
    assert "Task 1: Build plan parser" in selected_plan_html
    assert "Task 2: Ship plan UI" in selected_plan_html
    assert "📄 Plan" in selected_plan_html
    assert "done-plan-second.en.md" not in selected_plan_html

    # Selecting ledger-only milestone renders synthesized milestone summary card with Ledger footer and no bogus .en.md
    selected_ledger_html = res["selectedLedgerHtml"]
    assert "Direct ledger hotfix" in selected_ledger_html
    assert "📜 Ledger" in selected_ledger_html
    assert "done-ledger-newest.en.md" not in selected_ledger_html

    # Filter preservation on Done re-click and reset on switch to Doing
    assert res["filterAfterSelectPlan"] == "done-plan-second"
    assert res["filterAfterReclickDone"] == "done-plan-second"
    assert res["filterAfterSwitchDoing"] == "all"

    # Roadmap rows render Plan and Ledger badges for non-epic entries while keeping epic rows clean
    roadmap_html = res["roadmapHtml"]
    assert 'data-source-kind="plan"' in roadmap_html
    assert 'data-source-kind="ledger"' in roadmap_html
    assert 'data-source-kind="epic"' not in roadmap_html

    # Signature invalidation checks
    assert res["roadmapSigChanged"] is True
    assert res["kanbanSigChanged"] is True
    assert res["kanbanSigMilestoneChanged"] is True
    assert res["kanbanSigMtimeChanged"] is True

    # Overview header hint updated
    assert ".devtool/epic/ · plans/" in res["overviewHtml"]
