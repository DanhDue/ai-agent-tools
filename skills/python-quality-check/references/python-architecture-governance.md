# Python Architecture Governance

## Overview

In Android Native projects, Kotlin Konsist provides declarative AST-level architectural assertions for Clean Architecture
and MVI layer boundaries. In Python codebases, architectural layering and modular isolation are enforced through
declarative contract tools such as `import-linter` (`lint-imports`), `pytest-archon`, or project AST rules.

The authoritative Konsist-equivalent boundary for mature Python codebases is a **declarative import contracts suite**
powered by `import-linter` (`.importlinter`) or equivalent architecture linters.

## Declarative Import Contracts

A project declares its architecture verification command in `.agents/quality/python-quality.json`:

```json
{
  "capabilities": {
    "architecture": ["uv", "run", "lint-imports"]
  }
}
```

The `lint-imports` command evaluates contracts defined in `.importlinter`:
1. **Layer Boundary Inversion**: Enforces that Domain layers (models, business entities) contain pure domain logic with zero dependencies on presentation, CLI, or infrastructure layers.
2. **Feature Module Isolation**: Verifies that independent feature packages do not import internal implementations from sibling features.
3. **Application & Infrastructure Direction**: Verifies that Presentation (CLI/API) and Infrastructure (network, DB, storage) depend inward on Domain abstractions.
4. **Forbidden Dependencies**: Enforces dependency ban lists (e.g. banning network or async runtime packages inside pure domain models).

## Supplemental Diagnostic Tools

Other community tools may provide supplemental diagnostics:
- `pytest-archon`: Pytest fixtures defining architecture assertions for dependency flow.
- `tach`: Rust-backed modular architecture and dependency boundary enforcement for Python.
- AST analysis scripts: Suitable for narrow syntactic checks, but lack workspace-wide graph validation.

The provider requires project-declared `architecture` or `boundaries` evidence before granting `PASS` for the `epic` profile.
