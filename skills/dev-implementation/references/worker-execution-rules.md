# Worker Execution Rules

Read when: you are a Role 2.3 `task-implementer`, or you dispatch one, and need the test-health rules, the Tri-Persona model or the anti-rationalization table.

## Mechanical Verification vs. LLM Review & Tiered Execution

- **Mandatory Per-Task Mechanical Verification (Role 2.3 Programmer)**: For **every task**, the Programmer must execute and pass the entire `Verification` table (`RED -> GREEN -> REGRESSION -> TIER-B -> TIER-C`):
  1. `RED`: Exact node ID failing for the expected reason before production code changes.
  2. `GREEN`: New/updated unit tests for the task pass.
  3. `REGRESSION`: Full test suite of the touched module and all *Downstream Callers* from `## Impact Analysis & Blast Radius` pass (never run only the newly created unit test file).
  4. `TIER-B`: Lint/format (`ruff check`, `ruff format --check` or stack equivalent) and strict type-check (`mypy --strict` or stack equivalent) across **all** `Allowed files` (both production and new/modified test files), plus `lint-imports` / contract checks when touching cross-module imports or contracts.
  5. `TIER-C`: Integration / BDD scenario tests writing fresh report artifacts (`results <path>`).
  6. **Definition of Done Lock**: After `run_task_checks.py verify` passes, tick every `- [ ]` checkbox in `## Definition of Done` to `- [x]` and append a brief mechanical result note after the `(Vn)` reference (e.g. `- [x] Criterion (V2, V3) — exit 0, 42 passed`). Updating frontmatter to `status: "done"` (or setting `completedAt`) is strictly forbidden while any `- [ ]` remains.
- **Selective LLM / Cross-Model Review**: LLM review (`task-reviewer` Role 2.1) is skipped on small, purely mechanical tasks to avoid bottlenecks, and runs only at semantic/architectural boundaries or on high-risk tasks (`review_tier: "full"`, `security`/`architecture`/`concurrency`/`contract` labels, or `> 2` non-test modules changed), followed by epic-wide `/cross-model-review` after local Gate 4 passes.

## Test Assertion Health, Anti-Bloat & Tiered Execution

