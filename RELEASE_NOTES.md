# Release Notes: d3nexus v1.29.0

**Release Date:** November 13, 2026  
**Version:** `1.29.0`  
**Git Tag:** `v1.29.0`, `d3nexus--v1.29.0`

---

## Executive Summary

`v1.29.0` ships the interactive **Cross-Repo Tasks & Context Dashboard (`check-tasks`)**, comprehensive **Token Throttling Optimizations**, and **Runtime Sync & Dashboard Hardening**—along with multi-format HLD status parsing/syncing, automatic stale daemon replacement in `tasks_server.py`, and the regression fix keeping the embedded `check-quota` dialog open when toggling batch scheduling.

---

## Key Highlights

### 1. Cross-Repo Tasks & Context Dashboard (`check-tasks`)
- **Multi-Repo Harvester & Deterministic FSM** (`skills/check-tasks/resources/scripts/check_tasks.py`): Scans active worktrees, Kanban task files, Two-Tier memory (`PROJECT_LEDGER.md` vs `assistant_state.md`), and cross-model review results across workspace repositories.
- **Daemon Server & Dark Mode UI** (`skills/check-tasks/resources/scripts/tasks_server.py`, `skills/check-tasks/resources/dashboard/tasks_dashboard.html`): Serves REST APIs (`/api/tasks`, `/api/review`, `/api/profiles`, `/api/launch/*`), Rule 9 sanitized CLI/IDE launchers, per-epic PIC assignment, 4-repo focused tabs, Roadmap table, and embedded Quota viewer.
- **Multi-Format HLD Status & Auto-Restart**: Accurately parses and syncs bold, Markdown table, blockquote, YAML, and heading status formats across `check_tasks.py` and `sync_task_status.py`, fixes false `"abandon"` matches on `"superseded"`, and auto-restarts stale `tasks_server.py` daemons via `code_fingerprint` sidecar validation (`--restart`).

### 2. Runtime Sync & Dashboard Hardening
- **Atomic Runtime State Envelope** (`scripts/_state_envelope.py`, `scripts/resume_context.py`): Enforces atomic envelope updates, canonical slug normalization, worktree summary prioritization, PIC transaction locking, and symlink boundary enforcement.
- **Hybrid Heartbeat & Pool Isolation** (`scripts/estimate_heartbeat.py`, `skills/dev-lifecycle/`, `skills/dev-implementation/`): Provides live wave/slot progress estimation, fail-closed worker pool cleanup/pruning, and quality runner process-group cleanup.

### 3. Token Throttling & Review Optimization
- **Focused Context & Diff-Only Review** (`rules/CRITICAL_RULES.md`, `skills/dev-implementation/resources/scripts/run_external_review.py`): Slims rules/skills, isolates transcripts, applies silent Gate 4 checks, gates selective task review, and uses English worker orchestration to improve reasoning and reduce token overhead.

### 4. Quota Dashboard Modal Fix
- **Batch Schedule Toggle Fix** (`skills/check-quota/resources/dashboard/quota_dashboard.html`, `tests/test_rsdh_quota_modal_stack.py`): Preserves `#batchScheduleBtn` DOM identity via in-place span updates and guards outside-click detection against detached nodes after synchronous re-renders so clicking **"Lên lịch nhiều tài khoản"** or **"Thoát chọn"** never closes `#modal-quota`.

---

## Verifications & Quality Gates Passed

- `@quality_check` (`verify_polyglot_registry.py .agents/quality/check_quality.json --profile epic --execute --compact`): **PASS** (`architecture`, `format`, `lint`, `test`, `type_check`)
- `bash scripts/verify.sh --full --quiet`: **PASS — safe to publish** (Checks 1–10 + 55 test suites)
