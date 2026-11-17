---
id: "task_05_check_tasks_dashboard_persona_and_quota_sync"
status: "todo"
priority: "high"
assignee: null
epic: "four_persona_governance"
dueDate: null
created: "2026-11-17T10:00:00Z"
modified: "2026-11-17T10:00:00Z"
labels: ["dashboard", "telemetry", "quota"]
order: "a5"
review_tier: "full"
---

# Task 5: check-tasks Dashboard Sync for Personas, Checkpoints and Quota Alerts

Epic: [four_persona_governance](../epic/four_persona_governance/four_persona_governance.en.md)

## Requirement Analysis

Surface every new script output and state on `/d3nexus:check-tasks` (spec §9).

1. **Document resolution**: `check_tasks.py` (`extract_epic_hld_status` L528-L554, `harvest_epics_overview`
   L1181-L1339, `extract_epic_pic` L2343-L2381, `build_epic_pipeline_telemetry` L2697-L3278,
   `_extract_epic_title` L3983-L4010) and `tasks_server.py` (`_is_pic_hld_or_spec` L1009-L1019,
   `assign_epic_pic` L1022-L1340) resolve HLDs and specs through `_epic_docs.resolve_epic_doc` /
   `resolve_design_specs`; no code path opens a `.vi.md`.
2. **Payload**: `RepoMetadata` (`L264-L288`) gains `persona_bindings: list[dict]`, `persona_config_error:
   str | None`, `checkpoint: dict | None`, `low_quota: dict | None`, `notices: list[str]`, filled in
   `_scan_repo_impl` (`L4211-L4429`) via `persona_config` (loaded by path) and the heartbeat.
3. **Human action**: pending decisions of kind `quota` and `blocker`, and heartbeat or state halts
   `MODEL_UNAVAILABLE`, `QUOTA_LOW`, `LOW_QUOTA_STOP`, `FIX_PLAN_ESCALATE`, set
   `is_human_action_required` and add an `action_blockers` entry carrying the reason text (quota lines
   included); a checkpoint `warning: quota_unknown` adds a `notices` entry only.
4. **Roles**: `extract_two_tier_memory` (`L1713-L1753`) maps `assistant` to `architect`; the dashboard memory
   panel shows the four-persona label.
5. **UI (`tasks_dashboard.html`)**: new `renderPersonaBindings(repo)` and `renderCheckpointStatus(repo)`
   render hooks in the repository panel; `renderRepoTabs` (`L2184`), `buildOverviewSig` (`L3319`),
   `renderEpicsOverviewAndApprovalGate` (`L3438`) and `renderExecutionEpics` (`L2748`) include the new fields
   and alerts; the low-quota badge shows `expires_at`; the "Tri-Role" invariant text (`L1003`) is replaced.
6. **Tests**: new `tests/test_fpg_dashboard_sync.py` (FPG-HP-07, FPG-EC-05, FPG-ST-04); update existing
   harvester tests that assert `.vi.md` reads or the `Trạng thái` label.

## Files

Allowed files:
- `skills/check-tasks/resources/scripts/check_tasks.py`
- `skills/check-tasks/resources/scripts/tasks_server.py`
- `skills/check-tasks/resources/dashboard/tasks_dashboard.html`
- `tests/test_rsdh_harvester_and_pic.py`
- `tests/test_check_tasks_harvester.py`
- `tests/test_fpg_dashboard_sync.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/_epic_docs.py` (new) — Task 4 helper
- `scripts/persona_config.py` (new) — Task 1 resolver
- `scripts/_state_envelope.py` — checkpoint block written by Task 2
- `.devtool/epic/four_persona_governance/2026-11-17-four-persona-governance-design.en.md` — spec §9

## Design Rationale

The dashboard is where the Human Architect sees that the Orchestrator stopped; a quota or model stop that
does not render there is a silent stop. Applicable skills: `d3nexus:test-driven-development`,
`d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/check-tasks/resources/scripts/check_tasks.py`: `RepoMetadata` (L264-L288), `extract_epic_hld_status` (L528-L554), `harvest_epics_overview` (L1181-L1339), `extract_two_tier_memory` (L1713-L1753), `extract_epic_pic` (L2343-L2381), `build_epic_pipeline_telemetry` (L2697-L3278), `_extract_epic_title` (L3983-L4010), `_scan_repo_impl` (L4211-L4429)
  - `skills/check-tasks/resources/scripts/tasks_server.py`: `get_real_home` (L87-L95), `_is_pic_hld_or_spec` (L1009-L1019), `assign_epic_pic` (L1022-L1340)
  - `skills/check-tasks/resources/dashboard/tasks_dashboard.html`: `renderRepoTabs` (L2184-L2260), `renderExecutionEpics` (L2748-L2900), `buildOverviewSig` (L3319-L3360), `renderEpicsOverviewAndApprovalGate` (L3438-L3560), Tri-Role invariant text (L1000-L1006), memory panel (L5090-L5100)
  - `tests/test_rsdh_harvester_and_pic.py`: `test_rsdh_fr_04_partial_readonly_failure_warnings_and_counts` (L685-L716)
  - `tests/test_check_tasks_harvester.py`: `test_extract_epic_hld_status_legacy_and_multiformat_variants` (L321-L376)
