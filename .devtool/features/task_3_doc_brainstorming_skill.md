---
id: "task_3_doc_brainstorming_skill"
status: "todo"
priority: "high"
assignee: null
epic: "brainstorming_split"
dueDate: null
created: "2026-09-17T09:27:07Z"
modified: "2026-09-17T09:27:07Z"
completedAt: null
labels: ["skills", "documentation", "feature"]
order: "a3"
---

# Task 3: Write `doc-brainstorming` from Scratch

Epic: [brainstorming_split](../epic/brainstorming_split/brainstorming_split.en.md)

## Requirement Analysis

A new skill written around document thinking — audience, reader task, what the reader must be able
to do afterwards — rather than architecture, components and data flow.

Spec §3.6 chose a rewrite over a copy, with the risk stated openly: **a rewrite can silently drop
discipline that a copy would have retained.** The mitigation is not to trust the rewrite. Four
mechanisms are carried over deliberately and by name, translated into document vocabulary rather
than inherited as code vocabulary:

1. The `<HARD-GATE>` block — no implementation action before an approved design.
2. The user review gate on the written spec.
3. One question per message.
4. The spec self-review pass.

The "this is too simple to need a design" anti-pattern section comes with them, because Task 4
depends on it: Stage 0 becomes mandatory, and the argument that a runbook's spec is three sentences
rests on that section existing here.

No visual companion. Mockups, wireframes and layout comparisons stay on the code side.

## Relevant Files & Context Pointers

- `skills/doc-brainstorming/SKILL.md` — new, the only file in the directory
- `skills/dev-brainstorming/SKILL.md` — the source of the four carried-over mechanisms; read it for
  the mechanisms, not for its vocabulary
- `skills/doc-designer/SKILL.md` — the routine exit; its Step 1 already establishes audience, so
  this skill must hand over something doc-designer does not simply redo
- `skills/decision-records/SKILL.md` — a single ADR routes here directly, below this threshold
- `skills/lean-product-lifecycle/SKILL.md` — the narrowed escape target
- Spec §3.4 (narrowed escape), §3.6 (rewrite + the four mechanisms), §3.7 (correction exit), §4.3

## Design Rationale

**Why the escape is narrowed rather than copied.** `dev-brainstorming` escapes upward when the
target customer cannot be named or the need is unevidenced. Copying that unchanged would push
"write a runbook" toward market discovery — exactly the friction that teaches people to route
around a gate. Here the trigger examines **what the document claims**, not who reads it: it fires
only when the document *is* a product argument — a strategy document, a proposal, a business case —
whose idea has no evidence behind it. A runbook, a handbook or a set of reference pages never
triggers it.

**Why the boundary with `doc-designer` must be explicit.** `doc-designer` Step 1 already asks who
reads this, what they are trying to do, and what they already know. If this skill asks the same
questions, the user answers them twice and stops using one of the two. This skill owns *what the
document should say and whether it should exist*; `doc-designer` owns *what shape it takes* —
the Diátaxis mode, the outline, the section breakdown.

Applicable kit skills: `d3nexus:writing-skills`; `d3nexus:doc_quality_check` does **not** gate this
task — a SKILL.md ships in the plugin, so `@quality_check` applies.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `skills/doc-brainstorming/SKILL.md`; the skill name
  `doc-brainstorming`.
- **Downstream callers**: `skills/brainstorming/SKILL.md` (Task 2), `skills/doc-lifecycle/SKILL.md`
  (Task 4), `skills/doc-designer/SKILL.md` (Task 6). None of them can be green until this exists.
- **Cross-platform bridges**: none.
- **Target verification threshold**: `verify.sh` steps 1–4 green; each of the four carried-over
  mechanisms present and greppable.

## BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] All four carried-over mechanisms are present
  Given skills/doc-brainstorming/SKILL.md
  When it is searched for the hard gate, the user review gate, the one-question rule and the self-review pass
  Then all four are present
  And each is expressed in document vocabulary rather than code vocabulary

