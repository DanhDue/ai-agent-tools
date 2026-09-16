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
code work, however much prose you also write. `doc_quality_check` enforces this and will refuse the
document path outright.

If the whole job is smaller than a review, skip to
[If the work is too small](#if-the-work-is-too-small).

## If you are writing code

Pick by how many reviewable pieces the work has.

**Several independent components, or you would want an architecture diagram and a task board** —
run `d3nexus:dev-lifecycle`. It takes you through five gates: spec, task breakdown, execution order,
`quality_check`, and your own sign-off before the branch is finished.

**One component, one plan** — run `d3nexus:brainstorming`, then `d3nexus:writing-plans`. This leaves
the epic lifecycle and its remaining gates do not apply.

Either way, finish with `d3nexus:quality_check` and `d3nexus:finishing-a-development-branch`.

## If you are writing a document

Run `d3nexus:doc-lifecycle` when the document has enough sections that a reviewer could accept some
and reject others. It takes you through three gates: brief and outline, `doc_quality_check`, and
your sign-off.

Two shortcuts sit below that threshold:

- **A single architecture decision or spike report** — run `d3nexus:decision-records` directly and
  commit the record. Do not open gates around one file.
- **Anything smaller** — see [If the work is too small](#if-the-work-is-too-small).

If you do not yet know what the document should say — a strategy piece, a proposal, an argument you
have not finished having — run `d3nexus:brainstorming` first, then come back.

## If you do not know what to build yet

Run `d3nexus:lean-product-lifecycle`. Three gates: problem space, value proposition, MVP backlog.
Gate 3 hands its backlog to `d3nexus:dev-designer`, so you land back in the code branch with
something worth building.

Two signs you are in this case and should stop where you are:

- Nobody can name the target customer as a specific segment — only as "users" or "the business".
- The need is asserted rather than evidenced: no interviews, no data, no ranking of importance
  against satisfaction.

`d3nexus:brainstorming` checks both at step 2 and will send you here before it asks you anything else.

## If the work is too small

Do it. Commit it. Skip every lifecycle on this page.

Concretely: a typo, a broken link, a one-line correction, bumping a version, a comment. The test is
whether you can imagine a reviewer rejecting it. If you cannot, there is nothing for a gate to do.

You still run a quality gate afterwards — `d3nexus:quality_check` for code,
`d3nexus:doc_quality_check` for prose. That rule has no size exemption.

## Handing off between lifecycles

You will sometimes start in the wrong one. These are the three moves that keep your work:

**Discovery to code.** At Gate 3, `lean-product-lifecycle` hands `03_mvp_feature_backlog.md` to
`d3nexus:dev-designer`. Pass the file path; do not re-derive the backlog.

**Brainstorming to either branch.** `d3nexus:brainstorming` ends by invoking exactly one of
`dev-designer`, `writing-plans`, `doc-designer` or `lean-product-lifecycle`. Before it routes to
`dev-designer`, it moves your spec into `.devtool/epic/<epic_name>/` so the spec, the design and the
tasks stay together.

**Code back to discovery.** If a spec turns out to rest on an unvalidated assumption, stop and run
`d3nexus:lean-product-lifecycle`. Carry the context you already gathered so Stage 1 does not start
cold.

One rule holds across all three: **never merge two specs into one epic.** Each keeps its own
spec → design → implementation lineage.
