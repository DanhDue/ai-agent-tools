---
id: "task_01_persona_review_config_schema_and_resolver"
status: "todo"
priority: "high"
assignee: null
epic: "unified_review_config"
dueDate: null
created: "2026-11-28T03:12:00+07:00"
modified: "2026-11-28T03:12:00+07:00"
completedAt: null
labels: ["architecture", "contract", "dev-config", "persona-config"]
order: "a01"
review_tier: "full"
---

# Task 01: Core Layered Review Schema, Resolvers, and Legacy Fallback

Epic: [unified_review_config](unified_review_config.md)

## Requirement Analysis

Extend `scripts/personas.default.json` and `scripts/persona_config.py` under `schema_version: 1` (strictly additive) to own all four independent pass caps (`max_task_review_passes=2`, `max_fix_passes=1`, `max_principal_review_passes=3`, `max_cross_model_review_passes=3`) and the top-level `review` block (`provider_priority`, `providers`, `quota_thresholds`). Implement deterministic 5-tier precedence (`CLI > project > global > legacy (.devtool/review_config.json) > kit`), alias-or-raw model resolution for review providers, strict validation raising `PersonaConfigError`, and non-blocking legacy migration warnings in `detect_legacy_warnings()`.

## Files

Allowed files:
- `scripts/personas.default.json`
- `scripts/persona_config.py`
- `tests/test_urc_persona_review_config.py` (new)

Read-only context:
- `.devtool/epic/unified_review_config/unified_review_config.md`
- `.devtool/epic/unified_review_config/bdd_scenarios.md`
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `tests/test_fpg_persona_config.py`
- `tests/test_trc_persona_limits.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development` and `d3nexus:python-quality-check` (Python 3 stdlib only, strict type annotations).
- Keep `schema_version: 1` additive so every existing global and project `personas.json` file loads without migration.
- Rank `global` (`$REAL_HOME/.d3nexus/personas.json`) strictly above legacy `.devtool/review_config.json` per key so global `/dev-config` updates take effect across existing repositories that carry auto-seeded legacy config files.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/personas.default.json` (`L1-L184`): add `max_principal_review_passes`, `max_cross_model_review_passes`, and `review` (`provider_priority`, `quota_thresholds`, `providers`).
  - `scripts/persona_config.py` (`L19-L47`, `L135-L170`, `L412-L460`, `L607-L618`, `L720-L749`): `_ALLOWED_TOP_KEYS`, new review constants and frozen dataclasses (`ReviewLimits`, `ReviewProviderBinding`, `ResolvedReviewConfig`), validation helpers, `resolve_review_limits()`, `resolve_review_config()`, updated `resolve_task_review_limits()`, and updated `detect_legacy_warnings()`.
  - `tests/test_urc_persona_review_config.py` (new): unit and subcutaneous integration tests covering `URC-HP-01`, `URC-EC-01`, `URC-EC-02`, `URC-AR-01`, `URC-FR-01`.
- **Downstream Callers**: `scripts/dev_config.py`, `scripts/agy_dispatch.py`, `scripts/resume_context.py`, `skills/dev-implementation/resources/scripts/manage_worker_pool.py`, `skills/check-tasks/resources/scripts/check_tasks.py`, `tests/test_fpg_persona_config.py`, `tests/test_trc_persona_limits.py`, `tests/test_agy_effortless_models.py`.
- **Cross-Platform Bridges**: None (kit Python module).
- **Target Coverage Threshold**: >= 90% on newly added functions in `scripts/persona_config.py`, 100% on validation error paths.

### BDD SCENARIOS

Covers: URC-HP-01, URC-EC-01, URC-EC-02, URC-AR-01, URC-FR-01

```gherkin
Scenario: [URC-HP-01] [Tier C - Integration] Kit defaults resolve all four independent pass limits and external review settings
Given a clean temporary repository and isolated fake REAL_HOME containing no global, project, or legacy review config files
When persona_config.resolve_review_limits and persona_config.resolve_review_config are called
Then max_task_review_passes equals 2, max_fix_passes equals 1, max_principal_review_passes equals 3, and max_cross_model_review_passes equals 3 with source "kit"
And provider_priority equals ("claude", "codex", "kiro", "agy") with source "kit"
And providers resolve "claude" to model_id "opus" (effort "high"), "codex" to "gpt-6.1-sol" (effort "high"), "kiro" to "claude-opus-5.5" (effort "high"), "agy" to "gemini-4-argon-high" (effort "high"), and "ollama" to "gemma4:31b-it-qat" with host "http://localhost:11434"
And quota_thresholds match 5h_min_fraction=0.15, 7d_min_fraction=0.02, kiro_min_fraction=0.03, kiro_min_credits=15.0, and agy_argon_min_fraction=0.10

