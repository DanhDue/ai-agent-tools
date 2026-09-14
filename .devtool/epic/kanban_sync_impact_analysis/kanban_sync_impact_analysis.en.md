# Epic: Dual-Workspace Kanban Synchronization & Pre-Edit Impact Analysis

## 1. Meta Data
- **Epic**: kanban-sync-impact-analysis
- **Status**: In Progress
- **Target Release**: v1.1.0
- **Platform**: Cross-Platform Tooling (Flutter, Android Native, iOS Native)
- **Source Spec**: [2026-09-15-epic-kanban-sync-and-impact-analysis-design.md](2026-09-15-epic-kanban-sync-and-impact-analysis-design.md)

---

## 2. Background
In multi-agent and multi-worktree mobile software engineering across **Flutter**, **Android Native**, and **iOS Native**:
1. **Multi-Workspace Drift**: Work executed inside isolated git worktrees (`.worktrees/<epic_dir>`) leaves tasks in the main checkout frozen at `todo`, resulting in stale Kanban boards for developers watching the primary IDE window. Timestamps (`modified`, `completedAt`) are rarely updated or maintained uniformly.
2. **Blind Modifications & Regressions**: Developers and autonomous AI agents modifying existing source code often cause merge conflicts against outdated base refs, break downstream callers across package boundaries, alter public API/ABI contracts unexpectedly, and introduce runtime crashes in cross-platform bridges (e.g., Flutter `MethodChannel` $\leftrightarrow$ Kotlin/Swift).
3. **Unprotected Logic & Coverage Blind-Spots**: Editing code without baseline test coverage or neglecting BDD/TDD edge cases (nulls, timeout, offline, race conditions) introduces regressions that evade standard compile-time checks.

---

## 3. Goals & Non-Goals

### Goals
- **Dual-Workspace Live Synchronization**: Mirror every status transition (`backlog`, `todo`, `in-progress`, `review`, `done`) across all checkouts returned by `git worktree list --porcelain`, maintaining ISO-8601 UTC Zulu timestamps (`created`, `modified`, `completedAt`).
- **Dedicated `impact-analysis` Skill & Pre-Edit Checker**: Provide an automated 4-layer inspection pipeline (`check_code_impact.py` + reference manual `references/impact-mechanisms.md`):
  1. *Layer 1 (Git Conflicts)*: Detects divergence against `<base_ref>` and dirty worktree collisions.
  2. *Layer 2 (Architecture Blast Radius)*: Identifies all callers and module boundaries using fast symbol search (`ripgrep`).
  3. *Layer 3 (Cross-Platform Bridge)*: Detects Flutter `MethodChannel` and `EventChannel` couplings with Native handlers.
  4. *Layer 4 (Test Impact Analysis & Coverage)*: Maps source files to test suites, flags unprotected code (low coverage), and exposes missing edge case branches.
- **Workflow & Quality Integration**:
  - `epic-designer`: Enforces `### Impact Analysis & Blast Radius` and test coverage targets in task definitions and process diagrams.
  - `epic-implementation`: Enforces Pre-Edit Step 0 impact checking before code edits, process flow diagram updates, and live status flips.
  - `quality_check`: Enforces 3-Tier test runs with test coverage computed per platform and reverse-verified against 4 semantic audit categories (Security 100%, Architecture $\ge 85\%$, UI, Code Health).
  - `epic-lifecycle`: Updates Gate 2, Gate 3, and Gate 4 checkpoints and process flows.
- **Clean Teardown**: Automatically restore main checkout mirror copies in Phase 4 prior to branch merge.

### Non-Goals
- Replacing native compilers or static analysis linters: `check_code_impact.py` acts as a pre-flight guide; native compilers and Tier C tests remain the final dynamic enforcers.
- Expanding the status enum: Strictly five columns (`backlog | todo | in-progress | review | done`).

---

## 4. Architecture & Technical Design

