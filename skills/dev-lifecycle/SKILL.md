---
name: dev-lifecycle
description: Use this skill to orchestrate epic-scale work from idea to merged branch. It owns the sequence and the five approval gates connecting dev-brainstorming, dev-designer, dev-implementation, and quality_check — which skill runs next, what each stage must hand over, and what to do when a gate fails. Activate it when a request spans multiple components or needs an HLD plus a Kanban task breakdown, when routing an approved spec, or whenever it is unclear which epic stage the work is currently in.
---

# Development Lifecycle

The orchestrator for epic-scale work. It owns **sequence and gates only** — each stage's *how*
stays in that stage's own skill. If you need to know how to run a stage, open its skill; if you
need to know what runs next or what must be true before it does, stay here.

**Announce at start:** "I'm using the dev-lifecycle skill to orchestrate the `<epic_slug>` epic."

**Every stage is entered by invoking its skill.** Reading a stage's description here and then doing that stage's work yourself skips the gate the stage owns.

## When NOT to use this

- Single-component feature, bugfix, or anything one implementation plan covers → `dev-brainstorming` then `writing-plans`. Do not open an epic for it.
- You are already mid-stage and know exactly which stage → go straight to that stage's skill.

## The Sequence

The complete human-facing lifecycle and resume diagrams live in [lifecycles.en.md](../../docs/lifecycles.en.md) and [lifecycles.vi.md](../../docs/lifecycles.vi.md). The runtime sequence is:

1. **Stage 1 (Inception & Spec)**: `dev-brainstorming` -> Gate 1 approval -> Route to `dev-designer` (epic) or `writing-plans` (non-epic).
2. **Stage 2 (Architecture & Tasks)**: `dev-designer` -> Gate 2 approval -> Handoff Choice (Package or Continue).
3. **Stage 3 (Isolated Execution)**: `dev-implementation` -> Gate 3 (order confirmation) -> Task-by-task TDD in worktree -> Gate 4 machine acceptance -> Review Choice loop (Finish, Cross-model review or Local model review) -> Gate 5 Kanban review.
4. **Stage 4 (Finish Branch & Archival)**: `finishing-a-development-branch` -> Rebase, verify by tier, `--no-ff` merge, archive tasks into `.devtool/epic/<slug>/`.

<HARD-GATE>
Do NOT create `implementation_plan.md` or any Antigravity planning-mode artifact.
The d3nexus workflow replaces the native planning mode entirely.
Specs go to `docs/superpowers/specs/` (Stage 1) or `.devtool/epic/<epic_dir>/` (Stage 2+).
Plans go through `writing-plans` skill (non-epic) or `dev-designer` task files (epic).
If you find yourself about to write `implementation_plan.md`, STOP — you are bypassing a gate.

Do NOT skip or auto-decide the Review Choice after Gate 4 passes.
You MUST present the choice between "Finish", "Cross-model review" and "Local model review" on every Gate 4 PASS.
Cross-model review returns to a full Gate 4 run, which presents the choice again until the developer selects Finish. Local model review does the same.
</HARD-GATE>

## Document Contract

Every durable design document produced by this lifecycle MUST be emitted as a synchronized English `.en.md` and Vietnamese `.vi.md` pair. English is canonical; Vietnamese matches its structure and facts. Every variant MUST contain a linked table of contents covering every `##` section, regardless of document length. This applies to specs, HLD/overview documents, BDD scenario documents, and non-epic implementation plans. `task_*.md` files and an epic's `handoff.md` are the only exceptions and remain English-only; `handoff.md` still carries a complete table of contents.

### Markdown Formatting & Quality Standards

Every markdown document produced by this lifecycle MUST pass markdown quality standards:
- **Heading Hierarchy**: Exactly one top-level `# Title` (H1) at the start of the file. Heading levels increment by one without skipping. Space after `#`. No trailing punctuation in headings.
- **Fenced Code Blocks**: Specify a valid language tag (e.g. `bash`, `markdown`, `python`, `json`). Bare fences without a language are prohibited. Runtime skills MUST NOT contain diagram code fences.
- **Lists**: Consistent list markers (`-` for unordered lists), proper indentation, and blank lines around lists.
- **Links & Anchors**: Relative file links must resolve on disk; heading anchor fragments (`#anchor`) must match existing headings.
- **Formatting Hygiene**: No trailing whitespace, no hard tabs, maximum 1 consecutive blank line, and trailing newline.
- **Diagram Standards**: Human documentation (`docs/lifecycles.*.md`, HLDs) follows modern linting standards (`flowchart` over `graph`, quoted node labels containing special characters, valid alphanumeric IDs).

