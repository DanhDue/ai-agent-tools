# Source Fidelity Review — Lean Product Lifecycle Suite

> **Epic**: `lean_product_suite`
> **Date**: 2026-09-16
> **Purpose**: Re-evaluate every claim in the prior analysis against the primary source,
> *The Lean Product Playbook* (Dan Olsen, Wiley 2015), before implementing the skills.
> **Method**: Full text extracted from `docs/books/1. The Lean Product Playbook … (Olsen, Dan)2015.pdf`
> and read against the four derived documents plus the epic's own design spec, HLD, and BDD scenarios.

---

## 0. Why this review exists

Every artefact in this epic — the design spec, the HLD, the BDD scenarios, all five task
files — was derived from three intermediate documents in `docs/books/`, not from the book.
Those intermediates are themselves LLM-produced summaries. The errors below propagated
unchecked through four layers, and several of them would be **baked into shipped skills that
then teach the errors to every future agent and founder using this kit**.

Corrections are grouped by severity. Each carries the book's own words so the fix is
verifiable without re-reading the PDF.

---

## 1. Critical corrections (change behaviour; would produce wrong advice)

### C1 — Guardrail 1 misstates Olsen: the rule is *separate and alternate*, not *forbid*

**Prior claim** (design spec §4.1, HLD, `lean-product-roadmap.md` Guardrail 1):
> "The agent MUST reject any discussion of tech stacks, database schemas, UI wireframes, or
> detailed mechanics until Problem Space … is signed off at Gate 1."

**The book** (Chapter 2, *Problem Space versus Solution Space*):
> "…solution space discussions with customers is much more fruitful than trying to explicitly
> discuss the problem space with them. The feedback you gather in the solution space actually
> helps you test and improve your problem space hypotheses. **The best problem space learning
> often comes from feedback you receive from customers on the solution space artifacts you have
> created.** … Keeping problem space and solution space separate **and alternating between them**
> as you iteratively test and improve your hypotheses is the best way to achieve product-market fit."

**Why it matters.** The Lean Product Process *deliberately enters* solution space at Step 4
(MVP feature set), Step 5 (MVP prototype) and Step 6 (test). A guardrail that forbids solution
space "until Gate 1" is not a hardened version of Olsen — it contradicts him. In practice it
makes the skill refuse legitimate work, which is the fastest route to a user disabling it.

**Corrected rule.** A solution-space statement is never rejected. It is **captured, converted
to the problem-space need it implies, parked in a Solution Space Parking Lot, and returned to
at Step 4**. The failure mode being guarded against is a solution-space idea *substituting for*
a problem-space hypothesis — not the idea existing.

---

### C2 — Gate 3's "MVP = ROI cells 1–3 only" produces a non-viable MVP

**Prior claim** (design spec §5.3 Gate 3 criteria, task 4, BDD 2.3):
> "MVP features strictly confined to Cells 1–3 of the ROI grid."

**The book** (Chapter 6, *Deciding on Your MVP Candidate*):
> "You can sort your list of feature chunks by estimated ROI to create a rank-ordered list …
> However, **sometimes you can't just follow the strict rank order to create a complete MVP; you
> might need to skip down to include important features.** … To start with, your MVP candidate
> needs to have **all the must-haves you've identified**. After that, you should focus on the main
> performance benefit you're planning to use to beat the competition. You should select the set of
> feature chunks for this benefit that you believe will provide enough for customers to see the
> difference… You should include your **top delighter**… The goal is to make sure that your MVP
> candidate includes *something* that customers find superior to others' products and, ideally, unique."

**Why it matters.** A must-have is table stakes *regardless of its ROI rank*. Under the "cells 1–3
only" rule, a high-effort must-have is cut and the MVP is not viable — the exact failure Olsen
warns about. ROI ranking orders the work; it does not decide MVP membership.

**Corrected rule.** MVP composition is **benefit-driven, ROI-ordered**:
1. **All** identified must-haves (mandatory, ROI rank irrelevant).
2. Enough chunks of the **one** performance benefit you intend to win on that customers can see
   the difference.
3. Your **top delighter** — optional only if the performance advantage is very large.
4. ROI rank orders chunks *within* each benefit and sequences post-v1 versions.

---

### C3 — The Product-Market Fit Pyramid has five layers, not six

**Prior claim** (design spec §3.1/§4, HLD Goal 1, task 1, `lean-product-agent-skill.md` §1.2.2):
> "6-layer PMF Pyramid: Target Customer → Underserved Needs → Value Proposition → MVP Feature
> Set → MVP Prototype → User Testing."

