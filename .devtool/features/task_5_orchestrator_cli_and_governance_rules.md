---
id: "task_5_orchestrator_cli_and_governance_rules"
status: "todo"
priority: "high"
assignee: null
epic: "autonomous_lifecycle_runner"
dueDate: null
created: "2026-11-10T19:16:00Z"
modified: "2026-11-10T19:16:00Z"
completedAt: null
labels: ["lifecycle", "orchestration", "governance", "documentation"]
order: "a5"
---

# Task 5: End-to-End Orchestrator, CLI Integration, and Governance Rules

Epic: [autonomous_lifecycle_runner](autonomous_lifecycle_runner.en.md)

## Requirement Analysis

Complete the end-to-end autonomous orchestrator CLI and update system governance documentation across the codebase:
1. Complete CLI entry point `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`:
   - Argument parsing: `--epic <slug>`, `--resume`, `--config <path>`, `--reset-stage <stage>`, `--confirm-fixes`, `--reject-fixes`, `--assistant-model <model>`, `--programmer-model <model>`, and `--dry-run`.
   - Complete state machine driving: `INITIALIZED` -> `PRINCIPAL_REVIEW` -> `AWAITING_PRINCIPAL_CONFIRMATION` -> `IMPLEMENTATION` -> `CROSS_MODEL_REVIEW` -> `AWAITING_FINISH`.
   - Max round circuit breaker (`ALR-FR-03`): triggers `CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)` when Round 3 finishes with unresolved Critical findings.
   - Final executive report display: renders markdown summary of the entire review lifecycle across all rounds, synthesizing the Top 3 Highest-Risk Findings from across all rounds, displaying their resolution and Gate 4 verification, and halting cleanly only at this final round to prompt the Human Architect for next actions (proceed to /finishing-a-development-branch to merge to local base branch, or other actions).
2. Update governance rules, skills, and test suites:
   - `rules/CRITICAL_RULES.md`: update Sections 5, 6, and 8.2 to document autonomous review execution, auto Gate 3 confirmation, Assistant fix plan review, and autonomous mode role coordination.
   - `skills/dev-lifecycle/SKILL.md`: document `/dev-lifecycle --autonomous` and `lifecycle_runner.py` invocation.
   - `skills/dev-lifecycle/references/autonomous-mode.md`: create reference guide documenting CLI flags, state machine stages, circuit breakers, and actor responsibilities.
   - `skills/dev-implementation/SKILL.md`: document headless Programmer execution (`--model <model>` default `gemini-3.8-flash --effort high --mode auto`).
   - `skills/principal-review/SKILL.md`: document auto-triage and human fix confirmation checkpoint.
   - `skills/cross-model-review/SKILL.md`: document fix plan evaluation loop (`fix_plan_round<N>.md` with `APPROVED`/`ADJUSTED`/`CRITICAL_CONFLICT`).
   - `docs/lifecycles.en.md` and `docs/lifecycles.vi.md`: update bilingual lifecycle overviews with autonomous pipeline flow.
   - `scripts/verify.sh`: register `lifecycle-runner` in `SUITES` dictionary to execute `tests/test_lifecycle_runner.py`.
3. Verify all unit and integration tests in `tests/test_lifecycle_runner.py` and run full test suites.

## Files

Allowed files:
- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (new)
- `tests/test_lifecycle_runner.py` (new)
- `rules/CRITICAL_RULES.md`
- `skills/dev-lifecycle/SKILL.md`
- `skills/dev-lifecycle/references/autonomous-mode.md` (new)
- `skills/dev-implementation/SKILL.md`
- `skills/principal-review/SKILL.md`
- `skills/cross-model-review/SKILL.md`
- `docs/lifecycles.en.md`
- `docs/lifecycles.vi.md`
- `scripts/verify.sh`

Read-only context:
- `scripts/resume_context.py`
- `.devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md` — Module Contracts
- `.agents/quality/python-quality.json` — registered capabilities

## Design Rationale

Updating the governance rules and skill documentation ensures that all AI agent runtimes (Claude Code, Antigravity IDE, Cursor, Codex) operate with clear behavioral boundaries: interactive mode remains default and untouched, while autonomous mode follows strict 3-actor protocol with hard circuit breakers. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:writing-skills`, `d3nexus:doc_quality_check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `lifecycle_runner.py` main CLI, `CRITICAL_RULES.md` Sections 5 & 6, runtime skill markdown files.
- **Downstream callers**: Developers using `/dev-lifecycle --autonomous` or calling `lifecycle_runner.py`.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: 100% end-to-end integration flow coverage.

### BDD SCENARIOS

Covers: ALR-HP-01, ALR-FR-03, ALR-ST-02

