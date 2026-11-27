---
id: "task_03_quality_schemas_validators_and_scaffolder"
status: "todo"
priority: "high"
assignee: null
epic: "polyglot_lifecycle_and_quality_architecture"
dueDate: null
created: "2026-11-27T09:18:00+07:00"
modified: "2026-11-27T09:18:00+07:00"
completedAt: null
labels: ["quality_check", "schemas", "validators", "scaffolder"]
order: "a03"
review_tier: "full"
---

# Task 03: Unified Quality Schemas, Shared Validator Helper, Compact CLI Output, and Scaffolder Upgrade

Epic: [polyglot_lifecycle_and_quality_architecture](../epic/polyglot_lifecycle_and_quality_architecture/polyglot_lifecycle_and_quality_architecture.md)

## Requirement Analysis

Upgrade the quality registry contract, all 6 stack provider schemas and validators (`flutter`, `rust`, `web`, `python`, `android`, `ios`), and `setup_quality_check` (`scaffold_quality_manifest.py` + templates) with strict additive v1 backwards compatibility:

1. Create `skills/quality_check/resources/scripts/_provider_manifest_common.py` for shared additive v1 validation (`standards_catalog`, `extensions`, `task_tier_b`, object-shaped `triage_surfaces` with regex validation, dual-floor `coverage` fields `min_package_coverage`, `exclude_package_floor`, `min_diff_coverage`, `diff_base`) and compact 1-line `PASS` / expanded `BLOCKED`/`FAIL` / `--verbose` / `--json` CLI formatting.
2. Update `skills/quality_check/resources/schemas/check-quality.schema.json` and `validate_quality_contract.py` to support optional `"pool_mounts"` (`{path, mode: symlink|cow_copy}` rejecting path traversal) and compact 1-line `PASS` CLI output (`--verbose` / `--json` opt-in).
3. Create `skills/web-quality-check/resources/schemas/web-quality.schema.json` and update the 5 existing provider schemas (`flutter`, `rust`, `python`, `android`, `ios`) and all 6 `validate_*_quality.py` scripts to support 4 profiles (`pr`, `epic`, `scheduled`, `release`, keeping only `pr` and `epic` required), unified capabilities (`anti_stub`, `security`, `security_deps`, `pr_diff_audit`, `workspace_audit`, `pr_impact`, `workspace_impact`, `license`), dual-floor `coverage`, additive top-level keys, and compact 1-line `PASS` CLI output. Remove `"cleanup": ["pkill", "-9", "java"]` from `valid_android_quality.json` (keeping `cleanup` optional in `android-quality.schema.json` for legacy repo compatibility).
4. Update `scaffold_quality_manifest.py` and templates (`polyglot-check-quality.template.json`, `web-quality.template.json`) to scaffold all 4 profiles, unified capabilities, starter `.agents/quality/standards_catalog.json` (non-overwriting), `{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py` hooks, stack-appropriate `"pool_mounts"`, and zero Android `pkill -9 java`.

## Files

Allowed files:
- `skills/quality_check/resources/scripts/_provider_manifest_common.py` (new)
- `skills/quality_check/resources/schemas/check-quality.schema.json`
- `skills/quality_check/resources/scripts/validate_quality_contract.py`
- `skills/quality_check/resources/scripts/test_validate_quality_contract.py`
- `skills/flutter-quality-check/resources/schemas/flutter-quality.schema.json`
- `skills/flutter-quality-check/resources/scripts/validate_flutter_quality.py`
- `skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py`
- `skills/rust-quality-check/resources/schemas/rust-quality.schema.json`
- `skills/rust-quality-check/resources/scripts/validate_rust_quality.py`
- `skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py`
- `skills/web-quality-check/resources/schemas/web-quality.schema.json` (new)
- `skills/web-quality-check/resources/scripts/validate_web_quality.py`
- `skills/python-quality-check/resources/schemas/python-quality.schema.json`
- `skills/python-quality-check/resources/scripts/validate_python_quality.py`
- `skills/python-quality-check/resources/scripts/test_validate_python_quality.py`
- `skills/android-quality-check/resources/schemas/android-quality.schema.json`
- `skills/android-quality-check/resources/scripts/validate_android_quality.py`
- `skills/android-quality-check/resources/scripts/test_validate_android_quality.py`
- `skills/android-quality-check/resources/fixtures/valid_android_quality.json`
- `skills/ios-quality-check/resources/schemas/ios-quality.schema.json`
- `skills/ios-quality-check/resources/scripts/validate_ios_quality.py`
- `skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py`
- `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`
- `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py`
- `skills/setup_quality_check/resources/templates/polyglot-check-quality.template.json`
- `skills/setup_quality_check/resources/templates/web-quality.template.json`
- `tests/test_plq_quality_contracts_and_scaffolder.py` (new)

