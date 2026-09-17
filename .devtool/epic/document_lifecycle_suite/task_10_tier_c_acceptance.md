---
id: "task_10_tier_c_acceptance"
status: "done"
priority: "high"
assignee: null
epic: "document_lifecycle_suite"
dueDate: null
created: "2026-09-17T09:00:00Z"
modified: "2026-09-16T19:18:33Z"
completedAt: "2026-09-16T19:18:33Z"
labels: ["integration", "acceptance", "evals"]
order: "a10"
---

# Task 10: Tier C — End-to-End Acceptance

Epic: [document_lifecycle_suite](document_lifecycle_suite.en.md)

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

Produced [`docs/choosing-a-lifecycle.en.md`](../../docs/choosing-a-lifecycle.en.md) — directions for
picking among the three lifecycles, a gap this repository genuinely had once `doc-lifecycle` and
`lean-product-lifecycle` joined `dev-lifecycle`.

- **Audience** established before any outline: someone in this repo holding a piece of work, who
  knows the domain and needs directions rather than teaching.
- **One Diátaxis type**: how-to guide — informs action, application of skill.
- **Six sections, six commits**, `46a2547` through `f99eeb0`, one per section.
- **Gate 2 failed on the first attempt.** Checks 0 and 1 were clean; the content audit returned
  *Issues Found* and *Acceptance: not met*. This is the single most valuable result of the whole
  acceptance task — the gate was not a formality.

### What Gate 2 caught that nothing else did

`check_document.py` passed the document with zero findings. `scripts/verify.sh` passed all nine
steps. Both were right: nothing mechanical was wrong. The content audit found four real defects
anyway.

| Finding | Why no mechanical check could have caught it |
|---|---|
| A sentence on the one-component code path was garbled, and it was the **only route on the page with no gate cost stated** — the most common case in this repo | Grammatical prose, resolving links, valid anchors |
| "There is nothing for a gate to do" sat two lines above "You still run a quality gate afterwards" — a reader fixing a typo could not tell which applied | Both sentences are true in isolation; only their adjacency is wrong |
| The handoff section promised three moves that "keep your work"; the third gave no artefact and no path, handing the reader to a skill that would restart them at Stage 1 cold | A promise a document fails to keep is invisible to any parser |
| **`doc-lifecycle` still named `quality_check` in its mermaid Gate 2 node and in its Stage 1 prose** | In a different file, not under review, and syntactically fine |

The fourth is the serious one. It is a defect in a skill this epic shipped, and it contradicts the
premise the split was built on — that the two gates never reference each other. It survived Task 6
because the rewrite replaced exact strings and missed two. `doc-implementation` carried a fifth
instance of the same drift, found while fixing it.

**A reviewer reading for meaning found what nine mechanical checks could not.** That is the argument
for check 3 existing, and it would have been unprovable if the gate had passed first time.

All findings fixed; Gate 2 re-run **in full** rather than re-running only check 3, per
`doc-lifecycle`'s own rule.

### Round two — the fix was worse than the defect

The full re-run failed again, and the most serious finding was **a regression introduced by the
round-one fix**.

Round one's finding was that the "code back to discovery" handoff gave the reader no artefact. The
fix told them to write `.devtool/product/<slug>/01_problem_space_spec.md` before invoking
`lean-product-lifecycle`, so Stage 1 would not start cold. That is exactly backwards.
`skills/lean-product-lifecycle/SKILL.md:188` resumes on file **presence**:

> `01_problem_space_spec.md` present → "Gate 1 is already verified. Resuming at Stage 2."

So the advice made the lifecycle **announce the problem space as validated and skip Stage 1** — for a
reader who arrived precisely because the problem space had never been validated. Stage 1 *is* the
validation being sought. The fix defeated the purpose of the move it was fixing, and it read as
helpful, specific and well-sourced.

Two further findings in the same round, both real:

- The one-plan code route ran `brainstorming` → `writing-plans` → quality gate with **nothing
  executing the plan**. `writing-plans` produces a document; the reader needed
  `subagent-driven-development` or `executing-plans` and was never told.
- The discovery route was costed at three gates. Gate 3 hands off to `dev-designer`, which is Stage 2
  of `dev-lifecycle` — so the true cost is **seven**. A reader budgeting three is off by more than
  double.

### What this run actually demonstrated

The point of "re-run the gate **in full**, never only the failing check" stopped being a principle
and became a measured result. Had round two re-run only check 3 against the unchanged sections, it
would still have caught the regression — but the rule's real value is that **a fix is new work and
new work is unverified**. The round-one fix passed every mechanical check, was internally consistent,
cited a real file path, and was wrong in a way only someone reading the target skill could see.

