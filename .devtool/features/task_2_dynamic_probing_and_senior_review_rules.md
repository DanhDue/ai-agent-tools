---
id: "task_2_dynamic_probing_and_senior_review_rules"
status: "done"
priority: "high"
assignee: null
epic: "review_triage_standardization"
dueDate: null
created: "2026-10-31T06:00:00Z"
modified: "2026-10-31T06:30:00Z"
completedAt: "2026-10-31T06:30:00Z"
labels: ["review", "prompts", "rules"]
order: "a2"
---

# Task 2: Dynamic Probing Mandate and Senior Review Rules

Epic: [review_triage_standardization](../epic/review_triage_standardization/review_triage_standardization.en.md)

## Requirement Analysis

Static code inspection alone misses insidious runtime defects such as unbound variables in fallback exception blocks, morphological stemmer deformations, and database flush ordering violations. When reviewing code, Claude CLI previously ran under `--permission-mode plan`, which restricted active bash execution, and review prompts lacked an explicit mandate forcing reviewers to dynamically probe critical code paths.

Upgrade the review harness and prompts:
1. Configure Claude CLI with `--dangerously-skip-permissions` instead of `--permission-mode plan`, enabling safe read-only probing while strictly enforcing zero repository modification via `tree_changes(root, before, sha)`.
2. Insert `## Mandatory Dynamic Probing Rule` into `external-review-prompt.md` and `principal-review-prompt.md`.
3. Embed the `5-Layer Deep Verification Checklist` into `review-rules.md` and `principal-review-rules.md` in English.

## Files

Allowed files:
- `skills/dev-implementation/references/external-review-prompt.md`
- `skills/dev-implementation/references/review-rules.md`
- `skills/principal-review/references/principal-review-prompt.md`
- `skills/principal-review/references/principal-review-rules.md`
- `skills/dev-implementation/resources/scripts/run_external_review.py`

Read-only context:
- `.devtool/epic/review_triage_standardization/review_triage_standardization.en.md`
- `.devtool/epic/review_triage_standardization/bdd_scenarios.en.md`

## Design Rationale

Active probing transforms AI reviewers from passive document readers into active verification engines capable of testing edge cases via quick REPL commands (`python3 -c ...`). Preserving `tree_changes` ensures that if any command accidentally mutates the working tree, the round is aborted immediately.

### BDD SCENARIOS

Covers: RTS-HP-05, RTS-HP-06, RTS-FR-01

```gherkin
Scenario: [RTS-HP-05] [Tier C - Integration] Claude CLI receives dangerously-skip-permissions
  When cli_command is constructed for "claude"
  Then arguments include "--dangerously-skip-permissions"
  And arguments do not include "--permission-mode plan"

Scenario: [RTS-HP-06] [Tier C - Integration] Mandatory dynamic probing rule and 5-layer senior verification rules are present in prompts
  Given review prompts and rules
  When external-review-prompt.md, principal-review-prompt.md, review-rules.md and principal-review-rules.md are checked
  Then prompt files contain "## Mandatory Dynamic Probing Rule"
  And rule files contain "5-Layer Deep Verification Checklist"

Scenario: [RTS-FR-01] [Tier C - Integration] Tree change guard aborts if reviewer modifies working tree
  Given a reviewer CLI process that mutates or creates a file in the repository
  When tree_changes(root, before, sha) runs post-execution
  Then review execution detects modified paths and rejects the round
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k test_claude_thinking_level_arguments` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k test_claude_thinking_level_arguments` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/run_external_review.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/run_external_review.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/run-external-review.xml skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; results build/test-results/run-external-review.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Claude CLI execution command replaced `--permission-mode plan` with `--dangerously-skip-permissions`.
- Dynamic probing rule mandates at least 3 active read-only probes for exception branches, regex, NLP transformations, and ORM persistence.
- Added 5-layer senior verification checklist: (1) Unbound Variable in Fallback, (2) Part-of-Speech Ambiguity, (3) ORM Flush Semantics, (4) Interactive Contract Boundary, (5) Fixture Schema Sanity.
- All prompt additions and rules are authored in English.

## Definition of Done

- Claude CLI execution switches to `--dangerously-skip-permissions` with verified test assertions. (V2)
- Linting and static type checking pass cleanly on `run_external_review.py`. (V3, V4)
- JUnit test suite passes cleanly with generated report. (V5)
- Prompts and rule files contain clear dynamic probing instructions and the 5-layer checklist. (Gate 5)

## Dependencies & Blockers

None. Blocks [Task 3](../epic/review_triage_standardization/task_3_standardize_4_bullet_triage_header.md).

## References & Rollback

- [Epic HLD](../epic/review_triage_standardization/review_triage_standardization.en.md)
- **Rollback**: Restore previous prompt templates and revert CLI flags in `run_external_review.py`.
