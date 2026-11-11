---
name: check-tasks
description: Real-time Cross-Repo Tasks & Context Dashboard and CLI monitor across multi-repository workspaces.
---

# Check Tasks (Cross-Repo Tasks & Context Dashboard)

Monitors Kanban tasks progress, Two-Tier context memory, lifecycle state machines, and Cross-Model Review findings across multi-repository workspaces (`/Users/danhdueexoictif/AllProjects`).

## When to Use

- Whenever you need an executive overview of active epics, tasks, and Git worktrees across repositories.
- To inspect Kanban board states (Backlog, Todo, In-Progress, Review, Done) across projects in a single view.
- To compare Two-Tier memory (`PROJECT_LEDGER.md` milestone ledger vs active assistant state snapshot).
- To track Cross-Model Review findings (5-column triage table and raw evidence) without switching repositories.
- To launch isolated Antigravity IDE windows or terminal CLI subshells with Rule 9 environment sanitization.

## Invocations & Commands

### 1. In AI Agent Chat (Skill Invocations)

When this skill is invoked via `/check-tasks` or natural language (e.g., *"check tasks"*, *"hiển thị dashboard tiến độ tasks"*), the AI assistant will:
1. Scan workspace repositories via `scripts/check_tasks.py` and output current Kanban progress and next human actions.
2. Provide the option to launch the interactive Dark Mode Web Companion dashboard:
   ```bash
   check-tasks --ui
   ```

### 2. Terminal CLI Commands

The `check-tasks` executable CLI is available globally via `bin/check-tasks`:

| Command | Description |
|---|---|
| `check-tasks` | View detailed card for the current repository and active epic |
| `check-tasks <repo>` | View detailed card for a specific repository (e.g. `check-tasks lyrics-sync`, `check-tasks D3Nexus`) |
| `check-tasks all` | Scan all repositories across workspace in parallel and display rich ANSI summary table |
| `check-tasks --ui` or `check-tasks --web` | Launch the interactive Dark Mode Web Dashboard daemon and open in default browser |
| `check-tasks --ui -f` | Run Web Dashboard server in foreground mode (useful for debugging) |
| `check-tasks --stop` | Gracefully shut down background Web Dashboard server daemon |
| `check-tasks --status` | Check running state, PID, URL, and port of Web Dashboard server |
| `check-tasks -h` | Display help and usage options |

## Architecture & Core Modules

The `check-tasks` system consists of five modular, deterministic components:
1. **Harvester Engine (`check_tasks.py`)**: Asynchronous multi-repo scanner discovering active Git worktrees, Kanban tasks (`task_*.md`), and Two-Tier memory state.
2. **Lifecycle FSM Engine (`check_tasks.py`)**: Deterministic derivation of dev-lifecycle stage and next human action using dual-check verification across `GATE_LEDGER.md` and `assistant_state.md`.
3. **ANSI Reporter (`check_tasks.py`)**: Terminal table renderer with repository signature colors, progress bars, and zero terminal mangling.
4. **HTTP Daemon Server (`tasks_server.py`)**: Threaded daemon with port collision bumping, PID tracking, and REST endpoints (`/api/tasks`, `/api/review`, `/api/launch/cli`, `/api/launch/ide`, `/api/shutdown`).
5. **Interactive Web Dashboard (`tasks_dashboard.html`)**: Standalone Dark Mode companion featuring drag-and-drop card reordering, Antigravity auto-indexing notes, and pop-up modals for Kanban, Contexts, and Cross-Model Review.

## Repository Color Signatures

Matches `workbench.colorCustomizations` in `.vscode/settings.json`:
- 🟠 **`ai-agent-tools`**: `#b45309` (Warm Amber)
- 🔴 **`lyrics-sync`**: `#7f1d1d` (Crimson Red)
- 🟢 **`D3Nexus`**: `#065f46` (Emerald Green)
- 🔵 **`nexus`**: `#0d47a1` (Royal Blue)

