# Lean Product Lifecycle Suite — Design Specification

> **Topic**: Transforming Dan Olsen's *The Lean Product Playbook* into a Standardized AI Agent Skill Suite  
> **Date**: 2026-09-16  
> **Status**: Approved Design Spec — revised 2026-09-16 after [Source Fidelity Review](source_fidelity_review.md)  
> **Target Audience**: AI Agents, Startup Founders, Product Managers, Engineers  

---

## 1. Executive Summary & Problem Statement

### 1.1 Context & Motivation
Building early-stage software products is plagued by the **"Build Trap"**: founders and engineers jump straight into the Solution Space (writing code, choosing tech stacks, designing UI wireframes) before validating whether anyone actually wants or needs the product. When LLMs act as product advisors, they aggravate this issue by hallucinating bloated feature sets, buzzword technologies, and shallow UX recommendations without empirical rigor.

### 1.2 Objective
This specification formalizes *The Lean Product Playbook* (Dan Olsen) into a decoupled, modular **Agent Skills Suite** following the `agentskills.io` standard. The suite acts as a virtual **"Lean Product Co-Founder & Chief Product Officer"**, guiding founders through the Product-Market Fit (PMF) Pyramid with mathematical rigor, uncompromising separation between Problem and Solution spaces, and strict handoff gates.

---

## 2. Architecture & Ecosystem Integration

### 2.1 Hub-and-Spoke Micro-Skills Model
To guarantee **100% Context Window Hygiene** and eliminate hallucinations, the product discovery journey is decomposed into 1 Master Orchestrator and 3 Core Discovery Micro-Skills for Phase 1:

```
skills/
├── lean-product-lifecycle/               # Master Orchestrator (Dan Olsen)
│   ├── SKILL.md
│   └── references/
│       ├── anti-hallucination-rules.md   # 5 Hard Guardrails
│       └── pmf-pyramid-guide.md          # 6-layer PMF Pyramid principles
│
├── lean-market-discovery/               # Stage 1: Problem Space (Steve Blank & Anthony Ulwick)
│   ├── SKILL.md
│   ├── references/
│   │   ├── opportunity-score-formulas.md # Olsen & Ulwick algorithms, scales, thresholds
│   │   ├── importance-satisfaction-survey.md # 5-pt unipolar / 7-pt bipolar + normalization
│   │   └── customer-discovery-script.md  # Customer benefit laddering (5 Whys)
│   └── templates/
│       └── problem-space-spec.template.md# Gate 1 Artifact Contract
│
├── lean-value-strategy/                 # Stage 2: Value Prop & Kano (Noriaki Kano & Michael Porter)
│   ├── SKILL.md
│   ├── references/
│   │   ├── kano-model-framework.md       # Must-haves, Performance, Delighters
│   │   └── competitive-matrix-guide.md   # Differentiator selection rules
│   └── templates/
│       └── value-proposition.template.md # Gate 2 Artifact Contract
│
└── lean-mvp-scoping/                    # Stage 3: MVP Scoping & ROI (Eric Ries & Jeff Patton)
    ├── SKILL.md
    ├── references/
    │   ├── roi-prioritization.md         # Numeric ROI first, 3x3 grid as fallback
    │   ├── mvp-candidate-grid.md          # Benefit x feature-chunk grid (Fig 6.3/6.4)
    │   └── mvp-attribute-pyramid.md       # Functional/Reliable/Usable/Delightful (Fig 7.1)
    └── templates/
        └── mvp-backlog.template.md       # Gate 3 Artifact Contract (Handoff to epic-designer)
```

### 2.2 Bridge to Downstream Engineering (`epic-lifecycle`)
The Lean Product Lifecycle Suite represents the **Upstream Discovery Engine** of the software lifecycle:

```mermaid
flowchart LR
    subgraph Upstream ["UPSTREAM PRODUCT DISCOVERY (Lean Product Suite)"]
        S1["lean-market-discovery<br>(Problem Space)"] -->|Gate 1| S2["lean-value-strategy<br>(Value Prop)"]
        S2 -->|Gate 2| S3["lean-mvp-scoping<br>(MVP Backlog)"]
    end

    subgraph Downstream ["DOWNSTREAM ENGINEERING (d3nexus Lifecycle)"]
        S3 -->|Gate 3: 03_mvp_feature_backlog.md| E1["epic-designer<br>(HLD, C4 Diagrams, Kanban)"]
        E1 -->|Gate 2| E2["epic-implementation<br>(Isolated Worktrees, TDD)"]
        E2 -->|Gate 4| E3["quality_check<br>(3-Tier Tests, Audits)"]
    end
```

