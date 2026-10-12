---
id: "task_3_run_acceptance_and_release"
status: "done"
priority: "high"
assignee: null
epic: "python_quality_provider_and_onboarding"
dueDate: null
created: "2026-10-12T13:20:00Z"
modified: "2026-10-12T06:41:51Z"
completedAt: "2026-10-12T06:41:51Z"
labels: ["release", "acceptance", "d3nexus", "v1.7.0"]
order: "a3"
---

# Task 3: Run Acceptance Verification and Release d3nexus v1.7.0

Epic: [python_quality_provider_and_onboarding](../epic/python_quality_provider_and_onboarding/python_quality_provider_and_onboarding.en.md)

## Requirement Analysis

Verify end-to-end integration and publish the release bump for `d3nexus`:
1. **Acceptance Testing**:
   - Extend `skills/quality_check/resources/scripts/test_quality_provider_acceptance.py` to include Python provider end-to-end execution, schema validation, and exit code handling.
2. **Plugin Registration & Metadata**:
   - Register `python-quality-check` in `plugin.json` skills registry with accurate metadata.
   - Bump `plugin.json` version from `1.6.0` to `1.7.0`.
3. **Changelog & Documentation**:
   - Update `CHANGELOG.md` with release notes detailing Python quality provider support, scaffolding auto-detection, and test coverage enhancements.
4. **Full Workspace Verification**:
   - Execute `./scripts/verify.sh` in `ai-agent-tools` and ensure 100% green status across all 13 verification suites.

## Relevant Files & Context Pointers

- Target Test: `skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`
- Target Manifest: `plugin.json`
- Target Changelog: `CHANGELOG.md`
- Verification Suite: `./scripts/verify.sh`

## Design Rationale

Comprehensive integration testing ensures that `quality_check` can orchestrate `python-quality-check` seamlessly alongside other platform providers without regression, satisfying Gate 4 quality requirements.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `plugin.json`: Version bump and skill addition.
  - `skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`: Python provider test case.
  - `CHANGELOG.md`: Release notes.
- **Downstream Callers**: All plugin consumers accessing `d3nexus` capabilities.
- **Target Test Coverage Threshold**: 100% acceptance test pass rate.

### BDD Scenarios

```gherkin
Scenario: [Tier C - Acceptance] Execute end-to-end quality check against Python workspace
  Given a mock workspace configured with valid check_quality.json and python-quality.json
  When test_quality_provider_acceptance.py runs against the Python fixture
  Then execution succeeds with exit code 0
  And provider-result.json is validated and matches the schema

Scenario: [Tier B - Metadata] Validate plugin metadata and version bump
  Given plugin.json version 1.7.0
  When verify.sh validates plugin manifests and skills registry
  Then python-quality-check is verified as present and valid
```

## Test & Verification Checklist

- [x] **RED**: Add Python scenario to `test_quality_provider_acceptance.py` asserting full execution.
- [x] **GREEN**: Register skill and bump version to `1.7.0` in `plugin.json`. Update `CHANGELOG.md`.
- [x] **Tier A Verification**: Run `python3 -B skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`.
- [x] **Tier B Verification**: Run `./scripts/verify.sh` and confirm all 13 suites pass cleanly.

## Definition of Done (DoD)

- Python provider integrated into acceptance test suite.
- `plugin.json` bumped to `1.7.0` and `CHANGELOG.md` updated.
- `./scripts/verify.sh` passes 100% (13/13 suites).
- All changes cleanly tracked and committed.

## Dependencies & Blockers

- Blocked by: [Task 1](task_1_build_python_quality_provider.md), [Task 2](task_2_extend_scaffolding_skill.md).
- Blocks: [Task 4](task_4_onboard_lyrics_sync.md).

## References & Rollback

- Reference: [Acceptance Testing Guidelines](../epic/python_quality_provider_and_onboarding/python_quality_provider_and_onboarding.en.md).
- Rollback: Revert `plugin.json`, `CHANGELOG.md`, and test file updates.
