---
id: "task_1_build_python_quality_provider"
status: "todo"
priority: "high"
assignee: null
epic: "python_quality_provider_and_onboarding"
dueDate: null
created: "2026-10-12T13:20:00Z"
modified: "2026-10-12T13:20:00Z"
completedAt: null
labels: ["python", "provider", "quality_check", "ruff", "mypy", "pytest"]
order: "a1"
---

# Task 1: Build Python Quality Provider

Epic: [python_quality_provider_and_onboarding](../epic/python_quality_provider_and_onboarding/python_quality_provider_and_onboarding.en.md)

## Requirement Analysis

Build the dedicated `d3nexus:python-quality-check` skill to provide platform-specific quality governance for Python codebases:
1. **Workspace & Tooling Support**: Compatible with modern Python package managers and tooling environments (`uv`, standard `python -m`, and `pytest`).
2. **Formatting & Static Analysis**: Enforces Ruff formatting compliance (`uv run ruff format --check .`) and static analysis (`uv run ruff check .`).
3. **Type Safety Governance**: Enforces strict Mypy type-checking (`uv run mypy --strict src`).
4. **Architecture Governance**: Enforces Clean Architecture modular layer boundaries via Import-Linter (`uv run lint-imports`).
5. **Unit Tests (Tier A)**: Executes isolated unit test suites via Pytest (`uv run pytest -m "not slow and not acceptance and not live_llm"`).
6. **Coverage Governance**: Enforces line coverage threshold (e.g. 80%) parsing JSON coverage reports emitted by `pytest-cov`.
7. **Schema & Acceptance (Tier C)**: Executes model schema validation and end-to-end integration acceptance scripts (`./scripts/run_e2e_acceptance.sh`).
8. **Contract Emission**: Emits standardized `provider-result.json` bound cryptographically to the verified commit SHA.

## Relevant Files & Context Pointers

- Template Reference: `/Users/danhdueexoictif/AllProjects/lyrics-sync/pyproject.toml`
- Target Skill: `skills/python-quality-check/SKILL.md`
- Target Schema: `skills/python-quality-check/resources/schemas/python-quality.schema.json`
- Target Validator: `skills/python-quality-check/resources/scripts/validate_python_quality.py`
- Target Test: `skills/python-quality-check/resources/scripts/test_validate_python_quality.py`
- Target Fixture: `skills/python-quality-check/resources/fixtures/valid_python_quality.json`

## Design Rationale

The Python provider reads `.agents/quality/python-quality.json`. All capabilities are declared strictly as non-empty arrays of strings:
- The provider skill validates `python-quality.json` schema before process invocation.
- Resolves candidate commit SHA and ensures clean working tree state.
- Executes declared capabilities for the requested profile (`pr` or `epic`).
- Evaluates code coverage metrics against configured thresholds.
- Emits atomic `provider-result.json` bound to the verified commit SHA.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/python-quality-check/SKILL.md`: Operational skill definition.
  - `skills/python-quality-check/resources/scripts/validate_python_quality.py`: Manifest validator.
  - `skills/python-quality-check/resources/schemas/python-quality.schema.json`: JSON schema.
- **Downstream Callers**:
  - `skills/quality_check/SKILL.md`: Invokes provider when `python-core` is declared in registry.
- **Cross-Platform Bridges**: Reads Python JSON coverage metrics.
- **Target Test Coverage Threshold**: 100% validator coverage.

### BDD Scenarios

```gherkin
Scenario: [Tier A - Unit] Validate valid Python quality capability manifest
  Given a python-quality.json declaring format, lint, type_check, boundaries, test, and coverage commands
  When validate_python_quality.py validates the configuration
  Then validation succeeds with exit code 0

Scenario: [Tier A - Unit] Reject Python manifest with duplicate capability identifiers
  Given a python-quality.json declaring duplicate "lint" capabilities
  When validate_python_quality.py validates the configuration
  Then validation fails with error "DUPLICATE_CAPABILITY_ID"

Scenario: [Tier A - Unit] Reject Python manifest with empty command array
  Given a python-quality.json with capability "format" configured as []
  When validate_python_quality.py validates the configuration
  Then validation fails with code "command_array_empty"
```

## Test & Verification Checklist

- [ ] **RED**: Create test suite `test_validate_python_quality.py` asserting validation of valid fixtures and rejection of duplicate capability IDs, missing profiles, and empty command arrays. Confirm tests fail.
- [ ] **GREEN**: Implement `python-quality.schema.json` and `validate_python_quality.py`. Implement `skills/python-quality-check/SKILL.md` operational instructions.
- [ ] **REFACTOR**: Align capability structure with existing providers (`valid_flutter_quality.json`, `valid_rust_quality.json`).
- [ ] **Tier A Verification**: Run `python3 -B skills/python-quality-check/resources/scripts/test_validate_python_quality.py` and confirm 100% pass.
- [ ] **Tier B Verification**: Verify frontmatter (`name: python-quality-check`, single-line description) and relative documentation links.

## Definition of Done (DoD)

- `skills/python-quality-check/` created with `SKILL.md`, schema, fixtures, scripts, and tests.
- Unit tests pass with 100% success.
- Manifest accurately models all `lyrics-sync` verification scripts.
- `git status` shows clean, targeted additions.

## Dependencies & Blockers

- Blocked by: None.
- Blocks: [Task 2](task_2_extend_scaffolding_skill.md), [Task 3](task_3_run_acceptance_and_release.md).

## References & Rollback

- Reference: [Python Tooling in lyrics-sync](../../../lyrics-sync/scripts/check.sh).
- Rollback: Remove `skills/python-quality-check/` directory.
