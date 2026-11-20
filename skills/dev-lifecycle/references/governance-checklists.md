# Governance Checklists & Extended Operating Protocols

> Reference checklists offloaded from [CRITICAL_RULES.md](../../../rules/CRITICAL_RULES.md) to keep always-loaded rules concise while preserving full operational detail.

---

## 1. External Review Quota Priority, Triage Gate & Remediation Protocol

### 1.1 Quota-Aware Provider Priority & 3-Round Convergence Funnel
- **Provider Priority (`Claude -> Codex -> Kiro -> Argon`)**: Evaluations follow `["claude", "codex", "kiro", "agy"]` using `check-quota` thresholds:
  - Claude & Codex: `5H >= 15%` AND `7D > 2%`
  - Kiro: `Monthly Credits >= 3%` (`>= 15 credits`)
  - Argon (`agy`): `Weekly >= 10%` or `5H >= 15%`
- **3-Round Scope-Narrowing Funnel (`max_rounds = 3`)**:
  - `Round 1`: Full Scope Audit
  - `Round 2`: Delta Verification of `prev_sha..curr_sha` (no new `Minor` findings on untouched files)
  - `Round 3`: Blocker-Only Convergence Mode

### 1.2 Severity-Tiered Auto-Triage Gate
- **`AUTO_PASS_CLEAN` (`0 findings`)** or **`AUTO_PASS_FINAL_MINOR_SWEEP` (`0 Critical`, `0 Important`, only `Minor`)**:
  - Verify findings against live source and approved Spec/HLD (`Decisions Already Made`) first; halt only on `CRITICAL_CONFLICT`, `Debatable` trade-off choices, or `CIRCUIT_BREAKER_HALT`.
  - Otherwise fix valid `Minor` items in a single sweep, commit revisions + decisions, verify the local quality gate (`check_epic_readiness.py` + `package_epic.py` [or `--revise`] at Stage 2 end; full Gate 4 in Stage 3), and complete the review stage without invoking another external round.
- **`AUTO_FIX_ELIGIBLE` (Rounds 1–2 with `Critical`/`Important` findings and no Fix Loop)**:
  - **Stage 2 `/principal-review` (BOTH Interactive Mode and Autonomous `/dev-lifecycle` Mode)**: Run `run_external_review.py triage --kind principal --epic-dir <epic_dir>` and verify every finding against source + approved Spec/HLD before editing any document. Present `## Auto-Triage Gate`, `## Top 3 Highest-Risk Findings`, and `## Findings`. When all blocking findings verify `Valid` (or objective `False positive` with exact proof) and zero halt triggers apply, apply Role 2.1 design revisions (`principal-reviser`), commit revisions + decisions (`fixed in <sha>`), run scoped `check_epic_readiness.py <epic_dir>` (do NOT package `handoff.md` prematurely), and advance to Round `N+1`. Stop immediately on `CRITICAL_CONFLICT`, `Debatable`/`Not shown`, `CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)`, `CIRCUIT_BREAKER_HALT (FIX_LOOP)`, or `CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)`.
  - **Stage 3 `/cross-model-review` — Autonomous Mode**: The Orchestrator routes findings by risk.
    - **Low risk**: every open finding is `Valid` against real non-`.md`/non-`shared-contracts/` source files with unambiguous file/line targets and zero escalation triggers (`CRITICAL_CONFLICT`, `Debatable`, `Not shown`, `False positive`, `trade-off`, architectural state transition, or `shared-contracts/` touch), or a Gate 4 failure is the first failure of that check. A Role 2.3 `review-fixer` runs `fast-track`, commits, runs **scoped tests only**, and advances to Round `N+1`.
    - **High risk**: any `Critical` finding, any escalation marker, or the same Gate 4 check failing twice in a row. A Role 2.1 `fix-planner` (read-only, edits no files) drafts the plan and classifies it against the five halt criteria, returning `plan_markdown` (Orchestrator writes and commits `fix_plan_round<N>.md`): `PLANNED` (no criterion touched) is applied by a Role 2.3 `review-fixer` in `apply-plan` mode; `ESCALATE` records `--pending-decision`, renders the Top 3 Highest-Risk Findings, and stops for Role 1.0. The Orchestrator no longer rules on plans.
    - After every fix, a fresh `gate4-verifier` reruns Gate 4 in full.
  - **Stage 3 `/cross-model-review` — Interactive Mode** (or any `Debatable` / `False positive` / halt trigger): Stop calling tools after presenting the verified triage table (`run_external_review.py triage`) and wait for explicit developer confirmation before fixing.
