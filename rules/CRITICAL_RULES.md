---
trigger: always_on
---

# Critical Rules

> [!CRITICAL]
> These rules are MANDATORY and MUST be strictly applied by ALL AI Agent Plugins, runtimes, orchestrators, and subagents (including Claude Code, Antigravity IDE, Cursor, Codex, Windsurf, OpenCode, and any custom/third-party plugins) in every interaction across this project and downstream repositories. Failure to follow these rules is a direct violation of the engineering standard.

## Universal Scope & Plugin Applicability

> [!IMPORTANT]
> **Every AI Agent plugin operating in this environment MUST inherit and execute these rules.**
> Regardless of which plugin, tool, extension, or agent framework initiated the session:
> - Built-in or third-party plugins must NEVER override, circumvent, or weaken these rules.
> - Subagents, background runners, and multi-agent teams spawned by any plugin inherit these exact constraints.
> - If an AI agent or plugin has conflicting built-in behaviors (e.g. auto-pushing, autonomous planning artifacts, skipping human checkpoints), these Critical Rules take absolute precedence.

## 1. Mandatory Quality Gates

> [!IMPORTANT]
> After completing any workflow or skill — regardless of which plugin or tool executed it — you **MUST** run the quality gate for the **kind of work you did**, and fix any issues it raises. This is critical to maintain the quality of the project.
>
> | Kind of work | Gate |
> |---|---|
> | Anything that changes a file shipping in the build | `@quality_check` |
> | Anything whose deliverable is prose | `@doc_quality_check` |
>
> The two share no tier, no audit and no tooling. Running the wrong one produces a green light that means nothing — and `@doc_quality_check` refuses outright if the change touches shipped files.
>
> See: [Quality Check Skill](../skills/quality_check/SKILL.md) · [Document Quality Check Skill](../skills/doc_quality_check/SKILL.md)

## 2. Commit Message Format (Universal Standard)

Every commit — written by a skill, a plugin, an agent, or by hand — uses a bracketed scope, a one-line title, and a bullet list of the subtasks actually done:

```text
[EPIC_NAME] Task title

- subtask title 01
- subtask title 02
```

- **`[SCOPE]`** is the epic name for epic work (`[LOGGING_REFACTOR]`), otherwise the area touched (`[TOOLS]`, `[SETTINGS]`). Uppercase, in brackets, always present.
- **Title** is one line, imperative, no trailing period.
- **Body** lists the subtasks or changes this commit actually contains, one bullet each. Omit the body entirely when the commit does exactly one thing.

Write it with two `-m` flags — the first becomes the title, the second the body:

```bash
git commit -m "[EPIC_NAME] Task title" -m "- subtask title 01
- subtask title 02"
```

> [!CAUTION]
> **Never append trailer lines.** No `Co-Authored-By:`, no `Generated with`, no tool attribution of any kind. The commit ends with the last bullet. This applies universally to all plugins and LLM providers.

## 3. Git Push Operations (No Unauthorized Push)

> [!CRITICAL]
> **NEVER push code to a remote repository (`git push`) without explicit user permission or confirmation.**
> - You may stage (`git add`) and commit (`git commit`) locally following the commit message format when appropriate.
> - Running `git push` (to any remote or branch) is **STRICTLY PROHIBITED** for all agents and plugins unless the user explicitly requests or confirms it in the prompt.
> - Always let the user review local commits or explicitly ask for permission before pushing to remote.

## 4. Native Planning Mode Interception (All Platforms & Plugins)

