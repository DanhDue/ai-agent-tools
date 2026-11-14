---
id: "task_02_check_tasks_pipeline_harvester_and_progress_weights"
status: "todo"
priority: "high"
assignee: null
epic: "lifecycle_telemetry_and_stage_progress_ui"
dueDate: null
created: "2026-11-14T08:58:00Z"
modified: "2026-11-14T08:58:00Z"
completedAt: null
labels: ["architecture", "harvester", "progress-weights", "telemetry"]
order: "a2"
review_tier: "full"
---

# Task 2: Check-Tasks Early Epic Activation, Weighted Progress, and Pipeline Harvester

Epic: [lifecycle_telemetry_and_stage_progress_ui](lifecycle_telemetry_and_stage_progress_ui.en.md)

## Requirement Analysis

Enhance `skills/check-tasks/resources/scripts/check_tasks.py` so Epics activate in Section II immediately after Gate 1 (`dev-brainstorming`), decouple `100%` Task Implementation progress from weighted 6-stage `/dev-lifecycle` progress, and harvest detailed sub-step telemetry (`pipeline_telemetry`) across all 6 stages:

1. **Early Epic Activation from Gate 1 (`resolve_active_epic` & `harvest_epics_overview`)**:
   - In `resolve_active_epic(repo_path)` (`L807-L918`), after checking worktrees, `assistant_state.md`, `.devtool/state/*.md`, and `pending_decision.json`, inspect `parse_gate_ledger_entries(repo_path)` and `.devtool/state/*.heartbeat.json`. Resolve the most recently updated non-completed epic that has Gate 1+ approved or an active `.heartbeat.json` snapshot, while leaving dormant backlog folders without gates or heartbeats idle (`None`).
   - In `harvest_epics_overview(repo_path)` (`L964-L1078`), mark a non-completed, non-abandoned epic as `status = "in_progress"` when `has_wt` is True, `hld_status == "in_progress"`, OR when the epic has Gate 1+ approved in `parse_gate_ledger_entries(repo_path, slug)` or an active `.heartbeat.json` / state file.
   - In `extract_epic_pic(repo_path, active_epic)` (`L2081-L2120`), ensure `*design*.md` files inside `.devtool/epic/<epic>/` are scanned so Stage 1 specs with `- **PIC**: <profile>` resolve PIC immediately.
2. **Decoupled 100% Task Progress vs. Weighted 6-Stage Lifecycle Progress**:
   - Add `task_completion_pct: float = 0.0` to `TaskProgress` (`L227-L239`). In `extract_task_progress()` (`L1203-L1448`), set `task_completion_pct = round((done / total) * 100.0, 1)` when `total > 0` (reaching **`100.0`** immediately when `done >= total > 0`).
   - Compute `lifecycle_progress_pct: float` monotonically across the 6 `/dev-lifecycle` stages:
     - Stage 1 (`1. Spec`, `5% -> 10%`): `5.0` when spec exists pre-Gate 1; `10.0` when Gate 1 is approved.
     - Stage 2 (`2. HLD & Principal Review`, `10% -> 25%`): `14.0` when HLD/BDD exist; `18.0` when Gate 2 is approved or `task_*.md` exist; `20.0..23.0` during `/principal-review` Round `1..3`; `25.0` when `handoff.md` is packaged.
     - Stage 3 Phase 1–2 (`3. Task Implementation`, `25% -> 80%`): `25.0` when Gate 3 is approved or `.worktrees/<epic>` exists with `0` done tasks; `25.0 + round((done / total) * 55.0, 1)` when `0 < done < total` (capped at `79.0`); **`80.0`** when `done >= total > 0` before Gate 4 starts.
     - Stage 3 Phase 4a (`4. Gate 4 Quality Check`, `80% -> 88%`): `81.0..87.0` while Gate 4 (`audit_epic`, `bdd_traceability`, or `quality_check` step `i/N`) runs; **`88.0`** when Gate 4 PASS is recorded.
     - Stage 3 Phase 4b (`5. Cross-Model Review`, `88% -> 96%`): `89.0..96.0` across Round `1..3` and micro-steps (`reviewing`, `triage`, `fixing`, `verifying`).
     - Stage 4 (`6. Finish & Sign-Off`, `98% -> 100%`): **`98.0`** when Review Converged / Waiting `/finish` (`Stage 3 Phase 4.1 (Sign-off)`); **`100.0`** when Gate 5 is approved or epic status is `done`.
