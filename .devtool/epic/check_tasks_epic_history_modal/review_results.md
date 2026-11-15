# Cross-Model Review: check_tasks_epic_history_modal

## Round 1

- **Date**: 2026-11-14T21:05:50Z
- **SHA**: 2c16f3f58d73510ab6bc7cfbdb5b8fedc61f2f7e
- **Base**: main
- **CLI**: codex
- **Model**: gpt-6.1-sol
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Raw log**: `build/reviews/check_tasks_epic_history_modal_code_round1_2c16f3f.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | skills/check-tasks/resources/scripts/check_tasks.py:3411 | Deduplication drops distinct review transitions sharing timestamp, stage, sub-step, and message. Read-only probe reduced reviewing→triage to one event because normalization discards review_state. Preserve transition identity through aggregation. | fixed in 1551718: Valid - preserved review_state in _normalize_step_event and added review identity to deduplication keys; tested by test_cehm_regression_round1_review_transition_deduplication |
| 2 | Important | skills/check-tasks/resources/scripts/check_tasks.py:3927 | Any gate entry overrides Packaged status. Probe confirmed a Packaged HLD with only Gate 2 becomes in_progress, mislabeling the epic and enabling unnecessary live polling. | fixed in 1551718: Valid - packaged status preserved against pre-implementation gate entries in scan_repo and harvest_epic_history; tested by test_cehm_regression_round1_packaged_hld_with_gate2_status |
| 3 | Important | skills/check-tasks/resources/scripts/tasks_server.py:1394 | Unreadable review files abort the entire history request. Injecting UnicodeDecodeError produced no HTTP response, losing otherwise valid tasks and timeline. Isolate review-file failures as required by the resilience contract. | fixed in 1551718: Valid - isolated review file decode/read failures with graceful fallback in parse_review_results and TasksServer; tested by test_cehm_regression_round1_unreadable_review_files_resilience |
| 4 | Important | skills/check-tasks/resources/dashboard/tasks_dashboard.html:4432 | includeSubSteps:false removes the required sub-step strip from every history modal. DOM probe confirmed supplied Triage telemetry renders zero sub-step elements, contradicting Task 3’s shared-renderer requirement. | fixed in 1551718: Valid - enabled includeSubSteps: true in history modal stepper options and supported telemetry review_state; tested by test_cehm_regression_round1_substeps_strip_and_malformed_json |
| 5 | Important | skills/check-tasks/resources/dashboard/tasks_dashboard.html:4325 | JSON decoding failures become successful empty payloads. Probe confirmed malformed HTTP 200 JSON hides the Retry banner and renders empty history. Propagate decoding failures to the existing error handler. | fixed in 1551718: Valid - propagated res.json() decoding exceptions to promise rejection so error banner and retry display cleanly; tested by test_cehm_regression_round1_substeps_strip_and_malformed_json |

Raw output:

```text
Verdict: CHANGES REQUIRED
```

## Round 2

- **Date**: 2026-11-14T21:32:18Z
- **SHA**: e8c78f6ddbe90924d2ac604bf18ec54b7b5cf65b
- **Base**: main
- **CLI**: codex
- **Model**: gpt-6.1-sol
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Scope**: delta from round 1 (2c16f3f)
- **Raw log**: `build/reviews/check_tasks_epic_history_modal_code_round2_e8c78f6.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | skills/check-tasks/resources/scripts/check_tasks.py:3476 | [NEW_REGRESSION] Review-aware deduplication requires review_state, which production heartbeat events omit. A read-only producer-to-aggregator probe returned three timeline steps for two review transitions: two stream records plus duplicate heartbeat overlap. Violates CEHM-ST-01 and Task 2’s frozen deduplication contract. | fixed in 36d13c1: Valid - deduplicated heartbeat events omitting review_state against stream events sharing (ts, stage, sub_step, message) and prioritized richer review_state in _build_unified_timeline; tested by test_cehm_regression_round2_review_heartbeat_overlap_deduplication and test_cehm_regression_round2_unified_timeline_ordering_and_tie_breaking |
| 2 | Important | skills/check-tasks/resources/scripts/check_tasks.py:622 | [NEW_REGRESSION] Excluding all packaged HLDs prevents overview promotion despite Gate 3 approval or active telemetry. Probe: Packaged HLD + Gate 3 without a worktree produces packaged in Roadmap but in_progress in history, regressing Task 2’s preserved overview behavior. | fixed in 36d13c1: Valid - aligned packaged promotion across scan_repo and harvest_epic_history via shared helper _is_packaged_epic_promoted so Gate >= 3, worktree, active tasks, or telemetry promote to in_progress while preserving packaged for Gate 1/2 only; tested by test_cehm_regression_round2_packaged_hld_roadmap_and_history_parity |

Raw output:

```text
Verdict: CHANGES REQUIRED
```

## Round 3

- **Date**: 2026-11-15T01:32:21Z
- **SHA**: 4652f0fcacba31730abac0780cbf8d70a834acde
- **Base**: main
- **CLI**: claude
- **Model**: Opus 5.5
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Scope**: convergence from round 2 (e8c78f6)
- **Raw log**: `build/reviews/check_tasks_epic_history_modal_code_round3_4652f0f.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | skills/check-tasks/resources/scripts/check_tasks.py:1136 | [NEW_REGRESSION] _has_epic_active_tasks only suppresses OSError around tf.read_text(encoding="utf-8"); a non-UTF-8 or partially written task_*.md in an otherwise unpromoted Packaged epic raises UnicodeDecodeError out of harvest_epics_overview/scan_repo and aborts the whole Roadmap overview (probe: same fixture is OK at e8c78f6 and raises at 4652f0f); suppress UnicodeDecodeError per file | fixed in 2c159bc: Valid - suppressed (OSError, UnicodeDecodeError) per task file in _has_epic_active_tasks so non-UTF-8 or corrupt task_*.md files never abort scan_repo, harvest_epics_overview, or harvest_epic_history; tested by test_cehm_regression_round3_unreadable_task_file_in_packaged_epic |

Raw output:

```text
Verdict: CHANGES REQUIRED
```
