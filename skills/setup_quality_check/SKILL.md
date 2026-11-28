---
name: setup_quality_check
description: Inspects repository structure, auto-detects platforms (Flutter, Android, iOS, Rust, or Polyglot), and scaffolds standardized quality provider configurations adhering to canonical templates.
---

# Setup Quality Check

Automated onboarding skill that bootstraps the d3nexus quality governance system for both Greenfield
(new projects) and Brownfield (legacy repositories before active maintenance or AI agent code generation).

## Overview

The quality governance model requires deterministic, SHA-bound quality verification before any feature branch
or PR is merged. Setting up quality checking ensures that:
- Every platform present in the repository is discovered and registered in `.agents/quality/check_quality.json` across all 4 profiles (`pr`, `epic`, `scheduled`, `release`) with stack-appropriate `pool_mounts` (`symlink` caches and `cow_copy` local/untracked trees).
- Platform-specific quality manifests (`flutter-quality.json`, `android-quality.json`, `ios-quality.json`, `rust-quality.json`, `python-quality.json`, `web-quality.json`) are populated with canonical additive v1 toolchains, deduplicated profiles (`pr_diff_audit` + `pr_impact` in `pr` only; `workspace_audit` + `workspace_impact` in `epic`, `scheduled`, and `release`; offline-safe `npx --no-install` and `security_deps` isolation), unified capabilities (`anti_stub`, `security`, `security_deps`, `pr_diff_audit`, `workspace_audit`, `pr_impact`, `workspace_impact`, `license`), dual-floor coverage powered by `{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py` (with optional `package_floors` / `--package-floors` ratchets), and optional `task_tier_b`/`test_routing`/`triage_surfaces` hooks.
- A starter `.agents/quality/standards_catalog.json` (ISO 25010, ISO 27001/27002, OWASP, CWE) is created when absent and never overwritten (even with `--force`).
- Code generation agents and developers are constrained by automated quality gates from day one.

## Platform Detection Heuristics

The scaffolding engine inspects repository roots against the following marker files:

| Platform | Markers Detected | Provider ID | Target Manifest | Canonical Toolchain |
|---|---|---|---|---|
| **Flutter** | `pubspec.yaml`, `melos.yaml` | `flutter-core` | `flutter-quality.json` | `dartfmt.sh`, `fvm flutter analyze`, `check_module_boundaries.sh`, `check_license_header.sh`, `melos run test`, `check_diff_coverage.py` (LCOV) |
| **Android** | `build.gradle.kts`, `build.gradle`, `settings.gradle.kts`, `settings.gradle` | `android-core` | `android-quality.json` | `spotlessCheck`, `detekt`, `apiCheck`, `:konsist-test:test`, `testDebugUnitTest`, `jacocoTestReport`, `check_diff_coverage.py` (JaCoCo XML) |
| **iOS** | `Project.swift`, `Tuist.swift`, `Package.swift` | `ios-core` | `ios-quality.json` | `swiftformat`, `swiftlint`, `ArchTests` (K1-K10), `check_module_boundaries.sh`, `swift test`, `check_diff_coverage.py` (LCOV) |
| **Rust** | `Cargo.toml` | `rust-core` | `rust-quality.json` | `cargo fmt`, `cargo check`, `cargo clippy`, `cargo test`, `cargo llvm-cov`, `check_diff_coverage.py`, `xtask check-architecture` |
| **Python** | `pyproject.toml`, `uv.lock`, `requirements.txt`, `setup.py`, `Pipfile` | `python-core` | `python-quality.json` | `ruff format`, `ruff check`, `mypy --strict`, `pytest`, `check_diff_coverage.py` (Cobertura XML), `lint-imports` |
| **Web** | `astro.config.*`, `playwright.config.*`, `package.json`, `src/**/web/**` | `web-quality` | `web-quality.json` | `check_vanilla_js.py`, `audit_ui_state_and_styles.py`, `playwright test` (with watchdog fixture), `check_diff_coverage.py` (LCOV) |

