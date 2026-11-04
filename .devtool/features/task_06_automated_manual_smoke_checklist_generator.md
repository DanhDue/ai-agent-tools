---
id: "task_06_automated_manual_smoke_checklist_generator"
status: "todo"
priority: "medium"
assignee: null
epic: "web-quality-check-and-integration-gate"
dueDate: null
created: "2026-11-04T22:52:00Z"
modified: "2026-11-04T22:52:00Z"
completedAt: null
labels: ["automation", "smoke-test", "workflow"]
order: "a6"
---

# Task 06: Automated Manual Smoke Checklist Generator

Epic: [web_quality_check_and_integration_gate](../epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md)

## Requirement Analysis

Build the automated smoke checklist generator script `generate_smoke_checklist.py` and hook it into Phase 4 of `dev-implementation`. The script parses the canonical BDD Happy Path scenarios (`bdd_scenarios.en.md`), extracts 3 to 5 core user journey steps, and formats them into a clean markdown document at `.devtool/epic/<epic_dir>/manual_smoke_checklist.md` before the final Gate 4 validation run. This gives the human engineer an instant 2-minute manual sanity check checklist without dirtying the git working tree after Gate 4.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/generate_smoke_checklist.py` (new)
- `skills/dev-implementation/SKILL.md`
- `tests/test_smoke_checklist_generator.py` (new)

Read-only context:
- `.devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.en.md` (source BDD contract)
- `skills/dev-implementation/SKILL.md` (Phase 4 integration point)

## Design Rationale

Even with 100% automated testing, human developers naturally want to perform a quick sanity check before release. Without structured guidance, this exploratory testing often takes 20-30 minutes of aimless clicking. Automatically generating a focused 3-5 step walkthrough directly from the approved BDD Happy Paths concentrates human verification into a rapid 2-minute validation loop.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `generate_smoke_checklist.py`, `dev-implementation/SKILL.md`.
- **Downstream Callers**: `dev-implementation` Phase 4 upon Gate 4 pass.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 85\%$ for `generate_smoke_checklist.py`.

### BDD SCENARIOS

Covers: [WQG-HP-04]

#### Scenario: [WQG-HP-04] [Tier A - Unit] Automated generation of 3-5 step manual smoke checklist
Given all tasks in an epic reach status `done` and Phase 4 executes
When the smoke generator parses primary BDD Happy Path scenarios
Then it emits `.devtool/epic/<epic_dir>/manual_smoke_checklist.md` before Gate 4 validation
And the checklist contains between 3 and 5 actionable verification steps with Target (URL or CLI Command), Action, and Observable Outcome.

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest tests/test_smoke_checklist_generator.py::test_smoke_checklist_generation` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest tests/test_smoke_checklist_generator.py::test_smoke_checklist_generation` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check tests/test_smoke_checklist_generator.py skills/dev-implementation` | exit 0 | — |
| V4 | TIER-B | `mypy skills/dev-implementation/resources/scripts/generate_smoke_checklist.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest tests/test_smoke_checklist_generator.py -k "test_WQG_HP_04" --junitxml=build/test-results/task_06.xml` | exit 0; results build/test-results/task_06.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Output path: `.devtool/epic/<epic_dir>/manual_smoke_checklist.md`.
- Maximum checklist length: 5 items.
- Structure: Checklist table containing Step Number, Target (URL / CLI Command), Action, and Observable Outcome.
- Smoke extraction logic: Extracts URL if present in scenario steps; if step specifies a CLI or tooling command (such as `d3nexus:web-quality-check`), extracts the command/entrypoint as Target; fallback to `CLI / Workspace Root` with parsed When/Then actions when URLs are absent.
- Workflow timing: The generator executes and commits `manual_smoke_checklist.md` in Phase 4 before candidate SHA resolution and the final Gate 4 run, ensuring zero uncommitted files and maintaining candidate SHA stability.

## Definition of Done

- `generate_smoke_checklist.py` extracts Happy Path steps and outputs valid markdown. (V2)
- Script passes ruff linting and mypy typing. (V3, V4)
- Scenario [WQG-HP-04] fully verified and passing. (V5)
- Clean git status with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by: [Task 01](task_01_web_quality_check_skill_and_contract.md), [Task 05](task_05_anti_rationalization_and_doubt_driven_workflow.md).

## References & Rollback

- Reference: `dev-implementation/SKILL.md` Phase 4 verification flow.
- Rollback: Revert `generate_smoke_checklist.py` and test file.
