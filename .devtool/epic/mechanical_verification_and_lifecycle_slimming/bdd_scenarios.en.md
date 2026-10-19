# Mechanical Verification and Lifecycle Slimming BDD Scenarios

## Table of Contents

- [Meta Data](#meta-data)
- [Happy Paths](#happy-paths)
- [Edge Cases and Boundaries](#edge-cases-and-boundaries)
- [State Transitions](#state-transitions)
- [Async and Race Conditions](#async-and-race-conditions)
- [Failure and Resilience](#failure-and-resilience)

## Meta Data

- **Epic**: `mechanical_verification_and_lifecycle_slimming`
- **Canonical language**: English
- **Scenario prefix**: `MVLS`
- **Automation roots**: `skills/dev-implementation/resources/scripts/`, `scripts/`
- **Rule**: Every scenario ID is assigned to exactly one task and appears in an automated test.

## Happy Paths

```gherkin
Scenario: [MVLS-HP-01] [Tier C - Integration] Record a genuine collected-test RED

Given a RED row directly invokes pytest and its collected test fails with exit 1
When `run_task_checks.py` records the row
Then the positive failure summary qualifies as a genuine behavioral RED
And the evidence outcome is PASS for the expected RED phase

Scenario: [MVLS-HP-02] [Tier C - Integration] Audit genuine pytest RED evidence

Given committed evidence contains a supported pytest command, exit 1 or 2, and a positive failure summary
When `audit_epic.py` audits the candidate SHA
Then it recomputes the RED semantics successfully
And no invalid-pytest-RED finding is emitted

Scenario: [MVLS-HP-03] [Tier C - Integration] Accept complete Python TIER-B verification

Given a Python task has TIER-B rows that directly invoke a linter and a type checker
When `check_task_contract.py --design` validates the task
Then the Python tooling contract passes
And registered provider commands are accepted when their normalized argument sequences match

Scenario: [MVLS-HP-04] [Tier C - Integration] Preserve implementation orchestration in a concise skill

Given `dev-implementation/SKILL.md` has been slimmed
When the lifecycle document contract runs
Then entry-point detection, resume, Gate 3, evidence, Gate 4, Review Choice, Gate 5, and finishing handoff remain present
And the skill states the two semantic test-integrity rules
And its word count is at most 4,500 words

Scenario: [MVLS-HP-05] [Tier C - Integration] Preserve human lifecycle understanding in bilingual docs

Given runtime diagrams have moved out of the lifecycle skills
When the English and Vietnamese lifecycle documents are checked
Then both contain the lifecycle and resume diagrams
And both describe Gate 4, Review Choice, Gate 5, and the cross-model return to Gate 4
And `dev-lifecycle/SKILL.md` remains at most 2,500 words

Scenario: [MVLS-HP-06] [Tier C - Integration] Preserve task-generation rules and receiving-LLM guardrails

Given `dev-designer/SKILL.md` and `handoff-template.md` are evaluated by the lifecycle document contract
When contract assertions check task-generation rules and handoff templates
Then `dev-designer` retains grounded Decisions Already Made contracts, exact node IDs, and prohibitions on weak assertions
And `handoff-template.md` retains all four receiving-LLM guardrails and the Gate 3 resume prompt instruction

```

## Edge Cases and Boundaries

```gherkin
Scenario: [MVLS-EC-01] [Tier C - Integration] Reject a missing pytest file

Given a RED row invokes pytest for a path that does not exist
And the process exits 4 or reports `ERROR: file or directory not found`
When the recorder or Gate 4 auditor evaluates the row
Then the row fails with the required invalid-pytest-RED reason

Scenario: [MVLS-EC-02] [Tier C - Integration] Reject an empty pytest selection

Given a RED row collects zero tests or selects zero tests
And the process exits 5, reports `collected 0 items`, or reports `/ 0 selected`
When the recorder or Gate 4 auditor evaluates the row
Then the row fails with the required invalid-pytest-RED reason

Scenario: [MVLS-EC-03] [Tier C - Integration] Avoid a repository-wide Python false positive

Given a polyglot repository contains Python configuration
But a task's Allowed files and verification rows contain no task-local Python signal
When the task contract is validated
Then Python-specific TIER-B requirements are not imposed on that task

Scenario: [MVLS-EC-04] [Tier C - Integration] Distinguish supported wrappers from unrelated text

Given command rows include `uv run pytest`, `python -m pytest`, an executable path ending in pytest, and `echo pytest`
When the command classifier tokenizes the rows
Then the first three are classified as pytest invocations
And `echo pytest` is not classified as a pytest invocation

Scenario: [MVLS-EC-05] [Tier C - Integration] Keep diagrams outside runtime skills

Given the runtime skills and bilingual lifecycle docs are checked together
When the lifecycle document contract scans fenced blocks
Then neither runtime skill contains Mermaid or Graphviz DOT diagrams
And both lifecycle documents contain the expected human-facing Mermaid diagrams

Scenario: [MVLS-EC-06] [Tier C - Integration] Reject missing receiving-LLM guardrails or dev-designer anchors in lifecycle contract

Given `dev-designer/SKILL.md` lacks exact node ID rules or `handoff-template.md` drops a receiving-LLM guardrail
When the lifecycle document contract test runs
Then the test fails reporting the missing anchor
And release verification cannot pass until the contract is restored

Scenario: [MVLS-EC-07] [Tier C - Integration] Reject non-node-id pytest expressions, weak BDD assertions, or empty decisions

Given a task contract undergoing design or implementation verification
When `check_task_contract.py` checks pytest RED rows, BDD scenario assertions, or `Decisions Already Made`
Then a generic `-k` pytest command without an exact node ID is rejected
And weak assertions such as "should be truthy", "is valid", or "returns non-empty" are rejected
And an empty or missing `Decisions Already Made` section on a task with executable changes is rejected
```

## State Transitions

```gherkin
Scenario: [MVLS-ST-01] [Tier C - Integration] Invalid RED recording transitions to FAIL

Given a RED row's ordinary Expect would accept a non-zero exit
But its pytest semantics are invalid
When recording completes
Then the row outcome transitions to FAIL
And the recorder exits non-zero with the required reason stored in evidence

Scenario: [MVLS-ST-02] [Tier C - Integration] Tampered PASS evidence transitions Gate 4 to FAIL

Given invalid pytest RED evidence has been edited to say `outcome: PASS`
When Gate 4 audits the committed evidence
Then semantic recomputation overrides the stored outcome
And the Evidence section and final audit verdict transition to FAIL

Scenario: [MVLS-ST-03] [Tier C - Integration] Skill slimming keeps document contracts synchronized

Given orchestration prose or diagrams move between a runtime skill and lifecycle docs
When the lifecycle contract and bilingual document checker run
Then the change passes only if mandatory runtime invariants remain
And the English and Vietnamese human documents remain structurally synchronized

```

## Async and Race Conditions

```gherkin
Scenario: [MVLS-AR-01] [Tier C - Integration] Independent RED rows do not leak validation state

Given one task contains a valid pytest RED row and an invalid pytest RED row
When rows are evaluated in either order
Then each verdict depends only on its own command, exit code, and output
And the invalid row cannot inherit the valid row's positive summary

Scenario: [MVLS-AR-02] [Tier C - Integration] Multi-task audit remains deterministic

Given a candidate SHA contains several task evidence records with mixed pytest RED validity
When Gate 4 audits them repeatedly
Then findings are associated with the correct task and row
And the aggregate precedence remains FAIL over BLOCKED over PASS regardless of traversal order

```

## Failure and Resilience

```gherkin
Scenario: [MVLS-FR-01] [Tier C - Integration] Reject a wrapper that rewrites an invalid exit to 1

Given a wrapper runs pytest against a missing file or empty selection and then exits 1
When the merged output still contains a forbidden pytest marker
Then the recorder and auditor reject the RED despite the allowlisted exit code

Scenario: [MVLS-FR-02] [Tier C - Integration] Reject ambiguous exit 1 without a failure summary

Given a pytest RED command exits 1
But its output has no positive non-zero failed-or-error summary
When the semantic validator evaluates it
Then validation fails closed with the required invalid-pytest-RED reason

Scenario: [MVLS-FR-03] [Tier C - Integration] Fail on a malformed registered Python manifest

Given `.agents/quality/python-quality.json` exists but is malformed or has unusable lint or type-check capability data
When a Python task contract is validated
Then the validator reports the manifest problem
And it does not silently fall back to built-in tool names

Scenario: [MVLS-FR-04] [Tier C - Integration] Fail semantic test fakery at Gate 4

Given a test reconstructs production retry, progress, or configuration logic instead of importing and invoking Allowed-file symbols
Or a real repository artifact is replaced by synthetic data with different scenario anchors
When Gate 4 or its registered provider audits test integrity
Then the violation is reported as FAIL
And no universal cross-language mechanical-coverage claim is made

Scenario: [MVLS-FR-05] [Tier C - Integration] Fail when lifecycle invariants drift

Given slimming removes a required gate, recovery rule, review loop, or bilingual diagram invariant
When repository and document contract tests run
Then the affected test fails with the missing invariant
And release verification cannot pass until the contract is restored

Scenario: [MVLS-FR-06] [Tier C - Integration] Fail when active task core sections are tampered

Given an active task file in `.devtool/features/` whose `Files`, `Verification`, `Definition of Done`, or `Covers` differs from HEAD or epic mirror
When `run_task_checks.py` validates task integrity before running verification commands
Then it aborts with a task tampered error
And no verification evidence is committed
```
