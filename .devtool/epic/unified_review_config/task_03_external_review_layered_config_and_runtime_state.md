---
id: "task_03_external_review_layered_config_and_runtime_state"
status: "done"
priority: "high"
assignee: null
epic: "unified_review_config"
dueDate: null
created: "2026-11-28T03:12:00+07:00"
modified: "2026-11-27T21:16:52Z"
completedAt: "2026-11-27T21:16:52Z"
labels: ["architecture", "contract", "principal-review", "cross-model-review"]
order: "a03"
review_tier: "full"
---

# Task 03: Wire run_external_review.py to Layered Config, Per-Kind Caps, Dynamic Thresholds, and Runtime State Isolation

Epic: [unified_review_config](unified_review_config.md)

## Requirement Analysis

Wire `skills/dev-implementation/resources/scripts/run_external_review.py` to load external review settings from `scripts/persona_config.py` (resolved relative to the plugin install path so satellite repositories without `scripts/persona_config.py` work seamlessly), apply kind-specific default `max_rounds` (`max_principal_review_passes` for `--kind principal` and `max_cross_model_review_passes` for `--kind code`/`epic` when `--max-rounds` is omitted), pass resolved `quota_thresholds` into `evaluate_provider_quota()` and `select_provider_by_quota()`, isolate runtime `last_used_provider` in `.devtool/state/review_runtime.json`, and stop auto-seeding or rewriting `.devtool/review_config.json`. Update legacy auto-seeding assertions in `test_run_external_review.py` accordingly.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`
- `tests/test_tto_external_review.py`
- `tests/test_urc_external_review_integration.py` (new)

Read-only context:
- `.devtool/epic/unified_review_config/unified_review_config.md`
- `.devtool/epic/unified_review_config/bdd_scenarios.md`
- `scripts/persona_config.py`
- `scripts/personas.default.json`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development` and `d3nexus:python-quality-check`.
- Load `scripts/persona_config.py` via `importlib.util` from `Path(__file__).resolve().parents[4] / "scripts" / "persona_config.py"` so `run_external_review.py` never fails with `ImportError` when executed from an installed plugin inside a satellite repository.
- Isolate mutable runtime state (`last_used_provider`) in `.devtool/state/review_runtime.json` with atomic temp-file writes so `.devtool/review_config.json` is never auto-created or dirtied during reviews.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/run_external_review.py` (`L62-L245`, `L274-L367`, `L1860-L1885`, `L2265-L2315`, `L2725-L2765`, `L2950-L3060`): `REVIEW_RUNTIME_FILE`, `load_review_runtime()`, `save_review_runtime()`, `load_review_config()`, `update_sticky_review_config()`, `evaluate_provider_quota()`, `select_provider_by_quota()`, `resolve_review_settings()`, `resolve_effective_max_rounds()`, `--max-rounds` default `None` in CLI parser, `check()`, `triage()`, `status_cmd()`, `main()`.
  - `skills/dev-implementation/resources/scripts/test_run_external_review.py` (`L970-L1160`): update legacy auto-seeding and sticky overwrite assertions to verify read-only fallback and `.devtool/state/review_runtime.json` persistence.
  - `tests/test_urc_external_review_integration.py` (new): integration tests covering `URC-HP-04`, `URC-EC-04`, `URC-ST-03`, `URC-AR-02`, `URC-FR-03`.
- **Downstream Callers**: `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`, `scripts/dev_config.py`, `tests/test_tto_external_review.py`, `skills/dev-implementation/resources/scripts/test_run_external_review.py`.
- **Cross-Platform Bridges**: None (kit Python module).
- **Target Coverage Threshold**: >= 90% on modified review config/runtime/threshold functions in `run_external_review.py`.

### BDD SCENARIOS

Covers: URC-HP-04, URC-EC-04, URC-ST-03, URC-AR-02, URC-FR-03

```gherkin
Scenario: [URC-HP-04] [Tier C - Integration] run_external_review applies separate principal and cross-model pass limits and shared global provider_priority
Given a temporary repository with "$REAL_HOME/.d3nexus/personas.json" setting max_principal_review_passes=2, max_cross_model_review_passes=4, and review.provider_priority=["codex", "claude", "kiro", "agy"]
When run_external_review.resolve_effective_max_rounds runs for kind "principal" and kind "code" with cli_max_rounds=None
Then kind "principal" resolves to 2 rounds and kind "code" resolves to 4 rounds
And run_external_review.load_review_config returns provider_priority ["codex", "claude", "kiro", "agy"]
And passing explicit cli_max_rounds=5 overrides both kinds to 5

