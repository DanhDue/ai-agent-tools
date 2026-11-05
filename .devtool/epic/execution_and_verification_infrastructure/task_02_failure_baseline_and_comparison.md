---
id: "task_02_failure_baseline_and_comparison"
status: "backlog"
priority: "high"
assignee: null
epic: "execution-and-verification-infrastructure"
dueDate: null
created: "2026-11-06T03:20:00Z"
modified: "2026-11-06T03:20:00Z"
completedAt: null
labels: ["infrastructure", "testing", "baseline"]
order: "b2"
---

# Task 02: Failure-Set Baseline Recording and Regression Comparison CLI

Epic: [execution_and_verification_infrastructure](execution_and_verification_infrastructure.en.md)

## Requirement Analysis

Resolve Observation #0007: when an epic executes on a repository that has pre-existing full-suite test failures or when tasks verify that no new regressions were introduced across a test suite, hand-written bash pipelines in Verification rows repeatedly fail due to five failure modes:
1. Matching captured application log lines (`ERROR logger:module.py:42`) instead of terminal `pytest` summary lines.
2. Producing empty files (`0` bytes) when 0 tests fail (`grep` exits 1 under `pipefail`).
3. Leaving tracked files dirtied by side-effecting tests.
4. Reporting false-positive regressions caused by shared test state (e.g., shared SQLite/Postgres state across test modules) that pass when re-run in isolation.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/record_failure_baseline.py` (new)
- `skills/dev-implementation/resources/scripts/compare_failure_sets.py` (new)
- `skills/dev-implementation/resources/scripts/test_failure_baseline.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/run_task_checks.py` (subprocess execution conventions)
- `.devtool/epic/execution_and_verification_infrastructure/execution_and_verification_infrastructure.en.md` (HLD specification)

## Design Rationale

Applicable skills: `python-quality-check`, `test-driven-development`.
1. `record_failure_baseline.py` parses only the terminal `=== short test summary info ===` section of `pytest` output (or `# fail` / `not ok` / `✖` summary lines from `node --test`), extracting canonical `FAILED <nodeid>` and `ERROR <nodeid>` identifiers (preserving spaces inside parameterized `[...]` brackets) and sorting/deduplicating them. It distinguishes valid test completions (`exit 0` with summary footer or `exit 1`/`2` with short test summary info) from runner launch/usage/internal errors (`exit 3`, `4`, `5`, `127`, or non-zero exit without a summary block), failing with exit code `2` without writing a baseline on invalid runs. When 0 failures occur in a valid run, it writes `# 0 failures\n` so output files are always non-empty. When `--restore <path>` is passed, it runs `git checkout -- <path>` in a `finally:` block after the test command finishes.
2. `compare_failure_sets.py` loads baseline and current failure sets (or executes `<command...>` directly), computes `new_failures = sorted(current - baseline)`, and when `--rerun-new` is passed, re-executes each candidate new failure node ID as a single positional argument (`[*rerun_cmd_argv, node_id]`). Candidates that pass in isolation are classified as `ISOLATED_PASS` while those that still fail are classified as `PERSISTENT_FAILURE`; both cause exit code `1` by default so order-dependent state-pollution regressions are never masked, unless `--allow-isolated-pass` is explicitly provided.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/record_failure_baseline.py`: new `extract_pytest_failures`, new `extract_node_failures`, new `record_baseline`, and new `main`.
  - `skills/dev-implementation/resources/scripts/compare_failure_sets.py`: new `load_failure_set`, new `compare_failure_sets`, and new `main`.
- **Downstream Callers**: Task Verification rows in `dev-designer` and `dev-implementation`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on `record_failure_baseline.py` and `compare_failure_sets.py`.

### BDD SCENARIOS

Covers: EVI-HP-02, EVI-EC-01, EVI-ST-01, EVI-AR-02

```gherkin
  Scenario: [EVI-HP-02] [Tier C - Integration] Failure-set baseline recording and regression comparison pass when no new failures appear
    Given a pytest output stream containing 2 pre-existing failed test node IDs in the terminal "=== short test summary info ===" block
    When "record_failure_baseline.py --out baseline.txt" parses the output stream
    Then "baseline.txt" contains the 2 sorted failure node IDs
    And when "compare_failure_sets.py --baseline baseline.txt --current current.txt" runs with a current failure list containing a subset of those 2 node IDs
    Then it reports 0 new failures and exits with code 0

  Scenario: [EVI-EC-01] [Tier A - Unit] Failure-set parser ignores captured ERROR log lines before short test summary info and writes sentinel on zero failures
    Given a pytest output stream containing captured "ERROR logger:module.py:42" log lines in stdout before "=== short test summary info ==="
    When "record_failure_baseline.py" extracts failure IDs from the output stream
    Then it ignores the captured logger lines and extracts only "FAILED <nodeid>" and "ERROR <nodeid>" lines from the terminal summary block
    And when 0 tests fail or error in the terminal summary block
    Then "record_failure_baseline.py" writes "# 0 failures\n" to the output file so the file is non-empty

  Scenario: [EVI-ST-01] [Tier A - Unit] Failure-set comparison with --rerun-new classifies isolated-pass vs persistent failures and requires explicit opt-in to ignore isolated passes
    Given a baseline failure file with 0 failures and a current failure file with 2 candidate new failure node IDs (including a parameterized ID with spaces)
    When "compare_failure_sets.py --baseline baseline.txt --current current.txt --rerun-new" runs
    And the first candidate passes when re-run in isolation via "--rerun-cmd" while the second candidate fails
    Then the first candidate is classified as "ISOLATED_PASS" and the second as "PERSISTENT_FAILURE" and the command exits with code 1
    And when all candidates pass in isolation, "compare_failure_sets.py --rerun-new" still exits with code 1 unless "--allow-isolated-pass" is explicitly provided

  Scenario: [EVI-AR-02] [Tier A - Unit] record_failure_baseline.py --restore restores tracked files dirtied as a side effect of test execution
    Given a test suite command that mutates a tracked file "config/sample.json" during execution
    When "record_failure_baseline.py --cmd '<test_cmd>' --out baseline.txt --restore config/sample.json" runs
    Then after the test command completes, "record_failure_baseline.py" executes "git checkout -- config/sample.json" so the tracked file is restored to its clean HEAD state
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_failure_baseline.py::test_EVI_HP_02_record_and_compare_baseline` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_failure_baseline.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/record_failure_baseline.py skills/dev-implementation/resources/scripts/compare_failure_sets.py skills/dev-implementation/resources/scripts/test_failure_baseline.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent skills/dev-implementation/resources/scripts/record_failure_baseline.py skills/dev-implementation/resources/scripts/compare_failure_sets.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_failure_baseline.py --junitxml=build/test-results/task_02_baseline.xml` | exit 0; results build/test-results/task_02_baseline.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `record_failure_baseline.py` CLI interface:
  `record_failure_baseline.py --output|--out <baseline_file> [--cmd <shell_cmd>] [--in <raw_output_file>] [--runner auto|pytest|node] [--restore <path> ...] [--cwd <dir>] [-- <command...>]`
  - Accepts both `--output` and `--out` for the output file path, and either `--cmd <shell_cmd>`, `-- <command...>`, `--in <file>`, or stdin.
  - When executing a command (`--cmd` or `-- <command...>`), automatically appends `--continue-on-collection-errors` for `pytest` if absent, and validates runner completion: for `pytest`, exit code `0` must include a terminal `=== ... ===` summary footer and exit code `1`/`2` must include `=== short test summary info ===` (rejecting exit codes `3`, `4`, `5`, `126`, `127`, or missing summary blocks with exit code `2` and no baseline file written); for `node`, output must include TAP/spec summary lines (`# tests` or `ℹ tests`).
  - `extract_pytest_failures(output_text: str) -> list[str]` scans lines after the last `=== short test summary info ===` header up to the next `===...===` footer line, matching `^(?:FAILED|ERROR)\s+(.+?)(?:\s+-\s+.*)?$` so parameterized node IDs containing spaces (`tests/test_x.py::test_x[hello world]`) are preserved intact while stripping trailing ` - <reason>` suffixes.
  - `extract_node_failures(output_text: str) -> list[str]` extracts failing test names from `node --test` summary lines (`not ok <n> - <name>` or `✖ <name>`).
  - Writes sorted unique node IDs (one per line) to `--output`/`--out` (creating parent directories if needed), or `# 0 failures\n` when 0 tests fail in a valid run.
  - Always restores any `--restore` paths via `git checkout -- <path>` inside a `finally:` block even when the runner fails.
