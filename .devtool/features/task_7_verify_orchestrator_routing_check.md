---
id: "task_7_verify_orchestrator_routing_check"
status: "todo"
priority: "high"
assignee: null
epic: "brainstorming_split"
dueDate: null
created: "2026-09-17T09:27:07Z"
modified: "2026-09-17T09:27:07Z"
completedAt: null
labels: ["tooling", "governance", "verification"]
order: "a7"
---

# Task 7: Add the Orchestrator-Routing Check to `verify.sh`

Epic: [brainstorming_split](../epic/brainstorming_split/brainstorming_split.en.md)

## Requirement Analysis

Add a tenth step asserting that **no orchestrator names the router**. Each lifecycle stage must
name a concrete variant, because the router's job is to resolve an ambiguous entry — a stage that
routes to it has simply moved the ambiguity one hop downstream.

```bash
git ls-files 'skills/dev-lifecycle/*' 'skills/doc-lifecycle/*' \
  | xargs grep -n 'd3nexus:brainstorming\|`brainstorming`'
# must be empty
```

**Why the release-1.2.0 rename check cannot be reused.** Step 9 greps
`epic-lifecycle|epic-designer|epic-implementation` and works because those are unambiguous
identifiers. `brainstorming` is an ordinary English word. It appears legitimately in:

- `skills/writing-plans/SKILL.md` — "should have been broken into sub-project specs during
  brainstorming"
- `skills/dev-designer/SKILL.md` — "not a full brainstorming dialogue"
- `skills/doc_quality_check/references/document-reviewer-prompt.md:11` — a deliberately preserved
  pre-1.2.0 path
- `scripts/verify.sh:129` — a comment naming that same historical path

A bare rename sweep would fail on all four. The narrow check greps only the two orchestrators, and
only for the two *skill-reference* forms, so English prose about brainstorming never trips it.

This check also targets a failure mode with precedent: `epic-lifecycle` never contained the word
"invoke", so agents read a stage description and did that stage's work themselves. A stage naming
the router recreates that ambiguity.

## Relevant Files & Context Pointers

- `scripts/verify.sh` — currently 9 steps; step 9 is the `dev-*` rename check at lines 171–189
- `scripts/verify.sh:129` — the comment that must not trip the new check
- `skills/dev-lifecycle/SKILL.md`, `skills/doc-lifecycle/SKILL.md` — the two files checked
- Spec §5.2, §6 item 2

## Design Rationale

**Why `git ls-files` rather than a filesystem walk.** During release 1.2.0 a filesystem walk read
the gitignored `.superpowers/` directory, which exists in a normal checkout but not in a worktree.
The check passed in the worktree and failed on `main`. Step 9 was rewritten to drive from
`git ls-files` for that reason, and this step follows it.

**Why step 9 is left exactly as it is.** It guards a different rename that is already complete.
Merging the two checks would couple an old invariant to a new one for no benefit.

**Why the check is narrow rather than thorough.** A thorough check here is impossible: no grep can
distinguish "the skill named brainstorming" from "the activity of brainstorming" in prose. Scoping
to two files and two reference forms makes it exact instead.

Applicable kit skills: none — this is shell tooling.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `scripts/verify.sh`; the new step 10.
- **Downstream callers**: every future release runs `verify.sh`. A false positive here blocks
  releases, so the grep pattern is the risk, not the logic.
- **Cross-platform bridges**: none.
- **Target verification threshold**: the check must fail on a deliberately broken orchestrator and
  pass on the real one — both proven, not assumed.

## BDD SCENARIOS

```gherkin
Scenario: [Tier B - Governance] The check passes against the corrected orchestrators
  Given dev-lifecycle names dev-brainstorming and doc-lifecycle names doc-brainstorming
  When verify.sh step 10 runs
  Then it reports ok
  And the overall run is green

Scenario: [Tier B - Governance] The check fails when an orchestrator names the router
  Given dev-lifecycle Stage 1 is temporarily edited to say d3nexus:brainstorming
  When verify.sh step 10 runs
  Then it fails
  And its message names the offending file and line

Scenario: [Tier B - Governance] English prose about brainstorming does not trip the check
  Given writing-plans says "during brainstorming" and dev-designer says "not a full brainstorming dialogue"
  When verify.sh step 10 runs
  Then neither file is examined
  And the check passes

Scenario: [Tier B - Governance] The preserved provenance path does not trip the check
  Given document-reviewer-prompt.md line 11 names skills/brainstorming/spec-document-reviewer-prompt.md
  When verify.sh step 10 runs
  Then that file is not examined
  And the check passes

Scenario: [Tier B - Governance] verify.sh's own comment does not trip the check
  Given scripts/verify.sh line 129 names the historical orphan path
  When step 10 runs
  Then it does not examine verify.sh
  And the check passes

Scenario: [Tier B - Governance] The check reads tracked files only
  Given an untracked or gitignored copy of an orchestrator exists under .superpowers/
  When verify.sh step 10 runs
  Then that copy is not examined

Scenario: [Tier B - Governance] Step 9 is unchanged
  Given scripts/verify.sh
  When step 9 is diffed against its state before this task
  Then there are zero changes

Scenario: [Tier C - Integration] The full suite passes from a normal checkout
  Given a normal checkout with .superpowers/ present
  When scripts/verify.sh runs in full
  Then all ten steps pass
```

## Test & Verification Checklist

- [ ] **RED**: temporarily edit `dev-lifecycle` Stage 1 to name `d3nexus:brainstorming`, run the
      new step, and confirm it **fails**. A check never seen failing is not a check.
- [ ] **GREEN**: revert the edit; confirm the step passes.
- [ ] **REFACTOR**: confirm the grep pattern matches only the two skill-reference forms.
- [ ] **Tier B**: run `verify.sh` in full; all ten steps green.
- [ ] **Tier B**: confirm step 9 is byte-for-byte unchanged.
- [ ] **Tier C**: run `verify.sh` from a **normal checkout**, not a worktree — this is the exact
      difference that hid a bug during release 1.2.0.

## Definition of Done

- `verify.sh` has a tenth step implementing the narrow check, driven from `git ls-files`.
- The check has been **observed failing** on a deliberately broken orchestrator and passing after.
- All four known legitimate uses of the word "brainstorming" confirmed not to trip it.
- Step 9 byte-for-byte unchanged.
- Full `verify.sh` green from a normal checkout.
- Clean `git status` after the commit.

## Dependencies & Blockers

Blocked by [Task 4](task_4_doc_lifecycle_mandatory_stage_0.md) and
[Task 5](task_5_dev_lifecycle_retarget.md) — both orchestrators must already name variants, or the
new check fails on landing.

## References & Rollback

- Spec §5.2, §6
- `scripts/verify.sh` step 9 and its `git ls-files` rationale
- The worktree-versus-checkout bug from release 1.2.0

**Rollback**: `git revert` the commit. A single added step in one shell script; removing it cannot
break the other nine.
