---
name: dev-implementation
description: Use when an epic already has an approved HLD and Kanban task files (`.devtool/epic/<epic_dir>/` + `.devtool/features/task_*.md`) and you need to actually execute those tasks against the codebase, in the right order, inside an isolated worktree across Web Applications, Flutter, Android Native, iOS Native, Python, or Rust projects.
---

# Development Implementation

## Overview

Runs an already-approved epic's Kanban tasks end-to-end: reload the epic's own docs for context, detect the platform (Flutter, Android Native, iOS Native, Web, Python, or Rust), compute a dependency-safe execution order with parallel batches, bootstrap the main epic worktree with an isolated 2-slot ephemeral worker pool, then orchestrate tasks with sub-agents—running independent tasks in parallel with zero storage overhead via APFS clone / shared cache.

**Core principle:** Role 2.2 Orchestrator runs Stage 3; Role 2.3 Programmer subagents execute tasks in a 2-slot ephemeral worker pool + shared cache, Role 2.1 subagents review and plan fixes; one commit per task, docs stay truthful.

**Announce at start:** "I'm using the dev-implementation skill to implement the `<epic_slug>` epic."

## Two Placeholders, Not One

This skill uses two distinct placeholders, and **they are usually different strings** — do not substitute one for the other:

| Placeholder | What it is | Where it appears | Worked example |
|-------------|-----------|------------------|----------------|
| `<epic_dir>` | The epic's directory name on disk | `.devtool/epic/<epic_dir>/<epic_dir>.md` (legacy `<epic_dir>.en.md`), the worktree directory name | `logging_refactor` (underscores) |
| `<epic_slug>` | The epic's frontmatter `epic:` value | The calculator's CLI arg, matching `epic:` in `task_*.md`, the `epic/<epic_slug>` branch name, the `[EPIC_NAME]` commit prefix | `logging-refactor` (hyphens) |

Read both values off disk at the start — never derive one from the other by guessing the separator.

## When to Use

- The epic has a `.devtool/epic/<epic_dir>/<epic_dir>.md` (legacy `<epic_dir>.en.md`) HLD and one or more `.devtool/features/task_*.md` files with `epic: "<epic_slug>"` in frontmatter, and a human has already approved that design.
- You are about to implement more than one task from that epic in this session.
- You are resuming an epic — packaged (`handoff.md` present, Status `Packaged`) or interrupted midway through Stage 3. Invoke this skill with the epic's directory name or slug; Entry-Point Detection in Phase 0 decides where to start.

**Don't use when:** the epic/tasks don't exist yet (use `d3nexus:dev-brainstorming` then `dev-designer` first), or you're implementing a single one-off task with no epic context (just use `d3nexus:subagent-driven-development` directly).

## Process

This skill is **Stage 3** of the Epic Lifecycle. The surrounding stages, the five approval gates, and what each stage hands over are owned by the [`dev-lifecycle`](../dev-lifecycle/SKILL.md) skill (with diagrams preserved in `docs/lifecycles.en.md`). Gate 3 (execution order confirmed) is enforced below, in Phase 1.

### Phase 0 — Context Reload & Platform Detection (once, not per task)

0. **Resolve the epic.** This skill takes one epic name, in either form:
   - If `.devtool/epic/<name>/` exists, `<epic_dir>` is `<name>`, and `<epic_slug>` is the `epic:` value of its task mirrors: `grep -h -m1 '^epic:' .devtool/epic/<name>/task_*.md`.
   - Otherwise `<name>` is a slug, and `<epic_dir>` is the directory holding the files `grep -l -F 'epic: "<name>"' .devtool/epic/*/task_*.md` lists.
   - With no name, or no match, list the epic directories whose overview Status is not `Done` and ask which one. Never guess, even when only one is listed.
1. **Load Lean Orchestration Context (Bounded Context):**
   - `.devtool/epic/<epic_dir>/handoff.md`, when present — packaging record and Open Notes (never edited manually; updated only via `package_epic.py <epic_dir> --revise --reason "<text>"`).
   - `.devtool/epic/<epic_dir>/<epic_dir>.md` (legacy `<epic_dir>.en.md`) — canonical HLD & Maintenance Map ("Prompt to Maintain"; English SSOT, never open a `.vi.md` mirror). Read `Meta Data`, `Architecture, Feature Map & Technical Design`, `Integration Test Plan`, and `Verification Environment`.
   - Frontmatter, `Covers:`, and `Dependencies` of `.devtool/features/task_*.md` matching `epic: "<epic_slug>"` (read full task bodies one at a time in Phase 2).
   - Restore context and window title: `python3 scripts/resume_context.py --role orchestrator --epic <epic_slug>`.
   - Before Stage 3, each wave and each fix round run `python3 scripts/dev_config.py quota-check`; exit `2`: checkpoint `quota_low`, record a `quota` pending decision, stop.

