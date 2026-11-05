---
id: "task_01_inter_epic_dependencies"
status: "backlog"
priority: "high"
assignee: null
epic: "multi-epic-orchestration-and-governance"
dueDate: null
created: "2026-11-06T04:25:00Z"
modified: "2026-11-06T04:25:00Z"
completedAt: null
labels: ["orchestration", "dependencies", "readiness"]
order: "c1"
---

# Task 01: Inter-Epic Dependency Declarations, Readiness Resolution, and Prerequisite Replay

Epic: [multi_epic_orchestration_and_governance](multi_epic_orchestration_and_governance.en.md)

## Requirement Analysis

Resolve Observation #0013: when Epic B builds on files or symbols created by a packaged, unmerged Epic A, `check_task_contract.py --design` rejects `Read-only context` and non-`(new)` `Allowed files` paths that do not yet exist at `HEAD`, and `check_epic_readiness.py` (`R5`) rejects symbols created by Epic A unless re-marked `new` in Epic B. Adding `- **Depends on epic**: <epic_slug_or_dir>[, ...]` support to `task_contract.py`, `check_task_contract.py`, and `check_epic_readiness.py` (`R5`, `R7`, and `replay_with_prerequisites()`) allows dependent epics to validate cleanly at design time and automatically replay prerequisite epics in topological order before replaying the target epic.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/task_contract.py`
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
- `skills/dev-implementation/resources/scripts/test_inter_epic_dependencies.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/sync_task_status.py` (`find_epic_dir_for_slug` helper)
- `.devtool/epic/execution_and_verification_infrastructure/task_04_task_replay_and_measure_phase.md` (specifies `replay_epic_in_worktree` in `replay_task_text.py`)
- `.devtool/epic/multi_epic_orchestration_and_governance/multi_epic_orchestration_and_governance.en.md` (HLD specification)

## Design Rationale

