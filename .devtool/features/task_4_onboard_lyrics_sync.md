---
id: "task_4_onboard_lyrics_sync"
status: "done"
priority: "high"
assignee: null
epic: "python_quality_provider_and_onboarding"
dueDate: null
created: "2026-10-12T13:20:00Z"
modified: "2026-10-12T07:02:19Z"
completedAt: "2026-10-12T07:02:19Z"
labels: ["onboarding", "lyrics-sync", "ruff", "baseline"]
order: "a4"
---

# Task 4: Onboard and Certify lyrics-sync Quality Baseline

Epic: [python_quality_provider_and_onboarding](../epic/python_quality_provider_and_onboarding/python_quality_provider_and_onboarding.en.md)

## Requirement Analysis

Onboard the target consumer repository `/Users/danhdueexoictif/AllProjects/lyrics-sync` into the new Python quality framework and certify a 100% green baseline:
1. **Scaffold Manifests**:
   - Run the updated `scaffold_quality_manifest.py` against `/Users/danhdueexoictif/AllProjects/lyrics-sync`.
   - Verify creation of `.agents/quality/check_quality.json` and `.agents/quality/python-quality.json`.
2. **Align Capabilities to Ground Truth Tooling**:
   - Configure `python-quality.json` commands using `uv`:
     - `format`: `["uv", "run", "ruff", "format", "--check", "."]`
     - `lint`: `["uv", "run", "ruff", "check", "."]`
     - `type_check`: `["uv", "run", "mypy", "--strict", "src"]`
     - `boundaries`: `["uv", "run", "lint-imports"]`
     - `test`: `["uv", "run", "pytest", "-m", "not slow and not acceptance and not live_llm"]`
     - `coverage`: `["uv", "run", "pytest", "--cov=src", "--cov-report=json:coverage.json"]`
     - `schema`: `["uv", "run", "python", "-m", "lyrics_sync.model", "--check-schema"]`
     - `acceptance`: `["./scripts/run_e2e_acceptance.sh"]`
3. **Remediate Existing Lint Failures**:
   - Resolve all 44 existing Ruff lint errors across the test suites and source modules.
4. **Certify Baseline**:
   - Execute all verification commands and manifest validation.
   - Confirm 100% green status across formatting, linting, typing, boundaries, and testing.
   - Commit changes to `lyrics-sync` using bracketed commit format without trailers.

## Relevant Files & Context Pointers

- Target Consumer Repo: `/Users/danhdueexoictif/AllProjects/lyrics-sync`
- Target Manifests:
  - `/Users/danhdueexoictif/AllProjects/lyrics-sync/.agents/quality/check_quality.json`
  - `/Users/danhdueexoictif/AllProjects/lyrics-sync/.agents/quality/python-quality.json`
- Python Configuration: `/Users/danhdueexoictif/AllProjects/lyrics-sync/pyproject.toml`

## Design Rationale

Certifying `lyrics-sync` as the reference consumer validates that the Python quality provider operates accurately under real-world conditions with actual dependencies, linters, and type checkers.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `lyrics-sync/.agents/quality/`: Manifest configuration files.
  - `lyrics-sync/tests/`: Lint fixes for 44 Ruff issues.
- **Downstream Callers**: CI/CD pipelines and local development workflows in `lyrics-sync`.
- **Target Test Coverage Threshold**: 100% clean check for all configured capabilities.

### BDD Scenarios

```gherkin
Scenario: [Tier C - Acceptance] Scaffold lyrics-sync quality configuration
  Given the lyrics-sync repository
  When scaffold_quality_manifest.py runs with target lyrics-sync
  Then .agents/quality/check_quality.json and python-quality.json are generated

Scenario: [Tier A - Unit] Verify lyrics-sync passes all quality gates
  Given remediated Ruff lint errors and configured quality manifests
  When all tier checks (ruff, mypy, lint-imports, pytest) execute in lyrics-sync
  Then all commands exit with code 0
  And validate_python_quality.py confirms manifest compliance
```

## Test & Verification Checklist

- [x] **RED**: Run `uv run ruff check .` in `lyrics-sync` confirming 44 errors.
- [x] **GREEN**: Scaffold quality manifests, configure capabilities, and remediate all 44 Ruff lint errors.
- [x] **REFACTOR**: Ensure all imports and code styles in `lyrics-sync` comply with guidelines.
- [x] **Tier A Verification**: Execute `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy --strict src`, `uv run lint-imports`, and `uv run pytest -m "not slow and not acceptance and not live_llm"`.
- [x] **Tier B Verification**: Execute `validate_python_quality.py` on `lyrics-sync/.agents/quality/python-quality.json`.

## Definition of Done (DoD)

- `.agents/quality/` fully initialized and configured in `lyrics-sync`.
- All 44 Ruff errors remediated.
- 100% green verification baseline confirmed.
- Committed locally in `lyrics-sync` with standard bracketed commit message.

## Dependencies & Blockers

- Blocked by: [Task 1](task_1_build_python_quality_provider.md), [Task 2](task_2_extend_scaffolding_skill.md), [Task 3](task_3_run_acceptance_and_release.md).
- Blocks: Epic completion.

## References & Rollback

- Reference: [Scaffolding engine](../skills/setup_quality_check/SKILL.md).
- Rollback: `git checkout` modified files in `lyrics-sync`.
