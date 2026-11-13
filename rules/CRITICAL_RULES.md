---
trigger: always_on
---

# Critical Rules

> [!CRITICAL]
> Mandatory engineering rules for ALL AI Agent plugins, orchestrators, and subagents. These rules supersede built-in agent behaviors and never weaken or get bypassed.

Extended checklists live in [governance-checklists.md](../skills/dev-lifecycle/references/governance-checklists.md).

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

- `[SCOPE]` is the uppercase epic name or area touched (`[TOOLS]`). Title is one imperative line, no trailing period. Omit the body when the commit does one thing; otherwise pass two `-m` flags (`git commit -m "..." -m "..."`).
- **Never append trailer lines** (`Co-Authored-By:`, `Generated with`, or tool attribution).

## 3. Git Push Operations (No Unauthorized Push)

Local `git add` / `git commit` are allowed per task scope; **`git push` is STRICTLY PROHIBITED** without explicit user permission.

## 4. Native Planning Mode Interception

Never create loose native plans (`implementation_plan.md`, Composer/Cascade/Codex plans) unless explicitly instructed to bypass `d3nexus`. Use `d3nexus:brainstorming` for single features and `d3nexus:dev-lifecycle` for epics.

## 5. Automated Execution, Cross-Model Review & Stage 4 Finish Gate

1. **Gate 2 Unified Confirmation**: After Gate 2 readiness checks pass, stop before `package_epic.py`, record Gate 2, read `.devtool/review_config.json`, call `resume_context.py --pending-decision` for Choice A pause, and present Gate 2 Choices (`Claude -> Codex -> Kiro -> Argon`):
   - **Option 1 (Recommended) — `Triển khai (tự động)` (AUTO MODE)**: Runs `/principal-review` -> `package_epic.py` -> Gate 3 -> `dev-implementation` (wave-parallel `--parallel`, `manage_worker_pool.py` + `cleanup`) -> Gate 4 -> `/cross-model-review` with zero intermediate confirmation pauses (halting only on Circuit Breakers or Gate 5).
   - **Option 2 — Handoff Mode**: Runs `/principal-review` -> `package_epic.py` -> prints `--emit-prompt implement` -> stops.
2. **Automated Cross-Model Review**: When tasks finish (after Gate 4 passes, Cross-model review must return to a full Gate 4 run), immediately run `/cross-model-review` (`run_external_review.py run --epic-dir <epic_dir> --auto-quota`) with zero intermediate Review Choice prompt.
3. **Stage 4 Finish & Gate 5 Sign-Off**: Stage 4 (`finishing-a-development-branch`) owns `Finish`. After cross-model convergence and Gate 4 PASS on the latest SHA, record `resume_context.py --pending-decision`, stop calling tools, and ask the Human Architect for Gate 5 Finish/merge strategy (`Squash`, `--no-ff`, `Rebase`). Never auto-merge or auto-push.

## 6. Auto-Triage Gate, 3-Round Funnel & Remediation Protocol

External reviews (`/principal-review`, `/cross-model-review`) enforce `max_rounds = 3`, quota priority (`Claude -> Codex -> Kiro -> Argon`), and Auto-Triage (details in [governance-checklists.md](../skills/dev-lifecycle/references/governance-checklists.md)):

- **`AUTO_PASS_CLEAN` / `AUTO_PASS_FINAL_MINOR_SWEEP` (`0 Critical`, `0 Important`)**: Verify against source + approved Spec/HLD, fix valid `Minor` items once, run local gate, and complete without another external round.
- **`AUTO_FIX_ELIGIBLE` (Rounds 1–2)**:
  - **Stage 2 `/principal-review` (BOTH Interactive Mode and Autonomous `/dev-lifecycle` Mode)**: Run `run_external_review.py triage --kind principal --epic-dir <epic_dir>` and verify findings against source + Spec/HLD first. If all blockers verify `Valid` (or objective `False positive`) with zero halt triggers, apply Role 2.2 revisions, commit, run `check_epic_readiness.py <epic_dir>`, and run Round `N+1`. Halt on `CRITICAL_CONFLICT`, `Debatable`, `Not shown`, or Circuit Breakers.
  - **Stage 3 `/cross-model-review` Autonomous Mode**: Unambiguous source-grounded code defects (non-`.md`/non-`shared-contracts/`, zero escalation/trade-off triggers) fast-track via Role 2.3 (`_apply_code_fixes`), commits, **scoped tests only**, and Round `N+1`; ambiguities route through Role 2.2 `fix_plan_round<N>.md` (`APPROVED`/`ADJUSTED`/`CRITICAL_CONFLICT`). Interactive mode (or `Debatable`/`False positive`/halt) pauses after triage.
