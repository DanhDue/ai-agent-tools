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
- Every platform present in the repository is discovered and registered in `.agents/quality/check_quality.json`.
- Platform-specific quality manifests (`flutter-quality.json`, `android-quality.json`, `ios-quality.json`, `rust-quality.json`, `python-quality.json`) are populated with canonical, production-tested verification toolchains.
- Code generation agents and developers are constrained by automated quality gates from day one.

## Platform Detection Heuristics

The scaffolding engine inspects repository roots against the following marker files:

| Platform | Markers Detected | Provider ID | Target Manifest | Canonical Toolchain |
|---|---|---|---|---|
| **Flutter** | `pubspec.yaml`, `melos.yaml` | `flutter-core` | `flutter-quality.json` | `dartfmt.sh`, `fvm flutter analyze`, `check_module_boundaries.sh`, `check_license_header.sh`, `melos run test`, `testWithCoverage.sh` |
| **Android** | `build.gradle.kts`, `build.gradle`, `settings.gradle.kts`, `settings.gradle` | `android-core` | `android-quality.json` | `spotlessCheck`, `detekt`, `apiCheck`, `:konsist-test:test`, `testDebugUnitTest`, `jacocoTestReport`, `pkill -9 java` |
| **iOS** | `Project.swift`, `Tuist.swift`, `Package.swift` | `ios-core` | `ios-quality.json` | `swiftformat`, `swiftlint`, `ArchTests` (K1-K10), `check_module_boundaries.sh`, `swift test`, `check_coverage_thresholds.sh` |
| **Rust** | `Cargo.toml` | `rust-core` | `rust-quality.json` | `cargo fmt`, `cargo check`, `cargo clippy`, `cargo test`, `cargo llvm-cov`, `xtask check-architecture` |
| **Python** | `pyproject.toml`, `uv.lock`, `requirements.txt`, `setup.py`, `Pipfile` | `python-core` | `python-quality.json` | `ruff format`, `ruff check`, `mypy --strict`, `pytest`, `pytest-cov`, `lint-imports` |

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

Run an initial check to certify that the repository passes the baseline PR profile:

```bash
# Invoke quality_check skill
python3 skills/quality_check/resources/scripts/validate_quality_contract.py .agents/quality/check_quality.json
```

## CLI Reference

`scaffold_quality_manifest.py` accepts the following arguments:

- `--root <DIR>`: Path to the target repository root (default: current directory `.`).
- `--output-dir <DIR>`: Explicit output directory for generated manifests (default: `<root>/.agents/quality`).
- `--platform <LIST>`: Override automatic detection with comma-separated platforms (`flutter`, `android`, `ios`, `rust`, `python`).
- `--force`: Overwrite existing quality manifests (fails safely by default to prevent accidental overwrite).
- `--dry-run`: Display detected platforms and planned file list without writing to disk.

## Related Skills

- [Quality Check](../quality_check/SKILL.md)
- [Flutter Quality Check](../flutter-quality-check/SKILL.md)
- [Android Quality Check](../android-quality-check/SKILL.md)
- [iOS Quality Check](../ios-quality-check/SKILL.md)
- [Rust Quality Check](../rust-quality-check/SKILL.md)
- [Python Quality Check](../python-quality-check/SKILL.md)
