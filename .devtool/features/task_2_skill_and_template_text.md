---
id: "task_2_skill_and_template_text"
status: "done"
priority: "high"
assignee: null
epic: "lifecycle-followups"
dueDate: null
created: "2026-10-15T15:57:47Z"
modified: "2026-10-15T16:21:11Z"
completedAt: "2026-10-15T16:21:11Z"
labels: ["skills", "documentation"]
order: "a2"
---

# Task 2: Skill and template text

Epic: [lifecycle-followups](../epic/lifecycle_followups/lifecycle_followups.en.md)

## Requirement Analysis

Spec items B2, B5, B6, H1, H2, H3, H4a, H4b and H5: the rules the receiving agent needs, stated in
dev-designer, dev-implementation, dev-lifecycle and the handoff template, and locked by the lifecycle
contract test with one phrase per scenario, each tagged with its identifier.

### Exact changes

Every current text below occurs exactly once on `main`. Apply the contract-test changes (the three
`scripts/test_lifecycle_document_contract.py` entries) first and see the test fail; then the rest.
Applied to a copy of `main`, they leave the contract test at `checked 12 lifecycle document contract
surfaces` and `check_document.py` at 0 findings.

1. `skills/dev-designer/SKILL.md` (B2) — replace the current text:

```text
`tests/integration/` (Python)
```

with:

```text
`tests/integration/` and `tests/e2e/` (Python)
```

2. `skills/dev-implementation/SKILL.md` (B5) — replace the current text:

```text
and no test references a removed scenario.
```

with:

```text
and no test references a removed scenario. `--roots` and `--ids` take space- or comma-separated values, so the HLD's roots line and a task's `Covers:` line can be pasted as written.
```

3. `skills/dev-lifecycle/SKILL.md` (B6) — replace the current text:

```text
a fresh epic quality run is required before landing
```

with:

```text
a fresh traceability check and epic quality run are required before landing
```

4. `skills/dev-implementation/SKILL.md` (H1) — replace the current text:

```text

git branch -r --list '*/epic/<epic_slug>'
```

with:

```text

for remote in $(git remote); do git ls-remote --heads "$remote" "epic/<epic_slug>"; done
```

5. `skills/dev-implementation/SKILL.md` (H1) — replace the current text:

```text
`git branch -r` reveals an epic branch pushed from another clone.
```

with:

```text
`git ls-remote` asks each remote directly, so an epic branch pushed from another clone shows before any fetch; if a remote cannot be reached, say so in the announcement and fall back to `git branch -r --list '*/epic/<epic_slug>'`.
```

6. `skills/dev-implementation/SKILL.md` (H2) — replace the current text:

```text
if the overview Status is `Packaged` (a packaged epic starting fresh, row 3)
```

with:

```text
if the overview Status begins with `Packaged` (a packaged epic starting fresh, row 3)
```

7. `skills/dev-implementation/SKILL.md` (H2) — replace the current text:

```text
5. If the overview Status is `Packaged`, run
```

with:

```text
5. If the overview Status begins with `Packaged`, run
```

8. `skills/dev-lifecycle/SKILL.md` (H2) — replace the current text:

```text
   Two matching lines are required; with fewer, set the Status line by hand in both variants. Task
```

with:

```text
   Two matching lines are required; with fewer, set the Status line by hand in both variants. If the
   Status read `Queued (backlog) — behind <epic>` before packaging, run the script with
   `"Packaged (queued behind <epic>)"` instead and copy that line into Open Notes; the `grep` still
   matches. Task
```

9. `skills/dev-lifecycle/SKILL.md` (H2) — replace the current text:

```text
**Continue** → invoke `dev-implementation`. **Package** → run the packaging procedure below, then
```

with:

```text
When the overview Status says the epic is queued behind another epic, say so in the question.

**Continue** → invoke `dev-implementation`. **Package** → run the packaging procedure below, then
```

10. `skills/dev-lifecycle/references/handoff-template.md` (H3) — replace the current text:

```text
- **Design commit**: `<sha>` — `HEAD` before the packaging commit
```

with:

```text
- **Design commit**: `<sha>` — `HEAD` before the packaging commit, or `uncommitted` when `auto_commit` is false
```

11. `skills/dev-lifecycle/references/handoff-template.md` (H3) — replace the current text:

```text
- If `git log <sha>..HEAD -- .devtool/epic/<epic_dir>` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale.
```

with:

```text
- Unless the design commit is `uncommitted`: if `git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
```

12. `skills/dev-implementation/SKILL.md` (H4a) — replace the current text:

```text
so the interrupted task's uncommitted work stays out of that commit.
```

with:

```text
so the interrupted task's uncommitted work stays out of that commit. The interrupted task's own status fields may ride along in that commit; that is expected.
```

13. `skills/dev-implementation/SKILL.md` (H4b) — replace the current text:

```text
6. Enter Phase 2 at the interrupted task, or at the first remaining task.
```

with:

```text
6. Enter Phase 2 at the interrupted task — a task at `review` re-enters at Phase 2 step 2 and is reviewed on its existing changes; a task at `in-progress` resumes implementation with the changes kept at Gate 3 (resume) — or at the first remaining task.
```

14. `skills/dev-lifecycle/SKILL.md` (H5) — replace the current text:

```text
   and fill every placeholder. The first column
```

with:

```text
   and fill every placeholder; `<N>` is the task count the preflight printed. The first column
```

15. `scripts/test_lifecycle_document_contract.py` (CT) — replace the current text:

```text
        "Handoff Choice",
    ),
    "skills/writing-plans/SKILL.md": (
```

with:

```text
        "Handoff Choice",
        "`tests/integration/` and `tests/e2e/` (Python)",  # LF-HP-03
    ),
    "skills/writing-plans/SKILL.md": (
```

16. `scripts/test_lifecycle_document_contract.py` (CT) — replace the current text:

```text
        "handoff.md",
    ),
