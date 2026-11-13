---
id: "task_06_check_quota_modal_stack_controller"
status: "todo"
priority: "high"
assignee: null
epic: "runtime_sync_and_dashboard_hardening"
dueDate: null
created: "2026-11-13T09:24:00Z"
modified: "2026-11-13T09:24:00Z"
completedAt: null
labels: ["frontend", "check-quota", "modal", "ui"]
order: "a6"
review_tier: "full"
---

# Task 6: Check-Quota Single Modal Stack Controller and Embedded Cleanup

Epic: [runtime_sync_and_dashboard_hardening](../epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md)

## Requirement Analysis

Eliminate nested multi-layer overlapping dialogs when `check-quota` runs both standalone and embedded inside `tasks_dashboard.html`'s `#modal-quota` iframe:

1. **Single Modal Stack Controller (`skills/check-quota/resources/dashboard/quota_dashboard.html`)**:
   - Unify all four inner sub-modals (`#scheduleModal`, `#loginModal`, `#profileInfoModal`, `#appealDetailModal` at `L407-L765`, plus open/close helpers `openScheduleModal`..`closeLoginModal` at `L3570-L3885`) under a deterministic Single Modal Stack Controller (`closeAllInnerModals(exceptId)`, `openInnerModal(modalId, onOpen)`, `closeInnerModal(modalId)`, `getActiveInnerModal()`).
   - Opening any inner sub-modal closes any currently open sibling inner sub-modal first so at most `1` inner sub-modal can be active at any time.
2. **Backdrop, `Escape`, and `postMessage` Cascade Guards (`L4050-L4085`)**:
   - Attach consistent backdrop-click dismissal to **all four** inner sub-modals (`e.target === modalEl`) so clicking an inner sub-modal backdrop dismisses ONLY that active inner dialog and keeps `#dashboardCard` / parent `#modal-quota` intact.
   - Update the global `keydown` (`Escape`) handler so pressing `Escape` checks `getActiveInnerModal()` first: if an inner sub-modal is open, dismiss ONLY that inner sub-modal and `stopPropagation()`/`preventDefault()`; invoke `handleCardClose()` strictly when `0` inner sub-modals are open (and when `?embedded=1`, notify parent `#modal-quota` cleanly).
   - Listen for `{ action: 'reset_quota_submodals' }` via `window.addEventListener('message', ...)` so reopening or closing `#modal-quota` from `tasks_dashboard.html` resets all four inner sub-modals deterministically.
3. **Embedded Container Flattening (`#dashboardCard` `L176-L200`)**:
   - When `location.search` includes `?embedded=1` or `window.parent !== window` (iframe detection), apply an embedded mode class to `document.body` / `#dashboardCard` removing duplicate outer card borders, shadows, and excess padding while preserving full container framing in standalone mode.
   - **Strict Diff Hygiene**: Perform surgical edits ONLY to CSS, modal HTML/JS sections; NEVER overwrite or alter runtime `PROFILES_DATA` snapshot blocks in `quota_dashboard.html`.
4. Add `tests/test_rsdh_quota_modal_stack.py` executing real extracted `<script>` handlers under headless `node` (`v25.6.0`) covering `RSDH-HP-08`, `RSDH-EC-07`, `RSDH-ST-06`, and `RSDH-FR-05`.

## Files

Allowed files:
- `skills/check-quota/resources/dashboard/quota_dashboard.html`
- `tests/test_rsdh_quota_modal_stack.py` (new)

Read-only context:
- `.devtool/epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md` — HLD Module Contracts (§4.7)
- `.devtool/epic/runtime_sync_and_dashboard_hardening/bdd_scenarios.en.md` — Canonical BDD Scenarios

## Design Rationale

`quota_dashboard.html` previously managed `#profileInfoModal`, `#appealDetailModal`, `#scheduleModal`, and `#loginModal` independently inside `#modal-quota` without mutual exclusion, uniform backdrop handlers, or `?embedded=1` container flattening — causing stacked overlays when a user opens quota details from `tasks_dashboard.html`. Centralizing all four dialogs under one Single Modal Stack Controller resolves stacking, backdrop, `Escape`, and embedded close cascades systematically. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:web-quality-check`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/check-quota/resources/dashboard/quota_dashboard.html`: `#dashboardCard` container & styles (L176-L200), `#scheduleModal`/`#loginModal`/`#profileInfoModal`/`#appealDetailModal` markup (L407-L765), `openScheduleModal`..`closeLoginModal` functions (L3570-L3885), backdrop/`Escape`/embedded initialization (L4050-L4085)
  - `tests/test_rsdh_quota_modal_stack.py`: new Node DOM integration suite for `RSDH-HP-08`, `RSDH-EC-07`, `RSDH-ST-06`, `RSDH-FR-05`