- `compare_failure_sets.py` CLI interface:
  `compare_failure_sets.py --baseline <file> [--current <file>] [--output|--out <report_file>] [--runner auto|pytest|node] [--rerun-new] [--allow-isolated-pass] [--rerun-cmd <cmd_prefix>] [--restore <path> ...] [--cwd <dir>] [-- <command...>]`
  - Reads `baseline_set` from `--baseline` and `current_set` either from `--current <file>` or by running `-- <command...>` via `record_failure_baseline`'s validated runner and `--restore` logic.
  - Computes `new_failures = sorted(current_set - baseline_set)`.
  - If `--rerun-new` is active and `new_failures` is non-empty, runs `[*shlex.split(rerun_cmd), node_id]` (`shell=False`, defaulting `--rerun-cmd` to `"python3 -m pytest"`) for each candidate so spaces in parameterized node IDs are passed as a single argument:
    - Candidates exiting `0` are logged as `ISOLATED_PASS: <nodeid>`.
    - Candidates exiting non-zero are logged as `PERSISTENT_FAILURE: <nodeid>`.
    - Exits `0` only when `persistent_failures` is empty AND (`isolated_passes` is empty OR `--allow-isolated-pass` is set); otherwise exits `1`.
- In `test_failure_baseline.py`, import `record_failure_baseline` and `compare_failure_sets` inside test functions or helper functions so `pytest` collection succeeds during the `RED` phase before the implementation files exist.

## Definition of Done

- `record_failure_baseline.py` extracts failure node IDs strictly from the terminal summary block, writes `# 0 failures\n` when empty, and restores `--restore` paths after execution. (V2, V5)
- `compare_failure_sets.py` compares current vs baseline failure sets and filters transient shared-state failures with `--rerun-new`. (V2, V5)
- `ruff` and `mypy` pass with zero errors. (V3, V4)
- All 4 BDD scenarios (`EVI-HP-02`, `EVI-EC-01`, `EVI-ST-01`, `EVI-AR-02`) pass and emit JUnit XML results. (V5)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- None (Wave 1).

## References & Rollback

- Reference: [2026-11-06-execution-and-verification-infrastructure-design.en.md](2026-11-06-execution-and-verification-infrastructure-design.en.md).
- Rollback: `git revert` the task commit to remove `record_failure_baseline.py`, `compare_failure_sets.py`, and `test_failure_baseline.py`.