- **Halt criteria (the five)**: `CRITICAL_CONFLICT` (the solution contradicts the approved HLD or `Decisions Already Made`); `Debatable` / `Not shown` (the finding cannot be verified against live source); `SHARED_CONTRACT_CONFLICT` (touches `shared-contracts/`); `FIX_LOOP` (a location fixed in round N−1 fails again with `[INCOMPLETE_FIX]` or `[NEW_REGRESSION]`); `MAX_ROUNDS_CRITICAL_REMAINING` (a `Critical` finding survives round 3). A `fix-planner` plan touching any of them is `ESCALATE`.
- **Circuit Breakers**:
  - `CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)`: Any `Critical` or `Important` finding touching `shared-contracts/` or wire-level step/enum/payload contracts halts immediately; never auto-fix or revert approved HLD steps back to legacy contracts.
  - `CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)` & `CIRCUIT_BREAKER_HALT (FIX_LOOP)`: Halt immediately if `Critical` findings remain after Round 3 or if a file marked `fixed in <sha>` in Round `N-1` is flagged `Critical`/`Important` in Round `N`. If Round 3 finishes with `0 Critical` (only `Important`/`Minor`, no Fix Loop/contract conflict), run `AUTO_PASS_FINAL_SWEEP`, pass Gate 4 in full, and complete without a 4th round.

### 1.3 Intermediate Scoped Tests & Anti-Evasion Rules
- **Intermediate Rounds (Tier 1 Only)**: Run fast static checks (`ruff`, `mypy`, `lint-imports`, AST invariants) plus targeted pytest files covering modified modules (`uv run pytest <changed_test_files> -n auto --timeout=30 -q --tb=short`, or module-scoped runner for non-Python projects). Repo-wide `pytest`, `tests/e2e/` browser suites, and unfiltered `| tail` runs are forbidden until Final Convergence Gate (`Gate 4 in full`).
- **Zero-Tolerance Anti-Evasion**: Never delete a required dependency from `pyproject.toml` instead of running `uv lock`; never delete stale reports without regenerating them; never synthesize fake test data in place of immutable disk fixtures; always run `uv run playwright install chromium` after adding/upgrading `playwright`.

### 1.4 Per-Task Mechanical Verification vs. LLM Review, Blocker-Only Rubric & Two-Tier Risk Assessment Gate
- **Role Separation (Mechanical Test vs. LLM Review)**:
  - **Programmer (Role 2.3)**: Mandatory on **every task** to execute and pass the full mechanical `Verification` table (`RED -> GREEN -> REGRESSION -> TIER-B -> TIER-C`), covering module + *Downstream Callers* regression suites and `TIER-B` static checks across all `Allowed files` (production + tests, plus `lint-imports`/contract checks when cross-module imports or contracts change), and tick all `- [x]` checkboxes in `## Definition of Done` with brief mechanical result notes (e.g. `exit 0, 42 passed`). Transitioning frontmatter to `status: "done"` (or setting `completedAt`) is strictly forbidden while any `- [ ]` remains in `## Definition of Done`.
  - **LLM / Cross-Model Review (Role 2.1 `task-reviewer` & External Reviewers)**: Skipped on small, purely mechanical tasks (`review_tier` unset or `"skip"`, `<= 2` non-test modules, no high-risk labels) to prevent review bottlenecks; concentrated at semantic/architectural boundaries, high-risk tasks (`review_tier: "full"`, `security`, `architecture`, `concurrency`, `contract`, or `> 2` non-test modules), and epic-wide convergence at Gate 4 (`/cross-model-review`).