3. **Structured 6-Stage `pipeline_telemetry` Builder (`build_epic_pipeline_telemetry`)**:
   - Attach `pipeline_telemetry: dict[str, Any]` to `RepoMetadata` (`L265-L289`) and to each active/in-progress epic entry in `epics_summary.epics` inside `scan_repo()` (`L2122-L2227`).
   - Populate `stages` (6 items) with `id`, `index` (`1..6`), `label`, `status` (`"done" | "running" | "action_required" | "failed" | "pending"`), `summary`, and `sub_steps: list[dict[str, str]]`:
     - Stage 2 & Stage 5 Review sub-steps: `[1. <CLI/Model> Reviewing]`, `[2. Lập bảng Triage]`, `[3. Fix findings]`, `[4. Verifying]`, including automatic commit-based inference when git `HEAD` in the epic worktree has advanced past the latest round's `SHA` in `review_results.md` / `principal_review.md` or when `fixed in <sha>` is recorded.
     - Stage 3 Task Implementation sub-steps: Wave number, active worker slots (`Slot k: task_id (working/review)`), and `done/total (100%)` summary.
     - Stage 4 Gate 4 Quality Check sub-steps: `Epic Audit`, `BDD Traceability`, and per-capability steps from `quality_active.json` (`Static Lint`, `Typecheck`, `PyCore / Unit Test`, `Integration Test`, `UI / E2E Test`, `Architecture Gate`).
4. Add unit tests in `tests/test_ltsp_harvester_pipeline.py` covering `LTSP-HP-03`, `LTSP-HP-04`, `LTSP-EC-02`, `LTSP-ST-02`, and `LTSP-AR-01`.

## Files

Allowed files:
- `skills/check-tasks/resources/scripts/check_tasks.py`
- `tests/test_ltsp_harvester_pipeline.py` (new)

Read-only context:
- `.devtool/epic/lifecycle_telemetry_and_stage_progress_ui/lifecycle_telemetry_and_stage_progress_ui.en.md` — HLD Stage Weighting & Harvester Contract
- `.devtool/epic/lifecycle_telemetry_and_stage_progress_ui/bdd_scenarios.en.md` — Canonical BDD Scenarios

## Design Rationale

Synthesizing `pipeline_telemetry` in `check_tasks.py` from `GATE_LEDGER.md`, `<epic>.heartbeat.json`, `quality_active.json`, `principal_review.md`, `review_results.md`, and git commit history guarantees that both the CLI and Web Dashboard consume a single deterministic source of truth. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/check-tasks/resources/scripts/check_tasks.py`: `TaskProgress` (L227-L239), `RepoMetadata` (L265-L289), `resolve_active_epic` (L807-L918), `harvest_epics_overview` (L964-L1078), `extract_task_progress` (L1203-L1448), `derive_lifecycle_state` (L1835-L2036), `extract_epic_pic` (L2081-L2120), `scan_repo` (L2122-L2227)
  - `tests/test_ltsp_harvester_pipeline.py`: new unit test suite
- **Downstream Callers**: `skills/check-tasks/resources/scripts/tasks_server.py`, `skills/check-tasks/resources/dashboard/tasks_dashboard.html`, `tests/test_check_tasks_fsm.py`, `tests/test_rsdh_harvester_and_pic.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of `build_epic_pipeline_telemetry`, early Stage 1 activation, `task_completion_pct`, and `lifecycle_progress_pct`.

### BDD SCENARIOS

Covers: LTSP-HP-03, LTSP-HP-04, LTSP-EC-02, LTSP-ST-02, LTSP-AR-01

