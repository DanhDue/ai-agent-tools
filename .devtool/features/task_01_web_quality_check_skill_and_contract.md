---
id: "task_01_web_quality_check_skill_and_contract"
status: "todo"
priority: "high"
assignee: null
epic: "web-quality-check-and-integration-gate"
dueDate: null
created: "2026-11-04T22:52:00Z"
modified: "2026-11-04T22:52:00Z"
completedAt: null
labels: ["quality", "web", "provider"]
order: "a1"
---

# Task 01: Web Quality Check Skill and Provider Contract

Epic: [web_quality_check_and_integration_gate](../epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md)

## Requirement Analysis

Author the `d3nexus:web-quality-check` provider skill implementing the canonical Provider Result Contract v1. The provider reads `.agents/quality/web-quality.json` from the repository root, executes configured capability commands without shell interpolation, validates outputs, and produces certified result documents bound to the commit SHA. Include the companion validator script `validate_web_quality.py`. The provider enforces a strict capability profile matrix: profile `pr` requires `type_check`, `lint`, and `test_unit`; profiles `epic` and `release` require `type_check`, `lint`, `test_unit`, AND mandatory `test_e2e` with watchdog attachment. `validate_web_quality.py` and the provider emit status `BLOCKED` if `test_e2e` or watchdog execution evidence (Playwright JUnit XML artifact `build/test-results/playwright.xml` and watchdog trace log) is missing during `epic` or `release` profile verification.

## Files

Allowed files:
- `skills/web-quality-check/SKILL.md` (new)
- `skills/web-quality-check/resources/scripts/validate_web_quality.py` (new)
- `tests/test_web_quality_provider.py` (new)

Read-only context:
- `skills/python-quality-check/SKILL.md` (canonical capability provider reference)
- `skills/quality_check/references/provider-result-contract.md` (schema definition for provider results)

## Design Rationale

The web quality assurance provider follows the identical architecture as `python-quality-check` and `rust-quality-check`:
1. It avoids hardcoded build commands and instead reads capabilities from `.agents/quality/web-quality.json`.
2. It supports argument placeholders: `{skills_dir}` for referencing sibling scripts and `{base_ref}` for Git diff baselines.
3. It emits deterministic verdicts: `FAIL` (nonzero exit in tests/linter), `BLOCKED` (missing configuration, invalid schema, or executable failure), and `PASS` (all capabilities exit 0).

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `skills/web-quality-check/SKILL.md`, `validate_web_quality.py` (`validate_manifest`, `run_capabilities`).
- **Downstream Callers**: `quality_check` orchestrator via registry invocation.
- **Cross-Platform Bridges**: None (Python CLI tool).
- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage for `validate_web_quality.py`.

### BDD SCENARIOS

Covers: [WQG-HP-01], [WQG-EC-01], [WQG-ST-01], [WQG-FR-02]

#### Scenario: [WQG-HP-01] [Tier C - Integration] Web quality provider certification on Astro TypeScript repository
Given a repository containing an Astro project with `.agents/quality/web-quality.json`
When Gate 4 invokes `d3nexus:web-quality-check` with profile `epic`
Then the provider executes `type_check`, `lint`, and `test_e2e` via Playwright headless
And produces a validated Provider Result Document with status `PASS` bound to the commit SHA.

#### Scenario: [WQG-EC-01] [Tier A - Unit] Web quality manifest with empty or optional capabilities
Given a repository where `.agents/quality/web-quality.json` configures only `type_check` and `test_unit`
When `web-quality-check` is invoked with profile `pr`
Then it resolves only the declared capabilities
And successfully certifies the repository without erroring on missing optional capabilities.

#### Scenario: [WQG-ST-01] [Tier A - Unit] Transition from BLOCKED to PASS upon fixing invalid configuration
Given a repository with a malformed `.agents/quality/web-quality.json`
When `validate_web_quality.py` evaluates the manifest
Then it reports status `BLOCKED` with validation findings
And when the developer corrects the JSON schema
Then the validator transitions to status `PASS`.

#### Scenario: [WQG-FR-02] [Tier A - Unit] Missing node_modules or binary execution blocker
Given an environment where `playwright` or `astro` binary is not found in `PATH`
When `web-quality-check` attempts to spawn the process
Then it catches the spawn failure and emits status `BLOCKED` with actionable remediation guidance.

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest tests/test_web_quality_provider.py::test_contract_validation` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest tests/test_web_quality_provider.py::test_contract_validation` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest tests/test_web_quality_provider.py -k "test_WQG_HP_01 or test_WQG_EC_01 or test_WQG_ST_01 or test_WQG_FR_02" --junitxml=build/test-results/task_01.xml` | exit 0; results build/test-results/task_01.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Manifest file path: `.agents/quality/web-quality.json`.
- Schema Version: `1`.
- Standard profiles supported: `pr`, `epic`, `release`, `scheduled`.
- Mandatory capabilities per profile: `pr` requires `type_check`, `lint`, and `test_unit`. Profiles `epic` and `release` strictly mandate `test_e2e` with Zero-Console-And-Layout-Defect watchdog execution. If `test_e2e` or watchdog evidence is absent during `epic`/`release`, the provider emits `BLOCKED`.
- Output structure: Standard Provider Result Contract v1 format matching `skills/quality_check/resources/schemas/provider-result.schema.json` with 13 required top-level keys: `provider_id`, `contract_version`, `profile`, `repository_sha`, `status`, `checks`, `coverage`, `evidence`, `started_head`, `finished_head`, `duration`, `blockers`, `warnings` (forbidden root `summary` omitted; additionalProperties false).

## Definition of Done

- `SKILL.md` documents provider execution, profile resolution, and capabilities. (V2)
- `validate_web_quality.py` passes ruff linting and mypy strict typing. (V3, V4)
- 100% BDD scenarios ([WQG-HP-01], [WQG-EC-01], [WQG-ST-01], [WQG-FR-02]) automated and passing. (V5)
- Clean git status with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by: None (First task in execution order).

## References & Rollback

- Reference: `skills/quality_check/references/provider-result-contract.md`.
- Rollback: Revert changes in `skills/web-quality-check/` and `tests/test_web_quality_provider.py`.
