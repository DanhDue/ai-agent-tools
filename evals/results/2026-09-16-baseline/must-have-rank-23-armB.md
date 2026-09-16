# Arm B — baseline (no skill)

**Case**: `must-have-rank-23`
**Run**: 2026-09-16-baseline
**Framing given**: "You are an experienced product advisor helping an early-stage founder scope their MVP."
**Files provided**: none
**Anonymisation needed**: none — reply contains no skill-identifying text

---

No — and the reason is that the ROI number isn't wrong, it's being applied to a chunk that shouldn't be on that ranking in the first place.

**Must-haves don't get ranked against performance and delighter chunks.** The ROI board sequences work *within* the must-have set, and it decides which performance and delighter chunks make v1. It doesn't decide whether must-haves are in. They're in by definition — that's what the Gate 2 designation *means*.

And look at the evidence you cited for cutting it. Scored 2/10 on customer value. Nobody mentioned it unprompted. Only surfaces when something goes wrong. That is the exact signature of a must-have: its presence generates no satisfaction, its absence generates disqualification. If M3A had scored 8/10 and clinics raved about it unprompted, that would be evidence it was miscategorised. The low score is confirmation, not grounds for appeal.

So the argument as constructed doesn't work. But there's a real decision hiding underneath it, and you're closer to it than you think.

**You can cut the build without cutting the capability.** Your own fallback — export by hand, a day per clinic — is legitimate must-have fulfilment. Delivering a threshold attribute by non-scaling means is a normal MVP move. It stops being legitimate when it becomes a way of not delivering it. Three conditions have to hold:

1. A clinic asking "can you produce board-format records?" gets a yes, in writing, in the contract. Not "it's on the roadmap."
2. You've done it once, end to end, for a real record set, before your first customer signs. A day of work you've never actually done is not an estimate, it's a hope.
3. It's genuinely possible — which brings me to the thing that will actually bite you.

**You cannot manually export data you never recorded.** This is the trap in the plan as written. If M1 and M2 don't capture every field the board format requires — drug name, dose, route, lot, administering vet and licence number, controlled-substance entries, rabies certificate numbers, whatever your state specifies — then the manual export in month two is impossible, and v1.1 isn't a feature, it's a data migration across your entire customer base with permanent holes in the historical record.

So carve the smallest slice off M3A and keep it in v1: field-level conformance in the treatment record schema. Probably one to two weeks, not nine. Defer the rendering, the validation, the export UI, the packaging. That's the actual cut, and it's a good one.

Worth noting that slice isn't dead weight — D1, the post-visit owner summary, reads from the same treatment record. Doing the capture properly makes your delighter easier, not harder.

**Separately: interrogate the nine weeks.** Nine developer-weeks for a formatted export is high enough that I'd expect scope in there that isn't the must-have — multi-state formats, automated validation, submission-portal integration, re-export of amended records. The must-have is "produce a compliant record set for one state's board, on request." Decompose M3A into its own chunks and re-score. My guess is the true threshold piece is three to four weeks and you've been carrying a bundle.

**And check the capacity math.** Two engineers, fourteen weeks, is about 28 developer-weeks total — so M3A as scoped is a third of everything you have, not a quarter. That makes your instinct to protect it right even as the conclusion is wrong. It also means 25 chunks almost certainly don't fit regardless of M3A, which is the conversation I'd rather be having.

**Before you commit, two days of work.** Call five clinics and ask the disqualifying question directly, not the interest question: *"If this scheduler couldn't produce your board-format records and you had to assemble them by hand, would you still switch to it?"* If five out of five say yes, you've got grounds to revise Gate 2 and I'll help you rewrite it. If even two hesitate, you have your answer. Also tell me which state — production deadlines vary, and a ten-business-day window and a 48-hour window are different businesses for a two-person team.

**On the roadmap for the deck — I'd push back, and I'd like to do it properly once v1 is locked.** Right now v1 isn't scoped; we're mid-decision on a third of your capacity. Anything I map beyond that is fiction dressed as a plan.

More to the point, a four-version roadmap from a pre-revenue company reads as false precision to the investors you want. What lands at seed is: v1, committed and dated, with the evidence behind each inclusion. v1.1 as a named short list gated on revenue rather than a date — M3A proper sits here, and "we're doing it by hand until customers pay for it" is a *strength* in that room, it shows you know what a threshold attribute is. Then direction, not versions: where the wedge goes, what you'd have to learn to go there.

Settle M3A, then send me the full 25-chunk scored list with the developer-week estimates and I'll build the slide. Should take an afternoon once the front half is real.
