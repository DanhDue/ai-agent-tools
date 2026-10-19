---
id: "task_15_test_integrity_and_implementation_slimming"
status: "done"
priority: "high"
assignee: null
epic: "mechanical_verification_and_lifecycle_slimming"
dueDate: null
created: "2026-10-19T11:50:01Z"
modified: "2026-10-19T14:04:25Z"
completedAt: "2026-10-19T14:04:25Z"
labels: ["skill", "test-integrity", "documentation"]
order: "a15"
---

# Task 15: Add Test Integrity Rules and Slim Dev Implementation

Epic: [mechanical_verification_and_lifecycle_slimming](mechanical_verification_and_lifecycle_slimming.en.md)

## Requirement Analysis

Add the No Reconstructed Logic and Immutable Real Artifacts Gate 4 rules, then remove diagrams,
duplicated platform personas, incomplete quick references, and repeated red flags from
`dev-implementation/SKILL.md`. Preserve entry/resume, Gate 3, evidence, status, commit, integration,
Gate 4, Review Choice, Gate 5, and finishing handoff in at most 4,500 words.
Additionally, incorporate Mechanism 3: the 3-step Bounded Context Injection protocol in Phase 0
(read active task, read Allowed files and Read-only context, look up exact symbols in Decisions
Already Made; no undirected whole-repo searches) and strict spec fidelity instructions.

## Files

Allowed files:
- `skills/dev-implementation/SKILL.md`
- `scripts/test_lifecycle_document_contract.py`

Read-only context:
- `docs/lifecycles.en.md` — human-facing lifecycle overview
- `.devtool/epic/mechanical_verification_and_lifecycle_slimming/bdd_scenarios.en.md` — canonical scenarios
- `skills/quality_check/SKILL.md` — provider aggregation boundary

## Design Rationale

Keep behavioral rules in the runtime skill and move explanation/diagrams out. Contract tests assert
positive operational tokens, forbidden diagram fences, word count, and exact integrity rules.
Semantic provider review is mandatory, but this epic does not claim universal mechanical analysis.
Applicable skills: `d3nexus:writing-skills`, `d3nexus:python-quality-check`, and
`d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: implementation workflow prose and lifecycle contract assertions.
- **Downstream callers**: every epic implementation session and Gate 4 audit.
- **Cross-platform bridges**: None; provider-specific commands remain provider-owned.
- **Target test coverage threshold**: 100% of named lifecycle invariants in the contract test.

### BDD SCENARIOS

Covers: MVLS-HP-04, MVLS-FR-04

```gherkin
Scenario: Concision preserves implementation control flow
  Given the implementation skill is shortened
  When contract tests inspect it
  Then every gate, resume, evidence, review, and handoff invariant remains and word count is bounded

Scenario: Gate 4 rejects semantic test fakery
  Given tests reconstruct production logic or change anchors in a substituted artifact
  When Gate 4 or its provider reviews integrity
  Then the result is FAIL without claiming universal mechanical enforcement
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest scripts/test_lifecycle_document_contract.py` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest scripts/test_lifecycle_document_contract.py` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_15.xml scripts/test_lifecycle_document_contract.py` | exit 0; results build/test-results/task_15.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.
- Achieving the word target would remove a required gate, approval, recovery, or evidence command.

## Decisions Already Made

- Runtime rules stay inline; human diagrams and provider procedures do not.
- Test-integrity rules are Gate 4 semantic requirements, not a completed cross-language analyzer.

## Definition of Done

- Both assigned BDD IDs appear in automated contract tests and the JUnit report. (V2, V5)
- Both integrity rules, bounded context injection protocol, and every retained workflow invariant are asserted. (V2)
- No Mermaid or DOT fence remains and the skill is at most 4,500 words. (V2)
- Lint and strict type checking report zero issues. (V3, V4)

## Dependencies & Blockers

None. Blocks [Task 16](task_16_lifecycle_docs_and_acceptance.md), [Task 17](task_17_dev_designer_and_handoff_guardrails.md).

## References & Rollback

- [Epic HLD](mechanical_verification_and_lifecycle_slimming.en.md)
- **Rollback**: Restore the prior skill and contract test together if an invariant cannot be retained.
