---
id: "task_04_task_replay_and_measure_phase"
status: "done"
priority: "high"
assignee: null
epic: "execution-and-verification-infrastructure"
dueDate: null
created: "2026-11-06T03:20:00Z"
modified: "2026-11-06T14:40:26Z"
completedAt: "2026-11-06T14:40:26Z"
labels: ["infrastructure", "replay", "measure"]
order: "b4"
---

# Task 04: Task Text Replay Engine, Static Anchor Verification, and MEASURE Phase

Epic: [execution_and_verification_infrastructure](execution_and_verification_infrastructure.en.md)

## Requirement Analysis

Resolve Observations #0011 and #0017:
1. Authoring defects inside task prose (`Create <path>:`, `Replace in <path>:` / `With:`, and `Insert in <path> (after|before):` / `With:` code blocks) were previously discovered only by manually replaying task text in a scratch worktree before packaging. Integrating fast static edit-anchor verification (`verify_task_edit_anchors()`) into `check_epic_readiness.py` (`R5`) and providing `replay_task_text.py` (invoked by `check_epic_readiness.py --replay`) catches missing or ambiguous edit anchors automatically.
2. Long-running measurement tasks (such as multi-hour local model benchmarks) do not fit standard 600s Verification rows and need a dedicated `Phase: MEASURE` (`run_task_checks.py measure <task.md> [--timeout 7200] [--resume]`) that executes measurement rows, supports `--resume` when `runs["measure"]` passed and all declared `Evidence files:` exist and are non-empty on disk, and enforces `MEASURE` completion at `evaluate_done_gate()` and `audit_epic.py`.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/replay_task_text.py` (new)
- `skills/dev-implementation/resources/scripts/task_contract.py`
- `skills/dev-implementation/resources/scripts/run_task_checks.py`
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
- `skills/dev-implementation/resources/scripts/audit_epic.py`
- `skills/dev-implementation/resources/scripts/test_replay_and_measure.py` (new)

Read-only context:
- `.devtool/epic/execution_and_verification_infrastructure/execution_and_verification_infrastructure.en.md` (HLD specification)

## Design Rationale

Applicable skills: `python-quality-check`, `test-driven-development`.
1. `replay_task_text.py` parses structured fenced directives (`Create <path>:`, `Replace in <path>:` + `With:`, `Insert in <path> (after|before):` + `With:`) from task markdown. `verify_task_edit_anchors(root, task_path, task_text, prior_touched)` checks that every `Replace in` or `Insert in` anchor targeting a tracked file not yet created/modified by an earlier directive occurs **exactly once** (`count == 1`) in `root / <path>`, reporting missing (`0` matches) or ambiguous (`>= 2` matches) anchors in `check_epic_readiness.py` (`R5`).
2. `replay_epic_in_worktree(root, epic_dir, timeout)` creates a detached temporary git worktree and replays each task in topological order using a deterministic 3-step phase execution order: (a) apply directives targeting test files (`test_*.py`, `*_test.*`, `tests/**`) and, when the task has `RED` rows (and not `RED: n/a`), execute `RED` rows and verify they fail via `validate_pytest_red`; (b) apply all remaining production file directives (`Create`, `Replace in`, `Insert in`); (c) execute `MEASURE` rows first (generating declared `Evidence files:`), followed by `GREEN`, `TIER-B`, and `TIER-C` rows, removing the temporary worktree in a `finally:` block so `check_epic_readiness.py <epic> --replay` never mutates the main repository.
3. Adding `"MEASURE"` to `PHASES = ("RED", "MEASURE", "GREEN", "TIER-B", "TIER-C")` in `task_contract.py` (using Epic 1's `parse_evidence_files(task_text: str) -> list[AllowedPath]`) and `mode = "measure"` (`--timeout 7200`, `--resume`) in `run_task_checks.py` separates heavy measurement runs from fast `verify` assertions on committed evidence files.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/replay_task_text.py`: new `parse_task_directives`, new `verify_task_edit_anchors`, new `apply_task_directives`, and new `replay_epic_in_worktree`.
  - `skills/dev-implementation/resources/scripts/task_contract.py`: `PHASES`, `row_problems`, `evaluate_done_gate`, and new `parse_evidence_files`.
  - `skills/dev-implementation/resources/scripts/run_task_checks.py`: `run`, `main`.
  - `skills/dev-implementation/resources/scripts/check_epic_readiness.py`: `Context`, `check_grounding`, `check_baseline`, `run_checks`, `main`.
  - `skills/dev-implementation/resources/scripts/audit_epic.py`: `audit_evidence`.
- **Downstream Callers**: `check_epic_readiness.py`, `run_task_checks.py`, `audit_epic.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on `replay_task_text.py` and `MEASURE` phase logic.

### BDD SCENARIOS

Covers: EVI-HP-04, EVI-ST-02, EVI-FR-02, EVI-FR-03

```gherkin
  Scenario: [EVI-HP-04] [Tier C - Integration] Task text replay engine applies fenced directives in a scratch worktree and MEASURE phase executes and records evidence
    Given a task file containing "Create", "Replace in", and "Insert in" fenced code blocks, "Phase: MEASURE" rows, and "Evidence files: .devtool/epic/sample_epic/evidence/bench.json"
    When "replay_task_text.py" replays the task inside a temporary git worktree
    Then test directives apply before "RED" rows, production directives apply before "MEASURE" rows, and all Verification commands pass
    And when "run_task_checks.py measure" executes the task
    Then the "MEASURE" rows run, create ".devtool/epic/sample_epic/evidence/bench.json", and record a passing "measure" entry in the task's evidence JSON

  Scenario: [EVI-ST-02] [Tier C - Integration] run_task_checks.py measure --resume reuses cached MEASURE runs only when tree, row contracts, and evidence file digests match
    Given a task file with "Phase: MEASURE" rows and "Evidence files: .devtool/epic/sample_epic/evidence/bench.json"
    And a prior "run_task_checks.py measure" execution recorded "runs.measure.passed = true" with matching worktree tree, row commands/expectations, and ".devtool/epic/sample_epic/evidence/bench.json" SHA-256 digest
    When "run_task_checks.py measure <task.md> --resume" is invoked on the unchanged tree and evidence file
    Then it skips re-executing the "MEASURE" subprocess commands and exits with code 0
    And when the worktree tree, row command, or ".devtool/epic/sample_epic/evidence/bench.json" content is modified, "--resume" invalidates the cache and re-executes the "MEASURE" rows

  Scenario: [EVI-FR-02] [Tier A - Unit] R5 static anchor verification fails when a Replace in or Insert in anchor is missing or ambiguous in the target file
    Given a task file containing a "Replace in <path>:" or "Insert in <path>:" directive whose anchor text occurs 0 times or 2+ times in "<path>"
    When "verify_task_edit_anchors()" in "check_epic_readiness.py" inspects the task
    Then R5 fails and reports the exact file path and missing or ambiguous anchor snippet

  Scenario: [EVI-FR-03] [Tier A - Unit] evaluate_done_gate fails when a task contains MEASURE rows that are missing, failed, or stale relative to the current tree and evidence digests
    Given a task file containing at least one "Phase: MEASURE" Verification row
    And the task's evidence JSON either lacks "runs.measure", has "runs.measure.passed == false", or has a mismatched "tree", row contract, or evidence file SHA-256 digest
    When "evaluate_done_gate()" evaluates the task for transition to "done"
    Then it returns a non-empty failure list blocking the "done" transition until a fresh "run_task_checks.py measure" passes
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_replay_and_measure.py::test_EVI_HP_04_replay_and_measure_phase` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_replay_and_measure.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/replay_task_text.py skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/audit_epic.py skills/dev-implementation/resources/scripts/test_replay_and_measure.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/replay_task_text.py skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/audit_epic.py --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_replay_and_measure.py --junitxml=build/test-results/task_04_replay_measure.xml` | exit 0; results build/test-results/task_04_replay_measure.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- In `skills/dev-implementation/resources/scripts/task_contract.py`:
  - `PHASES = ("RED", "MEASURE", "GREEN", "TIER-B", "TIER-C")`.
  - Reuse `parse_evidence_files(task_text: str) -> list[AllowedPath]` from Epic 1 (`[entry.pattern for entry in parse_evidence_files(task_text)]` where each path matches `.devtool/epic/<epic_dir>/evidence/<filename>`); if `parse_evidence_files` is not yet present when running standalone unit tests, ensure its return type is `list[AllowedPath]`.
  - `row_problems(rows: list[Row], runs: dict) -> list[str]` maps `row.phase == "RED"` to `runs.get("red")`, `row.phase == "MEASURE"` to `runs.get("measure")`, and all other phases to `runs.get("verify")`, verifying that every `MEASURE` row has a matching `PASS` record with identical `command` and `expect_text`.
  - `evaluate_done_gate(task_file: Path) -> list[str]` checks `needs_measure = any(row.phase == "MEASURE" for row in rows)`: when `True`, requires `"measure"` in `runs`, verifies `runs["measure"].get("passed") is True`, verifies `runs["measure"].get("tree") == fingerprint(layout.root)[0]` (appending `"condition 4: the measure run's tree differs from the current tree"` on mismatch), and verifies that for every `entry` in `parse_evidence_files(task_text)`, `layout.root / entry.pattern` exists on disk, is non-empty, and its SHA-256 digest matches `runs["measure"].get("evidence_digests", {}).get(entry.pattern)`.
- In `skills/dev-implementation/resources/scripts/audit_epic.py`, `audit_evidence()` adds `(["measure"] if any(r.phase == "MEASURE" for r in rows) else [])` to `needed` and, when `"measure"` is needed, verifies `runs["measure"].get("passed") is True` and for every `entry` in `parse_evidence_files(text)` reads the committed file bytes at `HEAD` (`show(root, "HEAD", entry.pattern)`), verifying the file exists at `HEAD`, is non-empty, and `hashlib.sha256(raw.encode("utf-8")).hexdigest() == runs["measure"].get("evidence_digests", {}).get(entry.pattern)` (reporting `f"{stem}: evidence file {entry.pattern} missing or digest mismatch"` on failure).
- In `skills/dev-implementation/resources/scripts/run_task_checks.py`:
  - `main()` accepts `mode` in `("red", "measure", "verify", "status")`, `--timeout` (default `7200` when `mode == "measure"` and `--timeout` was not explicitly passed, else `1800`), and `--resume` (`action="store_true"`).
  - In `run(args)`: when `args.mode == "measure"`, selects `measure_rows = [row for row in rows if row.phase == "MEASURE"]`. If `--resume` is set, loads existing `evidence = load_evidence(layout.evidence)`: if `m_run := evidence.get("runs", {}).get("measure")` has `m_run.get("passed") is True`, `m_run.get("tree") == fingerprint(layout.root)[0]`, `row_problems(measure_rows, {"measure": m_run})` is empty, and for every `entry` in `parse_evidence_files(task_text)`, `layout.root / entry.pattern` exists with `stat().st_size > 0` and SHA-256 matching `m_run.get("evidence_digests", {}).get(entry.pattern)`, prints `"MEASURE resumed (cached PASS)"` and returns `0` without re-running subprocesses.
  - When recording `evidence["runs"][args.mode]`, include `"passed": passed` and (for `mode == "measure"`) `"evidence_digests": {entry.pattern: sha256_hex}` alongside `"head"`, `"tree"`, `"patch_id"`, `"started"`, `"finished"`, and `"rows"`.
- In `skills/dev-implementation/resources/scripts/replay_task_text.py`:
  - CLI interface: `replay_task_text.py <task.md> [--worktree <dir>] [--run-rows] [--timeout 600]`.
  - Support directives outside Gherkin fences:
    - `Create `?(<path>)`?:` followed by a fenced code block.
    - `Replace in `?(<path>)`?:` followed by a fenced code block (target anchor) and `With:` followed by a fenced code block (replacement).
    - `Insert in `?(<path>)`? (after|before):` followed by a fenced code block (anchor) and `With:` followed by a fenced code block (inserted text).
  - When `--run-rows` is active (including `replay_epic_in_worktree`), execute in deterministic phase order:
    1. Apply directives targeting test files (`Path(d.path).name.startswith("test_")` or `Path(d.path).name.endswith("_test.py")` or `"tests" in Path(d.path).parts`); if the task has `RED` rows (and not `RED: n/a`), run `RED` rows and verify they fail for the expected reason via `validate_pytest_red`.
    2. Apply remaining production file directives.
    3. Run `MEASURE` rows first (if any), then `GREEN`, `TIER-B`, and `TIER-C` rows.
  - `verify_task_edit_anchors(root: Path, task_path: Path, task_text: str, prior_modified: set[str] | None = None) -> list[str]` checks every `Replace in` and `Insert in` directive: if `<path>` is not in `prior_modified`, reads `root / <path>` and verifies `content.count(anchor) == 1`; if `0`, appends `f"{task_path.name}: missing edit anchor in {path}: {anchor.splitlines()[0]!r}"`; if `>= 2`, appends `f"{task_path.name}: ambiguous edit anchor ({count} matches) in {path}: {anchor.splitlines()[0]!r}"`; then adds `<path>` to `prior_modified`.
- In `skills/dev-implementation/resources/scripts/check_epic_readiness.py`:
  - Call `replay_task_text.verify_task_edit_anchors` in `check_grounding(ctx)` (`R5`) across tasks in sorted order, emitting `Finding("R5", "FAIL", msg)` for any anchor error.
  - Add `--replay` flag to `main()`, `Context`, `load_context()`, and `run_checks()`: when `ctx.replay` is True, `check_baseline(ctx)` calls `replay_task_text.replay_epic_in_worktree(ctx.root, ctx.epic_dir, timeout=ctx.row_timeout)` and emits `Finding("R8", "FAIL", msg)` on any replay failure.

## Definition of Done

- `replay_task_text.py` applies `Create`, `Replace in`, and `Insert in` directives in a scratch worktree and verifies anchors statically in `R5` (`EVI-HP-04`, `EVI-FR-02`). (V2, V5)
- `task_contract.py`, `run_task_checks.py`, and `audit_epic.py` support `Phase: MEASURE`, `run_task_checks.py measure --resume`, and Done-Gate enforcement (`EVI-HP-04`, `EVI-ST-02`, `EVI-FR-03`). (V2, V5)
- `ruff` and `mypy` pass with zero errors. (V3, V4)
- Automated tests pass and write JUnit XML results. (V5)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 01](task_01_polyglot_worktree_bootstrap.md)
- Blocked by [Task 03](task_03_live_integration_and_route_matching.md)

## References & Rollback

- Reference: [2026-11-06-execution-and-verification-infrastructure-design.en.md](2026-11-06-execution-and-verification-infrastructure-design.en.md).
- Rollback: `git revert` the task commit to remove `replay_task_text.py` and `MEASURE` phase changes.
