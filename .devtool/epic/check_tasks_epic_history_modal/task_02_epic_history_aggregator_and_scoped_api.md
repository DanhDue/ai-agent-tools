---
id: "task_02_epic_history_aggregator_and_scoped_api"
status: "todo"
priority: "high"
assignee: null
epic: "check_tasks_epic_history_modal"
dueDate: null
created: "2026-11-15T01:00:00Z"
modified: "2026-11-15T01:00:00Z"
completedAt: null
labels: ["check-tasks", "harvester", "http-api", "review-isolation"]
order: "a2"
review_tier: "full"
---

# Task 2: Epic History Aggregator, Scoped Review Lookup, and `/api/epic/history` Endpoint

Epic: [check_tasks_epic_history_modal](check_tasks_epic_history_modal.en.md)

## Requirement Analysis

Build the on-demand multi-source epic history harvester in `skills/check-tasks/resources/scripts/check_tasks.py` and expose it alongside strict epic-scoped review lookup via `GET /api/epic/history` in `skills/check-tasks/resources/scripts/tasks_server.py`:

1. **Multi-Source Harvester (`skills/check-tasks/resources/scripts/check_tasks.py`)**:
   - Add `_collect_slug_variants(epic_slug)` enumerating ordered unique variants across `epic_slug`, `epic_slug.replace("_", "-")`, and `epic_slug.replace("-", "_")`.
   - Implement `harvest_epic_history(repo_path: Path, epic_slug: str) -> dict[str, Any]` keeping `extract_task_progress()` (`L1374-L1515`) and `/api/tasks` overview scanning fast and untouched for legacy callers:
     - Resolve epic status/metadata from `harvest_epics_overview()` (`L1110-L1215`), matching worktrees (`_find_epic_dirs_for_checkout()` `L2236`), `.devtool/state/`, `.devtool/logs/`, and `.devtool/archive/`.
     - Reconstruct heartbeat via `_merge_epic_heartbeats()`: load all live and archived `<variant>.heartbeat.json` / `heartbeat_<variant>_*.json` files, pick the winning snapshot by `(generation, updated_at)` and union their `events`, and merge `.devtool/logs/events_<variant>*.jsonl` + `.devtool/archive/events_<variant>*.jsonl`.
     - Compute `pipeline_telemetry` using `build_epic_pipeline_telemetry()` (`L2611-L3175`) with resolved task counts, gate approvals, `heartbeat`, `quality_active`, `pending_decision`, and `is_completed`.
     - Parse task cards (`parse_frontmatter` `L336`, `natural_sort_key` `L1284`): prefer worktree `.devtool/features/` when `status == "in_progress"` (matching `extract_task_progress`), otherwise `.devtool/epic/<variant>/task_*.md` in canonical order, attaching `evidence/<task_id>.json` summaries (`head`, `started`, `finished`, `passed_rows`, `total_rows`, and bounded verification rows with `output_tail` capped at `<= 8` lines) while tolerating corrupt evidence JSON (`evidence: None`).
     - Build unified UTC-sorted `timeline` (`_build_unified_timeline()`) combining `events_log`, `heartbeat`, `gate_ledger`, `activity_log`, and `evidence` records, deduplicating overlapping ring-buffer entries against `events_*.jsonl` (preferring richer `events_log` entries) and returning `log_completeness`: `"full_stream" | "snapshot_and_ledger" | "none"`.
     - Tolerate malformed JSONL lines or corrupted markdown/JSON without raising unhandled exceptions (`CEHM-EC-01`, `CEHM-FR-01`).
