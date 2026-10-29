---
id: "task_2_cli_engine_hub_init"
status: "todo"
priority: "high"
assignee: null
epic: "setup_shared_contracts"
dueDate: null
created: "2026-10-30T05:35:00Z"
modified: "2026-10-30T05:35:00Z"
completedAt: null
labels: ["contracts", "cli", "hub"]
order: "a2"
---

# Task 2: CLI Engine Hub Initialization and Rules

Epic: [setup_shared_contracts](setup_shared_contracts.en.md)

## Requirement Analysis

Implement the `init-hub` command in `skills/setup-shared-contracts/resources/scripts/setup_contracts.py`.
The subcommand must:
1. Validate that the target repository path does not already contain `shared-contracts` as a symbolic link (`os.path.islink`). If it does, refuse execution and exit with non-zero exit code `1` (`[SSC-FR-01]`).
2. Create the physical directory `shared-contracts/` if missing.
3. Render `shared-contracts/README.md` from `hub_readme.md.tmpl`. When multiple domains exist or are added subsequently, update the Outbound Symlink Mappings table without erasing existing domain entries (`[SSC-ST-01]`).
4. Create the domain subdirectory `shared-contracts/<domain>/` containing the 3 canonical files (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`).
5. Ensure idempotent behavior: if a canonical contract file already exists, leave it untouched unless `--force` is provided.
6. Create the Hub local rule `.agents/rules/contract_rules.md` from `hub_rule.md.tmpl` if not already present.

Write unit and integration tests in `test_setup_contracts.py` exercising `init-hub` with throwaway temporary directories.

## Files

Allowed files:
- `skills/setup-shared-contracts/resources/scripts/setup_contracts.py` (new)
- `skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` (new)

Read-only context:
- `skills/setup-shared-contracts/resources/templates/api_contract.md.tmpl` — template
- `skills/setup-shared-contracts/resources/templates/architecture_and_flow.md.tmpl` — template
- `skills/setup-shared-contracts/resources/templates/gaps_and_rfcs.md.tmpl` — template
- `skills/setup-shared-contracts/resources/templates/hub_readme.md.tmpl` — template
- `skills/setup-shared-contracts/resources/templates/hub_rule.md.tmpl` — template
- `.devtool/epic/setup_shared_contracts/setup_shared_contracts.en.md` — HLD specifications

## Design Rationale

- `setup_contracts.py` is written in standard Python 3.10+ without third-party runtime dependencies.
- Subcommand routing is handled via `argparse.ArgumentParser` with subparsers (`init-hub`, `link-satellite`, `verify`).
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `skills/setup-shared-contracts/resources/scripts/setup_contracts.py` (`init_hub` function, CLI argument parser) and tests in `test_setup_contracts.py`.
- **Downstream Callers**: Developers and AI agents initializing Hub repositories.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% path coverage for `init-hub` error conditions and successful directory creations.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SSC-ST-01, SSC-FR-01

```gherkin
Scenario: [SSC-ST-01] [Tier C - Integration] Adding Subsequent Domains Updates Topology README
  Given an existing Hub repository already containing domain lyrics-sync
  When the engineer invokes setup_contracts.py init-hub --domain nexus
  Then the directory shared-contracts/nexus/ is created with its 3 canonical files
  And the root shared-contracts/README.md is updated to include nexus in the Outbound Symlink Mappings table
  And the existing lyrics-sync entry is preserved intact

Scenario: [SSC-FR-01] [Tier A - Unit] Refusing Hub Initialization on Existing Symlink
  Given a directory where shared-contracts is currently a symbolic link
  When the engineer invokes setup_contracts.py init-hub
  Then the command refuses to execute
  And prints an error explaining that Hub repositories must maintain physical directories
  And exits with non-zero exit code 1
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_st_01` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_st_01` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_fr_01` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/setup-shared-contracts/resources/scripts/setup_contracts.py skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent skills/setup-shared-contracts/resources/scripts/setup_contracts.py skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0; results build/test-results/task_2.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Target path contains a symbolic link and `init-hub` attempts to follow or overwrite it without error.

## Decisions Already Made

- Physical Hub directories must never be converted into symbolic links.
- Updating `shared-contracts/README.md` preserves all previously registered domains in the Outbound Symlink Mappings table.
- Subcommand syntax: `setup_contracts.py init-hub [--domain <name>] [--repo-root <path>] [--force]`.

## Definition of Done

- `setup_contracts.py` implements the `init-hub` subcommand with full argument parsing (V2).
- Adding subsequent domains updates the README table while retaining existing entries (V2).
- Rejection of symlinks for Hub directories exits code 1 with clear diagnostic message (V3).
- Linter and type checks pass cleanly (V4, V5).
- JUnit report produced and integration tests pass (V6).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 1](task_1_canonical_template_bundles.md) — requires templates for canonical contract rendering.

## References & Rollback

- Spec: `.devtool/epic/setup_shared_contracts/2026-10-30-setup-shared-contracts-design.en.md`
- HLD: `.devtool/epic/setup_shared_contracts/setup_shared_contracts.en.md`
- Rollback: Reverting `setup_contracts.py` and test additions restores previous state.
