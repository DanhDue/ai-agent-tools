---
name: setup-shared-contracts
description: Sets up and verifies shared contract topologies, canonical templates (api_contract, architecture_and_flow, gaps_and_rfcs), relative symlinks, and governance rules across Hub and Satellite repositories.
---

# Setup Shared Contracts

## Overview

The `setup-shared-contracts` skill establishes and verifies standardized contract directories (`shared-contracts/`) across multi-repository topologies.

In distributed ecosystems linking a central control plane (Hub) with worker nodes or client applications (Satellites), contracts must maintain strict Single Source of Truth (SSOT) boundaries, Git mode `120000` relative symlinks, and non-breaking schema guarantees.

## When to Use

- When initializing an ecosystem control plane or backend repository as the Hub Single Source of Truth.
- When creating or linking a satellite repository (worker node, frontend, or mobile client) to an existing Hub.
- When registering a new domain service (e.g. `lyrics-sync`, `nexus-auth`) within an existing Hub repository.
- When performing preflight or continuous integration audits to verify symlink health, canonical file completeness, and rule presence.

## Core Architecture and Topology

Shared contracts follow a Star Topology centered on a single Hub:

```mermaid
flowchart TD
    HUB["Hub Repository (e.g. D3Nexus)<br/>Physical shared-contracts/ (SSOT)"]
    SAT1["Worker Satellite (e.g. lyrics-sync)<br/>shared-contracts (relative symlink)"]
    SAT2["Client Satellite (e.g. nexus)<br/>shared-contracts (relative symlink)"]

    HUB -->|Relative Symlink (mode 120000)| SAT1
    HUB -->|Relative Symlink (mode 120000)| SAT2
```

### The Three Canonical Contract Files

Every domain directory (`shared-contracts/<domain>/`) must contain exactly three canonical files:

1. `api_contract.md`: Wire-level contracts (REST / SSE / IPC), authentication headers (`X-Worker-Token`), telemetry heartbeats, and payload schemas.
2. `architecture_and_flow.md`: Component interaction topology, 7 canonical pipeline lifecycle steps, state machine transitions, cancellation fencing (< 50ms), and scratch cleanup.
3. `gaps_and_rfcs.md`: Asynchronous change ledger and proposal templates for non-breaking schema evolution.

## Workflows

### 1. Hub Initialization Workflow

To designate the current repository as the Hub authority:

1. Verify the repository does not contain an existing symbolic link at `shared-contracts/`.
2. Run the initialization command:
   ```bash
   python3 skills/setup-shared-contracts/resources/scripts/setup_contracts.py init-hub --domain <domain_name>
   ```
3. The engine creates:
   - Physical directory `shared-contracts/`.
   - Root `shared-contracts/README.md` with Star Topology layout and Outbound Symlink Mappings table.
   - Domain directory `shared-contracts/<domain_name>/` populated with the 3 canonical contract files.
   - Local Hub rule `.agents/rules/contract_rules.md` establishing SSOT governance.

### 2. Satellite Linking Workflow

To link a satellite repository to an existing Hub domain:

1. Locate the relative or absolute path to the Hub repository checkout.
2. Run the linking command from inside the satellite repository root:
   ```bash
   python3 skills/setup-shared-contracts/resources/scripts/setup_contracts.py link-satellite \
     --hub <path_to_hub> \
     --domain <domain_name>
   ```
3. The engine:
   - Validates that the Hub exists and contains `shared-contracts/<domain_name>/`.
   - Aborts if `shared-contracts/` in the satellite is an existing non-empty physical directory without `--force`.
   - Calculates single-direction relative path via `os.path.relpath`.
   - Creates the symbolic link `shared-contracts -> <relative_target>`.
   - Installs `.agents/rules/contract_rules.md` in the satellite enforcing Git read-only restrictions.
   - Appends `@.agents/rules/contract_rules.md` to `AGENTS.md` if present.

### 3. Integrity Verification Workflow

To verify that shared contracts are correctly configured and uncorrupted:

```bash
python3 skills/setup-shared-contracts/resources/scripts/setup_contracts.py verify
```

The engine auto-detects repository mode:
- **Hub Mode**: Validates physical directory presence, `README.md`, domain subdirectories, 3 canonical files, and Hub rules.
- **Satellite Mode**: Validates relative symlink format, symlink target resolution, canonical file accessibility, loop/cycle freedom (<= 10 hops), and Satellite rules.

## CLI Engine Reference

The CLI engine `setup_contracts.py` supports the following syntax:

```bash
# Initialize Hub repository
python3 setup_contracts.py init-hub [--repo-root <path>] [--domain <name>] [--force]

# Link Satellite repository
python3 setup_contracts.py link-satellite --hub <path> --domain <name> [--satellite-root <path>] [--force]

# Verify repository configuration
python3 setup_contracts.py verify [--repo-root <path>]
```

## Governance Invariants

- **Git Boundary Rule**: Satellite repositories must NEVER include `shared-contracts/` in `Files Allowed` for git commits.
- **Stateless Worker Rule**: Worker satellites must not connect directly to Hub database engines; all state synchronization occurs over authenticated API endpoints.
- **Non-Breaking Schema Guarantee**: Schema changes must provide safe defaults and maintain backward compatibility.

