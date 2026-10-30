---
name: resume-context
description: Restores project architectural awareness, active epic states, recent programmer activity, and Kanban task progress across multi-repository workspaces on session startup or account rotation while enforcing the Tri-Role Governance Model.
---

# Resume Context

## Overview

Restores comprehensive project architectural context across multi-repository workspaces (`ai-agent-tools`, `D3Nexus`, `lyrics-sync`, `nexus`) and multiple account profiles. Inspects permanent ledger milestones, active epic states, recent programmer activity, git working tree status, open contract RFCs, and active Kanban tasks before any response or code change.

**Core principle:** Understand the architecture and locked decisions first before acting.

**Announce at start:** "I'm using the resume-context skill to restore project architectural memory."

## When to Use

- At the start of every new conversation or work session.
- After switching Antigravity account profiles or IDE windows.
- Before answering questions about system architecture, contract invariants, or open RFCs.
- When transitioning between advisory/review and implementation roles.

## Step 1: Execute Context Harvester

Run the harvester from the workspace terminal or execute the shell alias:

```bash
# Using the shell alias (configured via --sync-zshrc)
resume

# Or invoking the Python engine directly
python3 scripts/resume_context.py [--role assistant|programmer] [--epic <slug>]
```

The CLI outputs 6 canonical sections:
0. `PROJECT ARCHITECTURAL LEDGER` (`.devtool/PROJECT_LEDGER.md`) — Permanent system invariants and completed milestones.
1. `ACTIVE EPIC STATE` (`.devtool/state/<epic_slug>.md` & `.devtool/assistant_state.md`) — High-level decisions and immediate next steps ($\le 20$ lines per epic).
2. `RECENT PROGRAMMER ACTIVITY` (`.devtool/logs/activity_<epic_slug>.log`) — Tail of recent file changes and tests.
3. `GIT WORKING TREE STATUS ACROSS REPOS` — Branch names, staged diffs, and worktree checkouts.
4. `OPEN CONTRACT GAPS & RFCS` (`shared-contracts/*/gaps_and_rfcs.md`) — Active cross-repo RFCs.
5. `ACTIVE TASKS` (`.devtool/features/task_*.md` & `done/`) — Progress ratios and in-flight Kanban tasks.

## Step 2: Tri-Role Persona Governance

Every agent session operates under one of three governance roles:

### 2.1 Human Architect (Developer)
- Controls architectural strategy, reviews deliverables, and approves Gates 1–5.

### 2.2 AI Assistant (`--role assistant`)
- Default persona for general discussions, root cause analysis (RCA), HLD/task authoring (`d3nexus:dev-brainstorming`, `d3nexus:dev-designer`), Principal Review (`d3nexus:principal-review`), and Cross-Model Review (`d3nexus:cross-model-review`).
- **Hard Restriction:** Strictly prohibited from writing or modifying production source code or application test suites. Only design documentation (`docs/`, `.devtool/`, `shared-contracts/`) may be edited.

### 2.3 AI Programmer (`--role programmer`)
- Activated by implementation prompts or `/dev-implementation` (`d3nexus:dev-implementation`).
- Operates inside isolated git worktrees (`d3nexus:using-git-worktrees`), writing code and tests with strict TDD (Red-Green-Refactor) and Clean Code standards.
- **Hard Restriction:** Bound strictly to approved specifications, `Decisions Already Made`, and `Allowed files`. Never alters frozen architecture or `shared-contracts/` symlinks.

## Step 3: Summarize Context Before Answering

After harvesting context, present a concise 5–10 bullet summary to the developer:
1. **Active Epics**: Current epic slugs and their lifecycle stages.
2. **Recent Decisions Locked**: Core constraints established in prior sessions.
3. **Working Tree & Worktrees**: Active branches and isolated checkouts.
4. **Task Completion Progress**: Total completed vs remaining Kanban tasks (`done/total`).
5. **Contract Invariants & RFCs**: Status of relevant `shared-contracts/` boundaries.
6. **Next Immediate Step**: Recommended action for this session.

## Related Skills

- [save-context](../save-context/SKILL.md): Persists state snapshots, activity logs, and handoff prompts.
- [dev-lifecycle](../dev-lifecycle/SKILL.md): Orchestrates the 4-stage development lifecycle.
- [using-git-worktrees](../using-git-worktrees/SKILL.md): Manages isolated git worktrees.
