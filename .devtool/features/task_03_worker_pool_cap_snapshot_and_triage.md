---
id: "task_03_worker_pool_cap_snapshot_and_triage"
status: "todo"
completedAt: null
priority: "high"
assignee: null
epic: "review_cap_and_risk_triage"
dueDate: null
created: "2026-11-18T06:26:00Z"
modified: "2026-11-18T06:26:00Z"
labels: ["pool", "cli", "concurrency", "architecture", "contract"]
order: "a3"
review_tier: "full"
---

# Task 3: Worker Pool Hard Cap Git-Tree Snapshot and Two-Tier Risk Triage CLI

Epic: [review_cap_and_risk_triage](review_cap_and_risk_triage.md)

## Requirement Analysis

Implement mechanical hard-cap enforcement (`max_task_review_passes = 2`, `max_fix_passes = 1`), non-destructive `pass1_tree_sha` Git-tree snapshot capture, the `normalize_task_review_payload` Coercion Guard, Tier 1 deterministic heuristic risk assessment (`triage-fix`), terminal slot finalization (`finalize-slot`), and cross-worktree `.devtool/` mirror reconciliation inside `skills/dev-implementation/resources/scripts/manage_worker_pool.py` (Spec §5, §6.3, §7, §9; HLD Module Contracts §2):

1. **Slot State Machine & Hard Caps (`sync_slot` & `main`)**:
   - Load `(max_review_passes, max_fix_passes)` via `persona_config.resolve_task_review_limits(repo_root)` (falling back to `(2, 1)` if `persona_config` is absent in standalone environments).
   - Maintain per-slot fields in `<epic_slug>.heartbeat.json` (with direct JSON fallback when `_state_envelope` is `None`): `review_passes_used` (`int`), `fix_passes_used` (`int`), `pass1_tree_sha` (`str | None`), `pass1_head_sha` (`str | None`), `pass1_blockers` (`list[dict]`), `last_triage` (`dict | None`).
   - Reset counters and snapshot fields to `0` / `None` / `[]` on `init_slots`, `merge_slot`, `sync_slot(..., status="idle")`, and `sync_slot(..., status="working", reset_worktree=True)`.
   - On `sync_slot(..., status="review")`: if `prev_review >= max_review_passes`, raise `HardCapExceededError("HARD_REVIEW_CAP_EXCEEDED: ...")` (`main` prints to `stderr` and returns exit code `2`). Otherwise increment `review_passes_used`; when transitioning `0 -> 1`, capture `pass1_tree_sha = capture_slot_tree_sha(slot_path, epic_dir)` and `pass1_head_sha`.
   - On `sync_slot(..., status="working", reset_worktree=False)`:
     - When `review_payload` (`--review-file` or `--blockers-file`) is supplied, normalize via `normalize_task_review_payload`; if normalized `verdict != "CHANGES_REQUESTED"` or `len(blockers) == 0`, raise `HardCapExceededError("NO_BLOCKER_FOR_FIX_PASS: ...")` (`exit 2`).
     - If `prev_fix >= max_fix_passes`, raise `HardCapExceededError("HARD_FIX_CAP_EXCEEDED: ...")` (`exit 2`).
     - Otherwise increment `fix_passes_used` (`0 -> 1`) and persist `pass1_blockers` while preserving `review_passes_used` and `pass1_tree_sha`.
2. **Non-Destructive Git-Tree Snapshot (`capture_slot_tree_sha`)**:
   - Copy the slot's real Git index file (`git rev-parse --git-path index`) into a `tempfile.TemporaryDirectory()` as `TMP_INDEX`, run `git add -A` with `GIT_INDEX_FILE=TMP_INDEX`, unstage `CACHE_DIR_CANDIDATES` and `.devtool/epic/<epic_dir>/evidence/`, and run `git write-tree` with `GIT_INDEX_FILE=TMP_INDEX` so neither `HEAD` nor the real slot index changes.
3. **Reviewer Payload Normalization & Coercion Guard (`normalize_task_review_payload`)**:
   - Accept canonical `"APPROVED"`/`"CHANGES_REQUESTED"` and legacy `"PASS"`/`"FAIL"`.
   - If `verdict` is `"CHANGES_REQUESTED"` (or `"FAIL"`) while `blockers` is present and empty (`[]`) and `done_gate == "PASS"`, coerce `verdict` to `"APPROVED"` with `"coerced_from_non_blocking": True`.
   - Reject unparseable / non-mapping payloads (`"verdict": "UNPARSEABLE"`, `"valid": False`).
