# Check-Tasks Kanban Sticky Overview and Epic-Scoped Stage Telemetry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use d3nexus:subagent-driven-development (recommended) or d3nexus:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `/check-tasks` so the Kanban `220px` Overview panel stays pinned, all five status columns scroll inside one unified horizontal track with zero per-column horizontal scrollbars, standalone vertical stage titles drop orphan numeric prefixes (`Tasks: ...`), and pipeline telemetry counts tasks strictly per epic rather than mixing repository-wide totals.

**Architecture:** Normalize stage-summary labels and epic-scoped task tallies in `skills/check-tasks/resources/scripts/check_tasks.py` (deduplicating tasks by `(normalized_epic, task_id)` and reconciling promoted `.devtool/features/` tasks with packaged `.devtool/epic/<slug>/task_*.md` counts). Enforce strict CSS Grid containment (`220px minmax(0, 1fr)`), `position: sticky; left: 0`, `overflow-x: hidden` on `.kanban-col-cards`, ellipsis truncation on long epic identifiers, stripped vertical stage titles, and epic-scoped JS counts in `skills/check-tasks/resources/dashboard/tasks_dashboard.html`.

**Tech Stack:** Python 3.11+, HTML5 / CSS Grid / Vanilla JavaScript (ES2020), `pytest`, Node.js `vm` harness, Chrome DevTools (`browser` subagent).

**Spec:** [2026-11-18-check-tasks-kanban-and-stage-title-fixes-design.md](../specs/2026-11-18-check-tasks-kanban-and-stage-title-fixes-design.md)

## Table of Contents

