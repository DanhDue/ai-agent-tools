---
id: "task_05_worker_pool_cow_mounts_and_suffix_triage"
status: "todo"
priority: "high"
assignee: null
epic: "polyglot_lifecycle_and_quality_architecture"
dueDate: null
created: "2026-11-27T09:18:00+07:00"
modified: "2026-11-27T09:18:00+07:00"
completedAt: null
labels: ["dev-implementation", "worker-pool", "polyglot", "triage"]
order: "a05"
review_tier: "full"
---

# Task 05: Wire Worker Pool `apfs_cow_tree` Mounts and Suffix-Scoped `triage-fix` into `manage_worker_pool.py`

Epic: [polyglot_lifecycle_and_quality_architecture](polyglot_lifecycle_and_quality_architecture.md)

## Requirement Analysis

Wire `skills/dev-implementation/resources/scripts/manage_worker_pool.py` to Task 01's `_stack_lifecycle_registry.py` (`PoolWorkspaceStrategy` and `TriageSurfaceRegistry`):

1. Replace unconditional `CACHE_DIR_CANDIDATES` symlinking in `link_shared_caches` (`L193`) with `PoolWorkspaceStrategy`:
   - Keep O(1) `symlink` for heavy binary/package caches (`target`, `node_modules`, `.astro`, `.venv`, `.gradle`, `.build`, `Pods`).
   - Use `apfs_cow_tree` (`cp -c -R` on Darwin, automatic `shutil.copytree`/`shutil.copy2` fallback on Linux or cross-volume failure — NEVER symlinking `.dart_tool`) for root `.dart_tool`, nested Melos `packages/*/.dart_tool`, `features/*/.dart_tool`, `bricks/*/hooks/.dart_tool`, gitignored `secureFiles/`, `local.properties`, `android/local.properties`, `*.xcconfig`, plus validated custom `"pool_mounts"` entries in `.agents/quality/check_quality.json`.
   - Protect all active mounted paths (both `symlink` and `cow_copy`) across `sync_slot` (`git clean -fd -e`), `capture_slot_tree_sha` (temp index exclusion), `triage_fix_slot` (`:(exclude)` pathspecs), and `finalize_slot` (unstage before commit so secrets and `.dart_tool` are never committed).
2. Replace flat global surface regexes and Python-centric `_is_test_file` in `manage_worker_pool.py` (`L79-L108`, `L1050-L1197`) with `TriageSurfaceRegistry.from_repo(main_wt)` so every surface rule and test-file/assertion check is strictly suffix-scoped across `.dart`, `.rs`, `.ts/.tsx/.js/.mjs/.astro`, `.kt/.kts`, `.swift`, and `.py`, honoring optional `"triage_surfaces"` manifest overrides.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/manage_worker_pool.py`
- `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`
- `tests/test_plq_worker_pool_polyglot.py` (new)

Read-only context:
- `.devtool/epic/polyglot_lifecycle_and_quality_architecture/polyglot_lifecycle_and_quality_architecture.md`
- `.devtool/epic/polyglot_lifecycle_and_quality_architecture/bdd_scenarios.md`
- `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py` (new)
- `tests/test_trc_worker_pool_triage.py`
- `tests/test_ohk_worktree_and_pool.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development` and `d3nexus:python-quality-check`.
- Never copy tracked files into `cow_copy` targets that might conflict with git; copy only existing gitignored directories/files and explicitly exclude every materialized mount from `git clean`, `capture_slot_tree_sha`, `triage-fix`, and `finalize_slot` commits.
- Preserve all existing Python Tier 1 triage trigger codes (`TIER1_TRIGGER_ORDER`) and backward-compatible public helper signatures (`link_shared_caches`, `_is_test_file`, `_classify_tier1_diff`).

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/manage_worker_pool.py` (`CACHE_DIR_CANDIDATES` `L49-L65`, `_PUBLIC_SIGNATURE_RES`..`_TEST_SKIP_RE` `L79-L115`, `link_shared_caches` `L193-L235`, `capture_slot_tree_sha` `L576-L626`, `sync_slot` `L783-L880`, `_is_test_file` `L1050-L1058`, `_classify_tier1_diff` `L1079-L1197`, `triage_fix_slot` `L1200-L1315`, `finalize_slot` `L1593-L1775`)
  - `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py` (`L1-L429`)
  - `tests/test_plq_worker_pool_polyglot.py` (new): Integration tests for `PLQ-HP-05`, `PLQ-ST-03`, `PLQ-ST-04`, `PLQ-AR-04`, `PLQ-FR-05`.
