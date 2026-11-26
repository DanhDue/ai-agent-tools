---
name: cross-model-review
description: Reviews implemented code, commits, and diffs using external frontier models (Claude CLI, Codex CLI, Antigravity CLI, Kiro CLI) or local Ollama models with evidence-grounded triage.
---

# Cross-Model Review

## Overview

Cross-Model Review conducts Shift-Right independent code reviews on implemented software commits and diffs using external frontier models (Claude CLI, Codex CLI, Antigravity CLI, Kiro CLI) or local models (Ollama).

Operating on the principle of **Shift-Right Verification**, it catches code quality issues, missing test coverage, subtle concurrency regressions, architectural drift, and spec deviations before code is merged to main.

**Announce at start:** "I'm using the cross-model-review skill to conduct an independent code review."

## Two Modes of Operation

### 1. In-Lifecycle Mode (Automated Stage 3 Review after Gate 4 Local PASS)

Invoked automatically after all tasks of an epic are implemented and Gate 4 (machine acceptance) returns PASS.

- **Trigger**: Automatic transition from `dev-implementation` upon Gate 4 local PASS (zero intermediate confirmation pauses).
- **Scope**: Evaluates all task commits, diffs against base branch, audit disclosures, and integration test traceability in `.devtool/epic/<epic_dir>/`.
- **Execution**:
  - External CLI (`--auto-quota` or explicit `--cli` following priority `Claude -> Codex -> Kiro -> Argon` from `.devtool/review_config.json`):
    ```bash
    python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
      --epic-dir <epic_dir> --base <base_branch> [--auto-quota | --cli <claude|codex|kiro|agy>]
    ```
  - Local Ollama:
    ```bash
    python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
      --epic-dir <epic_dir> --base <base_branch> --cli ollama --model <model>
    ```
- **Persistence**: Results recorded into `.devtool/epic/<epic_dir>/review_results.md`.

### 2. Ad-Hoc Mode (Arbitrary Git Branch or Commits)

Invoked on-demand to review a feature branch, pull request diff, or specific commit range without requiring an epic directory.

- **Trigger**: Developer invokes `/cross-model-review --base <base> [--commits <range>] [--auto-quota | --cli <claude|codex|ollama|kiro|agy>] [--model <model>]`.
- **Scope**: Evaluates the commit range and diff against `--base` (or `--commits <range>`).
- **Execution**:
  ```bash
  python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
    --base <base_branch> [--commits <range>] [--auto-quota | --cli <claude|codex|kiro|agy>] [--model <model>]
  ```
- **Streaming & Visibility**:
  - The review output and formatted triage table stream directly to stdout.
  - Ephemeral review logs are written to `build/` (git-ignored) for live inspection.
  - No epic directory is required, and no `review_results.md` is created.

## Preconditions & Safeguards

1. **Clean Working Tree & Fast Mechanical Pre-Checks (< 5s, 0 Credits on Failure)**:
   - The runner enforces a clean git working tree before invoking any model (`commit or stash your changes before a review`).
   - Before invoking any external reviewer CLI, `run_external_review.py` runs fast mechanical pre-checks:
     - **Max 3 Rounds Guard**: Refuses a 4th round unless `--force` is passed (`[PRECONDITION BLOCKED] — Max review rounds (3) reached`).
     - **Gate 4 Epic Audit (`audit_epic.py`)**: Including the **Anti-Stub Enforcer** (`! git grep -n -E "def .+_stub\(|raise NotImplementedError|# STUB" src/`).
     - **Python Mechanical Gates** (when `.agents/quality/python-quality.json` is present): `anti_stub`, `importlinter_coverage` (`verify_importlinter_coverage.py`), and `self_probe` (`pre_review_self_probe.py`), plus Blast-Radius Scoped `Integration results:` and `check_bdd_traceability.py tests --results`.

2. **Quota-Aware Provider Selection (`check-quota`), 3-Round Convergence Funnel & Shared Context**:
   - **Provider Priority (`Claude -> Codex -> Kiro -> Argon`)**: Configured in `.devtool/review_config.json` (`provider_priority: ["claude", "codex", "kiro", "agy"]`, `max_rounds: 3`). With `--auto-quota`, `run_external_review.py` selects the highest-priority ACTIVE provider meeting thresholds: Claude/Codex (`5H >= 15%` AND `7D > 2%`), Kiro (`Monthly Credits >= 3%` AND `>= 15.0 credits`), or Argon (`Argon Weekly >= 10%` or `5H >= 15%`).
   - **3-Round Scope-Narrowing Convergence Funnel (Max 3 Rounds)**:
     - **Round 1 (`Scope: full`)**: Full audit of `base...HEAD` across touched modules (enforcing the **Exhaustive Per-File Pass** anti-drip-feed rule).
     - **Round 2 (`Scope: delta`)**: Verifies `fixed in <sha>` items and scopes diff to `Round1_SHA..Round2_SHA`; prohibits new `Minor` findings on untouched code.
     - **Round 3 (`Scope: convergence`)**: Strict Blocker-Only Convergence Mode (incomplete fixes or new `Critical`/`Important` regressions in `prev_sha..curr_sha`).
   - **Shared Context & 4 Anti-Fix-Loop Prompt Strategies**: `.devtool/epic/<epic_dir>/review_results.md` serves as the persistent Shared Context SSOT across rounds (`Earlier Rounds Shared Context Ledger`). `delta_round_context()` injects the **Universal Anti-Ping-Pong Guardrail** (both single-model and mixed-model), the **Previously Fixed Locations Registry (`Verify-Then-Close`)**, and **Diff-Hunk Isolation** on fixed files. See [review-triage.md](references/review-triage.md) for the complete 4-strategy specification.
   - CLI invocations run in read-only sandboxes under isolated process groups (`--timeout` default 1800s); any working-tree mutation discards the round immediately.

