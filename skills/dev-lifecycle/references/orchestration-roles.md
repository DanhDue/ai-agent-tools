# Four-Persona Role Matrix (Stages 1–3)

Single source of truth for the four personas, how the **Orchestrator** (Role 2.2, the Stage 3 main session) dispatches Role 2.1 and Role 2.3 subagents, and who may touch what, across `d3nexus:dev-designer`, `d3nexus:principal-review`, `d3nexus:dev-implementation` and `d3nexus:cross-model-review`. Personas are named by function, not by model: reviewer providers (`Claude -> Codex -> Kiro -> Argon`) are external review CLIs and unrelated to a persona's own model binding.

Each persona maps to a config key in `/d3nexus:dev-config` (`ai_architect_reviewer`, `orchestrator`, `programmer`); Role 1.0 is the user. In autonomous mode, `lifecycle_runner.py` is the Orchestrator and implements this matrix itself (`build_agy_command`, the `fix-planner` and `review-fixer` dispatch, `run_gate4`); the runner is authoritative there. This page governs interactive orchestration.

## Contents

- [1. Boundaries](#1-boundaries)
- [2. Dispatching Subagents](#2-dispatching-subagents)
- [3. Summary Contracts](#3-summary-contracts)
- [4. Independent Verification](#4-independent-verification)
- [Old-to-New Role Mapping](#old-to-new-role-mapping)

## 1. Boundaries

| Persona | Config key | May run | May edit | Forbidden |
|---|---|---|---|---|
| **Role 1.0 Human Architect** | — | anything | anything | — (owns Gates 1, 2, 5 and every escalation) |
| **Role 2.1 AI Architect & Reviewer** | `ai_architect_reviewer` | `resume_context.py`, `check_epic_readiness.py`, `package_epic.py`, `run_external_review.py` (synchronous external CLI calls for `/principal-review`), git metadata; as `task-reviewer` only `run_task_checks.py status` and `check_bdd_traceability.py` | spec, HLD, BDD scenarios, task Verification tables and `Allowed files` at design time, non-epic plans, `principal_review.md` | editing `src/` or `tests/`; running test suites, linters or type checkers; dispatching subagents or managing the worker pool |
| **Role 2.2 Orchestrator** | `orchestrator` | lifecycle scripts (`run_external_review.py`, `compute_execution_order.py`, `manage_worker_pool.py` including `triage-fix` [reading its bounded `<= 30` non-test line diff when `ELIGIBLE_FOR_SHORT_CIRCUIT`] and `finalize-slot` [whose internal read-only `run_task_checks.py status` and `check_bdd_traceability.py` status gates verify mechanical completion without running test suites], `sync_task_status.py`, `resume_context.py`, `dev_config.py`, `package_epic.py`, `check_epic_readiness.py`, `$INTEGRATE preflight`), git metadata (`git rev-parse`, `git status --porcelain`, `git log`, `git diff --name-only`/`--stat`) | Phase 3 Doc Sync prose; `fix_plan_round<N>.md` (from `fix-planner` `plan_markdown`); task status through `sync_task_status.py`; `review_results.md` / `principal_review.md` Decision cells only for `dismissed:` entries | direct reading or editing of `src/` / `tests/` (sole bounded exception: reading `triage-fix` `bounded_diff` JSON when `ELIGIBLE_FOR_SHORT_CIRCUIT`); editing HLD, BDD, task Verification tables, DoD or `Allowed files`; running tests, linters, type checkers, direct `run_task_checks.py` execution or `verify-tier` |
| **Role 2.3 Programmer** | `programmer` | `run_task_checks.py`, `check_code_impact.py`, `check_bdd_traceability.py`, test suites, linters, type checkers, `audit_epic.py`, `@quality_check`, `$INTEGRATE rebase` / `verify-tier` | `src/`, `tests/`, evidence, task `## Definition of Done` checkbox ticks (`- [x]` + brief mechanical output summary after `run_task_checks.py verify`), task status — bounded by the task's `Allowed files`; `fixed in <sha>` Decision cells; the generated `manual_smoke_checklist.md` | editing HLD, BDD scenarios, `shared-contracts/`, task Verification tables / DoD requirements / `Allowed files`; marking `status: "done"` (or setting `completedAt`) while any `- [ ]` remains in `## Definition of Done`; calling `manage_worker_pool.py` |

The Orchestrator reads epic docs (HLD, `bdd_scenarios.md`, legacy `bdd_scenarios.en.md`), `review_results.md`, `principal_review.md`, `fix_plan_round<N>.md`, quality reports and subagent summaries; a Role 2.3 subagent reads everything inside its slot or epic worktree.

`manage_worker_pool.py` is Orchestrator-only: its `sync`/`merge` read-modify-write the shared epic heartbeat, so calls must stay serialized in one process. Role 2.1 never spawns or waits on subagents.

## 2. Dispatching Subagents

**Session map.** The kit cannot choose a main session's model; Role 1.0 picks it when opening the IDE or CLI. Stages 1–2 run in a session on the `ai_architect_reviewer` model. Stage 3 runs in a session on the `orchestrator` model, opened from `resume_context.py --emit-prompt implement`. With **Triển khai (tự động)** Stage 3 continues in the Stage 2 session, so Role 2.2 then runs on that session's model. The kit can choose only the model of a subagent it dispatches.

1. **Resolve the binding.** Never read `.devtool/review_config.json` providers or `AGY_*` model variables for persona models; ask the resolver:
   ```bash
   python3 scripts/dev_config.py resolve <persona> --format argv --mode <read-only|write>
   ```
   `read-only` serves `task-reviewer` and `fix-planner` (strictly read-only, edits no files; `fix-planner` returns `plan_markdown`, and the Orchestrator writes and commits `fix_plan_round<N>.md`). `write` serves `task-implementer`, `review-fixer` and `gate4-verifier`. Use `--format json` to read the model, effort and fallback.
2. **Dispatch Role 2.3 through the agy profile pool.** Dispatch headless with the working directory set to the slot or epic worktree, using the pooled dispatcher instead of a hand-built `agy` command:
   ```bash
   python3 scripts/dev_config.py dispatch --persona programmer --mode write --prompt-file <file> --cwd <slot> --log <log> --epic <slug> --task <id> --slot <n>
   ```
   The lease file `agy_profile_leases.json` (under `$REAL_HOME/.d3nexus/`) records which profile each run uses; with no pool configured the dispatcher runs once on the host profile. The Orchestrator never launches `agy` itself and never builds a `HOME` or `AGY_PROFILE` for it. For Role 2.1 subagents use `--persona ai_architect_reviewer --mode read-only`; for `claude`, `codex` or `kiro` bindings the same command launches the CLI directly.
3. **Exit codes.** `0` means the subagent ran; read its summary contract. `1` means validation, task failure, `model_unavailable` or `preflight_failed`. `2` means every pool profile is out of quota, or quota ran out mid-work: record a quota pending decision with the printed report and stop (`resume_context.py --pending-decision "<persona> quota exhausted" --decision-kind quota --epic <slug>`), after a `quota_low` checkpoint. Never retry and never switch models on your own.
4. **Unavailable model.** On the first dispatch failure caused by a missing CLI, failed authentication or exhausted quota, there is no automatic fallback, no retry: checkpoint `model_unavailable`, record a blocker with the fallback command (for example `/d3nexus:dev-config set programmer claude-sonnet high`), stop. A task failure (red tests, failing checks) is not a model failure.
5. **Pool exhausted.** When `dispatch` reports `no_profile`, the report lists each profile's reset time and the recovery commands (`/d3nexus:dev-config profiles clear`, `/d3nexus:dev-config set programmer ...`). Present that report in the pending decision and stop; Role 1.0 chooses.
6. **In-runtime subagent tools** (Antigravity `invoke_subagent`, Claude Code `Task`) are acceptable **only** if they can pin the exact model and effort that `resolve` printed. Antigravity's `Model` enum (`inherit`/`flash_lite`/`flash`/`pro`) cannot, so never substitute `Model="flash"` or `"inherit"` for a Role 2.1 or Role 2.3 binding.
7. **Checkpoints.** After reading each subagent's summary contract and before the next dispatch, write `python3 scripts/resume_context.py --checkpoint subagent_returned --epic <slug>`; after every wave merge, `--checkpoint wave_merged`. Before Stage 3, each wave and each `/cross-model-review` fix round run `python3 scripts/dev_config.py quota-check`; exit `2` stops as in step 3.

Every brief names: the persona and brief role, worktree path, task or round, the exact inputs (task file, finding IDs + `PROPOSED ACTION`, approved `fix_plan_round<N>.md`), the dispatch mode, and the summary contract below. Generate the header and JSON contract with:

```bash
python3 scripts/resume_context.py --emit-prompt brief --brief-role <task-implementer|task-reviewer|fix-planner|review-fixer|gate4-verifier> --epic <epic_slug>
```

`principal-reviser` has no emitted brief: it runs inline in the Stage 2 session or as a same-model subagent briefed from `principal-review/SKILL.md`.

| Brief role | Persona | Mode | Purpose |
|---|---|---|---|
| `task-implementer` | Role 2.3 | `write` | TDD inside `Allowed files`; runs full mechanical `Verification` (`RED -> GREEN -> REGRESSION -> TIER-B -> TIER-C`) via `run_task_checks.py` and ticks all `## Definition of Done` checkboxes `[x]` with brief mechanical result notes (`exit 0, N passed`) |
| `task-reviewer` | Role 2.1 | `read-only` | Semantic and architectural review of the slot diff (only for gated high-risk or multi-module tasks, never routine purely mechanical tasks); never edits, commits or runs test suites |
| `review-fixer` | Role 2.3 | `write` | Applies fixes in `fast-track` or `apply-plan` mode |
| `gate4-verifier` | Role 2.3 | `write` | Runs full Gate 4 on a fresh context |
| `principal-reviser` | Role 2.1 | inline or same-model subagent | Revises HLD, BDD and task prose after `/principal-review` findings; read-only on `src/`/`tests/` |
| `fix-planner` | Role 2.1 | `read-only` | Drafts fix plan for high-risk findings (returns `plan_markdown`; Orchestrator writes `fix_plan_round<N>.md`) and classifies against halt criteria |

## 3. Summary Contracts

Each subagent ends with exactly one fenced `json` block; the Orchestrator reads nothing else.

| Role | Required keys |
|---|---|
| `task-implementer` | `task_id`, `slot`, `status` (`DONE`/`BLOCKED`/`NEEDS_CONTEXT`), `head_sha`, `verify` (`PASS`/`FAIL`), `changed_files`, `non_test_modules_changed`, `review_tier`, `labels`, `finalized` (bool) |
| `task-reviewer` (Role 2.1) | `task_id`, `pass` (`1`/`2`), `verdict` (`APPROVED`/`CHANGES_REQUESTED`), `head_sha`, `done_gate` (`PASS`/`FAIL`), `blockers`, `observations` |
| `review-fixer` | `round`, `mode` (`fast-track`/`apply-plan`), `status` (`FIXED`/`BLOCKED`), `fix_shas`, `decision_sha`, `changed_files`, `tier1` (`PASS`/`FAIL`) |
| `gate4-verifier` | `candidate_sha`, `verdict` (`PASS`/`FAIL`), `audit_exit`, `quality_check_report`, `failures` |
| `principal-reviser` (Role 2.1) | `round`, `status` (`REVISED`/`ESCALATE`), `revision_sha`, `decision_sha`, `changed_files`, `escalations` |
| `fix-planner` (Role 2.1) | `round`, `status` (`PLANNED`/`ESCALATE`), `halt_criteria` (list), `plan_markdown` |

## 4. Independent Verification

The agent that changes code never has the last word on it.

1. **Mechanical Verification vs. LLM Review (Selective review gating, Blocker-Only rubric & Two-Tier Risk Assessment Gate).**
   - **Mandatory Per-Task Mechanical Verification (Role 2.3 Programmer)**: Every task — regardless of size or `review_tier` — must run and pass all mechanical `Verification` rows (`RED -> GREEN -> REGRESSION -> TIER-B -> TIER-C`), including regression suites for the touched module and *Downstream Callers* plus `TIER-B` static checks across all `Allowed files` (production and test files), and tick every `- [ ]` checkbox in `## Definition of Done` to `- [x]` with a brief mechanical result summary (e.g. `exit 0, 42 passed`) before `status: "done"` or `completedAt` can be written.
   - **Selective LLM Review (Role 2.1 `task-reviewer` & `/cross-model-review`)**: LLM review does not run repeatedly on small, purely mechanical tasks (avoiding review bottlenecks) and focuses instead on semantic/architectural boundaries, high-risk tasks, and pre-Gate 4 / post-Gate 4 synthesis. `needs_review = review_tier == "full"` OR `labels` ∩ {`security`, `architecture`, `concurrency`, `contract`} OR `non_test_modules_changed > 2`. The implementer finalizes (`sync_task_status.py task <id> done` + commit) only when `needs_review` is false. The Orchestrator recomputes the module count with `git -C <slot> diff --name-only <base>..<head_sha>`; on mismatch it dispatches the Role 2.1 `task-reviewer` anyway.
   - **Hard cap**: `max_task_review_passes = 2`, `max_fix_passes = 1` (enforced by `manage_worker_pool.py`).
   - **Blocker-Only rubric (`BLOCKER` vs. `NON_BLOCKING_OBSERVATION`)**: Pass 1 (`--review-pass 1`) audits comprehensively and reports all `BLOCKER` items (`BDD_VIOLATION`, `CONTRACT_SCHEMA_VIOLATION`, `RUNTIME_SAFETY`, `OWNERSHIP_ARCHITECTURE_VIOLATION`) upfront to trigger `CHANGES_REQUESTED`; minor refinements/style nits are logged as `NON_BLOCKING_OBSERVATION` under `observations` with `"verdict": "APPROVED"` (empty `blockers` with `done_gate: "PASS"` coerces to `APPROVED`). On `APPROVED`, call `manage_worker_pool.py finalize-slot ... --mode pass1-approved`.
   - **Two-Tier Risk Assessment Gate (after Fix Pass 1)**: On `CHANGES_REQUESTED` with `>= 1` `BLOCKER`, run `sync --status working --no-reset` (`fix = 1`) and dispatch Role 2.3 `task-implementer` with `pass1_blockers` only. Once `run_task_checks.py verify` passes, run `manage_worker_pool.py triage-fix` (Tier 1 deterministic check over `pass1_tree_sha..curr_tree_sha`): `HIGH_RISK` (`> 30` non-test lines, sensitive surface, or weakened tests; `bounded_diff: null`) routes directly to Review Pass 2; `ELIGIBLE_FOR_SHORT_CIRCUIT` (`<= 30` non-test lines) passes `bounded_diff` and `pass1_blockers` to Role 2.2 Tier 2 `RiskAssessment` — **the single permitted Role 2.2 semantic ruling** (strictly bounded to evaluating `ELIGIBLE_FOR_SHORT_CIRCUIT` `bounded_diff` against `pass1_blockers`, whereas `fix-planner` plans remain governed by the halt criteria). `LOW` routes to `finalize-slot --mode tier2-short-circuit --risk-level LOW` (skipping Pass 2); `MEDIUM`/`HIGH` runs `triage-fix --record-tier2`, `sync --status review` (`review = 2`), Role 2.1 `task-reviewer --review-pass 2` (Delta-Only Verification over `git diff <pass1_tree_sha>`, `DIRECT_REGRESSION` only), and `finalize-slot --mode pass2-complete` (logs residual remarks to `review_audit_notes.jsonl`; zero Fix Pass 2).
2. **Findings are routed by risk, by the Orchestrator, not the fixer**, from the triage output (mirroring `_can_fast_track_code_findings`):
   - **Low risk** — every open finding is `Valid`, severity `Important` or `Minor` (a `Critical` finding is always high risk), and the triage contains none of: `shared-contracts`, `CRITICAL_CONFLICT`, `SHARED_CONTRACT_CONFLICT`, `Debatable`, `ambiguous`, `architectural state transition`, `trade-off`, `Not shown`, `False positive`; or a Gate 4 failure is the first failure of that check. A Role 2.3 `review-fixer` runs in `fast-track` mode.
   - **High risk** — any `Critical` finding, any escalation marker above, or the same Gate 4 check failing twice in a row. The Orchestrator dispatches a Role 2.1 `fix-planner`:
     - the plan touches none of the five halt criteria → `PLANNED`; a fresh Role 2.3 `review-fixer` applies it in `apply-plan` mode;
     - the plan touches any halt criterion → `ESCALATE`; record `--pending-decision`, render the Top 3 Highest-Risk Findings, and stop for Role 1.0.
   - The Orchestrator does not rule on fix plans; the plan's author is the design authority and the halt criteria replace the ruling.
3. **The five halt criteria** (details in [governance-checklists.md](governance-checklists.md)): `CRITICAL_CONFLICT`, `Debatable` / `Not shown`, `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, `MAX_ROUNDS_CRITICAL_REMAINING`.
4. **Post-fix scope check (review fixers).** The Orchestrator runs `git diff --name-only <pre_sha>..HEAD`. Any path under `shared-contracts/` or `.devtool/epic/<epic_dir>/` other than `review_results.md` / `principal_review.md` / `fix_plan_round<N>.md` halts with `CRITICAL_CONFLICT` (never auto-revert). Other files outside the findings' locations and their tests are listed in the Gate 5 executive report. A `fix-planner` edits no files (strictly read-only; it returns `plan_markdown`, and the Orchestrator writes and commits `fix_plan_round<N>.md`).
5. **Gate 4 is run by a fresh `gate4-verifier`** — never the implementer, reviewer or fixer of the same round. It edits no code (only the generated smoke checklist commit); on failure it returns `FAIL`, the Orchestrator dispatches a fixer, then a new verifier. The Orchestrator accepts `PASS` only when `candidate_sha == git rev-parse HEAD`, `git status --porcelain` is empty, and the `@quality_check` report it reads is bound to that SHA.

## Old-to-New Role Mapping

This table is the only place the retired Tri-Role labels may appear. Every other file uses the new labels.

| Tri-Role (old) | Four-persona (new) |
|---|---|
| Role 2.1 Human Architect | Role 1.0 Human Architect |
| Role 2.2 AI Assistant (design work, reviser, fix-plan ruling) | Role 2.1 AI Architect & Reviewer |
| Role 2.2 Orchestrator (Stage 3 main session) | Role 2.2 Orchestrator |
| Role 2.3 AI Programmer | Role 2.3 Programmer |

The `--role` values accepted by `resume_context.py` are `architect`, `orchestrator` and `programmer`; `assistant` remains an alias of `architect` for existing state files.
