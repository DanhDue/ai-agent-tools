---
id: "task_04_fail_closed_task_and_plan_contract_guards"
status: "done"
priority: "high"
assignee: null
epic: "shift_left_quality_resolver"
dueDate: null
created: "2026-11-28T10:10:00+07:00"
modified: "2026-11-28T05:04:42Z"
completedAt: "2026-11-28T05:04:42Z"
labels: ["architecture", "contract", "validation", "shift-left"]
order: "a04"
review_tier: "full"
---

# Task 04: Fail-Closed Task and Standalone Plan Contract Guards in check_task_contract.py

Epic: [shift_left_quality_resolver](shift_left_quality_resolver.md)

## Requirement Analysis

Upgrade `skills/dev-implementation/resources/scripts/check_task_contract.py` to close Observation `#0022` and enforce the fail-closed Shift-Left quality-layer invariants of Observation `#0025` across both epic tasks (`--design`, Gate 2) and standalone `/writing-plans` documents (`--check-plan <plan.md>`): (1) fix `_cap_tool_prefix()` and `matches_cap()` so multi-target `type_check`/`lint` manifests (`uv run mypy --strict src tests`, `ruff check --extend-select ... .`) accept task-scoped `Allowed files` commands unconditionally; (2) reject unexpanded `{skills_dir}`/`{base_ref}` placeholders; (3) reject full-repo Python `TIER-B` targets (`.` or `src tests`) on intermediate tasks (`Task 1..N-1`); (4) enforce Web V8 LCOV unit-test presence when touching production `.js`/`.mjs` in LCOV `diff_coverage` repos; (5) enforce `test_routing` (`forbidden_test_globs`, `canonical_test_globs`, `paired_source_globs`) and atomic `?v=` cache-bust template inclusion; and (6) add `--check-plan <plan.md>` parsing `### Task N:` blocks and enforcing the same guards plus bare-`npx` checks.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- `tests/test_slqr_task_and_plan_contracts.py` (new)

Read-only context:
- `.devtool/epic/shift_left_quality_resolver/shift_left_quality_resolver.md`
- `.devtool/epic/shift_left_quality_resolver/bdd_scenarios.md`
- `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py`
- `skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py` (new)
- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
- `tests/test_plq_task_contract_polyglot.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development` and `d3nexus:python-quality-check` (Python 3 stdlib only, deterministic error messages).
- Assert on the **mechanism, not merely exit code `1`** (`skill-authoring.md` Pre-Flight Principle): every negative test in `SLQR-FR-04` and `SLQR-ST-03` isolates one violation and asserts its exact guard substring.
- Preserve 100% compatibility for repos without `.agents/quality/` (`SLQR-AR-03`) and for historical done-task checks (`allow_historical_prefix=True`).

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/check_task_contract.py` (`L805-L824`, `L1043-L1160`, `L1440-L1540`, `L1660-L1750`): expand `_cap_tool_prefix()` (handling monorepo `uv --directory`, `python3 -m`, and value-taking flags `--extend-select`, `--select`, `--ignore`, `--per-file-ignores`, `--config`, `--config-file`, `--target-version`, `--line-length`, `--python-version`), enable prefix matching unconditionally in `matches_cap()`, add `check_shift_left_quality_guards()` in `--design` mode, add `check_standalone_plan()` + `--check-plan <path>` CLI mode in `main()`.
  - `tests/test_slqr_task_and_plan_contracts.py` (new): positive and isolated negative contract tests covering `SLQR-HP-04`, `SLQR-ST-03`, `SLQR-AR-03`, `SLQR-FR-04` (plus end-to-end `check_task_contract.py` assertions for `SLQR-EC-03` & `SLQR-EC-04`).
- **Downstream Callers**: `skills/dev-implementation/resources/scripts/test_check_task_contract.py`, `tests/test_plq_task_contract_polyglot.py`, `tests/test_slqr_quality_plan_resolver.py`.
- **Cross-Platform Bridges**: None.
- **Target Coverage Threshold**: >= 90% on new `check_task_contract.py` functions, 100% across all five fail-closed guard branches.

### BDD SCENARIOS

Covers: SLQR-HP-04, SLQR-EC-03, SLQR-EC-04, SLQR-ST-03, SLQR-AR-03, SLQR-FR-04

```gherkin
Scenario: [SLQR-HP-04] [Tier C - Integration] check_task_contract validates multi-target mypy and skills_dir commands in both --design and --check-plan modes
Given a repository whose "python-quality.json" sets type_check to ["uv", "run", "mypy", "--strict", "src", "tests"] and lint to ["uv", "run", "ruff", "check", "--extend-select", "F821,B904", "."] and whose "web-quality.json" sets type_check to ["python3", "{skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py", "--target-dir", "src/preview"] without a manual task_tier_b override
When check_task_contract.py runs "--design" on epic tasks and "--check-plan" on a standalone plan whose commands scope ruff and mypy to Allowed ".py" files, expand "$D3NEXUS_KIT/skills/.../check_vanilla_js.py", include a "tests/js/*.test.mjs" unit test, and include referencing "?v=" HTML templates
Then both "--design" and "--check-plan" exit 0 with "Result: 0 problems — PASS"