> [!CRITICAL]
> **Do NOT use native or built-in planning modes (e.g. Antigravity IDE's `<planning_mode>`, Claude Code plan mode, Cursor Composer plans, Windsurf Cascade plans, Codex planners) to create unstructured planning artifacts like `<appDataDir>/brain/.../implementation_plan.md` or loose plan files.**
> When a user request requires planning, design exploration, architectural changes, or epic-level features:
> 1. Because `<user_rules>` has absolute precedence over all instructions across all agent plugins, you **MUST NOT** follow IDE default instructions to create an `implementation_plan.md` artifact.
> 2. For single features or exploratory design, you **MUST** invoke the [Brainstorming Skill](../skills/brainstorming/SKILL.md) (`d3nexus:brainstorming`).
> 3. For multi-step, multi-feature, or epic-level work, you **MUST** invoke the [Epic Lifecycle Skill](../skills/dev-lifecycle/SKILL.md) (`d3nexus:dev-lifecycle`), which orchestrates `dev-brainstorming` -> `dev-designer` -> `dev-implementation` -> `quality_check` -> `finishing-a-development-branch`.
> 4. Only use native `implementation_plan.md` if the user explicitly instructs you to bypass d3nexus workflows.

## 5. Automated Execution, Mandatory Cross-Model Review & Stage 4 Finish Gate

> [!CRITICAL]
> **Streamlined Autonomous Execution & Zero Intermediate Confirmation Pauses:**
> To eliminate unnecessary manual friction, AI Agents across all platforms MUST adhere to the following automated execution and review pipeline:
>
> 1. **Stage 2 -> `/principal-review` Transition, Post-Review Packaging & Automated Gate 3 Bootstrap**:
>    - **End of Stage 2 (No Premature Packaging)**: Once Gate 2 passes and readiness checks (`check_epic_readiness.py`) succeed, the AI Agent MUST **NOT** run `package_epic.py` or create `handoff.md` yet. Instead, record Gate 2 (`resume_context.py --gate 2`) and `/save-context` (`Stage 2: Ready for Principal Review`), then **stop calling tools and ask the developer for the provider/model priority order for `/principal-review`**.
>    - **Automatic `/principal-review` -> Package/Handoff -> Launch Prompt**: Once the developer confirms the provider/model priority order, the AI Agent MUST **automatically invoke `/principal-review`** and run its convergence funnel. **Only at the end of `/principal-review`** (after PASS / convergence and any final sweep commits) does the agent run `package_epic.py <epic_dir>` (`--revise --reason "<text>"` only if `handoff.md` already exists) to create/anchor `handoff.md`, commit `[<EPIC_NAME>] Package epic for handoff` (if `auto_commit: true`), run `/save-context`, **print the AI Programmer implementation prompt (`resume_context.py --emit-prompt implement`)**, and ask a 2-option choice: **Triển khai (tự động)** vs **Dừng lại** (*"Dừng lại ở đây để tôi lấy prompt cho một AI Agents khác triển khai"*).
>    - **Automated Gate 3 & Worktree Bootstrap (No Execution Order Confirmation Pause)**: If the developer selects **Triển khai (tự động)** (or when resuming Stage 3 / running hands-off autonomous mode), the AI Agent proceeds automatically into `d3nexus:dev-implementation`, computes task execution order via `compute_execution_order.py`, creates/bootstraps the isolated Git worktree, records Gate 3 (`resume_context.py --gate 3`), and invokes Role 2.3 (AI Programmer) to begin TDD. If the developer chooses **Dừng lại** (or declines implementation), the agent **MUST STOP** cleanly without invoking `dev-implementation`.
>    - AI Agents **MUST NOT stop or prompt the developer for manual confirmation** on task execution order or worktree creation once implementation begins. Manual confirmation at Gate 3 is eliminated; halt occurs ONLY on fatal errors (cyclic DAG dependency, malformed task frontmatter, or unresolvable blocking prerequisites).
>
> 2. **Automated Transition to Cross-Model Review (No Intermediate Review Choice Prompt)**:
>    - When all tasks of an epic are implemented and Phase 4 / Gate 4 local machine verification returns PASS (after Gate 4 passes, Cross-model review must return to a full Gate 4 run), the AI Agent **MUST NOT pause to ask the developer for an intermediate Review Choice** (e.g. Finish vs Cross-model review).
>    - The workflow **AUTOMATICALLY transitions into `/cross-model-review`** using the provider priority and model configured in `.devtool/review_config.json` (running `run_external_review.py run --epic-dir <epic_dir> --auto-quota`).
>    - Cross-model review executes its 3-round convergence funnel and severity-tiered auto-triage gate (`AUTO_PASS_CLEAN`, `AUTO_PASS_FINAL_MINOR_SWEEP`, `AUTO_FIX_ELIGIBLE`) automatically.
>
> 3. **Stage 4 Finish Decision & Gate 5 Sign-off (Human Decision Point)**:
>    - The decision to "Finish" belongs strictly to **Stage 4 (`finishing-a-development-branch`)**.
>    - Only after `/cross-model-review` has converged, all findings are resolved, Gate 4 PASS is re-verified on the latest candidate SHA, and the synthesized Executive Report (Top 3 Highest-Risk Findings across all review rounds) is rendered, the AI Agent **MUST explicitly stop calling tools** and prompt the Human Architect for the **Stage 4 Finish Decision** (Gate 5 Sign-off) and Git merge strategy selection (`Squash`, `--no-ff`, or `Rebase`).
>    - The AI Agent **MUST NOT** auto-finish, auto-merge, or auto-push to remote without explicit developer confirmation.

## 6. Severity-Tiered Auto-Triage Gate, 3-Round Convergence Funnel & Post-Gate Checkpoints

> [!CRITICAL]
> **Every external review invocation (`/principal-review` and `/cross-model-review`) enforces the 3-Round Scope-Narrowing Convergence Funnel (`max_rounds = 3`), `check-quota` Provider Priority (`Claude -> Codex -> Kiro -> Argon`), and the Severity-Tiered Auto-Triage Gate.**
>
> 1. **Quota-Aware Provider Priority & 3-Round Convergence Funnel**:
>    - **Provider Priority (`Claude -> Codex -> Kiro -> Argon`)**: Evaluations follow `["claude", "codex", "kiro", "agy"]` using `check-quota` thresholds: Claude & Codex require `5H >= 15%` AND `7D > 2%`; Kiro requires `Monthly Credits >= 3%` (`>= 15 credits`); Argon (`agy`) requires `Weekly >= 10%` or `5H >= 15%`.
>    - **Max 3 Rounds**: Reviews are capped at `3` rounds (`Round 1`: Full Scope Audit; `Round 2`: Delta Verification of `prev_sha..curr_sha` with no new Minor on untouched files; `Round 3`: Blocker-Only Convergence Mode).
> 2. **Severity-Tiered Auto-Triage Gate & Automatic Local Quality Gate Re-run**:
>    - **`AUTO_PASS_CLEAN` (`0 findings`)** or **`AUTO_PASS_FINAL_MINOR_SWEEP` (`0 Critical`, `0 Important`, only `Minor` findings)**: Verify findings against live source and approved Spec/HLD first (halting only on `CRITICAL_CONFLICT`, `Debatable` trade-off choices, or `CIRCUIT_BREAKER_HALT`). Otherwise, fix valid `Minor` items in a single sweep (commit revisions + decisions), verify the local quality gate (`check_epic_readiness.py` + `package_epic.py` [or `--revise` when `handoff.md` already exists] at completion of Stage 2 `/principal-review`; full Gate 4 in Stage 3), and **complete the review stage immediately without re-invoking the external reviewer**. At the end of Stage 2 `/principal-review`, print `--emit-prompt implement` and ask **Triển khai (tự động)** vs **Dừng lại**.
>    - **`AUTO_FIX_ELIGIBLE` (Round 1..2 with `Critical`/`Important` findings and no Fix Loop)**:
>      - In **Stage 2 `/principal-review` (BOTH Interactive Mode and Autonomous `/dev-lifecycle` Mode)**: The agent MUST first run `run_external_review.py triage --kind principal --epic-dir <epic_dir>` and verify every finding against live source code and the approved Spec/HLD (`Decisions Already Made`) BEFORE editing any document. Present the verified triage summary (`## Auto-Triage Gate`, `## Top 3 Highest-Risk Findings`, `## Findings`), and **when all blocking findings verify as `Valid` (plus any objective `False positive` refuted with exact source/approved-Spec proof) and zero halt triggers apply, do NOT pause for interactive confirmation**: automatically apply the design revisions in Role 2.2, commit revisions and decisions (`fixed in <sha>`), verify `check_epic_readiness.py <epic_dir>` (without premature `handoff.md` packaging), and immediately advance to Round `N+1` (up to max 3 rounds). **Stop calling tools and escalate to the Human Architect ONLY when hitting**: (1) `CRITICAL_CONFLICT` (conflict with business/domain requirements, critical risks, or frozen Tier-1 Spec/`Decisions Already Made`), (2) a `Debatable` finding requiring a trade-off choice (or an unresolvable `Not shown` claim), (3) `CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)`, (4) `CIRCUIT_BREAKER_HALT (FIX_LOOP)`, or (5) `CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)`. Only after `/principal-review` converges does Stage 2 execute `package_epic.py`, print `--emit-prompt implement`, and ask **Triển khai (tự động)** vs **Dừng lại**.
>      - In **Stage 3 `/cross-model-review` — Autonomous `/dev-lifecycle` Mode**: When all blocking findings verify as `Valid` in source code and do not require unapproved changes to `shared-contracts/`, Role 2.3 drafts `fix_plan_round<N>.md` evaluated by Role 2.2 (`APPROVED`, `ADJUSTED`, `CRITICAL_CONFLICT`), applies the fixes, commits them, records decisions, runs **Phase 4 / Gate 4 in full**, and invokes the next convergence round (`Round N+1`, up to max 3 rounds). If `CRITICAL_CONFLICT` or `SHARED_CONTRACT_CONFLICT` is detected, halt immediately for the Human Architect.
>      - In **Stage 3 `/cross-model-review` — Interactive Mode** (or whenever any Stage 3 finding is `Debatable` / `False Positive` or hits a Halt Trigger): The agent **MUST STOP CALLING TOOLS** after presenting the verified triage table (`run_external_review.py triage`) and wait for explicit developer confirmation on the findings. Once confirmed, Role 2.3 applies the fixes, commits them, runs **Phase 4 / Gate 4 in full** without asking for an intermediate confirmation, and returns to the cross-model/Gate 4 loop.
>    - **`CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)` (Mandatory Immediate Stop on `shared-contracts/` Conflicts)**:
     - If ANY `Critical` or `Important` finding in `/principal-review` or `/cross-model-review` directly impacts or conflicts with `shared-contracts/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`, `contract_sync.json`, or wire-level step/enum/payload contracts — e.g. HLD defines 5 new steps while `shared-contracts/` still holds 7 legacy steps), the AI Agent **MUST IMMEDIATELY STOP CALLING TOOLS AND REPORT TO THE DEVELOPER**.
     - The AI Agent is **STRICTLY PROHIBITED** from auto-fixing `shared-contracts/` conflicts, **STRICTLY PROHIBITED** from proposing or applying a revert of the user's approved HLD/Spec design back to legacy contract steps, and **STRICTLY PROHIBITED** from continuing autonomous execution until the Human Architect explicitly confirms the contract alignment decision.
   - **`CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)` & `CIRCUIT_BREAKER_HALT (FIX_LOOP)`**:
     - If after **3 review rounds (`Round >= 3`) any `Critical` finding still remains**, OR if a **Fix Loop** occurs (the same file marked `fixed in <sha>` in Round $N-1$ is re-reported with a `Critical`/`Important` finding in Round $N$), the AI Agent **MUST IMMEDIATELY STOP CALLING TOOLS**, present the `## Top 3 Highest-Risk Findings (Executive Report)` and triage table, and escalate to the Human Architect (never auto-continue to implementation or branch finishing when a `Critical` finding survives 3 rounds).
     - Conversely, if Round 3 finishes with **`0 Critical` findings** (and no `shared-contracts/` conflict or Fix Loop, only remaining `Important`/`Minor` findings), `AUTO_PASS_FINAL_SWEEP` applies one final fix pass anchored to the approved design, runs the local quality gate green, and completes the stage without invoking a 4th review round.