### High-Level Architecture
```mermaid
flowchart TD
    subgraph KANBAN_SYNC["Dual-Workspace Kanban Synchronization"]
        SYNC_TOOL["sync_task_status.py"]
        WT_DISCOVER["git worktree list --porcelain"]
        WT_DISCOVER --> SYNC_TOOL
        SYNC_TOOL -->|Mirror Write| F_MAIN[".devtool/features/*.md (Main)"]
        SYNC_TOOL -->|Mirror Write| E_MAIN[".devtool/epic/*/*.md (Main)"]
        SYNC_TOOL -->|Mirror Write| F_WT[".devtool/features/*.md (Worktree)"]
        SYNC_TOOL -->|Mirror Write| E_WT[".devtool/epic/*/*.md (Worktree)"]
    end

    subgraph IMPACT_ENGINE["@impact-analysis Skill Engine (check_code_impact.py)"]
        direction LR
        L1["Layer 1: Git & Worktree Divergence"] --> L2["Layer 2: Blast Radius & Callers (ripgrep)"] --> L3["Layer 3: Cross-Platform Bridge (MethodChannel)"] --> L4["Layer 4: Test Impact & Coverage (TIA)"]
        L4 --> REPORT["Unified Impact Report"]
    end

    subgraph WORKFLOW_INTEGRATION["Epic Lifecycle with DOUBLE-CHECK (BOOKEND) MECHANISM"]
        STAGE2["1. CHECK 1: Design-Time (Shift-Left)<br/>Stage 2: epic-designer<br/>(Predict Blast Radius, Lock Contracts & Coverage DoD)"]
        STAGE3["2. INTERMEDIATE: Before Code Edits<br/>Stage 3: epic-implementation<br/>(Step 0 Pre-Edit Check & Live Kanban Sync)"]
        STAGE4["3. CHECK 2: Merge-Time (Shift-Right)<br/>Stage 4: quality_check (Gate 4)<br/>(Verify Actual Diff, develop divergence & Audit Coverage Matrix)"]
        
        STAGE2 -->|Handoff Spec & Tasks| STAGE3
        STAGE3 -->|Handoff Completed Code| STAGE4
    end

    %% Explicit Double-Check connections
    REPORT ==>|"CHECK 1 (Shift-Left): Predict blast radius & author tasks"| STAGE2
    REPORT -.->|"Intermediate Check: Safety gate before code edits"| STAGE3
    REPORT ==>|"CHECK 2 (Shift-Right): Verify actual diff against base_ref"| STAGE4

    SYNC_TOOL -.->|"Live 2-way status flips"| STAGE3
```

### Use Cases Flowchart
```mermaid
flowchart TB
    ACTOR["Mobile Engineer / AI Agent"]
    
    subgraph USE_CASES["Epic Lifecycle Use Cases (1 -> 2 -> 3 Left to Right)"]
        direction LR
        subgraph UC1["1. Use Case 1: Task State Transition"]
            direction TB
            UC1_START["Trigger Status Transition"] --> UC1_EXEC["Run sync_task_status.py task <id> <status>"]
            UC1_EXEC --> UC1_FANOUT["Fan out to Main & Worktree copies"]
            UC1_FANOUT --> UC1_TIME["Update modified & completedAt timestamps"]
        end

        subgraph UC2["2. Use Case 2: Pre-Edit Impact Verification"]
            direction TB
            UC2_START["Pick up Task for Implementation"] --> UC2_CHECK["Run check_code_impact.py"]
            UC2_CHECK --> UC2_VERIFY{"Conflict or High Risk?"}
            UC2_VERIFY -->|Yes| UC2_HALT["Halt & alert Engineer"]
            UC2_VERIFY -->|No| UC2_CONT["Proceed with TDD Red-Green-Refactor"]
        end

        subgraph UC3["3. Use Case 3: End-of-Epic Audit & Coverage Gate"]
            direction TB
            UC3_START["All Tasks Done"] --> UC3_RUN["Run @quality_check with Coverage"]
            UC3_RUN --> UC3_REVERSE["Reverse Verify Coverage against 4 Audits"]
            UC3_REVERSE --> UC3_GATE{"All Pass & Coverage Met?"}
            UC3_GATE -->|Yes| UC3_MERGE["Gate 4 🟢 LGTM: Clean & Merge"]
            UC3_GATE -->|No| UC3_FAIL["Fix Findings / Add Tests"]
        end

        UC1 ~~~ UC2 ~~~ UC3
    end

    ACTOR --> UC1_START
    ACTOR --> UC2_START
    ACTOR --> UC3_START
```

