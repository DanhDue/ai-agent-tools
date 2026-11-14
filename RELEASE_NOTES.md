# Release Notes: d3nexus v1.29.1

**Release Date:** November 14, 2026  
**Version:** `1.29.1`  
**Git Tag:** `v1.29.1`, `d3nexus--v1.29.1`

---

## Executive Summary

`v1.29.1` delivers automated **Kanban Task Status Synchronization & Heartbeat Slot Overlay**, embedding physical status transition gates directly in `dev-implementation` and `subagent-driven-development` workflows without rule bloat, adding `--status working|review|idle` and `--no-reset` to `manage_worker_pool.py`, automatically mapping active worker slots onto the Kanban Dashboard without dirtying the main worktree, and wiring task identities and execution waves into `lifecycle_runner.py`.

---

## Key Highlights

### 1. Physical Task Status Transition Gates
- **Workflow-Embedded Gates** (`skills/dev-implementation/SKILL.md`, `skills/subagent-driven-development/SKILL.md`): Embeds physical pre-dispatch, pre-review, and fix-loop transition gates directly in task execution skills instead of adding global rules, avoiding agent Focus Dilution.
- **Pool vs. Single-Worktree Discipline**: Enforces `manage_worker_pool.py sync --status working|review` in 2-slot pool mode (keeping `main_wt` clean) while gating `sync_task_status.py task <task_id> in-progress|review` for single-worktree runs, and ensures tasks run `done` + commit in slot before merging.

### 2. Worker Pool State Synchronization
- **Heartbeat Slot Management** (`skills/dev-implementation/resources/scripts/manage_worker_pool.py`): Adds `--status working|review|idle` and `--no-reset` to `sync`, allowing slots to update their execution status and assigned task IDs in `<epic_slug>.heartbeat.json`.
- **Uncommitted Change Preservation**: `--status review` and `--no-reset` preserve uncommitted implementation files and test evidence while updating slot telemetry.

### 3. Automated Kanban Dashboard Overlay
- **Clean In-Progress & Review Mapping** (`skills/check-tasks/resources/scripts/check_tasks.py`, `skills/check-tasks/resources/dashboard/tasks_dashboard.html`): Automatically maps tasks running in active pool slots from `todo` to `in-progress` or `review` on the Kanban Dashboard using heartbeat state, rendering slot badges (`slot-1`, `slot-2`) without touching tracked git files.
- **Review Progress Tracking**: Adds review task counts to the `TIẾN ĐỘ EPICS` sidebar in the dark-mode dashboard companion.

### 4. Autonomous Lifecycle Runner Enhancement
- **Task & Wave Propagation** (`skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`): Wires task IDs and execution wave numbers into slot synchronization during DAG batch execution, and safely resets slots to `idle` on rollback or merge failures.

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh --full --quiet`: **PASS — safe to publish** (Checks 1–10 + 56 test suites)
