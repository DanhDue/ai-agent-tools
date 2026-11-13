# Manual Smoke Walkthrough Checklist: Runtime Sync And Dashboard Hardening

> [!NOTE]
> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.
> Run through these 3–5 high-leverage user journeys before final sign-off.

| Step | Target (URL / CLI) | Action | Observable Outcome |
| :---: | :--- | :--- | :--- |
| 1 | `git repository` | _state_envelope.update_epic_heartbeat records a task transition and sync_task_status.py marks task_01 "in-progress" | .devtool/state/demo-sync.heartbeat.json is written atomically via os.replace to both the worktree and primary repository .devtool/state directories |
| 2 | `--quality-profile full` | scripts/estimate_heartbeat.py evaluates each input via CLI and Python API with --json | the micro fix (estimated_sec 35 < 60) returns tier "light" with recommended_interval_sec null, the feature wave (estimated_sec 80) returns tier "medium" with recommended_interval_sec 180, the full quality run (estimated_sec 250) returns tier "heavy" with 240, and the E2E run returns tier "heavy" with 300 |
| 3 | CLI / Workspace Root | both execute via Popen with start_new_session=True, a shortened test heartbeat interval, and shared devtool state directories | verify_polyglot_registry.py writes isolated logs under build/quality/<provider>/runs/<run_id>/<capability>.log without collisions while printing periodic "[quality_check]" progress lines to stderr |
| 4 | `git worktree` | resume_context.py --emit-prompt implement --epic demo-sync executes and skills/dev-lifecycle/references/handoff-template.md is rendered | both instruct the programmer orchestrator to run compute_execution_order.py --parallel, run estimate_heartbeat.py per wave and before Gate 4, execute multi-task waves across parallel pool slots, and invoke manage_worker_pool.py cleanup afterward |
| 5 | `git repository` | live slot transitions are observed while working and manage_worker_pool.py cleanup --epic-dir demo_epic --epic-slug demo-epic runs after slot integration | demo-epic.heartbeat.json initially records populated active_wave and slots ("working" with task_id) before cleanup |

## Sign-off
- [ ] All steps completed manually with expected outcomes verified.
- **Reviewer / Date:** __________________
