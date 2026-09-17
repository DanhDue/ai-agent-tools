---
id: "task_9_tier_c_acceptance"
status: "todo"
priority: "high"
assignee: null
epic: "brainstorming_split"
dueDate: null
created: "2026-09-17T09:27:07Z"
modified: "2026-09-17T09:27:07Z"
completedAt: null
labels: ["acceptance", "verification", "release"]
order: "a9"
---

# Task 9: Tier C Acceptance and CHANGELOG

Epic: [brainstorming_split](brainstorming_split.en.md)

## Requirement Analysis

The final integration task. It verifies the whole split behaves as designed rather than that each
file was edited, and it writes the CHANGELOG entry.

Spec §7 lists six verification items; they are this task's acceptance criteria:

1. `scripts/verify.sh` passes on the merged result, run from a **normal checkout** — not only from
   a worktree. A worktree lacks the gitignored `.superpowers/` directory, which is how a
   filesystem-walk bug passed in a worktree and failed on `main` during release 1.2.0.
2. The new orchestrator-routing check passes (Task 7).
3. Step 9's existing `epic-*` check stays exactly as it is.
4. `find skills -maxdepth 1 -type d` count equals `find skills -name SKILL.md` count. Today both
   are 52; after this epic both should be 53, since `doc-brainstorming` is added while
   `brainstorming` is replaced rather than removed. A mismatch is how a stale directory surviving
   `git mv` was caught last release, when it held gitignored `__pycache__` and so was never empty.
5. Both orchestrators' mermaid diagrams match their prose. Four prose/diagram mismatches were
   caught by Gate 2 during 1.2.0; this is the check that caught them.
6. `@doc_quality_check` for the four `docs/` files; `@quality_check` for everything else.

**Release.** The CHANGELOG entry is written under *Unreleased* targeting 1.3.0. Two commits already
on `main` ship with this epic — `0b8a030` (stage-entry imperative) and `8dd7beb` (branch-aware
guidance) — and must appear in the entry. **The user has not authorized a release.** Publishing is
a separate decision outside this epic; this task must not tag, bump a version file, or push.

## Relevant Files & Context Pointers

- `CHANGELOG.md` — a new *Unreleased* entry appended; existing entries untouched
- `scripts/verify.sh` — run in full, from a normal checkout
- `skills/dev-lifecycle/SKILL.md`, `skills/doc-lifecycle/SKILL.md` — the two diagram/prose pairs
- Commits `0b8a030`, `8dd7beb`, `c865728`, `caa085d` — the four already on `main`
- Spec §7, §9

## Design Rationale

**Why acceptance is its own task.** Each preceding task verifies its own file. None of them can
observe the property that matters: that an ambiguous request reaches the right variant, that a
small document still passes Stage 0, and that no orchestrator quietly names the router. Those are
system properties.

**Why the checkout-versus-worktree distinction is called out.** It is the single verification
lesson from the previous release that cost real time: `verify.sh` was green in the worktree and red
on `main`, because a filesystem walk read a gitignored directory that only exists in a normal
checkout.

**Why the skill count is expected to rise to 53, not stay at 52.** `brainstorming` is replaced in
place by the router, `dev-brainstorming` is a rename of the same directory, and
`doc-brainstorming` is genuinely new. One net addition.

Applicable kit skills: `d3nexus:quality_check` (shipped files), `d3nexus:doc_quality_check`
(the four `docs/` files), `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `CHANGELOG.md`; no skill files are edited by this task except to fix
  defects the acceptance run surfaces.
- **Downstream callers**: every consumer of the plugin, once a release is authorized.
- **Cross-platform bridges**: none.
- **Target verification threshold**: all six spec §7 items pass; both gates green.

## BDD SCENARIOS

```gherkin
Scenario: [Tier C - Integration] The full suite passes from a normal checkout
  Given a normal checkout on the merged branch with .superpowers/ present
  When scripts/verify.sh runs in full
  Then all ten steps pass

Scenario: [Tier C - Integration] The skill count rises by exactly one
  Given the merged result
  When skill directories and SKILL.md files are counted
  Then both counts are 53
  And they are equal

