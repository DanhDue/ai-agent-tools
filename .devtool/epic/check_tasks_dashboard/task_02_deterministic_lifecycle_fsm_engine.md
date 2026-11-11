---
id: "task_02_deterministic_lifecycle_fsm_engine"
status: "todo"
priority: "high"
assignee: null
epic: "check_tasks_dashboard"
dueDate: null
created: "2026-11-11T08:30:00Z"
modified: "2026-11-11T08:30:00Z"
completedAt: null
labels: ["fsm", "lifecycle", "governance"]
order: "a2"
---

# Task 2: Deterministic Lifecycle FSM Engine and Decision Derivation

Epic: [check_tasks_dashboard](check_tasks_dashboard.en.md)

## Requirement Analysis

Implement the deterministic lifecycle state machine engine in `skills/check-tasks/resources/scripts/check_tasks.py`:
1. Core enumerations and data structures:
   - `LifecycleStage`: `STAGE_1_INCEPTION`, `STAGE_2_ARCHITECTURE`, `STAGE_2_EXIT_HANDOFF`, `STAGE_2_REVIEW_TRIAGE`, `STAGE_3_PHASE_1_ORDER`, `STAGE_3_PHASE_2_TDD`, `STAGE_3_PHASE_4_REVIEW`, `STAGE_3_PHASE_4_1_SIGNOFF`, `IDLE`.
   - `LifecycleDecision`: stage_name, gate_status, prompt, is_human_action_required, is_blocked.
2. Derivation logic in `derive_lifecycle_state(repo_path: Path, active_epic: str | None) -> LifecycleDecision`:
   - Dual-check verification: inspects `.devtool/assistant_state.md` for explicit `## Next Immediate Step:` notes and `.devtool/GATE_LEDGER.md` for gate completion timestamps.
   - Evaluates the 8 Core Human Decision Mapping Matrix:
     - Stage 1: No Gate 1 recorded; spec exists -> "Approve Gate 1 (Design Spec)".
     - Stage 2: Gate 1 PASS, no Gate 2 -> "AI Assistant authoring HLD & Task Breakdown".
     - Stage 2 Exit: Gate 2 PASS, `handoff.md` present -> "Handoff Choice: (1) Run /principal-review or (2) Enter Stage 3".
     - Stage 2 Triage: Principal Review contains unconfirmed findings -> "Approve Triage Decisions".
     - Stage 3 Phase 1: Gate 2 PASS, worktree ready, no Gate 3 -> "Approve Gate 3 (Order & Worktree)".
     - Stage 3 Phase 2: Gate 3 PASS, tasks in progress -> "AI Programmer autonomously executing TDD".
     - Stage 3 Phase 4: All tasks done, Gate 4 PASS, no Gate 5 -> "Review Choice (Mandatory Rule 5)".
     - Stage 3 Phase 4.1: Gate 4 PASS after reviews -> "Approve Gate 5 (Kanban Sign-off)".
3. Unit test suite `tests/test_check_tasks_fsm.py` testing all 8 states, boundary transitions, and dual-check verification.

## Files

Allowed files:
- `skills/check-tasks/resources/scripts/check_tasks.py` (new)
- `tests/test_check_tasks_fsm.py` (new)

Read-only context:
- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` — state transitions and gate synchronization
- `.devtool/epic/check_tasks_dashboard/check_tasks_dashboard.en.md` — FSM Specification

## Design Rationale

Decoupled FSM derivation allows both the CLI and Web dashboard to present identical, deterministic decision prompts regardless of whether the agent is currently running. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `skills/check-tasks/resources/scripts/check_tasks.py` (`LifecycleStage`, `LifecycleDecision`, `derive_lifecycle_state`).
- **Downstream callers**: Tasks 3, 4, and 5 consume these lifecycle decisions.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: 100% of FSM transition branches and ledger conditions.

### BDD SCENARIOS

Covers: CTD-HP-02, CTD-ST-01, CTD-ST-02

```gherkin
Scenario: [CTD-HP-02] [Tier C - Integration] Deterministic Lifecycle FSM derives exact human decision prompt