- **Hard Cap**: `max_task_review_passes = 2`, `max_fix_passes = 1` (resolved via `persona_config.py`, enforced by `manage_worker_pool.py` exit `2` and `lifecycle_runner.py`).
- **Blocker-Only Severity Rubric (`BLOCKER` vs. `NON_BLOCKING_OBSERVATION`)**:
  - **`BLOCKER`** (triggers `CHANGES_REQUESTED`): direct BDD/HLD/API contract breach (`BDD_VIOLATION`, `CONTRACT_SCHEMA_VIOLATION`), crash/unhandled error/failed gate (`RUNTIME_SAFETY`), or `Allowed files`/layer boundary breach (`OWNERSHIP_ARCHITECTURE_VIOLATION`).
  - **`NON_BLOCKING_OBSERVATION`** (MUST return `APPROVED`): minor non-BDD edge refinements, style nits, or micro-optimizations; recorded under `Observations (Non-Blocking)` / `"observations"` and persisted to `review_audit_notes.jsonl` without a fix pass. Empty `blockers` with `done_gate: "PASS"` is coerced to `APPROVED`.
- **Two-Tier Risk Assessment Gate (after Fix Pass 1)**:
  - **Tier 1 (`manage_worker_pool.py triage-fix`)**: Deterministic diff check over `pass1_tree_sha..curr_tree_sha`; returns `HIGH_RISK` (`bounded_diff: null`) on `> 30` non-test changed lines, sensitive surface edits, or weakened test assertions; otherwise `ELIGIBLE_FOR_SHORT_CIRCUIT` (`<= 30` non-test changed lines).
  - **Tier 2 (`Role 2.2` `RiskAssessment`)**: Single bounded Role 2.2 semantic ruling comparing `ELIGIBLE_FOR_SHORT_CIRCUIT` `bounded_diff` against `pass1_blockers`: `LOW` routes to `finalize-slot --mode tier2-short-circuit --risk-level LOW`; `MEDIUM`/`HIGH` (or Tier 1 `HIGH_RISK`) routes to Review Pass 2 Delta-Only (`--review-pass 2`, `DIRECT_REGRESSION` only), then `finalize-slot --mode pass2-complete` (logs residual remarks to `review_audit_notes.jsonl`, zero Fix Pass 2).

---

## 2. Multi-Repo Governance, Memory Checkpointing & IDE Window Signatures

### 2.1 Multi-Repo Symlink & Contract Triad Protocol
- Satellite repos where `shared-contracts/` is a symlink to a Hub repo must treat `shared-contracts/` as read-only in satellite git (`Files Allowed` must never list `shared-contracts/...`; never run `git -C <other_repo> commit` without developer confirmation).
- Always inspect the Contract Triad in `shared-contracts/<domain>/`: `api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`. Log `GAP-XX` / `RFC-XXX` entries instead of unilateral breaking payload/enum edits.
- Satellite workers remain stateless compute nodes (HTTP REST/SSE + worker auth tokens only; zero direct `DATABASE_URL` access).

