---
name: dev-implementation
description: Use when an epic already has an approved HLD and Kanban task files (`.devtool/epic/<epic_dir>/` + `.devtool/features/task_*.md`) and you need to actually execute those tasks against the codebase, in the right order, inside an isolated worktree across Web Applications, Flutter, Android Native, iOS Native, Python, or Rust projects.
---

# Development Implementation

## Overview

Runs an already-approved epic's Kanban tasks end-to-end: reload the epic's own docs for context, detect the platform (Flutter, Android Native, iOS Native, Web, Python, or Rust), compute a dependency-safe execution order with parallel batches, bootstrap the main epic worktree with an isolated 2-slot ephemeral worker pool, then orchestrate tasks with sub-agents—running independent tasks in parallel with zero storage overhead via APFS clone / shared cache.

**Core principle:** AI Programmer acts as Implementation Orchestrator. 2-slot ephemeral worker pool + shared cache for parallel execution; one commit per task, docs stay truthful.

**Announce at start:** "I'm using the dev-implementation skill to implement the `<epic_slug>` epic."

## Two Placeholders, Not One

This skill uses two distinct placeholders, and **they are usually different strings** — do not substitute one for the other:

| Placeholder | What it is | Where it appears | Worked example |
|-------------|-----------|------------------|----------------|
| `<epic_dir>` | The epic's directory name on disk | `.devtool/epic/<epic_dir>/<epic_dir>.en.md`, the worktree directory name | `logging_refactor` (underscores) |
| `<epic_slug>` | The epic's frontmatter `epic:` value | The calculator's CLI arg, matching `epic:` in `task_*.md`, the `epic/<epic_slug>` branch name, the `[EPIC_NAME]` commit prefix | `logging-refactor` (hyphens) |

Read both values off disk at the start — never derive one from the other by guessing the separator.

## When to Use

- The epic has a `.devtool/epic/<epic_dir>/<epic_dir>.en.md` HLD and one or more `.devtool/features/task_*.md` files with `epic: "<epic_slug>"` in frontmatter, and a human has already approved that design.
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
   - `.devtool/epic/<epic_dir>/<epic_dir>.en.md` — canonical HLD & Maintenance Map ("Prompt to Maintain"; never `.vi.md` for decisions). Read `Meta Data`, `Architecture, Feature Map & Technical Design`, `Integration Test Plan`, and `Verification Environment`.
   - Frontmatter, `Covers:`, and `Dependencies` of `.devtool/features/task_*.md` matching `epic: "<epic_slug>"` (read full task bodies one at a time in Phase 2).
   - Restore context and window title: `python3 scripts/resume_context.py --role programmer --epic <epic_slug>`.

#### Bounded Context Injection & Spec Fidelity

Before implementing any task in Phase 2, adhere strictly to Bounded Context Injection:
1. Read **only** the active task file (`.devtool/features/task_*.md` — the Execution SSOT embedding assigned edge-case `### BDD SCENARIOS` from `bdd_scenarios.en.md` and `Decisions Already Made`).
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

Read these signals, all read-only, from the main checkout:

```bash
test -f .devtool/epic/<epic_dir>/handoff.md && echo packaged-handoff
test -f .devtool/epic/<epic_dir>/principal_review.md && python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --kind principal --epic-dir <epic_dir>
grep -m1 -E '^- \*\*Status\*\*:' .devtool/epic/<epic_dir>/<epic_dir>.en.md
git rev-parse --verify --quiet refs/heads/epic/<epic_slug>
for remote in $(git remote); do git ls-remote --heads "$remote" "epic/<epic_slug>"; done
git worktree list --porcelain | grep -E '^worktree .*/\.worktrees/<epic_dir>$'
python3 "$SKILL_DIR"/resources/scripts/compute_execution_order.py <epic_slug> \
  --features-dir .devtool/epic/<epic_dir>
```

