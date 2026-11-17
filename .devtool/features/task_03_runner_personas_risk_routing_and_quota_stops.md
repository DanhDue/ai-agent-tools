---
id: "task_03_runner_personas_risk_routing_and_quota_stops"
status: "todo"
priority: "high"
assignee: null
epic: "four_persona_governance"
dueDate: null
created: "2026-11-17T10:00:00Z"
modified: "2026-11-17T10:00:00Z"
labels: ["runner", "architecture", "concurrency", "quota"]
order: "a3"
review_tier: "full"
---

# Task 3: Lifecycle Runner on Persona Bindings, Risk Routing, Checkpoints and Quota Stops

Epic: [four_persona_governance](../epic/four_persona_governance/four_persona_governance.en.md)

## Requirement Analysis

Make the autonomous Orchestrator (`lifecycle_runner.py`) implement spec §4.3, §5.5 and §8.

1. **Bindings**: `RunnerConfig` (`L111-L226`) resolves `programmer` and `ai_architect_reviewer` through
   `persona_config.resolve_persona`; CLI flags and `--config` values stay the highest layer. The legacy
   `review_config.json` and `AGY_*` lookups are removed. `resolve_programmer_model`,
   `resolve_programmer_effort` and `resolve_assistant_model` remain as thin wrappers over the binding.
   `--architect-model` is added; `--assistant-model` stays as its alias.
2. **Risk routing**: `_can_fast_track_code_findings` (`L2228-L2304`) also refuses `Critical` findings. When
   fast-track is refused, `_draft_fix_plan` (`L1767-L1799`) dispatches the `ai_architect_reviewer` binding
   in `read-only` mode with the `fix-planner` brief and parses `PLANNED` or `ESCALATE: <criterion>`.
   `PLANNED` → a `programmer` review-fixer in `apply-plan` mode; `ESCALATE` → halt `FIX_PLAN_ESCALATE`.
   `FixPlanVerdict` (`L102-L108`) and `evaluate_programmer_fix_plan` (`L2306-L2360`) are deleted.
3. **Unavailable model**: every dispatch result goes through `classify_dispatch_failure`; on
   `model_unavailable` the runner writes a `model_unavailable` checkpoint, records a `blocker` pending
   decision whose reason contains `/d3nexus:dev-config set <persona> <fallback_alias> <effort>`, sets
   halt `MODEL_UNAVAILABLE`, and dispatches nothing further (no retry, no fallback).
4. **Checkpoints and budget**: `subagent_returned` after each dispatch result, `wave_merged` after each
   wave merge, `turn_budget` every `effective_turn_budget` dispatches.
5. **Quota gate and low-quota**: before Stage 3 starts and before each wave and each cross-model fix round,
   run the quota gate (`dev_config.cmd_quota_check`, injectable); insufficient → `quota_low` checkpoint,
   `quota` pending decision, halt `QUOTA_LOW`. When low-quota mode is on, finish the wave in flight, write
   `low_quota_stop`, record a pending decision, halt `LOW_QUOTA_STOP`.
6. **Prompt strings**: replace "AI Assistant (Role 2.2)" texts in principal-review revision prompts with
   "AI Architect & Reviewer (Role 2.1)".
7. **Tests**: new `tests/test_fpg_runner_personas.py` (FPG-ST-02, FPG-ST-03, FPG-FR-03, FPG-FR-04); update
   existing runner tests that pin removed symbols or legacy precedence.

## Files

