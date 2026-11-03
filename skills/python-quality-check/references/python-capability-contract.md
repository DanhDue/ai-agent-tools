# Python Quality Capability Contract

## Overview

The Python quality provider is capability-driven and read-only. It avoids imposing a single global command list
onto diverse Python environments (e.g. `uv`, `poetry`, standard `venv`, `pipenv`). Instead, a participating repository defines
its available verification capabilities in `.agents/quality/python-quality.json`.

The capability configuration is validated by [python-quality.schema.json](../resources/schemas/python-quality.schema.json)
and [validate_python_quality.py](../resources/scripts/validate_python_quality.py).

## Manifest Location and Structure

```json
{
  "schema_version": 1,
  "capabilities": {
    "format": ["uv", "run", "ruff", "format", "--check", "."],
    "lint": ["uv", "run", "ruff", "check", "."],
    "type_check": ["uv", "run", "mypy", "--strict", "src"],
    "test": ["uv", "run", "pytest", "-m", "not slow and not acceptance and not live_llm"],
    "coverage": {
      "command": ["uv", "run", "pytest", "--cov=src", "--cov-report=json:coverage.json"],
      "threshold": 0.80
    },
    "architecture": ["uv", "run", "lint-imports"],
    "schema": ["uv", "run", "python", "-m", "lyrics_sync.model", "--check-schema"],
    "acceptance": ["./scripts/run_e2e_acceptance.sh"]
  },
  "profiles": {
    "pr": ["format", "lint", "type_check", "test"],
    "epic": ["format", "lint", "type_check", "test", "coverage", "architecture", "acceptance"],
    "scheduled": ["format", "lint", "type_check", "test", "coverage", "architecture", "security"],
    "release": ["format", "lint", "type_check", "test", "coverage", "architecture", "acceptance", "docs"]
  }
}
```

## Contract Rules and Security Controls

1. **Structured Argument Arrays**: Every command must be an explicit array of string arguments. Bare strings, shell pipelines (`|`), or implicit shell interpolation are strictly prohibited to prevent command injection and ensure deterministic execution.
2. **Read-Only Execution**: Commands must verify code without mutating files. Formatting checks use `--check`, and linters report issues without writing in-place fixes.
3. **Fail-Closed Missing Capabilities**: If a profile requires a capability that is missing or fails to execute, the provider returns `BLOCKED`. Nonzero exit codes are mapped according to capability type (see Rule 7).
4. **Authoritative Architecture Requirement**: The `epic` profile requires an authoritative architecture governance command (`architecture` or `boundaries`, such as `lint-imports` or custom AST rules). Omission of this capability produces `BLOCKED`.
5. **Portable Plugin Paths**: Never hard-code a home directory or plugin cache path. An argument starting with `{skills_dir}` is resolved by the provider to the installed plugin's `skills/` directory, e.g. `["python3", "{skills_dir}/sync-shared-contracts/resources/scripts/sync_contracts.py", "check", "--strict"]`.
6. **Base Ref Placeholder**: An argument containing `{base_ref}` is expanded from `quality_check`'s normalized `base_ref` invocation parameter (falling back to `develop` or the repository default only when `base_ref` was not supplied), e.g. `["python3", "{skills_dir}/sync-shared-contracts/resources/scripts/sync_contracts.py", "diff-check", "--base-ref", "{base_ref}"]`.
7. **Exit Code 2 BLOCKED Mapping**: For governance and contract capabilities (`contracts`, `contracts_<domain>`, and `contract_diff`), exit code `0` maps to `PASS`, exit code `2` (or JSON `"status": "BLOCKED"`) maps to `BLOCKED`, and any other nonzero exit code (such as `1`) maps to `FAIL`. All other capabilities retain standard nonzero exit code -> `FAIL`.
