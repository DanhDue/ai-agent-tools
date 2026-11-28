---
id: "task_03_on_demand_quality_plan_resolver_cli"
status: "todo"
priority: "high"
assignee: null
epic: "shift_left_quality_resolver"
dueDate: null
created: "2026-11-28T10:10:00+07:00"
modified: "2026-11-28T10:10:00+07:00"
completedAt: null
labels: ["architecture", "contract", "cli", "quality-plan"]
order: "a03"
review_tier: "full"
---

# Task 03: On-Demand File-Scoped Quality Plan Resolver Engine and CLI

Epic: [shift_left_quality_resolver](../epic/shift_left_quality_resolver/shift_left_quality_resolver.md)

## Requirement Analysis

Implement the fifth Open-Closed Contract (`QualityPlanResolver`) in `skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py` and wire `"resolve-quality"` into `bin/d3nexus` (Observations `#0024` & `#0025`). Given `--files <planned_files>`, the resolver reads `.agents/quality/check_quality.json`, active `*-quality.json` manifests, `.agents/quality/coverage_floors.json` (when present), and `_stack_lifecycle_registry.py` defaults to emit **5–10 compact lines** (`< 0.1s` cold runtime, `0` untouched-stack noise) detailing canonical/forbidden test roots, dual Web V8 LCOV unit + Playwright Tier C2 rules, coverage/adapter ratchet floors, referencing `?v=` cache-bust templates, and `$D3NEXUS_KIT/skills`-interpolated file-scoped `TIER-B` commands.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py` (new)
- `bin/d3nexus`
- `tests/test_slqr_quality_plan_resolver.py` (new)

Read-only context:
- `.devtool/epic/shift_left_quality_resolver/shift_left_quality_resolver.md`
- `.devtool/epic/shift_left_quality_resolver/bdd_scenarios.md`
- `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py`
- `skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py`
- `tests/test_slqr_registry_and_schemas.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development` and `d3nexus:python-quality-check` (Python 3 stdlib only, zero LLM or git-log subprocess calls so cold runtime stays well below `0.10s`).
- Placing `resolve_task_quality_plan.py` beside `_stack_lifecycle_registry.py` and `check_task_contract.py` allows Task 04 (`check_task_contract.py`) to import the exact same `resolve_quality_plan()` engine, guaranteeing zero divergence between planning advice and Gate 2 / `--check-plan` enforcement.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py` (new): `StackQualityPlan`, `ResolvedQualityPlan`, `QualityPlanError`, `web_requires_lcov_unit_tests()`, `find_cache_bust_templates()`, `is_full_repo_python_tier_b_subcommand()`, `resolve_quality_plan()`, `format_compact_plan()`, and `main()`.
  - `bin/d3nexus` (`L11-L29`): register `"resolve-quality": "skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py"` in `SUBCOMMANDS`.
  - `tests/test_slqr_quality_plan_resolver.py` (new): unit, in-process (`< 0.10s`) and CLI (`< 1.0s`) latency, AST/stdlib purity, and subcutaneous integration tests covering `SLQR-HP-03`, `SLQR-AR-01`, `SLQR-AR-02`, `SLQR-FR-03` (plus unit tests for `find_cache_bust_templates` and `is_full_repo_python_tier_b_subcommand`).
- **Downstream Callers**: `tests/test_slqr_registry_and_schemas.py`, `tests/test_task_contract_ergonomics_e2e.py`.
- **Cross-Platform Bridges**: None.
- **Target Coverage Threshold**: >= 90% on `resolve_task_quality_plan.py`, 100% on LCOV/template/error branches.

### BDD SCENARIOS

Covers: SLQR-HP-03, SLQR-AR-01, SLQR-AR-02, SLQR-FR-03

