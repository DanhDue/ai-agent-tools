---
id: "task_2_readiness_grounding_and_baseline"
status: "done"
priority: "high"
assignee: null
epic: "principal_review"
dueDate: null
created: "2026-10-22T09:10:00Z"
modified: "2026-10-23T09:48:05Z"
completedAt: "2026-10-23T09:48:05Z"
labels: ["readiness", "grounding", "gate-4"]
order: "a2"
---

# Task 2: Readiness Grounding, Gate 4 Coverage and Baseline

Epic: [principal_review](principal_review.en.md)

## Requirement Analysis

Fill the three checks Task 1 registered empty:
- **R5**: every symbol a task's `Target Files & Symbols` lists for an existing, non-new file occurs in that file.
- **R5b** (WARN): every `/api/` route the tasks or the HLD name occurs in tracked source.
- **R6**: every task with a `Covers:` line has a `TIER-C` row, and every test path in a `TIER-C` row is run by an `Integration results:` command.
- **R8** (opt-in `--baseline`): the epic's existing `GREEN` and `TIER-B` rows run in the current checkout, and failures and timeouts are reported as warnings.

These are the checks that would have caught the nonexistent `buildPersistTrackPayload`, the
unpassable Gate 4 and the baseline Node failures in the lyrics-sync review.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py` (new)
- `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/run_task_checks.py` — `run_command(command, root, timeout)`, `mismatch(row, code, text)`
- `skills/dev-implementation/resources/scripts/task_contract.py` — `section()`, `parse_allowed_files()`, `parse_verification()`, `Row`, `AllowedPath`
- `.devtool/epic/principal_review/principal_review.en.md` — Module Contracts, rules R5, R5b, R6, R8

## Design Rationale

R5 fails only on explicit `path: symbol` pairs, so it never guesses at prose. Routes stay WARN
because a route can legitimately live in a config file or a generated table. R6 reasons about the
same tokens Gate 4 will run, so an epic that passes R6 cannot reach Gate 4 with a scenario that
has no result. R8 reuses `run_task_checks.py`'s own execution and Expect matching, so a baseline
warning means exactly what a failing row would mean during implementation.
Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/check_epic_readiness.py`: `check_grounding()`, `check_gate4_coverage()`, `check_baseline()`
- **Downstream Callers**: `run_checks()` (Task 1), the Principal Review precondition (Task 3).
- **Cross-Platform Bridges**: none.
- **Target Test Coverage Threshold**: every rule branch of R5, R5b, R6 and R8 has a named test.

### BDD SCENARIOS

Covers: PRV-EC-01, PRV-EC-03, PRV-EC-06, PRV-FR-01

