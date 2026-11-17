---
id: "task_01_check_quota_dynamic_models_and_argon_mode"
status: "done"
priority: "high"
assignee: null
epic: "check_quota_dynamic_models_and_review_action"
dueDate: null
created: "2026-11-18T03:11:00Z"
modified: "2026-11-17T23:03:45Z"
completedAt: "2026-11-17T23:03:45Z"
labels: ["check-quota", "architecture", "contract"]
order: "a1"
review_tier: "full"
---

# Task 1: Check-Quota Hybrid Dynamic Model Discovery, `argonMode` Mirror, Schema Types & `refresh` Cache Persistence

Epic: [check_quota_dynamic_models_and_review_action](../../epic/check_quota_dynamic_models_and_review_action/check_quota_dynamic_models_and_review_action.en.md)

## Requirement Analysis

Implement dynamic per-profile model discovery, capability derivation, shared-pool Argon mirroring, ping suppression, CLI rendering updates, and cache persistence across `scripts/agy_quota.py` and `scripts/types/quota_dashboard.types.ts`:

1. **Hybrid + Cache Model Discovery (`scripts/agy_quota.py`)**:
   - Add `parse_usage_group_models(groups: list) -> dict`: extract `g.get("description", "")` from `/usage` groups (`gemini`, `claude`, `argon`), normalize comma-separated model names while preserving clean display strings, and compute deterministic `groupDescSig` SHA-256 hex digest over normalized `(groupName, description)` pairs.
   - Add `parse_agy_models_catalog(stdout: str) -> list[dict]` parsing `agy models` into structured entries `{id, label, quotaFamily, tags}` (`carbon`, `argon`, `orchestrator`, `hydrogen`, `flash`, `claude`, `gpt`, `g1-pro`) while preserving existing `parse_agy_models_output(stdout: str) -> list[str]` unchanged.
   - Reconcile `/usage` descriptions with `agy models` catalog (e.g., adding `Orchestrator (Argon)` on `danhdue` when `gemini-pro-orchestrator-g1-pro` appears in `agy models` but is omitted from `groups[0].description`).
   - Enforce Hybrid + Cache policy: skip `agy models` entirely for `AUTH NEEDED` or `DISABLED` profiles; invoke `agy models` on single-profile queries (`check-quota <profile>`, `refresh`, `/api/refresh`, `execute_ping_profile()`) and during batch scans (`all`, `/api/refresh-all`) only when cache is missing, `modelsFetchedAt` > 24 hours old, or `groupDescSig` changed.
2. **`argonMode`, Shared-Pool Mirror & Strict Per-Profile Isolation**:
   - Classify `argonMode` into `"separate"` (dedicated Argon `/usage` group), `"shared_gemini"` (no dedicated Argon group, yet `"argon"` exists in Gemini `description` or `modelCatalog`), or `"none"`.
   - When `argonMode == "shared_gemini"`, populate `argonWeekly` by mirroring `geminiWeekly`'s emitted runtime keys (`fraction`, `countdown`, `resetTime`, `resetTimeLocal`, `unavailable`) with `sharedPool: True` and `mode: "shared_gemini"`. Set `hasArgon = (argonMode != "none")`.
   - Derive `capabilities`: `{tier, hasCarbon, hasArgon, argonMode, hasOrchestrator, badges}` (`ULTRA`, `PRO`, `FREE`, `Carbon`, `Argon`, `Orchestrator`). Return `"plan_name": plan_raw` from `fetch_quota_for_profile()`, keep top-level `tier` strictly `"PRO"` / `"FREE"` so `execute_ping_profile()` (`tier == "PRO"` / `"FREE"`) continues operating safely while `capabilities.tier` carries `"ULTRA"` when applicable.
   - Gate standalone Argon pings/probes across BOTH live and cached-fallback paths — `execute_ping_profile()` (including cached branch `L2908-L2920`) and `probe_blocked_profile()` (`L666-L820`) — on `argonMode == "separate"` (or legacy cache lacking `capabilities.argonMode` with `sharedPool != True` and `hasArgon and not unavailable`).
   - **Strict Per-Profile Isolation**: Never invoke or merge pools via `retrieveUserQuotaSummary`; every profile retains completely independent payloads and output entries.
