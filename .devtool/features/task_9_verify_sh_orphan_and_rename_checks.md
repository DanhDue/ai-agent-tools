---
id: "task_9_verify_sh_orphan_and_rename_checks"
status: "done"
priority: "high"
assignee: null
epic: "document_lifecycle_suite"
dueDate: null
created: "2026-09-17T09:00:00Z"
modified: "2026-09-16T18:53:13Z"
completedAt: "2026-09-16T18:53:13Z"
labels: ["tooling", "governance", "verification"]
order: "a9"
---

# Task 9: Two New `verify.sh` Checks — Orphan and Rename Completeness

Epic: [document_lifecycle_suite](../epic/document_lifecycle_suite/document_lifecycle_suite.en.md)

## Requirement Analysis

Add two steps to `scripts/verify.sh`, following its existing shape (`note` / `fail`, inline
`python3` heredoc, `FAILED=1` on error).

**Step 8 — Orphan check.** Fail if any *supporting* file under `skills/*/` is referenced by no other
file in the repository. Each skill's own `SKILL.md` is **exempt** — it is the entry point by
definition, and without that exemption the check fires on every skill in the kit.

This check exists because it already has a victim. `skills/brainstorming/spec-document-reviewer-prompt.md`
is 49 lines of working reviewer prompt that nothing referenced; it was written and never wired in,
and nothing prevented that from recurring. **Run against the pre-Task-6 tree the check must fail on
that file. If it passes, the check itself is broken** — this is the acceptance criterion, not a
nice-to-have.

**Step 9 — Rename completeness.** Fail if `epic-designer`, `epic-implementation` or `epic-lifecycle`
appears anywhere outside `.devtool/` and the historical entries in `CHANGELOG.md`.

## Relevant Files & Context Pointers

- `scripts/verify.sh` — 134 lines; add steps 8 and 9 before the final summary block
- `skills/brainstorming/spec-document-reviewer-prompt.md` — the known orphan used to prove step 8
- `scripts/check_source_fidelity.py` — the generalized guard from Task 1, invoked at step 7

## Design Rationale

Both checks turn a past incident into a permanent guard, which is the same reasoning that produced
`check_source_fidelity.py`. A rule nobody can violate silently is worth more than a rule written more
emphatically.

The `SKILL.md` exemption is the difference between a check that runs and a check that gets disabled
the first week: without it, every skill in the kit fails and the step is deleted rather than fixed.

**A check that has never failed is unproven.** Both steps must be demonstrated against a tree where
the defect exists.

Applicable kit skills: `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `scripts/verify.sh` steps 8 and 9.
- **Downstream callers**: `scripts/release.sh` and the pre-publish workflow; a false positive here
  blocks every release, so the exemption logic matters more than the detection logic.
- **Cross-platform bridges**: none.
- **Coverage threshold**: not applicable — proven by deliberate defect injection.

## BDD SCENARIOS

```gherkin
Scenario: An unreferenced supporting file fails the build  # [Tier B - Governance]
  Given a file under skills/<name>/ that no other file in the repository references
  And that file is not a SKILL.md
  When scripts/verify.sh runs
  Then the orphan check fails and names the file
```

```gherkin
Scenario: The orphan check is proven against a known defect  # [Tier B - Governance]
  Given the repository state before Task 6 relocated the reviewer prompt
  When the orphan check runs
  Then it fails on skills/brainstorming/spec-document-reviewer-prompt.md
  And a passing result means the check itself is broken
```

```gherkin
Scenario: SKILL.md is exempt  # [Tier B - Governance]
  Given every skill's own SKILL.md
  When the orphan check runs
  Then no SKILL.md is reported
  And the check does not fail on a skill that nothing else links to
```

```gherkin
Scenario: The rename is proven complete  # [Tier B - Governance]
  Given the rename task is finished
  When the rename-completeness check runs
  Then no live file contains epic-lifecycle, epic-designer or epic-implementation
  And files under .devtool/ are not examined
  And historical entries in CHANGELOG.md are not examined
