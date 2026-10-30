---
id: "task_01_resume_context_engine"
status: "todo"
priority: "high"
assignee: null
epic: "context_memory_management"
dueDate: null
created: "2026-10-30T16:05:00Z"
modified: "2026-10-30T16:05:00Z"
completedAt: null
labels: ["cli", "memory", "concurrency", "architecture"]
order: "a1"
---

# Task 1: Two-Tier Multi-Epic CLI Engine and Architecture Rules Synchronization

Epic: [context_memory_management](../epic/context_memory_management/context_memory_management.en.md)

## Requirement Analysis

Evolve the baseline implementation in `docs/architecture/resume_context.py` and `docs/architecture/save_resume_rules.md` into the canonical CLI engine `scripts/resume_context.py` (keeping `docs/architecture/resume_context.py` and `docs/architecture/save_resume_rules.md` synchronized):
1. Preserve all baseline constants and functions from `docs/architecture/resume_context.py` (`WORKSPACE_ROOT`, `REPOS`, `DEFAULT_LEDGER_TEMPLATE`, `print_section`, `ensure_ledger`, `read_tail`, `scan_project_ledger`, `scan_assistant_state`, `scan_activity_stream`, `scan_git_status`, `scan_open_rfcs`, `scan_active_tasks`, `complete_feature_and_rotate`).
2. Add dynamic workspace and worktree resolution:
   - `resolve_workspace_root(explicit_root: str | None = None) -> Path`: resolves from `--workspace-root`, `$WORKSPACE_ROOT`, the script's parent workspace (`Path(__file__).resolve().parents[2]`), `$HOME/Projects`, or `$HOME/AllProjects`.
   - `resolve_primary_repo_root(cwd: Path | None = None) -> Path`: uses `git rev-parse --git-common-dir` to route commands executed inside `.worktrees/<epic_dir>` back to the primary repository root's `.devtool/` directory (`[CMM-EC-02]`), and auto-detects the active epic slug from branch `epic/<slug>` when `--epic` is omitted.
3. Implement **Multi-Epic Tier 2 Partitioning & Concurrency Guard** (`[CMM-HP-01]`, `[CMM-EC-01]`, `[CMM-AR-01]`, `[CMM-FR-01]`):
   - Use `fcntl.flock` on `.devtool/.memory.lock` across all state, log, ledger, and rollup writes.
   - Migrate legacy `.devtool/assistant_state.md` and `.devtool/activity_stream.log` into `.devtool/state/general.md` and `.devtool/logs/activity_general.log` when `.devtool/state/` or `.devtool/logs/` do not exist yet (`[CMM-FR-01]`).
   - Implement `write_epic_state(root, epic_slug, decisions, status, next_step, prompt, role, repo)` writing `.devtool/state/<epic_slug>.md` with a hard 20-line maximum (`MAX_STATE_LINES = 20`, `[CMM-EC-01]`) and rendering `.devtool/assistant_state.md` from all active `.devtool/state/*.md` files.
   - Implement `append_activity_log(root, epic_slug, repo, task_id, request, action, note)` appending `[YYYY-MM-DD HH:MM] [<repo>/<epic_slug>/<task_id>] Request: <request> | Action: <action> | Note: <note>` to `.devtool/logs/activity_<epic_slug>.log` and refreshing `.devtool/activity_stream.log`.
   - Enhance `scan_active_tasks(root, epic_filter=None)` to scan both `.devtool/features/task_*.md` (`todo`, `in-progress`, `review`) and `.devtool/features/done/task_*.md` (`done`), printing completion ratios (`<done>/<total> done`, `[CMM-EC-03]`).
   - Enhance `complete_feature_and_rotate(root, epic_slug, summary, repo=None, checkpoint=False)` so standard `--complete` appends the milestone to `.devtool/PROJECT_LEDGER.md` and moves only `<epic_slug>`'s state and activity log into `.devtool/archive/` while leaving other active epics intact (`[CMM-HP-01]`), whereas `--checkpoint` updates Tier 2 state/log without archiving (`[CMM-ST-02]`).
4. Implement **Tri-Role Governance Banners & Prompt Emission** (`[CMM-ST-01]`):
   - Support `--role assistant|programmer` (accepting `implementer` and `worker` as aliases for `programmer`).
   - Implement `emit_handoff_prompt(mode, epic_slug, epic_dir=None, custom_prompt=None)` for `--emit-prompt` modes: `principal-review`, `implement`, `cross-review`, `finish`, and `assistant`.
