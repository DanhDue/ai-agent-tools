# Cross-Model Review: check_quota_dynamic_models_and_review_action

## Round 1

- **Date**: 2026-11-18T01:00:06Z
- **SHA**: 9ac54e1d2eb31338524851d75eb7f04c8c8b5275
- **Base**: main
- **CLI**: claude
- **Model**: Opus 5.5
- **Thinking**: high
- **Status**: completed
- **Verdict**: PASS
- **Raw log**: `build/reviews/check_quota_dynamic_models_and_review_action_code_round1_9ac54e1.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Minor | skills/check-tasks/resources/scripts/tasks_server.py:1109 | the `fix_plan_round<N>.md` / `fix_plan.md` fallback runs for every kind of review, so a `principal_review.md` finding with no proposal shows the action from the cross-model fix plan of the same round (confirmed by probe). The HLD limits the fallback to `review_results.md`. Proposed: run the fallback only when `result["kind"] != "principal"` and add a regression test for the principal case | fixed in c793551 |
| 2 | Minor | scripts/agy_quota.py:3077 | `_peek_cached_profile` checks whether `load_cached_profiles` is still the original function, which means production code changes path depending on whether a test has replaced it. Proposed: always read `CACHED_PROFILES_DATA` and the dashboard HTML through one path, and have tests patch `get_dashboard_html_path` / `CACHED_PROFILES_DATA` instead |  |
| 3 | Minor | skills/dev-implementation/resources/scripts/run_external_review.py:2440 | the last-marker rule required by Decisions Already Made cuts `Problem. Proposed: rename var. Fix: update tests` down to `update tests`, and `tasks_server.py` does the same. Proposed: record a Spec Erratum to use the first `Proposed:` marker after the last code span, falling back to the last `Fix:` / `Suggestion:` marker |  |
| 4 | Minor | scripts/agy_quota.py:3764 | the quota refresh after a ping uses `batch_mode=True`, but the cached `groupDescSig` / `modelsFetchedAt` has not been updated since the live probe, so a cold or stale cache triggers a second `agy models` call. Proposed: write the formatted `live_q` to the cache with `update_cached_profile()` before pinging, or pass `live_q`'s model metadata through to the post-ping format | fixed in c793551 |

Raw output:

```text
Verdict: PASS
```