3. **CLI Views & `refresh` Cache Persistence**:
   - Update `print_dashboard_cards()` and `print_all_summary()` to display dynamic group model lists and `(Shared Gemini)` mirrored quota percentages/resets for `shared_gemini` profiles.
   - Update `main()`'s `refresh` CLI branch to persist merged quota + model metadata via `update_cached_profile()`.
   - Tolerate missing/null `/usage` group descriptions or `agy models` timeouts without crashing `fetch_quota_for_profile()`.
4. **TypeScript Schema (`scripts/types/quota_dashboard.types.ts`)**:
   - Export `ArgonMode`, `ModelCatalogEntry`, `ProfileCapabilities`; align `QuotaBucket` with the emitted dashboard bucket fields (`name`, `fraction`, `countdown`, `resetTime`, `resetTimeLocal?`, `unavailable`, `tags?`, `sharedPool?: boolean`, `mode?: ArgonMode`, keeping `id?`, `window?`, `remainingFraction?`, `description?`, `isAvailable?` optional for backward compatibility); and add additive optional properties (`models?`, `availableModels?`, `modelCatalog?`, `groupModels?`, `capabilities?`, `modelsFetchedAt?`, `groupDescSig?`) on `QuotaGroup` and `ProfileQuotaState`.
5. **Unit & CLI Integration Suite (`tests/test_cqra_quota_discovery.py`)**:
   - Cover scenarios `CQRA-HP-01`, `CQRA-HP-02`, `CQRA-EC-01`, `CQRA-ST-01`, `CQRA-AR-01`, and `CQRA-FR-01`.

## Files

Allowed files:
- `scripts/agy_quota.py`
- `scripts/types/quota_dashboard.types.ts`
- `tests/test_cqra_quota_discovery.py` (new)

Read-only context:
- `.devtool/epic/check_quota_dynamic_models_and_review_action/check_quota_dynamic_models_and_review_action.en.md` — Epic HLD & Contracts
- `.devtool/epic/check_quota_dynamic_models_and_review_action/bdd_scenarios.en.md` — Canonical BDD Scenarios

## Design Rationale

