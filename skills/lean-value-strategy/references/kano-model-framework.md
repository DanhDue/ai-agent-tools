# The Kano Model

Reference for [lean-value-strategy](../SKILL.md), step 1. Noriaki Kano's framework for classifying
customer needs, as Olsen applies it in *The Lean Product Playbook* Chapters 4 and 5.

The model's utility is not the taxonomy. It is that **the three categories behave differently when
you invest in them**, so knowing which one a benefit is in tells you what a marginal unit of effort
buys.

---

## Table of Contents

1. [The three categories](#the-three-categories)
2. [The asymmetry that matters](#the-asymmetry-that-matters)
3. [Hierarchy: the order they matter in](#hierarchy-the-order-they-matter-in)
4. [Migration: categories decay over time](#migration-categories-decay-over-time)
5. [Classifying a benefit](#classifying-a-benefit)
6. [Strategic consequences](#strategic-consequences)

---

## The three categories

> "The utility of the model is that it breaks customer needs into three relevant categories that you
> can use: performance needs, must-have needs, and delighters."

### Must-haves

Basic expectations. Their presence is invisible; their absence is disqualifying.

- **Met**: neutral. Nobody thanks you. The customer assumed it.
- **Missing**: extreme dissatisfaction. The product is not considered.
- **Investment curve**: a cliff, then flat. You get nothing for exceeding the bar.

A car that starts. A bank app that shows your balance. Everyone in the category has these, which is
exactly why they cannot differentiate you.

### Performance benefits

More is better, roughly linearly. This is where head-to-head competition happens.

- **Met better**: satisfaction rises.
- **Met worse**: dissatisfaction rises.
- **Investment curve**: a slope. Every increment buys a proportional increment of satisfaction.

Fuel economy. Search relevance. Time to complete a booking.

### Delighters

Unexpected benefits that exceed expectations.

- **Present**: delight, out of proportion to the effort.
- **Absent**: *no dissatisfaction whatsoever* — the customer was not expecting it.
- **Investment curve**: asymmetric. Bounded downside, outsized upside.

Olsen's example: GPS navigation in the first car models to offer it. Drivers were not expecting it,
so its absence cost nothing — and its presence was remarkable.

---

## The asymmetry that matters

The categories differ in **what happens when you do not deliver**, and that asymmetry drives the
strategy:

| Category | Delivering it buys you | Not delivering it costs you |
|---|---|---|
| Must-have | Nothing — it was assumed | **Everything** — you are not in the running |
| Performance | Proportional satisfaction | Proportional dissatisfaction |
| Delighter | **Outsized** delight | Nothing — they were not expecting it |

Read the outer rows together. Must-haves are pure downside protection: unbounded loss, zero gain.
Delighters are pure upside: bounded loss, high gain.

That is the whole argument for the MVP composition rule. **All** must-haves, because missing one is
disqualifying regardless of how good the rest is. And at least one delighter, because it is the
cheapest asymmetric bet on the board.

---

## Hierarchy: the order they matter in

The categories are not a menu. They stack:

```
        /  Delighters       \     <- only matter once performance is competitive
       /  Performance        \    <- only matter once must-haves are met
      /   Must-haves          \   <- the foundation
     -------------------------
```

> "The Kano model also exhibits hierarchy… the fact that your product has a delighter doesn't matter
> [if must-haves are missing]. You have to be competitive on performance features before delighters
> matter."

Practically: a delighter cannot rescue a product that fails a must-have. Customers never get far
enough to see it. When a founder's differentiation is a delighter and their must-have coverage is
incomplete, the sequencing is not a preference — the delighter is unreachable.

Note the resemblance to the **MVP Attribute Pyramid** in `d3nexus:lean-mvp-scoping` — functional,
reliable, usable, delightful. Both say the same thing about *delight*: it sits at the top, it is
real value, and it is only collectable once the layers beneath it hold.

---

## Migration: categories decay over time

The single most consequential property of the model:

> "Needs migrate over time. **Yesterday's delighters become today's performance features and
> tomorrow's must-haves.** Growing customer expectations" drive the ratchet.

GPS navigation again: a delighter when it first appeared, then a performance benefit as competitors
added it and buyers compared screen size and map quality, now a must-have that a car without would
be marked down for.

```
   Delighter  ------->  Performance  ------->  Must-have
   (unique)             (compared)             (assumed)
```

The ratchet only turns one way. Three consequences:

**Your differentiation has a shelf life.** A delighter is a temporary lead, not a moat. Plan for the
day it is table stakes.

**You can lose product-market fit without changing anything.** If expectations rise while your
product stays still, benefits slide down the categories underneath you. Fit is measured against
current alternatives, not against your launch.

**Classification is dated, not permanent.** Record *when* you classified a benefit. A category
assignment from two years ago is a historical note, not a finding — and the further along the
category is in its migration, the shorter its useful life.

---

## Classifying a benefit

**Ask about absence, not presence.** "Would you like X?" gets a yes for everything. The diagnostic
question is what happens without it:

| Answer to "what if this were missing?" | Category |
|---|---|
| "I wouldn't use the product at all" / "that's not a real product" | **Must-have** |
| "I'd be annoyed" / "I'd prefer the one that does it better" | **Performance** |
| "I wouldn't have noticed" / "I wasn't expecting that" | **Delighter** |

Kano's own method pairs a **functional** question ("how do you feel if it has this?") with a
**dysfunctional** one ("how do you feel if it doesn't?"). The dysfunctional half carries most of the
signal, and it is the half people skip.

**Two failure modes to watch for:**

- **Everything is a must-have.** Usually the founder is describing what they want to build rather
  than what the category requires. Test: *"Name a product in this category that ships without it and
  still sells."* If one exists, it is not a must-have.
- **The delighter is actually a performance benefit.** "Faster than the competition" is not a
  delighter, however much faster. If customers are already comparing products on that axis, it is a
  performance benefit and you are competing, not surprising.

---

## Strategic consequences

**Must-haves: meet efficiently, do not over-invest.** Olsen: *"it's important to list the must-haves,
since they are required. However, since all products in the category have to have them, they are not
the core part of your value proposition."* Effort spent exceeding a must-have is effort that bought
nothing. Meet the bar and move the resources to where the slope is.

**Performance: pick one.** You cannot lead on all of them, and attempting it means leading on none.
Choose the one that matters most to your segment, and hold parity elsewhere.

**Delighters: at least one, and expect to need another.** Cheap asymmetric upside today, migrating to
table stakes tomorrow. A product with no delighter and no performance lead is a me-too, and the Kano
model has no category for "same as the competition" because there is no satisfaction curve for it.

**The Gate 1 quadrants tell you where to look:**

| Gate 1 quadrant | Likely Kano category | What to do |
|---|---|---|
| Upper-right — important, well satisfied | Must-have | Meet it. Cheaply. |
| Upper-left — important, poorly satisfied | Performance or delighter | **Compete here.** This is the opening. |
| Lower-right — unimportant, well satisfied | Over-served performance | Parity at low cost. Consider doing less. |
| Lower-left — unimportant, poorly satisfied | Neither | Ignore. |

---

## Related

- [Competitive Matrix Guide](competitive-matrix-guide.md) — turning this classification into a grid
- [lean-value-strategy](../SKILL.md)
