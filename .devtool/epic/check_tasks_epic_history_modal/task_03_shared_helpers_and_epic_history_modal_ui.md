---
id: "task_03_shared_helpers_and_epic_history_modal_ui"
status: "done"
priority: "high"
assignee: null
epic: "check_tasks_epic_history_modal"
dueDate: null
created: "2026-11-15T01:00:00Z"
modified: "2026-11-14T19:29:42Z"
completedAt: "2026-11-14T19:29:42Z"
labels: ["dashboard-ui", "vanilla-js", "modal", "shared-helpers"]
order: "a3"
review_tier: "full"
---

# Task 3: Shared JS Renderers and Interactive `modal-epic-history` Dashboard UI

Epic: [check_tasks_epic_history_modal](check_tasks_epic_history_modal.en.md)

## Requirement Analysis

Extract shared Vanilla JS rendering helpers inside `skills/check-tasks/resources/dashboard/tasks_dashboard.html` and implement the interactive `#modal-epic-history` Pop-up Modal:

1. **Extract Shared Pure Helpers Without Section II Regression**:
   - Extract `buildPipelineStepperHtml(pt, hb, options)` from `renderPipelineStepperAndLogs()` (`L2511-L2624`) so both live Section II cards and the `#modal-epic-history` compact header reuse identical 6-stage stepper + sub-step chip rendering while preserving all `[data-telemetry="..."]` attributes tested by `tests/test_ltsp_dashboard_ui.py` and `tests/test_rsdh_tasks_dashboard_ui.py`.
   - Extract `buildReviewHeaderHtml(data, options)` and `buildReviewFindingsTableHtml(findings)` from `openReviewModal()` (`L3757-L3966`) (6-column Triage Table, severity/decision badges, SHA/provider/model/thinking bar, and review token highlighting) so both `#modal-cross-review` and `#modal-epic-history` review tabs share one rendering implementation.
2. **Clickable Section III Roadmap Rows & PIC Isolation (`renderRoadmapTableRows` `L3396-L3455`)**:
   - Make every `<tr class="roadmap-epic-row">` across all statuses (`Done`, `In Progress`, `Packaged`, `Backlog`, `Abandon`) clickable via `data-epic-slug` / `openEpicHistoryModal(repoName, epicSlug)`, showing hover feedback and keeping `renderRepoDetailView()` (`L3457-L3545`) focus/scroll guards intact.
   - Ensure clicking or changing the inline `renderPicSelect()` `<select>` control in column 5 calls `event.stopPropagation()` (and guards `e.target.closest('select')`) so PIC reassignment never triggers `openEpicHistoryModal()` (`CEHM-EC-03`).
3. **Interactive `#modal-epic-history` Pop-up Modal, 4 Tabs, Race Guard & Live Refresh**:
   - Add `#modal-epic-history` HTML container modeled cleanly after `#modal-cross-review` (`L1026-L1060`) with `openLiveModal`/`closeLiveModal`/`initModalClickOutside` (`L1124-L1185`) plus `Escape` key closing, body scroll lock restoration (`document.body.style.overflow = ''`), and Section II left completely untouched underneath.
   - Render compact epic header (repo color border, status badge, PIC, last updated, stream completeness badge, and compact 6-stage summary from `buildPipelineStepperHtml`), loading/error states with inline `Retry` button, and 4 direct tabs (`Timeline & Step Logs` with `All / Gates / Steps / Activity / Evidence` category filter pills, `Tasks & Evidence` with expandable verification row details, `Principal Review`, `Cross-Model Review` with in-modal Round switcher without stacking modals).
   - Guard rapid clicks (`Epic A` then `Epic B`) using monotonic `epicHistoryRequestToken` + `AbortController` so delayed earlier responses never overwrite the active modal DOM (`CEHM-AR-02`).
   - Inside `pollDashboard()` (`L4260-L4307`), when `#modal-epic-history` is open and inspecting an `in_progress` epic, trigger `refreshEpicHistoryModal()` silently while preserving the selected sub-tab, timeline filter, expanded task rows, and selected review rounds; once closed, stop live modal refreshes (`CEHM-ST-02`, `CEHM-ST-03`).
4. **UI Unit & DOM Harness Verification (`tests/test_cehm_dashboard_modal_ui.py`)**:
   - Verify scenarios `CEHM-HP-04`, `CEHM-EC-03`, `CEHM-ST-02`, `CEHM-ST-03`, and `CEHM-AR-02` inside the Node VM DOM harness (`_NODE_DOM_HARNESS_PREAMBLE`).

