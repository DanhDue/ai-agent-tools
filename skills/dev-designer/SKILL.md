---
name: dev-designer
description: Use when analyzing high-level requirements to design a complete software Epic across Web Applications, Flutter, Android Native, iOS Native, Python, or Rust projects, including High-Level Design (HLD), Mermaid diagrams, Integration Test Plans, and Kanban task breakdowns with BDD & TDD specifications.
---

# Development Designer

## Overview
Transforms high-level requirements or approved `dev-brainstorming` specs into an Epic HLD, Integration Test Plan, exhaustive BDD suite, and LachyFS Kanban task contracts for **Web Applications**, **Flutter**, **Android Native**, **iOS Native**, **Python**, and **Rust Core / Polyglot** repositories.

This skill is **Stage 2** of [`dev-lifecycle`](../dev-lifecycle/SKILL.md), enforcing Gate 2 (task breakdown confirmed) before writing task files. Full YAML templates, `task_01` Hub/Satellite worked layouts, Mermaid parallel tracks, and per-platform testing matrices live in [`references/task-template-examples.md`](references/task-template-examples.md).

## Input
Starts either from a raw user requirement or an approved `dev-brainstorming` spec relocated into `.devtool/epic/<epic_name>/` (each sub-project spec becomes its own epic). Treat an approved spec as the SSOT for `Decisions Already Made`; record a same-directory link back to the source spec in Meta Data and inspect `## Shared Contract Warnings` to preserve all Stage 1 human-approved contract choices.

## Workflow Instructions

### Step 0: Detect Target Platform & Polyglot Bootstrap
Detect platform via root manifests (`package.json`, `pubspec.yaml`/`melos.yaml`, Gradle files, `Project.swift`/`Tuist.swift`/`Package.swift`, `pyproject.toml`, `Cargo.toml`). For polyglot repos, `detect_project_type.sh --all` + `bootstrap_worktree.sh` run sequentially (`.agents/quality/python-quality.json` supports an optional `"bootstrap"` command array).

### Step 1: Create the Epic Overview Document (`HLD`) & BDD Suite
Write artifacts inside `.devtool/epic/<epic_name>/`, strictly separating audiences:
1. **HLD (`<epic_name>.en.md` + Stage 4 companion `<epic_name>.vi.md`)**: Human overview & "Prompt to Maintain" map — Table of Contents (linking every `##`), Meta Data (stamp creator `- **PIC**: <profile>` resolved via `python3 scripts/resume_context.py --detect-profile`, Platform, `Depends on epic`, `Source Spec`), Background, Goals & Non-Goals, Architecture (`mermaid flowchart TD`/`LR` only — never `graph`; conditional `sequenceDiagram` only for multi-actor/async/IPC flows), Feature Maintenance Map, Rollout Strategy, Kanban Tasks Breakdown, and symmetric `[SE-NN]` `## Spec Errata`. Do **not** embed raw Gherkin blocks inside the HLD. All internal design/task prose, plans, code comments, and commits MUST be strictly in **English**.
2. **Option A Bilingual Authoring**: Write `<epic_name>.en.md` and `bdd_scenarios.en.md` first as English SSOT during Stages 1–3. Generating/delta-syncing `bdd_scenarios.vi.md` and final `<epic_name>.vi.md` parity is deferred to Stage 4 Pre-Finish (`--strict-bilingual`); whenever both variants exist before Gate 2, verify them mechanically with:
   ```bash
   python3 skills/doc_quality_check/resources/scripts/check_document.py \
     --require-toc --require-bilingual \
     .devtool/epic/<epic_name>/<epic_name>.en.md \
     .devtool/epic/<epic_name>/<epic_name>.vi.md
   ```
   (Run with `--require-toc` on `bdd_scenarios.en.md`, plus `bdd_scenarios.vi.md` once generated.)
3. **Check 1 (Shift-Left Impact Analysis)**: Run `check_code_impact.py --files <planned_files> --symbols <core_classes> --base-ref develop` to scope blast radius before freezing contracts.
4. **Integration Test Plan & Verification Environment**:
   Include `## Verification Environment` (data isolation, forbidden live stores, `Needs` vars; first task carries a live-store sentinel row if applicable) plus these exact lines:
   - `Integration test roots: <dirs>` — defaults: `tests/e2e/` (Web), `integration_test/` (Flutter), `app/src/test/` and `shell/src/test/` (Android), `App/Tests/` and `Shell/Tests/` (iOS), `tests/integration/` and `tests/e2e/` (Python), `tests/` (Rust).
   - `Protected paths: .agents/quality/**, .devtool/epic/<epic_name>/bdd_scenarios.en.md, .devtool/epic/<epic_name>/bdd_scenarios.vi.md`
   - `Integration results: <level-2 blast-radius command> -> <report_path>` (and optional `Integration results (live, needs: VAR1): <cmd> -> <path>` for opt-in suites). Level 3 full-repo test runs execute only at Stage 4 before landing.