Scenario: [SLQR-EC-03] [Tier C - Integration] Bundled ES module imports without src/href template attributes do not trigger false-positive cache-bust template requirements
Given a Web repository with "ui_review" enabled where "apps/web/src/store.ts" and "apps/web/src/helper.js" are imported via ES "import" statements and never referenced in "<script src=...>" or "<link href=...>" attributes inside ".astro" or ".html" templates
When resolve_task_quality_plan.py and check_task_contract.py evaluate a task modifying "apps/web/src/helper.js" (with a paired ".test.mjs" unit test)
Then cache_bust_templates is empty and check_task_contract.py exits 0 without demanding unrelated ".astro" or ".html" templates

Scenario: [SLQR-EC-04] [Tier C - Integration] Final epic task (Task N) and pyproject.toml edits are permitted to run workspace-wide Python static checks
Given a 2-task Python epic where Task 1 modifies only "src/pkg/a.py" and Task 2 (the final task) or a task modifying "pyproject.toml" runs "uv run mypy --strict src tests"
When check_task_contract.py --design validates the epic
Then Task 2 (final task) and any task listing "pyproject.toml" in Allowed files pass without a full-repo TIER-B scope error, whereas Task 1 fails if it uses bare "src tests" instead of Allowed files

Scenario: [SLQR-ST-03] [Tier C - Integration] Fixing violations in a standalone Markdown plan transitions check_task_contract --check-plan from exit 1 FAIL to exit 0 PASS idempotently
Given a standalone Markdown plan in "docs/superpowers/plans/2026-11-28-demo.md" initially containing literal "{skills_dir}", bare "npx playwright test", and a modified ".js" asset missing both its ".test.mjs" LCOV test and referencing "index.html"
When check_task_contract.py --check-plan runs before and after remediating those four defects
Then the initial run exits 1 reporting all four distinct contract problems and repeated post-fix runs exit 0 idempotently with "Result: 0 problems — PASS"

Scenario: [SLQR-AR-03] [Tier C - Integration] Repositories without .agents/quality manifests bypass manifest-only Shift-Left guards without false positives
Given a minimal Git repository without a ".agents/quality/" directory containing an epic HLD and Python task file with valid scoped ruff and mypy TIER-B rows
When check_task_contract.py --design executes against that repository
Then manifest-specific LCOV, test_routing, and cache-bust guards self-skip cleanly and check_task_contract.py exits 0