## The Triage & Fix Loop (Orchestrator + Role 2.1 / Role 2.3 Subagents)

Follow [review-triage.md](references/review-triage.md) and the role matrix in [orchestration-roles.md](../dev-lifecycle/references/orchestration-roles.md). In AUTO MODE (both `lifecycle_runner.py` AND interactive sessions where Gate 2 chose **Triển khai (tự động)**), run the risk-routed loop with **zero confirmation pauses between rounds** (`_can_fast_track_code_findings` -> `_apply_code_fixes`, else `_draft_fix_plan` dispatching the Role 2.1 `fix-planner`; halt ONLY on `ESCALATE`, `CIRCUIT_BREAKER_HALT`, or model/quota stops). Before each fix round run `python3 scripts/dev_config.py quota-check`; exit `2` means write `--checkpoint quota_low`, record a `quota` pending decision, and stop.

1. **Run & Triage (Role 2.2 Orchestrator)**:
   - Run `run_external_review.py run` and `triage`, commit `review_results.md`, and inspect `## Auto-Triage Gate`:
     ```bash
     python3 skills/dev-implementation/resources/scripts/run_external_review.py check --epic-dir <epic_dir>
     python3 skills/dev-implementation/resources/scripts/run_external_review.py triage --epic-dir <epic_dir>
     ```
   - **Boundary**: never read or edit `src/` / `tests/` and never run `pytest`/`ruff`/`mypy` in the main session.
   - **Route by risk** from the triage. **Low risk**: every open finding is `Valid` with severity `Important` or `Minor` (a `Critical` finding is always high risk) and the triage contains no escalation marker (`shared-contracts`, `CRITICAL_CONFLICT`, `SHARED_CONTRACT_CONFLICT`, `Debatable`, `ambiguous`, `architectural state transition`, `trade-off`, `Not shown`, `False positive`), or a Gate 4 failure is the first failure of that check: dispatch a `review-fixer` in `fast-track`. **High risk**: any `Critical` finding, any escalation marker, or the same Gate 4 check failing twice in a row: dispatch a `fix-planner`. The Orchestrator never rules on fix plans.

