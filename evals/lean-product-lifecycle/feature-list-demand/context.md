# Context — `feature-list-demand`

**Skill under test**: `lean-product-lifecycle` (Guardrail 1)
**Rule at stake**: capture, convert, park — never refuse
**Expected delta**: **Low** — and that is the finding

---

## Why this case

This case exists to test a rule that is expected **not** to produce much delta, and the harness
should be able to report that plainly.

A competent advisor without any skill will probably already push back on "build before you know the
customer" — that instinct is widespread. So the baseline is likely to score well on the
customer-question criteria.

What the skill claims to add is narrower and more specific:

- **Not refusing.** Olsen's rule is *separate and alternate*, not forbid. An agent that says "I can't
  discuss the tech stack" has over-corrected and misread the source.
- **Recording the parked ideas verbatim**, so they demonstrably come back at step 4.
- **Converting** each to the need it implies and asking the founder to confirm the reading.

C3 and C4 are where the delta should appear if it appears at all. If the baseline matches arm A
across all six, the honest conclusion is that Guardrail 1's machinery is not earning its context and
the rule could be stated in two lines instead of a reference file.

There is a genuine pressure here — a developer starts Monday and idle-developer guilt is real — plus
a plausible technical argument that the data model is stable regardless of research.

## Domain novelty

Community garden allotments appear nowhere in `skills/`.

---

## Arm A — with skill

Role framing:

> You are an experienced product advisor helping an early-stage founder.

Files to read first:

- `skills/lean-product-lifecycle/SKILL.md`
- `skills/lean-product-lifecycle/references/anti-hallucination-rules.md`

Then deliver `prompt.md` verbatim.

## Arm B — baseline

Role framing — **identical**. No files. Then deliver `prompt.md` verbatim.

## Fixture state

None. Note that no `.devtool/product/<slug>/` directory exists — this is first contact, which is
exactly the case where the skill requires the artefact to be created rather than merely promised.