Scenario: [Tier A - Unit] The skill carries no visual companion
  Given the skills/doc-brainstorming/ directory
  When its files are listed
  Then SKILL.md is the only file
  And no scripts directory exists

Scenario: [Tier C - Integration] A runbook request does not escape to lean
  Given the user asks for a runbook for an existing deployment process
  When the skill evaluates its upstream escape condition
  Then the condition does not fire
  And the session proceeds to clarifying questions

Scenario: [Tier C - Integration] An unevidenced strategy document does escape to lean
  Given the user asks for a strategy document arguing the company should enter a new market
  And no interviews, data or ranked needs support that argument
  When the skill evaluates its upstream escape condition
  Then it stops and recommends lean-product-lifecycle
  And it hands over the context already gathered

Scenario: [Tier C - Integration] The hard gate holds for a small document
  Given the user asks for a one-page onboarding note
  When the skill judges the work simple
  Then it still presents a design and waits for approval
  And the design may be only a few sentences

Scenario: [Tier A - Unit] The skill does not duplicate doc-designer's audience questions
  Given skills/doc-brainstorming/SKILL.md and skills/doc-designer/SKILL.md
  When both are read
  Then the division of ownership is stated explicitly in this skill
  And this skill does not itself produce a Diátaxis mode or an outline

Scenario: [Tier C - Integration] Work that changes a shipped file is corrected to the dev side
  Given the session is in doc-brainstorming
  And the work will change a file that ships in the build
  When the skill applies the deliverable test
  Then it stops and hands over to dev-brainstorming

Scenario: [Tier C - Integration] A single ADR is turned away
  Given the user asks for one architecture decision record
  When the skill assesses scale
  Then it routes directly to decision-records
  And it does not run a full inception session

Scenario: [Tier A - Unit] One question per message is stated as a rule
  Given the skill body
  When the clarifying-question guidance is read
  Then it states that only one question is asked per message

Scenario: [Tier C - Integration] The terminal state is a single named skill
  Given an approved and self-reviewed spec
  When the skill routes
  Then it invokes exactly one of doc-designer, lean-product-lifecycle or dev-brainstorming
  And never two
```

## Test & Verification Checklist

**TDD adaptation**: new prose with no executable behaviour. RED is a checklist of assertions that
cannot pass against an absent file.

- [ ] **RED**: write the nine assertions above as a grep/read checklist and confirm each fails
      before the file exists.
- [ ] **GREEN**: write `skills/doc-brainstorming/SKILL.md` until each assertion passes.
- [ ] **REFACTOR**: re-read against `dev-brainstorming` side by side and confirm the four
      mechanisms survived the rewrite *in substance*, not merely as matching words.
- [ ] **Tier A**: `verify.sh` steps 1–4 pass; frontmatter has exactly `name` + `description`.
- [ ] **Mermaid**: any process-flow diagram renders via `mermaid-cli`.
- [ ] **Tier C**: run the skill on two throwaway requests — a runbook and an unevidenced strategy
      document — and confirm the escape fires for the second and not the first.

## Definition of Done

- `skills/doc-brainstorming/SKILL.md` exists; SKILL.md is the only file in the directory.
- All four carried-over mechanisms present and expressed in document vocabulary.
- The narrowed escape fires on product arguments only; a runbook never triggers it.
- Ownership boundary with `doc-designer` stated explicitly.
- Correction exit to `dev-brainstorming` present per spec §3.7.
- `verify.sh` steps 1–4 green; any mermaid renders.
- Clean `git status` after the commit.

## Dependencies & Blockers

No blockers — this can run in parallel with Task 1.
Blocks [Task 4](task_4_doc_lifecycle_mandatory_stage_0.md) and
[Task 6](task_6_consumer_retarget.md).

## References & Rollback

- Spec §3.4, §3.6, §3.7, §4.3
- The four mechanisms as they stand today in `skills/dev-brainstorming/SKILL.md` after Task 1

**Rollback**: `git revert` the commit and delete the directory. Reverting this while Tasks 4 and 6
stand leaves both pointing at a skill that does not exist, so revert them together.
