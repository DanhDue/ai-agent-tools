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
# Portable across all repos and worktrees via `d3nexus resume-context` (or `python3 scripts/resume_context.py`)
d3nexus resume-context --state \
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

### 3. Lifecycle Checkpoint (`--checkpoint <event>`)

Writes a structured checkpoint block into the per-epic heartbeat (`.devtool/state/<epic_slug>.heartbeat.json`), updates `Next Immediate Step` in `.devtool/state/<epic_slug>.md`, and appends a `checkpoint` event to `events_<epic_slug>.jsonl`, all under the same lock. Plain `resume_context.py` prints the latest checkpoint first, so a fresh session resumes from it:

```bash
python3 scripts/resume_context.py --checkpoint <event> --epic <epic_slug> [--next "<next step>"]
```

Events: `gate2_tasks_locked` (Role 2.1, right after Gate 2), `subagent_returned` (Role 2.2, after each summary contract and before the next dispatch), `wave_merged` (Role 2.2, after every wave merge), `model_unavailable`, `turn_budget`, `low_quota_stop`, `quota_low`. In low-quota mode (`/d3nexus:dev-config low-quota on`) the Orchestrator writes `low_quota_stop`, prints `--emit-prompt implement`, records `--pending-decision`, and stops.

### 3b. Non-Destructive Checkpoint (`--complete --checkpoint`)

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
- `principal-review`: Emits **Role 2.2 Orchestrator** prompt for Stage 2 Principal Review (Role 2.1 revisions).
- `implement`: Emits **Role 2.2 Orchestrator** prompt for `/dev-implementation` (Stage 3; names the persona and its resolved model and effort; dispatches Role 2.1 and Role 2.3 subagents).
- `cross-review`: Emits **Role 2.2 Orchestrator** prompt for Cross-Model Review (Gate 4 PASS; dispatches Role 2.1 `fix-planner` and Role 2.3 fixers/verifier).
- `finish`: Emits **Role 2.2 Orchestrator** prompt for `/finish` (Stage 4; dispatches Role 2.3 for rebase/`verify-tier` if needed).
- `assistant`: Emits **Role 2.1 AI Architect & Reviewer** prompt for general architectural discussions.
- `brief` (`--brief-role <task-implementer|task-reviewer|fix-planner|review-fixer|gate4-verifier>`): Emits the subagent brief with its persona (Role 2.1 for `task-reviewer` and `fix-planner`, Role 2.3 otherwise) and summary JSON contract.

### 5. Feature Completion & Compaction (`--complete`)

Executed in `/finish` (Stage 4 Pre-Finish Hook) when an entire epic is complete:

```bash
python3 scripts/resume_context.py --complete <epic_slug> "<milestone summary>"
```

- Appends a permanent milestone to `.devtool/PROJECT_LEDGER.md`:
  `- **[YYYY-MM-DD] \`<epic_slug>\`**: <milestone summary>`
- Moves `.devtool/state/<epic_slug>.md` and `.devtool/logs/activity_<epic_slug>.log` into `.devtool/archive/`.
- Re-renders `.devtool/assistant_state.md` and `.devtool/activity_stream.log` from remaining active epics.
- Synchronizes the IDE window title to reflect feature completion: `<ICON> [<REPO>] [@<account_id>] <Vietnamese Epic Name> - Completed & Archived`.

### 6. Record & Query Gate Approval Ledger (`--gate` / `--check-gate`)

Records or queries formal Gate approvals (Gate 1–5) in `.devtool/GATE_LEDGER.md` (permanent, tracked) and `.devtool/state/gate_ledger.jsonl` (ephemeral):

```bash
# Record Gate approval
python3 scripts/resume_context.py --gate <1..5> \
  --epic <epic_slug> \
  --approved "<approved scope summary>" \
  [--deviations "<approved deviations or None>"] \
  [--by "<author or AI persona>"]

# Query Gate approval
python3 scripts/resume_context.py --check-gate <1..5> --epic <epic_slug>
```

## Concurrency Protection

All writes acquire an exclusive POSIX advisory lock via `fcntl.flock` on `.devtool/.memory.lock`. This guarantees that concurrent AI agents running in parallel across multiple epics or repositories do not interleave or corrupt disk state.

## Related Skills

- [resume-context](../resume-context/SKILL.md): Restores context and enforces role discipline on startup.
- [dev-lifecycle](../dev-lifecycle/SKILL.md): Orchestrates the 4-stage development lifecycle.
- [finishing-a-development-branch](../finishing-a-development-branch/SKILL.md): Handles branch landing and epic completion.
