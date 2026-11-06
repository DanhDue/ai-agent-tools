---
id: "task_05_multi_epic_governance_e2e_acceptance"
status: "todo"
priority: "high"
assignee: null
epic: "multi-epic-orchestration-and-governance"
dueDate: null
created: "2026-11-06T04:25:00Z"
modified: "2026-11-06T20:07:41Z"
completedAt: null
labels: ["acceptance", "integration", "docs"]
order: "c5"
---

# Task 05: End-to-End Multi-Epic Governance Acceptance Verification

Epic: [multi_epic_orchestration_and_governance](multi_epic_orchestration_and_governance.en.md)

## Requirement Analysis

Provide the end-to-end subcutaneous acceptance test suite (`tests/test_multi_epic_governance_acceptance.py`) verifying the complete multi-epic orchestration and governance lifecycle across all `[Tier C - Integration]` scenarios (`MEO-HP-01`, `MEO-HP-02`, `MEO-HP-03`, `MEO-HP-04`), and update the workflow skill documentation (`skills/dev-lifecycle/SKILL.md`, `skills/dev-designer/SKILL.md`, `skills/dev-implementation/SKILL.md`, `skills/principal-review/SKILL.md`, and `skills/save-context/SKILL.md`) to document:
1. HLD `Depends on epic:` declarations, design-time prerequisite resolution, and `sync_task_status.py check-prereqs` (`#0013`).
2. Conflict-aware concurrent epic analysis (`sync_task_status.py check-conflicts`) and bulk promotion (`sync_task_status.py promote [--force]`) (`#0014`).
3. Packaged epic revision (`package_epic.py <epic_dir> --revise --reason "<text>"`) and HLD `## Spec Errata` (`[SE-NN]`) (`#0015`).
4. Structured Gate Approval Ledger (`scripts/resume_context.py --gate` / `--check-gate`) (`#0020`).

## Files

Allowed files:
- `tests/test_multi_epic_governance_acceptance.py` (new)
- `scripts/verify.sh`
- `skills/dev-lifecycle/SKILL.md`
- `skills/dev-designer/SKILL.md`
- `skills/dev-implementation/SKILL.md`
- `skills/principal-review/SKILL.md`
- `skills/save-context/SKILL.md`

Read-only context:
- `skills/dev-implementation/resources/scripts/package_epic.py` (implemented in Task 03)
- `skills/dev-implementation/resources/scripts/sync_task_status.py` (updated in Task 02)
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py` (updated in Tasks 01 and 03)
- `scripts/resume_context.py` (updated in Task 04)
- `.devtool/epic/multi_epic_orchestration_and_governance/multi_epic_orchestration_and_governance.en.md` (HLD specification)

## Design Rationale

Applicable skills: `python-quality-check`, `doc_quality_check`, `verification-before-completion`.
Because Tasks 01–04 implement all underlying runtime behaviors, this final acceptance task uses `RED: n/a` and verifies the complete end-to-end multi-epic workflow in temporary Git repositories while updating the 5 skill manuals so agents and developers adopt these governance commands consistently.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `tests/test_multi_epic_governance_acceptance.py`: new `test_MEO_HP_01_to_04_end_to_end_multi_epic_governance`.
- **Downstream Callers**: `scripts/verify.sh` and Gate 4 `Integration results:`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $100\%$ of `[Tier C - Integration]` scenarios (`MEO-HP-01`, `MEO-HP-02`, `MEO-HP-03`, `MEO-HP-04`) verified in JUnit XML output.

### BDD SCENARIOS

Covers: MEO-AR-02

```gherkin
  Scenario: [MEO-AR-02] [Tier C - Integration] sync_task_status.py promote synchronizes task status across epic directory and features mirrors in all checkouts
    Given a queued epic with 3 tasks in "backlog" mirrored in both ".devtool/epic/<epic_dir>/" and ".devtool/features/"
    When "sync_task_status.py promote <epic_dir>" executes
    Then all 6 task files across ".devtool/epic/<epic_dir>/" and ".devtool/features/" are updated atomically to "status: \"todo\"" with a refreshed "modified" timestamp