- **Downstream Callers**: `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`, `tests/test_trc_worker_pool_triage.py`, `tests/test_ohk_worktree_and_pool.py`, `tests/test_trc_runner_and_acceptance.py`.
- **Cross-Platform Bridges**: None.
- **Target Coverage Threshold**: >= 90% on modified pool mount, clean/stage exclusion, and suffix triage branches; 100% on `cp -c -R` fallback and secret unstaging paths.

### BDD SCENARIOS

Covers: PLQ-HP-05, PLQ-ST-03, PLQ-ST-04, PLQ-AR-04, PLQ-FR-05

```gherkin
Scenario: [PLQ-HP-05] [Tier C - Integration] Worker pool materializes symlink caches and APFS/copytree COW trees without symlinking .dart_tool
Given a main worktree containing target/, node_modules/, .dart_tool/, packages/core/.dart_tool/, features/home/.dart_tool/, bricks/feat/hooks/.dart_tool/, and gitignored secureFiles/dev.json and android/local.properties
When manage_worker_pool.py creates and syncs slot 1
Then target and node_modules in slot 1 are symlinks pointing to the main worktree
And root .dart_tool, packages/core/.dart_tool, features/home/.dart_tool, bricks/feat/hooks/.dart_tool, secureFiles, and android/local.properties in slot 1 are real copied directories or files (is_symlink() is False)
And git status --porcelain inside slot 1 remains clean with zero untracked secret or .dart_tool noise

Scenario: [PLQ-ST-03] [Tier C - Integration] Repeated sync_slot preserves COW mounts and never deletes them during git clean
Given slot 1 with materialized .dart_tool, packages/core/.dart_tool, and gitignored secureFiles/dev.json plus an unrelated stale untracked file "scratch.tmp"
When manage_worker_pool.py runs sync_slot twice consecutively on slot 1
Then "scratch.tmp" is removed by git clean -fd
And .dart_tool, packages/core/.dart_tool, and secureFiles/dev.json remain intact as non-symlink directories/files after both syncs

Scenario: [PLQ-ST-04] [Tier C - Integration] finalize_slot unstages ignored mounts while committing edits to tracked xcconfig files
Given slot 1 containing a legitimate source edit, an edited git-tracked "ios/Flutter/Debug.xcconfig", plus materialized gitignored cow_copy mounts (.dart_tool, secureFiles/dev.json, android/local.properties) and a custom gitignored pool_mounts cow_copy entry
When manage_worker_pool.py runs capture_slot_tree_sha and finalize_slot on slot 1
Then the resulting slot commit contains both the legitimate source edit and the tracked "ios/Flutter/Debug.xcconfig" edit
And git show --stat HEAD contains zero paths from .dart_tool, secureFiles, android/local.properties, or custom gitignored pool_mounts

Scenario: [PLQ-AR-04] [Tier C - Integration] Polyglot _is_test_file classifies test files and assertion weakening accurately per language
Given a Fix Pass 1 diff in manage_worker_pool.py triage-fix that removes an expect() call or adds skip: true in a Dart *_test.dart file, #[ignore] in a Rust *_test.rs file, .skip( in a *.spec.ts file, @Ignore in a *Test.kt file, or XCTSkip in a *Tests.swift file
When triage_fix_slot evaluates the diff
Then each case classifies the file as a test file (0 non-test changed lines) and fires "TEST_ASSERTION_WEAKENED" with tier1_status "HIGH_RISK"

Scenario: [PLQ-FR-05] [Tier C - Integration] APFS copy-on-write failure gracefully falls back to shutil.copytree on non-APFS or Linux hosts
Given a simulated environment where `cp -c -R` returns exit code 1 (e.g., cross-volume or Linux host)
When manage_worker_pool.py materializes .dart_tool and secureFiles/dev.json into slot 1
Then PoolWorkspaceStrategy falls back to shutil.copytree / shutil.copy2 automatically
And slot 1 contains complete, readable, non-symlink copies of .dart_tool and secureFiles/dev.json with zero exceptions
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_plq_worker_pool_polyglot.py::test_plq_hp_05_worker_pool_symlink_and_cow_mounts` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_plq_worker_pool_polyglot.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 skills/dev-implementation/resources/scripts/test_manage_worker_pool.py tests/test_trc_worker_pool_triage.py tests/test_ohk_worktree_and_pool.py tests/test_trc_runner_and_acceptance.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/manage_worker_pool.py skills/dev-implementation/resources/scripts/test_manage_worker_pool.py tests/test_plq_worker_pool_polyglot.py && ruff format --check skills/dev-implementation/resources/scripts/manage_worker_pool.py skills/dev-implementation/resources/scripts/test_manage_worker_pool.py tests/test_plq_worker_pool_polyglot.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/manage_worker_pool.py skills/dev-implementation/resources/scripts/test_manage_worker_pool.py tests/test_plq_worker_pool_polyglot.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_plq_worker_pool_polyglot.py --junitxml=build/test-results/task_05.xml` | exit 0; results build/test-results/task_05.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`manage_worker_pool.py` `L49`, `L79-L108`, `L193`, `L576`, `L783`, `L1050`, `L1079`, `L1200`, `L1593`)**: Currently symlinks `.dart_tool` via `CACHE_DIR_CANDIDATES` and applies flat Python surface regexes in `_classify_tier1_diff`.
- **New contract**:
  - `CACHE_DIR_CANDIDATES` retains the O(1) symlink cache names (`target`, `node_modules`, `.astro`, `.venv`, `.gradle`, `.build`, `Pods`) and removes `.dart_tool` from symlink candidates; `link_shared_caches(main_wt, slot_wt)` delegates to `PoolWorkspaceStrategy.materialize_mounts(main_wt, slot_wt)` and returns the sorted list of materialized relative paths (preserving its `list[str]` return type for backwards compatibility with `test_manage_worker_pool.py`).
  - `sync_slot`, `capture_slot_tree_sha`, `triage_fix_slot`, and `finalize_slot` query `PoolWorkspaceStrategy.get_excluded_relpaths(main_wt, slot_path)` which returns ONLY materialized symlinked or untracked+gitignored `cow_copy` paths (never tracked files such as `ios/Flutter/Debug.xcconfig`), excluding them from `git clean -fd`, temp index snapshots, `triage-fix` diffs, and `finalize_slot` staging.
  - `_classify_tier1_diff(numstat_raw, unified_text, *, registry=None)` defaults to `TriageSurfaceRegistry.default()` when `registry` is `None` (preserving existing unit-test call signature) and uses `TriageSurfaceRegistry.from_repo(main_wt)` inside `triage_fix_slot`.
  - `_is_test_file(rel_path)` delegates to `TriageSurfaceRegistry.is_test_file(rel_path)` so Dart, Rust, TS/JS, Kotlin, Swift, and Python test files are all recognized consistently.

## Definition of Done

- [ ] `manage_worker_pool.py` uses `PoolWorkspaceStrategy` (`symlink` vs `apfs_cow_tree` with Linux/non-APFS fallback) and never symlinks `.dart_tool` (V2, V5)
- [ ] All symlink and `cow_copy` mounts survive `sync_slot` (`git clean -fd`) and are never committed by `finalize_slot` (V2, V5)
- [ ] `triage_fix_slot` and `_is_test_file` delegate to suffix-scoped `TriageSurfaceRegistry` with manifest override support and zero cross-stack false positives (V2, V3, V5)
- [ ] Existing `test_manage_worker_pool.py`, `test_trc_worker_pool_triage.py`, and `test_ohk_worktree_and_pool.py` pass without regressions (V3)
- [ ] `ruff check`, `ruff format --check`, and `mypy` pass across all Allowed files (V4)
- [ ] Fresh JUnit XML report written to `build/test-results/task_05.xml` containing all 5 assigned scenario IDs (V5)

## Dependencies & Blockers

- Blocked by [Task 01](task_01_stack_lifecycle_registry.md) (consumes `_stack_lifecycle_registry.py`).
- Wave 2 — runs in parallel with Task 04.

## References & Rollback

- Reference HLD: [polyglot_lifecycle_and_quality_architecture.md](polyglot_lifecycle_and_quality_architecture.md)
- Rollback: Revert edits to `manage_worker_pool.py` and `test_manage_worker_pool.py`; delete `tests/test_plq_worker_pool_polyglot.py`.
