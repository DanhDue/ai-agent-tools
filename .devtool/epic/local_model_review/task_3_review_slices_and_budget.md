---
id: "task_3_review_slices_and_budget"
status: "todo"
priority: "high"
assignee: null
epic: "local_model_review"
dueDate: null
created: "2026-10-21T09:10:00Z"
modified: "2026-10-21T09:10:00Z"
completedAt: null
labels: ["review", "ollama", "context-budget"]
order: "a3"
---

# Task 3: Build and Fit Review Slices

Epic: [local_model_review](local_model_review.en.md)

## Requirement Analysis

A local model cannot open files, so each pass must carry what it judges. Add to `local_review.py`
the slicing half of the HLD contract: one slice per task commit plus one epic slice, each rendered
as a user message under fixed headings, and a `fit` that drops droppable parts until the message
fits a token budget. Tests build a throwaway epic repository: a base commit, then an epic directory
with HLD, spec, `bdd_scenarios.en.md` and task mirrors, task commits that each add code and an
`evidence/<task_id>.json`, and an optional commit outside tasks.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/local_review.py` (new)
- `skills/dev-implementation/resources/scripts/test_local_review.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/audit_epic.py` — `load_commits` and the evidence-commit rule
- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` — `covers_of`
- `skills/dev-implementation/resources/scripts/run_external_review.py` — `EXCLUDES`, passed in by the caller
- `.devtool/epic/local_model_review/local_model_review.en.md` — Module Contracts

## Design Rationale

One commit per task makes the task commit the natural slice. The evidence-commit rule is the one
`audit_epic.py` already uses, so a slice and the audit agree on which commit belongs to which task.
Token estimates deliberately run high for code (bytes divided by 3). Applicable skills:
`d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `local_review.Slice`, `build_slices`, `estimate_tokens`, `fit`,
  `render_user`, constants `PROMPT_SHARE`, `BYTES_PER_TOKEN`, `TAIL_LINES`.
- **Downstream callers**: `render_system` (Task 4) reads `Slice.kind` and `Slice.paths`; the runner
  (Task 6) calls `build_slices`, `fit` and `render_user`.
- **Cross-platform bridges**: None; Git is read through `task_contract.git_run`.
- **Target test coverage threshold**: each heading, the drop order and the never-cut error are asserted.

### BDD SCENARIOS

Covers: LMR-HP-04, LMR-EC-03, LMR-EC-04, LMR-EC-06

```gherkin
Scenario: [LMR-HP-04] [Tier C - Integration] A task slice carries everything the reviewer may judge
  Given a task commit whose task file says "Covers: DEMO-HP-01" and whose evidence verify row has 40 output_tail lines
  When build_slices and render_user run
  Then the user message has "## Task file", "## Scenarios covered", "## Evidence" and "## Diff of <short sha>" in that order
  And "## Scenarios covered" holds the Gherkin block of DEMO-HP-01 and no other scenario
  And the evidence row shows exactly the last 15 of the 40 output lines
  And the diff holds no path under ".devtool/"

Scenario: [LMR-EC-03] [Tier C - Integration] An oversized task diff drops its largest file first
  Given a task commit that adds 9000 bytes to "big.py" and 300 bytes to "small.py"
  When fit runs with a budget that fits everything except the big.py diff
  Then the user message keeps the small.py diff and drops the big.py diff
  And "## Not shown" lists "big.py"
  And the fitted slice's omitted is ("big.py",)

Scenario: [LMR-EC-04] [Tier C - Integration] Never-cut content larger than the budget
  Given a task slice whose task file alone estimates to more than 1000 tokens
  When fit runs with a budget of 1000
  Then it raises LocalReviewError naming the task id and "raise --num-ctx"

Scenario: [LMR-EC-06] [Tier C - Integration] A legacy task joins the epic slice
  Given one task commit with evidence and one commit that changes "src/legacy.py" without touching any evidence file
  When build_slices runs
  Then it returns one task slice followed by the epic slice
  And the epic slice's "## Commits outside tasks" holds the src/legacy.py diff
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k SliceTest` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k SliceTest` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/local_review.py skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/local_review.py skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_3.xml skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0; results build/test-results/task_3.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Reusing `covers_of` or `task_contract.git_run` would require changing those modules.

