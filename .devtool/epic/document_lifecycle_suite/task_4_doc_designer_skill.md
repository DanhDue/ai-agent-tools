---
id: "task_4_doc_designer_skill"
status: "todo"
priority: "high"
assignee: null
epic: "document_lifecycle_suite"
dueDate: null
created: "2026-09-17T09:00:00Z"
modified: "2026-09-17T09:00:00Z"
completedAt: null
labels: ["skill", "diataxis", "documentation"]
order: "a4"
---

# Task 4: `doc-designer` Skill (Diátaxis)

Epic: [document_lifecycle_suite](document_lifecycle_suite.en.md)

## Requirement Analysis

Create `skills/doc-designer/SKILL.md`: Stage 1 of `doc-lifecycle`, enforcing Gate 1. Four steps, in
order:

1. **Audience and their job** — who reads this, what they are trying to accomplish, what they already
   know. This is the document equivalent of requirements; skipping it produces text that is correct
   and unusable.
2. **Choose exactly one Diátaxis mode.** If the material spans modes, **split into several
   documents**, one per mode. This is Diátaxis's central prescription and the single rule that
   prevents the most common defect in agent-written documentation — a guide that is part tutorial,
   part reference, part explanation, serving nobody.
3. **Outline** — section list, one line of purpose per section.
4. **Task breakdown** — one task per section. Presenting the list for confirmation **is** Gate 1.

**Overview document**: same two-language rule as `dev-designer` (`.en.md` canonical, `.vi.md` kept in
sync). BDD scenarios, architecture and sequence diagrams are **replaced**, not supplemented, by:

```
Kind: document
Audience: <who reads this>
Diátaxis mode: tutorial | how-to | reference | explanation
Non-goals: <what this document deliberately does not cover>
Acceptance: <one thing the reader can do after reading>
```

**`Acceptance` must be a reader task, never a length or a section count.** Documentation is measured
by whether the reader can do the thing. "Explains the deploy process" is not an acceptance criterion;
"a new engineer completes a dev deploy in under 15 minutes without asking anyone" is.

**All Diátaxis text is written from the primary source retained in
[Task 1](task_1_primary_sources_and_fidelity_guard.md), never from recall.**

## Relevant Files & Context Pointers

- `skills/doc-designer/SKILL.md` — to create
- `.devtool/epic/document_lifecycle_suite/source_fidelity_review.md` — the authors' own wording
- `skills/dev-designer/SKILL.md` — the structure to mirror (post-Task 2 name)
- `skills/doc-lifecycle/SKILL.md` — the orchestrator that invokes this stage
- `README.md` — inventory

## Design Rationale

The four modes sit on the author's two axes — **action/cognition** and
**acquisition/application** — and his compass resolves them into a decision table:
content that informs action serves either acquisition (tutorial) or application (how-to guide);
content that informs cognition serves either application (reference) or acquisition (explanation).
A document serving two cells serves neither well. Encode the split rule as a **procedure step**,
not advice:
an agent asked to write "a guide" will otherwise produce a blend by default, and advice does not stop
a default.

`Kind: document` in Meta Data is what [Task 6](task_6_quality_check_kind_branch.md) dispatches on —
this task defines the field, that task consumes it.

Applicable kit skills: `writing-skills`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: new `skills/doc-designer/SKILL.md`; the `Kind`/`Audience`/mode/
  `Non-goals`/`Acceptance` Meta Data contract.
- **Downstream callers**: [Task 6](task_6_quality_check_kind_branch.md) reads `Kind` and the declared
  mode; [Task 5](task_5_doc_implementation_skill.md) consumes the outline and task files;
  [Task 7](task_7_brainstorming_fourth_exit.md) routes here.
- **Cross-platform bridges**: none.
- **Coverage threshold**: not applicable. This is the highest-value skill for the `evals/` ablation
  in [Task 10](task_10_tier_c_acceptance.md).

## BDD SCENARIOS

```gherkin
Scenario: Material spanning two Diátaxis modes is split  # [Tier A - Unit]
  Given source material that is part tutorial and part reference
  When doc-designer selects a mode
  Then it does not declare both modes on one document
  And it splits the work into one document per mode
  And each resulting document declares exactly one mode
```

```gherkin
Scenario: Acceptance is stated as a reader task  # [Tier A - Unit]
  Given doc-designer is writing the overview Meta Data
  When it fills the Acceptance field
  Then the value names something the reader can do after reading
  And a word count, page count or section count is rejected as an Acceptance value
```

```gherkin
Scenario: Audience is established before the outline  # [Tier C - Integration]
  Given a work item with no stated reader
  When doc-designer runs
  Then it asks who the audience is before producing any outline
```

```gherkin
Scenario Outline: Degenerate inputs  # [Tier A - Unit]
  Given a work item described as "<input>"
  When doc-designer runs
  Then it <behaviour>

  Examples:
    | input                                  | behaviour                                          |
    | an outline with zero sections          | refuses Gate 1 and asks for the outline             |
    | a single-section document              | proceeds with exactly one task file                 |
```

```gherkin
Scenario: Gate 1 is the breakdown checkpoint  # [Tier C - Integration]
  Given doc-designer has produced an outline
  When it prepares to write task files
  Then it first presents the numbered task list for confirmation
  And no task file is written before the user confirms
```

## Test & Verification Checklist

**TDD adaptation**: a skill is a document. Structural checks plus the Task 10 ablation replace
RED/GREEN.

- [ ] Confirm every Diátaxis claim traces to a quotation in `source_fidelity_review.md`. Any claim
      that does not is removed or re-sourced.
- [ ] **Tier A**: `verify.sh` steps 1–4 pass.
- [ ] Confirm the Meta Data contract is stated verbatim and matches what Task 6 will parse.
- [ ] Confirm the mode-split rule is written as a procedure step, not as advice.
- [ ] Dry-run the four steps against one real document brief and confirm a single mode is produced.
- [ ] **Tier B**: `verify.sh` steps 5–7 pass, including the new Diátaxis fidelity checks.

## Definition of Done

- `skills/doc-designer/SKILL.md` exists with the four steps, the Meta Data contract and the
  mode-split rule.
- Every methodology claim is traceable to the primary source.
- Added to the README inventory. `scripts/verify.sh` passes in full. Clean git status.

## Dependencies & Blockers

- Blocked by [Task 1](task_1_primary_sources_and_fidelity_guard.md).
- Blocks [Task 6](task_6_quality_check_kind_branch.md).

## References & Rollback

- Diátaxis — Daniele Procida, diataxis.fr; quotations in the epic's `source_fidelity_review.md`.
- **Rollback**: delete the skill and its README entry. `doc-lifecycle` then has no Stage 1 and must
  be reverted with it.
