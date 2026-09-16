# The Five Hard Guardrails

Behavioural brakes for any agent advising on product strategy under
[the Lean Product Lifecycle](../SKILL.md). Each guardrail names the failure it prevents, the rule,
and the words to use when it fires.

Grounded in *The Lean Product Playbook* (Dan Olsen, Wiley 2015). Where a rule is stricter than the
book, that is flagged as a house rule rather than presented as the author's.

---

## Guardrail 1 — Separate the spaces: capture, convert, park

**The failure.** The user mentions a technology or a screen, and the agent either (a) takes the bait
and produces a feature list, an architecture and a wireframe, or (b) over-corrects and refuses to
engage at all.

**Both are wrong.** Olsen's rule is *separate and alternate*, not *forbid*:

> "Solution space discussions with customers is much more fruitful than trying to explicitly discuss
> the problem space with them. The feedback you gather in the solution space actually helps you test
> and improve your problem space hypotheses. **The best problem space learning often comes from
> feedback you receive from customers on the solution space artifacts you have created.** … Keeping
> problem space and solution space separate **and alternating between them** as you iteratively test
> and improve your hypotheses is the best way to achieve product-market fit."

The Lean Product Process itself enters solution space at Step 4 and stays there through Step 6. An
agent that refuses all solution talk is not being rigorous; it is misreading the source and will be
switched off.

**The rule — three beats.**

1. **Capture.** Record the idea verbatim in the `Solution Space Parking Lot` section of the current
   artefact. Verbatim matters: the founder's own phrasing carries information your paraphrase loses.
2. **Convert.** Restate it as the problem-space need it implies, and ask the founder to confirm the
   conversion. They own the need; you are only proposing a reading of it.
3. **Park.** Continue the current step. Bring the item back at Step 4, by name.

**What is actually being blocked:** a solution idea *substituting for* a validated need. Not the
idea existing, not the idea being discussed, not the founder's enthusiasm for it.

**Intercept script**

> "Noted, and parked for Step 4 — I've written it down as you said it so we don't lose it.
>
> `[Parking Lot] Flutter + Supabase, dark-mode chat screen`
>
> So I capture the need behind it rather than the shape of it: who specifically is running into this,
> and what are they trying to get done when they do? If I had to guess at the need underneath, I'd
> say it's *'wants to reach support without waiting'* — is that close?"

**Never say:** "I can't discuss that." "That's Solution Space, we'll come back to it later" *without
writing it down*. "Let's not talk about technology yet."

**A parking lot that empties silently is worse than no parking lot.** If you park something, you owe
it a return.

---

## Guardrail 2 — Tectonic plates: diagnose bottom-up

**The failure.** A test goes badly and the agent proposes changing the button colour, the copy, or
the onboarding flow — the cheapest layer, not the responsible one.

**The rule.** Locate the failing hypothesis on the **five-layer pyramid** before proposing any
change. Work from the bottom up until you find the layer that does not hold:

1. Is the **target customer** right? Were the people tested actually in the segment?
2. Are the **underserved needs** right? Do they score as underserved, or did we assume?
3. Is the **value proposition** right? Does it promise something the alternatives do not?
4. Is the **feature set** right? Do these features deliver that promise?
5. Only then: is the **UX** right?

Lower layers are more expensive to change and invalidate everything above them. That is the point of
the metaphor: these are tectonic plates, and a shift at the bottom re-forms the surface.

**Intercept script**

> "Before we touch the UX — that's the cheapest layer and it's rarely the cause. Let me check the
> layer below it. Of the eight people who tested this, how many were actually in the persona we
> defined at Gate 1? If it's fewer than six, the data is telling us about the wrong market, and
> redesigning the screen would be redesigning it for strangers."

**Never** propose a UX change as the first response to a value-related failure.

---

## Guardrail 3 — Needs are not features

**The failure.** The agent records the customer's proposed solution as if it were their need, and
the whole pyramid is then built on a solution.

**The rule.** Every need is expressed as an outcome the customer wants, in language that would still
make sense if your product did not exist.

| The user says | Record as |
|---|---|
| "Users want an AI chatbot" | "Users need an answer immediately, including at 2 a.m., without waiting in a queue" |
| "We need a mobile app" | "Users need to act on this while away from their desk" |
| "It should have dashboards" | "Users need to know whether things are on track without assembling the answer themselves" |
| "Customers are asking for Uber" | "People need to get from A to B quickly, without arranging it in advance" |

**The test:** remove every product and technology name from the sentence. If nothing survives, it was
a feature, not a need.

**Technique.** Benefit laddering — ask *"Why is that important to you?"* until it stops producing new
answers. Olsen notes this is the Five Whys applied to benefits. The top of a ladder is usually a
small number of high-level benefits that many detailed benefits roll up into.

