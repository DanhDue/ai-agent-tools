---
id: "task_04_lifecycle_runner_programmer_config_and_pool_isolation"
status: "todo"
priority: "high"
assignee: null
epic: "token_throttling_optimization"
dueDate: null
created: "2026-11-13T02:30:00Z"
modified: "2026-11-13T02:30:00Z"
completedAt: null
labels: ["lifecycle-runner", "worker-pool", "config", "token-optimization"]
order: "a4"
---

# Task 4: Config-Driven Programmer Persona, Pool Dispatch, and Runner Optimization

Epic: [token_throttling_optimization](token_throttling_optimization.en.md)

## Requirement Analysis

Upgrade `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` and `skills/dev-implementation/resources/scripts/manage_worker_pool.py` to enforce clean per-task session isolation (`Rule 4`), path-only Zero-Fluff worker prompts (`Rule 3`, `Rule 5`), config-driven Gemini 4 Hydrogen Role 2.3 resolution, Gate 4 25-line failure tailing (`Rule 2`), concurrent wave dispatch, and streamlined cross-model code-fix execution:
1. **Config-Driven Role 2.3 Model & Effort Precedence (`RunnerConfig` + `main`)**:
   - Replace hardcoded `"gemini-3.8-flash"` defaults with `"gemini-4-hydrogen-xhigh"` and `"xhigh"` fallback.
   - Add `normalize_agy_effort(raw: str) -> str` mapping `"extra"`, `"extra-high"`, `"extra_high"`, and `"xhigh"` (case-insensitive) to `"xhigh"`.
   - Implement `RunnerConfig.resolve_programmer_model(self, root: Path | None = None) -> str` and `RunnerConfig.resolve_programmer_effort(self, root: Path | None = None) -> str` following:
     `CLI (--programmer-model / --programmer-effort) -> Runner --config JSON -> .devtool/review_config.json["providers"]["programmer"] -> env (AGY_PROGRAMMER_MODEL / AGY_PROGRAMMER_EFFORT) -> fallback ("gemini-4-hydrogen-xhigh", "xhigh")`.
   - Update `main()` so `argparse` uses `default=None` for `--programmer-model` and add `--programmer-effort` (`default=None`), ensuring CLI overrides config only when explicitly passed.
   - Update startup `probe_model()` and `_execute_single_task()` / `_apply_code_fixes()` to pass resolved model and normalized `--effort` to `ModelDispatcher.dispatch()`.
2. **Parallel Worker Pool Execution & Path-Only Zero-Fluff Prompts**:
   - Refactor `step_implementation()` to consume `compute_execution_order.py --parallel` waves and execute disjoint tasks concurrently inside 2-slot worktrees via `manage_worker_pool.py` (`init_slots`, `sync_slot`, `merge_slot`, `cleanup_slots`).
   - Refactor `_execute_single_task()` so each task starts in a clean session context passing ONLY the task file path, target file paths + line ranges, and the Zero-Fluff output cap (no inlined task markdown or large source bodies).
   - Ensure `run_gate4()` invokes `--compact` on polyglot/Gate 4 commands where available and uses `_tail_lines(output, 25)` on failures in both `run_gate4()` and `run_intermediate_check()`.
3. **Streamlined Cross-Model Fix Loop & Real Executive Report**:
   - Update `step_cross_model_review()`: when verified findings are pure code fixes with zero `shared-contracts/` or architecture ambiguity (via `_has_domain_or_critical_conflict`), route directly to `_apply_code_fixes()` without extra `_draft_fix_plan()` / `evaluate_programmer_fix_plan()` LLM round-trips; preserve Role 2.2 escalation whenever `shared-contracts/` or architecture ambiguity exists.
   - Replace placeholder strings in `render_final_executive_report()` with parsed Top 3 Highest-Risk Findings and candidate SHAs read from `review_results.md` / `principal_review.md`.
4. Update `tests/test_lifecycle_runner.py` (including RED/GREEN coverage for `TTO-HP-04`, `TTO-HP-07`, `TTO-EC-04`, `TTO-ST-04`, `TTO-AR-01`, `TTO-FR-03` alongside updated model expectations).

## Files

