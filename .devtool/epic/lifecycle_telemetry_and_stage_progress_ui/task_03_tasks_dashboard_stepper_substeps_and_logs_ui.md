---
id: "task_03_tasks_dashboard_stepper_substeps_and_logs_ui"
status: "done"
priority: "high"
assignee: null
epic: "lifecycle_telemetry_and_stage_progress_ui"
dueDate: null
created: "2026-11-14T09:05:00Z"
modified: "2026-11-14T03:14:45Z"
completedAt: "2026-11-14T03:14:45Z"
labels: ["dashboard-ui", "stepper", "sub-steps", "kanban-overview", "event-logs"]
order: "a3"
review_tier: "full"
---

# Task 3: Tasks Dashboard 6-Stage Stepper, Sub-Step Bar, Dual Progress, Log Stream, and Kanban Overview UI

Epic: [lifecycle_telemetry_and_stage_progress_ui](lifecycle_telemetry_and_stage_progress_ui.en.md)

## Requirement Analysis

Update `skills/check-tasks/resources/dashboard/tasks_dashboard.html` so Section II ("Triển khai Epic") and the Kanban Board `"TIẾN ĐỘ EPICS"` sidebar render the complete 6-stage `/dev-lifecycle` pipeline, decoupled `100%` task completion vs. weighted lifecycle progress, active stage micro-steps (`sub_steps`), collapsible rolling event logs (`events`), and live Kanban epic stage overview:

1. **Decoupled Task Progress (`taskPct = 100%`) vs. Weighted Lifecycle Progress (`pct`) in `computeEpicProgressState()` (`L2058-L2107`)**:
   - Compute `taskPct = total > 0 ? Math.round((done / total) * 100) : 0` (reaches **`100`** immediately when `done >= total > 0`, never capped at `95%` or `96%`).
   - Prefer `pipeline_telemetry.lifecycle_progress_pct` (from `summaryEp?.pipeline_telemetry || (isAct ? repo.pipeline_telemetry : null)`) for `pct` when present; otherwise synthesize weighted 6-stage progress (`10% -> 25% -> 80% -> 88% -> 96% -> 98%/100%`) from `active_stage`, `done/total`, `quality_active`, and `heartbeat` as a graceful fallback for legacy payloads.
   - Return `{ isFullyDone, epNeedsConfirm, isWaitingFinish, pct, taskPct, pipelineTelemetry }`.
2. **6-Stage Pipeline Stepper, Active Micro-Steps Strip & Expandable Event Logs (`renderPipelineStepper` & `renderLiveTelemetryBanner` `L2136-L2196` & `renderExecutionEpics` `L2198-L2399`)**:
   - In `renderExecutionEpics()` (`L2198-L2399`):
     - Render **Dual Progress Header**:
       - Left indicator: `Tiến độ Tasks: ${done} / ${total} Hoàn thành (${taskPct}%${taskPct === 100 ? ' ✓' : ''})` (so `9 / 9 Hoàn thành (100% ✓)` is prominently shown as soon as all tasks finish).
       - Right indicator & main progress bar: weighted lifecycle percentage (`pct%`) and stage status badge (`⚡ ${pct}% · ${activeStageLabel}`, `⚠️ Chờ /finish`, or `✓ 100% Hoàn tất`).
     - Render **`[data-telemetry="pipeline-stepper"]`**:
       - 6 stage pills (`1. Spec`, `2. HLD & Principal`, `3. Tasks`, `4. Gate 4 QA`, `5. Cross-Review`, `6. Finish`) showing `done` (`✓`), `running` (`⚡`), `action_required` (`⚠️`), `failed` (`✗`), or `pending` (`•`) states with each stage's `summary`.
     - Render **`[data-telemetry="sub-steps"]`**:
       - Shows the active stage's granular `sub_steps` sequence:
         - For **Principal Review / Cross-Model Review**: Round header (`Round 1/3 · codex (gpt-6.1-sol)`) followed by `[1. Reviewing] -> [2. Lập bảng triage] -> [3. Fix findings] -> [4. Verifying]` with status badges (`passed`/`done`, `running`, `failed`/`action_required`, `pending`) and verdict/action detail.
         - For **Gate 4 Quality Check** (also tagged inside `[data-telemetry="quality"]`): step chips for `Epic Audit`, `BDD Traceability`, `Static Lint`, `Typecheck`, `PyCore / Unit Test`, `Unit & Integration Test`, `Integration Test`, `UI / E2E Test`, `Architecture Gate` with `step_index/step_total` and elapsed time.
         - For **Task Implementation**: Wave badge (`Wave k`), active worker slots (`Slot 1: task_02 (working/review)`), and `Done: done/total (taskPct%)`.
     - Render **`[data-telemetry="event-logs"]`**:
       - Collapsible rolling event log stream displaying the latest 4 entries from `heartbeat.events` (or `pipeline_telemetry.events`) by default, with a toggle button (`Xem tất cả N logs ▾` / `Thu gọn ▴`) backed by an in-memory `expandedEventLogsByEpic` Set so the expanded state persists across 2s `pollDashboard()` re-renders.
