---
id: "task_05_review_action_parser_ui_and_regression"
status: "backlog"
priority: "high"
assignee: null
epic: "check_quota_dynamic_models_and_review_action"
dueDate: null
created: "2026-11-18T03:11:00Z"
modified: "2026-11-18T03:11:00Z"
completedAt: null
labels: ["check-tasks", "http-api", "ui", "integration"]
order: "a5"
review_tier: "full"
---

# Task 5: `tasks_server.py` Multi-Strategy `Proposed Action` Extraction, `fix_plan` Fallback, Dashboard UI & Full Regression

Epic: [check_quota_dynamic_models_and_review_action](../epic/check_quota_dynamic_models_and_review_action/check_quota_dynamic_models_and_review_action.en.md)

## Requirement Analysis

Restore reliable `PROPOSED ACTION` extraction for both future and historical reviews inside `skills/check-tasks/resources/scripts/tasks_server.py`, verify rendering inside `skills/check-tasks/resources/dashboard/tasks_dashboard.html`, register all `CQRA` test suites in `scripts/verify.sh`, and run full cross-epic integration & regression verification:

1. **Multi-Strategy Extraction in `tasks_server.py::parse_review_results()` (`L525-L785`)**:
   - **Header-Aware Column Detection**: Inspect each round's markdown table header row so canonical 5-column tables (`# | Severity | File / Target | Problem | Decision`) AND explicit 6-column tables with a `Proposed Action` / `Action` column extract `proposed_action` separately from `decision`.
   - **Broadened Problem Prefix Extraction**: Expand regex extraction beyond `Proposed:\s*(.+)` to support `Proposed action:\s*(.+)`, `Fix:\s*(.+)`, and `Suggestion:\s*(.+)` (after `.`, `;`, or `—`), preserving problem colons when no proposal prefix matches and stripping only the proposal tail from `problem`.
   - **Round-Scoped `fix_plan_round<N>.md` Fallback**: When `proposed_action` remains empty for finding `#N` in round `<round_num>`, read `.devtool/epic/<epic>/fix_plan_round<round_num>.md` (then unnumbered `fix_plan.md` fallback):
     - Parse `### Finding #<N>` blocks for `- **Proposed Action (...):** <text>` (preferring detailed Finding prose).
     - Fall back to `## Summary Matrix` table rows mapping finding number `#` to `Action`.
     - Degrade safely per-finding on truncated/malformed fix-plan markdown without breaking HTTP `200` responses.
   - **Watch-Path Cache Invalidation**: Add discovered `fix_plan_round*.md` and `fix_plan.md` paths under the epic directory to `watch_paths` (`_file_stat_sig()` `L516-L524`) inside `_REVIEW_PARSE_CACHE` so edits immediately invalidate cached review payloads.
2. **Dashboard Table Rendering (`tasks_dashboard.html`)**:
   - Verify `buildReviewFindingsTableHtml()` (`L4050-L4089`), `formatReviewTokens()` (`L4017-L4048`), and `renderEpicHistoryReviewTab()` (`L4808-L4878`) display `f.proposed_action` cleanly across `Cross-Model Review` and `Principal Review` modals (rendering `—` only when all sources are empty) and tighten token formatting/CSS truncation if required without console errors.
3. **Suite Registration (`scripts/verify.sh`) & Acceptance Suite (`tests/test_cqra_review_action_e2e.py`)**:
   - Register all five `tests/test_cqra_*.py` suites inside `SUITES` (`scripts/verify.sh:L362-L445`) under Section `21`.
   - Cover scenarios `CQRA-HP-05`, `CQRA-EC-03`, `CQRA-ST-03`, and `CQRA-FR-03` including real `TasksServer` HTTP endpoints + headless Chrome CDP inspection of `Cross-Model Review` `PROPOSED ACTION` cells, plus sweep the full epic integration & regression matrix in `TIER-C`.

## Files

Allowed files:
- `skills/check-tasks/resources/scripts/tasks_server.py`
- `skills/check-tasks/resources/dashboard/tasks_dashboard.html`
- `scripts/verify.sh`
- `tests/test_cqra_review_action_e2e.py` (new)

Read-only context:
- `.devtool/epic/check_quota_dynamic_models_and_review_action/check_quota_dynamic_models_and_review_action.en.md` — Epic HLD & Parser Contracts
- `.devtool/epic/check_quota_dynamic_models_and_review_action/bdd_scenarios.en.md` — Canonical BDD Scenarios

