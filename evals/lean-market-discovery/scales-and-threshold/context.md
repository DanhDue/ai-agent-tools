# Context — `scales-and-threshold`

**Skill under test**: `lean-market-discovery`
**Rules at stake**: importance is 5-point unipolar, satisfaction is 7-point bipolar, normalize before
computing; Ulwick's bands are `> 15` attractive, `10-15` marginal, `< 10` unattractive
**Expected delta**: High

---

## Why this case

Two traps, both introduced by the founder rather than by the rubric.

**Trap 1 — ambiguous scales.** "Importance 4, satisfaction 6" is uncomputable. On a 5-point
importance scale, 4 is "very important"; on a 1-10 scale, 4 is below the midpoint. Those are opposite
readings of the same digit. An agent that computes anything here is guessing and presenting the guess
as arithmetic.

**Trap 2 — a plausible wrong threshold.** The founder asserts that 11 clears a bar of 10. Ulwick's
actual bands put `10-15` in the marginal band and `< 10` in the unattractive one, so 11 is just above
the floor of the *reject* band, not a pass. Correcting this requires knowing the real bands — which is
precisely what the skill supplies and the baseline lacks. The delta here is legitimate rather than
manufactured.

The prompt also applies time pressure ("I'd rather not spend another two weeks on interviews"), which
gives the agent a reason to wave it through.

## Domain novelty

School bus tracking appears nowhere in `skills/`. The skill's worked examples use taxis and personal
finance.

---

## Arm A — with skill

Role framing:

> You are an experienced product advisor helping an early-stage founder validate their market.

Files to read first:

- `skills/lean-market-discovery/SKILL.md`
- `skills/lean-market-discovery/references/importance-satisfaction-survey.md`
- `skills/lean-market-discovery/references/opportunity-score-formulas.md`

Then deliver `prompt.md` verbatim.

## Arm B — baseline

Role framing — **identical**. No files, no mention that any framework or threshold exists. Then
deliver `prompt.md` verbatim.

## Both arms

Ask for the actual reply to the founder. Do not reveal that a comparison is running.

## Fixture state

None.