Applicable skills: `python-quality-check`, `test-driven-development`.
1. `task_contract.py` adds `parse_depends_on_epics(hld_text: str) -> list[str]`, `resolve_prerequisite_epic_dirs(root: Path, hld_text: str) -> tuple[list[str], list[str]]` (returning `(topological_prereq_dirs, missing_or_cyclic_errors)` via depth-first traversal across `.devtool/epic/` using `sync_task_status.find_epic_dir_for_slug`), and `collect_prerequisite_artifacts(root: Path, prereq_dirs: list[str]) -> tuple[set[str], dict[str, set[str]]]` (collecting all `Allowed files` patterns and `new <symbol>` entries from `Target Files & Symbols` across prerequisite tasks).
2. `check_task_contract.py` (`main()` and `check_allowed()`) merges `prereq_files` into `created` and accepts non-`(new)` `Allowed files` entries when `any(tc.path_matches(p, pattern) or tc.path_matches(pattern, p) for p in prereq_files)`.
3. `check_epic_readiness.py` (`check_metadata()` `R7`, `check_grounding()` `R5`, and `main()`) validates that all declared `Depends on epic:` entries exist without cycles and match between `.en.md` and `.vi.md` (`R7`), accepts symbols in `Target Files & Symbols` that are in `prereq_symbols.get(path_str, set())` (`R5`), and provides `replay_with_prerequisites(root: Path, epic_dir: str, row_timeout: int = 600) -> list[str]` (wired to `--replay-prereqs` in `main()`) to replay unfinished prerequisite epics in topological order before replaying `epic_dir`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/task_contract.py`: new `DEPENDS_ON_EPIC_RE`, new `parse_depends_on_epics`, new `resolve_prerequisite_epic_dirs`, and new `collect_prerequisite_artifacts`.
  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `check_allowed`, `check_task`, and `main`.
  - `skills/dev-implementation/resources/scripts/check_epic_readiness.py`: `check_grounding`, `check_metadata`, `main`, and new `replay_with_prerequisites`.
- **Downstream Callers**: `check_epic_readiness.py`, `sync_task_status.py` (`Task 02`), `package_epic.py` (`Task 03`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on new dependency parsing, topological resolution, and artifact collection functions.

### BDD SCENARIOS

Covers: MEO-HP-01, MEO-EC-01, MEO-FR-01

```gherkin
  Scenario: [MEO-HP-01] [Tier C - Integration] Dependent epic declaring Depends on epic passes design-time contract and R5 checks and replays prerequisite tasks automatically
    Given a packaged prerequisite epic "epic_alpha" whose tasks create "src/alpha_helper.py" with symbol "compute_alpha"
    And a dependent epic "epic_beta" whose HLD declares "- **Depends on epic**: epic-alpha"
    And "epic_beta" tasks list "src/alpha_helper.py" in "Read-only context" and reference "compute_alpha" in "Target Files & Symbols"
    When "check_epic_readiness.py epic_beta" executes before "epic_alpha" is merged to HEAD
    Then R1, R5, and R7 pass with 0 failures because "src/alpha_helper.py" and "compute_alpha" resolve from "epic_alpha"
    And when "replay_with_prerequisites()" runs for "epic_beta"
    Then it replays "epic_alpha" tasks first in the temporary worktree followed by "epic_beta" tasks and exits 0

  Scenario: [MEO-EC-01] [Tier A - Unit] Transitive Depends on epic chain resolves in topological order and deduplicates prerequisite files and symbols
    Given "epic_c" depends on "epic_b" and "epic_b" depends on "epic_a"
    When "resolve_prerequisite_epic_dirs()" and "collect_prerequisite_artifacts()" inspect "epic_c"
    Then "resolve_prerequisite_epic_dirs()" returns ["epic_a", "epic_b"] in topological order
    And "collect_prerequisite_artifacts()" returns the union of created files and symbols across both "epic_a" and "epic_b"

  Scenario: [MEO-FR-01] [Tier A - Unit] R7 fails when Depends on epic references a missing epic directory or forms a dependency cycle
    Given an epic HLD whose "Depends on epic:" line names a non-existent epic "missing-epic" or forms a cycle "epic_a -> epic_b -> epic_a"
    When "check_epic_readiness.py" runs R7 metadata verification
    Then R7 fails and reports the missing prerequisite epic or dependency cycle
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_inter_epic_dependencies.py::test_MEO_HP_01_dependent_epic_readiness_and_replay` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_inter_epic_dependencies.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_inter_epic_dependencies.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/check_epic_readiness.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_inter_epic_dependencies.py --junitxml=build/test-results/task_01_inter_epic_deps.xml` | exit 0; results build/test-results/task_01_inter_epic_deps.xml | — |
| V6 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_inter_epic_dependencies.py::test_replay_prereqs_cli_flag` | exit 0; contains "passed" | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- In `skills/dev-implementation/resources/scripts/task_contract.py`:
  - `DEPENDS_ON_EPIC_RE = re.compile(r"^-\s*\*\*(?:Depends on epic|Phụ thuộc vào epic)\*\*:\s*(.+)$", re.MULTILINE)`
  - `parse_depends_on_epics(hld_text: str) -> list[str]` extracts comma-separated tokens from `DEPENDS_ON_EPIC_RE`, strips backticks and parenthetical suffixes, and ignores `"none"`, `"n/a"`, `"không"`, or `"-"`.
  - `resolve_prerequisite_epic_dirs(root: Path, hld_text: str, current_epic_dir: str | None = None) -> tuple[list[str], list[str]]` performs depth-first topological resolution across `.devtool/epic/`:
    - Resolves each identifier `ident` either to `.devtool/epic/<ident>` if that directory exists or by calling `sync_task_status.find_epic_dir_for_slug(root, ident)`.
    - If an identifier does not resolve to an existing `.devtool/epic/<dir>`, appends `f"Depends on epic '{ident}' does not exist under .devtool/epic/"` to `errors`.
    - If a cycle is encountered in the recursion stack (`visiting`), appends `f"Depends on epic cycle detected: {' -> '.join([*stack, dir_name])}"` to `errors`.
    - Returns `(ordered_dirs, errors)` where `ordered_dirs` lists prerequisites in topological order (deepest prerequisite first, deduplicated).
  - `collect_prerequisite_artifacts(root: Path, prereq_dirs: list[str]) -> tuple[set[str], dict[str, set[str]]]` scans all `task_[0-9]*_*.md` files in each `.devtool/epic/<prereq_dir>/` and returns `(prereq_files, prereq_symbols)` where:
    - `prereq_files` contains every `entry.pattern` from `parse_allowed_files(task_text)`.
    - `prereq_symbols[path_str]` contains every identifier preceded by `new ` under `Target Files & Symbols` in `## Impact Analysis & Blast Radius`.