Scenario: [URC-EC-01] [Tier C - Integration] Review provider model accepts both catalogue aliases with effort expansion and raw model IDs
Given a temporary repository whose global personas.json sets review.providers.agy to {"model": "argon", "effort": "medium"} and review.providers.claude to {"model": "claude-sonnet-4-6", "thinking_level": "low"}
When persona_config.resolve_review_config runs
Then provider "agy" expands alias "argon" + effort "medium" into model_id "gemini-4-argon-medium" with effort "medium"
And provider "claude" accepts the raw ID "claude-sonnet-4-6" verbatim and normalizes legacy key "thinking_level" to effort "low"

Scenario: [URC-EC-02] [Tier C - Integration] Legacy review_config.json serves as read-only fallback only for keys absent from both project and global layers
Given a repository containing ".devtool/review_config.json" with provider_priority=["kiro", "agy"], max_rounds=5, quota_thresholds={"5h_min_fraction": 0.30}, and providers.codex={"model": "gpt-legacy", "thinking_level": "medium"}
And no global or project personas.json defines those keys
When persona_config.resolve_review_config runs
Then provider_priority resolves to ("kiro", "agy") with source "legacy"
And both max_principal_review_passes and max_cross_model_review_passes resolve to 5 with source "legacy"
And quota_thresholds["5h_min_fraction"] resolves to 0.30 with source "legacy" and providers["codex"].model_id resolves to "gpt-legacy" with effort "medium" and source "legacy"
And detect_legacy_warnings includes a non-blocking migration warning naming ".devtool/review_config.json"

Scenario: [URC-AR-01] [Tier C - Integration] Global personas.json beats auto-seeded legacy .devtool/review_config.json while project personas.json beats global
Given a temporary repository containing legacy ".devtool/review_config.json" with provider_priority=["claude", "codex", "kiro", "agy"] and max_rounds=3
And "$REAL_HOME/.d3nexus/personas.json" sets review.provider_priority=["codex", "kiro"] and max_principal_review_passes=2
When persona_config.resolve_review_config runs before and after adding ".agents/config/personas.json" with review.provider_priority=["agy", "claude"] and max_principal_review_passes=1
Then before project config is added, global wins over legacy: provider_priority=("codex", "kiro") (source "global") and max_principal_review_passes=2 (source "global") while max_cross_model_review_passes=3 (source "legacy")
And after project config is added, project wins over global: provider_priority=("agy", "claude") (source "project") and max_principal_review_passes=1 (source "project")

