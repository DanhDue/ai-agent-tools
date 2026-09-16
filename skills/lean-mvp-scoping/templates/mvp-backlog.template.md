# MVP Feature Backlog — `<product_name>`

> **Product slug**: `<slug>`
> **Stage**: 3 of 3 — MVP Feature Set (Lean Product Process step 4)
> **Gate**: 3
> **Status**: `Draft` | `Awaiting Gate 3 Sign-Off` | `Approved`
> **Created**: `<YYYY-MM-DD>` · **Last updated**: `<YYYY-MM-DD>`
> **Upstream**: `01_problem_space_spec.md`, `02_value_proposition_spec.md` (same directory)
> **Produced by**: `d3nexus:lean-mvp-scoping`
> **Downstream**: `d3nexus:epic-designer`

> [!IMPORTANT]
> **Every identified must-have is in v1, regardless of its ROI rank.** ROI orders the work; it does
> not decide membership. An MVP missing a must-have is not a cheaper product — it is not a product in
> its category.

> [!NOTE]
> Everything below is a **bundle of hypotheses**, not validated truth. Lean Product Process steps 5
> (build an MVP test) and 6 (test with customers) have not been run. Nothing here is known until
> customers see it.

---

## 1. Inherited Context

| | |
|---|---|
| **Target persona** | `<from Gate 1>` |
| **Top priority gap** | `<need>` — Ulwick `<score>` |
| **Designated performance winner** | `P<n> — <benefit>` *(from Gate 2)* |
| **Top delighter** | `D<n> — <benefit>` |
| **Must-haves** | `M1 <benefit>`, `M2 <benefit>`, … |
| **Benefits scored Low (not being built)** | `P<n> <benefit>` — expect empty rows below |
| **Non-goals** | `<from Gate 2>` |

---

## 2. User Stories

Every story names a persona from Gate 1 and a `so that` benefit present in the Gate 2 grid.

| ID | Story | Benefit |
|---|---|---|
| US-1 | As a `<persona>`, I want to `<action>`, so that `<benefit>`. | `M1` |
| US-2 | | |

---

## 3. Prioritized Feature Chunk Backlog

Chunks are atomic and estimable. Effort in developer-weeks or story points; customer value on a
**ratio scale** (a 10 means twice a 5).

**Estimation method**: `numeric ROI` | `3x3 approximation (fallback — numeric estimates unavailable)`

> If the fallback was used, say why here: `<reason>`

| Chunk | Benefit | Story | Value (0–10) | Effort (dev-wks) | **ROI** | Rank | Cell |
|---|---|---|---|---|---|---|---|
| `M1A` | M1 | US-1 | | | | | |
| `P3A` | P3 | US-4 | | | | | |
| `D2A` | D2 | US-7 | | | | | |

- **ROI** = Value / Effort. Ties break toward the **smaller-scope** chunk.
- **Cell** only applies when the 3×3 fallback was used.

**Chunks moved left** — high-value items made cheaper rather than dropped:

| Chunk | Original scope & effort | Reduced scope & effort | What was trimmed |
|---|---|---|---|
| | | | |

---

## 4. Solution Space Parking Lot — Drained

Every item captured in Stages 1 and 2 is accounted for here. **Nothing is silently dropped.**

| # | Raised as (verbatim) | Converted need | Outcome | Where it went |
|---|---|---|---|---|
| P1 | `<their exact words>` | `<the need>` | `chunked` / `deferred` / `dropped` | `<chunk ID, version, or the reason>` |

> Every row needs an outcome. `dropped` requires a reason the founder would accept if read aloud.

---

## 5. MVP Candidate Grid

Rows are **benefits**. Cells are that benefit's chunks in priority order. The **v1 column is the MVP
candidate**. Empty rows are expected — they are Gate 2's trade-offs showing up in the backlog.

| Benefit | **v1** | v1.1 | v1.2 |
|---|---|---|---|
| `M1 — <must-have>` | | | |
| `M2 — <must-have>` | | | |
| `P1 — <benefit>` | | | |
| `P2 — <benefit>` | | | |
| **`P3 — <winner>`** | | | |
| `D1 — <competitor's delighter>` | | | |
| **`D2 — <top delighter>`** | | | |

