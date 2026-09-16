---
id: "task_6_quality_check_kind_branch"
status: "todo"
priority: "high"
assignee: null
epic: "document_lifecycle_suite"
dueDate: null
created: "2026-09-17T09:00:00Z"
modified: "2026-09-17T09:00:00Z"
completedAt: null
labels: ["skill", "quality-gate", "governance"]
order: "a6"
---

# Task 6: Branch `quality_check` on `Kind`

Epic: [document_lifecycle_suite](../epic/document_lifecycle_suite/document_lifecycle_suite.en.md)

## Requirement Analysis

Add a **single decision at the entry point** of `skills/quality_check/SKILL.md`, above every existing
tier table. `Kind: development` — the default when the field is absent — runs today's flow entirely
untouched. `Kind: document` runs four checks:

1. **Mechanical.** No `TBD`/`TODO`/placeholder text; every internal link resolves; ToC anchors match
   their headings; mermaid blocks parse; fenced code samples are syntactically valid. The first three
   are already stated as release requirements in `CLAUDE.md` — reuse that wording rather than
   inventing a second version. **The placeholder scan must skip code spans and fenced blocks**, or it
   fires on any document that documents the check. `verify.sh` step 3 already strips fences and code
   spans before checking links; follow that precedent.
2. **Diátaxis conformance.** Does the document stay inside its declared mode? Mode-mixing is a finding.
3. **Content audit (subagent).** Generalize `skills/brainstorming/spec-document-reviewer-prompt.md`
   from "spec reviewer" to "document reviewer" and relocate it to
   `skills/quality_check/references/document-reviewer-prompt.md`. Add two checks to its existing
   table: **unsupported claims**, and **whether the `Acceptance` criterion is actually met**.
4. **Refusal rule.** If the diff touches any file that ships in the build, **abort** with a message
   naming the offending files: this is development work and belongs in `dev-lifecycle`.

**Why this lives inside `quality_check` rather than a fourth skill**: it leaves
`rules/CRITICAL_RULES.md` untouched. That rule loads into every session on every project, and the
fewer edits it takes the better. One door, two paths behind it.

## Relevant Files & Context Pointers

- `skills/quality_check/SKILL.md` — 512 lines; add the entry branch above the tier tables
- `skills/brainstorming/spec-document-reviewer-prompt.md` — the orphan to relocate and generalize
- `skills/quality_check/references/document-reviewer-prompt.md` — its new home
- `CLAUDE.md` — the mechanical-check wording to reuse
- `scripts/verify.sh` step 3 — the fence/code-span stripping precedent
- `rules/CRITICAL_RULES.md` — **must not be edited**

## Design Rationale

**Check 4 exists because of an incentive misalignment, not a comprehension failure.** The document
path skips tests, the four audits, and — since 1.1.1 — a native binary build. The development path
does not. That hands the agent a legitimate-looking lazy path: call the work "documentation" and the
expensive gate disappears. Writing the rule more clearly cannot fix an incentive, so the mitigation is
mechanical and independent of the agent's judgment: **if the diff touches any file that ships in the
build, it is development work**, regardless of how much prose the task involved.

The user choosing the lifecycle by hand is a second, independent layer of the same defence.

Applicable kit skills: `writing-skills`, `d3nexus:dispatching-parallel-agents` (the content audit is a
subagent dispatch).

## Impact Analysis & Blast Radius

- **Target files & symbols**: `quality_check` entry section; the relocated reviewer prompt.
- **Downstream callers**: `rules/CRITICAL_RULES.md` mandates `quality_check` after every workflow —
  unchanged, which is the point. `doc-lifecycle` Gate 2 and `dev-lifecycle` Gate 4 both enter here.
- **Cross-platform bridges**: none.
- **Coverage threshold**: not applicable. The refusal rule is the highest-risk behaviour and is
  exercised explicitly below.