## 7. Multi-Repo Boundaries, Symlink Isolation & Contract Governance

> [!CRITICAL]
> **AI Agents MUST strictly respect repository boundaries, symbolic link isolation, and contract-first governance across multi-repo ecosystems (Hub and Satellite repositories).**
>
> 1. **Multi-Repo Git Boundary Isolation**:
>    - An AI Agent running in any repository MUST NOT stage (`git add`) or commit (`git commit`) files residing outside the current git working tree.
>    - In a Satellite repository where `shared-contracts/` is a symbolic link pointing to a Hub repository (e.g. `lyrics-sync` or `nexus` linking to `D3Nexus`):
>      - Agents MUST treat `shared-contracts/` as **strictly read-only** for git tracking within the satellite workspace.
>      - Agents **MUST NOT** include `shared-contracts/...` in `Files Allowed` for local git tasks (preventing `fatal: pathspec is beyond a symbolic link`).
>      - Agents **MUST NOT** autonomously execute git commit commands in adjacent repositories (e.g. `git -C <target_repo>`) without explicit developer confirmation.
>
> 2. **Contract-First Triad & Canonical SSOT**:
>    - The Hub repository containing the physical `shared-contracts/` directory is the sole canonical authority (Single Source of Truth) for contract commits.
>    - Before modifying endpoints, database models, worker bridges, offline sync logic, or DTOs, agents MUST inspect the 3 canonical contract files in the relevant domain folder (`shared-contracts/<domain>/`):
>      1. `api_contract.md`: Endpoints, wire format, headers, telemetry, and payload schemas.
>      2. `architecture_and_flow.md`: Pipeline states, state machines, lifecycle fencing, and failure handling.
>      3. `gaps_and_rfcs.md`: Asynchronous change proposals, gap ledger, and cross-repo alignments.
>
> 3. **No Unilateral Breaking Changes & Non-Breaking Schema Guarantee**:
>    - Never rename API fields, mutate JSON request/response structures, or alter pipeline state enums in backend or client implementations without prior documentation and alignment in `shared-contracts/`.
>    - All schema and payload modifications MUST guarantee backward compatibility across all consumers (optional fields with safe defaults, non-breaking enum additions). Breaking changes without backward-compatible transition windows or fallback shims are strictly forbidden.
>
> 4. **Asynchronous RFC Workflow (Gaps & RFCs Ledger)**:
>    - If an agent in a satellite repo detects a payload mismatch, missing field, or new requirement, it **MUST NOT** invent ad-hoc fields or silently diverge.
>    - The agent MUST log a formal `GAP-XX` or `RFC-XXX` entry in `gaps_and_rfcs.md` (or emit an Upstream Contract Handoff Summary via `d3nexus:dev-designer`) and wait for upstream alignment before implementing breaking changes.
>
> 5. **Stateless Compute & Architectural Isolation**:
>    - Satellite worker nodes (e.g. `lyrics-sync`) must act strictly as stateless compute nodes. Direct connection to the control plane database (`DATABASE_URL`, PostgreSQL/SQLite) is **STRICTLY FORBIDDEN**. All state transitions, lease acquisitions, and result deliveries occur strictly via documented HTTP REST/SSE endpoints using worker authentication tokens.

