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

Given representative inputs covering a 1-task/1-file micro fix, a 2-task/5-file feature wave, a full quality profile run (`--quality-profile full`), and an E2E quality run (`--has-e2e`)
When scripts/estimate_heartbeat.py evaluates each input via CLI and Python API with --json
Then the micro fix (estimated_sec 35 < 60) returns tier "light" with recommended_interval_sec null, the feature wave (estimated_sec 80) returns tier "medium" with recommended_interval_sec 180, the full quality run (estimated_sec 250) returns tier "heavy" with 240, and the E2E run returns tier "heavy" with 300

Scenario: [RSDH-HP-03] [Tier C - Integration] Polyglot quality runner streams zero-token stderr progress and isolates concurrent runs

Given two registered provider capability runs executing concurrently against the same capability under verify_polyglot_registry.py
When both execute via Popen with start_new_session=True, a shortened test heartbeat interval, and shared devtool state directories
Then verify_polyglot_registry.py writes isolated logs under build/quality/<provider>/runs/<run_id>/<capability>.log without collisions while printing periodic "[quality_check]" progress lines to stderr
And .devtool/state/quality_active.json namespaces both entries under runs[run_id] (with pid, host, updated_at, ttl_sec) and finalizes only each finished run_id without overwriting sibling live runs

Scenario: [RSDH-HP-04] [Tier C - Integration] Wave-parallel handoff prompt and template instruct parallel execution and cleanup

Given a packaged epic ready for Stage 3 implementation in an isolated git worktree
When resume_context.py --emit-prompt implement --epic demo-sync executes and skills/dev-lifecycle/references/handoff-template.md is rendered
Then both instruct the programmer orchestrator to run compute_execution_order.py --parallel, run estimate_heartbeat.py per wave and before Gate 4, execute multi-task waves across parallel pool slots, and invoke manage_worker_pool.py cleanup afterward
And neither emits instructions forcing strictly sequential one-task-at-a-time execution for independent waves

Scenario: [RSDH-HP-05] [Tier C - Integration] Worker pool tracks live slot and wave states and cleans clean integrated slots

Given a git repository with initialized 2-slot worker pool worktrees (.worktrees/demo_epic-slot-1 and slot-2) assigned via manage_worker_pool.py sync --task --wave and resume_context.py --wave
When live slot transitions are observed while working and manage_worker_pool.py cleanup --epic-dir demo_epic --epic-slug demo-epic runs after slot integration
Then demo-epic.heartbeat.json initially records populated active_wave and slots ("working" with task_id) before cleanup
And clean integrated slot worktrees and branches (epic/<slug>-slot-* and worker/<epic>/slot-*) are deleted and pruned, leaving an empty slots mapping without deleting non-slot epic metadata

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

Scenario: [RSDH-HP-08] [Tier C - Integration] Check-Quota Modal Stack Controller enforces max one inner modal and real iframe reset

Given quota_dashboard.html served inside #modal-quota's real iframe over TasksServer HTTP in provisioned headless Chrome CDP
When the user opens #scheduleModal and then triggers #loginModal, and later the parent closes #modal-quota
Then opening #loginModal automatically closes #scheduleModal so at most one inner sub-modal has the open state simultaneously
And closing #modal-quota posts {action: "reset_quota_submodals"} across the real iframe boundary causing quota_dashboard.html to close every inner sub-modal cleanly

Scenario: [RSDH-HP-09] [Tier C - Integration] End-to-end orchestration, envelope sync, 96% dashboard, PIC sync, and Chrome CDP modal stack pass together

Given a multi-worktree workspace running live TasksServer HTTP endpoints with Wave 1-3 updates applied
When an epic advances through sync_task_status, verify_polyglot_registry progress, Choice A pending-decision save/clear, PIC reassignment across root and worktree, and real provisioned Chrome CDP parent/iframe dashboard interactions
Then live /api/tasks reflects 96% pre-finish progress, updated PICs, cleared bottlenecks, and live browser rendering passes with zero console or runtime errors
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

Scenario: [RSDH-EC-03] [Tier C - Integration] Stage 3 package_epic --revise owns in-progress/done (new) files while failing todo collisions

