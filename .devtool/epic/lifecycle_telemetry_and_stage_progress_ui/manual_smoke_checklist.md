# Manual Smoke Walkthrough Checklist: Lifecycle Telemetry And Stage Progress Ui

> [!NOTE]
> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.
> Run through these 3–5 high-leverage user journeys before final sign-off.

| Step | Target (URL / CLI) | Action | Observable Outcome |
| :---: | :--- | :--- | :--- |
| 1 | `.devtool/state/` | `update_epic_heartbeat` is called 25 times with distinct `last_event` messages and `review_state={"kind": "code", "round": 1, "max_rounds": 3, "cli": "codex", "model": "gpt-6.1-sol", "phase": "reviewing"}` | `.devtool/state/demo_epic.heartbeat.json` contains an `events` list of length 20 |
| 2 | `["lint", "typecheck", "pycore", "integration", "e2e"]` | `_QualityRunCoordinator` starts step 1 (`"lint"`), completes it as `"passed"`, and starts step 3 (`"pycore"`) | `format_capability_label("python-qa", "pycore")` returns `"PyCore / Unit Test"` |
| 3 | `.devtool/epic/early_epic/2026-11-14-early-epic-design.en.md` | `scan_repo` harvests the repository metadata | `meta.active_epic` equals `"early_epic"` |
| 4 | `status: "done"` | `scan_repo` computes `task_progress` and `pipeline_telemetry` | `meta.task_progress.done_tasks` equals 9 and `meta.task_progress.total_tasks` equals 9 |
| 5 | `"done"` | `renderExecutionEpics` and `renderKanbanDashboard` render Section II and the Kanban board in `tasks_dashboard.html` | the rendered Section II HTML contains `"9 / 9 Hoàn thành"` and `"100%"` for Task Implementation |

## Sign-off
- [ ] All steps completed manually with expected outcomes verified.
- **Reviewer / Date:** __________________
