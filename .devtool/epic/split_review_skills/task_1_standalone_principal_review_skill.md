---
id: "task_1_standalone_principal_review_skill"
status: "todo"
priority: "high"
assignee: null
epic: "split_review_skills"
dueDate: null
created: "2026-10-23T11:40:00Z"
modified: "2026-10-23T11:40:00Z"
completedAt: null
labels: ["skill", "principal-review", "document-review", "cli"]
order: "a1"
---

# Task 1: Standalone Principal Review Skill and References

Epic: [split_review_skills](split_review_skills.en.md)

## Requirement Analysis

Create the standalone skill `skills/principal-review/SKILL.md` and its dedicated references (`principal-review-prompt.md`, `principal-review-rules.md`, `document-triage.md`).
Update `run_external_review.py` to support reviewing arbitrary standalone design documents via `--doc <path>` alongside the existing `--epic-dir <epic_dir>`, routing prompt and rules through `skills/principal-review/references/`.

Key deliverables:
1. `skills/principal-review/SKILL.md` with valid YAML frontmatter (`name: principal-review`, `description`), documenting both In-Lifecycle (called from `dev-lifecycle` Handoff Choice) and Ad-hoc (`/principal-review <path_or_epic>`) usage.
2. Supporting references in `skills/principal-review/references/`:
   - `principal-review-prompt.md`: Read-only architectural review prompt template.
   - `principal-review-rules.md`: Severity definitions (Critical, Important, Minor) and source grounding discipline.
   - `document-triage.md`: Decision protocol for document findings and revision commit requirements.
3. Update `run_external_review.py` to accept `--doc <path>` when `--kind principal` is specified, allowing ad-hoc validation and review without requiring an epic directory.
4. Unit tests in `test_run_external_review.py` verifying `--doc` support, preflight gate handling, and prompt interpolation.

## Files

Allowed files:
- `skills/principal-review/SKILL.md` (new)
- `skills/principal-review/references/principal-review-prompt.md` (new)
- `skills/principal-review/references/principal-review-rules.md` (new)
- `skills/principal-review/references/document-triage.md` (new)
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`

Read-only context:
- `skills/dev-lifecycle/references/principal-review.md`
- `skills/dev-implementation/references/review-triage.md`
- `.devtool/epic/split_review_skills/split_review_skills.en.md`
- `.devtool/epic/split_review_skills/bdd_scenarios.en.md`

## Design Rationale

Decoupling Principal Review into a standalone skill fulfills the Single Responsibility Principle for AI Agent skills and allows on-demand architectural vetting for RFCs, HLDs, and design documents without running the entire epic packaging pipeline.
The shared runner engine `run_external_review.py` is extended cleanly with optional `--doc` argument without altering the existing in-lifecycle `--epic-dir` contract.
Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/run_external_review.py`: `run()`, `parse_args()`, `principal_artefact_lines()`
  - `skills/dev-implementation/resources/scripts/test_run_external_review.py`: `TestPrincipalReviewDocMode`
- **Downstream Callers**: `dev-lifecycle` (Task 3), direct user invocations (`/principal-review`).
- **Cross-Platform Bridges**: none.
- **Target Test Coverage Threshold**: 100% test pass on new test methods in `test_run_external_review.py`.

### BDD SCENARIOS

Covers: SRS-HP-01, SRS-HP-02, SRS-EC-01, SRS-EC-04, SRS-ST-01, SRS-FR-01

```gherkin
Scenario: [SRS-HP-01] [Tier C - Integration] In-lifecycle Principal Review invocation from dev-lifecycle
  Given an epic "sample_epic" has passed Gate 2 and packaging preflight passes
  When the developer selects option 2 "Principal Review" with "codex" CLI
  Then the "d3nexus:principal-review" skill is invoked
  And "run_external_review.py run --kind principal" executes against the epic artifacts
  And round 1 is recorded into ".devtool/epic/sample_epic/principal_review.md"

Scenario: [SRS-HP-02] [Tier C - Integration] Ad-hoc Principal Review invocation on standalone design document
  Given a standalone design document "docs/rfc/feature-architecture.md" exists
  When the developer invokes "/principal-review docs/rfc/feature-architecture.md" with base "main" and CLI "claude"
  Then the "principal-review" skill validates the document structure
  And invokes the external reviewer with document text and source context
  And outputs an actionable review triage table without requiring an epic directory

Scenario: [SRS-EC-01] [Tier A - Unit] Ad-hoc review invocation with non-existent document
  Given a requested target path "docs/rfc/missing-doc.md" does not exist on disk
  When the user runs "/principal-review docs/rfc/missing-doc.md"
  Then the skill immediately refuses with an error naming the missing path
  And no external CLI process is spawned

Scenario: [SRS-EC-04] [Tier A - Unit] Standalone document without required structure
  Given a standalone document "docs/rfc/broken.md" contains syntax errors or missing headings
  When ad-hoc principal review executes pre-validation
  Then the check reports the formatting error
  And prompts the author to fix structure before running external model review

Scenario: [SRS-ST-01] [Tier C - Integration] Principal Review revision loop enforces commit ordering
  Given round 1 of principal review reported Important findings
  When the developer approves document edits
  Then the revised documents are committed first as "[EPIC] Revise epic after Principal Review round 1"
  And decisions referencing the revision commit SHA are committed into "principal_review.md"
  And the epic packaging procedure re-runs to refresh handoff metadata

Scenario: [SRS-FR-01] [Tier C - Integration] Principal review runner halts on failed readiness preflight
  Given an epic directory has broken document links or missing bilingual pairs
  When "principal-review" executes "check_epic_readiness.py"
  Then the readiness preflight fails with non-zero exit code
  And prints the precondition banner without calling the external CLI model
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k TestPrincipalReviewDocMode` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k TestPrincipalReviewDocMode` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_1.xml skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; results build/test-results/task_1.xml | — |

## Stop and Report If

- A command, path, symbol, or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files, or Covers line.

## Decisions Already Made

- Skill name is exactly `principal-review`.
- The CLI runner engine `run_external_review.py` remains in `skills/dev-implementation/resources/scripts/` to preserve backward compatibility for import and invocation paths.
- Frontmatter follows standard: name and description only.

## Definition of Done

- `skills/principal-review/SKILL.md` exists with frontmatter and complete instructions for both in-lifecycle and ad-hoc modes. (V2, V5)
- References `principal-review-prompt.md`, `principal-review-rules.md`, and `document-triage.md` exist and validate cleanly. (V2, V5)
- `run_external_review.py` supports `--doc <path>` under `--kind principal`. (V2, V5)
- All lint, type checks, and verification rows V1–V5 pass. (V3, V4, V5)

## Dependencies & Blockers

- Blocked by: none.
- Blocks [Task 3](task_3_orchestrators_delegation_refactor.md).

## References & Rollback

- [Epic HLD](split_review_skills.en.md), Module Contracts.
- **Rollback**: Revert task commit.
