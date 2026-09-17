# BDD Scenarios — Document Lifecycle Suite

Behavioural contract for the epic, derived from the HLD's Use Cases and Sequence Diagram, **not**
from any implementation. Scenarios are tagged by tier:

- `[Tier A - Unit]` — one skill's own rule, verifiable by reading that skill or running one check.
- `[Tier C - Integration]` — end-to-end across skills, verifiable only by driving a real work item.

---

## UC1 — Produce a multi-section document through `doc-lifecycle`

### Dimension 1: Happy paths

```gherkin
Scenario: A multi-section document passes all three gates
  Given a work item whose deliverable is a four-section runbook
  And the diff touches no file that ships in the build
  When doc-lifecycle runs from Stage 1
  Then doc-designer asks who the audience is before anything else
  And exactly one Diátaxis mode is declared in the overview Meta Data
  And the outline lists four sections, each with one line of purpose
  And Gate 1 is presented to the user as a numbered task list
  And after approval one task file exists per section
  And doc-implementation produces exactly one commit per section
  And quality_check with Kind document returns a green verdict
  And Gate 3 is presented to the user before the branch is finished
```

```gherkin
Scenario: Acceptance is stated as a reader task  # [Tier A - Unit]
  Given doc-designer is writing the overview Meta Data
  When it fills the Acceptance field
  Then the value names something the reader can do after reading
  And a word count, page count or section count is rejected as an Acceptance value
```

### Dimension 2: Edge cases & boundaries

```gherkin
Scenario: Material spanning two Diátaxis modes is split  # [Tier A - Unit]
  Given source material that is part tutorial and part reference
  When doc-designer selects a mode
  Then it does not declare both modes on one document
  And it splits the work into one document per mode
  And each resulting document declares exactly one mode
```

```gherkin
Scenario Outline: Degenerate inputs  # [Tier A - Unit]
  Given a work item described as "<input>"
  When doc-lifecycle is invoked
  Then it <behaviour>

  Examples:
    | input                                  | behaviour                                          |
    | a one-line typo fix                    | routes to the direct-edit path, opening no gate     |
    | a document with no identifiable reader | stops and asks for the audience before the outline  |
    | an outline with zero sections          | refuses Gate 1 and asks for the outline             |
    | a single-section document              | proceeds with exactly one task file                 |
```

### Dimension 3: State transitions

```gherkin
Scenario: Stage 3 is unreachable without Gate 2  # [Tier C - Integration]
  Given a document draft that quality_check has not verified
  When finishing-a-development-branch is invoked
  Then the lifecycle refuses to proceed
  And it names Gate 2 as the unmet precondition
```

```gherkin
Scenario Outline: Gate failure routing  # [Tier A - Unit]
  Given the lifecycle is at <gate>
  When the gate fails
  Then control returns to <stage>

  Examples:
    | gate                        | stage                                    |
    | Gate 1 brief and outline    | Stage 1 — revise the brief or outline    |
    | Gate 2 draft verified       | Stage 2 — fix findings, re-run in full   |
    | Gate 3 sign-off             | Stage 2 — apply the requested changes    |
```

```gherkin
Scenario: A failed Gate 2 is re-run in full, never partially  # [Tier C - Integration]
  Given quality_check reported one failing mechanical check
  And the author fixed only that check
  When Gate 2 is re-evaluated
  Then the complete document check suite runs again
  And a green verdict from a partial run is not accepted
```

### Dimension 4: Async / race conditions

```gherkin
Scenario: A second epic is already active  # [Tier C - Integration]
  Given another epic has at least one task with status todo, in-progress or review
  When doc-designer writes task files for this epic
  Then every new task is created with status backlog, not todo
  And the epic overview Status field names the blocking epic
```

```gherkin
Scenario: Two sessions generate task files concurrently  # [Tier C - Integration]
  Given two sessions are writing task files for different epics
  When both write into .devtool/features/
  Then neither overwrites the other's files
  And each task file carries its own epic field in frontmatter
```

### Dimension 5: Failures & resilience

```gherkin
Scenario: The primary source cannot be reached  # [Tier A - Unit]
  Given diataxis.fr cannot be fetched
  When a task would write Diátaxis methodology text
  Then no methodology text is written
  And the task reports the fetch failure rather than writing from recall
```

---

## UC2 — Record a technical decision as an ADR

### Dimension 1: Happy paths

```gherkin
Scenario: A decision is recorded  # [Tier A - Unit]
  Given a technical decision has been made
  When decision-records runs
  Then the record carries Title, Status, Context, Decision and Consequences
  And it is numbered sequentially under docs/adr/
  And the Consequences section contains at least one negative consequence
  And the rejected alternatives are named with the reason each was rejected
```

### Dimension 2: Edge cases & boundaries

```gherkin
Scenario: An accepted record is never edited  # [Tier A - Unit]
  Given an ADR whose Status is Accepted
  When the decision it records is reversed
  Then the accepted record is left unmodified
  And a new record is written that supersedes it by number
  And no existing ADR number is reused or renumbered
```

```gherkin
Scenario: A record listing only benefits is rejected  # [Tier A - Unit]
  Given a draft ADR whose Consequences are all positive
  When the record is reviewed
  Then it is rejected as a sales pitch rather than a record
```

### Dimension 3: State transitions

