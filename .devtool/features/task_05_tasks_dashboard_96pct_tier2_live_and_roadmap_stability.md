---
id: "task_05_tasks_dashboard_96pct_tier2_live_and_roadmap_stability"
status: "todo"
priority: "high"
assignee: null
epic: "runtime_sync_and_dashboard_hardening"
dueDate: null
created: "2026-11-13T09:24:00Z"
modified: "2026-11-13T09:24:00Z"
completedAt: null
labels: ["frontend", "dashboard", "live-sync", "check-tasks"]
order: "a5"
review_tier: "full"
---

# Task 5: Tasks Dashboard 96% Ceiling, Section II Live Telemetry, and Roadmap Stability

Epic: [runtime_sync_and_dashboard_hardening](../epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md)

## Requirement Analysis

Fix the pre-finish `99%` ceiling, live Section II Tier 2 telemetry updates, and Roadmap row-jump / PIC-dropdown glitches in `skills/check-tasks/resources/dashboard/tasks_dashboard.html`:

1. **`96%` Pre-Finish Ceiling & Progress Display (`renderExecutionEpics`, `renderKanbanDashboard`)**:
   - Update progress formatting in `renderExecutionEpics` (`L1970-L2151`) and `renderKanbanDashboard` (`L2153-L2295`, specifically `L2244-L2279`) from `99%` / `98%` to a strict `96%` pre-finish ceiling (`⚡ 96% Review` when all tasks are done before Gate 4 convergence; active in-progress tasks capped at `<= 95%`; `100%` rendered strictly when the epic reaches converged `Waiting Finish` / Sign-off or `Done`).
2. **Section II Live Tier 2 Synchronization (`tier2Sig`, `pollDashboard`)**:
   - Expand `tier2Sig` (`L2724-L2740`) beyond stage/epic slug alone to serialize `account_id`, active `prompt`, `is_human_action_required`, `task_progress`, `pending_decision`, `heartbeat`, and `quality_active`, so `fetchTasks` / `renderRepoDetailView` re-renders Section II (`renderExecutionEpics` / `renderKanbanDashboard`) immediately on every genuine runtime transition without forcing manual refresh.
  - Surface active heartbeat wave/event and running `quality_active` telemetry cleanly inside Section II without console errors or null-dereference regressions when optional fields are absent.
3. **Roadmap Row Stability, Focus Guard, and Modal Refresh (`sortEpicsForRoadmap`, `renderRoadmapTableRows`, `updateEpicPic`, `modal-quota`)**:
   - Stabilize `sortEpicsForRoadmap` (`L1721-L1760`) with deterministic tie-breaking on epic slug (`a.slug.localeCompare(b.slug)`) when timestamps or priorities match.
   - Stamp explicit `data-row-key` attributes on rows in `renderRoadmapTableRows` (`L2575-L2635`), align `roadmapSig` (`L2697-L2715`) with PIC/progress/row identity, and defer `roadmapTbody.innerHTML` replacement during 5s polling inside `renderRepoDetailView` whenever a `.select-pic-roadmap` inside `#roadmap-tbody` holds `document.activeElement` (applying the queued render once the select blurs).
   - Fix `updateEpicPic` (`L1614-L1652`, line `L1642`) to check `#modal-epics` visibility using `style.display === 'flex'` instead of stale `.classList.contains('active')`, and synchronize `#modal-quota` open/close (`closeLiveModal` `L1119-L1158`, `openQuotaModal` `L1470-L1515`) by posting `{ type: 'reset-quota-modals' }` to the quota iframe and handling child close messages cleanly.
4. Add `tests/test_rsdh_tasks_dashboard_ui.py` executing real extracted `<script>` logic in headless `node` (`v25.6.0`) against DOM fixtures covering `RSDH-HP-07`, `RSDH-EC-06`, `RSDH-ST-05`, and `RSDH-AR-02`.

## Files

Allowed files:
- `skills/check-tasks/resources/dashboard/tasks_dashboard.html`
- `tests/test_rsdh_tasks_dashboard_ui.py` (new)

Read-only context:
- `.devtool/epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md` — HLD Module Contracts (§4.6)
- `.devtool/epic/runtime_sync_and_dashboard_hardening/bdd_scenarios.en.md` — Canonical BDD Scenarios
- `skills/check-tasks/resources/scripts/check_tasks.py` — Backend `96%` cap & `RepoMetadata` JSON schema (Task 4)

## Design Rationale

DOM replacement during active `<select>` interaction causes native dropdown options to jump across rows when sorting shifts slightly, and coarse `tier2Sig` signatures hide mid-stage task, heartbeat, and quality updates until manual reload. Deferring Roadmap re-renders strictly during `.select-pic-roadmap` focus and hashing full Tier 2 state fixes both bugs cleanly without extra frameworks. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:web-quality-check`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/check-tasks/resources/dashboard/tasks_dashboard.html`: `closeLiveModal` (L1119-L1158), `openQuotaModal` (L1470-L1515), `updateEpicPic` (L1614-L1652), `sortEpicsForRoadmap` (L1721-L1760), `renderExecutionEpics` (L1970-L2151), `renderKanbanDashboard` (L2153-L2295), `renderRoadmapTableRows` (L2575-L2635), `renderRepoDetailView` (L2631-L2740), `fetchTasks` (L3459-L3535)
  - `tests/test_rsdh_tasks_dashboard_ui.py`: new Node DOM + HTTP integration test suite for `RSDH-HP-07`, `RSDH-EC-06`, `RSDH-ST-05`, `RSDH-AR-02`
