# Cross-Repo Tasks and Context Dashboard BDD Scenarios

## Table of Contents

- [Meta Data](#meta-data)
- [Happy Paths](#happy-paths)
- [Edge Cases and Boundaries](#edge-cases-and-boundaries)
- [State Transitions](#state-transitions)
- [Async and Race Conditions](#async-and-race-conditions)
- [Failure and Resilience](#failure-and-resilience)

## Meta Data

- **Epic**: `check_tasks_dashboard`
- **Canonical language**: English
- **Scenario prefix**: `CTD`
- **Automation roots**: `tests/`
- **Rule**: Every scenario ID is assigned to exactly one task and appears in an automated test.
- **Mocking**: Subprocess calls (`git worktree`, `ag_run`) and directory traversals are isolated via mock filesystems and synthetic fixtures in unit/integration tests.

## Happy Paths

```gherkin
Scenario: [CTD-HP-01] [Tier C - Integration] Multi-repo harvesting discovers all projects, worktrees, and styling metadata

Given a root directory containing multiple repositories "ai-agent-tools", "lyrics-sync", "nexus", and "D3Nexus"
And each repository contains .vscode/settings.json with window.title and workbench.colorCustomizations
When the harvester scans the workspace root via harvest_dashboard_graph
Then the returned graph contains metadata objects for all 4 repositories
And each repository correctly reflects its theme colors, active worktrees, and git branches
And task progress counts for done, in-progress, and todo match the filesystem state

Scenario: [CTD-HP-02] [Tier C - Integration] Deterministic Lifecycle FSM derives exact human decision prompt

Given an epic with Gate 4 PASS recorded in .devtool/GATE_LEDGER.md
And all Kanban tasks in .devtool/features/ are marked done
And Gate 5 is not yet recorded in the ledger
When the lifecycle engine evaluates derive_lifecycle_state for the epic
Then the derived stage name is "Stage 3 Phase 4 (Review)"
And the next immediate human decision prompt explicitly contains "Review Choice (Rule 5)"

Scenario: [CTD-HP-03] [Tier C - Integration] Terminal CLI renders rich ANSI colored multi-repo overview

Given multiple discovered repositories with varying Kanban progress
When a developer executes check_tasks.py with argument "all"
Then the CLI prints a formatted ANSI table with repository color badges
And the output displays repository name, active branch or worktree, active epic, and task progress percentages
And the next immediate step for each active epic is clearly visible in the table

Scenario: [CTD-HP-04] [Tier C - Integration] Web server daemon starts cleanly and serves REST API

Given an unoccupied port 8766
When tasks_server.py starts with argument "--daemon"
Then the process writes its PID to /tmp/agy_tasks_server.pid
And a GET request to http://localhost:8766/api/tasks returns HTTP 200 with valid JSON graph data
And a POST request to http://localhost:8766/api/shutdown terminates the server and removes the PID file

Scenario: [CTD-HP-05] [Tier C - Integration] Interactive web dashboard displays project cards and review modal

Given the web server is running and serving tasks_dashboard.html
When the user accesses the dashboard in a browser
Then the interface renders dark mode cards for all repositories
And clicking a review button opens a modal displaying the candidate SHA, reviewer model, and the 7-column triage table
And clicking an IDE launch button triggers a POST request to /api/launch/ide without throwing errors
```

## Edge Cases and Boundaries

```gherkin
Scenario: [CTD-EC-01] [Tier A - Unit] Graceful fallback when .vscode/settings.json is absent

Given a repository directory that lacks a .vscode/settings.json file
When scan_repo collects metadata for this repository
Then the repository theme color falls back to the deterministic palette signature
And window title defaults to the repository folder basename
And scanning completes without raising FileNotFoundError

Scenario: [CTD-EC-02] [Tier A - Unit] Graceful handling of repositories without active epics

Given a repository with a clean working tree and no .devtool/epic/ directory
When the harvester collects metadata for this repository
Then the active epic name is reported as "None"
And the Kanban task count is 0 of 0 with 100% idle status
And the lifecycle stage is reported as "Idle"

Scenario: [CTD-EC-03] [Tier A - Unit] Parsing dirty worktrees and detached HEAD commits

Given a git worktree operating on a detached HEAD commit with unstaged file modifications
When scan_repo executes git worktree parsing
Then the worktree metadata records the abbreviated commit SHA
And the dirty flag is correctly set to true with the count of modified files

Scenario: [CTD-EC-04] [Tier A - Unit] Terminal CLI falls back to plain text when stdout is redirected

Given stdout is redirected to a non-TTY pipe or file
When check_tasks.py formats the output table
Then all ANSI escape codes are stripped from the output
And the output remains cleanly aligned plain text
```

## State Transitions

```gherkin
Scenario: [CTD-ST-01] [Tier A - Unit] FSM transitions from Stage 2 Architecture to Stage 2 Exit Handoff

Given an epic where Gate 1 is PASS and Gate 2 has just been recorded in GATE_LEDGER.md
And the packaging file handoff.md is present in the epic directory
When derive_lifecycle_state evaluates the repository
Then the state transitions to "Stage 2 Exit (Handoff)"
And the next immediate step prompts the human architect for the handoff choice between Principal Review and Implementation

Scenario: [CTD-ST-02] [Tier A - Unit] FSM transitions to Stage 3 Phase 2 TDD when tasks enter in-progress

Given an epic with Gate 3 PASS recorded in GATE_LEDGER.md
And at least one Kanban task in .devtool/features/ has status "in-progress"
When derive_lifecycle_state evaluates the repository
Then the state transitions to "Stage 3 Phase 2 (TDD)"
And the next immediate step indicates the AI Programmer is actively implementing tasks with zero human intervention required
```

## Async and Race Conditions

```gherkin
Scenario: [CTD-AR-01] [Tier C - Integration] Daemon server increments port safely on port collision

Given port 8766 is already bound by an unrelated third-party process
When tasks_server.py attempts to start the dashboard service
Then the server detects that port 8766 is occupied by an alien PID
And the server safely increments the listening port to 8767
And the server updates the PID file and prints the active listening URL on port 8767
```

## Failure and Resilience

```gherkin
Scenario: [CTD-FR-01] [Tier A - Unit] Rule 9 launcher enforcement prevents environment contamination

Given a request to launch the CLI or IDE targeting an Antigravity profile "hau"
When tasks_server.py constructs the launch command
Then the command prefixes execution with localized subshell invocation "ag_run hau"
And the command strips VSCODE_GIT_IPC_HANDLE and ELECTRON_RUN_AS_NODE environment variables
And the command never executes security default-keychain or modifies global ~/.zshrc

Scenario: [CTD-FR-02] [Tier A - Unit] Server recovers gracefully from stale or orphan PID files

Given a stale PID file /tmp/agy_tasks_server.pid referencing a dead process
When tasks_server.py checks daemon status or initiates startup
Then verify_pid detects that the process is no longer alive via signal 0
And the stale PID file is safely unlinked and replaced with the new process PID
```
