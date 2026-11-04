---
id: "task_02_playwright_zero_error_watchdog"
status: "done"
priority: "high"
assignee: null
epic: "web-quality-check-and-integration-gate"
dueDate: null
created: "2026-11-04T22:52:00Z"
modified: "2026-11-04T21:04:14Z"
completedAt: "2026-11-04T21:04:14Z"
labels: ["web", "playwright", "integration"]
order: "a2"
---

# Task 02: Playwright Zero-Console-And-Layout-Defect Watchdog and Fixtures

Epic: [web_quality_check_and_integration_gate](../epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md)

## Requirement Analysis

Implement the Playwright Zero-Console-And-Layout-Defect watchdog fixture and helper harness. The fixture intercepts all browser `console.error` and `pageerror` events, halting tests on uncaught runtime errors, while supporting a regex allowlist for benign vendor deprecation warnings. To close the Visual Companion to Runtime CSS/Layout Gap, the fixture enforces three mandatory runtime checks:
1. **Static Asset Network Trap**: Listen to `page.on('response')` and immediately FAIL the test if any stylesheet (`.css`), script (`.js`), or font returns HTTP status `>= 400`.
2. **Computed Style & Geometry Assertion Helper (`assertVisualIntegrity`)**: Verify that structural UI containers (cards, drawers, badges, progress bars) ported from Visual Companion mockups have real computed styles applied (`window.getComputedStyle(el)` must not fall back to unstyled `backgroundColor: rgba(0, 0, 0, 0)` + `borderWidth: 0px` + `padding: 0px`, and `getBoundingClientRect()` must have `width > 0` and `height > 0`).
3. **DOM State Leak & Duplicate Text Guard**: Refine visibility inspection to avoid false positives on accessible clipped elements. Intentionally clipped accessibility elements (e.g. `.sr-only`, `.visually-hidden`, `clip: rect(0, 0, 0, 0)`, `clip-path: inset(50%)`, or dimensions `width <= 1 && height <= 1` with `overflow: hidden`) are recognized as hidden by design and ignored. Element visibility is evaluated using `el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })` and ancestor visibility inspection. Mutually exclusive state elements are checked via explicit selector groups (`exclusiveStateSelectors`, e.g. `[['[data-state="running"]', '[data-state="failed"]'], ['[data-state="running"]', '[data-state="completed"]']]`), failing if multiple selectors from any group are simultaneously visible. Detects unstyled hidden span leakage causing consecutive duplicate text in headings/labels.
The harness also provides wire-level network mocking patterns using `page.route()` to consume canonical contract fixtures.

## Files

Allowed files:
- `skills/web-quality-check/resources/templates/playwright-zero-error.fixture.ts` (new)
- `skills/web-quality-check/resources/templates/playwright_zero_error.py` (new)
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

Covers: [WQG-HP-03], [WQG-EC-02], [WQG-EC-03], [WQG-AR-02], [WQG-FR-01], [WQG-FR-03]

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

#### Scenario: [WQG-EC-03] [Tier C - Integration] Mutually exclusive DOM state leak and duplicate text detection
Given a UI component with conditional state badges and tooltip accessibility spans
When Playwright executes with the Zero-Console-And-Layout-Defect Watchdog
Then it asserts that mutually exclusive elements (e.g. running spinner vs terminal failure badge, visible title vs hidden tooltip) are not simultaneously visible
And detects consecutive duplicate substring rendering inside card titles/subtitles caused by unstyled hidden spans
And fails Gate 4 if unstyled hidden spans leak into visible layout.

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

#### Scenario: [WQG-FR-03] [Tier C - Integration] Immediate failure on 404 static stylesheet or unstyled computed geometry
Given an Astro or web page where a critical `.css` stylesheet returns HTTP status >= 400
Or a primary structural UI container renders with unstyled default computed styles (transparent background, zero border/padding, or zero dimensions)
When the Playwright test suite executes with `assertVisualIntegrity`
Then the Static Asset Network Trap and geometry watchdog immediately fail the test
And log the missing asset URL and unstyled element selectors as evidence.

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest tests/test_playwright_watchdog.py::test_watchdog_filters` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest tests/test_playwright_watchdog.py::test_watchdog_filters` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check tests/test_playwright_watchdog.py skills/web-quality-check` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/run_playwright_harness.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest tests/test_playwright_watchdog.py -k "test_WQG_HP_03 or test_WQG_EC_02 or test_WQG_EC_03 or test_WQG_AR_02 or test_WQG_FR_01 or test_WQG_FR_03" --junitxml=build/test-results/task_02.xml` | exit 0; results build/test-results/task_02.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Target browser for Tier C runs: Chromium headless.
- Console listener syntax: `page.on('console', msg => ...)` and `page.on('pageerror', err => ...)`.
- Static Asset Network Trap: `page.on('response', resp => { if (['stylesheet', 'script', 'font'].includes(resp.request().resourceType()) && resp.status() >= 400) throw new Error(...); })`.
- `assertVisualIntegrity(locator, options)`: evaluates `window.getComputedStyle(el)` verifying background/border/padding styling and `getBoundingClientRect()` with `width > 0 && height > 0`.
- DOM State Leak guard: evaluates `el.checkVisibility()` and ancestor visibility; ignores intentionally clipped accessibility elements (`.sr-only`, `clip: rect(0,0,0,0)`, `clip-path`, `1px` bounding box); checks mutually exclusive state locators via `exclusiveStateSelectors`; flags consecutive duplicate text chunks.
- Wire mocking pattern: `await page.route('**/api/**', route => route.fulfill({ json: fixture }))`.
- Allowlist pattern: Array of regex strings in manifest config under `console_error_allowlist`.
- Python companion helper: `skills/web-quality-check/resources/templates/playwright_zero_error.py` provides Python Playwright equivalents (`attach_zero_error_watchdog(page)` and `assert_visual_integrity(page, selector, ...)`) for Python-based test runners (such as `lyrics-sync`).
- Positive accessibility fixtures: test suite includes positive fixtures verifying standard `.sr-only` accessibility patterns to prevent false positives.

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