2. **`fix-planner` (Role 2.1, high risk only)** — `--mode read-only` on the `ai_architect_reviewer` binding (`python3 scripts/dev_config.py resolve ai_architect_reviewer --format argv --mode read-only`). It verifies the findings against code, the approved HLD, `bdd_scenarios.md` (legacy `bdd_scenarios.en.md`) and `Decisions Already Made`, is strictly read-only (edits no files), classifies each finding against the five halt criteria (`CRITICAL_CONFLICT`, `Debatable`/`Not shown`, `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, `MAX_ROUNDS_CRITICAL_REMAINING`) and returns `PLANNED` or `ESCALATE` with `plan_markdown` (Orchestrator writes and commits `fix_plan_round<N>.md`). On `ESCALATE` the Orchestrator records `--pending-decision`, renders the Top 3 Highest-Risk Findings, and stops for Role 1.0.

3. **`review-fixer` (Role 2.3)** — dispatched for `AUTO_FIX_ELIGIBLE`, `AUTO_PASS_FINAL_MINOR_SWEEP`, or `AUTO_PASS_FINAL_SWEEP` on the `programmer` binding through `python3 scripts/dev_config.py dispatch --persona programmer --mode write --prompt-file <file> --cwd <worktree> --log <log> --epic <slug>` (never a lighter in-runtime substitute such as `invoke_subagent` `Model="flash"`; no automatic fallback, no retry on a model or quota failure: checkpoint `model_unavailable`, record a blocker, stop):
     1. **`fast-track` / `apply-plan`**: The fixer applies code/test fixes (emitting `--phase fixing`; `apply-plan` follows a `PLANNED` plan exactly), runs **Tier 1 scoped tests only** (`--phase verifying`: `uv run pytest <changed_test_files> -n auto --timeout=30 -q --tb=short` + fast static checks; repo-wide pytest and `tests/e2e/` forbidden), commits `[<EPIC_NAME>] Fix <what>`, records `fixed in <sha>` in `review_results.md`, commits `[<EPIC_NAME>] Record review decisions for round <n>`, and returns the `review-fixer` JSON summary. Write `--checkpoint subagent_returned` after each subagent return.
     2. **Scope check (Orchestrator)**: `git diff --name-only <pre_sha>..HEAD`; any path under `shared-contracts/` or epic design docs halts with `CRITICAL_CONFLICT` (never auto-revert); other unexpected files go into the Gate 5 executive report.
     3. After every fix a fresh `gate4-verifier` reruns Gate 4 in full.
   - **Halt Triggers (`CIRCUIT_BREAKER_HALT`)**: Stop immediately and record `python3 scripts/resume_context.py --pending-decision "Resolve Cross-Model Review blocker (<reason>)" --decision-kind blocker --epic <epic_slug>` on `CRITICAL_CONFLICT`, `Debatable`/`Not shown`, `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, `MAX_ROUNDS_CRITICAL_REMAINING`, or a `fix-planner` `ESCALATE`:
     ```markdown
     Cross-Model Review Triage: Round <N> (<CLI>)

     • Candidate SHA: <commit_sha>
     • Reviewer: <CLI> ( <model> )
     • Thinking Level: <Light | Low | Medium | High | Extra High | None>
     • Verdict: <VERDICT> (<count> <Severity> findings)
     ```

3. **Final Convergence Gate & Stage 4 Handoff**:
   - Once Cross-Model Review converges (`AUTO_PASS_CLEAN`, `AUTO_PASS_FINAL_MINOR_SWEEP`, or `AUTO_PASS_FINAL_SWEEP` with 0 Critical findings), the Orchestrator dispatches a **fresh `gate4-verifier`** (not the round's fixer) to run **full Gate 4 machine acceptance** (full regression suite, `tests/e2e/`, `audit_epic.py`, and `@quality_check --profile epic`) on the latest candidate SHA. It accepts `PASS` only when `candidate_sha == git rev-parse HEAD`, the tree is clean, and the `@quality_check` report is bound to that SHA.
   - Once Gate 4 is green on candidate SHA, the Orchestrator records `python3 scripts/resume_context.py --state --epic <epic_slug> --status "Stage 4: Awaiting Finish"` and `python3 scripts/resume_context.py --pending-decision "Review Gate 5 executive report and choose Finish strategy" --decision-kind gate_5 --epic <epic_slug>`, emits `python3 scripts/resume_context.py --emit-prompt finish --epic <epic_slug>`, renders `## Top 3 Highest-Risk Findings (Executive Report)`, and stops calling tools ONCE with the unified Gate 5 + `/finishing-a-development-branch` Finish menu (`1. Merge locally`, `2. Push & PR`, `3. Keep as-is`).

## ⚡ Remediation Loop & Test Execution Protocol (Hard Constraints)

1. **Scoped Tests Only During Intermediate Fix Rounds (Round 1, Round 2...)**:
   - While fixing findings in intermediate rounds, run **ONLY** fast static/architecture checks (`ruff`, `mypy`, `lint-imports`, AST invariants) and **explicitly targeted test files** that directly cover modified modules:
     `uv run pytest <explicit_test_file_1.py> <explicit_test_file_2.py>`
   - **STRICTLY FORBIDDEN IN INTERMEDIATE ROUNDS**: Do NOT run repo-wide `pytest` discoveries (even with `-m "not slow..."`), do NOT run `tests/e2e/` browser suites, and do NOT pipe unfiltered repo-wide test runs into `| tail` (which hides hanging browser/SSE sockets).
   - **FINAL GATE ONLY**: Reserve the full regression suite, Playwright E2E browser harness, and full `quality_check` artifact regeneration strictly for the **Final Convergence Gate** after all code findings are resolved.

2. **Zero-Tolerance Anti-Evasion Rules (No Shortcut Fixes)**:
   - **No Dependency/Artifact Deletion**: Never resolve an unlocked dependency finding by removing the required package from `pyproject.toml`, and never resolve a stale quality report finding by simply deleting the report without regenerating it. If `uv.lock` is blocked by task scope rules, explicitly add `uv.lock` to the task's `Allowed files` and run `uv lock`.
   - **No Synthesized Fallback Fixtures**: When a finding flags fake/generated test data, do not replace it with another runtime generator. Load genuine immutable fixtures from disk and fail hard when missing.
   - **Browser Binary Synchronization**: Whenever `playwright` is added or upgraded in `pyproject.toml` / `uv.lock`, immediately run `uv run playwright install chromium` before invoking any browser E2E check.

## References

- [Review Triage Protocol](references/review-triage.md): Verification discipline and decision cell standards.
- [Local Review Setup](references/local-review-setup.md): Guidance on setting up Ollama, Modelfiles, context budgets, and live logs.