Never assert only inside `if path.exists()`; always assert `found > 0`. Enforce:
- **Mandatory Parametrization**: Never copy-paste `def test_*` functions across input variations; consolidate into `@pytest.mark.parametrize` (or table tests).
- **No Trivial Boilerplate Tests**: Ban tests asserting only Python language features, Pydantic defaults, or trivial getters/setters; verify distinct Spec/HLD contracts.
- **Fixture Scope Discipline**: Read-only fixtures (JSON snapshots, AST trees, mock servers, headless browsers) MUST use `scope="module"` or `scope="session"`, never `scope="function"`.
- **Tier 1 (Task & Fix Rounds)**: Static checks (`TIER-B`) + stack-mapped scoped tests from the 6-stack table below; never run `Tier C2` E2E or repo-wide suites in a fix round. **Tier 2 (Pre-Gate)**: Scoped non-E2E regression suite (e.g., Python `uv run pytest --ignore=tests/e2e -m "not slow and not acceptance and not live_llm" -n auto --dist loadscope --timeout=30 -q --tb=short`, or the project's non-E2E workspace unit + Tier C1 suite). **Tier 3 (Final Gate Convergence Only)**: Tier 2 + `Needs:`-gated Tier C2 suites (`tests/e2e`, device/simulator harnesses) + `audit_epic.py` / `@quality_check` (including portable dual-floor diff-coverage via `{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py`).

## 6-Stack Platform-Mapped Commands & Tier C1 vs. Tier C2 Discipline

All 6 stacks resolve their static gates, slot mounts, suffix-scoped triage surfaces, and Tier C rules through [`_stack_lifecycle_registry.py`](../resources/scripts/_stack_lifecycle_registry.py) (`TierBContractAdapter`, `PoolWorkspaceStrategy`, `TriageSurfaceRegistry`, `TierCTaxonomy`). Prefer commands from `.agents/quality/<stack>-quality.json` when present.

| Stack | Tier 1 Scoped Task / Review-Fixer Tests | Tier B Static Gate (All `Allowed files`) | Tier C1 Mandatory Host/VM Integration (`< 5s`) | Tier C2 Heavy E2E (`# tier: C2`, `Needs:`-Gated) |
| :--- | :--- | :--- | :--- | :--- |
| **Python** | `uv run pytest <changed_test_files> -n auto --timeout=30 -q --tb=short` | `ruff check`, `ruff format --check`, `mypy --strict` (+ `lint-imports` on boundary edits) | `python3 -m pytest -q --tb=short --maxfail=3 tests/integration/ --junitxml=<path>` | `python3 -m pytest -q --tb=short --maxfail=3 tests/e2e/ --junitxml=<path> # tier: C2` (`Needs: DOCKER_LIVE`) |
| **Flutter** | `fvm flutter test <changed_test_files>` | `fvm dart format --output=none --set-exit-if-changed <allowed_dart_files> && fvm dart analyze` (+ boundary check on `domain/` or `pubspec.yaml`) | `fvm flutter test test/integration/<feature>_integration_test.dart --file-reporter json:<path>` | `fvm flutter test integration_test/<flow>_test.dart --file-reporter json:<path> # tier: C2` (`Needs: FLUTTER_DEVICE`) |
| **Rust** | `cargo test -p <crate> <filter>` | `cargo fmt --check && cargo clippy --all-targets -- -D warnings` (+ `xtask check-architecture` on `Cargo.toml` / domain edits) | `cargo nextest run -p <crate> --test '*' --profile ci` | `cargo nextest run --test e2e --profile ci # tier: C2` (`Needs: RUST_LIVE_ENV`) |
| **Web** | `npx --no-install vitest run <changed_test_files>` | `npx --no-install eslint <allowed_files> && npx --no-install tsc --noEmit` | `npx --no-install vitest run tests/integration/<feature>.test.ts --reporter=junit --outputFile=<path>` | `env PLAYWRIGHT_JUNIT_OUTPUT_FILE=<path> npx --no-install playwright test tests/e2e/<spec>.spec.ts --reporter=junit # tier: C2` (`Needs: PLAYWRIGHT_BROWSER`) |
| **Android** | `./gradlew :<module>:testDebugUnitTest --tests '*<TestClass>'` | `./gradlew spotlessCheck detekt` (+ `:konsist-test:test apiCheck` on domain/Gradle edits) | `./gradlew :app:testDebugUnitTest --tests '*FlowTest'` (JVM / Robolectric) | `./gradlew :app:connectedDebugAndroidTest # tier: C2` (`Needs: ANDROID_EMULATOR`) |
| **iOS** | `swift test --package-path <Pkg> --filter <TestSuite>` | `swiftformat --lint <allowed_files> && swiftlint lint --strict <allowed_files>` (+ `ArchTests` on `Package.swift` / domain edits) | `swift test --package-path <Pkg> --filter <Feature>FlowTests --xunit-output <path>` | `xcodebuild test -scheme <Scheme> -destination <Dest> # tier: C2` (`Needs: IOS_SIMULATOR`) |

- **Tier C1 (Mandatory per task)**: Runs deterministically in `< 5s` on the host/VM with real DI, wire fixtures, and in-memory persistence; never requires a device, simulator, or live browser.
- **Tier C2 (`# tier: C2` + `Needs:`)**: Any `TIER-C` command that launches a simulator, emulator, physical device, or Playwright browser MUST end with `# tier: C2` and declare its `Needs:` variable in the table and HLD `## Verification Environment` (enforced by `TierCTaxonomy`).
- **Compact CLI Output**: `check_task_contract.py`, `check_diff_coverage.py`, and stack quality validators emit a single-line `PASS` summary by default (`--verbose` / `--json` opt-in for full diagnostics).

## Tri-Persona Subagent Execution Model

Operate across the 3-Tier Testing Standard:
1. **Expert QA (Red Team)**: Authors adversarial BDD scenarios (`HP`, `EC`, `ST`, `AR`, `FR`) split cleanly between `[Tier A - Unit]` and `[Tier C - Integration]`.
2. **Principal Engineer (TDD Master — Tier A)**: Executes RED failing test -> minimal GREEN code -> REFACTOR/lint/strict types in task files only.
3. **System Integration & E2E Engineer (Tier C)**: Authors integration/browser suites (`integration_test/`, `*FlowTest.kt`, `App/Tests`, `tests/e2e/`, `tests/integration/`) exercising real DI, navigation, and persistence.

## Anti-Rationalization and Doubt-Driven Verification

Reject rationalizations that cut testing corners:
- **"Node test is sufficient for web UI"**: REJECTED. Node tests prove only pure data logic. Web defects occur in DOM queries and CSS rendering. Tier C requires headless Playwright with Zero-Console-Error watchdog.
- **"Mock data in stub is enough"**: REJECTED. Method stubs bypass JSON deserialization and network interceptors. Wire fixtures from `shared-contracts/` are mandatory.
- **"Red console errors are harmless warnings"**: REJECTED. Zero-Console-Error rule fails Gate 4 on any browser console error.
- **"Cannot launch simulator, unit test instead"**: REJECTED. Mobile Tier C requires Subcutaneous testing with real DI and in-memory persistence.
- **"HTML ported from mockup, selectors match"**: REJECTED. Tier C2 UI tests MUST assert `getComputedStyle` and `getBoundingClientRect` properties against the Visual Companion design.

**Doubt-Driven Verification Protocol**:
Before claiming done on any task: `CLAIM` Tier C coverage -> `EXTRACT` test reports -> `DOUBT` mock isolation -> `RECONCILE` real headless/subcutaneous tests.
