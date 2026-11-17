# Mandatory Window Title Synchronization & Persistent Top/Bottom Bar Customization

> [!IMPORTANT]
> To eliminate cross-project window confusion when developers operate multiple IDE instances or profile accounts simultaneously, AI Agents MUST keep the IDE window title and persistent bar colors synchronized with the active Epic and Task.

## 1. When to Update Window Title
The AI Agent MUST automatically update `window.title` in `.vscode/settings.json` whenever:
1. Entering or resuming an Epic (Stage 1 Inception, Stage 2 Design, Stage 3 Implementation, Stage 4 Quality Check).
2. Starting or completing a Kanban task (`task_*.md`).
3. Transitioning between lifecycle stages or approval checkpoints.
4. Archiving or finishing an epic feature.

## 2. Title Format Standard
The `window.title` property in `.vscode/settings.json` MUST strictly follow:
```text
"<ICON> [<REPO_NAME>] [@<account_id>] <Epic Name> - <Stage / Task>"
```

### Format Specifications:
- **`<ICON>` & `<REPO_NAME>`**:
  - `lyrics-sync`: `🔴 [LYRICS-SYNC]`
  - `D3Nexus`: `🟢 [D3NEXUS]`
  - `nexus`: `🔵 [NEXUS]`
  - `ai-agent-tools`: `🟠 [AGENT-TOOLS]`
- **`[@<account_id>]`**:
  - Extracted from the active profile / home environment (e.g. `basename $HOME` under `antigravity_homes/` -> `[@danhdue]`, `[@tess]`).
- **`<Epic Name>`**:
  - The English epic name. No `.vi.md` file is read; English is the single source of truth.
  - Written by hand: the name Role 1.0 gave in chat, else the epic name already in the current `window.title`, else the epic slug.
  - Written by `python3 scripts/resume_context.py --sync-title`: the first H1 of the English epic document (`.devtool/epic/<epic_slug>/<epic_slug>.md`, else `<epic_slug>.en.md`, then `*-design.md` / `*-design.en.md`), with the `# Epic:` prefix stripped. When none has an H1, the script leaves the epic name out and writes `<ICON> [<REPO_NAME>] [@<account_id>] <Stage / Task>`.
- **`<Stage / Task>`**:
  - `Stage 1: Brainstorming`
  - `Stage 2: Design Approved`
  - `Task X/Y: <Short Task Title>`
  - `Stage 4: Gate 4 Quality Check`
  - `Stage 4.1: Review Choice`
  - `Completed & Archived`

## 3. Persistent Top/Bottom Bar Customization
In `.vscode/settings.json`, both `titleBar` and `statusBar` MUST configure matching inactive background colors to eliminate IDE dimming when windows lose focus:
- `titleBar.inactiveBackground`: Must equal `titleBar.activeBackground`
- `statusBar.inactiveBackground`: Must equal `statusBar.background`
- `activityBar.background`: Keep uncolored in default dark theme to avoid peripheral clutter.

## 4. Preservation Constraint
When updating `.vscode/settings.json`:
- Surgically modify ONLY the `window.title` key and ensure inactive bar parity.
- Preserve all existing developer configurations, settings, and terminal allowlists intact.

