---
id: "task_02_dev_config_cli_limits_review_and_thresholds"
status: "todo"
priority: "high"
assignee: null
epic: "unified_review_config"
dueDate: null
created: "2026-11-28T03:12:00+07:00"
modified: "2026-11-28T03:12:00+07:00"
completedAt: null
labels: ["architecture", "contract", "dev-config", "cli"]
order: "a02"
review_tier: "full"
---

# Task 02: dev-config CLI (limits, review, Updated status, models remove Guard, and Quota Thresholds)

Epic: [unified_review_config](unified_review_config.md)

## Requirement Analysis

Extend `scripts/dev_config.py` with the `limits` subcommand (independent read/write/reset of `max_task_review_passes`, `max_fix_passes`, `max_principal_review_passes`, and `max_cross_model_review_passes`) and the `review` subcommand (`status`, `priority`, `set`, `thresholds`, `reset`) across `--scope global|project` with global-masked-by-project warnings. Update `dev_config.py status [--json]` to report all four pass limits and external review settings while preserving `task_review_limits`. Protect `cmd_models_remove` from removing aliases referenced by `review.providers.*`, and route `_load_quota_thresholds` in `scripts/dev_config.py` and `_load_thresholds` in `scripts/agy_dispatch.py` through `persona_config.resolve_review_config()`.

## Files

Allowed files:
- `scripts/dev_config.py`
- `scripts/agy_dispatch.py`
- `tests/test_urc_dev_config_cli.py` (new)

Read-only context:
- `.devtool/epic/unified_review_config/unified_review_config.md`
- `.devtool/epic/unified_review_config/bdd_scenarios.md`
- `scripts/persona_config.py`
- `scripts/personas.default.json`
- `tests/test_fpg_agy_dispatch.py`
- `tests/test_fpg_set_provider_model_profile.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development` and `d3nexus:python-quality-check`.
- Reuse `_pc.locked_update_layer()` so every write validates before atomic replace under `fcntl.flock`, leaving zero `.tmp` files and never partially mutating JSON on validation errors.
- Prune empty `review` sub-dicts cleanly on `review reset` so `personas.json` remains minimal and readable.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/dev_config.py` (`L119-L134`, `L224-L300`, `L429-L470`, `L856-L885`, `L1412-L1728`): `_load_quota_thresholds()`, `cmd_status()`, `_find_alias_references()`, `cmd_models_remove()`, new `cmd_limits()` / `cmd_limits_reset()` / `cmd_review_*()`, `_build_parser()`, `_dispatch_args()`.
  - `scripts/agy_dispatch.py` (`L126-L143`): `_load_thresholds()` delegating to `persona_config.resolve_review_config(project_root, real_home=real_home).quota_thresholds`.
  - `tests/test_urc_dev_config_cli.py` (new): CLI and dispatch-threshold integration tests covering `URC-HP-02`, `URC-HP-03`, `URC-EC-03`, `URC-ST-01`, `URC-ST-02`, `URC-FR-02`.
- **Downstream Callers**: `scripts/agy_dispatch.py`, `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`, `tests/test_fpg_agy_dispatch.py`, `tests/test_fpg_set_provider_model_profile.py`, `tests/test_fpg_agy_profile_pool.py`, `tests/test_trc_persona_limits.py`.
- **Cross-Platform Bridges**: None (kit Python CLI).
- **Target Coverage Threshold**: >= 90% on newly added `dev_config.py` handlers and `agy_dispatch.py::_load_thresholds`.

### BDD SCENARIOS

Covers: URC-HP-02, URC-HP-03, URC-EC-03, URC-ST-01, URC-ST-02, URC-FR-02

```gherkin
Scenario: [URC-HP-02] [Tier C - Integration] dev-config limits independently reads and updates all four pass caps across global and project scopes
Given a clean temporary repository and isolated fake REAL_HOME
When dev_config.py runs "limits --principal-review 2 --cross-model-review 4 --scope global" followed by "limits --task-review 3 --fix 0 --scope project"
Then "$REAL_HOME/.d3nexus/personas.json" persists max_principal_review_passes=2 and max_cross_model_review_passes=4 without writing max_task_review_passes or max_fix_passes
And ".agents/config/personas.json" persists max_task_review_passes=3 and max_fix_passes=0
And "dev_config.py limits --json" returns task=3 (project), fix=0 (project), principal=2 (global), cross_model=4 (global)
And "dev_config.py status --json" preserves task_review_limits (3, 0) while adding review_limits (3, 0, 2, 4)