If the HLD declares `- **Depends on epic**:`, verify prerequisites first:
```bash
python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py check-prereqs <epic_dir>
```
If this exits `1`, halt immediately and report the blocking prerequisite epics. Do not proceed to execution until all prerequisite epics are finished and merged into `develop` (or the target base branch).

`git ls-remote` asks each remote directly, so an epic branch pushed from another clone shows before any fetch; if a remote cannot be reached, fall back to `git branch -r --list '*/epic/<epic_slug>'`. The last command reads the epic's task mirrors (`sync_task_status.py` keeps them in step with `.devtool/features/` and `.devtool/features/done/`); its flattened order prints each task's status as `[priority, status]`. Evaluate the rows top-down — first match wins — and announce it: "Entry point: row N — <state>."

| # | Signals | State | Entry point |
|---|---------|-------|-------------|
| 1 | Overview Status is `Done` | Finished, or Stage 4 interrupted | With no epic branch left, report finished and stop. With epic branch still present, Stage 4 was interrupted or its PR is still open: report and ask |
| 2 | No epic branch, and any task is `backlog` | Queued behind another epic | Stop. Check conflicts via `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py check-conflicts <epic_dir>`, and promote tasks to `todo` via `sync_task_status.py promote <epic_dir> [--force]` when confirmed |
| 3 | No epic branch locally or on remote, no worktree, every task `todo` | Not started — packaged if `handoff.md` exists | Phase 1 as written: Gate 3, then new worktree |
| 4 | Epic branch exists, no worktree, some task not `done` | Interrupted, worktree removed | Resume Procedure |
| 5 | Worktree exists, some task not `done` | Interrupted midway through Stage 3 | Resume Procedure |
| 6 | Epic branch exists, every task `done` | Tasks finished | Recreate worktree if missing (`git worktree add .worktrees/<epic_dir> epic/<epic_slug>`, no `-b`) and bootstrap (Phase 1 step 5), run Resume Procedure preflight (step 2), then Phase 4 in full; its PASS presents Review Choice |
| 7 | Anything else — branch only on remote, or tasks `in-progress` or `done` with no epic branch | Inconsistent | Stop, report signals, ask |

#### Resume Procedure

For rows 4 and 5. Phase 1 step 4's `git worktree add -b` never runs here.

1. Row 4 only: recreate worktree from existing branch, `git worktree add .worktrees/<epic_dir> epic/<epic_slug>` with no `-b`. For rows 4 and 5, check bootstrap with Phase 1 step 5's platform checks and re-run if needed.
2. In the worktree, run `python3 "$INTEGRATE" preflight --base develop`. A rebase in progress, or diverged base, is handled per Phase 2 step 7 before anything else.
3. Find the interrupted task: one at `in-progress` or `review`. If worktree has uncommitted changes, collect `git status --short`.
4. **Gate 3 (resume).** Check mirror scan summary against task mirror count and read Manual review advised section. State the Principal Review status (`not run`, `round <n>: PASS`, or `round <n>: decided`), and stop with the triage if that check exits 1. Run Phase 1 step 3's BDD mapping check and task contract check, including retrofit if needed. Commit any retrofit on epic branch staging only touched files (both `bdd_scenarios`, both HLD variants, task files — never `git add -A`). The interrupted task's own status fields may ride along in that commit; that is expected. Present tasks already `done` with commits (`git log --oneline develop..epic/<epic_slug>`), remaining order with `done` tasks removed, choice on uncommitted changes (keep or discard), and request permission to fast-forward `develop`. Wait for confirmation.
5. If overview Status begins with `Packaged`, run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`.
6. Enter Phase 2 at the interrupted task — a task at `review` re-enters at Phase 2 step 2; a task at `in-progress` resumes implementation with kept changes — or at the first remaining task.

### Phase 1 — Execution Plan

1. Run:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/compute_execution_order.py <epic_slug> --parallel
   ```
   Check scan summary line (`Scanned N task_*.md files; M matched epic ...`). If `M` is smaller than expected, fix broken frontmatter before proceeding. Inspect the computed parallel batches.
