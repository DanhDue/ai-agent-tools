---
id: "task_6_consumer_retarget"
status: "done"
priority: "medium"
assignee: null
epic: "brainstorming_split"
dueDate: null
created: "2026-09-17T09:27:07Z"
modified: "2026-09-17T09:37:07Z"
completedAt: "2026-09-17T09:37:07Z"
labels: ["skills", "rename", "governance"]
order: "a6"
---

# Task 6: Retarget the Remaining Live Consumers

Epic: [brainstorming_split](brainstorming_split.en.md)

## Requirement Analysis

Eight files whose references must move to a variant, and four groups that must **not** be touched.
The exclusions carry as much weight as the changes here — three of the four would look like
oversights to a later reader, and one of them would be a false positive for Task 7's check.

**Retarget:**

| File | Count | To |
|---|---|---|
| `skills/dev-designer/SKILL.md` | 6 | `dev-brainstorming` |
| `skills/doc-designer/SKILL.md` | 2 | `doc-brainstorming` |
| `skills/dev-implementation/SKILL.md` | 1 | `dev-brainstorming` |
| `skills/writing-plans/SKILL.md` | 1 | `dev-brainstorming` |
| `skills/impact-analysis/SKILL.md` | 3 | `dev-brainstorming` |
| `skills/impact-analysis/references/impact-mechanisms.md` | 1 | `dev-brainstorming` |
| `skills/lean-product-lifecycle/SKILL.md` | 2 | see below |
| `templates/AGENTS.md` | 1 | `dev-brainstorming` |
| `rules/CRITICAL_RULES.md` | 2 | see below |

`lean-product-lifecycle` line 37 routes small work — "a single bug, a refactor, a change to an
existing feature" — all unambiguously code, so it becomes `dev-brainstorming`. Line 79's mermaid
entry node says "Arrives here from brainstorming's step-2 escape" and becomes "from either
brainstorming variant's step-2 escape", because spec §3.4 splits that escape across both.

`CRITICAL_RULES.md` has two sites with different answers. The link at line 61 targets the router
and stays — that is the correct destination for "single features or exploratory design". The
orchestration chain at line 62 lists `brainstorming -> dev-designer -> dev-implementation ->
quality_check` and becomes `dev-brainstorming`, because it describes the development lifecycle
specifically.

**Do not touch:**

1. `skills/using-superpowers/SKILL.md` (2) and `hooks/session-start` (1) — both describe an
   unclassified request, so the router is the right destination.
2. `skills/doc_quality_check/references/document-reviewer-prompt.md:11` — records the pre-1.2.0
   path `skills/brainstorming/spec-document-reviewer-prompt.md` as provenance. Editing it falsifies
   the record.
3. `.devtool/epic/**` — historical epic records.
4. `CHANGELOG.md` history — same reason. Task 9 appends a new entry; it does not rewrite old ones.

## Relevant Files & Context Pointers

- The nine files in the retarget table
- `skills/doc_quality_check/references/document-reviewer-prompt.md:11` — the deliberate
  false-positive that Task 7's check must tolerate
- `scripts/verify.sh:129` — a comment naming the same historical path, also left alone
- Spec §4.4, §4.7, §5.2

## Design Rationale

**Why these are one task and not nine.** Every change is the same operation with the same risk
profile: a string in prose pointing at a skill name. Splitting them into nine commits would be
ceremony. The two files needing judgement — `lean-product-lifecycle` and `CRITICAL_RULES.md` — are
called out individually above so the judgement is recorded rather than buried in a diff.

**Why the exclusions are written down.** `brainstorming` is an ordinary English word. Without an
explicit list, a later reader sweeping for stragglers would "fix" the provenance note and the
historical records, destroying exactly the information those files exist to hold.

Applicable kit skills: `d3nexus:writing-skills`; `d3nexus:impact-analysis` for confirming the
blast radius has not grown since Check 1.

