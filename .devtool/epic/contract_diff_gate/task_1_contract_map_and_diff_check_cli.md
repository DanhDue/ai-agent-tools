---
id: "task_1_contract_map_and_diff_check_cli"
status: "todo"
priority: "high"
assignee: null
epic: "contract_diff_gate"
dueDate: null
created: "2026-10-31T05:43:00Z"
modified: "2026-10-31T05:43:00Z"
completedAt: null
labels: ["contracts", "cli", "gate", "python"]
order: "a1"
---

# Task 1: Implement Contract Map Validator, Anchored Glob Matcher, and sync_contracts.py diff-check Engine

Epic: [contract_diff_gate](contract_diff_gate.en.md)

## Requirement Analysis

Extend `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` with the `diff-check` subcommand and `.agents/contract_map.json` validation, create the reference template `skills/setup-shared-contracts/resources/templates/contract_map.json.tmpl`, and author comprehensive unit and integration tests in `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py`.

1. **CLI Registration (`main` / `cmd_diff_check`)**:
   - Register `diff-check` subparser accepting `--repo-root <path>`, `--base-ref <ref>`, repeatable `--domain <name>` (`action="append"`), and `--json` (`action="store_true"`).
   - Return deterministic exit codes: `0` (`PASS`), `1` (`FAIL`), and `2` (`BLOCKED`).
2. **Contract Map Schema & Anchored Glob Engine**:
   - Parse and validate `.agents/contract_map.json`: `schema_version == 1`, non-empty `base_ref: str`, non-empty `domains: dict[str, dict]` where each domain has non-empty `paths: list[str]` and optional `exclude: list[str]`, and optional `waivers: list[dict]` (`id` unique `str`, `domain` in `domains`, non-empty `paths: list[str]`, non-empty `reason: str`, `gap: str | None`).
   - Compile POSIX-normalized repository-relative globs into full-path anchored regular expressions matching `skills/dev-implementation/resources/scripts/task_contract.py` (`**/` matches zero or more directory segments; `*` and `?` never cross `/`). A path belongs to domain `D` iff it matches at least one `domains[D].paths` pattern and zero `domains[D].exclude` patterns.
   - Author `skills/setup-shared-contracts/resources/templates/contract_map.json.tmpl` with `schema_version: 1`, `base_ref`, example `domains`, and `waivers: []`.
