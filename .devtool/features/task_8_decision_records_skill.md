---
id: "task_8_decision_records_skill"
status: "done"
priority: "medium"
assignee: null
epic: "document_lifecycle_suite"
dueDate: null
created: "2026-09-17T09:00:00Z"
modified: "2026-09-16T18:55:16Z"
completedAt: "2026-09-16T18:55:16Z"
labels: ["skill", "adr", "documentation"]
order: "a8"
---

# Task 8: `decision-records` Skill (ADR + Spike Report)

Epic: [document_lifecycle_suite](../epic/document_lifecycle_suite/document_lifecycle_suite.en.md)

## Requirement Analysis

Create `skills/decision-records/SKILL.md`, grounded in **Michael Nygard, *Documenting Architecture
Decisions* (2011)**, retained by [Task 1](task_1_primary_sources_and_fidelity_guard.md).

Record structure, in Nygard's own order: **Title / Context / Decision / Status / Consequences**.

Two rules come from the source itself, quoted in the epic's
[source fidelity review](../epic/document_lifecycle_suite/source_fidelity_review.md):

1. **One decision per record, immutable once `Accepted`.** Nygard: *"If a decision is reversed, we
   will keep the old one around, but mark it as superseded… It's still relevant to know that it
   *was* the decision, but is *no longer* the decision."* This is what separates an ADR from a wiki
   page, and why the history stays trustworthy.
2. **`Consequences` lists positive, negative *and* neutral outcomes.** Nygard: *"All consequences
   should be listed here, not just the 'positive' ones."* A record listing only benefits is a sales
   pitch.

A third rule is **this kit's own addition and must not be cited to Nygard** — his 2011 article does
not mention it:

3. **Name the alternatives that were rejected, and why.** This is precisely what nobody remembers
   six months later, and the reason teams reverse decisions that were correct. It comes from later
   ADR templates, not from the source; the skill must say so wherever it states the rule.

**Spike / research report variant**: Question / Method / Findings / Recommendation / Confidence /
**What would change this conclusion**. The last field is mandatory and forces the conclusion to be
falsifiable.

**Location**: `docs/adr/NNNN-kebab-title.md`, sequentially numbered, never renumbered.

**Relationship to `doc-lifecycle`**: a single ADR sits below the lifecycle's threshold — invoke this
skill directly and skip the gates. Reach for `doc-lifecycle` only when a batch of records is produced
or backfilled as one piece of work. The skill must say so, or every ADR will drag three gates behind it.

## Relevant Files & Context Pointers

- `skills/decision-records/SKILL.md` — to create
- `.devtool/epic/document_lifecycle_suite/source_fidelity_review.md` — Nygard's own wording
- `skills/doc-lifecycle/SKILL.md` — the threshold rule this skill points back to
- `docs/adr/` — to create, with the numbering convention documented
- `README.md` — inventory

## Design Rationale

Immutability is the rule most often dropped when ADRs are adopted, and dropping it quietly converts
the record into a wiki page that always agrees with the present — worthless exactly when someone
needs to know what was believed at the time. Encode it as a refusal, not a preference.

Applicable kit skills: `writing-skills`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: new `skills/decision-records/SKILL.md`; the `docs/adr/` convention.
- **Downstream callers**: none — additive and standalone. It may be referenced from `doc-lifecycle`'s
  `When NOT to use this`.
- **Cross-platform bridges**: none.
- **Coverage threshold**: not applicable.

## BDD SCENARIOS

```gherkin
Scenario: A decision is recorded  # [Tier A - Unit]
  Given a technical decision has been made
  When decision-records runs
  Then the record carries Title, Status, Context, Decision and Consequences
  And it is numbered sequentially under docs/adr/
  And the Consequences section contains at least one negative consequence
  And the rejected alternatives are named with the reason each was rejected
```

```gherkin
Scenario: An accepted record is never edited  # [Tier A - Unit]
  Given an ADR whose Status is Accepted
  When the decision it records is reversed
  Then the accepted record is left unmodified
  And a new record is written that supersedes it by number
  And no existing ADR number is reused or renumbered
```

```gherkin
Scenario: A record listing only benefits is rejected  # [Tier A - Unit]
  Given a draft ADR whose Consequences are all positive
  When the record is reviewed
  Then it is rejected as a sales pitch rather than a record
```

```gherkin
Scenario Outline: Legal ADR status transitions  # [Tier A - Unit]
  Given an ADR with status <from>
  When a transition to <to> is attempted
  Then it is <verdict>

  Examples:
    | from       | to         | verdict  |
    | Proposed   | Accepted   | allowed  |
    | Accepted   | Superseded | allowed  |
    | Accepted   | Proposed   | refused  |
    | Superseded | Accepted   | refused  |
```

```gherkin
Scenario: A spike report states what would refute it  # [Tier A - Unit]
  Given a research spike has produced a recommendation
  When the report is written
  Then it contains a "What would change this conclusion" section
  And that section is not empty
```

```gherkin
Scenario: A single ADR opens no gates  # [Tier C - Integration]
  Given one technical decision to record
  When decision-records is invoked
  Then no doc-lifecycle gate is opened
  And the record is written and committed directly
```

## Test & Verification Checklist

**TDD adaptation**: a skill plus a template. Verification is structural plus fixture-driven refusals.

- [ ] Confirm every ADR claim traces to a quotation in `source_fidelity_review.md`.
- [ ] **RED**: draft an ADR with only positive consequences; confirm the skill's rule rejects it.
- [ ] **RED**: attempt to edit an `Accepted` record; confirm the skill directs to supersession instead.
- [ ] **GREEN**: produce one real ADR for a decision already made in this epic — for example, why
      `quality_check` branches on `Kind` instead of a fourth skill being created.
- [ ] **Tier A/B**: `verify.sh` steps 1–7 pass, including the new ADR fidelity checks.

## Definition of Done

- `skills/decision-records/SKILL.md` exists with the five-section format, the three rules and the
  spike variant.
- The `docs/adr/` numbering convention is documented and one real ADR exists.
- The below-threshold rule pointing back to `doc-lifecycle` is stated.
- Added to the README inventory. `scripts/verify.sh` passes in full. Clean git status.

## Dependencies & Blockers

- Blocked by [Task 1](task_1_primary_sources_and_fidelity_guard.md).
- Blocks nothing. Additive — may slip a release without stranding anything.

## References & Rollback

- Michael Nygard, *Documenting Architecture Decisions*, 2011; quotations in the epic's
  `source_fidelity_review.md`.
- **Rollback**: delete the skill, its README entry and `docs/adr/`. Nothing depends on it.