2. Read "Manual review advised" section (if any) and cross-check against Phase 0 context. Adjust flattened order by hand if a prose note should win.
3. **Automated Gate 3 Bootstrap (Zero Manual Confirmation):**
   The AI Assistant computes and resolves the execution order automatically via `compute_execution_order.py`.
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
   python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py plan \
     --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md \
     --tasks .devtool/epic/<epic_dir>/task_*.md
   ```
   Proceed directly to worktree creation (Step 4) and task execution. Do NOT prompt the developer for manual confirmation on execution order. (Halt ONLY on cyclic DAG dependencies, malformed frontmatter, or unresolvable prerequisites).
   Verify Principal Review state: `python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --kind principal --epic-dir <epic_dir>`. Principal Review must be `not run`, `round <n>: PASS`, or `round <n>: decided`.
   If needed, add bracketed identifiers to `bdd_scenarios.*.md`, `Covers:` lines to task files, and `Integration test roots:` to HLD. Commit as `[EPIC_NAME] Add BDD scenario identifiers`.

   Then check task contract:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/check_task_contract.py \
     --hld .devtool/epic/<epic_dir>/<epic_dir>.en.md \
     --tasks .devtool/epic/<epic_dir>/task_*.md
   ```
   Do not create worktree until both checks exit 0 and developer has confirmed the order.

#### Phase 1 (continued) — Worktree Bootstrap, once the order is confirmed

4. Bring local `develop` up to date with upstream, then create one worktree for whole epic (`d3nexus:using-git-worktrees`):
   ```bash
   python3 "$INTEGRATE" sync-base --base develop
   git worktree add .worktrees/<epic_dir> -b epic/<epic_slug> develop
   ```
   If `sync-base` exits 3 (diverged or dirty file), stop and ask.
   If overview Status begins with `Packaged`, run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`.

   **Isolated IDE Window Launch**: Recommend or execute launching a separate Antigravity IDE window for this worktree to maintain isolated Git branches, separate title bars, and distinct user profiles:
   ```bash
   # Quick open via user profile alias (e.g. peter, danhdue, tess):
   <profile_alias> .worktrees/<epic_dir>
   # Or using antigravity launcher:
   antigravity <profile> .worktrees/<epic_dir>
   ```
5. Bootstrap worktree using platform tooling (`bootstrap_worktree.sh`, Gradle sync, Tuist, npm/pnpm, uv sync, cargo check).
6. Never copy build caches (`.dart_tool/`, `/build/`, `.build/`, `android/**/.cxx/`) from another checkout into this worktree.
7. **Initialize 2-Slot Ephemeral Worker Pool:**
   Set up isolated worktree slots with shared caches (APFS clone / symlink):
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/manage_worker_pool.py init --epic-dir <epic_dir> --epic-slug <epic_slug>
   ```

### Phase 2 — Parallel Task Execution (AI Programmer as Orchestrator)

The AI Programmer acts as the **Implementation Orchestrator**, coordinating execution across a **2-Slot Ephemeral Worker Pool** with shared cache.

#### 2-Slot Ephemeral Worker Pool
- **Main Worktree**: `.worktrees/<epic_dir>` (`epic/<epic_slug>`) holds canonical build tooling and base dependencies.
- **Worker Slots**: `.worktrees/<epic_dir>-slot-1` and `...-slot-2`. Caches (`node_modules`, `.venv`, `.gradle`, `target`, `.dart_tool`) are symlinked or APFS-cloned (`cp -c -R`) with **0 byte storage overhead**.
- **Pool CLI**:
  - Init: `python3 "$SKILL_DIR"/resources/scripts/manage_worker_pool.py init --epic-dir <epic_dir> --epic-slug <epic_slug>`
  - Sync: `python3 "$SKILL_DIR"/resources/scripts/manage_worker_pool.py sync --epic-dir <epic_dir> --epic-slug <epic_slug> --slot <1|2>`
  - Merge: `python3 "$SKILL_DIR"/resources/scripts/manage_worker_pool.py merge --epic-dir <epic_dir> --epic-slug <epic_slug> --slot <1|2> --task <task_id>`
  - Cleanup: `python3 "$SKILL_DIR"/resources/scripts/manage_worker_pool.py cleanup --epic-dir <epic_dir> --epic-slug <epic_slug>`