- [Global Constraints](#global-constraints)
- [File Structure](#file-structure)
- [ Implementation Tasks](#implementation-tasks)
  - [Task 1: Epic-Scoped Telemetry Counts, Multi-Wave Task Parity, and Stripped Stage Summary Labels in check_tasks.py](#task-1-epic-scoped-telemetry-counts-multi-wave-task-parity-and-stripped-stage-summary-labels-in-check_taskspy)
  - [Task 2: Sticky Kanban Overview, Single 5-Column Horizontal Scroll, Unnumbered Sub-Step Headers, and Live Browser Verification in tasks_dashboard.html](#task-2-sticky-kanban-overview-single-5-column-horizontal-scroll-unnumbered-sub-step-headers-and-live-browser-verification-in-tasks_dashboardhtml)
  - [Task 3: Non-Shrinking Kanban Cards, Horizontal Trackpad Wheel Bridge Over Column Items, and Compact 210px Column Width](#task-3-non-shrinking-kanban-cards-horizontal-trackpad-wheel-bridge-over-column-items-and-compact-210px-column-width)

## Global Constraints

- Always invoke `pytest` as `python3 -m pytest` from the repository/worktree root so `from tests....` imports resolve cleanly.
- Keep horizontal 6-pill stepper `stage.label` values as `"1. Spec"`, `"2. HLD & Principal"`, `"3. Tasks"`, `"4. Gate 4 QA"`, `"5. Cross-Review"`, `"6. Finish"` to preserve existing `test_ltsp_dashboard_ui.py` and `test_cehm_dashboard_modal_ui.py` contracts; strip `^\d+\.\s*` ONLY on standalone vertical headers (`buildSubStepsHtml`) and `active_sub_step_summary` / Kanban epic stage summaries.
- Follow Universal Commit Message Format (`[CHECK_TASKS] Imperative title` + `- bullet` lines, zero `Co-Authored-By:` or tool trailers). Never run `git push`.
- Never open, grep, or glob `*.vi.md` files (Rule 11).

---

## File Structure

- Modify: `skills/check-tasks/resources/scripts/check_tasks.py` — `_strip_stage_index_prefix()`, `(normalized_epic, task_id)` deduplication and features-frontmatter `candidate_epics` discovery in `extract_task_progress()`, worktree-aware `task_count` in `harvest_epics_overview()`, `done_tasks`/`total_tasks` emission + `max(total_tasks, dir_task_count)` in `build_epic_pipeline_telemetry()`, and epic-filtered `done_tasks` / `total_tasks` in `scan_repo()` and `derive_lifecycle_state()`.
- Modify: `skills/check-tasks/resources/dashboard/tasks_dashboard.html` — `stripStageIndexPrefix()`, `buildSubStepsHtml()`, `synthesizePipelineTelemetry()`, `computeEpicProgressState()`, `renderExecutionEpics()`, `renderKanbanDashboard()`, `buildKanbanSig()`, Tier 1 container `min-width: 0`, and `openKanbanModal()`.
- Create: `tests/test_check_tasks_kanban_and_telemetry_fixes.py` — Python unit/integration tests for `check_tasks.py` and Node.js `vm` DOM/CSS/JS verification tests for `tasks_dashboard.html`.

## Implementation Tasks

### Task 1: Epic-Scoped Telemetry Counts, Multi-Wave Task Parity, and Stripped Stage Summary Labels in check_tasks.py

**Files:**
- Modify: `skills/check-tasks/resources/scripts/check_tasks.py:1330-1380`
- Modify: `skills/check-tasks/resources/scripts/check_tasks.py:1533-1785`
- Modify: `skills/check-tasks/resources/scripts/check_tasks.py:2274-2303`
- Modify: `skills/check-tasks/resources/scripts/check_tasks.py:2835-2850`
- Modify: `skills/check-tasks/resources/scripts/check_tasks.py:3280-3355`
- Modify: `skills/check-tasks/resources/scripts/check_tasks.py:4645-4665`
- Modify: `skills/check-tasks/resources/scripts/check_tasks.py:4775-4792`
- Create: `tests/test_check_tasks_kanban_and_telemetry_fixes.py`

**Interfaces:**
- Consumes: `harvest_epics_overview(repo_path, active_epic)`, `extract_task_progress(repo_path, active_epic)`, `derive_lifecycle_state(...)`, `build_epic_pipeline_telemetry(...)`, `scan_repo(repo_path)` in `skills/check-tasks/resources/scripts/check_tasks.py`.
- Produces:
  - `_strip_stage_index_prefix(label: str) -> str` in `check_tasks.py`
  - `active_sub_step_summary` formatted without leading `"1. "`..`"6. "` (for example `"Tasks · 4/4 (100%)"`)
  - Top-level `"done_tasks"` and `"total_tasks"` on `pipeline_telemetry` and `"total_tasks"` / `"done_tasks"` on `stages[2]` (`id == "tasks"`)
  - Epic-scoped `done_tasks` and `total_tasks` in `repo.pipeline_telemetry` and `epics_summary[].pipeline_telemetry`, with `seen_tasks` keyed by `(_normalize_slug(epic), task_id)`, worktree-aware `task_count` in `harvest_epics_overview()`, and `total_tasks = max(total_tasks, dir_task_count)`.

- [ ] **Step 1: Write the failing backend unit and integration tests**

Create `tests/test_check_tasks_kanban_and_telemetry_fixes.py`:

```python
"""Tests for check-tasks Kanban sticky layout, unnumbered stage summaries, and epic-scoped telemetry."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECK_TASKS_PATH = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts" / "check_tasks.py"


@pytest.fixture(scope="module")
def check_tasks_mod():
    spec = importlib.util.spec_from_file_location("check_tasks_under_test", CHECK_TASKS_PATH)
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
        lambda rp, slug: [wt] if "translation_studio" in str(slug) else [],
    )
    monkeypatch.setattr(
        check_tasks_mod,
        "extract_worktrees",
        lambda rp: [
            check_tasks_mod.WorktreeInfo(
                path=str(rp), branch="main", head="abc1234", is_dirty=False, dirty_file_count=0
            ),
            check_tasks_mod.WorktreeInfo(
                path=str(wt),
                branch="epic/translation_studio_sync_and_standalone",
                head="def5678",
                is_dirty=False,
                dirty_file_count=0,
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
    assert tasks_stage["total_tasks"] == 5
    assert not pt["active_sub_step_summary"].startswith(("1.", "2.", "3.", "4.", "5.", "6."))


def test_multi_wave_packaged_epic_uses_epic_dir_total_count(
    tmp_path: Path, check_tasks_mod
) -> None:
    """When Wave 1 promoted 4 tasks to .devtool/features/done/ while 20 task_*.md exist in .devtool/epic/<slug>/, telemetry reports 4/20 (20%)."""
    repo = tmp_path / "wave-repo"
    (repo / ".git").mkdir(parents=True)
    epic_slug = "multi_wave_epic"
    epic_dir = repo / ".devtool" / "epic" / epic_slug
    epic_dir.mkdir(parents=True)
    (epic_dir / f"{epic_slug}.md").write_text("# Epic\n\n- **Status**: In Progress\n", encoding="utf-8")

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
    assert pt["total_tasks"] == 20
    tasks_stage = next(s for s in pt["stages"] if s["id"] == "tasks")
    assert tasks_stage["summary"] == "4/20 (20%)"
    assert tasks_stage["total_tasks"] == 20
    assert pt["active_sub_step_summary"] == "Tasks · 4/20 (20%)"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_check_tasks_kanban_and_telemetry_fixes.py -v`
Expected: FAIL (`progress.total_tasks == 20` instead of `21`, `pt["task_completion_pct"]` contaminated by backlog epic, `pt["active_sub_step_summary"]` starts with `"3. "` or `"4. "`, and `4/20` reported as `4/4`).

- [ ] **Step 3: Implement minimal backend fixes in `skills/check-tasks/resources/scripts/check_tasks.py`**

1. In `harvest_epics_overview()` (`check_tasks.py` around line `1343`):
   - When computing `task_count` for epic directory `d`, also inspect any matching worktree epic directories `_find_epic_dirs_for_checkout(wt_path, slug)` and take `max(...)` of `len(list(ed.glob("task_*.md")))` so epics packaged inside a linked worktree report accurate `task_count`.
2. In `extract_task_progress()` (`check_tasks.py` around lines `1540-1760`):
   - Change `seen_tasks: set[str] = set()` to `seen_tasks: set[tuple[str, str]] = set()`.
   - Also allow root `.devtool/features/task_*.md` whose `epic` frontmatter is not in `completed_slugs` or `abandoned_slugs` to register into `candidate_epics` (or pass through when non-completed/non-abandoned) even if no `.devtool/epic/<slug>/` folder exists yet.
   - Key `seen_tasks` by `(_normalize_slug(ep), task_id)` in Rule 3 (worktree loop) and `(_normalize_slug(str(task_epic)), task_id)` in Rule 2 (root loop).
3. In `derive_lifecycle_state()` (`check_tasks.py` around lines `2277-2285`):
   - Reconcile `active_total` with packaged `task_*.md` count across root + worktree epic directories (`active_total = max(len(active_tasks), packaged_dir_task_count)`) so Wave 1 (`4/20`) does not prematurely report `"Tasks Done (Running Gate 4 Verification)"`.
4. In `build_epic_pipeline_telemetry()` (`check_tasks.py` around lines `2842` and `3281-3354`):
   - Replace `if total_tasks == 0 and dir_task_count > 0: total_tasks = dir_task_count` with `if dir_task_count > total_tasks: total_tasks = dir_task_count`.
   - Add `"done_tasks": done_tasks` and `"total_tasks": total_tasks` both onto `stages[2]` (`id == "tasks"`) and onto the returned `pipeline_telemetry` dictionary.
   - Add `_strip_stage_index_prefix(label: str) -> str` (`re.sub(r"^\d+\.\s*", "", str(label or "").strip())`) and format `active_sub_summary = f"{_strip_stage_index_prefix(str(cur_stage_obj['label']))} · {cur_stage_obj['summary']}"`.
5. In `scan_repo()` (`check_tasks.py` around lines `4647-4663` and `4775-4790`):
   - Filter `task_progress.tasks` to `_normalize_slug(active_epic)` when computing `done_tasks` and `total_tasks` for `repo.pipeline_telemetry` (falling back to `task_progress.done_tasks`/`total_tasks` only when all tasks in `task_progress.tasks` belong to at most 1 epic).
   - Around line `4775`, populate `ep["pipeline_telemetry"]` whenever `ep.get("status") == "in_progress" or _normalize_slug(slug) == _normalize_slug(active_epic or "")`, using `ep_tot = max(len(ep_tasks), int(ep.get("task_count") or 0))` and propagating `ep["task_count"] = max(int(ep.get("task_count") or 0), int(ep["pipeline_telemetry"].get("total_tasks") or 0))`.

- [ ] **Step 4: Run tests to verify GREEN and zero regressions**

Run: `python3 -m pytest tests/test_check_tasks_kanban_and_telemetry_fixes.py tests/test_ltsp_dashboard_ui.py tests/test_cehm_dashboard_modal_ui.py -q --tb=short`
Expected: PASS (`0 failures`).

- [ ] **Step 5: Commit Task 1**

```bash
git add skills/check-tasks/resources/scripts/check_tasks.py tests/test_check_tasks_kanban_and_telemetry_fixes.py
git commit -m "[CHECK_TASKS] Scope pipeline telemetry per epic and strip stage summary prefix" \
  -m "- Deduplicate scanned tasks by normalized epic slug plus stem" \
  -m "- Reconcile promoted wave tasks with packaged epic task counts and isolate active epic tallies" \
  -m "- Strip leading numeric index from active_sub_step_summary while preserving stepper pill labels"
```

---

### Task 2: Sticky Kanban Overview, Single 5-Column Horizontal Scroll, Unnumbered Sub-Step Headers, and Live Browser Verification in tasks_dashboard.html

**Files:**
- Modify: `skills/check-tasks/resources/dashboard/tasks_dashboard.html:2392-2495`
- Modify: `skills/check-tasks/resources/dashboard/tasks_dashboard.html:2730-2815`
- Modify: `skills/check-tasks/resources/dashboard/tasks_dashboard.html:2960-2990`
- Modify: `skills/check-tasks/resources/dashboard/tasks_dashboard.html:3170-3455`
- Modify: `skills/check-tasks/resources/dashboard/tasks_dashboard.html:3915-3980`
- Modify: `skills/check-tasks/resources/dashboard/tasks_dashboard.html:5220-5262`
- Modify: `tests/test_check_tasks_kanban_and_telemetry_fixes.py`

**Interfaces:**
- Consumes: `active_sub_step_summary`, `epics_summary[].task_count`, and `pipeline_telemetry` from Task 1.
- Produces:
  - `stripStageIndexPrefix(label)` in `tasks_dashboard.html`
  - Pinned `220px` `OVERVIEW` sidebar (`data-kanban-overview="pinned"`, `position: sticky; left: 0; z-index: 3`) inside `grid-template-columns: 220px minmax(0, 1fr)`
  - Single horizontal scroll track `.kanban-columns-scroll` (`overflow-x: auto; overflow-y: hidden`) with `.kanban-col-cards` locked to `overflow-x: hidden; overflow-y: auto` and truncated long epic links/chips
  - Epic-scoped `totalCount` reconciling `epicTasks.length` with `epicMeta.task_count` and `pipeline_telemetry`.

- [ ] **Step 1: Write the failing frontend Node VM tests in `tests/test_check_tasks_kanban_and_telemetry_fixes.py`**

Append Node VM tests (reusing `_eval_dashboard_js` from `tests/test_ltsp_dashboard_ui.py`) to `tests/test_check_tasks_kanban_and_telemetry_fixes.py` asserting:
1. `renderKanbanDashboard` renders `grid-template-columns: 220px minmax(0, 1fr)`, pins `[data-kanban-overview="pinned"]` with `position: sticky; left: 0`, sets `overflow-x: auto; overflow-y: hidden` on `.kanban-columns-scroll`, sets `overflow-x: hidden` on every `.kanban-col-cards`, and applies `text-overflow: ellipsis` on long unbroken epic slugs (`translation_studio_sync_and_standalone_very_long_epic_identifier`).
2. `buildSubStepsHtml` renders `<strong>Tasks:</strong>` (NOT `3. Tasks:`) and `synthesizePipelineTelemetry().active_sub_step_summary` omits `"3. "`, while `buildStagePillsHtml` still renders `1. Spec` .. `6. Finish`.
3. `renderExecutionEpics` and `renderKanbanDashboard` report `4 / 20 Completed (20%)` and `'Promoting next wave tasks...'` (NOT `4 / 4 Completed (20%)` or `'All tasks completed ✓'`) when 4 Wave-1 tasks are promoted and `epicMeta.task_count` is `20`, and report `4 / 4 Completed (100%)` for a 4-task active epic alongside 16 tasks of a second backlog epic.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_check_tasks_kanban_and_telemetry_fixes.py -v`
Expected: FAIL on sticky Overview attribute/grid rule, missing `overflow-x: hidden` on `.kanban-col-cards`, `"3. Tasks:"` prefix in `buildSubStepsHtml`, and `4 / 4 Completed (20%)` mismatch.

- [ ] **Step 3: Implement frontend fixes in `skills/check-tasks/resources/dashboard/tasks_dashboard.html`**

1. Add helper near `buildStagePillsHtml()`:
   ```javascript
   function stripStageIndexPrefix(label) {
     return String(label || '').replace(/^\d+\.\s*/, '').trim();
   }
   ```
   - In `synthesizePipelineTelemetry()` (`L2746`): set `active_sub_step_summary: `${stripStageIndexPrefix(curSt.label)} · ${curSt.summary}``.
   - In `buildSubStepsHtml()` (`L2806`): render `<strong style="color: #cbd5e1;">${escapeHtml(stripStageIndexPrefix(activeStageObj.label))}:</strong> ${escapeHtml(String(activeStageObj.summary || ''))}`.
   - In `renderKanbanDashboard()` (`L3246`): strip any leading stage index via `stripStageIndexPrefix(kanbanStageSummary)`.
2. Fix epic-scoped task count reconciliation:
   - In `computeEpicProgressState()` (`L2427`): only fall back to `repo.task_progress?.task_completion_pct` when `(repo.epics_summary?.epics || []).length <= 1` and all `repo.task_progress?.tasks` belong to at most one epic.
   - In `renderExecutionEpics()` (`L2964-2988`):
     ```javascript
     const epicPt = epicMeta?.pipeline_telemetry || (slugsMatch(repo.active_epic, slug) ? repo.pipeline_telemetry : null) || null;
     const ptTotalCount = Number(epicPt?.total_tasks || epicPt?.stages?.[2]?.total_tasks || 0);
     const rawEpicTasksCount = epicTasks.length > 0
       ? epicTasks.length
       : (slugsMatch(repo.active_epic, slug) && (repo.epics_summary?.epics || []).length <= 1 ? (repo.task_progress?.total_tasks || 0) : 0);
     const metaTaskCount = Number(epicMeta?.task_count || 0);
     const totalCount = Math.max(rawEpicTasksCount, metaTaskCount, ptTotalCount);
     const doneCount = epicTasks.length > 0
       ? epicTasks.filter(t => t.status === 'done').length
       : (slugsMatch(repo.active_epic, slug) && (repo.epics_summary?.epics || []).length <= 1 ? (repo.task_progress?.done_tasks || 0) : 0);
     ```
     Guard `if (isPrimaryActive && repo.task_progress?.active_task_name && epicTasks.length === 0 && (repo.epics_summary?.epics || []).length <= 1)` so another epic's `in-progress` task never overrides `activeTaskName`. When `!inProgTask && !nextTodoTask`, if `totalCount > 0 && doneCount >= totalCount` -> `'All tasks completed ✓'`, else if `doneCount > 0 && doneCount < totalCount` -> `'Promoting next wave tasks...'`, else `'Setting up tasks...'`.
   - In `renderKanbanDashboard()` (`L3174-3191`): match `epicsProgressMap` entries via `slugsMatch()` (not strict key equality alone), and compute `item.total = Math.max(item.total, Number(summaryEp.task_count || 0), Number(summaryEp.pipeline_telemetry?.total_tasks || summaryEp.pipeline_telemetry?.stages?.[2]?.total_tasks || 0))`. Also include `Number(e.task_count || 0)` in `buildKanbanSig()` (`L3468-3476`).
3. Fix Kanban CSS & DOM containment (`renderKanbanDashboard`, Tier 1 wrapper, and `openKanbanModal`):
   - On `#repo-detail-content-${escapeHtml(repo.name)}` (`L3916`), Tier 1 card (`L3921`), and `#kanban-dashboard-wrapper-${escapeHtml(repo.name)}` (`L3974`), add `min-width: 0; max-width: 100%;`.
   - In `renderKanbanDashboard()`:
     - Outer grid (`L3375`): `<div class="kanban-board-shell" style="display: grid; grid-template-columns: 220px minmax(0, 1fr); width: 100%; max-width: 100%; min-height: 680px; position: relative; overflow: hidden;">`
     - Left `OVERVIEW` sidebar (`L3378`): `<div data-kanban-overview="pinned" style="width: 220px; min-width: 220px; max-width: 220px; position: sticky; left: 0; z-index: 3; background: #090c14; border-right: 1px solid #1e2638; padding: 18px 16px; display: flex; flex-direction: column; flex-shrink: 0;">`
     - Right columns scroll track (`L3448`): `<div class="kanban-columns-scroll" data-scroll-id="kanban-board-scroll-${escapeHtml(repo.name)}" style="min-width: 0; width: 100%; overflow-x: auto; overflow-y: hidden; display: grid; grid-template-columns: repeat(5, minmax(260px, 1fr)); gap: 0; background: #0c0f17;">`
     - Each `.kanban-col` (`L3359`): add `min-width: 0; overflow: hidden;`.
     - Each `.kanban-col-cards` (`L3367`): add `min-width: 0; overflow-x: hidden; overflow-y: auto;`.
     - Each `.kanban-task-card` (`L3325-3347`): add `min-width: 0; max-width: 100%; overflow: hidden;`; add `overflow-wrap: anywhere; word-break: break-word; min-width: 0;` on task title `<strong>`; add `overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%;` on the Epic link row (`L3333-3336`) and `max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: inline-block;` on the `🗂 ${escapeHtml(t.epic)}` chip (`L3339-3341`).
   - In `openKanbanModal()` (`L5225-5260`): wrap the 5 columns in `<div class="kanban-columns-scroll" style="min-width: 0; width: 100%; overflow-x: auto; overflow-y: hidden; display: grid; grid-template-columns: repeat(5, minmax(240px, 1fr)); gap: 10px;">` and add `min-width: 0; overflow-x: hidden;` on each column and card.

- [ ] **Step 4: Run automated tests to verify GREEN**

Run: `python3 -m pytest tests/test_check_tasks_kanban_and_telemetry_fixes.py tests/test_ltsp_dashboard_ui.py tests/test_cehm_dashboard_modal_ui.py tests/test_rsdh_tasks_dashboard_ui.py -q --tb=short`
Expected: PASS (`0 failures`).

- [ ] **Step 5: Live Web Browser Verification (`browser` subagent)**

Start a local `tasks_server.py` instance from the worktree on an ephemeral port (e.g. `18766`), invoke the `browser` subagent to open `http://127.0.0.1:18766`, switch to `lyrics-sync` (or active multi-epic repo), inspect computed styles (`getComputedStyle` & `getBoundingClientRect` on `[data-kanban-overview="pinned"]`, `.kanban-columns-scroll`, and `.kanban-col-cards`), scroll `.kanban-columns-scroll` horizontally and verify `OVERVIEW` bounding `left` remains unchanged, verify sub-step header renders `Tasks:` without `3.`, verify zero console errors, capture screenshot evidence, and shut down the temporary server.

- [ ] **Step 6: Commit Task 2**

```bash
git add skills/check-tasks/resources/dashboard/tasks_dashboard.html tests/test_check_tasks_kanban_and_telemetry_fixes.py
git commit -m "[CHECK_TASKS] Pin Kanban Overview, unify 5-column scroll, and drop orphan stage prefix" \
  -m "- Lock Kanban outer grid to 220px minmax(0, 1fr) with sticky Overview and single horizontal scroll track" \
  -m "- Set overflow-x hidden on column card lists and truncate long unbroken epic identifiers" \
  -m "- Strip leading numeric index from vertical sub-step titles and reconcile multi-wave task counts"
```

---

### Task 3: Non-Shrinking Kanban Cards, Horizontal Trackpad Wheel Bridge Over Column Items, and Compact 210px Column Width

**Files:**
- Modify: `skills/check-tasks/resources/dashboard/tasks_dashboard.html:550-605`
- Modify: `skills/check-tasks/resources/dashboard/tasks_dashboard.html:3385-3515`
- Modify: `skills/check-tasks/resources/dashboard/tasks_dashboard.html:5288-5325`
- Modify: `tests/test_check_tasks_kanban_and_telemetry_fixes.py`

**Interfaces:**
- Consumes: `renderKanbanDashboard()`, `openKanbanModal()`, `.kanban-task-card`, `.kanban-col-cards`, `.kanban-columns-scroll`.
- Produces:
  - `flex-shrink: 0` on `.kanban-task-card`, `.kanban-task-card > div`, and `.kanban-col > div:first-child` so 16+ task cards in a single column preserve full 4-row height (`>= 105px`) and scroll vertically rather than collapsing to `32px`.
  - Split `overscroll-behavior`: `.kanban-col-cards` uses `overscroll-behavior-y: contain; overscroll-behavior-x: auto;` while `.kanban-columns-scroll` uses `overscroll-behavior-x: contain;`.
  - `ensureKanbanHorizontalWheelBridge()` delegated `{ passive: false }` `wheel` handler forwarding horizontal-dominant gestures (`Math.abs(deltaX) > Math.abs(deltaY)`) anywhere inside `.kanban-columns-scroll` (including over 16-card `.kanban-col-cards` bodies) directly to `scroller.scrollLeft`, while preserving native vertical column scroll when `Math.abs(deltaY) >= Math.abs(deltaX)`.
  - Compact default column width `repeat(5, minmax(210px, 1fr))` in both `renderKanbanDashboard()` and `openKanbanModal()` (`#modal-kanban`).

- [ ] **Step 1: Write failing Node VM and Headless Chrome CDP E2E tests**

Update `tests/test_check_tasks_kanban_and_telemetry_fixes.py` to assert:
1. `repeat(5, minmax(210px, 1fr))` in both `renderKanbanDashboard()` and `openKanbanModal()`, `flex-shrink: 0` on `.kanban-task-card` and its inner rows, and `overscroll-behavior-x: auto` on `.kanban-col-cards`.
2. In `test_live_chrome_cdp_kanban_sticky_scroll_and_unnumbered_stage_titles`:
   - At `1180x900` viewport, all 16 `Backlog` task cards render with `height >= 100px`, `flexShrink === "0"`, all 4 internal rows visible (`childHeight >= 12` and `childBottom <= cardBottom`), and `backlogCol.scrollHeight > backlogCol.clientHeight + 500`.
   - Real CDP `Input.dispatchMouseEvent` (`type: "mouseWheel"`, `deltaX: 140, deltaY: 10`) dispatched over Card #2 in the 16-card `Backlog` column advances `.kanban-columns-scroll.scrollLeft >= 130` while keeping `backlogCol.scrollTop == 0` and `[data-kanban-overview="pinned"]` `left` invariant.
   - Real CDP vertical `mouseWheel` (`deltaX: 6, deltaY: 220`) over the 16-card `Backlog` column advances `backlogCol.scrollTop >= 180` without altering `scrollLeft`.
   - Each column measures `210px` wide at `1180x900` and all 5 columns fit cleanly without horizontal overflow at `1366x900`.

- [ ] **Step 2: Run test to verify RED failure**

Run: `python3 -m pytest tests/test_check_tasks_kanban_and_telemetry_fixes.py -v`
Expected: FAIL (`cardHeight == 32`, `scrollLeft == 0` on `mouseWheel`, and `260px` column width).

- [ ] **Step 3: Implement CSS, `ensureKanbanHorizontalWheelBridge()`, and `210px` column width in `tasks_dashboard.html`**

Apply the surgical CSS and wheel-bridge updates in `skills/check-tasks/resources/dashboard/tasks_dashboard.html`.

- [ ] **Step 4: Run automated tests, visually inspect screenshots, and execute `@quality_check`**

Run: `python3 -m pytest tests/test_check_tasks_kanban_and_telemetry_fixes.py tests/test_ltsp_dashboard_ui.py tests/test_cehm_dashboard_modal_ui.py tests/test_rsdh_tasks_dashboard_ui.py -v`
Inspect rendered PNG screenshots at `1366x900` and `1180x900` via `read_file`, then run `@quality_check` and `scripts/verify.sh`.

- [ ] **Step 5: Commit Task 3**

```bash
git add skills/check-tasks/resources/dashboard/tasks_dashboard.html tests/test_check_tasks_kanban_and_telemetry_fixes.py
git commit -m "[CHECK_TASKS] Fix Kanban 16-card collapse, 5-column horizontal wheel scroll, and 210px column width" \
  -m "- Add flex-shrink 0 to Kanban task cards and inner rows so multi-card columns scroll vertically instead of collapsing" \
  -m "- Split overscroll-behavior axes and add horizontal-dominant wheel bridge across all 5 status columns" \
  -m "- Reduce default Kanban column min-width from 260px to 210px and verify via Chrome CDP mouseWheel E2E"
```
