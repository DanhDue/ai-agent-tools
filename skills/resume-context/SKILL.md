---
name: resume-context
description: Restores project architectural awareness, active epic states, recent programmer activity, and Kanban task progress across multi-repository workspaces on session startup or account rotation while enforcing the four-persona governance model.
---

# Resume Context

## Overview

Restores comprehensive project architectural context across multi-repository workspaces (`ai-agent-tools`, `D3Nexus`, `lyrics-sync`, `nexus`) and multiple account profiles. Inspects permanent ledger milestones, active epic states, recent programmer activity, git working tree status, open contract RFCs, and active Kanban tasks before any response or code change.

**Core principle:** Understand the architecture and locked decisions first before acting.

**Announce at start:** "I'm using the resume-context skill to restore project architectural memory."

## When to Use

- At the start of a substantive development session or epic lifecycle workflow.
- After switching Antigravity account profiles or IDE windows for development.
- Before answering questions about system architecture, contract invariants, or open RFCs.
- When transitioning between advisory/review and implementation roles.

## When NOT to Use

- Fast-execution or maintenance commands like `/refresh-session`, `/setup_keybindings`, or checking git status.
- Ongoing turns within an active conversation where context has already been harvested.
- Quick one-off utility questions that do not touch system architecture or active epic state.

## Step 1: Execute Context Harvester

Run the harvester from the workspace terminal or execute the shell alias:

```bash
# Portable CLI across all repositories and linked worktrees (.worktrees/<epic_dir>)
d3nexus resume-context [--role architect|orchestrator|programmer] [--epic <slug>]

# Or using the shell alias (configured via --sync-zshrc)
resume

# Or invoking the Python engine directly from ai-agent-tools
python3 scripts/resume_context.py [--role architect|orchestrator|programmer] [--epic <slug>]
```

The CLI outputs 6 canonical sections:
0. `PROJECT ARCHITECTURAL LEDGER` (`.devtool/PROJECT_LEDGER.md`) — Permanent system invariants and completed milestones.
1. `ACTIVE EPIC STATE` (`.devtool/state/<epic_slug>.md` & `.devtool/assistant_state.md`) — High-level decisions and immediate next steps ($\le 20$ lines per epic).
2. `RECENT PROGRAMMER ACTIVITY` (`.devtool/logs/activity_<epic_slug>.log`) — Tail of recent file changes and tests.
3. `GIT WORKING TREE STATUS ACROSS REPOS` — Branch names, staged diffs, and worktree checkouts.
4. `OPEN CONTRACT GAPS & RFCS` (`shared-contracts/*/gaps_and_rfcs.md`) — Active cross-repo RFCs.
5. `ACTIVE TASKS` (`.devtool/features/task_*.md` & `done/`) — Progress ratios and in-flight Kanban tasks.

## Step 2: Four-Persona Governance

Every agent session operates under one of four personas (matrix: [orchestration-roles.md](../dev-lifecycle/references/orchestration-roles.md); models: `/d3nexus:dev-config`). `--role assistant` remains an alias of `--role architect` for existing state files. When a checkpoint exists, the harvest prints the latest one first; resume from its `next_step`.

### 2.1 Role 1.0 Human Architect (Developer)
- Controls architectural strategy, reviews deliverables, and approves Gates 1, 2 and 5, and every escalation.

### 2.2 Role 2.1 AI Architect & Reviewer (`--role architect`)
- Stages 1–2 main session: discussions, RCA, spec/HLD/BDD/task authoring (`d3nexus:dev-brainstorming`, `d3nexus:dev-designer`), Principal Review (`d3nexus:principal-review`) and packaging; in Stage 3 the `task-reviewer` and `fix-planner` subagents (`--mode read-only`).
- **Hard Restriction:** Never edits `src/` or `tests/`, runs test suites, linters or type checkers, dispatches subagents, or manages the worker pool.

### 2.3 Role 2.2 Orchestrator (`--role orchestrator`)
- Stage 3 main session (`d3nexus:dev-implementation`, `d3nexus:cross-model-review`, Stage 4 orchestration via `d3nexus:finishing-a-development-branch`), opened from `--emit-prompt implement` on the `orchestrator` model.
- **Hard Restriction:** Never reads or edits `src/` or `tests/`, edits HLD, BDD, Verification tables, DoD or `Allowed files`, or runs tests, linters, type checkers, `run_task_checks.py` or `verify-tier`. It owns the worker pool, dispatches Role 2.1 and Role 2.3 subagents, verifies their claims independently, writes checkpoints, and marks tasks `done`.

### 2.4 Role 2.3 Programmer (`--role programmer`)
- Dispatched as isolated subagents on the `programmer` binding (`dev_config.py dispatch`, briefs via `--emit-prompt brief --brief-role <task-implementer|task-reviewer|fix-planner|review-fixer|gate4-verifier>`) for `task-implementer`, `review-fixer` and `gate4-verifier`.
- Operates inside isolated git worktrees (`d3nexus:using-git-worktrees`), writing code and tests with strict TDD (Red-Green-Refactor) and Clean Code standards.
- **Hard Restriction:** Bound strictly to approved specifications, `Decisions Already Made`, and `Allowed files`. Never alters frozen architecture or `shared-contracts/` symlinks, and never calls `manage_worker_pool.py`.

## Step 3: Summarize Context Before Answering

After harvesting context, present a concise 5–10 bullet summary to the developer:
1. **Active Epics**: Current epic slugs and their lifecycle stages.
2. **Recent Decisions Locked**: Core constraints established in prior sessions.
3. **Working Tree & Worktrees**: Active branches and isolated checkouts.
4. **Task Completion Progress**: Total completed vs remaining Kanban tasks (`done/total`).
5. **Contract Invariants & RFCs**: Status of relevant `shared-contracts/` boundaries.
6. **Next Immediate Step**: Recommended action for this session.

## Step 4: Window Title & Workspace Bar Synchronization

Executing `resume_context.py` automatically synchronizes the IDE window title and workspace bar colors:
- Synthesizes `"<ICON> [<REPO_NAME>] [@<account_id>] <Vietnamese Epic Name> - <Stage / Task>"` into `.vscode/settings.json`.
- Enforces persistent top/bottom bar color parity (`inactiveBackground = activeBackground`), eliminating IDE dimming when windows lose focus.
- You can also invoke `--sync-title` standalone with `--stage "<custom_stage>"` to re-sync title states without harvesting.

## Related Skills

- [save-context](../save-context/SKILL.md): Persists state snapshots, activity logs, and handoff prompts.
- [dev-lifecycle](../dev-lifecycle/SKILL.md): Orchestrates the 4-stage development lifecycle.
- [using-git-worktrees](../using-git-worktrees/SKILL.md): Manages isolated git worktrees.
