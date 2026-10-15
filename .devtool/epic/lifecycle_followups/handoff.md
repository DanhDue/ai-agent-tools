# Handoff: lifecycle-followups

## Table of Contents

- [Status](#status)
- [Identifiers](#identifiers)
- [Read First](#read-first)
- [Resume Prompt](#resume-prompt)
- [Open Notes](#open-notes)
- [Rules for the Receiving Agent](#rules-for-the-receiving-agent)

## Status

- **Packaged**: 2026-10-15
- **Design commit**: `b727c56201edd044c3ed309721dd97e5dcd1935f` — `HEAD` before the packaging commit
- **Base branch**: `main`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `<epic_dir>` | `lifecycle_followups` |
| `<epic_slug>` | `lifecycle-followups` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/lifecycle_followups/lifecycle_followups.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 3 tasks.
2. `.devtool/epic/lifecycle_followups/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/lifecycle_followups/2026-10-15-lifecycle-followups-design.en.md` — the approved source spec.

## Resume Prompt

```text
Use the d3nexus:dev-implementation skill for the `lifecycle-followups` epic.
Read .devtool/epic/lifecycle_followups/handoff.md first.
Gates 1 and 2 are passed; do not re-run brainstorming or design.
Gate 3 is pending: present the execution order to me and wait for my confirmation.
```

## Open Notes

- **Read the skills from this repository, not the installed plugin.** This repository is the d3nexus
  kit itself. The installed plugin (1.7.1) predates the workflow this epic relies on: Entry-Point
  Detection, the Resume Procedure, BDD traceability and the Handoff Choice exist only in
  `skills/` on `main`. Follow `skills/dev-implementation/SKILL.md` and `skills/dev-lifecycle/SKILL.md`
  from the working tree, or reinstall the plugin from this repository first.
- **The base branch is `main`.** This repository has no `develop`. Wherever dev-implementation says
  `develop`, use `main`, including `integrate_branch.py --base main` and the worktree's base ref.
- **Gate 4 cannot pass by the letter here.** There is no `.agents/quality/check_quality.json`, so
  `@quality_check` returns `BLOCKED`. Earlier epics in this repository used `scripts/verify.sh` as the
  release gate with the developer's agreement. At Gate 4, run the full traceability check and
  `scripts/verify.sh`, report `@quality_check` as `BLOCKED`, and ask the developer.
- **This handoff predates fix H3, which it ships.** Its staleness rule below compares against `HEAD`;
  inside the epic worktree that flags every task commit. Run it against the base branch instead:
  `git log b727c56201edd044c3ed309721dd97e5dcd1935f..main -- .devtool/epic/lifecycle_followups`.
- **Every task carries exact, pre-verified changes.** They were applied to a copy of `main`
  before packaging: Task 1 fails first with `FAILED (failures=2, errors=2)` and then passes 32 tests;
  Task 3's tests fail with `FAILED (failures=4)` before Task 2 and pass all 4 after it; the epic's full
  traceability check reports `17/17 covered — PASS`; `scripts/verify.sh` passes. Transcribe them
  exactly; the outer `~~~~` fences in the task files only wrap the text.
- **Platform detection.** `detect_project_type.sh` reports `unknown` for this repository. Treat it as
  Python: standard-library scripts, `unittest`, no bootstrap beyond a clean checkout.
- **Known false positives.** `check_code_impact.py` reports "no test file found" for
  `check_bdd_traceability.py` and "exception handling" in Markdown files; neither is real.
- **Behaviour tests.** Task 2's checklist asks for before-and-after tests with fresh subagents. If your
  runtime cannot dispatch subagents, say so at Gate 3 and agree a substitute with the developer.

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- If `git log <sha>..HEAD -- .devtool/epic/<epic_dir>` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale.
- This file is a dated record. It is never updated after packaging.
