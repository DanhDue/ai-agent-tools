# Rust Tool Mapping

## Overview

This reference maps mobile quality assurance concepts (Android Native, Flutter, iOS Native) to their
corresponding Rust ecosystem equivalents and capabilities.

## Concept and Tool Mapping Table

| Quality Dimension | Android / Flutter Tool | Rust Ecosystem Equivalent | Capability Key |
|-------------------|------------------------|---------------------------|----------------|
| **Formatting** | Spotless / `dart format` | `cargo fmt --all -- --check` | `format` |
| **Compilation** | Gradle `compileKotlin` | `cargo check --all-targets` | `check` |
| **Linting & Code Smells** | Detekt & Android Lint / `melos analyze` | `cargo clippy --all-targets -- -D warnings` | `clippy` |
| **Unit & Integration Tests** | JUnit 5 & MockK / `bloc_test` | `cargo test --workspace` | `test` |
| **Code Coverage Gate** | Kover / `testWithCoverage.sh` | `cargo-llvm-cov` or `cargo-tarpaulin` | `coverage` |
| **Architecture Gate** | Konsist K1–K10 / `ArchTests` | `cargo run -p xtask -- check-architecture` | `architecture` |
| **Dependency & License Policy** | Dependency Analysis plugin | `cargo-deny check` | `deny` |
| **Vulnerability Audit** | OWASP Dependency-Check | `cargo-audit` | `audit` |
| **API / Semver Compatibility** | Binary Compatibility Validator (BCV) | `cargo-semver-checks` | `semver` |
| **Contract Acceptance** | Acceptance Harness / E2E flows | FFI & WASM test suites | `acceptance` |

## Status Interpretation

- **Tool Missing / Unexecutable**: Produces status `BLOCKED`. Absence of a declared tool cannot be treated as a pass.
- **Check Completed with Defects**: Produces status `FAIL`.
- **Check Completed Successfully**: Produces status `PASS` with structured evidence.
