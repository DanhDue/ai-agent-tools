# Provider Registry Contract

## Overview

The provider registry defines explicit dependency injection for quality verification in consumer repositories.
Instead of relying on central heuristics or first-match platform detection, each participating repository defines
its registered quality providers in `.agents/quality/check_quality.json`.

The contract is validated mechanically using [check-quality.schema.json](../resources/schemas/check-quality.schema.json)
and the contract validator script [validate_quality_contract.py](../resources/scripts/validate_quality_contract.py).

## Manifest Location and Structure

Every participating project defines `.agents/quality/check_quality.json` at the root of the repository:

```json
{
  "schema_version": 1,
  "providers": [
    {
      "id": "rust-core",
      "skill": "d3nexus:rust-quality-check",
      "required": true,
      "profiles": [
        "pr",
        "epic",
        "scheduled",
        "release"
      ]
    }
  ]
}
```

## Schema Specification

### Top-Level Fields

- `schema_version` (integer, required): Must be integer `1`. Unknown or unsupported schema versions fail closed.
- `providers` (array of objects, required): Non-empty array of registered quality providers.

### Provider Object Fields

- `id` (string, required): Stable unique identifier for the provider within the repository (e.g. `rust-core`, `mobile-shell`). Must match `^[a-z0-9_-]+$`.
- `skill` (string, required): Namespaced skill identifier invoked to execute quality checks (e.g. `d3nexus:rust-quality-check`).
- `required` (boolean, required): Explicit boolean indicating whether passing this provider is mandatory for overall gate success.
- `profiles` (array of strings, required): Non-empty array of supported quality profiles. Permitted values: `pr`, `epic`, `scheduled`, `release`.

## Contract Rules and Fail-Closed Semantics

1. **Strict Unknown-Field Rejection**: In schema version 1, any unrecognized top-level or provider field is rejected as `unknown_field` with status `BLOCKED`.
2. **Missing Manifest**: If `.agents/quality/check_quality.json` is missing or unreadable, the orchestrator returns `BLOCKED`. No platform heuristic or legacy fallback is attempted.
3. **Duplicate Provider IDs**: Duplicate provider identifiers are strictly forbidden and produce `duplicate_id` with status `BLOCKED`.
4. **Skill Resolution**: Every selected provider's skill must be discoverable in the active runtime. If an unresolvable skill is selected, validation returns `unresolved_skill` with status `BLOCKED`.
5. **Deterministic Ordering**: Execution order and report aggregation sort providers by `id` ascending, ensuring reproducible verdicts across parallel runs.
