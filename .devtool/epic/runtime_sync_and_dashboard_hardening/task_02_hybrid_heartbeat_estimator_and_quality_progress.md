---
id: "task_02_hybrid_heartbeat_estimator_and_quality_progress"
status: "done"
priority: "high"
assignee: null
epic: "runtime_sync_and_dashboard_hardening"
dueDate: null
created: "2026-11-13T09:18:00Z"
modified: "2026-11-13T03:27:40Z"
completedAt: "2026-11-13T03:27:40Z"
labels: ["observability", "quality-check", "heartbeat"]
order: "a2"
review_tier: "full"
---

# Task 2: Hybrid Heartbeat Estimator and Live Quality Progress

Epic: [runtime_sync_and_dashboard_hardening](runtime_sync_and_dashboard_hardening.en.md)

## Requirement Analysis

Implement zero-LLM workload duration estimation (`scripts/estimate_heartbeat.py`) and zero-token live `stderr` + `quality_active.json` progress reporting inside `verify_polyglot_registry.py`:

1. **Rule-Based Heartbeat Estimator (`scripts/estimate_heartbeat.py`)**:
   - Accept `--tasks-count`, `--files-count`, `--epic-dir`, `--wave`, `--quality-profile` (`fast|pr|epic|release|full`), `--has-e2e`, and `--json`.
   - When `--epic-dir` (and optional `--wave`) is passed without explicit counts, inspect `.devtool/features/` / `.devtool/epic/<epic_dir>/task_*.md` to derive pending task count and modified file count cleanly.
   - Evaluate deterministic additive formula (`base 5s + 25s*tasks + 5s*files + profile baseline {fast:15, pr:120, epic:210, release:245, full:245} + e2e bonus 240s`, yielding `5s` for 0/0, `35s` for 1/1, `80s` for 2/5, `250s` for `--quality-profile full`) into tiers:
     - `estimated_sec < 60` -> `"light"`, `recommended_interval_sec: null`
     - `60 <= estimated_sec <= 240` -> `"medium"`, `recommended_interval_sec: 180`
     - `estimated_sec > 240` -> `"heavy"`, `recommended_interval_sec: 240` (escalating to `300` strictly when `--has-e2e` is set)
2. **Live Progress Streaming, Isolation & Signal Safety in `verify_polyglot_registry.py`**:
   - Upgrade `execute_provider` (`L142-L458`) and `verify_polyglot_execution` (`L459-L557`) to accept optional `heartbeat_interval` (default `15.0`, CLI `--heartbeat-interval` in `main` `L636-L726`) and `epic_slug` (`--epic` / auto-resolved).
   - Assign a unique `run_id` per invocation and launch capability subprocesses via `subprocess.Popen(..., start_new_session=True)` redirecting combined stdout/stderr into run-isolated logs `build/quality/<provider_id>/runs/<run_id>/<cap_name>.log` so concurrent runs never collide.
   - Poll at `heartbeat_interval` ticks, printing `[quality_check] <i>/<n> <provider>:<cap> (<elapsed>s elapsed)` to `stderr` and refreshing namespaced `runs[run_id]` inside `.devtool/state/quality_active.json` (`run_id`, `epic_slug`, `pid`, `host`, `updated_at`, `ttl_sec = max(120, estimated_sec * 2)`) under `scripts/_state_envelope.py` (with local locked fallback).
   - Register `SIGINT` & `SIGTERM` handlers (saving & cleanly restoring prior handlers) alongside `try ... finally` to terminate (`os.killpg` `SIGTERM` -> bounded wait -> `SIGKILL`) and reap active child process groups cleanly, finalizing **only** `runs[run_id]` (under `run_id` ownership) to `"passed"`, `"failed"`, or `"aborted"` with `finished_at` without touching concurrent live runs.
3. **Document Estimator & Watchdog Workflow (`skills/quality_check/SKILL.md`)**:
   - Document running `python3 scripts/estimate_heartbeat.py --quality-profile <profile> --json` before long quality checks and monitoring live `[quality_check]` stderr output / namespaced `quality_active.json`.
