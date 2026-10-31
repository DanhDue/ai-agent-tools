# Handoff: contract_diff_gate

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
- **Design commit**: `b18bc53` — `HEAD` before the packaging commit, or `uncommitted` when `auto_commit` is false
- **Base branch**: `main`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `<epic_dir>` | `contract_diff_gate` |
| `<epic_slug>` | `contract_diff_gate` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/contract_diff_gate/contract_diff_gate.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 3 tasks.
2. `.devtool/epic/contract_diff_gate/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/contract_diff_gate/2026-10-31-contract-diff-gate-design.en.md` — the approved source spec.
4. `.devtool/epic/contract_diff_gate/principal_review.md`, when present — Principal Review rounds and decisions.

## Resume Prompt

```text
[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]
Use the d3nexus:dev-implementation skill for the `contract_diff_gate` epic.
Read .devtool/epic/contract_diff_gate/handoff.md first.
Run: python3 scripts/resume_context.py --role programmer --epic contract_diff_gate
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

- **Repository boundary**: This epic modifies `ai-agent-tools` only. Downstream adoption in `D3Nexus`, `lyrics-sync`, and `nexus` (creating `.agents/contract_map.json`, auditing `brief`, running `ack`, and enabling `contract_diff`) will run in separate per-repository epics after plugin release `1.19.0`.
- **Explicit scope exclusion**: Do NOT modify `skills/principal-review/` or `skills/cross-model-review/`; upgrading external review CLI harness flags was explicitly separated out of this epic by the developer.
- **Principal Review Round 1 (`codex`)**: All 3 `Important` findings were verified and fixed in `4ed9835` (`git diff --no-ext-diff --no-renames --name-only -z M..HEAD` + `CDG-EC-05`, `union(M, HEAD)` baseline domain mapping with bootstrap + `CDG-ST-04`, and `Python 3.11+` minimum runtime in HLD `Verification Environment`).
- **Quality provider reference layout**: Only `rust-quality-check` and `python-quality-check` maintain `references/{rust,python}-capability-contract.md`; `flutter-quality-check`, `android-quality-check`, and `ios-quality-check` document `{skills_dir}`, `{base_ref}`, and exit code `2 -> BLOCKED` directly inside their `SKILL.md` files.
- **Supporting-file & lint hygiene**: `skills/setup-shared-contracts/SKILL.md` must explicitly mention `contract_map.json.tmpl` so `scripts/verify.sh` Check 8 passes, and Task 2 removes the 4 unused `# noqa: E402` comments in `test_validate_{android,flutter,ios,rust}_quality.py` so `ruff check` exits `0`.

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- Unless the design commit is `uncommitted`: if `git log b18bc53..main -- .devtool/epic/contract_diff_gate` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
- This file is a dated record. It is never updated after packaging.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.
