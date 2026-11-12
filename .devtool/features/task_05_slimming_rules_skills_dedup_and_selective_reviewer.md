---
id: "task_05_slimming_rules_skills_dedup_and_selective_reviewer"
status: "todo"
priority: "high"
assignee: null
epic: "token_throttling_optimization"
dueDate: null
created: "2026-11-13T02:36:00Z"
modified: "2026-11-13T02:36:00Z"
completedAt: null
labels: ["docs", "slimming", "skills", "token-optimization"]
order: "a5"
---

# Task 5: Rules and Skills Slimming, Deduplication, Selective Reviewer, and Pre-Finish Sync

Epic: [token_throttling_optimization](../epic/token_throttling_optimization/token_throttling_optimization.en.md)

## Requirement Analysis

Slim always-on instructions and lifecycle skills (`Rule 1`, `Rule 3`, `Rule 5`), replace scattered legacy `Gemini Flash 3.8` / `gemini-3.8-flash` defaults with config-driven `.devtool/review_config.json` resolution (`gemini-4-hydrogen-xhigh`, `--effort xhigh`), deduplicate overlapping reference files across `dev-implementation/`, `principal-review/`, and `cross-model-review/`, enforce selective `task-reviewer` gating, and add the Stage 4 Pre-Finish bilingual sync hook:
1. **Always-On Rule & Observer Slimming (`CRITICAL_RULES.md`, `task-observer/SKILL.md`)**:
   - Compress `rules/CRITICAL_RULES.md` to `<= 8192` bytes while preserving all mandatory headings, markers (`## 8. Mandatory Two-Tier Project Memory & Tri-Role Persona Discipline`, `BOTH Interactive Mode and Autonomous`, `CRITICAL_CONFLICT`, `Debatable`), update Role 2.3 description to reference `.devtool/review_config.json["providers"]["programmer"]` (default `gemini-4-hydrogen-xhigh`, `--effort xhigh`), and add §9 Zero-Fluff Output Cap (`Rule 5`).
   - Prepend an explicit `<SUBAGENT-STOP>` block at the top of `skills/task-observer/SKILL.md` forbidding invocation inside headless/subagent task workers and `lifecycle_runner.py` sessions while preserving interactive session trigger behavior.
2. **Stage 2 Designer Slimming, Surgical Line Ranges, and Bilingual Option A (`dev-designer/SKILL.md`)**:
   - Extract verbose worked task examples/templates into `skills/dev-designer/references/task-template-examples.md` (and keep `verification-rows.md` / `verification-row-grammar.md` linked) so `skills/dev-designer/SKILL.md` measures `<= 22528` bytes while preserving all `EXPECTED["skills/dev-designer/SKILL.md"]` contract markers (`exact node ID`, `Decisions Already Made`, etc.).
   - Document Option A bilingual deferral (`.en.md` SSOT in Stages 1–3, Stage 4 Pre-Finish `.vi.md` sync), mandatory `target_files` symbol + `(L<start>-L<end>)` range anchors for modified files `> 200` lines (`Rule 3`), and selective `task-reviewer` metadata tagging (`review_tier: "full"`).
3. **Selective `task-reviewer` & Config-Driven Programmer Wording (`dev-implementation`, `dev-lifecycle`, `principal-review`, `subagent-driven-development`)**:
   - Replace remaining `Gemini Flash 3.8` / `gemini-3.8-flash` strings in `skills/dev-implementation/SKILL.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-lifecycle/references/autonomous-mode.md`, and `skills/principal-review/SKILL.md` with `.devtool/review_config.json` Role 2.3 resolution (`gemini-4-hydrogen-xhigh`, `--effort xhigh`).
   - Enforce selective `task-reviewer` gating across `skills/dev-designer/SKILL.md`, `skills/dev-implementation/SKILL.md`, and `skills/subagent-driven-development/SKILL.md`: skip per-task `task-reviewer` for single-file/trivial tasks and trigger it only when `review_tier: "full"`, high-risk labels (`security`, `architecture`, `concurrency`, `contract`), or `> 2` non-test modules are touched.
   - Inject `Rule 3` (line-bounded reads) and `Rule 5` (Zero-Fluff Output Cap) into `dev-implementation/SKILL.md`, `dev-lifecycle/SKILL.md`, and `subagent-driven-development/SKILL.md`.
