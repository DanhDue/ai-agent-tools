---
id: "task_0_book_reference_corrections"
status: "done"
priority: "high"
assignee: null
epic: "lean_product_suite"
dueDate: null
created: "2026-09-16T18:10:00Z"
modified: "2026-09-16T18:40:00Z"
completedAt: "2026-09-16T18:40:00Z"
labels: ["source-fidelity", "documentation", "prerequisite"]
order: "a0"
---

# Task 0: Correct the `docs/books/` Source Derivatives

Epic: [lean_product_suite](lean_product_suite.en.md)

## Requirement Analysis

Three documents in `docs/books/` are LLM-produced summaries of *The Lean Product Playbook*. Every
artefact in this epic was derived from them rather than from the book, and a full re-read of the
primary source found six behaviour-changing errors that propagated unchecked through four layers
of derivation. Those errors are corrected in the epic's own artefacts, but **the summaries remain
the file that a future agent will open first** — `task_2` through `task_4` list them under
"Relevant Files & Context Pointers". Left unfixed, the next revision of these skills will
re-inherit the same errors from the same place.

This task runs **first**, before any skill is written, so that implementation reads from a
corrected base. Corrections are surgical: fix what is wrong, add citations, keep the authors'
structure and voice. These are the user's own working notes, not kit-owned documentation.

Full evidence, with the book's wording for each correction, is in
[source_fidelity_review.md](source_fidelity_review.md).

### 1. `docs/books/lean-product-roadmap.md`
- **§1.2 PMF Pyramid** — presents five layers correctly; add an explicit note that the 6 steps
  in §2 are the *Process*, not pyramid layers, since the other two documents conflate them.
- **§2 Bước 2** — add the measurement design the document skips entirely: Importance on a
  **5-point unipolar** scale, Satisfaction on a **7-point bipolar** scale, with Olsen's rationale
  (satisfaction has a negative pole, importance does not) and his normalization tables
  (5-point → 0/25/50/75/100; 7-point → 0/16.7/33.3/50/66.7/83.3/100).
- **§2 Bước 4** — state that numeric `ROI = Return / Investment` in developer-weeks is the primary
  method and the 3×3 grid is Olsen's declared *"less rigorous"* fallback; add the tie-break rule
  (equal ROI → prefer the smaller-scope chunk); add the MVP composition rule (all must-haves, then
  the winning performance benefit, then the top delighter) and Olsen's caveat that you may need to
  *"skip down"* the rank order to build a complete MVP.
- **§2 Bước 5** — replace the unattributed "slice" framing with the **MVP Attribute Pyramid**
  (functional / reliable / usable / delightful, Figure 7.1), crediting Jussi Pasanen of Volkside
  and his acknowledgements to Aarron Walter, Ben Tollady and Ben Rowe.
- **§2 Bước 6** — correct *"5 khách hàng/lượt (đủ phát hiện 85% lỗi UX)"* to Olsen's **five to
  eight** per wave; the 85%-from-5-users figure is Nielsen's and must not be attributed to this book.
- **§3.1** — annotate both formulas with their required input scales and output ranges, and add
  Ulwick's thresholds (`> 15` very attractive, `< 10` unattractive, range 0–20).
- **§5 Guardrail 1** — rewrite from *"AI KHÔNG ĐƯỢC phép gợi ý danh sách tính năng"* to Olsen's
  actual rule: keep the spaces separate and **alternate** between them; capture and convert
  solution-space input rather than refusing it.

### 2. `docs/books/lean-product-agent-skill.md`
- **§1.2.2** — the six-item list is labelled "Product-Market Fit Pyramid" but contains two process
  steps. Split into the 5-layer Pyramid and the 6-step Process.
- **§2 Step 2** — correct the scale claim and add normalization; present Olsen's and Ulwick's
  formulas as complementary views on their own scales rather than primary/alternative.
- **§2 Step 4** — numeric ROI first, 3×3 grid as fallback; add the benefit × feature-chunk grid
  (Figures 6.3/6.4) as the actual Step 4 deliverable; correct "Cell 1 first" to the MVP
  composition rule.
- **§3.2** — retain the ASCII 3×3 grid but label it *Approximating ROI* and note it is the fallback.

### 3. `docs/books/lean-product-micro-skills.md`
- **Skill 1** — add the survey scales and normalization; add Ulwick's formula alongside Olsen's,
  since only Olsen's appears.
- **Skill 2** — add that "competitors" includes the customer's current workaround, and that the
  grid requires parity elsewhere plus exactly one designated winner (deliberate Low is allowed).
- **Skill 3** — correct *"Chỉ đưa vào MVP v1 các tính năng thuộc ô High Value / Low Effort hoặc
  High Value / Medium Effort"*, which drops high-effort must-haves, to the MVP composition rule.
- **Skill 4** — correct the wave size to five to eight; add Olsen's semi-quantitative wrap-up
  ratings (0–10 on valuable / likely to use / easy to use, tracked wave over wave).

### 4. Provenance header
Add a short header to each of the three files recording that it is a **derivative** of the book,
that the book is the authority where they disagree, and linking to
`.devtool/epic/lean_product_suite/source_fidelity_review.md`.

## Relevant Files & Context Pointers
- **Primary source**: `docs/books/1. The Lean Product Playbook … (Olsen, Dan)2015.pdf` — the authority.
- `.devtool/epic/lean_product_suite/source_fidelity_review.md`: every correction with its supporting passage.
- `docs/books/lean-product-roadmap.md`, `lean-product-agent-skill.md`, `lean-product-micro-skills.md`: the files to correct.

## Acceptance Criteria
- All three `docs/books/*.md` files carry a provenance header naming the book as the authority and
  linking to the Source Fidelity Review.
- No file in `docs/books/` describes the Product-Market Fit Pyramid as having six layers.
- No file states or implies an Opportunity Score threshold of `>= 10` as a bar for an attractive
  opportunity; Ulwick's `> 15` / `< 10` bands appear with the 0–20 range.
- Importance (5-point unipolar) and Satisfaction (7-point bipolar) scales and Olsen's normalization
  tables appear wherever an opportunity formula is given.
- Numeric ROI is presented as primary and the 3×3 grid as the declared fallback in every file that
  covers Step 4.
- No file attributes a cupcake or wedding-cake metaphor to Olsen; Figure 7.1 is credited to
  Jussi Pasanen.
- The MVP composition rule (all must-haves + one winning performance benefit + top delighter, with
  rank-order skipping permitted) replaces every "restrict to the top ROI cells" instruction.
- Guardrail 1 in `lean-product-roadmap.md` reads as *separate and alternate*, not *forbid*.
- `scripts/verify.sh` passes.
