# BDD Scenarios: Execution and Verification Infrastructure

## Table of Contents

- [1. Dimension 1 — Happy Paths](#1-dimension-1--happy-paths)
- [2. Dimension 2 — Edge Cases & Boundaries](#2-dimension-2--edge-cases--boundaries)
- [3. Dimension 3 — State Transitions](#3-dimension-3--state-transitions)
- [4. Dimension 4 — Async & Concurrency](#4-dimension-4--async--concurrency)
- [5. Dimension 5 — Failures & Resilience](#5-dimension-5--failures--resilience)

---

## 1. Dimension 1 — Happy Paths

```gherkin
Feature: Execution and Verification Infrastructure — Happy Paths

  Scenario: [EVI-HP-01] [Tier C - Integration] Worktree bootstrap executes python-quality.json bootstrap commands and installs polyglot dependencies
    Given a polyglot git repository containing both "pyproject.toml" and "package.json"
    And ".agents/quality/python-quality.json" defines "bootstrap" as ["pip install -e .[dev]"]
    When "detect_project_type.sh --all" is executed on the repository
    Then it outputs "python web"
    And when "bootstrap_worktree.sh" runs on a worktree of the repository
    Then it executes both the Python bootstrap phase (including the "bootstrap" commands from ".agents/quality/python-quality.json") and the Web dependency installation phase

  Scenario: [EVI-HP-02] [Tier C - Integration] Failure-set baseline recording and regression comparison pass when no new failures appear
    Given a pytest output stream containing 2 pre-existing failed test node IDs in the terminal "=== short test summary info ===" block
    When "record_failure_baseline.py --out baseline.txt" parses the output stream
    Then "baseline.txt" contains the 2 sorted failure node IDs
    And when "compare_failure_sets.py --baseline baseline.txt --current current.txt" runs with a current failure list containing a subset of those 2 node IDs
    Then it reports 0 new failures and exits with code 0

  Scenario: [EVI-HP-03] [Tier C - Integration] Opt-in live integration results satisfy R6 coverage, skip cleanly when env is unset, and execute when env is set
    Given an epic HLD containing both "## Integration results:" and "## Integration results (live, needs: EVI_LIVE_MODEL):"
    And "bdd_scenarios.en.md" declares a "[Tier C - Integration]" scenario mapped only in the live integration table
    When "check_epic_readiness.py" evaluates R6 coverage for the epic
    Then R6 passes with 0 missing Tier C scenarios
    And when "audit_epic.py" evaluates Gate 4 with "EVI_LIVE_MODEL" unset in the environment
    Then the live integration row is reported as "SKIPPED (missing env: EVI_LIVE_MODEL)" and Gate 4 passes
    And when "audit_epic.py" evaluates Gate 4 with "EVI_LIVE_MODEL=1" set in the environment
    Then the live integration row is executed and its exit status is enforced

  Scenario: [EVI-HP-04] [Tier C - Integration] Task text replay engine applies fenced directives in a scratch worktree and MEASURE phase executes and records evidence
    Given a task file containing "Create", "Replace in", and "Insert in" fenced code blocks, "Phase: MEASURE" rows, and "Evidence files: .devtool/evidence/bench.json"
    When "replay_task_text.py" replays the task inside a temporary git worktree
    Then all fenced directives apply cleanly and the task's Verification commands pass
    And when "run_task_checks.py measure" executes the task
    Then the "MEASURE" rows run, create ".devtool/evidence/bench.json", and record a passing "measure" entry in the task's evidence JSON
```

---

## 2. Dimension 2 — Edge Cases & Boundaries

```gherkin
Feature: Execution and Verification Infrastructure — Edge Cases & Boundaries

  Scenario: [EVI-EC-01] [Tier A - Unit] Failure-set parser ignores captured ERROR log lines before short test summary info and writes sentinel on zero failures
    Given a pytest output stream containing captured "ERROR logger:module.py:42" log lines in stdout before "=== short test summary info ==="
    When "record_failure_baseline.py" extracts failure IDs from the output stream
    Then it ignores the captured logger lines and extracts only "FAILED <nodeid>" and "ERROR <nodeid>" lines from the terminal summary block
    And when 0 tests fail or error in the terminal summary block
    Then "record_failure_baseline.py" writes "# 0 failures\n" to the output file so the file is non-empty

  Scenario: [EVI-EC-02] [Tier A - Unit] Task runner automatically creates parent directories for JUnit XML output flags before executing Verification rows
    Given a task Verification row containing "--junitxml=.devtool/evidence/nested/junit/report.xml" where ".devtool/evidence/nested/junit" does not exist
    When "run_task_checks.py" executes the Verification row
    Then "ensure_output_dirs()" creates ".devtool/evidence/nested/junit" prior to invoking the subprocess so the test runner writes the XML report without error

  Scenario: [EVI-EC-03] [Tier A - Unit] R5b route drift check matches concrete route literals against parameterized route templates without false-positive warnings
    Given a task file referencing the concrete route literal "/api/align/stream/job_plt"
    And the target codebase defines the parameterized route "/api/align/stream/{job_id}" (or "<job_id>" or ":job_id")
    When "check_epic_readiness.py" runs the R5b route drift check
    Then "route_matches_codebase()" matches the concrete route against the parameterized template and emits 0 R5b warnings
```

---

## 3. Dimension 3 — State Transitions

```gherkin
Feature: Execution and Verification Infrastructure — State Transitions

  Scenario: [EVI-ST-01] [Tier A - Unit] Failure-set comparison with --rerun-new filters out transient shared-state failures while failing on persistent regressions
    Given a baseline failure file with 0 failures and a current failure file with 2 candidate new failure node IDs
    When "compare_failure_sets.py --baseline baseline.txt --current current.txt --rerun-new" runs
    And the first candidate passes when re-run in isolation via "--rerun-cmd"
    Then the first candidate is reported as a transient shared-state failure and ignored
    And when the second candidate still fails when re-run in isolation
    Then "compare_failure_sets.py" reports the persistent regression and exits with code 1

  Scenario: [EVI-ST-02] [Tier C - Integration] run_task_checks.py measure --resume skips re-running MEASURE rows when prior run passed and declared evidence files exist
    Given a task file with "Phase: MEASURE" rows and "Evidence files: .devtool/evidence/bench.json"
    And a prior "run_task_checks.py measure" execution recorded "runs.measure.passed = true" and created a non-empty ".devtool/evidence/bench.json"
    When "run_task_checks.py measure <task.md> --resume" is invoked
    Then it skips re-executing the "MEASURE" subprocess commands and exits with code 0
```

---

## 4. Dimension 4 — Async & Concurrency

```gherkin
Feature: Execution and Verification Infrastructure — Async & Concurrency

  Scenario: [EVI-AR-01] [Tier C - Integration] check_epic_readiness.py --replay executes task text in an isolated scratch worktree and cleans up without mutating the main tree
    Given an epic whose tasks contain valid "Create", "Replace in", and "Insert in" directives
    When "check_epic_readiness.py <epic> --replay" is executed
    Then it creates a temporary git worktree, replays each task's fenced edits sequentially, runs the Verification commands, and removes the temporary worktree on completion
    And "git status --porcelain" on the main repository remains completely unchanged

  Scenario: [EVI-AR-02] [Tier A - Unit] record_failure_baseline.py --restore restores tracked files dirtied as a side effect of test execution
    Given a test suite command that mutates a tracked file "config/sample.json" during execution
    When "record_failure_baseline.py --cmd '<test_cmd>' --out baseline.txt --restore config/sample.json" runs
    Then after the test command completes, "record_failure_baseline.py" executes "git checkout -- config/sample.json" so the tracked file is restored to its clean HEAD state
```

---

## 5. Dimension 5 — Failures & Resilience

```gherkin
Feature: Execution and Verification Infrastructure — Failures & Resilience

  Scenario: [EVI-FR-01] [Tier A - Unit] validate_python_quality.py rejects malformed bootstrap configurations with invalid_bootstrap_format
    Given a ".agents/quality/python-quality.json" file where "bootstrap" is not a non-empty list of non-empty strings
    When "validate_python_quality.py" validates the configuration
    Then it fails validation and emits an error with code "invalid_bootstrap_format"

  Scenario: [EVI-FR-02] [Tier A - Unit] R5 static anchor verification fails when a Replace in or Insert in anchor is missing or ambiguous in the target file
    Given a task file containing a "Replace in <path>:" or "Insert in <path>:" directive whose anchor text occurs 0 times or 2+ times in "<path>"
    When "verify_task_edit_anchors()" in "check_epic_readiness.py" inspects the task
    Then R5 fails and reports the exact file path and missing or ambiguous anchor snippet

  Scenario: [EVI-FR-03] [Tier A - Unit] evaluate_done_gate fails when a task contains MEASURE rows that have not been executed or did not pass
    Given a task file containing at least one "Phase: MEASURE" Verification row
    And the task's evidence JSON either lacks "runs.measure" or has "runs.measure.passed == false"
    When "evaluate_done_gate()" evaluates the task for transition to "done"
    Then it returns a non-empty failure list blocking the "done" transition until "run_task_checks.py measure" passes
```
