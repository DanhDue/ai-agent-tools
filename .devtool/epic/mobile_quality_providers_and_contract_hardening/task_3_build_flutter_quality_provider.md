---
id: "task_3_build_flutter_quality_provider"
status: "done"
priority: "high"
assignee: null
epic: "mobile_quality_providers_and_contract_hardening"
dueDate: null
created: "2026-10-12T12:30:00Z"
modified: "2026-10-12T05:45:44Z"
completedAt: "2026-10-12T05:45:44Z"
labels: ["flutter", "provider", "melos", "quality_check"]
order: "a3"
---

# Task 3: Build Flutter Quality Provider

Epic: [mobile_quality_providers_and_contract_hardening](mobile_quality_providers_and_contract_hardening.en.md)

## Requirement Analysis

Build the dedicated `d3nexus:flutter-quality-check` skill to provide platform-specific quality assurance for Flutter codebases.
Crucially, this provider is modeled directly on the canonical ground truth established in the [bloc_digital_wallet](file:///Users/danhdueexoictif/AllProjects/digital_wallet/bloc_digital_wallet/) template:
1. **Workspace Management**: Compatible with Melos 7.3.0 and Dart Native Pub Workspaces.
2. **Formatting**: Enforces line length 99 via `./scripts/dartfmt.sh` (or `fvm dart format -l 99`).
3. **Static Analysis**: Executes `fvm flutter analyze` against strict `analysis_options.yaml` rules.
4. **Architecture Boundaries**: Executes `./scripts/check_module_boundaries.sh` with whitelist support (`scripts/module_boundary_whitelist.txt`) to block unauthorized cross-feature imports and deep-imports into `data/` or `*_impl.dart`.
5. **License Compliance**: Executes `./scripts/check_license_header.sh` using `addlicense` and `header_template.txt`.
6. **Testing & Coverage**: Executes `melos run test` (root app + feature packages) and `./scripts/testWithCoverage.sh`, parsing `coverage_report/lcov.info` to extract line coverage.
7. **Semantic Audits**: Dispatches specialist audits (`@security-audit`, `@architecture-audit`, `@flutter-ui-audit`, `@code-health-audit`).
8. **Contract Emission**: Emits standardized `provider-result.json` matching schema version 1.

## Relevant Files & Context Pointers

- Template Reference: `/Users/danhdueexoictif/AllProjects/digital_wallet/bloc_digital_wallet/pubspec.yaml`.
- Template Scripts:
  - `/Users/danhdueexoictif/AllProjects/digital_wallet/bloc_digital_wallet/scripts/dartfmt.sh`.
  - `/Users/danhdueexoictif/AllProjects/digital_wallet/bloc_digital_wallet/scripts/check_module_boundaries.sh`.
  - `/Users/danhdueexoictif/AllProjects/digital_wallet/bloc_digital_wallet/scripts/check_license_header.sh`.
  - `/Users/danhdueexoictif/AllProjects/digital_wallet/bloc_digital_wallet/scripts/testWithCoverage.sh`.
- Target Skill: `skills/flutter-quality-check/SKILL.md`.
- Target Schema: `skills/flutter-quality-check/resources/schemas/flutter-quality.schema.json`.
- Target Validator: `skills/flutter-quality-check/resources/scripts/validate_flutter_quality.py`.
- Target Test: `skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py`.
- Target Fixture: `skills/flutter-quality-check/resources/fixtures/valid_flutter_quality.json`.

## Design Rationale

Following the capability model of `rust-quality-check`, the Flutter provider reads `.agents/quality/flutter-quality.json`. The provider contains zero hardcoded commands; all executables (`fvm`, `melos`, bash scripts) are declared in structured command arrays:
- The provider skill validates `flutter-quality.json` schema.
- Resolves repository root and candidate SHA.
- Executes declared capabilities for the requested profile (`pr` or `epic`).
- Evaluates LCOV coverage metrics against declared threshold.
- Emits atomic `provider-result.json` to the target directory.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/flutter-quality-check/SKILL.md`: Operational skill definition.
  - `skills/flutter-quality-check/resources/scripts/validate_flutter_quality.py`: Manifest validator.
  - `skills/flutter-quality-check/resources/schemas/flutter-quality.schema.json`: JSON schema.
- **Downstream Callers**:
  - `skills/quality_check/SKILL.md`: Invokes provider when `flutter-core` is declared in registry.
- **Cross-Platform Bridges**: Reads LCOV coverage format.
- **Target Test Coverage Threshold**: 100% validator coverage.

### BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] Validate valid Flutter quality capability manifest
  Given a flutter-quality.json declaring format, analyze, boundaries, test, and coverage commands
  When validate_flutter_quality.py validates the configuration
  Then validation succeeds with exit code 0

Scenario: [Tier A - Unit] Reject Flutter manifest with missing command executable
  Given a flutter-quality.json declaring capability "test" with an empty command array
  When validate_flutter_quality.py validates the configuration
  Then validation fails with error "COMMAND_ARRAY_EMPTY"

Scenario: [Tier C - Integration] Execute complete Flutter quality provider flow
  Given a mock Flutter workspace mirroring bloc_digital_wallet structure
  When flutter-quality-check executes with profile="epic"
  Then dartfmt, analyze, boundaries, test, and coverage commands execute in sequence
  And a valid provider-result.json is emitted bound to candidate SHA
  And measured coverage is accurately parsed from lcov.info
```

## Test & Verification Checklist

- [x] **RED**: Create test suite `test_validate_flutter_quality.py` asserting validation of valid fixtures and rejection of empty capabilities, missing profiles, and malformed command arrays. Confirm tests fail.
- [x] **GREEN**: Implement `flutter-quality.schema.json` and `validate_flutter_quality.py`. Implement `skills/flutter-quality-check/SKILL.md` operational instructions.
- [x] **REFACTOR**: Align capability structure with `valid_rust_quality.json` and ensure full schema adherence.
- [x] **Tier A Verification**: Run `python3 -B skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py` and confirm 100% pass.
- [x] **Tier B Verification**: Verify frontmatter (`name: flutter-quality-check`, single-line description) and relative documentation links.

## Definition of Done (DoD)

- `skills/flutter-quality-check/` created with `SKILL.md`, schema, fixtures, scripts, and tests.
- Unit tests pass with 100% success.
- Manifest accurately models all `bloc_digital_wallet` verification scripts.
- `git status` shows clean, targeted additions.

## Dependencies & Blockers

- Blocked by: [Task 1](task_1_harden_contract_validator.md).
- Blocks: [Task 6](task_6_build_scaffolding_skill.md), [Task 7](task_7_run_e2e_acceptance_and_release.md).

## References & Rollback

- Reference: [Flutter Template scripts in bloc_digital_wallet](../../../digital_wallet/bloc_digital_wallet/scripts/).
- Rollback: Remove `skills/flutter-quality-check/` directory.
