---
id: "task_03_wave_parallel_handoff_stage3_revise_and_pool_cleanup"
status: "todo"
priority: "high"
assignee: null
epic: "runtime_sync_and_dashboard_hardening"
dueDate: null
created: "2026-11-13T09:18:00Z"
modified: "2026-11-13T09:18:00Z"
completedAt: null
labels: ["architecture", "workflow", "worktree", "handoff"]
order: "a3"
review_tier: "full"
---

# Task 3: Wave Handoff, Stage 3 Revise Fix, Pool Cleanup, and Choice A CLI

Epic: [runtime_sync_and_dashboard_hardening](runtime_sync_and_dashboard_hardening.en.md)

## Requirement Analysis

Upgrade handoff instructions to wave-parallel orchestration, fix Stage 3 `package_epic.py --revise`, automate worker pool cleanup, and enforce Choice A approval-bottleneck tracking and compact rules across lifecycle skills:

1. **Wave-Parallel Handoff, Creator Profile PIC Detection & Choice A CLI (`scripts/resume_context.py`, `handoff-template.md`, `package_epic.py`)**:
   - Update `emit_handoff_prompt` (`mode == "implement"` L1770-L1785) in `scripts/resume_context.py` and `skills/dev-lifecycle/references/handoff-template.md` to instruct: computing waves (`compute_execution_order.py <epic_slug> --parallel`), running `estimate_heartbeat.py`, running multi-task waves in parallel pool slots (`manage_worker_pool.py` / `workspace:"share"`), running `manage_worker_pool.py cleanup` after waves, and running Gate 4 + Cross-Model Review.
   - Add `detect_current_profile()` + `--detect-profile` CLI flag in `scripts/resume_context.py` (`sync_window_title` L480-L725, CLI parser L2045-L2145 & main L2215-L2315): prioritize Antigravity profile folder name (`AGY_PROFILE` / `ANTIGRAVITY_PROFILE` -> `/antigravity_homes/<profile>` -> running IDE `--user-data-dir` / `workspaceStorage` -> `.vscode/settings.json` `[@profile]` -> `USER`) before `extract_email_id_from_profile`, and normalize `-`/`_` in `epic_candidates` (`L500-L507`) so hyphenated/underscored epic slugs match workspace storage cleanly.
   - Stamp creator profile automatically as initial PIC (`- **PIC**: <profile>` / `- **PIC / Assigned Profile**: @<profile>`) in `package_epic.py` (when generating `handoff.md` from `handoff-template.md`, falling back to `detect_current_profile()` and never emitting literal `<profile_account_id>`), `skills/dev-brainstorming/SKILL.md`, and `skills/dev-designer/SKILL.md`.
   - Add `--pending-decision "<reason>"`, `--decision-kind <kind>`, and `--clear-decision` CLI flags (`L2045-L2145`, `L2260-L2315`) writing/clearing `.devtool/state/pending_decision.json` across shared devtool dirs via `_state_envelope.py`. Automatically clear `pending_decision.json` when `--gate` records approval (`record_gate_approval` L846-L887) or `--state` sets a non-paused execution status (`Executing`, `Stage 3`, etc.).
2. **Stage 3 `--revise` Contract Compatibility (`package_epic.py`, `check_epic_readiness.py`, `check_task_contract.py`)**:
   - Add `--allow-existing-done-new` to `check_task_contract.py` (`check_allowed` L145-L174, `check_evidence` L175-L201, `check_task` L603-L630, `main` L718-L775): when `--design --allow-existing-done-new` is active, **only** tasks with status `done` or `review` skip the `<pattern> is marked (new) but already exists` error on Allowed Files and Evidence files; pre-done tasks still fail if `(new)` collides on disk.
   - Add `--post-design` to `check_epic_readiness.py` (`check_preflight` L123-L224, `run_checks` L897-L923, `main` L1021-L1107) forwarding `--allow-existing-done-new` to `check_task_contract.py --design`.
   - In `package_epic.py` (`package_epic` L268-L372), when `--revise` runs on an epic that has entered Stage 3 (Gate 3 in `gate_ledger.jsonl` / `GATE_LEDGER.md` OR any task in status `in-progress`, `review`, `done`), invoke `check_epic_readiness.py <epic_dir> --post-design`; also auto-clear `pending_decision.json` on package completion.
