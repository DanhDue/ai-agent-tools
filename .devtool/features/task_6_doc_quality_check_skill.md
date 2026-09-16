---
id: "task_6_doc_quality_check_skill"
status: "done"
priority: "high"
assignee: null
epic: "document_lifecycle_suite"
dueDate: null
created: "2026-09-17T09:00:00Z"
modified: "2026-09-16T18:50:23Z"
completedAt: "2026-09-16T18:50:23Z"
labels: ["skill", "quality-gate", "governance"]
order: "a6"
---

# Task 6: Add the `doc_quality_check` Skill

Epic: [document_lifecycle_suite](../epic/document_lifecycle_suite/document_lifecycle_suite.en.md)

## Requirement Analysis

> [!NOTE]
> **Approach changed during execution.** This task originally added a `Kind` branch inside
> `quality_check`. It now creates a **standalone `doc_quality_check` skill** and leaves
> `quality_check` untouched. Rationale in Design Rationale below; the design spec and HLD were
> synced in the same run.

Create `skills/doc_quality_check/` as the quality gate for documentation work. It runs four checks,
in order:

0. **Refusal rule.** If the change touches any file that ships in the build, abort and name the
   offending paths. Nothing else runs.
1. **Mechanical.** Placeholders in prose, relative links that do not resolve, anchors with no
   matching heading, unbalanced code fences. Code spans and fenced blocks are stripped first, so a
   document that documents these checks does not fail them.
2. **Diátaxis type conformance.** Does the document stay inside its declared type? A missing type
   declaration is itself a finding.
3. **Content audit.** A subagent checks internal contradictions, ambiguity, **unsupported claims**,
   and whether the declared audience could actually perform the `Acceptance` criterion.

Checks 0 and 1 are executable: `resources/scripts/check_document.py`. Prose instructions to "verify
every link resolves" are exactly what gets skipped under load.

`rules/CRITICAL_RULES.md` is amended so the mandated gate depends on the kind of work.

## Relevant Files & Context Pointers

- `skills/doc_quality_check/SKILL.md` — to create
- `skills/doc_quality_check/resources/scripts/check_document.py` — checks 0 and 1
- `skills/doc_quality_check/references/document-reviewer-prompt.md` — relocated from
  `skills/brainstorming/spec-document-reviewer-prompt.md`, where nothing referenced it
- `rules/CRITICAL_RULES.md` — one amendment: the gate depends on the kind of work
- `skills/quality_check/SKILL.md` — **must not be modified**
- `scripts/verify.sh` step 3 — the fence/code-span stripping precedent

## Design Rationale

**Why a separate skill rather than a branch inside `quality_check`:**

1. **Decoupling.** The two gates share no tier, no audit and no tooling. Neither invokes the other.
   Routing lives in `doc-lifecycle` and in `CRITICAL_RULES.md` — where routing belongs — so the two
   skills never have to know about each other and can be maintained independently.
2. **Progressive disclosure.** Both runtimes load skills lazily; this repository's `CLAUDE.md` says
   so explicitly. `quality_check` is 512 lines of Flutter, Gradle and Xcode matrices. Loading them
   to verify a runbook is pure waste.
3. **Regression risk.** `quality_check` gates every merge in every project and changed 57 lines in
   1.1.1. Not touching it puts the regression risk for that file at exactly zero.

**Why `CRITICAL_RULES.md` is amended after all.** The design spec set "do not edit it" as a goal, but
the spec's own §1 identified the problem that the mandate to run `quality_check` after *every*
workflow is unsatisfiable for a Markdown deliverable — "an instruction that cannot be obeyed teaches
the agent that rules are negotiable". Those two positions were in tension. Amending the rule resolves
the problem the spec raised; leaving it merely avoided the file.

**Why check 0 is mechanical.** The document path skips the 3-tier suite, the four audits and the
native build gate; the development path does not. That makes mislabelling code as documentation a
cheap, legitimate-looking shortcut — an incentive misalignment, not a comprehension failure. Writing
the rule more emphatically cannot fix an incentive. A file-extension test can.

Applicable kit skills: `writing-skills`, `d3nexus:dispatching-parallel-agents`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: new `skills/doc_quality_check/`; one block in `rules/CRITICAL_RULES.md`.
- **Downstream callers**: `doc-lifecycle` Gate 2 and `doc-implementation` Phase 4 name this skill.
  `CRITICAL_RULES.md` loads into every session on every project — the highest-reach file touched.
