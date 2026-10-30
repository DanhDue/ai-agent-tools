# Handoff: context_memory_management

## Table of Contents

- [Status](#status)
- [Identifiers](#identifiers)
- [Read First](#read-first)
- [Resume Prompt](#resume-prompt)
- [Execution Guardrails for Receiving LLM](#execution-guardrails-for-receiving-llm)
- [Open Notes](#open-notes)
- [Rules for the Receiving Agent](#rules-for-the-receiving-agent)

## Status

- **Packaged**: 2026-10-30
- **Design commit**: `d30ecc8` — `HEAD` before the packaging commit, or `uncommitted` when `auto_commit` is false
- **Base branch**: `main`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `<epic_dir>` | `context_memory_management` |
| `<epic_slug>` | `context_memory_management` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/context_memory_management/context_memory_management.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 4 tasks.
2. `.devtool/epic/context_memory_management/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/context_memory_management/2026-10-30-context-memory-management-design.en.md` — the approved source spec.
4. `.devtool/epic/context_memory_management/principal_review.md`, when present — Principal Review rounds and decisions.

## Resume Prompt

```text
[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]
Use the d3nexus:dev-implementation skill for the `context_memory_management` epic.
Read .devtool/epic/context_memory_management/handoff.md first.
Apply the Execution Guardrails for Receiving LLM before presenting Gate 3.
Gates 1 and 2 are passed; do not re-run brainstorming or design.
Gate 3 is pending: present the execution order to me and wait for my confirmation.
```

## Execution Guardrails for Receiving LLM

Fast executor models and receiving agents MUST adhere to these four hard guardrails throughout implementation:

1. **Bounded context protocol**:
   - Step 1: Read only the active task file (`.devtool/features/task_*.md`).
   - Step 2: Read only the exact files declared in `Allowed files` and `Read-only context`.
   - Step 3: Look up exact symbol definitions identified under `## Decisions Already Made`.
   Undirected whole-repository searches (`grep`, `find`, `list_dir`) are forbidden unless an unresolved import explicitly requires symbol lookup.
2. **Strict spec fidelity**: Frozen constants, defaults, retry counts, fallback conditions, signatures, and call paths under `## Decisions Already Made` and the HLD are hard contracts. Any mismatch causes STOP and report rather than an executor-side simplification.
3. **Zero test fakery**: Tests import or invoke real production symbols and do not reconstruct retry loops, progress math, callback behavior, or configuration resolution.
4. **No contract repair by the executor**: The receiver never edits Verification tables, Allowed files, Definition of Done, Covers lines, protected paths, or frozen contract facts.

## Open Notes

- **Baseline Files**: Task 1 and Task 2 evolve `docs/architecture/resume_context.py` and `docs/architecture/save_resume_rules.md` into `scripts/resume_context.py` while keeping both files in `docs/architecture/` synchronized.
- **Multi-Epic Tier 2 Partitioning (Model A)**: Active per-epic states live under `.devtool/state/<epic_slug>.md` ($\le 20$ lines) and per-epic logs under `.devtool/logs/activity_<epic_slug>.log`, protected by `fcntl.flock` on `.devtool/.memory.lock`, with automatic rollup into `.devtool/assistant_state.md` and `.devtool/activity_stream.log`.
- **Tri-Role Governance**: Role 2.1 is Human Architect, Role 2.2 is AI Assistant (`--role assistant`, prohibited from modifying production code), and Role 2.3 is AI Programmer (`--role programmer`, accepting `implementer`/`worker` as backward-compatible aliases).
- **Shell `.zshrc` & Terminal History Sync**: `sync_shell_env` (`--sync-zshrc`) configures `REAL_HOME`, `WORKSPACE_ROOT`, `HISTFILE="$REAL_HOME/.zsh_history"`, `SHARE_HISTORY`, `INC_APPEND_HISTORY`, merges profile `.zsh_history` files before symlinking, adds `AllProjects`, `Projects`, and `.zsh_history` to `ag_run()` `sync_items`, and defines `alias resume` and `alias save-context`.
- **Lifecycle Word Limits**: When editing `skills/dev-lifecycle/SKILL.md` and `skills/dev-implementation/SKILL.md` in Task 4, keep word counts strictly $\le 2500$ and $\le 4500$ words respectively, with zero Mermaid or DOT diagram code fences.

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- Unless the design commit is `uncommitted`: if `git log d30ecc8..main -- .devtool/epic/context_memory_management` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
- This file is a dated record. It is never updated after packaging.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.