- In `skills/dev-implementation/resources/scripts/check_task_contract.py`:
  - In `main()`: resolve `prereq_dirs, _ = tc.resolve_prerequisite_epic_dirs(check.root, hld_text, args.hld.parent.name)` and `prereq_files, _ = tc.collect_prerequisite_artifacts(check.root, prereq_dirs)`.
  - Pass `created = {entry.pattern for text in tasks.values() for entry in tc.parse_allowed_files(text) if entry.new} | prereq_files` into `check_task()`, and in `check_grounding` / `check_allowed(check, stem, text, design, prereq_files)` match prerequisite paths using `any(tc.path_matches(p, pattern) or tc.path_matches(pattern, p) for p in prereq_files)` so glob prerequisite patterns match concrete dependent paths.
- In `skills/dev-implementation/resources/scripts/check_epic_readiness.py`:
  - In `check_metadata(ctx)` (`R7`): call `prereq_dirs, prereq_errors = tc.resolve_prerequisite_epic_dirs(ctx.root, ctx.hld_text, ctx.epic_dir)` and emit `Finding("R7", "FAIL", err)` for each `err` in `prereq_errors`. Also check `<epic_dir>.vi.md` if present: if `tc.parse_depends_on_epics(vi_text) != tc.parse_depends_on_epics(ctx.hld_text)`, emit `Finding("R7", "FAIL", "Depends on epic differs between .en.md and .vi.md")`.
  - In `check_grounding(ctx)` (`R5`): resolve `prereq_files, prereq_symbols = tc.collect_prerequisite_artifacts(ctx.root, prereq_dirs)`. For each target file `path_str`: if `not full_path.is_file()` and `any(tc.path_matches(p, path_str) for p in prereq_files)`, validate each non-`new` symbol against `prereq_symbols.get(path_str, set())` (emitting `R5 FAIL` if missing from `prereq_symbols`); if `full_path.is_file()` and `name not in file_text`, accept `name` when `name in prereq_symbols.get(path_str, set())`.
  - Add `replay_with_prerequisites(root: Path, epic_dir: str, row_timeout: int = 600) -> list[str]`: resolves `prereq_dirs, errors = tc.resolve_prerequisite_epic_dirs(root, hld_text, epic_dir)` (returning `errors` immediately if non-empty), imports `replay_epic_in_worktree` from `replay_task_text` (returning `["replay_task_text.py is unavailable; merge execution-and-verification-infrastructure first"]` when the module is absent), filters `active_prereqs = [d for d in prereq_dirs if not _is_epic_done(root, d)]`, and calls `replay_epic_in_worktree(root, d, row_timeout=row_timeout)` for each epic `d` in `[*active_prereqs, epic_dir]` in topological order.
  - In `main()`: `argparse` gains `--replay-prereqs` (`action="store_true"`), dispatching to `replay_with_prerequisites(root, args.epic_dir, row_timeout=args.row_timeout)` and exiting `1` (printing errors to `stderr`) on any returned error or `0` when clean.

## Definition of Done

- `task_contract.py` implements `parse_depends_on_epics()`, `resolve_prerequisite_epic_dirs()`, and `collect_prerequisite_artifacts()` (`MEO-HP-01`, `MEO-EC-01`, `MEO-FR-01`). (V2, V5)
- `check_task_contract.py` and `check_epic_readiness.py` (`R5`, `R7`, `replay_with_prerequisites()`, and `--replay-prereqs` in `main()`) resolve prerequisite files/symbols and replay prerequisite epics in topological order (`MEO-HP-01`, `MEO-FR-01`). (V2, V5, V6)
- `ruff` and `mypy` pass with zero errors. (V3, V4)
- Automated tests emit JUnit XML results covering `MEO-HP-01`, `MEO-EC-01`, and `MEO-FR-01`. (V5)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- None (Wave 1).

## References & Rollback

- Reference: [2026-11-06-multi-epic-orchestration-and-governance-design.en.md](2026-11-06-multi-epic-orchestration-and-governance-design.en.md).
- Rollback: `git revert` the task commit to restore prior single-epic readiness behavior.
