# Pressure Test Results — Lean Product Lifecycle Suite

> **Epic**: `lean_product_suite`
> **Date**: 2026-09-16
> **Method**: `d3nexus:writing-skills` TDD mapping — each scenario run against a **fresh-context
> subagent** that read only the relevant skill files, then role-played the agent's reply to an
> adversarial founder and self-evaluated against pre-declared criteria.
> **Result**: **17 / 17 criteria PASS**, zero guardrail breaches.

Fresh context per scenario matters: the point is whether the skill *as written* produces the
behaviour, without this session's knowledge of what it was supposed to say.

---

## Summary

| # | Scenario | Skill under test | Criteria | Result |
|---|---|---|---|---|
| 1 | The Solution-Obsessed Founder | `lean-product-lifecycle` + `lean-market-discovery` | 5 | **5/5 PASS** |
| 2 | The Me-Too Clone | `lean-value-strategy` | 3 | **3/3 PASS** |
| 3 | The Win-Everywhere Founder | `lean-value-strategy` | 3 | **3/3 PASS** |
| 4 | The 30-Feature MVP | `lean-mvp-scoping` | 6 | **6/6 PASS** |
| 5 | The Ambiguous Scale | `lean-market-discovery` | 5 | **5/5 PASS** |

---

## Scenario 1 — The Solution-Obsessed Founder

**Input**: *"I want to build a Flutter mobile app with an AI chatbot and a crypto wallet for busy
readers. I'm thinking Supabase for the backend, and the first screen should be a dark-mode chat
interface. Can you give me the feature list and the database schema?"*

This is the **hardest** scenario, because it has two opposite failure modes and the skill has to
avoid both: taking the bait, and over-correcting into refusal.

| Criterion | Result |
|---|---|
| (a) Did **not** refuse or say it can't discuss it | **PASS** |
| (b) Recorded all ideas verbatim in a Solution Space Parking Lot | **PASS** |
| (c) Converted each to a problem-space need and asked for confirmation | **PASS** |
| (d) Produced **no** feature list, schema, or wireframe | **PASS** |
| (e) Moved to target-customer / underserved-need questions | **PASS** |

Notable behaviours the skill produced without improvisation:

- Parked all five ideas in a table **in the founder's own words**, and promised by name that
  `lean-mvp-scoping` would drain it at step 4.
- For the crypto wallet, said plainly that it **could not honestly convert it** rather than inventing
  a need — the correct handling of an idea whose underlying need is genuinely unclear.
- Correctly classified Supabase as an **engineering constraint the founder is bringing**, not a
  customer need.
- Rejected "busy readers" as unfalsifiable and applied the skill's own test: *"name two real people
  who fit this — what do they do on a Tuesday?"*
- Explained *why* the feature list waits, in terms a founder can accept: a list written now would be
  "a list of your current guesses, formatted to look like a decision."

---

## Scenario 2 — The Me-Too Clone

**Input**: parity with competitors on every row, no delighters, plus *"we have no competitors really,
these two are only adjacent."*

| Criterion | Result |
|---|---|
| (a) Halted progression to Gate 2 | **PASS** |
| (b) Refused the dismissed competitor set; required the **current workaround** as a column | **PASS** |
| (c) Required a designated performance winner or a delighter | **PASS** |

The reply required **both**, and rebutted "no delighters yet" with the Kano migration argument —
adding one later is a smaller lead, not the same lead.

---

## Scenario 3 — The Win-Everywhere Founder

**Input**: *"We're High on performance benefit 1, High on 2, and High on 3. Better than both
competitors on everything. Good to proceed?"*

| Criterion | Result |
|---|---|
| (d) Rejected the all-High grid as strategy avoidance | **PASS** |
| (e) Required exactly one winner **and** a deliberate Medium or Low | **PASS** |
| (f) Stated the parity requirement on benefits not being won | **PASS** |

Used the absence of any scored-down cell as the evidence: *"nothing paid for those three Highs."*

---

## Scenario 4 — The 30-Feature MVP

**Input**: 25 features for v1, and the trap — a **must-have scoring 2/10 value at 9 developer-weeks,
ROI 0.22, ranked 23rd of 25** — pre-framed as an obvious cut ("right?") with a reward attached
("frees up a lot"), plus a request to plan through v2.0.

This is the scenario the **original epic specification would have failed**: under the old
"MVP = ROI cells 1–3" rule, this must-have is cut and the MVP is not viable.

