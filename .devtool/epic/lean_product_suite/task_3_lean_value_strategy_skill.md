---
id: "task_3_lean_value_strategy_skill"
status: "todo"
priority: "high"
assignee: null
epic: "lean_product_suite"
dueDate: null
created: "2026-09-16T16:34:00Z"
modified: "2026-09-16T16:34:00Z"
completedAt: null
labels: ["product-management", "value-proposition", "kano-model", "competitive-strategy"]
order: "c1"
---

# Task 3: Stage 2 (lean-value-strategy), Kano Framework, & Gate 2

Epic: [lean_product_suite](lean_product_suite.en.md)

## Requirement Analysis
Stage 2 sits at the interface between the Problem Space and the Solution Space (Chapter 5 of Dan Olsen's book). It determines how the product will satisfy customer needs differently and better than existing market alternatives. Without clear differentiation and a deliberate choice of what NOT to do, products become generic copycats ("Me-Too" traps).

This task requires creating:
1. `skills/lean-value-strategy/SKILL.md`:
   - YAML frontmatter: `name: lean-value-strategy`, `description: Use when defining the product value proposition, categorizing features with the Kano model, evaluating competitors, or identifying unique differentiators and non-goals.`
   - Persona: **Prof. Noriaki Kano & Michael Porter**. Analytical, strategic, hostile to "Me-Too" copies ("Competitive strategy is about being different").
   - Prerequisite Check: Validates existence and integrity of `01_problem_space_spec.md`.
   - Workflows:
     - Benefit classification into Must-Haves, Performance Benefits, and Delighters.
     - Construction of the Competitive Value Proposition Grid.
     - Selection of 1–2 Key Differentiators.
     - Definition of explicit Non-Goals.
     - Generation of Gate 2 deliverable: `02_value_proposition_spec.md`.
2. `skills/lean-value-strategy/references/kano-model-framework.md`:
   - Mathematical/visual explanation of the Kano Model: Must-Haves (dysfunctional if missing, neutral if present), Performance (linear scale), Delighters (exponential delight, unexpected).
   - Dynamic decay principle: Delighters naturally transition into Performance benefits, then into Must-haves over time.
3. `skills/lean-value-strategy/references/competitive-matrix-guide.md`:
   - Framework for evaluating direct and indirect competitors, scoring parity vs superiority, and formulating a defensible Unfair Advantage.
4. `skills/lean-value-strategy/templates/value-proposition.template.md`:
   - Gate 2 artifact template for `.devtool/product/<slug>/02_value_proposition_spec.md` containing `Kano Categories Breakdown`, `Competitive Value Proposition Grid`, `Core Differentiator Statement`, and `Explicit Non-Goals`.

## Relevant Files & Context Pointers
- `docs/books/lean-product-roadmap.md`: Section 2 (Bước 3) and Section 3.3.
- `docs/books/lean-product-micro-skills.md`: Skill 2 specification.
- `.devtool/epic/lean_product_suite/bdd_scenarios.md`: Scenarios 1.1, 2.2, 3.2, 5.1.

## Acceptance Criteria
- `skills/lean-value-strategy/SKILL.md` exists with Noriaki Kano & Michael Porter persona and Step 3 workflows.
- `skills/lean-value-strategy/references/kano-model-framework.md` details Kano categories and the decay cycle.
- `skills/lean-value-strategy/references/competitive-matrix-guide.md` details competitive grid construction and differentiator rules.
- `skills/lean-value-strategy/templates/value-proposition.template.md` defines the Gate 2 artifact schema.
