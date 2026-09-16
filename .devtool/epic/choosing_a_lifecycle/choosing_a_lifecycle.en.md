# Document: Choosing a lifecycle

## 1. Meta Data

```
Kind: document
Audience: Someone working in this repository who has a piece of work in front of them and does not
          know which lifecycle to enter. They know the domain — they work here — so they need
          directions, not teaching.
Diátaxis mode: how-to guide
Non-goals: Explaining why the lifecycles exist, teaching any individual skill, or describing what
           happens inside a lifecycle once you are in it. Each skill documents itself.
Acceptance: A person with a piece of work reaches the correct lifecycle, and knows what it will cost
            them in gates, without asking anyone.
Deliverable: docs/choosing-a-lifecycle.md
Source Spec: none — this document was produced as the Tier C acceptance exercise for the
             document_lifecycle_suite epic.
```

## 2. Why this document exists

Until this epic there was one lifecycle. There are now three, and nothing told a reader which one
their work belongs to. `README.md` names them; it does not route.

## 3. Diátaxis classification

The reader's question is *"what should I do now"* — it **informs action** and serves the
**application** of skill they already have. By Procida's compass that is a **how-to guide**, and
exactly one type applies: no part of this document teaches a newcomer (tutorial), lists parameters
(reference), or argues a position (explanation).

## 4. Outline

| # | Section | Purpose |
|---|---|---|
| 1 | Start here | Get the reader to the right branch with one question |
| 2 | If you are writing code | Route to dev-lifecycle or writing-plans by number of reviewable pieces, and name who executes the plan |
| 3 | If you are writing a document | Route to doc-lifecycle, and give the threshold below which it does not apply |
| 4 | If you do not know what to build yet | Route up to lean-product-lifecycle, with its true end-to-end gate cost |
| 5 | If the work is too small | Permit skipping every lifecycle, while keeping the quality gate |
| 6 | Handing off between lifecycles | Move between branches without losing work or falsely passing a gate |

## 5. Verification

Gate 2 is `doc_quality_check`. It failed twice before passing; the rounds and what they caught are
recorded in
[`../document_lifecycle_suite/task_10_tier_c_acceptance.md`](../document_lifecycle_suite/task_10_tier_c_acceptance.md).

## 6. Kanban Tasks Breakdown

None. The Concurrent-Epic Backlog Rule applies: `document_lifecycle_suite` has an active task, so any
task file generated here would be created as `status: "backlog"` and could not be worked. The six
sections were drafted directly, one commit each, and the breakdown is the outline above.
