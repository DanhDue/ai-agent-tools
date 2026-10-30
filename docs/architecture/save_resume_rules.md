# Two-Tier Project Memory & Tri-Role Governance Telemetry

To maintain full project-wide architectural awareness across account rotations and among the **Human Architect**, **AI Assistant**, and **AI Programmer** personas without context bloat, enforce this 2-tier disk-backed state architecture.

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

## 3. Tri-Role Governance Model

1. **Role 2.1 — Human Architect (Developer):**
   - Strategic direction, Gate approvals (Gate 1, 2, 3, 5), and decisions at Review Choice.
2. **Role 2.2 — AI Assistant (`[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]`):**
   - Problem analysis, RFC drafting, HLD / Kanban task design, Principal Review, Cross-Model Review.
   - **Hard Restriction:** **STRICTLY PROHIBITED from modifying production code or application tests.** Only design docs (`docs/`, `.devtool/`, `shared-contracts/`) may be edited.
3. **Role 2.3 — AI Programmer (`[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]`):**
   - Execution of Kanban tasks inside isolated git worktrees following strict TDD (Red-Green-Refactor) and Clean Code standards.
   - **Hard Restriction:** **STRICTLY BOUND to approved specifications, `Decisions Already Made`, and `Allowed files`.** No speculative abstractions or unapproved contract changes.

## 4. CLI Capabilities & Workflow Cheatsheet

```bash
# 1. Startup Context Restoration
python3 scripts/resume_context.py [--role assistant|programmer] [--epic <slug>]

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
