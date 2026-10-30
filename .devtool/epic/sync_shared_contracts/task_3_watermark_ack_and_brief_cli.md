---
id: "task_3_watermark_ack_and_brief_cli"
status: "todo"
priority: "high"
assignee: null
epic: "sync_shared_contracts"
dueDate: null
created: "2026-10-30T11:58:00Z"
modified: "2026-10-30T11:58:00Z"
completedAt: null
labels: ["contracts", "watermark", "cli"]
order: "a3"
---

# Task 3: Watermark Ack Command, Drift Detection, and Brief CLI Subcommands

Epic: [sync_shared_contracts](../epic/sync_shared_contracts/sync_shared_contracts.en.md)

## Requirement Analysis

Implement the `ack` subcommand, incremental drift detection (`IN_SYNC` vs `DRIFT_DETECTED`), multi-domain watermark preservation, atomic JSON writing, and corrupted watermark recovery in `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`.
1. **Watermark Ack Command (`[SYC-HP-02]`, `[SYC-ST-02]`, `[SYC-AR-01]`)**:
   - Compute SHA-256 hashes for `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md`, query the Hub git commit SHA, and collect acknowledged endpoints and RFC IDs (including `--rfc <RFC-ID>` arguments).
   - Write `.agents/contract_sync.json` atomically using a temporary file in `.agents/` and `os.replace()`, preserving existing entries for other domains (`[SYC-ST-02]`, `[SYC-AR-01]`).
2. **Incremental Drift Detection (`[SYC-ST-01]`)**:
   - After `ack` is run, `check --strict` must report `IN_SYNC` and exit `0` (`[SYC-HP-02]`).
   - When `api_contract.md`, `architecture_and_flow.md`, or `gaps_and_rfcs.md` changes in the Hub, `check` must transition to `DRIFT_DETECTED`, surface modified files, new endpoints, and new RFCs, and exit `1` when `--strict` is passed (`[SYC-ST-01]`).
3. **Corrupted Watermark Recovery (`[SYC-FR-03]`)**:
   - If `.agents/contract_sync.json` contains malformed JSON, `check` logs a warning to stderr and falls back to `INITIAL_SYNC` without crashing, while `ack` overwrites it with valid `schema_version: 1` JSON.

## Files

Allowed files:
- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (new)
- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` (new)

Read-only context:
- `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` (new) — brief template from Task 1
- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — HLD specifications

## Design Rationale

- Atomic file replacement (`tempfile.NamedTemporaryFile` in `.agents/` + `os.replace`) guarantees concurrent readers never observe truncated JSON.
- Preserving sibling domain keys in `.agents/contract_sync.json` allows a multi-domain Hub or multi-service consumer to track each domain independently.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `sync_contracts.py` (`cmd_ack`, `cmd_brief`, `load_sync_state`, `save_sync_state_atomic`, `evaluate_domain_drift`) and `test_sync_contracts.py`.
- **Downstream Callers**: Task 4 (`SKILL.md` workflow and `scripts/verify.sh`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% coverage of `ack`, `brief --output`, drift transitions, and malformed JSON recovery.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SYC-HP-02, SYC-ST-01, SYC-ST-02, SYC-AR-01, SYC-FR-03

```gherkin
Scenario: [SYC-HP-02] [Tier C - Integration] End-to-End Satellite Synchronization and Strict Check Pass
  Given a Satellite repository linked via relative symlink shared-contracts to ../Hub/shared-contracts/lyrics-sync
  When the engineer invokes sync_contracts.py ack followed by sync_contracts.py check --strict
  Then the file .agents/contract_sync.json is created in the Satellite repository with mode "satellite" and domain "lyrics-sync"
  And the recorded sha256 hashes match all 3 canonical files in the Hub
  And sync_contracts.py check --strict outputs status "IN_SYNC" and exits with code 0

