---
id: "task_1_canonical_template_bundles"
status: "done"
priority: "high"
assignee: null
epic: "setup_shared_contracts"
dueDate: null
created: "2026-10-30T05:35:00Z"
modified: "2026-10-30T07:00:51Z"
completedAt: "2026-10-30T07:00:51Z"
labels: ["contracts", "templates"]
order: "a1"
---

# Task 1: Canonical Template Bundles

Epic: [setup_shared_contracts](setup_shared_contracts.en.md)

## Requirement Analysis

Package the canonical templates required by `setup_contracts.py` into `skills/setup-shared-contracts/resources/templates/`.
These templates represent the authoritative standard for all multi-repo shared contracts:
1. `api_contract.md.tmpl`: Canonical API and event schemas (Overview, Protocol & Transports, Schema Definitions, Endpoints / Message Types, Error Invariants, Version Changelog).
2. `architecture_and_flow.md.tmpl`: Architecture topology (Mermaid `flowchart TD`), sequence flows (Mermaid `sequenceDiagram`), actor responsibilities, state transitions.
3. `gaps_and_rfcs.md.tmpl`: Gap analysis, RFC proposals, non-breaking schema evolution guarantees.
4. `hub_readme.md.tmpl`: Root README for Hub `shared-contracts/` documenting Star Topology, Outbound Symlink Mappings table, and Hub SSOT rules.
5. `hub_rule.md.tmpl`: Local Hub rule `.agents/rules/contract_rules.md` establishing Hub as SSOT.
6. `satellite_rule.md.tmpl`: Local Satellite rule `.agents/rules/contract_rules.md` establishing relative symlink tracking (mode `120000`), Git read-only boundary, and forbidding `shared-contracts/` in task `Files Allowed`.

Also initialize `skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` with the test harness and test cases covering template rendering, placeholder validation, and idempotent preservation (`SSC-HP-01`, `SSC-EC-01`).

## Files

Allowed files:
- `skills/setup-shared-contracts/resources/templates/api_contract.md.tmpl` (new)
- `skills/setup-shared-contracts/resources/templates/architecture_and_flow.md.tmpl` (new)
- `skills/setup-shared-contracts/resources/templates/gaps_and_rfcs.md.tmpl` (new)
- `skills/setup-shared-contracts/resources/templates/hub_readme.md.tmpl` (new)
- `skills/setup-shared-contracts/resources/templates/hub_rule.md.tmpl` (new)
- `skills/setup-shared-contracts/resources/templates/satellite_rule.md.tmpl` (new)
- `skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` (new)

Read-only context:
- `.devtool/epic/setup_shared_contracts/setup_shared_contracts.en.md` — HLD specifications
- `rules/CRITICAL_RULES.md` — canonical contract rules and multi-repo boundary standards

## Design Rationale

- Templates use Python `string.Template` syntax (`$domain`, `$hub_repo`, `$timestamp`) for safe, dependency-free rendering without Jinja2 or external dependencies.
- Hermetic test cases verify that every template contains required sections, valid Markdown anchors, and placeholder substitutions.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: 6 canonical template files in `skills/setup-shared-contracts/resources/templates/` and test harness `test_setup_contracts.py`.
- **Downstream Callers**: Tasks 2, 3, 4 consume these templates in `setup_contracts.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% template integrity and substitution validation.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SSC-HP-01, SSC-EC-01

```gherkin
Scenario: [SSC-HP-01] [Tier C - Integration] Fresh Hub Repository Initialization
  Given an empty repository directory designated as a Hub
  When the engineer invokes setup_contracts.py init-hub --domain lyrics-sync
  Then the physical directory shared-contracts/ is created
  And the file shared-contracts/README.md is rendered with the Star Topology layout
  And the domain directory shared-contracts/lyrics-sync/ contains api_contract.md, architecture_and_flow.md, and gaps_and_rfcs.md
  And the local Hub rule .agents/rules/contract_rules.md is created with SSOT ownership instructions
  And the command exits with code 0

Scenario: [SSC-EC-01] [Tier A - Unit] Idempotent Execution Preserves Custom Edits
  Given an existing Hub repository where api_contract.md has been modified with custom endpoints
  When the engineer invokes setup_contracts.py init-hub --domain lyrics-sync without --force
  Then the existing api_contract.md is left unchanged and not overwritten
  And the command completes successfully with exit code 0
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_hp_01` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_hp_01` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_ec_01` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_1.xml skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0; results build/test-results/task_1.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Any template file contains unresolved non-standard syntax that breaks `string.Template`.

## Decisions Already Made

- Templates use `.tmpl` extension and standard library `string.Template` placeholders (`$domain`, `$hub_repo`, `$timestamp`).
- The 3 canonical contract files are: `api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`.
- Satellite local rules enforce symlink mode `120000`, Git read-only, and forbid `shared-contracts/` in task `Files Allowed`.
- Hub rules enforce SSOT ownership and mandate schema backward compatibility.

## Definition of Done

- All 6 canonical template files exist under `skills/setup-shared-contracts/resources/templates/` with valid Markdown headers (V2).
- Unit tests in `test_setup_contracts.py` verify template loading, substitution, and `SSC-HP-01` and `SSC-EC-01` behavior (V2, V3).
- Linter and type checks pass cleanly (V4, V5).
- JUnit report is produced and integration tests pass (V6).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- None.

## References & Rollback

- Spec: `.devtool/epic/setup_shared_contracts/2026-10-30-setup-shared-contracts-design.en.md`
- HLD: `.devtool/epic/setup_shared_contracts/setup_shared_contracts.en.md`
- Rollback: Deleting `skills/setup-shared-contracts/resources/templates/` leaves the repository clean.