3. **Kanban Sidebar `"TIẾN ĐỘ EPICS"` Stage Overview & Weighted Progress (`renderKanbanDashboard` `L2401-L2726`)**:
   - Seed `epicsProgressMap` (`L2432-L2468`) not only from `allTasks`, but also from `repo.epics_summary.epics` for any epic with `status === 'in_progress'` or matching `repo.active_epic` (so Stage 1 Spec and early Stage 2 HLD epics with `0` tasks still appear in `"TIẾN ĐỘ EPICS"`).
   - In each `.epic-progress-item` card (`L2479-L2551`):
     - Display `pct%` (weighted lifecycle progress, e.g. `18%`, `80%`, `92%`, `98%`, `100%`) on the top right and as the progress bar width.
     - Display `${ep.done}/${ep.total} Tasks${ep.total > 0 ? ` (${progState.taskPct}%)` : ''}` on the bottom left and `statusText` on the bottom right.
     - Add an overview row `<div data-telemetry="kanban-epic-stage" ...>` inside `.epic-progress-item` showing the current `/dev-lifecycle` stage and active micro-step summary (e.g. `Stage 2: HLD & Principal · R1 Reviewing`, `Stage 3: Tasks (4/4 · 100% ✓)`, `Stage 4: Gate 4 QA · PyCore (3/5)`, `Stage 5: Cross-Review · R1 Lập bảng triage`), so the user immediately sees which step the epic is in from the Kanban sidebar.
4. **Live Polling Signatures (`buildKanbanSig` `L2728-L2743` & `buildTier2Sig` `L2766-L2805`)**:
   - Include `pipeline_telemetry` (`lifecycle_progress_pct`, `task_completion_pct`, `current_stage_index`, `active_sub_step_summary`, stage statuses/sub-steps, `review_state`, `quality_active.steps`, and `heartbeat.events` length/latest timestamp) in both `buildTier2Sig(repo)` and `buildKanbanSig(repo, selectedEpicFilter)` so both Section II and the Kanban `"TIẾN ĐỘ EPICS"` sidebar update immediately on every sub-step or event log change without touching Section I or Section III Roadmap DOM focus.
5. Add unit/DOM integration tests in `tests/test_ltsp_dashboard_ui.py` covering `LTSP-HP-05`, `LTSP-EC-03`, `LTSP-ST-03`, `LTSP-AR-02`, and `LTSP-FR-02`, and align any affected assertions in `tests/test_rsdh_tasks_dashboard_ui.py`.

## Files

Allowed files:
- `skills/check-tasks/resources/dashboard/tasks_dashboard.html`
- `tests/test_ltsp_dashboard_ui.py` (new)
- `tests/test_rsdh_tasks_dashboard_ui.py`

Read-only context:
- `.devtool/epic/lifecycle_telemetry_and_stage_progress_ui/lifecycle_telemetry_and_stage_progress_ui.en.md` — HLD UI & Telemetry Contract
- `.devtool/epic/lifecycle_telemetry_and_stage_progress_ui/bdd_scenarios.en.md` — Canonical BDD Scenarios

