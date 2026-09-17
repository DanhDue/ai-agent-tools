---
id: "task_5_dev_lifecycle_retarget"
status: "done"
priority: "medium"
assignee: null
epic: "brainstorming_split"
dueDate: null
created: "2026-09-17T09:27:07Z"
modified: "2026-09-17T09:36:32Z"
completedAt: "2026-09-17T09:36:32Z"
labels: ["skills", "orchestrator", "rename"]
order: "a5"
---

# Task 5: Retarget `dev-lifecycle` to `dev-brainstorming`

Epic: [brainstorming_split](brainstorming_split.en.md)

## Requirement Analysis

Eight references, one file, **no structural change**. The development sequence, its five gates and
its stage order are explicitly out of scope for this epic (spec §2). This task changes which skill
Stage 1 names, and nothing else.

The eight sites:

| # | Location | What it says now |
|---|---|---|
| 1 | frontmatter `description` | names `brainstorming` among the connected skills |
| 2 | small-work bullet, line ~20 | "anything one implementation plan covers → `brainstorming`" |
| 3 | Stage 1 mermaid node, line ~28 | `S1["Stage 1 — Inception & Spec<br/>(brainstorming)"]` |
| 4 | gate table row, line ~69 | Gate 1 "enforced in `brainstorming`" |
| 5 | Stage 1 heading, line ~77 | `### Stage 1 — Inception & Spec → brainstorming` |
| 6 | invoke line, line ~79 | `**Invoke d3nexus:brainstorming.**` |
| 7 | decomposition note, line ~98 | "If brainstorming decomposed the request…" |
| 8 | Stage Skills table, line ~171 | `\| 1 \| brainstorming \| 1 \|` |

Site 6 matters most. It was added in commit `0b8a030` precisely because the orchestrator had never
contained the word "invoke" — agents read the stage description and did the stage's work
themselves, skipping Gate 1. Pointing it at the wrong skill would undo that fix.

## Relevant Files & Context Pointers

- `skills/dev-lifecycle/SKILL.md` — all eight sites
- `skills/dev-brainstorming/SKILL.md` — the target, must exist first
- Commit `0b8a030` — the stage-entry imperative this task must preserve
- Spec §2 (non-goals), §4.5

## Design Rationale

A mechanical retarget, deliberately kept mechanical. The temptation on touching an orchestrator is
to improve it; spec §2 rules that out, and the user stated twice during design that this flow stays
as it is.

Site 3 is inside a mermaid diagram, so the change must be verified by rendering, not by reading.

Applicable kit skills: `d3nexus:writing-skills`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `skills/dev-lifecycle/SKILL.md`; the skill name in its Stage 1 and
  Gate 1 contracts.
- **Downstream callers**: none read `dev-lifecycle` programmatically. Task 7's new check greps this
  file, so the two must agree.
- **Cross-platform bridges**: none.
- **Target verification threshold**: zero occurrences of bare `brainstorming` as a skill reference
  in this file; five gates unchanged; mermaid renders.

## BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] Stage 1 names the development variant
  Given skills/dev-lifecycle/SKILL.md
  When the Stage 1 heading and invoke line are read
  Then both name d3nexus:dev-brainstorming

Scenario: [Tier A - Unit] The orchestrator no longer names the router
  Given skills/dev-lifecycle/SKILL.md
  When it is searched for d3nexus:brainstorming or a backticked bare brainstorming
  Then there are zero matches

Scenario: [Tier A - Unit] The stage-entry imperative survives the retarget
  Given the Stage 1 section
  When it is read
  Then it still instructs the agent to invoke the skill
  And it still states that writing the spec directly skips Gate 1

Scenario: [Tier A - Unit] The gate count is unchanged
  Given the gate table
  When its rows are counted
  Then there are five

Scenario: [Tier A - Unit] The stage order is unchanged
  Given the Stage Skills table
  When its rows are read in order
  Then the sequence matches the version before this task, with only the Stage 1 skill name differing

Scenario: [Tier A - Unit] The mermaid node is updated and still renders
  Given the process-flow diagram
  When it is rendered with mermaid-cli
  Then it succeeds
  And the Stage 1 node reads dev-brainstorming

Scenario: [Tier A - Unit] The description frontmatter names the variant
  Given the frontmatter description field
  When it is read
  Then it names dev-brainstorming
  And it still says five approval gates

Scenario: [Tier C - Integration] Entering the epic lifecycle reaches the development variant
  Given a request that spans multiple components
  When dev-lifecycle is invoked and reaches Stage 1
  Then it invokes dev-brainstorming
  And the router is not involved
```

## Test & Verification Checklist

**TDD adaptation**: reference retarget, no new behaviour. RED is a grep whose count must go to zero.

- [ ] **RED**: confirm `grep -c "brainstorming" skills/dev-lifecycle/SKILL.md` returns 8.
- [ ] **GREEN**: retarget all eight sites to `dev-brainstorming`.
- [ ] **REFACTOR**: none — resist improving adjacent prose.
- [ ] **Tier A**: `verify.sh` steps 1–4 pass; ToC anchors still match.
- [ ] **Mermaid**: the process-flow diagram renders.
- [ ] **Tier B**: Task 7's check passes against this file.
- [ ] **Tier C**: invoke `d3nexus:dev-lifecycle` on a throwaway multi-component request and confirm
      Stage 1 invokes `dev-brainstorming`.

## Definition of Done

- All eight sites name `dev-brainstorming`.
- Zero occurrences of `d3nexus:brainstorming` or a backticked bare `brainstorming` in this file.
- Five gates and the stage order are byte-for-byte unchanged apart from the skill name.
- The stage-entry imperative from `0b8a030` is intact.
- `verify.sh` steps 1–4 green; mermaid renders.
- Clean `git status` after the commit.

## Dependencies & Blockers

Blocked by [Task 1](task_1_dev_brainstorming_rename.md) — the target skill must exist.
Blocks [Task 7](task_7_verify_orchestrator_routing_check.md) and
[Task 8](task_8_docs_bilingual_update.md).

## References & Rollback

- Spec §2, §4.5
- Commit `0b8a030` — the stage-entry imperative
- HLD §4.1

**Rollback**: `git revert` the commit. Single file, eight string changes, no state.
