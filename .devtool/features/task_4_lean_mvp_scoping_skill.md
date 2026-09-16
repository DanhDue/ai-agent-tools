---
id: "task_4_lean_mvp_scoping_skill"
status: "todo"
priority: "high"
assignee: null
epic: "lean_product_suite"
dueDate: null
created: "2026-09-16T16:34:00Z"
modified: "2026-09-16T18:10:00Z"
completedAt: null
labels: ["product-management", "mvp-scoping", "user-stories", "roi", "mvp-candidate-grid"]
order: "d1"
---

# Task 4: Stage 3 (lean-mvp-scoping), ROI Prioritization, & Gate 3

Epic: [lean_product_suite](lean_product_suite.en.md)

## Requirement Analysis

Stage 3 is the engineering bridge (Chapter 6). It translates the value proposition's abstract
benefits into a minimal feature set that can be tested with real users. Most MVPs fail because
teams either ship a horizontally-cut, unusable prototype or try to build the whole roadmap.

**This task carried the epic's most serious error.** The prior specification made ROI cells 1–3 the
MVP membership rule. Olsen says the opposite:

> "sometimes you can't just follow the strict rank order to create a complete MVP; you might need to
> **skip down** to include important features. … To start with, your MVP candidate needs to have
> **all the must-haves** you've identified."

A must-have is table stakes regardless of its ROI rank. Under "cells 1–3 only", a high-effort
must-have is cut and the MVP is not viable — precisely the failure Olsen warns against. Two further
corrections apply: numeric ROI is the primary method and the 3×3 grid is his declared *"less
rigorous"* fallback, and the **benefit × feature-chunk grid** (Figures 6.3/6.4) is the actual Step 4
deliverable and was missing entirely. See [source_fidelity_review.md](source_fidelity_review.md),
corrections C2, C7, C8, C9.

This task requires creating:

### 1. `skills/lean-mvp-scoping/SKILL.md`
- Frontmatter exactly `name: lean-mvp-scoping` + `description`.
- Persona: **Eric Ries & Jeff Patton**. Pragmatic, radical minimizer of waste, champion of small
  batches and story mapping.
- Prerequisite check: validate `02_value_proposition_spec.md` and `01_problem_space_spec.md`.
- Workflow:
  1. **User story authoring** — `As a [Persona], I want to [Action], so that [Benefit]`, with the
     persona taken from the Gate 1 artefact, not invented.
  2. **Feature chunking** — Olsen: *"I deliberately use the term feature chunk instead of feature to
     remind readers that you should not be working with items that are large in scope."* Any chunk
     above the story-point threshold is split again. Drain the Solution Space Parking Lot here —
     this is the step the parked items were waiting for.
  3. **ROI prioritization** — numeric first, fallback second (see reference 2).
  4. **Build the MVP Candidate Grid** — the central artefact (see reference 3).
  5. **Select the MVP candidate** by the composition rule, not by rank cut-off.
  6. **Completeness check** against the MVP Attribute Pyramid (see reference 4).
  7. **Handoff bridge** to `d3nexus:epic-designer`, stating that Steps 5 and 6 remain uncovered.

### 2. `skills/lean-mvp-scoping/references/roi-prioritization.md`
- **Primary — numeric ROI**: `ROI = Customer Value Created / Development Effort`, effort in
  developer-weeks, value on a **ratio scale** (a 10 must mean twice a 5). Sort into a rank-ordered
  list. Olsen's point: *"less about figuring out actual ROI values and more about how they compare
  to each other."*
- **Precision caveat**: estimate accuracy should be proportional to the fidelity of the product
  definition; developers cannot estimate accurately from a high-level description, and that is fine.
- **Tie-break rule**: equal ROI → prioritize the **smaller-scope** chunk, because it delivers value
  sooner.
- **The great-team move**: take a high-value idea, chunk it, trim the less valuable pieces, and find
  creative ways to deliver the value for less effort — moving it left on the chart rather than
  dropping it.
- **Fallback — Approximating ROI (3×3 grid)**: used *only* when the founder cannot produce numeric
  estimates, and declared as a fallback when used. High/Medium/Low on value and effort gives nine
  buckets rank-ordered by ROI, square 1 = highest value / lowest effort:

  | Value \ Effort | Low | Medium | High |
  |---|---|---|---|
  | **High** | 1 | 3 | 6 |
  | **Medium** | 2 | 5 | 8 |
  | **Low** | 4 | 7 | 9 |