## Design Rationale

Combining inline proposal parsing, header-aware column detection, `fix_plan_round<N>.md` fallback, and `watch_paths` cache invalidation guarantees both newly reviewed epics and historical epics (`duet_refrain_harmonization`) populate `PROPOSED ACTION` immediately without mutating historical `.devtool/epic/` files or breaking 5-column validation. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/check-tasks/resources/scripts/tasks_server.py`: `_discover_round_files` (L354-L376), `_collect_review_candidates` (L443-L483), `_scan_round_headings` (L489-L515), `_file_stat_sig` (L516-L524), `parse_review_results` (L525-L785), new _parse_fix_plan_actions
  - `skills/check-tasks/resources/dashboard/tasks_dashboard.html`: `formatReviewTokens` (L4017-L4048), `buildReviewFindingsTableHtml` (L4050-L4089), `renderEpicHistoryReviewTab` (L4808-L4878)
  - `scripts/verify.sh`: `SUITES` (L362-L445)
  - `tests/test_cqra_review_action_e2e.py`: new server + Chrome CDP E2E acceptance suite
- **Downstream Callers**: `tests/test_check_tasks_server.py`, `tests/test_cehm_history_aggregator.py`, `tests/test_cehm_dashboard_modal_ui.py`, `tests/test_cehm_e2e_cdp.py`, `tests/test_rsdh_tasks_dashboard_ui.py`.
- **Cross-Platform Bridges**: JSON REST endpoints `GET /api/review` and `GET /api/epic/history` consumed by `tasks_dashboard.html`.
- **Target Test Coverage Threshold**: 100% of 5/6-col extraction, multi-prefix regex, `fix_plan_round<N>.md` fallback, cache invalidation, malformed markdown safety, and full cross-epic integration regression.

### BDD SCENARIOS

Covers: CQRA-HP-05, CQRA-EC-03, CQRA-ST-03, CQRA-FR-03

```gherkin
Scenario: [CQRA-HP-05] [Tier C - Integration] Cross-Model Review parser and tasks_dashboard.html populate PROPOSED ACTION from inline prefixes, 6-col tables, and fix_plan_roundN fallback
Given a running `TasksServer` over a temporary repository containing epic `"duet_harmonize"` with Round 1 5-column `review_results.md` lacking inline `Proposed:` text paired with `fix_plan_round1.md` (`Summary Matrix` Action `"Align sidecar priority"` and `### Finding #1` `- **Proposed Action (Adjusted):** Enforce script > doc > sidecar precedence in ingest`), plus Round 2 containing `- [Minor] src/a.py:10 — Missing guard. Proposed: add early return`
When `GET /api/epic/history?repo=demo&epic=duet_harmonize&round_cross=1` is fetched and rendered in `tasks_dashboard.html` under headless Chrome
Then finding `#1` in Round 1 carries `"Enforce script > doc > sidecar precedence in ingest"` in `proposed_action` and renders that text in the `PROPOSED ACTION` cell of the Cross-Model Review table with zero `"—"` placeholder
And zero uncaught JavaScript console errors occur during modal and tab transitions

Scenario: [CQRA-EC-03] [Tier A - Unit] Multi-prefix Problem extraction preserves problem text with colons and leaves empty action only when all sources omit proposals
Given a 5-column `review_results.md` row whose `Problem` cell ends with `; Suggestion: cache mtime per round file` and a 6-column table row having explicit `Proposed Action` column `"Use bounded helper"`, alongside a third row having `Flag edge case: null id` with no matching entry in `fix_plan_round1.md`
When `parse_review_results()` parses all three rows
Then Row 1 sets `proposed_action == "cache mtime per round file"` and `problem` excludes the `Suggestion:` tail, Row 2 preserves `proposed_action == "Use bounded helper"` separately from `decision`, and Row 3 yields `proposed_action == ""` while retaining `"Flag edge case: null id"` intact

Scenario: [CQRA-ST-03] [Tier A - Unit] Modifying fix_plan_roundN.md invalidates tasks_server review parse cache immediately via watch_paths
Given `parse_review_results(repo_dir, active_epic="demo_epic")` has cached a Round 1 result in `_REVIEW_PARSE_CACHE` where Finding #1 has `proposed_action == "Initial fix"`
When `.devtool/epic/demo_epic/fix_plan_round1.md` is edited on disk (with updated content and distinct mtime) to `"Updated fix action"` and `parse_review_results(repo_dir, active_epic="demo_epic")` is called again
Then `_REVIEW_PARSE_CACHE` detects the `watch_paths` signature delta and returns Finding #1 with `proposed_action == "Updated fix action"`

