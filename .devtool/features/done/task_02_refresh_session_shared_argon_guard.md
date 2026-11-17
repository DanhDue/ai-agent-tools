---
id: "task_02_refresh_session_shared_argon_guard"
status: "done"
priority: "medium"
assignee: null
epic: "check_quota_dynamic_models_and_review_action"
dueDate: null
created: "2026-11-18T03:11:00Z"
modified: "2026-11-17T23:34:10Z"
completedAt: "2026-11-17T23:34:10Z"
labels: ["refresh-session", "concurrency", "architecture"]
order: "a2"
review_tier: "full"
---

# Task 2: Refresh-Session Shared-Pool Argon Ping Suppression Guard

Epic: [check_quota_dynamic_models_and_review_action](../../epic/check_quota_dynamic_models_and_review_action/check_quota_dynamic_models_and_review_action.en.md)

## Requirement Analysis

Update `skills/refresh-session/resources/scripts/refresh_session.py` so `Argon 7D` standalone pings run exclusively for accounts with a separate Argon quota bucket and are suppressed when Argon shares the active `"Gemini Models"` pool (`argonMode == "shared_gemini"`):

1. **Extract Usage Descriptions & Classify `argonMode` (`_extract_usage_buckets`, `check_profile_has_argon`)**:
   - Extend `_extract_usage_buckets(cmd_data)` (`L1327-L1358`) to inspect each `/usage` group's `description` alongside group names (`has_dedicated_argon_group`, `gemini_group_active`, normalized model tokens).
   - Determine `argonMode` (`"separate"` when a dedicated Argon `/usage` group exists; `"shared_gemini"` when no dedicated Argon group exists yet Argon models/keywords exist in `"Gemini Models"` description or `available_models`; `"none"` otherwise).
   - Update `check_profile_has_argon(profile)` (`L1306-L1324`, reading `_DASHBOARD_HTML_CANDIDATES` `L531`) to return `bool` gated on cached `capabilities.argonMode == "separate"` (or, for legacy caches lacking `capabilities.argonMode`, when `argonWeekly.sharedPool != True` and `hasArgon and not argonWeekly.unavailable`); return `False` for `"shared_gemini"`, `"none"`, or corrupt/missing entries.
2. **Ping Suppression Guard in `ping_profile()` (`L1486-L1656`)**:
   - Before queuing `_run_isolated_agy_model_ping` for `"Argon 7D"`, verify `argonMode == "separate"` and the dedicated Argon bucket is not already activated (`is_bucket_activated`).
   - In the non-live fallback (`L1581-L1583`), consult `_DASHBOARD_HTML_CANDIDATES` cached state alongside `check_profile_has_argon()` so `"shared_gemini"` profiles suppress `Argon 7D` pings even when `available_models` includes `"argon"`.
   - When `argonMode == "shared_gemini"` and `"Gemini Models"` is active (or covered by the Gemini ping), skip standalone `Argon 7D` pings cleanly without emitting false Argon failure status.
   - When `_probe_profile_usage_and_models()` (`L1371-L1423`) yields malformed/empty data (`{}` or `None`), degrade softly without raising unhandled exceptions or firing spurious Argon pings.
3. **Unit Suite (`tests/test_cqra_refresh_session_argon.py`)**:
   - Cover scenarios `CQRA-ST-02` and `CQRA-FR-02`.

## Files

Allowed files:
- `skills/refresh-session/resources/scripts/refresh_session.py`
- `tests/test_cqra_refresh_session_argon.py` (new)

Read-only context:
- `.devtool/epic/check_quota_dynamic_models_and_review_action/check_quota_dynamic_models_and_review_action.en.md` — Epic HLD & Ping Guard Contract
- `.devtool/epic/check_quota_dynamic_models_and_review_action/bdd_scenarios.en.md` — Canonical BDD Scenarios

## Design Rationale

Aligning `refresh_session.py` with `agy_quota.py`'s `argonMode` distinction prevents background scheduled/manual session pings from wasting Argon requests or recording bogus failures on `g1-ultra-tier` accounts whose Argon already rides on the active `"Gemini Models"` pool. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/refresh-session/resources/scripts/refresh_session.py`: `parse_agy_models_output` (L78-L92), `select_model_from_candidates` (L95-L106), `is_bucket_activated` (L109-L145), `_DASHBOARD_HTML_CANDIDATES` (L531), `check_profile_has_argon` (L1306-L1324), `_extract_usage_buckets` (L1327-L1358), `_probe_profile_usage_and_models` (L1371-L1423), `ping_profile` (L1486-L1656; fallback L1581-L1583)
  - `tests/test_cqra_refresh_session_argon.py`: new unit test suite