Scenario: [Tier C - Integration] An ambiguous request reaches the right variant end to end
  Given a user says only "brainstorm this"
  When the router asks and the user answers "làm tài liệu"
  Then doc-brainstorming runs
  And doc-lifecycle Stage 0 is satisfied by its approved spec

Scenario: [Tier C - Integration] A small document still passes Stage 0
  Given a runbook request whose content is fully known
  When doc-lifecycle runs
  Then Stage 0 executes
  And Gate 1 is the spec approval
  And the spec may be three sentences

Scenario: [Tier C - Integration] Neither orchestrator names the router
  Given both orchestrators on the merged result
  When verify.sh step 10 runs
  Then it passes

Scenario: [Tier C - Integration] Every mermaid diagram matches its prose
  Given both orchestrators and both brainstorming variants
  When each diagram is rendered and compared against the surrounding prose
  Then the stage names, gate counts and exits agree
  And every diagram renders without error

Scenario: [Tier B - Governance] Each gate is run on the right kind of change
  Given the epic's commits
  When the docs-only commit is gated with doc_quality_check
  And the skill commits are gated with quality_check
  Then both report green
  And doc_quality_check does not refuse

Scenario: [Tier A - Unit] The CHANGELOG entry is unreleased and complete
  Given CHANGELOG.md
  When the new entry is read
  Then it is under Unreleased targeting 1.3.0
  And it lists the split, the mandatory Stage 0, the gate renumber and the new verify step
  And it includes the two commits already on main

Scenario: [Tier A - Unit] No release is performed
  Given this task is complete
  When the repository state is inspected
  Then no tag was created
  And no version file was bumped
  And nothing was pushed

Scenario: [Tier A - Unit] Existing CHANGELOG entries are untouched
  Given CHANGELOG.md
  When it is diffed against its state before this task
  Then only an addition appears
  And no prior entry is modified
```

## Test & Verification Checklist

- [ ] **Tier A**: skill directory count equals SKILL.md count, both 53.
- [ ] **Tier B**: `scripts/verify.sh` full run green **from a normal checkout**; step 9 unchanged.
- [ ] **Tier B**: `@quality_check` on the shipped-file commits.
- [ ] **Tier B**: `@doc_quality_check` on the docs-only commit; confirm Check 0 does not refuse.
- [ ] **Tier C**: render every mermaid diagram in both orchestrators and both variants; compare
      each against its surrounding prose.
- [ ] **Tier C**: drive the router end to end for each of the three answers.
- [ ] **Tier C**: drive `doc-lifecycle` end to end on one small real document.
- [ ] **Release**: CHANGELOG entry written as *Unreleased*; no tag, no version bump, no push.

## Definition of Done

- All six spec §7 verification items pass, each with observed output rather than assumption.
- Skill directory and SKILL.md counts both 53 and equal.
- `verify.sh` green in full from a normal checkout; step 9 byte-for-byte unchanged.
- Both quality gates run on the right commits and both green.
- Every mermaid diagram renders and agrees with its prose.
- CHANGELOG entry under *Unreleased* for 1.3.0, naming `0b8a030` and `8dd7beb`.
- **No release performed**: no tag, no version bump, no push.
- Clean `git status`.

## Dependencies & Blockers

Blocked by Tasks [1](task_1_dev_brainstorming_rename.md), [2](task_2_brainstorming_router.md),
[3](task_3_doc_brainstorming_skill.md), [4](task_4_doc_lifecycle_mandatory_stage_0.md),
[5](task_5_dev_lifecycle_retarget.md), [6](task_6_consumer_retarget.md),
[7](task_7_verify_orchestrator_routing_check.md) and [8](task_8_docs_bilingual_update.md).

## References & Rollback

- Spec §7, §9
- HLD §5, release section
- The worktree-versus-checkout bug and the stale-directory bug, both from release 1.2.0

**Rollback**: the CHANGELOG addition reverts cleanly on its own. If acceptance fails, the failing
task's commit is reverted rather than this one — this task's job is to find the failure, not to
absorb it.
