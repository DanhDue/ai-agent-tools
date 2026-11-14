---
id: "task_04_integration_and_cdp_acceptance_verification"
status: "todo"
priority: "high"
assignee: null
epic: "lifecycle_telemetry_and_stage_progress_ui"
dueDate: null
created: "2026-11-14T09:06:00Z"
modified: "2026-11-14T09:06:00Z"
completedAt: null
labels: ["integration", "cdp", "e2e", "verify"]
order: "a4"
review_tier: "full"
---

# Task 4: End-to-End Integration, Chrome CDP Verification, and Regression Alignment

Epic: [lifecycle_telemetry_and_stage_progress_ui](lifecycle_telemetry_and_stage_progress_ui.en.md)

## Requirement Analysis

Build the end-to-end integration and headless Chrome CDP acceptance test suite `tests/test_lifecycle_telemetry_and_stage_progress.py`, align any affected assertions in `tests/test_rsdh_harvester_and_pic.py`, and register the new test suites in `scripts/verify.sh`:

1. **End-to-End Integration & Chrome CDP Suite (`tests/test_lifecycle_telemetry_and_stage_progress.py`)**:
   - **`LTSP-HP-06` (`test_ltsp_hp_06_chrome_cdp_live_stage_and_microstep_transitions`)**:
     - Launch `TasksServer` on an ephemeral port and connect via headless Chrome CDP (with JSDOM / `TasksServer` HTTP harness fallback only if Chrome binary is absent, matching `test_rsdh_tasks_dashboard_ui.py`).
     - Transition the server state sequentially across:
       1. Wave 2 Task Implementation (`8/9 tasks`, active worker slots)
       2. All Tasks Done (`9/9 · 100%`) running Gate 4 Quality Check (`PyCore / Unit Test 3/5`)
       3. Cross-Model Review Round 1 (`codex reviewing -> Lập bảng triage -> Fix findings -> Verifying`)
     - Verify `pollDashboard()` updates Section II and the Kanban `"TIẾN ĐỘ EPICS"` overview in-place without reloading, displays `"9 / 9 Hoàn thành"` and `"100%"`, shows `"PyCore / Unit Test"` during Quality Check and `"Round 1/3"`, `"Lập bảng triage"`, and `"Fix findings"` during Cross-Model Review, and records `cdp.consoleErrors == []` and `cdp.runtimeExceptions == []`.
   - **`LTSP-EC-04` (`test_ltsp_ec_04_expandable_event_log_preserves_state_across_polls`)**:
     - Render an epic card with 8 heartbeat events, click the toggle button to expand all event logs, trigger `pollDashboard()` with a 9th heartbeat event, and verify the drawer remains expanded and renders all 9 events.
   - **`LTSP-ST-04` (`test_ltsp_st_04_commit_based_fix_and_verifying_inference`)**:
     - Create an epic worktree where `review_results.md` Round 1 recorded `SHA: <sha1>` with `Verdict: CHANGES REQUIRED` and 1 Important finding; create a new commit `<sha2>` with subject `"[REV_EPIC] Fix validation edge case"` and record `fixed in <sha2>`, and verify `build_epic_pipeline_telemetry` infers `"fixing"` / `"verifying"` micro-steps before Round 2 starts.
   - **`LTSP-AR-03` (`test_ltsp_ar_03_multi_epic_pipeline_telemetry_isolation`)**:
     - Create a repository with primary `active_epic` `"epic_alpha"` in Stage 3 Cross-Model Review (`4/4 tasks · 100%`) and secondary `in_progress` `"epic_beta"` in Stage 2 Principal Review (`0/3 tasks · 0%`), run `scan_repo` and `renderExecutionEpics`, and verify zero cross-epic state bleed.
   - **`LTSP-FR-03` (`test_ltsp_fr_03_corrupted_review_and_heartbeat_recovery`)**:
     - Write truncated JSON in `.heartbeat.json` and malformed markdown table rows in `review_results.md`, run `scan_repo`, and verify it returns a valid 6-stage `pipeline_telemetry` structure without raising an exception.