Three rounds of Gate 2 on a six-section document is not a sign the gate is too strict. It is the
measurement: one author, writing carefully, produced defects in two consecutive attempts, and the
mechanical half of the gate reported clean every single time.

### Round three — an ordering that merges before it verifies

Two findings, one of them worse than either previous round.

**The one-plan route told the reader to merge unverified code.** The page said to run the executor,
then "finish with `quality_check` and `finishing-a-development-branch`". But both executors call
`finishing-a-development-branch` **themselves**, as their terminal step, and neither mentions
`quality_check` at all — zero occurrences in either file. Following the page literally, the branch is
merged or PR'd *before* the quality gate ever runs. That is the exact outcome
`rules/CRITICAL_RULES.md` and `dev-lifecycle`'s Gate 4 exist to prevent, and the page was routing
people into it.

**A gate-worthy one-page document had no destination.** The threshold was written as "enough sections
that a reviewer could accept some and reject others", with two shortcuts below it: a single ADR, and
"anything smaller". A one-page runbook — `doc-lifecycle`'s own worked example — is neither
multi-section nor an ADR, so it fell into "anything smaller", which says skip every lifecycle. The
too-small section's own test ("can you imagine a reviewer rejecting it") then said the opposite. The
skill does not have this gap: its exclusion list ends with a **residual** test rather than a size
comparison. The page had replaced the residual with a size word and lost a case.

### A process gap in this run, found by the gate

The audit also observed that **no `Diátaxis mode` Meta Data existed on disk for this document**. The
type, audience and Acceptance criterion had been decided and stated in prose, but never written into
the artefact `doc-designer` specifies. `doc_quality_check` Check 2 reads the declared mode "from its
Meta Data" — so the next person to re-run Gate 2 would have had nothing to read, and Check 2 would
have been unrunnable rather than passing.

This is worth naming plainly: **the Stage 1 steps were followed and the Stage 1 artefact was not
produced.** Fixed by writing
[`.devtool/epic/choosing_a_lifecycle/choosing_a_lifecycle.en.md`](../epic/choosing_a_lifecycle/choosing_a_lifecycle.en.md)
and its `.vi.md`.

### Incidental: three skills carried a stale gate count

`dev-lifecycle`'s description said "the four approval gates" while its own table says five, and
`dev-designer` and `dev-implementation` repeated it. Pre-existing drift from when Gate 5 was added,
unrelated to this epic, corrected in passing.

### The measurement after three rounds

| | Rounds run | Rounds clean | Defects found |
|---|---|---|---|
| Mechanical (`check_document.py`, `verify.sh`) | 4 | **4** | 0 |
| Semantic (content audit) | 3 | 0 | 9 |

The mechanical half was right every time — nothing mechanical was ever wrong. It is simply not the
half that catches a document routing people into an unverified merge.

### Round four — a false claim about a named skill

One blocking finding, and again **the round-three fix created it**.

Round three's fix warned that both executors call `finishing-a-development-branch` themselves, then
added: *"once it reaches its finish step your branch is merged or PR'd, verified or not."* That is
false. `skills/finishing-a-development-branch/SKILL.md:97` reads *"Wait for their answer; the
integration decision is theirs."* It presents three options and stops. Nothing is merged or pushed
until a human answers.

The instruction attached to the false claim was also unfollowable. It said to run `quality_check`
"while the executor is still working", but `subagent-driven-development` mandates *"Continuous
execution: Do not pause to check in with your human partner between tasks"*, and `executing-plans`
runs straight into its finish step. There is no window mid-run, and forcing one would grade a
half-written branch.

Net effect: a reader would believe integration was automatic, find the only stated window
unreachable, and skip the quality gate — the exact outcome the paragraph was written to prevent.

The real window was sitting in plain sight: the executor **stops** at the three-option menu. Choose
option 3, run `quality_check`, fix, then finish and choose merge or PR.

### A severity bug in `doc_quality_check`, found by using it

The audit also noted that a typo fix in a file with no Meta Data — a README, a `SKILL.md` — would
return 🔴: Check 2 treated an absent `Diátaxis mode` as a finding, and 🟢 requires all four checks
clean. The routing was correct and the verdict was useless. Check 2 is now scoped: a missing mode is
a finding on a `doc-lifecycle` deliverable and **not applicable** on a file that never was one.
Returning 🔴 on a one-word fix teaches people to stop running the gate.

### The pattern, stated plainly

| Round | Defects found | Of which created by the previous round's fix |
|---|---|---|
| 1 | 4 | — |
| 2 | 3 | 1 |
| 3 | 2 | 1 |
| 4 | 1 | 1 |

**Three consecutive rounds surfaced a defect introduced while fixing the round before.** Each fix was
plausible, specific, cited a real file, and passed every mechanical check. Each was wrong in a way
visible only to someone who opened the skill being described and followed its control flow.

