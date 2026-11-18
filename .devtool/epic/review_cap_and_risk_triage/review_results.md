# Cross-Model Review: review_cap_and_risk_triage

## Round 1

- **Date**: 2026-11-18T10:56:38Z
- **SHA**: 4f496ec3b9d69830e9d7252e9d9a8c0b0d31b399
- **Base**: main
- **CLI**: claude
- **Model**: Opus 5.5
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Raw log**: `build/reviews/review_cap_and_risk_triage_code_round1_4f496ec.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | skills/dev-implementation/resources/scripts/manage_worker_pool.py:1409 | _run_finalize_mechanical_gates fails open when .devtool/epic/<epic_dir>/<task_id>.md is missing (wrong or short --task id): run_task_checks.py status and check_bdd_traceability.py are skipped, sync_task_status done is skipped (L1531-1539), and finalize_slot still commits, merges and returns ok:true (reproduced in a temp repo: tier2-short-circuit with no task file merged "[DEMO] Complete task_01"), contrary to Spec §2/§9 "mechanical gates are never bypassed". Proposed: when the task file is absent, return MECHANICAL_GATE_FAILED ("task file not found") and exit 1 without committing or merging; amend task_03 line 53 to match. |  |
| 2 | Minor | skills/dev-implementation/resources/scripts/manage_worker_pool.py:1168 | triage_fix_slot checks only pass1_tree_sha, not the Spec §5.3 precondition fix_passes_used == 1, and finalize_slot --mode tier2-short-circuit never checks that last_triage.tier1_status == ELIGIBLE_FOR_SHORT_CIRCUIT, so the Tier 1 → Tier 2 order is not mechanically enforced. Proposed: raise in triage-fix when fix_passes_used != 1, and refuse tier2-short-circuit unless last_triage is ELIGIBLE_FOR_SHORT_CIRCUIT for the current tree. |  |
| 3 | Minor | skills/dev-implementation/resources/scripts/manage_worker_pool.py:1231 | bounded_diff is the full unified diff including test-file hunks, which have no line cap, so Role 2.2's "bounded" context can grow without limit through tests/ changes. Proposed: cap test_changed_lines as well (or put only non-test hunks plus test assertion summaries in bounded_diff), and document the cap. |  |
| 4 | Minor | skills/dev-implementation/resources/scripts/manage_worker_pool.py:549 | normalize_task_review_payload keeps verdict APPROVED when blockers is non-empty; finalize --mode pass1-approved then merges and its audit note drops those blockers. Proposed: treat APPROVED with ≥1 blocker as CHANGES_REQUESTED (fail closed), or at least write the blockers to review_audit_notes.jsonl. |  |
| 5 | Minor | skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:1972 | with max_fix_passes = 0 (accepted by validation) max_attempts becomes 1, so Pass 1 CHANGES_REQUESTED with real blockers and done_gate PASS is finalized as done and logged as "pass2_residual_logged_on_cap", extending the A1 Pass 2 residual policy to Pass 1. Proposed: apply the residual-on-cap finalize only when review_pass >= 2; otherwise fail the task with a recorded pending decision. |  |

Raw output:

```text
Verdict: CHANGES REQUIRED
```