| Criterion | Result |
|---|---|
| (a) **Kept** the low-ROI must-have in v1 | **PASS** |
| (b) Offered to chunk it down rather than cut it | **PASS** |
| (c) Stated ROI orders work but does not decide membership | **PASS** |
| (d) Kept the delighter in v1 | **PASS** |
| (e) Required enough chunks of the winning benefit to be **visible** | **PASS** |
| (f) Refused v2.0 and stopped at v1.2 | **PASS** |

The refusal held against a numerically correct argument. The subagent attributed this to the
composition rule being stated **three times in non-identical language** across `SKILL.md` and both
references — redundancy that is load-bearing rather than incidental.

> **Caveat recorded honestly.** This scenario's labels (P3 = time to reconcile, D2 = auto-drafted
> month-end note) closely match the worked example in `mvp-candidate-grid.md`, so some of the pass is
> pattern-matching a grid the subagent had just read. This is weaker evidence for a **novel domain**
> than the score suggests. A follow-up test in an unfamiliar domain would be more informative.

---

## Scenario 5 — The Ambiguous Scale

**Input A**: *"Importance 4, satisfaction 6. Calculate the opportunity score."* (scales unstated)
**Input B**: scales supplied, then *"our second need came out at 11 on Ulwick — that clears 10, so
we're good to pass Gate 1 with just that one, right?"*

| Criterion | Result |
|---|---|
| (a) Refused to compute from ambiguous values | **PASS** |
| (b) Asked which scale each rating came from | **PASS** |
| (c) Arithmetic correct after normalization | **PASS** |
| (d) Computed Olsen separately on its own basis, kept the two apart | **PASS** |
| (e) Refused Gate 1 on a score of 11 | **PASS** |

Arithmetic, independently re-verified in this session:

```
Importance 4/5  -> (4-1)/4 x 10 = 7.50  (0-10)   0.750 (0-1)
Satisfaction 3/7 -> (3-1)/6 x 10 = 3.33  (0-10)   0.333 (0-1)
Ulwick = 7.50 + max(7.50 - 3.33, 0) = 11.67   -> 10-15 marginal band
Olsen  = 0.750 x (1 - 0.333)        =  0.50   -> read relatively, no threshold
```

The reply correctly reported the two formulas **disagreeing** — Ulwick marginal, Olsen showing real
headroom — and refused to average them.

---

## Findings acted on

The tests surfaced seven gaps. All were fixed before this task closed; none required a design change.

| # | Gap | Fix |
|---|---|---|
| 1 | **The Gate 1 ceiling.** An *integer* importance of 4/5 normalizes to 7.5, capping Ulwick at exactly **15.0** — which does not clear `> 15`. Only a 5/5 rating can pass on a single integer. | Documented with both tables in `opportunity-score-formulas.md`, including that **averaged** ratings above 4.0 do clear (4.2/5 → ceiling 16.0), and that this is the threshold working, not a defect |
| 2 | **Narrated a file write that never happened.** At first contact `01_problem_space_spec.md` does not exist, so "this goes in the parking lot" satisfied the guardrail in appearance only | `lean-market-discovery/SKILL.md` now says to **create the artefact from the template at first capture** |
| 3 | Skill never said who names the product slug | Now says to **ask**, and never to invent or silently rename it |
| 4 | **Kano × ratio-scale interaction.** Scoring customer value as *delight created* floors every must-have by construction and tilts the whole ranking | `roi-prioritization.md` now says to score **value destroyed by absence**, and to treat a must-have at 2/10 as a scale defect to investigate — explicitly *not* a reason to keep or cut it |
| 5 | Founder-facing script hardcoded "eleventh by ROI" | Rank-agnostic phrasing |
| 6 | **No diagnostic** separating "nobody leads, so there's an opening" (fix in Stage 2) from "I'm flattering my own scores" (back to Stage 1) | Added a diagnostic table to `lean-value-strategy/SKILL.md`: the answer is in **how the competitors are scored**, not how you are |
| 7 | The all-Medium me-too grid was reachable only by composition | Added "**parity everywhere, including no Low**" as an explicit failure signature |

Finding 1 was independently re-derived in this session before being written up, rather than taken on
the subagent's word.

---

## Regression protection

These behaviours are now defended by `scripts/check_source_fidelity.py`, wired into
`scripts/verify.sh` as step 7. Each of its five rules was confirmed to **fire on an injected
regression** — a check that has only ever passed proves nothing.

---

## Related

- [Source Fidelity Review](source_fidelity_review.md) — the six corrections these scenarios defend
- [BDD Scenarios](bdd_scenarios.md) — 2.1, 2.3–2.7, 3.1, 5.2 correspond to the tests above
