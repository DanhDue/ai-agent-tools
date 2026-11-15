---
id: "task_01_append_only_event_stream_and_archival"
status: "done"
priority: "high"
assignee: null
epic: "check_tasks_epic_history_modal"
dueDate: null
created: "2026-11-15T01:00:00Z"
modified: "2026-11-14T18:30:56Z"
completedAt: "2026-11-14T18:30:56Z"
labels: ["telemetry", "state-envelope", "archival", "concurrency"]
order: "a1"
review_tier: "full"
---

# Task 1: Append-Only Per-Epic Event Stream and Dual-Variant Archival

Epic: [check_tasks_epic_history_modal](check_tasks_epic_history_modal.en.md)

## Requirement Analysis

Eliminate the 20-event rolling-buffer ceiling on long epics and close the underscore/hyphen heartbeat filename split across archival:

1. **Untruncated Append-Only Event Stream (`scripts/_state_envelope.py`)**:
   - Extend `update_epic_heartbeat()` (`L430-L565`) so that inside the existing `run_state_transaction()` / `_discover_active_mirror_dirs()` flow, whenever a new distinct event or state transition occurs (`last_event` is non-empty and differs from the previous trailing event message, or `stage`, `sub_step`, or `review_state` phase/round changed), it appends a single compact JSONL record to `.devtool/logs/events_<safe_slug>.jsonl` across each mirrored `.devtool` directory while keeping `.devtool/state/<safe_slug>.heartbeat.json` capped at `max_events = 20`.
   - When `last_event` repeats identically with no stage/sub-step/review transition (only `updated_at` ticking), update the live heartbeat snapshot's `ts` in-place without writing duplicate lines to `.devtool/logs/events_<safe_slug>.jsonl`.
   - Keep append logic exception-safe (wrapping optional JSONL appends safely when `.devtool/logs` cannot be created only if tolerated, or writing atomically under the transaction lock so concurrent multi-worker calls never interleave partial JSON lines).
2. **Dual-Variant Heartbeat & Event Stream Archival (`scripts/resume_context.py`)**:
   - Update `complete_feature_and_rotate()` (`L954-L1068`) in `--complete` mode so archival moves:
     - both `<safe_slug>.heartbeat.json` and any `<epic_slug>.heartbeat.json` / underscore-hyphen counterpart (`_sanitize_epic_slug` vs raw underscore slug) to `.devtool/archive/heartbeat_<variant>_<timestamp>.json`, leaving zero orphan `.heartbeat.json` files for that epic inside `.devtool/state/`, and
     - `.devtool/logs/events_<safe_slug>.jsonl` (plus `<epic_slug>` variant if present) to `.devtool/archive/events_<safe_slug>_<timestamp>.jsonl`.
3. **Unit & Concurrency Verification (`tests/test_cehm_telemetry_stream.py`)**:
   - Verify scenarios `CEHM-HP-01` (25+ events preserved across archival, zero orphan state/log files) and `CEHM-AR-01` (6 threads x 8 concurrent calls = 48 valid non-interleaved JSONL records across mirrors).

## Files

Allowed files:
- `scripts/_state_envelope.py`
- `scripts/resume_context.py`
- `tests/test_cehm_telemetry_stream.py` (new)

Read-only context:
- `.devtool/epic/check_tasks_epic_history_modal/check_tasks_epic_history_modal.en.md` — HLD Module Contracts
- `.devtool/epic/check_tasks_epic_history_modal/bdd_scenarios.en.md` — Canonical BDD Scenarios

## Design Rationale

Preserving the existing `max_events = 20` ring buffer inside `<safe_slug>.heartbeat.json` guarantees zero `/api/tasks` polling bloat while appending transitions to `.devtool/logs/events_<safe_slug>.jsonl` gives `#modal-epic-history` complete step forensics across long multi-round epics and clean archival under `--complete`. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/_state_envelope.py`: `update_epic_heartbeat` (L430-L565), `run_state_transaction` (L387), `_discover_active_mirror_dirs` (L241), `_sanitize_epic_slug` (L115), new `_append_epic_event_stream`
  - `scripts/resume_context.py`: `complete_feature_and_rotate` (L954-L1068)
  - `tests/test_cehm_telemetry_stream.py`: new unit and concurrency test suite
- **Downstream Callers**: `skills/check-tasks/resources/scripts/check_tasks.py` (`harvest_epic_history`), `tests/test_ltsp_state_and_producers.py`, `tests/test_rsdh_state_envelope.py`, `scripts/test_resume_context.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of `events_<safe_slug>.jsonl` append/dedup rules and `--complete` dual-variant archival branches covered.