## The Five Gates

Every gate is a **human approval** except Gate 4, which is a machine verdict. Never cross one on your own judgement.

| Gate | Name | Approver | Enforced in | Handoff artefact |
|------|------|----------|-------------|------------------|
| **1** | Spec Approved | User | end of `dev-brainstorming` | `YYYY-MM-DD-<topic>-design.en.md` + `.vi.md` |
| **2** | HLD & Task Breakdown | User | `dev-designer` task-breakdown checkpoint | `<epic_dir>.en.md` + `.vi.md` + `bdd_scenarios.en.md` + `.vi.md` + `task_*.md` |
| **3** | Execution Order | User | `dev-implementation` Phase 1 checkpoint, or Gate 3 (resume) in its Resume Procedure | confirmed order + bootstrapped worktree |
| **4** | Quality LGTM & Check 2 | `audit_epic.py` + `check_bdd_traceability.py` + `quality_check` | `dev-implementation` Phase 4 | `audit_epic.py` report + 🟢 report + coverage matrix + BDD traceability matrix + merge-ready branch |
| **5** | Developer Kanban Sign-Off | User | `dev-implementation` Phase 4.1 checkpoint | User confirmation to proceed with branch finishing and archival |

## Stages

### Resuming an Epic

A request to implement, continue or resume an epic whose `.devtool/epic/<epic_dir>/` already holds `task_*.md` files is past Gate 2 — whether the epic was packaged (`handoff.md` present, Status `Packaged`) or interrupted midway through Stage 3. Announce "Gates 1 and 2 already passed; resuming at Stage 3", invoke `dev-implementation` with that epic name, and let its Entry-Point Detection choose where to start. Never redo Stage 1 or Stage 2 for it. New requirements for such an epic are not a resume: they go to dev-designer's Updating an Existing Epic.

### Stage 1 — Inception & Spec → `dev-brainstorming`

**Invoke `d3nexus:dev-brainstorming`.** Do not write the spec yourself: Gate 1 is *its* user-approval step.
- **Entry:** a raw idea or requirement.
- **Exit (Gate 1):** the user has approved a written spec that passed self-review.
- **Routing decision:** Once the spec is approved, choose:
  - **Epic-scale code** → `dev-designer` (Stage 2). Relocate spec variants to `.devtool/epic/<epic_dir>/`, update links, and enter Stage 2 with the canonical `.en.md` path.
  - **Everything else** → `writing-plans`. This leaves the epic lifecycle; remaining gates do not apply.
If dev-brainstorming decomposed the request into several sub-project specs, **route each one independently**. Never merge multiple specs into one epic.

### Stage 2 — Architecture & Tasks → `dev-designer`

**Invoke `d3nexus:dev-designer`.**
- **Entry:** Gate 1 spec in `.devtool/epic/<epic_dir>/`.
- **Exit (Gate 2):** user has confirmed the proposed task list and granularity.
Treat the approved spec as the source of truth for scope and decisions already made.

### Handoff Choice

Between Gate 2 and Stage 3 the developer decides when, and by whom, the epic is implemented:

> Gate 2 passed: the HLD, BDD scenarios and N task files for `<epic_slug>` are written. How do you want to proceed?
>
> 1. **Package** — write `handoff.md`, mark the epic `Packaged`, and stop.
> 2. **Continue** — enter Stage 3 now (`dev-implementation`, starting with Gate 3: execution order).

**Continue** → invoke `dev-implementation`.
**Package** → run packaging procedure:
1. **Preflight, read-only.** Must exit 0:
   - `python3 "$SCRIPTS"/compute_execution_order.py <epic_slug>`
   - `ls .devtool/epic/<epic_dir>/task_*.md | wc -l` (scan matched count must equal task mirror count)
   - `python3 "$SCRIPTS"/check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks .devtool/epic/<epic_dir>/task_*.md`
   - `python3 "$SCRIPTS"/check_task_contract.py --design --hld .devtool/epic/<epic_dir>/<epic_dir>.en.md --tasks .devtool/epic/<epic_dir>/task_*.md`
