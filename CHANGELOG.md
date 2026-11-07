# Changelog

Notable changes per release. Starts at 1.1.0 — earlier versions were released without notes.

Versions follow `MAJOR.MINOR.PATCH`. A bump is **required** for any release: `claude plugin update`
compares the version in `.claude-plugin/plugin.json` and does nothing when it is unchanged, leaving
every installed machine on the old cached copy.

---

## 1.26.0 — 2026-11-07

Adds **Kiro CLI (`--cli kiro`)** as a first-class external reviewer across `principal-review`, `cross-model-review`, and `run_external_review.py`, establishes the **3-Tier Epic Documentation Architecture ("Prompt to Maintain" HLD vs Exhaustive Edge-Case BDD vs Self-Contained Task SSOT)** to reduce LLM token bloat while maximizing edge-case coverage, and completes `bin/d3nexus` subcommand & Gate Approval Ledger wiring across `/dev-lifecycle`.

### Added

- **Kiro CLI External Reviewer Support** (`skills/dev-implementation/resources/scripts/run_external_review.py`, `skills/principal-review/`, `skills/cross-model-review/`, `skills/dev-lifecycle/`, `rules/CRITICAL_RULES.md`):
  - Adds `--cli kiro` (`kiro-cli` / `kiro`) to `run_external_review.py` (`DEFAULT_REVIEW_CONFIG["providers"]["kiro"] = {"model": "claude-opus-5.5", "thinking_level": "high"}`), invoking `kiro-cli chat --no-interactive --trust-all-tools --wrap never --effort <effort> --model <model>`.
  - Automatically forwards `HOME=$REAL_HOME` when executing `kiro-cli` from inside an isolated Antigravity profile (`/antigravity_homes/<profile>`) so Kiro accesses the host macOS Keychain Builder ID session cleanly.
- **Complete `bin/d3nexus` Subcommand & Gate Ledger Wiring** (`bin/d3nexus`, `skills/dev-brainstorming/`, `skills/dev-implementation/`):
  - Adds `audit-epic`, `check-bdd`, `check-impact`, `integrate`, `package-epic`, `quality-check`, and `run-external-review` subcommands to `bin/d3nexus`.
  - Wires `resume_context.py --gate 1`, `--gate 4`, and `--gate 5` into `dev-brainstorming` and `dev-implementation` so all 5 lifecycle gates are recorded deterministically in `.devtool/GATE_LEDGER.md`.

### Changed

- **3-Tier Epic Documentation Separation ("Prompt to Maintain" vs LLM Execution SSOT)** (`skills/dev-designer/SKILL.md`, `skills/dev-implementation/SKILL.md`, `skills/dev-lifecycle/SKILL.md`):
  - **Human-Facing HLD (`<epic_name>.{en,vi}.md`)**: Redesigned as a concise System Overview & `Feature Maintenance Map ("Prompt to Maintain" Index)` mapping capabilities to canonical source entry points, core invariants, and troubleshooting hooks; keeps 1 mandatory High-Level Architecture diagram and makes Sequence Diagrams conditional on multi-actor/async flows (dropping redundant Use Case flowcharts and embedded Gherkin duplicates).
  - **Exhaustive Edge-Case & Exception BDD Suite (`bdd_scenarios.{en,vi}.md`)**: Dedicated exclusively to adversarial boundary testing across the 5 dimensions, prioritizing malformed inputs (`EC`), invalid state transitions (`ST`), concurrency/race conditions (`AR`), and fault injection with atomic rollback invariants (`FR`).
  - **Strict Bounded Context in `dev-implementation` & Single-Pass Readiness Check**: Phase 0 loads only orchestration metadata (`handoff.md`, HLD Maintenance Map & Integration Test Plan, and task headers), while Phase 2 loads one self-contained `task_*.md` SSOT at a time; Step 3 of `dev-designer` runs single-pass `check_epic_readiness.py` and Phase 2 Step 7 skips redundant per-task rebase when local `develop` has not moved.

## 1.25.0 — 2026-11-07

Delivers the **Contract & Authoring Ergonomics**, **Execution & Verification Infrastructure**, and **Multi-Epic Orchestration & Governance** epics alongside **Account Block Security Auditing (`audit-account-block`)**, **Multi-Profile OS & IPC Boundary Hardening (Rule 9)**, **Automated Gate 2 Handoff & Post-Review Quality Gates**, **Worktree-Aware IDE Theme & Title Synchronization**, **Scope-Aware `NOT_APPLICABLE` UI Audits**, and **Parallel + Two-Tier Cached `scripts/verify.sh`**.

### Added

- **Contract & Authoring Ergonomics** (`bin/d3nexus`, `skills/dev-implementation/`):
  - Ships portable `bin/d3nexus` CLI with zero-setup runtime dispatch across `check-task-contract`, `check-epic-readiness`, `sync-task-status`, `run-task-checks`, `package-epic`, `audit-epic`, `run-external-review`, and `resume-context`.
  - Adds `Evidence Files` task contract section, single-source task rendering (`render_epic_tasks.py`), shift-left R2/R3 parity checks, and verification row grammar diagnostics.
- **Execution & Verification Infrastructure** (`skills/dev-implementation/resources/scripts/`):
  - Adds task text replay engine (`replay_task_text.py`), static anchor verification against `HEAD`, and `MEASURE` phase execution.
  - Adds failure-set baseline recording (`record_failure_baseline.py`) and regression comparison CLI (`compare_failure_sets.py`).
  - Enhances `bootstrap_worktree.sh` with polyglot dependency detection (`uv sync`, `npm`, `cargo`, `flutter`), automatic `.vscode/settings.json` and `.env*` seeding from `REPO_ROOT`, and immediate window title synchronization.
- **Multi-Epic Orchestration & Governance** (`skills/dev-implementation/resources/scripts/`, `scripts/resume_context.py`):
  - Adds inter-epic `Depends On` declarations, readiness dependency resolution, and prerequisite task replay across queued epics.
  - Adds conflict-aware concurrent epic backlog management (`promote_epic_tasks.py`) and bulk task promotion with file-overlap inspection.
  - Adds `package_epic.py --revise` workflow and HLD `Spec Errata` contract for in-place packaged epic revisions without silent handoff overwrites.
  - Adds structured Gate Approval Ledger in `scripts/resume_context.py` (`--gate`, `--status`, `--notes`).
- **Account Block Auditing & Multi-Profile OS Safety** (`skills/audit-account-block/`, `rules/CRITICAL_RULES.md`, `scripts/agy_quota.py`):
  - Adds `d3nexus:audit-account-block` skill to audit Antigravity profiles for cloned machine IDs, cross-account trajectory leaks, and 403 ToS suspension risks.
  - Codifies Rule 9 in `rules/CRITICAL_RULES.md` enforcing `.zshrc` backup/syntax verification, host macOS default keychain protection, subshell-scoped profile environments, shared toolchain symlinks, and parent IPC handle stripping in `ag_run`.
  - Upgrades `quota_dashboard.html` and `scripts/agy_quota.py` with live OpenAI usage API, Claude/Codex hashed session tracking, 30-minute init refresh throttling, and schedule auto-expiration.
- **Gate 4 Active Execution Lease & Receipt** (`verify_polyglot_registry.py`, `integrate_branch.py`):
  - Writes `.gate4_active.lease` during active polyglot Gate 4 execution and `gate4_receipt.json` upon completion; `integrate_branch.py` refuses branch landing while a Gate 4 run is still in progress.

### Changed

- **Automated Gate 2 Packaging & Post-Review Quality Gates** (`skills/dev-designer/`, `skills/dev-lifecycle/`, `skills/dev-implementation/`, `skills/principal-review/`, `skills/cross-model-review/`, `rules/CRITICAL_RULES.md`):
  - Automatically runs `package_epic.py` and `/save-context` (`--gate 2`, `--state`, `--emit-prompt`) upon Gate 2 approval and presents a single unified Handoff Choice (`/principal-review` vs `/dev-implementation` vs `Done`).
  - Automatically executes local mechanical quality gates (`Phase 4 / Gate 4` in Stage 3; `package_epic.py --revise` + `/save-context` in Stage 2) immediately after developer-approved review triage fixes are committed, while preserving the mandatory human Triage decision checkpoint.
- **Scope-Aware UI Quality Checks & Impact Analysis** (`audit_ui_state_and_styles.py`, `validate_web_quality.py`, `check_code_impact.py`, `*-quality-check/SKILL.md`):
  - Short-circuits `ui_review` with `status: "NOT_APPLICABLE"` (`code: "scope_unmodified"`) when `git diff --name-only <base_ref>...HEAD` modifies zero UI files.
  - Upgrades `check_code_impact.py` to discover `tests/**/test_<stem>.py`, parse Python `coverage.json`, and report 3 distinct states (`MEASURED`, `TESTS_PRESENT_NO_REPORT`, `NO_TESTS_FOUND`).
- **Worktree-Aware IDE Theme & Context Reporting** (`scripts/resume_context.py`):
  - Resolves the primary repository root (`resolve_primary_repo_root`) when running inside `.worktrees/<epic_dir>` so `REPO_SIGNATURES` (icon `🔴/🟢/🔵/🟠` and persistent title/status bar colors) are always preserved and synced to both primary repo and worktree `.vscode/settings.json`.
  - Separates base-branch progress, worktree-branch progress, and uncommitted dirty file counts in `scan_active_tasks`.
- **Parallel & Cached Verification Runner** (`scripts/verify.sh`):
  - Replaces `root.rglob("*")` in Section 8 with `git ls-files`, combines Sections 1 & 1b into a single Python invocation, runs all 39 `unittest` and `pytest` suites in parallel via `ThreadPoolExecutor` (Longest-Job-First scheduling), and adds worktree-safe 2-tier content-hash caching (`FULL_HASH:CODE_HASH` in `$GIT_DIR_PATH/.verify_tests_tree_cache` with `--full` override), cutting full verification from ~151s to ~32s and cached runs to ~1s.

---

## 1.24.0 — 2026-11-05

Introduces the Web Quality Assurance Provider and Integration Quality Gate, delivers Playwright zero-console-and-layout-defect watchdog fixtures for TypeScript and Python, adds in-place Vanilla JavaScript JSDoc type-checking, implements Polyglot Gate 4 registry fan-out, embeds anti-rationalization doubt-driven workflow rules, adds automated manual smoke checklist generation, introduces component UI state and styling audits, and supports worktree-isolated window title synchronization with zero-context tool exemptions.

### Added

- **Web Quality Assurance Provider & Contract** (`skills/web-quality-check/`, `skills/quality_check/`):
  - Adds `d3nexus:web-quality-check` skill implementing Provider Result Contract v1 for Astro TypeScript and Vanilla JavaScript projects.
  - Adds `skills/web-quality-check/resources/scripts/validate_web_quality.py` to validate web quality configurations, run platform capabilities, verify genuine XML test results (`build/test-results/`), enforce execution freshness against Git HEAD, and ensure watchdog attachment evidence.
  - Adds `skills/web-quality-check/resources/scripts/run_playwright_harness.py` for headless browser test execution and artifact capture.
  - Defines web quality capabilities (`type_check`, `lint`, `test_unit`, `test_e2e`, `ui_review`, `contracts`) and standard profiles (`pr`, `epic`, `release`, `scheduled`).
