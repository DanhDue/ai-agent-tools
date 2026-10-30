---
id: "task_4_skill_definition_and_verify_integration"
status: "todo"
priority: "high"
assignee: null
epic: "sync_shared_contracts"
dueDate: null
created: "2026-10-30T11:58:00Z"
modified: "2026-10-30T12:23:00Z"
completedAt: null
labels: ["skill", "docs", "harness", "integration"]
order: "a4"
---

# Task 4: Skill Definition, Lifecycle Bridge Instructions, and Verify Harness Integration

Epic: [sync_shared_contracts](sync_shared_contracts.en.md)

## Requirement Analysis

Create the skill definition `skills/sync-shared-contracts/SKILL.md` and wire the test suite into the repository verification script `scripts/verify.sh`.
1. Author `skills/sync-shared-contracts/SKILL.md`:
   - YAML frontmatter strictly containing only `name: sync-shared-contracts` and `description`.
   - Complete documentation of the 3-layer Hybrid Delta Engine (`check`, `brief`, `ack`), Dual-Format Markdown contract support (canonical tables and narrative `Method`/`Path` + `GAP-XX` sections), worktree-aware relative symlink resolution, and `.agents/contract_sync.json` (`snapshot_id`, `pending_rfcs`, `baseline_snapshot`) schema.
   - Detailed 5-step Orchestrated Bridge into `d3nexus:dev-lifecycle`:
     - Step 1: Preflight & Contract Delta Audit (`sync_contracts.py check` & `brief`).
     - Step 2: Scope Confirmation with developer (recording the target `snapshot_id` and selected RFC/GAP IDs).
     - Step 3: Stage 1 (`dev-brainstorming`) & Stage 2 (`dev-designer`) rules (Hub `task_01` canonical contract update vs Satellite `task_01` consumer DTO/adapter update, Satellite Git read-only symlink rule, and final task running `sync_contracts.py ack --snapshot <snapshot_id> [--rfc <ID> ...]`).
     - Step 4: Stage 3 (`dev-implementation`) TDD execution inside `.worktrees/<epic_dir>` (where `sync_contracts.py` automatically resolves the Satellite's relative `shared-contracts` symlink via the primary repository root while writing `.agents/contract_sync.json` in the worktree) and `sync_contracts.py check --strict` verification.
     - Step 5: Stage 4 (`finishing-a-development-branch`).
2. Wire `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` into `scripts/verify.sh` in Section 14 (`== 14. Shared contracts CLI engine is enforced ==`) alongside `test_setup_contracts.py`.
3. Add final integration test `test_syc_hp_03_skill_and_verify_harness` in `test_sync_contracts.py` verifying `SKILL.md` frontmatter, links, and end-to-end CLI execution (`[SYC-HP-03]`).

## Files

Allowed files:
- `skills/sync-shared-contracts/SKILL.md` (new)
- `scripts/verify.sh`
- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` (new)

Read-only context:
- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (new)
- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — HLD specifications
- `skills/setup-shared-contracts/SKILL.md` — companion skill reference

## Design Rationale

- Frontmatter adheres strictly to the two-key contract (`name` + `description`) required by Claude Code and Antigravity.
- Documenting the worktree-aware symlink resolution and `--snapshot` acknowledgement contract ensures agents running Stage 3 (`dev-implementation`) inside `.worktrees/<epic_dir>` never hit dangling link errors or overwrite unimplemented RFCs.
- Applicable skills: `d3nexus:writing-skills`, `d3nexus:verification-before-completion`, `d3nexus:test-driven-development`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `skills/sync-shared-contracts/SKILL.md`, `scripts/verify.sh`, and `test_sync_contracts.py`.
- **Downstream Callers**: All AI agents discovering `sync-shared-contracts` and CI/CD running `scripts/verify.sh`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% full suite integration coverage and `scripts/verify.sh` green gate.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SYC-HP-03

```gherkin
Scenario: [SYC-HP-03] [Tier C - Integration] Skill Definition and Release Verify Harness Execution
  Given the completed sync-shared-contracts skill directory and scripts/verify.sh registration
  When the engineer runs the verification suite for sync-shared-contracts
  Then skills/sync-shared-contracts/SKILL.md passes frontmatter and link validation
  And all unit and integration tests in test_sync_contracts.py pass with exit code 0
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_hp_03` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_hp_03` | exit 0; contains "OK" | — |
| V3 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/sync-shared-contracts/SKILL.md` | exit 0; contains "0 findings" | — |
| V4 | TIER-B | `ruff check skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V6 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
| V7 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/sync-shared-contracts.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0; results build/test-results/sync-shared-contracts.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `scripts/verify.sh` reports any failure across the verification sections.

## Decisions Already Made

- Skill frontmatter in `skills/sync-shared-contracts/SKILL.md` has exactly `name` and `description` keys.
- `scripts/verify.sh` Section 14 (`== 14. Shared contracts CLI engine is enforced ==`) executes both `test_setup_contracts.py` and `test_sync_contracts.py`.

## Definition of Done

- `skills/sync-shared-contracts/SKILL.md` is complete with valid frontmatter and 5-step `d3nexus:dev-lifecycle` bridge documentation (V3).
- End-to-end integration test `test_syc_hp_03` passes (V2).
- Linting and typing checks pass cleanly (V4, V5).
- `scripts/verify.sh` runs `test_sync_contracts.py` and outputs "PASS — safe to publish" (V6).
- JUnit report is produced and integration tests pass (V7).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 3](task_3_watermark_ack_and_brief_cli.md) — requires all `sync_contracts.py` subcommands (`check`, `brief`, `ack`) to be complete.

## References & Rollback

- Spec: `.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md`
- HLD: `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md`
- Rollback: Revert `skills/sync-shared-contracts/SKILL.md` and `scripts/verify.sh`.
