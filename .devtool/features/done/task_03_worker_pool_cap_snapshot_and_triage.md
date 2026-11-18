---
id: "task_03_worker_pool_cap_snapshot_and_triage"
status: "done"
completedAt: "2026-11-18T09:54:15Z"
priority: "high"
assignee: null
epic: "review_cap_and_risk_triage"
dueDate: null
created: "2026-11-18T06:26:00Z"
modified: "2026-11-18T09:54:15Z"
labels: ["pool", "cli", "concurrency", "architecture", "contract"]
order: "a3"
review_tier: "full"
---

# Task 3: Worker Pool Hard Cap Git-Tree Snapshot and Two-Tier Risk Triage CLI

Epic: [review_cap_and_risk_triage](review_cap_and_risk_triage.md)

## Requirement Analysis

Implement mechanical hard-cap enforcement (`max_task_review_passes = 2`, `max_fix_passes = 1`), idempotent `sync` preconditions, non-destructive `pass1_tree_sha` Git-tree snapshot capture, the `normalize_task_review_payload` Coercion Guard, Tier 1 deterministic heuristic risk assessment (`triage-fix`), terminal slot finalization (`finalize-slot`), and cross-worktree `.devtool/features` mirror & `main_wt`-only audit-note isolation inside `skills/dev-implementation/resources/scripts/manage_worker_pool.py` (Spec §5, §6.3, §7, §9; HLD Module Contracts §2, `[SE-03]`):

1. **Idempotent Slot State Machine & Hard Caps (`sync_slot` & `main`)**:
   - Load `(max_review_passes, max_fix_passes)` via `persona_config.resolve_task_review_limits(repo_root)` (falling back to `(2, 1)` when `persona_config` is absent).
   - Maintain per-slot fields in `<epic_slug>.heartbeat.json` (with direct JSON fallback when `_state_envelope` is `None`): `review_passes_used` (`int`), `fix_passes_used` (`int`), `pass1_tree_sha` (`str | None`), `pass1_head_sha` (`str | None`), `pass1_blockers` (`list[dict]`), `last_triage` (`dict | None`).
   - Reset counters and snapshot fields to `0` / `None` / `[]` on `init_slots`, `merge_slot`, `sync_slot(..., status="idle")`, and `sync_slot(..., status="working", reset_worktree=True)`.
   - **Idempotency & Preconditions on `sync_slot(..., status="review")`**:
     - If `prev_status == "review"` and `effective_task_id == prev_task_id`: treat as an **idempotent re-sync** for any pass (`Pass 1` or `Pass 2`), preserving `review_passes_used` and `pass1_tree_sha` unchanged across `model_unavailable`/`quota_low` stops and resumes.
     - When entering `review` from another status (`prev_status != "review"`):
       - If `prev_review >= max_review_passes`, raise `HardCapExceededError("HARD_REVIEW_CAP_EXCEEDED: ...")` (`exit 2`).
       - If `prev_review == 1` and `fix_passes_used == 0`, raise `HardCapExceededError("NO_FIX_PASS_BEFORE_REVIEW_PASS_2: ...")` (`exit 2`).
       - Otherwise set `review_passes_used = prev_review + 1`; when `review_passes_used` transitions `0 -> 1`, capture `pass1_tree_sha = capture_slot_tree_sha(slot_path, epic_dir)` and `pass1_head_sha`.
   - **Preconditions on `sync_slot(..., status="working", reset_worktree=False)`**:
     - When `review_payload` (`--review-file` or `--blockers-file`) is supplied, normalize via `normalize_task_review_payload`; if normalized `verdict != "CHANGES_REQUESTED"` or `len(blockers) == 0`, raise `HardCapExceededError("NO_BLOCKER_FOR_FIX_PASS: ...")` (`exit 2`).
     - Count as a Fix Pass (`fix_passes_used += 1`) **only** when `prev_review >= 1` and `prev_status == "review"`: if `prev_fix >= max_fix_passes`, raise `HardCapExceededError("HARD_FIX_CAP_EXCEEDED: ...")` (`exit 2`); otherwise set `fix_passes_used = prev_fix + 1` and store `pass1_blockers`.
     - If `prev_review == 0` (re-dispatching an incomplete/blocked Pass 1 implementer before any review) or `prev_status == "working"` for the same `task_id` (idempotent re-sync mid-fix), leave `review_passes_used` and `fix_passes_used` unchanged (unless `prev_fix >= max_fix_passes` and `prev_review >= max_review_passes`, which raises `HARD_FIX_CAP_EXCEEDED`).