### Primary Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    participant Agent as Lead Agent / Developer
    participant Sync as sync_task_status.py
    participant Impact as @impact-analysis (check_code_impact.py)
    participant Disk as Dual Workspace Disk
    participant TDD as Tri-Persona TDD Engine
    participant QC as @quality_check (Gate 4)

    Note over Agent, Disk: Phase 2: Sequential Task Execution
    Agent->>Sync: task <task_id> in-progress
    Sync->>Disk: Mirror status & modified across all worktrees
    Sync-->>Agent: Wrote 4 copies + tally

    Agent->>Impact: --files <target_files> --base-ref develop
    Impact->>Disk: Check git log base_ref...HEAD
    Impact->>Disk: Scan symbol callers via ripgrep
    Impact->>Disk: Scan MethodChannel references across Dart/Kotlin/Swift
    Impact->>Disk: Map test files & evaluate coverage baseline
    Impact-->>Agent: Unified Impact Report (🟢 Clean to proceed)

    Agent->>TDD: Implement BDD Scenarios (RED -> GREEN -> REFACTOR)
    TDD-->>Agent: Unit tests passing with target coverage

    Agent->>Sync: task <task_id> review
    Sync->>Disk: Mirror review status
    Agent->>Sync: task <task_id> done
    Sync->>Disk: Mirror done status & completedAt timestamp

    Note over Agent, QC: Phase 4: End-of-Epic Verification
    Agent->>QC: Run full quality check & coverage verification
    QC->>Disk: Run testWithCoverage.sh / Jacoco / xccov
    QC->>QC: Reverse verify coverage against Security/Arch/UI/CodeHealth
    QC-->>Agent: 🟢 LGTM (Audit Coverage Matrix Passed)
    Agent->>Disk: git restore main checkout mirror copies
    Agent->>Disk: Merge epic branch to develop
```

---

## 5. Process Flow & Diagram Updates by Skill

### 5.1 `skills/epic-lifecycle/SKILL.md` Process Flow Update
The lifecycle orchestrator sequence is upgraded to enforce Impact Analysis at Gate 2, conflict-free base ref at Gate 3, and Coverage Reverse Verification at Gate 4:

```mermaid
flowchart TD
    S1["Stage 1 — Inception & Spec<br/>(brainstorming)"]
    G1{"Gate 1<br/>Spec approved?"}
    ROUTE{"Epic-scale?"}
    PLANS(["writing-plans<br/>(leaves workflow)"])
    S2["Stage 2 — Architecture & Tasks<br/>(epic-designer)"]
    G2{"Gate 2<br/>HLD & Task Breakdown approved?<br/><b>* Includes Impact Matrix & Coverage DoD</b>"}
    S3["Stage 3 — Isolated Execution<br/>(epic-implementation)"]
    G3{"Gate 3<br/>Execution Order & Base Ref confirmed?<br/><b>* Verified zero git merge conflicts</b>"}
    EXEC["Phase 2: Pre-Edit Impact Check + Task TDD<br/>Live dual-workspace sync, one commit/task"]
    G4{"Gate 4<br/>quality_check 🟢 LGTM?<br/><b>* Passes 3-Tier + 4 Audits + Coverage Matrix</b>"}
    S4["Stage 4 — Finish Branch<br/>(finishing-a-development-branch)"]

    S1 --> G1
    G1 -->|no, revise| S1
    G1 -->|yes| ROUTE
    ROUTE -->|no| PLANS
    ROUTE -->|yes| S2
    S2 --> G2
    G2 -->|no, adjust| S2
    G2 -->|yes| S3
    S3 --> G3
    G3 -->|no, reorder/re-pick ref| G3
    G3 -->|yes| EXEC
    EXEC --> G4
    G4 -->|no, fix findings| EXEC
    G4 -->|yes| S4
