# Handoff: contract-and-authoring-ergonomics

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
- **Design commit**: `766f78e` — `HEAD` before the packaging commit, or `uncommitted` when `auto_commit` is false
- **Base branch**: `main`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `<epic_dir>` | `contract_and_authoring_ergonomics` |
| `<epic_slug>` | `contract-and-authoring-ergonomics` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 5 tasks.
2. `.devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/contract_and_authoring_ergonomics/2026-11-06-contract-and-authoring-ergonomics-design.en.md` — the approved source spec.
4. `.devtool/epic/contract_and_authoring_ergonomics/principal_review.md`, when present — Principal Review rounds and decisions.

## Resume Prompt

```text
[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]
Use the d3nexus:dev-implementation skill for the `contract-and-authoring-ergonomics` epic.
Read .devtool/epic/contract_and_authoring_ergonomics/handoff.md first.
Run: python3 scripts/resume_context.py --role programmer --epic contract-and-authoring-ergonomics
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

- **Three-Epic Optimization Roadmap**: This epic (`contract_and_authoring_ergonomics`) is Epic 1 of 3 addressing the 15 open observations in `skill-observations/observation-log/` (`#0008, #0009, #0012, #0016, #0019`). Epic 2 (`execution_and_verification_infrastructure` for `#0006, #0007, #0010, #0011, #0017, #0018`) and Epic 3 (`multi_epic_orchestration_and_governance` for `#0013, #0014, #0015, #0020`) follow sequentially.
- **Zero-Setup `D3NEXUS_KIT` & `bin/d3nexus`**: `run_task_checks.py` and `check_epic_readiness.py` compute `KIT_ROOT = Path(__file__).resolve().parents[4]` dynamically at runtime and inject `D3NEXUS_KIT` and `PATH="<kit_root>/bin:$PATH"` into child subprocesses, requiring zero manual setup across machines or profiles.
- **Mypy Import Narrowing**: Tasks 01–04 use `--follow-imports=silent` on `mypy` rows because `check_bdd_traceability.py` has an unnarrowed `Optional[str]` on `fence` in `scenario_ids()`; Task 05 narrows `fence` in `check_bdd_traceability.py` so `mypy` passes cleanly without `--follow-imports=silent`.
- **Observation #0021**: Logged during Stage 2 when an epic directory starting with `task_` collided with `task_*.md` globs; Task 02 (`render_epic_tasks`) should match task files with `re.fullmatch(r"task_[0-9]+_.*\.md", path.name)` (or exclude `*.en.md`/`*.vi.md`).

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- Unless the design commit is `uncommitted`: if `git log 766f78e..main -- .devtool/epic/contract_and_authoring_ergonomics` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
- This file is a dated record. It is never updated after packaging.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.
