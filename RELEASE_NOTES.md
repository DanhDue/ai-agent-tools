# Release Notes: d3nexus v1.25.0

**Release Date:** November 07, 2026  
**Version:** `1.25.0`  
**Git Tag:** `v1.25.0`, `d3nexus--v1.25.0`

---

## Executive Summary

`v1.25.0` delivers three major platform epics (**Contract & Authoring Ergonomics**, **Execution & Verification Infrastructure**, and **Multi-Epic Orchestration & Governance**), introduces **Account Block Security Auditing (`d3nexus:audit-account-block`)** and **Multi-Profile OS Boundary Safety (Rule 9)**, automates **Gate 2 Handoff Packaging & Post-Review Quality Gates**, adds **Scope-Aware `NOT_APPLICABLE` (`scope_unmodified`) UI Review Short-Circuiting**, hardens **Worktree-Aware IDE Theme & Title Synchronization**, and upgrades **`scripts/verify.sh`** with Longest-Job-First parallel test execution and 2-tier content-hash caching (~5x faster full runs, ~1s cached runs).

---

## Key Highlights

### 1. Automated Gate 2 Packaging & Post-Review Quality Gates
- **Unified Gate 2 Handoff**: Approving Gate 2 in `/dev-designer` now automatically runs `package_epic.py` and `/save-context` (`--gate 2`, `--state`, `--emit-prompt`) and presents a single choice: `/principal-review`, `/dev-implementation`, or `Done`.
- **Auto-Run Mechanical Gates After Review Triage**: While preserving the mandatory human Triage decision checkpoint, committing review fixes in `principal-review` or `cross-model-review` now automatically runs the local mechanical quality gate (`Phase 4 / Gate 4` in Stage 3; `package_epic.py --revise` + `/save-context` in Stage 2) before returning to Review Choice.

### 2. Scope-Aware Quality Checks & Upgraded Impact Analysis
- **Zero-UI-Diff Short-Circuit (`scope_unmodified`)**: `audit_ui_state_and_styles.py`, `validate_web_quality.py`, and all platform quality providers (`flutter`, `android`, `ios`, `web`) now inspect `git diff --name-only <base_ref>...HEAD` and emit `NOT_APPLICABLE` (`code: "scope_unmodified"`) when zero UI files are modified.
- **3-State Coverage & Test Discovery**: `check_code_impact.py` now discovers `tests/**/test_<stem>.py`, parses Python `coverage.json`, and distinguishes `MEASURED`, `TESTS_PRESENT_NO_REPORT`, and `NO_TESTS_FOUND`.
- **Gate 4 Active Execution Lease**: `verify_polyglot_registry.py` writes `.gate4_active.lease` while running and `gate4_receipt.json` on completion; `integrate_branch.py` blocks landing while a Gate 4 run is active.

### 3. Worktree-Aware IDE Theme & Context CLI (`bin/d3nexus`)
- **Primary Repo Signature Preservation in Worktrees**: `scripts/resume_context.py` resolves the primary repository root (`resolve_primary_repo_root`) inside `.worktrees/<epic_dir>` so repository icons (`🔴/🟢/🔵/🟠`) and persistent title/status bar colors (`#7f1d1d`, `#065f46`, `#0d47a1`, `#b45309`) are always preserved and synced across both primary repo and worktree `.vscode/settings.json`.
- **Automatic Worktree Seeding**: `bootstrap_worktree.sh` automatically copies `.vscode/settings.json` and `.env*` from `REPO_ROOT`, runs `resume_context.py --sync-title`, and supports `uv sync`.
- **Portable `d3nexus` CLI**: Added `bin/d3nexus` supporting `resume-context`, `check-task-contract`, `check-epic-readiness`, `sync-task-status`, `run-task-checks`, `package-epic`, `audit-epic`, and `run-external-review`.

### 4. Multi-Epic Orchestration, Execution Replay & Contract Ergonomics
- **Multi-Epic Governance**: Added inter-epic `Depends On` dependency resolution, conflict-aware concurrent backlog promotion (`promote_epic_tasks.py`), `package_epic.py --revise` with HLD `Spec Errata`, and a structured Gate Approval Ledger in `PROJECT_LEDGER.md`.
- **Task Replay & Failure Baselines**: Added `replay_task_text.py` for static anchor verification and `MEASURE` phase execution, plus `record_failure_baseline.py` and `compare_failure_sets.py`.
- **Single-Source Task Rendering**: Added `render_epic_tasks.py` and `Evidence Files` contract enforcement.

### 5. Account Block Security Audit & Rule 9 OS Boundary Safety
- **`d3nexus:audit-account-block`**: Audits Antigravity profiles for cloned machine IDs, cross-account trajectory leaks, and 403 ToS risks.
- **Rule 9 Multi-Profile Safety**: Codifies `.zshrc` backup/syntax verification, host macOS default keychain protection, subshell-scoped profile environments, shared toolchain symlinks, and parent IPC handle stripping.

### 6. Parallel & Two-Tier Cached `scripts/verify.sh`
- **Longest-Job-First Parallel Test Runner**: Runs all 39 `unittest` and `pytest` suites concurrently across CPU cores (`~32s` vs `~151s` sequential) and caches `FULL_HASH:CODE_HASH` in `$GIT_DIR_PATH/.verify_tests_tree_cache` (`~1s` on cache hit, `--full` to force).

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh --full`: 🟢 **PASS — safe to publish** (Sections 1–16, 39/39 test suites green)
- `verify_polyglot_registry.py .agents/quality/check_quality.json --profile epic`: 🟢 **PASS** (`architecture`, `format`, `lint`, `test` 62/62 pytest, `type_check` mypy)
