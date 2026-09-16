---
id: "task_3_doc_lifecycle_orchestrator"
status: "todo"
priority: "high"
assignee: null
epic: "document_lifecycle_suite"
dueDate: null
created: "2026-09-17T09:00:00Z"
modified: "2026-09-17T09:00:00Z"
completedAt: null
labels: ["skill", "orchestrator", "documentation"]
order: "a3"
---

# Task 3: `doc-lifecycle` Orchestrator Skill

Epic: [document_lifecycle_suite](../epic/document_lifecycle_suite/document_lifecycle_suite.en.md)

## Requirement Analysis

Create `skills/doc-lifecycle/SKILL.md`: the sequence-and-gates owner for work whose deliverable is a
document. It mirrors `dev-lifecycle` in shape — it owns sequence and gates only; each stage's method
lives in that stage's own skill.

**Three gates, not five.** Code and prose differ in ways that change what verification can mean: the
unit of work is a section rather than a testable deliverable, verification is mechanical checks plus
human judgment rather than a machine running tests, the governing constraint is the *audience*
rather than the architecture, and the cost of being wrong is low. Because the cost of being wrong is
low, the gate count must be low. A runbook that costs five approvals will not be written through
this lifecycle; it will be written around it.

| Gate | Name | Approver | Handoff artefact |
|---|---|---|---|
| 1 | Brief & Outline approved | User | `<slug>.en.md` + `<slug>.vi.md` + `task_*.md` |
| 2 | Draft verified | `quality_check` (machine) | 🟢 report |
| 3 | Sign-off | User | confirmation to finish the branch |

**Stages**: Stage 0 `brainstorming` (optional — only when the content itself is still unknown);
Stage 1 `doc-designer`, exits at Gate 1; Stage 2 `doc-implementation`, exits at Gate 2 then Gate 3;
Stage 3 `finishing-a-development-branch`, entered only once Gate 3 has passed.

**Gate failure routing**: Gate 1 → Stage 1 (revise brief or outline). Gate 2 → Stage 2 (fix findings,
re-run `quality_check` **in full**, never only the previously failing check). Gate 3 → Stage 2.

**A mandatory `When NOT to use this` section** naming concrete cases — a typo fix, a one-line README
correction, any edit a reviewer would not meaningfully gate — resolved by editing directly with no
lifecycle. Without it the lifecycle becomes a tax on small edits and users route around it, which
costs more than having no lifecycle at all.

## Relevant Files & Context Pointers

- `skills/doc-lifecycle/SKILL.md` — to create
- `skills/dev-lifecycle/SKILL.md` — the structure to mirror section-for-section (post-Task 2 name)
- `skills/writing-skills/SKILL.md` — authoring standard
- `CLAUDE.md` — frontmatter is exactly `name` + `description`; keep SKILL.md concise
- `README.md` — add the skill to the inventory

## Design Rationale

Mirroring `dev-lifecycle` section-for-section is deliberate: two independently maintained
orchestrators drift — gates get renumbered on one side, terminology shifts on the other — and a
readable diff between the two files is what makes drift visible.

The `description:` carries the routing. Because the user picks the lifecycle by hand, there is no
triage algorithm anywhere; `description:` frontmatter is the entire routing mechanism for the case
where the user names no skill.

Applicable kit skills: `writing-skills`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: new `skills/doc-lifecycle/SKILL.md`; README inventory.
- **Downstream callers**: [Task 7](task_7_brainstorming_fourth_exit.md) routes to this skill;
  [Task 5](task_5_doc_implementation_skill.md) is its Stage 2.
- **Cross-platform bridges**: none.
- **Coverage threshold**: not applicable; verified structurally by `verify.sh` and behaviourally in
  [Task 10](task_10_tier_c_acceptance.md).

## BDD SCENARIOS

```gherkin
Scenario: A trivial edit opens no gates  # [Tier C - Integration]
  Given a one-line correction to README.md
  When the author consults doc-lifecycle
  Then the "When NOT to use this" section names this case
  And the edit is made directly with no brief, outline or gate
```

```gherkin
Scenario Outline: Gate failure routing  # [Tier A - Unit]
  Given the lifecycle is at <gate>
  When the gate fails
  Then control returns to <stage>

  Examples:
    | gate                        | stage                                    |
    | Gate 1 brief and outline    | Stage 1 — revise the brief or outline    |
    | Gate 2 draft verified       | Stage 2 — fix findings, re-run in full   |
    | Gate 3 sign-off             | Stage 2 — apply the requested changes    |
```

```gherkin
Scenario: Stage 3 is unreachable without Gate 2  # [Tier C - Integration]
  Given a document draft that quality_check has not verified
  When finishing-a-development-branch is invoked
  Then the lifecycle refuses to proceed
  And it names Gate 2 as the unmet precondition
```

```gherkin
Scenario: A failed Gate 2 is re-run in full  # [Tier C - Integration]
  Given quality_check reported one failing mechanical check
  And the author fixed only that check
  When Gate 2 is re-evaluated
  Then the complete document check suite runs again
  And a green verdict from a partial run is not accepted
```

## Test & Verification Checklist

**TDD adaptation**: a skill is a document, not code. RED/GREEN is replaced by structural checks plus
the behavioural ablation in Task 10.

- [ ] **Tier A**: `verify.sh` steps 1–4 — frontmatter exactly `name` + `description`, name matches
      directory, every relative link resolves, ToC anchors match headings.
- [ ] Confirm the gate table, stage list and failure-routing table each mirror `dev-lifecycle`'s
      corresponding section; diff the two files and confirm the difference is only content.
- [ ] Confirm `When NOT to use this` names at least three concrete cases, not an abstract threshold.
- [ ] Render every mermaid block and confirm it parses.
- [ ] **Tier B**: `verify.sh` steps 5–7 pass.

## Definition of Done

- `skills/doc-lifecycle/SKILL.md` exists with three gates, the stage list, gate-failure routing and
  a concrete `When NOT to use this`.
- Structurally mirrors `dev-lifecycle`. Added to the README inventory.
- `scripts/verify.sh` passes in full. Clean git status.

## Dependencies & Blockers

- Blocks [Task 5](task_5_doc_implementation_skill.md) and [Task 7](task_7_brainstorming_fourth_exit.md).
- Blocked by: nothing, but land after [Task 2](task_2_rename_epic_skills_to_dev.md) so it mirrors the
  already-renamed `dev-lifecycle`.

## References & Rollback

- Source spec §3.3, §4.1.
- **Rollback**: delete the skill directory and its README entry. Additive — nothing else depends on
  it until Tasks 5 and 7 land.
