# Principal Review: check_quota_dynamic_models_and_review_action

## Round 1

- **Date**: 2026-11-17T20:39:30Z
- **SHA**: 62590e08e600ce5f27c1891488feb3fcc1c1f8ed
- **Base**: main
- **CLI**: claude
- **Model**: opus
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal
- **Raw log**: `build/reviews/check_quota_dynamic_models_and_review_action_principal_round1_62590e0.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | bdd_scenarios.en.md:CQRA-HP-01, CQRA-HP-02, CQRA-AR-02 and task_01_check_quota_dynamic_models_and_argon_mode.md:Requirement Analysis §2 | The scenarios assert `argonWeekly["remainingFraction"]`, and Task 01 mirrors `remainingPct`, `usedPct`, `remainingStr`, `resetStr`, `status` and `available`. The dashboard bucket the code actually emits uses `name`, `fraction`, `countdown`, `resetTime`, `resetTimeLocal`, `unavailable` and `tags` (`scripts/agy_quota.py:2697-2734`), and `quota_dashboard.html` reads `.fraction` (L2704, L2715; `remainingFraction` appears 0 times). Only the stale `quota_dashboard.types.ts:20` declares `remainingFraction`, so the RED/GREEN tests would assert keys nothing produces. Proposed: rewrite the scenarios and the Task 01 mirror list to the real keys (`fraction`, `countdown`, `resetTime`, `resetTimeLocal`, `unavailable`), and add a Task 01 decision to align `QuotaBucket` in `quota_dashboard.types.ts` with the emitted shape. | fixed in f008eba |
| 2 | Important | 2026-11-18-check-quota-dynamic-models-and-review-action-design.en.md:§3.4 Quota Score, task_04_quota_dashboard_dynamic_ui.md:Requirement Analysis §3 and bdd_scenarios.en.md:CQRA-AR-02 | `getProfileQuotaScore()` (`quota_dashboard.html:2875-2891`) already ignores `argonWeekly`; it scores `(g5+c5+gw+cw)/4`. There is no double-count to fix, the shared-pool assertion passes before any change, and "separate profile weights its independent 0.20 Argon pool" would add a new term that changes sorting for every separate-Argon profile. Proposed: restate the goal as "score formula unchanged; Argon stays excluded", and rewrite CQRA-AR-02 to assert equal scores for both profiles plus an `argon` filter match through `hasArgon`. | fixed in f008eba |
| 3 | Important | task_01_check_quota_dynamic_models_and_argon_mode.md:Impact Analysis & Blast Radius and task_02_refresh_session_shared_argon_guard.md:Decisions Already Made | Setting `hasArgon = true` and mirroring `argonWeekly` (`unavailable: false`) for `shared_gemini` turns on the cached-fallback Argon paths no task lists: `execute_ping_profile()`'s cached branch (`agy_quota.py:2908-2920`, which leads to `should_ping_argon`), `probe_blocked_profile()` (`agy_quota.py:753`, which sends a `gemini-4-argon-low` prompt) and `check_profile_has_argon()` (`refresh_session.py:1306-1324`, which feeds the `ping_profile` fallback). That fires the redundant Argon pings Goal 3 forbids. CQRA-FR-02 also assumes `check_profile_has_argon()` reads the mocked probe, but it reads cached dashboard HTML. Proposed: add `probe_blocked_profile` and the cached branch to Task 01 targets, and decide that every fallback gates Argon on cached `capabilities.argonMode == "separate"` (or `argonWeekly.sharedPool != true`). Rewrite CQRA-FR-02 to patch `_DASHBOARD_HTML_CANDIDATES` with a shared_gemini cache entry and assert 0 Argon pings. | fixed in f008eba |
| 4 | Important | task_01_check_quota_dynamic_models_and_argon_mode.md:Decisions Already Made | `capabilities.badges` must include `ULTRA`, but no derivation rule exists. `format_profile_for_dashboard()` sets only `PRO`/`FREE` (`agy_quota.py:2621-2622`), and `execute_ping_profile()` compares `tier == "PRO"`/`"FREE"` (L2881, L2910). Changing top-level `tier` to `ULTRA` would quietly turn off the default-available buckets. Proposed: add a decision naming the ULTRA source (e.g. `/usage` `plan_name` containing `ULTRA`, or no dedicated Argon group plus a Carbon model) that sets only `capabilities.tier`, with top-level `tier` staying `PRO`/`FREE`. | fixed in f008eba |
| 5 | Important | task_01_check_quota_dynamic_models_and_argon_mode.md:BDD CQRA-ST-01 / Verification V2 | The scenario requires persistence through `update_cached_profile()`. That writes the repo-tracked `quota_dashboard.html` (`get_dashboard_html_path()`, `agy_quota.py:1174`) and sync copies under `~/antigravity_homes/huynhminhtien0510/...` (L2541-2544), which breaks the HLD Verification Environment's forbidden-store rule unless patched. Proposed: add a decision that tests patch `update_cached_profile` (or `get_dashboard_html_path` and the sync-copy list) to a `tmp_path` and assert the call, never the real file. | fixed in f008eba |
| 6 | Important | task_03_review_prompts_and_triage_prefill.md:Requirement Analysis §2, bdd_scenarios.en.md:CQRA-HP-04 and CQRA-EC-04 | `triage()` only prints a skeleton to stdout (`run_external_review.py:2623`) and never writes `fix_plan_round<N>.md`. That file is drafted by an LLM in `lifecycle_runner.py:1767` (`_draft_fix_plan`, not in Allowed files) or written by Role 2.2. Proposed: change the scenarios and Task 03 to assert the pre-filled `Proposed action` cell in `triage()` stdout (the 7-column triage table at L2559-2562 and `top_risk_findings_section()`), not a generated `fix_plan_round1.md`. | fixed in f008eba |
| 7 | Important | task_05_review_action_parser_ui_and_regression.md:Requirement Analysis §1 and the Spec §4.3.3 fallback | The format the fallback parses (`### Finding #N` + `- **Proposed Action (...):**` + `## Summary Matrix`) appears in none of the repo's four fix plans. Those use `### Fix N [Important #3]`, `## Planned Fixes` and `\| # \| … \| Planned Surgical Fix \|` (`.devtool/epic/{check_tasks_dashboard,runtime_sync_and_dashboard_hardening,token_throttling_optimization}/fix_plan_round*.md`), and nothing pins a template. Proposed: either pin a canonical fix-plan section (a `\| # \| … \| Proposed action \|` table copied from the triage skeleton) as a decision with the writer named, or widen the fallback to the observed `### Fix N [<Sev> #N]` and `Planned Surgical Fix` variants, labelled best-effort. | fixed in f008eba |
| 8 | Important | 2026-11-18-check-quota-dynamic-models-and-review-action-design.en.md:§4.2.2, task_03_review_prompts_and_triage_prefill.md:Decisions Already Made and task_05_review_action_parser_ui_and_regression.md:Requirement Analysis §1 | These name the persisted header `\| # \| Severity \| File / Target \| Problem \| Decision \|`, but `render_round()` emits `\| # \| Severity \| Location \| Problem \| Decision \|` (`run_external_review.py:1307`), and `tasks_server.py:717` detects the table by `Severity`. Header-aware mapping keyed on `File / Target` would miss every real table. Proposed: replace `File / Target` with `Location` in all three places, and tell Task 05 to map columns by header name for `Location` and `Proposed Action`/`Action`, falling back to positions. | fixed in f008eba |
| 9 | Important | task_05_review_action_parser_ui_and_regression.md:Decisions Already Made (watch_paths) | Watching only *discovered* fix-plan files misses the usual sequence, where `fix_plan_round<N>.md` is created after `review_results.md` has been parsed and cached (`tasks_server.py:770-782`). The cached `—` would persist until another watched file changes. Proposed: always add the expected `fix_plan_round<round>.md` and `fix_plan.md` paths to `watch_paths` (`_file_stat_sig` gives `None` for a missing file, so creation still invalidates the cache), and extend CQRA-ST-03 with a create-after-cache case. | fixed in f008eba |
| 10 | Important | check_quota_dynamic_models_and_review_action.en.md:Impact Analysis and the task_03/task_04/task_05 Impact Analysis line anchors | Every `quota_dashboard.html` anchor is already off by +22 lines (`getTierBadgeHTML` is at L2252, not L2230; also `renderProfileCard` L2399, `getProfileQuotaScore` L2875, `isProfileSchedulable` L3162, `openProfileInfoModal` L4252). The queued-ahead `four_persona_governance` task_04 (`run_external_review.py`) and task_05 (`tasks_server.py`, `tasks_dashboard.html`) edit the same files, so the "CLEAN" claim will not hold at promotion and the anchors will trigger Stop-and-Report. Proposed: record the file overlap with `four_persona_governance` task_04 and task_05 in the HLD Impact Analysis and Rollout. Require re-baselining anchors (symbol-only, or `--revise`) when the epic is promoted, and fix the current `quota_dashboard.html` ranges now. | fixed in f008eba |
| 11 | Minor | task_03_review_prompts_and_triage_prefill.md:Requirement Analysis §2 and task_05_review_action_parser_ui_and_regression.md:Requirement Analysis §1 | Two separate proposal-extraction implementations are specified with no shared regex. The existing `tasks_server.py:736` pattern has no word boundary (matches `Unproposed:`) and takes the first marker. Proposed: pin one regex in both tasks' Decisions, e.g. `(?:^\|[.;—]\s*)\b(?:Proposed(?:\s+action)?\|Fix\|Suggestion):\s*(.+)$` applied to the last match. | fixed in f008eba |
| 12 | Minor | 2026-11-18-check-quota-dynamic-models-and-review-action-design.en.md:§1.2 item 3 | This says the parser uses only `Proposed:\s*(.+)`, but `tasks_server.py:736` already accepts `Proposed Action` and `Đề xuất`. Proposed: correct the root-cause wording. | fixed in f008eba |
| 13 | Minor | bdd_scenarios.en.md:CQRA-HP-05 | The Round 2 Given uses a raw list-format finding line, but persisted `review_results.md` rounds contain 5-column table rows, and the Then never asserts Round 2. Proposed: express Round 2 as a table row `\| 1 \| Minor \| src/a.py:10 \| Missing guard. Proposed: add early return \|  \|` and assert its `proposed_action`. | fixed in f008eba |