## 8. Mandatory Two-Tier Project Memory & Tri-Role Persona Discipline

> [!CRITICAL]
> **AI Agents MUST strictly preserve Two-Tier Project Memory across session rotations and respect Tri-Role Persona boundaries across all stages of development.**
>
> 1. **Mandatory Context Restoration on Session Startup (Scoped to Development Lifecycle)**:
>    - When starting substantive feature engineering, architectural design, or task execution in the development lifecycle (`d3nexus:dev-lifecycle`, `dev-brainstorming`, `dev-designer`, `dev-implementation`) or after an account profile switch for development, the AI Agent MUST run `python3 scripts/resume_context.py` (or the `d3nexus:resume-context` skill) to restore architectural memory before answering or proposing solutions.
>    - The agent MUST summarize the restored project context in 5–10 concise bullets for the developer.
>    - **Zero-Context & Fast-Execution Exemption**: Routine operational prompts, standalone utility skills, and fast-execution commands — specifically `/refresh-session` (pinging quota windows), `/setup_keybindings`, git status/diff inspections, or quick standalone queries — **MUST NOT** invoke `resume_context.py` or `resume-context`. They must execute their requested actions immediately without loading repository context.
>    - **No Redundant Invocation**: Within an already-resumed active working session, the AI Agent MUST NOT repeatedly re-invoke `resume-context` on normal conversation turns.
>
> 2. **Strict Tri-Role Persona Discipline**:
>    - **Role 2.1 — Human Architect (Developer)**: Sole authority for system strategy, Gate approvals (Gate 1, 2, 5), triage escalations, and Stage 4 Finish decisions. Task execution order (Gate 3), local Gate 4 runs, and transition to Cross-Model Review are automated by default without manual confirmation pauses. In autonomous mode, halted strictly on critical risks, business/contract conflicts, or final merge sign-off.
>    - **Role 2.2 — AI Assistant (`[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]`)**:
>      - Activated for architectural analysis, problem statement exploration, design specifications (`d3nexus:dev-brainstorming`, `d3nexus:dev-designer`), Principal Review (`d3nexus:principal-review`), Cross-Model Review (`d3nexus:cross-model-review`), and fix plan evaluation.
>      - Dynamically inherits developer's selected model (Argon, Claude, Codex) or CLI override `--assistant-model`.
>      - **STRICT PROHIBITION**: The AI Assistant is **STRICTLY PROHIBITED from modifying production source code or application test suites**. Only architectural documentation (`docs/`, `.devtool/`, `shared-contracts/`) may be edited.
>    - **Role 2.3 — AI Programmer (`[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]`)**:
>      - Activated for `/dev-implementation` and task execution inside isolated git worktrees. Defaults to Model **Gemini Flash 3.8** (`--effort high --mode auto`).
>      - **STRICT BOUNDARIES**: Bound strictly to approved specifications, `Decisions Already Made`, and `Allowed files`. Must practice strict TDD (Red-Green-Refactor) and Clean Code standards. Zero test fakery.
>
> 3. **Deterministic State & Log Checkpointing**:
>    - After completing each Kanban task, the AI Programmer MUST log programmer activity (`scripts/resume_context.py --log`) and update Tier 2 snapshot state (`scripts/resume_context.py --state`).
>    - Upon feature completion in Stage 4 (`/finish`), the agent MUST run `scripts/resume_context.py --complete <epic_slug> "<milestone_summary>"` to record the permanent milestone in `.devtool/PROJECT_LEDGER.md` and archive the completed epic's Tier 2 files into `.devtool/archive/`.
>
> 4. **Mandatory Window Title Synchronization & Persistent Top/Bottom Bar Customization**:
>    - To eliminate cross-project window confusion when developers operate multiple IDEs or profile accounts, AI Agents MUST synchronize `window.title` and ensure persistent top/bottom bar colors in `.vscode/settings.json` upon entering an epic, transitioning lifecycle stages, or completing tasks.
>    - **Title Format**: `"<ICON> [<REPO_NAME>] [@<account_id>] <Vietnamese Epic Name> - <Stage / Task>"`.
>    - The `<account_id>` is extracted from the active profile / home environment (`os.path.basename(os.environ["HOME"])` under `antigravity_homes/`, e.g. `[@danhdue]`, `[@tess]`).
>    - The Vietnamese Epic Name MUST be extracted directly from the H1 header of `.devtool/epic/<epic_slug>/<epic_slug>.vi.md` (stripping the `# Epic:` prefix).
>    - **Persistent Inactive Bar Parity**: Both `titleBar` and `statusBar` MUST configure matching inactive background colors (`titleBar.inactiveBackground = titleBar.activeBackground` and `statusBar.inactiveBackground = statusBar.background`) to eliminate IDE dimming when windows lose focus.
>    - **Clean Activity Toolbar**: The left `activityBar.background` remains uncolored in default dark theme to avoid peripheral visual clutter.
>    - **Repository Color Signatures**:
>      - 🔴 `[LYRICS-SYNC]`: `#7f1d1d` (Crimson Red)
>      - 🟢 `[D3NEXUS]`: `#065f46` (Emerald Green)
>      - 🔵 `[NEXUS]`: `#0d47a1` (Royal Blue)
>      - 🟠 `[AGENT-TOOLS]`: `#b45309` (Warm Amber)
>    - Agents MUST preserve all existing `workbench.colorCustomizations` and developer configurations in `.vscode/settings.json`.

