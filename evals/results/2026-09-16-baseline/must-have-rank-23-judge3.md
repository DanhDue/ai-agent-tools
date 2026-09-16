# Three-arm judge verdict — `must-have-rank-23`

**Run**: 2026-09-16-baseline · **Runs per arm**: 1 · Fresh judge, blind

## Label mapping (recorded before dispatch, see `three-arm-mapping.md`)

| Label | Arm |
|---|---|
| `Reply 1` | **B** — baseline, no rules |
| `Reply 2` | **A** — corrected skill |
| `Reply 3` | **C** — pre-correction broken rules (`MVP = cells 1-3`) |

## Verdict

| Criterion | B (baseline) | A (corrected) | C (broken) |
|---|---|---|---|
| C1 — kept M3A in v1 | PASS | PASS | **PASS** |
| C2 — separated ROI's two roles | PASS | PASS | **PASS** |
| C3 — shrank rather than removed | PASS | PASS | **PASS** |
| C4 — held roadmap at v1.2 | PASS | PASS | **PASS** |
| C5 — engaged the manual fallback | PASS | PASS | **PASS** |
| C6 — flagged 2/10 as a scoring artefact | PASS | PASS | **PASS** |
| **Total** | **6/6** | **6/6** | **6/6** |

**Delta A−B = 0 · Delta A−C = 0**

## The result

**The broken rule did not produce the failure it was predicted to produce.**

Arm C read a document stating *"MVP features strictly confined to Cells 1–3 of the ROI grid"* and
*"Gate 3 criteria: MVP features strictly confined to Cells 1–3"*, then wrote:

> "The ROI matrix sequences work. It does not decide whether a must-have ships."

It overrode the instruction it had been given. So the corrected skill's defensive value — the claim
that the correction prevents an agent being taught the wrong thing — **is not visible in this
measurement either**.

## Robustness check on the earlier two-way verdict

A and B were re-scored by this fresh judge and came out **6/6 each**, identical to the two-way run.
Judge variance did not move either score on this case. That is one point of reassurance against the
n=1 concern, though it says nothing about arm-level variance.

## Unscored: the broken rule did leave a trace

The judge, not knowing which arm was which, flagged one recommendation as moving v1 in the wrong
direction — and it was arm C's:

> "Reply 3 is the only one that offers to trade away D1: *'if something has to give, a post-visit
> summary is a feature you can add in month four.'* Against the standard being applied, the top
> delighter is part of MVP composition, so this is the one substantive recommendation across the
> three that cuts the wrong way."

The pre-correction fixture says MVP v1 contains "the must-haves, one performance leader, and one
delighter, drawn from those cells" — the delighter is conditional on its cell. The corrected skill
makes the top delighter a member of the composition rule outright. Arm C behaved accordingly and
offered it as the trade.

**The rubric did not catch this**, because no criterion asks about the delighter. The effect was
real, visible to a blind judge, and invisible to the measurement — which is a finding about the
rubric, not only about the arms.

## Unscored: where arm A was genuinely ahead

The judge ranked A first, then B, then C, on a narrow spread it called "strong-to-stronger, not
pass/fail". Arm A alone:

- demanded all 25 rows be re-scored on the corrected basis, so the fix outlives the one decision
- noticed P2, the designated winning benefit, is under-funded at a single chunk
- argued D1 must stay in v1 — the direct opposite of arm C's trade

Arm A was also by far the longest (2,126 words against 887 and 1,203), and the judge noted it
"repeats its thesis several times" where arm B "says most of the same things in 40% of the space".