5. **Shared Contract Impact**: Inspect `shared-contracts/` (`physical` = Hub Mode -> Contract Owner Persona; `symlink` = Satellite Mode -> Consumer Persona). Read Triad (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`), guarantee non-breaking backward-compatible schemas, and document findings in `## Shared Contract Impact` (`None — self-contained feature` if unaffected).
6. **Adversarial BDD Suite (`bdd_scenarios.en.md`, later synced to `bdd_scenarios.vi.md`)**: Organize across all 5 dimensions (`HP`, `EC`, `ST`, `AR`, `FR`) prioritizing boundary/fault cases with linked ToC and bracketed IDs `Scenario: [<EPIC>-<DIM>-<NN>] [Tier A - Unit | Tier C - Integration] ...`. Verify prefix uniqueness via `grep -ho '\[[A-Z][A-Z0-9]*-' .devtool/epic/*/bdd_scenarios.en.md | sort -u`.

### Checkpoint: Confirm Task Breakdown Before Writing Task Files
Present a short numbered task list (title, one-line scope, assigned `Covers:` IDs, and `review_tier`) for user confirmation before writing `task_*.md`.
- **`task_01` Contract-First Rule**: If `shared-contracts/` is impacted, `task_01` MUST run first — Hub Mode updates canonical contracts and emits a Parallel Handoff Summary; Satellite Mode updates internal DTOs/adapters (never adding `shared-contracts/...` to `Allowed files`, see `references/task-template-examples.md` for interactive cross-repo Hub commits and `sync_contracts.py ack`).
- **Concurrent-Epic Backlog Rule**: Check `.devtool/features/*.md` (excluding `done/` and `archived/`) for active (`todo`/`in-progress`/`review`) tasks in another epic. If present, generate new tasks as `status: "backlog"` and mark Meta Data `Status: Queued (backlog) — behind <epic>`.

### Step 2: Generate LachyFS Kanban Tasks
Write each task to `.devtool/features/task_<number>_<name>.md` and mirror to `.devtool/epic/<epic_name>/task_<number>_<name>.md`. **Task files are English-only** — never create `.vi.md` task variants or mix Vietnamese prose.

Each task must include:
1. **Frontmatter & Selective `task-reviewer` Gating**: Include `review_tier: "full"` in task YAML frontmatter when a task modifies `> 2` non-test modules OR carries high-risk labels (`security`, `architecture`, `concurrency`, `contract`); omit `review_tier` (or set `"skip"`) for trivial single-file tasks so Stage 3 skips `task-reviewer`.
2. **Epic Reference, Requirement Analysis & Files**:
   - `Allowed files:` Exact paths/globs (`(new)` if created; no bare directories; never `.devtool/` mirrors/evidence unless updating a protected path; never `shared-contracts/` in Satellite Mode). For the final Tier C task, include `.agents/contract_sync.json` (for `sync_contracts.py ack`) and `.agents/contract_map.json` when using path waivers.
   - `Read-only context:` Paths read only (may carry `(new)` for upstream outputs).
   - **Surgical `target_files` Anchors**: Under `## Impact Analysis & Blast Radius`, whenever a task modifies an existing file `> 200` lines, annotate each target file with exact target symbol names plus line ranges `(L<start>-L<end>)` so implementers run bounded reads immediately.
3. **3-Tier & 3-Level Test Scope Pyramid**: Structure `Level 1` task-scoped `Task 1..N-1` rows (`Allowed files` only — never whole-repo `ruff`/`mypy`/`pytest`), `Level 2` blast-radius `Task N` integration rows + fast mechanical gates (`check_anti_stub.py`, `verify_importlinter_coverage.py`, `lint-imports`, `verify_bdd_coverage.py`, `pre_review_self_probe.py`), and `Level 3` full suite at Stage 4. Every scenario in `bdd_scenarios.en.md` MUST be covered by **at least one automated integration test** under `Integration test roots` carrying the scenario ID, assigned through `Covers:` to **exactly one task** (final Tier C task sweeps any remaining IDs). Unit mocks never substitute for Tier C integration tests.
4. **BDD Scenarios (`### BDD SCENARIOS`)**: Directly under `### BDD SCENARIOS`, write `Covers: <ID>, <ID>` (omit only on non-scenario tooling tasks) and copy exact `Given / When / Then` blocks verbatim from `bdd_scenarios.en.md`. Pin assertions to concrete production outputs/indices/timestamps — vague assertions (`should be truthy`, `is valid`, `should work`, `returns non-empty`) are rejected by `check_task_contract.py --design`.
5. **Verification Table (`## Verification`)**: Use columns `ID | Phase | Command | Expect | Needs` with phases `RED`, `MEASURE` (writing declared `Evidence files:`), `GREEN`, `TIER-B`, `TIER-C`. Follow [`references/verification-rows.md`](references/verification-rows.md) and [`references/verification-row-grammar.md`](references/verification-row-grammar.md).
   - Every pytest `RED` row MUST target an exact node ID (`path/test_file.py::test_name`), expect `exit 1`, and require test failure output (`-k` without a node ID is rejected).
   - Pure refactor/doc/config tasks with no runtime behavior omit `RED` rows and place `RED: n/a — <reason>` right under the table.
   - Place `## Stop and Report If` directly below the table with the five default escalation bullets (see `references/task-template-examples.md`).
6. **`## Decisions Already Made`**: Inline exact production signatures, defaults, constants, and caller-to-callee chains (`Source:` grounded vs `New contract:`). For executable tasks (`RED` or `GREEN` rows), `Decisions Already Made` **must not be empty or write `None`**; only non-behavioral doc tasks may write `None`.
7. **`## Definition of Done` & Links**: Every DoD bullet ends with verifying row IDs `(V2, V4)` or `(Gate 5)` for human review; include `Blocked by [Task N](...)` and rollback notes.

### Step 3: Finalize, Readiness Check & Gate 2 Handoff
1. Run single-pass readiness and replay verification against epic task mirrors (never `.devtool/features/`):
   ```bash
   python3 "$SKILL_DIR"/../dev-implementation/resources/scripts/check_epic_readiness.py <epic_name> [--baseline]
   python3 "$SKILL_DIR"/../dev-implementation/resources/scripts/check_epic_readiness.py <epic_name> --replay
   ```
   (Isolate failures with `check_bdd_traceability.py plan` and `check_task_contract.py --design`.) Both must exit 0 before committing.
2. If `.agents/config.json` sets `auto_commit: true`, stage only `.devtool/epic/<epic_name>/` and generated `.devtool/features/task_*.md`, committing per [Commit Message Format](../../rules/CRITICAL_RULES.md#commit-message-format) (no trailers).
3. Record Gate 2, pause via `--pending-decision` for Choice A, and checkpoint state (do **not** run `package_epic.py` or generate `handoff.md` yet — packaging runs at `/principal-review` completion and stamps creator PIC cleanly; verify parallel waves cleanly via `compute_execution_order.py <epic_slug> --parallel`):
   ```bash
   python3 scripts/resume_context.py --gate 2 --epic <epic_slug> --approved "<task breakdown summary>"
   python3 scripts/resume_context.py --pending-decision "Approve Gate 2 HLD and choose execution mode" --decision-kind gate_2 --epic <epic_slug>
   python3 scripts/resume_context.py --state --epic <epic_slug> --status "Stage 2: Waiting for Choice A"
   ```
   (When the user chooses AUTO MODE or Handoff Mode, `--gate` / non-paused `--state` / `package_epic.py` clears this epic's pending decision automatically.)
4. Read `.devtool/review_config.json`, stop calling tools, and present the [Handoff Choice](../dev-lifecycle/SKILL.md#handoff-choice) (Gate 2 Unified Confirmation with reviewer provider/model priority: AUTO MODE `Triển khai (tự động)` vs Handoff Mode `Dừng lại`). Never invoke `dev-implementation` directly.

### Updating an Existing Epic
Append sequentially numbered task files, update Kanban Tasks Breakdown links (and Mermaid diagrams if changed) in the HLD, and retrofit scenario IDs / `Covers:` / `Integration test roots:` before running `check_bdd_traceability.py plan`.

## Anti-Rationalization and Doubt-Driven Verification

| Agent Rationalization | Enforced Counter-Rule |
|---|---|
| "Node.js unit tests prove this web UI works." | **REJECTED**: Web Tier C requires headless Playwright + Zero-Console-And-Layout-Defect checks. |
| "Hardcoding mock data in a stub is enough." | **REJECTED**: Wire-level fixtures from `shared-contracts/` are required. |
| "Browser console errors are harmless warnings." | **REJECTED**: Zero-Console-Error fails Gate 4 on any uncaught console error. |
| "No simulator, so a unit test counts as Tier C." | **REJECTED**: Mobile Tier C requires Subcutaneous Testing with real DI/persistence. |
| "HTML matches the Visual Companion mockup." | **REJECTED**: Web Tier C2 UI tests must assert `getComputedStyle` and `getBoundingClientRect` layout properties against the Visual Companion design. |

**Doubt-Driven Verification Protocol**: **1. CLAIM** (state assertion) -> **2. EXTRACT** (inspect JUnit XML classnames, Playwright traces, mocks) -> **3. DOUBT** (challenge mock/unit shortcuts) -> **4. RECONCILE** (verify against real production code paths).

## Red Flags - STOP and Start Over
- Modifying `shared-contracts/` design without checking Triad files first, omitting `task_01`, or putting `shared-contracts/...` in Satellite `Allowed files`.
- Writing task files before breakdown confirmation, omitting the final Tier C task, mixing languages in `task_*.md`, or omitting `Covers:` / scenario IDs.
- Using legacy Mermaid `graph TD`/`LR`, unquoted special-char labels, or skipping `check_bdd_traceability.py plan` / `check_task_contract.py --design`.
- Running `package_epic.py` or `dev-implementation` directly instead of stopping at the Gate 2 Handoff Choice for `/principal-review`.
