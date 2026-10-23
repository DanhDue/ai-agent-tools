---
id: "task_5_principal_review_choice_and_acceptance"
status: "done"
priority: "high"
assignee: null
epic: "principal_review"
dueDate: null
created: "2026-10-22T09:10:00Z"
modified: "2026-10-23T10:20:58Z"
completedAt: "2026-10-23T10:20:58Z"
labels: ["lifecycle", "docs", "acceptance"]
order: "a5"
---

# Task 5: Principal Review Choice in the Lifecycle, and Acceptance

Epic: [principal_review](../epic/principal_review/principal_review.en.md)

## Requirement Analysis

This is the final Tier C task. It wires Tasks 1–4 into the workflow the agents follow.

- **`dev-lifecycle`**:
  - its packaging step 1 becomes the single `check_epic_readiness.py` command;
  - a new step 8 offers **Principal Review Choice**;
  - the full loop lives in a new `references/principal-review.md`;
  - Red Flags names the two new mistakes.
- **`dev-implementation`**: checks `principal_review.md` before Gate 3.
- **Handoff template**: lists `principal_review.md` under Read First.
- **Both `docs/lifecycles.*.md`**: draw the loop.
- **Contract tests and `scripts/verify.sh`**: pin all of it, and the acceptance rows run every
  suite of the epic and the full pre-release check.

`dev-lifecycle/SKILL.md` stands at 2454 of its 2500-word ceiling. Replacing the four preflight
commands with one frees the words the pointer needs.

## Files

Allowed files:
- `skills/dev-lifecycle/SKILL.md`
- `skills/dev-lifecycle/references/principal-review.md` (new)
- `skills/dev-lifecycle/references/handoff-template.md`
- `skills/dev-implementation/SKILL.md`
- `docs/lifecycles.en.md`
- `docs/lifecycles.vi.md`
- `scripts/test_lifecycle_document_contract.py`
- `scripts/verify.sh`

Read-only context:
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py` (new) — the command step 1 runs (Tasks 1–2)
- `skills/dev-implementation/resources/scripts/run_external_review.py` — `--kind principal` (Task 3)
- `skills/dev-implementation/references/review-triage.md` — the triage the loop presents
- `scripts/test_lifecycle_signals.py` — pins the handoff staleness command (`test_lf_st_02`) and queued packaging
- `scripts/test_verifiable_handoff_text.py` — pins the Review Choice transitions and the handoff guardrails
- `.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md` — §6, the loop procedure
- `.devtool/epic/principal_review/principal_review.en.md` — Workflow text contract, clarifications C2–C4

## Design Rationale

The runtime skill only points; the reference holds the procedure, as `review-triage.md` does for
Review Choice. Both skills keep their pinned tokens, so every earlier epic's contract tests stay
green. The handoff staleness command is not touched: the Done rule (C3) re-packages instead, so
the command stays exact.
Applicable skills: `d3nexus:writing-skills`, `d3nexus:doc_quality_check`, `d3nexus:test-driven-development`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/test_lifecycle_document_contract.py`: `EXPECTED`, new `PrincipalReviewWorkflowTest`
  - `scripts/verify.sh`: the unit-test list
- **Downstream Callers**: every session that packages an epic or starts Gate 3, in every project with the plugin installed.
- **Cross-Platform Bridges**: none.
- **Target Test Coverage Threshold**: every covered scenario has a named test; every changed document passes the linter.

### BDD SCENARIOS

Covers: PRV-HP-04, PRV-EC-07, PRV-ST-03, PRV-ST-04