3. **Worker Pool & Branch Land Cleanup (`manage_worker_pool.py`, `integrate_branch.py`)**:
   - Enhance `cleanup_slots()` (`L227-L275`) and `main()` (`L280-L381`) in `manage_worker_pool.py` to support `--stale-only`, force-remove `.worktrees/<epic>-slot-*`, run `git worktree prune`, delete temporary slot branches (`epic/<slug>-slot-*` and `worker/<epic>/slot-*`), and strip cleared slot entries from `.devtool/state/<epic_slug>.heartbeat.json` (preserving `get_slot_branch` existing naming for unit tests).
   - Invoke orphan slot cleanup in `integrate_branch.py` (`cmd_land` L413-L450) right after successful branch merge landing.
4. **Governance & Prompt Sync (`rules/CRITICAL_RULES.md` + Stage 1–4 Skills)**:
   - Update `skills/dev-implementation/SKILL.md` (`L182-L215` — mandate estimator + `manage_worker_pool.py cleanup` before Phase 4), `skills/dev-brainstorming/SKILL.md` (`L118-L250`), `skills/dev-designer/SKILL.md`, `skills/principal-review/SKILL.md`, `skills/cross-model-review/SKILL.md`, `skills/finishing-a-development-branch/SKILL.md` (`L115-L165`), and `rules/CRITICAL_RULES.md` with Choice A `--pending-decision` save-on-pause / clear-on-resume rules, tightening wording where needed so `rules/CRITICAL_RULES.md <= 8192` UTF-8 bytes and `skills/dev-designer/SKILL.md <= 22528` UTF-8 bytes.
5. Add `tests/test_rsdh_orchestration.py` covering `RSDH-HP-04`, `RSDH-HP-05`, `RSDH-EC-03`, `RSDH-EC-08`, `RSDH-ST-01`, `RSDH-ST-03`, and `RSDH-FR-03`.

## Files

Allowed files:
- `scripts/resume_context.py`
- `skills/dev-lifecycle/references/handoff-template.md`
- `skills/dev-implementation/resources/scripts/package_epic.py`
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- `skills/dev-implementation/resources/scripts/manage_worker_pool.py`
- `skills/finishing-a-development-branch/resources/scripts/integrate_branch.py`
- `skills/dev-implementation/SKILL.md`
- `skills/dev-brainstorming/SKILL.md`
- `skills/dev-designer/SKILL.md`
- `skills/principal-review/SKILL.md`
- `skills/cross-model-review/SKILL.md`
- `skills/finishing-a-development-branch/SKILL.md`
- `rules/CRITICAL_RULES.md`
- `tests/test_rsdh_orchestration.py` (new)

Read-only context:
- `.devtool/epic/runtime_sync_and_dashboard_hardening/runtime_sync_and_dashboard_hardening.en.md` — HLD Module Contracts (§4.3–§4.5)
- `.devtool/epic/runtime_sync_and_dashboard_hardening/bdd_scenarios.en.md` — Canonical BDD Scenarios
- `scripts/_state_envelope.py` — Shared envelope API (Task 1)

## Design Rationale

Fixing Stage 3 `--revise` without relaxing pre-implementation Stage 2 `--design` prevents false passes while unblocking in-flight HLD revisions. Pairing Choice A `pending_decision` auto-clear across CLI/gates/tasks with automatic slot cleanup closes orphaned worktree and stale bottleneck leaks systematically without bloating `CRITICAL_RULES.md` beyond 8 KB. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/resume_context.py`: `sync_window_title` (L480-L725), `record_gate_approval` (L846-L887), `emit_handoff_prompt` (L1770-L1790), `main` CLI parser & handlers (L2045-L2145, L2215-L2315)
  - `skills/dev-lifecycle/references/handoff-template.md`: small file (`78` lines `<= 200`), parallel wave execution & creator PIC stamping template
  - `skills/dev-implementation/resources/scripts/package_epic.py`: `package_epic` (L268-L372)
  - `skills/dev-implementation/resources/scripts/check_epic_readiness.py`: `check_preflight` (L123-L224), `run_checks` (L897-L923), `main` (L1021-L1107)
  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `check_allowed` (L145-L174), `check_evidence` (L175-L201), `check_task` (L603-L630), `main` (L718-L775)
  - `skills/dev-implementation/resources/scripts/manage_worker_pool.py`: `cleanup_slots` (L227-L275), `main` (L280-L381)
  - `skills/finishing-a-development-branch/resources/scripts/integrate_branch.py`: `cmd_land` (L413-L450)
  - `skills/dev-implementation/SKILL.md`: `Phase 2 — Parallel Task Execution` & cleanup (L182-L215)
  - `skills/dev-brainstorming/SKILL.md`: Gate 1 human pause, creator PIC stamping & recording (L118-L250)
  - `skills/finishing-a-development-branch/SKILL.md`: `Step 5` archival & cleanup (L115-L165)
  - Small (`<= 200` lines) doc targets: `skills/dev-designer/SKILL.md` (`98`), `skills/principal-review/SKILL.md` (`105`), `skills/cross-model-review/SKILL.md` (`120`), `rules/CRITICAL_RULES.md` (`80`)
  - `tests/test_rsdh_orchestration.py`: new unit and integration suite for `RSDH-HP-04`, `RSDH-HP-05`, `RSDH-EC-03`, `RSDH-EC-08`, `RSDH-ST-01`, `RSDH-ST-03`, `RSDH-FR-03`
- **Downstream Callers**: `test_package_and_revise_epic.py`, `test_manage_worker_pool.py`, `test_check_epic_readiness.py`, `test_check_task_contract.py`, `test_integrate_branch.py`, `test_token_throttling_acceptance.py`, `scripts/verify.sh`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of Stage 3 `--post-design` gate detection, cleanup branches (`--stale-only` & `land`), Choice A pause/clear transitions, creator profile `--detect-profile` priority, and `CRITICAL_RULES.md` byte budget guard.

### BDD SCENARIOS

Covers: RSDH-HP-04, RSDH-HP-05, RSDH-EC-03, RSDH-EC-08, RSDH-ST-01, RSDH-ST-03, RSDH-FR-03


```gherkin
Scenario: [RSDH-HP-04] [Tier C - Integration] Wave-parallel handoff prompt and template instruct parallel execution and cleanup

