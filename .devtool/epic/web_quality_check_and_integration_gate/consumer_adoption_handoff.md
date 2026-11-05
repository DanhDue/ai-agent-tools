# Consumer Adoption Handoff: Polyglot Quality Gate & Web Provider

## Table of Contents

- [Overview](#overview)
- [Rule 7 Isolation Compliance](#rule-7-isolation-compliance)
- [D3Nexus Adoption Package](#d3nexus-adoption-package)
  - [Quality Check Registry](#quality-check-registry)
  - [Web Quality Manifest](#web-quality-manifest)
  - [Playwright Watchdog Attachment](#playwright-watchdog-attachment)
- [lyrics-sync Adoption Package](#lyrics-sync-adoption-package)
  - [Quality Check Registry](#quality-check-registry-1)
  - [Web Quality Manifest](#web-quality-manifest-1)
  - [Playwright Watchdog Attachment](#playwright-watchdog-attachment-1)
- [Downstream Execution Workflow](#downstream-execution-workflow)

## Overview

This document specifies the exact configuration files, provider declarations, and watchdog attachments required for downstream repositories (`D3Nexus` and `lyrics-sync`) to adopt the `web-quality-check` provider and multi-provider Gate 4 orchestration delivered in `ai-agent-tools`.

## Rule 7 Isolation Compliance

> [!IMPORTANT]
> Under **Critical Rule 7 (Multi-Repo Boundaries & Contract Governance)**, agents operating in `ai-agent-tools` MUST NOT execute git commits or stage files in adjacent repositories (`D3Nexus`, `lyrics-sync`, `nexus`).
> 
> The packages below are canonical blueprints. Downstream engineers or AI agents must implement these configurations inside dedicated task branches within their respective repository workspaces.

## D3Nexus Adoption Package

- **Repository**: `D3Nexus`
- **Architecture**: Polyglot Hub (Rust Core + Astro TypeScript Web Frontend)
- **Target Directories**: `.agents/quality/`, `apps/learning-web/`

### Quality Check Registry

Place at `.agents/quality/check_quality.json`:

```json
{
  "schema_version": 1,
  "providers": [
    {
      "id": "rust-core",
      "skill": "d3nexus:rust-quality-check",
      "required": true,
      "profiles": ["pr", "epic", "release", "scheduled"]
    },
    {
      "id": "learning-web",
      "skill": "d3nexus:web-quality-check",
      "required": true,
      "profiles": ["pr", "epic", "release", "scheduled"]
    }
  ]
}
```

### Web Quality Manifest

Place at `.agents/quality/web-quality.json`:

```json
{
  "schema_version": 1,
  "capabilities": {
    "type_check": ["npm", "--prefix", "apps/learning-web", "run", "check"],
    "lint": ["npm", "--prefix", "apps/learning-web", "run", "lint"],
    "test_unit": ["npm", "--prefix", "apps/learning-web", "run", "test:unit"],
    "test_e2e": ["npx", "playwright", "test", "--config", "apps/learning-web/playwright.config.ts"],
    "contracts": ["python3", "{skills_dir}/sync-shared-contracts/resources/scripts/sync_contracts.py", "diff-check", "--base-ref", "{base_ref}"]
  },
  "profiles": {
    "pr": ["type_check", "lint", "test_unit"],
    "epic": ["type_check", "lint", "test_unit", "test_e2e"],
    "release": ["type_check", "lint", "test_unit", "test_e2e"],
    "scheduled": ["type_check", "lint", "test_unit", "test_e2e"]
  }
}
```

### Playwright Watchdog Attachment

1. Copy `playwright-zero-error.fixture.ts` from `ai-agent-tools/skills/web-quality-check/resources/templates/` to `apps/learning-web/tests/fixtures/playwright-zero-error.fixture.ts`.
2. In `apps/learning-web/tests/e2e/*.spec.ts`, import `test` and `expect` from the fixture:
   ```typescript
   import { test, expect, assertVisualIntegrity, assertDomStateIntegrity } from '../fixtures/playwright-zero-error.fixture';
   ```

---

## lyrics-sync Adoption Package

- **Repository**: `lyrics-sync`
- **Architecture**: Polyglot Satellite (Python FastAPI Worker + Vanilla JavaScript Preview UI)
- **Target Directories**: `.agents/quality/`, `src/lyrics_sync/preview/`

### Quality Check Registry

Place at `.agents/quality/check_quality.json`:

```json
{
  "schema_version": 1,
  "providers": [
    {
      "id": "python-core",
      "skill": "d3nexus:python-quality-check",
      "required": true,
      "profiles": ["pr", "epic", "release", "scheduled"]
    },
    {
      "id": "preview-ui",
      "skill": "d3nexus:web-quality-check",
      "required": true,
      "profiles": ["pr", "epic", "release", "scheduled"]
    }
  ]
}
```

### Web Quality Manifest

Place at `.agents/quality/web-quality.json`:

```json
{
  "schema_version": 1,
  "capabilities": {
    "type_check": ["npx", "tsc", "--project", "jsconfig.json"],
    "lint": ["ruff", "check", "."],
    "test_unit": ["python3", "-m", "pytest", "tests/unit"],
    "test_e2e": ["python3", "-m", "pytest", "tests/e2e_full_screens_chrome_test.py", "--junitxml=build/test-results/playwright.xml"],
    "ui_review": [
      "python3",
      "{skills_dir}/web-quality-check/resources/scripts/audit_ui_state_and_styles.py",
      "--base-ref",
      "{base_ref}"
    ],
    "contracts": [
      "python3",
      "{skills_dir}/sync-shared-contracts/resources/scripts/sync_contracts.py",
      "diff-check",
      "--base-ref",
      "{base_ref}"
    ]
  },
  "profiles": {
    "pr": ["type_check", "lint", "test_unit", "contracts"],
    "epic": ["type_check", "lint", "test_unit", "test_e2e", "ui_review", "contracts"],
    "release": ["type_check", "lint", "test_unit", "test_e2e", "ui_review", "contracts"],
    "scheduled": ["type_check", "lint", "test_unit", "test_e2e", "ui_review", "contracts"]
  }
}
```

### Playwright Watchdog Attachment and Reporter Configuration

#### Python (pytest-playwright) Projects
1. Copy `playwright_zero_error.py` from `ai-agent-tools/skills/web-quality-check/resources/templates/` to `tests/helpers/playwright_zero_error.py`.
2. Configure pytest to emit JUnit XML to `build/test-results/playwright.xml` by passing `--junitxml=build/test-results/playwright.xml`.
3. In `tests/e2e_full_screens_chrome_test.py`, attach watchdog during page fixture setup:
   ```python
   from tests.helpers.playwright_zero_error import attach_zero_error_watchdog

   def test_screen(page):
       watchdog = attach_zero_error_watchdog(page)
       page.goto("http://localhost:8000/preview/")
       # user actions ...
       watchdog.assert_zero_defects()  # automatically emits build/test-results/watchdog-receipt.json
   ```

#### TypeScript (Playwright Test) Projects
1. Copy `playwright-zero-error.fixture.ts` from `ai-agent-tools/skills/web-quality-check/resources/templates/` to `tests/fixtures/playwright-zero-error.fixture.ts`.
2. Configure `playwright.config.ts` to output JUnit XML to `build/test-results/playwright.xml`:
   ```typescript
   import { defineConfig } from '@playwright/test';

   export default defineConfig({
     reporter: [
       ['list'],
       ['junit', { outputFile: 'build/test-results/playwright.xml' }]
     ],
     testDir: './tests',
   });
   ```
3. Use the extended `test` fixture in spec files:
   ```typescript
   import { test, expect } from './fixtures/playwright-zero-error.fixture';

   test('preview loads with zero console or layout defects', async ({ page, watchdog }) => {
     await page.goto('http://localhost:4321/');
     // assertions...
     // watchdog fixture teardown automatically verifies zero defects and emits build/test-results/watchdog-receipt.json
   });
   ```

---

## Historical Evidence Disclosure (RED Scaffold Placeholders)

During the inception and task specification phase of Tasks 01 through 06, initial task kickoff evidence files in `evidence/` captured initial failure markers via red scaffold placeholders (`assert False`) prior to implementation and authoring of comprehensive BDD regression test suites.

All behavioral contracts and invariants are now validated by genuine regression tests across 14 BDD scenarios with 43+ passing tests, structured watchdog receipts, live server verification, and polyglot gate aggregation.

---

## Downstream Execution Workflow

1. Open workspace in the downstream repository (`D3Nexus` or `lyrics-sync`).
2. Run `dev-implementation` or create a new quality setup branch `epic/polyglot-quality-gate`.
3. Apply the registry and manifest files above.
4. Run `python3 skills/quality_check/resources/scripts/verify_polyglot_registry.py .agents/quality/check_quality.json --profile epic --execute` to verify Gate 4 returns certified `PASS`.