```

### 5.2 `skills/epic-implementation/SKILL.md` Phase 2 Process Flow Update
The Phase 2 loop inside `epic-implementation` is updated to include Step 0 (Pre-Edit Impact Check) and live dual-workspace status flips:

```mermaid
flowchart TB
    T_START["Pick Next Task in Order"] --> SYNC_INP["1. sync_task_status.py task <id> in-progress<br/>(Mirrors all 4 copies across checkouts)"]
    SYNC_INP --> STEP0["2. Step 0: Pre-Edit Impact & Conflict Check<br/>(@impact-analysis / check_code_impact.py)"]
    STEP0 --> CHK_RES{"Impact / Git Risk?"}
    CHK_RES -->|🔴 Git Conflict / Unprotected Code| HALT["Halt & Prompt User/Lead Agent"]
    CHK_RES -->|🟢 Clean / Acknowledged| RED["3. RED: Author failing tests from BDD scenarios"]
    RED --> GREEN["4. GREEN: Implement minimal feature code"]
    GREEN --> REFACTOR["5. REFACTOR: Clean code, verify coverage threshold"]
    REFACTOR --> SYNC_REV["6. sync_task_status.py task <id> review"]
    SYNC_REV --> REVIEWS{"Code Reviews Passed?"}
    REVIEWS -->|Changes Needed| STEP0
    REVIEWS -->|Approved| SYNC_DONE["7. sync_task_status.py task <id> done<br/>(Records completedAt timestamp)"]
    SYNC_DONE --> COMMIT["8. Git Commit: [EPIC] Task title (Worktree copies)"]
    COMMIT --> NEXT_TASK{"More Tasks in Order?"}
    NEXT_TASK -->|Yes| T_START
    NEXT_TASK -->|No| PHASE4["Phase 4: @quality_check & Main Checkout Cleanup"]
```

### 5.3 `skills/quality_check/SKILL.md` Dual-Track & Reverse Verification Update
The `@quality_check` orchestrator diagram is updated to pair automated platform test coverage with semantic audit reverse verification:

```mermaid
flowchart TD
    START(["Trigger: @quality_check"]) --> DETECT{"Detect Platform<br/>(Flutter / Android / iOS)"}

    subgraph TRACK1["Track 1: Platform Automated 3-Tier Suite + Coverage"]
        T1["Tier A: Package / Unit Tests"]
        T2["Tier B: Architecture Governance & Linters"]
        T3["Tier C: Acceptance & Integration Harness"]
        COV["Compute Coverage Data<br/>(Flutter: lcov.info / Android: Jacoco/Kover / iOS: xccov)"]
        T1 --> T2 --> T3 --> COV
    end

    subgraph TRACK2["Track 2: Parallel Semantic Audits"]
        A_SEC["@security-audit (Fintech & OWASP)"]
        A_ARCH["@architecture-audit (Clean Arch Boundaries)"]
        A_UI["@ui-audit (Performance & Lifecycle)"]
        A_CODE["@code-health-audit (Clean Code & Safety)"]
    end

    DETECT --> TRACK1
    DETECT --> TRACK2

    subgraph REVERSE_VERIFY["Reverse Verification: Coverage by Audit Category Matrix"]
        COV & A_SEC --> V_SEC["Verify Security Logic: 100% Coverage Required"]
        COV & A_ARCH --> V_ARCH["Verify Domain/Repositories: >= 85% Coverage Required"]
        COV & A_UI --> V_UI["Verify UI State Hoisting & View Lifecycle Covered"]
        COV & A_CODE --> V_CODE["Verify Branch Coverage on Complex Logic"]
        V_SEC & V_ARCH & V_UI & V_CODE --> MATRIX["Coverage-by-Audit Category Matrix"]
    end

    MATRIX --> REPORT["Unified Executive Quality Report"]
    REPORT --> VERDICT{"All 3 Tiers Green +<br/>Audits Green +<br/>Coverage Met?"}
    VERDICT -->|Yes| PASS["🟢 LGTM (Merge Permitted)"]
    VERDICT -->|No| FAIL["🔴 Blocked (Remediate Issues)"]
