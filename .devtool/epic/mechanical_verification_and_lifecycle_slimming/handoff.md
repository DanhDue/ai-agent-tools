# Handoff: mechanical_verification_and_lifecycle_slimming

## Table of Contents

- [Status](#status)
- [Identifiers](#identifiers)
- [Read First](#read-first)
- [Resume Prompt](#resume-prompt)
- [Open Notes](#open-notes)
- [Rules for the Receiving Agent](#rules-for-the-receiving-agent)

## Status

- **Packaged**: 2026-10-19
- **Design commit**: `73b8e8988ed45531441592ee3b4d02147f1dde6a` — `HEAD` before the packaging commit
- **Base branch**: `main`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `<epic_dir>` | `mechanical_verification_and_lifecycle_slimming` |
| `<epic_slug>` | `mechanical_verification_and_lifecycle_slimming` |

These identifiers intentionally match. Use the exact underscore form because task frontmatter and
the execution-order scanner use it; do not derive a hyphenated alias.

## Read First

1. `.devtool/epic/mechanical_verification_and_lifecycle_slimming/mechanical_verification_and_lifecycle_slimming.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 5 tasks.
2. `.devtool/epic/mechanical_verification_and_lifecycle_slimming/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/mechanical_verification_and_lifecycle_slimming/2026-10-19-mechanical-verification-and-lifecycle-slimming-design.en.md` — the approved source spec.

## Resume Prompt

```text
Use the d3nexus:dev-implementation skill for the `mechanical_verification_and_lifecycle_slimming` epic.
Read .devtool/epic/mechanical_verification_and_lifecycle_slimming/handoff.md first.
Gates 1 and 2 are passed; do not re-run brainstorming or design.
Gate 3 is pending: present the execution order to me and wait for my confirmation.
```

## Open Notes

- **Use the skills from this repository checkout.** This repository is the agent kit itself; the
  installed plugin cache may not contain this newly designed behavior.
- **The base branch is `main`.** Use it for impact analysis, worktree creation, staleness checks,
  and eventual integration unless the developer explicitly changes the base.
- **Preflight order is fixed but Gate 3 is not passed.** The computed sequential order is Task 12,
  Task 14, Task 15, Task 13, then Task 16. Tasks 12, 14, and 15 occupy the same dependency layer,
  but `dev-implementation` still runs them sequentially.
- **The local environment currently has neither `ruff` nor `mypy` on PATH.** Every Python task
  deliberately requires both in TIER-B. Provision the tools or report `BLOCKED`; do not delete or
  weaken the verification rows.
- **The repository has no `.agents/quality/check_quality.json`.** The registered aggregate quality
  gate will be `BLOCKED` until a provider configuration exists. Report that honestly at Gate 4;
  `scripts/verify.sh` does not silently replace the required provider verdict.
- **Test integrity has a deliberate boundary.** Reconstructed production logic and substituted
  real-artifact anchors are Gate 4 failures, but this epic does not add a universal cross-language
  mechanical provider capability. Do not claim such coverage.
- **Pytest RED is fail closed.** A collection-time import failure with zero collected tests is not
  accepted. Exercise the import inside a collected test so the RED represents behavior.

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- If `git log 73b8e8988ed45531441592ee3b4d02147f1dde6a..main -- .devtool/epic/mechanical_verification_and_lifecycle_slimming` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale.
- This file is a dated record. It is never updated after packaging.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.
