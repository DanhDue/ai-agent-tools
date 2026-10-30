# Sync Shared Contracts BDD Scenarios

## Table of Contents

- [Dimension 1: Happy Paths](#dimension-1-happy-paths)
- [Dimension 2: Edge Cases and Boundaries](#dimension-2-edge-cases-and-boundaries)
- [Dimension 3: State Transitions](#dimension-3-state-transitions)
- [Dimension 4: Async and Multi-Repo Concurrency](#dimension-4-async-and-multi-repo-concurrency)
- [Dimension 5: Failures and Storage Resilience](#dimension-5-failures-and-storage-resilience)

## Dimension 1: Happy Paths

```gherkin
Scenario: [SYC-HP-01] [Tier C - Integration] Dual-Format Contract Parsing and Requirements Brief Rendering
  Given an initialized Hub repository with domain lyrics-sync containing canonical table contracts or live narrative contracts (HTML comment Version, Method/Path bullets, and GAP-XX sections with OPEN/PROPOSED/ACCEPTED statuses)
  When the engineer invokes sync_contracts.py brief --domain lyrics-sync
  Then the parser extracts the contract version, all declared endpoints, authentication headers, JSON payload keys, pipeline steps, and normalized RFC/GAP entries
  And the output Markdown report contains sections for Topology Metadata (including snapshot_id), API and Schema Requirements, Architecture Invariants, Actionable RFCs, and Lifecycle Execution Rules
  And the command exits with code 0

Scenario: [SYC-HP-02] [Tier C - Integration] End-to-End Satellite and Nested Worktree Synchronization Pass
  Given a Satellite repository linked via relative symlink shared-contracts to ../Hub/shared-contracts/lyrics-sync and a nested git worktree at .worktrees/sync_epic
  When the engineer invokes sync_contracts.py ack followed by sync_contracts.py check --strict from either the Satellite root or .worktrees/sync_epic
  Then the relative symlink shared-contracts resolves cleanly to the Hub domain without modifying the tracked symlink target
  And the file .agents/contract_sync.json is written in the active checkout with mode "satellite", domain "lyrics-sync", snapshot_id, and baseline_snapshot
  And sync_contracts.py check --strict outputs status "IN_SYNC" when no pending_rfcs remain and exits with code 0

Scenario: [SYC-HP-03] [Tier C - Integration] Skill Definition and Release Verify Harness Execution
  Given the completed sync-shared-contracts skill directory and scripts/verify.sh registration
  When the engineer runs the verification suite for sync-shared-contracts
  Then skills/sync-shared-contracts/SKILL.md passes frontmatter and link validation
  And all unit and integration tests in test_sync_contracts.py pass with exit code 0
```

## Dimension 2: Edge Cases and Boundaries

```gherkin
Scenario: [SYC-EC-01] [Tier A - Unit] Initial Sync Detection When Watermark File Is Absent
  Given a valid Satellite repository where .agents/contract_sync.json does not exist
  When the engineer invokes sync_contracts.py check --json
  Then the JSON report identifies the domain status as "INITIAL_SYNC"
  And lists all 3 canonical contract files as unsynced baseline deltas
  And the command exits with code 0 when --strict is omitted and code 1 when --strict is provided

Scenario: [SYC-EC-02] [Tier A - Unit] Heuristic Codebase Scanner Matches Parameterized Routes and CamelCase DTO Fields
  Given a target repository containing source file src/worker_client.ts with route "/api/v1/lyrics-sync/tasks" and "/progress" and field "leaseDurationMs"
  When the heuristic scanner evaluates endpoints "/api/v1/lyrics-sync/tasks/{id}/progress" and "/api/v1/lyrics-sync/status" and payload key "lease_duration_ms"
  Then endpoint "/api/v1/lyrics-sync/tasks/{id}/progress" and key "lease_duration_ms" are classified as "FOUND_IN_CODE"
  And unimplemented endpoint "/api/v1/lyrics-sync/status" is classified as "MISSING_IN_CODE"

Scenario: [SYC-EC-03] [Tier A - Unit] Semantic Baseline Diffing When Hub Has No Git History or Field Types Change
  Given a Hub directory without a .git repository where a Satellite previously ran sync_contracts.py ack storing baseline_snapshot with payload_fields
  When an uncommitted edit in the Hub modifies api_contract.md by adding payload key "retry_after_ms", changing field "metrics.execution_time_ms" from integer to string, and changing a pipeline step
  And the engineer invokes sync_contracts.py check or brief
  Then the engine skips git rev-parse and git log without raising a subprocess error
  And compares the current contract against baseline_snapshot to surface "retry_after_ms", the modified field type "metrics.execution_time_ms: integer -> string", and the modified pipeline step as semantic deltas

Scenario: [SYC-EC-04] [Tier A - Unit] Worktree-Aware Relative Symlink Resolution Inside Nested Epic Worktree
  Given a Satellite repository whose root shared-contracts symlink points relatively to ../Hub/shared-contracts/lyrics-sync and a nested git worktree at .worktrees/sync_epic
  When resolve_topology is invoked with repo_root set to the nested worktree .worktrees/sync_epic
  Then the engine detects the primary repository root via the worktree .git metadata and resolves the relative symlink against the primary root
  And returns the valid Hub contract directory without altering the tracked symlink inside the worktree
```

## Dimension 3: State Transitions

```gherkin
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
```

## Dimension 4: Async and Multi-Repo Concurrency

```gherkin
Scenario: [SYC-AR-01] [Tier A - Unit] Atomic Watermark File Update Prevents Partial JSON Reads
  Given an existing .agents/contract_sync.json file in the target repository
  When sync_contracts.py ack writes updated synchronization metadata
  Then the engine writes to a temporary file in .agents/ and atomically replaces .agents/contract_sync.json
  And no leftover temporary files remain in .agents/ after completion

Scenario: [SYC-AR-02] [Tier A - Unit] Circular Symlink Loop Protection During Topology Resolution
  Given a repository where shared-contracts is part of a circular symbolic link chain exceeding 10 hops
  When the engineer invokes sync_contracts.py check
  Then symlink traversal halts deterministically at the 10-hop boundary
  And exits with code 1 and an error message reporting a symbolic link loop
```

## Dimension 5: Failures and Storage Resilience

```gherkin
Scenario: [SYC-FR-01] [Tier A - Unit] Refusing Execution When Shared Contracts Directory Is Missing
  Given a target repository that has no shared-contracts directory or symlink
  When the engineer invokes sync_contracts.py check, brief, or ack
  Then the command aborts with exit code 1
  And prints an error instructing the user to initialize or link contracts with setup_contracts.py

Scenario: [SYC-FR-02] [Tier A - Unit] Refusing Execution on Dangling Symlink, Missing Canonical Files, or Unsupported Contract Format
  Given a Satellite repository whose shared-contracts symlink points to a non-existent Hub path, lacks architecture_and_flow.md, or contains an api_contract.md with zero recognizable endpoints
  When the engineer invokes sync_contracts.py check
  Then the command aborts with exit code 1
  And prints a diagnostic message naming the broken target, missing canonical file, or "UNSUPPORTED_CONTRACT_FORMAT"

Scenario: [SYC-FR-03] [Tier A - Unit] Resilience Against Corrupted Watermark JSON File
  Given a target repository where .agents/contract_sync.json contains truncated invalid JSON "{corrupt"
  When the engineer runs sync_contracts.py check followed by sync_contracts.py ack
  Then sync_contracts.py check logs a warning about invalid JSON and falls back to "INITIAL_SYNC" without crashing
  And sync_contracts.py ack cleanly overwrites .agents/contract_sync.json with valid schema_version 1 JSON
```