- **Playwright Zero-Console-And-Layout-Defect Watchdog & Fixtures** (`skills/web-quality-check/resources/templates/`):
  - Delivers `playwright-zero-error.fixture.ts` and `playwright_zero_error.py` test fixtures for TypeScript and Python environments.
  - Implements 4-tier watchdog protection: console error interceptor (`console.error`, unhandled exceptions), 404 network failure trap (static assets, stylesheets, fonts), visual layout defect checker (`assertVisualIntegrity` inspecting unstyled defaults and CSS rule cascade), and consecutive duplicate text / DOM state leak detector.
  - Adds accessibility and visibility clipping filters to prevent false positives on hidden or offscreen elements.
- **Vanilla JS JSDoc Type-Checking Engine** (`skills/web-quality-check/resources/scripts/check_vanilla_js.py`):
  - Provides in-place static type checking for Vanilla JavaScript files using TypeScript compiler (`tsc --project jsconfig.json --noEmit`) without migrating to `.ts`.
  - Scaffolds `jsconfig.json` template (`skills/web-quality-check/resources/templates/jsconfig.template.json`) with `checkJs: true`, DOM lib types, and strict parameter inspection.
- **Polyglot Gate 4 Registry & Multi-Provider Fan-Out** (`skills/quality_check/resources/scripts/verify_polyglot_registry.py`):
  - Implements concurrent fan-out and dispatch across multiple registered providers in `.agents/quality/check_quality.json`.
  - Adds `--execute` runner flag for end-to-end multi-provider quality gate runs.
  - Enforces repository SHA binding, Git HEAD verification, and rejects stale evidence or SHA drift.
  - Scaffolds polyglot templates (`polyglot-check-quality.template.json` and `web-quality.template.json`) in `skills/setup_quality_check/`.
- **UI State & Styles Audit Engine** (`skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py`):
  - Implements static and AST analysis of CSS and styling declarations across HTML, Astro, and CSS files.
  - Detects component-scoped style definitions, inline CSS attributes, and visual styling adherence.
  - Includes worktree path filtering, git base diff cache-busting, and strict word boundary matching.
- **Automated Manual Smoke Checklist Generator** (`skills/dev-implementation/resources/scripts/generate_smoke_checklist.py`):
  - Generates a concise 3-5 step `manual_smoke_checklist.md` upon epic completion, targeting extracted CLI and script entrypoints.
  - Drastically compresses manual verification time for human architects from 30 minutes to 2 minutes.
- **Anti-Rationalization & Doubt-Driven Workflow Rules** (`skills/test-driven-development/SKILL.md`, `skills/dev-implementation/SKILL.md`):
  - Codifies strict Anti-Rationalization Tables banning test fakery, trivial unit mocks for Tier C integration tests, and ungrounded completion claims.
  - Requires genuine integration test execution, real DOM logic assertions, and evidence-backed triage.
- **Self-Verification Quality Manifest for `ai-agent-tools`** (`.agents/quality/check_quality.json`, `.agents/quality/python-quality.json`):
  - Registers `agent-tools-python` quality provider executing `ruff format`, `ruff check`, `mypy`, `pytest tests`, and `verify.sh`.
- **Worktree-Aware Window Title Sync & Fast-Execution Exemption** (`scripts/resume_context.py`, `rules/CRITICAL_RULES.md`):
  - Updates `sync_window_title` to detect git worktree paths and isolate window title updates to current worktree context, preventing clobbering primary repository titles.
  - Adds Section 8.1 Zero-Context and Fast-Execution Exemption in `CRITICAL_RULES.md` for routine operational commands (`/refresh-session`, `/setup_keybindings`, git status/diff inspections).

### Changed

- **Scenario Runner Constraints & Provenance Verification** (`skills/dev-implementation/resources/scripts/result_reports.py`):
  - Recognizes compiler and audit workflow integration patterns in test report summaries.
  - Extracts explicit Tier tags from scenario metadata and enforces positive integration evidence.
  - Extracts Dart test URL provenance and enforces classname runner provenance for Tier C integration verification.
- **Quality Check Provider Acceptance** (`skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`):
  - Updated to test multi-provider acceptance and contract compatibility across polyglot architectures.

---

## 1.23.0 — 2026-11-04

Introduces visual multi-epic workspace synchronization and persistent color customization, adds dynamic SQLite account & email ID extraction across 19 Antigravity profiles, guarantees multi-profile GUI isolation without cross-account title contamination, hardens Python 3.9 compatibility across all lifecycle tools and test suites, and publishes bilingual architecture specifications and implementation plans.

### Added

- **Visual Multi-Epic Workspace Synchronization Engine** (`scripts/resume_context.py`):
  - Adds `sync_window_title` with support for `--sync-title`, `--stage`, and `--profile` CLI options.
  - Implements repository color signatures: 🔴 `[LYRICS-SYNC]` (`#7f1d1d`), 🟢 `[D3NEXUS]` (`#065f46`), 🔵 `[NEXUS]` (`#0d47a1`), and 🟠 `[AGENT-TOOLS]` (`#b45309`).
  - Enforces persistent inactive bar parity: synchronizes `titleBar.inactiveBackground` and `statusBar.inactiveBackground` to match active theme backgrounds, eliminating IDE dimming when windows lose focus.
  - Formats window titles dynamically: `"<ICON> [<REPO_NAME>] [@<account_id>] <Vietnamese Epic Name> - <Stage / Task>"`.
  - Integrates Vietnamese Epic titles parsed from `.devtool/epic/<slug>/*.vi.md` H1 headers.
- **Dynamic SQLite Account & Email ID Extraction** (`scripts/resume_context.py`):
  - Adds `extract_email_id_from_profile` inspecting `state.vscdb` (`google.google-antigravity` onboarding storage) in read-only URI mode (`file:...mode=ro`).
  - Implements 4-tier account resolution precedence: CLI/environment override -> active process inspection (`ps -eo command`) -> `workspaceStorage` MRU timestamp matching -> `HOME` directory fallback.
  - Supports all 19 Antigravity profiles seamlessly (`brother`, `buivantrong8901`, `d3molt`, `daddy`, `danhdue`, `duedd`, `duvthinh403`, `hau`, `hoangcongtam690`, `khe`, `mau`, `molt`, `mommy`, `ngocanh000690`, `nguyenhieu000690`, `peter`, `phungthuy8901`, `tess`, `trananh`).
  - Adds comprehensive unit test `test_extract_email_id_from_profile` in `scripts/test_resume_context.py`.
- **Multi-Profile GUI Isolation & Rule Governance** (`rules/CRITICAL_RULES.md`):
  - Establishes Section 8.4 in `CRITICAL_RULES.md` mandating window title synchronization, active/inactive bar parity, and repository color signatures.
  - Separates personal identity (`User/settings.json`) from workspace invariants (`.vscode/settings.json`), preventing cross-account title leakage when opening repositories directly from Antigravity IDE GUI (`File -> Open Folder`).
  - Updates template settings in `templates/.vscode/settings.json` and canonical rule template `templates/.agents/rules/window_title_sync.md`.
- **Bilingual Specifications & Plans** (`docs/superpowers/`):
  - Publishes full bilingual High-Level Design (HLD) specifications: `docs/superpowers/specs/2026-11-04-visual-multi-epic-workspace-sync-design.en.md` and `docs/superpowers/specs/2026-11-04-visual-multi-epic-workspace-sync-design.vi.md`.
  - Publishes full bilingual implementation plans: `docs/superpowers/plans/2026-11-04-visual-multi-epic-workspace-sync-plan.en.md` and `docs/superpowers/plans/2026-11-04-visual-multi-epic-workspace-sync-plan.vi.md`.

### Changed

- **Python 3.9 Compatibility Hardening**:
  - Adds `from __future__ import annotations` across 29 test and CLI tool scripts to enable PEP 604 type unions (`type | None`) on macOS default Python 3.9.6.
  - Adds backward-compatible UTC timezone fallbacks (`timezone.utc`) in `sync_task_status.py`, `run_task_checks.py`, `run_external_review.py`, and `sync_contracts.py`.
  - Hardens symlink loop detection in `sync_contracts.py` to catch `RuntimeError` raised by Python 3.9 `Path.resolve()`.
  - Resolves `socket.timeout` exception inheritance in `local_review.py` for Python 3.9.
  - Replaces `itertools.pairwise` with `zip(chats, chats[1:])` in `test_local_review.py`.

---

## 1.22.0 — 2026-11-03

Introduces contract diff gating across multi-repo Hub/Satellite topologies, adds diff-check engine and contract map validation to sync-shared-contracts, aligns quality check schemas across all 5 platforms, and publishes bilingual shared contracts quick-guides.

### Added

- **Contract Diff-Check Engine** (`skills/sync-shared-contracts/resources/scripts/sync_contracts.py`):
  - Adds `diff-check` subcommand with `--contract-map`, `--base-ref`, `--hub-root`, `--format` (`text` / `json`), and `--strict` options.
  - Implements contract map schema validation (`.agents/contracts/contract_map.json`) with strict rule semantics and path safety checks.
  - Implements glob pattern matching (`rules[].include` and `exclude`) to detect modifications in contract-bound source files.
  - Resolves multi-domain Hub topologies and validates satellite outbound symlinks.
  - Enforces base-ref resolution precedence (CLI `--base-ref`, merge-base against upstream, `origin/develop`, `origin/main`, and `HEAD~1` fallback).
  - Enforces gap waiver proof tracking: verifies whether contract drifts or contract-bound code modifications are documented with valid active RFC/Gap references in `gaps_and_rfcs.md`.
  - Integrates interactive and programmatic contract synchronization workflows (`check`, `brief`, `ack`, `diff-check`).
- **Standardized `contract_diff` Quality Provider Schemas** (`skills/*-quality-check/resources/schemas/`):
  - Aligns and expands schema definitions across all 5 quality check platforms: Android (`android-quality.schema.json`), Flutter (`flutter-quality.schema.json`), iOS (`ios-quality.schema.json`), Python (`python-quality.schema.json`), and Rust (`rust-quality.schema.json`).
  - Scaffolds contract diff capability placeholders and validation in quality provider test suites.