```gherkin
Scenario: [PRV-EC-01] [Tier C - Integration] A symbol missing from its file fails R5
  Given the PRV-HP-01 epic whose task_2 lists "- `src/app.py`: `build_payload()`, new `render()`" under Target Files & Symbols
  And src/app.py exists without the text "build_payload"
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R5 FAIL" that contains "task_2", "build_payload" and "src/app.py"
  And no R5 line mentions "render"
  And the last line ends "— FAIL" and the exit code is 1

Scenario: [PRV-EC-03] [Tier C - Integration] A TIER-C test outside every Integration results command fails R6
  Given the PRV-HP-01 epic whose task_2 TIER-C row runs "python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml tests/test_extra.py"
  And the HLD's only Integration results command names "tests/test_core.py"
  And "tests/" is an Integration test roots directory
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R6 FAIL" containing "task_2" and "tests/test_extra.py"
  And the exit code is 1

Scenario: [PRV-EC-06] [Tier C - Integration] A route found in no source file warns R5b without failing
  Given the PRV-HP-01 epic whose task_1 names "/api/tts/ocr-upload" and whose only tracked source names "/api/studio/extract/start"
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R5b WARN" containing "/api/tts/ocr-upload"
  And no line mentions "/api/studio/extract/start"
  And the last line is "Result: 0 FAIL, 1 WARN — PASS" and the exit code is 0

Scenario: [PRV-FR-01] [Tier C - Integration] Baseline failures and timeouts warn and the other rows still run
  Given the PRV-HP-01 epic in a clean tree whose task_1 has rows V2 GREEN "python3 -c 'raise SystemExit(1)'" expecting "exit 0", V3 TIER-B "sleep 5" expecting "exit 0", and V4 GREEN "python3 -c 'print(1)'" expecting "exit 0"
  And task_2 has a GREEN row whose command names a path marked (new)
  When check_epic_readiness.py demo_epic --baseline --row-timeout 2 runs
  Then the output has a line starting "R8 WARN" containing "task_1:V2"
  And a line starting "R8 WARN" containing "task_1:V3" and "timeout"
  And no R8 line mentions "task_1:V4" or task_2's row
  And the exit code is 0
  When the tree has an uncommitted change and the same command runs
  Then the output has the line "R8 WARN baseline skipped: dirty tree"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k ReadinessGroundingTest` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` | exit 0; results build/test-results/task_2.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `build_ready_epic` stops passing once R5, R6 or R8 are real: fix the fixture, never weaken a rule.
- `run_task_checks.run_command` or `mismatch` would need a different signature.

## Decisions Already Made

- **R5** (`check_grounding(ctx) -> list[Finding]`):
  - in each task, take the `Impact Analysis & Blast Radius` section and its bullet whose label is `Target Files & Symbols` or `Target files and symbols`, case-insensitive;
  - read its sub-bullets matching ``^\s*-\s+`([^`]+)`:\s*(.*)$``;
  - check a path only if it exists under `root` and that task's `parse_allowed_files()` does not mark it `new`;
  - for each backticked token in the rest of the line that matches `[A-Za-z_][\w.]*(?:\(\))?`, unless it is preceded by the word `new` and whitespace, strip `()` and keep the text after the last `.`;
  - that name must occur in the file text. Otherwise the finding is `R5 FAIL <task file>: <name> not in <path>`.
- **R5b** (WARN, same function):
  - routes match `(?<![\w/])/api/[\w\-/{}.:]*[\w}]` in every task file and the HLD; each is cut at its first `{` and stripped of a trailing `/`;
  - search the files `git ls-files` lists, outside `.devtool/` and `docs/` and not ending in `.md`;
  - a route found nowhere is `R5b WARN <route>: not found in tracked source`, reported once per route.
- **R6** (`check_gate4_coverage(ctx) -> list[Finding]`):
  - a task with a `Covers:` line and no `TIER-C` row is `R6 FAIL <task file>: Covers without a TIER-C row`;
  - for each `TIER-C` row, a `shlex.split` token is a test path when it starts with one of `ctx.roots`;
  - a test path is covered when some `ctx.results` command, split the same way, contains the same token, or a token ending in `/` that the path starts with;
  - an uncovered path is `R6 FAIL <task file>:<row id>: <path> is in no Integration results command`.
- **R8** (`check_baseline(ctx) -> list[Finding]`):
  - when `ctx.baseline` is false, return `[]`; the report prints `R8 SKIP`;
  - when `git status --porcelain` is non-empty, return exactly one `R8 WARN baseline skipped: dirty tree`;
  - otherwise, for every task in file order and every row with Phase `GREEN` or `TIER-B` whose command contains no path any epic task marks `new`:
    - run `run_task_checks.run_command(row.command, ctx.root, ctx.row_timeout)`;
    - a `None` code is `R8 WARN <task stem>:<row id> timeout after <row_timeout>s`;
    - otherwise a non-`None` `run_task_checks.mismatch(row, code, text)` is `R8 WARN <task stem>:<row id> <mismatch text>`;
  - with no warning, the report prints `R8 PASS`.
- `run_task_checks` is imported as a module from the same directory, as `run_external_review.py` imports `local_review`.

## Definition of Done

- All four covered scenarios have a `test_prv_*` method in `ReadinessGroundingTest` and pass in the JUnit report. (V2, V5)
- `ReadinessCoreTest` from Task 1 still passes, including PRV-HP-01 with R5, R6 and R8 real. (V2)
- Lint and strict type checking report zero issues on both files. (V3, V4)

## Dependencies & Blockers

- Blocked by [Task 1](task_1_readiness_check_core.md)
- Blocks [Task 3](task_3_principal_review_runner_mode.md).

## References & Rollback

- [Epic HLD](principal_review.en.md), Module Contracts.
- Spec: [2026-10-22-principal-review-design.en.md](2026-10-22-principal-review-design.en.md), §5.1.
- **Rollback**: revert the commit; R5, R6 and R8 fall back to Task 1's empty results.