### 2.2 Two-Tier Memory, Persona Models & Checkpoints
- Persona models resolve through `/d3nexus:dev-config` (`python3 scripts/dev_config.py resolve <persona> --format argv --mode <read-only|write>`); layers are kit defaults, `$REAL_HOME/.d3nexus/personas.json`, `.agents/config/personas.json`, then CLI flags. Role 2.3 defaults to `gemini-4-hydrogen-xhigh` (`xhigh`), Role 2.2 to Hydrogen `high`, Role 2.1 to Argon `high`. `.devtool/review_config.json` keeps only the external reviewer provider priority and `quota_thresholds`.
- Checkpoint human pauses before stopping: `python3 scripts/resume_context.py --state --status "Waiting for <Action>" --prompt "<Question>"`.
- Checkpoint autonomous phases: `python3 scripts/resume_context.py --state --status "In progress: <Phase>"` (`is_human_action_required: false`).
- Mandatory checkpoint events (`resume_context.py --checkpoint <event> --epic <slug> [--next "<step>"]`): `gate2_tasks_locked` (Role 2.1, right after Gate 2), `subagent_returned` and `wave_merged` (Role 2.2), `model_unavailable`, `turn_budget`, `low_quota_stop`, `quota_low`.
- Turn budget: `checkpoint_policy.max_orchestrator_turns_before_checkpoint` (default 8; halved by low-quota mode). Low-quota mode (`/d3nexus:dev-config low-quota on|off [--for <hours>]`, default 5 hours, stored per profile) keeps only structured outputs, skips optional work (`task-observer` logging, narrative Doc Sync prose), finishes the task or wave in flight, writes `low_quota_stop`, prints `--emit-prompt implement`, records `--pending-decision`, and stops. It never skips gates, `gate4-verifier`, required reviews, `/cross-model-review` rounds or halt criteria.
- Quota gate (`dev_config.py quota-check`, before Stage 3, each wave and each fix round): exit `2` writes `quota_low`, records a `quota` pending decision listing each persona's CLI, quota line and recovery commands, and stops; unreadable quota records `quota_unknown` and continues. Thresholds come from `quota_thresholds` only.
- Unavailable model: no automatic fallback, no retry; checkpoint `model_unavailable`, record `--pending-decision "<persona> model <alias> unavailable" --decision-kind blocker --epic <slug>` with the advisory fallback command, and stop.

### 2.3 Window Title & Persistent Bar Colors (`.vscode/settings.json`)
- **Title Format**: `"<ICON> [<REPO_NAME>] [@<account_id>] <Vietnamese Epic Name> - <Stage / Task>"` (`account_id` from `os.path.basename(os.environ["HOME"])` under `antigravity_homes/`; Vietnamese Epic Name as Role 1.0 gave it in chat or as already shown in the current `window.title`; never read it from a `.vi.md` mirror, and fall back to the epic slug when unknown).
- **Parity**: Keep `titleBar.inactiveBackground == titleBar.activeBackground` and `statusBar.inactiveBackground == statusBar.background`; leave `activityBar.background` default. Preserve existing developer `workbench.colorCustomizations`.
- **Repo Color Signatures**:
  - `[LYRICS-SYNC]`: `#7f1d1d` (Crimson Red)
  - `[D3NEXUS]`: `#065f46` (Emerald Green)
  - `[NEXUS]`: `#0d47a1` (Royal Blue)
  - `[AGENT-TOOLS]`: `#b45309` (Warm Amber)

---

## 3. Shell (`.zshrc`) & Multi-Profile OS Safety Checklist

