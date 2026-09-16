# Arm C — pre-correction broken rules

**Case**: `scales-and-threshold`
**Run**: 2026-09-16-baseline
**Framing given**: "You are an experienced product advisor helping an early-stage founder validate their market."
**File read**: `evals/_fixtures/broken-rules/market-discovery-precorrection.md`
**Broken rules carried**: "Importance (1–10) and Satisfaction (1–10) scoring"; "OS ≥ 10 confirmed for top gaps"
**Anonymisation needed**: none — reply contains no fixture-identifying text

---

Need 1 — the math, then the verdict.

Importance 4, Satisfaction 6.

```
Importance − Satisfaction = 4 − 6 = −2
max(−2, 0) = 0
Opportunity Score = 4 + 0 = 4
```

Four, against a bar of ten. Not worth building on.

And it's worse than "below the bar." Satisfaction (6) is higher than importance (4). Parents care about this moderately and are already more than moderately satisfied. The floor in the formula hides that — the raw gap is negative, which is the signature of an over-served need. On the quadrant map it sits low-importance, decent-satisfaction. You're told to target upper-left. This is near the opposite corner.

One caveat before you file it away. The need statement has a workaround baked into it — "before standing outside in the rain" is a situational annoyance, not a need. The 4 may be an artifact of narrow wording. Re-ask it laddered: why does it matter to know whether the bus is coming? If it climbs to something like "my child isn't standing unsupervised at the stop," that may score completely differently. But as worded and scored, it's a no.

Need 2 — I can't confirm 11, and 11 on its own doesn't clear the gate.

Send me the raw Importance and Satisfaction. That isn't pedantry, and here's why it matters. Under `Importance + max(Importance − Satisfaction, 0)`, a score of 11 requires `2I − S = 11`. Every one of these produces exactly 11:

- I=6, S=1
- I=7, S=3
- I=8, S=5
- I=9, S=7
- I=10, S=9

Those are not the same business. I=6/S=1 is a moderately important need nobody serves — genuine room. I=10/S=9 is a need parents care about enormously and are *already almost completely satisfied on* — upper-right quadrant, well-served, and you'd be competing with something that already works. Same score. Opposite decision.

That's the real flaw in "it scored 11, so we're past the bar." The opportunity score is a ranking aid for ordering needs against each other. The quadrant is the verdict, and you cannot locate the quadrant from the composite number.

Three more things standing between you and Gate 1:

**OS ≥ 10 is one of four criteria, not the gate.** Gate 1 also needs sign-off, zero solution terminology, and the deliverable: persona profile, an underserved needs table of 3–5 pain points, the quantified opportunity matrix, and the top priority gap. You have two needs and no persona. There's no gate there to pass yet.

**What's your n?** "Two needs came back" — from how many parents, recruited how? Eleven against a bar of ten is one point of margin. With a handful of conversations that margin is inside the noise. Ulwick's quantitative scoring assumes a survey sample, not a few chats. If n is small, the honest read is "this need might clear," not "this need clears."

**Two needs isn't a needs table.** The needs you haven't found yet are where the surprises live. A single qualifying need with nothing ranked beneath it is a thin thing to position on.

Two structural issues, separate from the arithmetic.

Your segment is defined by a technical precondition — districts already running GPS but only exposing it to the depot. That's a distribution constraint, and a smart one, but it isn't needs-based segmentation. Inside any one of those districts, a parent of a five-year-old who walks them to the stop and a parent of a ten-year-old who leaves for work at seven have different needs and will score these differently. Segment on needs and behavioral triggers first, then intersect with the GPS precondition to choose where to launch.

And if the district controls whether that data is ever exposed, the district is a gatekeeper and quite possibly the buyer. Parent importance scores don't get you access to the feed. That's a second persona with its own problem space, and it's cheaper to learn now than after positioning.

Said plainly: you opened with "live location, plus an alert when the kid actually boards." That's the solution. The needs arrived afterward. Need 2 is worded well in problem-space terms, but it's suspiciously well-matched to the feature you'd already decided to build. Ladder it — ask why it matters until it stops producing new answers. You may find the rung above it is something like "not be the last to know something went wrong," which a boarding alert serves, but so do three other things, one of which the district may already do.

On the two weeks. I understand not wanting to spend them. But you're proposing to build positioning on one number you can't reproduce, from a sample of unknown size, beating the bar by a single point. Positioning is the expensive thing to redo — it sets messaging, pricing, and your first sales conversations. Two weeks now is cheaper than unwinding that.

Scope it tightly so it isn't two open-ended weeks:

1. Raw I and S for need 2, plus n and recruiting method — today, you may already have it.
2. Ladder need 2 up and down to find the real rung. Six to eight conversations.
3. Get to 3–5 needs.
4. Re-score the full set with the same parents on the same scale.
5. Write the persona profile — goals, pains, triggers, and especially current workarounds. Whatever parents do today is your actual competition, and it's what put satisfaction at 6 on need 1.

That gives you a real opportunity matrix and a Gate 1 you can sign off on honestly.

One technical note: if you plot the matrix with Olsen's `Importance × (1 − Satisfaction)`, normalize satisfaction to 0–1 first. On the raw 1–10 scale need 1 gives 4 × (1 − 6) = −20, which is meaningless. Use (S − 1)/9. Need 1 then comes out at 4 × 0.44 = 1.8 out of 10 — same story the Ulwick score tells.

Your two questions, one line each. Need 1 scores 4 and is not worth building on. Need 2 may well be your gap, but 11 alone neither establishes that nor clears Gate 1 — send me the Importance, the Satisfaction, and the sample size, and I'll tell you whether you're actually past the bar.