## Design Rationale

Rendering both the decoupled `100%` Task Completion indicator and the 6-stage `/dev-lifecycle` stepper + sub-step micro-tracker in Section II and the Kanban `"TIẾN ĐỘ EPICS"` sidebar gives the Human Architect complete visibility into every stage (`Spec -> HLD & Principal Review -> Tasks -> Gate 4 QA -> Cross-Model Review -> Finish`) and every mechanical sub-step (`Reviewing -> Lập bảng triage -> Fix findings -> Verifying`, `PyCore / Unit Test`, `UI / E2E Test`, etc.). Applicable skills: `d3nexus:test-driven-development`, `d3nexus:web-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/check-tasks/resources/dashboard/tasks_dashboard.html`: `computeEpicProgressState` (L2058-L2107), `renderLiveTelemetryBanner` (L2136-L2196), `renderExecutionEpics` (L2198-L2399), `renderKanbanDashboard` (L2401-L2726), `buildKanbanSig` (L2728-L2743), `buildTier2Sig` (L2766-L2805), `pollDashboard` (L3787-L3870)
  - `tests/test_ltsp_dashboard_ui.py`: new DOM & Chrome CDP test suite
  - `tests/test_rsdh_tasks_dashboard_ui.py`: `test_rsdh_hp_07_96_cap_and_tier2_live_sync` (L756-L898), `test_rsdh_hp_07_chrome_cdp_integration` (L903-L1007), `test_rsdh_st_05_progress_transitions` (L1304-L1382), `test_rsdh_ar_02_live_polling_preserves_focus_and_zero_console_errors` (L1383-L1519)
- **Downstream Callers**: `skills/check-tasks/resources/scripts/tasks_server.py`.
- **Cross-Platform Bridges**: `/api/tasks` JSON payload consumed by `tasks_dashboard.html`.
- **Target Test Coverage Threshold**: 100% of new stepper, sub-step, event log, and Kanban `"TIẾN ĐỘ EPICS"` rendering functions.

### BDD SCENARIOS

Covers: LTSP-HP-05, LTSP-EC-03, LTSP-ST-03, LTSP-AR-02, LTSP-FR-02