3. **Working Tree, Merge-Base, Union Domain Mapping, Hub & Satellite Rules, and Waiver Diffs**:
   - Validate preconditions ahead of the `M == HEAD` short-circuit: fail closed (`2` `BLOCKED`) if `.agents/contract_map.json` is missing or malformed at `HEAD`, if any `--domain` is absent from `HEAD`'s `domains`, if `git status --porcelain --untracked-files=no` is non-empty, if `git merge-base <effective_base_ref> HEAD` fails, if `resolve_topology(repo_root, domain)` fails (`TopologyError` / `ContractFormatError`), or if `mode == "satellite"` and any domain in `HEAD`'s `domains` differs from the linked `contract_dir.name` (since `setup_contracts.py link-satellite` links a single Hub domain).
   - Probe baseline file presence at `M` via `git ls-tree -r --name-only <M> -- <path>` before reading `git show <M>:<path>` (both for `.agents/contract_map.json` and `.agents/contract_sync.json`): exit `0` with empty stdout indicates genuine absence (bootstrap); any non-zero git exit from `ls-tree` or `show`, or malformed JSON / invalid schema in an existing `M:.agents/contract_map.json` or `M:.agents/contract_sync.json`, fails closed with `2` (`BLOCKED`).
   - If `M == HEAD`, emit `PASS` (`0`) with per-domain `proof: "none"`. Otherwise compute `git diff --no-ext-diff --no-renames --name-only -z M..HEAD` and split NUL-delimited UTF-8 records (`surrogateescape`) so renames/moves preserve both source and destination paths and filenames with spaces or non-ASCII characters are never C-quoted (any non-zero git exit returns `2` `BLOCKED`).
   - Evaluate domain obligations against the **union** of `HEAD` and baseline (`M:.agents/contract_map.json`) domain mappings, applying each version's own `paths` and `exclude` independently: a changed path `f` belongs to domain `D` iff it matches `head_domains[D]` (`paths` minus `exclude`) OR (when `M:.agents/contract_map.json` existed and defined `D`) `baseline_domains[D]` (`paths` minus `exclude`). When `M:.agents/contract_map.json` did not exist at `M` (bootstrap), only `head_domains` applies. If `D` existed at `M` and was removed from `HEAD`: return `1` (`FAIL`) when any changed file matched `baseline_domains[D]`, or pass `D` when zero changed files matched `baseline_domains[D]`.
   - Enforce historical waiver immutability: compare waivers in `HEAD` vs `M:.agents/contract_map.json`; mutating an existing waiver ID (`domain`, `paths`, `reason`, `gap`) returns `1` (`FAIL`); deleting obsolete waivers is allowed; only newly added waiver IDs cover changed files in `M..HEAD`.
   - When an active newly added waiver has non-null `gap`, parse `<contract_dir>/gaps_and_rfcs.md` via `parse_gaps_and_rfcs` and verify `W.gap` exists in `rfcs` with normalized status `"ACTIONABLE_PENDING"` or `"ACKNOWLEDGED_ACTIVE"`; missing or `"INACTIVE"` (`SUPERSEDED`/`REJECTED`) `GAP` citations return `1` (`FAIL`).
   - **Hub**: domain `D` with changed mapped files passes as a whole (`proof: "contract_edit"`) if `M..HEAD` touched any canonical file under `shared-contracts/<D>/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`); otherwise every changed mapped file `f` in `D` must match a newly added valid waiver for `D` (`proof: "waiver"`, else `proof: "uncovered"`).
   - **Satellite**: domain `D` with changed mapped files passes as a whole (`proof: "ack"`) if `domains[D]` in `.agents/contract_sync.json` was added or modified between `M` (`M:.agents/contract_sync.json`) and `HEAD` AND `domains[D].snapshot_id` at `HEAD` equals the live `snapshot_id` computed from resolved `shared-contracts`; otherwise every changed mapped file `f` in `D` must match a newly added valid waiver for `D` (`proof: "waiver"`, else `proof: "uncovered"`).
   - Print per-domain discharge summaries (`{"domain", "changed_files", "proof"}` in `domains`) and active newly added waivers (`id`, `domain`, `paths`, `reason`, `gap` in `active_waivers`) in both human-readable output and `--json`.

## Files

Allowed files:
- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`
- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py`
- `skills/setup-shared-contracts/resources/templates/contract_map.json.tmpl` (new)

Read-only context:
- `.devtool/epic/contract_diff_gate/contract_diff_gate.en.md` — HLD architecture and boundary matrix
- `.devtool/epic/contract_diff_gate/2026-10-31-contract-diff-gate-design.en.md` — approved Gate 1 design specification
- `skills/dev-implementation/resources/scripts/task_contract.py` — reference anchored POSIX glob semantics (`path_matches`, line 246)

## Design Rationale

- Compiling globs into anchored regular expressions avoids Python 3.12's unanchored `PurePosixPath.match()` bugs on multi-level `**` patterns while preserving zero third-party dependencies.
- Comparing `.agents/contract_map.json` and `.agents/contract_sync.json` directly against `merge-base` via `git show <M>:...` makes waiver freshness and domain-specific Satellite `ack` verification deterministic and tamper-evident.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (`compile_glob`, `path_matches_domain`, `validate_contract_map`, `cmd_diff_check`, `main`), `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py`, and `skills/setup-shared-contracts/resources/templates/contract_map.json.tmpl`.
- **Downstream Callers**: Task 2 quality provider manifests/docs and Task 3 skill documentation (`sync-shared-contracts/SKILL.md`, `setup-shared-contracts/SKILL.md`). Existing `check`, `brief`, and `ack` callers remain 100% backward-compatible.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 90\%$ branch and line coverage across `diff-check`, glob compilation, waiver diffing, and error paths.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: CDG-HP-01, CDG-HP-02, CDG-EC-01, CDG-EC-02, CDG-EC-03, CDG-EC-04, CDG-EC-05, CDG-ST-01, CDG-ST-02, CDG-ST-03, CDG-ST-04, CDG-AR-01, CDG-AR-02, CDG-FR-01, CDG-FR-02

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

