# Handoff: multi-epic-orchestration-and-governance

## Table of Contents

- [Status](#status)
- [Identifiers](#identifiers)
- [Read First](#read-first)
- [Resume Prompt](#resume-prompt)
- [Execution Guardrails for Receiving LLM](#execution-guardrails-for-receiving-llm)
- [Open Notes](#open-notes)
- [Rules for the Receiving Agent](#rules-for-the-receiving-agent)

## Status

- **Packaged**: 2026-11-06
- **Design commit**: `59e3146` — `HEAD` before the packaging commit, or `uncommitted` when `auto_commit` is false
- **Base branch**: `main`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `<epic_dir>` | `multi_epic_orchestration_and_governance` |
| `<epic_slug>` | `multi-epic-orchestration-and-governance` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/multi_epic_orchestration_and_governance/multi_epic_orchestration_and_governance.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 5 tasks.
2. `.devtool/epic/multi_epic_orchestration_and_governance/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/multi_epic_orchestration_and_governance/2026-11-06-multi-epic-orchestration-and-governance-design.en.md` — the approved source spec.
4. `.devtool/epic/multi_epic_orchestration_and_governance/principal_review.md`, when present — Principal Review rounds and decisions.

## Resume Prompt

```text
[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]
Use the d3nexus:dev-implementation skill for the `multi-epic-orchestration-and-governance` epic.
Read .devtool/epic/multi_epic_orchestration_and_governance/handoff.md first.
Run: python3 scripts/resume_context.py --role programmer --epic multi-epic-orchestration-and-governance
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

- **Three-Epic Optimization Roadmap**: This epic (`multi_epic_orchestration_and_governance`) is Epic 3 of 3 addressing open observations `#0013, #0014, #0015, #0020`. It is queued behind Epic 1 (`contract_and_authoring_ergonomics`) and Epic 2 (`execution_and_verification_infrastructure`), and declares both under `Depends on epic`. Do not start Stage 3 until both are merged into `main`.
- **Execution Order & Wave Structure**:
  - Wave 1 (Independent): `task_01_inter_epic_dependencies.md` and `task_04_gate_approval_ledger.md`.
  - Wave 2 (Depends on Task 01): `task_02_conflict_aware_epic_promotion.md` and `task_03_package_revise_and_spec_errata.md`.
  - Wave 3 (Depends on Tasks 01–04): `task_05_multi_epic_governance_e2e_acceptance.md`.
- **Principal Review**: One round (Claude Opus, `CHANGES REQUIRED`, 8 Important + 7 Minor); all 15 findings fixed in `9a9205f` and recorded in `principal_review.md`. No confirmation round was run.
- **Hard dependency on Epic 2**: Task 01 `replay_with_prerequisites()` imports `replay_epic_in_worktree` from `replay_task_text.py`, which Epic 2 creates; it returns a single error when the module is absent.
- **Tracked ledger**: Task 04 adds `!.devtool/GATE_LEDGER.md` to `.gitignore` so the gate ledger is a tracked record, while `.devtool/state/gate_ledger.jsonl` stays ephemeral.

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- Unless the design commit is `uncommitted`: if `git log 59e3146..main -- .devtool/epic/multi_epic_orchestration_and_governance` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
- This file is a dated record. It is never updated after packaging.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.
