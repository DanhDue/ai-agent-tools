---
id: "task_01_registry_prefix_wrappers_and_provider_schemas"
status: "todo"
priority: "high"
assignee: null
epic: "shift_left_quality_resolver"
dueDate: null
created: "2026-11-28T10:10:00+07:00"
modified: "2026-11-28T10:10:00+07:00"
completedAt: null
labels: ["architecture", "contract", "registry", "schema"]
order: "a01"
review_tier: "full"
---

# Task 01: Registry Wrapper/Placeholder Normalization and Six-Stack Provider Schema Parity

Epic: [shift_left_quality_resolver](../epic/shift_left_quality_resolver/shift_left_quality_resolver.md)

## Requirement Analysis

Extend `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py` and `skills/quality_check/resources/scripts/_provider_manifest_common.py` along with all six `*-quality.schema.json` files so manifest-derived `TIER-B` prefixes normalize `{skills_dir}` and unwrap monorepo/version-manager wrappers (`uv --directory <dir> run`, `uv --project <dir> run`, `mise exec [--]`, `npm --prefix <dir>`), Web defaults recognize `check_vanilla_js.py`, `_match_prefix_on_tokens()` matches `.py`/`.sh` script basenames plus required flags across relocated paths, and all six provider JSON Schemas accept additive `test_routing`, `coverage.package_floors`, Flutter `architecture`, and Rust/Web/Python `cache_enable`/`cache_purge` capabilities.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py`
- `skills/quality_check/resources/scripts/_provider_manifest_common.py`
- `skills/flutter-quality-check/resources/schemas/flutter-quality.schema.json`
- `skills/rust-quality-check/resources/schemas/rust-quality.schema.json`
- `skills/web-quality-check/resources/schemas/web-quality.schema.json`
- `skills/python-quality-check/resources/schemas/python-quality.schema.json`
- `skills/android-quality-check/resources/schemas/android-quality.schema.json`
- `skills/ios-quality-check/resources/schemas/ios-quality.schema.json`
- `tests/test_slqr_registry_and_schemas.py` (new)

Read-only context:
- `.devtool/epic/shift_left_quality_resolver/shift_left_quality_resolver.md`
- `.devtool/epic/shift_left_quality_resolver/bdd_scenarios.md`
- `tests/test_stack_lifecycle_registry.py`
- `tests/test_plq_quality_contracts_and_scaffolder.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development` and `d3nexus:python-quality-check` (Python 3 stdlib only, zero circular imports into `check_task_contract.py` or `manage_worker_pool.py`).
- Normalizing `{skills_dir}` -> `$D3NEXUS_KIT/skills` and matching `.py`/`.sh` script basenames + required `--flag` names eliminates per-repository `task_tier_b` workarounds (Observation `#0022`).
- Keeping `test_routing` and `coverage.package_floors` strictly additive under `schema_version: 1` guarantees 100% backward compatibility across existing manifests while failing closed (`BLOCKED`) on unknown keys or `..` path traversal.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py` (`L114-L169`, `L333-L382`, `L576-L656`, `L739-L820`, `L875-L945`, `L984-L1064`): add `TestRoutingPolicy` onto `StackDescriptor`, add `"check_vanilla_js.py"` to `BUILTIN_STACKS["web"].default_tier_b.typecheck_prefixes`, unwrap `uv --directory`/`--project`, `mise exec [--]`, and `npm --prefix` in `_strip_command_wrappers()`, normalize `{skills_dir}` and strip `--base-ref {base_ref}` in `_cap_command_str()`, load `test_routing` in `_load_repo_manifests()`, and generalize `.py`/`.sh` basename + required-flag matching in `_match_prefix_on_tokens()`.
  - `skills/quality_check/resources/scripts/_provider_manifest_common.py` (`L38-L50`, `L130-L187`, `L189-L319`): add `TEST_ROUTING_KEYS`, validate `package_floors` in `validate_dual_floor_coverage()`, and validate `test_routing` in `validate_additive_provider_fields()`.
  - `skills/flutter-quality-check/resources/schemas/flutter-quality.schema.json` (`L80-L215`): add top-level `test_routing`, `coverage.properties.package_floors`, and `capabilities.properties.architecture`.
  - `skills/rust-quality-check/resources/schemas/rust-quality.schema.json` (`L80-L245`): add top-level `test_routing`, `coverage.properties.package_floors`, and `capabilities.properties.cache_enable` + `cache_purge`.
  - `skills/web-quality-check/resources/schemas/web-quality.schema.json` (`L80-L240`): add top-level `test_routing`, `coverage.properties.package_floors`, and `capabilities.properties.cache_enable` + `cache_purge`.
  - `skills/python-quality-check/resources/schemas/python-quality.schema.json` (`L80-L240`): add top-level `test_routing`, `coverage.properties.package_floors`, and `capabilities.properties.cache_enable` + `cache_purge`.
  - `skills/android-quality-check/resources/schemas/android-quality.schema.json` (`L80-L230`): add top-level `test_routing` and `coverage.properties.package_floors`.
  - `skills/ios-quality-check/resources/schemas/ios-quality.schema.json` (`L80-L225`): add top-level `test_routing` and `coverage.properties.package_floors`.
  - `tests/test_slqr_registry_and_schemas.py` (new): unit and subcutaneous integration tests covering `SLQR-HP-01`, `SLQR-EC-01`, `SLQR-AR-01`, `SLQR-FR-01`.
- **Downstream Callers**: `tests/test_stack_lifecycle_registry.py`, `tests/test_plq_quality_contracts_and_scaffolder.py`.
- **Cross-Platform Bridges**: None (kit Python & JSON Schema contracts).
- **Target Coverage Threshold**: >= 90% across modified registry/validator functions, 100% on `test_routing` fail-closed error paths.

### BDD SCENARIOS

Covers: SLQR-HP-01, SLQR-EC-01, SLQR-AR-01, SLQR-FR-01

```gherkin
Scenario: [SLQR-HP-01] [Tier C - Integration] Provider schemas and runtime validators accept additive test_routing, package_floors, architecture, and cache capabilities
Given all 6 stack JSON Schemas ("*-quality.schema.json") and runtime validators ("validate_*_quality.py")
When manifests declaring optional "test_routing", "coverage.package_floors", Flutter "architecture", and Rust/Web/Python "cache_enable" and "cache_purge" are validated across profiles ("pr", "epic", "scheduled", "release")
Then all 6 runtime validators return status "PASS" with 0 findings
And every capability key accepted by each runtime validator exists in the corresponding JSON Schema "capabilities.properties"

