---
id: "task_2_subprocess_dispatcher_and_headless_agy"
status: "todo"
priority: "high"
assignee: null
epic: "autonomous_lifecycle_runner"
dueDate: null
created: "2026-11-10T19:16:00Z"
modified: "2026-11-10T19:16:00Z"
completedAt: null
labels: ["lifecycle", "process-supervision", "dispatcher"]
order: "a2"
---

# Task 2: Subprocess Dispatcher and Headless agy Runner

Epic: [autonomous_lifecycle_runner](autonomous_lifecycle_runner.en.md)

## Requirement Analysis

Implement headless model dispatching and process supervision in `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`:
1. Implement `ModelDispatcher.dispatch` executing headless command `agy --print "<prompt>" --model <model> --effort <effort> --mode <mode>`.
2. Process isolation: spawn subprocesses with `start_new_session=True` so child processes run within a dedicated POSIX process group.
3. Timeout and termination fencing: supervisor timer triggers `os.killpg(pgid, signal.SIGTERM)`, awaits a 1.0s grace period, and escalates to `os.killpg(pgid, signal.SIGKILL)` if processes remain alive.
4. Auto Gate 3 order calculation: implement `LifecycleRunner.resolve_gate3_order` calling `compute_execution_order.py`, validating topological task order, auto-confirming Gate 3, and recording the execution order in `.devtool/GATE_LEDGER.md`.
5. Implementation loop: implement `LifecycleRunner.step_implementation` to loop through the resolved tasks in order, dispatch the Programmer headless subprocess for each task via stdin, capture per-task logs, sync task status, commit each task cleanly (`[AUTONOMOUS_LIFECYCLE_RUNNER] Execute <task_slug>`), and recover from crash or interruption via saved state (`ALR-ST-01`).
6. Implement unit tests in `tests/test_lifecycle_runner.py` covering `ALR-HP-02`, `ALR-EC-04`, `ALR-AR-01`, and `ALR-ST-01`.

## Files

Allowed files:
- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (new)
- `tests/test_lifecycle_runner.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/compute_execution_order.py` — topological sort implementation
- `scripts/resume_context.py` — gate approval recording
- `.devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md` — Module Contracts
- `.agents/quality/python-quality.json` — registered capabilities

## Design Rationale

Executing headless LLM sessions in isolated process groups (`start_new_session=True`) ensures that runaway child processes, compiler daemons, or spawned test runners are terminated cleanly when timeouts occur. Auto-confirming Gate 3 via `compute_execution_order.py` removes the interactive menu prompt while maintaining dependency safety. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`ModelDispatcher.dispatch`, `LifecycleRunner.resolve_gate3_order`).
- **Downstream callers**: Stage 3 implementation loop and review dispatcher.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: 100% of dispatch and process termination paths.

### BDD SCENARIOS

Covers: ALR-HP-02, ALR-EC-04, ALR-AR-01, ALR-ST-01

```gherkin
Scenario: [ALR-HP-02] [Tier C - Integration] Headless dispatch of AI Programmer with Gemini 3.8 Flash High

Given a pending implementation task file in .devtool/features/task_1_pipeline_state_machine_and_probing.md
When lifecycle_runner.py dispatches the AI Programmer for task execution
Then the dispatched command executes "agy" with "--model gemini-3.8-flash"
And the command specifies "--effort high" and "--mode auto"
And the execution runs inside the isolated git worktree with dedicated process group supervision

Scenario: [ALR-EC-04] [Tier C - Integration] Gate 3 execution order auto-confirmed via compute_execution_order

Given multiple task files with explicit dependency links in .devtool/features/
When the runner enters Stage 3 Implementation
Then compute_execution_order.py is executed to resolve the topological execution sequence
And the resulting task sequence is auto-confirmed and recorded in .devtool/GATE_LEDGER.md under Gate 3
And task execution begins immediately without presenting an interactive prompt

Scenario: [ALR-AR-01] [Tier C - Integration] Subprocess group process isolation and clean SIGTERM termination on timeout

Given a headless agy programmer process exceeds the configured timeout limit
When the supervisor timer expires in ModelDispatcher
Then SIGTERM is broadcast to the entire subprocess group via os.killpg
And after a 1.0s grace period, SIGKILL is escalated if the child processes remain alive
And the runner records a timeout failure in the pipeline state without leaving orphaned processes

Scenario: [ALR-ST-01] [Tier C - Integration] State persistence and resumption from crash in intermediate stage

Given the runner is interrupted by SIGINT during Stage 3 task execution
When lifecycle_runner.py is invoked again with --resume
Then the runner reads .devtool/state/<epic>.pipeline.json
And the runner recovers the active stage "implementation", completed task list, and current round
And execution resumes from the exact interrupted task without re-running completed tasks
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest tests/test_lifecycle_runner.py -k test_alr_hp_02` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest tests/test_lifecycle_runner.py -k test_alr_hp_02` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest tests/test_lifecycle_runner.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_lifecycle_runner.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_lifecycle_runner.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml tests/test_lifecycle_runner.py` | exit 0; results build/test-results/task_2.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `compute_execution_order.py` detects a dependency cycle among task files.

## Decisions Already Made

- The Programmer is dispatched with `--model <model>` (default: `gemini-3.8-flash`), `--effort high`, and `--mode auto` inside the worktree directory, with prompts piped via stdin.
- `subprocess.Popen` is launched with `start_new_session=True` so `pgid = p.pid` provides the process group ID. On timeout or exit, `os.killpg(pgid, signal.SIGTERM)` is called (handling `ProcessLookupError` gracefully) followed by SIGKILL escalation if needed.
- Gate 3 auto-confirmation runs `compute_execution_order.py`, parses the sequential order from the `Flattened sequential order:` output block (or imports `load_tasks`), fails on non-zero exit or manual review notes, and records Gate 3 approval via `resume_context.py --gate 3 --epic <slug> --approved "<order>" --by lifecycle_runner`.
- `step_implementation` iterates sequentially over tasks, captures stdout/stderr to task log files, updates task status to done, and commits changes per task (`[AUTONOMOUS_LIFECYCLE_RUNNER] Execute <task_slug>`).

## Definition of Done

- Scenarios ALR-HP-02, ALR-EC-04, ALR-AR-01, ALR-ST-01 are covered and pass in the test suite. (V2, V3, V6)
- Python quality checks (lint and type check) pass cleanly. (V4, V5)
- Process termination leaves zero orphan processes upon timeout. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 1](task_1_pipeline_state_machine_and_probing.md).
- Blocks [Task 3](task_3_principal_review_automation_and_checkpoint.md), [Task 4](task_4_cross_model_review_fix_plan_loop.md), and [Task 5](task_5_orchestrator_cli_and_governance_rules.md).

## References & Rollback

- [Epic HLD](autonomous_lifecycle_runner.en.md), Module Contracts.
- **Rollback**: Revert task commit; dispatcher changes are removed.
