---
id: "task_1_pipeline_state_machine_and_probing"
status: "done"
priority: "high"
assignee: null
epic: "autonomous_lifecycle_runner"
dueDate: null
created: "2026-11-10T19:16:00Z"
modified: "2026-11-10T23:54:14Z"
completedAt: "2026-11-10T23:54:14Z"
labels: ["lifecycle", "state-machine", "persistence"]
order: "a1"
---

# Task 1: Pipeline State Machine, Persistence, and Model Probing

Epic: [autonomous_lifecycle_runner](autonomous_lifecycle_runner.en.md)

## Requirement Analysis

Implement the foundational state machine and persistence infrastructure for `lifecycle_runner.py`:
1. Core enumerations and dataclasses: `StageName`, `FixPlanVerdict`, `RunnerConfig`, and `PipelineState`.
2. Atomic JSON persistence in `.devtool/state/<epic>.pipeline.json` using atomic temporary file renaming and file locking (`fcntl.flock`).
3. Crash recovery logic: `LifecycleRunner.load_or_init_state` restores active stage, round counters, last commit SHA, and completed task lists from existing state files.
4. Gate Ledger synchronization: updates `.devtool/GATE_LEDGER.md` with timestamps, candidate SHAs, and autonomous verification entries.
5. Model capability prober: `ModelDispatcher.probe_model` executes a fast, minimal headless invocation to verify that the CLI accepts the configured model identifiers (`gemini-3.8-flash` and Assistant model) before initializing state.
6. Create unit test suite `tests/test_lifecycle_runner.py` verifying state recovery, probing, and persistence.
7. Review model priority support: update `load_review_config` in `run_external_review.py` to load and persist custom `provider_priority` lists, and update `select_provider_by_quota` to accept custom priority orders, enabling the 4 selectable model priority options from Gate 2 with default `Claude -> Codex -> Kiro -> Argon`.

## Files

Allowed files:
- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (new)
- `tests/test_lifecycle_runner.py` (new)
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`

Read-only context:
- `scripts/resume_context.py` — state persistence patterns, gate hydration, and Gate Ledger formatting
- `.devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md` — Module Contracts
- `.agents/quality/python-quality.json` — registered capabilities

## Design Rationale

Atomic writes via temporary files combined with `fcntl.flock` prevent JSON corruption when processes are aborted or interrupted. The startup probe guarantees that typos or deprecated model strings are caught instantly prior to executing any task or modifying any repository state. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`StageName`, `FixPlanVerdict`, `RunnerConfig`, `PipelineState`, `ModelDispatcher.probe_model`, `LifecycleRunner.save_state`, `LifecycleRunner.load_or_init_state`).
- **Downstream callers**: Tasks 2 through 5 will build directly on these contracts.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: 100% branch coverage on state serialization and error handling.

### BDD SCENARIOS

Covers: ALR-ST-03, ALR-AR-02

```gherkin
Scenario: [ALR-ST-03] [Tier C - Integration] Probing verifies model capabilities before state initialization

Given an invalid or deprecated model string specified in configuration
When lifecycle_runner.py initiates the startup capability probe
Then ModelDispatcher.probe_model executes a minimal headless agy call
And upon non-zero exit or error, the runner aborts before writing pipeline state or modifying files
And a descriptive error message indicating the rejected model is printed to stderr

Scenario: [ALR-AR-02] [Tier C - Integration] File locking during state updates prevents concurrency corruption

Given concurrent processes or rapid consecutive state transitions
When LifecycleRunner writes updates to .devtool/state/<epic>.pipeline.json
Then state updates are serialized using file locking and atomic temporary file replacement (.tmp rename)
And the pipeline state file remains valid and uncorrupted JSON at all times
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest tests/test_lifecycle_runner.py -k test_alr_st_03` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest tests/test_lifecycle_runner.py -k test_alr_st_03` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest tests/test_lifecycle_runner.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_lifecycle_runner.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_lifecycle_runner.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_1.xml tests/test_lifecycle_runner.py` | exit 0; results build/test-results/task_1.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Atomic state file serialization fails on POSIX file systems.

## Decisions Already Made

- `StageName` enum: `initialized`, `principal_review`, `awaiting_principal_confirmation`, `implementation`, `cross_model_review`, `awaiting_finish`, `completed`, `halted`.
- `FixPlanVerdict` enum: `APPROVED`, `ADJUSTED`, `CRITICAL_CONFLICT`.
- `RunnerConfig` defaults: `programmer_model="gemini-3.8-flash"`, `programmer_effort="high"`, `assistant_model=None` (precedence: CLI `--assistant-model` -> `.devtool/review_config.json` `providers.assistant.model` -> active profile model -> fallback `claude-sonnet-5-5-high`), `assistant_effort="high"`, `timeout_seconds=1800`, `max_review_rounds=3`.
- `run_external_review.py` loads and respects `provider_priority` from `.devtool/review_config.json` and supports custom priority lists matching the 4 Gate 2 options.
- `PipelineState` tracks `epic_slug`, `active_stage`, `principal_round`, `cross_model_round`, `last_commit_sha`, `last_verdict`, `halt_reason`, `last_error`, `task_order`, and `completed_tasks`.
- State is serialized to `.devtool/state/<epic>.pipeline.json` via `.tmp` rename with `fcntl.flock(fd, fcntl.LOCK_EX)`.
- Gate updates execute via `resume_context.py --gate <n> --epic <slug> --approved "<text>" --by lifecycle_runner` to guarantee synchronization with `gate_ledger.jsonl`.

## Definition of Done

- Scenarios ALR-ST-03, ALR-AR-02 are covered and pass in the test suite. (V2, V3, V6)
- Python quality checks (lint and type check) pass cleanly. (V4, V5)
- State persistence and recovery work reliably across interrupted sessions. (Gate 5)

## Dependencies & Blockers

None. Blocks [Task 2](task_2_subprocess_dispatcher_and_headless_agy.md), [Task 3](task_3_principal_review_automation_and_checkpoint.md), [Task 4](task_4_cross_model_review_fix_plan_loop.md), and [Task 5](task_5_orchestrator_cli_and_governance_rules.md).

## References & Rollback

- [Epic HLD](autonomous_lifecycle_runner.en.md), Module Contracts.
- **Rollback**: Revert task commit; deletes `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` and `tests/test_lifecycle_runner.py`.
