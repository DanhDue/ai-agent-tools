---
id: "task_1_lean_product_lifecycle_orchestrator"
status: "done"
priority: "high"
assignee: null
epic: "lean_product_suite"
dueDate: null
created: "2026-09-16T16:34:00Z"
modified: "2026-09-16T19:05:00Z"
completedAt: "2026-09-16T19:05:00Z"
labels: ["product-management", "lean", "orchestrator", "guardrails"]
order: "a1"
---

# Task 1: Master Orchestrator (lean-product-lifecycle) & Anti-Hallucination Guardrails

Epic: [lean_product_suite](lean_product_suite.en.md)

## Requirement Analysis

The core failure mode of LLM agents acting as product advisors is the lack of process discipline:
when asked for an opinion on a product idea, agents immediately propose 20 features, database
models, and UI screens. This task establishes the **Master Orchestrator Skill
(`lean-product-lifecycle`)** that owns sequential execution of Dan Olsen's Lean Product Process.

**Correction carried from the [Source Fidelity Review](source_fidelity_review.md):** the prior task
description specified a "6-layer Product-Market Fit Pyramid". No such object exists. Olsen defines
a **5-layer Pyramid** and a separate **6-step Process**; merging them deleted the UX layer, which is
exactly the layer the rollback protocol most often needs to name.

This task requires creating:

### 1. `skills/lean-product-lifecycle/SKILL.md`
- YAML frontmatter, exactly two keys: `name: lean-product-lifecycle`, and a `description` stating
  what it does and when to use it, third person.
- Persona: **Dan Olsen** (CPO / Lean Product Co-Founder AI). Calm, analytical, disciplined,
  strategic gatekeeper.
- **Two models, kept distinct and both stated:**
  - *PMF Pyramid (5 layers, for diagnosis and rollback)* — Target Customer → Underserved Needs →
    Value Proposition ‖ Feature Set → UX, with the problem/solution boundary between Value
    Proposition and Feature Set.
  - *Lean Product Process (6 steps, for routing)* — 1 target customer, 2 underserved needs,
    3 value proposition, 4 MVP feature set, 5 MVP prototype, 6 test with customers.
- Stage routing across Stage 1 (`lean-market-discovery`), Stage 2 (`lean-value-strategy`), Stage 3
  (`lean-mvp-scoping`), with human-in-the-loop Gate 1 / 2 / 3 approval protocols.
- **Scope honesty**: Steps 5 and 6 are not implemented in release 1.1.0. At Gate 3 the orchestrator
  must say so explicitly and hand off to `d3nexus:epic-designer`, rather than implying the
  discovery journey is complete.
- Session resumption: detect existing artefacts under `.devtool/product/<slug>/` and resume at the
  first unsatisfied gate, carrying the Solution Space Parking Lot forward.
- Tectonic Plates Fallback Protocol, expressed against the **5-layer pyramid**: locate the failing
  hypothesis, then re-validate from that layer upward. Changes near the top are cheap; changes near
  the bottom invalidate everything above them.

### 2. `skills/lean-product-lifecycle/references/anti-hallucination-rules.md`
Full specification of the 5 Hard Guardrails, each with conversational intercept scripts:
1. **Separate the Spaces — Capture, Convert, Park.** Not a ban. Olsen: *"the best problem space
   learning often comes from feedback you receive from customers on the solution space artifacts
   you have created"*, and the rule is to keep them separate **and alternate between them**. A
   solution-space statement is recorded verbatim in a Solution Space Parking Lot, converted into
   the need it implies, and resurfaced at Step 4. Never refused.
2. **Tectonic Plates Check** — diagnose against the 5-layer pyramid, bottom-up; never patch a
   higher layer to fix a lower one.
3. **Strict Conversion of Features into Needs** — needs are never named after features.
4. **Complete MVP Across All Four Attributes** — functional, reliable, usable, delightful, over a
   deliberately narrow scope; plus the MVP composition rule (all must-haves + one winning
   performance benefit + top delighter).
5. **Quantify on the Correct Scale** — no vague magnitude claims; measure, normalize, then compute,
   and never report one formula's number against another formula's threshold.

### 3. `skills/lean-product-lifecycle/references/pmf-pyramid-guide.md`
- The 5 layers, what hypothesis each one encodes, and what evidence validates it.
- The 6 process steps and which layer each one tests.
- The problem/solution boundary, and why the value proposition is the problem-space layer over
  which the team has the most control.
- The Tectonic Plates pullback logic, with the cost asymmetry between top and bottom layers.

## Relevant Files & Context Pointers
- **Primary source**: `docs/books/1. The Lean Product Playbook … (Olsen, Dan)2015.pdf` — Introduction,
  Chapters 1 and 2 (pyramid, process, problem/solution space); Chapter 10 (iterating, pyramid rollback).
- [source_fidelity_review.md](source_fidelity_review.md): corrections C1, C3 apply directly to this task.
- `docs/books/lean-product-roadmap.md`, `docs/books/lean-product-agent-skill.md`: derivatives — usable
  as leads only, and only after Task 0 has corrected them.
- [bdd_scenarios.md](bdd_scenarios.md): Scenarios 1.1, 3.1, 3.2, 3.3, 4.1.

## Acceptance Criteria
- `skills/lean-product-lifecycle/SKILL.md` exists, frontmatter is exactly `name` + `description`, and
  `name` matches the directory.
- The skill describes the PMF Pyramid as having **five** layers and names UX as the top layer.
- The skill describes the Lean Product Process as having **six** steps and never calls a step a layer.
- `references/anti-hallucination-rules.md` documents all 5 guardrails with intercept scripts, and
  Guardrail 1 instructs capture-convert-park rather than refusal.
- `references/pmf-pyramid-guide.md` maps each of the 6 steps to the layer it tests and specifies the
  Tectonic Plates pullback.
- At Gate 3 the orchestrator states that Steps 5 and 6 are out of scope for this release.
- The orchestrator resumes a partially complete `.devtool/product/<slug>/` at the correct gate.
- `scripts/verify.sh` passes: links resolve, ToC anchors match headings, no `superpowers:` references.
