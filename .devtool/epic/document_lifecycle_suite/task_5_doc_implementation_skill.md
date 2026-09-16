---
id: "task_5_doc_implementation_skill"
status: "todo"
priority: "high"
assignee: null
epic: "document_lifecycle_suite"
dueDate: null
created: "2026-09-17T09:00:00Z"
modified: "2026-09-17T09:00:00Z"
completedAt: null
labels: ["skill", "execution", "documentation"]
order: "a5"
---

# Task 5: `doc-implementation` Skill

Epic: [document_lifecycle_suite](document_lifecycle_suite.en.md)

## Requirement Analysis

Create `skills/doc-implementation/SKILL.md`: Stage 2 of `doc-lifecycle`.

Reuses `dev-implementation`'s Kanban machinery **unchanged** — one worktree, one task at a time, one
commit per section, `.devtool/features/task_*.md` files, and the same divergence discipline: if the
draft departs from the outline, sync the outline before starting the next task.

**What replaces TDD.** There is nothing to run. In its place: after writing a section, re-read it
against that section's own one-line purpose in the outline. On mismatch, either fix the section or
change the outline deliberately. There is no third option, and "close enough" is not one.

The skill must state plainly that it does **not** invoke the 3-tier test suite, and that Gate 2 is
`quality_check` with `Kind: document`.

## Relevant Files & Context Pointers

- `skills/doc-implementation/SKILL.md` — to create
- `skills/dev-implementation/SKILL.md` — the machinery to reuse (post-Task 2 name)
- `skills/dev-implementation/resources/scripts/sync_task_status.py` — reused as-is
- `skills/dev-implementation/resources/scripts/compute_execution_order.py` — reused as-is
- `skills/doc-lifecycle/SKILL.md` — the orchestrator
- `README.md` — inventory

## Design Rationale

Reusing the Kanban scripts rather than forking them is the point: task status, execution order and
archival behave identically for both kinds of epic, so `.devtool/features/` stays one board rather
than two. Forking would double the maintenance surface for no behavioural gain.

The outline-purpose re-read is the cheapest available substitute for a failing test: it gives each
section an explicit, pre-written expectation to be checked against, which is what a test actually
provides.

Applicable kit skills: `writing-skills`, `d3nexus:using-git-worktrees`,
`d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: new `skills/doc-implementation/SKILL.md`. No change to the Kanban
  scripts — reuse only.
- **Downstream callers**: `doc-lifecycle` Stage 2; `quality_check` receives its output.
- **Cross-platform bridges**: none.
- **Coverage threshold**: not applicable.

## BDD SCENARIOS

```gherkin
Scenario: One commit per section  # [Tier C - Integration]
  Given an approved outline with four sections
  When doc-implementation executes the four task files
  Then exactly four section commits exist
  And each commit message names the section it wrote
```

```gherkin
Scenario: Divergence syncs the outline  # [Tier C - Integration]
  Given a section whose draft departs from its outline purpose line
  When the section is complete
  Then either the section is corrected or the outline is changed deliberately
  And the outline is synced before the next task starts
```

```gherkin
Scenario: The 3-tier test suite is not invoked  # [Tier A - Unit]
  Given doc-implementation is executing a document task
  When it reaches its verification step
  Then it does not run unit, integration or native build commands
  And it hands off to quality_check with Kind document
```

```gherkin
Scenario: A second epic is already active  # [Tier C - Integration]
  Given another epic has at least one task with status todo, in-progress or review
  When task files for this epic are generated
  Then every new task is created with status backlog, not todo
  And the epic overview Status field names the blocking epic
```

## Test & Verification Checklist

**TDD adaptation**: no new executable behaviour. Verification is structural plus one real end-to-end
run in [Task 10](task_10_tier_c_acceptance.md).

- [ ] **Tier A**: `verify.sh` steps 1–4 pass.
- [ ] Confirm the skill references the Kanban scripts by their post-rename paths and does not fork
      them.
- [ ] Confirm the skill explicitly states that it runs no test suite and why.
- [ ] Confirm the outline-sync rule offers exactly two outcomes, with no escape hatch.
- [ ] **Tier B**: `verify.sh` steps 5–7 pass.

## Definition of Done

- `skills/doc-implementation/SKILL.md` exists, reusing the Kanban machinery unchanged.
- The re-read-against-outline rule replaces TDD and is stated as a procedure.
- Added to the README inventory. `scripts/verify.sh` passes in full. Clean git status.

## Dependencies & Blockers

- Blocked by [Task 3](task_3_doc_lifecycle_orchestrator.md).
- Land after [Task 2](task_2_rename_epic_skills_to_dev.md) so script paths are already final.

## References & Rollback

- Source spec §4.3.
- **Rollback**: delete the skill and its README entry. The Kanban scripts are untouched, so
  `dev-implementation` is unaffected.