Scenario: [URC-HP-03] [Tier C - Integration] dev-config review configures shared priority, provider models, and quota thresholds across global and project scopes
Given a clean temporary repository and isolated fake REAL_HOME
When dev_config.py runs "review priority codex,claude,kiro,agy --scope global", "review set agy --model gemini-4-carbon-high --effort high --scope global", "review set ollama --model qwen2.5-coder:32b --host http://127.0.0.1:11434 --scope project", and "review thresholds --5h 0.25 --kiro-credits 25.0 --scope global"
Then "dev_config.py review status --json" reports provider_priority ["codex", "claude", "kiro", "agy"] with source "global"
And provider "agy" resolves model_id "gemini-4-carbon-high" (effort "high", source "global") while provider "ollama" resolves model_id "qwen2.5-coder:32b" with host "http://127.0.0.1:11434" (source "project")
And quota_thresholds report 5h_min_fraction=0.25 and kiro_min_credits=25.0 (source "global")
And both dev_config._load_quota_thresholds and agy_dispatch._load_thresholds return 5h_min_fraction=0.25 and kiro_min_credits=25.0

Scenario: [URC-EC-03] [Tier C - Integration] Global write emits masking warning when project personas.json overrides the same review or limit key
Given a temporary repository where ".agents/config/personas.json" sets max_principal_review_passes=1 and review.provider_priority=["kiro", "claude"]
When dev_config.py runs "limits --principal-review 4 --scope global" and "review priority codex,claude --scope global"
Then both commands succeed (exit 0) and write to "$REAL_HOME/.d3nexus/personas.json"
And stderr prints a masking warning identifying the project override in ".agents/config/personas.json"
And effective resolution in that repository remains max_principal_review_passes=1 and provider_priority=("kiro", "claude")

Scenario: [URC-ST-01] [Tier C - Integration] Resetting project review or limit overrides restores global layer without disturbing sibling keys
Given a temporary repository with global max_principal_review_passes=2, global review.provider_priority=["codex", "claude"], project max_principal_review_passes=1, project max_fix_passes=0, and project review.provider_priority=["kiro", "agy"]
When dev_config.py runs "limits reset principal --scope project" and "review reset priority --scope project"
Then max_principal_review_passes falls back to 2 (source "global") and provider_priority falls back to ("codex", "claude") (source "global")
And project max_fix_passes remains 0 (source "project") untouched

Scenario: [URC-ST-02] [Tier C - Integration] Resetting all review overrides in a scope prunes empty review objects cleanly
Given a temporary repository whose ".agents/config/personas.json" contains active_preset="default" plus review.provider_priority, review.providers.claude, and review.quota_thresholds
When dev_config.py runs "review reset all --scope project"
Then ".agents/config/personas.json" no longer contains a "review" key while retaining active_preset="default"
And running "review reset all --scope project" a second time exits 0 idempotently

