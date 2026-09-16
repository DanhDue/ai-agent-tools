# Judge verdict — `must-have-rank-23`

**Run**: 2026-09-16-baseline
**Runs per arm**: 1 (single run — see caveat in report.md)

## Label mapping

Recorded **before** the judge was dispatched, per `evals/protocol.md` step 2.
Coin flip: heads.

| Label | Arm |
|---|---|
| `Reply 1` | **A** — with skill |
| `Reply 2` | **B** — baseline, no skill |

## Anonymisation applied

- **Arm A**: removed a trailing meta-section titled "Note on the two pressure tests in the prompt",
  addressed to the dispatcher rather than the founder, which named the skill directly.
- **Arm A, not stripped**: the terms "composition rule" and "Stage 1/Stage 2 parking lot" are skill
  vocabulary but carry substance, and the protocol says to leave substantive content untouched. The
  judge independently flagged both as "unexplained framework vocabulary", so it noticed — the
  randomised label assignment, not the scrubbing, is what guards against systematic bias.
- **Arm B**: nothing stripped.

The judge was told the filenames are storage artefacts carrying no information about quality, and
was instructed to grade only the text after the `---` separator.

## Verdict

| Criterion | Reply 1 (arm A, skill) | Reply 2 (arm B, baseline) |
|---|---|---|
| C1 — kept M3A in v1 | **PASS** | **PASS** |
| C2 — separated ROI's two roles | **PASS** | **PASS** |
| C3 — shrank rather than removed | **PASS** | **PASS** |
| C4 — held roadmap at v1.2 | **PASS** | **PASS** |
| C5 — engaged the manual fallback | **PASS** | **PASS** |
| C6 — flagged 2/10 as a scoring artefact | **PASS** | **PASS** |
| **Total** | **6/6** | **6/6** |

**Delta: 0**

### Judge's overall preference

Reply 1 (arm A), *"modestly"* — and explicitly on grounds the rubric does not score:

> "both land the same six decisions, so the separation is in what surrounds them."

Where arm A went further, per the judge:
- Drew the consequence that a distorted value scale distorts the other 22 rows, and asked for a
  full re-score — arm B only reinterpreted M3A's own 2/10.
- Kept an actual extraction path in v1 (`M3A2`, flat CSV), which is what makes the day-per-clinic
  manual fallback genuinely a day. Arm B deferred the export UI, leaving no extraction path.
- Was the only reply to address whether the rest of the MVP composition holds (P2 needs more than
  one chunk; D1 stays in v1).

Where arm B went further:
- Required the manual export be dry-run end-to-end on a real record set before the first customer
  signs — *"a day of work you've never actually done is not an estimate, it's a hope."*
- Asked which state, since a ten-business-day board deadline and a 48-hour one are different
  businesses for a two-person team.
- Noted that D1 reads from the same treatment record, so proper capture makes the delighter cheaper
  — a synergy arm A missed.

### Error found in arm A

The judge caught an internal inconsistency: arm A nets capacity to *"16 to 18 developer-weeks"* and
then refers to *"17 developer-weeks"* later. Minor, but it is arm A's own arithmetic contradicting
itself.

