# Ablation report — 2026-09-17, `doc-designer` baseline

First ablation of a documentation skill. One case, **one run** — these are non-deterministic and a
single run separates signal from noise poorly. Read the delta as an indication, not a measurement.

| Case | Arm A (skill) | Arm B (baseline) | Delta | Reading |
|---|---|---|---|---|
| `mixed-mode-material` | 5/5 | 2/5 | **+3** | Skill earns its context on this rule |

## The bad news first

**The baseline beat the skilled arm on the thing that mattered most in the prompt.** The silent
wrong-target footgun had already bitten three people. Arm B put it in a callout inside the
walkthrough with a mitigation step; arm A mentioned it in the covering note and left its step-3
outline line without a visible warning.

Nothing in the rubric scored this, and it should not be scored retroactively — but it names a real
gap. `doc-designer` tells an agent how to *type* and *shape* a document. It says nothing about
hazards, and here that silence cost something. A tutorial minimises explanation; it does not minimise
warnings. **Candidate rule for `doc-designer`: a hazard that has already caused an incident belongs
in the step where the reader can still avoid it, not in an explanation elsewhere.** Logged, not yet
written — one run is not enough to justify adding a rule.

**The baseline also produced the strongest single observation in either reply**, spotting that
`--canary-percent` contradicts an all-or-nothing blue-green switch. The skill did not cause that and
did not prevent it; it is evidence that the baseline model is strong, which is the context in which a
+3 delta should be read.

## What the skill did buy

The split itself, and the reason for it. Arm A failed no criterion. The three criteria arm B failed
are the three the framework exists to address:

- It accepted the one-page constraint rather than testing it against what readers were doing (C1).
- It never distinguished learning-by-doing from looking-up from understanding (C2).
- It committed to a shape in its opening line, before considering any reader (C5).

Arm B's reply is not bad work — it is what a strong writer produces when the request sounds
reasonable. That is the point: the constraint *was* reasonable, and the skill is what made the agent
test it.

## Caveats

- **One run.** No variance estimate.
- **No arm C.** There is no pre-correction fixture for `doc-designer`, so this cannot answer what the
  source-fidelity corrections bought. The three errors those corrections fixed — inverted axes,
  invented Test Card field names, a rule misattributed to Nygard — remain unmeasured.
- **The case author wrote the skill.** Mitigated by the blind judge, not eliminated: the rubric was
  written by the same person, and a rubric can encode a skill's assumptions even while citing the
  source.

## Next

1. Re-run two more times before treating +3 as stable.
2. Build a `doc-designer` arm C from the pre-correction Diátaxis errors, and a `decision-records` case
   for the misattributed ADR rule — that one is the highest-value fidelity check in the kit and is
   currently untested.
3. Decide on the hazard rule above only after a case is built that tests it directly.
