# Setup Shared Contracts Design

- **Date**: 2026-10-30
- **Status**: In Review
- **Scope**: New skill `skills/setup-shared-contracts/`, CLI engine `setup_contracts.py`, canonical templates, hermetic test suite, integration with `scripts/verify.sh`
- **Next step**: `d3nexus:dev-designer` (Stage 2 — Architecture & Kanban Task Breakdown)

## Table of Contents

- [1. Background and Motivation](#1-background-and-motivation)
- [2. Goals and Non-Goals](#2-goals-and-non-goals)
- [3. Architecture and Topology Decisions](#3-architecture-and-topology-decisions)
- [4. Directory Structure and Components](#4-directory-structure-and-components)
- [5. CLI Engine Specifications](#5-cli-engine-specifications)
- [6. Canonical Template Bundles](#6-canonical-template-bundles)
- [7. Verification and Test Strategy](#7-verification-and-test-strategy)
- [8. Lifecycle Integration and Agent Experience](#8-lifecycle-integration-and-agent-experience)
- [9. Error Handling and Edge Cases](#9-error-handling-and-edge-cases)
- [10. Risks and Mitigations](#10-risks-and-mitigations)

## 1. Background and Motivation

In modern multi-repository and multi-tier architectures (such as the D3Nexus ecosystem linking the control plane `D3Nexus` with worker nodes like `lyrics-sync` and mobile clients like `nexus`), inter-service communication depends on a shared contracts directory (`shared-contracts/`). 

Historically, setting up `shared-contracts/` was a manual, error-prone procedure:
- Engineers had to manually construct subdirectories and author three canonical files (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`).
- Satellite repositories manually configured symbolic links. Agents frequently made symlinks using absolute paths, which broke on other machines or in CI/CD environments.
- Critical governance rules (such as Git tracking boundaries, stateless compute prohibitions against direct database access, and Non-Breaking Schema Guarantees) were often omitted or inconsistently configured in local `.agents/rules/`.

To eliminate these setup bottlenecks and ensure 100% adherence to Rule 7 of `CRITICAL_RULES.md`, we are introducing the `setup-shared-contracts` skill and its underlying CLI engine.

## 2. Goals and Non-Goals

### Goals
- Provide an automated CLI script (`setup_contracts.py`) written strictly in standard Python with zero external dependencies.
- Support **Hub Initialization (`init-hub`)**: Create physical `shared-contracts/`, generate domain folders, populate the 3 canonical contract files from validated templates, update root `README.md`, and install Hub local rules.
- Support **Satellite Linking (`link-satellite`)**: Compute robust relative symlinks (`os.path.relpath`), verify against dangling targets, install Satellite local rules, and update `AGENTS.md`.
- Support **Integrity Verification (`verify`)**: Auto-detect repository mode, validate symlink health, ensure the 3 canonical files exist, and check Git tracking boundaries.
- Include a comprehensive hermetic test suite (`test_setup_contracts.py`) validating all operations in isolated temporary directories.

### Non-Goals
- Generating domain-specific application DTOs in target programming languages (Rust, Dart, Python). That responsibility belongs to language-specific code generators or `dev-implementation`.
- Managing remote Git operations or pushing commits to remote repositories (strictly prohibited by Rule 3).

## 3. Architecture and Topology Decisions

1. **Star Topology (Hub-and-Spoke SSOT)**:
   - The Hub repository (`D3Nexus`) owns the physical `shared-contracts/` directory and acts as the Single Source of Truth (SSOT).
   - Satellite repositories (`lyrics-sync`, `nexus`) connect via single-direction relative symbolic links to their respective domain directories.
2. **Relative Symlink Standard**:
   - Symlinks MUST always be relative (e.g. `../D3Nexus/shared-contracts/lyrics-sync`), never absolute (`/Users/...`). This ensures portability across different development machines and CI runners.
3. **Canonical Contract Triad**:
   - Every domain folder inside `shared-contracts/<domain>/` MUST contain exactly three canonical files:
     - `api_contract.md`: Endpoints, payload schemas, telemetry heartbeats, and error contracts.
     - `architecture_and_flow.md`: Pipeline steps, state transitions, cancellation fencing, and isolation boundaries.
     - `gaps_and_rfcs.md`: RFC ledger and asynchronous change proposal tracking.
4. **Two-Tier Rule Architecture**:
   - Platform-wide invariants live in `CRITICAL_RULES.md` (Plugin Layer).
   - Domain-specific execution rules live in `.agents/rules/contract_rules.md` (Local Workspace Layer), customized for Hub vs Satellite modes.

## 4. Directory Structure and Components

The new skill is structured as follows within `ai-agent-tools`:

```text
skills/setup-shared-contracts/
├── SKILL.md
└── resources/
    ├── scripts/
    │   ├── setup_contracts.py
    │   └── test_setup_contracts.py
    └── templates/
        ├── api_contract.md.tmpl
        ├── architecture_and_flow.md.tmpl
        ├── gaps_and_rfcs.md.tmpl
        ├── shared_contracts_readme.md.tmpl
        ├── hub_contract_rules.md.tmpl
        └── satellite_contract_rules.md.tmpl
```

## 5. CLI Engine Specifications

The CLI script `setup_contracts.py` supports three primary commands:

### 5.1 Command: `init-hub`
```bash
python3 setup_contracts.py init-hub [--root <hub_root>] [--domain <domain_name>] [--force]
```
- **Validation**: Verifies that `shared-contracts` is not an existing symlink (Hub must be physical).
- **Actions**:
  1. Creates physical directory `<hub_root>/shared-contracts/`.
  2. Renders `<hub_root>/shared-contracts/README.md` from `shared_contracts_readme.md.tmpl`.
  3. If `--domain` is supplied:
     - Creates `<hub_root>/shared-contracts/<domain>/`.
     - Renders `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md` from templates.
     - Appends the domain to the Outbound Symlink Mappings table in `README.md`.
  4. Installs `<hub_root>/.agents/rules/contract_rules.md` from `hub_contract_rules.md.tmpl`.

### 5.2 Command: `link-satellite`
```bash
python3 setup_contracts.py link-satellite --hub <path_to_hub> --domain <domain_name> [--root <sat_root>] [--force]
```
- **Validation**:
  - Validates that `<path_to_hub>` exists and contains `shared-contracts/<domain_name>/`.
  - Aborts if `<sat_root>/shared-contracts` is a physical non-empty directory without `--force`.
- **Actions**:
  1. Computes the relative target path: `rel_target = os.path.relpath(hub_domain_dir, sat_root)`.
  2. Creates symbolic link: `<sat_root>/shared-contracts -> rel_target`.
  3. Asserts the symlink resolves cleanly on disk (no dangling symlink).
  4. Installs `<sat_root>/.agents/rules/contract_rules.md` from `satellite_contract_rules.md.tmpl`.
  5. Appends or updates the SSOT Contract Rule reminder in `<sat_root>/AGENTS.md` if the file exists.

### 5.3 Command: `verify`
```bash
python3 setup_contracts.py verify [--root <path>]
```
- **Actions**:
  - Automatically detects whether `<path>` is Hub Mode or Satellite Mode.
  - In Hub Mode: Validates that `shared-contracts/` is a physical directory, `README.md` exists, all domain directories contain the 3 canonical files, and `.agents/rules/contract_rules.md` is present.
  - In Satellite Mode: Validates that `shared-contracts` is a valid symbolic link, resolves to a target with all 3 canonical files, and verifies `.agents/rules/contract_rules.md` is present.
  - Exits `0` on success; exits `1` with explicit troubleshooting instructions on failure.

## 6. Canonical Template Bundles

Each template in `resources/templates/` includes parameter placeholders (e.g. `{{DOMAIN_NAME}}`, `{{HUB_NAME}}`, `{{DATE}}`):

1. **`shared_contracts_readme.md.tmpl`**:
   - Defines the Star Topology overview and Outbound Symlink table.
   - Embeds Mandatory Rules for AI Agents & Engineers (No Unilateral Breaking Changes, Contract-First Workflow, RFC Ledger).
2. **`api_contract.md.tmpl`**:
   - REST / SSE / IPC endpoint contracts, headers (`X-Worker-Token`), and telemetry heartbeat specs.
   - Result payload schemas with backward compatibility guarantees (safe defaults).
3. **`architecture_and_flow.md.tmpl`**:
   - 7 Canonical Pipeline Steps, State Machine transitions, cancellation fencing (< 50ms), and scratch cleanup.
   - Stateless compute boundary rules.
4. **`gaps_and_rfcs.md.tmpl`**:
   - RFC Ledger markdown table and template for logging new gaps/proposals.
5. **`hub_contract_rules.md.tmpl`**:
   - Local rule file for Hub repo enforcing SSOT ownership, `task_01` priority, and Parallel Handoff generation.
6. **`satellite_contract_rules.md.tmpl`**:
   - Local rule file for Satellite repo enforcing Git read-only boundary, prohibition of direct DB connections, and Asynchronous RFC workflows.

## 7. Verification and Test Strategy

The test suite in `resources/scripts/test_setup_contracts.py` executes under Python's `unittest` framework:
- **Test Hub Initialization**: Asserts directory structure, file contents, and idempotency of repeated runs.
- **Test Satellite Linking**: Creates mock sibling directories, creates symlinks, and asserts relative path correctness and file readability across the link.
- **Test Dangling Link Detection**: Verifies that invalid hub paths or missing domains trigger clear exit errors.
- **Test Verification Command**: Tests `verify` command on valid and corrupt setups, ensuring correct exit codes.
- **Continuous Integration**: Integrated directly into `scripts/verify.sh` as part of the repository release check suite.

## 8. Lifecycle Integration and Agent Experience

- **Skill Entry**: Triggered when a developer asks to initialize contracts, connect repos, or run `/setup-shared-contracts`.
- **Self-Detection**: The skill inspects the current directory and parent paths to auto-suggest whether to initialize as Hub or link as Satellite.
- **Handoff Generation**: Upon completing `link-satellite`, the tool outputs the exact Next Steps for the developer (running `verify` and proceeding with `dev-designer`).

## 9. Error Handling and Edge Cases

| Scenario | Handled By | Behavior |
|---|---|---|
| User runs `init-hub` in a satellite repo | `init-hub` | Detects `islink('shared-contracts')`, aborts with error: "Cannot init hub on a symlink". |
| User runs `link-satellite` with non-existent hub | `link-satellite` | Validates target path, aborts with error: "Hub domain directory not found". |
| Satellite `shared-contracts` is already a physical folder | `link-satellite` | Aborts with error unless `--force` is specified. |
| Existing files would be overwritten | All commands | Preserves existing files by default unless `--force` is explicitly provided. |

## 10. Risks and Mitigations

- **Risk: Breaking existing contracts during re-runs.**
  *Mitigation*: The CLI never overwrites existing contract files by default; existing files are preserved unless `--force` is given.
- **Risk: Absolute paths hardcoded in symlinks.**
  *Mitigation*: The script exclusively uses `os.path.relpath()` to compute relative paths, ensuring full machine portability.
- **Risk: Divergence from CRITICAL_RULES.**
  *Mitigation*: Templates directly incorporate the exact requirements from Rule 7 of `CRITICAL_RULES.md`.
