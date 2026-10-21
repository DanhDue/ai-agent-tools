---
id: "task_5_record_round_from_passes"
status: "done"
priority: "high"
assignee: null
epic: "local_model_review"
dueDate: null
created: "2026-10-21T09:10:00Z"
modified: "2026-10-21T09:37:51Z"
completedAt: "2026-10-21T09:37:51Z"
labels: ["review", "refactor", "review-results"]
order: "a5"
---

# Task 5: Record One Round From Many Passes

Epic: [local_model_review](../epic/local_model_review/local_model_review.en.md)

## Requirement Analysis

`run()` today parses one CLI output and appends one round. Extract that into
`record_round(root, args, sha, passes, changed, extra)` over a list of `Pass` values, so a local
review of N passes still writes one round. The Claude CLI and Codex CLI become a single pass and
must write the same round byte for byte; the existing runner suite proves it. Rules that apply only
when `args.cli == "ollama"`: findings come from each pass's last `Verdict:` line onward, unseen
blocking locations are annotated, a pass needs `done_reason == "stop"`, raw output carries a header
per pass, and metadata gains `Passes`, `Context` and `Omitted`.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_local_review.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/test_run_external_review.py` — the guard that must pass unchanged
- `.devtool/epic/local_model_review/local_model_review.en.md` — Module Contracts

## Design Rationale

Refactor first, with the existing suite as the guard, then add the local path on top in Task 6.
`check` stays untouched: a local round is an ordinary round, so decisions, numbering and "latest
completed round governs" work unchanged (spec D12). Applicable skills:
`d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: new `Pass` and `record_round`; `run` delegates to it;
  `parse_findings`, `render_round`, `rounds_in` and `check` are reused unchanged.
- **Downstream callers**: every review round written by the runner.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: each ollama-only rule has a named test; the CLI path is
  guarded by the whole existing suite.

### BDD SCENARIOS

Covers: LMR-EC-08, LMR-EC-09, LMR-ST-01, LMR-ST-02, LMR-FR-05, LMR-FR-06

```gherkin
Scenario: [LMR-EC-08] [Tier C - Integration] A draft finding in Analysis is not a finding
  Given an ollama pass whose out is "## Analysis\n- [Critical] a.py:1 — draft\nVerdict: PASS" with code 0 and done_reason "stop"
  When record_round runs
  Then the round has no findings row, "- **Status**: completed" and "- **Verdict**: PASS"
  And record_round returns 0

Scenario: [LMR-EC-09] [Tier C - Integration] Dropped files reach the round metadata
  Given an ollama pass "task_1" with omitted ("big.py",) and an epic pass with nothing omitted
  When record_round runs
  Then the round shows "- **Omitted**: task_1: big.py"

Scenario: [LMR-ST-01] [Tier C - Integration] A blocking local finding holds check until decided
  Given a recorded ollama round with "[Important] lib/a.py:3 — missing guard" where lib/a.py was shown
  When check runs
  Then it exits 1 and prints "undecided: #1 Important lib/a.py:3"
  And after the Decision cell becomes "dismissed: false positive" check exits 0

Scenario: [LMR-ST-02] [Tier C - Integration] Round numbering is shared across reviewers
  Given review_results.md already holds a completed Claude "## Round 1" with an undecided Critical finding
  When an ollama round with no finding is recorded
  Then it is "## Round 2" with "- **CLI**: ollama"
  And check exits 0 because only the latest completed round governs it

Scenario: [LMR-FR-05] [Tier C - Integration] Truncated output is no verdict
  Given an ollama pass with code 0, done_reason "length" and out "Verdict: PASS"
  When record_round runs
  Then the round has "- **Status**: no verdict"
  And record_round returns 2

Scenario: [LMR-FR-06] [Tier C - Integration] A blocking finding at an unseen path is annotated
  Given an ollama pass whose shown text never contains "ghost.py" and whose out is "Verdict: CHANGES REQUIRED\n[Critical] ghost.py:9 — broken\n[Important] seen.py:2 — weak"
  When record_round runs
  Then the ghost.py row keeps Severity "Critical" and its Problem ends with "(location not shown to reviewer)"
  And the seen.py row, whose path was shown, is not annotated
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k RoundTest` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k RoundTest` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_5.xml skills/dev-implementation/resources/scripts/test_local_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; results build/test-results/task_5.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Keeping the Claude/Codex round byte-identical would need a change to `check`, `rounds_in` or the
  existing suite.

## Decisions Already Made

- `@dataclass(frozen=True) class Pass: label: str; code: int | None; out: str; err: str; shown: str; omitted: tuple[str, ...] = (); done_reason: str | None = None`.
  `code` is 0 for transport success, `None` for a timeout, anything else for a failure; `out` is the
  text the parser reads; `shown` is what the reviewer was shown.
- `def record_round(root: Path, args: argparse.Namespace, sha: str, passes: list[Pass], changed: list[str], extra: dict[str, str]) -> int`
  appends one round to `.devtool/epic/<args.epic_dir>/review_results.md`, prints
  `Round <n>: <status> (<path>)` as today, and returns 0, 1 or 2 by today's rules. `changed` is the
  list `run()` already computes for "discarded: tree modified".
- For the Claude CLI and Codex CLI, `run()` builds one `Pass("review", code, out, err, shown=prompt)`
  and `extra={}`; the round text, status and exit code are byte-identical to today's.
- Only when `args.cli == "ollama"`:
  - findings of a pass are parsed from its last line matching `VERDICT` to the end of `out`;
  - a pass completes only with `code == 0`, `done_reason == "stop"`, a verdict, and a finding
    behind `CHANGES REQUIRED`; the round completes only when every pass completes;
  - the round verdict is `CHANGES REQUIRED` when any pass says so, `PASS` when every pass has a
    verdict and none says `CHANGES REQUIRED`, otherwise `none`;
  - a Critical or Important finding whose location path (the text before the first `:`, with
    backticks removed) does not occur in `Pass.shown` gets ` (location not shown to reviewer)`
    appended to its Problem; Severity never changes;
  - raw output is each pass as `### Pass <n>: <label>` followed by its `out`, then its `err` under
    `--- error ---` when non-empty;
  - metadata after `Verdict` adds `extra` in order; `Omitted` is added only when some pass has
    `omitted`, formatted `<label>: <name>, <name>` joined by `; `.
- `check`, `rounds_in`, `metadata`, `table_findings` and `render_round` keep their behaviour.

## Definition of Done

- All six covered scenarios have a `test_lmr_*` method in `RoundTest` and pass in the JUnit
  report. (V2, V6)
- The existing runner suite passes unchanged. (V3, V6)
- Lint and strict type checking report zero issues on the touched Python files. (V4, V5)

## Dependencies & Blockers

Blocked by [Task 1](task_1_share_verification_rules.md)

Blocks [Task 6](task_6_wire_local_review_into_runner.md).

## References & Rollback

- [Epic HLD](../epic/local_model_review/local_model_review.en.md), Module Contracts.
- **Rollback**: revert the commit; `run()` returns to inline recording.