```

with:

```text
        "handoff.md",
        "space- or comma-separated values",  # LF-HP-04
        "re-enters at Phase 2 step 2",  # LF-ST-04
        "may ride along in that commit",  # LF-ST-06
    ),
```

17. `scripts/test_lifecycle_document_contract.py` (CT) — replace the current text:

```text
        "Packaged",
    ),
```

with:

```text
        "Packaged",
        "a fresh traceability check and epic quality run",  # LF-ST-05
        "`<N>` is the task count the preflight printed",  # LF-HP-05
    ),
    "skills/dev-lifecycle/references/handoff-template.md": (
        "or `uncommitted` when `auto_commit` is false",  # LF-FR-04
    ),
```

## Relevant Files & Context Pointers

- `skills/dev-designer/SKILL.md` — Integration Test Roots bullet
- `skills/dev-implementation/SKILL.md` — Entry-Point Detection, Resume Procedure, Phase 1 step 4, Phase 4
- `skills/dev-lifecycle/SKILL.md` — Handoff Choice, packaging steps 2 and 4, Gate 4 condition 4
- `skills/dev-lifecycle/references/handoff-template.md` — Status and staleness rule
- `scripts/test_lifecycle_document_contract.py`

## Design Rationale

- Wording follows the source spec §5 verbatim, so the spec stays the authority.
- Contract phrases carry `# LF-...` comments: that is how a text-only rule gets an automated test that
  names its scenario.
- Applicable skills: `writing-skills` (edits to existing skills), `verification-before-completion`.
  Behaviour tests with fresh subagents, before and after, for: a remote-only epic branch, a task at
  `review`, and packaging a queued epic.

## Impact Analysis & Blast Radius

- **Target files**: the four skill files above; every project with the plugin installed reads them.
- **Downstream**: Task 3's tests read the new `ls-remote` line, the packaging `grep` and the template's
  staleness command from this text.
- **Risk**: a reworded phrase breaks the contract test; that is the intended guard.

## BDD Scenarios & Acceptance Criteria

### BDD SCENARIOS

Covers: LF-HP-03, LF-HP-04, LF-HP-05, LF-ST-04, LF-ST-05, LF-ST-06, LF-FR-04

```gherkin
Feature: lifecycle follow-ups

  Scenario: [LF-HP-03] [Tier C - Integration] Python's default integration roots include tests/e2e
    Given dev-designer's Integration Test Roots defaults
    When an agent designs a Python epic
    Then the defaults name "tests/integration/" and "tests/e2e/"

  Scenario: [LF-HP-04] [Tier C - Integration] The value separators of --roots and --ids are documented
    Given dev-implementation's Phase 4 traceability check
    When an agent copies the HLD's roots line or a task's Covers line
    Then the skill says both options take space- or comma-separated values

  Scenario: [LF-HP-05] [Tier C - Integration] The template's task-count placeholder is explained
    Given the packaging procedure's step 2
    When the agent fills the handoff template
    Then the skill text says "<N>" is the task count the preflight printed

  Scenario: [LF-ST-04] [Tier C - Integration] A task at review resumes its review, not its implementation
    Given an interrupted epic whose task_2 is at "review"
    When the Resume Procedure enters Phase 2
    Then it re-enters at Phase 2 step 2 and reviews the existing changes

  Scenario: [LF-ST-05] [Tier C - Integration] Gate 4 names the traceability check in its re-run rule
    Given a Gate 4 verdict made stale by a later commit
    When dev-lifecycle's candidate-immutability condition is read
    Then it requires a fresh traceability check and epic quality run

  Scenario: [LF-ST-06] [Tier C - Integration] The retrofit commit may carry the interrupted task's status fields
    Given a resumed epic that needs the BDD identifier retrofit
    And an interrupted task whose file holds an uncommitted "in-progress" status
    When the retrofit is committed by path
    Then the skill text states that the task's status fields may ride along in that commit

  Scenario: [LF-FR-04] [Tier C - Integration] An uncommitted design records "uncommitted" and skips the check
    Given auto_commit is false when the epic is packaged
    When the receiver reads handoff.md
    Then the design commit reads "uncommitted"
    And the template tells it to skip the staleness check
```

## Test & Verification Checklist

- [ ] **RED**: apply only the contract-test entries; `python3 scripts/test_lifecycle_document_contract.py`
  exits 1 listing the missing phrases.
- [ ] **GREEN**: apply the text changes; it prints `checked 12 lifecycle document contract surfaces`.
- [ ] **REFACTOR**: `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-lifecycle/SKILL.md skills/dev-designer/SKILL.md skills/dev-implementation/SKILL.md`
  and `--require-toc skills/dev-lifecycle/references/handoff-template.md` report 0 findings.
- [ ] **Tier C**: `python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py tests --scenarios .devtool/epic/lifecycle_followups/bdd_scenarios.en.md --roots scripts/ --ids LF-HP-03 LF-HP-04 LF-HP-05 LF-ST-04 LF-ST-05 LF-ST-06 LF-FR-04`
  exits 0, and `scripts/verify.sh` passes.

## Definition of Done

All seven identifiers are covered by tagged contract phrases, the per-task traceability check exits 0,
lint and `scripts/verify.sh` pass, the before/after behaviour tests show the new rules applied, and the
task lands as one commit `[LIFECYCLE_FOLLOWUPS] Skill and template text` with no trailer.

## Dependencies & Blockers

- None.

## References & Rollback

- Spec: `.devtool/epic/lifecycle_followups/2026-10-15-lifecycle-followups-design.en.md` §5
- Rollback: revert this task's commit.
