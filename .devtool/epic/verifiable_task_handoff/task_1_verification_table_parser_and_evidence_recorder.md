---
id: "task_1_verification_table_parser_and_evidence_recorder"
status: "done"
priority: "high"
assignee: null
epic: "verifiable_task_handoff"
dueDate: null
created: "2026-10-16T06:53:44Z"
modified: "2026-10-16T07:33:00Z"
completedAt: "2026-10-16T07:33:00Z"
labels: ["scripts", "evidence"]
order: "a1"
---

# Task 1: Verification table parser and evidence recorder

Epic: [verifiable_task_handoff](verifiable_task_handoff.en.md)

## Requirement Analysis

Build the shared parser every later task imports, the recorder that writes evidence, and a JUnit
runner for `unittest` files. The authority is the source spec
`.devtool/epic/verifiable_task_handoff/2026-10-16-verifiable-task-handoff-design.en.md`, sections 5,
6 and 8; everything this task needs from it is restated below.

### task_contract.py (new)

`skills/dev-implementation/resources/scripts/task_contract.py`, Python 3 standard library only:

- `ContractError(Exception)`: a task file or HLD the parser cannot accept; the message names the row
  or section.
- Frozen dataclasses: `Expect(exit_code: int | None, nonzero: bool, contains: tuple[str, ...],
  results: str | None)`, `Row(id, phase, command, expect_text, expect: Expect, needs: tuple[str, ...])`,
  `AllowedPath(pattern: str, new: bool)`, `EpicLayout(root, epic_dir, hld, scenarios, evidence)`.
- `section(text, title) -> str | None`: the body under `## <title>` up to the next `## ` heading.
  Headings inside fenced code blocks do not count.
- `parse_expect(text) -> Expect`, for this grammar; anything else raises `ContractError`:

  ```text
  expect := exit-clause ( "; " clause )*
  exit-clause := "exit " DIGITS | "exit non-zero"
  clause := "contains \"" TEXT "\"" | "results " PATH
  ```

  TEXT contains no double quote; `results` appears at most once.
- `parse_verification(task_text) -> tuple[list[Row], str | None]`: the rows of the table under
  `## Verification`, and the reason of a `RED: n/a — <reason>` line (`—` or `-`), else `None`.
  The header is exactly `| ID | Phase | Command | Expect | Needs |`. The Command cell is exactly one
  inline code span, and `\|` inside it becomes `|`. Needs is `—` or `-` for none, otherwise
  comma-separated names matching `[A-Z_][A-Z0-9_]*`. Phase is one of `RED`, `GREEN`, `TIER-B`,
  `TIER-C`. A missing section or header, a duplicate ID or a malformed cell raises `ContractError`.
- `parse_allowed_files(task_text) -> list[AllowedPath]`: the bullets ``- `path` `` or
  ``- `path` (new)`` following the line `Allowed files:` inside `## Files`, up to the first line
  that is not such a bullet.
- `parse_protected_paths(hld_text) -> list[str]`: the comma-separated entries of the line starting
  `Protected paths:`; an empty list when there is none.
- `path_matches(pattern, path) -> bool`: `**` spans directories, `*` and `?` stay within one path
  segment, anything else must match exactly.
- `program_of(command, root) -> str | None`: shell-split the command and stop at the first `&&`,
  `||`, `;` or `|` token. Drop the wrappers `uv run`, `poetry run`, `npx`, `fvm`, and `env` with its
  `NAME=value` tokens. If the first token is `python`, `python3`, `bash`, `sh`, `zsh`, `node`, `deno`,
  `ruby` or `perl`, the candidate is its first argument not starting with `-`, and `-m` or `-c` means
  there is none; otherwise the candidate is the first token without a leading `./`. Return the
  candidate only when `git ls-files --error-unmatch` says it is tracked.
- `epic_layout(task_file) -> EpicLayout`: for `<root>/.devtool/epic/<epic_dir>/task_*.md`, with
  `root` from `git rev-parse --show-toplevel`: `hld` is `<epic_dir>.en.md`, `scenarios` is
  `bdd_scenarios.en.md`, `evidence` is `evidence/<task file stem>.json`, all in that directory. Any
  other path raises `ContractError("pass the task's mirror under .devtool/epic/<epic_dir>/")`.
- `fingerprint(root) -> tuple[str, str | None]`: in a temporary index (`GIT_INDEX_FILE` pointing into
  a temporary directory), run `git read-tree HEAD`, `git add -A -- . ':(exclude).devtool'`,
  `git write-tree` for the tree, and `git diff --cached HEAD -- . ':(exclude).devtool'` piped into
  `git patch-id --stable` for the patch id, which is `None` when the diff is empty. The real index is
  never touched.
- `changed_paths(root) -> list[str]`: every path in `git status --porcelain=v1 -z --untracked-files=all`,
  both sides of a rename included.
- `load_evidence(path) -> dict | None` and `save_evidence(path, data)`: JSON with a two-space indent
  and a trailing newline; `save_evidence` creates the directory.

