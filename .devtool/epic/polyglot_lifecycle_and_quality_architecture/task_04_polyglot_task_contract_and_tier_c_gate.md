---
id: "task_04_polyglot_task_contract_and_tier_c_gate"
status: "todo"
priority: "high"
assignee: null
epic: "polyglot_lifecycle_and_quality_architecture"
dueDate: null
created: "2026-11-27T09:18:00+07:00"
modified: "2026-11-27T09:18:00+07:00"
completedAt: null
labels: ["dev-implementation", "polyglot", "task-contract", "tier-c"]
order: "a04"
review_tier: "full"
---

# Task 04: Wire Polyglot Tier B Adapter, Tier C2 Gate, and Compact Output into `check_task_contract.py`

Epic: [polyglot_lifecycle_and_quality_architecture](polyglot_lifecycle_and_quality_architecture.md)

## Requirement Analysis

Wire `skills/dev-implementation/resources/scripts/check_task_contract.py` and `skills/dev-implementation/resources/scripts/task_contract.py` to Task 01's `_stack_lifecycle_registry.py` (`TierBContractAdapter` and `TierCTaxonomy`):

1. Replace the Python-only `if is_python_task(text, rows): check_python_tier_b(...)` branch in `check_task_contract.py::check_task` with `TierBContractAdapter` polyglot dispatch (intersecting `Allowed files` extensions with active `.agents/quality/*-quality.json` manifests; falling back to `check_python_tier_b` only when zero manifests exist in `check.root`).
2. Add `parse_integration_test_roots(hld_text: str) -> list[str]` to `task_contract.py`, and wire `TierCTaxonomy` in `check_task_contract.py::check_task` and `check_hld`: hard-fail explicit `Tier C2`/`TIER-C2` rows missing `Needs:` and unsafe/missing-target HLD `Integration test roots:`; emit non-blocking warnings to `check.warnings` for heuristic ungated heavy-runtime `TIER-C` commands (`integration_test/`, `connected*AndroidTest`, `xcodebuild test`, `playwright test`).
3. Enforce the compact 1-line `PASS` stdout invariant in `check_task_contract.py::main`: default `PASS` emits exactly `Result: 0 problems — PASS`; `--verbose` prints `Implicit protected paths: ...` before the Result line; `--json` emits structured JSON; `FAIL` emits all problem lines + `Implicit protected paths: ...` + `Result: <n> problems — FAIL`. Update the 3 existing `Implicit protected paths:` tests in `test_check_task_contract.py` (`L113`, `L122`, `L618`) to pass `--verbose` per `[SE-03]`.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- `skills/dev-implementation/resources/scripts/task_contract.py`
- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
- `tests/test_plq_task_contract_polyglot.py` (new)

