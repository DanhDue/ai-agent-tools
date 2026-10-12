---
id: "task_5_build_ios_quality_provider"
status: "todo"
priority: "high"
assignee: null
epic: "mobile_quality_providers_and_contract_hardening"
dueDate: null
created: "2026-10-12T12:30:00Z"
modified: "2026-10-12T12:30:00Z"
completedAt: null
labels: ["ios", "provider", "tuist", "swiftlint", "quality_check"]
order: "a5"
---

# Task 5: Build iOS Quality Provider

Epic: [mobile_quality_providers_and_contract_hardening](mobile_quality_providers_and_contract_hardening.en.md)

## Requirement Analysis

Build the dedicated `d3nexus:ios-quality-check` skill to provide platform-specific quality assurance for iOS Native codebases.
Crucially, this provider is modeled directly on the canonical ground truth established in the [ios_digital_wallet](file:///Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/) template:
1. **Workspace & Build System**: Compatible with Tuist project generation (`Project.swift`, `Tuist.swift`) and multi-package SwiftPM workspaces (`Packages/*`, `Features/*`).
2. **Formatting & Static Analysis**: Enforces SwiftFormat style compliance (`swiftformat --config quality/.swiftformat --lint .`) and strict SwiftLint static analysis (`swiftlint lint --config quality/.swiftlint.yml --strict`).
3. **Architecture Governance (ArchTests)**: Executes Swift-syntax AST governance rules K1–K10 via dedicated package `swift test --package-path ArchTests`.
4. **Boundary Checks**: Executes `./scripts/check_module_boundaries.sh` with whitelist support (`scripts/module_boundary_whitelist.txt`).
5. **Unit Tests (Tier A)**: Executes isolated Swift package unit tests (`swift test`).
6. **Coverage Governance**: Executes `./scripts/check_coverage_thresholds.sh` parsing `default.profdata` code coverage.
7. **Acceptance Harness (Tier C)**: Executes `./scripts/acceptance_check.sh` verifying end-to-end host app composition and clean builds.
8. **Semantic Audits**: Dispatches specialist audits (`@security-audit`, `@architecture-audit`, `@ios-ui-audit`, `@code-health-audit`).
9. **Contract Emission**: Emits standardized `provider-result.json` matching schema version 1.

## Relevant Files & Context Pointers

- Template Reference: `/Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/Project.swift`.
- Template Scripts & Configs:
  - `/Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/ArchTests/`.
  - `/Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/quality/.swiftlint.yml`.
  - `/Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/quality/.swiftformat`.
  - `/Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/scripts/check_module_boundaries.sh`.
  - `/Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/scripts/check_coverage_thresholds.sh`.
  - `/Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/scripts/acceptance_check.sh`.
- Target Skill: `skills/ios-quality-check/SKILL.md`.
- Target Schema: `skills/ios-quality-check/resources/schemas/ios-quality.schema.json`.
- Target Validator: `skills/ios-quality-check/resources/scripts/validate_ios_quality.py`.
- Target Test: `skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py`.
- Target Fixture: `skills/ios-quality-check/resources/fixtures/valid_ios_quality.json`.

## Design Rationale

The iOS provider reads `.agents/quality/ios-quality.json`. All tools are declared as explicit structured arrays (e.g. `["swift", "test", "--package-path", "ArchTests"]`):
- The provider skill validates `ios-quality.json` schema.
- Resolves candidate commit SHA and working tree state.
- Executes declared capabilities for the requested profile (`pr` or `epic`).
- Evaluates code coverage thresholds against configured standards.
- Emits atomic `provider-result.json` bound to the verified commit SHA.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/ios-quality-check/SKILL.md`: Operational skill definition.
  - `skills/ios-quality-check/resources/scripts/validate_ios_quality.py`: Manifest validator.
  - `skills/ios-quality-check/resources/schemas/ios-quality.schema.json`: JSON schema.
- **Downstream Callers**:
  - `skills/quality_check/SKILL.md`: Invokes provider when `ios-core` is declared in registry.
- **Cross-Platform Bridges**: Reads Swift code coverage metrics.
- **Target Test Coverage Threshold**: 100% validator coverage.

### BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] Validate valid iOS quality capability manifest
  Given an ios-quality.json declaring format, lint, boundaries, architecture, test, and coverage commands
  When validate_ios_quality.py validates the configuration
  Then validation succeeds with exit code 0

Scenario: [Tier A - Unit] Reject iOS manifest with duplicate capability identifiers
  Given an ios-quality.json declaring duplicate "lint" capabilities
  When validate_ios_quality.py validates the configuration
  Then validation fails with error "DUPLICATE_CAPABILITY_ID"

Scenario: [Tier C - Integration] Execute complete iOS quality provider flow
  Given a mock iOS workspace mirroring ios_digital_wallet structure
  When ios-quality-check executes with profile="epic"
  Then swiftformat, swiftlint, ArchTests, unit tests, and coverage harness execute in sequence
  And a valid provider-result.json is emitted bound to candidate SHA
```

## Test & Verification Checklist

- [ ] **RED**: Create test suite `test_validate_ios_quality.py` asserting validation of valid fixtures and rejection of duplicate capability IDs, missing profiles, and empty command arrays. Confirm tests fail.
- [ ] **GREEN**: Implement `ios-quality.schema.json` and `validate_ios_quality.py`. Implement `skills/ios-quality-check/SKILL.md` operational instructions.
- [ ] **REFACTOR**: Align capability structure with `valid_rust_quality.json` and ensure full schema adherence.
- [ ] **Tier A Verification**: Run `python3 -B skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py` and confirm 100% pass.
- [ ] **Tier B Verification**: Verify frontmatter (`name: ios-quality-check`, single-line description) and relative documentation links.

## Definition of Done (DoD)

- `skills/ios-quality-check/` created with `SKILL.md`, schema, fixtures, scripts, and tests.
- Unit tests pass with 100% success.
- Manifest accurately models all `ios_digital_wallet` verification scripts and packages.
- `git status` shows clean, targeted additions.

## Dependencies & Blockers

- Blocked by: [Task 1](task_1_harden_contract_validator.md).
- Blocks: [Task 6](task_6_build_scaffolding_skill.md), [Task 7](task_7_run_e2e_acceptance_and_release.md).

## References & Rollback

- Reference: [iOS Template quality configs in ios_digital_wallet](../../../digital_wallet/ios_digital_wallet/quality/).
- Rollback: Remove `skills/ios-quality-check/` directory.
