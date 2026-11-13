---
id: "task_07_integration_and_regression_verification"
status: "todo"
priority: "high"
assignee: null
epic: "runtime_sync_and_dashboard_hardening"
dueDate: null
created: "2026-11-13T09:24:00Z"
modified: "2026-11-13T09:24:00Z"
completedAt: null
labels: ["integration", "regression", "verify-sh", "acceptance"]
order: "a7"
review_tier: "full"
---

# Task 7: End-to-End Integration Suite and Verify Registration

Epic: [runtime_sync_and_dashboard_hardening](../epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md)

## Requirement Analysis

Lock in cross-layer end-to-end verification and continuous CI regression guards across all deliverables of `runtime_sync_and_dashboard_hardening`:

1. **Cross-Layer End-to-End Integration Suite (`tests/test_runtime_sync_and_dashboard_hardening.py`)**:
   - **`RSDH-HP-09`**: Orchestrate a real multi-worktree temporary git repository end-to-end:
     - Write dual-root `_state_envelope` heartbeat + quality telemetry and run `resume_context.py --detect-profile` / `--pending-decision` / `--gate` / `--clear-decision` / `sync_window_title()`.
     - Run `estimate_heartbeat.py` + `verify_polyglot_registry.py` against real test subprocess capabilities and confirm `quality_active.json` transitions (`running` -> `passed`).
     - Test Stage 3 `package_epic.py --revise` (`handoff.md` creator PIC stamping + `--post-design`) and `manage_worker_pool.py cleanup`.
     - Start a bound local `127.0.0.1` `TasksServer` alongside a local static HTTP server serving `quota_dashboard.html`, verify `/api/tasks` + `/api/epic/pic` root+worktree updates (including concurrent `quality_runs`, dead-PID/`ttl_sec` stale recovery, and multi-epic `pending_decision` isolation), and run real provisioned **headless Chrome CDP** (`CHROME_BIN` / local Google Chrome + `node v25` WebSocket) against live `tasks_dashboard.html` (`96%` cap, Section II `tier2Sig`, distinct same-day mtime order stability + native `<select>` focus guard, `/api/launch/quota` -> `#quota-iframe` `?embedded=1`) embedding real `quota_dashboard.html` inside the real `<iframe>` (verifying `getComputedStyle` flattening, Single Modal Stack Controller `max=1`, backdrop/Escape cascade, and cross-iframe `{ action: 'reset_quota_submodals' }`) with zero browser console/exception errors.
   - **`RSDH-FR-06`**: Verify regression invariants deterministically:
     - `rules/CRITICAL_RULES.md` UTF-8 size `<= 8192` bytes; `skills/dev-designer/SKILL.md` UTF-8 size `<= 22528` bytes.
     - `skills/check-tasks/resources/scripts/check_tasks.py` contains no Strategy 7 alphabetical fallback to unstarted `.devtool/epic/` folders (`choosing_a_lifecycle`).
     - `skills/dev-lifecycle/references/handoff-template.md` + `package_epic.py` leave zero unreplaced `<profile_account_id>` literal when packaging an epic with a detected creator profile.
     - `scripts/verify.sh` registers every `tests/test_rsdh_*.py` and `tests/test_runtime_sync_and_dashboard_hardening.py` suite inside `SUITES`, and `.agents/quality/python-quality.json` includes `scripts/_state_envelope.py` and `scripts/estimate_heartbeat.py` in standing `format`/`lint`/`type_check` coverage.
2. **Suite Registration & Standing Quality Coverage (`scripts/verify.sh`, `.agents/quality/python-quality.json`)**:
   - Update `SUITES = [` (`L362-L420`) in `scripts/verify.sh` to include all new epic unit/integration suites (`tests/test_rsdh_state_envelope.py`, `tests/test_rsdh_heartbeat_quality.py`, `tests/test_rsdh_orchestration.py`, `tests/test_rsdh_harvester_and_pic.py`, `tests/test_rsdh_tasks_dashboard_ui.py`, `tests/test_rsdh_quota_modal_stack.py`, `tests/test_runtime_sync_and_dashboard_hardening.py`) without triggering recursive `verify.sh` execution inside pytest.
   - Extend `.agents/quality/python-quality.json` `format`, `lint`, and `type_check` commands to include `scripts/_state_envelope.py` and `scripts/estimate_heartbeat.py` so standing Gate 4 runs cover the new `scripts/` modules continuously.

## Files

Allowed files:
- `tests/test_runtime_sync_and_dashboard_hardening.py` (new)
- `scripts/verify.sh`
- `.agents/quality/python-quality.json`

Read-only context:
- `.devtool/epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md` — HLD Integration Test Plan & Coverage Matrix
- `.devtool/epic/runtime_sync_and_dashboard_hardening/bdd_scenarios.en.md` — Canonical BDD Scenarios (`RSDH-HP-09`, `RSDH-FR-06`)

## Design Rationale

