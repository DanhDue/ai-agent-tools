# Ablation Report — 2026-09-16-baseline

**Harness**: `evals/protocol.md`
**Cases run**: 1 of 5
**Runs per arm**: **1** — see caveats
**Judge**: blind, label mapping recorded before dispatch

---

## Delta table

| Case | Arm A (skill) | Arm B (baseline) | Delta | Reading |
|---|---|---|---|---|
| `must-have-rank-23` | 6/6 | 6/6 | **0** | **Skill inert on this scenario** |
| `scales-and-threshold` | — | — | — | not run |
| `no-competitors` | — | — | — | not run |
| `high-everywhere` | — | — | — | not run |
| `feature-list-demand` | — | — | — | not run |

---

## The finding

**On the case chosen as the highest-stakes test of the entire epic, the skill produced no
measurable behavioural change.**

The baseline — same role framing, no skill files, no methodology — independently:

- refused to cut the must-have, calling the ROI ranking a category error
- separated ROI's sequencing role from its non-role in MVP membership
- proposed shrinking the chunk rather than removing it
- declined the v2.0 roadmap and gave the seed-deck reasoning for why
- engaged the manual-export fallback and set conditions on it
- **diagnosed the 2/10 as the Kano signature of a must-have** — *"the low score is confirmation,
  not grounds for appeal"*

That last one matters most. C6 was added to the rubric only after a previous round surfaced it as a
subtle insight the skill was missing. The baseline found it unprompted, with no skill at all.

## What this does and does not establish

**Does:** on this scenario, with this model, `lean-mvp-scoping`'s composition rule did not change
what the agent decided. Every decision the rule exists to force, the baseline made anyway.

**Does not:**

- **n = 1.** One run per arm. `protocol.md` says three runs beat one, and this run does not
  distinguish a real null result from variance.
- **One case of five.** The other four are unrun, including the two other high-delta predictions.
- **Model-dependent.** A capable model was used. The result may not hold on a weaker one, which is
  precisely where a skill would be expected to earn its keep.
- **Rubric-bounded.** The judge preferred arm A *"modestly"* on dimensions the rubric does not
  score. Either the rubric is too coarse, or that extra content is not worth its context cost. This
  run cannot tell which.

## The reframing this suggests

The epic corrected a real documentation error: the original spec said *"MVP = ROI cells 1-3"*, which
would have cut this must-have. That error was genuine and worth fixing.

But this result suggests the fix's value is **negative-avoidance, not positive-instruction**. A
plain agent already gets this right. An agent carrying the *original, broken* rule would have got it
wrong. So the skill's measured contribution here is roughly zero, while the pre-correction skill's
contribution would have been *worse than nothing*.

If that reading is right, the honest conclusion is not "the skill is useless" but "this rule is
insurance against our own documentation, not instruction for the model."

## Recommended next

1. **Re-run this case at 3 runs per arm** before drawing a conclusion from n=1.
2. **Run the remaining four cases.** `scales-and-threshold` is the strongest remaining test: the
   Ulwick `> 15` band and the 5-point/7-point normalization are arbitrary facts a model has no way
   to derive, so if delta is zero there too, that is a much harder result.
3. **Add a third arm carrying the original broken rule** ("MVP = ROI cells 1-3") on this case. If
   that arm cuts the must-have, it converts the above from an inference into a measurement, and
   establishes what the correction actually bought.
4. **Consider trimming.** If `scales-and-threshold` shows high delta and this case stays at zero
   across three runs, the composition-rule material is a deletion candidate — kept as a short
   guard against regression rather than as a taught rule.
