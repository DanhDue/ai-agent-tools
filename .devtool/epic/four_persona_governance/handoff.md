# Handoff: four_persona_governance

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

- **Packaged**: 2026-11-17
- **Design commit**: `02d9e6d`
- **Base branch**: `main`
- **PIC / Assigned Profile**: `danhdue` (e.g. `danhdue`, `buivantrong8901`, `huynhminhtien0510`)
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) is automated upon entry.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `four_persona_governance` | `four_persona_governance` |
| `four_persona_governance` | `four_persona_governance` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/four_persona_governance/four_persona_governance.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 8 tasks.
2. `.devtool/epic/four_persona_governance/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/four_persona_governance/2026-11-17-four-persona-governance-design.en.md` — the approved source spec.
4. `.devtool/epic/four_persona_governance/principal_review.md`, when present — Principal Review rounds and decisions.

## Resume Prompt

```text
[PERSONA: AI ASSISTANT — ORCHESTRATOR]
Use the d3nexus:dev-implementation skill for the `four_persona_governance` epic, following `skills/dev-lifecycle/references/orchestration-roles.md`.
Read .devtool/epic/four_persona_governance/handoff.md first. Write all internal orchestration, plans, code comments, and commits strictly in English.
Run: python3 scripts/resume_context.py --role assistant --epic four_persona_governance
Apply the Execution Guardrails for Receiving LLM before presenting Gate 3 (Role 2.2 Orchestrator never reads/edits `src/` or `tests/` or runs test suites in the main session).
Gates 1 and 2 are passed; do not re-run brainstorming or design.
Gate 3 runs automatically: compute wave order via `python3 skills/dev-implementation/resources/scripts/compute_execution_order.py four_persona_governance --parallel`, monitor `python3 scripts/estimate_heartbeat.py`, own all `manage_worker_pool.py` calls (`sync --slot <1|2> --task <task_id> [--wave <k>] --status working|review`, `merge`, `cleanup`), dispatch Role 2.3 Programmer subagents (`agy` on configured programmer model, or `workspace:"share"` where supported, with `--emit-prompt brief`), verify gating/Gate 4 independently, and run Cross-Model Review before Stage 4 landing.
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

- **2026-11-17 (`66511cd`)**: Initial Stage 2 packaging
- **2026-11-17 (`66511cd` -> `1912c7e`)**: Add SE-07 provider quick-setup (dev-config --provider agy|claude|codex): scenarios FPG-HP-10 and FPG-EC-06, new Task 09, Task 08 now also blocked by Task 09
- **2026-11-17 (`1912c7e` -> `3802d7e`)**: SE-08: correct mypy argument order in Task 04 V5 and Task 06 V6 (flags after the last file); add --follow-imports=silent to Task 04 V5
- **2026-11-17 (`3802d7e` -> `02d9e6d`)**: SE-09: agy profile pool, global lease file and pooled dispatch (Task 10) with 5-hour and weekly quota windows and a Human exhaustion report; scenarios FPG-HP-11..13, EC-07, ST-07, AR-06, AR-07, FR-05..07; Tasks 03, 05, 06, 08 updated before they start

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- Gate 3 computes wave-parallel execution automatically via `compute_execution_order.py four_persona_governance --parallel`, estimates wave heartbeat via `estimate_heartbeat.py`, dispatches independent wave tasks across isolated slots (`manage_worker_pool.py init|sync|merge|cleanup` / `workspace:"share"` subagents — pass `--task <task_id> [--wave <k>] --status working|review` on `sync` or use `sync_task_status.py task <task_id> in-progress|review` in single-worktree mode before dispatch/review, then `done` + commit in slot before `merge`), and pauses via `resume_context.py --pending-decision` only on Choice A gates or `CRITICAL_CONFLICT`.
- Unless the design commit is `uncommitted`: if `git log 02d9e6d..main -- .devtool/epic/four_persona_governance` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
- This file is updated only by `package_epic.py --revise`, which records each re-anchoring under `## Revisions` and clears any pending revision decision for this epic.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.