Centralizing Hybrid + Cache discovery, `argonMode` classification, and Shared-Pool mirroring inside `scripts/agy_quota.py` ensures HTTP server endpoints, CLI dashboard cards, `--table` views, and Web UI state consume one consistent contract while preserving legacy `parse_agy_models_output()` compatibility. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/agy_quota.py`: `parse_agy_models_output` (L116-L126), `probe_blocked_profile` (L666-L820), `fetch_quota_for_profile` (L883-L968), `parse_quota_items` (L971-L1021), `print_dashboard_cards` (L1024-L1101), `print_all_summary` (L1117-L1169), `get_dashboard_html_path` (L1172-L1182), `load_cached_profiles` (L2456-L2517), `update_cached_profile` (L2520-L2551), `format_profile_for_dashboard` (L2554-L2734), `execute_ping_profile` (L2737-L3079; cached branch L2908-L2920), `_discover_profile_models` (L3105-L3120), `main` (L3983-L4223), new `parse_usage_group_models`, new `parse_agy_models_catalog`, new `classify_argon_mode`
  - `scripts/types/quota_dashboard.types.ts`: `QuotaBucket` (L16-L24), `QuotaGroup` (L26-L30), `ProfileQuotaState` (L58-L71), new `ArgonMode`, new `ModelCatalogEntry`, new `ProfileCapabilities`
  - `tests/test_cqra_quota_discovery.py`: new unit and CLI test suite
- **Downstream Callers**: Task 04 (`quota_dashboard.html`), `tests/test_agy_quota.py`, `tests/test_claude_quota.py`, `tests/test_kiro_quota.py`.
- **Cross-Platform Bridges**: JSON payload served by `agy_quota.py` HTTP server and HTML injection matching `scripts/types/quota_dashboard.types.ts`.
- **Target Test Coverage Threshold**: 100% of Hybrid cache branches, `argonMode` paths, strict per-profile isolation, `refresh` persistence, and error fallbacks.

### BDD SCENARIOS

Covers: CQRA-HP-01, CQRA-HP-02, CQRA-EC-01, CQRA-ST-01, CQRA-AR-01, CQRA-FR-01

```gherkin
Scenario: [CQRA-HP-01] [Tier A - Unit] Ultra shared-pool profile discovers dynamic models, capabilities, and mirrors Gemini Weekly onto Argon
Given an authenticated profile "nguyenhieu000690" where `/usage` returns two quota groups `"Gemini Models"` (description `"Gemini 4 Carbon, Gemini 4 Argon, Gemini 4 Hydrogen, Orchestrator (Carbon), Orchestrator (Argon), Gemini 3.8 Flash"`, 85% remaining, reset `"2026-11-24T00:00:00Z"`) and `"Claude and GPT models"` (description `"Claude Sonnet 4.6, Claude Opus 4.6, GPT-OSS 120B"`, 90% remaining) with no dedicated Argon group, and `agy models` returns 18 IDs including `gemini-4-carbon-high`, `gemini-4-argon-high`, `gemini-pro-orchestrator`, and `gemini-pro-orchestrator-argon`
When `fetch_quota_for_profile("nguyenhieu000690")` and `format_profile_for_dashboard("nguyenhieu000690", result)` execute
Then `groupModels["gemini"]` equals `["Gemini 4 Carbon", "Gemini 4 Argon", "Gemini 4 Hydrogen", "Orchestrator (Carbon)", "Orchestrator (Argon)", "Gemini 3.8 Flash"]` and `groupModels["claude"]` equals `["Claude Sonnet 4.6", "Claude Opus 4.6", "GPT-OSS 120B"]`
And `capabilities["argonMode"]` equals `"shared_gemini"`, `capabilities["tier"]` equals `"ULTRA"`, `capabilities["badges"]` includes `"ULTRA"`, `"Carbon"`, `"Argon"`, and `"Orchestrator"`, top-level `tier` equals `"PRO"`, and `hasArgon` is `True`
And `argonWeekly["sharedPool"]` is `True`, `argonWeekly["mode"]` equals `"shared_gemini"`, and `argonWeekly["fraction"]` equals `0.85` with resetTime `"2026-11-24T00:00:00Z"`

Scenario: [CQRA-HP-02] [Tier A - Unit] Pro separate-Argon profile merges agy models catalog with /usage descriptions and preserves Claude 5.5 labels
Given an authenticated profile "danhdue" where `/usage` returns three quota groups `"Gemini Models"` (description `"Gemini 4 Hydrogen, Gemini 3.8 Flash"`, 100% remaining), `"Claude and GPT models"` (description `"Claude Opus 5.5, Claude Sonnet 5.5, GPT-OSS 120B"`, 80% remaining), and `"Gemini 4 Argon"` (`gemini-argon-wtu-weekly`, 45% remaining), and `agy models` additionally includes `gemini-pro-orchestrator-g1-pro`
When `fetch_quota_for_profile("danhdue")` and `format_profile_for_dashboard("danhdue", result)` execute
Then `capabilities["argonMode"]` equals `"separate"`, `capabilities["tier"]` equals `"PRO"`, `capabilities["hasOrchestrator"]` is `True`, top-level `tier` equals `"PRO"`, and `groupModels["claude"]` contains `"Claude Opus 5.5"`, `"Claude Sonnet 5.5"`, and `"GPT-OSS 120B"`
And `argonWeekly["sharedPool"]` is `False`, `argonWeekly["mode"]` equals `"separate"`, `argonWeekly["fraction"]` equals `0.45`, and `modelCatalog` includes the reconciled `gemini-pro-orchestrator-g1-pro` entry

