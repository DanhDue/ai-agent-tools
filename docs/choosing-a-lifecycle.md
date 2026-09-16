# Choosing a lifecycle

You have a piece of work and three lifecycles to choose from. This page gets you to the right one.

## Start here

Answer one question: **what will exist when you are finished?**

| What you will have produced | Go to |
|---|---|
| Changed code that ships in the build | [If you are writing code](#if-you-are-writing-code) |
| A document someone will read | [If you are writing a document](#if-you-are-writing-a-document) |
| A decision about what to build at all | [If you do not know what to build yet](#if-you-do-not-know-what-to-build-yet) |

If two of those look true at once, pick by the **build**: if any file that ships is changing, it is
code work, however much prose you also write. `d3nexus:doc_quality_check` enforces this and will refuse the
document path outright.

If the whole job is smaller than a review, skip to
[If the work is too small](#if-the-work-is-too-small).

## If you are writing code

Pick by how many reviewable pieces the work has.

**Several independent components, or you would want an architecture diagram and a task board** —
run `d3nexus:dev-lifecycle`. It takes you through five gates: spec, task breakdown, execution order,
`quality_check`, and your own sign-off before the branch is finished.

**One component, one plan** — run `d3nexus:brainstorming`, then `d3nexus:writing-plans`. This leaves
the epic lifecycle; its remaining gates do not apply. You still cross two: `brainstorming` will not
let you start without an approved design, and it asks you to review the written spec before
planning.

**On the one-plan route, something has to execute the plan.** `writing-plans` produces a document,
not code. Run `d3nexus:subagent-driven-development` (recommended) or `d3nexus:executing-plans` on it
before you go near a quality gate. The epic route does this for you inside `dev-implementation`.

Either way, finish with `d3nexus:quality_check` and `d3nexus:finishing-a-development-branch`.

## If you are writing a document

Run `d3nexus:doc-lifecycle` when the document has enough sections that a reviewer could accept some
and reject others. It takes you through three gates: brief and outline, `d3nexus:doc_quality_check`, and
your sign-off.

Two shortcuts sit below that threshold:

- **A single architecture decision or spike report** — run `d3nexus:decision-records` directly and
  commit the record. Do not open gates around one file.
- **Anything smaller** — see [If the work is too small](#if-the-work-is-too-small).

A *batch* of records produced or backfilled as one piece of work is different: that does belong in
`d3nexus:doc-lifecycle`.

If you do not yet know what the document should say — a strategy piece, a proposal, an argument you
have not finished having — run `d3nexus:brainstorming` first, then come back.

## If you do not know what to build yet

Run `d3nexus:lean-product-lifecycle`. Three gates: problem space, value proposition, MVP backlog.
Gate 3 hands its backlog to `d3nexus:dev-designer`, so you land back in the code branch with
something worth building.

Budget for seven gates, not three — once you arrive at `dev-designer` you are at Stage 2 of
`dev-lifecycle` and its Gates 2 through 5 still apply.

Two signs you are in this case and should stop where you are:

- Nobody can name the target customer as a specific segment — only as "users" or "the business".
- The need is asserted rather than evidenced: no interviews, no data, no ranking of importance
  against satisfaction.

`d3nexus:brainstorming` checks both at step 2 and will send you here before it asks you anything else.

## If the work is too small

Do it. Commit it. Skip every lifecycle on this page.

Concretely: a typo, a broken link, a one-line correction, bumping a version, a comment. The test is
whether you can imagine a reviewer rejecting it. If you cannot, there is no breakdown to approve and
no outline to agree, so the **lifecycle gates** have nothing to do.

The **quality gate** is a different thing and you still run it — `d3nexus:quality_check` for code,
`d3nexus:doc_quality_check` for prose. Skipping a lifecycle is not skipping verification.

## Handing off between lifecycles

You will sometimes start in the wrong one. These are the three moves that keep your work:

**Discovery to code.** At Gate 3, `lean-product-lifecycle` hands `03_mvp_feature_backlog.md` to
`d3nexus:dev-designer`. Pass the file path; do not re-derive the backlog.

**Brainstorming to either branch.** `d3nexus:brainstorming` ends by invoking exactly one of
`dev-designer`, `writing-plans`, `doc-designer` or `lean-product-lifecycle`. Before it routes to
`dev-designer`, it moves your spec into `.devtool/epic/<epic_name>/` so the spec, the design and the
tasks stay together.

**Code back to discovery.** If a spec turns out to rest on an unvalidated assumption, stop and run
`d3nexus:lean-product-lifecycle`. Carry what you already know into the session as context — the
segment, the need, the evidence you have and the evidence you are missing — so Stage 1 does not start
cold.

> **Do not pre-create `.devtool/product/<slug>/01_problem_space_spec.md`.**
> `lean-product-lifecycle` resumes on file *presence*: that file existing makes it announce
> "Gate 1 is already verified" and start at Stage 2. You came here because the problem space was
> never validated, and Stage 1 is the validation. Creating the artefact skips it.

Leave the epic directory and its `task_*.md` files where they are. If the assumption survives
discovery you will come back to them; if it does not, they are the record of what you did not build.

One rule holds across all three: **never merge two specs into one epic.** Each keeps its own
spec → design → implementation lineage.
