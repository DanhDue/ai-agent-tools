---
id: "task_1_primary_sources_and_fidelity_guard"
status: "todo"
priority: "high"
assignee: null
epic: "document_lifecycle_suite"
dueDate: null
created: "2026-09-17T09:00:00Z"
modified: "2026-09-17T09:00:00Z"
completedAt: null
labels: ["research", "governance", "fidelity"]
order: "a1"
---

# Task 1: Fetch Primary Sources & Generalize the Fidelity Guard

Epic: [document_lifecycle_suite](document_lifecycle_suite.en.md)

## Requirement Analysis

Two external methodologies enter the kit in this epic: **Diátaxis** (Daniele Procida) in
`doc-designer`, and **Architecture Decision Records** (Michael Nygard, *Documenting Architecture
Decisions*, 2011) in `decision-records`. Neither is in `docs/books/`.

This repository already holds the line that methodology skills are written from primary sources.
`scripts/check_source_fidelity.py` and
[`.devtool/epic/lean_product_suite/source_fidelity_review.md`](../lean_product_suite/source_fidelity_review.md)
exist because six behaviour-changing errors reached the Lean Product suite through LLM-written
summaries and propagated through four layers of derived artefacts before anyone opened the book.

That risk already materialised inside this very epic, before implementation began: the first draft
of the sibling assumption-mapping spec inverted the Assumptions Map axes and invented field names
for tools that already have canonical ones. It read as authoritative and was wrong. Writing Diátaxis
or ADR text from recall would reproduce exactly that failure.

**No methodology text is written anywhere in this epic until this task lands.**

Deliverables:

1. Fetch and retain both primary sources (the Diátaxis site by Daniele Procida; Nygard's 2011
   article).
2. Write `source_fidelity_review.md` in the epic directory: for each methodology, the author's own
   wording for the rules the skills will encode, and any point where common summaries differ.
3. Generalize `scripts/check_source_fidelity.py`. It is currently titled and scoped to the Lean
   Product suite; it must become a registry of (source, label, pattern) checks so this epic and
   future ones can add their own without forking the script. Existing Lean checks must keep passing
   unchanged.

## Relevant Files & Context Pointers

- `scripts/check_source_fidelity.py` — the guard to generalize
- `scripts/verify.sh` — step 7 invokes it; the step title must stop naming only the Lean suite
- `.devtool/epic/lean_product_suite/source_fidelity_review.md` — the format to follow
- `.devtool/epic/document_lifecycle_suite/source_fidelity_review.md` — to create
- `docs/books/` — where a retained source belongs if it is a file

## Design Rationale

Follow the existing `(label, pattern)` model: the label states the **correct** rule so a failure
explains itself without opening another document. Generalization means grouping those pairs by
source, not rewriting the mechanism.

Applicable kit skills: `writing-skills` (authoring standard), `d3nexus:verification-before-completion`
(evidence before claiming the fetch succeeded).

## Impact Analysis & Blast Radius

- **Target files & symbols**: `check_source_fidelity.py` CHECKS registry; `verify.sh` step 7 label.
- **Downstream callers**: `scripts/verify.sh` only. No skill invokes the script directly.
- **Cross-platform bridges**: none.
- **Coverage threshold**: not applicable — this repository has no coverage instrumentation. The
  guard is proven by the RED step below instead.

## BDD SCENARIOS

```gherkin
Scenario: The primary source cannot be reached  # [Tier A - Unit]
  Given the Diátaxis source cannot be fetched
  When a task would write Diátaxis methodology text
  Then no methodology text is written
  And the task reports the fetch failure rather than writing from recall
```

```gherkin
Scenario: Existing Lean checks survive generalization  # [Tier B - Governance]
  Given the generalized check_source_fidelity.py
  When scripts/verify.sh step 7 runs against the current tree
  Then every Lean Product check still runs
  And the result is unchanged from before the refactor
```

```gherkin
Scenario: A reintroduced error is caught  # [Tier B - Governance]
  Given a new fidelity check for a Diátaxis or ADR rule
  When text contradicting that rule is added to any skill
  Then scripts/verify.sh fails
  And the failure message states the correct rule
```

## Test & Verification Checklist

**TDD adaptation**: this task produces documentation and a pattern registry, not behaviour with unit
tests. The RED/GREEN cycle applies to the guard itself.

- [ ] **RED**: add each new fidelity check, then deliberately insert the error it targets into a
      scratch copy and confirm `verify.sh` fails. A check that never fails proves nothing.
- [ ] **GREEN**: remove the inserted errors; confirm `verify.sh` step 7 passes.
- [ ] **Tier A**: `scripts/verify.sh` steps 1–4 pass.
- [ ] **Tier B**: `scripts/verify.sh` step 7 passes with both the Lean checks and the new ones.
- [ ] Confirm the fetched sources are retained and cited by path or URL in `source_fidelity_review.md`.

## Definition of Done

- Both primary sources fetched and retained.
- `source_fidelity_review.md` exists, quoting the authors' own wording for every rule Tasks 4 and 8
  will encode.
- `check_source_fidelity.py` is source-agnostic; Lean checks pass unchanged; new checks demonstrably
  fail when their target error is reintroduced.
- `scripts/verify.sh` passes in full. Clean git status.

## Dependencies & Blockers

- Blocks [Task 4](task_4_doc_designer_skill.md) and [Task 8](task_8_decision_records_skill.md).
- Blocked by: nothing.

## References & Rollback

- Diátaxis — Daniele Procida, diataxis.fr
- Michael Nygard, *Documenting Architecture Decisions*, 2011
- **Rollback**: revert the commit. `check_source_fidelity.py` returns to its Lean-only form and the
  epic is blocked again — which is the correct state if the sources could not be obtained.