#### Orchestration Workflow per Layer
1. **Parallel Slots**: For 2-task parallel batches from `compute_execution_order.py --parallel`, dispatch 2 implementers into Slot 1 and Slot 2 concurrently. For 1-task batches, dispatch to Slot 1. Isolated worktrees prevent compiler or test collision.
2. **Sequential Merge**: As each task finishes, verify (`run_task_checks.py verify <task mirror>`), merge into main worktree (`manage_worker_pool.py merge`), update dual-workspace status (`sync_task_status.py task <task_id> done`), and sync slot (`manage_worker_pool.py sync`).
3. **Layer Barrier & Cleanup**: Run hermetic sanity tests on main worktree after each layer. Run `manage_worker_pool.py cleanup` after all layers complete before Phase 4.

#### Headless & Autonomous Task Execution
In Autonomous Mode (`/dev-lifecycle --autonomous`), `lifecycle_runner.py` dispatches Role 2.3 (AI Programmer resolved via `.devtool/review_config.json["providers"]["programmer"]`, default `gemini-4-hydrogen-xhigh --effort xhigh --mode auto`) in an isolated process group (`start_new_session=True`) with SIGTERM/SIGKILL supervision, per-task logs, and commits (`[<EPIC_NAME>] Execute <task_slug>`).

0. **Pre-Edit Verification (Impact & Conflict Check)**:
   ```bash
   python3 skills/impact-analysis/resources/scripts/check_code_impact.py \
     --files <target_files> \
     --symbols <target_symbols> \
     --base-ref <base_ref>
   ```
   - If `🔴 DIVERGENCE DETECTED`: **HALT IMMEDIATELY**. Run step 7 (Integrate with develop) now, then rerun check.
   - If `⚠️ UNPROTECTED CODE (0% Coverage)`: Author baseline characterization unit tests first.

