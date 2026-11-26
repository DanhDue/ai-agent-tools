---
id: "task_02_ohk_revise_reanchor_and_replay_skip"
status: "done"
priority: "high"
assignee: null
epic: "observer-hardening-2026-11"
dueDate: null
created: "2026-11-26T22:10:00Z"
modified: "2026-11-26T16:32:42Z"
completedAt: "2026-11-26T16:32:42Z"
labels: ["architecture", "readiness", "replay"]
order: "a2"
review_tier: "full"
---

# Task 2: Support Post-Rebase `package_epic.py --revise` Re-Anchoring (`--reanchoring`) and Contract-Task `R8 --replay` Self-Skip

Epic: [observer-hardening-2026-11](../../epic/observer_hardening_2026_11/observer_hardening_2026_11.md)

## Requirement Analysis

Fix two lifecycle readiness and replay gate defects:

1. **Observation `#10` (`package_epic.py --revise` & `check_epic_readiness.py` `R7`)**:
   - After `integrate_branch.py rebase` rewrites commits on `epic/<slug>`, the old `Design commit` SHA in `handoff.md` is no longer an ancestor of `HEAD`. Running `package_epic.py <epic_dir> --revise --reason "..."` fails its own preflight `check_epic_readiness.py` on `R7` before re-anchoring `Design commit`.
   - Add `--reanchoring` to `check_epic_readiness.py` (`Context.reanchoring = False` by default) so `check_metadata` skips ONLY the `git merge-base --is-ancestor <design_commit> HEAD` check when `--reanchoring` is set, keeping all other `R7` assertions intact.
   - Update `package_epic.py` to pass `--reanchoring` whenever `revise=True`.
2. **Observation `#6` (`replay_task_text.py` & `check_epic_readiness.py` `R8 --replay`)**:
   - On standard contract-based Kanban tasks that declare `(new)` test files in `Allowed files` (to be authored by Role 2.3 in Stage 3) without embedding literal `Create`/`Replace in`/`Insert in` test-creation directives in task prose, `replay_epic_in_worktree()` runs `RED` pytest rows against nonexistent paths, producing pytest exit 4 (`R8 FAIL`).
   - Update `replay_task_text.py` and `check_epic_readiness.py` so tasks with zero test-creation directives for their `(new)` test files (or zero directives overall on contract-based tasks) gracefully skip `R8` (`R8 SKIP`), while directive-bearing tasks still run strict RED/GREEN replay and fail on broken patches.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/package_epic.py`
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
- `skills/dev-implementation/resources/scripts/replay_task_text.py`
- `skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py`
- `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py`
- `tests/test_ohk_revise_and_replay.py` (new)

Read-only context:
- `.devtool/epic/observer_hardening_2026_11/2026-11-26-observer-hardening-design.md`
- `.devtool/epic/observer_hardening_2026_11/observer_hardening_2026_11.md`

## Design Rationale & Applicable Skills

- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.
- Keep normal `check_epic_readiness.py` (without `--reanchoring`) and directive-bearing `--replay` runs 100% fail-closed.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/package_epic.py`: `package_epic` (L350-L493).
  - `skills/dev-implementation/resources/scripts/check_epic_readiness.py`: `Context`, `check_metadata` (L660-L735), `check_baseline` (L737-L800), `render_report` / `main` (L841-L1032).
  - `skills/dev-implementation/resources/scripts/replay_task_text.py`: `parse_task_directives` (L96-L159), `replay_task` (L252-L310), `replay_epic_in_worktree` (L312-L369).
  - `skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py`: revise & re-anchor tests (L1-L339).
  - `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py`: R7 & R8 tests (L600-L939).
  - `skills/dev-implementation/resources/scripts/test_replay_and_measure.py`: replay tests (L1-L410).
- **Downstream Callers**: `skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py`, `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py`, `skills/dev-implementation/resources/scripts/test_replay_and_measure.py`.
- **Target Coverage**: 100% of modified branches across `package_epic.py`, `check_epic_readiness.py`, and `replay_task_text.py`.

### BDD SCENARIOS

Covers: OHK-HP-02, OHK-EC-02, OHK-ST-02

