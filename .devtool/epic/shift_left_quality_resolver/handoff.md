# Handoff: shift_left_quality_resolver

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

- **Packaged**: 2026-11-28
- **Design commit**: `3ce7a46` — `HEAD` before the packaging commit, or `uncommitted` when `auto_commit` is false
- **Base branch**: `main`
- **PIC / Assigned Profile**: `tess` (e.g. `danhdue`, `buivantrong8901`, `huynhminhtien0510`)
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) is automated upon entry.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `shift_left_quality_resolver` | `shift_left_quality_resolver` |
| `shift_left_quality_resolver` | `shift_left_quality_resolver` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/shift_left_quality_resolver/shift_left_quality_resolver.md` — the HLD. Its Kanban Tasks Breakdown lists the 5 tasks.
2. `.devtool/epic/shift_left_quality_resolver/bdd_scenarios.md` — the behavioural contract.
3. `.devtool/epic/shift_left_quality_resolver/2026-11-28-shift-left-quality-resolver-design.md` — the approved source spec.
4. `.devtool/epic/shift_left_quality_resolver/principal_review.md`, when present — Principal Review rounds and decisions.

## Resume Prompt

```text
[PERSONA: Role 2.2 Orchestrator]
Use the d3nexus:dev-implementation skill for the `shift_left_quality_resolver` epic, following `skills/dev-lifecycle/references/orchestration-roles.md`.
Read .devtool/epic/shift_left_quality_resolver/handoff.md first. Write all internal orchestration, plans, code comments, and commits strictly in English.
You are the Role 2.2 Orchestrator (config key `orchestrator`; open this session on that model — see `python3 scripts/dev_config.py status`).
Run: python3 scripts/resume_context.py --role orchestrator --epic shift_left_quality_resolver
Apply the Execution Guardrails for Receiving LLM before presenting Gate 3 (Role 2.2 Orchestrator never reads/edits `src/` or `tests/` or runs test suites in the main session).
Gates 1 and 2 are passed; do not re-run brainstorming or design.
Gate 3 runs automatically: compute wave order via `python3 skills/dev-implementation/resources/scripts/compute_execution_order.py shift_left_quality_resolver --parallel`, monitor `python3 scripts/estimate_heartbeat.py`, own all `manage_worker_pool.py` calls (`sync --slot <1|2> --task <task_id> [--wave <k>] --status working|review`, `triage-fix`, `finalize-slot`, `merge`, `cleanup`; enforce the 2-pass task review cap and 1 fix pass via Two-Tier Risk Assessment), dispatch Role 2.3 Programmer subagents (`python3 scripts/dev_config.py dispatch --persona programmer --mode write ...`, or `workspace:"share"` where supported, with `--emit-prompt brief`) and Role 2.1 `task-reviewer`/`fix-planner` subagents (`--mode read-only`), run `python3 scripts/dev_config.py quota-check` before each wave, write `resume_context.py --checkpoint subagent_returned|wave_merged` as you go, verify gating/Gate 4 independently, and run Cross-Model Review before Stage 4 landing.
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

- **2026-11-28 (`3ce7a46`)**: Initial Stage 2 packaging

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- Gate 3 computes wave-parallel execution automatically via `compute_execution_order.py shift_left_quality_resolver --parallel`, estimates wave heartbeat via `estimate_heartbeat.py`, dispatches independent wave tasks across isolated slots (`manage_worker_pool.py init|sync|triage-fix|finalize-slot|merge|cleanup` / `workspace:"share"` subagents — pass `--task <task_id> [--wave <k>] --status working|review` on `sync` or use `sync_task_status.py task <task_id> in-progress|review` in single-worktree mode before dispatch/review, enforce the 2-pass task review cap and 1 fix pass, then finalize via `finalize-slot` or `done` + commit in slot before `merge`), and pauses via `resume_context.py --pending-decision` only on Choice A gates or `CRITICAL_CONFLICT`.
- Unless the design commit is `uncommitted`: if `git log 3ce7a46..main -- .devtool/epic/shift_left_quality_resolver` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
- This file is updated only by `package_epic.py --revise`, which records each re-anchoring under `## Revisions` and clears any pending revision decision for this epic.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.
- On a missing CLI, failed authentication or exhausted quota there is no automatic fallback and no retry: write `--checkpoint model_unavailable`, record a blocker with the fallback command, and stop. In low-quota mode finish the wave in flight, write `--checkpoint low_quota_stop`, print `--emit-prompt implement`, and stop.
