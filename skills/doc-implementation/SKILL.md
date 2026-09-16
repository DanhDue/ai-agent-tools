---
name: doc-implementation
description: Use when a document already has an approved brief, outline and section task files and you need to actually write it — one worktree, one section at a time, one commit per section. It enforces Gate 2 by handing the draft to quality_check with Kind document, and holds Gate 3 for the user's sign-off. Activate it at Stage 2 of the document lifecycle, after doc-designer's breakdown has been confirmed.
---

# Document Implementation

Stage 2 of `doc-lifecycle`. Drafts an approved outline section by section.

**Core principle:** one worktree, one section at a time, one commit per section, the outline stays
truthful.

**Announce at start:** "I'm using the doc-implementation skill to draft the `<doc_slug>` document."

## Two Placeholders, Not One

Exactly as in `dev-implementation`, and for the same reason — read both off disk, never derive one
from the other:

| Placeholder | What it is | Worked example |
|---|---|---|
| `<doc_dir>` | The directory name on disk | `onboarding_guide` (underscores) |
| `<doc_slug>` | The `epic:` value in task frontmatter | `onboarding-guide` (hyphens) |

## When to Use

- `doc-lifecycle` routes here at Stage 2, after Gate 1.
- `.devtool/epic/<doc_dir>/<doc_dir>.en.md` exists with `Kind: document`, and one or more
  `.devtool/features/task_*.md` carry that document's `epic:` value.

**Don't use when** the outline does not exist yet (run `doc-designer` first), or the work is one
section a reviewer would not gate (edit it directly).

## Shared machinery, not a fork

This skill **reuses `dev-implementation`'s Kanban scripts unchanged**:

- `skills/dev-implementation/resources/scripts/sync_task_status.py`
- `skills/dev-implementation/resources/scripts/compute_execution_order.py`

Status, ordering and archival behave identically for both kinds of work, so `.devtool/features/`
stays one board rather than two. Forking these scripts would double the maintenance surface for no
behavioural gain. If a script needs changing, change it once, in `dev-implementation`.

## Process

### Phase 0 — Context reload (once, not per section)

Read in full: the canonical `<doc_dir>.en.md` (never the `.vi.md` for decisions — it is a synced
translation), every `task_*.md` whose `epic:` matches `<doc_slug>`, and any source spec the Meta
Data links to. Note the declared **audience**, **Diátaxis mode** and **Acceptance** criterion; all
three are checked at Gate 2.

### Phase 1 — Order and worktree

Sections are drafted in **outline order** unless a task file's prose says otherwise. There is no
dependency calculation to run: prose sections do not block one another the way code does, and
`compute_execution_order.py` is only needed when task files declare blockers.

Create one worktree for the whole document, with an explicit base ref:

```bash
git worktree add .worktrees/<doc_dir> -b doc/<doc_slug> <base_ref>
```

There is no build to bootstrap.

### Phase 2 — Section-by-section drafting

For each section, in order:

1. Set the task in progress across every checkout:
   ```bash
   python3 skills/dev-implementation/resources/scripts/sync_task_status.py task <task_id> in-progress
   ```
2. Draft the section, staying inside the document's declared Diátaxis mode. Material belonging to
   another mode is **relocated and linked**, never inlined and never deleted.
3. **Re-read the section against its own purpose line in the outline.** This replaces the failing
   test, and it is the whole of this skill's verification discipline — see below.
4. Mark it done, then make exactly one commit staging the section and its task file:
   ```bash
   python3 skills/dev-implementation/resources/scripts/sync_task_status.py task <task_id> done
   git add -A && git commit -m "[DOC_NAME] <section title>"
   ```

**No test suite runs here.** Not unit tests, not integration tests, not a native build. There is
nothing to run, and running the development gates on prose would produce a green light that means
nothing. Gate 2 is `quality_check` with `Kind: document`, at Phase 4.

#### What replaces TDD

A test gives a unit a pre-written expectation it can fail against. For a section, that expectation
already exists: **the one-line purpose `doc-designer` wrote for it in the outline.**

After drafting, read the section against that line. There are exactly two outcomes:

- The section does not match its purpose → **fix the section.**
- The purpose was wrong → **change the outline, deliberately**, and say so.

There is no third outcome. "Close enough" is not one, and neither is leaving the outline stale
because the draft is better than the plan.

### Phase 3 — Outline sync on divergence

When Phase 2 changed the outline, sync **both** `<doc_dir>.en.md` and `<doc_dir>.vi.md` before the
next section starts, and commit that separately:

```bash
git commit -m "[DOC_NAME] Sync outline after <section title>"
```

Keeping it out of the section's own commit is what keeps `git log` readable as one-commit-per-section.

### Phase 4 — Gate 2 verification

Once every section is done, run `quality_check`. The document's `Kind: document` selects the
document path: mechanical checks, Diátaxis conformance, the content audit, and the refusal rule
that aborts if the diff touches a file shipping in the build.

On any failure, fix and re-run **in full**. A 🟢 assembled from a partial re-run is not a 🟢.

### Phase 4.1 — Gate 3 sign-off (🛑 mandatory stop)

With Gate 2 green, **stop calling tools.** Leave every completed task in `.devtool/features/done/`
so the board is inspectable, present the draft and the `quality_check` verdict, and wait:

> "The `<doc_slug>` document is drafted and `quality_check` is 🟢. All sections are visible in the
> DONE column. Please review the document. Reply to proceed with branch finishing and archival."

Only an explicit approval advances. A change request routes back to Phase 2.

### Phase 5 — Finish the branch

After Gate 3, invoke `finishing-a-development-branch`. Its pre-finish hook archives the completed
tasks into `.devtool/epic/<doc_dir>/`.

**Then place the finished document where it belongs** — `docs/`, a README, a skill's `references/`.
A deliverable left in `.devtool/` has not shipped.

## Red Flags

- Running unit, integration or native build commands on a document.
- Skipping `quality_check` because "it is only prose".
- More than one commit per section, or folding an outline sync into a section's commit.
- Drafting material that belongs to another Diátaxis mode instead of relocating and linking it.
- Leaving a section that does not match its outline purpose, without changing either one.
- Forking the Kanban scripts instead of reusing `dev-implementation`'s.
- Advancing past Phase 4.1 without the user's explicit sign-off.
- Leaving the finished document inside `.devtool/`.
