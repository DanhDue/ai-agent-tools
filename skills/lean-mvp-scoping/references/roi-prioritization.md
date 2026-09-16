# ROI Prioritization

Reference for [lean-mvp-scoping](../SKILL.md), step 3. How Olsen prioritizes feature chunks in
*The Lean Product Playbook* Chapter 6 — the numeric method, the approximation, and the boundary
between what ROI decides and what it does not.

---

## Table of Contents

1. [The formula](#the-formula)
2. [Estimating the two terms](#estimating-the-two-terms)
3. [Reading the ROI chart](#reading-the-roi-chart)
4. [The tie-break rule](#the-tie-break-rule)
5. [Moving ideas left](#moving-ideas-left)
6. [Approximating ROI: the 3x3 grid](#approximating-roi-the-3x3-grid)
7. [What ROI does not decide](#what-roi-does-not-decide)
8. [The business-value variant](#the-business-value-variant)

---

## The formula

```
ROI = Return / Investment
    = Customer Value Created / Development Effort
```

Olsen's framing: invest \$100, get \$300 back, ROI is 3. In product development the investment is
almost never money —

> "When you are building a product or feature, the investment is usually the time that your
> development resources spend working on it, which you generally measure in units such as
> developer-weeks (one developer working for one week)."

So a chunk worth 6 units of customer value taking 2 developer-weeks has an ROI of 3; the same value
over 4 developer-weeks has an ROI of 1.5. Build the first one first.

**Sort every chunk into a rank-ordered list.** That list is the primary output of this step.

---

## Estimating the two terms

**Investment — developer-weeks or story points.** Either works. Story points are the Agile
convention: a very small story might be 1 point, a medium one 3, a large one 8. Anything above your
maximum threshold gets broken down further — that threshold is what makes a "chunk" a chunk.

**Return — customer value on a ratio scale.** This is the term people get wrong.

> "You need to use a **ratio scale**, which just means that the scores you use are in proportion to
> their value. For example, say you use a 0 to 10 scale for customer value… if one feature chunk has
> a score of 10 and another feature chunk has a score of 5, that should mean that the first feature
> would create double the amount of customer value as the second."

A rating scale where 10 is "very valuable" and 5 is "moderately valuable" is **not** a ratio scale,
and dividing by effort produces a number with no meaning. Before scoring, ask: *is a 10 here really
worth twice a 5?* If not, rescale until it is.

> [!WARNING]
> **Must-haves break naive value scoring, and the symptom is a distorted rank order.** By Kano
> definition a must-have produces *no* satisfaction when present and severe dissatisfaction when
> absent. So if "customer value" is scored as *how much this delights someone* — the intuitive
> reading — every must-have floors at 1 or 2 out of 10 **by construction**, and the whole ranking
> tilts away from the features the product cannot ship without.
>
> Score customer value as **value destroyed by absence, not delight created by presence**. On that
> basis a must-have scores high, which is correct: a product without it is worth nothing in its
> category.
>
> When a must-have comes back at 2/10, treat it as a **scale defect to investigate**, not as
> evidence about the feature. Re-scoring is a data-quality fix — it is never a reason to keep or cut
> a must-have, because [the composition rule](mvp-candidate-grid.md) already settles that
> independently of any number.

**On precision — do not over-invest in it.**

> "Some people struggle to create numerical estimates of customer value they feel are accurate.
> However, that isn't something to worry about too much, since this isn't about achieving decimal
> point precision. Even the effort estimates aren't likely to be very precise, because you haven't
> fully designed the features yet. You can't expect developers to give you accurate estimates based
> on just a high-level description of a feature. **The accuracy of the estimates should be
> proportional to the fidelity of the product definition.**"

The purpose is **comparison, not measurement**:

> "The main point of these calculations is less about figuring out actual ROI values and more about
> how they **compare** to each other."

A founder who spends a week refining estimates has misunderstood the tool. Rough numbers that rank
correctly are the whole deliverable.

---

## Reading the ROI chart

Plot customer value (return) on the vertical axis and development effort (investment) on the
horizontal. Each chunk is a point; ROI is the slope from the origin.

```
  high  |  D            G          <- G: high value, low effort. Build these.
 value  |       C
        |  A                B
        |            E
   low  |  F                    H  <- H: low value, high effort. Avoid.
        +---------------------------->
          low        effort      high
```

Olsen's worked pairs:

| Chunks | Value | Effort | ROI | Verdict |
|---|---|---|---|---|
| A | 6 | 2 dev-weeks | **3** | Same value as B for half the cost |
| B | 6 | 4 dev-weeks | 1.5 | |
| C | 4 | 4 dev-weeks | **1** | Same ROI as D — see the tie-break |
| D | 8 | 8 dev-weeks | 1 | |
| H | 2 | 8 dev-weeks | **0.25** | The quadrant that kills products |

On the bottom-right quadrant, Olsen's warning is worth quoting because the failure is asymmetric in
*time*:

> "The large effort of a low-ROI idea is often recognized early as the team works on implementing it;
> however, they usually don't realize the low customer value until after launch."

Google Buzz and Google Wave are his examples — large builds, shut down shortly after launch when
customer reaction showed the value was not there. You feel the cost long before you learn the return,
which is exactly why the estimate has to be made *before* you start.

---

## The tie-break rule

> "If you have two feature ideas with the same ROI, it's best to **prioritize the smaller scope idea
> higher**, because it takes less time to implement. You will deliver the value to customers more
> quickly."

C (4 value, 4 weeks) and D (8 value, 8 weeks) both score 1. Build C first: customers get value four
weeks sooner, and you get four weeks of feedback before committing to D — which may well change
what D should be.

This is the small-batch principle applied to prioritization. The same-ROI case is not a coin flip.

---

## Moving ideas left

The most valuable habit in this step, and it is a *creative* act rather than an analytical one:

> "Good product teams strive to come up with ideas like idea G — the ones that create high customer
> value for low effort. **Great product teams are able to take ideas like that, break them down into
> chunks, trim off less valuable pieces, and identify creative ways to deliver the customer value
> with less effort than initially scoped** — indicated in the figure by moving idea G to the left."

When a high-value chunk is expensive, the first response is not to drop it and not to accept the
cost. It is to ask what a cheaper version that delivers most of the value would look like.

Prompts that move things left:

- "What's the manual version of this?" — a human doing it behind the scenes tests the value at a
  fraction of the cost.
- "What if it only worked for the most common case?" — most of the value, a fraction of the edge cases.
- "What's the read-only version?" — displaying is usually far cheaper than editing.
- "What if it ran once a day instead of in real time?"
- "Which part of this would customers notice if it were missing?"

This is also the move to reach for when a **must-have** ranks badly. Must-haves cannot be cut, so the
only lever is making them cheaper.

---

## Approximating ROI: the 3x3 grid

> "I've explained how to think about ROI rigorously, but you can **also use this prioritization tool
> in a less rigorous manner**. **If you are struggling with creating numerical estimates** of customer
> value or development effort, you can score each feature idea high, medium, or low on customer value
> and on effort. This will create a three-by-three grid."

The nine buckets, rank-ordered by ROI, with square 1 the highest value at the lowest effort:

| Value \ Effort | Low | Medium | High |
|---|---|---|---|
| **High** | **1** | 3 | 6 |
| **Medium** | 2 | 5 | 8 |
| **Low** | 4 | 7 | 9 |

Priority sequence: `1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9`. Cell 9 — low value, high effort — is the one
to avoid outright.

> "If you find yourself stuck because you're not sure about the estimates for customer value and
> effort, just use your best guess to place each feature into one of the nine cells. These are just
> your starting hypotheses; you can and likely will change them as you learn and iterate."

**Three rules for using it:**

1. **Numeric ROI first.** Reach for the grid only when estimates genuinely cannot be produced — not
   because it is faster.
2. **Declare it.** Say in the artefact that the fallback was used and why. A reader six months from
   now cannot otherwise tell whether a cell assignment was measured or guessed.
3. **It still only orders the work.** The cell number is a priority, not an admission ticket.

---

## What ROI does not decide

> [!WARNING]
> **ROI ranking orders the work. It does not decide MVP membership.**

Any rule of the form *"the MVP is cells 1–3"* or *"the MVP is the top N by ROI"* will eventually cut
a high-effort must-have, and a product missing a must-have is not viable at any price.

Olsen breaks his own rank order explicitly:

> "You can sort your list of feature chunks by estimated ROI to create a rank-ordered list — which is
> a good starting point to help decide which feature chunks should be part of the MVP candidate.
> **However, sometimes you can't just follow the strict rank order to create a complete MVP; you
> might need to skip down to include important features.**"

Membership is decided by the **MVP composition rule** — all must-haves, enough of the designated
performance benefit to be visible, the top delighter. See
[The MVP Candidate Grid](mvp-candidate-grid.md).

**Where each tool applies:**

| Question | Tool |
|---|---|
| Which chunk do we build first? | ROI rank |
| Which chunks are in v1 at all? | MVP composition rule |
| Which version does a non-v1 chunk land in? | ROI rank |
| This must-have ranks 11th — cut it? | **No.** Chunk it down. |

---

## The business-value variant

Return does not have to be customer value.

> "The return in the ROI calculation can be a measure of value to your business instead of value to
> the customer. In those cases, you often have an estimated dollar amount that you can use for the
> return. This will be an expected gain in revenue or an expected decrease in cost."

Useful once the product is live and you are optimizing rather than discovering — for a given
improvement in conversion rate, you can estimate the revenue, and each improvement idea carries a
dollar figure.

**Do not mix the two in one ranking.** A list where some chunks are scored in customer-value units
and others in dollars is not sorted by anything. Pick one basis per ranking and say which in the
artefact. During MVP scoping the basis is **customer value**, because there is no conversion rate to
improve yet.

---

## Related

- [The MVP Candidate Grid](mvp-candidate-grid.md) — what membership is actually decided by
- [The MVP Attribute Pyramid](mvp-attribute-pyramid.md) — the completeness check
- [lean-mvp-scoping](../SKILL.md)
