# BDD Scenarios: Lifecycle Follow-ups

## Table of Contents

- [1. Overview and Boundary Matrix](#1-overview-and-boundary-matrix)
- [2. UC-1 The Traceability Script Reads Coverage Faithfully](#2-uc-1-the-traceability-script-reads-coverage-faithfully)
- [3. UC-2 Resuming an Epic Reads Truthful Signals](#3-uc-2-resuming-an-epic-reads-truthful-signals)
- [4. UC-3 Packaging Records What the Receiver Needs](#4-uc-3-packaging-records-what-the-receiver-needs)
- [5. UC-4 Skill Text States the Rules](#5-uc-4-skill-text-states-the-rules)

## 1. Overview and Boundary Matrix

The behavioural contract for the `lifecycle_followups` epic. Every scenario carries an `LF-` identifier and
needs at least one automated integration test under the HLD's integration test roots that names it.

| Dimension | Scenarios | Guarantee |
|-----------|-----------|-----------|
| 1. Happy paths | LF-HP-01 to LF-HP-05 | Prose in `Covers:` is tolerated; new rules are stated in the skills |
| 2. Edge cases and boundaries | LF-EC-01, LF-EC-02 | Ignored files never count; non-git roots still work |
| 3. State transitions | LF-ST-01 to LF-ST-06 | Resume and packaging read the real state of branches, statuses and commits |
| 4. Async and race conditions | none | Nothing in scope runs concurrently; the dimension is intentionally empty |
| 5. Failures and resilience | LF-FR-01 to LF-FR-04 | Bad encodings exit 2; unreachable remotes and uncommitted designs degrade safely |

## 2. UC-1 The Traceability Script Reads Coverage Faithfully

```gherkin
Feature: check_bdd_traceability.py reads Covers lines and test files faithfully

  Scenario: [LF-HP-01] A Covers line with prose and trailing punctuation is accepted
    Given a scenario document with PY-HP-01 and PY-EC-02
    And a task file whose line reads "Covers: PY-HP-01 (happy path), PY-EC-02."
    When the plan mode runs
    Then both identifiers are assigned to the task
    And no identifier is reported as unknown

  Scenario: [LF-HP-02] Tracked and new, unignored test files count as coverage
    Given an integration test root inside a git repository
    And one tracked test naming PY-HP-01 and one untracked, unignored test naming PY-EC-02
    When the tests mode runs
    Then both identifiers are covered

  Scenario: [LF-EC-01] A gitignored generated report does not count as coverage
    Given an integration test root inside a git repository that ignores "playwright-report/"
    And an ignored report file under that root naming PY-HP-01 and PY-EC-02
    When the tests mode runs
    Then neither identifier is covered and the run exits 1

  Scenario: [LF-EC-02] A root outside any git repository falls back to the directory walk
    Given an integration test root that is not inside a git repository
    And a test file under it naming PY-HP-01 and PY-EC-02
    When the tests mode runs
    Then both identifiers are covered

  Scenario: [LF-FR-01] A task file that is not valid UTF-8 is a usage error
    Given a task file whose bytes are not valid UTF-8
    When the plan mode runs
    Then the run exits 2 with "is not valid UTF-8" on stderr

  Scenario: [LF-FR-02] A scenario document that is not valid UTF-8 is a usage error
    Given a scenario document whose bytes are not valid UTF-8
    When the plan mode runs
    Then the run exits 2 with "is not valid UTF-8" on stderr
```

## 3. UC-2 Resuming an Epic Reads Truthful Signals

```gherkin
Feature: Entry-Point Detection and the Resume Procedure read the real state

  Scenario: [LF-ST-01] An epic branch pushed from another clone is visible before any fetch
    Given a remote that holds "epic/todo-export", pushed from another clone
    And a local repository that has not fetched since
    When the remote-branch signal of Entry-Point Detection runs
    Then "git branch -r" shows nothing
    And the "git ls-remote --heads" loop prints "refs/heads/epic/todo-export"

  Scenario: [LF-FR-03] An unreachable remote falls back to remote-tracking refs
    Given a repository whose remote URL cannot be reached
    When the "git ls-remote --heads" loop runs
    Then it exits non-zero
    And the skill text tells the agent to say so and fall back to "git branch -r"

  Scenario: [LF-ST-04] A task at review resumes its review, not its implementation
    Given an interrupted epic whose task_2 is at "review"
    When the Resume Procedure enters Phase 2
    Then it re-enters at Phase 2 step 2 and reviews the existing changes

  Scenario: [LF-ST-06] The retrofit commit may carry the interrupted task's status fields
    Given a resumed epic that needs the BDD identifier retrofit
    And an interrupted task whose file holds an uncommitted "in-progress" status
    When the retrofit is committed by path
    Then the skill text states that the task's status fields may ride along in that commit
```

## 4. UC-3 Packaging Records What the Receiver Needs

```gherkin
Feature: Packaging writes a handoff the receiver can trust

  Scenario: [LF-ST-02] The staleness check ignores the epic branch's own task commits
    Given an epic packaged at design commit S on the base branch
    And a task commit on the epic branch that changes the epic's task mirror
    When the template's check runs "git log S..<base_branch> -- .devtool/epic/<epic_dir>"
    Then only the "Package epic for handoff" commit is listed

  Scenario: [LF-FR-04] An uncommitted design records "uncommitted" and skips the check
    Given auto_commit is false when the epic is packaged
    When the receiver reads handoff.md
    Then the design commit reads "uncommitted"
    And the template tells it to skip the staleness check

  Scenario: [LF-ST-03] A queued epic keeps its queue when packaged
    Given an epic whose overview Status reads "Queued (backlog) — behind logging-refactor"
    When it is packaged with the Status "Packaged (queued behind logging-refactor)"
    Then the packaging grep finds that Status in both overview variants

  Scenario: [LF-HP-05] The template's task-count placeholder is explained
    Given the packaging procedure's step 2
    When the agent fills the handoff template
    Then the skill text says "<N>" is the task count the preflight printed
```

## 5. UC-4 Skill Text States the Rules

```gherkin
Feature: The skills state the rules the receiver needs

  Scenario: [LF-HP-03] Python's default integration roots include tests/e2e
    Given dev-designer's Integration Test Roots defaults
    When an agent designs a Python epic
    Then the defaults name "tests/integration/" and "tests/e2e/"

  Scenario: [LF-HP-04] The value separators of --roots and --ids are documented
    Given dev-implementation's Phase 4 traceability check
    When an agent copies the HLD's roots line or a task's Covers line
    Then the skill says both options take space- or comma-separated values

  Scenario: [LF-ST-05] Gate 4 names the traceability check in its re-run rule
    Given a Gate 4 verdict made stale by a later commit
    When dev-lifecycle's candidate-immutability condition is read
    Then it requires a fresh traceability check and epic quality run
```
