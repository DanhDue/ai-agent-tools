# Behavior-Driven Development (BDD) Scenarios: Epic Done Archival & Antigravity Planning Gate

This document defines the formal behavioral specifications in Gherkin syntax (`Given - When - Then`) for the **epic-archival-and-planning-gate** epic.

---

## UC1: Automated Task & Document Archival on Epic Completion

### Scenario 1.1: Automatic Archival Triggered by `sync_epic Done`
- **Given** an epic with slug `logging-refactor` and directory `logging_refactor` has completed all its tasks
- **And** completed task files `task_1_setup.md` and `task_2_core.md` reside in `.devtool/features/done/`
- **And** draft specs/plans matching `logging-refactor` reside in `docs/superpowers/plans/` and `docs/superpowers/specs/`
- **When** the developer or agent runs `sync_task_status.py epic logging_refactor Done`
- **Then** the status in `logging_refactor.en.md` and `logging_refactor.vi.md` updates to `Done`
- **And** `task_1_setup.md` and `task_2_core.md` are moved into `.devtool/epic/logging_refactor/`
- **And** source task files are removed from `.devtool/features/done/`
- **And** a `.gitkeep` file is created/retained in `.devtool/features/done/`
- **And** draft specs/plans are moved from `docs/superpowers/` into `.devtool/epic/logging_refactor/`
- **And** `.gitkeep` files are retained in `docs/superpowers/plans/` and `docs/superpowers/specs/`

### Scenario 1.2: Standalone CLI Archival via `archive-epic`
- **Given** completed task files exist in `.devtool/features/done/` matching an epic
- **When** the user executes `python3 sync_task_status.py archive-epic <epic_dir>`
- **Then** all matching task files and superpowers documents are archived into `.devtool/epic/<epic_dir>/`
- **And** the CLI reports the count of archived tasks and cleaned source files with exit code `0`

### Scenario 1.3: Relative Link Rewriting in Archived Task Files
- **Given** a task file in `.devtool/features/done/` contains:
  - `Epic: [slug](../epic/my_epic/my_epic.en.md)`
  - `Blocks: [Task 2](../../features/task_2.md)`
  - `Reference: [HLD](../epic/my_epic/my_epic.en.md#section)`
- **When** `archive_epic_tasks` relocates the file into `.devtool/epic/my_epic/`
- **Then** the parent epic link is rewritten to `Epic: [slug](my_epic.en.md)`
- **And** the dependency link is rewritten to `Blocks: [Task 2](task_2.md)`
- **And** the reference link is rewritten to `Reference: [HLD](my_epic.en.md#section)`

### Scenario 1.4: Relative Link Rewriting in Epic Overview Section 8
- **Given** `my_epic.en.md` and `my_epic.vi.md` contain Section 8 links pointing to `../../features/task_1.md` or `../../features/done/task_1.md`
- **When** `archive_epic_tasks` executes for `my_epic`
- **Then** Section 8 links in both `.en.md` and `.vi.md` are rewritten to local links `task_1.md`

### Scenario 1.5: Idempotency & Preserving Existing Files
- **Given** `archive_epic_tasks` has already run once for an epic
- **When** `archive_epic_tasks` runs a second time
- **Then** no errors occur, no files are duplicated or corrupted, and exit code is `0`

---

## UC2: Antigravity Planning Mode Interception

### Scenario 2.1: Turn 0 Prompt Injection via Session-Start Hook
- **Given** an Antigravity IDE session starts on turn 0 (`invocationNum == 0`)
- **When** `hooks/session-start` executes
- **Then** it injects an `ephemeralMessage` containing `d3nexus:using-superpowers`
- **And** it injects explicit instructions warning against creating `implementation_plan.md` directly
- **And** it mandates that any planning requirement must invoke `d3nexus:brainstorming` or `d3nexus:epic-lifecycle`

### Scenario 2.2: Precedence Rule in `rules/CRITICAL_RULES.md`
- **Given** Antigravity IDE parses plugin rules into system `<user_rules>`
- **When** the AI Agent receives a user prompt that warrants planning
- **Then** the mandatory rule in `rules/CRITICAL_RULES.md` takes precedence over Antigravity's built-in `<planning_mode>`
- **And** the agent halts direct plan writing and invokes `d3nexus:brainstorming` or `d3nexus:epic-lifecycle`

---

## UC3: Regression Testing & Kit Verification

### Scenario 3.1: Complete Unit Test Suite Verification
- **Given** the enhanced `sync_task_status.py` script
- **When** `python3 test_sync_task_status.py -v` is executed
- **Then** all 39 unit tests pass with zero failures and zero errors

### Scenario 3.2: Kit Manifest and Hook Verification
- **Given** all updated rules, hooks, and skill files
- **When** `bash scripts/verify.sh` is executed
- **Then** JSON manifests, frontmatter rules, link resolution, ToC anchors, and hook JSON outputs all report `PASS`