```gherkin
Scenario: [PRV-HP-04] [Tier C - Integration] Packaging runs one readiness command and offers Principal Review Choice
  Given skills/dev-lifecycle/SKILL.md and skills/dev-lifecycle/references/principal-review.md
  Then the skill contains "check_epic_readiness.py <epic_dir>", "Principal Review Choice" and "references/principal-review.md"
  And the skill no longer contains "check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks"
  And the skill has at most 2500 words and keeps every pinned dev-lifecycle token
  And the reference contains "1. **Done**", "2. **Principal Review**", "Claude CLI", "Codex CLI", "Never choose for the developer" and "strongly recommended"

Scenario: [PRV-EC-07] [Tier C - Integration] Read First lists principal_review.md
  Given skills/dev-lifecycle/references/handoff-template.md
  Then its Read First section contains ".devtool/epic/<epic_dir>/principal_review.md, when present"
  And it keeps "`git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>`" unchanged

Scenario: [PRV-ST-03] [Tier C - Integration] The loop returns to Package and Done re-packages after a round
  Given docs/lifecycles.en.md, docs/lifecycles.vi.md and skills/dev-lifecycle/references/principal-review.md
  Then both documents contain 'PKG --> PRC', 'PRC -->|"2. Principal Review"| PR' and 'PR -->|"revised and re-packaged"| PKG'
  And neither document has an edge from PR to S3 or to G3
  And the reference contains "Record Principal Review round <n>", "Revise epic after Principal Review round <n>" and "Package epic for handoff"
  And the reference states that Done runs "check --kind principal" and re-packages when the last commit touching the epic directory is not the Package commit

Scenario: [PRV-ST-04] [Tier C - Integration] Gate 3 stops while a blocking principal finding is undecided
  Given skills/dev-implementation/SKILL.md
  Then Entry-Point Detection contains "run_external_review.py check --kind principal --epic-dir <epic_dir>"
  And Phase 1 step 3 and Resume Gate 3 both mention "Principal Review" with "not run", "round <n>: PASS" and "round <n>: decided"
  And the skill has at most 4500 words
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest scripts/test_lifecycle_document_contract.py -k PrincipalReviewWorkflowTest` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest scripts/test_lifecycle_document_contract.py` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest scripts/test_lifecycle_signals.py` | exit 0; contains "OK" | — |
| V4 | GREEN | `python3 -m unittest scripts/test_verifiable_handoff_text.py` | exit 0; contains "OK" | — |
| V5 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc --require-bilingual docs/lifecycles.en.md docs/lifecycles.vi.md` | exit 0 | — |
| V6 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-lifecycle/SKILL.md skills/dev-implementation/SKILL.md skills/dev-lifecycle/references/principal-review.md skills/dev-lifecycle/references/handoff-template.md` | exit 0 | — |
| V7 | TIER-B | `ruff check scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V8 | TIER-B | `mypy --strict --follow-imports=silent scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V9 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
| V10 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_5.xml skills/dev-implementation/resources/scripts/test_check_epic_readiness.py skills/dev-implementation/resources/scripts/test_run_external_review.py skills/dev-implementation/resources/scripts/test_sync_task_status.py scripts/test_lifecycle_document_contract.py scripts/test_lifecycle_signals.py scripts/test_verifiable_handoff_text.py` | exit 0; results build/test-results/task_5.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `dev-lifecycle/SKILL.md` cannot reach 2500 words or fewer without removing a pinned token.
- A pinned token or transition in `test_lifecycle_signals.py` or `test_verifiable_handoff_text.py` would have to change.

## Decisions Already Made

- **`dev-lifecycle/SKILL.md`, packaging procedure**:
  - step 1 becomes `1. **Preflight, read-only.** Must exit 0: \`python3 "$SCRIPTS"/check_epic_readiness.py <epic_dir>\`. Its first line gives the task count.`;
  - step 2 keeps "`<N>` is the task count the preflight printed";
  - step 7 becomes `Print \`handoff.md\` path and rendered Resume Prompt.`;
  - new step 8: `8. Present **Principal Review Choice** — follow [references/principal-review.md](references/principal-review.md).`;
  - Red Flags gains `- Picking the Principal Review CLI for the developer.` and `- Acting on a Principal Review finding before triage.`;
  - the file stays at 2500 words or fewer. If it does not, trim prose that repeats the Review Choice transitions, never a token in `EXPECTED` or in the two signal suites.
