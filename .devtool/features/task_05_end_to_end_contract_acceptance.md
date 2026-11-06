---
id: "task_05_end_to_end_contract_acceptance"
status: "in-progress"
priority: "high"
assignee: null
epic: "contract-and-authoring-ergonomics"
dueDate: null
created: "2026-11-06T01:50:00Z"
modified: "2026-11-06T03:34:36Z"
completedAt: null
labels: ["integration", "acceptance", "tier-c"]
order: "a5"
---

# Task 05: End-to-End Integration and Acceptance Verification

Epic: [contract_and_authoring_ergonomics](../epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md)

## Requirement Analysis

Every epic requires a final Tier C integration and acceptance task exercising the full end-to-end workflow across all component seams (`bin/d3nexus`, `sync_task_status.py render`, `check_task_contract.py --design`, `run_task_checks.py`, and `task_contract.py` Done-Gate evaluation) and verifying repository-wide quality gates (`scripts/verify.sh`).

This task creates `tests/test_task_contract_ergonomics_e2e.py` covering the remaining integration scenarios (`TCAE-ST-02`, `TCAE-AR-02`, `TCAE-FR-03`) and running end-to-end subcutaneous workflows in isolated temporary git repositories.

## Files

Allowed files:
- `tests/test_task_contract_ergonomics_e2e.py` (new)
- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
- `scripts/test_verifiable_handoff.py`

Read-only context:
- `bin/d3nexus` (created in Task 03) (new)
- `skills/dev-implementation/resources/scripts/task_contract.py` (modified in Task 01 and Task 03)
- `skills/dev-implementation/resources/scripts/check_task_contract.py` (modified in Tasks 01–04)
- `skills/dev-implementation/resources/scripts/sync_task_status.py` (modified in Task 02)
- `skills/dev-implementation/resources/scripts/run_task_checks.py` (modified in Task 03)

## Design Rationale

Applicable skills: `python-quality-check`, `test-driven-development`.
Placing the end-to-end subcutaneous suite in `tests/test_task_contract_ergonomics_e2e.py` ensures that `python3 -m pytest tests/` exercises the complete lifecycle from single-source authoring to Done-Gate verification on every PR and Epic quality gate run. In addition, fixing the two `Optional[str]` narrowing lines in `check_bdd_traceability.py` ensures clean `mypy` runs across the entire script suite without requiring workarounds.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `tests/test_task_contract_ergonomics_e2e.py`: new `test_TCAE_ST_02_done_gate_evidence_transition`, new `test_TCAE_AR_02_idempotent_render`, new `test_TCAE_FR_03_render_unknown_covers_aborts`.
  - `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`: `scenario_ids`.
- **Downstream Callers**: Gate 4 `quality_check` and `check_bdd_traceability.py tests --results`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% BDD scenario traceability across all 14 `[TCAE-*]` scenarios.

### BDD SCENARIOS

Covers: TCAE-ST-02, TCAE-AR-02, TCAE-FR-03

```gherkin
Scenario: [TCAE-ST-02] [Tier C - Integration] Done Gate transitions from FAIL to PASS once declared Evidence file is written
  Given a task declaring ".devtool/epic/sample_epic/evidence/summary.json (new)" under "Evidence files:"
  When "evaluate_done_gate" runs before ".devtool/epic/sample_epic/evidence/summary.json" is created on disk
  Then "evaluate_done_gate" returns a condition failure naming ".devtool/epic/sample_epic/evidence/summary.json"
  And when the verification run writes non-empty JSON to ".devtool/epic/sample_epic/evidence/summary.json"
  Then "evaluate_done_gate" returns an empty problem list

Scenario: [TCAE-AR-02] [Tier C - Integration] Deterministic idempotent re-rendering across repeated render calls
  Given an epic directory with multiple tasks covering multiple scenarios and file embeds
  When "sync_task_status.py render sample_epic" is executed twice in succession without intermediate edits
  Then the second run produces byte-for-byte identical files in ".devtool/epic/sample_epic/" and ".devtool/features/"

Scenario: [TCAE-FR-03] [Tier C - Integration] Render aborts cleanly when Covers references an unknown scenario ID or missing embed file
  Given a task in ".devtool/epic/sample_epic/" whose "Covers:" line names "TCAE-HP-99" which is absent from "bdd_scenarios.en.md"
  When "sync_task_status.py render sample_epic" executes
  Then it exits 1 naming the unknown scenario ID "TCAE-HP-99" and leaves existing ".devtool/features/" files untouched
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | GREEN | `python3 -m pytest tests/test_task_contract_ergonomics_e2e.py` | exit 0; contains "passed" | — |
| V2 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py` | exit 0 | — |
| V3 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py` | exit 0 | — |
| V4 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "OK" | — |
| V5 | TIER-C | `python3 -m pytest tests/ skills/dev-implementation/resources/scripts/ --junitxml=build/test-results/pytest.xml` | exit 0; results build/test-results/pytest.xml | — |

RED: n/a — end-to-end acceptance test suite verifying behaviors already implemented in Tasks 01–04.

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `tests/test_task_contract_ergonomics_e2e.py` exercises the end-to-end flow using temporary git repositories (`tmp_path`), invoking `bin/d3nexus` (`sync-status render`, `check-contract --design`, `run-checks verify`) and asserting all 14 `[TCAE-*]` scenarios pass across the test suite.
- In `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`, narrow `fence_marker: str | None` before indexing `fence_marker[0]` and `len(fence_marker)` in `scenario_ids()` so `mypy` passes cleanly without `--follow-imports=silent`.

## Definition of Done

- End-to-end integration tests in `tests/test_task_contract_ergonomics_e2e.py` pass for `TCAE-ST-02`, `TCAE-AR-02`, and `TCAE-FR-03`. (V1, V5)
- `ruff`, `mypy`, and `bash scripts/verify.sh` pass with zero errors. (V2, V3, V4)
- Full test suite across `tests/` and `skills/dev-implementation/resources/scripts/` passes with 100% `[TCAE-*]` scenario traceability in `build/test-results/pytest.xml`. (V5)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 04](../epic/contract_and_authoring_ergonomics/task_04_verification_grammar_and_docs.md)

## References & Rollback

- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](../epic/contract_and_authoring_ergonomics/2026-11-06-contract-and-authoring-ergonomics-design.en.md).
- Rollback: `git revert` the task commit to remove `tests/test_task_contract_ergonomics_e2e.py`.