2. Copy `references/handoff-template.md` to `.devtool/epic/<epic_dir>/handoff.md` and fill every placeholder; `<N>` is the task count the preflight printed. Add conversation decisions and risks into Open Notes.
3. Lint it: `python3 "$CHECK_DOC" --require-toc .devtool/epic/<epic_dir>/handoff.md`.
4. Mark the epic packaged, then confirm both overview variants changed:
   ```bash
   python3 "$SCRIPTS"/sync_task_status.py epic <epic_dir> Packaged
   grep -n -E '^- \*\*(Status|Trạng thái)\*\*: Packaged' \
     .devtool/epic/<epic_dir>/<epic_dir>.en.md .devtool/epic/<epic_dir>/<epic_dir>.vi.md
   ```
   Two matching lines are required; with fewer, set the Status line by hand in both variants. If the Status read `Queued (backlog) — behind <epic>` before packaging, run the script with `"Packaged (queued behind <epic>)"` instead and copy that line into Open Notes; the `grep` still matches.
5. Commit if `auto_commit: true`: `git commit -m "[<EPIC_NAME>] Package epic for handoff"`.
6. Offer to push only with explicit permission.
7. Print `handoff.md` path and rendered Resume Prompt, then stop.

### Stage 3 — Isolated Execution → `dev-implementation`

**Entry:** Gate 2 passed, HLD and `task_*.md` exist, and Continue chosen (or resuming packaged/interrupted epic).
**Exit (Gate 5):** Gate 4 is 🟢 LGTM and user approves Kanban completion.

- **Gate 3 (Execution Order)**: Present computed execution order and get user confirmation **before** creating worktrees or dispatching subagents.
- **Execution**: One worktree, one task at a time, one commit per task, docs kept truthful. Rebase and integrate with `develop` after each task.

**Review Choice loop**:
After all tasks are complete, run Gate 4. On every PASS, present Review Choice:
- **Option 1: Finish** -> Proceed to Gate 5 (Developer Kanban Review), then Stage 4.
- **Option 2: Cross-model review** -> Invoke `run_external_review.py run` (prompting for Claude CLI or Codex CLI). Record round in `.devtool/epic/<epic_dir>/review_results.md`. Check unresolved findings with `run_external_review.py check --epic-dir <epic_dir>`. Any dismissed finding requires explicit developer instruction. Return to a full Gate 4 run on the new commit.
- **Option 3: Local model review** -> Run `ollama list`, ask which model, then invoke `run_external_review.py run --cli ollama --model <model>`. A model served by the local Ollama reviews each task commit, then the epic, and one round is recorded in the same `review_results.md` under the same `check` rules. Return to a full Gate 4 run on the new commit.

When an epic's tasks were executed by a fast executor model (e.g. Gemini Flash, Claude Haiku, GPT-4o-mini), the agent presents a strong recommendation in the Review Choice prompt:
*"Tasks were executed by a fast executor model. Option 2: Cross-model review (Claude CLI or Codex CLI) is STRONGLY RECOMMENDED to audit test integrity and subtle regressions before finishing the branch."* Local model review does not replace it.

The invariant is **Gate 4 PASS → Review Choice; Finish → Gate 5; Cross-model review → Gate 4 in full; Local model review → Gate 4 in full**. Loop repeats until developer selects Finish.
The review choice loop follows these exact transitions: `EXEC --> G4`, `G4 -->|"yes"| RC`, `RC -->|"1. Finish"| REVIEW`, `XR -->|"round recorded"| G4`, `RC -->|"3. Local model review"| LR`, and `LR -->|"round recorded"| G4`.

> [!CRITICAL]
> **Mandatory Review Choice loop**: Once every task is `done`, run Gate 4. On PASS, the agent MUST stop calling tools and present Review Choice. Silently skipping the choice or assuming Finish is strictly prohibited. Cross-model review and Local model review always return to a full Gate 4 run before Review Choice is presented again.