2. **Non-Destructive Git-Tree Snapshot (`capture_slot_tree_sha`)**:
   - Copy the slot's real Git index file (`git rev-parse --git-path index`) into a `tempfile.TemporaryDirectory()` as `TMP_INDEX`, run `git add -A` with `GIT_INDEX_FILE=TMP_INDEX`, unstage `CACHE_DIR_CANDIDATES`, `.devtool/epic/<epic_dir>/evidence/`, and `.devtool/epic/<epic_dir>/review_audit_notes*`, and run `git write-tree` with `GIT_INDEX_FILE=TMP_INDEX` so neither `HEAD` nor the real slot index changes.
3. **Reviewer Payload Normalization & Coercion Guard (`normalize_task_review_payload`)**:
   - Reject non-mapping or missing-verdict payloads (`"verdict": "UNPARSEABLE"`, `"valid": False`).
   - Map legacy `"PASS"` -> `"APPROVED"` and `"FAIL"` -> `"CHANGES_REQUESTED"`.
   - When `blockers` key is absent and legacy `findings` is non-empty, convert each finding not explicitly tagged `NON_BLOCKING_OBSERVATION` into a structured blocker entry `{"id": f"BLK-{i}", "category": "LEGACY_FINDING", "summary": str(item)}` so legacy `FAIL` payloads remain actionable.
   - When `done_gate == "FAIL"` and `blockers` is empty, synthesize `[{"id": "BLK-GATE", "category": "RUNTIME_SAFETY", "summary": "done_gate reported FAIL"}]` so a failing mechanical gate is never coerced to `APPROVED` and never hits `NO_BLOCKER_FOR_FIX_PASS`.
   - **Coercion Guard**: When `verdict == "CHANGES_REQUESTED"` while `blockers` is empty and `done_gate == "PASS"`, coerce `verdict` to `"APPROVED"` with `"coerced_from_non_blocking": True`.
4. **Tier 1 Heuristic Risk Check (`triage_fix_slot` / `triage-fix`)**:
   - Capture `<curr_tree_sha> = capture_slot_tree_sha(slot_path, epic_dir)` (`[SE-03]`) and compare `<pass1_tree_sha>..<curr_tree_sha>` via `git diff --numstat` (`non_test_changed_lines = insertions + deletions` across non-test files) and `git diff --unified=0` (excluding `CACHE_DIR_CANDIDATES`, `.devtool/epic/<epic_dir>/evidence/`, and `.devtool/state/`).
   - Partition changed files into test files (`tests/...`, `**/test_*.py`, `**/*_test.py`, `**/*.spec.ts`, `**/*.test.ts`) vs. non-test production files.
   - Strip the leading `+` or `-` marker from each unified-diff hunk line (ignoring `+++`/`---` file headers) before matching Tier 1 regexes!
   - Flag `tier1_status = "HIGH_RISK"` (`bounded_diff = None`) when ANY trigger fires: `NON_TEST_DIFF_OVER_30_LINES` (`non_test_changed_lines > 30`), `PUBLIC_SIGNATURE_CHANGED` (`^\s*(async\s+)?def\s+[A-Za-z][A-Za-z0-9_]*\s*\(`, `^\s*class\s+[A-Za-z]`, `^\s*export\s+(async\s+)?(function|class|interface|type)\b`, `^\s*pub\s+(async\s+)?(fn|struct|enum|trait)\b` on stripped `+`/`-` lines), `API_ROUTE_OR_SCHEMA_CHANGED`, `DB_OR_PERSISTENCE_CHANGED`, `CONCURRENCY_OR_LOCKING_CHANGED`, or `TEST_ASSERTION_WEAKENED` (`net_assertions < 0` or added `skip`/`xfail` marker in any touched test file).
   - Otherwise return `tier1_status = "ELIGIBLE_FOR_SHORT_CIRCUIT"` with `bounded_diff`, `non_test_changed_lines`, `test_changed_lines`, `changed_files`, and `pass1_blockers`. Support `--record-tier2 --risk-level <MEDIUM|HIGH> --rationale <text>` to log Tier 2 escalations to `main_wt` `.devtool/epic/<epic_dir>/review_audit_notes.jsonl`.
