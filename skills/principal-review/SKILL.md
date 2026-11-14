---
name: principal-review
description: Performs Shift-Left architectural and task design document reviews (HLD, BDD, Tasks, RFC) against source code before implementation begins.
---

# Principal Review

## Overview

Principal Review provides rigorous, cross-model architectural inspection of High-Level Designs (HLDs), BDD scenarios, Kanban task breakdowns, and standalone RFC documents against the active source codebase.

Operating on the principle of **Shift-Left Quality Assurance**, it catches misunderstandings, missing contracts, scope regressions, and symbol drift before implementation starts, when resolving them in documents is an order of magnitude faster and cheaper than debugging in code.

**Announce at start:** "I'm using the principal-review skill to conduct an architectural review."

## Two Modes of Operation

### 1. In-Lifecycle Mode (Post-Gate 2 Auto-Review -> Package/Handoff)

Automatically invoked at the end of Stage 2 (`dev-lifecycle` / `dev-designer`) after all epic artefacts pass Gate 2 and mechanical readiness checks and the developer specifies the provider/model priority order. Packaging (`package_epic.py` / `handoff.md`) runs **at the end** of Principal Review once convergence is reached.

- **Trigger**: Automatic immediately after developer confirms the `/principal-review` provider/model priority order at the end of Stage 2 (or standalone `/principal-review` on an epic).
- **Scope**: Evaluates all epic artefacts in `.devtool/epic/<epic_dir>/`:
  - Architecture spec (`*-design.en.md`, `*-design.vi.md`)
  - Canonical HLD (`<epic_dir>.en.md`, `<epic_dir>.vi.md`)
  - BDD scenarios (`bdd_scenarios.en.md`, `bdd_scenarios.vi.md`)
  - All Kanban tasks (`task_*.md`)
  - Packaging record (`handoff.md`, when already present)
- **Execution**:
  ```bash
  python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
    --kind principal --epic-dir <epic_dir> --base <base_branch> [--auto-quota [--provider-priority <order>] | --cli <claude|codex|kiro|agy>]
  ```
- **Persistence**: Results recorded in `.devtool/epic/<epic_dir>/principal_review.md`.

### 2. Ad-Hoc Mode (Standalone Documents)

Invoked on-demand to review standalone design documents, architecture proposals, or RFCs without requiring an epic directory.

- **Trigger**: Developer invokes `/principal-review <path>` (e.g. `/principal-review docs/rfc/payment-service.md`).
- **Scope**: Target markdown document and the active git repository context at `HEAD`.
- **Pre-validation**:
  1. The target file path must exist on disk.
  2. The document must contain structural headings (e.g. `# Title`, `## Overview`).
- **Execution**:
  ```bash
  python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
    --kind principal --doc <path> --base <base_branch> [--auto-quota | --cli <claude|codex|kiro|agy>]
  ```
- **Streaming & Visibility**:
  - The review output and triage table stream directly to stdout.
  - Ephemeral review logs are saved under `build/` (git-ignored) for inspection.
  - No epic directory is created or required.

## The Review & Triage Loop

1. **Pre-Check**:
   - For epics, `check_epic_readiness.py` runs first (enforcing R1–R8, BDD Scenario Count Parity `Count(bdd_scenarios.en.md) == Count(task_acceptance.md)`, and `check_task_contract.py --design`). If any check fails, or if `max_rounds` (default: `3`) has already been reached without `--force`, review halts immediately with `[PRECONDITION BLOCKED]` without calling external model CLIs (0 credits used).
   - For standalone docs, structural validation checks that the file exists and has valid headings.

2. **Provider Selection (`check-quota` Priority), 3-Round Convergence Funnel & Shared Context**:
   - **Quota-Aware Provider Priority (`Claude -> Codex -> Kiro -> Argon`)**: Configured in `.devtool/review_config.json` (`provider_priority: ["claude", "codex", "kiro", "agy"]`, `max_rounds: 3`). With `--auto-quota`, `run_external_review.py` selects the highest-priority ACTIVE provider meeting thresholds: Claude/Codex (`5H >= 15%` AND `7D > 2%`), Kiro (`Monthly Credits >= 3%` AND `>= 15.0 credits`), or Argon (`Argon Weekly >= 10%` or `5H >= 15%`).
   - **3-Round Scope-Narrowing Convergence Funnel (Max 3 Rounds)**:
     - **Round 1 (`Scope: full`)**: Full audit of all epic artefacts against active code (enforcing the **Exhaustive Per-File Pass** anti-drip-feed rule).
     - **Round 2 (`Scope: delta`)**: Verifies `fixed in <sha>` items and inspects only `prev_sha..curr_sha` diff hunks; prohibits new `Minor` findings on untouched files.
     - **Round 3 (`Scope: convergence`)**: Strict Blocker-Only Convergence Mode (incomplete fixes or new `Critical`/`Important` regressions in `prev_sha..curr_sha`).
   - **Shared Context & 4 Anti-Fix-Loop Prompt Strategies**: `.devtool/epic/<epic_dir>/principal_review.md` acts as the persistent Shared Context SSOT across rounds (`Earlier Rounds Shared Context Ledger`). `delta_round_context()` injects the **Universal Anti-Ping-Pong Guardrail** (both single-model and mixed-model), the **Previously Fixed Locations Registry (`Verify-Then-Close`)**, and **Diff-Hunk Isolation** on fixed files. See [document-triage.md](references/document-triage.md) for the complete 4-strategy specification.

