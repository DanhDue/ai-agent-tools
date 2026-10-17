# Review Workflow Enhancements BDD Scenarios

## Table of Contents

- [Meta Data](#meta-data)
- [Happy Paths](#happy-paths)
- [Edge Cases & Boundaries](#edge-cases--boundaries)
- [State Transitions](#state-transitions)
- [Failure & Resilience](#failure--resilience)

## Meta Data

- **Epic**: `review_workflow_enhancements`
- **Status**: Draft
- **Total Scenarios**: 12

## Happy Paths

```gherkin
Feature: Review Workflow Enhancements

  Scenario: [RWE-HP-01] [Tier A - Unit] [Happy] Verdict regex matches Markdown bold and header variants
    Given an AI CLI raw output ending with "**Verdict:** PASS" or "### Verdict: CHANGES REQUIRED"
    When the runner extracts verdicts from the output
    Then the verdict is identified cleanly as "PASS" or "CHANGES REQUIRED"
    And the round status is recorded as "completed"

  Scenario: [RWE-HP-02] [Tier A - Unit] [Happy] Finding lines match list items with mixed dashes and bullets
    Given an AI CLI raw output containing findings starting with "-" or "*" or "1."
    When the runner parses the findings
    Then each finding severity, location, and problem are parsed into structured elements

  Scenario: [RWE-HP-03] [Tier A - Unit] [Happy] Table cells are sanitized against control characters
    Given finding problem text containing carriage returns or newlines
    When the runner formats the round Markdown table
    Then all carriage returns are removed and internal newlines are replaced with spaces
    And pipe characters are escaped so each finding remains on exactly one table row

  Scenario: [RWE-HP-04] [Tier A - Unit] [Happy] Clean facts collection proceeds to CLI execution
    Given an epic with passing audit, integration results, and traceability checks
    When collect_facts executes within facts timeout limits
    Then audit and test facts are gathered cleanly and passed into prompt substitution
```

## Edge Cases & Boundaries

```gherkin
  Scenario: [RWE-EC-01] [Tier A - Unit] [Boundary] Conversational summary text does not trigger unparsed blocking
    Given an AI output with verdict "PASS" containing "I found 0 [Critical] or [Important] issues"
    When the runner checks for unparsed blocking findings
    Then no unparsed Critical or Important findings are generated
    And the round finishes with exit code 0

  Scenario: [RWE-EC-02] [Tier A - Unit] [Boundary] Trailing whitespace and mixed case in verdict
    Given an AI output line with "  verdict:   pass   "
    When the runner matches the verdict line
    Then it successfully parses "PASS" as the final verdict

  Scenario: [RWE-EC-03] [Tier A - Unit] [Boundary] Table findings row with multiple escaped pipes
    Given a finding problem containing text like "use a | b | c syntax"
    When the finding is rendered into review_results.md and checked by split_row
    Then split_row parses exactly 5 cells without splitting on escaped pipes

  Scenario: [RWE-EC-04] [Tier A - Unit] [Boundary] Facts timeout separates from CLI timeout
    Given a facts timeout configured to 300 seconds and a CLI timeout of 1800 seconds
    When collect_facts runs
    Then each fact command is bounded by the facts timeout without truncating the CLI timeout
```

## State Transitions

```gherkin
  Scenario: [RWE-ST-01] [Tier A - Unit] [State] Round transitions from CHANGES REQUIRED to completed check after decisions
    Given a round recorded with CHANGES REQUIRED and two Important findings
    When the developer records "fixed in <sha>" or "dismissed: <reason>" for all blocking findings
    Then run_external_review check exits 0 with no undecided findings

  Scenario: [RWE-ST-02] [Tier A - Unit] [State] Undecided findings block check command
    Given a completed round with an unresolved Critical finding
    When run_external_review check executes
    Then it lists the undecided finding identifier and exits with code 1
```

## Failure & Resilience

```gherkin
  Scenario: [RWE-FR-01] [Tier A - Unit] [Failure] Fail-fast aborts execution when audit_epic fails
    Given an epic branch where audit_epic.py returns exit code 1
    When run_external_review run executes
    Then it halts immediately without invoking the AI CLI
    And reports a precondition failure to prevent spending AI credits

  Scenario: [RWE-FR-02] [Tier A - Unit] [Failure] Fail-fast aborts execution when integration tests time out
    Given an integration test that times out and returns code is None
    When collect_facts executes
    Then it raises a precondition error and aborts before calling the AI CLI
```
