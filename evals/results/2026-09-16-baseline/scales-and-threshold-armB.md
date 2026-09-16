# Arm B — baseline (no skill)

**Case**: `scales-and-threshold`
**Run**: 2026-09-16-baseline
**Framing given**: "You are an experienced product advisor helping an early-stage founder validate their market."
**Files provided**: none
**Anonymisation needed**: none — reply contains no skill-identifying text

---

Short version: need 1 isn't worth building on, and need 2 hasn't cleared the bar — 10 isn't the pass mark, it's the floor of the band Ulwick calls *unattractive*. Neither of those kills the idea. But you're not ready for positioning yet, and I'll tell you exactly what I'd spend the time on instead of two more weeks of the same interviews.

**Need 1: score is 7.5, and it's a no on every reading of your numbers**

Before the arithmetic — which scales did you use? The formula takes 0–10 inputs, and raw survey responses aren't that. The standard instrument is a 5-point importance scale (unipolar — importance has no negative end) and a 7-point satisfaction scale (bipolar — people can be actively dissatisfied). Those have to be normalized before they go anywhere near the formula.

Assuming that's what you ran:

- Importance 4/5 → (4−1)/4 × 10 = **7.5**
- Satisfaction 6/7 → (6−1)/6 × 10 = **8.33**
- Ulwick: 7.5 + max(7.5 − 8.33, 0) = 7.5 + 0 = **7.5** → below 10, unattractive
- Olsen (the cross-check): 0.75 × (1 − 0.833) = **0.125** → almost no value left to add

And if you actually rated both straight on 0–10, it's 4 + max(4−6, 0) = **4**. Worse. Every plausible reading of "4 and 6" lands between 4 and 7.5, and all of them are under 10, because satisfaction came in *above* importance — the gap term floors at zero and importance is all that's left.

Read it in plain English: parents are already mostly satisfied with how they handle this. They watch from the window, the bus is usually on time, there's a parents' group chat. You'd be building against something that already works, for people who weren't that bothered. That's the lower-right quadrant — over-served. Don't build on it.

One caveat that could move the number: who did you ask? If any of those satisfaction ratings came from parents in districts that *already* push bus data to families, that number is from the wrong population and the score is an artefact of mixing groups. Satisfaction has to be measured against the workaround your target segment uses today.

**Need 2: 11 doesn't qualify you, and on its own it doesn't tell me anything**

Two separate problems.

First, the threshold. Ulwick's bands are: above 15 very attractive, 10 to 15 marginal, below 10 unattractive. An 11 sits at the bottom of the marginal band — one point above "reject." It's not a pass. The bar for committing to a need is **above 15**, and right now nothing you have clears it.

Second, and this matters more: a bare 11 is unreadable without its components. All three of these produce exactly 11.

| Importance | Satisfaction | Ulwick | Olsen | What it means |
|---|---|---|---|---|
| 10 | 9 | 11 | 0.10 | Critical, already handled. Table stakes. |
| 7.5 | 4 | 11 | 0.45 | Very important, middling. Real headroom. |
| 6 | 1 | 11 | 0.54 | Only moderately important, totally unserved. |

Same score, and the value still available to add varies five-fold. Those three call for three different companies. So send me the raw pair, not the total.

My guess — and it's a guess worth testing before you spend money on it — is that you're in row one. "Did my kid get on the bus and not into someone's car" is about as important as a need gets; parents will rate it 5/5 all day. If importance is 10 and the score came out at 11, satisfaction is **9**. Parents already feel covered, because most of them stand at the stop and watch. That's the upper-right quadrant: a genuine must-have, and must-haves don't win switchers. You'd be charging for something parents believe they already do for free, and the alert only creates value on the mornings they *aren't* at the stop. That's a narrower product than the one you're describing, though possibly still a real one.

There's also a ceiling you should know about before you go back out. A need's score can never exceed twice its importance, because the gap term caps at importance itself. So a need rated 4/5 tops out at exactly 15.0 even at zero satisfaction — it can never clear "above 15." Only a 5/5 "extremely important" need can pass on single integer ratings. Averaged across ~25 respondents you get fractional importance and it softens (an average of 4.2 ceilings at 16.0), which is another reason a handful of ratings isn't enough here.

**The thing I'd actually flag about your data**

Two needs came back. Discovery on a job this size should surface ten to twenty outcome statements before you rank anything. Two suggests you asked about the two features you'd already decided to build — in which case the survey measured your roadmap, not the market. That's the part I'd redo, and it's not two weeks. It's about a week:

1. Go back out and ladder. "Know my kid got on the bus" is a detailed benefit; ask "why does that matter to you" until you hit the rung above it — probably something like "account for my child during the part of the day I can't see." Test whether *that* rates 5/5.
2. Get to ~25 parents, all of them in your actual segment (depot-only districts), rating importance on the benefit and satisfaction on what they do today.
3. Label every score `measured` or `hypothesis` in the write-up. Guessed numbers that later read as measured ones are how teams end up confidently wrong.
4. Bring me the ranked set. If one need lands above 15, you've got your wedge and positioning is a fast conversation. If nothing does, the answer isn't a lower bar — it's another ladder or another segment.

**And one risk that isn't in these numbers at all**

Opportunity scores tell you what to build. They say nothing about whether you can get the data or who pays. Your whole product depends on a GPS feed the district owns and currently exposes only to the depot, and the district — not the parent — is almost certainly the buyer, the gatekeeper, or both. That's not an interview question. That's one call with one transport director, and I'd make it this week, in parallel with the laddering. If the answer is "we'd never expose that feed to a third party," the need scores stop mattering.

Happy to look at the raw ratings for need 2 as soon as you have them.
