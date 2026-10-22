# Handoff: principal_review

## Table of Contents

- [Status](#status)
- [Identifiers](#identifiers)
- [Read First](#read-first)
- [Resume Prompt](#resume-prompt)
- [Execution Guardrails for Receiving LLM](#execution-guardrails-for-receiving-llm)
- [Open Notes](#open-notes)
- [Rules for the Receiving Agent](#rules-for-the-receiving-agent)

## Status

- **Packaged**: 2026-10-22
- **Design commit**: `34802af` — `HEAD` before the packaging commit
- **Base branch**: `main`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `<epic_dir>` | `principal_review` |
| `<epic_slug>` | `principal_review` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/principal_review/principal_review.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 5 tasks.
2. `.devtool/epic/principal_review/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md` — the approved source spec.

## Resume Prompt

```text
Use the d3nexus:dev-implementation skill for the `principal_review` epic.
Read .devtool/epic/principal_review/handoff.md first.
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

- **Decisions taken with the developer (2026-10-22)**:
  1. Principal Review is an **optional** choice offered after every Package, worded like Review Choice: `1. Done` or `2. Principal Review`. The developer picks Claude CLI or Codex CLI; the agent never picks. It is not a mandatory gate.
  2. Approach A: extend `run_external_review.py` with `--kind principal` rather than a separate engine. Parallel dual-model review and reviewer-written patches are out of scope.
  3. The `sync_task_status.py epic` scope fix (Task 4) is in scope. It caused real uncommitted edits in another epic's worktree in `lyrics-sync` on 2026-10-22, and the Principal Review loop re-packages on every round.
  4. The HLD's clarifications C1–C5 formalize gaps in the spec and change no decision. C3 exists because `test_lf_st_02` pins the handoff staleness command, which must stay byte-identical.
- **Origin**: a manual pre-implementation review of `lyrics-sync`'s `flashcard_compact_data_enrichment` found the defect classes listed in the spec's Background. Its packaged commit `5cc7d720` is a good Gate 5 trial target for `check_epic_readiness.py`, in a scratch worktree, never in the live checkout.
- **Baseline at `34802af`**:
  - `scripts/verify.sh` prints `PASS — safe to publish`.
  - The guard suites pass: `test_run_external_review.py`, `test_local_review.py`, `test_sync_task_status.py`, `test_lifecycle_document_contract.py`, `test_lifecycle_signals.py`, `test_verifiable_handoff_text.py` and `test_verifiable_handoff.py`.
  - Existing lint and type debt kept out of Tier B rows: `test_run_external_review.py` (14 ruff, 1 mypy) and `test_sync_task_status.py` (66 strict mypy).
  - Task 4 clears the 8 ruff and 3 mypy findings in `sync_task_status.py`.
- **Tooling**:
  - On the design machine, `ruff` 0.16.9 and `mypy` 2.3.1 resolved from another project's virtualenv. Before Gate 3, confirm both are on `PATH` in the implementation shell, or every TIER-B row will fail for a reason other than its Expect.
  - Finding counts can differ with other versions; a Tier B row that fails at baseline on a file the task did not create is a Stop-and-Report.
- **Word budget**: `skills/dev-lifecycle/SKILL.md` is 2454 of 2500 words. Task 5 frees words by replacing the four preflight commands with one.
- **Known limit of R5**: it checks only `- \`<path>\`: <symbols>` sub-bullets. Older epics that write `Target files and symbols` inline (`module.symbol`) are skipped, not failed. That is acceptable for this release.
- **Self-reference**: this epic was packaged with the four-command preflight, because `check_epic_readiness.py` does not exist yet.
- **Base branch**: this repository merges epics into `main` and has no `develop`. Where `dev-implementation` mentions fast-forwarding `develop`, read `main`.

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- Unless the design commit is `uncommitted`: if `git log 34802af..main -- .devtool/epic/principal_review` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
- This file is a dated record. It is never updated after packaging.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.