4. Add `tests/test_rsdh_heartbeat_quality.py` covering `RSDH-HP-02`, `RSDH-HP-03` (concurrent run isolation + isolated `runs/<run_id>/` logs), `RSDH-EC-02`, `RSDH-FR-02`, and `RSDH-FR-07` (`SIGTERM` signal trap, child reaping, abort status without clobbering concurrent runs).

## Files

Allowed files:
- `scripts/estimate_heartbeat.py` (new)
- `skills/quality_check/resources/scripts/verify_polyglot_registry.py`
- `skills/quality_check/SKILL.md`
- `tests/test_rsdh_heartbeat_quality.py` (new)

Read-only context:
- `.devtool/epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md` — HLD Module Contracts (§4.2)
- `.devtool/epic/runtime_sync_and_dashboard_hardening/bdd_scenarios.en.md` — Canonical BDD Scenarios
- `tests/test_polyglot_gate4.py` — Existing polyglot Gate 4 contracts

## Design Rationale

Long `quality_check` runs across Android, iOS, Flutter, Rust, and Web previously blocked silently until exit, risking agent timeouts or blind polling that burns LLM tokens. Streaming 15-second `stderr` ticks plus atomic `quality_active.json` snapshots gives both humans and the `check-tasks` dashboard live visibility at zero token cost while keeping existing `verify_polyglot_execution` contracts backward-compatible. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/estimate_heartbeat.py`: new standalone CLI and library (`estimate_workload`, `build_parser`, `main`)
  - `skills/quality_check/resources/scripts/verify_polyglot_registry.py`: `execute_provider` (L142-L458), `verify_polyglot_execution` (L459-L557), `main` (L636-L726)
  - `skills/quality_check/SKILL.md`: complete file (`141` lines `<= 200`), pre-flight estimator & live quality heartbeat instructions
  - `tests/test_rsdh_heartbeat_quality.py`: new unit and subprocess integration tests for `RSDH-HP-02`, `RSDH-HP-03`, `RSDH-EC-02`, `RSDH-FR-02`
- **Downstream Callers**: `tests/test_polyglot_gate4.py`, `skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`, `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of estimator tier branches, `Popen` heartbeat loop, run-isolated logs/telemetry, `SIGINT`/`SIGTERM` child reaping + abort finalization, and `finally` transitions.

### BDD SCENARIOS

Covers: RSDH-HP-02, RSDH-HP-03, RSDH-EC-02, RSDH-FR-02, RSDH-FR-07