1. **Live Dual-Workspace Kanban Status (In-Progress)**:
   ```bash
   python3 skills/dev-implementation/resources/scripts/sync_task_status.py task <task_id> in-progress
   ```

   **Test Assertion Health Rule**: When authoring tests verifying build artifacts, never assert conditions only inside `if path.exists()` without asserting evaluated counts. Always assert `found > 0`.

   **Tri-Persona Subagent Execution Model**:
   When dispatching implementer subagent, operate across the 3-Tier Testing Standard:
   1. **Expert QA (Red Team)**: Authors adversarial BDD scenarios decoupled from code across 5 dimensions (`HP`, `EC`, `ST`, `AR`, `FR`) into `[Tier A - Unit]` vs `[Tier C - Integration]` (validating backward-compatible payloads in Satellite Mode).
   2. **Principal Engineer (TDD Master — Tier A)**: Executes RED failing test -> minimal GREEN code -> REFACTOR/lint/strict types in task files only.
   3. **System Integration & E2E Engineer (Tier C)**: Authors host integration flow tests (`integration_test/`, `*FlowTest.kt`, `App/Tests`, `tests/e2e/`, `tests/integration/`) exercising real DI, navigation, and persistence.

   #### Anti-Rationalization and Doubt-Driven Verification

   Reject rationalizations that cut testing corners:
   - **"Node test is sufficient for web UI"**: REJECTED. Node tests prove only pure data logic. Web defects occur in DOM queries and CSS rendering. Tier C requires headless Playwright with Zero-Console-Error watchdog.
   - **"Mock data in stub is enough"**: REJECTED. Method stubs bypass JSON deserialization and network interceptors. Wire fixtures from `shared-contracts/` are mandatory.
   - **"Red console errors are harmless warnings"**: REJECTED. Zero-Console-Error rule fails Gate 4 on any browser console error.
   - **"Cannot launch simulator, unit test instead"**: REJECTED. Mobile Tier C requires Subcutaneous testing with real DI and in-memory persistence.
   - **"HTML ported from mockup, selectors match"**: REJECTED. Tier C2 UI tests MUST assert `getComputedStyle` and `getBoundingClientRect` properties against the Visual Companion design.

   **Doubt-Driven Verification Protocol**:
   Before claiming done on any task: `CLAIM` Tier C coverage -> `EXTRACT` test reports -> `DOUBT` mock isolation -> `RECONCILE` real headless/subcutaneous tests.

   > [!CRITICAL]
   > ### 🎯 MANDATORY 100% BDD-TO-TEST TRACEABILITY RULE
   > 1. **100% Scenario Traceability**: Every single BDD scenario authored in Phase 1 MUST map directly to at least one concrete automated test function or test block.
   > 2. **Tier Separation**: `[Tier A - Unit]` covered 100% by unit tests; `[Tier C - Integration]` covered 100% by host integration flow tests. Mocks do NOT substitute for Tier C integration tests.
   > 3. **BDD Automation (Tier C, all platforms)**: For every identifier on task's `Covers:` line, author at least one integration test under HLD's `Integration test roots`, carrying the identifier in test name, description, or tag.
   > 4. **Gate to Done**:
   >    ```bash
   >    python3 "$SKILL_DIR"/resources/scripts/run_task_checks.py red <task mirror>                       # before implementing (exits 0 on expected fail)
   >    python3 "$SKILL_DIR"/resources/scripts/run_task_checks.py measure <task mirror> [--timeout 7200] [--resume] # for tasks with MEASURE rows
   >    python3 "$SKILL_DIR"/resources/scripts/run_task_checks.py verify <task mirror>                    # after last change (exits 0 with all pass)
   >    python3 "$SKILL_DIR"/resources/scripts/run_task_checks.py status <task mirror>                    # prints done gate: PASS
   >    ```
   >    Never edit `.devtool/epic/<epic_dir>/evidence/<task_id>.json` by hand. `sync_task_status.py task <id> done` refuses unless evidence matches tree and table.
   >    When task has `Covers:` line, run traceability check (exit 0):
   >    ```bash
   >    python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py tests \
   >      --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md \
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

2. When implementer reports `DONE`:
   - **Selective `task-reviewer` gating:** Dispatch `task-reviewer` **only** when `review_tier: "full"` in task frontmatter, OR task labels include `security`, `architecture`, `concurrency`, or `contract`, OR `> 2` non-test modules change (`sync_task_status.py task <task_id> review`). Trivial single-file tasks without high-risk triggers skip `task-reviewer` (rely on implementer self-review + `run_task_checks.py verify`).
3. If `task-reviewer` is dispatched and finds issues, cycle between `status: "in-progress"` and `status: "review"`.
4. When required review passes (or is skipped per selective gating), `run_task_checks.py status <task mirror>` prints `done gate: PASS`, and `check_bdd_traceability.py tests --ids` exits 0, update status to `done`:
   ```bash
   python3 skills/dev-implementation/resources/scripts/sync_task_status.py task <task_id> done
   ```
   This moves `.devtool/features/<task_id>.md` into `.devtool/features/done/`.
5. Make exactly one commit staging code, task file, and evidence file (`.devtool/epic/<epic_dir>/evidence/<task_id>.json`):
   ```bash
   git status                                    # check nothing unrelated is pending
   git add -A                                    # code changes + .devtool/features/ + evidence
   git commit -m "[EPIC_NAME] <task_title>" -m "- <subtask 1>
   - <subtask 2>"
   ```
   No trailers (no `Co-Authored-By`).
   Log programmer activity and update state (which synchronizes `window.title` to the latest completed task):
   ```bash
   python3 scripts/resume_context.py --log --epic <epic_slug> --task <task_id> --request "<summary>" --action "<tests>"
   python3 scripts/resume_context.py --state --epic <epic_slug>
   ```
6. If implementation diverged from HLD, perform Phase 3 Doc Sync before next task.
7. **Integrate with develop (only when base branch moved).** First check locally whether `<base_ref>` (`develop`) has any commits not in `HEAD` (`git rev-parse develop != $(git merge-base HEAD develop)`). If `develop` has not moved since the worktree branched, skip per-task rebase/verify-tier and proceed immediately to the next task (full integration runs at Stage 4). When `develop` has moved, run in orchestrator from epic worktree after step 5 commit:
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
1. Update epic's Mermaid diagrams in both `<epic_dir>.en.md` and `.vi.md`.
2. Update affected task file(s) prose.
3. Commit separately:
   ```bash
   git commit -m "[EPIC_NAME] Sync HLD after <task_title>" -m "- <diagram or section updated>"
   ```

### Fixes after the last task

Once every task is `done`, a fix is never made by reopening a task. Make it as its own commit on the epic branch, titled `[EPIC_NAME] Fix <what>`. Do not move a done task back, and do not re-record its evidence. `audit_epic.py` lists these commits under "Commits outside tasks". After fixes, run Phase 4 again in full on the new SHA.

### Phase 4 — End of Epic Verification

Once every task is `done`:

0. **Manual Smoke Walkthrough Checklist Generation**:
   Before Gate 4 validation, automatically generate and commit a structured 3–5 step manual smoke checklist from canonical BDD Happy Path scenarios:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/generate_smoke_checklist.py --epic-dir <epic_dir>
   git add .devtool/epic/<epic_dir>/manual_smoke_checklist.md
   git commit -m "[EPIC_NAME] Generate manual smoke walkthrough checklist"
   ```
   This gives the human engineer an immediate 2-minute sanity check walkthrough while keeping the working tree clean and preserving candidate SHA stability.