```gherkin
Scenario: [OHK-HP-02] [Tier C - Integration] Re-anchor handoff after rebasing an active Stage 3 epic branch
Given an epic packaged with handoff.md referencing pre-rebase Design commit SHA "old_sha"
And the epic branch is rebased onto an advanced base branch so "old_sha" is no longer an ancestor of HEAD
When "package_epic.py <epic_dir> --revise --reason 'Rebased onto base'" executes
Then check_epic_readiness.py runs with "--reanchoring" and exits 0
And handoff.md updates Design commit to the new rebased short HEAD SHA
And running "check_epic_readiness.py --post-design <epic_dir>" afterwards exits 0 with "R7 PASS"

Scenario: [OHK-EC-02] [Tier C - Integration] Check epic readiness --replay skips R8 when contract-based tasks have zero test-creation directives
Given an epic whose task files declare "(new)" pytest test paths in Allowed files and RED rows targeting those not-yet-created tests
And the task files embed zero "Create", "Replace in", or "Insert in" directives for test files
When "check_epic_readiness.py <epic_dir> --replay" executes
Then check_epic_readiness.py exits 0
And output contains "R8 SKIP" rather than failing with pytest exit 4

Scenario: [OHK-ST-02] [Tier C - Integration] Replay engine still enforces strict RED and GREEN checks on directive-bearing tasks
Given an epic task embedding literal "Create tests/test_sample_replay.py:" and "Create src_replay_mod.py:" directives
When "check_epic_readiness.py <epic_dir> --replay" executes with valid failing RED and passing GREEN rows
Then R8 reports "R8 PASS" and exits 0
When the embedded implementation directive breaks the GREEN test
Then R8 reports "R8 FAIL" and exits 1
```

## Verification

| ID | Phase | Command | Expect | Needs |
|---|---|---|---|---|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_revise_and_replay.py::test_ohk_hp_02_package_revise_after_rebase` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_revise_and_replay.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py && python3 -m pytest -q --tb=short --maxfail=3 skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py skills/dev-implementation/resources/scripts/test_replay_and_measure.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/package_epic.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/replay_task_text.py skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py && ruff format --check tests/test_ohk_revise_and_replay.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && mypy --ignore-missing-imports --follow-imports=silent skills/dev-implementation/resources/scripts/package_epic.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/replay_task_text.py skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py tests/test_ohk_revise_and_replay.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_revise_and_replay.py --junitxml=build/test-results/task_02.xml` | exit 0; results build/test-results/task_02.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`check_epic_readiness.py:685-708`)**: `check_metadata` checks `git merge-base --is-ancestor design_commit HEAD` whenever `handoff.md` exists and `design_commit != "uncommitted"`.
  - **New contract**: Add `reanchoring: bool = False` on `Context` and `--reanchoring` CLI flag. When `ctx.reanchoring` is `True`, skip only the `git merge-base --is-ancestor` subprocess call; retain missing `Design commit` line check, HLD status check, and task metadata checks.
- **Source (`package_epic.py:380-391`)**: `package_epic()` constructs `readiness_cmd = [sys.executable, str(READINESS_SCRIPT)]` and optionally appends `--post-design`.
  - **New contract**: Whenever `revise` is `True`, append `"--reanchoring"` to `readiness_cmd`.
- **Source (`replay_task_text.py:252-368`, `check_epic_readiness.py:737-755`, `863-872`)**: `replay_task()` runs `RED` rows even when `test_directives` is empty and `(new)` test files do not exist on disk.
  - **New contract**: Add helper `has_uncreated_new_test_targets(root: Path, task_text: str, directives: list[Directive]) -> bool` inspecting `parse_allowed_files(task_text)` for `(new)` test files (using `is_test_file(ap.pattern)`) that are absent from `root` and not created by any directive in `directives`. When `replay_epic_in_worktree()` finds that a task has zero test-creation directives for its `(new)` test files, skip replaying that task; if all tasks in the epic were skipped (0 replayed, >=1 skipped), return `(0, ["SKIP: no literal test-creation directives for (new) test files"])` and render `R8 SKIP (...)` in `check_epic_readiness.py` (exit 0). Any task that DOES embed test directives executes strict `RED` -> `GREEN` -> `REGRESSION` -> `TIER-B` -> `TIER-C` replay and fails `R8` on any error.

## Definition of Done

- [x] `package_epic.py --revise` passes `--reanchoring` and re-anchors `handoff.md` after rebase while normal `R7` still fails on non-ancestor SHAs (V2, V3, V6) — exit 0, 6 passed
- [x] `check_epic_readiness.py --replay` emits `R8 SKIP` (exit 0) for contract-based `(new)` tasks without test directives and enforces `R8 PASS`/`R8 FAIL` on directive-bearing tasks (V2, V3, V6) — exit 0, 6 passed
- [x] All regression, lint, format, and type checks pass across modified scripts and test suites (V2, V3, V4, V5) — exit 0, ruff + mypy + regressions passed
- [x] Assigned BDD integration scenarios (`OHK-HP-02`, `OHK-EC-02`, `OHK-ST-02`) pass with JUnit XML evidence (V6) — exit 0, 3/3 covered in build/test-results/task_02.xml

## Dependencies & Blockers

None.

## References & Rollback

- Spec: [2026-11-26-observer-hardening-design.md](../../epic/observer_hardening_2026_11/2026-11-26-observer-hardening-design.md)
- HLD: [observer_hardening_2026_11.md](../../epic/observer_hardening_2026_11/observer_hardening_2026_11.md)
- BDD: [bdd_scenarios.md](../../epic/observer_hardening_2026_11/bdd_scenarios.md)
- Rollback: Revert this task's commit on `epic/observer-hardening-2026-11`.
