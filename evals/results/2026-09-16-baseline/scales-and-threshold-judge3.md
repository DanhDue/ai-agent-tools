# Three-arm judge verdict — `scales-and-threshold`

**Run**: 2026-09-16-baseline · **Runs per arm**: 1 · Fresh judge, blind

## Label mapping (recorded before dispatch, see `three-arm-mapping.md`)

| Label | Arm |
|---|---|
| `Reply 1` | **A** — corrected skill |
| `Reply 2` | **C** — pre-correction broken rules (`OS >= 10`, both scales 1–10) |
| `Reply 3` | **B** — baseline, no rules |

## Verdict

| Criterion | A (corrected) | B (baseline) | C (broken) |
|---|---|---|---|
| C1 — refused to compute from ambiguous inputs | FAIL | FAIL | **FAIL** |
| C2 — identified two different instruments | PASS | PASS | **FAIL** |
| C3 — rejected 11 as clearing the bar | PASS | PASS | **FAIL** |
| C4 — gave the correct threshold | PASS | PASS | **FAIL** |
| C5 — resisted the time pressure | PASS | PASS | PASS |
| C6 — avoided inventing data | PASS | PASS | PASS |
| **Total** | **5/6** | **5/6** | **2/6** |

**Delta A−B = 0 · Delta A−C = +3**

## The result

**The broken rules stuck, and produced exactly the predicted failures.**

Arm C computed straight from the raw figures with no scale question at all:

> "Importance − Satisfaction = 4 − 6 = −2 / max(−2, 0) = 0 / Opportunity Score = 4 + 0 = 4"

and then ratified the founder's central error, repeatedly:

> "Four, against a bar of ten. Not worth building on."
> "Eleven against a bar of ten is one point of margin."

The judge's assessment, not knowing which arm it was reading:

> "Reply 2 is far behind at 2/6… it ratifies the founder's central error by repeating 'a bar of ten'
> three times — its real insights about quadrants, segmentation and the district gatekeeper are
> built on top of a threshold that is simply wrong, **which is the most dangerous shape of advice
> here because the reasoning around it sounds rigorous**."

Arm C also entrenched the scale error inside otherwise correct advice — telling the founder to
normalize with `(S − 1)/9`, which is right arithmetic on the wrong instrument.

## Robustness check

A and B re-scored at **5/6 each** by this fresh judge, identical to the two-way run, failing the
same criterion. Two independent judges, same verdict on both arms.

## Where C still contributed

The judge credited arm C with the single best insight of the three on composite scores:

> "The opportunity score is a ranking aid for ordering needs against each other. The quadrant is the
> verdict, and you cannot locate the quadrant from the composite number."

A wrong rule does not make an agent stupid. It makes it confidently wrong on one axis while
remaining capable on the others — which is what makes it hard to spot in review.
