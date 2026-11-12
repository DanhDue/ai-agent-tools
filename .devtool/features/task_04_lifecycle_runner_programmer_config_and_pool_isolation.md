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
   - Implement `RunnerConfig.resolve_programmer_model(self, root: Path | None = None) -> str` and `RunnerConfig.resolve_programmer_effort(self, root: Path | None = None) -> str` applying the shared legacy alias upgrade (`{"gemini-3.8-flash", "gemini-3.8-flash-high"}` -> `("gemini-4-hydrogen-xhigh", "xhigh")`, matching `run_external_review.load_review_config` and `resume_context.emit_handoff_prompt` while leaving git-tracked `.devtool/review_config.json` untouched on disk) using precedence:
     `CLI (--programmer-model / --programmer-effort) -> Runner --config JSON -> .devtool/review_config.json["providers"]["programmer"] -> env (AGY_PROGRAMMER_MODEL / AGY_PROGRAMMER_EFFORT) -> fallback ("gemini-4-hydrogen-xhigh", "xhigh")`.
   - Update `main()` so `argparse` uses `default=None` for `--programmer-model` and add `--programmer-effort` (`default=None`), ensuring CLI overrides config only when explicitly passed.
   - Update startup `probe_model()` and `_execute_single_task()` / `_apply_code_fixes()` to pass resolved model and normalized `--effort` to `ModelDispatcher.dispatch()`.
2. **Parallel Worker Pool Execution & Path-Only Zero-Fluff Prompts**:
   - Explicitly separate `repo_root` (parent repository holding `.worktrees/<epic_dir>`) from `epic_worktree_root` and `epic_dir` from `epic_slug` across `step_implementation()` and `manage_worker_pool.py` so `merge_slot()` never nests `.worktrees/<epic_dir>/.worktrees/<epic_dir>`; bind each concurrent worker `ModelDispatcher` to its isolated `slot_path`, require EVERY post-dispatch subprocess in `_execute_single_task()` (`sync_task_status.py` L475-L489 and `git status --porcelain`/`git add`/`git commit` L492-L507) to take the owning `slot_path` as `cwd`, commit per slot, integrate strictly via serialized `merge_slot()` with rollback/error recovery, and test executing from an actual epic worktree asserting each slot commit contains only its own paths alongside conflict/failure recovery.
   - Refactor `_execute_single_task()` so each task starts in a clean session context passing ONLY the task file path, target file paths + line ranges, an explicit `"do not invoke d3nexus:task-observer"` instruction, and the Zero-Fluff output cap (scoping prose omission strictly to discretionary narration so mandatory verdicts, status tokens, findings tables, and structured gate contracts remain intact).
   - Pass `--quiet` to `["bash", str(verify_script), "--quiet"]` in `run_gate4()` (`L1023-L1035`) and wrap ALL six `err = ...stderr.strip() or ...stdout.strip()` failure branches in `run_gate4()` (L930, L951, L972, L993, L1020, L1034) plus `run_intermediate_check()` (L1076) in `_tail_lines(..., 25)`.
3. **Streamlined Cross-Model Fix Loop & Real Executive Report**:
   - Update `step_cross_model_review()`: require an explicit, source-grounded classification confirming every open finding is an unambiguous code defect before bypassing Role 2.2; route any unknown, `"Debatable:"`, `"ambiguous architectural state transition"`, or `shared-contracts/` finding through Role 2.2 `_draft_fix_plan()` + `evaluate_programmer_fix_plan()` (or halt cleanly on `CRITICAL_CONFLICT`), and cover negative classification paths with unit tests.
   - Define an explicit input and success contract on `_apply_code_fixes(round_num, findings=..., review_artifact=..., plan_text=...) -> bool`: inject verified findings and design anchors into the worker prompt, verify BOTH `dispatcher.dispatch()` return code AND scoped-test pass before returning `True`, return `False` on dispatch or verification failure, and prohibit recording `"fixed"` decisions or advancing rounds when `_apply_code_fixes()` returns `False`.
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
  - `tests/test_lifecycle_runner.py`: `TestLifecycleRunner_Integration` (L29-L629), unit and integration tests covering `TTO-HP-04`, `TTO-HP-07`, `TTO-EC-04`, `TTO-ST-04`, `TTO-AR-01`, `TTO-FR-03` plus negative ambiguity and worktree merge recovery cases
