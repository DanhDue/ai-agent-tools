---
id: "task_01_state_envelope_events_and_stage_producers"
status: "todo"
priority: "high"
assignee: null
epic: "lifecycle_telemetry_and_stage_progress_ui"
dueDate: null
created: "2026-11-14T08:58:00Z"
modified: "2026-11-14T08:58:00Z"
completedAt: null
labels: ["architecture", "telemetry", "state-sync", "quality-check", "review"]
order: "a1"
review_tier: "full"
---

# Task 1: State Envelope Rolling Events and Stage Sub-Step Producers

Epic: [lifecycle_telemetry_and_stage_progress_ui](lifecycle_telemetry_and_stage_progress_ui.en.md)

## Requirement Analysis

Extend the atomic state envelope (`scripts/_state_envelope.py`) with a bounded rolling event log and structured stage sub-step metadata, and wire mechanical sub-step telemetry producers across `/dev-lifecycle` scripts and skills:

1. **Heartbeat Rolling Event Log & Sub-Step Envelope (`scripts/_state_envelope.py`)**:
   - Extend `update_epic_heartbeat()` (`L416-L492`) with optional keyword parameters `sub_step: str | None = None`, `sub_step_detail: str | None = None`, `review_state: Mapping[str, Any] | None = None`, and `max_events: int = 20`.
   - Maintain `events: list[dict[str, str]]` in `<epic_slug>.heartbeat.json`. Whenever `last_event` is non-empty, if `events` is empty or `events[-1].get("message") != last_event`, append `{"ts": state["updated_at"], "stage": str(state.get("stage") or ""), "sub_step": str(state.get("sub_step") or ""), "message": str(last_event)}` and slice `events[-max_events:]`. When `last_event` matches `events[-1].get("message")`, update `events[-1]["ts"] = state["updated_at"]` in-place without duplicating the entry.
2. **Quality Check Capability Labels & Per-Step Status (`skills/quality_check/resources/scripts/verify_polyglot_registry.py`)**:
   - Add `format_capability_label(provider: str, capability: str) -> str` mapping capability identifiers (`pycore`/`unit` -> `"PyCore / Unit Test"`, `test`/`pytest` -> `"Unit & Integration Test"`, `integration` -> `"Integration Test"`, `e2e`/`ui`/`playwright` -> `"UI / E2E Test"`, `lint`/`ruff` -> `"Static Lint"`, `typecheck`/`type_check`/`mypy` -> `"Typecheck"`, `architecture`/`import_linter` -> `"Architecture Gate"`).
   - Extend `_QualityRunCoordinator` (`L319-L494`) and `_plan_step_stats` / `execute_polyglot_plan` (`L549-L1150`) to maintain `steps: list[dict[str, Any]]` (`index`, `provider`, `capability`, `label`, `status` in `"pending" | "running" | "passed" | "failed"`, `elapsed_sec`) and `capability_label` inside `runs[run_id]` in `quality_active.json`, and emit a non-fatal heartbeat event via `_state_envelope.update_epic_heartbeat()` when each step starts and finishes.
3. **Review Micro-Step State Machine & Mechanical Producers (`run_external_review.py`, `audit_epic.py`, `check_bdd_traceability.py`, `package_epic.py`, `run_task_checks.py`, `resume_context.py`, `lifecycle_runner.py`, `SKILL.md` files)**:
   - In `skills/dev-implementation/resources/scripts/run_external_review.py` (`run` `L1405-L1602`, `record_round` `L1604-L1677`, `triage` `L1913-L1986`, `main` `L1988-L2045`):
     - Add `_emit_review_heartbeat(...)` updating `<epic_slug>.heartbeat.json` (`review_state`, `sub_step`, `sub_step_detail`, `last_event`) when a review round starts (`phase="reviewing"`, `"{kind_label} Round {round_num}/{max_rounds}: {cli} ({model}) reviewing"`), when `record_round()` or `triage()` completes (`phase="triage"`, `"Lập bảng triage"` with verdict/counts/action), and add subcommand `status --epic-dir <dir> [--kind code|principal|epic] --phase <reviewing|triage|fixing|verifying|converged> [--round <n>] [--detail <text>]`.
   - Emit non-fatal heartbeat events in `audit_epic.py` (`main` `L292-L316`), `check_bdd_traceability.py` (`main` `L230-L274`), `package_epic.py` (`package_epic` `L312-L432`), `run_task_checks.py` (`run` `L377-L446`), and `resume_context.py` (`write_epic_state` `L849-L925`, `record_gate_approval` `L1073-L1160`).
   - Wire `run_external_review.py status --phase fixing` / `--phase verifying` in `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`step_principal_review` `L1066-L1200`, `_apply_code_fixes` `L1689-L1760`, `step_cross_model_review` `L2087-L2220`) and document the physical CLI step in `skills/principal-review/SKILL.md` and `skills/cross-model-review/SKILL.md`.
4. Add unit tests in `tests/test_ltsp_state_and_producers.py` covering `LTSP-HP-01`, `LTSP-HP-02`, `LTSP-EC-01`, `LTSP-ST-01`, and `LTSP-FR-01`.

## Files

Allowed files:
- `scripts/_state_envelope.py`
- `scripts/resume_context.py`
- `skills/quality_check/resources/scripts/verify_polyglot_registry.py`
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/audit_epic.py`
- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`
- `skills/dev-implementation/resources/scripts/package_epic.py`
- `skills/dev-implementation/resources/scripts/run_task_checks.py`
- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`
- `skills/principal-review/SKILL.md`
- `skills/cross-model-review/SKILL.md`
- `tests/test_ltsp_state_and_producers.py` (new)

