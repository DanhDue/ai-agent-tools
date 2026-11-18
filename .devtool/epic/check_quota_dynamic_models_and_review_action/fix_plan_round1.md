# Cross-Model Review Fix Plan — Round 1

- **Epic**: `check_quota_dynamic_models_and_review_action`
- **Round**: 1
- **Verdict**: `PASS` (`0 Critical`, `0 Important`, `4 Minor`)
- **Auto-Triage Gate**: `AUTO_PASS_FINAL_MINOR_SWEEP`
- **Allowed Remediation Files**:
  - `skills/check-tasks/resources/scripts/tasks_server.py`
  - `scripts/agy_quota.py`
  - `tests/test_cqra_review_action_e2e.py`
  - `tests/test_cqra_quota_discovery.py`
  - `.devtool/epic/check_quota_dynamic_models_and_review_action/review_results.md`

## Summary Matrix

| # | Severity | Location | Assessment | Planned Action |
|---|----------|----------|------------|----------------|
| 1 | Minor | `skills/check-tasks/resources/scripts/tasks_server.py:1109` | Valid (`fix_plan` fallback leaks into `principal_review.md` findings) | fix |
| 2 | Minor | `scripts/agy_quota.py:3077` | Non-blocking Minor — skip (shim required by untouched `tests/test_agy_quota.py` mocks) | none |
| 3 | Minor | `skills/dev-implementation/resources/scripts/run_external_review.py:2440` | Design-locked Minor — skip (last-marker rule frozen in HLD & `Decisions Already Made`) | none |
| 4 | Minor | `scripts/agy_quota.py:3764` | Valid (cold/stale cache triggers redundant 2nd `agy models` call on post-ping refresh) | fix |

## Detailed Findings Analysis & Surgical Plan

### Finding #1

- **Design Anchor:** Epic HLD (`check_quota_dynamic_models_and_review_action.en.md`, `Part B Review Proposed Action Extraction Flow`, `Module Contracts #5`, and `Spec Errata [SE-03]`), Design Spec (`2026-11-18-check-quota-dynamic-models-and-review-action-design.en.md` §1.2 & §4.3), and Task 05 (`task_05_review_action_parser_ui_and_regression.md` `Decisions Already Made`). `fix_plan_round<N>.md` / `fix_plan.md` is a Stage 3 Cross-Model Review artefact paired with `review_results.md`, while expected `fix_plan_round<round>.md` and `fix_plan.md` paths remain unconditionally registered in `watch_paths` per `[SE-03]`.
- **Evidence:** Confirmed in `skills/check-tasks/resources/scripts/tasks_server.py:1109-1129`. `parse_review_results()` sets `result["kind"] = "principal"` when parsing `principal_review.md` (`L937-L938`, or via `- **Kind**:` at `L1039-L1041`), but `L1109` (`if any(not f["proposed_action"] for f in findings):`) executes `_parse_fix_plan_actions(...)` unconditionally for every review kind. When an epic directory contains both `principal_review.md` (with a Round `N` finding lacking an inline `Proposed:` clause) and Stage 3 `fix_plan_round<N>.md`, Principal Review finding `#K` erroneously inherits the cross-model code fix action for `#K`.
- **Proposed Action:** `fix` — Apply a surgical kind guard in `skills/check-tasks/resources/scripts/tasks_server.py` and add a regression test in `tests/test_cqra_review_action_e2e.py`:
  1. In `skills/check-tasks/resources/scripts/tasks_server.py:1109`, guard the `fix_plan` fallback block so it runs only when `result` is not a Principal Review (`if str(result.get("kind") or "").strip().lower() != "principal" and any(not f["proposed_action"] for f in findings):`), while keeping the unconditional `watch_paths` registration (`L1154-L1163`) intact.
  2. In `tests/test_cqra_review_action_e2e.py`, add `test_principal_review_ignores_cross_model_fix_plan_fallback(tmp_path: Path) -> None` creating an epic directory with `principal_review.md` (Round 1 `#1` without inline proposal and `#2` with `. Proposed: clarify HLD`), `review_results.md` (Round 1 `#1` without inline proposal), and `fix_plan_round1.md` (`### Finding #1` -> `- **Proposed Action:** Apply cross-model fix`), asserting `parse_review_results(repo_dir, active_epic="...", kind="principal")` returns `proposed_action == ""` on `#1` and `"clarify HLD"` on `#2`, while `kind="cross-model"` returns `"Apply cross-model fix"` on `#1`.
  3. Record `fixed in <sha>` in the `Decision` column for row `#1` in `.devtool/epic/check_quota_dynamic_models_and_review_action/review_results.md`.