Then resolve candidate commit SHA (`git rev-parse HEAD`) with a clean tree (`git status --porcelain` prints nothing):

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
   python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py tests \
     --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md \
     --roots <Integration test roots from the HLD> \
     --results <reports written by Integration results commands>
   ```
   Must exit 0: every scenario in `bdd_scenarios.en.md` is covered by at least one passing integration test. `--roots` and `--ids` accept space- or comma-separated values.
5. **Quality check.** Run `@quality_check` on the same SHA:
   - Inputs:
     - `profile`: `"epic"`
     - `base_ref`: `<base_ref>`
     - `repository_sha`: Candidate commit SHA from `git rev-parse HEAD`
   - Only an aggregated verdict of **PASS** bound to that exact SHA qualifies for Gate 4 `🟢 LGTM`.

#### Semantic Test Integrity Governance (Gate 4 Rules)

Gate 4 enforces strict semantic test integrity to prevent false-confidence passes. Registered providers and auditors reject test fakery with **`FAIL`**:
1. **No Reconstructed Logic**: Tests MUST import and invoke production code directly from Allowed files. Tests MUST NOT reconstruct production logic (such as retry loops, progress tracking, mapping transformations, or configuration defaults) locally within test helpers or mock harnesses. If a test reconstructs production logic instead of invoking production symbols, the review reports FAIL.
2. **Immutable Real Artifacts**: Tests MUST execute against genuine, immutable repository artifacts, schemas, and fixtures. Tests MUST NOT substitute synthetic artifacts or mock data that alter scenario anchors or weaken contractual invariants. If a test substitutes synthetic artifacts that alter scenario anchors, the review reports FAIL.

*(Note: These are Gate 4 semantic integrity requirements evaluated by specialist providers and audits; no universal cross-language mechanical coverage claim is made.)*

### Automated Transition to Cross-Model Review (Zero Intermediate Confirmation)

<HARD-GATE>
Do NOT stop to ask for an intermediate Review Choice prompt after Gate 4 passes.
When all tasks are complete and Phase 4 / Gate 4 local machine acceptance passes (🟢 LGTM), the workflow MUST AUTOMATICALLY transition into `/cross-model-review` (`run_external_review.py run --epic-dir <epic_dir> --auto-quota`).
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
3. Commit `review_results.md` after every round (`[EPIC_NAME] Record cross-model review round N`). After every round, run `python3 "$SKILL_DIR"/resources/scripts/run_external_review.py triage --epic-dir <epic_dir>`, fill it as [review-triage.md](references/review-triage.md) says, and inspect `## Auto-Triage Gate` (`AUTO_PASS_FINAL_MINOR_SWEEP`, `AUTO_FIX_ELIGIBLE`, `CIRCUIT_BREAKER_HALT`):
   - **`AUTO_PASS_CLEAN` or `AUTO_PASS_FINAL_MINOR_SWEEP`**: Apply minor fixes if any, re-run full Gate 4 machine acceptance green (Final Convergence Gate), and complete the review stage.
   - **`AUTO_FIX_ELIGIBLE`**: Role 2.3 (AI Programmer) applies verified fixes, commits `[<EPIC_NAME>] Fix <what>`, records `fixed in <sha>`, commits decisions, runs **scoped tests only** (fast static checks and explicitly targeted unit tests covering modified modules; repo-wide pytest and Playwright E2E suites forbidden), and advances to the next review round (up to max 3 rounds). Full Gate 4 is reserved strictly for the Final Convergence Gate.
   - **`CIRCUIT_BREAKER_HALT`**: Halts cleanly and alerts Human Architect only if `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, or remaining Critical findings after Round 3 occur.
4. Once `/cross-model-review` completes (converged with 0 Critical findings) and Gate 4 passes on the latest candidate SHA:
   - Present the synthesized `## Top 3 Highest-Risk Findings (Executive Report)`.
   - Advance directly to **Phase 4.1 (Stage 4: Developer Kanban Review & Finish Decision — Gate 5)**.