Scenario: [CQRA-EC-01] [Tier A - Unit] Auth-needed and disabled profiles never invoke agy models subprocesses
Given profiles `"broken_auth"` with `AUTH NEEDED` status and `"banned_acct"` with `DISABLED` status, where `"banned_acct"` has a previously cached `availableModels` list `["gemini-4-hydrogen-high"]`
When `fetch_quota_for_profile()` and batch `all` processing run across both profiles
Then subprocess runner mocks receive zero calls invoking `agy models` for `"broken_auth"` or `"banned_acct"`
And `"banned_acct"` retains its cached `availableModels` without clearing existing metadata

Scenario: [CQRA-ST-01] [Tier A - Unit] Hybrid cache refreshes agy models on miss, signature change, 24h expiry, and single-profile refresh while skipping warm batch hits
Given an authenticated `"shared_gemini"` profile cached 2 hours ago with matching `groupDescSig` inside a `tmp_path`-isolated cache HTML (never mutating repo-tracked or host home files)
When batch scan (`all`) runs once with unchanged `/usage` descriptions, then runs again after `/usage` `description` changes `groupDescSig`, then runs a third time after `modelsFetchedAt` ages past 24 hours, followed by single-profile `refresh` CLI command
Then batch run 1 invokes `agy models` 0 times, batch run 2 invokes `agy models` 1 time and updates `groupDescSig`, batch run 3 invokes `agy models` 1 time and refreshes `modelsFetchedAt`, and single-profile `refresh` invokes `agy models` 1 time and persists updated data via `update_cached_profile()` into the isolated `tmp_path` target

Scenario: [CQRA-AR-01] [Tier A - Unit] Strictly independent per-profile quota isolation, ping suppression, and CLI table formatting
Given two Ultra profiles `"hoangcongtam690"` and `"nguyenhieu000690"` whose mocked `/usage` timestamps match, without invoking `retrieveUserQuotaSummary`
When `fetch_quota_for_profile()`, `execute_ping_profile()`, `print_dashboard_cards()`, and `print_all_summary(..., show_providers=True)` execute for both profiles
Then neither `fetch_quota_for_profile()` nor `format_profile_for_dashboard()` calls `retrieveUserQuotaSummary` or emits any cross-profile pool linkage field
And `execute_ping_profile()` suppresses standalone `Argon 7D` pings for both `shared_gemini` profiles while `print_all_summary()` prints `(Shared Gemini)` and mirrored percentages per profile independently