- **Contract Map Template** (`skills/setup-shared-contracts/resources/templates/contract_map.json.tmpl`): Adds canonical starter template for repo-level contract mapping.
- **Bilingual Shared Contracts Quick Guides** (`docs/shared-contracts-quick-guide.en.md`, `docs/shared-contracts-quick-guide.vi.md`): Detailed 626-line quick-lookup guides covering Hub & Satellite topologies, Canonical Contract Triad (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`), symlink configuration, drift detection (`diff-check`), gap lifecycles, and troubleshooting.
- **Expanded Contract & Lifecycle Unit Tests** (`skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py`, `scripts/test_lifecycle_document_contract.py`): Adds 958 lines of unit tests covering contract map validation, glob patterns, base ref resolution, gap waivers, satellite quoting, and multi-domain hub topologies, plus contract diff gate assertions.

### Changed

- **Lifecycle Skills Integration** (`skills/dev-brainstorming/SKILL.md`, `skills/dev-designer/SKILL.md`, `skills/sync-shared-contracts/SKILL.md`, `skills/setup-shared-contracts/SKILL.md`):
  - Updates `dev-brainstorming` and `dev-designer` to enforce contract diff gating and contract-first sequencing (`task_01`).
  - Updates `sync-shared-contracts` documentation with full `diff-check` CLI options, output formats, and CI integration.
  - Refreshes capability contract reference specifications for Python and Rust.

---

## 1.21.0 — 2026-11-01

Adds a 30-second default safety delay buffer (offset) to scheduled pre-warming daemons in the refresh-session engine to guarantee complete cloud rate-limit rollover, updates CLI flags, and synchronizes bilingual quick-guides.

### Added

- **Safety Delay Buffer for Scheduled Daemons** (`skills/refresh-session/resources/scripts/refresh_session.py`):
  - Adds `--delay` and `--offset` options to `refresh-session schedule`.
  - Sets default delay buffer to 30 seconds for scheduled OS daemons (`--delay 30`), ensuring background pings wake at the reset minute (e.g. `05:00:00`) but sleep 30 seconds to execute safely at `05:00:30`, absorbing any cloud rate-limit worker clock skew or delayed quota bucket replenishment.
  - Keeps on-demand manual pings immediate (`--delay 0`) for zero-latency manual refreshes.
- **Delay Buffer Invariants & Unit Tests** (`skills/refresh-session/resources/scripts/test_refresh_session.py`): Adds 4 new unit tests verifying delay argument defaults (0 for ping, 30 for schedule), custom delay overrides, launchd plist argument generation with delay, and delay sleep execution (31 total unit tests).

### Changed

- **Native OS Daemon Integration** (`skills/refresh-session/resources/scripts/refresh_session.py`): Injects `--delay <sec>` into macOS launchd agent plists and Linux crontab commands, and displays delay buffer configuration in daemon status reports (`• Delay buffer: 30s`).
- **Bilingual Quick Guides & Skill Documentation** (`skills/refresh-session/SKILL.md`, `docs/refresh-session-quick-guide.en.md`, `docs/refresh-session-quick-guide.vi.md`): Documents the 30-second safety delay buffer across natural language examples, cheat-sheet command tables, and underlying architecture sections.

---

## 1.20.0 — 2026-11-01

Adds daily scheduling automation (Shift-Left Quota Staggering) to the refresh-session engine via macOS launchd and Linux crontab daemons, flexible time parsing, and comprehensive bilingual quick guides.

### Added

- **Daily Scheduled Session Pre-Warming Engine** (`skills/refresh-session/resources/scripts/refresh_session.py`): Adds `schedule` subcommand supporting `--time`, `--target`, `--status`, `--uninstall` (`--remove`), and `--json`. Allows developers to schedule pre-warming daemons at custom hours (e.g. `05:00`, `5h`, `6am`) so rolling 5-hour quota windows reset ahead of deep work hours.
- **Flexible Natural Time Parser** (`skills/refresh-session/resources/scripts/refresh_session.py`): Parses standard 24-hour time (`05:00`, `14:30`), short hour (`5h`, `6h`, `5`, `6`), and 12-hour AM/PM (`5am`, `5:30am`, `6pm`, `12pm`) formats into `(hour, minute)` with robust validation.
- **Native OS Daemon Management** (`skills/refresh-session/resources/scripts/refresh_session.py`):
  - macOS: Generates launchd agent plist (`~/Library/LaunchAgents/com.d3nexus.refresh-session.plist`) with absolute paths and injected `PATH` environment, and controls lifecycle via `launchctl load`/`unload`.
  - Linux: Automates user crontab entries with idempotent comment block delimiters.
- **Bilingual Refresh-Session Quick-Guides** (`docs/refresh-session-quick-guide.en.md`, `docs/refresh-session-quick-guide.vi.md`): Detailed quick-lookup cheat sheets covering all chat and CLI commands, Shift-Left Quota Staggering strategy, launchd troubleshooting, and logs inspection.
- **Expanded Scheduling Unit Tests** (`skills/refresh-session/resources/scripts/test_refresh_session.py`): Adds 14 unit tests covering 24h, short hour, and AM/PM time parsing, plist generation, daemon install/status/uninstall workflows, and schedule CLI argument parsing (27 total unit tests).

### Changed

- **`refresh-session` Skill Documentation** (`skills/refresh-session/SKILL.md`): Documents natural language scheduling triggers, daily daemon configuration commands, flexible time format examples, and links to the bilingual quick guides while preserving 100% backward compatibility for on-demand pings.

---

## 1.19.0 — 2026-11-01

Adds the refresh-session skill and engine for pre-warming 5-hour rolling session windows with minimum token consumption and zero skill initialization, formalizes review triage standardization and sticky review preferences, and strengthens context memory and task observer resilience.

### Added

- **`refresh-session` skill and engine** (`skills/refresh-session/SKILL.md`, `skills/refresh-session/resources/scripts/refresh_session.py`, `skills/refresh-session/resources/scripts/test_refresh_session.py`): Pings Claude Code CLI (`claude`) and OpenAI Codex CLI (`codex`) inside an ephemeral isolated sandbox to pre-warm or refresh rolling 5-hour quota windows with near-zero tokens (~50 tokens on Claude, 1,645 tokens on Codex) and zero skill/plugin/MCP initialization.
- **Release Verification Harness Section 16** (`scripts/verify.sh`): Adds automated Section 16 verifying the `refresh-session` CLI engine contracts, sandboxed temporary directory execution, isolation flags, and unit test suite.

### Changed

- **Review Triage Standardization & Sticky Preferences** (`skills/dev-implementation/resources/scripts/run_external_review.py`, `skills/dev-implementation/resources/scripts/test_run_external_review.py`): Enforces a unified 4-bullet triage header (`Candidate SHA`, `Reviewer`, `Thinking Level`, `Verdict`), persists sticky per-provider reviewer preferences in `.devtool/review_config.json`, implements dynamic Claude `--effort` / `--thinking` flag probing, and embeds senior 5-layer reviewer verification instructions.
- **Context Memory & Task Observer Resilience** (`scripts/resume_context.py`, `skills/task-observer/SKILL.md`): Ignores volatile Tier 2 runtime state files in status checks, fixes nested repository `.devtool` path resolution, and guards zsh session-start glob expressions against `no matches found` errors.

---

## 1.18.0 — 2026-10-31

Reminds brainstorming sessions about shared-contract drift and lets Rust quality manifests call plugin scripts without machine-specific paths.

### Added

- **`{skills_dir}` placeholder** (`skills/rust-quality-check/SKILL.md`, `skills/rust-quality-check/references/rust-capability-contract.md`): Capability commands may start an argument with `{skills_dir}`, which the provider resolves to the installed plugin's `skills/` directory.

### Changed

- **Contract reminder in brainstorming** (`skills/dev-brainstorming/SKILL.md`): When `shared-contracts/` exists, run the read-only `check` and `brief` and record shared-contract impact in the spec. Never `ack` during brainstorming.

---

## 1.17.0 — 2026-10-31

Adds the Tri-Role Context Memory Quick-Guide, robust multi-line array parsing and metafied zsh history decoding in `--sync-zshrc`, automatic sibling workspace repository context harvesting in `resume_context.py`, and external review runner hardening across Antigravity and Claude CLIs.

### Added

- **Tri-Role Context Memory Quick-Guide** (`docs/context-memory-quick-guide.en.md`, `docs/context-memory-quick-guide.vi.md`): Comprehensive bilingual quick-guide detailing the Tri-Role operating model (Role 2.1 Human Architect, Role 2.2 AI Assistant, Role 2.3 AI Programmer), a 10-second command cheat-sheet, and 5 step-by-step workflow scenario playbooks (Principal Review, AI Programmer task execution, Cross-Model Review, Independent Technical Discussion, and Interrupted Session Resume).
- **Updated Lifecycle State Diagrams** (`docs/lifecycles.en.md`, `docs/lifecycles.vi.md`): Synchronized Mermaid lifecycle and resume diagrams annotated with Tri-Role governance personas and context restoration checkpoints.
- **Sibling Workspace Repository Auto-Harvest** (`scripts/resume_context.py`, `docs/architecture/resume_context.py`): Automatically discovers and scans sibling repositories (`ai-agent-tools`, `D3Nexus`, `lyrics-sync`, `nexus`) when executed from within any individual repository directory, displaying Git working tree status across all repos, open contract RFCs in `D3Nexus/shared-contracts/*/gaps_and_rfcs.md`, and active Kanban tasks.

### Changed

- **Multi-Line Array & Metafied Byte History Sync** (`scripts/resume_context.py`, `docs/architecture/resume_context.py`): Hardens `update_zshrc_sync_items` to cleanly parse multi-line `sync_items=(...)` arrays containing comment lines (`# ...`), and decodes `.zsh_history` with `errors="replace"` to handle non-UTF-8 metafied bytes (`0x83`) on macOS.
- **External Review Runner Hardening** (`skills/dev-implementation/resources/scripts/run_external_review.py`): Tolerates severity tags without square brackets in reviewer output, strips backtick wrappers from integration results and roots in HLD files, adds `--dangerously-skip-permissions` to Antigravity CLI invocations, and supports optional `--developer-note` in Principal Review prompts.
- **BDD Traceability & Task Execution Tooling** (`skills/dev-implementation/resources/scripts/check_bdd_traceability.py`, `skills/dev-implementation/resources/scripts/compute_execution_order.py`, `skills/dev-implementation/resources/scripts/result_reports.py`): Normalizes whitespace and comma separation in Covers declarations, supports both `&` and `and` in dependency headers while including completed tasks from `features/done/`, and improves Dart test event JSON stream detection.
- **Brainstorming Server Idle Timeout** (`skills/dev-brainstorming/scripts/server.cjs`): Extends default idle timeout to 4 hours, configurable via `BRAINSTORM_IDLE_TIMEOUT_MS`.

---

## 1.16.0 — 2026-10-31

Delivers Two-Tier Project Memory (`scripts/resume_context.py`), Tri-Role Governance Model, multi-profile shell environment & shared history synchronization, new `resume-context` and `save-context` skills, Critical Rule 8 in `CRITICAL_RULES.md`, automatic context hooks across all 9 dev-lifecycle skills, and full JSON harvest export.

### Added

- **Two-Tier Context Engine** (`scripts/resume_context.py`, `docs/architecture/resume_context.py`): Delivers a zero-dependency Python CLI engine providing Tier 1 permanent project memory (`.devtool/PROJECT_LEDGER.md`) and Tier 2 active feature isolation (`.devtool/state/<epic_slug>.md` $\le 20$ lines and `.devtool/logs/activity_<epic_slug>.log`) protected by exclusive `fcntl.flock` concurrency locking (`.devtool/.memory.lock`). Automatically resolves primary repo root from git worktrees (`git rev-parse --git-common-dir`) and generates unified rollups into `.devtool/assistant_state.md` and `.devtool/activity_stream.log`.
- **JSON Harvest Serialization** (`scripts/resume_context.py`): Adds `--json` capability to export comprehensive context telemetry in machine-readable JSON format, including ledger milestones, active state snapshots, recent programmer activity logs, git working tree status, open contract RFCs, and active Kanban tasks.
- **Tri-Role Persona Governance Discipline**: Formalizes and enforces strict persona boundaries: Human Architect (Role 2.1 — Strategic decisions & approval gates), AI Assistant (Role 2.2 — Technical Advisor & Reviewer, strictly prohibited from editing production code), and AI Programmer (Role 2.3 — Senior TDD Software Engineer, executing Kanban tasks under strict TDD and bounded context boundaries). Deterministic handoff prompt emission via `--emit-prompt` covers 5 standard lifecycle scenarios (`principal-review`, `implement`, `cross-review`, `finish`, `assistant`).
- **Standalone `resume-context` & `save-context` Skills** (`skills/resume-context/`, `skills/save-context/`): New core skills to restore context on startup, check environment health, persist real-time decisions and activity logs to disk, and save non-destructive checkpoints without premature feature archiving.
- **Mandatory Memory & Persona Rule in Critical Rules** (`rules/CRITICAL_RULES.md`): Adds Section 8 establishing non-negotiable two-tier project memory hygiene, strict 20-line state ceiling, advisory file locking, and Tri-Role persona discipline across all agent runtimes.
- **Multi-Profile Shell Environment & History Sync** (`scripts/resume_context.py --sync-zshrc`): Synchronizes `.zshrc` across Antigravity and user home directories (`~/.zshrc` and `antigravity_homes/*`), establishes real-time shared history (`HISTFILE="$REAL_HOME/.zsh_history"`, `SHARE_HISTORY`), creates symlinks (`Projects -> AllProjects`), and defines universal shell aliases (`alias resume` and `alias save-context`).
- **Release Verification Harness Section 15** (`scripts/verify.sh`): Adds automated Section 15 verifying context memory management CLI capabilities, multi-epic concurrency locking, worktree routing, legacy migrations, and Tri-Role governance rules.

### Changed

- **Dev-Lifecycle Skills Context Integration**: Integrates automatic `resume_context.py` state/activity recording and handoff prompt hooks across 9 dev-lifecycle skills and templates (`dev-brainstorming`, `dev-designer`, `dev-lifecycle`, `dev-implementation`, `principal-review`, `cross-model-review`, `finishing-a-development-branch`, `handoff-template.md`, and `principal-review.md`).
- **Dev-Implementation Pre-Finish Hook**: Extends Stage 4 Pre-Finish Hook to execute `python3 scripts/resume_context.py --complete <slug> "<milestone>"` to record permanent milestones and archive feature states upon branch landing.

---

## 1.15.0 — 2026-10-25

Adds support for the Antigravity CLI (`agy`) with `Gemini 4 Argon (Medium)` as an external review engine for both Principal Review (Shift-Left design verification) and Cross-Model Review (Shift-Right code verification).

### Added

- **Antigravity CLI (`agy`) Review Engine** (`skills/dev-implementation/resources/scripts/run_external_review.py`): Integrates `agy` into the review runner with sandboxed execution (`--sandbox --mode plan`), automatic stdin streaming, and default model configuration to `"Gemini 4 Argon (Medium)"`. Supports custom model overrides via `--model`.
- **Review CLI Selection Coverage**: Expands CLI choices across `--kind principal` and `--kind code` to include `agy` alongside `claude`, `codex`, and `ollama`.
- **Automated Test Suite for `agy` CLI** (`skills/dev-implementation/resources/scripts/test_run_external_review.py`): Adds unit tests verifying `agy` execution flags, sandboxing, model defaults, and output parsing in both code review and principal review modes.

### Changed

- **Principal Review Procedure & Choice Prompt** (`skills/dev-lifecycle/references/principal-review.md`, `skills/principal-review/SKILL.md`): Updates the packaging checkpoint prompt and documentation to offer Antigravity CLI (`agy --model "Gemini 4 Argon (Medium)"`) alongside Claude CLI and Codex CLI.
- **Review Choice at Gate 4** (`skills/dev-implementation/SKILL.md`, `skills/dev-lifecycle/SKILL.md`, `skills/cross-model-review/SKILL.md`): Extends Gate 4 Review Choice Option 2 prompt (`command -v claude codex agy`) to include Antigravity CLI.
- **Critical Rules & Lifecycle Documentation** (`rules/CRITICAL_RULES.md`, `docs/lifecycles.en.md`, `docs/lifecycles.vi.md`): Authorizes `agy` under Critical Rules 5 & 6 as an allowed review CLI, and updates bilingual architecture documentation and triage guides.

---

## 1.14.0 — 2026-10-23

Decouples external AI review into two standalone skills (`principal-review` and `cross-model-review`), adds ad-hoc document and branch diff review modes with live streaming triage, establishes Critical Rules banning autonomous review triggers and infinite loops, and refactors orchestrators to delegate to the new standalone review skills.

### Added

- **Standalone Principal Review Skill** (`skills/principal-review/`): Extracts design document verification into a reusable, modular skill (`d3nexus:principal-review`) equipped with prompt templates, severity classification rules (Critical, Important, Minor), and revision loop protocols.
- **Standalone Cross-Model Review Skill** (`skills/cross-model-review/`): Extracts multi-model and local code review into an independent skill (`d3nexus:cross-model-review`) covering Claude CLI, Codex CLI, and local Ollama review passes, with dedicated triage protocols and setup guides.
- **Ad-Hoc Review Modes** (`skills/dev-implementation/resources/scripts/run_external_review.py`): Adds `--document <path>` for standalone document reviews outside epics and `--diff-range <base..head>` for ad-hoc git diff reviews between branches or commits.
- **Streaming Review & Live Triage Output** (`skills/dev-implementation/resources/scripts/run_external_review.py`): Streams raw model response tokens and dynamically extracts and renders live markdown triage tables as reviewer findings emerge.
- **Critical Rules Against Autonomous Reviews & Infinite Loops** (`rules/CRITICAL_RULES.md`): Mandates strict human checkpointing by forbidding AI agents from autonomously triggering Principal or Cross-Model reviews, and strictly prohibiting infinite re-review chaining by requiring human self-review and explicit developer confirmation after fixing findings.

### Changed

- **Orchestrator Delegation Refactor** (`skills/dev-lifecycle/SKILL.md`, `skills/dev-implementation/SKILL.md`): Refactors Stage 2 Gate 2 and Stage 3 Gate 4 review phases to invoke `d3nexus:principal-review` and `d3nexus:cross-model-review` directly while preserving hard gate invariants and loop properties.
- **Bilingual Lifecycle & Architecture Documentation** (`docs/lifecycles.en.md`, `docs/lifecycles.vi.md`): Updates Mermaid flowcharts, subgraphs, and bilingual text to document the standalone review skills at Stage 2 and Stage 3.
- **Task Archival & Lifecycle Sync**: Finalizes the `split_review_skills` epic with 100% test coverage and 19/19 BDD scenario traceability, archiving completed tasks into the epic record.

---

## 1.13.0 — 2026-10-21

Introduces full offline Local Model Review powered by Ollama, dependency-aware diff slicing with token budget enforcement, shared platform review checklists, multi-pass aggregation and triage tooling, 3-option Review Choice at Gate 4, and resilient test result parsing.

### Added

- **Local Model Review via Ollama** (`skills/dev-implementation/resources/scripts/local_review.py`, `skills/dev-implementation/resources/scripts/run_external_review.py`): Delivers a 100% free, offline, private code review engine connecting directly to local Ollama models (`qwen2.5-coder:14b`, `deepseek-r1:14b`, `llama3.3:70b`, etc.) over streamed NDJSON HTTP transport with automatic endpoint health checks and timeout controls.
- **Dependency-Aware Diff Slicing & Token Budgets** (`skills/dev-implementation/resources/scripts/local_review.py`): Intelligently chunks complex code diffs into bounded slices topologically ordered by dependency depth and constrained by configurable token budgets (`--token-budget`, `--pass-budget`), with graceful snippet markers (`[SNIP: remainder of file diff exceeds slice budget]`) to prevent context window blowouts.
- **Shared Platform Review Checklists & Verification Rules** (`skills/dev-implementation/references/review-rules.md`, `skills/dev-implementation/references/local-review-*.md`): Centralizes universal verification standards across mobile (Flutter, Android, iOS), web, Python, and Rust stacks, shared seamlessly between external reviewers (Claude/Codex CLI) and local reviewers (Ollama).
- **Multi-Pass Finding Aggregation & Deduplication** (`skills/dev-implementation/resources/scripts/local_review.py`): Executes concurrent or sequential review passes with live progress streaming, deduplicating matching findings across passes and producing structured markdown rounds in `review_results.md`.
- **Review Triage & Round Comparison Subcommands** (`skills/dev-implementation/resources/scripts/run_external_review.py`): Adds `run_external_review.py triage` to classify findings (accept/reject/fix) and `run_external_review.py compare` to track resolution and regression deltas across successive review rounds.

### Changed

- **3-Option Review Choice at Gate 4** (`rules/CRITICAL_RULES.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-implementation/SKILL.md`): Extends the post-Gate 4 review decision to offer three explicit paths: Option 1 (Finish to Gate 5), Option 2 (Local model review via Ollama), and Option 3 (Cross-model review via Claude CLI or Codex CLI). Any findings generating Fix commits mandate a full Gate 4 rerun before offering Review Choice again.
- **Bilingual Lifecycle & Architecture Documentation** (`docs/lifecycles.*`, `docs/choosing-a-lifecycle.*`): Updates English and Vietnamese documentation, flowchart diagrams, and lifecycle guides to reflect the 3-option Review Choice workflow and local review capabilities.
- **Resilient Test Result Parsing & Archive Slug Matching** (`skills/dev-implementation/resources/scripts/result_reports.py`, `skills/dev-implementation/resources/scripts/sync_task_status.py`): Protects Dart test event parsing from malformed JSON lines or non-dict payloads, and supports interchangeable hyphens and underscores in epic directory slugs during task archival.

---

## 1.12.0 — 2026-10-19

Introduces mechanical task tamper protection, deterministic fast-model contract checks, bounded context injection, dynamic cross-model review recommendation at Gate 4, runtime skill slimming with diagram relocation to bilingual docs, and strict Python TIER-B verification.

### Added

- **Mechanical Task Tamper Guard** (`skills/dev-implementation/resources/scripts/run_task_checks.py`): Halts task execution and evidence collection (`TASK_TAMPERED_ERROR`) if active task files or their epic mirrors deviate in core sections (`Files`, `Verification`, `Definition of Done`, or `Covers`) from each other or committed `HEAD`.
- **Deterministic Fast-Model Contract Checks** (`skills/dev-implementation/resources/scripts/check_task_contract.py`): Rejects pytest `-k` expressions without exact node IDs (`path/to/test.py::test_name`), bans weak assertion patterns in BDD scenarios (`should be truthy`, `returns non-empty`), and requires non-empty grounded decisions for executable tasks.
- **Dynamic Cross-Model Review Recommendation** (`skills/dev-lifecycle/SKILL.md`): Dynamically prompts for Claude CLI or Codex CLI review at Gate 4 when fast executor models performed task execution.
- **Bounded Context Injection Protocol** (`skills/dev-designer/SKILL.md`, `skills/dev-lifecycle/references/handoff-template.md`): Establishes strict receiving-LLM execution guardrails (Bounded context, Strict spec fidelity, Zero test fakery, No contract repair) and mandatorily enforces grounded decision anchors and TOC generation.
- **Semantic Test Integrity Governance** (`skills/dev-implementation/SKILL.md`, `skills/dev-implementation/resources/scripts/audit_epic.py`): Gate 4 audit rejects reconstructed production logic in test fixtures, synthetic fixture substitutions, and wrapper exit code rewriting.

### Changed

- **Runtime Skill Slimming & Diagram Relocation** (`skills/dev-lifecycle/SKILL.md`, `skills/dev-implementation/SKILL.md`, `docs/lifecycles.*`): Slims `dev-lifecycle` below 2,500 words and `dev-implementation` below 4,500 words, removing all Mermaid fences from runtime skills while embedding synchronized bilingual state and resume diagrams in human-facing documentation.
- **Python TIER-B Requirement Enforcement** (`skills/dev-implementation/resources/scripts/check_task_contract.py`): Requires Python tasks to accompany linting with type checking (`mypy`, `pyright`, `ty`) or registered quality provider suites.
- **Pytest RED Recording Semantics** (`skills/dev-implementation/resources/scripts/run_task_checks.py`): Validates failure summaries to prevent exit 1 test selection or syntax failures from falsely recording as valid RED proof.

---

## 1.11.0 — 2026-10-18

Universalizes CRITICAL RULES across all AI Agent plugins and runtimes, restructures the Review Choice workflow into a strict post-Gate 4 verification loop, and enhances external review execution with live ANSI status streaming.

### Added

- **Universal Multi-Plugin Governance** (`rules/CRITICAL_RULES.md`): Extends mandatory critical rules to all AI Agent plugins, orchestrators, and subagents (Claude Code, Antigravity IDE, Cursor, Codex, Windsurf, OpenCode, and custom plugins) across projects and repositories.
- **Mandatory Review Choice Rule**: Strictly forbids bypassing Review Choice or auto-selecting Finish. Mandates developer choice between Finish and Cross-model review before proceeding to branch completion.
- **Live Status Streaming for Preconditions** (`skills/dev-implementation/resources/scripts/run_external_review.py`): Displays real-time ANSI status indicators and blocking step diagnostics while gathering audit and traceability facts.

### Changed

- **Looped Review Choice Workflow** (`skills/dev-lifecycle/SKILL.md`, `skills/dev-implementation/SKILL.md`): Moves Review Choice to evaluate after Gate 4 PASS (`Gate 4 PASS → Review Choice; Finish → Gate 5; Cross-model review → Gate 4 in full`). Every review round, decision, or Fix commit invalidates candidate SHA and requires a full Gate 4 rerun.
- **Lifecycle Documentation & Diagrams Synchronized** (`docs/lifecycles.*`, `docs/choosing-a-lifecycle.*`, `templates/AGENTS.md`): Updates English and Vietnamese documentation, flowchart diagrams, and templates to reflect the 5 approval gates, Handoff Choice, and post-Gate 4 Review Choice loop.

---

## 1.10.0 — 2026-10-18

Hardens the cross-model review workflow against parsing failures and malformed table rows, adds a fail-fast precondition architecture to protect API credit budgets, introduces smart hybrid diff inlining with multi-stack exclusions, and adds test quality rules prohibiting vacuous false-PASS loops.

### Added

- **Smart Hybrid Diff Inlining** (`skills/dev-implementation/resources/scripts/run_external_review.py`, `skills/dev-implementation/references/external-review-prompt.md`): Automatically inlines the filtered code diff directly into the prompt when within budget (<=1,500 lines and <=60 KB), transforming common reviews into single-turn executions while preventing prompt blowout on large changes. Full file change statistics (`git diff --stat`) are always included for complete visibility.
- **Multi-Stack Noise Excludes**: Comprehensive exclusion filters automatically omit noisy lock files, Flutter/Dart codegen (`*.g.dart`, `*.freezed.dart`), Android Gradle wrappers, Xcode metadata and assets (`*.pbxproj`, `*.xcassets`, `*.storyboard`, `*.xib`, `*.xcstrings`), Rust/Python generated protobufs/snapshots, and minified web assets from the inlined diff.
- **Fail-Fast Precondition Gates**: `collect_facts` now immediately halts execution (exit code 2 with `PreconditionFailedError`) without invoking the AI CLI if `audit_epic.py` fails, if any integration test command exits non-zero or times out, or if `check_bdd_traceability.py` fails, preventing wasted AI credits on broken builds.
- **Facts Timeout Isolation**: Added `--facts-timeout` parameter (default: 300s) separated completely from the AI reviewer CLI execution `--timeout` (default: 1800s).
- **Test Quality & Assertion Health Rule (`HLT-TEST-01`)** (`skills/code-health-audit/SKILL.md`, `skills/dev-implementation/SKILL.md`): Prohibits candidate iteration loops on build artifacts (e.g. WASM binaries, shared libraries, generated schemas) that assert conditions only inside `if path.exists()` without validating evaluated counts (`assert!(found > 0)`).

### Changed

- **Resilient Verdict & Finding Parser**: `run_external_review.py` now tolerates Markdown bold markers (`**Verdict:** PASS`), headings (`### Verdict: CHANGES REQUIRED`), and case variations. Severity tags (`Critical`, `Important`) are normalized to Title Case for case-sensitive blocking checks. `UNPARSED_BLOCKING` strictly requires bracketed tags to avoid false positives on conversational list items.
- **Table Cell Sanitization**: Strips Windows carriage returns (`\r`), converts internal newlines (`\n`) to spaces, and escapes pipe characters (`\|`) so each finding stays on exactly one table row, eliminating `unreadable findings row` failures.
- **Prompt Hierarchy & Negative Constraints**: Instructs reviewers on task-level scope vs. Gate 4 workspace quality orchestrator, compiled language TDD RED semantics, and strictly forbids bracketed severity tags in prose above the final verdict block.

### Fixed

- **Template Dollar Sign Collisions**: Switched prompt generation to `Template.safe_substitute()` so diffs containing raw shell variables (`$VAR`) or regex patterns do not crash the runner.

---

## 1.9.1 — 2026-10-16

Lets epic status synchronization handle overview documents that write the colon inside the bold label.

### Fixed

- **Epic Status lines with the colon inside the bold** (`skills/dev-implementation/resources/scripts/sync_task_status.py`): `sync_task_status.py epic <epic_dir> <status>` now rewrites `- **Status:** …` and `- **Trạng thái:** …` as well as `- **Status**: …`, so overviews written in that style no longer keep a stale Status after packaging, resuming or archiving.

---

## 1.9.0 — 2026-10-16

Makes epic tasks verifiable when they are handed to another model: a task reaches `done` only through evidence a script recorded by running the task's declared commands, traceability is proved by test results rather than identifier strings, every grader change is disclosed at Gate 4, and the developer can have the finished epic reviewed by the Claude CLI or the Codex CLI before Gate 4.

### Upgrade notes

- **Epics in flight must be retrofitted.** For a code epic (an overview with an `Integration test roots:` line), `sync_task_status.py task <id> done` now refuses a task file without a `## Verification` section with "retrofit required". Retrofit the remaining tasks through dev-designer's Updating an Existing Epic before continuing. Document epics are unaffected.
- **Run the done gate in the epic worktree.** It reads the evidence of the checkout it runs in and refuses from a checkout that lacks the task.
- **Results reports must be git-ignored** (for example `build/`), and results paths are read per file: only reports written by the current run count.

### Added

- **Task contract** (`skills/dev-designer/`): task files gain `## Files` (`Allowed files:` with `(new)` markers, `Read-only context:`), a `## Verification` table (`ID | Phase | Command | Expect | Needs`, phases `RED`/`GREEN`/`TIER-B`/`TIER-C`, `RED: n/a — <reason>`), Definition of Done bullets that reference rows or `(Gate 5)`, `## Stop and Report If` and `## Decisions Already Made`. HLDs gain `Protected paths:`, `Integration results:` and a `## Verification Environment` section. New `references/verification-rows.md` gives example rows and report commands per platform.
- **Design-time contract check** (`check_task_contract.py [--design]`): structure, grounding of paths and commands against the repository, and HLD declarations, run at dev-designer Step 3, the packaging preflight and Gate 3.
- **Evidence recorder** (`run_task_checks.py red|verify|status`): runs a task's Verification rows, checks scope against Allowed files and protected paths, and writes `.devtool/epic/<epic_dir>/evidence/<task_id>.json` with a tree fingerprint and patch-id; `status` previews the done gate.
- **Done gate** (`sync_task_status.py task <id> done`): refuses a code-epic task unless its recorded evidence matches the current table and tree, RED preceded the change, every covered identifier has a passing test case, and SCOPE passed.
- **Result-based traceability** (`check_bdd_traceability.py tests --results`, `result_reports.py`): reads JUnit XML and the Dart JSON reporter; an identifier passes only with a passed, non-skipped test case named after it.
- **Gate 4 audit** (`audit_epic.py`): checks every done task's committed evidence against its table and discloses protected-path changes, grader amendments, commits outside tasks and `(Gate 5)` items.
- **Cross-model review** (`run_external_review.py run|check`, `references/external-review-prompt.md`): after the last task, dev-implementation offers a Review Choice; the developer picks the Claude CLI or the Codex CLI, the reviewer runs read-only, rounds are recorded in `review_results.md`, and Critical or Important findings block Phase 4 until each has a decision.
- **Standard-library JUnit runner** (`scripts/run_unittest_junit.py`) for the kit's own `unittest` suites, and the epic's end-to-end and skill-text tests wired into `scripts/verify.sh`.

### Changed

- **One owner per identifier**: `check_bdd_traceability.py plan` fails an identifier named on more than one task's `Covers:` line.
- **dev-implementation**: Phase 2 records `red` and `verify` and passes the done gate before the single task commit; fixes made after the last task land as `[<EPIC>] Fix …` commits disclosed by the audit; Phase 4 runs the review check, `audit_epic.py`, the Integration results commands, `tests --results`, then `quality_check`.
- **dev-lifecycle and the handoff template**: Gate 4 criteria name the audit and result-based traceability; the packaging preflight runs the contract check; receiving agents never edit a task's grader sections.
- **subagent-driven-development**: for a task with a Verification table, the evidence file is the test evidence, implementers leave the change uncommitted, reviewers run `run_task_checks.py status`, and `review-package` gains a `WORKTREE` mode for uncommitted diffs.

### Fixed

- **Done tasks reach `done/`** (`sync_task_status.py`): `task <id> done` moves each checkout's `.devtool/features/<task_id>.md` into `.devtool/features/done/`, and back when the status leaves done, so the finishing hook's `archive-done` finds them.

---

## 1.8.1 — 2026-10-16

Tightens BDD integration traceability and epic lifecycle reliability: prevents ignored files from masking missing test coverage, accepts prose in task `Covers:` lines, reports non-UTF-8 files as usage errors, discovers remote-only epic branches before fetching, and fixes handoff staleness checks and queued packaging.

### Added

- **Lifecycle Signal Integration Tests** (`scripts/test_lifecycle_signals.py`): Standalone integration test suite testing lifecycle git signals against throwaway repositories: verifies remote branch discovery (`git ls-remote --heads`), fallback on unreachable remotes, handoff staleness check scoping against base branch, and queued epic packaging status synchronization and grep validation. Integrated into `scripts/verify.sh`.
- **Gitignore-Aware Test File Discovery** (`skills/dev-implementation/resources/scripts/check_bdd_traceability.py`): Scans integration test roots using `git -C <root> ls-files --cached --others --exclude-standard -z` so generated test reports, vendored code, and gitignored artifacts never count toward BDD scenario coverage. Falls back to directory walking when run outside a git repository.
- **Python E2E Integration Roots Default** (`skills/dev-designer/`): Adds `tests/e2e/` alongside `tests/integration/` in default integration test roots for Python projects.

### Changed

- **Fault-Tolerant Covers Parsing** (`skills/dev-implementation/resources/scripts/check_bdd_traceability.py`): Matches BDD scenario identifiers by token shape (`ID_TOKEN`) across `Covers:` lines, cleanly accepting trailing punctuation and descriptive prose (e.g., `Covers: SCN-01 (happy path), SCN-02.`) without causing false "unknown identifier" failures.
- **Strict UTF-8 Enforcement** (`skills/dev-implementation/resources/scripts/check_bdd_traceability.py`): Requires scenario documents (`.en.md`, `.vi.md`) and task files to be valid UTF-8, exiting immediately with usage code 2 and a clear error message instead of unhandled decode exceptions.
- **Direct Remote Branch Discovery** (`skills/dev-implementation/`): Entry-Point Detection checks remote branches using `for remote in $(git remote); do git ls-remote --heads "$remote" "epic/<epic_slug>"; done`, detecting epic branches pushed from other clones before any local `git fetch` runs, and falling back gracefully on unreachable remotes.
- **Handoff Staleness Scoping** (`skills/dev-lifecycle/references/handoff-template.md`): Scopes the handoff staleness check against `<base_branch>` instead of `HEAD`, preventing task commits on the epic branch from triggering false "stale handoff" warnings. Handles uncommitted designs when `auto_commit` is false.
- **Queued Epic Packaging & Review Re-Entry** (`skills/dev-lifecycle/`, `skills/dev-implementation/`): Preserves queued status when packaging epics (`Packaged (queued behind <epic>)`), allows interrupted tasks at `review` to re-enter at review verification instead of restarting implementation, and permits BDD retrofit commits to carry interrupted task status fields.

---

## 1.8.0 — 2026-10-15

Introduces automated 100% BDD-to-Test integration traceability tooling with Gate 4 verification, formalizes Stage 4 (Gate 5) Epic Handoff Choice and packaging lifecycle, and integrates entry-point detection and in-flight epic resume capabilities into `dev-implementation`.

### Added

- **BDD Integration Traceability Tooling** (`skills/dev-implementation/resources/scripts/check_bdd_traceability.py`): Standalone CLI tool with `plan` and `tests` modes enforcing 100% traceability between Gherkin BDD scenario identifiers (e.g. `[SCN-FEATURE-001]`) and executable test cases. Validates bracketed IDs, checks for stale references, and verifies test suites directly.
- **Scenario IDs and Covers Mapping in Design** (`skills/dev-designer/`): Requires all BDD scenarios to carry uppercase hyphenated scenario IDs, mandates a `Covers:` metadata line in Kanban task files, and requires Tier C BDD Automation coverage across all testable requirements.
- **BDD Traceability Enforcement in Implementation** (`skills/dev-implementation/`): Enforces that the System Integration Engineer (Tier C persona) authors an automated test for every identifier in the task's `Covers:` line. Gates task completion on `check_bdd_traceability.py tests --ids` exit 0, and runs full traceability verification before `quality_check` in Phase 4.
- **Gate 4 BDD Traceability Verification** (`skills/dev-lifecycle/`): Mandates that `check_bdd_traceability.py tests` exits 0 alongside `quality_check` PASS on the exact same commit SHA before passing Gate 4.
- **Epic Handoff Choice & Packaging Lifecycle** (`skills/dev-lifecycle/`): Introduces formal Stage 4 (Gate 5) handoff protocol with 4 explicit delivery options:
  1. *Pull Request & Review*: Push branch, open PR, and delegate to `pr_review`.
  2. *Push Branch*: Push epic branch to remote and notify user.
  3. *Local Merge*: Fast-forward / rebase merge directly to local base branch with post-merge verification.
  4. *Pack & Park*: Clean worktree, preserve branch, and archive tasks into `.devtool/epic/<epic_dir>/` for future handoff.
- **Entry-Point Detection & Epic Resume** (`skills/dev-implementation/`): Auto-detects whether an epic is starting fresh (Row 1) or resuming from an existing branch or worktree (Rows 4/6). Recreates worktrees when needed, discovers entry points, and provides BDD mapping retrofits for epics created before scenario identifiers.

---

## 1.7.1 — 2026-10-12

Enforces 100% BDD-to-Test Traceability rule across lifecycle design, implementation, and observation skills. Extends `dev-designer`, `dev-implementation`, and `writing-plans` with automated Tier C integration test suites and live web browser verification, introduces dedicated Web Frontend Tri-Persona and Python Clean Architecture support across project detection, worktree bootstrap, and 3-Tier Testing discipline.

### Added

- **100% BDD-to-Test Traceability Rule**: Enforced across `dev-designer`, `dev-implementation`, `writing-plans`, and `task-observer`. Mandates that 100% of BDD scenarios (`[Tier A - Unit]` and `[Tier C - Integration]`) in `bdd_scenarios.*.md` and task files map 1-to-1 to executable test cases; tasks and epics cannot be marked complete without full test suite coverage.
- **Web Frontend Tri-Persona Architecture** (`skills/dev-implementation/`): Introduces specialized Web Tri-Persona execution blocks (`##### 🌐 If Project Type is web:`) specifying `node --test` / Vitest for Tier A unit testing, `tests/e2e` host integration suites for Tier C, and live web browser verification via `browser_subagent` recording video (`.webp`) and screenshot artifacts.
- **Python Project Detection & Worktree Bootstrap** (`skills/dev-implementation/resources/scripts/`): Extends `detect_project_type.sh` to recognize Python environments (`pyproject.toml`, `setup.py`, `Pipfile`, `requirements.txt`), and `bootstrap_worktree.sh` to synchronize dependencies using `uv sync` (with fallback to `poetry install` or `pip install -r requirements.txt`).
- **Python 3-Tier Testing Standard & Tri-Persona** (`skills/dev-designer/`, `skills/dev-implementation/`): Integrates Python into the canonical 3-tier testing standard:
  - **Tier A (Unit Tests)**: `pytest tests/unit/` using `pytest-mock` and `unittest.mock`.
  - **Tier B (Tooling & Governance)**: Ruff formatting and linting (`ruff check .`, `ruff format --check .`), strict Mypy type-checking (`mypy --strict src`), and architectural boundary validation (`lint-imports`).
  - **Tier C (Acceptance & Integration)**: `pytest tests/integration/` and `pytest tests/e2e/`.
  - **Python Tri-Persona**: Red Team QA, Principal Backend Engineer (TDD Master), and System Integration & E2E Engineer.

---

## 1.7.0 — 2026-10-12

Introduces dedicated Python quality check provider (`d3nexus:python-quality-check`) with capability schema, manifest validator, and architectural governance via `import-linter`. Extends the automated onboarding engine (`setup_quality_check`) to detect Python projects (`pyproject.toml`, `uv.lock`, `requirements.txt`, etc.), and integrates Python into the multi-provider end-to-end acceptance test suite.

### Added

- **`python-quality-check`** (`skills/python-quality-check/`): dedicated provider for Python environments (`uv`, standard `python -m`, and `pytest`). Enforces Ruff formatting compliance (`uv run ruff format --check .`), Ruff static analysis (`uv run ruff check .`), strict Mypy type-checking (`uv run mypy --strict src`), Clean Architecture layer boundaries via Import-Linter (`uv run lint-imports`), Pytest unit test suites, and line coverage thresholds.
- **Python Quality Capability Schema & Validator** (`skills/python-quality-check/resources/schemas/python-quality.schema.json`, `validate_python_quality.py`): machine-readable JSON Schema and standalone CLI validator enforcing capability contracts and authoritative architecture checks for epic profiles.
- **Python Scaffolding Support** (`skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`): auto-detects Python codebases via root markers (`pyproject.toml`, `uv.lock`, `requirements.txt`, `setup.py`, `Pipfile`), generates `.agents/quality/python-quality.json`, and registers `python-core` in `check_quality.json`.
- **Python Acceptance Verification** (`skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`): end-to-end multi-provider acceptance test verifying Python provider registration, result reconciliation, and executive report emission.

---

## 1.6.0 — 2026-10-12

Introduces dedicated quality check providers for Flutter, Android Native, and iOS Native modeled on canonical digital wallet architecture templates, hardens quality contracts against false-PASS vulnerabilities and candidate SHA drift, and introduces an automated onboarding scaffolding engine.

### Added

- **`flutter-quality-check`** (`skills/flutter-quality-check/`): dedicated provider for Flutter and Melos multi-package workspaces modeled after `bloc_digital_wallet`. Enforces Dart formatting (`dartfmt.sh`), static analysis (`fvm flutter analyze`), Clean Architecture module boundaries (`check_module_boundaries.sh`), license headers (`check_license_header.sh`), package tests (`melos run test`), and LCOV coverage thresholds (`testWithCoverage.sh`).
- **`android-quality-check`** (`skills/android-quality-check/`): dedicated provider for Android Gradle multi-module codebases modeled after `android_digital_wallet`. Enforces Spotless formatting (`spotlessCheck`), Detekt static analysis (`detekt`), Binary Compatibility Validator (`apiCheck`), Konsist architectural governance (`:konsist-test:test`), unit testing (`testDebugUnitTest`), Jacoco coverage (`jacocoTestReport`), and Gradle daemon cleanup (`pkill -9 java`).
- **`ios-quality-check`** (`skills/ios-quality-check/`): dedicated provider for iOS Tuist and SwiftPM workspaces modeled after `ios_digital_wallet`. Enforces SwiftFormat (`swiftformat`), strict SwiftLint (`swiftlint`), ArchTests AST architectural governance (`swift test --package-path ArchTests`), framework boundary validation (`check_module_boundaries.sh`), unit testing (`swift test`), and profdata code coverage thresholds (`check_coverage_thresholds.sh`).
- **`setup_quality_check`** (`skills/setup_quality_check/`): automated scaffolding engine and operational skill that inspects repository roots, auto-detects project platforms (Flutter, Android, iOS, Rust, and Polyglot composites), and generates standardized `.agents/quality/check_quality.json` and platform capability manifests with zero configuration friction.
- **Multi-provider end-to-end acceptance test suite** (`skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`): tests pure platform workspaces, composite repositories, and False-PASS vulnerability elimination.

### Changed

- **Quality contract validator (`validate_quality_contract.py`)**: hardened against False-PASS vulnerabilities F1–F3. Reject top-level PASS when checks fail (`contract_violation`), reject top-level PASS with sub-threshold coverage (`coverage_deficit`), reject stale candidate SHAs (`repository_sha_mismatch`), and reject empty command arrays (`command_array_empty`).
- **Result aggregator engine (`aggregate_quality_results.py`)**: synthesizes BLOCKED provider records for missing required providers and demotes contradictory provider results to BLOCKED.
- **Pre-release verification harness (`scripts/verify.sh`)**: step 13 now runs contract, schema, aggregation, Rust, Flutter, Android, iOS, scaffolding, and end-to-end acceptance test suites.

---

## 1.5.0 — 2026-10-09

Makes integrating a development branch safe: conflicts are resolved on the branch, inside its
worktree, and the base branch only ever receives a `--no-ff` merge of the exact tree that passed
verification — at finish time and after every epic task.

### Added

- **`integrate_branch.py`** (`finishing-a-development-branch/resources/scripts/`): a standard-library
  CLI with five commands — `sync-base` (fetch, fast-forward a local base that is behind, stop on
  divergence), `preflight` (read-only report of upstream commits and epics, overlap files, predicted
  tier, regenerate and manifest flags), `rebase` (backup ref, rerere, `--continue` / `--abort`),
  `verify-tier` (measures `noop` / `clean` / `conflicts` from zero-context net diffs) and `land`
  (`--no-ff` merge of the verified sha with pre- and postcondition checks and rollback). Exit codes
  0–4. Hardened against user git config (`rebase.updateRefs`, `rerere.autoUpdate`,
  `log.showSignature`, `core.quotePath`).
- **38 CLI tests** against temporary repositories, run by `scripts/verify.sh` step 12.
- **Conflict playbook** (`finishing-a-development-branch/references/conflict-playbook.md`): the
  `--ours` / `--theirs` reversal during a rebase, and the regenerate / Kanban-mirror / mechanical /
  semantic classification with a stop-and-ask template.

### Changed

- **`finishing-a-development-branch`**: Options 1 and 2 run *Update onto Base* — preflight, rebase
  in the worktree, re-bootstrap when manifests changed, verify by measured tier — and Option 1 lands
  through `integrate_branch.py land` instead of `git checkout <base> && git pull && git merge`. An
  already-pushed branch is never rebased.
- **`dev-implementation`**: new Phase 2 step 7 integrates the epic branch with `develop` after every
  task, with lighter task-boundary verification. Phase 1 runs `sync-base` before creating the
  worktree, and the Gate 3 checkpoint asks once for permission to fast-forward `develop`.
- **`dev-lifecycle`**: a Gate 4 🟢 belongs to the SHA it ran on; Stage 4 rebases, re-verifies by
  tier and lands with `--no-ff`.

### Fixed

- The pre-finish archival hook looked for `sync_task_status.py` only in the repository and the
  Antigravity install, so under Claude Code it skipped archival silently. It now resolves the script
  through `SKILL_DIR` and stops loudly when it is missing.
- Restoring the main checkout before archival re-dirtied it and aborted the first merge. Archival
  copies are now restored only when `land` names them as colliding, after archival.

---

## 1.4.3 — 2026-10-04

Standardizes modern Mermaid diagram syntax, Graphviz DOT conventions, and Markdown lint rules across the development and document lifecycles.

### Added

- **Modern Mermaid syntax standard**: Mandates `flowchart` over deprecated `graph` syntax, enabling per-subgraph `direction` controls, richer styling, and AST stability. Requires enclosing node labels with special characters (parentheses, brackets, colons) in double quotes.
- **Graphviz (DOT) conventions**: Enforces semantic node shapes (`box`, `diamond`, `cylinder`, `ellipse`), statement terminating semicolons, quoted labels, and `cluster_` subgraph naming.
- **Markdown linting standards**: Enforces single H1 (MD025), sequential heading increments (MD001/MD003), spaces after `#` (MD018), and mandatory language tags on fenced code blocks (MD040).
- **Automated mechanical validation**: Extended `check_document.py` with AST checks for legacy Mermaid `graph`, unquoted special-character labels, missing fence language tags, heading whitespace, and DOT statement syntax.
- **Regression test coverage**: Added unit tests in `test_check_document.py` validating detection of legacy Mermaid syntax, untagged code fences, and heading format issues.

### Changed

- **`dev-lifecycle` and `doc-lifecycle`**: Integrated Markdown and modern diagram standards directly into their Document Contracts, Gate criteria, and Red Flags.
- **`dev-designer`**: Updated Step 1 architecture prompt to default to `mermaid flowchart TD` (explicitly prohibiting legacy `graph TD`).
- **`dev-brainstorming`, `doc-brainstorming`, `writing-plans`, `doc-designer`, `doc-implementation`, `doc_quality_check`, `brainstorming`, and `decision-records`**: Added explicit diagram and markdown lint rules into drafting guidelines and self-review checklists.

---

## 1.4.2 — 2026-10-03

Makes bilingual, navigable design documentation a verified contract across the development and
document lifecycles.

### Added

- **Bilingual lifecycle artefacts**: specs, HLD/overview documents, BDD scenario documents,
  non-epic implementation plans, document outlines, and published documents now require a
  canonical English `.en.md` file and a synchronized Vietnamese `.vi.md` translation.
- **Complete table-of-contents contract** for every lifecycle document regardless of length.
  Implementation plans must also link every `### Task` heading.
- **Lifecycle document regression tests** covering missing translations, omitted variants,
  heading-structure drift, incomplete tables of contents, short documents, and decorated ToC
  headings.

### Changed

- **`dev-designer`** now generates bilingual HLD and BDD scenario pairs; `writing-plans` generates
  bilingual implementation-plan pairs. Kanban `task_*.md` files remain English-only.
- **`dev-brainstorming`, `doc-brainstorming`, `doc-designer`, and `doc-implementation`** now create,
  synchronize, and mechanically verify both language variants before their approval gates.
- **`dev-lifecycle` and `doc-lifecycle`** explicitly carry the bilingual and ToC requirements in
  their handoff contracts and red flags.
- **`doc_quality_check`** now requires both variants in the same run, checks heading-shape parity,
  verifies complete ToC coverage, and audits semantic translation parity.
- **`dev-implementation`** consumes `bdd_scenarios.en.md` as the canonical behavioral contract.

### Verification

- `scripts/verify.sh` now runs the lifecycle document contract suite as a release gate.

---

## 1.4.1 — 2026-10-02

Adds a mandatory critical rule prohibiting unauthorized remote git push operations and improves worktree bootstrapping resilience.

### Added

- **Git push operations guard** in `rules/CRITICAL_RULES.md`, strictly prohibiting agents from running `git push` to remote repositories without explicit user permission or confirmation.

### Fixed

- **Worktree bootstrap script** (`bootstrap_worktree.sh`) now falls back to locating `copy_secure_files.sh` directly within the installed plugin directory when not vendored in `.agents/`.
- **Kanban task status synchronizer** (`sync_task_status.py`) falls back to `sanitize_slug(epic_dir)` to prevent lookup failures during task synchronization.

---

## 1.4.0 — 2026-09-28

Adds Codex distribution while keeping one shared skill library for Codex, Claude Code, and
Antigravity.

### Added

- **Codex plugin manifest** at `.codex-plugin/plugin.json`, with discovery metadata, starter
  prompts, and the existing `skills/` directory as its skill source.
- **Codex installation and update instructions** in the README, including the distinction
  between GitHub marketplace distribution and submission to OpenAI's public Plugins Directory.
- **Codex tool mapping** in `using-superpowers`, covering skill loading, file and shell tools,
  optional subagents, and explicit rule loading through a project's `AGENTS.md`.

### Changed

- The shared `.agents/plugins/marketplace.json` uses a local source path at the repository root,
  so Codex resolves the plugin from the checked-out marketplace.
- Project scaffolding includes Codex installation commands and explicit instructions to read
  rules from the project or installed plugin. The bootstrap hook directs agents to the runtime
  tool mapping instead of assuming Claude's `Skill` tool exists.
- `release.sh` requires dated release notes and a newer version, releases from `main`, and keeps
  the root, Claude, and Codex manifests plus Claude marketplace versions synchronized. It
  verifies again after the bump and prints Codex refresh commands.
- `verify.sh` checks Codex metadata, shared skill paths, marketplace identity, version agreement,
  dated release notes, and README anchors in addition to the existing checks.

### Fixed

- Claude marketplace metadata still advertised `1.3.0` after the plugin reached `1.3.1`.
- The shared marketplace described `./` as a remote URL instead of a local plugin path.

### Upgrading

Install in Codex:

```bash
codex plugin marketplace add DanhDue/ai-agent-tools
codex plugin add d3nexus@danhdue-agent-tools
```

Start a new thread after installation. Existing consuming projects should merge the **Rules**
section from [templates/AGENTS.md](templates/AGENTS.md) so Codex reads the kit's rule files.
Claude Code and Antigravity users can use their existing update commands.

---

## 1.3.1 — 2026-09-18

Adds planning-mode interception guards to prevent agents from bypassing the d3nexus workflow
by writing `implementation_plan.md` directly (the Antigravity native planning artifact).

### Changed

- **`dev-lifecycle`**: Added `<HARD-GATE>` prohibiting `implementation_plan.md` creation.
  Added 2 new Red Flags (writing `implementation_plan.md`, skipping brainstorming).
  Added Rationalization Table covering 5 common bypass excuses.
- **`dev-brainstorming`**: Expanded `<HARD-GATE>` to explicitly cover `implementation_plan.md`
  as a gate bypass.

---

## 1.3.0 — 2026-09-17

Splits `brainstorming` into a development variant and a documentation variant, and makes the
document lifecycle's inception stage mandatory.

### Added

| Skill | What it does |
|---|---|
| `dev-brainstorming` | Turns an idea for code work into an approved design spec. The former `brainstorming`, with the document branch removed. Keeps the visual companion and its server scripts |
| `doc-brainstorming` | Turns an idea or a document request into an approved content spec. Written around what a document must say rather than around architecture. No visual companion |

- **`scripts/verify.sh` gains step 10.** It fails when either orchestrator names the `brainstorming`
  router instead of a concrete variant. The check is scoped to the two orchestrators and to the two
  forms that denote the skill, because `brainstorming` is also an ordinary English word and a
  repo-wide sweep like step 9's would fire on four legitimate uses.

### Changed

- **`brainstorming` is now a router.** It keeps its name and path, holds one question — idea,
  document, or coding — and invokes the matching variant. It has no default: an unclear answer is
  asked about again rather than guessed at. Everything that names `d3nexus:brainstorming` today
  keeps working, including the session-start hook and `rules/CRITICAL_RULES.md`.
- **`doc-lifecycle` Stage 0 is mandatory, and the gates renumber from three to four.** Gate 1 is now
  spec approval; the former gates 1, 2 and 3 become 2, 3 and 4. The stage was optional, and its skip
  condition asked whether the content was already known — a question an agent answers yes to
  essentially always. The stage is now required to *happen* while its depth still scales, so a
  runbook's spec is three sentences.
- **The upstream escape to `lean-product-lifecycle` splits asymmetrically.** `dev-brainstorming`
  keeps the original trigger. `doc-brainstorming` fires only when the document *is* a product
  argument whose idea has no evidence; a runbook or reference page never triggers it.
- **Each variant can correct a misroute to its sibling**, using the existing test: if the work
  changes a file that ships in the build, it is code.
- `dev-lifecycle` Stage 1 now names `dev-brainstorming`; its five gates and stage order are
  unchanged.
- Stage entry in both orchestrators is now imperative — a stage is entered by invoking its skill,
  not by reading its description and doing the work. `dev-lifecycle` had never contained the word
  "invoke", which is why agents skipped Gate 1.
- Guidance in `dev-brainstorming` that leaned toward code is no longer branch-conditional, since the
  branch is gone.

### Fixed

- Fifteen stale `doc-lifecycle` gate numbers across `doc-designer`, `doc-implementation` and
  `doc_quality_check`, left wrong by the renumber.
- A dead path in `dev-brainstorming` to `skills/brainstorming/visual-companion.md`, which the rename
  broke at exactly the point where the user had just accepted the visual companion.
- A claim in `dev-brainstorming` that `dev-lifecycle` has four approval gates. It has five.

### Upgrading

No action is required. `d3nexus:brainstorming` still resolves, and now asks which kind of work you
want before routing. Name `d3nexus:dev-brainstorming` or `d3nexus:doc-brainstorming` directly to
skip the question. Anything that quotes `doc-lifecycle` gate numbers needs re-reading: they shifted
by one.

---

## 1.2.0 — 2026-09-17

Adds the **Document Lifecycle Suite**: work whose deliverable is a document now has its own
lifecycle, its own quality gate and its own stage skills, instead of being forced through gates
built for code.

### Added

| Skill | What it does |
|---|---|
| `doc-lifecycle` | Orchestrates document work through three gates — brief and outline, verification, sign-off |
| `doc-designer` | Establishes the audience, classifies the document into exactly one Diátaxis type, produces the outline and the section breakdown |
| `doc-implementation` | Drafts section by section, one commit each, reusing the existing Kanban machinery unchanged |
| `doc_quality_check` | The documentation quality gate: refusal rule, mechanical checks, type conformance, content audit |
| `decision-records` | Architecture Decision Records in Michael Nygard's format, plus spike reports |

- **`brainstorming` gains two exits.** It now routes to `doc-designer` for document deliverables, and
  **upstream** to `lean-product-lifecycle` when the problem space was never validated — a route that
  did not previously exist in that direction.
- **`scripts/verify.sh` gains two checks.** Step 8 fails when a skill's own supporting file is
  referenced by nothing; it found seven pre-existing orphans on its first run, including a second
  reviewer prompt that had never been wired in. Step 9 fails when a live file still names a
  pre-rename skill.
- **`docs/lifecycles.en.md`** — reference: what each lifecycle is for, what it produces, and its
  process flow. **`docs/choosing-a-lifecycle.en.md`** — how-to: picking one for a specific piece of
  work, including when to skip all of them. Both carry a Vietnamese variant.
- **`docs/adr/`** — decision records for this repository, starting with why the documentation
  quality gate is a separate skill.
- **`evals/doc-designer/mixed-mode-material`** — the first ablation case for a documentation skill.
  Arm A 5/5, arm B 2/5. The report leads with where the baseline beat the skill.

### Changed

- **`rules/CRITICAL_RULES.md`** now selects the quality gate by the kind of work: `@quality_check`
  for anything that changes a file shipping in the build, `@doc_quality_check` for prose. The
  previous mandate was unsatisfiable for a Markdown deliverable.
- **`skills/quality_check/SKILL.md` is unmodified.** The documentation gate is a separate skill
  precisely so that the gate guarding every merge in every project did not have to change.

> [!CAUTION]
> **Breaking.** Three skills are renamed. `/d3nexus:epic-lifecycle`,
> `/d3nexus:epic-designer` and `/d3nexus:epic-implementation` no longer resolve, and any
> per-project `AGENTS.md` naming them must be updated.

### Renamed — the development lifecycle

"Epic" becomes the umbrella term covering both development and documentation work, so the
development lifecycle takes a name that distinguishes it:

| Old | New |
|---|---|
| `epic-lifecycle` | `dev-lifecycle` |
| `epic-designer` | `dev-designer` |
| `epic-implementation` | `dev-implementation` |

Each renamed skill keeps the word "epic" in its `description`, so a request phrased as epic-scale
work still activates it. `finishing-a-development-branch` and the directory `.devtool/epic/` are
unchanged — both kinds of epic live there, distinguished by a `Kind:` field. There is no data
migration, and the historical epic records under `.devtool/` deliberately keep the old names.

### Changed — source fidelity

- `check_source_fidelity.py` becomes a multi-source registry instead of a Lean-Product-only guard,
  and `verify.sh` step 7 is retitled accordingly.

---

## 1.1.1 — 2026-09-17

Strengthens the `quality_check` master governance skill by making Tier B zero-tolerance explicit and introducing Tier C2 Native Build Smoke Testing.

### Changed — quality_check

- **Tier B Zero-Tolerance Enforcement**: Formally documents that all analyzer errors, compiler warnings, module boundary leaks, formatting issues, and license headers must be 100% resolved (0 errors, 0 warnings).
- **Tier C2 Native Build Smoke Gate**: Adds an explicit binary compilation check (`flutter build apk --debug`, `./gradlew assembleDebug`, `xcodebuild build`) to Tier C before merging, closing the blind spot where headless tests pass but native binary assembly fails.
- **Reporting**: Updates the 3-Tier Automated Test Results table to track Tier C1 (Integration Flows) and Tier C2 (Native Build Smoke Gate) separately.

---

## 1.1.0 — 2026-09-16

Adds the **Lean Product Lifecycle Suite**: four skills covering upstream product discovery, for
deciding *what to build and for whom* before `epic-lifecycle` takes over the engineering. Also adds
a reusable harness for measuring whether a skill changes agent behaviour at all.

### Added — Lean Product Lifecycle Suite

Four skills implementing Dan Olsen's Lean Product Process, grounded in *The Lean Product Playbook*
(Wiley, 2015).

| Skill | Covers | Produces |
|---|---|---|
| `lean-product-lifecycle` | Orchestration, three human gates, five guardrails | routes the other three |
| `lean-market-discovery` | Steps 1–2: target customer, underserved needs | `01_problem_space_spec.md` |
| `lean-value-strategy` | Step 3: Kano classification, competitive grid | `02_value_proposition_spec.md` |
| `lean-mvp-scoping` | Step 4: chunking, ROI, MVP candidate grid | `03_mvp_feature_backlog.md` |

Artefacts land in `.devtool/product/<slug>/`. The Gate 3 backlog is consumed directly by
`epic-designer`.

Process steps 5 (build an MVP test) and 6 (test with customers) are **not implemented**. The
orchestrator says so at Gate 3 rather than implying the journey is complete.

### Added — skill ablation harness (`evals/`)

Measures whether a skill changes behaviour, rather than whether an agent holding it can recite it.
Each scenario runs with the skill, without it, and optionally with the pre-correction rules; a third
agent grades all arms blind against a rubric that cites the book rather than the skill.

Five reusable cases, a protocol, and pre-correction fixtures. Not wired into `verify.sh` — each run
costs real agent invocations, so it belongs at release time or after a skill is edited.

### Added — source-fidelity regression gate

`scripts/check_source_fidelity.py`, wired into `scripts/verify.sh` as step 7. Fails the build if any
of six corrected errors reappears in `skills/lean-*/` or `docs/books/`. Every rule was confirmed to
fire on an injected regression.

### Fixed — six errors in the documentation this suite was derived from

The suite was originally specified from three LLM-written summaries in `docs/books/`, not from the
book. Reading the primary source found six behaviour-changing errors that had propagated through
four layers of artefacts. All are corrected in `docs/books/` at source, with provenance headers
naming the book as the authority. Evidence with the author's wording:
`.devtool/epic/lean_product_suite/source_fidelity_review.md`.

| Was | Is |
|---|---|
| "MVP = ROI cells 1–3" | All must-haves enter v1 regardless of ROI rank |
| Guardrail 1 forbids solution-space talk | Capture, convert, park — Olsen's rule is *separate and alternate* |
| 6-layer PMF Pyramid | 5-layer Pyramid **and** a separate 6-step Process; UX is the top layer |
| Gate 1 bar `OS >= 10` | `> 15` attractive · `10–15` marginal · `< 10` unattractive |
| Importance and Satisfaction both 1–10 | 5-point unipolar / 7-point bipolar, normalized before use |
| 3×3 grid is the ROI method | Numeric ROI is primary; the grid is Olsen's declared fallback |

"Cupcake MVP" was also removed as an attribution error — Figure 7.1 is adapted from **Jussi
Pasanen**; the cupcake metaphor is Brandon Schauer's and does not appear in the book.

### Known limitations

Stated because they change how much to trust this suite, not as boilerplate.

- **No measured advantage over an unaided agent.** Two scenarios were ablated with a blind judge.
  Both scored **0 delta** — a competent agent without the skill reached the same decisions. The
  process layer (gates, artefacts, session resumption) is untested and is where the value plausibly
  sits, but that is a belief, not a measurement.
- **One correction has measured value, one does not.** Against an arm carrying the pre-correction
  rules: the `OS >= 10` and scale corrections scored **+3**; the `cells 1–3` correction scored
  **0**, because the agent overrode the broken rule unprompted.
- **`lean-value-strategy` and `lean-product-lifecycle` have never been ablated.** Three of five
  cases are unrun.
- **n = 1 per arm.** `evals/protocol.md` requires three runs before a result is cited as settled.
- Results and full reasoning: `evals/results/2026-09-16-baseline/report.md`.

### Notes

- Skill count 42 → 47.
- `evals/` must stay outside `check_source_fidelity.py`'s glob — its fixtures deliberately contain
  the corrected errors.
