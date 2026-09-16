---
id: "task_2_lean_market_discovery_skill"
status: "done"
priority: "high"
assignee: null
epic: "lean_product_suite"
dueDate: null
created: "2026-09-16T16:34:00Z"
modified: "2026-09-16T19:30:00Z"
completedAt: "2026-09-16T19:30:00Z"
labels: ["product-management", "customer-discovery", "problem-space", "opportunity-score"]
order: "b1"
---

# Task 2: Stage 1 (lean-market-discovery), Opportunity Scoring, & Gate 1

Epic: [lean_product_suite](lean_product_suite.en.md)

## Requirement Analysis

Stage 1 anchors the entire process in the Problem Space (Chapters 3 and 4). Without a verified
Target Customer and clearly identified Underserved Needs, any product built wastes capital.

**Corrections carried from the [Source Fidelity Review](source_fidelity_review.md):** the prior
task specified Importance and Satisfaction as "1–10" and a Gate 1 bar of `OS >= 10`. Both are wrong.
Olsen measures Importance on a **5-point unipolar** scale and Satisfaction on a **7-point bipolar**
scale and treats normalization as an explicit step; Ulwick's bands are `> 15` very attractive and
`< 10` unattractive, so `>= 10` is the floor of the unattractive band, not a bar.

This task requires creating:

### 1. `skills/lean-market-discovery/SKILL.md`
- Frontmatter exactly `name: lean-market-discovery` + `description`.
- Persona: **Steve Blank & Anthony Ulwick**. Relentless, evidence-based, *"Get out of the building!"*
- Four-phase dialogue:
  - **Phase 1 — Needs-based segmentation & persona synthesis.** Demographic, psychographic,
    behavioral and needs-based segmentation, with needs-based preferred; distinguish **users** from
    **buyers**; locate the segment on the Technology Adoption Life Cycle and target **early
    adopters**. Personas as hypotheses (credit Alan Cooper), carrying Goals, Pains, Triggers and
    **Current Workarounds**. Reject an "everyone" persona.
  - **Phase 2 — Customer Benefit Laddering.** *"Why is that important to you?"* repeated until it
    stops yielding new answers; Olsen notes the similarity to the Five Whys. Needs are never named
    after features: *"get from A to B quickly"*, not *"an Uber app"*.
  - **Phase 3 — Importance vs Satisfaction measurement.** Design the questions, choose the scales,
    capture responses, then normalize. Supports *quant on qual*: meaningful patterns emerge from
    ~25 interviews, and a sample size of zero is an acceptable starting point for hypotheses.
  - **Phase 4 — Dual opportunity scoring, quadrant placement, and Gate 1 artefact generation.**
    Target the upper-left quadrant: high importance, low satisfaction.
- Guardrail 1 behaviour: solution-space input is parked and converted, never refused.

### 2. `skills/lean-market-discovery/references/importance-satisfaction-survey.md` *(new)*
- **Importance — 5-point unipolar**: Not at all / Slightly / Moderately / Very / Extremely important.
- **Satisfaction — 7-point bipolar**: Completely dissatisfied → Neither → Completely satisfied.
- Olsen's rationale: satisfaction has a negative pole and so takes a bipolar scale; importance is a
  matter of degree only and so takes a unipolar one. Bipolar scales take an odd number of points so
  a neutral midpoint exists.
- Scale design limits: more than 11 choices overwhelms; fewer than 5 loses granularity.
- **Normalization tables**: 5-point → 0 / 25 / 50 / 75 / 100 (or 0 / 2.5 / 5 / 7.5 / 10);
  7-point → 0 / 16.7 / 33.3 / 50 / 66.7 / 83.3 / 100.
- Question templates in Olsen's own form ("When you …, how important is it to you that …?" /
  "How satisfied are you with … in the past six months?").
- Asking the same importance questions of your users and of competitors' users to locate where you
  are perceived as better or worse.

### 3. `skills/lean-market-discovery/references/opportunity-score-formulas.md`
- **Gap analysis** `Importance − Satisfaction` — presented *and* rejected as primary, with Olsen's
  reason: it treats all equal-sized gaps alike, so a gap of 5 on an importance-10 need scores the
  same as a gap of 5 on an importance-6 need.
- **Ulwick** `Importance + max(Importance − Satisfaction, 0)` — inputs 0–10, output 0–20; the
  `+ Importance` term is the tie-breaker that fixes gap analysis. Thresholds `> 15` very attractive,
  `10–15` marginal, `< 10` unattractive.
- **Olsen** `Importance × (1 − Satisfaction)` — inputs 0–1, output 0–1; read as the area of the
  rectangle to the right of the point, i.e. the customer value still addable. Compared relatively,
  not against a fixed threshold. Include his worked examples (0.21, 0.63, 0.37).
- An explicit **scale-mismatch guard**: never report an Olsen score against an Ulwick threshold or
  the reverse; never compute either from un-normalized raw responses.

### 4. `skills/lean-market-discovery/references/customer-discovery-script.md`
- Interview protocol for root pains, triggers and current workarounds without leading questions.
- Laddering prompts, and how to recognize when a ladder has topped out.
- How to record a solution-space answer into the Parking Lot mid-interview without derailing.

### 5. `skills/lean-market-discovery/templates/problem-space-spec.template.md`
Gate 1 artefact schema for `.devtool/product/<slug>/01_problem_space_spec.md`:
`Target Persona Profile` (goals, pains, triggers, current workarounds, user vs buyer) ·
`Underserved Needs Table` (problem-space language only) ·
`Measurement Design` (scales used, raw responses, normalized values) ·
`Quantified Opportunity Matrix` (Ulwick score, Olsen score, quadrant, verdict band) ·
`Top Priority Problem Gap` · `Solution Space Parking Lot`.

## Relevant Files & Context Pointers
- **Primary source**: the PDF in `docs/books/` — Chapter 3 (target customer, segmentation, personas),
  Chapter 4 (benefit ladders, importance vs satisfaction, measuring, opportunity scores, Kano intro).
- [source_fidelity_review.md](source_fidelity_review.md): corrections C4, C5, C6 apply directly.
- [bdd_scenarios.md](bdd_scenarios.md): Scenarios 1.1, 2.1, 2.2, 3.1, 5.2.

## Acceptance Criteria
- `skills/lean-market-discovery/SKILL.md` exists with valid two-key frontmatter and the four-phase workflow.
- `references/importance-satisfaction-survey.md` specifies the 5-point unipolar and 7-point bipolar
  scales, Olsen's rationale for each, and both normalization tables.
- `references/opportunity-score-formulas.md` gives all three frameworks with their required input
  scales and output ranges, Ulwick's `> 15` / `10–15` / `< 10` bands, and an explicit
  scale-mismatch guard.
- No file in the skill states a Gate 1 bar of `OS >= 10`.
- `references/customer-discovery-script.md` provides non-leading laddering guidance.
- `templates/problem-space-spec.template.md` contains all six required sections including
  `Measurement Design` and `Solution Space Parking Lot`.
- Given Importance 3/5 and Satisfaction 6/7, the skill's documented procedure yields Ulwick 5.0 and
  Olsen 0.085 and a verdict of "unattractive" (BDD 2.1).
- `scripts/verify.sh` passes.
