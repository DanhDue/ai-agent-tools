---
id: "task_01_persona_config_task_review_limits"
status: "todo"
completedAt: null
priority: "high"
assignee: null
epic: "review_cap_and_risk_triage"
dueDate: null
created: "2026-11-18T06:25:00Z"
modified: "2026-11-18T06:25:00Z"
labels: ["config", "cli", "contract"]
order: "a1"
review_tier: "full"
---

# Task 1: Persona Config Review and Fix Pass Limits

Epic: [review_cap_and_risk_triage](review_cap_and_risk_triage.md)

## Requirement Analysis

Add layered configuration and validation for task-level review and fix pass bounds (`max_task_review_passes = 2`, `max_fix_passes = 1`) across kit defaults, project persona configuration, `persona_config.py`, and `dev_config.py` (Spec §4; HLD Module Contracts §1):

1. **Kit Defaults (`scripts/personas.default.json`)**: Add top-level keys `"max_task_review_passes": 2` and `"max_fix_passes": 1`.
2. **Project Config (`.agents/config/personas.json`)**: Create `.agents/config/personas.json` with `{"schema_version": 1, "max_task_review_passes": 2, "max_fix_passes": 1}` so `ai-agent-tools` explicitly declares the project-level cap while inheriting model presets from kit/global layers.
3. **Schema Validation & Resolver (`scripts/persona_config.py`)**:
   - Add `DEFAULT_MAX_TASK_REVIEW_PASSES: int = 2` and `DEFAULT_MAX_FIX_PASSES: int = 1`.
   - Extend `_ALLOWED_TOP_KEYS` with `"max_task_review_passes"` and `"max_fix_passes"`.
   - Validate in `_validate_policy_and_low_quota(cfg)` (and layer-level validation if present) that `"max_task_review_passes"` has exact type `int` (`type(v) is int`, rejecting `bool` and `str`) with value `>= 1`, and `"max_fix_passes"` has exact type `int` with value `>= 0`; raise `PersonaConfigError` naming the offending key on violation.
   - Implement `resolve_task_review_limits(project_root: Path, *, real_home: Path | str | None = None) -> tuple[int, int]` returning `(max_task_review_passes, max_fix_passes)` from `load_persona_config(project_root, real_home=real_home)` (with fallback defaults `(2, 1)` when keys are absent from a minimal dict).
4. **CLI Exposure (`scripts/dev_config.py`)**: Include `"task_review_limits": {"max_task_review_passes": max_rev, "max_fix_passes": max_fix}` in `cmd_status` JSON output (`status --json`) and human-readable status summary.
5. **Parametrized Unit & Integration Tests (`tests/test_trc_persona_limits.py`)**: Cover `TRC-HP-01`, `TRC-EC-01` (using `@pytest.mark.parametrize` across `0`, `-1`, `True`, `"2"`, `False`), and `TRC-FR-01` under isolated `tmp_path` `REAL_HOME` and project directories.

## Files

Allowed files:
- `scripts/personas.default.json`
- `.agents/config/personas.json` (new)
- `scripts/persona_config.py`
- `scripts/dev_config.py`
- `tests/test_trc_persona_limits.py` (new)

Read-only context:
- `.devtool/epic/review_cap_and_risk_triage/review_cap_and_risk_triage.md` — HLD Module Contracts §1
- `.devtool/epic/review_cap_and_risk_triage/2026-11-18-task-review-cap-and-risk-triage-design.md` — Spec §4
- `tests/test_fpg_persona_config.py` — existing `persona_config` test fixtures and assertions

## Design Rationale

Keeping `max_task_review_passes` and `max_fix_passes` in the existing `kit -> global -> project` `personas.json` hierarchy avoids introducing a second configuration file while ensuring both `manage_worker_pool.py` and `lifecycle_runner.py` read a single validated source of truth. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/persona_config.py`: `DEFAULT_TURN_BUDGET` / `_ALLOWED_TOP_KEYS` `(L24-L43)`, `_validate_policy_and_low_quota` `(L312-L340)`, `validate_merged_config` `(L341-L356)`
  - `scripts/dev_config.py`: `cmd_status` `(L224-L291)`
  - `scripts/personas.default.json`: top-level policy keys `(L160-L166)`
- **Downstream Callers**: Task 3 (`manage_worker_pool.py`), Task 4 (`lifecycle_runner.py`), `tests/test_fpg_persona_config.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% branch coverage of `resolve_task_review_limits` and validation error branches in `_validate_policy_and_low_quota`.

### BDD SCENARIOS

Covers: TRC-HP-01, TRC-EC-01, TRC-FR-01