Per-component suites (`test_rsdh_*.py`) isolate Wave 1–3 contracts, while `test_runtime_sync_and_dashboard_hardening.py` proves that envelope writes, `resume_context`, `verify_polyglot_registry`, `check_tasks` / `TasksServer`, `tasks_dashboard.html`, and `quota_dashboard.html` work seamlessly as a single system. Registering all 7 suites in `scripts/verify.sh` ensures future kit releases cannot silently regress byte caps, idle false positives, `96%` UI display, or modal stacking. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:verification-before-completion`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/verify.sh`: `SUITES` array (L362-L420)
  - `.agents/quality/python-quality.json`: small file (`16` lines `<= 200`), extend `format`, `lint`, and `type_check` with `scripts/_state_envelope.py` and `scripts/estimate_heartbeat.py`
  - `tests/test_runtime_sync_and_dashboard_hardening.py`: new end-to-end and regression test suite (`test_rsdh_hp_09_cross_layer_orchestration`, `test_rsdh_fr_06_verify_and_byte_budget_invariants`)
- **Downstream Callers**: `.agents/quality/python-quality.json` (`architecture` capability `bash scripts/verify.sh`) and release Gate 4 verification.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% cross-layer boundary path + continuous verification registration of all 7 epic test suites.

### BDD SCENARIOS

Covers: RSDH-HP-09, RSDH-FR-06


```gherkin
Scenario: [RSDH-HP-09] [Tier C - Integration] End-to-end orchestration, envelope sync, 96% dashboard, PIC sync, and Chrome CDP modal stack pass together

Given a multi-worktree workspace running live TasksServer HTTP endpoints with Wave 1-3 updates applied
When an epic advances through sync_task_status, verify_polyglot_registry progress, Choice A pending-decision save/clear, PIC reassignment across root and worktree, and real provisioned Chrome CDP parent/iframe dashboard interactions
Then live /api/tasks reflects 96% pre-finish progress, updated PICs, cleared bottlenecks, and live browser rendering passes with zero console or runtime errors

Scenario: [RSDH-FR-06] [Tier C - Integration] Registered verification suites guard byte budgets, idle false positives, and snapshot isolation continuously

Given scripts/verify.sh with all epic suites registered in SUITES and current kit files on disk
When bash scripts/verify.sh --quiet runs and regression checks inspect CRITICAL_RULES.md, dev-designer/SKILL.md, and dashboard scripts
Then CRITICAL_RULES.md remains <= 8192 bytes, dev-designer/SKILL.md remains <= 22528 bytes, idle alphabetical fallbacks stay absent, and all registered verification sections exit 0
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_runtime_sync_and_dashboard_hardening.py::test_rsdh_fr_06_verify_and_byte_budget_invariants` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_runtime_sync_and_dashboard_hardening.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `bash scripts/verify.sh --quiet` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_runtime_sync_and_dashboard_hardening.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_7.xml tests/test_rsdh_state_envelope.py tests/test_rsdh_heartbeat_quality.py tests/test_rsdh_orchestration.py tests/test_rsdh_harvester_and_pic.py tests/test_rsdh_tasks_dashboard_ui.py tests/test_rsdh_quota_modal_stack.py tests/test_runtime_sync_and_dashboard_hardening.py` | exit 0; results build/test-results/task_7.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `test_runtime_sync_and_dashboard_hardening.py` MUST NOT spawn `bash scripts/verify.sh` recursively inside `pytest` because `verify.sh` itself executes `SUITES` (preventing infinite subprocess recursion); full `verify.sh --quiet` execution is verified explicitly in V3 and Gate 4.
- All 7 new test files (`test_rsdh_*.py` + `test_runtime_sync_and_dashboard_hardening.py`) are explicitly appended to `SUITES` inside `scripts/verify.sh` (`L362-L420`).
- Real browser end-to-end assertions run via provisioned headless Google Chrome CDP (`CHROME_BIN` -> `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` -> `google-chrome`/`chromium`) driven by `node` (`v25.6.0`) built-in `WebSocket` against live bound `127.0.0.1` `TasksServer` across real parent `tasks_dashboard.html` + `<iframe src="http://127.0.0.1:<quota_port>/?embedded=1">` (`quota_dashboard.html`) with zero pip/npm downloads required.

## Definition of Done

- Scenarios RSDH-HP-09 and RSDH-FR-06 pass cleanly across real git worktrees, HTTP server, Node + provisioned Chrome CDP browser checks, and byte budget guards. (V2, V6)
- `bash scripts/verify.sh --quiet` exits `0` with all 7 new test suites registered and green. (V3)
- Ruff lint and registered mypy checks pass cleanly. (V4, V5)

## Dependencies & Blockers

Blocked by [Task 1](../epic/runtime_sync_and_dashboard_hardening/task_01_runtime_state_envelope_and_two_tier_sync.md), [Task 2](../epic/runtime_sync_and_dashboard_hardening/task_02_hybrid_heartbeat_estimator_and_quality_progress.md), [Task 3](../epic/runtime_sync_and_dashboard_hardening/task_03_wave_parallel_handoff_stage3_revise_and_pool_cleanup.md), [Task 4](../epic/runtime_sync_and_dashboard_hardening/task_04_check_tasks_harvester_bottleneck_and_pic_backend.md), [Task 5](../epic/runtime_sync_and_dashboard_hardening/task_05_tasks_dashboard_96pct_tier2_live_and_roadmap_stability.md), and [Task 6](../epic/runtime_sync_and_dashboard_hardening/task_06_check_quota_modal_stack_controller.md).

## References & Rollback

- [Epic HLD](../epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md), Integration Test Plan and Boundary Matrix.
- **Rollback**: Revert task commit; removes `tests/test_runtime_sync_and_dashboard_hardening.py` and restores `scripts/verify.sh` `SUITES`.
