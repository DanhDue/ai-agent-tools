# BDD Scenarios: Multi-Epic Orchestration and Governance

## Table of Contents

- [1. Dimension 1 — Happy Paths](#1-dimension-1--happy-paths)
- [2. Dimension 2 — Edge Cases & Boundaries](#2-dimension-2--edge-cases--boundaries)
- [3. Dimension 3 — State Transitions](#3-dimension-3--state-transitions)
- [4. Dimension 4 — Async & Concurrency](#4-dimension-4--async--concurrency)
- [5. Dimension 5 — Failures & Resilience](#5-dimension-5--failures--resilience)

---

## 1. Dimension 1 — Happy Paths

```gherkin
Feature: Multi-Epic Orchestration and Governance — Happy Paths

  Scenario: [MEO-HP-01] [Tier C - Integration] Dependent epic declaring Depends on epic passes design-time contract and R5 checks and replays prerequisite tasks automatically
    Given a packaged prerequisite epic "epic_alpha" whose tasks create "src/alpha_helper.py" with symbol "compute_alpha"
    And a dependent epic "epic_beta" whose HLD declares "- **Depends on epic**: epic-alpha"
    And "epic_beta" tasks list "src/alpha_helper.py" in "Read-only context" and reference "compute_alpha" in "Target Files & Symbols"
    When "check_epic_readiness.py epic_beta" executes before "epic_alpha" is merged to HEAD
    Then R1, R5, and R7 pass with 0 failures because "src/alpha_helper.py" and "compute_alpha" resolve from "epic_alpha"
    And when "replay_epic_in_worktree()" runs for "epic_beta"
    Then it replays "epic_alpha" tasks first in the temporary worktree followed by "epic_beta" tasks and exits 0

  Scenario: [MEO-HP-02] [Tier C - Integration] Conflict-aware check-conflicts and promote transition a disjoint epic from backlog to todo in one command
    Given an active epic "epic_alpha" with tasks in "todo" touching "src/alpha.py"
    And a queued epic "epic_gamma" with tasks in "backlog" touching "src/gamma.py" and no unfinished prerequisites
    When "sync_task_status.py check-conflicts epic_gamma" runs
    Then it reports "0 conflicts — safe for concurrent execution" and exits with code 0
    And when "sync_task_status.py promote epic_gamma" runs
    Then all "backlog" tasks of "epic_gamma" in ".devtool/epic/epic_gamma/" and ".devtool/features/" transition to "todo"

  Scenario: [MEO-HP-03] [Tier C - Integration] package_epic.py packages an epic, validates bilingual Spec Errata, and re-anchors handoff.md on --revise
    Given an epic whose ".en.md" and ".vi.md" HLD files declare matching "## Spec Errata" entries "[SE-01]"
    When "package_epic.py <epic_dir>" runs on a passing readiness check
    Then it writes ".devtool/epic/<epic_dir>/handoff.md" anchored to the current HEAD commit
    And when a post-packaging revision commit is made and "package_epic.py <epic_dir> --revise --reason 'Clarify SE-01 contract'" runs
    Then "handoff.md" updates "Design commit" to the new HEAD SHA and appends the revision entry under "## Revisions"

  Scenario: [MEO-HP-04] [Tier C - Integration] Gate approval ledger records structured Gate 1-5 approvals and answers --check-gate queries
    Given a repository with ".devtool/" project memory
    When "scripts/resume_context.py --gate 2 --epic sample-epic --approved 'HLD and 5 Kanban tasks' --deviations 'SE-01'" is executed
    Then ".devtool/state/gate_ledger.jsonl" records a JSON entry with "epic": "sample-epic", "gate": 2, "approved": "HLD and 5 Kanban tasks", "deviations": "SE-01", and the current commit SHA
    And ".devtool/GATE_LEDGER.md" is rendered with the Gate 2 approval row
    And "scripts/resume_context.py --check-gate 2 --epic sample-epic" outputs the approval record and exits with code 0
```

---

## 2. Dimension 2 — Edge Cases & Boundaries

```gherkin
Feature: Multi-Epic Orchestration and Governance — Edge Cases & Boundaries

  Scenario: [MEO-EC-01] [Tier A - Unit] Transitive Depends on epic chain resolves in topological order and deduplicates prerequisite files and symbols
    Given "epic_c" depends on "epic_b" and "epic_b" depends on "epic_a"
    When "resolve_prerequisite_epic_dirs()" and "collect_prerequisite_artifacts()" inspect "epic_c"
    Then "resolve_prerequisite_epic_dirs()" returns ["epic_a", "epic_b"] in topological order
    And "collect_prerequisite_artifacts()" returns the union of created files and symbols across both "epic_a" and "epic_b"

  Scenario: [MEO-EC-02] [Tier A - Unit] check_epic_file_conflicts ignores done tasks of other epics while detecting glob-vs-literal overlaps on active tasks
    Given "epic_done" has only "done" tasks touching "src/shared/core.py"
    And "epic_active" has an "in-progress" task with Allowed file glob "src/shared/*.py"
    When "check_epic_file_conflicts()" evaluates "epic_candidate" whose task touches "src/shared/core.py"
    Then it ignores "epic_done" and reports a conflict only against "epic_active" on "src/shared/core.py"
```

---

## 3. Dimension 3 — State Transitions

```gherkin
Feature: Multi-Epic Orchestration and Governance — State Transitions

  Scenario: [MEO-ST-01] [Tier A - Unit] sync_task_status.py promote blocks on unfinished prerequisites or active file conflicts unless --force is supplied
    Given "epic_beta" depends on "epic_alpha" whose status is "In Progress"
    When "sync_task_status.py promote epic_beta" is executed without "--force"
    Then it exits with code 1 and leaves "epic_beta" tasks in "backlog"
    And when "epic_alpha" transitions to "Done" (or "--force" is passed), "sync_task_status.py promote epic_beta" transitions all "epic_beta" tasks to "todo" and exits 0

  Scenario: [MEO-ST-02] [Tier A - Unit] package_epic.py --revise preserves custom Open Notes while updating Design commit, staleness git log SHA, and Revisions section
    Given an existing "handoff.md" with custom bullets under "## Open Notes" and "Design commit: `aaa1111`"
    When "package_epic.py <epic_dir> --revise --reason 'Align task 02 CLI flags'" runs at commit "bbb2222"
    Then "## Open Notes" retains all custom bullets verbatim
    And "Design commit" and the "git log" staleness check command are updated to "bbb2222"
    And "## Revisions" lists "`aaa1111` -> `bbb2222`" with reason "Align task 02 CLI flags"
```

---

## 4. Dimension 4 — Async & Concurrency

```gherkin
Feature: Multi-Epic Orchestration and Governance — Async & Concurrency

  Scenario: [MEO-AR-01] [Tier A - Unit] Concurrent resume_context.py --gate invocations serialize under fcntl.flock without losing approval records
    Given 4 parallel subprocesses invoking "scripts/resume_context.py --gate <n> --epic concurrent-epic --approved 'Gate <n> scope'" simultaneously
    When all 4 subprocesses complete
    Then ".devtool/state/gate_ledger.jsonl" contains 4 valid JSON lines with 0 interleaved or truncated records
    And ".devtool/GATE_LEDGER.md" contains all 4 gate approval rows

  Scenario: [MEO-AR-02] [Tier A - Unit] sync_task_status.py promote synchronizes task status across epic directory and features mirrors in all checkouts
    Given a queued epic with 3 tasks in "backlog" mirrored in both ".devtool/epic/<epic_dir>/" and ".devtool/features/"
    When "sync_task_status.py promote <epic_dir>" executes
    Then all 6 task files across ".devtool/epic/<epic_dir>/" and ".devtool/features/" are updated atomically to "status: \"todo\"" with a refreshed "modified" timestamp
```

---

## 5. Dimension 5 — Failures & Resilience

```gherkin
Feature: Multi-Epic Orchestration and Governance — Failures & Resilience

  Scenario: [MEO-FR-01] [Tier A - Unit] R7 fails when Depends on epic references a missing epic directory or forms a dependency cycle
    Given an epic HLD whose "Depends on epic:" line names a non-existent epic "missing-epic" or forms a cycle "epic_a -> epic_b -> epic_a"
    When "check_epic_readiness.py" runs R7 metadata verification
    Then R7 fails and reports the missing prerequisite epic or dependency cycle

  Scenario: [MEO-FR-02] [Tier A - Unit] R7 and package_epic.py fail when Spec Errata IDs mismatch between .en.md and .vi.md or --revise omits --reason
    Given an epic where ".en.md" declares "[SE-01]" and "[SE-02]" under "## Spec Errata" while ".vi.md" declares only "[SE-01]"
    When "check_epic_readiness.py" evaluates R7
    Then R7 fails reporting the asymmetric Spec Errata ID "[SE-02]"
    And when "package_epic.py <epic_dir> --revise" is invoked without "--reason"
    Then it exits with code 2 and reports that "--reason" is required for "--revise"

  Scenario: [MEO-FR-03] [Tier A - Unit] resume_context.py rejects --gate with empty --approved text and exits 1 on --check-gate for unapproved gates
    Given a repository where Gate 3 has not been approved for "sample-epic"
    When "scripts/resume_context.py --check-gate 3 --epic sample-epic" is executed
    Then it exits with code 1 and reports that Gate 3 is not yet recorded for "sample-epic"
    And when "scripts/resume_context.py --gate 3 --epic sample-epic --approved ''" is executed with an empty approval scope
    Then it exits with code 2 without modifying ".devtool/state/gate_ledger.jsonl"
```
