---
id: "task_06_lifecycle_docs_provider_skills_and_acceptance"
status: "todo"
priority: "high"
assignee: null
epic: "polyglot_lifecycle_and_quality_architecture"
dueDate: null
created: "2026-11-27T09:18:00+07:00"
modified: "2026-11-27T09:18:00+07:00"
completedAt: null
labels: ["docs", "skills", "verify", "acceptance"]
order: "a06"
review_tier: "full"
---

# Task 06: Lifecycle & Provider Skill Documentation, `verify.sh` Registration, and End-to-End Acceptance Suite

Epic: [polyglot_lifecycle_and_quality_architecture](../epic/polyglot_lifecycle_and_quality_architecture/polyglot_lifecycle_and_quality_architecture.md)

## Requirement Analysis

Finalize documentation, skill references, `scripts/verify.sh` suite registration, and end-to-end polyglot acceptance verification:

1. Update lifecycle skills and references (`skills/dev-designer/SKILL.md`, `skills/dev-designer/references/verification-rows.md`, `skills/dev-designer/references/verification-row-grammar.md`, `skills/dev-implementation/SKILL.md`, `skills/dev-implementation/references/worker-execution-rules.md`) to:
   - Replace hardcoded `uv run pytest` fixer/tier prose with concise 6-stack platform-mapped commands (`python`, `flutter`, `rust`, `web`, `android`, `ios`).
   - Standardize `Tier C1` (mandatory fast host/VM subcutaneous integration `< 5s`: `test/integration/*_integration_test.dart`, `cargo nextest`, Vitest/Node wire tests, `tests/integration/`, JVM/Robolectric `*FlowTest`, `swift test --filter *FlowTests`) vs `Tier C2` (`Needs:`-gated device/simulator/Playwright E2E).
   - Reference `_stack_lifecycle_registry.py`, `TierBContractAdapter`, `PoolWorkspaceStrategy`, `TriageSurfaceRegistry`, `TierCTaxonomy`, compact 1-line `PASS` CLI output (`--verbose` / `--json`), and `{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py`.
   - Strictly obey `skills/dev-implementation/SKILL.md <= 4500` words (`[SE-02]`), `skills/dev-designer/SKILL.md <= 22528` UTF-8 bytes, and preserve `"-q --tb=short --maxfail=3"` in `verification-rows.md`.
2. Update `skills/quality_check/SKILL.md`, `skills/setup_quality_check/SKILL.md`, and all 6 `skills/*-quality-check/SKILL.md` files (frontmatter exclusively `name` + `description`; `d3nexus:` namespace only; reference every new script and schema under `skills/` so `verify.sh` §8 passes; remove Android `pkill -9 java` doc mention).
3. Register all 6 new test suites (`tests/test_stack_lifecycle_registry.py`, `tests/test_check_diff_coverage.py`, `tests/test_plq_quality_contracts_and_scaffolder.py`, `tests/test_plq_task_contract_polyglot.py`, `tests/test_plq_worker_pool_polyglot.py`, `tests/test_plq_end_to_end_acceptance.py`) in `scripts/verify.sh` (`SUITES`).
4. Create `tests/test_plq_end_to_end_acceptance.py` proving full end-to-end polyglot lifecycle integration (scaffold -> task contract check -> worker pool sync & triage -> diff-coverage) and verifying doc structure, word/byte caps, `verify.sh` registration, and reference reachability.

## Files

Allowed files:
- `skills/dev-designer/SKILL.md`
- `skills/dev-designer/references/verification-rows.md`
- `skills/dev-designer/references/verification-row-grammar.md`
- `skills/dev-implementation/SKILL.md`
- `skills/dev-implementation/references/worker-execution-rules.md`
- `skills/quality_check/SKILL.md`
- `skills/setup_quality_check/SKILL.md`
- `skills/flutter-quality-check/SKILL.md`
- `skills/rust-quality-check/SKILL.md`
- `skills/web-quality-check/SKILL.md`
- `skills/python-quality-check/SKILL.md`
- `skills/android-quality-check/SKILL.md`
- `skills/ios-quality-check/SKILL.md`
- `scripts/verify.sh`
- `tests/test_plq_end_to_end_acceptance.py` (new)