Given a Stage 3 epic where task_01 is "done" and task_02 is "in-progress" referencing their already-created "(new)" files alongside an unstarted Stage 2 epic and a Stage 3 revision introducing a new "todo" task declaring an already-existing "(new)" file
When package_epic.py --revise runs on the active Stage 3 epic and check_epic_readiness.py checks the Stage 2 and colliding-todo epics
Then Stage 3 revision accepts existing "(new)" files owned by done/review/in-progress tasks and exits 0
And Stage 2 readiness and newly colliding todo "(new)" declarations or duplicate "(new)" claims exit non-zero under strict ownership checks

Scenario: [RSDH-EC-04] [Tier A - Unit] Check-Tasks harvester leaves idle repositories without active worktrees or tasks in Idle state

Given a git repository containing legacy unstarted folders under .devtool/epic/ (including choosing_a_lifecycle) with zero worktrees, zero features/ tasks, and no pending_decision.json
When check_tasks.resolve_active_epic and check_tasks.derive_lifecycle_state evaluate that repository
Then resolve_active_epic returns None and derive_lifecycle_state returns Idle with is_human_action_required False

Scenario: [RSDH-EC-05] [Tier A - Unit] PIC reassignment validates profile names and isolates sibling epics across worktrees

Given a repository with two distinct epics (demo_epic and sibling_epic) having separate directories and worktrees behind a live TasksServer HTTP endpoint
When tasks_server.assign_epic_pic is called directly and via POST /api/epic/pic with malformed PIC "../bad", and then called with valid PIC "tess" for "demo_epic"
Then the direct assign_epic_pic call raises ValueError without modifying any files and POST /api/epic/pic returns HTTP 400 with {"status": "error", ...} rather than HTTP 500
And the valid update changes only demo_epic across root and its matched worktree while leaving all sibling_epic files untouched

Scenario: [RSDH-EC-06] [Tier C - Integration] Roadmap eliminates sub-day mtime sorting and preserves native select focus in Chrome CDP

Given tasks_dashboard.html served over HTTP in provisioned headless Chrome CDP with two same-day epics whose file mtimes differ and change when editing a PIC, while a user focuses .select-pic-roadmap with data-row-key
When 5s pollDashboard delivers a payload bumping the second epic's sub-day mtime while .select-pic-roadmap holds document.activeElement, and updateEpicPic completes while #modal-epics has computed style display === "flex"
Then sortEpicsForRoadmap ignores sub-day mtime diffs so rows do not reorder between same-day timestamps and pollDashboard defers DOM replacement until blur
And updateEpicPic detects #modal-epics visibility via style.display === "flex" and refreshes modal rows cleanly without losing selection

Scenario: [RSDH-EC-07] [Tier C - Integration] Check-Quota inner sub-modal backdrop and Escape close only the active inner dialog

Given #modal-quota is open and inside quota_dashboard.html one of #profileInfoModal, #appealDetailModal, #scheduleModal, or #loginModal is open
When the user clicks the sub-modal backdrop or presses Escape inside the iframe
Then only the active inner sub-modal closes, preserving the rest of #dashboardCard and keeping #modal-quota open

Scenario: [RSDH-EC-08] [Tier C - Integration] Epic creator profile is automatically detected and stamped as initial PIC

Given an active Antigravity profile environment where AGY_PROFILE (or profile folder /antigravity_homes/brother) runs alongside an HLD containing "- **PIC**: brother" and an active workspace slug with mixed "-" and "_" separators
When resume_context.py --detect-profile and sync_window_title run and package_epic.py generates handoff.md from handoff-template.md
Then --detect-profile outputs "brother" prioritizing folder profile name over email prefix, sync_window_title writes "[@brother]" into .vscode/settings.json without failing on "-" vs "_" slug differences, and generated handoff.md stamps "- **PIC / Assigned Profile**: @brother" rather than "<profile_account_id>"
```

## State Transitions and Invariants

```gherkin
Scenario: [RSDH-ST-01] [Tier C - Integration] Namespaced pending_decision flags pause per epic and require matching ownership on clear

Given two concurrent epics (epic-a and epic-b) both paused cleanly via resume_context.py --pending-decision with distinct decision_id values
When sync_task_status.py marks a task in epic-b "in-progress" (or --gate 2 / --clear-decision clears epic-b) while check_tasks.scan_repo inspects both epics
Then pending_decision.json stores isolated decisions[epic] entries so epic-b resume clears ONLY epic-b while epic-a keeps pending decision and is_human_action_required True
And clearing epic-a's own decision across root and worktree transitions epic-a's is_human_action_required cleanly back to False

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

Scenario: [RSDH-ST-05] [Tier C - Integration] Progress calculation enforces 75% mid-epic, 95% in-progress cap, 96% pre-finish cap, and 100% finished state