- **Downstream Callers**: `tasks_server.py` dashboard serving (`/`), embedded `quota_dashboard.html` iframe via `postMessage`, `tests/test_check_tasks_e2e.py`.
- **Cross-Platform Bridges**: `postMessage` (`reset-quota-modals`) with `quota_dashboard.html` (Task 6).
- **Target Test Coverage Threshold**: 100% of `96%` cap thresholds, `tier2Sig` diffing, Roadmap `data-row-key` focus guard, and `modal-epics` refresh path with zero console errors.

### BDD SCENARIOS

Covers: RSDH-HP-07, RSDH-EC-06, RSDH-ST-05, RSDH-AR-02


```gherkin
Scenario: [RSDH-HP-07] [Tier C - Integration] Tasks dashboard enforces 96% pre-finish ceiling and refreshes Section II live on state changes

Given tasks_dashboard.html loaded with a repo payload containing an in_progress epic with 5/5 tasks done and Gate 4 not yet converged
When pollDashboard receives an updated payload updating active account_id, task_progress, prompt, heartbeat active wave, or quality_active running state
Then both Section I sidebar and Section II execution card render 96% ("96% Review") rather than 99%
And tier2Sig detects the change and re-renders Section II with the live wave/quality progress banner without reloading the page

Scenario: [RSDH-EC-06] [Tier C - Integration] Roadmap select preserves focus and exact row mapping during 5s polling and open modals

Given tasks_dashboard.html rendering a Roadmap table where two epics share recent update timestamps and the user focuses a .select-pic-roadmap dropdown with data-row-key
When a 5s poll payload arrives while .select-pic-roadmap holds document.activeElement, and updateEpicPic completes while #modal-epics has style.display === "flex"
Then pollDashboard defers replacing roadmapTbody.innerHTML until focus blurs so the dropdown choice does not jump rows
And updateEpicPic detects #modal-epics visibility via style.display === "flex" and refreshes modal rows accurately

Scenario: [RSDH-ST-05] [Tier C - Integration] Progress calculation enforces 95% in-progress cap, 96% pre-finish cap, and 100% finished state

Given task counts transitioning from 3/4 done, 4/4 done before Gate 4 convergence, 4/4 done with Gate 4 Review Converged (Waiting Finish), and Gate 5 Done
When check_tasks backend and tasks_dashboard.html compute progress display values
Then 3/4 done yields <= 95%, 4/4 done pre-convergence yields exactly 96%, and converged Waiting Finish / Done yields 100%

Scenario: [RSDH-AR-02] [Tier C - Integration] Live polling applies Tier 2 updates immediately without clobbering focused controls or emitting console errors

Given tasks_dashboard.html receiving periodic pollDashboard snapshots containing changed heartbeat waves, quality_active status, and PIC selections
When poll updates run both during active .select-pic-roadmap focus and after blur
Then Section II updates immediately once focus settles, focused selects never lose user selection, and zero console errors are raised
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_tasks_dashboard_ui.py::test_rsdh_hp_07_96_cap_and_tier2_live_sync` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_tasks_dashboard_ui.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_check_tasks_e2e.py tests/test_check_tasks_server.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_rsdh_tasks_dashboard_ui.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_5.xml tests/test_rsdh_tasks_dashboard_ui.py tests/test_check_tasks_e2e.py` | exit 0; results build/test-results/task_5.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Pre-finish ceiling is strictly `96%` (`⚡ 96% Review`); active uncompleted task progress caps at `95%`; `100%` displays strictly on converged `Waiting Finish` / Sign-off or `Done`.
- `playwright` is not installed (`playwright_pkg: False`), so `tests/test_rsdh_tasks_dashboard_ui.py` extracts real embedded `<script>` code from `tasks_dashboard.html` and executes it under headless `node` (`v25.6.0`) with genuine DOM mocks and `console.error` fail-fast assertions.
- Pending Roadmap polling renders queued while `.select-pic-roadmap` has focus must flush automatically on `blur`/`change` without dropping the user's selected value.

## Definition of Done

- Scenarios RSDH-HP-07, RSDH-EC-06, RSDH-ST-05, and RSDH-AR-02 pass under Node DOM + pytest execution with zero console errors. (V2, V6)
- Existing `test_check_tasks_e2e.py` and `test_check_tasks_server.py` suites pass cleanly. (V3, V6)
- Ruff lint and registered mypy checks pass cleanly. (V4, V5)

## Dependencies & Blockers

Blocked by [Task 1](../epic/runtime_sync_and_dashboard_hardening/task_01_runtime_state_envelope_and_two_tier_sync.md) and [Task 3](../epic/runtime_sync_and_dashboard_hardening/task_03_wave_parallel_handoff_stage3_revise_and_pool_cleanup.md).

Downstream dependent (blocked by Task 5): `task_07`.

## References & Rollback

- [Epic HLD](../epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md), Module Contracts (§4.6).
- **Rollback**: Revert task commit; restores prior `tasks_dashboard.html` and removes `tests/test_rsdh_tasks_dashboard_ui.py`.
