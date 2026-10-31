---
id: "task_3_standardize_4_bullet_triage_header"
status: "done"
priority: "high"
assignee: null
epic: "review_triage_standardization"
dueDate: null
created: "2026-10-31T06:00:00Z"
modified: "2026-10-31T06:30:00Z"
completedAt: "2026-10-31T06:30:00Z"
labels: ["review", "triage", "header"]
order: "a3"
---

# Task 3: Standardize 4-Bullet Triage Header

Epic: [review_triage_standardization](review_triage_standardization.en.md)

## Requirement Analysis

The presentation of review triage summaries across `/principal-review` and `/cross-model-review` had small discrepancies in header formatting, reviewer details, and finding counts. Specifically, developer reviews require an immediate, unambiguous executive summary at the very top displaying:
- `• Candidate SHA: <commit_sha>`
- `• Reviewer: <CLI> ( <model> )`
- `• Thinking Level: <Light | Low | Medium | High | Extra High | None>`
- `• Verdict: <VERDICT> (<count> findings)`

Standardize this output by implementing `format_triage_header()` in `run_external_review.py` and updating `triage()`, `run()`, and `run_adhoc_code()`. Maintain backward compatibility by retaining `# Review Triage: <epic>, Round <N>` as the first line and appending `- **Status**: <status>` when non-completed. Synchronize reference documentation across skills.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`
- `skills/cross-model-review/SKILL.md`
- `skills/cross-model-review/references/review-triage.md`
- `skills/principal-review/SKILL.md`
- `skills/principal-review/references/document-triage.md`

Read-only context:
- `.devtool/epic/review_triage_standardization/review_triage_standardization.en.md`
- `.devtool/epic/review_triage_standardization/bdd_scenarios.en.md`

## Design Rationale

A unified 4-bullet header guarantees that human architects and automated agents can parse candidate SHA, active reviewer model, reasoning effort, and verdict with finding counts consistently across all review modes without ambiguity.

### BDD SCENARIOS

Covers: RTS-HP-01, RTS-EC-03, RTS-ST-02

```gherkin
Scenario: [RTS-HP-01] [Tier C - Integration] Triage format renders standardized 4-bullet header
  Given a completed review round in review_results.md
  When triage() formats the summary
  Then output starts with "# Review Triage: <epic>, Round <N>"
  And contains "• Candidate SHA: <sha>"
  And contains "• Reviewer: <cli> ( <model> )"
  And contains "• Thinking Level: <level>"
  And contains "• Verdict: <verdict> (<count> findings)"

Scenario: [RTS-EC-03] [Tier C - Integration] Zero findings in review verdict displays 0 findings
  Given a review round with verdict "PASS" and zero findings
  When format_triage_header() runs
  Then verdict bullet displays "• Verdict: PASS (0 findings)"

Scenario: [RTS-ST-02] [Tier C - Integration] Incomplete review round reflects non-completed status
  Given a review round with status "failed" or "no verdict"
  When triage() renders the summary
  Then "- **Status**: <status>" is appended to the triage output
```

## Verification

RED: n/a — retroactive formalization: implementation and test suite already verified.

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k test_rts_hp_01` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/run-external-review.xml skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; results build/test-results/run-external-review.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Implemented helper `format_triage_header(epic_dir, sha, cli, model, thinking_level, verdict, findings_summary)` in `run_external_review.py`.
- Formatted reviewer as `<Capitalized CLI> ( <model> )`.
- Formatted thinking level as title-cased string (e.g. `High`, `Medium`, `None`).
- Retained title `# Review Triage: <epic>, Round <N>` preceding the bullets for test backwards-compatibility.
- Updated skill guidelines in `cross-model-review` and `principal-review`.

## Definition of Done

- Standardized 4-bullet header is emitted across all triage calls and unit tests pass. (V2)
- Linting and static type checking pass cleanly on modified scripts. (V3, V4)
- JUnit test suite executes cleanly and records valid results. (V5)
- Skill documentation in `cross-model-review` and `principal-review` correctly illustrates the 4-bullet format. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 1](task_1_review_config_and_sticky_defaults.md) and [Task 2](task_2_dynamic_probing_and_senior_review_rules.md).

## References & Rollback

- [Epic HLD](review_triage_standardization.en.md)
- **Rollback**: Revert `format_triage_header()` changes in `run_external_review.py` and skill markdown files.
