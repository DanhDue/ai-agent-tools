# Release Notes: d3nexus v1.23.0

**Release Date:** November 04, 2026  
**Version:** `1.23.0`  
**Git Tag:** `v1.23.0`, `d3nexus--v1.23.0`

---

## Executive Summary

`v1.23.0` introduces **Visual Multi-Epic Workspace Synchronization & Color Customization**, dynamic **SQLite Account & Email ID Extraction**, and **Multi-Profile GUI Isolation** across the entire developer ecosystem (`ai-agent-tools`, `D3Nexus`, `lyrics-sync`, `nexus`) and all 19 Antigravity profiles. It completely eliminates cross-account title contamination when opening repositories directly from the Antigravity IDE GUI (`File -> Open Folder`), enforces persistent active/inactive theme bar parity, establishes Section 8.4 in `CRITICAL_RULES.md`, and hardens Python 3.9 compatibility across all lifecycle CLI tools and test suites.

---

## Key Highlights

### 1. Visual Multi-Epic Workspace Synchronization Engine
- **Dynamic Window Title**: Synchronizes window titles to `"<ICON> [<REPO_NAME>] [@<account_id>] <Vietnamese Epic Name> - <Stage / Task>"`.
- **Repository Signature Colors**:
  - 🔴 `[LYRICS-SYNC]`: `#7f1d1d` (Crimson Red)
  - 🟢 `[D3NEXUS]`: `#065f46` (Emerald Green)
  - 🔵 `[NEXUS]`: `#0d47a1` (Royal Blue)
  - 🟠 `[AGENT-TOOLS]`: `#b45309` (Warm Amber)
- **Persistent Inactive Bar Parity**: Configures `titleBar.inactiveBackground = titleBar.activeBackground` and `statusBar.inactiveBackground = statusBar.background` to eliminate IDE dimming when windows lose focus.
- **Clean Activity Bar**: Preserves default dark background on the left activity toolbar to avoid peripheral visual clutter.
- **Vietnamese Epic Titles**: Extracts epic names directly from H1 headers of `.devtool/epic/<slug>/*.vi.md`.

### 2. Dynamic SQLite Account & Email ID Engine
- **Direct SQLite Querying**: `extract_email_id_from_profile` in `scripts/resume_context.py` inspects `state.vscdb` (`google.google-antigravity` onboarding storage) in read-only URI mode (`file:...mode=ro`).
- **4-Tier Account Resolution Hierarchy**:
  1. CLI `--profile` or `AGY_PROFILE` / `ANTIGRAVITY_PROFILE` override.
  2. Active process inspection (`ps -eo command`) matching `agy` or `Antigravity IDE` attached to target repo.
  3. `workspaceStorage` MRU timestamp inspection across all profiles in `antigravity_homes`.
  4. Active shell `HOME` environment fallback.
- **All 19 Profiles Supported**: Full coverage for `brother`, `buivantrong8901`, `d3molt`, `daddy`, `danhdue`, `duedd`, `duvthinh403`, `hau`, `hoangcongtam690`, `khe`, `mau`, `molt`, `mommy`, `ngocanh000690`, `nguyenhieu000690`, `peter`, `phungthuy8901`, `tess`, and `trananh`.

### 3. Multi-Profile GUI Isolation & Governance
- **Strict Separation of Concerns**: Workspace `.vscode/settings.json` houses project-wide invariants (`workbench.colorCustomizations`), while personal identity is isolated in `antigravity_homes/<account>/data/User/settings.json`.
- **Zero GUI Contamination**: Opening any project directly from Antigravity IDE GUI (`File -> Open Folder`) reliably displays the current profile's identity without leaking previously active accounts.
- **Plugin Rule Standard**: Rule codified into `rules/CRITICAL_RULES.md` (Section 8.4) and synced to installed plugins for all AI assistants (Claude, Codex, Antigravity).

### 4. Python 3.9 Compatibility Hardening
- **PEP 604 Type Unions**: Added `from __future__ import annotations` across 29 test and CLI tool files, guaranteeing complete compatibility with macOS default `/usr/bin/python3` (Python 3.9.6).
- **Timezone Fallbacks**: Added fallback to `timezone.utc` for `datetime.UTC`.
- **Runtime Error & Symlink Loop Handling**: Handled `Path.resolve()` symlink loop exceptions in `sync_contracts.py`.
- **Transport & Pairwise Fixes**: Replaced `itertools.pairwise` with `zip(chats, chats[1:])` and resolved `socket.timeout` error handling in `local_review.py`.

---

## Verifications & Quality Gates Passed

- `scripts/verify.sh`: 🟢 **PASS — safe to publish** (16/16 sections green)
- `scripts/test_resume_context.py`: 🟢 **PASS** (21/21 unit tests green)
- `skills/dev-implementation/resources/scripts/test_local_review.py`: 🟢 **PASS** (40/40 unit tests green)
- `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py`: 🟢 **PASS** (9/9 unit tests green)
- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py`: 🟢 **PASS** (31/31 unit tests green)
