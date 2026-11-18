# Cross-Model Review Round 1 Remediation Plan (`review_cap_and_risk_triage`)

## Allowed Files

- `skills/dev-implementation/resources/scripts/manage_worker_pool.py`
- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`
- `tests/test_trc_worker_pool_triage.py`
- `tests/test_trc_runner_and_acceptance.py`

> **Strict Boundary**: Do NOT edit `.devtool/epic/review_cap_and_risk_triage/*.md` or any file outside the list above.

## Step-by-Step Fixes

### 1. Fail-Closed Task Resolution in `_run_finalize_mechanical_gates` and `finalize_slot` (Finding #1)
- **File**: `skills/dev-implementation/resources/scripts/manage_worker_pool.py`
- Add a helper `_resolve_slot_task_mirror(slot_path: Path, epic_dir: str, task_id: str) -> tuple[Path | None, str]` that resolves the task file inside `slot_path`:
  1. Check exact `slot_path / ".devtool" / "epic" / epic_dir / f"{task_id}.md"`.
  2. If not found, check unique prefix match `sorted((slot_path / ".devtool" / "epic" / epic_dir).glob(f"{task_id}_*.md"))` (excluding `*.vi.md`); if exactly one file matches, use it and its stem as `canonical_task_id`.
  3. If still not found, check exact `slot_path / ".devtool" / "features" / f"{task_id}.md"` or unique prefix match in `slot_path / ".devtool" / "features"` (and `done/`).
- In `_run_finalize_mechanical_gates(slot_path, repo_root, epic_dir, epic_slug, task_id)` (`L1397-L1470`):
  - Resolve `task_mirror, _ = _resolve_slot_task_mirror(slot_path, epic_dir, task_id)`.
  - If `task_mirror is None` or not `task_mirror.is_file()`, immediately return `f"MECHANICAL_GATE_FAILED: task file not found for {task_id}"` so `finalize_slot` exits `1` without committing or merging.
  - If `rtc_script.is_file()` is `False`, return `"MECHANICAL_GATE_FAILED: run_task_checks.py not found"`.
- In `finalize_slot` (`L1530-L1558`):
  - Resolve `_, resolved_task_id = _resolve_slot_task_mirror(slot_path, epic_dir, task_id)` and invoke `sync_task_status.py task <resolved_task_id> done` when `sync_script.is_file()`.

### 2. Enforce `fix_passes_used == 1` in `triage_fix_slot` and Tier 1 Eligibility in `finalize_slot` (Finding #2)
- **File**: `skills/dev-implementation/resources/scripts/manage_worker_pool.py`
- In `triage_fix_slot` (`L1168-L1174`):
  - After verifying `pass1_tree_sha`, check `int(counters.get("fix_passes_used", 0)) == 1`. If `int(counters.get("fix_passes_used", 0)) != 1`, raise `RuntimeError(f"Slot {slot} requires fix_passes_used == 1 before triage-fix (got {counters.get('fix_passes_used', 0)})")`.
- In `finalize_slot` (`L1501-L1530`):
  - When `mode == "tier2-short-circuit"`, read the slot's heartbeat entry (`counters = _carry_forward_slot_counters(entry)`):
    - Verify `int(counters.get("fix_passes_used", 0)) == 1`, `isinstance(counters.get("last_triage"), Mapping)`, and `counters["last_triage"].get("tier1_status") == "ELIGIBLE_FOR_SHORT_CIRCUIT"`.
    - Verify `curr_tree_sha = capture_slot_tree_sha(slot_path, epic_dir)` matches `counters["last_triage"].get("curr_tree_sha")`.
    - If any check fails, return `{"ok": False, "code": "TIER1_SHORT_CIRCUIT_NOT_ELIGIBLE", "error": "MECHANICAL_GATE_FAILED: tier2-short-circuit requires prior triage-fix ELIGIBLE_FOR_SHORT_CIRCUIT on current slot tree", "task_id": task_id, "slot": slot, "mode": mode, "merged": False}`.

### 3. Bound `bounded_diff` to Non-Test Hunks Plus Concise Test Assertion Summaries (Finding #3)
- **File**: `skills/dev-implementation/resources/scripts/manage_worker_pool.py`
- In `_classify_tier1_diff` / `triage_fix_slot` (`L1048-L1234`):
  - Build `bounded_diff` when `tier1_status == "ELIGIBLE_FOR_SHORT_CIRCUIT"` by keeping unified-diff sections (`diff --git ...`, `---`, `+++`, `@@ ...`, `+`/`-` lines) ONLY for non-test files (`not _is_test_file(current_file)`), and appending a 1-line summary per touched test file: `# test-summary <file>: +<added_asserts>/-<removed_asserts> assertions, skip_added=<skip_added>`.

### 4. Fail Closed When `verdict == "APPROVED"` Has Non-Empty `blockers` (Finding #4)
- **File**: `skills/dev-implementation/resources/scripts/manage_worker_pool.py`
- In `normalize_task_review_payload` (`L538-L552`):
  - Add `elif normalized_verdict == "APPROVED" and blockers:` -> `normalized_verdict = "CHANGES_REQUESTED"` so any `APPROVED`/`PASS` payload carrying `>= 1` blocking entry fails closed to `CHANGES_REQUESTED`.
- In `finalize_slot` (`L1524-L1529`):
  - When `mode == "pass1-approved"` and `norm_review is not None`, if `not norm_review.get("valid")` or `norm_review.get("verdict") != "APPROVED"` or `norm_review.get("blockers")`, return `{"ok": False, "code": "MECHANICAL_GATE_FAILED", "error": "MECHANICAL_GATE_FAILED: pass1-approved requires an APPROVED review payload with zero blockers", "task_id": task_id, "slot": slot, "mode": mode, "merged": False}`.

### 5. Restrict `pass2_residual_logged_on_cap` (`A1`) to `review_pass >= 2` in `lifecycle_runner.py` (Finding #5)
- **File**: `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`
- At `L2108`, change:
  `if mechanical_ok and review_pass >= max_attempts:`
  to:
  `if mechanical_ok and review_pass >= max_attempts and review_pass >= 2:`
  so `max_fix_passes == 0` (`max_attempts == 1`) with a Pass 1 `CHANGES_REQUESTED` blocker fails closed instead of finalizing as `pass2_residual_logged_on_cap`.

### 6. Update & Extend Unit/Integration Tests
- **File**: `tests/test_trc_worker_pool_triage.py`
  - In `test_trc_ar_03_mirror_reconciliation_and_parallel_audit_notes`: transition slot 1 and slot 2 through `sync --status review`, `sync --status working --no-reset --blockers-file`, write `src/m1.py` / `src/m2.py`, and run `triage-fix` before calling `finalize-slot --mode tier2-short-circuit`.
  - Add assertions verifying:
    1. `finalize-slot` with a missing task file exits `1` with `MECHANICAL_GATE_FAILED` and does not commit or merge, while a short prefix `--task task_01` resolves to `task_01_<slug>.md` when unambiguous.
    2. `triage-fix` fails when `fix_passes_used != 1`, and `finalize-slot --mode tier2-short-circuit` fails when `last_triage` is missing, `HIGH_RISK`, or stale after new slot edits.
    3. `bounded_diff` excludes raw multi-line test file bodies and includes `# test-summary` for touched test files.
    4. `normalize_task_review_payload({"verdict": "APPROVED", "done_gate": "PASS", "blockers": [{"id": "BLK-1", "summary": "Bug"}]})` returns `verdict == "CHANGES_REQUESTED"`.
- **File**: `tests/test_trc_runner_and_acceptance.py`
  - In `test_trc_st_04_custom_persona_limits_control_runner_attempts`: add a case with `max_task_review_passes = 2, max_fix_passes = 0` where Pass 1 returns `verdict: "CHANGES_REQUESTED"`, `done_gate: "PASS"`, and `blockers: [{"id": "BLK-1", "summary": "Real blocker"}]`, asserting `_execute_single_task` returns `False` and does NOT log `pass2_residual_logged_on_cap` or mark the task `done`.

## Tier 1 Scoped Verification Commands

```bash
python3 -m pytest -q --tb=short --maxfail=3 tests/test_trc_worker_pool_triage.py tests/test_trc_runner_and_acceptance.py skills/dev-implementation/resources/scripts/test_manage_worker_pool.py tests/test_fpg_runner_personas.py
python3 -m unittest tests/test_lifecycle_runner.py
ruff check skills/dev-implementation/resources/scripts/manage_worker_pool.py skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_trc_worker_pool_triage.py tests/test_trc_runner_and_acceptance.py
mypy skills/dev-implementation/resources/scripts/manage_worker_pool.py skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_trc_worker_pool_triage.py tests/test_trc_runner_and_acceptance.py --ignore-missing-imports --follow-imports=silent
```
