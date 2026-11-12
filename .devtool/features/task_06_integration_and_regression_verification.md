---
id: "task_06_integration_and_regression_verification"
status: "todo"
priority: "high"
assignee: null
epic: "token_throttling_optimization"
dueDate: null
created: "2026-11-13T02:36:00Z"
modified: "2026-11-13T02:36:00Z"
completedAt: null
labels: ["acceptance", "regression", "verification", "token-optimization"]
order: "a6"
---

# Task 6: Token Throttling Acceptance and Quantitative Regression Suite

Epic: [token_throttling_optimization](../epic/token_throttling_optimization/token_throttling_optimization.en.md)

## Requirement Analysis

Implement the end-to-end quantitative token-throttling acceptance and regression test suite (`tests/test_token_throttling_acceptance.py`) and register all new epic test suites inside `scripts/verify.sh` so Gate 4 and release verification enforce every token-throttling bound continuously:
1. **End-to-End Token-Throttling Acceptance (`tests/test_token_throttling_acceptance.py`)**:
   - Validate all quantitative byte ceilings against the live repository and mock epic fixtures:
     - `rules/CRITICAL_RULES.md <= 8192` bytes and contains Zero-Fluff Output Cap (`Rule 5`).
     - `skills/dev-designer/SKILL.md <= 22528` bytes.
     - `skills/task-observer/SKILL.md` opens with `<SUBAGENT-STOP>`.
     - `scripts/resume_context.py --compact --epic <slug> <= 4096` bytes.
     - Zero stale hardcoded `Gemini Flash 3.8` / `gemini-3.8-flash` Role 2.3 defaults in lifecycle skills, rules, templates, or runner defaults; resolved default programmer model equals `gemini-4-hydrogen-xhigh` with effort `xhigh`.
   - Verify fail-loud quantitative assertions (`TTO-FR-04`): exceeding any threshold produces explicit actual-vs-budget byte diagnostic messages.
   - Verify isolated per-task context and per-round raw log isolation (`TTO-AR-02`): consecutive review rounds write distinct `build/reviews/<epic>_<kind>_round<n>_<sha7>.raw.log` files without colliding between `principal` and `code` reviews or leaking transcripts into adjacent rounds/markdown tables, and consecutive `lifecycle_runner.py` task prompts carry zero accumulated Task `N` output into Task `N+1`.
   - Verify compact Gate 4 and `--quiet` vs `--full` release harness behavior (`TTO-HP-08`, `TTO-EC-06`).
2. **Release Verification Registry (`scripts/verify.sh`)**:
   - Add `tests/test_tto_external_review.py`, `tests/test_tto_bilingual_and_surgical.py`, `tests/test_tto_docs_and_slimming.py`, and `tests/test_token_throttling_acceptance.py` (alongside any unregistered polyglot/runner test suites as appropriate) into `SUITES` in `scripts/verify.sh` so both `--quiet` and `--full` run all §1–§17 checks cleanly.

## Files

Allowed files:
- `tests/test_token_throttling_acceptance.py` (new)
- `scripts/verify.sh`

Read-only context:
- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Integration Test Plan (§4)
- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios
- `tests/test_tto_external_review.py` — External review tests (Task 1)
- `tests/test_polyglot_gate4.py` — Compact Gate 4 tests (Task 2)
- `tests/test_tto_bilingual_and_surgical.py` — Option A & compact context tests (Task 3)
- `tests/test_lifecycle_runner.py` — Config precedence & pool dispatch tests (Task 4)
- `tests/test_tto_docs_and_slimming.py` — Rules, skills & selective reviewer tests (Task 5)

## Design Rationale

Token budgets erode silently over future commits unless enforced by automated quantitative regression assertions wired directly into the repository's CI release gate (`scripts/verify.sh`). Keeping acceptance tests in `tests/test_token_throttling_acceptance.py` while registering every new module test in `SUITES` ensures any future rule bloat, hardcoded model drift, or log leak fails loudly at release time. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `tests/test_token_throttling_acceptance.py`: new quantitative regression and end-to-end acceptance suite for `TTO-HP-08`, `TTO-EC-06`, `TTO-AR-02`, `TTO-FR-04`
  - `scripts/verify.sh`: `SUITES` (L303-L400) suite registrations and section status execution
- **Downstream Callers**: CI release verification (`bash scripts/verify.sh --full`), developer quiet runs (`bash scripts/verify.sh --quiet`), Polyglot Gate 4 `pytest` runner.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of HLD quantitative caps, cross-task isolation invariants, and `--quiet`/`--full` section parity checks.

### BDD SCENARIOS

Covers: TTO-HP-08, TTO-EC-06, TTO-AR-02, TTO-FR-04