3. **Role Matrix (Orchestrator + Role 2.2 Reviser Subagent) & Auto-Triage Gate** — see [orchestration-roles.md](../dev-lifecycle/references/orchestration-roles.md):
   - **Orchestrator (Role 2.2, main session)**: runs `run_external_review.py run --kind principal` & `triage` and inspects the triage table; it does not read `src/`/`tests/` or edit task files in the main session.
   - **Reviser Subagent (Role 2.2)**: Document revisions are Role 2.2 work (CRITICAL_RULES §8), so whenever findings exist (`AUTO_FIX_ELIGIBLE`, `AUTO_PASS_FINAL_MINOR_SWEEP`, or `AUTO_PASS_FINAL_SWEEP`) the Orchestrator dispatches a `principal-reviser` on its own model (`invoke_subagent` `TypeName="self"`, `Model="inherit"`, or Claude Code `Task`). The reviser is read-only on `src/`/`tests/` and edits only `.devtool/epic/<epic_dir>/` docs and task prose:
     1. Verify every finding against actual source code and the approved Spec/HLD per [document-triage.md](references/document-triage.md).
     2. **Escalate instead of editing** when any finding is `Debatable`, `Not shown`, a `CRITICAL_CONFLICT`, or touches `shared-contracts/`: return `status: ESCALATE` with the reasons.
     3. **Otherwise revise**: edit the epic docs per each finding's `PROPOSED ACTION`, commit `[<EPIC_NAME>] Revise epic after Principal Review round <n>`, record `fixed in <sha>` in `principal_review.md`, commit `[<EPIC_NAME>] Record Principal Review decisions for round <n>`, and return the `principal-reviser` JSON summary.
   - **Independent check (Orchestrator)**: run `check_epic_readiness.py <epic_dir>` itself (must exit 0) and `git diff --name-only <pre_sha>..HEAD` (any path outside `.devtool/epic/<epic_dir>/` or the epic's task files halts with `CRITICAL_CONFLICT`).
   - **Halt Triggers (`CIRCUIT_BREAKER_HALT` / Escalation)**: Stop immediately and record `python3 scripts/resume_context.py --pending-decision "Resolve Principal Review blocker (<reason>)" --decision-kind blocker --epic <epic_slug>` ONLY on reviser `ESCALATE`, `CRITICAL_CONFLICT`, `Debatable` trade-offs, `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, or `MAX_ROUNDS_CRITICAL_REMAINING`:
     ```markdown
     Principal Review Triage: Round <N> (<CLI>)
     *(or `Principal Review Triage: <doc_path> (<CLI>)`)*

     • Candidate SHA: <commit_sha>
     • Reviewer: <CLI> ( <model> )
     • Thinking Level: <Light | Low | Medium | High | Extra High | None>
     • Verdict: <VERDICT> (<count> <Severity> findings)
     ```

4. **Round Progression, Convergence & Post-Review Packaging (`package_epic.py` + `/save-context`)**:
   - **Intermediate Rounds (`Round n -> n+1`)**: Once the reviser returns `REVISED` and the Orchestrator's own `check_epic_readiness.py` run exits 0, the Orchestrator immediately triggers Round `n+1` (never running `package_epic.py` mid-loop). Sub-step heartbeats (`--phase fixing` / `--phase verifying`) are emitted during execution.
   - **Upon Convergence (`AUTO_PASS_CLEAN`, `AUTO_PASS_FINAL_MINOR_SWEEP`, or `AUTO_PASS_FINAL_SWEEP`)**:
     - Run `python3 skills/dev-implementation/resources/scripts/package_epic.py <epic_dir>` (`--revise --reason "Revise after Principal Review round <n>"` if `handoff.md` exists) and commit `[<EPIC_NAME>] Package epic for handoff`.
     - Record Gate 2 (`python3 scripts/resume_context.py --gate 2 --epic <epic_slug> --approved "Passed Principal Review round <n> and packaged"`), save state (`--state --epic <epic_slug> --status "Stage 2: Packaged & Ready"`), and print `python3 scripts/resume_context.py --emit-prompt implement --epic <epic_slug>` + `handoff.md` path.
     - In autonomous mode (`lifecycle_runner.py`), transition directly to `d3nexus:dev-implementation` (`gemini-4-hydrogen-xhigh --effort xhigh`). In interactive mode, record `--pending-decision "Choose Triển khai (tự động) vs Dừng lại" --decision-kind choice_a`, stop calling tools, and ask **Triển khai (tự động)** vs **Dừng lại**.

## Guidelines & Reference Documents

Read these on demand, not up front. `run_external_review.py` loads the prompt template and review rules itself, so do not open them to run a review.

- [Prompt Template](references/principal-review-prompt.md): The read-only instruction template sent to reviewer CLIs (script-consumed; do not read).
- [Review Rules](references/principal-review-rules.md): Severity definitions (Critical, Important, Minor) and source grounding standards (script-consumed; do not read).
- [Document Triage Protocol](references/document-triage.md): Step-by-step decision verification and revision loop enforcement (read at step 3 only).
- [Verification Row Grammar](../dev-designer/references/verification-row-grammar.md) (read only when a finding concerns Verification rows): Canonical Verification table grammar rules (including `\|` pipe escaping, `env VAR=val` prefixing, slash-containing search pattern rules, and portable CLI usage). Escaped pipes `\|` in table command cells are unescaped by `task_contract.py` and must not be flagged as syntax errors.