4. **Reference Deduplication (`dev-implementation/references/`, `principal-review/references/`, `cross-model-review/references/`)**:
   - Reconcile overlapping reference files (`principal-review-prompt.md`, `principal-review-rules.md`, `review-triage.md`, `local-review-setup.md`, `review-rules.md`) so duplicate instructions live in a single canonical location with thin relative pointers where required by `scripts/verify.sh` §3/§8 and `scripts/test_lifecycle_document_contract.py`.
5. **Stage 4 Pre-Finish Bilingual Sync Hook (`finishing-a-development-branch/SKILL.md`)**:
   - Update Step 5 Pre-Finish Hook (`L119-L160`) to delta-sync `.vi.md` companions from changed `.en.md` Spec/HLD documents, generate/sync `bdd_scenarios.vi.md` matching IDs and ToC headings, and run `check_epic_readiness.py <epic> --strict-bilingual` + `check_bdd_traceability.py plan <epic> --strict-bilingual` before merge while preserving `resume_context.py` archival behavior.
6. Update `scripts/test_lifecycle_document_contract.py` if needed and create `tests/test_tto_docs_and_slimming.py` covering `TTO-HP-05`, `TTO-EC-05`, and `TTO-ST-05`.

## Files

Allowed files:
- `rules/CRITICAL_RULES.md`
- `skills/task-observer/SKILL.md`
- `skills/dev-designer/SKILL.md`
- `skills/dev-designer/references/verification-rows.md`
- `skills/dev-designer/references/task-template-examples.md` (new)
- `skills/dev-implementation/SKILL.md`
- `skills/dev-lifecycle/SKILL.md`
- `skills/dev-lifecycle/references/autonomous-mode.md`
- `skills/dev-lifecycle/references/principal-review.md`
- `skills/principal-review/SKILL.md`
- `skills/subagent-driven-development/SKILL.md`
- `skills/finishing-a-development-branch/SKILL.md`
- `skills/dev-implementation/references/principal-review-prompt.md`
- `skills/dev-implementation/references/principal-review-rules.md`
- `skills/dev-implementation/references/review-triage.md`
- `skills/dev-implementation/references/local-review-setup.md`
- `skills/dev-implementation/references/review-rules.md`
- `skills/principal-review/references/principal-review-rules.md`
- `skills/cross-model-review/references/review-triage.md`
- `skills/cross-model-review/references/local-review-setup.md`
- `scripts/test_lifecycle_document_contract.py`
- `tests/test_tto_docs_and_slimming.py` (new)

Read-only context:
- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Summary, Architecture, and Acceptance Bounds
- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios
- `scripts/verify.sh` — §3/§4/§5b/§8 release link and reference integrity rules

## Design Rationale