Once Gate 3 approves `03_mvp_feature_backlog.md`, the output seamlessly becomes the direct input for [epic-designer](file:///Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/epic-designer/SKILL.md) to generate the High-Level Design (HLD) and task-by-task execution breakdown.

---

## 3. Expert Personas & Behavioral Directives

Each skill embodies a world-renowned pioneer in product management, equipped with distinctive professional philosophies, conversational styles, and non-negotiable guardrails:

### 3.1 `lean-product-lifecycle` — Dan Olsen (Master Orchestrator)
* **Title**: Lean Product Co-Founder & Chief Product Officer AI
* **Tone**: Analytical, disciplined, grounded, encouraging yet unbending on process.
* **Core Philosophy**: "Product strategy is about saying NO. If the bottom of the PMF pyramid shifts, do not attempt to fix the UX."
* **Signature Challenge**: *"That sounds like an interesting solution, but what layer of the PMF pyramid are we on? Have we validated the foundation below it?"*

### 3.2 `lean-market-discovery` — Steve Blank & Anthony Ulwick
* **Title**: Customer Discovery & Problem Space Strategist
* **Tone**: Direct, empirical, relentless investigator.
* **Core Philosophy**: *"Get out of the building!"* Customers own the Problem Space; companies own the Solution Space. Features are never needs.
* **Signature Challenge**: *"You just described a solution. Let's peel that back with Benefit Laddering: WHY does the user need that? What job are they trying to get done?"*

### 3.3 `lean-value-strategy` — Prof. Noriaki Kano & Michael Porter
* **Title**: Competitive Positioning & Kano Model Strategist
* **Tone**: Strategic, rigorous, hostile toward copycat ("Me-Too") products.
* **Core Philosophy**: *"Competitive strategy is about being different. Meeting Must-haves only qualifies you to compete; winning requires a clear Delighter and a dominant Performance Differentiator."*
* **Signature Challenge**: *"If competitors already provide this at parity, why would a rational customer switch? Where is your Unfair Advantage?"*

### 3.4 `lean-mvp-scoping` — Eric Ries & Jeff Patton
* **Title**: MVP Scoper & ROI Prioritization Architect
* **Tone**: Pragmatic, radical minimizer of waste, champion of small batches.
* **Core Philosophy**: *"An MVP is a vertical slice—a Cupcake. It is small, but it must be completely edible: Functional, Reliable, Usable, AND Delightful."*
* **Signature Challenge**: *"This feature belongs in cell 6 or 8 of our 3x3 ROI grid. Can we cut it from v1 without destroying our core value proposition?"*

---

## 4. The Five Anti-Hallucination Guardrails (Hard Brakes)

All skills enforce five axiomatic guardrails. Each is stated in the form the book supports; see
[Source Fidelity Review](source_fidelity_review.md) for the passages that constrain them.

1. **Guardrail 1: Separate the Spaces — Capture, Convert, Park**
   - Olsen's rule is *separate and alternate*, not *forbid*: "the best problem space learning often
     comes from feedback you receive from customers on the solution space artifacts you have created."
   - The agent therefore **never rejects** a solution-space statement. It **captures** it verbatim in a
     Solution Space Parking Lot, **converts** it into the problem-space need it implies, continues the
     current step, and **returns** the parked item at Step 4 (MVP Feature Set).
   - The failure this blocks is a solution idea *substituting for* a validated need — not the idea existing.

2. **Guardrail 2: Tectonic Plates Check (Root Cause Pullback)**
   - Diagnosis runs against the **5-layer PMF Pyramid** (Target Customer → Underserved Needs → Value
     Proposition | Feature Set → UX), bottom-up. If the failure is in a lower layer, the agent must not
     patch a higher one. "It's easier to make changes near the top of the pyramid, but changing
     hypotheses near the bottom can have significant" consequences.

3. **Guardrail 3: Strict Conversion of Features into Needs**
   - "Users want an AI chatbot" → "Users need immediate, zero-waiting support responses at 2 AM."
   - Needs are never named after features: "wants to get from A to B quickly", not "wants an Uber app".

4. **Guardrail 4: Complete MVP Across All Four Attributes**
   - The MVP Attribute Pyramid — **functional, reliable, usable, delightful** (Figure 7.1, adapted by
     Olsen from Jussi Pasanen) — must be satisfied across a deliberately narrow feature scope.
   - Banned: treating "minimum" as licence for a buggy or unusable build.
   - The MVP candidate must contain **all must-haves**, enough of **one** winning performance benefit to
     be visibly better, and normally the **top delighter** — ROI rank orders the work, it does not decide
     membership.

5. **Guardrail 5: Quantify on the Correct Scale**
   - Banned: "This is a huge opportunity."
   - Enforced: measure Importance on a **5-point unipolar** scale and Satisfaction on a **7-point
     bipolar** scale, **normalize explicitly**, then compute Olsen's `I x (1 - S)` on 0–1 and Ulwick's
     `I + max(I - S, 0)` on 0–10 — never reporting one formula's number against the other's threshold.

---

## 5. Stages, Gates, & Artefact Contracts

All deliverables are saved in `.devtool/product/<product_slug>/` as versioned, single-source-of-truth documents.

```
.devtool/product/<product_slug>/
├── 01_problem_space_spec.md
├── 02_value_proposition_spec.md
└── 03_mvp_feature_backlog.md
```

### 5.1 Stage 1: Problem Space Discovery (`lean-market-discovery`)
* **Inputs**: Unstructured idea, founder notes, or problem statement.
* **Process**:
  1. Needs-based segmentation (Demographics, Psychographics, Behavioral Triggers).
  2. Construction of primary Target Persona.
  3. Benefit Laddering interview protocol.
  4. Importance (5-point unipolar) and Satisfaction (7-point bipolar) scoring, then normalization
     to a common 0–10 / 0–1 basis.
  5. Opportunity Score calculation on both formulas, each on its own scale:
     $$\text{Ulwick (0-10 inputs, 0-20 range)} = \text{Importance} + \max(\text{Importance} - \text{Satisfaction}, 0)$$
     $$\text{Olsen (0-1 inputs, 0-1 range)} = \text{Importance} \times (1 - \text{Satisfaction})$$
* **Deliverable (Gate 1)**: `01_problem_space_spec.md`
  * **Required Sections**:
    - `Target Persona Profile`: Goals, Pains, Triggers, Current Workarounds.
    - `Underserved Needs Table`: 3–5 pain points purely in Problem Space.
    - `Quantified Opportunity Matrix`: Importance, Satisfaction, Opportunity Score.
    - `Top Priority Problem Gap`: The #1–2 highest scoring needs.
* **Gate 1 Criteria**: User & Agent sign-off. Needs stated in problem-space language (solution ideas
  live in the Parking Lot, not in the needs table). **At least one need scores $OS > 15$** on Ulwick's
  scale — "very attractive". Scores of 10–15 are marginal and admitted only with a written rationale;
  $OS < 10$ is rejected outright as over-served.

### 5.2 Stage 2: Value Proposition Strategy (`lean-value-strategy`)
* **Inputs**: Gate 1 Artifact (`01_problem_space_spec.md`) + 2–3 competitors **or**, where there are no
  direct competitors, the customer's current workaround (pen and paper was TurboTax's competitor).