Scenario: [URC-EC-04] [Tier C - Integration] Custom layered quota_thresholds control select_provider_by_quota decisions in run_external_review
Given a temporary repository with "$REAL_HOME/.d3nexus/personas.json" setting review.quota_thresholds.5h_min_fraction=0.50 and review.provider_priority=["claude", "codex"]
And a stubbed quota fetcher reporting claude ACTIVE with 5H=0.35 (7D=0.80) and codex ACTIVE with 5H=0.70 (7D=0.80)
When run_external_review.resolve_review_settings runs with auto_quota=True
Then claude is skipped because 0.35 < 0.50 (resolved threshold, not hardcoded 0.15)
And codex is selected as the active reviewer

Scenario: [URC-ST-03] [Tier C - Integration] update_sticky_review_config persists last_used_provider to .devtool/state/review_runtime.json without mutating .devtool/review_config.json
Given a temporary repository containing a pre-existing ".devtool/review_config.json" with exact bytes B0
When run_external_review.load_review_config and run_external_review.update_sticky_review_config(root, "codex", "gpt-custom", "medium") execute
Then ".devtool/review_config.json" remains byte-identical to B0 (never auto-seeded or overwritten)
And ".devtool/state/review_runtime.json" records last_used_provider="codex"
And subsequent run_external_review.load_review_config returns last_used_provider="codex" while keeping configured provider models intact

Scenario: [URC-AR-02] [Tier C - Integration] run_external_review loads persona_config relative to its plugin install path when run inside a satellite repository
Given a temporary satellite repository containing no "scripts/persona_config.py" and an isolated fake REAL_HOME with global personas.json setting max_principal_review_passes=2 and review.provider_priority=["kiro", "claude"]
When run_external_review.py executes from its kit location with cwd set to the satellite repository
Then load_review_config and resolve_effective_max_rounds resolve the satellite repository's project layer plus fake REAL_HOME global layer cleanly without ImportError

