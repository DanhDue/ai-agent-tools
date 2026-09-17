---
name: doc-designer
description: Turns a document request into a brief, an outline and one task per section. Establishes who the document is for, classifies it into exactly one Diátaxis type, and enforces Gate 2 of the document lifecycle. Use it at the start of any documentation work large enough to break down.
---

# Document Designer

Stage 1 of `doc-lifecycle`. Turns a document request into a brief, an outline, and one task per
section. Enforces **Gate 2**.

The development-side sibling is `dev-designer`. Where that skill produces architecture diagrams and
BDD scenarios, this one produces an audience and a type — because a document's binding constraint
is not what calls it, but who reads it.

**Announce at start:** "I'm using the doc-designer skill to design the `<doc_slug>` document."

## When to Use

- `doc-lifecycle` routes here at Stage 1.
- A document spans enough sections to need a breakdown.
- An existing document has drifted and needs re-outlining before it is rewritten.

**Don't use when** the work is a typo, a one-line correction, or a single Architecture Decision
Record — see `doc-lifecycle`'s *When NOT to use this*.

## Input

Either a raw request ("we need a runbook for X") or an approved spec from `doc-brainstorming`. When a
spec exists, treat it as settled on scope and record it in the overview's Meta Data as
`Source Spec:`. Your job is to give it an audience, a type and a shape — not to re-open its
decisions.

## The Four Steps

### Step 1 — Establish the audience and their job

Before anything else, answer three questions in the brief:

- **Who reads this?** A role, not "the team".
- **What are they trying to do** at the moment they open it?
- **What do they already know?** This sets the floor the document may assume.

This is the document equivalent of requirements. Skipping it produces text that is accurate and
unusable, and no later step recovers from it.

### Step 2 — Classify into exactly one Diátaxis type

Diátaxis (Daniele Procida, [diataxis.fr](https://diataxis.fr/)) identifies four needs and four
corresponding forms of documentation. Use the author's own compass: ask **action or cognition?**
and **acquisition or application?**

| If the content… | …and serves the user's… | …then it must belong to… |
|---|---|---|
| informs action | acquisition of skill | a **tutorial** |
| informs action | application of skill | a **how-to guide** |
| informs cognition | application of skill | **reference** |
| informs cognition | acquisition of skill | **explanation** |

| Type | Orientation |
|---|---|
| Tutorial | learning-oriented |
| How-to guide | goal-oriented |
| Reference | information-oriented |
| Explanation | understanding-oriented |

The author's own definitions of each type: [`references/diataxis-source.md`](references/diataxis-source.md).

**If the material spans more than one type, split it into more than one document — one per type —
and link between them.** This is a procedure step, not advice. An agent asked for "a guide" produces
a blend by default, and advice does not stop a default. The result of a blend is a document that is
part tutorial, part reference, part explanation, and serves nobody.

The author states this exclusion separately for **all four** types — it is his rule, not an
inference from it. The four passages are quoted in
[`references/diataxis-source.md`](references/diataxis-source.md).

Note the remedy is to **relocate and link**, never to delete. The other material belongs elsewhere,
not nowhere.

### Step 3 — Write the outline

A list of sections, each with **one line stating that section's purpose**. That line is not
decoration: `doc-implementation` checks every drafted section against it, and it is the only
pre-written expectation a section is measured by.

**This outline becomes the deliverable's table of contents.** From four sections upward the finished
document carries one, linking each section — it is the same list the reader needs, so write it once.
Gate 3 checks for it.

### Step 4 — Break the outline into tasks

One task per section. Present the numbered list and ask the user to confirm the breakdown and
granularity. **This checkpoint is Gate 2.** Write no task file before the user confirms.

## The Overview Document

Generate both language variants in the document's own directory:

- English: `.devtool/epic/<doc_dir>/<doc_dir>.en.md` — **canonical**, always written first
- Vietnamese: `.devtool/epic/<doc_dir>/<doc_dir>.vi.md` — a translation, kept in sync, never
  diverging in structure or facts

Architecture diagrams, sequence diagrams and BDD scenarios do not apply. **They are replaced, not
supplemented, by this Meta Data block:**

```
Kind: document
Audience: <who reads this, and what they are trying to do>
Diátaxis mode: tutorial | how-to | reference | explanation
Non-goals: <what this document deliberately does not cover>
Acceptance: <one thing the reader can do after reading it>
Source Spec: <link, if this came from doc-brainstorming>
```

`Kind: document` records what this work item is, for the shared Kanban board and the archive. It is
not a dispatch key — `doc-lifecycle` names `doc_quality_check` as Gate 3 directly, so the two
quality gates never have to know about each other.

**`Acceptance` must name something the reader can do.** Not a length, not a section count, and not
"explains the deploy process" — that describes the document, not the reader. "A new engineer
completes a dev deploy in under 15 minutes without asking anyone" is an acceptance criterion,
because it can be observed and it can fail.

## Concurrent-Epic Backlog Rule

The Kanban board is shared with `dev-lifecycle`. Before writing any task file, check
`.devtool/features/*.md` (excluding `done/` and `archived/`) for a task whose `epic:` names a
*different* epic with status `todo`, `in-progress` or `review`. If one exists:

- Create every task in this run with `status: "backlog"` instead of `"todo"`.
- Note in the overview's **Status** field which epic it is queued behind, by name.

Flipping `backlog` to `todo` later is a human call, not this skill's.

## Red Flags

- Producing an outline before the audience is established.
- Declaring two types on one document, or declaring none.
- Deleting out-of-type material instead of relocating and linking it.
- An `Acceptance` field describing the document rather than the reader.
- Writing task files before the user confirms the breakdown — that checkpoint *is* Gate 2.
- Stating a Diátaxis rule that does not trace to a quotation in the source fidelity review.
- Defaulting tasks to `todo` without checking for another epic's active tasks first.
