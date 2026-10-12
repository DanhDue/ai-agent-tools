---
id: "task_2_extend_scaffolding_skill"
status: "done"
priority: "high"
assignee: null
epic: "python_quality_provider_and_onboarding"
dueDate: null
created: "2026-10-12T13:20:00Z"
modified: "2026-10-12T06:37:07Z"
completedAt: "2026-10-12T06:37:07Z"
labels: ["python", "scaffolding", "setup_quality_check"]
order: "a2"
---

# Task 2: Extend Scaffolding Skill for Python

Epic: [python_quality_provider_and_onboarding](python_quality_provider_and_onboarding.en.md)

## Requirement Analysis

Extend the automated onboarding engine `setup_quality_check` (`scaffold_quality_manifest.py`) to recognize and scaffold Python workspaces:
1. **Repository Inspection**:
   - Detects Python through root markers: `pyproject.toml`, `uv.lock`, `requirements.txt`, `setup.py`, or `Pipfile`.
   - Supports polyglot repositories where Python coexists with other platform markers.
2. **Deterministic Manifest Output**:
   - Registers `python-core` mapped to `d3nexus:python-quality-check` in `.agents/quality/check_quality.json`.
   - Generates `.agents/quality/python-quality.json` pre-populated with standard capabilities (`format`, `lint`, `type_check`, `boundaries`, `test`, `coverage`).
3. **Safety & Flags**:
   - Preserves overwrite safety (fails safely unless `--force` is passed).
   - Supports `--dry-run` and `--platform python` overrides.

## Relevant Files & Context Pointers

- Target Script: `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`
- Target Skill: `skills/setup_quality_check/SKILL.md`
- Target Test: `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py`

## Design Rationale

Adding Python heuristics to `scaffold_quality_manifest.py` allows engineers and AI agents to bootstrap Python quality contracts on any codebase with a single command.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`: `detect_platforms`, `PLATFORM_CONFIGS`.
  - `skills/setup_quality_check/SKILL.md`: Documentation updates.
  - `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py`: Unit test assertions.
- **Downstream Callers**: All AI agents and engineers setting up quality gates on Python projects.
- **Target Test Coverage Threshold**: 100% path coverage for detection heuristics.

### BDD Scenarios

```gherkin
Scenario: [Tier A - Unit] Auto-detect Python repository via pyproject.toml
  Given a mock directory containing pyproject.toml
  When scaffold_quality_manifest.py executes
  Then check_quality.json declares provider python-core
  And python-quality.json contains valid format, lint, and test capabilities

Scenario: [Tier A - Unit] Auto-detect Python repository via requirements.txt
  Given a mock directory containing requirements.txt
  When scaffold_quality_manifest.py executes
  Then check_quality.json declares provider python-core
  And python-quality.json is generated successfully
```

## Test & Verification Checklist

- [x] **RED**: Add tests in `test_scaffold_quality_manifest.py` for Python markers and polyglot Python repositories. Confirm tests fail.
- [x] **GREEN**: Implement Python detection in `scaffold_quality_manifest.py` and update `SKILL.md`.
- [x] **REFACTOR**: Ensure generated Python JSON files validate cleanly against `python-quality.schema.json`.
- [x] **Tier A Verification**: Run `python3 -B skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py` and confirm 100% pass.
- [x] **Tier B Verification**: Verify skill documentation and relative links.

## Definition of Done (DoD)

- `scaffold_quality_manifest.py` detects Python projects and generates valid manifests.
- Multi-platform test suite passes 100%.
- Documentation reflects Python platform support.

## Dependencies & Blockers

- Blocked by: [Task 1](task_1_build_python_quality_provider.md).
- Blocks: [Task 3](task_3_run_acceptance_and_release.md), [Task 4](task_4_onboard_lyrics_sync.md).

## References & Rollback

- Reference: [Scaffolding Engine in setup_quality_check](../skills/setup_quality_check/SKILL.md).
- Rollback: Revert modifications to `scaffold_quality_manifest.py`.