In composite repositories (e.g. Flutter mobile host with Rust core, or native Android/iOS bridging modules), all detected platforms are registered in `.agents/quality/check_quality.json`.

## Operational Workflow

### Step 1: Dry-Run Inspection

Inspect what platforms the tool detects and what files will be created:

```bash
python3 skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py --dry-run
```

### Step 2: Scaffold Configuration Files

Execute scaffolding to generate the `.agents/quality/` directory:

```bash
python3 skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py
```

If configurations already exist and you want to reset them to canonical defaults:

```bash
python3 skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py --force
```

### Step 3: Run Baseline Quality Verification

Run an initial check to certify that the repository passes the baseline PR profile (`validate_quality_contract.py registry` defaults to JSON and supports `--compact` for a 1-line `PASS:` summary; stack validators default to compact 1-line `PASS:` with `--verbose` / `--json`):

```bash
# Validate registry (JSON default; pass --compact for 1-line PASS)
python3 skills/quality_check/resources/scripts/validate_quality_contract.py registry .agents/quality/check_quality.json --profile pr --compact
```

## Coverage Report Prerequisite

Scaffolded `test` (`test_unit` on Web) commands are intentionally minimal defaults and do not emit coverage artifacts on their own. Both `diff_coverage` (in the `pr` profile) and `coverage` (in `epic`, `scheduled`, and `release`) invoke `check_diff_coverage.py`, which fails closed with exit code `2` (`BLOCKED`) on a clean checkout when the expected report file is missing.

Before running `pr`, `epic`, `scheduled`, or `release`, update the project's `test` / `test_unit` capability (or add a prior coverage-producing step before `diff_coverage` / `coverage`) so the stack's expected report is written first:

| Platform | Expected Report Path | Format | Example Coverage Producer |
|---|---|---|---|
| **Flutter** | `coverage_report/lcov.info` | `lcov` | Emit `--coverage` in `melos run test` and merge LCOV into `coverage_report/lcov.info` |
| **Android** | `build/reports/jacoco/jacocoTestReport/jacocoTestReport.xml` | `jacoco` | `./gradlew testDebugUnitTest jacocoTestReport` |
| **iOS** | `build/coverage/lcov.info` | `lcov` | `swift test --enable-code-coverage` + `llvm-cov export --format=lcov` |
| **Rust** | `target/llvm-cov/lcov.info` | `lcov` | `cargo llvm-cov --workspace --lcov --output-path target/llvm-cov/lcov.info` |
| **Python** | `coverage.xml` | `cobertura` | Add `--cov --cov-report=xml:coverage.xml` to `pytest` |
| **Web** | `coverage/lcov.info` | `lcov` | Configure `npm run test:unit` with `--coverage` and an LCOV reporter |

## CLI Reference

`scaffold_quality_manifest.py` accepts the following arguments:

- `--root <DIR>`: Path to the target repository root (default: current directory `.`).
- `--output-dir <DIR>`: Explicit output directory for generated manifests (default: `<root>/.agents/quality`).
- `--platform <LIST>`: Override automatic detection with comma-separated platforms (`flutter`, `android`, `ios`, `rust`, `python`, `web`).
- `--force`: Overwrite existing registry/provider manifests (never overwrites `.agents/quality/standards_catalog.json`).
- `--dry-run`: Display detected platforms and planned file list without writing to disk.

## Related Skills

- [Quality Check](../quality_check/SKILL.md)
- [Portable Diff-Coverage Engine](../quality_check/resources/scripts/check_diff_coverage.py)
- [Flutter Quality Check](../flutter-quality-check/SKILL.md)
- [Android Quality Check](../android-quality-check/SKILL.md)
- [iOS Quality Check](../ios-quality-check/SKILL.md)
- [Rust Quality Check](../rust-quality-check/SKILL.md)
- [Python Quality Check](../python-quality-check/SKILL.md)
- [Web Quality Check](../web-quality-check/SKILL.md)