5. Update `docs/architecture/save_resume_rules.md` to document the Multi-Epic Tier 2 partitioning, Tri-Role Governance (Human Architect / AI Assistant / AI Programmer), and CLI flags.
6. Create `scripts/test_resume_context.py` covering `CMM-HP-01`, `CMM-EC-01`, `CMM-EC-02`, `CMM-EC-03`, `CMM-ST-01`, `CMM-AR-01`, and `CMM-FR-01`.

## Files

Allowed files:
- `scripts/resume_context.py` (new)
- `docs/architecture/resume_context.py`
- `docs/architecture/save_resume_rules.md`
- `scripts/test_resume_context.py` (new)

Read-only context:
- `.devtool/epic/context_memory_management/context_memory_management.en.md` — HLD specifications
- `.devtool/epic/context_memory_management/2026-10-30-context-memory-management-design.en.md` — approved source spec

## Design Rationale

- Partitioning Tier 2 state into `.devtool/state/<epic_slug>.md` and `.devtool/logs/activity_<epic_slug>.log` while auto-rendering `.devtool/assistant_state.md` and `.devtool/activity_stream.log` prevents multi-agent overwrites and premature log truncation while maintaining 100% backward compatibility with `docs/architecture/save_resume_rules.md`.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `scripts/resume_context.py`, `docs/architecture/resume_context.py`, `docs/architecture/save_resume_rules.md`, and `scripts/test_resume_context.py`.
- **Downstream Callers**: Tasks 2, 3, and 4 build upon `scripts/resume_context.py` and `scripts/test_resume_context.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% coverage of multi-epic state/log partitioning, worktree resolution, 20-line truncation, and Tri-Role prompt emission.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: CMM-HP-01, CMM-EC-01, CMM-EC-02, CMM-EC-03, CMM-ST-01, CMM-AR-01, CMM-FR-01

```gherkin
Scenario: [CMM-HP-01] [Tier C - Integration] Two-Tier Context Harvesting, Multi-Epic Isolation, and Feature Compaction
  Given a multi-repository workspace where epic-alpha and epic-beta both record active state via resume_context.py --state and programmer logs via resume_context.py --log
  When the engineer runs resume_context.py followed by resume_context.py --complete epic-alpha "Delivered alpha engine"
  Then the initial harvest prints all 6 canonical sections (0. PROJECT ARCHITECTURAL LEDGER, 1. ACTIVE EPIC STATE, 2. RECENT PROGRAMMER ACTIVITY, 3. GIT WORKING TREE STATUS, 4. OPEN CONTRACT GAPS & RFCS, 5. ACTIVE TASKS) including both epic-alpha and epic-beta
  And after --complete epic-alpha, the milestone "- **[YYYY-MM-DD] `epic-alpha`**: Delivered alpha engine" is appended to .devtool/PROJECT_LEDGER.md
  And epic-alpha's state and activity log are moved into .devtool/archive/ while epic-beta's state (.devtool/state/epic-beta.md) and activity log (.devtool/logs/activity_epic-beta.log) remain active in .devtool/assistant_state.md and .devtool/activity_stream.log

Scenario: [CMM-EC-01] [Tier A - Unit] Enforcing the 20-Line Ceiling on Per-Epic State Snapshots
  Given an active epic context_memory_management where --state is invoked with multi-line decisions and custom prompt notes exceeding 25 lines
  When resume_context.py --state --epic context_memory_management writes .devtool/state/context_memory_management.md
  Then the written file .devtool/state/context_memory_management.md contains at most 20 lines
  And preserves all 4 mandatory fields (Active Epic, Recent Decisions Locked, Repo/Task Status, Next Immediate Step)

Scenario: [CMM-EC-02] [Tier A - Unit] Worktree-Aware Routing From Nested .worktrees/<epic_dir> Checkout
  Given a git repository with a nested worktree at .worktrees/context_memory_management on branch epic/context_memory_management
  When an AI Programmer invokes resume_context.py --state or --log from inside .worktrees/context_memory_management without passing --repo
  Then the engine resolves the primary repository root via git rev-parse --git-common-dir
  And writes the state and log files into the primary repository's .devtool/ directory rather than the ephemeral worktree

Scenario: [CMM-EC-03] [Tier A - Unit] Kanban Task Progress Calculation Across Active and Done Directories
  Given a repository with 2 tasks in .devtool/features/ (status todo and in-progress) and 3 completed tasks in .devtool/features/done/ (status done) for epic context_memory_management
  When scan_active_tasks executes during a resume_context.py harvest
  Then Section 5 lists the active todo and in-progress tasks and reports the epic completion progress summary "3/5 done"

