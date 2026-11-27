# Verification Rows by Platform

Example rows for a task's `## Verification` table, one set per platform, and the command that
produces the test report a `TIER-C` row names after `results`. The table grammar is in
[`SKILL.md`](../SKILL.md); here are only the platform commands.

## Table of Contents

- [How to Read the Examples](#how-to-read-the-examples)
- [Python](#python)
- [Android](#android)
- [Web](#web)
- [iOS](#ios)
- [Rust](#rust)
- [Flutter](#flutter)

## How to Read the Examples

- `RED` rows run before implementation and must fail for the right reason, so their Expect names
  the failure (`exit 1; contains "ModuleNotFoundError"`). `GREEN` rows run the new/modified test
  file(s) after implementation. `REGRESSION` rows run the existing test suite of the entire touched
  module plus all *Downstream Callers* listed in `## Impact Analysis & Blast Radius` (never let a
  `Verification` table run only a newly created unit test file). `TIER-B` rows run static lint,
  format check, and strict type-check across **all** `Allowed files` (both production and test
  files), plus architectural boundary checks (`lint-imports` or contract check) when cross-module
  imports or contracts are touched. `TIER-C` rows run integration tests and name the report with
  `results <path>`.
- Replace the paths, package names and flags with the project's own. The rows show the shape, not
  the project's commands; use the commands the HLD's Integration Test Plan already names.
- The `results` path must be ignored by git (for example `build/` in `.gitignore`), because the
  report is rewritten on every run and is never committed.
- A report that records a test passing is what proves a scenario identifier. The test name, tag or
  description carries the identifier, and the framework writes it into the report.

## Python

### Task 1..N-1 (Level 1 — Task-Scoped to `Allowed files` + Module/Downstream `REGRESSION`)

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `uv run pytest -q --tb=short --maxfail=3 tests/unit/test_taxonomy_guard.py::test_parse_node` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `uv run pytest -q --tb=short --maxfail=3 tests/unit/test_taxonomy_guard.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `uv run pytest -q --tb=short --maxfail=3 tests/unit/test_taxonomy.py tests/unit/test_downstream_caller.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `uv run ruff check src/pkg/taxonomy.py tests/unit/test_taxonomy_guard.py tests/unit/test_taxonomy.py && uv run ruff format --check src/pkg/taxonomy.py tests/unit/test_taxonomy_guard.py tests/unit/test_taxonomy.py && uv run mypy --strict src/pkg/taxonomy.py tests/unit/test_taxonomy_guard.py tests/unit/test_taxonomy.py && uv run lint-imports` | exit 0 | — |
| V5 | TIER-C | `uv run pytest -q --tb=short --maxfail=3 tests/integration/test_taxonomy_bdd.py --junitxml=build/test-results/task_1.xml` | exit 0; results build/test-results/task_1.xml | — |

### Task N Final Integration & Governance Task (Level 2 — Blast-Radius Scoped + Fast Mechanical Gates)

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `uv run pytest -q --tb=short --maxfail=3 tests/integration/test_taxonomy_flow.py::test_full_pipeline` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `uv run pytest -q --tb=short --maxfail=3 tests/integration/test_taxonomy_flow.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `uv run pytest -q --tb=short --maxfail=3 tests/unit/test_taxonomy.py tests/unit/test_downstream_caller.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `uv run ruff check src/pkg/taxonomy.py tests/integration/test_taxonomy_flow.py && uv run ruff format --check src/pkg/taxonomy.py tests/integration/test_taxonomy_flow.py && uv run mypy --strict src/pkg/taxonomy.py tests/integration/test_taxonomy_flow.py && python3 scripts/check_anti_stub.py && python3 scripts/verify_importlinter_coverage.py && uv run lint-imports && python3 scripts/verify_bdd_coverage.py --verify-epic-parity --verify-contract-watermark && python3 scripts/pre_review_self_probe.py` | exit 0 | — |
| V5 | TIER-C | `uv run pytest -q --tb=short --maxfail=3 tests/integration/test_taxonomy_flow.py --junitxml=build/test-results/task_n.xml` | exit 0; results build/test-results/task_n.xml | — |

Report: `pytest --junitxml=<path>`.

> **Chained vs. split `TIER-B` rows:** `check_task_contract.py` splits unconditional sequential shell chains (`&&` and `;`) when matching registered `lint` and `type_check` capabilities (tails after `||` or `|` are excluded). Both a single chained `V4 | TIER-B` row and separate `V4`/`V5` `TIER-B` rows are valid.

## Android

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `./gradlew :feature:cart:testDebugUnitTest --tests '*CartDiscountGuardTest'` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `./gradlew :feature:cart:testDebugUnitTest --tests '*CartDiscountGuardTest'` | exit 0; contains "BUILD SUCCESSFUL" | — |
| V3 | REGRESSION | `./gradlew :feature:cart:testDebugUnitTest --tests '*CartViewModelTest' :feature:checkout:testDebugUnitTest` | exit 0; contains "BUILD SUCCESSFUL" | — |
| V4 | TIER-B | `./gradlew spotlessCheck detekt :konsist-test:test apiCheck` | exit 0; contains "BUILD SUCCESSFUL" | — |
| V5 | TIER-C | `./gradlew :app:testDebugUnitTest --tests '*CartFlowTest'` | exit 0; results app/build/test-results/testDebugUnitTest | — |

Report: Gradle writes JUnit XML under `build/test-results/<task>/`. Name that directory after
`results`; every `.xml` file inside it is read.

## Web

When `.agents/quality/*-quality.json` exists, copy its canonical `type_check` and `lint` commands verbatim instead of inventing ad-hoc `npx` calls. Never use bare `npx <bin>` (it can hang on interactive install prompts in headless subagents) — always pass `npx --no-install <bin>` (or explicit `npx --yes --package <pkg> <bin>` when a non-interactive install is intentionally required).

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `npx --no-install vitest run src/cart/discount-guard.test.ts` | exit 1; contains "FAIL" | — |
| V2 | GREEN | `npx --no-install vitest run src/cart/discount-guard.test.ts` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `npx --no-install vitest run src/cart/store.test.ts src/checkout/summary.test.ts` | exit 0; contains "passed" | — |
| V4 | TIER-B | `npx --no-install eslint src/cart/store.ts src/cart/discount-guard.test.ts src/cart/store.test.ts && npx --no-install tsc --noEmit` | exit 0 | — |
| V5 | TIER-C | `PLAYWRIGHT_JUNIT_OUTPUT_FILE=build/test-results/e2e.xml npx --no-install playwright test tests/e2e/cart.spec.ts --reporter=junit` | exit 0; results build/test-results/e2e.xml | — |

Report: choose the reporter that writes JUnit XML.

- `node --test --test-reporter=junit --test-reporter-destination=<path>`
- `vitest --reporter=junit --outputFile=<path>`
- `playwright test --reporter=junit`, with the file set by the `PLAYWRIGHT_JUNIT_OUTPUT_FILE`
  environment variable or the `outputFile` option of the reporter in `playwright.config`.

## iOS

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `swift test --package-path Packages/Cart --filter CartDiscountGuardTests` | exit 1; contains "error" | — |
| V2 | GREEN | `swift test --package-path Packages/Cart --filter CartDiscountGuardTests` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `swift test --package-path Packages/Cart --filter CartReducerTests && swift test --package-path Packages/Checkout --filter CheckoutSummaryTests` | exit 0; contains "passed" | — |
| V4 | TIER-B | `swiftlint lint --strict --config quality/.swiftlint.yml Packages/Cart/Sources/CartReducer.swift Packages/Cart/Tests/CartDiscountGuardTests.swift Packages/Cart/Tests/CartReducerTests.swift` | exit 0 | — |
| V5 | TIER-C | `swift test --package-path Packages/Cart --filter CartFlowTests --xunit-output build/test-results/cart.xml` | exit 0; results build/test-results/cart.xml | — |

Report: `swift test --xunit-output <path>`. XCTest results go to the named file. Swift Testing
writes its results to a second file beside it, so pass the directory after `results` when the
tests use Swift Testing. Converting an `.xcresult` bundle to JUnit is the project's job: add a
script to the repository and run it in the row's command; this kit does not read `.xcresult`.

## Rust

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `cargo test -p cart --lib discount_guard` | exit non-zero; contains "error" | — |
| V2 | GREEN | `cargo test -p cart --lib discount_guard` | exit 0; contains "test result: ok" | — |
| V3 | REGRESSION | `cargo test -p cart --lib totals && cargo test -p checkout --lib cart_adapter` | exit 0; contains "test result: ok" | — |
| V4 | TIER-B | `cargo fmt --check && cargo clippy --all-targets -- -D warnings` | exit 0 | — |
| V5 | TIER-C | `cargo nextest run -p cart --test '*' --profile ci` | exit 0; results target/nextest/ci/junit.xml | — |

Report: `cargo nextest` with a JUnit section in `.config/nextest.toml`:

```toml
[profile.ci.junit]
path = "junit.xml"
```

nextest writes the file to `target/nextest/<profile>/junit.xml`.

## Flutter

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `fvm flutter test test/cart/cart_discount_guard_test.dart` | exit 1; contains "Some tests failed" | — |
| V2 | GREEN | `fvm flutter test test/cart/cart_discount_guard_test.dart` | exit 0; contains "All tests passed" | — |
| V3 | REGRESSION | `fvm flutter test test/cart/cart_bloc_test.dart test/checkout/checkout_cubit_test.dart` | exit 0; contains "All tests passed" | — |
| V4 | TIER-B | `fvm dart analyze lib/cart/cart_bloc.dart test/cart/cart_discount_guard_test.dart test/cart/cart_bloc_test.dart` | exit 0; contains "No issues found" | — |
| V5 | TIER-C | `fvm flutter test integration_test/cart_flow_test.dart --file-reporter json:build/test-results/cart.json` | exit 0; results build/test-results/cart.json | — |

Report: `flutter test --file-reporter json:<path>`, which writes the Dart JSON test events that
`results` reads.
