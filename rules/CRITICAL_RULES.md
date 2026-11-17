---
trigger: always_on
---

# Critical Rules

> [!CRITICAL]
> Mandatory engineering rules for ALL AI Agent plugins, orchestrators, and subagents. These rules supersede built-in agent behaviors and never weaken or get bypassed.

## 1. Mandatory Quality Gates

After completing any workflow or skill, run the matching quality gate and fix every issue raised:
- Shipped/build-affecting change -> `@quality_check`
- Prose/documentation deliverable -> `@doc_quality_check`

## 2. Commit Message Format (Universal Standard)

```text
[EPIC_NAME] Task title

- subtask title 01
- subtask title 02
```

- `[SCOPE]` is the uppercase epic name or area touched (`[TOOLS]`). Title is one imperative line, no trailing period. Omit the body when the commit does one thing; otherwise pass two `-m` flags.
- **Never append trailer lines** (`Co-Authored-By:`, `Generated with`, or tool attribution).

## 3. Git Push Operations (No Unauthorized Push)

Local `git add` / `git commit` are allowed per task scope; **`git push` is STRICTLY PROHIBITED** without explicit user permission.

## 4. Native Planning Mode Interception

Never create loose native plans (`implementation_plan.md`, Composer/Cascade/Codex plans) unless explicitly instructed to bypass `d3nexus`. Use `d3nexus:brainstorming` for single features and `d3nexus:dev-lifecycle` for epics.

## 5. Automated Execution, Cross-Model Review & Stage 4 Finish Gate

1. **Gate 2 Unified Confirmation**: After Gate 2 readiness passes, stop before `package_epic.py`, record Gate 2, read `.devtool/review_config.json`, record `--pending-decision` (Choice A), and present (`Claude -> Codex -> Kiro -> Argon`):
   - **Option 1 (Recommended) — `Triển khai (tự động)`**: `/principal-review` -> `package_epic.py` -> Gate 3 -> `dev-implementation` (`--parallel`) -> Gate 4 -> `/cross-model-review`, pausing only on Circuit Breakers, `ESCALATE`, model/quota stops or Gate 5. Stage 3 stays in this session, so Role 2.2 runs on its model (the prompt names the `orchestrator` binding).
   - **Option 2 — `Dừng lại`**: Stops after packaging, printing `--emit-prompt implement`.
2. **Cross-Model Review**: When tasks finish (after Gate 4 passes, Cross-model review must return to a full Gate 4 run), run `/cross-model-review` (`run_external_review.py run --epic-dir <epic_dir> --auto-quota`) with no Review Choice prompt.
3. **Stage 4 Finish & Gate 5**: After convergence and Gate 4 PASS on the latest SHA, record `--pending-decision`, stop, and ask the Human Architect for the merge strategy. Never auto-merge or auto-push.

## 6. Auto-Triage Gate, 3-Round Funnel & Remediation Protocol

External reviews use `max_rounds = 3` and Auto-Triage; remediation hygiene and extended checklists: [governance-checklists.md](../skills/dev-lifecycle/references/governance-checklists.md).

