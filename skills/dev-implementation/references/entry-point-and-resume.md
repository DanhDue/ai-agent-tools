# Entry-Point Detection and Resume Procedure

Read when: you start or resume an epic in `d3nexus:dev-implementation`, before Phase 1, to decide where Stage 3 begins.

## Entry-Point Detection

Read these signals, all read-only, from the main checkout:

```bash
test -f .devtool/epic/<epic_dir>/handoff.md && echo packaged-handoff
test -f .devtool/epic/<epic_dir>/principal_review.md && python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --kind principal --epic-dir <epic_dir>
HLD=".devtool/epic/<epic_dir>/<epic_dir>.md"; [ -f "$HLD" ] || HLD=".devtool/epic/<epic_dir>/<epic_dir>.en.md"; grep -m1 -E '^- \*\*Status\*\*:' "$HLD"
git rev-parse --verify --quiet refs/heads/epic/<epic_slug>
for remote in $(git remote); do git ls-remote --heads "$remote" "epic/<epic_slug>"; done
git worktree list --porcelain | grep -E '^worktree .*/\.worktrees/<epic_dir>$'
python3 "$SKILL_DIR"/resources/scripts/compute_execution_order.py <epic_slug> \
  --features-dir .devtool/epic/<epic_dir>
```

If the HLD declares `- **Depends on epic**:`, verify prerequisites first:
```bash
python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py check-prereqs <epic_dir>
```
If this exits `1`, halt immediately and report the blocking prerequisite epics. Do not proceed to execution until all prerequisite epics are finished and merged into `develop` (or the target base branch).

`git ls-remote` asks each remote directly, so an epic branch pushed from another clone shows before any fetch; if a remote cannot be reached, fall back to `git branch -r --list '*/epic/<epic_slug>'`. The last command reads the epic's task mirrors (`sync_task_status.py` keeps them in step with `.devtool/features/` and `.devtool/features/done/`); its flattened order prints each task's status as `[priority, status]`. Evaluate the rows top-down — first match wins — and announce it: "Entry point: row N — <state>."

| # | Signals | State | Entry point |
|---|---------|-------|-------------|
| 1 | Overview Status is `Done` | Finished, or Stage 4 interrupted | With no epic branch left, report finished and stop. With epic branch still present, Stage 4 was interrupted or its PR is still open: report and ask |
| 2 | No epic branch, and any task is `backlog` | Queued behind another epic | Stop. Check conflicts via `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py check-conflicts <epic_dir>`, and promote tasks to `todo` via `sync_task_status.py promote <epic_dir> [--force]` when confirmed |
| 3 | No epic branch locally or on remote, no worktree, every task `todo` | Not started — packaged if `handoff.md` exists | Phase 1 as written: Gate 3, then new worktree |
| 4 | Epic branch exists, no worktree, some task not `done` | Interrupted, worktree removed | Resume Procedure |
| 5 | Worktree exists, some task not `done` | Interrupted midway through Stage 3 | Resume Procedure |
| 6 | Epic branch exists, every task `done` | Tasks finished | Recreate worktree if missing (`git worktree add .worktrees/<epic_dir> epic/<epic_slug>`, no `-b`) and bootstrap (Phase 1 step 5), run Resume Procedure preflight (step 2), then Phase 4 in full; its PASS transitions automatically to `/cross-model-review` |
| 7 | Anything else — branch only on remote, or tasks `in-progress` or `done` with no epic branch | Inconsistent | Stop, report signals, ask |

## Resume Procedure

For rows 4 and 5. Phase 1 step 4's `git worktree add -b` never runs here.

1. Row 4 only: recreate worktree from existing branch, `git worktree add .worktrees/<epic_dir> epic/<epic_slug>` with no `-b`. For rows 4 and 5, check bootstrap with Phase 1 step 5's platform checks and re-run if needed.
2. In the worktree, run `python3 "$INTEGRATE" preflight --base develop`. A rebase in progress, or diverged base, is handled per Phase 2 step 7 before anything else.
3. Find the interrupted task: one at `in-progress` or `review`. If worktree has uncommitted changes, collect `git status --short`.
4. **Gate 3 (resume).** Check mirror scan summary against task mirror count and read Manual review advised section. State the Principal Review status (`not run`, `round <n>: PASS`, or `round <n>: decided`), and stop with the triage if that check exits 1. Run Phase 1 step 3's BDD mapping check and task contract check, including retrofit if needed. Commit any retrofit on epic branch staging only touched files (English `bdd_scenarios`, HLD, and task files — never `git add -A`). The interrupted task's own status fields may ride along in that commit; that is expected. In AUTO MODE (`Triển khai (tự động)`) with a clean worktree (no uncommitted changes) and no diverged base or blockers, log tasks already `done` + remaining order and proceed directly without waiting for confirmation; pause and wait for confirmation only if uncommitted changes exist (keep or discard), the base diverged, or a high-risk blocker is detected.
5. If overview Status begins with `Packaged`, run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`.
6. Enter Phase 2 at the interrupted task — a task at `review` re-enters at Phase 2 step 2; a task at `in-progress` resumes implementation with kept changes — or at the first remaining task.