```gherkin
Scenario: [RSDH-HP-02] [Tier A - Unit] Simple rule-based heartbeat estimator maps workloads across light, medium, and heavy cadence tiers

Given representative inputs covering a 1-task/1-file micro fix, a 2-task/5-file feature wave, a full quality profile run (`--quality-profile full`), and an E2E quality run (`--has-e2e`)
When scripts/estimate_heartbeat.py evaluates each input via CLI and Python API with --json
Then the micro fix (estimated_sec 35 < 60) returns tier "light" with recommended_interval_sec null, the feature wave (estimated_sec 80) returns tier "medium" with recommended_interval_sec 180, the full quality run (estimated_sec 250) returns tier "heavy" with 240, and the E2E run returns tier "heavy" with 300

Scenario: [RSDH-HP-03] [Tier C - Integration] Polyglot quality runner streams zero-token stderr progress and isolates concurrent runs

Given two registered provider capability runs executing concurrently against the same capability under verify_polyglot_registry.py
When both execute via Popen with start_new_session=True, a shortened test heartbeat interval, and shared devtool state directories
Then verify_polyglot_registry.py writes isolated logs under build/quality/<provider>/runs/<run_id>/<capability>.log without collisions while printing periodic "[quality_check]" progress lines to stderr
And .devtool/state/quality_active.json namespaces both entries under runs[run_id] (with pid, host, updated_at, ttl_sec) and finalizes only each finished run_id without overwriting sibling live runs

Scenario: [RSDH-EC-02] [Tier A - Unit] Heartbeat estimator clamps zero inputs and escalates E2E runs to 300 seconds

Given an invocation of scripts/estimate_heartbeat.py with --tasks-count 0 --files-count 0 and another with --quality-profile epic --has-e2e
When both evaluations run
Then the empty input produces tier "light" with recommended_interval_sec null
And the epic E2E run produces tier "heavy" with recommended_interval_sec 300

Scenario: [RSDH-FR-02] [Tier C - Integration] Quality verification finalizes failing run_id without clobbering concurrent runs

Given a failing capability command in verify_polyglot_registry.py running alongside an independent healthy run_id in quality_active.json
When the failing command exits non-zero
Then only its own runs[run_id] transitions to status "failed" with non-null finished_at while sibling live runs remain intact

Scenario: [RSDH-FR-07] [Tier C - Integration] Signal-aborted quality verification reaps child processes and recovers stale owners

Given a running capability subprocess group under verify_polyglot_registry.py alongside an independent healthy concurrent run
When SIGTERM interrupts the first verify_polyglot_registry.py runner process
Then the signal handler terminates and reaps the active child process group and transitions only its own runs[run_id] to status "aborted" while leaving the sibling run intact
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_heartbeat_quality.py::test_rsdh_hp_03_live_stderr_and_quality_active` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_heartbeat_quality.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_polyglot_gate4.py && python3 -m unittest skills/quality_check/resources/scripts/test_quality_provider_acceptance.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/estimate_heartbeat.py tests/test_rsdh_heartbeat_quality.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/estimate_heartbeat.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_2.xml tests/test_rsdh_heartbeat_quality.py tests/test_polyglot_gate4.py` | exit 0; results build/test-results/task_2.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `scripts/estimate_heartbeat.py` is 100% deterministic (zero LLM/network calls) and maps discrete tiers: `< 60s -> light (null)`, `60..240s -> medium (180)`, `> 240s -> heavy (240, or 300 strictly with --has-e2e)` using `base 5s + 25s*tasks + 5s*files + profile {fast:15, pr:120, epic:210, release:245, full:245} + e2e 240s`.
- `verify_polyglot_registry.py` assigns a unique `run_id`, launches capability subprocesses with `start_new_session=True` streaming combined stdout/stderr into run-isolated `build/quality/<provider_id>/runs/<run_id>/<cap_name>.log`, emits `[quality_check] <i>/<n> <provider>:<cap> (<elapsed>s elapsed)` every `heartbeat_interval` (default `15.0s`), installs `SIGINT`/`SIGTERM` handlers (cleanly restoring previous handlers on exit) to terminate + reap child process groups, and finalizes **only** `runs[run_id]` (keeping `pid`, `host`, `updated_at`, `ttl_sec`) under run-ownership locking across shared `.devtool/state/` dirs without touching sibling live runs; also clean up pre-existing `S110` at `L294` if touched (`# noqa` or structured warning log).
- `tests/test_rsdh_heartbeat_quality.py` MUST import `scripts/estimate_heartbeat` lazily inside test function bodies (not at module top level) so V1 RED executes collected tests and exits `1` (`failed`) cleanly rather than failing collection with exit `2`.
- Keep `execute_provider` and `verify_polyglot_execution` signatures strictly backward-compatible for callers omitting `heartbeat_interval`.

## Definition of Done

- Scenarios RSDH-HP-02, RSDH-HP-03, RSDH-EC-02, RSDH-FR-02, and RSDH-FR-07 pass across unit, subprocess isolation, and `SIGTERM` reaping tests. (V2, V6)
- Existing polyglot Gate 4 and quality provider acceptance suites pass with zero regressions. (V3, V6)
- Ruff lint and mypy strict checks pass on `estimate_heartbeat.py` and `verify_polyglot_registry.py`. (V4, V5)
- `quality_check/SKILL.md` link and ToC checks remain valid on candidate commit. (Gate 5)

## Dependencies & Blockers

None.

Downstream dependents (blocked by Task 2): `task_03`, `task_07`.

## References & Rollback

- [Epic HLD](runtime_sync_and_dashboard_hardening.en.md), Module Contracts (§4.2).
- **Rollback**: Revert task commit; removes `scripts/estimate_heartbeat.py` and restores `verify_polyglot_registry.py` and `skills/quality_check/SKILL.md`.
