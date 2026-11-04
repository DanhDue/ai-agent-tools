---
id: "task_02_playwright_zero_error_watchdog"
status: "todo"
priority: "high"
assignee: null
epic: "web-quality-check-and-integration-gate"
dueDate: null
created: "2026-11-04T22:52:00Z"
modified: "2026-11-04T22:52:00Z"
completedAt: null
labels: ["web", "playwright", "integration"]
order: "a2"
---

# Task 02: Playwright Zero-Console-Error Watchdog and Fixtures

Epic: [web_quality_check_and_integration_gate](../epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md)

## Requirement Analysis

Implement the Playwright Zero-Console-Error watchdog fixture and helper harness. The fixture intercepts all browser `console.error` and `pageerror` events, halting tests on uncaught runtime errors, while supporting a regex allowlist for benign vendor deprecation warnings. It also provides wire-level network mocking patterns using `page.route()` to consume canonical contract fixtures.

## Files

Allowed files:
- `skills/web-quality-check/resources/templates/playwright-zero-error.fixture.ts` (new)
- `skills/web-quality-check/resources/scripts/run_playwright_harness.py` (new)
- `tests/test_playwright_watchdog.py` (new)

Read-only context:
- `skills/web-quality-check/SKILL.md` (new in Task 01)
- `docs/refresh-session-quick-guide.en.md` (documentation guide)

## Design Rationale

Browser testing often produces silent failures where a missing DOM node or failed network request logs an uncaught exception to the DevTools console while the test runner completes without error. By enforcing Zero-Console-Error at the test fixture root, any unhandled JavaScript exception immediately fails the test suite. An explicit allowlist ensures known vendor warnings (e.g. deprecation notices from third-party analytics) do not cause false positives.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `playwright-zero-error.fixture.ts`, `run_playwright_harness.py`.
- **Downstream Callers**: Web test suites across `D3Nexus` (`apps/learning-web`) and `lyrics-sync` (`tests/e2e_full_screens_chrome_test.py`).
- **Cross-Platform Bridges**: Browser DevTools Protocol (CDP) via Playwright.
- **Target Test Coverage Threshold**: $\ge 85\%$ for watchdog harness.

### BDD SCENARIOS

Covers: [WQG-HP-03], [WQG-EC-02], [WQG-AR-02], [WQG-FR-01]

#### Scenario: [WQG-HP-03] [Tier C - Integration] Playwright headless execution with wiremock and Zero-Console-Error
Given an Astro web page with client-side interactive controllers
And Playwright configured with the Zero-Console-Error watchdog fixture
When the test simulates user navigation, button clicks, and network mocking via `page.route()`
Then the page renders without emitting any `console.error` or uncaught exceptions
And the test suite completes successfully.

#### Scenario: [WQG-EC-02] [Tier A - Unit] Benign console warnings filtered by allowlist
Given a web page emitting known third-party library deprecation warnings
And an allowlist regex configured in `.agents/quality/web-quality.json`
When the Playwright test executes
Then the Zero-Console-Error watchdog filters out matching allowlisted warnings
And does not falsely fail the test suite.

#### Scenario: [WQG-AR-02] [Tier C - Integration] Playwright webServer lifecycle management
Given Playwright configured with `webServer` command `npm run preview`
When Playwright starts the test runner
Then it awaits the server healthcheck port before dispatching browser tests
And cleanly tears down the webServer process upon completion.

#### Scenario: [WQG-FR-01] [Tier C - Integration] Immediate test failure on uncaught JavaScript console error
Given a web component with a runtime bug emitting `console.error("Uncaught TypeError")`
When Playwright executes the test suite
Then the Zero-Console-Error watchdog immediately halts and fails the test
And logs the full console message, stack trace, and target URL as evidence.

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest tests/test_playwright_watchdog.py::test_watchdog_filters` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest tests/test_playwright_watchdog.py::test_watchdog_filters` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check tests/test_playwright_watchdog.py skills/web-quality-check` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/run_playwright_harness.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest tests/test_playwright_watchdog.py -k "test_WQG_HP_03 or test_WQG_EC_02 or test_WQG_AR_02 or test_WQG_FR_01" --junitxml=build/test-results/task_02.xml` | exit 0; results build/test-results/task_02.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Target browser for Tier C runs: Chromium headless.
- Console listener syntax: `page.on('console', msg => ...)` and `page.on('pageerror', err => ...)`.
- Wire mocking pattern: `await page.route('**/api/**', route => route.fulfill({ json: fixture }))`.
- Allowlist pattern: Array of regex strings in manifest config under `console_error_allowlist`.

## Definition of Done

- `playwright-zero-error.fixture.ts` template provides reusable test extension. (V2)
- Zero-Console-Error watchdog passes ruff and mypy. (V3, V4)
- Scenarios [WQG-HP-03], [WQG-EC-02], [WQG-AR-02], [WQG-FR-01] fully tested and passing. (V5)
- Clean git status with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by: [Task 01](task_01_web_quality_check_skill_and_contract.md).

## References & Rollback

- Reference: [Playwright Network Mocking Guide](https://playwright.dev/docs/mock).
- Rollback: Revert `playwright-zero-error.fixture.ts` and test additions.