```gherkin
Scenario: [SLQR-HP-03] [Tier C - Integration] d3nexus resolve-quality emits compact file-scoped guidance within latency budgets
Given a polyglot repository configuring ".agents/quality/python-quality.json", ".agents/quality/web-quality.json" (with V8 LCOV diff_coverage on ".js,.mjs" and ui_review), ".agents/quality/coverage_floors.json", and "src/preview/static/index.html" referencing "align-studio.js?v=20261128"
When resolve_quality_plan() executes in-process and "bin/d3nexus resolve-quality --files src/lyrics_sync/align/ctc.py src/preview/static/align-studio.js --base-ref develop" executes via CLI
Then in-process resolve_quality_plan() completes in under 0.10 seconds (best of 3 runs) and the CLI subprocess exits 0 in under 1.0 second printing between 5 and 10 non-empty lines
And the output specifies canonical test roots for Python and dual Web test requirements (V8 LCOV unit test in "tests/js/*.test.mjs" plus Playwright "# tier: C2")
And the output lists matched adapter/module floors from "coverage_floors.json", names "src/preview/static/index.html" for "?v=" cache-busting, and emits "$D3NEXUS_KIT/skills"-interpolated scoped TIER-B commands

Scenario: [SLQR-AR-01] [Tier C - Integration] Stack lifecycle registry and quality plan resolver maintain zero circular imports and Python 3 stdlib purity
Given "skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py" and "skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py"
When AST imports are inspected and both modules are imported in a clean Python 3 stdlib environment without third-party packages
Then neither module imports "check_task_contract" or "manage_worker_pool", and 100% of imported modules belong to the Python 3 standard library or "_stack_lifecycle_registry"

Scenario: [SLQR-AR-02] [Tier C - Integration] Single-stack Python invocation of resolve-quality emits zero lines mentioning Web, Flutter, Android, iOS, or Rust
Given a polyglot repository containing manifests for all 6 stacks ("python", "web", "flutter", "android", "ios", "rust")
When "d3nexus resolve-quality --files src/worker/pipeline.py tests/unit/worker/test_pipeline.py" executes
Then stdout contains Python test roots, floors, and scoped TIER-B commands, and contains 0 occurrences of "playwright", "lcov", "flutter", "gradlew", "swiftlint", or "clippy"

Scenario: [SLQR-FR-03] [Tier C - Integration] resolve_task_quality_plan exits 2 with clear diagnostic on malformed quality manifest JSON
Given a repository whose ".agents/quality/web-quality.json" contains truncated invalid JSON
When "d3nexus resolve-quality --files src/web/app.js" executes
Then the CLI exits with code 2 and prints a descriptive error message to stderr naming "web-quality.json"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_quality_plan_resolver.py::test_slqr_hp_03_resolve_quality_cli_emits_compact_scoped_lines_within_budget` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_quality_plan_resolver.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_registry_and_schemas.py tests/test_stack_lifecycle_registry.py tests/test_task_contract_ergonomics_e2e.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py bin/d3nexus tests/test_slqr_quality_plan_resolver.py && ruff format --check skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py bin/d3nexus tests/test_slqr_quality_plan_resolver.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py bin/d3nexus tests/test_slqr_quality_plan_resolver.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_quality_plan_resolver.py --junitxml=build/test-results/slqr_task_03.xml` | exit 0; results build/test-results/slqr_task_03.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`audit_ui_state_and_styles.py` `L405-L455`, `_stack_lifecycle_registry.py` `L191-L481`, `bin/d3nexus` `L11-L29`)**: `audit_ui_state_and_styles.py` scans `*.html`, `*.astro`, `*.jinja`, `*.jinja2` with `(?:src|href)=['"][^'"]*?{re.escape(static_filename)}(\?[^'"]*)?['"]`; `bin/d3nexus` dispatches subcommands via `SUBCOMMANDS`.
- **New contract (`resolve_task_quality_plan.py`)**:
  - `web_requires_lcov_unit_tests(web_manifest: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]`: returns `(True, lcov_globs)` when `capabilities.diff_coverage` or `capabilities.test_unit` references `.info` or `--lcov` (and `--source-ext` is absent or includes `.js`/`.mjs`), defaulting `lcov_globs` to `test_routing.lcov_unit_test_globs` or `("tests/js/*.test.mjs", "*.test.mjs", "*.test.js", "*.test.ts")`.
  - `find_cache_bust_templates(repo_root: Path, modified_assets: Sequence[str], web_manifest: Mapping[str, Any] | None) -> list[str]`: active when `web_manifest` defines `capabilities.ui_review` or `test_routing.cache_bust_extensions`; walks non-ignored repo dirs (skipping `.git`, `node_modules`, `build`, `dist`, `.worktrees`, `.venv`, `venv`, `target`, `.astro`, `.dart_tool`, `.gradle`, `Pods`, `coverage`) matching `(?:src|href)=['"][^'"]*?{re.escape(asset_name)}(\?[^'"]*)?['"]` on `*.html`, `*.astro`, `*.jinja`, `*.jinja2`.
  - Scoped `TIER-B` synthesis: replaces `{skills_dir}` with `"$D3NEXUS_KIT/skills"` and `{base_ref}` with `base_ref` (default `"develop"`), strips trailing full-repo targets (`.`, `src`, `tests`) on file-scoping tools (`ruff`, `mypy`, `pyright`, `dart format`) and substitutes the task's matching source/test paths (appending `<test_files>` placeholder if no test path was supplied). Also exports `is_full_repo_python_tier_b_subcommand(sub: Sequence[str], cap: Sequence[str] | None = None) -> bool` consumed by Task 04 (`SLQR-EC-04`).

## Definition of Done

- [ ] `skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py` implements `QualityPlanResolver` (`resolve_quality_plan`, `format_compact_plan`, `--files`, `--repo-root`, `--base-ref`, `--json`) in pure Python 3 stdlib (V2, V4, V5)
- [ ] `bin/d3nexus` registers `resolve-quality`, completing `resolve_quality_plan()` in `< 0.10s` in-process (best of 3) and CLI invocations in `< 1.0s` emitting 5–10 compact stack-filtered lines with zero untouched-stack noise (V2, V5)
- [ ] Assigned scenarios (`SLQR-HP-03`, `SLQR-AR-01`, `SLQR-AR-02`, `SLQR-FR-03`) pass in `tests/test_slqr_quality_plan_resolver.py` with JUnit XML at `build/test-results/slqr_task_03.xml` (V2, V5)
- [ ] Registry and schema regression suites pass without regressions (V3)
- [ ] `ruff check`, `ruff format --check`, and `mypy` pass across all Allowed files (V4)

## Dependencies & Blockers

- Blocked by [Task 01](../epic/shift_left_quality_resolver/task_01_registry_prefix_wrappers_and_provider_schemas.md)

## References & Rollback

- Reference HLD: [shift_left_quality_resolver.md](../epic/shift_left_quality_resolver/shift_left_quality_resolver.md)
- Rollback: Revert `bin/d3nexus` and delete `skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py` and `tests/test_slqr_quality_plan_resolver.py`.
