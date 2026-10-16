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
  the failure (`exit 1; contains "ModuleNotFoundError"`). `GREEN` rows run the same command after
  implementation. `TIER-B` rows are tooling and governance checks. `TIER-C` rows run integration
  tests and name the report with `results <path>`.
- Replace the paths, package names and flags with the project's own. The rows show the shape, not
  the project's commands; use the commands the HLD's Integration Test Plan already names.
- The `results` path must be ignored by git (for example `build/` in `.gitignore`), because the
  report is rewritten on every run and is never committed.
- A report that records a test passing is what proves a scenario identifier. The test name, tag or
  description carries the identifier, and the framework writes it into the report.

## Python

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `uv run pytest tests/unit/test_taxonomy.py` | exit 1; contains "ModuleNotFoundError" | — |
| V2 | GREEN | `uv run pytest tests/unit/test_taxonomy.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `uv run ruff check src tests` | exit 0 | — |
| V4 | TIER-C | `uv run pytest tests/integration/test_taxonomy_bdd.py --junitxml=build/test-results/task_3.xml` | exit 0; results build/test-results/task_3.xml | — |

Report: `pytest --junitxml=<path>`.

## Android

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `./gradlew :feature:cart:testDebugUnitTest --tests '*CartViewModelTest'` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `./gradlew :feature:cart:testDebugUnitTest --tests '*CartViewModelTest'` | exit 0; contains "BUILD SUCCESSFUL" | — |
| V3 | TIER-B | `./gradlew spotlessCheck detekt :konsist-test:test apiCheck` | exit 0; contains "BUILD SUCCESSFUL" | — |
| V4 | TIER-C | `./gradlew :app:testDebugUnitTest --tests '*CartFlowTest'` | exit 0; results app/build/test-results/testDebugUnitTest | — |

Report: Gradle writes JUnit XML under `build/test-results/<task>/`. Name that directory after
`results`; every `.xml` file inside it is read.

## Web

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `npx vitest run src/cart/store.test.ts` | exit 1; contains "FAIL" | — |
| V2 | GREEN | `npx vitest run src/cart/store.test.ts` | exit 0; contains "passed" | — |
| V3 | TIER-B | `npx tsc --noEmit` | exit 0 | — |
| V4 | TIER-C | `PLAYWRIGHT_JUNIT_OUTPUT_FILE=build/test-results/e2e.xml npx playwright test tests/e2e/cart.spec.ts --reporter=junit` | exit 0; results build/test-results/e2e.xml | — |

Report: choose the reporter that writes JUnit XML.

- `node --test --test-reporter=junit --test-reporter-destination=<path>`
- `vitest --reporter=junit --outputFile=<path>`
- `playwright test --reporter=junit`, with the file set by the `PLAYWRIGHT_JUNIT_OUTPUT_FILE`
  environment variable or the `outputFile` option of the reporter in `playwright.config`.

## iOS

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `swift test --package-path Packages/Cart --filter CartReducerTests` | exit 1; contains "error" | — |
| V2 | GREEN | `swift test --package-path Packages/Cart --filter CartReducerTests` | exit 0; contains "passed" | — |
| V3 | TIER-B | `swiftlint lint --strict --config quality/.swiftlint.yml` | exit 0 | — |
| V4 | TIER-C | `swift test --package-path Packages/Cart --filter CartFlowTests --xunit-output build/test-results/cart.xml` | exit 0; results build/test-results/cart.xml | — |

Report: `swift test --xunit-output <path>`. XCTest results go to the named file. Swift Testing
writes its results to a second file beside it, so pass the directory after `results` when the
tests use Swift Testing. Converting an `.xcresult` bundle to JUnit is the project's job: add a
script to the repository and run it in the row's command; this kit does not read `.xcresult`.

## Rust

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `cargo test -p cart --lib totals` | exit non-zero; contains "error" | — |
| V2 | GREEN | `cargo test -p cart --lib totals` | exit 0; contains "test result: ok" | — |
| V3 | TIER-B | `cargo clippy --all-targets -- -D warnings` | exit 0 | — |
| V4 | TIER-C | `cargo nextest run -p cart --test '*' --profile ci` | exit 0; results target/nextest/ci/junit.xml | — |

Report: `cargo nextest` with a JUnit section in `.config/nextest.toml`:

```toml
[profile.ci.junit]
path = "junit.xml"
```

nextest writes the file to `target/nextest/<profile>/junit.xml`.

## Flutter

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `fvm flutter test test/cart/cart_bloc_test.dart` | exit 1; contains "Some tests failed" | — |
| V2 | GREEN | `fvm flutter test test/cart/cart_bloc_test.dart` | exit 0; contains "All tests passed" | — |
| V3 | TIER-B | `fvm flutter analyze` | exit 0; contains "No issues found" | — |
| V4 | TIER-C | `fvm flutter test integration_test/cart_flow_test.dart --file-reporter json:build/test-results/cart.json` | exit 0; results build/test-results/cart.json | — |

Report: `flutter test --file-reporter json:<path>`, which writes the Dart JSON test events that
`results` reads.
