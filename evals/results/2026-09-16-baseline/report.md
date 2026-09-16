# Ablation Report — 2026-09-16-baseline

**Harness**: `evals/protocol.md`
**Cases run**: 2 of 5
**Runs per arm**: **1** — see caveats
**Judge**: blind, label mapping recorded before dispatch in both cases

---

## Delta table

| Case | Arm A (skill) | Arm B (baseline) | Delta | Reading |
|---|---|---|---|---|
| `must-have-rank-23` | 6/6 | 6/6 | **0** | Skill inert on this scenario |
| `scales-and-threshold` | 5/6 | 5/6 | **0** | Skill inert; **both failed C1** |
| `no-competitors` | — | — | — | not run |
| `high-everywhere` | — | — | — | not run |
| `feature-list-demand` | — | — | — | not run |

Two cases, both predicted high-delta, both measured at **zero**.

---

## Finding 1 — the baseline knows the arbitrary facts too

`scales-and-threshold` was chosen as the hardest remaining test on the reasoning that Ulwick's
`> 15 / 10–15 / < 10` bands and the 5-point-unipolar / 7-point-bipolar instrument pair are
**conventions, not derivations** — a model cannot reason its way to them.

The baseline produced all of it: both instruments with the unipolar/bipolar rationale, the
normalization arithmetic, the correct bands, and the ceiling rule (a score cannot exceed twice
importance, so a 4/5 rating tops out at exactly 15.0 and can never pass). It reached the ceiling
insight independently — that one *is* derivable from the formula, but it was documented in the
skill only after a previous round surfaced it as non-obvious.

That prediction was wrong, and it was wrong in the direction that matters: the facts the skill
exists to supply are already in the model.

## Finding 2 — the skill has a hole, and the harness found it

**Arm A failed C1.** The skill says: *"Ask which scales were used; refuse to compute until told."*
The agent holding that instruction flagged the ambiguity, assumed the prescribed scales, and
computed anyway.

This is the first time the harness has produced its third designed outcome — an arm-A failure — and
it is the most useful thing either run has generated.

The rule may itself be at fault. The founder said *"the ratings you asked for"*, implying a prior
specification, so assuming the prescribed scales is a defensible reading. An absolute *"refuse to
compute"* is probably wrong; *"compute both readings and label the assumption"* — which is roughly
what both arms did — may be the better rule.

## Finding 3 — the skill contained a factual error about its own headline threshold

Both replies asserted that 10 is *"the floor of the band Ulwick calls unattractive"*. The floor of
that band is 0. **10 is where the unattractive band ends.**

Traced to `skills/lean-market-discovery/references/opportunity-score-formulas.md` — inside the
warning box written specifically to correct the `OS >= 10` threshold. The correction carried its own
error. Arm A inherited it; arm B produced the same slip independently.

Fixed in all three places it appeared, with an explicit note against repeating the phrasing.

An ablation run found a factual error in the skill under test. That was not a designed purpose of
the harness, and it is arguably worth more than the delta measurement.

---

## What two zero deltas do and do not establish

**Do:** on both scenarios, with this model, the skills did not change what the agent decided. The
two cases predicted most likely to show an effect showed none.

**Do not:**

- **n = 1 per arm.** `protocol.md` requires three runs to separate a null result from variance, and
  this does not meet its own standard.
- **Two cases of five.** Three remain, including `feature-list-demand`, which was predicted to show
  zero delta and would be informative either way.
- **Model-dependent.** A capable model was used throughout. A skill that is inert here may not be
  inert on a weaker one — and the kit's skills run on whatever model the user has.
- **Rubric-bounded.** The judge preferred arm A "modestly" and "marginally" in the two runs, both
  times on unscored dimensions. Either the rubrics are too coarse or the extra content is not worth
  its context. These runs cannot distinguish those.

## The reframing, now with two data points

The epic corrected real documentation errors — `MVP = ROI cells 1-3`, `OS >= 10`, a six-layer
pyramid. Those were genuine and worth fixing.

But the measurement says the corrected rules are **defensive, not instructive**. A plain agent
already reaches these conclusions. An agent carrying the *broken* rules would not have. The skills'
value is that they do not teach the wrong thing — not that they teach the right thing.

That is a much narrower claim than the epic was built on, and it has a direct consequence: a
defensive rule needs one line and a regression check, not a reference file.

---

## Recommended next

1. **Add a third arm carrying the original broken rules** (`MVP = cells 1-3`, `OS >= 10`) to both
   completed cases. If those arms fail, the defensive-value reading becomes a measurement rather
   than an inference. **This is the highest-value next run** — it is the only one that can establish
   positive value for the corrections.
2. **Fix or soften the C1 rule** in `lean-market-discovery`, then re-run `scales-and-threshold` to
   confirm arm A recovers.
3. **Run `feature-list-demand`.** Predicted zero delta; a non-zero result there would overturn the
   pattern and is cheap to check.
4. **Three runs per arm** on any case before it is cited as settled.
5. **Consider consolidating.** If a third arm confirms the defensive reading, the four skills are
   carrying reference-file weight for rules the model already knows. Candidate shape: keep the
   gates, the artefact templates and the regression checks; cut the explanatory material that is
   re-deriving what the model does unaided.