- **`AUTO_PASS_CLEAN` / `AUTO_PASS_FINAL_MINOR_SWEEP`**: verify against source + Spec/HLD, fix valid `Minor` items once.
- **`AUTO_FIX_ELIGIBLE`** (Rounds 1–2):
  - **Stage 2 `/principal-review` (BOTH Interactive Mode and Autonomous `/dev-lifecycle` Mode)**: run `run_external_review.py triage --kind principal --epic-dir <epic_dir>` and verify findings against source + Spec/HLD. If every blocker is `Valid` with no halt trigger, Role 2.1 revises, runs `check_epic_readiness.py <epic_dir>`, and starts Round `N+1`.
  - **Stage 3 `/cross-model-review` Autonomous Mode**: low risk (all `Valid`, no escalation marker, or a Gate 4 check's first failure): Role 2.3 `review-fixer` `fast-track`. High risk (any `Critical`, escalation marker, or the same check failing twice): Role 2.1 `fix-planner` writes `fix_plan_round<N>.md`; `PLANNED` -> `review-fixer` `apply-plan`; `ESCALATE` -> `--pending-decision`, stop for Role 1.0.
- **Halt criteria (`CIRCUIT_BREAKER_HALT`)**: `CRITICAL_CONFLICT`, `Debatable`/`Not shown`, `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, `MAX_ROUNDS_CRITICAL_REMAINING`.

## 7. Multi-Repo Boundaries, Symlink Isolation & Contract Governance

- Never stage/commit outside the active git tree. Keep `shared-contracts/` symlinks read-only in satellite git (omit from `Files Allowed`; never commit in adjacent repos autonomously).
- Inspect `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md` before changing wire contracts; log `GAP-XX`/`RFC-XXX` rather than making breaking changes. Satellite workers stay stateless (HTTP REST/SSE only; no direct `DATABASE_URL`).

## 8. Mandatory Two-Tier Project Memory & Four-Persona Discipline

1. **Startup Context**: Run `python3 scripts/resume_context.py` once on entering dev lifecycle work and summarize in 5–10 bullets (exempt `/refresh-session`).
2. **Four Personas** ([orchestration-roles.md](../skills/dev-lifecycle/references/orchestration-roles.md)):
   - **Role 1.0 Human Architect**: Vision, Gates 1, 2, 5, Stage 4 Finish, escalations.
   - **Role 2.1 AI Architect & Reviewer** (`ai_architect_reviewer`): Stage 1–2 design, packaging; Stage 3 `task-reviewer`, `fix-planner`. Never edits `src/`/`tests/`, runs tests, dispatches subagents, or manages the pool.
   - **Role 2.2 Orchestrator** (`orchestrator`): Gate 3, worker pool, dispatches 2.1/2.3 subagents, verifies claims, marks tasks `done`. Never reads/edits `src/`/`tests/` or HLD/BDD/Verification tables/DoD/`Allowed files`, or runs tests, linters, `run_task_checks.py`.
   - **Role 2.3 Programmer** (`programmer`, default `gemini-4-hydrogen-xhigh`): `task-implementer`, `review-fixer`, `gate4-verifier` in `Allowed files`; no pool calls.
3. **Session map & models**: Role 1.0 opens Stages 1–2 on the `ai_architect_reviewer` model, Stage 3 on the `orchestrator` model (`--emit-prompt implement`). Subagents use their persona's binding from `python3 scripts/dev_config.py resolve <persona> --format argv --mode <read-only|write>` (switch via `/d3nexus:dev-config`). Model unavailable (CLI, auth, quota): no fallback, no retry; checkpoint, `--pending-decision` with the fallback command, stop.
4. **Checkpoints** (`resume_context.py --checkpoint <event> --epic <slug>`): `gate2_tasks_locked` (2.1), `subagent_returned`, `wave_merged` (2.2), `model_unavailable`, `turn_budget`, `low_quota_stop`, `quota_low`.
5. **Turn budget, low-quota & quota gate**: Tool calls between checkpoints are capped by `checkpoint_policy.max_orchestrator_turns_before_checkpoint` (default 8). `/d3nexus:dev-config low-quota on` halves it, finishes the wave in flight, checkpoints `low_quota_stop`, records `--pending-decision`, stops. `dev_config.py quota-check` runs before Stage 3, each wave and each fix round: exit `2` checkpoints `quota_low`, records a `quota` pending decision, stops.
6. **Choice A & English SSOT**: Record Choice A pauses (`--pending-decision`, cleared on `--gate`/non-paused `--state`/`--revise`), creator PIC (`--detect-profile`), and English-only internal docs/code/commits; `--complete` at Stage 4; sync `window.title` per [governance-checklists.md](../skills/dev-lifecycle/references/governance-checklists.md).

## 9. Shell Configuration (`.zshrc`) & Multi-Profile OS Boundary Safety

- Back up `~/.zshrc` before edits and run `zsh -n ~/.zshrc` after.
- Never mutate `security default-keychain` / `list-keychains -s` or export `HOME`/`AGY_PROFILE`/`TMPDIR` at top-level `~/.zshrc` (keep `$HOME == $REAL_HOME` in IDE terminals).
- `ag_run` and any `<profile>-cli` alias must be launched through `zsh -ic` and never from an agent runtime's own shell, because `ag_run` deletes a profile's symlinks when its underscore helper functions are missing.
- Symlink host toolchains from `$REAL_HOME`; keep `.gemini/antigravity`, `state.vscdb`, Keychain, and telemetry IDs isolated per profile ([governance-checklists.md](../skills/dev-lifecycle/references/governance-checklists.md)).

## 10. Zero-Fluff Output Cap

- Keep discretionary prose, preamble, narration, and redundant recaps minimal during autonomous runs and worker handoffs.
- **Never** omit or truncate required structured outputs: machine Verdicts (`PASS`/`FAIL`/`BLOCKED`, `🟢 LGTM`/`🟡 CONCERNS`/`🔴 BLOCKED`), Findings tables, JSON/provider gate results (`run_external_review.py`, `run_task_checks.py`), worker status contracts, or human Gate prompts.
