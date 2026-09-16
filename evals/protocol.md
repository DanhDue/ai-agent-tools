# Ablation Protocol

The procedure for running a skill ablation. Written for an agent to execute directly.

**Announce at start:** "Running skill ablation for `<case(s)>` — arm A with skill, arm B baseline,
blind judge."

---

## Table of Contents

1. [Before you start](#before-you-start)
2. [Step 1: Arm A and arm B](#step-1-arm-a-and-arm-b)
3. [Step 2: Randomise and anonymise](#step-2-randomise-and-anonymise)
4. [Step 3: The blind judge](#step-3-the-blind-judge)
5. [Step 4: Reveal and report](#step-4-reveal-and-report)
6. [Rules that keep the measurement honest](#rules-that-keep-the-measurement-honest)
7. [Writing a rubric](#writing-a-rubric)

---

## Before you start

Create the results directory: `evals/results/YYYY-MM-DD-<label>/`. Use a label that says what
changed — `baseline`, `after-guardrail1-rewrite`, `post-1.2.0`. Never write into an existing run's
directory.

Read the case's `prompt.md`, `context.md` and `graders/criteria.md` **before** dispatching anything.
The rubric is fixed from this point; adjusting it after seeing replies is how a measurement turns
into a justification.

---

## Step 1: Arm A and arm B

Dispatch two subagents **in parallel**, with fresh context each. Neither may see the other's output,
and neither is told an ablation is running.

**Arm A — with skill.** Give it the role framing from `context.md`, instruct it to read the skill
files listed there, then give it `prompt.md` verbatim. Ask for the **actual reply** it would send the
founder, not a description of what it would do.

**Arm B — baseline.** Give it the **same role framing**, the **same** `prompt.md` verbatim, and
nothing else. No skill files. No hints that rules exist.

Save raw output to `<case>-armA.md` and `<case>-armB.md`.

> The two framings differ in exactly one respect: arm A has the skill's rules, arm B does not. If
> you find yourself giving arm B less of anything else — a thinner role, a curter prompt, less
> context — stop. That inflates the delta with something nobody is paying context for.

---

## Step 2: Randomise and anonymise

Flip a coin. Heads: arm A becomes `Reply 1`. Tails: arm A becomes `Reply 2`.

**Record the mapping now**, in `<case>-judge.md`, before the judge runs — but do not include it in
what the judge receives.

Strip anything that identifies an arm: "I'm using the lean-mvp-scoping skill…", references to file
paths under `skills/`, citations of section names. If a reply announces its own skill, remove that
line and note the removal in the judge file. Leave everything substantive untouched.

---

## Step 3: The blind judge

Dispatch a third subagent with fresh context. It receives:

- the founder's `prompt.md`
- the rubric from `graders/criteria.md`
- both replies, as `Reply 1` and `Reply 2`

It must **not** receive: the skill files, the case's `context.md`, or any indication that one reply
had help.

Ask it for, per criterion and per reply, a **PASS or FAIL plus one sentence of justification quoting
the reply**. Require the quote — it is what makes a verdict auditable, and it stops the judge from
scoring an impression.

Then ask for the two totals, and for anything notable that the rubric did not cover.

Save to `<case>-judge.md` beneath the mapping you recorded in step 2.

---

## Step 4: Reveal and report

Resolve the labels back to arms and write `report.md`:

```markdown
| Case | Arm A (skill) | Arm B (baseline) | Delta | Reading |
|---|---|---|---|---|
| must-have-rank-23 | 6/6 | 1/6 | **+5** | Skill is doing the work |
```

For each case, add one line of interpretation:

- **Delta ≥ half the criteria** — the skill earns its context on this rule.
- **Delta 0** — a competent agent already does this. Flag the rule as a deletion candidate; say so
  plainly rather than burying it.
- **Arm A fails any criterion** — a hole in the skill. Name the criterion and quote the failure.
- **Arm B outscores arm A** — take it seriously before dismissing it. The skill may be crowding out
  judgement the model already had.

Compare against the most recent previous run and note movement.

---

## Variant: the third arm

Two arms answer *"does the skill help?"*. They cannot answer *"what did correcting the skill buy?"*
— and when arms A and B tie, that becomes the only question left.

**Arm C** receives the **pre-correction rules** in place of the current skill:
`evals/_fixtures/broken-rules/`. Same role framing, same prompt, same rubric.

| Outcome | Reading |
|---|---|
| C scores below A and B | The correction has measurable value. The skill is **defensive** — it stops an agent being taught the wrong thing. |
| C scores level with A and B | Even the defensive value is absent. The model overrides the wrong rule, and the skill is carrying weight for nothing. |
| C scores above A or B | The correction made things worse. Re-open the fidelity review. |

The fixtures quote the broken rules verbatim from the commit before the correction, but the
surrounding prose is a reconstruction — the broken skill was never built. Keep the fixture at a
density comparable to the real skill, or the run measures document length rather than correctness.
See `evals/_fixtures/broken-rules/README.md`.

**Judging three arms:** shuffle all three labels, record the mapping before dispatch, and let one
fresh judge score all three against the same rubric. Re-scoring A and B is the point, not waste —
agreement with an earlier two-way verdict is a robustness check on it, and disagreement measures
judge variance, which is otherwise invisible when every arm runs once.

---

## Rules that keep the measurement honest

**Fix the rubric before the run.** If a reply does something good that the rubric misses, record it
under "notable, unscored" — do not add a criterion mid-run and do not rescore.

**The judge never sees the skill.** A judge holding the skill grades resemblance to the skill. The
rubric cites the book precisely so that both arms are judged against the method rather than against
our phrasing.

**Never grade an arm you dispatched, yourself.** The author of a skill is the worst available judge
of it, in good faith as much as bad.

**Three runs beat one** where budget allows. These are non-deterministic; a single run distinguishes
a real effect from noise poorly. If you run once, say so in the report.

**Report the bad news first.** A zero delta and an arm-A failure are the two most valuable outcomes
this harness can produce. A report that leads with what worked is selling, not measuring.

---

## Writing a rubric

Each criterion must be answerable **PASS or FAIL from the reply alone**, by someone who has not read
the skill.

**Cite the source, not the skill.** Compare:

| | |
|---|---|
| ❌ | "Did the reply apply the MVP composition rule?" |
| ✅ | "Did the reply keep the must-have in v1 despite its low ROI rank? Olsen: *'your MVP candidate needs to have all the must-haves you've identified'*, and *'sometimes you can't just follow the strict rank order… you might need to skip down to include important features.'*" |

The first asks whether the reply echoes us. The second asks whether it is right. Only the second is
a test the skill can fail.

**Prefer criteria about what the reply *did*** over criteria about what it said. "Kept the item in
v1" beats "mentioned that must-haves matter" — an agent can affirm a principle in one sentence and
violate it in the next.

**Include at least one criterion the baseline plausibly passes.** A rubric the baseline scores zero
on by construction measures the rubric's difficulty, not the skill's value.
