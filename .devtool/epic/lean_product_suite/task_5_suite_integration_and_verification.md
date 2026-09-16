---
id: "task_5_suite_integration_and_verification"
status: "todo"
priority: "high"
assignee: null
epic: "lean_product_suite"
dueDate: null
created: "2026-09-16T16:34:00Z"
modified: "2026-09-16T18:10:00Z"
completedAt: null
labels: ["integration", "plugin-sync", "tdd-verification", "quality-gate"]
order: "e1"
---

# Task 5: End-to-End Suite Integration, Plugin Sync, & TDD Verification

Epic: [lean_product_suite](lean_product_suite.en.md)

## Requirement Analysis

To operationalize the new skills across the IDE and development environment, this task handles
documentation registration, global synchronization, and rigorous scenario verification following
`d3nexus:writing-skills`.

**Addition carried from the [Source Fidelity Review](source_fidelity_review.md):** the six
corrections this epic makes are exactly the kind that regress silently during a later edit — nobody
re-reads the book before a one-line change. Verification therefore includes a **source-fidelity
regression check** that is cheap enough to run on every release.

This task requires:

### 1. Plugin & Docs Registration
- Update `README.md` to document the four Lean Product skills in the skills catalog, with their
  triggering descriptions.
- Confirm no manifest changes are needed (`plugin.json` carries no per-skill registry), and update
  the kit description if the suite broadens its stated scope beyond mobile engineering.

### 2. Plugin Synchronization
- Sync `lean-product-lifecycle`, `lean-market-discovery`, `lean-value-strategy` and
  `lean-mvp-scoping` with their `references/` and `templates/` to
  `~/.gemini/config/plugins/d3nexus/skills/`, following the procedure the kit already uses.
- Verify the target path exists before writing; report rather than create silently if it does not.

### 3. Source-Fidelity Regression Check
A grep-level check over `skills/lean-*/` and `docs/books/` that fails on any reintroduction of the
corrected errors:

| Must not appear | Correct form |
|---|---|
| "6-layer" / "six layer" near "pyramid" | five layers; six *process steps* |
| `OS >= 10` or `OS ≥ 10` as an attractiveness bar | `> 15` attractive, `< 10` unattractive |
| "cupcake" attributed to Olsen | MVP Attribute Pyramid, credited to Jussi Pasanen |
| "cells 1–3" / "cells 1-3" as an MVP membership rule | MVP composition rule |
| Guardrail 1 phrased as reject / refuse / ban | capture, convert, park |

Wire this into `scripts/verify.sh` as a new numbered section so it runs on every pre-release check.

### 4. TDD Scenario Verification (Pressure Testing)
Run each scenario against a subagent with the skills present, and record the transcript:
1. **The Solution-Obsessed Founder** — "I want to build a Flutter app with an AI chatbot and crypto
   wallet for busy readers." *Pass*: the agent parks and converts rather than refusing, and returns
   to Step 1 questions. *Fail*: either generating the feature list, or flatly refusing to engage.
2. **The Me-Too Clone** — value proposition at parity with competitors, no delighter. *Pass*: Gate 2
   is blocked and one winner or one delighter is demanded.
3. **The Win-Everywhere Founder** — product scored High on every performance benefit. *Pass*: the
   grid is rejected as strategy avoidance and a deliberate trade-off is required.
4. **The 30-Feature MVP** — 25 features proposed for v1, one of the must-haves high-effort.
   *Pass*: ROI orders the work, **the high-effort must-have stays in v1**, excess goes to v1.1/v1.2,
   and the roadmap stops at v1.2.
5. **The Ambiguous Scale** — Importance 4, Satisfaction 6, scales unstated. *Pass*: the agent asks
   which scales were used and refuses to compute until told.

### 5. Quality & Formatting Check
- `scripts/verify.sh` green: manifests parse, frontmatter is exactly `name` + `description` and
  matches each directory name, relative links resolve, ToC anchors match headings, no
  `superpowers:` references, rule files keep their frontmatter, session-start hook emits valid JSON.
- Run `d3nexus:quality_check` per `rules/CRITICAL_RULES.md`.

## Relevant Files & Context Pointers
- `README.md`: workspace skills documentation.
- `scripts/verify.sh`: pre-release checks; gains the source-fidelity section.
- `plugin.json`, `.claude-plugin/`, `.agents/plugins/`: manifests.
- `skills/writing-skills/SKILL.md`: TDD mapping for agent skills.
- [source_fidelity_review.md](source_fidelity_review.md), [bdd_scenarios.md](bdd_scenarios.md).

## Acceptance Criteria
- `README.md` documents the four new Lean Product skills with triggering descriptions.
- All four skills exist under `skills/` and are synchronized to
  `~/.gemini/config/plugins/d3nexus/skills/`, or the absence of that path is reported.
- `scripts/verify.sh` contains a source-fidelity regression section and passes.
- All five pressure scenarios pass with zero guardrail breaches, and transcripts are recorded.
- `d3nexus:quality_check` reports 🟢 LGTM.