### run_task_checks.py (new)

`skills/dev-implementation/resources/scripts/run_task_checks.py`:

```bash
python3 skills/dev-implementation/resources/scripts/run_task_checks.py red    <task mirror> [--timeout 1800]
python3 skills/dev-implementation/resources/scripts/run_task_checks.py verify <task mirror> [--timeout 1800]
```

- `red` runs the RED rows; a task with `RED: n/a` or no RED row exits 2. `verify` runs every
  `GREEN`, `TIER-B` and `TIER-C` row in table order, never stopping early, then adds a `SCOPE` row.
- Each row runs as `["bash", "-o", "pipefail", "-c", command]` with `cwd=root`, stdout and stderr
  combined, `start_new_session=True`; on timeout the process group is killed.
- Outcomes: `PASS` when the exit code and every `contains` text match; `FAIL` otherwise, or on
  timeout (`reason: "timeout after N s"`), or when a `results` path is not fresh; `BLOCKED`, without
  running, when a `Needs` variable is unset or empty (`reason: "unset: NAME"`).
- Freshness: the `results` path, relative to root, is a file or a directory. Its newest modification
  time — of the file, or of the newest `*.xml` or `*.json` under the directory — must not be earlier
  than the row's start time. Otherwise the row fails with `reason: "results not produced by this run"`.
  The row stores `"results": {"path": <path>, "fresh": <bool>}`; Task 2 adds a digest.
- `SCOPE`: from `changed_paths`, ignore paths under `.devtool/` unless protected. Every other path
  must match an Allowed files pattern (`outside Allowed files: <path>`). A protected path — an entry
  of the HLD's `Protected paths:` line, matched with `path_matches`, or the `program_of` any row of
  any `task_*.md` in the epic directory that parses — must equal a non-glob Allowed files entry
  exactly (`protected path not named exactly in Allowed files: <path>`).
- The evidence file holds `{"schema": 1, "task": <stem>, "runs": {"red": ..., "verify": ...}}`. Each
  run holds `head`, `tree`, `patch_id`, `started`, `finished` (UTC ISO-8601) and `rows`. A row holds
  `id`, `phase`, `command`, `expect` (the cell text as written), `needs`, `exit` (`null` when not
  run), `outcome`, `reason` (`null` on PASS), `started`, `finished`, `output_tail` (last 40 lines),
  `output_sha256`, and `results` when the row has one. The `SCOPE` row holds `id: "SCOPE"`,
  `phase: "SCOPE"`, `outcome`, `changed` and `violations`. A run replaces the previous run of the
  same kind.
- Output: one line per row, `<id> <phase> <outcome> <detail>`, then `Result: PASS` or
  `Result: FAIL`, and the evidence path. Exit 0 when every row passes, 1 otherwise (evidence still
  written), 2 for usage errors or a `ContractError`, in which case no evidence is written.

### scripts/run_unittest_junit.py (new)

```bash
python3 scripts/run_unittest_junit.py --junitxml <path> <test file> [<test file> ...]
```

For each file: put its directory first on `sys.path`, import it under a unique module name with
`importlib.util`, load it with `unittest.defaultTestLoader`, and run everything with a text runner
whose result records each test's outcome. Write JUnit XML to `<path>`, creating parent directories:
`<testsuites>` holding one `<testsuite>` per file with `tests`, `failures`, `errors` and `skipped`
counts, and one `<testcase classname="<module>.<Class>" name="<method>" time="...">` per test with a
`<failure>`, `<error>` or `<skipped>` child when relevant. A file that fails to import becomes one
`<testcase name="import">` with an `<error>`. Exit 0 when every test passed or was skipped, 1
otherwise.

### Also

- `.gitignore`: add the line `build/`.
- `scripts/verify.sh`, section 11: add
  `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_task_checks.py || FAILED=1`
  and `python3 -m unittest scripts/test_run_unittest_junit.py || FAILED=1`.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/task_contract.py` (new)
- `skills/dev-implementation/resources/scripts/run_task_checks.py` (new)
- `skills/dev-implementation/resources/scripts/test_run_task_checks.py` (new)
- `scripts/run_unittest_junit.py` (new)
- `scripts/test_run_unittest_junit.py` (new)
- `.gitignore`
- `scripts/verify.sh`

Read-only context:
- `.devtool/epic/verifiable_task_handoff/2026-10-16-verifiable-task-handoff-design.en.md` — sections 5, 6 and 8
- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` — style, `UsageError` and exit-code conventions
- `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py` — test style with temporary git repositories

## Design Rationale

- One parser module, so the contract check, recorder, gate and audit read task files identically.
- The recorder writes evidence; nothing else may. The agent never writes JSON by hand.
- Tests build throwaway git repositories with `tempfile` and call `main()`; fixtures use a small
  fake epic whose rows are shell one-liners such as `test -f feature.txt`.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: the new module and scripts above; `.gitignore`; `scripts/verify.sh`.