```gherkin
Scenario: [LTSP-HP-03] [Tier A - Unit] Check-Tasks harvester activates epic immediately after Gate 1 approval and extracts Stage 1-2 telemetry
Given a git repository with `.devtool/epic/early_epic/2026-11-14-early-epic-design.en.md` containing `- **PIC**: phungthuy8901` and Gate 1 recorded in `GATE_LEDGER.md` without a `.worktrees/early_epic` directory
When `scan_repo` harvests the repository metadata
Then `meta.active_epic` equals `"early_epic"`
And `meta.account_id` equals `"phungthuy8901"`
And the epic entry in `meta.epics_summary.epics` has `status` equal to `"in_progress"`
And `meta.pipeline_telemetry["lifecycle_progress_pct"]` is between 10 and 25
And `meta.pipeline_telemetry["stages"][0]["status"]` equals `"done"` and `meta.pipeline_telemetry["stages"][1]["status"]` equals `"running"`

Scenario: [LTSP-HP-04] [Tier A - Unit] Harvester decouples 100% Task Implementation completion from weighted 6-stage lifecycle progress
Given an active epic "full_tasks_epic" with Gate 1, Gate 2, and Gate 3 approved and 9 out of 9 tasks marked `status: "done"` before Gate 4 convergence
When `scan_repo` computes `task_progress` and `pipeline_telemetry`
Then `meta.task_progress.done_tasks` equals 9 and `meta.task_progress.total_tasks` equals 9
And `meta.task_progress.task_completion_pct` equals 100.0
And `meta.pipeline_telemetry["task_completion_pct"]` equals 100.0
And `meta.pipeline_telemetry["stages"][2]["status"]` equals `"done"` and `meta.pipeline_telemetry["stages"][2]["summary"]` contains `"9/9 (100%)"`
And `meta.pipeline_telemetry["lifecycle_progress_pct"]` is between 80 and 96

Scenario: [LTSP-EC-02] [Tier A - Unit] Dormant backlog epic directories without Gate 1 or active heartbeat remain unstarted and do not trigger active_epic
Given a repository containing `.devtool/epic/dormant_backlog/dormant_backlog.en.md` with `- **Status**: Backlog` and zero entries in `GATE_LEDGER.md`, `gate_ledger.jsonl`, or `.devtool/state/`
When `resolve_active_epic` and `harvest_epics_overview` inspect the repository
Then `resolve_active_epic` returns `None`
And the `"dormant_backlog"` entry in `epics_summary.epics` has `status` equal to `"unstarted"`

Scenario: [LTSP-ST-02] [Tier A - Unit] Lifecycle progress percentage advances monotonically across all 6 stages from Stage 1 to Stage 4
Given an epic progressing sequentially through: (1) Stage 1 Spec, (2) Stage 2 HLD + Principal Review Round 1, (3) Stage 3 Tasks 2/4 Done, (4) Stage 3 Tasks 4/4 Done + Gate 4 QA Running, (5) Gate 4 PASS + Cross-Model Review Round 2, (6) Review Converged Waiting Finish, and (7) Gate 5 Done
When `build_epic_pipeline_telemetry` computes `(task_completion_pct, lifecycle_progress_pct)` at each state
Then `lifecycle_progress_pct` strictly increases across states `(1) < (2) < (3) < (4) < (5) < (6) < (7)` ending at `100.0`
And `task_completion_pct` equals `0.0` at `(1)-(2)`, `50.0` at `(3)`, and `100.0` for all states `(4)` through `(7)`

Scenario: [LTSP-AR-01] [Tier A - Unit] Multi-process concurrent heartbeat event updates preserve all distinct events under flock
Given 4 concurrent worker processes calling `update_epic_heartbeat` with distinct `last_event` strings on the same repository
When all 4 processes complete
Then `.devtool/state/<epic>.heartbeat.json` in both primary root and worktree mirror have identical `generation` and `events` lists containing all 4 events without corruption
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ltsp_harvester_pipeline.py::test_ltsp_hp_03_early_epic_activation_from_gate1` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ltsp_harvester_pipeline.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_check_tasks_fsm.py tests/test_check_tasks_harvester.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/check-tasks/resources/scripts/check_tasks.py tests/test_ltsp_harvester_pipeline.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/check-tasks/resources/scripts/check_tasks.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/ltsp_task_02.xml tests/test_ltsp_harvester_pipeline.py` | exit 0; results build/test-results/ltsp_task_02.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `TaskProgress` (`check_tasks.py:L227-L239`) adds `task_completion_pct: float = 0.0` (`100.0` when `done_tasks == total_tasks > 0`) while keeping `percentage` compatible with backend callers.
- `RepoMetadata` (`check_tasks.py:L265-L289`) adds `pipeline_telemetry: dict[str, Any] | None = None`, and `scan_repo()` also populates `ep["pipeline_telemetry"]` for each active/in-progress epic in `epics_summary.epics`.
- `resolve_active_epic()` (`check_tasks.py:L807-L918`) activates any non-completed epic with Gate 1+ in `parse_gate_ledger_entries(repo_path)` or an active `.heartbeat.json`, while never activating bare unstarted backlog folders (`RSDH-EC-04`).

## Definition of Done

- Scenarios LTSP-HP-03, LTSP-HP-04, LTSP-EC-02, LTSP-ST-02, and LTSP-AR-01 pass. (V2, V6)
- Existing `test_check_tasks_fsm.py` and `test_check_tasks_harvester.py` suites pass. (V3)
- Ruff lint and mypy typecheck pass cleanly on `check_tasks.py`. (V4, V5)

## Dependencies & Blockers

Blocked by [Task 1](task_01_state_envelope_events_and_stage_producers.md).

Downstream dependents (blocked by Task 2): `task_04`.

## References & Rollback

- [Epic HLD](lifecycle_telemetry_and_stage_progress_ui.en.md)
- **Rollback**: Revert task commit to restore `check_tasks.py`.