Raw output:

```text
Verdict: CHANGES REQUIRED
```

## Round 2

- **Date**: 2026-11-17T21:32:50Z
- **SHA**: 1a179794fe36de5d4f93026a1932052ca0748337
- **Base**: main
- **CLI**: claude
- **Model**: opus
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal
- **Scope**: delta from round 1 (62590e0)
- **Raw log**: `build/reviews/check_quota_dynamic_models_and_review_action_principal_round2_1a17979.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | task_05_review_action_parser_ui_and_regression.md:Decisions Already Made (fix_plan fallback) and bdd_scenarios.en.md:CQRA-EC-03 | [INCOMPLETE_FIX] the pinned `### Fix N` form `- **Action:** <text>` (inline, colon inside bold) does not match the repo's real fix plans, which use `- **Action**:` with a multi-line bullet body (`check_tasks_dashboard/fix_plan_round1.md:15-21`) or a numbered `N. **Finding #N (...)**:` heading whose body starts on the next line (`runtime_sync_and_dashboard_hardening/fix_plan_round2.md:8`), so historical plans still produce an empty `proposed_action`. Proposed: accept `**Action**:` and `**Action:**` (colon on either side of the bold), capture the following indented/bullet lines up to the next `###` heading, `- **` key or numbered item, and add an EC-03 fixture row copied verbatim from `check_tasks_dashboard/fix_plan_round1.md` `### Fix 3 [Important #3]`. | fixed in 211ef6a |
| 2 | Minor | task_03_review_prompts_and_triage_prefill.md:Decisions Already Made and task_05_review_action_parser_ui_and_regression.md:Decisions Already Made (shared marker regex) | the corpus probe shows the last-`finditer()` rule mis-splits a proposal that quotes a marker inside a code span: this epic's own `principal_review.md` Round 1 #13 row yields `add early return \\|  \\|` and assert …` instead of `express Round 2 as a table row …`. Proposed: ignore marker matches that fall inside backtick code spans before taking the last match; this also fixes the Round 1 #11 row that the old regex mis-split. | fixed in 211ef6a |
| 3 | Minor | bdd_scenarios.en.md:CQRA-EC-02 and task_04_quota_dashboard_dynamic_ui.md:CQRA-EC-02 | the Given still uses the non-emitted key `argonWeekly.available == false`, while the dashboard and the revised HLD §3.2 use `argonWeekly.unavailable` (`quota_dashboard.html:3101`). Proposed: change it to `argonWeekly.unavailable == true` to match the corrected #1 sibling scenarios. | fixed in 211ef6a |
| 4 | Minor | task_01_check_quota_dynamic_models_and_argon_mode.md:Decisions Already Made (ULTRA tier derivation) | `plan_name` is computed in `fetch_quota_for_profile()` (`agy_quota.py:954`) but not returned (L958-964), so `format_profile_for_dashboard()` cannot see it, and no source anywhere emits a `DEV` tier. Proposed: state that `fetch_quota_for_profile()` returns `plan_name` in its result dict, and either name the `DEV` source or drop `DEV` from the derivation rule. | fixed in 211ef6a |

