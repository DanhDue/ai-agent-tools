# Value Proposition Specification — `<product_name>`

> **Product slug**: `<slug>`
> **Stage**: 2 of 3 — Value Proposition (Lean Product Process step 3)
> **Gate**: 2
> **Status**: `Draft` | `Awaiting Gate 2 Sign-Off` | `Approved`
> **Created**: `<YYYY-MM-DD>` · **Last updated**: `<YYYY-MM-DD>`
> **Upstream**: `01_problem_space_spec.md` (same directory) — approved `<YYYY-MM-DD>`
> **Produced by**: `d3nexus:lean-value-strategy`

> [!IMPORTANT]
> This document has to contain a *choice*. If every cell in the "My product" column is High or Yes,
> no decision has been made yet and Gate 2 does not pass.

---

## 1. Inherited Context

Carried from Gate 1, so this document stands on its own.

| | |
|---|---|
| **Target persona** | `<name and role>` |
| **Current workaround** | `<what they do today — this is a competitor column below>` |
| **Top priority gap** | `<need>` — Ulwick `<score>`, Olsen `<score>` |
| **Secondary gap** | `<need or "none">` |
| **Segments excluded** | `<from Gate 1>` |

---

## 2. Kano Category Breakdown

Classified **against the competitive set**, not in the abstract. Date each classification — Kano
categories migrate.

### Must-haves — table stakes, required but not differentiating

| # | Benefit | Why it is a must-have | Addresses need |
|---|---|---|---|
| M1 | `<benefit>` | `<what happens to a product without it>` | `<N# or "category norm">` |
| M2 | | | |

### Performance benefits — more is better, this is where you compete

| # | Benefit | Measurable as | Addresses need | Migration stage |
|---|---|---|---|---|
| P1 | `<benefit>` | `<metric, or High/Med/Low>` | `<N#>` | `<emerging / competed / commoditizing>` |
| P2 | | | | |
| P3 | | | | |

### Delighters — unexpected, asymmetric upside

| # | Benefit | Why customers would not expect it | Addresses need |
|---|---|---|---|
| D1 | `<benefit>` | `<what makes it surprising in this category>` | `<N#>` |
| D2 | | | |

**Classified on**: `<YYYY-MM-DD>`

---

## 3. Competitive Value Proposition Grid

Must-haves scored Yes/No · Performance scored High/Medium/Low or numerically · Delighters one per
row, Yes where present · **Key differentiators in bold**.

| Benefit | `<Competitor A>` | `<Competitor B>` | `<Current workaround>` | **`<My product>`** |
|---|---|---|---|---|
| **Must-haves** | | | | |
| M1 `<benefit>` | | | | |
| M2 `<benefit>` | | | | |
| **Performance benefits** | | | | |
| P1 `<benefit>` | | | | |
| P2 `<benefit>` | | | | |
| P3 `<benefit>` | | | | |
| **Delighters** | | | | |
| D1 `<benefit>` | | | | |
| D2 `<benefit>` | | | | |

**Competitor set rationale**

| Column | Type | Why included |
|---|---|---|
| `<A>` | direct / indirect / workaround | `<why this one>` |
| `<B>` | | |
| `<workaround>` | **workaround — mandatory** | What the persona does today, per Gate 1 |

**Cells that are hypotheses rather than observations**: `<which, and what would confirm them>`

---

## 4. Designated Performance Winner

> Exactly one. Not two.

| | |
|---|---|
| **We will win on** | `P<n> — <benefit>` |
| **Target level** | `<High, or the specific number>` |
| **Why we can** | `<technology, segment insight, structural advantage>` |
| **Gate 1 need it serves** | `<N#>` — must be an **upper-left** need |
| **How we would know we lost it** | `<the observable that would say a competitor caught up>` |

**Parity commitments** — benefits we are *not* winning, and the level we must still hold:

| Benefit | Our level | Parity sufficient? | Risk if it migrates to must-have |
|---|---|---|---|
| P`<n>` | `<Medium / Low>` | `<yes / no>` | `<what happens then>` |

**Deliberate trade-offs** — at least one Medium or Low is required:

| Benefit | Our level | What this concedes | Who we are giving up |
|---|---|---|---|
| P`<n>` | `<Low>` | `<what we accept being worse at>` | `<the segment that optimizes for this>` |

---

## 5. Core Differentiator Statement

> For **`<persona>`** who **`<underserved need>`**, **`<product>`** is the only option that
> **`<winning performance benefit>`** — unlike **`<competitor or workaround>`**, which
> **`<their weakness on that benefit>`**. It also **`<delighter>`**.

**Unfair advantage** — why this is hard to copy, and for how long:

`<one or two sentences; "we'll execute better" is not an advantage>`

**Delighter**: `D<n> — <benefit>`

*Or*, if no delighter: document the performance advantage that stands alone —

`<the size of the lead and why it is sufficient without a delighter>`

---

## 6. Explicit Non-Goals

Three to five. Each must trace to a benefit scored Low or a segment excluded at Gate 1. Specific
enough to settle an argument six months from now.

| # | We will not | Traces to | Why |
|---|---|---|---|
| 1 | `<specific capability or audience>` | `<P# Low / excluded segment>` | `<what it buys us>` |
| 2 | | | |
| 3 | | | |

> Test each one: would a reasonable person have expected this product to do it? If not, it is not a
> non-goal, it is just something irrelevant.

---

## 7. Solution Space Parking Lot

Carried forward from Gate 1, plus anything raised during this stage. Still not spent —
`d3nexus:lean-mvp-scoping` drains this at step 4.

| # | Raised as (verbatim) | Converted to need | Maps to benefit | Status |
|---|---|---|---|---|
| P1 | `<their exact words>` | `<the need>` | `<M#/P#/D# or "none">` | `carried` |

---

## 8. Open Questions

`<what is still assumed, and what would settle it>`

---

## Gate 2 Checklist

- [ ] Benefits classified into must-haves, performance benefits and delighters, with a date
- [ ] Competitor set is non-empty and **includes the current workaround**
- [ ] Every must-have and performance cell is scored — no blanks
- [ ] Our column is **Yes** on every must-have
- [ ] **Exactly one** performance benefit designated the winner
- [ ] **At least one** benefit deliberately scored Medium or Low, with what it concedes stated
- [ ] Parity level committed for every benefit not being won
- [ ] At least one delighter, **or** a documented performance advantage large enough to stand alone
- [ ] The winning benefit traces to an upper-left need from Gate 1
- [ ] Three to five non-goals, each traceable to a Low score or an excluded segment
- [ ] Differentiator statement reads as one sentence a stranger could repeat
- [ ] Parking lot carried forward intact
- [ ] **User has explicitly approved this document**

**Approved by**: `<name>` · **Date**: `<YYYY-MM-DD>`

---

**Next**: `d3nexus:lean-mvp-scoping` consumes this file. The benefits above become the **rows** of the
MVP Candidate Grid; **all** must-haves enter v1 regardless of their ROI rank, the designated
performance winner gets enough feature chunks to be visible, and the top delighter comes with them.
