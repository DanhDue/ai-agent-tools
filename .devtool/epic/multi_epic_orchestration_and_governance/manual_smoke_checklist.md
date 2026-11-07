# Manual Smoke Walkthrough Checklist: Multi Epic Orchestration And Governance

> [!NOTE]
> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.
> Run through these 3–5 high-leverage user journeys before final sign-off.

| Step | Target (URL / CLI) | Action | Observable Outcome |
| :---: | :--- | :--- | :--- |
| 1 | CLI / Workspace Root | "check_epic_readiness.py epic_beta" executes before "epic_alpha" is merged to HEAD | R1, R5, and R7 pass with 0 failures because "src/alpha_helper.py" and "compute_alpha" resolve from "epic_alpha" it replays "epic_alpha" tasks first in the temporary worktree followed by "epic_beta" tasks and exits 0 |
| 2 | CLI / Workspace Root | "sync_task_status.py check-conflicts epic_gamma" runs | it reports "0 conflicts — safe for concurrent execution" and exits with code 0 all "backlog" tasks of "epic_gamma" in ".devtool/epic/epic_gamma/" and ".devtool/features/" transition to "todo" |
| 3 | CLI / Workspace Root | "package_epic.py <epic_dir>" runs on a passing readiness check | it writes ".devtool/epic/<epic_dir>/handoff.md" anchored to the current HEAD commit "handoff.md" updates "Design commit" to the new HEAD SHA and appends the revision entry under "## Revisions" |
| 4 | CLI / Workspace Root | "scripts/resume_context.py --gate 2 --epic sample-epic --approved 'HLD and 5 Kanban tasks' --deviations 'SE-01'" is executed | ".devtool/state/gate_ledger.jsonl" records a JSON entry with "epic": "sample-epic", "gate": 2, "approved": "HLD and 5 Kanban tasks", "deviations": "SE-01", and the current commit SHA |

## Sign-off
- [ ] All steps completed manually with expected outcomes verified.
- **Reviewer / Date:** __________________