Scenario: [CQRA-FR-03] [Tier C - Integration] Malformed fix_plan_roundN.md alongside valid review_results.md degrades per-file without breaking TasksServer endpoints
Given a running `TasksServer` over a temporary epic directory containing valid Round 1 5-column `review_results.md` alongside a truncated/corrupted `fix_plan_round1.md` containing invalid markdown table separators
When clients request both `GET /api/review?repo=demo&epic=broken_fp` and `GET /api/epic/history?repo=demo&epic=broken_fp`
Then both HTTP endpoints respond with status `200`, valid JSON `reviews` metadata, and cleanly extracted inline proposals (or `""`) without raising `500 Internal Server Error`
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cqra_review_action_e2e.py::test_cqra_hp_05_cross_model_proposed_action_cdp_e2e` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cqra_review_action_e2e.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_check_tasks_server.py tests/test_cehm_history_aggregator.py tests/test_cehm_dashboard_modal_ui.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_cqra_review_action_e2e.py && ruff check --select E9,F63,F7,F821,F841,B007,B904 skills/check-tasks/resources/scripts/tasks_server.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && mypy skills/check-tasks/resources/scripts/tasks_server.py tests/test_cqra_review_action_e2e.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/cqra-integration.xml tests/test_cqra_quota_discovery.py tests/test_cqra_refresh_session_argon.py tests/test_cqra_external_review_proposed.py tests/test_cqra_quota_ui.py tests/test_cqra_review_action_e2e.py tests/test_agy_quota.py tests/test_check_tasks_server.py tests/test_cehm_history_aggregator.py tests/test_cehm_dashboard_modal_ui.py tests/test_rsdh_quota_modal_stack.py tests/test_claude_quota.py` | exit 0; results build/test-results/cqra-integration.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- When both `### Finding #<N>` `- **Proposed Action (...):**` text and `## Summary Matrix` `Action` column exist in `fix_plan_round<N>.md`, `### Finding #<N>` takes precedence and `Summary Matrix` serves as secondary fallback.
- Cache invalidation includes every discovered `fix_plan_round*.md` and `fix_plan.md` inside `watch_paths` monitored by `_file_stat_sig()` inside `_REVIEW_PARSE_CACHE`.
- `build/test-results/cqra-integration.xml` is written by `V6` (`TIER-C`) matching the HLD `Integration results:` contract.
- `scripts/verify.sh` `SUITES` registers all five `tests/test_cqra_*.py` suites under Section `21`.

## Definition of Done

- Scenarios CQRA-HP-05, CQRA-EC-03, CQRA-ST-03, and CQRA-FR-03 pass cleanly across unit, HTTP, and Chrome CDP tests with zero console errors. (V2, V6)
- `scripts/verify.sh` includes all five `tests/test_cqra_*.py` suites cleanly under `SUITES`. (V6)
- Existing review/dashboard suites and the full cross-epic `TIER-C` regression matrix pass cleanly with `build/test-results/cqra-integration.xml` written. (V3, V4, V5, V6)

## Dependencies & Blockers

Blocked by [Task 1](../epic/check_quota_dynamic_models_and_review_action/task_01_check_quota_dynamic_models_and_argon_mode.md), [Task 2](../epic/check_quota_dynamic_models_and_review_action/task_02_refresh_session_shared_argon_guard.md), [Task 3](../epic/check_quota_dynamic_models_and_review_action/task_03_review_prompts_and_triage_prefill.md), [Task 4](../epic/check_quota_dynamic_models_and_review_action/task_04_quota_dashboard_dynamic_ui.md).

Downstream dependents (blocked by Task 5): None.

## References & Rollback

- [Epic HLD](../epic/check_quota_dynamic_models_and_review_action/check_quota_dynamic_models_and_review_action.en.md)
- **Rollback**: Revert task commit to restore `skills/check-tasks/resources/scripts/tasks_server.py`, `skills/check-tasks/resources/dashboard/tasks_dashboard.html`, and `scripts/verify.sh`.