- **Downstream Callers**: Standalone `check-quota` UI server and `tasks_dashboard.html` `#modal-quota` embedded iframe (`?embedded=1`).
- **Cross-Platform Bridges**: `postMessage` (`{ action: 'reset_quota_submodals' }` matching `e.data.action`) from `tasks_dashboard.html` `#modal-quota` close handler (end-to-end parent+iframe integration runs in Wave 4 Task 07).
- **Target Test Coverage Threshold**: 100% of Single Modal Stack Controller exclusivity across all 4 inner modals, backdrop dismissal, `Escape` cascade (`1 -> 0` modals), `?embedded=1` layout flattening, and zero `console.error` events.

### BDD SCENARIOS

Covers: RSDH-HP-08, RSDH-EC-07, RSDH-ST-06, RSDH-FR-05


```gherkin
Scenario: [RSDH-HP-08] [Tier C - Integration] Check-Quota Modal Stack Controller limits open inner sub-modals to one and resets on parent close

Given quota_dashboard.html embedded inside #modal-quota in tasks_dashboard.html
When the user opens #scheduleModal and then triggers #loginModal, and later the parent closes #modal-quota
Then opening #loginModal automatically closes #scheduleModal so at most one inner sub-modal has the open state simultaneously
And closing #modal-quota posts {action: "reset_quota_submodals"} causing quota_dashboard.html to close every inner sub-modal cleanly

Scenario: [RSDH-EC-07] [Tier C - Integration] Check-Quota inner sub-modal backdrop and Escape close only the active inner dialog

Given #modal-quota is open and inside quota_dashboard.html one of #profileInfoModal, #appealDetailModal, #scheduleModal, or #loginModal is open
When the user clicks the sub-modal backdrop or presses Escape inside the iframe
Then only the active inner sub-modal closes, preserving the rest of #dashboardCard and keeping #modal-quota open

Scenario: [RSDH-ST-06] [Tier C - Integration] Check-Quota embedded mode strips redundant outer card frame cleanly

Given quota_dashboard.html loaded with query parameter "?embedded=1" versus standalone URL
When the initialization script applies embedded styling classes to #dashboardCard
Then embedded mode removes redundant outer modal spacing/borders while standalone mode preserves full container layout

Scenario: [RSDH-FR-05] [Tier C - Integration] Pressing Escape with no open inner quota sub-modal closes cleanly via handleCardClose

Given quota_dashboard.html with all four inner sub-modals closed inside #modal-quota
When the user presses the Escape key
Then the key handler sees zero open inner sub-modals and invokes handleCardClose cleanly without runtime errors
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_quota_modal_stack.py::test_rsdh_hp_08_single_modal_stack_exclusivity` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_quota_modal_stack.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_quota_modal_stack.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_rsdh_quota_modal_stack.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_6.xml tests/test_rsdh_quota_modal_stack.py` | exit 0; results build/test-results/task_6.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Pre-existing dirty runtime snapshot lines in `quota_dashboard.html` (`PROFILES_DATA`) MUST be preserved intact during edits — apply surgical diffs ONLY to styles, modal HTML/JS stack controller, and `?embedded=1` handlers.
- The canonical cross-iframe reset payload is `{ action: 'reset_quota_submodals' }` (`postMessage`), matching `tasks_dashboard.html` `e.data.action` conventions; end-to-end parent+iframe integration runs in Wave 4 Task 07 so Task 06 stays independent of Wave 3 sibling Task 05.
- Because `playwright` is not installed (`playwright_pkg: False`), `tests/test_rsdh_quota_modal_stack.py` executes the real extracted modal controller script under headless `node` (`v25.6.0`) across all 4 modal IDs.

## Definition of Done

- Scenarios RSDH-HP-08, RSDH-EC-07, RSDH-ST-06, and RSDH-FR-05 pass under Node DOM execution with zero console errors. (V2, V6)
- Ruff lint and registered mypy checks pass cleanly with `PROFILES_DATA` uncorrupted. (V4, V5)

## Dependencies & Blockers

Blocked by [Task 3](../epic/runtime_sync_and_dashboard_hardening/task_03_wave_parallel_handoff_stage3_revise_and_pool_cleanup.md).

Downstream dependent (blocked by Task 6): `task_07`.

## References & Rollback

- [Epic HLD](../epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md), Module Contracts (§4.7).
- **Rollback**: Revert task commit; restores prior modal code in `quota_dashboard.html` and removes `tests/test_rsdh_quota_modal_stack.py`.