Scenario: [CDG-ST-03] [Tier C - Integration] Satellite Sibling-Domain Ack Isolation, Stale Snapshot Rejection, and Missing or INACTIVE GAP-XX Failure
  Given a Satellite repository with mapped changes in domain "lyrics-sync" where either .agents/contract_sync.json in M..HEAD updated only domain "nexus", or domains["lyrics-sync"].snapshot_id at HEAD differs from the live Hub snapshot_id, or a new waiver cites gap "GAP-999" absent from gaps_and_rfcs.md or a gap whose normalized status is "INACTIVE" ("REJECTED" or "SUPERSEDED")
  When the engineer invokes sync_contracts.py diff-check --json
  Then the JSON report contains status "FAIL" and records the uncovered path or missing/inactive GAP violation
  And the command exits with code 1

Scenario: [CDG-ST-04] [Tier C - Integration] Baseline-Union Domain Mapping Prevents Self-Exemption While Allowing Bootstrap and Untouched Domain Retirement
  Given a repository whose baseline M:.agents/contract_map.json maps "src/api/dto/**" to domain "lyrics-sync" alongside domain "legacy-domain"
  When branch A modifies "src/api/dto/worker.py" while either adding "src/api/dto/worker.py" to exclude or narrowing paths without coverage, or deleting domain "lyrics-sync" at HEAD, branch B deletes untouched "legacy-domain" at HEAD, and bootstrap branch C introduces .agents/contract_map.json for the first time after M
  Then sync_contracts.py diff-check on branch A exits with code 1 reporting "src/api/dto/worker.py" under domain "lyrics-sync" via baseline-union domain evaluation
  And sync_contracts.py diff-check on branch B exits with code 0 and bootstrap branch C evaluates coverage obligations against HEAD domains without blocking on the absent baseline map

Scenario: [CDG-AR-01] [Tier C - Integration] Nested Epic Worktree Symlink Resolution During Satellite Diff-Check
  Given a Satellite repository whose root shared-contracts symlink points relatively to ../Hub/shared-contracts/lyrics-sync and an isolated git worktree at .worktrees/cdg_epic with a committed mapped change and fresh domain ack
  When the engineer invokes sync_contracts.py diff-check --repo-root .worktrees/cdg_epic --json
  Then diff-check resolves the outbound relative symlink via the primary repository root without modifying tracked files in .worktrees/cdg_epic
  And outputs status "PASS", mode "satellite", and exits with code 0

Scenario: [CDG-AR-02] [Tier A - Unit] Dirty Tracked Working Tree Fails Closed With Exit Code 2
  Given a Hub or Satellite repository that has an unstaged or staged modification to a tracked file while untracked build files exist under build/
  When the engineer invokes sync_contracts.py diff-check --json
  Then diff-check inspects git status --porcelain --untracked-files=no, outputs status "BLOCKED" with a dirty working tree blocker, and exits with code 2

Scenario: [CDG-FR-01] [Tier A - Unit] Missing or Malformed Contract Map at HEAD or Merge-Base Fails Closed With BLOCKED
  Given a repository where .agents/contract_map.json is missing at HEAD, fails schema_version 1 validation at HEAD (empty domains, duplicate waiver id, or unknown waiver domain), or contains truncated invalid JSON at merge-base M
  When the engineer invokes sync_contracts.py diff-check --json
  Then the JSON report contains status "BLOCKED" and a diagnostic message in blockers naming the missing file or schema defect
  And the command exits with code 2

