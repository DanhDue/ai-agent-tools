# Orchestrator / Programmer Role Matrix (Stages 2–3)

Single source of truth for how the **Orchestrator** (Role 2.2, the main session) delegates to **Programmer subagents** (Role 2.3) in `d3nexus:principal-review`, `d3nexus:dev-implementation` and `d3nexus:cross-model-review`. Roles are named by function, not by model: reviewer providers (`Claude -> Codex -> Kiro -> Argon`) are external review CLIs and unrelated to the Orchestrator's own model.

In autonomous mode, `lifecycle_runner.py` implements this matrix itself (`build_agy_command`, `_can_fast_track_code_findings`, `_draft_fix_plan` -> `evaluate_programmer_fix_plan` -> `_apply_code_fixes`, `run_gate4`); the runner is authoritative there. This page governs interactive orchestration.

## Contents

- [1. Boundaries](#1-boundaries)
- [2. Dispatching Role 2.3](#2-dispatching-role-23)
- [3. Summary Contracts](#3-summary-contracts)
- [4. Independent Verification](#4-independent-verification)

## 1. Boundaries

| | Orchestrator (Role 2.2, main session) | Programmer subagent (Role 2.3) |
|---|---|---|
| May run | lifecycle scripts (`run_external_review.py`, `compute_execution_order.py`, `manage_worker_pool.py`, `sync_task_status.py`, `resume_context.py`, `package_epic.py`, `check_epic_readiness.py`, `$INTEGRATE preflight`), git metadata (`git rev-parse`, `git status --porcelain`, `git log`, `git diff --name-only`/`--stat`) | `run_task_checks.py`, `check_code_impact.py`, `check_bdd_traceability.py`, test suites, linters, type checkers, `audit_epic.py`, `@quality_check`, `$INTEGRATE rebase` / `verify-tier` |
| May read | epic docs (HLD, `bdd_scenarios.en.md`), `review_results.md`, `principal_review.md`, `fix_plan_round<N>.md`, quality reports, subagent summaries | everything inside its slot / epic worktree |
| May edit | epic docs and Phase 3 Doc Sync prose; `review_results.md` / `principal_review.md` Decision cells only for `dismissed:` entries | `src/`, `tests/`, evidence, task status — bounded by the task's `Allowed files`; `fixed in <sha>` Decision cells in `review_results.md`; `fix_plan_round<N>.md`; the generated `manual_smoke_checklist.md` |
| Forbidden | reading or editing `src/` / `tests/`; editing task Verification tables / DoD / `Allowed files`; running tests, linters, type checkers, `run_task_checks.py` or `verify-tier` | editing HLD, `bdd_scenarios.en.md`, `shared-contracts/`, task Verification tables / DoD / `Allowed files`; calling `manage_worker_pool.py` |

`manage_worker_pool.py` is Orchestrator-only: its `sync`/`merge` read-modify-write the shared epic heartbeat, so calls must stay serialized in one process.

## 2. Dispatching Role 2.3

1. Resolve the model from `.devtool/review_config.json["providers"]["programmer"]` (default `gemini-4-hydrogen-xhigh`, effort `xhigh`).
2. Dispatch headless, with the working directory set to the slot or epic worktree:
   ```bash
   agy --model <programmer_model> --effort <effort> --mode auto   # same argv as build_agy_command()
   ```
3. An in-runtime subagent tool (Antigravity `invoke_subagent`, Claude Code `Task`) is acceptable **only** if it can pin that exact model and effort. Antigravity's `Model` enum (`inherit`/`flash_lite`/`flash`/`pro`) cannot, so never substitute `Model="flash"` or `"inherit"` for Role 2.3.
4. If the configured programmer model cannot be dispatched, do not downgrade silently: record `resume_context.py --pending-decision "Programmer model unavailable" --decision-kind blocker --epic <epic_slug>` and stop.

Role 2.2 work may also be delegated to keep the main context lean — e.g. the Principal Review **reviser** — using any subagent on the Orchestrator's own model (`invoke_subagent` `TypeName="self"`, `Model="inherit"`, or Claude Code `Task`). A reviser stays inside Role 2.2 boundaries: read-only on `src/`/`tests/`, edits only `.devtool/epic/<epic_dir>/` docs and task prose.

Every brief names: the role, worktree path, task or round, the exact inputs (task file, finding IDs + `PROPOSED ACTION`, approved fix plan), the dispatch mode, and the summary contract below. Generate the Role 2.3 header and JSON contract with:

```bash
python3 scripts/resume_context.py --emit-prompt brief --brief-role <task-implementer|task-reviewer|review-fixer|gate4-verifier> --epic <epic_slug>
```

## 3. Summary Contracts

Each subagent ends with exactly one fenced `json` block; the Orchestrator reads nothing else.

| Role | Required keys |
|---|---|
| `task-implementer` | `task_id`, `slot`, `status` (`DONE`/`BLOCKED`/`NEEDS_CONTEXT`), `head_sha`, `verify` (`PASS`/`FAIL`), `changed_files`, `non_test_modules_changed`, `review_tier`, `labels`, `finalized` (bool) |
| `task-reviewer` | `task_id`, `verdict` (`PASS`/`FAIL`), `head_sha`, `done_gate` (`PASS`/`FAIL`), `findings` |
| `review-fixer` | `round`, `mode` (`fast-track`/`plan-first`/`apply-plan`), `status` (`FIXED`/`PLAN_WRITTEN`/`BLOCKED`), `fix_shas`, `decision_sha`, `changed_files`, `tier1` (`PASS`/`FAIL`) |
| `gate4-verifier` | `candidate_sha`, `verdict` (`PASS`/`FAIL`), `audit_exit`, `quality_check_report`, `failures` |
| `principal-reviser` (Role 2.2) | `round`, `status` (`REVISED`/`ESCALATE`), `revision_sha`, `decision_sha`, `changed_files`, `escalations` |

## 4. Independent Verification

The agent that changes code never has the last word on it.

1. **Selective review gating.** `needs_review = review_tier == "full"` OR `labels` ∩ {`security`, `architecture`, `concurrency`, `contract`} OR `non_test_modules_changed > 2`. The implementer finalizes (`sync_task_status.py task <id> done` + commit) only when `needs_review` is false. The Orchestrator recomputes the module count with `git -C <slot> diff --name-only <base>..<head_sha>`; on mismatch it dispatches `task-reviewer` anyway.
2. **Fix dispatch mode is decided by the Orchestrator, not the fixer**, from the triage output and mirroring `_can_fast_track_code_findings`:
   - `fast-track` — every open finding is `Valid`, severity `Critical`/`Important`/`Minor`, and the triage contains none of: `shared-contracts`, `CRITICAL_CONFLICT`, `SHARED_CONTRACT_CONFLICT`, `Debatable`, `ambiguous`, `architectural state transition`, `trade-off`, `Not shown`, `False positive`.
   - `plan-first` — otherwise. The fixer writes `fix_plan_round<N>.md` and returns `PLAN_WRITTEN`; the Orchestrator evaluates it against the HLD and `Decisions Already Made` (`APPROVED` / `ADJUSTED` / `CRITICAL_CONFLICT`); on approval a fresh fixer runs in `apply-plan` mode.
3. **Post-fix scope check (review fixers).** The Orchestrator runs `git diff --name-only <pre_sha>..HEAD`. Any path under `shared-contracts/` or `.devtool/epic/<epic_dir>/` other than `review_results.md` / `principal_review.md` / `fix_plan_round<N>.md` halts with `CRITICAL_CONFLICT` (never auto-revert). Other files outside the findings' locations and their tests are listed in the Gate 5 executive report.
4. **Gate 4 is run by a fresh `gate4-verifier`** — never the implementer, reviewer or fixer of the same round. It edits no code (only the generated smoke checklist commit); on failure it returns `FAIL`, the Orchestrator dispatches a fixer, then a new verifier. The Orchestrator accepts `PASS` only when `candidate_sha == git rev-parse HEAD`, `git status --porcelain` is empty, and the `@quality_check` report it reads is bound to that SHA.
