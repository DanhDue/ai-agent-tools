# Measuring Importance and Satisfaction

Reference for [lean-market-discovery](../SKILL.md), Phase 3. The measurement design that both
opportunity formulas depend on, from *The Lean Product Playbook* Chapter 4.

Getting this wrong invalidates everything downstream silently — the formulas will still produce
numbers, they will just be meaningless. That is what makes this the most-skipped and
highest-consequence step in Stage 1.

---

## Table of Contents

1. [Why two different scales](#why-two-different-scales)
2. [The importance scale](#the-importance-scale)
3. [The satisfaction scale](#the-satisfaction-scale)
4. [Scale design rules](#scale-design-rules)
5. [Normalization](#normalization)
6. [Who to ask, and about what](#who-to-ask-and-about-what)
7. [Sample size: quant on qual](#sample-size-quant-on-qual)
8. [Worked example](#worked-example)

---

## Why two different scales

There are two kinds of rating scale, and importance and satisfaction are not the same kind.

- A **unipolar** scale runs from 0 to 100% of an attribute. There is no negative end.
- A **bipolar** scale runs from negative through neutral to positive.

Olsen's reasoning:

> "It's usually best to measure satisfaction using a bipolar scale; since people can be satisfied or
> dissatisfied, a negative score makes sense. In contrast, importance is just a matter of degree —
> without any negative value — and therefore better measured with a unipolar scale."

Research on scale reliability generally finds **5 points best for unipolar** and **7 points best for
bipolar**, which is why the two instruments differ in length. This is not a stylistic choice; a
7-point importance scale asks respondents to express something the construct does not have.

---

## The importance scale

**5-point unipolar.**

| Value | Label |
|---|---|
| 1 | Not at all important |
| 2 | Slightly important |
| 3 | Moderately important |
| 4 | Very important |
| 5 | Extremely important |

**Question form** — ground it in the activity, not in your product:

> "When you take a ride in a taxi or other hired car, how important is it to you that the driver is
> polite?"

Pattern: *"When you \<do the activity\>, how important is it to you that \<benefit\>?"*

Ask one question per need. Average the responses across respondents to get the need's importance.

---

## The satisfaction scale

**7-point bipolar.**

| Value | Label |
|---|---|
| 1 | Completely dissatisfied |
| 2 | Mostly dissatisfied |
| 3 | Somewhat dissatisfied |
| 4 | Neither satisfied nor dissatisfied |
| 5 | Somewhat satisfied |
| 6 | Mostly satisfied |
| 7 | Completely satisfied |

**Question form** — bound it to a concrete recent period and to what they actually use:

> "How satisfied are you with how polite your driver was during the taxi rides you've taken in the
> past six months?"

Pattern: *"How satisfied are you with \<benefit\> in \<the thing you use today\>, over
\<recent bounded period\>?"*

The bounded period matters. "How satisfied are you generally" invites a summary judgement; "in the
past six months" invites recall of actual events.

---

## Scale design rules

- **Odd number of points for bipolar scales**, so a neutral midpoint exists. Forcing a side produces
  noise, not decisiveness.
- **Upper bound: 11 choices.** More than that overwhelms respondents.
- **Lower bound: 5 choices.** Fewer loses the granularity you need to rank needs against each other.
- **Use the scale the customer finds easiest**, then transform it yourself. Olsen: *"since you can
  easily transform the scores, you should use a scale with customers that is easy for them to
  understand and that doesn't try to ask them for more precision than they can realistically
  provide."* Do not ask a human for a number out of 100.

---

## Normalization

Both formulas require specific input ranges, and neither takes raw 5-point or 7-point responses.
Normalization is a required step, not an optional refinement.

**5-point → 0–10**

| Raw | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **0–10** | 0 | 2.5 | 5 | 7.5 | 10 |
| **0–100** | 0 | 25 | 50 | 75 | 100 |
| **0–1** | 0 | 0.25 | 0.50 | 0.75 | 1.00 |

**7-point → 0–10**

| Raw | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| **0–10** | 0 | 1.67 | 3.33 | 5 | 6.67 | 8.33 | 10 |
| **0–100** | 0 | 16.7 | 33.3 | 50 | 66.7 | 83.3 | 100 |
| **0–1** | 0 | 0.167 | 0.333 | 0.50 | 0.667 | 0.833 | 1.00 |

General form: `normalized = (raw − 1) / (points − 1) × target_max`.

**Then feed the right basis to each formula:**

- **Ulwick** takes the **0–10** columns → output 0–20.
- **Olsen** takes the **0–1** columns → output 0–1.

> Averaging note: average the **raw** responses per need first, then normalize the average. The
> transform is linear, so the order does not change the result — but keeping raw averages in the
> artefact preserves the ability to re-derive everything if a scale choice is later questioned.

---

## Who to ask, and about what

**Prospective customers** — ask importance about the benefit, and satisfaction about **the
workaround they use today**. This is the baseline that matters: your product does not exist, and
the gap you are hunting is the one in their current solution.

**Existing users of a competitor** — ask the *same* importance questions, and satisfaction questions
about that competitor. Olsen: *"comparing satisfaction ratings with competitive products is a good
way to identify where your product is perceived as better or worse."* This feeds Stage 2's
competitive grid directly, so ask it now if you can.

**Your own users**, once you have them — same importance questions, satisfaction about your product.
Tracking these over time is how you notice fit eroding as expectations rise.

Record in the artefact **which population each number came from**. An importance average from
prospective customers and a satisfaction average from your own beta users are not comparable, and
the resulting opportunity score is an artefact of mixing them.

---

## Sample size: quant on qual

You do not need statistical significance to act.

> "If a very large percentage of people you interview rate something high or low, there's a decent
> chance you've uncovered something that will be proven out as you gain more data points. I call
> this technique doing 'quant on qual' — quantitative analysis on qualitative data. While you must
> use it with care, it is an underutilized tool."

Practical guidance:

- **~25 interviews** produces patterns worth acting on.
- **A sample size of zero is an acceptable start.** Score your own hypotheses to force the
  conversation into numbers — but label them `hypothesis` in the artefact, and replace them with
  measured values as they arrive.
- The failure mode is not small samples; it is **unlabelled** samples. A guessed score that later
  reads as a measured one is how a team ends up confidently wrong.

Olsen's caution on over-rigour: *"too many product people have convinced themselves that they need
to prove things beyond a shadow of a doubt. That's just not the case — and often, especially in the
early stages of working on a v1 product, not even possible."*

---

## Worked example

A founder rates one need: importance **3** ("moderately important"), satisfaction **6** ("mostly
satisfied") with the current workaround.

**Normalize**

- Importance 3/5 → `(3−1)/4 × 10` = **5.0** on the 0–10 basis, **0.50** on the 0–1 basis
- Satisfaction 6/7 → `(6−1)/6 × 10` = **8.33** on the 0–10 basis, **0.833** on the 0–1 basis

**Score**

- Ulwick: `5.0 + max(5.0 − 8.33, 0)` = `5.0 + 0` = **5.0** → below 10, **unattractive**
- Olsen: `0.50 × (1 − 0.833)` = `0.50 × 0.167` = **0.085** → very little value left to add

**Read it.** They care only moderately and are already well served. The gap is small and the ceiling
is low. This is an over-served need: building here competes against something that already works,
for customers who were not that bothered. Ladder to a different need, or re-segment to people who
feel this one acutely.

Note how both formulas agree while measuring different things — Ulwick says "not worth pursuing",
Olsen says "almost no headroom". When they disagree, it is usually because importance is high but
satisfaction is also high: Ulwick will say marginal, Olsen will say there is little room left. Trust
the reading, not the ranking, and say which one you used.

---

## Related

- [Opportunity Score Formulas](opportunity-score-formulas.md) — what to do with these numbers
- [Customer Discovery Script](customer-discovery-script.md) — how to get them without leading
- [lean-market-discovery](../SKILL.md)
