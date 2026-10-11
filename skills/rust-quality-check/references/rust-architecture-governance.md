# Rust Architecture Governance

## Overview

In Android Native projects, Kotlin Konsist provides declarative AST-level architectural assertions for Clean Architecture
and MVI layer boundaries. Rust does not currently offer a single universal Konsist clone that understands arbitrary
crate-oriented architectural boundaries.

The authoritative Konsist-equivalent boundary for mature Rust codebases is a **project-owned `xtask` architecture check**
powered by `cargo_metadata`.

## The Authoritative xtask Boundary

A project declares its architecture verification command in `.agents/quality/rust-quality.json`:

```json
{
  "capabilities": {
    "architecture": ["cargo", "run", "-p", "xtask", "--", "check-architecture"]
  }
}
```

The `xtask` command queries `cargo_metadata` to inspect:
1. **Feature Module Isolation**: Verifies that sibling feature crates do not import each other directly.
2. **Layer Boundary Inversion**: Enforces that Domain crates contain pure business logic with zero framework or driver dependencies.
3. **Application & Infrastructure Direction**: Verifies that Presentation and Infrastructure layers depend inward on Domain abstractions.
4. **MVI State Immutability**: Inspects crate public exports to ensure intents, reducers, and states follow unidirectional data flow contracts.
5. **Forbidden Dependencies**: Enforces dependency deny-lists across sensitive crates (e.g. banning async runtimes in pure domain crates).

## Supplemental Diagnostic Tools

Other community tools may provide supplemental diagnostics, but are not treated as authoritative architecture gates:
- `cargo-modules`: Provides dependency tree visualizations and crate hierarchy graphs.
- `ArchUnitRust`: Evaluated as an experimental DSL; non-authoritative unless formally integrated into project policy.
- `syn`-based scripts: Suitable for narrow AST checks (e.g. enforcing naming conventions), but lack workspace-wide dependency graph context.

The provider requires project-declared `architecture` evidence before granting `PASS` for the `epic` profile.
