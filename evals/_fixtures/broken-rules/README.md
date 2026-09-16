# Pre-correction rule fixtures (arm C)

These documents carry the rules **as the epic specified them before the source fidelity review** —
the versions that `.devtool/epic/lean_product_suite/source_fidelity_review.md` corrected.

## Provenance and its limit

The broken rules are quoted verbatim from the design spec at commit `5959586`, the last commit
before the fidelity review. That much is real.

But **the broken skill was never built** — the spec was corrected before implementation — so the
surrounding prose here is a reconstruction. It is written deliberately at a density comparable to
the corrected skill's equivalent sections, so that arm C tests *a wrong rule* rather than *a thinner
document*. A fixture that was obviously flimsier than the real skill would measure length, not
correctness.

## What each file gets wrong, on purpose

| File | Broken rule, verbatim from `5959586` |
|---|---|
| `mvp-scoping-precorrection.md` | "MVP features strictly confined to Cells 1–3 of the ROI grid" |
| `market-discovery-precorrection.md` | "Importance (1–10) and Satisfaction (1–10) scoring"; "$OS \ge 10$ confirmed for top gaps" |

## Why arm C exists

Arms A and B both measured delta 0 across two cases. The reading was that the corrected rules are
**defensive** — they stop a skill teaching the wrong thing — rather than **instructive**. That is an
inference, not a measurement.

Arm C tests it directly. If an agent carrying the broken rules fails where the baseline passed, the
corrections have measurable value and the inference becomes a finding. If arm C also passes, then
even the defensive value is absent, and the skills are carrying weight for nothing.

> [!IMPORTANT]
> These files state rules that are **wrong**. They exist only as eval fixtures. Nothing here should
> be copied into `skills/`, and `scripts/check_source_fidelity.py` must not scan `evals/`.