- **Downstream Callers**: `scripts/agy_quota.py` (`_load_refresh_session_module`), `skills/refresh-session/resources/scripts/test_refresh_session.py`, `tests/test_agy_quota.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of `shared_gemini` suppression, `separate` activation, and corrupt probe fallback branches.

### BDD SCENARIOS

Covers: CQRA-ST-02, CQRA-FR-02

```gherkin
Scenario: [CQRA-ST-02] [Tier A - Unit] Refresh-session ping suppresses Argon 7D ping on shared_gemini while preserving ping on inactive separate Argon
Given `refresh_session.py` inspecting two authenticated accounts after `/usage`: `"ultra_shared"` (`argonMode == "shared_gemini"` with active `"Gemini Models"` bucket) and `"pro_sep"` (`argonMode == "separate"` with inactive dedicated `"Gemini 4 Argon"` bucket)
When `ping_profile()` evaluates ping candidates for both profiles with mocked isolated CLI execution
Then `"ultra_shared"` triggers 0 `Argon 7D` model pings and records no spurious Argon failure
And `"pro_sep"` dispatches exactly 1 `Argon 7D` ping against `"gemini-argon"` candidate

Scenario: [CQRA-FR-02] [Tier A - Unit] Shared-gemini cache fallback and corrupted usage probes degrade safely with zero Argon pings
Given `_DASHBOARD_HTML_CANDIDATES` patched to a temporary HTML file containing a `shared_gemini` cache entry for `"shared_cached"` (`hasArgon: true`, `capabilities.argonMode: "shared_gemini"`, `argonWeekly: {unavailable: false, sharedPool: true}`) and a missing entry for `"corrupt_probe"`, alongside a mocked `_probe_profile_usage_and_models()` returning empty groups (`{}`) and malformed `available_models` (`None` / empty output)
When `refresh_session.py` (`check_profile_has_argon()` and `ping_profile()`) executes for both profiles
Then `check_profile_has_argon("shared_cached")` and `check_profile_has_argon("corrupt_probe")` both return `False`
And `ping_profile()` completes cleanly with `0` spurious `Argon 7D` pings and zero unhandled exceptions
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cqra_refresh_session_argon.py::test_cqra_st_02_suppresses_argon_ping_for_shared_gemini` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cqra_refresh_session_argon.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_cqra_refresh_session_argon.py && ruff check --select E9,F63,F7,F821,F841,B007,B904 skills/refresh-session/resources/scripts/refresh_session.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && mypy tests/test_cqra_refresh_session_argon.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/cqra_task_02.xml tests/test_cqra_refresh_session_argon.py tests/test_agy_quota.py` | exit 0; results build/test-results/cqra_task_02.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Shared-pool detection triggers `argonMode == "shared_gemini"` only when NO dedicated Argon group exists in `/usage` and Argon capability is indicated by Gemini group description or discovered model catalog.
- Dedicated `Argon 7D` ping only fires when `argonMode == "separate"` and `!is_bucket_activated(...)` on the separate Argon weekly bucket.
- Cached-fallback gating in `check_profile_has_argon()` (`L1306-L1324`) and `ping_profile()` (`L1581-L1583`) gates standalone Argon pings on cached `capabilities.argonMode == "separate"` (or legacy cache lacking `capabilities.argonMode` with `argonWeekly.sharedPool != True` and `hasArgon and not unavailable`); `"shared_gemini"` cache entries yield `False` and dispatch `0` `Argon 7D` pings even if `available_models` includes `"argon"`.
- `is_bucket_activated()` (`L109-L145`) retains its existing 1-arg or `usage_buckets` signature compatibility for `scripts/agy_quota.py` and existing `test_refresh_session.py` callers.

## Definition of Done

- Scenarios CQRA-ST-02 and CQRA-FR-02 pass cleanly. (V2, V6)
- Existing `test_refresh_session.py` and `test_agy_quota.py` pass without regressions. (V3, V6)
- Ruff lint and mypy typecheck pass cleanly. (V4, V5)

## Dependencies & Blockers

None.

Downstream dependents (blocked by Task 2): `task_05`.

## References & Rollback

- [Epic HLD](../../epic/check_quota_dynamic_models_and_review_action/check_quota_dynamic_models_and_review_action.en.md)
- **Rollback**: Revert task commit to restore `skills/refresh-session/resources/scripts/refresh_session.py`.
