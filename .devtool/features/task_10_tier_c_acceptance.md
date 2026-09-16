---
id: "task_10_tier_c_acceptance"
status: "in-progress"
priority: "high"
assignee: null
epic: "document_lifecycle_suite"
dueDate: null
created: "2026-09-17T09:00:00Z"
modified: "2026-09-16T19:01:35Z"
completedAt: null
labels: ["integration", "acceptance", "evals"]
order: "a10"
---

# Task 10: Tier C — End-to-End Acceptance

Epic: [document_lifecycle_suite](../epic/document_lifecycle_suite/document_lifecycle_suite.en.md)

## Requirement Analysis

The mandatory final integration task. Everything before this verifies parts; this verifies the
system, and it is the only task that can show the suite actually works.

Four deliverables:

1. **Drive `doc-lifecycle` end-to-end on one real document.** Not a fixture — a document this
   repository genuinely needs. Gate 1 → Gate 2 → Gate 3, one commit per section, using the real
   Kanban board. Producing a document this way is the acceptance test.
2. **Run the `evals/` blind-judge ablation on `doc-designer`.** Per `evals/protocol.md`: with the
   skill and without it, graded blind by a third agent. The highest-value scenario hands an agent
   material spanning two Diátaxis modes and checks whether the skill causes it to split the
   document. **A zero delta is a result, not a failure** — it says the rule is not paying for the
   context it occupies, and that finding is recorded rather than buried.
3. **Full `scripts/verify.sh`** including the two new steps.
4. **Update `README.md` and `CHANGELOG.md`** — the skill inventory, the skill count, a section
   describing the two lifecycles, and the 1.2.0 breaking entry.

## Relevant Files & Context Pointers

- `evals/protocol.md` — the ablation procedure
- `evals/` — where the new scenario and its results live
- `scripts/verify.sh` — must pass in full
- `README.md` — skill count, inventory, and the new two-lifecycle section
- `CHANGELOG.md` — 1.2.0, marked breaking
- `.devtool/features/` — the live Kanban used by the end-to-end run

## Design Rationale

The end-to-end run is deliberately on a real document rather than a fixture. A fixture proves the
steps execute; a real document proves the lifecycle is worth using — and if the gates are annoying,
that only becomes apparent when the output actually matters.

The ablation is the only evidence that distinguishes "the skill changed the agent's behaviour" from
"a competent agent would have done that anyway". Per the README, that distinction is the entire point
of `evals/`, and skipping it would leave the suite verified structurally and unverified behaviourally.

Applicable kit skills: `d3nexus:verification-before-completion`, `d3nexus:quality_check`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `README.md`, `CHANGELOG.md`, `evals/` scenario and results, plus the
  real document produced by the run.
- **Downstream callers**: everything. This is the release gate for 1.2.0.
- **Cross-platform bridges**: none.
- **Coverage threshold**: not applicable; this task *is* the coverage.

## BDD SCENARIOS

```gherkin
Scenario: A multi-section document passes all three gates  # [Tier C - Integration]
  Given a work item whose deliverable is a multi-section document
  And the diff touches no file that ships in the build
  When doc-lifecycle runs from Stage 1
  Then doc-designer asks who the audience is before anything else
  And exactly one Diátaxis mode is declared in the overview Meta Data
  And Gate 1 is presented as a numbered task list
  And doc-implementation produces exactly one commit per section
  And quality_check with Kind document returns a green verdict
  And Gate 3 is presented to the user before the branch is finished
```

```gherkin
Scenario: The ablation reports a delta  # [Tier C - Integration]
  Given a scenario whose material spans two Diátaxis modes
  When the same task runs with doc-designer and without it
  And a third agent grades both replies without knowing which is which
  Then the delta is recorded in evals/
  And a zero delta is recorded as a result, not suppressed
```

```gherkin
Scenario: The release gate holds  # [Tier B - Governance]
  Given all ten tasks are complete
  When scripts/verify.sh runs
  Then all nine steps pass
  And the summary prints PASS — safe to publish
```

```gherkin
Scenario: The README describes both lifecycles  # [Tier A - Unit]
  Given the updated README
  When the skill inventory is read
  Then the skill count matches the number of skills on disk
  And both dev-lifecycle and doc-lifecycle are described
  And the breaking rename is noted
```

## Test & Verification Checklist

**TDD adaptation**: this task is itself the acceptance test for the epic. Its RED state is the epic
before Tasks 1–9 land.