4. **Tier 1 Heuristic Risk Check (`triage_fix_slot` / `triage-fix`)**:
   - Diff `pass1_tree_sha` against current slot working tree (via a temporary `GIT_INDEX_FILE` + `git write-tree` compared with `git diff --unified=0 <pass1_tree_sha> <curr_tree_sha>`, excluding `CACHE_DIR_CANDIDATES`, `.devtool/epic/<epic_dir>/evidence/`, and `.devtool/state/`).
   - Partition changed files into test files (`tests/...`, `**/test_*.py`, `**/*_test.py`, `**/*.spec.ts`, `**/*.test.ts`) vs. non-test production files.
   - Flag `tier1_status = "HIGH_RISK"` (omitting `bounded_diff`, i.e., `None`) when ANY trigger fires: `NON_TEST_DIFF_OVER_30_LINES` (`non_test_changed_lines > 30`), `PUBLIC_SIGNATURE_CHANGED`, `API_ROUTE_OR_SCHEMA_CHANGED`, `DB_OR_PERSISTENCE_CHANGED`, `CONCURRENCY_OR_LOCKING_CHANGED`, or `TEST_ASSERTION_WEAKENED` (`net_assertions < 0` or added `skip`/`xfail` marker in any touched test file).
   - Otherwise return `tier1_status = "ELIGIBLE_FOR_SHORT_CIRCUIT"` with `bounded_diff`, `non_test_changed_lines`, `test_changed_lines`, `changed_files`, and `pass1_blockers`. Support `--record-tier2 --risk-level <MEDIUM|HIGH> --rationale <text>` to log Tier 2 escalations to `.devtool/epic/<epic_dir>/review_audit_notes.jsonl`.
5. **Terminal Slot Finalization & `.devtool/` Mirror Hygiene (`finalize_slot` / `finalize-slot` & `merge_slot`)**:
   - Verify mechanical gates inside the slot: run `run_task_checks.py status <task_mirror>` (when script and task mirror exist; must exit `0` and contain `"done gate: PASS"`) and `check_bdd_traceability.py tests` (when task declares `Covers:` and scenario file + roots exist; must exit `0`). On failure, print `MECHANICAL_GATE_FAILED` to `stderr` and return exit code `1` without committing or merging.
   - Append structured JSONL audit entries to `.devtool/epic/<epic_dir>/review_audit_notes.jsonl` (both in slot/main worktree) when `observations` are present, when `mode == "tier2-short-circuit"` (`risk_level == "LOW"` + `rationale`), or when `mode == "pass2-complete"` carries residual `CHANGES_REQUESTED` (`"event": "pass2_residual_logged_on_cap"`).
   - Sync task status to `done` (`sync_task_status.py task <task_id> done` when script/task file present), stage and commit uncommitted slot work with `[<EPIC_SLUG_UPPER>] Complete <task_id>` (no trailers), reconcile unstaged `.devtool/features/` and `.devtool/epic/` mirror diffs on `main_wt` without touching any non-`.devtool/` file, and call `merge_slot` to integrate into `epic/<epic_slug>` and reset the slot to `idle`.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/manage_worker_pool.py`
- `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`
- `tests/test_trc_worker_pool_triage.py` (new)

Read-only context:
- `.devtool/epic/review_cap_and_risk_triage/review_cap_and_risk_triage.md` — HLD Module Contracts §2
- `scripts/persona_config.py` — `resolve_task_review_limits` added by Task 1
- `scripts/_state_envelope.py` — `update_epic_heartbeat` slot dictionary merging `(L643-L662)`
- `skills/dev-implementation/resources/scripts/run_task_checks.py` — `status` subcommand output contract
- `skills/dev-implementation/resources/scripts/sync_task_status.py` — `task <id> done` CLI contract

## Design Rationale

Comparing two temporary-index Git tree SHAs (`git diff <pass1_tree_sha> <curr_tree_sha>`) captures both modified tracked files and newly created untracked files from Fix Pass 1 with zero working-tree or index side effects, keeping `run_task_checks.py` `patch_id` valid. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/manage_worker_pool.py`: `init_slots` `(L272-L329)`, `sync_slot` `(L331-L415)`, `merge_slot` `(L417-L477)`, `main` `(L684-L839)`
  - `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`: `WorkerPoolTests.test_sync_slot_working_and_review_statuses_preserve_uncommitted_changes` `(L156-L309)`
