---
id: "task_01_evidence_files_contract"
status: "todo"
priority: "high"
assignee: null
epic: "contract-and-authoring-ergonomics"
dueDate: null
created: "2026-11-06T01:50:00Z"
modified: "2026-11-06T01:50:00Z"
completedAt: null
labels: ["architecture", "contract", "python"]
order: "a1"
---

# Task 01: Evidence Files Contract and Done-Gate Verification

Epic: [contract_and_authoring_ergonomics](../epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md)

## Requirement Analysis

Resolve Observation #0008: task files cannot list `.devtool/` paths under `Allowed files:`, yet `check_task_contract.py` rejects any `Verification` row or `Read-only context:` path that does not exist on disk, is not git-ignored, and is not marked `(new)` in some task. Consequently, tasks that produce evidence artifacts under `.devtool/epic/<epic_dir>/evidence/` (such as `baseline_failures.txt`, `results.json`, or `summary.json`) cannot reference those files in their own or downstream Verification rows.

This task introduces an optional `Evidence files:` subsection under `## Files` in `task_contract.py` and `check_task_contract.py`:
1. `parse_evidence_files(task_text: str) -> list[AllowedPath]` parses `- `<path>` (new)` bullets under `Evidence files:` inside `## Files`.
2. `check_evidence(check, stem, text, design)` in `check_task_contract.py` validates that every entry resides strictly under `.devtool/epic/<epic_dir>/evidence/<filename>` without `..` segments or bare directories, and when `--design` is passed, ensures `(new)` entries do not already exist on disk.
3. `Evidence files:` entries marked `(new)` are added to the `created` set in `check_task_contract.py` so `check_grounding()` accepts references to them in `Verification` rows and `Read-only context:`.
4. `evaluate_done_gate(task_file: Path)` in `task_contract.py` verifies that every path declared in `parse_evidence_files(task_text)` exists as a non-empty file on disk after `verify` completes.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/task_contract.py`
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
- `skills/dev-implementation/resources/scripts/test_run_task_checks.py`

Read-only context:
- `.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md` (HLD specification)
- `.devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md` (canonical BDD scenarios)

## Design Rationale

Applicable skills: `python-quality-check`, `test-driven-development`.
Separating `Evidence files:` from `Allowed files:` preserves the invariant that `Allowed files:` tracks production/test code outside `.devtool/` (which `fingerprint()` and `SCOPE` evaluate with `:(exclude).devtool`), while giving `.devtool/epic/<epic_dir>/evidence/*` artifacts first-class contract grounding at design time and existence enforcement at the Done Gate.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/task_contract.py`: `parse_allowed_files`, `evaluate_done_gate`, and new `parse_evidence_files`.
  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `check_allowed`, `check_grounding`, `check_task`, `main`, and new `check_evidence`.
- **Downstream Callers**: `skills/dev-implementation/resources/scripts/run_task_checks.py`, `skills/dev-implementation/resources/scripts/check_epic_readiness.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage across modified functions in `task_contract.py` and `check_task_contract.py`.

### BDD SCENARIOS

Covers: TCAE-HP-01, TCAE-FR-01

```gherkin
Scenario: [TCAE-HP-01] [Tier C - Integration] Evidence files declaration passes design contract and Done-Gate verification
  Given a task declaring ".devtool/epic/sample_epic/evidence/baseline.txt (new)" under "Evidence files:" in "## Files"
  And a Verification row referencing ".devtool/epic/sample_epic/evidence/baseline.txt"
  When check_task_contract.py runs with "--design"
  Then it exits 0 with 0 problems and grounds the new evidence path across the epic
  And when run_task_checks.py verify executes the row that writes ".devtool/epic/sample_epic/evidence/baseline.txt"
  Then evaluate_done_gate confirms the evidence file exists on disk and passes all Done-Gate conditions

Scenario: [TCAE-FR-01] [Tier A - Unit] Reject invalid Evidence files path outside epic evidence directory or with path traversal
  Given a task listing ".devtool/epic/sample_epic/../secret.txt (new)" or "src/output.json (new)" under "Evidence files:"
  When "check_task_contract.py --design" evaluates the task
  Then it exits 1 and reports that every "Evidence files:" entry must reside under ".devtool/epic/<epic_dir>/evidence/" without ".." segments
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py::test_TCAE_HP_01_evidence_files_grounding` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/test_check_task_contract.py skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/check_task_contract.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py skills/dev-implementation/resources/scripts/test_run_task_checks.py --junitxml=build/test-results/task_01.xml` | exit 0; results build/test-results/task_01.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Grounded existing symbol `parse_allowed_files(task_text: str) -> list[AllowedPath]` in `skills/dev-implementation/resources/scripts/task_contract.py`: add sibling frozen contract `parse_evidence_files(task_text: str) -> list[AllowedPath]` parsing `- `<path>` (new)` bullets under `Evidence files:` inside `## Files`.
- Every `Evidence files:` path must match `^\.devtool/epic/[A-Za-z0-9_-]+/evidence/[A-Za-z0-9_.-]+$` and must not contain `..` or trailing `/`.
- In `skills/dev-implementation/resources/scripts/check_task_contract.py`, `main()` unions `{entry.pattern for text in tasks.values() for entry in tc.parse_evidence_files(text) if entry.new}` into `created` so `check_grounding()` accepts those paths in `Verification` rows and `Read-only context:`.
- In `skills/dev-implementation/resources/scripts/task_contract.py`, `evaluate_done_gate(task_file: Path)` checks every entry in `parse_evidence_files(task_text)` and appends `"condition 8: evidence file <path> declared in Evidence files was not created or is empty"` if the file is missing or has size 0.

## Definition of Done

- `parse_evidence_files` and `check_evidence` validate `Evidence files:` entries and ground `(new)` evidence paths across tasks. (V2)
- `evaluate_done_gate` enforces that declared `Evidence files:` exist and are non-empty on disk. (V2, V5)
- `ruff` and `mypy` pass with zero errors on all modified files. (V3, V4)
- Automated tests covering `TCAE-HP-01` and `TCAE-FR-01` pass and write JUnit XML results. (V5)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by: None (first task in execution order).

## References & Rollback

- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](../epic/contract_and_authoring_ergonomics/2026-11-06-contract-and-authoring-ergonomics-design.en.md).
- Rollback: `git revert` the task commit to restore `task_contract.py` and `check_task_contract.py`.
