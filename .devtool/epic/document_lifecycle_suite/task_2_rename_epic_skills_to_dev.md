---
id: "task_2_rename_epic_skills_to_dev"
status: "todo"
priority: "high"
assignee: null
epic: "document_lifecycle_suite"
dueDate: null
created: "2026-09-17T09:00:00Z"
modified: "2026-09-17T09:00:00Z"
completedAt: null
labels: ["refactor", "breaking-change", "governance"]
order: "a2"
---

# Task 2: Rename `epic-*` Skills to `dev-*`

Epic: [document_lifecycle_suite](document_lifecycle_suite.en.md)

## Requirement Analysis

"Epic" becomes the umbrella term covering both kinds of work, so the development lifecycle needs a
name that distinguishes it from the document lifecycle:

| Current | New |
|---|---|
| `epic-lifecycle` | `dev-lifecycle` |
| `epic-designer` | `dev-designer` |
| `epic-implementation` | `dev-implementation` |

Unchanged: `finishing-a-development-branch` (shared by both lifecycles) and the directory
`.devtool/epic/` — both kinds of epic live there, distinguished by `Kind:`. **There is no data
migration.**

This task lands early and alone. Every later task edits files it touches, and rebasing a rename
across them is expensive.

**This is a breaking change.** `/d3nexus:epic-lifecycle` stops working, as do per-project
`AGENTS.md` files naming the old skills.

## Relevant Files & Context Pointers

Measured live surface — **19 files**. The source spec estimated 18 and omitted `hooks/` and
`templates/`; this list governs.

- `skills/epic-lifecycle/` → `skills/dev-lifecycle/` (directory rename)
- `skills/epic-designer/` → `skills/dev-designer/` (directory rename)
- `skills/epic-implementation/` → `skills/dev-implementation/` (directory rename, plus 5 scripts
  under `resources/scripts/` whose documented invocation paths change)
- `skills/finishing-a-development-branch/SKILL.md` — **lines 109–112, executable path probe**
- `skills/brainstorming/SKILL.md`, `skills/impact-analysis/SKILL.md`,
  `skills/impact-analysis/references/impact-mechanisms.md`, `skills/lean-mvp-scoping/SKILL.md`,
  `skills/lean-mvp-scoping/templates/mvp-backlog.template.md`, `skills/lean-product-lifecycle/SKILL.md`
- `hooks/session-start`, `rules/CRITICAL_RULES.md`, `README.md`, `templates/AGENTS.md`

**Excluded on purpose**: `.devtool/` (28 further files) and the historical entries in
`CHANGELOG.md`. They record work done under the old names; editing them falsifies the record.

## Design Rationale

Two findings from Check 1 shape this task:

1. **The rename breaks an executable path, not just prose.**
   `skills/finishing-a-development-branch/SKILL.md:109-112` probes for `sync_task_status.py` at a
   hard-coded path under `skills/epic-implementation/`. Left stale, the probe fails its `if` and the
   archival step silently takes a fallback branch. Blind find-and-replace across prose would miss
   the significance of this one; it needs its own verification.
2. **`hooks/session-start` names the skills**, and that hook injects content into every session on
   every project — a stale name there travels further than any SKILL.md.

Use `git mv` for directories so history follows the files.

Applicable kit skills: `d3nexus:impact-analysis` (Check 1 already run, recorded in the HLD),
`d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: three skill directories; the three skill names wherever they appear in
  the 19 live files; `description:` frontmatter of the three renamed skills.
- **Downstream callers**: `finishing-a-development-branch` (runtime path probe);
  `hooks/session-start`; `templates/AGENTS.md` consumed by every new project; `rules/CRITICAL_RULES.md`.
- **Cross-platform bridges**: none.
- **Coverage threshold**: not applicable. Proven by the rename-completeness check in
  [Task 9](task_9_verify_sh_orphan_and_rename_checks.md) and by exercising the archival probe.

## BDD SCENARIOS

```gherkin
Scenario: Activation still matches on the word "epic"  # [Tier A - Unit]
  Given the renamed skill dev-lifecycle
  When its description frontmatter is read
  Then it contains the word "epic"
  And a request phrased as epic-scale work still activates it
```

```gherkin
Scenario: The runtime script path survives the rename  # [Tier C - Integration]
  Given finishing-a-development-branch probes for sync_task_status.py by path
  When the epic-implementation directory is renamed
  Then that probe resolves to the new path
  And the archival step does not fall through to its fallback branch
```

```gherkin
Scenario: Historical records are left alone  # [Tier B - Governance]
  Given files under .devtool/ that name the old skills
  When the rename is complete
  Then those files are unmodified
  And git shows no changes under .devtool/ from this task
```

```gherkin
Scenario: Frontmatter name matches the new directory  # [Tier A - Unit]
  Given each renamed skill directory
  When scripts/verify.sh step 2 runs
  Then the frontmatter name equals the directory name
  And no WARN is emitted for a name/directory mismatch
```

## Test & Verification Checklist

**TDD adaptation**: a pure rename with no new behaviour. The cycle is "prove the old state, change,
prove the new state, prove nothing else moved".

- [ ] **Before**: record `git grep -l` counts for the three old names across live paths.
- [ ] `git mv` the three directories; update the 19 live files.
- [ ] Fix `finishing-a-development-branch/SKILL.md:109-112` and **execute** that probe logic against
      the renamed tree to confirm it takes the primary branch, not the fallback.
- [ ] Update `hooks/session-start`; re-run `scripts/verify.sh` step 6 (hook JSON, both runtimes).
- [ ] Confirm each renamed skill's `description:` still contains "epic".
- [ ] **Tier A**: `verify.sh` steps 1–4 pass, including name/directory agreement.
- [ ] **Tier B**: `verify.sh` steps 5–7 pass; `git status` shows zero changes under `.devtool/`.
- [ ] Add the breaking-change entry to `CHANGELOG.md` for 1.2.0 naming all three renames.

## Definition of Done

- Three directories renamed via `git mv`; all 19 live files updated; zero live occurrences of the
  old names outside `.devtool/` and CHANGELOG history.
- The archival path probe demonstrably resolves post-rename.
- `hooks/session-start` updated and its JSON still valid for both runtimes.
- CHANGELOG marks 1.2.0 breaking. `scripts/verify.sh` passes in full. Clean git status.

## Dependencies & Blockers

- Blocks [Task 9](task_9_verify_sh_orphan_and_rename_checks.md) (its rename check needs this done).
- Blocked by: nothing. Land before Tasks 3–8 to avoid rebasing.

## References & Rollback

- HLD §4.4 Check 1 findings.
- **Rollback**: a single revertible commit. Reverting restores the old names everywhere; no data
  migration to undo because `.devtool/epic/` never changed.