Allowed files:
- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`
- `skills/dev-implementation/resources/scripts/manage_worker_pool.py`
- `tests/test_lifecycle_runner.py`

Read-only context:
- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Module Contracts (§4)
- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios
- `skills/dev-implementation/resources/scripts/run_external_review.py` — Config loader & upgrade helper
- `skills/dev-implementation/resources/scripts/compute_execution_order.py` — Topological parallel wave generator

## Design Rationale

Centralizing Role 2.3 resolution into `RunnerConfig` mirrors `resolve_assistant_model` while upgrading the default coding engine to `gemini-4-hydrogen-xhigh` (`--effort xhigh`) with zero hardcoded scattered strings. Running disjoint DAG waves concurrently across isolated pool slots with path-only prompts stops context snowballing across tasks while eliminating sequential wait time. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`: `RunnerConfig` (L44-L80), `ModelDispatcher` (L119-L205), `LifecycleRunner._execute_single_task` (L432-L509), `LifecycleRunner.step_implementation` (L884-L908), `LifecycleRunner.run_gate4` (L910-L1049), `LifecycleRunner.run_intermediate_check` (L1051-L1078), `LifecycleRunner.step_cross_model_review` (L1220-L1336), `LifecycleRunner.render_final_executive_report` (L1338-L1362), `main` (L1365-L1414), new `normalize_agy_effort`, new `_tail_lines`
  - `skills/dev-implementation/resources/scripts/manage_worker_pool.py`: `init_slots` (L68-L106), `sync_slot` (L109-L119), `merge_slot` (L122-L136)
  - `tests/test_lifecycle_runner.py`: unit and integration tests covering `TTO-HP-04`, `TTO-HP-07`, `TTO-EC-04`, `TTO-ST-04`, `TTO-AR-01`, `TTO-FR-03`
- **Downstream Callers**: `skills/dev-lifecycle/SKILL.md`, `skills/dev-lifecycle/references/autonomous-mode.md`, `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of config precedence branches, effort alias normalization, worker pool wave dispatch, and Role 2.2 escalation paths.

### BDD SCENARIOS

Covers: TTO-HP-04, TTO-HP-07, TTO-EC-04, TTO-ST-04, TTO-AR-01, TTO-FR-03

```gherkin
Scenario: [TTO-HP-04] [Tier A - Unit] RunnerConfig resolves Role 2.3 programmer model and effort using config precedence

Given a .devtool/review_config.json defining providers.programmer.model as "gemini-4-hydrogen-xhigh" and thinking_level as "extra"
And AGY_PROGRAMMER_MODEL environment override is unset
When lifecycle_runner.RunnerConfig resolves the programmer model and effort with no CLI flag supplied
Then resolve_programmer_model returns "gemini-4-hydrogen-xhigh" and resolve_programmer_effort returns "xhigh"
And supplying --programmer-model "gemini-4-pro-high" via CLI overrides both .devtool/review_config.json and environment variables

Scenario: [TTO-HP-07] [Tier C - Integration] Streamlined cross-model review fast-tracks clean code fixes and renders actual Executive Report findings

Given a cross-model review Round 1 verdict of CHANGES_REQUIRED containing only verified code bugs with zero shared-contracts conflicts
When lifecycle_runner.step_cross_model_review executes one remediation iteration followed by convergence
Then unambiguous code fixes bypass _draft_fix_plan and evaluate_programmer_fix_plan and route directly to _apply_code_fixes
And render_final_executive_report populates the Top 3 Highest-Risk Findings table directly from parsed review_results.md and principal_review.md entries rather than placeholder strings

Scenario: [TTO-EC-04] [Tier A - Unit] Programmer effort normalization maps "extra" aliases to xhigh

Given raw effort values "extra", "EXTRA", "extra-high", "extra_high", and "xhigh"
When lifecycle_runner.normalize_agy_effort normalizes each configured thinking level
Then every variant returns the canonical flag value "xhigh"
And invoking the agy command builder passes "--effort", "xhigh" on the command line

Scenario: [TTO-ST-04] [Tier C - Integration] Cross-model review escalates to Role 2.2 when shared-contracts or architecture ambiguity arises

Given a cross-model review finding in Round 1 referencing shared-contracts/api_contract.md or an ambiguous architectural state transition
When lifecycle_runner.step_cross_model_review triages the round findings
Then fast-path auto-fix is NOT taken and either CRITICAL_CONFLICT halts immediately or fix_plan_round1.md is routed through Role 2.2 evaluation before any edit occurs