## Files

Allowed files:
- `skills/check-tasks/resources/dashboard/tasks_dashboard.html`
- `tests/test_cehm_dashboard_modal_ui.py` (new)

Read-only context:
- `.devtool/epic/check_tasks_epic_history_modal/check_tasks_epic_history_modal.en.md` — HLD & Shared Helpers Contract
- `.devtool/epic/check_tasks_epic_history_modal/bdd_scenarios.en.md` — Canonical BDD Scenarios
- `tests/test_rsdh_tasks_dashboard_ui.py` — Shared Node DOM harness pattern

## Design Rationale

Extracting `buildPipelineStepperHtml`, `buildReviewHeaderHtml`, and `buildReviewFindingsTableHtml` eliminates duplicated template logic between Section II, `#modal-cross-review`, and `#modal-epic-history`, while monotonic request tokens and `AbortController` prevent race conditions on rapid row switching. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:web-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/check-tasks/resources/dashboard/tasks_dashboard.html`: `openLiveModal` (L1124-L1185), `closeLiveModal` (L1124-L1185), `initModalClickOutside` (L1124-L1185), `renderPipelineStepperAndLogs` (L2511-L2624), `renderRoadmapTableRows` (L3396-L3455), `renderRepoDetailView` (L3457-L3545), `renderPicSelect` (L3451), `openReviewModal` (L3757-L3966), `switchReviewRound` (L3968-L3972), `pollDashboard` (L4260-L4307), `escapeHtml` (L3911), new `buildPipelineStepperHtml`, new `buildReviewHeaderHtml`, new `buildReviewFindingsTableHtml`, new `openEpicHistoryModal`, new `switchEpicHistoryTab`, new `refreshEpicHistoryModal`
  - `tests/test_cehm_dashboard_modal_ui.py`: new UI DOM harness test suite
- **Downstream Callers**: `tests/test_ltsp_dashboard_ui.py`, `tests/test_rsdh_tasks_dashboard_ui.py`, `tests/test_cehm_e2e_cdp.py`.
- **Cross-Platform Bridges**: Fetches `GET /api/epic/history` served by `tasks_server.py`.
- **Target Test Coverage Threshold**: 100% of Roadmap click, PIC click isolation, tab/round switching, token race protection, poll preservation, and ESC/backdrop dismissal covered.

### BDD SCENARIOS

Covers: CEHM-HP-04, CEHM-EC-03, CEHM-ST-02, CEHM-ST-03, CEHM-AR-02

```gherkin
Scenario: [CEHM-HP-04] [Tier C - Integration] Clicking any Roadmap epic row opens modal-epic-history keeping Section II untouched and switches tabs cleanly
Given `tasks_dashboard.html` rendered with an active running epic in Section II and Roadmap rows in Section III for `"done_epic"`, `"in_prog_epic"`, and `"backlog_epic"`
When the user clicks the `.roadmap-epic-row` for `"done_epic"`
Then `#modal-epic-history` opens with `style.display === "flex"` and displays the 6-stage pipeline stepper while Section II underneath continues displaying the active epic unchanged
And clicking the modal tabs switches directly between `Timeline & Step Logs`, `Tasks & Evidence`, `Principal Review`, and `Cross-Model Review` and switches Round 1 to Round 2 inside Review without opening a second stacked modal

Scenario: [CEHM-EC-03] [Tier C - Integration] Changing inline PIC dropdown inside Roadmap row updates PIC without opening modal-epic-history
Given `tasks_dashboard.html` rendered with a clickable `.roadmap-epic-row` containing a `renderPicSelect` `<select>` control in column 5
When a click event and change event fire on that `<select>` element to assign `@phungthuy8901`
Then event propagation does not trigger `openEpicHistoryModal` and `#modal-epic-history` remains hidden

Scenario: [CEHM-ST-02] [Tier C - Integration] Open modal inspecting an In Progress epic prefers worktree tasks and preserves active tab across 5s poll refreshes
Given an active `"in_prog_epic"` whose `.worktrees/in_prog_epic/.devtool/features/task_01_live.md` is `"in-progress"` while root `.devtool/epic/in_prog_epic/task_01_live.md` says `"todo"`
When the user opens `#modal-epic-history` for `"in_prog_epic"`, switches to `"Cross-Model Review"` tab, and `pollDashboard()` executes a live tick after server data updates
Then `tasks[0]["status"]` reflects `"in-progress"` from the worktree source
And the silent refresh updates telemetry while keeping `"Cross-Model Review"` selected as the active tab inside `#modal-epic-history`

