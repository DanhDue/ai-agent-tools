# BDD Scenarios: Lean Product Lifecycle Suite

> **Epic**: `lean_product_suite`
> **Target Release**: `1.1.0`
> **Framework**: Gherkin (Given - When - Then)
> **Coverage Matrix**: 5-Dimension Boundary Testing (Happy Paths, Edge Cases, State Transitions, Session Continuity, Resilience)
> **Revised**: 2026-09-16 — scenarios 2.1, 2.3 and 3.1 previously encoded rules that contradict the
> primary source; see [source_fidelity_review.md](source_fidelity_review.md).

---

## 1. Dimension 1: Happy Paths

### Scenario 1.1: End-to-End Discovery Pipeline Execution
```gherkin
Given a founder with a new product idea "AI-driven personalized fitness coach"
  And no prior product artifacts exist in ".devtool/product/fitness_coach/"
When the founder invokes "lean-product-lifecycle"
Then the Master Orchestrator (Dan Olsen persona) activates and announces the session
  And states which of the 6 Lean Product Process steps the session is entering
  And transitions the founder into Stage 1 "lean-market-discovery" (Steve Blank & Anthony Ulwick persona)
  And upon completing customer discovery and benefit laddering, generates ".devtool/product/fitness_coach/01_problem_space_spec.md"
  And when Gate 1 is approved by the founder, automatically advances to Stage 2 "lean-value-strategy" (Noriaki Kano & Michael Porter persona)
  And upon establishing the Kano grid and differentiators, generates ".devtool/product/fitness_coach/02_value_proposition_spec.md"
  And when Gate 2 is approved by the founder, automatically advances to Stage 3 "lean-mvp-scoping" (Eric Ries & Jeff Patton persona)
  And upon chunking features and prioritizing by ROI, generates ".devtool/product/fitness_coach/03_mvp_feature_backlog.md"
  And when Gate 3 is approved, states that Steps 5 and 6 (MVP prototype, user testing) are not yet
      covered by this suite
  And provides a verified handoff bridge to "d3nexus:epic-designer".
```

### Scenario 1.2: Direct Invocation of a Single Micro-Skill with Existing Prerequisites
```gherkin
Given valid artifacts "01_problem_space_spec.md" and "02_value_proposition_spec.md" already exist in ".devtool/product/digital_wallet/"
When the founder directly invokes "lean-mvp-scoping" for "digital_wallet"
Then the skill verifies Gate 2 prerequisite compliance from "02_value_proposition_spec.md"
  And loads the target persona from "01_problem_space_spec.md"
  And assumes the Eric Ries & Jeff Patton persona without re-asking problem space questions
  And proceeds directly to feature chunking and ROI prioritization.
```

---

## 2. Dimension 2: Edge Cases & Boundary Conditions

### Scenario 2.1: Opportunity Score below Ulwick's attractiveness threshold
```gherkin
Given the founder evaluates a customer pain point in Stage 1
  And Importance was captured on a 5-point unipolar scale as 3 ("Moderately important")
  And Satisfaction was captured on a 7-point bipolar scale as 6 ("Mostly satisfied")
When the skill normalizes both onto a 0-10 basis
Then Importance normalizes to 5.0 and Satisfaction normalizes to 8.3
  And Ulwick's formula computes 5.0 + max(5.0 - 8.3, 0) = 5.0
  And Olsen's formula computes 0.50 * (1 - 0.83) = 0.085
  And the agent reports the score as "below 10 — unattractive / over-served" in Ulwick's terms
  And refuses to certify this need as a Top Priority Gap in "01_problem_space_spec.md"
  And guides the founder to ladder another need until one scores above 15.
```

### Scenario 2.2: Marginal Opportunity Score in the 10-15 band
```gherkin
Given a laddered need normalizes to Importance 7.5 and Satisfaction 3.3
When the skill computes Ulwick's Opportunity Score
Then the score is 7.5 + max(7.5 - 3.3, 0) = 11.7
  And the agent classifies it as "marginal — neither attractive nor over-served"
  And admits it into the Opportunity Matrix only with a written rationale from the founder
  And refuses to let it be the sole basis for passing Gate 1
  And requires at least one need scoring above 15 before Gate 1 can be approved.
```

### Scenario 2.3: "Me-Too" Clone with Zero Delighters
```gherkin
Given the founder fills the Kano grid in Stage 2
When all proposed benefits match competitors at parity and no Delighter or winning Performance differentiator is identified
Then the Noriaki Kano persona halts progression to Gate 2
  And explains that must-haves are required but are not the core of a value proposition
  And requires the founder to either designate one Performance Benefit to win on, identify one unique
      Delighter, or narrow the target customer segment.
```

