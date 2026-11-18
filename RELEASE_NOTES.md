# Release Notes: d3nexus v1.33.0

**Release Date:** November 18, 2026  
**Version:** `1.33.0`  
**Git Tag:** `v1.33.0`, `d3nexus--v1.33.0`

---

## Executive Summary

`v1.33.0` introduces **Task Review Cap, Blocker-Only Triage & Two-Tier Risk Short-Circuit (`review_cap_and_risk_triage`)** across `dev-lifecycle` and `dev-implementation`, adds **Antigravity (`agy`) Orchestrator Aliases & Effortless Models (`agy_orchestrator_and_effortless_models`)** in `dev-config`, brings **Dynamic Model Discovery, Shared Argon Guards & Multi-Strategy Review Actions** to `/check-quota`, `/refresh-session`, and `/check-tasks`, normalizes **Dynamic 4-Provider Account Tiers** in `/check-quota`, and hardens **Kanban Scrolling, Card Sizing & Per-Epic Stage Telemetry** in `/check-tasks`.

---

## Key Highlights

### 1. Task Review Cap, Blocker-Only Triage & Two-Tier Risk Short-Circuit (`review_cap_and_risk_triage`)
- **Configurable Review & Fix Caps (`scripts/persona_config.py`, `scripts/personas.default.json`, `scripts/dev_config.py`)**: Resolves `task_review_limits` (`max_task_review_passes = 2`, `max_fix_passes = 1`) with strict `type(v) is int` validation and displays resolved limits in `dev_config.py status`.
- **Non-Destructive Pass 1 Snapshots & Delta-Only Pass 2 (`scripts/resume_context.py`, `skills/dev-implementation/resources/scripts/manage_worker_pool.py`)**: Captures `pass1_tree_sha` using a temporary `GIT_INDEX_FILE` (`capture_slot_tree_sha`) without mutating working trees or shared git indexes, enforces the `APPROVED|CHANGES_REQUESTED` (`blockers` / `observations`) contract in `--review-pass 1`, and generates Pass 2 Delta-Only prompts via `--review-pass 2 --pass1-tree-sha ... --blockers-file ...`.
- **Blocker-Only Coercion Guard & Two-Tier Risk Triage (`manage_worker_pool.py`, `lifecycle_runner.py`)**: Coerces inconsistent `APPROVED` payloads with non-empty `blockers` via `normalize_task_review_payload`, applies Tier 1 deterministic heuristics (`triage-fix`) and bounded Role 2.2 Tier 2 short-circuit checks (`tier2-short-circuit`), enforces `finalize-slot` mechanical gates, and writes append-only records (`pass2_residual_logged_on_cap`, `tier1_triage_short_circuit`, `tier2_triage_short_circuit`) to `review_audit_notes.jsonl` with full `LifecycleRunner` parity.

### 2. Antigravity Orchestrator Aliases & Effortless Models (`agy_orchestrator_and_effortless_models`)
- **Effortless Dispatch & Defaults (`scripts/dev_config.py`, `scripts/persona_config.py`, `scripts/personas.default.json`, `skills/dev-config/SKILL.md`)**: Supports Antigravity `orchestrator` model aliases and effortless models across `dev-config set` and `dev-config models add`, backed by `tests/test_agy_effortless_models.py`.

### 3. Check-Quota Dynamic Models, Shared Argon Guard & Review Proposed Actions (`check_quota_dynamic_models_and_review_action`)
- **Dynamic Quota Discovery & `argonMode` (`scripts/agy_quota.py`, `skills/refresh-session/resources/scripts/refresh_session.py`, `skills/check-quota/resources/dashboard/quota_dashboard.html`)**: Combines `FetchAvailableModels` discovery with static fallbacks and `argonMode` (`PRO_ARGON`, `ULTRA_ARGON`, `PRO_HYDROGEN`, `ULTRA_CARBON`), renders dynamic rosters and shared pools in `quota_dashboard.html`, and suppresses redundant shared-pool Argon pings in `/refresh-session`.
- **Multi-Strategy Review Action Extraction (`skills/dev-implementation/resources/scripts/run_external_review.py`, `skills/check-tasks/resources/scripts/tasks_server.py`, `tasks_dashboard.html`)**: Aligns `Proposed:` prompts across local and external review templates with prefill triage and multi-strategy action extraction in `/check-tasks`.

### 4. Dynamic 4-Provider Account Tiers (`check_quota_dynamic_provider_account_tiers`)
- **Unified Provider Tiers (`scripts/agy_quota.py`, `scripts/types/quota_dashboard.types.ts`, `skills/check-quota/resources/dashboard/quota_dashboard.html`)**: Normalizes `planLabel`, `vendorLabel`, priority sorting, and `accountMeta` across Antigravity (`GOOGLE`), Claude (`ANTHROPIC`), Codex (`OPENAI`), and Kiro (`AWS`), adding dynamic provider badges, an account info modal, and the Ultra Carbon-Argon row.

### 5. `/check-tasks` Kanban Scroll, Width & Stage Telemetry Fixes (`check_tasks_kanban_and_stage_title_fixes`)
- **Kanban UX & Telemetry (`skills/check-tasks/resources/dashboard/tasks_dashboard.html`, `skills/check-tasks/resources/scripts/check_tasks.py`)**: Pins Kanban Overview, unifies 5-column horizontal `Shift+Wheel` scrolling at `210px` column width, fixes 16-card height collapse and badge/chip right-edge clipping, scopes pipeline telemetry per epic, and removes orphan stage prefixes, verified via Chrome CDP E2E tests.

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh` (all 22 verification sections & 89 Python test suites)
- `uv run pytest tests/test_trc_*.py tests/test_agy_effortless_models.py tests/test_cqra_*.py tests/test_check_tasks_kanban_and_telemetry_fixes.py tests/test_check_quota_dynamic_provider_tiers.py`