2. **Strict Epic Review Scoping & HTTP Route (`skills/check-tasks/resources/scripts/tasks_server.py`)**:
   - Extend `parse_review_results(repo_dir, active_epic=None, target_round=None, kind=None, *, strict_epic: bool = False)` (`L339-L625`) so `strict_epic=True` excludes repo-root `.devtool/principal_review.md` and `.devtool/review_results.md` fallback candidates, searching strictly under worktree/root `.devtool/epic/<variant>/` directories, and includes `"present": bool(review_file)` (returning `"verdict": "UNKNOWN"`, `"findings": []`, `"present": False` when absent). Keep `/api/review` backward compatible while optionally honoring `&strict=1`.
   - Register `GET /api/epic/history` inside `TasksHandler.do_GET()` (`L1214-L1290`):
     - Require `repo` and `epic`, validate slug with `_EPIC_SLUG_RE` (`L629`) and repository path containment via `_assert_contained(..., self.server.workspace_root, "repo")` (`L76-L82`), rejecting missing params (`400`) or path traversal (`400`/`404`) and unknown repo/epic (`404`).
     - Invoke `harvest_epic_history()` and `parse_review_results(..., strict_epic=True)` for both `kind="principal"` (`round_principal`) and `kind="cross-model"` (`round_cross`), returning HTTP `200` JSON with `{success, epic, pipeline_telemetry, tasks, timeline, reviews, log_completeness}`.
3. **Unit & Server Integration Suite (`tests/test_cehm_history_aggregator.py`)**:
   - Cover scenarios `CEHM-HP-02`, `CEHM-HP-03`, `CEHM-EC-01`, `CEHM-EC-02`, `CEHM-ST-01`, `CEHM-AR-03`, and `CEHM-FR-01`.

## Files

Allowed files:
- `skills/check-tasks/resources/scripts/check_tasks.py`
- `skills/check-tasks/resources/scripts/tasks_server.py`
- `tests/test_cehm_history_aggregator.py` (new)

Read-only context:
- `.devtool/epic/check_tasks_epic_history_modal/check_tasks_epic_history_modal.en.md` — HLD & API Schema
- `.devtool/epic/check_tasks_epic_history_modal/bdd_scenarios.en.md` — Canonical BDD Scenarios

## Design Rationale

Computing complete epic forensics on demand inside `GET /api/epic/history` keeps regular 5-second `/api/tasks` polling lightweight while giving the dashboard strict cross-epic isolation (`strict_epic=True`), legacy artifact stitching across `-`/`_` variants, and fault tolerance for malformed files. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/check-tasks/resources/scripts/check_tasks.py`: `harvest_epics_overview` (L1110-L1215), `extract_task_progress` (L1374-L1515), `_read_epic_heartbeat` (L1890-L1927), `build_epic_pipeline_telemetry` (L2611-L3175), `parse_frontmatter` (L336), `get_completed_epic_slugs` (L556), `_normalize_slug` (L625), `_collect_devtool_dirs` (L711), `natural_sort_key` (L1284), `_find_epic_dirs_for_checkout` (L2236), `scan_repo` (L3195), new `harvest_epic_history`, new `_collect_slug_variants`, new `_merge_epic_heartbeats`, new `_build_unified_timeline`
  - `skills/check-tasks/resources/scripts/tasks_server.py`: `parse_review_results` (L339-L625), `TasksHandler` (`do_GET` L1214-L1290), `TasksServer` (`workspace_root` L1411-L1427), `_assert_contained` (L76-L82), `_EPIC_SLUG_RE` (L629)
  - `tests/test_cehm_history_aggregator.py`: new unit and HTTP server integration test suite
- **Downstream Callers**: `skills/check-tasks/resources/dashboard/tasks_dashboard.html`, `tests/test_check_tasks_server.py`, `tests/test_ltsp_harvester_pipeline.py`, `tests/test_rsdh_harvester_and_pic.py`.
- **Cross-Platform Bridges**: JSON REST contract `GET /api/epic/history` consumed by `tasks_dashboard.html`.
- **Target Test Coverage Threshold**: 100% of `harvest_epic_history`, `strict_epic=True` isolation, and `/api/epic/history` error codes covered.

### BDD SCENARIOS

Covers: CEHM-HP-02, CEHM-HP-03, CEHM-EC-01, CEHM-EC-02, CEHM-ST-01, CEHM-AR-03, CEHM-FR-01

```gherkin
Scenario: [CEHM-HP-02] [Tier C - Integration] History aggregator stitches multi-source artifacts across hyphen and underscore variants for Done epics
Given a repository with completed epic "alignment_flow_hardening" in `PROJECT_LEDGER.md`, `.devtool/state/alignment-flow-hardening.heartbeat.json`, `.devtool/archive/heartbeat_alignment_flow_hardening_20261114_1200.json`, `.devtool/state/gate_ledger.jsonl`, `.devtool/archive/activity_alignment_flow_hardening_20261114_1200.log`, `task_01_alpha.md`, and `evidence/task_01_alpha.json`
When `harvest_epic_history(repo_path, "alignment_flow_hardening")` executes
Then the returned `epic["status"]` equals `"done"` and `pipeline_telemetry["stages"][5]["status"]` equals `"done"`
And `tasks` includes `"task_01_alpha"` with attached `evidence` summary `passed_rows`, `total_rows`, and `head` SHA
And `timeline` contains merged chronological events from `gate_ledger`, `heartbeat`, `activity_log`, and `evidence` sorted by UTC timestamp

