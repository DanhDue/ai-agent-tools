---
id: "task_1_lean_product_lifecycle_orchestrator"
status: "todo"
priority: "high"
assignee: null
epic: "lean_product_suite"
dueDate: null
created: "2026-09-16T16:34:00Z"
modified: "2026-09-16T16:34:00Z"
completedAt: null
labels: ["product-management", "lean", "orchestrator", "guardrails"]
order: "a1"
---

# Task 1: Master Orchestrator (lean-product-lifecycle) & Anti-Hallucination Guardrails

Epic: [lean_product_suite](lean_product_suite.en.md)

## Requirement Analysis
The core failure mode of LLM agents acting as product advisors is the lack of process discipline: when asked for an opinion on a product idea, agents immediately propose 20 features, database models, and UI screens. This task establishes the **Master Orchestrator Skill (`lean-product-lifecycle`)** that owns the sequential execution of the 6-layer Product-Market Fit Pyramid based on Dan Olsen's *The Lean Product Playbook*.

This task requires creating:
1. `skills/lean-product-lifecycle/SKILL.md`:
   - YAML frontmatter: `name: lean-product-lifecycle`, `description: Use when starting a new product discovery workflow, validating an idea against the Product-Market Fit Pyramid, or orchestrating lean product discovery across market discovery, value strategy, and MVP scoping.`
   - Persona: **Dan Olsen** (CPO / Co-Founder AI). Calm, analytical, disciplined, strategic gatekeeper.
   - Stage routing engine guiding the user across Stage 1 (`lean-market-discovery`), Stage 2 (`lean-value-strategy`), and Stage 3 (`lean-mvp-scoping`).
   - Human-in-the-loop Gate approval protocols for Gate 1, Gate 2, and Gate 3.
   - Tectonic Plates Fallback Protocol: If higher layers fail, pull the founder back down to re-validate foundational assumptions.
2. `skills/lean-product-lifecycle/references/anti-hallucination-rules.md`:
   - Full specification of the **5 Hard Guardrails**:
     1. Ban Premature Solution Space Jumping.
     2. Tectonic Plates Check (Root Cause Pullback).
     3. Strict Conversion of Features into Core Needs.
     4. Vertical Slice MVP (Cupcake Slice) Enforcement.
     5. Mathematical Quantification over Vague Qualitative Claims.
3. `skills/lean-product-lifecycle/references/pmf-pyramid-guide.md`:
   - Dan Olsen's 6-layer PMF Pyramid: Target Customer -> Underserved Needs -> Value Proposition -> MVP Feature Set -> MVP Prototype -> Customer Testing.
   - Problem Space vs. Solution Space boundary contracts.

## Relevant Files & Context Pointers
- `docs/books/lean-product-roadmap.md`: System manual with anti-hallucination rules and PMF philosophy.
- `docs/books/lean-product-agent-skill.md`: Role specification and dialogue scripts.
- `.devtool/epic/lean_product_suite/bdd_scenarios.md`: Scenarios 1.1, 3.1, 3.2, 4.1.

## Acceptance Criteria
- `skills/lean-product-lifecycle/SKILL.md` exists with valid YAML frontmatter and Dan Olsen persona instructions.
- `skills/lean-product-lifecycle/references/anti-hallucination-rules.md` explicitly documents all 5 Hard Guardrails with conversational intercept scripts.
- `skills/lean-product-lifecycle/references/pmf-pyramid-guide.md` details the 6 layers and the Tectonic Plates pullback logic.
- Master Orchestrator announces stage progression and checks gate artifacts before routing.
