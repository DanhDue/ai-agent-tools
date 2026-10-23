---
id: "task_3_orchestrators_delegation_refactor"
status: "todo"
priority: "high"
assignee: null
epic: "split_review_skills"
dueDate: null
created: "2026-10-23T11:40:00Z"
modified: "2026-10-23T11:40:00Z"
completedAt: null
labels: ["orchestration", "dev-lifecycle", "dev-implementation", "delegation"]
order: "a3"
---

# Task 3: Refactor Dev-Lifecycle and Dev-Implementation Orchestrators

Epic: [split_review_skills](split_review_skills.en.md)

## Requirement Analysis

Refactor `dev-lifecycle` and `dev-implementation` to adhere strictly to the "sequence and gates only" architectural principle by delegating review execution to `d3nexus:principal-review` and `d3nexus:cross-model-review`.

Key deliverables:
1. `skills/dev-lifecycle/SKILL.md`:
   - Under Handoff Choice, Step 8 invokes `d3nexus:principal-review` upon choosing option 2.
   - Streamline reference documentation in `skills/dev-lifecycle/references/principal-review.md` while preserving contract tokens required by downstream tests.
2. `skills/dev-implementation/SKILL.md`:
   - Under Phase 4 Review Choice, option 2 (Cross-model review) and option 3 (Local model review) explicitly invoke `d3nexus:cross-model-review`.
   - Maintain the strict `<HARD-GATE>` invariant: every review round must return to a full Gate 4 run on the new SHA.
   - Preserve Gate 3 check for undecided principal findings and Gate 5 check for undecided code findings.
3. Unit tests in `scripts/test_lifecycle_signals.py` asserting proper skill delegation and invariant retention.

## Files

Allowed files:
- `skills/dev-lifecycle/SKILL.md`
- `skills/dev-lifecycle/references/principal-review.md`
- `skills/dev-implementation/SKILL.md`
- `scripts/test_lifecycle_signals.py`

Read-only context:
- `skills/principal-review/SKILL.md`
- `skills/cross-model-review/SKILL.md`
- `.devtool/epic/split_review_skills/split_review_skills.en.md`
- `.devtool/epic/split_review_skills/bdd_scenarios.en.md`

## Design Rationale

Orchestrator skills should govern lifecycle transitions and quality gates, not host extensive procedural scripts for reviewer sub-workflows.
Delegating execution to dedicated skills keeps orchestrator word counts well below the 2500-word ceiling while improving modularity and clarity.
Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-lifecycle/SKILL.md`: `dev-lifecycle`
  - `skills/dev-implementation/SKILL.md`: `dev-implementation`
  - `scripts/test_lifecycle_signals.py`: `TestReviewSkillDelegation`
- **Downstream Callers**: developers and agents executing epic lifecycles.
- **Cross-Platform Bridges**: none.
- **Target Test Coverage Threshold**: all delegation test assertions pass.

### BDD SCENARIOS

Covers: SRS-ST-03, SRS-ST-04

```gherkin
Scenario: [SRS-ST-03] [Tier A - Unit] Gate 3 execution order enforces zero undecided principal findings
  Given ".devtool/epic/sample_epic/principal_review.md" contains undecided blocking findings
  When "dev-implementation" initiates Gate 3 execution order verification
  Then Gate 3 check exits with code 1 and refuses to proceed to worktree dispatch

Scenario: [SRS-ST-04] [Tier A - Unit] Gate 5 Kanban sign-off enforces zero undecided code findings
  Given ".devtool/epic/sample_epic/review_results.md" contains undecided blocking findings
  When developer chooses "Finish" at Review Choice
  Then the finish preflight check exits with code 1
  And prompts the developer to decide all findings before proceeding to Gate 5
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest scripts/test_lifecycle_signals.py -k TestReviewSkillDelegation` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest scripts/test_lifecycle_signals.py -k TestReviewSkillDelegation` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check scripts/test_lifecycle_signals.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict --follow-imports=silent scripts/test_lifecycle_signals.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_3.xml scripts/test_lifecycle_signals.py` | exit 0; results build/test-results/task_3.xml | — |

## Stop and Report If

- A command, path, symbol, or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files, or Covers line.

## Decisions Already Made

- Orchestrators name concrete skill invocations (`d3nexus:principal-review` and `d3nexus:cross-model-review`).
- All `<HARD-GATE>` blocks remain intact.

## Definition of Done

- `dev-lifecycle/SKILL.md` delegates to `d3nexus:principal-review`. (V2, V5)
- `dev-implementation/SKILL.md` delegates to `d3nexus:cross-model-review`. (V2, V5)
- All lint, type checks, and verification rows V1–V5 pass. (V3, V4, V5)

## Dependencies & Blockers

- Blocked by [Task 1](task_1_standalone_principal_review_skill.md) and [Task 2](task_2_standalone_cross_model_review_skill.md).
- Blocks [Task 4](task_4_documentation_and_contract_tests.md).

## References & Rollback

- [Epic HLD](split_review_skills.en.md), Module Contracts.
- **Rollback**: Revert task commit.
