# Release Notes: d3nexus v1.30.0

**Release Date:** November 14, 2026  
**Version:** `1.30.0`  
**Git Tag:** `v1.30.0`, `d3nexus--v1.30.0`

---

## Executive Summary

`v1.30.0` delivers real-time **Lifecycle Stage Telemetry & Stage Progress UI** across the `/check-tasks` dashboard and terminal monitor, enabling early Stage 1 activation right after brainstorming, a 6-stage interactive stepper with granular sub-step activity descriptions, dynamic event logging, weighted stage progress allocation, and an overview stage badge on the Kanban Epics card.

---

## Key Highlights

### 1. Early Stage 1 Activation & End-to-End Visibility
- **Immediate Brainstorming Tracking** (`skills/check-tasks/resources/scripts/check_tasks.py`): Epics appear on the dashboard immediately upon spec creation (`Stage 1 Inception`), providing end-to-end lifecycle visibility across all 5 stages before Kanban task decomposition.
- **Stage Progression Overview**: Adds an overview stage badge directly to the `TIẾN ĐỘ EPICS` sidebar card, allowing developers to see which stage every epic is in without opening detailed modals.

### 2. Granular Sub-Step Activity Telemetry
- **Live Activity Reporting** (`scripts/_state_envelope.py`, `skills/check-tasks/resources/scripts/check_tasks.py`): Replaces static stage labels with real-time descriptions of active operations:
  - **Quality Check**: Specific suites currently executing (PyCore testing, unit tests, integration tests, UI audits).
  - **External Reviews**: Active review round, reviewing model (`Codex -> Kiro -> Claude -> agy`), triage table synthesis, finding fixes, and re-verification.
  - **Task Implementation**: Current task title, active wave, and slot status.
- **Chronological Event Logs**: Preserves a rolling ring-buffer of up to 50 lifecycle events per epic with timestamps and formatted details.

### 3. Interactive 6-Stage Stepper & Event Logs UI
- **Visual Lifecycle Stepper** (`skills/check-tasks/resources/dashboard/tasks_dashboard.html`): Displays an interactive stepper featuring active pulsing glow effects, completed milestone markers, and live sub-step pills.
- **Expandable Logs Drawer**: Developers can toggle open a live event logs drawer directly below the progress bar to inspect historical step transitions.

### 4. Balanced Stage Progress Weighting
- **Proportional Weighting**: Allocates progress accurately across lifecycle stages (Inception 5%, Design 15%, Implementation 50%, Review 20%, Finished 10%).
- **Strict Completion Guarantees**: Ensures task implementation displays 100% when all tasks finish, and overall progress reaches 100% upon Gate 5 completion.

### 5. Worker Pool Slot State Isolation
- **Mirror Exclusion** (`scripts/_state_envelope.py`, `skills/dev-implementation/resources/scripts/sync_task_status.py`): Excludes ephemeral `-slot-N` pool worktrees from runtime `.devtool/state` synchronization, preventing merge conflicts during parallel task execution.

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh --full`: **PASS — safe to publish** (Checks 1–10 + 60 test suites across 14 workers)
