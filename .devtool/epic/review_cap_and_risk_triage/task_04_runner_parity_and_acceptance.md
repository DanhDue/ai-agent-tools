---
id: "task_04_runner_parity_and_acceptance"
status: "todo"
completedAt: null
priority: "high"
assignee: null
epic: "review_cap_and_risk_triage"
dueDate: null
created: "2026-11-18T06:26:00Z"
modified: "2026-11-18T06:26:00Z"
labels: ["runner", "integration", "acceptance", "architecture"]
order: "a4"
review_tier: "full"
---

# Task 4: Lifecycle Runner Parity verify.sh Registration and End-to-End Acceptance

Epic: [review_cap_and_risk_triage](review_cap_and_risk_triage.md)

## Requirement Analysis

Align autonomous `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` with the task-review cap, Blocker-Only Coercion Guard, and Pass 2 Delta-Only termination rules from Tasks 1–3, register all four `tests/test_trc_*.py` suites in `scripts/verify.sh`, and verify end-to-end acceptance across the epic blast radius (Spec §8.2, §9, §10.2; HLD Module Contracts §4):

1. **Autonomous `lifecycle_runner.py` Parity**:
   - Load `(max_review_passes, max_fix_passes)` in `_execute_single_task` via `persona_config.resolve_task_review_limits(self.root)` (default `(2, 1)`), bounding task attempts to `max_attempts = max(1, min(max_review_passes, max_fix_passes + 1))`.
   - Update `_build_task_reviewer_prompt` (`L1690-L1710`) to accept `review_pass: int = 1`, `pass1_tree_sha: str | None = None`, and `pass1_blockers: Sequence[Mapping[str, Any]] | None = None`:
     - Pass 1 emits the structured `APPROVED|CHANGES_REQUESTED` JSON contract with `BLOCKER` vs. `NON_BLOCKING_OBSERVATION` rules (while still noting legacy `PASS` compatibility).
     - Pass 2 emits **Delta-Only Verification** instructions referencing `git diff <pass1_tree_sha>` and `pass1_blockers`, forbidding new non-regression findings.
   - Normalize reviewer JSON output via `manage_worker_pool.normalize_task_review_payload` (imported from sibling `dev-implementation/resources/scripts/manage_worker_pool.py`):
     - Fail closed (`verdict=UNPARSEABLE`, no `APPROVED` coercion) when `_extract_last_fenced_json(rev_out)` returns `None` (`TRC-FR-03`), when `rev_code != 0`, when `rev_done_gate != "PASS"`, when `not task_id_ok`, or when `rev_sha != impl_head_sha`.
     - When `normalized["verdict"] == "APPROVED"` (including zero-blocker `CHANGES_REQUESTED` coerced to `APPROVED`) with valid SHA and `done_gate == "PASS"`: call `self._finalize_task_done(...)` in `exec_root`. If `observations` is non-empty: when `worktree_dir is None`, call `manage_worker_pool.append_review_audit_note(self.root, exec_root, self.epic_slug, self.epic_slug, task_slug, entry, commit=True)` directly; when `worktree_dir is not None` (pool mode), append `entry` to `self._pending_audit_notes[task_slug]` so `_run_pool_batch` (`L2538-L2548`, inside `with merge_lock:` immediately after `pool_mod.merge_slot(...)` succeeds) flushes and commits each queued entry onto its existing `epic_wt` parameter (`append_review_audit_note(repo_root, epic_wt, self.epic_slug, self.epic_slug, task_slug, entry, commit=True)`), never onto `main` and never inside a pool slot.
     - When Pass 1 (`review_pass == 1`) returns `CHANGES_REQUESTED` with `>= 1` `blockers` and another attempt remains: capture `pass1_tree_sha = capture_slot_tree_sha(exec_root, self.epic_slug)` (when `self._is_git_repo(exec_root)`), format `retry_note` from `blockers`, and run Fix Pass 1.
     - When Pass 2 (`review_pass == 2` / final allowed review pass) completes with `rev_code == 0`, valid JSON, `rev_done_gate == "PASS"`, `task_id_ok`, and `rev_sha == impl_head_sha`, even if `normalized["verdict"] == "CHANGES_REQUESTED"` (`A1` policy, `TRC-ST-04`): call `self._finalize_task_done(...)` and queue/write `{"event": "pass2_residual_logged_on_cap", "task_id": task_slug, "head_sha": impl_head_sha, "blockers": normalized["blockers"]}` using the same `worktree_dir is None` (`self.root` / `exec_root`) vs. `self._pending_audit_notes[task_slug]` -> `_run_pool_batch` (`repo_root` / `epic_wt`) mechanism (never staging `review_audit_notes.jsonl` inside a pool slot and never spawning Fix Pass 2).