Scenario: [CDG-FR-02] [Tier A - Unit] Unresolvable Base-Ref, Satellite Unlinked Domain, or Broken Shared-Contracts Topology Fails Closed With BLOCKED
  Given a repository where effective_base_ref does not resolve to a git commit, a Satellite contract_map.json declares a domain other than its linked shared-contracts target, or shared-contracts is missing, a dangling symlink, or a 12-hop circular symlink loop
  When the engineer invokes sync_contracts.py diff-check --json
  Then the JSON report contains status "BLOCKED" and records the git merge-base, unlinked Satellite domain, or topology error in blockers
  And the command exits with code 2
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_cdg_hp_01` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_cdg_` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0; contains "OK" | — |
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
- Adding `diff-check` alters the CLI behavior or exit codes of existing `check`, `brief`, or `ack` subcommands.

## Decisions Already Made

- Grounded existing contracts in `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`: reuse `CANONICAL_FILES`, `TopologyError`, `ContractFormatError`, `resolve_topology(repo_root: Path, domain: str) -> dict[str, Any]`, `compute_file_hash(path: Path) -> str`, `compute_snapshot_id(file_hashes: dict[str, str]) -> str`, `parse_gaps_and_rfcs(content: str) -> dict[str, Any]`, and `main(argv: list[str] | None = None) -> int`.
- New frozen CLI contract: `sync_contracts.py diff-check [--repo-root <path>] [--base-ref <ref>] [--domain <name>] [--json]` returning `0` (`PASS`), `1` (`FAIL`), or `2` (`BLOCKED`).
- New frozen JSON output schema on `--json`: `{"status": "PASS" | "FAIL" | "BLOCKED", "mode": "hub" | "satellite" | None, "base_ref": str | None, "merge_base": str | None, "head_sha": str | None, "domains": list[dict[str, Any]], "violations": list[dict[str, str]], "active_waivers": list[dict[str, Any]], "blockers": list[str]}` where each entry in `"domains"` has shape `{"domain": str, "changed_files": list[str], "proof": "none" | "contract_edit" | "ack" | "waiver" | "uncovered"}`.
- Anchored POSIX glob compiler converts `**/` to `(?:[^/]+/)*`, trailing `/**` to `(?:/.*)?`, standalone `**` to `.*`, `*` to `[^/]*`, and `?` to `[^/]`, anchored with `\A...\Z`.
- Baseline file presence at `M` (`.agents/contract_map.json` and `.agents/contract_sync.json`) is probed via `git ls-tree -r --name-only <M> -- <path>` before `git show <M>:<path>` so genuine bootstrap absence is distinguished from git failures (`2` `BLOCKED`). Changed paths in `M..HEAD` are extracted strictly via `git diff --no-ext-diff --no-renames --name-only -z M..HEAD` (NUL-delimited UTF-8 `surrogateescape`), and domain membership evaluates against `union(M, HEAD)` domain mappings (applying each version's `paths` and `exclude` independently, with bootstrap fallback when `M:.agents/contract_map.json` is absent).
- Reference template `skills/setup-shared-contracts/resources/templates/contract_map.json.tmpl` parses as syntactically sound JSON documenting `schema_version: 1`, `base_ref`, `domains`, and `waivers: []`.

## Definition of Done

- `sync_contracts.py diff-check` and `contract_map.json.tmpl` are implemented and pass all 15 `CDG-*` scenarios plus existing `SYC-*` regressions (V2, V3).
- `ruff check` and `mypy --strict` pass with zero errors on `sync_contracts.py` and `test_sync_contracts.py` (V4, V5).
- JUnit XML report `build/test-results/task_1.xml` is written and passes all `CDG-*` cases assigned to Task 1 (V6).
- Active waiver output format and code cleanliness reviewed at Kanban sign-off (Gate 5).

## Dependencies & Blockers

- None.

## References & Rollback

- Spec: `.devtool/epic/contract_diff_gate/2026-10-31-contract-diff-gate-design.en.md`
- HLD: `.devtool/epic/contract_diff_gate/contract_diff_gate.en.md`
- Rollback: Revert edits to `sync_contracts.py` and `test_sync_contracts.py` and remove `skills/setup-shared-contracts/resources/templates/contract_map.json.tmpl`.