Scenario: [CMM-ST-01] [Tier C - Integration] Tri-Role Persona Governance Banners and 4-Scenario Handoff Prompt Emission
  Given an active epic context_memory_management in .devtool/
  When resume_context.py is invoked with --role assistant, --role programmer (or alias implementer), and --emit-prompt for principal-review, implement, cross-review, finish, and assistant
  Then --role assistant outputs the "[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]" banner with the "NO IMPLEMENTATION" restriction
  And --role programmer outputs the "[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]" banner enforcing TDD, Clean Code, and Allowed files boundaries
  And each --emit-prompt mode outputs a self-contained handoff prompt containing the target role persona, startup resume_context.py command, and stage-specific instructions

Scenario: [CMM-AR-01] [Tier A - Unit] Exclusive File Locking Prevents Interleaved Writes Across Parallel Agents
  Given 4 concurrent worker processes simultaneously invoking resume_context.py --log and --state across epic-alpha and epic-beta on the same repository
  When all 4 processes complete execution under .devtool/.memory.lock synchronization
  Then every log entry is recorded intact without line corruption or missing entries in .devtool/logs/activity_epic-alpha.log and .devtool/logs/activity_epic-beta.log
  And .devtool/assistant_state.md contains valid snapshots for both epics

Scenario: [CMM-FR-01] [Tier A - Unit] Automatic Migration of Legacy Flat assistant_state.md and activity_stream.log
  Given a repository containing legacy .devtool/assistant_state.md and .devtool/activity_stream.log but no .devtool/state/ or .devtool/logs/ directories
  When resume_context.py runs a harvest or writes a new epic state
  Then the legacy content is preserved and migrated into .devtool/state/general.md and .devtool/logs/activity_general.log without data loss
  And the command exits with code 0
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_hp_01` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_hp_01` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_ec_01` | exit 0; contains "OK" | — |
| V4 | GREEN | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_ec_02` | exit 0; contains "OK" | — |
| V5 | GREEN | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_ec_03` | exit 0; contains "OK" | — |
| V6 | GREEN | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_st_01` | exit 0; contains "OK" | — |
| V7 | GREEN | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_ar_01` | exit 0; contains "OK" | — |
| V8 | GREEN | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_fr_01` | exit 0; contains "OK" | — |
| V9 | TIER-B | `ruff check scripts/resume_context.py docs/architecture/resume_context.py scripts/test_resume_context.py` | exit 0 | — |
| V10 | TIER-B | `mypy --strict --follow-imports=silent scripts/resume_context.py scripts/test_resume_context.py` | exit 0 | — |
| V11 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_01.xml scripts/test_resume_context.py` | exit 0; results build/test-results/task_01.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `scripts/resume_context.py` and `docs/architecture/resume_context.py` diverge in behavior.

## Decisions Already Made

- Grounded baseline functions in `docs/architecture/resume_context.py` (`print_section`, `ensure_ledger`, `read_tail`, `scan_project_ledger`, `scan_assistant_state`, `scan_activity_stream`, `scan_git_status`, `scan_open_rfcs`, `scan_active_tasks`, `complete_feature_and_rotate`) are preserved and extended in `scripts/resume_context.py`.
- `MAX_STATE_LINES = 20` enforces the 20-line cap on every `.devtool/state/<epic_slug>.md` snapshot.
- `--role programmer` is the canonical execution persona (`[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]`), with `implementer` and `worker` accepted as aliases; `--role assistant` is the canonical advisory/review persona (`[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]`).
- `--emit-prompt` supports `principal-review`, `implement`, `cross-review`, `finish`, and `assistant`.

## Definition of Done

- `scripts/resume_context.py` and `docs/architecture/resume_context.py` implement multi-epic Tier 2 partitioning, rollup rendering, and epic-isolated `--complete` compaction (V2).
- 20-line state cap, worktree routing, and Kanban `done/total` progress reporting pass unit tests (V3, V4, V5).
- Tri-Role banners (`AI ASSISTANT` and `AI PROGRAMMER`), `--emit-prompt` modes, `fcntl.flock` concurrency, and legacy file migration pass unit and integration tests (V6, V7, V8).
- Ruff linting and Mypy strict type checks pass cleanly (V9, V10).
- JUnit XML report is generated and all Task 1 BDD scenarios pass (V11).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- None.

## References & Rollback

- Baseline: `docs/architecture/resume_context.py` and `docs/architecture/save_resume_rules.md`
- HLD: `.devtool/epic/context_memory_management/context_memory_management.en.md`
- Rollback: Remove `scripts/resume_context.py` and `scripts/test_resume_context.py` and restore `docs/architecture/` files via `git checkout`.