Read-only context:
- `.devtool/epic/polyglot_lifecycle_and_quality_architecture/polyglot_lifecycle_and_quality_architecture.md`
- `.devtool/epic/polyglot_lifecycle_and_quality_architecture/bdd_scenarios.md`
- `skills/quality_check/resources/scripts/verify_polyglot_registry.py`
- `tests/test_web_quality_provider.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development` and `d3nexus:python-quality-check`.
- Keep all Python library function return dicts (`validate_registry`, `validate_*_config`, `validate_manifest`) 100% unchanged so `verify_polyglot_registry.py` and existing callers need zero edits.
- Place shared validation logic and CLI formatting in `_provider_manifest_common.py` imported via `Path(__file__).resolve().parents[3] / "quality_check" / "resources" / "scripts"` so all 6 provider validators stay DRY and consistent.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/quality_check/resources/scripts/validate_quality_contract.py` (`validate_registry` `L50-L200`, `validate_capability_manifest` `L566-L674`, `main` `L675-L745`)
  - `skills/quality_check/resources/scripts/test_validate_quality_contract.py` (`QualityContractTests` `L1-L416`)
  - `skills/web-quality-check/resources/scripts/validate_web_quality.py` (`validate_manifest` `L40-L215`, `main` `L679-L720`)
  - `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py` (`detect_platforms` `L166-L225`, `build_registry_data` `L226-L243`, `scaffold_quality_manifests` `L244-L314`, `main` `L315-L378`)
  - `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py` (`ScaffoldQualityManifestTests` `L1-L292`)
  - `skills/quality_check/resources/scripts/_provider_manifest_common.py` (new): `validate_additive_provider_fields`, `validate_dual_floor_coverage`, `validate_pool_mounts`, `format_validator_cli_output`.
  - `skills/web-quality-check/resources/schemas/web-quality.schema.json` (new).
  - `tests/test_plq_quality_contracts_and_scaffolder.py` (new).
- **Downstream Callers**: `skills/quality_check/resources/scripts/verify_polyglot_registry.py`, `skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`, `tests/test_web_quality_provider.py`, `tests/test_polyglot_gate4.py`.
- **Cross-Platform Bridges**: None.
- **Target Coverage Threshold**: >= 90% on `_provider_manifest_common.py` and modified validator/scaffolder branches; 100% on `pool_mounts`, `standards_catalog`, and `triage_surfaces` rejection paths.

### BDD SCENARIOS

Covers: PLQ-HP-03, PLQ-EC-05, PLQ-ST-01, PLQ-AR-02, PLQ-FR-03

```gherkin
Scenario: [PLQ-HP-03] [Tier C - Integration] Scaffolder generates 4-profile unified manifests and validators emit compact one-line PASS
Given a polyglot repository containing Cargo.toml, pubspec.yaml, package.json, pyproject.toml, build.gradle.kts, and Package.swift
When scaffold_quality_manifest.py scaffolds check_quality.json, all 6 <stack>-quality.json manifests, and standards_catalog.json
Then every generated manifest defines all 4 profiles ("pr", "epic", "scheduled", "release"), unified capabilities ("anti_stub", "security", "security_deps", "pr_diff_audit", "workspace_audit", "pr_impact", "workspace_impact", "license"), "standards_catalog", dual-floor coverage referencing check_diff_coverage.py, and Android omits "cleanup" ("pkill -9 java")
And validate_quality_contract.py and all 6 validate_<stack>_quality.py CLIs exit 0 with a single stdout line starting with "PASS:"

Scenario: [PLQ-EC-05] [Tier C - Integration] Legacy v1 manifests without scheduled/release or new additive fields still pass validation
Given legacy check_quality.json and all 6 legacy <stack>-quality.json fixtures containing only schema_version 1, pr/epic profiles, and original capability keys
When validate_quality_contract.py and all 6 validate_<stack>_quality.py validators run for profile "pr" and "epic"
Then every validator returns status "PASS" with 0 findings

Scenario: [PLQ-ST-01] [Tier C - Integration] Scaffolder does not overwrite existing standards_catalog.json and validates all 4 profiles
Given a repository that already contains a customized ".agents/quality/standards_catalog.json" with sentinel content "CUSTOM-RULE-01"
When scaffold_quality_manifest.py runs on that repository
Then ".agents/quality/standards_catalog.json" retains "CUSTOM-RULE-01" byte-for-byte
And generated provider manifests reference ".agents/quality/standards_catalog.json" and validate PASS across profiles "pr", "epic", "scheduled", and "release"