**The book** (Introduction, Chapter 1, Figure 2.1 — verbatim from the figure):
```
Product:   Solution Space  →  UX
                              Feature Set
           ------------------ Product-Market Fit ------------------
Market:    Problem Space   →  Value Proposition
                              Underserved Needs
                              Target Customer
```
> "The framework, which I call the Product-Market Fit Pyramid, breaks product-market fit down into
> **five** key components … The Lean Product Process consists of **six steps**."

**Why it matters.** Two different objects were merged into one. "MVP Prototype" and "Test with
customers" are *process steps*, not *pyramid layers*; **UX** — the actual top layer — vanished
entirely from the epic's model. A skill that routes on a six-layer pyramid cannot express
"the problem is in the UX layer, not the feature set", which is precisely the diagnosis the
Tectonic Plates protocol exists to make.

**Corrected rule.** The suite carries **both** models explicitly: a 5-layer **Pyramid** (the
hypothesis hierarchy, used for diagnosis and rollback) and a 6-step **Process** (the workflow,
used for routing). The interface between problem and solution space sits **between Value
Proposition and Feature Set**.

---

### C4 — Gate 1's `OS ≥ 10` threshold admits opportunities Olsen calls unattractive

**Prior claim** (design spec §5.1, BDD 2.1): "$OS \ge 10$ confirmed for top gaps."

**The book** (Chapter 4, *Jobs to Be Done*):
> "Using 0 to 10 for each rating, the resulting score can vary from 0 … to 20 … **Ulwick considers
> opportunities with scores greater than 15 to be very attractive, and those below 10 to be
> unattractive.**"

**Why it matters.** `OS ≥ 10` is the floor of the *unattractive* band, not a bar for a top
opportunity. The gate as specified passes almost anything.

**Corrected thresholds** (Ulwick scale, 0–20):

| Opportunity Score | Verdict | Gate 1 action |
|---|---|---|
| `> 15` | Very attractive | Certify as a Top Priority Gap |
| `10 – 15` | Moderate | Flag as marginal; allow at most one, and only with a stated rationale |
| `< 10` | Unattractive / over-served | Reject; ladder again or re-segment |

Gate 1 requires **at least one need scoring > 15**.

---

### C5 — Importance and Satisfaction are measured on *different* scales, then normalized

**Prior claim** (all derived docs): "Importance (1–10) and Satisfaction (1–10)."

**The book** (Chapter 4, *Measuring Importance and Satisfaction*):
- **Importance — 5-point unipolar**: 1 Not at all important · 2 Slightly · 3 Moderately ·
  4 Very · 5 Extremely important.
- **Satisfaction — 7-point bipolar**: 1 Completely dissatisfied → 4 Neither → 7 Completely satisfied.
- Rationale, in Olsen's words: *"It's usually best to measure satisfaction using a bipolar scale;
  since people can be satisfied or dissatisfied, a negative score makes sense. In contrast,
  importance is just a matter of degree without any negative value and therefore better measured
  with a unipolar scale."*
- Scale design limits: *"Using more than 11 choices will overwhelm customers, while using fewer
  than 5 won't achieve enough granularity."* Bipolar scales take an **odd** number of choices.
- **Normalization is an explicit step**: *"you could map the values of a 5-point scale to 0, 25,
  50, 75, and 100. Or to 0, 2.5, 5, 7.5, and 10. Likewise, you could map the values of a 7-point
  scale to 0, 16.7, 33.3, 50, 66.7, 83.3, and 100."*

**Why it matters.** Both opportunity formulas are scale-sensitive, and they do not take the same
scale (see C6). Feeding raw 5-point and 7-point responses into either one silently produces
meaningless numbers. The derived docs skip measurement design entirely and jump to the formula.

---

### C6 — The two opportunity formulas are not interchangeable

| | Dan Olsen — *Opportunity to Add Value* | Anthony Ulwick — *Opportunity Score* |
|---|---|---|
| Formula | `Importance × (1 − Satisfaction)` | `Importance + max(Importance − Satisfaction, 0)` |
| Required scale | **0–1 fractions** (or 0–100%) | **0–10 integers** |
| Output range | 0 – 1 | 0 – 20 |
| Thresholds | Relative — compare scores; the book's worked example treats 0.37 as the best of 13 | Absolute — `>15` attractive, `<10` unattractive |
| Reading | Area of the rectangle to the right of the point: value still addable | Gap, floored at zero, with importance as tie-breaker |

