---
id: "task_17_dev_designer_and_handoff_guardrails"
status: "done"
priority: "high"
assignee: null
epic: "mechanical_verification_and_lifecycle_slimming"
dueDate: null
created: "2026-10-19T12:30:00Z"
modified: "2026-10-19T14:21:54Z"
completedAt: "2026-10-19T14:21:54Z"
labels: ["skills", "contracts", "prompt-hardening"]
order: "a17"
---

# Task 17: Harden Dev-Designer Task Contract and Handoff Guardrails

Epic: [mechanical_verification_and_lifecycle_slimming](../epic/mechanical_verification_and_lifecycle_slimming/mechanical_verification_and_lifecycle_slimming.en.md)

## Requirement Analysis

Fast executor models need task files and packaged handoffs that expose frozen implementation facts
without requiring broad repository exploration. `dev-designer/SKILL.md` must instruct the designer to
state exact production signatures, parameter defaults, canonical constants, and caller-to-callee chains
under `## Decisions Already Made`, pin BDD assertions to production observation points without weak
checks (`non-empty`, `truthy`, `works`, `valid`), require exact node IDs for pytest RED rows
(`path/test_file.py::test_name`) expecting exit 1 with positive failure output, and allow
`RED: n/a — <reason>` for tasks without new executable behavior.
`skills/dev-lifecycle/references/handoff-template.md` must provide the four receiving-LLM guardrails
(bounded context loading, strict spec fidelity, zero test fakery, no contract repair by the executor)
and instruct the receiver to apply them before Gate 3. `scripts/test_lifecycle_document_contract.py`
must enforce these anchors with mechanical anti-drift assertions.

## Files

Allowed files:
- `skills/dev-designer/SKILL.md`
- `skills/dev-lifecycle/references/handoff-template.md`
- `scripts/test_lifecycle_document_contract.py`

Read-only context:
- `skills/dev-lifecycle/SKILL.md` — lifecycle orchestrator and handoff procedure
- `.devtool/epic/mechanical_verification_and_lifecycle_slimming/mechanical_verification_and_lifecycle_slimming.en.md` — HLD
- `.devtool/epic/mechanical_verification_and_lifecycle_slimming/bdd_scenarios.en.md` — canonical scenarios
- `docs/lifecycles.en.md` — human lifecycle documentation

## Design Rationale

Prompt hardening backed by anti-drift token assertions ensures fast models do not drift or
hallucinate implementations. Applicable skills: `d3nexus:writing-skills`,
`d3nexus:python-quality-check`, `d3nexus:doc_quality_check`, and
`d3nexus:verification-before-completion`; tools are `unittest`, `ruff`, and `mypy`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: dev-designer task-generation instructions, handoff template receiving
  guardrails, and lifecycle document contract assertions.
- **Downstream callers**: future epic task generation, handoff packaging, and receiving agents across
  all supported platforms.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: 100% of the new task-generation and handoff-guardrail anchors
  in `scripts/test_lifecycle_document_contract.py`.

### BDD SCENARIOS

Covers: MVLS-HP-06, MVLS-EC-06

```gherkin
Scenario: Preserve task-generation rules and receiving-LLM guardrails
  Given `dev-designer/SKILL.md` and `handoff-template.md` are evaluated by the lifecycle document contract
  When contract assertions check task-generation rules and handoff templates
  Then `dev-designer` retains grounded Decisions Already Made contracts, exact node IDs, and prohibitions on weak assertions
  And `handoff-template.md` retains all four receiving-LLM guardrails and the Gate 3 resume prompt instruction

Scenario: Reject missing receiving-LLM guardrails or dev-designer anchors in lifecycle contract
  Given `dev-designer/SKILL.md` lacks exact node ID rules or `handoff-template.md` drops a receiving-LLM guardrail
  When the lifecycle document contract test runs
  Then the test fails reporting the missing anchor
  And release verification cannot pass until the contract is restored
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest scripts/test_lifecycle_document_contract.py` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest scripts/test_lifecycle_document_contract.py` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V5 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc skills/dev-lifecycle/references/handoff-template.md` | exit 0; contains "0 findings" | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_17.xml scripts/test_lifecycle_document_contract.py` | exit 0; results build/test-results/task_17.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- The prompt hardening would require inventing ungrounded contracts or building a cross-language validator.

## Decisions Already Made

- No cross-language mechanical schema validator is added in this epic; prompt hardening is enforced by
  anti-drift token assertions.
- Existing packaged handoff files remain immutable.

## Definition of Done

- `dev-designer/SKILL.md` contains the task-generation rules (Decisions Already Made contracts, exact node IDs, weak assertion ban). (V2)
- `handoff-template.md` contains the four receiving-LLM guardrails and passes TOC lint. (V2, V5)
- `scripts/test_lifecycle_document_contract.py` asserts all new anchors and passes lint/type-check. (V2, V3, V4, V6)
- Assigned BDD IDs appear in automated tests and the JUnit report. (V2, V6)

## Dependencies & Blockers

Blocked by [Task 15](../epic/mechanical_verification_and_lifecycle_slimming/task_15_test_integrity_and_implementation_slimming.md).

Blocks [Task 16](../epic/mechanical_verification_and_lifecycle_slimming/task_16_lifecycle_docs_and_acceptance.md).

## References & Rollback

- [Epic HLD](../epic/mechanical_verification_and_lifecycle_slimming/mechanical_verification_and_lifecycle_slimming.en.md)
- [Approved source spec](../epic/mechanical_verification_and_lifecycle_slimming/2026-10-19-mechanical-verification-and-lifecycle-slimming-design.en.md)
- [Canonical BDD scenarios](../epic/mechanical_verification_and_lifecycle_slimming/bdd_scenarios.en.md)
- **Rollback**: Revert `skills/dev-designer/SKILL.md`, `skills/dev-lifecycle/references/handoff-template.md`,
  and `scripts/test_lifecycle_document_contract.py` together, then rerun contract verification.
