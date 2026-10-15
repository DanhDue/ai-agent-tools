# Handoff: <epic_slug>

## Table of Contents

- [Status](#status)
- [Identifiers](#identifiers)
- [Read First](#read-first)
- [Resume Prompt](#resume-prompt)
- [Open Notes](#open-notes)
- [Rules for the Receiving Agent](#rules-for-the-receiving-agent)

## Status

- **Packaged**: <YYYY-MM-DD>
- **Design commit**: `<sha>` — `HEAD` before the packaging commit
- **Base branch**: `<base_branch>`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `<epic_dir>` | `<epic_dir value>` |
| `<epic_slug>` | `<epic_slug value>` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/<epic_dir>/<epic_dir>.en.md` — the HLD. Its Kanban Tasks Breakdown lists the <N> tasks.
2. `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/<epic_dir>/<source spec>.en.md` — the approved source spec.

## Resume Prompt

```text
Use the d3nexus:dev-implementation skill for the `<epic_slug>` epic.
Read .devtool/epic/<epic_dir>/handoff.md first.
Gates 1 and 2 are passed; do not re-run brainstorming or design.
Gate 3 is pending: present the execution order to me and wait for my confirmation.
```

## Open Notes

<What the design session knows that the documents do not say — decisions taken in conversation, risks, doubts. Write `None` when there is nothing.>

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- If `git log <sha>..HEAD -- .devtool/epic/<epic_dir>` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale.
- This file is a dated record. It is never updated after packaging.
