---
name: dev-lifecycle
description: Use this skill to orchestrate epic-scale work from idea to merged branch. It owns the sequence and the five approval gates connecting dev-brainstorming, dev-designer, dev-implementation, and quality_check — which skill runs next, what each stage must hand over, and what to do when a gate fails. Activate it when a request spans multiple components or needs an HLD plus a Kanban task breakdown, when routing an approved spec, or whenever it is unclear which epic stage the work is currently in.
---

# Development Lifecycle

The orchestrator for epic-scale work. It owns **sequence and gates only** — each stage's *how* stays in that stage's own skill.

**Announce at start:** "I'm using the dev-lifecycle skill to orchestrate the `<epic_slug>` epic."

**Every stage is entered by invoking its skill.** Doing a stage's work yourself skips its gate.

## When NOT to use this

- Single-component feature, bugfix, or anything one implementation plan covers → `dev-brainstorming` then `writing-plans`. Do not open an epic for it.
- You are already mid-stage and know exactly which stage → go straight to that stage's skill.

## The Sequence

Human-facing lifecycle and resume diagrams live in [lifecycles.en.md](../../docs/lifecycles.en.md) and [lifecycles.vi.md](../../docs/lifecycles.vi.md). Runtime sequence (Interactive & Autonomous Pipeline Mode):

1. **Stage 1 (Inception & Spec)**: `dev-brainstorming` -> Gate 1 approval -> Route to `dev-designer` (epic) or `writing-plans` (non-epic).
2. **Stage 2 (Architecture & Tasks)**: `dev-designer` -> Gate 2 approval -> Provider/model priority prompt -> `/principal-review` (auto, up to Max 3 rounds) -> Post-review Package (`package_epic.py`) & print implement prompt -> Choice (**Triển khai (tự động)** vs **Dừng lại**).
3. **Stage 3 (Automated Execution & Audit)**: Role 2.3 (**Gemini Flash 3.8**) -> `dev-implementation` -> Automated Gate 3 (execution order & worktree) -> TDD in worktree -> Gate 4 local PASS -> Automated Cross-Model Review (`review_config.json`, Auto-fix up to Max 3 rounds) -> Gate 4 re-verification green.
4. **Stage 4 (Finish Decision, Integration & Archival)**: Prompt Human Architect for Finish Decision & Gate 5 Sign-off -> `finishing-a-development-branch` -> Archive tasks into `.devtool/epic/<slug>/`, rebase, verify by tier (`Test All` once), `--no-ff` or squash merge, explicit Git push confirmation.

<HARD-GATE>
Do NOT create `implementation_plan.md` or Antigravity planning-mode artifacts.
Specs go to `docs/superpowers/specs/` (Stage 1) or `.devtool/epic/<epic_dir>/` (Stage 2+); plans go through `writing-plans` (non-epic) or `dev-designer` tasks (epic).
Do NOT package (`package_epic.py`) before `/principal-review` completes.
Once Gate 2 passes, ask for provider/model priority and run `d3nexus:principal-review`; package (`handoff.md`) only when converged, print implementation prompt, and ask **Triển khai (tự động)** vs **Dừng lại**.
In **Triển khai (tự động)**, Gate 3 order and worktree bootstrap run automatically.
When tasks complete and Gate 4 passes locally, transition automatically into Cross-model review. Finish belongs strictly in Stage 4 (Gate 5 sign-off).
</HARD-GATE>

## Document Contract

Durable design documents MUST be emitted as synchronized `.en.md` (canonical) and `.vi.md` pairs with a linked ToC covering every `##` section (specs, HLDs, BDD scenarios, non-epic plans). Only `task_*.md` and `handoff.md` are English-only (`handoff.md` still requires a ToC).

### Markdown Quality Standards
Enforce heading hierarchy, valid code block tags, resolving links, no trailing whitespace, and quoted flowchart labels in human docs.

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
- **3-Tier Document Separation:**
  - `<epic_dir>.{en,vi}.md` (HLD): System overview & Feature Maintenance Map (1 Architecture diagram, optional Sequence diagram, canonical entry points — no duplicate Gherkin).
  - `bdd_scenarios.{en,vi}.md`: Adversarial edge-case, boundary, exception, and rollback suite across 5 dimensions.
  - `task_*.md`: Self-contained LLM Execution SSOT loaded one task at a time during Stage 3.
Declare `- **Depends on epic**: <epic_slug_or_dir>[, ...]` in HLD Meta Data when an epic depends on others.

### Handoff Choice

Follow [references/principal-review.md](references/principal-review.md) across Stage 2 -> Principal Review -> Packaging -> Stage 3:

- **Gate 2 Unified Confirmation (Tasks & AUTO MODE):** After Gate 2 and `check_epic_readiness.py <epic_dir>` pass, save Gate 2 & state (`--status "Stage 2: Ready for Principal Review"`), read `.devtool/review_config.json`, stop calling tools, and present the **provider/model priority** order for reviews (`/principal-review` and `/cross-model-review`):
  1. **(Recommended) Phê duyệt & Chạy AUTO MODE xuyên suốt (Triển khai (tự động)):** Run `/principal-review` -> package `handoff.md` -> proceed automatically into `/dev-implementation` (2-slot pool) -> `/cross-model-review` without pausing. Halts ONLY on Circuit Breakers or at Gate 5 (Finish/Merge).
  2. **Phê duyệt & Handoff Mode (Dừng lại):** Run `/principal-review` -> package `handoff.md` -> stop cleanly to copy implementation prompt for another profile.