Scenario: [CEHM-ST-03] [Tier C - Integration] Closing modal-epic-history via close button, backdrop, or Escape restores scroll lock and detaches live refresh
Given `#modal-epic-history` is currently open (`style.display === "flex"` and `document.body.style.overflow === "hidden"`)
When the user closes it via the `✕` button, or clicks `.modal-backdrop`, or dispatches `KeyboardEvent("keydown", { key: "Escape" })`
Then `#modal-epic-history` hides (`style.display === "none"`), `document.body.style.overflow` resets to `""`, and subsequent `pollDashboard()` ticks do not re-fetch `/api/epic/history`

Scenario: [CEHM-AR-02] [Tier C - Integration] Fast sequential clicks on Epic A then Epic B discard delayed Epic A HTTP responses via request token
Given mock `fetch()` where `/api/epic/history?repo=R&epic=epic_a` resolves after 120ms and `/api/epic/history?repo=R&epic=epic_b` resolves after 10ms
When the user clicks row `"epic_a"` and 5ms later clicks row `"epic_b"`
Then `#modal-epic-history` renders `"epic_b"` metadata and tasks
And when the delayed `"epic_a"` promise resolves later, `"epic_a"` content does not overwrite `"epic_b"` inside the modal DOM
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cehm_dashboard_modal_ui.py::test_cehm_hp_04_roadmap_click_opens_modal_and_tabs` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cehm_dashboard_modal_ui.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ltsp_dashboard_ui.py tests/test_rsdh_tasks_dashboard_ui.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_cehm_dashboard_modal_ui.py tests/test_ltsp_dashboard_ui.py tests/test_rsdh_tasks_dashboard_ui.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && mypy tests/test_cehm_dashboard_modal_ui.py tests/test_ltsp_dashboard_ui.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/cehm_task_03.xml tests/test_cehm_dashboard_modal_ui.py tests/test_ltsp_dashboard_ui.py tests/test_rsdh_tasks_dashboard_ui.py` | exit 0; results build/test-results/cehm_task_03.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- All dynamic strings rendered inside `#modal-epic-history`, shared stepper builders, and review helpers pass through `escapeHtml(...)`.
- Inline `renderPicSelect()` `<select>` clicks stop propagation (`event.stopPropagation()`) and `.roadmap-epic-row` click handler also returns early if `event.target.closest('select, button, a, input')` so changing PIC never opens `#modal-epic-history`.
- `epicHistoryState` stores `{ isOpen, repoName, epicSlug, status, activeTab, timelineFilter, roundPrincipal, roundCross, expandedTasks, requestToken, abortController }` so 5-second `pollDashboard()` refreshes preserve UI state only while `isOpen && status === 'in_progress'`.
- Preserves existing `[data-telemetry="pipeline-stepper"]`, `[data-telemetry="sub-steps"]`, `[data-telemetry="event-logs"]`, and `#modal-cross-review` element IDs (`cross-review-title`, `review-sha`, `review-provider`, `review-model`, `review-verdict`, `review-raw-evidence`).

## Definition of Done

- Scenarios CEHM-HP-04, CEHM-EC-03, CEHM-ST-02, CEHM-ST-03, and CEHM-AR-02 pass inside the Node VM DOM harness and verify valid JS compilation. (V2, V6)
- Existing dashboard suites (`test_ltsp_dashboard_ui.py`, `test_rsdh_tasks_dashboard_ui.py`) pass with zero regressions. (V3, V6)
- Ruff check and mypy pass cleanly on `tests/test_cehm_dashboard_modal_ui.py`. (V4, V5)

## Dependencies & Blockers

Blocked by [Task 2](task_02_epic_history_aggregator_and_scoped_api.md).

Downstream dependents (blocked by Task 3): `task_04`.

## References & Rollback

- [Epic HLD](check_tasks_epic_history_modal.en.md)
- **Rollback**: Revert task commit to restore `skills/check-tasks/resources/dashboard/tasks_dashboard.html`.
