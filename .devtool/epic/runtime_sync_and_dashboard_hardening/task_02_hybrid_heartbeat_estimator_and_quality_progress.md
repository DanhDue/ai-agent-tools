---
id: "task_02_hybrid_heartbeat_estimator_and_quality_progress"
status: "todo"
priority: "high"
assignee: null
epic: "runtime_sync_and_dashboard_hardening"
dueDate: null
created: "2026-11-13T09:18:00Z"
modified: "2026-11-13T09:18:00Z"
completedAt: null
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
   - Evaluate deterministic additive formula (`base 10s + 45s*tasks + 10s*files + profile baseline {fast:20, pr:120, epic:210, release:270, full:270} + e2e bonus 90s`, clamping `0` tasks & `0` files with no quality profile to `< 60s`) into tiers:
     - `estimated_sec < 60` -> `"light"`, `recommended_interval_sec: null`
     - `60 <= estimated_sec <= 240` -> `"medium"`, `recommended_interval_sec: 180`
     - `estimated_sec > 240` -> `"heavy"`, `recommended_interval_sec: 240` (or `300` when `--has-e2e` or `epic`/`release`/`full`)
2. **Live Progress Streaming in `verify_polyglot_registry.py`**:
   - Upgrade `execute_provider` (`L142-L458`) and `verify_polyglot_execution` (`L459-L557`) to accept an optional `heartbeat_interval` parameter (default `15.0`, CLI flag `--heartbeat-interval` in `main` `L636-L726`).
   - Run capability subprocesses via `subprocess.Popen` redirecting combined stdout/stderr directly into `build/quality/<provider_id>/<cap_name>.log`.
   - Poll at `heartbeat_interval` ticks, emitting a concise zero-token progress line to `stderr` (`[quality_check] <i>/<n> <provider>:<cap> (<elapsed>s elapsed)`) and updating `.devtool/state/quality_active.json` atomically (`Atomic` JSON helper — local atomic helper fallback if `_state_envelope.py` is absent in older repos, using `scripts/_state_envelope.py` when present).
   - Wrap provider execution in `try ... finally` so passing, failing (`exit != 0`), or aborted runs always transition `quality_active.json` out of `"running"` into `"passed"`, `"failed"`, or `"aborted"` with `finished_at`.
3. **Document Estimator & Watchdog Workflow (`skills/quality_check/SKILL.md`)**:
   - Document running `python3 scripts/estimate_heartbeat.py --quality-profile <profile> --json` before long quality checks and monitoring live `[quality_check]` stderr output / `quality_active.json`.
4. Add `tests/test_rsdh_heartbeat_quality.py` covering `RSDH-HP-02`, `RSDH-HP-03`, `RSDH-EC-02`, and `RSDH-FR-02`.

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
- **Target Test Coverage Threshold**: 100% of estimator tier branches, `Popen` heartbeat loop, and `finally` state transitions (`passed`/`failed`/`aborted`).

### BDD SCENARIOS

Covers: RSDH-HP-02, RSDH-HP-03, RSDH-EC-02, RSDH-FR-02


```gherkin
Scenario: [RSDH-HP-02] [Tier A - Unit] Simple rule-based heartbeat estimator maps workloads across light, medium, and heavy cadence tiers

Given representative inputs covering a 1-task/1-file micro fix, a 2-task/5-file feature wave, a full polyglot quality run, and an E2E quality run
When scripts/estimate_heartbeat.py evaluates each input via CLI and Python API with --json
Then the micro fix returns tier "light" with recommended_interval_sec null, the feature wave returns tier "medium" with recommended_interval_sec 180, the full quality run returns tier "heavy" with 240, and the E2E run returns tier "heavy" with 300

Scenario: [RSDH-HP-03] [Tier C - Integration] Polyglot quality runner streams zero-token stderr progress and updates quality_active.json

Given a registered provider capability command that runs longer than the configured heartbeat interval
When verify_polyglot_registry.py executes the provider via Popen with a shortened test heartbeat interval and active devtool state directory
Then verify_polyglot_registry.py writes command output to build/quality/<provider>/<capability>.log while printing periodic "[quality_check]" progress lines to stderr
And .devtool/state/quality_active.json transitions from status "running" with step_index/step_total to final status "passed" upon completion

Scenario: [RSDH-EC-02] [Tier A - Unit] Heartbeat estimator clamps zero inputs and escalates E2E runs to 300 seconds

Given an invocation of scripts/estimate_heartbeat.py with --tasks-count 0 --files-count 0 and another with --quality-profile epic --has-e2e
When both evaluations run
Then the empty input produces tier "light" with recommended_interval_sec null
And the epic E2E run produces tier "heavy" with recommended_interval_sec 300

Scenario: [RSDH-FR-02] [Tier C - Integration] Quality verification finalizes quality_active.json on failing command or runtime error

Given a capability command in verify_polyglot_registry.py that exits non-zero with failing stdout/stderr
When verify_polyglot_registry.py runs and handles the failure inside try/finally
Then quality_active.json is finalized cleanly with status "failed" and non-null finished_at so no permanent "running" indicator remains
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_heartbeat_quality.py::test_rsdh_hp_03_live_stderr_and_quality_active` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_heartbeat_quality.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_polyglot_gate4.py && python3 -m unittest skills/quality_check/resources/scripts/test_quality_provider_acceptance.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/estimate_heartbeat.py skills/quality_check/resources/scripts/verify_polyglot_registry.py tests/test_rsdh_heartbeat_quality.py` | exit 0 | — |
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

- `scripts/estimate_heartbeat.py` is 100% deterministic (zero LLM/network calls) and maps discrete tiers: `< 60s -> light (null)`, `60..240s -> medium (180)`, `> 240s -> heavy (240 or 300 with --has-e2e or full/epic/release profile)`.
- `verify_polyglot_registry.py` streams capability stdout/stderr directly to `build/quality/<provider_id>/<cap_name>.log` via `subprocess.Popen`, emits `[quality_check] <i>/<n> <provider>:<cap> (<elapsed>s elapsed)` every `heartbeat_interval` (default `15.0s`), and finalizes `quality_active.json` in `try ... finally` across resolved shared `.devtool/state/` dirs without importing project-specific paths.
- Keep `execute_provider` and `verify_polyglot_execution` signatures strictly backward-compatible for callers omitting `heartbeat_interval`.

## Definition of Done

- Scenarios RSDH-HP-02, RSDH-HP-03, RSDH-EC-02, and RSDH-FR-02 pass across unit and subprocess capability tests. (V2, V6)
- Existing polyglot Gate 4 and quality provider acceptance suites pass with zero regressions. (V3, V6)
- Ruff lint and mypy strict checks pass on `estimate_heartbeat.py` and `verify_polyglot_registry.py`. (V4, V5)
- `quality_check/SKILL.md` link and ToC checks remain valid on candidate commit. (Gate 5)

## Dependencies & Blockers

None.

Downstream dependents (blocked by Task 2): `task_03`, `task_07`.

## References & Rollback

- [Epic HLD](runtime_sync_and_dashboard_hardening.en.md), Module Contracts (§4.2).
- **Rollback**: Revert task commit; removes `scripts/estimate_heartbeat.py` and restores `verify_polyglot_registry.py` and `skills/quality_check/SKILL.md`.