#### Bounded Context Injection & Spec Fidelity

Before implementing any task in Phase 2, adhere strictly to Bounded Context Injection:
1. Read **only** the active task file (`.devtool/features/task_*.md` — the Execution SSOT embedding assigned edge-case `### BDD SCENARIOS` from `bdd_scenarios.md` and `Decisions Already Made`).
2. Read listed `Allowed files:` and `Read-only context:` using **Rule 3 bounded reads** (`StartLine`/`EndLine` at `target_files` ranges + symbol search when files exceed `200` lines).
3. Look up symbols in `Decisions Already Made` (avoid undirected whole-repo searches). Enforce **Rule 5 Zero-Fluff Output Cap** (omit filler narration while preserving Verdicts, Findings, and gate outputs).

**Strict Spec Fidelity**: Stay strictly within the active task and `Allowed files`; avoid unrequested abstractions or adjacent refactors.

**Symlink & Multi-Repo Boundary Invariant**: Where `shared-contracts/` is a symlink (`lyrics-sync`, `nexus`), treat it as read-only for git (never `git add shared-contracts/...` -> `fatal: pathspec is beyond a symbolic link`); report `BLOCKED` with an Upstream Contract Handoff Summary if upstream changes are required.

2. Resolve the three paths the rest of this skill uses. `SKILL_DIR` is the directory this `SKILL.md` was loaded from:
   ```bash
   SKILL_DIR=<absolute path of the directory containing this SKILL.md>
   REPO_ROOT=$(git rev-parse --show-toplevel)
   INTEGRATE="$SKILL_DIR/../finishing-a-development-branch/resources/scripts/integrate_branch.py"
   ```
3. Detect the platform:
   ```bash
   PROJECT_TYPE=$("$SKILL_DIR"/resources/scripts/detect_project_type.sh "$REPO_ROOT")
   echo "Detected project type: $PROJECT_TYPE"
   ```
   Supported platforms: `flutter`, `android`, `ios`, `web`, `python`, `rust`.
4. Run **Entry-Point Detection** before Phase 1. It decides whether Phase 1 starts fresh or the Resume Procedure takes over.

#### Entry-Point Detection

**MANDATORY: read [references/entry-point-and-resume.md](references/entry-point-and-resume.md) before Phase 1.** It holds the read-only signals and the 7-row entry table. Evaluate the rows top-down (first match wins) and announce it: "Entry point: row N — <state>."

#### Resume Procedure

