# BDD Scenarios: Lean Product Lifecycle Suite

> **Epic**: `lean_product_suite`  
> **Target Release**: `1.1.0`  
> **Framework**: Gherkin (Given - When - Then)  
> **Coverage Matrix**: 5-Dimension Boundary Testing (Happy Paths, Edge Cases, State Transitions, Session Continuity, Resilience)  

---

## 1. Dimension 1: Happy Paths

### Scenario 1.1: End-to-End Discovery Pipeline Execution
```gherkin
Given a founder with a new product idea "AI-driven personalized fitness coach"
  And no prior product artifacts exist in ".devtool/product/fitness_coach/"
When the founder invokes "lean-product-lifecycle"
Then the Master Orchestrator (Dan Olsen persona) activates and announces the session
  And transitions the founder into Stage 1 "lean-market-discovery" (Steve Blank & Anthony Ulwick persona)
  And upon completing customer discovery and benefit laddering, generates ".devtool/product/fitness_coach/01_problem_space_spec.md"
  And when Gate 1 is approved by the founder, automatically advances to Stage 2 "lean-value-strategy" (Noriaki Kano & Michael Porter persona)
  And upon establishing the Kano matrix and differentiators, generates ".devtool/product/fitness_coach/02_value_proposition_spec.md"
  And when Gate 2 is approved by the founder, automatically advances to Stage 3 "lean-mvp-scoping" (Eric Ries & Jeff Patton persona)
  And upon chunking features and prioritizing via the 3x3 ROI grid, generates ".devtool/product/fitness_coach/03_mvp_feature_backlog.md"
  And when Gate 3 is approved, provides a verified handoff bridge to "d3nexus:epic-designer".
```

### Scenario 1.2: Direct Invocation of a Single Micro-Skill with Existing Prerequisites
```gherkin
Given valid artifacts "01_problem_space_spec.md" and "02_value_proposition_spec.md" already exist in ".devtool/product/digital_wallet/"
When the founder directly invokes "lean-mvp-scoping" for "digital_wallet"
Then the skill verifies Gate 2 prerequisite compliance from "02_value_proposition_spec.md"
  And loads the target persona from "01_problem_space_spec.md"
  And assumes the Eric Ries & Jeff Patton persona without re-asking problem space questions
  And proceeds directly to User Story Chunking and 3x3 ROI prioritization.
```

---

## 2. Dimension 2: Edge Cases & Boundary Conditions

### Scenario 2.1: Insufficient Opportunity Score ($OS < 10$)
```gherkin
Given the founder evaluates a customer pain point in Stage 1
When the calculated Importance is 4 and Satisfaction is 8
Then Anthony Ulwick's formula computes Opportunity Score = 4 + max(4 - 8, 0) = 4
  And Dan Olsen's formula computes Opportunity to Add Value = 4 * (1 - 0.8) = 0.8
  And the agent warns the founder that this need is in the "Over-served / Low-Opportunity" quadrant
  And refuses to certify this need as a Top Priority Gap in "01_problem_space_spec.md"
  And guides the founder to ladder another need until a gap with OS >= 10 is identified.
```

### Scenario 2.2: "Me-Too" Clone with Zero Delighters
```gherkin
Given the founder fills the Kano table in Stage 2
When all proposed benefits match competitors at parity and no Delighter or winning Performance differentiator is identified
Then the Noriaki Kano persona halts progression to Gate 2
  And issues a Critical Alert: "A Me-Too product with zero differentiation has a 90%+ failure rate"
  And requires the founder to either identify 1 unique Delighter or narrow the target customer segment.
```

### Scenario 2.3: Overwhelming Feature Backlog (> 20 Stories Proposed)
```gherkin
Given the founder proposes 25 features for the initial launch in Stage 3
When the Eric Ries & Jeff Patton persona applies the 3x3 ROI Matrix
Then features falling into Priority Cells 4 through 9 are systematically categorized into "Post-v1 Roadmap (v1.1, v1.2)"
  And the MVP v1 scope is strictly constrained to Priority Cells 1, 2, and 3
  And the Cupcake principle is verified (100% vertical slice across Functional, Reliable, Usable, Delightful).
```

---

## 3. Dimension 3: State Transitions & Guardrails

### Scenario 3.1: Premature Jump to Solution Space (Guardrail 1 Triggered)
```gherkin
Given the agent is currently in Stage 1 "lean-market-discovery"
When the user states: "I want to use Flutter, Supabase, and build a dark-mode chat screen"
Then the agent intercepts the statement using Guardrail 1
  And responds: "That is an interesting solution, but right now we are in the Problem Space. Before discussing Flutter or UI screens, who specifically is having this problem and what job are they trying to get done?"
  And prevents any code generation or UI wireframing.
```

### Scenario 3.2: Tectonic Plates Rollback (Gate 2 Failure Triggers Stage 1 Fallback)
```gherkin
Given the founder and agent are in Stage 2 "lean-value-strategy"
When the competitive analysis reveals that all candidate differentiators are commoditized and no underserved need exists in the current segment
Then the agent executes the Tectonic Plates Fallback Protocol
  And explains that fixing the Value Proposition is impossible because the foundational layer (Target Customer / Needs) shifted
  And transitions the session back to Stage 1 "lean-market-discovery" to re-segment the market.
```

---

## 4. Dimension 4: Session Continuity & Persistence

### Scenario 4.1: Seamless Interrupted Session Resumption
```gherkin
Given a previous session generated and saved ".devtool/product/crypto_pay/01_problem_space_spec.md"
  And the session was terminated before Stage 2
When a new agent session starts and invokes "lean-product-lifecycle" for "crypto_pay"
Then the Master Orchestrator detects the existing Gate 1 artifact
  And parses the Target Persona and Top Opportunity Gaps
  And announces: "Gate 1 (Problem Space) is already verified. Resuming at Stage 2: Value Proposition Strategy."
  And smoothly transitions to Stage 2 without repeating Stage 1 questions.
```

---

## 5. Dimension 5: Failures, Corruption, & Resilience

### Scenario 5.1: Corrupted or Incomplete Prerequisite Artifact
```gherkin
Given the user invokes "lean-value-strategy"
  And ".devtool/product/health_app/01_problem_space_spec.md" exists but is missing the "Quantified Opportunity Matrix" table
When the skill validates the input contract
Then it halts with an actionable error message specifying the exact missing section
  And offers the user two options:
    | Option A: Re-run Stage 1 to complete the Opportunity Matrix |
    | Option B: Manually populate the missing section in 01_problem_space_spec.md |
```
