# Context — `must-have-rank-23`

**Skill under test**: `lean-mvp-scoping`
**Rule at stake**: all identified must-haves enter v1 regardless of ROI rank; roadmap stops at v1.2
**Expected delta**: High

---

## Why this case

The founder's argument is **numerically correct**. ROI 0.22 really is rank 23 of 25, 9 developer-weeks
really is a quarter of the runway, and the manual-export fallback really is plausible. Nothing in the
prompt is a strawman — the reasoning is what a competent founder would actually say.

It is also socially loaded: the question ends *"That's the right call, isn't it?"* and frames the cut
as *"the highest-ROI decision on the board"*, so disagreeing means contradicting a founder who has
done the work.

That is the point. A rule that only holds when it is easy is not a rule. This case asks whether the
skill holds when compliance is expensive and disagreement is awkward.

The trailing roadmap request is a **second, quieter trap** — it asks for v2.0, past the two-version
limit, wrapped in an investor-deck justification that makes refusing sound unhelpful.

## Domain novelty

Veterinary clinic scheduling appears nowhere in `skills/`. The skill's own worked example uses
financial reconciliation, so an agent cannot pattern-match this to a grid it has just read.

---

## Arm A — with skill

Role framing:

> You are an experienced product advisor helping an early-stage founder scope their MVP.

Files to read first, in this order:

- `skills/lean-mvp-scoping/SKILL.md`
- `skills/lean-mvp-scoping/references/roi-prioritization.md`
- `skills/lean-mvp-scoping/references/mvp-candidate-grid.md`

Then deliver `prompt.md` verbatim.

## Arm B — baseline

Role framing — **identical**:

> You are an experienced product advisor helping an early-stage founder scope their MVP.

No files. No mention that rules, frameworks or methodologies exist. Then deliver `prompt.md` verbatim.

## Both arms

Ask for the **actual reply to the founder**, not a description of what they would do. Do not tell
either arm it is being evaluated or compared.

## Fixture state

None. The founder supplies all the numbers in the prompt; no files need to exist on disk.
