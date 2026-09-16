---
id: "task_7_brainstorming_fourth_exit"
status: "done"
priority: "medium"
assignee: null
epic: "document_lifecycle_suite"
dueDate: null
created: "2026-09-17T09:00:00Z"
modified: "2026-09-16T18:54:42Z"
completedAt: "2026-09-16T18:54:42Z"
labels: ["skill", "routing", "documentation"]
order: "a7"
---

# Task 7: `brainstorming` — Fourth Exit and Upstream Escape

Epic: [document_lifecycle_suite](document_lifecycle_suite.en.md)

## Requirement Analysis

Two changes to `skills/brainstorming/SKILL.md`, and nothing else.

1. **Replace the terminal-state rule.** It currently reads that the terminal state is `epic-designer`
   or `writing-plans`, "never both, and never any other implementation skill". It becomes four exits:
   `dev-designer`, `writing-plans`, `doc-designer`, and `lean-product-lifecycle`.
2. **Add an upstream escape.** If the session reveals that the target customer or the underserved
   need has never been validated, stop and recommend `lean-product-lifecycle` rather than continuing
   into a spec.

Everything else in `brainstorming` — the mindset, 5W1H, alternatives, self-review, the user review
gate, the visual companion — is unchanged. This is a surgical edit.

## Relevant Files & Context Pointers

- `skills/brainstorming/SKILL.md` — the two sections to edit
- `skills/lean-product-lifecycle/SKILL.md` — the upstream target; already routes *down* here
- `skills/doc-designer/SKILL.md` — the new exit
- `skills/dev-designer/SKILL.md` — the renamed existing exit

## Design Rationale

`lean-product-lifecycle` routes down to `brainstorming` but `brainstorming` has no route up. That
asymmetry means a session that discovers the customer was never validated can only continue downhill
into a spec — the Build Trap with better paperwork. Closing the loop costs two paragraphs.

The escape must fire **early**, before the 5W1H questions, because those questions *are* Stage 1 of
`lean-market-discovery` asked less rigorously. Firing late makes the user answer the same questions
twice, which is exactly the friction that makes people stop using a gate.

Applicable kit skills: `writing-skills`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `brainstorming`'s routing section and process-flow mermaid.
- **Downstream callers**: `dev-lifecycle` Stage 1 quotes this routing decision and must stay
  consistent; `lean-product-lifecycle` names `brainstorming` as its small-work route.
- **Cross-platform bridges**: none.
- **Coverage threshold**: not applicable.
- **Consistency risk**: the routing rule is stated in **two** places — here and in `dev-lifecycle`
  Stage 1. Both must be updated or they will disagree.

## BDD SCENARIOS

```gherkin
Scenario: brainstorming has four exits, not two  # [Tier A - Unit]
  Given the brainstorming skill
  When its routing section is read
  Then it names dev-designer, writing-plans, doc-designer and lean-product-lifecycle
  And no other skill is named as a terminal state
```

```gherkin
Scenario: The customer was never validated  # [Tier C - Integration]
  Given a brainstorming session about a new product feature
  When the session reveals no validated target customer or underserved need
  Then brainstorming stops before writing a spec
  And it recommends lean-product-lifecycle
  And it does not continue into dev-designer or writing-plans
```

```gherkin
Scenario: The escape fires before the detailed questions  # [Tier C - Integration]
  Given a request for an unvalidated product idea
  When brainstorming begins
  Then the escape is offered before the 5W1H clarifying questions
  And the user is not asked the same questions lean-market-discovery will ask
```

```gherkin
Scenario: The two statements of the routing rule agree  # [Tier B - Governance]
  Given the routing rule in brainstorming and in dev-lifecycle Stage 1
  When both are read
  Then they name the same four exits
  And neither contradicts the other
```

## Test & Verification Checklist

**TDD adaptation**: a surgical documentation edit. Verification is consistency plus the Task 10
end-to-end run.

- [ ] **Tier A**: `verify.sh` steps 1–4 pass; the process-flow mermaid still parses with the new exits.
- [ ] Diff `brainstorming` and confirm only the routing section and the escape changed — no
      collateral edits to the mindset, 5W1H or review-gate sections.
- [ ] Confirm `dev-lifecycle` Stage 1 states the same four exits.
- [ ] **Tier B**: `verify.sh` steps 5–7 pass.

## Definition of Done

- `brainstorming` names four exits and carries the upstream escape, placed before the clarifying
  questions.
- `dev-lifecycle` Stage 1 agrees with it.
- No other section of `brainstorming` changed. `scripts/verify.sh` passes in full. Clean git status.

## Dependencies & Blockers

- Blocked by [Task 3](task_3_doc_lifecycle_orchestrator.md) and
  [Task 4](task_4_doc_designer_skill.md) — it routes to skills that must exist.

## References & Rollback

- Source spec §1, §4.6.
- **Rollback**: revert to the two-exit rule. Nothing depends on the fourth exit except discoverability
  of the doc track.
