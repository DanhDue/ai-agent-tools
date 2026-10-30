---
id: "task_3_watermark_ack_and_brief_cli"
status: "todo"
priority: "high"
assignee: null
epic: "sync_shared_contracts"
dueDate: null
created: "2026-10-30T11:58:00Z"
modified: "2026-10-30T12:23:00Z"
completedAt: null
labels: ["contracts", "watermark", "cli"]
order: "a3"
---

# Task 3: Watermark Ack Command, Drift Detection, and Brief CLI Subcommands

Epic: [sync_shared_contracts](../epic/sync_shared_contracts/sync_shared_contracts.en.md)

## Requirement Analysis

Implement the snapshot-and-scope-bound `ack` subcommand, nested worktree synchronization verification, incremental drift detection (`IN_SYNC` vs `DRIFT_DETECTED`), multi-domain watermark preservation, atomic JSON writing, and corrupted watermark recovery in `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`.
1. **Snapshot- and Scope-Bound Watermark Ack Command (`[SYC-HP-02]`, `[SYC-ST-01]`, `[SYC-ST-02]`, `[SYC-ST-03]`, `[SYC-AR-01]`)**:
   - Compute SHA-256 hashes for `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md`, composite `snapshot_id`, Hub git commit SHA, and normalized `baseline_snapshot` (`endpoints`, `headers`, `payload_keys`, `payload_fields`, `pipeline_steps`, `rfcs`).
   - If `--snapshot <expected_id>` is passed and differs from the current `snapshot_id`, abort with exit code `1` (`SNAPSHOT_MISMATCH`) without modifying `.agents/contract_sync.json` (`[SYC-ST-03]`). Support Hub `task_01` snapshot refresh (`brief` / `check --json` refreshes `snapshot_id` after `task_01` edits canonical contracts so the final Hub task binds `ack --snapshot` to the refreshed `snapshot_id`) (`[SYC-ST-01]`).
   - Keep all newly discovered or previously unacknowledged active RFC/Gap items (both `ACTIONABLE_PENDING`: `OPEN`, `PROPOSED`, `DRAFT`, `IN_REVIEW` and `ACKNOWLEDGED_ACTIVE`: `ACCEPTED`, `APPROVED`, `IMPLEMENTED`) in `pending_rfcs` unless explicitly passed via `--rfc <ID>` (repeatable) or `--all-rfcs` (`[SYC-ST-02]`).
   - Write `.agents/contract_sync.json` atomically using a temporary file in `.agents/` and `os.replace()`, preserving existing entries for other domains (`[SYC-ST-02]`, `[SYC-AR-01]`).
   - Support running `ack` and `check --strict` from both the primary Satellite root and a nested `.worktrees/<epic_dir>` checkout (`[SYC-HP-02]`).
2. **Global vs Scoped Drift Detection (`[SYC-ST-01]`, `[SYC-ST-02]`)**:
   - After `ack` is run with no remaining `pending_rfcs`, global `check --strict` reports `IN_SYNC` and exits `0` (`[SYC-HP-02]`).
   - When `check --strict --rfc <ID>` is passed after a partial scope implementation, verify that `snapshot_id` matches and every specified `<ID>` is in `acknowledged_rfcs` (and not in `pending_rfcs`), exiting `0` (`scoped_in_sync: true`) while retaining unselected RFCs in `pending_rfcs` (`[SYC-ST-02]`).
   - When `api_contract.md`, `architecture_and_flow.md`, or `gaps_and_rfcs.md` changes in the Hub, or when `pending_rfcs` is non-empty during a global check (without `--rfc`), `check --strict` reports `DRIFT_DETECTED` and exits `1` (`[SYC-ST-01]`, `[SYC-ST-02]`).
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

