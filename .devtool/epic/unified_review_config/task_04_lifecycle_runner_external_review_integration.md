---
id: "task_04_lifecycle_runner_external_review_integration"
status: "done"
priority: "high"
assignee: null
epic: "unified_review_config"
dueDate: null
created: "2026-11-28T03:12:00+07:00"
modified: "2026-11-27T21:29:48Z"
completedAt: "2026-11-27T21:29:48Z"
labels: ["architecture", "dev-lifecycle", "dev-config"]
order: "a04"
review_tier: "full"
---

# Task 04: Wire lifecycle_runner.py to Layered External Review Caps and Shared provider_priority

Epic: [unified_review_config](unified_review_config.md)

## Requirement Analysis

Update `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`RunnerConfig` and `LifecycleRunner`) so autonomous Stage 2 Principal Review and Stage 3 Cross-Model Review read their separate round caps (`max_principal_review_passes` and `max_cross_model_review_passes`) and shared layered `provider_priority` from `persona_config` when explicit CLI/runner overrides are not supplied, while preserving backward compatibility for callers passing `RunnerConfig(max_review_rounds=N)` or explicit `provider_priority`.

## Files

Allowed files:
- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`
- `tests/test_urc_lifecycle_runner_review_config.py` (new)

Read-only context:
- `.devtool/epic/unified_review_config/unified_review_config.md`
- `.devtool/epic/unified_review_config/bdd_scenarios.md`
- `scripts/persona_config.py`
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `tests/test_lifecycle_runner.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development` and `d3nexus:python-quality-check`.
- Mirror `_resolve_task_review_bounds()` (`L1762-L1773`) with `_resolve_external_review_bounds(stage)` and `_resolve_review_provider_priority()` so all four pass caps and review priority follow the same `real_home`-aware resolution path.
- Preserve exact backward compatibility for existing tests constructing `RunnerConfig(max_review_rounds=...)` by treating explicit `max_review_rounds` as an override when per-stage overrides (`max_principal_review_rounds` / `max_cross_model_review_rounds`) are `None`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`L274-L295`, `L1762-L1775`, `L2382-L2505`, `L3820-L3960`): `RunnerConfig` (`max_review_rounds: int | None = None`, `max_principal_review_rounds: int | None = None`, `max_cross_model_review_rounds: int | None = None`), `LifecycleRunner._resolve_external_review_bounds(stage)`, `LifecycleRunner._resolve_review_provider_priority()`, `evaluate_circuit_breakers()`, `step_principal_review()`, `step_cross_model_review()`, CLI `--max-rounds` parser wiring.
  - `tests/test_urc_lifecycle_runner_review_config.py` (new): unit and integration tests covering `URC-HP-05`, `URC-ST-04`, `URC-AR-03`.
- **Downstream Callers**: `tests/test_lifecycle_runner.py`, `tests/test_ohk_revise_and_replay.py`, `tests/test_tto_docs_and_slimming.py`.
- **Cross-Platform Bridges**: None (kit Python orchestrator).
- **Target Coverage Threshold**: >= 90% on newly added `LifecycleRunner` review resolution helpers and circuit-breaker round cap checks.

### BDD SCENARIOS

Covers: URC-HP-05, URC-ST-04, URC-AR-03