Allowed files:
- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`
- `tests/test_lifecycle_runner.py`
- `tests/test_token_throttling_acceptance.py`
- `tests/test_fpg_runner_personas.py` (new)

Read-only context:
- `scripts/persona_config.py` (new) — Task 1 contracts
- `scripts/dev_config.py` (new) — `cmd_quota_check`
- `scripts/_state_envelope.py` — `update_epic_checkpoint` (Task 2), `record_pending_decision` (L699-L752)
- `.devtool/epic/four_persona_governance/four_persona_governance.en.md` — Stage 3 Risk Routing diagram

## Design Rationale

The runner is the only place where Orchestrator behaviour is executable code, so it carries the exact turn
count and the deterministic quota and escalation stops; interactive sessions follow the same rules from the
skill text. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`: `FixPlanVerdict` (L102-L108), `RunnerConfig` (L111-L226), `ModelDispatcher` (L265-L361), `step_principal_review` (L1149-L1314), `_make_slot_dispatcher` (L1339-L1349), `step_implementation` (L1447-L1525), `_draft_fix_plan` (L1767-L1799), `_apply_code_fixes` (L1912-L2016), `_can_fast_track_code_findings` (L2228-L2304), `evaluate_programmer_fix_plan` (L2306-L2360), `step_cross_model_review` (L2362-L2529), `main` (L2653-L2740)
  - `tests/test_lifecycle_runner.py`: `test_runner_config_assistant_model_precedence` (L132-L151), `test_alr_fr_04` (L440-L487), `test_alr_ec_03` (L489-L545), `test_alr_hp_04` (L547-L602), `test_scoped_tests_protocol_intermediate_rounds` (L694-L751), `test_tto_hp_04_runner_config_precedence` (L818-L1000), `test_tto_ec_04_effort_normalization_and_cli_args` (L1003-L1069), `test_tto_hp_07_streamlined_code_fix_and_real_executive_report` (L1166-L1285), `test_tto_st_04_cross_model_escalation_on_contract_or_ambiguity` (L1288-L1422)
  - `tests/test_token_throttling_acceptance.py`: `test_tto_hp_08_end_to_end_pipeline` (L202-L708), `test_tto_fr_04_quantitative_byte_caps_and_fail_loud` (L990-L1140)
- **Downstream Callers**: `scripts/verify.sh` suite `tests/test_lifecycle_runner.py`; dashboard halt rendering (Task 5).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: each halt reason, each of the five halt criteria, budget arithmetic in both modes.

### BDD SCENARIOS

Covers: FPG-ST-02, FPG-ST-03, FPG-FR-03, FPG-FR-04


```gherkin
Scenario: [FPG-ST-02] [Tier A - Unit] High-risk findings go to the fix-planner and halt criteria escalate
Given a runner whose cross-model triage contains one Critical finding and stub dispatchers recording persona and mode
When the fix-planner stub returns status "PLANNED"
Then the first dispatch is persona "ai_architect_reviewer" in mode "read-only" and the second is persona "programmer" with review-fixer mode "apply-plan"
When, for each of "CRITICAL_CONFLICT", "Debatable", "SHARED_CONTRACT_CONFLICT", "FIX_LOOP" and "MAX_ROUNDS_CRITICAL_REMAINING", the fix-planner stub returns status "ESCALATE" with that criterion
Then each run halts with halt_reason "FIX_PLAN_ESCALATE", records a pending decision naming the criterion, and dispatches no programmer

Scenario: [FPG-ST-03] [Tier A - Unit] Turn budget and low-quota stop at the next safe point
Given a runner with three waves of two tasks each and stub dispatchers that succeed
When max_orchestrator_turns_before_checkpoint is 4 and low-quota mode is off
Then a "turn_budget" checkpoint is written after dispatches 4 and 8
When low-quota mode is on before wave 2 starts
Then wave 2 completes, a "low_quota_stop" checkpoint is written, no wave 3 task is dispatched, and halt_reason is "LOW_QUOTA_STOP"

Scenario: [FPG-FR-03] [Tier A - Unit] An unavailable model halts with a checkpoint and a fallback command, never a retry
Given a runner whose programmer stub fails with stderr "RESOURCE_EXHAUSTED" and whose binding fallback is "claude-sonnet"
When the implementation step dispatches the first task
Then exactly one dispatch was attempted
And a "model_unavailable" checkpoint precedes a pending decision of kind "blocker" containing "/d3nexus:dev-config set programmer claude-sonnet"
And halt_reason is "MODEL_UNAVAILABLE"

Scenario: [FPG-FR-04] [Tier A - Unit] The runner checks quota before each wave
Given a runner with two waves and a quota gate stub that returns sufficient before wave 1 and insufficient before wave 2
When the implementation step runs
Then wave 1 tasks are dispatched and wave 2 tasks are not
And a "quota_low" checkpoint and a pending decision of kind "quota" are recorded, and halt_reason is "QUOTA_LOW"
```

