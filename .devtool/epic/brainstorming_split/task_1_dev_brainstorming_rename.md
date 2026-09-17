---
id: "task_1_dev_brainstorming_rename"
status: "done"
priority: "high"
assignee: null
epic: "brainstorming_split"
dueDate: null
created: "2026-09-17T09:27:07Z"
modified: "2026-09-17T09:33:39Z"
completedAt: "2026-09-17T09:33:39Z"
labels: ["refactor", "skills", "rename"]
order: "a1"
---

# Task 1: Rename `brainstorming` to `dev-brainstorming` and Strip the Document Branch

Epic: [brainstorming_split](brainstorming_split.en.md)

## Requirement Analysis

Move the existing skill directory wholesale, then remove the document-side routing that spec §3.1
relocates to the router. The visual companion and its server scripts stay here — 1126 of the
directory's 1354 lines — because mockups, wireframes and layout comparisons are code-side concerns.

Two edits are *caused by* the move rather than chosen, and belong in this task's commit for that
reason:

- **Finding 1 (functional break).** `SKILL.md:228` hard-codes `skills/brainstorming/visual-companion.md`.
  After the move that path is dead, and the instruction fires at exactly the moment the user has
  accepted the companion offer.
- **Finding 2 (comment only).** `scripts/start-server.sh:80` says
  `# SCRIPT_DIR is .agents/skills/brainstorming/scripts — walk up to .agents/`. The logic below it
  is depth-based and survives the move unchanged; only the comment becomes wrong.

Routine exits reduce from four to three. The `doc-designer` exit is removed as a routine exit — the
router owns that decision now — but the spec §3.7 correction exit to `doc-brainstorming` is added,
so the total number of ways out stays four with different meanings.

## Relevant Files & Context Pointers

- `skills/brainstorming/` → `skills/dev-brainstorming/` — the whole directory, 7 files
- `skills/brainstorming/SKILL.md:228` — the dead self-referential path (Finding 1)
- `skills/brainstorming/SKILL.md` — `Routing After Approval`, the process-flow mermaid, the
  four-exit sentence, and the Upstream Escape section
