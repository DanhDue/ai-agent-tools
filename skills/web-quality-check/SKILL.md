---
name: web-quality-check
description: Read-only Web quality assurance provider implementing the common quality contract. Executes project-configured capabilities from .agents/quality/web-quality.json for Astro TypeScript and Vanilla JavaScript projects, and outputs structured results bound to repository SHA.
---

# Web Quality Assurance Provider

## Table of Contents

- [Overview](#overview)
- [Workflow](#workflow)
  - [Step 1: Configuration Loading and Validation](#step-1-configuration-loading-and-validation)
  - [Step 2: Read-Only Command Execution](#step-2-read-only-command-execution)
  - [Step 3: Watchdog Verification](#step-3-watchdog-verification)
  - [Step 4: Result Assembly and Contract Emission](#step-4-result-assembly-and-contract-emission)
- [Profile Capability Matrix](#profile-capability-matrix)
- [References and Resources](#references-and-resources)

## Overview

You are the Web Quality Provider (`d3nexus:web-quality-check`). When invoked by `quality_check`, you execute read-only quality verification against the active repository according to the requested quality profile.

You do not guess commands from file layouts. You load capabilities from `.agents/quality/web-quality.json`, execute the project-declared command arrays, collect evidence, and output a validated result document adhering to the shared [Provider Result Contract](../quality_check/references/provider-result-contract.md).

## Workflow

```mermaid
flowchart TD
    INVOKE["Invoked with normalized request payload"] --> LOAD["Step 1: Load .agents/quality/web-quality.json"]
    LOAD --> VALIDATE["Step 2: Validate capability configuration and profile completeness"]
    VALIDATE --> PLAN["Step 3: Resolve execution plan for requested profile"]
    PLAN --> EXEC["Step 4: Execute read-only commands without shell interpolation"]
    EXEC --> WATCHDOG["Step 5: Verify Playwright Zero-Console-And-Layout-Defect Watchdog"]
    WATCHDOG --> RESULT["Step 6: Emit validated result document bound to repository SHA"]
```

### Step 1: Configuration Loading and Validation

Load the project capability manifest `.agents/quality/web-quality.json` from the repository root:

```bash
python3 skills/web-quality-check/resources/scripts/validate_web_quality.py .agents/quality/web-quality.json --profile "<profile>"
```

- If `.agents/quality/web-quality.json` is missing or invalid: emit status `BLOCKED`.
- If the requested profile is not configured: emit status `BLOCKED`.
- For profile `pr`: if `type_check`, `lint`, or `test_unit` is missing: emit status `BLOCKED`.
- For profile `epic` or `release`: if `test_e2e` is missing: emit status `BLOCKED`.

### Step 2: Read-Only Command Execution

Execute commands declared in `capabilities` for the target profile:
1. Commands are executed as structured argument arrays (no shell interpolation).
   - An argument beginning with `{skills_dir}` is resolved to the directory containing this plugin's `skills/` folders (the parent of `web-quality-check/`), so manifests can call sibling skill scripts without machine-specific paths (e.g. `["python3", "{skills_dir}/sync-shared-contracts/resources/scripts/sync_contracts.py", "diff-check", "--base-ref", "{base_ref}"]`).
   - An argument containing `{base_ref}` is substituted with the normalized `base_ref` invocation parameter from `quality_check` (falling back to `main` or `develop` as appropriate).
2. All commands run from the resolved repository root.
3. If an executable is missing or cannot be spawned: record check status as `BLOCKED`.
4. If a command runs and reports defects (nonzero exit code):
   - For governance and contract capabilities (`contracts`, `contracts_<domain>`, and `contract_diff`): exit code `0` records `PASS`, exit code `2` (or JSON `"status": "BLOCKED"`) records `BLOCKED`, and any other nonzero exit code records `FAIL`.
   - For all other capabilities: nonzero exit code records `FAIL`.
5. If a command succeeds (zero exit code): record check status as `PASS`.

Independent commands (e.g. `type_check`, `lint`, `test_unit`) may run concurrently.

### Step 3: Watchdog Verification

For `epic` and `release` profiles:
- Web integration testing mandates headless Playwright execution with the Zero-Console-And-Layout-Defect watchdog fixture.
- The provider verifies that `build/test-results/playwright.xml` exists and records zero console errors and zero layout leaks.
- If watchdog evidence is missing or unverified, the provider reports status `BLOCKED`.

### Step 4: Result Assembly and Contract Emission

Assemble the result document matching the Provider Result Contract schema:

- `provider_id`: `"web-quality"` (or matching invocation identifier)
- `contract_version`: `1`
- `profile`: `<profile>`
- `repository_sha`: Verified commit SHA matching invocation
- `status`: Aggregated provider status (`FAIL` if any check failed, `BLOCKED` if any check blocked, else `PASS`)
- `started_head` and `finished_head`: Git SHA recorded before and after execution
- `checks`, `coverage`, `evidence`, `blockers`, `warnings`

Return the result document to the orchestrator.

## Profile Capability Matrix

| Profile | Required Capabilities | Verification Standard |
| :--- | :--- | :--- |
| `pr` | `type_check`, `lint`, `test_unit` | Fast verification of static types and unit invariants |
| `epic` | `type_check`, `lint`, `test_unit`, `test_e2e` | Strict end-to-end certification with Playwright watchdog evidence |
| `release` | `type_check`, `lint`, `test_unit`, `test_e2e` | Strict release sign-off with watchdog evidence |
| `scheduled` | Configured periodic capabilities | Continuous monitoring and health audits |

## References and Resources

- [Provider Result Contract](../quality_check/references/provider-result-contract.md): Shared schema specification for quality provider results.
- [Capability Validator](resources/scripts/validate_web_quality.py): Script and CLI validator for Web capability configuration files.
