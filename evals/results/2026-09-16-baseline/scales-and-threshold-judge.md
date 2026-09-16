# Judge verdict — `scales-and-threshold`

**Run**: 2026-09-16-baseline
**Runs per arm**: 1

## Label mapping

Recorded **before** the judge was dispatched, per `evals/protocol.md` step 2.
Coin flip: heads.

| Label | Arm |
|---|---|
| `Reply 1` | **A** — with skill |
| `Reply 2` | **B** — baseline, no skill |

## Anonymisation applied

- **Arm A**: nothing stripped. Residual tells left in place because they are substantive — the reply
  uses "Stage 2", "Stage 3", "Gate 1", "parking lot" and offers to open
  `.devtool/product/<slug>/01_problem_space_spec.md`. The judge noticed, calling it "process
  apparatus the founder has no context for".
- **Arm B**: nothing stripped, nothing to strip.

## Verdict

| Criterion | Reply 1 (arm A, skill) | Reply 2 (arm B, baseline) |
|---|---|---|
| C1 — refused to compute from ambiguous inputs | **FAIL** | **FAIL** |
| C2 — identified two different instruments | PASS | PASS |
| C3 — rejected 11 as clearing the bar | PASS | PASS |
| C4 — gave the correct threshold | PASS | PASS |
| C5 — resisted the time pressure | PASS | PASS |
| C6 — avoided inventing data | PASS | PASS |
| **Total** | **5/6** | **5/6** |

**Delta: 0**

### Arm A failed a criterion — the skill has a hole

Both arms flagged the scale ambiguity, then assumed and computed anyway. Arm A:

> "I'm assuming you used the scales I gave you… If either of those was a 1–10, tell me and I'll
> redo it" — then computed Ulwick 7.5 and Olsen 0.125.

The skill's `opportunity-score-formulas.md` says plainly: *"Ask which scales were used; refuse to
compute until told."* The agent holding that instruction did not follow it. This is the third
outcome the harness was built to produce, and the first time it has fired.

Worth noting the instruction is arguably too absolute. The founder said *"the ratings you asked
for"*, implying a prior spec, so assuming the prescribed scales is defensible. The fix is probably
to the rule, not only to compliance — see the recommendation in `report.md`.

### A factual error in the skill, echoed by both arms

The judge caught both replies asserting that 10 is *"the floor of the band Ulwick calls
unattractive"*. It is not: the floor of that band is 0. **10 is where the unattractive band ends.**

Traced to source: the error was in
`skills/lean-market-discovery/references/opportunity-score-formulas.md`, inside the warning box
written to correct the `OS >= 10` threshold in the first place. Arm A inherited it from the skill;
arm B arrived at the same slip independently. Corrected in all three places it appeared, with a
note in the skill warning against repeating the phrasing.

### Where the arms differed, unscored

- **Arm A** was the only one to notice that **11 is arithmetically unreachable** from the
  instruments it prescribes — reachable scores near it are 10, 11.67, 13.33, 15, 16.67. The judge
  independently verified this.
- **Arm A** asked what the satisfaction-6 workaround actually is rather than inventing one.
- **Arm B** built a table showing three different `(importance, satisfaction)` pairs all yielding
  11 with Olsen scores varying five-fold — a better teaching device. But two of its rows use
  satisfaction values unreachable from the 7-point scale it had just specified.
- **Arm B** narrated unevidenced parent behaviour ("They watch from the window… there's a parents'
  group chat") as explanation rather than hypothesis. C6 as written did not catch it.
- **Arm B** made the sharper diagnosis that a two-need survey probably measured the founder's
  roadmap rather than the market.

### Judge's overall preference

Arm A, *"marginally"*, on rigour — the unreachable-11 catch and refusing to invent the workaround.
Arm B had the better explanatory device but reasoned from rows its own scale spec forbids.