- **Automatic `/principal-review`:** Once confirmed, automatically invoke `d3nexus:principal-review` (`--auto-quota` / `--provider-priority` / `--cli`, max 3 rounds; intermediate rounds run `check_epic_readiness.py`, never `package_epic.py`).
- **End-of-Review Packaging:** Upon convergence, run `python3 skills/dev-implementation/resources/scripts/package_epic.py <epic_dir> [--revise --reason "<reason>"]` (without `--revise` when `handoff.md` does not exist):
1. **Preflight:** `python3 "$SCRIPTS"/check_epic_readiness.py <epic_dir>` (runs `check_task_contract.py --design`). First line prints task count.
2. Copy `references/handoff-template.md` to `.devtool/epic/<epic_dir>/handoff.md` (`<N>` is the task count the preflight printed) and lint via `python3 "$CHECK_DOC" --require-toc .devtool/epic/<epic_dir>/handoff.md`.
3. Mark packaged and verify both overview variants:
   ```bash
   python3 "$SCRIPTS"/sync_task_status.py epic <epic_dir> Packaged
   grep -n -E '^- \*\*(Status|Trạng thái)\*\*: Packaged' \
     .devtool/epic/<epic_dir>/<epic_dir>.en.md .devtool/epic/<epic_dir>/<epic_dir>.vi.md
   ```
   If previously queued, use `"Packaged (queued behind <epic>)"` in Open Notes. Commit `[<EPIC_NAME>] Package epic for handoff` (`auto_commit: true`).
4. Run `/save-context` (`--state --epic <epic_slug> --status "Stage 2: Packaged & Ready"`), print `handoff.md` path and **`python3 scripts/resume_context.py --emit-prompt implement --epic <epic_slug>`**.
5. When **Triển khai (tự động)** / AUTO MODE was selected at Gate 2, automatically invoke `d3nexus:dev-implementation` without pausing. If **Dừng lại** (Handoff Mode) was chosen, stop cleanly.

### Stage 3 — Isolated Execution → `dev-implementation`

**Entry:** Gate 2 passed, `/principal-review` converged and packaged (`handoff.md`), and **Triển khai (tự động)** chosen (or resuming packaged/interrupted epic).
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
   - In intermediate fix rounds (`AUTO_FIX_ELIGIBLE`), AI Programmer applies verified fixes, commits them, records decisions, and validates via **scoped tests only** (fast static/architecture checks and explicitly targeted unit tests covering modified modules; repo-wide pytest and Playwright E2E suites forbidden) without intermediate confirmation.
   - Only upon final convergence (`AUTO_PASS_CLEAN`, `AUTO_PASS_FINAL_MINOR_SWEEP`, or `AUTO_PASS_FINAL_SWEEP` with 0 Critical findings), **automatically re-run Gate 4 in full** (full regression suite, Playwright E2E browser harness, and `@quality_check` artifact regeneration).
   - Halts cleanly ONLY on Circuit Breakers (`SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, or remaining Critical findings after Round 3).
4. **Transition to Stage 4 (Finish Decision)**: Once the review converges and full Gate 4 passes on the candidate SHA, render the synthesized Executive Report (Top 3 Highest-Risk Findings across rounds) and present the **Stage 4 Finish Decision & Gate 5 Sign-off** to the Human Architect.

> [!CRITICAL]
> **Streamlined Pipeline & Remediation Test Protocol**:
> 1. **Zero-Pause Review**: Once tasks are `done`, Gate 4 runs automatically. On PASS, transition directly to Cross-Model Review without asking between Finish and Review. Finish belongs in Stage 4 (Gate 5 sign-off).
> 2. **Scoped Tests in Intermediate Rounds**: While fixing intermediate findings (Round 1, Round 2...), run ONLY fast static checks and explicitly targeted test files covering modified modules (`uv run pytest <test_file.py>`). Repo-wide pytest, `tests/e2e/`, and piping to `| tail` are strictly forbidden.
> 3. **Final Gate Only**: Reserve full regression, Playwright E2E harness, and `@quality_check` artifact regeneration strictly for the Final Convergence Gate.
> 4. **Zero-Tolerance Anti-Evasion**: Never delete packages from `pyproject.toml` or delete stale quality reports (add `uv.lock` to Allowed files and run `uv lock`). Never synthesize fake test fixtures; load immutable fixtures from disk. Run `uv run playwright install chromium` if playwright was added/updated.

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
- Creating a worktree before resolving the dependency DAG (recreating an existing epic branch worktree in Resume Procedure is allowed).
- Running `package_epic.py` before `/principal-review` completes, or invoking `dev-implementation` without presenting the post-package Handoff Choice (**Triển khai (tự động)** vs **Dừng lại**).
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
- Acting on review findings before presenting the triage from `run_external_review.py triage` (every finding must first be verified against live source and approved Spec/HLD).
- Acting on a Principal Review finding before verifying against source/Spec and running triage (once verified as `Valid` with zero halt triggers, auto-fix and advance without pausing).
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