Scenario: [CEHM-HP-03] [Tier C - Integration] History HTTP endpoint returns 6-stage summary, tasks, timeline, and both Principal and Cross-Model reviews
Given a running `TasksServer` over a temporary workspace containing repository "demo_repo" and epic "hist_epic" with `principal_review.md` (Round 1 and Round 2) and `review_results.md` (Round 1)
When a client requests `GET /api/epic/history?repo=demo_repo&epic=hist_epic&round_principal=2&round_cross=1`
Then HTTP status is 200 and JSON `reviews["principal"]["round"]` equals 2 with `available_rounds == [1, 2]`
And `reviews["cross_model"]["round"]` equals 1 with `present is True` and parsed `findings` rows
And `pipeline_telemetry["stages"]` contains 6 stages matching `compute_pipeline_telemetry`

Scenario: [CEHM-EC-01] [Tier A - Unit] Unstarted Backlog and Packaged epics without logs, tasks, or reviews return clean empty history structures
Given a repository containing `.devtool/epic/draft_epic/2026-11-15-draft-epic-design.en.md` with no `task_*.md`, no `gate_ledger.jsonl` entry, no `events_*.jsonl`, and no review markdown
When `harvest_epic_history(repo_path, "draft_epic")` runs and `/api/epic/history?repo=<repo>&epic=draft_epic` is queried
Then HTTP status is 200 with `tasks == []`, `timeline == []`, `log_completeness == "none"`, and `reviews["principal"]["present"] is False` and `reviews["cross_model"]["present"] is False`
And `pipeline_telemetry["stages"]` returns all 6 stages with zero unhandled exceptions

Scenario: [CEHM-EC-02] [Tier A - Unit] Strict epic review lookup refuses falling back to unrelated repo-root review files
Given a repository where repo-root `.devtool/principal_review.md` and `.devtool/review_results.md` exist for `"other_epic"`, while `.devtool/epic/legacy_oct_epic/` has no review markdown files
When `parse_review_results(repo_path, active_epic="legacy_oct_epic", kind="cross-model", strict_epic=True)` executes
Then `result["present"]` equals `False` and `result["findings"]` equals `[]` and `result["verdict"]` equals `"UNKNOWN"`
And repo-root `review_results.md` content for `"other_epic"` is never leaked into `"legacy_oct_epic"`

Scenario: [CEHM-ST-01] [Tier A - Unit] Unified timeline deduplicates ring-buffer overlap with events JSONL and labels stream completeness
Given an epic `"stream_epic"` whose archived `events_stream-epic_*.jsonl` contains 22 entries (`e01`..`e22`) and whose `heartbeat` snapshot repeats trailing `e15`..`e22`, alongside a separate legacy epic `"snap_epic"` having only a 3-event `.heartbeat.json`
When `harvest_epic_history` aggregates `"stream_epic"` and `"snap_epic"`
Then `"stream_epic"` reports `log_completeness == "full_stream"` and contains all 22 unique step entries with zero duplicated `e15`..`e22` entries
And `"snap_epic"` reports `log_completeness == "snapshot_and_ledger"` and preserves all 3 heartbeat entries ordered deterministically by UTC timestamp

