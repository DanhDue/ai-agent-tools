# Cross-Model Review: runtime_sync_and_dashboard_hardening

## Round 1

- **Date**: 2026-11-13T05:37:08Z
- **SHA**: b7dfa1b000be1807e719bfcd51f73de5503f6976
- **Base**: main
- **CLI**: codex
- **Model**: gpt-6.1-sol
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Raw log**: `build/reviews/runtime_sync_and_dashboard_hardening_code_round1_b7dfa1b.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | skills/quality_check/resources/scripts/verify_polyglot_registry.py:288 | SIGKILL escalation stops when the group leader exits. A live probe reproduced a SIGTERM-ignoring grandchild surviving cleanup. | fixed in bcd043d |
| 2 | Important | skills/quality_check/resources/scripts/verify_polyglot_registry.py:699 | Capability unwinding unregisters the process before direct `execute_provider()` signal cleanup can reap it. The signal probe recorded zero termination calls. | fixed in bcd043d |
| 3 | Important | skills/quality_check/resources/scripts/verify_polyglot_registry.py:745 | Web execution bypasses coordinated child tracking and returns shared evidence paths. Cancellation can wait for web completion, while concurrent runs overwrite referenced logs despite subsequent run-scoped copies. | fixed in bcd043d |
| 4 | Important | skills/check-tasks/resources/scripts/tasks_server.py:883 | PIC reassignment updates heartbeat JSON outside the canonical transaction lock. An interleaving probe lost a concurrent slot update; independent mirror increments also permit generation divergence. | fixed in 1f0fc80 |
| 5 | Important | skills/check-tasks/resources/scripts/tasks_server.py:765 | Target containment is unchecked. An epic-directory symlink into another repository allows PIC reassignment to rewrite that repository’s metadata. | fixed in 1f0fc80 |
| 6 | Important | skills/check-tasks/resources/scripts/check_tasks.py:1280 | Convergence detection searches the entire shared assistant-state rollup. A sibling epic’s “Review Converged / Awaiting Finish” text incorrectly makes the active epic eligible for 100%; reproduced by probe. | fixed in 1f0fc80 |
| 7 | Important | scripts/resume_context.py:872 | Separate per-root memory locks do not serialize the complete mirror update. Interleaved producers leave primary markdown containing producer B’s state and worktree markdown containing producer A’s state. | fixed in 1f0fc80 |
| 8 | Important | skills/dev-implementation/resources/scripts/manage_worker_pool.py:504 | Failed `git status` execution is treated as clean, allowing forced worktree removal without establishing cleanliness. The failure probe returned successful deletion. | fixed in 7da0ad5 |
| 9 | Important | skills/dev-implementation/resources/scripts/manage_worker_pool.py:529 | Branch deletion precedes pruning missing-worktree registrations. Git still considers the orphan branch checked out, so the first cleanup fails and incorrectly reports a merged branch as preserved. | fixed in 7da0ad5 |
| 10 | Important | skills/dev-lifecycle/references/handoff-template.md:48 | The estimator command names nonexistent `skills/dev-implementation/resources/scripts/estimate_heartbeat.py`. The same broken command appears in scripts/resume_context.py:1986; the implementation resides at `scripts/estimate_heartbeat.py`. | fixed in 7da0ad5 |
| 11 | Important | skills/dev-implementation/resources/scripts/check_task_contract.py:223 | Separate Allowed/Evidence ownership maps permit duplicate cross-category `(new)` claims. Additionally, `lstrip("./")` conflates distinct `.agents/x` and `agents/x` paths. Both defects were reproduced. | fixed in 7da0ad5 |
| 12 | Important | tests/test_rsdh_orchestration.py:1339 | Scenario bindings are incorrect: HP-05 exercises profile detection, EC-08 cleanup, ST-03 heartbeat updates, and ST-07 documentation caps. Their passing results therefore certify different behavior from the corresponding canonical Gherkin scenarios. | fixed in 7da0ad5 |

Raw output:

```text
Verdict: CHANGES REQUIRED
```

## Round 2

- **Date**: 2026-11-13T07:47:55Z
- **SHA**: b6e0ecfcf17d31c788139600b34f92fe9ea7e65a
- **Base**: main
- **CLI**: claude
- **Model**: Opus 5.5
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Raw log**: `build/reviews/runtime_sync_and_dashboard_hardening_code_round2_b6e0ecf.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Critical | .agents/quality/python-quality.json:3 | adding `scripts/_state_envelope.py` and `scripts/estimate_heartbeat.py` to `lint`/`type_check` without updating tasks' V4/V5 rows makes `check_task_contract.py --design` exit 1 with 12 "missing registered capability" problems (0 on `main`), so `check_epic_readiness.py` and `package_epic.py --revise` now abort for this epic and for already-merged Python epics — defeating task_03's Stage 3 `--revise` fix. | fixed in fa8f958 |
| 2 | Important | skills/dev-implementation/resources/scripts/sync_task_status.py:375 | the envelope is keyed by the task frontmatter `epic:` value (underscores) while `resume_context.write_epic_state` and `manage_worker_pool` key by the hyphen slug, producing two `<epic>.heartbeat.json` + two `<epic>.md` files with independent `generation` counters and a duplicated epic in `assistant_state.md`, breaking the HLD's single-envelope contract and `RSDH-AR-01`'s monotonic-generation guarantee. | fixed in 7fafd2a |
| 3 | Important | skills/dev-implementation/resources/scripts/sync_task_status.py:327 | `_collect_epic_task_summary`/`board_tally` run over `summary_roots` with the primary checkout first and dedupe first-seen-wins, so stale primary `.devtool/features/` copies override the worktree's authoritative statuses; the shipped state records `[todo: 7]` and "Start task_01" while all 7 tasks are `done`. | fixed in 7fafd2a |

Raw output:

```text
Verdict: CHANGES REQUIRED
```