- **Downstream Callers**: `/api/tasks`, `/api/epic/history`, CLI `check_tasks.py`; UI suites `tests/test_rsdh_tasks_dashboard_ui.py`, `tests/test_ltsp_dashboard_ui.py`, `tests/test_cehm_dashboard_modal_ui.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: each new payload field with present, absent and invalid inputs; each halt reason.

### BDD SCENARIOS

Covers: FPG-HP-07, FPG-EC-05, FPG-ST-04


```gherkin
Scenario: [FPG-HP-07] [Tier C - Integration] The dashboard payload carries persona bindings, the latest checkpoint and low-quota state
Given a temporary workspace with repository "demo_repo", a project persona config, a heartbeat with checkpoint event "wave_merged" and next_step "start wave 3", and low-quota enabled for the current profile
When "scan_repo" runs and "GET /api/tasks" is requested from a running TasksServer
Then the repository JSON has "persona_bindings" with three entries carrying "alias", "model_id", "effort" and "sources"
And "checkpoint" has "event" == "wave_merged" and "next_step" == "start wave 3"
And "low_quota" has "enabled" == true and an "expires_at" timestamp
And "tasks_dashboard.html" contains the render hooks "renderPersonaBindings" and "renderCheckpointStatus"

Scenario: [FPG-EC-05] [Tier A - Unit] An invalid persona configuration degrades to a dashboard warning
Given repository "demo_repo" whose ".agents/config/personas.json" contains {"schema_version": 99}
When "scan_repo" runs
Then it returns without raising
And "persona_bindings" is empty and "persona_config_error" contains "schema_version"

Scenario: [FPG-ST-04] [Tier C - Integration] Quota, model and escalation stops render as human action on the dashboard
Given repositories whose pending decisions are kind "quota" (with quota lines "programmer agy 5H=12.0%"), kind "blocker" titled "programmer model hydrogen unavailable", and a heartbeat halt "FIX_PLAN_ESCALATE"
And a fourth repository whose latest checkpoint carries warning "quota_unknown"
When "scan_repo" runs for each repository
Then the first three have is_human_action_required true and an action_blockers entry whose text contains "5H=12.0%", "unavailable" and "FIX_PLAN_ESCALATE" respectively
And the fourth has is_human_action_required false and a "notices" entry containing "quota_unknown"
```

```gherkin
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_dashboard_sync.py::test_fpg_st_04_quota_model_and_escalation_stops_render_as_human_action` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_dashboard_sync.py tests/test_rsdh_harvester_and_pic.py tests/test_check_tasks_harvester.py tests/test_check_tasks_fsm.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_check_tasks_server.py tests/test_ltsp_harvester_pipeline.py tests/test_cehm_history_aggregator.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/check-tasks/resources/scripts/check_tasks.py skills/check-tasks/resources/scripts/tasks_server.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/check-tasks/resources/scripts/check_tasks.py skills/check-tasks/resources/scripts/tasks_server.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/fpg_task_05.xml tests/test_fpg_dashboard_sync.py tests/test_check_tasks_fsm.py` | exit 0; results build/test-results/fpg_task_05.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Source: `RepoMetadata` (`check_tasks.py` `L264-L288`) is a dataclass serialised to `/api/tasks`; new fields
  default to empty values so existing payload consumers are unaffected.
- Source: `pending_decision.json` entries carry `kind`; `_match_pending_decision_for_epic` (`L814`) already
  scopes them per epic.
- New contract: `persona_bindings` entries `{"persona", "alias", "cli", "model_id", "effort",
  "fallback_alias", "sources"}`; on `PersonaConfigError` the list is empty and `persona_config_error` holds
  the message.
- New contract: `checkpoint` is the heartbeat `checkpoint` block verbatim; `low_quota` is
  `persona_config.low_quota_state(root, profile)` for the profile of the repository's latest PIC or the
  detected current profile.
- New contract: halt reasons recognised for human action: `MODEL_UNAVAILABLE`, `QUOTA_LOW`, `LOW_QUOTA_STOP`,
  `FIX_PLAN_ESCALATE` (matched case-sensitively in heartbeat `halt_reason` or state text).
- `persona_config.py` and `_epic_docs.py` are loaded by path with `importlib.util`; a load failure degrades
  to `persona_config_error` rather than raising.
- UI functions follow the existing pattern: pure `build*Html` helpers plus render functions; DOM ids
  `persona-bindings-<repo>` and `checkpoint-status-<repo>`.

## Definition of Done

- FPG-HP-07, FPG-EC-05 and FPG-ST-04 pass. (V2, V6)
- Existing check-tasks harvester, server and history suites pass. (V2, V3)
- Ruff and mypy pass on `check_tasks.py` and `tasks_server.py`. (V4, V5)
- The persona panel, checkpoint line, low-quota badge and quota alert look right in a browser. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 1](../epic/four_persona_governance/task_01_persona_config_and_dev_config_cli.md), [Task 2](../epic/four_persona_governance/task_02_checkpoints_briefs_and_handoff_prompts.md) and [Task 4](../epic/four_persona_governance/task_04_english_only_resolution_and_ownership_check.md).

Downstream dependents (blocked by Task 5): `task_06`.

## References & Rollback

- [Epic HLD](../epic/four_persona_governance/four_persona_governance.en.md)
- **Rollback**: Revert the task commit; the dashboard falls back to the previous payload.