```gherkin
Scenario: [ALR-HP-01] [Tier C - Integration] Complete autonomous pipeline executes from handoff to final executive report

Given an epic with approved Gate 1 spec and Gate 2 task breakdown in a git worktree
And configured runner models in .devtool/review_config.json
When lifecycle_runner.py runs with --epic autonomous_lifecycle_runner
Then the runner executes Principal Review, advances through Stage 3 implementation, and completes Cross-Model Review without intermediate menu pauses
And only at the final round after convergence and Gate 4 PASS, the runner renders the executive summary report synthesizing the Top 3 Highest-Risk Findings across all review rounds
And the runner halts cleanly, presenting the prompt for /finishing-a-development-branch (merge to base branch or other actions) to the Human Architect

Scenario: [ALR-FR-03] [Tier C - Integration] Circuit Breaker halts on max rounds exhaustion with Critical remaining

Given Cross-Model Review reaches Round 3 with at least 1 unresolved Critical finding
When evaluate_circuit_breakers checks the round counter and severity counts
Then the runner triggers CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)
And the runner halts without launching a 4th round, outputting the Top 3 Highest-Risk Findings

Scenario: [ALR-ST-02] [Tier C - Integration] Gate Ledger synchronization on autonomous state transitions

Given the pipeline progresses autonomously through Stage 2 and Stage 3
When each gate milestone (Gate 3 and Gate 4) is achieved
Then .devtool/GATE_LEDGER.md is updated with the timestamp, candidate SHA, and auto-approval metadata
And Gate 5 candidate readiness is recorded in .devtool/state/<epic>.pipeline.json awaiting explicit human finish sign-off
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest tests/test_lifecycle_runner.py -k test_alr_hp_01` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest tests/test_lifecycle_runner.py -k test_alr_hp_01` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest tests/test_lifecycle_runner.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_lifecycle_runner.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_lifecycle_runner.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/autonomous-lifecycle-runner.xml tests/test_lifecycle_runner.py` | exit 0; results build/test-results/autonomous-lifecycle-runner.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Document quality check reports linting or bilingual parity errors.

## Decisions Already Made

- Autonomous mode does not auto-merge: it halts at `AWAITING_FINISH` and displays the prompt for `/finishing-a-development-branch`.
- `run_gate4(self) -> Tuple[bool, str]` executes the complete Stage 3 Gate 4 verification sequence on the candidate commit SHA: (1) smoke checklist generation via `generate_smoke_checklist.py --epic-dir <epic>`; (2) review decision check via `run_external_review.py check --epic-dir <epic> --kind code`; (3) code and security audit checks via `audit_epic.py --epic-dir <epic> --base <base>`; (4) result-based BDD traceability via `check_bdd_traceability.py tests --scenarios .devtool/epic/<epic>/bdd_scenarios.en.md --roots <roots> --results <reports>`, dynamically deriving test roots and report paths from the target epic's HLD Integration Test Plan; and (5) complete headless `quality_check` workflow executed with `profile="epic"`, base reference, candidate commit SHA, registered provider execution, and contract reconciliation, requiring an aggregated verdict of PASS bound to that candidate SHA (`skills/dev-implementation/SKILL.md:349–356`).
- Gate 4 PASS candidate SHA is verified before rendering the final executive report.
- Circuit breaker on Round 3 critical exhaustion outputs the Top 3 Highest-Risk Findings and halts.
- Role boundaries: In autonomous mode, the orchestrator runner invokes review CLIs and generates coordination proposals (`.devtool/`), while source code modifications are strictly executed by the AI Programmer subprocess.
- Gate synchronization: Gate 3 and Gate 4 approvals are recorded via `resume_context.py --gate <n>` to keep `.devtool/state/gate_ledger.jsonl` and `.devtool/GATE_LEDGER.md` synchronized (`ALR-ST-02`). Candidate readiness for Gate 5 is tracked strictly in `.devtool/state/<epic>.pipeline.json` (`active_stage = "awaiting_finish"`); `resume_context.py --gate 5` is executed only upon explicit Human finish and merge sign-off.
- `scripts/verify.sh` registers `lifecycle-runner` suite pointing to `tests/test_lifecycle_runner.py`.

## Definition of Done

- Scenarios ALR-HP-01, ALR-FR-03, ALR-ST-02 are covered and pass in the test suite. (V2, V3, V6)
- Python quality checks (lint and type check) pass cleanly. (V4, V5)
- Document checks pass across all modified skills and bilingual markdown files. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 1](task_1_pipeline_state_machine_and_probing.md), [Task 2](task_2_subprocess_dispatcher_and_headless_agy.md), [Task 3](task_3_principal_review_automation_and_checkpoint.md), and [Task 4](task_4_cross_model_review_fix_plan_loop.md).

## References & Rollback

- [Epic HLD](autonomous_lifecycle_runner.en.md), Module Contracts.
- **Rollback**: Revert task commit; documentation and CLI wiring restored to previous revision.