## Impact Analysis & Blast Radius

- **Target files & symbols**: nine files; the skill names `brainstorming`, `dev-brainstorming`,
  `doc-brainstorming`.
- **Downstream callers**: `docs/` is Task 8's; `.devtool/` is excluded by design.
- **Cross-platform bridges**: none.
- **Target verification threshold**: every retargeted reference resolves to a skill that exists;
  all four excluded groups byte-for-byte unchanged.

## BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] Every retargeted reference names a skill that exists
  Given the nine retargeted files
  When each skill reference is resolved against the skills directory
  Then every one resolves

Scenario: [Tier A - Unit] The provenance note is untouched
  Given skills/doc_quality_check/references/document-reviewer-prompt.md
  When it is diffed against its state before this task
  Then there are zero changes

Scenario: [Tier A - Unit] Historical records are untouched
  Given .devtool/epic/ and CHANGELOG.md
  When they are diffed against their state before this task
  Then there are zero changes

Scenario: [Tier A - Unit] The hook and using-superpowers still name the router
  Given hooks/session-start and skills/using-superpowers/SKILL.md
  When their brainstorming references are read
  Then each names brainstorming, not a variant

Scenario: [Tier A - Unit] CRITICAL_RULES treats its two sites differently
  Given rules/CRITICAL_RULES.md
  When line 61 and line 62 are read
  Then the link at 61 still targets skills/brainstorming/SKILL.md
  And the orchestration chain at 62 names dev-brainstorming

Scenario: [Tier A - Unit] The lean small-work route reaches the development variant
  Given skills/lean-product-lifecycle/SKILL.md line 37
  When it is read
  Then it names dev-brainstorming

Scenario: [Tier A - Unit] The lean entry node acknowledges both variants
  Given the lean-product-lifecycle mermaid entry node
  When it is read
  Then it says the escape arrives from either brainstorming variant
  And the diagram renders

Scenario: [Tier A - Unit] doc-designer names the documentation variant
  Given skills/doc-designer/SKILL.md
  When its two references are read
  Then both name doc-brainstorming

Scenario: [Tier C - Integration] dev-designer's spec relocation instruction still works
  Given dev-designer receives an approved spec from dev-brainstorming
  When it runs its self-sufficiency check on spec placement
  Then the instruction names dev-brainstorming as the relocating skill
  And the relocation behaviour is unchanged
```

## Test & Verification Checklist

**TDD adaptation**: reference updates only. RED is a per-file grep count that must reach the
expected value.

- [ ] **RED**: record the current per-file counts from the retarget table and confirm they match.
- [ ] **GREEN**: retarget each file; apply the two judgement calls as written above.
- [ ] **REFACTOR**: none — surgical changes only, no adjacent improvement.
- [ ] **Tier A**: `verify.sh` steps 1–4 pass.
- [ ] **Mermaid**: the `lean-product-lifecycle` diagram renders after its node edit.
- [ ] **Tier B**: `git diff --stat` touches exactly nine files and none of the four excluded groups.
- [ ] **Tier C**: Task 7's check passes; `verify.sh` full run is green.

## Definition of Done

- All nine files retargeted; every reference resolves to an existing skill.
- The two judgement calls applied and visible in the diff.
- All four excluded groups byte-for-byte unchanged, confirmed by `git diff --stat`.
- `verify.sh` steps 1–4 green; the lean mermaid renders.
- Clean `git status` after the commit.

## Dependencies & Blockers

Blocked by [Task 1](task_1_dev_brainstorming_rename.md) and [Task 3](task_3_doc_brainstorming_skill.md).
Both targets must exist.
Blocks [Task 8](task_8_docs_bilingual_update.md).

## References & Rollback

- Spec §4.4, §4.7, §5.2
- HLD §4.4, the blast radius table and its exclusions

**Rollback**: `git revert` the commit. Nine files, string changes only.