2. **`scripts/verify.sh` Registration**:
   - Register `tests/test_trc_persona_limits.py` (`affects_doc_only=False`), `tests/test_trc_reviewer_briefs_and_governance.py` (`affects_doc_only=True`), `tests/test_trc_worker_pool_triage.py` (`affects_doc_only=False`), and `tests/test_trc_runner_and_acceptance.py` (`affects_doc_only=False`) in `SUITES` (Section `"11"`, mode `"pytest"`).
3. **End-to-End Acceptance Suite (`tests/test_trc_runner_and_acceptance.py`)**:
   - Cover `TRC-HP-04`, `TRC-ST-04`, and `TRC-FR-03`, plus verify that `scripts/verify.sh` `SUITES` registers all four `tests/test_trc_*.py` files.

## Files

Allowed files:
- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`
- `scripts/verify.sh`
- `tests/test_trc_runner_and_acceptance.py` (new)

Read-only context:
- `.devtool/epic/review_cap_and_risk_triage/review_cap_and_risk_triage.md` — HLD Module Contracts §4 & Integration Test Plan
- `scripts/persona_config.py` — `resolve_task_review_limits` (Task 1)
- `scripts/resume_context.py` — `--review-pass 1|2` contract (Task 2)
- `skills/dev-implementation/resources/scripts/manage_worker_pool.py` — `normalize_task_review_payload`, `capture_slot_tree_sha`, `append_review_audit_note` (Task 3)
- `tests/test_fpg_runner_personas.py` — existing `FPG-ST-05` task-reviewer SHA & `done_gate: FAIL` tests `(L720-L865, L1835-L1880)`

## Design Rationale

Sharing `normalize_task_review_payload` and `capture_slot_tree_sha` between `manage_worker_pool.py` and `lifecycle_runner.py` guarantees identical verdict coercion, hard caps, and audit-note logging across interactive 2-slot orchestration and headless autonomous runs. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`: `_build_task_reviewer_prompt` `(L1690-L1710)`, `_execute_single_task` `(L1780-L1957)`, `_run_pool_batch` `(L2538-L2567)`
  - `scripts/verify.sh`: `SUITES = [` `(L362-L464)`
