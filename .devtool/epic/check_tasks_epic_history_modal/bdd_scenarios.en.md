# BDD Scenarios: Check-Tasks Epic History Modal & Append-Only Telemetry

## Table of Contents

- [1. Happy Path Scenarios (HP)](#1-happy-path-scenarios-hp)
- [2. Edge Case Scenarios (EC)](#2-edge-case-scenarios-ec)
- [3. State Transition Scenarios (ST)](#3-state-transition-scenarios-st)
- [4. Architecture and Concurrency Scenarios (AR)](#4-architecture-and-concurrency-scenarios-ar)
- [5. Fault Resilience Scenarios (FR)](#5-fault-resilience-scenarios-fr)

---

## 1. Happy Path Scenarios (HP)

```gherkin
Scenario: [CEHM-HP-01] [Tier A - Unit] Untruncated append-only event stream records over 20 steps and archives dual hyphen-underscore heartbeats
Given an isolated git repository with epic "alpha_epic" inside `.devtool/state/`
When `update_epic_heartbeat` is invoked 25 times with distinct `last_event` values `"step-01"` through `"step-25"` and `resume_context.py --complete alpha_epic "Completed alpha"` runs while `.devtool/state/alpha_epic.heartbeat.json` also exists
Then `.devtool/state/alpha-epic.heartbeat.json` keeps at most 20 events before archival while `.devtool/archive/events_alpha-epic_*.jsonl` retains all 25 events `"step-01"` through `"step-25"`
And `.devtool/state/` no longer contains orphan `alpha-epic.heartbeat.json`, `alpha_epic.heartbeat.json`, or `logs/events_alpha-epic.jsonl` files

Scenario: [CEHM-HP-02] [Tier C - Integration] History aggregator stitches multi-source artifacts across hyphen and underscore variants for Done epics
Given a repository with completed epic "alignment_flow_hardening" in `PROJECT_LEDGER.md`, `.devtool/state/alignment-flow-hardening.heartbeat.json`, `.devtool/archive/heartbeat_alignment_flow_hardening_20261114_1200.json`, `.devtool/state/gate_ledger.jsonl`, `.devtool/archive/activity_alignment_flow_hardening_20261114_1200.log`, `task_01_alpha.md`, and `evidence/task_01_alpha.json`
When `harvest_epic_history(repo_path, "alignment_flow_hardening")` executes
Then the returned `epic["status"]` equals `"done"` and `pipeline_telemetry["stages"][5]["status"]` equals `"done"`
And `tasks` includes `"task_01_alpha"` with attached `evidence` summary `passed_rows`, `total_rows`, and `head` SHA
And `timeline` contains merged chronological events from `gate_ledger`, `heartbeat`, `activity_log`, and `evidence` sorted by UTC timestamp

Scenario: [CEHM-HP-03] [Tier C - Integration] History HTTP endpoint returns 6-stage summary, tasks, timeline, and both Principal and Cross-Model reviews
Given a running `TasksServer` over a temporary workspace containing repository "demo_repo" and epic "hist_epic" with `principal_review.md` (Round 1 and Round 2) and `review_results.md` (Round 1)
When a client requests `GET /api/epic/history?repo=demo_repo&epic=hist_epic&round_principal=2&round_cross=1`
Then HTTP status is 200 and JSON `reviews["principal"]["round"]` equals 2 with `available_rounds == [1, 2]`
And `reviews["cross_model"]["round"]` equals 1 with `present is True` and parsed `findings` rows
And `pipeline_telemetry["stages"]` contains 6 stages matching `compute_pipeline_telemetry`

Scenario: [CEHM-HP-04] [Tier C - Integration] Clicking any Roadmap epic row opens modal-epic-history keeping Section II untouched and switches tabs cleanly
Given `tasks_dashboard.html` rendered with an active running epic in Section II and Roadmap rows in Section III for `"done_epic"`, `"in_prog_epic"`, and `"backlog_epic"`
When the user clicks the `.roadmap-epic-row` for `"done_epic"`
Then `#modal-epic-history` opens with `style.display === "flex"` and displays the 6-stage pipeline stepper while Section II underneath continues displaying the active epic unchanged
And clicking the modal tabs switches directly between `Timeline & Step Logs`, `Tasks & Evidence`, `Principal Review`, and `Cross-Model Review` and switches Round 1 to Round 2 inside Review without opening a second stacked modal
```

---

## 2. Edge Case Scenarios (EC)

```gherkin
Scenario: [CEHM-EC-01] [Tier A - Unit] Unstarted Backlog and Packaged epics without logs, tasks, or reviews return clean empty history structures
Given a repository containing `.devtool/epic/draft_epic/2026-11-15-draft-epic-design.en.md` with no `task_*.md`, no `gate_ledger.jsonl` entry, no `events_*.jsonl`, and no review markdown
When `harvest_epic_history(repo_path, "draft_epic")` runs and `/api/epic/history?repo=<repo>&epic=draft_epic` is queried
Then HTTP status is 200 with `tasks == []`, `timeline == []`, `log_completeness == "none"`, and `reviews["principal"]["present"] is False` and `reviews["cross_model"]["present"] is False`
And `pipeline_telemetry["stages"]` returns all 6 stages with zero unhandled exceptions

Scenario: [CEHM-EC-02] [Tier A - Unit] Strict epic review lookup refuses falling back to unrelated repo-root review files
Given a repository where repo-root `.devtool/principal_review.md` and `.devtool/review_results.md` exist for `"other_epic"`, while `.devtool/epic/legacy_oct_epic/` has no review markdown files
When `parse_review_results(repo_path, active_epic="legacy_oct_epic", kind="cross-model", strict_epic=True)` executes
Then `result["present"]` equals `False` and `result["findings"]` equals `[]` and `result["verdict"]` equals `"UNKNOWN"`
And repo-root `review_results.md` content for `"other_epic"` is never leaked into `"legacy_oct_epic"`

Scenario: [CEHM-EC-03] [Tier C - Integration] Changing inline PIC dropdown inside Roadmap row updates PIC without opening modal-epic-history
Given `tasks_dashboard.html` rendered with a clickable `.roadmap-epic-row` containing a `renderPicSelect` `<select>` control in column 5
When a click event and change event fire on that `<select>` element to assign `@phungthuy8901`
Then event propagation does not trigger `openEpicHistoryModal` and `#modal-epic-history` remains hidden
```

---

## 3. State Transition Scenarios (ST)

```gherkin
Scenario: [CEHM-ST-01] [Tier A - Unit] Unified timeline deduplicates ring-buffer overlap with events JSONL and labels stream completeness
Given an epic `"stream_epic"` whose archived `events_stream-epic_*.jsonl` contains 22 entries (`e01`..`e22`) and whose `heartbeat` snapshot repeats trailing `e15`..`e22`, alongside a separate legacy epic `"snap_epic"` having only a 3-event `.heartbeat.json`
When `harvest_epic_history` aggregates `"stream_epic"` and `"snap_epic"`
Then `"stream_epic"` reports `log_completeness == "full_stream"` and contains all 22 unique step entries with zero duplicated `e15`..`e22` entries
And `"snap_epic"` reports `log_completeness == "snapshot_and_ledger"` and preserves all 3 heartbeat entries ordered deterministically by UTC timestamp

Scenario: [CEHM-ST-02] [Tier C - Integration] Open modal inspecting an In Progress epic prefers worktree tasks and preserves active tab across 5s poll refreshes
Given an active `"in_prog_epic"` whose `.worktrees/in_prog_epic/.devtool/features/task_01_live.md` is `"in-progress"` while root `.devtool/epic/in_prog_epic/task_01_live.md` says `"todo"`
When the user opens `#modal-epic-history` for `"in_prog_epic"`, switches to `"Cross-Model Review"` tab, and `pollDashboard()` executes a live tick after server data updates
Then `tasks[0]["status"]` reflects `"in-progress"` from the worktree source
And the silent refresh updates telemetry while keeping `"Cross-Model Review"` selected as the active tab inside `#modal-epic-history`

Scenario: [CEHM-ST-03] [Tier C - Integration] Closing modal-epic-history via close button, backdrop, or Escape restores scroll lock and detaches live refresh
Given `#modal-epic-history` is currently open (`style.display === "flex"` and `document.body.style.overflow === "hidden"`)
When the user closes it via the `✕` button, or clicks `.modal-backdrop`, or dispatches `KeyboardEvent("keydown", { key: "Escape" })`
Then `#modal-epic-history` hides (`style.display === "none"`), `document.body.style.overflow` resets to `""`, and subsequent `pollDashboard()` ticks do not re-fetch `/api/epic/history`
```

---

## 4. Architecture and Concurrency Scenarios (AR)

```gherkin
Scenario: [CEHM-AR-01] [Tier A - Unit] Concurrent update_epic_heartbeat callers write valid non-interleaved lines to events JSONL under transactional lock
Given 6 worker threads sharing an isolated git repo with root and worktree `.devtool` mirrors for epic `"concurrent_epic"`
When each thread calls `update_epic_heartbeat` 8 times concurrently with distinct worker-tagged `last_event` strings
Then every line in `.devtool/logs/events_concurrent-epic.jsonl` across both mirrors parses cleanly with `json.loads()`
And all 48 unique worker events are preserved without truncation or partial JSON corruption

Scenario: [CEHM-AR-02] [Tier C - Integration] Fast sequential clicks on Epic A then Epic B discard delayed Epic A HTTP responses via request token
Given mock `fetch()` where `/api/epic/history?repo=R&epic=epic_a` resolves after 120ms and `/api/epic/history?repo=R&epic=epic_b` resolves after 10ms
When the user clicks row `"epic_a"` and 5ms later clicks row `"epic_b"`
Then `#modal-epic-history` renders `"epic_b"` metadata and tasks
And when the delayed `"epic_a"` promise resolves later, `"epic_a"` content does not overwrite `"epic_b"` inside the modal DOM

Scenario: [CEHM-AR-03] [Tier C - Integration] History HTTP handler rejects missing query params with 400 and path traversal attempts with 400 or 404
Given a running `TasksServer` bound to an isolated temporary `workspace_root`
When requests arrive for `/api/epic/history?repo=demo` (missing `epic`), `/api/epic/history?repo=../etc&epic=passwd`, and `/api/epic/history?repo=demo&epic=../../secret`
Then the server responds with HTTP 400 or 404 JSON error payloads and accesses zero files outside `workspace_root`
```

---

## 5. Fault Resilience Scenarios (FR)

```gherkin
Scenario: [CEHM-FR-01] [Tier A - Unit] Malformed JSONL lines or corrupted evidence JSON fail softly per record without aborting epic history
Given an epic `"corrupt_epic"` containing one valid event line and one truncated JSON line `{bad` in `.devtool/logs/events_corrupt-epic.jsonl`, plus one malformed `evidence/task_01_broken.json` file alongside `task_01_broken.md`
When `harvest_epic_history(repo_path, "corrupt_epic")` executes
Then valid timeline events and `task_01_broken` markdown metadata are still returned cleanly with `evidence: null` on the broken task and zero raised exceptions

Scenario: [CEHM-FR-02] [Tier C - Integration] End-to-end headless Chrome CDP validates full modal forensics workflow, filters, error retry, and zero console errors
Given a live `TasksServer` backed by mock repositories containing `"done_epic"` (11 tasks with evidence, gate ledger, events stream, and 2-round Principal + Cross-Model reviews), `"in_prog_epic"`, and `"backlog_epic"`
When Playwright / Chrome CDP tests Roadmap click interactions, PIC select isolation, Timeline category filter chips (`All`, `Gates`, `Steps`, `Activity`, `Evidence`), expandable task verification rows, direct Principal <-> Cross-Model Review tab & round switching, HTTP 500 inline Retry banner recovery, and `ESC` dismissal
Then every asserted DOM panel renders accurate non-empty historical values while Section II remains intact underneath
And `cdp.consoleErrors` and `cdp.runtimeExceptions` are both `[]`
```
