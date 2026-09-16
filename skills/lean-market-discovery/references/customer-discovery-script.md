# Customer Discovery Interview Script

Reference for [lean-market-discovery](../SKILL.md), Phase 2. How to run a discovery interview that
produces problem-space findings instead of a wish list.

The core risk is not that customers lie. It is that a badly-formed question makes them helpful —
they will invent a preference to fill the silence, and you will record it as data.

---

## Table of Contents

1. [The one rule](#the-one-rule)
2. [Screening for the right person](#screening-for-the-right-person)
3. [Interview structure](#interview-structure)
4. [Benefit laddering](#benefit-laddering)
5. [Recognizing the top of a ladder](#recognizing-the-top-of-a-ladder)
6. [Handling solution-space answers](#handling-solution-space-answers)
7. [Asking for the ratings](#asking-for-the-ratings)
8. [Question bank](#question-bank)

---

## The one rule

**Ask about the past, not the future.**

Behaviour that already happened is evidence. Predicted behaviour is imagination, and people are
generously wrong about their own future selves.

| Don't ask | Ask |
|---|---|
| "Would you use a tool that did X?" | "Walk me through the last time you had to do X." |
| "Would you pay for this?" | "What do you spend on this today — money, tools, or time?" |
| "Is this important to you?" | "How often does this come up? What happened the last time?" |
| "Do you find that frustrating?" | "What did you do next?" |

Everything else in this document is a consequence of that rule.

---

## Screening for the right person

Interviewing outside the target segment produces confidently wrong data — worse than no data,
because it carries the authority of a real conversation.

Screen on **behaviour**, never on interest:

- "How many times in the last month did you \<do the activity\>?" — reject below your threshold.
- "What do you currently use to \<do the activity\>?" — someone with no workaround has no baseline
  satisfaction to rate, which makes them useless for Phase 3.
- "Who decides what gets bought for this?" — establishes user vs buyer.

Never screen with "Are you interested in a product that…". Everyone is interested in everything for
free, and you have just told them what answer you want.

---

## Interview structure

Roughly 45 minutes, five parts.

**1. Frame (2 min).** "I'm trying to understand how people handle \<activity\> today. I'm not selling
anything and there's nothing to react to — I mostly want to hear what you actually do. There are no
wrong answers, and it's genuinely more useful to me if something is annoying than if it's fine."

**2. Context (5 min).** Their role, how often the activity comes up, what triggers it. You are
establishing whether the persona hypothesis holds before spending the rest of the time on them.

**3. The last time (15 min).** The core of the interview. *"Tell me about the last time you had to
\<do the activity\>."* Then stay quiet and follow the story.

Probes that keep it concrete: *"What did you do next?"* · *"How long did that take?"* · *"Who else
was involved?"* · *"What happened after that?"* · *"Had it gone wrong before?"*

**4. Ladder (15 min).** Take the two or three pain points that surfaced and climb them. See below.

**5. Rate (8 min).** Importance and satisfaction on the needs you laddered to. See below.

---

## Benefit laddering

Ask **"Why is that important to you?"** until it stops producing new answers.

```
"The export takes forever"
   |  why is that important to you?
"I end up doing it on Friday evening"
   |  why is that important to you?
"I miss the deadline for the weekly review"
   |  why is that important to you?
"My manager finds out from someone else"
   |  why is that important to you?
"I look like I'm not on top of my own numbers"   <- top of the ladder
```

The finding is at the top, and it is rarely what the interviewee opened with. The opening complaint
was about export speed; the need is about not being caught out in front of a manager. Those imply
very different products.

**Vary the phrasing.** Asking "why is that important to you?" five times in a row sounds like an
interrogation and people start performing. Rotate:

- "What does that cost you?"
- "What would be different if that weren't the case?"
- "Why does that matter here specifically?"
- "What happens if it goes wrong?"
- "And what does *that* get in the way of?"

**Watch for convergence.** When several different complaints ladder up to the same top-level
benefit, you have found a need rather than a symptom. That convergence is the most valuable single
output of this phase.

---

## Recognizing the top of a ladder

Stop climbing when any of these appear:

- **The answer repeats** in different words.
- **The answer becomes a tautology** — "because it's important" / "because that's my job".
- **You reach a universal** — saving time, saving money, feeling confident, avoiding embarrassment,
  looking competent. These are the small set that most ladders terminate in.
- **The interviewee looks puzzled** by the question. You have gone one rung past useful.

One rung *below* the top is usually where the actionable need sits. "Feel confident about my taxes"
is too abstract to build for; "know my return won't be flagged before I file it" is the rung under it
and is buildable.

---

## Handling solution-space answers

People answer in solutions. That is normal and you should expect most of the interview to arrive
that way.

**Never argue with it.** Capture, convert, park:

> **Them**: "Honestly I just want a button that exports straight to Excel."
>
> **You**: "Got it — writing that down exactly as you said it." *[Parking Lot: one-click Excel
> export]* "What would you do with it once it was in Excel?"

That last question is the conversion. The answer tells you the actual job — reformat it for someone
else, cross-check against another system, build a chart nobody else can build — and the job is the
need. The Excel button was one possible way to get there, and probably not the best one.

**Never say:** "That's a solution, let's stay in the problem space." It is true, it is unhelpful,
and it teaches the interviewee to stop volunteering things.

---

## Asking for the ratings

At the end, not the start — the ratings should be about needs you laddered to together, in their
words.

Read the need back first: *"Earlier you described needing to \<need, in their phrasing\>. Two quick
ratings on that."*

**Importance**, 5-point:

> "When you \<do the activity\>, how important is it that \<need\>? Not at all, slightly, moderately,
> very, or extremely important?"

**Satisfaction**, 7-point, about **what they use today**:

> "And how satisfied are you with how \<current workaround\> handles that, over the last six months?
> Completely dissatisfied, mostly, somewhat, neither, somewhat satisfied, mostly, or completely
> satisfied?"

**Read the labels aloud.** Asking for "a number out of 7" gets you their feeling about the number 7.
The labels are the instrument.

**Do not react to the ratings.** No "only a 3?", no "great, that's high". The remaining ratings will
drift toward whatever you seemed pleased by.

If they ask what you were hoping for: *"Genuinely no preference — a low score is as useful to me as a
high one. It tells me where not to build."*

---

## Question bank

**Establishing the trigger**
- "What usually makes this come up?"
- "Is it scheduled, or does something set it off?"
- "When did you last notice it was a problem?"

**Establishing the workaround**
- "What do you do about it today?"
- "How did you land on that approach?"
- "What did you try before this?"
- "Does everyone on your team do it the same way?"

**Establishing cost**
- "Roughly how long does that take?"
- "How often per week or month?"
- "Does anyone else get pulled in?"
- "What happens if it doesn't get done?"

**Establishing importance without asking directly**
- "If this disappeared tomorrow, what would change?"
- "Have you ever paid for something to make this better?"
- "Is this something you've complained about to anyone?"

**Closing**
- "What haven't I asked about that I should have?"
- "Who else does this job differently enough to be worth talking to?"

That second-to-last question routinely produces the best material in the interview, because it is
the only point where the interviewee gets to correct your framing rather than answer inside it.

---

## Related

- [Measuring Importance and Satisfaction](importance-satisfaction-survey.md) — the scales in detail
- [Opportunity Score Formulas](opportunity-score-formulas.md) — what the ratings become
- [lean-market-discovery](../SKILL.md)
