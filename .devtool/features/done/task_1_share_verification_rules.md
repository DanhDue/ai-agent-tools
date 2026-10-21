---
id: "task_1_share_verification_rules"
status: "done"
priority: "high"
assignee: null
epic: "local_model_review"
dueDate: null
created: "2026-10-21T09:10:00Z"
modified: "2026-10-21T09:25:55Z"
completedAt: "2026-10-21T09:25:55Z"
labels: ["review", "prompt", "refactor"]
order: "a1"
---

# Task 1: Share Verification Rules Between Review Prompts

Epic: [local_model_review](../epic/local_model_review/local_model_review.en.md)

## Requirement Analysis

The Verification rules live inline in `external-review-prompt.md` (section "Verification Hierarchy &
Process Rules", four rules). Move them into a new `references/review-rules.md`, add the two Gate 4
Semantic Test Integrity rules that the review checklist lacks today ("No Reconstructed Logic",
"Immutable Real Artifacts", worded as in `skills/dev-implementation/SKILL.md` Phase 4), and make the
external prompt insert the file through `$rules`. The local prompt of Task 4 will insert the same
file. Create the epic's test suite `test_local_review.py` with the HP-02 test.

`run_external_review.py` carries three existing ruff findings (EXE001, FURB167 `re.M`, UP017
`timezone.utc`). Fix exactly those three so the TIER-B lint row can pass; no other cleanup.

## Files

Allowed files:
- `skills/dev-implementation/references/review-rules.md` (new)
- `skills/dev-implementation/references/external-review-prompt.md`
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_local_review.py` (new)

Read-only context:
- `skills/dev-implementation/SKILL.md` — Phase 4 "Semantic Test Integrity Governance" wording
- `skills/dev-implementation/resources/scripts/test_run_external_review.py` — fake CLI fixture pattern to copy
- `.devtool/epic/local_model_review/local_model_review.en.md` — Module Contracts

## Design Rationale

One rules file keeps the Claude/Codex prompt and the local prompt identical on rules (spec D11).
The HP-02 test drives the real runner with a fake `claude` on `PATH` that saves its stdin, the same
pattern as `test_run_external_review.py`, in a new file because that suite is a protected path.
Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `run_external_review.run` (prompt substitution), new constant
  `RULES`, `external-review-prompt.md` rules section.
- **Downstream callers**: every Claude CLI and Codex CLI review round; `test_run_external_review.py`
  must still pass unchanged.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: the rendered prompt is asserted for all six rule titles.

### BDD SCENARIOS

Covers: LMR-HP-02

```gherkin
Scenario: [LMR-HP-02] [Tier C - Integration] Shared rules reach the Claude and Codex prompt
  Given a throwaway epic repository and a fake claude on PATH that saves its stdin
  When run_external_review.py run --cli claude records a round
  Then the saved prompt contains "Task-Level vs. Gate 4 Workspace Scope", "No Reconstructed Logic" and "Immutable Real Artifacts"
  And the saved prompt contains no literal "$rules"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k test_lmr_hp_02` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k test_lmr_hp_02` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_1.xml skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0; results build/test-results/task_1.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `test_run_external_review.py` fails after the change: the Claude/Codex prompt must differ only by
  the two added rules.

## Decisions Already Made

- New frozen constant in `run_external_review.py`: `RULES = SCRIPTS.parent.parent / "references" / "review-rules.md"`.
- `run()` passes `rules=RULES.read_text(encoding="utf-8").strip()` to the existing
  `Template(PROMPT.read_text(...)).safe_substitute(...)` call.
- `external-review-prompt.md`: the body of `## Verification Hierarchy & Process Rules` (its intro
  sentence and rules 1–4) moves verbatim into `review-rules.md`; the heading stays and its body
  becomes the single line `$rules`.
- `review-rules.md` has no H1 heading; it is a fragment inserted into a prompt. It holds the intro
  sentence, rules 1–4 unchanged, then rule 5 **No Reconstructed Logic** and rule 6 **Immutable Real
  Artifacts**, each stated as in dev-implementation Phase 4.
- The ruff fixes are exactly: `chmod +x` (EXE001, matching `audit_epic.py` at mode 100755),
  `re.M` → `re.MULTILINE`, `timezone.utc` → `UTC` imported from `datetime`.
- `test_local_review.py` imports only `run_external_review` in this task; it adds its own directory
  to `sys.path` as `test_run_external_review.py` does, and its fake `claude` is the only one on
  `PATH` during the test.

## Definition of Done

- LMR-HP-02 is covered by `test_lmr_hp_02_shared_rules_reach_the_external_prompt` and passes in the
  JUnit report. (V2, V6)
- The existing runner suite passes unchanged. (V3)
- Lint and strict type checking report zero issues on the touched Python files. (V4, V5)
- `review-rules.md` reads as one coherent rules list a reviewer can follow. (Gate 5)

## Dependencies & Blockers

None. Blocks [Task 4](task_4_local_review_prompt_base.md) and [Task 5](task_5_record_round_from_passes.md).

## References & Rollback

- [Epic HLD](../epic/local_model_review/local_model_review.en.md), Module Contracts.
- **Rollback**: revert the commit; the prompt returns to its inline rules.
