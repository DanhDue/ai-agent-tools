# Contract Diff Gate BDD Scenarios

## Table of Contents

- [Dimension 1: Happy Paths](#dimension-1-happy-paths)
- [Dimension 2: Edge Cases and Boundaries](#dimension-2-edge-cases-and-boundaries)
- [Dimension 3: State Transitions](#dimension-3-state-transitions)
- [Dimension 4: Async and Multi-Repo Concurrency](#dimension-4-async-and-multi-repo-concurrency)
- [Dimension 5: Failures and Storage Resilience](#dimension-5-failures-and-storage-resilience)

## Dimension 1: Happy Paths

```gherkin
Scenario: [CDG-HP-01] [Tier C - Integration] Hub Mapped File Change Covered by Canonical Contract Edit
  Given an initialized Hub repository on branch develop with .agents/contract_map.json mapping "crates/**/routes/**" and "crates/**/dto/**" (excluding "**/tests/**") to domain "lyrics-sync"
  When a committed feature branch modifies "crates/api/routes/worker.rs" and "shared-contracts/lyrics-sync/api_contract.md" on a clean working tree
  And the engineer invokes sync_contracts.py diff-check --base-ref develop --json
  Then the JSON report contains status "PASS", mode "hub", violations [], and blockers []
  And the command exits with code 0

Scenario: [CDG-HP-02] [Tier C - Integration] Satellite Mapped File Change Covered by Fresh Domain Ack Matching Live Snapshot
  Given a Satellite repository linked via relative symlink shared-contracts to ../Hub/shared-contracts/lyrics-sync with .agents/contract_map.json mapping "src/api/dto/**" to domain "lyrics-sync"
  When a committed feature branch modifies "src/api/dto/worker.py" and updates domains["lyrics-sync"] in .agents/contract_sync.json via sync_contracts.py ack --snapshot <live_snapshot_id> --all-rfcs
  And the engineer invokes sync_contracts.py diff-check --json
  Then diff-check confirms domains["lyrics-sync"].snapshot_id at HEAD equals the live snapshot_id computed from shared-contracts
  And the JSON report contains status "PASS", mode "satellite", and violations []
  And the command exits with code 0

Scenario: [CDG-HP-03] [Tier C - Integration] Quality Provider Schemas, Placeholders, and Exit Code 2 Mapping Verification
  Given the updated *-quality.schema.json files and SKILL.md contracts across rust, python, flutter, android, and ios quality providers
  When the engineer runs the five test_validate_*_quality.py test suites
  Then every provider schema permits capabilities "contracts", "contract_diff", and pattern "^contracts_[a-z0-9_]+$" (and rust-quality.schema.json permits "db_hygiene")
  And every provider validator accepts capability arrays using "{skills_dir}" and "{base_ref}" placeholders and documents exit code 2 mapping to status "BLOCKED"
  And all five validator test suites exit with code 0

Scenario: [CDG-HP-04] [Tier C - Integration] Lifecycle Document Contracts, Template Reference, and Verify Harness Pass
  Given the contract_map.json.tmpl template in setup-shared-contracts and the updated SKILL.md files in setup-shared-contracts, sync-shared-contracts, dev-brainstorming, and dev-designer
  When the engineer executes scripts/test_lifecycle_document_contract.py and scripts/verify.sh
  Then dev-brainstorming enforces read-only contract check/brief warnings, mandatory per-warning human confirmation, and bilingual "## Shared Contract Warnings" / "## Cảnh báo Shared Contract" persistence
  And dev-designer enforces reading "## Shared Contract Warnings", Hub task_01 Contract-First ordering, and final-task Allowed files entries for .agents/contract_sync.json and .agents/contract_map.json
  And setup-shared-contracts documents contract_map.json.tmpl and scripts/verify.sh exits with code 0
```

## Dimension 2: Edge Cases and Boundaries

```gherkin
Scenario: [CDG-EC-01] [Tier A - Unit] Anchored Multi-Level POSIX Glob Matching and Exclude Precedence
  Given .agents/contract_map.json configuring domain "lyrics-sync" with paths ["crates/**/routes/**", "src/*/dto/*.py"] and exclude ["**/tests/**"]
  When the anchored POSIX glob matcher evaluates "crates/routes/v1.rs", "crates/core/http/routes/v1/tasks.rs", "src/worker/dto/job.py", "crates/api/routes/tests/mock.rs", and "other/crates/routes/v1.rs"
  Then "crates/routes/v1.rs", "crates/core/http/routes/v1/tasks.rs", and "src/worker/dto/job.py" match domain "lyrics-sync"
  And excluded path "crates/api/routes/tests/mock.rs" and unanchored prefix path "other/crates/routes/v1.rs" do not match domain "lyrics-sync"

Scenario: [CDG-EC-02] [Tier A - Unit] Empty Diff at Merge-Base or Unmapped File Changes Pass Cleanly
  Given an initialized Hub or Satellite repository with .agents/contract_map.json where either merge-base(base_ref, HEAD) equals HEAD or commits in M..HEAD modify only "README.md"
  When the engineer invokes sync_contracts.py diff-check --json
  Then the JSON report contains status "PASS", violations [], and active_waivers []
  And the command exits with code 0

Scenario: [CDG-EC-03] [Tier A - Unit] Base-Ref CLI Override Precedence and Repeatable Domain Filter Validation
  Given .agents/contract_map.json declaring base_ref "main" and domains "lyrics-sync" and "nexus" where "nexus" has an uncovered mapped file edit relative to branch "develop" while "lyrics-sync" has zero mapped edits
  When the engineer runs sync_contracts.py diff-check --base-ref develop --domain lyrics-sync and then runs sync_contracts.py diff-check --domain nonexistent_domain
  Then the first command evaluates diff range merge-base(develop, HEAD)..HEAD restricted to "lyrics-sync" and exits with code 0
  And the second command reports unknown domain "nonexistent_domain" in blockers and exits with code 2

Scenario: [CDG-EC-04] [Tier C - Integration] Newly Added Path-Scoped Waivers With Null Gap and Documented GAP-XX Pass With Audit Output
  Given a repository where commits in M..HEAD modify mapped file "src/routes/tts.py" without contract or ack updates and append new waiver "W-001" for domain "lyrics-sync" matching ["src/routes/tts.py"] with either gap null or gap "GAP-08" present in gaps_and_rfcs.md
  When the engineer invokes sync_contracts.py diff-check --json and sync_contracts.py diff-check
  Then both invocations exit with code 0
  And active_waivers in JSON and stdout text explicitly list waiver id "W-001", domain "lyrics-sync", paths ["src/routes/tts.py"], reason, and gap value for Gate 4 and Gate 5 review

Scenario: [CDG-EC-05] [Tier C - Integration] NUL-Delimited Rename-Out Detection and Git-Quoted Filename Matching Across Hub and Satellite
  Given Hub and Satellite repositories mapping "src/api/dto/**" to domain "lyrics-sync"
  When commits in M..HEAD either rename mapped file "src/api/dto/worker.py" to unmapped path "src/internal/worker.py" or modify filename "src/api/dto/worker v2 (draft).py" requiring Git C-quoting
  And sync_contracts.py diff-check runs via git diff --no-ext-diff --no-renames --name-only -z M..HEAD first without coverage and then with a canonical contract edit (Hub) or fresh domain ack (Satellite)
  Then the uncovered runs exit with code 1 reporting "src/api/dto/worker.py" and "src/api/dto/worker v2 (draft).py" in violations
  And the covered Hub and Satellite runs exit with code 0 with status "PASS"
```

## Dimension 3: State Transitions

```gherkin
Scenario: [CDG-ST-01] [Tier C - Integration] Uncovered Mapped File Changes and Partial Waivers Transition Verdict to FAIL
  Given a Hub repository where commits in M..HEAD modify mapped files "crates/a/routes/x.rs" and "crates/a/dto/y.rs" without editing shared-contracts/lyrics-sync/ and add new waiver "W-010" covering only ["crates/a/routes/x.rs"]
  When the engineer invokes sync_contracts.py diff-check --json
  Then the JSON report transitions to status "FAIL" and lists "crates/a/dto/y.rs" under domain "lyrics-sync" in violations while omitting covered file "crates/a/routes/x.rs"
  And the command exits with code 1

Scenario: [CDG-ST-02] [Tier C - Integration] Historical Waiver Non-Masking, Mutation Rejection, and Obsolete Waiver Deletion
  Given a repository whose .agents/contract_map.json at merge-base M already contains waiver "W-OLD" for domain "lyrics-sync" and path ["crates/a/routes/x.rs"]
  When branch A modifies "crates/a/routes/x.rs" keeping "W-OLD" unchanged, branch B modifies "W-OLD" paths or reason at HEAD, and branch C removes "W-OLD" with zero uncovered mapped edits
  Then sync_contracts.py diff-check on branch A exits with code 1 reporting "crates/a/routes/x.rs" uncovered because "W-OLD" is not newly added in M..HEAD
  And sync_contracts.py diff-check on branch B exits with code 1 reporting illegal mutation of historical waiver "W-OLD"
  And sync_contracts.py diff-check on branch C exits with code 0

Scenario: [CDG-ST-03] [Tier C - Integration] Satellite Sibling-Domain Ack Isolation, Stale Snapshot Rejection, and Missing GAP-XX Failure
  Given a Satellite repository with mapped changes in domain "lyrics-sync" where either .agents/contract_sync.json in M..HEAD updated only domain "nexus", or domains["lyrics-sync"].snapshot_id at HEAD differs from the live Hub snapshot_id, or a new waiver cites gap "GAP-999" absent from gaps_and_rfcs.md
  When the engineer invokes sync_contracts.py diff-check --json
  Then the JSON report contains status "FAIL" and records the uncovered path or missing "GAP-999" violation
  And the command exits with code 1

Scenario: [CDG-ST-04] [Tier C - Integration] Baseline-Union Domain Mapping Prevents Self-Exemption While Allowing Bootstrap and Untouched Domain Retirement
  Given a repository whose baseline M:.agents/contract_map.json maps "src/api/dto/**" to domain "lyrics-sync" alongside domain "legacy-domain"
  When branch A modifies "src/api/dto/worker.py" while adding "src/api/dto/worker.py" to exclude or narrowing paths or deleting domain "lyrics-sync" at HEAD without coverage, branch B deletes untouched "legacy-domain" at HEAD, and bootstrap branch C introduces .agents/contract_map.json for the first time after M
  Then sync_contracts.py diff-check on branch A exits with code 1 reporting "src/api/dto/worker.py" under domain "lyrics-sync" via baseline-union domain evaluation
  And sync_contracts.py diff-check on branch B exits with code 0 and bootstrap branch C evaluates coverage obligations against HEAD domains without blocking on the absent baseline map
```

## Dimension 4: Async and Multi-Repo Concurrency

```gherkin
Scenario: [CDG-AR-01] [Tier C - Integration] Nested Epic Worktree Symlink Resolution During Satellite Diff-Check
  Given a Satellite repository whose root shared-contracts symlink points relatively to ../Hub/shared-contracts/lyrics-sync and an isolated git worktree at .worktrees/cdg_epic with a committed mapped change and fresh domain ack
  When the engineer invokes sync_contracts.py diff-check --repo-root .worktrees/cdg_epic --json
  Then diff-check resolves the outbound relative symlink via the primary repository root without modifying tracked files in .worktrees/cdg_epic
  And outputs status "PASS", mode "satellite", and exits with code 0

Scenario: [CDG-AR-02] [Tier A - Unit] Dirty Tracked Working Tree Fails Closed With Exit Code 2
  Given a Hub or Satellite repository that has an unstaged or staged modification to a tracked file while untracked build files exist under build/
  When the engineer invokes sync_contracts.py diff-check --json
  Then diff-check inspects git status --porcelain --untracked-files=no, outputs status "BLOCKED" with a dirty working tree blocker, and exits with code 2
```

## Dimension 5: Failures and Storage Resilience

```gherkin
Scenario: [CDG-FR-01] [Tier A - Unit] Missing or Malformed Contract Map at HEAD or Merge-Base Fails Closed With BLOCKED
  Given a repository where .agents/contract_map.json is missing at HEAD, fails schema_version 1 validation at HEAD (empty domains, duplicate waiver id, or unknown waiver domain), or contains truncated invalid JSON at merge-base M
  When the engineer invokes sync_contracts.py diff-check --json
  Then the JSON report contains status "BLOCKED" and a diagnostic message in blockers naming the missing file or schema defect
  And the command exits with code 2

Scenario: [CDG-FR-02] [Tier A - Unit] Unresolvable Base-Ref or Broken Shared-Contracts Topology Fails Closed With BLOCKED
  Given a repository where either effective_base_ref does not resolve to a git commit or shared-contracts is missing, a dangling symlink, or a 12-hop circular symlink loop
  When the engineer invokes sync_contracts.py diff-check --json
  Then the JSON report contains status "BLOCKED" and records the git merge-base or topology error in blockers
  And the command exits with code 2
```

