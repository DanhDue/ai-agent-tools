---
id: "task_5_skill_definition_and_harness_integration"
status: "todo"
priority: "high"
assignee: null
epic: "setup_shared_contracts"
dueDate: null
created: "2026-10-30T05:35:00Z"
modified: "2026-10-30T05:35:00Z"
completedAt: null
labels: ["skill", "docs", "harness", "integration"]
order: "a5"
---

# Task 5: Skill Definition and Verify Harness Integration

Epic: [setup_shared_contracts](setup_shared_contracts.en.md)

## Requirement Analysis

Create the skill definition `skills/setup-shared-contracts/SKILL.md` and wire the test suite into the repository verification script `scripts/verify.sh`.
1. Author `skills/setup-shared-contracts/SKILL.md`:
   - YAML frontmatter strictly containing only `name: setup-shared-contracts` and `description`.
   - Comprehensive instructions guiding AI agents and human engineers on when and how to establish shared contracts.
   - Clear workflows for Hub Mode (`init-hub`), Satellite Mode (`link-satellite`), and Health Auditing (`verify`).
   - Grounded examples for multi-repo topologies (e.g. `D3Nexus` hub with `lyrics-sync` and `nexus` satellites).
2. Wire `skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` into `scripts/verify.sh` in Section 14 (`== 14. Shared contracts CLI engine is enforced ==`) so that repository validation exercises the new skill suite on every commit.
3. Complete final end-to-end integration test `test_ssc_hp_03` verifying full end-to-end lifecycle pass (`[SSC-HP-03]`).

## Files

Allowed files:
- `skills/setup-shared-contracts/SKILL.md` (new)
- `scripts/verify.sh`
- `skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` (new)

Read-only context:
- `skills/setup-shared-contracts/resources/scripts/setup_contracts.py`
- `.devtool/epic/setup_shared_contracts/setup_shared_contracts.en.md` — HLD specifications

## Design Rationale

- Frontmatter adheres strictly to the two-key contract (`name` + `description`) required by Claude Code and Antigravity.
- `scripts/verify.sh` integration prevents regressions across all future plugin releases.
- Applicable skills: `d3nexus:writing-skills`, `d3nexus:verification-before-completion`, `d3nexus:test-driven-development`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `skills/setup-shared-contracts/SKILL.md`, `scripts/verify.sh`, and `test_setup_contracts.py`.
- **Downstream Callers**: All AI agents discovering the new skill and CI/CD running `scripts/verify.sh`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% full suite integration coverage and `scripts/verify.sh` green gate.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SSC-HP-03

```gherkin
Scenario: [SSC-HP-03] [Tier C - Integration] Comprehensive Health Verification Pass
  Given a validly initialized Hub repository and linked Satellite repository
  When the engineer invokes setup_contracts.py verify in either repository
  Then the engine auto-detects the repository mode
  And validates the physical files, symlink targets, and local rule existence
  And outputs a green PASS report with exit code 0
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_hp_03` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_hp_03` | exit 0; contains "OK" | — |
| V3 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/setup-shared-contracts/SKILL.md` | exit 0; contains "0 findings" | — |
| V4 | TIER-B | `ruff check skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0 | — |
| V6 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
| V7 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/setup-shared-contracts.xml skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0; results build/test-results/setup-shared-contracts.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `scripts/verify.sh` reports any failure across the 14 verification sections.

## Decisions Already Made

- Skill frontmatter has exactly `name` and `description` keys.
- `scripts/verify.sh` Section 14 (`== 14. Shared contracts CLI engine is enforced ==`) executes `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py`.

## Definition of Done

- `skills/setup-shared-contracts/SKILL.md` is complete with frontmatter and documentation (V3).
- End-to-end integration test `test_ssc_hp_03` passes (V2).
- Linting and typing checks pass cleanly (V4, V5).
- `scripts/verify.sh` runs the new test suite and outputs "PASS — safe to publish" (V6).
- JUnit report produced and integration tests pass (V7).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 4](task_4_cli_engine_verification.md) — requires all CLI subcommands to be implemented.

## References & Rollback

- Spec: `.devtool/epic/setup_shared_contracts/2026-10-30-setup-shared-contracts-design.en.md`
- HLD: `.devtool/epic/setup_shared_contracts/setup_shared_contracts.en.md`
- Rollback: Reverting `SKILL.md` and edits to `scripts/verify.sh`.
