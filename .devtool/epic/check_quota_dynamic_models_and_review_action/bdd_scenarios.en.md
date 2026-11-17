# Check-Quota Dynamic Models and Review Proposed Action BDD Scenarios

- **Epic**: `check_quota_dynamic_models_and_review_action`
- **PIC**: `nguyenhieu000690`
- **HLD**: [High-Level Design](check_quota_dynamic_models_and_review_action.en.md)
- **Source Spec**: [Design Spec](2026-11-18-check-quota-dynamic-models-and-review-action-design.en.md)

## Table of Contents

- [Dimension 1 Happy Path](#dimension-1-happy-path)
- [Dimension 2 Edge Cases](#dimension-2-edge-cases)
- [Dimension 3 State Transitions](#dimension-3-state-transitions)
- [Dimension 4 Architecture and Concurrency](#dimension-4-architecture-and-concurrency)
- [Dimension 5 Fault Resilience](#dimension-5-fault-resilience)

## Dimension 1 Happy Path

```gherkin
Scenario: [CQRA-HP-01] [Tier A - Unit] Ultra shared-pool profile discovers dynamic models, capabilities, and mirrors Gemini Weekly onto Argon
Given an authenticated profile "nguyenhieu000690" where `/usage` returns two quota groups `"Gemini Models"` (description `"Gemini 4 Carbon, Gemini 4 Argon, Gemini 4 Hydrogen, Orchestrator (Carbon), Orchestrator (Argon), Gemini 3.8 Flash"`, 85% remaining, reset `"2026-11-24T00:00:00Z"`) and `"Claude and GPT models"` (description `"Claude Sonnet 4.6, Claude Opus 4.6, GPT-OSS 120B"`, 90% remaining) with no dedicated Argon group, and `agy models` returns 18 IDs including `gemini-4-carbon-high`, `gemini-4-argon-high`, `gemini-pro-orchestrator`, and `gemini-pro-orchestrator-argon`
When `fetch_quota_for_profile("nguyenhieu000690")` and `format_profile_for_dashboard("nguyenhieu000690", result)` execute
Then `groupModels["gemini"]` equals `["Gemini 4 Carbon", "Gemini 4 Argon", "Gemini 4 Hydrogen", "Orchestrator (Carbon)", "Orchestrator (Argon)", "Gemini 3.8 Flash"]` and `groupModels["claude"]` equals `["Claude Sonnet 4.6", "Claude Opus 4.6", "GPT-OSS 120B"]`
And `capabilities["argonMode"]` equals `"shared_gemini"`, `capabilities["badges"]` includes `"Carbon"`, `"Argon"`, and `"Orchestrator"`, and `hasArgon` is `True`
And `argonWeekly["sharedPool"]` is `True`, `argonWeekly["mode"]` equals `"shared_gemini"`, and `argonWeekly["remainingFraction"]` equals `0.85` with resetTime `"2026-11-24T00:00:00Z"`

Scenario: [CQRA-HP-02] [Tier A - Unit] Pro separate-Argon profile merges agy models catalog with /usage descriptions and preserves Claude 5.5 labels
Given an authenticated profile "danhdue" where `/usage` returns three quota groups `"Gemini Models"` (description `"Gemini 4 Hydrogen, Gemini 3.8 Flash"`, 100% remaining), `"Claude and GPT models"` (description `"Claude Opus 5.5, Claude Sonnet 5.5, GPT-OSS 120B"`, 80% remaining), and `"Gemini 4 Argon"` (`gemini-argon-wtu-weekly`, 45% remaining), and `agy models` additionally includes `gemini-pro-orchestrator-g1-pro`
When `fetch_quota_for_profile("danhdue")` and `format_profile_for_dashboard("danhdue", result)` execute
Then `capabilities["argonMode"]` equals `"separate"`, `capabilities["hasOrchestrator"]` is `True`, and `groupModels["claude"]` contains `"Claude Opus 5.5"`, `"Claude Sonnet 5.5"`, and `"GPT-OSS 120B"`
And `argonWeekly["sharedPool"]` is `False`, `argonWeekly["mode"]` equals `"separate"`, `argonWeekly["remainingFraction"]` equals `0.45`, and `modelCatalog` includes the reconciled `gemini-pro-orchestrator-g1-pro` entry

Scenario: [CQRA-HP-03] [Tier C - Integration] Quota dashboard Web UI renders dynamic badges, per-group rosters, and Shared Gemini Pool row without INACTIVE errors
Given an HTTP server serving `skills/check-quota/resources/dashboard/quota_dashboard.html` injected with formatted `shared_gemini` ("nguyenhieu000690") and `separate` ("danhdue") profiles
When headless Chrome loads the dashboard page and opens the profile info modal for "nguyenhieu000690"
Then the card header displays dynamic badges matching `capabilities["badges"]` (`Carbon`, `Argon`, `Orchestrator`) and zero uncaught browser console errors occur
And the Argon row inside "nguyenhieu000690" renders `"Shared w/ Gemini Pool"` alongside `85%` instead of `"INACTIVE"` or `"Unavailable N/A"`
And `#profile-info-modal` displays the full dynamic model lists for `Gemini Models`, `Claude & GPT`, and `Argon / Orchestrator`

Scenario: [CQRA-HP-04] [Tier A - Unit] Review prompts mandate Proposed suffix while run_external_review preserves 5-column tables and pre-fills triage actions
Given `skills/dev-implementation/references/external-review-prompt.md` and `skills/dev-implementation/references/local-review-prompt.md` alongside raw reviewer output containing `- [Important] scripts/app.py:42 — Stale cache key omits round id. Proposed: include round_num in cache key`
When `run_external_review.py` renders `review_results.md` via `render_round()`, validates it via `check()`, and generates `fix_plan_round1.md` via `triage()` plus `top_risk_findings_section()`
Then every row in `review_results.md` contains strictly 5 pipe-delimited columns passing `check()` with exit code `0`
And both `top_risk_findings_section()` output and generated `fix_plan_round1.md` pre-fill `Proposed action: include round_num in cache key` instead of `?`

Scenario: [CQRA-HP-05] [Tier C - Integration] Cross-Model Review parser and tasks_dashboard.html populate PROPOSED ACTION from inline prefixes, 6-col tables, and fix_plan_roundN fallback
Given a running `TasksServer` over a temporary repository containing epic `"duet_harmonize"` with Round 1 5-column `review_results.md` lacking inline `Proposed:` text paired with `fix_plan_round1.md` (`Summary Matrix` Action `"Align sidecar priority"` and `### Finding #1` `- **Proposed Action (Adjusted):** Enforce script > doc > sidecar precedence in ingest`), plus Round 2 containing `- [Minor] src/a.py:10 — Missing guard. Proposed: add early return`
When `GET /api/epic/history?repo=demo&epic=duet_harmonize&round_cross=1` is fetched and rendered in `tasks_dashboard.html` under headless Chrome
Then finding `#1` in Round 1 carries `"Enforce script > doc > sidecar precedence in ingest"` in `proposed_action` and renders that text in the `PROPOSED ACTION` cell of the Cross-Model Review table with zero `"—"` placeholder
And zero uncaught JavaScript console errors occur during modal and tab transitions
```

## Dimension 2 Edge Cases

```gherkin
Scenario: [CQRA-EC-01] [Tier A - Unit] Auth-needed and disabled profiles never invoke agy models subprocesses
Given profiles `"broken_auth"` with `AUTH NEEDED` status and `"banned_acct"` with `DISABLED` status, where `"banned_acct"` has a previously cached `availableModels` list `["gemini-4-hydrogen-high"]`
When `fetch_quota_for_profile()` and batch `all` processing run across both profiles
Then subprocess runner mocks receive zero calls invoking `agy models` for `"broken_auth"` or `"banned_acct"`
And `"banned_acct"` retains its cached `availableModels` without clearing existing metadata

Scenario: [CQRA-EC-02] [Tier A - Unit] Legacy cached payloads without new model fields and none-Argon accounts render safely on Web UI
Given one legacy cached profile object missing `groupModels`, `capabilities`, and `argonWeekly.sharedPool`, plus a Free-tier profile `"free_acct"` with `argonMode == "none"` and `argonWeekly.available == false`
When `renderProfileCard()` and `getProfileQuotaScore()` run against both profiles in a real browser DOM
Then the legacy profile renders fallback group headers without throwing a `TypeError` or blank DOM node
And `"free_acct"` does not display an active Argon badge or `"Shared w/ Gemini Pool"` indicator

Scenario: [CQRA-EC-03] [Tier A - Unit] Multi-prefix Problem extraction preserves problem text with colons and leaves empty action only when all sources omit proposals
Given a 5-column `review_results.md` row whose `Problem` cell ends with `; Suggestion: cache mtime per round file` and a 6-column table row having explicit `Proposed Action` column `"Use bounded helper"`, alongside a third row having `Flag edge case: null id` with no matching entry in `fix_plan_round1.md`
When `parse_review_results()` parses all three rows
Then Row 1 sets `proposed_action == "cache mtime per round file"` and `problem` excludes the `Suggestion:` tail, Row 2 preserves `proposed_action == "Use bounded helper"` separately from `decision`, and Row 3 yields `proposed_action == ""` while retaining `"Flag edge case: null id"` intact

Scenario: [CQRA-EC-04] [Tier A - Unit] External review triage falls back to question mark only for findings omitting Proposed suffix
Given two parsed findings in one review round where Finding #1 includes `. Proposed: clamp negative fraction` in its Problem cell and Finding #2 omits any `. Proposed:` suffix
When `triage()` generates the initial fix plan entries for the round
Then Finding #1 pre-fills `Proposed action: clamp negative fraction` while Finding #2 sets `Proposed action: ?`
```

## Dimension 3 State Transitions

```gherkin
Scenario: [CQRA-ST-01] [Tier A - Unit] Hybrid cache refreshes agy models on miss, signature change, 24h expiry, and single-profile refresh while skipping warm batch hits
Given an authenticated `"shared_gemini"` profile cached 2 hours ago with matching `groupDescSig`
When batch scan (`all`) runs once with unchanged `/usage` descriptions, then runs again after `/usage` `description` changes `groupDescSig`, then runs a third time after `modelsFetchedAt` ages past 24 hours, followed by single-profile `refresh` CLI command
Then batch run 1 invokes `agy models` 0 times, batch run 2 invokes `agy models` 1 time and updates `groupDescSig`, batch run 3 invokes `agy models` 1 time and refreshes `modelsFetchedAt`, and single-profile `refresh` invokes `agy models` 1 time and persists updated data via `update_cached_profile()`

Scenario: [CQRA-ST-02] [Tier A - Unit] Refresh-session ping suppresses Argon 7D ping on shared_gemini while preserving ping on inactive separate Argon
Given `refresh_session.py` inspecting two authenticated accounts after `/usage`: `"ultra_shared"` (`argonMode == "shared_gemini"` with active `"Gemini Models"` bucket) and `"pro_sep"` (`argonMode == "separate"` with inactive dedicated `"Gemini 4 Argon"` bucket)
When `ping_profile()` evaluates ping candidates for both profiles with mocked isolated CLI execution
Then `"ultra_shared"` triggers 0 `Argon 7D` model pings and records no spurious Argon failure
And `"pro_sep"` dispatches exactly 1 `Argon 7D` ping against `"gemini-argon"` candidate

Scenario: [CQRA-ST-03] [Tier A - Unit] Modifying fix_plan_roundN.md invalidates tasks_server review parse cache immediately via watch_paths
Given `parse_review_results(repo_dir, active_epic="demo_epic")` has cached a Round 1 result in `_REVIEW_PARSE_CACHE` where Finding #1 has `proposed_action == "Initial fix"`
When `.devtool/epic/demo_epic/fix_plan_round1.md` is edited on disk (with updated content and distinct mtime) to `"Updated fix action"` and `parse_review_results(repo_dir, active_epic="demo_epic")` is called again
Then `_REVIEW_PARSE_CACHE` detects the `watch_paths` signature delta and returns Finding #1 with `proposed_action == "Updated fix action"`
```

## Dimension 4 Architecture and Concurrency

```gherkin
Scenario: [CQRA-AR-01] [Tier A - Unit] Strictly independent per-profile quota isolation, ping suppression, and CLI table formatting
Given two Ultra profiles `"hoangcongtam690"` and `"nguyenhieu000690"` whose mocked `/usage` timestamps match, without invoking `retrieveUserQuotaSummary`
When `fetch_quota_for_profile()`, `execute_ping_profile()`, `print_dashboard_cards()`, and `print_all_summary(..., show_providers=True)` execute for both profiles
Then neither `fetch_quota_for_profile()` nor `format_profile_for_dashboard()` calls `retrieveUserQuotaSummary` or emits any cross-profile pool linkage field
And `execute_ping_profile()` suppresses standalone `Argon 7D` pings for both `shared_gemini` profiles while `print_all_summary()` prints `(Shared Gemini)` and mirrored percentages per profile independently

Scenario: [CQRA-AR-02] [Tier A - Unit] Frontend quota score avoids double-counting shared_gemini Argon bucket while preserving Argon filter match
Given profile data in `quota_dashboard.html` for `"nguyenhieu000690"` (`geminiWeekly.remainingFraction = 0.80`, `argonWeekly.remainingFraction = 0.80`, `argonWeekly.sharedPool = true`, `hasArgon = true`) alongside an identical `separate` profile where `argonWeekly.remainingFraction = 0.20` and `argonWeekly.sharedPool = false`
When `getProfileQuotaScore()` and the `argon` filter predicate evaluate both profiles
Then `"nguyenhieu000690"` matches the `argon` filter predicate without counting the shared `0.80` pool twice in aggregate weighted quota score, while the `separate` profile weights its independent `0.20` Argon pool separately
```

## Dimension 5 Fault Resilience

```gherkin
Scenario: [CQRA-FR-01] [Tier A - Unit] Malformed /usage group descriptions or agy models timeout degrade softly without crashing quota fetch
Given a profile whose `/usage` payload contains a group with `description: null` and an `agy models` subprocess invocation that raises `subprocess.TimeoutExpired`
When `fetch_quota_for_profile()` runs with fallback cache present
Then `fetch_quota_for_profile()` returns `available` quota buckets with empty/cached `groupModels` and `argonMode == "none"` (or cached mode) without raising an unhandled exception

Scenario: [CQRA-FR-02] [Tier A - Unit] Corrupted or incomplete usage probe in refresh_session.py degrades safely without firing false Argon pings
Given a mocked `_probe_profile_usage_and_models()` call returning empty groups (`{}`) and malformed `available_models` strings (`None` / empty output) for profile `"corrupt_probe"`
When `refresh_session.py` (`check_profile_has_argon()` and `ping_profile()`) executes
Then `check_profile_has_argon("corrupt_probe")` returns `False` and `ping_profile()` completes cleanly with `0` spurious `Argon 7D` pings and zero unhandled exceptions

Scenario: [CQRA-FR-03] [Tier C - Integration] Malformed fix_plan_roundN.md alongside valid review_results.md degrades per-file without breaking TasksServer endpoints
Given a running `TasksServer` over a temporary epic directory containing valid Round 1 5-column `review_results.md` alongside a truncated/corrupted `fix_plan_round1.md` containing invalid markdown table separators
When clients request both `GET /api/review?repo=demo&epic=broken_fp` and `GET /api/epic/history?repo=demo&epic=broken_fp`
Then both HTTP endpoints respond with status `200`, valid JSON `reviews` metadata, and cleanly extracted inline proposals (or `""`) without raising `500 Internal Server Error`
```
