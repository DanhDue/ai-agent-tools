# BDD Scenarios — Runtime State Sync, Hybrid Heartbeat, and Dashboard Hardening

## Table of Contents

- [Happy Path](#happy-path)
- [Edge Cases](#edge-cases)
- [State Transitions and Invariants](#state-transitions-and-invariants)
- [Async and Concurrency](#async-and-concurrency)
- [Failure Recovery](#failure-recovery)

## Happy Path

```gherkin
Scenario: [RSDH-HP-01] [Tier C - Integration] Atomic runtime state envelope syncs worktree, primary repo, and Two-Tier Memory

Given a git repository with an active isolated worktree on epic branch "epic/demo-sync" and matching Kanban tasks
When _state_envelope.update_epic_heartbeat records a task transition and sync_task_status.py marks task_01 "in-progress"
Then .devtool/state/demo-sync.heartbeat.json is written atomically via os.replace to both the worktree and primary repository .devtool/state directories
And both .devtool/state/demo-sync.md and .devtool/assistant_state.md reflect the updated task status and timestamp mechanically without manual resume_context invocations

Scenario: [RSDH-HP-02] [Tier A - Unit] Simple rule-based heartbeat estimator maps workloads across light, medium, and heavy cadence tiers

Given representative inputs covering a 1-task/1-file micro fix, a 2-task/5-file feature wave, a full polyglot quality run, and an E2E quality run
When scripts/estimate_heartbeat.py evaluates each input via CLI and Python API with --json
Then the micro fix returns tier "light" with recommended_interval_sec null, the feature wave returns tier "medium" with recommended_interval_sec 180, the full quality run returns tier "heavy" with 240, and the E2E run returns tier "heavy" with 300

Scenario: [RSDH-HP-03] [Tier C - Integration] Polyglot quality runner streams zero-token stderr progress and updates quality_active.json

Given a registered provider capability command that runs longer than the configured heartbeat interval
When verify_polyglot_registry.py executes the provider via Popen with a shortened test heartbeat interval and active devtool state directory
Then verify_polyglot_registry.py writes command output to build/quality/<provider>/<capability>.log while printing periodic "[quality_check]" progress lines to stderr
And .devtool/state/quality_active.json transitions from status "running" with step_index/step_total to final status "passed" upon completion

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

Scenario: [RSDH-HP-06] [Tier C - Integration] PIC reassignment synchronizes root and worktree PIC-bearing files while preserving review and BDD prose

Given a repository with epic artifacts in both primary root .devtool/epic/demo_epic/ and an active git worktree .worktrees/demo_epic/, including handoff.md ("- **PIC / Assigned Profile**: ..."), HLD, task_*.md, bdd_scenarios.en.md, and principal_review.md
When tasks_server.py assign_epic_pic updates the epic PIC from "mommy" to "brother"
Then both root and worktree HLD, handoff.md, task_*.md (under epic and features), pipeline/heartbeat JSON files, and worktree .vscode/settings.json update to "brother"
And bdd_scenarios.en.md and principal_review.md remain byte-for-byte unchanged without injected PIC bullets

Scenario: [RSDH-HP-07] [Tier C - Integration] Tasks dashboard enforces 96% pre-finish ceiling and refreshes Section II live on state changes

Given tasks_dashboard.html loaded with a repo payload containing an in_progress epic with 5/5 tasks done and Gate 4 not yet converged
When pollDashboard receives an updated payload updating active account_id, task_progress, prompt, heartbeat active wave, or quality_active running state
Then both Section I sidebar and Section II execution card render 96% ("96% Review") rather than 99%
And tier2Sig detects the change and re-renders Section II with the live wave/quality progress banner without reloading the page

Scenario: [RSDH-HP-08] [Tier C - Integration] Check-Quota Modal Stack Controller limits open inner sub-modals to one and resets on parent close

Given quota_dashboard.html embedded inside #modal-quota in tasks_dashboard.html
When the user opens #scheduleModal and then triggers #loginModal, and later the parent closes #modal-quota
Then opening #loginModal automatically closes #scheduleModal so at most one inner sub-modal has the open state simultaneously
And closing #modal-quota posts reset_submodals causing quota_dashboard.html to close every inner sub-modal cleanly

Scenario: [RSDH-HP-09] [Tier C - Integration] End-to-end orchestration, envelope sync, 96% dashboard, PIC sync, and modal stack pass together

Given a multi-worktree workspace running live TasksServer HTTP endpoints with Wave 1-3 updates applied
When an epic advances through sync_task_status, verify_polyglot_registry progress, Choice A pending-decision save/clear, PIC reassignment across root and worktree, and dashboard DOM interactions in headless Node
Then live /api/tasks reflects 96% pre-finish progress, updated PICs, cleared bottlenecks, and extracted dashboard JS runs with zero uncaught errors
```

## Edge Cases

```gherkin
Scenario: [RSDH-EC-01] [Tier A - Unit] Envelope reader tolerates missing, empty, or truncated state JSON without failing

Given nonexistent, zero-byte, and malformed truncated files at .devtool/state/broken.heartbeat.json
When _state_envelope.read_json_safe reads each path with a default dictionary
Then read_json_safe returns the provided default dictionary cleanly without raising JSONDecodeError or OSError

Scenario: [RSDH-EC-02] [Tier A - Unit] Heartbeat estimator clamps zero inputs and escalates E2E runs to 300 seconds

Given an invocation of scripts/estimate_heartbeat.py with --tasks-count 0 --files-count 0 and another with --quality-profile epic --has-e2e
When both evaluations run
Then the empty input produces tier "light" with recommended_interval_sec null
And the epic E2E run produces tier "heavy" with recommended_interval_sec 300

Scenario: [RSDH-EC-03] [Tier C - Integration] Stage 3 package_epic --revise accepts completed (new) files while Stage 2 design remains strict

Given a Stage 3 epic where task_01 is status "done" referencing an already-created "(new)" file in Allowed Files and Evidence, alongside an unstarted Stage 2 epic whose todo task references an already-existing "(new)" file
When package_epic.py --revise runs on the Stage 3 epic and check_epic_readiness.py runs natively on the Stage 2 epic
Then the Stage 3 revision enables --post-design / --allow-existing-done-new and exits 0
And the Stage 2 readiness check retains strict --design enforcement and exits non-zero on the colliding todo "(new)" path

Scenario: [RSDH-EC-04] [Tier A - Unit] Check-Tasks harvester leaves idle repositories without active worktrees or tasks in Idle state

Given a git repository containing legacy unstarted folders under .devtool/epic/ (including choosing_a_lifecycle) with zero worktrees, zero features/ tasks, and no pending_decision.json
When check_tasks.resolve_active_epic and check_tasks.derive_lifecycle_state evaluate that repository
Then resolve_active_epic returns None and derive_lifecycle_state returns Idle with is_human_action_required False

Scenario: [RSDH-EC-05] [Tier A - Unit] PIC reassignment validates profile names and isolates sibling epics across worktrees

Given a repository with two distinct epics (demo_epic and sibling_epic) having separate directories and worktrees
When tasks_server.assign_epic_pic is called with malformed PIC "../bad" and then valid PIC "tess" for "demo_epic"
Then the malformed PIC request raises ValueError without modifying any files
And the valid update changes only demo_epic across root and its matched worktree while leaving all sibling_epic files untouched

Scenario: [RSDH-EC-06] [Tier C - Integration] Roadmap select preserves focus and exact row mapping during 5s polling and open modals

Given tasks_dashboard.html rendering a Roadmap table where two epics share recent update timestamps and the user focuses a .select-pic-roadmap dropdown with data-row-key
When a 5s poll payload arrives while .select-pic-roadmap holds document.activeElement, and updateEpicPic completes while #modal-epics has style.display === "flex"
Then pollDashboard defers replacing roadmapTbody.innerHTML until focus blurs so the dropdown choice does not jump rows
And updateEpicPic detects #modal-epics visibility via style.display === "flex" and refreshes modal rows accurately

Scenario: [RSDH-EC-07] [Tier C - Integration] Check-Quota inner sub-modal backdrop and Escape close only the active inner dialog

Given #modal-quota is open and inside quota_dashboard.html one of #profileInfoModal, #appealDetailModal, #scheduleModal, or #loginModal is open
When the user clicks the sub-modal backdrop or presses Escape inside the iframe
Then only the active inner sub-modal closes, preserving the rest of #dashboardCard and keeping #modal-quota open

Scenario: [RSDH-EC-08] [Tier A - Unit] Epic creator profile is automatically detected and stamped as initial PIC

Given an active Antigravity profile environment where AGY_PROFILE (or profile folder /antigravity_homes/brother) runs alongside an HLD containing "- **PIC**: brother" and an active workspace slug with mixed "-" and "_" separators
When resume_context.py --detect-profile and sync_window_title run and package_epic.py generates handoff.md from handoff-template.md
Then --detect-profile outputs "brother" prioritizing folder profile name over email prefix, sync_window_title writes "[@brother]" into .vscode/settings.json without failing on "-" vs "_" slug differences, and generated handoff.md stamps "- **PIC / Assigned Profile**: @brother" rather than "<profile_account_id>"
```

## State Transitions and Invariants

```gherkin
Scenario: [RSDH-ST-01] [Tier C - Integration] Choice A pending_decision flags pause cleanly and clears automatically on confirmation or resume

Given an epic paused awaiting human confirmation via resume_context.py --pending-decision "Confirm Gate 2" --decision-kind gate_2_choice
When check_tasks.scan_repo inspects the repo before and after running --gate 2 (or --clear-decision, non-paused --state, sync_task_status in-progress, or package_epic)
Then pending_decision.json initially sets is_human_action_required True with the recorded prompt
And each resume/confirmation trigger removes pending_decision.json across root and worktree so is_human_action_required flips back to False

Scenario: [RSDH-ST-02] [Tier C - Integration] Gate ledger unification merges root and worktree JSONL and GATE_LEDGER.md entries

Given a repository whose older gate_ledger.jsonl records Gate 1 while active worktree GATE_LEDGER.md (or root GATE_LEDGER.md) contains newer Gate 2 and Gate 3 approvals
When check_tasks.parse_gate_ledger_entries inspects the repository
Then all Gates 1, 2, and 3 are returned without short-circuiting on gate_ledger.jsonl

Scenario: [RSDH-ST-03] [Tier C - Integration] Stale worker pool pruning and branch landing clean orphaned slot resources safely

Given a repository whose slot-1 worktree folder was manually removed on disk while its git worktree admin metadata and slot branch still exist, alongside an epic ready for integrate_branch.py land
When manage_worker_pool.py cleanup --stale-only and integrate_branch.py cmd_land execute
Then git worktree prune and branch cleanup remove orphaned slot metadata/branches cleanly without failing on missing directories

Scenario: [RSDH-ST-04] [Tier A - Unit] extract_epic_pic resolves PIC across root and worktree handoff placeholders cleanly

Given an active epic whose root HLD has no PIC yet while its active worktree handoff.md contains "- **PIC / Assigned Profile**: @danhdue" (or "<unassigned>")
When check_tasks.extract_epic_pic inspects the repository
Then the valid worktree PIC "danhdue" is extracted cleanly and placeholder tokens like "<unassigned>" return None

Scenario: [RSDH-ST-05] [Tier C - Integration] Progress calculation enforces 95% in-progress cap, 96% pre-finish cap, and 100% finished state

Given task counts transitioning from 3/4 done, 4/4 done before Gate 4 convergence, 4/4 done with Gate 4 Review Converged (Waiting Finish), and Gate 5 Done
When check_tasks backend and tasks_dashboard.html compute progress display values
Then 3/4 done yields <= 95%, 4/4 done pre-convergence yields exactly 96%, and converged Waiting Finish / Done yields 100%

Scenario: [RSDH-ST-06] [Tier A - Unit] Check-Quota embedded mode strips redundant outer card frame cleanly

Given quota_dashboard.html loaded with query parameter "?embedded=1" versus standalone URL
When the initialization script applies embedded styling classes to #dashboardCard
Then embedded mode removes redundant outer modal spacing/borders while standalone mode preserves full container layout
```

## Async and Concurrency

```gherkin
Scenario: [RSDH-AR-01] [Tier C - Integration] Concurrent multi-process envelope writes preserve valid JSON and latest updates under flock

Given multiple worker processes concurrently calling _state_envelope.atomic_write_json and update_epic_heartbeat on the same .devtool/state/ targets
When all parallel writes complete across 16 concurrent invocations
Then every JSON file parses cleanly without truncation or JSONDecodeError and lock contention produces zero exceptions

Scenario: [RSDH-AR-02] [Tier C - Integration] Live polling applies Tier 2 updates immediately without clobbering focused controls or emitting console errors

Given tasks_dashboard.html receiving periodic pollDashboard snapshots containing changed heartbeat waves, quality_active status, and PIC selections
When poll updates run both during active .select-pic-roadmap focus and after blur
Then Section II updates immediately once focus settles, focused selects never lose user selection, and zero console errors are raised
```

## Failure Recovery

```gherkin
Scenario: [RSDH-FR-01] [Tier C - Integration] Stale heartbeat metadata never blocks subsequent task status synchronization

Given an old heartbeat.json file referencing an aborted previous wave and missing slot directory
When sync_task_status.py or resume_context.py writes a new state transition
Then the stale heartbeat is safely superseded atomically under lock and execution continues cleanly

Scenario: [RSDH-FR-02] [Tier C - Integration] Quality verification finalizes quality_active.json on failing command or runtime error

Given a capability command in verify_polyglot_registry.py that exits non-zero with failing stdout/stderr
When verify_polyglot_registry.py runs and handles the failure inside try/finally
Then quality_active.json is finalized cleanly with status "failed" and non-null finished_at so no permanent "running" indicator remains

Scenario: [RSDH-FR-03] [Tier C - Integration] Updated Choice A and cleanup rules keep CRITICAL_RULES.md within the 8192-byte prompt cap

Given edits adding Choice A pending-decision and worker-pool cleanup governance across rules/CRITICAL_RULES.md and Stage 1-4 SKILL.md files
When UTF-8 byte size of rules/CRITICAL_RULES.md and scripts/verify.sh §1-§10 are checked
Then rules/CRITICAL_RULES.md remains strictly <= 8192 UTF-8 bytes and all static link, ToC, frontmatter, and orphan-reference checks pass

Scenario: [RSDH-FR-04] [Tier C - Integration] Partial read-only failure during PIC reassignment reports warnings without corrupting sibling files

Given an epic containing both writable metadata files and a simulated unwritable path or missing optional state file during PIC assignment
When tasks_server.assign_epic_pic executes
Then writable target files still update cleanly, warnings identify the failed path, and JSON responses reflect accurate updated_files counts

Scenario: [RSDH-FR-05] [Tier C - Integration] Pressing Escape with no open inner quota sub-modal closes cleanly via handleCardClose

Given quota_dashboard.html with all four inner sub-modals closed inside #modal-quota
When the user presses the Escape key
Then the key handler sees zero open inner sub-modals and invokes handleCardClose cleanly without runtime errors

Scenario: [RSDH-FR-06] [Tier C - Integration] Registered verification suites guard byte budgets, idle false positives, and snapshot isolation continuously

Given scripts/verify.sh with all epic suites registered in SUITES and current kit files on disk
When bash scripts/verify.sh --quiet runs and regression checks inspect CRITICAL_RULES.md, dev-designer/SKILL.md, and dashboard scripts
Then CRITICAL_RULES.md remains <= 8192 bytes, dev-designer/SKILL.md remains <= 22528 bytes, idle alphabetical fallbacks stay absent, and all registered verification sections exit 0
```