**Gate 4 Machine Acceptance Criteria:**
Gate 4 grants `🟢 LGTM` only when:
1. `audit_epic.py` exits 0 (committed evidence matches Verification tables, graders disclosed).
2. Enforce result-based traceability: `check_bdd_traceability.py tests --results` exits 0.
3. `@quality_check` returns aggregated verdict of **PASS** with `profile: "epic"` against `<base_ref>` bound to candidate `repository_sha`.

Gate 4 conditions:
1. **Normalized Invocation Contract**: Explicit profile `epic`, target `base_ref`, and candidate `repository_sha`.
2. **Deterministic Aggregation**: All registered providers resolve cleanly under `FAIL > BLOCKED > PASS`.
3. **No Partial Approvals**: `BLOCKED` cannot approve.
4. **Candidate Immutability**: A 🟢 verdict belongs strictly to the tested SHA. If commits change after Gate 4, a fresh traceability check and epic quality run are required before landing.

On failure, route back to `dev-implementation` with defect report; land fixes as `[EPIC_NAME] Fix <what>` commits and re-run Gate 4 in full.

**Gate 5 Developer Kanban Review & Sign-Off:**
Completed tasks remain in `.devtool/features/done/`. Stop calling tools and present final report for visual inspection. On user approval, advance to Stage 4. Any requested adjustments land as Fix commits and return to full Gate 4.

### Stage 4 — Finish Branch → `finishing-a-development-branch`

**Entry:** Gate 5 passed.
**Exit:** Branch rebased onto `develop`, verified by tier, merged `--no-ff`, and tasks archived into `.devtool/epic/<epic_dir>/`.

## When a Gate Fails

| Gate | On failure, return to |
|------|----------------------|
| 1 | Stage 1 — revise spec, re-run self-review |
| 2 | Stage 2 — adjust task breakdown |
| 3 | Stage 3 Phase 1 — reorder tasks manually |
| 4 | Stage 3 — fix findings as Fix commits, re-run traceability and quality_check in full |
| 5 | Stage 3 — apply user adjustments as Fix commits, re-run Gate 4 in full |

Never advance on a partial pass or re-run isolated checks.

## Red Flags

- Writing to `implementation_plan.md` or any Antigravity native planning artifact.
- Skipping `dev-brainstorming` because scope seems clear.
- Routing an approved spec straight to implementation, skipping Stage 2 for epic-scale work.
- Merging several sub-project specs into one epic directory.
- Creating a worktree or dispatching subagents before Gate 3. Recreating the worktree of an existing epic branch (dev-implementation Resume Procedure) is not creating one.
- Invoking `dev-implementation` without presenting Handoff Choice.
- Packaging an epic without preflight, or pushing without explicit permission.
- Treating packaged Gate 3 as passed.
- Redoing design of an epic whose task files exist; use Updating an Existing Epic.
- Merging to `develop` without Gate 4 🟢.
- Granting Gate 4 without a passing traceability check on the same SHA, or without a passing `audit_epic.py`.
- Ticking checkboxes or writing evidence by hand instead of running `run_task_checks.py`.
- Changing Verification tables, Allowed files, or protected paths without stopping to ask.
- Skipping Review Choice after Gate 4 PASS or auto-selecting Finish.
- Reusing a Gate 4 PASS after review rounds, finding decisions, or Fix commits change SHA.
- Never pick the review CLI for the developer; picking the review CLI for the developer instead of prompting for Claude CLI or Codex CLI is forbidden.
- Picking the Ollama model for the developer instead of running `ollama list` and asking.
- Writing `dismissed` decisions in `review_results.md` without explicit developer words.
- Merging to `develop` manually instead of through `integrate_branch.py land`.
- Starting a task while integration with `develop` is failing.
- Invoking `finishing-a-development-branch` without Gate 5 user sign-off.
- Archiving tasks from `.devtool/features/done/` prematurely before Gate 5 sign-off.
- Leaving completed tasks or draft specs unarchived after branch integration.
- Translating `task_*.md`; task files remain English-only.

## Stage Skills

| Stage | Skill | Gate it enforces |
|-------|-------|------------------|
| 1 | `dev-brainstorming` | 1 |
| 2 | `dev-designer` | 2 |
| 3 | `dev-implementation` | 3, triggers 4, and enforces 5 |
| 3 (verification) | `quality_check` + `check_bdd_traceability.py` | 4 |
| 4 | `finishing-a-development-branch` | — |
