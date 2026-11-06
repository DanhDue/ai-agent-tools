---
id: "task_02_conflict_aware_epic_promotion"
status: "todo"
priority: "high"
assignee: null
epic: "multi-epic-orchestration-and-governance"
dueDate: null
created: "2026-11-06T04:25:00Z"
modified: "2026-11-06T20:07:41Z"
completedAt: null
labels: ["orchestration", "kanban", "concurrency"]
order: "c2"
---

# Task 02: Conflict-Aware Concurrent Epic Backlog and Bulk Task Promotion

Epic: [multi_epic_orchestration_and_governance](multi_epic_orchestration_and_governance.en.md)

## Requirement Analysis

Resolve Observation #0014:
1. Previously, any active task of another epic in `.devtool/features/` forced new epics into `status: "backlog"` even when the two epics touched completely disjoint sets of `Allowed files`.
2. Promoting a queued epic from `backlog` to `todo` required invoking `sync_task_status.py task <id> todo` manually for each task, with no automated pre-check for unfinished `Depends on epic:` prerequisites or active `Allowed files` overlaps.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/sync_task_status.py`
- `skills/dev-implementation/resources/scripts/test_concurrent_epic_backlog.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/task_contract.py` (`parse_allowed_files`, `path_matches`, `resolve_prerequisite_epic_dirs`)
- `.devtool/epic/multi_epic_orchestration_and_governance/multi_epic_orchestration_and_governance.en.md` (HLD specification)

## Design Rationale

Applicable skills: `python-quality-check`, `test-driven-development`.
1. `check_epic_prerequisites(root: Path, epic_dir: str) -> list[str]` in `sync_task_status.py` reads `<epic_dir>.en.md`, resolves `prereq_dirs, errors = tc.resolve_prerequisite_epic_dirs(root, hld_text, epic_dir)`, and checks whether each prerequisite epic has `Status: Done` (or all its tasks in `status: "done"`), returning a list of unfinished prerequisite epic names or resolution errors.
2. `check_epic_file_conflicts(root: Path, epic_dir: str) -> dict[str, list[str]]` collects all `Allowed files` patterns across `<epic_dir>`'s tasks and compares them against `Allowed files` patterns of all active (`status` in `("todo", "in-progress", "review")`) tasks in `.devtool/features/task_*.md` belonging to other epics using `tc.path_matches(pat_a, pat_b) or tc.path_matches(pat_b, pat_a)`, ignoring `done` and `backlog` tasks.
3. `promote_epic_tasks(roots: list[Path], epic_dir: str, *, force: bool = False) -> tuple[list[Path], list[str]]` verifies `check_epic_prerequisites()` and `check_epic_file_conflicts()` on `roots[0]` (unless `force=True`), then transitions all `backlog` tasks of `<epic_dir>` across `roots` (`.devtool/epic/<epic_dir>/` and `.devtool/features/`) to `todo`, leaving an existing `Packaged …` HLD `Status` untouched and only rewriting a `Queued (backlog)` HLD `Status` to `f"Packaged ({today_iso})"`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/sync_task_status.py`: `main`, new `check_epic_prerequisites`, new `check_epic_file_conflicts`, and new `promote_epic_tasks`.
- **Downstream Callers**: `dev-designer` and `dev-implementation` entry-point checks.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on `check_epic_prerequisites`, `check_epic_file_conflicts`, and `promote_epic_tasks`.

### BDD SCENARIOS

Covers: MEO-HP-02, MEO-EC-02, MEO-ST-01

