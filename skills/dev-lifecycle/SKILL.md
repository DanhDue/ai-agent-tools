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

Human-facing lifecycle and resume diagrams live in [lifecycles.en.md](../../docs/lifecycles.en.md) and [lifecycles.vi.md](../../docs/lifecycles.vi.md). Runtime sequence (Interactive & Autonomous Pipeline Mode):

1. **Stage 1 (Inception & Spec)**: `dev-brainstorming` -> Gate 1 approval -> Route to `dev-designer` (epic) or `writing-plans` (non-epic).
2. **Stage 2 (Architecture & Tasks)**: `dev-designer` -> Gate 2 approval -> Handoff (`package_epic.py`) -> Principal Review (`Claude -> Codex -> Kiro -> Argon` via `check-quota`, Auto-fix up to Max 3 rounds).
3. **Stage 3 (Automated Execution & Audit)**: Role 2.3 (**Gemini Flash 3.8**) -> `dev-implementation` -> Automated Gate 3 (execution order & worktree) -> TDD in worktree -> Gate 4 local PASS -> Automated Cross-Model Review (`review_config.json`, Auto-fix up to Max 3 rounds) -> Gate 4 re-verification green.
4. **Stage 4 (Finish Decision, Integration & Archival)**: Prompt Human Architect for Finish Decision & Gate 5 Sign-off -> `finishing-a-development-branch` -> Archive tasks into `.devtool/epic/<slug>/`, rebase, verify by tier (`Test All` once), `--no-ff` or squash merge, explicit Git push confirmation.

<HARD-GATE>
Do NOT create `implementation_plan.md` or any Antigravity planning-mode artifact.
The d3nexus workflow replaces the native planning mode entirely.
Specs go to `docs/superpowers/specs/` (Stage 1) or `.devtool/epic/<epic_dir>/` (Stage 2+).
Plans go through `writing-plans` skill (non-epic) or `dev-designer` task files (epic).
If you find yourself about to write `implementation_plan.md`, STOP — you are bypassing a gate.

Do NOT prompt the developer for intermediate Review Choice or Gate 3 confirmation pauses.
Once Gate 2 passes and dev-implementation is entered, Gate 3 execution order and worktree creation run automatically.
When all tasks complete and Gate 4 passes locally, transition AUTOMATICALLY into cross-model review.
The decision to Finish belongs strictly to Stage 4 (Gate 5 sign-off) after Cross-model review completes.
</HARD-GATE>

## Document Contract

Durable design documents MUST be emitted as synchronized `.en.md` (canonical) and `.vi.md` pairs with a linked ToC covering every `##` section (specs, HLDs, BDD scenarios, non-epic plans). Only `task_*.md` and `handoff.md` are English-only (`handoff.md` still requires a ToC).

### Markdown Quality Standards
Synchronized `.en.md`/`.vi.md` pairs with ToCs. Enforce heading hierarchy, valid code block tags, resolving links, no trailing whitespace, and `flowchart` with quoted labels in human docs.

## The Five Gates

Every gate is a **human approval** except Gate 4 (machine verdict). Never cross one on your own judgement. Record and query approvals in `.devtool/GATE_LEDGER.md` via `resume_context.py --gate <1..5>` and `--check-gate <1..5>`.

| Gate | Name | Approver | Enforced in | Handoff artefact |
|------|------|----------|-------------|------------------|
| **1** | Spec Approved | User | `dev-brainstorming` | `YYYY-MM-DD-<topic>-design.en.md` + `.vi.md` |
| **2** | HLD & Task Breakdown | User | `dev-designer` | `<epic_dir>.en.md` + `.vi.md` + `bdd_scenarios.en.md` + `.vi.md` + `task_*.md` |
| **3** | Execution Order | Automated (AI Assistant) | `dev-implementation` Phase 1 / Resume | auto-resolved order + bootstrapped worktree |
| **4** | Quality LGTM & Check 2 | `audit_epic.py` + `check_bdd_traceability.py` + `quality_check` | `dev-implementation` Phase 4 | `audit_epic.py` + 🟢 report + coverage + BDD traceability + merge-ready branch |
| **5** | Developer Kanban Sign-Off & Finish | User | `dev-implementation` Phase 4.1 / Stage 4 | User confirmation for branch finishing and archival |

## Stages

### Resuming an Epic

An epic whose `.devtool/epic/<epic_dir>/` holds `task_*.md` files is past Gate 2 — whether `Packaged` (`handoff.md` present) or interrupted in Stage 3. Announce "Gates 1 and 2 already passed; resuming at Stage 3", invoke `dev-implementation`, and let its Entry-Point Detection choose where to start. Never redo Stage 1 or 2; route new requirements to dev-designer's Updating an Existing Epic.

### Autonomous Mode (`/dev-lifecycle --autonomous`)

