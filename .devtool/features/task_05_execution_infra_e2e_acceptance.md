---
id: "task_05_execution_infra_e2e_acceptance"
status: "todo"
priority: "high"
assignee: null
epic: "execution-and-verification-infrastructure"
dueDate: null
created: "2026-11-06T03:20:00Z"
modified: "2026-11-06T12:57:55Z"
completedAt: null
labels: ["acceptance", "integration", "docs"]
order: "b5"
---

# Task 05: End-to-End Execution Infrastructure Acceptance Verification

Epic: [execution_and_verification_infrastructure](../epic/execution_and_verification_infrastructure/execution_and_verification_infrastructure.en.md)

## Requirement Analysis

Provide the end-to-end subcutaneous acceptance test suite (`tests/test_execution_infra_acceptance.py`) verifying `check_epic_readiness.py --replay` isolated worktree execution and cleanup (`EVI-AR-01`) alongside all `[Tier C - Integration]` scenarios (`EVI-HP-01`, `EVI-HP-02`, `EVI-HP-03`, `EVI-HP-04`, `EVI-ST-02`, `EVI-AR-01`), and update `skills/dev-designer/SKILL.md` and `skills/dev-implementation/SKILL.md` to document:
1. Optional `"bootstrap"` commands in `.agents/quality/python-quality.json` and polyglot worktree bootstrap (`#0006`, `#0018`).
2. Failure-set baseline recording (`record_failure_baseline.py`) and regression comparison (`compare_failure_sets.py`) (`#0007`).
3. Opt-in `Integration results (live, needs: VAR):` and parameterized route matching in `R5b` (`#0010`).
4. Static edit-anchor checking (`R5`) and scratch-worktree replay (`check_epic_readiness.py --replay`) (`#0011`).
5. `Phase: MEASURE` (`run_task_checks.py measure --resume`) and the **Measurement-to-Evidence** pattern (`#0017`).

## Files

Allowed files:
- `tests/test_execution_infra_acceptance.py` (new)
- `skills/dev-designer/SKILL.md`
- `skills/dev-implementation/SKILL.md`

Read-only context:
- `skills/dev-implementation/resources/scripts/replay_task_text.py` (implemented in Task 04)
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py` (updated in Tasks 03–04)
- `skills/dev-implementation/resources/scripts/run_task_checks.py` (updated in Tasks 01 and 04)
- `.devtool/epic/execution_and_verification_infrastructure/execution_and_verification_infrastructure.en.md` (HLD specification)

## Design Rationale

Applicable skills: `python-quality-check`, `doc_quality_check`, `verification-before-completion`.
Because Tasks 01–04 implement all underlying runtime behaviors, this final acceptance task uses `RED: n/a` and verifies the complete end-to-end integration across temporary Git repositories and worktrees while updating the skill documentation so future designers and programmers adopt these tools by default.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `tests/test_execution_infra_acceptance.py`: new `test_EVI_AR_01_readiness_replay_isolated_worktree` and end-to-end Tier C acceptance tests.
- **Downstream Callers**: `scripts/verify.sh` and Gate 4 `Integration results:`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $100\%$ of `[Tier C - Integration]` scenarios (`EVI-HP-01`, `EVI-HP-02`, `EVI-HP-03`, `EVI-HP-04`, `EVI-ST-02`, `EVI-AR-01`) verified in JUnit XML output.

### BDD SCENARIOS

Covers: EVI-AR-01

```gherkin
  Scenario: [EVI-AR-01] [Tier C - Integration] check_epic_readiness.py --replay executes task text in an isolated scratch worktree and cleans up without mutating the main tree
    Given an epic whose tasks contain valid "Create", "Replace in", and "Insert in" directives
    When "check_epic_readiness.py <epic> --replay" is executed
    Then it creates a temporary git worktree, replays each task's fenced edits sequentially, runs the Verification commands, and removes the temporary worktree on completion
    And "git status --porcelain" on the main repository remains completely unchanged
```

## Verification

RED: n/a — end-to-end acceptance test suite and skill documentation verifying behaviors already implemented in Tasks 01–04.

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | GREEN | `python3 -m pytest tests/test_execution_infra_acceptance.py` | exit 0; contains "passed" | — |
| V2 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_execution_infra_acceptance.py` | exit 0 | — |
| V3 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_execution_infra_acceptance.py --follow-imports=silent` | exit 0 | — |
| V4 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-designer/SKILL.md skills/dev-implementation/SKILL.md` | exit 0; contains "0 findings" | — |
| V5 | TIER-C | `python3 -m pytest tests/ skills/dev-implementation/resources/scripts/ skills/python-quality-check/resources/scripts/ --junitxml=build/test-results/pytest.xml` | exit 0; results build/test-results/pytest.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `tests/test_execution_infra_acceptance.py` tests `check_epic_readiness.py <epic> --replay` on a temporary Git repository containing a 2-task epic with `Create`, `Replace in`, and `Insert in` directives, asserting exit code `0`, `R8 PASS`, and `git status --porcelain == ""` + `len(git worktree list) == 1` after completion (`EVI-AR-01`).
- `skills/dev-designer/SKILL.md` documents `Integration results (live, needs: VAR):`, `Phase: MEASURE` (**Measurement-to-Evidence** pattern), and `check_epic_readiness.py --replay`.
- `skills/dev-implementation/SKILL.md` documents `run_task_checks.py measure <task.md> [--timeout 7200] [--resume]`, `record_failure_baseline.py`, and `compare_failure_sets.py`.

## Definition of Done

- `tests/test_execution_infra_acceptance.py` verifies `EVI-AR-01` (`check_epic_readiness.py --replay` isolated worktree execution and cleanup) and passes the full Tier C integration suite. (V1, V5)
- `skills/dev-designer/SKILL.md` and `skills/dev-implementation/SKILL.md` document the new execution and verification infrastructure capabilities and pass `check_document.py`. (V4)
- `ruff` and `mypy` pass with zero errors. (V2, V3)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 01](../epic/execution_and_verification_infrastructure/task_01_polyglot_worktree_bootstrap.md)
- Blocked by [Task 02](../epic/execution_and_verification_infrastructure/task_02_failure_baseline_and_comparison.md)
- Blocked by [Task 03](../epic/execution_and_verification_infrastructure/task_03_live_integration_and_route_matching.md)
- Blocked by [Task 04](../epic/execution_and_verification_infrastructure/task_04_task_replay_and_measure_phase.md)

## References & Rollback

- Reference: [2026-11-06-execution-and-verification-infrastructure-design.en.md](../epic/execution_and_verification_infrastructure/2026-11-06-execution-and-verification-infrastructure-design.en.md).
- Rollback: `git revert` the task commit to remove `tests/test_execution_infra_acceptance.py` and doc updates.
