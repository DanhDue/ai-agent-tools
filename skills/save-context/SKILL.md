---
name: save-context
description: Persists architectural decisions, active epic states, and programmer activity logs under fcntl.flock concurrency protection, emits role-bound handoff prompts, or completes and archives epic features into the permanent project ledger.
---

# Save Context

## Overview

Persists conversational decisions, active feature states, and programmer activity logs to disk so that work can be resumed seamlessly across account rotations or multi-agent sessions without context degradation.

**Core principle:** Document decisions and progress on disk as they happen.

**Announce at start:** "I'm using the save-context skill to persist project memory and state."

## When to Use

- When an architectural decision, trade-off, or design choice is agreed upon.
- After completing a code request, Kanban task, or bug fix.
- Before switching accounts, closing a session, or handing off to another agent.
- Upon finishing an entire epic in Stage 4 (`/finish`).

## Operations & CLI Commands

### 1. Persist State Snapshot (`--state`)

Records an architectural or task status snapshot into `.devtool/state/<epic_slug>.md` ($\le 20$ lines) and refreshes `.devtool/assistant_state.md`:

```bash
python3 scripts/resume_context.py --state \
  --epic <epic_slug> \
  --decisions "<bullet list of key decisions>" \
  --status "<current stage or task status>" \
  --next "<immediate next step>" \
  [--prompt "<custom note for next session>"]
```

### 2. Append Programmer Activity Entry (`--log`)

Appends a structured log entry to `.devtool/logs/activity_<epic_slug>.log` and updates `.devtool/activity_stream.log`:

```bash
python3 scripts/resume_context.py --log \
  --epic <epic_slug> \
  --task <task_id> \
  --request "<summary of user request>" \
  --action "<files modified and test results>" \
  --note "<deviations, trade-offs, or None>"
```

### 3. Non-Destructive Checkpoint (`--complete --checkpoint`)

Saves in-flight state and logs without archiving the epic or adding milestones to the permanent ledger:

```bash
save-context --checkpoint <epic_slug> "<checkpoint note / next immediate goal>"
```

### 4. Emit Role-Bound Handoff Prompt (`--emit-prompt`)

Generates a ready-to-copy handoff prompt locking the target agent into the appropriate persona:

```bash
python3 scripts/resume_context.py --emit-prompt <mode> --epic <epic_slug> [--epic-dir <dir>] [--prompt "<custom_note>"]
```

Supported modes:
- `principal-review`: Emits **AI Assistant** prompt for Stage 2 Principal Review.
- `implement`: Emits **AI Programmer** prompt for `/dev-implementation` (Stage 3).
- `cross-review`: Emits **AI Assistant** prompt for Cross-Model Review (Gate 4 PASS).
- `finish`: Emits **AI Programmer** prompt for `/finish` (Stage 4).
- `assistant`: Emits **AI Assistant** prompt for general architectural discussions.

### 5. Feature Completion & Compaction (`--complete`)

Executed in `/finish` (Stage 4 Pre-Finish Hook) when an entire epic is complete:

```bash
python3 scripts/resume_context.py --complete <epic_slug> "<milestone summary>"
```

- Appends a permanent milestone to `.devtool/PROJECT_LEDGER.md`:
  `- **[YYYY-MM-DD] \`<epic_slug>\`**: <milestone summary>`
- Moves `.devtool/state/<epic_slug>.md` and `.devtool/logs/activity_<epic_slug>.log` into `.devtool/archive/`.
- Re-renders `.devtool/assistant_state.md` and `.devtool/activity_stream.log` from remaining active epics.

## Concurrency Protection

All writes acquire an exclusive POSIX advisory lock via `fcntl.flock` on `.devtool/.memory.lock`. This guarantees that concurrent AI agents running in parallel across multiple epics or repositories do not interleave or corrupt disk state.

## Related Skills

- [resume-context](../resume-context/SKILL.md): Restores context and enforces role discipline on startup.
- [dev-lifecycle](../dev-lifecycle/SKILL.md): Orchestrates the 4-stage development lifecycle.
- [finishing-a-development-branch](../finishing-a-development-branch/SKILL.md): Handles branch landing and epic completion.
