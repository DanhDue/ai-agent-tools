---
id: "task_04_check_tasks_harvester_bottleneck_and_pic_backend"
status: "todo"
priority: "high"
assignee: null
epic: "runtime_sync_and_dashboard_hardening"
dueDate: null
created: "2026-11-13T09:18:00Z"
modified: "2026-11-13T09:18:00Z"
completedAt: null
labels: ["backend", "harvester", "pic-sync", "check-tasks"]
order: "a4"
review_tier: "full"
---

# Task 4: Check-Tasks Harvester, Ledger Union, 96% Backend, and PIC Sync

Epic: [runtime_sync_and_dashboard_hardening](../epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md)

## Requirement Analysis

Fix false-positive approval bottlenecks, incomplete gate ledger resolution, runtime state ingestion, `96%` pre-finish percentage backend, and root + worktree PIC assignment in the `check-tasks` backend:

1. **Idle False-Positive Elimination & Ledger Union (`skills/check-tasks/resources/scripts/check_tasks.py`)**:
   - In `resolve_active_epic()` (`L434-L537`), remove **Strategy 7** (`L519-L536`) alphabetical `.devtool/epic/` fallback (`choosing_a_lifecycle`) when no active branch, active worktree, active `features/` task, or active `pending_decision.json` exists, while **preserving Strategy 6** (`L508-L517`) `.devtool/features/` scan and returning `None` cleanly on idle repositories.
   - In `parse_gate_ledger_entries()` (`L1007-L1065`), merge gate approval records across both `gate_ledger.jsonl` and `GATE_LEDGER.md` from both primary root and active worktree (deduplicating cleanly without letting an older `gate_ledger.jsonl` shadow newer `GATE_LEDGER.md` approvals).
   - In `derive_lifecycle_state()` (`L1076-L1266`) and `scan_repo()` (`L1296-L1366`):
     - Ingest namespaced `.devtool/state/pending_decision.json` (`decisions[active_epic]` with legacy single-record fallback), `.devtool/state/<slug>.heartbeat.json`, and namespaced `.devtool/state/quality_active.json` (`runs[run_id]`) via `_state_envelope` into `RepoMetadata` (`L183-L202` optional fields `pending_decision`, `heartbeat`, `quality_active`, `quality_runs` defaulting to `None`/`[]`).
     - Expire stale `"running"` quality entries whose `now - updated_at > ttl_sec` OR local dead `pid` (`status = "stale"`) so crashed runs never leave permanent `"running"` banners, and surface concurrent live runs in `quality_runs` alongside the active epic's matched `quality_active`.
     - If matching epic `pending_decision.active` is True, surface its explicit `reason`/`stage` (`is_human_action_required = True`); ignore pending decisions belonging to unrelated sibling epics; otherwise remove the implicit `Approve Gate 1 (Design Spec)` heuristic (`L1240-L1258`) for idle folders without active worktree/tasks, and update `tests/test_check_tasks_fsm.py::test_stage_1_inception` (`L150-L162`) to assert `IDLE`/`False` when `pending_decision.json` is absent plus a positive test with `pending_decision.json` present.
     - Apply backend `96%` pre-finish / `95%` in-progress cap in `extract_task_progress` / `scan_repo` (`100%` only on Gate 4 converged `Waiting Finish` / Gate 5 `Done`).
     - Update `extract_epic_pic()` (`L1268-L1294`) to check both active worktree and root `handoff.md` (`- **PIC / Assigned Profile**:`) + HLD while ignoring placeholder values (`<unassigned>`, `<profile_account_id>`, `None`, `null`).