### Phase 4.1 — Developer Kanban Review & Finish Decision (🛑 MANDATORY STOP & WAIT — Gate 5)

Once `/cross-model-review` has converged, `@quality_check` reports 🟢 LGTM on candidate SHA, and all tasks completed:
1. **Preserve Kanban Visibility**: All completed `task_*.md` files MUST remain in `.devtool/features/done/`.
2. **Present Executive Summary**: Output summary containing epic slug, worktree path, completed tasks, `@quality_check` verdict, BDD matrix, audit disclosure sections (Evidence, Protected paths, Commits outside tasks, Gate 5 items), and synthesized Executive Review Findings.
3. 🛑 **MANDATORY STOP & WAIT**: Stop calling tools immediately. Prompt user explicitly:
   > "All tasks for epic `<epic_slug>` are completed, `@quality_check` is **🟢 LGTM**, and Cross-model review has converged.
   > All task cards are visible in the **DONE** column on your Kanban dashboard.
   > Please review completed tasks and code changes. Reply to proceed with branch integration (Stage 4 Finish)."
4. **Wait for Gate 5 Confirmation**: Only proceed to Phase 5 when user explicitly approves (then record Gate 5 via `python3 scripts/resume_context.py --gate 5 --epic <epic_slug> --approved "Gate 5 Kanban sign-off"`).

### Phase 5 — Branch Finishing

Only after user explicitly approves Gate 5:
1. Invoke `d3nexus:finishing-a-development-branch` on epic branch (base = `develop`).
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
