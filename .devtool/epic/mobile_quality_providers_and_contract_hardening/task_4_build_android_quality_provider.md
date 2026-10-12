---
id: "task_4_build_android_quality_provider"
status: "done"
priority: "high"
assignee: null
epic: "mobile_quality_providers_and_contract_hardening"
dueDate: null
created: "2026-10-12T12:30:00Z"
modified: "2026-10-12T05:47:39Z"
completedAt: "2026-10-12T05:47:39Z"
labels: ["android", "provider", "gradle", "konsist", "quality_check"]
order: "a4"
---

# Task 4: Build Android Quality Provider

Epic: [mobile_quality_providers_and_contract_hardening](mobile_quality_providers_and_contract_hardening.en.md)

## Requirement Analysis

Build the dedicated `d3nexus:android-quality-check` skill to provide platform-specific quality assurance for Android Native codebases.
Crucially, this provider is modeled directly on the canonical ground truth established in the [android_digital_wallet](file:///Users/danhdueexoictif/AllProjects/digital_wallet/android_digital_wallet/) template:
1. **Formatting & Static Quality**: Spotless code formatting (`./gradlew spotlessCheck`) and Detekt static analysis (`./gradlew detekt`).
2. **Public ABI Governance (BCV)**: Binary Compatibility Validator (`./gradlew apiCheck`) enforcing API surface stability across foundation packages (`core`, `platform`, `network`, `ui_kit`).
3. **Architecture Governance (Konsist)**: Clean Architecture rule verification via `:konsist-test:test` with boundary whitelist support (`scripts/konsist_boundary_whitelist.txt`).
4. **Unit Tests (Tier A)**: Executes `./gradlew testDebugUnitTest` across all modules.
5. **Coverage Reporting**: Evaluates Jacoco test reports (`./gradlew jacocoTestReport`) against target coverage threshold.
6. **Acceptance Harness (Tier C)**: Executes `./scripts/acceptance_check.sh` to prove module composition, dynamic feature splitting, and clean builds.
7. **Resource Management**: Executes `pkill -9 java` to release hanging Gradle daemons.
8. **Semantic Audits**: Dispatches specialist audits (`@security-audit`, `@architecture-audit`, `@android-ui-audit`, `@code-health-audit`).
9. **Contract Emission**: Emits standardized `provider-result.json` matching schema version 1.

## Relevant Files & Context Pointers

- Template Reference: `/Users/danhdueexoictif/AllProjects/digital_wallet/android_digital_wallet/build.gradle.kts`.
- Template Scripts & Modules:
  - `/Users/danhdueexoictif/AllProjects/digital_wallet/android_digital_wallet/konsist-test/`.
  - `/Users/danhdueexoictif/AllProjects/digital_wallet/android_digital_wallet/scripts/konsist_boundary_whitelist.txt`.
  - `/Users/danhdueexoictif/AllProjects/digital_wallet/android_digital_wallet/scripts/acceptance_check.sh`.
  - `/Users/danhdueexoictif/AllProjects/digital_wallet/android_digital_wallet/buildSrc/src/main/kotlin/codeanalyzetools/`.
- Target Skill: `skills/android-quality-check/SKILL.md`.
- Target Schema: `skills/android-quality-check/resources/schemas/android-quality.schema.json`.
- Target Validator: `skills/android-quality-check/resources/scripts/validate_android_quality.py`.
- Target Test: `skills/android-quality-check/resources/scripts/test_validate_android_quality.py`.
- Target Fixture: `skills/android-quality-check/resources/fixtures/valid_android_quality.json`.

## Design Rationale

The Android provider reads `.agents/quality/android-quality.json`. All commands are declared as explicit structured arrays (e.g. `["./gradlew", "spotlessCheck"]`):
- The provider skill validates `android-quality.json` schema.
- Resolves candidate SHA and working directory.
- Executes declared capabilities for the requested profile (`pr` or `epic`).
- Always executes cleanup commands (`pkill -9 java`) upon completion to prevent memory exhaustion.
- Emits atomic `provider-result.json` bound to the verified commit SHA.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/android-quality-check/SKILL.md`: Operational skill definition.
  - `skills/android-quality-check/resources/scripts/validate_android_quality.py`: Manifest validator.
  - `skills/android-quality-check/resources/schemas/android-quality.schema.json`: JSON schema.
- **Downstream Callers**:
  - `skills/quality_check/SKILL.md`: Invokes provider when `android-core` is declared in registry.
- **Cross-Platform Bridges**: None (Standard Library Python 3.10+).
- **Target Test Coverage Threshold**: 100% validator coverage.

### BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] Validate valid Android quality capability manifest
  Given an android-quality.json declaring format, lint, bcv, architecture, test, and acceptance commands
  When validate_android_quality.py validates the configuration
  Then validation succeeds with exit code 0

Scenario: [Tier A - Unit] Reject Android manifest missing required profile
  Given an android-quality.json omitting the required "epic" profile
  When validate_android_quality.py validates the configuration
  Then validation fails with error "MISSING_REQUIRED_PROFILE"

Scenario: [Tier C - Integration] Execute complete Android quality provider flow
  Given a mock Android workspace mirroring android_digital_wallet structure
  When android-quality-check executes with profile="epic"
  Then Spotless, Detekt, apiCheck, Konsist, unit tests, and acceptance harness execute in sequence
  And Gradle daemons are terminated via cleanup
  And a valid provider-result.json is emitted bound to candidate SHA
```

## Test & Verification Checklist

- [x] **RED**: Create test suite `test_validate_android_quality.py` asserting validation of valid fixtures and rejection of malformed capability arrays, missing profiles, and empty commands. Confirm tests fail.
- [x] **GREEN**: Implement `android-quality.schema.json` and `validate_android_quality.py`. Implement `skills/android-quality-check/SKILL.md` operational instructions.
- [x] **REFACTOR**: Align capability structure with `valid_rust_quality.json` and ensure full schema adherence.
- [x] **Tier A Verification**: Run `python3 -B skills/android-quality-check/resources/scripts/test_validate_android_quality.py` and confirm 100% pass.
- [x] **Tier B Verification**: Verify frontmatter (`name: android-quality-check`, single-line description) and relative documentation links.

## Definition of Done (DoD)

- `skills/android-quality-check/` created with `SKILL.md`, schema, fixtures, scripts, and tests.
- Unit tests pass with 100% success.
- Manifest accurately models all `android_digital_wallet` verification scripts and tasks.
- `git status` shows clean, targeted additions.

## Dependencies & Blockers

- Blocked by: [Task 1](task_1_harden_contract_validator.md).
- Blocks: [Task 6](task_6_build_scaffolding_skill.md), [Task 7](task_7_run_e2e_acceptance_and_release.md).

## References & Rollback

- Reference: [Android Template build scripts in android_digital_wallet](../../../digital_wallet/android_digital_wallet/build.gradle.kts).
- Rollback: Remove `skills/android-quality-check/` directory.
