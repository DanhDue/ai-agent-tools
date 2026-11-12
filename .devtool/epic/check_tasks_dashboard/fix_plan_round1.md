# Fix Plan: check_tasks_dashboard, Round 1 (Claude Opus 5.5)

## Findings Triage Summary

- **Round**: 1 / 3
- **Reviewer**: Claude (Opus 5.5)
- **Verdict**: CHANGES REQUIRED (1 Critical, 9 Important, 10 Minor)
- **Auto-Triage Gate**: AUTO_FIX_ELIGIBLE
- **Shared Contracts Impact**: None (purely local to check-tasks CLI, server, dashboard, and tests)

## Fix Specifications

### Fix 1 [Critical #1]: Dynamic Web Dashboard Rendering
- **Files**: `skills/check-tasks/resources/dashboard/tasks_dashboard.html`
- **Action**:
  - Update `fetchTasks()` to read `data.repos` and `data.summary` from `/api/tasks`.
  - Dynamically render `.repo-card` elements into `#repos-container` when `data.repos` is returned, preserving color signatures, notes input with auto-indexing, worktree tags, and action buttons.
  - Implement dynamic `openKanbanModal(repoName)` rendering 5 columns from `repo.tasks.all_tasks`.
  - Implement dynamic `openContextModal(repoName)` rendering Two-Tier memory from `repo.memory`.
  - Ensure drag-and-drop reordering and `pinRepoToTop()` work seamlessly on dynamically rendered cards.

### Fix 2 [Important #2]: Surface `LifecycleDecision.prompt` in Metadata, CLI, and UI
- **Files**: `skills/check-tasks/resources/scripts/check_tasks.py`, `skills/check-tasks/resources/dashboard/tasks_dashboard.html`
- **Action**:
  - Add `prompt: str | None = None` to `RepoMetadata`.
  - Set `repo.prompt = decision.prompt` in `scan_repo()`.
  - Surface prompt in `render_single_repo()` and `render_terminal_table()`.
  - Display dynamic `repo.prompt` in the "⚡ Next Immediate Step" box in web cards.

### Fix 3 [Important #3]: Multi-Round & Schema Robustness in `parse_review_results`
- **Files**: `skills/check-tasks/resources/scripts/tasks_server.py`
- **Action**:
  - Support parsing standard `- **SHA**:`, `- **CLI**:`, `- **Model**:`, `- **Thinking**:`, `- **Verdict**:` headers.
  - Support `round` query parameter in `/api/review?repo=<repo>&epic=<epic>&round=<N>`.
  - Match raw output fence following `Raw output:` header.

### Fix 4 [Important #4 & #5]: FSM Stage 3 Phase 1 & Gate Ledger Slug Normalization
- **Files**: `skills/check-tasks/resources/scripts/check_tasks.py`
- **Action**:
  - In `derive_lifecycle_state()`: allow Stage 3 Phase 1 when worktree exists on `refs/heads/epic/<slug>` even if `handoff.md` is present.
  - In `parse_gate_ledger_entries()`: normalize epic slugs with `slug.replace("_", "-")` and bidirectional check.

### Fix 5 [Important #7]: Shell Injection Prevention via `shlex.quote`
- **Files**: `skills/check-tasks/resources/scripts/tasks_server.py`
- **Action**:
  - Use `shlex.quote(profile)` and `shlex.quote(worktree)` in `build_ide_launch_command()` and `build_cli_launch_command()`.

### Fix 6 [Important #8]: Terminal Table Width & ANSI Alignment
- **Files**: `skills/check-tasks/resources/scripts/check_tasks.py`
- **Action**:
  - Use `strip_ansi()` to compute visible string widths for table columns, preventing ragged borders.

### Fix 7 [Important #9, #14, #15]: CLI Delegation & Flag Alignment
- **Files**: `skills/check-tasks/resources/scripts/check_tasks.py`, `scripts/check_tasks.py`, `skills/check-tasks/SKILL.md`
- **Action**:
  - Support `--web` alias and `--ui -f` / `--foreground` options.
  - Fix `--status` to output full server status (running state, PID, URL).
  - Forward `--workspace-root` in daemon spawn.

### Fix 8 [Important #10, Minor #11, #12, #13, #18, #20]: Architecture & Engine Hardening
- **Files**: `skills/check-tasks/resources/scripts/check_tasks.py`, `skills/check-tasks/resources/scripts/tasks_server.py`
- **Action**:
  - `#10`: In `resolve_active_epic()`, prioritize `epic/<slug>` branch, filter out `general` placeholder, and sort epics deterministically.
  - `#11`: Derive worktrees dynamically via `git worktree list --porcelain`.
  - `#12`: Use `os.O_CREAT | os.O_EXCL | os.O_WRONLY` for exclusive PID file writing.
  - `#18`: Add `if __name__ == "__main__": sys.exit(main())` in `skills/check-tasks/resources/scripts/check_tasks.py`.
  - `#20`: Remove `digital_wallet` signature.