Scenario: [PLQ-AR-02] [Tier C - Integration] Web provider schema matches draft 2020-12 parity with the other 5 provider schemas
Given all 6 provider JSON schemas (flutter, rust, web, python, android, ios) under skills/*-quality-check/resources/schemas/
When the test suite inspects each schema's top-level properties, capabilities properties, coverage properties, and profile keys
Then all 6 schemas declare additionalProperties: false, schema_version const 1, profiles pr/epic/scheduled/release, unified capabilities (anti_stub, security, security_deps, pr_diff_audit, workspace_audit, pr_impact, workspace_impact, license), dual-floor coverage keys, standards_catalog, extensions, task_tier_b, and object-shaped triage_surfaces

Scenario: [PLQ-FR-03] [Tier C - Integration] Validators reject invalid pool_mounts, standards_catalog traversal, non-object triage_surfaces, and bad regexes
Given a check_quality.json with pool_mounts mode "hardlink" and path "/etc/passwd", and a python-quality.json with standards_catalog "../escape.json", triage_surfaces as a JSON array instead of an object, and an invalid regex in triage_surfaces.api_wire
When validate_quality_contract.py and validate_python_quality.py validate these configs
Then both return status "BLOCKED" with deterministic finding codes and exit code 1 in CLI mode
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_plq_quality_contracts_and_scaffolder.py::test_plq_ar_02_all_six_schemas_have_unified_parity` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_plq_quality_contracts_and_scaffolder.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 skills/quality_check/resources/scripts/test_validate_quality_contract.py skills/quality_check/resources/scripts/test_quality_provider_acceptance.py skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py skills/python-quality-check/resources/scripts/test_validate_python_quality.py skills/android-quality-check/resources/scripts/test_validate_android_quality.py skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py tests/test_web_quality_provider.py tests/test_polyglot_gate4.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/quality_check/resources/scripts/_provider_manifest_common.py skills/quality_check/resources/scripts/validate_quality_contract.py skills/quality_check/resources/scripts/test_validate_quality_contract.py skills/flutter-quality-check/resources/scripts/validate_flutter_quality.py skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py skills/rust-quality-check/resources/scripts/validate_rust_quality.py skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py skills/web-quality-check/resources/scripts/validate_web_quality.py skills/python-quality-check/resources/scripts/validate_python_quality.py skills/python-quality-check/resources/scripts/test_validate_python_quality.py skills/android-quality-check/resources/scripts/validate_android_quality.py skills/android-quality-check/resources/scripts/test_validate_android_quality.py skills/ios-quality-check/resources/scripts/validate_ios_quality.py skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py tests/test_plq_quality_contracts_and_scaffolder.py && ruff format --check skills/quality_check/resources/scripts/_provider_manifest_common.py skills/quality_check/resources/scripts/validate_quality_contract.py skills/quality_check/resources/scripts/test_validate_quality_contract.py skills/flutter-quality-check/resources/scripts/validate_flutter_quality.py skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py skills/rust-quality-check/resources/scripts/validate_rust_quality.py skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py skills/web-quality-check/resources/scripts/validate_web_quality.py skills/python-quality-check/resources/scripts/validate_python_quality.py skills/python-quality-check/resources/scripts/test_validate_python_quality.py skills/android-quality-check/resources/scripts/validate_android_quality.py skills/android-quality-check/resources/scripts/test_validate_android_quality.py skills/ios-quality-check/resources/scripts/validate_ios_quality.py skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py tests/test_plq_quality_contracts_and_scaffolder.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/quality_check/resources/scripts/_provider_manifest_common.py skills/quality_check/resources/scripts/validate_quality_contract.py skills/quality_check/resources/scripts/test_validate_quality_contract.py skills/flutter-quality-check/resources/scripts/validate_flutter_quality.py skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py skills/rust-quality-check/resources/scripts/validate_rust_quality.py skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py skills/web-quality-check/resources/scripts/validate_web_quality.py skills/python-quality-check/resources/scripts/validate_python_quality.py skills/python-quality-check/resources/scripts/test_validate_python_quality.py skills/android-quality-check/resources/scripts/validate_android_quality.py skills/android-quality-check/resources/scripts/test_validate_android_quality.py skills/ios-quality-check/resources/scripts/validate_ios_quality.py skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py tests/test_plq_quality_contracts_and_scaffolder.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_plq_quality_contracts_and_scaffolder.py --junitxml=build/test-results/task_03.xml` | exit 0; results build/test-results/task_03.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Additive v1 schema keys** (all optional at schema and validator level to keep existing repos valid):
  - Registry (`check-quality.schema.json` + `validate_quality_contract.py`): top-level `pool_mounts` array of `{"path": string, "mode": "symlink" | "cow_copy"}`; reject empty/absolute paths or `..` segments with finding codes `invalid_pool_mount_path` / `invalid_pool_mount_mode`.
  - All 6 provider schemas + `_provider_manifest_common.py`:
    - Top-level: `standards_catalog` (relative string without `..`, finding `invalid_standards_catalog_path`), `extensions` (`list[str]` matching `^\.[a-z0-9]+$`, finding `invalid_extensions`), `task_tier_b` (object with optional `format_prefixes`, `lint_prefixes`, `typecheck_prefixes`, `boundary_prefixes`, `boundary_triggers`, `require_all_allowed_files_in_format`), `triage_surfaces` (object with allowed keys `signature`, `api_wire`, `persistence`, `concurrency`, `test_weakening` -> `list[str]` valid regexes, findings `invalid_triage_surfaces_format`, `unknown_triage_surface_category`, `invalid_triage_surface_regex`).
    - Capabilities: add `anti_stub`, `security`, `security_deps`, `pr_diff_audit`, `workspace_audit`, `pr_impact`, `workspace_impact`, `license` across all 6 schemas alongside existing stack-native capabilities.
    - Dual-floor `coverage` optional keys: `min_package_coverage` (`0..1`), `exclude_package_floor` (`list[str]`), `min_diff_coverage` (`0..1`), `diff_base` (`str`), `lcov_path` / `report_path` / `profdata_path` (`str`).
- **Compact CLI output across all 7 validators**:
  - Add `--verbose` and `--json` flags to `validate_quality_contract.py` and all 6 `validate_*_quality.py` CLIs.
  - Default `PASS`: single line (`PASS: <label> (profile=<profile>, caps=<n>)` or `PASS: <subcommand> (...)`).
  - Default `BLOCKED`/`FAIL`: summary line plus one line per finding (`  - <code>: <message>`).
  - `--json`: preserves exact full JSON payload `json.dumps(res, indent=2)`.
- **Android `pkill -9 java` removal**: Remove `"cleanup": ["pkill", "-9", "java"]` from `scaffold_quality_manifest.py` and `skills/android-quality-check/resources/fixtures/valid_android_quality.json`; keep `cleanup` optional in `android-quality.schema.json` strictly for legacy consumer manifest compatibility.
- **Scaffolder `standards_catalog.json`**: Create starter `.agents/quality/standards_catalog.json` with ISO/IEC 25010:2023, ISO/IEC 27001/27002:2022, OWASP, and CWE skeleton entries ONLY if the file does not already exist (never overwrite existing customized catalogs).

## Definition of Done

- [ ] `_provider_manifest_common.py` and `web-quality.schema.json` created and all 6 provider schemas + `check-quality.schema.json` upgraded with additive v1 parity (V2, V5)
- [ ] All 7 validator CLIs emit compact 1-line `PASS` stdout by default with `--verbose` and `--json` opt-in while preserving Python dict APIs (V2, V3, V5)
- [ ] `scaffold_quality_manifest.py` scaffolds 4 profiles, unified capabilities, `standards_catalog.json` (non-overwriting), `check_diff_coverage.py` hooks, `pool_mounts`, and omits Android `pkill -9 java` (V2, V3, V5)
- [ ] All existing validator, scaffolder, and polyglot acceptance tests pass without regressions (V3)
- [ ] `ruff check`, `ruff format --check`, and `mypy` pass across all Python Allowed files (V4)
- [ ] Fresh JUnit XML report written to `build/test-results/task_03.xml` containing all 5 assigned scenario IDs (V5)

## Dependencies & Blockers

- None (Wave 1 — runs in parallel with Task 01 and Task 02).

## References & Rollback

- Reference HLD: [polyglot_lifecycle_and_quality_architecture.md](../epic/polyglot_lifecycle_and_quality_architecture/polyglot_lifecycle_and_quality_architecture.md)
- Rollback: Revert modified schema/validator/scaffolder files and delete `_provider_manifest_common.py`, `web-quality.schema.json`, and `tests/test_plq_quality_contracts_and_scaffolder.py`.
