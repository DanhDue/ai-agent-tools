# BDD Scenarios: Lifecycle Telemetry, Stage Sub-Steps & Progress Bar UI

## Table of Contents

- [1. Happy Path Scenarios (HP)](#1-happy-path-scenarios-hp)
- [2. Edge Case Scenarios (EC)](#2-edge-case-scenarios-ec)
- [3. State Transition Scenarios (ST)](#3-state-transition-scenarios-st)
- [4. Architecture and Concurrency Scenarios (AR)](#4-architecture-and-concurrency-scenarios-ar)
- [5. Fault Resilience Scenarios (FR)](#5-fault-resilience-scenarios-fr)

---

## 1. Happy Path Scenarios (HP)

```gherkin
Scenario: [LTSP-HP-01] [Tier A - Unit] Heartbeat envelope maintains a bounded 20-entry rolling event log and structured review_state
Given a git repository with an initialized `.devtool/state/` directory for epic "demo_epic"
When `update_epic_heartbeat` is called 25 times with distinct `last_event` messages and `review_state={"kind": "code", "round": 1, "max_rounds": 3, "cli": "codex", "model": "gpt-6.1-sol", "phase": "reviewing"}`
Then `.devtool/state/demo_epic.heartbeat.json` contains an `events` list of length 20
And `events[0]["message"]` equals `"event-06"` and `events[-1]["message"]` equals `"event-25"`
And `review_state["phase"]` equals `"reviewing"` and `review_state["cli"]` equals `"codex"`

Scenario: [LTSP-HP-02] [Tier A - Unit] Polyglot quality runner maps capability labels and records per-step status and distinct start/completion events
Given a quality manifest for provider "python-qa" with capabilities `["lint", "typecheck", "pycore", "integration", "e2e"]`
When `_QualityRunCoordinator` starts step 1 (`"lint"`), completes it as `"passed"`, and starts step 3 (`"pycore"`)
Then `format_capability_label("python-qa", "pycore")` returns `"PyCore / Unit Test"`
And `format_capability_label("python-qa", "integration")` returns `"Integration Test"`
And `format_capability_label("python-qa", "e2e")` returns `"UI / E2E Test"`
And `quality_active.json` `runs[run_id]["steps"]` contains 5 entries where step `"lint"` has status `"passed"` and step `"pycore"` has status `"running"` and label `"PyCore / Unit Test"`
And `<epic_slug>.heartbeat.json` `events` preserves both the `"lint"` start (`"running..."`) and completion (`"-> passed"`) events as separate entries without deduplication collapse

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

Scenario: [LTSP-HP-05] [Tier C - Integration] Tasks dashboard renders 6-stage stepper, sub-step micro-tracker, 100% task badge, rolling event logs, and Kanban TIẾN ĐỘ EPICS stage overview
Given a repository payload where 9 of 9 tasks are `"done"`, Cross-Model Review Round 1 (`codex / gpt-6.1-sol`) is in `"triage"` phase, and `heartbeat.events` has 5 timestamped entries
When `renderExecutionEpics` and `renderKanbanDashboard` render Section II and the Kanban board in `tasks_dashboard.html`
Then the rendered Section II HTML contains `"9 / 9 Hoàn thành"` and `"100%"` for Task Implementation
And `[data-telemetry="pipeline-stepper"]` renders all 6 lifecycle stages with `"Tasks"` marked completed (`100%`) and `"Cross-Review"` marked active
And `[data-telemetry="sub-steps"]` renders the 4 review micro-steps `"Reviewing"`, `"Lập bảng triage"`, `"Fix findings"`, and `"Verifying"` with `"Round 1/3"` and `"codex"`
And `[data-telemetry="event-logs"]` renders the latest timestamped heartbeat events
And the Kanban `"TIẾN ĐỘ EPICS"` sidebar card renders the weighted lifecycle progress percentage, `"9/9 Tasks (100%)"`, and `[data-telemetry="kanban-epic-stage"]` showing the current stage and micro-step overview

Scenario: [LTSP-HP-06] [Tier C - Integration] End-to-end headless Chrome CDP verifies live stage and micro-step transitions from Tasks to Quality Check to Cross-Model Review
Given a live `TasksServer` serving `tasks_dashboard.html` in headless Chrome CDP
When the server state transitions from Wave 2 Task Implementation (`8/9 tasks`) to All Tasks Done (`9/9 · 100%`) running Quality Check (`PyCore / Unit Test 3/5`) to Cross-Model Review Round 1 (`codex reviewing -> Lập bảng triage -> Fix findings -> Verifying`)
Then `pollDashboard()` updates Section II in-place without reloading the page
And the Task Implementation indicator displays `"9 / 9 Hoàn thành"` and `"100%"`
And the active sub-step strip displays `"PyCore / Unit Test"` during Quality Check and `"Round 1/3"` with `"Lập bảng triage"` and `"Fix findings"` during Cross-Model Review
And `cdp.consoleErrors` and `cdp.runtimeExceptions` are both `[]`
```

---

## 2. Edge Case Scenarios (EC)

```gherkin
Scenario: [LTSP-EC-01] [Tier A - Unit] Consecutive identical heartbeat events are deduplicated in the events ring buffer
Given an epic heartbeat file `.devtool/state/dedup_epic.heartbeat.json`
When `update_epic_heartbeat` is called 5 times in a row with the same `last_event="wave 1 polling"`
Then `heartbeat["events"]` contains exactly 1 entry with `message == "wave 1 polling"` and its `ts` updated to the latest timestamp

Scenario: [LTSP-EC-02] [Tier A - Unit] Dormant backlog and abandoned epic directories do not trigger active_epic even if abandoned epic retains Gate 1 or heartbeat
Given a repository containing `.devtool/epic/dormant_backlog/dormant_backlog.en.md` with `- **Status**: Backlog` and `.devtool/epic/abandoned_old/abandoned_old.en.md` with `- **Status**: Abandoned` plus a retained Gate 1 entry and `.devtool/state/abandoned_old.heartbeat.json`
When `resolve_active_epic` and `harvest_epics_overview` inspect the repository
Then `resolve_active_epic` returns `None`
And the `"dormant_backlog"` entry in `epics_summary.epics` has `status` equal to `"unstarted"` and `"abandoned_old"` has `status` equal to `"abandoned"`

Scenario: [LTSP-EC-03] [Tier C - Integration] Dashboard degrades gracefully when legacy payloads omit pipeline_telemetry or events
Given a legacy `/api/tasks` repository payload without `pipeline_telemetry` or `heartbeat.events` where `done_tasks == 4` and `total_tasks == 4`
When `renderExecutionEpics` and `renderKanbanDashboard` execute in the DOM harness
Then zero JavaScript exceptions are thrown
And `computeEpicProgressState` synthesizes `taskPct == 100` for task completion and a valid `pct` for lifecycle progress

Scenario: [LTSP-EC-04] [Tier C - Integration] Expandable event log drawer preserves expanded state across live pollDashboard ticks
Given a repository card in `tasks_dashboard.html` with 8 heartbeat events where the user clicks the toggle button to expand all event logs
When `pollDashboard()` runs on the next polling tick with a new 9th heartbeat event
Then the event log container remains expanded and displays all 9 events without collapsing back to the 4-line preview
```

---

## 3. State Transition Scenarios (ST)

```gherkin
Scenario: [LTSP-ST-01] [Tier A - Unit] External review runner transitions review_state through reviewing, triage, fixing, and verifying phases
Given an epic directory `.devtool/epic/rev_epic` with a completed Round 1 in `review_results.md` containing 1 Important finding
When `run_external_review.py triage --epic-dir rev_epic` and `run_external_review.py status --epic-dir rev_epic --phase fixing` and `run_external_review.py status --epic-dir rev_epic --phase verifying` are invoked sequentially
Then `.devtool/state/rev_epic.heartbeat.json` records `review_state["phase"]` transitioning from `"triage"` (`action == "AUTO_FIX_ELIGIBLE"`) to `"fixing"` to `"verifying"`
And `events` records each phase transition in chronological order

Scenario: [LTSP-ST-02] [Tier A - Unit] Lifecycle progress percentage advances monotonically across all 6 stages and requires full Gate 4 on latest SHA before 98% Finish
Given an epic progressing sequentially through: (1) Stage 1 Spec, (2) Stage 2 HLD + Principal Review Round 1, (3) Stage 3 Tasks 2/4 Done, (4) Stage 3 Tasks 4/4 Done + quality_check capabilities passed without Epic Audit/BDD (`87%`), (5) Full Gate 4 PASS (`88%`) + Cross-Model Review Round 2 + post-review Gate 4 re-verification running (`96%`), (6) Review Converged AND Gate 4 PASS on latest HEAD SHA (`98%` Waiting Finish), and (7) Gate 5 Done (`100%`)
When `build_epic_pipeline_telemetry` computes `(task_completion_pct, lifecycle_progress_pct)` at each state
Then `lifecycle_progress_pct` strictly increases across states `(1) < (2) < (3) < (4) < (5) < (6) < (7)` ending at `100.0`
And `task_completion_pct` equals `0.0` at `(1)-(2)`, `50.0` at `(3)`, and `100.0` for all states `(4)` through `(7)`

Scenario: [LTSP-ST-03] [Tier C - Integration] Quality Check sub-steps transition visually from Static Lint to Typecheck to PyCore/Unit Test to UI/E2E Test
Given `quality_active.json` with a running `python-qa` run whose `steps` array transitions from step 1 (`Static Lint`: `passed`), step 2 (`Typecheck`: `passed`), step 3 (`PyCore / Unit Test`: `running`), to step 4 (`UI / E2E Test`: `pending`)
When `renderExecutionEpics` renders the card
Then `[data-telemetry="quality"]` displays completed checkmarks for `"Static Lint"` and `"Typecheck"`, an active running badge for `"PyCore / Unit Test"`, and a pending indicator for `"UI / E2E Test"`

Scenario: [LTSP-ST-04] [Tier C - Integration] Commit-based fix and verification detection infers fixing after commit and verifying only when verification executes
Given an epic worktree where `review_results.md` Round 1 recorded `SHA: <sha1>` with `Verdict: CHANGES REQUIRED` and 1 Important finding
When a new commit `<sha2>` with subject `"[REV_EPIC] Fix validation edge case"` is committed in the worktree and `fixed in <sha2>` is recorded in `review_results.md`, and subsequently a verification run (`quality_active.json` or `run_external_review.py status --phase verifying`) starts on `<sha2>`
Then `build_epic_pipeline_telemetry` infers the Cross-Model Review Round 1 micro-step as `"fixing"` immediately after `<sha2>` and transitions to `"verifying"` once the verification execution starts on `<sha2>`
```

---

## 4. Architecture and Concurrency Scenarios (AR)

```gherkin
Scenario: [LTSP-AR-01] [Tier A - Unit] Multi-process concurrent heartbeat event updates preserve all distinct events under flock
Given 4 concurrent worker processes calling `update_epic_heartbeat` with distinct `last_event` strings on the same repository
When all 4 processes complete
Then `.devtool/state/<epic>.heartbeat.json` in both primary root and worktree mirror have identical `generation` and `events` lists containing all 4 events without corruption

Scenario: [LTSP-AR-02] [Tier C - Integration] Section II tier2Sig detects sub-step, review_state, quality step, and event log changes without clobbering sibling Roadmap focus
Given the dashboard rendered in headless Chrome CDP with focus held on a Roadmap PIC `<select>` control
When `/api/tasks` updates only `heartbeat.review_state.phase` from `"triage"` to `"fixing"` and appends an entry to `heartbeat.events`
Then `pollDashboard()` updates Section II immediately to show `"Fix findings"` while `document.activeElement` remains on the focused Roadmap `<select>`

Scenario: [LTSP-AR-03] [Tier C - Integration] Multi-epic workspace isolates pipeline_telemetry per epic across active and secondary in-progress epics
Given a repository with primary `active_epic` `"epic_alpha"` in Stage 3 Cross-Model Review (`4/4 tasks · 100%`) and secondary `in_progress` `"epic_beta"` in Stage 2 Principal Review (`0/3 tasks · 0%`)
When `scan_repo` and `renderExecutionEpics` render both epic cards
Then `"epic_alpha"` displays `100%` task completion and Stage 5 Cross-Model Review active, while `"epic_beta"` displays `0%` task completion and Stage 2 HLD & Principal Review active without cross-epic state bleed
```

---

## 5. Fault Resilience Scenarios (FR)

```gherkin
Scenario: [LTSP-FR-01] [Tier A - Unit] Telemetry write errors inside run_external_review.py or audit_epic.py never abort the underlying CLI command
Given a repository where `.devtool/state/` is temporarily read-only (`chmod 0555`)
When `audit_epic.py` or `run_external_review.py triage` executes
Then the command still completes with exit code `0` and emits its normal stdout report without raising an unhandled `PermissionError`

Scenario: [LTSP-FR-02] [Tier C - Integration] Failed or aborted quality step and Circuit Breaker review halt render explicit error badges in the stage stepper
Given a repository payload where `quality_active` has `status: "failed"` on capability `"integration"` (`"Integration Test"`) or `review_state` has `action: "CIRCUIT_BREAKER_HALT"`
When `renderExecutionEpics` renders the card
Then the corresponding stage and sub-step chip render a failure/halt alert state with the exact failed capability or circuit-breaker reason and zero console errors

Scenario: [LTSP-FR-03] [Tier C - Integration] Corrupted or truncated review_results.md / heartbeat.json files recover cleanly during pipeline harvesting
Given an epic worktree with truncated JSON in `.heartbeat.json` and malformed markdown table rows in `review_results.md`
When `scan_repo` harvests the repository
Then `scan_repo` completes without raising an exception and returns a valid `pipeline_telemetry` structure with 6 stages
```
