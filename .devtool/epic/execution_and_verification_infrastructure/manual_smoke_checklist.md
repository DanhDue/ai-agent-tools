# Manual Smoke Walkthrough Checklist: Execution And Verification Infrastructure

> [!NOTE]
> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.
> Run through these 3–5 high-leverage user journeys before final sign-off.

| Step | Target (URL / CLI) | Action | Observable Outcome |
| :---: | :--- | :--- | :--- |
| 1 | `git repository` | "detect_project_type.sh --all" is executed on the repository | it outputs "python web" it executes both the Python bootstrap phase (including the "bootstrap" command arrays from ".agents/quality/python-quality.json") and the Web dependency installation phase |
| 2 | `pytest output` | "record_failure_baseline.py --out baseline.txt" parses the output stream | "baseline.txt" contains the 2 sorted failure node IDs it reports 0 new failures and exits with code 0 |
| 3 | CLI / Workspace Root | "check_epic_readiness.py" evaluates R6 coverage for the epic | R6 passes with 0 missing Tier C test files the live integration row is recorded as "SKIPPED (missing env: EVI_LIVE_MODEL)" without failing Gate 4 the live integration row is executed and its exit status is enforced |
| 4 | `git worktree` | "replay_task_text.py" replays the task inside a temporary git worktree | test directives apply before "RED" rows, production directives apply before "MEASURE" rows, and all Verification commands pass the "MEASURE" rows run, create ".devtool/epic/sample_epic/evidence/bench.json", and record a passing "measure" entry in the task's evidence JSON |

## Sign-off
- [ ] All steps completed manually with expected outcomes verified.
- **Reviewer / Date:** __________________
