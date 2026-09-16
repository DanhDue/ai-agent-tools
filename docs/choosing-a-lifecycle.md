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
