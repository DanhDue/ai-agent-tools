---
id: "task_11_progressive_disclosure_cleanup"
status: "done"
priority: "medium"
assignee: null
epic: "document_lifecycle_suite"
dueDate: null
created: "2026-09-17T14:00:00Z"
modified: "2026-09-16T19:00:41Z"
completedAt: "2026-09-16T19:00:41Z"
labels: ["refactor", "progressive-disclosure", "token-cost"]
order: "a11"
---

# Task 11: Apply Progressive Disclosure to the New Skills

Epic: [document_lifecycle_suite](../epic/document_lifecycle_suite/document_lifecycle_suite.en.md)

## Requirement Analysis

Added after Task 8, from a question raised during review: does inlining the Diátaxis and Nygard
material inflate token cost?

Measurement first, because the premise turned out to be half right:

| | Result |
|---|---|
| New `SKILL.md` bodies | 118–150 lines, all **below** the kit median of 158 |
| Quoted source material | ~12% of those files |
| New `description` lengths | 391–573 chars against a kit mean of **227** |
| Share of the permanent cost | 9.6% of skills, **19%** of total description length |

So the bodies are not the problem — the **descriptions** are, and those are the part that sits in
every session on every project. `doc-lifecycle`'s is the longest of all 52 skills.

`CLAUDE.md` already requires this: *"Keep `SKILL.md` concise… Bulk material belongs in the skill's
`references/`."* The Lean suite complies; these five skills did not.

Two deliverables:

1. **Trim all five descriptions** toward the kit mean, keeping the nouns that drive activation. One
   is also **stale**: `doc-lifecycle` still names `quality_check` as Gate 2, which changed to
   `doc_quality_check` during Task 6.
2. **Move quoted source material to `references/`** in `doc-designer` and `decision-records`.

## Relevant Files & Context Pointers

- `skills/doc-lifecycle/SKILL.md`, `skills/doc-designer/SKILL.md`,
  `skills/doc-implementation/SKILL.md`, `skills/doc_quality_check/SKILL.md`,
  `skills/decision-records/SKILL.md` — descriptions
- `skills/doc-designer/references/diataxis-source.md` — to create
- `skills/decision-records/references/adr-source.md` — to create
- `skills/lean-product-lifecycle/references/` — the precedent to follow
- `CLAUDE.md` — the rule being applied

## Design Rationale

**Move the evidence, never the rule.** A rule in `references/` is a rule the agent may not read —
the exact failure this kit's eval harness exists to measure. The Diátaxis compass decision table is
six lines and is the single most behaviour-changing artefact in `doc-designer`; it stays inline. The
four definitional quotes that justify it do not need to.

| Stays in `SKILL.md` | Moves to `references/` |
|---|---|
| Compass decision table; one-type-per-document rule | The four type definitions, quoted |
| ADR format table; immutability; status transitions | Nygard's quotations |

**On magnitude, stated honestly:** all 52 descriptions total ~11,800 characters, roughly 3k tokens.
Trimming these five saves on the order of 250 tokens per session. Real, permanent, and small. The
stronger reason is consistency with the kit's own stated convention, not the saving.

## Impact Analysis & Blast Radius

- **Target files & symbols**: five `description` fields; two new `references/` files.
- **Downstream callers**: descriptions drive activation in both runtimes — over-trimming breaks
  discovery, which is a worse failure than the cost being fixed.
- **Cross-platform bridges**: none.
- **Coverage threshold**: not applicable. The orphan check in `verify.sh` step 8 proves the new
  `references/` files are actually wired in.

## BDD SCENARIOS

```gherkin
Scenario: Descriptions come down toward the kit mean  # [Tier A - Unit]
  Given the five skills added by this epic
  When their description lengths are measured
  Then none exceeds the kit maximum it previously set
  And each still names the nouns that drive its activation
```

```gherkin
Scenario: The stale gate reference is corrected  # [Tier A - Unit]
  Given doc-lifecycle's description
  When it names the skill that enforces Gate 2
  Then it names doc_quality_check
  And it does not name quality_check
```

```gherkin
Scenario: Rules stay inline, evidence moves out  # [Tier A - Unit]
  Given doc-designer after this task
  When its SKILL.md is read
  Then the Diátaxis compass decision table is still present in full
  And the four definitional quotations are in references/ instead
```

```gherkin
Scenario: The moved files are wired in  # [Tier B - Governance]
  Given the new references/ files
  When scripts/verify.sh step 8 runs
  Then neither is reported as an orphan
```

```gherkin
Scenario: Fidelity guards still cover the moved material  # [Tier B - Governance]
  Given the quotations now live under references/
  When scripts/verify.sh step 7 runs
  Then those files are still scanned by the Diátaxis and Nygard checks
```

## Test & Verification Checklist

**TDD adaptation**: documentation refactor. Verification is measurement plus the existing guards.

- [ ] Measure all five descriptions before and after; record both.
- [ ] Confirm `doc-lifecycle`'s description names `doc_quality_check`, not `quality_check`.
- [ ] Confirm each description still contains its activation-critical nouns.
- [ ] Confirm the compass decision table and the ADR rule tables remain in their `SKILL.md`.
- [ ] **Tier B**: `verify.sh` step 8 reports no orphan — the new `references/` files are referenced.
- [ ] **Tier B**: `verify.sh` step 7 still scans the moved quotations.
- [ ] `scripts/verify.sh` passes in full.

## Definition of Done

- Five descriptions trimmed toward the kit mean, with the stale gate reference fixed.
- Quoted source material lives in `references/`; every behaviour-changing rule remains inline.
- Both new `references/` files are referenced from their skill.
- `scripts/verify.sh` passes in full. Clean git status.

## Dependencies & Blockers

- Blocked by Tasks 3–8 — it refines their output.
- Blocks [Task 10](task_10_tier_c_acceptance.md): the README skill count and the ablation should
  describe the skills in their final shape.

## References & Rollback

- `CLAUDE.md` on progressive disclosure; `skills/lean-product-lifecycle/references/` as precedent.
- **Rollback**: inline the `references/` content again and restore the longer descriptions. No
  behaviour depends on the split.