### BDD SCENARIOS

Covers: CEHM-HP-01, CEHM-AR-01

```gherkin
Scenario: [CEHM-HP-01] [Tier A - Unit] Untruncated append-only event stream records over 20 steps and archives dual hyphen-underscore heartbeats
Given an isolated git repository with epic "alpha_epic" inside `.devtool/state/`
When `update_epic_heartbeat` is invoked 25 times with distinct `last_event` values `"step-01"` through `"step-25"` and `resume_context.py --complete alpha_epic "Completed alpha"` runs while `.devtool/state/alpha_epic.heartbeat.json` also exists
Then `.devtool/state/alpha-epic.heartbeat.json` keeps at most 20 events before archival while `.devtool/archive/events_alpha-epic_*.jsonl` retains all 25 events `"step-01"` through `"step-25"`
And `.devtool/state/` no longer contains orphan `alpha-epic.heartbeat.json`, `alpha_epic.heartbeat.json`, or `logs/events_alpha-epic.jsonl` files

Scenario: [CEHM-AR-01] [Tier A - Unit] Concurrent update_epic_heartbeat callers write valid non-interleaved lines to events JSONL under transactional lock
Given 6 worker threads sharing an isolated git repo with root and worktree `.devtool` mirrors for epic `"concurrent_epic"`
When each thread calls `update_epic_heartbeat` 8 times concurrently with distinct worker-tagged `last_event` strings
Then every line in `.devtool/logs/events_concurrent-epic.jsonl` across both mirrors parses cleanly with `json.loads()`
And all 48 unique worker events are preserved without truncation or partial JSON corruption
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cehm_telemetry_stream.py::test_cehm_hp_01_append_only_events_and_dual_archival` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cehm_telemetry_stream.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ltsp_state_and_producers.py tests/test_rsdh_state_envelope.py && python3 -m unittest scripts/test_resume_context.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/resume_context.py tests/test_cehm_telemetry_stream.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/resume_context.py tests/test_cehm_telemetry_stream.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/cehm_task_01.xml tests/test_cehm_telemetry_stream.py tests/test_ltsp_state_and_producers.py tests/test_rsdh_state_envelope.py` | exit 0; results build/test-results/cehm_task_01.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `update_epic_heartbeat()` in `scripts/_state_envelope.py` (`L430-L565`) retains its exact existing parameter signature and defaults while appending `{ "ts": ..., "stage": ..., "sub_step": ..., "sub_step_detail": ..., "message": ..., "review_state": ... }` lines (omitting null/empty optional sub-fields only if desired or keeping stable keys) into `.devtool/logs/events_<safe_slug>.jsonl` across every mirrored `.devtool` root under `run_state_transaction()`.
- Duplicate suppression checks the prior snapshot's trailing event message, `stage`, `sub_step`, and `review_state` `(phase, round, kind)` so idle heartbeat ticks (`updated_at` only) never bloat `events_<safe_slug>.jsonl`.
- `complete_feature_and_rotate()` in `scripts/resume_context.py` (`L954-L1068`) archives `<safe_slug>.heartbeat.json`, raw `<epic_slug>.heartbeat.json` (plus underscore/hyphen toggle), `activity_<epic_slug>.log`, and `events_<safe_slug>.jsonl` (plus raw `<epic_slug>` variant if distinct) into `.devtool/archive/`.

## Definition of Done

- Scenarios CEHM-HP-01 and CEHM-AR-01 pass with all 25+ events preserved and clean dual-variant archival. (V2, V6)
- Existing state envelope and `resume_context.py` test suites pass without regression. (V3, V6)
- Ruff lint and mypy typecheck pass cleanly on all modified Python files. (V4, V5)

## Dependencies & Blockers

None.

Downstream dependents (blocked by Task 1): `task_02`, `task_03`, `task_04`.

## References & Rollback

- [Epic HLD](check_tasks_epic_history_modal.en.md)
- **Rollback**: Revert task commit to restore `scripts/_state_envelope.py` and `scripts/resume_context.py`.