5. **Terminal Slot Finalization, `main_wt`-Only Audit Notes & `.devtool/features` Mirror Reconciliation (`finalize_slot` & `merge_slot`)**:
   - Verify mechanical gates inside the slot: run `run_task_checks.py status <task_mirror>` (when script and task mirror exist; must exit `0` and contain `"done gate: PASS"`) and `check_bdd_traceability.py tests` (when task declares `Covers:` and scenario file + roots exist; must exit `0`). On failure, print `MECHANICAL_GATE_FAILED` to `stderr` and return exit code `1` without committing or merging.
   - Sync task status to `done` (`sync_task_status.py task <task_id> done` when script/task file present), stage slot changes excluding audit notes (`git add -A -- . ':!.devtool/epic/<epic_dir>/review_audit_notes*'`), and commit `[<EPIC_SLUG_UPPER>] Complete <task_id>` (no trailers) if the slot has staged changes.
   - Before `git merge` in `merge_slot`, reconcile `.devtool/` mirrors in `main_wt`: restore tracked paths listed by `git diff --name-only -- .devtool/features .devtool/epic/<epic_dir>` with `git checkout -- <paths>` AND delete untracked mirror files only under `.devtool/features/` reported by `git ls-files --others --exclude-standard -- .devtool/features` (such as `.devtool/features/done/<task_id>.md` written by `sync_task_status.py::board_location`), while never touching non-`.devtool/` files!
   - Expose `append_review_audit_note(repo_root, main_wt, epic_dir, epic_slug, task_id, entry, *, commit=True)`: under `fcntl.flock` on `<repo_root>/.devtool/.memory.lock`, append structured JSONL audit entries **exclusively in `main_wt`** at `<main_wt>/.devtool/epic/<epic_dir>/review_audit_notes.jsonl` (after `merge_slot` succeeds in `finalize_slot`, or directly in `triage-fix --record-tier2`) and immediately stage + commit the file in `main_wt` (`git add .devtool/epic/<epic_dir>/review_audit_notes.jsonl && git commit -m "[<EPIC_SLUG_UPPER>] Record review audit note for <task_id>"`, no trailers) so `/cross-model-review --base <ref>` sees every audit note on the epic branch and `integrate_branch.py` sees zero dirty files!

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/manage_worker_pool.py`
- `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`
- `tests/test_trc_worker_pool_triage.py` (new)

Read-only context:
- `.devtool/epic/review_cap_and_risk_triage/review_cap_and_risk_triage.md` — HLD Module Contracts §2 & `[SE-03]`
- `scripts/persona_config.py` — `resolve_task_review_limits` added by Task 1
- `scripts/_state_envelope.py` — `update_epic_heartbeat` `(L516-L676)`, per-slot dictionary replacement `(L643-L661)`
- `skills/dev-implementation/resources/scripts/sync_task_status.py` — `board_location` cross-worktree `.devtool/features/done/` mirroring `(L618-L644)`
- `skills/dev-implementation/resources/scripts/run_task_checks.py` — `status` subcommand output contract

## Design Rationale

Writing `review_audit_notes.jsonl` only in `main_wt` after `merge_slot` and cleaning both tracked and untracked `.devtool/features/` mirrors before `git merge` eliminates `untracked working tree files would be overwritten by merge` and parallel add/add conflicts across 2-slot waves. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/manage_worker_pool.py`: `init_slots` `(L272-L329)`, `sync_slot` `(L331-L415)`, `merge_slot` `(L417-L477)`, `main` `(L684-L839)`
  - `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`: `WorkerPoolTests.test_sync_slot_working_and_review_statuses_preserve_uncommitted_changes` `(L156-L309)`