```

### 5.4 The Double-Check Mechanism (Bookend Verification: Design-time & Merge-time)

To guarantee end-to-end reliability and eliminate blind spots, `@impact-analysis` is applied as a **Double-Check (Bookend) Mechanism** operating at both ends of the development lifecycle:

```mermaid
flowchart LR
    subgraph CHECK1["CHECK 1: Design-Time (Shift-Left)"]
        D1["Brainstorming & epic-designer"]
        D1 -->|Invoke impact-analysis| R1["Predict Blast Radius, Map Callers,<br/>Expose Bridge & Coverage Needs"]
    end

    subgraph CHECK_MID["INTERMEDIATE: Pre-Edit"]
        M1["epic-implementation (Phase 2)"]
        M1 -->|Step 0 Just-In-Time Check| R2["Confirm file safety before coding"]
    end

    subgraph CHECK2["CHECK 2: Merge-Time (Shift-Right)"]
        Q1["quality_check (Gate 4)"]
        Q1 -->|Invoke impact-analysis on git diff| R3["Verify Actual Diff vs Spec,<br/>Check develop divergence & Coverage Matrix"]
    end

    CHECK1 --> CHECK_MID --> CHECK2
```

#### Why the Double-Check Mechanism is Tremendously More Effective:
1. **Closed-Loop Feedback**:
   - *Check 1 (Planning / Design-Time)*: Establishes the expected blast radius, informs task decomposition, and identifies missing logic cases before a single line of code is written (cheapest time to fix design flaws).
   - *Check 2 (Gate 4 / Merge-Time)*: Inspects the *actual* `git diff` against the updated base branch. Catches any scope creep, unpredicted file edits, or missing test coverage that arose during implementation.
2. **Eliminates Merge Surprises in Long-Running Epics**:
   - While an epic is being implemented over days or weeks, `<base_ref>` (`develop`) moves forward. Check 2 re-evaluates divergence against the latest upstream commits right before merge, ensuring zero merge collisions.
3. **Accountability & Integrity**:
   - Proves mathematically that what was planned in Check 1 was faithfully and safely executed in Check 2.


---

## 6. BDD Output in Epic Directory (`bdd_scenarios.md`)
A dedicated behavioral specification contract is maintained in `bdd_scenarios.md` alongside this HLD, formalizing:
1. Status transition symmetry and timestamp integrity across worktrees.
2. Rejection of invalid status enumerations.
3. Pre-flight Git conflict detection and upstream divergence warnings.
4. Cross-module caller mapping and boundary protection.
5. Cross-platform MethodChannel identification.
6. Coverage blind-spot alerting and missing logic detection.
7. Main checkout cleanup and safe merge invariants.

---

## 7. Rollout Strategy & Mitigation
- **Phased Rollout**:
  - Phase 1: Deploy `sync_task_status.py` and `test_sync_task_status.py` to stabilize cross-workspace Kanban sync.
  - Phase 2: Deploy `check_code_impact.py` and `test_check_code_impact.py` to enable automated pre-edit checking.
  - Phase 3: Publish `skills/impact-analysis/` and reference documentation.
  - Phase 4: Integrate workflows across `epic-designer`, `epic-implementation`, `quality_check`, and `epic-lifecycle`.
- **Mitigation & Fallback**:
  - `sync_task_status.py` preserves unparseable documents and fails loud on ambiguity without corrupting text.
  - `check_code_impact.py` provides non-destructive read-only static analysis. If coverage reports are absent, it degrades gracefully to static test-file mapping without breaking execution.
  - Main checkout restoration uses `git restore` without `--staged`, preserving developer manual stages.

---

## 8. Kanban Tasks Breakdown
- [Task 1: Complete and Wire Dual-Workspace Status Synchronizer](../../features/task_1_kanban_sync_status.md)
- [Task 2: Build Pre-Edit Impact and Conflict Checker](../../features/task_2_pre_edit_impact_checker.md)
- [Task 3: Author Dedicated Impact Analysis Skill and Reference Manual](../../features/task_3_impact_analysis_skill.md)
- [Task 4: Integrate Workflow Gates in Epic Designer and Epic Implementation](../../features/task_4_workflow_integration.md)
- [Task 5: Integrate Quality Check Test Coverage and Reverse Verification Gate](../../features/task_5_quality_check_coverage_gate.md)
