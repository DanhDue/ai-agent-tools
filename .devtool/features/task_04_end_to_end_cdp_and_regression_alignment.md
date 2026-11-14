---
id: "task_04_end_to_end_cdp_and_regression_alignment"
status: "todo"
priority: "high"
assignee: null
epic: "check_tasks_epic_history_modal"
dueDate: null
created: "2026-11-15T01:00:00Z"
modified: "2026-11-15T01:00:00Z"
completedAt: null
labels: ["integration", "cdp", "e2e", "verify"]
order: "a4"
review_tier: "full"
---

# Task 4: End-to-End Integration, Headless Chrome CDP Verification, and Regression Alignment

Epic: [check_tasks_epic_history_modal](../epic/check_tasks_epic_history_modal/check_tasks_epic_history_modal.en.md)

## Requirement Analysis

Build the end-to-end headless Chrome CDP integration acceptance suite `tests/test_cehm_e2e_cdp.py` and register all 4 `CEHM` test suites inside `scripts/verify.sh` (`SUITES` `L362-L435`):

1. **End-to-End Headless Chrome CDP Verification (`tests/test_cehm_e2e_cdp.py`)**:
   - Launch `TasksServer` over an isolated temporary workspace directory bound to an ephemeral port (`find_available_port`), seeded with mock repositories containing:
     - `"done_epic"`: 11 `task_*.md` items with `evidence/*.json`, `gate_ledger.jsonl`, `events_done-epic.jsonl` (archived >20 events), and 2-round `principal_review.md` + 2-round `review_results.md`,
     - `"in_prog_epic"`: worktree active task state alongside live Section II card, and
     - `"backlog_epic"`: HLD draft only (no tasks, logs, or reviews).
   - Execute `CEHM-FR-02` (`test_cehm_fr_02_end_to_end_chrome_cdp_history_modal_workflow`) via real headless Chrome CDP (reusing `_NODE_CDP_HELPER` and `_resolve_chrome_binary` from `tests/test_rsdh_tasks_dashboard_ui.py`), verifying:
     - Clicking `.roadmap-epic-row` for `"done_epic"` opens `#modal-epic-history` with 6-stage summary while Section II underneath remains intact,
     - Interacting with inline `PIC` `<select>` does not open `#modal-epic-history`,
     - Filtering `Timeline & Step Logs` via `All`, `Gates`, `Steps`, `Activity`, and `Evidence` pills,
     - Expanding verification rows under `Tasks & Evidence`,
     - Switching directly between `Principal Review` and `Cross-Model Review` and switching Round 1 <-> Round 2 without stacking a second modal,
     - Simulating an HTTP 500 response from `/api/epic/history` triggers the inline Retry banner and recovers cleanly on retry,
     - Pressing `Escape` closes `#modal-epic-history` and restores body scroll lock,
     - Recording `cdp.consoleErrors == []` and `cdp.runtimeExceptions == []`.
2. **Release Verification Suite Registration (`scripts/verify.sh` `L362-L435`)**:
   - Append section `20` entries in `SUITES` for `tests/test_cehm_telemetry_stream.py`, `tests/test_cehm_history_aggregator.py`, `tests/test_cehm_dashboard_modal_ui.py`, and `tests/test_cehm_e2e_cdp.py`.

## Files

Allowed files:
- `tests/test_cehm_e2e_cdp.py` (new)
- `scripts/verify.sh`

Read-only context:
- `.devtool/epic/check_tasks_epic_history_modal/check_tasks_epic_history_modal.en.md` — HLD & Integration Results Contract
- `.devtool/epic/check_tasks_epic_history_modal/bdd_scenarios.en.md` — Canonical BDD Scenarios
- `tests/test_rsdh_tasks_dashboard_ui.py` — Shared headless Chrome CDP helpers

## Design Rationale

Validating the complete producer -> harvester -> HTTP `/api/epic/history` -> browser DOM workflow inside real headless Chrome CDP and registering the suites in `scripts/verify.sh` guarantees durable end-to-end correctness across releases. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `tests/test_cehm_e2e_cdp.py`: new end-to-end headless Chrome CDP integration suite
  - `scripts/verify.sh`: `SUITES` (L362-L435)
