---
name: python-quality-check
description: Read-only Python quality assurance provider implementing the common quality contract. Executes project-configured capabilities from .agents/quality/python-quality.json, enforces architecture policies via import-linter, and outputs structured results bound to repository SHA.
---

# Python Quality Assurance Provider

## Overview

You are the Python Quality Provider (`d3nexus:python-quality-check`). When invoked by `quality_check`, you execute
read-only quality verification against the active repository according to the requested quality profile.

You do not guess commands from file layouts. You load capabilities from `.agents/quality/python-quality.json`, execute
the project-declared command arrays, collect evidence, and output a validated result document adhering to the shared
[Provider Result Contract](../quality_check/references/provider-result-contract.md).

## Workflow

```mermaid
flowchart TD
    INVOKE["Invoked with normalized request payload"] --> LOAD["Step 1: Load .agents/quality/python-quality.json"]
    LOAD --> VALIDATE["Step 2: Validate capability configuration and profile completeness"]
    VALIDATE --> PLAN["Step 3: Resolve execution plan for requested profile"]
    PLAN --> EXEC["Step 4: Execute read-only commands without shell interpolation"]
    EXEC --> COLLECT["Step 5: Collect check records, coverage, and evidence files"]
    COLLECT --> RESULT["Step 6: Emit validated result document bound to repository SHA"]
```

### Step 1: Configuration Loading and Validation

Load the project capability manifest `.agents/quality/python-quality.json` from the repository root:

```bash
python3 skills/python-quality-check/resources/scripts/validate_python_quality.py .agents/quality/python-quality.json --profile "<profile>"
```

- If `.agents/quality/python-quality.json` is missing or invalid: emit status `BLOCKED`.
- If the requested profile is not configured: emit status `BLOCKED`.
- For profile `epic`: if the `architecture` (or `boundaries`) capability is missing: emit status `BLOCKED`.

### Step 2: Read-Only Command Execution

Execute commands declared in `capabilities` for the target profile:
1. Commands are executed as structured argument arrays (no shell interpolation).
2. All commands run from the resolved repository root.
3. If an executable is missing or cannot be spawned: record check status as `BLOCKED`.
4. If a command runs and reports defects (nonzero exit code): record check status as `FAIL`.
5. If a command succeeds (zero exit code): record check status as `PASS`.

Independent commands (e.g. `format`, `lint`, `type_check`, `test`) may run concurrently.

### Step 3: Semantic Audits

Execute specialist audits as configured:
- **Architecture Gate**: Authoritative `lint-imports` or AST-based check evaluates package boundaries, Clean Architecture layer inversion, and forbidden imports.
- **Coverage Gate**: Evaluates `pytest-cov` or project coverage wrapper against configured threshold.
- **Security Policy**: Evaluates `bandit` or `pip-audit` for scheduled and release profiles.

### Step 4: Result Assembly and Contract Emission

Assemble the result document matching [provider-result.schema.json](../quality_check/resources/schemas/provider-result.schema.json):

- `provider_id`: `"python-core"` (or matching invocation identifier)
- `contract_version`: `1`
- `profile`: `<profile>`
- `repository_sha`: Verified commit SHA matching invocation
- `status`: Aggregated provider status (`FAIL` if any check failed, `BLOCKED` if any check blocked, else `PASS`)
- `started_head` and `finished_head`: Git SHA recorded before and after execution
- `checks`, `coverage`, `evidence`, `blockers`, `warnings`

Return the result document to the orchestrator.

## References & Resources

- [Python Capability Contract](references/python-capability-contract.md): Format and rules for `.agents/quality/python-quality.json`.
- [Python Architecture Governance](references/python-architecture-governance.md): Architecture policies via `import-linter` and Clean Architecture boundaries.
- [Python Tool Mapping](references/python-tool-mapping.md): Mapping mobile quality concepts to Python ecosystem equivalents.
- [Capability Schema](resources/schemas/python-quality.schema.json): Machine-readable JSON Schema for Python capability manifests.
- [Capability Validator](resources/scripts/validate_python_quality.py): Script and CLI validator for Python capability files.
- [Valid Fixture](resources/fixtures/valid_python_quality.json): Reference valid capability configuration fixture.