1. **Backup & Syntax**: `cp ~/.zshrc ~/.zshrc.bak.$(date +%Y%m%d_%H%M%S)` before editing; verify `zsh -n ~/.zshrc` after; deduplicate functions/aliases before appending.
2. **Host Keychain Protection**: Never mutate `security default-keychain` or `security list-keychains -s` globally. Isolate profiles strictly via per-profile `~/antigravity_homes/<profile>/Library/Preferences/com.apple.security.plist` and subshell-scoped `security unlock-keychain -p <pass> <profile.keychain-db>`.
3. **Subshell Scope Only**: Never export `HOME=...`, `AGY_PROFILE=...`, or `TMPDIR=/tmp/ag_...` globally in `~/.zshrc`. Inside IDE terminals (`TERM_PROGRAM == "vscode"` and `-z "$AGY_CLI_MODE"`), keep `$HOME == $REAL_HOME`.
4. **Shared Host Toolchains**: Symlink Homebrew, Android SDK, Gradle, FVM, Flutter, Rust/Cargo, Go, Python/UV, npm, Docker socket, and Caches from `$REAL_HOME`.
5. **Launcher IPC Stripping (`ag_run`)**: `ag_run` removes the VS Code IPC variables (`ELECTRON_RUN_AS_NODE`, `VSCODE_GIT_IPC_HANDLE`, `VSCODE_IPC_HOOK_CLI`) with `env -u`, then sets the profile's own home, profile name and temp directory only inside its subshell before opening Antigravity. Launch `ag_run` and any `<profile>-cli` alias through `zsh -ic`, never from an agent runtime's own shell: `ag_run` deletes a profile's symlinks when its underscore helper functions are missing. Agents dispatch `agy` through `dev_config.py dispatch` and never build those variables themselves.
6. **Profile DB & Telemetry Isolation**: Never symlink `.gemini/antigravity` or `data/User/globalStorage/state.vscdb` across profiles; kill resident PIDs (`pkill -f antigravity_homes/<profile>`) before DB edits; keep `agy.onboarding.lastLoginUsername` matched to `<profile>.keychain-db`; purge `signedOut` OAuth flags, `comments`, `workspaceStorage`, and cross-profile `extensions.user.cache`; generate unique `telemetry.machineId` / `telemetry.devDeviceId` in `storage.json`; set `"telemetry.telemetryLevel": "off"`; never clone `conversation_summaries.db`. Full local protocol: `.agents/rules/profile_isolation_rules.md`.

---

## 4. Zero-Fluff Output Cap Scope

- **Trim**: Discretionary preamble, step-by-step narration, redundant restatements of already-read files, and conversational padding in subagent/worker outputs.
- **Always Preserve**: Machine Verdicts (`PASS`/`FAIL`/`BLOCKED`, `🟢 LGTM`/`🟡 CONCERNS`/`🔴 BLOCKED`), severity-tiered Findings tables, JSON/provider gate results (`run_external_review.py`, `run_task_checks.py`), worker status contracts, and human Gate decision prompts.

---

## 5. Test Efficiency, Anti-Test-Bloat & Tiered Execution Protocol

### 5.1 Anti-Test-Bloat Rules (When Writing Tests in Gate 3)
- **Mandatory Parametrization**: Never write multiple copy-pasted `def test_*` functions that test the same logic branch with different inputs. Always consolidate variations into a single `@pytest.mark.parametrize` (or table-driven) test.
- **No Trivial Boilerplate Tests**: Do NOT write tests that merely assert Python language features, Pydantic default field values, or trivial getters/setters without business logic. Every test must verify a distinct behavioral contract or edge case from the Spec/HLD.
- **Fixture Scope Discipline**: Any read-only fixture (loading JSON snapshots, parsing ASTs, spinning up mock servers or headless browsers) MUST use `scope="module"` or `scope="session"` — never `scope="function"`.

### 5.2 Tiered Test Execution Protocol (When Running Tests)
- **Tier 1 — Task Implementation & Intermediate Review Fix Rounds**:
  - Run ONLY static checks (`ruff`, `mypy`, `lint-imports`) + explicitly scoped test files in parallel:
    `uv run pytest <changed_test_files> -n auto --timeout=30 -q --tb=short`
  - **NEVER** run `tests/e2e` or unfiltered repo-wide `pytest` during intermediate steps.
- **Tier 2 — Pre-Review / Pre-Gate Fast Regression**:
  - Run unit + integration tests in parallel across CPU cores, excluding `tests/e2e`:
    `uv run pytest --ignore=tests/e2e -m "not slow and not acceptance and not live_llm" -n auto --dist loadscope --timeout=30 -q --tb=short`
- **Tier 3 — Final Gate Convergence Only (Run Exactly Once per Epic)**:
  - Run Tier 2 + the session-scoped `tests/e2e` Playwright suite + `audit_epic.py` / `quality_check`.

---

## 6. Detail Relocated from CRITICAL_RULES.md

