# Round 2 Fix Plan — runtime_sync_and_dashboard_hardening

- **Candidate SHA**: `b6e0ecf`
- **Role 2.2 Evaluation**: `APPROVED` (all 3 findings verified `Valid` against source, HLD `runtime_sync_and_dashboard_hardening.en.md`, and `bdd_scenarios.en.md`; zero `CRITICAL_CONFLICT` and zero `SHARED_CONTRACT_CONFLICT`).

## Planned Changes

1. **Finding #1 (`check_task_contract.py` + `.agents/quality/python-quality.json:3` — Critical)**:
   - Keep `scripts/_state_envelope.py` and `scripts/estimate_heartbeat.py` in `.agents/quality/python-quality.json` as mandated by HLD (§Feature Maintenance Map, §Verification Environment) and `task_07`.
   - Update `check_python_tier_b` / `check_task` in `skills/dev-implementation/resources/scripts/check_task_contract.py` so completed tasks (`status: done`, as well as `review`/`in-progress` when `--allow-existing-done-new` is active in Stage 3 `--revise`) validate against the registered tool/runner prefix (`_cap_tool_prefix(cap)`), preventing standing-target additions in `.agents/quality/python-quality.json` from breaking `check_epic_readiness.py` and `package_epic.py --revise` on this epic or already-merged Python epics, while keeping `todo` tasks and runner mismatches strict.

2. **Finding #2 (`skills/dev-implementation/resources/scripts/sync_task_status.py:375` — Important)**:
   - Canonicalize the envelope and Two-Tier Memory key inside `_sync_runtime_envelope_and_memory` via `_canonical_envelope_slug(epic_slug)` (normalizing `_` -> `-` per HLD §Module Contracts `L146-L209`) so `sync_task_status.py`, `resume_context.write_epic_state`, and `manage_worker_pool.py` write a single `<hyphen-slug>.heartbeat.json`, single `<hyphen-slug>.md`, and single `assistant_state.md` section with strictly monotonic `generation`.
   - Normalize `-`/`_` comparison in `_collect_epic_task_summary` and `board_tally` (`_same_epic_slug`), migrate prior locked decisions from legacy `<epic_slug>.md` when needed, and clear pending decisions under both forms.

3. **Finding #3 (`skills/dev-implementation/resources/scripts/sync_task_status.py:327` — Important)**:
   - Order `summary_roots` in `_sync_runtime_envelope_and_memory` via `_order_summary_roots` with the active checkout (`_current_checkout_root()`) and non-primary epic worktrees ahead of `primary_root`, preventing stale `.devtool/features/` `todo` copies on `main` from overriding authoritative worktree `done` / `in-progress` task statuses.

4. **Regression Tests & Scoped Verification**:
   - Add regression tests in `skills/dev-implementation/resources/scripts/test_check_task_contract.py`, `skills/dev-implementation/resources/scripts/test_sync_task_status.py`, and `tests/test_rsdh_state_envelope.py`.
   - Reconcile live gitignored `.devtool/state/` and `.devtool/assistant_state.md` in primary/worktree checkouts to remove the stale pre-fix underscore duplicate and confirm `[done: 7]`.
   - Run scoped `ruff check`, `mypy`, `unittest`, targeted `pytest`, `check_epic_readiness.py --post-design`, and `package_epic.py --revise` (reserving full Gate 4 for final convergence).

