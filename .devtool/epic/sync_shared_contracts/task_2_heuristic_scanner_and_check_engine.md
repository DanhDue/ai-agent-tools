---
id: "task_2_heuristic_scanner_and_check_engine"
status: "todo"
priority: "high"
assignee: null
epic: "sync_shared_contracts"
dueDate: null
created: "2026-10-30T11:58:00Z"
modified: "2026-10-30T12:23:00Z"
completedAt: null
labels: ["contracts", "scanner", "cli"]
order: "a2"
---

# Task 2: Target Codebase Heuristic Scanner and Dual-Mode Check Engine

Epic: [sync_shared_contracts](sync_shared_contracts.en.md)

## Requirement Analysis

Implement the Target Codebase Heuristic Scanner, Worktree-Aware Dual-Mode topology resolver (Hub physical mode vs Satellite relative symlink mode), semantic baseline diffing (`baseline_snapshot`), circular symlink protection, and error validation in `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`.
1. **Heuristic Codebase Scanner (`[SYC-EC-02]`)**:
   - Recursively scan source files in `<repo_root>` while skipping `.git`, `.worktrees`, `shared-contracts`, `.devtool`, `.agents`, `node_modules`, `build`, `dist`, `target`, `.dart_tool`, and `__pycache__`.
   - Normalize parameterized endpoints (e.g., `/api/v1/lyrics-sync/tasks/{id}/progress` -> static route segments `/api/v1/lyrics-sync/tasks` and `/progress`) and check both `snake_case` and `camelCase` DTO field names (`lease_duration_ms` / `leaseDurationMs`) to classify each item as `FOUND_IN_CODE` or `MISSING_IN_CODE`.
2. **Semantic Baseline Diffing & Git-less Hub Fallback (`[SYC-EC-03]`)**:
   - When the Hub directory has no `.git` repository or has uncommitted edits, skip `git log` errors and compare the parsed contract structure against `baseline_snapshot` in `.agents/contract_sync.json` to surface added, removed, or modified endpoints, payload keys, pipeline steps, and RFCs.
3. **Worktree-Aware Symlink Resolution, Cycle Protection & Format Validation (`[SYC-AR-02]`, `[SYC-FR-01]`, `[SYC-FR-02]`)**:
   - When `<repo_root>/shared-contracts` is a relative symlink that does not resolve directly from `<repo_root>` because `<repo_root>` is a nested git worktree (`.worktrees/<epic_dir>`), inspect `.git` / `git rev-parse --git-common-dir` to locate the primary repository checkout root and resolve the relative link from there while keeping codebase scanning and `.agents/contract_sync.json` local to `<repo_root>`.
   - Enforce a 10-hop maximum when traversing symbolic links (`[SYC-AR-02]`).
   - Exit with code `1` and clear diagnostics if `shared-contracts` is missing (`[SYC-FR-01]`), is a dangling symlink even after worktree fallback, lacks any of the 3 canonical contract files, or has an unrecognizable contract format (`UNSUPPORTED_CONTRACT_FORMAT`) (`[SYC-FR-02]`).

## Files