2. **Regression Alignment (`tests/test_rsdh_harvester_and_pic.py` `L548-L757`) & `scripts/verify.sh` (`L362-L435`)**:
   - Ensure `tests/test_rsdh_harvester_and_pic.py` passes alongside the new `task_completion_pct` (`100.0`) and `pipeline_telemetry` fields.
   - Register `tests/test_ltsp_state_and_producers.py`, `tests/test_ltsp_harvester_pipeline.py`, `tests/test_ltsp_dashboard_ui.py`, and `tests/test_lifecycle_telemetry_and_stage_progress.py` in `SUITES` in `scripts/verify.sh` (`L362-L435`).

## Files

Allowed files:
- `tests/test_lifecycle_telemetry_and_stage_progress.py` (new)
- `tests/test_rsdh_harvester_and_pic.py`
- `scripts/verify.sh`

Read-only context:
- `.devtool/epic/lifecycle_telemetry_and_stage_progress_ui/lifecycle_telemetry_and_stage_progress_ui.en.md` — HLD & Integration Test Plan
- `.devtool/epic/lifecycle_telemetry_and_stage_progress_ui/bdd_scenarios.en.md` — Canonical BDD Scenarios

## Design Rationale

Verifying the full producer -> harvester -> `/api/tasks` -> headless Chrome CDP pipeline end-to-end guarantees that real-time polling, DOM focus preservation, expandable event log state, and multi-epic isolation work seamlessly in production. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `tests/test_lifecycle_telemetry_and_stage_progress.py`: new end-to-end integration & CDP suite
  - `tests/test_rsdh_harvester_and_pic.py`: `test_rsdh_ar_03_multi_epic_isolation_quality_runs_and_stale_expiry` (L548-L684), `test_backend_progress_ceiling_tiers` (L718-L757)
  - `scripts/verify.sh`: `SUITES` (L362-L435)
- **Downstream Callers**: `scripts/verify.sh` and Gate 4 `audit_epic.py` / `check_bdd_traceability.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of all 18 `LTSP-*` BDD scenarios traced and passing.

### BDD SCENARIOS

Covers: LTSP-HP-06, LTSP-EC-04, LTSP-ST-04, LTSP-AR-03, LTSP-FR-03

```gherkin
Scenario: [LTSP-HP-06] [Tier C - Integration] End-to-end headless Chrome CDP verifies live stage and micro-step transitions from Tasks to Quality Check to Cross-Model Review
Given a live `TasksServer` serving `tasks_dashboard.html` in headless Chrome CDP
When the server state transitions from Wave 2 Task Implementation (`8/9 tasks`) to All Tasks Done (`9/9 · 100%`) running Quality Check (`PyCore / Unit Test 3/5`) to Cross-Model Review Round 1 (`codex reviewing -> Lập bảng triage -> Fix findings -> Verifying`)
Then `pollDashboard()` updates Section II in-place without reloading the page
And the Task Implementation indicator displays `"9 / 9 Hoàn thành"` and `"100%"`
And the active sub-step strip displays `"PyCore / Unit Test"` during Quality Check and `"Round 1/3"` with `"Lập bảng triage"` and `"Fix findings"` during Cross-Model Review
And `cdp.consoleErrors` and `cdp.runtimeExceptions` are both `[]`

Scenario: [LTSP-EC-04] [Tier C - Integration] Expandable event log drawer preserves expanded state across live pollDashboard ticks
Given a repository card in `tasks_dashboard.html` with 8 heartbeat events where the user clicks the toggle button to expand all event logs
When `pollDashboard()` runs on the next polling tick with a new 9th heartbeat event
Then the event log container remains expanded and displays all 9 events without collapsing back to the 4-line preview