Scenario: [URC-FR-02] [Tier C - Integration] dev_config models remove refuses deleting an alias referenced by review.providers and rejects invalid CLI flags atomically
Given a temporary repository with custom alias "custom-claude" in global models referenced by global review.providers.claude.model
When dev_config.py runs "models remove custom-claude --scope global"
Then the command exits 1 with an error citing "review.providers.claude.model" and leaves global personas.json unchanged
And running "review set ollama --model gemma4 --host ftp://bad-host" or "limits --principal-review 0" exits 1 without corrupting or partially writing personas.json
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_dev_config_cli.py::test_urc_hp_02_limits_subcommand_global_and_project` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_dev_config_cli.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_agy_dispatch.py tests/test_fpg_set_provider_model_profile.py tests/test_fpg_agy_profile_pool.py tests/test_trc_persona_limits.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/dev_config.py scripts/agy_dispatch.py tests/test_urc_dev_config_cli.py && ruff format --check scripts/dev_config.py scripts/agy_dispatch.py tests/test_urc_dev_config_cli.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/dev_config.py scripts/agy_dispatch.py tests/test_urc_dev_config_cli.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_dev_config_cli.py --junitxml=build/test-results/task_02.xml` | exit 0; results build/test-results/task_02.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`scripts/dev_config.py` `L119-L134`, `L224-L300`, `L429-L470`, `L1412-L1728`; `scripts/agy_dispatch.py` `L126-L143`)**: Existing `_load_quota_thresholds`, `cmd_status`, `_find_alias_references`, `_build_parser`, `_dispatch_args`, and `agy_dispatch._load_thresholds`.
- **New contract (`scripts/dev_config.py`)**:
  - `limits [--json]` | `limits [--task-review N] [--fix N] [--principal-review N] [--cross-model-review N] [--scope global|project]` | `limits reset [task|fix|principal|cross-model|all] [--scope global|project]`.
  - `review status [--json]` | `review priority PROVIDER_LIST... [--scope global|project]` (supports comma-separated or multi-token provider names) | `review set PROVIDER --model M [--effort E] [--host URL] [--scope global|project]` | `review thresholds [--5h F] [--7d F] [--kiro-frac F] [--kiro-credits N] [--argon F] [--scope global|project]` | `review reset [priority|providers|PROVIDER|thresholds|all] [--scope global|project]`.
  - `status [--json]` preserves `task_review_limits` (`max_task_review_passes`, `max_fix_passes`) and adds `review_limits` (all 4 caps + `sources`) and `review` (`provider_priority`, `providers`, `quota_thresholds`, `last_used_provider`, `sources`).
  - `_find_alias_references(cfg, alias)` checks `review.providers.<cli>.model == alias` and appends `f"review.providers.{cli}.model"`.
  - `_load_quota_thresholds(project_root, review_mod=None, *, real_home=None)` in `dev_config.py` and `_load_thresholds(project_root, *, real_home=None)` in `agy_dispatch.py` delegate to `_pc.resolve_review_config(project_root, real_home=real_home).quota_thresholds` (preserving compatibility with existing call sites that pass `review_mod`).
  - Writing to `--scope global` checks `.agents/config/personas.json` for overlapping keys and prints a masking warning to `sys.stderr` without failing.

## Definition of Done

- [ ] `scripts/dev_config.py` implements `limits` (read/set/reset), `review` (`status`/`priority`/`set`/`thresholds`/`reset`), updated `status [--json]`, global-masked-by-project warnings, and `models remove` protection for `review.providers.*` (V2, V5)
- [ ] `scripts/dev_config.py` and `scripts/agy_dispatch.py` resolve `quota_thresholds` via `persona_config.resolve_review_config()` (V2, V3, V5)
- [ ] All 6 assigned scenarios (`URC-HP-02`, `URC-HP-03`, `URC-EC-03`, `URC-ST-01`, `URC-ST-02`, `URC-FR-02`) pass in `tests/test_urc_dev_config_cli.py` with JUnit XML written to `build/test-results/task_02.xml` (V2, V5)
- [ ] Downstream `agy_dispatch`, `set_provider_model_profile`, `agy_profile_pool`, and `persona_limits` regression suites pass without regressions (V3)
- [ ] `ruff check`, `ruff format --check`, and `mypy` pass across all Allowed files (V4)

## Dependencies & Blockers

- Blocked by [Task 01](task_01_persona_review_config_schema_and_resolver.md) (runs in Wave 2 in parallel with Task 03).

## References & Rollback

- Reference HLD: [unified_review_config.md](unified_review_config.md)
- Rollback: Revert changes to `scripts/dev_config.py` and `scripts/agy_dispatch.py`, and delete `tests/test_urc_dev_config_cli.py`.