## Decisions Already Made

- Frozen constants: `PROMPT_SHARE = 0.6`, `BYTES_PER_TOKEN = 3`, `TAIL_LINES = 15`.
- `@dataclass(frozen=True) class Slice` exposes `label: str` (task id or `"epic"`), `kind: str`
  (`"task"` or `"epic"`), `paths: tuple[str, ...]` (changed paths shown in its diffs) and
  `omitted: tuple[str, ...]` (names dropped by `fit`, in drop order). Further fields are private.
- `def estimate_tokens(text: str) -> int`: `math.ceil(len(text.encode("utf-8")) / BYTES_PER_TOKEN)`.
- `def build_slices(root: Path, epic_dir: str, base: str, sha: str, audit_output: str, results_output: str, excludes: tuple[str, ...]) -> list[Slice]`:
  - A task slice exists for each `.devtool/epic/<epic_dir>/evidence/<task_id>.json` at `sha`; its
    commit is `git log -1 --format=%H <base>..<sha> -- <evidence path>`, as in `audit_epic.py`.
    Task slices follow `git rev-list --reverse <base>..<sha>` order; the epic slice is last.
  - Task file: `.devtool/epic/<epic_dir>/<task_id>.md`. Covered IDs:
    `check_bdd_traceability.covers_of(path)`. A scenario block runs from the `Scenario` line
    carrying `[<ID>]` up to the next `Scenario` line or the closing fence.
  - Evidence: for each of the runs `red` and `verify` present, one line per row with `id`, `phase`,
    `command`, `expect`, `exit`, `outcome`, then the last `TAIL_LINES` lines of `output_tail` in a
    `text` fence.
  - Diff: `git diff <commit>^ <commit> -- . <excludes>`, split into one droppable part per file at
    each `diff --git` line. `excludes` is supplied by the caller and contains `:(exclude).devtool/**`.
  - Epic slice: every `*-design.en.md` in the epic directory as the spec, `<epic_dir>.en.md` as the
    HLD, `audit_output`, `results_output`, `git diff --stat <base>...<sha> -- . :(exclude).devtool/**`,
    and one droppable part per commit outside tasks: a commit in `<base>..<sha>` that is no task
    commit and changes a path outside `.devtool/`, shown with `excludes` applied.
- `def render_user(slice_: Slice) -> str` writes, for a task slice, `## Task file`,
  `## Scenarios covered`, `## Evidence`, `## Diff of <short sha>`, `## Not shown`; for the epic
  slice, `## Spec`, `## HLD`, `## Audit`, `## Traceability`, `## Diff stat`,
  `## Commits outside tasks`, `## Not shown`. A dropped part disappears from its section and its name
  is listed under `## Not shown`; `## Not shown` reads `None.` when nothing was dropped. Bodies that
  may contain backticks get a fence longer than their longest backtick run.
- `def fit(slice_: Slice, budget_tokens: int) -> Slice` returns a slice whose
  `estimate_tokens(render_user(...)) <= budget_tokens`. A task slice drops file diffs largest first;
  the epic slice drops the commits outside tasks, then the spec, then the HLD. When the slice with
  every droppable part removed still exceeds the budget, it raises
  `LocalReviewError(f"{label} needs {n} tokens of never-cut content but the budget is {budget}; raise --num-ctx")`.

## Definition of Done

- All four covered scenarios have a `test_lmr_*` method in `SliceTest` and pass in the JUnit
  report. (V2, V5)
- Tests run against throwaway Git repositories only. (V2)
- Lint and strict type checking report zero issues. (V3, V4)

## Dependencies & Blockers

None. Blocks [Task 6](task_6_wire_local_review_into_runner.md).

## References & Rollback

- [Epic HLD](local_model_review.en.md), Module Contracts.
- **Rollback**: revert the commit; nothing calls the slicing functions yet.