This is the measured case for `doc-lifecycle`'s rule that a failed Gate 2 is re-run **in full**. The
rule is not about the sections that did not change. It is that **a fix is new, unreviewed work, and
the person writing it is the person who just got it wrong.**

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
gate counts, pointing at `docs/choosing-a-lifecycle.en.md` rather than duplicating it — a README is not
a how-to guide, and inlining it would break the discipline this epic just shipped.

### Observed discrepancy, not fixed

`dev-implementation`'s SKILL.md states that `sync_task_status.py` *moves* completed tasks from
`.devtool/features/` into `.devtool/features/done/`. It does not: it updates frontmatter only, and
`done/` is empty with all eleven tasks still in `.devtool/features/`. The move appears to happen at
`archive-done` instead. Either the prose or the script is wrong. Out of scope here, and recorded so
the next person does not rediscover it.

### Round five — 🟢 Approved

Gate 2 passed. The auditor traced every instruction through the named skill's control flow, including
the two chains most likely to strand a reader: `doc-designer` → `doc-implementation` →
`finishing-a-development-branch`, and the one-plan code route. Both run to a finished branch. The
option-3 recovery path was verified end to end — Option 3 preserves branch *and* worktree,
`quality_check` runs against the working tree and its cleanup does not remove the worktree, and
re-invoking `finishing-a-development-branch` re-presents the menu. The advice produces what it
promises.

**Final defect count: 4 → 3 → 2 → 1 → 0.**

### Advisories deliberately not applied

Five advisories came back, none blocking. They are **not** applied, and the reason is the same rule
this task spent four rounds demonstrating: a fix is new, unreviewed work. Applying five edits after
approval and shipping without another audit would contradict the principle that the preceding rounds
established at some cost. The approved version is the version that ships.

Logged for a follow-up pass:

1. **"Pick option 3"** is true in a normal repo; in a **detached-HEAD** workspace
   `finishing-a-development-branch` presents only two options and "keep as-is" is option 2. The
   document names the label as well as the number, so a reader recovers — prefer the label.
2. **`executing-plans` is internally inconsistent.** Its procedure body runs straight through, but its
   own frontmatter says "with review checkpoints" and `writing-plans` advertises it the same way. The
   document is right about the behaviour; the kit disagrees with itself. **This is a real defect in
   `executing-plans`, not in the document.**
3. **"bumping a version"** overlaps `brainstorming`'s anti-pattern, which names a config change as
   still needing a short design. Narrow it to "bumping a version string".
4. **`writing-skills` is never named**, and for this repository editing a skill is the most common
   piece of work there is. Nobody is stranded — the page's own test routes a skill edit to the
   document branch — but a one-line pointer would close it for the stated audience.
5. **After fixing `quality_check` findings, say "re-run it in full"**, matching the rule both quality
   gates already carry.

Item 2 is the one worth acting on soonest: it is a contradiction inside a shipped skill, found only
because a document had to describe that skill accurately.

---

## Post-Gate-5 finding — epic archival was unreachable through the documented flow

Discovered while finishing the branch. Three components each assume another one moves the task
files, and none of them does:

| Component | What it assumes |
|---|---|
| `dev-implementation` prose | *"`sync_task_status.py` moves them from `.devtool/features/` into `.devtool/features/done/`"* |
| `sync_task_status.py` | `sync_task()` writes frontmatter only — the move lives in `archive_epic_tasks`, nowhere else |
| `finishing-a-development-branch` hook | guards on `ls .devtool/features/done/task_*.md` |
| `archive-done` command | its discovery also scans only `done/` |

Net effect: `done/` is always empty, so the hook never fires and `archive-done` reports *"No
completed tasks to archive."* **Archival never runs through the documented path.**

Worked around with `archive-epic <epic_dir>`, which takes the epic explicitly and whose
`archive_epic_tasks` does iterate both directories. 21 task copies archived, `features/` left clean.

### A second, separate defect — this one was mine

`sync_epic` flips the epic Status with a regex that matches a **bullet**:

```
- **Status**: Done
```

Every earlier epic in `.devtool/epic/` uses that format. **This epic's HLD used a table instead**
(`| **Status** | In-Progress |`), so the regex matched nothing. The script still printed
*"Synchronized 4 epic docs"* — it reports files visited, not fields changed — and `git diff` was
empty. Converted both language variants to the house bullet format; the flip then took.

Two things worth carrying forward:

1. **`dev-designer` specifies which Meta Data *fields* are required but not their *format*.** The
   tooling depends on the format. Either the skill should state it or the script should accept both.
2. **A sync script that reports success without verifying it changed anything** hides exactly this
   class of failure. The message should count fields written, not documents opened.

Neither is fixed here — both are defects in skills outside this epic's scope.
