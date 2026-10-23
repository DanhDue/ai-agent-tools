---
name: dev-implementation
description: Use when an epic already has an approved HLD and Kanban task files (`.devtool/epic/<epic_dir>/` + `.devtool/features/task_*.md`) and you need to actually execute those tasks against the codebase, in the right order, inside an isolated worktree across Web Applications, Flutter, Android Native, iOS Native, Python, or Rust projects.
---

# Development Implementation

## Overview

Runs an already-approved epic's Kanban tasks end-to-end: reload the epic's own docs for context, detect the platform (Flutter, Android Native, iOS Native, Web, Python, or Rust), compute a dependency-safe execution order, bootstrap one worktree that can actually build this project, then drive each task sequentially through `d3nexus:subagent-driven-development` with exactly one commit per task.

**Core principle:** One worktree, one task at a time, one commit per task, docs stay truthful.

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
1. Read, in full:
   - `.devtool/epic/<epic_dir>/<epic_dir>.en.md` (the canonical HLD — never `.vi.md` for decisions, that's a synced translation).
   - `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` (the canonical behavioral contract across the 5 dimensions, if present; `.vi.md` is its synchronized translation).
   - Every `.devtool/features/task_*.md` whose frontmatter `epic:` matches `<epic_slug>`.
   - Any spec file(s) linked from the HLD's Meta Data section.
   - `.devtool/epic/<epic_dir>/handoff.md`, when present — the packaging record. Use its Open Notes as context; it is never updated after packaging.

#### Bounded Context Injection & Spec Fidelity

Before implementing any task, the executor MUST adhere strictly to the 3-step Bounded Context Injection protocol:
1. Read the active task file (`.devtool/features/task_*.md`).
2. Read the Allowed files and Read-only context listed in the task file.
3. Look up exact symbols and architectural choices declared in `Decisions Already Made`; do not perform undirected whole-repository searches.

**Strict Spec Fidelity**: Implement strictly within the boundaries specified by the active task and its Allowed files. Do not add speculative abstractions, configurability, or adjacent refactoring not requested by the task specification.

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

`git ls-remote` asks each remote directly, so an epic branch pushed from another clone shows before any fetch; if a remote cannot be reached, fall back to `git branch -r --list '*/epic/<epic_slug>'`. The last command reads the epic's task mirrors (`sync_task_status.py` keeps them in step with `.devtool/features/` and `.devtool/features/done/`); its flattened order prints each task's status as `[priority, status]`. Evaluate the rows top-down — first match wins — and announce it: "Entry point: row N — <state>."

| # | Signals | State | Entry point |
|---|---------|-------|-------------|
| 1 | Overview Status is `Done` | Finished, or Stage 4 interrupted | With no epic branch left, report finished and stop. With epic branch still present, Stage 4 was interrupted or its PR is still open: report and ask |
| 2 | No epic branch, and any task is `backlog` | Queued behind another epic | Stop. Flipping `backlog` to `todo` is developer's call |
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
   python3 "$SKILL_DIR"/resources/scripts/compute_execution_order.py <epic_slug>
   ```
   Check scan summary line (`Scanned N task_*.md files; M matched epic ...`). If `M` is smaller than expected, fix broken frontmatter before proceeding.
2. Read "Manual review advised" section (if any) and cross-check against Phase 0 context. Adjust flattened order by hand if a prose note should win.
3. **Checkpoint (Gate 3):** present the final order to user and get confirmation before touching git.
   In the same message, state the Principal Review status (`not run`, `round <n>: PASS`, or `round <n>: decided`; stop with the triage if that check exits 1), and ask once for permission to fast-forward local `develop` from its upstream for the rest of this epic (Phase 1 step 4 and Phase 2 step 7).

   Before presenting order, run BDD traceability plan check:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py plan \
     --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md \
     --tasks .devtool/epic/<epic_dir>/task_*.md
   ```
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
5. Bootstrap worktree using platform tooling (`bootstrap_worktree.sh`, Gradle sync, Tuist, npm/pnpm, uv sync, cargo check).
6. Never copy build caches (`.dart_tool/`, `/build/`, `.build/`, `android/**/.cxx/`) from another checkout into this worktree.

### Phase 2 — Sequential Task Execution

For each task in confirmed order, follow `d3nexus:subagent-driven-development`.

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
   1. **Expert QA (Red Team Persona)**: Authors BDD Scenarios in complete isolation from coding, purely from HLD and `bdd_scenarios.en.md`, applying 5 dimensions: Happy Paths, Edge Cases & Boundaries, State Transitions, Async / Race Conditions, Failures & Resilience. Categorizes scenarios into `[Tier A - Unit]` vs `[Tier C - Integration]`.
   2. **Principal Engineer (TDD Master Persona — Tier A)**: Implements unit logic, state emissions, and hermetic tests using platform tools (Dart/Flutter, Kotlin/Compose, Swift/SwiftUI, TypeScript/Web, Python/pytest, Rust/cargo). Enforces RED failing test first -> minimal GREEN code -> REFACTOR formatting, linter, strict types.
   3. **System Integration & E2E Engineer (Tier C Persona)**: Implements host integration flow tests (`integration_test/`, `*FlowTest.kt`, `App/Tests`, `tests/e2e/`, `tests/integration/`) connecting DI, navigation, and persistence contracts.

   > [!CRITICAL]
   > ### 🎯 MANDATORY 100% BDD-TO-TEST TRACEABILITY RULE
   > 1. **100% Scenario Traceability**: Every single BDD scenario authored in Phase 1 MUST map directly to at least one concrete automated test function or test block.
   > 2. **Tier Separation**: `[Tier A - Unit]` covered 100% by unit tests; `[Tier C - Integration]` covered 100% by host integration flow tests. Mocks do NOT substitute for Tier C integration tests.
   > 3. **BDD Automation (Tier C, all platforms)**: For every identifier on task's `Covers:` line, author at least one integration test under HLD's `Integration test roots`, carrying the identifier in test name, description, or tag.
   > 4. **Gate to Done**:
   >    ```bash
   >    python3 "$SKILL_DIR"/resources/scripts/run_task_checks.py red <task mirror>     # before implementing (exits 0 on expected fail)
   >    python3 "$SKILL_DIR"/resources/scripts/run_task_checks.py verify <task mirror>  # after last change (exits 0 with all pass)
   >    python3 "$SKILL_DIR"/resources/scripts/run_task_checks.py status <task mirror>  # prints done gate: PASS
   >    ```
   >    Never edit `.devtool/epic/<epic_dir>/evidence/<task_id>.json` by hand. `sync_task_status.py task <id> done` refuses unless evidence matches tree and table.
   >    When task has `Covers:` line, run traceability check (exit 0):
   >    ```bash
   >    python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py tests \
   >      --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md \
   >      --roots <Integration test roots from the HLD> \
   >      --ids <identifiers on the task's Covers: line>
   >    ```
   > 5. **Stop and Report**: A `Stop and Report If` condition in task is reported as `BLOCKED`. Never edit Verification table, Definition of Done, Allowed files or Covers line, or protected path, to force a pass.

2. When implementer reports `DONE`, synchronize review status:
   ```bash
   python3 skills/dev-implementation/resources/scripts/sync_task_status.py task <task_id> review
   ```
3. If review finds issues, cycle between `status: "in-progress"` and `status: "review"`.
4. When both reviews pass, `run_task_checks.py status <task mirror>` prints `done gate: PASS` and `check_bdd_traceability.py tests --ids` exits 0, update status to `done`:
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
6. If implementation diverged from HLD, perform Phase 3 Doc Sync before next task.
7. **Integrate with develop.** Run in orchestrator from epic worktree after step 5 commit:
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

Once every task is `done`, resolve candidate commit SHA (`git rev-parse HEAD`) with a clean tree (`git status --porcelain` prints nothing):

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

### Review Choice — after every Gate 4 PASS

<HARD-GATE>
You MUST NOT skip or auto-decide Review Choice after Gate 4 passes.
Present the choice between "Finish", "Cross-model review" and "Local model review" and wait for the developer's explicit instruction.
Cross-model review and Local model review must return to Phase 4 in full; only the next Gate 4 PASS may present Review Choice again.
</HARD-GATE>

The loop invariant is **Gate 4 PASS → Review Choice; Finish → Gate 5; Cross-model review → Gate 4 in full; Local model review → Gate 4 in full**.
<!-- Workflow transitions:
moretasks -- "no, epic done" --> phase4
phase4 -- "PASS" --> choice
choice -- "Finish" --> checkpoint4
review -- "round recorded" --> phase4
choice -- "Local model review" --> localreview
localreview -- "round recorded" --> phase4
-->
Ask developer and wait for answer:

> Gate 4 is 🟢 LGTM for `<candidate_sha>`. How do you want to proceed?
>
> 1. **Finish** — continue to Gate 5, then `finishing-a-development-branch`.
> 2. **Cross-model review** — an independent model reviews the epic through Claude CLI or Codex CLI (`command -v claude codex`).
> 3. **Local model review** — a model served by your local Ollama reviews the epic task by task (`ollama list`).

Option 1 goes to Phase 4.1 / Gate 5. Option 2 runs in epic worktree with clean tree:
```bash
python3 "$SKILL_DIR"/resources/scripts/run_external_review.py run \
  --epic-dir <epic_dir> --base <base_ref> --cli claude|codex
```
Commit `review_results.md` after every round (`[EPIC_NAME] Record cross-model review round N`). After every round of option 2 or 3, run `python3 "$SKILL_DIR"/resources/scripts/run_external_review.py triage --epic-dir <epic_dir>`, fill it as [review-triage.md](references/review-triage.md) says, present it, and wait for the developer's decisions before any Fix commit or Decision cell. Then make the Fix commits, record the decisions, commit, and rerun Phase 4 / Gate 4 in full.

Option 3 runs `ollama list` first and asks the developer which model to use; never pick it. Then, in the epic worktree with a clean tree:
```bash
python3 "$SKILL_DIR"/resources/scripts/run_external_review.py run \
  --epic-dir <epic_dir> --base <base_ref> --cli ollama --model <model>
```
The model reviews each task commit, then the epic, and one round is recorded with the same `check` rules. Sampling and context come from the model's Modelfile; `--num-ctx` overrides the context and `--host` the server. Setup: [local-review-setup.md](references/local-review-setup.md). Commit each round as `[EPIC_NAME] Record local model review round N`, then handle findings as for option 2.

### Phase 4.1 — Developer Kanban Review Checkpoint (🛑 MANDATORY STOP & WAIT — Gate 5)

Once `@quality_check` reports 🟢 LGTM, all tasks completed, and developer selects **Finish** at Review Choice:
1. **Preserve Kanban Visibility**: All completed `task_*.md` files MUST remain in `.devtool/features/done/`.
2. **Present Executive Summary**: Output summary containing epic slug, worktree path, completed tasks, `@quality_check` verdict, BDD matrix, and audit disclosure sections (Evidence, Protected paths, Commits outside tasks, Gate 5 items).
3. 🛑 **MANDATORY STOP & WAIT**: Stop calling tools immediately. Prompt user explicitly:
   > "All tasks for epic `<epic_slug>` are completed and `@quality_check` is **🟢 LGTM**.
   > All task cards are visible in the **DONE** column on your Kanban dashboard.
   > Please review completed tasks and code changes. Reply to proceed with branch integration."
4. **Wait for Gate 5 Confirmation**: Only proceed to Phase 5 when user explicitly approves.

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