Read-only context:
- `.devtool/epic/polyglot_lifecycle_and_quality_architecture/polyglot_lifecycle_and_quality_architecture.md`
- `.devtool/epic/polyglot_lifecycle_and_quality_architecture/bdd_scenarios.md`
- `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py` (new)
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development` and `d3nexus:python-quality-check`.
- Preserve 100% legacy compatibility for Python repos without `.agents/quality/*-quality.json` and for `check_epic_readiness.py` invoking `check_task_contract.py`.
- Keep all stack-specific rules inside `_stack_lifecycle_registry.py` (zero new `if is_flutter_task ... elif is_rust_task ...` branches inside `check_task_contract.py`).

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/check_task_contract.py` (`check_python_tier_b` `L861-L941`, `_check_python_tier_b_allowed_coverage` `L942-L1020`, `check_task` `L1205-L1261`, `check_hld` `L1263-L1304`, `main` `L1352-L1419`)
  - `skills/dev-implementation/resources/scripts/task_contract.py` (`parse_protected_paths` `L232-L260`, `parse_integration_results` `L332-L355` — add `parse_integration_test_roots`)
  - `skills/dev-implementation/resources/scripts/test_check_task_contract.py` (`L105-L128`, `L610-L625` — pass `--verbose` on implicit protected paths assertions per `[SE-03]`)
  - `tests/test_plq_task_contract_polyglot.py` (new): Integration tests for `PLQ-HP-04`, `PLQ-EC-06`, `PLQ-ST-02`, `PLQ-AR-03`, `PLQ-FR-04`.
- **Downstream Callers**: `skills/dev-implementation/resources/scripts/check_epic_readiness.py`, `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py`, `skills/dev-implementation/resources/scripts/test_check_task_contract.py`, `tests/test_ohk_cmr_and_contracts.py`.
- **Cross-Platform Bridges**: None.
- **Target Coverage Threshold**: >= 90% on all new branches in `check_task_contract.py` and `task_contract.py`.

### BDD SCENARIOS

Covers: PLQ-HP-04, PLQ-EC-06, PLQ-ST-02, PLQ-AR-03, PLQ-FR-04

```gherkin
Scenario: [PLQ-HP-04] [Tier C - Integration] Polyglot task contract passes when all touched stacks satisfy Tier B and emits one-line PASS
Given a repository with active rust-quality.json and web-quality.json manifests and a task whose Allowed files touch both "crates/core/src/lib.rs" and "apps/web/src/app.ts"
When check_task_contract.py --design validates the task containing chained TIER-B commands covering cargo fmt --check, cargo clippy -D warnings, eslint, and tsc --noEmit
Then check_task_contract.py exits with code 0
And default stdout is exactly one line: "Result: 0 problems — PASS"
And re-running with --verbose appends the "Implicit protected paths:" line before the Result line

Scenario: [PLQ-EC-06] [Tier C - Integration] Legacy Python repo without .agents/quality manifests preserves check_python_tier_b fallback
Given a temporary git repository with no .agents/quality directory and a task whose Allowed files touch "src/app.py"
When check_task_contract.py --design validates the task with a missing mypy row
Then the legacy check_python_tier_b fallback reports the missing Python type-check problem and exits with code 1

Scenario: [PLQ-ST-02] [Tier C - Integration] TierCTaxonomy distinguishes explicit Tier C2 missing Needs from heuristic heavy-runtime warning
Given an epic with a task having a TIER-C row explicitly marked "Tier C2" with empty Needs ("—") and another task having an unlabeled "npx --no-install playwright test" TIER-C row with empty Needs ("—")
When check_task_contract.py --design validates the first task
Then it exits with code 1 and reports an explicit Tier C2 missing Needs problem
When check_task_contract.py --design validates the second task
Then it exits with code 0 and emits a non-blocking Tier C2 warning to stderr suggesting a Needs variable

Scenario: [PLQ-AR-03] [Tier C - Integration] Conditional boundary checks activate only when domain or manifest boundary files change
Given active manifests for flutter, rust, android, and ios
When check_task_contract.py validates tasks touching "packages/core/lib/domain/entity.dart", "crates/domain/Cargo.toml", "feature/wallet/domain/UseCase.kt", or "Packages/Core/Package.swift" without boundary/architecture TIER-B rows
Then check_task_contract.py reports the missing stack-specific boundary check for each task
And when a task only touches non-domain presentation/utility files without manifest edits, no boundary check problem is emitted

Scenario: [PLQ-FR-04] [Tier C - Integration] Invalid HLD Integration test roots with path traversal or missing targets fail check_task_contract
Given an Epic HLD declaring "Integration test roots: ../escape, nonexistent_dir/"
When check_task_contract.py --design validates the HLD and tasks
Then check_task_contract.py exits with code 1 and reports explicit problems for both "../escape" (path traversal) and "nonexistent_dir/" (no matching tracked or planned files)
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_plq_task_contract_polyglot.py::test_plq_hp_04_polyglot_task_passes_with_one_line_pass` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_plq_task_contract_polyglot.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 skills/dev-implementation/resources/scripts/test_check_task_contract.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py tests/test_ohk_cmr_and_contracts.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/test_check_task_contract.py tests/test_plq_task_contract_polyglot.py && ruff format --check skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/test_check_task_contract.py tests/test_plq_task_contract_polyglot.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/test_check_task_contract.py tests/test_plq_task_contract_polyglot.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_plq_task_contract_polyglot.py --junitxml=build/test-results/task_04.xml` | exit 0; results build/test-results/task_04.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`check_task_contract.py` `L1237-L1238`, `L1352-L1419`)**: Currently runs `if is_python_task(text, rows): check_python_tier_b(...)` and prints both `Implicit protected paths:` and `Result:` unconditionally on `PASS`.
- **New contract**:
  - `check_task()` checks `TierBContractAdapter.has_provider_manifests(check.root)`: when `True`, delegates Tier B validation strictly to `TierBContractAdapter.validate_tier_b(...)` (invoking `check_python_tier_b` for Python when `python-quality.json` is active alongside `.py` files, and dispatching every other active touched stack); when `False`, preserves legacy `if is_python_task(text, rows): check_python_tier_b(...)`.
  - `check_task()` invokes `TierCTaxonomy.check_tier_c_rows(rows, active_stacks)`, appending hard problems to `check.problems` and heuristic warnings to `check.warnings`.
  - `check_hld()` parses optional `Integration test roots:` via `tc.parse_integration_test_roots(text)` and validates paths via `TierCTaxonomy.validate_integration_test_roots(check.root, roots, check.tracked, created)` (only when `Integration test roots:` is declared in the HLD).
  - `main()` adds `--verbose` and `--json`: default `PASS` prints only `Result: 0 problems — PASS`; `--verbose` prints `Implicit protected paths: ...` followed by `Result: ...`; `--json` prints `{"status": "PASS|FAIL", "problems": [...], "warnings": [...], "implicit_protected_paths": [...]}`.
  - Per `[SE-03]`, update the 3 implicit-protected-path assertions in `test_check_task_contract.py` (`L113`, `L122`, `L618`) to pass `--verbose`.

## Definition of Done

- [ ] `check_task_contract.py` delegates polyglot Tier B checks to `TierBContractAdapter` while preserving legacy Python fallback when no manifests exist (V2, V3, V5)
- [ ] `TierCTaxonomy` hard-fails explicit `Tier C2` rows missing `Needs:` and invalid HLD `Integration test roots:`, and warns on heuristic ungated heavy-runtime `TIER-C` commands (V2, V5)
- [ ] `check_task_contract.py` emits 1-line `Result: 0 problems — PASS` by default with `--verbose` and `--json` opt-in (V2, V3, V5)
- [ ] Existing `test_check_task_contract.py`, `test_check_epic_readiness.py`, and `test_ohk_cmr_and_contracts.py` pass without regressions (V3)
- [ ] `ruff check`, `ruff format --check`, and `mypy` pass across all Allowed files (V4)
- [ ] Fresh JUnit XML report written to `build/test-results/task_04.xml` containing all 5 assigned scenario IDs (V5)

## Dependencies & Blockers

- Blocked by [Task 01](task_01_stack_lifecycle_registry.md) (consumes `_stack_lifecycle_registry.py`).
- Wave 2 — runs in parallel with Task 05.

## References & Rollback

- Reference HLD: [polyglot_lifecycle_and_quality_architecture.md](polyglot_lifecycle_and_quality_architecture.md)
- Rollback: Revert edits to `check_task_contract.py`, `task_contract.py`, and `test_check_task_contract.py`; delete `tests/test_plq_task_contract_polyglot.py`.
