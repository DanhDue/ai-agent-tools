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
  - **Stage 2 `/principal-review` (BOTH Interactive Mode and Autonomous `/dev-lifecycle` Mode)**: Run `run_external_review.py triage --kind principal --epic-dir <epic_dir>` and verify every finding against source + approved Spec/HLD before editing any document. Present `## Auto-Triage Gate`, `## Top 3 Highest-Risk Findings`, and `## Findings`. When all blocking findings verify `Valid` (or objective `False positive` with exact proof) and zero halt triggers apply, apply Role 2.2 design revisions, commit revisions + decisions (`fixed in <sha>`), run scoped `check_epic_readiness.py <epic_dir>` (do NOT package `handoff.md` prematurely), and advance to Round `N+1`. Stop immediately on `CRITICAL_CONFLICT`, `Debatable`/`Not shown`, `CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)`, `CIRCUIT_BREAKER_HALT (FIX_LOOP)`, or `CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)`.
  - **Stage 3 `/cross-model-review` — Autonomous Mode**: When all blocking findings verify `Valid` against real non-`.md`/non-`shared-contracts/` source files with unambiguous file/line targets and zero escalation triggers (`CRITICAL_CONFLICT`, `Debatable`, `Not shown`, `False positive`, `trade-off`, architectural state transition, or `shared-contracts/` touch), Role 2.3 fast-tracks fixes via `_apply_code_fixes`, commits, runs **scoped tests only**, and advances to Round `N+1`. Whenever any finding involves contract/architecture ambiguity or escalation markers, Role 2.3 drafts `fix_plan_round<N>.md` for Role 2.2 evaluation (`APPROVED`, `ADJUSTED`, `CRITICAL_CONFLICT`) before editing; halt immediately on `CRITICAL_CONFLICT` or `SHARED_CONTRACT_CONFLICT`.
  - **Stage 3 `/cross-model-review` — Interactive Mode** (or any `Debatable` / `False positive` / halt trigger): Stop calling tools after presenting the verified triage table (`run_external_review.py triage`) and wait for explicit developer confirmation before fixing.
- **Circuit Breakers**:
  - `CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)`: Any `Critical` or `Important` finding touching `shared-contracts/` or wire-level step/enum/payload contracts halts immediately; never auto-fix or revert approved HLD steps back to legacy contracts.
  - `CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)` & `CIRCUIT_BREAKER_HALT (FIX_LOOP)`: Halt immediately if `Critical` findings remain after Round 3 or if a file marked `fixed in <sha>` in Round `N-1` is flagged `Critical`/`Important` in Round `N`. If Round 3 finishes with `0 Critical` (only `Important`/`Minor`, no Fix Loop/contract conflict), run `AUTO_PASS_FINAL_SWEEP`, pass Gate 4 in full, and complete without a 4th round.

### 1.3 Intermediate Scoped Tests & Anti-Evasion Rules
- **Intermediate Rounds (Tier 1 Only)**: Run fast static checks (`ruff`, `mypy`, `lint-imports`, AST invariants) plus targeted pytest files covering modified modules (`uv run pytest <changed_test_files> -n auto --timeout=30 -q --tb=short`, or module-scoped runner for non-Python projects). Repo-wide `pytest`, `tests/e2e/` browser suites, and unfiltered `| tail` runs are forbidden until Final Convergence Gate (`Gate 4 in full`).
- **Zero-Tolerance Anti-Evasion**: Never delete a required dependency from `pyproject.toml` instead of running `uv lock`; never delete stale reports without regenerating them; never synthesize fake test data in place of immutable disk fixtures; always run `uv run playwright install chromium` after adding/upgrading `playwright`.

---

## 2. Multi-Repo Governance, Memory Checkpointing & IDE Window Signatures

### 2.1 Multi-Repo Symlink & Contract Triad Protocol
- Satellite repos where `shared-contracts/` is a symlink to a Hub repo must treat `shared-contracts/` as read-only in satellite git (`Files Allowed` must never list `shared-contracts/...`; never run `git -C <other_repo> commit` without developer confirmation).
- Always inspect the Contract Triad in `shared-contracts/<domain>/`: `api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`. Log `GAP-XX` / `RFC-XXX` entries instead of unilateral breaking payload/enum edits.
- Satellite workers remain stateless compute nodes (HTTP REST/SSE + worker auth tokens only; zero direct `DATABASE_URL` access).

### 2.2 Two-Tier Memory Checkpoints & Role 2.3 Config Default
- Role 2.3 (AI Programmer) resolves its model dynamically from `.devtool/review_config.json["providers"]["programmer"]` (default `gemini-4-hydrogen-xhigh`, `--effort xhigh --mode auto`).
- Checkpoint human pauses before stopping: `python3 scripts/resume_context.py --state --status "Waiting for <Action>" --prompt "<Question>"`.
- Checkpoint autonomous phases: `python3 scripts/resume_context.py --state --status "In progress: <Phase>"` (`is_human_action_required: false`).

### 2.3 Window Title & Persistent Bar Colors (`.vscode/settings.json`)
- **Title Format**: `"<ICON> [<REPO_NAME>] [@<account_id>] <Vietnamese Epic Name> - <Stage / Task>"` (`account_id` from `os.path.basename(os.environ["HOME"])` under `antigravity_homes/`; Vietnamese Epic Name from H1 of `<epic_slug>.vi.md` stripping `# Epic:`).
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
5. **Launcher IPC Stripping (`ag_run`)**:
   ```bash
   env -u ELECTRON_RUN_AS_NODE -u VSCODE_GIT_IPC_HANDLE -u VSCODE_IPC_HOOK_CLI \
     HOME="$ag_home" AGY_PROFILE="$profile" TMPDIR="/tmp/ag_$profile" open -n -a "Antigravity IDE" ...
   ```
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
