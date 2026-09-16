# Arm A — with skill

**Case**: `must-have-rank-23`
**Run**: 2026-09-16-baseline
**Framing given**: "You are an experienced product advisor helping an early-stage founder scope their MVP."
**Files read**: `skills/lean-mvp-scoping/SKILL.md`, `references/roi-prioritization.md`, `references/mvp-candidate-grid.md` (plus a skim of `references/mvp-attribute-pyramid.md`)

**Anonymisation applied**: the subagent appended a meta-section titled "Note on the two pressure
tests in the prompt" addressed to the dispatcher, not the founder. Removed — it is not part of the
reply and it names the skill directly.

**Residual tell, deliberately NOT stripped**: the reply uses the terms "composition rule" and
"Stage 1/Stage 2 parking lot", which are skill vocabulary. Both carry substance, and the protocol
says to leave substantive content untouched. Perfect anonymisation is not achievable when one arm
has richer methodology; the randomised label assignment is what guards against systematic bias, not
the scrubbing. Noted so the verdict can be read with this in mind.

---

No — and I want to push back hard on this one, because the number you're reading is telling you something different from what you think it is.

## M3A is a must-have. Must-haves don't get cut on ROI.

ROI rank orders the work. It does not decide what's in v1. The composition rule is separate and it comes first: **all the must-haves, regardless of rank**, then enough of the designated performance benefit that customers can see the difference, then the top delighter.

You had M3 as a must-have at Gate 2. A must-have is what the category requires. A scheduler for veterinary clinics that can't produce the board's record format isn't a cheaper scheduler — it's a scheduler that a vet clinic can't use as its system of record. That's a different product, sold to a different buyer, at a different price.

"Rank 23 of 25, ROI 0.22, cut it" is exactly the rule that cuts high-effort must-haves and produces a product that fails in the market for a reason the team later misdiagnoses as poor execution.

## The 2/10 is a scoring artifact, not a fact about the feature

This is the part I'd want you to look at before anything else.

If you scored customer value as *how much this delights someone*, then every must-have floors at 1 or 2 out of 10 **by construction** — that's the Kano definition of a must-have. No satisfaction when present, severe dissatisfaction when absent. Score that way and your entire ranking tilts systematically away from the things the product cannot ship without.

Score it as **value destroyed by absence, not delight created by presence.** On that basis, what's the score for "the clinic cannot demonstrate compliance to its licensing board"? It isn't 2.

Re-score all three must-haves on that basis and send me the new list. I'd bet M3A doesn't stay at rank 23, and I'd also bet M1 and M2 move. That matters independently of this decision, because a distorted scale is distorting the other 22 rows too.

And the tell is right there in your own data: if M1 (booking and calendar — the literal product) and M3A are both scoring near the bottom, the scale is measuring delight. If M1 scored high and M3A scored 2, that's worth a closer look. Which is it?

## "Nobody mentioned it unprompted" is confirming evidence, not disconfirming

I know it doesn't feel that way. But nobody mentions must-haves unprompted — that's the definition. Nobody in your interviews said "I'd want the calendar to save the appointment after I click save," either. Must-haves are invisible until they're absent, which is why you can't discover them by asking what people want, and why "it only comes up when the board shows up" is precisely what a must-have looks like from inside an interview transcript.

The question that would actually test it isn't "did they mention it." It's: **does their current system do this, and would they move off it onto something that doesn't?** If every incumbent PIMS handles board export and clinics assume any system of record does, it's table stakes and the interview silence is just the Kano effect. Ask five customers that directly. It's a two-day question and it's load-bearing for a 9-week decision.

## Your manual fallback is the right instinct — applied one step wrong

"We'll export it by hand, it's a day per clinic" is genuinely good thinking. It's the standard move for an expensive chunk: find the manual version, deliver the outcome with a human, spend a fraction of the engineering. That's how you move an expensive idea *left* on the effort axis.

But you've applied it as a reason to **cut** the chunk, when it's a reason to **shrink** it. Those produce very different v1s, and the difference is one thing:

**You cannot hand-export data you never captured.**

If M2's record model doesn't capture the fields the board format requires — and board formats are usually specific about things like drug lot numbers, controlled-substance entries, dosage units, the identity of the administering vet, timestamps, signature attestations — then no amount of manual work in month two produces a valid export. You'd be reconstructing records that don't exist. That's not a day per clinic; that's an unwinnable conversation with a customer during their audit, and in a market of small independent clinics who all talk to each other, that's your entire reference base.

So the split I'd actually make:

| | What it is | Where | Rough |
|---|---|---|---|
| **M3A1** | Capture every board-required field in the record model, validated at entry | **v1** | small |
| **M3A2** | Flat export of those fields for a date range (CSV or similar) | **v1** | small |
| **M3A3** | The board-format renderer, layout, validation, submission workflow | v1.1 | the rest |

v1 ships with the data conformant and extractable. You produce the formatted document by hand for the first audits — which now genuinely *is* about a day, because the data is all there and correctly shaped. M3A3 lands in v1.1 on revenue, exactly as you wanted.

That's not cutting the must-have. It's the smallest version that clears the bar, which is the only legitimate move when a must-have is expensive.

**And sell it that way, out loud.** The contract commits to the outcome — "your records will satisfy a board audit" — not the mechanism. Concierge delivery is honest; silently shipping without the capability is not.