### Finding #2

- **Design Anchor:** Task 01 (`task_01_check_quota_dynamic_models_and_argon_mode.md` `Allowed files`, `Verification` `V3`/`V6`, and `Decisions Already Made`), which keeps `tests/test_agy_quota.py` outside epic `Allowed files` and mandates zero regressions across `tests/test_agy_quota.py` without external provider side effects.
- **Evidence:** Confirmed in `scripts/agy_quota.py:3055-3101` and `tests/test_agy_quota.py:133, 189, 221, 362, 380, 610, 703, 747, 822, 1014, 1195`. `load_cached_profiles()` (`L3055-L3068`) invokes live `fetch_claude_quota()`, `fetch_codex_quota()`, and `fetch_kiro_quota()` calls when provider entries are absent, so `_peek_cached_profile()` (`L3075-L3101`) reads `CACHED_PROFILES_DATA` and `get_dashboard_html_path()` directly in production. However, multiple legacy tests in `tests/test_agy_quota.py` (notably `test_argon_ping_triggered_when_max_7d` at `L221`, `test_format_profile_without_argon_group_has_argon_false` at `L362`, and `test_probe_blocked_profile_skips_argon_when_has_argon_false` at `L380`) inject isolated cache state exclusively via `patch("agy_quota.load_cached_profiles", return_value=mock_cached)` without patching `CACHED_PROFILES_DATA` or `get_dashboard_html_path`. Removing the `load_cached_profiles is not _ORIG_LOAD_CACHED_PROFILES` check without modifying `tests/test_agy_quota.py` (which is outside `Allowed files`) would break existing unit tests or re-introduce external provider fetches.
- **Proposed Action:** `none` — Non-blocking `Minor`; retain `_peek_cached_profile()` as-is to preserve backward compatibility with untouched `tests/test_agy_quota.py` monkeypatches, and leave the `Decision` cell for row `#2` blank in `review_results.md`.

### Finding #3

- **Design Anchor:** Epic HLD (`check_quota_dynamic_models_and_review_action.en.md` `Module Contracts #4 & #5`), Design Spec (`2026-11-18-check-quota-dynamic-models-and-review-action-design.en.md` §4.3), BDD Scenarios `CQRA-EC-03` & `CQRA-EC-04` (`bdd_scenarios.en.md`), Task 03 `Decisions Already Made`, and Task 05 `Decisions Already Made`.
- **Evidence:** Confirmed in `skills/dev-implementation/resources/scripts/run_external_review.py:2440-2456` and `skills/check-tasks/resources/scripts/tasks_server.py:527-552`. Both modules implement verbatim the explicitly frozen rule in `Decisions Already Made`: mask inline backtick code spans index-for-index and split on the **last** match of `(?:^|(?:[.;—]|\n)\s*)\b(?:Proposed(?:\s+action)?|Fix|Suggestion|Đề xuất):\s*` outside code spans. Round 1 already achieved `Verdict: PASS` (`0 Critical`, `0 Important`, `AUTO_PASS_FINAL_MINOR_SWEEP`), HLD/Spec files are outside Stage 3 `Allowed files`, and skipping an optional `Minor` Spec-Erratum suggestion violates zero contracts.
- **Proposed Action:** `none` — Design-locked `Minor` (`skip`); keep the frozen last-marker rule in `run_external_review.py` and `tasks_server.py` unchanged, do not edit HLD/Spec documents, and leave the `Decision` cell for row `#3` blank in `review_results.md`.

### Finding #4

