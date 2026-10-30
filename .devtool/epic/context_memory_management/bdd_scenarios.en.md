# Context Memory Management BDD Scenarios

## Table of Contents

- [Dimension 1: Happy Paths](#dimension-1-happy-paths)
- [Dimension 2: Edge Cases and Boundaries](#dimension-2-edge-cases-and-boundaries)
- [Dimension 3: State Transitions](#dimension-3-state-transitions)
- [Dimension 4: Async and Multi-Agent Concurrency](#dimension-4-async-and-multi-agent-concurrency)
- [Dimension 5: Failures and Storage Resilience](#dimension-5-failures-and-storage-resilience)

## Dimension 1: Happy Paths

```gherkin
Scenario: [CMM-HP-01] [Tier C - Integration] Two-Tier Context Harvesting, Multi-Epic Isolation, and Feature Compaction
  Given a multi-repository workspace where epic-alpha and epic-beta both record active state via resume_context.py --state and programmer logs via resume_context.py --log
  When the engineer runs resume_context.py followed by resume_context.py --complete epic-alpha "Delivered alpha engine"
  Then the initial harvest prints all 6 canonical sections (0. PROJECT ARCHITECTURAL LEDGER, 1. ACTIVE EPIC STATE, 2. RECENT PROGRAMMER ACTIVITY, 3. GIT WORKING TREE STATUS, 4. OPEN CONTRACT GAPS & RFCS, 5. ACTIVE TASKS) including both epic-alpha and epic-beta
  And after --complete epic-alpha, the milestone "- **[YYYY-MM-DD] `epic-alpha`**: Delivered alpha engine" is appended to .devtool/PROJECT_LEDGER.md
  And epic-alpha's state and activity log are moved into .devtool/archive/ while epic-beta's state (.devtool/state/epic-beta.md) and activity log (.devtool/logs/activity_epic-beta.log) remain active in .devtool/assistant_state.md and .devtool/activity_stream.log

Scenario: [CMM-HP-02] [Tier C - Integration] Multi-Profile Zshrc Environment, Shared Terminal History, and Alias Synchronization
  Given a host environment with a primary .zshrc and multiple Antigravity profile homes under antigravity_homes/<profile>
  When the engineer runs resume_context.py --sync-zshrc
  Then .zshrc defines REAL_HOME, WORKSPACE_ROOT, HISTFILE="$REAL_HOME/.zsh_history", SHARE_HISTORY, INC_APPEND_HISTORY, and both aliases (resume and save-context)
  And ag_run() sync_items includes AllProjects, Projects, and .zsh_history
  And each profile home contains symlinks for Projects, AllProjects, and .zsh_history pointing to the primary home after merging unique profile history lines

Scenario: [CMM-HP-03] [Tier C - Integration] End-to-End Skill Definitions, Dev-Lifecycle Hooks, and Release Verification Harness
  Given the completed resume-context and save-context skills, CRITICAL_RULES.md Rule 8, dev-lifecycle stage skill hooks, and scripts/verify.sh registration
  When the engineer runs the verification suite for context_memory_management
  Then skills/resume-context/SKILL.md and skills/save-context/SKILL.md pass YAML frontmatter and relative link checks
  And dev-brainstorming, dev-designer, dev-lifecycle, principal-review, dev-implementation, cross-model-review, and finishing-a-development-branch contain the required resume_context.py integration hooks
  And scripts/verify.sh executes scripts/test_resume_context.py with exit code 0
```

## Dimension 2: Edge Cases and Boundaries

```gherkin
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
```

## Dimension 3: State Transitions

```gherkin
Scenario: [CMM-ST-01] [Tier C - Integration] Tri-Role Persona Governance Banners and 4-Scenario Handoff Prompt Emission
  Given an active epic context_memory_management in .devtool/
  When resume_context.py is invoked with --role assistant, --role programmer (or alias implementer), and --emit-prompt for principal-review, implement, cross-review, finish, and assistant
  Then --role assistant outputs the "[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]" banner with the "NO IMPLEMENTATION" restriction
  And --role programmer outputs the "[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]" banner enforcing TDD, Clean Code, and Allowed files boundaries
  And each --emit-prompt mode outputs a self-contained handoff prompt containing the target role persona, startup resume_context.py command, and stage-specific instructions

Scenario: [CMM-ST-02] [Tier A - Unit] Non-Destructive Checkpoint Save via --complete --checkpoint With Custom Prompt
  Given an in-flight epic context_memory_management with existing entries in .devtool/logs/activity_context_memory_management.log
  When the engineer or agent runs save-context --checkpoint context_memory_management "Locked multi-epic storage model; next write task_01"
  Then .devtool/state/context_memory_management.md and .devtool/logs/activity_context_memory_management.log are updated with the custom prompt note
  And .devtool/PROJECT_LEDGER.md is not modified and .devtool/logs/activity_context_memory_management.log is not moved to .devtool/archive/
```

## Dimension 4: Async and Multi-Agent Concurrency

```gherkin
Scenario: [CMM-AR-01] [Tier A - Unit] Exclusive File Locking Prevents Interleaved Writes Across Parallel Agents
  Given 4 concurrent worker processes simultaneously invoking resume_context.py --log and --state across epic-alpha and epic-beta on the same repository
  When all 4 processes complete execution under .devtool/.memory.lock synchronization
  Then every log entry is recorded intact without line corruption or missing entries in .devtool/logs/activity_epic-alpha.log and .devtool/logs/activity_epic-beta.log
  And .devtool/assistant_state.md contains valid snapshots for both epics

Scenario: [CMM-AR-02] [Tier A - Unit] Idempotent Zsh History Merge Preserves Chronological Commands Without Duplicating Symlinks
  Given a profile home whose .zsh_history is already a symlink to $REAL_HOME/.zsh_history and another profile home with a regular file containing 3 unique commands
  When sync_shell_env runs twice consecutively
  Then the 3 unique commands are appended exactly once to $REAL_HOME/.zsh_history
  And both profile homes remain valid symlinks to $REAL_HOME/.zsh_history with exit code 0
```

## Dimension 5: Failures and Storage Resilience

```gherkin
Scenario: [CMM-FR-01] [Tier A - Unit] Automatic Migration of Legacy Flat assistant_state.md and activity_stream.log
  Given a repository containing legacy .devtool/assistant_state.md and .devtool/activity_stream.log but no .devtool/state/ or .devtool/logs/ directories
  When resume_context.py runs a harvest or writes a new epic state
  Then the legacy content is preserved and migrated into .devtool/state/general.md and .devtool/logs/activity_general.log without data loss
  And the command exits with code 0

Scenario: [CMM-FR-02] [Tier A - Unit] Graceful Fallback When D3Nexus Shared Contracts or Repo Git Directory Is Absent
  Given a workspace root where D3Nexus/shared-contracts does not exist and one configured repository directory lacks a .git folder
  When resume_context.py executes a full context harvest
  Then scan_open_rfcs prints "(D3Nexus/shared-contracts not initialized yet.)" and scan_git_status skips the non-git directory cleanly
  And the command completes all 6 sections with exit code 0
```