Text removed from [CRITICAL_RULES.md](../../../rules/CRITICAL_RULES.md) to keep it under its 8192-byte cap, kept here verbatim. In `CRITICAL_RULES.md`, Rules 6, 8.6, and 9 link to this file; Rules 2, 5.1, 8.3, 8.5, and 10 keep the mandate inline without a link, while their trimmed wording and lists remain here (and in sections 1, 2, and 4).

- **Rule 2 (Commit Message Format)**: Omit the body when the commit does one thing; otherwise pass two `-m` flags.
- **Rule 5.1 (Option 1)**: Stage 3 stays in this session, so Role 2.2 runs on its model (the prompt names the `orchestrator` binding).
- **Rule 5.1 (provider priority)**: `Claude -> Codex -> Kiro -> Argon`, ordered by `.devtool/review_config.json` as described in section 1.1.
- **Rule 8.3 (model unavailable)**: Model unavailable (CLI, auth, quota): no fallback, no retry; checkpoint, `--pending-decision` with the fallback command, stop.
- **Rule 8.5 (turn budget, low-quota & quota gate)**: Tool calls between checkpoints are capped by `checkpoint_policy.max_orchestrator_turns_before_checkpoint` (default 8). `/d3nexus:dev-config low-quota on` halves it, finishes the wave in flight, checkpoints `low_quota_stop`, records `--pending-decision`, stops. `dev_config.py quota-check` runs before Stage 3, each wave and each fix round: exit `2` checkpoints `quota_low`, records a `quota` pending decision, stops.
- **Rule 8.6 (Choice A & English SSOT)**: Record Choice A pauses (`--pending-decision`, cleared on `--gate`/non-paused `--state`/`--revise`), creator PIC (`--detect-profile`), and English-only internal docs/code/commits (`docs, reports, code, commits`); `--complete` at Stage 4; sync `window.title` per section 2.3.
- **Rule 10 (Zero-Fluff Output Cap)**: machine Verdicts (`PASS`/`FAIL`/`BLOCKED`, `🟢 LGTM`/`🟡 CONCERNS`/`🔴 BLOCKED`), Findings tables, JSON/provider gate results (`run_external_review.py`, `run_task_checks.py`), worker status contracts, or human Gate prompts (the full list is in section 4).

---

## 7. English SSOT and Vietnamese Mirror Isolation

Extended checklist for [CRITICAL_RULES.md](../../../rules/CRITICAL_RULES.md) rule 8.6 and rule 11.

- **English is the single source of truth.** Every persisted dev-lifecycle artefact is English-only: specs, HLDs, BDD scenarios, task files and their Verification tables, non-epic plans, `handoff.md`, review and fix-plan files, execution and Gate 5 reports, code comments, and commit messages.
- **Chat language.** Chat with Role 1.0 may use Vietnamese. A Vietnamese explanation or mirror is produced only when Role 1.0 asks for it.
- **New artefact names.** `YYYY-MM-DD-<topic>-design.md`, `<epic_dir>.md`, `bdd_scenarios.md` and `docs/superpowers/plans/YYYY-MM-DD-<feature>.md`. Legacy `<stem>.en.md` files are accepted, not produced.
- **Mirror isolation.** A `.vi.md` file is a mirror, not SSOT. Agents never open, grep, glob or list it; searches over epic or doc directories exclude `*.vi.md`; subagent briefs and review bundles never name it. The only exceptions are a file Role 1.0 names explicitly and writing the `.vi.md` variant of a doc-lifecycle document.
- **Stays bilingual.** The doc-lifecycle skills and the kit guides under `docs/`.

---

## 8. Authoring Standards from the dev-lifecycle Skill

Text moved verbatim from [SKILL.md](../SKILL.md) to keep it within its 2500-word cap.

### Markdown Quality Standards
Enforce heading hierarchy, valid code block tags, resolving links, no trailing whitespace, and quoted flowchart labels in human docs.

### Epic Dependencies
Declare `- **Depends on epic**: <epic_slug_or_dir>[, ...]` in HLD Meta Data when an epic depends on others.