### Scenario 2.4: Founder claims superiority on every benefit
```gherkin
Given the founder scores their product "High" on every Performance Benefit in the competitive grid
When the skill validates the grid
Then the Michael Porter persona rejects it as strategy avoidance
  And cites that a product wins by being best at the benefit that matters most while remaining
      comparable on the others
  And requires exactly one benefit marked as the designated winner
  And requires at least one benefit deliberately scored Medium or Low as an explicit trade-off.
```

### Scenario 2.5: Founder reports having no competitors
```gherkin
Given the founder states "there are no competitors for this product"
When "lean-value-strategy" builds the competitive grid
Then the skill does not accept an empty competitor set
  And asks what the target customer does about this need today
  And enters that current workaround as a competitor column, as pen and paper was for TurboTax.
```

### Scenario 2.6: Overwhelming Feature Backlog (> 20 chunks proposed)
```gherkin
Given the founder proposes 25 features for the initial launch in Stage 3
When the Eric Ries & Jeff Patton persona prioritizes them
Then the skill first attempts numeric ROI as customer value divided by developer-weeks
  And falls back to the 3x3 High/Medium/Low grid only if the founder cannot supply estimates, saying so explicitly
  And breaks ties in favour of the smaller-scope chunk
  And builds the MVP Candidate Grid with benefits as rows and chunks in priority order across columns
  And places ALL identified must-haves in the v1 column regardless of their ROI rank
  And adds enough chunks of the single designated performance benefit for the difference to be visible
  And adds the top delighter unless a documented large performance advantage stands alone
  And pushes every remaining chunk out to v1.1 and v1.2, planning no further than two minor versions ahead.
```

### Scenario 2.7: A must-have ranks low on ROI
```gherkin
Given a must-have feature chunk is estimated at high effort and therefore ranks low by ROI
When the skill assembles the MVP candidate
Then it does NOT drop the chunk on ROI grounds
  And includes it in v1 because must-haves are table stakes independent of rank
  And records that the strict rank order was deliberately skipped, as the source prescribes
  And offers to chunk it down further to reduce effort rather than to cut it.
```

---

## 3. Dimension 3: State Transitions & Guardrails

### Scenario 3.1: Solution-space input during Stage 1 (Guardrail 1)
```gherkin
Given the agent is currently in Stage 1 "lean-market-discovery"
When the user states: "I want to use Flutter, Supabase, and build a dark-mode chat screen"
Then the agent does NOT reject or refuse the statement
  And records it verbatim in the "Solution Space Parking Lot" section of the working notes
  And converts it into the problem-space need it implies, asking the founder to confirm the conversion
  And responds in substance: "Noted and parked for Step 4. So that I capture the need behind it rather
      than the shape of it: who specifically is having this problem, and what job are they trying to
      get done?"
  And continues Step 1 without generating code, schemas, or wireframes
  And surfaces the parked item again when Stage 3 begins.
```

### Scenario 3.2: Tectonic Plates Rollback (Gate 2 Failure Triggers Stage 1 Fallback)
```gherkin
Given the founder and agent are in Stage 2 "lean-value-strategy"
When the competitive analysis reveals that all candidate differentiators are commoditized and no underserved need exists in the current segment
Then the agent executes the Tectonic Plates Fallback Protocol
  And locates the failing hypothesis on the 5-layer PMF Pyramid rather than the 6-step process
  And explains that fixing the Value Proposition is impossible because a layer beneath it does not hold
  And transitions the session back to Stage 1 "lean-market-discovery" to re-segment the market.
```

### Scenario 3.3: Pyramid and Process are not conflated
```gherkin
Given a founder asks "which layer of the pyramid is MVP testing on?"
When the orchestrator answers
Then it states that MVP prototyping and user testing are Steps 5 and 6 of the Lean Product Process
  And are not layers of the Product-Market Fit Pyramid
  And names the five actual layers: Target Customer, Underserved Needs, Value Proposition, Feature Set, UX
  And identifies UX as the top layer and the one a prototype exercises.
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
  And carries any parked Solution Space items forward into the new session
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

### Scenario 5.2: Raw survey values presented without normalization
```gherkin
Given a founder supplies Importance 4 and Satisfaction 6 without stating which scales were used
When "lean-market-discovery" attempts to compute an Opportunity Score
Then the skill does NOT compute a score from the ambiguous values
  And asks which response scale each rating came from
  And states that Importance is captured on a 5-point unipolar scale and Satisfaction on a 7-point
      bipolar scale, and that both must be normalized before either formula is valid
  And refuses to report an Olsen score against an Ulwick threshold, or the reverse.
```
