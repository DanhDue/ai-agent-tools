# BDD Scenarios: Dual-Workspace Kanban Sync & Impact Analysis

- **Epic**: kanban-sync-impact-analysis
- **Parent HLD**: [kanban_sync_impact_analysis.en.md](kanban_sync_impact_analysis.en.md)
- **Status**: Contract Frozen

---

## Dimension 1: Happy Paths & Standard Lifecycle

### Scenario 1.1: Live Dual-Workspace Status Synchronization across All Checkouts
- **Tag**: `[Tier A - Unit]`
- **Given** an epic task `task_1_setup` exists in both `.devtool/features/` and `.devtool/epic/kanban_sync_impact_analysis/` across a main checkout and an isolated git worktree `.worktrees/kanban_sync_impact_analysis`
- **When** the developer or agent executes `sync_task_status.py task task_1_setup in-progress`
- **Then** all 4 copies of `task_1_setup.md` must have their frontmatter `status:` updated to `"in-progress"`
- **And** all 4 copies must have their `modified:` field updated to the current ISO-8601 UTC timestamp ending in `Z`
- **And** the document body and all unrelated frontmatter keys (`priority`, `assignee`, `labels`, `order`) must remain preserved byte-for-byte
- **And** the script must exit with status code `0` and output the board tally.

### Scenario 1.2: CompletedAt Timestamp Invariant on Done
- **Tag**: `[Tier A - Unit]`
- **Given** an epic task is in `"review"` with `completedAt: null`
- **When** the reviewer approves and executes `sync_task_status.py task task_1_setup done`
- **Then** `status:` becomes `"done"`
- **And** `completedAt:` must be populated with the current ISO-8601 UTC timestamp
- **And** `modified:` must match the same current timestamp.

### Scenario 1.3: Epic Overview Status Synchronization
- **Tag**: `[Tier A - Unit]`
- **Given** both `kanban_sync_impact_analysis.en.md` and `kanban_sync_impact_analysis.vi.md` exist with `Status: Planned`
- **When** `sync_task_status.py epic kanban_sync_impact_analysis "In Progress"` is executed
- **Then** the Meta Data `Status:` line in both the `.en.md` and `.vi.md` files must be updated to `"In Progress"`
- **And** neither language variant may diverge from the other.

---

## Dimension 2: Edge Cases, Boundaries & Schema Rejections

### Scenario 2.1: Rejection of Invalid Status Enumerations
- **Tag**: `[Tier A - Unit]`
- **Given** a user or agent invokes `sync_task_status.py task task_1_setup blocked`
- **When** the status argument is evaluated against the 5-column enum (`backlog`, `todo`, `in-progress`, `review`, `done`)
- **Then** the script must refuse to write to any file
- **And** print an error to stderr stating `Invalid status 'blocked'. Expected one of: backlog, todo, in-progress, review, done`
- **And** exit with code `2`.

### Scenario 2.2: Epic Collision Guard across Duplicate Task IDs
- **Tag**: `[Tier A - Unit]`
- **Given** a task `task_1_setup` exists under `epic: "kanban-sync-impact-analysis"` in `.devtool/features/`
- **And** a different task with the same filename `task_1_setup.md` exists under `.devtool/epic/payments/` with `epic: "payments"`
- **When** `sync_task_status.py task task_1_setup in-progress` is invoked
- **Then** the file under `payments/` must be skipped
- **And** a warning note must be printed reporting the epic mismatch
- **And** only the copies belonging to `"kanban-sync-impact-analysis"` may be updated.

### Scenario 2.3: Insertion of Absent Frontmatter Keys
- **Tag**: `[Tier A - Unit]`
- **Given** a legacy task file created without `modified:` or `completedAt:` fields
- **When** `sync_task_status.py task legacy_task done` is invoked
- **Then** `modified:` and `completedAt:` must be inserted directly following `status:`
- **And** existing keys and markdown body must not be corrupted.

---

## Dimension 3: Pre-Edit Impact & Git Conflict Verification