**Empty rows and why**: `<benefit — scored Low at Gate 2 / competitor's delighter, not matched>`

> Stop at v1.2. Anything further is fiction until customers have seen v1.

---

## 6. MVP v1 Scope — Composition Rule Evidence

Each clause evidenced line by line. This section is what Gate 3 is checked against.

### 1. All must-haves present, regardless of ROI rank

| Must-have | v1 chunk | ROI rank | Included despite rank? |
|---|---|---|---|
| `M1` | `M1A` | | `<yes — table stakes>` |
| `M2` | `M2A` | | |

> Any must-have **not** in v1 fails Gate 3. If one is expensive, record the chunking that made it
> affordable — not the reasoning that removed it.

### 2. Designated performance benefit, visible

| | |
|---|---|
| **Winner** | `P<n> — <benefit>` |
| **v1 chunks** | `<list>` |
| **Why this is enough for customers to see the difference** | `<argument, not assertion>` |

### 3. Top delighter

| | |
|---|---|
| **Delighter in v1** | `D<n> — <benefit>` |
| *Or*, if omitted | `<the performance advantage that stands alone, and its size>` |

### 4. Covering test

> "The goal is to make sure that your MVP candidate includes **something** that customers find
> superior to others' products and, ideally, unique."

**What in v1 would make someone switch?** `<answer plainly; "it covers the basics" is a failure>`

---

## 7. MVP Attribute Pyramid Check

Narrow in functionality, complete through all four layers. A horizontal cut fails.

| Attribute | How v1 satisfies it | Effort included in estimates? |
|---|---|---|
| **Functional** | `<the persona can complete the job end to end by …>` | |
| **Reliable** | `<what consistency means here and what it costs>` | `<yes / no>` |
| **Usable** | `<the persona gets through unaided because …>` | `<yes / no>` |
| **Delightful** | `<the delighter chunk, and what makes it remarkable>` | `<yes / no>` |

> If reliability and usability effort is not in the estimates, the ROI ranking above is built on
> happy-path numbers and needs redoing.

---

## 8. Roadmap Backlog

### v1.1
| Chunk | Benefit | Why deferred |
|---|---|---|
| | | |

### v1.2
| Chunk | Benefit | Why deferred |
|---|---|---|
| | | |

**Nothing is planned beyond v1.2.** Expect to discard these once customers see v1.

---

## 9. Handoff Notes for `d3nexus:epic-designer`

| | |
|---|---|
| **v1 chunks to build** | `<list>` |
| **Hypotheses most at risk** | `<which assumptions a build would be testing>` |
| **Not yet validated** | Steps 5 and 6 have not been run. This is a candidate, not a validated product. |
| **Known constraints** | `<runway, team size, platform, deadlines>` |
| **Non-goals carried forward** | `<from Gate 2 — these bound the technical design too>` |

---

## Gate 3 Checklist

- [ ] Every story names a Gate 1 persona and a Gate 2 benefit
- [ ] Chunks are atomic, estimable, below the story-point threshold
- [ ] Parking lot fully drained — every item chunked, deferred, or dropped **with a reason**
- [ ] ROI estimated numerically, **or** the 3×3 fallback used **and declared**
- [ ] Ties broken toward the smaller-scope chunk
- [ ] MVP Candidate Grid has benefits as rows and version columns
- [ ] **Every identified must-have is in v1, regardless of ROI rank**
- [ ] The designated performance winner carries enough chunks to be visible
- [ ] Top delighter in v1, **or** a documented performance advantage that stands alone
- [ ] The covering test is answered plainly
- [ ] All four MVP attributes addressed, with their effort in the estimates
- [ ] Roadmap stops at v1.2
- [ ] **User has explicitly approved this document**

**Approved by**: `<name>` · **Date**: `<YYYY-MM-DD>`

---

**Next**: hand this file to `d3nexus:epic-designer` for the HLD, diagrams and Kanban breakdown;
`d3nexus:epic-lifecycle` then owns the engineering gates. Separately, steps 5 and 6 of the Lean
Product Process remain outstanding — an MVP test at the lowest fidelity that can test these
hypotheses, and waves of five to eight target customers.