Scenario: [SLQR-EC-01] [Tier C - Integration] TierBContractAdapter unwraps monorepo directory flags, mise exec prefixes, and relocated script paths
Given stack manifests declaring "uv --directory apps/align-worker run ruff check .", "mise exec -- swiftlint lint --config quality/.swiftlint.yml --strict", and "python3 {skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py --target-dir src/preview"
When TierBContractAdapter.validate_tier_b evaluates task TIER-B rows using "uv --directory apps/align-worker run ruff check apps/align-worker/src/mod.py", "swiftlint lint --config quality/.swiftlint.yml --strict Packages/Core/Sources/Foo.swift", and "python3 \"$D3NEXUS_KIT/skills/web-quality-check/resources/scripts/check_vanilla_js.py\" --target-dir src/preview"
Then all three TIER-B subcommands match their respective stack capabilities with 0 problems

Scenario: [SLQR-AR-01] [Tier C - Integration] Stack lifecycle registry and quality plan resolver maintain zero circular imports and Python 3 stdlib purity
Given "skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py" and "skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py"
When AST imports are inspected and both modules are imported in a clean Python 3 stdlib environment without third-party packages
Then neither module imports "check_task_contract" or "manage_worker_pool", and 100% of imported modules belong to the Python 3 standard library or "_stack_lifecycle_registry"