- **Cross-platform bridges**: none.
- **Coverage threshold**: not applicable; checks 0 and 1 are proven by defect fixtures.
- **Regression risk**: near zero for `quality_check`, which is not modified. The real risk is the
  rule edit, mitigated by keeping it to one block that adds a case rather than changing one.

## BDD SCENARIOS

```gherkin
Scenario: The document path is refused for code work  # [Tier C - Integration]
  Given a documentation work item
  And its diff modifies a file that ships in the build
  When doc_quality_check runs
  Then check 0 aborts before any other check runs
  And the abort message names the offending files
  And it states that the work belongs in dev-lifecycle
```

```gherkin
Scenario: The placeholder scan ignores code spans  # [Tier A - Unit]
  Given a document that documents the placeholder check itself
  And the words TBD and TODO appear only inside code spans and fenced blocks
  When check 1 runs
  Then the document passes
```

```gherkin
Scenario Outline: Mechanical failures  # [Tier A - Unit]
  Given a document containing <defect>
  When check 1 runs
  Then it fails and names the offending line

  Examples:
    | defect                                      |
    | the literal text TBD in prose               |
    | a relative link to a file that is not there |
    | a ToC anchor with no matching heading       |
    | an unbalanced mermaid fence                 |
```

```gherkin
Scenario: A missing type declaration is a finding  # [Tier A - Unit]
  Given a document whose Meta Data declares no Diátaxis mode
  When check 2 runs
  Then the absence is reported as a finding
  And it is not treated as not applicable
```

```gherkin
Scenario: The content audit checks the Acceptance criterion  # [Tier C - Integration]
  Given a document whose Acceptance criterion is a named reader task
  When check 3 runs
  Then it reports whether the document actually enables that task
  And it flags claims made without support
```

```gherkin
Scenario: quality_check is not modified  # [Tier B - Governance]
  Given this task is complete
  When the diff for skills/quality_check/SKILL.md is taken
  Then it is empty
```

```gherkin
Scenario: The rule names both gates  # [Tier B - Governance]
  Given rules/CRITICAL_RULES.md after this task
  When its quality-gate section is read
  Then it names quality_check for code and doc_quality_check for prose
  And it states that the two share no checks
```

## Test & Verification Checklist

**TDD adaptation**: the deliverable is a skill plus a script. RED/GREEN applies to the script,
exercised against deliberately defective fixtures held outside the repository.

- [ ] **RED**: one fixture per mechanical defect; confirm each fails with the right message.
- [ ] **RED**: a fixture declaring documentation while touching a shipped file; confirm check 0 aborts.
- [ ] **RED, inverted**: a document that documents the checks; confirm it **passes** — a false
      positive here would make the gate unusable on this kit's own documentation.
- [ ] **GREEN**: run checks 0 and 1 over the epic's own skills; confirm clean.
- [ ] Confirm `git diff` for `skills/quality_check/SKILL.md` is empty.
- [ ] Confirm the reviewer prompt no longer exists under `skills/brainstorming/` and is referenced
      from its new home, so [Task 9](task_9_verify_sh_orphan_and_rename_checks.md)'s orphan check passes.
- [ ] Repoint `doc-lifecycle` and `doc-implementation` Gate 2 references; confirm no doc skill still
      names `quality_check` as its gate.
- [ ] **Tier A/B**: `scripts/verify.sh` passes in full.

## Definition of Done

- `skills/doc_quality_check/` exists with the four checks, the executable script and the relocated
  reviewer prompt.
- Every mechanical check has a fixture proving it can fail, and one proving it does not false-positive.
- `skills/quality_check/SKILL.md` is unmodified.
- `rules/CRITICAL_RULES.md` names both gates and says they share no checks.
- `scripts/verify.sh` passes in full. Clean git status.

## Dependencies & Blockers

- Blocked by [Task 4](task_4_doc_designer_skill.md) — needs the Meta Data contract.
- Blocks [Task 9](task_9_verify_sh_orphan_and_rename_checks.md)'s orphan check turning green.

## References & Rollback

- Source spec §4.4, §6.1. `CLAUDE.md` on progressive disclosure. `verify.sh` step 3 precedent.
- **Rollback**: delete `skills/doc_quality_check/` and revert the rule block. `quality_check` is
  untouched, so the development gate cannot be affected either way.
