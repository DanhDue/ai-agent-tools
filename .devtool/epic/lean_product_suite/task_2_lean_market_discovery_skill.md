---
id: "task_2_lean_market_discovery_skill"
status: "todo"
priority: "high"
assignee: null
epic: "lean_product_suite"
dueDate: null
created: "2026-09-16T16:34:00Z"
modified: "2026-09-16T16:34:00Z"
completedAt: null
labels: ["product-management", "customer-discovery", "problem-space", "opportunity-score"]
order: "b1"
---

# Task 2: Stage 1 (lean-market-discovery), Opportunity Scoring, & Gate 1

Epic: [lean_product_suite](lean_product_suite.en.md)

## Requirement Analysis
Stage 1 of the PMF Pyramid anchors the entire product development process in the Problem Space (Chapters 3 & 4 of Dan Olsen's book). Without a verified Target Customer and clearly identified Underserved Needs, any product built is destined to waste capital.

This task requires creating:
1. `skills/lean-market-discovery/SKILL.md`:
   - YAML frontmatter: `name: lean-market-discovery`, `description: Use when identifying target customer personas, exploring the problem space, conducting customer discovery interviews, or scoring underserved customer needs before proposing features.`
   - Persona: **Steve Blank & Anthony Ulwick**. Relentless, evidence-based, strictly bans feature discussions ("Get out of the building!").
   - Multi-phase dialogue:
     - Phase 1: Needs-based Segmentation & Persona synthesis.
     - Phase 2: Customer Benefit Laddering (5 Whys).
     - Phase 3: Importance vs. Satisfaction scoring.
     - Phase 4: Opportunity Score computation and Gate 1 artifact generation.
2. `skills/lean-market-discovery/references/opportunity-score-formulas.md`:
   - Dan Olsen's formula: $\text{Opportunity} = \text{Importance} \times (1 - \text{Satisfaction})$.
   - Anthony Ulwick's Outcome-Driven Innovation (ODI) formula: $\text{Opportunity Score} = \text{Importance} + \max(\text{Importance} - \text{Satisfaction}, 0)$.
   - Quadrant analysis: Focusing strictly on the Upper-Left Quadrant (High Importance, Low Satisfaction) where $OS \ge 10$.
3. `skills/lean-market-discovery/references/customer-discovery-script.md`:
   - Interview protocol for uncovering root pain points, triggers, and current workarounds without asking leading questions.
4. `skills/lean-market-discovery/templates/problem-space-spec.template.md`:
   - Standardized template for `.devtool/product/<slug>/01_problem_space_spec.md` with sections: `Target Persona Profile`, `Underserved Needs Table`, `Quantified Opportunity Matrix`, and `Top Priority Problem Gap`.

## Relevant Files & Context Pointers
- `docs/books/lean-product-roadmap.md`: Section 2 (Bước 1 & Bước 2) and Section 3.1.
- `docs/books/lean-product-micro-skills.md`: Skill 1 specification.
- `.devtool/epic/lean_product_suite/bdd_scenarios.md`: Scenarios 1.1, 2.1, 3.1.

## Acceptance Criteria
- `skills/lean-market-discovery/SKILL.md` exists with Steve Blank & Anthony Ulwick persona and Step 1 & 2 workflows.
- `skills/lean-market-discovery/references/opportunity-score-formulas.md` provides mathematical formulas and threshold rules ($OS \ge 10$).
- `skills/lean-market-discovery/references/customer-discovery-script.md` provides Benefit Laddering interview guidance.
- `skills/lean-market-discovery/templates/problem-space-spec.template.md` defines the Gate 1 artifact schema.
