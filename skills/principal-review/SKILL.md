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

### 1. In-Lifecycle Mode (Stage 2 Handoff Choice)

Invoked during the packaging phase of `dev-lifecycle` after all epic artefacts pass Gate 2 and mechanical readiness checks.

- **Trigger**: Developer selects option 2 ("Principal Review") at the Handoff Choice prompt.
- **Scope**: Evaluates all epic artefacts in `.devtool/epic/<epic_dir>/`:
  - Architecture spec (`*-design.en.md`, `*-design.vi.md`)
  - Canonical HLD (`<epic_dir>.en.md`, `<epic_dir>.vi.md`)
  - BDD scenarios (`bdd_scenarios.en.md`, `bdd_scenarios.vi.md`)
  - All Kanban tasks (`task_*.md`)
  - Packaging record (`handoff.md`)
- **Execution**:
  ```bash
  python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
    --kind principal --epic-dir <epic_dir> --base <base_branch> [--auto-quota | --cli <claude|codex|kiro|agy>]
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

3. **Triage Findings, Top 3 Highest-Risk Report & Auto-Triage Gate**:
   - Read and follow [document-triage.md](references/document-triage.md) (Source-of-Truth Hierarchy: Forward Alignment over Legacy Reversion, Top 3 Highest-Risk Findings Report, and Auto-Triage Gate).
   - Inspect `## Auto-Triage Gate` from `run_external_review.py triage --kind principal --epic-dir <epic_dir>`:
     - **`AUTO_PASS_CLEAN` / `AUTO_PASS_FINAL_MINOR_SWEEP` / `AUTO_PASS_FINAL_SWEEP` (Round 3 with `0 Critical`)**: Apply one final revision pass for any valid non-critical items, run `package_epic.py <epic_dir> --revise` green, and advance to Stage 3 without calling another review round.
     - **`AUTO_FIX_ELIGIBLE` (Round 1..2 with `Critical`/`Important`, no `shared-contracts/` conflict, no Fix Loop)**: Verify against codebase and approved HLD; in autonomous mode, apply revisions, record `fixed in <sha>`, run `package_epic.py --revise`, and run Round $N+1$. In interactive mode, present the triage header block and wait for developer confirmation:
       ```markdown
       Principal Review Triage: Round <N> (<CLI>)
       *(or `Principal Review Triage: <doc_path> (<CLI>)`)*

       • Candidate SHA: <commit_sha>
       • Reviewer: <CLI> ( <model> )
       • Thinking Level: <Light | Low | Medium | High | Extra High | None>
       • Verdict: <VERDICT> (<count> <Severity> findings)
       ```
     - **`CIRCUIT_BREAKER_HALT` (`SHARED_CONTRACT_CONFLICT` in any round, `FIX_LOOP`, or `MAX_ROUNDS_CRITICAL_REMAINING` when `>= 1 Critical` survives Round 3)**: **STOP IMMEDIATELY**, never auto-fix or revert the user-approved HLD design, and report `## Top 3 Highest-Risk Findings (Executive Report)` to the Human Architect.

4. **Revision Loop & Commit Ordering (Automatic Re-Package & `/save-context`)**:
   - When applying revisions (either via `AUTO_FIX_ELIGIBLE` / `AUTO_PASS_FINAL_MINOR_SWEEP` or after developer confirmation), apply document edits and automatically execute the re-packaging and context-saving steps without asking for an intermediate confirmation:
   - Apply document edits first and commit:
     `git commit -m "[<EPIC_NAME>] Revise epic after Principal Review round <n>"`
   - Record decisions with revision commit SHA in `principal_review.md`, then commit:
     `git commit -m "[<EPIC_NAME>] Record Principal Review decisions for round <n>"`
   - Automatically re-anchor `handoff.md` via `python3 skills/dev-implementation/resources/scripts/package_epic.py <epic_dir> --revise --reason "Revise after Principal Review round <n>"` (and commit `[<EPIC_NAME>] Package epic for handoff` if `auto_commit: true`).
   - Automatically record Gate 2 approval in the Gate Approval Ledger via `python3 scripts/resume_context.py --gate 2 --epic <epic_slug> --approved "Revised after Principal Review round <n>"`.
   - Automatically record state via `python3 scripts/resume_context.py --state --epic <epic_slug> --status "Stage 2: Revised after Principal Review"`, and emit the AI Programmer prompt via `python3 scripts/resume_context.py --emit-prompt implement --epic <epic_slug>`. In autonomous lifecycle mode, once Principal Review converges (`AUTO_PASS_CLEAN` or `AUTO_PASS_FINAL_MINOR_SWEEP`), transition to Role 2.3 (AI Programmer, Model Gemini Flash 3.8) and invoke `d3nexus:dev-implementation`; in interactive mode, present the Principal Review Choice (`/principal-review` vs `/dev-implementation`) again.

## Guidelines & Reference Documents

Read these on demand, not up front. `run_external_review.py` loads the prompt template and review rules itself, so do not open them to run a review.

- [Prompt Template](references/principal-review-prompt.md): The read-only instruction template sent to reviewer CLIs (script-consumed; do not read).
- [Review Rules](references/principal-review-rules.md): Severity definitions (Critical, Important, Minor) and source grounding standards (script-consumed; do not read).
- [Document Triage Protocol](references/document-triage.md): Step-by-step decision verification and revision loop enforcement (read at step 3 only).
- [Verification Row Grammar](../dev-designer/references/verification-row-grammar.md) (read only when a finding concerns Verification rows): Canonical Verification table grammar rules (including `\|` pipe escaping, `env VAR=val` prefixing, slash-containing search pattern rules, and portable CLI usage). Escaped pipes `\|` in table command cells are unescaped by `task_contract.py` and must not be flagged as syntax errors.