Scenario: [CEHM-AR-03] [Tier C - Integration] History HTTP handler rejects missing query params with 400 and path traversal attempts with 400 or 404
Given a running `TasksServer` bound to an isolated temporary `workspace_root`
When requests arrive for `/api/epic/history?repo=demo` (missing `epic`), `/api/epic/history?repo=../etc&epic=passwd`, and `/api/epic/history?repo=demo&epic=../../secret`
Then the server responds with HTTP 400 or 404 JSON error payloads and accesses zero files outside `workspace_root`

Scenario: [CEHM-FR-01] [Tier A - Unit] Malformed JSONL lines or corrupted evidence JSON fail softly per record without aborting epic history
Given an epic `"corrupt_epic"` containing one valid event line and one truncated JSON line `{bad` in `.devtool/logs/events_corrupt-epic.jsonl`, plus one malformed `evidence/task_01_broken.json` file alongside `task_01_broken.md`
When `harvest_epic_history(repo_path, "corrupt_epic")` executes
Then valid timeline events and `task_01_broken` markdown metadata are still returned cleanly with `evidence: null` on the broken task and zero raised exceptions
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cehm_history_aggregator.py::test_cehm_hp_02_stitch_legacy_done_epic` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cehm_history_aggregator.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_check_tasks_server.py tests/test_ltsp_harvester_pipeline.py tests/test_rsdh_harvester_and_pic.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/check-tasks/resources/scripts/check_tasks.py tests/test_cehm_history_aggregator.py && ruff check --select F821,F841,B,E9 skills/check-tasks/resources/scripts/tasks_server.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/check-tasks/resources/scripts/check_tasks.py skills/check-tasks/resources/scripts/tasks_server.py tests/test_cehm_history_aggregator.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/cehm_task_02.xml tests/test_cehm_history_aggregator.py tests/test_check_tasks_server.py tests/test_ltsp_harvester_pipeline.py` | exit 0; results build/test-results/cehm_task_02.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `harvest_epic_history(repo_path: Path, epic_slug: str) -> dict[str, Any]` returns keys `"epic"`, `"pipeline_telemetry"`, `"tasks"`, `"timeline"`, and `"log_completeness"`, reusing `build_epic_pipeline_telemetry()` (`L2611-L3175`) without modifying `/api/tasks` overview behavior (`extract_task_progress` continues skipping archived `Done` tasks in polling snapshots).
- `parse_review_results(repo_dir, active_epic=None, target_round=None, kind=None, *, strict_epic: bool = False)` (`tasks_server.py:L339-L625`) excludes repo-root `.devtool/principal_review.md` and `.devtool/review_results.md` fallback paths whenever `strict_epic=True` and sets `"present": bool(review_file)`.
- `GET /api/epic/history` validates `repo` containment under `self.server.workspace_root` via `_assert_contained()` and rejects missing/unsafe `epic` query strings before invoking `harvest_epic_history()`.
- `timeline` entries normalize timestamps to ISO-8601 UTC (`...Z`), deduplicate overlapping trailing `heartbeat` items when identical `(message, stage, sub_step)` entries already exist from `events_log`, and sort chronologically.

## Definition of Done

- Scenarios CEHM-HP-02, CEHM-HP-03, CEHM-EC-01, CEHM-EC-02, CEHM-ST-01, CEHM-AR-03, and CEHM-FR-01 pass cleanly. (V2, V6)
- Existing harvester and server test suites pass without regression. (V3, V6)
- Ruff checks and mypy typecheck pass cleanly across `check_tasks.py`, `tasks_server.py`, and `tests/test_cehm_history_aggregator.py`. (V4, V5)

## Dependencies & Blockers

Blocked by [Task 1](task_01_append_only_event_stream_and_archival.md).

Downstream dependents (blocked by Task 2): `task_03`, `task_04`.

## References & Rollback

- [Epic HLD](check_tasks_epic_history_modal.en.md)
- **Rollback**: Revert task commit to restore `check_tasks.py` and `tasks_server.py`.
