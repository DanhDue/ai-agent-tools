---
id: "task_01_ohk_worktree_status_and_pool_isolation"
status: "todo"
priority: "high"
assignee: null
epic: "observer-hardening-2026-11"
dueDate: null
created: "2026-11-26T22:10:00Z"
modified: "2026-11-26T22:10:00Z"
completedAt: null
labels: ["architecture", "concurrency", "worktree"]
order: "a1"
review_tier: "full"
---

# Task 1: Isolate Worktree Task Sync (`promote`, `archive-done`, `archive-epic`) and Harden Worker Pool `finalize_slot`

Epic: [observer-hardening-2026-11](observer_hardening_2026_11.md)

## Requirement Analysis

Fix three high-priority multi-worktree defects from Cluster 1:

1. **Observation `#7` (`sync_task_status.py promote` & `epic_checkout_roots`)**:
   - In `main()`, `args.command == "promote"` currently uses `checkout_roots()`, where `roots[0]` is the primary checkout rather than the isolated epic worktree holding `.devtool/epic/<epic_dir>/`.
   - Switch `promote` to `epic_checkout_roots(args.epic_dir)`, and harden `epic_checkout_roots(epic_dir)` so it skips `_is_slot_worktree(path)` and places the checkout actually containing `.devtool/epic/<epic_dir>/` at `roots[0]` (preferring `current_root` when it contains `.devtool/epic/<epic_dir>/`, otherwise promoting the matching epic worktree to index 0).
2. **Observation `#14` Part 1 (`sync_task_status.py archive-done` & `archive-epic`)**:
   - Prevent archiving Epic A from mutating sibling `.worktrees/<other_epic>` checkouts checked out on unrelated `refs/heads/epic/*` branches.
   - Switch `main()` `archive-epic` to `roots = epic_checkout_roots(args.epic_dir)`.
   - Switch `main()` `archive-done` to discover completed epic directories strictly from `current_root / ".devtool" / "features" / "done"` and archive each discovered epic via `sync_epic(epic_checkout_roots(epic_dir), epic_dir, "Done")`.
   - Keep `archive_all_done_epics(roots: list[Path]) -> list[str]` backwards compatible for direct callers while filtering out checkouts on unrelated `refs/heads/epic/*` branches when git branch metadata is available.
3. **Observation `#1` (`manage_worker_pool.py finalize_slot`)**:
   - Stop passing `:!.venv` (and other gitignored `CACHE_DIR_CANDIDATES` symlinks) to `git add -A`, which causes Git to exit 1 (`The following paths are ignored by one of your .gitignore files`).
   - Run `git add -A` first, then safely unstage excluded symlinked cache directories (`CACHE_DIR_CANDIDATES`) and `.devtool/epic/<epic_dir>/review_audit_notes*` without mutating on-disk symlinks and without touching tracked symlinks such as `shared-contracts`.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/sync_task_status.py`
- `skills/dev-implementation/resources/scripts/test_sync_task_status.py`
- `skills/dev-implementation/resources/scripts/manage_worker_pool.py`
- `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`
- `tests/test_ohk_worktree_and_pool.py` (new)

Read-only context:
- `.devtool/epic/observer_hardening_2026_11/2026-11-26-observer-hardening-design.md`
- `.devtool/epic/observer_hardening_2026_11/observer_hardening_2026_11.md`

## Design Rationale & Applicable Skills

- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.
- Reuse `epic_checkout_roots()` and `capture_slot_tree_sha()` staging semantics rather than introducing new wrapper scripts.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/sync_task_status.py`: `epic_checkout_roots` (L260-L300), `archive_epic_tasks` (L838-L918), `archive_all_done_epics` (L992-L1015), `promote_epic_tasks` (L1405-L1448), `main` (L1646-L1735).
  - `skills/dev-implementation/resources/scripts/test_sync_task_status.py`: `archive_all_done_epics` & `promote` tests (L580-L720, L1450-L1694).
  - `skills/dev-implementation/resources/scripts/manage_worker_pool.py`: `CACHE_DIR_CANDIDATES` (L49-L57), `capture_slot_tree_sha` (L576-L626), `finalize_slot` (L1593-L1760).
  - `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`: slot staging & finalize tests (L1-L311).