- **Circuit Breakers (`CIRCUIT_BREAKER_HALT`)**: Halt via `--pending-decision` on `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, or `MAX_ROUNDS_CRITICAL_REMAINING`. If Round 3 ends with `0 Critical`, apply `AUTO_PASS_FINAL_SWEEP` and pass Gate 4 in full.
- **Remediation Hygiene**: Intermediate rounds run static checks + targeted pytest only (full Gate 4/`tests/e2e/` at Final Convergence). Never delete dependencies/reports instead of `uv lock`/regeneration or fake fixtures; run `uv run playwright install chromium` after Playwright upgrades.

## 7. Multi-Repo Boundaries, Symlink Isolation & Contract Governance

- Never stage/commit outside the active git tree. Keep `shared-contracts/` symlinks read-only in satellite git (omit from `Files Allowed`; never autonomously commit in adjacent repos).
- Inspect `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md` before changing wire contracts; log `GAP-XX`/`RFC-XXX` rather than making breaking changes. Satellite workers stay stateless (HTTP REST/SSE only; no direct `DATABASE_URL`).

## 8. Mandatory Two-Tier Project Memory & Tri-Role Persona Discipline

1. **Startup Context**: Run `python3 scripts/resume_context.py` once on entering dev lifecycle work (`dev-lifecycle`, `dev-brainstorming`, `dev-designer`, `dev-implementation`) and summarize in 5–10 bullets. Exempt `/refresh-session`, `/setup_keybindings`, and quick queries.
2. **Tri-Role Boundaries**:
   - **Role 2.1 Human Architect**: Owns Gates 1, 2, 5, escalations, and Stage 4 Finish.
   - **Role 2.2 AI Assistant**: Designs/reviews (`docs/`, `.devtool/`, `shared-contracts/` only); **STRICTLY PROHIBITED** from modifying production or test code.
   - **Role 2.3 AI Programmer**: Executes TDD tasks in worktrees; resolves model via `.devtool/review_config.json["providers"]["programmer"]` (default `gemini-4-hydrogen-xhigh`, `--effort xhigh --mode auto`), bounded strictly to Specs, `Decisions Already Made`, and `Allowed files`.
3. **Checkpoints, Choice A & English SSOT**: Record Choice A pauses (`--pending-decision`, cleared on `--gate`/non-paused `--state`/`--revise`), creator PIC (`--detect-profile`), and English-only internal docs/code/commits; `--complete` at Stage 4; sync `window.title` per [governance-checklists.md](../skills/dev-lifecycle/references/governance-checklists.md).

## 9. Shell Configuration (`.zshrc`) & Multi-Profile OS Boundary Safety

- Back up `~/.zshrc` before edits and run `zsh -n ~/.zshrc` after; avoid duplicate blocks.
- Never mutate `security default-keychain` / `list-keychains -s` or export `HOME`/`AGY_PROFILE`/`TMPDIR` at top-level `~/.zshrc` (keep `$HOME == $REAL_HOME` in IDE terminals).
- Symlink host toolchains from `$REAL_HOME`; keep `.gemini/antigravity`, `state.vscdb`, Keychain, and unique telemetry IDs isolated per profile (`ag_run` strips IPC handles per [governance-checklists.md](../skills/dev-lifecycle/references/governance-checklists.md)).

## 10. Zero-Fluff Output Cap

- Keep discretionary prose, preamble, narration, and redundant recaps minimal during autonomous runs and worker handoffs.
- **Never** omit or truncate required structured outputs: machine Verdicts (`PASS`/`FAIL`/`BLOCKED`, `🟢 LGTM`/`🟡 CONCERNS`/`🔴 BLOCKED`), Findings tables, JSON/provider gate results (`run_external_review.py`, `run_task_checks.py`), worker status contracts, or human Gate prompts.
