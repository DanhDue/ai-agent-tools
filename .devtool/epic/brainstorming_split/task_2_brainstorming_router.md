---
id: "task_2_brainstorming_router"
status: "todo"
priority: "high"
assignee: null
epic: "brainstorming_split"
dueDate: null
created: "2026-09-17T09:27:07Z"
modified: "2026-09-17T09:27:07Z"
completedAt: null
labels: ["skills", "routing"]
order: "a2"
---

# Task 2: Rewrite `brainstorming` as the Routing Skill

Epic: [brainstorming_split](brainstorming_split.en.md)

## Requirement Analysis

Create a new `skills/brainstorming/SKILL.md` — roughly 30 lines — holding one question and two
destinations, and nothing else.

The name survives on purpose. `hooks/session-start:47` injects *"use `d3nexus:brainstorming` for
design exploration"* into every session on every project; `skills/using-superpowers/SKILL.md` names
it twice; `rules/CRITICAL_RULES.md:61` links to `../skills/brainstorming/SKILL.md`. Under the
earlier "brainstorming disappears" plan that link would have been a broken relative path inside the
kit's own critical rules. Keeping a router at the same path keeps all three correct and
`verify.sh` steps 1–4 green.

The question is the user's own wording, verbatim:

> Bạn muốn brainstorming để phát triển ý tưởng, làm tài liệu, hay thực hiện phát triển tính năng
> (coding) luôn?

Three labels, two destinations. "Phát triển ý tưởng" and "làm tài liệu" both reach
`doc-brainstorming`, because developing an idea in this kit produces a document.

## Relevant Files & Context Pointers

- `skills/brainstorming/SKILL.md` — created new, after Task 1 has moved the old directory away
- `hooks/session-start:47` — the injected line that makes this name load-bearing
- `skills/using-superpowers/SKILL.md:22,30` — two references that stay pointed here
- `rules/CRITICAL_RULES.md:61` — the relative link that stays resolvable
- Spec §3.1 (the router), §3.2 (discriminate by deliverable, ask rather than infer), §4.1

## Design Rationale

**Why a skill rather than a section inside both variants.** The question is needed exactly once,
at the ambiguous entry. Putting it at the top of both variants duplicates it and reintroduces the
drift this epic exists to remove.

**Why it cannot drift.** Spec §3.5 accepts divergence between the two variants as the intended
outcome and builds no mechanism against it. The router is exempt by construction: it holds no
process discipline, so there is nothing to drift *from*.

**Why no default branch.** An earlier proposal was to infer — source-code features to code,
generic requests to documents. Rejected in §3.2: a vague request is more often unclear *code* work,
so the heuristic fails in the direction that costs most, sending a feature into the document path
where the three-tier suite never runs.

**Cost.** One more `description` field resident in context permanently. Descriptions are the
standing cost of a skill; bodies load per invocation. Roughly three lines.

Applicable kit skills: `d3nexus:writing-skills` — in particular the rule that `description` drives
activation in both runtimes and must state *what* and *when* in third person.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `skills/brainstorming/SKILL.md`, recreated; the skill name
  `brainstorming` now denoting a router rather than a process.
- **Downstream callers**: `hooks/session-start`, `skills/using-superpowers/SKILL.md`,
  `rules/CRITICAL_RULES.md`, `templates/AGENTS.md`. The first three keep naming the router and are
  correct unchanged; `templates/AGENTS.md` is retargeted in Task 6 because its row is specifically
  about feature work.
- **Cross-platform bridges**: none.
- **Target verification threshold**: `verify.sh` steps 1–4 green; the body stays under ~40 lines,
  since progressive disclosure makes a long router self-defeating.

## BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] The router keeps the name and path its consumers depend on
  Given skills/brainstorming/SKILL.md exists
  When its frontmatter name field is read
  Then it reads "brainstorming"
  And rules/CRITICAL_RULES.md's relative link to it resolves

Scenario: [Tier C - Integration] An ambiguous request is routed by the answer, not by a guess
  Given the user says only "brainstorm this"
  When the router runs
  Then it asks the three-option question before doing anything else
  And it does not explore the codebase first

Scenario: [Tier C - Integration] Choosing coding reaches the development variant
  Given the router has asked its question
  When the user answers "phát triển tính năng (coding)"
  Then dev-brainstorming is invoked

Scenario: [Tier C - Integration] Both non-coding labels reach the same destination
  Given the router has asked its question
  When the user answers "phát triển ý tưởng"
  Then doc-brainstorming is invoked
  And the same holds when the user answers "làm tài liệu"

Scenario: [Tier A - Unit] There is no default branch
  Given the router's body
  When it is searched for a fallback or default destination
  Then none is declared
  And the instruction on an unclear answer is to ask again

Scenario: [Tier C - Integration] A non-committal answer produces another question, not a guess
  Given the router has asked its question
  When the user answers "không chắc" or says nothing about the deliverable
  Then the router asks again
  And it does not pick a variant on the user's behalf

Scenario: [Tier C - Integration] A caller that already knows the branch bypasses the router
  Given doc-lifecycle is entering Stage 0
  When it invokes the inception stage
  Then it invokes doc-brainstorming directly
  And the router is not involved

Scenario: [Tier A - Unit] The router carries no process discipline
  Given the router's body
  When it is searched for a checklist, clarifying-question process, or design-presentation steps
  Then none are present

Scenario: [Tier A - Unit] Frontmatter carries exactly two keys
  Given skills/brainstorming/SKILL.md frontmatter
  When its keys are enumerated
  Then they are exactly name and description
  And no third key is present
```

## Test & Verification Checklist

**TDD adaptation**: new prose with no executable behaviour. RED is the set of assertions that fail
against an absent file and pass against the written one.

- [ ] **RED**: confirm `skills/brainstorming/SKILL.md` does not exist after Task 1, so the
      `CRITICAL_RULES.md:61` link is momentarily broken and `verify.sh` step 1 fails. This failure
      is the proof that the router is load-bearing.
- [ ] **GREEN**: write the router; the broken link resolves again.
- [ ] **REFACTOR**: cut anything that is not the question, the destinations, or the no-inference
      rule.
- [ ] **Tier A**: `verify.sh` steps 1–4 pass; frontmatter has exactly two keys.
- [ ] **Tier C**: invoke `d3nexus:brainstorming` with a bare "brainstorm this" and confirm the
      question is asked first and each answer reaches the right variant.

## Definition of Done

- `skills/brainstorming/SKILL.md` exists, ~30 lines, frontmatter exactly `name` + `description`.
- The three-option question appears in the user's wording.
- Two destinations declared; no default; unclear answers are asked about again.
- No checklist, no clarifying-question process, no design presentation steps.
- `verify.sh` steps 1–4 green; `CRITICAL_RULES.md:61` resolves.
- Clean `git status` after the commit.

## Dependencies & Blockers

Blocked by [Task 1](task_1_dev_brainstorming_rename.md) — Task 1 moves `skills/brainstorming/`
away; creating this file first produces a directory that the move then swallows.

## References & Rollback

- Spec §3.1, §3.2, §4.1
- HLD [§4.4 Finding 3](brainstorming_split.en.md#44-check-1--shift-left-impact-analysis) — the
  broken link this task's existence prevents
- HLD §5, ordering hazard

**Rollback**: `git revert` the commit. Reverting this alone while Task 1 stands leaves
`CRITICAL_RULES.md:61` broken, so revert Tasks 1 and 2 together or neither.
