---
name: dev-lifecycle
description: Use this skill to orchestrate epic-scale work from idea to merged branch. It owns the sequence and the five approval gates connecting dev-brainstorming, dev-designer, dev-implementation, and quality_check — which skill runs next, what each stage must hand over, and what to do when a gate fails. Activate it when a request spans multiple components or needs an HLD plus a Kanban task breakdown, when routing an approved spec, or whenever it is unclear which epic stage the work is currently in.
---

# Development Lifecycle

The orchestrator for epic-scale work. It owns **sequence and gates only** — each stage's *how* stays in that stage's own skill.

**Announce at start:** "I'm using the dev-lifecycle skill to orchestrate the `<epic_slug>` epic."

**Every stage is entered by invoking its skill.** Doing a stage's work yourself skips its gate.

## When NOT to use this

- Single-component feature, bugfix, or one implementation plan → `dev-brainstorming` then `writing-plans` (no epic).
- Already mid-stage → invoke that stage's skill directly.

## The Sequence

Lifecycle diagrams: [lifecycles.en.md](../../docs/lifecycles.en.md). Runtime sequence:

1. **Stage 1 (Inception & Spec)**: `dev-brainstorming` -> Gate 1 approval -> Route to `dev-designer` (epic) or `writing-plans` (non-epic).
2. **Stage 2 (Architecture & Tasks)**: `dev-designer` (Role 2.1) -> Gate 2 Unified Confirmation (`--checkpoint gate2_tasks_locked`, provider priority + **Triển khai (tự động)** vs **Dừng lại**) -> `/principal-review` (max 3 rounds, zero-pause on `Valid`) -> `package_epic.py` & implement prompt -> auto-enter Stage 3 if **Triển khai (tự động)** (else stop).
3. **Stage 3 (Automated Execution & Audit)**: Role 2.2 Orchestrator coordinates only -> `dev-implementation` -> Automated Gate 3 (wave order & 2-slot pool) -> dispatches Role 2.3 Programmer subagents (`dev_config.py dispatch`; default `gemini-4-hydrogen-xhigh`) for `task-implementer`, `review-fixer` and fresh `gate4-verifier`, plus Role 2.1 `task-reviewer` and `fix-planner` (`/cross-model-review`, max 3 rounds) -> full Gate 4 convergence.
4. **Stage 4 (Finish Decision, Integration & Archival)**: Prompt Human Architect for Finish Decision & Gate 5 Sign-off -> `finishing-a-development-branch` -> Archive tasks into `.devtool/epic/<slug>/`, rebase, verify by tier (`Test All` once), `--no-ff` or squash merge, explicit Git push confirmation.

<HARD-GATE>
- **Orchestrator boundary (Role 2.2, Stage 3)**: never read/edit `src/` or `tests/`, never edit task Verification tables / DoD / `Allowed files`, never run tests, linters, type checkers, `run_task_checks.py` or `verify-tier` in the main session. Delegate TDD tasks, fixes and Gate 4 to Role 2.3 subagents and reviews/fix plans to Role 2.1 subagents on their `dev_config.py resolve` bindings (never `Model="flash"`), verifying claims independently. Matrix: [orchestration-roles.md](references/orchestration-roles.md).
- No automatic model fallback or retry (checkpoint `model_unavailable`, stop). Run `dev_config.py quota-check` before Stage 3, each wave and fix round; exit `2` stops.
- Never create `implementation_plan.md`; specs live in `docs/superpowers/specs/` or `.devtool/epic/<epic_dir>/`.
- Package (`package_epic.py`) only after `/principal-review` converges. Under Gate 2 **Triển khai (tự động)**, never re-prompt during `/principal-review` (`Valid` findings) or after packaging — run `d3nexus:dev-implementation`, Gate 3, worktree bootstrap, and Gate 4 -> Cross-model review automatically; Finish stays at Stage 4 (Gate 5).
</HARD-GATE>

## Document Contract