Every top-level session loads `rules/CRITICAL_RULES.md` unconditionally and every worker subagent sees skill instructions. Compressing `CRITICAL_RULES.md` (`<= 8KB`) and `dev-designer/SKILL.md` (`<= 22KB`), halting `task-observer` inside subagents via `<SUBAGENT-STOP>`, deduplicating dual-maintained review references, skipping redundant `task-reviewer` subagents on trivial tasks, and moving `.vi.md` translation maintenance to Stage 4 preserves full governance fidelity at a fraction of the token budget. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:writing-skills`, `d3nexus:doc_quality_check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `rules/CRITICAL_RULES.md`: rule sections (L1-L239), Zero-Fluff Output Cap addition
  - `skills/task-observer/SKILL.md`: frontmatter and preamble (L1-L60), new `<SUBAGENT-STOP>` directive
  - `skills/dev-designer/SKILL.md`: design spec and task authoring sections (L1-L540)
  - `skills/dev-designer/references/verification-rows.md`: canonical row examples (L1-L120)
  - `skills/dev-designer/references/task-template-examples.md`: new extracted task templates and example blocks
  - `skills/dev-implementation/SKILL.md`: worker loop and selective reviewer section (L1-L437)
  - `skills/dev-lifecycle/SKILL.md`: stage summary and Role 2.3 config note (L1-L206)
  - `skills/dev-lifecycle/references/autonomous-mode.md`: autonomous Role 2.3 description (L1-L75)
  - `skills/dev-lifecycle/references/principal-review.md`: stage 2 review handoff wording (L1-L74)
  - `skills/principal-review/SKILL.md`: convergence handoff line (L80-L105)
  - `skills/subagent-driven-development/SKILL.md`: flowchart, selective task-reviewer gate, and Zero-Fluff cap (L1-L593)
  - `skills/finishing-a-development-branch/SKILL.md`: Step 5 Pre-Finish Hook (L119-L160)
  - `skills/dev-implementation/references/principal-review-prompt.md`: thin canonical pointer to `principal-review/references/` (L1-L60)
  - `skills/dev-implementation/references/principal-review-rules.md`: deduplicated canonical reference (L1-L25)
  - `skills/dev-implementation/references/review-triage.md`: reconciled pointer / canonical rules (L1-L56)
  - `skills/dev-implementation/references/local-review-setup.md`: deduplicated pointer (L1-L109)
  - `skills/dev-implementation/references/review-rules.md`: concise canonical review rules (L1-L24)
  - `skills/principal-review/references/principal-review-rules.md`: canonical standalone rules (L1-L38)
  - `skills/cross-model-review/references/review-triage.md`: canonical cross-model triage guide (L1-L78)
  - `skills/cross-model-review/references/local-review-setup.md`: canonical local review guide (L1-L76)
  - `scripts/test_lifecycle_document_contract.py`: `EXPECTED` (L12-L157), `LifecycleDocumentContractTest` (L159-L327), `PrincipalReviewWorkflowTest` (L329-L408), `TestReviewSkillContracts` (L410-L454)
  - `tests/test_tto_docs_and_slimming.py`: new doc-contract and size regression tests for `TTO-HP-05`, `TTO-EC-05`, `TTO-ST-05`