Scenario: [URC-FR-03] [Tier C - Integration] Corrupted legacy .devtool/review_config.json and .devtool/state/review_runtime.json fall back cleanly without crashing external review
Given a temporary repository containing truncated invalid JSON in both ".devtool/review_config.json" and ".devtool/state/review_runtime.json"
When persona_config.resolve_review_config and run_external_review.load_review_config execute
Then neither raises JSONDecodeError
And configuration falls back cleanly to global/kit defaults with last_used_provider="claude"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_external_review_integration.py::test_urc_hp_04_per_kind_pass_limits_and_global_priority` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_external_review_integration.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 skills/dev-implementation/resources/scripts/test_run_external_review.py tests/test_tto_external_review.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py tests/test_tto_external_review.py tests/test_urc_external_review_integration.py && ruff format --check skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py tests/test_tto_external_review.py tests/test_urc_external_review_integration.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py tests/test_tto_external_review.py tests/test_urc_external_review_integration.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_external_review_integration.py --junitxml=build/test-results/task_03.xml` | exit 0; results build/test-results/task_03.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`skills/dev-implementation/resources/scripts/run_external_review.py` `L62-L245`, `L274-L367`, `L1860-L1885`, `L2265-L2315`, `L2725-L2765`, `L2950-L3060`)**: Existing `load_review_config`, `save_review_config`, `update_sticky_review_config`, `evaluate_provider_quota`, `select_provider_by_quota`, `resolve_review_settings`, and `--max-rounds` argument wiring.
- **New contract (`run_external_review.py`)**:
  - `REVIEW_RUNTIME_FILE = ".devtool/state/review_runtime.json"` stores `{"last_used_provider": "<cli>", "updated_at": "<iso-utc>"}` atomically via temp file + replace.
  - `load_review_config(root: Path, *, real_home: Path | str | None = None) -> dict[str, Any]` resolves via `persona_config.resolve_review_config(root, real_home=real_home)`, populates `provider_priority`, `quota_thresholds`, `max_rounds` (`max_cross_model_review_passes`), `max_principal_review_passes`, `max_cross_model_review_passes`, `providers` (with both `"effort"` and `"thinking_level"` populated from resolved binding for full caller compatibility, plus `"host"` on `ollama`), and `last_used_provider` (from `.devtool/state/review_runtime.json` else read-only `.devtool/review_config.json` else `"claude"`). NEVER writes `.devtool/review_config.json`.
  - `update_sticky_review_config(root, cli, model, thinking_level)` persists only `last_used_provider` into `.devtool/state/review_runtime.json`.
  - `resolve_effective_max_rounds(root: Path, kind: str, cli_max_rounds: int | None = None, *, real_home: Path | str | None = None) -> int`: returns `cli_max_rounds` when `cli_max_rounds is not None`, otherwise `resolve_review_config(...).max_rounds_for_kind(kind)`.
  - `evaluate_provider_quota(cli, quota_data, *, thresholds=None)` and `select_provider_by_quota(priority=None, fetcher=None, *, thresholds=None)` use `thresholds or QUOTA_THRESHOLDS`; `resolve_review_settings()` passes `thresholds=config.get("quota_thresholds")`.
  - Keep `save_review_config(root, config)` function exported for explicit test/tool callers, while removing all automatic calls from `load_review_config()` and `update_sticky_review_config()`.
  - In `run_external_review.py` CLI parser (`main()`), `--max-rounds` uses `default=None` and `run`/`check`/`triage`/`status_cmd` call `resolve_effective_max_rounds(root, args.kind, args.max_rounds)`.
  - Per `[SE-01]` (`tests/test_tto_external_review.py`): update `test_tto_st_01_load_review_config_migrates_legacy_and_preserves_custom` (`L493-L506`) to verify in-memory defaults without mutating untracked `.devtool/review_config.json` on disk (matching `URC-ST-03`), and reuse `sys.modules.get("run_external_review")` in `_load_external_review_module()` (`L37-L50`) so combined `V3` pytest runs preserve single module identity.

## Definition of Done

- [x] `run_external_review.py` loads layered config from `persona_config.py` relative to plugin install path, resolves kind-specific default `max_rounds`, applies resolved `quota_thresholds`, and isolates `last_used_provider` in `.devtool/state/review_runtime.json` without mutating `.devtool/review_config.json` (V2, V5) — PASS (exit 0)
- [x] All 5 assigned scenarios (`URC-HP-04`, `URC-EC-04`, `URC-ST-03`, `URC-AR-02`, `URC-FR-03`) pass in `tests/test_urc_external_review_integration.py` with JUnit XML written to `build/test-results/task_03.xml` (V2, V5) — PASS (5 passed; `build/test-results/task_03.xml` written)
- [x] Updated `test_run_external_review.py` and `tests/test_tto_external_review.py` regression suites pass without regressions (V3) — PASS (81 passed, 3 subtests passed)
- [x] `ruff check`, `ruff format --check`, and `mypy` pass across all Allowed files (V4) — PASS (exit 0)

## Dependencies & Blockers

- Blocked by [Task 01](task_01_persona_review_config_schema_and_resolver.md) (runs in Wave 2 in parallel with Task 02).

## References & Rollback

- Reference HLD: [unified_review_config.md](unified_review_config.md)
- Rollback: Revert changes to `skills/dev-implementation/resources/scripts/run_external_review.py` and `test_run_external_review.py`, and delete `tests/test_urc_external_review_integration.py`.
