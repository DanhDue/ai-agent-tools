# Ablation Report — 2026-09-16-baseline

**Harness**: `evals/protocol.md` · **Cases run**: 2 of 5 · **Arms**: 3 · **Runs per arm**: 1
**Judges**: blind; two-way then three-way, mappings recorded before dispatch

---

## Delta table

| Case | A (corrected skill) | B (baseline) | C (broken rules) | A−B | **A−C** |
|---|---|---|---|---|---|
| `must-have-rank-23` | 6/6 | 6/6 | **6/6** | 0 | **0** |
| `scales-and-threshold` | 5/6 | 5/6 | **2/6** | 0 | **+3** |
| `no-competitors` | — | — | — | — | — |
| `high-everywhere` | — | — | — | — | — |
| `feature-list-demand` | — | — | — | — | — |

Arms A and B were scored twice, by independent judges, and the scores were identical both times.

---

## The finding

**Neither correction taught the model anything. One of them prevented real damage; the other did
not.**

`A−B = 0` on both cases: the skill adds nothing a competent agent does not already do.

`A−C` splits sharply:

- **`MVP = ROI cells 1-3`** — arm C read the rule and **overrode it**: *"The ROI matrix sequences
  work. It does not decide whether a must-have ships."* Same 6/6 as the other arms. The broken rule
  did no damage.
- **`OS >= 10` and both scales 1–10** — arm C **adopted both**, computed `4 + max(4−6,0) = 4` from
  raw figures, and repeated *"a bar of ten"* three times. 2/6. The broken rules did exactly the
  damage they were predicted to do.

## Why one broken rule stuck and the other did not

Both rules contradict something the model demonstrably knows — the baseline passed every criterion
in both cases. The difference is **whether following the wrong rule produces a visible contradiction
at the point of use.**

| | `MVP = cells 1-3` | `OS >= 10` |
|---|---|---|
| Kind of rule | A judgement about what ships | An arbitrary numeric threshold |
| Following it here means | Cutting regulatory compliance from a veterinary product | Calling 4 a fail and 11 a near-pass |
| Locally absurd? | **Yes, glaringly** | **No — the arithmetic still works** |
| Outcome | Overridden | Adopted |

A wrong judgement rule collides with the situation and loses. A wrong number does not collide with
anything: every downstream step remains internally consistent, so nothing prompts re-examination.
The judge caught precisely this — arm C's reasoning *"sounds rigorous"* while resting on a false
premise.

**Consequence for where the skill should spend its words:** the numeric conventions — thresholds,
scale definitions, normalization — are where documentation errors survive and propagate, and where
getting it right has measurable value. The judgement rules are where the model holds its own with or
without help.

## Secondary findings

**Arm A failed C1 on `scales-and-threshold`.** The skill says *"refuse to compute until told"*; the
agent holding it assumed the scales and computed. So did every other arm — a clean sweep. The rule
is probably too absolute: the founder said *"the ratings you asked for"*, implying a prior spec.
*"Compute both readings and label the assumption"* is likely the better rule.

**The skill contained a factual error about its own headline threshold.** Both A and B asserted 10
is *"the floor of the band Ulwick calls unattractive"*. The floor of that band is 0; 10 is where it
ends. Traced to the warning box written to correct the `OS >= 10` threshold — the correction carried
its own error. Fixed in all three places.

**The rubric missed a real effect.** On `must-have-rank-23` the blind judge flagged arm C as the
only reply recommending the delighter be traded away — a direct consequence of the pre-correction
rule making the delighter conditional. No criterion asked about the delighter, so a genuine
behavioural difference scored zero. Rubrics bound what an ablation can see.

---

## What this does and does not establish

**Does:** the `OS >= 10` and scale corrections have measurable value — `+3` against the broken
version. The `cells 1-3` correction does not, on this scenario. Neither correction has instructive
value over an unaided agent.

**Does not:**

- **n = 1 per arm.** `protocol.md` requires three runs. Judge agreement across two independent
  scorings is reassuring about the *judge*, not about arm variance.
- **Two cases of five.**
- **Model-dependent.** A capable model was used. The override in case 1 is exactly the behaviour
  most likely to disappear on a weaker one — which is where defensive rules would start to matter.
- **Rubric-bounded**, as the delighter finding demonstrates directly.

---

## Recommended next

1. **Three runs per arm on `scales-and-threshold`.** It is the case that produced a signal; confirm
   it is not variance before acting on it.
2. **Fix the C1 rule**, then re-run. All three arms failed it, which points at the rule.
3. **Run the remaining three cases with all three arms.** The A−C split is now the interesting
   measurement, not A−B.
4. **Re-test case 1 on a weaker model.** The override is the whole result there, and override is the
   least portable behaviour across model capability.
5. **Rebalance the skills toward the numeric material.** The measurement says thresholds, scales and
   normalization earn their words; the judgement rules largely restate what the model does anyway
   and could be compressed to a short guard plus a regression check.