- **Design Anchor:** Epic HLD (`check_quota_dynamic_models_and_review_action.en.md` `Part A Hybrid Model Discovery and Argon Classification Flow`), Design Spec (`2026-11-18-check-quota-dynamic-models-and-review-action-design.en.md` §3.1), BDD Scenario `CQRA-ST-01`, and Task 01 (`task_01_check_quota_dynamic_models_and_argon_mode.md` `Requirement Analysis` #1 & `Decisions Already Made`).
- **Evidence:** Confirmed in `scripts/agy_quota.py:1358-1365` and `L3543, L3706-L3711, L3764-L3768`. During `execute_ping_profile(profile)`, `live_q = fetch_quota_for_profile(profile)` (`L3543`, `batch_mode=False`) already runs `agy models` once and populates `availableModels`, `modelCatalog`, `modelsFetchedAt`, and `groupDescSig` in `live_q`, without writing to `CACHED_PROFILES_DATA` / HTML before pinging. At `L3764`, `post_q = fetch_quota_for_profile(profile, batch_mode=True)` looks up `cached_entry = _peek_cached_profile(profile)` (`L1358`), which still holds the pre-probe cold or stale cache entry; `_is_models_cache_warm(cached_entry, group_desc_sig)` returns `False` and spawns a redundant second `agy models` subprocess.
- **Proposed Action:** `fix` — Pass `live_q`'s discovered model metadata in-memory into the post-ping refresh and formatting path in `scripts/agy_quota.py` and add a unit regression test in `tests/test_cqra_quota_discovery.py`:
  1. In `scripts/agy_quota.py:1270-1274, 1358`, add optional keyword parameter `cached_override: dict | None = None` to `fetch_quota_for_profile(...)`, merging it into a shallow copy of `_peek_cached_profile(profile)` (`cached_entry = dict(_peek_cached_profile(profile)); if isinstance(cached_override, dict): cached_entry.update(cached_override)`). Passing `cached_override` as an optional keyword argument preserves full compatibility with all `unittest.mock.patch("agy_quota.fetch_quota_for_profile", ...)` mocks in `tests/test_agy_quota.py` and `lambda p, **_kw:` in `tests/test_cqra_quota_discovery.py:721`.
  2. In `scripts/agy_quota.py:3763-3768` (`execute_ping_profile`), construct an in-memory `seed_model_meta` dict from `live_q` (and `available_models` when discovered at `L3707-L3711`) carrying `availableModels`, `modelCatalog`, `modelsFetchedAt` (defaulting to current UTC ISO timestamp when `available_models` was discovered via `_discover_profile_models` and `live_q` lacked `modelsFetchedAt`), and `groupDescSig` (plus `groupModels` / `capabilities` when present in `live_q`). Pass `cached_override=seed_model_meta or None` into `fetch_quota_for_profile(profile, batch_mode=True, cached_override=seed_model_meta or None)`, and copy any missing `("availableModels", "modelCatalog", "modelsFetchedAt", "groupDescSig")` keys from `seed_model_meta` onto a shallow copy of `post_q` before calling `format_profile_for_dashboard(profile, post_q_merged)` and `update_cached_profile(profile, post_quota_formatted)`.
  3. In `tests/test_cqra_quota_discovery.py`, add `test_execute_ping_profile_cold_and_stale_cache_runs_agy_models_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ultra_models_stdout: str) -> None` verifying that with a cold (`{}`) and a >24h-stale `tmp_path`-isolated cache on an inactive profile requiring bucket activation, `execute_ping_profile("nguyenhieu000690")` invokes `agy models` (`len(cmd) >= 2 and cmd[1] == "models"`) at most once per `execute_ping_profile()` call (never a second time during the post-ping `batch_mode=True` refresh) and persists the fresh `modelCatalog`, `modelsFetchedAt`, and `groupDescSig` into `post_quota` and the isolated `tmp_path` HTML cache.
  4. Record `fixed in <sha>` in the `Decision` column for row `#4` in `.devtool/epic/check_quota_dynamic_models_and_review_action/review_results.md`.

## Verification & Convergence Checklist for Role 2.3 (`review-fixer`)

1. Run targeted new & existing suites: `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cqra_quota_discovery.py tests/test_cqra_review_action_e2e.py tests/test_agy_quota.py tests/test_check_tasks_server.py tests/test_cehm_history_aggregator.py`
2. Run formatting, lint, and typechecks:
   - `ruff format --check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py`
   - `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py`
   - `ruff check --select E9,F63,F7,F821,F841,B007,B904 scripts/agy_quota.py skills/check-tasks/resources/scripts/tasks_server.py`
   - `mypy skills/check-tasks/resources/scripts/tasks_server.py tests/test_cqra_quota_discovery.py tests/test_cqra_review_action_e2e.py`
3. Commit code + test fixes, record `fixed in <sha>` on rows `#1` and `#4` in `.devtool/epic/check_quota_dynamic_models_and_review_action/review_results.md` (leaving `Decision` cells blank on non-blocking skipped rows `#2` and `#3`), and verify `python3 skills/dev-implementation/resources/scripts/run_external_review.py check --epic-dir check_quota_dynamic_models_and_review_action` exits `0`.
4. Run full Gate 4 verification (`python3 -m pytest -q --tb=short --maxfail=3 tests` and `bash scripts/verify.sh`).
