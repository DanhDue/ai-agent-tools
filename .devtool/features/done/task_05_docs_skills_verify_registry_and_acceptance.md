---
id: "task_05_docs_skills_verify_registry_and_acceptance"
status: "done"
priority: "high"
assignee: null
epic: "unified_review_config"
dueDate: null
created: "2026-11-28T03:12:00+07:00"
modified: "2026-11-27T21:42:01Z"
completedAt: "2026-11-27T21:42:01Z"
labels: ["architecture", "docs", "verification", "dev-config"]
order: "a05"
review_tier: "full"
---

# Task 05: Skill Docs, Quick Guide, verify.sh Suite Registration, and End-to-End Acceptance Suite

Epic: [unified_review_config](unified_review_config.md)

## Requirement Analysis

Document `/dev-config limits` and `/dev-config review` (`kit -> global -> project` precedence, shared `provider_priority`, four independent pass limits, alias-or-raw model resolution, and `.devtool/state/review_runtime.json` runtime isolation with `.devtool/review_config.json` read-only fallback) across `skills/dev-config/SKILL.md`, `skills/principal-review/SKILL.md`, `skills/cross-model-review/SKILL.md`, `skills/dev-lifecycle/SKILL.md`, `rules/CRITICAL_RULES.md`, and `docs/dev-config-quick-guide.en.md` while strictly honoring existing word/byte caps (`rules/CRITICAL_RULES.md <= 1000` words). Register all five URC test suites in `scripts/verify.sh` (`§26`) and add `tests/test_urc_end_to_end_acceptance.py` verifying the complete CLI -> `persona_config` -> `run_external_review` -> `lifecycle_runner` flow and documentation invariants.

## Files

Allowed files:
- `skills/dev-config/SKILL.md`
- `skills/principal-review/SKILL.md`
- `skills/cross-model-review/SKILL.md`
- `skills/dev-lifecycle/SKILL.md`
- `rules/CRITICAL_RULES.md`
- `docs/dev-config-quick-guide.en.md`
- `scripts/verify.sh`
- `tests/test_urc_end_to_end_acceptance.py` (new)

Read-only context:
- `.devtool/epic/unified_review_config/unified_review_config.md`
- `.devtool/epic/unified_review_config/bdd_scenarios.md`
- `scripts/persona_config.py`
- `scripts/dev_config.py`
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`
- `tests/test_tto_docs_and_slimming.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development` and `d3nexus:python-quality-check`.
- Keep `rules/CRITICAL_RULES.md` strictly `<= 1000` words (currently `994` words) by replacing `.devtool/review_config.json` references in place with `/d3nexus:dev-config review` without net word growth.
- Register all five new suites under `# 26. Unified Review Config suites` in `scripts/verify.sh` (`L482-L490`) so every future release verifies them automatically.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-config/SKILL.md` (`L1-L106`): add `limits` and `review` rows to Invocation Mapping and brief usage guidance.
  - `skills/principal-review/SKILL.md` (`L56-L70`): reference layered `/d3nexus:dev-config review` & `max_principal_review_passes` (default `3`, `.devtool/review_config.json` read-only fallback).
  - `skills/cross-model-review/SKILL.md` (`L20-L70`): reference layered `/d3nexus:dev-config review` & `max_cross_model_review_passes` (default `3`, `.devtool/review_config.json` read-only fallback).
  - `skills/dev-lifecycle/SKILL.md` (`L83-L95`): reference `/d3nexus:dev-config review` alongside `.devtool/review_config.json` fallback at Gate 2 Unified Confirmation.
  - `rules/CRITICAL_RULES.md` (`L29-L36`): update Gate 2 priority source reference cleanly while staying `<= 1000` words.
  - `docs/dev-config-quick-guide.en.md` (`L1-L400`): document `dev-config limits`, `dev-config review`, 5-tier precedence, and `.devtool/state/review_runtime.json`.
  - `scripts/verify.sh` (`L482-L491`): append `# 26. Unified Review Config suites` registering all 5 `tests/test_urc_*.py` files.
  - `tests/test_urc_end_to_end_acceptance.py` (new): end-to-end acceptance tests covering `URC-HP-06`, `URC-EC-05`, `URC-FR-04`.
- **Downstream Callers**: `scripts/verify.sh` (§2 frontmatter, §3 links, §4 ToC, §5 namespace, §5b rule frontmatter), `tests/test_tto_docs_and_slimming.py`.
- **Cross-Platform Bridges**: None (kit docs, registry, and Python acceptance tests).
- **Target Coverage Threshold**: 100% pass across end-to-end acceptance assertions and `verify.sh` structural checks.

### BDD SCENARIOS

Covers: URC-HP-06, URC-EC-05, URC-FR-04