Scenario: [LTSP-ST-04] [Tier C - Integration] Commit-based fix and verification detection infers fixing and verifying sub-steps when git HEAD advances past review round SHA
Given an epic worktree where `review_results.md` Round 1 recorded `SHA: <sha1>` with `Verdict: CHANGES REQUIRED` and 1 Important finding
When a new commit `<sha2>` with subject `"[REV_EPIC] Fix validation edge case"` is committed in the worktree and later `fixed in <sha2>` is recorded in `review_results.md`
Then `build_epic_pipeline_telemetry` infers the Cross-Model Review Round 1 micro-step as `"fixing"` / `"verifying"` even before Round 2 starts

Scenario: [LTSP-AR-03] [Tier C - Integration] Multi-epic workspace isolates pipeline_telemetry per epic across active and secondary in-progress epics
Given a repository with primary `active_epic` `"epic_alpha"` in Stage 3 Cross-Model Review (`4/4 tasks · 100%`) and secondary `in_progress` `"epic_beta"` in Stage 2 Principal Review (`0/3 tasks · 0%`)
When `scan_repo` and `renderExecutionEpics` render both epic cards
Then `"epic_alpha"` displays `100%` task completion and Stage 5 Cross-Model Review active, while `"epic_beta"` displays `0%` task completion and Stage 2 HLD & Principal Review active without cross-epic state bleed

Scenario: [LTSP-FR-03] [Tier C - Integration] Corrupted or truncated review_results.md / heartbeat.json files recover cleanly during pipeline harvesting
Given an epic worktree with truncated JSON in `.heartbeat.json` and malformed markdown table rows in `review_results.md`
When `scan_repo` harvests the repository
Then `scan_repo` completes without raising an exception and returns a valid `pipeline_telemetry` structure with 6 stages
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_lifecycle_telemetry_and_stage_progress.py::test_ltsp_hp_06_chrome_cdp_live_stage_and_microstep_transitions` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_lifecycle_telemetry_and_stage_progress.py tests/test_rsdh_harvester_and_pic.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_lifecycle_telemetry_and_stage_progress.py tests/test_rsdh_harvester_and_pic.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/lifecycle-telemetry-and-stage-progress-ui.xml tests/test_ltsp_state_and_producers.py tests/test_ltsp_harvester_pipeline.py tests/test_ltsp_dashboard_ui.py tests/test_lifecycle_telemetry_and_stage_progress.py tests/test_check_tasks_fsm.py tests/test_rsdh_state_envelope.py tests/test_rsdh_harvester_and_pic.py tests/test_rsdh_tasks_dashboard_ui.py` | exit 0; results build/test-results/lifecycle-telemetry-and-stage-progress-ui.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- All tests in `tests/test_lifecycle_telemetry_and_stage_progress.py` must run inside temporary directories and ephemeral localhost ports without touching `~/.gemini` or `/tmp/agy_tasks_server.pid`.
- `build/test-results/lifecycle-telemetry-and-stage-progress-ui.xml` is generated via `pytest --junitxml=...` to satisfy the HLD `Integration results:` contract.

## Definition of Done

- Scenarios LTSP-HP-06, LTSP-EC-04, LTSP-ST-04, LTSP-AR-03, and LTSP-FR-03 pass. (V2, V5)
- `tests/test_rsdh_harvester_and_pic.py` passes with zero regressions. (V2, V5)
- `scripts/verify.sh` includes the new `LTSP` test suites. (V2)
- Ruff check and mypy pass on `tests/test_lifecycle_telemetry_and_stage_progress.py`. (V3, V4)

## Dependencies & Blockers

Blocked by [Task 1](task_01_state_envelope_events_and_stage_producers.md), [Task 2](task_02_check_tasks_pipeline_harvester_and_progress_weights.md), [Task 3](task_03_tasks_dashboard_stepper_substeps_and_logs_ui.md).

Downstream dependents (blocked by Task 4): None.

## References & Rollback

- [Epic HLD](lifecycle_telemetry_and_stage_progress_ui.en.md)
- **Rollback**: Revert task commit to restore `tests/test_rsdh_harvester_and_pic.py` and `scripts/verify.sh`.