```gherkin
  Scenario: [MEO-HP-02] [Tier C - Integration] Conflict-aware check-conflicts and promote transition a disjoint epic from backlog to todo in one command
    Given an active epic "epic_alpha" with tasks in "todo" touching "src/alpha.py"
    And a queued epic "epic_gamma" with tasks in "backlog" touching "src/gamma.py" and no unfinished prerequisites
    When "sync_task_status.py check-conflicts epic_gamma" runs
    Then it reports "0 conflicts — safe for concurrent execution" and exits with code 0
    And when "sync_task_status.py promote epic_gamma" runs
    Then all "backlog" tasks of "epic_gamma" in ".devtool/epic/epic_gamma/" and ".devtool/features/" transition to "todo"

  Scenario: [MEO-EC-02] [Tier A - Unit] check_epic_file_conflicts ignores done tasks of other epics while detecting glob-vs-literal overlaps on active tasks
    Given "epic_done" has only "done" tasks touching "src/shared/core.py"
    And "epic_active" has an "in-progress" task with Allowed file glob "src/shared/*.py"
    When "check_epic_file_conflicts()" evaluates "epic_candidate" whose task touches "src/shared/core.py"
    Then it ignores "epic_done" and reports a conflict only against "epic_active" on "src/shared/core.py"

  Scenario: [MEO-ST-01] [Tier A - Unit] sync_task_status.py promote blocks on unfinished prerequisites or active file conflicts unless --force is supplied
    Given "epic_beta" depends on "epic_alpha" whose status is "In Progress"
    When "sync_task_status.py promote epic_beta" is executed without "--force"
    Then it exits with code 1 and leaves "epic_beta" tasks in "backlog"
    And when "epic_alpha" transitions to "Done" (or "--force" is passed), "sync_task_status.py promote epic_beta" transitions all "epic_beta" tasks to "todo" and exits 0
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_concurrent_epic_backlog.py::test_MEO_HP_02_check_conflicts_and_promote` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_concurrent_epic_backlog.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/sync_task_status.py skills/dev-implementation/resources/scripts/test_concurrent_epic_backlog.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/sync_task_status.py --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_concurrent_epic_backlog.py --junitxml=build/test-results/task_02_epic_promotion.xml` | exit 0; results build/test-results/task_02_epic_promotion.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- In `skills/dev-implementation/resources/scripts/sync_task_status.py`:
  - `check_epic_prerequisites(root: Path, epic_dir: str) -> list[str]`:
    - Reads `hld_path = root / ".devtool" / "epic" / epic_dir / f"{epic_dir}.en.md"`.
    - Calls `prereq_dirs, errors = tc.resolve_prerequisite_epic_dirs(root, hld_text, epic_dir)` (returning `errors` if non-empty).
    - For each `p_dir` in `prereq_dirs`: checks if `p_dir`'s HLD `Status` starts with `"Done"` / `"Hoàn thành"` OR all `task_*.md` files in `.devtool/epic/<p_dir>/` have `status: "done"` in frontmatter; if not, appends `f"prerequisite epic '{p_dir}' is not Done"`.
  - `check_epic_file_conflicts(root: Path, epic_dir: str) -> dict[str, list[str]]`:
    - Reads all `task_*.md` files in `root / ".devtool" / "epic" / epic_dir` and collects `target_patterns = [entry.pattern for task in tasks for entry in tc.parse_allowed_files(task)]`.
    - Scans `root / ".devtool" / "features" / "task_*.md"` (excluding `done/`): for each task whose `status` in frontmatter is in `("todo", "in-progress", "review")` and whose `epic` slug differs from `find_epic_slug(root, epic_dir)`, checks each `other_pat` in `tc.parse_allowed_files(other_text)` against `target_patterns` using `tc.path_matches(t_pat, other_pat) or tc.path_matches(other_pat, t_pat)`.
    - Returns `{other_epic_slug: sorted(overlapping_patterns)}` for all epics with at least one overlap.
  - `promote_epic_tasks(roots: list[Path], epic_dir: str, *, force: bool = False) -> tuple[list[Path], list[str]]`:
    - When `not force`: runs `prereq_blockers = check_epic_prerequisites(roots[0], epic_dir)` and `conflicts = check_epic_file_conflicts(roots[0], epic_dir)`. If either is non-empty, returns `([], [*prereq_blockers, *(f"conflict with {ep}: {', '.join(pats)}" for ep, pats in conflicts.items())])`.
    - Finds all `task_*.md` in `roots[0] / ".devtool" / "epic" / epic_dir` whose `status` is `"backlog"`, calls `sync_task(roots, task_file.stem, "todo")` for each, and leaves an existing `Packaged …` HLD `Status` untouched while rewriting a `Queued (backlog)` HLD `Status` to `f"Packaged ({today_iso})"` via `sync_epic(roots, epic_dir, f"Packaged ({today_iso})")`.
  - Add 3 CLI subcommands in `main()`:
    - `check-prereqs <epic_dir>`: prints `"0 unfinished prerequisites"` and exits `0` when clean, else prints blockers to `stderr` and exits `1`.
    - `check-conflicts <epic_dir>`: prints `"0 conflicts — safe for concurrent execution"` and exits `0` when clean, else prints conflicts to `stderr` and exits `1`.
    - `promote <epic_dir> [--force]`: calls `promote_epic_tasks(roots, args.epic_dir, force=args.force)`; exits `1` on blockers or `0` after promoting all `backlog` tasks of `<epic_dir>` to `todo`.

## Definition of Done

- `sync_task_status.py` implements `check_epic_prerequisites()`, `check_epic_file_conflicts()`, and `promote_epic_tasks()` (`MEO-HP-02`, `MEO-EC-02`, `MEO-ST-01`). (V2, V5)
- CLI subcommands `check-prereqs`, `check-conflicts`, and `promote [--force]` work as specified. (V2, V5)
- `ruff` and `mypy` pass with zero errors. (V3, V4)
- Automated tests pass and write JUnit XML results. (V5)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 01](task_01_inter_epic_dependencies.md)

## References & Rollback

- Reference: [2026-11-06-multi-epic-orchestration-and-governance-design.en.md](2026-11-06-multi-epic-orchestration-and-governance-design.en.md).
- Rollback: `git revert` the task commit to restore prior `sync_task_status.py` subcommands.
