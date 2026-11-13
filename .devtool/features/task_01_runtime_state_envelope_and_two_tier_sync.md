---
id: "task_01_runtime_state_envelope_and_two_tier_sync"
status: "todo"
priority: "high"
assignee: null
epic: "runtime_sync_and_dashboard_hardening"
dueDate: null
created: "2026-11-13T09:18:00Z"
modified: "2026-11-13T09:18:00Z"
completedAt: null
labels: ["architecture", "concurrency", "state-sync"]
order: "a1"
review_tier: "full"
---

# Task 1: Atomic Runtime State Envelope and Two-Tier Memory Sync

Epic: [runtime_sync_and_dashboard_hardening](../epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md)

## Requirement Analysis

Implement the shared atomic runtime state layer (`scripts/_state_envelope.py`) and mechanically couple Kanban / memory transitions to dual-root `.devtool/state/` snapshots across worktree and primary repository roots:

1. **Shared State Envelope (`scripts/_state_envelope.py`)**:
   - Provide `resolve_shared_devtool_dirs(start_path: Path) -> list[Path]` returning deduplicated `.devtool/` paths for both the active worktree top-level (`git rev-parse --show-toplevel`) and the primary repository root (`git rev-parse --git-common-dir` parent).
   - Provide `atomic_write_json(path: Path, payload: dict[str, Any]) -> None` using a sibling temporary file + `os.replace()` protected by an `fcntl.flock` sidecar lock (`path.with_suffix(path.suffix + ".lock")`).
   - Provide `read_json_safe(path: Path, default: T) -> T` returning `default` cleanly on missing, empty, or malformed JSON.
   - Provide structured domain helpers (`update_epic_heartbeat(...)`, `write_pending_decision(...)`, `clear_pending_decision(...)`, `write_quality_active(...)`) mirroring writes atomically across all resolved shared `.devtool/state/` directories.
2. **Mechanical Two-Tier Sync in `resume_context.py` and `sync_task_status.py`**:
   - Update `scripts/resume_context.py` (`write_epic_state` L728-L762 and `complete_feature_and_rotate` L785-L845) so saving state refreshes `<epic_slug>.heartbeat.json` across shared devtool dirs and completing an epic cleans/archives stale state files cleanly from both active worktree and primary repo `.devtool/state/` + `.devtool/assistant_state.md` rollup without duplicating `PROJECT_LEDGER.md` entries.
   - Update `skills/dev-implementation/resources/scripts/sync_task_status.py` (`sync_task` L303-L335, `sync_epic` L566-L600, `main` L1079-L1276) so task/epic status mutations mechanically call `update_epic_heartbeat()`, regenerate `.devtool/state/<epic_slug>.md` + `.devtool/assistant_state.md` under lock (`resume_context`), and invoke `clear_pending_decision()` when marking a task `in-progress` or `done`.
3. Add `tests/test_rsdh_state_envelope.py` covering `RSDH-HP-01`, `RSDH-EC-01`, `RSDH-AR-01`, and `RSDH-FR-01`.

## Files

Allowed files:
- `scripts/_state_envelope.py` (new)
- `scripts/resume_context.py`
- `skills/dev-implementation/resources/scripts/sync_task_status.py`
- `tests/test_rsdh_state_envelope.py` (new)

Read-only context:
- `.devtool/epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md` — HLD Module Contracts and JSON schemas
- `.devtool/epic/runtime_sync_and_dashboard_hardening/bdd_scenarios.en.md` — Canonical BDD Scenarios
- `.agents/quality/python-quality.json` — Registered lint and type_check commands

## Design Rationale

`sync_task_status.py` and `manage_worker_pool.py` frequently execute inside `.worktrees/<epic_dir>`, while `check_tasks.py` and `tasks_server.py` inspect the primary repository root. Centralizing dual-root atomic JSON writes and mechanical Two-Tier Memory updates in `scripts/_state_envelope.py` keeps both views synchronized without external daemons or database locks. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/_state_envelope.py`: new shared atomic state module (`resolve_shared_devtool_dirs`, `atomic_write_json`, `read_json_safe`, `update_epic_heartbeat`, `write_pending_decision`, `clear_pending_decision`, `write_quality_active`)
  - `scripts/resume_context.py`: `write_epic_state` (L728-L762), `complete_feature_and_rotate` (L785-L845)
  - `skills/dev-implementation/resources/scripts/sync_task_status.py`: `sync_task` (L303-L335), `sync_epic` (L566-L600), `main` (L1079-L1276)
  - `tests/test_rsdh_state_envelope.py`: new test suite for `RSDH-HP-01`, `RSDH-EC-01`, `RSDH-AR-01`, `RSDH-FR-01`
- **Downstream Callers**: `skills/dev-implementation/resources/scripts/manage_worker_pool.py`, `skills/quality_check/resources/scripts/verify_polyglot_registry.py`, `skills/check-tasks/resources/scripts/check_tasks.py`, `scripts/test_resume_context.py`, `skills/dev-implementation/resources/scripts/test_sync_task_status.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of dual-root path resolution, `flock` atomic replace, corrupt fallback, and mechanical `.md` sync paths.

