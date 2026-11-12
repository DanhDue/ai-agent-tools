---
id: "task_05_slimming_rules_skills_dedup_and_selective_reviewer"
status: "done"
priority: "high"
assignee: null
epic: "token_throttling_optimization"
dueDate: null
created: "2026-11-13T02:36:00Z"
modified: "2026-11-12T22:29:04Z"
completedAt: "2026-11-12T22:29:04Z"
labels: ["docs", "slimming", "skills", "token-optimization"]
order: "a5"
---

# Task 5: Rules and Skills Slimming, Deduplication, Selective Reviewer, and Pre-Finish Sync

Epic: [token_throttling_optimization](token_throttling_optimization.en.md)

## Requirement Analysis

Slim always-on instructions and lifecycle skills (`Rule 1`, `Rule 3`, `Rule 5`), replace scattered legacy `Gemini Flash 3.8` / `gemini-3.8-flash` defaults with config-driven `.devtool/review_config.json` resolution (`gemini-4-hydrogen-xhigh`, `--effort xhigh`), deduplicate overlapping reference files across `dev-implementation/`, `principal-review/`, and `cross-model-review/`, enforce selective `task-reviewer` gating, and add the Stage 4 Pre-Finish bilingual sync hook:
1. **Always-On Rule & Observer Slimming (`CRITICAL_RULES.md`, `task-observer/SKILL.md`)**:
   - Compress `rules/CRITICAL_RULES.md` to `<= 8192` bytes by offloading extended checklists into `skills/dev-lifecycle/references/governance-checklists.md` (new, referenced by name from a tracked file for `verify.sh` §8) while preserving the leading `---\ntrigger: always_on\n---` YAML frontmatter block (`scripts/verify.sh` §5b) alongside all mandatory headings and markers (`## 8. Mandatory Two-Tier Project Memory & Tri-Role Persona Discipline`, `## 9. Shell Configuration (.zshrc) & Multi-Profile OS Boundary Safety`, `BOTH Interactive Mode and Autonomous`, `CRITICAL_CONFLICT`, `Debatable`, `"after Gate 4 passes"`, `"Cross-model review must return to a full Gate 4 run"`, `"run_external_review.py triage"`), update Role 2.3 description to reference `.devtool/review_config.json["providers"]["programmer"]` (default `gemini-4-hydrogen-xhigh`, `--effort xhigh`), and add `## 10. Zero-Fluff Output Cap` (`Rule 5`) scoped strictly to **discretionary prose/narration** while explicitly preserving mandatory machine-parsed Verdicts, complete Findings tables, structured JSON/provider gate results, worker status contracts, and human Gate prompts.
   - Insert `<SUBAGENT-STOP>` immediately after the YAML frontmatter in `skills/task-observer/SKILL.md` (`L20+`, never before the opening `---` delimiter so `verify.sh` §2 frontmatter parsing stays green), amend lines `L12-L18` of `description` in `skills/task-observer/SKILL.md` so the session-start trigger explicitly excludes subagents and headless task workers, and pair that with an explicit `"do not invoke d3nexus:task-observer"` instruction in `skills/subagent-driven-development/implementer-prompt.md` (and in `lifecycle_runner._execute_single_task()` in Task 4).
2. **Stage 2 Designer Slimming, Surgical Line Ranges, and Bilingual Option A (`dev-designer/SKILL.md`)**:
   - Extract verbose worked task examples/templates into `skills/dev-designer/references/task-template-examples.md` (and keep `verification-rows.md` / `verification-row-grammar.md` linked) so `skills/dev-designer/SKILL.md` measures `<= 22528` bytes while preserving all `EXPECTED["skills/dev-designer/SKILL.md"]` contract markers (`exact node ID`, `Decisions Already Made`, etc.).
   - Document Option A bilingual deferral (`.en.md` SSOT in Stages 1–3, Stage 4 Pre-Finish `.vi.md` sync), mandatory `target_files` symbol + `(L<start>-L<end>)` range anchors for modified files `> 200` lines (`Rule 3`), and selective `task-reviewer` metadata tagging (`review_tier: "full"`).
