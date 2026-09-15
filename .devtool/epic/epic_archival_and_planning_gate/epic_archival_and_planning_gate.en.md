# Epic: Epic Done Archival & Antigravity Planning Gate

## 1. Meta Data
- **Epic**: epic-archival-and-planning-gate
- **Status**: In Progress
- **Target Release**: v1.0.15
- **Platform**: Cross-Platform Tooling (Agent Kit, Python, Bash, Markdown)
- **Source Spec**: [2026-09-15-epic-done-archival-and-antigravity-planning-gate-design.md](2026-09-15-epic-done-archival-and-antigravity-planning-gate-design.md)

---

## 2. Background
In multi-agent collaborative workflows across **Claude Code** and **Google Antigravity IDE**:
1. When an epic completes, finished tasks were lingering in `.devtool/features/done/`, and drafting artifacts were left in `docs/superpowers/`. There was no automated mechanism to relocate all completed tasks and related documents into the epic's permanent directory (`.devtool/epic/<epic_name>/`).
2. Google Antigravity IDE's `<planning_mode>` prompt caused AI agents to bypass the mandatory `<HARD-GATE>` of `d3nexus:brainstorming` and write `implementation_plan.md` in `brain/` directly.

This Epic delivers a unified automated archival engine in `sync_task_status.py` and a two-layer governance gate intercepting Antigravity's Planning Mode.

---

## 3. Goals & Non-Goals

### Goals
- Automatically move all `task_*.md` files from `.devtool/features/done/` into `.devtool/epic/<epic_dir>/` upon epic completion.
- Automatically relocate related specs and plans from `docs/superpowers/` into `.devtool/epic/<epic_dir>/`.
- Automatically rewrite relative Markdown links in task files and Section 8 of Epic Overviews to point to local files.
- Ensure `.gitkeep` files are preserved in emptied directories.
- Provide a two-layer defense in `rules/CRITICAL_RULES.md` and `hooks/session-start` preventing Antigravity from bypassing brainstorming.
- Update `epic-implementation`, `epic-lifecycle`, and `epic-designer` skills to reflect this lifecycle.

### Non-Goals
- Modifying unrelated skills or altering standard Kanban status values.

---

## 4. Architecture & Technical Design

### 4.1 High-Level Architecture
```mermaid
graph TD
    subgraph TRIGGER["Epic Done Event (Phase 4.1)"]
        QC["@quality_check 🟢 LGTM"]
        SYNC_CLI["sync_task_status.py epic <epic_dir> Done"]
    end

    subgraph ENGINE["Archival Engine (sync_task_status.py)"]
        DISCOVER["1. discover_epic_slug & match_tasks"]
        MOVE_TASKS["2. relocate .devtool/features/done/task_*.md -> .devtool/epic/<epic_dir>/"]
        MOVE_DOCS["3. relocate docs/superpowers/(specs|plans) -> .devtool/epic/<epic_dir>/"]
        REWRITE["4. rewrite relative links to local format"]
        CLEAN["5. remove source files & ensure .gitkeep"]
    end

    subgraph GOVERNANCE["Antigravity Governance Gate"]
        RULES["rules/CRITICAL_RULES.md (<user_rules> precedence)"]
        HOOK["hooks/session-start (Turn 0 injection)"]
        INTERCEPT["Intercept <planning_mode> -> Force d3nexus:brainstorming"]
    end

    QC --> SYNC_CLI
    SYNC_CLI --> DISCOVER
    DISCOVER --> MOVE_TASKS
    DISCOVER --> MOVE_DOCS
    MOVE_TASKS --> REWRITE
    MOVE_DOCS --> REWRITE
    REWRITE --> CLEAN

    RULES --> INTERCEPT
    HOOK --> INTERCEPT
```

### 4.2 Use Cases
```mermaid
flowchart TD
    DEV["Developer / AI Agent"]
    AG_RUNTIME["Antigravity IDE Runtime"]

    subgraph UC1["UC1: Automated Task & Document Archival"]
        U1["Mark Epic Done (CLI/Script)"]
        U2["Move done tasks from features/done to epic folder"]
        U3["Centralize docs/superpowers into epic folder"]
        U4["Rewrite relative Markdown links"]
    end

    subgraph UC2["UC2: Antigravity Planning Gate"]
        U5["Trigger Planning Mode"]
        U6["Intercept plan mode via CRITICAL_RULES & Hook"]
        U7["Force d3nexus:brainstorming invocation"]
    end

    DEV --> U1
    U1 --> U2
    U1 --> U3
    U2 --> U4

    AG_RUNTIME --> U5
    U5 --> U6
    U6 --> U7
```

### 4.3 Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer / Lead Agent
    participant Script as sync_task_status.py
    participant Features as .devtool/features/done/
    participant Superpowers as docs/superpowers/
    participant EpicDir as .devtool/epic/<epic_dir>/
    participant Rules as rules/CRITICAL_RULES.md

    Note over Dev,Script: Phase 4.1 Epic Done Archival
    Dev->>Script: sync_task_status.py epic <epic_dir> Done
    Script->>Features: scan task_*.md matching epic
    Script->>Superpowers: scan specs & plans matching epic
    Script->>EpicDir: move tasks and docs, rewrite links
    Script->>Features: remove sources, ensure .gitkeep
    Script->>Superpowers: remove sources, ensure .gitkeep
    Script-->>Dev: report archived tasks & updated status

    Note over Dev,Rules: Antigravity Planning Mode Gate
    Dev->>Rules: check planning rules on user request
    Rules-->>Dev: MUST invoke d3nexus:brainstorming first
```

### 4.4 Check 1 (Shift-Left Impact Analysis)
- **Target Files**:
  - `skills/epic-implementation/resources/scripts/sync_task_status.py`
  - `skills/epic-implementation/resources/scripts/test_sync_task_status.py`
  - `rules/CRITICAL_RULES.md`
  - `hooks/session-start`
  - `skills/epic-implementation/SKILL.md`
  - `skills/epic-lifecycle/SKILL.md`
  - `skills/epic-designer/SKILL.md`
- **Blast Radius**: Zero breaking changes to existing test suite or CLI invocation. Fully backward-compatible with 39 passing unit tests.

### 4.5 Comprehensive BDD Test Scenarios
Documented in detail in [bdd_scenarios.md](bdd_scenarios.md).

---

## 5. BDD Output in Epic Directory
The complete behavioral specifications are committed to [bdd_scenarios.md](bdd_scenarios.md).

---

## 6. Rollout Strategy & Mitigation
- **Phased Rollout**: Implement within `ai-agent-tools`, run full unit test and verification suite, and release v1.0.15 via `scripts/release.sh`.
- **Mitigation**: All file operations verify source existence before unlinking and preserve `.gitkeep` to prevent git working tree divergence.

---

## 7. Kanban Tasks Breakdown
- [Task 1: Complete Archival Engine and Link Rewriter in sync_task_status.py](task_1_archival_engine_and_link_rewriter.md)
- [Task 2: Implement Antigravity Planning Gate in CRITICAL_RULES and Hook](task_2_antigravity_planning_gate.md)
- [Task 3: Update Workflow Skills Documentation](task_3_workflow_skills_documentation.md)
- [Task 4: Complete Workspace Archival, Kit Verification, and Release](task_4_workspace_verification_and_release.md)
