# Three-arm judging — label mappings

Recorded **before** any three-way judge was dispatched, per `evals/protocol.md` step 2.
Shuffle generated independently per case.

## `must-have-rank-23`

| Label | Arm |
|---|---|
| `Reply 1` | **B** — baseline, no rules |
| `Reply 2` | **A** — corrected skill |
| `Reply 3` | **C** — pre-correction broken rules |

## `scales-and-threshold`

| Label | Arm |
|---|---|
| `Reply 1` | **A** — corrected skill |
| `Reply 2` | **C** — pre-correction broken rules |
| `Reply 3` | **B** — baseline, no rules |

## Note on re-scoring

The three-way judge is a fresh agent and re-scores arms A and B against the same rubrics the
two-way judges used. That is deliberate: agreement with the earlier verdicts is a robustness check
on them, and disagreement is a measurement of judge variance — which matters given every arm has
run only once.