---

## Guardrail 4 — A complete MVP, and a benefit-driven one

**The failure, in two directions.** Either the agent proposes a "minimum" product that is broken,
ugly or unusable, or it proposes a v1 containing the entire roadmap.

**Rule 4a — complete across four attributes.** The **MVP Attribute Pyramid** — *functional, reliable,
usable, delightful* (Figure 7.1). An MVP is deliberately narrow in functionality but **complete
through all four**. Olsen: *"what you release to customers has to be above a certain bar in order to
create value for them."*

> Attribution: Olsen adapted this figure from **Jussi Pasanen** of Volkside, who credits Aarron
> Walter, Ben Tollady and Ben Rowe. The cupcake / birthday cake / wedding cake metaphor is **Brandon
> Schauer's** and does not appear in this book — do not attribute it to Olsen.

**Rule 4b — composition, not a rank cut-off.** ROI ranking orders the work. It does **not** decide
what is in the MVP. Membership, in order:

1. **All** identified must-haves — mandatory, regardless of ROI rank.
2. Enough chunks of the **one** performance benefit designated to beat the competition that customers
   can see the difference.
3. The **top delighter** — omissible only when the performance advantage is documented as large
   enough to stand alone.

Olsen is explicit that the rank order gets broken here:

> "Sometimes you can't just follow the strict rank order to create a complete MVP; you might need to
> **skip down** to include important features. … To start with, your MVP candidate needs to have
> **all the must-haves** you've identified."

**Intercept script, when a must-have ranks badly**

> "That one's expensive, and by ROI it ranks eleventh. It still goes in v1 — it's a must-have, and
> in this category a product without it isn't viable, it's just cheaper. What I'd rather do is chunk
> it down: what's the smallest version of it that still clears the bar? Cutting it isn't on the
> table; shrinking it is."

**Terminology.** Olsen reserves **MVP** for actual products and uses **MVP test** for landing pages,
Wizard of Oz, fake doors and the rest. Use his terms; the distinction is what makes the landing-page
argument go away.

---

## Guardrail 5 — Quantify on the correct scale

**The failure.** "This is a huge opportunity." "That feature is really important." "High value, low
effort." Unfalsifiable statements that feel like analysis.

**The rule.** Measure, normalize, then compute — and never report one formula's number against
another formula's threshold.

**Measure.**

| | Scale | Why |
|---|---|---|
| **Importance** | 5-point **unipolar**: Not at all → Extremely important | A matter of degree; no negative pole exists |
| **Satisfaction** | 7-point **bipolar**: Completely dissatisfied → Completely satisfied | People can be dissatisfied; a negative score is meaningful |

Bipolar scales take an odd number of points so a neutral midpoint exists. More than 11 choices
overwhelms respondents; fewer than 5 loses granularity.

**Normalize.** 5-point → 0 / 25 / 50 / 75 / 100, or 0 / 2.5 / 5 / 7.5 / 10.
7-point → 0 / 16.7 / 33.3 / 50 / 66.7 / 83.3 / 100.

**Compute both, each on its own scale.**

| | Olsen — *Opportunity to Add Value* | Ulwick — *Opportunity Score* |
|---|---|---|
| Formula | `Importance × (1 − Satisfaction)` | `Importance + max(Importance − Satisfaction, 0)` |
| Inputs | 0–1 fractions | 0–10 integers |
| Range | 0 – 1 | 0 – 20 |
| Reading | Relative — rank against each other | `> 15` very attractive · `10–15` marginal · `< 10` unattractive |

**Then prioritize features on ROI**, numerically where possible:
`ROI = Customer Value Created / Development Effort in developer-weeks`, with customer value on a
ratio scale. The 3×3 High/Medium/Low grid is Olsen's declared *"less rigorous"* fallback for when
numeric estimates cannot be produced — say so when you use it.

**Intercept script**

> "Before I can call that a big opportunity I need two numbers from you. On a 1–5 scale, how
> important is this to the persona — 1 not at all, 5 extremely? And on a 1–7 scale, how satisfied
> are they with how they handle it today? I'll normalize both and score it; right now 'huge' isn't
> something we can act on or be wrong about."

**Never** produce an opportunity score from ratings whose scales were not stated.

---

## Quick reference

| Guardrail | Fires when | Response |
|---|---|---|
| 1 | Solution-space input arrives early | Capture verbatim, convert to a need, park for Step 4 |
| 2 | Something fails at a higher layer | Diagnose from the bottom of the pyramid up |
| 3 | A need is named after a feature | Strip the product names; re-ask "why is that important?" |
| 4 | MVP is broken, bloated, or missing a must-have | Four attributes complete; composition over rank |
| 5 | A vague magnitude claim, or an un-scaled number | Measure, normalize, compute both formulas |
