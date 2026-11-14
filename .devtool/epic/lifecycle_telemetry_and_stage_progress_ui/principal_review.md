# Principal Review: lifecycle_telemetry_and_stage_progress_ui

## Round 1

- **Date**: 2026-11-14T02:21:05Z
- **SHA**: f703e9e713967cd07438df2cb09359b7f15e9967
- **Base**: main
- **CLI**: codex
- **Model**: gpt-6.1-sol
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal
- **Raw log**: `build/reviews/lifecycle_telemetry_and_stage_progress_ui_principal_round1_f703e9e.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | .devtool/epic/lifecycle_telemetry_and_stage_progress_ui/lifecycle_telemetry_and_stage_progress_ui.en.md:84 | “Early Epic Activation and Stage Weighting Model” permits 88% Gate 4 completion when all quality capabilities pass, without requiring successful Epic Audit and BDD Traceability. Proposed: require the complete Gate 4 result; capability completion alone must remain insufficient. | fixed in 7925678: Require full Gate 4 PASS (Epic Audit + BDD Traceability + Quality Check or Gate 4 ledger entry) for 88%; capability completion alone caps at 87%. |
| 2 | Important | .devtool/epic/lifecycle_telemetry_and_stage_progress_ui/lifecycle_telemetry_and_stage_progress_ui.en.md:86 | “Early Epic Activation and Stage Weighting Model” advances to Finish on review convergence without modeling the mandatory full Gate 4 rerun and latest-SHA PASS required by rules/CRITICAL_RULES.md:43–44. Its monotonic percentages also conflict with revisiting QA after review. Proposed: define repeated QA attempts, bind evidence to candidate SHA, separate monotonic milestone progress from current execution stage, and require current-SHA Gate 4 PASS before displaying 98% / Waiting Finish; update Task 02 and LTSP-ST-02 accordingly. | fixed in 7925678: Decouple monotonic lifecycle_progress_pct watermark from current_stage_index during post-review QA reruns (96%) and require both review convergence and current-HEAD Gate 4 PASS before advancing to 98% Waiting Finish; updated HLD, Spec, Task 02, and LTSP-ST-02. |
| 3 | Important | .devtool/epic/lifecycle_telemetry_and_stage_progress_ui/2026-11-14-lifecycle-telemetry-and-stage-progress-ui-design.en.md:141 | “4.4. Quality Check Capability Breakdown and Review Micro-Step Producers” prescribes identical start/finish messages. The message-only deduplication at line 127 collapses both into one event, confirmed by an in-memory probe. Proposed: include transition and outcome in producer messages, and require Task 01 to assert that start and completion remain separate events. | fixed in 7925678: Emit distinct start ('running...') and completion ('-> status (elapsed)') messages for quality steps and assert both are preserved in LTSP-HP-02 and Task 01. |
| 4 | Important | .devtool/epic/lifecycle_telemetry_and_stage_progress_ui/task_02_check_tasks_pipeline_harvester_and_progress_weights.md:25 | “Requirement Analysis” excludes completed epics from active resolution but omits the abandoned exclusion explicitly required for overview harvesting at line 26. This permits inconsistent selection and visibility. Proposed: share one eligibility predicate excluding completed, archived, and abandoned epics; test an abandoned epic with retained Gate 1 approval and heartbeat. | fixed in 7925678: Share _is_epic_eligible_for_active across resolve_active_epic and harvest_epics_overview excluding completed, archived, and abandoned epics, and updated LTSP-EC-02 and Task 02 to test an abandoned epic with retained Gate 1 and heartbeat. |
| 5 | Important | .devtool/epic/lifecycle_telemetry_and_stage_progress_ui/bdd_scenarios.en.md:117 | “3. State Transition Scenarios”, LTSP-ST-04 permits inferring “verifying” from a commit and decision annotation without any verification execution. Those observations cannot distinguish whether tests ran. Proposed: assert fix-recorded status after the commit, then require a matching verification-start event before asserting “verifying”; align Task 02 and Task 04’s duplicated scenario. | fixed in 7925678: Updated HLD, LTSP-ST-04, Task 02, and Task 04 so commit/decision advancement infers 'fixing' and transitions to 'verifying' only when a verification execution starts on the fix SHA. |
| 6 | Important | .devtool/epic/lifecycle_telemetry_and_stage_progress_ui/task_04_integration_and_cdp_acceptance_verification.md:26 | “Requirement Analysis” allows an HTTP/DOM fallback to satisfy LTSP-HP-06, although that scenario requires actual Chrome CDP polling and console/runtime evidence. Proposed: retain fallback coverage as a separate smoke test; require Chrome CDP for LTSP-HP-06 and report acceptance BLOCKED when unavailable. | fixed in 7925678: Updated Task 04 so LTSP-HP-06 requires a real headless Chrome CDP session and reports failure/BLOCKED if unavailable, keeping non-CDP checks separate. |

Raw output:

```text
Verdict: CHANGES REQUIRED
```

## Round 2

- **Date**: 2026-11-14T02:28:56Z
- **SHA**: 3a50dd4f73d2f53db3fa593b380b9632c48500d4
- **Base**: main
- **CLI**: codex
- **Model**: gpt-6.1-sol
- **Thinking**: high
- **Status**: completed
- **Verdict**: PASS
- **Kind**: principal
- **Scope**: delta from round 1 (f703e9e)
- **Raw log**: `build/reviews/lifecycle_telemetry_and_stage_progress_ui_principal_round2_3a50dd4.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|

Raw output:

```text
Verdict: PASS
```
