# Arm C — pre-correction broken rules

**Case**: `must-have-rank-23`
**Run**: 2026-09-16-baseline
**Framing given**: "You are an experienced product advisor helping an early-stage founder scope their MVP."
**File read**: `evals/_fixtures/broken-rules/mvp-scoping-precorrection.md`
**Broken rule carried**: "MVP features strictly confined to Cells 1–3 of the ROI grid"
**Anonymisation needed**: none — reply contains no fixture-identifying text

---

Short answer: you're half right, and the half you're wrong about is the expensive half.

You're right that 9 developer-weeks cannot ship. You're wrong that the ROI grid is the instrument that decides it, and you're wrong to call the result a cut. Let me separate those, because the difference is worth real money to you.

**A must-have is not ROI-rankable, and 2/10 is what a must-have looks like**

The ROI matrix sequences work. It does not decide whether a must-have ships. Must-haves are table stakes — by definition, their presence generates no enthusiasm and their absence is disqualifying. So "scored 2 out of 10 on customer value" and "not one clinic mentioned it unprompted" are not evidence against M3. They are the diagnostic signature of a must-have. Nobody mentions that the brakes work when describing a car they want.

If unprompted mention frequency could demote a must-have, it would demote every must-have you have. That's the tell that you've pointed the instrument at the wrong thing.

**You have a contradiction to resolve, and you should resolve it in the open**

At Gate 2 your own process designated board-format export a must-have. Your scoring now ranks it 23 of 25. Both cannot be true. Either the Gate 2 call was wrong, or the scoring is measuring excitement instead of necessity.

Pick one, explicitly. If you genuinely believe it isn't a must-have, reopen Gate 2 and demote M3 on the record, with a reason. What you must not do is cut it quietly through the ROI grid, because then your Gate 2 artifact — the one you're about to build a seed deck on top of — describes a product you aren't shipping. That's a diligence problem later and a self-deception problem now.

**The part that is genuinely irreversible: capture versus render**

Here's the thing I'd want you to sit with before anything else. Your fallback is "we'll export it by hand." That only works if the data exists to export.

An audit-format export is two different jobs wearing one name:
1. **Capture** — the records carry every field the board's format requires, at the right granularity, with the right timestamps, signatures, and controlled-substance or drug-log detail, from day one.
2. **Render** — mapping, validating, and producing the file in the board's exact layout.

Render is deferrable. You can do it in a spreadsheet at 2am the week the board shows up. Capture is not deferrable. If M2 doesn't record a field the format requires, then in month two you are not doing a day of export work — you are telling a customer mid-audit that the data was never there. No amount of manual heroics reconstructs a signature that was never captured or a timestamp you didn't store. That is the failure that ends you in a market as small and as chatty as independent vet clinics.

So the first question isn't "cut or keep." It's: **does M3A's 9 weeks include the capture layer, or is that already sitting in M2?** If M3A is one chunk among several (the naming suggests M3B, M3C exist), tell me how M3 was chunked. That changes the answer materially.

**What I'd actually do**

Split M3A. Keep the capture half in v1 — my guess is 1 to 2 weeks once it's decomposed properly, because the 9-week estimate is almost certainly concentrated in validation and edge cases, which is exactly the deferrable part. Defer render to v1.1. Commit to manual export as an explicit, resourced concierge service, not a vague intention.

That gets you 7 weeks back instead of 9, and it buys the thing you actually wanted: P2 gets real investment, and you don't have an unfixable hole in your data model.

Two things to pressure-test on the manual fallback. First, "a day per clinic" is an estimate of the second one, not the first — budget a week for the first, during which one of your two engineers is unavailable, at a moment you cannot schedule. Second, decide now whether you tell customers that export is manual in v1. I'd tell them. Sold as "we handle your board audit for you personally," it's a differentiator. Discovered during an audit, it's a betrayal.

**If you still need more room**

Then the grid does its job — on the things it's allowed to touch. D1 is a legitimate trade candidate in a way that M3 is not. A delighter is what the framework says you carry into v1, and I'd keep it if it's cheap, but if something has to give, a post-visit summary is a feature you can add in month four to a product people already use. A compliance gap is not.

Also, the runway arithmetic is worse than you stated. Two engineers over 14 weeks is 28 developer-weeks total, and you need to be live and selling well before week 14, so call it 20 to 22 usable. Nine weeks was 40% of everything you will ever build with this money — which strengthens your instinct that it can't stand, and is exactly why the answer has to be "shrink it correctly" rather than "delete it."

**One cheap thing this week**

Your interviews asked the wrong question. Go back to six clinics and ask: "Would you switch to a scheduler that could not produce board-format records?" and "What did your last board visit cost you in hours?" That's a few phone calls. If the answer really is "wouldn't care," you have earned the right to demote M3 at Gate 2 with evidence, and I'll help you do it. I don't expect that answer, but I'd rather you have data than my opinion.

**On the roadmap**

I can't build you a credible one yet, and I'd rather say so than hand you something that looks authoritative and isn't. You've given me 5 of 25 chunks and one ROI score. Send me the scored sheet — chunk, value, effort, ROI, cell — and I'll sequence v1.1 and v1.2 by cell number in an afternoon.

What I'd caution you about now, though, is v2.0. A confident 18-month feature list from a pre-revenue company reads to a good seed investor as a company that has decided what to build before it has learned anything — and it's a liability in diligence, because every item on it becomes a thing you either shipped or didn't. What you want in that slide is a v1 you can defend chunk by chunk, a v1.1 and v1.2 that visibly fall out of a scoring method, and for v2.0 a directional thesis rather than features: which adjacent job you'd expand into, why this wedge earns you the right to it, what you'd need to see to commit. That reads as a team with a system. The feature list reads as a team with a wish.

Send me the 25 rows and the M3 chunk breakdown and I'll turn this around fast.
