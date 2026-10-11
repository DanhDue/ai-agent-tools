# Provider Result Contract

## Overview

Quality providers communicate findings and verification evidence through machine-readable result documents.
Each provider produces one structured result document bound to the immutable repository commit SHA being verified.

The contract is validated mechanically using [provider-result.schema.json](../resources/schemas/provider-result.schema.json)
and the contract validator script [validate_quality_contract.py](../resources/scripts/validate_quality_contract.py).

## Result Structure

```json
{
  "provider_id": "rust-core",
  "contract_version": 1,
  "profile": "epic",
  "repository_sha": "5d8b7b0f1b7a9c6f7c8f6498e69c3d6f1e0a4123",
  "status": "PASS",
  "checks": [
    {
      "id": "cargo-check",
      "category": "compile",
      "status": "PASS",
      "source": "cargo check --all-targets",
      "duration": 12.4,
      "summary": "Compilation check succeeded with 0 warnings",
      "evidence_refs": ["check-log"]
    }
  ],
  "coverage": {
    "lines": {
      "measured": 0.88,
      "threshold": 0.85
    }
  },
  "evidence": [
    {
      "id": "check-log",
      "type": "command",
      "source": "cargo check",
      "location": "artifacts/cargo-check.log"
    }
  ],
  "started_head": "5d8b7b0f1b7a9c6f7c8f6498e69c3d6f1e0a4123",
  "finished_head": "5d8b7b0f1b7a9c6f7c8f6498e69c3d6f1e0a4123",
  "duration": 45.2,
  "blockers": [],
  "warnings": []
}
```

## Schema Specification

### Top-Level Fields

- `provider_id` (string, required): Identifier matching the provider registration.
- `contract_version` (integer, required): Must be integer `1`.
- `profile` (string, required): Quality profile matching the invocation (`pr`, `epic`, `scheduled`, `release`).
- `repository_sha` (string, required): 40-character hexadecimal git commit SHA.
- `status` (string, required): Overall provider verdict: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.
- `checks` (array of objects, required): Structured breakdown of individual checks performed.
- `coverage` (object, required): Measured code coverage and required thresholds.
- `evidence` (array of objects, required): Verifiable evidence records confirming executed checks.
- `started_head` (string, required): Git HEAD SHA at the start of provider execution.
- `finished_head` (string, required): Git HEAD SHA at the conclusion of provider execution.
- `duration` (number, required): Execution duration in seconds (must be non-negative).
- `blockers` (array, required): Actionable blocking issues requiring resolution.
- `warnings` (array, required): Non-blocking advisory findings.

### Check Object Fields

- `id` (string, required): Unique check identifier within the provider.
- `category` (string, required): Category classification (e.g. `lint`, `compile`, `unit-test`, `security`, `architecture`).
- `status` (string, required): Individual check verdict (`PASS`, `FAIL`, `BLOCKED`, `NOT_APPLICABLE`).
- `source` (string, required): Executed command or audit tool source.
- `duration` (number, required): Check duration in seconds.
- `summary` (string, required): Human-readable summary of the check result.
- `evidence_refs` (array of strings, required): List of evidence identifiers referenced by this check.
- `not_applicable_reason` (object, optional): Mandatory when status is `NOT_APPLICABLE`. Contains `code` and `detail`.

### Evidence Object Fields

- `id` (string, required): Evidence identifier referenced by checks.
- `type` (string, required): Evidence type (`command`, `applicability`, `audit`, `log`, `report`).
- `source` (string, required): Producing tool or command.
- `location` (string, required): File path or URL to evidence output.
- `digest` (string, optional): SHA256 cryptographic digest of the evidence content.

## Contract Rules and Verification Boundaries

1. **Identity and SHA Integrity**: `started_head`, `finished_head`, and `repository_sha` must match the requested SHA. Any divergence invalidates evidence as stale and produces `BLOCKED`.
2. **Evidence Resolution**: Every reference in `evidence_refs` must resolve to a valid entry in `evidence`.
3. **NOT_APPLICABLE Constraints**: `NOT_APPLICABLE` requires a structured reason (`profile_policy`, `scope_unmodified`, `capability_not_configured`, `target_absent`, `platform_not_applicable`) and evidence of type `applicability`. Missing tools, timeouts, or command errors produce `BLOCKED` or `FAIL`, never `NOT_APPLICABLE`.
4. **Deterministic Precedence**: `FAIL` > `BLOCKED` > `PASS`. Product defects outrank infrastructure blockage.
