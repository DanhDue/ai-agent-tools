# Release Notes: d3nexus v1.35.1

**Release Date:** November 26, 2026  
**Version:** `1.35.1`  
**Git Tag:** `v1.35.1`, `d3nexus--v1.35.1`

---

## Executive Summary

`v1.35.1` adds safe, clean-only worktree and worker-slot cleanup when moving epics to **Pending** or **Cancelled** in the Tasks UI so developers can reclaim disk space (`node_modules`, `.venv`, `build/`, `target/`, `.dart_tool/`) while keeping epic documentation, git branches, and any dirty worktrees intact.

---

## Key Highlights

### Safe Clean-Only Worktree Cleanup (`skills/check-tasks/`)
- **Confirmation Modal Option**: The Pending / Cancel confirmation dialog now includes a default-checked checkbox: **Remove worktree & worker slots to free disk space** (*keeps epic docs and git branch*).
- **Zero-Data-Loss Guard**: `_cleanup_epic_worktrees_if_clean()` removes ephemeral worker slots (`-slot-*`) and the main epic worktree strictly when `git status --porcelain -uall` is clean, then runs `git worktree prune`. Dirty worktrees with uncommitted or untracked files are never force-removed and are surfaced via a warning toast.
- **API Contract**: `POST /api/epic/execution-state` accepts `remove_worktree: boolean` and returns `worktree_cleanup` (`removed`, `skipped_dirty`, `errors`).

---

## Verifications & Quality Gates Passed

- `python3 -m pytest tests/test_tasks_ui_epic_execution_tabs.py -v` (4/4 passed, including clean worktree/slot removal, dirty worktree preservation, and Headless Chrome CDP E2E)
- `bash scripts/verify.sh --quiet` (all structural integrity checks & 90 test suites across 14 parallel workers: PASS)