Rows 4 and 5 only. **MANDATORY: read [references/entry-point-and-resume.md](references/entry-point-and-resume.md#resume-procedure) before Phase 1.** Phase 1 step 4's `git worktree add -b` never runs here.

### Phase 1 — Execution Plan

1. Run:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/compute_execution_order.py <epic_slug> --parallel
   ```
   Check scan summary line (`Scanned N task_*.md files; M matched epic ...`). If `M` is smaller than expected, fix broken frontmatter before proceeding. Inspect the computed parallel batches.
2. Read "Manual review advised" section (if any) and cross-check against Phase 0 context. Adjust flattened order by hand if a prose note should win.
3. **Automated Gate 3 Bootstrap (Zero Manual Confirmation):**
   The Orchestrator computes and resolves the execution order automatically via `compute_execution_order.py`.
   Record Gate 3 approval in the Gate Approval Ledger:
   ```bash
   python3 scripts/resume_context.py --gate 3 --epic <epic_slug> --approved "<execution order auto-resolved>"
   ```
   Query or verify Gate 3 status at any time via:
   ```bash
   python3 scripts/resume_context.py --check-gate 3 --epic <epic_slug>
   ```

   Run BDD traceability plan check:
   ```bash
   SCENARIOS=".devtool/epic/<epic_dir>/bdd_scenarios.md"; [ -f "$SCENARIOS" ] || SCENARIOS=".devtool/epic/<epic_dir>/bdd_scenarios.en.md"
   python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py plan \
     --scenarios "$SCENARIOS" \
     --tasks .devtool/epic/<epic_dir>/task_*.md
   ```
   Proceed directly to worktree creation (Step 4) and task execution. Do NOT prompt the developer for manual confirmation on execution order. (Halt ONLY on cyclic DAG dependencies, malformed frontmatter, or unresolvable prerequisites).
   Verify Principal Review state: `python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --kind principal --epic-dir <epic_dir>`. Principal Review must be `not run`, `round <n>: PASS`, or `round <n>: decided`.
   If needed, add bracketed identifiers to `bdd_scenarios.md` (legacy `bdd_scenarios.en.md`), `Covers:` lines to task files, and `Integration test roots:` to HLD. Commit as `[EPIC_NAME] Add BDD scenario identifiers`.

   Then check task contract:
   ```bash
   HLD=".devtool/epic/<epic_dir>/<epic_dir>.md"; [ -f "$HLD" ] || HLD=".devtool/epic/<epic_dir>/<epic_dir>.en.md"
   python3 "$SKILL_DIR"/resources/scripts/check_task_contract.py \
     --hld "$HLD" \
     --tasks .devtool/epic/<epic_dir>/task_*.md
   ```
   Do not create worktree until both checks exit 0. In AUTO MODE (`Triển khai (tự động)`), proceed directly to worktree bootstrap without pausing for execution-order confirmation.

#### Phase 1 (continued) — Worktree Bootstrap (Automated Gate 3)

4. Bring local `develop` up to date with upstream, then create one worktree for whole epic (`d3nexus:using-git-worktrees`):
   ```bash
   python3 "$INTEGRATE" sync-base --base develop
   git worktree add .worktrees/<epic_dir> -b epic/<epic_slug> develop
   ```
   If `sync-base` exits 3 (diverged or dirty file), stop and ask.
   If overview Status begins with `Packaged`, run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`.

   **Isolated IDE Window**: Optionally open the worktree in a separate IDE profile window (`antigravity <profile> .worktrees/<epic_dir>`).
5. Bootstrap worktree using platform tooling (`bootstrap_worktree.sh` — installs Python `[project.optional-dependencies]` via `uv sync --all-extras` and `[dependency-groups].dev` via `--group dev` when declared; `verify_polyglot_registry.py` injects `UV_NO_SYNC=1` on `uv run` capabilities to preserve extras — plus Gradle sync, Tuist, npm/pnpm, cargo check). Whenever a linked worktree reuses a symlinked parent `.venv`, run all worker commands with `UV_NO_SYNC=1 PYTHONPATH="$WORKTREE_ROOT/src"` so editable `.pth` files never shadow the worktree's `src/` and `uv run` never prunes shared extras.
6. Never copy build caches (`.dart_tool/`, `/build/`, `.build/`, `android/**/.cxx/`) from another checkout into this worktree.
7. **Initialize 2-Slot Ephemeral Worker Pool:**
   Set up isolated worktree slots with shared caches (APFS clone / symlink):
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/manage_worker_pool.py init --epic-dir <epic_dir> --epic-slug <epic_slug>
   ```

### Phase 2 — Parallel Task Execution (Orchestrator + Programmer Subagents)

<HARD-GATE>
- **Orchestrator (Role 2.2)**: never reads/edits `src/`/`tests/` (sole bounded exception: reading `manage_worker_pool.py triage-fix` JSON `bounded_diff` `<= 30` non-test lines when `ELIGIBLE_FOR_SHORT_CIRCUIT` to form Tier 2 `RiskAssessment`) or runs tests, linters, direct `run_task_checks.py`, or `verify-tier` (only `finalize-slot` runs internal read-only `run_task_checks.py status` and `check_bdd_traceability.py` mechanical gates); reads only subagent JSON summaries, epic docs, and git metadata ([orchestration-roles.md](../dev-lifecycle/references/orchestration-roles.md)).
- **Pool state is Orchestrator-only**: subagents never call `manage_worker_pool.py`.
</HARD-GATE>

**Dispatch Role 2.3** with `python3 scripts/dev_config.py dispatch --persona programmer --mode write --prompt-file <file> --cwd <slot> --log <log> --epic <epic_slug> --task <task_id> --slot <n>`; the lease file `agy_profile_leases.json` records the `agy` profile in use. Exit code `2` means record a quota pending decision with the printed report and stop. Never hand-build the `agy` environment, substitute a lighter model, fall back or retry (checkpoint `model_unavailable`, record a blocker, stop); other personas use `dev_config.py resolve <persona>` (`programmer` default `gemini-4-hydrogen-xhigh`).

Autonomous Mode: `lifecycle_runner.py` dispatches itself (`build_agy_command`, `start_new_session=True`, SIGTERM/SIGKILL supervision, per-task logs).

#### 2-Slot Ephemeral Worker Pool & Layer Workflow
- **Slots**: `.worktrees/<epic_dir>-slot-1` / `-slot-2` share caches with the main worktree `.worktrees/<epic_dir>`.
- **Pool CLI** (`python3 "$SKILL_DIR"/resources/scripts/manage_worker_pool.py <cmd> --epic-dir <epic_dir> --epic-slug <epic_slug>`): `init [--wave <k>]` | `sync --slot <1|2> --task <task_id> [--wave <k>] [--status working|review|idle] [--no-reset] [--review-file <json>] [--blockers-file <json>]` | `triage-fix --slot <1|2> --task <task_id> [--record-tier2 --risk-level <MEDIUM|HIGH> --rationale "<text>"]` | `finalize-slot --slot <1|2> --task <task_id> [--wave <k>] [--mode <pass1-approved|tier2-short-circuit|pass2-complete>] [--risk-level <LOW>] [--rationale "<text>"] [--review-file <json>]` | `merge --slot <1|2> --task <task_id>` | `cleanup` (keeps dirty/unmerged work)
1. **Wave Setup (Orchestrator)**: **MANDATORY: read [references/worker-execution-rules.md](references/worker-execution-rules.md) before dispatching or acting as a `task-implementer`** (test assertion health, anti-bloat and tiered test execution; the Tri-Persona model; anti-rationalization and doubt-driven verification). Run `compute_execution_order.py <epic_slug> --parallel`, monitor `estimate_heartbeat.py`, and log wave (`resume_context.py --epic <epic_slug> --wave <k> --state --status "In progress: Wave <k>"`). For each task (max 2 per wave), run `manage_worker_pool.py sync ... --slot <1|2> --task <task_id> --wave <k> --status working` (single-worktree mode: `sync_task_status.py task <task_id> in-progress`), then dispatch the slot's `task-implementer`.
2. **`task-implementer` (Role 2.3 — Mandatory Per-Task Mechanical Verification)**: Inside the slot, run `check_code_impact.py` (halt on `🔴 DIVERGENCE DETECTED`; add characterization tests on `⚠️ UNPROTECTED CODE`), write `RED` tests -> `GREEN` code, and execute the full mechanical `Verification` table (`RED -> GREEN -> REGRESSION -> TIER-B -> TIER-C`, covering touched module + *Downstream Callers* regression suites and `TIER-B` static checks across all `Allowed files`) via `run_task_checks.py red` and `run_task_checks.py verify`. Once `run_task_checks.py verify` passes, tick every `- [ ]` checkbox in `## Definition of Done` to `- [x]` with a brief post-reference mechanical result summary (e.g. `- [x] Criterion (V2, V3) — exit 0, 42 passed`) and confirm `run_task_checks.py status` prints `done gate: PASS` (updating frontmatter to `status: "done"` or `completedAt` while any `- [ ]` remains is strictly forbidden and rejected by the validators). If `needs_review` (step 2 below) is false and `done gate: PASS`, finalize directly: `sync_task_status.py task <task_id> done`, `git status`, `git add -A`, commit `[EPIC_NAME] <task_title>` (no trailers). When `needs_review` is true, leave changes uncommitted (`finalized: false`) so `run_task_checks.py` `patch_id` stays valid. Return the JSON summary, then `--checkpoint subagent_returned`.
3. **`task-reviewer` (Role 2.1, fresh read-only subagent — Selective LLM Review)**: LLM review does not run repeatedly on small, purely mechanical tasks (avoiding review bottlenecks); it is dispatched by the Orchestrator only at semantic/architectural boundaries or when Selective Gating triggers, after `sync ... --status review` (Pass 1 captures pre-fix `pass1_tree_sha`). Audits diff + AST + Zero Fakery + ticked `[x]` `Definition of Done` items via `run_task_checks.py status` and `check_bdd_traceability.py` only; never edits or commits. Pass 1 (`--review-pass 1`) audits comprehensively under the Blocker-Only rubric (`BLOCKER` triggers `CHANGES_REQUESTED`; minor nits are `NON_BLOCKING_OBSERVATION` in `"observations"` with `"verdict": "APPROVED"`). Empty `blockers` with `done_gate: "PASS"` coerces to `APPROVED`. On `APPROVED`, Orchestrator calls `manage_worker_pool.py finalize-slot ... --mode pass1-approved`.
4. **Merge & Cleanup (Orchestrator)**: see steps 4–5 below (then `--checkpoint wave_merged`); `cleanup` before Phase 4; revisions use `package_epic.py --revise --reason "<text>" <epic_dir>`.

   > [!CRITICAL]
   > ### 🎯 MANDATORY 100% BDD-TO-TEST TRACEABILITY RULE
   > 1. **100% Scenario Traceability**: Every single BDD scenario authored in Phase 1 MUST map directly to at least one concrete automated test function or test block.
   > 2. **Tier Separation**: `[Tier A - Unit]` covered 100% by unit tests; `[Tier C - Integration]` covered 100% by host integration flow tests. Mocks do NOT substitute for Tier C integration tests.
   > 3. **BDD Automation (Tier C, all platforms)**: For every identifier on task's `Covers:` line, author at least one integration test under HLD's `Integration test roots`, carrying the identifier in test name, description, or tag.
   > 4. **Gate to Done**:
   >    ```bash
   >    python3 "$SKILL_DIR"/resources/scripts/run_task_checks.py red <task mirror>                       # before implementing (exits 0 on expected fail)
   >    python3 "$SKILL_DIR"/resources/scripts/run_task_checks.py measure <task mirror> [--timeout 7200] [--resume] # for tasks with MEASURE rows
   >    python3 "$SKILL_DIR"/resources/scripts/run_task_checks.py verify <task mirror>                    # after last change (runs GREEN, REGRESSION, TIER-B, TIER-C)
   >    # After verify passes: tick every `- [ ]` in `## Definition of Done` to `- [x]` with a brief mechanical result note (e.g. `exit 0, 42 passed`)
   >    python3 "$SKILL_DIR"/resources/scripts/run_task_checks.py status <task mirror>                    # prints done gate: PASS (fails if any `- [ ]` remains)
   >    ```
   >    Never edit `.devtool/epic/<epic_dir>/evidence/<task_id>.json` by hand. `sync_task_status.py task <id> done` refuses unless evidence matches tree and table and every `## Definition of Done` checkbox is ticked `[x]`.
   >    When task has `Covers:` line, run traceability check (exit 0):
   >    ```bash
   >    SCENARIOS=".devtool/epic/<epic_dir>/bdd_scenarios.md"; [ -f "$SCENARIOS" ] || SCENARIOS=".devtool/epic/<epic_dir>/bdd_scenarios.en.md"
   >    python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py tests \
   >      --scenarios "$SCENARIOS" \
   >      --roots <Integration test roots from the HLD> \
   >      --ids <identifiers on the task's Covers: line>
   >    ```
   >
   >    **Failure-Set Baseline & Regression Comparison**:
   >    When isolating pre-existing test failures before making changes or comparing regression deltas:
   >    ```bash
   >    python3 "$SKILL_DIR"/resources/scripts/record_failure_baseline.py \
   >      --cmd "<test-command>" \
   >      --out .devtool/epic/<epic_dir>/evidence/baseline.txt \
   >      [--restore <path>]
   >
   >    python3 "$SKILL_DIR"/resources/scripts/compare_failure_sets.py \
   >      --baseline .devtool/epic/<epic_dir>/evidence/baseline.txt \
   >      --current .devtool/epic/<epic_dir>/evidence/current.txt \
   >      [--rerun-new] [--allow-isolated-pass]
   >    ```
   >
   >    **Task Text Replay**:
   >    To replay structured directives (`Create`, `Replace in`, `Insert in`) and test verification rows:
   >    ```bash
   >    python3 "$SKILL_DIR"/resources/scripts/replay_task_text.py <task.md> [--worktree <dir>] [--run-rows]
   >    ```
   > 5. **Stop and Report**: A `Stop and Report If` condition in task is reported as `BLOCKED`. Never edit Verification table, Definition of Done, Allowed files or Covers line, or protected path, to force a pass. In Satellite Mode, report `BLOCKED` if an unmerged upstream contract change prevents local tests from passing.

2. **Selective `task-reviewer` Gating**: `needs_review` is true when `review_tier: "full"` is in frontmatter, labels include `security`, `architecture`, `concurrency`, or `contract`, or `> 2` non-test modules change. The Orchestrator recomputes the module count with `git -C <slot> diff --name-only <base>..<head_sha>` and dispatches `task-reviewer` on mismatch.
3. **Fix Loop & Two-Tier Risk Assessment Gate (`max_task_review_passes = 2`, `max_fix_passes = 1`)**:
   - On `CHANGES_REQUESTED` with `>= 1` `BLOCKER` in Pass 1, the Orchestrator runs `sync ... --status working --no-reset --review-file <p1.json>` (`fix = 1`) and dispatches Role 2.3 `task-implementer` with `pass1_blockers` only (`run_task_checks.py verify`, uncommitted).
   - **Tier 1 (`triage-fix`)**: Run `manage_worker_pool.py triage-fix <epic> --slot <N> --task <id>` against `pass1_tree_sha`.
   - **Tier 2 (`RiskAssessment`)**: When `tier1_status == "ELIGIBLE_FOR_SHORT_CIRCUIT"` (`<= 30` non-test changed lines, zero sensitive-surface/test-weakening triggers), Role 2.2 evaluates `bounded_diff` vs. `pass1_blockers` in-place: `LOW` calls `finalize-slot --mode tier2-short-circuit --risk-level LOW --rationale "<1-2 sentences>"` (runs internal read-only mechanical status gates, logs audit note, marks `done`, commits, merges, skipping Pass 2); `MEDIUM`/`HIGH` runs `triage-fix --record-tier2` and enters Pass 2.
   - **Pass 2 Delta-Only (`HIGH_RISK` or Tier 2 `MEDIUM`/`HIGH`)**: Run `sync ... --status review` (`review = 2`) and dispatch fresh Role 2.1 `task-reviewer` (`--review-pass 2 --pass1-tree-sha <sha> --blockers-file <p1_blockers.json>`; `DIRECT_REGRESSION` only, zero new nitpicks). Once Pass 2 completes with green mechanical gates, run `finalize-slot --mode pass2-complete --review-file <p2.json>` (commits, marks `done`, merges, logs residual remarks to `review_audit_notes.jsonl`, zero Fix Pass 2).
4. **Merge**: Once finalized (implementer `finalized: true` when `needs_review == false` -> `manage_worker_pool.py merge`, or `finalize-slot` after review/short-circuit), the slot merges into `epic/<epic_slug>` and resets to `idle`.
5. **Log**: After `merge`, the Orchestrator logs state (`resume_context.py --log --epic <epic_slug> --task <task_id> --request "<summary>" --action "<verify status>"` and `resume_context.py --state --epic <epic_slug>`, which syncs `window.title`).
6. If implementation diverged from HLD, perform Phase 3 Doc Sync before next task.
7. **Integrate with develop (only when base branch moved).** First check locally whether `<base_ref>` (`develop`) has any commits not in `HEAD` (`git rev-parse develop != $(git merge-base HEAD develop)`). If `develop` has not moved since the worktree branched, skip per-task rebase/verify-tier and proceed immediately to the next task (full integration runs at Stage 4). When `develop` has moved and no slot is `working`, the Orchestrator runs `preflight` from the epic worktree after `merge`, then dispatches a Role 2.3 subagent for `rebase`, conflict resolution and `verify-tier`:
   ```bash
   python3 "$INTEGRATE" preflight --base develop
   ```
   - If clean or noop, rebase if needed:
     ```bash
     python3 "$INTEGRATE" rebase --base develop
     ```
   - Resolve conflicts with playbook; stop and ask on semantic conflicts.
   - Verify tier:
     ```bash
     python3 "$INTEGRATE" verify-tier --base develop
     ```
   - If verification is red, fix before next task starts, commit as `[EPIC_NAME] Fix integration with develop after <task_title>`.

### Phase 3 — Doc Sync on Divergence

Only when Phase 2 flags divergence:
1. Update the epic's Mermaid diagrams in the English HLD `<epic_dir>.md` only.
2. Update affected task file(s) prose.
3. Commit separately:
   ```bash
   git commit -m "[EPIC_NAME] Sync HLD after <task_title>" -m "- <diagram or section updated>"
   ```

### Fixes after the last task

Once every task is `done`, a fix is never made by reopening a task. Make it as its own commit on the epic branch, titled `[EPIC_NAME] Fix <what>`. Do not move a done task back, and do not re-record its evidence. `audit_epic.py` lists these commits under "Commits outside tasks". After fixes, run Phase 4 again in full on the new SHA.

### Phase 4 — End of Epic Verification (Fresh `gate4-verifier` Subagent)

Once every task is `done` and slots are cleaned up, the Orchestrator dispatches a **fresh Role 2.3 `gate4-verifier`** (never the round's implementer, reviewer or fixer) to run steps 0–5. It edits no code; on failure it returns `FAIL`, and the Orchestrator dispatches a fixer, then a new verifier. `PASS` counts only when `candidate_sha == git rev-parse HEAD`, the tree is clean, and the `@quality_check` report is bound to that SHA ([orchestration-roles.md](../dev-lifecycle/references/orchestration-roles.md#4-independent-verification)):

0. **Manual Smoke Checklist**:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/generate_smoke_checklist.py --epic-dir <epic_dir>
   git add .devtool/epic/<epic_dir>/manual_smoke_checklist.md
   git commit -m "[EPIC_NAME] Generate manual smoke walkthrough checklist"
   ```
Resolve candidate SHA (`git rev-parse HEAD`) on a clean tree:

1. **Review decisions**, only when `.devtool/epic/<epic_dir>/review_results.md` exists:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --epic-dir <epic_dir>
   ```
   Exit 1 means unresolved finding: record decision or make Fix commit, then restart Phase 4 in full.
2. **Gate 4 audit**:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/audit_epic.py --epic-dir <epic_dir> --base <base_ref>
   ```
   Must exit 0. Keep output for Phase 4.1.
3. **HLD Integration results commands.** Run every `Integration results:` line of HLD Integration Test Plan.
4. **Result-based traceability**: run `check_bdd_traceability.py tests --results` over those reports:
   ```bash
   SCENARIOS=".devtool/epic/<epic_dir>/bdd_scenarios.md"; [ -f "$SCENARIOS" ] || SCENARIOS=".devtool/epic/<epic_dir>/bdd_scenarios.en.md"
   python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py tests \
     --scenarios "$SCENARIOS" \
     --roots <Integration test roots from the HLD> \
     --results <reports written by Integration results commands>
   ```
   Must exit 0: every scenario in `bdd_scenarios.md` (legacy `bdd_scenarios.en.md`) is covered by at least one passing integration test. `--roots` and `--ids` accept space- or comma-separated values.
5. **Quality check.** Run `@quality_check` on the same SHA:
   - Inputs:
     - `profile`: `"epic"`
     - `base_ref`: `<base_ref>`
     - `repository_sha`: Candidate commit SHA from `git rev-parse HEAD`
   - Only an aggregated verdict of **PASS** bound to that exact SHA qualifies for Gate 4 `🟢 LGTM`.

#### Semantic Test Integrity Governance (Gate 4 Rules)

**MANDATORY: read [references/gate4-semantic-integrity.md](references/gate4-semantic-integrity.md) before running or judging Gate 4.** Gate 4 rejects test fakery with **`FAIL`**: **No Reconstructed Logic** and **Immutable Real Artifacts**.

### Automated Transition to Cross-Model Review (Zero Intermediate Confirmation)

<HARD-GATE>
Do NOT stop to ask for an intermediate Review Choice prompt after Gate 4 passes.
When all tasks are complete and Phase 4 / Gate 4 local machine acceptance passes (🟢 LGTM), the workflow MUST AUTOMATICALLY transition into `/cross-model-review` (`run_external_review.py run --epic-dir <epic_dir> --base <base_ref> --auto-quota`).
Do NOT ask the developer whether to review or finish at this intermediate point.
The decision to Finish belongs strictly in Stage 4 (Phase 4.1 / Gate 5), after Cross-Model Review completes.
</HARD-GATE>

The loop invariant is **Gate 4 PASS → Review Choice (Automated Cross-model review) → Gate 4 in full → Finish → Gate 5**.

On Gate 4 local PASS:
1. Record Gate 4 in `.devtool/GATE_LEDGER.md` via `python3 scripts/resume_context.py --gate 4 --epic <epic_slug> --approved "Gate 4 Local PASS (<candidate_sha>)"`, and update state via `python3 scripts/resume_context.py --state --epic <epic_slug> --status "Stage 3: Cross-Model Review"`.
2. Automatically invoke `d3nexus:cross-model-review` in epic worktree with clean tree (`--auto-quota` priority `Claude -> Codex -> Kiro -> Argon`, 3-Round Convergence Funnel, max 3 rounds):
```bash
python3 "$SKILL_DIR"/resources/scripts/run_external_review.py run \
  --epic-dir <epic_dir> --base <base_ref> --auto-quota
```
3. Commit `review_results.md` (`[EPIC_NAME] Record cross-model review round N`), run `python3 "$SKILL_DIR"/resources/scripts/run_external_review.py triage --epic-dir <epic_dir>`, and inspect `## Auto-Triage Gate`:
   - **`AUTO_PASS_CLEAN` / `AUTO_PASS_FINAL_MINOR_SWEEP` / `AUTO_FIX_ELIGIBLE`**: In AUTO MODE (Gate 2 `Triển khai (tự động)` or `lifecycle_runner.py`), **never pause for developer confirmation between rounds**; the Orchestrator routes by risk: low risk -> Role 2.3 `review-fixer` `fast-track`; high risk (any `Critical`, escalation marker, or the same Gate 4 check failing twice) -> Role 2.1 `fix-planner` (`--mode read-only`), whose `fix_plan_round<N>.md` is `PLANNED` (`review-fixer` runs `apply-plan`) or `ESCALATE` (`--pending-decision`, stop for Role 1.0). The fixer runs **Tier 1 scoped tests only** (`uv run pytest <changed_test_files> -n auto --timeout=30 -q --tb=short`), commits `[<EPIC_NAME>] Fix <what>`, records `fixed in <sha>` in `review_results.md`, and returns the `review-fixer` summary; the Orchestrator checks `git diff --name-only <pre_sha>..HEAD` for out-of-scope paths. On convergence a fresh `gate4-verifier` runs full Gate 4. Details: [orchestration-roles.md](../dev-lifecycle/references/orchestration-roles.md#4-independent-verification).
   - **`CIRCUIT_BREAKER_HALT`**: Halts cleanly via `--pending-decision` on `CRITICAL_CONFLICT`, `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, or Critical findings surviving Round 3.
4. Once `/cross-model-review` completes (converged with 0 Critical findings) and Gate 4 passes on the latest candidate SHA:
   - Present the synthesized `## Top 3 Highest-Risk Findings (Executive Report)`.
   - Advance directly to **Phase 4.1 (Stage 4: Developer Kanban Review & Finish Decision — Gate 5)**.

### Phase 4.1 — Unified Gate 5 Sign-Off & Stage 4 Finish Choice (🛑 SINGLE FINAL STOP & WAIT)

Once `/cross-model-review` has converged, `@quality_check` reports 🟢 LGTM on candidate SHA, and all tasks completed:
1. **Preserve Kanban Visibility**: All completed `task_*.md` files MUST remain in `.devtool/features/done/` until the user chooses Merge or Push & PR.
2. **Present Executive Summary**: Output summary containing epic slug, worktree path, completed tasks, `@quality_check` verdict, BDD matrix, audit disclosure sections (Evidence, Protected paths, Commits outside tasks, Gate 5 items), and synthesized `## Top 3 Highest-Risk Findings (Executive Report)`.
3. 🛑 **SINGLE FINAL STOP & WAIT (Gate 5 + `/finishing-a-development-branch` Menu Combined)**: Record Choice A decision (`python3 scripts/resume_context.py --pending-decision "Gate 5 Kanban review and Stage 4 finish option" --decision-kind gate_5 --epic <epic_slug>`) and stop calling tools immediately — present Gate 5 status **together with** the Stage 4 integration options in **one** prompt (do NOT ask a separate "reply to proceed" confirmation before showing the Finish options):
   > "Epic `<epic_slug>` tasks complete, `@quality_check` **🟢 LGTM**, Cross-model review converged; tasks remain in `.devtool/features/done/`. Choose how to finish (Gate 5 sign-off + Stage 4 integration):
   > 1. Merge back to `<base-branch>` locally
   > 2. Push and create a Pull Request
   > 3. Keep the branch as-is (I'll handle it later)"
4. **Execute Chosen Option**: Once the user picks Option 1, 2, or 3, record `--gate 5` (clears the pending decision automatically) and proceed directly to Phase 5 **without re-presenting Step 4 of `finishing-a-development-branch`**.

### Phase 5 — Branch Finishing

Only after user picks their Finish option in Phase 4.1:
1. Invoke `d3nexus:finishing-a-development-branch` on epic branch (base = `develop`), proceeding directly to Step 5 for the user's chosen option (skipping duplicate Step 4 menu).
   Pre-Finish Archival Hook executes automatically:
   ```bash
   python3 skills/dev-implementation/resources/scripts/sync_task_status.py archive-done
   ```
   This sets Epic Status to `Done`, moves completed `task_*.md` files into `.devtool/epic/<epic_dir>/`, updates links, and commits archival before merge or PR.

## Integration

**Required workflow skills:**
- **d3nexus:using-git-worktrees** — creates epic worktree (`develop` as base ref).
- **d3nexus:subagent-driven-development** — runs each task.
- **d3nexus:test-driven-development** — used by implementer subagent.
- **d3nexus:quality_check** — runs end-of-epic verification.
- **d3nexus:finishing-a-development-branch** — completes epic branch.
- **d3nexus:copy_secure_configurations** — copies configuration secrets.
