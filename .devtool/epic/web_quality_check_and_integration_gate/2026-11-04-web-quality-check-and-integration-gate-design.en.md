# Web Quality Check and Integration Gate Design Spec

## Table of Contents

- [Metadata](#metadata)
- [Problem Statement and Context](#problem-statement-and-context)
- [Goals and Non-Goals](#goals-and-non-goals)
- [Architecture and 3-Tier Testing Standard](#architecture-and-3-tier-testing-standard)
- [Anti-Rationalization and Doubt-Driven Verification](#anti-rationalization-and-doubt-driven-verification)
- [Web Quality Provider Specification](#web-quality-provider-specification)
- [Multi-Repo Registry and Polyglot Gate 4 Integration](#multi-repo-registry-and-polyglot-gate-4-integration)
- [Dev-Designer and Dev-Implementation Enhancements](#dev-designer-and-dev-implementation-enhancements)
- [Automated Smoke Walkthrough Generation](#automated-smoke-walkthrough-generation)
- [Risks and Mitigations](#risks-and-mitigations)
- [Verification Plan](#verification-plan)

## Metadata

- **Epic Name**: `web_quality_check_and_integration_gate`
- **Epic Slug**: `web-quality-check-and-integration-gate`
- **Date**: 2026-11-04
- **Author**: Human Architect & AI Assistant
- **Status**: Draft Spec (Stage 1 Inception)
- **Target Repositories**: `ai-agent-tools`, `D3Nexus`, `lyrics-sync`, `nexus`

## Problem Statement and Context

In our multi-repository ecosystem (`D3Nexus`, `lyrics-sync`, `nexus`), developers experience a significant gap between theoretical architectural design and real runtime behavior. This gap forces human engineers to conduct extensive manual testing (bấm tay) on devices and browsers for every release:

1. **The Mocking Fallacy**: Unit tests in `[Tier A - Unit]` achieve 100% green pass rates by isolating components with mock objects (`when(...).thenReturn(...)`). However, the application crashes or breaks when components are wired together at runtime due to DI registration failures, JSON serialization mismatches, lifecycle cancellation, or event-bus stream race conditions.
2. **Missing Web Quality Provider in Gate 4**: The quality orchestration system (`d3nexus:quality_check`) has dedicated providers for Flutter, Android, iOS, Rust, and Python, but completely lacks a `web-quality-check` provider. Consequently:
   - In `D3Nexus`, Gate 4 only verifies `rust-core` (`d3nexus:rust-quality-check`), leaving the Astro + Vanilla TypeScript web application (`apps/learning-web`) completely unverified.
   - In `lyrics-sync`, Gate 4 only verifies `python-core` (`d3nexus:python-quality-check`), leaving the 17 Vanilla JavaScript files (`src/lyrics_sync/preview/static/*.js`) unverified.
3. **Simulated Node-Only E2E Tests**: Many tests located under `tests/e2e/` run in `node:test` without rendering real HTML, without testing Custom Element connections, and without verifying DOM events or browser layout geometries (`getBoundingClientRect`).
4. **AI Rationalization**: AI coding agents routinely rationalize shortcuts: asserting tests in pure Node, ignoring browser console errors, and avoiding headless browser execution.

## Goals and Non-Goals

### Goals
- Create a standardized `web-quality-check` provider implementing Provider Result Contract v1 for Astro TypeScript and Vanilla JavaScript projects.
- Eliminate blind spots in Gate 4 by enabling polyglot multi-provider registration in `D3Nexus` (`rust-core` + `learning-web`) and `lyrics-sync` (`python-core` + `preview-ui`).
- Enforce a strict 3-Tier Testing Standard: Tier A (Unit), Tier C1 (Subcutaneous Integration with real DI and in-memory DB), and Tier C2 (Headless Browser Integration with Playwright and Zero-Console-Error).
- Embed Anti-Rationalization Tables and Doubt-Driven Verification (inspired by `addyosmani/agent-skills`) into skill workflows.
- Automate human verification by generating a concise 3-5 step `manual_smoke_checklist.md` at epic completion, reducing manual exploratory testing time from 30 minutes to 2 minutes.

### Non-Goals
- Migrating Vanilla JavaScript files in `lyrics-sync` to TypeScript (type checking is achieved in-place via JSDoc `// @ts-check` and `jsconfig.json`).
- Replacing existing unit test suites in `D3Nexus` or `lyrics-sync` (existing fast unit tests remain as Tier A).
- Requiring heavy device emulators for local PR/Epic gates (Tier C tests run headless via Playwright and subcutaneous VM harnesses).

## Architecture and 3-Tier Testing Standard

The architecture establishes three distinct testing tiers across mobile and web platforms:

1. **Tier A — Unit Testing**:
   - Scope: Pure algorithms, mathematical state machines, standalone data parsers, and helper functions.
   - Execution: In-process (Node.js, Dart VM, JVM, Python VM).
   - Mocking: External dependencies may be mocked. Speed: <10ms per test.
2. **Tier C1 — Subcutaneous Integration Testing (Mobile & Backend)**:
   - Scope: Presentation controllers (BLoC / ViewModel) down to local database storage, caching, and serialization.
   - Invariant: Zero-Domain-Mock. Mocking domain UseCases or Repositories is strictly prohibited. Real DI containers and in-memory databases (SQLite `:memory:`, Room in-memory) are required.
   - Network Boundary: Network I/O is mocked at the HTTP wire socket using canonical JSON fixtures from `shared-contracts/`.
3. **Tier C2 — Headless Browser Integration Testing (Web)**:
   - Scope: Real DOM rendering, Custom Elements, Vanilla JS/TS controllers, user clicks, navigation, and visual popover placement.
   - Invariant: Zero-Console-Error. Any `console.error` or uncaught page exception immediately fails the test.
   - Network Boundary: Mocked at the browser socket via Playwright `page.route()` returning canonical contract JSON fixtures.

## Anti-Rationalization and Doubt-Driven Verification

Drawing from the principles of `addyosmani/agent-skills`, all coding and testing workflows enforce four anti-rationalization rules:

| Agent Rationalization | Enforced Counter-Rule |
| :--- | :--- |
| "A Node.js test is sufficient to prove this web UI feature works." | **REJECTED**: Node tests prove only pure data logic. 80% of web defects occur in DOM queries, event bubbling, and CSS rendering. Tier C requires headless Playwright execution. |
| "This component is simple; hardcoding mock data in a stub is enough." | **REJECTED**: Method-level stubs bypass JSON deserialization and network interceptors. Wire-level fixtures from `shared-contracts/` are mandatory. |
| "The red errors in the browser console are just harmless warnings." | **REJECTED**: The Zero-Console-Error rule fails Gate 4 on any browser console error or uncaught exception. |
| "I cannot launch a mobile simulator, so I will write a unit test instead." | **REJECTED**: Mobile Tier C requires Subcutaneous Testing with real DI and in-memory persistence. Pure unit tests cannot be tagged as Tier C. |

Under Doubt-Driven Verification (`CLAIM -> EXTRACT -> DOUBT -> RECONCILE`), Gate 4 audits tests to confirm that Tier C tests actually exercise production code paths without mocking the primary system under test.

## Web Quality Provider Specification

A new skill `d3nexus:web-quality-check` is authored in `skills/web-quality-check/`:

1. **Invocation Contract**: Conforms to Provider Result Contract v1, accepting `{ "profile": "<profile>", "base_ref": "<base_ref>", "repository_sha": "<sha>" }`.
2. **Configuration File**: Reads `.agents/quality/web-quality.json` from the repository root.
3. **Capabilities**:
   - `type_check`: Runs `astro check` or `tsc --noEmit` for TypeScript projects, or `tsc --project jsconfig.json` for Vanilla JavaScript projects.
   - `lint`: Runs project linter (ESLint, Biome, or Astro linter).
   - `test_unit`: Executes fast in-memory unit tests (Tier A).
   - `test_e2e`: Launches headless Playwright suites (Tier C2) with the Zero-Console-Error watchdog.
   - `contracts`: Runs cross-repo contract diff verification.
4. **Validation Tooling**: Provides `validate_web_quality.py` to ensure schema conformance and executable presence before execution.

## Multi-Repo Registry and Polyglot Gate 4 Integration

The root Gate 4 orchestrator (`d3nexus:quality_check`) executes multi-provider fan-out across repositories:

- **`D3Nexus` (`.agents/quality/check_quality.json`)**:
  - Provider 1: `rust-core` (`d3nexus:rust-quality-check`) for Rust core, WASM compilation, and system tests.
  - Provider 2: `learning-web` (`d3nexus:web-quality-check`) for Astro templates, Vanilla TypeScript controllers, and Playwright suites.
- **`lyrics-sync` (`.agents/quality/check_quality.json`)**:
  - Provider 1: `python-core` (`d3nexus:python-quality-check`) for FastAPI endpoints, worker logic, and pytest suites.
  - Provider 2: `preview-ui` (`d3nexus:web-quality-check`) for static Vanilla JS type checking and Chrome Playwright tests.
- **`nexus` (`.agents/quality/check_quality.json`)**:
  - Provider 1: `flutter-core` (`d3nexus:flutter-quality-check`) enforcing Subcutaneous Widget Testing with real DI and WireMock.

## Dev-Designer and Dev-Implementation Enhancements

1. **`dev-designer` (Stage 2)**:
   - When detecting a Web project, the HLD `Integration results:` line must target Playwright headless output (`build/test-results/playwright.json`).
   - BDD scenarios for Tier C must include concrete DOM interaction expectations and wiremock assertions.
2. **`dev-implementation` (Stage 3)**:
   - Integrates the Anti-Rationalization Table into task execution.
   - Validates that tasks claiming Tier C scenario coverage execute real headless browser or subcutaneous tests.
   - Halts and reports `BLOCKED` if test code mocks the component under test.

## Automated Smoke Walkthrough Generation

Upon successful completion of all tasks and a passing Gate 4 machine verdict, `dev-implementation` automatically generates a human-oriented verification artifact:
- Path: `.devtool/epic/<epic_dir>/manual_smoke_checklist.md`
- Content: 3 to 5 concise, actionable manual steps extracted directly from the primary BDD Happy Path scenarios (e.g. Target URL, user action, observable visual outcome).
- Benefit: Reduces developer exploratory testing from 30 minutes of unstructured wandering to a 2-minute deterministic confirmation.

## Risks and Mitigations

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| Playwright installation overhead in CI / local dev | Slow Gate 4 runs | Use headless Chromium only; cache browser binaries; profile `pr` runs unit tests, profile `epic` runs Playwright. |
| Port conflicts when launching preview servers | Test flakiness | Playwright `webServer` configuration binds to dynamic or dedicated ports with healthcheck probes. |
| Existing legacy console warnings triggering Zero-Console-Error | False positive failures | Allow an explicit, documented allowlist of benign vendor warnings in `.agents/quality/web-quality.json`. |

## Verification Plan

1. **Provider Contract Verification**:
   - Run `validate_web_quality.py` against `.agents/quality/web-quality.json` sample configurations.
   - Execute `quality_check` with profile `epic` in `D3Nexus` and verify both `rust-core` and `learning-web` produce certified verdicts.
2. **Playwright Zero-Console-Error Verification**:
   - Inject an intentional `console.error` into a test page; confirm that Playwright and Gate 4 correctly report `FAIL`.
   - Resolve the error and confirm Gate 4 transitions to `PASS`.
3. **Vanilla JS Type-Checking Verification**:
   - Run `tsc --project jsconfig.json` against `lyrics-sync/src/lyrics_sync/preview/static/` and verify clean type validation.
4. **Smoke Checklist Generation Verification**:
   - Verify that completing an epic produces `.devtool/epic/<epic_dir>/manual_smoke_checklist.md` containing 3-5 structured steps.
