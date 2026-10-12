# Python Tool Mapping

## Overview

This reference maps mobile quality assurance concepts (Android Native, Flutter, iOS Native) to their
corresponding Python ecosystem equivalents and capabilities.

## Concept and Tool Mapping Table

| Quality Dimension | Android / Flutter Tool | Python Ecosystem Equivalent | Capability Key |
|-------------------|------------------------|-----------------------------|----------------|
| **Formatting** | Spotless / `dart format` | `ruff format --check .` | `format` |
| **Linting & Code Smells** | Detekt & Android Lint / `melos analyze` | `ruff check .` | `lint` |
| **Type Checking** | Kotlin compiler / `dart analyze` | `mypy --strict src` | `type_check` |
| **Unit & Component Tests** | JUnit 5 & MockK / `bloc_test` | `pytest` | `test` |
| **Code Coverage Gate** | Kover / `testWithCoverage.sh` | `pytest --cov=src --cov-report=json` | `coverage` |
| **Architecture Gate** | Konsist K1–K10 / `ArchTests` | `lint-imports` (`import-linter`) | `architecture` / `boundaries` |
| **Model Schema Verification** | Schema Validator / Serialization Tests | `python -m <pkg>.model --check-schema` | `schema` |
| **Security & Vulnerability Audit** | Dependency-Check / Mobile Audit | `bandit` / `pip-audit` | `security` |
| **Contract Acceptance / E2E** | Acceptance Harness / E2E flows | End-to-end acceptance script (`run_e2e_acceptance.sh`) | `acceptance` |
| **Documentation Integrity** | Dokka / `dartdoc` | `mkdocs build --strict` / `sphinx-build` | `docs` |

## Status Interpretation

- **Tool Missing / Unexecutable**: Produces status `BLOCKED`. Absence of a declared tool cannot be treated as a pass.
- **Check Completed with Defects**: Produces status `FAIL`.
- **Check Completed Successfully**: Produces status `PASS` with structured evidence.