### BDD SCENARIOS

Covers: RSDH-HP-01, RSDH-EC-01, RSDH-AR-01, RSDH-FR-01


```gherkin
Scenario: [RSDH-HP-01] [Tier C - Integration] Atomic runtime state envelope syncs worktree, primary repo, and Two-Tier Memory

Given a git repository with an active isolated worktree on epic branch "epic/demo-sync" and matching Kanban tasks
When _state_envelope.update_epic_heartbeat records a task transition and sync_task_status.py marks task_01 "in-progress"
Then .devtool/state/demo-sync.heartbeat.json is written atomically via os.replace to both the worktree and primary repository .devtool/state directories
And both .devtool/state/demo-sync.md and .devtool/assistant_state.md reflect the updated task status and timestamp mechanically without manual resume_context invocations

Scenario: [RSDH-EC-01] [Tier A - Unit] Envelope reader tolerates missing, empty, or truncated state JSON without failing

Given nonexistent, zero-byte, and malformed truncated files at .devtool/state/broken.heartbeat.json
When _state_envelope.read_json_safe reads each path with a default dictionary
Then read_json_safe returns the provided default dictionary cleanly without raising JSONDecodeError or OSError

Scenario: [RSDH-AR-01] [Tier C - Integration] Concurrent multi-process envelope writes preserve valid JSON and latest updates under flock

Given multiple worker processes concurrently calling _state_envelope.atomic_write_json and update_epic_heartbeat on the same .devtool/state/ targets
When all parallel writes complete across 16 concurrent invocations
Then every JSON file parses cleanly without truncation or JSONDecodeError and lock contention produces zero exceptions

Scenario: [RSDH-FR-01] [Tier C - Integration] Stale heartbeat metadata never blocks subsequent task status synchronization

Given an old heartbeat.json file referencing an aborted previous wave and missing slot directory
When sync_task_status.py or resume_context.py writes a new state transition
Then the stale heartbeat is safely superseded atomically under lock and execution continues cleanly
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_state_envelope.py::test_rsdh_hp_01_dual_root_envelope_and_sync` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_state_envelope.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m unittest scripts/test_resume_context.py skills/dev-implementation/resources/scripts/test_sync_task_status.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/resume_context.py skills/dev-implementation/resources/scripts/sync_task_status.py tests/test_rsdh_state_envelope.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/resume_context.py skills/dev-implementation/resources/scripts/sync_task_status.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_1.xml tests/test_rsdh_state_envelope.py` | exit 0; results build/test-results/task_1.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `_state_envelope.py` resolves unique `.devtool/` dirs via `git rev-parse --show-toplevel` and `git rev-parse --git-common-dir` so worktree executions mirror runtime JSON envelopes (`<epic_slug>.heartbeat.json`, `quality_active.json`, `pending_decision.json`) to primary repo `.devtool/state/` as well.
- All JSON mutations go through a sidecar `.lock` under `fcntl.flock` + temporary sibling write + `os.replace()`; `read_json_safe()` catches `OSError` and `json.JSONDecodeError` returning defaults cleanly.
- `sync_task_status.py` refreshes `.devtool/state/<epic_slug>.md` + `.devtool/assistant_state.md` via `resume_context.write_epic_state` / `render_assistant_state_rollup` when available and calls `clear_pending_decision()` on `in-progress` and `done` transitions without duplicating `PROJECT_LEDGER.md`.
- `resume_context.py` (`write_epic_state` L728-L762, `complete_feature_and_rotate` L785-L845) synchronizes completion/archival across shared `.devtool/` dirs cleanly.
- `tests/test_rsdh_state_envelope.py` MUST import `scripts/_state_envelope` lazily inside each test function body rather than at module top level so pytest V1 RED runs execute collected tests and exit `1` (`failed`) instead of failing collection with exit `2`.

## Definition of Done

- Scenarios RSDH-HP-01, RSDH-EC-01, RSDH-AR-01, and RSDH-FR-01 pass in real temporary git repos with worktrees and multi-process concurrency. (V2, V6)
- Existing `test_resume_context.py` and `test_sync_task_status.py` suites pass without regressions. (V3)
- Ruff lint and mypy strict checks pass across modified files and `tests/test_rsdh_state_envelope.py`. (V4, V5)
- Dual-root atomic synchronization verified on candidate commit. (Gate 5)

## Dependencies & Blockers

None.

Downstream dependents (blocked by Task 1): `task_03`, `task_04`, `task_05`, `task_07`.

## References & Rollback

- [Epic HLD](../epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md), Module Contracts (§4.1 / `_state_envelope.py`).
- **Rollback**: Revert task commit; removes `scripts/_state_envelope.py` and restores `resume_context.py` and `sync_task_status.py`.