Olsen's worked examples: Opportunity A `0.7 × (1 − 0.7) = 0.21`; Opportunity B
`0.9 × (1 − 0.3) = 0.63`; Feature X `0.82 × (1 − 0.55) = 0.37`.

Olsen also presents **plain gap analysis** (`Importance − Satisfaction`) and explains why he
rejects it as a primary tool: *"its biggest shortcoming is that it treats all gaps of equal size
the same"* — a gap of 5 on an importance-10 need is not equal to a gap of 5 on an importance-6
need. Ulwick's `+ Importance` term exists precisely to break that tie.

**Corrected rule.** The skill computes **both**, on their own correct scales, from one normalized
data set — and never reports one formula's number against the other's threshold.

---

## 2. Significant corrections (missing method; not wrong, but incomplete)

### C7 — Numeric ROI is the primary method; the 3×3 grid is the explicitly-labelled fallback

**The book** (Chapter 6, *Using Return on Investment to Prioritize* → *Approximating ROI*):
> "`ROI = Return / Investment` … the investment is usually the time that your development
> resources spend working on it, which you generally measure in units such as developer-weeks …
> You need to use a **ratio scale** … You can sort your list of feature chunks by estimated ROI to
> create a rank-ordered list."
>
> Then, separately: *"I've explained how to think about ROI rigorously, but you can **also** use
> this prioritization tool in a **less rigorous** manner. **If you are struggling with creating
> numerical estimates** of customer value or development effort, you can score each feature idea
> high, medium, or low … This will create a three-by-three grid."*

The prior analysis promoted the fallback to *the* method and dropped numeric ROI entirely.
The 3×3 grid's nine buckets are rank-ordered by ROI with square 1 = highest value / lowest effort;
the cell numbering used in this epic reads Figure 6.2 and is retained.

**Also missing — Olsen's tie-break rule:** *"if you have two feature ideas with the same ROI, it's
best to prioritize the smaller scope idea higher, because it takes less time to implement."*

**Corrected rule.** Attempt numeric ROI (customer value 0–10 on a ratio scale ÷ developer-weeks)
first. Fall back to the 3×3 grid only when the founder cannot produce estimates, and say so
explicitly when doing it.

---

### C8 — The benefit × feature-chunk grid is the Step 4 deliverable, and it is missing

**The book** (Chapter 6, Figures 6.3 and 6.4): after chunking and prioritizing, you build a grid
whose **rows are the benefits from your value proposition** (labelled `M1`, `M2` for must-haves,
`P1`…`P3` for performance benefits, `D1`, `D2` for delighters) and whose **cells are that benefit's
feature chunks in priority order**, highest priority leftmost. The **leftmost column becomes v1**;
chunks pushed right become v1.1, v1.2. Olsen: *"I don't recommend that you plan more than one or
two minor versions ahead."*

This grid is the physical link between Gate 2 and Gate 3 — it is how the value proposition becomes
a backlog — and it does not appear anywhere in the epic's `mvp-backlog.template.md` specification.
It must be the template's centrepiece.

---

### C9 — "Cupcake MVP" is not Olsen's, and the correct attribution is specific

**Prior claim**: "Cupcake MVP (Vertical slice)"; *"MVP is NOT a dry cake without frosting or a
single layer of a wedding cake."*

**The book** (Chapter 7, Figure 7.1, *Building an MVP*): the word *cupcake* does not occur in the
book. The figure is a **four-layer pyramid of product attributes — functional, reliable, usable,
delightful** — contrasting the wrong reading of MVP (only the bottom layer) with the right one
(narrow but complete through all four). Olsen: *"I've adapted this figure from one created by
talented UX designer **Jussi Pasanen** of Volkside, who gives his acknowledgements to **Aarron
Walter, Ben Tollady, and Ben Rowe**."*

The cupcake / birthday cake / wedding cake metaphor is **Brandon Schauer's**, and conflating it
with Olsen's figure misattributes both. Note also this material sits in **Chapter 7 (Step 5)**,
not Chapter 6 — it constrains how you *build* the MVP, and therefore bounds what Step 4 may scope.

**Corrected naming.** `vertical-slice-guide.md` teaches the **MVP Attribute Pyramid
(functional / reliable / usable / delightful)** with correct attribution, and may mention the
cupcake metaphor only as a *related, differently-sourced* mnemonic.

---

### C10 — "Competitors" includes non-consumption and workarounds