3. **Selective `task-reviewer` & Config-Driven Programmer Wording (`dev-implementation`, `dev-lifecycle`, `principal-review`, `docs/lifecycles`, `subagent-driven-development`)**:
   - Replace remaining `Gemini Flash 3.8` / `gemini-3.8-flash` strings in `skills/dev-implementation/SKILL.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-lifecycle/references/autonomous-mode.md`, `skills/principal-review/SKILL.md`, `docs/lifecycles.en.md`, and `docs/lifecycles.vi.md` with `.devtool/review_config.json` Role 2.3 resolution (`gemini-4-hydrogen-xhigh`, `--effort xhigh`) while keeping existing lifecycle diagram/token assertions in `test_lifecycle_document_contract.py` passing.
   - Enforce selective `task-reviewer` gating across `skills/dev-designer/SKILL.md`, `skills/dev-implementation/SKILL.md`, and `skills/subagent-driven-development/SKILL.md`: skip per-task `task-reviewer` for single-file/trivial tasks and trigger it only when `review_tier: "full"`, high-risk labels (`security`, `architecture`, `concurrency`, `contract`), or `> 2` non-test modules are touched.
   - Inject `Rule 3` (line-bounded reads using `StartLine`/`EndLine` or `sed -n 'X,Yp'` and symbol search) and `Rule 5` (Zero-Fluff Output Cap preserving mandatory Verdicts, Findings, and gate contracts) into `dev-implementation/SKILL.md`, `dev-lifecycle/SKILL.md`, `subagent-driven-development/SKILL.md`, and `skills/subagent-driven-development/implementer-prompt.md` — offsetting EVERY insertion into `skills/dev-lifecycle/SKILL.md` (`2499/2500` words) and `skills/dev-implementation/SKILL.md` (`4490/4500` words) with at least equal removals or offloading to `references/` so both hard word caps remain strictly unbroken (`<= 2500` and `<= 4500`).
4. **Reference Deduplication (`dev-implementation/references/`, `principal-review/references/`, `cross-model-review/references/`)**:
   - Reconcile overlapping reference files (`principal-review-prompt.md`, `principal-review-rules.md`, `review-triage.md`, `local-review-setup.md`, `review-rules.md`) so duplicate instructions live in a single canonical location with thin relative pointers where required by `scripts/verify.sh` §3/§8 and `scripts/test_lifecycle_document_contract.py`.
5. **Stage 4 Pre-Finish Bilingual Sync Hook (`finishing-a-development-branch/SKILL.md`)**:
   - Update Step 5 Pre-Finish Hook (`L119-L160`) to delta-sync `.vi.md` companions from changed `.en.md` Spec/HLD documents, refresh `<!-- sync-en-sha256: <hex16> -->` content-sync provenance inside each synced Spec/HLD `.vi.md`, generate/sync `bdd_scenarios.vi.md` matching IDs and ToC headings, and run the complete executable verification sequence before merge while preserving `resume_context.py` archival behavior:
     - `python3 skills/dev-implementation/resources/scripts/check_epic_readiness.py <epic_slug> --strict-bilingual`
     - `python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks .devtool/epic/<epic_dir>/task_*.md --strict-bilingual`
6. Update `scripts/test_lifecycle_document_contract.py` if needed and create `tests/test_tto_docs_and_slimming.py` covering `TTO-HP-05` (`test_tto_hp_05_slimmed_rules_and_skills_caps` including asserting `rules/CRITICAL_RULES.md` starts with `---\ntrigger: always_on\n---`), `TTO-EC-05`, `TTO-ST-05`, `skills/subagent-driven-development/implementer-prompt.md` bounded-read rules, Zero-Fluff Verdict/Findings exemptions, and the exact Stage 4 Pre-Finish `check_bdd_traceability.py` command.

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
- `skills/dev-lifecycle/references/governance-checklists.md` (new)
- `docs/lifecycles.en.md`
- `docs/lifecycles.vi.md`
- `skills/principal-review/SKILL.md`
- `skills/subagent-driven-development/SKILL.md`
- `skills/subagent-driven-development/implementer-prompt.md`
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
  - `skills/dev-lifecycle/SKILL.md`: stage summary and Role 2.3 config note (L1-L206, balanced removals keeping `<= 2500` words)
  - `skills/dev-lifecycle/references/autonomous-mode.md`: autonomous Role 2.3 description (L1-L75)
  - `skills/dev-lifecycle/references/principal-review.md`: stage 2 review handoff wording (L1-L74)
  - `skills/dev-lifecycle/references/governance-checklists.md`: new offloaded extended workflow checklists from `CRITICAL_RULES.md`
  - `docs/lifecycles.en.md`: Role 2.3 programmer config update (`L125-L155`)
  - `docs/lifecycles.vi.md`: Role 2.3 programmer config update (`L125-L155`)
  - `skills/principal-review/SKILL.md`: convergence handoff line (L80-L105)
  - `skills/subagent-driven-development/SKILL.md`: flowchart, selective task-reviewer gate, and Zero-Fluff cap (L1-L593)
  - `skills/subagent-driven-development/implementer-prompt.md`: bounded-read rules and discretionary-narration Zero-Fluff cap (L1-L187)
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