- **Downstream Callers**: Role 2.2 Orchestrator (`skills/dev-implementation/SKILL.md`), Task 4 (`lifecycle_runner.py`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% branch coverage of idempotent sync & hard caps, `capture_slot_tree_sha`, `normalize_task_review_payload` (including legacy `findings` and `done_gate: FAIL`), all 6 Tier 1 risk triggers on stripped diff lines, `finalize_slot` modes, and untracked `done/` mirror + parallel audit-note isolation.

### BDD SCENARIOS

Covers: TRC-HP-03, TRC-EC-02, TRC-EC-03, TRC-EC-04, TRC-ST-01, TRC-ST-02, TRC-ST-03, TRC-AR-02, TRC-AR-03, TRC-FR-02

```gherkin
Scenario: [TRC-HP-03] [Tier C - Integration] Clean surgical Fix Pass 1 passes Tier 1 eligibility and short-circuits via Tier 2 LOW finalize-slot
Given an initialized 2-slot worker pool for epic "trc_demo" where slot 1 completed Pass 1 review ("review_passes_used" == 1) and transitioned to Fix Pass 1 ("fix_passes_used" == 1) with blocker "BLK-1"
And Fix Pass 1 inserts 8 lines inside an internal helper of "src/worker.py" and adds 4 assertion lines in "tests/test_worker.py" with passing task checks and BDD traceability
When "manage_worker_pool.py triage-fix trc_demo --slot 1 --task task_01" runs
Then exit code is 0 and stdout JSON has "tier1_status" == "ELIGIBLE_FOR_SHORT_CIRCUIT", "triggers" == [], "non_test_changed_lines" == 8, and a non-empty "bounded_diff"
When "manage_worker_pool.py finalize-slot trc_demo --slot 1 --task task_01 --mode tier2-short-circuit --risk-level LOW --rationale 'Directly resolves BLK-1 with zero side effects'" runs
Then exit code is 0, "task_01" status in ".devtool/features/" is synced to "done", the slot commit is merged into "epic/trc-demo", ".devtool/epic/trc_demo/review_audit_notes.jsonl" in the main epic worktree contains one entry with "mode": "tier2-short-circuit" and "risk_level": "LOW", and slot 1 heartbeat resets to "status": "idle" with "review_passes_used": 0 and "fix_passes_used": 0

Scenario: [TRC-EC-02] [Tier A - Unit] Parser Coercion Guard converts zero-blocker CHANGES_REQUESTED to APPROVED and blocks Fix Pass 1 without blockers
Given a reviewer JSON payload {"task_id": "task_03", "pass": 1, "verdict": "CHANGES_REQUESTED", "head_sha": "abc1234", "done_gate": "PASS", "blockers": [], "observations": [{"id": "OBS-1", "file": "src/x.py", "summary": "Nitpick"}]}
When "normalize_task_review_payload" evaluates the payload
Then the normalized payload has "verdict" == "APPROVED" and "coerced_from_non_blocking" == True
And running "manage_worker_pool.py sync trc_demo --slot 1 --status working --no-reset --review-file coerced.json" exits with code 2 and stderr containing "NO_BLOCKER_FOR_FIX_PASS"

Scenario: [TRC-EC-03] [Tier A - Unit] Tier 1 heuristic boundary and sensitive-surface triggers classify HIGH_RISK accurately
Given a slot worktree with a captured "pass1_tree_sha" and "fix_passes_used" == 1
When Fix Pass 1 inserts exactly 30 internal lines in "src/calc.py" with zero signature/API/DB/concurrency hits and adds 1 test assertion
Then "triage-fix" returns "tier1_status" == "ELIGIBLE_FOR_SHORT_CIRCUIT" and "non_test_changed_lines" == 30
When Fix Pass 1 instead introduces (a) 31 inserted non-test lines, (b) a modified public "def compute_score(" signature, (c) an "@router.post" or "BaseModel" change, (d) an SQL "UPDATE " or "sqlite3" change, (e) a "threading.Lock(" or "os.killpg(" change, or (f) removes an "assert " line in "tests/test_calc.py" without replacement
Then in every case (a) through (f) "triage-fix" returns "tier1_status" == "HIGH_RISK", "bounded_diff" == None, and the corresponding trigger code in "triggers"

Scenario: [TRC-EC-04] [Tier C - Integration] Pass 2 residual CHANGES_REQUESTED with green mechanical gates finalizes to done with audit note and zero Fix Pass 2
Given slot 1 of epic "trc_demo" has completed Review Pass 2 ("review_passes_used" == 2, "fix_passes_used" == 1)
And "run_task_checks.py status" reports "done gate: PASS" and "check_bdd_traceability.py" exits 0
And Pass 2 reviewer file "pass2.json" contains {"task_id": "task_03", "pass": 2, "verdict": "CHANGES_REQUESTED", "head_sha": "<sha>", "done_gate": "PASS", "blockers": [{"id": "BLK-2", "category": "BDD_VIOLATION", "file": "src/worker.py", "summary": "Residual nit"}], "observations": []}
When "manage_worker_pool.py finalize-slot trc_demo --slot 1 --task task_03 --mode pass2-complete --review-file pass2.json" runs
Then exit code is 0, "task_03" is marked "done" and merged into "epic/trc-demo", ".devtool/epic/trc_demo/review_audit_notes.jsonl" records an entry with "event" == "pass2_residual_logged_on_cap" and "BLK-2", and zero additional fix passes execute

Scenario: [TRC-ST-01] [Tier C - Integration] Worker pool enforces idempotent re-sync across both review passes and max_task_review_passes = 2 while rejecting a third review transition with exit code 2
Given an initialized slot 1 for epic "trc_demo" with "max_task_review_passes" == 2 and "max_fix_passes" == 1
When "sync --slot 1 --task task_01 --status review" runs twice in a row for Pass 1, followed by "sync --slot 1 --status working --no-reset" with 1 blocker, followed by "sync --slot 1 --status review" twice in a row for Pass 2
Then the duplicate Pass 1 review sync keeps "review_passes_used" == 1, Fix Pass 1 sets "fix_passes_used" == 1, and both Pass 2 review syncs succeed keeping "review_passes_used" == 2
When slot 1 has "status" == "working" with "review_passes_used" == 2 and "manage_worker_pool.py sync trc_demo --slot 1 --status review" attempts a third entry into "review"
Then the command exits with code 2, stderr contains "HARD_REVIEW_CAP_EXCEEDED", and "review_passes_used" remains 2

Scenario: [TRC-ST-02] [Tier C - Integration] Worker pool enforces max_fix_passes = 1 and rejects a second fix pass with exit code 2
Given slot 1 of epic "trc_demo" has "review_passes_used" == 2 and "fix_passes_used" == 1 after Review Pass 2
When "manage_worker_pool.py sync trc_demo --slot 1 --status working --no-reset" runs
Then the command exits with code 2, stderr contains "HARD_FIX_CAP_EXCEEDED", and "fix_passes_used" remains 1

Scenario: [TRC-ST-03] [Tier A - Unit] Temporary GIT_INDEX_FILE snapshot isolates Fix Pass 1 delta from uncommitted Pass 1 changes without touching HEAD or index
Given slot 1 has 220 uncommitted lines added in "src/feature_big.py" during Pass 1 implementation
When "manage_worker_pool.py sync trc_demo --slot 1 --task task_03 --status review" captures "pass1_tree_sha"
Then "git rev-parse HEAD" and the SHA-256 digest of ".git/index" (slot git index) before and after "sync --status review" are identical
When Fix Pass 1 inserts 6 lines in "src/feature_big.py" after "sync --status working --no-reset"
Then "triage-fix" reports "non_test_changed_lines" == 6 (not 226) and "tier1_status" == "ELIGIBLE_FOR_SHORT_CIRCUIT"

Scenario: [TRC-AR-02] [Tier C - Integration] Concurrent slot 1 and slot 2 pool operations preserve independent per-slot review and fix counters
Given an initialized 2-slot worker pool for epic "trc_conc" with "task_01" in slot 1 and "task_02" in slot 2
When slot 1 transitions through Pass 1 review ("review_passes_used" == 1) and Fix Pass 1 ("fix_passes_used" == 1) while slot 2 transitions to Pass 1 review ("review_passes_used" == 1, "fix_passes_used" == 0)
Then ".devtool/state/trc-conc.heartbeat.json" preserves distinct "pass1_tree_sha" values, "fix_passes_used" == 1 on "slot-1", "fix_passes_used" == 0 on "slot-2", and "active_tasks" == ["task_01", "task_02"]

Scenario: [TRC-AR-03] [Tier C - Integration] Slot merge and finalize-slot reconcile tracked epic and features mirrors plus untracked done mirrors and commit main_wt audit notes across parallel slots
Given a main epic worktree ".worktrees/trc_mirror" whose tracked ".devtool/features/task_01.md" and ".devtool/epic/trc_mirror/task_01.md" have unstaged edits and whose ".devtool/features/done/task_01.md" exists untracked from cross-worktree status syncing
And both slot 1 ("task_01") and slot 2 ("task_02") finalize with audit notes recorded for "trc_mirror"
When "manage_worker_pool.py finalize-slot" merges slot 1 and then slot 2 into ".worktrees/trc_mirror"
Then tracked ".devtool/features/" and ".devtool/epic/trc_mirror/" diffs and untracked ".devtool/features/" mirrors in ".worktrees/trc_mirror" are reconciled before each merge, both merges exit 0 without add/add conflict, ".devtool/epic/trc_mirror/review_audit_notes.jsonl" is committed cleanly on "epic/trc-mirror" retaining both slots' audit lines with zero dirty tracked files left in ".worktrees/trc_mirror", and any non-".devtool/" dirty file in ".worktrees/trc_mirror" is never discarded

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

- Source: `_state_envelope.update_epic_heartbeat` (`L516-L676`) replaces each `merged_slots[key_str]` entry (`L643-L661`); `manage_worker_pool.py` must read `prev_entry` from `_active_tasks_from_heartbeat` and carry forward `review_passes_used`, `fix_passes_used`, `pass1_tree_sha`, `pass1_head_sha`, `pass1_blockers`, and `last_triage` whenever `reset_worktree` is `False` or `status == "review"`.
- Source: `test_manage_worker_pool.py` (`L254-L264`) calls `sync_slot(..., status="working", reset_worktree=False)` without `review_payload` after a single `review` sync (`review_passes_used == 1`, `fix_passes_used == 0`). That first `review -> working (--no-reset)` transition sets `fix_passes_used = 1` and returns `True`; a second transition from `review` (`review_passes_used == 2`, `fix_passes_used == 1`) raises `HardCapExceededError("HARD_FIX_CAP_EXCEEDED: ...")` (`exit 2`). Re-running `sync --status review` while already in `status == "review"` for the same `task_id` is idempotent for **any** pass (`Pass 1` or `Pass 2`, keeping `review_passes_used` unchanged), whereas transitioning **into** `review` from another status (`prev_status != "review"`, e.g. seeded or transitioned `status: "working"` with `review_passes_used >= max_review_passes`) raises `HardCapExceededError("HARD_REVIEW_CAP_EXCEEDED: ...")` (`exit 2`).
- New contract: `HardCapExceededError(RuntimeError)` carries `.code` (`"HARD_REVIEW_CAP_EXCEEDED"`, `"HARD_FIX_CAP_EXCEEDED"`, `"NO_BLOCKER_FOR_FIX_PASS"`, or `"NO_FIX_PASS_BEFORE_REVIEW_PASS_2"`); `main()` catches `HardCapExceededError`, prints `f"{exc.code}: {exc}"` to `sys.stderr`, and returns `2`.
- New contract (`[SE-03]`): `triage_fix_slot` computes `non_test_changed_lines = insertions + deletions` via `git diff --numstat <pass1_tree_sha> <curr_tree_sha>` and strips the single leading `+` or `-` character from unified-diff hunk lines before evaluating Tier 1 regexes.
- New contract (`[SE-03]`): `append_review_audit_note` writes `review_audit_notes.jsonl` ONLY in `main_wt` (`<main_wt>/.devtool/epic/<epic_dir>/review_audit_notes.jsonl` under `fcntl.flock` on `<repo_root>/.devtool/.memory.lock`), excludes it from slot commits (`:!.devtool/epic/<epic_dir>/review_audit_notes*`), and immediately commits it on `main_wt` (`git add .devtool/epic/<epic_dir>/review_audit_notes.jsonl && git commit -m "[<EPIC_SLUG_UPPER>] Record review audit note for <task_id>"`, no trailers). `_reconcile_main_wt_devtool_mirrors(main_wt, epic_dir)` restores tracked paths listed by `git diff --name-only -- .devtool/features .devtool/epic/<epic_dir>` with `git checkout --` and unlinks untracked files listed by `git ls-files --others --exclude-standard -- .devtool/features`, never touching non-`.devtool/` files.
- Parametrize `TRC-EC-03` triggers in `tests/test_trc_worker_pool_triage.py` with `@pytest.mark.parametrize`.

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
