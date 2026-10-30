## Two-Tier Project Memory & Zero-Touch Handoff Telemetry

To maintain full project-wide architectural awareness across account rotations and between the **Architect (Assistant)** and **Worker (Implementer)** personas without context bloat, enforce this 2-tier disk-backed state architecture:

### 1. Tier 1 — Permanent Project Ledger (`.devtool/PROJECT_LEDGER.md`)
- **Role:** Long-term architectural memory & completed Epic history across the entire project lifecycle. Never delete this file.
- **When to Update:** Whenever an Epic/Feature is completed (or a core system invariant is locked), the Architect appends a concise 3–5 line milestone summary under `## Completed Epics & Milestones`.

### 2. Tier 2 — Active Feature State & Telemetry
- **Architect Snapshot (`.devtool/assistant_state.md`):**
  - Overwrite automatically (max 20 lines) whenever an architectural decision is locked, `shared-contracts/` is updated, or `task_*.md` files are emitted/reviewed.
  - Must include: `Active Epic`, `Recent Decisions Locked`, `Repo/Task Status`, and `Next Immediate Step`.
- **Implementer Stream (`.devtool/activity_stream.log`):**
  - After completing any user code request or finishing a `task_*.md`, the Implementer MUST append 1–3 lines:
    `[YYYY-MM-DD HH:MM] [<repo>/<task_id>] Request: <summary> | Action: <files & tests> | Note: <deviations or None>`

### 3. Session Startup & Feature Compaction (Log Rotation)
- **On Startup / Account Switch:** Run `python3 scripts/resume_context.py` (or inspect `PROJECT_LEDGER.md`, `assistant_state.md`, and the tail of `activity_stream.log`) to restore 100% context before answering.
- **On Feature Completion ONLY:** Do NOT clear logs on session exit. Only when an entire Epic/Feature is finished, run:
  `python3 scripts/resume_context.py --complete "<epic_slug>" "<1-line milestone summary>"`
  to append the milestone to `PROJECT_LEDGER.md` and archive `activity_stream.log` into `.devtool/archive/`.
