---
id: "task_3_cli_engine_satellite_linking"
status: "todo"
priority: "high"
assignee: null
epic: "setup_shared_contracts"
dueDate: null
created: "2026-10-30T05:35:00Z"
modified: "2026-10-30T05:35:00Z"
completedAt: null
labels: ["contracts", "cli", "satellite", "symlink"]
order: "a3"
---

# Task 3: CLI Engine Satellite Linking and Relative Symlinks

Epic: [setup_shared_contracts](setup_shared_contracts.en.md)

## Requirement Analysis

Implement the `link-satellite` subcommand in `skills/setup-shared-contracts/resources/scripts/setup_contracts.py`.
The subcommand must:
1. Verify that the target Hub directory exists and contains `shared-contracts/<domain>/`. If either does not exist, refuse to create a dangling link and exit with non-zero exit code `1` (`[SSC-FR-02]`).
2. Calculate the single-direction relative path from the Satellite workspace root to the Hub domain directory using `os.path.relpath(hub_domain_path, satellite_root)` (`[SSC-HP-02]`, `[SSC-EC-02]`).
3. Check for existing paths at `shared-contracts`:
   - If `shared-contracts/` is an existing non-empty physical directory and `--force` is omitted, abort with code `1` to prevent uncommitted file loss (`[SSC-FR-03]`).
   - If `shared-contracts` is an existing symbolic link or `--force` is provided, update the link target atomically (`[SSC-ST-02]`).
4. Generate the Satellite local rule `.agents/rules/contract_rules.md` from `satellite_rule.md.tmpl`.
5. Check if `AGENTS.md` exists in the satellite; if present and not already referencing the contract rules, append the `@.agents/rules/contract_rules.md` reference.

Implement unit and integration tests in `test_setup_contracts.py` verifying deep sibling hierarchy calculations and boundary conditions.

## Files

Allowed files:
- `skills/setup-shared-contracts/resources/scripts/setup_contracts.py` (new)
- `skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` (new)

Read-only context:
- `skills/setup-shared-contracts/resources/templates/satellite_rule.md.tmpl` — template
- `.devtool/epic/setup_shared_contracts/setup_shared_contracts.en.md` — HLD specifications

## Design Rationale

- Single-direction relative symlinks (`os.path.relpath`) guarantee that symlinks remain valid across developer machines, alternate clone locations, and CI/CD containers.
- Absolute symlinks are strictly rejected as non-portable.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `skills/setup-shared-contracts/resources/scripts/setup_contracts.py` (`link_satellite` function, relative path math) and tests in `test_setup_contracts.py`.
- **Downstream Callers**: All satellite consumer repositories (e.g. `lyrics-sync`, `nexus`).
- **Cross-Platform Bridges**: Git symbolic link mode `120000` preservation across macOS and Linux.
- **Target Test Coverage Threshold**: 100% path coverage for symlink generation, deep nesting, force replacement, and error conditions.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SSC-HP-02, SSC-EC-02, SSC-ST-02, SSC-FR-02, SSC-FR-03

```gherkin
Scenario: [SSC-HP-02] [Tier C - Integration] Fresh Satellite Repository Relative Symlinking
  Given an existing Hub repository with initialized shared-contracts/lyrics-sync/
  And a separate sibling satellite repository directory lyrics-sync
  When the engineer invokes setup_contracts.py link-satellite --hub ../D3Nexus --domain lyrics-sync from inside lyrics-sync
  Then the path shared-contracts is created as a relative symbolic link pointing to ../D3Nexus/shared-contracts/lyrics-sync
  And the symlink resolves to all 3 canonical contract files without dangling errors
  And the satellite rule .agents/rules/contract_rules.md is created with Git read-only restrictions
  And the command exits with code 0

Scenario: [SSC-EC-02] [Tier A - Unit] Deep Sibling Hierarchy Relative Path Calculation
  Given a Hub located at root/control-plane/hub
  And a Satellite located at root/services/workers/audio/satellite
  When the engineer executes link-satellite with the path to the hub
  Then the generated symlink uses the exact relative path ../../../../control-plane/hub/shared-contracts/<domain>
  And the symlink successfully resolves to the target files

Scenario: [SSC-ST-02] [Tier C - Integration] Switching Linked Domain on Satellite with Force
  Given a satellite repository symlinked to domain alpha
  When the engineer invokes link-satellite --hub ../Hub --domain beta --force
  Then the existing symlink is updated to point to ../Hub/shared-contracts/beta
  And the old symlink target is cleanly replaced without leftover dangling references

Scenario: [SSC-FR-02] [Tier A - Unit] Refusing Satellite Linking When Target Domain Missing
  Given a valid Hub repository that does not contain domain unknown-service
  When the engineer invokes link-satellite --hub ../Hub --domain unknown-service
  Then the command refuses to create a dangling symlink
  And prints an error stating that the target domain was not found in the Hub
  And exits with non-zero exit code 1

Scenario: [SSC-FR-03] [Tier A - Unit] Refusing Overwrite of Existing Physical Directory Without Force
  Given a satellite repository where shared-contracts/ is an existing non-empty physical directory
  When the engineer invokes link-satellite without --force
  Then the command refuses to replace the physical directory with a symlink
  And prints an error warning of potential uncommitted file loss
  And exits with non-zero exit code 1
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_hp_02` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_hp_02` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_ec_02` | exit 0; contains "OK" | — |
| V4 | GREEN | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_st_02` | exit 0; contains "OK" | — |
| V5 | GREEN | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_fr_02` | exit 0; contains "OK" | — |
| V6 | GREEN | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_fr_03` | exit 0; contains "OK" | — |
| V7 | TIER-B | `ruff check skills/setup-shared-contracts/resources/scripts/setup_contracts.py skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0 | — |
| V8 | TIER-B | `mypy --strict --follow-imports=silent skills/setup-shared-contracts/resources/scripts/setup_contracts.py skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0 | — |
| V9 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_3.xml skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0; results build/test-results/task_3.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Symlink generated is absolute instead of relative.

## Decisions Already Made

- All symlinks must be computed via `os.path.relpath`.
- Existing non-empty physical directories must never be overwritten without explicit `--force`.
- Subcommand syntax: `setup_contracts.py link-satellite --hub <path> --domain <name> [--satellite-root <path>] [--force]`.

## Definition of Done

- `setup_contracts.py` implements `link-satellite` creating single-direction relative symlinks (V2, V3).
- Force re-linking updates domain destinations cleanly (V4).
- Missing hub or missing domain targets are rejected with code 1 (V5).
- Existing non-empty physical directories are protected against accidental erasure (V6).
- Linter and type checks pass cleanly (V7, V8).
- JUnit report produced and integration tests pass (V9).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 2](task_2_cli_engine_hub_init.md) — builds upon the CLI parser and core engine.

## References & Rollback

- Spec: `.devtool/epic/setup_shared_contracts/2026-10-30-setup-shared-contracts-design.en.md`
- HLD: `.devtool/epic/setup_shared_contracts/setup_shared_contracts.en.md`
- Rollback: Reverting `link_satellite` in `setup_contracts.py` and test additions.
