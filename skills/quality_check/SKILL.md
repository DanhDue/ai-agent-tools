---
name: quality_check
description: Platform-neutral quality gatekeeper and orchestrator that discovers project-registered providers from .agents/quality/check_quality.json, validates versioned contracts, aggregates verdicts (FAIL > BLOCKED > PASS), and renders immutable SHA-bound executive reports.
---

# Platform-Neutral Quality Check Orchestrator

## Overview

You are the Master Quality Orchestrator and Governance Gatekeeper. Your role is platform-neutral: you do not embed
ecosystem-specific compilers, testing tools, or heuristics. Instead, you act as the composition root for project quality,
discovering registered capability providers via dependency injection, fanning out execution across all selected providers,
validating versioned contracts, and synthesizing a single deterministic Gate 4 verdict bound to an immutable commit SHA.

Execution is strictly read-only: quality certification verifies existing code and never mutates source files or applies
auto-fix scripts during verification.

## Architecture and Execution Sequence

```mermaid
flowchart TD
    CALLER["Caller supplies profile, base ref, and target SHA"] --> NORMALIZE["Step 0: Normalize request and verify repository SHA"]
    NORMALIZE --> REGISTRY["Step 1: Load .agents/quality/check_quality.json"]
    REGISTRY --> VALIDATE["Step 2: Validate registry and select providers"]
    VALIDATE --> FANOUT["Step 3: Fan out invocation across all selected providers"]
    FANOUT --> HEAD_CHECK["Step 4: Verify finished repository HEAD matches initial SHA"]
    HEAD_CHECK --> CONTRACT_CHECK["Step 5: Validate provider results and reconcile plan"]
    CONTRACT_CHECK --> REDUCE["Step 6: Aggregate statuses and render executive report"]
    REDUCE --> VERDICT{"Overall status"}
    VERDICT -->|"PASS"| LGTM["Render Gate 4 LGTM for verified SHA"]
    VERDICT -->|"FAIL"| REJECT_FAIL["Report product defects"]
    VERDICT -->|"BLOCKED"| REJECT_BLOCKED["Report infrastructure blockers"]
```

## Step-by-Step Orchestration Workflow

### Step 0: Input Normalization and Invocation Contract

Normalize caller parameters:
- `profile`: Defaults to `pr` for direct interactive invocations. Formal lifecycle callers (`dev-implementation`, `dev-lifecycle`) must pass explicit profile (`epic`, `scheduled`, `release`).
- `base_ref`: Branch or ref used for blast radius, changed-file scope, and impact analysis (e.g. `main`, `develop`).
- `repository_sha`: The 40-character commit SHA to certify. If omitted, resolve immediately using `git rev-parse HEAD`.

Construct the immutable invocation payload:

```json
{
  "contract_version": 1,
  "profile": "<profile>",
  "base_ref": "<base_ref>",
  "repository_sha": "<sha>"
}
```

Validate the invocation using [validate_quality_contract.py](resources/scripts/validate_quality_contract.py). If invocation parameters are invalid, halt immediately with status `BLOCKED`.

### Step 1: Project Registry Loading

Load the project quality manifest located at `.agents/quality/check_quality.json` from the repository root:

```bash
python3 skills/quality_check/resources/scripts/validate_quality_contract.py registry .agents/quality/check_quality.json --profile "<profile>"
```

Fail-closed rules:
- If `.agents/quality/check_quality.json` is missing or unreadable: halt with status `BLOCKED`. Never attempt fallback platform detection.
- If the registry contains unknown fields, unsupported schema versions, duplicate provider IDs, or empty provider lists: halt with status `BLOCKED`.
- If no provider matches the requested profile: return `BLOCKED` with finding `empty_selection`.
- If a selected provider's skill is unresolvable in the active environment: halt with status `BLOCKED`.

### Step 2: Provider Invocation Fan-Out

For every provider selected by the registry for the requested profile:
1. Provide the identical immutable invocation payload, adding the provider's `provider_id` and `required` flag.
2. Invoke the provider skill (e.g. `d3nexus:rust-quality-check`).
3. Providers execute read-only checks matching their declared profile capabilities.
4. Collect one structured result document per provider.

Independent providers may run concurrently. Output ordering is never dependent on execution order.

### Step 3: Stale-Evidence and Final HEAD Verification

Before accepting provider evidence, verify current repository HEAD:

```bash
git rev-parse HEAD
```

If current HEAD differs from `repository_sha`, repository state drifted during execution. All collected evidence is rejected as stale, and the overall run returns `BLOCKED`.

### Step 4: Result Contract Validation and Plan Reconciliation

Reconcile collected provider results against the execution plan:

```bash
python3 skills/quality_check/resources/scripts/validate_quality_contract.py reconcile "<plan_json>" --results "<result_files...>"
```

Validation guarantees:
- Every result document matches [provider-result.schema.json](resources/schemas/provider-result.schema.json).
- Identity fields (`provider_id`, `profile`, `repository_sha`, `started_head`, `finished_head`) match the invocation.
- Missing results or duplicate results for a provider generate synthetic `BLOCKED` findings.
- Evidence references resolve cleanly to recorded evidence artifacts.

### Step 5: Deterministic Aggregation and Executive Report

Reduce validated results into a unified verdict:

```bash
python3 skills/quality_check/resources/scripts/aggregate_quality_results.py "<plan_json>" "<result_files...>" --markdown
```

Precedence policy:
$$\text{FAIL} > \text{BLOCKED} > \text{PASS}$$

1. **FAIL**: If any provider reported `FAIL`, the overall verdict is `FAIL`. All defects and blockers remain visible.
2. **BLOCKED**: If no failure occurred, but any required provider reported `BLOCKED` or failed reconciliation, the overall verdict is `BLOCKED`.
3. **PASS**: Granted if and only if every required provider passed.
4. **NOT_APPLICABLE**: An optional provider may be neutral if supported by applicability evidence. A required provider with only `NOT_APPLICABLE` checks is converted to `BLOCKED`.

### Step 6: Gate 4 Certification

Only an aggregated verdict of **PASS** bound to the candidate commit SHA qualifies for Gate 4 `🟢 LGTM`. If the verdict is `FAIL` or `BLOCKED`, render the complete executive report detailing all blockers and warnings, and stop.

## Reference Contracts and Resources

- [Provider Registry Contract](references/provider-registry-contract.md): Format and rules for `.agents/quality/check_quality.json`.
- [Provider Result Contract](references/provider-result-contract.md): Schema and constraints for provider result documents.
- [Result Aggregation Contract](references/aggregation-contract.md): Deterministic precedence and status reduction model.
- [Executive Report Format](references/executive-report-format.md): Layout specification for pull request and Gate 4 reports.
- [Registry Schema](resources/schemas/check-quality.schema.json): Machine-readable JSON Schema for project registries.
- [Result Schema](resources/schemas/provider-result.schema.json): Machine-readable JSON Schema for provider results.
- [Contract Validator](resources/scripts/validate_quality_contract.py): Standard-library validator script and CLI.
- [Aggregation Engine](resources/scripts/aggregate_quality_results.py): Result aggregation and markdown report engine.