Read-only context:
- `.devtool/epic/lifecycle_telemetry_and_stage_progress_ui/lifecycle_telemetry_and_stage_progress_ui.en.md` — HLD Module Contracts
- `.devtool/epic/lifecycle_telemetry_and_stage_progress_ui/bdd_scenarios.en.md` — Canonical BDD Scenarios

## Design Rationale

Coupling sub-step telemetry directly to the mechanical CLI tools invoked by every `/dev-lifecycle` stage eliminates LLM memory drift and ensures `/check-tasks` always reflects the true micro-step (`reviewing -> triage -> fixing -> verifying` and per-capability quality checks). Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/_state_envelope.py`: `update_epic_heartbeat` (L416-L492), `update_quality_run` (L658-L754)
  - `scripts/resume_context.py`: `write_epic_state` (L849-L925), `record_gate_approval` (L1073-L1160)
  - `skills/quality_check/resources/scripts/verify_polyglot_registry.py`: `_QualityRunCoordinator` (L319-L494), `_plan_step_stats` (L549-L577), `verify_polyglot_execution` (L1199-L1337)
  - `skills/dev-implementation/resources/scripts/run_external_review.py`: `run` (L1405-L1602), `record_round` (L1604-L1677), `triage` (L1913-L1986), `main` (L1988-L2045)
  - `skills/dev-implementation/resources/scripts/audit_epic.py`: `main` (L292-L316)
  - `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`: `main` (L230-L274)
  - `skills/dev-implementation/resources/scripts/package_epic.py`: `package_epic` (L312-L432)
  - `skills/dev-implementation/resources/scripts/run_task_checks.py`: `run` (L377-L446)
  - `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`: `step_principal_review` (L1066-L1200), `_apply_code_fixes` (L1689-L1760), `step_cross_model_review` (L2087-L2220)
  - `skills/principal-review/SKILL.md`: small file (105 lines)
  - `skills/cross-model-review/SKILL.md`: small file (120 lines)
  - `tests/test_ltsp_state_and_producers.py`: new unit test suite
- **Downstream Callers**: `skills/check-tasks/resources/scripts/check_tasks.py`, `tests/test_rsdh_state_envelope.py`, `skills/dev-implementation/resources/scripts/test_run_external_review.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of `events` ring buffer, `format_capability_label`, `_QualityRunCoordinator.steps`, and `run_external_review.py` `review_state` transitions.

### BDD SCENARIOS

Covers: LTSP-HP-01, LTSP-HP-02, LTSP-EC-01, LTSP-ST-01, LTSP-FR-01