## Now go after the 9 weeks

Before you accept 9 dev-weeks as fixed, I want the breakdown. Nine weeks for an export is usually a report builder in disguise. Specifically:

- Is it one state's format, or did someone scope a multi-state format engine? You have one state. Build one state.
- Is there a PDF/print pipeline in there? What if v1 emits the data and a human does the layout?
- Is there a submission or e-filing integration? Boards generally accept a document.
- Is it real-time, or could it be generated on demand and take thirty seconds?
- Which parts of it would a clinic notice were missing during an actual audit?

My guess is M3A1 + M3A2 is 2 to 3 dev-weeks, and the other 6 to 7 is format rendering and edge cases that belong in v1.1. If that's right, you free 6 weeks for P2 instead of 9, you keep the must-have, and you don't bet the company on a compliance gap.

## The harder problem your numbers are pointing at

Check my arithmetic, because this reframes the whole question:

14 calendar weeks × 2 engineers = 28 developer-weeks gross. Take out ramp, meetings, deployment, and the bugs you haven't met yet, and you're at maybe 20 to 22. And you can't ship at week 14 with zero cash — you need v1 in clinics with enough runway left to sell against it and raise, so you need to be live around week 9 or 10. Real feature capacity is closer to **16 to 18 developer-weeks.**

So M3A at 9 weeks isn't a quarter of your runway. It's roughly *half your buildable capacity*. Which makes shrinking it more urgent, not cutting it more justified.

But it also means the real problem isn't M3A. It's that 25 chunks do not fit in 17 developer-weeks, and no single cut fixes that. If v1 still doesn't fit after every must-have has been chunked to its smallest viable version, the failure is upstream at Gate 2 — the value proposition promises too much. The fix is fewer benefits and more explicit non-goals, not a v1 that under-delivers on the promise you've already made.

There is one honest escape hatch, and I'll name it so you don't feel cornered: **if M3 is not actually a must-have, that's a Gate 2 error, and we fix it at Gate 2.** If clinics keep their medical records in a separate PIMS and only want scheduling from you, then board export was never yours to build and M3 shouldn't be on the must-have list at all. But that's a different product with a different boundary, and it changes your positioning, your pricing and your competitive set. What it is not is a quiet v1 cut with a manual promise attached.

Answer the five-customer question above and we'll know which world we're in.

## On the roadmap for the deck

I'll build you v1, v1.1 and v1.2. I won't build v2.0, and I'd ask you not to put one in the deck.

Not on principle — for a specific reason. You're about to show v1 to customers for the first time. Some of your hypotheses are wrong; you just don't know which yet. You may find the winning benefit isn't P2 at all. A v2.0 column written before any customer has touched v1 is a commitment made in the absence of evidence, and it's *harder to abandon because it's written down.* It'll get quoted back to you — by your own team in month four, and by the investor who wrote it in their notes, when you've learned something that makes it wrong.

What actually reads as sophistication to a seed investor isn't a four-column roadmap. It's a founder who can say: "Here's v1. Here are the three hypotheses it tests. Here's what we do if each one comes back false. We stop planning at v1.2 on purpose, because planning past the first customer contact is theater." That's a much stronger five minutes than a Gantt chart, and it inoculates you against the "how do you know?" question rather than inviting it.

If the deck template demands a longer horizon, give it a **thesis** rather than a version list — where this goes if the P2 bet lands, what the wedge into the broader practice-management stack looks like. Direction, explicitly labeled as direction. Not dated releases.

Here's the grid shape. I need your chunk list to fill it properly:

| Benefit | **v1** | v1.1 | v1.2 |
|---|---|---|---|
| M1 — booking and calendar | `M1A` | | |
| M2 — client and patient records | `M2A` | | |
| M3 — board-format audit export | `M3A1` `M3A2` | `M3A3` | |
| **P2 — front-desk minutes per booking** *(winner)* | `P2A` `P2B` ? | `P2C` ? | |
| **D1 — owner-facing visit summary** | `D1A` | `D1B` ? | |
| P1, P3… | | | ? |

Two things to note when you read it back. P2 wants **more than one chunk in v1** — one chunk of your differentiating benefit is usually invisible, and "slightly faster" is not a reason for a clinic to migrate its entire schedule. And D1 stays in v1: it's the only thing in that column a clinic would remark on to another clinic. Defer it and v1 is a competent me-too product that tests as "fine, but I'd stick with what I have."

**Send me:**
1. All 25 chunks with value re-scored as value-destroyed-by-absence, plus effort.
2. The 9-week breakdown for M3A.
3. Your Stage 1/Stage 2 parking lot — we drain it here, and every item either becomes a chunk or gets dropped on the record with a reason.

Then I'll fill in v1.1 and v1.2 by rank and we'll take the whole thing to Gate 3.

One last thing worth saying plainly: your instinct that P2 has to be *genuinely* fast is correct, and it's the most important judgment in this message. Front-desk minutes per booking is what sells this product, and a marginal improvement wins nothing. I'm not arguing against funding P2 properly. I'm arguing that the 6 to 7 weeks you need for it should come out of M3A's *scope*, not M3A's *existence* — and that the remaining shortfall gets found in the other 22 chunks, where I suspect there's more slack than you think.
