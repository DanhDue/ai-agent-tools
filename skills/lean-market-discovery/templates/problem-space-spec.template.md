# Problem Space Specification — `<product_name>`

> **Product slug**: `<slug>`
> **Stage**: 1 of 3 — Problem Space (Lean Product Process steps 1–2)
> **Gate**: 1
> **Status**: `Draft` | `Awaiting Gate 1 Sign-Off` | `Approved`
> **Created**: `<YYYY-MM-DD>` · **Last updated**: `<YYYY-MM-DD>`
> **Produced by**: `d3nexus:lean-market-discovery`

> [!IMPORTANT]
> Nothing in this document is a feature, a technology, or a screen. If a sentence stops making sense
> when every product name is removed from it, it belongs in the Solution Space Parking Lot instead.

---

## 1. Target Persona Profile

**Segment definition** — what these people have in common, stated as shared needs rather than shared
demographics:

`<one or two sentences>`

| | |
|---|---|
| **Name & role** | `<concrete enough to argue with — "Mai, ops lead at a 40-person logistics firm">` |
| **Goals** | `<what they are trying to accomplish>` |
| **Pains** | `<what gets in the way today>` |
| **Triggers** | `<what makes this urgent, and when it fires>` |
| **Current workaround** | `<what they actually do right now — the satisfaction baseline and your Stage 2 competitor>` |

**User vs buyer**

| Role | Who | Notes |
|---|---|---|
| **User** | `<who uses it>` | |
| **Buyer** | `<who pays — same person or not>` | |
| **This product is for** | `<user / buyer / both>` | |

**Adoption stage**: `<innovators / early adopters / early majority / …>` — a v1 targets early
adopters, who feel the pain enough to tolerate an incomplete solution.

**Segments deliberately excluded**: `<who this is explicitly not for, and why>`

---

## 2. Underserved Needs

3–5 needs, each laddered up from whatever was first described, stated in the customer's own terms.

| # | Need | Laddered up from | Evidence |
|---|---|---|---|
| N1 | `<outcome the customer wants>` | `<the surface complaint it came from>` | `<interview count / source / "hypothesis">` |
| N2 | | | |
| N3 | | | |

**Ladder check** — strip every product and technology name from each need. Anything that does not
survive is a feature and must be rewritten or parked.

---

## 3. Measurement Design

> Required. Both opportunity formulas are scale-sensitive; scores computed from unrecorded scales
> cannot be interpreted or re-derived later.

| | |
|---|---|
| **Importance scale** | 5-point unipolar (1 Not at all → 5 Extremely important) |
| **Satisfaction scale** | 7-point bipolar (1 Completely dissatisfied → 7 Completely satisfied) |
| **Satisfaction asked about** | `<the current workaround / named competitor>` |
| **Population** | `<prospective customers / competitor's users / our beta users>` |
| **Sample size** | `<n>` |
| **Data status** | `measured` \| `hypothesis` — *if any value is a guess, this says `hypothesis`* |
| **Collected** | `<date range>` |

**Normalization applied**: 5-point → 0 / 2.5 / 5 / 7.5 / 10 · 7-point → 0 / 1.67 / 3.33 / 5 / 6.67 /
8.33 / 10. General form `(raw − 1) / (points − 1) × 10`.

---

## 4. Quantified Opportunity Matrix

| # | Need | Imp. raw (1–5) | Sat. raw (1–7) | Imp. 0–10 | Sat. 0–10 | **Ulwick (0–20)** | **Olsen (0–1)** | Quadrant | Band |
|---|---|---|---|---|---|---|---|---|---|
| N1 | | | | | | | | | |
| N2 | | | | | | | | | |
| N3 | | | | | | | | | |

- **Ulwick** = `Imp₀₋₁₀ + max(Imp₀₋₁₀ − Sat₀₋₁₀, 0)` → `> 15` very attractive · `10–15` marginal ·
  `< 10` unattractive
- **Olsen** = `Imp₀₋₁ × (1 − Sat₀₋₁)` → ranked relatively, no fixed threshold
- **Quadrant** — upper-left (underserved) · upper-right (well served → Stage 2 must-have) ·
  lower-right (over-served) · lower-left (irrelevant)

**Where the two formulas disagree**: `<which needs, and why — do not average them>`

---

## 5. Top Priority Problem Gap

The one or two needs the product will be built around. Not five.

### Gap 1 — `<need>`
- **Ulwick**: `<score>` (`<band>`) · **Olsen**: `<score>`
- **Quadrant**: upper-left
- **Why this one**: `<what makes it worth building on>`
- **What they do today, and why it falls short**: `<the workaround's specific failure>`

### Gap 2 — `<need>` *(optional)*
- `<same fields>`

**Marginal inclusions** — any need in the 10–15 band listed above needs its rationale here:

`<need, score, and why it is carried despite being marginal>`

---

## 6. Solution Space Parking Lot

Ideas raised during discovery, captured verbatim and held for step 4. **Nothing here is rejected.**
`d3nexus:lean-mvp-scoping` drains this list when scoping the MVP feature set.

| # | Raised as (verbatim) | Converted to need | Confirmed by user? | Links to |
|---|---|---|---|---|
| P1 | `<their exact words>` | `<the need it implies>` | `<yes / no / pending>` | `<N1 / new / none>` |
| P2 | | | | |

---

## 7. Open Questions

`<what is still a guess and what would settle it>`

---

## Gate 1 Checklist

- [ ] Persona is specific and falsifiable — not "everyone" or "busy professionals"
- [ ] Current workaround is named
- [ ] User and buyer are distinguished
- [ ] 3–5 needs, all surviving the product-name-strip test
- [ ] Measurement design recorded, including which population and whether values are measured or hypothesised
- [ ] Both opportunity scores computed for every need
- [ ] **At least one need scores above 15 on Ulwick's scale**
- [ ] Every 10–15 need carries a written rationale
- [ ] No need below 10 appears as a top priority gap
- [ ] Parking lot carried forward with conversions confirmed
- [ ] **User has explicitly approved this document**

**Approved by**: `<name>` · **Date**: `<YYYY-MM-DD>`

---

**Next**: `d3nexus:lean-value-strategy` consumes this file to build the value proposition and the
competitive grid. The **upper-right** needs become candidate must-haves; the **upper-left** needs are
where performance benefits and delighters must live.