Read-only context:
- `.devtool/epic/polyglot_lifecycle_and_quality_architecture/polyglot_lifecycle_and_quality_architecture.md`
- `.devtool/epic/polyglot_lifecycle_and_quality_architecture/bdd_scenarios.md`
- `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py` (new)
- `skills/quality_check/resources/scripts/check_diff_coverage.py` (new)
- `skills/quality_check/resources/scripts/_provider_manifest_common.py` (new)
- `skills/web-quality-check/resources/schemas/web-quality.schema.json` (new)
- `tests/test_tto_docs_and_slimming.py`
- `tests/test_fpg_governance_text.py`
- `scripts/test_verifiable_handoff_text.py`
- `scripts/test_lifecycle_document_contract.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development`, `d3nexus:doc_quality_check`, and `AGENTS.md` kit authoring rules (`SKILL.md` frontmatter strictly `name` + `description`, `d3nexus:` cross-references, never `superpowers:` under `skills/`).
- Keep `skills/dev-implementation/SKILL.md` concise (`<= 4500` words) by placing detailed 6-stack fixer/Tier C1/Tier C2 command tables in `skills/dev-implementation/references/worker-execution-rules.md` and `skills/dev-designer/references/verification-rows.md`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/SKILL.md` (`L160-L172` Tier Separation & BDD automation, `L207-L215` Fix Loop & Triage, `L300-L311` review-fixer platform-mapped scoped tests — currently 342 lines / 4123 words, keep `<= 4500` words)
  - `scripts/verify.sh` (`SUITES` list `L362-L482` — append Section 25 Polyglot Lifecycle & Quality Architecture suites)
  - `skills/dev-designer/SKILL.md`, `skills/dev-designer/references/verification-rows.md`, `skills/dev-designer/references/verification-row-grammar.md`, `skills/dev-implementation/references/worker-execution-rules.md`, `skills/quality_check/SKILL.md`, `skills/setup_quality_check/SKILL.md`, and 6 `skills/*-quality-check/SKILL.md` (all <= 200 lines)
  - `tests/test_plq_end_to_end_acceptance.py` (new): End-to-end polyglot lifecycle pipeline & documentation acceptance tests (`PLQ-HP-06`, `PLQ-ST-05`, `PLQ-AR-05`).
- **Downstream Callers**: `tests/test_tto_docs_and_slimming.py`, `tests/test_fpg_governance_text.py`, `tests/test_fpg_english_only_text.py`, `scripts/test_verifiable_handoff_text.py`, `scripts/test_lifecycle_document_contract.py`, `tests/test_ohk_docs_and_acceptance.py`, `tests/test_ohk2_skill_docs.py`.
- **Cross-Platform Bridges**: None.
- **Target Coverage Threshold**: 100% pass across all documentation, frontmatter, word/byte cap, reference-reachability, and end-to-end polyglot pipeline checks.

### BDD SCENARIOS

Covers: PLQ-HP-06, PLQ-ST-05, PLQ-AR-05

```gherkin
Scenario: [PLQ-HP-06] [Tier C - Integration] Lifecycle docs, provider skills, and verify.sh registry pass full structural and word-cap checks
Given all updated dev-designer, dev-implementation, quality_check, setup_quality_check, and 6 stack quality-check SKILL.md files plus scripts/verify.sh
When end-to-end documentation, frontmatter, reference-reachability, and Tier C1/Tier C2 contract assertions execute
Then dev-implementation/SKILL.md stays <= 4500 words and dev-designer/SKILL.md stays <= 22528 UTF-8 bytes
And every newly created script and schema under skills/ is referenced by at least one tracked file
And all 6 new polyglot test suites are registered in scripts/verify.sh SUITES

Scenario: [PLQ-ST-05] [Tier C - Integration] End-to-end polyglot lifecycle pipeline transitions cleanly from scaffold to contract check to pool triage
Given a synthetic polyglot repo (Flutter + Rust + Python) initialized via scaffold_quality_manifest.py
When check_task_contract.py validates a polyglot task, manage_worker_pool.py syncs and triages a low-risk fix in slot 1, and check_diff_coverage.py checks a passing LCOV + Cobertura diff
Then every CLI stage exits with code 0 and emits compact one-line PASS summaries where applicable

Scenario: [PLQ-AR-05] [Tier C - Integration] Documentation cross-references obey d3nexus namespace and exclude forbidden prefixes
Given all modified SKILL.md and references/*.md files in dev-designer, dev-implementation, quality_check, setup_quality_check, and the 6 *-quality-check skills
When frontmatter, markdown lint (check_document.py), and namespace checks run
Then every SKILL.md frontmatter contains exclusively "name" and "description"
And zero files under skills/ contain the forbidden "superpowers:" prefix
And dev-designer/references/verification-rows.md preserves "-q --tb=short --maxfail=3" alongside 6-stack Tier C1/Tier C2 examples
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_plq_end_to_end_acceptance.py::test_plq_hp_06_docs_caps_reachability_and_verify_registration` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_plq_end_to_end_acceptance.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_docs_and_slimming.py tests/test_fpg_governance_text.py tests/test_fpg_english_only_text.py scripts/test_verifiable_handoff_text.py tests/test_ohk_docs_and_acceptance.py tests/test_ohk2_skill_docs.py tests/test_stack_lifecycle_registry.py tests/test_check_diff_coverage.py tests/test_plq_quality_contracts_and_scaffolder.py tests/test_plq_task_contract_polyglot.py tests/test_plq_worker_pool_polyglot.py && python3 scripts/test_lifecycle_document_contract.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_plq_end_to_end_acceptance.py && ruff format --check tests/test_plq_end_to_end_acceptance.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_plq_end_to_end_acceptance.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_plq_end_to_end_acceptance.py --junitxml=build/test-results/task_06.xml` | exit 0; results build/test-results/task_06.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`skills/dev-implementation/SKILL.md` `L306`, `skills/dev-designer/references/verification-rows.md` `L1-L138`, `skills/dev-implementation/references/worker-execution-rules.md` `L1-L41`)**: Currently hardcodes `uv run pytest` in review-fixer prose and lacks explicit `Tier C1` vs `Tier C2` tables across all 6 stacks.
- **New contract**:
  - `dev-implementation/SKILL.md` replaces hardcoded `uv run pytest` at `L306` with a concise pointer to the 6-stack command table in `references/worker-execution-rules.md` and documents `_stack_lifecycle_registry.py` (`TierBContractAdapter`, `PoolWorkspaceStrategy`, `TriageSurfaceRegistry`, `TierCTaxonomy`) concisely while staying `<= 4500` words (`[SE-02]`).
  - `dev-designer/references/verification-rows.md` preserves `"-q --tb=short --maxfail=3"` and distinguishes `Tier C1` (`< 5s` host/VM subcutaneous integration: `test/integration/*_integration_test.dart`, `cargo nextest`, Vitest/Node wire tests, `tests/integration/`, JVM/Robolectric `*FlowTest`, `swift test --filter *FlowTests`) from `Tier C2` (`Needs:`-gated simulator/emulator/device/Playwright E2E) across all 6 stacks.
  - `dev-designer/references/verification-row-grammar.md` updates the `Implicit protected paths` section to document default compact 1-line `PASS` stdout (`Result: 0 problems — PASS`), opt-in `--verbose` / `--json` flags, and the canonical `# tier: C2` trailing command comment marker enforced by `TierCTaxonomy`.
  - `quality_check/SKILL.md`, `setup_quality_check/SKILL.md` (explicitly removing `pkill -9 java` at `L26`), and all 6 `*-quality-check/SKILL.md` files (explicitly removing `pkill -9 java` in `android-quality-check/SKILL.md` at `L59`) document 4 profiles, unified capabilities, dual-floor coverage, `standards_catalog.json`, `task_tier_b`/`triage_surfaces`/`pool_mounts`, compact 1-line `PASS` validator output (`--verbose` / `--json`; JSON default preserved for `validate_quality_contract.py registry`/`invocation`/`reconcile` with `--compact`), and link `_provider_manifest_common.py`, `check_diff_coverage.py`, and `web-quality.schema.json` (ensuring `verify.sh` §8 passes).
  - `scripts/verify.sh` adds Section 25 registering all 6 new test suites (`tests/test_stack_lifecycle_registry.py`, `tests/test_check_diff_coverage.py`, `tests/test_plq_quality_contracts_and_scaffolder.py`, `tests/test_plq_task_contract_polyglot.py`, `tests/test_plq_worker_pool_polyglot.py`, `tests/test_plq_end_to_end_acceptance.py`).

## Definition of Done

- [ ] Lifecycle docs (`dev-designer`, `dev-implementation`) standardize 6-stack commands and `Tier C1` vs `Tier C2` within word/byte caps (V2, V3, V5)
- [ ] `quality_check`, `setup_quality_check`, and all 6 `*-quality-check/SKILL.md` files document additive v1 capabilities, compact CLI output, and link every new script/schema (V2, V5)
- [ ] All 6 new test suites are registered in `scripts/verify.sh` (`SUITES`) (V2, V5)
- [ ] All documentation, governance, and polyglot task regression suites pass without regressions (V3)
- [ ] `ruff check`, `ruff format --check`, and `mypy` pass on `tests/test_plq_end_to_end_acceptance.py` (V4)
- [ ] Fresh JUnit XML report written to `build/test-results/task_06.xml` containing all 3 assigned scenario IDs (V5)

## Dependencies & Blockers

- Blocked by [Task 01](../epic/polyglot_lifecycle_and_quality_architecture/task_01_stack_lifecycle_registry.md), [Task 02](../epic/polyglot_lifecycle_and_quality_architecture/task_02_portable_diff_coverage_engine.md), [Task 03](../epic/polyglot_lifecycle_and_quality_architecture/task_03_quality_schemas_validators_and_scaffolder.md), [Task 04](../epic/polyglot_lifecycle_and_quality_architecture/task_04_polyglot_task_contract_and_tier_c_gate.md), [Task 05](../epic/polyglot_lifecycle_and_quality_architecture/task_05_worker_pool_cow_mounts_and_suffix_triage.md).
- Wave 3 — final integration and acceptance task.

## References & Rollback

- Reference HLD: [polyglot_lifecycle_and_quality_architecture.md](../epic/polyglot_lifecycle_and_quality_architecture/polyglot_lifecycle_and_quality_architecture.md)
- Rollback: Revert edits to lifecycle/provider docs and `scripts/verify.sh`; delete `tests/test_plq_end_to_end_acceptance.py`.
