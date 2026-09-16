# The MVP Candidate Grid

Reference for [lean-mvp-scoping](../SKILL.md), steps 4–5. Olsen's Figures 6.3 and 6.4 — the artefact
that turns a value proposition into a backlog, and the composition rule that decides what ships.

This grid is the physical link between Gate 2 and Gate 3. Without it, "which features are in the
MVP?" gets answered from a flat ROI list, and a flat list has no way to notice that a must-have is
missing.

---

## Table of Contents

1. [Structure](#structure)
2. [The composition rule](#the-composition-rule)
3. [Why rank order is not the rule](#why-rank-order-is-not-the-rule)
4. [Columns become versions](#columns-become-versions)
5. [The two-version limit](#the-two-version-limit)
6. [Worked example](#worked-example)
7. [Common failures](#common-failures)

---

## Structure

**Rows are benefits, taken straight from the value proposition.** Not features — benefits. Olsen's
labelling:

| Label | Meaning |
|---|---|
| `M1`, `M2` … | Must-have 1, must-have 2 … |
| `P1`, `P2`, `P3` … | Performance benefit 1, 2, 3 … |
| `D1`, `D2` … | Delighter 1, delighter 2 … |

A chunk is then `M1A` — feature chunk A for must-have 1 — or `P3B`, chunk B for performance benefit 3.

**Cells hold that benefit's feature chunks in priority order**, highest priority leftmost.

> "Once you are done chunking, scoping, and prioritizing, you can create a simple grid that lists the
> benefits from your value proposition and that lists, for each benefit, the top feature ideas broken
> into chunks… I've listed the top feature chunks for each benefit in priority order, with higher
> priority on the left."

**Why rows are benefits and not features.** A flat, ROI-sorted feature list cannot tell you whether
every benefit is covered — you have to reconstruct that relationship in your head, and under
deadline pressure nobody does. Grouping by benefit makes a missing must-have a visibly empty row.
That is the grid's entire job.

---

## The composition rule

Work down the **leftmost column** and decide which chunks the MVP candidate needs. Refer back to the
value proposition constantly while doing it.

### 1. All the must-haves

> "To start with, your MVP candidate needs to have **all the must-haves** you've identified."

Non-negotiable, and independent of ROI rank. A must-have is what the category requires; a product
missing one is not a cheaper product, it is not a product in that category.

**If a must-have is expensive:** chunk it down further. Ask what the smallest version that still
clears the customer's bar looks like. Cutting is not an option; shrinking is.

### 2. Enough of the designated performance benefit to be visible

> "After that, you should focus on the main performance benefit you're planning to use to beat the
> competition. You should select the set of feature chunks for this benefit that you believe will
> provide **enough for customers to see the difference** in your product."

Note "the set". One chunk is frequently not enough — "marginally better" is not a reason to switch,
and a differentiator nobody notices is not a differentiator. This is the row where including two or
three chunks in v1 is normal.

### 3. The top delighter

> "Delighters are part of your differentiation, too. You should include your top delighter in your
> MVP candidate. That may not be necessary if you have a very large advantage on a performance
> benefit."

Omissible only when the performance lead is genuinely large — and "large" is a claim that belongs in
the artefact, not an assumption.

### 4. The covering test

> "The goal is to make sure that your MVP candidate includes **something** that customers find
> superior to others' products and, ideally, unique."

Read the v1 column back and ask: what here would make someone switch? If the honest answer is
"nothing, but it covers the basics", you have specified a me-too MVP, and steps 2 and 3 were not
satisfied however many chunks are listed.

**Chunks per benefit.** Olsen draws at most one chunk per benefit in v1 for simplicity, then notes:
*"it may be the case that you need two or three feature chunks for a given benefit, depending on your
situation and how small your chunks are."* The principle is unchanged — pick which chunks belong in
the leftmost column.

---

## Why rank order is not the rule

The ROI list is where you *start*, not where you land:

> "You can sort your list of feature chunks by estimated ROI to create a rank-ordered list — which is
> a good starting point to help decide which feature chunks should be part of the MVP candidate.
> **However, sometimes you can't just follow the strict rank order to create a complete MVP; you
> might need to skip down to include important features.**"

The two tools do different jobs:

| Tool | Answers |
|---|---|
| **ROI rank** | In what order do we build? Which version does a deferred chunk land in? |
| **MVP Candidate Grid** | Is this chunk in v1 at all? |

When they conflict, the grid wins — because the grid knows about benefits and the list does not.

> [!WARNING]
> **"The MVP is ROI cells 1–3"** is not a rule from this book, and it is actively harmful. It cuts
> high-effort must-haves and produces an incomplete product that fails in the market for a reason the
> team will misdiagnose as poor execution.

---

## Columns become versions

> "The feature chunks that you believe need to be in your MVP candidate will stay in the leftmost
> column, which you can label **v1**, while the others are pushed out to the right. You can create a
> preliminary product roadmap by continuing this process and creating columns for each future version,
> with each column containing the feature chunks that you plan to add."

The roadmap is a *by-product* of scoping, not a separate exercise. Everything not in v1 is already
sorted into v1.1 and v1.2 by the same ROI ranking that ordered v1.

---

## The two-version limit

> "I don't recommend that you plan more than one or two minor versions ahead at the outset, since a
> lot of things are apt to change when you show your MVP candidate to customers for the first time.
> You'll learn that some of your hypotheses weren't quite right and will come up with new ones. You
> may end up changing your mind on which benefit is most important… So if you've made tentative plans
> beyond your MVP, **you must be prepared to throw them out the window** and come up with new plans
> based on what you learn from customers."

**Stop at v1.2.** A v2.0 column in a pre-launch roadmap is not planning; it is a commitment made
before any evidence exists, and it is harder to abandon precisely because it is written down.

State this when handing the artefact over. Founders read a roadmap as a promise, and the whole point
of the MVP is that these are hypotheses about to be tested.

---

## Worked example

Gate 2 produced: two must-haves, three performance benefits with **P3** designated the winner, and
**D2** as the top delighter.

| Benefit | **v1** | v1.1 | v1.2 |
|---|---|---|---|
| M1 — account setup | `M1A` | | |
| M2 — transaction history | `M2A` | | |
| P1 — breadth of integrations | | | `P1A` |
| P2 — reporting depth | | | |
| **P3 — time to reconcile** *(winner)* | `P3A` | `P3B` | |
| D1 — *(competitor's delighter)* | | | |
| **D2 — auto-drafted month-end note** | `D2A` | `D2B` | |

Reading it back:

- Both must-haves in v1. `M2A` ranked eighth by ROI; it is in anyway.
- **P3** is the designated winner and carries `P3A` in v1 with `P3B` following in v1.1 — the lead is
  extended rather than declared once.
- **D2** gives v1 something unique.
- **P2** has no chunks in any column. That is the Gate 2 decision to score it Low, showing up in the
  backlog as an empty row. Correct, and worth pointing at during review.
- **P1** is deferred to v1.2 — parity is committed but not extended.
- **D1** is a competitor's delighter and is not being matched. Also a Gate 2 decision.

Two empty rows in a grid are usually a sign that the strategy survived contact with the backlog. A
grid with no empty rows means everything is being built, which means nothing was decided.

---

## Common failures

**The flat backlog.** A single ROI-sorted list with no benefit grouping. It cannot show a missing
must-have, and it invites "take the top 10" as a scoping method.

**The empty must-have row.** A must-have with no chunk in v1. Either it was cut on ROI grounds, which
is the failure this document exists to prevent, or it was never chunked. Both block Gate 3.

**One chunk on the winning benefit.** Technically present, practically invisible. Ask: would a
customer comparing the two products notice? If not, add chunks or accept you are not winning that
benefit.

**The v2.0 column.** Planning past the two-version limit. Delete it; it is fiction and it will be
quoted back at you.

**Delighter deferred to v1.1.** Then v1 contains nothing customers find superior. This is the me-too
MVP, and it will test as "fine, but I'd stick with what I have."

**Every row populated in v1.** No trade-offs made. Go back to the Gate 2 grid — if the value
proposition had a Low, it should appear here as an empty row.

---

## Related

- [ROI Prioritization](roi-prioritization.md) — what the ranking is for
- [The MVP Attribute Pyramid](mvp-attribute-pyramid.md) — completeness within the narrow scope
- [lean-mvp-scoping](../SKILL.md)