For hands-off execution, `lifecycle_runner.py` drives Stage 2 and Stage 3:
- **Tri-Role**: 2.1 Architect (strategy/gates), 2.2 Assistant (HLD/fix-plan review), 2.3 Programmer (Gemini 3.8 Flash High).
- **Automation**: Auto Gate 3 order, process group timeouts, auto-triage, and Assistant fix plan review (`APPROVED`/`ADJUSTED`/`CRITICAL_CONFLICT`).
- **Safety**: Circuit breakers on contract conflicts, fix loops, and max rounds; final Top 3 report halts at `AWAITING_FINISH`.
- See [references/autonomous-mode.md](references/autonomous-mode.md).

### Stage 1 — Inception & Spec → `dev-brainstorming`

**Invoke `d3nexus:dev-brainstorming`.** Gate 1 is its user-approval step.
- **Entry:** raw idea or requirement. **Exit (Gate 1):** user-approved spec passing self-review.
- **Routing:** **Epic-scale code** → relocate spec variants to `.devtool/epic/<epic_dir>/`, update links, enter `dev-designer` (Stage 2). **Everything else** → `writing-plans`. Route decomposed sub-project specs independently; never merge multiple specs into one epic.

### Stage 2 — Architecture & Tasks → `dev-designer`

**Invoke `d3nexus:dev-designer`.**
- **Entry:** Gate 1 spec in `.devtool/epic/<epic_dir>/`. **Exit (Gate 2):** user-confirmed task list and granularity.
- **3-Tier Document Separation ("Prompt to Maintain" vs LLM SSOT):**
  - `<epic_dir>.{en,vi}.md` (HLD): Human-facing system overview & Feature Maintenance Map (1 Architecture diagram, conditional Sequence diagram, canonical entry points — no duplicate embedded Gherkin).
  - `bdd_scenarios.{en,vi}.md`: Exhaustive adversarial edge-case, boundary, exception, and atomic-rollback suite across the 5 dimensions.
  - `task_*.md`: Self-contained LLM Execution SSOT loaded one task at a time during Stage 3.
When an epic depends on other epics, declare `- **Depends on epic**: <epic_slug_or_dir>[, ...]` in HLD Meta Data.

### Handoff Choice

Once Gate 2 passes, **automatically package the epic and run `/save-context`** before prompting:
```bash
python3 skills/dev-implementation/resources/scripts/package_epic.py <epic_dir> [--revise --reason "<reason>"]
```
Packaging steps (automated by `package_epic.py`):
1. **Preflight:** `python3 "$SCRIPTS"/check_epic_readiness.py <epic_dir>` (runs `check_task_contract.py --design`). First line gives task count.
2. Copy `references/handoff-template.md` to `.devtool/epic/<epic_dir>/handoff.md` and fill placeholders; `<N>` is the task count the preflight printed.
3. Lint: `python3 "$CHECK_DOC" --require-toc .devtool/epic/<epic_dir>/handoff.md`.
4. Mark packaged and verify both overview variants:
   ```bash
   python3 "$SCRIPTS"/sync_task_status.py epic <epic_dir> Packaged
   grep -n -E '^- \*\*(Status|Trạng thái)\*\*: Packaged' \
     .devtool/epic/<epic_dir>/<epic_dir>.en.md .devtool/epic/<epic_dir>/<epic_dir>.vi.md
   ```
   If previously queued, use `"Packaged (queued behind <epic>)"` and copy into Open Notes.
5. Commit if `auto_commit: true`: `git commit -m "[<EPIC_NAME>] Package epic for handoff"`. Offer to push only with permission.
6. Run `/save-context`: `resume_context.py --gate 2 --epic <epic_slug> --approved "<summary>"`, `resume_context.py --state --epic <epic_slug> --status "Stage 2: Packaged & Ready"`, emit prompts (`--emit-prompt principal-review` and `implement`), and print `handoff.md` path.
7. Stop calling tools and present **Handoff Choice / Principal Review Choice** — follow [references/principal-review.md](references/principal-review.md):

> Gate 2 passed: `<epic_slug>` is packaged (`handoff.md`) and context saved (`/save-context`). How do you want to proceed?
> 1. **`/principal-review` (Principal Review)** — cross-model design review against source (Claude CLI, Codex CLI, Antigravity CLI, or Kiro CLI).
> 2. **`/dev-implementation` (Continue to Stage 3)** — enter Stage 3 now (`dev-implementation`, starting at Gate 3).
> 3. **Done (Stop here)** — keep packaged handoff for a later session.

- **Principal Review** → invoke `d3nexus:principal-review` (`--auto-quota` priority `Claude -> Codex -> Kiro -> Argon`, 3-Round Convergence Funnel, Auto-Triage Gate auto-revises package and `/save-context` up to max 3 rounds).
- **Continue** → invoke `d3nexus:dev-implementation`.

### Stage 3 — Isolated Execution → `dev-implementation`