```gherkin
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_runner_personas.py::test_fpg_st_02_high_risk_routes_to_fix_planner_and_escalates` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_runner_personas.py tests/test_lifecycle_runner.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_token_throttling_acceptance.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/fpg_task_03.xml tests/test_fpg_runner_personas.py tests/test_lifecycle_runner.py` | exit 0; results build/test-results/fpg_task_03.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Source: `build_agy_command(model, effort, mode="auto")` (`lifecycle_runner.py` `L40-L50`) and
  `normalize_agy_effort` stay; persona argv comes from `persona_config.build_dispatch_argv`, whose `agy`
  write form equals `build_agy_command`.
- Source: `_state_envelope.record_pending_decision(start_path, epic_slug, reason, *, kind="approval", ...)`
  (`L699-L752`) records every runner stop; kinds used: `"blocker"` (`MODEL_UNAVAILABLE`, `FIX_PLAN_ESCALATE`,
  `LOW_QUOTA_STOP`) and `"quota"` (`QUOTA_LOW`).
- New contract: halt reasons are the exact strings `"MODEL_UNAVAILABLE"`, `"QUOTA_LOW"`, `"LOW_QUOTA_STOP"`,
  `"FIX_PLAN_ESCALATE"`; `FIX_PLAN_ESCALATE` pending-decision reasons name the criterion.
- New contract: halt criteria `HALT_CRITERIA = ("CRITICAL_CONFLICT", "Debatable", "SHARED_CONTRACT_CONFLICT",
  "FIX_LOOP", "MAX_ROUNDS_CRITICAL_REMAINING")`; a fix-planner reply whose first line is `ESCALATE: <c>` with
  `c` outside this tuple is treated as `ESCALATE` with criterion `"UNPARSEABLE"`.
- New contract: resolution precedence for each persona is CLI flag > `--config` JSON > `persona_config`
  (project > global > kit). `AGY_PROGRAMMER_MODEL`, `AGY_PROGRAMMER_EFFORT`, `AGY_ASSISTANT_MODEL` and
  `review_config.json` persona keys are no longer read.
- The quota gate and the checkpoint writer are injected attributes (`self.quota_gate`, `self.checkpoint_writer`)
  defaulting to `dev_config.cmd_quota_check` and `_state_envelope.update_epic_checkpoint`, so tests use stubs.
- Turn budget counts dispatches, not tool calls; the budget value comes from
  `persona_config.effective_turn_budget`.

## Definition of Done

- FPG-ST-02, FPG-ST-03, FPG-FR-03 and FPG-FR-04 pass. (V2, V6)
- The existing runner and token-throttling acceptance suites pass after updates for removed symbols. (V2, V3)
- Ruff and mypy pass on `lifecycle_runner.py`. (V4, V5)

## Dependencies & Blockers

Blocked by [Task 1](../epic/four_persona_governance/task_01_persona_config_and_dev_config_cli.md) and [Task 2](../epic/four_persona_governance/task_02_checkpoints_briefs_and_handoff_prompts.md).

Downstream dependents (blocked by Task 3): `task_06`.

## References & Rollback

- [Epic HLD](../epic/four_persona_governance/four_persona_governance.en.md)
- **Rollback**: Revert the task commit to restore `FixPlanVerdict` and the legacy resolution order.
