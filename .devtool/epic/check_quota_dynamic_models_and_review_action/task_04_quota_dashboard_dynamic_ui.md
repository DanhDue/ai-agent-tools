---
id: "task_04_quota_dashboard_dynamic_ui"
status: "backlog"
priority: "high"
assignee: null
epic: "check_quota_dynamic_models_and_review_action"
dueDate: null
created: "2026-11-18T03:11:00Z"
modified: "2026-11-18T03:11:00Z"
completedAt: null
labels: ["check-quota", "ui", "frontend"]
order: "a4"
review_tier: "full"
---

# Task 4: Quota Dashboard Web UI Dynamic Badges, Group Model Rosters, Shared-Pool Mirror & Modal

Epic: [check_quota_dynamic_models_and_review_action](check_quota_dynamic_models_and_review_action.en.md)

## Requirement Analysis

Update `skills/check-quota/resources/dashboard/quota_dashboard.html` so profile cards, header capability badges, quota score sorting, and profile detail modals dynamically reflect per-profile model rosters and `shared_gemini` Argon semantics produced by Task 01:

1. **Dynamic Header Tier & Capability Badges (`getTierBadgeHTML`, `getArgonBadgeHTML`)**:
   - Render tier badge from `data.capabilities?.tier || data.tier` (`ULTRA`, `PRO`, `FREE`, `DEV`) and render capability pills from `data.capabilities?.badges` (`Carbon`, `Argon`, `Orchestrator`) rather than hardcoded `PRO` + boolean `hasArgon` only.
   - Annotate `Argon` badges with a pooled tooltip hint (`"Shared w/ Gemini Pool"`) when `argonWeekly?.sharedPool === true` / `argonMode === "shared_gemini"`.
2. **Per-Group Model Rosters & Shared-Pool Mirror (`renderProfileCard`, `renderDetailModelCard`)**:
   - Display actual dynamic model lists from `data.groupModels?.gemini` (e.g., `Gemini 4 Carbon`, `Gemini 4 Argon`, `Gemini 4 Hydrogen`, `Orchestrator`, `Gemini 3.8 Flash`) and `data.groupModels?.claude` (e.g., `Claude Sonnet 4.6`, `Claude Opus 4.6`, `GPT-OSS 120B` vs `5.5`), falling back safely to default labels on legacy cached profiles missing `groupModels`.
   - For the Argon weekly bucket: render independent weekly quota when `argonMode === "separate"`, render mirrored `geminiWeekly` progress + countdown + explicit `"Shared w/ Gemini Pool"` pill alongside Argon/Orchestrator model labels when `sharedPool === true` (eliminating false `INACTIVE` / `Unavailable N/A`), and suppress active badges/cards when `argonMode === "none"`.
3. **Quota Score & Auto-Switch Eligibility (`getProfileQuotaScore`, `isProfileSchedulable`, `renderAllProfiles`)**:
   - Prevent double-counting `argonWeekly` against `geminiWeekly` inside `getProfileQuotaScore()` when `argonWeekly?.sharedPool === true`, while preserving `hasArgon === true` so `shared_gemini` accounts still satisfy Argon filters.
4. **Profile Info Modal (`openProfileInfoModal`)**:
   - Render grouped `Gemini Models`, `Claude & GPT`, and `Argon / Orchestrator` model lists, `capabilities.badges`, `argonMode`, `modelsFetchedAt`, and `groupDescSig`.
5. **Browser / DOM Verification Suite (`tests/test_cqra_quota_ui.py`)**:
   - Cover scenarios `CQRA-HP-03`, `CQRA-EC-02`, and `CQRA-AR-02` using both DOM JS verification and headless Chrome CDP (asserting rendered badges, `"Shared w/ Gemini Pool"`, modal text, layout bounds, and zero console errors / runtime exceptions).

## Files

Allowed files:
- `skills/check-quota/resources/dashboard/quota_dashboard.html`
- `tests/test_cqra_quota_ui.py` (new)

Read-only context:
- `.devtool/epic/check_quota_dynamic_models_and_review_action/check_quota_dynamic_models_and_review_action.en.md` — Epic HLD & UI Contracts
- `.devtool/epic/check_quota_dynamic_models_and_review_action/bdd_scenarios.en.md` — Canonical BDD Scenarios
- `scripts/types/quota_dashboard.types.ts` — Updated payload schema

## Design Rationale

Rendering straight from Task 01's additive `ProfileQuotaState` properties (`capabilities`, `groupModels`, `argonWeekly.sharedPool`, `argonWeekly.mode`) while preserving graceful fallback on legacy cached entries upgrades Web UI fidelity with zero downtime on warm caches. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/check-quota/resources/dashboard/quota_dashboard.html`: `getTierBadgeHTML` (L2230-L2244), `getArgonBadgeHTML` (L2254-L2261), `renderDetailModelCard` (L2305-L2366), `renderProfileCard` (L2377-L2756), `getProfileQuotaScore` (L2853-L2869), `renderAllProfiles` (L3026-L3126), `isProfileSchedulable` (L3140-L3145), `openProfileInfoModal` (L4230-L4255)
  - `tests/test_cqra_quota_ui.py`: new UI DOM + headless Chrome CDP test suite
