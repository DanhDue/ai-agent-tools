---
id: "task_07_english_only_skill_text_and_mirror_isolation"
status: "done"
completedAt: "2026-11-17T13:31:37Z"
priority: "high"
assignee: null
epic: "four_persona_governance"
dueDate: null
created: "2026-11-17T10:00:00Z"
modified: "2026-11-17T13:31:37Z"
labels: ["governance", "english-only", "docs"]
order: "a7"
review_tier: "full"
---

# Task 7: English-Only Dev-Lifecycle Skill Text and Vietnamese Mirror Isolation

Epic: [four_persona_governance](four_persona_governance.en.md)

## Requirement Analysis

Rewrite the dev-lifecycle document contract to English-only (spec §6, [SE-01], [SE-02]).

1. **`rules/CRITICAL_RULES.md`**: add §11 "English SSOT and Vietnamese Mirror Isolation" with the exact rule
   of [SE-01]; extend §8.3 with the chat-language rule (Vietnamese allowed in chat with Role 1.0; every
   persisted dev artefact English-only; Vietnamese only on explicit request).
2. **`skills/dev-lifecycle/SKILL.md`**: Document Contract, Gates table artefacts (`...-design.md`,
   `<epic_dir>.md`, `bdd_scenarios.md`, legacy `.en.md` accepted), Stage 2 three-tier list, packaging step 3
   (`grep` matches `Status` in the resolved English file only), Red Flags; the Sequence keeps a link to
   `lifecycles.en.md` only.
