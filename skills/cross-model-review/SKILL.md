---
name: cross-model-review
description: Reviews implemented code, commits, and diffs using external frontier models (Claude CLI, Codex CLI, Antigravity CLI) or local Ollama models with evidence-grounded triage.
---

# Cross-Model Review

## Overview

Cross-Model Review conducts Shift-Right independent code reviews on implemented software commits and diffs using external frontier models (Claude CLI, Codex CLI, Antigravity CLI) or local models (Ollama).

Operating on the principle of **Shift-Right Verification**, it catches code quality issues, missing test coverage, subtle concurrency regressions, architectural drift, and spec deviations before code is merged to main.

**Announce at start:** "I'm using the cross-model-review skill to conduct an independent code review."

## Two Modes of Operation

### 1. In-Lifecycle Mode (Stage 3 Review Choice after Gate 4)

Invoked after all tasks of an epic are implemented and Gate 4 (machine acceptance) returns PASS.

- **Trigger**: Developer selects Option 2 ("Cross-model review") or Option 3 ("Local model review") at the Review Choice prompt.
- **Scope**: Evaluates all task commits, diffs against base branch, audit disclosures, and integration test traceability in `.devtool/epic/<epic_dir>/`.
- **Execution**:
  - External CLI:
    ```bash
    python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
      --epic-dir <epic_dir> --base <base_branch> --cli <claude|codex|agy>
    ```
  - Local Ollama:
    ```bash
    python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
      --epic-dir <epic_dir> --base <base_branch> --cli ollama --model <model>
    ```
- **Persistence**: Results recorded into `.devtool/epic/<epic_dir>/review_results.md`.

### 2. Ad-Hoc Mode (Arbitrary Git Branch or Commits)

Invoked on-demand to review a feature branch, pull request diff, or specific commit range without requiring an epic directory.

- **Trigger**: Developer invokes `/cross-model-review --base <base> [--commits <range>] [--cli <claude|codex|ollama|agy>] [--model <model>]`.
- **Scope**: Evaluates the commit range and diff against `--base` (or `--commits <range>`).
- **Execution**:
  ```bash
  python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
    --base <base_branch> [--commits <range>] --cli <claude|codex|agy> [--model <model>]
  ```
- **Streaming & Visibility**:
  - The review output and formatted triage table stream directly to stdout.
  - Ephemeral review logs are written to `build/` (git-ignored) for live inspection.
  - No epic directory is required, and no `review_results.md` is created.

## Preconditions & Safeguards

1. **Clean Working Tree**:
   - The runner enforces a clean git working tree before invoking any model.
   - If unstaged or untracked changes exist, execution halts immediately with:
     `commit or stash your changes before a review`.

2. **Read-Only Sandbox**:
   - CLI invocations operate under read-only sandboxes (`claude -p --permission-mode plan`, `codex exec --sandbox read-only`, or `agy --sandbox --mode plan`).
   - The runner verifies git status before and after execution; any file modifications made by a reviewer cause the round to be discarded immediately.

3. **Process Supervision & Timeouts**:
   - External CLI invocations run in their own process group.
   - If a model call exceeds `--timeout` (default: 1800s), the process group is cleanly terminated without leaving orphaned processes.

## The Triage & Fix Loop

Every review round is triaged before taking action. A reviewer's finding is a claim to check, not an order:

1. **Check Decisions & Status**:
   - For epics, check undecided findings:
     ```bash
     python3 skills/dev-implementation/resources/scripts/run_external_review.py check --epic-dir <epic_dir>
     ```
   - Print the triage skeleton:
     ```bash
     python3 skills/dev-implementation/resources/scripts/run_external_review.py triage --epic-dir <epic_dir>
     ```

2. **Verify Every Finding (No Performative Agreement)**:
   - Check every finding against the actual source code at candidate SHA.
   - Follow `d3nexus:receiving-code-review`: open the file and line, inspect the claim, and never accept or reject on the reviewer's word alone.

3. **Fill Assessment & Evidence**:
   - **Assessment**: `Valid` (the claim holds), `Debatable` (holds by letter, not intent), `False positive` (does not hold), or `Not shown` (reviewer lacked context).
   - **Evidence**: The file, line, and code quote verifying your assessment.
   - **Proposed action**: `fix`, `dismiss: <reason>`, or `none` for Minor findings.

4. **Present Triage and Wait**:
   - Present the completed triage table to the developer and stop. Wait for the developer's explicit decision on each finding.

5. **Commit Fixes & Record Decisions**:
   - Make each fix in its own commit: `[<EPIC_NAME>] Fix <what>`.
   - Update each Decision cell in `review_results.md`: `fixed in <sha>` or `dismissed: <reason>` in developer's exact words.
   - Commit decisions: `[<EPIC_NAME>] Record review decisions for round <n>`.
   - Re-run Gate 4 machine acceptance in full on the new candidate SHA.
   - Present Review Choice again only after Gate 4 returns PASS.

## References

- [Review Triage Protocol](references/review-triage.md): Verification discipline and decision cell standards.
- [Local Review Setup](references/local-review-setup.md): Guidance on setting up Ollama, Modelfiles, context budgets, and live logs.
