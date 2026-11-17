# Check-Quota Dynamic Models and Review Proposed Action High-Level Design

## Table of Contents

- [Meta Data](#meta-data)
- [Background](#background)
- [Goals and Non-Goals](#goals-and-non-goals)
- [Architecture and Technical Design](#architecture-and-technical-design)
- [Feature Maintenance Map](#feature-maintenance-map)
- [Module Contracts and HTTP Interfaces](#module-contracts-and-http-interfaces)
- [Impact Analysis](#impact-analysis)
- [Shared Contract Impact](#shared-contract-impact)
- [Integration Test Plan and Boundary Matrix](#integration-test-plan-and-boundary-matrix)
- [Verification Environment](#verification-environment)
- [Comprehensive BDD Scenario Coverage](#comprehensive-bdd-scenario-coverage)
- [Rollout Strategy and Mitigation](#rollout-strategy-and-mitigation)
- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)
- [Spec Errata](#spec-errata)

## Meta Data

- **Epic name**: `check_quota_dynamic_models_and_review_action`
- **Status**: Queued (backlog) — behind `four_persona_governance`
- **PIC**: `nguyenhieu000690`
- **Target release**: Next plugin release
- **Platform**: Python tooling, Markdown skill prompts, TypeScript contract types, local HTTP servers, and HTML/Vanilla JS dashboards
- **Depends on epic**: none
- **Source Spec**: [Check-Quota Dynamic Models and Review Proposed Action Design Spec](2026-11-18-check-quota-dynamic-models-and-review-action-design.en.md)

## Background

This epic resolves two high-impact observability regressions discovered across the kit's quota and task dashboards:

1. **`/check-quota` Static Model Strings & False Argon Inactive State**:
   - `parse_quota_items()` (`scripts/agy_quota.py:L971-L1021`) ignores `/usage` `groups[].description`, and UI/CLI renderers (`print_dashboard_cards` `L1024-L1102`, `renderProfileCard` `quota_dashboard.html:L2377-L2756`, `openProfileInfoModal` `L4230-L4255`) hardcode static strings (`"Gemini 3.8 / Pro 5H"`, `"Claude 5.5 / GPT 5H"`, `"Gemini 4 Argon Weekly"`).
   - Ultra-tier profiles (`hoangcongtam690`, `nguyenhieu000690`) bundle `Gemini 4 Carbon`, `Gemini 4 Argon`, `Gemini 4 Hydrogen`, `Orchestrator (Carbon)`, `Orchestrator (Argon)`, and `Gemini 3.8 Flash` inside `"Gemini Models"` with no 3rd Argon group, whereas Pro-tier profiles (`danhdue`) carry a separate 3rd `"Gemini 4 Argon"` group while omitting `Orchestrator (Argon)` from `/usage` description despite exposing `gemini-pro-orchestrator-g1-pro` via `agy models`.
   - Treating `has_argon = items["argon_weekly"]["available"]` marks Ultra pooled profiles as `INACTIVE` / `Unavailable N/A` and causes `refresh_session.py` (`ping_profile` `L1486-L1658`) to trigger redundant `Argon 7D` pings. Meanwhile, CLI `refresh` (`agy_quota.py:L4079-L4135`) fails to persist updated cache entries via `update_cached_profile()`.
   - Cross-profile pool aggregation via `retrieveUserQuotaSummary` is explicitly forbidden by the user: every profile must display strictly independent quota metrics.
2. **Missing `PROPOSED ACTION` in `/check-tasks` Cross-Model Review**:
   - `skills/principal-review/references/principal-review-prompt.md:L56` mandates `. Proposed: <edit>`, whereas `skills/dev-implementation/references/external-review-prompt.md:L67` and `local-review-prompt.md:L50` omit `. Proposed: <edit>`.
   - `run_external_review.py` hardcodes `?` in `top_risk_findings_section()` (`L2407-L2431`) and `triage()` (`L2515-L2610`), while `check()` (`L2230-L2251`) enforces 5-column persisted tables (`len(cells) == 5`).
   - `tasks_server.py` (`parse_review_results` `L525-L785`) searches only `cells[3]` with `Proposed:\s*(.+)`, assumes `cells[4]` is always `decision`, ignores `.devtool/epic/<epic>/fix_plan_round<N>.md` (`Summary Matrix` / `### Finding #N`), and omits `fix_plan_round*.md` from `watch_paths` (`L770-L778`).

## Goals and Non-Goals

### Goals

- Combine live `/usage` `groups[].description` parsing with cached `agy models` (`groupDescSig` + 24h TTL + immediate refresh on single-profile commands, never on `AUTH NEEDED` or `DISABLED` profiles).
- Classify `argonMode` (`"separate"` | `"shared_gemini"` | `"none"`), mirror `geminiWeekly` onto `argonWeekly` (`sharedPool: true`) for `shared_gemini`, avoid double-counting shared pool quota in `getProfileQuotaScore()`, and suppress redundant `Argon 7D` pings in both `agy_quota.py` and `refresh_session.py`.
- Surface dynamic `capabilities.badges` (`ULTRA`, `PRO`, `FREE`, `DEV`, `Carbon`, `Argon`, `Orchestrator`), per-group model rosters, and `(Shared Gemini)` / `"Shared w/ Gemini Pool"` indicators across `quota_dashboard.html` and CLI output, plus persist CLI `refresh` updates via `update_cached_profile()`.
- Update `external-review-prompt.md` and `local-review-prompt.md` to emit `. Proposed: <edit>`, pre-fill `Proposed action` in `run_external_review.py` while keeping `check()` 5-column compliant, and enhance `tasks_server.py` (`parse_review_results()` + `watch_paths`) with multi-prefix extraction, 5/6-column table detection, and `fix_plan_round<N>.md` fallback.

### Non-Goals

- Cross-profile pool grouping or `retrieveUserQuotaSummary` aggregation in UI or CLI.
- Breaking 5-column persisted `review_results.md` compatibility enforced by `run_external_review.py check()`.
- Modifying `four_persona_governance` active `.devtool/features/` tasks (`status: "backlog"` applies per Concurrent-Epic Backlog Rule).

## Architecture and Technical Design

### Part A Hybrid Model Discovery and Argon Classification Flow

```mermaid
flowchart TD
    U["Run agy --output-format json -p /usage"] --> PG["parse_usage_group_models and compute groupDescSig"]
    PG --> AD{"Profile AUTH NEEDED or DISABLED?"}
    AD -- "Yes" --> SC["Skip agy models and preserve cached catalog"]
    AD -- "No" --> HC{"Single-profile command OR missing cache OR TTL > 24h OR groupDescSig changed?"}
    HC -- "Yes" --> MC["Run agy models and parse_agy_models_catalog"]
    MC --> MG["Merge /usage groups with modelCatalog and persist cache"]
    HC -- "No" --> RC["Reuse cached modelCatalog and re-merge live /usage"]
    SC --> AM["Classify argonMode: separate vs shared_gemini vs none"]
    MG --> AM
    RC --> AM
    AM --> UI["Render Web UI badges, Shared w/ Gemini Pool mirror, CLI cards, and --table"]
    AM --> PG2["Ping Guard: trigger Argon 7D only when argonMode == separate"]
```

### Part B Review Proposed Action Extraction Flow

```mermaid
flowchart LR
    PR["external-review-prompt.md & local-review-prompt.md (. Proposed: edit)"] --> RR["run_external_review.py (5-col table + pre-filled triage & top-risk)"]
    LG["Legacy 5-col review_results.md & fix_plan_roundN.md"] --> TS["tasks_server.py parse_review_results (5/6-col + multi-prefix + fallback + watch_paths)"]
    RR --> TS
    TS --> DASH["tasks_dashboard.html Cross-Model Review PROPOSED ACTION"]
```

## Feature Maintenance Map

| Feature Area | Primary Files | Entry / Function |
|---|---|---|
| Dynamic Model Parsing, Hybrid Cache, `argonMode`, CLI Cards & `refresh` Cache | `scripts/agy_quota.py` | `parse_usage_group_models`, `parse_agy_models_catalog`, `parse_quota_items()`, `format_profile_for_dashboard()`, `execute_ping_profile()`, `print_dashboard_cards()`, `print_all_summary()`, `main()` |
| Ping Suppression Guard for Shared-Pool Argon | `skills/refresh-session/resources/scripts/refresh_session.py` | `_extract_usage_buckets()`, `check_profile_has_argon()`, `ping_profile()` |
| Quota Payload TypeScript Schema | `scripts/types/quota_dashboard.types.ts` | `ArgonMode`, `ModelCatalogEntry`, `ProfileCapabilities`, `QuotaBucket`, `QuotaGroup`, `ProfileQuotaState` |
| Quota Dashboard Dynamic Badges, Roster & Shared Mirror UI | `skills/check-quota/resources/dashboard/quota_dashboard.html` | `getTierBadgeHTML()`, `getArgonBadgeHTML()`, `renderProfileCard()`, `getProfileQuotaScore()`, `openProfileInfoModal()` |
| External/Local Prompt Format & Review Triage Pre-Fill | `skills/dev-implementation/references/external-review-prompt.md`, `skills/dev-implementation/references/local-review-prompt.md`, `skills/dev-implementation/resources/scripts/run_external_review.py` | Prompt format section, `parse_findings()`, `top_risk_findings_section()`, `triage()` |
| Multi-Strategy Review Parser, `fix_plan` Fallback & Dashboard Rendering | `skills/check-tasks/resources/scripts/tasks_server.py`, `skills/check-tasks/resources/dashboard/tasks_dashboard.html`, `scripts/verify.sh` | `parse_review_results()`, `_file_stat_sig()`, `buildReviewFindingsTableHtml()`, `formatReviewTokens()`, `SUITES` |

## Module Contracts and HTTP Interfaces

1. **`scripts/agy_quota.py` Additives & Contracts**:
   - `parse_usage_group_models(groups: list) -> dict`: returns `groupDescriptions`, `groupModels` (`gemini`, `claude`, `argon`), and `groupDescSig` (SHA-256 hex prefix over normalized `(groupName, description)` tuples).
   - `parse_agy_models_catalog(stdout: str) -> list[dict]`: extracts `{id, label, quotaFamily, tags}`; preserves `parse_agy_models_output(stdout: str) -> list[str]` unchanged.
   - `format_profile_for_dashboard()` adds `availableModels`, `modelCatalog`, `groupModels`, `capabilities` (`tier`, `hasCarbon`, `hasArgon`, `argonMode`, `hasOrchestrator`, `badges`), `modelsFetchedAt`, `groupDescSig`; sets `hasArgon = (argonMode != "none")`; when `argonMode == "shared_gemini"`, populates `argonWeekly` with mirrored `geminiWeekly` metrics plus `sharedPool: True` and `mode: "shared_gemini"`.
   - Zero calls to `retrieveUserQuotaSummary`.

2. **`skills/refresh-session/resources/scripts/refresh_session.py` Ping Guard**:
   - `_extract_usage_buckets(cmd_data)` includes normalized per-group descriptions/models so `check_profile_has_argon()` and `ping_profile()` determine `argonMode`: suppress `Argon 7D` ping when `argonMode == "shared_gemini"` and `"Gemini Models"` is active; retain `Argon 7D` ping when `argonMode == "separate"` and dedicated Argon bucket is inactive/empty.

3. **`scripts/types/quota_dashboard.types.ts` Contract**:
   - Exports `ArgonMode = 'separate' | 'shared_gemini' | 'none'`, `ModelCatalogEntry`, `ProfileCapabilities`, and additive optional fields on `QuotaBucket`, `QuotaGroup`, and `ProfileQuotaState`.

4. **`skills/dev-implementation/resources/scripts/run_external_review.py`**:
   - Keeps `render_round()`, `check()`, and `finding_rows()` enforcing 5-column tables in `review_results.md`.
   - `top_risk_findings_section()` and `triage()` extract inline `. Proposed: <edit>` proposals from `finding[3]` (`Problem`) and pre-fill `Proposed action` in `fix_plan_round<N>.md` / top-risk blocks (fallback `?` only when absent).

5. **`skills/check-tasks/resources/scripts/tasks_server.py::parse_review_results`**:
   - Preserves existing call signature; detects 5-column vs 6-column (`Proposed Action`/`Action`) table headers per round; expands `Problem` regex to `. Proposed:`, `Proposed action:`, `Fix:`, `Suggestion:`; falls back per `(round, finding_num)` to `.devtool/epic/<epic>/fix_plan_round<N>.md` (`### Finding #N` `- **Proposed Action (...):**` preferred over `## Summary Matrix` `Action` column, then `fix_plan.md`); adds discovered fix-plan files to `watch_paths` inside `_REVIEW_PARSE_CACHE`.

## Impact Analysis

Shift-left impact analysis (`check_code_impact.py --base-ref main`) audited all target files and 21 downstream callers across tests and scripts:

- **Upstream Git Conflict Status**: **CLEAN** (`0` unmerged commits against `main`). Note that pre-existing dirty worktree changes exist in `skills/check-quota/resources/dashboard/quota_dashboard.html` on the main checkout; Stage 3 tasks execute cleanly inside an isolated branch worktree.
- **Downstream Compatibility**:
  - `parse_agy_models_output` retains its `list[str]` return signature (`test_agy_quota.py`, `refresh_session.py`).
  - Existing `/api/review` and `/api/epic/history` callers receive populated string `proposed_action` values in the existing finding dict shape (`test_check_tasks_server.py`, `test_cehm_history_aggregator.py`, `test_cehm_dashboard_modal_ui.py`).
  - Persisted `review_results.md` tables remain 5-column compatible (`test_run_external_review.py`, `test_local_review.py`, `lifecycle_runner.py`).

## Shared Contract Impact

None — self-contained feature inside `ai-agent-tools` (`shared-contracts/` does not exist in this repository).

## Integration Test Plan and Boundary Matrix

Integration test roots: tests
Protected paths: .agents/quality/**, .devtool/epic/check_quota_dynamic_models_and_review_action/bdd_scenarios.en.md, .devtool/epic/check_quota_dynamic_models_and_review_action/bdd_scenarios.vi.md
Integration results: python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/cqra-integration.xml tests/test_cqra_quota_discovery.py tests/test_cqra_refresh_session_argon.py tests/test_cqra_external_review_proposed.py tests/test_cqra_quota_ui.py tests/test_cqra_review_action_e2e.py tests/test_agy_quota.py tests/test_check_tasks_server.py tests/test_cehm_history_aggregator.py tests/test_cehm_dashboard_modal_ui.py tests/test_rsdh_quota_modal_stack.py tests/test_claude_quota.py -> build/test-results/cqra-integration.xml

| Boundary | Producer | Consumer | Verification Tier |
|---|---|---|---|
| `/usage` descriptions + `agy models` -> Cached `ProfileQuotaState` + `argonMode` | `scripts/agy_quota.py`, `scripts/types/quota_dashboard.types.ts` | `quota_dashboard.html`, CLI cards & `--table` | Tier A Unit + CLI Regression |
| `argonMode` ping guard in `refresh_session.py` | `_extract_usage_buckets()`, `ping_profile()` | `agy_quota.py` & isolated `agy` pings | Tier A Unit |
| `ProfileQuotaState` JSON -> Dynamic Badges & `"Shared w/ Gemini Pool"` UI | `scripts/agy_quota.py` HTTP/HTML embed | `skills/check-quota/resources/dashboard/quota_dashboard.html` | Tier C Headless Chrome CDP |
| Review Prompts `. Proposed:` -> `run_external_review.py` 5-col + pre-filled `fix_plan` | `external-review-prompt.md`, `local-review-prompt.md`, `run_external_review.py` | `parse_review_results()`, human & fixer agents | Tier A Unit |
| `review_results.md` + `fix_plan_round<N>.md` -> `parse_review_results()` -> `PROPOSED ACTION` | `skills/check-tasks/resources/scripts/tasks_server.py` | `skills/check-tasks/resources/dashboard/tasks_dashboard.html` | Tier C HTTP + Headless Chrome CDP |

## Verification Environment

- **Data Isolation**: Automated tests execute inside ephemeral `tmp_path` / `tempfile.TemporaryDirectory` workspaces and bind test HTTP servers only to dynamically assigned localhost ports (`find_available_port`).
- **Forbidden Live Stores**: Automated tests must never mutate host `~/.gemini/`, `~/antigravity_homes/`, `~/.zshrc`, `/tmp/agy_tasks_server.pid`, or `/tmp/agy_quota_server*`. Live CLI checks in manual QA run read-only `check-quota` queries only.
- **Needs Variables**: None (`Needs: —`).

## Comprehensive BDD Scenario Coverage

All 17 BDD scenarios (`CQRA-HP-01` through `CQRA-FR-03`) are defined in [bdd_scenarios.en.md](bdd_scenarios.en.md) spanning Happy Path (`HP`), Edge Cases (`EC`), State Transitions (`ST`), Architecture & Concurrency (`AR`), and Fault Resilience (`FR`).

## Rollout Strategy and Mitigation

- Execute Wave 1 tasks (`Task 01`, `Task 02`, `Task 03`) in parallel over disjoint file sets inside worker slots before advancing to Wave 2 (`Task 04`, `Task 05`).
- Because `four_persona_governance` currently holds active `todo` tasks in `.devtool/features/`, this epic initializes with `status: "backlog"` per Concurrent-Epic Backlog Rule and promotes cleanly once `four_persona_governance` lands or is superseded.
- Verify both existing regression suites (`test_agy_quota.py`, `test_refresh_session.py`, `test_run_external_review.py`, `test_check_tasks_server.py`, `test_cehm_history_aggregator.py`, `test_cehm_dashboard_modal_ui.py`) and `bash scripts/verify.sh` cleanly before Gate 4 convergence.

## Kanban Tasks Breakdown

Confirmed 5-task breakdown (queued behind `four_persona_governance` per Concurrent-Epic Backlog Rule):

1. **[Task 01: Check-Quota Hybrid Model Discovery, `argonMode` Mirror, Schema Types & `refresh` Cache Persistence](task_01_check_quota_dynamic_models_and_argon_mode.md)** (`review_tier: "full"`) — Covers: `CQRA-HP-01`, `CQRA-HP-02`, `CQRA-EC-01`, `CQRA-ST-01`, `CQRA-AR-01`, `CQRA-FR-01`
2. **[Task 02: Refresh-Session Shared-Pool Argon Ping Suppression Guard](task_02_refresh_session_shared_argon_guard.md)** (`review_tier: "full"`) — Covers: `CQRA-ST-02`, `CQRA-FR-02`
3. **[Task 03: Review Prompts `. Proposed:` Contract & `run_external_review.py` Pre-Filled Triage](task_03_review_prompts_and_triage_prefill.md)** (`review_tier: "full"`) — Covers: `CQRA-HP-04`, `CQRA-EC-04`
4. **[Task 04: Quota Dashboard Web UI Dynamic Badges, Group Model Rosters, Shared-Pool Mirror & Modal](task_04_quota_dashboard_dynamic_ui.md)** (`review_tier: "full"`) — Covers: `CQRA-HP-03`, `CQRA-EC-02`, `CQRA-AR-02`
5. **[Task 05: `tasks_server.py` Multi-Strategy `Proposed Action` Extraction, `fix_plan` Fallback, Dashboard UI & Full Regression](task_05_review_action_parser_ui_and_regression.md)** (`review_tier: "full"`) — Covers: `CQRA-HP-05`, `CQRA-EC-03`, `CQRA-ST-03`, `CQRA-FR-03`

## Spec Errata

None.
