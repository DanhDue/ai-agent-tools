# The Product-Market Fit Pyramid and the Lean Product Process

Reference for [the Lean Product Lifecycle](../SKILL.md). Two models from *The Lean Product Playbook*
(Dan Olsen, Wiley 2015) that are routinely merged into one, and the rollback logic that depends on
keeping them apart.

---

## Table of Contents

1. [Why these are two objects](#why-these-are-two-objects)
2. [The pyramid: five layers](#the-pyramid-five-layers)
3. [Problem space and solution space](#problem-space-and-solution-space)
4. [The process: six steps](#the-process-six-steps)
5. [Mapping steps to layers](#mapping-steps-to-layers)
6. [Tectonic plates: the rollback protocol](#tectonic-plates-the-rollback-protocol)
7. [What product-market fit actually means](#what-product-market-fit-actually-means)

---

## Why these are two objects

Olsen developed the **Product-Market Fit Pyramid** first — a model of what product-market fit *is*,
decomposed into five testable hypotheses. He then designed the **Lean Product Process** — a
six-step workflow for *achieving* it, which walks the pyramid from the bottom up.

> "The framework, which I call the Product-Market Fit Pyramid, breaks product-market fit down into
> **five** key components: your target customer, your customers' underserved needs, your value
> proposition, your feature set, and your user experience (UX). … The Lean Product Process consists
> of **six steps**."

Summaries frequently present a six-item list labelled "the pyramid", produced by appending "MVP
prototype" and "test with customers" to the five layers. That list is neither model. Its specific
damage: **UX disappears**. The top layer of the pyramid — the layer a prototype exists to exercise,
and the cheapest layer to change — is silently replaced by two process steps, so an agent working
from that list cannot say "the problem is in the UX layer, not the feature set."

---

## The pyramid: five layers

Bottom to top, each layer depending on the one beneath it:

### 1. Target Customer *(bottom)*

The specific segment whose needs the product addresses. Members of a segment must genuinely share a
structure of needs — that is what makes needs-based segmentation stronger than demographic
segmentation, where a "unified group" can turn out to want different things.

*Hypothesis*: this specific segment exists, is reachable, and shares this set of needs.

### 2. Underserved Needs

Needs that matter a great deal to that customer and are poorly satisfied by what exists today.
"Underserved" is relative to the competitive landscape, not absolute.

*Hypothesis*: these needs score high on importance and low on satisfaction.

### 3. Value Proposition

How your product will meet those needs better and differently than the alternatives. This is the
essence of product strategy, and the problem-space layer over which you have the most control —
you cannot change customers or their needs, but you can choose which needs you aspire to meet.

*Hypothesis*: winning on *this* benefit will make this customer switch.

### 4. Feature Set

The specific functionality that delivers the value proposition.

*Hypothesis*: these features deliver that promise.

### 5. UX *(top)*

What brings the product's functionality to life for the user. Customers see and react to the UX and
the feature set; everything else they infer.

*Hypothesis*: this experience makes those features usable and valuable to this person.

---

## Problem space and solution space

```
Product:   SOLUTION SPACE      UX
                               Feature Set
           ============== PRODUCT-MARKET FIT ==============
Market:    PROBLEM SPACE       Value Proposition
                               Underserved Needs
                               Target Customer
```

- **Problem space** holds customer needs, pains, desires, jobs to be done and benefits — the *what*
  and the *why*. The customer owns it. You can target it; you cannot change it.
- **Solution space** holds the product, design, technology, interface and code — the *how*. The
  company owns it. It is entirely within your control.
- The **interface** falls between Value Proposition and Feature Set.

Dave McClure, quoted by Olsen: *"Customers don't care about your solution. They care about their
problems."*

**The nuance that summaries drop.** Keeping the spaces separate does not mean staying out of the
solution space. Olsen argues the opposite about *how you learn*:

> "Solution space discussions with customers is much more fruitful than trying to explicitly discuss
> the problem space with them. … The best problem space learning often comes from feedback you
> receive from customers on the solution space artifacts you have created."

The discipline is **alternation**: form problem-space hypotheses, build a solution-space artefact to
test them, learn, revise the hypotheses. Not abstinence.

---

## The process: six steps

1. **Determine your target customers.** Segment the market — demographic, psychographic, behavioral,
   and especially **needs-based**. Separate **users** from **buyers**. Locate the segment on the
   technology adoption life cycle and aim at **early adopters**. Build personas as hypotheses.
2. **Identify underserved customer needs.** Discovery interviews. Customer benefit laddering. Measure
   importance and satisfaction. Score the opportunity. Target high importance, low satisfaction.
3. **Define your value proposition.** Classify benefits with the Kano model against the competitive
   set. Build the value proposition grid. Choose one benefit to win on and commit to parity on the
   rest. Decide what you will not do.
4. **Specify your MVP feature set.** User stories. Feature chunking. ROI prioritization. The MVP
   Candidate Grid. Select the candidate by composition, not rank cut-off.
5. **Create your MVP prototype.** The lowest-fidelity solution-space artefact that can test these
   hypotheses — wireframes, interactive prototype, Wizard of Oz, concierge, smoke test, fake door.
   Note Olsen's terminology: **MVP** is an actual product; these are **MVP tests**.
6. **Test your MVP with customers.** Waves of five to eight target customers. Separate usability
   feedback from product-market fit feedback. Iterate: hypothesize, design, test, learn.

> Steps 5 and 6 are **not implemented** in release 1.1.0 of this skill suite. The lifecycle
> orchestrator must say so at Gate 3 rather than implying the process is complete.

---

## Mapping steps to layers

| Process step | Tests which pyramid layer | Stage skill |
|---|---|---|
| 1 Determine target customers | Target Customer | `d3nexus:lean-market-discovery` |
| 2 Identify underserved needs | Underserved Needs | `d3nexus:lean-market-discovery` |
| 3 Define value proposition | Value Proposition | `d3nexus:lean-value-strategy` |
| 4 Specify MVP feature set | Feature Set | `d3nexus:lean-mvp-scoping` |
| 5 Create MVP prototype | UX | *not yet implemented* |
| 6 Test MVP with customers | all five at once | *not yet implemented* |

Six steps, five layers: step 6 is the one that has no layer of its own, because it tests the whole
stack.

---

## Tectonic plates: the rollback protocol

Each layer is a hypothesis resting on the ones below. Olsen:

> "It's easier to make changes near the top of the pyramid, but changing hypotheses near the bottom
> can have significant" consequences for everything above.

Hence the metaphor: the lower layers are tectonic plates. When one shifts, the surface re-forms, and
polishing the surface first is wasted work.

**When something fails, walk up from the bottom.** For each layer ask whether its hypothesis still
holds, and stop at the first that does not:

| Layer | Diagnostic question | If it fails |
|---|---|---|
| Target Customer | Were the people we tested actually in the persona? | Re-segment. Everything above is built on strangers. |
| Underserved Needs | Do these needs still score high-importance, low-satisfaction? | Re-ladder, or re-segment to a group where they do. |
| Value Proposition | Does our promise give a rational customer a reason to switch? | Find a different angle, or a segment that values it. |
| Feature Set | Do these features actually deliver the promise? | Re-chunk. Usually cheaper than it looks. |
| UX | Can they use it and do they see the value? | Iterate the design. The cheapest fix — and rarely the cause. |

**The failure this prevents:** iterating at a higher level than where the problem lives. Olsen's own
words: *"you may find that you are iterating at a higher level than where the true problem lies …
iterating your UX design won't make much difference. You want to start at the bottom of the pyramid
and work your way up."*

**Say the cost out loud.** Founders resist bottom-layer changes because they are expensive, and an
agent that recommends one without acknowledging the cost sounds naive. Name what a re-segmentation
throws away, then recommend it anyway if that is where the failure is.

---

## What product-market fit actually means

> "Viewing product-market fit in light of this model, it is the measure of how well your product —
> **the top three layers of the pyramid** — satisfies the market — **the bottom two layers**."

Two consequences worth stating to a founder:

**Fit is judged relatively.** Customers assess your product against the alternatives available to
them, not against an absolute standard. A product can improve and lose fit if the alternatives
improve faster.

**Fit can be lost without changing anything.** Kano categories migrate: *"yesterday's delighters
become today's performance features and tomorrow's must-haves."* A static product slides down the
categories as expectations rise.

**The quantitative check**, once real users exist, is Sean Ellis's question — *"How would you feel if
you could no longer use this product?"* — with **≥ 40% answering "very disappointed"** indicating
product-market fit. That belongs to step 6 and is out of scope for this release, but it is the
number the whole process is aiming at, and a founder is entitled to know what the target is.

---

## Related

- [The Five Hard Guardrails](anti-hallucination-rules.md)
- [Lean Product Lifecycle](../SKILL.md)