2. **Root + Worktree PIC Reassignment (`skills/check-tasks/resources/scripts/tasks_server.py`)**:
   - Refactor `assign_epic_pic()` (`L520-L678`) to:
     - Validate `new_pic` strictly against `^[a-zA-Z0-9_\-]+$` (raising `ValueError` on invalid input) and ensure epic slug stays within repo boundaries, AND wrap the `assign_epic_pic` call in `TasksHandler.do_POST` (`L799-L812` inside `do_POST` `L788-L865`) with `except ValueError as exc: self._send_json(400, {"status": "error", "error": str(exc)})` so `POST /api/epic/pic` cleanly returns HTTP `400` rather than HTTP `500`.
     - Discover all matching worktrees via `git worktree list --porcelain` (matching branch `epic/<slug>` or worktree folder `<epic_dir>`/`<slug>`).
     - Update PIC atomically in **both** primary root and matched worktrees across **PIC-bearing files only**: HLD (`<epic>.en.md`, `<epic>.vi.md`, design spec metadata), `handoff.md` (including `- **PIC / Assigned Profile**:`), `task_*.md` in `.devtool/epic/<epic>/` & `.devtool/features/`, `.devtool/state/<slug>.pipeline.json`, `<slug>.heartbeat.json`, and worktree `.vscode/settings.json`.
     - Explicitly skip review and BDD prose artifacts (`bdd_scenarios.*`, `principal_review.md`, `review_results.md`, `fix_plan_*.md`, `manual_smoke_checklist.md`) and never mutate sibling epics or unrelated directories.
     - Catch per-file permission/IO errors gracefully, returning warnings alongside accurate `updated_files` count.
3. Add `tests/test_rsdh_harvester_and_pic.py` covering `RSDH-HP-06`, `RSDH-EC-04`, `RSDH-EC-05`, `RSDH-ST-02`, `RSDH-ST-04`, `RSDH-AR-03` (concurrent `quality_runs`, `ttl_sec`/dead-PID stale expiry, and multi-epic `pending_decision` isolation), and `RSDH-FR-04`.

## Files

Allowed files:
- `skills/check-tasks/resources/scripts/check_tasks.py`
- `skills/check-tasks/resources/scripts/tasks_server.py`
- `tests/test_check_tasks_fsm.py`
- `tests/test_rsdh_harvester_and_pic.py` (new)

Read-only context:
- `.devtool/epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md` — HLD Module Contracts (§4.5, §4.6)
- `.devtool/epic/runtime_sync_and_dashboard_hardening/bdd_scenarios.en.md` — Canonical BDD Scenarios
- `scripts/_state_envelope.py` — Shared envelope reader (Task 1)

## Design Rationale

Idle false positives occur because `check_tasks.py` falls back alphabetically onto dormant `.devtool/epic/` folders, while `assign_epic_pic()` misses worktree copies and `handoff.md` profile formats and mutates unrelated markdown files. Scoping `assign_epic_pic()` to strict PIC-bearing files across both root and matched git worktrees eliminates cross-epic drift cleanly. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/check-tasks/resources/scripts/check_tasks.py`: `RepoMetadata` (L183-L202), `resolve_active_epic` (L434-L537), `parse_gate_ledger_entries` (L1007-L1065), `derive_lifecycle_state` (L1076-L1266), `extract_epic_pic` (L1268-L1294), `scan_repo` (L1296-L1366)
  - `skills/check-tasks/resources/scripts/tasks_server.py`: `assign_epic_pic` (L520-L678), `TasksHandler.do_POST` (L788-L865)
  - `tests/test_check_tasks_fsm.py`: `test_stage_1_inception` (L150-L162)
  - `tests/test_rsdh_harvester_and_pic.py`: new unit and integration suite for `RSDH-HP-06`, `RSDH-EC-04`, `RSDH-EC-05`, `RSDH-ST-02`, `RSDH-ST-04`, `RSDH-AR-03`, `RSDH-FR-04`
- **Downstream Callers**: `skills/check-tasks/resources/dashboard/tasks_dashboard.html` (`/api/tasks`, `/api/epic/pic`), `tests/test_check_tasks_server.py`, `tests/test_check_tasks_fsm.py`, `tests/test_check_tasks_harvester.py`, `tests/test_check_tasks_e2e.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of idle fallback removal, ledger union, concurrent `quality_runs` & stale-owner expiry recovery, multi-epic `pending_decision` isolation, worktree+root PIC file filtering, invalid PIC HTTP `400` rejection, and partial IO warning branches.