Every dev artefact is English-only and a single file. Specs, HLDs, BDD scenarios and non-epic plans carry a linked ToC covering every `##` section: `YYYY-MM-DD-<topic>-design.md`, `<epic_dir>.md`, `bdd_scenarios.md`, `docs/superpowers/plans/YYYY-MM-DD-<feature>.md`; legacy `.en.md` files are accepted, not produced. `task_*.md` and `handoff.md` stay English-only (`handoff.md` still requires a ToC). Vietnamese mirrors are not SSOT: never open or create one unless Role 1.0 asks ([rule 11](../../rules/CRITICAL_RULES.md#11-english-ssot-and-vietnamese-mirror-isolation)).

Authoring standards (Markdown quality, `Depends on epic` declaration) — read when authoring or reviewing an HLD or a human-facing document: [governance-checklists.md](references/governance-checklists.md#8-authoring-standards-from-the-dev-lifecycle-skill).

## The Five Gates

Every gate except Gate 4 (machine verdict) requires **human approval**. Never cross one on your own judgement. Record and query approvals in `.devtool/GATE_LEDGER.md` via `resume_context.py --gate <1..5>` and `--check-gate <1..5>`.

| Gate | Name | Approver | Enforced in | Handoff artefact |
|------|------|----------|-------------|------------------|
| **1** | Spec Approved | User | `dev-brainstorming` | `YYYY-MM-DD-<topic>-design.md` |
| **2** | HLD & Task Breakdown | User | `dev-designer` | `<epic_dir>.md` + `bdd_scenarios.md` + `task_*.md` |
| **3** | Execution Order | Automated (Role 2.2 Orchestrator) | `dev-implementation` Phase 1 / Resume | auto-resolved order + bootstrapped worktree |
| **4** | Quality LGTM & Check 2 | `audit_epic.py` + `check_bdd_traceability.py` + `quality_check` | `dev-implementation` Phase 4 | `audit_epic.py` + 🟢 report + coverage + BDD traceability + merge-ready branch |
| **5** | Developer Kanban Sign-Off & Finish | User | `dev-implementation` Phase 4.1 / Stage 4 | User confirmation for branch finishing and archival |

## Stages

### Resuming an Epic

An epic whose `.devtool/epic/<epic_dir>/` holds `task_*.md` files is past Gate 2 — whether `Packaged` (`handoff.md` present) or interrupted in Stage 3. Announce "Gates 1 and 2 already passed; resuming at Stage 3", invoke `dev-implementation`, and let its Entry-Point Detection choose where to start. Never redo Stage 1 or 2; route new requirements to dev-designer's Updating an Existing Epic.

### Autonomous Mode (`/dev-lifecycle --autonomous`)

For hands-off execution, `lifecycle_runner.py` drives Stage 2 and Stage 3:
- **Four personas**: 1.0 Human Architect, 2.1 AI Architect & Reviewer (`fix-planner`), 2.2 Orchestrator (the runner), 2.3 Programmer (default `gemini-4-hydrogen-xhigh`); bindings from `/d3nexus:dev-config`.
- **Execution Hygiene & Checklists**: Enforce Rule 3 bounded reads (`StartLine`/`EndLine` on files > 200 lines) and Rule 5 Zero-Fluff Output Cap (preserve Verdicts, Findings, and gate results). Extended checklists: [governance-checklists.md](references/governance-checklists.md).
- **Automation**: Auto Gate 3 order, process timeouts, auto-triage, risk routing to `fix-planner` (`PLANNED`/`ESCALATE`), turn-budget checkpoints, quota gate.
- **Safety**: Circuit breakers on contract conflicts, fix loops, and max rounds; final Top 3 report halts at `AWAITING_FINISH`.
- See [references/autonomous-mode.md](references/autonomous-mode.md).

### Stage 1 — Inception & Spec → `dev-brainstorming`

**Invoke `d3nexus:dev-brainstorming`.** Gate 1 is its user-approval step.
- **Entry:** raw idea/requirement. **Exit (Gate 1):** approved spec passing self-review.
- **Routing:** **Epic-scale code** → move spec to `.devtool/epic/<epic_dir>/`, update links, enter `dev-designer` (Stage 2). **Everything else** → `writing-plans`. Route decomposed sub-project specs independently; never merge multiple specs into one epic.

### Stage 2 — Architecture & Tasks → `dev-designer`

**Invoke `d3nexus:dev-designer`.**
- **Entry:** Gate 1 spec in `.devtool/epic/<epic_dir>/`. **Exit (Gate 2):** user-confirmed task list and granularity.
- **3-Tier Document Separation:**
  - `<epic_dir>.md` (HLD): System overview & Feature Maintenance Map (1 Architecture diagram, optional Sequence diagram, canonical entry points — no duplicate Gherkin).
  - `bdd_scenarios.md`: Adversarial edge-case, boundary, exception, and rollback suite across 5 dimensions.
  - `task_*.md`: Self-contained LLM Execution SSOT loaded one task at a time in Stage 3.

### Handoff Choice

Follow [references/principal-review.md](references/principal-review.md) across Stage 2 -> Principal Review -> Packaging -> Stage 3:

- **Gate 2 Unified Confirmation (Tasks & AUTO MODE):** After Gate 2 and `check_epic_readiness.py <epic_dir>` pass, save Gate 2 & state (`--status "Stage 2: Ready for Principal Review"`, `--checkpoint gate2_tasks_locked`), read `/d3nexus:dev-config review` (`.devtool/review_config.json` fallback; caps via `/d3nexus:dev-config limits`), stop calling tools, and present the **provider/model priority** order:
  1. **(Recommended) Phê duyệt & Chạy AUTO MODE xuyên suốt (Triển khai (tự động)):** Run `/principal-review` -> `handoff.md` -> `/dev-implementation` (2-slot pool) -> `/cross-model-review` without pausing; Stage 3 uses this session's model (state `orchestrator` binding). Halts ONLY on Circuit Breakers, `ESCALATE`, model/quota stops, or Gate 5.
  2. **Phê duyệt & Handoff Mode (Dừng lại):** Run `/principal-review` -> `handoff.md` -> stop cleanly (new session on the `orchestrator` model).
- **Automatic `/principal-review` (Zero-Pause):** Run `d3nexus:principal-review` (`--auto-quota`/`--provider-priority`/`--cli`, default 3 rounds; mid-loop runs `check_epic_readiness.py`, never `package_epic.py`). Auto-fix `Valid` findings without pausing; halt only on the five triggers.
- **End-of-Review Packaging:** On convergence, run `python3 skills/dev-implementation/resources/scripts/package_epic.py <epic_dir> [--revise --reason "<reason>"]` (omit `--revise` when `handoff.md` is absent):
1. **Preflight:** `python3 "$SCRIPTS"/check_epic_readiness.py <epic_dir>` (runs `check_task_contract.py --design`). First line prints task count.
2. Copy `references/handoff-template.md` to `.devtool/epic/<epic_dir>/handoff.md` (`<N>` is the task count the preflight printed) and lint via `python3 "$CHECK_DOC" --require-toc .devtool/epic/<epic_dir>/handoff.md`.
3. Mark packaged and verify English overview (`<epic_dir>.en.md` for legacy epics):
   ```bash
   python3 "$SCRIPTS"/sync_task_status.py epic <epic_dir> Packaged
   grep -n -E '^- \*\*Status\*\*: Packaged' \
     .devtool/epic/<epic_dir>/<epic_dir>.md
   ```
   If previously queued, use `"Packaged (queued behind <epic>)"` in Open Notes. Commit `[<EPIC_NAME>] Package epic for handoff` (`auto_commit: true`).
4. Run `/save-context` (`--state --epic <epic_slug> --status "Stage 2: Packaged & Ready"`), print `handoff.md` path and **`python3 scripts/resume_context.py --emit-prompt implement --epic <epic_slug>`**.
5. If Gate 2 chose **Triển khai (tự động)**, invoke `d3nexus:dev-implementation` without pausing; if **Dừng lại**, stop.

### Stage 3 — Isolated Execution → `dev-implementation`

**Entry:** Gate 2 passed, `/principal-review` converged and packaged (`handoff.md`), and **Triển khai (tự động)** chosen (or resuming packaged/interrupted epic).
**Exit (Gate 5):** Gate 4 is 🟢 LGTM and user approves Kanban completion.

- **Prerequisites & Concurrency**: If `Depends on epic:` is declared, run `sync_task_status.py check-prereqs <epic_dir>`. If queued behind another epic, run `sync_task_status.py check-conflicts <epic_dir>` and `sync_task_status.py promote <epic_dir> [--force]`.
- **Gate 3 (Automated)**: Orchestrator runs `compute_execution_order.py --parallel`, bootstraps worktree + 2-slot pool, and records `--gate 3` (halting ONLY on cyclic DAG or unresolvable prerequisites).
- **Wave Execution (Orchestrator + Subagents)**: Orchestrator owns `manage_worker_pool.py` (`sync working`, `sync review`, `triage-fix`, `finalize-slot`, `merge`, `cleanup`).
  - **Programmer (Role 2.3 `task-implementer`, every task)**: Runs `check_code_impact.py` and full mechanical `Verification` (`RED -> GREEN -> REGRESSION -> TIER-B -> TIER-C` via `run_task_checks.py`), covering module + *Downstream Callers* `REGRESSION` and `TIER-B` across all `Allowed files` (plus `lint-imports`/contract checks), then ticks all `## Definition of Done` `- [x]` checkboxes with brief mechanical notes (e.g. `exit 0, 42 passed`). Setting `status: "done"` or `completedAt` with any `- [ ]` is forbidden.
  - **LLM Review (Role 2.1 `task-reviewer` & `/cross-model-review`, selective)**: Skipped on routine mechanical tasks (`task-implementer` finalizes directly); runs only at semantic/architectural boundaries or high-risk tasks (`review_tier: "full"`, `security`/`architecture`/`concurrency`/`contract` labels, or `> 2` non-test modules via `git diff --name-only`; 2-pass review cap, 1 fix pass, Two-Tier Risk Assessment) and Gate 4 synthesis. After `cleanup`, fresh `gate4-verifier` runs Gate 4.

**Automated Review Pipeline (Gate 4 Local PASS → Automatic Cross-Model Review)**:
When Gate 4 returns `PASS` (🟢 LGTM):
1. **Zero-Pause Transition**: Record `--gate 4` and run `run_external_review.py run --epic-dir <epic_dir> --base <base_ref> --auto-quota` & `triage`.
2. **Fixer Loop (Max 3 Rounds)**: Route by risk: `fast-track` `review-fixer` (all `Valid`, no escalation marker) or Role 2.1 `fix-planner` returning `plan_markdown` (Orchestrator writes `fix_plan_round<N>.md`; `PLANNED` -> `apply-plan`; `ESCALATE` -> stop for Role 1.0). Role 2.3 fixer applies fixes, runs **Tier 1 scoped tests only**, commits `[<EPIC_NAME>] Fix ...`, records `fixed in <sha>` in `review_results.md`; Orchestrator scope-checks `git diff --name-only`. On convergence a fresh `gate4-verifier` runs full Gate 4. Halt on `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, or Critical findings after Round 3.
3. **Transition to Stage 4**: On convergence + Gate 4 PASS, render Top 3 Highest-Risk Findings and prompt Human Architect for **Stage 4 Finish Decision & Gate 5 Sign-off**.

- **Zero-Pause, Test Efficiency & Anti-Test-Bloat**: Finish belongs in Stage 4 / Gate 5. Require `@pytest.mark.parametrize` (no copy-pasted per-input tests), ban boilerplate language/Pydantic-default/getter tests, enforce `scope="module"`/`scope="session"` read-only/server/browser fixtures, and follow Tier 1 (`uv run pytest <changed_test_files> -n auto --timeout=30 -q --tb=short`), Tier 2 (`--ignore=tests/e2e -n auto --dist loadscope --timeout=30 -q --tb=short`), and Tier 3 (Tier 2 + session `tests/e2e` + `quality_check` once per epic). Never delete deps/reports or fake fixtures. See [governance-checklists.md](references/governance-checklists.md).

**Gate 4 Machine Acceptance Criteria:**
Gate 4 grants `🟢 LGTM` only when:
1. `audit_epic.py` exits 0 (committed evidence matches Verification tables, DoD checkboxes ticked, graders disclosed).
2. Enforce result-based traceability: `check_bdd_traceability.py tests --results` exits 0.
3. `@quality_check` returns aggregated verdict of **PASS** with `profile: "epic"` against `<base_ref>` bound to candidate `repository_sha`.

Gate 4 conditions:
1. **Contract**: profile `epic`, `base_ref`, candidate `repository_sha`.
2. **Aggregation**: `FAIL > BLOCKED > PASS`.
3. **No Partial Approvals**: `BLOCKED` cannot approve.
4. **Candidate Immutability**: A 🟢 verdict belongs strictly to the tested SHA. If commits change after Gate 4, a fresh traceability check and epic quality run are required before landing.

On failure, route back to `dev-implementation` with defect report; land fixes as `[EPIC_NAME] Fix <what>` commits and re-run Gate 4 in full.

**Gate 5 Developer Kanban Review & Sign-Off:**
Completed tasks remain in `.devtool/features/done/`. Stop calling tools and present final report for visual inspection. On user approval, advance to Stage 4. Requested adjustments land as Fix commits and return to full Gate 4.

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

- Writing to `implementation_plan.md` or any native planning artifact.
- Skipping `dev-brainstorming` because scope seems clear, or skipping Stage 2 on an approved epic-scale spec.
- Merging sub-project specs into one epic, or redoing design when task files exist (use Updating an Existing Epic).
- Creating a worktree before resolving the dependency DAG (recreating an existing epic worktree in Resume Procedure is allowed).
- Running `package_epic.py` before `/principal-review` completes, packaging without preflight, or re-prompting during `/principal-review` (`Valid` findings) or after packaging when Gate 2 chose **Triển khai (tự động)**.
- Merging to `develop` without Gate 4 🟢 or manually instead of `integrate_branch.py land`; pushing without explicit permission.
- Granting Gate 4 without a passing traceability check on the same SHA, or without a passing `audit_epic.py`; reusing a Gate 4 PASS after review rounds, finding decisions, or Fix commits change SHA.
- Marking `status: "done"` (or `completedAt`) with any `- [ ]` in `## Definition of Done`, omitting `REGRESSION` or full `Allowed files` `TIER-B` coverage, or ticking checkboxes/evidence by hand without `run_task_checks.py`.
- Changing Verification tables, Allowed files, or protected paths without stopping to ask.
- Prompting developer for intermediate Review Choice or Gate 3 confirmation pauses, or advancing to Stage 4 (Finish) without Cross-Model Review convergence and Gate 5 sign-off.
- Launching `agy`, `ag_run` or `<profile>-cli` from an agent shell instead of `dev_config.py dispatch`.
- Prohibited: picking the review CLI for the developer instead of prompting for Claude CLI, Codex CLI, or Antigravity CLI, or picking the Ollama model instead of running `ollama list` and asking.
- Acting on review findings before presenting the triage from `run_external_review.py triage` (verify against source & Spec/HLD; visibility log only, never a pause on `Valid` `/principal-review` findings).
- Acting on a Principal Review finding before verifying against source/Spec and running triage (once verified as `Valid` with zero halt triggers, auto-fix and advance without pausing).
- Writing `dismissed` decisions in `review_results.md` without explicit developer words.
- Starting a task while integration with `develop` is failing.
- Invoking `finishing-a-development-branch` or archiving `.devtool/features/done/` tasks before Gate 5 sign-off, or leaving completed tasks/draft specs unarchived after integration.
- Opening or creating a `*.vi.md` mirror (not SSOT), or translating `task_*.md`.

## Stage Skills

| Stage | Skill | Gate it enforces |
|-------|-------|------------------|
| 1 | `dev-brainstorming` | 1 |
| 2 | `dev-designer` | 2 |
| 3 | `dev-implementation` | 3, triggers 4, and enforces 5 |
| 3 (verification) | `quality_check` + `check_bdd_traceability.py` | 4 |
| 4 | `finishing-a-development-branch` | — |