- **`dev-lifecycle/references/principal-review.md`** (new):
  - steps 1–7 of the spec's §6 in order, with:
    - the choice text `1. **Done** — stop here.` and `2. **Principal Review** — a cross-model review of the design against the source before implementation (Claude CLI or Codex CLI).`;
    - the sentence `Never choose for the developer.`;
    - the D2 recommendation including the words `strongly recommended`, judged from the HLD's `Author` line or the developer's word;
    - the commands `run_external_review.py run --kind principal --epic-dir <epic_dir> --base <base_branch> --cli <claude|codex>`, `triage --kind principal` and `check --kind principal`;
  - the commit titles `[EPIC_NAME] Record Principal Review round <n>`, `[EPIC_NAME] Record Principal Review decisions for round <n>` and `[EPIC_NAME] Revise epic after Principal Review round <n>` (C2);
  - the Done rule: run `check --kind principal`, which must exit 0. Then re-run the packaging procedure when `git log -1 --format=%s -- .devtool/epic/<epic_dir>` is not `[<EPIC_NAME>] Package epic for handoff` (C3). Then print the handoff path and the Resume Prompt and stop;
  - it ends by pointing at `../../dev-implementation/references/review-triage.md` for how to fill the triage.
- **`dev-implementation/SKILL.md`**:
  - Entry-Point Detection's read-only signals gain `test -f .devtool/epic/<epic_dir>/principal_review.md && python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --kind principal --epic-dir <epic_dir>`;
  - Phase 1 step 3 (Gate 3) and Resume Procedure step 4 (Gate 3, resume) each state the Principal Review status, `not run`, `round <n>: PASS` or `round <n>: decided`, and stop with the triage when that check exits 1;
  - the file stays at 4500 words or fewer.
- **`handoff-template.md`**:
  - Read First gains `4. \`.devtool/epic/<epic_dir>/principal_review.md\`, when present — Principal Review rounds and decisions.`;
  - the staleness command `git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>` is unchanged.
- **`docs/lifecycles.en.md` and `docs/lifecycles.vi.md`, Stage 2 diagram**:
  - the terminal `PKG([...])` node becomes `PKG["Package epic<br/>handoff.md, status Packaged"]`;
  - add `PRC{"Principal Review Choice<br/>Done or Principal Review?"}` and `PR["run_external_review.py run --kind principal<br/>triage, decisions, revision"]`;
  - add the edges `PKG --> PRC`, `PRC -->|"1. Done"| PKGSTOP(["Stop: handoff.md and Resume Prompt"])`, `PRC -->|"2. Principal Review"| PR` and `PR -->|"revised and re-packaged"| PKG`;
  - add one paragraph after the Routing & Handoff Choice bullet. The Vietnamese node labels may be translated; the edge labels are kept verbatim.
- **`scripts/test_lifecycle_document_contract.py`**:
  - `EXPECTED["skills/dev-lifecycle/SKILL.md"]` gains `"check_epic_readiness.py <epic_dir>"`, `"Principal Review Choice"` and `"references/principal-review.md"`;
  - new class `PrincipalReviewWorkflowTest(unittest.TestCase)` has one `test_prv_*` method per covered scenario.
- **`scripts/verify.sh`**: add `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py || FAILED=1` beside the other `dev-implementation` suites.

## Definition of Done

- All four covered scenarios have a `test_prv_*` method in `PrincipalReviewWorkflowTest` and pass in the JUnit report. (V2, V10)
- Every earlier lifecycle and handoff contract test passes unchanged. (V2, V3, V4)
- Every changed or new document lints clean, and both lifecycle documents keep their bilingual structure. (V5, V6)
- The contract test file lints and type-checks clean, and the full pre-release check passes. (V7, V8, V9)
- Every suite of the epic passes together in one JUnit report. (V10)
- Run against a packaged epic the developer chooses (for example lyrics-sync's `flashcard_compact_data_enrichment` at `5cc7d720` in a scratch worktree), `check_epic_readiness.py` produces a report the developer judges accurate and useful. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 3](task_3_principal_review_runner_mode.md)
- Blocked by [Task 4](task_4_epic_status_sync_scope.md)
- Blocks: none (final integration and acceptance task).

## References & Rollback

- [Epic HLD](../epic/principal_review/principal_review.en.md), Workflow text and Clarifications of the Spec.
- Spec: [2026-10-22-principal-review-design.en.md](../epic/principal_review/2026-10-22-principal-review-design.en.md), §5.4–§5.7 and §6.
- **Rollback**: revert the commit; packaging falls back to the four preflight commands and Principal Review is no longer offered.