Raw output:

```text
Verdict: CHANGES REQUIRED
```

## Round 3

- **Date**: 2026-11-17T21:51:27Z
- **SHA**: 161968967c019434a1a40e86a3afb28b3f1cd154
- **Base**: main
- **CLI**: claude
- **Model**: opus
- **Thinking**: high
- **Status**: completed
- **Verdict**: PASS
- **Kind**: principal
- **Scope**: convergence from round 2 (1a17979)
- **Raw log**: `build/reviews/check_quota_dynamic_models_and_review_action_principal_round3_1619689.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Minor | 2026-11-18-check-quota-dynamic-models-and-review-action-design.en.md:§3.2 Tier derivation (L94), task_01_check_quota_dynamic_models_and_argon_mode.md:Requirement Analysis §1 (L32) and task_04_quota_dashboard_dynamic_ui.md:Requirement Analysis (L25) | [INCOMPLETE_FIX] Round 2 #4 dropped `DEV` only from task_01's Decisions Already Made, from Spec §2.1/§3.4 and from the HLD. These three places still say `"DEV" if DEV` and "top-level tier PRO/FREE (or DEV)", or list `DEV` among the badges. That contradicts the pinned rule that `"DEV"` is dropped. The source has no `DEV` emitter: `agy_quota.py:956` sets `tier` only to `"FREE"`/`"PRO"`. Proposed: remove `DEV` from all three lines so they match task_01's Decisions Already Made. |  |
| 2 | Minor | bdd_scenarios.en.md:CQRA-EC-03 and task_05_review_action_parser_ui_and_regression.md:CQRA-EC-03 | The revised Row 4 is now finding `#3`, and it matches `### Fix 3 [Important #3]`. Row 3's finding number is not stated. If someone writes Row 3 as `#3` (the natural reading of "Row 3"), the `(round, finding_num)` fallback fills its `proposed_action` from Fix 3, and the assertion `Row 3 yields proposed_action == ""` fails. Proposed: give Row 3 an explicit number with no fix-plan entry, e.g. `\| 5 \| Minor \| src/c.py:5 \| Flag edge case: null id \|  \|`. |  |

Raw output:

```text
Verdict: PASS
```