Given the updated rules/CRITICAL_RULES.md, skills/dev-designer/SKILL.md, skills/dev-lifecycle/SKILL.md, skills/dev-implementation/SKILL.md, and skills/task-observer/SKILL.md in the repository
When scripts/test_lifecycle_document_contract.py executes and file byte/word sizes are measured on disk
Then rules/CRITICAL_RULES.md measures at most 8192 bytes retaining §9 Shell Configuration and adding §10 Zero-Fluff Output Cap
And skills/dev-designer/SKILL.md measures at most 22528 bytes, skills/dev-lifecycle/SKILL.md stays <= 2500 words, and skills/dev-implementation/SKILL.md stays <= 4500 words while preserving every required section and Extracted reference link
And skills/task-observer/SKILL.md places <SUBAGENT-STOP> immediately after valid YAML frontmatter and amends its description trigger to exclude subagents and headless workers
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
| V5 | GREEN | `python3 -m unittest scripts/test_verifiable_handoff_text.py scripts/test_verifiable_handoff.py` | exit 0; contains "OK" | — |
| V6 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_docs_and_slimming.py::test_tto_hp_05_lifecycle_word_caps` | exit 0; contains "passed" | — |
| V7 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 scripts/test_lifecycle_document_contract.py tests/test_tto_docs_and_slimming.py` | exit 0 | — |
| V8 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_tto_docs_and_slimming.py` | exit 0 | — |
| V9 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_5.xml tests/test_tto_docs_and_slimming.py` | exit 0; results build/test-results/task_5.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `rules/CRITICAL_RULES.md` must stay `<= 8192` bytes, preserve the leading `---` / `trigger: always_on` / `---` frontmatter block required by `scripts/verify.sh` §5b, retain all required contract markers (`test_lifecycle_document_contract.py`, `test_resume_context.py`, `test_verifiable_handoff_text.py` including `"after Gate 4 passes"`, `"Cross-model review must return to a full Gate 4 run"`, `"run_external_review.py triage"`, and `"## 9. Shell Configuration heading retained"`), offload extended checklists into `skills/dev-lifecycle/references/governance-checklists.md` (referenced cleanly from tracked files for `verify.sh` §8), replace `Gemini Flash 3.8` with `.devtool/review_config.json`, and define `## 10. Zero-Fluff Output Cap` scoped strictly to discretionary prose/narration while explicitly preserving mandatory machine-parsed Verdicts, Findings tables, JSON/provider gate results, worker statuses, and human Gate prompts; `test_tto_hp_05_slimmed_rules_and_skills_caps` (V2) verifies `rules/CRITICAL_RULES.md` starts with `---\ntrigger: always_on\n---`.
- Every insertion into `skills/dev-lifecycle/SKILL.md` (`2499/2500` baseline words) and `skills/dev-implementation/SKILL.md` (`4490/4500` baseline words) must be balanced by at least equal word reductions or offloading to `references/` so the existing hard word caps (`<= 2500` and `<= 4500`) remain unchanged and unbroken.
- Stage 4 Pre-Finish Hook in `skills/finishing-a-development-branch/SKILL.md` invokes exact valid CLI arguments: `check_epic_readiness.py <epic_slug> --strict-bilingual` and `check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks .devtool/epic/<epic_dir>/task_*.md --strict-bilingual`, after delta-syncing `.vi.md` files and stamping `<!-- sync-en-sha256: <hex16> -->`.
- `skills/dev-designer/SKILL.md` must stay `<= 22528` bytes by offloading worked templates to linked `references/` files (`verify.sh` §8 requires every file in `references/` to be referenced by filename in a tracked file).
- `skills/task-observer/SKILL.md` places `<SUBAGENT-STOP>` immediately after YAML frontmatter (`L20+`, preserving `verify.sh` §2 `name`/`description` keys), amends `description` to exclude subagents and headless workers, and is explicitly blocked in `implementer-prompt.md` + Task 4 worker prompts.
- Selective `task-reviewer` criteria are standardized identically across `dev-designer`, `dev-implementation`, and `subagent-driven-development`: trigger on `review_tier: "full"`, labels containing `security`, `architecture`, `concurrency`, or `contract`, or `> 2` non-test modules; otherwise skip.
- Duplicate files across `dev-implementation/references/` and standalone `principal-review/references/` / `cross-model-review/references/` are collapsed to canonical definitions with thin pointers preserving existing link contracts.

## Definition of Done

- Scenarios TTO-HP-05, TTO-EC-05, and TTO-ST-05 pass consistently without byte-budget, word-cap, or link regressions. (V2, V4, V6, V9)
- Existing lifecycle document contract, handoff text, and resume context tests remain green. (V3, V4, V5)
- Python ruff lint and mypy checks pass on test and contract scripts. (V7, V8)
- Slimmed instructions and Stage 4 Pre-Finish bilingual sync hook reviewed during Gate 5 completion. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 1](task_01_diff_only_external_review_and_transcript_isolation.md), [Task 2](task_02_silent_gate4_and_truncated_test_runners.md), and [Task 3](task_03_option_a_bilingual_and_surgical_contract_guards.md).
Blocks [Task 6](task_06_integration_and_regression_verification.md).

## References & Rollback

- [Epic HLD](token_throttling_optimization.en.md), Architecture Design & Quantitative Budgets (§1–§4).
- **Rollback**: Revert task commit; restores original rules, skill prose, reference copies, and `tests/test_tto_docs_and_slimming.py`.
