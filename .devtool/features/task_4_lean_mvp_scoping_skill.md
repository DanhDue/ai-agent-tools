---
id: "task_4_lean_mvp_scoping_skill"
status: "todo"
priority: "high"
assignee: null
epic: "lean_product_suite"
dueDate: null
created: "2026-09-16T16:34:00Z"
modified: "2026-09-16T16:34:00Z"
completedAt: null
labels: ["product-management", "mvp-scoping", "user-stories", "roi-matrix", "cupcake-slice"]
order: "d1"
---

# Task 4: Stage 3 (lean-mvp-scoping), 3x3 ROI Grid, & Gate 3

Epic: [lean_product_suite](lean_product_suite.en.md)

## Requirement Analysis
Stage 3 represents the core engineering bridge (Chapter 6 of Dan Olsen's book). It translates the abstract benefits defined in the Value Proposition into a tangible, minimal set of features that can be tested with real users. Most MVPs fail because teams either build a horizontal, buggy prototype (unusable) or try to build an entire roadmap at once (bloat).

This task requires creating:
1. `skills/lean-mvp-scoping/SKILL.md`:
   - YAML frontmatter: `name: lean-mvp-scoping`, `description: Use when scoping an MVP feature set, writing user stories, applying feature chunking, prioritizing backlog items with the 3x3 ROI grid, or preparing an MVP backlog for epic-designer.`
   - Persona: **Eric Ries & Jeff Patton**. Pragmatic, radical minimizer of waste, champion of small batches and story mapping.
   - Prerequisite Check: Validates existence and integrity of `02_value_proposition_spec.md` and `01_problem_space_spec.md`.
   - Workflows:
     - User story authoring (`As a [Persona], I want to [Action], so that [Benefit]`).
     - Feature chunking into atomic units.
     - 3x3 ROI matrix scoring (Value vs Effort).
     - Vertical slice (Cupcake MVP) scope boundary definition.
     - Generation of Gate 3 deliverable: `03_mvp_feature_backlog.md`.
     - Engineering handoff bridge to `d3nexus:epic-designer`.
2. `skills/lean-mvp-scoping/references/roi-3x3-matrix-rules.md`:
   - 9-cell ROI matrix layout:
     - Priority 1: High Value / Low Effort (Cell 1)
     - Priority 2: Medium Value / Low Effort (Cell 2)
     - Priority 3: High Value / Medium Effort (Cell 3)
     - Priority 4: Low Value / Low Effort (Cell 4)
     - Priority 5: Medium Value / Medium Effort (Cell 5)
     - Priority 6: High Value / High Effort (Cell 6)
     - Priority 7: Low Value / Medium Effort (Cell 7)
     - Priority 8: Medium Value / High Effort (Cell 8)
     - Priority 9: Low Value / High Effort (Cell 9 - AVOID)
   - Mandatory rule: MVP v1 candidate features must strictly be constrained to Cells 1–3.
3. `skills/lean-mvp-scoping/references/vertical-slice-guide.md`:
   - The Cupcake Principle: MVP is NOT a dry cake without frosting or a single layer of a wedding cake; it is a small, complete, delightful cupcake cutting vertically through Functional, Reliable, Usable, and Delightful.
4. `skills/lean-mvp-scoping/templates/mvp-backlog.template.md`:
   - Gate 3 artifact template for `.devtool/product/<slug>/03_mvp_feature_backlog.md` containing `Prioritized User Story Backlog`, `ROI 3x3 Grid Distribution`, `MVP v1 Scope Boundary`, and `Roadmap Backlog (v1.1, v1.2)`.

## Relevant Files & Context Pointers
- `docs/books/lean-product-roadmap.md`: Section 2 (Bước 4) and Section 3.2.
- `docs/books/lean-product-micro-skills.md`: Skill 3 specification.
- `.devtool/epic/lean_product_suite/bdd_scenarios.md`: Scenarios 1.1, 1.2, 2.3.

## Acceptance Criteria
- `skills/lean-mvp-scoping/SKILL.md` exists with Eric Ries & Jeff Patton persona and Step 4 workflows.
- `skills/lean-mvp-scoping/references/roi-3x3-matrix-rules.md` specifies the 9-cell prioritization sequence and constraints.
- `skills/lean-mvp-scoping/references/vertical-slice-guide.md` provides vertical slicing guidance.
- `skills/lean-mvp-scoping/templates/mvp-backlog.template.md` defines the Gate 3 artifact schema ready for handoff to `epic-designer`.
