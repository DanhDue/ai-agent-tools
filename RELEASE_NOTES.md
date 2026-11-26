# Release Notes: d3nexus v1.35.0

**Release Date:** November 26, 2026  
**Version:** `1.35.0`  
**Git Tag:** `v1.35.0`, `d3nexus--v1.35.0`

---

## Executive Summary

`v1.35.0` delivers end-to-end **Zero-Pause AUTO MODE** execution from Gate 2 through Stage 4 Finish, **immediate Tasks UI confirmation alert clearing** when resuming autonomous execution, **Section II Execution Tabs (`Doing` / `Pending` / `Cancelled`)** with confirmation reason dialogs and full Kanban/Overview synchronization, **dynamic Google profile discovery** in `check-quota`, and **native CLI trajectory recognition** in `audit-account-block`.

---

## Key Highlights

### 1. Tasks UI Execution Tabs (`Doing` / `Pending` / `Cancelled`) & Kanban Sync (`skills/check-tasks/`, `scripts/_state_envelope.py`)
- **3-Tab Execution Panel**: Section II (*Worktree & Profile (PIC) Execution*) now organizes active epics into `Doing`, `Pending`, and `Cancelled` tabs. `Doing` includes all active epics even before `handoff.md` is created.
- **Required-Reason Confirmation Dialog & Resume**: Clicking `Pending` or `Cancel` opens a confirmation modal requiring a reason, stores the override in `.devtool/state/epic_execution_state.json` (zero git/worktree mutations), suppresses active alerts for paused/cancelled epics, and displays the recorded reason alongside a one-click `Resume` button.
- **Kanban Filter, 5-Card Epics Overview & Zero-Jump UX**: Kanban defaults to `Doing` epics with a `Doing` / `Pending` / `Cancelled` sidebar filter, Epics Overview syncs all 5 status cards (`In-Progress`, `Pending`, `Backlog`, `Done`, `Cancelled`), panel heights stay locked across tab switches (top-center empty states), and `Strategic Notes` scrolls cleanly on long content.

### 2. Zero-Pause AUTO MODE Alignment (`rules/CRITICAL_RULES.md`, `skills/dev-lifecycle/`, `skills/principal-review/`, `skills/dev-implementation/`, `skills/cross-model-review/`, `skills/finishing-a-development-branch/`)
- Eliminates redundant confirmation pauses after Gate 2 Unified Confirmation (`Triển khai (tự động)`): `/principal-review` auto-fixes verified `Valid` findings across rounds without pausing, transitions straight past `package_epic.py` into `dev-implementation`, runs Gate 3 and `/cross-model-review` without intermediate stops, and combines Gate 5 with `/finishing-a-development-branch` into one final confirmation menu.
- Halts strictly on high-risk escalations (`ESCALATE`, `CRITICAL_CONFLICT`, `Debatable`, `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, `MAX_ROUNDS_CRITICAL_REMAINING`), quota/model stops, or final Stage 4 Finish.

### 3. Immediate Tasks UI Human-Confirmation Clearing (`check_tasks.py`, `resume_context.py`, `run_external_review.py`, `manage_worker_pool.py`, `lifecycle_runner.py`)
- Active review phases, worker-pool `init`/`working`/`review` syncs, `--clear-decision`, and `--confirm-fixes` immediately clear stale `pending_decision.json` entries and emit active heartbeats.
- `check_tasks.derive_lifecycle_state()` detects active non-paused heartbeats and live `quality_active.json` runs so the `HUMAN DECISION REQUIRED` banner clears instantaneously upon returning to AUTO MODE.

### 4. Dynamic Check-Quota Profile Discovery & Audit Hardening (`skills/check-quota/`, `skills/audit-account-block/`)
- Fetches live Google tier, email, and license metadata for Antigravity profiles with updated Quota Dashboard UI.
- Recognizes native CLI trajectories in `audit-account-block` to eliminate false-positive foreign trajectory alerts.

---

## Verifications & Quality Gates Passed

- `python3 -m pytest tests/test_tasks_ui_epic_execution_tabs.py -v` (3/3 passed, including 9-step live Headless Chrome CDP E2E verification with 0 console/runtime errors)
- `python3 -m unittest tests/test_check_tasks_fsm.py` (12/12 passed)
- `bash scripts/verify.sh --quiet` (all structural integrity checks & 90 test suites across 14 parallel workers: PASS)
