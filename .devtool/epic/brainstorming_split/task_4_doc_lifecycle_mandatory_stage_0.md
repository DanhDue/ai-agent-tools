---
id: "task_4_doc_lifecycle_mandatory_stage_0"
status: "todo"
priority: "high"
assignee: null
epic: "brainstorming_split"
dueDate: null
created: "2026-09-17T09:27:07Z"
modified: "2026-09-17T09:27:07Z"
completedAt: null
labels: ["skills", "orchestrator", "gates"]
order: "a4"
---

# Task 4: Make `doc-lifecycle` Stage 0 Mandatory and Renumber the Gates

Epic: [brainstorming_split](brainstorming_split.en.md)

## Requirement Analysis

The only structural change in this epic. Everything else is a rename or a reference update.

Stage 0 is currently optional, and its skip condition cannot be tested:

> Skip this stage whenever the content is known and only its shape is open.

An agent evaluating "is the content known?" answers yes essentially always, because it has just
read the request and believes it understands it. The stage therefore does not exist in practice.

Making it mandatory gives it a gate, which renumbers the rest:

| Gate | Before | After |
|------|--------|-------|
| 1 | Brief & Outline (`doc-designer`) | **Spec Approved (`doc-brainstorming`)** |
| 2 | Draft Verified (`doc_quality_check`) | Brief & Outline (`doc-designer`) |
| 3 | Sign-Off (user) | Draft Verified (`doc_quality_check`) |
| 4 | — | Sign-Off (user) |

This restores symmetry with `dev-lifecycle`, where Stage 1 is inception and owns Gate 1. The two
orchestrators are meant to read as siblings — a readable diff between them is what makes drift
visible, and an optional Stage 0 broke that.

**The cost, and the answer.** Stage 0 was optional so a runbook would not pass two approval gates
before a word is drafted. The resolution is that the stage is mandatory in its *existence* and
elastic in its *depth*, which is the idiom the inception skill already states about itself: the
design can be short, but it must be presented and approved. The runbook still passes through
Stage 0; its spec is three sentences.

What this buys is a gate question that can be answered: not "is the content already known?" but
"was a spec presented and approved?"

## Relevant Files & Context Pointers

- `skills/doc-lifecycle/SKILL.md` — every change in this task
  - frontmatter `description` — says "three approval gates", and does not name the inception skill
  - line ~42 — the Stage 0 mermaid node, labelled `(optional)`
  - the mermaid edges — `S0 --> S1` is unconditional already, but `G1`–`G3` renumber
  - `## The Three Gates` heading and the sentence "Three, not five"
  - the gate table, 3 rows → 4
  - `### Stage 0 — Inception → brainstorming *(optional)*` heading
  - the untestable skip sentence, deleted
  - the Stage Skills table row `| 0 | brainstorming | — (optional) |`
- `skills/dev-lifecycle/SKILL.md` — the sibling to diff against
- `skills/dev-brainstorming/SKILL.md` — the "too simple to need a design" anti-pattern this
  argument rests on
- Spec §3.3, §4.6

## Design Rationale

**Why four representations must be checked against each other, not incidentally.** The gate count
appears in the mermaid diagram, the prose, the gate table and the Stage Skills table. During
release 1.2.0, Gate 2 caught four separate instances of prose updated and the corresponding diagram
not — all of this exact shape. The Definition of Done below names the four explicitly so the check
is a step rather than a hope.

**Why the skip sentence is deleted rather than reworded.** Any reworded condition is still a
condition the agent evaluates about its own understanding. Removing optionality removes the
evaluation.

Applicable kit skills: `d3nexus:writing-skills`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `skills/doc-lifecycle/SKILL.md`; the gate numbers 1–4 as referenced
  by any other file.
- **Downstream callers**: `skills/doc-implementation/SKILL.md` and
  `skills/doc_quality_check/SKILL.md` may name gate numbers; `skills/dev-brainstorming/SKILL.md`
  carries the sentence "which has three gates rather than five"; `docs/lifecycles.{en,vi}.md` and
  `docs/choosing-a-lifecycle.{en,vi}.md` state the count. Every one of these must be swept.
- **Cross-platform bridges**: none.
- **Target verification threshold**: the number four appears consistently in all four
  representations plus every downstream mention; zero occurrences of "three gates" referring to
  `doc-lifecycle`.

## BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] The gate count agrees across all four representations
  Given skills/doc-lifecycle/SKILL.md
  When the mermaid diagram, the prose, the gate table and the Stage Skills table are compared
  Then all four describe four gates
  And the gate names match one another row for row

Scenario: [Tier A - Unit] The untestable skip condition is gone
  Given skills/doc-lifecycle/SKILL.md
  When it is searched for "only its shape is open"
  Then there are zero matches

Scenario: [Tier A - Unit] Stage 0 is no longer labelled optional
  Given the Stage 0 heading and its mermaid node
  When both are read
  Then neither contains the word "optional"

Scenario: [Tier A - Unit] Gate 1 is owned by the inception stage
  Given the gate table
  When row 1 is read
  Then its approver is the user
  And it is enforced in doc-brainstorming

Scenario: [Tier A - Unit] The description frontmatter states the new count
  Given the frontmatter description field
  When it is read
  Then it says four approval gates
  And it names doc-brainstorming among the connected skills

Scenario: [Tier C - Integration] A small document still passes through Stage 0
  Given the user asks for a runbook whose content is entirely known
  When doc-lifecycle enters Stage 0
  Then doc-brainstorming is invoked
  And the resulting spec may be three sentences
  And the stage is not skipped

Scenario: [Tier C - Integration] The stage is entered by invoking its skill
  Given doc-lifecycle is at Stage 0
  When the orchestrator proceeds
  Then it invokes d3nexus:doc-brainstorming
  And it does not read the stage description and do the work itself

Scenario: [Tier A - Unit] No downstream file still claims three gates
  Given the whole repository excluding .devtool and CHANGELOG.md
  When it is searched for a three-gate claim about doc-lifecycle
  Then there are zero matches

Scenario: [Tier A - Unit] The two orchestrators still read as siblings
  Given skills/dev-lifecycle/SKILL.md and skills/doc-lifecycle/SKILL.md
  When their section headings are listed side by side
  Then each has a stage that owns Gate 1 through an inception skill

Scenario: [Tier C - Integration] Sign-off remains the last gate
  Given the renumbered sequence
  When the final gate is read
  Then it is the user's sign-off
  And it precedes finishing-a-development-branch
```

## Test & Verification Checklist

**TDD adaptation**: prose restructuring with no executable behaviour. RED is a set of greps whose
results must flip.

- [ ] **RED**: confirm `grep -n "only its shape is open" skills/doc-lifecycle/SKILL.md` returns a
      hit, and `grep -c "Three, not five"` returns 1.
- [ ] **GREEN**: renumber the gates; delete the skip sentence; update the four representations and
      the frontmatter description.
- [ ] **REFACTOR**: diff `doc-lifecycle` against `dev-lifecycle` section by section and confirm the
      sibling structure reads cleanly.
- [ ] **Tier A**: `verify.sh` steps 1–4 pass; ToC anchors still match headings.
- [ ] **Mermaid**: the sequence diagram renders via `mermaid-cli` after renumbering.
- [ ] **Tier B**: repo-wide sweep for stale "three gates" claims, excluding `.devtool/` and
      `CHANGELOG.md`.
- [ ] **Tier C**: drive `doc-lifecycle` end-to-end on one small real document and confirm Stage 0
      runs and Gate 1 is the spec approval.

## Definition of Done

- Four gates, consistently, in **all four** representations: mermaid, prose, gate table, Stage
  Skills table. Each checked against the other three explicitly.
- `description` frontmatter says four gates and names `doc-brainstorming`.
- The untestable skip sentence is deleted, not reworded.
- Stage 0 headings and nodes carry no "optional".
- Zero stale three-gate claims anywhere outside `.devtool/` and `CHANGELOG.md`.
- `verify.sh` steps 1–4 green; mermaid renders; ToC anchors match.
- Clean `git status` after the commit.

## Dependencies & Blockers

Blocked by [Task 3](task_3_doc_brainstorming_skill.md) — Stage 0 must name a skill that exists.
Blocks [Task 7](task_7_verify_orchestrator_routing_check.md) and
[Task 8](task_8_docs_bilingual_update.md).

## References & Rollback

- Spec §3.3, §4.6
- HLD §5, the gate-renumber mitigation
- The four prose/diagram mismatches caught at Gate 2 during release 1.2.0

**Rollback**: `git revert` the commit. The gate numbering is self-contained within one file plus
the downstream sweep, so the revert is clean provided Task 8's doc updates are reverted with it.
