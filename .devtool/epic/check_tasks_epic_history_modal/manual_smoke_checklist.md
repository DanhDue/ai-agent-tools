# Manual Smoke Walkthrough Checklist: Check Tasks Epic History Modal

> [!NOTE]
> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.
> Run through these 3–5 high-leverage user journeys before final sign-off.

| Step | Target (URL / CLI) | Action | Observable Outcome |
| :---: | :--- | :--- | :--- |
| 1 | `.devtool/state/` | `update_epic_heartbeat` is invoked 25 times with distinct `last_event` values `"step-01"` through `"step-25"` and `resume_context.py --complete alpha_epic "Completed alpha"` runs while `.devtool/state/alpha_epic.heartbeat.json` also exists | `.devtool/state/alpha-epic.heartbeat.json` keeps at most 20 events before archival while `.devtool/archive/events_alpha-epic_*.jsonl` retains all 25 events `"step-01"` through `"step-25"` |
| 2 | `PROJECT_LEDGER.md` | `harvest_epic_history(repo_path, "alignment_flow_hardening")` executes | the returned `epic["status"]` equals `"done"` and `pipeline_telemetry["stages"][5]["status"]` equals `"done"` |
| 3 | `TasksServer` | a client requests `GET /api/epic/history?repo=demo_repo&epic=hist_epic&round_principal=2&round_cross=1` | HTTP status is 200 and JSON `reviews["principal"]["round"]` equals 2 with `available_rounds == [1, 2]` |
| 4 | `tasks_dashboard.html` | the user clicks the `.roadmap-epic-row` for `"done_epic"` | `#modal-epic-history` opens with `style.display === "flex"` and displays the 6-stage pipeline stepper while Section II underneath continues displaying the active epic unchanged |

## Sign-off
- [ ] All steps completed manually with expected outcomes verified.
- **Reviewer / Date:** __________________