```gherkin
Scenario: [LTSP-HP-01] [Tier A - Unit] Heartbeat envelope maintains a bounded 20-entry rolling event log and structured review_state
Given a git repository with an initialized `.devtool/state/` directory for epic "demo_epic"
When `update_epic_heartbeat` is called 25 times with distinct `last_event` messages and `review_state={"kind": "code", "round": 1, "max_rounds": 3, "cli": "codex", "model": "gpt-6.1-sol", "phase": "reviewing"}`
Then `.devtool/state/demo_epic.heartbeat.json` contains an `events` list of length 20
And `events[0]["message"]` equals `"event-06"` and `events[-1]["message"]` equals `"event-25"`
And `review_state["phase"]` equals `"reviewing"` and `review_state["cli"]` equals `"codex"`

Scenario: [LTSP-HP-02] [Tier A - Unit] Polyglot quality runner maps capability labels and records per-step status in quality_active.json
Given a quality manifest for provider "python-qa" with capabilities `["lint", "typecheck", "pycore", "integration", "e2e"]`
When `_QualityRunCoordinator` starts step 1 (`"lint"`), completes it, and starts step 3 (`"pycore"`)
Then `format_capability_label("python-qa", "pycore")` returns `"PyCore / Unit Test"`
And `format_capability_label("python-qa", "integration")` returns `"Integration Test"`
And `format_capability_label("python-qa", "e2e")` returns `"UI / E2E Test"`
And `quality_active.json` `runs[run_id]["steps"]` contains 5 entries where step `"lint"` has status `"passed"` and step `"pycore"` has status `"running"` and label `"PyCore / Unit Test"`

Scenario: [LTSP-EC-01] [Tier A - Unit] Consecutive identical heartbeat events are deduplicated in the events ring buffer
Given an epic heartbeat file `.devtool/state/dedup_epic.heartbeat.json`
When `update_epic_heartbeat` is called 5 times in a row with the same `last_event="wave 1 polling"`
Then `heartbeat["events"]` contains exactly 1 entry with `message == "wave 1 polling"` and its `ts` updated to the latest timestamp

Scenario: [LTSP-ST-01] [Tier A - Unit] External review runner transitions review_state through reviewing, triage, fixing, and verifying phases
Given an epic directory `.devtool/epic/rev_epic` with a completed Round 1 in `review_results.md` containing 1 Important finding
When `run_external_review.py triage --epic-dir rev_epic` and `run_external_review.py status --epic-dir rev_epic --phase fixing` and `run_external_review.py status --epic-dir rev_epic --phase verifying` are invoked sequentially
Then `.devtool/state/rev_epic.heartbeat.json` records `review_state["phase"]` transitioning from `"triage"` (`action == "AUTO_FIX_ELIGIBLE"`) to `"fixing"` to `"verifying"`
And `events` records each phase transition in chronological order

Scenario: [LTSP-FR-01] [Tier A - Unit] Telemetry write errors inside run_external_review.py or audit_epic.py never abort the underlying CLI command
Given a repository where `.devtool/state/` is temporarily read-only (`chmod 0555`)
When `audit_epic.py` or `run_external_review.py triage` executes
Then the command still completes with exit code `0` and emits its normal stdout report without raising an unhandled `PermissionError`
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ltsp_state_and_producers.py::test_ltsp_hp_01_events_ring_buffer_and_review_state` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ltsp_state_and_producers.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_state_envelope.py skills/dev-implementation/resources/scripts/test_run_external_review.py skills/dev-implementation/resources/scripts/test_audit_epic.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/resume_context.py skills/quality_check/resources/scripts/verify_polyglot_registry.py tests/test_ltsp_state_and_producers.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/resume_context.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/ltsp_task_01.xml tests/test_ltsp_state_and_producers.py` | exit 0; results build/test-results/ltsp_task_01.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `update_epic_heartbeat()` in `scripts/_state_envelope.py` (`L416-L492`) preserves all existing parameters and defaults while adding `sub_step: str | None = None`, `sub_step_detail: str | None = None`, `review_state: Mapping[str, Any] | None = None`, and `max_events: int = 20`.
- `format_capability_label(provider: str, capability: str) -> str` in `verify_polyglot_registry.py` maps capability names case-insensitively (`pycore`/`unit` -> `"PyCore / Unit Test"`, `test`/`pytest` -> `"Unit & Integration Test"`, `integration` -> `"Integration Test"`, `e2e`/`ui`/`playwright` -> `"UI / E2E Test"`, `lint`/`ruff` -> `"Static Lint"`, `typecheck`/`type_check`/`mypy` -> `"Typecheck"`, `architecture`/`import_linter` -> `"Architecture Gate"`).
- `_QualityRunCoordinator` accepts optional `planned_steps: list[tuple[str, str]] | None = None` and updates `steps[i]["status"]` (`"pending"` -> `"running"` -> `"passed" | "failed"`) in `runs[run_id]["steps"]` inside `quality_active.json`.
- `run_external_review.py` adds a `status` parser mode (`run_external_review.py status --epic-dir <dir> [--kind code|principal|epic] --phase <reviewing|triage|fixing|verifying|converged> [--round <n>] [--detail <text>]`) and wraps all `_state_envelope` calls in `contextlib.suppress(Exception)` so read-only `.devtool/state/` never aborts review or audit execution.

## Definition of Done

- Scenarios LTSP-HP-01, LTSP-HP-02, LTSP-EC-01, LTSP-ST-01, and LTSP-FR-01 pass. (V2, V6)
- Existing state envelope, external review, and audit tests pass without regression. (V3)
- Ruff lint and mypy typecheck pass cleanly on modified modules. (V4, V5)

## Dependencies & Blockers

None.

Downstream dependents (blocked by Task 1): `task_02`, `task_03`, `task_04`.

## References & Rollback

- [Epic HLD](lifecycle_telemetry_and_stage_progress_ui.en.md)
- **Rollback**: Revert task commit to restore `_state_envelope.py`, `verify_polyglot_registry.py`, and producer scripts.