- **Downstream Callers**: Task 05, `tests/test_rsdh_quota_modal_stack.py`, `scripts/agy_quota.py` HTTP dashboard HTML embed.
- **Cross-Platform Bridges**: Consumes `ProfileQuotaState` JSON schema defined in `scripts/types/quota_dashboard.types.ts`.
- **Target Test Coverage Threshold**: 100% of dynamic badges, shared-pool mirror UI, legacy cache fallback, quota score non-double-count, and modal DOM rendering with zero CDP console errors.

### BDD SCENARIOS

Covers: CQRA-HP-03, CQRA-EC-02, CQRA-AR-02

```gherkin
Scenario: [CQRA-HP-03] [Tier C - Integration] Quota dashboard Web UI renders dynamic badges, per-group rosters, and Shared Gemini Pool row without INACTIVE errors
Given an HTTP server serving `skills/check-quota/resources/dashboard/quota_dashboard.html` injected with formatted `shared_gemini` ("nguyenhieu000690") and `separate` ("danhdue") profiles
When headless Chrome loads the dashboard page and opens the profile info modal for "nguyenhieu000690"
Then the card header displays dynamic badges matching `capabilities["badges"]` (`Carbon`, `Argon`, `Orchestrator`) and zero uncaught browser console errors occur
And the Argon row inside "nguyenhieu000690" renders `"Shared w/ Gemini Pool"` alongside `85%` instead of `"INACTIVE"` or `"Unavailable N/A"`
And `#profile-info-modal` displays the full dynamic model lists for `Gemini Models`, `Claude & GPT`, and `Argon / Orchestrator`

Scenario: [CQRA-EC-02] [Tier A - Unit] Legacy cached payloads without new model fields and none-Argon accounts render safely on Web UI
Given one legacy cached profile object missing `groupModels`, `capabilities`, and `argonWeekly.sharedPool`, plus a Free-tier profile `"free_acct"` with `argonMode == "none"` and `argonWeekly.available == false`
When `renderProfileCard()` and `getProfileQuotaScore()` run against both profiles in a real browser DOM
Then the legacy profile renders fallback group headers without throwing a `TypeError` or blank DOM node
And `"free_acct"` does not display an active Argon badge or `"Shared w/ Gemini Pool"` indicator

Scenario: [CQRA-AR-02] [Tier A - Unit] Frontend quota score avoids double-counting shared_gemini Argon bucket while preserving Argon filter match
Given profile data in `quota_dashboard.html` for `"nguyenhieu000690"` (`geminiWeekly.remainingFraction = 0.80`, `argonWeekly.remainingFraction = 0.80`, `argonWeekly.sharedPool = true`, `hasArgon = true`) alongside an identical `separate` profile where `argonWeekly.remainingFraction = 0.20` and `argonWeekly.sharedPool = false`
When `getProfileQuotaScore()` and the `argon` filter predicate evaluate both profiles
Then `"nguyenhieu000690"` matches the `argon` filter predicate without counting the shared `0.80` pool twice in aggregate weighted quota score, while the `separate` profile weights its independent `0.20` Argon pool separately
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cqra_quota_ui.py::test_cqra_hp_03_quota_dashboard_cdp_dynamic_badges_and_shared_pool` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cqra_quota_ui.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_quota_modal_stack.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_cqra_quota_ui.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && mypy tests/test_cqra_quota_ui.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/cqra_task_04.xml tests/test_cqra_quota_ui.py tests/test_rsdh_quota_modal_stack.py` | exit 0; results build/test-results/cqra_task_04.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- All dynamic strings rendered inside profile cards, badges, and `#profile-info-modal` must escape HTML safely and preserve existing DOM hooks relied upon by `tests/test_rsdh_quota_modal_stack.py`.
- Cross-profile pool links are never computed or displayed; each card renders exclusively from its own `PROFILES_DATA[profile]` entry.
- Zero console errors (`console.error` / uncaught `pageerror`) must occur under headless Chrome CDP loading.

## Definition of Done

- Scenarios CQRA-HP-03, CQRA-EC-02, and CQRA-AR-02 pass in Chrome CDP / DOM harness with zero console errors. (V2, V6)
- Existing quota modal regression suite (`test_rsdh_quota_modal_stack.py`) passes without regressions. (V3, V6)
- Ruff lint and mypy typecheck pass cleanly on `tests/test_cqra_quota_ui.py`. (V4, V5)

## Dependencies & Blockers

Blocked by [Task 1](task_01_check_quota_dynamic_models_and_argon_mode.md).

Downstream dependents (blocked by Task 4): `task_05`.

## References & Rollback

- [Epic HLD](check_quota_dynamic_models_and_review_action.en.md)
- **Rollback**: Revert task commit to restore `skills/check-quota/resources/dashboard/quota_dashboard.html`.