Given a packaged epic ready for Stage 3 implementation in an isolated git worktree
When resume_context.py --emit-prompt implement --epic demo-sync executes and skills/dev-lifecycle/references/handoff-template.md is rendered
Then both instruct the programmer orchestrator to run compute_execution_order.py --parallel, run estimate_heartbeat.py per wave and before Gate 4, execute multi-task waves across parallel pool slots, and invoke manage_worker_pool.py cleanup afterward
And neither emits instructions forcing strictly sequential one-task-at-a-time execution for independent waves

Scenario: [RSDH-HP-05] [Tier C - Integration] Worker pool cleanup removes slot worktrees, prunes refs, deletes slot branches, and clears heartbeat slots

Given a git repository with initialized 2-slot worker pool worktrees (.worktrees/demo_epic-slot-1 and slot-2), temporary slot branches, and active slot entries in demo-epic.heartbeat.json
When manage_worker_pool.py cleanup --epic-dir demo_epic --epic-slug demo-epic runs
Then both slot worktree directories and both slot branch refs (epic/<slug>-slot-* and worker/<epic>/slot-*) are deleted and pruned
And .devtool/state/demo-epic.heartbeat.json contains an empty slots mapping without deleting non-slot epic metadata

Scenario: [RSDH-EC-03] [Tier C - Integration] Stage 3 package_epic --revise accepts completed (new) files while Stage 2 design remains strict

Given a Stage 3 epic where task_01 is status "done" referencing an already-created "(new)" file in Allowed Files and Evidence, alongside an unstarted Stage 2 epic whose todo task references an already-existing "(new)" file
When package_epic.py --revise runs on the Stage 3 epic and check_epic_readiness.py runs natively on the Stage 2 epic
Then the Stage 3 revision enables --post-design / --allow-existing-done-new and exits 0
And the Stage 2 readiness check retains strict --design enforcement and exits non-zero on the colliding todo "(new)" path

Scenario: [RSDH-EC-08] [Tier A - Unit] Epic creator profile is automatically detected and stamped as initial PIC

Given an active Antigravity profile environment where AGY_PROFILE (or profile folder /antigravity_homes/brother) runs alongside an HLD containing "- **PIC**: brother" and an active workspace slug with mixed "-" and "_" separators
When resume_context.py --detect-profile and sync_window_title run and package_epic.py generates handoff.md from handoff-template.md
Then --detect-profile outputs "brother" prioritizing folder profile name over email prefix, sync_window_title writes "[@brother]" into .vscode/settings.json without failing on "-" vs "_" slug differences, and generated handoff.md stamps "- **PIC / Assigned Profile**: @brother" rather than "<profile_account_id>"

Scenario: [RSDH-ST-01] [Tier C - Integration] Choice A pending_decision flags pause cleanly and clears automatically on confirmation or resume

Given an epic paused awaiting human confirmation via resume_context.py --pending-decision "Confirm Gate 2" --decision-kind gate_2_choice
When check_tasks.scan_repo inspects the repo before and after running --gate 2 (or --clear-decision, non-paused --state, sync_task_status in-progress, or package_epic)
Then pending_decision.json initially sets is_human_action_required True with the recorded prompt
And each resume/confirmation trigger removes pending_decision.json across root and worktree so is_human_action_required flips back to False