Given task counts transitioning from 3/4 done, 4/4 done before Gate 4 convergence, 4/4 done with Gate 4 Review Converged (Waiting Finish), and Gate 5 Done
When check_tasks backend and tasks_dashboard.html compute progress display values
Then 3/4 done yields 75% (high in-progress ratios capped at 95%), 4/4 done pre-convergence yields exactly 96%, and converged Waiting Finish / Done yields 100%

Scenario: [RSDH-ST-06] [Tier C - Integration] Check-Quota embedded mode strips redundant outer card frame in real Chrome iframe

Given quota_dashboard.html loaded with "?embedded=1" inside an actual iframe versus standalone URL in provisioned headless Chrome CDP
When window.getComputedStyle evaluates #dashboardCard border, boxShadow, margin, and padding across standalone and embedded views
Then embedded mode flattens outer spacing, borders, and shadow cleanly while standalone mode preserves full card framing

Scenario: [RSDH-ST-07] [Tier C - Integration] Worker pool cleanup preserves dirty worktrees, unmerged commits, and missing-worktree unmerged branches

Given a repository whose slot-1 has uncommitted dirty changes, slot-2 has an unmerged commit with its worktree folder deleted on disk, and slot-3 is clean and merged into epic/demo-epic
When manage_worker_pool.py cleanup runs in default safe mode versus explicit --discard-unmerged
Then default cleanup deletes only clean merged slot-3 while preserving slot-1 worktree, keeping slot-2's unmerged orphan branch intact, reporting preserved resources cleanly, and marking preserved status instead of silent deletion
And passing --discard-unmerged removes all targeted slots and temporary branches when discard is explicitly requested
```

## Async and Concurrency

```gherkin
Scenario: [RSDH-AR-01] [Tier C - Integration] Canonical transaction lock serializes interleaved slot RMW updates and versioned mirrors

Given multiple concurrent workers performing interleaved read-modify-write slot mutations on shared .devtool/state/ targets across primary root and active worktree
When 16 parallel updates execute under _state_envelope.py's canonical-root fcntl.flock transaction lock
Then zero slot updates are dropped across concurrent RMW cycles and primary plus worktree mirrors contain identical generation numbers and JSON payloads

Scenario: [RSDH-AR-02] [Tier C - Integration] Live polling applies Tier 2 updates immediately without clobbering focused controls or emitting console errors

Given tasks_dashboard.html receiving periodic pollDashboard snapshots containing changed heartbeat waves, quality_active status, and PIC selections
When poll updates run both during active .select-pic-roadmap focus and after blur
Then Section II updates immediately once focus settles, focused selects never lose user selection, and zero console errors are raised

Scenario: [RSDH-AR-03] [Tier C - Integration] Check-tasks harvester isolates multi-epic decisions, exposes live quality_runs, and expires stale owners

Given quality_active.json containing one active live run, one dead-PID/expired-TTL stale running entry, plus pending_decision.json with multiple namespaced epic decisions
When check_tasks.scan_repo inspects the repository
Then expired/dead-PID runs transition to status "stale" without rendering permanent running banners, active concurrent runs surface via quality_runs, and active_epic resolves only its matching namespaced pending_decision
```

## Failure Recovery

```gherkin
Scenario: [RSDH-FR-01] [Tier C - Integration] Stale heartbeat metadata never blocks subsequent task status synchronization

Given an old heartbeat.json file referencing an aborted previous wave and missing slot directory
When sync_task_status.py or resume_context.py writes a new state transition
Then the stale heartbeat is safely superseded atomically under lock and execution continues cleanly

Scenario: [RSDH-FR-02] [Tier C - Integration] Quality verification finalizes failing run_id without clobbering concurrent runs

Given a failing capability command in verify_polyglot_registry.py running alongside an independent healthy run_id in quality_active.json
When the failing command exits non-zero
Then only its own runs[run_id] transitions to status "failed" with non-null finished_at while sibling live runs remain intact

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

Scenario: [RSDH-FR-07] [Tier C - Integration] Signal-aborted quality verification reaps child processes and recovers stale owners

Given a running capability subprocess group under verify_polyglot_registry.py alongside an independent healthy concurrent run
When SIGTERM interrupts the first verify_polyglot_registry.py runner process
Then the signal handler terminates and reaps the active child process group and transitions only its own runs[run_id] to status "aborted" while leaving the sibling run intact
```
