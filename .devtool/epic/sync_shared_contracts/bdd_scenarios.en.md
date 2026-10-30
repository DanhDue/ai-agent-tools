# Sync Shared Contracts BDD Scenarios

## Table of Contents

- [Dimension 1: Happy Paths](#dimension-1-happy-paths)
- [Dimension 2: Edge Cases and Boundaries](#dimension-2-edge-cases-and-boundaries)
- [Dimension 3: State Transitions](#dimension-3-state-transitions)
- [Dimension 4: Async and Multi-Repo Concurrency](#dimension-4-async-and-multi-repo-concurrency)
- [Dimension 5: Failures and Storage Resilience](#dimension-5-failures-and-storage-resilience)

## Dimension 1: Happy Paths

```gherkin
Scenario: [SYC-HP-01] [Tier C - Integration] Structured Contract Parsing and Requirements Brief Rendering
  Given an initialized Hub repository with domain lyrics-sync containing api_contract.md, architecture_and_flow.md, and gaps_and_rfcs.md
  When the engineer invokes sync_contracts.py brief --domain lyrics-sync
  Then the parser extracts version "1.0.0", the 4 canonical endpoints, authentication headers, JSON payload keys, 7 pipeline steps, and RFC-001
  And the output Markdown report contains sections for Topology Metadata, API and Schema Requirements, Architecture Invariants, Actionable RFCs, and Lifecycle Execution Rules
  And the command exits with code 0

Scenario: [SYC-HP-02] [Tier C - Integration] End-to-End Satellite Synchronization and Strict Check Pass
  Given a Satellite repository linked via relative symlink shared-contracts to ../Hub/shared-contracts/lyrics-sync
  When the engineer invokes sync_contracts.py ack followed by sync_contracts.py check --strict
  Then the file .agents/contract_sync.json is created in the Satellite repository with mode "satellite" and domain "lyrics-sync"
  And the recorded sha256 hashes match all 3 canonical files in the Hub
  And sync_contracts.py check --strict outputs status "IN_SYNC" and exits with code 0

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

Scenario: [SYC-EC-03] [Tier A - Unit] Graceful Fallback When Hub Directory Has No Git History
  Given a Hub directory that was created on disk without a .git repository
  When the engineer invokes sync_contracts.py check or brief
  Then the engine skips git rev-parse and git log without raising a subprocess error
  And computes drift status accurately using sha256 file hashes and contract Version metadata
```

## Dimension 3: State Transitions

```gherkin
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

Scenario: [SYC-FR-02] [Tier A - Unit] Refusing Execution on Dangling Symlink or Missing Canonical Files
  Given a Satellite repository whose shared-contracts symlink points to a non-existent Hub path or a domain missing architecture_and_flow.md
  When the engineer invokes sync_contracts.py check
  Then the command aborts with exit code 1
  And prints a diagnostic message naming the broken target or missing canonical file

Scenario: [SYC-FR-03] [Tier A - Unit] Resilience Against Corrupted Watermark JSON File
  Given a target repository where .agents/contract_sync.json contains truncated invalid JSON "{corrupt"
  When the engineer runs sync_contracts.py check followed by sync_contracts.py ack
  Then sync_contracts.py check logs a warning about invalid JSON and falls back to "INITIAL_SYNC" without crashing
  And sync_contracts.py ack cleanly overwrites .agents/contract_sync.json with valid schema_version 1 JSON
```

