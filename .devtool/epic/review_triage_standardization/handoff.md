# Handoff: review_triage_standardization

## Table of Contents

- [Status](#status)
- [Identifiers](#identifiers)
- [Read First](#read-first)
- [Resume Prompt](#resume-prompt)
- [Execution Guardrails for Receiving LLM](#execution-guardrails-for-receiving-llm)
- [Open Notes](#open-notes)
- [Rules for the Receiving Agent](#rules-for-the-receiving-agent)

## Status

- **Packaged**: 2026-10-31
- **Design commit**: `744f187` — `HEAD` before packaging commit
- **Base branch**: `main`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation` / Cross-Model Review.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `<epic_dir>` | `review_triage_standardization` |
| `<epic_slug>` | `review_triage_standardization` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/review_triage_standardization/review_triage_standardization.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 3 tasks.
2. `.devtool/epic/review_triage_standardization/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/review_triage_standardization/2026-10-31-review-triage-header-and-provider-defaults-design.en.md` — the approved source spec.

## Resume Prompt

```text
[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]
Use the d3nexus:dev-implementation skill for the `review_triage_standardization` epic.
Read .devtool/epic/review_triage_standardization/handoff.md first.
Run: python3 scripts/resume_context.py --role programmer --epic review_triage_standardization
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

- **4-Bullet Header Standard**: Every review mode (`triage`, `run`, `run_adhoc_code`, conversational AI summaries) outputs:
  - `• Candidate SHA: <commit_sha>`
  - `• Reviewer: <CLI> ( <model> )`
  - `• Thinking Level: <Light | Low | Medium | High | Extra High | None>`
  - `• Verdict: <VERDICT> (<count> findings)`
- **Dynamic Probing Mandate**: `external-review-prompt.md` and `principal-review-prompt.md` instruct reviewers to execute active REPL commands (`python3 -c ...`) for exception fallback paths, regex, morphology, and ORM persistence.
- **Claude CLI Security**: Claude runs with `--dangerously-skip-permissions` to allow terminal probe execution, with zero-mutation guarantee enforced by `tree_changes(root, before, sha)`.
- **Sticky Defaults**: `.devtool/review_config.json` stores per-provider model and thinking level preferences, seeded with canonical defaults.

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- Unless the design commit is `uncommitted`: if `git log 744f187..main -- .devtool/epic/review_triage_standardization` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
- This file is a dated record. It is never updated after packaging.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.