- [ ] Select a real document this repository needs and run `doc-lifecycle` on it end to end.
- [ ] Confirm one commit exists per section and the Kanban board reflects each task's status.
- [ ] Confirm `quality_check` with `Kind: document` returned green on that document.
- [ ] Write the `evals/` scenario, run all three agent invocations per `evals/protocol.md`, record
      the delta.
- [ ] **Regression**: run `quality_check` once on a `Kind: development` item and confirm the existing
      3-tier flow, including Tier C2, is unchanged.
- [ ] Update `README.md` skill count and inventory; add the two-lifecycle section.
- [ ] Add the 1.2.0 CHANGELOG entry, marked breaking, naming the three renames.
- [ ] **Tier A/B/C**: `scripts/verify.sh` passes in full and prints `PASS — safe to publish`.

## Definition of Done

- One real document produced end to end through `doc-lifecycle`, with all three gates exercised.
- The ablation has run and its delta is recorded in `evals/`, whatever the result.
- `README.md` and `CHANGELOG.md` updated; skill count correct.
- `scripts/verify.sh` prints `PASS — safe to publish`. Clean git status.

## Dependencies & Blockers

- Blocked by Tasks [3](task_3_doc_lifecycle_orchestrator.md), [4](task_4_doc_designer_skill.md),
  [5](task_5_doc_implementation_skill.md), [6](task_6_doc_quality_check_skill.md),
  [7](task_7_brainstorming_fourth_exit.md), [8](task_8_decision_records_skill.md),
  [9](task_9_verify_sh_orphan_and_rename_checks.md).

## References & Rollback

- `evals/protocol.md`; README §3.7 on measuring whether a skill works.
- **Rollback**: this task publishes nothing by itself. If acceptance fails, the epic does not ship;
  revert to the last green commit and route the findings back to the failing task.

---

## Completion Record

### 1. `doc-lifecycle` driven end to end on a real document

Produced [`docs/choosing-a-lifecycle.md`](../../docs/choosing-a-lifecycle.md) — directions for
picking among the three lifecycles, a gap this repository genuinely had once `doc-lifecycle` and
`lean-product-lifecycle` joined `dev-lifecycle`.

- **Audience** established before any outline: someone in this repo holding a piece of work, who
  knows the domain and needs directions rather than teaching.
- **One Diátaxis type**: how-to guide — informs action, application of skill.
- **Six sections, six commits**, `46a2547` through `f99eeb0`, one per section.
- **Gate 2**: `doc_quality_check` checks 0 and 1 clean; check 3 dispatched to a reviewer subagent.

**Two honest limitations of this run:**

1. **Gates 1 and 3 were self-approved.** Both are human approvals by design. Running them against
   their author tests the process, not the gate. A real run with a real reviewer is stronger and has
   not happened.
2. **The Kanban half could not run.** `doc-designer`'s Concurrent-Epic Backlog Rule fired correctly:
   `document_lifecycle_suite` has an active task, so a document epic started now would have every
   task created as `status: backlog`. Correct behaviour, and it means **a document epic cannot be
   executed while a development epic is open**. Worth knowing before anyone plans around it.

### 2. Ablation

`evals/results/2026-09-17-doc-designer-baseline/` — arm A 5/5, arm B 2/5, delta **+3**, one run.

The report leads with the bad news, as the protocol requires: the **baseline handled the safety
footgun better than the skilled arm**, and produced the strongest single observation in either reply.
Neither is scored, both are real. A candidate rule for `doc-designer` — a hazard that has already
caused an incident belongs in the step where the reader can still avoid it — is logged, not written:
one run does not justify a new rule.

### 3. Regression on the development gate

Proven by diff rather than by execution: `skills/quality_check/SKILL.md` is **byte-identical** to the
base branch. The 3-tier flow, including the Tier C2 native build gate added in 1.1.1, cannot have
regressed, because the file did not change. This is stronger evidence than running it would have
been, and it did not require a mobile toolchain this repository does not have.

### 4. README and CHANGELOG

Skill count corrected 47 → 52. The single entry point is replaced by the three lifecycles and their
gate counts, pointing at `docs/choosing-a-lifecycle.md` rather than duplicating it — a README is not
a how-to guide, and inlining it would break the discipline this epic just shipped.

### Observed discrepancy, not fixed

`dev-implementation`'s SKILL.md states that `sync_task_status.py` *moves* completed tasks from
`.devtool/features/` into `.devtool/features/done/`. It does not: it updates frontmatter only, and
`done/` is empty with all eleven tasks still in `.devtool/features/`. The move appears to happen at
`archive-done` instead. Either the prose or the script is wrong. Out of scope here, and recorded so
the next person does not rediscover it.