- **Regression risk**: highest in this epic — `quality_check` gates every merge in every project. The
  `Kind: development` path must be byte-for-byte unchanged in behaviour.

## BDD SCENARIOS

```gherkin
Scenario: The document path is refused for code work  # [Tier C - Integration]
  Given a work item declared Kind document
  And its diff modifies a file that ships in the build
  When quality_check runs
  Then it aborts before running any document check
  And the abort message names the offending files
  And it states that the work belongs in dev-lifecycle
```

```gherkin
Scenario: Kind is absent  # [Tier A - Unit]
  Given a work item whose Meta Data declares no Kind
  When quality_check runs
  Then it defaults to Kind development
  And the full existing 3-tier suite runs unchanged
```

```gherkin
Scenario: The placeholder scan ignores code spans  # [Tier A - Unit]
  Given a document that documents the placeholder check itself
  And the words TBD and TODO appear only inside code spans and fenced blocks
  When the mechanical check runs
  Then the document passes
  And the occurrences inside code spans are not reported
```

```gherkin
Scenario Outline: Mechanical failures  # [Tier A - Unit]
  Given a document containing <defect>
  When the mechanical check runs
  Then it fails and names the offending line

  Examples:
    | defect                                      |
    | the literal text TBD in prose               |
    | a relative link to a file that is not there |
    | a ToC anchor with no matching heading       |
    | an unbalanced mermaid fence                 |
```

```gherkin
Scenario: Mode mixing is reported  # [Tier A - Unit]
  Given a document that declares Diátaxis mode reference
  And it contains step-by-step tutorial narration
  When the conformance check runs
  Then mode mixing is reported as a finding
```

```gherkin
Scenario: The content audit checks the Acceptance criterion  # [Tier C - Integration]
  Given a document whose Acceptance criterion is a named reader task
  When the content-audit subagent runs
  Then it reports whether the document actually enables that task
  And it flags claims made without support
```

## Test & Verification Checklist

**TDD adaptation**: the deliverable is skill text plus a prompt template. RED/GREEN applies to the
checks themselves, exercised against deliberately defective fixtures.

- [ ] **RED**: build one fixture per mechanical defect in the scenario outline; confirm each fails.
- [ ] **RED**: build a fixture whose diff touches a shipped file while declaring `Kind: document`;
      confirm `quality_check` aborts and names the file.
- [ ] **RED**: build a document that documents the placeholder check; confirm it **passes**.
- [ ] **GREEN**: a clean document passes all four checks.
- [ ] **Regression**: run `quality_check` on a `Kind: development` work item and confirm the existing
      3-tier flow is unchanged, including Tier C2.
- [ ] Confirm `rules/CRITICAL_RULES.md` is untouched — `git diff` shows no change to it.
- [ ] Confirm the orphan prompt file no longer exists at its old path and is referenced from its new
      one, so [Task 9](task_9_verify_sh_orphan_and_rename_checks.md)'s orphan check passes.
- [ ] **Tier A/B**: `verify.sh` steps 1–7 pass.

## Definition of Done

- `quality_check` branches on `Kind` at its entry point; the `development` path is behaviourally
  unchanged.
- All four document checks are specified, each with a fixture proving it can fail.
- The reviewer prompt is relocated, generalized and referenced.
- `rules/CRITICAL_RULES.md` unmodified. `scripts/verify.sh` passes in full. Clean git status.

## Dependencies & Blockers

- Blocked by [Task 4](task_4_doc_designer_skill.md) — needs the `Kind` and mode contract.
- Blocks [Task 9](task_9_verify_sh_orphan_and_rename_checks.md)'s orphan check passing.

## References & Rollback

- Source spec §4.4, §6.1. `CLAUDE.md` release requirements. `verify.sh` step 3 precedent.
- **Rollback**: revert the entry branch; `quality_check` returns to development-only. `doc-lifecycle`
  then has no Gate 2 and must be reverted with it.
