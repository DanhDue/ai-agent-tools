# Release Notes: d3nexus v1.31.0

**Release Date:** November 15, 2026  
**Version:** `1.31.0`  
**Git Tag:** `v1.31.0`, `d3nexus--v1.31.0`

---

## Executive Summary

`v1.31.0` introduces the **Epic History Modal** with append-only event stream archival and fast review-tab loading in `/check-tasks`, unified **Action Alerts & English UI**, **Dynamic Claude Quota Buckets** & macOS multi-schedule hardening in `/check-quota`, and the **Argon Orchestrator / Hydrogen Subagent Role Matrix** across `dev-lifecycle`.

---

## Key Highlights

### 1. Epic History Modal & Review Tab Performance (`skills/check-tasks/`)
- **4-Tab Epic History Modal**: Clicking any epic in the Project Epics Roadmap opens a dedicated modal with `Timeline`, `Tasks`, `Principal Review`, and `Cross-Model Review` tabs, backed by `/api/epic/history` and append-only event stream archival.
- **Fast Round Switching & Client Cache**: `switchEpicHistoryReviewRound` now queries `/api/review` and caches visited rounds in `epicHistoryState.reviewCache`, eliminating redundant `harvest_epic_history` runs.
- **Lazy-Loaded Verbatim Raw Output**: Modal fetches pass `include_raw=0` so heavy `raw_output` logs are only fetched when expanding `<details>`.
- **Backend Parse & Scan Caching**: `parse_review_results` uses a thread-safe `(st_mtime_ns, st_size)` cache (`_REVIEW_PARSE_CACHE`), and `harvest_epic_history` shares `_scan_cache_scope()` across nested worktree and directory scans.

### 2. Action Alerts & English Dashboard UI (`skills/check-tasks/`)
- Unifies 4-location confirmation alerts and English dashboard UI with active epic priority and multi-epic blocker aggregation.

### 3. Dynamic Claude Quota Buckets & Schedule Hardening (`skills/check-quota/`)
- Adds dynamic Claude quota buckets in CLI and Web UI, 3-bucket activation, FREE gating, macOS multi-schedule support, Argon expired reset & live 5H session detection, and fallback CLI OAuth token file checks.

### 4. Argon Orchestrator & Hydrogen Subagent Role Matrix (`skills/dev-lifecycle/`, `docs/`)
- Standardizes Role 2.2 as Argon Orchestrator and Role 2.3 subagent as Hydrogen (`xhigh`), documented in `docs/lifecycles.en.md` and `docs/lifecycles.vi.md`.

### 5. Test Isolation (`skills/refresh-session/`)
- Isolates `refresh-session` Darwin schedule tests from host LaunchAgents.

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh`
- `uv run pytest tests/test_check_tasks_*.py tests/test_cehm_*.py`
- `uv run ruff check` on modified Python modules
