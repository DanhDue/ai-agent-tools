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
    --kind principal --epic-dir <epic_dir> --base <base_branch> --cli <claude|codex|agy>
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
    --kind principal --doc <path> --base <base_branch> --cli <claude|codex|agy>
  ```
- **Streaming & Visibility**:
  - The review output and triage table stream directly to stdout.
  - Ephemeral review logs are saved under `build/` (git-ignored) for inspection.
  - No epic directory is created or required.

## The Review & Triage Loop

1. **Pre-Check**:
   - For epics, `check_epic_readiness.py` runs first. If any check fails (R1–R8), review halts immediately with a precondition banner without calling external model CLIs.
   - For standalone docs, structural validation checks that the file exists and has valid headings.

2. **External Model Review**:
   - Executes with a read-only permissions profile (`claude -p --dangerously-skip-permissions`, `codex exec --sandbox read-only`, or `agy --sandbox --mode plan`).
   - The reviewer inspects active code at candidate SHA to verify groundedness (P1–P8 checklists).

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

4. **Revision Loop & Commit Ordering**:
   - Apply document edits first and commit:
     `git commit -m "[<EPIC_NAME>] Revise epic after Principal Review round <n>"`
   - Record decisions with revision commit SHA in `principal_review.md`, then commit:
     `git commit -m "[<EPIC_NAME>] Record Principal Review decisions for round <n>"`
   - Re-run packaging to refresh handoff metadata, record state via `python3 scripts/resume_context.py --state --epic <epic_slug>`, emit the AI Programmer prompt via `python3 scripts/resume_context.py --emit-prompt implement --epic <epic_slug>`, and present the Principal Review Choice again.

## Guidelines & Reference Documents

- [Prompt Template](references/principal-review-prompt.md): The read-only instruction template sent to reviewer CLIs.
- [Review Rules](references/principal-review-rules.md): Severity definitions (Critical, Important, Minor) and source grounding standards.
- [Document Triage Protocol](references/document-triage.md): Step-by-step decision verification and revision loop enforcement.
