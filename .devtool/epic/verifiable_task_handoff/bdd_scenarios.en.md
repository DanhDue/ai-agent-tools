# BDD Scenarios: Verifiable Task Handoff

## Table of Contents

- [1. Overview and Boundary Matrix](#1-overview-and-boundary-matrix)
- [2. UC-1 The Designer's Task Contract Is Checked](#2-uc-1-the-designers-task-contract-is-checked)
- [3. UC-2 The Executor's Checks Are Recorded](#3-uc-2-the-executors-checks-are-recorded)
- [4. UC-3 The Done Gate Trusts Only Recorded Evidence](#4-uc-3-the-done-gate-trusts-only-recorded-evidence)
- [5. UC-4 Traceability Reads Test Results](#5-uc-4-traceability-reads-test-results)
- [6. UC-5 Gate 4 Audits the Epic](#6-uc-5-gate-4-audits-the-epic)
- [7. UC-6 Skill Text States the Contract](#7-uc-6-skill-text-states-the-contract)
- [8. UC-7 The Whole Cycle Runs End to End](#8-uc-7-the-whole-cycle-runs-end-to-end)
- [9. UC-8 A Second Model Reviews the Finished Epic](#9-uc-8-a-second-model-reviews-the-finished-epic)

## 1. Overview and Boundary Matrix

The behavioural contract for the `verifiable_task_handoff` epic. Every scenario carries a `VTH-`
identifier and needs at least one automated integration test, under the HLD's integration test roots,
whose test case name contains it and which passes in the JUnit report.

| Dimension | Scenarios | Guarantee |
|-----------|-----------|-----------|
| 1. Happy paths | VTH-HP-01 to VTH-HP-13 | A compliant task goes from design to audit with every script exiting 0; a clean review is recorded; the skills state the contract |
| 2. Edge cases and boundaries | VTH-EC-01 to VTH-EC-07 | Malformed contracts, ungrounded paths, unset variables and misleading test reports are caught by name; Minor review findings do not block |
| 3. State transitions | VTH-ST-01 to VTH-ST-11 | `done` is reachable only from a matching, recorded, in-scope verification; the audit catches every other route; blocking review findings hold Phase 4 |
| 4. Async and race conditions | VTH-AR-01, VTH-AR-02 | A base branch that moves, and a gate run from the wrong checkout, degrade safely |
| 5. Failures and resilience | VTH-FR-01 to VTH-FR-08 | Timeouts, stale reports, bad input and failing or meddling review CLIs fail closed with the documented exit codes |

## 2. UC-1 The Designer's Task Contract Is Checked

```gherkin
Feature: check_task_contract.py and plan check what the designer wrote

  Scenario: [VTH-HP-01] [Tier C - Integration] A compliant epic passes the design-time contract check
    Given a git repository with an HLD declaring Protected paths, Integration results and a Verification Environment
    And two task files whose Files, Verification, Definition of Done, Stop and Report If and Decisions Already Made sections are complete
    When check_task_contract.py runs with --design
    Then it exits 0
    And it prints the tracked programs the Verification rows run as implicit protected paths

  Scenario: [VTH-EC-01] [Tier C - Integration] Paths that do not match the repository are named
    Given a task whose Allowed files lists an untracked path without "(new)"
    And a "(new)" path that already exists
    And a Read-only context path that does not exist
    And a Command naming a repository path that no task creates
    When check_task_contract.py runs with --design
    Then it exits 1 and names each path with its task
    And without --design the existing "(new)" path of a task already done is not reported

  Scenario: [VTH-EC-02] [Tier C - Integration] A Definition of Done item with no command is rejected
    Given a Definition of Done bullet ending with neither a row reference nor "(Gate 5)"
    And a bullet referencing row V9 that the table does not contain
    When check_task_contract.py runs
    Then it exits 1 and names both bullets

  Scenario: [VTH-EC-03] [Tier C - Integration] A malformed Verification table is rejected row by row
    Given a table with a duplicate ID, an unknown phase, an Expect clause outside the grammar and "results" on a GREEN row
    And a task with neither a RED row nor a "RED: n/a" reason
    And a task with a Covers line but no TIER-C row carrying "results"
    When check_task_contract.py runs
    Then it exits 1 and names every problem as "<task>:<row>: <problem>"

  Scenario: [VTH-EC-04] [Tier C - Integration] Missing HLD declarations are rejected
    Given an HLD without a Protected paths line, without an Integration results line or with an empty Verification Environment section
    And a Needs variable the Verification Environment does not name
    And a results path that git does not ignore
    When check_task_contract.py runs
    Then it exits 1 and names each missing or invalid declaration

  Scenario: [VTH-ST-01] [Tier C - Integration] An identifier owned by two tasks fails the plan
    Given a scenario document with VTH-HP-01
    And two task files whose Covers lines both name VTH-HP-01
    When check_bdd_traceability.py plan runs
    Then it exits 1 and names both tasks for VTH-HP-01

  Scenario: [VTH-FR-04] [Tier C - Integration] The contract check reports usage errors with exit 2
    Given a task file that cannot be read, or a working directory outside any git repository
    When check_task_contract.py runs
    Then it exits 2 with the reason on stderr
```

## 3. UC-2 The Executor's Checks Are Recorded

```gherkin
Feature: run_task_checks.py runs the declared rows and writes evidence

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

## 4. UC-3 The Done Gate Trusts Only Recorded Evidence

```gherkin
Feature: sync_task_status.py task done refuses unless the recorded evidence matches

  Scenario: [VTH-HP-03] [Tier C - Integration] Matching evidence lets the task reach done
    Given a task of a code epic whose red and verify runs are recorded and match the current tree
    When run_task_checks.py status runs
    Then it reports that the done gate would pass and exits 0
    When sync_task_status.py task done runs in the epic worktree
    Then the status, modified and completedAt fields are written in every checkout

  Scenario: [VTH-ST-03] [Tier C - Integration] Done without evidence is refused
    Given a task of a code epic with no evidence file
    When sync_task_status.py task done runs
    Then it exits 1 naming the missing evidence
    And the task's status is unchanged in every checkout

  Scenario: [VTH-ST-04] [Tier C - Integration] Edits after verification are refused
    Given a task whose verify run passed
    When a source file is changed afterwards and sync_task_status.py task done runs
    Then it exits 1 because the verify tree differs from the current tree
    When instead the Expect of row V2 is changed afterwards and sync_task_status.py task done runs
    Then it exits 1 because the recorded expect of V2 differs from the table

  Scenario: [VTH-ST-05] [Tier C - Integration] A RED run that did not precede the change is refused
    Given a task whose red run was recorded on the same tree as its verify run
    When sync_task_status.py task done runs
    Then it exits 1 naming the RED ordering condition
    And the same holds when the red run finished after the verify run started

  Scenario: [VTH-ST-06] [Tier C - Integration] Only code epics are gated
    Given a task of a code epic whose overview declares "Integration test roots:" and whose file has no Verification section
    When sync_task_status.py task done runs
    Then it exits 1 with "retrofit required"
    Given instead a task of a document epic whose overview declares no "Integration test roots:"
    When sync_task_status.py task done runs
    Then the status is written as before

  Scenario: [VTH-ST-07] [Tier C - Integration] A covered identifier without a passing case is refused
    Given a task whose Covers line names VTH-HP-01 and VTH-EC-01
    And evidence whose results digest has a passed case for VTH-HP-01 only
    When sync_task_status.py task done runs
    Then it exits 1 naming VTH-EC-01

  Scenario: [VTH-AR-02] [Tier C - Integration] The gate run from a checkout without the evidence writes nothing
    Given a main checkout and an epic worktree, with the evidence only in the worktree
    When sync_task_status.py task done runs from the main checkout
    Then it exits 1 saying the gate must run in the epic worktree
    And no checkout's copy of the task changes
```

## 5. UC-4 Traceability Reads Test Results

```gherkin
Feature: check_bdd_traceability.py tests --results proves each identifier ran and passed

  Scenario: [VTH-HP-04] [Tier C - Integration] JUnit and Dart reports prove every identifier
    Given a JUnit file with a passed case "test_vth_hp_01_compliant_epic"
    And a Gradle-style directory of JUnit files with a passed case for VTH-EC-01
    And a Dart JSON reporter file with a passed test "[VTH-ST-01] plan rejects" inside a group
    When the tests mode runs with --results naming the file, the directory and the Dart file
    Then every selected identifier passes and the run exits 0

  Scenario: [VTH-EC-06] [Tier C - Integration] Misleading coverage is rejected with its reason
    Given an identifier that appears only in a comment of a test file
    And an identifier whose only case is skipped
    And an identifier with one passed and one failed case
    When the tests mode runs with --results
    Then the first fails with "no test case in results", the second with "skipped" and the third with "failed in"
    And the run exits 1

  Scenario: [VTH-FR-02] [Tier C - Integration] A report in neither format is a usage error
    Given a results file that starts with neither "<" nor "{"
    When the tests mode runs with --results naming it
    Then it exits 2 naming the file
```

## 6. UC-5 Gate 4 Audits the Epic

```gherkin
Feature: audit_epic.py audits every done task and discloses every grader change

  Scenario: [VTH-HP-05] [Tier C - Integration] A clean epic passes the audit
    Given an epic branch whose done tasks each committed passing evidence with their code
    When audit_epic.py runs against the base branch
    Then every task's commit patch-id equals its verify patch_id
    And the audit exits 0

  Scenario: [VTH-HP-10] [Tier C - Integration] Disclosures are listed without failing the audit
    Given a task whose Verification row was amended after the task file was created
    And a commit on the epic branch that belongs to no task and touches a file outside .devtool
    And a Definition of Done bullet marked "(Gate 5)"
    And a done task whose task commit has no Verification section
    When audit_epic.py runs
    Then the report lists the amendment with its commit title, the commit outside tasks, the Gate 5 item and the legacy task
    And the audit exits 0

  Scenario: [VTH-ST-08] [Tier C - Integration] A done status written by hand fails the audit
    Given a task with a Verification section whose status was set to done by editing its frontmatter
    And no evidence file for it on the epic branch
    When audit_epic.py runs
    Then it exits 1 naming the task's missing evidence

  Scenario: [VTH-ST-09] [Tier C - Integration] Protected changes outside tasks fail outside .devtool and are disclosed inside it
    Given a commit outside any task that changes "scripts/verify.sh", a protected path
    And a doc-sync commit that adds a scenario identifier to bdd_scenarios.en.md
    When audit_epic.py runs
    Then it exits 1 naming the scripts/verify.sh change
    And it lists the added identifier as a disclosure

  Scenario: [VTH-AR-01] [Tier C - Integration] A moved base branch changes trees but not the verdict
    Given an epic branch rebased onto a base branch that moved after its tasks were verified
    When the rebase had no conflicts and audit_epic.py runs
    Then every patch-id still matches and the audit exits 0
    When a conflict resolution changed one task's patch and audit_epic.py runs
    Then that task is listed as "patch changed after verify" and the audit still exits 0

  Scenario: [VTH-FR-03] [Tier C - Integration] An unknown base reference is a usage error
    Given a base reference that git cannot resolve
    When audit_epic.py runs
    Then it exits 2 naming the reference
```

## 7. UC-6 Skill Text States the Contract

```gherkin
Feature: the skills and prompts state the new contract a receiving agent must follow

  Scenario: [VTH-HP-06] [Tier C - Integration] dev-designer states the task contract
    Given skills/dev-designer/SKILL.md and its references/verification-rows.md
    When the text is read
    Then the task template names Files, Verification, Definition of Done, Stop and Report If and Decisions Already Made
    And it requires each identifier on exactly one task's Covers line
    And Step 3 runs check_task_contract.py --design beside plan
    And verification-rows.md gives report commands for Python, Android, Web, iOS, Rust and Flutter

  Scenario: [VTH-HP-07] [Tier C - Integration] dev-implementation states the recorder and the gate
    Given skills/dev-implementation/SKILL.md
    When the text is read
    Then Phase 2 runs run_task_checks.py red before implementation and verify after it
    And the task commit stages the evidence file
    And Phase 4 runs audit_epic.py, the Integration results commands, tests --results and quality_check in that order

  Scenario: [VTH-HP-08] [Tier C - Integration] dev-lifecycle and the handoff template state the rules
    Given skills/dev-lifecycle/SKILL.md and its references/handoff-template.md
    When the text is read
    Then Gate 4 names the audit and result-based traceability
    And the packaging preflight runs check_task_contract.py --design
    And the handoff rules forbid editing a Verification table, Allowed files or a protected path

  Scenario: [VTH-HP-09] [Tier C - Integration] The SDD prompts treat evidence, not prose, as proof
    Given the implementer and task reviewer prompts of subagent-driven-development
    When the text is read
    Then the implementer runs the recorder and cites the evidence file
    And the reviewer runs run_task_checks.py status and treats missing evidence as Critical

  Scenario: [VTH-HP-13] [Tier C - Integration] The Review Choice is stated where it is asked
    Given skills/dev-implementation/SKILL.md and skills/dev-lifecycle/SKILL.md
    When the text is read
    Then dev-implementation asks the Review Choice, "Finish" or "Cross-model review", after the last task
    And the developer picks the Claude CLI or the Codex CLI
    And Phase 4 starts with run_external_review.py check when review_results.md exists
    And dev-lifecycle's Red Flags name picking the review CLI for the developer
```

## 8. UC-7 The Whole Cycle Runs End to End

```gherkin
Feature: one task travels the whole lifecycle on a throwaway repository

  Scenario: [VTH-HP-11] [Tier C - Integration] Design to audit, every step exits 0
    Given a throwaway git repository with an HLD and one compliant task file
    When check_task_contract.py --design and plan run
    And run_task_checks.py red runs, the change is made and run_task_checks.py verify runs
    And sync_task_status.py task done runs and the task is committed with its evidence
    And audit_epic.py runs against the base branch
    Then every command exits 0
```

## 9. UC-8 A Second Model Reviews the Finished Epic

```gherkin
Feature: run_external_review.py runs the developer's chosen CLI and records each round

  Scenario: [VTH-HP-12] [Tier C - Integration] A clean review round is recorded
    Given a clean epic worktree whose tasks are all done
    And a fake "codex" on PATH that saves its stdin and prints "Verdict: PASS"
    When run_external_review.py run runs with --cli codex --model gpt-test
    Then it exits 0
    And the prompt it sent names the candidate SHA, the base, the evidence directory and the review checklist
    And review_results.md gains "## Round 1" with status completed, CLI codex, model gpt-test and verdict PASS

  Scenario: [VTH-EC-07] [Tier C - Integration] Minor findings alone do not block
    Given a fake "claude" that prints "Verdict: CHANGES REQUIRED" and one "[Minor]" finding
    When run_external_review.py run runs with --cli claude
    Then it exits 0
    And the Minor finding is listed in the round's findings table

  Scenario: [VTH-ST-10] [Tier C - Integration] Blocking findings hold Phase 4 until each has a decision
    Given a fake CLI that prints "Verdict: CHANGES REQUIRED" with one "[Critical]" and one "[Important]" finding
    When run_external_review.py run runs
    Then it exits 1 and the round lists both findings with an empty Decision
    When run_external_review.py check runs
    Then it exits 1 naming both findings
    When the Decision column reads "fixed in <sha>" for one and "dismissed: <reason>" for the other
    And run_external_review.py check runs
    Then it exits 0

  Scenario: [VTH-ST-11] [Tier C - Integration] The latest completed round governs check
    Given review_results.md whose round 1 has an undecided Critical finding
    And a round 2, completed with no blocking finding
    And a round 3 recorded as "no verdict"
    When run_external_review.py check runs
    Then it exits 0 because round 2 is the latest completed round
    And rounds 1 and 3 are still present and unchanged

  Scenario: [VTH-FR-06] [Tier C - Integration] A missing CLI or a dirty tree stops the review before it runs
    Given no "claude" on PATH
    When run_external_review.py run runs with --cli claude
    Then it exits 2 naming the missing CLI
    And review_results.md is not created
    Given instead an uncommitted change in the worktree
    When run_external_review.py run runs
    Then it exits 2 asking for a clean tree and writes nothing

  Scenario: [VTH-FR-07] [Tier C - Integration] A reviewer that modifies the tree is discarded
    Given a fake CLI that creates a file in the repository and prints "Verdict: PASS"
    When run_external_review.py run runs
    Then it exits 2
    And the round is recorded as "discarded: tree modified", naming the created file

  Scenario: [VTH-FR-08] [Tier C - Integration] A failing, silent or slow CLI records no verdict
    Given a fake CLI that exits 1 printing "credit balance is too low"
    When run_external_review.py run runs
    Then it exits 2 and records the round as "no verdict" with the CLI's output
    And the same holds for a CLI whose output has no Verdict line, and for one that outlives --timeout
```