Scenario: [CQRA-FR-01] [Tier A - Unit] Malformed /usage group descriptions or agy models timeout degrade softly without crashing quota fetch
Given a profile whose `/usage` payload contains a group with `description: null` and an `agy models` subprocess invocation that raises `subprocess.TimeoutExpired`
When `fetch_quota_for_profile()` runs with fallback cache present
Then `fetch_quota_for_profile()` returns `available` quota buckets with empty/cached `groupModels` and `argonMode == "none"` (or cached mode) without raising an unhandled exception
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cqra_quota_discovery.py::test_cqra_hp_01_ultra_shared_pool_discovery_and_mirror` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cqra_quota_discovery.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m unittest tests/test_agy_quota.py tests/test_kiro_quota.py && python3 -m pytest -q --tb=short --maxfail=3 tests/test_claude_quota.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_cqra_quota_discovery.py && ruff check --select E9,F63,F7,F821,F841,B007,B904 scripts/agy_quota.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && mypy tests/test_cqra_quota_discovery.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/cqra_task_01.xml tests/test_cqra_quota_discovery.py tests/test_agy_quota.py tests/test_claude_quota.py` | exit 0; results build/test-results/cqra_task_01.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Hybrid + Cache TTL is fixed at `24 hours` (`86400s`), keyed by `modelsFetchedAt` (ISO-8601 UTC) and `groupDescSig` (SHA-256 hex digest prefix of normalized `(groupName, description)` pairs).
- Single-profile refresh paths (`check-quota <profile>`, `refresh`, `/api/refresh`, `execute_ping_profile()`) refresh `agy models` whenever authenticated & enabled; batch scans (`all`, `/api/refresh-all`) skip `agy models` on warm matching signatures within 24h; `AUTH NEEDED` / `DISABLED` profiles never invoke `agy models`.
- `argonMode` values are strictly `"separate" | "shared_gemini" | "none"`. `hasArgon = (argonMode != "none")`. When `argonMode == "shared_gemini"`, `argonWeekly` mirrors `geminiWeekly`'s emitted keys (`fraction`, `countdown`, `resetTime`, `resetTimeLocal`, `unavailable`) with `sharedPool: True`, `mode: "shared_gemini"`.
- `QuotaBucket` in `scripts/types/quota_dashboard.types.ts` aligns with the runtime emitted shape (`name`, `fraction`, `countdown`, `resetTime`, `resetTimeLocal?`, `unavailable`, `tags?`, `sharedPool?: boolean`, `mode?: ArgonMode`) while keeping legacy fields (`id?`, `window?`, `remainingFraction?`, `description?`, `isAvailable?`) optional for backward compatibility.
- `ULTRA` tier derivation: `fetch_quota_for_profile()` (`L954-L964`) returns `"plan_name": plan_raw` in its result dict alongside existing fields. In `format_profile_for_dashboard()`, `capabilities.tier` resolves to `"FREE"` when top-level `tier == "FREE"`, `"ULTRA"` when `result.get("plan_name", "")` contains `"ULTRA"` OR (top-level `tier != "FREE"` AND no dedicated Argon group exists AND a Carbon model is present in `groupModels`/`modelCatalog`), else `"PRO"` (`"DEV"` is dropped since no runtime source emits `DEV`). Top-level `tier` stays strictly `"PRO"` or `"FREE"` so `execute_ping_profile()` (`tier == "PRO"` / `"FREE"`) continues operating safely.
- Every cached-fallback Argon path (`probe_blocked_profile` `L666-L820`, `execute_ping_profile` cached branch `L2908-L2920`) gates Argon probes/pings on `capabilities.argonMode == "separate"` (or, for legacy caches lacking `capabilities.argonMode`, when `argonWeekly.sharedPool != True` and `hasArgon and not argonWeekly.unavailable`).
- Test isolation for cache persistence (`CQRA-ST-01` and `refresh`): tests MUST patch `update_cached_profile` (or patch `get_dashboard_html_path` and `sync_copies` / `REAL_HOME` / `Path.home` to `tmp_path`), asserting the mock or `tmp_path` file and NEVER mutating repo-tracked `quota_dashboard.html` or `~/antigravity_homes/`.
- Cross-profile pool aggregation via `retrieveUserQuotaSummary` is strictly prohibited.
- `parse_agy_models_output(stdout: str) -> list[str]` preserves its existing return type and contract for downstream callers.

## Definition of Done

- Scenarios CQRA-HP-01, CQRA-HP-02, CQRA-EC-01, CQRA-ST-01, CQRA-AR-01, and CQRA-FR-01 pass cleanly. (V2, V6)
- Existing quota suites (`test_agy_quota.py`, `test_kiro_quota.py`, `test_claude_quota.py`) pass with zero regressions. (V3, V6)
- Ruff checks and mypy typecheck pass cleanly on `tests/test_cqra_quota_discovery.py` and modified paths in `scripts/agy_quota.py`. (V4, V5)

## Dependencies & Blockers

None.

Downstream dependents (blocked by Task 1): `task_04`, `task_05`.

## References & Rollback

- [Epic HLD](../../epic/check_quota_dynamic_models_and_review_action/check_quota_dynamic_models_and_review_action.en.md)
- **Rollback**: Revert task commit to restore `scripts/agy_quota.py` and `scripts/types/quota_dashboard.types.ts`.