```gherkin
Scenario: [TTO-HP-08] [Tier C - Integration] End-to-end token-throttling pipeline enforces compact prompts, review isolation, and programmer config

Given an isolated epic workspace bootstrapped with .devtool/review_config.json, task files containing target line ranges, and fake review/agy CLIs
When the lifecycle pipeline executes readiness, external review, worker dispatch, compact Gate 4, and executive summary generation
Then every review prompt respects the diff-only -U5 budget and writes raw output outside markdown files
And every worker prompt omits inlined source files while invoking gemini-4-hydrogen-xhigh with --effort xhigh
And compact Gate 4 emits single-line GATE_PASS statuses upon green verification

Scenario: [TTO-EC-06] [Tier C - Integration] Compact verify.sh --quiet prints concise section lines while --full executes all 17 suites

Given the repository tooling scripts and markdown skills under scripts/verify.sh
When bash scripts/verify.sh --quiet runs and when bash scripts/verify.sh --full runs
Then --quiet prints a single concise status line per passing section without verbose suite noise
And --full executes all registered verification sections §1 through §17 and exits with status 0

Scenario: [TTO-AR-02] [Tier C - Integration] Per-task clean context and per-round raw logs prevent cross-session transcript contamination

Given sequential Principal Review and Cross-Model Review rounds alongside consecutive task dispatches within a single epic run
When run_external_review.render_round writes logs and lifecycle_runner invokes Task N+1 after Task N commits
Then each review round writes its isolated raw transcript to a distinct build/reviews/<epic>_<kind>_round<n>_<sha7>.raw.log path without colliding across principal and code reviews or appending into adjacent round logs
And the Task N+1 invocation prompt contains no accumulated tool output or stderr from Task N

Scenario: [TTO-FR-04] [Tier C - Integration] Quantitative regression tests fail loudly if rule, skill, context, or prompt sizes exceed caps

Given the live kit files and mock epic harness inside tests/test_token_throttling_acceptance.py
When the quantitative token-throttling acceptance suite executes under pytest
Then assertions explicitly check byte ceilings (CRITICAL_RULES.md <= 8192, dev-designer/SKILL.md <= 22528, resume_context --compact <= 4096) and review/prompt budgets
And exceeding any ceiling fails with concrete byte-count diagnostics rather than generic boolean checks
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_token_throttling_acceptance.py::test_tto_ec_06_verify_suite_registration` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_token_throttling_acceptance.py::test_tto_ec_06_verify_suite_registration` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_external_review.py tests/test_polyglot_gate4.py tests/test_tto_bilingual_and_surgical.py tests/test_lifecycle_runner.py tests/test_tto_docs_and_slimming.py tests/test_token_throttling_acceptance.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 tests/test_token_throttling_acceptance.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_token_throttling_acceptance.py` | exit 0 | — |
| V6 | TIER-B | `bash scripts/verify.sh --quiet` | exit 0 | — |
| V7 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_6.xml tests/test_token_throttling_acceptance.py` | exit 0; results build/test-results/task_6.xml | — |
| V8 | TIER-C | `bash scripts/verify.sh --full` | exit 0 | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path not named explicitly here.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Quantitative regression assertions fail with concrete formatted actual vs limit byte counts rather than opaque booleans; `V1` RED targets missing `scripts/verify.sh` `SUITES` registration (`test_tto_ec_06_verify_suite_registration`) rather than pre-satisfied Tasks 3/5 byte bounds.
- `TTO-AR-02` validates non-colliding `build/reviews/<epic>_<kind>_round<n>_<sha7>.raw.log` isolation between `principal` and `code` reviews.
- `scripts/verify.sh` retains full backward compatibility on `--full` (`§1`–`§17`) while `--quiet` prints single-line summaries for passing sections and capped failure tails.

## Definition of Done

- All 25 epic BDD scenarios (`TTO-HP-01..FR-04`) are covered across Tasks 1–6 and verified end-to-end by `tests/test_token_throttling_acceptance.py`. (V2, V3, V7)
- `scripts/verify.sh --quiet` and `scripts/verify.sh --full` pass across every registered suite `§1`–`§17`. (V6, V8)
- Ruff lint and mypy checks pass on `tests/test_token_throttling_acceptance.py`. (V4, V5)
- Final quantitative measurements and before/after summary inspected at Gate 5 completion. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 1](../epic/token_throttling_optimization/task_01_diff_only_external_review_and_transcript_isolation.md), [Task 2](../epic/token_throttling_optimization/task_02_silent_gate4_and_truncated_test_runners.md), [Task 3](../epic/token_throttling_optimization/task_03_option_a_bilingual_and_surgical_contract_guards.md), [Task 4](../epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md), and [Task 5](../epic/token_throttling_optimization/task_05_slimming_rules_skills_dedup_and_selective_reviewer.md). Blocks none.

## References & Rollback

- [Epic HLD](../epic/token_throttling_optimization/token_throttling_optimization.en.md), Integration Test Plan & Rollout (§4).
- **Rollback**: Revert task commit; restores prior `scripts/verify.sh` suite list and removes `tests/test_token_throttling_acceptance.py`.