Allowed files:
- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (new)
- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` (new)

Read-only context:
- `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` (new) — brief template from Task 1
- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — HLD specifications

## Design Rationale

- Worktree-aware symlink resolution ensures Stage 3 (`dev-implementation`) tasks running inside `.worktrees/<epic_dir>` can execute `sync_contracts.py check`, `brief`, and `ack` without modifying the tracked relative symlink.
- Comparing against `baseline_snapshot` provides exact semantic deltas even when Git history is absent or changes are uncommitted.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `sync_contracts.py` (`scan_target_codebase`, `resolve_topology`, `compute_semantic_delta`, `to_camel_case`, `cmd_check`) and tests in `test_sync_contracts.py`.
- **Downstream Callers**: `cmd_brief` and `cmd_ack` in Task 3.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% branch coverage on heuristic token matching, worktree symlink fallback, symlink loop detection, and format/path validation errors.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SYC-EC-02, SYC-EC-03, SYC-AR-02, SYC-FR-01, SYC-FR-02

```gherkin
Scenario: [SYC-EC-02] [Tier A - Unit] Heuristic Codebase Scanner Matches Parameterized Routes and CamelCase DTO Fields
  Given a target repository containing source file src/worker_client.ts with route "/api/v1/lyrics-sync/tasks" and "/progress" and field "leaseDurationMs"
  When the heuristic scanner evaluates endpoints "/api/v1/lyrics-sync/tasks/{id}/progress" and "/api/v1/lyrics-sync/status" and payload key "lease_duration_ms"
  Then endpoint "/api/v1/lyrics-sync/tasks/{id}/progress" and key "lease_duration_ms" are classified as "FOUND_IN_CODE"
  And unimplemented endpoint "/api/v1/lyrics-sync/status" is classified as "MISSING_IN_CODE"

Scenario: [SYC-EC-03] [Tier A - Unit] Semantic Baseline Diffing When Hub Has No Git History or Uncommitted Changes
  Given a Hub directory without a .git repository where a Satellite previously ran sync_contracts.py ack storing baseline_snapshot
  When an uncommitted edit in the Hub modifies api_contract.md by adding payload key "retry_after_ms" and changing a pipeline step
  And the engineer invokes sync_contracts.py check or brief
  Then the engine skips git rev-parse and git log without raising a subprocess error
  And compares the current contract against baseline_snapshot to surface "retry_after_ms" and the modified pipeline step as semantic deltas

Scenario: [SYC-AR-02] [Tier A - Unit] Circular Symlink Loop Protection During Topology Resolution
  Given a repository where shared-contracts is part of a circular symbolic link chain exceeding 10 hops
  When the engineer invokes sync_contracts.py check
  Then symlink traversal halts deterministically at the 10-hop boundary
  And exits with code 1 and an error message reporting a symbolic link loop

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
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ec_02` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ec_02` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ec_03` | exit 0; contains "OK" | — |
| V4 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ar_02` | exit 0; contains "OK" | — |
| V5 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_fr_01` | exit 0; contains "OK" | — |
| V6 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_fr_02` | exit 0; contains "OK" | — |
| V7 | TIER-B | `ruff check skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V8 | TIER-B | `mypy --strict --follow-imports=silent skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V9 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0; results build/test-results/task_2.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Symlink traversal follows unbounded loops without enforcing the 10-hop limit.

## Decisions Already Made

- Excluded directories during codebase scanning are `.git`, `.worktrees`, `shared-contracts`, `.devtool`, `.agents`, `node_modules`, `build`, `dist`, `target`, `.dart_tool`, and `__pycache__`.
- Symlink resolution halts at `MAX_SYMLINK_HOPS = 10` and falls back to resolving relative links against the primary git repository root when invoked inside a git worktree.
- Missing `shared-contracts`, dangling symlinks, missing canonical files, or unrecognizable contract files (`UNSUPPORTED_CONTRACT_FORMAT`) exit with code `1`.

## Definition of Done

- Heuristic codebase scanner accurately classifies parameterized endpoints and `snake_case`/`camelCase` fields (V2).
- Semantic baseline diffing (`baseline_snapshot`) works for Git-less Hub directories and uncommitted edits (V3).
- Circular symlink chains (`> 10` hops), missing `shared-contracts`, dangling symlinks, and unsupported contract formats exit with code `1` and clear diagnostics (V4, V5, V6).
- Ruff and Mypy strict checks pass (V7, V8).
- JUnit report is generated and all covered scenarios pass (V9).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 1](task_1_brief_template_and_contract_parser.md) — requires initial `sync_contracts.py` parser and test suite scaffold.

## References & Rollback

- Spec: `.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md`
- HLD: `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md`
- Rollback: Revert Task 2 additions in `sync_contracts.py` and `test_sync_contracts.py`.