**Entry:** Gate 2 passed, HLD and `task_*.md` exist, and Continue chosen (or resuming packaged/interrupted epic).
**Exit (Gate 5):** Gate 4 is 🟢 LGTM and user approves Kanban completion.

- **Prerequisites & Concurrency Check**: If `Depends on epic:` is declared, verify prerequisites via `sync_task_status.py check-prereqs <epic_dir>`. If queued behind another epic, inspect conflicts via `sync_task_status.py check-conflicts <epic_dir>` and promote when confirmed via `sync_task_status.py promote <epic_dir> [--force]`.
- **Gate 3 (Execution Order & Worktree — Automated)**: The AI Assistant automatically resolves execution order via `compute_execution_order.py`, creates/bootstraps the isolated Git worktree, records Gate 3 in `.devtool/GATE_LEDGER.md` via `resume_context.py --gate 3`, and invokes Role 2.3 (AI Programmer) without pausing for manual confirmation. Manual halt occurs ONLY on fatal errors (cyclic DAG or unresolvable prerequisites).
- **Execution**: One worktree, one task at a time, one commit per task, docs kept truthful. Rebase and integrate with `develop` after each task.

**Automated Review Pipeline (Gate 4 Local PASS → Automatic Cross-Model Review)**:
Once all tasks are complete and Phase 4 / Gate 4 local machine verification returns PASS (🟢 LGTM):
1. **Zero-Pause Transition**: The workflow automatically transitions into `d3nexus:cross-model-review` without pausing or asking for an intermediate Review Choice.
2. **Review Execution**: `run_external_review.py run --epic-dir <epic_dir> --base <base_ref> --auto-quota` runs using the provider priority and model configured in `.devtool/review_config.json`.
3. **Auto-Triage & Auto-Fix Funnel (Max 3 Rounds)**:
   - Evaluates `AUTO_PASS_CLEAN`, `AUTO_PASS_FINAL_MINOR_SWEEP`, and `AUTO_FIX_ELIGIBLE`.
   - AI Programmer applies verified fixes, commits them, records decisions, and automatically re-runs Gate 4 in full without intermediate confirmation.
   - Halts cleanly ONLY on Circuit Breakers (`SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, or remaining Critical findings after Round 3).
4. **Transition to Stage 4 (Finish Decision)**: Once the review converges and Gate 4 passes on the candidate SHA, render the synthesized Executive Report (Top 3 Highest-Risk Findings across rounds) and present the **Stage 4 Finish Decision & Gate 5 Sign-off** to the Human Architect.

> [!CRITICAL]
> **Streamlined Pipeline Invariant**: Once every task is `done`, Gate 4 runs automatically. On PASS, the agent MUST NOT prompt for an intermediate choice between Finish and Review; it automatically invokes Cross-Model Review. The decision to Finish belongs strictly in Stage 4 (Gate 5 Sign-Off) after review convergence is complete.

**Gate 4 Machine Acceptance Criteria:**
Gate 4 grants `🟢 LGTM` only when:
1. `audit_epic.py` exits 0 (committed evidence matches Verification tables, graders disclosed).
2. Enforce result-based traceability: `check_bdd_traceability.py tests --results` exits 0.
3. `@quality_check` returns aggregated verdict of **PASS** with `profile: "epic"` against `<base_ref>` bound to candidate `repository_sha`.

Gate 4 conditions:
1. **Contract**: Explicit profile `epic`, target `base_ref`, and candidate `repository_sha`.
2. **Aggregation**: Registered providers resolve under `FAIL > BLOCKED > PASS`.
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
- Creating a worktree before the AI Assistant has resolved the dependency DAG. Recreating the worktree of an existing epic branch (dev-implementation Resume Procedure) is not creating one.
- Invoking `dev-implementation` without presenting Handoff Choice.
- Packaging an epic without preflight, or pushing without explicit permission.
- Redoing design of an epic whose task files exist; use Updating an Existing Epic.
- Merging to `develop` without Gate 4 🟢.
- Granting Gate 4 without a passing traceability check on the same SHA, or without a passing `audit_epic.py`.
- Ticking checkboxes or writing evidence by hand instead of running `run_task_checks.py`.
- Changing Verification tables, Allowed files, or protected paths without stopping to ask.
- Prompting developer for intermediate Review Choice or Gate 3 confirmation pauses instead of running the automated pipeline.
- Advancing to Stage 4 (Finish) without completing Cross-Model Review convergence and Gate 5 sign-off.
- Reusing a Gate 4 PASS after review rounds, finding decisions, or Fix commits change SHA.
- Prohibited: picking the review CLI for the developer instead of prompting for Claude CLI, Codex CLI, or Antigravity CLI.
- Picking the Principal Review CLI for the developer.
- Picking the Ollama model for the developer instead of running `ollama list` and asking.
- Acting on review findings before presenting the triage from `run_external_review.py triage`.
- Acting on a Principal Review finding before triage.
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
