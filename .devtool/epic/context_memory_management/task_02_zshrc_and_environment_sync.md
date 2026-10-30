---
id: "task_02_zshrc_and_environment_sync"
status: "todo"
priority: "high"
assignee: null
epic: "context_memory_management"
dueDate: null
created: "2026-10-30T16:05:00Z"
modified: "2026-10-30T16:05:00Z"
completedAt: null
labels: ["zshrc", "environment", "history", "aliases"]
order: "a2"
---

# Task 2: Multi-Profile Shell Environment, Shared Terminal History, and Aliases Synchronization

Epic: [context_memory_management](../epic/context_memory_management/context_memory_management.en.md)

## Requirement Analysis

Implement deterministic shell environment, shared terminal history (`.zsh_history`), and alias synchronization in `scripts/resume_context.py` (`--sync-zshrc`) and `docs/architecture/resume_context.py`:
1. Implement `sync_shell_env(real_home: Path | None = None, workspace_root: Path | None = None) -> dict[str, object]` in `scripts/resume_context.py` (invoked via `--sync-zshrc [--real-home <path>] [--workspace-root <path>]`):
   - Ensure `export REAL_HOME="/Users/danhdueexoictif"` (or target `real_home`) and `export WORKSPACE_ROOT="$REAL_HOME/AllProjects"` are declared in `.zshrc`.
   - Create symlink `<real_home>/Projects -> <workspace_root>` when `<real_home>/Projects` does not exist yet (`[CMM-HP-02]`).
   - Update `sync_items` inside `ag_run()` in `.zshrc` to include `AllProjects`, `Projects`, and `.zsh_history`.
   - Ensure shared history configuration is present after `source $ZSH/oh-my-zsh.sh` in `.zshrc`:
     - `export HISTFILE="$REAL_HOME/.zsh_history"`
     - `export HISTSIZE=50000`
     - `export SAVEHIST=50000`
     - `setopt INC_APPEND_HISTORY`
     - `setopt SHARE_HISTORY`
     - `setopt HIST_IGNORE_DUPS`
   - Ensure the two canonical aliases are declared in `.zshrc`:
     - `alias resume='python3 $HOME/Projects/ai-agent-tools/scripts/resume_context.py'`
     - `alias save-context='python3 $HOME/Projects/ai-agent-tools/scripts/resume_context.py --complete'`
   - Iterate over all profile directories in `<real_home>/antigravity_homes/*`:
     - Merge any unique lines from a profile's non-symlink `.zsh_history` into `<real_home>/.zsh_history` before replacing `<profile>/.zsh_history` with a symlink to `<real_home>/.zsh_history` (`[CMM-AR-02]`).
     - Ensure `<profile>/AllProjects` and `<profile>/Projects` symlink to `<workspace_root>`.
2. Ensure graceful fallback in `scan_open_rfcs` and `scan_git_status` when `D3Nexus/shared-contracts` or a repo's `.git` folder is missing (`[CMM-FR-02]`).
3. Add unit and integration tests in `scripts/test_resume_context.py` covering `CMM-HP-02`, `CMM-AR-02`, and `CMM-FR-02`.

## Files

Allowed files:
- `scripts/resume_context.py` (new)
- `docs/architecture/resume_context.py`
- `scripts/test_resume_context.py` (new)

Read-only context:
- `.devtool/epic/context_memory_management/context_memory_management.en.md` — HLD specifications
- `docs/architecture/save_resume_rules.md` — baseline architecture rules

## Design Rationale

- Placing `export HISTFILE="$REAL_HOME/.zsh_history"` and `setopt SHARE_HISTORY INC_APPEND_HISTORY` after `source $ZSH/oh-my-zsh.sh` prevents Oh-My-Zsh from resetting `HISTFILE` to `$HOME/.zsh_history` in isolated Antigravity profiles.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `sync_shell_env` in `scripts/resume_context.py` and `docs/architecture/resume_context.py`, plus `test_cmm_hp_02`, `test_cmm_ar_02`, and `test_cmm_fr_02` in `scripts/test_resume_context.py`.
- **Downstream Callers**: All Antigravity profile shells and Task 4 verification.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% coverage of `.zshrc` synchronization, history merge idempotency, and missing directory fallback.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: CMM-HP-02, CMM-AR-02, CMM-FR-02

