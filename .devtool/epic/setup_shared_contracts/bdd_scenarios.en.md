# Setup Shared Contracts BDD Scenarios

## Table of Contents

- [Dimension 1: Happy Paths](#dimension-1-happy-paths)
- [Dimension 2: Edge Cases and Boundaries](#dimension-2-edge-cases-and-boundaries)
- [Dimension 3: State Transitions](#dimension-3-state-transitions)
- [Dimension 4: Async and Multi-Repo Concurrency](#dimension-4-async-and-multi-repo-concurrency)
- [Dimension 5: Failures and Storage Resilience](#dimension-5-failures-and-storage-resilience)

## Dimension 1: Happy Paths

```gherkin
Scenario: [SSC-HP-01] [Tier C - Integration] Fresh Hub Repository Initialization
  Given an empty repository directory designated as a Hub
  When the engineer invokes setup_contracts.py init-hub --domain lyrics-sync
  Then the physical directory shared-contracts/ is created
  And the file shared-contracts/README.md is rendered with the Star Topology layout
  And the domain directory shared-contracts/lyrics-sync/ contains api_contract.md, architecture_and_flow.md, and gaps_and_rfcs.md
  And the local Hub rule .agents/rules/contract_rules.md is created with SSOT ownership instructions
  And the command exits with code 0

Scenario: [SSC-HP-02] [Tier C - Integration] Fresh Satellite Repository Relative Symlinking
  Given an existing Hub repository with initialized shared-contracts/lyrics-sync/
  And a separate sibling satellite repository directory lyrics-sync
  When the engineer invokes setup_contracts.py link-satellite --hub ../D3Nexus --domain lyrics-sync from inside lyrics-sync
  Then the path shared-contracts is created as a relative symbolic link pointing to ../D3Nexus/shared-contracts/lyrics-sync
  And the symlink resolves to all 3 canonical contract files without dangling errors
  And the satellite rule .agents/rules/contract_rules.md is created with Git read-only restrictions
  And the command exits with code 0

Scenario: [SSC-HP-03] [Tier C - Integration] Comprehensive Health Verification Pass
  Given a validly initialized Hub repository and linked Satellite repository
  When the engineer invokes setup_contracts.py verify in either repository
  Then the engine auto-detects the repository mode
  And validates the physical files, symlink targets, and local rule existence
  And outputs a green PASS report with exit code 0
```

## Dimension 2: Edge Cases and Boundaries

```gherkin
Scenario: [SSC-EC-01] [Tier A - Unit] Idempotent Execution Preserves Custom Edits
  Given an existing Hub repository where api_contract.md has been modified with custom endpoints
  When the engineer invokes setup_contracts.py init-hub --domain lyrics-sync without --force
  Then the existing api_contract.md is left unchanged and not overwritten
  And the command completes successfully with exit code 0

Scenario: [SSC-EC-02] [Tier A - Unit] Deep Sibling Hierarchy Relative Path Calculation
  Given a Hub located at root/control-plane/hub
  And a Satellite located at root/services/workers/audio/satellite
  When the engineer executes link-satellite with the path to the hub
  Then the generated symlink uses the exact relative path ../../../../control-plane/hub/shared-contracts/<domain>
  And the symlink successfully resolves to the target files

Scenario: [SSC-EC-03] [Tier A - Unit] Domain Name Normalization and Whitespace Stripping
  Given an engineer passes a domain name with leading spaces and mixed casing "  Lyrics-Sync  "
  When the CLI processes the domain argument
  Then the domain directory is normalized to lowercase trimmed string "lyrics-sync"
  And paths and documentation anchors are generated consistently
```

## Dimension 3: State Transitions

```gherkin
Scenario: [SSC-ST-01] [Tier C - Integration] Adding Subsequent Domains Updates Topology README
  Given an existing Hub repository already containing domain lyrics-sync
  When the engineer invokes setup_contracts.py init-hub --domain nexus
  Then the directory shared-contracts/nexus/ is created with its 3 canonical files
  And the root shared-contracts/README.md is updated to include nexus in the Outbound Symlink Mappings table
  And the existing lyrics-sync entry is preserved intact

Scenario: [SSC-ST-02] [Tier C - Integration] Switching Linked Domain on Satellite with Force
  Given a satellite repository symlinked to domain alpha
  When the engineer invokes link-satellite --hub ../Hub --domain beta --force
  Then the existing symlink is updated to point to ../Hub/shared-contracts/beta
  And the old symlink target is cleanly replaced without leftover dangling references
```

## Dimension 4: Async and Multi-Repo Concurrency

```gherkin
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

## Dimension 5: Failures and Storage Resilience

```gherkin
Scenario: [SSC-FR-01] [Tier A - Unit] Refusing Hub Initialization on Existing Symlink
  Given a directory where shared-contracts is currently a symbolic link
  When the engineer invokes setup_contracts.py init-hub
  Then the command refuses to execute
  And prints an error explaining that Hub repositories must maintain physical directories
  And exits with non-zero exit code 1

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