### BDD SCENARIOS

Covers: RSDH-HP-06, RSDH-EC-04, RSDH-EC-05, RSDH-ST-02, RSDH-ST-04, RSDH-AR-03, RSDH-FR-04


```gherkin
Scenario: [RSDH-HP-06] [Tier C - Integration] PIC reassignment synchronizes root and worktree PIC-bearing files while preserving review and BDD prose

Given a repository with epic artifacts in both primary root .devtool/epic/demo_epic/ and an active git worktree .worktrees/demo_epic/, including handoff.md ("- **PIC / Assigned Profile**: ..."), HLD, task_*.md, bdd_scenarios.en.md, and principal_review.md
When tasks_server.py assign_epic_pic updates the epic PIC from "mommy" to "brother"
Then both root and worktree HLD, handoff.md, task_*.md (under epic and features), pipeline/heartbeat JSON files, and worktree .vscode/settings.json update to "brother"
And bdd_scenarios.en.md and principal_review.md remain byte-for-byte unchanged without injected PIC bullets

Scenario: [RSDH-EC-04] [Tier A - Unit] Check-Tasks harvester leaves idle repositories without active worktrees or tasks in Idle state

Given a git repository containing legacy unstarted folders under .devtool/epic/ (including choosing_a_lifecycle) with zero worktrees, zero features/ tasks, and no pending_decision.json
When check_tasks.resolve_active_epic and check_tasks.derive_lifecycle_state evaluate that repository
Then resolve_active_epic returns None and derive_lifecycle_state returns Idle with is_human_action_required False

Scenario: [RSDH-EC-05] [Tier A - Unit] PIC reassignment validates profile names and isolates sibling epics across worktrees

Given a repository with two distinct epics (demo_epic and sibling_epic) having separate directories and worktrees behind a live TasksServer HTTP endpoint
When tasks_server.assign_epic_pic is called directly and via POST /api/epic/pic with malformed PIC "../bad", and then called with valid PIC "tess" for "demo_epic"
Then the direct assign_epic_pic call raises ValueError without modifying any files and POST /api/epic/pic returns HTTP 400 with {"status": "error", ...} rather than HTTP 500
And the valid update changes only demo_epic across root and its matched worktree while leaving all sibling_epic files untouched

Scenario: [RSDH-ST-02] [Tier C - Integration] Gate ledger unification merges root and worktree JSONL and GATE_LEDGER.md entries

Given a repository whose older gate_ledger.jsonl records Gate 1 while active worktree GATE_LEDGER.md (or root GATE_LEDGER.md) contains newer Gate 2 and Gate 3 approvals
When check_tasks.parse_gate_ledger_entries inspects the repository
Then all Gates 1, 2, and 3 are returned without short-circuiting on gate_ledger.jsonl

Scenario: [RSDH-ST-04] [Tier A - Unit] extract_epic_pic resolves PIC across root and worktree handoff placeholders cleanly

Given an active epic whose root HLD has no PIC yet while its active worktree handoff.md contains "- **PIC / Assigned Profile**: @danhdue" (or "<unassigned>")
When check_tasks.extract_epic_pic inspects the repository
Then the valid worktree PIC "danhdue" is extracted cleanly and placeholder tokens like "<unassigned>" return None

Scenario: [RSDH-AR-03] [Tier C - Integration] Check-tasks harvester isolates multi-epic decisions, exposes live quality_runs, and expires stale owners

Given quality_active.json containing one active live run, one dead-PID/expired-TTL stale running entry, plus pending_decision.json with multiple namespaced epic decisions
When check_tasks.scan_repo inspects the repository
Then expired/dead-PID runs transition to status "stale" without rendering permanent running banners, active concurrent runs surface via quality_runs, and active_epic resolves only its matching namespaced pending_decision

Scenario: [RSDH-FR-04] [Tier C - Integration] Partial read-only failure during PIC reassignment reports warnings without corrupting sibling files

Given an epic containing both writable metadata files and a simulated unwritable path or missing optional state file during PIC assignment
When tasks_server.assign_epic_pic executes
Then writable target files still update cleanly, warnings identify the failed path, and JSON responses reflect accurate updated_files counts
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_harvester_and_pic.py::test_rsdh_hp_06_pic_root_worktree_sync` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_harvester_and_pic.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_check_tasks_server.py tests/test_check_tasks_fsm.py tests/test_check_tasks_harvester.py tests/test_check_tasks_cli.py tests/test_check_tasks_e2e.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_check_tasks_fsm.py tests/test_rsdh_harvester_and_pic.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_4.xml tests/test_rsdh_harvester_and_pic.py tests/test_check_tasks_server.py tests/test_check_tasks_fsm.py` | exit 0; results build/test-results/task_4.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `assign_epic_pic()` updates ONLY HLD (`<epic>.{en,vi}.md`, design specs), `handoff.md` (`- **PIC / Assigned Profile**:` & `- **PIC**:`), `task_*.md` in `.devtool/epic/<epic>/` & `.devtool/features/`, `.pipeline.json`, `.heartbeat.json`, and worktree `.vscode/settings.json`; it NEVER injects PIC headers into `bdd_scenarios.*`, `principal_review.md`, `review_results.md`, `fix_plan_*.md`, or `manual_smoke_checklist.md`.
- `tests/test_check_tasks_fsm.py::test_stage_1_inception` (`L150-L162`) is re-pinned to expect `IDLE`/`False` when `pending_decision.json` is absent on bare `.devtool/epic/` folders, alongside a new positive test verifying `STAGE_1_INCEPTION`/`True` when `pending_decision.json` is present.
- `resolve_active_epic()` removes Strategy 7 (`L519-L536`) alphabetical dormant-folder fallback while keeping Strategy 6 (`L508-L517`) `.devtool/features/` scan intact; explicit epic-namespaced `pending_decision.json` (`decisions[active_epic]`) overrides heuristics for human-action flags without surfacing sibling epic pauses.
- `scan_repo()` expires any `quality_active.json` `"running"` entry whose `ttl_sec` has elapsed or whose same-host `pid` is no longer alive to `"stale"` and exposes concurrent live runs in `quality_runs` alongside `quality_active`.
- `TasksHandler.do_POST` (`L799-L812`) wraps `assign_epic_pic()` with `except ValueError as exc:` -> HTTP `400 {"status": "error", "error": str(exc)}` so invalid PIC validation stays safe at the HTTP boundary.
- `extract_epic_pic()` also ignores placeholder tokens such as `<unassigned>`, `<profile_account_id>`, `None`, and `null` so unpopulated templates never surface as fake PICs.
- `check_tasks.py` and `tasks_server.py` carry pre-existing `mypy` and global-config `ruff` findings elsewhere, so V4/V5 scope to registered `.agents/quality/python-quality.json` targets + touched tests while keeping newly modified functions cleanly typed and `ruff`-clean.

## Definition of Done

- Scenarios RSDH-HP-06, RSDH-EC-04, RSDH-EC-05, RSDH-ST-02, RSDH-ST-04, RSDH-AR-03, and RSDH-FR-04 pass across temp git repos, worktrees, and HTTP API tests. (V2, V6)
- All existing check-tasks server, FSM, harvester, CLI, and E2E suites pass cleanly. (V3, V6)
- Ruff lint and registered mypy checks pass cleanly. (V4, V5)
- Worktree PIC synchronization and idle elimination verified on candidate commit. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 1](../epic/runtime_sync_and_dashboard_hardening/task_01_runtime_state_envelope_and_two_tier_sync.md) and [Task 3](../epic/runtime_sync_and_dashboard_hardening/task_03_wave_parallel_handoff_stage3_revise_and_pool_cleanup.md).

Downstream dependent (blocked by Task 4): `task_07`.

## References & Rollback

- [Epic HLD](../epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md), Module Contracts (§4.5, §4.6).
- **Rollback**: Revert task commit; restores prior `check_tasks.py` and `tasks_server.py` and removes `tests/test_rsdh_harvester_and_pic.py`.