## 9. Shell Configuration (`.zshrc`) & Multi-Profile OS Boundary Safety

> [!CRITICAL]
> **Modifications to `~/.zshrc` or shell startup scripts MUST strictly follow Multi-Profile OS Safety rules to prevent breaking host OS system services (AirDrop, Apple ID, WiFi, Docker, Keychain) and profile isolation.**
>
> 1. **Mandatory Pre-Modification Backup & Syntax Verification**:
>    - Before applying ANY edits to `~/.zshrc`, agents MUST create a timestamped backup: `cp ~/.zshrc ~/.zshrc.bak.$(date +%Y%m%d_%H%M%S)`.
>    - After editing, agents MUST immediately verify syntax via `zsh -n ~/.zshrc` before concluding the turn.
>    - Agents MUST check for existing functions, aliases, or environment blocks before appending to avoid duplicate definitions.
>
> 2. **Strict Host OS Keychain & Security Protection (Zero Global Mutating)**:
>    - AI Agents are **STRICTLY PROHIBITED** from executing `security default-keychain` or `security list-keychains -s` globally in `~/.zshrc` or global shell commands.
>    - The host macOS default keychain MUST ALWAYS remain `/Users/<user>/Library/Keychains/login.keychain-db` to prevent crippling macOS system daemons (especially `sharingd` for AirDrop, `identityservicesd`, `trustd`, and Wi-Fi credential lookups).
>    - Profile keychain isolation is achieved EXCLUSIVELY via:
>      - Per-profile plist: `~/antigravity_homes/<profile>/Library/Preferences/com.apple.security.plist` (automatically respected by macOS Security framework when `HOME=$ag_home`).
>      - Scoped unlock inside subshells: `security unlock-keychain -p <pass> <profile.keychain-db>` within isolated scripts or `ag_run` subshells.
>      - Zero CLI Mutation: Profile CLI commands (`ag_run <profile> cli`, `{profile}-cli`) MUST NEVER mutate `security default-keychain` or `security list-keychains`.
>
> 3. **Strict Subshell Scope for Profile Environments (No Global Environment Contamination)**:
>    - AI Agents MUST **NEVER** export profile-specific environment variables (such as `export HOME=...`, `export AGY_PROFILE=...`, `export TMPDIR=/tmp/ag_...`) at the top-level of `~/.zshrc`.
>    - Profile environments MUST ONLY be established within localized subshells spawned by `ag_run()` or dedicated profile CLI aliases (`{profile}-cli`).
>    - Inside IDE terminals (`TERM_PROGRAM == "vscode"` and `-z "$AGY_CLI_MODE"`), `$HOME` MUST always remain `$REAL_HOME` (`/Users/<user>`) to guarantee unhindered access to OS services, local daemons (PostgreSQL, Docker daemon, Redis, MinIO), and host toolchains.
>
> 4. **Shared Toolchains, Libs & Symlink Architecture**:
>    - **Profile Scope & Boundary**: An Antigravity profile (`antigravity_homes/<profile>`) exists solely to isolate Antigravity user identity, credentials, OAuth tokens, and IDE session state.
>    - **Mandatory Shared Development Infrastructure**: All programming toolchains, developer tools, shared libraries, package managers, and compilation caches (Homebrew, Android SDK, Gradle, FVM, Flutter, Rust/Cargo, Go, Python/UV, npm, Docker socket, Caches) MUST be shared from the host OS (`$REAL_HOME`) via symlinks, NEVER duplicated, isolated, or severed.
>    - Agents modifying profile provisioning scripts or symlinks MUST strictly preserve symlinks to `$REAL_HOME` for all shared toolchains and libraries.
>
> 5. **Parent Process & IPC Handle Stripping in Launchers (`ag_run`)**:
>    - When launching Antigravity IDE instances (`open -n -a "Antigravity IDE"`), agents MUST explicitly strip parent process IPC handles, socket variables, and leaked runtime environment states:
>      `env -u ELECTRON_RUN_AS_NODE -u VSCODE_GIT_IPC_HANDLE -u VSCODE_IPC_HOOK_CLI HOME="$ag_home" AGY_PROFILE="$profile" TMPDIR="/tmp/ag_$profile" open ...`
>    - This eliminates socket collisions, channel crossover, and environment leaks when launching a new profile from within an existing IDE terminal or background automation daemon.
>
> 6. **Strict Antigravity Profile Identity & State Decoupling**:
>    - **Independent Antigravity State**: All internal Antigravity runtime state (`.gemini/antigravity`, conversation summaries, and `data/User/globalStorage/state.vscdb`) MUST remain strictly independent per profile. Never symlink `.gemini/antigravity` or `state.vscdb` to `$REAL_HOME` or another profile.
>    - **Identity Parity with Keychain**: The stored username in `data/User/globalStorage/state.vscdb` (`google.google-antigravity -> agy.onboarding.lastLoginUsername`) MUST match the profile's dedicated Keychain (`<profile>.keychain-db`).
>    - **Process & Token Hygiene**: Always terminate resident Electron PIDs of a profile (`pkill -f antigravity_homes/<profile>`) before modifying its DB to prevent stale RAM overwrites, and purge `signedOut` OAuth flags. For the exhaustive local protocol, see `.agents/rules/profile_isolation_rules.md`.
>    - **No Blind State Cloning**: Agents MUST NEVER clone `state.vscdb` from another profile without resetting `agy.onboarding.lastLoginUsername` to the target profile's email, and purging stale `comments`, `workspaceStorage`, and cross-profile paths from `extensions.user.cache`.
>    - **Hardware Fingerprint & Telemetry Decoupling**: Every profile's `storage.json` MUST contain unique, cryptographically generated `telemetry.machineId` and `telemetry.devDeviceId`. Never copy them without regenerating. Every profile's `settings.json` MUST set `"telemetry.telemetryLevel": "off"` to prevent leaking workspace paths and hardware signatures. Profile trajectory databases (`conversation_summaries.db`) must never be cloned.