Scenario: [URC-FR-01] [Tier C - Integration] Invalid pass limits, duplicate or unknown priorities, out-of-range thresholds, and CLI-mismatched aliases are rejected with PersonaConfigError
Given malformed persona config layers testing max_principal_review_passes=0, max_cross_model_review_passes=True, max_fix_passes=-1, review.provider_priority=["claude", "claude"], review.provider_priority=["ollama"], review.quota_thresholds.5h_min_fraction=1.5, review.providers.claude={"model": "codex-gpt", "effort": "high"}, and review.providers.claude={"model": "opus", "host": "http://localhost:11434"}
When persona_config.load_persona_config or persona_config.resolve_review_config validates each case
Then every invalid case raises PersonaConfigError with an actionable message naming the offending field or provider
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_persona_review_config.py::test_urc_hp_01_kit_defaults_resolve_limits_and_review_config` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_persona_review_config.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_persona_config.py tests/test_trc_persona_limits.py tests/test_agy_effortless_models.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/persona_config.py tests/test_urc_persona_review_config.py && ruff format --check scripts/persona_config.py tests/test_urc_persona_review_config.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/persona_config.py tests/test_urc_persona_review_config.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_persona_review_config.py --junitxml=build/test-results/task_01.xml` | exit 0; results build/test-results/task_01.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`scripts/persona_config.py` `L26-L47`, `L135-L170`, `L607-L618`, `L720-L749`)**: Existing constants `DEFAULT_MAX_TASK_REVIEW_PASSES = 2`, `DEFAULT_MAX_FIX_PASSES = 1`, `_ALLOWED_TOP_KEYS`, `_validate_task_review_limits()`, `resolve_task_review_limits()`, and `detect_legacy_warnings()`.
- **New contract (`scripts/persona_config.py` & `scripts/personas.default.json`)**:
  - Constants: `DEFAULT_MAX_PRINCIPAL_REVIEW_PASSES = 3`, `DEFAULT_MAX_CROSS_MODEL_REVIEW_PASSES = 3`, `REVIEW_PRIORITY_PROVIDERS = ("claude", "codex", "kiro", "agy")`, `REVIEW_PROVIDERS = ("claude", "codex", "kiro", "agy", "ollama")`, `REVIEW_THINKING_LEVELS = ("none", "light", "low", "medium", "high", "xhigh", "extra-high")`, `DEFAULT_REVIEW_QUOTA_THRESHOLDS = {"5h_min_fraction": 0.15, "7d_min_fraction": 0.02, "kiro_min_fraction": 0.03, "kiro_min_credits": 15.0, "agy_argon_min_fraction": 0.10}`.
  - Dataclasses: `ReviewLimits(max_task_review_passes, max_fix_passes, max_principal_review_passes, max_cross_model_review_passes, sources)`, `ReviewProviderBinding(provider, model, model_id, effort, host, source)`, `ResolvedReviewConfig(provider_priority, providers, quota_thresholds, limits, sources)` with `max_rounds_for_kind(kind: str) -> int` returning `max_principal_review_passes` for `"principal"` and `max_cross_model_review_passes` for `"code"`/`"epic"` (raising `PersonaConfigError` on unknown kind).
  - Precedence per key: `project` (`.agents/config/personas.json`) > `global` (`$REAL_HOME/.d3nexus/personas.json`) > `legacy` (`.devtool/review_config.json`, read-only and malformed-safe) > `kit` (`scripts/personas.default.json`). Legacy `max_rounds` (when valid `int >= 1`) falls back for both `max_principal_review_passes` and `max_cross_model_review_passes` when absent in `project` and `global`.
  - Alias-or-raw model resolution: if `model` is in merged `models` catalogue, enforce `models[alias]["cli"] == provider`, set `effort = "none"` when `efforts == ["none"]`, else validate `effort in efforts` when `{effort}` template is present and expand `{effort}`; if `model` is not in `models`, keep raw string as `model_id`. Normalize legacy `thinking_level` to `effort` on read.
  - `resolve_task_review_limits(project_root, *, real_home=None) -> tuple[int, int]` delegates to `resolve_review_limits()` keeping identical signature and return type.
  - In TDD `RED` (`V1`), `test_urc_hp_01_kit_defaults_resolve_limits_and_review_config` checks `getattr(persona_config, "resolve_review_limits", None)` and calls `pytest.fail(...)` when missing so `V1` exits `1` with `FAILED`.

## Definition of Done

- [ ] `scripts/personas.default.json` adds `max_principal_review_passes` (`3`), `max_cross_model_review_passes` (`3`), and `review` (`provider_priority`, `quota_thresholds`, `providers`) while keeping existing defaults intact (V2, V5)
- [ ] `scripts/persona_config.py` implements `ReviewLimits`, `ReviewProviderBinding`, `ResolvedReviewConfig`, `resolve_review_limits`, `resolve_review_config`, 5-tier precedence (`project > global > legacy > kit`), alias-or-raw expansion, validation guards, and legacy review warnings (V2, V5)
- [ ] All 5 assigned scenarios (`URC-HP-01`, `URC-EC-01`, `URC-EC-02`, `URC-AR-01`, `URC-FR-01`) pass in `tests/test_urc_persona_review_config.py` with JUnit XML written to `build/test-results/task_01.xml` (V2, V5)
- [ ] Existing persona config, limits, and effortless-models regression suites pass without regressions (V3)
- [ ] `ruff check`, `ruff format --check`, and `mypy` pass across all Allowed files (V4)

## Dependencies & Blockers

- None (Wave 1 root task).

## References & Rollback

- Reference HLD: [unified_review_config.md](unified_review_config.md)
- Rollback: Revert changes to `scripts/personas.default.json` and `scripts/persona_config.py`, and delete `tests/test_urc_persona_review_config.py`.
