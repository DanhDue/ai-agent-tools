# BDD Test Scenarios: Web Quality Check Provider and Integration Quality Gate

## Table of Contents

- [Dimension 1: Happy Paths](#dimension-1-happy-paths)
- [Dimension 2: Edge Cases and Boundaries](#dimension-2-edge-cases-and-boundaries)
- [Dimension 3: State Transitions](#dimension-3-state-transitions)
- [Dimension 4: Async and Concurrency](#dimension-4-async-and-concurrency)
- [Dimension 5: Failures and Resilience](#dimension-5-failures-and-resilience)

## Dimension 1: Happy Paths

```gherkin
Scenario: [WQG-HP-01] [Tier C - Integration] Web quality provider certification on Astro TypeScript repository
  Given a repository containing an Astro project with .agents/quality/web-quality.json
  When Gate 4 invokes d3nexus:web-quality-check with profile epic
  Then the provider executes type_check, lint, and test_e2e via Playwright headless
  And produces a validated Provider Result Document with status PASS bound to the commit SHA

Scenario: [WQG-HP-02] [Tier C - Integration] Vanilla JavaScript type-checking via JSDoc configuration
  Given a repository containing Vanilla JavaScript files in preview/static/
  And a jsconfig.json configured with "checkJs": true
  When web-quality-check executes the type_check capability
  Then the TypeScript compiler validates all JavaScript files without emitting errors
  And passes without requiring any .ts file renaming

Scenario: [WQG-HP-03] [Tier C - Integration] Playwright headless execution with wiremock and Zero-Console-Error
  Given an Astro web page with client-side interactive controllers
  And Playwright configured with the Zero-Console-Error watchdog fixture
  When the test simulates user navigation, button clicks, and network mocking via page.route()
  Then the page renders without emitting any console.error or uncaught exceptions
  And the test suite completes successfully

Scenario: [WQG-HP-04] [Tier A - Unit] Automated generation of 3-5 step manual smoke checklist
  Given all tasks in an epic reach status done and Phase 4 executes
  When the smoke generator parses primary BDD Happy Path scenarios
  Then it emits .devtool/epic/<epic_dir>/manual_smoke_checklist.md before Gate 4 validation
  And the checklist contains between 3 and 5 actionable verification steps with Target (URL or CLI Command), Action, and Observable Outcome
```

## Dimension 2: Edge Cases and Boundaries

```gherkin
Scenario: [WQG-EC-01] [Tier A - Unit] Web quality manifest with empty or optional capabilities
  Given a repository where .agents/quality/web-quality.json configures only type_check and test_unit
  When web-quality-check is invoked with profile pr
  Then it resolves only the declared capabilities
  And successfully certifies the repository without erroring on missing optional capabilities

Scenario: [WQG-EC-02] [Tier A - Unit] Benign console warnings filtered by allowlist
  Given a web page emitting known third-party library deprecation warnings
  And an allowlist regex configured in .agents/quality/web-quality.json
  When the Playwright test executes
  Then the Zero-Console-Error watchdog filters out matching allowlisted warnings
  And does not falsely fail the test suite

Scenario: [WQG-EC-03] [Tier C - Integration] Mutually exclusive DOM state leak and duplicate text detection
  Given a UI component with conditional state badges and tooltip accessibility spans
  When Playwright executes with the Zero-Console-And-Layout-Defect Watchdog
  Then it asserts that mutually exclusive elements (e.g. running spinner vs terminal failure badge, visible title vs hidden tooltip) are not simultaneously visible
  And detects consecutive duplicate substring rendering inside card titles/subtitles caused by unstyled hidden spans
  And fails Gate 4 if unstyled hidden spans leak into visible layout
```

## Dimension 3: State Transitions

```gherkin
Scenario: [WQG-ST-01] [Tier A - Unit] Transition from BLOCKED to PASS upon fixing invalid configuration
  Given a repository with a malformed .agents/quality/web-quality.json
  When validate_web_quality.py evaluates the manifest
  Then it reports status BLOCKED with validation findings
  And when the developer corrects the JSON schema
  Then the validator transitions to status PASS

Scenario: [WQG-ST-02] [Tier C - Integration] Task status progression under Anti-Rationalization audit
  Given a Kanban task covering Tier C scenario [WQG-HP-01]
  When the verification runner evaluates task completion with missing Tier C integration evidence or only unit mocks
  Then task_contract.py and task status sync reject the transition to done with condition 6 violation
  And when real Playwright headless integration test execution evidence is provided in the verification results
  Then the task transitions cleanly to status done
```

## Dimension 4: Async and Concurrency

```gherkin
Scenario: [WQG-AR-01] [Tier C - Integration] Concurrent multi-provider fan-out in Gate 4
  Given a polyglot repository (D3Nexus) with providers rust-core and learning-web
  When Gate 4 quality_check executes profile epic
  Then both providers execute concurrently without interfering with each other's outputs
  And Gate 4 aggregates the final verdict based on FAIL > BLOCKED > PASS priority

Scenario: [WQG-AR-02] [Tier C - Integration] Playwright webServer lifecycle management
  Given Playwright configured with webServer command npm run preview
  When Playwright starts the test runner
  Then it awaits the server healthcheck port before dispatching browser tests
  And cleanly tears down the webServer process upon completion
```

## Dimension 5: Failures and Resilience

```gherkin
Scenario: [WQG-FR-01] [Tier C - Integration] Immediate test failure on uncaught JavaScript console error
  Given a web component with a runtime bug emitting console.error("Uncaught TypeError")
  When Playwright executes the test suite
  Then the Zero-Console-Error watchdog immediately halts and fails the test
  And logs the full console message, stack trace, and target URL as evidence

Scenario: [WQG-FR-02] [Tier A - Unit] Missing node_modules or binary execution blocker
  Given an environment where playwright or astro binary is not found in PATH
  When web-quality-check attempts to spawn the process
  Then it catches the spawn failure and emits status BLOCKED with actionable remediation guidance

Scenario: [WQG-FR-03] [Tier C - Integration] Immediate failure on 404 static stylesheet or unstyled computed geometry
  Given an Astro or web page where a critical .css stylesheet returns HTTP status >= 400
  Or a primary structural UI container renders with unstyled default computed styles (transparent background, zero border/padding, or zero dimensions)
  When the Playwright test suite executes with assertVisualIntegrity
  Then the Static Asset Network Trap and geometry watchdog immediately fail the test
  And log the missing asset URL and unstyled element selectors as evidence
```
