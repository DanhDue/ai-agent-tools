# Opportunity Score Formulas

Reference for [lean-market-discovery](../SKILL.md), Phase 4. Three frameworks for turning importance
and satisfaction into a decision, from *The Lean Product Playbook* Chapter 4 — two to use and one to
understand and reject.

All three assume **normalized** inputs. If you have not read
[Measuring Importance and Satisfaction](importance-satisfaction-survey.md), the numbers below will
be arithmetic performed on noise.

---

## Table of Contents

1. [Gap analysis, and why it is not enough](#gap-analysis-and-why-it-is-not-enough)
2. [Ulwick: Opportunity Score](#ulwick-opportunity-score)
3. [Olsen: Opportunity to Add Value](#olsen-opportunity-to-add-value)
4. [The scale-mismatch guard](#the-scale-mismatch-guard)
5. [The quadrant](#the-quadrant)
6. [Choosing what to pursue](#choosing-what-to-pursue)

---

## Gap analysis, and why it is not enough

The obvious move:

```
Gap = Importance − Satisfaction
```

The bigger the gap, the more underserved the need. It is trivial to compute and easy to explain, and
Olsen presents it first — then rejects it as a primary tool:

> "Its biggest shortcoming is that it treats all gaps of equal size the same. For example, using a
> 0 to 10 scale, if a need had an importance of 10 and a satisfaction of 5, the gap would be 5. If
> another need had an importance of 6 and a satisfaction of 1, the gap would also be 5. But this
> doesn't make intuitive sense, because a gap of 5 on a need with an importance of 10 should be more
> important than the same size gap on a need with an importance of 6."

It also goes negative when satisfaction exceeds importance, which is real information — that need is
over-served — but makes the score hard to rank alongside the others.

**Use it for intuition. Do not rank on it.** Both formulas below exist to fix exactly this defect.

---

## Ulwick: Opportunity Score

From Anthony Ulwick's outcome-driven innovation (*What Customers Want*), adopted by Olsen.

```
Opportunity Score = Importance + max(Importance − Satisfaction, 0)
```

| | |
|---|---|
| **Input scale** | 0–10 integers, both terms |
| **Output range** | 0 – 20 |
| **Floor** | 0, when importance is 0 |
| **Ceiling** | 20, when importance is 10 and satisfaction is 0 |

**How it fixes gap analysis.** Two changes. The difference is **floored at zero**, so an over-served
need cannot produce a negative that competes with genuinely small gaps. And **importance is added
back**, which makes it the tie-breaker between equal gaps.

Olsen's own worked comparison:

| Need | Importance | Satisfaction | Gap | Opportunity Score |
|---|---|---|---|---|
| A | 10 | 5 | 5 | `10 + max(5, 0)` = **15** |
| B | 6 | 1 | 5 | `6 + max(5, 0)` = **11** |

> "Using Ulwick's formula, even though the gap in importance and satisfaction is the same between
> the two needs, the first need — with the higher importance — has the higher opportunity score."

### Thresholds

> "Ulwick considers opportunities with scores greater than 15 to be very attractive, and those below
> 10 to be unattractive."

| Score | Band | What to do |
|---|---|---|
| **> 15** | Very attractive | Pursue. Gate 1 requires at least one of these. |
| **10 – 15** | Marginal | Admit only with a written rationale. Never the sole basis for Gate 1. |
| **< 10** | Unattractive / over-served | Reject. Ladder further, or re-segment. |

> [!WARNING]
> A threshold of `>= 10` is **not** a bar for an attractive opportunity — it is the floor of the
> band Olsen calls unattractive. Gate 1 requires a need above **15**.

---

## Olsen: Opportunity to Add Value

Olsen's own visual framework. Importance and satisfaction are plotted on a unit square; the customer
value a product *delivers* is the area of the rectangle under the point, and the value that can
still be *added* is the area of the rectangle to its right.

```
Opportunity to Add Value = Importance × (1 − Satisfaction)
```

| | |
|---|---|
| **Input scale** | 0–1 fractions (or 0–100%), both terms |
| **Output range** | 0 – 1 |
| **Reading** | Relative — rank scores against each other, no fixed threshold |

**Worked examples from the book:**

| Opportunity | Importance | Satisfaction | Score |
|---|---|---|---|
| A | 0.70 | 0.70 | `0.7 × 0.3` = **0.21** |
| B | 0.90 | 0.30 | `0.9 × 0.7` = **0.63** |
| Feature X *(real product data)* | 0.82 | 0.55 | `0.82 × 0.45` = **0.37** |

> "Opportunity B offers the potential to create three times as much customer value as Opportunity A."

In the real-product dataset, Feature X at 0.37 was the highest of 13 features; eleven scored below
0.25. There is no absolute "good" score here — 0.37 was excellent *in that set*.

**The structural insight this formula carries**, which the Ulwick score hides: the *maximum* customer
value a need can ever yield is set by its **importance** alone — the height of the rectangle. Raising
satisfaction only widens it. That is the mathematical case for pursuing high-importance needs even
when the current gap looks modest: low-importance needs have a low ceiling no matter how badly they
are served today.

---

## The scale-mismatch guard

The two formulas take different inputs and produce different ranges. They are not interchangeable
and their numbers are not comparable.

| | Olsen | Ulwick |
|---|---|---|
| Inputs | **0–1** | **0–10** |
| Output | 0 – 1 | 0 – 20 |
| Thresholds | none — relative | `>15` / `10–15` / `<10` |

**Three failures to refuse outright:**

1. **Un-normalized inputs.** Raw 5-point and 7-point responses fed to either formula. Ask which
   scales were used; refuse to compute until told.
2. **Cross-threshold reporting.** An Olsen score of 0.63 announced as "unattractive, below 10", or an
   Ulwick score of 16 as "0.16, low headroom". The number is valid; the threshold belongs to the
   other formula.
3. **Silent scale conversion.** Taking a 1–10 satisfaction of 8 and using 0.8 in Olsen's formula
   without saying so. It happens to be arithmetically close, and it hides whether anyone chose the
   basis deliberately.

**Always report both, labelled, with their inputs:**

> Need: *"know whether the transfer arrived, without asking"*
> Importance 4/5 → 7.5 (0–10) / 0.75 (0–1) · Satisfaction 2/7 → 1.67 (0–10) / 0.167 (0–1)
> **Ulwick 13.3** (marginal) · **Olsen 0.62** (high headroom)

When the two disagree, say so and say why. The usual pattern: high importance with high satisfaction
gives a marginal Ulwick score and a low Olsen score — both saying "well served, little room". High
importance with moderate satisfaction can read marginal on Ulwick while Olsen still shows real
headroom. Report the disagreement rather than picking the flattering one.

---

## The quadrant

Plot every need with **importance on the vertical axis** and **satisfaction on the horizontal**.

```
  high  |  UNDERSERVED          |  WELL SERVED
importance|  (target this)      |  (table stakes)
        |----------------------|---------------------
   low  |  IRRELEVANT          |  OVER-SERVED
        |  (ignore)            |  (stop investing)
        +----------------------+--------------------->
           low                     high
                    satisfaction
```

- **Upper left — underserved.** High importance, low satisfaction. This is the target, and this is
  what both formulas are designed to surface.
- **Upper right — well served.** Important and already handled. These become your Kano **must-haves**
  in Stage 2: required, but not a source of differentiation.
- **Lower right — over-served.** The industry is over-investing in something customers stopped caring
  about. Cheap parity, sometimes a cost advantage.
- **Lower left — irrelevant.** Leave it.

Olsen's example: Uber pursued an upper-left opportunity. The needs around hired cars — comfort,
convenience, safety, punctuality — rated high in importance and low in satisfaction with taxis, and
almost nobody described themselves as completely satisfied.

An axis caution from the book: when plotting real data, draw both axes from zero. A cluster near the
origin of a truncated chart can look like a low-opportunity corner when those points would sit near
the centre of a full one.

---

## Choosing what to pursue

> "When you are evaluating opportunities to pursue, you should pursue the ones with the highest
> opportunity scores."

In practice:

1. Rank all needs by **Ulwick score**; this is the one with absolute bands.
2. Sanity-check the ranking against **Olsen scores**. Large disagreements mean you should look again
   at the underlying ratings, not average the two.
3. Confirm the top needs sit in the **upper-left quadrant**.
4. Take the **top one or two** into Stage 2. Not five. The value proposition is about choosing.
5. **Gate 1 requires at least one need above 15.** If nothing clears it, the answer is not a lower
   bar — it is another ladder, or another segment.

What carries into Stage 2: the top needs become the rows of the Kano classification and the
competitive value proposition grid. Needs in the **upper right** carry forward as must-haves. Needs
in the **upper left** are where your performance benefits and delighters must live, because they are
the only place a rational customer has a reason to switch.

---

## Related

- [Measuring Importance and Satisfaction](importance-satisfaction-survey.md) — the inputs
- [Customer Discovery Script](customer-discovery-script.md) — getting honest ratings
- [lean-market-discovery](../SKILL.md)