**The book** (Chapter 5): *"'Competitors' doesn't just mean direct competitors: in the unlikely
case that you don't have any direct competitors, there should still be alternative solutions that
customers are currently using to meet their needs (remember how pen and paper was an alternative
to TurboTax)."*

The prior spec says "List of 2–3 key competitors", which lets a founder answer "we have no
competitors" and skip Stage 2's core exercise. The skill must force the current workaround into
the grid as a column.

---

### C11 — The value proposition grid permits being deliberately *worse*

**The book** (Table 5.5, a completed value proposition): the author's own product scores
**Medium** on performance benefit 1, **Low** on performance benefit 2, and **High** on performance
benefit 3 — the one it chooses to win. From the Google case: Google won *"because they were best
at the benefit that mattered most **and had comparable or better performance on the other
dimensions**."*

Two rules the derived docs lose: you may deliberately place **Low** on a benefit you are not
competing on, but you must not be low on *everything else* — parity is required on the
dimensions you are not winning. This is the concrete mechanism behind "strategy is saying no",
and without it the agent will try to claim High everywhere.

---

## 3. Minor corrections

- **C12** — `lean-product-roadmap.md` Step 6 states *"5 customers per wave (enough to find 85% of
  UX problems)"*. Olsen says *"testing in waves of **five to eight** customers"*; the 85%/5-users
  figure is **Nielsen's**, not Olsen's, and should not be attributed to this book. (Phase 2 scope.)
- **C13** — `lean-product-agent-skill.md` §2 Step 2 presents `Importance × (1 − Satisfaction)` as
  primary with Ulwick's as an "alternative". Olsen presents them as complementary views; see C6.
- **C14** — The semi-quantitative wrap-up ratings Olsen recommends at the end of each user test
  (0–10 on *how valuable*, *how likely to use*, *how easy to use*, tracked wave over wave) are
  absent. Phase 2 scope — noted so `lean-ux-testing` inherits it.

---

## 4. What the prior analysis got right

Confirmed against the source and carried forward unchanged:

- **Kano model** — three categories (must-have, performance, delighter); *"Yesterday's delighters
  become today's performance features and tomorrow's must-haves"*; the hierarchy in which
  delighters don't matter until you are competitive on performance.
- **Customer benefit laddering** — *"keep asking them, 'Why is that important to you?' until it
  doesn't lead to any new answers"*; Olsen himself notes the similarity to the Five Whys.
- **Needs-based segmentation** preferred over demographic/psychographic/behavioral alone.
- **Personas** as hypotheses about the target customer, crediting **Alan Cooper**.
- **Sean Ellis PMF metric** — ≥ 40% "very disappointed" indicates product-market fit.
- **Problem space is the customer's, solution space is the company's**; value proposition is the
  problem-space layer over which you have the most control.
- **Plan no more than one or two minor versions ahead.**
- **Feature chunking** — *"I deliberately use the term feature chunk instead of feature to remind
  readers that you should not be working with items that are large in scope."*
- **Quant on qual** — meaningful patterns emerge from ~25 interviews; *"a sample size of zero is okay."*
- The **hub-and-spoke micro-skill decomposition** itself: a sound architectural response to
  context-window hygiene, and orthogonal to the book.

---

## 5. Net effect on the epic

| Artefact | Change required |
|---|---|
| Design spec | Correct §3, §4 Guardrails 1/4/5, §5.1 Gate 1 threshold, §5.3 Gate 3 criteria |
| `lean_product_suite.en.md` / `.vi.md` | Correct "6-layer pyramid"; restate Gate criteria |
| `bdd_scenarios.md` | Rewrite 2.1 (threshold), 2.3 (MVP composition), 3.1 (Guardrail 1 behaviour) |
| `task_1` | 5-layer pyramid + 6-step process as distinct models; rewrite Guardrail 1 |
| `task_2` | Add survey measurement design + normalization; correct thresholds |
| `task_3` | Add workaround-as-competitor; add deliberate-Low / parity rule |
| `task_4` | Numeric ROI primary; benefit × chunk grid; MVP composition rule; correct attribution |
| `task_5` | Add a source-fidelity regression check to verification |
| **new `task_0`** | Correct the three `docs/books/` intermediates so the errors cannot re-propagate |

---

*Every quotation above was extracted from the PDF in `docs/books/` during this review. Where the
book's text is reproduced, spacing has been restored from the PDF's kerned text layer; wording,
numbers and emphasis are the author's.*