Scenario: [TTO-AR-01] [Tier C - Integration] Parallel wave dispatch executes independent tasks concurrently with path-only Zero-Fluff prompts

Given an epic DAG containing two disjoint Wave 1 tasks (no mutual blocker dependency) and one Wave 2 task blocked by both
And an isolated worker pool initialized by manage_worker_pool.py
When lifecycle_runner.step_implementation executes the implementation phase using a thread-safe recording mock dispatcher
Then both Wave 1 tasks run concurrently inside distinct pool slots before Wave 2 begins
And each task prompt omits inlined task markdown bodies, injects only target file paths and line ranges, and includes the Zero-Fluff output cap

Scenario: [TTO-FR-03] [Tier A - Unit] lifecycle_runner._tail_lines bounds Gate 4 and intermediate check failure summaries to 25 lines

Given a subprocess failure from run_gate4 or run_intermediate_check emitting 120 traceback lines
When lifecycle_runner formats the failure message via _tail_lines(output, 25)
Then the returned failure excerpt contains at most 25 lines terminating at the final failing assertion summary
And the exception or state message propagated to the next step never exceeds 25 lines of traceback
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_lifecycle_runner.py::test_tto_hp_04_runner_config_precedence` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_lifecycle_runner.py::test_tto_hp_04_runner_config_precedence` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_lifecycle_runner.py skills/dev-implementation/resources/scripts/test_manage_worker_pool.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/dev-lifecycle/resources/scripts/lifecycle_runner.py skills/dev-implementation/resources/scripts/manage_worker_pool.py tests/test_lifecycle_runner.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-lifecycle/resources/scripts/lifecycle_runner.py skills/dev-implementation/resources/scripts/manage_worker_pool.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_4.xml tests/test_lifecycle_runner.py` | exit 0; results build/test-results/task_4.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `normalize_agy_effort(raw: str) -> str` maps `{"extra", "extra-high", "extra_high", "xhigh"}` -> `"xhigh"`, lowercasing and trimming input; default fallback pair is `("gemini-4-hydrogen-xhigh", "xhigh")`.
- `RunnerConfig.resolve_programmer_model` and `resolve_programmer_effort` follow: `CLI -> Runner --config -> .devtool/review_config.json["providers"]["programmer"] -> env (AGY_PROGRAMMER_MODEL / AGY_PROGRAMMER_EFFORT) -> fallback`.
- `main()` sets `default=None` on `--programmer-model` and `--programmer-effort` so `.devtool/review_config.json` controls defaults unless explicitly overridden at invocation.
- `LifecycleRunner.step_implementation` dispatches independent parallel batches concurrently via `manage_worker_pool.py` slots with clean per-task prompts referencing file paths, line ranges, and Zero-Fluff output cap.
- `LifecycleRunner._tail_lines(text: str, limit: int = 25) -> str` caps Gate 4 and intermediate failure summaries at `25` lines.
- `step_cross_model_review` skips `_draft_fix_plan` / `evaluate_programmer_fix_plan` strictly when findings contain no `shared-contracts/` or architectural ambiguity, preserving `CRITICAL_CONFLICT` halts and Role 2.2 escalation otherwise.

## Definition of Done

- Scenarios TTO-HP-04, TTO-HP-07, TTO-EC-04, TTO-ST-04, TTO-AR-01, and TTO-FR-03 pass reliably. (V2, V3, V6)
- Worker pool regression suite passes cleanly with zero concurrency or cleanup failures. (V3)
- Python ruff lint and mypy strict type checks pass cleanly. (V4, V5)
- Config precedence and clean executive summary verified visually at completion review. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 1](task_01_diff_only_external_review_and_transcript_isolation.md), [Task 2](task_02_silent_gate4_and_truncated_test_runners.md), and [Task 3](task_03_option_a_bilingual_and_surgical_contract_guards.md).
Blocks [Task 6](task_06_integration_and_regression_verification.md).

## References & Rollback

- [Epic HLD](token_throttling_optimization.en.md), Module Contracts (§4).
- **Rollback**: Revert task commit; restores prior `lifecycle_runner.py`, `manage_worker_pool.py`, and `tests/test_lifecycle_runner.py`.
