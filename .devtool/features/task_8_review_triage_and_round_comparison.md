---
id: "task_8_review_triage_and_round_comparison"
status: "todo"
priority: "high"
assignee: null
epic: "local_model_review"
dueDate: null
created: "2026-10-21T12:05:00Z"
modified: "2026-10-21T12:05:00Z"
completedAt: null
labels: ["review", "workflow", "triage"]
order: "a8"
---

# Task 8: Triage Review Findings and Compare Rounds

Epic: [local_model_review](../epic/local_model_review/local_model_review.en.md)

## Requirement Analysis

The first review rounds of this epic showed a gap: after a round is recorded, nothing makes the agent
verify each finding, lay the findings out for the developer, and wait for decisions before acting.
Some findings are real, some are false positives, some only say a file was not shown. Add a read-only
`run_external_review.py triage --epic-dir <epic_dir>` that prints a skeleton for the latest round
(passes, findings, a comparison of every round, and what became of the previous round's findings),
a reference that says how to fill it, and the workflow text that requires it for every reviewer:
Claude CLI, Codex CLI and Ollama. A confirmation round after blocking fixes then measures the
improvement through the comparison.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_local_review.py`
- `skills/dev-implementation/references/review-triage.md` (new)
- `skills/dev-implementation/SKILL.md`
- `skills/dev-lifecycle/SKILL.md`
- `rules/CRITICAL_RULES.md`
- `docs/lifecycles.en.md`
- `docs/lifecycles.vi.md`
- `scripts/test_lifecycle_document_contract.py`

Read-only context:
- `skills/receiving-code-review/SKILL.md` — the verification discipline the triage applies
- `.devtool/epic/local_model_review/review_results.md` — real rounds of this epic, the shape triage reads
- `.devtool/epic/local_model_review/local_model_review.en.md` — Module Contracts, Review triage
- `scripts/test_verifiable_handoff_text.py` — Review Choice assertions that must keep passing unchanged

## Design Rationale

The command makes the synthesis mechanical where it can be: no finding is left out, numbering
matches the Decision cells, and the round comparison is computed rather than recalled. Judgement
stays with the agent and the developer: the command never assesses a finding. Paths are compared
without line numbers because a fix moves lines. Triage sits inside the review step, so the
`round recorded` edges and the phrases existing tests assert do not change. Applicable skills:
`d3nexus:receiving-code-review`, `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: new `triage` mode and its helpers in `run_external_review.py`;
  `main` argument parsing; the Review Choice text of both skills and rule 5.
- **Downstream callers**: every review round of every epic, from any reviewer.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: every output section and both exit codes have a named test.

### BDD SCENARIOS

Covers: LMR-HP-08, LMR-HP-09, LMR-HP-10, LMR-EC-10, LMR-EC-11, LMR-ST-04, LMR-FR-08

```gherkin
Scenario: [LMR-HP-08] [Tier C - Integration] Triage lists every finding of the latest round
  Given a recorded round with "[Important] a.py:3 — missing guard" and "[Minor] b.py:5 — wording"
  When run_external_review.py triage --epic-dir demo runs
  Then it exits 0 and prints "# Review Triage: demo, Round 1"
  And its "## Findings" table has rows 1 and 2 with the round's severity, location and problem, and "?" in Assessment, Evidence and Proposed action
  And it ends with a "## Next Steps" section

Scenario: [LMR-HP-09] [Tier C - Integration] The workflow requires triage before acting on findings
  Given skills/dev-implementation/SKILL.md, skills/dev-lifecycle/SKILL.md and rules/CRITICAL_RULES.md
  When the lifecycle contract tests read them
  Then each names "run_external_review.py triage"
  And dev-implementation links references/review-triage.md and waits for the developer's decisions before any Fix commit
  And dev-lifecycle's Red Flags forbid acting on review findings before presenting the triage

Scenario: [LMR-HP-10] [Tier C - Integration] Triage compares every round
  Given a claude Round 1 whose Important finding is decided "fixed in abc1234" and an ollama Round 2 with one Minor finding
  When triage runs
  Then the "## Round Comparison" table has one row per round with CLI / Model, Status, Verdict, Critical, Important, Minor, Fixed, Dismissed and Undecided
  And Round 1 shows Important 1 and Fixed 1, and Round 2 shows Minor 1

Scenario: [LMR-EC-10] [Tier C - Integration] Triage marks passes without a verdict
  Given an ollama round whose pass 2 has no verdict line and whose pass 3 failed with "HTTP 500: boom"
  When triage runs
  Then the "## Passes" table shows pass 2 with verdict "none" and pass 3 with error "HTTP 500: boom"

Scenario: [LMR-EC-11] [Tier C - Integration] A fixed finding reported again at the same path is flagged
  Given Round 1 with "[Important] src/a.py:3 — missing guard" and "[Important] src/b.py:9 — weak", both decided "fixed in abc1234"
  And Round 2 reports "[Minor] src/a.py:40 — still unguarded"
  When triage runs
  Then "## Since Round 1" lists src/a.py:3 as re-reported at the same path with "check the fix"
  And lists src/b.py:9 as not re-reported

Scenario: [LMR-ST-04] [Tier C - Integration] Triage reads the latest round, completed or not
  Given a completed Round 1 and a "no verdict" Round 2
  When triage runs
  Then it prints "Round 2" and Round 2's findings only in its Findings table

Scenario: [LMR-FR-08] [Tier C - Integration] Triage without a review round stops
  Given an epic directory without review_results.md
  When triage runs
  Then it exits 2 and prints "no review round recorded for demo" on stderr
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k TriageTest` | exit 1; contains "FAILED" | — |
| V2 | RED | `python3 -m unittest scripts/test_lifecycle_document_contract.py -k lmr_hp_09` | exit 1; contains "FAILED" | — |
| V3 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k TriageTest` | exit 0; contains "OK" | — |
| V4 | GREEN | `python3 -m unittest scripts/test_lifecycle_document_contract.py` | exit 0; contains "OK" | — |
| V5 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; contains "OK" | — |
| V6 | GREEN | `python3 -m unittest scripts/test_verifiable_handoff_text.py` | exit 0; contains "OK" | — |
| V7 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_local_review.py scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V8 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_local_review.py scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V9 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py --require-bilingual docs/lifecycles.en.md docs/lifecycles.vi.md` | exit 0 | — |
| V10 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-implementation/references/review-triage.md` | exit 0 | — |
| V11 | TIER-B | `bash scripts/verify.sh` | exit 0 | — |
| V12 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/local-model-review.xml skills/dev-implementation/resources/scripts/test_local_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py scripts/test_lifecycle_document_contract.py scripts/test_verifiable_handoff_text.py` | exit 0; results build/test-results/local-model-review.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `skills/dev-lifecycle/SKILL.md` would exceed 2,500 words, or an existing assertion of
  `test_verifiable_handoff_text.py` would need to change.
- Mapping a finding to its pass would need a new column in the findings table: `check` reads exactly
  five cells.

## Decisions Already Made

- New mode `triage` of `run_external_review.py`: `triage --epic-dir <epic_dir>`, handled by a new
  `def triage(args: argparse.Namespace) -> int`. It only reads `review_results.md` and prints
  Markdown to stdout. With no file or no round it prints `no review round recorded for <epic_dir>`
  to stderr and returns 2; otherwise it returns 0.
- It reads the latest round from `rounds_in`, whatever its status. Findings come from
  `table_findings`, numbered as in the file; `check`, `rounds_in`, `metadata`, `table_findings` and
  the findings table format do not change.
- Output sections, in order:
  - `# Review Triage: <epic_dir>, Round <n>`, then `- **SHA**`, `- **CLI**`, `- **Model**`,
    `- **Status**` and `- **Verdict**` lines copied from the round's metadata.
  - `## Passes`: table `| Pass | Verdict | Error |`. Passes are the `### Pass <n>: <label>` blocks of
    the round's raw output, or one pass `review` when it has none. Verdict is the block's last
    `VERDICT` match, else `none`; Error is the first line after `--- error ---`, else `—`.
  - `## Findings`: table `| # | Severity | Location | Problem | Assessment | Evidence | Proposed action |`
    with the round's number, severity, location and problem, and `?` in the last three cells.
  - `## Round Comparison`: table `| Round | CLI / Model | SHA | Status | Verdict | Critical | Important | Minor | Fixed | Dismissed | Undecided |`,
    one row per round in order. SHA is the first 7 characters. Fixed counts decisions starting
    `fixed in `, Dismissed those starting `dismissed: `, Undecided the Critical or Important findings
    with neither.
  - `## Since Round <n-1>` when an earlier round exists, else `## Since the Previous Round` with
    `No earlier round.`: one bullet per previous finding that was Critical, Important or fixed,
    `- <location>: re-reported at the same path (#k[, #m])` with ` — check the fix` appended when it
    was fixed, or `- <location>: not re-reported`. The path is the location before its first `:`,
    without backticks.
  - `## Next Steps` with the line
    `To be written after verifying every finding: Fix commits, decisions, a confirmation round, then Gate 4 in full.`
- `references/review-triage.md` holds the procedure: run triage; verify every finding at the round's
  SHA with the discipline of `d3nexus:receiving-code-review`; assess each as Valid, Debatable, False
  positive or Not shown; give the file and line checked, with a quote, as Evidence; propose `fix`,
  `dismiss: <reason>` or `none`; read the Passes table for slices that were never reviewed; read the
  comparison and Since sections for improvement or regression; write Next Steps, recommending a
  confirmation round after blocking fixes; then stop until the developer decides each finding. After
  the decisions: Fix commits titled `[EPIC_NAME] Fix <what>`, Decision cells `fixed in <sha>` or
  `dismissed: <the developer's reason>`, a commit, and Phase 4 in full.
- `skills/dev-implementation/SKILL.md`: after every round of option 2 or 3, run
  `run_external_review.py triage --epic-dir <epic_dir>`, fill it as
  `references/review-triage.md` says, present it, and wait for the developer's decisions before any
  Fix commit or Decision cell.
- `skills/dev-lifecycle/SKILL.md`: the Review Choice loop names the triage, and Red Flags add
  "Acting on review findings before presenting the triage from `run_external_review.py triage`."
- `rules/CRITICAL_RULES.md` rule 5, item 3, adds: before any Fix commit or decision, the agent
  presents the triage from `run_external_review.py triage` and waits for the developer's decisions.
- `docs/lifecycles.en.md` and `.vi.md` add one sentence to the Gate 4 paragraph: every review round
  is triaged with the developer before any fix. Diagram edges do not change.
- New tests: `TriageTest` in `test_local_review.py`, and
  `test_lmr_hp_09_the_workflow_requires_triage_before_acting_on_findings` in
  `test_lifecycle_document_contract.py`.

## Definition of Done

- All seven covered scenarios have a `test_lmr_*` test and pass in the epic's JUnit report. (V3, V4, V12)
- The existing runner suite and Review Choice assertions pass unchanged. (V5, V6)
- Lint and strict type checking report zero issues on the touched Python files. (V7, V8)
- The changed documents pass the document checker, and `scripts/verify.sh` passes. (V9, V10, V11)
- The triage of the next review round of this epic, filled and presented, lets the developer decide
  each finding without opening `review_results.md`. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 7](task_7_review_choice_workflow_and_acceptance.md)

## References & Rollback

- [Epic HLD](../epic/local_model_review/local_model_review.en.md), Review triage.
- **Rollback**: revert the commit; review rounds keep working without the triage step.