```gherkin
Scenario: [URC-HP-06] [Tier C - Integration] End-to-end dev-config changes propagate cleanly to external review, runner, docs, and verify.sh registry
Given a clean temporary repository and isolated fake REAL_HOME where global and project settings are written exclusively via dev_config.py CLI commands
When dev_config.py status, run_external_review.load_review_config, run_external_review.resolve_effective_max_rounds, and LifecycleRunner resolve settings against that workspace
Then all consumers agree on the exact same provider_priority, resolved provider model IDs, quota_thresholds, and four independent pass caps
And skills/dev-config/SKILL.md, skills/principal-review/SKILL.md, skills/cross-model-review/SKILL.md, skills/dev-lifecycle/SKILL.md, rules/CRITICAL_RULES.md (<= 1000 words), docs/dev-config-quick-guide.en.md, and scripts/verify.sh all document and register the unified review config and all 5 URC test suites

Scenario: [URC-EC-05] [Tier C - Integration] Fixed-effort catalogue alias in review.providers resolves effort to "none" and preserves zero-cap fix passes
Given a temporary repository with global personas.json setting review.providers.agy={"model": "orchestrator-argon"} and max_fix_passes=0
When persona_config.resolve_review_config and dev_config.py limits --json execute
Then provider "agy" resolves model_id "gemini-pro-orchestrator-g1-pro" with effort "none"
And max_fix_passes resolves cleanly to 0 without raising validation errors

Scenario: [URC-FR-04] [Tier C - Integration] Running dev_config limits or review commands on missing directories creates parent folders atomically without leaving .tmp artifacts
Given an isolated fake REAL_HOME where "$REAL_HOME/.d3nexus" does not exist yet and a temporary repository where ".agents/config" does not exist yet
When dev_config.py writes global limits and project review priority
Then both target JSON files are created atomically with valid JSON and schema_version=1
And zero ".tmp" files remain in either directory
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_end_to_end_acceptance.py::test_urc_hp_06_end_to_end_cli_propagation_and_docs_registry` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_end_to_end_acceptance.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_docs_and_slimming.py tests/test_urc_persona_review_config.py tests/test_urc_dev_config_cli.py tests/test_urc_external_review_integration.py tests/test_urc_lifecycle_runner_review_config.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_urc_end_to_end_acceptance.py && ruff format --check tests/test_urc_end_to_end_acceptance.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_urc_end_to_end_acceptance.py --ignore-missing-imports --follow-imports=silent && python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc docs/dev-config-quick-guide.en.md` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_persona_review_config.py tests/test_urc_dev_config_cli.py tests/test_urc_external_review_integration.py tests/test_urc_lifecycle_runner_review_config.py tests/test_urc_end_to_end_acceptance.py --junitxml=build/test-results/unified-review-config.xml` | exit 0; results build/test-results/unified-review-config.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`rules/CRITICAL_RULES.md` `L29-L36`, `scripts/verify.sh` `L482-L491`, `tests/test_tto_docs_and_slimming.py`)**: `rules/CRITICAL_RULES.md` word cap is `<= 1000` words (currently `994`); `skills/dev-config/SKILL.md` frontmatter MUST stay strictly `name` + `description`; every cross-skill link uses `d3nexus:` namespace (zero `superpowers:` references).
- **New contract (`scripts/verify.sh` §26)**:
  - Register all five suites under `# 26. Unified Review Config suites`:
    - `("26", "pytest", "tests/test_urc_persona_review_config.py", 15, False)`
    - `("26", "pytest", "tests/test_urc_dev_config_cli.py", 15, False)`
    - `("26", "pytest", "tests/test_urc_external_review_integration.py", 15, False)`
    - `("26", "pytest", "tests/test_urc_lifecycle_runner_review_config.py", 15, False)`
    - `("26", "pytest", "tests/test_urc_end_to_end_acceptance.py", 15, True)`
- **Final JUnit XML**: `V5` writes the combined epic report `build/test-results/unified-review-config.xml` matching the HLD `Integration results:` contract and containing all 22 `URC-*` scenario IDs across the five test suites.

## Definition of Done

- [x] `skills/dev-config/SKILL.md`, `skills/principal-review/SKILL.md`, `skills/cross-model-review/SKILL.md`, `skills/dev-lifecycle/SKILL.md`, `rules/CRITICAL_RULES.md` (`<= 1000` words), and `docs/dev-config-quick-guide.en.md` document `/dev-config limits`, `/dev-config review`, 5-tier precedence, and runtime state isolation cleanly (V2, V3, V4) — exit 0; CRITICAL_RULES.md 986 words / 8158 bytes, dev-lifecycle 2492 words
- [x] All five `tests/test_urc_*.py` suites are registered in `scripts/verify.sh` under section 26 (V2, V5) — exit 0; 5 URC suites registered under §26
- [x] All 3 assigned scenarios (`URC-HP-06`, `URC-EC-05`, `URC-FR-04`) pass in `tests/test_urc_end_to_end_acceptance.py` and the combined JUnit XML `build/test-results/unified-review-config.xml` contains all 22 `URC-*` scenarios passing (V2, V5) — exit 0; 22/22 URC scenarios PASS
- [x] `tests/test_tto_docs_and_slimming.py` and all URC suites pass without regressions (V3) — exit 0; regression suites passed
- [x] `ruff check`, `ruff format --check`, `mypy`, and `check_document.py --require-toc` pass across all Allowed files (V4) — exit 0; lint, format, type, and ToC checks passed

## Dependencies & Blockers

- Blocked by [Task 01](task_01_persona_review_config_schema_and_resolver.md), [Task 02](task_02_dev_config_cli_limits_review_and_thresholds.md), [Task 03](task_03_external_review_layered_config_and_runtime_state.md), and [Task 04](task_04_lifecycle_runner_external_review_integration.md).

## References & Rollback

- Reference HLD: [unified_review_config.md](unified_review_config.md)
- Rollback: Revert doc/skill/`scripts/verify.sh` edits and delete `tests/test_urc_end_to_end_acceptance.py`.
