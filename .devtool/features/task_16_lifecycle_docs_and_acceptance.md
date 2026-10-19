---
id: "task_16_lifecycle_docs_and_acceptance"
status: "todo"
priority: "high"
assignee: null
epic: "mechanical_verification_and_lifecycle_slimming"
dueDate: null
created: "2026-10-19T11:50:01Z"
modified: "2026-10-19T11:50:01Z"
completedAt: null
labels: ["integration", "lifecycle", "acceptance"]
order: "a16"
---

# Task 16: Consolidate Lifecycle Docs and Run Acceptance

Epic: [mechanical_verification_and_lifecycle_slimming](../epic/mechanical_verification_and_lifecycle_slimming/mechanical_verification_and_lifecycle_slimming.en.md)

## Requirement Analysis

This is the final Tier C task. Slim `dev-lifecycle/SKILL.md` to at most 2,500 words while preserving
all five gates, resume/failure routing, Handoff Choice, Review Choice, and cross-model return to a
fresh Gate 4. Incorporate Mechanism 4: Dynamic Cross-Model Review Recommendation for fast executor
models at Gate 4. Keep lifecycle and resume diagrams in the synchronized human docs, strengthen the
anti-drift test, and run the complete epic and repository acceptance commands.

## Files

Allowed files:
- `skills/dev-lifecycle/SKILL.md`
- `docs/lifecycles.en.md`
- `docs/lifecycles.vi.md`
- `scripts/test_lifecycle_document_contract.py`

Read-only context:
- `skills/dev-implementation/SKILL.md` — implementation handoff and review loop
- `scripts/verify.sh` — repository release verification
- `.devtool/epic/mechanical_verification_and_lifecycle_slimming/bdd_scenarios.en.md` — canonical scenarios

## Design Rationale

Human diagrams remain durable and bilingual; runtime skills remain operational sources of truth.
Positive contract assertions protect gates and recovery semantics before duplicate prose is removed.
Applicable skills: `d3nexus:writing-skills`, `d3nexus:doc_quality_check`,
`d3nexus:quality_check`, and `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: lifecycle routing prose, bilingual diagrams, document contract tests.
- **Downstream callers**: every epic lifecycle session and human maintainer of the kit.
- **Cross-platform bridges**: None; quality provider internals remain unchanged.
- **Target test coverage threshold**: 100% of the named lifecycle and bilingual invariants.

### BDD SCENARIOS

Covers: MVLS-HP-05, MVLS-EC-05, MVLS-ST-03, MVLS-FR-05

```gherkin
Scenario: Human docs retain diagrams while runtime skills stay concise
  Given both lifecycle surfaces are checked together
  When document and contract tests run
  Then diagrams exist only in synchronized human docs and every runtime invariant remains

Scenario: Drift blocks release acceptance
  Given a gate, recovery rule, review loop, word limit, or bilingual invariant is missing
  When full acceptance runs
  Then the relevant contract fails until the invariant is restored
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest scripts/test_lifecycle_document_contract.py` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest scripts/test_lifecycle_document_contract.py` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/audit_epic.py skills/dev-implementation/resources/scripts/check_task_contract.py scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/audit_epic.py skills/dev-implementation/resources/scripts/check_task_contract.py scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V5 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc --require-bilingual docs/lifecycles.en.md docs/lifecycles.vi.md` | exit 0; contains "0 findings" | — |
| V6 | TIER-B | `scripts/verify.sh` | exit 0 | — |
| V7 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/mechanical-verification-and-lifecycle-slimming.xml skills/dev-implementation/resources/scripts/test_run_task_checks.py skills/dev-implementation/resources/scripts/test_audit_epic.py skills/dev-implementation/resources/scripts/test_check_task_contract.py scripts/test_lifecycle_document_contract.py` | exit 0; results build/test-results/mechanical-verification-and-lifecycle-slimming.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.
- A provider/schema change appears necessary to claim cross-language test-integrity enforcement.

## Decisions Already Made

- Runtime scripts and skills are operational truth; lifecycle docs explain the system for humans.
- No quality-provider schema or provider implementation changes belong to this epic.

## Definition of Done

- All four assigned BDD IDs appear in automated tests and the final JUnit report. (V2, V7)
- Runtime skills contain no diagram fences and meet both word limits without losing invariants. (V2)
- English and Vietnamese lifecycle docs retain synchronized lifecycle and resume diagrams. (V2, V5)
- Lint, strict type checking, repository verification, and complete integration acceptance pass. (V3, V4, V6, V7)
- Semantic test-integrity findings remain Gate 4 failures without a false mechanical claim. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 13](../epic/mechanical_verification_and_lifecycle_slimming/task_13_audit_pytest_red_evidence.md).
Blocked by [Task 14](../epic/mechanical_verification_and_lifecycle_slimming/task_14_enforce_python_tier_b.md).
Blocked by [Task 15](../epic/mechanical_verification_and_lifecycle_slimming/task_15_test_integrity_and_implementation_slimming.md).
Blocked by [Task 17](../epic/mechanical_verification_and_lifecycle_slimming/task_17_dev_designer_and_handoff_guardrails.md).

## References & Rollback

- [Epic HLD](../epic/mechanical_verification_and_lifecycle_slimming/mechanical_verification_and_lifecycle_slimming.en.md)
- [Canonical BDD scenarios](../epic/mechanical_verification_and_lifecycle_slimming/bdd_scenarios.en.md)
- **Rollback**: Revert runtime skill, bilingual docs, and contract-test changes together, then rerun
  the complete acceptance matrix.
