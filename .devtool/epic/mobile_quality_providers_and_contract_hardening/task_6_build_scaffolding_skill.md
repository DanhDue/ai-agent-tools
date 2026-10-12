---
id: "task_6_build_scaffolding_skill"
status: "done"
priority: "high"
assignee: null
epic: "mobile_quality_providers_and_contract_hardening"
dueDate: null
created: "2026-10-12T12:30:00Z"
modified: "2026-10-12T05:53:51Z"
completedAt: "2026-10-12T05:53:51Z"
labels: ["scaffolding", "onboarding", "automation", "python"]
order: "a6"
---

# Task 6: Build Scaffolding and Onboarding Skill

Epic: [mobile_quality_providers_and_contract_hardening](mobile_quality_providers_and_contract_hardening.en.md)

## Requirement Analysis

Build the automated onboarding skill `d3nexus:setup_quality_check` to eliminate adoption friction for both Greenfield (new codebases) and Brownfield (legacy codebases before maintenance).
1. **Repository Inspection**:
   - Detects Rust: `Cargo.toml`.
   - Detects Flutter: `pubspec.yaml` or `melos.yaml`.
   - Detects Android: `build.gradle.kts` or `settings.gradle.kts`.
   - Detects iOS: `Project.swift`, `Tuist.swift`, or `Package.swift`.
   - Detects Polyglot composites: Registers multiple providers when multiple platform roots coexist.
2. **Deterministic Manifest Generation**:
   - Generates `.agents/quality/check_quality.json` with appropriate provider IDs and required profiles.
   - Generates matching platform capability configurations pre-populated with tools matching the canonical templates:
     - Flutter (`flutter-quality.json`): `./scripts/dartfmt.sh`, `fvm flutter analyze`, `./scripts/check_module_boundaries.sh`, `./scripts/check_license_header.sh`, `./scripts/testWithCoverage.sh`.
     - Android (`android-quality.json`): `./gradlew spotlessCheck`, `./gradlew detekt`, `./gradlew apiCheck`, `./gradlew :konsist-test:test`, `./gradlew testDebugUnitTest`, `pkill -9 java`.
     - iOS (`ios-quality.json`): `swiftformat --config quality/.swiftformat --lint .`, `swiftlint lint --config quality/.swiftlint.yml --strict`, `swift test --package-path ArchTests`, `./scripts/check_module_boundaries.sh`, `swift test`, `./scripts/check_coverage_thresholds.sh`.
     - Rust (`rust-quality.json`): `cargo fmt --check`, `cargo clippy`, `cargo test`, `cargo llvm-cov`.
3. **Baseline Certification**:
   - Runs an initial `@quality_check` with profile `pr` to verify that newly generated configurations execute cleanly and establish a certified baseline.
4. **Idempotence and Safety**:
   - Fails safely without modifying existing configurations unless `--force` is specified.
   - Provides `--dry-run` inspection mode.

## Relevant Files & Context Pointers

- Target Skill: `skills/setup_quality_check/SKILL.md`.
- Target Script: `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`.
- Target Test: `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py`.
- Canonical Template References:
  - `digital_wallet/bloc_digital_wallet` (Flutter).
  - `digital_wallet/android_digital_wallet` (Android).
  - `digital_wallet/ios_digital_wallet` (iOS).

## Design Rationale

The scaffolding tool acts as the primary onboarding entry point. When a developer or AI agent starts work on any project, running `setup_quality_check` inspects the project, provisions the `.agents/quality/` directory, and locks down the quality contracts within seconds.
- Written in Python 3.10+ standard library.
- Zero dependencies outside the repo.
- Atomic file generation with validation pre-flight.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/setup_quality_check/SKILL.md`: Skill definition and prompts.
  - `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`: Core detection and generation CLI.
  - `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py`: Multi-platform test suite.
- **Downstream Callers**: Developers and AI agents at session start.
- **Cross-Platform Bridges**: Generates JSON configurations across POSIX and macOS paths.
- **Target Test Coverage Threshold**: 100% path coverage for platform detection heuristics.

### BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] Auto-detect Flutter repository and scaffold manifests
  Given a mock directory containing pubspec.yaml with workspace configuration
  When scaffold_quality_manifest.py executes
  Then .agents/quality/check_quality.json declares provider flutter-core
  And .agents/quality/flutter-quality.json contains valid format, analyze, and test capabilities

Scenario: [Tier A - Unit] Idempotent protection against overwriting existing configuration
  Given a directory where check_quality.json already exists
  When scaffold_quality_manifest.py runs without --force
  Then the script exits with status 1 without mutating existing files

Scenario: [Tier A - Unit] Detect composite polyglot workspace
  Given a mock directory containing both Cargo.toml and settings.gradle.kts
  When scaffold_quality_manifest.py executes
  Then check_quality.json declares both rust-core and android-core providers
```

## Test & Verification Checklist

- [x] **RED**: Create test suite `test_scaffold_quality_manifest.py` testing detection of Rust, Flutter, Android, iOS, composite repos, and idempotence. Confirm tests fail.
- [x] **GREEN**: Implement `scaffold_quality_manifest.py` detection logic and manifest templates. Implement `skills/setup_quality_check/SKILL.md`.
- [x] **REFACTOR**: Ensure generated JSON files strictly validate against their respective schemas (`check-quality.schema.json`, `flutter-quality.schema.json`, etc.).
- [x] **Tier A Verification**: Run `python3 -B skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py` and confirm 100% pass.
- [x] **Tier B Verification**: Verify frontmatter (`name: setup_quality_check`, single-line description).

## Definition of Done (DoD)

- `skills/setup_quality_check/` created with `SKILL.md`, scripts, and unit tests.
- Unit tests pass with 100% success across all 4 platforms and composite workspaces.
- Generated configurations pass validator tests cleanly.
- `git status` shows clean, targeted additions.

## Dependencies & Blockers

- Blocked by: [Task 3](task_3_build_flutter_quality_provider.md), [Task 4](task_4_build_android_quality_provider.md), [Task 5](task_5_build_ios_quality_provider.md).
- Blocks: [Task 7](task_7_run_e2e_acceptance_and_release.md).

## References & Rollback

- Reference: [Scaffolding specification in HLD §4.2](mobile_quality_providers_and_contract_hardening.en.md#42-use-cases).
- Rollback: Remove `skills/setup_quality_check/` directory.