```gherkin
Scenario Outline: Legal ADR status transitions  # [Tier A - Unit]
  Given an ADR with status <from>
  When a transition to <to> is attempted
  Then it is <verdict>

  Examples:
    | from      | to         | verdict  |
    | Proposed  | Accepted   | allowed  |
    | Accepted  | Superseded | allowed  |
    | Accepted  | Proposed   | refused  |
    | Superseded| Accepted   | refused  |
```

### Dimension 5: Failures & resilience

```gherkin
Scenario: A spike report states what would refute it  # [Tier A - Unit]
  Given a research spike has produced a recommendation
  When the report is written
  Then it contains a "What would change this conclusion" section
  And that section is not empty
```

---

## UC3 / UC8 — Refusal and escape paths

### Dimension 5: Failures & resilience

```gherkin
Scenario: The document path is refused for code work  # [Tier C - Integration]
  Given a work item declared Kind document
  And its diff modifies a file that ships in the build
  When quality_check runs
  Then it aborts before running any document check
  And the abort message names the offending files
  And it states that the work belongs in dev-lifecycle
```

```gherkin
Scenario: Kind is absent  # [Tier A - Unit]
  Given a work item whose Meta Data declares no Kind
  When quality_check runs
  Then it defaults to Kind development
  And the full existing 3-tier suite runs unchanged
```

```gherkin
Scenario: A trivial edit opens no gates  # [Tier C - Integration]
  Given a one-line correction to README.md
  When the author consults doc-lifecycle
  Then the "When NOT to use this" section names this case
  And the edit is made directly with no brief, outline or gate
```

---

## UC4 — Upstream escape from `brainstorming`

```gherkin
Scenario: The customer was never validated  # [Tier C - Integration]
  Given a brainstorming session about a new product feature
  When the session reveals no validated target customer or underserved need
  Then brainstorming stops before writing a spec
  And it recommends lean-product-lifecycle
  And it does not continue into epic-designer or writing-plans
```

```gherkin
Scenario: brainstorming has four exits, not two  # [Tier A - Unit]
  Given the brainstorming skill
  When its routing section is read
  Then it names dev-designer, writing-plans, doc-designer and lean-product-lifecycle
  And no other skill is named as a terminal state
```

---

## UC7 — Verifying a document

### Dimension 1: Happy paths

```gherkin
Scenario: A clean document passes  # [Tier A - Unit]
  Given a document with no placeholders, resolving links and balanced fences
  And the document stays inside its declared Diátaxis mode
  When quality_check runs with Kind document
  Then all four document checks pass
  And the verdict is green
```

### Dimension 2: Edge cases & boundaries

```gherkin
Scenario: The placeholder scan ignores code spans  # [Tier A - Unit]
  Given a document that documents the placeholder check itself
  And the words TBD and TODO appear only inside code spans and fenced blocks
  When the mechanical check runs
  Then the document passes
  And the occurrences inside code spans are not reported
```

```gherkin
Scenario Outline: Mechanical failures  # [Tier A - Unit]
  Given a document containing <defect>
  When the mechanical check runs
  Then it fails and names the offending line

  Examples:
    | defect                                      |
    | the literal text TBD in prose               |
    | a relative link to a file that is not there |
    | a ToC anchor with no matching heading       |
    | an unbalanced mermaid fence                 |
```

```gherkin
Scenario: Mode mixing is reported  # [Tier A - Unit]
  Given a document that declares Diátaxis mode reference
  And it contains step-by-step tutorial narration
  When the conformance check runs
  Then mode mixing is reported as a finding
```

### Dimension 5: Failures & resilience

```gherkin
Scenario: The content audit checks the Acceptance criterion  # [Tier C - Integration]
  Given a document whose Acceptance criterion is a named reader task
  When the content-audit subagent runs
  Then it reports whether the document actually enables that task
  And it flags claims made without support
```

---

## Governance — `verify.sh`

```gherkin
Scenario: An unreferenced supporting file fails the build  # [Tier B - Governance]
  Given a file under skills/<name>/ that no other file in the repository references
  And that file is not a SKILL.md
  When scripts/verify.sh runs
  Then the orphan check fails and names the file
```

```gherkin
Scenario: The orphan check is proven against a known defect  # [Tier B - Governance]
  Given the repository state before this epic
  When the orphan check runs
  Then it fails on skills/brainstorming/spec-document-reviewer-prompt.md
  And a passing result means the check itself is broken
```

```gherkin
Scenario: SKILL.md is exempt from the orphan check  # [Tier B - Governance]
  Given every skill's own SKILL.md
  When the orphan check runs
  Then no SKILL.md is reported
  And the check does not fail on a skill that nothing else links to
```

```gherkin
Scenario: The rename is proven complete  # [Tier B - Governance]
  Given the rename task is finished
  When the rename-completeness check runs
  Then no live file contains epic-lifecycle, epic-designer or epic-implementation
  And files under .devtool/ are not examined
  And historical entries in CHANGELOG.md are not examined
```

```gherkin
Scenario: The runtime script path survives the rename  # [Tier C - Integration]
  Given finishing-a-development-branch probes for sync_task_status.py by path
  When the epic-implementation directory is renamed
  Then that probe resolves to the new path
  And the archival step does not fall through to its fallback branch
```