- **Downstream callers**: Tasks 2–8 import `task_contract.py` and run the recorder and the runner.
- **Cross-platform bridges**: none.
- **Target test coverage threshold**: every function of `task_contract.py` exercised by
  `test_run_task_checks.py`; every outcome of the runner by `test_run_unittest_junit.py`.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: VTH-HP-02, VTH-EC-05, VTH-ST-02, VTH-FR-01, VTH-FR-05

Test methods are named `test_vth_hp_02_…`, `test_vth_ec_05_…`, `test_vth_st_02_…`, `test_vth_fr_01_…`
and `test_vth_fr_05_…` in `test_run_task_checks.py`. The scenarios, from the epic's
`bdd_scenarios.en.md`:

```gherkin
Scenario: [VTH-HP-02] [Tier C - Integration] Red then verify on a correct change records passing evidence
  Given an epic worktree with a task whose RED row fails before the change and whose GREEN row passes after it
  When run_task_checks.py red runs, the change is made, and run_task_checks.py verify runs
  Then both commands exit 0
  And the evidence file holds both runs with head, tree, patch_id, every row's outcome PASS and its output tail
  And the verify run ends with a SCOPE row that is PASS

Scenario: [VTH-EC-05] [Tier C - Integration] A row whose Needs variable is unset is blocked, not run
  Given a TIER-C row whose Needs column names TEST_DATABASE_URL
  And TEST_DATABASE_URL is unset
  When run_task_checks.py verify runs
  Then the row is BLOCKED and its command is never executed
  And the run exits 1 with the evidence written

Scenario: [VTH-ST-02] [Tier C - Integration] Scope rejects a change outside Allowed files or to a protected program
  Given a task whose Allowed files lists "scripts/**"
  And a Verification row that runs the tracked program "scripts/verify_coverage.py"
  When the change edits a file outside Allowed files and edits "scripts/verify_coverage.py"
  And run_task_checks.py verify runs
  Then the SCOPE row is FAIL and names both files
  And the protected program is reported as not named exactly in Allowed files

Scenario: [VTH-FR-01] [Tier C - Integration] A slow row and a stale report fail closed
  Given a row whose command runs longer than the timeout
  And a TIER-C row whose results file was written before the row started
  When run_task_checks.py verify runs with a short --timeout
  Then the slow row is FAIL with a timeout reason
  And the TIER-C row is FAIL with "results not produced by this run"

Scenario: [VTH-FR-05] [Tier C - Integration] A task file the parser rejects writes no evidence
  Given a task file whose Verification table has no Expect column
  When run_task_checks.py verify runs
  Then it exits 2 with the parse error on stderr
  And no evidence file is created
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_task_checks.py scripts/test_run_unittest_junit.py` | exit 0; contains "OK" | — |
| V2 | TIER-B | `git check-ignore -q build/test-results/task_1.xml` | exit 0 | — |
| V3 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
| V4 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_1.xml skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0; results build/test-results/task_1.xml | — |
| V5 | TIER-C | `python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py tests --scenarios .devtool/epic/verifiable_task_handoff/bdd_scenarios.en.md --roots skills/dev-implementation/resources/scripts/ --ids VTH-HP-02 VTH-EC-05 VTH-ST-02 VTH-FR-01 VTH-FR-05` | exit 0; contains "Result: 5/5 covered — PASS" | — |

RED: n/a — bootstrap: this task builds run_task_checks.py, which cannot record a RED run before it exists.

## Definition of Done

- `task_contract.py` and `run_task_checks.py` behave as specified, and the five covered scenarios pass (V1, V4, V5).
- The JUnit runner reports passed, failed, errored, skipped and unimportable tests correctly (V1).
- `build/` is ignored and `scripts/verify.sh` passes with both new test files wired in (V2, V3).
- This task's own `verify` run is recorded in `evidence/task_1_verification_table_parser_and_evidence_recorder.json` by the recorder it built, and that file is in the task commit (Gate 5).

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- The installed git lacks `patch-id --stable`, `check-ignore` or the `:(exclude)` pathspec.

## Decisions Already Made

- Python 3 standard library only; there is no `pytest` in this repository.
- Evidence lives at `.devtool/epic/<epic_dir>/evidence/<task_id>.json`, schema 1, written only by the recorder.
- `.devtool/` is excluded from `tree`, `patch_id` and Allowed-files matching, never from the protected-path check.
- The recorder accepts only a task's mirror under `.devtool/epic/<epic_dir>/`.
- The results digest belongs to Task 2; this task records only `path` and `fresh`.
- Test fixtures use identifiers with the `DEMO-` prefix; only test method names carry `VTH-` identifiers.
- After the last change, run `run_task_checks.py verify` on this task's mirror and commit the evidence with the code.

## Dependencies & Blockers

- None.

## References & Rollback

- Source spec sections 5, 6 and 8; HLD section 4.5, items 2, 4 and 5.
- Rollback: revert this task's commit. Nothing else imports the new files yet.
