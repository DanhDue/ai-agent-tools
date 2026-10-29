---
id: "task_4_cli_engine_verification"
status: "todo"
priority: "high"
assignee: null
epic: "setup_shared_contracts"
dueDate: null
created: "2026-10-30T05:35:00Z"
modified: "2026-10-30T05:35:00Z"
completedAt: null
labels: ["contracts", "cli", "verify", "audit"]
order: "a4"
---

# Task 4: CLI Engine Verification and Integrity Audit

Epic: [setup_shared_contracts](setup_shared_contracts.en.md)

## Requirement Analysis

Implement the `verify` subcommand in `skills/setup-shared-contracts/resources/scripts/setup_contracts.py`.
The subcommand must:
1. Auto-detect workspace repository mode:
   - Hub mode when `shared-contracts` is a physical directory (`not os.path.islink`).
   - Satellite mode when `shared-contracts` is a symbolic link (`os.path.islink`).
   - Missing configuration when `shared-contracts` does not exist (exit code 1).
2. For Hub mode:
   - Verify `shared-contracts/README.md` exists and contains the Star Topology layout.
   - For every registered domain subdirectory, verify presence of `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md`.
   - Verify `.agents/rules/contract_rules.md` exists.
3. For Satellite mode:
   - Verify `shared-contracts` is a relative symbolic link (`not os.path.isabs(os.readlink(path))`).
   - Verify the symlink resolves to the physical domain directory and all 3 canonical files are accessible.
   - Traverse paths with depth limiting and cycle detection to prevent infinite recursion on cyclical symlinks (`[SSC-AR-02]`).
   - Verify `.agents/rules/contract_rules.md` exists and enforces Git read-only restrictions.
4. Provide domain name normalization trimming whitespace and lowercasing (`[SSC-EC-03]`).
5. Ensure atomic file writes using temporary swap files during generation/updates (`[SSC-AR-01]`).

Implement unit and integration tests in `test_setup_contracts.py` covering health audits and failure diagnostics.

## Files

Allowed files:
- `skills/setup-shared-contracts/resources/scripts/setup_contracts.py` (new)
- `skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` (new)

Read-only context:
- `.devtool/epic/setup_shared_contracts/setup_shared_contracts.en.md` — HLD specifications

## Design Rationale

- Auto-detection eliminates developer error by inspecting filesystem properties directly.
- Depth boundaries and cycle detection safeguard verification from hangs in malformed repositories.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `skills/setup-shared-contracts/resources/scripts/setup_contracts.py` (`verify` function, cycle detector, normalization helpers) and tests in `test_setup_contracts.py`.
- **Downstream Callers**: Quality check gates and CI/CD pipelines validating multi-repo contract setups.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% path coverage for verify audit passes, dangling link failures, missing file diagnostics, and cycle detections.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SSC-EC-03, SSC-AR-01, SSC-AR-02

```gherkin
Scenario: [SSC-EC-03] [Tier A - Unit] Domain Name Normalization and Whitespace Stripping
  Given an engineer passes a domain name with leading spaces and mixed casing "  Lyrics-Sync  "
  When the CLI processes the domain argument
  Then the domain directory is normalized to lowercase trimmed string "lyrics-sync"
  And paths and documentation anchors are generated consistently

Scenario: [SSC-AR-01] [Tier A - Unit] Atomic File Creation Prevents Partial Writes
  Given template rendering operations writing out the 3 canonical contract files
  When file writing occurs during parallel execution
  Then files are written atomically using temporary swap files or direct unbuffered writes
  And no partially written or zero-byte canonical files are observed by concurrent processes

Scenario: [SSC-AR-02] [Tier A - Unit] Circular Symlink and Loop Protection
  Given an unusual workspace containing existing cyclical symbolic links
  When setup_contracts.py verify traverses paths to resolve contracts
  Then the traversal uses cycle detection and depth boundaries
  And halts cleanly without entering infinite recursion loops
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_ec_03` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_ec_03` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_ar_01` | exit 0; contains "OK" | — |
| V4 | GREEN | `python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py -k test_ssc_ar_02` | exit 0; contains "OK" | — |
| V5 | TIER-B | `ruff check skills/setup-shared-contracts/resources/scripts/setup_contracts.py skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0 | — |
| V6 | TIER-B | `mypy --strict --follow-imports=silent skills/setup-shared-contracts/resources/scripts/setup_contracts.py skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0 | — |
| V7 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_4.xml skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py` | exit 0; results build/test-results/task_4.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Symlink cycle detector fails to terminate on circular symlink fixtures.

## Decisions Already Made

- Normalization algorithm: `domain.strip().lower()`.
- Maximum symlink resolution depth is 10 hops before reporting cyclical loop error.
- Subcommand syntax: `setup_contracts.py verify [--repo-root <path>]`.

## Definition of Done

- `setup_contracts.py` implements the `verify` subcommand with auto-detection of Hub and Satellite modes (V2).
- Domain names with leading/trailing whitespace and mixed casing are normalized (V2).
- Atomic write helpers prevent partial or torn writes (V3).
- Cyclical symlinks are safely trapped without recursion errors (V4).
- Linter and type checks pass cleanly (V5, V6).
- JUnit report produced and integration tests pass (V7).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 3](task_3_cli_engine_satellite_linking.md) — completes the full CLI lifecycle commands.

## References & Rollback

- Spec: `.devtool/epic/setup_shared_contracts/2026-10-30-setup-shared-contracts-design.en.md`
- HLD: `.devtool/epic/setup_shared_contracts/setup_shared_contracts.en.md`
- Rollback: Reverting `verify` in `setup_contracts.py` and test additions.
