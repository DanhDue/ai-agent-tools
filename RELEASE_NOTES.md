# Release Notes: d3nexus v1.32.0

**Release Date:** November 18, 2026  
**Version:** `1.32.0`  
**Git Tag:** `v1.32.0`, `d3nexus--v1.32.0`

---

## Executive Summary

`v1.32.0` delivers **Four-Persona Governance & Model Configuration (`dev-config`)** across `dev-lifecycle`, replacing the legacy Tri-Role split with four explicit personas (`Human Architect 1.0`, `AI Architect & Reviewer 2.1`, `Orchestrator 2.2`, `Programmer 2.3`), a 4-layer model binding and preset engine (`dev_config.py`, `persona_config.py`), a priority-ordered **Antigravity (`agy`) Profile Pool & Exclusive Lease Dispatcher** (`agy_profile_pool.py`, `agy_dispatch.py`), proactive turn-budget and quota-gate checkpoints, **English-Only SSOT & Vietnamese Mirror Isolation** (Rule 11), and `/check-tasks` persona and quota-stop telemetry.

---

## Key Highlights

### 1. Four-Persona Governance & `/d3nexus:dev-config` (`skills/dev-config/`, `scripts/dev_config.py`, `scripts/persona_config.py`)
- **Four-Persona Split**:
  - **Role 1.0 (`Human Architect`)**: Owns vision, Gates 1, 2, 5, escalations, and Stage 4 Finish.
  - **Role 2.1 (`ai_architect_reviewer`)**: Owns Stage 1–2 specs/HLD/tasks/packaging and Stage 3 `task-reviewer` & `fix-planner`.
  - **Role 2.2 (`orchestrator`)**: Owns Gate 3, worker pool orchestration, subagent dispatch, and task status transitions without reading/editing `src/` or `tests/`.
  - **Role 2.3 (`programmer`)**: Executes `task-implementer`, `review-fixer`, and `gate4-verifier` strictly within `Allowed files`.
- **4-Layer Config & Presets**: Resolves persona bindings across `Kit defaults -> Global ($REAL_HOME/.d3nexus/personas.json) -> Project (.agents/config/personas.json) -> Invocation CLI flags` with 7 built-in presets (`default`, `gemini-saver`, `claude-hybrid`, `all-hydrogen`, `codex-kiro`, `all-claude`, `all-codex`), runtime catalogue management (`models add|remove`), `--provider agy|claude|codex` quick-setup, and flag-based `set PERSONA [--provider ...] --model M --effort E [--profile NAME|auto]`.

### 2. Global `agy` Profile Pool & Pooled Dispatch (`scripts/agy_profile_pool.py`, `scripts/agy_dispatch.py`)
- **Profile Pool & Exclusive Leases**: Manages priority-ordered Antigravity profiles (`profiles list|add|remove|release|clear|probe|discover`) backed by file-locked leases (`agy_profile_leases.json`) and heartbeat/PID expiration.
- **Safe Multi-Profile Execution & Rotation**: Dispatches non-host profiles via `zsh -ic 'ag_run "$0" cli "$@"'` after preflight checks for `_ag_link_ok`, `_ag_rel_link`, and `ag_run`. Automatically rotates to the next pool profile on pre-work quota exhaustion (`HEAD` and working tree unchanged) and stops cleanly on `quota_midrun` or `no_profile` without silent model fallbacks.

### 3. Checkpoints, Risk-Tiered Remediation & Quota Gates (`scripts/resume_context.py`, `lifecycle_runner.py`)
- **Proactive Checkpoints & Turn Budgets**: Records structured checkpoints (`gate2_tasks_locked`, `subagent_returned`, `wave_merged`, `model_unavailable`, `turn_budget`, `low_quota_stop`, `quota_low`), enforces `max_orchestrator_turns_before_checkpoint` (default `8`, halved in `low-quota` mode), and runs `dev_config.py quota-check` before Stage 3, each wave, and each review fix round.
- **Risk-Tiered Stage 3 Fixes**: Routes low-risk review findings to Role 2.3 `review-fixer` (`fast-track`) and high-risk findings (`Critical`, escalation markers, repeated check failures) through Role 2.1 `fix-planner` (`apply-plan` / `ESCALATE`).

### 4. English-Only SSOT, Mirror Isolation & Ownership Expansion (`rules/CRITICAL_RULES.md`, `skills/dev-implementation/`)
- **Rule 11 (`*.vi.md` Isolation)**: Prevents agents from loading, grepping, or bundling `*.vi.md` files unless explicitly requested by Role 1.0, backed by deterministic English document resolution (`_epic_docs.py`).
- **Ownership Glob/Directory Expansion**: Expands directory and glob claims during task contract and epic readiness checks to prevent overlapping file ownership across parallel wave tasks.

### 5. `/check-tasks` Persona & Quota Telemetry (`skills/check-tasks/`)
- Displays resolved persona bindings, checkpoint status, wave-0 labels, and quota-stop alerts in `/check-tasks`, and clears stale halt alerts on finished epics.

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh` (all 20 sections & 73 Python/pytest suites)
- `uv run pytest tests/test_fpg_*.py`