- Binding `ack` to `--snapshot <snapshot_id>`, requiring explicit `--rfc <ID>` / `--all-rfcs` for RFC acknowledgement, and providing `check --strict --rfc <ID>` for scoped verification prevents partial implementations from silently marking unselected RFCs or concurrent upstream edits as synchronized.
- Atomic file replacement (`tempfile.NamedTemporaryFile` in `.agents/` + `os.replace`) guarantees concurrent readers never observe truncated JSON.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `sync_contracts.py` (`cmd_ack`, `cmd_brief`, `load_sync_state`, `save_sync_state_atomic`, `evaluate_domain_drift`) and `test_sync_contracts.py`.
- **Downstream Callers**: Task 4 (`SKILL.md` workflow and `scripts/verify.sh`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% coverage of `ack`, `--snapshot` validation, `--rfc` / `--all-rfcs` scope handling, worktree execution, and malformed JSON recovery.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SYC-HP-02, SYC-ST-01, SYC-ST-02, SYC-ST-03, SYC-AR-01, SYC-FR-03

```gherkin
Scenario: [SYC-HP-02] [Tier C - Integration] End-to-End Satellite and Nested Worktree Synchronization Pass
  Given a Satellite repository linked via relative symlink shared-contracts to ../Hub/shared-contracts/lyrics-sync and a nested git worktree at .worktrees/sync_epic
  When the engineer invokes sync_contracts.py ack followed by sync_contracts.py check --strict from either the Satellite root or .worktrees/sync_epic
  Then the relative symlink shared-contracts resolves cleanly to the Hub domain without modifying the tracked symlink target
  And the file .agents/contract_sync.json is written in the active checkout with mode "satellite", domain "lyrics-sync", snapshot_id, and baseline_snapshot
  And sync_contracts.py check --strict outputs status "IN_SYNC" when no pending_rfcs remain and exits with code 0

Scenario: [SYC-ST-01] [Tier C - Integration] Hub Snapshot Refresh and Incremental Drift Detection After Upstream Update
  Given a Hub or Satellite repository that previously ran sync_contracts.py ack --all-rfcs and is in state "IN_SYNC"
  When Hub task_01 updates api_contract.md to version "1.1.0" with a new endpoint POST /api/v1/lyrics-sync/tasks/{id}/cancel and logs RFC-002 in gaps_and_rfcs.md
  And the engineer runs sync_contracts.py check --strict before acknowledging, then refreshes the snapshot_id via sync_contracts.py brief and runs sync_contracts.py ack --snapshot <refreshed_snapshot_id> --all-rfcs
  Then sync_contracts.py check --strict before ack reports "DRIFT_DETECTED", surfaces the new cancel endpoint and RFC-002, and exits with code 1
  And sync_contracts.py ack --snapshot <refreshed_snapshot_id> --all-rfcs succeeds and subsequent check --strict exits with code 0

Scenario: [SYC-ST-02] [Tier C - Integration] Explicit Scope-Bound RFC Selection, Scoped Strict Check, and Multi-Domain Watermark Preservation
  Given a Hub repository with domains lyrics-sync and nexus where gaps_and_rfcs.md for nexus contains GAP-01 with status "OPEN" and GAP-03 with status "ACCEPTED"
  When the engineer invokes sync_contracts.py ack --domain nexus --rfc GAP-03, runs check --domain nexus --strict --rfc GAP-03 and global check --domain nexus --strict, and then invokes sync_contracts.py ack --domain nexus --rfc GAP-01
  Then after the first ack, .agents/contract_sync.json retains the existing "lyrics-sync" entry, places only "GAP-03" in acknowledged_rfcs, keeps "GAP-01" in pending_rfcs, scoped check --strict --rfc GAP-03 exits with code 0, and global check --strict exits with code 1
  And after the second ack with --rfc GAP-01, "GAP-01" moves to acknowledged_rfcs, pending_rfcs becomes empty, and global check --strict exits with code 0

Scenario: [SYC-ST-03] [Tier A - Unit] Snapshot Mismatch Rejection When Contract Changes Before Ack
  Given a target repository where sync_contracts.py brief recorded snapshot_id "sha256:stale"
  When a canonical contract file is modified on disk before sync_contracts.py ack --snapshot sha256:stale is executed
  Then sync_contracts.py ack aborts with exit code 1 and prints "SNAPSHOT_MISMATCH" without modifying .agents/contract_sync.json

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
| V5 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_st_03` | exit 0; contains "OK" | — |
| V6 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ar_01` | exit 0; contains "OK" | — |
| V7 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_fr_03` | exit 0; contains "OK" | — |
| V8 | TIER-B | `ruff check skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V9 | TIER-B | `mypy --strict --follow-imports=silent skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V10 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_3.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0; results build/test-results/task_3.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `ack` writes any file inside `shared-contracts/` instead of `.agents/contract_sync.json`.

## Decisions Already Made

- Watermark state is persisted at `<repo_root>/.agents/contract_sync.json` with `schema_version: 1`, `mode`, and per-domain objects containing `snapshot_id`, `hub_commit_sha`, `contract_version`, `last_synced_at`, `file_hashes`, `acknowledged_rfcs`, `pending_rfcs`, `acknowledged_endpoints`, and `baseline_snapshot` (including `payload_fields` and `rfcs`).
- `ack --snapshot <id>` validates `snapshot_id` before writing and exits `1` (`SNAPSHOT_MISMATCH`) on mismatch.
- `ack` uses atomic file replacement (`os.replace`) inside `.agents/`.

## Definition of Done

- `sync_contracts.py ack` writes `.agents/contract_sync.json` atomically (including from inside `.worktrees/<epic_dir>`) and `check --strict` passes with `IN_SYNC` when `pending_rfcs` is empty (V2, V6).
- Hub `task_01` snapshot refresh and upstream contract drift detection pass, while mismatched `--snapshot` flags fail `ack` with exit code `1` (V3, V5).
- Unselected active RFCs remain in `pending_rfcs` until acknowledged via `--rfc <ID>`, scoped `check --strict --rfc <ID>` passes for completed subsets, and sibling domain entries are preserved (V4).
- Corrupted `.agents/contract_sync.json` files are handled gracefully by `check` and repaired by `ack` (V7).
- Ruff and Mypy strict checks pass (V8, V9).
- JUnit report is generated and all covered scenarios pass (V10).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 2](task_2_heuristic_scanner_and_check_engine.md) — requires worktree-aware topology resolution and heuristic scanner in `sync_contracts.py`.

## References & Rollback

- Spec: `.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md`
- HLD: `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md`
- Rollback: Revert Task 3 additions in `sync_contracts.py` and `test_sync_contracts.py`.
