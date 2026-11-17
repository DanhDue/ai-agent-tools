# Two-Tier Project Memory & Four-Persona Governance Telemetry

To maintain full project-wide architectural awareness across account rotations and among the **Human Architect**, **AI Architect & Reviewer**, **Orchestrator**, and **Programmer** personas without context bloat, enforce this 2-tier disk-backed state architecture.

## 1. Tier 1 — Permanent Project Ledger (`.devtool/PROJECT_LEDGER.md`)

- **Role:** Long-term architectural memory & completed Epic history across the entire project lifecycle. Never delete this file.
- **When to Update:** Whenever an Epic/Feature is completed (or a core system invariant is locked), append a concise 1–3 line milestone summary under `## 2. Completed Epics & Architectural Milestones`:
  `- **[YYYY-MM-DD] \`<epic_slug>\`**: <milestone summary>`

## 2. Tier 2 — Multi-Epic Partitioned State & Telemetry

To support concurrent AI agents without cross-epic state overwrites or premature log rotation, Tier 2 state is partitioned per epic under exclusive file locking (`.devtool/.memory.lock` via `fcntl.flock`):

### 2.1 Per-Epic State Snapshots (`.devtool/state/<epic_slug>.md`)
- **Ceiling:** Hard limit of 20 lines (`MAX_STATE_LINES = 20`).
- **Trigger:** Written via `python3 scripts/resume_context.py --state --epic <slug>` whenever an architectural decision is locked, `shared-contracts/` is updated, or tasks transition status.
- **Mandatory Sections:**
  1. `# Active Epic: <epic_slug>` (includes role and timestamp)
  2. `## Recent Decisions Locked:`
  3. `## Repo/Task Status:`
  4. `## Next Immediate Step:`
  5. `## Custom Prompt / Notes:` (optional)
- **Auto-Rollup:** Every `--state` write regenerates `.devtool/assistant_state.md` by concatenating all active `.devtool/state/*.md` files.

### 2.2 Per-Epic Programmer Activity Stream (`.devtool/logs/activity_<epic_slug>.log`)
- **Trigger:** Written via `python3 scripts/resume_context.py --log --epic <slug> --task <task_id> --request "<req>" --action "<action>" --note "<note>"` after completing any task or code request.
- **Format:**
  `[YYYY-MM-DD HH:MM] [<repo>/<epic_slug>/<task_id>] Request: <summary> | Action: <files & tests> | Note: <deviations or None>`
- **Auto-Rollup:** Every `--log` write refreshes `.devtool/activity_stream.log` with the last 50 entries across all active epic logs.

## 3. Four-Persona Governance Model

1. **Role 1.0 Human Architect (Developer):**
   - Vision, strategic direction, Gate approvals (Gates 1, 2, 5), Stage 4 Finish, and every escalation.
2. **Role 2.1 AI Architect & Reviewer (`[PERSONA: Role 2.1 AI Architect & Reviewer]`, `--role architect`; `assistant` remains an alias):**
   - Stages 1–2 design (`dev-brainstorming`, `dev-designer`), Principal Review (`principal-review`), and packaging; Stage 3 `task-reviewer` and `fix-planner` subagents (`--mode read-only`).
   - **Hard Restriction:** **STRICTLY PROHIBITED from editing `src/` or `tests/`, running test suites, linters, or type checkers, dispatching subagents, or managing the worker pool.**
3. **Role 2.2 Orchestrator (`[PERSONA: Role 2.2 Orchestrator]`, `--role orchestrator`):**
   - Stage 3–4 orchestration: Gate 3, worker pool management (`manage_worker_pool.py`), dispatching Role 2.1 and Role 2.3 subagents, independent verification, lifecycle checkpoints, `/cross-model-review`, and marking tasks `done`.
   - **Hard Restriction:** **STRICTLY PROHIBITED from reading or editing `src/` or `tests/`, editing HLD, BDD scenarios, Verification tables, DoD, or `Allowed files`, or running tests, linters, type checkers, `run_task_checks.py`, or `verify-tier`.**
4. **Role 2.3 Programmer (`[PERSONA: Role 2.3 Programmer — Senior TDD Software Engineer]`, `--role programmer`):**
   - Isolated `task-implementer`, `review-fixer`, and `gate4-verifier` subagent execution inside git worktrees following strict TDD (Red-Green-Refactor) and Clean Code standards.
   - **Hard Restriction:** **STRICTLY BOUND to approved specifications, `Decisions Already Made`, and `Allowed files`.** Never alters HLD, BDD scenarios, `shared-contracts/`, Verification tables, DoD, or `Allowed files`, and never calls `manage_worker_pool.py`.

## 4. CLI Capabilities & Workflow Cheatsheet

```bash
# 1. Startup Context Restoration
python3 scripts/resume_context.py [--role architect|orchestrator|programmer] [--epic <slug>]

# 2. Persist State Snapshot (<= 20 lines)
python3 scripts/resume_context.py --state --epic <slug> --decisions "<text>" --status "<text>" --next "<text>"

# 3. Append Programmer Activity Entry
python3 scripts/resume_context.py --log --epic <slug> --task <id> --request "<text>" --action "<text>"

# 4. Feature Completion & Compaction (Archives single epic state/log)
python3 scripts/resume_context.py --complete <slug> "<milestone summary>"

# 5. Non-Destructive Checkpoint (Saves state/log without archiving)
python3 scripts/resume_context.py --complete <slug> "<custom prompt>" --checkpoint

# 6. Emit Role-Bound Handoff Prompt
python3 scripts/resume_context.py --emit-prompt <principal-review|implement|cross-review|finish|assistant> --epic <slug>

# 7. Shell Environment & History Sync
python3 scripts/resume_context.py --sync-zshrc
```
