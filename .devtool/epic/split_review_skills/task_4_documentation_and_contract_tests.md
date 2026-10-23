---
id: "task_4_documentation_and_contract_tests"
status: "todo"
priority: "high"
assignee: null
epic: "split_review_skills"
dueDate: null
created: "2026-10-23T11:40:00Z"
modified: "2026-10-23T11:40:00Z"
completedAt: null
labels: ["documentation", "mermaid", "contract-tests", "verification"]
order: "a4"
---

# Task 4: Update Lifecycle Documentation, Diagrams and Contract Tests

Epic: [split_review_skills](split_review_skills.en.md)

## Requirement Analysis

Update human-facing lifecycle documentation (`docs/lifecycles.en.md` and `docs/lifecycles.vi.md`) with modernized Mermaid diagrams displaying explicit invocations of `principal-review` in Stage 2 and `cross-model-review` in Stage 3.
Update `scripts/test_lifecycle_document_contract.py` to enforce the contract across `skills/principal-review/SKILL.md` and `skills/cross-model-review/SKILL.md`.
Run full system verification (`./scripts/verify.sh`) to confirm all 62 skills, relative links, and test suites pass.

Key deliverables:
1. Update `docs/lifecycles.en.md` and `docs/lifecycles.vi.md`:
   - Stage 2 flowchart showing `principal-review` call at Principal Review Choice.
   - Stage 3 flowchart showing `cross-model-review` call at Review Choice.
   - Synchronized bilingual prose explaining the shift-left vs shift-right rationale.
2. Update `scripts/test_lifecycle_document_contract.py`:
   - Add expected contract keywords for `skills/principal-review/SKILL.md` and `skills/cross-model-review/SKILL.md`.
   - Update `PrincipalReviewWorkflowTest` assertions (`test_prv_hp_04_packaging_readiness_and_principal_review_choice` and `test_prv_st_03_diagram_loop_returns_to_package_and_done_repackages`) to match the streamlined `skills/dev-lifecycle/references/principal-review.md` delegation content.
3. Validate plugin manifests and execute `./scripts/verify.sh` until clean pass.

## Files

Allowed files:
- `docs/lifecycles.en.md`
- `docs/lifecycles.vi.md`
- `scripts/test_lifecycle_document_contract.py`
- `scripts/verify.sh`

Read-only context:
- `skills/principal-review/SKILL.md`
- `skills/cross-model-review/SKILL.md`
- `.devtool/epic/split_review_skills/split_review_skills.en.md`
- `.devtool/epic/split_review_skills/bdd_scenarios.en.md`

## Design Rationale

Keeping human-facing documentation truthful and synchronized with active runtime skills ensures developers and AI agents maintain unified mental models.
Contract tests guarantee that future refactoring will not accidentally break skill references or document bilingual parity.
Applicable skills: `d3nexus:test-driven-development`, `d3nexus:doc_quality_check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `docs/lifecycles.en.md`, `docs/lifecycles.vi.md`: updated Mermaid diagrams and lifecycle prose
  - `scripts/test_lifecycle_document_contract.py`: `PrincipalReviewWorkflowTest`, `test_prv_hp_04_packaging_readiness_and_principal_review_choice()`, `test_prv_st_03_diagram_loop_returns_to_package_and_done_repackages()`, new `TestReviewSkillContracts`
- **Downstream Callers**: entire repository quality gates and publishing checks.
- **Cross-Platform Bridges**: none.
- **Target Test Coverage Threshold**: `./scripts/verify.sh` outputs `PASS — safe to publish`.

### BDD SCENARIOS

Covers: SRS-HP-06, SRS-HP-07

```gherkin
Scenario: [SRS-HP-06] [Tier C - Integration] Document contracts enforce new review skills exposure
  Given the repository skill directory contains "principal-review" and "cross-model-review"
  When "test_lifecycle_document_contract.py" evaluates all lifecycle producers
  Then both skills expose expected contract keywords and YAML frontmatter
  And "scripts/verify.sh" completes with zero contract regressions

Scenario: [SRS-HP-07] [Tier C - Integration] Lifecycle diagrams reflect two standalone review stages
  Given human-facing lifecycle documentation "docs/lifecycles.en.md" and "docs/lifecycles.vi.md"
  When modern flowchart diagrams are inspected
  Then Stage 2 displays explicit delegation to "principal-review"
  And Stage 3 displays explicit delegation to "cross-model-review"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest scripts/test_lifecycle_document_contract.py -k TestReviewSkillContracts` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest scripts/test_lifecycle_document_contract.py -k TestReviewSkillContracts` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict --follow-imports=silent scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_4.xml scripts/test_lifecycle_document_contract.py` | exit 0; results build/test-results/task_4.xml | — |

## Stop and Report If

- A command, path, symbol, or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files, or Covers line.

## Decisions Already Made

- All Mermaid diagrams use `flowchart` syntax with quoted labels.
- Both language variants remain synchronized.

## Definition of Done

- `docs/lifecycles.en.md` and `docs/lifecycles.vi.md` reflect the updated skill invocations. (V2, V5)
- `scripts/test_lifecycle_document_contract.py` validates new skills cleanly. (V2, V5)
- All lint, type checks, and verification rows V1–V5 pass. (V3, V4, V5)

## Dependencies & Blockers

- Blocked by [Task 3](task_3_orchestrators_delegation_refactor.md).
- Blocks: None.

## References & Rollback

- [Epic HLD](split_review_skills.en.md), Module Contracts.
- **Rollback**: Revert task commit.