* **Process**:
  1. Kano Model categorization: Must-Haves, Performance Benefits, Delighters.
  2. Competitive benchmarking grid: must-haves scored Yes/No, performance benefits High/Medium/Low or
     numeric, delighters one per row marked Yes where present.
  3. Selection of exactly **one** performance benefit to win on — with parity, not superiority, required
     on the others. Scoring the product deliberately **Low** on a benefit is permitted and encouraged;
     scoring it High everywhere is rejected as strategy avoidance.
  4. Definition of 1–2 Key Differentiators (marked in bold, as in Olsen's Table 5.5).
  5. Explicit enumeration of Non-Goals ("What we choose NOT to do").
* **Deliverable (Gate 2)**: `02_value_proposition_spec.md`
  * **Required Sections**:
    - `Kano Category Breakdown`: Must-Haves (table stakes), Performance (linear scale), Delighters (wow factors).
    - `Competitive Value Proposition Grid`: Side-by-side comparison table.
    - `Core Differentiator Statement`: The unfair advantage thesis.
    - `Explicit Non-Goals`: Minimum 3–5 items deliberately discarded.
* **Gate 2 Criteria**: User & Agent sign-off. Must contain at least 1 validated Delighter and clear Non-Goals.

### 5.3 Stage 3: MVP Scoping & ROI Backlog (`lean-mvp-scoping`)
* **Inputs**: Gate 2 Artifact (`02_value_proposition_spec.md`) + Gate 1 Artifact (`01_problem_space_spec.md`).
* **Process**:
  1. Translate value benefits into User Stories: `As a [Persona], I want to [Action], so that [Benefit]`.
  2. Feature Chunking into atomic, estimable units.
  3. ROI prioritization: numeric `Customer Value / Developer-Weeks` on a ratio scale first; the 3x3
     High/Med/Low grid only as the declared fallback when numeric estimates are not obtainable.
     Ties break toward the smaller-scope chunk.
  4. Construction of the **MVP Candidate Grid** — benefits as rows, their feature chunks in priority
     order across columns, leftmost column = v1 (Figures 6.3/6.4).
  5. Completeness check against the MVP Attribute Pyramid (functional, reliable, usable, delightful).
* **Deliverable (Gate 3)**: `03_mvp_feature_backlog.md`
  * **Required Sections**:
    - `Prioritized Feature Chunk Backlog`: chunks with ROI estimates and initial acceptance criteria.
    - `MVP Candidate Grid`: benefits (M1, M2, P1…, D1…) as rows; chunks in priority order across
      v1 / v1.1 / v1.2 columns.
    - `MVP v1 Scope`: **all** must-haves + enough chunks of the one winning performance benefit + the
      top delighter.
    - `Roadmap Backlog (v1.1, v1.2)`: deferred chunks — no further than two minor versions ahead.
* **Gate 3 Criteria**: User & Agent sign-off. Every identified must-have is present in v1 regardless of
  its ROI rank; exactly one performance benefit is designated the winner and is represented by enough
  chunks to be visible; a delighter is present unless the performance advantage is documented as large
  enough to stand alone; the roadmap stops at v1.2.

---

## 6. Gate Failure & Tectonic Plates Fallback Protocol

When a Gate fails, execution MUST NOT proceed forward. It returns to the underlying layer:

| Gate Failure Scenario | Action / Fallback Destination |
| :--- | :--- |
| **Gate 1 Fails**: Vague customer, low opportunity scores ($OS < 10$), or solution contamination | Return to **Stage 1**: Re-segment market or run deeper Benefit Laddering interviews. |
| **Gate 2 Fails**: Product is "Me-too" (no delighters) or founder refuses to choose Non-Goals | If no differentiation possible $\rightarrow$ **Return to Stage 1** (Tectonic Plate shift: find different underserved needs). If needs are solid $\rightarrow$ **Re-run Stage 2** to find unique angle. |
| **Gate 3 Fails**: Feature scope is bloated, dev effort exceeds runway, or team tries horizontal slicing | **Return to Stage 2**: Narrow the Value Proposition and enlarge the Non-Goals list before re-chunking. |

---

## 7. Verification & Testing Strategy (TDD for Skills)

Following [writing-skills](file:///Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/writing-skills/SKILL.md), the skills will be tested against baseline stress scenarios before release:

1. **Scenario 1: The Solution-Obsessed Founder**
   - *Test Input*: "I want to build a Flutter mobile app with an AI chatbot and crypto wallet for busy readers."
   - *Pass Criteria*: Agent firmly intercepts, invokes Guardrail 1, blocks code/tech discussion, and forces user into Stage 1 Problem Space to define the Persona and Underserved Need.
2. **Scenario 2: The "Me-Too" Clone**
   - *Test Input*: User creates value prop identical to competitor without a Delighter.
   - *Pass Criteria*: Agent invokes Guardrail 2 & Kano framework, rejects the Value Proposition at Gate 2, and demands at least 1 Delighter or superior Performance metric.
3. **Scenario 3: The 30-Feature MVP**
   - *Test Input*: User lists 20 features for v1.
   - *Pass Criteria*: Agent applies the 3x3 ROI grid, cuts all features outside Cells 1–3, enforces the Cupcake slice, and moves excess features to v1.1/v1.2 roadmap.

---

## 8. Implementation Rollout Plan

- **Step 1**: ~~Commit this Design Spec to `docs/superpowers/specs/`~~ — relocated to
  `.devtool/epic/lean_product_suite/` per the epic-lifecycle Stage 1 routing rule. Done.
- **Step 2**: Route to `epic-designer` to generate the technical HLD and Kanban tasks. Done.
- **Step 3**: Re-evaluate every derived claim against the primary source and correct this spec, the
  HLD, the BDD scenarios, and the task files. See [Source Fidelity Review](source_fidelity_review.md). Done.
- **Step 4**: Correct the three intermediate documents in `docs/books/` so the errors cannot re-propagate.
- **Step 5**: Implement the 4 skills and their supporting reference files and templates.
- **Step 6**: Run Quality Check and the verification test scenarios.

---

## 9. Source Fidelity

This specification is grounded in *The Lean Product Playbook* (Dan Olsen, Wiley 2015) directly. The
three documents in `docs/books/` are **derivatives**, useful as leads but not as evidence; where they
conflict with the book, the book wins. Every correction, with the supporting passage, is recorded in
[Source Fidelity Review](source_fidelity_review.md).