- **Downstream Callers**: All downstream repositories inheriting `d3nexus` rules and skills (`verify.sh` §3/§4/§5b/§8 checks, `test_lifecycle_document_contract.py`, `test_resume_context.py`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of byte-size limits, contract string invariants, `<SUBAGENT-STOP>` presence, selective reviewer gating clauses, and Pre-Finish `.vi.md` sync checks.

### BDD SCENARIOS

Covers: TTO-HP-05, TTO-EC-05, TTO-ST-05

```gherkin
Scenario: [TTO-HP-05] [Tier C - Integration] Slimmed rules and dev-designer skill satisfy byte caps and release contract checks

Given the updated rules/CRITICAL_RULES.md, skills/dev-designer/SKILL.md, and skills/task-observer/SKILL.md in the repository
When scripts/test_lifecycle_document_contract.py executes and file byte sizes are measured on disk
Then rules/CRITICAL_RULES.md measures at most 8192 bytes and contains the Zero-Fluff Output Cap directive
And skills/dev-designer/SKILL.md measures at most 22528 bytes while preserving every required section and Extracted reference link
And skills/task-observer/SKILL.md contains an explicit <SUBAGENT-STOP> instruction preventing invocation in subagents and headless workers
And scripts/test_lifecycle_document_contract.py exits with status 0 and zero assertion failures

Scenario: [TTO-EC-05] [Tier C - Integration] Selective task-reviewer gating skips trivial tasks and activates on high-risk or multi-module tasks

Given a trivial single-file documentation or utility task without high-risk labels and review_tier unset
And a complex task carrying review_tier: "full" or labels ["security", "concurrency"] or touching 3 non-test modules
When the selective task-reviewer criteria documented across dev-designer, dev-implementation, and subagent-driven-development are evaluated
Then the trivial single-file task skips the redundant task-reviewer subagent pass
And the complex or high-risk task triggers the dedicated task-reviewer pass before task sign-off

Scenario: [TTO-ST-05] [Tier C - Integration] Finishing-a-development-branch Stage 4 Pre-Finish hook synchronizes .vi.md before merge

Given skills/finishing-a-development-branch/SKILL.md in the updated agent kit
When the Stage 4 finishing workflow specification is inspected and checked by verify.sh §3 and §8
Then an explicit Stage 4 Pre-Finish bilingual sync step delta-syncs Spec and HLD .vi.md companions, generates bdd_scenarios.vi.md, and runs check_epic_readiness.py --strict-bilingual before merge
And all cross-references and doc contract invariants remain unbroken under verify.sh
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_docs_and_slimming.py::test_tto_hp_05_slimmed_rules_and_skills_caps` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_docs_and_slimming.py::test_tto_hp_05_slimmed_rules_and_skills_caps` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V4 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_docs_and_slimming.py scripts/test_lifecycle_document_contract.py scripts/test_resume_context.py` | exit 0; contains "passed" | — |
| V5 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 scripts/test_lifecycle_document_contract.py tests/test_tto_docs_and_slimming.py` | exit 0 | — |
| V6 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_tto_docs_and_slimming.py` | exit 0 | — |
| V7 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_5.xml tests/test_tto_docs_and_slimming.py` | exit 0; results build/test-results/task_5.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `rules/CRITICAL_RULES.md` must stay `<= 8192` bytes, retain all required contract markers (`test_lifecycle_document_contract.py` + `test_resume_context.py`), replace `Gemini Flash 3.8` with `.devtool/review_config.json`, and define §9 Zero-Fluff Output Cap.
- `skills/dev-designer/SKILL.md` must stay `<= 22528` bytes by offloading worked templates to linked `references/` files (`verify.sh` §8 requires every file in `references/` to be referenced by filename in a tracked file).
- `skills/task-observer/SKILL.md` opens with `<SUBAGENT-STOP>` so subagents never activate continuous observer overhead.
- Selective `task-reviewer` criteria are standardized identically across `dev-designer`, `dev-implementation`, and `subagent-driven-development`: trigger on `review_tier: "full"`, labels containing `security`, `architecture`, `concurrency`, or `contract`, or `> 2` non-test modules; otherwise skip.
- Duplicate files across `dev-implementation/references/` and standalone `principal-review/references/` / `cross-model-review/references/` are collapsed to canonical definitions with thin pointers preserving existing link contracts.

## Definition of Done

- Scenarios TTO-HP-05, TTO-EC-05, and TTO-ST-05 pass consistently without byte-budget or link regressions. (V2, V4, V7)
- Existing lifecycle document contract and resume context tests remain green. (V3, V4)
- Python ruff lint and mypy checks pass on test and contract scripts. (V5, V6)
- Slimmed instructions and Stage 4 Pre-Finish bilingual sync hook reviewed during Gate 5 completion. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 1](../epic/token_throttling_optimization/task_01_diff_only_external_review_and_transcript_isolation.md), [Task 2](../epic/token_throttling_optimization/task_02_silent_gate4_and_truncated_test_runners.md), and [Task 3](../epic/token_throttling_optimization/task_03_option_a_bilingual_and_surgical_contract_guards.md).
Blocks [Task 6](../epic/token_throttling_optimization/task_06_integration_and_regression_verification.md).

## References & Rollback

- [Epic HLD](../epic/token_throttling_optimization/token_throttling_optimization.en.md), Architecture Design & Quantitative Budgets (§1–§4).
- **Rollback**: Revert task commit; restores original rules, skill prose, reference copies, and `tests/test_tto_docs_and_slimming.py`.