```

```gherkin
Scenario: A reintroduced old name fails the build  # [Tier B - Governance]
  Given a live skill file edited to mention epic-implementation
  When scripts/verify.sh runs
  Then the rename-completeness check fails and names the file
```

## Test & Verification Checklist

**TDD adaptation**: shell and Python tooling with no unit-test harness in this repository. RED/GREEN
is performed by injecting the defect each check targets.

- [ ] **RED (step 8)**: run against a tree where the reviewer prompt is still unreferenced; confirm
      failure naming that exact file.
- [ ] **RED (step 8, exemption)**: confirm no `SKILL.md` is ever reported, including skills nothing
      links to.
- [ ] **RED (step 9)**: reintroduce an old skill name into a live file; confirm failure naming it.
- [ ] **RED (step 9, scoping)**: confirm files under `.devtool/` and CHANGELOG history do **not**
      trigger it.
- [ ] **GREEN**: with Tasks 2 and 6 landed, both steps pass.
- [ ] Confirm `verify.sh` still exits non-zero overall when any single step fails.
- [ ] **Tier A/B**: `verify.sh` passes in full.

## Definition of Done

- `verify.sh` has steps 8 and 9, matching the file's existing style.
- Each check has been demonstrated to fail on the defect it targets, and the demonstration is
  recorded in the task's completion notes.
- The `SKILL.md` exemption and the `.devtool/`/CHANGELOG scoping both verified.
- `scripts/verify.sh` passes in full. Clean git status.

## Dependencies & Blockers

- Blocked by [Task 2](task_2_rename_epic_skills_to_dev.md) — step 9 cannot pass before the rename.
- Step 8 turns green only once [Task 6](task_6_doc_quality_check_skill.md) relocates the orphan.

## References & Rollback

- Source spec §1.1, §7. `scripts/check_source_fidelity.py` as the precedent.
- **Rollback**: remove the two steps. The kit loses two guards but nothing breaks.

---

## Completion Record — proofs run

A check that has never failed is unproven. Both were demonstrated against trees where the defect
exists.

**Step 8 — orphan check, historical proof.** The shipped step-8 logic was extracted from
`scripts/verify.sh` and run against the tree at `3b77671` (release 1.1.1). It failed, naming
`skills/brainstorming/spec-document-reviewer-prompt.md` — the orphan this check was built for.

A first attempt used `c385f0a` as the baseline and the check **passed**, which the harness reported
as a failure of the proof rather than a success. It was right to: by that commit this epic's own
spec already referenced the file, so it was no longer an orphan. The baseline was wrong, not the
check. Worth keeping in mind — "the check passed" and "there was nothing to find" look identical.

**Step 8 — seven further orphans found, and fixed.** The same run surfaced a recurring defect, not a
one-off:

| File | Resolution |
|---|---|
| `writing-plans/plan-document-reviewer-prompt.md` | Referenced from `writing-plans/SKILL.md` — the same defect as the file this epic set out to fix |
| `systematic-debugging/test-pressure-{1,2,3}.md` | Referenced from a new *Verifying This Skill* section |
| `systematic-debugging/test-academic.md` | Referenced from the same section |
| `systematic-debugging/CREATION-LOG.md` | Referenced from the same section |
| `dev-implementation/resources/scripts/test_bootstrap_worktree_validation.sh` | Referenced from the bootstrap step it validates |

These edits touch two skills outside this epic's stated scope. They are the minimum needed to ship a
check that passes, and each is a single accurate reference to a file that was always meant to be
reachable.

**Step 8 — scope narrowed twice during proving.** The first version fired on every `SKILL.md`; the
second on binary assets, `LICENSE` files and the `.github/` directory a vendored skill carries. The
rule it settled on: *a skill's own content must be reachable from the skill*. Assets, legal files and
dotfile directories are not that content.

**Step 9 — rename check.** Reintroducing `epic-implementation` into a live file failed the build and
named the file and line; removing it restored `PASS`. The check also had to exclude `scripts/verify.sh`
itself, whose grep pattern necessarily contains the names it looks for.