Scenario: [RSDH-ST-03] [Tier C - Integration] Stale worker pool pruning and branch landing clean orphaned slot resources safely

Given a repository whose slot-1 worktree folder was manually removed on disk while its git worktree admin metadata and slot branch still exist, alongside an epic ready for integrate_branch.py land
When manage_worker_pool.py cleanup --stale-only and integrate_branch.py cmd_land execute
Then git worktree prune and branch cleanup remove orphaned slot metadata/branches cleanly without failing on missing directories

Scenario: [RSDH-FR-03] [Tier C - Integration] Updated Choice A and cleanup rules keep CRITICAL_RULES.md within the 8192-byte prompt cap

Given edits adding Choice A pending-decision and worker-pool cleanup governance across rules/CRITICAL_RULES.md and Stage 1-4 SKILL.md files
When UTF-8 byte size of rules/CRITICAL_RULES.md and scripts/verify.sh §1-§10 are checked
Then rules/CRITICAL_RULES.md remains strictly <= 8192 UTF-8 bytes and all static link, ToC, frontmatter, and orphan-reference checks pass
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_orchestration.py::test_rsdh_ec_03_stage3_revise_vs_stage2_strict` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_rsdh_orchestration.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_task_contract.py && python3 -m unittest skills/dev-implementation/resources/scripts/test_manage_worker_pool.py skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py scripts/test_resume_context.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/resume_context.py skills/dev-implementation/resources/scripts/package_epic.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/manage_worker_pool.py tests/test_rsdh_orchestration.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/resume_context.py skills/dev-implementation/resources/scripts/package_epic.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/manage_worker_pool.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_3.xml tests/test_rsdh_orchestration.py tests/test_multi_epic_governance_acceptance.py` | exit 0; results build/test-results/task_3.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `rules/CRITICAL_RULES.md` currently occupies `7760` bytes (cap `<= 8192`); tighten redundant prose when adding Choice A pause/clear & pool cleanup rules so final UTF-8 size stays `<= 8192` bytes, and run `bash scripts/verify.sh --quiet` (§1–§10 link/frontmatter/ToC checks) to confirm zero broken links.
- `--allow-existing-done-new` is passed ONLY by `package_epic.py --revise` (via `check_epic_readiness.py --post-design`) when Gate 3 exists or >= 1 task is `in-progress`/`review`/`done`, and exempts ONLY `done`/`review` tasks.
- Preserve existing `get_slot_branch()` return format (`epic/<slug>-slot-<N>`) so `test_manage_worker_pool.py` remains green while `cleanup_slots()` cleans both `epic/<slug>-slot-*` and `worker/<epic>/slot-*` branch patterns plus `git worktree prune` and `heartbeat.json` slots.
- `integrate_branch.py` already has pre-existing unrelated `mypy` warnings outside `cmd_land`, so V5 targets `mypy`-clean Python modules directly while V2/V3/V6 test `integrate_branch.py` thoroughly via `pytest`/`unittest`.
- Profile folder name under `antigravity_homes/<profile>` / `AGY_PROFILE` takes precedence over email prefix (`extract_email_id_from_profile`) in `detect_current_profile()` and `sync_window_title()`, and both hyphenated and underscored epic slugs normalize when matching workspace storage folders.

## Definition of Done

- Scenarios RSDH-HP-04, RSDH-HP-05, RSDH-EC-03, RSDH-EC-08, RSDH-ST-01, RSDH-ST-03, and RSDH-FR-03 pass in real temp git repos and doc checks. (V2, V6)
- All existing readiness, revise, contract, worker pool, resume context, integrate branch, and governance tests pass. (V3, V6)
- Ruff lint and mypy strict checks pass across modified Python modules and new test file. (V4, V5)
- `rules/CRITICAL_RULES.md <= 8192` bytes and `verify.sh` §1–§10 verified on candidate commit. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 1](task_01_runtime_state_envelope_and_two_tier_sync.md) and [Task 2](task_02_hybrid_heartbeat_estimator_and_quality_progress.md).

Downstream dependents (blocked by Task 3): `task_04`, `task_05`, `task_06`, `task_07`.

## References & Rollback

- [Epic HLD](runtime_sync_and_dashboard_hardening.en.md), Module Contracts (§4.3–§4.5).
- **Rollback**: Revert task commit; restores prior handoff, readiness, pool, integrate, and rule files and removes `tests/test_rsdh_orchestration.py`.