```gherkin
Scenario: [TRC-HP-01] [Tier A - Unit] Layered persona configuration resolves default and overridden task review and fix pass limits
Given a temporary REAL_HOME and project root with no custom personas.json files
When "resolve_task_review_limits" and "dev_config.py status --json" run against the project root
Then "resolve_task_review_limits" returns "(2, 1)" matching "scripts/personas.default.json" and ".agents/config/personas.json"
And the status JSON includes "task_review_limits" equal to {"max_task_review_passes": 2, "max_fix_passes": 1}
When global ".d3nexus/personas.json" sets {"schema_version": 1, "max_task_review_passes": 3, "max_fix_passes": 2} and project ".agents/config/personas.json" sets {"schema_version": 1, "max_fix_passes": 1}
Then "resolve_task_review_limits" returns "(3, 1)" reflecting kit -> global -> project precedence

Scenario: [TRC-EC-01] [Tier A - Unit] Invalid or boolean task review limit values in personas.json raise PersonaConfigError
Given a temporary project root with kit defaults present
When ".agents/config/personas.json" sets any of {"max_task_review_passes": 0}, {"max_task_review_passes": -1}, {"max_task_review_passes": true}, {"max_task_review_passes": "2"}, {"max_fix_passes": -1}, or {"max_fix_passes": false}
Then loading or validating persona config raises "PersonaConfigError" naming the invalid key

Scenario: [TRC-FR-01] [Tier A - Unit] Missing optional persona config layers fall back to kit defaults while malformed JSON fails closed
Given a temporary project root with no ".agents/config/personas.json" and an empty temporary REAL_HOME
When "resolve_task_review_limits" runs
Then it returns "(2, 1)" without error
When ".agents/config/personas.json" contains truncated invalid JSON "{bad"
Then "resolve_task_review_limits" raises "PersonaConfigError" naming ".agents/config/personas.json"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_trc_persona_limits.py::test_trc_hp_01_layered_task_review_limits_and_status_json` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_trc_persona_limits.py tests/test_fpg_persona_config.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/persona_config.py scripts/dev_config.py tests/test_trc_persona_limits.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/persona_config.py scripts/dev_config.py tests/test_trc_persona_limits.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/trc_task_01.xml tests/test_trc_persona_limits.py tests/test_fpg_persona_config.py` | exit 0; results build/test-results/trc_task_01.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Source: `scripts/persona_config.py::_ALLOWED_TOP_KEYS` (`L33-L43`) whitelists top-level keys on every layer read in `_read_layer_json` (`L129-L150`), and `_validate_policy_and_low_quota` (`L312-L340`) checks `type(turns) is not int` so `bool` (`isinstance(True, int)`) is rejected.
- New contract: `DEFAULT_MAX_TASK_REVIEW_PASSES = 2` and `DEFAULT_MAX_FIX_PASSES = 1`. In `_validate_policy_and_low_quota(cfg)`, `max_rev = cfg.get("max_task_review_passes", DEFAULT_MAX_TASK_REVIEW_PASSES)` must satisfy `type(max_rev) is int and max_rev >= 1`, and `max_fix = cfg.get("max_fix_passes", DEFAULT_MAX_FIX_PASSES)` must satisfy `type(max_fix) is int and max_fix >= 0`; otherwise raise `PersonaConfigError` naming `"max_task_review_passes"` or `"max_fix_passes"`.
- New contract: `resolve_task_review_limits(project_root: Path, *, real_home: Path | str | None = None) -> tuple[int, int]` calls `load_persona_config(project_root, real_home=real_home)` and returns `(int(cfg.get("max_task_review_passes", DEFAULT_MAX_TASK_REVIEW_PASSES)), int(cfg.get("max_fix_passes", DEFAULT_MAX_FIX_PASSES)))`.
- New contract: `.agents/config/personas.json` in `ai-agent-tools` contains `{"schema_version": 1, "max_task_review_passes": 2, "max_fix_passes": 1}` so existing `ai-agent-tools` preset bindings from `personas.default.json` and `$REAL_HOME/.d3nexus/personas.json` remain unchanged.
- In `tests/test_trc_persona_limits.py`, import `persona_config` at module level and check `getattr(persona_config, "resolve_task_review_limits", None)` inside the test body so RED row `V1` fails with pytest assertion failure (`exit 1; contains "failed"`) rather than `ImportError` at collection time.

## Definition of Done

- `TRC-HP-01`, `TRC-EC-01`, and `TRC-FR-01` pass alongside all existing `tests/test_fpg_persona_config.py` tests. (V2, V5)
- `.agents/config/personas.json` and `scripts/personas.default.json` both declare `"max_task_review_passes": 2` and `"max_fix_passes": 1`. (V2, V5)
- `ruff check` and `mypy` pass with zero errors on modified and added files. (V3, V4)
- Config schema and `dev_config.py status` output are clear for Human Architect inspection. (Gate 5)

## Dependencies & Blockers

None.

Downstream dependents (blocked by Task 1): [Task 3](task_03_worker_pool_cap_snapshot_and_triage.md), [Task 4](task_04_runner_parity_and_acceptance.md).

## References & Rollback

- [Epic HLD](review_cap_and_risk_triage.md)
- **Rollback**: Revert `scripts/personas.default.json`, `scripts/persona_config.py`, and `scripts/dev_config.py`, and delete `.agents/config/personas.json` and `tests/test_trc_persona_limits.py`.