```gherkin
Scenario: [URC-HP-05] [Tier C - Integration] LifecycleRunner honors separate principal and cross-model round caps and layered provider_priority
Given a temporary repository with "$REAL_HOME/.d3nexus/personas.json" setting max_principal_review_passes=2, max_cross_model_review_passes=4, and review.provider_priority=["codex", "claude", "kiro", "agy"]
When LifecycleRunner initializes with RunnerConfig leaving max_review_rounds, max_principal_review_rounds, max_cross_model_review_rounds, and provider_priority unset
Then _resolve_external_review_bounds("principal") returns 2 and _resolve_external_review_bounds("code") returns 4
And _resolve_review_provider_priority() returns ["codex", "claude", "kiro", "agy"]

Scenario: [URC-ST-04] [Tier C - Integration] Explicit RunnerConfig overrides take precedence over global and project persona_config limits
Given a temporary repository with project personas.json setting max_principal_review_passes=2, max_cross_model_review_passes=4, and review.provider_priority=["codex", "claude"]
When LifecycleRunner is constructed with RunnerConfig(max_principal_review_rounds=1, max_cross_model_review_rounds=5, provider_priority=["kiro", "agy"])
Then _resolve_external_review_bounds("principal") returns 1, _resolve_external_review_bounds("code") returns 5, and _resolve_review_provider_priority() returns ["kiro", "agy"]
And constructing RunnerConfig(max_review_rounds=6) overrides both principal and code bounds to 6 for legacy caller compatibility

Scenario: [URC-AR-03] [Tier C - Integration] LifecycleRunner isolates Principal Review cap from Cross-Model Review cap during execution
Given a temporary repository where global personas.json sets max_principal_review_passes=1 and max_cross_model_review_passes=3
When LifecycleRunner evaluates circuit-breaker round exhaustion for stage "principal" at round 1 and stage "code" at round 1 with Critical findings present
Then stage "principal" triggers "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)" at round 1
And stage "code" does not trigger max-rounds halt at round 1 because its cap is 3
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_lifecycle_runner_review_config.py::test_urc_hp_05_runner_resolves_separate_caps_and_priority` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_lifecycle_runner_review_config.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_lifecycle_runner.py tests/test_ohk_revise_and_replay.py tests/test_tto_docs_and_slimming.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_urc_lifecycle_runner_review_config.py && ruff format --check skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_urc_lifecycle_runner_review_config.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_urc_lifecycle_runner_review_config.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_urc_lifecycle_runner_review_config.py --junitxml=build/test-results/task_04.xml` | exit 0; results build/test-results/task_04.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` `L274-L295`, `L1762-L1773`, `L2382-L2505`, `L3820-L3960`)**: Existing `RunnerConfig.max_review_rounds`, `RunnerConfig.provider_priority`, `_resolve_task_review_bounds()`, `evaluate_circuit_breakers()`, `step_principal_review()`, and `step_cross_model_review()`.
- **New contract (`lifecycle_runner.py`)**:
  - `RunnerConfig` fields: `max_review_rounds: int | None = None`, `max_principal_review_rounds: int | None = None`, `max_cross_model_review_rounds: int | None = None`, `provider_priority: list[str] | None = None`.
  - `_resolve_external_review_bounds(self, stage: str) -> int`:
    - If `stage == "principal"`: check `self.config.max_principal_review_rounds` -> `self.config.max_review_rounds` -> `pc.resolve_review_limits(self.root, real_home=self.config.real_home).max_principal_review_passes`.
    - Otherwise (`"code"`, `"cross_model"`, `"epic"`): check `self.config.max_cross_model_review_rounds` -> `self.config.max_review_rounds` -> `pc.resolve_review_limits(self.root, real_home=self.config.real_home).max_cross_model_review_passes`.
  - `_resolve_review_provider_priority(self) -> list[str]`: returns `list(self.config.provider_priority)` when explicitly set, else `list(pc.resolve_review_config(self.root, real_home=self.config.real_home).provider_priority)`.
  - `evaluate_circuit_breakers(stage, round_num, ...)` uses `self._resolve_external_review_bounds(stage)` instead of hardcoded `self.config.max_review_rounds`.
  - `step_principal_review()` loops up to `self._resolve_external_review_bounds("principal")` and passes `--max-rounds` + `--provider-priority` resolved via `_resolve_review_provider_priority()`; `step_cross_model_review()` loops up to `self._resolve_external_review_bounds("code")` similarly.

## Definition of Done

- [x] `RunnerConfig` and `LifecycleRunner` in `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` resolve separate principal and cross-model review round caps and layered `provider_priority` from `persona_config` while honoring explicit overrides (V2, V5) — Verified PASS (6 passed in `tests/test_urc_lifecycle_runner_review_config.py`)
- [x] All 3 assigned scenarios (`URC-HP-05`, `URC-ST-04`, `URC-AR-03`) pass in `tests/test_urc_lifecycle_runner_review_config.py` with JUnit XML written to `build/test-results/task_04.xml` (V2, V5) — Verified PASS (3/3 BDD traceability covered; JUnit XML fresh)
- [x] Existing `tests/test_lifecycle_runner.py` regression suite passes without regressions (V3) — Verified PASS (50 passed)
- [x] `ruff check`, `ruff format --check`, and `mypy` pass across all Allowed files (V4) — Verified PASS (0 ruff/format/mypy issues)

## Dependencies & Blockers

- Blocked by [Task 01](task_01_persona_review_config_schema_and_resolver.md) and [Task 03](task_03_external_review_layered_config_and_runtime_state.md).

## References & Rollback

- Reference HLD: [unified_review_config.md](unified_review_config.md)
- Rollback: Revert changes to `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` and delete `tests/test_urc_lifecycle_runner_review_config.py`.