- **Downstream Callers**: `skills/dev-lifecycle/SKILL.md`, `skills/dev-lifecycle/references/autonomous-mode.md`, `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of config precedence branches, effort alias normalization, worker pool wave dispatch, and Role 2.2 escalation paths.

### BDD SCENARIOS

Covers: TTO-HP-04, TTO-HP-07, TTO-EC-04, TTO-ST-04, TTO-AR-01, TTO-FR-03

```gherkin
Scenario: [TTO-HP-04] [Tier A - Unit] RunnerConfig resolves Role 2.3 programmer model and effort using config precedence

Given a .devtool/review_config.json defining providers.programmer.model as "gemini-4-hydrogen-xhigh" and thinking_level as "extra" (or legacy "gemini-3.8-flash-high" on disk)
And AGY_PROGRAMMER_MODEL environment override is unset
When lifecycle_runner.RunnerConfig resolves the programmer model and effort or dispatches agy with no CLI flag supplied
Then resolve_programmer_model returns "gemini-4-hydrogen-xhigh", resolve_programmer_effort returns "xhigh", and dispatched commands receive "--model gemini-4-hydrogen-xhigh --effort xhigh" via the shared legacy alias map
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
Then both Wave 1 tasks run concurrently inside distinct pool slots with status sync and git commits running inside cwd=slot_path so each slot commit contains only its owning task paths before serialized merge_slot integration
And each task prompt omits inlined task markdown bodies, forbids d3nexus:task-observer, injects only target file paths and line ranges, and includes the Zero-Fluff output cap

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
- `RunnerConfig.resolve_programmer_model` and `resolve_programmer_effort` follow: `CLI -> Runner --config -> .devtool/review_config.json["providers"]["programmer"] -> env (AGY_PROGRAMMER_MODEL / AGY_PROGRAMMER_EFFORT) -> fallback`, applying the shared legacy alias map (`{"gemini-3.8-flash", "gemini-3.8-flash-high"}` -> `("gemini-4-hydrogen-xhigh", "xhigh")`) consistently regardless of whether `load_review_config()` persists tracked files on disk.
- `main()` sets `default=None` on `--programmer-model` and `--programmer-effort` so `.devtool/review_config.json` controls defaults unless explicitly overridden at invocation.
- `LifecycleRunner` explicitly distinguishes `repo_root` vs `epic_worktree_root` and `epic_dir` vs `epic_slug` for `manage_worker_pool.py` `merge_slot()`, binds each parallel worker `ModelDispatcher` and all `_execute_single_task()` post-dispatch subprocesses (`sync_task_status.py`, `git status`/`git add`/`git commit`) to `cwd=slot_path`, serializes `merge_slot()` under lock with failure recovery, and executes clean per-task prompts referencing file paths, line ranges, `"do not invoke d3nexus:task-observer"`, and discretionary-narration Zero-Fluff output cap (preserving mandatory Verdicts, Findings, and status tokens).
- `run_gate4()` passes `--quiet` to `bash scripts/verify.sh` (`L1023-L1035`) and `LifecycleRunner._tail_lines(text: str, limit: int = 25) -> str` wraps all six `run_gate4()` error branches (L930, L951, L972, L993, L1020, L1034) plus `run_intermediate_check()` (L1076) at `25` lines.
- `step_cross_model_review()` only bypasses `_draft_fix_plan` / `evaluate_programmer_fix_plan` when every verified finding is explicitly classified via source/severity/category check as an unambiguous code defect; unknown, `"Debatable:"`, ambiguous architectural transitions, or `shared-contracts/` conflicts halt with `CRITICAL_CONFLICT` or route through Role 2.2. `_apply_code_fixes()` checks both dispatcher exit status and scoped tests and never records `"fixed"` on failure.

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