- **Downstream Callers**: `skills/dev-implementation/resources/scripts/test_sync_task_status.py`, `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`, `tests/test_trc_worker_pool_triage.py`, `skills/dev-implementation/resources/scripts/test_concurrent_epic_backlog.py`.
- **Target Coverage**: 100% of modified branches in `sync_task_status.py` and `manage_worker_pool.py`.

### BDD SCENARIOS

Covers: OHK-HP-01, OHK-EC-01, OHK-ST-01, OHK-FR-01

```gherkin
Scenario: [OHK-HP-01] [Tier C - Integration] Promote epic tasks inside an isolated worktree without mutating primary checkout
Given a git repository with a primary checkout on develop lacking epic "iso_epic"
And a linked worktree ".worktrees/iso_epic" on branch "epic/iso-epic" containing ".devtool/epic/iso_epic" with a "backlog" task
When "sync_task_status.py promote iso_epic" executes inside ".worktrees/iso_epic"
Then the command exits 0 and prints "Promoted"
And the task frontmatter inside ".worktrees/iso_epic" updates from "backlog" to "todo"
And the primary checkout remains clean with zero untracked or modified ".devtool/" files

Scenario: [OHK-EC-01] [Tier C - Integration] Finalize worker slot succeeds with gitignored .venv symlink and preserves tracked shared-contracts symlink
Given a worker pool slot containing a gitignored ".venv" symlink and a tracked "shared-contracts" symlink
And the slot has a valid code edit and completed task verification evidence
When "manage_worker_pool.py finalize-slot" executes on that slot
Then git staging succeeds with exit 0 without triggering ".venv is ignored by .gitignore"
And the created slot commit includes the code edit, excludes ".venv" and "review_audit_notes*", and preserves the tracked "shared-contracts" symlink intact

Scenario: [OHK-ST-01] [Tier C - Integration] Archiving or promoting Epic A never dirties concurrent sibling Epic B worktree even with inherited Epic A files
Given a git repository with primary checkout on develop, worktree ".worktrees/epic_a" on branch "epic/epic-a", and sibling worktree ".worktrees/epic_b" on branch "epic/epic-b" that inherited ".devtool/epic/epic_a/" from develop
And Epic A has completed tasks in ".worktrees/epic_a/.devtool/features/done/" while Epic B has clean tracked ".devtool/" tasks inside ".worktrees/epic_b"
When "sync_task_status.py archive-done" executes inside ".worktrees/epic_a"
Then Epic A tasks archive into ".worktrees/epic_a/.devtool/epic/epic_a/" and Epic A HLD status becomes "Done"
And "git -C .worktrees/epic_b status --porcelain" remains completely empty
When "sync_task_status.py promote epic_a" is invoked from inside ".worktrees/epic_b"
Then "epic_checkout_roots" excludes ".worktrees/epic_b" because its branch is "refs/heads/epic/epic-b" and leaves ".worktrees/epic_b" completely clean

Scenario: [OHK-FR-01] [Tier C - Integration] archive-epic called for Epic A skips unrelated Epic B worktrees even when run from primary checkout
Given a repository where primary checkout on develop has Epic A done tasks while sibling ".worktrees/epic_b" is active on "epic/epic-b"
When "sync_task_status.py archive-epic epic_a" runs from the primary checkout
Then Epic A archives cleanly in the primary checkout
And ".worktrees/epic_b" receives zero file writes or deletions
```

## Verification

