# Fix Plan — Cross-Model Review Round 1

- **Candidate SHA**: `b7dfa1b000be1807e719bfcd51f73de5503f6976`
- **Reviewer**: Codex (`gpt-6.1-sol`, thinking `high`)
- **Role 2.2 Evaluation**: `APPROVED` (12/12 Valid; 0 `shared-contracts/` conflicts; 0 `CRITICAL_CONFLICT`)

## Planned Fixes

1. **Finding #1 (`verify_polyglot_registry.py:288`)**: Reap exited group leader first and probe process-group liveness via `os.killpg(pgid, 0)` in `_terminate_process_group` so `SIGTERM`-ignoring grandchildren receive `SIGKILL` even after leader exit.
2. **Finding #2 (`verify_polyglot_registry.py:699`)**: Keep subprocesses registered in `_QualityRunCoordinator._active_procs` when unwinding under `_SignalAbort` / exceptions (popping inside `abort_and_reap_children` after termination) so direct `execute_provider()` signal cleanup always terminates and reaps active process groups.
3. **Finding #3 (`verify_polyglot_registry.py:745`, `validate_web_quality.py`)**: Thread run-scoped log directories and coordinator process tracking hooks through `_execute_web_provider` -> `validate_web_quality.run_capabilities` so web capabilities log directly under `build/quality/<provider>/runs/<run_id>/`, return run-scoped evidence locations, and abort/reap cleanly on `SIGTERM`.
4. **Finding #4 (`tasks_server.py:883`)**: Route PIC updates of `<epic>.heartbeat.json` inside `assign_epic_pic` through `_state_envelope._state_lock` + highest-generation snapshot mirror writes (`generation + 1`) rather than unlocked manual RMW.
5. **Finding #5 (`tasks_server.py:765`)**: Enforce strict resolved containment against each checkout root (`target.resolve().is_relative_to(checkout_resolved)`) across `_discover_pic_worktrees` and `assign_epic_pic` reads/writes so symlinks pointing into other repositories raise `ValueError` (HTTP `400`) without writing external files.
6. **Finding #6 (`check_tasks.py:1280`)**: Scope `assistant_state.md` reading in `_read_combined_state_text` to sections matching `active_epic` (`# Active Epic: <variant>`) while preserving legacy single-epic unheaded files so sibling epics' `"Review Converged"` cannot leak across epics.
7. **Finding #7 (`scripts/resume_context.py:872`)**: Wrap multi-root `write_epic_state` and `complete_feature_and_rotate` archival/mirror writes inside a single canonical lock (`_state_envelope._state_lock`) with atomic sibling-temp replacement.
8. **Finding #8 (`manage_worker_pool.py:504`)**: Fail closed on non-zero `git status --porcelain` return codes (`dirty = st.returncode != 0 or bool(st.stdout.strip())`).
9. **Finding #9 (`manage_worker_pool.py:529`)**: Run `git worktree prune` before `git branch -D` when pruning missing-worktree orphan branches so merged orphan branches delete cleanly on the first cleanup pass.
10. **Finding #10 (`handoff-template.md:48`, `resume_context.py:1986`)**: Replace nonexistent `skills/dev-implementation/resources/scripts/estimate_heartbeat.py` with `scripts/estimate_heartbeat.py` (`handoff.md` never referenced `estimate_heartbeat.py`, so `package_epic.py --revise` is not required).
11. **Finding #11 (`check_task_contract.py:223`)**: Unify Allowed and Evidence `(new)` ownership maps in `check_duplicate_new_claims` and replace `.lstrip("./")` with safe prefix stripping (`re` / `./` prefix removal) so `.agents/x` and `agents/x` never collide.
12. **Finding #12 (`tests/test_rsdh_orchestration.py:1339`)**: Realign integration wrapper mappings in `TestRSDHOrchestration_Integration` (plus scenario labels/tests where swapped) so `RSDH-HP-05`, `RSDH-EC-08`, `RSDH-ST-03`, `RSDH-ST-07`, and `RSDH-FR-03` directly exercise their canonical Gherkin scenarios.

## Verification Scope (Scoped Intermediate Round)
- Run `ruff check`, `mypy`, and targeted pytest/unittest suites covering all 12 fixes (`tests/test_rsdh_heartbeat_quality.py`, `tests/test_rsdh_harvester_and_pic.py`, `tests/test_rsdh_state_envelope.py`, `tests/test_rsdh_orchestration.py`, `tests/test_web_quality_provider.py`, `tests/test_web_quality_integration.py`, `tests/test_polyglot_gate4.py`, `tests/test_check_tasks_fsm.py`, `tests/test_check_tasks_server.py`, `skills/dev-implementation/resources/scripts/test_check_task_contract.py`, `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`, `scripts/test_resume_context.py`), then advance directly to Round 2 external review.

