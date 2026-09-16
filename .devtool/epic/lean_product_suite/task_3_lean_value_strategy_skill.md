---
id: "task_3_lean_value_strategy_skill"
status: "done"
priority: "high"
assignee: null
epic: "lean_product_suite"
dueDate: null
created: "2026-09-16T16:34:00Z"
modified: "2026-09-16T19:55:00Z"
completedAt: "2026-09-16T19:55:00Z"
labels: ["product-management", "value-proposition", "kano-model", "competitive-strategy"]
order: "c1"
---

# Task 3: Stage 2 (lean-value-strategy), Kano Framework, & Gate 2

Epic: [lean_product_suite](lean_product_suite.en.md)

## Requirement Analysis

Stage 2 sits at the interface between Problem Space and Solution Space (Chapter 5). It decides how
the product will satisfy customer needs differently and better than the alternatives. Without
differentiation and a deliberate choice of what **not** to do, products become "me-too" copies.

**Corrections carried from the [Source Fidelity Review](source_fidelity_review.md):** the prior task
scoped competitors as "Top 2–3 competitors", which lets a founder answer "we have no competitors"
and skip the exercise; and it omitted the rule that makes the grid a *strategy* rather than a wish
list — you may deliberately score **Low** on benefits you are not competing on, but you must hold
**parity** on them.

This task requires creating:

### 1. `skills/lean-value-strategy/SKILL.md`
- Frontmatter exactly `name: lean-value-strategy` + `description`.
- Persona: **Prof. Noriaki Kano & Michael Porter**. Analytical, strategic, hostile to me-too copies.
- Prerequisite check: validate `01_problem_space_spec.md` exists and contains a populated
  `Quantified Opportunity Matrix`; halt with the specific missing section named if not (BDD 5.1).
- Workflow:
  1. **Classify benefits with the Kano model** — must-haves, performance benefits, delighters —
     *in the context of the relevant competitors*, since must-haves are usually shared across a
     category and performance benefits usually overlap, while delighters differ.
  2. **Establish the competitor set.** Direct competitors, and where there are none, the customer's
     **current workaround** — pen and paper was TurboTax's competitor. An empty competitor set is
     never accepted.
  3. **Build the Value Proposition Grid** (Olsen's Table 5.4/5.5): benefits as rows grouped by Kano
     category, one column per competitor plus one for your product. Must-haves scored Yes/No;
     performance benefits High/Medium/Low, or numeric where the benefit is measurable; delighters
     one per row marked Yes where present. Key differentiators in **bold**.
  4. **Designate exactly one performance benefit to win on**, with parity — not superiority —
     required on the others. Scoring High everywhere is rejected as strategy avoidance; scoring
     deliberately Low on a non-competing benefit is permitted and encouraged.
  5. **Enumerate explicit Non-Goals** — what the product deliberately will not do.
  6. Generate the Gate 2 deliverable.

### 2. `skills/lean-value-strategy/references/kano-model-framework.md`
- The three categories with their satisfaction curves: must-haves (absence causes extreme
  dissatisfaction, presence is neutral and expected), performance (linear — more is better),
  delighters (unexpected; absence causes no dissatisfaction).
- **Migration over time**: *"Yesterday's delighters become today's performance features and
  tomorrow's must-haves"*, with Olsen's car GPS navigation example.
- **Hierarchy**: a delighter does not matter until you are competitive on performance, which does
  not matter until must-haves are met — a three-tier pyramid with must-haves at the bottom.
- Why must-haves are *required but not the core* of a value proposition: every product in the
  category has them, so they cannot differentiate.

### 3. `skills/lean-value-strategy/references/competitive-matrix-guide.md`
- Direct competitors, indirect alternatives, and non-consumption workarounds — all valid columns.
- Scoring conventions and when to use numbers instead of High/Medium/Low.
- The **win-one / hold-parity** rule, with Olsen's search-engine case: early engines competed on
  number, freshness and relevance of results; as number and freshness commoditized, relevance became
  the benefit that mattered, and Google won by being best at it **while remaining comparable or
  better on the others**.
- Reading the grid back as a differentiator statement, and the failure signature of a me-too column.

### 4. `skills/lean-value-strategy/templates/value-proposition.template.md`
Gate 2 artefact schema for `.devtool/product/<slug>/02_value_proposition_spec.md`:
`Kano Category Breakdown` · `Competitive Value Proposition Grid` (competitor columns including the
current workaround) · `Designated Performance Winner` (exactly one, with the parity commitments on
the rest) · `Core Differentiator Statement` · `Explicit Non-Goals` (3–5 minimum) ·
`Solution Space Parking Lot` (carried forward).

## Relevant Files & Context Pointers
- **Primary source**: the PDF in `docs/books/` — Chapter 5 in full (value proposition, search-engine
  case, Tables 5.1–5.5); Chapter 4's Kano section for the model itself.
- [source_fidelity_review.md](source_fidelity_review.md): corrections C10, C11 apply directly.
- [bdd_scenarios.md](bdd_scenarios.md): Scenarios 1.1, 2.3, 2.4, 2.5, 3.2, 5.1.

## Acceptance Criteria
- `skills/lean-value-strategy/SKILL.md` exists with valid two-key frontmatter and the six-step workflow.
- The skill refuses an empty competitor set and substitutes the customer's current workaround.
- The skill rejects a grid scoring the product High on every performance benefit, and requires
  exactly one designated winner plus at least one deliberate Medium or Low.
- `references/kano-model-framework.md` documents the three categories, the migration cycle, and the
  hierarchy, and states that must-haves are required but not the core of the value proposition.
- `references/competitive-matrix-guide.md` documents the win-one / hold-parity rule with the
  search-engine case.
- `templates/value-proposition.template.md` contains all six required sections.
- Prerequisite validation halts with the exact missing section named (BDD 5.1).
- `scripts/verify.sh` passes.