Given an epic with Gate 4 PASS recorded in .devtool/GATE_LEDGER.md
And all Kanban tasks in .devtool/features/ are marked done
And Gate 5 is not yet recorded in the ledger
When the lifecycle engine evaluates derive_lifecycle_state for the epic
Then the derived stage name is "Stage 3 Phase 4 (Review)"
And the next immediate human decision prompt explicitly contains "Review Choice (Rule 5)"

Scenario: [CTD-ST-01] [Tier A - Unit] FSM transitions from Stage 2 Architecture to Stage 2 Exit Handoff

Given an epic where Gate 1 is PASS and Gate 2 has just been recorded in GATE_LEDGER.md
And the packaging file handoff.md is present in the epic directory
When derive_lifecycle_state evaluates the repository
Then the state transitions to "Stage 2 Exit (Handoff)"
And the next immediate step prompts the human architect for the handoff choice between Principal Review and Implementation

Scenario: [CTD-ST-02] [Tier A - Unit] FSM transitions to Stage 3 Phase 2 TDD when tasks enter in-progress

Given an epic with Gate 3 PASS recorded in GATE_LEDGER.md
And at least one Kanban task in .devtool/features/ has status "in-progress"
When derive_lifecycle_state evaluates the repository
Then the state transitions to "Stage 3 Phase 2 (TDD)"
And the next immediate step indicates the AI Programmer is actively implementing tasks with zero human intervention required
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest tests/test_check_tasks_fsm.py -k test_ctd_hp_02` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest tests/test_check_tasks_fsm.py -k test_ctd_hp_02` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest tests/test_check_tasks_fsm.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/check-tasks/resources/scripts/check_tasks.py tests/test_check_tasks_fsm.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/check-tasks/resources/scripts/check_tasks.py tests/test_check_tasks_fsm.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml tests/test_check_tasks_fsm.py` | exit 0; results build/test-results/task_2.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.
- An undefined gate name is encountered in `GATE_LEDGER.md`.

## Decisions Already Made

- 8 core human decision stages are mapped verbatim to the HLD specification.
- Dual-check verification inspects `.devtool/assistant_state.md` and verifies consistency with `.devtool/GATE_LEDGER.md`.
- In case of conflict, immutable `GATE_LEDGER.md` records take precedence over volatile assistant snapshots.
- `derive_lifecycle_state` evaluates gates in descending order (Gate 5 -> 4 -> 3 -> 2 -> 1); a stage row matches only when its gate is the highest PASS in `GATE_LEDGER.md` for the normalized epic slug, and Stage 1 requires Gate 2 absent as well as Gate 1.
- Stage 2 Exit is disambiguated from Stage 3 Phase 1 by checking for the existence of an active worktree checkout on `refs/heads/epic/<slug>`.
- Status token comparison accepts both "in-progress" and legacy "in_progress", normalizing to canonical "in-progress".
- Missing ledger records default gracefully to `IDLE` state with no unhandled exceptions.

## Definition of Done

- Scenarios CTD-HP-02, CTD-ST-01, and CTD-ST-02 are covered and pass in the test suite. (V2, V3, V6)
- Python quality checks (lint and type check) pass cleanly. (V4, V5)
- All 8 lifecycle gate conditions return deterministic human action prompts. (Gate 5)

## Dependencies & Blockers

Requires [Task 1](task_01_harvester_engine_and_data_models.md). Blocks [Task 3](task_03_terminal_cli_and_ansi_reporter.md), [Task 4](task_04_http_daemon_server_and_rest_api.md), and [Task 5](task_05_interactive_web_dashboard_and_skill.md).

## References & Rollback

- [Epic HLD](check_tasks_dashboard.en.md), FSM Engine Specification.
- **Rollback**: Revert task commit; deletes changes to `skills/check-tasks/resources/scripts/check_tasks.py` and `tests/test_check_tasks_fsm.py`.