- `skills/brainstorming/scripts/start-server.sh:80` — the stale comment (Finding 2)
- `skills/brainstorming/visual-companion.md` — moves unchanged
- Spec §3.4 (asymmetric escape), §3.7 (correction exit), §4.2 (this task's component)

## Design Rationale

`git mv` on the directory rather than file-by-file, so git records a rename and the history of the
visual companion and its scripts survives intact.

The correction exit is deliberately *not* drawn as a normal edge in the process-flow diagram. It
fires on a discovery, not on a decision, and drawing it as a routine branch would invite agents to
treat "is this actually a document?" as a question to ask at the start — which is the router's job,
not this skill's.

Applicable kit skills: `d3nexus:writing-skills` for the frontmatter and progressive-disclosure
rules; `d3nexus:doc_quality_check` does **not** apply — this changes files that ship in the plugin,
so `@quality_check` is the gate.

## Impact Analysis & Blast Radius

- **Target files & symbols**: the `skills/brainstorming/` directory path; the skill name
  `brainstorming` as it appears in this file's own frontmatter and prose.
- **Downstream callers**: every file in Task 5 and Task 6. This task does not update them — it
  leaves the kit briefly inconsistent, which is why the whole epic merges as one unit (HLD §5).
- **Cross-platform bridges**: none.
- **Target verification threshold**: `verify.sh` steps 1–4 green for the new directory; the
  `name:` frontmatter field must equal `dev-brainstorming` and match its directory.

## BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] The renamed skill declares a matching name
  Given skills/dev-brainstorming/SKILL.md exists
  When verify.sh step 2 compares frontmatter name against directory name
  Then the name field reads "dev-brainstorming"
  And the check passes

Scenario: [Tier A - Unit] The visual companion path resolves after the move
  Given the agent has offered the visual companion and the user accepted
  When the skill instructs it to read the detailed guide
  Then the path names skills/dev-brainstorming/visual-companion.md
  And that file exists

Scenario: [Tier A - Unit] No reference to the old directory path survives in the moved files
  Given the directory has been moved
  When the 7 moved files are searched for the string "skills/brainstorming/"
  Then zero matches are found

Scenario: [Tier A - Unit] The server script still resolves its agent directory
  Given SCRIPT_DIR is skills/dev-brainstorming/scripts
  When start-server.sh walks up three levels
  Then it lands on the same directory it landed on before the rename
  And the comment above that line names the new path

Scenario: [Tier C - Integration] The skill offers three routine exits, not four
  Given a completed and approved design spec
  When the skill reaches Routing After Approval
  Then the routine exits are dev-designer, writing-plans and lean-product-lifecycle
  And doc-designer is not among them

Scenario: [Tier C - Integration] A misroute discovered mid-session can be corrected
  Given the session is in dev-brainstorming
  And nothing the work produces will change a file that ships in the build
  When the skill applies the deliverable test
  Then it stops and hands over to doc-brainstorming
  And it does not present a code-oriented design first

Scenario: [Tier A - Unit] The correction exit is absent from the routine process flow
  Given the process-flow mermaid diagram
  When its edges are enumerated
  Then no solid edge leads to doc-brainstorming

Scenario: [Tier A - Unit] The lean escape keeps its original trigger on this side
  Given the target customer cannot be named as a specific segment
  When the skill reaches checklist step 2
  Then it stops and recommends lean-product-lifecycle

Scenario: [Tier C - Integration] git records a rename rather than a delete and add
  Given the move is committed
  When git show --stat is run on that commit
  Then the moved files appear as renames
  And the visual companion's history is reachable through git log --follow
```

## Test & Verification Checklist

**TDD adaptation**: this is a rename plus prose edits, with no new executable behaviour. The RED
step is therefore a set of assertions that fail before the change and pass after, rather than unit
tests.

- [ ] **RED**: confirm `grep -rn "skills/brainstorming/" skills/brainstorming/` currently returns
      the two known hits (SKILL.md:228, scripts/start-server.sh:80) — these are the assertions that
      must flip.
- [ ] **GREEN**: `git mv skills/brainstorming skills/dev-brainstorming`, then fix both hits and
      strip the `doc-designer` routine exit; add the §3.7 correction exit.
- [ ] **REFACTOR**: re-read the process-flow mermaid against the prose; the exit count in the text
      must match the edges in the diagram.
- [ ] **Tier A**: `scripts/verify.sh` steps 1, 2 and 4 pass; step 3 fails on exactly one link,
      the `CRITICAL_RULES.md` reference to the router that Task 2 restores.
- [ ] **Mermaid**: the process-flow diagram renders via `mermaid-cli`.
- [ ] **Tier C**: invoke `d3nexus:dev-brainstorming` on a throwaway request and confirm it offers
      the companion, resolves the guide path, and terminates in exactly one of its three routine
      exits.

## Definition of Done

- The directory is `skills/dev-brainstorming/` with all 7 files and git-recorded renames.
- `name:` frontmatter equals `dev-brainstorming`; frontmatter has exactly `name` + `description`.
- Zero occurrences of `skills/brainstorming/` inside the moved files.
- Three routine exits; `doc-designer` removed; correction exit present and not drawn as a routine
  edge.
- `verify.sh` steps 1, 2 and 4 green; the process-flow mermaid renders.
- Step 3 reports exactly one broken link — `rules/CRITICAL_RULES.md -> ../skills/brainstorming/SKILL.md`.
  This is expected and is [Task 2](task_2_brainstorming_router.md)'s RED proof that the router is
  load-bearing. Any *other* broken link is a defect in this task.
- Clean `git status` after the commit.

## Dependencies & Blockers

Blocks [Task 2](task_2_brainstorming_router.md) — Task 2 recreates `skills/brainstorming/`, and
running it first would create a directory that this task's `git mv` then swallows.
Also blocks [Task 5](task_5_dev_lifecycle_retarget.md) and
[Task 6](task_6_consumer_retarget.md).

## References & Rollback

- Spec §3.1, §3.4, §3.7, §4.2
- HLD [§4.4 Check 1](brainstorming_split.en.md#44-check-1--shift-left-impact-analysis) — Findings 1 and 2

**Rollback**: `git revert` the commit. The rename reverses as another `git mv`; no generated
artefacts and no state outside git are involved.
