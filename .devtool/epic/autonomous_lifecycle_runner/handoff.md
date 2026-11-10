# Handoff: autonomous_lifecycle_runner

## Table of Contents

- [Status](#status)
- [Identifiers](#identifiers)
- [Read First](#read-first)
- [Resume Prompt](#resume-prompt)
- [Execution Guardrails for Receiving LLM](#execution-guardrails-for-receiving-llm)
- [Open Notes](#open-notes)
- [Revisions](#revisions)
- [Rules for the Receiving Agent](#rules-for-the-receiving-agent)

## Status

- **Packaged**: 2026-11-10
- **Design commit**: `6ad5af4` — `HEAD` before the packaging commit, or `uncommitted` when `auto_commit` is false
- **Base branch**: `main`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `autonomous_lifecycle_runner` | `autonomous_lifecycle_runner` |
| `autonomous_lifecycle_runner` | `autonomous_lifecycle_runner` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md` — the HLD. Its Kanban Tasks Breakdown lists the <N> tasks.
2. `.devtool/epic/autonomous_lifecycle_runner/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/autonomous_lifecycle_runner/<source spec>.en.md` — the approved source spec.
4. `.devtool/epic/autonomous_lifecycle_runner/principal_review.md`, when present — Principal Review rounds and decisions.

## Resume Prompt

```text
[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]
Use the d3nexus:dev-implementation skill for the `autonomous_lifecycle_runner` epic.
Read .devtool/epic/autonomous_lifecycle_runner/handoff.md first.
Run: python3 scripts/resume_context.py --role programmer --epic autonomous_lifecycle_runner
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

None

## Revisions

- **2026-11-10 (`6ad5af4`)**: Initial Stage 2 packaging

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- Unless the design commit is `uncommitted`: if `git log 6ad5af4..main -- .devtool/epic/autonomous_lifecycle_runner` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
- This file is updated only by `package_epic.py --revise`, which records each re-anchoring under `## Revisions`.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.