```gherkin
Scenario: [LTSP-HP-05] [Tier C - Integration] Tasks dashboard renders 6-stage stepper, sub-step micro-tracker, 100% task badge, rolling event logs, and Kanban TIẾN ĐỘ EPICS stage overview
Given a repository payload where 9 of 9 tasks are `"done"`, Cross-Model Review Round 1 (`codex / gpt-6.1-sol`) is in `"triage"` phase, and `heartbeat.events` has 5 timestamped entries
When `renderExecutionEpics` and `renderKanbanDashboard` render Section II and the Kanban board in `tasks_dashboard.html`
Then the rendered Section II HTML contains `"9 / 9 Hoàn thành"` and `"100%"` for Task Implementation
And `[data-telemetry="pipeline-stepper"]` renders all 6 lifecycle stages with `"Tasks"` marked completed (`100%`) and `"Cross-Review"` marked active
And `[data-telemetry="sub-steps"]` renders the 4 review micro-steps `"Reviewing"`, `"Lập bảng triage"`, `"Fix findings"`, and `"Verifying"` with `"Round 1/3"` and `"codex"`
And `[data-telemetry="event-logs"]` renders the latest timestamped heartbeat events
And the Kanban `"TIẾN ĐỘ EPICS"` sidebar card renders the weighted lifecycle progress percentage, `"9/9 Tasks (100%)"`, and `[data-telemetry="kanban-epic-stage"]` showing the current stage and micro-step overview

Scenario: [LTSP-EC-03] [Tier C - Integration] Dashboard degrades gracefully when legacy payloads omit pipeline_telemetry or events
Given a legacy `/api/tasks` repository payload without `pipeline_telemetry` or `heartbeat.events` where `done_tasks == 4` and `total_tasks == 4`
When `renderExecutionEpics` and `renderKanbanDashboard` execute in the DOM harness
Then zero JavaScript exceptions are thrown
And `computeEpicProgressState` synthesizes `taskPct == 100` for task completion and a valid `pct` for lifecycle progress

Scenario: [LTSP-ST-03] [Tier C - Integration] Quality Check sub-steps transition visually from Static Lint to Typecheck to PyCore/Unit Test to UI/E2E Test
Given `quality_active.json` with a running `python-qa` run whose `steps` array transitions from step 1 (`Static Lint`: `passed`), step 2 (`Typecheck`: `passed`), step 3 (`PyCore / Unit Test`: `running`), to step 4 (`UI / E2E Test`: `pending`)
When `renderExecutionEpics` renders the card
Then `[data-telemetry="quality"]` displays completed checkmarks for `"Static Lint"` and `"Typecheck"`, an active running badge for `"PyCore / Unit Test"`, and a pending indicator for `"UI / E2E Test"`

Scenario: [LTSP-AR-02] [Tier C - Integration] Section II tier2Sig detects sub-step, review_state, quality step, and event log changes without clobbering sibling Roadmap focus
Given the dashboard rendered in headless Chrome CDP with focus held on a Roadmap PIC `<select>` control
When `/api/tasks` updates only `heartbeat.review_state.phase` from `"triage"` to `"fixing"` and appends an entry to `heartbeat.events`
Then `pollDashboard()` updates Section II immediately to show `"Fix findings"` while `document.activeElement` remains on the focused Roadmap `<select>`

Scenario: [LTSP-FR-02] [Tier C - Integration] Failed or aborted quality step and Circuit Breaker review halt render explicit error badges in the stage stepper
Given a repository payload where `quality_active` has `status: "failed"` on capability `"integration"` (`"Integration Test"`) or `review_state` has `action: "CIRCUIT_BREAKER_HALT"`
When `renderExecutionEpics` renders the card
Then the corresponding stage and sub-step chip render a failure/halt alert state with the exact failed capability or circuit-breaker reason and zero console errors
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ltsp_dashboard_ui.py::test_ltsp_hp_05_stepper_substeps_logs_and_kanban_overview` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ltsp_dashboard_ui.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_tasks_dashboard_ui.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_ltsp_dashboard_ui.py tests/test_rsdh_tasks_dashboard_ui.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/ltsp_task_03.xml tests/test_ltsp_dashboard_ui.py tests/test_rsdh_tasks_dashboard_ui.py` | exit 0; results build/test-results/ltsp_task_03.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- All dynamic strings rendered into HTML in `tasks_dashboard.html` must pass through `escapeHtml(...)`.
- Preserve existing `[data-telemetry="heartbeat"]` and `[data-telemetry="quality"]` hooks while adding `[data-telemetry="pipeline-stepper"]`, `[data-telemetry="sub-steps"]`, `[data-telemetry="event-logs"]`, and `[data-telemetry="kanban-epic-stage"]`.
- `expandedEventLogsByEpic` stores expanded epic keys in memory so `pollDashboard()` never collapses an open event log drawer on the next 2s poll tick.

## Definition of Done

- Scenarios LTSP-HP-05, LTSP-EC-03, LTSP-ST-03, LTSP-AR-02, and LTSP-FR-02 pass. (V2, V6)
- Existing dashboard tests in `tests/test_rsdh_tasks_dashboard_ui.py` pass with zero regressions. (V3)
- Ruff check and mypy pass on dashboard test suites. (V4, V5)

## Dependencies & Blockers

Blocked by [Task 1](task_01_state_envelope_events_and_stage_producers.md).

Downstream dependents (blocked by Task 3): `task_04`.

## References & Rollback

- [Epic HLD](lifecycle_telemetry_and_stage_progress_ui.en.md)
- **Rollback**: Revert task commit to restore `tasks_dashboard.html` and `tests/test_rsdh_tasks_dashboard_ui.py`.