Scenario: [SLQR-FR-01] [Tier C - Integration] Provider manifest validators fail closed on invalid test_routing keys or path traversal globs
Given a provider manifest containing unknown key "test_routing.rogue_key" or traversal glob "test_routing.canonical_test_globs": ["../outside/test_*.py"]
When validate_additive_provider_fields runs via any stack validator
Then validation fails closed with status "BLOCKED" and finding code "invalid_test_routing"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_registry_and_schemas.py::test_slqr_hp_01_provider_schemas_and_validators_accept_additive_contracts` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_registry_and_schemas.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_stack_lifecycle_registry.py tests/test_plq_quality_contracts_and_scaffolder.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py skills/quality_check/resources/scripts/_provider_manifest_common.py tests/test_slqr_registry_and_schemas.py && ruff format --check skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py skills/quality_check/resources/scripts/_provider_manifest_common.py tests/test_slqr_registry_and_schemas.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py skills/quality_check/resources/scripts/_provider_manifest_common.py tests/test_slqr_registry_and_schemas.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_registry_and_schemas.py --junitxml=build/test-results/slqr_task_01.xml` | exit 0; results build/test-results/slqr_task_01.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`_stack_lifecycle_registry.py` `L158-L169`, `L349-L361`, `L576-L656`, `L739-L775`, `L984-L1042`; `_provider_manifest_common.py` `L130-L319`)**: `StackDescriptor` currently holds `extensions`, `test_path_patterns`, `default_tier_b`, `default_surfaces`, and `tier_c_policy`; `_cap_command_str` joins raw tokens with `{skills_dir}` intact; `_match_prefix_on_tokens` Rule 4 requires `plen == 1` for `.py`/`.sh` scripts; `_strip_command_wrappers` only handles `uv run` when `toks[1] == "run"`.
- **New contract**:
  - `TestRoutingPolicy(canonical_test_globs=(), forbidden_test_globs=(), paired_source_globs=(), lcov_unit_test_globs=(), cache_bust_extensions=())` added as an optional field (`test_routing: TestRoutingPolicy = TestRoutingPolicy()`) on `StackDescriptor` so existing positional/keyword callers stay 100% compatible.
  - `TEST_ROUTING_KEYS = ("canonical_test_globs", "forbidden_test_globs", "paired_source_globs", "lcov_unit_test_globs", "cache_bust_extensions")`; `validate_additive_provider_fields` emits finding code `"invalid_test_routing"` when `test_routing` is non-dict, has unknown keys, has empty/non-list values, contains `..`/absolute paths in glob keys, or contains strings not matching `EXTENSION_PATTERN` in `cache_bust_extensions`.
  - `validate_dual_floor_coverage` accepts `"package_floors"` validated via `is_safe_relative_path()` (emitting `"invalid_coverage_config"` if invalid).
  - `_strip_command_wrappers` unwraps `uv [--directory <d>|--project <d>|-q|--quiet|--frozen|--offline|--no-sync]... run`, `mise exec [<tool@ver>...] --` (or `mise x --`), and `npm [--prefix <d>] exec [--]`.
  - In `SLQR-AR-01` inside `tests/test_slqr_registry_and_schemas.py`, inspect `_stack_lifecycle_registry.py` unconditionally and inspect `resolve_task_quality_plan.py` when present (Task 03 also re-verifies `SLQR-AR-01` once `resolve_task_quality_plan.py` is created).
  - In TDD `RED` (`V1`), `test_slqr_hp_01_provider_schemas_and_validators_accept_additive_contracts` asserts `"test_routing"` is in `flutter-quality.schema.json` `properties` so `V1` exits `1` with `FAILED` before implementation.

## Definition of Done

- [ ] `_stack_lifecycle_registry.py` implements `TestRoutingPolicy`, Web `"check_vanilla_js.py"` typecheck default, `{skills_dir}` normalization, monorepo/mise wrapper stripping, and `.py`/`.sh` script basename + required-flag matching (V2, V5)
- [ ] `_provider_manifest_common.py` and all 6 `*-quality.schema.json` files validate `test_routing`, `coverage.package_floors`, Flutter `architecture`, and Rust/Web/Python `cache_enable`/`cache_purge` cleanly while failing closed on invalid `test_routing` (V2, V5)
- [ ] All 4 assigned scenarios (`SLQR-HP-01`, `SLQR-EC-01`, `SLQR-AR-01`, `SLQR-FR-01`) pass in `tests/test_slqr_registry_and_schemas.py` with JUnit XML written to `build/test-results/slqr_task_01.xml` (V2, V5)
- [ ] Existing stack lifecycle registry and provider schema/scaffolder regression suites pass without regressions (V3)
- [ ] `ruff check`, `ruff format --check`, and `mypy` pass across all Allowed Python files (V4)

## Dependencies & Blockers

- None (Wave 1 root task, parallel with Task 02).

## References & Rollback

- Reference HLD: [shift_left_quality_resolver.md](../epic/shift_left_quality_resolver/shift_left_quality_resolver.md)
- Rollback: Revert changes to `_stack_lifecycle_registry.py`, `_provider_manifest_common.py`, and the 6 `*-quality.schema.json` files, and delete `tests/test_slqr_registry_and_schemas.py`.
