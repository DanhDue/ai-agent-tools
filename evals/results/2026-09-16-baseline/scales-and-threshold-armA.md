# Arm A — with skill

**Case**: `scales-and-threshold`
**Run**: 2026-09-16-baseline
**Framing given**: "You are an experienced product advisor helping an early-stage founder validate their market."
**Files read**: `skills/lean-market-discovery/SKILL.md`, `references/importance-satisfaction-survey.md`, `references/opportunity-score-formulas.md`

**Anonymisation applied**: none — the reply contains no skill self-announcement.

**Residual tells, deliberately NOT stripped**: the reply offers to create
`.devtool/product/<slug>/01_problem_space_spec.md` and uses the terms "parking lot", "Stage 2",
"Stage 3" and "Gate 1". The file path is the strongest tell in either run so far. All of it is
substantive — it is an offer to do actual work — and the protocol says to leave substantive content
untouched. Recorded so the verdict can be read with this in mind.

---

Ran the numbers. Short version: Need 1 is a no, and Need 2 doesn't clear the bar — because 10 isn't the bar. There's also one number of yours I can't reconcile. Details below.

---

**Need 1 — "know whether the bus is actually coming, before standing outside in the rain"**

I'm assuming you used the scales I gave you: importance on the 5-point unipolar, satisfaction on the 7-point bipolar. If either of those was a 1–10, tell me and I'll redo it, because the arithmetic changes completely and the answer might too.

Normalize first — neither formula takes raw responses:

- Importance 4/5 → (4−1)/4 × 10 = **7.5** on the 0–10 basis, **0.75** on the 0–1 basis
- Satisfaction 6/7 → (6−1)/6 × 10 = **8.33** on the 0–10 basis, **0.833** on the 0–1 basis

Then both formulas, each on its own scale:

- **Ulwick:** 7.5 + max(7.5 − 8.33, 0) = 7.5 + 0 = **7.5** → below 10, unattractive
- **Olsen:** 0.75 × (1 − 0.833) = **0.125** → almost no headroom

They agree, and they're telling you slightly different things. Ulwick says don't pursue it. Olsen says the rectangle of value still available to the right of that point is tiny. Note also that satisfaction came in *above* importance, so the raw gap is negative — this need isn't underserved, it's over-served. On the quadrant it sits upper-right: important, and already handled.

That's not nothing. Upper-right needs become Kano **must-haves** in Stage 2. You will probably have to ship live location, because its absence will be conspicuous once you're selling a bus app. But nobody switches for a must-have and nobody pays extra for one. It is not a thing to build a company on.

Before you file it away, though, one question I need answered. Satisfaction 6 means "mostly satisfied." You told me these districts expose the GPS feed only to the depot. So parents are mostly satisfied with *something* — what? The WhatsApp group where whoever's at the stop first reports in? The bus just being reliably punctual? The kid texting on arrival? That thing is your competitor in Stage 2 and your satisfaction baseline, and right now I don't know its name. If the 6 came from "the bus is basically always on time in our district," that's a fact about that district's operations, not about the need — and it will not hold in the next district.

---

**Need 2 — the 11, and why it doesn't get you to positioning**

No. 10 is not the bar. 10 is the *floor of the band Ulwick calls unattractive*.

- **> 15** — very attractive, pursue
- **10 – 15** — marginal; admit only with a written rationale, never as the sole basis for passing
- **< 10** — unattractive or over-served, reject

11 sits near the bottom of the marginal band. Gate 1 requires at least one need above 15, and I'm not going to move that for you. A product founded on a need nobody rates above 15 is a product nobody switches for — and switching is the entire ask here, since these parents currently do nothing and pay nothing.

Second problem: **I can't reproduce 11 from the prescribed scales.** With single integer ratings, normalized importance can only be 0 / 2.5 / 5 / 7.5 / 10 and normalized satisfaction only 0 / 1.67 / 3.33 / 5 / 6.67 / 8.33 / 10. Run every combination and the reachable Ulwick scores in that neighbourhood are 10, 11.67, 13.33, 15, 16.67. There is no pair that yields 11. So one of three things happened: it's an average over real respondents (fine — tell me n, and whether these are measured or your own estimates), the raw 1–5 and 1–7 numbers went into the formula un-normalized, or it got rounded off somewhere. Send me the two inputs and the population and I'll recompute. Either way, 11.67 is still marginal, so the conclusion survives — but I want to know which number we're actually holding.

---

**Why the arithmetic is stricter than you're expecting**

Worth knowing before you go back out. A need's Ulwick score can never exceed **twice its importance**, because the gap term is capped at importance itself (satisfaction can't go below zero). So importance alone sets the ceiling:

| Raw importance | Normalized | Ceiling at satisfaction 0 | Clears >15? |
|---|---|---|---|
| 5/5 Extremely important | 10.0 | 20.0 | Yes |
| 4/5 Very important | 7.5 | 15.0 | **No** — 15.0 isn't *above* 15 |
| 3/5 Moderately important | 5.0 | 10.0 | No |

With a single integer rating, **only a 5/5 "extremely important" can ever pass.** A need rated "very important" and served by literally nothing lands on exactly 15.0 and fails.

Which makes Need 2 the interesting one. "My kid got into someone's car instead of the bus" ought to be an unhesitating 5/5 for a parent of a seven-year-old. If it isn't rating 5/5, one of these is true: you asked it in a way that invited a considered answer instead of a gut one; the parents you asked are already covered by something (the driver knows every kid by name, the school does a roll call and calls you); or the need is written one rung too low on the ladder.

My money is on the ladder. "Got on the bus" is an observable *event*, not a benefit. Ask "why is that important to you?" and keep going — my guess is you land somewhere near *"I know where my child is during the part of the day I can't see them."* That's the rung people rate 5/5, and it's also a much bigger product than a boarding alert.

---

**About the two weeks**

I'm not asking for two more weeks of the same interviews. But look again at that ceiling table, because it changes what the interviews are *for*: with one person picking one integer, you essentially cannot clear 15 by arithmetic. Averaging across respondents is the only thing that produces fractional importance — 4.2 average → ceiling 16.0, 4.5 → 17.5. More conversations aren't diligence theatre here. They're the only mechanism that can pass you.

Days, not weeks:

1. **Ladder Need 2** with 8–10 parents. No rating, no survey — just "why is that important to you?" until it stops producing new answers. You're looking for the rung above "got on the bus."
2. **Re-rate whatever comes out on top**, plus Need 1, with ~25 parents. Ask satisfaction against the workaround *by name*, over a bounded period ("in the past school term"), not in general.
3. **Come back with 3–5 needs.** You have 2. Gate 1 wants 3–5, and two needs means we're ranking a field of two.

One more thing, possibly bigger than either need. You have a user/buyer split you haven't named. The parent is the user. The district owns the GPS feed and has **already decided** not to expose it to parents — someone made that call, has a reason, and stands between you and your product. Whether you're selling to parents over the district's head, selling to the district, or asking the district for a feed changes the segment itself, not just the go-to-market. Worth an hour with one district transport manager this week.

Also, parking two things you said so they don't evaporate: "live location" and "alert when the kid boards" are both solution space — they're shapes, not needs, and they belong in the parking lot until Stage 3 drains it. Give me a product slug and I'll open `.devtool/product/<slug>/01_problem_space_spec.md` and write them in now, along with everything above.

**Gate 1: not passed.** Blockers — no need above 15; only 2 needs; Need 1's workaround unnamed; Need 2's inputs and population unverified; user vs buyer not split.