### Scenario 3.1: Upstream Git Divergence Detection
- **Tag**: `[Tier A - Unit]`
- **Given** an epic branch is working on `features/payment/PaymentRepository.kt`
- **And** the base branch `<base_ref>` (`develop`) has received new commits touching `PaymentRepository.kt` that are unmerged into the current branch
- **When** `check_code_impact.py --files features/payment/PaymentRepository.kt --base-ref develop` is run
- **Then** the report must flag `Git Conflict: 🔴 DIVERGENCE DETECTED`
- **And** list the upstream unmerged commits
- **And** recommend rebasing before making edits.

### Scenario 3.2: Blast Radius & Downstream Callers Identification
- **Tag**: `[Tier A - Unit]`
- **Given** class `PaymentRepository` in module `:features:payment` is imported by `PaymentViewModel.kt` and `CheckoutFlow.kt`
- **When** `check_code_impact.py --files features/payment/PaymentRepository.kt --symbols PaymentRepository` is executed
- **Then** the tool must list both dependent files with exact line numbers
- **And** calculate the blast radius across module boundaries.

### Scenario 3.3: Cross-Platform MethodChannel String Detection
- **Tag**: `[Tier A - Unit]`
- **Given** a Flutter file invokes `MethodChannel('com.example.app/biometrics')`
- **And** Native Android Kotlin implements `MethodChannel(..., "com.example.app/biometrics")`
- **And** Native iOS Swift implements `FlutterMethodChannel(name: "com.example.app/biometrics", ...)`
- **When** `check_code_impact.py` runs on the Flutter file
- **Then** it must identify the native Android and iOS plugin files
- **And** flag `Cross-Platform Bridge: ⚠️ NATIVE BRIDGE DETECTED` with exact file paths.

---

## Dimension 4: Test Impact Analysis (TIA) & Coverage Discipline

### Scenario 4.1: Unprotected Code & Coverage Blind-Spot Warning
- **Tag**: `[Tier A - Unit]`
- **Given** a function `processRefund()` in `PaymentService.kt` has no associated unit test file or 0% coverage in reports
- **When** `check_code_impact.py` inspects the function
- **Then** the report must display `Coverage Safety Net: ⚠️ UNPROTECTED CODE (0% Coverage)`
- **And** prompt the developer/agent to write baseline characterization tests before altering code.

### Scenario 4.2: Missing Logic Cases Detection against 5 BDD Dimensions
- **Tag**: `[Tier A - Unit]`
- **Given** a method handles network requests with a catch block for timeout
- **And** existing test suite only asserts the happy path 200 OK
- **When** impact analysis analyzes test scenario coverage
- **Then** it must warn `Missing Logic Alert: Timeout / Failure handling is untested`
- **And** require adding an edge scenario to the task's BDD specification.

---

## Dimension 5: End-of-Epic Reverse Verification & Clean Merge Invariants

### Scenario 5.1: Reverse Verification against 4 Semantic Audits at Gate 4
- **Tag**: `[Tier C - Integration]`
- **Given** all tasks in the epic are marked `done`
- **When** `@quality_check` runs on the worktree
- **Then** platform test suite coverage is computed (`lcov.info` / JaCoCo / `xccov`)
- **And** security-critical files must demonstrate 100% test coverage
- **And** architecture domain use cases must demonstrate $\ge 85\%$ coverage
- **And** Gate 4 grants `🟢 LGTM` only when both 3-Tier tests, 4 semantic audits, and the Coverage Matrix pass.

### Scenario 5.2: Main Checkout Mirror Reversion before Merge
- **Tag**: `[Tier C - Integration]`
- **Given** the main checkout contains mirrored `.devtool/features/*.md` files updated during task execution
- **When** Phase 4 executes `git -C "$MAIN_ROOT" restore -- .devtool/features/ .devtool/epic/<epic_dir>/`
- **Then** `git -C "$MAIN_ROOT" status --porcelain` must be completely clean
- **And** merging the epic branch into `<base_ref>` must execute with zero git working tree collision.
