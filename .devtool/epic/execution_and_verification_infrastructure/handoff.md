# Handoff: execution-and-verification-infrastructure

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
- **Design commit**: `dc256e8` — `HEAD` before the packaging commit, or `uncommitted` when `auto_commit` is false
- **Base branch**: `main`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `<epic_dir>` | `execution_and_verification_infrastructure` |
| `<epic_slug>` | `execution-and-verification-infrastructure` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/execution_and_verification_infrastructure/execution_and_verification_infrastructure.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 5 tasks.
2. `.devtool/epic/execution_and_verification_infrastructure/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/execution_and_verification_infrastructure/2026-11-06-execution-and-verification-infrastructure-design.en.md` — the approved source spec.
4. `.devtool/epic/execution_and_verification_infrastructure/principal_review.md`, when present — Principal Review rounds and decisions.

## Resume Prompt

```text
[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]
Use the d3nexus:dev-implementation skill for the `execution-and-verification-infrastructure` epic.
Read .devtool/epic/execution_and_verification_infrastructure/handoff.md first.
Run: python3 scripts/resume_context.py --role programmer --epic execution-and-verification-infrastructure
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

- **Three-Epic Optimization Roadmap**: This epic (`execution_and_verification_infrastructure`) is Epic 2 of 3 addressing open observations `#0006, #0007, #0010, #0011, #0017, #0018`. It is queued behind Epic 1 (`contract_and_authoring_ergonomics`) and precedes Epic 3 (`multi_epic_orchestration_and_governance`).
- **Execution Order & Wave Structure**:
  - Wave 1 (Independent): `task_01_polyglot_worktree_bootstrap.md`, `task_02_failure_baseline_and_comparison.md`, and `task_03_live_integration_and_route_matching.md`.
  - Wave 2 (Depends on Task 01 & Task 03): `task_04_task_replay_and_measure_phase.md`.
  - Wave 3 (Depends on Tasks 01–04): `task_05_execution_infra_e2e_acceptance.md`.
- **Contract Alignment with Epic 1**: `task_04` reuses `parse_evidence_files(task_text: str) -> list[AllowedPath]` (`entry.pattern`) and the `.devtool/epic/<epic_dir>/evidence/<filename>` path prefix established by Epic 1.

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- Unless the design commit is `uncommitted`: if `git log dc256e8..main -- .devtool/epic/execution_and_verification_infrastructure` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
- This file is a dated record. It is never updated after packaging.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.