3. **Stage skills**: `dev-brainstorming` (Checklist step 7, After the Design), `dev-designer` (Step 1 items
   1, 2, 4, 6; Protected paths line), `dev-designer/references/task-template-examples.md` (HLD sections,
   Spec Errata), `writing-plans` (Overview, Reviewing a Written Plan, Self-Review, Execution Handoff),
   `finishing-a-development-branch` (Pre-Finish Hook: drop bilingual sync, keep archival and Kanban clean-up),
   `dev-implementation` (Phase 0 context list, Phase 3 Doc Sync), `principal-review` (input list),
   `sync-shared-contracts` (Stage 1 line), and the two review-prompt references
   `dev-implementation/references/external-review-prompt.md` and
   `principal-review/references/principal-review-prompt.md`
   ([SE-14](four_persona_governance.en.md#spec-errata)).
4. **Tests**: create `tests/test_fpg_english_only_text.py` for FPG-AR-04; update contract tests that pin the
   bilingual wording.

## Files

Allowed files:
- `rules/CRITICAL_RULES.md`
- `skills/dev-lifecycle/SKILL.md`
- `skills/dev-lifecycle/references/governance-checklists.md`
- `skills/dev-brainstorming/SKILL.md`
- `skills/dev-designer/SKILL.md`
- `skills/dev-designer/references/task-template-examples.md`
- `skills/writing-plans/SKILL.md`
- `skills/finishing-a-development-branch/SKILL.md`
- `skills/dev-implementation/SKILL.md`
- `skills/principal-review/SKILL.md`
- `skills/sync-shared-contracts/SKILL.md`
- `skills/dev-implementation/references/external-review-prompt.md`
- `skills/principal-review/references/principal-review-prompt.md`
- `scripts/test_lifecycle_signals.py`
- `scripts/test_lifecycle_document_contract.py`
- `scripts/test_verifiable_handoff_text.py`
- `tests/test_tto_docs_and_slimming.py`
- `tests/test_fpg_english_only_text.py` (new)

Read-only context:
- `.devtool/epic/four_persona_governance/four_persona_governance.en.md` — [SE-01], [SE-02]
- `skills/dev-implementation/resources/scripts/_epic_docs.py` (new) — resolution order from Task 4
- `skills/doc-lifecycle/SKILL.md` — must stay bilingual and untouched

## Design Rationale

The English-only rule only saves tokens if no skill tells an agent to write or open the Vietnamese file;
a contract test over the dev skills keeps it that way, while the doc-lifecycle keeps its bilingual
contract. Applicable skills: `d3nexus:writing-skills`, `d3nexus:doc_quality_check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-brainstorming/SKILL.md`: `## Checklist` (L24-L42), `## After the Design` (L185-L244)
  - `skills/writing-plans/SKILL.md`: `## Overview` (L8-L33), `## Reviewing a Written Plan` (L61-L67), `## Self-Review` (L206-L231), `## Execution Handoff` (L232-L251)
  - `skills/finishing-a-development-branch/SKILL.md`: `### Pre-Finish Hook: Bilingual Sync, Epic Archival & Kanban Clean-up` (L121-L165)
  - `skills/dev-implementation/SKILL.md`: `#### Bounded Context Injection & Spec Fidelity` (L51-L75), `### Phase 3 — Doc Sync on Divergence` (L279-L288)
  - `scripts/test_lifecycle_document_contract.py`: `test_mvls_hp_05_lifecycle_docs_and_skill_word_limit` (L214-L229), `test_prv_st_03_diagram_loop_returns_to_package_and_done_repackages` (L368-L386)
  - `tests/test_tto_docs_and_slimming.py`: `test_tto_st_05_pre_finish_bilingual_sync_hook` (L224-L236), `test_tto_st_05_integration` (L251-L253)
  - `tests/test_fpg_english_only_text.py`: new `test_fpg_ar_04_dev_skills_are_english_only_and_isolate_mirrors`
- **Downstream Callers**: every runtime loading these skills; consuming repositories after plugin sync.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: zero `.vi.md` creation or reading instructions in the scanned dev skills.

### BDD SCENARIOS

Covers: FPG-AR-04


```gherkin
Scenario: [FPG-AR-04] [Tier A - Unit] Dev-lifecycle skills are English-only and isolate Vietnamese mirrors
Given the SKILL.md and references of "dev-lifecycle", "dev-brainstorming", "dev-designer", "dev-implementation", "writing-plans", "finishing-a-development-branch", "principal-review" and "cross-model-review"
When the English-only contract test scans them
Then none instructs creating a ".vi.md" file or passing "--require-bilingual" or "--strict-bilingual"
And none instructs reading a ".vi.md" file
And "rules/CRITICAL_RULES.md" contains a section titled "English SSOT and Vietnamese Mirror Isolation"
And the doc-lifecycle skills "doc-brainstorming", "doc-designer" and "doc-implementation" still contain "--require-bilingual"
```

```gherkin
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_english_only_text.py::test_fpg_ar_04_dev_skills_are_english_only_and_isolate_mirrors` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_english_only_text.py tests/test_tto_docs_and_slimming.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 scripts/test_lifecycle_signals.py scripts/test_lifecycle_document_contract.py scripts/test_verifiable_handoff_text.py` | exit 0 | — |
| V4 | GREEN | `python3 skills/doc_quality_check/resources/scripts/check_document.py rules/CRITICAL_RULES.md skills/dev-lifecycle/SKILL.md skills/dev-designer/SKILL.md` | exit 0 | — |
| V5 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/test_lifecycle_signals.py` | exit 0 | — |
| V6 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_fpg_english_only_text.py` | exit 0 | — |
| V7 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/fpg_task_07.xml tests/test_fpg_english_only_text.py` | exit 0; results build/test-results/fpg_task_07.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- New contract: `CRITICAL_RULES.md` §11 title is exactly `## 11. English SSOT and Vietnamese Mirror
  Isolation`; its text states the [SE-01] prohibitions and the two exceptions verbatim.
- New contract: the FPG-AR-04 scan set is the SKILL.md and `references/*.md` of `dev-lifecycle`,
  `dev-brainstorming`, `dev-designer`, `dev-implementation`, `writing-plans`,
  `finishing-a-development-branch`, `principal-review`, `cross-model-review`. In that set, `.vi.md` may
  appear only on a line that also contains `MUST NOT`, `never` or `not SSOT`; `--require-bilingual` and
  `--strict-bilingual` must not appear.
- New contract ([SE-14](four_persona_governance.en.md#spec-errata)): `skills/dev-implementation/references/external-review-prompt.md` and `skills/principal-review/references/principal-review-prompt.md` belong to the
  FPG-AR-04 scan set, and line 3 of each says "ignore `*.vi.md` mirrors", a line with none of `MUST NOT`, `never` or
  `not SSOT`. Reword that one clause in both files to "never read `*.vi.md` mirrors" and change nothing else in them.
  A repository search found no test that pins the old clause; if one appears, retarget that assertion to the new
  clause and never weaken or delete it.
- Source: `skills/doc-brainstorming/SKILL.md`, `skills/doc-designer/SKILL.md` and
  `skills/doc-implementation/SKILL.md` keep `--require-bilingual`; this task does not edit them.
- Source: links from skills to the bilingual kit guides under `docs/` outside the scan set
  (`sync-shared-contracts`, `setup-shared-contracts`, `refresh-session`) stay.
- New contract: new-artefact names are `YYYY-MM-DD-<topic>-design.md`, `<epic_dir>.md`, `bdd_scenarios.md`,
  `docs/superpowers/plans/YYYY-MM-DD-<feature>.md`; legacy `.en.md` is "accepted, not produced".
- The IDE window-title convention (`<Vietnamese Epic Name>`) is not a persisted dev artefact and stays.

## Definition of Done

- FPG-AR-04 passes. (V2, V7)
- Updated contract suites pass. (V2, V3)
- Edited rule and skill documents pass the document checker. (V4)
- Ruff and mypy pass on touched Python. (V5, V6)

## Dependencies & Blockers

Blocked by [Task 6](task_06_four_persona_governance_text.md).

Downstream dependents (blocked by Task 7): `task_08`.

## References & Rollback

- [Epic HLD](four_persona_governance.en.md)
- **Rollback**: Revert the task commit to restore the bilingual document contract text.