```gherkin
Scenario: [CMM-HP-02] [Tier C - Integration] Multi-Profile Zshrc Environment, Shared Terminal History, and Alias Synchronization
  Given a host environment with a primary .zshrc and multiple Antigravity profile homes under antigravity_homes/<profile>
  When the engineer runs resume_context.py --sync-zshrc
  Then .zshrc defines REAL_HOME, WORKSPACE_ROOT, HISTFILE="$REAL_HOME/.zsh_history", SHARE_HISTORY, INC_APPEND_HISTORY, and both aliases (resume and save-context)
  And ag_run() sync_items includes AllProjects, Projects, and .zsh_history
  And each profile home contains symlinks for Projects, AllProjects, and .zsh_history pointing to the primary home after merging unique profile history lines

Scenario: [CMM-AR-02] [Tier A - Unit] Idempotent Zsh History Merge Preserves Chronological Commands Without Duplicating Symlinks
  Given a profile home whose .zsh_history is already a symlink to $REAL_HOME/.zsh_history and another profile home with a regular file containing 3 unique commands
  When sync_shell_env runs twice consecutively
  Then the 3 unique commands are appended exactly once to $REAL_HOME/.zsh_history
  And both profile homes remain valid symlinks to $REAL_HOME/.zsh_history with exit code 0

Scenario: [CMM-FR-02] [Tier A - Unit] Graceful Fallback When D3Nexus Shared Contracts or Repo Git Directory Is Absent
  Given a workspace root where D3Nexus/shared-contracts does not exist and one configured repository directory lacks a .git folder
  When resume_context.py executes a full context harvest
  Then scan_open_rfcs prints "(D3Nexus/shared-contracts not initialized yet.)" and scan_git_status skips the non-git directory cleanly
  And the command completes all 6 sections with exit code 0
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_hp_02` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_hp_02` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_ar_02` | exit 0; contains "OK" | — |
| V4 | GREEN | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_fr_02` | exit 0; contains "OK" | — |
| V5 | TIER-B | `ruff check scripts/resume_context.py docs/architecture/resume_context.py scripts/test_resume_context.py` | exit 0 | — |
| V6 | TIER-B | `mypy --strict --follow-imports=silent scripts/resume_context.py scripts/test_resume_context.py` | exit 0 | — |
| V7 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_02.xml scripts/test_resume_context.py` | exit 0; results build/test-results/task_02.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `sync_shell_env` overwrites `.zsh_history` without first merging unique lines from profile `.zsh_history` files.

## Decisions Already Made

- New frozen contract `sync_shell_env(real_home: Path | None = None, workspace_root: Path | None = None) -> dict[str, object]` in `scripts/resume_context.py` accepts explicit paths for hermetic testing in `tempfile.TemporaryDirectory()` and defaults to `Path("/Users/danhdueexoictif")` and `Path("/Users/danhdueexoictif/AllProjects")` when invoked via `--sync-zshrc`.
- Both aliases in `.zshrc` are exact:
  `alias resume='python3 $HOME/Projects/ai-agent-tools/scripts/resume_context.py'`
  `alias save-context='python3 $HOME/Projects/ai-agent-tools/scripts/resume_context.py --complete'`

## Definition of Done

- `sync_shell_env` (`--sync-zshrc`) configures `.zshrc`, `ag_run()` `sync_items`, shared `HISTFILE`, profile symlinks (`Projects`, `AllProjects`, `.zsh_history`), and aliases `resume` / `save-context` (V2).
- Idempotent history merging and missing directory fallback pass unit tests (V3, V4).
- Ruff linting and Mypy strict type checks pass cleanly (V5, V6).
- JUnit XML report is generated and all Task 2 BDD scenarios pass (V7).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 1](task_01_resume_context_engine.md) — extends `scripts/resume_context.py` and `scripts/test_resume_context.py`.

## References & Rollback

- Spec: `.devtool/epic/context_memory_management/2026-10-30-context-memory-management-design.en.md`
- HLD: `.devtool/epic/context_memory_management/context_memory_management.en.md`
- Rollback: Revert changes to `scripts/resume_context.py` and `scripts/test_resume_context.py`.