Scenario: [SYC-ST-01] [Tier C - Integration] Incremental Drift Detection After Upstream Hub Contract Update
  Given a Satellite repository that previously ran sync_contracts.py ack and is in state "IN_SYNC"
  When the Hub repository updates api_contract.md to version "1.1.0" with a new endpoint POST /api/v1/lyrics-sync/tasks/{id}/cancel and logs RFC-002 in gaps_and_rfcs.md
  And the engineer runs sync_contracts.py check --strict in the Satellite repository
  Then the status transitions from "IN_SYNC" to "DRIFT_DETECTED"
  And the delta report identifies api_contract.md and gaps_and_rfcs.md as modified, surfaces the new cancel endpoint as "MISSING_IN_CODE", and lists RFC-002
  And sync_contracts.py check --strict exits with code 1

Scenario: [SYC-ST-02] [Tier C - Integration] Multi-Domain Watermark Preservation and Explicit RFC Acknowledgement
  Given a Hub repository with domains lyrics-sync and nexus where lyrics-sync is already recorded in .agents/contract_sync.json
  When the engineer invokes sync_contracts.py ack --domain nexus --rfc RFC-005
  Then .agents/contract_sync.json retains the existing "lyrics-sync" entry unchanged
  And records the new "nexus" entry containing "RFC-005" in acknowledged_rfcs

Scenario: [SYC-AR-01] [Tier A - Unit] Atomic Watermark File Update Prevents Partial JSON Reads
  Given an existing .agents/contract_sync.json file in the target repository
  When sync_contracts.py ack writes updated synchronization metadata
  Then the engine writes to a temporary file in .agents/ and atomically replaces .agents/contract_sync.json
  And no leftover temporary files remain in .agents/ after completion

Scenario: [SYC-FR-03] [Tier A - Unit] Resilience Against Corrupted Watermark JSON File
  Given a target repository where .agents/contract_sync.json contains truncated invalid JSON "{corrupt"
  When the engineer runs sync_contracts.py check followed by sync_contracts.py ack
  Then sync_contracts.py check logs a warning about invalid JSON and falls back to "INITIAL_SYNC" without crashing
  And sync_contracts.py ack cleanly overwrites .agents/contract_sync.json with valid schema_version 1 JSON
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_hp_02` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_hp_02` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_st_01` | exit 0; contains "OK" | — |
| V4 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_st_02` | exit 0; contains "OK" | — |
| V5 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ar_01` | exit 0; contains "OK" | — |
| V6 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_fr_03` | exit 0; contains "OK" | — |
| V7 | TIER-B | `ruff check skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V8 | TIER-B | `mypy --strict --follow-imports=silent skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V9 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_3.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0; results build/test-results/task_3.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `ack` writes any file inside `shared-contracts/` instead of `.agents/contract_sync.json`.

## Decisions Already Made

- Watermark state is persisted at `<repo_root>/.agents/contract_sync.json` with `schema_version: 1`, `mode`, and per-domain objects containing `hub_commit_sha`, `contract_version`, `last_synced_at`, `file_hashes`, `acknowledged_rfcs`, and `acknowledged_endpoints`.
- `ack` uses atomic file replacement (`os.replace`) inside `.agents/`.

## Definition of Done

- `sync_contracts.py ack` writes `.agents/contract_sync.json` atomically and `check --strict` passes with `IN_SYNC` (V2, V5).
- Upstream contract edits transition status to `DRIFT_DETECTED` and fail `check --strict` with exit code `1` (V3).
- Multi-domain watermark entries and explicit `--rfc` flags are preserved and recorded (V4).
- Corrupted `.agents/contract_sync.json` files are handled gracefully by `check` and repaired by `ack` (V6).
- Ruff and Mypy strict checks pass (V7, V8).
- JUnit report is generated and all covered scenarios pass (V9).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 2](task_2_heuristic_scanner_and_check_engine.md) — requires topology resolution and heuristic scanner in `sync_contracts.py`.

## References & Rollback

- Spec: `.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md`
- HLD: `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md`
- Rollback: Revert Task 3 additions in `sync_contracts.py` and `test_sync_contracts.py`.