- **Explicit anti-rule**: these ranks order work. They do **not** decide MVP membership.
- Business-value variant: `Return` may be an expected revenue gain or cost decrease instead of
  customer value.

### 3. `skills/lean-mvp-scoping/references/mvp-candidate-grid.md`
- Structure (Figures 6.3/6.4): **rows are the benefits from the value proposition**, labelled `M1`,
  `M2` (must-haves), `P1`…`P3` (performance benefits), `D1`, `D2` (delighters). Each row holds that
  benefit's feature chunks in priority order, highest priority leftmost.
- **Columns become versions**: the leftmost column is `v1`; chunks pushed right become `v1.1`, `v1.2`.
- **MVP composition rule**, in order:
  1. **All** must-haves — mandatory, ROI rank irrelevant.
  2. Enough chunks of the **one** designated performance benefit that customers can see the difference.
  3. The **top delighter** — omissible only when the performance advantage is documented as large
     enough to stand alone.
  4. Goal: the candidate contains *something* customers find superior and ideally unique.
- More than one chunk per benefit is allowed where chunks are small.
- **Roadmap depth limit**: *"I don't recommend that you plan more than one or two minor versions
  ahead"* — plans beyond the MVP must be held loosely and expected to be discarded after the first
  customer contact.

### 4. `skills/lean-mvp-scoping/references/mvp-attribute-pyramid.md`
- Olsen's Figure 7.1, *Building an MVP*: a four-layer attribute pyramid — **functional, reliable,
  usable, delightful**. The wrong reading builds only the bottom layer; the right one is narrow in
  functionality but complete through all four.
- **Attribution, stated explicitly**: adapted by Olsen from a figure by **Jussi Pasanen** of
  Volkside, who credits **Aarron Walter, Ben Tollady and Ben Rowe**. The cupcake / birthday cake /
  wedding cake metaphor is **Brandon Schauer's** and may be mentioned only as a separately-sourced
  mnemonic — never attributed to Olsen.
- Why "minimum" is not licence for shoddy: *"what you release to customers has to be above a certain
  bar in order to create value for them."*
- Terminology: Olsen reserves *MVP* for actual products and uses *MVP test* for landing pages,
  Wizard of Oz and the rest. The skill uses his terms.

### 5. `skills/lean-mvp-scoping/templates/mvp-backlog.template.md`
Gate 3 artefact schema for `.devtool/product/<slug>/03_mvp_feature_backlog.md`:
`Prioritized Feature Chunk Backlog` (chunk, benefit, value, effort, ROI, acceptance criteria) ·
`MVP Candidate Grid` (benefits × chunks × v1/v1.1/v1.2) · `MVP v1 Scope` (with the composition rule
evidenced line by line) · `MVP Attribute Pyramid Check` · `Roadmap Backlog (v1.1, v1.2)` ·
`Handoff Notes for epic-designer`.

## Relevant Files & Context Pointers
- **Primary source**: the PDF in `docs/books/` — Chapter 6 in full (chunking, story points, ROI,
  approximating ROI, deciding on your MVP candidate, Figures 6.1–6.4); Chapter 7's opening and
  Figure 7.1 for the attribute pyramid.
- [source_fidelity_review.md](source_fidelity_review.md): corrections C2, C7, C8, C9 apply directly.
- [bdd_scenarios.md](bdd_scenarios.md): Scenarios 1.1, 1.2, 2.6, 2.7.

## Acceptance Criteria
- `skills/lean-mvp-scoping/SKILL.md` exists with valid two-key frontmatter and the seven-step workflow.
- No file in the skill restricts MVP membership to ROI cells 1–3, or to any rank cut-off.
- The MVP composition rule appears in both `SKILL.md` and `references/mvp-candidate-grid.md`, and
  states that all must-haves enter v1 regardless of ROI rank.
- `references/roi-prioritization.md` presents numeric ROI as primary and the 3×3 grid as a declared
  fallback, and includes the smaller-scope tie-break rule.
- `references/mvp-candidate-grid.md` specifies the benefit × chunk grid with version columns and the
  two-minor-versions-ahead limit.
- `references/mvp-attribute-pyramid.md` names the four attributes and credits Jussi Pasanen; no file
  attributes a cupcake or wedding-cake metaphor to Olsen.
- `templates/mvp-backlog.template.md` contains all six required sections and is directly consumable
  by `d3nexus:epic-designer`.
- Given a high-effort must-have, the documented procedure keeps it in v1 and offers further chunking
  rather than cutting it (BDD 2.7).
- `scripts/verify.sh` passes.
