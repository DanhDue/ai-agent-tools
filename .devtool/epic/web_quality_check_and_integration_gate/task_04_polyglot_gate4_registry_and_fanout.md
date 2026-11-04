---
id: "task_04_polyglot_gate4_registry_and_fanout"
status: "todo"
priority: "high"
assignee: null
epic: "web-quality-check-and-integration-gate"
dueDate: null
created: "2026-11-04T22:52:00Z"
modified: "2026-11-04T22:52:00Z"
completedAt: null
labels: ["orchestration", "quality-gate", "polyglot"]
order: "a4"
---

# Task 04: Polyglot Gate 4 Registry and Multi-Provider Fan-Out

Epic: [web_quality_check_and_integration_gate](web_quality_check_and_integration_gate.en.md)

## Requirement Analysis

Extend project quality templates and verification tooling to support multi-provider polyglot registries in `.agents/quality/check_quality.json`. Enable concurrent fan-out and deterministic aggregation across disparate stacks: `rust-core` + `learning-web` for `D3Nexus`, and `python-core` + `preview-ui` for `lyrics-sync`.

## Files

Allowed files:
- `skills/setup_quality_check/resources/templates/polyglot-check-quality.template.json` (new)
- `skills/setup_quality_check/resources/templates/web-quality.template.json` (new)
- `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`
- `skills/quality_check/resources/scripts/verify_polyglot_registry.py` (new)
- `tests/test_polyglot_gate4.py` (new)

Read-only context:
- `skills/quality_check/SKILL.md` (Gate 4 orchestrator)
- `skills/quality_check/resources/scripts/validate_quality_contract.py` (registry validator)

## Design Rationale

Modern systems are increasingly polyglot: a single repository may house a Rust/WASM core alongside an Astro frontend (`D3Nexus`), or a Python worker service alongside a Vanilla JavaScript player (`lyrics-sync`). Gate 4 must not be constrained to a single provider. It must concurrently dispatch checks across all registered providers, aggregate verdicts under `FAIL > BLOCKED > PASS`, and report a unified executive summary.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `polyglot-check-quality.template.json`, `verify_polyglot_registry.py`.
- **Downstream Callers**: All polyglot repositories consuming `quality_check`.
- **Cross-Platform Bridges**: Multi-process fan-out.
- **Target Test Coverage Threshold**: $\ge 85\%$ for `verify_polyglot_registry.py`.

### BDD SCENARIOS

Covers: [WQG-AR-01]

#### Scenario: [WQG-AR-01] [Tier C - Integration] Concurrent multi-provider fan-out in Gate 4
Given a polyglot repository (`D3Nexus`) with providers `rust-core` and `learning-web`
When Gate 4 `quality_check` executes profile `epic`
Then both providers execute concurrently without interfering with each other's outputs
And Gate 4 aggregates the final verdict based on `FAIL > BLOCKED > PASS` priority.

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest tests/test_polyglot_gate4.py::test_polyglot_fanout` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest tests/test_polyglot_gate4.py::test_polyglot_fanout` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check tests/test_polyglot_gate4.py skills/quality_check` | exit 0 | — |
| V4 | TIER-B | `mypy skills/quality_check/resources/scripts/verify_polyglot_registry.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest tests/test_polyglot_gate4.py -k "test_WQG_AR_01" --junitxml=build/test-results/task_04.xml` | exit 0; results build/test-results/task_04.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Aggregation precedence: `FAIL` trumps `BLOCKED`, which trumps `PASS`.
- Output format: Unified executive markdown report listing every provider's status, executed checks, and SHA binding.
- Manifest schema version: `1` with multiple objects in the `providers` array.
- Scaffolder integration: `scaffold_quality_manifest.py` registers `web` in `PLATFORM_CONFIGS` (mapping to `web-quality.json` and `web-quality.template.json`) and detects web projects via `package.json`, `astro.config.*`, or `playwright.config.*`.
- Consumer adoption handoffs: define exact check_quality.json configurations and watchdog attachment steps for `D3Nexus` (`rust-core` + `learning-web`) and `lyrics-sync` (`python-core` + `preview-ui`).

## Definition of Done

- `polyglot-check-quality.template.json` provides working configuration models for multi-provider repos. (V2)
- Multi-provider concurrency and verdict reduction verified with ruff and mypy. (V3, V4)
- Scenario [WQG-AR-01] fully tested and passing. (V5)
- Clean git status with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by: [Task 01](task_01_web_quality_check_skill_and_contract.md).

## References & Rollback

- Reference: `skills/quality_check/SKILL.md`.
- Rollback: Revert `polyglot-check-quality.template.json` and verification test.
