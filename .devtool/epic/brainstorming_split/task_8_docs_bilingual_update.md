---
id: "task_8_docs_bilingual_update"
status: "todo"
priority: "medium"
assignee: null
epic: "brainstorming_split"
dueDate: null
created: "2026-09-17T09:27:07Z"
modified: "2026-09-17T09:27:07Z"
completedAt: null
labels: ["documentation", "bilingual"]
order: "a8"
---

# Task 8: Update the Four Bilingual Lifecycle Documents

Epic: [brainstorming_split](brainstorming_split.en.md)

## Requirement Analysis

Four files, six `brainstorming` references each, plus the gate-count change from Task 4:

- `docs/lifecycles.en.md` / `docs/lifecycles.vi.md` — reference material
- `docs/choosing-a-lifecycle.en.md` / `docs/choosing-a-lifecycle.vi.md` — a how-to

Each document states that `doc-lifecycle` has three gates. All four must say four, and the
`.en`/`.vi` pairs must stay identical in structure and facts.

Both documents also describe the entry point to each lifecycle. With the router introduced, that
description changes: a user with an ambiguous request enters through `brainstorming`, which asks;
a user who already knows enters through the lifecycle directly.

**This task is gated by `@doc_quality_check`, not `@quality_check`.** These four files do not ship
in the plugin build. Running the wrong gate produces a green light that means nothing, and
`@doc_quality_check` refuses outright if the change touches shipped files — so this task must be
committed separately from any task that edits `skills/`.

## Relevant Files & Context Pointers

- `docs/lifecycles.en.md`, `docs/lifecycles.vi.md` — 6 references each
- `docs/choosing-a-lifecycle.en.md`, `docs/choosing-a-lifecycle.vi.md` — 6 references each
- `skills/doc_quality_check/SKILL.md` — the gate, including its Check 0 refusal rule
- All four files use semantic line breaks; preserve that wrapping
- Spec §4.7

## Design Rationale

**Why a separate commit from the skill changes.** `@doc_quality_check` Check 0 refuses when the
diff touches files that ship in the build. Mixing these four files into a commit with `skills/`
edits makes the correct gate unrunnable.

**Why Diátaxis type matters here.** `lifecycles.*` is reference and `choosing-a-lifecycle.*` is a
how-to. The router changes what a reader *does*, so the how-to needs its decision path reworked,
while reference only needs its facts corrected. Treating both the same way would turn the how-to
into a description of the system rather than instructions for using it.

**Vietnamese is a translation, not an independent document.** The `.en` variant is the source of
truth; the `.vi` variant must not diverge in structure or facts. Update `.en` first.

Applicable kit skills: `d3nexus:doc_quality_check` (the gate), `d3nexus:doc-designer` for the
Diátaxis distinction.

## Impact Analysis & Blast Radius

- **Target files & symbols**: four documents; the gate count for `doc-lifecycle`; the entry-point
  description for all three lifecycles.
- **Downstream callers**: `README.md` may link these documents; links must still resolve.
- **Cross-platform bridges**: none.
- **Target verification threshold**: `@doc_quality_check` green; `.en`/`.vi` structural parity;
  internal links resolve; ToC anchors match headings.

## BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] All four documents state four gates for doc-lifecycle
  Given the four documents
  When each is searched for the doc-lifecycle gate count
  Then each says four
  And none says three

Scenario: [Tier A - Unit] The English and Vietnamese variants stay structurally identical
  Given lifecycles.en.md and lifecycles.vi.md
  When their heading lists are compared
  Then the counts and the nesting match
  And the same holds for the choosing-a-lifecycle pair

Scenario: [Tier A - Unit] Semantic line breaks are preserved
  Given the four documents after editing
  When their wrapping is inspected
  Then lines still break at clause boundaries
  And no line exceeds the existing maximum width

Scenario: [Tier C - Integration] The how-to gives a decision path, not a description
  Given docs/choosing-a-lifecycle.en.md
  When a reader follows it with an ambiguous request
  Then it tells them to enter through brainstorming and answer its question
  And it does not merely describe that the router exists

Scenario: [Tier A - Unit] The reference document records both variants
  Given docs/lifecycles.en.md
  When the skills for each lifecycle are listed
  Then dev-lifecycle names dev-brainstorming
  And doc-lifecycle names doc-brainstorming

Scenario: [Tier B - Governance] The correct gate is used
  Given this task's commit touches only files under docs/
  When doc_quality_check runs
  Then Check 0 does not refuse
  And the report is green

Scenario: [Tier B - Governance] The wrong gate would refuse
  Given a hypothetical commit mixing docs/ and skills/ changes
  When doc_quality_check runs
  Then Check 0 refuses outright

Scenario: [Tier A - Unit] Internal links and anchors still resolve
  Given the four documents
  When their internal links and ToC anchors are checked
  Then every link resolves
  And every anchor matches a heading
```

## Test & Verification Checklist

**TDD adaptation**: prose updates. RED is the gate-count grep plus the structural-parity diff.

- [ ] **RED**: confirm each of the four documents currently claims three gates.
- [ ] **GREEN**: update `.en` first, then bring `.vi` into line; rework the how-to's decision path.
- [ ] **REFACTOR**: re-read the wrapping; semantic line breaks must survive the edit.
- [ ] **Tier A**: ToC anchors match headings; internal links resolve.
- [ ] **Tier B**: `@doc_quality_check` green, on a commit containing **only** `docs/` changes.
- [ ] **Tier C**: follow `choosing-a-lifecycle.en.md` end to end as a reader with an ambiguous
      request and confirm it lands in the right lifecycle.

## Definition of Done

- All four documents state four gates for `doc-lifecycle`.
- `.en`/`.vi` pairs match in structure and facts; `.en` was edited first.
- The how-to gives a decision path including the router's question; the reference states facts.
- Semantic line breaks preserved.
- `@doc_quality_check` green on a docs-only commit.
- Clean `git status` after the commit.

## Dependencies & Blockers

Blocked by [Task 1](task_1_dev_brainstorming_rename.md), [Task 3](task_3_doc_brainstorming_skill.md), [Task 4](task_4_doc_lifecycle_mandatory_stage_0.md) and [Task 5](task_5_dev_lifecycle_retarget.md).
The documents describe what those tasks build.

## References & Rollback

- Spec §4.7
- `skills/doc_quality_check/SKILL.md`, Check 0
- The semantic-line-break convention applied to these files during release 1.2.0

**Rollback**: `git revert` the commit. Four prose files, no tooling impact.
