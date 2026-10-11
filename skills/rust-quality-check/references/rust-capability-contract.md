# Rust Quality Capability Contract

## Overview

The Rust quality provider is capability-driven and read-only. It avoids imposing a single global command list
onto diverse Rust workspaces. Instead, a participating repository defines its available verification capabilities
in `.agents/quality/rust-quality.json`.

The capability configuration is validated by [rust-quality.schema.json](../resources/schemas/rust-quality.schema.json)
and [validate_rust_quality.py](../resources/scripts/validate_rust_quality.py).

## Manifest Location and Structure

```json
{
  "schema_version": 1,
  "capabilities": {
    "format": ["cargo", "fmt", "--all", "--", "--check"],
    "check": ["cargo", "check", "--all-targets"],
    "clippy": ["cargo", "clippy", "--all-targets", "--", "-D", "warnings"],
    "test": ["cargo", "test", "--workspace"],
    "coverage": {
      "command": ["cargo", "llvm-cov", "--workspace", "--fail-under-lines", "80"],
      "threshold": 0.80
    },
    "architecture": ["cargo", "run", "-p", "xtask", "--", "check-architecture"]
  },
  "profiles": {
    "pr": ["format", "check", "clippy", "test", "architecture"],
    "epic": ["format", "check", "clippy", "test", "coverage", "architecture"],
    "scheduled": ["format", "check", "clippy", "test", "coverage", "architecture", "audit"],
    "release": ["format", "check", "clippy", "test", "coverage", "architecture", "semver"]
  }
}
```

## Contract Rules and Security Controls

1. **Structured Argument Arrays**: Every command must be an explicit array of string arguments. Bare strings, shell pipelines (`|`), or implicit shell interpolation are strictly prohibited to prevent command injection and ensure deterministic execution.
2. **Read-Only Execution**: Commands must verify code without mutating files. Formatting checks use `--check`, and linters report issues without writing in-place fixes.
3. **Fail-Closed Missing Capabilities**: If a profile requires a capability that is missing or fails to execute, the provider returns `BLOCKED`. A nonzero exit code from a completed check returns `FAIL`.
4. **Authoritative Architecture Requirement**: The `epic` profile requires an authoritative `architecture` capability (typically an `xtask`). Omission of this capability produces `BLOCKED`.
