---
id: "task_1_brief_template_and_contract_parser"
status: "todo"
priority: "high"
assignee: null
epic: "sync_shared_contracts"
dueDate: null
created: "2026-10-30T11:58:00Z"
modified: "2026-10-30T11:58:00Z"
completedAt: null
labels: ["contracts", "templates", "parser"]
order: "a1"
---

# Task 1: Canonical Brief Template and Markdown Contract Parser

Epic: [sync_shared_contracts](../epic/sync_shared_contracts/sync_shared_contracts.en.md)

## Requirement Analysis

Create the canonical delta brief template `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` and implement the structured Markdown contract parser and initial sync baseline logic in `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`.
1. Author `contract_delta_brief.md.tmpl` using standard library `string.Template` placeholders (`$domain`, `$mode`, `$sync_status`, `$previous_version`, `$current_version`, `$hub_commit_range`, `$changed_files_summary`, `$endpoints_section`, `$payload_keys_section`, `$pipeline_steps_section`, `$rfcs_section`, `$lifecycle_rules_section`).
2. Implement structured Markdown parsing in `sync_contracts.py` for the 3 canonical contract files:
   - `api_contract.md`: Extract `Version`, required authentication headers table, `Endpoints Matrix` rows (`Method`, `Endpoint`, `Auth`, `Purpose`), JSON payload schema top-level and nested keys, and `Version Changelog` entries.
   - `architecture_and_flow.md`: Extract numbered canonical pipeline steps and state machine transitions.
   - `gaps_and_rfcs.md`: Extract `Active RFC Ledger` rows (`RFC ID`, `Title`, `Proposing Repo`, `Status`, `Target Release`, `Breaking?`).
3. Implement initial baseline detection (`INITIAL_SYNC`) when `.agents/contract_sync.json` does not exist yet (`[SYC-EC-01]`) and brief rendering (`[SYC-HP-01]`).
4. Initialize `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` covering `[SYC-HP-01]` and `[SYC-EC-01]`.

## Files

Allowed files:
- `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` (new)
- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (new)
- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` (new)

Read-only context:
- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — HLD specifications
- `skills/setup-shared-contracts/resources/templates/api_contract.md.tmpl` — canonical API contract structure
- `skills/setup-shared-contracts/resources/templates/architecture_and_flow.md.tmpl` — canonical architecture structure
- `skills/setup-shared-contracts/resources/templates/gaps_and_rfcs.md.tmpl` — canonical RFC ledger structure

## Design Rationale

- Standard library `string.Template` and regex/line-based table parsers keep `sync_contracts.py` 100% dependency-free and portable across Python 3.10+ environments.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `contract_delta_brief.md.tmpl`, `sync_contracts.py` (`parse_api_contract`, `parse_architecture_and_flow`, `parse_gaps_and_rfcs`, `render_brief`), and `test_sync_contracts.py`.
- **Downstream Callers**: Tasks 2, 3, and 4 build upon `sync_contracts.py` and `test_sync_contracts.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% coverage of Markdown table/schema extraction and template substitution.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SYC-HP-01, SYC-EC-01

```gherkin
Scenario: [SYC-HP-01] [Tier C - Integration] Structured Contract Parsing and Requirements Brief Rendering
  Given an initialized Hub repository with domain lyrics-sync containing api_contract.md, architecture_and_flow.md, and gaps_and_rfcs.md
  When the engineer invokes sync_contracts.py brief --domain lyrics-sync
  Then the parser extracts version "1.0.0", the 4 canonical endpoints, authentication headers, JSON payload keys, 7 pipeline steps, and RFC-001
  And the output Markdown report contains sections for Topology Metadata, API and Schema Requirements, Architecture Invariants, Actionable RFCs, and Lifecycle Execution Rules
  And the command exits with code 0

Scenario: [SYC-EC-01] [Tier A - Unit] Initial Sync Detection When Watermark File Is Absent
  Given a valid Satellite repository where .agents/contract_sync.json does not exist
  When the engineer invokes sync_contracts.py check --json
  Then the JSON report identifies the domain status as "INITIAL_SYNC"
  And lists all 3 canonical contract files as unsynced baseline deltas
  And the command exits with code 0 when --strict is omitted and code 1 when --strict is provided
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_hp_01` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_hp_01` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ec_01` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_1.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0; results build/test-results/task_1.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Any canonical template placeholder in `contract_delta_brief.md.tmpl` fails substitution under `string.Template`.

## Decisions Already Made

- New frozen contract `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` uses `string.Template` placeholders and emits the 5 canonical brief sections (`Topology & Sync Metadata`, `API & Schema Requirements`, `Architecture & Pipeline Invariants`, `Actionable RFCs & Gaps`, `Lifecycle Execution Rules`).
- Grounded canonical contract files from `skills/setup-shared-contracts/resources/templates/` are `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md`.
- When `.agents/contract_sync.json` is absent, `check` reports `status: "INITIAL_SYNC"`, exits `0` by default, and exits `1` when `--strict` is passed.

## Definition of Done

- `contract_delta_brief.md.tmpl` and Markdown contract parsers in `sync_contracts.py` are implemented and render the full brief (V2).
- `INITIAL_SYNC` status detection and `--strict` exit code behavior pass unit tests (V3).
- Ruff linting and Mypy strict type checks pass with zero errors (V4, V5).
- JUnit XML report is generated and integration tests for `SYC-HP-01` and `SYC-EC-01` pass (V6).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- None.

## References & Rollback

- Spec: `.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md`
- HLD: `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md`
- Rollback: Remove `skills/sync-shared-contracts/resources/` to restore clean state.