Scenario: [SLQR-FR-04] [Tier C - Integration] check_task_contract --design fails closed on each independent Shift-Left violation with distinct guard diagnostics
Given a polyglot repository with LCOV Web diff_coverage, "ui_review", and Python/Web "test_routing" rules ("forbidden_test_globs": ["tests/test_*.py", "scripts/test_*.py"], "paired_source_globs": ["src/api/**/*.py"])
When check_task_contract.py --design evaluates negative task fixtures separately testing: (1) Playwright-only Web task touching "src/static/app.js" without a JS unit test, (2) new test placed at forbidden "tests/test_rogue.py", (3) new "src/api/routes.py" missing a paired unit test, (4) modified "src/static/app.js" omitting referencing "src/static/index.html" ("?v="), and (5) unexpanded "{skills_dir}" in TIER-B
Then each of the five negative fixtures exits 1 and reports the exact diagnostic corresponding to that specific guard mechanism
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_task_and_plan_contracts.py::test_slqr_hp_04_multi_target_mypy_and_skills_dir_pass_design_and_check_plan` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_task_and_plan_contracts.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 skills/dev-implementation/resources/scripts/test_check_task_contract.py tests/test_plq_task_contract_polyglot.py tests/test_slqr_quality_plan_resolver.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/check_task_contract.py tests/test_slqr_task_and_plan_contracts.py && ruff format --check skills/dev-implementation/resources/scripts/check_task_contract.py tests/test_slqr_task_and_plan_contracts.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/check_task_contract.py tests/test_slqr_task_and_plan_contracts.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_task_and_plan_contracts.py --junitxml=build/test-results/slqr_task_04.xml` | exit 0; results build/test-results/slqr_task_04.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`check_task_contract.py` `L805-L824`, `L1098-L1130`, `L1660-L1750`)**: `matches_cap` currently checks `sub == cap`, `sub[:len(cap)-1] == cap[:-1]`, `sub[:len(cap)] == cap`, and gates `_cap_tool_prefix(cap)` behind `allow_historical_prefix`; `main()` currently requires `--hld` and `--tasks` unconditionally.
- **New contract (`check_task_contract.py`)**:
  - `_cap_tool_prefix(cap)` & `matches_cap()`: `_cap_tool_prefix(cap)` retains runner wrappers (`uv [--directory <d>] run`, `python3 -m`), tool binary, subcommand (`check`, `format`), and flags (including value-taking flags `--extend-select`, `--select`, `--ignore`, `--per-file-ignores`, `--config`, `--config-file`, `--target-version`, `--line-length`, `--python-version`). When `allow_historical_prefix` is `True`, `len(sub) > len(prefix) and sub[:len(prefix)] == prefix` matches as before. When `allow_historical_prefix` is `False` (`todo` / active tasks), the `_cap_tool_prefix(cap)` fallback matches ONLY when `len(sub) > len(prefix)`, `sub[:len(prefix)] == prefix`, `allowed_py` (non-glob `.py` paths in `Allowed files`) is non-empty, every path in `allowed_py` is covered by the subcommand's non-flag positional targets (`_target_covers_path(t, p)`), and every positional target `t` either covers at least one `allowed_py` path or is in `cap[len(prefix):]`. This keeps `test_todo_task_still_rejected_when_omitting_newly_registered_targets` (`test_check_task_contract.py:1035-1056`) green and blocks `mypy unrelated.py` on single-file tasks!
  - CLI: `--check-plan <Path>` is optional; when `--check-plan` is provided, `--hld` and `--tasks` are not required (passing both `--check-plan` and `--hld`/`--tasks` raises `UsageError` -> `exit 2`).
  - Intermediate-task full-repo Python `TIER-B` guard: applies in `--design` (when `not allow_historical_prefix`, `len(tasks) >= 2`, task is not the highest-numbered / final task, and `pyproject.toml` / `.agents/quality/` not in `Allowed files`) and in `--check-plan` (when `len(plan_tasks) >= 2`, task is not the final task, and `pyproject.toml` not in task files). Flags Python `ruff` / `mypy` / `pyright` subcommands whose manifest `cap` ends in `"."` or `["src", "tests"]` (or when `python-quality.json` is absent) when the subcommand still passes bare `"."` or both `"src"` and `"tests"` instead of scoping to the task's `Allowed files` (so manifests like `ai-agent-tools` that list explicit check paths are never false-flagged).
  - `?v=` cache-bust template guard: fires when modifying an existing non-test `.js` or `.css` file (not `(new)`) that is referenced via `(?:src|href)=['"][^'"]*?<basename>(\?[^'"]*)?['"]` in a tracked template (`*.html`, `*.astro`, `*.jinja`, `*.jinja2`) inside a repository whose `web-quality.json` defines `ui_review` or `test_routing.cache_bust_extensions`, requiring every matched template to appear in the same task's `Allowed files` (or `Modify:` in `--check-plan`).
  - Bare `npx` guard in `--check-plan`: reuses the exact same `npx --no-install` / `npx --yes --package <pkg>` check already enforced on task `Verification` rows.

## Definition of Done

- [x] `check_task_contract.py` `_cap_tool_prefix()` and `matches_cap()` support multi-target `type_check`/`lint` manifests (`mypy --strict src tests`, `ruff check --extend-select ... .`) for scoped `Allowed files` while rejecting unrelated targets and preserving `test_check_task_contract.py` (V2, V3, V5) — exit 0, all contract and regression tests passed
- [x] `check_task_contract.py --design` enforces all 5 Shift-Left quality-layer guards while self-skipping cleanly when `.agents/quality/` is absent or `allow_existing_done_new` / historical done tasks are checked (V2, V3, V5) — exit 0, all 5 guards and self-skip cases verified
- [x] `check_task_contract.py --check-plan <plan.md>` validates standalone `/writing-plans` files and fails closed on `{skills_dir}`, bare `npx`, missing LCOV JS unit tests, forbidden test dirs, missing paired tests, and omitted `?v=` templates (V2, V5) — exit 0, fail-to-pass idempotency and CLI edges verified
- [x] All 6 assigned scenarios (`SLQR-HP-04`, `SLQR-EC-03`, `SLQR-EC-04`, `SLQR-ST-03`, `SLQR-AR-03`, `SLQR-FR-04`) and all existing contract regression suites pass with JUnit XML at `build/test-results/slqr_task_04.xml` (V2, V3, V5) — exit 0, 6/6 BDD scenarios covered PASS
- [x] `ruff check`, `ruff format --check`, and `mypy` pass across all Allowed files (V4) — exit 0, 0 diagnostics

## Dependencies & Blockers

- Blocked by [Task 01](task_01_registry_prefix_wrappers_and_provider_schemas.md), [Task 03](task_03_on_demand_quality_plan_resolver_cli.md)

## References & Rollback

- Reference HLD: [shift_left_quality_resolver.md](shift_left_quality_resolver.md)
- Rollback: Revert `skills/dev-implementation/resources/scripts/check_task_contract.py` and delete `tests/test_slqr_task_and_plan_contracts.py`.