- **Downstream Callers**: `scripts/verify.sh` release verification and Gate 4 acceptance checks.
- **Cross-Platform Bridges**: End-to-end browser HTTP/DOM/JS bridge between `tasks_dashboard.html` and `tasks_server.py`.
- **Target Test Coverage Threshold**: 100% of all 15 `CEHM-*` BDD scenarios verified across Tasks 1..4 and passing full regression.

### BDD SCENARIOS

Covers: CEHM-FR-02

```gherkin
Scenario: [CEHM-FR-02] [Tier C - Integration] End-to-end headless Chrome CDP validates full modal forensics workflow, filters, error retry, and zero console errors
Given a live `TasksServer` backed by mock repositories containing `"done_epic"` (11 tasks with evidence, gate ledger, events stream, and 2-round Principal + Cross-Model reviews), `"in_prog_epic"`, and `"backlog_epic"`
When Playwright / Chrome CDP tests Roadmap click interactions, PIC select isolation, Timeline category filter chips (`All`, `Gates`, `Steps`, `Activity`, `Evidence`), expandable task verification rows, direct Principal <-> Cross-Model Review tab & round switching, HTTP 500 inline Retry banner recovery, and `ESC` dismissal
Then every asserted DOM panel renders accurate non-empty historical values while Section II remains intact underneath
And `cdp.consoleErrors` and `cdp.runtimeExceptions` are both `[]`
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cehm_e2e_cdp.py::test_cehm_fr_02_end_to_end_chrome_cdp_history_modal_workflow` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cehm_e2e_cdp.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_cehm_e2e_cdp.py tests/test_cehm_telemetry_stream.py tests/test_cehm_history_aggregator.py tests/test_cehm_dashboard_modal_ui.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && mypy tests/test_cehm_e2e_cdp.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/check-tasks-epic-history-modal.xml tests/test_cehm_telemetry_stream.py tests/test_cehm_history_aggregator.py tests/test_cehm_dashboard_modal_ui.py tests/test_cehm_e2e_cdp.py tests/test_check_tasks_server.py tests/test_check_tasks_fsm.py tests/test_ltsp_state_and_producers.py tests/test_ltsp_harvester_pipeline.py tests/test_ltsp_dashboard_ui.py tests/test_rsdh_state_envelope.py tests/test_rsdh_harvester_and_pic.py tests/test_rsdh_tasks_dashboard_ui.py` | exit 0; results build/test-results/check-tasks-epic-history-modal.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- All CDP tests bind `TasksServer` inside `tmp_path` and dynamic ephemeral ports without touching `~/.gemini` or `/tmp/agy_tasks_server.pid`.
- `build/test-results/check-tasks-epic-history-modal.xml` is written by `V5` (`TIER-C`) to match the HLD `Integration results:` contract.
- `scripts/verify.sh` `SUITES` registers all four `tests/test_cehm_*.py` modules with `mode="pytest"` under Section `20`.

## Definition of Done

- Scenario CEHM-FR-02 passes in headless Chrome CDP with `cdp.consoleErrors == []` and `cdp.runtimeExceptions == []`. (V2, V5)
- `scripts/verify.sh` includes all four `tests/test_cehm_*.py` test suites. (V5)
- Ruff lint, mypy typecheck, and the entire cross-epic regression matrix exit 0 with `build/test-results/check-tasks-epic-history-modal.xml` written. (V3, V4, V5)

## Dependencies & Blockers

Blocked by [Task 1](task_01_append_only_event_stream_and_archival.md), [Task 2](task_02_epic_history_aggregator_and_scoped_api.md), [Task 3](task_03_shared_helpers_and_epic_history_modal_ui.md).

Downstream dependents (blocked by Task 4): None.

## References & Rollback

- [Epic HLD](../epic/check_tasks_epic_history_modal/check_tasks_epic_history_modal.en.md)
- **Rollback**: Revert task commit to restore `scripts/verify.sh` and remove `tests/test_cehm_e2e_cdp.py`.