- **Downstream Callers**: Role 2.2 Orchestrator (`skills/dev-implementation/SKILL.md`), Task 4 (`lifecycle_runner.py`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% branch coverage of hard caps, `capture_slot_tree_sha`, `normalize_task_review_payload`, all 6 Tier 1 risk triggers, `finalize_slot` modes, and `.devtool/` mirror reconciliation.

### BDD SCENARIOS

Covers: TRC-HP-03, TRC-EC-02, TRC-EC-03, TRC-EC-04, TRC-ST-01, TRC-ST-02, TRC-ST-03, TRC-AR-02, TRC-AR-03, TRC-FR-02

```gherkin
Scenario: [TRC-HP-03] [Tier C - Integration] Clean surgical Fix Pass 1 passes Tier 1 eligibility and short-circuits via Tier 2 LOW finalize-slot
Given an initialized 2-slot worker pool for epic "trc_demo" where slot 1 completed Pass 1 review ("review_passes_used" == 1) and transitioned to Fix Pass 1 ("fix_passes_used" == 1) with blocker "BLK-1"
And Fix Pass 1 modifies 8 lines inside an internal helper of "src/worker.py" and adds 4 assertion lines in "tests/test_worker.py" with passing task checks and BDD traceability
When "manage_worker_pool.py triage-fix trc_demo --slot 1 --task task_01" runs
Then exit code is 0 and stdout JSON has "tier1_status" == "ELIGIBLE_FOR_SHORT_CIRCUIT", "triggers" == [], "non_test_changed_lines" == 8, and a non-empty "bounded_diff"
When "manage_worker_pool.py finalize-slot trc_demo --slot 1 --task task_01 --mode tier2-short-circuit --risk-level LOW --rationale 'Directly resolves BLK-1 with zero side effects'" runs
Then exit code is 0, "task_01" status in ".devtool/features/" is synced to "done", the slot commit is merged into "epic/trc-demo", ".devtool/epic/trc_demo/review_audit_notes.jsonl" contains one entry with "mode": "tier2-short-circuit" and "risk_level": "LOW", and slot 1 heartbeat resets to "status": "idle" with "review_passes_used": 0 and "fix_passes_used": 0

Scenario: [TRC-EC-02] [Tier A - Unit] Parser Coercion Guard converts zero-blocker CHANGES_REQUESTED to APPROVED and blocks Fix Pass 1 without blockers
Given a reviewer JSON payload {"task_id": "task_03", "pass": 1, "verdict": "CHANGES_REQUESTED", "head_sha": "abc1234", "done_gate": "PASS", "blockers": [], "observations": [{"id": "OBS-1", "file": "src/x.py", "summary": "Nitpick"}]}
When "normalize_task_review_payload" evaluates the payload
Then the normalized payload has "verdict" == "APPROVED" and "coerced_from_non_blocking" == True
And running "manage_worker_pool.py sync trc_demo --slot 1 --status working --no-reset --review-file coerced.json" exits with code 2 and stderr containing "NO_BLOCKER_FOR_FIX_PASS"

Scenario: [TRC-EC-03] [Tier A - Unit] Tier 1 heuristic boundary and sensitive-surface triggers classify HIGH_RISK accurately
Given a slot worktree with a captured "pass1_tree_sha" and "fix_passes_used" == 1
When Fix Pass 1 changes exactly 30 internal lines in "src/calc.py" with zero signature/API/DB/concurrency hits and adds 1 test assertion
Then "triage-fix" returns "tier1_status" == "ELIGIBLE_FOR_SHORT_CIRCUIT" and "non_test_changed_lines" == 30
When Fix Pass 1 instead introduces (a) 31 non-test changed lines, (b) a modified public "def compute_score(" signature, (c) an "@router.post" or "BaseModel" change, (d) an SQL "UPDATE " or "sqlite3" change, (e) a "threading.Lock(" or "os.killpg(" change, or (f) removes an "assert " line in "tests/test_calc.py" without replacement
Then in every case (a) through (f) "triage-fix" returns "tier1_status" == "HIGH_RISK", "bounded_diff" == None, and the corresponding trigger code in "triggers"

Scenario: [TRC-EC-04] [Tier C - Integration] Pass 2 residual CHANGES_REQUESTED with green mechanical gates finalizes to done with audit note and zero Fix Pass 2
Given slot 1 of epic "trc_demo" has completed Review Pass 2 ("review_passes_used" == 2, "fix_passes_used" == 1)
And "run_task_checks.py status" reports "done gate: PASS" and "check_bdd_traceability.py" exits 0
And Pass 2 reviewer file "pass2.json" contains {"task_id": "task_03", "pass": 2, "verdict": "CHANGES_REQUESTED", "head_sha": "<sha>", "done_gate": "PASS", "blockers": [{"id": "BLK-2", "category": "BDD_VIOLATION", "file": "src/worker.py", "summary": "Residual nit"}], "observations": []}
When "manage_worker_pool.py finalize-slot trc_demo --slot 1 --task task_03 --mode pass2-complete --review-file pass2.json" runs
Then exit code is 0, "task_03" is marked "done" and merged into "epic/trc-demo", ".devtool/epic/trc_demo/review_audit_notes.jsonl" records an entry with "event" == "pass2_residual_logged_on_cap" and "BLK-2", and zero additional fix passes execute

Scenario: [TRC-ST-01] [Tier C - Integration] Worker pool enforces max_task_review_passes = 2 and rejects a third review pass with exit code 2
Given an initialized slot 1 for epic "trc_demo" with "max_task_review_passes" == 2 and "max_fix_passes" == 1
When "sync --slot 1 --task task_01 --status review" runs for Pass 1, followed by "sync --slot 1 --status working --no-reset" with 1 blocker, followed by "sync --slot 1 --status review" for Pass 2
Then Pass 1 sets "review_passes_used" == 1, Fix Pass 1 sets "fix_passes_used" == 1, and Pass 2 sets "review_passes_used" == 2
When a third "manage_worker_pool.py sync trc_demo --slot 1 --status review" command runs before slot reset
Then the command exits with code 2, stderr contains "HARD_REVIEW_CAP_EXCEEDED", and "review_passes_used" remains 2

Scenario: [TRC-ST-02] [Tier C - Integration] Worker pool enforces max_fix_passes = 1 and rejects a second fix pass with exit code 2
Given slot 1 of epic "trc_demo" has "review_passes_used" == 2 and "fix_passes_used" == 1 after Review Pass 2
When "manage_worker_pool.py sync trc_demo --slot 1 --status working --no-reset" runs
Then the command exits with code 2, stderr contains "HARD_FIX_CAP_EXCEEDED", and "fix_passes_used" remains 1

Scenario: [TRC-ST-03] [Tier A - Unit] Temporary GIT_INDEX_FILE snapshot isolates Fix Pass 1 delta from uncommitted Pass 1 changes without touching HEAD or index
Given slot 1 has 220 uncommitted lines added in "src/feature_big.py" during Pass 1 implementation
When "manage_worker_pool.py sync trc_demo --slot 1 --task task_03 --status review" captures "pass1_tree_sha"
Then "git rev-parse HEAD" and the SHA-256 digest of ".git/index" (slot git index) before and after "sync --status review" are identical
When Fix Pass 1 edits 6 lines in "src/feature_big.py" after "sync --status working --no-reset"
Then "triage-fix" reports "non_test_changed_lines" == 6 (not 226) and "tier1_status" == "ELIGIBLE_FOR_SHORT_CIRCUIT"

Scenario: [TRC-AR-02] [Tier C - Integration] Concurrent slot 1 and slot 2 pool operations preserve independent per-slot review and fix counters
Given an initialized 2-slot worker pool for epic "trc_conc" with "task_01" in slot 1 and "task_02" in slot 2
When slot 1 transitions through Pass 1 review ("review_passes_used" == 1) and Fix Pass 1 ("fix_passes_used" == 1) while slot 2 transitions to Pass 1 review ("review_passes_used" == 1, "fix_passes_used" == 0)
Then ".devtool/state/trc-conc.heartbeat.json" preserves distinct "pass1_tree_sha" values, "fix_passes_used" == 1 on "slot-1", "fix_passes_used" == 0 on "slot-2", and "active_tasks" == ["task_01", "task_02"]

Scenario: [TRC-AR-03] [Tier C - Integration] Slot merge and finalize-slot reconcile unstaged .devtool status mirrors on main epic worktree
Given a main epic worktree ".worktrees/trc_mirror" whose ".devtool/features/task_01.md" has unstaged status-mirror edits produced by cross-worktree status syncing
And slot 1 has a clean committed implementation on branch "epic/trc-mirror-slot-1"
When "manage_worker_pool.py merge trc_mirror --slot 1 --task task_01" runs
Then unstaged ".devtool/" mirror edits in ".worktrees/trc_mirror" are reconciled cleanly before merge, "git merge" exits 0 without conflict or abort, and any non-".devtool/" dirty file in ".worktrees/trc_mirror" is never discarded

Scenario: [TRC-FR-02] [Tier C - Integration] finalize-slot aborts with exit code 1 when mechanical done_gate or BDD traceability fails
Given slot 1 of epic "trc_demo" has uncommitted changes for "task_01" where "run_task_checks.py status" outputs "done gate: FAIL"
When "manage_worker_pool.py finalize-slot trc_demo --slot 1 --task task_01 --mode pass1-approved" runs
Then the command exits with code 1, stderr contains "MECHANICAL_GATE_FAILED", no commit or merge occurs on "epic/trc-demo", and slot 1 retains its uncommitted working tree for diagnosis
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_trc_worker_pool_triage.py::test_trc_st_01_and_st_02_hard_review_and_fix_caps` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_trc_worker_pool_triage.py skills/dev-implementation/resources/scripts/test_manage_worker_pool.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/manage_worker_pool.py skills/dev-implementation/resources/scripts/test_manage_worker_pool.py tests/test_trc_worker_pool_triage.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/manage_worker_pool.py tests/test_trc_worker_pool_triage.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/trc_task_03.xml tests/test_trc_worker_pool_triage.py skills/dev-implementation/resources/scripts/test_manage_worker_pool.py` | exit 0; results build/test-results/trc_task_03.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Source: `_state_envelope.update_epic_heartbeat` (`L653-L658`) deep-copies each `slot_updates[slot_key]` dictionary rather than shallow-merging keys; `manage_worker_pool.py` must read `prev_entry` from `_active_tasks_from_heartbeat` and carry forward `review_passes_used`, `fix_passes_used`, `pass1_tree_sha`, `pass1_head_sha`, `pass1_blockers`, and `last_triage` whenever `reset_worktree` is `False` or `status == "review"`.
- Source: `test_manage_worker_pool.py` (`L254-L264`) calls `sync_slot(..., status="working", reset_worktree=False)` without `review_payload` after a single `review` sync (`review_passes_used == 1`, `fix_passes_used == 0`). When `review_payload` is `None`, allow the first `working --no-reset` transition (`fix_passes_used: 0 -> 1`) and raise `HardCapExceededError("HARD_FIX_CAP_EXCEEDED: ...")` on any second `working --no-reset` (`fix_passes_used >= max_fix_passes`); when `review_payload` (`--review-file` / `--blockers-file`) IS provided, also require `len(blockers) >= 1` (`NO_BLOCKER_FOR_FIX_PASS`).
- New contract: `HardCapExceededError(RuntimeError)` carries `.code` (`"HARD_REVIEW_CAP_EXCEEDED"`, `"HARD_FIX_CAP_EXCEEDED"`, or `"NO_BLOCKER_FOR_FIX_PASS"`); `main()` catches `HardCapExceededError`, prints `f"{exc.code}: {exc}"` to `sys.stderr`, and returns `2`.
- New contract: `capture_slot_tree_sha(slot_path: Path, epic_dir: str) -> str` resolves the slot's git index path via `git rev-parse --git-path index` inside `slot_path` (critical for linked git worktrees where `.git` is a file pointing to `.git/worktrees/<name>`!), copies it to `tmp_dir / "index"` if it exists, runs `git add -A` with `GIT_INDEX_FILE`, runs `git rm --cached -r --ignore-unmatch` on `CACHE_DIR_CANDIDATES` and `.devtool/epic/<epic_dir>/evidence`, and returns `git write-tree` stdout stripped.
- New contract: Before `git merge` in `merge_slot`, run `git checkout -- .devtool/features .devtool/epic` (only on paths reported modified under `.devtool/features/` or `.devtool/epic/` by `git diff --name-only -- .devtool/features .devtool/epic`) inside `main_wt` so unstaged cross-worktree mirror edits from `sync_task_status.py` never abort `git merge`, while never touching untracked or non-`.devtool/` files.
- Parametrize `TRC-EC-03` triggers in `tests/test_trc_worker_pool_triage.py` with `@pytest.mark.parametrize` to comply with anti-test-bloat rules.

## Definition of Done

- `TRC-HP-03`, `TRC-EC-02`, `TRC-EC-03`, `TRC-EC-04`, `TRC-ST-01`, `TRC-ST-02`, `TRC-ST-03`, `TRC-AR-02`, `TRC-AR-03`, and `TRC-FR-02` pass alongside `test_manage_worker_pool.py`. (V2, V5)
- `ruff check` and `mypy` pass with zero errors on `manage_worker_pool.py`, `test_manage_worker_pool.py`, and `tests/test_trc_worker_pool_triage.py`. (V3, V4)
- CLI output for `triage-fix` and `finalize-slot` is deterministic JSON suitable for Role 2.2 Orchestrator consumption. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 1](task_01_persona_config_task_review_limits.md).

Downstream dependents (blocked by Task 3): [Task 4](task_04_runner_parity_and_acceptance.md).

## References & Rollback

- [Epic HLD](review_cap_and_risk_triage.md)
- **Rollback**: Revert `skills/dev-implementation/resources/scripts/manage_worker_pool.py` and `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`, and delete `tests/test_trc_worker_pool_triage.py`.
