# Handoff: split_review_skills

## Table of Contents

- [Status](#status)
- [Identifiers](#identifiers)
- [Read First](#read-first)
- [Resume Prompt](#resume-prompt)
- [Execution Guardrails for Receiving LLM](#execution-guardrails-for-receiving-llm)
- [Open Notes](#open-notes)
- [Rules for the Receiving Agent](#rules-for-the-receiving-agent)

## Status

- **Packaged**: 2026-10-23
- **Design commit**: `30aa0e7b742f89f84e7436c02e0edc6a7ae8e0eb`
- **Base branch**: `main`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `<epic_dir>` | `split_review_skills` |
| `<epic_slug>` | `split_review_skills` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/split_review_skills/split_review_skills.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 4 tasks.
2. `.devtool/epic/split_review_skills/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/split_review_skills/2026-10-23-split-review-skills-design.en.md` — the approved source spec.
4. `.devtool/epic/split_review_skills/principal_review.md`, when present — Principal Review rounds and decisions.

## Resume Prompt

```text
Use the d3nexus:dev-implementation skill for the `split_review_skills` epic.
Read .devtool/epic/split_review_skills/handoff.md first.
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

- Theoretical basis for separating review skills is documented in `2026-10-23-split-review-skills-design.en.md` and `.vi.md` (Shift-Left vs Shift-Right Boehm curve, context separation, and Single Responsibility Principle).
- Both skills (`principal-review` and `cross-model-review`) support dual-mode execution: in-lifecycle and ad-hoc.
- The underlying execution script `run_external_review.py` remains in `skills/dev-implementation/resources/scripts/` to preserve backward compatibility.

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- Unless the design commit is `uncommitted`: if `git log 30aa0e7b742f89f84e7436c02e0edc6a7ae8e0eb..main -- .devtool/epic/split_review_skills` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
- This file is a dated record. It is never updated after packaging.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.