| ID | Phase | Command | Expect | Needs |
|---|---|---|---|---|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_worktree_and_pool.py::test_ohk_hp_01_promote_in_isolated_worktree` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_worktree_and_pool.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m unittest skills/dev-implementation/resources/scripts/test_sync_task_status.py && python3 -m pytest -q --tb=short --maxfail=3 skills/dev-implementation/resources/scripts/test_manage_worker_pool.py skills/dev-implementation/resources/scripts/test_concurrent_epic_backlog.py tests/test_trc_worker_pool_triage.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/sync_task_status.py skills/dev-implementation/resources/scripts/test_sync_task_status.py skills/dev-implementation/resources/scripts/manage_worker_pool.py skills/dev-implementation/resources/scripts/test_manage_worker_pool.py && ruff format --check tests/test_ohk_worktree_and_pool.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && mypy --ignore-missing-imports --follow-imports=silent skills/dev-implementation/resources/scripts/sync_task_status.py skills/dev-implementation/resources/scripts/test_sync_task_status.py skills/dev-implementation/resources/scripts/manage_worker_pool.py skills/dev-implementation/resources/scripts/test_manage_worker_pool.py tests/test_ohk_worktree_and_pool.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_worktree_and_pool.py --junitxml=build/test-results/task_01.xml` | exit 0; results build/test-results/task_01.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`sync_task_status.py:260-300`)**: `epic_checkout_roots(epic_dir: str) -> list[Path]` currently retains `current_root` unconditionally at index 0 and appends worktrees whose branch matches `refs/heads/epic/<slug>` (underscore/hyphen variants).
  - **New contract**: Filter EVERY candidate checkout from `git worktree list --porcelain` — including `current_root` — by slot exclusion (`not _is_slot_worktree(path)`) AND branch ownership: a checkout whose branch starts with `refs/heads/epic/` and does NOT match `target_branches` for `epic_dir`'s slug is strictly excluded even when it inherited `.devtool/epic/<epic_dir>/` from `develop`. Resolve `slug` from eligible checkouts containing `.devtool/epic/<epic_dir>/` (checking matching `refs/heads/epic/*` worktrees first when `current_root` is on an unrelated `epic/*` branch). Order returned roots so an eligible checkout containing `.devtool/epic/<epic_dir>/` is at `roots[0]` (preferring eligible `current_root` when it owns the epic branch or is on a non-epic branch holding the epic dir, else promoting the matching `refs/heads/epic/<slug>` worktree to index 0). Add a regression test invoking `sync_task_status.py promote epic_a` and `archive-epic epic_a` from inside `.worktrees/epic_b` (on `refs/heads/epic/epic-b`) when `.worktrees/epic_b` inherited `.devtool/epic/epic_a/` from `develop`.
- **Source (`sync_task_status.py:1656-1673`, `1721-1732`)**: `archive-epic`, `archive-done`, and `promote` currently call `checkout_roots()`.
  - **New contract**:
    - `promote`: `roots = epic_checkout_roots(args.epic_dir)`.
    - `archive-epic`: `roots = epic_checkout_roots(args.epic_dir)`.
    - `archive-done`: inspect only `current_root = _current_checkout_root() or Path.cwd()` for `.devtool/features/done/` tasks; for each discovered `epic_dir`, call `sync_epic(epic_checkout_roots(epic_dir), epic_dir, "Done")`.
    - `archive_all_done_epics(roots: list[Path]) -> list[str]`: preserve function signature for direct callers; when filtering checkouts inside `archive_all_done_epics`, for each discovered `epic_dir`, skip any root in `roots` whose current git branch is `refs/heads/epic/<other>` not matching `epic_dir`'s slug (while preserving non-git `tmp_path` test roots that have no `.git`).
- **Source (`manage_worker_pool.py:1717-1732`)**: `finalize_slot` builds `add_specs` with `:!{cdir}` for symlinked `CACHE_DIR_CANDIDATES`, failing on gitignored `.venv`.
  - **New contract**: Run `git add -A` in `slot_path`, then unstage only excluded paths (`[f".devtool/epic/{epic_dir}/review_audit_notes*"] + [cdir for cdir in CACHE_DIR_CANDIDATES if (slot_path / cdir).is_symlink()]`) via `git reset -q HEAD -- <paths>` (or `git rm -r -q --cached --ignore-unmatch` for paths untracked in `HEAD`), never deleting on-disk symlinks and never touching `shared-contracts`.

## Definition of Done

- [ ] `sync_task_status.py promote`, `archive-epic`, and `archive-done` scope strictly to target epic checkouts without dirtying sibling `epic/*` worktrees (V2, V3, V6)
- [ ] `manage_worker_pool.py finalize_slot` stages cleanly with gitignored `.venv` symlink and preserves tracked `shared-contracts` symlink (V2, V3, V6)
- [ ] All unit, regression, lint, format, and type checks pass across modified scripts and test suites (V2, V3, V4, V5)
- [ ] Assigned BDD integration scenarios (`OHK-HP-01`, `OHK-EC-01`, `OHK-ST-01`, `OHK-FR-01`) pass with JUnit XML evidence (V6)

## Dependencies & Blockers

None.

## References & Rollback

- Spec: [2026-11-26-observer-hardening-design.md](2026-11-26-observer-hardening-design.md)
- HLD: [observer_hardening_2026_11.md](observer_hardening_2026_11.md)
- BDD: [bdd_scenarios.md](bdd_scenarios.md)
- Rollback: Revert this task's commit on `epic/observer-hardening-2026-11`.