```

## Verification

RED: n/a — end-to-end acceptance test suite and skill documentation verifying behaviors already implemented in Tasks 01–04.

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | GREEN | `python3 -m pytest tests/test_multi_epic_governance_acceptance.py` | exit 0; contains "passed" | — |
| V2 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_multi_epic_governance_acceptance.py` | exit 0 | — |
| V3 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_multi_epic_governance_acceptance.py --follow-imports=silent` | exit 0 | — |
| V4 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-lifecycle/SKILL.md skills/dev-designer/SKILL.md skills/dev-implementation/SKILL.md skills/principal-review/SKILL.md skills/save-context/SKILL.md` | exit 0; contains "0 findings" | — |
| V5 | TIER-C | `python3 -m pytest tests/ skills/dev-implementation/resources/scripts/ --junitxml=build/test-results/pytest.xml` | exit 0; results build/test-results/pytest.xml | — |
| V6 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS" | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `tests/test_multi_epic_governance_acceptance.py` exercises `MEO-HP-01`..`MEO-HP-04` and `MEO-AR-02` end-to-end in temporary Git repositories.
- In `scripts/verify.sh` step 11 (`== 11. Lifecycle document contracts are enforced ==`), register the three new `skills/dev-implementation/resources/scripts/` unit test suites:
  - `python3 -m unittest skills/dev-implementation/resources/scripts/test_inter_epic_dependencies.py || FAILED=1`
  - `python3 -m unittest skills/dev-implementation/resources/scripts/test_concurrent_epic_backlog.py || FAILED=1`
  - `python3 -m unittest skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py || FAILED=1`
- In `skills/dev-implementation/SKILL.md` Phase 0 Entry-Point Detection, require running `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py check-prereqs <epic_dir>` and halting with the blocker list on exit `1` whenever the HLD declares `Depends on epic:`.
- `skills/dev-lifecycle/SKILL.md`, `skills/dev-designer/SKILL.md`, `skills/dev-implementation/SKILL.md`, `skills/principal-review/SKILL.md`, and `skills/save-context/SKILL.md` document `Depends on epic:`, `sync_task_status.py check-prereqs / check-conflicts / promote`, `package_epic.py [--revise --reason]`, `## Spec Errata` (`[SE-NN]`), and `scripts/resume_context.py --gate / --check-gate`.

## Definition of Done

- `tests/test_multi_epic_governance_acceptance.py` passes and verifies `MEO-HP-01`..`MEO-HP-04` and `MEO-AR-02` in JUnit XML output. (V1, V5)
- `skills/dev-implementation/SKILL.md` Phase 0 Entry-Point Detection mandates running `sync_task_status.py check-prereqs <epic_dir>` and halting with the blocker list on exit `1` whenever the HLD declares `Depends on epic:`. (V4)
- All 5 updated `SKILL.md` files pass `check_document.py` with 0 findings. (V4)
- `scripts/verify.sh` step 11 registers `test_inter_epic_dependencies.py`, `test_concurrent_epic_backlog.py`, and `test_package_and_revise_epic.py` and `bash scripts/verify.sh` passes. (V6)
- `ruff` and `mypy` pass with zero errors. (V2, V3)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 01](task_01_inter_epic_dependencies.md)
- Blocked by [Task 02](task_02_conflict_aware_epic_promotion.md)
- Blocked by [Task 03](task_03_package_revise_and_spec_errata.md)
- Blocked by [Task 04](task_04_gate_approval_ledger.md)

## References & Rollback

- Reference: [2026-11-06-multi-epic-orchestration-and-governance-design.en.md](2026-11-06-multi-epic-orchestration-and-governance-design.en.md).
- Rollback: `git revert` the task commit to remove `tests/test_multi_epic_governance_acceptance.py` and doc updates.
