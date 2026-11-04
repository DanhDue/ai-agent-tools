---
id: "task_05_anti_rationalization_and_doubt_driven_workflow"
status: "done"
priority: "high"
assignee: null
epic: "web-quality-check-and-integration-gate"
dueDate: null
created: "2026-11-04T22:52:00Z"
modified: "2026-11-04T21:18:31Z"
completedAt: "2026-11-04T21:18:31Z"
labels: ["governance", "workflow", "anti-rationalization"]
order: "a5"
---

# Task 05: Anti-Rationalization and Doubt-Driven Workflow Rules

Epic: [web_quality_check_and_integration_gate](../epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md)

## Requirement Analysis

Incorporate Anti-Rationalization Tables and Doubt-Driven Verification principles (inspired by `addyosmani/agent-skills`) into core lifecycle and implementation skills: `dev-designer`, `dev-implementation`, and `test-driven-development`. Enforce Subcutaneous Testing for mobile, require real Playwright execution for web Tier C scenarios, reject mock-substitution shortcuts during task execution, and enforce the 5th anti-rationalization rule rejecting porting Visual Companion HTML/JS without verifying computed CSS styles and geometry assertions. Enforce scenario-aware test runner provenance in `task_contract.py` condition 6 and `result_reports.py`: tests satisfying Tier C scenarios (`[WQG-HP-*]`, `[WQG-FR-*]`, `[WQG-EC-*]`) must demonstrate integration runner provenance in their JUnit XML `classname` (e.g. matching Playwright runner patterns or subcutaneous harness suites). Pure unit test classes (`tests/unit/.*` or unit mocks) claiming Tier C scenario names without integration runner provenance must be rejected at the done-gate with condition 6 violation.

## Files

Allowed files:
- `skills/dev-designer/SKILL.md`
- `skills/dev-implementation/SKILL.md`
- `skills/test-driven-development/SKILL.md`
- `skills/dev-implementation/resources/scripts/task_contract.py`
- `skills/dev-implementation/resources/scripts/result_reports.py`
- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
- `tests/test_workflow_anti_rationalization.py` (new)

Read-only context:
- `rules/CRITICAL_RULES.md` (mandatory quality gates)
- `.devtool/epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md` (parent HLD)

## Design Rationale

AI coding agents naturally seek the path of least resistance, often writing Unit mocks while tagging them as Integration tests or skipping browser validation. Codifying explicit Anti-Rationalization Tables directly in the skill prompts provides an active behavioral counter-force, preventing agents from cutting corners before task completion.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `dev-designer`, `dev-implementation`, `test-driven-development`.
- **Downstream Callers**: All developers and agents running epic lifecycles across mobile and web.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: Document syntax and skill lint validation (0 errors).

### BDD SCENARIOS

Covers: [WQG-ST-02]

#### Scenario: [WQG-ST-02] [Tier C - Integration] Task status progression under Anti-Rationalization audit
Given a Kanban task covering Tier C scenario `[WQG-HP-01]`
When the verification runner evaluates task completion with missing Tier C integration evidence or only unit mocks
Then `task_contract.py` and task status sync reject the transition to `done` with condition 6 violation
And when real Playwright headless integration test execution evidence is provided in the verification results
Then the task transitions cleanly to status `done`.

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest tests/test_workflow_anti_rationalization.py::test_anti_rationalization_content` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest tests/test_workflow_anti_rationalization.py::test_anti_rationalization_content` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check tests/test_workflow_anti_rationalization.py` | exit 0 | — |
| V4 | TIER-B | `mypy tests/test_workflow_anti_rationalization.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest tests/test_workflow_anti_rationalization.py -k "test_WQG_ST_02" --junitxml=build/test-results/task_05.xml` | exit 0; results build/test-results/task_05.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Frontmatter of `SKILL.md` files must remain strictly `name` and `description` only.
- Anti-Rationalization tables placed in dedicated sections within each skill.
- Subcutaneous testing guidelines formalized for Flutter and native mobile.
- `task_contract.py` condition 6 enforces real Tier C test cases in verification results for Tier C scenarios, rejecting mock-only completion attempts.
- 5th Anti-Rationalization rule: Rejects porting HTML/JS from Visual Companion mockups without computed CSS assertions; requires `getComputedStyle` and `getBoundingClientRect` verification (non-zero dimensions, layout display mode, and mutually exclusive state visibility) against the design.
- Execution provenance verification: `result_reports.py` and `task_contract.py` condition 6 verify test runner provenance for Tier C scenarios via classname patterns/markers (Playwright integration test suite or subcutaneous runner). Unit-only mock suites attempting to claim Tier C coverage are rejected.
- Rejection tests: `test_check_task_contract.py` adds regression tests asserting that unit-only test reports covering Tier C scenarios fail condition 6.

## Definition of Done

- `dev-designer/SKILL.md` requires Playwright for Web and Subcutaneous tests for Mobile. (V2)
- Test suite passes ruff linting and mypy typing. (V3, V4)
- Scenario [WQG-ST-02] fully verified and passing. (V5)
- Clean git status with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by: [Task 01](task_01_web_quality_check_skill_and_contract.md).

## References & Rollback

- Reference: `addyosmani/agent-skills` Anti-Rationalization patterns.
- Rollback: Revert modifications to `skills/` files via git restore.
