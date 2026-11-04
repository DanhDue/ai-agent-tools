# Handoff: web_quality_check_and_integration_gate

## Table of Contents

- [Status](#status)
- [Identifiers](#identifiers)
- [Read First](#read-first)
- [Resume Prompt](#resume-prompt)
- [Execution Guardrails for Receiving LLM](#execution-guardrails-for-receiving-llm)
- [Open Notes](#open-notes)
- [Rules for the Receiving Agent](#rules-for-the-receiving-agent)

## Status

- **Packaged**: 2026-11-05
- **Design commit**: `2dea1f5`
- **Base branch**: `main`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `<epic_dir>` | `web_quality_check_and_integration_gate` |
| `<epic_slug>` | `web-quality-check-and-integration-gate` |

These are two distinct strings (underscores for directory, hyphens for slug). Never derive one from the other.

## Read First

1. `.devtool/epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 6 tasks.
2. `.devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.en.md` — the behavioural contract covering all 12 scenarios.
3. `.devtool/epic/web_quality_check_and_integration_gate/2026-11-04-web-quality-check-and-integration-gate-design.en.md` — the approved source spec.

## Resume Prompt

```text
[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]
Use the d3nexus:dev-implementation skill for the `web-quality-check-and-integration-gate` epic.
Read .devtool/epic/web_quality_check_and_integration_gate/handoff.md first.
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
3. **Zero test fakery & Anti-Rationalization**: Tests must exercise real production symbols. In Tier C tests, mocking domain use cases or repositories is strictly forbidden. Web Tier C tests must run in headless Playwright with Zero-Console-Error assertion.
4. **No contract repair by the executor**: The receiver never edits Verification tables, Allowed files, Definition of Done, Covers lines, protected paths, or frozen contract facts.

## Open Notes

- **Polyglot Ecosystem Scope**: This epic implements the `web-quality-check` provider in `ai-agent-tools`, which unblocks full Gate 4 multi-provider verification across `D3Nexus` (`rust-core` + `learning-web`) and `lyrics-sync` (`python-core` + `preview-ui`), as well as formalizing Subcutaneous Testing guidelines for `nexus` (`flutter-core`).
- **Anti-Rationalization Integration**: Inspired by `addyosmani/agent-skills`, Anti-Rationalization tables and Doubt-Driven Verification rules are codified into `dev-designer`, `dev-implementation`, and `test-driven-development`.
- **Zero-Console-Error Watchdog**: Playwright fixtures intercept all `console.error` and `pageerror` events, halting tests on unhandled runtime exceptions while supporting an allowlist regex for benign third-party library deprecation warnings.
- **In-Place Vanilla JS Type-Checking**: Static JavaScript files in `lyrics-sync` are type-checked via `jsconfig.json` with JSDoc `// @ts-check` without requiring `.ts` file renaming.
- **Automated Smoke Walkthrough**: Task 06 provides `generate_smoke_checklist.py`, hooked into `dev-implementation` Phase 4, generating `.devtool/epic/<epic_dir>/manual_smoke_checklist.md` (3-5 steps, 2-minute sanity check) upon Gate 4 pass.

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- Unless the design commit is `uncommitted`: if `git log dfad265..main -- .devtool/epic/web_quality_check_and_integration_gate` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
- This file is a dated record. It is never updated after packaging.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.
