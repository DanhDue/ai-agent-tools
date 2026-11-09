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
    --kind principal --epic-dir <epic_dir> --base <base_branch> --cli <claude|codex|agy|kiro>
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
    --kind principal --doc <path> --base <base_branch> --cli <claude|codex|agy|kiro>
  ```
- **Streaming & Visibility**:
  - The review output and triage table stream directly to stdout.
  - Ephemeral review logs are saved under `build/` (git-ignored) for inspection.
  - No epic directory is created or required.

## The Review & Triage Loop

1. **Pre-Check**:
   - For epics, `check_epic_readiness.py` runs first. If any check fails (R1–R8), review halts immediately with a precondition banner without calling external model CLIs.
   - For standalone docs, structural validation checks that the file exists and has valid headings.

2. **Provider Configuration (`.devtool/review_config.json`) & External Model Review**:
   - **Load Sticky Provider Config**: Read `.devtool/review_config.json` (auto-seeded from `DEFAULT_REVIEW_CONFIG` in `run_external_review.py` when absent) to inspect `last_used_provider` and each provider's default `model` and `thinking_level` (`claude`, `codex`, `agy`, `kiro`, `ollama`). When prompting the developer to choose a reviewer CLI, surface the configured `model` and `thinking_level` for each available CLI and highlight `last_used_provider`. Passing `--cli`, `--model`, or `--thinking-level` to `run_external_review.py run` automatically persists the updated sticky preferences back to `.devtool/review_config.json`.
   - Executes with a read-only permissions profile (`claude -p --dangerously-skip-permissions`, `codex exec --sandbox read-only`, `agy --sandbox --mode plan`, or `kiro-cli chat --no-interactive --trust-all-tools --wrap never`).
   - The reviewer inspects active code at candidate SHA to verify groundedness (P1–P8 checklists).
   - **Delta rounds (Round ≥ 2)**: keep the same reviewer model. The script automatically sends the previous completed round's findings and decisions plus the `git diff` of the epic artefacts since that round, so the reviewer checks the fixes and the revised text instead of re-deriving the whole design. Add `--full` to force a full review of every artefact, and use it for the final confirmation round before Gate 2 sign-off. The script falls back to a full review by itself when no revision exists since the last round or the revision exceeds `--diff-limit` lines. A delta round is recorded as `- **Scope**: delta from round <n> (<sha>)` in `principal_review.md`.

3. **Triage Findings**:
   - Follow [document-triage.md](references/document-triage.md).
   - Verify every finding against the codebase.
   - Present the triage table to the developer and wait for decisions. The presentation MUST begin with the standardized 4-bullet header block:
     ```markdown
     Principal Review Triage: Round <N> (<CLI>)
     *(or `Principal Review Triage: <doc_path> (<CLI>)`)*

     • Candidate SHA: <commit_sha>
     • Reviewer: <CLI> ( <model> )
     • Thinking Level: <Light | Low | Medium | High | Extra High | None>
     • Verdict: <VERDICT> (<count> <Severity> findings)
     ```

4. **Revision Loop & Commit Ordering (Automatic Re-Package & `/save-context`)**:
   - Once the developer confirms the triage decisions, apply document edits and automatically execute the re-packaging and context-saving steps without asking for an intermediate confirmation:
   - Apply document edits first and commit:
     `git commit -m "[<EPIC_NAME>] Revise epic after Principal Review round <n>"`
   - Record decisions with revision commit SHA in `principal_review.md`, then commit:
     `git commit -m "[<EPIC_NAME>] Record Principal Review decisions for round <n>"`
   - Automatically re-anchor `handoff.md` via `python3 skills/dev-implementation/resources/scripts/package_epic.py <epic_dir> --revise --reason "Revise after Principal Review round <n>"` (and commit `[<EPIC_NAME>] Package epic for handoff` if `auto_commit: true`).
   - Automatically record Gate 2 approval in the Gate Approval Ledger via `python3 scripts/resume_context.py --gate 2 --epic <epic_slug> --approved "Revised after Principal Review round <n>"`.
   - Automatically record state via `python3 scripts/resume_context.py --state --epic <epic_slug> --status "Stage 2: Revised after Principal Review"`, emit the AI Programmer prompt via `python3 scripts/resume_context.py --emit-prompt implement --epic <epic_slug>`, and then stop calling tools to present the Principal Review Choice (`/principal-review` vs `/dev-implementation`) again.

## Guidelines & Reference Documents

Read these on demand, not up front. `run_external_review.py` loads the prompt template and review rules itself, so do not open them to run a review.

- [Prompt Template](references/principal-review-prompt.md): The read-only instruction template sent to reviewer CLIs (script-consumed; do not read).
- [Review Rules](references/principal-review-rules.md): Severity definitions (Critical, Important, Minor) and source grounding standards (script-consumed; do not read).
- [Document Triage Protocol](references/document-triage.md): Step-by-step decision verification and revision loop enforcement (read at step 3 only).
- [Verification Row Grammar](../dev-designer/references/verification-row-grammar.md) (read only when a finding concerns Verification rows): Canonical Verification table grammar rules (including `\|` pipe escaping, `env VAR=val` prefixing, slash-containing search pattern rules, and portable CLI usage). Escaped pipes `\|` in table command cells are unescaped by `task_contract.py` and must not be flagged as syntax errors.