- **Downstream Callers**: `tests/test_fpg_runner_personas.py`, `tests/test_lifecycle_runner.py`, `tests/test_token_throttling_acceptance.py`, Gate 4 `architecture` check (`bash scripts/verify.sh`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% branch coverage of Pass 1 approval with observations, Pass 2 Delta-Only retry + `A1` cap finalization, unparseable JSON fail-closed handling, and `verify.sh` registration.

### BDD SCENARIOS

Covers: TRC-HP-04, TRC-ST-04, TRC-FR-03

```gherkin
Scenario: [TRC-HP-04] [Tier C - Integration] End-to-end runner parity and verify.sh registration enforce Pass 1 non-blocking approval and Pass 2 cap
Given an isolated git repository with an English-only epic of two review-gated tasks and stub persona CLIs
When Task 1's Pass 1 reviewer returns {"task_id": "task_01", "pass": 1, "verdict": "APPROVED", "head_sha": "<sha1>", "done_gate": "PASS", "blockers": [], "observations": [{"id": "OBS-1", "file": "src/a.py", "summary": "Style nit"}]}
And Task 2's Pass 1 reviewer returns {"task_id": "task_02", "pass": 1, "verdict": "CHANGES_REQUESTED", "head_sha": "<sha2>", "done_gate": "PASS", "blockers": [{"id": "BLK-1", "category": "BDD_VIOLATION", "file": "src/b.py", "summary": "Fix return code", "remediation": "Return 0"}], "observations": []} followed by Fix Pass 1 producing "<sha2_fix>" and Pass 2 Delta-Only {"task_id": "task_02", "pass": 2, "verdict": "APPROVED", "head_sha": "<sha2_fix>", "done_gate": "PASS", "blockers": [], "observations": []}
Then Task 1 finalizes after exactly 1 review pass and 0 fix passes with "OBS-1" recorded and committed on the epic branch in "review_audit_notes.jsonl"
And Task 2 finalizes after exactly 2 review passes and 1 fix pass with Pass 2 prompt containing Delta-Only instructions
And "scripts/verify.sh" lists all four "tests/test_trc_*.py" suites in "SUITES"

Scenario: [TRC-ST-04] [Tier C - Integration] Headless lifecycle_runner caps review passes at 2 and finalizes on Pass 2 completion when done_gate is PASS
Given an autonomous "LifecycleRunner" configured with default limits ("max_task_review_passes" == 2, "max_fix_passes" == 1) and a review-gated task "task_01"
When Pass 1 "task-reviewer" returns "CHANGES_REQUESTED" with 1 blocker, Fix Pass 1 succeeds, and Pass 2 "task-reviewer" returns residual "CHANGES_REQUESTED" with "done_gate": "PASS" and matching "head_sha"
Then the runner dispatches "task-implementer" exactly twice (initial + Fix Pass 1) and "task-reviewer" exactly twice (Pass 1 + Pass 2), logs "pass2_residual_logged_on_cap" to "review_audit_notes.jsonl", and marks "task_01" done

Scenario: [TRC-FR-03] [Tier A - Unit] Unparseable or missing task-reviewer JSON output fails closed without triggering Coercion Guard
Given raw reviewer stdout containing prose with no fenced JSON block or a malformed JSON block "{not valid json}"
When "lifecycle_runner.py" or "normalize_task_review_payload" processes the reviewer output
Then it never coerces the verdict to "APPROVED", records "verdict=UNPARSEABLE", and respects the "max_task_review_passes" bound without infinite retries
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_trc_runner_and_acceptance.py::test_trc_hp_04_end_to_end_runner_and_verify_registration` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_trc_runner_and_acceptance.py tests/test_fpg_runner_personas.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m unittest tests/test_lifecycle_runner.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_trc_runner_and_acceptance.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_trc_runner_and_acceptance.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/review-cap-and-risk-triage.xml tests/test_trc_persona_limits.py tests/test_trc_reviewer_briefs_and_governance.py tests/test_trc_worker_pool_triage.py tests/test_trc_runner_and_acceptance.py skills/dev-implementation/resources/scripts/test_manage_worker_pool.py tests/test_fpg_persona_config.py tests/test_fpg_checkpoint_and_briefs.py tests/test_fpg_governance_text.py tests/test_tto_docs_and_slimming.py tests/test_fpg_runner_personas.py tests/test_rsdh_orchestration.py tests/test_runtime_sync_and_dashboard_hardening.py tests/test_fpg_english_only_text.py tests/test_workflow_anti_rationalization.py` | exit 0; results build/test-results/review-cap-and-risk-triage.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Source: `tests/test_fpg_runner_personas.py` (`L776-L828`, `L1840-L1880`) asserts that `head_sha: "zzz999"`, `done_gate: "FAIL"`, or `task_id: "other_task"` in `task-reviewer` JSON causes `_execute_single_task` to reject finalization and return `False` after retries. Preserve all three checks strictly: `A1` finalization on Pass 2 applies ONLY when `rev_code == 0`, `rev_summary is not None`, `rev_done_gate == "PASS"`, `task_id_ok`, and `rev_sha == impl_head_sha`.
- Source: Do NOT execute `bash scripts/verify.sh` inside Verification rows `V1..V6` (otherwise `scripts/verify.sh` becomes an implicit protected path in `check_task_contract.py`); instead parse `SUITES` in `tests/test_trc_runner_and_acceptance.py` and let Gate 4 run `bash scripts/verify.sh` via the `architecture` capability.
- New contract: When `rev_summary is None` (`TRC-FR-03`), `retry_note` records `verdict=UNPARSEABLE` (matching existing `L1947` format `verdict={rev_verdict or 'UNPARSEABLE'}`) and never coerces or finalizes.

## Definition of Done

- `TRC-HP-04`, `TRC-ST-04`, and `TRC-FR-03` pass alongside `test_fpg_runner_personas.py`, `test_lifecycle_runner.py`, and the full blast-radius integration suite `V6`. (V2, V3, V6)
- All four `tests/test_trc_*.py` suites are registered in `scripts/verify.sh` `SUITES`. (V2, V6)
- `ruff check` and `mypy` pass with zero errors on `lifecycle_runner.py` and `tests/test_trc_runner_and_acceptance.py`. (V4, V5)
- End-to-end blast-radius JUnit report `build/test-results/review-cap-and-risk-triage.xml` is green. (V6)
- Runner parity and `verify.sh` suite registration are ready for Human Architect review. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 1](task_01_persona_config_task_review_limits.md), [Task 2](task_02_reviewer_briefs_and_governance_exception.md), and [Task 3](task_03_worker_pool_cap_snapshot_and_triage.md).

Downstream dependents (blocked by Task 4): none.

## References & Rollback

- [Epic HLD](review_cap_and_risk_triage.md)
- **Rollback**: Revert `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` and `scripts/verify.sh`, and delete `tests/test_trc_runner_and_acceptance.py`.
