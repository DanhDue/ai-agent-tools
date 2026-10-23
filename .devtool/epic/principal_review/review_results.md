# Cross-Model Review: principal_review

## Round 1

- **Date**: 2026-10-23T10:47:17Z
- **SHA**: c09cb95593c5908098462a0a2963f1a300d9efcb
- **Base**: main
- **CLI**: codex
- **Model**: default
- **Status**: completed
- **Verdict**: CHANGES REQUIRED

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | skills/dev-implementation/resources/scripts/check_epic_readiness.py:157-176 | R1 only sends already-complete language pairs to `--require-bilingual`; a missing `.en.md` or `.vi.md` counterpart is omitted entirely, allowing incomplete spec, HLD, or BDD artifacts to pass. | fixed in 81376fa |
| 2 | Important | skills/dev-implementation/resources/scripts/check_epic_readiness.py:575-595 | R7 validates `Design commit` only when the line matches; a handoff with the field missing silently passes despite the published contract requiring `uncommitted` or an ancestor of HEAD. | fixed in 81376fa |
| 3 | Important | skills/dev-lifecycle/references/principal-review.md:13-15 | The recommendation omits D2’s different-model trigger and required HLD `Author` grounding, and does not include the HLD’s promised recommendation to use each CLI’s strongest reasoning model. | fixed in 55af9ec |
| 4 | Important | skills/dev-lifecycle/references/principal-review.md:49-58 | The procedure records `fixed in <sha>` and commits decisions before the revision commit that would create that SHA, then requests a separate revision commit; the prescribed order cannot produce truthful decision metadata. | fixed in 55af9ec |

Raw output:

````text
The supplied audit, 22/22 traceability result, task evidence, and protected-path changes are consistent. No grader amendments or out-of-task commits were disclosed. However, static inspection found four merge-blocking contract gaps not covered by the passing tests.

Gate 5 still requires:

- Human confirmation that the Principal Reviewer prompt is a genuine sign-off brief covering P1–P8.
- A developer-selected packaged-epic trial proving `check_epic_readiness.py` produces an accurate, useful report.

No files or Git state were changed.

Verdict: CHANGES REQUIRED
[Important] skills/dev-implementation/resources/scripts/check_epic_readiness.py:157-176 — R1 only sends already-complete language pairs to `--require-bilingual`; a missing `.en.md` or `.vi.md` counterpart is omitted entirely, allowing incomplete spec, HLD, or BDD artifacts to pass.
[Important] skills/dev-implementation/resources/scripts/check_epic_readiness.py:575-595 — R7 validates `Design commit` only when the line matches; a handoff with the field missing silently passes despite the published contract requiring `uncommitted` or an ancestor of HEAD.
[Important] skills/dev-lifecycle/references/principal-review.md:13-15 — The recommendation omits D2’s different-model trigger and required HLD `Author` grounding, and does not include the HLD’s promised recommendation to use each CLI’s strongest reasoning model.
[Important] skills/dev-lifecycle/references/principal-review.md:49-58 — The procedure records `fixed in <sha>` and commits decisions before the revision commit that would create that SHA, then requests a separate revision commit; the prescribed order cannot produce truthful decision metadata.


--- stderr ---
OpenAI Codex v0.162.1
--------
workdir: /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: medium
reasoning summaries: none
session id: 01a1685c-a4a9-7e13-a096-fb6c2cfec68b
--------
user
# External Review Prompt

You are an independent reviewer of a finished epic. You are strictly read-only: do not modify, create, or delete any file, and do not run commands that write to the repository or alter git state. Read the artefacts, inspect the provided code diff, and report.

## Candidate

- Commit under review: `c09cb95593c5908098462a0a2963f1a300d9efcb`
- Base the epic branched from: `main`
- Epic directory: `.devtool/epic/principal_review`

## Artefacts

Read these paths, relative to the repository root:

- `.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md`
- `.devtool/epic/principal_review/2026-10-22-principal-review-design.vi.md`
- `.devtool/epic/principal_review/handoff.md`
- `.devtool/epic/principal_review/principal_review.en.md`
- `.devtool/epic/principal_review/bdd_scenarios.en.md`
- `.devtool/epic/principal_review/task_1_readiness_check_core.md`
- `.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md`
- `.devtool/epic/principal_review/task_3_principal_review_runner_mode.md`
- `.devtool/epic/principal_review/task_4_epic_status_sync_scope.md`
- `.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md`
- `.devtool/epic/principal_review/evidence/`

## Facts gathered for you

The audit of the epic branch, with its exit code:

```text
$ audit_epic.py
exit 0
### Evidence
- task_1_readiness_check_core: PASS
- task_2_readiness_grounding_and_baseline: PASS
- task_3_principal_review_runner_mode: PASS
- task_4_epic_status_sync_scope: PASS
- task_5_principal_review_choice_and_acceptance: PASS

### Legacy tasks
None

### Protected paths
- 97fcbe4 skills/dev-implementation/resources/scripts/test_sync_task_status.py
- a0e1537 skills/dev-implementation/resources/scripts/test_run_external_review.py
- c09cb95 scripts/test_lifecycle_document_contract.py
- c09cb95 scripts/verify.sh

### Grader amendments
None

### Commits outside tasks
None

### Gate 5 items
- task_3_principal_review_runner_mode: The principal prompt reads as a Principal Reviewer's sign-off brief and covers P1–P8. (Gate 5)
- task_5_principal_review_choice_and_acceptance: Run against a packaged epic the developer chooses (for example lyrics-sync's `flashcard_compact_data_enrichment` at `5cc7d720` in a scratch worktree), `check_epic_readiness.py` produces a report the developer judges accurate and useful. (Gate 5)

Result: PASS
```

The integration test commands and the result-based traceability check, with their exit codes:

```text
$ python3 scripts/run_unittest_junit.py --junitxml build/test-results/principal-review.xml skills/dev-implementation/resources/scripts/test_check_epic_readiness.py skills/dev-implementation/resources/scripts/test_run_external_review.py skills/dev-implementation/resources/scripts/test_sync_task_status.py scripts/test_lifecycle_document_contract.py scripts/test_lifecycle_signals.py scripts/test_verifiable_handoff_text.py
exit 0
.........
----------------------------------------------------------------------
Ran 9 tests in 9.076s

OK
......................................
----------------------------------------------------------------------
Ran 38 tests in 22.836s

OK
.............................................................
----------------------------------------------------------------------
Ran 61 tests in 8.349s

OK
.................
----------------------------------------------------------------------
Ran 17 tests in 0.007s

OK
....
----------------------------------------------------------------------
Ran 4 tests in 0.678s

OK
......
----------------------------------------------------------------------
Ran 6 tests in 0.002s

OK

$ /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review/skills/dev-implementation/resources/scripts/check_bdd_traceability.py tests --scenarios .devtool/epic/principal_review/bdd_scenarios.en.md --roots 'skills/dev-implementation/resources/scripts/, scripts/' --results build/test-results/principal-review.xml
exit 0
PRV-HP-01    PASS test_prv_hp_01_ready_fixture_epic_passes_every_check
PRV-EC-01    PASS test_prv_ec_01_symbol_missing_from_file_fails_r5
PRV-EC-02    PASS test_prv_ec_02_tier_drift_fails_r3_and_tier_b_tag_fails_r4
PRV-EC-03    PASS test_prv_ec_03_tier_c_test_outside_integration_results_fails_r6
PRV-EC-04    PASS test_prv_ec_04_mirror_drift_fails_and_location_link_passes
PRV-EC-05    PASS test_prv_ec_05_metadata_packaged_without_handoff_and_draft_spec
PRV-EC-06    PASS test_prv_ec_06_route_not_found_warns_r5b
PRV-FR-01    PASS test_prv_fr_01_baseline_failures_and_timeouts_warn
PRV-FR-02    PASS test_prv_fr_02_failing_preflight_subcheck_and_missing_dir
PRV-HP-02    PASS test_prv_hp_02_principal_round_recorded_in_principal_review_md
PRV-HP-03    PASS test_prv_hp_03_findings_with_proposed_edits_become_table_rows
PRV-ST-01    PASS test_prv_st_01_decisions_move_check_from_1_to_0
PRV-ST-02    PASS test_prv_st_02_triage_reads_selected_file
PRV-AR-01    PASS test_prv_ar_01_second_round_before_commit_refused
PRV-FR-03    PASS test_prv_fr_03_readiness_fail_blocks_cli
PRV-FR-04    PASS test_prv_fr_04_ollama_rejected_before_precheck
PRV-HP-05    PASS test_prv_hp_05_own_worktree_updated
PRV-FR-05    PASS test_prv_fr_05_other_epics_untouched
PRV-HP-04    PASS test_prv_hp_04_packaging_readiness_and_principal_review_choice
PRV-EC-07    PASS test_prv_ec_07_handoff_template_reads_first_principal_review
PRV-ST-03    PASS test_prv_st_03_diagram_loop_returns_to_package_and_done_repackages
PRV-ST-04    PASS test_prv_st_04_gate_3_stops_while_principal_finding_undecided
Result: 22/22 covered — PASS
```

All commands above have passed their execution gates (exit 0); inspect their output details for coverage, warnings, or audit disclosures.

## Code Changes (Diff)

Full file change summary (`git diff --stat`, including locks/codegen):

```text
docs/lifecycles.en.md                              |  13 +-
 docs/lifecycles.vi.md                              |  13 +-
 scripts/test_lifecycle_document_contract.py        |  78 ++
 scripts/verify.sh                                  |   1 +
 skills/dev-implementation/SKILL.md                 |   5 +-
 .../references/principal-review-prompt.md          |  57 ++
 .../references/principal-review-rules.md           |  20 +
 .../resources/scripts/check_epic_readiness.py      | 801 +++++++++++++++++++++
 .../resources/scripts/run_external_review.py       |  96 ++-
 .../resources/scripts/sync_task_status.py          |  86 ++-
 .../resources/scripts/test_check_epic_readiness.py | 754 +++++++++++++++++++
 .../resources/scripts/test_run_external_review.py  | 200 +++++
 .../resources/scripts/test_sync_task_status.py     |  86 +++
 skills/dev-lifecycle/SKILL.md                      |  11 +-
 .../dev-lifecycle/references/handoff-template.md   |   1 +
 .../dev-lifecycle/references/principal-review.md   |  70 ++
 16 files changed, 2261 insertions(+), 31 deletions(-)
```

The source diff is large (2664 lines, 117 KB > inline budget). Do NOT run an unfiltered `git diff`; inspect specific target files via `git diff main...c09cb95593c5908098462a0a2963f1a300d9efcb -- <path>` as needed.

## Verification Hierarchy & Process Rules

To avoid false-positive findings, evaluate evidence against these architectural principles:

1. **Task-Level vs. Gate 4 Workspace Scope**:
   - Each task's `Verification` table is strictly scoped to that individual task's deliverables (e.g. documentation, domain models, or specific adapters).
   - Tasks are NOT required to execute workspace-wide profiles. Full workspace capabilities (coverage thresholds, security advisories/deny, FFI/WASM release builds, database hygiene, and end-to-end acceptance) belong exclusively to the platform-neutral **Gate 4 Quality Orchestrator (`@quality_check`)** evaluated on the final candidate SHA. Do not report task evidence as defective solely because it does not run the entire workspace epic profile.
2. **Compiled Language TDD RED Semantics**:
   - In compiled languages (Rust, Go, C++, etc.), the initial TDD RED phase for a new component or function is legitimately satisfied by a compilation failure or missing test target. A non-zero exit code prior to implementation code being written demonstrates a valid RED state.
3. **Artifact Budget Assertions**:
   - Verify that test assertions checking generated build artifacts (such as WASM binary size or exported types) strictly verify that the target artifact actually exists (avoiding vacuous false-PASS loops).
4. **Contract Drift Inspection**:
   - Check whether code constants, default parameters, and enum variants match the published API reference documentation and cross-epic integration contracts without divergence.
5. **No Reconstructed Logic**:
   - Tests MUST import and invoke production code directly from Allowed files. Tests MUST NOT reconstruct production logic (such as retry loops, progress tracking, mapping transformations, or configuration defaults) locally within test helpers or mock harnesses.
   - A test that reconstructs production logic instead of invoking production symbols is a blocking finding; Gate 4 reports it as FAIL.
6. **Immutable Real Artifacts**:
   - Tests MUST execute against genuine, immutable repository artifacts, schemas, and fixtures. Tests MUST NOT substitute synthetic artifacts or mock data that alter scenario anchors or weaken contractual invariants.
   - A test that substitutes synthetic artifacts altering scenario anchors is a blocking finding; Gate 4 reports it as FAIL.

## Checklist

- Each done task's evidence against its Verification table, and rows too weak for the Definition of Done item they back.
- Whether each identifier's test genuinely exercises its Gherkin scenario, or merely passes superficially.
- Each audit disclosure — grader amendments, protected path changes, commits outside tasks — and whether it is justified.
- Whether the implementation respects the spec, the HLD, schema definitions, and each task's Decisions Already Made.
- The `(Gate 5)` items, restated clearly for the developer.

## Required output

Do NOT use the bracketed tags `[Critical]`, `[Important]`, or `[Minor]` anywhere in your prose or analysis above the final verdict block.

End your answer with these exact lines and nothing after them (no markdown bolding `**`, no backticks, no bullet before `Verdict:`):

Verdict: PASS
(or `Verdict: CHANGES REQUIRED`)
[Critical|Important|Minor] <artefact>:<location> — <problem>

Rules for Severity & Verdict:
- Use `Critical` for a defect that breaks the epic's goal, `Important` for one that must be fixed before merge, and `Minor` for anything else.
- Output `Verdict: CHANGES REQUIRED` if and only if there is at least one `Critical` or `Important` finding.
- If there are no findings (or only `Minor` findings), you MUST output `Verdict: PASS`.
- A review with no finding still ends with its `Verdict: PASS` line.

2026-10-23T10:44:27.267287Z ERROR codex_memories_write::phase2: Phase 2 no changes
hook: SessionStart
hook: SessionStart Completed
codex
I’m using `d3nexus:pr_review` to structure the independent, SHA-bound review, plus the Codex tool-mapping instructions required by the kit. I’ll keep all inspection strictly read-only and finish with the exact verdict format you specified.
exec
/bin/zsh -lc "sed -n '1,240p' /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.13.0/skills/pr_review/SKILL.md && sed -n '1,240p' /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.13.0/skills/using-superpowers/references/codex-tools.md" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
---
name: pr_review
description: Performs comprehensive Pull Request reviews by delegating quality verification to quality_check with profile pr, validating project-registered provider contracts, and consuming the unified executive report.
---

# Pull Request Review Skill

## Overview

The PR Review skill automates Pull Request code review by delegating quality verification to the platform-neutral
orchestrator [`@quality_check`](../quality_check/SKILL.md).

It requests the `pr` quality profile, ensuring fast, focused verification of changed scope, required architecture gates,
linting, unit tests, and security audits as registered by the project in `.agents/quality/check_quality.json`.

## Architecture and Delegation Flow

```mermaid
flowchart TD
    TRIGGER(["Trigger: @pr_review (PR Diff / Commit)"]) --> RESOLVE["Resolve target branch (base_ref) and HEAD SHA"]
    RESOLVE --> INVOKE["Invoke @quality_check with profile=pr"]
    INVOKE --> ORCH["quality_check discovers and runs registered providers"]
    ORCH --> REPORT["Return Unified Executive Quality Report"]
    REPORT --> VERDICT{"Overall status"}
    VERDICT -->|"PASS"| LGTM["Render 🟢 LGTM approval"]
    VERDICT -->|"FAIL"| REJECT["Render 🔴 CHANGES REQUESTED with defect breakdown"]
    VERDICT -->|"BLOCKED"| BLOCKED["Render 🔴 BLOCKED with infrastructure blocker list"]
```

## Input Methods

| Input Type | Description | Command / Usage |
| :--- | :--- | :--- |
| **Working Diff** | Review staged or uncommitted local changes | `@pr_review` (analyzes current `git diff`) |
| **Commit ID** | Review changes introduced by a specific commit | `git show <COMMIT_ID>` or `@pr_review commit=<COMMIT_ID>` |
| **PR Number / Diff** | Review Pull Request changes via GitHub CLI | `gh pr diff <PR_NUMBER>` |
| **Branch Range** | Review changes against the base branch | `git diff origin/main...HEAD` or `git diff origin/develop...HEAD` |

## Review Workflow

1. **Resolve Identity & Base**:
   - Resolve target branch base reference (e.g. `main`, `develop`) and candidate git commit SHA.
2. **Invoke Quality Orchestration via `@quality_check`**:
   - Construct normalized invocation request:
     ```json
     {
       "contract_version": 1,
       "profile": "pr",
       "base_ref": "<base_ref>",
       "repository_sha": "<head_sha>"
     }
     ```
   - Delegate execution to `@quality_check`, which loads `.agents/quality/check_quality.json`, fans out to registered providers supporting `pr`, and validates results.
3. **Synthesize & Render Verdict**:
   - Consume the unified executive report from `@quality_check`.
   - **🟢 LGTM**: Granted only when overall status is `PASS`.
   - **🔴 CHANGES REQUESTED**: If status is `FAIL`, detail all failing checks, code smells, and defect locations.
   - **🔴 BLOCKED**: If status is `BLOCKED`, report missing dependencies, unexecutable tools, or unresolvable contracts.

## Executive Report Format

PR reviews format output using the standard [Executive Report Format](../quality_check/references/executive-report-format.md) emitted by `@quality_check`.
# Using d3nexus in Codex

The plugin ships the same skills in all runtimes. When a skill uses a Claude Code tool name,
perform the equivalent action using the tools exposed by the current Codex session.

| Skill instruction | Codex action |
|---|---|
| Invoke `Skill` or `d3nexus:<name>` | Select the installed d3nexus skill, then read its `SKILL.md` and follow it. Resolve supporting paths relative to that skill's directory. |
| `Read`, `Grep`, `Glob` | Use file tools or shell reads; prefer `rg` and `rg --files` for searches. |
| `Edit`, `Write` | Use the available patch or file editing tool. |
| `Bash` | Use the session's shell execution tool, respecting its permission boundaries. |
| `TodoWrite` | Use an available plan/task tool, or maintain a short progress checklist if none exists. |
| `Agent`, `Task`, parallel reviewers | Use subagents only when available and authorized. Otherwise perform independent steps sequentially and report the limitation. |

Codex reads the consuming project's `AGENTS.md`. Claude's `@file` import syntax and Antigravity's
Markdown `trigger: always_on` frontmatter are not substitutes for explicit reading instructions.
Read the project's rule files when present; otherwise read the plugin's
[critical rules](../../../rules/CRITICAL_RULES.md) and
[coding guidelines](../../../rules/coding-guidelines.md).

Keep `d3nexus:` cross-references in shared skill text. They identify the owning plugin; they do
not imply that Codex has Claude's slash-command or `Skill` API. Use the skill picker or name the
plugin and skill in a prompt when invocation syntax differs across Codex surfaces.

Follow the current host's instruction hierarchy and honor the user's authorized scope. References
to Antigravity's native planning artifact apply to that environment; do not invent unavailable
tools or configuration in Codex. Platform build tools, credentials, and devices requested by a
skill still need to exist in the consuming project.

After reinstalling or upgrading the plugin, start a new thread to load the updated skill inventory.

codex
The review skill normally launches the repository’s PR quality profile, but this prompt forbids repository writes and supplies the completed audit/integration outputs. I’ll therefore validate those supplied results against the committed artifacts and diff, while checking the quality contract and repository rules without rerunning write-producing verification. I’m also applying `d3nexus:task-observer`; if its logging requirements conflict with strict read-only scope, the user’s scope takes precedence.
exec
/bin/zsh -lc "sed -n '1,280p' \"rules/coding-guidelines.md\"" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
exec
/bin/zsh -lc "sed -n '1,280p' \"rules/CRITICAL_RULES.md\"" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
exec
/bin/zsh -lc "sed -n '1,280p' \"/Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.13.0/skills/task-observer/SKILL.md\"" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
exec
/bin/zsh -lc "sed -n '1,280p' \"/Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.13.0/skills/quality_check/SKILL.md\"" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
---
trigger: always_on
---

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

> **TL;DR — 4 rules to always follow:**
> 1. **Think first** — State assumptions, ask when unclear, present tradeoffs before acting.
> 2. **Simplicity** — Minimum code that solves the problem. If it could be 50 lines, don't write 200.
> 3. **Surgical** — Touch only what the request requires. Don't improve adjacent code.
> 4. **Verify** — Define success criteria upfront. Don't claim done without running the check.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

 succeeded in 0ms:
---
trigger: always_on
---

# Critical Rules

> [!CRITICAL]
> These rules are MANDATORY and MUST be strictly applied by ALL AI Agent Plugins, runtimes, orchestrators, and subagents (including Claude Code, Antigravity IDE, Cursor, Codex, Windsurf, OpenCode, and any custom/third-party plugins) in every interaction across this project and downstream repositories. Failure to follow these rules is a direct violation of the engineering standard.

## Universal Scope & Plugin Applicability

> [!IMPORTANT]
> **Every AI Agent plugin operating in this environment MUST inherit and execute these rules.**
> Regardless of which plugin, tool, extension, or agent framework initiated the session:
> - Built-in or third-party plugins must NEVER override, circumvent, or weaken these rules.
> - Subagents, background runners, and multi-agent teams spawned by any plugin inherit these exact constraints.
> - If an AI agent or plugin has conflicting built-in behaviors (e.g. auto-pushing, autonomous planning artifacts, skipping human checkpoints), these Critical Rules take absolute precedence.

## 1. Mandatory Quality Gates

> [!IMPORTANT]
> After completing any workflow or skill — regardless of which plugin or tool executed it — you **MUST** run the quality gate for the **kind of work you did**, and fix any issues it raises. This is critical to maintain the quality of the project.
>
> | Kind of work | Gate |
> |---|---|
> | Anything that changes a file shipping in the build | `@quality_check` |
> | Anything whose deliverable is prose | `@doc_quality_check` |
>
> The two share no tier, no audit and no tooling. Running the wrong one produces a green light that means nothing — and `@doc_quality_check` refuses outright if the change touches shipped files.
>
> See: [Quality Check Skill](../skills/quality_check/SKILL.md) · [Document Quality Check Skill](../skills/doc_quality_check/SKILL.md)

## 2. Commit Message Format (Universal Standard)

Every commit — written by a skill, a plugin, an agent, or by hand — uses a bracketed scope, a one-line title, and a bullet list of the subtasks actually done:

```text
[EPIC_NAME] Task title

- subtask title 01
- subtask title 02
```

- **`[SCOPE]`** is the epic name for epic work (`[LOGGING_REFACTOR]`), otherwise the area touched (`[TOOLS]`, `[SETTINGS]`). Uppercase, in brackets, always present.
- **Title** is one line, imperative, no trailing period.
- **Body** lists the subtasks or changes this commit actually contains, one bullet each. Omit the body entirely when the commit does exactly one thing.

Write it with two `-m` flags — the first becomes the title, the second the body:

```bash
git commit -m "[EPIC_NAME] Task title" -m "- subtask title 01
- subtask title 02"
```

> [!CAUTION]
> **Never append trailer lines.** No `Co-Authored-By:`, no `Generated with`, no tool attribution of any kind. The commit ends with the last bullet. This applies universally to all plugins and LLM providers.

## 3. Git Push Operations (No Unauthorized Push)

> [!CRITICAL]
> **NEVER push code to a remote repository (`git push`) without explicit user permission or confirmation.**
> - You may stage (`git add`) and commit (`git commit`) locally following the commit message format when appropriate.
> - Running `git push` (to any remote or branch) is **STRICTLY PROHIBITED** for all agents and plugins unless the user explicitly requests or confirms it in the prompt.
> - Always let the user review local commits or explicitly ask for permission before pushing to remote.

## 4. Native Planning Mode Interception (All Platforms & Plugins)

> [!CRITICAL]
> **Do NOT use native or built-in planning modes (e.g. Antigravity IDE's `<planning_mode>`, Claude Code plan mode, Cursor Composer plans, Windsurf Cascade plans, Codex planners) to create unstructured planning artifacts like `<appDataDir>/brain/.../implementation_plan.md` or loose plan files.**
> When a user request requires planning, design exploration, architectural changes, or epic-level features:
> 1. Because `<user_rules>` has absolute precedence over all instructions across all agent plugins, you **MUST NOT** follow IDE default instructions to create an `implementation_plan.md` artifact.
> 2. For single features or exploratory design, you **MUST** invoke the [Brainstorming Skill](../skills/brainstorming/SKILL.md) (`d3nexus:brainstorming`).
> 3. For multi-step, multi-feature, or epic-level work, you **MUST** invoke the [Epic Lifecycle Skill](../skills/dev-lifecycle/SKILL.md) (`d3nexus:dev-lifecycle`), which orchestrates `dev-brainstorming` -> `dev-designer` -> `dev-implementation` -> `quality_check` -> `finishing-a-development-branch`.
> 4. Only use native `implementation_plan.md` if the user explicitly instructs you to bypass d3nexus workflows.

## 5. Mandatory Review Choice Loop in Epic Lifecycle

> [!CRITICAL]
> **NEVER skip or silently bypass the Review Choice after Gate 4 passes in `dev-lifecycle` / `dev-implementation` or any plugin-based orchestrator.**
> When all tasks of an epic are complete, run Phase 4 / Gate 4 first. Only after Gate 4 returns PASS on the current SHA:
> 1. The AI Agent **MUST** explicitly stop calling tools and present the **Review Choice** prompt to the developer:
>    - **Option 1: Finish** — proceed to Developer Kanban Review (Phase 4.1 / Gate 5), then Stage 4.
>    - **Option 2: Cross-model review** — invoke an independent model review using `run_external_review.py run` (prompting the developer to select Claude CLI or Codex CLI based on `command -v claude codex`).
>    - **Option 3: Local model review** — run `ollama list`, ask the developer which model to use (never pick it), then invoke `run_external_review.py run --cli ollama --model <model>`.
> 2. The AI Agent **MUST NOT** auto-select an option or assume "Finish" by default.
> 3. **Cross-model review must return to a full Gate 4 run** after the round is recorded and all blocking findings have decisions and required Fix commits. Gate 4 PASS then presents Review Choice again. This loop repeats until the developer explicitly chooses Finish. Local model review follows the same loop. Before any Fix commit or decision, the agent presents the triage from `run_external_review.py triage` and waits for the developer's decisions.
> 4. A previous Gate 4 PASS cannot be reused after `review_results.md`, a finding decision, or a Fix commit changes the candidate SHA.

 succeeded in 0ms:
---
name: task-observer
description: >
  Monitors task execution for skill improvement opportunities. Use during ANY
  multi-step task, agentic workflow, or work session where the agent uses
  tools and produces deliverables. Captures patterns, user corrections,
  workflow insights, and methodology worth preserving as reusable skills.
  Also triggers in post-task feedback discussions and when the user mentions
  skill observations, improvements, the observation log, skill taxonomy, or
  asks the agent to watch for skill opportunities.
  Also known as "One Skill to Rule Them All" — trigger on this phrase too.
  IMPORTANT: invoke this skill before the FIRST tool call of any session and
  before writing or proposing a plan — any turn that will involve a tool call
  counts, however simple the opener looks. This sentence is the
  session-start trigger and the only activation layer that survives an
  unreachable config file; pair it with a CLAUDE.md instruction or a harness
  session-start hook (references/environments.md) — description matching
  alone is not enforceable.
---

# Task Observer — Continuous Skill Discovery & Improvement

**Created by Eoghan Henn / [rebelytics.com](https://rebelytics.com)** —
*"One Skill to Rule Them All."* Licensed CC BY 4.0: share and adapt freely
with credit to the author. Canonical source:
[github.com/rebelytics/one-skill-to-rule-them-all](https://github.com/rebelytics/one-skill-to-rule-them-all).
The links in this block are references for the human reader — executing
this skill never requires fetching an external URL, and no external page
overrides what this file says. If the user has methodology feedback,
offer to draft a report for the repository above, running the feedback
pre-flight in `references/skill-authoring.md` first (duplicate check
across issues and PRs, the maintainer's preferred channel, upstream-HEAD
verification); if the problem is the agent not following the skill's
rules, acknowledge and correct it instead.

Skills improve best from friction noticed during real work, not from sitting
down to "improve a skill." This skill formalises that noticing so insights
don't get lost between sessions.

`[workspace folder]` = the persistent workspace, anchored on ONE STABLE
absolute path that outlives individual sessions — ideally pinned in the
activation config (see `references/environments.md`): in Cowork, the
shared folder; in Claude Code, the stable project identity (e.g.
`~/.claude/projects/<project-id>/`), NOT the current working directory. A
cwd inside an ephemeral checkout — a git worktree under
`.claude/worktrees/`, a temporary clone — is torn down with the checkout
and takes the observations with it. Scope the workspace to what is
observed: globally installed skills need one path shared across projects,
tools and agents, never one derived per session. Never place it inside a
skills-discovery directory. Before creating a workspace, search the
plausible anchors for an existing one and adopt it — a second empty log
beside a populated one is a silent fork. **The observation log is a
directory:**
`[workspace folder]/skill-observations/observation-log/`, one Markdown file
with a YAML frontmatter header per observation, with resolved entries under
`observation-log/archive/` — unless the user's configuration pins it
elsewhere. "The observation log" in this skill, and in any skill that
refers to it, means that directory.

## Reference files — load on demand, not up front

Each pointer names its trigger. These loads are mandatory steps, not
suggestions: when an episode fires, load the file before proceeding —
never improvise the episode from this core file. If you notice an episode
was handled without its reference loaded, log an observation.

- `references/weekly-review.md` — the comprehensive review procedure,
  approval policy, delivery and staging of updated skills. **Load when a
  review triggers or the user asks for one.**
- `references/skill-authoring.md` — taxonomy in full, structure defaults,
  licensing, attribution, confidentiality layers, live-file editing and
  relocation-verification rules. **Load before creating or editing any
  skill.**
- `references/observation-log.md` — storage layout, frontmatter fields,
  helper snippets, archival details, and the reasoning behind the rules.
  **Load when setting up the log for the first time, when archiving, when
  an id or frontmatter looks wrong, or before changing how anything reads
  the log.**
- `references/signals.md` — the full catalogue of what is and isn't worth
  logging. **Load when unsure whether something is an observation, or when
  sorting many candidates.**
- `references/environments.md` — activation and config setup, compaction
  behaviour, bundle manifest, handoff-doc mode for storage-less
  environments. **Load for setup questions, after compaction, or when
  there is no filesystem.**
- `references/migration.md` — the one-time scripted conversion of a
  pre-3.0 single-file `log.md`. **Load only when the Session Start
  Protocol detects a legacy log.** Fresh installs never read it.

## Session Start Protocol

1. **Storage.** If `skill-observations/observation-log/` (with its
   `archive/` subdirectory) or
   `skill-observations/cross-cutting-principles.md` don't exist,
   create them (principles template: `references/skill-authoring.md`).
   Create `skill-observations/last-review-date.txt` containing the literal
   value `never` if it doesn't exist — never write a date into it at setup;
   a date means a review actually ran. If a legacy single-file
   `skill-observations/log.md` exists and `observation-log/` does not, this
   is an upgrade from a pre-3.0 install: load `references/migration.md` and
   run the scripted conversion before writing anything else. Before
   creating or writing anything: if the resolved workspace folder sits
   under an ephemeral path (e.g. `.claude/worktrees/`, a temporary clone),
   warn the user and re-anchor on the stable project path first — state
   written to an ephemeral checkout is lost at teardown.
2. **Scan.** Read only the frontmatter of each file in `observation-log/`
   — the header block between the first two `---` lines, never the bodies
   — and build awareness from `status`, `skill`, `proposes_skill` and
   `title`; also read the active principles. Hold them in awareness, don't
   surface unprompted. Frontmatter-only is the whole point of the per-file
   format: the scan stays cheap once hundreds of observations exist.

   **An empty scan in a log known to be non-empty is a broken command
   until proven otherwise**, never the finding "no relevant observations".
   Count the files independently of the parse — a literal path, not the
   variable the loop uses — and halt if files exist but nothing parsed.
   Re-derive every path inside the same tool call: shell state does not
   carry between calls in most harnesses, and a path variable that
   silently resolves to empty turns a filter into a match-nothing glob
   rather than an error.

   ```bash
   d=skill-observations/observation-log                                # re-derive in EVERY call
   n=$(ls skill-observations/observation-log/*.md 2>/dev/null | wc -l) # literal path: independent of $d
   parsed=0
   for f in "$d"/*.md; do
     [ -e "$f" ] || continue
     hdr=$(awk 'NR==1 && /^---[[:space:]]*$/ {fm=1; next}
                fm && /^---[[:space:]]*$/ {exit}
                fm' "$f")
     [ -n "$hdr" ] && parsed=$(( parsed + 1 ))
     printf '%s\n---\n' "$hdr"
   done
   [ "$n" -gt 0 ] && [ "$parsed" -eq 0 ] && \
     { echo "SCAN COMMAND BROKEN — $n files present, 0 headers parsed"; exit 1; }
   ```
3. **Review trigger.** Read `skill-observations/last-review-date.txt`. The
   value carries the truth: a date = when the last review actually ran;
   `never` = no review has run yet. A missing file is abnormal (step 1
   creates it) — recreate it with `never`, don't invent a date. If the
   value is `never` or older than 7 days AND there are OPEN observations:
   in an interactive session, offer the review in one line ("the
   observation backlog hasn't been reviewed [in N days / yet] — run it now,
   or carry on with your task?") and proceed with the user's task unless
   they opt in; never gate their work on the review. Only a
   scheduled/autonomous run loads `references/weekly-review.md` and runs
   the review unprompted.
4. **Activation.** Once per session: if no CLAUDE.md (or equivalent)
   activation instruction for this skill exists, briefly suggest adding one
   (see `references/environments.md`). Skip if already configured.
5. **Concurrency.** There is no shared log file to guard: each observation
   is its own file, so creating one never collides with or overwrites
   another session's entry. Before changing the *status* of an existing
   observation, re-read that one file first (a parallel review may have
   resolved it).
6. **Targets and staged work.** Resolve each distinct `skill:` value in
   the scanned frontmatter against the installed skill set and mention, in
   one line, any that no longer resolve — a deleted skill can accumulate
   dozens of observations before a review discovers the target is gone.
   If `skill-updates/PENDING.md` lists staged updates, say "N staged
   updates awaiting review" in one line.
7. **First run.** If the log is empty and the project has history
   (handover or decision docs, commit history, test scripts, an existing
   CLAUDE.md — which is largely a record of corrections nobody logged),
   offer a one-off backfill pass over those artefacts. Backfilled entries
   cite the durable artefact (file and section) in `session_context`
   instead of a session, and the same-turn immediacy rule is satisfied by
   one batched write. The pass is one-off; the scheduled review takes
   over afterwards.

## When to Observe

Active for the entire task session — execution, post-task feedback, review
discussion, meta-discussion about skills or methodology, and strategy
conversations about how work should be done. **The observation mindset
does not deactivate when the conversation shifts from doing the work to
discussing it**; review-phase feedback is often the highest-signal input.
Inactive only for casual conversation and quick factual questions with no
tools or deliverables involved.

## What to Watch For

**New skill:** a reusable multi-step workflow, a methodology the user
explains that no skill captures, a recurring task type, a process the user
describes as "I always do it this way". **Improve a skill:** the agent
violates a documented rule (the skill needs enforcement, not louder rules);
a user correction reveals a missing rule or edge case; a better workflow or
technique emerges than the skill recommends; a wrong assumption; new
tooling obsoletes a step; a principle that applies to other skills too.
**Simplify a skill:** a section never relevant across many sessions, a rule
from a single unvalidated observation, contradictory rules, a rule the
agent consistently fails to follow — convert to structural enforcement or
remove. Full catalogue with examples: `references/signals.md`.

**Do NOT log:** one-off corrections that don't generalise; preferences
already captured in a skill; tool bugs unrelated to methodology;
observations that would need proprietary client information to be useful
in an open-source skill (unless an internal skill is the right home). The
generalisability test, when unsure: would this still make sense in another
project, and for another task using the same skill? Does it name a missing
rule, step or principle rather than fix this task? Is it likely to recur?
Mostly no → task context, not an observation. Before minting a
`proposes_skill` name, check the existing candidates and reuse a fitting
one — independently logged proposals for one skill rarely share a name.

**Validate the target at write time.** A name in `skill:` must be a skill
that exists now; if it doesn't, the observation proposes a skill instead.
Checking is cheap at write time and expensive forty entries later.

**Check the target's siblings at write time, and record that you did.**
Libraries accumulate *families* — several skills implementing one
methodology for different tools, one structure for different subjects, one
companion pattern for different base skills. An insight found while using
one member usually applies to the rest, but nothing in the workflow asks,
so `skill:` collapses to a single entry and the family silently diverges.
Before writing, resolve the target against the family registry
(`skill-observations/skill-families.md`; spec, coherence models and the
no-registry fallback in `references/observation-log.md`), and for each
sibling either add it to `skill:` or state in the body why it does not
apply. Fast test: **could this sentence survive having the tool's or
subject's name removed?** If yes it belongs to every sibling — and a rule
that declares itself generic inside one artefact ("this applies to any
file-writing script, not just X") is the cheapest possible propagation
signal, so treat that phrasing as an automatic multi-skill flag. Then
record the outcome in the mandatory `siblings_checked:` frontmatter field,
including the verdict "checked — instance-specific, no propagation": a
one-entry `skill:` list is byte-identical whether the siblings were
evaluated or never considered, and only the recorded field makes the
*absence* of the judgement visible to a review or a drift audit.

## How to Log

Write the observation file **silently, within the same turn or the next** —
never batch mentally for later; the act of writing is the enforcement
mechanism.

**Mandatory checkpoint after every 3rd completed todo item.** After marking
the 3rd, 6th, 9th (etc.) item complete, you must **write to disk** — not
merely ask yourself whether anything is pending. Either write any pending
observation files, or, if genuinely none have accumulated, append a
one-line `no observations` acknowledgement to
`skill-observations/checkpoints.log`. The required action is a concrete
write; a remembered "ask whether" is not enforcement. The count need not be
precise; roughly every third completion is the rule. (Exception: where the
workspace is a shared hosted document store in which every write is priced
and invalidates other sessions' context, suppress the empty marker and
keep only the check — see `references/environments.md`.)

**A denied or failed write is not a read-only log.** Retry once before
concluding the workspace is unwritable, and try a second tool that reaches
the same path — a permission classifier can deny one interface while
allowing another, and consecutive denials from a probabilistic gatekeeper
are noise, not a wall. Report "failed N times", never "cannot be done",
unless retries and alternate interfaces are actually exhausted; otherwise
observations are silently lost for the rest of the session.

**Deliverable-event flush.** Whenever you present or render a major
deliverable — a file handed to the user, a deck or PDF render, a staged
skill file — or complete a task/todo batch, write any pending observation
files at that moment, before moving on. These checkpoints already involve a
tool call; piggy-backing the flush onto them makes the write a side effect
of work you were doing anyway. (Why both checkpoints are writes rather than
questions: `references/observation-log.md`.)

**Two gaps this pairing still leaves — both observed across full working days
in which nothing was logged at all.**

1. *A session can contain no todo items whatsoever.* The 3rd-completion
   checkpoint is bound to ONE tool; work driven entirely through direct tool
   calls and shell commands never trips it. It is armed only in sessions that
   happen to use todos, so it is not a safety net that is always present. When
   a session runs without them, the deliverable flush is the only enforcement
   left and must be applied deliberately.
2. *"Is this a major deliverable?" is a self-assessment, and self-assessment is
   what fails under load.* Prefer triggers unmistakable in the tool record over
   ones needing a judgement call. In particular, treat any **project-completing
   command** — a deploy, release, publish, or push — as a flush point: it is a
   concrete tool call, as hard a trigger as a completed todo, and it reliably
   marks the end of a unit of work where insights have accumulated.


 succeeded in 0ms:
---
name: quality_check
description: Platform-neutral quality gatekeeper and orchestrator that discovers project-registered providers from .agents/quality/check_quality.json, validates versioned contracts, aggregates verdicts (FAIL > BLOCKED > PASS), and renders immutable SHA-bound executive reports.
---

# Platform-Neutral Quality Check Orchestrator

## Overview

You are the Master Quality Orchestrator and Governance Gatekeeper. Your role is platform-neutral: you do not embed
ecosystem-specific compilers, testing tools, or heuristics. Instead, you act as the composition root for project quality,
discovering registered capability providers via dependency injection, fanning out execution across all selected providers,
validating versioned contracts, and synthesizing a single deterministic Gate 4 verdict bound to an immutable commit SHA.

Execution is strictly read-only: quality certification verifies existing code and never mutates source files or applies
auto-fix scripts during verification.

## Architecture and Execution Sequence

```mermaid
flowchart TD
    CALLER["Caller supplies profile, base ref, and target SHA"] --> NORMALIZE["Step 0: Normalize request and verify repository SHA"]
    NORMALIZE --> REGISTRY["Step 1: Load .agents/quality/check_quality.json"]
    REGISTRY --> VALIDATE["Step 2: Validate registry and select providers"]
    VALIDATE --> FANOUT["Step 3: Fan out invocation across all selected providers"]
    FANOUT --> HEAD_CHECK["Step 4: Verify finished repository HEAD matches initial SHA"]
    HEAD_CHECK --> CONTRACT_CHECK["Step 5: Validate provider results and reconcile plan"]
    CONTRACT_CHECK --> REDUCE["Step 6: Aggregate statuses and render executive report"]
    REDUCE --> VERDICT{"Overall status"}
    VERDICT -->|"PASS"| LGTM["Render Gate 4 LGTM for verified SHA"]
    VERDICT -->|"FAIL"| REJECT_FAIL["Report product defects"]
    VERDICT -->|"BLOCKED"| REJECT_BLOCKED["Report infrastructure blockers"]
```

## Step-by-Step Orchestration Workflow

### Step 0: Input Normalization and Invocation Contract

Normalize caller parameters:
- `profile`: Defaults to `pr` for direct interactive invocations. Formal lifecycle callers (`dev-implementation`, `dev-lifecycle`) must pass explicit profile (`epic`, `scheduled`, `release`).
- `base_ref`: Branch or ref used for blast radius, changed-file scope, and impact analysis (e.g. `main`, `develop`).
- `repository_sha`: The 40-character commit SHA to certify. If omitted, resolve immediately using `git rev-parse HEAD`.

Construct the immutable invocation payload:

```json
{
  "contract_version": 1,
  "profile": "<profile>",
  "base_ref": "<base_ref>",
  "repository_sha": "<sha>"
}
```

Validate the invocation using [validate_quality_contract.py](resources/scripts/validate_quality_contract.py). If invocation parameters are invalid, halt immediately with status `BLOCKED`.

### Step 1: Project Registry Loading

Load the project quality manifest located at `.agents/quality/check_quality.json` from the repository root:

```bash
python3 skills/quality_check/resources/scripts/validate_quality_contract.py registry .agents/quality/check_quality.json --profile "<profile>"
```

Fail-closed rules:
- If `.agents/quality/check_quality.json` is missing or unreadable: halt with status `BLOCKED`. Never attempt fallback platform detection.
- If the registry contains unknown fields, unsupported schema versions, duplicate provider IDs, or empty provider lists: halt with status `BLOCKED`.
- If no provider matches the requested profile: return `BLOCKED` with finding `empty_selection`.
- If a selected provider's skill is unresolvable in the active environment: halt with status `BLOCKED`.

### Step 2: Provider Invocation Fan-Out

For every provider selected by the registry for the requested profile:
1. Provide the identical immutable invocation payload, adding the provider's `provider_id` and `required` flag.
2. Invoke the provider skill (e.g. `d3nexus:rust-quality-check`).
3. Providers execute read-only checks matching their declared profile capabilities.
4. Collect one structured result document per provider.

Independent providers may run concurrently. Output ordering is never dependent on execution order.

### Step 3: Stale-Evidence and Final HEAD Verification

Before accepting provider evidence, verify current repository HEAD:

```bash
git rev-parse HEAD
```

If current HEAD differs from `repository_sha`, repository state drifted during execution. All collected evidence is rejected as stale, and the overall run returns `BLOCKED`.

### Step 4: Result Contract Validation and Plan Reconciliation

Reconcile collected provider results against the execution plan:

```bash
python3 skills/quality_check/resources/scripts/validate_quality_contract.py reconcile "<plan_json>" --results "<result_files...>"
```

Validation guarantees:
- Every result document matches [provider-result.schema.json](resources/schemas/provider-result.schema.json).
- Identity fields (`provider_id`, `profile`, `repository_sha`, `started_head`, `finished_head`) match the invocation.
- Missing results or duplicate results for a provider generate synthetic `BLOCKED` findings.
- Evidence references resolve cleanly to recorded evidence artifacts.

### Step 5: Deterministic Aggregation and Executive Report

Reduce validated results into a unified verdict:

```bash
python3 skills/quality_check/resources/scripts/aggregate_quality_results.py "<plan_json>" "<result_files...>" --markdown
```

Precedence policy:
$$\text{FAIL} > \text{BLOCKED} > \text{PASS}$$

1. **FAIL**: If any provider reported `FAIL`, the overall verdict is `FAIL`. All defects and blockers remain visible.
2. **BLOCKED**: If no failure occurred, but any required provider reported `BLOCKED` or failed reconciliation, the overall verdict is `BLOCKED`.
3. **PASS**: Granted if and only if every required provider passed.
4. **NOT_APPLICABLE**: An optional provider may be neutral if supported by applicability evidence. A required provider with only `NOT_APPLICABLE` checks is converted to `BLOCKED`.

### Step 6: Gate 4 Certification

Only an aggregated verdict of **PASS** bound to the candidate commit SHA qualifies for Gate 4 `🟢 LGTM`. If the verdict is `FAIL` or `BLOCKED`, render the complete executive report detailing all blockers and warnings, and stop.

## Reference Contracts and Resources

- [Provider Registry Contract](references/provider-registry-contract.md): Format and rules for `.agents/quality/check_quality.json`.
- [Provider Result Contract](references/provider-result-contract.md): Schema and constraints for provider result documents.
- [Result Aggregation Contract](references/aggregation-contract.md): Deterministic precedence and status reduction model.
- [Executive Report Format](references/executive-report-format.md): Layout specification for pull request and Gate 4 reports.
- [Registry Schema](resources/schemas/check-quality.schema.json): Machine-readable JSON Schema for project registries.
- [Result Schema](resources/schemas/provider-result.schema.json): Machine-readable JSON Schema for provider results.
- [Contract Validator](resources/scripts/validate_quality_contract.py): Standard-library validator script and CLI.
- [Aggregation Engine](resources/scripts/aggregate_quality_results.py): Result aggregation and markdown report engine.
- [Acceptance Suite](resources/scripts/test_quality_provider_acceptance.py): End-to-end multi-provider acceptance test suite.

exec
/bin/zsh -lc "rg -n -i -C 2 'principal.review|external.review|Gate 4 Review Choice|run_external_review|check_epic_readiness|ai-agent-tools' /Users/danhdueexoictif/.codex/memories/MEMORY.md | head -n 220" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
67-- Do not add chunks to accepted LRCLIB/song paths: it adds request/boundary/merge overhead when the correct optimization is to remove the LLM call. [Task 1]
68-
69:# Task Group: ai-agent-tools mechanical verification hardening and lightweight executor-contract amendment
70-
71-scope: Packaged mechanical-verification epic and design-only, platform-aware guardrails for dev-designer/handoff contracts; use to avoid overclaiming semantic enforcement.
72:applies_to: cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools; reuse_rule=reinspect current lifecycle tooling and provider semantics; the section-14 amendment is not runtime implementation.
73-
74-## Task 1: Package mechanical verification and lifecycle slimming epic, success
--
76-### rollout_summary_files
77-
78:- rollout_summaries/2026-10-19T06-48-08-xLHz-lightweight_dev_designer_executor_contract_amendment_analysi.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/19/rollout-2026-10-19T13-48-08-01a152ea-e567-7251-b428-6f5047d1cb51.jsonl, updated_at=2026-10-19T12:02:45+00:00, thread_id=01a152ea-e567-7251-b428-6f5047d1cb51, packaged and validated; Stage 3 not entered)
79-
80-### keywords
--
86-### rollout_summary_files
87-
88:- rollout_summaries/2026-10-19T06-48-08-xLHz-lightweight_dev_designer_executor_contract_amendment_analysi.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/19/rollout-2026-10-19T13-48-08-01a152ea-e567-7251-b428-6f5047d1cb51.jsonl, updated_at=2026-10-19T12:02:45+00:00, thread_id=01a152ea-e567-7251-b428-6f5047d1cb51, design amendment only; no runtime implementation/commit shown)
89-
90-### keywords
--
158-- Green structural validators did not catch semantic package errors. Before trusting them, inspect existing repository anchors and ownership; parser failures on new paths/DoD need parser-compatible recursive Allowed-file globs, explicit scope notes, resolved dependency state, and each DoD line ending in `(V<n>)` or `(Gate 5)`. Preserve unrelated `reports/` and `research_notes/`; stage only epic-owned files. [Task 2]
159-
160:# Task Group: ai-agent-tools Gate 4 Review Choice loop and external-review diagnostics
161-
162:scope: Verified lifecycle state-machine update and streamed external-review precondition reporting.
163:applies_to: cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools; reuse_rule=inspect current lifecycle rules/skills and candidate SHA before reuse; flow is repository policy, not a generic shortcut around gates.
164-
165-## Task 1: Reposition Review Choice into a Gate 4 loop, success
--
167-### rollout_summary_files
168-
169:- rollout_summaries/2026-10-18T10-39-52-b3XU-gate4_review_choice_loop_and_external_review_streaming.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/18/rollout-2026-10-18T17-39-52-01a14e98-b2b9-7043-9d17-65dd8df4be46.jsonl, updated_at=2026-10-18T15:23:36+00:00, thread_id=01a14e98-b2b9-7043-9d17-65dd8df4be46, committed and fully verified)
170-
171-### keywords
--
173-- Gate 4, Review Choice, Cross-model review, Gate 5, SHA-bound, rules/CRITICAL_RULES.md, test_verifiable_handoff_text.py, df9f67af7c1f7fecd3b4a9768c0863d035ed3088
174-
175:## Task 2: Add realtime ANSI pre-check output to external review, success
176-
177-### rollout_summary_files
178-
179:- rollout_summaries/2026-10-18T10-39-52-b3XU-gate4_review_choice_loop_and_external_review_streaming.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/18/rollout-2026-10-18T17-39-52-01a14e98-b2b9-7043-9d17-65dd8df4be46.jsonl, updated_at=2026-10-18T15:23:36+00:00, thread_id=01a14e98-b2b9-7043-9d17-65dd8df4be46, 31 targeted tests and full verification passed)
180-
181-### keywords
182-
183:- run_external_review.py, run_gate, PreconditionFailedError, [PRECONDITION BLOCKED], ANSI, flush=True, audit_epic.py, check_bdd_traceability.py, scripts/verify.sh, android-ui-audit
184-
185-## User preferences
186-
187:- The user explicitly corrected the lifecycle sequence: “Gate 4 => Review Choice”, then “Finish” or “Cross model review”, and “Sau bước này chạy lại Gate 4 ... Loop cho tới khi finish.” -> preserve this order for similar ai-agent-tools lifecycle work. [Task 1]
188-- After verification, the user asked “Commit and finish all tasks.” -> commit locally when requested, but do not push without explicit permission. [Task 1]
189-
--
193-- The policy update touched `rules/CRITICAL_RULES.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-implementation/SKILL.md`, bilingual lifecycle docs, lifecycle-selection docs, and `scripts/test_verifiable_handoff_text.py`; commit `df9f67af7c1f7fecd3b4a9768c0863d035ed3088` is `[REVIEW_WORKFLOW] Loop review choice through Gate 4`. [Task 1]
194-- `run_gate()` emits `[Pre-check]`, `PASS`, `FAILED`, or `TIMEOUT` to stderr with `flush=True`. `PreconditionFailedError` holds `gate`, `reason`, and `details`; its banner shows the final 25 detail lines and confirms the selected CLI was not invoked. [Task 2]
195:- Route `audit_epic.py`, declared Integration commands, and `check_bdd_traceability.py` through `run_gate()` while retaining captured output in the facts bundle. `run_external_review.py` does not directly invoke `android-ui-audit`; that is only indirect through the quality-provider registry. Targeted suite passed 31 tests and `scripts/verify.sh` reported `PASS — safe to publish`; worktree was clean on `main`, with no push. [Task 2]
196-
197-## Failures and how to do differently
--
499-- Upstream accepted malformed/contradictory PASS, low coverage, stale SHA/invalid capability. Simulated helper insufficient; certify production path. Commit/SHA not evidenced: stage scope, commit, verify SHA/clean status. [Task 1]
500-
501:# Task Group: ai-agent-tools skill discovery and safe branch integration
502-
503-scope: Local skill lookup, lifecycle routing, released rebase/land workflow.
504:applies_to: cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools; reuse_rule=inspect current SKILL.md and installed release.
505-
506-## Task 1: Discover skills, resolve prefixes, and release safe integration
507-### rollout_summary_files
508:- rollout_summaries/2026-10-11T06-52-24-wArW-skill_catalog_and_dev_lifecycle_discovery.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/11/rollout-2026-10-11T13-52-24-01a129bb-ef74-7833-80a5-ffa27599e2a4.jsonl, updated_at=2026-10-11T06:54:24+00:00, thread_id=01a129bb-ef74-7833-80a5-ffa27599e2a4, prefix routing)
509:- rollout_summaries/2026-10-11T06-26-43-i2zP-discover_available_skills.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/11/rollout-2026-10-11T13-26-43-01a129a4-6a65-7ee3-8ec5-411bb148e0b5.jsonl, updated_at=2026-10-11T06:27:03+00:00, thread_id=01a129a4-6a65-7ee3-8ec5-411bb148e0b5, catalog)
510:- rollout_summaries/2026-10-09T09-41-49-wx3v-safe_rebase_branch_integration_release_1_5_0.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/09/rollout-2026-10-09T16-41-49-01a1200a-5229-7423-9c53-3b5ae8fa1fdd.jsonl, updated_at=2026-10-09T02:55:30+00:00, thread_id=01a1200a-5229-7423-9c53-3b5ae8fa1fdd, released 1.5.0)
511-### keywords
512-- skills/*/SKILL.md, find-skills, d3nexus:dev-lifecycle, dev-li, quality_check, integrate_branch.py, rebase.updateRefs, release.sh

exec
/bin/zsh -lc "sed -n '160,200p' /Users/danhdueexoictif/.codex/memories/MEMORY.md && sed -n '1,220p' /Users/danhdueexoictif/.codex/memories/rollout_summaries/2026-10-18T10-39-52-b3XU-gate4_review_choice_loop_and_external_review_streaming.md" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
# Task Group: ai-agent-tools Gate 4 Review Choice loop and external-review diagnostics

scope: Verified lifecycle state-machine update and streamed external-review precondition reporting.
applies_to: cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools; reuse_rule=inspect current lifecycle rules/skills and candidate SHA before reuse; flow is repository policy, not a generic shortcut around gates.

## Task 1: Reposition Review Choice into a Gate 4 loop, success

### rollout_summary_files

- rollout_summaries/2026-10-18T10-39-52-b3XU-gate4_review_choice_loop_and_external_review_streaming.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/18/rollout-2026-10-18T17-39-52-01a14e98-b2b9-7043-9d17-65dd8df4be46.jsonl, updated_at=2026-10-18T15:23:36+00:00, thread_id=01a14e98-b2b9-7043-9d17-65dd8df4be46, committed and fully verified)

### keywords

- Gate 4, Review Choice, Cross-model review, Gate 5, SHA-bound, rules/CRITICAL_RULES.md, test_verifiable_handoff_text.py, df9f67af7c1f7fecd3b4a9768c0863d035ed3088

## Task 2: Add realtime ANSI pre-check output to external review, success

### rollout_summary_files

- rollout_summaries/2026-10-18T10-39-52-b3XU-gate4_review_choice_loop_and_external_review_streaming.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/18/rollout-2026-10-18T17-39-52-01a14e98-b2b9-7043-9d17-65dd8df4be46.jsonl, updated_at=2026-10-18T15:23:36+00:00, thread_id=01a14e98-b2b9-7043-9d17-65dd8df4be46, 31 targeted tests and full verification passed)

### keywords

- run_external_review.py, run_gate, PreconditionFailedError, [PRECONDITION BLOCKED], ANSI, flush=True, audit_epic.py, check_bdd_traceability.py, scripts/verify.sh, android-ui-audit

## User preferences

- The user explicitly corrected the lifecycle sequence: “Gate 4 => Review Choice”, then “Finish” or “Cross model review”, and “Sau bước này chạy lại Gate 4 ... Loop cho tới khi finish.” -> preserve this order for similar ai-agent-tools lifecycle work. [Task 1]
- After verification, the user asked “Commit and finish all tasks.” -> commit locally when requested, but do not push without explicit permission. [Task 1]

## Reusable knowledge

- Enforced invariant: `Gate 4 PASS -> Review Choice; Finish -> Gate 5; Cross-model review -> Gate 4 in full`. A review round, decision, Fix commit, Gate 5-requested change, cross-model CLI failure, or timeout that changes/reassesses the candidate requires full Gate 4 before another Review Choice. Gate 4 is SHA-bound. [Task 1]
- The policy update touched `rules/CRITICAL_RULES.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-implementation/SKILL.md`, bilingual lifecycle docs, lifecycle-selection docs, and `scripts/test_verifiable_handoff_text.py`; commit `df9f67af7c1f7fecd3b4a9768c0863d035ed3088` is `[REVIEW_WORKFLOW] Loop review choice through Gate 4`. [Task 1]
- `run_gate()` emits `[Pre-check]`, `PASS`, `FAILED`, or `TIMEOUT` to stderr with `flush=True`. `PreconditionFailedError` holds `gate`, `reason`, and `details`; its banner shows the final 25 detail lines and confirms the selected CLI was not invoked. [Task 2]
- Route `audit_epic.py`, declared Integration commands, and `check_bdd_traceability.py` through `run_gate()` while retaining captured output in the facts bundle. `run_external_review.py` does not directly invoke `android-ui-audit`; that is only indirect through the quality-provider registry. Targeted suite passed 31 tests and `scripts/verify.sh` reported `PASS — safe to publish`; worktree was clean on `main`, with no push. [Task 2]

## Failures and how to do differently

- A first regression failed because normative files still said Review Choice occurred before Gate 4. Do not make a flowchart-only edit: synchronize rules, both skills, diagrams, English/Vietnamese docs, lifecycle-selection docs, and negative assertions. [Task 1]

thread_id: 01a14e98-b2b9-7043-9d17-65dd8df4be46
updated_at: 2026-10-18T15:23:36+00:00
rollout_path: /Users/danhdueexoictif/.codex/sessions/2026/10/18/rollout-2026-10-18T17-39-52-01a14e98-b2b9-7043-9d17-65dd8df4be46.jsonl
cwd: /Users/danhdueexoictif/AllProjects/ai-agent-tools
git_branch: main

# Review workflow loop and realtime external-review diagnostics implemented

Rollout context: In `/Users/danhdueexoictif/AllProjects/ai-agent-tools`, the user requested (in Vietnamese) both a workflow change and an enhancement to `run_external_review.py`. The user clarified the desired state machine: `Gate 4 → Review Choice`; **Finish → Gate 5**, while **Cross-model review → record round/findings → rerun full Gate 4 → Review Choice**, repeating until Finish.

## Task 1: Reposition Review Choice into a Gate 4 loop

Outcome: success

Preference signals:
- The user explicitly corrected the initial interpretation: “I. Gate 4 => Review Choice: 1. Finish. 2. Cross model review. II. Sau bước này chạy lại Gate 4. => Loop cho tới khi finish.” Future lifecycle changes should preserve this exact ordering and loop, rather than placing Review Choice before Gate 4.
- The user then requested “Commit and finish all tasks.” This indicates that once verification is complete, they prefer the changes committed locally and the workflow finished without pushing unless explicitly requested.

Key steps:
- Added the invariant `Gate 4 PASS → Review Choice; Finish → Gate 5; Cross-model review → Gate 4 in full` to `skills/dev-lifecycle/SKILL.md` and `skills/dev-implementation/SKILL.md`.
- Updated `rules/CRITICAL_RULES.md`, English/Vietnamese lifecycle docs, and lifecycle-selection docs so review rounds, decisions, Fix commits, and Gate 5 changes invalidate the prior SHA-bound Gate 4 result.
- Added regression assertions in `scripts/test_verifiable_handoff_text.py` for the new edges and for removal of old “before Gate 4” wording.
- Corrected a documentation lint issue in `rules/CRITICAL_RULES.md` by tagging a fenced block as `text`.

Reusable knowledge:
- Gate 4 is SHA-bound. Any review round, review decision, Fix commit, or Gate 5-requested change that changes the candidate SHA requires a complete Gate 4 rerun.
- A cross-model CLI failure/timeout or recorded round also returns to full Gate 4 before another Review Choice; it does not jump directly to Gate 5 or another choice.

Failures and how to do differently:
- The first regression test intentionally failed because the repository still encoded Review Choice before Gate 4. Updating only the flowchart was insufficient; normative rules, both skills, bilingual docs, lifecycle-selection docs, and negative assertions all needed alignment.

References:
- Commit: `df9f67af7c1f7fecd3b4a9768c0863d035ed3088`
- Commit message: `[REVIEW_WORKFLOW] Loop review choice through Gate 4`
- Core flow edges: `EXEC --> G4`, `G4 -- yes --> RC`, `RC -- Finish --> REVIEW`, `RC -- Cross-model review --> XR`, `XR -- round recorded --> G4`.

## Task 2: Add realtime ANSI pre-check output to external review

Outcome: success

Key steps:
- Enhanced `skills/dev-implementation/resources/scripts/run_external_review.py` with ANSI color helpers, `run_gate()`, flushed progress output, structured `PreconditionFailedError`, and a blocking banner showing the failed gate, reason, last 25 detail lines, and confirmation that the CLI was not invoked.
- Routed audit, integration, and BDD traceability checks through `run_gate()` while preserving their captured output in the facts bundle.
- Added/updated regression tests for PASS, failure, timeout, flushed output, and banner behavior.

Reusable knowledge:
- The script directly runs `audit_epic.py`, declared Integration commands, and `check_bdd_traceability.py`; `android-ui-audit` is not invoked directly by this script and may only be involved indirectly through the quality provider registry.

References:
- `run_gate()` streams to `stderr` with `flush=True`.
- Blocking banner includes `[PRECONDITION BLOCKED]` and `<CLI> CLI WAS NOT INVOKED (0 CREDITS USED)`.
- Targeted suite: `31` tests passed; final full verification also passed.

Final verification:
- `scripts/verify.sh`: `PASS — safe to publish`.
- Worktree clean on `main`; no push performed.

codex
I’ve anchored the review to the required lifecycle invariant: Gate 4 is SHA-bound, and any recorded review round or resulting decision/fix returns through full Gate 4 before Review Choice. Next I’m verifying candidate identity, task ownership, and every artifact against the committed snapshot—not the mutable worktree view.
exec
/bin/zsh -lc 'git rev-parse HEAD main c09cb95593c5908098462a0a2963f1a300d9efcb && git merge-base main c09cb95593c5908098462a0a2963f1a300d9efcb && git status --short && git log --oneline --decorate --no-merges main..c09cb95593c5908098462a0a2963f1a300d9efcb && git diff --name-status main...c09cb95593c5908098462a0a2963f1a300d9efcb' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 9975ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-jmgaq3O2' (errno=Operation not permitted)
2026-10-23 17:44:45.434 xcodebuild[25943:2215533]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:44:45.714 xcodebuild[25943:2215531] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-aPM9L9z6' (errno=Operation not permitted)
2026-10-23 17:44:46.263 xcodebuild[25947:2215562]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:44:46.391 xcodebuild[25947:2215560] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
c09cb95593c5908098462a0a2963f1a300d9efcb
8f7d5cbe38ac9d0424abf94efad12f1f994d6b51
c09cb95593c5908098462a0a2963f1a300d9efcb
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-ez9wBDGN' (errno=Operation not permitted)
2026-10-23 17:44:47.475 xcodebuild[25952:2215616]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:44:47.635 xcodebuild[25952:2215614] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-VqUjQZKb' (errno=Operation not permitted)
2026-10-23 17:44:48.156 xcodebuild[25964:2215785]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:44:48.286 xcodebuild[25964:2215779] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
8f7d5cbe38ac9d0424abf94efad12f1f994d6b51
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-sxBjYJk7' (errno=Operation not permitted)
2026-10-23 17:44:49.367 xcodebuild[25972:2215855]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:44:49.498 xcodebuild[25972:2215853] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-x9cAreJP' (errno=Operation not permitted)
2026-10-23 17:44:49.969 xcodebuild[25976:2215870]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:44:50.109 xcodebuild[25976:2215869] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-5UYsAEHa' (errno=Operation not permitted)
2026-10-23 17:44:51.255 xcodebuild[25984:2215912]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:44:51.389 xcodebuild[25984:2215911] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-vIV3kIUv' (errno=Operation not permitted)
2026-10-23 17:44:51.919 xcodebuild[25986:2215930]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:44:52.054 xcodebuild[25986:2215927] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
c09cb95 (HEAD -> epic/principal_review) [PRINCIPAL_REVIEW] Task 5: Principal review choice and acceptance
a0e1537 [PRINCIPAL_REVIEW] Task 3: Principal review mode in the runner
7b43036 [PRINCIPAL_REVIEW] Task 2: Readiness grounding, Gate 4 coverage and baseline
97fcbe4 [PRINCIPAL_REVIEW] Task 4: Scope epic status sync to its own worktrees
019190e [PRINCIPAL_REVIEW] Task 1: Readiness check core
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-vtIdy9KJ' (errno=Operation not permitted)
2026-10-23 17:44:53.184 xcodebuild[26000:2216040]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:44:53.318 xcodebuild[26000:2216038] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-nPl4veF8' (errno=Operation not permitted)
2026-10-23 17:44:53.817 xcodebuild[26003:2216071]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:44:53.947 xcodebuild[26003:2216070] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
A	.devtool/epic/principal_review/evidence/task_1_readiness_check_core.json
A	.devtool/epic/principal_review/evidence/task_2_readiness_grounding_and_baseline.json
A	.devtool/epic/principal_review/evidence/task_3_principal_review_runner_mode.json
A	.devtool/epic/principal_review/evidence/task_4_epic_status_sync_scope.json
A	.devtool/epic/principal_review/evidence/task_5_principal_review_choice_and_acceptance.json
M	.devtool/epic/principal_review/principal_review.en.md
M	.devtool/epic/principal_review/principal_review.vi.md
M	.devtool/epic/principal_review/task_1_readiness_check_core.md
M	.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md
M	.devtool/epic/principal_review/task_3_principal_review_runner_mode.md
M	.devtool/epic/principal_review/task_4_epic_status_sync_scope.md
M	.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md
R099	.devtool/features/task_1_readiness_check_core.md	.devtool/features/done/task_1_readiness_check_core.md
R099	.devtool/features/task_2_readiness_grounding_and_baseline.md	.devtool/features/done/task_2_readiness_grounding_and_baseline.md
R099	.devtool/features/task_3_principal_review_runner_mode.md	.devtool/features/done/task_3_principal_review_runner_mode.md
R098	.devtool/features/task_4_epic_status_sync_scope.md	.devtool/features/done/task_4_epic_status_sync_scope.md
R099	.devtool/features/task_5_principal_review_choice_and_acceptance.md	.devtool/features/done/task_5_principal_review_choice_and_acceptance.md
M	docs/lifecycles.en.md
M	docs/lifecycles.vi.md
M	scripts/test_lifecycle_document_contract.py
M	scripts/verify.sh
M	skills/dev-implementation/SKILL.md
A	skills/dev-implementation/references/principal-review-prompt.md
A	skills/dev-implementation/references/principal-review-rules.md
A	skills/dev-implementation/resources/scripts/check_epic_readiness.py
M	skills/dev-implementation/resources/scripts/run_external_review.py
M	skills/dev-implementation/resources/scripts/sync_task_status.py
A	skills/dev-implementation/resources/scripts/test_check_epic_readiness.py
M	skills/dev-implementation/resources/scripts/test_run_external_review.py
M	skills/dev-implementation/resources/scripts/test_sync_task_status.py
M	skills/dev-lifecycle/SKILL.md
M	skills/dev-lifecycle/references/handoff-template.md
A	skills/dev-lifecycle/references/principal-review.md

exec
/bin/zsh -lc "wc -l .devtool/epic/principal_review/2026-10-22-principal-review-design.en.md .devtool/epic/principal_review/2026-10-22-principal-review-design.vi.md .devtool/epic/principal_review/handoff.md .devtool/epic/principal_review/principal_review.en.md .devtool/epic/principal_review/principal_review.vi.md .devtool/epic/principal_review/bdd_scenarios.en.md .devtool/epic/principal_review/task_*.md .devtool/epic/principal_review/evidence/*.json && rg -n '"'^(#|##|###|'"\\| V[0-9]|- \\[.|Status:|status:|Decision|Definition of Done|Verification|Allowed|Dependencies|Integration|Gate 5)' .devtool/epic/principal_review/{2026-10-22-principal-review-design.en.md,handoff.md,principal_review.en.md,bdd_scenarios.en.md,task_*.md}" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
     257 .devtool/epic/principal_review/2026-10-22-principal-review-design.en.md
     252 .devtool/epic/principal_review/2026-10-22-principal-review-design.vi.md
      86 .devtool/epic/principal_review/handoff.md
     395 .devtool/epic/principal_review/principal_review.en.md
     395 .devtool/epic/principal_review/principal_review.vi.md
     302 .devtool/epic/principal_review/bdd_scenarios.en.md
     211 .devtool/epic/principal_review/task_1_readiness_check_core.md
     161 .devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md
     214 .devtool/epic/principal_review/task_3_principal_review_runner_mode.md
     139 .devtool/epic/principal_review/task_4_epic_status_sync_scope.md
     186 .devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md
     199 .devtool/epic/principal_review/evidence/task_1_readiness_check_core.json
     219 .devtool/epic/principal_review/evidence/task_2_readiness_grounding_and_baseline.json
     227 .devtool/epic/principal_review/evidence/task_3_principal_review_runner_mode.json
     215 .devtool/epic/principal_review/evidence/task_4_epic_status_sync_scope.json
     442 .devtool/epic/principal_review/evidence/task_5_principal_review_choice_and_acceptance.json
    3900 total
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:3:status: "done"
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:15:# Task 4: Scope Epic Status Sync to Its Own Worktrees
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:19:## Requirement Analysis
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:35:## Files
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:37:Allowed files:
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:47:## Design Rationale
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:57:## Impact Analysis & Blast Radius
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:65:### BDD SCENARIOS
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:83:## Verification
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:87:| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_sync_task_status.py -k EpicCheckoutRootsTests` | exit 1; contains "FAILED" | — |
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:88:| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_sync_task_status.py` | exit 0; contains "OK" | — |
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:89:| V3 | GREEN | `python3 -m unittest scripts/test_lifecycle_signals.py` | exit 0; contains "OK" | — |
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:90:| V4 | GREEN | `python3 -m unittest scripts/test_verifiable_handoff.py` | exit 0; contains "OK" | — |
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:91:| V5 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/sync_task_status.py` | exit 0 | — |
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:92:| V6 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/sync_task_status.py` | exit 0 | — |
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:93:| V7 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_4.xml skills/dev-implementation/resources/scripts/test_sync_task_status.py scripts/test_lifecycle_signals.py` | exit 0; results build/test-results/task_4.xml | — |
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:95:## Stop and Report If
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:105:## Decisions Already Made
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:124:## Definition of Done
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:130:## Dependencies & Blockers
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:135:## References & Rollback
.devtool/epic/principal_review/task_4_epic_status_sync_scope.md:137:- [Epic HLD](principal_review.en.md), Module Contracts.
.devtool/epic/principal_review/handoff.md:1:# Handoff: principal_review
.devtool/epic/principal_review/handoff.md:3:## Table of Contents
.devtool/epic/principal_review/handoff.md:5:- [Status](#status)
.devtool/epic/principal_review/handoff.md:6:- [Identifiers](#identifiers)
.devtool/epic/principal_review/handoff.md:7:- [Read First](#read-first)
.devtool/epic/principal_review/handoff.md:8:- [Resume Prompt](#resume-prompt)
.devtool/epic/principal_review/handoff.md:9:- [Execution Guardrails for Receiving LLM](#execution-guardrails-for-receiving-llm)
.devtool/epic/principal_review/handoff.md:10:- [Open Notes](#open-notes)
.devtool/epic/principal_review/handoff.md:11:- [Rules for the Receiving Agent](#rules-for-the-receiving-agent)
.devtool/epic/principal_review/handoff.md:13:## Status
.devtool/epic/principal_review/handoff.md:21:## Identifiers
.devtool/epic/principal_review/handoff.md:30:## Read First
.devtool/epic/principal_review/handoff.md:36:## Resume Prompt
.devtool/epic/principal_review/handoff.md:46:## Execution Guardrails for Receiving LLM
.devtool/epic/principal_review/handoff.md:59:## Open Notes
.devtool/epic/principal_review/handoff.md:80:## Rules for the Receiving Agent
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:3:status: "done"
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:15:# Task 3: Principal Review Mode in the Runner
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:19:## Requirement Analysis
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:32:## Files
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:34:Allowed files:
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:49:## Design Rationale
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:60:## Impact Analysis & Blast Radius
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:68:### BDD SCENARIOS
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:130:## Verification
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:134:| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k PrincipalReviewTest` | exit 1; contains "FAILED" | — |
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:135:| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; contains "OK" | — |
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:136:| V3 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0; contains "OK" | — |
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:137:| V4 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/run_external_review.py` | exit 0 | — |
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:138:| V5 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/run_external_review.py` | exit 0 | — |
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:139:| V6 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-implementation/references/principal-review-prompt.md skills/dev-implementation/references/principal-review-rules.md` | exit 0 | — |
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:140:| V7 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_3.xml skills/dev-implementation/resources/scripts/test_run_external_review.py skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0; results build/test-results/task_3.xml | — |
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:142:## Stop and Report If
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:152:## Decisions Already Made
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:198:## Definition of Done
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:205:## Dependencies & Blockers
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:210:## References & Rollback
.devtool/epic/principal_review/task_3_principal_review_runner_mode.md:212:- [Epic HLD](principal_review.en.md), Module Contracts and Sequence Diagram.
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:3:status: "done"
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:15:# Task 5: Principal Review Choice in the Lifecycle, and Acceptance
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:19:## Requirement Analysis
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:37:## Files
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:39:Allowed files:
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:58:## Design Rationale
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:66:## Impact Analysis & Blast Radius
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:75:### BDD SCENARIOS
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:106:## Verification
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:110:| V1 | RED | `python3 -m unittest scripts/test_lifecycle_document_contract.py -k PrincipalReviewWorkflowTest` | exit 1; contains "FAILED" | — |
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:111:| V2 | GREEN | `python3 -m unittest scripts/test_lifecycle_document_contract.py` | exit 0; contains "OK" | — |
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:112:| V3 | GREEN | `python3 -m unittest scripts/test_lifecycle_signals.py` | exit 0; contains "OK" | — |
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:113:| V4 | GREEN | `python3 -m unittest scripts/test_verifiable_handoff_text.py` | exit 0; contains "OK" | — |
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:114:| V5 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc --require-bilingual docs/lifecycles.en.md docs/lifecycles.vi.md` | exit 0 | — |
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:115:| V6 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-lifecycle/SKILL.md skills/dev-implementation/SKILL.md skills/dev-lifecycle/references/principal-review.md skills/dev-lifecycle/references/handoff-template.md` | exit 0 | — |
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:116:| V7 | TIER-B | `ruff check scripts/test_lifecycle_document_contract.py` | exit 0 | — |
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:117:| V8 | TIER-B | `mypy --strict --follow-imports=silent scripts/test_lifecycle_document_contract.py` | exit 0 | — |
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:118:| V9 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:119:| V10 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_5.xml skills/dev-implementation/resources/scripts/test_check_epic_readiness.py skills/dev-implementation/resources/scripts/test_run_external_review.py skills/dev-implementation/resources/scripts/test_sync_task_status.py scripts/test_lifecycle_document_contract.py scripts/test_lifecycle_signals.py scripts/test_verifiable_handoff_text.py` | exit 0; results build/test-results/task_5.xml | — |
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:121:## Stop and Report If
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:132:## Decisions Already Made
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:167:## Definition of Done
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:176:## Dependencies & Blockers
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:182:## References & Rollback
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:184:- [Epic HLD](principal_review.en.md), Workflow text and Clarifications of the Spec.
.devtool/epic/principal_review/principal_review.en.md:1:# Principal Review High-Level Design
.devtool/epic/principal_review/principal_review.en.md:3:## Table of Contents
.devtool/epic/principal_review/principal_review.en.md:5:- [Meta Data](#meta-data)
.devtool/epic/principal_review/principal_review.en.md:6:- [Background](#background)
.devtool/epic/principal_review/principal_review.en.md:7:- [Goals and Non-Goals](#goals-and-non-goals)
.devtool/epic/principal_review/principal_review.en.md:8:- [Architecture and Technical Design](#architecture-and-technical-design)
.devtool/epic/principal_review/principal_review.en.md:9:- [Integration Test Plan and Boundary Matrix](#integration-test-plan-and-boundary-matrix)
.devtool/epic/principal_review/principal_review.en.md:10:- [Verification Environment](#verification-environment)
.devtool/epic/principal_review/principal_review.en.md:11:- [Comprehensive BDD Scenario Coverage](#comprehensive-bdd-scenario-coverage)
.devtool/epic/principal_review/principal_review.en.md:12:- [Rollout Strategy and Mitigation](#rollout-strategy-and-mitigation)
.devtool/epic/principal_review/principal_review.en.md:13:- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)
.devtool/epic/principal_review/principal_review.en.md:15:## Meta Data
.devtool/epic/principal_review/principal_review.en.md:23:## Background
.devtool/epic/principal_review/principal_review.en.md:41:## Goals and Non-Goals
.devtool/epic/principal_review/principal_review.en.md:43:### Goals
.devtool/epic/principal_review/principal_review.en.md:54:### Non-Goals
.devtool/epic/principal_review/principal_review.en.md:63:## Architecture and Technical Design
.devtool/epic/principal_review/principal_review.en.md:65:### High-Level Architecture
.devtool/epic/principal_review/principal_review.en.md:111:### Use Cases
.devtool/epic/principal_review/principal_review.en.md:137:### Sequence Diagram
.devtool/epic/principal_review/principal_review.en.md:173:### Module Contracts
.devtool/epic/principal_review/principal_review.en.md:175:#### `check_epic_readiness.py` (new)
.devtool/epic/principal_review/principal_review.en.md:231:#### `run_external_review.py` (changed)
.devtool/epic/principal_review/principal_review.en.md:256:#### Principal Review prompt and rules (new)
.devtool/epic/principal_review/principal_review.en.md:269:#### `sync_task_status.py` (changed)
.devtool/epic/principal_review/principal_review.en.md:283:#### Workflow text (changed)
.devtool/epic/principal_review/principal_review.en.md:298:### Clarifications of the Spec
.devtool/epic/principal_review/principal_review.en.md:310:### Shift-Left Impact Analysis
.devtool/epic/principal_review/principal_review.en.md:328:## Integration Test Plan and Boundary Matrix
.devtool/epic/principal_review/principal_review.en.md:330:Integration test roots: skills/dev-implementation/resources/scripts/, scripts/
.devtool/epic/principal_review/principal_review.en.md:334:Integration results: python3 scripts/run_unittest_junit.py --junitxml build/test-results/principal-review.xml skills/dev-implementation/resources/scripts/test_check_epic_readiness.py skills/dev-implementation/resources/scripts/test_run_external_review.py skills/dev-implementation/resources/scripts/test_sync_task_status.py scripts/test_lifecycle_document_contract.py scripts/test_lifecycle_signals.py scripts/test_verifiable_handoff_text.py -> build/test-results/principal-review.xml
.devtool/epic/principal_review/principal_review.en.md:348:## Verification Environment
.devtool/epic/principal_review/principal_review.en.md:360:## Comprehensive BDD Scenario Coverage
.devtool/epic/principal_review/principal_review.en.md:373:## Rollout Strategy and Mitigation
.devtool/epic/principal_review/principal_review.en.md:389:## Kanban Tasks Breakdown
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:3:status: "done"
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:15:# Task 2: Readiness Grounding, Gate 4 Coverage and Baseline
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:19:## Requirement Analysis
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:30:## Files
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:32:Allowed files:
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:41:## Design Rationale
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:50:## Impact Analysis & Blast Radius
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:58:### BDD SCENARIOS
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:98:## Verification
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:102:| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k ReadinessGroundingTest` | exit 1; contains "FAILED" | — |
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:103:| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` | exit 0; contains "OK" | — |
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:104:| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` | exit 0 | — |
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:105:| V4 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` | exit 0 | — |
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:106:| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` | exit 0; results build/test-results/task_2.xml | — |
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:108:## Stop and Report If
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:119:## Decisions Already Made
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:146:## Definition of Done
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:152:## Dependencies & Blockers
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:157:## References & Rollback
.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md:159:- [Epic HLD](principal_review.en.md), Module Contracts.
.devtool/epic/principal_review/bdd_scenarios.en.md:1:# Principal Review BDD Scenarios
.devtool/epic/principal_review/bdd_scenarios.en.md:3:## Table of Contents
.devtool/epic/principal_review/bdd_scenarios.en.md:5:- [Coverage Matrix](#coverage-matrix)
.devtool/epic/principal_review/bdd_scenarios.en.md:6:- [Use Case 1: Mechanical Readiness Check](#use-case-1-mechanical-readiness-check)
.devtool/epic/principal_review/bdd_scenarios.en.md:7:- [Use Case 2: Principal Review Round](#use-case-2-principal-review-round)
.devtool/epic/principal_review/bdd_scenarios.en.md:8:- [Use Case 3: Epic Status Sync Scope](#use-case-3-epic-status-sync-scope)
.devtool/epic/principal_review/bdd_scenarios.en.md:9:- [Use Case 4: Lifecycle Workflow](#use-case-4-lifecycle-workflow)
.devtool/epic/principal_review/bdd_scenarios.en.md:11:## Coverage Matrix
.devtool/epic/principal_review/bdd_scenarios.en.md:38:## Use Case 1: Mechanical Readiness Check
.devtool/epic/principal_review/bdd_scenarios.en.md:40:### PRV-HP-01: A Ready Epic Passes
.devtool/epic/principal_review/bdd_scenarios.en.md:52:### PRV-EC-01: Missing Symbol
.devtool/epic/principal_review/bdd_scenarios.en.md:64:### PRV-EC-02: Tier Drift
.devtool/epic/principal_review/bdd_scenarios.en.md:75:### PRV-EC-03: Uncovered Gate 4 Path
.devtool/epic/principal_review/bdd_scenarios.en.md:87:### PRV-EC-04: Mirror Drift
.devtool/epic/principal_review/bdd_scenarios.en.md:100:### PRV-EC-05: Metadata
.devtool/epic/principal_review/bdd_scenarios.en.md:115:### PRV-EC-06: Unknown Route
.devtool/epic/principal_review/bdd_scenarios.en.md:126:### PRV-FR-01: Baseline Failures
.devtool/epic/principal_review/bdd_scenarios.en.md:141:### PRV-FR-02: Failing Preflight Sub-check
.devtool/epic/principal_review/bdd_scenarios.en.md:153:## Use Case 2: Principal Review Round
.devtool/epic/principal_review/bdd_scenarios.en.md:155:### PRV-HP-02: A Principal Round Is Recorded
.devtool/epic/principal_review/bdd_scenarios.en.md:168:### PRV-HP-03: Findings With Proposed Edits
.devtool/epic/principal_review/bdd_scenarios.en.md:179:### PRV-ST-01: Decisions Gate Check
.devtool/epic/principal_review/bdd_scenarios.en.md:192:### PRV-ST-02: Triage Reads the Selected File
.devtool/epic/principal_review/bdd_scenarios.en.md:204:### PRV-AR-01: Rounds in Order
.devtool/epic/principal_review/bdd_scenarios.en.md:216:### PRV-FR-03: Readiness Blocks the CLI
.devtool/epic/principal_review/bdd_scenarios.en.md:228:### PRV-FR-04: Ollama Rejected
.devtool/epic/principal_review/bdd_scenarios.en.md:239:## Use Case 3: Epic Status Sync Scope
.devtool/epic/principal_review/bdd_scenarios.en.md:241:### PRV-HP-05: Own Worktree Updated
.devtool/epic/principal_review/bdd_scenarios.en.md:250:### PRV-FR-05: Other Epics Untouched
.devtool/epic/principal_review/bdd_scenarios.en.md:261:## Use Case 4: Lifecycle Workflow
.devtool/epic/principal_review/bdd_scenarios.en.md:263:### PRV-HP-04: Packaging Offers the Choice
.devtool/epic/principal_review/bdd_scenarios.en.md:274:### PRV-EC-07: Handoff Read First
.devtool/epic/principal_review/bdd_scenarios.en.md:283:### PRV-ST-03: The Loop Returns to Package
.devtool/epic/principal_review/bdd_scenarios.en.md:294:### PRV-ST-04: Gate 3 Stops on Undecided Findings
.devtool/epic/principal_review/task_1_readiness_check_core.md:3:status: "done"
.devtool/epic/principal_review/task_1_readiness_check_core.md:15:# Task 1: Readiness Check Core
.devtool/epic/principal_review/task_1_readiness_check_core.md:19:## Requirement Analysis
.devtool/epic/principal_review/task_1_readiness_check_core.md:34:## Files
.devtool/epic/principal_review/task_1_readiness_check_core.md:36:Allowed files:
.devtool/epic/principal_review/task_1_readiness_check_core.md:50:## Design Rationale
.devtool/epic/principal_review/task_1_readiness_check_core.md:58:## Impact Analysis & Blast Radius
.devtool/epic/principal_review/task_1_readiness_check_core.md:66:### BDD SCENARIOS
.devtool/epic/principal_review/task_1_readiness_check_core.md:115:## Verification
.devtool/epic/principal_review/task_1_readiness_check_core.md:119:| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k ReadinessCoreTest` | exit 1; contains "FAILED" | — |
.devtool/epic/principal_review/task_1_readiness_check_core.md:120:| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k ReadinessCoreTest` | exit 0; contains "OK" | — |
.devtool/epic/principal_review/task_1_readiness_check_core.md:121:| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` | exit 0 | — |
.devtool/epic/principal_review/task_1_readiness_check_core.md:122:| V4 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` | exit 0 | — |
.devtool/epic/principal_review/task_1_readiness_check_core.md:123:| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_1.xml skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` | exit 0; results build/test-results/task_1.xml | — |
.devtool/epic/principal_review/task_1_readiness_check_core.md:125:## Stop and Report If
.devtool/epic/principal_review/task_1_readiness_check_core.md:135:## Decisions Already Made
.devtool/epic/principal_review/task_1_readiness_check_core.md:196:## Definition of Done
.devtool/epic/principal_review/task_1_readiness_check_core.md:202:## Dependencies & Blockers
.devtool/epic/principal_review/task_1_readiness_check_core.md:207:## References & Rollback
.devtool/epic/principal_review/task_1_readiness_check_core.md:209:- [Epic HLD](principal_review.en.md), Module Contracts.
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:1:# Principal Review Design
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:9:## Table of Contents
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:11:- [1. Background](#1-background)
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:12:- [2. Goals and Non-Goals](#2-goals-and-non-goals)
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:13:- [3. Decisions](#3-decisions)
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:14:- [4. Flow](#4-flow)
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:15:- [5. Components](#5-components)
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:16:- [6. Principal Review Loop Procedure](#6-principal-review-loop-procedure)
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:17:- [7. Error Handling](#7-error-handling)
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:18:- [8. Testing](#8-testing)
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:19:- [9. Risks and Dependencies](#9-risks-and-dependencies)
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:20:- [10. Out of Scope](#10-out-of-scope)
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:22:## 1. Background
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:48:## 2. Goals and Non-Goals
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:50:### Goals
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:62:### Non-Goals
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:70:## 3. Decisions
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:88:## 4. Flow
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:110:## 5. Components
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:112:### 5.1 `check_epic_readiness.py`
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:138:### 5.2 `run_external_review.py --kind principal`
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:153:### 5.3 Principal Review prompt and rules
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:179:### 5.4 `dev-lifecycle`
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:186:### 5.5 `dev-implementation`
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:193:### 5.6 `sync_task_status.py epic`
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:198:### 5.7 Human documentation and template
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:203:## 6. Principal Review Loop Procedure
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:216:## 7. Error Handling
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:228:## 8. Testing
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:242:## 9. Risks and Dependencies
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:251:## 10. Out of Scope

exec
/bin/zsh -lc 'for f in .devtool/epic/principal_review/task_*.md; do echo "===== $f"; sed -n '"'1,45p' \""'$f"; sed -n '"'/### BDD SCENARIOS/,/## Verification/p' \""'$f"; sed -n '"'/## Decisions Already Made/,/## Definition of Done/p' \""'$f"; sed -n '"'/## Definition of Done/,/## Dependencies/p' \""'$f"; done' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
===== .devtool/epic/principal_review/task_1_readiness_check_core.md
---
id: "task_1_readiness_check_core"
status: "done"
priority: "high"
assignee: null
epic: "principal_review"
dueDate: null
created: "2026-10-22T09:10:00Z"
modified: "2026-10-23T09:22:42Z"
completedAt: "2026-10-23T09:22:42Z"
labels: ["readiness", "preflight", "cli"]
order: "a1"
---

# Task 1: Readiness Check Core

Epic: [principal_review](principal_review.en.md)

## Requirement Analysis

Create `check_epic_readiness.py`, the single command that later replaces the four packaging
preflight commands and gates every Principal Review round. This task builds the frame and the
structural checks:
- the `Context`, the `Finding` record, the ordered `CHECKS` table, the report and the exit codes;
- R1 (the existing preflight scripts and the document linter);
- R2 (task mirror parity);
- R3 (scenario parity between task copies and the canonical BDD file);
- R4 (tier tags);
- R7 and R7b (metadata).

R5, R6 and R8 get their names in `CHECKS` now, and Task 2 fills them. The test module also
provides the reusable fixture builder that Task 3 imports.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py` (new)
- `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/compute_execution_order.py` — prints `Scanned <n> task_*.md files; <m> matched epic '<slug>'; …`
- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` — `scenario_ids()`, `SCENARIO_LINE`, `FENCE`, the `plan` mode
- `skills/dev-implementation/resources/scripts/check_task_contract.py` — `--design` mode, and a valid task fixture in `test_check_task_contract.py`
- `skills/dev-implementation/resources/scripts/task_contract.py` — `section()`, `parse_allowed_files()`, `parse_verification()`, `parse_integration_results()`, `git_run()`
- `skills/dev-implementation/resources/scripts/sync_task_status.py` — `TASK_STATUSES`
### BDD SCENARIOS

Covers: PRV-HP-01, PRV-EC-02, PRV-EC-04, PRV-EC-05, PRV-FR-02

```gherkin
Scenario: [PRV-HP-01] [Tier C - Integration] A ready fixture epic passes every check
  Given a throwaway repository with epic "demo_epic" whose 2 tasks have epic "demo-epic", mirrors in .devtool/features/, canonical Gherkin copies, existing symbols, covered TIER-C paths and an approved spec
  When check_epic_readiness.py demo_epic runs
  Then the first line is "Epic: demo_epic (demo-epic), 2 tasks"
  And the output has the lines "R1 PASS" through "R7 PASS" in order, then "R8 SKIP"
  And the last line is "Result: 0 FAIL, 0 WARN — PASS"
  And the exit code is 0

Scenario: [PRV-EC-02] [Tier C - Integration] Tier drift fails R3 and a Tier B tag fails R4
  Given the PRV-HP-01 epic whose bdd_scenarios.en.md tags DEMO-HP-01 "[Tier B - Unit]" while task_1 copies it as "[Tier A - Unit]"
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R3 FAIL" containing "task_1" and "DEMO-HP-01"
  And a line starting "R4 FAIL" containing "DEMO-HP-01" and "Tier B - Unit"
  And the exit code is 1

Scenario: [PRV-EC-04] [Tier C - Integration] Mirror drift fails R2 and location-only link differences pass
  Given the PRV-HP-01 epic whose .devtool/features/task_1 mirror links "../epic/demo_epic/demo_epic.en.md" where the epic copy links "demo_epic.en.md"
  When check_epic_readiness.py demo_epic runs
  Then the output has the line "R2 PASS"
  When the mirror's Requirement Analysis gains the extra line "Stale sentence."
  And check_epic_readiness.py demo_epic runs again
  Then the output has a line starting "R2 FAIL" containing "task_1" and "Stale sentence."
  And the exit code is 1

Scenario: [PRV-EC-05] [Tier C - Integration] Packaged without a handoff fails R7 and a draft spec warns R7b
  Given the PRV-HP-01 epic whose HLD Status is "Packaged" and whose directory has no handoff.md
  And whose spec Status is "Draft, awaiting Gate 1 review"
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R7 FAIL" containing "handoff.md"
  And a line starting "R7b WARN" containing "Draft, awaiting Gate 1 review"
  And the exit code is 1
  When handoff.md is added with "- **Design commit**: `uncommitted`" and the spec Status stays a draft
  And check_epic_readiness.py demo_epic runs again
  Then the output has the line "R7 PASS" and the exit code is 0

Scenario: [PRV-FR-02] [Tier C - Integration] A failing preflight sub-check fails R1 by name
  Given the PRV-HP-01 epic whose bdd_scenarios.en.md adds DEMO-EC-09 covered by no task
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R1 FAIL" containing "check_bdd_traceability.py plan"
  And the exit code is 1
  When check_epic_readiness.py runs with a directory that does not exist
  Then the exit code is 2
```

## Verification
## Decisions Already Made

- **Frozen contract** (HLD, Module Contracts):
  ```python
  @dataclass(frozen=True)
  class Finding:
      check: str     # "R1" ... "R8", "R5b", "R7b"
      severity: str  # "FAIL" or "WARN"
      message: str

  CHECKS: tuple[tuple[str, Callable[[Context], list[Finding]]], ...]  # R1..R8 in order

  def load_context(root: Path, epic_dir: str) -> Context
  def run_checks(ctx: Context, *, baseline: bool = False, row_timeout: int = 600) -> list[Finding]
  def render_report(ctx: Context, findings: list[Finding]) -> str
  def main(argv: list[str] | None = None) -> int
  ```
  `Context` is a frozen dataclass holding:
  - `root`, `epic_dir` and `epic_slug` (the `epic:` value shared by the epic directory's tasks);
  - `hld_text`;
  - `tasks: dict[Path, str]` (every `.devtool/epic/<epic_dir>/task_*.md`);
  - `results: list[str]` (from `task_contract.parse_integration_results`);
  - `roots: list[str]` (the comma-separated `Integration test roots:` values);
  - `baseline: bool` and `row_timeout: int`.
- **CLI**: `check_epic_readiness.py <epic_dir> [--baseline] [--row-timeout 600]`. The root comes from `git rev-parse --show-toplevel` run in the current directory. Every subprocess runs with `cwd=root`.
- **Report**:
  - the first line is exactly `Epic: <epic_dir> (<epic_slug>), <N> tasks`;
  - then, in `CHECKS` order: `<check> PASS` for each of R1–R7 with no FAIL finding, and each finding as `<check> <severity> <message>`. R5b WARN lines follow R5, and R7b WARN lines follow R7;
  - R8 prints `R8 SKIP` without `--baseline`;
  - the last line is exactly `Result: <f> FAIL, <w> WARN — PASS` or `… — FAIL`.
- **Exit codes**: 0 when no finding is FAIL, 1 otherwise, 2 when `.devtool/epic/<epic_dir>/` or `<epic_dir>.en.md` is missing (one line on stderr naming the path).
- **R1**: run with `sys.executable`, in this order, each failure being one finding `R1 FAIL <script name and mode>: <last non-empty output line>`:
  1. `compute_execution_order.py <epic_slug>`. Its exit code must be 0, and the `<m>` in `<m> matched` must equal `len(ctx.tasks)`; a mismatch is `R1 FAIL task mirror count: <m> matched, <N> in the epic directory`.
  2. `check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks <the epic directory's task files>`.
  3. `check_task_contract.py --design --hld .devtool/epic/<epic_dir>/<epic_dir>.en.md --tasks <the same task files>`.
  4. `check_document.py --require-toc --require-bilingual` on every `*.en.md` and `*.vi.md` pair in the epic directory. Then `check_document.py --require-toc handoff.md` when it exists, then `check_document.py <task files>`. The linter path is `Path(__file__).resolve().parents[2] / "doc_quality_check/resources/scripts/check_document.py"`.
- **R2**:
  - for each task, the mirror is `.devtool/features/<name>` or else `.devtool/features/done/<name>`;
  - compare `mirror.replace(f"](../epic/{epic_dir}/", "](")` with the epic copy;
  - a missing mirror is `R2 FAIL <name>: no mirror in .devtool/features/`;
  - a difference is `R2 FAIL <name>: line <k>: <the epic copy's line>`, with `<k>` the first differing 1-based line.
- **R3**:
  - a block is a line matching `check_bdd_traceability.SCENARIO_LINE` inside a `gherkin` fence, plus the following lines up to the next scenario line, a blank line or the closing fence, each `rstrip()`-ed;
  - a task block whose identifier is in the canonical file but whose text differs is `R3 FAIL <task file>: <ID> differs from bdd_scenarios.en.md`;
  - different identifier sets between the `.en.md` and `.vi.md` BDD files give `R3 FAIL bdd_scenarios.vi.md: <ID> missing or extra`.
- **R4**: on every scenario line of `bdd_scenarios.en.md`, the bracketed tag right after the identifier must be exactly `Tier A - Unit` or `Tier C - Integration`. Otherwise the finding is `R4 FAIL <ID>: tier tag "<tag or none>"`.
- **R7** (FAIL):
  - Status starts with `Packaged` and there is no `handoff.md`;
  - `handoff.md` exists and Status starts with none of `Packaged`, `In Progress` or `Done`;
  - the handoff's `- **Design commit**: \`<value>\`` is neither `uncommitted` nor a commit for which `git merge-base --is-ancestor <value> HEAD` exits 0;
  - a task's `epic:` differs from `epic_slug`, or its `status` is not in `sync_task_status.TASK_STATUSES`.

  The Status is the first `- **Status**:` line of `<epic_dir>.en.md`.
- **R7b** (WARN): the `- **Status**:` line of the epic directory's `*-design.en.md` matches `re.compile(r"draft|awaiting|under .*review|bản nháp|chờ duyệt", re.I)`. The finding is `R7b WARN spec status: <the line's value>`.
- **R5, R6, R8 in this task**: `CHECKS` already lists `("R5", check_grounding)`, `("R6", check_gate4_coverage)` and `("R8", check_baseline)`. `check_grounding` and `check_gate4_coverage` return `[]` until Task 2. `check_baseline` returns `[]`; the report prints `R8 SKIP` whenever `baseline` is false.
- **Fixture builder** (new frozen contract for Task 3), in `test_check_epic_readiness.py`:
  ```python
  def build_ready_epic(root: Path) -> None
  ```
  It writes the PRV-HP-01 epic `demo_epic` (slug `demo-epic`, 2 tasks) into an existing Git repository at `root`, and commits nothing. Every task passes the real `check_task_contract.py --design`, every scenario is assigned, both document pairs pass the linter, the spec Status is `Approved (Gate 1)`, and the HLD Status is `Planned`.

## Definition of Done
## Definition of Done

- All five covered scenarios have a `test_prv_*` method in `ReadinessCoreTest` and pass in the JUnit report. (V2, V5)
- `build_ready_epic` produces an epic for which `check_epic_readiness.py` exits 0. (V2)
- Lint and strict type checking report zero issues on both new files. (V3, V4)

## Dependencies & Blockers
===== .devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md
---
id: "task_2_readiness_grounding_and_baseline"
status: "done"
priority: "high"
assignee: null
epic: "principal_review"
dueDate: null
created: "2026-10-22T09:10:00Z"
modified: "2026-10-23T09:48:05Z"
completedAt: "2026-10-23T09:48:05Z"
labels: ["readiness", "grounding", "gate-4"]
order: "a2"
---

# Task 2: Readiness Grounding, Gate 4 Coverage and Baseline

Epic: [principal_review](principal_review.en.md)

## Requirement Analysis

Fill the three checks Task 1 registered empty:
- **R5**: every symbol a task's `Target Files & Symbols` lists for an existing, non-new file occurs in that file.
- **R5b** (WARN): every `/api/` route the tasks or the HLD name occurs in tracked source.
- **R6**: every task with a `Covers:` line has a `TIER-C` row, and every test path in a `TIER-C` row is run by an `Integration results:` command.
- **R8** (opt-in `--baseline`): the epic's existing `GREEN` and `TIER-B` rows run in the current checkout, and failures and timeouts are reported as warnings.

These are the checks that would have caught the nonexistent `buildPersistTrackPayload`, the
unpassable Gate 4 and the baseline Node failures in the lyrics-sync review.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py` (new)
- `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/run_task_checks.py` — `run_command(command, root, timeout)`, `mismatch(row, code, text)`
- `skills/dev-implementation/resources/scripts/task_contract.py` — `section()`, `parse_allowed_files()`, `parse_verification()`, `Row`, `AllowedPath`
- `.devtool/epic/principal_review/principal_review.en.md` — Module Contracts, rules R5, R5b, R6, R8

## Design Rationale

R5 fails only on explicit `path: symbol` pairs, so it never guesses at prose. Routes stay WARN
because a route can legitimately live in a config file or a generated table. R6 reasons about the
same tokens Gate 4 will run, so an epic that passes R6 cannot reach Gate 4 with a scenario that
### BDD SCENARIOS

Covers: PRV-EC-01, PRV-EC-03, PRV-EC-06, PRV-FR-01

```gherkin
Scenario: [PRV-EC-01] [Tier C - Integration] A symbol missing from its file fails R5
  Given the PRV-HP-01 epic whose task_2 lists "- `src/app.py`: `build_payload()`, new `render()`" under Target Files & Symbols
  And src/app.py exists without the text "build_payload"
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R5 FAIL" that contains "task_2", "build_payload" and "src/app.py"
  And no R5 line mentions "render"
  And the last line ends "— FAIL" and the exit code is 1

Scenario: [PRV-EC-03] [Tier C - Integration] A TIER-C test outside every Integration results command fails R6
  Given the PRV-HP-01 epic whose task_2 TIER-C row runs "python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml tests/test_extra.py"
  And the HLD's only Integration results command names "tests/test_core.py"
  And "tests/" is an Integration test roots directory
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R6 FAIL" containing "task_2" and "tests/test_extra.py"
  And the exit code is 1

Scenario: [PRV-EC-06] [Tier C - Integration] A route found in no source file warns R5b without failing
  Given the PRV-HP-01 epic whose task_1 names "/api/tts/ocr-upload" and whose only tracked source names "/api/studio/extract/start"
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R5b WARN" containing "/api/tts/ocr-upload"
  And no line mentions "/api/studio/extract/start"
  And the last line is "Result: 0 FAIL, 1 WARN — PASS" and the exit code is 0

Scenario: [PRV-FR-01] [Tier C - Integration] Baseline failures and timeouts warn and the other rows still run
  Given the PRV-HP-01 epic in a clean tree whose task_1 has rows V2 GREEN "python3 -c 'raise SystemExit(1)'" expecting "exit 0", V3 TIER-B "sleep 5" expecting "exit 0", and V4 GREEN "python3 -c 'print(1)'" expecting "exit 0"
  And task_2 has a GREEN row whose command names a path marked (new)
  When check_epic_readiness.py demo_epic --baseline --row-timeout 2 runs
  Then the output has a line starting "R8 WARN" containing "task_1:V2"
  And a line starting "R8 WARN" containing "task_1:V3" and "timeout"
  And no R8 line mentions "task_1:V4" or task_2's row
  And the exit code is 0
  When the tree has an uncommitted change and the same command runs
  Then the output has the line "R8 WARN baseline skipped: dirty tree"
```

## Verification
## Decisions Already Made

- **R5** (`check_grounding(ctx) -> list[Finding]`):
  - in each task, take the `Impact Analysis & Blast Radius` section and its bullet whose label is `Target Files & Symbols` or `Target files and symbols`, case-insensitive;
  - read its sub-bullets matching ``^\s*-\s+`([^`]+)`:\s*(.*)$``;
  - check a path only if it exists under `root` and that task's `parse_allowed_files()` does not mark it `new`;
  - for each backticked token in the rest of the line that matches `[A-Za-z_][\w.]*(?:\(\))?`, unless it is preceded by the word `new` and whitespace, strip `()` and keep the text after the last `.`;
  - that name must occur in the file text. Otherwise the finding is `R5 FAIL <task file>: <name> not in <path>`.
- **R5b** (WARN, same function):
  - routes match `(?<![\w/])/api/[\w\-/{}.:]*[\w}]` in every task file and the HLD; each is cut at its first `{` and stripped of a trailing `/`;
  - search the files `git ls-files` lists, outside `.devtool/` and `docs/` and not ending in `.md`;
  - a route found nowhere is `R5b WARN <route>: not found in tracked source`, reported once per route.
- **R6** (`check_gate4_coverage(ctx) -> list[Finding]`):
  - a task with a `Covers:` line and no `TIER-C` row is `R6 FAIL <task file>: Covers without a TIER-C row`;
  - for each `TIER-C` row, a `shlex.split` token is a test path when it starts with one of `ctx.roots`;
  - a test path is covered when some `ctx.results` command, split the same way, contains the same token, or a token ending in `/` that the path starts with;
  - an uncovered path is `R6 FAIL <task file>:<row id>: <path> is in no Integration results command`.
- **R8** (`check_baseline(ctx) -> list[Finding]`):
  - when `ctx.baseline` is false, return `[]`; the report prints `R8 SKIP`;
  - when `git status --porcelain` is non-empty, return exactly one `R8 WARN baseline skipped: dirty tree`;
  - otherwise, for every task in file order and every row with Phase `GREEN` or `TIER-B` whose command contains no path any epic task marks `new`:
    - run `run_task_checks.run_command(row.command, ctx.root, ctx.row_timeout)`;
    - a `None` code is `R8 WARN <task stem>:<row id> timeout after <row_timeout>s`;
    - otherwise a non-`None` `run_task_checks.mismatch(row, code, text)` is `R8 WARN <task stem>:<row id> <mismatch text>`;
  - with no warning, the report prints `R8 PASS`.
- `run_task_checks` is imported as a module from the same directory, as `run_external_review.py` imports `local_review`.

## Definition of Done
## Definition of Done

- All four covered scenarios have a `test_prv_*` method in `ReadinessGroundingTest` and pass in the JUnit report. (V2, V5)
- `ReadinessCoreTest` from Task 1 still passes, including PRV-HP-01 with R5, R6 and R8 real. (V2)
- Lint and strict type checking report zero issues on both files. (V3, V4)

## Dependencies & Blockers
===== .devtool/epic/principal_review/task_3_principal_review_runner_mode.md
---
id: "task_3_principal_review_runner_mode"
status: "done"
priority: "high"
assignee: null
epic: "principal_review"
dueDate: null
created: "2026-10-22T09:10:00Z"
modified: "2026-10-23T10:03:37Z"
completedAt: "2026-10-23T10:03:37Z"
labels: ["review", "cli", "principal-review"]
order: "a3"
---

# Task 3: Principal Review Mode in the Runner

Epic: [principal_review](principal_review.en.md)

## Requirement Analysis

Teach `run_external_review.py` a second kind of review.
- `run --kind principal` sends the epic's design documents, not a code diff, to the Claude CLI or
  the Codex CLI, with the Principal Reviewer prompt and the `check_epic_readiness.py` report as
  facts.
- It records the round in `principal_review.md`.
- `check --kind principal` and `triage --kind principal` read that file.

Readiness is a precondition: a FAIL prints the existing banner and never invokes the CLI. With the
default `--kind code`, every behaviour of today's code review stays byte-identical. The two new
reference files hold the prompt and the rules.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`
- `skills/dev-implementation/references/principal-review-prompt.md` (new)
- `skills/dev-implementation/references/principal-review-rules.md` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py` (new) — the precondition (Tasks 1–2)
- `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` (new) — `build_ready_epic(root)`
- `skills/dev-implementation/resources/scripts/test_local_review.py` — the Ollama suite that must pass unchanged
- `skills/dev-implementation/references/external-review-prompt.md` — the output contract the principal prompt reuses
- `skills/dev-implementation/references/review-triage.md` — the triage discipline the prompt and rules defer to
### BDD SCENARIOS

Covers: PRV-HP-02, PRV-HP-03, PRV-ST-01, PRV-ST-02, PRV-AR-01, PRV-FR-03, PRV-FR-04

```gherkin
Scenario: [PRV-HP-02] [Tier C - Integration] A principal round is recorded in principal_review.md
  Given the PRV-HP-01 epic committed in a clean tree and a fake "claude" on PATH that saves its stdin and prints "Verdict: PASS"
  When run_external_review.py run --kind principal --epic-dir demo_epic --base main --cli claude runs
  Then the saved prompt contains "Principal Reviewer", "Result: 0 FAIL, 0 WARN — PASS", ".devtool/epic/demo_epic/demo_epic.en.md" and the SHA of main
  And the saved prompt does not contain "audit_epic.py"
  And principal_review.md starts with "# Principal Review: demo_epic" and has "## Round 1" with "- **Kind**: principal", "- **CLI**: claude", "- **Status**: completed" and "- **Verdict**: PASS"
  And review_results.md does not exist
  And the exit code is 0

Scenario: [PRV-HP-03] [Tier C - Integration] Findings with proposed edits become table rows and set the exit code
  Given a fake "codex" that prints "Verdict: CHANGES REQUIRED" and "[Important] task_2:Decisions Already Made — persist_track returns a dict. Proposed: keep TrackPersistResult."
  When run --kind principal --cli codex runs
  Then principal_review.md has a findings row with "Important", "task_2:Decisions Already Made" and "Proposed: keep TrackPersistResult."
  And the round's "- **Verdict**: CHANGES REQUIRED"
  And the exit code is 1

Scenario: [PRV-ST-01] [Tier C - Integration] Decisions move check --kind principal from 1 to 0, independent of code rounds
  Given principal_review.md whose latest completed round has one Important finding with an empty Decision cell
  And review_results.md whose latest round has no finding
  When run_external_review.py check --kind principal --epic-dir demo_epic runs
  Then it prints "undecided: #1 Important" and exits 1
  And check --epic-dir demo_epic without --kind exits 0
  When the Decision cell becomes "fixed in abc1234"
  Then check --kind principal exits 0

Scenario: [PRV-ST-02] [Tier C - Integration] triage reads the file --kind selects
  Given principal_review.md with 2 rounds and review_results.md with 1 round
  When run_external_review.py triage --kind principal --epic-dir demo_epic runs
  Then the output starts "# Review Triage: demo_epic, Round 2"
  And triage without --kind prints "Round 1"
  When principal_review.md does not exist
  Then triage --kind principal prints "no review round recorded for demo_epic" and exits 2

Scenario: [PRV-AR-01] [Tier C - Integration] A second round before the first is committed is refused and rounds number in order
  Given a completed principal round 1 written but not committed
  When run --kind principal runs again
  Then it prints "commit or stash your changes before a review" and exits 2
  And the fake CLI is called exactly once in total
  When round 1 is committed and run --kind principal runs again
  Then principal_review.md has "## Round 1" followed by "## Round 2"

Scenario: [PRV-FR-03] [Tier C - Integration] A readiness FAIL blocks the CLI and records nothing
  Given the PRV-EC-01 epic committed in a clean tree and a fake "claude" that records every call
  When run --kind principal --cli claude runs
  Then stderr shows "WAS NOT INVOKED" and "check_epic_readiness.py"
  And stderr shows the line containing "R5 FAIL"
  And the fake CLI was never called
  And principal_review.md does not exist and the exit code is 2

Scenario: [PRV-FR-04] [Tier C - Integration] --kind principal --cli ollama is rejected before any work
  Given a throwaway epic repository with an uncommitted change
  When run --kind principal --cli ollama --model m runs
  Then stderr shows "--kind principal supports --cli claude or codex"
  And stderr never shows "[Pre-check]"
  And the exit code is 2 and no principal_review.md exists
```

## Verification
## Decisions Already Made

- **New frozen symbols** (HLD, Module Contracts):
  ```python
  KINDS = ("code", "principal")
  PRINCIPAL_PROMPT = SCRIPTS.parent.parent / "references" / "principal-review-prompt.md"
  PRINCIPAL_RULES = SCRIPTS.parent.parent / "references" / "principal-review-rules.md"

  def review_file(kind: str) -> tuple[str, str]
  def principal_artefact_lines(root: Path, epic_dir: str) -> str
  def run_principal(root: Path, args: argparse.Namespace, sha: str) -> int
  ```
  `review_file("code") == ("review_results.md", "Cross-Model Review")` and
  `review_file("principal") == ("principal_review.md", "Principal Review")`.
- **Arguments**: `run`, `check` and `triage` each gain `--kind` with `choices=KINDS`, `default="code"`.
- **Shared functions**:
  - `record_round` builds `path = root / ".devtool" / "epic" / args.epic_dir / name`, and starts a new file with `f"# {title}: {args.epic_dir}\n"`, where `name, title = review_file(getattr(args, "kind", "code"))`;
  - `check` and `triage` resolve `path` the same way;
  - no other line of those functions changes.
- **`run` order for `--kind principal`**, each failure exiting 2 with no round:
  1. `--cli ollama`: print `--kind principal supports --cli claude or codex` to stderr, before any other check.
  2. The CLI is not on PATH: today's message.
  3. A dirty tree: today's message, `commit or stash your changes before a review`.
  4. In `run_principal`: `run_gate("check_epic_readiness.py", [sys.executable, str(SCRIPTS / "check_epic_readiness.py"), args.epic_dir], root, args.facts_timeout)`. A `PreconditionFailedError` goes through `print_gate_banner(error, args.cli)`.
- **Prompt**: `Template(PRINCIPAL_PROMPT.read_text(encoding="utf-8")).safe_substitute(rules=PRINCIPAL_RULES.read_text(encoding="utf-8").strip(), sha=sha, base=args.base, base_sha=<git rev-parse --verify args.base>, epic_dir=f".devtool/epic/{args.epic_dir}", artefacts=principal_artefact_lines(root, args.epic_dir), readiness_output=<the gate's stdout, rstripped>)`.
- **Execution and record**: `before = status_lines(root)`, then `code, out, err = execute(cli_command(args.cli, args.model), root, args.timeout, prompt)`, then `changed = tree_changes(root, before, sha)`, then `return record_round(root, args, sha, [Pass("principal", code, out, err, prompt)], changed, {"Kind": "principal"})`. `collect_facts`, `audit_epic.py`, the integration commands and `build_diff_section` are never called for `--kind principal`.
- **`principal_artefact_lines`**: one ``- `.devtool/epic/<epic_dir>/<name>` `` line each, in this order:
  1. the `*-design.en.md` and `*-design.vi.md` files;
  2. `<epic_dir>.en.md` and `<epic_dir>.vi.md`;
  3. `bdd_scenarios.en.md` and `bdd_scenarios.vi.md`;
  4. every `task_*.md`, sorted;
  5. `handoff.md` when present.

  It never lists `review_results.md` or `principal_review.md`.
- **`principal-review-prompt.md`**:
  - the reader is "the Principal Reviewer who signs off this epic before implementation";
  - it is strictly read-only, and must read the source at `$sha`;
  - sections: Candidate (`$sha`, `$base`, `$base_sha`, `$epic_dir`), Artefacts (`$artefacts`), Readiness facts (`$readiness_output` in a `text` fence), Rules (`$rules`), and a Checklist with P1–P8 worded as in the spec's §5.3;
  - Required output is the external review prompt's block, with the finding line `[Critical|Important|Minor] <artefact>:<location> — <problem>. Proposed: <edit>`.
- **`principal-review-rules.md`**:
  - severities: Critical, the epic cannot reach its goal or Gate 4 as designed; Important, a task would hit Stop-and-Report or ship wrong behaviour; Minor, wording and consistency;
  - the readiness report is already proven: do not restate it, spend the review on judgement and grounding;
  - every claim about the source names the file and line it read;
  - a finding names the artefact and section to change, and its `Proposed:` edit.
- **Tests**: class `PrincipalReviewTest(ReviewCase)`, one `test_prv_*` method per covered scenario. Fake `claude` and `codex` executables go on `PATH` as the existing cases do, and the fixture epic comes from `test_check_epic_readiness.build_ready_epic`.

## Definition of Done
## Definition of Done

- All seven covered scenarios have a `test_prv_*` method in `PrincipalReviewTest` and pass in the JUnit report. (V2, V7)
- The existing code-review and Ollama suites pass unchanged. (V2, V3, V7)
- Lint and strict type checking report zero issues on `run_external_review.py`, and the two reference files lint clean. (V4, V5, V6)
- The principal prompt reads as a Principal Reviewer's sign-off brief and covers P1–P8. (Gate 5)

## Dependencies & Blockers
===== .devtool/epic/principal_review/task_4_epic_status_sync_scope.md
---
id: "task_4_epic_status_sync_scope"
status: "done"
priority: "medium"
assignee: null
epic: "principal_review"
dueDate: null
created: "2026-10-22T09:10:00Z"
modified: "2026-10-23T09:33:45Z"
completedAt: "2026-10-23T09:33:45Z"
labels: ["kanban-sync", "worktree", "packaging"]
order: "a4"
---

# Task 4: Scope Epic Status Sync to Its Own Worktrees

Epic: [principal_review](principal_review.en.md)

## Requirement Analysis

`sync_task_status.py epic <epic_dir> <status>` rewrites the overview Status in every checkout of
the repository, including worktrees of other epics. In lyrics-sync, packaging one epic left
uncommitted Status edits inside another epic's worktree, and another session could have committed
them to the wrong epic. The Principal Review loop re-packages after every revision, so it would
repeat that side effect on every round.

The `epic` subcommand must now write only to the current checkout and to worktrees on the
`epic/<epic_slug>` branch. The `task`, `archive-epic` and `archive-done` subcommands keep
mirroring across every checkout, which is their purpose.

The file also carries 8 ruff and 3 strict-mypy findings on `main`, among them a real
`str | None` union access and two `list[str]` / `list[Path]` mix-ups. This task clears them, so its
Tier B rows prove the file clean.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/sync_task_status.py`
- `skills/dev-implementation/resources/scripts/test_sync_task_status.py`

Read-only context:
- `skills/dev-implementation/SKILL.md` — `<epic_slug>` and the `epic/<epic_slug>` branch name
- `scripts/test_lifecycle_signals.py` — `QueuedPackagingTest` runs `sync_task_status.py epic`
- `scripts/test_verifiable_handoff.py` — runs the done gate through `sync_task_status.py`
- `.devtool/epic/principal_review/principal_review.en.md` — Module Contracts, `sync_task_status.py`
### BDD SCENARIOS

Covers: PRV-HP-05, PRV-FR-05

```gherkin
Scenario: [PRV-HP-05] [Tier C - Integration] epic updates the main checkout and the epic's own worktree
  Given a throwaway repository with epic "demo_epic" (slug "demo-epic") and a worktree on branch "epic/demo-epic"
  When sync_task_status.py epic demo_epic Packaged runs in the main checkout
  Then demo_epic.en.md and demo_epic.vi.md read "Packaged" in both checkouts

Scenario: [PRV-FR-05] [Tier C - Integration] Another epic's worktree stays byte-identical and task sync still mirrors everywhere
  Given the PRV-HP-05 repository plus a worktree on branch "epic/other-epic" that also contains .devtool/epic/demo_epic/
  When sync_task_status.py epic demo_epic Packaged runs in the main checkout
  Then git status in the "epic/other-epic" worktree is empty
  When sync_task_status.py task task_1_demo in-progress runs
  Then task_1_demo reads "in-progress" in all three checkouts
```

## Verification
## Decisions Already Made

- **New frozen symbols** (HLD, Module Contracts):
  ```python
  def parse_worktree_branches(output: str) -> list[tuple[Path, str | None]]
  def epic_checkout_roots(epic_dir: str) -> list[Path]
  ```
- **`parse_worktree_branches`**:
  - reads `git worktree list --porcelain` output, in which entries are separated by blank lines;
  - each entry yields `(Path(<worktree>), <branch ref>)`, for example `refs/heads/epic/demo-epic`, or `None` when the entry has `detached` or no `branch` line.
- **`epic_checkout_roots`**:
  - `current = Path(git rev-parse --show-toplevel)`, and `slug = find_epic_slug(current, epic_dir) or epic_dir`;
  - the result is `current` followed by every worktree path whose branch is `f"refs/heads/epic/{slug}"`;
  - paths are compared after `resolve()`, deduplicated and kept in order.
- **`main`**: only the `epic` subcommand changes its roots, from `checkout_roots()` to `epic_checkout_roots(args.epic_dir)`. `sync_epic()`, its return value and its printed `Synchronized <n> epic docs …` line are unchanged.
- **Unchanged subcommands**: `task`, `archive-epic` and `archive-done` keep `checkout_roots()`.
- **Lint and type debt**: clear every finding `ruff check` and `mypy --strict --follow-imports=silent` report on `sync_task_status.py` without changing behaviour. On `main` at `5f91fd7` there are 8 ruff and 3 mypy findings.
- **Tests**: class `EpicCheckoutRootsTests(unittest.TestCase)` builds a throwaway repository with worktrees on `epic/demo-epic` and `epic/other-epic`, and has one `test_prv_*` method per covered scenario plus a parser test.

## Definition of Done
## Definition of Done

- Both covered scenarios have a `test_prv_*` method in `EpicCheckoutRootsTests` and pass in the JUnit report. (V2, V7)
- The existing sync, lifecycle-signal and verifiable-handoff suites pass unchanged. (V2, V3, V4, V7)
- `sync_task_status.py` reports zero ruff and strict-mypy findings. (V5, V6)

## Dependencies & Blockers
===== .devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md
---
id: "task_5_principal_review_choice_and_acceptance"
status: "done"
priority: "high"
assignee: null
epic: "principal_review"
dueDate: null
created: "2026-10-22T09:10:00Z"
modified: "2026-10-23T10:20:58Z"
completedAt: "2026-10-23T10:20:58Z"
labels: ["lifecycle", "docs", "acceptance"]
order: "a5"
---

# Task 5: Principal Review Choice in the Lifecycle, and Acceptance

Epic: [principal_review](principal_review.en.md)

## Requirement Analysis

This is the final Tier C task. It wires Tasks 1–4 into the workflow the agents follow.

- **`dev-lifecycle`**:
  - its packaging step 1 becomes the single `check_epic_readiness.py` command;
  - a new step 8 offers **Principal Review Choice**;
  - the full loop lives in a new `references/principal-review.md`;
  - Red Flags names the two new mistakes.
- **`dev-implementation`**: checks `principal_review.md` before Gate 3.
- **Handoff template**: lists `principal_review.md` under Read First.
- **Both `docs/lifecycles.*.md`**: draw the loop.
- **Contract tests and `scripts/verify.sh`**: pin all of it, and the acceptance rows run every
  suite of the epic and the full pre-release check.

`dev-lifecycle/SKILL.md` stands at 2454 of its 2500-word ceiling. Replacing the four preflight
commands with one frees the words the pointer needs.

## Files

Allowed files:
- `skills/dev-lifecycle/SKILL.md`
- `skills/dev-lifecycle/references/principal-review.md` (new)
- `skills/dev-lifecycle/references/handoff-template.md`
- `skills/dev-implementation/SKILL.md`
- `docs/lifecycles.en.md`
- `docs/lifecycles.vi.md`
### BDD SCENARIOS

Covers: PRV-HP-04, PRV-EC-07, PRV-ST-03, PRV-ST-04

```gherkin
Scenario: [PRV-HP-04] [Tier C - Integration] Packaging runs one readiness command and offers Principal Review Choice
  Given skills/dev-lifecycle/SKILL.md and skills/dev-lifecycle/references/principal-review.md
  Then the skill contains "check_epic_readiness.py <epic_dir>", "Principal Review Choice" and "references/principal-review.md"
  And the skill no longer contains "check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks"
  And the skill has at most 2500 words and keeps every pinned dev-lifecycle token
  And the reference contains "1. **Done**", "2. **Principal Review**", "Claude CLI", "Codex CLI", "Never choose for the developer" and "strongly recommended"

Scenario: [PRV-EC-07] [Tier C - Integration] Read First lists principal_review.md
  Given skills/dev-lifecycle/references/handoff-template.md
  Then its Read First section contains ".devtool/epic/<epic_dir>/principal_review.md, when present"
  And it keeps "`git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>`" unchanged

Scenario: [PRV-ST-03] [Tier C - Integration] The loop returns to Package and Done re-packages after a round
  Given docs/lifecycles.en.md, docs/lifecycles.vi.md and skills/dev-lifecycle/references/principal-review.md
  Then both documents contain 'PKG --> PRC', 'PRC -->|"2. Principal Review"| PR' and 'PR -->|"revised and re-packaged"| PKG'
  And neither document has an edge from PR to S3 or to G3
  And the reference contains "Record Principal Review round <n>", "Revise epic after Principal Review round <n>" and "Package epic for handoff"
  And the reference states that Done runs "check --kind principal" and re-packages when the last commit touching the epic directory is not the Package commit

Scenario: [PRV-ST-04] [Tier C - Integration] Gate 3 stops while a blocking principal finding is undecided
  Given skills/dev-implementation/SKILL.md
  Then Entry-Point Detection contains "run_external_review.py check --kind principal --epic-dir <epic_dir>"
  And Phase 1 step 3 and Resume Gate 3 both mention "Principal Review" with "not run", "round <n>: PASS" and "round <n>: decided"
  And the skill has at most 4500 words
```

## Verification
## Decisions Already Made

- **`dev-lifecycle/SKILL.md`, packaging procedure**:
  - step 1 becomes `1. **Preflight, read-only.** Must exit 0: \`python3 "$SCRIPTS"/check_epic_readiness.py <epic_dir>\`. Its first line gives the task count.`;
  - step 2 keeps "`<N>` is the task count the preflight printed";
  - step 7 becomes `Print \`handoff.md\` path and rendered Resume Prompt.`;
  - new step 8: `8. Present **Principal Review Choice** — follow [references/principal-review.md](references/principal-review.md).`;
  - Red Flags gains `- Picking the Principal Review CLI for the developer.` and `- Acting on a Principal Review finding before triage.`;
  - the file stays at 2500 words or fewer. If it does not, trim prose that repeats the Review Choice transitions, never a token in `EXPECTED` or in the two signal suites.
- **`dev-lifecycle/references/principal-review.md`** (new):
  - steps 1–7 of the spec's §6 in order, with:
    - the choice text `1. **Done** — stop here.` and `2. **Principal Review** — a cross-model review of the design against the source before implementation (Claude CLI or Codex CLI).`;
    - the sentence `Never choose for the developer.`;
    - the D2 recommendation including the words `strongly recommended`, judged from the HLD's `Author` line or the developer's word;
    - the commands `run_external_review.py run --kind principal --epic-dir <epic_dir> --base <base_branch> --cli <claude|codex>`, `triage --kind principal` and `check --kind principal`;
  - the commit titles `[EPIC_NAME] Record Principal Review round <n>`, `[EPIC_NAME] Record Principal Review decisions for round <n>` and `[EPIC_NAME] Revise epic after Principal Review round <n>` (C2);
  - the Done rule: run `check --kind principal`, which must exit 0. Then re-run the packaging procedure when `git log -1 --format=%s -- .devtool/epic/<epic_dir>` is not `[<EPIC_NAME>] Package epic for handoff` (C3). Then print the handoff path and the Resume Prompt and stop;
  - it ends by pointing at `../../dev-implementation/references/review-triage.md` for how to fill the triage.
- **`dev-implementation/SKILL.md`**:
  - Entry-Point Detection's read-only signals gain `test -f .devtool/epic/<epic_dir>/principal_review.md && python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --kind principal --epic-dir <epic_dir>`;
  - Phase 1 step 3 (Gate 3) and Resume Procedure step 4 (Gate 3, resume) each state the Principal Review status, `not run`, `round <n>: PASS` or `round <n>: decided`, and stop with the triage when that check exits 1;
  - the file stays at 4500 words or fewer.
- **`handoff-template.md`**:
  - Read First gains `4. \`.devtool/epic/<epic_dir>/principal_review.md\`, when present — Principal Review rounds and decisions.`;
  - the staleness command `git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>` is unchanged.
- **`docs/lifecycles.en.md` and `docs/lifecycles.vi.md`, Stage 2 diagram**:
  - the terminal `PKG([...])` node becomes `PKG["Package epic<br/>handoff.md, status Packaged"]`;
  - add `PRC{"Principal Review Choice<br/>Done or Principal Review?"}` and `PR["run_external_review.py run --kind principal<br/>triage, decisions, revision"]`;
  - add the edges `PKG --> PRC`, `PRC -->|"1. Done"| PKGSTOP(["Stop: handoff.md and Resume Prompt"])`, `PRC -->|"2. Principal Review"| PR` and `PR -->|"revised and re-packaged"| PKG`;
  - add one paragraph after the Routing & Handoff Choice bullet. The Vietnamese node labels may be translated; the edge labels are kept verbatim.
- **`scripts/test_lifecycle_document_contract.py`**:
  - `EXPECTED["skills/dev-lifecycle/SKILL.md"]` gains `"check_epic_readiness.py <epic_dir>"`, `"Principal Review Choice"` and `"references/principal-review.md"`;
  - new class `PrincipalReviewWorkflowTest(unittest.TestCase)` has one `test_prv_*` method per covered scenario.
- **`scripts/verify.sh`**: add `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py || FAILED=1` beside the other `dev-implementation` suites.

## Definition of Done
## Definition of Done

- All four covered scenarios have a `test_prv_*` method in `PrincipalReviewWorkflowTest` and pass in the JUnit report. (V2, V10)
- Every earlier lifecycle and handoff contract test passes unchanged. (V2, V3, V4)
- Every changed or new document lints clean, and both lifecycle documents keep their bilingual structure. (V5, V6)
- The contract test file lints and type-checks clean, and the full pre-release check passes. (V7, V8, V9)
- Every suite of the epic passes together in one JUnit report. (V10)
- Run against a packaged epic the developer chooses (for example lyrics-sync's `flashcard_compact_data_enrichment` at `5cc7d720` in a scratch worktree), `check_epic_readiness.py` produces a report the developer judges accurate and useful. (Gate 5)

## Dependencies & Blockers

exec
/bin/zsh -lc 'for f in .devtool/epic/principal_review/evidence/*.json; do echo "===== $f"; jq '"'{task_id,status,candidate_sha,task_commit,allowed_files,verification_count:(.verification|length),verification:[.verification[]|{id,phase,command,exit_code,status,expected,output_tail}],definition_of_done,notes}' \""'$f"; done' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 exited 5 in 0ms:
===== .devtool/epic/principal_review/evidence/task_1_readiness_check_core.json
jq: error (at .devtool/epic/principal_review/evidence/task_1_readiness_check_core.json:199): Cannot iterate over null (null)
===== .devtool/epic/principal_review/evidence/task_2_readiness_grounding_and_baseline.json
jq: error (at .devtool/epic/principal_review/evidence/task_2_readiness_grounding_and_baseline.json:219): Cannot iterate over null (null)
===== .devtool/epic/principal_review/evidence/task_3_principal_review_runner_mode.json
jq: error (at .devtool/epic/principal_review/evidence/task_3_principal_review_runner_mode.json:227): Cannot iterate over null (null)
===== .devtool/epic/principal_review/evidence/task_4_epic_status_sync_scope.json
jq: error (at .devtool/epic/principal_review/evidence/task_4_epic_status_sync_scope.json:215): Cannot iterate over null (null)
===== .devtool/epic/principal_review/evidence/task_5_principal_review_choice_and_acceptance.json
jq: error (at .devtool/epic/principal_review/evidence/task_5_principal_review_choice_and_acceptance.json:442): Cannot iterate over null (null)

exec
/bin/zsh -lc 'for f in .devtool/epic/principal_review/evidence/*.json; do echo "===== $f"; jq '"'keys' \""'$f"; jq '"'. | {task_id,task,status,commit,head_sha,base_sha,keys:(keys)}' \""'$f"; done' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
===== .devtool/epic/principal_review/evidence/task_1_readiness_check_core.json
[
  "runs",
  "schema",
  "task"
]
{
  "task_id": null,
  "task": "task_1_readiness_check_core",
  "status": null,
  "commit": null,
  "head_sha": null,
  "base_sha": null,
  "keys": [
    "runs",
    "schema",
    "task"
  ]
}
===== .devtool/epic/principal_review/evidence/task_2_readiness_grounding_and_baseline.json
[
  "runs",
  "schema",
  "task"
]
{
  "task_id": null,
  "task": "task_2_readiness_grounding_and_baseline",
  "status": null,
  "commit": null,
  "head_sha": null,
  "base_sha": null,
  "keys": [
    "runs",
    "schema",
    "task"
  ]
}
===== .devtool/epic/principal_review/evidence/task_3_principal_review_runner_mode.json
[
  "runs",
  "schema",
  "task"
]
{
  "task_id": null,
  "task": "task_3_principal_review_runner_mode",
  "status": null,
  "commit": null,
  "head_sha": null,
  "base_sha": null,
  "keys": [
    "runs",
    "schema",
    "task"
  ]
}
===== .devtool/epic/principal_review/evidence/task_4_epic_status_sync_scope.json
[
  "runs",
  "schema",
  "task"
]
{
  "task_id": null,
  "task": "task_4_epic_status_sync_scope",
  "status": null,
  "commit": null,
  "head_sha": null,
  "base_sha": null,
  "keys": [
    "runs",
    "schema",
    "task"
  ]
}
===== .devtool/epic/principal_review/evidence/task_5_principal_review_choice_and_acceptance.json
[
  "runs",
  "schema",
  "task"
]
{
  "task_id": null,
  "task": "task_5_principal_review_choice_and_acceptance",
  "status": null,
  "commit": null,
  "head_sha": null,
  "base_sha": null,
  "keys": [
    "runs",
    "schema",
    "task"
  ]
}

exec
/bin/zsh -lc 'for f in .devtool/epic/principal_review/evidence/*.json; do echo "===== $f"; jq '"'{schema,task,runs:[.runs[]|{id,phase,command,expected_exit,exit_code,started_at,finished_at,output_sha256,output_tail,status}]}' \""'$f"; done' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
===== .devtool/epic/principal_review/evidence/task_1_readiness_check_core.json
{
  "schema": 1,
  "task": "task_1_readiness_check_core",
  "runs": [
    {
      "id": null,
      "phase": null,
      "command": null,
      "expected_exit": null,
      "exit_code": null,
      "started_at": null,
      "finished_at": null,
      "output_sha256": null,
      "output_tail": null,
      "status": null
    },
    {
      "id": null,
      "phase": null,
      "command": null,
      "expected_exit": null,
      "exit_code": null,
      "started_at": null,
      "finished_at": null,
      "output_sha256": null,
      "output_tail": null,
      "status": null
    }
  ]
}
===== .devtool/epic/principal_review/evidence/task_2_readiness_grounding_and_baseline.json
{
  "schema": 1,
  "task": "task_2_readiness_grounding_and_baseline",
  "runs": [
    {
      "id": null,
      "phase": null,
      "command": null,
      "expected_exit": null,
      "exit_code": null,
      "started_at": null,
      "finished_at": null,
      "output_sha256": null,
      "output_tail": null,
      "status": null
    },
    {
      "id": null,
      "phase": null,
      "command": null,
      "expected_exit": null,
      "exit_code": null,
      "started_at": null,
      "finished_at": null,
      "output_sha256": null,
      "output_tail": null,
      "status": null
    }
  ]
}
===== .devtool/epic/principal_review/evidence/task_3_principal_review_runner_mode.json
{
  "schema": 1,
  "task": "task_3_principal_review_runner_mode",
  "runs": [
    {
      "id": null,
      "phase": null,
      "command": null,
      "expected_exit": null,
      "exit_code": null,
      "started_at": null,
      "finished_at": null,
      "output_sha256": null,
      "output_tail": null,
      "status": null
    },
    {
      "id": null,
      "phase": null,
      "command": null,
      "expected_exit": null,
      "exit_code": null,
      "started_at": null,
      "finished_at": null,
      "output_sha256": null,
      "output_tail": null,
      "status": null
    }
  ]
}
===== .devtool/epic/principal_review/evidence/task_4_epic_status_sync_scope.json
{
  "schema": 1,
  "task": "task_4_epic_status_sync_scope",
  "runs": [
    {
      "id": null,
      "phase": null,
      "command": null,
      "expected_exit": null,
      "exit_code": null,
      "started_at": null,
      "finished_at": null,
      "output_sha256": null,
      "output_tail": null,
      "status": null
    },
    {
      "id": null,
      "phase": null,
      "command": null,
      "expected_exit": null,
      "exit_code": null,
      "started_at": null,
      "finished_at": null,
      "output_sha256": null,
      "output_tail": null,
      "status": null
    }
  ]
}
===== .devtool/epic/principal_review/evidence/task_5_principal_review_choice_and_acceptance.json
{
  "schema": 1,
  "task": "task_5_principal_review_choice_and_acceptance",
  "runs": [
    {
      "id": null,
      "phase": null,
      "command": null,
      "expected_exit": null,
      "exit_code": null,
      "started_at": null,
      "finished_at": null,
      "output_sha256": null,
      "output_tail": null,
      "status": null
    },
    {
      "id": null,
      "phase": null,
      "command": null,
      "expected_exit": null,
      "exit_code": null,
      "started_at": null,
      "finished_at": null,
      "output_sha256": null,
      "output_tail": null,
      "status": null
    }
  ]
}

exec
/bin/zsh -lc "sed -n '1,230p' .devtool/epic/principal_review/evidence/task_1_readiness_check_core.json" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
{
  "schema": 1,
  "task": "task_1_readiness_check_core",
  "runs": {
    "red": {
      "head": "8f7d5cbe38ac9d0424abf94efad12f1f994d6b51",
      "tree": "a69e1e11a943c8b90b357b203c99186d6190bb45",
      "patch_id": "4905262705ac4834d65de486829d585de76055d0",
      "started": "2026-10-23T09:16:54Z",
      "finished": "2026-10-23T09:16:55Z",
      "rows": [
        {
          "id": "V1",
          "phase": "RED",
          "command": "python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k ReadinessCoreTest",
          "expect": "exit 1; contains \"FAILED\"",
          "needs": [],
          "exit": 1,
          "outcome": "PASS",
          "reason": null,
          "started": "2026-10-23T09:16:54Z",
          "finished": "2026-10-23T09:16:55Z",
          "output_tail": [
            "----------------------------------------------------------------------",
            "Traceback (most recent call last):",
            "  File \"/Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review/skills/dev-implementation/resources/scripts/test_check_epic_readiness.py\", line 507, in test_prv_ec_05_metadata_packaged_without_handoff_and_draft_spec",
            "    self.assertEqual(code, 1, f\"Expected 1, got {code}.\\nStdout:\\n{stdout}\")",
            "    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
            "AssertionError: 2 != 1 : Expected 1, got 2.",
            "Stdout:",
            "",
            "",
            "======================================================================",
            "FAIL: test_prv_fr_02_failing_preflight_subcheck_and_missing_dir (skills.dev-implementation.resources.scripts.test_check_epic_readiness.ReadinessCoreTest.test_prv_fr_02_failing_preflight_subcheck_and_missing_dir)",
            "PRV-FR-02: A failing preflight sub-check fails R1 by name; missing dir exits 2.",
            "----------------------------------------------------------------------",
            "Traceback (most recent call last):",
            "  File \"/Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review/skills/dev-implementation/resources/scripts/test_check_epic_readiness.py\", line 553, in test_prv_fr_02_failing_preflight_subcheck_and_missing_dir",
            "    self.assertEqual(code, 1, f\"Expected 1, got {code}.\\nStdout:\\n{stdout}\")",
            "    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
            "AssertionError: 2 != 1 : Expected 1, got 2.",
            "Stdout:",
            "",
            "",
            "======================================================================",
            "FAIL: test_prv_hp_01_ready_fixture_epic_passes_every_check (skills.dev-implementation.resources.scripts.test_check_epic_readiness.ReadinessCoreTest.test_prv_hp_01_ready_fixture_epic_passes_every_check)",
            "PRV-HP-01: A ready fixture epic passes every check.",
            "----------------------------------------------------------------------",
            "Traceback (most recent call last):",
            "  File \"/Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review/skills/dev-implementation/resources/scripts/test_check_epic_readiness.py\", line 417, in test_prv_hp_01_ready_fixture_epic_passes_every_check",
            "    self.assertEqual(code, 0, f\"Expected 0, got {code}.\\nStdout:\\n{stdout}\\nStderr:\\n{stderr}\")",
            "    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
            "AssertionError: 2 != 0 : Expected 0, got 2.",
            "Stdout:",
            "",
            "Stderr:",
            "/opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/Resources/Python.app/Contents/MacOS/Python: can't open file '/Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review/skills/dev-implementation/resources/scripts/check_epic_readiness.py': [Errno 2] No such file or directory",
            "",
            "",
            "----------------------------------------------------------------------",
            "Ran 5 tests in 0.412s",
            "",
            "FAILED (failures=5)"
          ],
          "output_sha256": "2c696d7242b728c4e6a20b4c4133c81ffbbedf766f3c6b5f6e1533f7f5d04cd7"
        }
      ]
    },
    "verify": {
      "head": "8f7d5cbe38ac9d0424abf94efad12f1f994d6b51",
      "tree": "0240fd3505da5f109f4ebe629158d4c245df0302",
      "patch_id": "c05dda7cf2b9ef808deeac91dc4a9e13dae9432c",
      "started": "2026-10-23T09:22:12Z",
      "finished": "2026-10-23T09:22:19Z",
      "rows": [
        {
          "id": "V2",
          "phase": "GREEN",
          "command": "python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k ReadinessCoreTest",
          "expect": "exit 0; contains \"OK\"",
          "needs": [],
          "exit": 0,
          "outcome": "PASS",
          "reason": null,
          "started": "2026-10-23T09:22:12Z",
          "finished": "2026-10-23T09:22:15Z",
          "output_tail": [
            ".....",
            "----------------------------------------------------------------------",
            "Ran 5 tests in 3.465s",
            "",
            "OK"
          ],
          "output_sha256": "24cb7c5738084a41fc4631deefdea2e26225a542cdea0615e52c9b04f6e7e127"
        },
        {
          "id": "V3",
          "phase": "TIER-B",
          "command": "ruff check skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py",
          "expect": "exit 0",
          "needs": [],
          "exit": 0,
          "outcome": "PASS",
          "reason": null,
          "started": "2026-10-23T09:22:15Z",
          "finished": "2026-10-23T09:22:15Z",
          "output_tail": [
            "All checks passed!"
          ],
          "output_sha256": "82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18"
        },
        {
          "id": "V4",
          "phase": "TIER-B",
          "command": "mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py",
          "expect": "exit 0",
          "needs": [],
          "exit": 0,
          "outcome": "PASS",
          "reason": null,
          "started": "2026-10-23T09:22:15Z",
          "finished": "2026-10-23T09:22:15Z",
          "output_tail": [
            "Success: no issues found in 2 source files"
          ],
          "output_sha256": "f9b031e5c45aa702cd4fef028d465551cb20a2c4698e0913c7b00766b20ac4d8"
        },
        {
          "id": "V5",
          "phase": "TIER-C",
          "command": "python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_1.xml skills/dev-implementation/resources/scripts/test_check_epic_readiness.py",
          "expect": "exit 0; results build/test-results/task_1.xml",
          "needs": [],
          "exit": 0,
          "outcome": "PASS",
          "reason": null,
          "started": "2026-10-23T09:22:15Z",
          "finished": "2026-10-23T09:22:19Z",
          "output_tail": [
            ".....",
            "----------------------------------------------------------------------",
            "Ran 5 tests in 3.177s",
            "",
            "OK"
          ],
          "output_sha256": "fa6c0953f7269e432c23d836171f65105be658c988d4cc6f4275adbd97ef857a",
          "results": {
            "path": "build/test-results/task_1.xml",
            "fresh": true,
            "digest": {
              "totals": {
                "passed": 5,
                "failed": 0,
                "skipped": 0
              },
              "cases": [
                {
                  "name": "test_prv_ec_02_tier_drift_fails_r3_and_tier_b_tag_fails_r4",
                  "classname": "test_check_epic_readiness.ReadinessCoreTest",
                  "status": "passed"
                },
                {
                  "name": "test_prv_ec_04_mirror_drift_fails_and_location_link_passes",
                  "classname": "test_check_epic_readiness.ReadinessCoreTest",
                  "status": "passed"
                },
                {
                  "name": "test_prv_ec_05_metadata_packaged_without_handoff_and_draft_spec",
                  "classname": "test_check_epic_readiness.ReadinessCoreTest",
                  "status": "passed"
                },
                {
                  "name": "test_prv_fr_02_failing_preflight_subcheck_and_missing_dir",
                  "classname": "test_check_epic_readiness.ReadinessCoreTest",
                  "status": "passed"
                },
                {
                  "name": "test_prv_hp_01_ready_fixture_epic_passes_every_check",
                  "classname": "test_check_epic_readiness.ReadinessCoreTest",
                  "status": "passed"
                }
              ]
            }
          }
        },
        {
          "id": "SCOPE",
          "phase": "SCOPE",
          "outcome": "PASS",
          "changed": [
            "skills/dev-implementation/resources/scripts/check_epic_readiness.py",
            "skills/dev-implementation/resources/scripts/test_check_epic_readiness.py"
          ],
          "violations": []
        }
      ]
    }
  }
}

exec
/bin/zsh -lc 'for f in .devtool/epic/principal_review/evidence/*.json; do echo "===== $f"; jq -r '"'.task, (\"RED head=\" + .runs.red.head + \" tree=\" + .runs.red.tree), (.runs.red.rows[] | [.id,.phase,(.exit|tostring),.outcome,.command] | @tsv), (\"VERIFY head=\" + .runs.verify.head + \" tree=\" + .runs.verify.tree), (.runs.verify.rows[] | [.id,.phase,((.exit // \"-\")|tostring),.outcome,(.command // ((.changed // [])|join(\",\"))),(.reason // \"\")] | @tsv)' \""'$f"; done' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
===== .devtool/epic/principal_review/evidence/task_1_readiness_check_core.json
task_1_readiness_check_core
RED head=8f7d5cbe38ac9d0424abf94efad12f1f994d6b51 tree=a69e1e11a943c8b90b357b203c99186d6190bb45
V1	RED	1	PASS	python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k ReadinessCoreTest
VERIFY head=8f7d5cbe38ac9d0424abf94efad12f1f994d6b51 tree=0240fd3505da5f109f4ebe629158d4c245df0302
V2	GREEN	0	PASS	python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k ReadinessCoreTest	
V3	TIER-B	0	PASS	ruff check skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py	
V4	TIER-B	0	PASS	mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py	
V5	TIER-C	0	PASS	python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_1.xml skills/dev-implementation/resources/scripts/test_check_epic_readiness.py	
SCOPE	SCOPE	-	PASS	skills/dev-implementation/resources/scripts/check_epic_readiness.py,skills/dev-implementation/resources/scripts/test_check_epic_readiness.py	
===== .devtool/epic/principal_review/evidence/task_2_readiness_grounding_and_baseline.json
task_2_readiness_grounding_and_baseline
RED head=97fcbe454d8bad4e16c2657c9f314f1e75d4aa3b tree=eb8ae5e4e71abe59c489ae921a08bddc14541dcf
V1	RED	1	PASS	python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k ReadinessGroundingTest
VERIFY head=97fcbe454d8bad4e16c2657c9f314f1e75d4aa3b tree=864e1f15ec4670985964553aaf8d6d19a3e74495
V2	GREEN	0	PASS	python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py	
V3	TIER-B	0	PASS	ruff check skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py	
V4	TIER-B	0	PASS	mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py	
V5	TIER-C	0	PASS	python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml skills/dev-implementation/resources/scripts/test_check_epic_readiness.py	
SCOPE	SCOPE	-	PASS	skills/dev-implementation/resources/scripts/check_epic_readiness.py,skills/dev-implementation/resources/scripts/test_check_epic_readiness.py	
===== .devtool/epic/principal_review/evidence/task_3_principal_review_runner_mode.json
task_3_principal_review_runner_mode
RED head=7b430362c9e26343544f1e28a8de72d7236b5bec tree=6c3fe3efd7bdec4f5546f0eeeeb086ed9250635e
V1	RED	1	PASS	python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k PrincipalReviewTest
VERIFY head=7b430362c9e26343544f1e28a8de72d7236b5bec tree=4d96d64d89df614aad083dc862cc81d54d621843
V2	GREEN	0	PASS	python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py	
V3	GREEN	0	PASS	python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py	
V4	TIER-B	0	PASS	ruff check skills/dev-implementation/resources/scripts/run_external_review.py	
V5	TIER-B	0	PASS	mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/run_external_review.py	
V6	TIER-B	0	PASS	python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-implementation/references/principal-review-prompt.md skills/dev-implementation/references/principal-review-rules.md	
V7	TIER-C	0	PASS	python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_3.xml skills/dev-implementation/resources/scripts/test_run_external_review.py skills/dev-implementation/resources/scripts/test_local_review.py	
SCOPE	SCOPE	-	PASS	skills/dev-implementation/references/principal-review-prompt.md,skills/dev-implementation/references/principal-review-rules.md,skills/dev-implementation/resources/scripts/run_external_review.py,skills/dev-implementation/resources/scripts/test_run_external_review.py	
===== .devtool/epic/principal_review/evidence/task_4_epic_status_sync_scope.json
task_4_epic_status_sync_scope
RED head=019190e0b848c4a71c415ee85e7889fed1220722 tree=20339d5bc0b18a6cf19819a01cfe87d8f58ad656
V1	RED	1	PASS	python3 -m unittest skills/dev-implementation/resources/scripts/test_sync_task_status.py -k EpicCheckoutRootsTests
VERIFY head=019190e0b848c4a71c415ee85e7889fed1220722 tree=65bd2abd688c7b2d9f49f7a52f1f0407f34d0149
V2	GREEN	0	PASS	python3 -m unittest skills/dev-implementation/resources/scripts/test_sync_task_status.py	
V3	GREEN	0	PASS	python3 -m unittest scripts/test_lifecycle_signals.py	
V4	GREEN	0	PASS	python3 -m unittest scripts/test_verifiable_handoff.py	
V5	TIER-B	0	PASS	ruff check skills/dev-implementation/resources/scripts/sync_task_status.py	
V6	TIER-B	0	PASS	mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/sync_task_status.py	
V7	TIER-C	0	PASS	python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_4.xml skills/dev-implementation/resources/scripts/test_sync_task_status.py scripts/test_lifecycle_signals.py	
SCOPE	SCOPE	-	PASS	skills/dev-implementation/resources/scripts/sync_task_status.py,skills/dev-implementation/resources/scripts/test_sync_task_status.py	
===== .devtool/epic/principal_review/evidence/task_5_principal_review_choice_and_acceptance.json
task_5_principal_review_choice_and_acceptance
RED head=a0e1537d2c006fbbd9f608477ed9f1979af90c95 tree=8c262cedbf57872d7cb962805f88a151b4095b26
V1	RED	1	PASS	python3 -m unittest scripts/test_lifecycle_document_contract.py -k PrincipalReviewWorkflowTest
VERIFY head=a0e1537d2c006fbbd9f608477ed9f1979af90c95 tree=632bf1f5170d20c0aa111bc5858e36b6745a6f1e
V2	GREEN	0	PASS	python3 -m unittest scripts/test_lifecycle_document_contract.py	
V3	GREEN	0	PASS	python3 -m unittest scripts/test_lifecycle_signals.py	
V4	GREEN	0	PASS	python3 -m unittest scripts/test_verifiable_handoff_text.py	
V5	TIER-B	0	PASS	python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc --require-bilingual docs/lifecycles.en.md docs/lifecycles.vi.md	
V6	TIER-B	0	PASS	python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-lifecycle/SKILL.md skills/dev-implementation/SKILL.md skills/dev-lifecycle/references/principal-review.md skills/dev-lifecycle/references/handoff-template.md	
V7	TIER-B	0	PASS	ruff check scripts/test_lifecycle_document_contract.py	
V8	TIER-B	0	PASS	mypy --strict --follow-imports=silent scripts/test_lifecycle_document_contract.py	
V9	TIER-B	0	PASS	bash scripts/verify.sh	
V10	TIER-C	0	PASS	python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_5.xml skills/dev-implementation/resources/scripts/test_check_epic_readiness.py skills/dev-implementation/resources/scripts/test_run_external_review.py skills/dev-implementation/resources/scripts/test_sync_task_status.py scripts/test_lifecycle_document_contract.py scripts/test_lifecycle_signals.py scripts/test_verifiable_handoff_text.py	
SCOPE	SCOPE	-	PASS	docs/lifecycles.en.md,docs/lifecycles.vi.md,scripts/test_lifecycle_document_contract.py,scripts/verify.sh,skills/dev-implementation/SKILL.md,skills/dev-lifecycle/SKILL.md,skills/dev-lifecycle/references/handoff-template.md,skills/dev-lifecycle/references/principal-review.md	

exec
/bin/zsh -lc 'for c in 019190e 97fcbe4 7b43036 a0e1537 c09cb95; do echo "===== $c"; git show --format='"'%H%n%s%n%b' --name-status --no-renames \""'$c"; done' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 9200ms:
===== 019190e
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-Fx4o1lok' (errno=Operation not permitted)
2026-10-23 17:45:14.721 xcodebuild[26129:2216981]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:14.865 xcodebuild[26129:2216980] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-YbqriBCB' (errno=Operation not permitted)
2026-10-23 17:45:15.380 xcodebuild[26132:2217006]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:15.517 xcodebuild[26132:2217005] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
019190e0b848c4a71c415ee85e7889fed1220722
[PRINCIPAL_REVIEW] Task 1: Readiness check core
- implement check_epic_readiness.py with R1-R4, R7, R7b and report frame
- add unit and integration test suite test_check_epic_readiness.py
- verify 5/5 BDD scenarios and record check evidence


A	.devtool/epic/principal_review/evidence/task_1_readiness_check_core.json
M	.devtool/epic/principal_review/principal_review.en.md
M	.devtool/epic/principal_review/principal_review.vi.md
M	.devtool/epic/principal_review/task_1_readiness_check_core.md
A	.devtool/features/done/task_1_readiness_check_core.md
D	.devtool/features/task_1_readiness_check_core.md
A	skills/dev-implementation/resources/scripts/check_epic_readiness.py
A	skills/dev-implementation/resources/scripts/test_check_epic_readiness.py
===== 97fcbe4
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-SkPdjhVN' (errno=Operation not permitted)
2026-10-23 17:45:16.594 xcodebuild[26138:2217052]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:16.731 xcodebuild[26138:2217051] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-FlpGlm5a' (errno=Operation not permitted)
2026-10-23 17:45:17.225 xcodebuild[26149:2217115]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:17.362 xcodebuild[26149:2217114] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
97fcbe454d8bad4e16c2657c9f314f1e75d4aa3b
[PRINCIPAL_REVIEW] Task 4: Scope epic status sync to its own worktrees
- implement parse_worktree_branches and epic_checkout_roots in sync_task_status.py
- scope epic subcommand to current checkout and worktrees on refs/heads/epic/<epic_slug>
- clear 8 ruff and 3 strict-mypy issues in sync_task_status.py
- add unit and integration tests for PRV-HP-05 and PRV-FR-05


A	.devtool/epic/principal_review/evidence/task_4_epic_status_sync_scope.json
M	.devtool/epic/principal_review/task_4_epic_status_sync_scope.md
A	.devtool/features/done/task_4_epic_status_sync_scope.md
D	.devtool/features/task_4_epic_status_sync_scope.md
M	skills/dev-implementation/resources/scripts/sync_task_status.py
M	skills/dev-implementation/resources/scripts/test_sync_task_status.py
===== 7b43036
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-fkzHbkY0' (errno=Operation not permitted)
2026-10-23 17:45:18.500 xcodebuild[26156:2217193]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:18.635 xcodebuild[26156:2217192] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-Raygi35D' (errno=Operation not permitted)
2026-10-23 17:45:19.109 xcodebuild[26158:2217205]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:19.248 xcodebuild[26158:2217204] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
7b430362c9e26343544f1e28a8de72d7236b5bec
[PRINCIPAL_REVIEW] Task 2: Readiness grounding, Gate 4 coverage and baseline
- implement R5 symbol grounding check and R5b route check in check_epic_readiness.py
- implement R6 gate 4 integration coverage check
- implement R8 baseline check for clean/dirty trees and timeout handling
- add tests covering PRV-EC-01, PRV-EC-03, PRV-EC-06, and PRV-FR-01


A	.devtool/epic/principal_review/evidence/task_2_readiness_grounding_and_baseline.json
M	.devtool/epic/principal_review/task_2_readiness_grounding_and_baseline.md
A	.devtool/features/done/task_2_readiness_grounding_and_baseline.md
D	.devtool/features/task_2_readiness_grounding_and_baseline.md
M	skills/dev-implementation/resources/scripts/check_epic_readiness.py
M	skills/dev-implementation/resources/scripts/test_check_epic_readiness.py
===== a0e1537
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-PCtgVoNb' (errno=Operation not permitted)
2026-10-23 17:45:20.319 xcodebuild[26164:2217240]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:20.452 xcodebuild[26164:2217238] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-lhLkXmxc' (errno=Operation not permitted)
2026-10-23 17:45:20.971 xcodebuild[26168:2217254]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:21.115 xcodebuild[26168:2217253] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
a0e1537d2c006fbbd9f608477ed9f1979af90c95
[PRINCIPAL_REVIEW] Task 3: Principal review mode in the runner
- add --kind principal to run_external_review.py
- implement principal_artefact_lines, run_principal, and review_file routing
- create principal-review-prompt.md and principal-review-rules.md
- add tests covering PRV-HP-02, PRV-HP-03, PRV-ST-01, PRV-ST-02, PRV-AR-01, PRV-FR-03, and PRV-FR-04


A	.devtool/epic/principal_review/evidence/task_3_principal_review_runner_mode.json
M	.devtool/epic/principal_review/task_3_principal_review_runner_mode.md
A	.devtool/features/done/task_3_principal_review_runner_mode.md
D	.devtool/features/task_3_principal_review_runner_mode.md
A	skills/dev-implementation/references/principal-review-prompt.md
A	skills/dev-implementation/references/principal-review-rules.md
M	skills/dev-implementation/resources/scripts/run_external_review.py
M	skills/dev-implementation/resources/scripts/test_run_external_review.py
===== c09cb95
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-hbC91vmy' (errno=Operation not permitted)
2026-10-23 17:45:22.177 xcodebuild[26185:2217348]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:22.313 xcodebuild[26185:2217346] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-yxOSievv' (errno=Operation not permitted)
2026-10-23 17:45:22.787 xcodebuild[26187:2217361]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:22.932 xcodebuild[26187:2217360] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
c09cb95593c5908098462a0a2963f1a300d9efcb
[PRINCIPAL_REVIEW] Task 5: Principal review choice and acceptance
- replace preflight in dev-lifecycle packaging with check_epic_readiness.py
- add Principal Review Choice step 8 and reference principal-review.md
- update handoff-template.md Read First to list principal_review.md
- update dev-implementation Entry-Point Detection and Gate 3 checks
- add PRC transitions and paragraphs in docs/lifecycles.en.md and docs/lifecycles.vi.md
- add test_check_epic_readiness.py to scripts/verify.sh
- add PrincipalReviewWorkflowTest in test_lifecycle_document_contract.py


A	.devtool/epic/principal_review/evidence/task_5_principal_review_choice_and_acceptance.json
M	.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md
A	.devtool/features/done/task_5_principal_review_choice_and_acceptance.md
D	.devtool/features/task_5_principal_review_choice_and_acceptance.md
M	docs/lifecycles.en.md
M	docs/lifecycles.vi.md
M	scripts/test_lifecycle_document_contract.py
M	scripts/verify.sh
M	skills/dev-implementation/SKILL.md
M	skills/dev-lifecycle/SKILL.md
M	skills/dev-lifecycle/references/handoff-template.md
A	skills/dev-lifecycle/references/principal-review.md

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/check_epic_readiness.py | sed -n '1,280p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/check_epic_readiness.py | sed -n '281,560p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/check_epic_readiness.py | sed -n '561,840p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
   281	                current_lines = []
   282	            continue
   283	
   284	        if not in_gherkin:
   285	            continue
   286	
   287	        sc_match = cb.SCENARIO_LINE.match(line)
   288	        if sc_match:
   289	            if current_id is not None:
   290	                blocks[current_id] = current_lines
   291	                current_lines = []
   292	            rest = sc_match.group(1).strip()
   293	            id_match = cb.ID_SHAPE.search(rest)
   294	            if id_match:
   295	                current_id = id_match.group(0)
   296	                current_lines = [line.rstrip()]
   297	            else:
   298	                current_id = None
   299	        elif current_id is not None:
   300	            if not line.strip():
   301	                blocks[current_id] = current_lines
   302	                current_id = None
   303	                current_lines = []
   304	            else:
   305	                current_lines.append(line.rstrip())
   306	
   307	    if current_id is not None:
   308	        blocks[current_id] = current_lines
   309	
   310	    return blocks
   311	
   312	
   313	def check_bdd_scenarios(ctx: Context) -> list[Finding]:
   314	    findings: list[Finding] = []
   315	    epic_path = ctx.root / ".devtool" / "epic" / ctx.epic_dir
   316	    bdd_en_path = epic_path / "bdd_scenarios.en.md"
   317	    if not bdd_en_path.is_file():
   318	        return findings
   319	
   320	    canonical_blocks = extract_scenario_blocks(bdd_en_path.read_text(encoding="utf-8"))
   321	
   322	    for task_path, task_text in ctx.tasks.items():
   323	        task_blocks = extract_scenario_blocks(task_text)
   324	        for sc_id, t_lines in task_blocks.items():
   325	            if sc_id in canonical_blocks and t_lines != canonical_blocks[sc_id]:
   326	                findings.append(
   327	                    Finding("R3", "FAIL", f"{task_path.name}: {sc_id} differs from bdd_scenarios.en.md")
   328	                )
   329	
   330	    bdd_vi_path = epic_path / "bdd_scenarios.vi.md"
   331	    if bdd_vi_path.is_file():
   332	        en_ids, _ = cb.scenario_ids(bdd_en_path)
   333	        vi_ids, _ = cb.scenario_ids(bdd_vi_path)
   334	        en_set = set(en_ids)
   335	        vi_set = set(vi_ids)
   336	        if en_set != vi_set:
   337	            for missing_or_extra in sorted(en_set ^ vi_set):
   338	                findings.append(
   339	                    Finding("R3", "FAIL", f"bdd_scenarios.vi.md: {missing_or_extra} missing or extra")
   340	                )
   341	
   342	    return findings
   343	
   344	
   345	def check_tier_tags(ctx: Context) -> list[Finding]:
   346	    findings: list[Finding] = []
   347	    bdd_en_path = ctx.root / ".devtool" / "epic" / ctx.epic_dir / "bdd_scenarios.en.md"
   348	    if not bdd_en_path.is_file():
   349	        return findings
   350	
   351	    in_gherkin = False
   352	    fence_marker: str | None = None
   353	    for line in bdd_en_path.read_text(encoding="utf-8").splitlines():
   354	        fence_match = cb.FENCE.match(line)
   355	        if fence_match and fence_marker is None:
   356	            fence_marker = fence_match.group(1)
   357	            in_gherkin = fence_match.group(2).lower() == "gherkin"
   358	            continue
   359	        if (
   360	            fence_match
   361	            and fence_marker
   362	            and fence_match.group(1)[0] == fence_marker[0]
   363	            and len(fence_match.group(1)) >= len(fence_marker)
   364	            and not fence_match.group(2)
   365	        ):
   366	            fence_marker = None
   367	            in_gherkin = False
   368	            continue
   369	
   370	        if not in_gherkin:
   371	            continue
   372	
   373	        sc_match = cb.SCENARIO_LINE.match(line)
   374	        if not sc_match:
   375	            continue
   376	
   377	        rest = sc_match.group(1).strip()
   378	        tags = re.findall(r"\[([^\]]+)\]", rest)
   379	        if not tags:
   380	            continue
   381	        sc_id = tags[0].strip()
   382	        tier_tag = tags[1].strip() if len(tags) > 1 else "none"
   383	
   384	        if tier_tag not in ("Tier A - Unit", "Tier C - Integration"):
   385	            findings.append(Finding("R4", "FAIL", f'{sc_id}: tier tag "{tier_tag}"'))
   386	
   387	    return findings
   388	
   389	
   390	def check_grounding(ctx: Context) -> list[Finding]:
   391	    findings: list[Finding] = []
   392	
   393	    # --- R5: Symbol Grounding ---
   394	    target_header_re = re.compile(
   395	        r"^\s*-\s*\*\*(?:Target Files & Symbols|Target files and symbols)\*\*:\s*(.*)$",
   396	        re.IGNORECASE,
   397	    )
   398	    sub_bullet_re = re.compile(r"^\s*-\s+`([^`]+)`:\s*(.*)$")
   399	    token_re = re.compile(r"`([^`]+)`")
   400	    ident_re = re.compile(r"^[A-Za-z_][\w.]*(?:\(\))?$")
   401	
   402	    for task_path, task_text in ctx.tasks.items():
   403	        impact_body = tc.section(task_text, "Impact Analysis & Blast Radius")
   404	        if not impact_body:
   405	            for heading in (
   406	                "Impact Analysis & Blast Radius",
   407	                "Impact analysis & blast radius",
   408	                "Impact Analysis and Blast Radius",
   409	            ):
   410	                impact_body = tc.section(task_text, heading)
   411	                if impact_body:
   412	                    break
   413	        if not impact_body:
   414	            continue
   415	
   416	        allowed_files = tc.parse_allowed_files(task_text)
   417	        new_patterns = {ap.pattern for ap in allowed_files if ap.new}
   418	
   419	        in_target_symbols = False
   420	        target_lines: list[str] = []
   421	        for line in impact_body.splitlines():
   422	            if target_header_re.match(line):
   423	                in_target_symbols = True
   424	                continue
   425	            if in_target_symbols:
   426	                if re.match(r"^\s*-\s+\*\*", line) or (line.startswith("- ") and not line.startswith("  - ")):
   427	                    break
   428	                target_lines.append(line)
   429	
   430	        for line in target_lines:
   431	            sub_m = sub_bullet_re.match(line)
   432	            if not sub_m:
   433	                continue
   434	            path_str = sub_m.group(1).strip()
   435	            rest = sub_m.group(2)
   436	
   437	            full_path = ctx.root / path_str
   438	            if not full_path.is_file() or path_str in new_patterns:
   439	                continue
   440	
   441	            try:
   442	                file_text = full_path.read_text(encoding="utf-8", errors="ignore")
   443	            except OSError:
   444	                continue
   445	
   446	            for span_m in token_re.finditer(rest):
   447	                token_raw = span_m.group(1).strip()
   448	                if not ident_re.match(token_raw):
   449	                    continue
   450	                prefix = rest[:span_m.start()]
   451	                if re.search(r"\bnew\s+$", prefix):
   452	                    continue
   453	
   454	                clean_name = token_raw.removesuffix("()")
   455	                name = clean_name.split(".")[-1]
   456	                if name not in file_text:
   457	                    findings.append(Finding("R5", "FAIL", f"{task_path.name}: {name} not in {path_str}"))
   458	
   459	    # --- R5b: Route Grounding (WARN) ---
   460	    route_re = re.compile(r"(?<![\w/])/api/[\w\-/{}.:]*[\w}]")
   461	    routes_to_check: list[str] = []
   462	    texts_to_scan = list(ctx.tasks.values()) + [ctx.hld_text]
   463	
   464	    for text in texts_to_scan:
   465	        for match in route_re.finditer(text):
   466	            r = match.group(0)
   467	            if "{" in r:
   468	                r = r.split("{", 1)[0]
   469	            r = r.rstrip("/")
   470	            if r and r not in routes_to_check:
   471	                routes_to_check.append(r)
   472	
   473	    if routes_to_check:
   474	        try:
   475	            ls_proc = subprocess.run(
   476	                ["git", "ls-files"],
   477	                check=False,
   478	                cwd=ctx.root,
   479	                capture_output=True,
   480	                text=True,
   481	            )
   482	            files_list = [
   483	                ctx.root / p
   484	                for p in ls_proc.stdout.splitlines()
   485	                if not p.startswith((".devtool/", "docs/")) and not p.endswith(".md")
   486	            ]
   487	        except OSError:
   488	            files_list = []
   489	
   490	        tracked_contents: list[str] = []
   491	        for f in files_list:
   492	            if f.is_file():
   493	                try:
   494	                    tracked_contents.append(f.read_text(encoding="utf-8", errors="ignore"))
   495	                except OSError:
   496	                    pass
   497	
   498	        for route in routes_to_check:
   499	            if not any(route in content for content in tracked_contents):
   500	                findings.append(Finding("R5b", "WARN", f"{route}: not found in tracked source"))
   501	
   502	    return findings
   503	
   504	
   505	def check_gate4_coverage(ctx: Context) -> list[Finding]:
   506	    findings: list[Finding] = []
   507	
   508	    results_tokens_list: list[list[str]] = []
   509	    for cmd in ctx.results:
   510	        try:
   511	            results_tokens_list.append(shlex.split(cmd))
   512	        except ValueError:
   513	            results_tokens_list.append(cmd.split())
   514	
   515	    for task_path, task_text in ctx.tasks.items():
   516	        covers = cb.covers_of(task_path)
   517	        try:
   518	            rows, _ = tc.parse_verification(task_text)
   519	        except tc.ContractError:
   520	            continue
   521	
   522	        tier_c_rows = [r for r in rows if r.phase == "TIER-C"]
   523	        if covers and not tier_c_rows:
   524	            findings.append(Finding("R6", "FAIL", f"{task_path.name}: Covers without a TIER-C row"))
   525	            continue
   526	
   527	        for r in tier_c_rows:
   528	            try:
   529	                tokens = shlex.split(r.command)
   530	            except ValueError:
   531	                tokens = r.command.split()
   532	
   533	            for t in tokens:
   534	                if not any(t.startswith(root) for root in ctx.roots):
   535	                    continue
   536	
   537	                covered = False
   538	                for res_toks in results_tokens_list:
   539	                    if t in res_toks:
   540	                        covered = True
   541	                        break
   542	                    if any(rt.endswith("/") and t.startswith(rt) for rt in res_toks):
   543	                        covered = True
   544	                        break
   545	
   546	                if not covered:
   547	                    findings.append(
   548	                        Finding(
   549	                            "R6",
   550	                            "FAIL",
   551	                            f"{task_path.name}:{r.id}: {t} is in no Integration results command",
   552	                        )
   553	                    )
   554	
   555	    return findings
   556	
   557	
   558	def check_metadata(ctx: Context) -> list[Finding]:
   559	    findings: list[Finding] = []
   560	    epic_path = ctx.root / ".devtool" / "epic" / ctx.epic_dir

 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""Check epic readiness before implementation or review.
     3	
     4	Usage:
     5	    check_epic_readiness.py <epic_dir> [--baseline] [--row-timeout 600]
     6	"""
     7	from __future__ import annotations
     8	
     9	import argparse
    10	import re
    11	import shlex
    12	import subprocess
    13	import sys
    14	from collections.abc import Callable
    15	from dataclasses import dataclass
    16	from pathlib import Path
    17	
    18	# Sibling modules
    19	SCRIPTS_DIR = Path(__file__).resolve().parent
    20	if str(SCRIPTS_DIR) not in sys.path:
    21	    sys.path.insert(0, str(SCRIPTS_DIR))
    22	
    23	import check_bdd_traceability as cb
    24	import run_task_checks as rtc
    25	import sync_task_status as sts
    26	import task_contract as tc
    27	
    28	LINTER_PATH = SCRIPTS_DIR.parents[2] / "doc_quality_check" / "resources" / "scripts" / "check_document.py"
    29	
    30	
    31	@dataclass(frozen=True)
    32	class Finding:
    33	    check: str     # "R1" ... "R8", "R5b", "R7b"
    34	    severity: str  # "FAIL" or "WARN"
    35	    message: str
    36	
    37	
    38	@dataclass(frozen=True)
    39	class Context:
    40	    root: Path
    41	    epic_dir: str
    42	    epic_slug: str
    43	    hld_text: str
    44	    tasks: dict[Path, str]
    45	    results: list[str]
    46	    roots: list[str]
    47	    baseline: bool = False
    48	    row_timeout: int = 600
    49	
    50	
    51	def parse_integration_test_roots(hld_text: str) -> list[str]:
    52	    for line in hld_text.splitlines():
    53	        if line.startswith("Integration test roots:"):
    54	            _, rest = line.split(":", 1)
    55	            return [part.strip() for part in rest.split(",") if part.strip()]
    56	    return []
    57	
    58	
    59	def load_context(
    60	    root: Path,
    61	    epic_dir: str,
    62	    *,
    63	    baseline: bool = False,
    64	    row_timeout: int = 600,
    65	) -> Context:
    66	    epic_path = root / ".devtool" / "epic" / epic_dir
    67	    hld_path = epic_path / f"{epic_dir}.en.md"
    68	    hld_text = hld_path.read_text(encoding="utf-8")
    69	
    70	    task_paths = sorted(epic_path.glob("task_*.md"))
    71	    tasks: dict[Path, str] = {p: p.read_text(encoding="utf-8") for p in task_paths}
    72	
    73	    epic_slug = epic_dir
    74	    for text in tasks.values():
    75	        m = re.search(r'^epic:\s*"?([^"\n]+)"?', text, re.MULTILINE)
    76	        if m:
    77	            epic_slug = m.group(1).strip()
    78	            break
    79	
    80	    results = tc.parse_integration_results(hld_text)
    81	    roots = parse_integration_test_roots(hld_text)
    82	
    83	    return Context(
    84	        root=root,
    85	        epic_dir=epic_dir,
    86	        epic_slug=epic_slug,
    87	        hld_text=hld_text,
    88	        tasks=tasks,
    89	        results=results,
    90	        roots=roots,
    91	        baseline=baseline,
    92	        row_timeout=row_timeout,
    93	    )
    94	
    95	
    96	def get_last_non_empty_line(*outputs: str) -> str:
    97	    combined = "\n".join(outputs)
    98	    lines = [ln.strip() for ln in combined.splitlines() if ln.strip()]
    99	    return lines[-1] if lines else ""
   100	
   101	
   102	def check_preflight(ctx: Context) -> list[Finding]:
   103	    findings: list[Finding] = []
   104	    task_paths_str = [str(p) for p in ctx.tasks]
   105	    epic_path = ctx.root / ".devtool" / "epic" / ctx.epic_dir
   106	
   107	    # 1. compute_execution_order.py <epic_slug>
   108	    cmd1 = [sys.executable, str(SCRIPTS_DIR / "compute_execution_order.py"), ctx.epic_slug]
   109	    res1 = subprocess.run(cmd1, check=False, cwd=ctx.root, capture_output=True, text=True)
   110	    if res1.returncode != 0:
   111	        last_line = get_last_non_empty_line(res1.stdout, res1.stderr)
   112	        findings.append(Finding("R1", "FAIL", f"compute_execution_order.py: {last_line}"))
   113	    else:
   114	        m_match = re.search(r"(\d+)\s+matched", res1.stdout)
   115	        if m_match:
   116	            m = int(m_match.group(1))
   117	            if m != len(ctx.tasks):
   118	                findings.append(
   119	                    Finding(
   120	                        "R1",
   121	                        "FAIL",
   122	                        f"task mirror count: {m} matched, {len(ctx.tasks)} in the epic directory",
   123	                    )
   124	                )
   125	
   126	    # 2. check_bdd_traceability.py plan
   127	    cmd2 = [
   128	        sys.executable,
   129	        str(SCRIPTS_DIR / "check_bdd_traceability.py"),
   130	        "plan",
   131	        "--scenarios",
   132	        str(epic_path / "bdd_scenarios.en.md"),
   133	        "--tasks",
   134	        *task_paths_str,
   135	    ]
   136	    res2 = subprocess.run(cmd2, check=False, cwd=ctx.root, capture_output=True, text=True)
   137	    if res2.returncode != 0:
   138	        last_line = get_last_non_empty_line(res2.stdout, res2.stderr)
   139	        findings.append(Finding("R1", "FAIL", f"check_bdd_traceability.py plan: {last_line}"))
   140	
   141	    # 3. check_task_contract.py --design
   142	    cmd3 = [
   143	        sys.executable,
   144	        str(SCRIPTS_DIR / "check_task_contract.py"),
   145	        "--design",
   146	        "--hld",
   147	        str(epic_path / f"{ctx.epic_dir}.en.md"),
   148	        "--tasks",
   149	        *task_paths_str,
   150	    ]
   151	    res3 = subprocess.run(cmd3, check=False, cwd=ctx.root, capture_output=True, text=True)
   152	    if res3.returncode != 0:
   153	        last_line = get_last_non_empty_line(res3.stdout, res3.stderr)
   154	        findings.append(Finding("R1", "FAIL", f"check_task_contract.py --design: {last_line}"))
   155	
   156	    # 4. check_document.py
   157	    en_files = sorted(epic_path.glob("*.en.md"))
   158	    bilingual_pairs: list[str] = []
   159	    for ef in en_files:
   160	        stem = ef.name[:-6]
   161	        vf = epic_path / f"{stem}.vi.md"
   162	        if vf.is_file():
   163	            bilingual_pairs.extend([str(ef), str(vf)])
   164	
   165	    if bilingual_pairs:
   166	        cmd_doc1 = [
   167	            sys.executable,
   168	            str(LINTER_PATH),
   169	            "--require-toc",
   170	            "--require-bilingual",
   171	            *bilingual_pairs,
   172	        ]
   173	        res_doc1 = subprocess.run(cmd_doc1, check=False, cwd=ctx.root, capture_output=True, text=True)
   174	        if res_doc1.returncode != 0:
   175	            last_line = get_last_non_empty_line(res_doc1.stdout, res_doc1.stderr)
   176	            findings.append(Finding("R1", "FAIL", f"check_document.py: {last_line}"))
   177	
   178	    handoff_file = epic_path / "handoff.md"
   179	    if handoff_file.is_file():
   180	        cmd_handoff = [
   181	            sys.executable,
   182	            str(LINTER_PATH),
   183	            "--require-toc",
   184	            str(handoff_file),
   185	        ]
   186	        res_handoff = subprocess.run(cmd_handoff, check=False, cwd=ctx.root, capture_output=True, text=True)
   187	        if res_handoff.returncode != 0:
   188	            last_line = get_last_non_empty_line(res_handoff.stdout, res_handoff.stderr)
   189	            findings.append(Finding("R1", "FAIL", f"check_document.py: {last_line}"))
   190	
   191	    if task_paths_str:
   192	        cmd_tasks = [
   193	            sys.executable,
   194	            str(LINTER_PATH),
   195	            *task_paths_str,
   196	        ]
   197	        res_tasks = subprocess.run(cmd_tasks, check=False, cwd=ctx.root, capture_output=True, text=True)
   198	        if res_tasks.returncode != 0:
   199	            last_line = get_last_non_empty_line(res_tasks.stdout, res_tasks.stderr)
   200	            findings.append(Finding("R1", "FAIL", f"check_document.py: {last_line}"))
   201	
   202	    return findings
   203	
   204	
   205	def check_task_mirrors(ctx: Context) -> list[Finding]:
   206	    findings: list[Finding] = []
   207	    features_dir = ctx.root / ".devtool" / "features"
   208	    done_dir = features_dir / "done"
   209	    link_pattern = f"](../epic/{ctx.epic_dir}/"
   210	
   211	    for task_path, epic_text in ctx.tasks.items():
   212	        name = task_path.name
   213	        mirror_path = features_dir / name
   214	        if not mirror_path.is_file():
   215	            mirror_path = done_dir / name
   216	        if not mirror_path.is_file():
   217	            findings.append(Finding("R2", "FAIL", f"{name}: no mirror in .devtool/features/"))
   218	            continue
   219	
   220	        mirror_text = mirror_path.read_text(encoding="utf-8")
   221	        norm_mirror = mirror_text.replace(link_pattern, "](")
   222	
   223	        if norm_mirror != epic_text:
   224	            epic_lines = epic_text.splitlines()
   225	            mirror_lines = norm_mirror.splitlines()
   226	            max_len = max(len(epic_lines), len(mirror_lines))
   227	            diff_line_idx = -1
   228	            epic_line_content = ""
   229	            mirror_line_content = ""
   230	            for i in range(max_len):
   231	                el = epic_lines[i] if i < len(epic_lines) else ""
   232	                ml = mirror_lines[i] if i < len(mirror_lines) else ""
   233	                if el != ml:
   234	                    diff_line_idx = i + 1
   235	                    epic_line_content = el
   236	                    mirror_line_content = ml
   237	                    break
   238	            diff_msg = (
   239	                f"{name}: line {diff_line_idx}: {epic_line_content}"
   240	                if not mirror_line_content
   241	                else (
   242	                    f"{name}: line {diff_line_idx}: {epic_line_content} != {mirror_line_content}"
   243	                    if epic_line_content
   244	                    else f"{name}: line {diff_line_idx}: {mirror_line_content}"
   245	                )
   246	            )
   247	            findings.append(Finding("R2", "FAIL", diff_msg))
   248	
   249	    return findings
   250	
   251	
   252	def extract_scenario_blocks(text: str) -> dict[str, list[str]]:
   253	    blocks: dict[str, list[str]] = {}
   254	    in_gherkin = False
   255	    fence_marker: str | None = None
   256	    current_id: str | None = None
   257	    current_lines: list[str] = []
   258	
   259	    for line in text.splitlines():
   260	        fence_match = cb.FENCE.match(line)
   261	        if fence_match and fence_marker is None:
   262	            fence_marker = fence_match.group(1)
   263	            in_gherkin = fence_match.group(2).lower() == "gherkin"
   264	            if not in_gherkin and current_id is not None:
   265	                blocks[current_id] = current_lines
   266	                current_id = None
   267	                current_lines = []
   268	            continue
   269	        if (
   270	            fence_match
   271	            and fence_marker
   272	            and fence_match.group(1)[0] == fence_marker[0]
   273	            and len(fence_match.group(1)) >= len(fence_marker)
   274	            and not fence_match.group(2)
   275	        ):
   276	            fence_marker = None
   277	            in_gherkin = False
   278	            if current_id is not None:
   279	                blocks[current_id] = current_lines
   280	                current_id = None

 succeeded in 0ms:
   561	    handoff_file = epic_path / "handoff.md"
   562	    has_handoff = handoff_file.is_file()
   563	
   564	    status_match = re.search(r"^- \*\*Status\*\*:\s*(.*)$", ctx.hld_text, re.MULTILINE)
   565	    hld_status = status_match.group(1).strip() if status_match else ""
   566	
   567	    if hld_status.startswith("Packaged") and not has_handoff:
   568	        findings.append(Finding("R7", "FAIL", "Status starts with Packaged but handoff.md is missing"))
   569	
   570	    if has_handoff:
   571	        valid_prefixes = ("Packaged", "In Progress", "Done")
   572	        if not any(hld_status.startswith(prefix) for prefix in valid_prefixes):
   573	            findings.append(Finding("R7", "FAIL", f"handoff.md exists but Status is '{hld_status}'"))
   574	
   575	        handoff_text = handoff_file.read_text(encoding="utf-8")
   576	        design_commit_match = re.search(
   577	            r"^- \*\*Design commit\*\*:\s*`?([^`\n]+)`?", handoff_text, re.MULTILINE
   578	        )
   579	        if design_commit_match:
   580	            design_commit = design_commit_match.group(1).strip()
   581	            if design_commit != "uncommitted":
   582	                check_ancestor = subprocess.run(
   583	                    ["git", "merge-base", "--is-ancestor", design_commit, "HEAD"],
   584	                    check=False,
   585	                    cwd=ctx.root,
   586	                    capture_output=True,
   587	                )
   588	                if check_ancestor.returncode != 0:
   589	                    findings.append(
   590	                        Finding(
   591	                            "R7",
   592	                            "FAIL",
   593	                            f"handoff.md Design commit `{design_commit}` is not an ancestor of HEAD",
   594	                        )
   595	                    )
   596	
   597	    for task_path, task_text in ctx.tasks.items():
   598	        epic_m = re.search(r'^epic:\s*"?([^"\n]+)"?', task_text, re.MULTILINE)
   599	        t_epic = epic_m.group(1).strip() if epic_m else ""
   600	        if t_epic != ctx.epic_slug:
   601	            findings.append(
   602	                Finding("R7", "FAIL", f"{task_path.name}: epic '{t_epic}' differs from '{ctx.epic_slug}'")
   603	            )
   604	
   605	        status_m = re.search(r'^status:\s*"?([^"\n]+)"?', task_text, re.MULTILINE)
   606	        t_status = status_m.group(1).strip() if status_m else ""
   607	        if t_status not in sts.TASK_STATUSES:
   608	            findings.append(
   609	                Finding("R7", "FAIL", f"{task_path.name}: status '{t_status}' not in TASK_STATUSES")
   610	            )
   611	
   612	    spec_files = list(epic_path.glob("*-design.en.md"))
   613	    if spec_files:
   614	        spec_text = spec_files[0].read_text(encoding="utf-8")
   615	        spec_status_m = re.search(r"^- \*\*Status\*\*:\s*(.*)$", spec_text, re.MULTILINE)
   616	        if spec_status_m:
   617	            spec_status = spec_status_m.group(1).strip()
   618	            draft_pattern = re.compile(r"draft|awaiting|under .*review|bản nháp|chờ duyệt", re.IGNORECASE)
   619	            if draft_pattern.search(spec_status):
   620	                findings.append(Finding("R7b", "WARN", f"spec status: {spec_status}"))
   621	
   622	    return findings
   623	
   624	
   625	def check_baseline(ctx: Context) -> list[Finding]:
   626	    if not ctx.baseline:
   627	        return []
   628	
   629	    status_proc = subprocess.run(
   630	        ["git", "status", "--porcelain"],
   631	        check=False,
   632	        cwd=ctx.root,
   633	        capture_output=True,
   634	        text=True,
   635	    )
   636	    if status_proc.stdout.strip():
   637	        return [Finding("R8", "WARN", "baseline skipped: dirty tree")]
   638	
   639	    findings: list[Finding] = []
   640	
   641	    new_paths: set[str] = set()
   642	    for t_text in ctx.tasks.values():
   643	        for ap in tc.parse_allowed_files(t_text):
   644	            if ap.new:
   645	                new_paths.add(ap.pattern)
   646	
   647	    for task_path, task_text in ctx.tasks.items():
   648	        try:
   649	            rows, _ = tc.parse_verification(task_text)
   650	        except tc.ContractError:
   651	            continue
   652	
   653	        for row in rows:
   654	            if row.phase not in ("GREEN", "TIER-B"):
   655	                continue
   656	
   657	            if any(np in row.command for np in new_paths):
   658	                continue
   659	
   660	            code, raw_output = rtc.run_command(row.command, ctx.root, ctx.row_timeout)
   661	            if code is None:
   662	                findings.append(
   663	                    Finding(
   664	                        "R8",
   665	                        "WARN",
   666	                        f"{task_path.stem}:{row.id} timeout after {ctx.row_timeout}s",
   667	                    )
   668	                )
   669	            else:
   670	                out_text = raw_output.decode("utf-8", errors="replace")
   671	                mis = rtc.mismatch(row, code, out_text)
   672	                if mis is not None:
   673	                    findings.append(Finding("R8", "WARN", f"{task_path.stem}:{row.id} {mis}"))
   674	
   675	    return findings
   676	
   677	
   678	CHECKS: tuple[tuple[str, Callable[[Context], list[Finding]]], ...] = (
   679	    ("R1", check_preflight),
   680	    ("R2", check_task_mirrors),
   681	    ("R3", check_bdd_scenarios),
   682	    ("R4", check_tier_tags),
   683	    ("R5", check_grounding),
   684	    ("R6", check_gate4_coverage),
   685	    ("R7", check_metadata),
   686	    ("R8", check_baseline),
   687	)
   688	
   689	
   690	def run_checks(
   691	    ctx: Context,
   692	    *,
   693	    baseline: bool = False,
   694	    row_timeout: int = 600,
   695	) -> list[Finding]:
   696	    active_ctx = Context(
   697	        root=ctx.root,
   698	        epic_dir=ctx.epic_dir,
   699	        epic_slug=ctx.epic_slug,
   700	        hld_text=ctx.hld_text,
   701	        tasks=ctx.tasks,
   702	        results=ctx.results,
   703	        roots=ctx.roots,
   704	        baseline=baseline,
   705	        row_timeout=row_timeout,
   706	    )
   707	    findings: list[Finding] = []
   708	    for _check_id, check_fn in CHECKS:
   709	        findings.extend(check_fn(active_ctx))
   710	    return findings
   711	
   712	
   713	def render_report(ctx: Context, findings: list[Finding]) -> str:
   714	    lines: list[str] = [f"Epic: {ctx.epic_dir} ({ctx.epic_slug}), {len(ctx.tasks)} tasks"]
   715	
   716	    by_check: dict[str, list[Finding]] = {}
   717	    for f in findings:
   718	        by_check.setdefault(f.check, []).append(f)
   719	
   720	    for check_id in ("R1", "R2", "R3", "R4", "R5", "R6", "R7"):
   721	        check_findings = by_check.get(check_id, [])
   722	        has_fail = any(f.severity == "FAIL" for f in check_findings)
   723	        if not has_fail:
   724	            lines.append(f"{check_id} PASS")
   725	        for f in check_findings:
   726	            lines.append(f"{f.check} {f.severity} {f.message}")
   727	
   728	        if check_id == "R5":
   729	            for f in by_check.get("R5b", []):
   730	                lines.append(f"{f.check} {f.severity} {f.message}")
   731	        elif check_id == "R7":
   732	            for f in by_check.get("R7b", []):
   733	                lines.append(f"{f.check} {f.severity} {f.message}")
   734	
   735	    if not ctx.baseline:
   736	        lines.append("R8 SKIP")
   737	    else:
   738	        r8_findings = by_check.get("R8", [])
   739	        has_fail = any(f.severity == "FAIL" for f in r8_findings)
   740	        if not has_fail and not any(f.severity == "WARN" for f in r8_findings):
   741	            lines.append("R8 PASS")
   742	        for f in r8_findings:
   743	            lines.append(f"{f.check} {f.severity} {f.message}")
   744	
   745	    fail_count = sum(1 for f in findings if f.severity == "FAIL")
   746	    warn_count = sum(1 for f in findings if f.severity == "WARN")
   747	    verdict = "PASS" if fail_count == 0 else "FAIL"
   748	    lines.append(f"Result: {fail_count} FAIL, {warn_count} WARN — {verdict}")
   749	
   750	    return "\n".join(lines)
   751	
   752	
   753	def main(argv: list[str] | None = None) -> int:
   754	    parser = argparse.ArgumentParser(description="Check epic readiness before implementation or review.")
   755	    parser.add_argument("epic_dir", help="Epic directory name under .devtool/epic/")
   756	    parser.add_argument(
   757	        "--baseline",
   758	        action="store_true",
   759	        help="Run baseline GREEN and TIER-B verification rows",
   760	    )
   761	    parser.add_argument(
   762	        "--row-timeout",
   763	        type=int,
   764	        default=600,
   765	        help="Timeout in seconds for each baseline row",
   766	    )
   767	
   768	    args = parser.parse_args(argv)
   769	
   770	    try:
   771	        root_str = subprocess.run(
   772	            ["git", "rev-parse", "--show-toplevel"],
   773	            check=True,
   774	            capture_output=True,
   775	            text=True,
   776	        ).stdout.strip()
   777	        root = Path(root_str).resolve()
   778	    except (subprocess.CalledProcessError, OSError):
   779	        sys.stderr.write("error: not in a git repository\n")
   780	        return 2
   781	
   782	    epic_path = root / ".devtool" / "epic" / args.epic_dir
   783	    if not epic_path.is_dir():
   784	        sys.stderr.write(f"error: {epic_path} does not exist\n")
   785	        return 2
   786	
   787	    hld_path = epic_path / f"{args.epic_dir}.en.md"
   788	    if not hld_path.is_file():
   789	        sys.stderr.write(f"error: {hld_path} does not exist\n")
   790	        return 2
   791	
   792	    ctx = load_context(root, args.epic_dir, baseline=args.baseline, row_timeout=args.row_timeout)
   793	    findings = run_checks(ctx, baseline=args.baseline, row_timeout=args.row_timeout)
   794	    report = render_report(ctx, findings)
   795	    print(report)
   796	
   797	    return 1 if any(f.severity == "FAIL" for f in findings) else 0
   798	
   799	
   800	if __name__ == "__main__":
   801	    sys.exit(main())

exec
/bin/zsh -lc "sed -n '170,330p' .devtool/epic/principal_review/principal_review.en.md && sed -n '100,230p' .devtool/epic/principal_review/2026-10-22-principal-review-design.en.md && sed -n '1,110p' .devtool/epic/principal_review/handoff.md" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
    Agent->>Dev: handoff.md path and Resume Prompt
```

### Module Contracts

#### `check_epic_readiness.py` (new)

Located in `skills/dev-implementation/resources/scripts/`.

```python
@dataclass(frozen=True)
class Finding:
    check: str     # "R1" ... "R8", "R5b", "R7b"
    severity: str  # "FAIL" or "WARN"
    message: str

CHECKS: tuple[tuple[str, Callable[[Context], list[Finding]]], ...]  # R1..R8 in order

def load_context(root: Path, epic_dir: str) -> Context
def run_checks(ctx: Context, *, baseline: bool = False, row_timeout: int = 600) -> list[Finding]
def render_report(ctx: Context, findings: list[Finding]) -> str
def main(argv: list[str] | None = None) -> int
```

- **CLI**: `check_epic_readiness.py <epic_dir> [--baseline] [--row-timeout 600]`, run from anywhere inside the repository; the root comes from `git rev-parse --show-toplevel`.
- **`Context`** holds:
  - `root`, `epic_dir` and `epic_slug` (from the epic tasks' `epic:` frontmatter);
  - the HLD text;
  - every `task_*.md` path and text in the epic directory;
  - the parsed `Integration results:` commands and `Integration test roots:` directories.
- **Report**:
  - the first line is `Epic: <epic_dir> (<epic_slug>), <N> tasks`. This is the task count the packaging procedure's `<N>` refers to;
  - then, in check order, `<check> PASS` for each of R1–R7 with no FAIL finding and one line per finding, `<check> <severity> <message>`. R5b and R7b only ever print WARN lines. R8 prints `R8 SKIP` without `--baseline`, and `R8 PASS` with it when no row warns;
  - the last line is `Result: <f> FAIL, <w> WARN — PASS` or `— FAIL`.
- **Exit codes**: 0 with no FAIL, 1 with any FAIL, 2 when the directory or the HLD is missing.
- **R1** runs, through `subprocess` with `sys.executable`:
  - `compute_execution_order.py <epic_slug>`. Its `Scanned … ; M matched` count must equal the epic directory's task count;
  - `check_bdd_traceability.py plan` and `check_task_contract.py --design` with the packaging preflight's arguments;
  - `check_document.py` (`SCRIPTS.parents[2] / "doc_quality_check/resources/scripts/check_document.py"`) with `--require-toc --require-bilingual` on the spec, HLD and BDD pairs, with `--require-toc` on `handoff.md` when present, and plainly on every task file.

  Each failing sub-check is its own `R1 FAIL <command>: <last output line>` finding.
- **R2** compares each epic task file with `.devtool/features/<name>`, or `.devtool/features/done/<name>`. The mirror is read with `](../epic/<epic_dir>/` replaced by `](`. A missing mirror or any other difference is a FAIL naming the file and the first differing line.
- **R3**: a scenario block is a `Scenario:` or `Scenario Outline:` line inside a `gherkin` fence, plus every following line up to the next scenario line, a blank line or the closing fence, all right-stripped. Each task block must equal the canonical block with the same identifier. `scenario_ids()` of `bdd_scenarios.en.md` and `bdd_scenarios.vi.md` must be equal sets.
- **R4**: the bracketed tag after the identifier on every scenario line of `bdd_scenarios.en.md` is exactly `Tier A - Unit` or `Tier C - Integration`. A missing tag fails too.
- **R5** reads the sub-bullets of each task's `Target Files & Symbols` (or `Target files and symbols`) bullet that have the form ``- `<path>`: <rest>``.
  - It checks only paths that exist and are not marked `(new)` in that task's Allowed files.
  - For each backticked identifier in `<rest>`, trailing `()` removed and the last dotted segment kept, the identifier must occur in the file's text. An identifier written as ``new `name` `` is skipped.
- **R5b** collects `/api/` routes from the task files and the HLD, cut at the first `{` and stripped of a trailing `/`. Each must occur in a file listed by `git ls-files` outside `.devtool/` and `docs/`, excluding `*.md`; otherwise WARN.
- **R6**: every task with a `Covers:` line has at least one `TIER-C` row.
  - For every `TIER-C` row, each `shlex` token that lies under an `Integration test roots` directory must also occur in an `Integration results:` command, either as the same token or under a directory token of that command.
- **R7** fails when:
  - the HLD Status starts with `Packaged` and `handoff.md` is missing;
  - `handoff.md` exists and the Status starts with none of `Packaged`, `In Progress` or `Done`;
  - the handoff's `Design commit` neither reads `uncommitted` nor resolves to a commit that is an ancestor of `HEAD`;
  - a task's `epic:` differs from `epic_slug`, or its `status` is not in `TASK_STATUSES`.
- **R7b** warns when the spec's Status line matches `draft|awaiting|under .*review|bản nháp|chờ duyệt` (case-insensitive). The spec is the `*-design.en.md` file in the epic directory.
- **R8** runs only with `--baseline`.
  - A dirty tree produces a single `R8 WARN baseline skipped: dirty tree`.
  - Otherwise every `GREEN` and `TIER-B` row whose command names no path marked `(new)` in any epic task runs with `run_task_checks.run_command(command, root, row_timeout)`.
  - A row that times out, or where `run_task_checks.mismatch(row, code, text)` is not `None`, is a WARN `<task>:<row id> <reason>`.

#### `run_external_review.py` (changed)

```python
KINDS = ("code", "principal")
PRINCIPAL_PROMPT = SCRIPTS.parent.parent / "references" / "principal-review-prompt.md"
PRINCIPAL_RULES = SCRIPTS.parent.parent / "references" / "principal-review-rules.md"

def review_file(kind: str) -> tuple[str, str]
    # "code" -> ("review_results.md", "Cross-Model Review"); "principal" -> ("principal_review.md", "Principal Review")
def principal_artefact_lines(root: Path, epic_dir: str) -> str
def run_principal(root: Path, args: argparse.Namespace, sha: str) -> int
```

- **`--kind`** (choices `KINDS`, default `code`) is added to the `run`, `check` and `triage` parsers.
- **Shared selector**: `record_round`, `check` and `triage` take the file name and the title of a new file from `review_file(getattr(args, "kind", "code"))`. With `code`, every byte they read or write is unchanged.
- **`run` with `--kind principal`**:
  1. `--cli ollama` prints `--kind principal supports --cli claude or codex` and exits 2.
  2. The PATH check and the clean-tree check run as today.
  3. `run_principal` runs `run_gate("check_epic_readiness.py", [sys.executable, SCRIPTS / "check_epic_readiness.py", args.epic_dir], root, args.facts_timeout)`. A `PreconditionFailedError` goes through `print_gate_banner` and exits 2.
  4. The prompt is filled with `Template(PRINCIPAL_PROMPT.read_text()).safe_substitute(rules=…, sha=sha, base=args.base, base_sha=<git rev-parse args.base>, epic_dir=f".devtool/epic/{args.epic_dir}", artefacts=principal_artefact_lines(...), readiness_output=<gate stdout>)`.
  5. `execute(cli_command(args.cli, args.model), root, args.timeout, prompt)` runs the reviewer, and `tree_changes` is computed around it as today.
  6. `record_round(root, args, sha, [Pass("principal", code, out, err, prompt)], changed, {"Kind": "principal"})` records the round.
- **`principal_artefact_lines`** lists the spec pair, the HLD pair, the BDD pair, every `task_*.md` and `handoff.md` when present. It never lists `review_results.md` or `principal_review.md`.
- **Unchanged**: `audit_epic.py` and the integration commands never run for `--kind principal`, and no diff is built.

#### Principal Review prompt and rules (new)

- **`principal-review-prompt.md`** casts the reader as the Principal Reviewer who signs off the epic before implementation.
  - It is strictly read-only, and must read the source at `$sha`.
  - It carries `$rules`, `$sha`, `$base`, `$base_sha`, `$epic_dir`, `$artefacts`, `$readiness_output` and checklist P1–P8 from the spec.
  - It ends with the code review's output contract: no severity tags above the verdict block, then `Verdict: PASS` or `Verdict: CHANGES REQUIRED`, then `[Critical|Important|Minor] <artefact>:<location> — <problem>. Proposed: <edit>`.
- **`principal-review-rules.md`** states the severity meanings:
  - Critical: the goal or Gate 4 is unreachable as designed;
  - Important: Stop-and-Report, or wrong behaviour;
  - Minor: wording.

  It also says the readiness report is already proven, so the review spends its effort on judgement and source grounding, and that a claim about the source must name the file and line it read.

#### `sync_task_status.py` (changed)

```python
def parse_worktree_branches(output: str) -> list[tuple[Path, str | None]]
def epic_checkout_roots(epic_dir: str) -> list[Path]
```

- **`parse_worktree_branches`** reads `git worktree list --porcelain`. Each entry yields its `worktree` path and `branch` ref, or `None` when the worktree is detached.
- **`epic_checkout_roots`**:
  - returns the current `git rev-parse --show-toplevel`, plus every worktree whose branch is `refs/heads/epic/<epic_slug>`;
  - takes `epic_slug` from `find_epic_slug(current_root, epic_dir)`, falling back to `epic_dir`;
  - deduplicates, keeping order.
- **`main`**: only the `epic` subcommand uses it. `task`, `archive-epic` and `archive-done` keep `checkout_roots()`.

#### Workflow text (changed)

- **`dev-lifecycle/SKILL.md`**:
  - packaging step 1 becomes one command, `python3 "$SCRIPTS"/check_epic_readiness.py <epic_dir>`, which must exit 0;
  - step 7 prints the handoff path and Resume Prompt;
  - a new step 8 presents **Principal Review Choice** and follows `references/principal-review.md`;
  - Red Flags gains "Picking the Principal Review CLI for the developer" and "Acting on a Principal Review finding before triage";
  - every pinned token stays, and the file stays at or under 2500 words.
- **`dev-lifecycle/references/principal-review.md`** (new): the procedure of spec §6, the choice wording, the D2 recommendation, the commit titles and the Done rule (see the clarifications).
- **`dev-implementation/SKILL.md`**:
  - Entry-Point Detection gains `test -f .devtool/epic/<epic_dir>/principal_review.md && python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --kind principal --epic-dir <epic_dir>`;
  - Phase 1 step 3 and Resume Gate 3 both state the Principal Review status (`not run`, `round <n>: PASS` or `round <n>: decided`), and stop on exit 1.
- **`handoff-template.md`**: Read First gains `4. .devtool/epic/<epic_dir>/principal_review.md, when present — Principal Review rounds and decisions.`
- **`docs/lifecycles.en.md` and `docs/lifecycles.vi.md`**: the Stage 2 diagram gains `PRC{"Principal Review Choice"}`, `PKG --> PRC`, `PRC -->|"1. Done"| …`, `PRC -->|"2. Principal Review"| PR` and `PR -->|"revised and re-packaged"| PKG`, plus one paragraph.

### Clarifications of the Spec

These formalize gaps the spec left open; none changes an approved decision.

| # | Clarification | Why |
|---|---|---|
| C1 | R7's reverse direction accepts `In Progress` and `Done`: a resumed epic keeps its `handoff.md` | The spec's "and the reverse" would fail every resumed epic |
| C2 | Each recorded round is committed as `[EPIC_NAME] Record Principal Review round <n>`, and its decisions as `[EPIC_NAME] Record Principal Review decisions for round <n>` | `run` refuses a dirty tree, so a round must be committed before the next one |
| C3 | Done re-runs the packaging procedure when `git log -1 --format=%s -- .devtool/epic/<epic_dir>` is not `[<EPIC_NAME>] Package epic for handoff` | Keeps the handoff staleness command pinned by `test_lf_st_02` exact without changing it |
| C4 | The readiness report's first line carries the task count | The packaging step 2 token "`<N>` is the task count the preflight printed" is pinned |
| C5 | R8 evaluates rows with `run_task_checks.run_command` and `mismatch` | One definition of a row's Expect |

### Shift-Left Impact Analysis

`check_code_impact.py` ran on the planned files against `main`; its coverage table reports 0% for
files that have paired suites, which is the known false alarm, so callers were confirmed by `grep`.

- `run_external_review.py`: called by `dev-implementation/SKILL.md` (Review Choice),
  `review-triage.md`, `local-review-setup.md`, `local_review.py`, `rules/CRITICAL_RULES.md`, and
  tested by `test_run_external_review.py`, `test_local_review.py`, `scripts/test_lifecycle_document_contract.py`,
  `scripts/test_verifiable_handoff_text.py`. Every new path sits behind `--kind principal`.
- `sync_task_status.py`: called by `dev-lifecycle`, `dev-implementation`, `dev-designer`, `doc-implementation`,
  `finishing-a-development-branch`, `subagent-driven-development`, and tested by
  `test_sync_task_status.py`, `scripts/test_lifecycle_signals.py`, `scripts/test_verifiable_handoff.py`.
  Only the `epic` subcommand's roots change.
- `dev-lifecycle/SKILL.md`: 2454 words of a 2500 ceiling; tokens pinned by
  `test_lifecycle_document_contract.py`, `test_lifecycle_signals.py` and `test_verifiable_handoff_text.py`.
- `scripts/verify.sh` lists test files explicitly; the new suite must be added.
- No cross-platform bridges.

## Integration Test Plan and Boundary Matrix

Integration test roots: skills/dev-implementation/resources/scripts/, scripts/
    CLI --> RDY{"check_epic_readiness.py passes?"}
    RDY -->|"no: 0 credits"| FIXR["Fix the mechanical failures"]
    FIXR --> PKG
    RDY -->|"yes"| RUN["run_external_review.py run --kind principal"]
    RUN --> TRI["Triage with the developer"]
    TRI --> DEC["Developer decides each finding"]
    DEC --> REV["Revise the epic in place, commit"]
    REV --> PKG
```

## 5. Components

### 5.1 `check_epic_readiness.py`

Location: `skills/dev-implementation/resources/scripts/`, beside the scripts it reuses.

```bash
python3 "$SCRIPTS"/check_epic_readiness.py <epic_dir> [--baseline] [--row-timeout 600]
```

| Check | Rule | Severity |
|---|---|---|
| R1 Preflight | `compute_execution_order.py` exits 0. The scan matches as many tasks as the epic directory holds. `check_bdd_traceability.py plan` and `check_task_contract.py --design` exit 0. `check_document.py` passes with `--require-toc --require-bilingual` on the spec, HLD and BDD pairs, with `--require-toc` on `handoff.md` when present, and on every task file | FAIL |
| R2 Mirror parity | Each `.devtool/epic/<epic_dir>/task_*.md` equals its mirror in `.devtool/features/` (or `features/done/`) once the location-dependent `Epic:` and `Spec:` links are normalised | FAIL |
| R3 Scenario parity | Each scenario block in a task equals the canonical block in `bdd_scenarios.en.md`, tier tag included; `bdd_scenarios.vi.md` carries the same identifier set | FAIL |
| R4 Tier tags | Every scenario is tagged `[Tier A - Unit]` or `[Tier C - Integration]`; Tier B is tooling only | FAIL |
| R5 Grounding | In each task's `Target Files & Symbols`, every symbol listed for a file that exists and is not `(new)` occurs in that file, unless the bullet marks it `new` | FAIL |
| R5b Routes | Every `/api/...` route named in a task or the HLD occurs in a tracked source file outside `.devtool/` and `docs/` | WARN |
| R6 Gate 4 coverage | Every task with a `Covers:` line has a `TIER-C` row, and every path argument of a `TIER-C` row that points into an `Integration test roots` directory is named by, or lies under a directory named by, an `Integration results:` command of the HLD | FAIL |
| R7 Metadata | An HLD Status of `Packaged` comes with `handoff.md` and the reverse. The handoff's design commit resolves and is an ancestor of `HEAD`, unless it reads `uncommitted`. Task frontmatter names this epic and a valid status | FAIL |
| R7b Spec status | The spec Status no longer reads as a draft or as awaiting Gate 1 (`dev-brainstorming` does not update it on approval today) | WARN |
| R8 Baseline (opt-in) | With `--baseline` and a clean tree, every `GREEN` and `TIER-B` row whose command names no `(new)` path runs in the current checkout; a failure is reported with the row id and the last lines of its output | WARN |

Output: one line per check (`R1 PASS`, `R5 FAIL task_2:…: buildPersistTrackPayload not in src/…/tts-studio.js`), then
`Result: <n> FAIL, <m> WARN — PASS|FAIL`. Exit 0 with no FAIL, 1 with any FAIL, 2 on a usage error.
R8 runs in place because a packaged epic's commits change documents only, so the checkout's code
is the base the tasks will start from.

### 5.2 `run_external_review.py --kind principal`

```bash
python3 "$SCRIPTS"/run_external_review.py run --kind principal --epic-dir <epic_dir> --base <base_ref> --cli claude|codex [--model <name>] [--timeout 1800]
python3 "$SCRIPTS"/run_external_review.py check --kind principal --epic-dir <epic_dir>
python3 "$SCRIPTS"/run_external_review.py triage --kind principal --epic-dir <epic_dir>
```

- `--kind` defaults to `code`; everything the code review does today is unchanged.
- `--kind principal` with `--cli ollama` is a usage error (exit 2).
- **Preconditions**: the CLI is on PATH and the tree is clean, as today. `check_epic_readiness.py <epic_dir>` must exit 0; otherwise the existing precondition banner is printed and the CLI is not invoked.
- **Facts**: the readiness report, the base ref and its SHA, the reviewed SHA (`HEAD`), and the artefact list (spec pair, HLD pair, BDD pair, task files, `handoff.md`). No code diff is sent: the reviewer reads the source itself, read-only (`claude -p --permission-mode plan`, `codex exec --sandbox read-only`).
- **Record**: `principal_review.md` uses the round, findings-table and decision format of `review_results.md`, with `Kind: principal` in each round's metadata. `check` and `triage` read the file `--kind` selects.
- `--model` is passed through. `principal-review.md` recommends the strongest reasoning model each CLI offers.

### 5.3 Principal Review prompt and rules

New files in `skills/dev-implementation/references/`, beside the code-review prompt:
`principal-review-prompt.md` and `principal-review-rules.md`. The reviewer acts as the Principal
Reviewer who signs off the epic before implementation. It is strictly read-only and checks the
artefacts against the source at the reviewed SHA:

| # | Checklist item |
|---|---|
| P1 | Consistency across spec, HLD, BDD, tasks and `handoff.md`: decisions, field names, numbers, titles, statuses |
| P2 | Grounding: every path, symbol, signature, return type, route and constant in `Decisions Already Made` and `Impact Analysis` exists as described |
| P3 | Pinned behaviour: existing tests that pin a behaviour a task changes, when those tests are outside the task's Allowed files |
| P4 | Blast radius: other writers and readers of the changed data, background jobs, callers outside Allowed files, migrations and backfill |
| P5 | Task split and Verification: dependency order, RED rows that can fail before implementation (the behaviour is not already there), GREEN rows that can pass at baseline, DoD references, Stop conditions |
| P6 | BDD quality: valid Gherkin, dimensions that match their scenarios, grounded assertions, tier tags |
| P7 | Gate 4 feasibility: `Integration results:` covers every scenario; the Verification Environment declares every resource the rows need |
| P8 | Risks, rollout and rollback |

Output keeps the parser contract of the code review: a closing `Verdict: PASS` or
`Verdict: CHANGES REQUIRED`, then one line per finding,
`[Critical|Important|Minor] <artefact>:<location> — <problem>. Proposed: <edit>`.
The severities mean:
- **Critical**: the epic cannot reach its goal or Gate 4 as designed;
- **Important**: a task would hit Stop-and-Report or ship wrong behaviour;
- **Minor**: wording and consistency.

### 5.4 `dev-lifecycle`

- **Packaging procedure step 1**: one command, `check_epic_readiness.py <epic_dir>`, replaces the four preflight commands.
- **After step 7**: a short pointer to Principal Review Choice and `references/principal-review.md`. The new reference file carries §6, the choice wording, the D2 recommendation and the re-package rule.
- **Red Flags gains two items**: picking the Principal Review CLI for the developer, and acting on a Principal Review finding before triage.
- **Unchanged**: all invariants pinned by `test_lifecycle_document_contract.py`, and the 2500-word ceiling.

### 5.5 `dev-implementation`

Phase 0 and the Resume Procedure: when `principal_review.md` exists, run
`run_external_review.py check --kind principal --epic-dir <epic_dir>` before Gate 3. On exit 1,
stop and present the triage. The Gate 3 summary states the Principal Review status: `not run`,
`round <n>: PASS`, or `round <n>: decided`.

### 5.6 `sync_task_status.py epic`

The `epic` subcommand narrows its roots to the current checkout plus the worktrees whose branch is
`epic/<epic_slug>`. The `task`, `archive-epic` and `archive-done` subcommands keep every checkout.

### 5.7 Human documentation and template

- `docs/lifecycles.en.md` and `docs/lifecycles.vi.md` gain the Principal Review Choice loop in the Stage 2 diagram, and one paragraph.
- `handoff-template.md` lists `principal_review.md, when present` under Read First.

## 6. Principal Review Loop Procedure

1. After the packaging procedure prints `handoff.md`, present:
   > Packaged. 1. **Done** — stop here. 2. **Principal Review** — a cross-model review of the design against the source before implementation (Claude CLI or Codex CLI).

   Add the D2 recommendation when it applies.
2. **Done**: if `principal_review.md` exists, run `check --kind principal`. Exit 0 stops with the handoff path and the Resume Prompt; exit 1 goes to step 5.
3. **Principal Review**: ask which CLI, Claude CLI or Codex CLI, and optionally which model. Never choose for the developer.
4. Run `run_external_review.py run --kind principal --epic-dir <epic_dir> --base <base_branch> --cli <cli>`. A readiness FAIL prints the banner: fix the named failures as an epic revision, re-package, and return to step 1.
5. Present `triage --kind principal`, filled as `review-triage.md` describes: every finding is verified against the source at the round's SHA. Stop and wait for the developer's decision on each finding.
6. Apply each accepted finding as an in-place revision of the epic (D8). Write the Decision cells (`fixed in <sha>` or `dismissed: <developer's words>`) and commit `[EPIC_NAME] Revise epic after Principal Review round <n>`.
7. Re-run the packaging procedure from step 1: readiness, a regenerated `handoff.md` with the new design commit, lint, status, commit. Then return to step 1 of this procedure.

## 7. Error Handling

| Situation | Behaviour |
|---|---|
| CLI not on PATH, dirty tree, `--cli ollama` with `--kind principal` | Exit 2; no round recorded |
| `check_epic_readiness.py` FAIL | Precondition banner, CLI not invoked, exit 2; the report names each failure |
| R8 row exceeds `--row-timeout` | WARN `timeout` for that row; the other rows still run |
| Reviewer output has no Verdict line | Round recorded as incomplete, exit 2, as for code review |
| Reviewer changes a file despite read-only mode | Existing tree-change guard records the paths in the round |
| Developer chooses Done with undecided blocking findings | Done refused; triage presented (D9) |
| `principal_review.md` exists but cannot be parsed at Gate 3 | `check` exits 1; Gate 3 stops and names the row |

## 8. Testing

- `test_check_epic_readiness.py`: one passing and one failing fixture epic per check R1–R8, built in temporary git repositories. The failing fixtures reproduce the defect classes of §1: a missing symbol, Tier A versus Tier B drift, an uncovered `TIER-C` path, a draft spec Status, a broken mirror and a failing baseline row.
# Handoff: principal_review

## Table of Contents

- [Status](#status)
- [Identifiers](#identifiers)
- [Read First](#read-first)
- [Resume Prompt](#resume-prompt)
- [Execution Guardrails for Receiving LLM](#execution-guardrails-for-receiving-llm)
- [Open Notes](#open-notes)
- [Rules for the Receiving Agent](#rules-for-the-receiving-agent)

## Status

- **Packaged**: 2026-10-22
- **Design commit**: `34802af` — `HEAD` before the packaging commit
- **Base branch**: `main`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `<epic_dir>` | `principal_review` |
| `<epic_slug>` | `principal_review` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/principal_review/principal_review.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 5 tasks.
2. `.devtool/epic/principal_review/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md` — the approved source spec.

## Resume Prompt

```text
Use the d3nexus:dev-implementation skill for the `principal_review` epic.
Read .devtool/epic/principal_review/handoff.md first.
Apply the Execution Guardrails for Receiving LLM before presenting Gate 3.
Gates 1 and 2 are passed; do not re-run brainstorming or design.
Gate 3 is pending: present the execution order to me and wait for my confirmation.
```

## Execution Guardrails for Receiving LLM

Fast executor models and receiving agents MUST adhere to these four hard guardrails throughout implementation:

1. **Bounded context protocol**:
   - Step 1: Read only the active task file (`.devtool/features/task_*.md`).
   - Step 2: Read only the exact files declared in `Allowed files` and `Read-only context`.
   - Step 3: Look up exact symbol definitions identified under `## Decisions Already Made`.
   Undirected whole-repository searches (`grep`, `find`, `list_dir`) are forbidden unless an unresolved import explicitly requires symbol lookup.
2. **Strict spec fidelity**: Frozen constants, defaults, retry counts, fallback conditions, signatures, and call paths under `## Decisions Already Made` and the HLD are hard contracts. Any mismatch causes STOP and report rather than an executor-side simplification.
3. **Zero test fakery**: Tests import or invoke real production symbols and do not reconstruct retry loops, progress math, callback behavior, or configuration resolution.
4. **No contract repair by the executor**: The receiver never edits Verification tables, Allowed files, Definition of Done, Covers lines, protected paths, or frozen contract facts.

## Open Notes

- **Decisions taken with the developer (2026-10-22)**:
  1. Principal Review is an **optional** choice offered after every Package, worded like Review Choice: `1. Done` or `2. Principal Review`. The developer picks Claude CLI or Codex CLI; the agent never picks. It is not a mandatory gate.
  2. Approach A: extend `run_external_review.py` with `--kind principal` rather than a separate engine. Parallel dual-model review and reviewer-written patches are out of scope.
  3. The `sync_task_status.py epic` scope fix (Task 4) is in scope. It caused real uncommitted edits in another epic's worktree in `lyrics-sync` on 2026-10-22, and the Principal Review loop re-packages on every round.
  4. The HLD's clarifications C1–C5 formalize gaps in the spec and change no decision. C3 exists because `test_lf_st_02` pins the handoff staleness command, which must stay byte-identical.
- **Origin**: a manual pre-implementation review of `lyrics-sync`'s `flashcard_compact_data_enrichment` found the defect classes listed in the spec's Background. Its packaged commit `5cc7d720` is a good Gate 5 trial target for `check_epic_readiness.py`, in a scratch worktree, never in the live checkout.
- **Baseline at `34802af`**:
  - `scripts/verify.sh` prints `PASS — safe to publish`.
  - The guard suites pass: `test_run_external_review.py`, `test_local_review.py`, `test_sync_task_status.py`, `test_lifecycle_document_contract.py`, `test_lifecycle_signals.py`, `test_verifiable_handoff_text.py` and `test_verifiable_handoff.py`.
  - Existing lint and type debt kept out of Tier B rows: `test_run_external_review.py` (14 ruff, 1 mypy) and `test_sync_task_status.py` (66 strict mypy).
  - Task 4 clears the 8 ruff and 3 mypy findings in `sync_task_status.py`.
- **Tooling**:
  - On the design machine, `ruff` 0.16.9 and `mypy` 2.3.1 resolved from another project's virtualenv. Before Gate 3, confirm both are on `PATH` in the implementation shell, or every TIER-B row will fail for a reason other than its Expect.
  - Finding counts can differ with other versions; a Tier B row that fails at baseline on a file the task did not create is a Stop-and-Report.
- **Word budget**: `skills/dev-lifecycle/SKILL.md` is 2454 of 2500 words. Task 5 frees words by replacing the four preflight commands with one.
- **Known limit of R5**: it checks only `- \`<path>\`: <symbols>` sub-bullets. Older epics that write `Target files and symbols` inline (`module.symbol`) are skipped, not failed. That is acceptable for this release.
- **Self-reference**: this epic was packaged with the four-command preflight, because `check_epic_readiness.py` does not exist yet.
- **Base branch**: this repository merges epics into `main` and has no `develop`. Where `dev-implementation` mentions fast-forwarding `develop`, read `main`.

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- Unless the design commit is `uncommitted`: if `git log 34802af..main -- .devtool/epic/principal_review` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
- This file is a dated record. It is never updated after packaging.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.

exec
/bin/zsh -lc 'nl -ba skills/dev-lifecycle/references/principal-review.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
     1	# Principal Review Loop Procedure
     2	
     3	Principal Review is a cross-model review of an epic's architecture and task designs against the source repository before implementation begins. It catches grounded misunderstandings, missing contracts, and scope regressions while fixing them in documents is cheap.
     4	
     5	## Procedure
     6	
     7	1. After the packaging procedure prints `handoff.md`, present the Principal Review Choice to the developer:
     8	
     9	   > Packaged.
    10	   > 1. **Done** — stop here.
    11	   > 2. **Principal Review** — a cross-model review of the design against the source before implementation (Claude CLI or Codex CLI).
    12	
    13	   Add the recommendation when it applies:
    14	   - When the epic design was authored by a fast model or when the developer requests review, cross-model review is strongly recommended before committing to implementation.
    15	   - Never choose for the developer. Always wait for explicit selection.
    16	
    17	2. **Done**:
    18	   If `.devtool/epic/<epic_dir>/principal_review.md` exists, run:
    19	   ```bash
    20	   python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --kind principal --epic-dir <epic_dir>
    21	   ```
    22	   - If this check exits 1 (undecided blocking findings exist), refusal is enforced: proceed to step 5 (triage).
    23	   - If this check exits 0, check whether the epic documents were revised:
    24	     ```bash
    25	     git log -1 --format=%s -- .devtool/epic/<epic_dir>
    26	     ```
    27	     When the last commit touching the epic directory is not `[<EPIC_NAME>] Package epic for handoff`, re-run the packaging procedure from step 1 (readiness check, regenerated `handoff.md`, lint, status, and package commit).
    28	     Then print the `handoff.md` path and the Resume Prompt, and stop.
    29	
    30	3. **Principal Review**:
    31	   Ask the developer which CLI to use — Claude CLI or Codex CLI — and optionally which model. Never choose for the developer.
    32	
    33	4. Run the principal review:
    34	   ```bash
    35	   python3 "$SKILL_DIR"/resources/scripts/run_external_review.py run --kind principal --epic-dir <epic_dir> --base <base_branch> --cli <claude|codex>
    36	   ```
    37	   - A readiness FAIL prints the precondition banner: the CLI is never invoked. Fix the named failures as an epic revision, re-package, and return to step 1.
    38	   - On success, the round is recorded in `.devtool/epic/<epic_dir>/principal_review.md`. Commit the recorded round:
    39	     ```bash
    40	     git commit -m "[<EPIC_NAME>] Record Principal Review round <n>"
    41	     ```
    42	
    43	5. Present the review triage for the latest principal round:
    44	   ```bash
    45	   python3 "$SKILL_DIR"/resources/scripts/run_external_review.py triage --kind principal --epic-dir <epic_dir>
    46	   ```
    47	   Fill the triage by verifying every finding against the source at the round's SHA, following the discipline in [review-triage.md](../../dev-implementation/references/review-triage.md). Stop calling tools and wait for the developer's decision on each finding.
    48	
    49	6. Apply each accepted finding as an in-place revision of the epic documents.
    50	   - Record the decisions in `.devtool/epic/<epic_dir>/principal_review.md` (e.g. `fixed in <sha>` or `dismissed: <developer's words>`).
    51	   - Commit decisions:
    52	     ```bash
    53	     git commit -m "[<EPIC_NAME>] Record Principal Review decisions for round <n>"
    54	     ```
    55	   - Commit the document revision:
    56	     ```bash
    57	     git commit -m "[<EPIC_NAME>] Revise epic after Principal Review round <n>"
    58	     ```
    59	
    60	7. Re-run the packaging procedure from step 1:
    61	   - Run `check_epic_readiness.py <epic_dir>`.
    62	   - Update `handoff.md` with the new design commit SHA.
    63	   - Lint `handoff.md`.
    64	   - Sync epic status to `Packaged`.
    65	   - Commit: `[<EPIC_NAME>] Package epic for handoff`.
    66	   - Return to step 1 of this procedure and present the Principal Review Choice again.
    67	
    68	## Guidelines and References
    69	
    70	For detailed guidelines on how to verify reviewer claims, assess validity, and record decisions, refer to [review-triage.md](../../dev-implementation/references/review-triage.md).

exec
/bin/zsh -lc 'nl -ba skills/dev-implementation/references/principal-review-prompt.md; nl -ba skills/dev-implementation/references/principal-review-rules.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
     1	# Principal Review Prompt
     2	
     3	You are the Principal Reviewer who signs off this epic before implementation. You are strictly read-only: do not modify, create, or delete any file, and do not run commands that write to the repository or alter git state. Read the artefacts, inspect the source at `$sha`, and report.
     4	
     5	## Candidate
     6	
     7	- Commit under review: `$sha`
     8	- Base the epic branched from: `$base`
     9	- Base commit: `$base_sha`
    10	- Epic directory: `$epic_dir`
    11	
    12	## Artefacts
    13	
    14	Read these paths, relative to the repository root:
    15	
    16	$artefacts
    17	
    18	## Readiness facts
    19	
    20	The pre-review readiness report from `check_epic_readiness.py`:
    21	
    22	```text
    23	$readiness_output
    24	```
    25	
    26	The readiness report is already proven: all facts above have passed their mechanical checks; do not restate them, spend your review on judgement and grounding.
    27	
    28	## Rules
    29	
    30	$rules
    31	
    32	## Checklist
    33	
    34	- **P1 (Consistency)**: Consistency across spec, HLD, BDD, tasks and `handoff.md`: decisions, field names, numbers, titles, statuses.
    35	- **P2 (Grounding)**: Grounding: every path, symbol, signature, return type, route and constant in `Decisions Already Made` and `Impact Analysis` exists as described.
    36	- **P3 (Pinned behaviour)**: Pinned behaviour: existing tests that pin a behaviour a task changes, when those tests are outside the task's Allowed files.
    37	- **P4 (Blast radius)**: Blast radius: other writers and readers of the changed data, background jobs, callers outside Allowed files, migrations and backfill.
    38	- **P5 (Task split and Verification)**: Task split and Verification: dependency order, RED rows that can fail before implementation (the behaviour is not already there), GREEN rows that can pass at baseline, DoD references, Stop conditions.
    39	- **P6 (BDD quality)**: BDD quality: valid Gherkin, dimensions that match their scenarios, grounded assertions, tier tags.
    40	- **P7 (Gate 4 feasibility)**: Gate 4 feasibility: `Integration results:` covers every scenario; the Verification Environment declares every resource the rows need.
    41	- **P8 (Risks, rollout and rollback)**: Risks, rollout and rollback.
    42	
    43	## Required output
    44	
    45	Do NOT use the bracketed tags `[Critical]`, `[Important]`, or `[Minor]` anywhere in your prose or analysis above the final verdict block.
    46	
    47	End your answer with these exact lines and nothing after them (no markdown bolding `**`, no backticks, no bullet before `Verdict:`):
    48	
    49	Verdict: PASS
    50	(or `Verdict: CHANGES REQUIRED`)
    51	[Critical|Important|Minor] <artefact>:<location> — <problem>. Proposed: <edit>
    52	
    53	Rules for Severity & Verdict:
    54	- Use `Critical` for a defect that breaks the epic's goal, `Important` for one that must be fixed before implementation, and `Minor` for anything else.
    55	- Output `Verdict: CHANGES REQUIRED` if and only if there is at least one `Critical` or `Important` finding.
    56	- If there are no findings (or only `Minor` findings), you MUST output `Verdict: PASS`.
    57	- A review with no finding still ends with its `Verdict: PASS` line.
     1	# Principal Review Rules
     2	
     3	To avoid false-positive findings, evaluate the epic against these principles:
     4	
     5	1. **Severities**:
     6	   - **Critical**: The epic cannot reach its goal or Gate 4 as designed.
     7	   - **Important**: A task would hit Stop-and-Report or ship wrong behaviour.
     8	   - **Minor**: Wording, formatting, and minor consistency adjustments.
     9	
    10	2. **Readiness Report Is Proven Fact**:
    11	   - The mechanical checks (R1–R8) in `check_epic_readiness.py` are already validated.
    12	   - Do not re-verify mechanically checked facts or restate them as findings; spend your review effort on judgement, architecture, and source grounding.
    13	
    14	3. **Grounding in Active Source**:
    15	   - Every claim about the repository source code must name the specific file and line number read.
    16	   - Grounding verifies that referenced symbols, functions, methods, and configurations actually exist at `$sha`.
    17	
    18	4. **Actionable Findings**:
    19	   - Each finding must name the specific artefact (file path) and location (heading or section) to change.
    20	   - Each finding must conclude with a concrete `Proposed: <edit>` recommendation.

exec
/bin/zsh -lc 'git diff --unified=80 main...c09cb95593c5908098462a0a2963f1a300d9efcb -- skills/dev-implementation/resources/scripts/run_external_review.py' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
exec
/bin/zsh -lc 'git diff --unified=80 main...c09cb95593c5908098462a0a2963f1a300d9efcb -- skills/dev-implementation/resources/scripts/sync_task_status.py' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 1838ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-aX3LuiFD' (errno=Operation not permitted)
2026-10-23 17:45:35.411 xcodebuild[26252:2217815]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:35.550 xcodebuild[26252:2217812] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-OKpQyz3v' (errno=Operation not permitted)
2026-10-23 17:45:36.079 xcodebuild[26256:2217836]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:36.234 xcodebuild[26256:2217833] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
diff --git a/skills/dev-implementation/resources/scripts/run_external_review.py b/skills/dev-implementation/resources/scripts/run_external_review.py
index 8e2cbc7..a976758 100755
--- a/skills/dev-implementation/resources/scripts/run_external_review.py
+++ b/skills/dev-implementation/resources/scripts/run_external_review.py
@@ -1,117 +1,164 @@
 #!/usr/bin/env python3
 """Review of a finished epic through the Claude CLI, the Codex CLI, or a model served by a local Ollama.
 
 Usage:
   run_external_review.py run --epic-dir <epic_dir> --base <base_ref> --cli claude|codex [--model <name>] [--timeout 1800] [--facts-timeout 300] [--diff-limit 1500]
   run_external_review.py run --epic-dir <epic_dir> --base <base_ref> --cli ollama --model <name> [--host <url>] [--num-ctx <tokens>] [--timeout 1800]
   run_external_review.py check --epic-dir <epic_dir>
   run_external_review.py triage --epic-dir <epic_dir>
 
 `run` exit codes: 0 a completed round without a Critical or Important finding; 1 a completed round with
 one; 2 every other outcome, including CHANGES REQUIRED with no finding line (the round is recorded whenever
 the reviewer ran). `check` exit codes: 0 nothing undecided; 1 a Critical or Important finding of the latest
 completed round has no decision, or a findings row cannot be read. `triage` prints the latest round as a
 skeleton to fill before acting on it, with a comparison of every round; exit 0, or 2 with no round.
 """
 from __future__ import annotations
 
 import argparse
 import os
 import re
 import shlex
 import shutil
 import signal
 import subprocess
 import sys
 import time
 from dataclasses import dataclass
 from datetime import UTC, datetime
 from pathlib import Path
 from string import Template
 
 import local_review
 from task_contract import ContractError, git_run, parse_integration_results
 
 SCRIPTS = Path(__file__).resolve().parent
 PROMPT = SCRIPTS.parent.parent / "references" / "external-review-prompt.md"
 RULES = SCRIPTS.parent.parent / "references" / "review-rules.md"
+KINDS = ("code", "principal")
+PRINCIPAL_PROMPT = SCRIPTS.parent.parent / "references" / "principal-review-prompt.md"
+PRINCIPAL_RULES = SCRIPTS.parent.parent / "references" / "principal-review-rules.md"
+
+
+def review_file(kind: str) -> tuple[str, str]:
+    if kind == "principal":
+        return ("principal_review.md", "Principal Review")
+    return ("review_results.md", "Cross-Model Review")
+
+
+def principal_artefact_lines(root: Path, epic_dir: str) -> str:
+    epic_path = root / ".devtool" / "epic" / epic_dir
+    lines: list[str] = []
+
+    # 1. *-design.en.md and *-design.vi.md
+    for f in sorted(epic_path.glob("*-design.en.md")):
+        lines.append(f"- `.devtool/epic/{epic_dir}/{f.name}`")
+    for f in sorted(epic_path.glob("*-design.vi.md")):
+        lines.append(f"- `.devtool/epic/{epic_dir}/{f.name}`")
+
+    # 2. <epic_dir>.en.md and <epic_dir>.vi.md
+    for ext in (".en.md", ".vi.md"):
+        doc = epic_path / f"{epic_dir}{ext}"
+        if doc.is_file():
+            line = f"- `.devtool/epic/{epic_dir}/{doc.name}`"
+            if line not in lines:
+                lines.append(line)
+
+    # 3. bdd_scenarios.en.md and bdd_scenarios.vi.md
+    for ext in (".en.md", ".vi.md"):
+        doc = epic_path / f"bdd_scenarios{ext}"
+        if doc.is_file():
+            line = f"- `.devtool/epic/{epic_dir}/{doc.name}`"
+            if line not in lines:
+                lines.append(line)
+
+    # 4. every task_*.md, sorted
+    for t in sorted(epic_path.glob("task_*.md")):
+        lines.append(f"- `.devtool/epic/{epic_dir}/{t.name}`")
+
+    # 5. handoff.md when present
+    handoff = epic_path / "handoff.md"
+    if handoff.is_file():
+        lines.append(f"- `.devtool/epic/{epic_dir}/handoff.md`")
+
+    return "\n".join(lines)
 
 # Tolerates optional markdown headings, bullet prefixes, and bold markers around Verdict.
 VERDICT = re.compile(
     r"^\s*(?:#+\s*|[-*+]\s*)?\*{0,2}Verdict(?:(?:\*{0,2}:)|(?::\*{0,2}))\s*\*{0,2}(PASS|CHANGES REQUIRED)\*{0,2}\s*$",
     re.IGNORECASE,
 )
 # Tolerates list numbering, bullets and ** around the severity, and —, –, - or : between location and problem.
 FINDING = re.compile(
     r"^\s*(?:[-*+]|\d+[.)])?\s*\*{0,2}\[\*{0,2}(Critical|Important|Minor)\*{0,2}\]\*{0,2}\s*"
     r"(\S.*?)(?:\s+[—–-]|\s*:)\s+(\S.*)$",
     re.IGNORECASE,
 )
 # Only catch unparsed blocking tags when they appear on a list-like or tag-leading line to avoid prose false positives.
 UNPARSED_BLOCKING = re.compile(
     r"^\s*(?:[-*+]|\d+[.)])?\s*\*{0,2}\[\*{0,2}(Critical|Important)\*{0,2}\]",
     re.IGNORECASE,
 )
 FINDING_ROW = re.compile(r"^\|\s*\d+\s*\|")
 META_LINE = re.compile(r"^- \*\*(.+?)\*\*: (.*)$")
 PASS_HEADER = re.compile(r"^### Pass (\d+): (.+)$")
 NEXT_STEPS = ("To be written after verifying every finding: Fix commits, decisions, a confirmation round, "
               "then Gate 4 in full.")
 BLOCKING = ("Critical", "Important")
 FENCE = re.compile(r"^(`{3,})")
 
 MAX_DIFF_LINES = 1500
 MAX_DIFF_BYTES = 60_000
 
 RED = "\033[1;31m"
 GREEN = "\033[1;32m"
 YELLOW = "\033[1;33m"
 CYAN = "\033[1;36m"
 RESET = "\033[0m"
 
 EXCLUDES = (
     # 1. Common Locks, Build & Devtool
     ":(exclude)*.lock",
     ":(exclude)*-lock.*",
     ":(exclude)*.lockfile",
     ":(exclude)**/Package.resolved",
     ":(exclude)build/**",
     ":(exclude).devtool/**",
     # 2. Flutter / Dart Codegen & FFI Bridge
     ":(exclude)*.g.dart",
     ":(exclude)*.freezed.dart",
     ":(exclude)*.gr.dart",
     ":(exclude)*.config.dart",
     ":(exclude)*.mocks.dart",
     ":(exclude)*.chopper.dart",
     ":(exclude)*.pigeon.*",
     ":(exclude)*frb_generated*",
     ":(exclude)**/l10n/app_localizations*.dart",
     # 3. iOS Native (Xcode metadata, assets & UI layout XML)
     ":(exclude)*.pbxproj",
     ":(exclude)*.xcworkspacedata",
     ":(exclude)*.xcscheme",
     ":(exclude)*.storyboard",
     ":(exclude)*.xib",
     ":(exclude)**/*.xcassets/**",
     ":(exclude)*.xcstrings",
     # 4. Android Native (Gradle wrapper & Baseline profiles)
     ":(exclude)gradlew",
     ":(exclude)gradlew.bat",
     ":(exclude)**/gradle/wrapper/**",
     ":(exclude)**/baseline-prof.txt",
     # 5. Rust & Python Generated / Snapshots
     ":(exclude)*.generated.*",
     ":(exclude)*_pb2.py",
     ":(exclude)*_pb2_grpc.py",
     ":(exclude)*_pb2.pyi",
     ":(exclude)**/.sqlx/**",
     ":(exclude)**/__snapshots__/**",
     ":(exclude)*.snap",
     ":(exclude)*.ambr",
     # 6. Minified Web Assets & Source Maps
     ":(exclude)*.min.js",
     ":(exclude)*.min.css",
     ":(exclude)*.map",
 )
 
@@ -244,411 +291,452 @@ def build_diff_section(root: Path, base: str, sha: str, max_lines: int = MAX_DIF
         )
 
     return (
         stat_block
         + f"The source diff is large ({line_count} lines, {byte_size // 1024} KB > inline budget). "
         f"Do NOT run an unfiltered `git diff`; inspect specific target files via `git diff {base}...{sha} -- <path>` as needed."
     )
 
 
 def cli_command(cli: str, model: str | None) -> list[str]:
     extra = ["--model", model] if model else []
     if cli == "claude":
         return ["claude", "-p", "--permission-mode", "plan", *extra]
     return ["codex", "exec", "--sandbox", "read-only", *extra, "-"]
 
 
 def cell(text: str) -> str:
     return text.replace("|", "\\|").replace("\r", "").replace("\n", " ").strip()
 
 
 def fence_for(text: str) -> str:
     longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
     return "`" * max(3, longest + 1)
 
 
 def rounds_in(text: str) -> list[tuple[int, list[str]]]:
     """Split review_results.md into (number, lines) rounds, ignoring headings inside fenced raw output."""
     rounds: list[tuple[int, list[str]]] = []
     fence = ""
     for line in text.splitlines():
         match = FENCE.match(line)
         if fence:
             fence = "" if line.rstrip() == fence else fence
         elif match:
             fence = match.group(1)
         elif (heading := re.fullmatch(r"## Round (\d+)", line)):
             rounds.append((int(heading.group(1)), []))
             continue
         if rounds:
             rounds[-1][1].append(line)
     return rounds
 
 
 def split_row(line: str) -> list[str]:
     return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
 
 
 def metadata(lines: list[str]) -> list[str]:
     """A round's own lines: its fields and findings table, never its raw output."""
     return lines[:lines.index("Raw output:")] if "Raw output:" in lines else lines
 
 
 def table_findings(lines: list[str]) -> list[tuple[str, list[str]]]:
     """(line, cells) for every findings row, `| <number> |` onwards, well formed or not."""
     return [(line, split_row(line)) for line in metadata(lines) if FINDING_ROW.match(line)]
 
 
 def parse_findings(out: str, verdict: str | None = None) -> list[tuple[str, str, str]]:
     """Each finding line as (severity, location, problem); a blocking line in list format keeps its raw text."""
     findings = []
     for line in out.splitlines():
         if (match := FINDING.match(line)):
             sev, loc, problem = match.groups()
             findings.append((sev.capitalize(), loc, problem))
         elif (blocking := UNPARSED_BLOCKING.search(line)):
             if verdict == "PASS" and not findings:
                 continue
             findings.append((blocking.group(1).capitalize(), "unparsed", line.strip()))
     return findings
 
 
 def render_round(number: int, meta: dict[str, str], findings: list[tuple[str, str, str]], output: str) -> str:
     head = "".join(f"- **{key}**: {value}\n" for key, value in meta.items())
     table = "| # | Severity | Location | Problem | Decision |\n|---|----------|----------|---------|----------|\n"
     table += "".join(f"| {i} | {sev} | {cell(loc)} | {cell(problem)} |  |\n"
                      for i, (sev, loc, problem) in enumerate(findings, 1))
     fence = fence_for(output)
     return f"## Round {number}\n\n{head}\n{table}\nRaw output:\n\n{fence}text\n{output.rstrip()}\n{fence}\n"
 
 
+def run_principal(root: Path, args: argparse.Namespace, sha: str) -> int:
+    facts_timeout = getattr(args, "facts_timeout", 300)
+    check_cmd = [sys.executable, str(SCRIPTS / "check_epic_readiness.py"), args.epic_dir]
+    try:
+        _code, out, _err = run_gate("check_epic_readiness.py", check_cmd, root, facts_timeout)
+    except PreconditionFailedError as error:
+        print_gate_banner(error, args.cli)
+        return 2
+
+    base_sha = git_run(root, "rev-parse", "--verify", args.base).decode().strip()
+    readiness_output = out.rstrip()
+
+    prompt = Template(PRINCIPAL_PROMPT.read_text(encoding="utf-8")).safe_substitute(
+        rules=PRINCIPAL_RULES.read_text(encoding="utf-8").strip(),
+        sha=sha,
+        base=args.base,
+        base_sha=base_sha,
+        epic_dir=f".devtool/epic/{args.epic_dir}",
+        artefacts=principal_artefact_lines(root, args.epic_dir),
+        readiness_output=readiness_output,
+    )
+
+    before = status_lines(root)
+    code, out, err = execute(cli_command(args.cli, args.model), root, args.timeout, prompt)
+    changed = tree_changes(root, before, sha)
+    return record_round(root, args, sha, [Pass("principal", code, out, err, prompt)], changed, {"Kind": "principal"})
+
+
 def run(args: argparse.Namespace) -> int:
+    if getattr(args, "kind", "code") == "principal" and args.cli == "ollama":
+        print("--kind principal supports --cli claude or codex", file=sys.stderr)
+        return 2
+
     if args.cli == "ollama":
         if not args.model:
             print("--cli ollama needs --model", file=sys.stderr)
             return 2
     elif not shutil.which(args.cli):
         print(f"{args.cli} not found on PATH", file=sys.stderr)
         return 2
     root = Path(git_run(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
     if status_lines(root):
         print("commit or stash your changes before a review", file=sys.stderr)
         return 2
     sha = head_of(root)
+
+    if getattr(args, "kind", "code") == "principal":
+        return run_principal(root, args, sha)
     model_ctx = None
     if args.cli == "ollama":
         try:
             model_ctx = local_review.probe(args.host, args.model)
         except local_review.LocalReviewError as error:
             print_gate_banner(PreconditionFailedError("Ollama probe", str(error)), args.cli)
             return 2
     hld_text = (root / ".devtool" / "epic" / args.epic_dir / f"{args.epic_dir}.en.md").read_text(encoding="utf-8")
     try:
         facts_timeout = getattr(args, "facts_timeout", 300)
         audit_output, results_output = collect_facts(root, args.epic_dir, args.base, hld_text, facts_timeout)
     except PreconditionFailedError as error:
         print_gate_banner(error, args.cli)
         return 2
     if args.cli == "ollama":
         return run_local(root, args, sha, audit_output, results_output, model_ctx)
     diff_limit = getattr(args, "diff_limit", MAX_DIFF_LINES)
     diff_section = build_diff_section(root, args.base, sha, max_lines=diff_limit)
     prompt = Template(PROMPT.read_text(encoding="utf-8")).safe_substitute(
         rules=RULES.read_text(encoding="utf-8").strip(),
         sha=sha,
         base=args.base,
         epic_dir=f".devtool/epic/{args.epic_dir}",
         artefacts=artefact_lines(root, args.epic_dir),
         audit_output=audit_output.rstrip(),
         results_output=results_output.rstrip(),
         diff_section=diff_section,
     )
     before = status_lines(root)  # after the facts: running the test commands may write build output
     code, out, err = execute(cli_command(args.cli, args.model), root, args.timeout, prompt)
     changed = tree_changes(root, before, sha)
     return record_round(root, args, sha, [Pass("review", code, out, err, prompt)], changed, {})
 
 
 def live_log_dir(root: Path, epic_dir: str) -> Path:
     """Where each pass streams its output: build/local-review/<epic_dir> when Git ignores it, else the Git directory.
 
     Either place leaves `git status` untouched, so the logs never trip the tree-modified check."""
     visible = root / "build" / "local-review" / epic_dir
     if subprocess.run(["git", "check-ignore", "-q", str(visible)], cwd=root, check=False).returncode == 0:
         return visible
     return root / git_run(root, "rev-parse", "--git-path", f"local-review/{epic_dir}").decode().strip()
 
 
 def run_local(root: Path, args: argparse.Namespace, sha: str, audit_output: str, results_output: str,
               model_ctx: int | None) -> int:
     """Fit every slice before the first call, then review them one at a time; the first failed pass ends the run."""
     ctx = args.num_ctx or model_ctx or local_review.DEFAULT_NUM_CTX
     planned: list[tuple[local_review.Slice, str]] = []
     try:
         for slice_ in local_review.build_slices(root, args.epic_dir, args.base, sha, audit_output, results_output,
                                                 EXCLUDES):
             system = local_review.render_system(slice_)
             budget = int(ctx * local_review.PROMPT_SHARE) - local_review.estimate_tokens(system)
             planned.append((local_review.fit(slice_, budget), system))
     except local_review.LocalReviewError as error:
         print_gate_banner(PreconditionFailedError("Context budget", str(error)), args.cli)
         return 2
     logs = live_log_dir(root, args.epic_dir)
     logs.mkdir(parents=True, exist_ok=True)
     print(f"{CYAN}Live logs:{RESET} {logs}", file=sys.stderr, flush=True)
     before = status_lines(root)
     passes: list[Pass] = []
     for number, (slice_, system) in enumerate(planned, 1):
         user = local_review.render_user(slice_)
         prompt_tokens = local_review.estimate_tokens(system) + local_review.estimate_tokens(user)
         options = local_review.chat_options(model_ctx, args.num_ctx, prompt_tokens)
         print(f"{CYAN}⏳ [Pass {number}/{len(planned)}]{RESET} {slice_.label} ... ", end="", file=sys.stderr, flush=True)
         started = time.monotonic()
         reply = local_review.chat(args.host, args.model, system, user, options, args.timeout,
                                   logs / f"{number}-{slice_.label}.log")
         code = 0 if reply.error is None else None if reply.error.startswith("timed out") else 1
         passes.append(Pass(slice_.label, code, reply.content, reply.error or "", user, slice_.omitted,
                            reply.done_reason))
         if reply.error is not None or reply.done_reason != "stop":
             print(f"{RED}❌ {reply.error or f'done_reason {reply.done_reason}'}{RESET}", file=sys.stderr, flush=True)
             break
         print(f"{GREEN}✅ {round(time.monotonic() - started)}s{RESET}", file=sys.stderr, flush=True)
     changed = tree_changes(root, before, sha)
     return record_round(root, args, sha, passes, changed, {"Passes": str(len(planned)), "Context": str(ctx)})
 
 
 @dataclass(frozen=True)
 class Pass:
     label: str
     code: int | None  # 0 transport success, None timeout, otherwise failure
     out: str  # the text the parser reads
     err: str
     shown: str  # what the reviewer was shown
     omitted: tuple[str, ...] = ()
     done_reason: str | None = None
 
 
 def tree_changes(root: Path, before: list[str], sha: str) -> list[str]:
     """Status lines that appeared or vanished since `before`, led by HEAD when it moved."""
     changed = sorted(set(status_lines(root)) ^ set(before))
     if head_of(root) != sha:
         changed.insert(0, "HEAD")
     return changed
 
 
 def path_of(location: str) -> str:
     """The file a finding points at: its location before the first colon, without backticks."""
     return location.split(":", 1)[0].strip().strip("`")
 
 
 def annotate(finding: tuple[str, str, str], shown: str) -> tuple[str, str, str]:
     """Mark a blocking finding whose location path the reviewer was never shown; its severity stays."""
     sev, loc, problem = finding
     if sev in BLOCKING and loc != "unparsed" and path_of(loc) not in shown:
         problem += " (location not shown to reviewer)"
     return sev, loc, problem
 
 
 def pass_output(item: Pass, number: int, args: argparse.Namespace) -> str:
     if args.cli == "ollama":
         return f"### Pass {number}: {item.label}\n\n{item.out}" + (f"\n--- error ---\n{item.err}" if item.err.strip() else "")
     output = item.out + (f"\n--- stderr ---\n{item.err}" if item.err.strip() else "")
     if item.code is None:
         output += f"\n--- timed out after {args.timeout} seconds ---\n"
     return output
 
 
 def record_round(root: Path, args: argparse.Namespace, sha: str, passes: list[Pass],
                  changed: list[str], extra: dict[str, str]) -> int:
     """Append one round to review_results.md from every pass of a review; return the run's exit code."""
     local = args.cli == "ollama"
     verdicts: list[str | None] = []
     findings: list[tuple[str, str, str]] = []
     complete = True
     for item in passes:
         lines = item.out.splitlines()
         marks = [(index, m.group(1).upper()) for index, line in enumerate(lines) if (m := VERDICT.match(line))]
         verdict = marks[-1][1] if marks else None
         if local:  # a draft line in the Analysis above the verdict block is never a finding
             block = "\n".join(lines[marks[-1][0]:]) if marks else ""
             found = [annotate(finding, item.shown) for finding in parse_findings(block, verdict)]
         else:
             found = parse_findings(item.out, verdict)
         verdicts.append(verdict)
         findings.extend(found)
         complete = complete and item.code == 0 and verdict is not None \
             and not (verdict == "CHANGES REQUIRED" and not found) and (not local or item.done_reason == "stop")
     if changed:
         status = f"discarded: tree modified ({', '.join(line[3:] if line != 'HEAD' else line for line in changed)})"
     else:
         status = "completed" if complete else "no verdict"
     if "CHANGES REQUIRED" in verdicts:
         verdict_text = "CHANGES REQUIRED"
     else:
         verdict_text = "PASS" if verdicts and None not in verdicts else "none"
-    path = root / ".devtool" / "epic" / args.epic_dir / "review_results.md"
-    existing = path.read_text(encoding="utf-8") if path.exists() else f"# Cross-Model Review: {args.epic_dir}\n"
+    name, title = review_file(getattr(args, "kind", "code"))
+    path = root / ".devtool" / "epic" / args.epic_dir / name
+    existing = path.read_text(encoding="utf-8") if path.exists() else f"# {title}: {args.epic_dir}\n"
     round_num = len(rounds_in(existing)) + 1
     meta = {
         "Date": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
         "SHA": sha,
         "Base": args.base,
         "CLI": args.cli,
         "Model": args.model or "default",
         "Status": status,
         "Verdict": verdict_text,
         **extra,
     }
     if (omitted := "; ".join(f"{item.label}: {', '.join(item.omitted)}" for item in passes if item.omitted)):
         meta["Omitted"] = omitted
     output = "\n\n".join(pass_output(item, number, args) for number, item in enumerate(passes, 1))
     text = existing.rstrip("\n") + "\n\n" + render_round(round_num, meta, findings, output)
     path.write_text(text, encoding="utf-8")
     print(f"Round {round_num}: {status} ({path.relative_to(root)})")
     if status != "completed":
         return 2
     return 1 if any(sev in BLOCKING for sev, _, _ in findings) else 0
 
 
 def check(args: argparse.Namespace) -> int:
     root = Path(git_run(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
-    path = root / ".devtool" / "epic" / args.epic_dir / "review_results.md"
+    name, _ = review_file(getattr(args, "kind", "code"))
+    path = root / ".devtool" / "epic" / args.epic_dir / name
     if not path.exists():
         return 0
     completed = [(n, lines) for n, lines in rounds_in(path.read_text(encoding="utf-8"))
                  if "- **Status**: completed" in metadata(lines)]
     undecided = []
     for line, cells in table_findings(completed[-1][1]) if completed else []:
         if len(cells) != 5:
             undecided.append(f"undecided: unreadable findings row: {line.strip()}")
         elif cells[1] in BLOCKING and not cells[4].startswith(("fixed in ", "dismissed: ")):
             undecided.append(f"undecided: #{cells[0]} {cells[1]} {cells[2]}")
     if undecided:
         print("\n".join(undecided))
     return 1 if undecided else 0
 
 
 def round_meta(lines: list[str]) -> dict[str, str]:
     """A round's `- **Key**: value` fields."""
     return {m.group(1): m.group(2) for line in metadata(lines) if (m := META_LINE.match(line))}
 
 
 def round_output(lines: list[str]) -> str:
     """The fenced raw output of a round, without its fence."""
     body = lines[lines.index("Raw output:") + 1:] if "Raw output:" in lines else []
     fences = [(index, match.group(1)) for index, line in enumerate(body) if (match := FENCE.match(line))]
     if not fences:
         return ""
     start, fence = fences[0]
     end = next((i for i in range(start + 1, len(body)) if body[i].rstrip() == fence), len(body))
     return "\n".join(body[start + 1:end])
 
 
 def round_passes(output: str) -> list[tuple[str, str, str]]:
     """(pass, verdict, error) for each `### Pass` block, or one `review` pass when there is none."""
     blocks: list[tuple[str, list[str]]] = []
     for line in output.splitlines():
         if (header := PASS_HEADER.match(line)):
             blocks.append((f"{header.group(1)} {header.group(2)}", []))
         elif blocks:
             blocks[-1][1].append(line)
     rows = []
     for name, lines in blocks or [("review", output.splitlines())]:
         verdicts = [m.group(1).upper() for line in lines if (m := VERDICT.match(line))]
         after = lines[lines.index("--- error ---") + 1:] if "--- error ---" in lines else []
         rows.append((name, verdicts[-1] if verdicts else "none", after[0].strip() if after else "—"))
     return rows
 
 
 def finding_rows(lines: list[str]) -> list[list[str]]:
     return [cells for _, cells in table_findings(lines) if len(cells) == 5]
 
 
 def comparison_row(number: int, lines: list[str]) -> str:
     meta, rows = round_meta(lines), finding_rows(lines)
     counts = [sum(cells[1] == severity for cells in rows) for severity in ("Critical", "Important", "Minor")]
     fixed = sum(cells[4].startswith("fixed in ") for cells in rows)
     dismissed = sum(cells[4].startswith("dismissed: ") for cells in rows)
     undecided = sum(cells[1] in BLOCKING and not cells[4].startswith(("fixed in ", "dismissed: ")) for cells in rows)
     values = [str(number), f"{meta.get('CLI', '?')} / {meta.get('Model', '?')}", meta.get("SHA", "?")[:7],
               meta.get("Status", "?"), meta.get("Verdict", "?"), *map(str, [*counts, fixed, dismissed, undecided])]
     return "| " + " | ".join(cell(value) for value in values) + " |"
 
 
 def since_lines(previous: list[list[str]], latest: list[list[str]]) -> list[str]:
     """What became of the previous round's blocking or fixed findings, compared by file path."""
     lines = []
     for cells in previous:
         fixed = cells[4].startswith("fixed in ")
         if cells[1] not in BLOCKING and not fixed:
             continue
         again = [f"#{row[0]}" for row in latest if path_of(row[2]) == path_of(cells[2])]
         if again:
             lines.append(f"- {cells[2]}: re-reported at the same path ({', '.join(again)})"
                          + (" — check the fix" if fixed else ""))
         else:
             lines.append(f"- {cells[2]}: not re-reported")
     return lines or ["No blocking or fixed finding in the previous round."]
 
 
 def triage(args: argparse.Namespace) -> int:
     """Print the latest round as a skeleton to fill, verify and present before any action on its findings."""
     root = Path(git_run(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
-    path = root / ".devtool" / "epic" / args.epic_dir / "review_results.md"
+    name, _ = review_file(getattr(args, "kind", "code"))
+    path = root / ".devtool" / "epic" / args.epic_dir / name
     rounds = rounds_in(path.read_text(encoding="utf-8")) if path.exists() else []
     if not rounds:
         print(f"no review round recorded for {args.epic_dir}", file=sys.stderr)
         return 2
     number, lines = rounds[-1]
     meta = round_meta(lines)
     out = [f"# Review Triage: {args.epic_dir}, Round {number}", "",
            *(f"- **{key}**: {meta.get(key, '?')}" for key in ("SHA", "CLI", "Model", "Status", "Verdict")), "",
            "## Passes", "", "| Pass | Verdict | Error |", "|------|---------|-------|",
            *(f"| {cell(name)} | {verdict} | {cell(error)} |" for name, verdict, error in round_passes(round_output(lines))),
            "", "## Findings", ""]
     latest = finding_rows(lines)
     if latest:
         out += ["| # | Severity | Location | Problem | Assessment | Evidence | Proposed action |",
                 "|---|----------|----------|---------|------------|----------|-----------------|",
                 *(f"| {cells[0]} | {cells[1]} | {cell(cells[2])} | {cell(cells[3])} | ? | ? | ? |" for cells in latest)]
     else:
         out.append("None.")
     out += ["", "## Round Comparison", "",
             "| Round | CLI / Model | SHA | Status | Verdict | Critical | Important | Minor | Fixed | Dismissed | Undecided |",
             "|-------|-------------|-----|--------|---------|----------|-----------|-------|-------|-----------|-----------|",
             *(comparison_row(n, round_lines) for n, round_lines in rounds), ""]
     if len(rounds) > 1:
         out += [f"## Since Round {rounds[-2][0]}", "", *since_lines(finding_rows(rounds[-2][1]), latest)]
     else:
         out += ["## Since the Previous Round", "", "No earlier round."]
     out += ["", "## Next Steps", "", NEXT_STEPS]
     print("\n".join(out))
     return 0
 
 
 def main(argv: list[str] | None = None) -> int:
     parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
     modes = parser.add_subparsers(dest="mode", required=True)
     runner = modes.add_parser("run", help="have the CLI review the epic and record a round")
+    runner.add_argument("--kind", choices=KINDS, default="code")
     runner.add_argument("--epic-dir", required=True)
     runner.add_argument("--base", required=True)
     runner.add_argument("--cli", required=True, choices=("claude", "codex", "ollama"))
     runner.add_argument("--model")
     runner.add_argument("--host", default=local_review.host_from_env())
     runner.add_argument("--num-ctx", type=int, default=None)
     runner.add_argument("--timeout", type=int, default=1800)
     runner.add_argument("--facts-timeout", type=int, default=300)
     runner.add_argument("--diff-limit", type=int, default=MAX_DIFF_LINES)
     checker = modes.add_parser("check", help="list undecided blocking findings of the latest completed round")
+    checker.add_argument("--kind", choices=KINDS, default="code")
     checker.add_argument("--epic-dir", required=True)
     triager = modes.add_parser("triage", help="print the latest round as a skeleton to fill before acting on it")
+    triager.add_argument("--kind", choices=KINDS, default="code")
     triager.add_argument("--epic-dir", required=True)
     args = parser.parse_args(argv)
     try:
         return {"run": run, "check": check, "triage": triage}[args.mode](args)
     except (ContractError, OSError) as error:
         print(f"error: {error}", file=sys.stderr)
         return 2
 
 
 if __name__ == "__main__":
     sys.exit(main())

 succeeded in 1837ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-lJLA5Ltk' (errno=Operation not permitted)
2026-10-23 17:45:35.411 xcodebuild[26253:2217814]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:35.550 xcodebuild[26253:2217811] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-TWgdo9ys' (errno=Operation not permitted)
2026-10-23 17:45:36.079 xcodebuild[26257:2217835]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:36.234 xcodebuild[26257:2217834] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
diff --git a/skills/dev-implementation/resources/scripts/sync_task_status.py b/skills/dev-implementation/resources/scripts/sync_task_status.py
index 0f9d8a1..630beb7 100755
--- a/skills/dev-implementation/resources/scripts/sync_task_status.py
+++ b/skills/dev-implementation/resources/scripts/sync_task_status.py
@@ -1,527 +1,583 @@
 #!/usr/bin/env python3
 """Mirror one epic task's Kanban status across every checkout of this repo.
 
 `dev-implementation` runs an epic inside an isolated worktree, but the same
 task files are also checked out in the main workspace -- and `dev-designer`
 writes each task twice, into `.devtool/features/` and into
 `.devtool/epic/<epic_dir>/`. Writing a status to only one of those four copies
 leaves every other Kanban board stale for the whole epic.
 
 This script writes them all:
 
     sync_task_status.py task <task_id> <status>
     sync_task_status.py epic <epic_dir> <status>
 
 `task` mode rewrites `status`, `modified`, and -- on `done` -- `completedAt` in
 the frontmatter of every copy of that task, in every checkout `git worktree
 list` reports. `epic` mode rewrites the Meta Data `Status` line of the Epic
 Overview's `.en.md` and `.vi.md` together, so the pair can never diverge.
 
 Only matched lines change; every other key and the whole document body survive
 byte-for-byte. Frontmatter is parsed with the same hand-rolled regex idiom as
 compute_execution_order.py -- deliberately no PyYAML, so this stays stdlib-only.
 """
 import re
 import subprocess
-from datetime import datetime, timezone
 import sys
+from datetime import UTC, datetime
 from pathlib import Path
 
 sys.path.insert(0, str(Path(__file__).parent))
 from slug_utils import parse_frontmatter, sanitize_slug
 
 TASK_STATUSES = ("backlog", "todo", "in-progress", "review", "done")
 FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
 
 
 def now_iso() -> str:
     """UTC, seconds precision, Zulu suffix -- e.g. 2026-09-14T10:23:45Z."""
-    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
+    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
 
 
 def set_frontmatter_field(text: str, key: str, value: str | None) -> str:
     """Set `key: "value"` or `key: null` inside the leading frontmatter block only.
 
     A key that is absent is inserted directly after `status:`, so task files
     written before this script existed (no `modified`, no `completedAt`) keep
     working instead of silently losing the field. Body text is never scanned.
     """
     match = FRONTMATTER_RE.match(text)
     if not match:
         return text
     block = match.group(1)
     if value is None or value == "null":
         new_line = f"{key}: null"
     else:
         new_line = f'{key}: "{value}"'
-    key_re = re.compile(rf"^{re.escape(key)}\s*:.*$", re.M)
+    key_re = re.compile(rf"^{re.escape(key)}\s*:.*$", re.MULTILINE)
     if key_re.search(block):
         new_block = key_re.sub(lambda _m: new_line, block, count=1)
     else:
-        status_re = re.compile(r"^status\s*:.*$", re.M)
+        status_re = re.compile(r"^status\s*:.*$", re.MULTILINE)
         if status_re.search(block):
             new_block = status_re.sub(lambda m: m.group(0) + "\n" + new_line, block, count=1)
         else:
             new_block = block + "\n" + new_line
     return text[:match.start(1)] + new_block + text[match.end(1):]
 
 
 def parse_worktree_list(output: str) -> list[Path]:
     """Extract checkout roots from `git worktree list --porcelain` output.
 
     Git always reports the main worktree first, and callers rely on that
     ordering -- Phase 4's main-checkout restore uses roots[0]. Paths may
     contain spaces, so take everything after the first token.
     """
     return [Path(line[len("worktree "):]) for line in output.splitlines()
             if line.startswith("worktree ")]
 
 
+def parse_worktree_branches(output: str) -> list[tuple[Path, str | None]]:
+    """Extract (path, branch) pairs from `git worktree list --porcelain` output.
+
+    Branch is the full ref string (e.g. 'refs/heads/epic/name') or None if detached.
+    """
+    entries: list[tuple[Path, str | None]] = []
+    current_path: Path | None = None
+    current_branch: str | None = None
+
+    for line in output.splitlines():
+        if line.startswith("worktree "):
+            if current_path is not None:
+                entries.append((current_path, current_branch))
+            current_path = Path(line[len("worktree "):])
+            current_branch = None
+        elif line.startswith("branch "):
+            current_branch = line[len("branch "):]
+        elif line == "detached":
+            current_branch = None
+
+    if current_path is not None:
+        entries.append((current_path, current_branch))
+
+    return entries
+
+
 def checkout_roots() -> list[Path]:
     """Every checkout of this repo, main worktree first.
 
     The only subprocess boundary in this module -- everything else is pure and
     directly testable, which is why the test suite needs no git fixtures.
     """
     result = subprocess.run(["git", "worktree", "list", "--porcelain"],
                             capture_output=True, text=True, check=True)
     return parse_worktree_list(result.stdout)
 
 
+def epic_checkout_roots(epic_dir: str) -> list[Path]:
+    """Return the current checkout root plus every worktree on branch refs/heads/epic/<epic_slug>.
+
+    Current checkout is always first. Other worktrees are included only if their branch
+    matches this epic's slug.
+    """
+    top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
+                         capture_output=True, text=True, check=True)
+    current_root = Path(top.stdout.strip())
+
+    wt_result = subprocess.run(["git", "worktree", "list", "--porcelain"],
+                               capture_output=True, text=True, check=True)
+    entries = parse_worktree_branches(wt_result.stdout)
+
+    slug = find_epic_slug(current_root, epic_dir) or epic_dir
+    target_branch = f"refs/heads/epic/{slug}"
+
+    roots: list[Path] = [current_root]
+    seen = {current_root.resolve()}
+
+    for path, branch in entries:
+        if branch == target_branch:
+            resolved = path.resolve()
+            if resolved not in seen:
+                seen.add(resolved)
+                roots.append(path)
+
+    return roots
+
+
 def task_targets(root: Path, task_id: str) -> list[Path]:
     """Every copy of one task inside one checkout: features, features/done, + each epic dir."""
     candidates = [
         root / ".devtool" / "features" / f"{task_id}.md",
         root / ".devtool" / "features" / "done" / f"{task_id}.md",
     ]
     candidates.extend(sorted((root / ".devtool" / "epic").glob(f"*/{task_id}.md")))
     return [path for path in candidates if path.is_file()]
 
 
 def epic_of(path: Path) -> str | None:
     val = parse_frontmatter(path.read_text()).get("epic")
     return sanitize_slug(val) if val else None
 
 
 def expected_epic(roots: list[Path], task_id: str) -> str | None:
     """The epic this task_id belongs to, per the authoritative features copy (or epic copy if archived).
 
     Task ids are `task_<number>_<name>`, so a name like `task_1_setup` can
     plausibly exist under two different epics -- and `task_targets`' `*/` glob
     would match both. Callers use this value to refuse any copy whose own
     `epic:` differs. Checked main-worktree-first; mirrors cannot disagree.
     """
     for root in roots:
         for features_dir in (root / ".devtool" / "features", root / ".devtool" / "features" / "done"):
             features = features_dir / f"{task_id}.md"
             if features.is_file():
                 return epic_of(features)
         for epic_copy in sorted((root / ".devtool" / "epic").glob(f"*/{task_id}.md")):
             if epic_copy.is_file():
                 return epic_of(epic_copy)
     return None
 
 
 def sync_task(roots: list[Path], task_id: str, new_status: str) -> tuple[list[Path], list[str]]:
     """Synchronize a task's status across all checkout roots."""
     exp_epic = expected_epic(roots, task_id)
     written: list[Path] = []
     notes: list[str] = []
     now = now_iso()
 
     for root in roots:
         targets = task_targets(root, task_id)
         for path in targets:
             file_epic = epic_of(path)
             if exp_epic and file_epic and file_epic != exp_epic:
                 notes.append(f"Skipped {path}: belongs to epic '{file_epic}', expected '{exp_epic}'")
                 continue
             text = path.read_text()
             text = set_frontmatter_field(text, "status", new_status)
             text = set_frontmatter_field(text, "modified", now)
             if new_status == "done":
                 text = set_frontmatter_field(text, "completedAt", now)
             else:
                 fm = parse_frontmatter(text)
                 if "completedAt" in fm and fm["completedAt"] != "null":
                     text = set_frontmatter_field(text, "completedAt", "null")
             path.write_text(text)
             written.append(board_location(root, path, new_status))
 
     return written, notes
 
 
 def board_location(root: Path, path: Path, status: str) -> Path:
     """Move a features copy into features/done when it becomes done, and back when it leaves done.
 
     Epic mirrors stay put. A copy already at the target is replaced by the one just written.
     """
     features = root / ".devtool" / "features"
     if status == "done" and path.parent == features:
         target = features / "done" / path.name
     elif status != "done" and path.parent == features / "done":
         target = features / path.name
     else:
         return path
     target.parent.mkdir(parents=True, exist_ok=True)
     path.replace(target)
     return target
 
 
 def board_tally(roots: list[Path], epic_slug: str) -> dict[str, int]:
     """Tally task counts per status for the given epic, counting each task once."""
     tally = {status: 0 for status in TASK_STATUSES}
     seen_tasks: set[str] = set()
     for root in roots:
         search_dirs = [
             root / ".devtool" / "features",
             root / ".devtool" / "features" / "done",
         ]
         search_dirs.extend(sorted((root / ".devtool" / "epic").glob("*")))
         for features_dir in search_dirs:
             if not features_dir.is_dir():
                 continue
             for path in sorted(features_dir.glob("task_*.md")):
                 task_id = path.stem
                 if task_id in seen_tasks:
                     continue
                 fm = parse_frontmatter(path.read_text())
                 if fm.get("epic") == epic_slug:
                     seen_tasks.add(task_id)
                     status = fm.get("status")
                     if status in tally:
                         tally[status] += 1
     return tally
 
 
 def find_epic_slug(root: Path, epic_dir: str) -> str | None:
     """Find the epic slug from the epic's HLD overview or contained tasks."""
     epic_path = root / ".devtool" / "epic" / epic_dir
     if not epic_path.is_dir():
         return None
     for ext in (".en.md", ".vi.md"):
         doc = epic_path / f"{epic_dir}{ext}"
         if doc.is_file():
-            match = re.search(r"^-\s*\*\*(?:Epic)\*\*:\s*(.+)$", doc.read_text(), re.M)
+            match = re.search(r"^-\s*\*\*(?:Epic)\*\*:\s*(.+)$", doc.read_text(), re.MULTILINE)
             if match:
                 slug = sanitize_slug(match.group(1))
                 if slug:
                     return slug
     for task_file in sorted(epic_path.glob("task_*.md")):
         slug = epic_of(task_file)
         if slug:
             return slug
     return sanitize_slug(epic_dir)
 
 
 def find_epic_dir_for_slug(root: Path, epic_slug: str) -> str | None:
     """Find the epic directory name matching the given epic slug."""
     epics_parent = root / ".devtool" / "epic"
     if not epics_parent.is_dir():
         return None
     for sub in sorted(epics_parent.iterdir()):
         if not sub.is_dir():
             continue
         slug = find_epic_slug(root, sub.name)
         if slug == epic_slug:
             return sub.name
     # Fallback to name heuristic: replace hyphens with underscores
     candidate = epic_slug.replace("-", "_")
     if (epics_parent / candidate).is_dir():
         return candidate
     return None
 
 
 
 def fix_task_markdown_links(text: str, epic_dir: str) -> str:
     """Rewrite task links when relocated into .devtool/epic/<epic_dir>/."""
     text = re.sub(rf"\]\(\.\./epic/{re.escape(epic_dir)}/([^)]+)\)", r"](\1)", text)
     text = re.sub(r"\]\(\.\./\.\./features/(?:done/)?(task_[^)]+\.md)\)", r"](\1)", text)
     return text
 
 
 def fix_epic_overview_links(text: str) -> str:
     """Rewrite Section 8 links in <epic_dir>.en.md / .vi.md to local task_*.md."""
     return re.sub(r"\]\(\.\./\.\./features/(?:done/)?(task_[^)]+\.md)\)", r"](\1)", text)
 
 
 def archive_superpowers_docs(root: Path, epic_dir: str, epic_slug: str | None) -> list[Path]:
     """Relocate any specs or plans matching this epic from docs/superpowers/ to the epic dir."""
     moved: list[Path] = []
     dest_dir = root / ".devtool" / "epic" / epic_dir
     if not dest_dir.is_dir():
         return moved
     patterns = {epic_dir}
     if epic_slug:
         patterns.add(epic_slug)
         patterns.add(epic_slug.replace("-", "_"))
         patterns.add(epic_slug.replace("_", "-"))
 
     for sub in ("plans", "specs"):
         sp_dir = root / "docs" / "superpowers" / sub
         if not sp_dir.is_dir():
             continue
         for f in sorted(sp_dir.glob("*.md")):
             if any(pat in f.name for pat in patterns):
                 dest_file = dest_dir / f.name
                 if not dest_file.exists():
                     f.rename(dest_file)
                     moved.append(dest_file)
                 else:
                     f.unlink()
                     moved.append(dest_file)
         non_keep = [f for f in sp_dir.iterdir() if f.name != ".gitkeep"]
         if not non_keep:
             (sp_dir / ".gitkeep").touch()
     return moved
 
 
 def archive_epic_tasks(roots: list[Path], epic_dir: str) -> tuple[list[Path], list[Path]]:
     """Move all done tasks of an epic from features/done into .devtool/epic/<epic_dir>/,
 
     clean up source files, rewrite links to local format, and retain .gitkeep.
     Returns (archived_files, cleaned_source_files).
     """
     archived: list[Path] = []
     cleaned: list[Path] = []
 
     for root in roots:
         dest_dir = root / ".devtool" / "epic" / epic_dir
         dest_dir.mkdir(parents=True, exist_ok=True)
         epic_slug = find_epic_slug(root, epic_dir)
 
         # 1. Relocate task files from features and features/done
         for fdir in (root / ".devtool" / "features", root / ".devtool" / "features" / "done"):
             if not fdir.is_dir():
                 continue
             for task_file in sorted(fdir.glob("task_*.md")):
                 file_epic = epic_of(task_file)
-                target_slug = epic_slug or sanitize_slug(epic_dir)
+                target_slug = epic_slug or sanitize_slug(epic_dir) or epic_dir
                 target_slugs = {target_slug, target_slug.replace("-", "_"), target_slug.replace("_", "-")}
                 if file_epic and file_epic not in target_slugs:
                     continue
                 dest_file = dest_dir / task_file.name
                 content = task_file.read_text()
                 content = fix_task_markdown_links(content, epic_dir)
                 dest_file.write_text(content)
                 archived.append(dest_file)
                 task_file.unlink()
                 cleaned.append(task_file)
 
         # 2. Ensure existing tasks in dest_dir have clean links
         for task_file in sorted(dest_dir.glob("task_*.md")):
             content = task_file.read_text()
             fixed = fix_task_markdown_links(content, epic_dir)
             if fixed != content:
                 task_file.write_text(fixed)
                 if task_file not in archived:
                     archived.append(task_file)
 
         # 3. Fix Section 8 links in epic overview documents (.en.md and .vi.md)
         for ext in (".en.md", ".vi.md"):
             doc = dest_dir / f"{epic_dir}{ext}"
             if doc.is_file():
                 doc_content = doc.read_text()
                 fixed_doc = fix_epic_overview_links(doc_content)
                 if fixed_doc != doc_content:
                     doc.write_text(fixed_doc)
 
         # 4. Relocate superpowers specs & plans if any exist for this epic
         archive_superpowers_docs(root, epic_dir, epic_slug)
 
         # 5. Ensure .gitkeep exists in features/done if directory is empty
         done_dir = root / ".devtool" / "features" / "done"
         if done_dir.is_dir():
             non_keep = [f for f in done_dir.iterdir() if f.name != ".gitkeep"]
             if not non_keep:
                 (done_dir / ".gitkeep").touch()
 
     return archived, cleaned
 
 
 def sync_epic(roots: list[Path], epic_dir: str, new_status: str) -> tuple[list[Path], list[Path]]:
     """Update Status line in Meta Data for both .en.md and .vi.md across all checkouts.
 
     Returns (matched_docs, written_docs).
     """
     matched: list[Path] = []
     written: list[Path] = []
-    status_re = re.compile(r"^(-\s*\*\*(?:Status|Trạng thái)(?:\*\*:\s*|:\*\*\s*)).*$", re.M)
+    status_re = re.compile(r"^(-\s*\*\*(?:Status|Trạng thái)(?:\*\*:\s*|:\*\*\s*)).*$", re.MULTILINE)
     for root in roots:
         epic_path = root / ".devtool" / "epic" / epic_dir
         if not epic_path.is_dir():
             continue
         for ext in (".en.md", ".vi.md"):
             doc = epic_path / f"{epic_dir}{ext}"
             if not doc.is_file():
                 continue
             matched.append(doc)
             text = doc.read_text()
             if status_re.search(text):
                 new_text = status_re.sub(rf"\g<1>{new_status}", text)
                 if new_text != text:
                     doc.write_text(new_text)
                 written.append(doc)
 
     if new_status.strip().lower() in ("done", "hoàn thành"):
         archive_epic_tasks(roots, epic_dir)
 
     return matched, written
 
 
 def archive_all_done_epics(roots: list[Path]) -> list[str]:
     """Find all completed tasks in .devtool/features/done/ and archive them into their epics.
 
     Returns the list of epic_dirs that were archived and marked Done.
     """
     epics_to_archive: set[str] = set()
     for root in roots:
         done_dir = root / ".devtool" / "features" / "done"
         if not done_dir.is_dir():
             continue
         for task_file in sorted(done_dir.glob("task_*.md")):
             slug = epic_of(task_file)
             if slug:
                 epic_dir = find_epic_dir_for_slug(root, slug)
                 if epic_dir:
                     epics_to_archive.add(epic_dir)
 
     archived_dirs: list[str] = []
     for epic_dir in sorted(epics_to_archive):
         sync_epic(roots, epic_dir, "Done")
         archived_dirs.append(epic_dir)
 
     return archived_dirs
 
 
 def code_epic_dir(root: Path, task_id: str) -> str | None:
     """The epic directory of this checkout's copy of the task when that epic is a code epic, else None."""
     from task_contract import is_code_epic
 
     for features in (root / ".devtool" / "features", root / ".devtool" / "features" / "done"):
         if (features / f"{task_id}.md").is_file():
             slug = epic_of(features / f"{task_id}.md")
             epic_dir = find_epic_dir_for_slug(root, slug) if slug else None
             if epic_dir and is_code_epic(root / ".devtool" / "epic" / epic_dir / f"{epic_dir}.en.md"):
                 return epic_dir
             return None
     return None
 
 
 def done_gate_failures(task_id: str) -> list[str]:
     """Messages refusing `task <id> done` for a code epic's task; empty when the gate does not apply or passes."""
     from task_contract import ContractError, evaluate_done_gate, section
 
-    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
+    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=False, capture_output=True, text=True)
     if top.returncode != 0:
         return []
     root = Path(top.stdout.strip())
     epic_dir = code_epic_dir(root, task_id)
     if epic_dir is None:
         if (any(code_epic_dir(other, task_id) for other in checkout_roots() if other.resolve() != root.resolve())
                 and not task_targets(root, task_id)):
             return ["run the done gate in the checkout that holds the task and its evidence (the epic worktree)"]
         return []
     mirror = root / ".devtool" / "epic" / epic_dir / f"{task_id}.md"
     if not mirror.is_file() or section(mirror.read_text(encoding="utf-8"), "Verification") is None:
-        return [f"retrofit required: {mirror} has no Verification section — retrofit it through "
-                "dev-designer's Updating an Existing Epic"]
+        return [(f"retrofit required: {mirror} has no Verification section — retrofit it through "
+                "dev-designer's Updating an Existing Epic")]
     try:
         return evaluate_done_gate(mirror)
     except ContractError as error:
         return [f"condition 1: {error}"]
 
 
 def main() -> None:
     import argparse
     import sys
 
     parser = argparse.ArgumentParser(
         description="Mirror one epic task's Kanban status across every checkout of this repo."
     )
     subparsers = parser.add_subparsers(dest="command", required=True)
 
     task_parser = subparsers.add_parser("task", help="Sync task status")
     task_parser.add_argument("task_id", help="Task ID (e.g. task_1_setup)")
     task_parser.add_argument("status", help=f"New status ({', '.join(TASK_STATUSES)})")
 
     epic_parser = subparsers.add_parser("epic", help="Sync epic overview status")
     epic_parser.add_argument("epic_dir", help="Epic directory name (e.g. logging_refactor)")
     epic_parser.add_argument("status", help="New status string (e.g. 'In Progress')")
 
     archive_parser = subparsers.add_parser(
         "archive-epic", help="Archive done tasks of an epic into .devtool/epic/<epic_dir>/"
     )
     archive_parser.add_argument("epic_dir", help="Epic directory name (e.g. logging_refactor)")
 
-    archive_done_parser = subparsers.add_parser(
+    subparsers.add_parser(
         "archive-done",
         help="Find all completed tasks in .devtool/features/done/ and archive them into their respective epic directories",
     )
 
     args = parser.parse_args()
 
     if args.command == "task":
         if args.status not in TASK_STATUSES:
             sys.stderr.write(
                 f"Invalid status '{args.status}'. Expected one of: {', '.join(TASK_STATUSES)}\n"
             )
             sys.exit(2)
 
         failures = done_gate_failures(args.task_id) if args.status == "done" else []
         if failures:
             sys.stderr.write(f"refused: {args.task_id} cannot be marked done\n")
             for failure in failures:
                 sys.stderr.write(f"  {failure}\n")
             sys.exit(1)
 
         roots = checkout_roots()
         written, notes = sync_task(roots, args.task_id, args.status)
         for note in notes:
             sys.stderr.write(f"Note: {note}\n")
 
         if not written:
             sys.stderr.write(f"Warning: No copies of task '{args.task_id}' found in any checkout.\n")
             sys.exit(1)
 
         exp_epic = expected_epic(roots, args.task_id)
         if exp_epic:
             tally = board_tally(roots, exp_epic)
             tally_str = ", ".join(f"{k}: {v}" for k, v in tally.items())
             print(
                 f"Updated {len(written)} copies of {args.task_id} -> '{args.status}' "
                 f"[Epic '{exp_epic}': {tally_str}]"
             )
         else:
             print(f"Updated {len(written)} copies of {args.task_id} -> '{args.status}'")
 
     elif args.command == "epic":
-        roots = checkout_roots()
+        roots = epic_checkout_roots(args.epic_dir)
         matched, written = sync_epic(roots, args.epic_dir, args.status)
         if not matched:
             sys.stderr.write(f"Warning: No epic docs found for '{args.epic_dir}'.\n")
             sys.exit(1)
         print(f"Synchronized {len(matched)} epic docs for '{args.epic_dir}' -> '{args.status}'")
 
     elif args.command == "archive-epic":
         roots = checkout_roots()
         archived, cleaned = archive_epic_tasks(roots, args.epic_dir)
         print(
             f"Archived {len(archived)} tasks into .devtool/epic/{args.epic_dir} "
             f"(cleaned {len(cleaned)} from features)"
         )
 
     elif args.command == "archive-done":
         roots = checkout_roots()
-        archived = archive_all_done_epics(roots)
-        if archived:
-            print(f"Archived {len(archived)} epic(s) into .devtool/epic/: {', '.join(archived)}")
+        done_epics = archive_all_done_epics(roots)
+        if done_epics:
+            print(f"Archived {len(done_epics)} epic(s) into .devtool/epic/: {', '.join(done_epics)}")
         else:
             print("No completed tasks to archive.")
 
 
 
 if __name__ == "__main__":
     main()
 
 

exec
/bin/zsh -lc "rg -n '"'^def (review_file|principal_artefact_lines|run_principal|run'"\\(|record_round|check|triage|parser|main)|add_argument\\(\"--kind\"|set_defaults' skills/dev-implementation/resources/scripts/run_external_review.py && nl -ba skills/dev-implementation/resources/scripts/run_external_review.py | sed -n '300,590p' && nl -ba skills/dev-implementation/resources/scripts/run_external_review.py | sed -n '590,790p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
43:def review_file(kind: str) -> tuple[str, str]:
49:def principal_artefact_lines(root: Path, epic_dir: str) -> str:
371:def run_principal(root: Path, args: argparse.Namespace, sha: str) -> int:
399:def run(args: argparse.Namespace) -> int:
542:def record_round(root: Path, args: argparse.Namespace, sha: str, passes: list[Pass],
595:def check(args: argparse.Namespace) -> int:
677:def triage(args: argparse.Namespace) -> int:
713:def main(argv: list[str] | None = None) -> int:
717:    runner.add_argument("--kind", choices=KINDS, default="code")
728:    checker.add_argument("--kind", choices=KINDS, default="code")
731:    triager.add_argument("--kind", choices=KINDS, default="code")
   300	def cli_command(cli: str, model: str | None) -> list[str]:
   301	    extra = ["--model", model] if model else []
   302	    if cli == "claude":
   303	        return ["claude", "-p", "--permission-mode", "plan", *extra]
   304	    return ["codex", "exec", "--sandbox", "read-only", *extra, "-"]
   305	
   306	
   307	def cell(text: str) -> str:
   308	    return text.replace("|", "\\|").replace("\r", "").replace("\n", " ").strip()
   309	
   310	
   311	def fence_for(text: str) -> str:
   312	    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
   313	    return "`" * max(3, longest + 1)
   314	
   315	
   316	def rounds_in(text: str) -> list[tuple[int, list[str]]]:
   317	    """Split review_results.md into (number, lines) rounds, ignoring headings inside fenced raw output."""
   318	    rounds: list[tuple[int, list[str]]] = []
   319	    fence = ""
   320	    for line in text.splitlines():
   321	        match = FENCE.match(line)
   322	        if fence:
   323	            fence = "" if line.rstrip() == fence else fence
   324	        elif match:
   325	            fence = match.group(1)
   326	        elif (heading := re.fullmatch(r"## Round (\d+)", line)):
   327	            rounds.append((int(heading.group(1)), []))
   328	            continue
   329	        if rounds:
   330	            rounds[-1][1].append(line)
   331	    return rounds
   332	
   333	
   334	def split_row(line: str) -> list[str]:
   335	    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
   336	
   337	
   338	def metadata(lines: list[str]) -> list[str]:
   339	    """A round's own lines: its fields and findings table, never its raw output."""
   340	    return lines[:lines.index("Raw output:")] if "Raw output:" in lines else lines
   341	
   342	
   343	def table_findings(lines: list[str]) -> list[tuple[str, list[str]]]:
   344	    """(line, cells) for every findings row, `| <number> |` onwards, well formed or not."""
   345	    return [(line, split_row(line)) for line in metadata(lines) if FINDING_ROW.match(line)]
   346	
   347	
   348	def parse_findings(out: str, verdict: str | None = None) -> list[tuple[str, str, str]]:
   349	    """Each finding line as (severity, location, problem); a blocking line in list format keeps its raw text."""
   350	    findings = []
   351	    for line in out.splitlines():
   352	        if (match := FINDING.match(line)):
   353	            sev, loc, problem = match.groups()
   354	            findings.append((sev.capitalize(), loc, problem))
   355	        elif (blocking := UNPARSED_BLOCKING.search(line)):
   356	            if verdict == "PASS" and not findings:
   357	                continue
   358	            findings.append((blocking.group(1).capitalize(), "unparsed", line.strip()))
   359	    return findings
   360	
   361	
   362	def render_round(number: int, meta: dict[str, str], findings: list[tuple[str, str, str]], output: str) -> str:
   363	    head = "".join(f"- **{key}**: {value}\n" for key, value in meta.items())
   364	    table = "| # | Severity | Location | Problem | Decision |\n|---|----------|----------|---------|----------|\n"
   365	    table += "".join(f"| {i} | {sev} | {cell(loc)} | {cell(problem)} |  |\n"
   366	                     for i, (sev, loc, problem) in enumerate(findings, 1))
   367	    fence = fence_for(output)
   368	    return f"## Round {number}\n\n{head}\n{table}\nRaw output:\n\n{fence}text\n{output.rstrip()}\n{fence}\n"
   369	
   370	
   371	def run_principal(root: Path, args: argparse.Namespace, sha: str) -> int:
   372	    facts_timeout = getattr(args, "facts_timeout", 300)
   373	    check_cmd = [sys.executable, str(SCRIPTS / "check_epic_readiness.py"), args.epic_dir]
   374	    try:
   375	        _code, out, _err = run_gate("check_epic_readiness.py", check_cmd, root, facts_timeout)
   376	    except PreconditionFailedError as error:
   377	        print_gate_banner(error, args.cli)
   378	        return 2
   379	
   380	    base_sha = git_run(root, "rev-parse", "--verify", args.base).decode().strip()
   381	    readiness_output = out.rstrip()
   382	
   383	    prompt = Template(PRINCIPAL_PROMPT.read_text(encoding="utf-8")).safe_substitute(
   384	        rules=PRINCIPAL_RULES.read_text(encoding="utf-8").strip(),
   385	        sha=sha,
   386	        base=args.base,
   387	        base_sha=base_sha,
   388	        epic_dir=f".devtool/epic/{args.epic_dir}",
   389	        artefacts=principal_artefact_lines(root, args.epic_dir),
   390	        readiness_output=readiness_output,
   391	    )
   392	
   393	    before = status_lines(root)
   394	    code, out, err = execute(cli_command(args.cli, args.model), root, args.timeout, prompt)
   395	    changed = tree_changes(root, before, sha)
   396	    return record_round(root, args, sha, [Pass("principal", code, out, err, prompt)], changed, {"Kind": "principal"})
   397	
   398	
   399	def run(args: argparse.Namespace) -> int:
   400	    if getattr(args, "kind", "code") == "principal" and args.cli == "ollama":
   401	        print("--kind principal supports --cli claude or codex", file=sys.stderr)
   402	        return 2
   403	
   404	    if args.cli == "ollama":
   405	        if not args.model:
   406	            print("--cli ollama needs --model", file=sys.stderr)
   407	            return 2
   408	    elif not shutil.which(args.cli):
   409	        print(f"{args.cli} not found on PATH", file=sys.stderr)
   410	        return 2
   411	    root = Path(git_run(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
   412	    if status_lines(root):
   413	        print("commit or stash your changes before a review", file=sys.stderr)
   414	        return 2
   415	    sha = head_of(root)
   416	
   417	    if getattr(args, "kind", "code") == "principal":
   418	        return run_principal(root, args, sha)
   419	    model_ctx = None
   420	    if args.cli == "ollama":
   421	        try:
   422	            model_ctx = local_review.probe(args.host, args.model)
   423	        except local_review.LocalReviewError as error:
   424	            print_gate_banner(PreconditionFailedError("Ollama probe", str(error)), args.cli)
   425	            return 2
   426	    hld_text = (root / ".devtool" / "epic" / args.epic_dir / f"{args.epic_dir}.en.md").read_text(encoding="utf-8")
   427	    try:
   428	        facts_timeout = getattr(args, "facts_timeout", 300)
   429	        audit_output, results_output = collect_facts(root, args.epic_dir, args.base, hld_text, facts_timeout)
   430	    except PreconditionFailedError as error:
   431	        print_gate_banner(error, args.cli)
   432	        return 2
   433	    if args.cli == "ollama":
   434	        return run_local(root, args, sha, audit_output, results_output, model_ctx)
   435	    diff_limit = getattr(args, "diff_limit", MAX_DIFF_LINES)
   436	    diff_section = build_diff_section(root, args.base, sha, max_lines=diff_limit)
   437	    prompt = Template(PROMPT.read_text(encoding="utf-8")).safe_substitute(
   438	        rules=RULES.read_text(encoding="utf-8").strip(),
   439	        sha=sha,
   440	        base=args.base,
   441	        epic_dir=f".devtool/epic/{args.epic_dir}",
   442	        artefacts=artefact_lines(root, args.epic_dir),
   443	        audit_output=audit_output.rstrip(),
   444	        results_output=results_output.rstrip(),
   445	        diff_section=diff_section,
   446	    )
   447	    before = status_lines(root)  # after the facts: running the test commands may write build output
   448	    code, out, err = execute(cli_command(args.cli, args.model), root, args.timeout, prompt)
   449	    changed = tree_changes(root, before, sha)
   450	    return record_round(root, args, sha, [Pass("review", code, out, err, prompt)], changed, {})
   451	
   452	
   453	def live_log_dir(root: Path, epic_dir: str) -> Path:
   454	    """Where each pass streams its output: build/local-review/<epic_dir> when Git ignores it, else the Git directory.
   455	
   456	    Either place leaves `git status` untouched, so the logs never trip the tree-modified check."""
   457	    visible = root / "build" / "local-review" / epic_dir
   458	    if subprocess.run(["git", "check-ignore", "-q", str(visible)], cwd=root, check=False).returncode == 0:
   459	        return visible
   460	    return root / git_run(root, "rev-parse", "--git-path", f"local-review/{epic_dir}").decode().strip()
   461	
   462	
   463	def run_local(root: Path, args: argparse.Namespace, sha: str, audit_output: str, results_output: str,
   464	              model_ctx: int | None) -> int:
   465	    """Fit every slice before the first call, then review them one at a time; the first failed pass ends the run."""
   466	    ctx = args.num_ctx or model_ctx or local_review.DEFAULT_NUM_CTX
   467	    planned: list[tuple[local_review.Slice, str]] = []
   468	    try:
   469	        for slice_ in local_review.build_slices(root, args.epic_dir, args.base, sha, audit_output, results_output,
   470	                                                EXCLUDES):
   471	            system = local_review.render_system(slice_)
   472	            budget = int(ctx * local_review.PROMPT_SHARE) - local_review.estimate_tokens(system)
   473	            planned.append((local_review.fit(slice_, budget), system))
   474	    except local_review.LocalReviewError as error:
   475	        print_gate_banner(PreconditionFailedError("Context budget", str(error)), args.cli)
   476	        return 2
   477	    logs = live_log_dir(root, args.epic_dir)
   478	    logs.mkdir(parents=True, exist_ok=True)
   479	    print(f"{CYAN}Live logs:{RESET} {logs}", file=sys.stderr, flush=True)
   480	    before = status_lines(root)
   481	    passes: list[Pass] = []
   482	    for number, (slice_, system) in enumerate(planned, 1):
   483	        user = local_review.render_user(slice_)
   484	        prompt_tokens = local_review.estimate_tokens(system) + local_review.estimate_tokens(user)
   485	        options = local_review.chat_options(model_ctx, args.num_ctx, prompt_tokens)
   486	        print(f"{CYAN}⏳ [Pass {number}/{len(planned)}]{RESET} {slice_.label} ... ", end="", file=sys.stderr, flush=True)
   487	        started = time.monotonic()
   488	        reply = local_review.chat(args.host, args.model, system, user, options, args.timeout,
   489	                                  logs / f"{number}-{slice_.label}.log")
   490	        code = 0 if reply.error is None else None if reply.error.startswith("timed out") else 1
   491	        passes.append(Pass(slice_.label, code, reply.content, reply.error or "", user, slice_.omitted,
   492	                           reply.done_reason))
   493	        if reply.error is not None or reply.done_reason != "stop":
   494	            print(f"{RED}❌ {reply.error or f'done_reason {reply.done_reason}'}{RESET}", file=sys.stderr, flush=True)
   495	            break
   496	        print(f"{GREEN}✅ {round(time.monotonic() - started)}s{RESET}", file=sys.stderr, flush=True)
   497	    changed = tree_changes(root, before, sha)
   498	    return record_round(root, args, sha, passes, changed, {"Passes": str(len(planned)), "Context": str(ctx)})
   499	
   500	
   501	@dataclass(frozen=True)
   502	class Pass:
   503	    label: str
   504	    code: int | None  # 0 transport success, None timeout, otherwise failure
   505	    out: str  # the text the parser reads
   506	    err: str
   507	    shown: str  # what the reviewer was shown
   508	    omitted: tuple[str, ...] = ()
   509	    done_reason: str | None = None
   510	
   511	
   512	def tree_changes(root: Path, before: list[str], sha: str) -> list[str]:
   513	    """Status lines that appeared or vanished since `before`, led by HEAD when it moved."""
   514	    changed = sorted(set(status_lines(root)) ^ set(before))
   515	    if head_of(root) != sha:
   516	        changed.insert(0, "HEAD")
   517	    return changed
   518	
   519	
   520	def path_of(location: str) -> str:
   521	    """The file a finding points at: its location before the first colon, without backticks."""
   522	    return location.split(":", 1)[0].strip().strip("`")
   523	
   524	
   525	def annotate(finding: tuple[str, str, str], shown: str) -> tuple[str, str, str]:
   526	    """Mark a blocking finding whose location path the reviewer was never shown; its severity stays."""
   527	    sev, loc, problem = finding
   528	    if sev in BLOCKING and loc != "unparsed" and path_of(loc) not in shown:
   529	        problem += " (location not shown to reviewer)"
   530	    return sev, loc, problem
   531	
   532	
   533	def pass_output(item: Pass, number: int, args: argparse.Namespace) -> str:
   534	    if args.cli == "ollama":
   535	        return f"### Pass {number}: {item.label}\n\n{item.out}" + (f"\n--- error ---\n{item.err}" if item.err.strip() else "")
   536	    output = item.out + (f"\n--- stderr ---\n{item.err}" if item.err.strip() else "")
   537	    if item.code is None:
   538	        output += f"\n--- timed out after {args.timeout} seconds ---\n"
   539	    return output
   540	
   541	
   542	def record_round(root: Path, args: argparse.Namespace, sha: str, passes: list[Pass],
   543	                 changed: list[str], extra: dict[str, str]) -> int:
   544	    """Append one round to review_results.md from every pass of a review; return the run's exit code."""
   545	    local = args.cli == "ollama"
   546	    verdicts: list[str | None] = []
   547	    findings: list[tuple[str, str, str]] = []
   548	    complete = True
   549	    for item in passes:
   550	        lines = item.out.splitlines()
   551	        marks = [(index, m.group(1).upper()) for index, line in enumerate(lines) if (m := VERDICT.match(line))]
   552	        verdict = marks[-1][1] if marks else None
   553	        if local:  # a draft line in the Analysis above the verdict block is never a finding
   554	            block = "\n".join(lines[marks[-1][0]:]) if marks else ""
   555	            found = [annotate(finding, item.shown) for finding in parse_findings(block, verdict)]
   556	        else:
   557	            found = parse_findings(item.out, verdict)
   558	        verdicts.append(verdict)
   559	        findings.extend(found)
   560	        complete = complete and item.code == 0 and verdict is not None \
   561	            and not (verdict == "CHANGES REQUIRED" and not found) and (not local or item.done_reason == "stop")
   562	    if changed:
   563	        status = f"discarded: tree modified ({', '.join(line[3:] if line != 'HEAD' else line for line in changed)})"
   564	    else:
   565	        status = "completed" if complete else "no verdict"
   566	    if "CHANGES REQUIRED" in verdicts:
   567	        verdict_text = "CHANGES REQUIRED"
   568	    else:
   569	        verdict_text = "PASS" if verdicts and None not in verdicts else "none"
   570	    name, title = review_file(getattr(args, "kind", "code"))
   571	    path = root / ".devtool" / "epic" / args.epic_dir / name
   572	    existing = path.read_text(encoding="utf-8") if path.exists() else f"# {title}: {args.epic_dir}\n"
   573	    round_num = len(rounds_in(existing)) + 1
   574	    meta = {
   575	        "Date": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
   576	        "SHA": sha,
   577	        "Base": args.base,
   578	        "CLI": args.cli,
   579	        "Model": args.model or "default",
   580	        "Status": status,
   581	        "Verdict": verdict_text,
   582	        **extra,
   583	    }
   584	    if (omitted := "; ".join(f"{item.label}: {', '.join(item.omitted)}" for item in passes if item.omitted)):
   585	        meta["Omitted"] = omitted
   586	    output = "\n\n".join(pass_output(item, number, args) for number, item in enumerate(passes, 1))
   587	    text = existing.rstrip("\n") + "\n\n" + render_round(round_num, meta, findings, output)
   588	    path.write_text(text, encoding="utf-8")
   589	    print(f"Round {round_num}: {status} ({path.relative_to(root)})")
   590	    if status != "completed":
   590	    if status != "completed":
   591	        return 2
   592	    return 1 if any(sev in BLOCKING for sev, _, _ in findings) else 0
   593	
   594	
   595	def check(args: argparse.Namespace) -> int:
   596	    root = Path(git_run(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
   597	    name, _ = review_file(getattr(args, "kind", "code"))
   598	    path = root / ".devtool" / "epic" / args.epic_dir / name
   599	    if not path.exists():
   600	        return 0
   601	    completed = [(n, lines) for n, lines in rounds_in(path.read_text(encoding="utf-8"))
   602	                 if "- **Status**: completed" in metadata(lines)]
   603	    undecided = []
   604	    for line, cells in table_findings(completed[-1][1]) if completed else []:
   605	        if len(cells) != 5:
   606	            undecided.append(f"undecided: unreadable findings row: {line.strip()}")
   607	        elif cells[1] in BLOCKING and not cells[4].startswith(("fixed in ", "dismissed: ")):
   608	            undecided.append(f"undecided: #{cells[0]} {cells[1]} {cells[2]}")
   609	    if undecided:
   610	        print("\n".join(undecided))
   611	    return 1 if undecided else 0
   612	
   613	
   614	def round_meta(lines: list[str]) -> dict[str, str]:
   615	    """A round's `- **Key**: value` fields."""
   616	    return {m.group(1): m.group(2) for line in metadata(lines) if (m := META_LINE.match(line))}
   617	
   618	
   619	def round_output(lines: list[str]) -> str:
   620	    """The fenced raw output of a round, without its fence."""
   621	    body = lines[lines.index("Raw output:") + 1:] if "Raw output:" in lines else []
   622	    fences = [(index, match.group(1)) for index, line in enumerate(body) if (match := FENCE.match(line))]
   623	    if not fences:
   624	        return ""
   625	    start, fence = fences[0]
   626	    end = next((i for i in range(start + 1, len(body)) if body[i].rstrip() == fence), len(body))
   627	    return "\n".join(body[start + 1:end])
   628	
   629	
   630	def round_passes(output: str) -> list[tuple[str, str, str]]:
   631	    """(pass, verdict, error) for each `### Pass` block, or one `review` pass when there is none."""
   632	    blocks: list[tuple[str, list[str]]] = []
   633	    for line in output.splitlines():
   634	        if (header := PASS_HEADER.match(line)):
   635	            blocks.append((f"{header.group(1)} {header.group(2)}", []))
   636	        elif blocks:
   637	            blocks[-1][1].append(line)
   638	    rows = []
   639	    for name, lines in blocks or [("review", output.splitlines())]:
   640	        verdicts = [m.group(1).upper() for line in lines if (m := VERDICT.match(line))]
   641	        after = lines[lines.index("--- error ---") + 1:] if "--- error ---" in lines else []
   642	        rows.append((name, verdicts[-1] if verdicts else "none", after[0].strip() if after else "—"))
   643	    return rows
   644	
   645	
   646	def finding_rows(lines: list[str]) -> list[list[str]]:
   647	    return [cells for _, cells in table_findings(lines) if len(cells) == 5]
   648	
   649	
   650	def comparison_row(number: int, lines: list[str]) -> str:
   651	    meta, rows = round_meta(lines), finding_rows(lines)
   652	    counts = [sum(cells[1] == severity for cells in rows) for severity in ("Critical", "Important", "Minor")]
   653	    fixed = sum(cells[4].startswith("fixed in ") for cells in rows)
   654	    dismissed = sum(cells[4].startswith("dismissed: ") for cells in rows)
   655	    undecided = sum(cells[1] in BLOCKING and not cells[4].startswith(("fixed in ", "dismissed: ")) for cells in rows)
   656	    values = [str(number), f"{meta.get('CLI', '?')} / {meta.get('Model', '?')}", meta.get("SHA", "?")[:7],
   657	              meta.get("Status", "?"), meta.get("Verdict", "?"), *map(str, [*counts, fixed, dismissed, undecided])]
   658	    return "| " + " | ".join(cell(value) for value in values) + " |"
   659	
   660	
   661	def since_lines(previous: list[list[str]], latest: list[list[str]]) -> list[str]:
   662	    """What became of the previous round's blocking or fixed findings, compared by file path."""
   663	    lines = []
   664	    for cells in previous:
   665	        fixed = cells[4].startswith("fixed in ")
   666	        if cells[1] not in BLOCKING and not fixed:
   667	            continue
   668	        again = [f"#{row[0]}" for row in latest if path_of(row[2]) == path_of(cells[2])]
   669	        if again:
   670	            lines.append(f"- {cells[2]}: re-reported at the same path ({', '.join(again)})"
   671	                         + (" — check the fix" if fixed else ""))
   672	        else:
   673	            lines.append(f"- {cells[2]}: not re-reported")
   674	    return lines or ["No blocking or fixed finding in the previous round."]
   675	
   676	
   677	def triage(args: argparse.Namespace) -> int:
   678	    """Print the latest round as a skeleton to fill, verify and present before any action on its findings."""
   679	    root = Path(git_run(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
   680	    name, _ = review_file(getattr(args, "kind", "code"))
   681	    path = root / ".devtool" / "epic" / args.epic_dir / name
   682	    rounds = rounds_in(path.read_text(encoding="utf-8")) if path.exists() else []
   683	    if not rounds:
   684	        print(f"no review round recorded for {args.epic_dir}", file=sys.stderr)
   685	        return 2
   686	    number, lines = rounds[-1]
   687	    meta = round_meta(lines)
   688	    out = [f"# Review Triage: {args.epic_dir}, Round {number}", "",
   689	           *(f"- **{key}**: {meta.get(key, '?')}" for key in ("SHA", "CLI", "Model", "Status", "Verdict")), "",
   690	           "## Passes", "", "| Pass | Verdict | Error |", "|------|---------|-------|",
   691	           *(f"| {cell(name)} | {verdict} | {cell(error)} |" for name, verdict, error in round_passes(round_output(lines))),
   692	           "", "## Findings", ""]
   693	    latest = finding_rows(lines)
   694	    if latest:
   695	        out += ["| # | Severity | Location | Problem | Assessment | Evidence | Proposed action |",
   696	                "|---|----------|----------|---------|------------|----------|-----------------|",
   697	                *(f"| {cells[0]} | {cells[1]} | {cell(cells[2])} | {cell(cells[3])} | ? | ? | ? |" for cells in latest)]
   698	    else:
   699	        out.append("None.")
   700	    out += ["", "## Round Comparison", "",
   701	            "| Round | CLI / Model | SHA | Status | Verdict | Critical | Important | Minor | Fixed | Dismissed | Undecided |",
   702	            "|-------|-------------|-----|--------|---------|----------|-----------|-------|-------|-----------|-----------|",
   703	            *(comparison_row(n, round_lines) for n, round_lines in rounds), ""]
   704	    if len(rounds) > 1:
   705	        out += [f"## Since Round {rounds[-2][0]}", "", *since_lines(finding_rows(rounds[-2][1]), latest)]
   706	    else:
   707	        out += ["## Since the Previous Round", "", "No earlier round."]
   708	    out += ["", "## Next Steps", "", NEXT_STEPS]
   709	    print("\n".join(out))
   710	    return 0
   711	
   712	
   713	def main(argv: list[str] | None = None) -> int:
   714	    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
   715	    modes = parser.add_subparsers(dest="mode", required=True)
   716	    runner = modes.add_parser("run", help="have the CLI review the epic and record a round")
   717	    runner.add_argument("--kind", choices=KINDS, default="code")
   718	    runner.add_argument("--epic-dir", required=True)
   719	    runner.add_argument("--base", required=True)
   720	    runner.add_argument("--cli", required=True, choices=("claude", "codex", "ollama"))
   721	    runner.add_argument("--model")
   722	    runner.add_argument("--host", default=local_review.host_from_env())
   723	    runner.add_argument("--num-ctx", type=int, default=None)
   724	    runner.add_argument("--timeout", type=int, default=1800)
   725	    runner.add_argument("--facts-timeout", type=int, default=300)
   726	    runner.add_argument("--diff-limit", type=int, default=MAX_DIFF_LINES)
   727	    checker = modes.add_parser("check", help="list undecided blocking findings of the latest completed round")
   728	    checker.add_argument("--kind", choices=KINDS, default="code")
   729	    checker.add_argument("--epic-dir", required=True)
   730	    triager = modes.add_parser("triage", help="print the latest round as a skeleton to fill before acting on it")
   731	    triager.add_argument("--kind", choices=KINDS, default="code")
   732	    triager.add_argument("--epic-dir", required=True)
   733	    args = parser.parse_args(argv)
   734	    try:
   735	        return {"run": run, "check": check, "triage": triage}[args.mode](args)
   736	    except (ContractError, OSError) as error:
   737	        print(f"error: {error}", file=sys.stderr)
   738	        return 2
   739	
   740	
   741	if __name__ == "__main__":
   742	    sys.exit(main())

exec
/bin/zsh -lc "rg -n '"'^def (parse_worktree_branches|checkout_roots|epic_checkout_roots|find_epic_slug)'"' skills/dev-implementation/resources/scripts/sync_task_status.py && nl -ba skills/dev-implementation/resources/scripts/sync_task_status.py | sed -n '1,180p' && git diff --unified=35 main...c09cb95593c5908098462a0a2963f1a300d9efcb -- skills/dev-implementation/resources/scripts/test_sync_task_status.py" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 1803ms:
80:def parse_worktree_branches(output: str) -> list[tuple[Path, str | None]]:
106:def checkout_roots() -> list[Path]:
117:def epic_checkout_roots(epic_dir: str) -> list[Path]:
253:def find_epic_slug(root: Path, epic_dir: str) -> str | None:
     1	#!/usr/bin/env python3
     2	"""Mirror one epic task's Kanban status across every checkout of this repo.
     3	
     4	`dev-implementation` runs an epic inside an isolated worktree, but the same
     5	task files are also checked out in the main workspace -- and `dev-designer`
     6	writes each task twice, into `.devtool/features/` and into
     7	`.devtool/epic/<epic_dir>/`. Writing a status to only one of those four copies
     8	leaves every other Kanban board stale for the whole epic.
     9	
    10	This script writes them all:
    11	
    12	    sync_task_status.py task <task_id> <status>
    13	    sync_task_status.py epic <epic_dir> <status>
    14	
    15	`task` mode rewrites `status`, `modified`, and -- on `done` -- `completedAt` in
    16	the frontmatter of every copy of that task, in every checkout `git worktree
    17	list` reports. `epic` mode rewrites the Meta Data `Status` line of the Epic
    18	Overview's `.en.md` and `.vi.md` together, so the pair can never diverge.
    19	
    20	Only matched lines change; every other key and the whole document body survive
    21	byte-for-byte. Frontmatter is parsed with the same hand-rolled regex idiom as
    22	compute_execution_order.py -- deliberately no PyYAML, so this stays stdlib-only.
    23	"""
    24	import re
    25	import subprocess
    26	import sys
    27	from datetime import UTC, datetime
    28	from pathlib import Path
    29	
    30	sys.path.insert(0, str(Path(__file__).parent))
    31	from slug_utils import parse_frontmatter, sanitize_slug
    32	
    33	TASK_STATUSES = ("backlog", "todo", "in-progress", "review", "done")
    34	FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
    35	
    36	
    37	def now_iso() -> str:
    38	    """UTC, seconds precision, Zulu suffix -- e.g. 2026-09-14T10:23:45Z."""
    39	    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    40	
    41	
    42	def set_frontmatter_field(text: str, key: str, value: str | None) -> str:
    43	    """Set `key: "value"` or `key: null` inside the leading frontmatter block only.
    44	
    45	    A key that is absent is inserted directly after `status:`, so task files
    46	    written before this script existed (no `modified`, no `completedAt`) keep
    47	    working instead of silently losing the field. Body text is never scanned.
    48	    """
    49	    match = FRONTMATTER_RE.match(text)
    50	    if not match:
    51	        return text
    52	    block = match.group(1)
    53	    if value is None or value == "null":
    54	        new_line = f"{key}: null"
    55	    else:
    56	        new_line = f'{key}: "{value}"'
    57	    key_re = re.compile(rf"^{re.escape(key)}\s*:.*$", re.MULTILINE)
    58	    if key_re.search(block):
    59	        new_block = key_re.sub(lambda _m: new_line, block, count=1)
    60	    else:
    61	        status_re = re.compile(r"^status\s*:.*$", re.MULTILINE)
    62	        if status_re.search(block):
    63	            new_block = status_re.sub(lambda m: m.group(0) + "\n" + new_line, block, count=1)
    64	        else:
    65	            new_block = block + "\n" + new_line
    66	    return text[:match.start(1)] + new_block + text[match.end(1):]
    67	
    68	
    69	def parse_worktree_list(output: str) -> list[Path]:
    70	    """Extract checkout roots from `git worktree list --porcelain` output.
    71	
    72	    Git always reports the main worktree first, and callers rely on that
    73	    ordering -- Phase 4's main-checkout restore uses roots[0]. Paths may
    74	    contain spaces, so take everything after the first token.
    75	    """
    76	    return [Path(line[len("worktree "):]) for line in output.splitlines()
    77	            if line.startswith("worktree ")]
    78	
    79	
    80	def parse_worktree_branches(output: str) -> list[tuple[Path, str | None]]:
    81	    """Extract (path, branch) pairs from `git worktree list --porcelain` output.
    82	
    83	    Branch is the full ref string (e.g. 'refs/heads/epic/name') or None if detached.
    84	    """
    85	    entries: list[tuple[Path, str | None]] = []
    86	    current_path: Path | None = None
    87	    current_branch: str | None = None
    88	
    89	    for line in output.splitlines():
    90	        if line.startswith("worktree "):
    91	            if current_path is not None:
    92	                entries.append((current_path, current_branch))
    93	            current_path = Path(line[len("worktree "):])
    94	            current_branch = None
    95	        elif line.startswith("branch "):
    96	            current_branch = line[len("branch "):]
    97	        elif line == "detached":
    98	            current_branch = None
    99	
   100	    if current_path is not None:
   101	        entries.append((current_path, current_branch))
   102	
   103	    return entries
   104	
   105	
   106	def checkout_roots() -> list[Path]:
   107	    """Every checkout of this repo, main worktree first.
   108	
   109	    The only subprocess boundary in this module -- everything else is pure and
   110	    directly testable, which is why the test suite needs no git fixtures.
   111	    """
   112	    result = subprocess.run(["git", "worktree", "list", "--porcelain"],
   113	                            capture_output=True, text=True, check=True)
   114	    return parse_worktree_list(result.stdout)
   115	
   116	
   117	def epic_checkout_roots(epic_dir: str) -> list[Path]:
   118	    """Return the current checkout root plus every worktree on branch refs/heads/epic/<epic_slug>.
   119	
   120	    Current checkout is always first. Other worktrees are included only if their branch
   121	    matches this epic's slug.
   122	    """
   123	    top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
   124	                         capture_output=True, text=True, check=True)
   125	    current_root = Path(top.stdout.strip())
   126	
   127	    wt_result = subprocess.run(["git", "worktree", "list", "--porcelain"],
   128	                               capture_output=True, text=True, check=True)
   129	    entries = parse_worktree_branches(wt_result.stdout)
   130	
   131	    slug = find_epic_slug(current_root, epic_dir) or epic_dir
   132	    target_branch = f"refs/heads/epic/{slug}"
   133	
   134	    roots: list[Path] = [current_root]
   135	    seen = {current_root.resolve()}
   136	
   137	    for path, branch in entries:
   138	        if branch == target_branch:
   139	            resolved = path.resolve()
   140	            if resolved not in seen:
   141	                seen.add(resolved)
   142	                roots.append(path)
   143	
   144	    return roots
   145	
   146	
   147	def task_targets(root: Path, task_id: str) -> list[Path]:
   148	    """Every copy of one task inside one checkout: features, features/done, + each epic dir."""
   149	    candidates = [
   150	        root / ".devtool" / "features" / f"{task_id}.md",
   151	        root / ".devtool" / "features" / "done" / f"{task_id}.md",
   152	    ]
   153	    candidates.extend(sorted((root / ".devtool" / "epic").glob(f"*/{task_id}.md")))
   154	    return [path for path in candidates if path.is_file()]
   155	
   156	
   157	def epic_of(path: Path) -> str | None:
   158	    val = parse_frontmatter(path.read_text()).get("epic")
   159	    return sanitize_slug(val) if val else None
   160	
   161	
   162	def expected_epic(roots: list[Path], task_id: str) -> str | None:
   163	    """The epic this task_id belongs to, per the authoritative features copy (or epic copy if archived).
   164	
   165	    Task ids are `task_<number>_<name>`, so a name like `task_1_setup` can
   166	    plausibly exist under two different epics -- and `task_targets`' `*/` glob
   167	    would match both. Callers use this value to refuse any copy whose own
   168	    `epic:` differs. Checked main-worktree-first; mirrors cannot disagree.
   169	    """
   170	    for root in roots:
   171	        for features_dir in (root / ".devtool" / "features", root / ".devtool" / "features" / "done"):
   172	            features = features_dir / f"{task_id}.md"
   173	            if features.is_file():
   174	                return epic_of(features)
   175	        for epic_copy in sorted((root / ".devtool" / "epic").glob(f"*/{task_id}.md")):
   176	            if epic_copy.is_file():
   177	                return epic_of(epic_copy)
   178	    return None
   179	
   180	
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-dNnvHPaK' (errno=Operation not permitted)
2026-10-23 17:45:44.628 xcodebuild[26303:2218394]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:44.756 xcodebuild[26303:2218393] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-uh9F24K2' (errno=Operation not permitted)
2026-10-23 17:45:45.241 xcodebuild[26305:2218428]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:45.402 xcodebuild[26305:2218427] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
diff --git a/skills/dev-implementation/resources/scripts/test_sync_task_status.py b/skills/dev-implementation/resources/scripts/test_sync_task_status.py
index 79b4441..57ade25 100755
--- a/skills/dev-implementation/resources/scripts/test_sync_task_status.py
+++ b/skills/dev-implementation/resources/scripts/test_sync_task_status.py
@@ -744,37 +744,123 @@ class DoneGateTests(DoneGateCase):
         self.edit_evidence(break_rows)
         self.refuse_leaves_copies("condition 3:", "V3", "condition 7:")
 
     def test_verify_recorded_after_committing_is_refused(self):
         self.build()
         self.record()
         git(self.wt, "add", "-A")
         git(self.wt, "commit", "-q", "-m", "[DEMO] Task 1 committed before the gate")
         self.assertEqual(run_py(RECORDER, self.wt, "verify", str(self.wt / MIRROR)).returncode, 0)
         self.refuse_leaves_copies("condition 4: verify saw no change outside .devtool — record verify before committing",
                                   "condition 5: red and verify were recorded on different commits")
 
     def test_red_and_verify_on_different_commits_is_refused(self):
         self.build()
         mirror = self.wt / MIRROR
         self.assertEqual(run_py(RECORDER, self.wt, "red", str(mirror)).returncode, 0)
         git(self.wt, "add", "-A")
         git(self.wt, "commit", "-q", "-m", "[DEMO] Unrelated commit between red and verify")
         (self.wt / "feature.txt").write_text("done\n", encoding="utf-8")
         self.assertEqual(run_py(RECORDER, self.wt, "verify", str(mirror)).returncode, 0)
         result = self.done(self.wt)
         self.assert_refused(result, "condition 5: red and verify were recorded on different commits")
         self.assertNotIn("condition 4:", result.stderr)
 
     def test_failed_row_no_longer_in_the_table_is_refused(self):
         self.build()
         self.record()
 
         def add_dropped_row(runs):
             runs["verify"]["rows"].append({"id": "V9", "phase": "GREEN", "outcome": "FAIL", "reason": "exit 1"})
 
         self.edit_evidence(add_dropped_row)
         self.refuse_leaves_copies("condition 2: verify row V9 is FAIL and no longer in the table")
 
 
+class EpicCheckoutRootsTests(unittest.TestCase):
+    def setUp(self) -> None:
+        self.directory = tempfile.TemporaryDirectory()
+        self.addCleanup(self.directory.cleanup)
+        self.base = Path(self.directory.name).resolve()
+        self.main = self.base / "main"
+        self.wt_own = self.base / "wt_own"
+        self.wt_other = self.base / "wt_other"
+
+        self.main.mkdir()
+        git(self.main, "init", "-q", "-b", "main")
+        git(self.main, "config", "user.email", "demo@example.com")
+        git(self.main, "config", "user.name", "Demo")
+
+        (self.main / "README.md").write_text("# Main\n", encoding="utf-8")
+        (self.main / ".devtool" / "epic" / "demo_epic").mkdir(parents=True, exist_ok=True)
+        (self.main / ".devtool" / "features").mkdir(parents=True, exist_ok=True)
+
+        overview_en = "# Demo Epic\n\n- **Epic**: demo-epic\n- **Status**: Planned\n"
+        overview_vi = "# Demo Epic\n\n- **Epic**: demo-epic\n- **Trạng thái**: Planned\n"
+        (self.main / ".devtool" / "epic" / "demo_epic" / "demo_epic.en.md").write_text(overview_en, encoding="utf-8")
+        (self.main / ".devtool" / "epic" / "demo_epic" / "demo_epic.vi.md").write_text(overview_vi, encoding="utf-8")
+
+        task_content = '''---
+id: "task_1_demo"
+status: "todo"
+epic: "demo-epic"
+---
+# Task 1 Demo
+'''
+        (self.main / ".devtool" / "features" / "task_1_demo.md").write_text(task_content, encoding="utf-8")
+        (self.main / ".devtool" / "epic" / "demo_epic" / "task_1_demo.md").write_text(task_content, encoding="utf-8")
+
+        git(self.main, "add", "-A")
+        git(self.main, "commit", "-q", "-m", "initial commit")
+
+        git(self.main, "worktree", "add", "-q", "-b", "epic/demo-epic", str(self.wt_own))
+        git(self.main, "worktree", "add", "-q", "-b", "epic/other-epic", str(self.wt_other))
+
+    def test_parse_worktree_branches(self) -> None:
+        sample = f"""worktree {self.main}
+HEAD 1111111111111111111111111111111111111111
+branch refs/heads/main
+
+worktree {self.wt_own}
+HEAD 2222222222222222222222222222222222222222
+branch refs/heads/epic/demo-epic
+
+worktree {self.base / "wt_detached"}
+HEAD 3333333333333333333333333333333333333333
+detached
+"""
+        from sync_task_status import parse_worktree_branches
+        branches = parse_worktree_branches(sample)
+        self.assertEqual(len(branches), 3)
+        self.assertEqual(branches[0], (self.main, "refs/heads/main"))
+        self.assertEqual(branches[1], (self.wt_own, "refs/heads/epic/demo-epic"))
+        self.assertEqual(branches[2], (self.base / "wt_detached", None))
+
+    def test_prv_hp_05_own_worktree_updated(self) -> None:
+        """PRV-HP-05: epic updates the main checkout and the epic's own worktree."""
+        res = run_py(SYNC, self.main, "epic", "demo_epic", "Packaged")
+        self.assertEqual(res.returncode, 0, res.stderr)
+
+        for wt in (self.main, self.wt_own):
+            en_text = (wt / ".devtool" / "epic" / "demo_epic" / "demo_epic.en.md").read_text(encoding="utf-8")
+            vi_text = (wt / ".devtool" / "epic" / "demo_epic" / "demo_epic.vi.md").read_text(encoding="utf-8")
+            self.assertIn("- **Status**: Packaged", en_text)
+            self.assertIn("- **Trạng thái**: Packaged", vi_text)
+
+    def test_prv_fr_05_other_epics_untouched(self) -> None:
+        """PRV-FR-05: Another epic's worktree stays byte-identical and task sync still mirrors everywhere."""
+        res = run_py(SYNC, self.main, "epic", "demo_epic", "Packaged")
+        self.assertEqual(res.returncode, 0, res.stderr)
+
+        status_proc = subprocess.run(["git", "-C", str(self.wt_other), "status", "--porcelain"], capture_output=True, text=True)
+        self.assertEqual(status_proc.stdout.strip(), "")
+
+        res_task = run_py(SYNC, self.main, "task", "task_1_demo", "in-progress")
+        self.assertEqual(res_task.returncode, 0, res_task.stderr)
+
+        for root in (self.main, self.wt_own, self.wt_other):
+            task_file = root / ".devtool" / "features" / "task_1_demo.md"
+            self.assertIn('status: "in-progress"', task_file.read_text(encoding="utf-8"))
+
+
 if __name__ == "__main__":
     unittest.main()

exec
/bin/zsh -lc 'git diff --unified=30 main...c09cb95593c5908098462a0a2963f1a300d9efcb -- skills/dev-lifecycle/SKILL.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
exec
/bin/zsh -lc 'git diff --unified=30 main...c09cb95593c5908098462a0a2963f1a300d9efcb -- skills/dev-implementation/SKILL.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
exec
/bin/zsh -lc 'git diff --unified=30 main...c09cb95593c5908098462a0a2963f1a300d9efcb -- scripts/test_lifecycle_document_contract.py scripts/verify.sh' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
exec
/bin/zsh -lc 'git diff --unified=20 main...c09cb95593c5908098462a0a2963f1a300d9efcb -- docs/lifecycles.en.md docs/lifecycles.vi.md skills/dev-lifecycle/references/handoff-template.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 1977ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-WMz6rsHn' (errno=Operation not permitted)
2026-10-23 17:45:50.719 xcodebuild[26346:2218991]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:50.872 xcodebuild[26346:2218983] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-f0DehHL4' (errno=Operation not permitted)
2026-10-23 17:45:51.419 xcodebuild[26354:2219029]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:51.568 xcodebuild[26354:2219026] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
diff --git a/scripts/test_lifecycle_document_contract.py b/scripts/test_lifecycle_document_contract.py
index 178495b..0c43d7f 100755
--- a/scripts/test_lifecycle_document_contract.py
+++ b/scripts/test_lifecycle_document_contract.py
@@ -64,60 +64,63 @@ EXPECTED: dict[str, tuple[str, ...]] = {
     "skills/doc_quality_check/references/document-reviewer-prompt.md": (
         "English document",
         "Vietnamese document",
         "Translation parity",
     ),
     "skills/dev-implementation/SKILL.md": (
         '`profile`: `"epic"`',
         '`repository_sha`',
         "aggregated verdict of **PASS**",
         "check_bdd_traceability.py tests",
         "--ids",
         "Entry-Point Detection",
         "Resume Procedure",
         "handoff.md",
         "space- or comma-separated values",  # LF-HP-04
         "re-enters at Phase 2 step 2",  # LF-ST-04
         "may ride along in that commit",  # LF-ST-06
     ),
     "skills/dev-lifecycle/SKILL.md": (
         'profile `epic`',
         "`repository_sha`",
         "FAIL > BLOCKED > PASS",
         "check_bdd_traceability.py tests",
         "Granting Gate 4 without a passing traceability check",
         "Handoff Choice",
         "handoff-template.md",
         "Resuming an Epic",
         "Packaged",
         "a fresh traceability check and epic quality run",  # LF-ST-05
         "`<N>` is the task count the preflight printed",  # LF-HP-05
+        "check_epic_readiness.py <epic_dir>",
+        "Principal Review Choice",
+        "references/principal-review.md",
     ),
     "skills/dev-lifecycle/references/handoff-template.md": (
         "or `uncommitted` when `auto_commit` is false",  # LF-FR-04
         "Execution Guardrails for Receiving LLM",
         "Bounded context protocol",
         "Strict spec fidelity",
         "Zero test fakery",
         "No contract repair by the executor",
         "Apply the Execution Guardrails for Receiving LLM before presenting Gate 3",
     ),
     "skills/pr_review/SKILL.md": (
         '"profile": "pr"',
         '"base_ref"',
         "Executive Report Format",
     ),
 }
 
 FORBIDDEN: dict[str, tuple[str, ...]] = {
     "skills/pr_review/SKILL.md": (
         "melos test",
         "./gradlew check",
         "swift test",
         "cleanup-java",
     ),
 }
 
 
 class LifecycleDocumentContractTest(unittest.TestCase):
     def test_mvls_hp_06_dev_designer_and_handoff_guardrails(self) -> None:
         """[MVLS-HP-06] dev-designer retains Decisions Already Made contracts, exact node IDs, weak assertion ban, and handoff-template retains 4 guardrails."""
@@ -255,32 +258,107 @@ class LifecycleDocumentContractTest(unittest.TestCase):
         """[LMR-HP-09] Every review round is triaged with the developer before any fix or decision."""
         for relative in ("skills/dev-implementation/SKILL.md", "skills/dev-lifecycle/SKILL.md", "rules/CRITICAL_RULES.md"):
             text = (ROOT / relative).read_text(encoding="utf-8")
             self.assertIn("run_external_review.py triage", text, relative)
         implementation = (ROOT / "skills/dev-implementation/SKILL.md").read_text(encoding="utf-8")
         self.assertIn("references/review-triage.md", implementation)
         self.assertIn("wait for the developer's decisions before any Fix commit", implementation)
         lifecycle = (ROOT / "skills/dev-lifecycle/SKILL.md").read_text(encoding="utf-8")
         red_flags = lifecycle.split("## Red Flags", 1)[1].split("\n## ", 1)[0]
         self.assertIn("Acting on review findings before presenting the triage", red_flags)
 
     def test_document_contract_expected_tokens(self) -> None:
         for relative_path, required_tokens in EXPECTED.items():
             path = ROOT / relative_path
             if not path.exists():
                 continue
             text = path.read_text(encoding="utf-8")
             for token in required_tokens:
                 self.assertIn(token, text, f"{relative_path}: missing {token}")
 
     def test_document_contract_forbidden_tokens(self) -> None:
         for relative_path, forbidden_tokens in FORBIDDEN.items():
             path = ROOT / relative_path
             if not path.exists():
                 continue
             text = path.read_text(encoding="utf-8")
             for token in forbidden_tokens:
                 self.assertNotIn(token, text, f"{relative_path}: contains forbidden {token}")
 
 
+class PrincipalReviewWorkflowTest(unittest.TestCase):
+    def test_prv_hp_04_packaging_readiness_and_principal_review_choice(self) -> None:
+        """[PRV-HP-04] Packaging runs one readiness command and offers Principal Review Choice."""
+        skill_path = ROOT / "skills/dev-lifecycle/SKILL.md"
+        skill_text = skill_path.read_text(encoding="utf-8")
+        self.assertIn("check_epic_readiness.py <epic_dir>", skill_text)
+        self.assertIn("Principal Review Choice", skill_text)
+        self.assertIn("references/principal-review.md", skill_text)
+        self.assertNotIn(
+            "check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks",
+            skill_text,
+        )
+        words = len(skill_text.split())
+        self.assertLessEqual(words, 2500, f"dev-lifecycle/SKILL.md exceeds word limit: {words} > 2500")
+        for token in EXPECTED["skills/dev-lifecycle/SKILL.md"]:
+            self.assertIn(token, skill_text)
+
+        ref_path = ROOT / "skills/dev-lifecycle/references/principal-review.md"
+        self.assertTrue(ref_path.is_file(), f"{ref_path} must exist")
+        ref_text = ref_path.read_text(encoding="utf-8")
+        self.assertIn("1. **Done**", ref_text)
+        self.assertIn("2. **Principal Review**", ref_text)
+        self.assertIn("Claude CLI", ref_text)
+        self.assertIn("Codex CLI", ref_text)
+        self.assertIn("Never choose for the developer", ref_text)
+        self.assertIn("strongly recommended", ref_text)
+
+    def test_prv_ec_07_handoff_template_reads_first_principal_review(self) -> None:
+        """[PRV-EC-07] Read First lists principal_review.md."""
+        template_path = ROOT / "skills/dev-lifecycle/references/handoff-template.md"
+        text = template_path.read_text(encoding="utf-8")
+        read_first = text.split("## Read First", 1)[1].split("## ", 1)[0]
+        self.assertIn("`.devtool/epic/<epic_dir>/principal_review.md`, when present", read_first)
+        self.assertIn("`git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>`", text)
+
+    def test_prv_st_03_diagram_loop_returns_to_package_and_done_repackages(self) -> None:
+        """[PRV-ST-03] The loop returns to Package and Done re-packages after a round."""
+        for doc_name in ("docs/lifecycles.en.md", "docs/lifecycles.vi.md"):
+            doc_text = (ROOT / doc_name).read_text(encoding="utf-8")
+            self.assertIn("PKG --> PRC", doc_text)
+            self.assertIn('PRC -->|"2. Principal Review"| PR', doc_text)
+            self.assertIn('PR -->|"revised and re-packaged"| PKG', doc_text)
+            self.assertNotRegex(doc_text, r"PR\s*[-.=]+>[^\n]*(S3|G3)")
+
+        ref_path = ROOT / "skills/dev-lifecycle/references/principal-review.md"
+        ref_text = ref_path.read_text(encoding="utf-8")
+        self.assertIn("Record Principal Review round <n>", ref_text)
+        self.assertIn("Revise epic after Principal Review round <n>", ref_text)
+        self.assertIn("Package epic for handoff", ref_text)
+        self.assertIn("check --kind principal", ref_text)
+        self.assertIn("git log -1 --format=%s -- .devtool/epic/<epic_dir>", ref_text)
+
+    def test_prv_st_04_gate_3_stops_while_principal_finding_undecided(self) -> None:
+        """[PRV-ST-04] Gate 3 stops while a blocking principal finding is undecided."""
+        impl_path = ROOT / "skills/dev-implementation/SKILL.md"
+        text = impl_path.read_text(encoding="utf-8")
+        self.assertIn("run_external_review.py check --kind principal --epic-dir <epic_dir>", text)
+
+        phase1_section = text.split("### Phase 1", 1)[1].split("#### Phase 1 (continued)", 1)[0]
+        self.assertIn("Principal Review", phase1_section)
+        self.assertIn("not run", phase1_section)
+        self.assertIn("round <n>: PASS", phase1_section)
+        self.assertIn("round <n>: decided", phase1_section)
+
+        resume_section = text.split("#### Resume Procedure", 1)[1].split("### Phase 1", 1)[0]
+        self.assertIn("Principal Review", resume_section)
+        self.assertIn("not run", resume_section)
+        self.assertIn("round <n>: PASS", resume_section)
+        self.assertIn("round <n>: decided", resume_section)
+
+        words = len(text.split())
+        self.assertLessEqual(words, 4500, f"dev-implementation/SKILL.md exceeds word limit: {words} > 4500")
+
+
 if __name__ == "__main__":
     unittest.main()
+
diff --git a/scripts/verify.sh b/scripts/verify.sh
index 2d9b6cc..26107ad 100755
--- a/scripts/verify.sh
+++ b/scripts/verify.sh
@@ -221,60 +221,61 @@ fi
 echo
 note "== 10. Orchestrators route to a variant, never the router =="
 # Step 9's repo-wide sweep cannot be reused for this rename. `brainstorming` is an ordinary English
 # word: it appears legitimately as "during brainstorming" in writing-plans, "not a full brainstorming
 # dialogue" in dev-designer, as a deliberately preserved pre-1.2.0 path in
 # doc_quality_check/references/document-reviewer-prompt.md, and in this file's own comments. A bare
 # sweep would fail on all four. Scope it instead to the two orchestrators, and only to the two forms
 # that actually denote the skill rather than the activity.
 #
 # What this guards: `brainstorming` is a router that resolves an ambiguous entry. A lifecycle stage
 # naming it has not routed — it has moved the ambiguity one hop downstream. The precedent is real:
 # epic-lifecycle never contained the word "invoke", so agents read a stage description and did that
 # stage's work themselves, skipping the gate the stage owned.
 if hits=$(git ls-files 'skills/dev-lifecycle/*' 'skills/doc-lifecycle/*' \
           | tr '\n' '\0' \
           | xargs -0 grep -n 'd3nexus:brainstorming\|`brainstorming`' 2>/dev/null) \
    && [ -n "$hits" ]; then
   printf '%s\n' "$hits" | head -5
   fail "an orchestrator stage names the brainstorming router instead of a variant"
 else
   note "  ok   both orchestrators name a concrete brainstorming variant"
 fi
 
 echo
 note "== 11. Lifecycle document contracts are enforced =="
 python3 -m unittest skills/doc_quality_check/resources/scripts/test_check_document.py || FAILED=1
 python3 scripts/test_lifecycle_document_contract.py || FAILED=1
 python3 -m unittest scripts/test_lifecycle_signals.py || FAILED=1
 python3 -m unittest skills/dev-implementation/resources/scripts/test_audit_epic.py || FAILED=1
 python3 -m unittest skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py || FAILED=1
+python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py || FAILED=1
 python3 -m unittest skills/dev-implementation/resources/scripts/test_check_task_contract.py || FAILED=1
 python3 -m unittest skills/dev-implementation/resources/scripts/test_result_reports.py || FAILED=1
 python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py || FAILED=1
 python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py || FAILED=1
 python3 -m unittest skills/dev-implementation/resources/scripts/test_run_task_checks.py || FAILED=1
 python3 -m unittest skills/dev-implementation/resources/scripts/test_sync_task_status.py || FAILED=1
 python3 -m unittest scripts/test_run_unittest_junit.py || FAILED=1
 python3 -m unittest scripts/test_verifiable_handoff_text.py || FAILED=1
 python3 -m unittest scripts/test_verifiable_handoff.py || FAILED=1
 
 echo
 note "== 12. Branch integration script behaves =="
 python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py || FAILED=1
 
 echo
 note "== 13. Quality provider contracts, schemas, aggregation, and platform capabilities are enforced =="
 python3 -m unittest skills/quality_check/resources/scripts/test_validate_quality_contract.py || FAILED=1
 python3 -m unittest skills/quality_check/resources/scripts/test_aggregate_quality_results.py || FAILED=1
 python3 -m unittest skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py || FAILED=1
 python3 -m unittest skills/python-quality-check/resources/scripts/test_validate_python_quality.py || FAILED=1
 python3 -m unittest skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py || FAILED=1
 python3 -m unittest skills/android-quality-check/resources/scripts/test_validate_android_quality.py || FAILED=1
 python3 -m unittest skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py || FAILED=1
 python3 -m unittest skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py || FAILED=1
 python3 -m unittest skills/quality_check/resources/scripts/test_quality_provider_acceptance.py || FAILED=1
 
 echo
 if [ "$FAILED" -eq 0 ]; then
   echo "PASS — safe to publish"
 else

 succeeded in 1978ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-E9ghyNiM' (errno=Operation not permitted)
2026-10-23 17:45:50.719 xcodebuild[26345:2218984]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:50.872 xcodebuild[26345:2218982] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-XgN5LIQO' (errno=Operation not permitted)
2026-10-23 17:45:51.419 xcodebuild[26352:2219034]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:51.568 xcodebuild[26352:2219027] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
diff --git a/skills/dev-lifecycle/SKILL.md b/skills/dev-lifecycle/SKILL.md
index a2d3653..a9af484 100644
--- a/skills/dev-lifecycle/SKILL.md
+++ b/skills/dev-lifecycle/SKILL.md
@@ -72,77 +72,74 @@ Every gate is a **human approval** except Gate 4, which is a machine verdict. Ne
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
-1. **Preflight, read-only.** Must exit 0:
-   - `python3 "$SCRIPTS"/compute_execution_order.py <epic_slug>`
-   - `ls .devtool/epic/<epic_dir>/task_*.md | wc -l` (scan matched count must equal task mirror count)
-   - `python3 "$SCRIPTS"/check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks .devtool/epic/<epic_dir>/task_*.md`
-   - `python3 "$SCRIPTS"/check_task_contract.py --design --hld .devtool/epic/<epic_dir>/<epic_dir>.en.md --tasks .devtool/epic/<epic_dir>/task_*.md`
+1. **Preflight, read-only.** Must exit 0: `python3 "$SCRIPTS"/check_epic_readiness.py <epic_dir>` (runs `check_task_contract.py --design`). Its first line gives the task count.
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
-7. Print `handoff.md` path and rendered Resume Prompt, then stop.
+7. Print `handoff.md` path and rendered Resume Prompt.
+8. Present **Principal Review Choice** — follow [references/principal-review.md](references/principal-review.md).
 
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
 
 Every review round, option 2 or 3, is triaged before anyone acts on it: present `run_external_review.py triage --epic-dir <epic_dir>` filled as dev-implementation's `references/review-triage.md` says, and wait for the developer's decision on each finding.
 
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
@@ -167,49 +164,51 @@ Completed tasks remain in `.devtool/features/done/`. Stop calling tools and pres
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
+- Picking the Principal Review CLI for the developer.
 - Picking the Ollama model for the developer instead of running `ollama list` and asking.
 - Acting on review findings before presenting the triage from `run_external_review.py triage`.
+- Acting on a Principal Review finding before triage.
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

 succeeded in 1978ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-nwxDcqXm' (errno=Operation not permitted)
2026-10-23 17:45:50.719 xcodebuild[26344:2218986]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:50.872 xcodebuild[26344:2218981] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-efgxOFYW' (errno=Operation not permitted)
2026-10-23 17:45:51.419 xcodebuild[26355:2219032]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:51.568 xcodebuild[26355:2219028] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
diff --git a/skills/dev-implementation/SKILL.md b/skills/dev-implementation/SKILL.md
index d59a5e0..5e20a9f 100644
--- a/skills/dev-implementation/SKILL.md
+++ b/skills/dev-implementation/SKILL.md
@@ -51,101 +51,102 @@ This skill is **Stage 3** of the Epic Lifecycle. The surrounding stages, the fiv
 
 #### Bounded Context Injection & Spec Fidelity
 
 Before implementing any task, the executor MUST adhere strictly to the 3-step Bounded Context Injection protocol:
 1. Read the active task file (`.devtool/features/task_*.md`).
 2. Read the Allowed files and Read-only context listed in the task file.
 3. Look up exact symbols and architectural choices declared in `Decisions Already Made`; do not perform undirected whole-repository searches.
 
 **Strict Spec Fidelity**: Implement strictly within the boundaries specified by the active task and its Allowed files. Do not add speculative abstractions, configurability, or adjacent refactoring not requested by the task specification.
 
 2. Resolve the three paths the rest of this skill uses. `SKILL_DIR` is the directory this `SKILL.md` was loaded from:
    ```bash
    SKILL_DIR=<absolute path of the directory containing this SKILL.md>
    REPO_ROOT=$(git rev-parse --show-toplevel)
    INTEGRATE="$SKILL_DIR/../finishing-a-development-branch/resources/scripts/integrate_branch.py"
    ```
 3. Detect the platform:
    ```bash
    PROJECT_TYPE=$("$SKILL_DIR"/resources/scripts/detect_project_type.sh "$REPO_ROOT")
    echo "Detected project type: $PROJECT_TYPE"
    ```
    Supported platforms: `flutter`, `android`, `ios`, `web`, `python`, `rust`.
 4. Run **Entry-Point Detection** before Phase 1. It decides whether Phase 1 starts fresh or the Resume Procedure takes over.
 
 #### Entry-Point Detection
 
 Read these signals, all read-only, from the main checkout:
 
 ```bash
 test -f .devtool/epic/<epic_dir>/handoff.md && echo packaged-handoff
+test -f .devtool/epic/<epic_dir>/principal_review.md && python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --kind principal --epic-dir <epic_dir>
 grep -m1 -E '^- \*\*Status\*\*:' .devtool/epic/<epic_dir>/<epic_dir>.en.md
 git rev-parse --verify --quiet refs/heads/epic/<epic_slug>
 for remote in $(git remote); do git ls-remote --heads "$remote" "epic/<epic_slug>"; done
 git worktree list --porcelain | grep -E '^worktree .*/\.worktrees/<epic_dir>$'
 python3 "$SKILL_DIR"/resources/scripts/compute_execution_order.py <epic_slug> \
   --features-dir .devtool/epic/<epic_dir>
 ```
 
 `git ls-remote` asks each remote directly, so an epic branch pushed from another clone shows before any fetch; if a remote cannot be reached, fall back to `git branch -r --list '*/epic/<epic_slug>'`. The last command reads the epic's task mirrors (`sync_task_status.py` keeps them in step with `.devtool/features/` and `.devtool/features/done/`); its flattened order prints each task's status as `[priority, status]`. Evaluate the rows top-down — first match wins — and announce it: "Entry point: row N — <state>."
 
 | # | Signals | State | Entry point |
 |---|---------|-------|-------------|
 | 1 | Overview Status is `Done` | Finished, or Stage 4 interrupted | With no epic branch left, report finished and stop. With epic branch still present, Stage 4 was interrupted or its PR is still open: report and ask |
 | 2 | No epic branch, and any task is `backlog` | Queued behind another epic | Stop. Flipping `backlog` to `todo` is developer's call |
 | 3 | No epic branch locally or on remote, no worktree, every task `todo` | Not started — packaged if `handoff.md` exists | Phase 1 as written: Gate 3, then new worktree |
 | 4 | Epic branch exists, no worktree, some task not `done` | Interrupted, worktree removed | Resume Procedure |
 | 5 | Worktree exists, some task not `done` | Interrupted midway through Stage 3 | Resume Procedure |
 | 6 | Epic branch exists, every task `done` | Tasks finished | Recreate worktree if missing (`git worktree add .worktrees/<epic_dir> epic/<epic_slug>`, no `-b`) and bootstrap (Phase 1 step 5), run Resume Procedure preflight (step 2), then Phase 4 in full; its PASS presents Review Choice |
 | 7 | Anything else — branch only on remote, or tasks `in-progress` or `done` with no epic branch | Inconsistent | Stop, report signals, ask |
 
 #### Resume Procedure
 
 For rows 4 and 5. Phase 1 step 4's `git worktree add -b` never runs here.
 
 1. Row 4 only: recreate worktree from existing branch, `git worktree add .worktrees/<epic_dir> epic/<epic_slug>` with no `-b`. For rows 4 and 5, check bootstrap with Phase 1 step 5's platform checks and re-run if needed.
 2. In the worktree, run `python3 "$INTEGRATE" preflight --base develop`. A rebase in progress, or diverged base, is handled per Phase 2 step 7 before anything else.
 3. Find the interrupted task: one at `in-progress` or `review`. If worktree has uncommitted changes, collect `git status --short`.
-4. **Gate 3 (resume).** Check mirror scan summary against task mirror count and read Manual review advised section. Run Phase 1 step 3's BDD mapping check and task contract check, including retrofit if needed. Commit any retrofit on epic branch staging only touched files (both `bdd_scenarios`, both HLD variants, task files — never `git add -A`). The interrupted task's own status fields may ride along in that commit; that is expected. Present tasks already `done` with commits (`git log --oneline develop..epic/<epic_slug>`), remaining order with `done` tasks removed, choice on uncommitted changes (keep or discard), and request permission to fast-forward `develop`. Wait for confirmation.
+4. **Gate 3 (resume).** Check mirror scan summary against task mirror count and read Manual review advised section. State the Principal Review status (`not run`, `round <n>: PASS`, or `round <n>: decided`), and stop with the triage if that check exits 1. Run Phase 1 step 3's BDD mapping check and task contract check, including retrofit if needed. Commit any retrofit on epic branch staging only touched files (both `bdd_scenarios`, both HLD variants, task files — never `git add -A`). The interrupted task's own status fields may ride along in that commit; that is expected. Present tasks already `done` with commits (`git log --oneline develop..epic/<epic_slug>`), remaining order with `done` tasks removed, choice on uncommitted changes (keep or discard), and request permission to fast-forward `develop`. Wait for confirmation.
 5. If overview Status begins with `Packaged`, run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`.
 6. Enter Phase 2 at the interrupted task — a task at `review` re-enters at Phase 2 step 2; a task at `in-progress` resumes implementation with kept changes — or at the first remaining task.
 
 ### Phase 1 — Execution Plan
 
 1. Run:
    ```bash
    python3 "$SKILL_DIR"/resources/scripts/compute_execution_order.py <epic_slug>
    ```
    Check scan summary line (`Scanned N task_*.md files; M matched epic ...`). If `M` is smaller than expected, fix broken frontmatter before proceeding.
 2. Read "Manual review advised" section (if any) and cross-check against Phase 0 context. Adjust flattened order by hand if a prose note should win.
 3. **Checkpoint (Gate 3):** present the final order to user and get confirmation before touching git.
-   In the same message, ask once for permission to fast-forward local `develop` from its upstream for the rest of this epic (Phase 1 step 4 and Phase 2 step 7).
+   In the same message, state the Principal Review status (`not run`, `round <n>: PASS`, or `round <n>: decided`; stop with the triage if that check exits 1), and ask once for permission to fast-forward local `develop` from its upstream for the rest of this epic (Phase 1 step 4 and Phase 2 step 7).
 
    Before presenting order, run BDD traceability plan check:
    ```bash
    python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py plan \
      --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md \
      --tasks .devtool/epic/<epic_dir>/task_*.md
    ```
    If needed, add bracketed identifiers to `bdd_scenarios.*.md`, `Covers:` lines to task files, and `Integration test roots:` to HLD. Commit as `[EPIC_NAME] Add BDD scenario identifiers`.
 
    Then check task contract:
    ```bash
    python3 "$SKILL_DIR"/resources/scripts/check_task_contract.py \
      --hld .devtool/epic/<epic_dir>/<epic_dir>.en.md \
      --tasks .devtool/epic/<epic_dir>/task_*.md
    ```
    Do not create worktree until both checks exit 0 and developer has confirmed the order.
 
 #### Phase 1 (continued) — Worktree Bootstrap, once the order is confirmed
 
 4. Bring local `develop` up to date with upstream, then create one worktree for whole epic (`d3nexus:using-git-worktrees`):
    ```bash
    python3 "$INTEGRATE" sync-base --base develop
    git worktree add .worktrees/<epic_dir> -b epic/<epic_slug> develop
    ```
    If `sync-base` exits 3 (diverged or dirty file), stop and ask.
    If overview Status begins with `Packaged`, run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`.
 5. Bootstrap worktree using platform tooling (`bootstrap_worktree.sh`, Gradle sync, Tuist, npm/pnpm, uv sync, cargo check).
 6. Never copy build caches (`.dart_tool/`, `/build/`, `.build/`, `android/**/.cxx/`) from another checkout into this worktree.
 
 ### Phase 2 — Sequential Task Execution

 succeeded in 1977ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-uaP4SnP7' (errno=Operation not permitted)
2026-10-23 17:45:50.719 xcodebuild[26343:2218985]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:50.872 xcodebuild[26343:2218980] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-Uzb3ysUP' (errno=Operation not permitted)
2026-10-23 17:45:51.419 xcodebuild[26353:2219033]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:45:51.568 xcodebuild[26353:2219025] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
diff --git a/docs/lifecycles.en.md b/docs/lifecycles.en.md
index 21ee0a8..9ec6daf 100644
--- a/docs/lifecycles.en.md
+++ b/docs/lifecycles.en.md
@@ -33,81 +33,90 @@ The two quality gates share no tier, no audit and no tooling, and neither invoke
 
 **Purpose.** Orchestrate epic-scale code work from an idea to a merged branch.
 It owns sequence and gates only; each stage's method lives in that stage's own skill.
 
 **What it produces.** A merged branch, plus a High-Level Design in English and Vietnamese,
 a Gherkin BDD suite, and one task file per unit of work
 — all archived into `.devtool/epic/<slug>/` when the epic closes.
 
 **When it does not apply.** A single component that one implementation plan covers.
 That work uses `dev-brainstorming` then `writing-plans`, which leaves this lifecycle and its remaining gates behind.
 
 ```mermaid
 flowchart TD
     S1["Stage 1 — Inception &amp; Spec<br/>(dev-brainstorming)"]
     G1{"Gate 1<br/>Spec approved?"}
     ROUTE{"Epic-scale?"}
     PLANS(["writing-plans<br/>(leaves this workflow)"])
     S2["Stage 2 — Architecture &amp; Tasks<br/>(dev-designer)"]
     G2{"Gate 2<br/>HLD &amp; task breakdown approved?"}
     HC{"Handoff choice<br/>package or continue?"}
-    PKG(["Package epic<br/>handoff.md, status Packaged, stop"])
+    PKG["Package epic<br/>handoff.md, status Packaged"]
+    PRC{"Principal Review Choice<br/>Done or Principal Review?"}
+    PR["run_external_review.py run --kind principal<br/>triage, decisions, revision"]
+    PKGSTOP(["Stop: handoff.md and Resume Prompt"])
     S3["Stage 3 — Isolated Execution<br/>(dev-implementation)"]
     G3{"Gate 3<br/>Execution order confirmed?"}
     EXEC["Phase 2-3: task-by-task TDD<br/>one commit per task, doc sync on divergence,<br/>integrate with develop after each task"]
     RC{"Review Choice<br/>Finish, Cross-model review or Local model review?"}
     XR["run_external_review.py run<br/>(review_results.md committed per round)"]
     LR["run_external_review.py run --cli ollama<br/>(review_results.md committed per round)"]
     G4{"Gate 4<br/>audit + result-based traceability + quality_check 🟢 LGTM?"}
     REVIEW["Phase 4.1: Developer Kanban Review<br/>(All tasks held in DONE column for visual inspection)"]
     G5{"Gate 5<br/>User sign-off &amp; finish approved?"}
     S4["Stage 4 — Finish Branch &amp; Archival<br/>(finishing-a-development-branch)"]
 
     S1 --> G1
     G1 -->|no, revise| S1
     G1 -->|yes| ROUTE
     ROUTE -->|no| PLANS
     ROUTE -->|yes| S2
     S2 --> G2
     G2 -->|no, adjust breakdown| S2
     G2 -->|yes| HC
     HC -->|"1. package"| PKG
     HC -->|"2. continue"| S3
-    PKG -.->|"later session or another LLM"| S3
+    PKG --> PRC
+    PRC -->|"1. Done"| PKGSTOP
+    PRC -->|"2. Principal Review"| PR
+    PR -->|"revised and re-packaged"| PKG
+    PKGSTOP -.->|"later session or another LLM"| S3
     S3 --> G3
     G3 -->|no, reorder| G3
     G3 -->|yes| EXEC
     EXEC --> G4
     G4 -->|"no, fix findings as Fix commits"| EXEC
     G4 -->|"yes"| RC
     RC -->|"1. Finish"| REVIEW
     RC -->|"2. Cross-model review"| XR
     XR -->|"round recorded"| G4
     RC -->|"3. Local model review"| LR
     LR -->|"round recorded"| G4
     REVIEW --> G5
     G5 -->|"no, changes as Fix commits"| EXEC
     G5 -->|yes| S4
 ```
 
 The lifecycle proceeds through four stages and five approval gates, with two explicit human choice points:
 - **Routing & Handoff Choice**: Once Gate 1 passes, epic-scale work routes to Stage 2 (`dev-designer`). Between Gate 2 and Stage 3, the developer chooses whether to **Package** (`handoff.md`, status `Packaged`, stop for later session or another LLM) or **Continue** into Stage 3 immediately.
+
+When an epic is packaged, the developer faces **Principal Review Choice**: either conclude packaging (**Done**) or run **Principal Review** (a cross-model review of design documents and readiness against the source code via Claude CLI or Codex CLI). Rounds are recorded in `principal_review.md`, triaged with the developer, revised in place, and re-packaged before returning to the choice.
 - **Isolated Execution**: Stage 3 executes each task independently in an isolated worktree with TDD and continuous integration into `develop`. Once all tasks are complete, the agent runs Gate 4 on the candidate SHA.
 - **Gate 4 and Review Choice loop**: Gate 4 is the only machine verdict in this kit's development path. It grants 🟢 only when `audit_epic.py` exits 0, `check_bdd_traceability.py tests --results` exits 0, and `@quality_check` profile `epic` returns PASS on the exact candidate commit SHA. Every PASS presents **Review Choice**: **Finish** advances to Gate 5; **Cross-model review** (Claude CLI or Codex CLI) records the round and returns to a full Gate 4 run, and so does **Local model review** (a model served by a local Ollama, reviewed task by task). Every review round is triaged with the developer (`run_external_review.py triage`) before any fix. The loop repeats until the developer selects Finish.
 - **Gate 5 Developer Kanban Review**: Completed tasks are retained in `.devtool/features/done/` for visual developer sign-off before Stage 4 rebases, verifies by tier, lands the branch with a `--no-ff` merge, and archives tasks into `.devtool/epic/<slug>/`.
 
 ### Interrupted and resume states
 
 When work stops or an epic is packaged, the lifecycle resumes deterministically across five operational states:
 
 ```mermaid
 flowchart TD
     FRESH["Fresh Epic<br/>(Stage 1 or Stage 2, no task files)"]
     PKG["Packaged Epic<br/>(handoff.md present, status Packaged)"]
     INTR["Interrupted Epic<br/>(task files exist, mid-Stage 3)"]
     DONE_EPIC["Completed Epic<br/>(all tasks done, Gate 4 PASS)"]
     INCON["Inconsistent State<br/>(documents modified after packaging)"]
 
     FRESH -->|"Stage 1-2 completion"| PKG
     FRESH -->|"Continue at Handoff Choice"| INTR
     PKG -->|"Check git log since packaging"| INCON
     PKG -->|"Resume at Stage 3 Gate 3"| INTR
diff --git a/docs/lifecycles.vi.md b/docs/lifecycles.vi.md
index 1157cfb..582620e 100644
--- a/docs/lifecycles.vi.md
+++ b/docs/lifecycles.vi.md
@@ -36,81 +36,90 @@ Hai cổng chất lượng **không chia sẻ tier, audit hay tooling nào**, v
 
 **Mục đích.** Điều phối công việc code quy mô epic, từ ý tưởng tới nhánh đã merge.
 Nó chỉ sở hữu trình tự và các cổng; cách làm của từng stage nằm trong skill của stage đó.
 
 **Cho ra cái gì.** Một nhánh đã merge, cộng với một High-Level Design bằng tiếng Anh và tiếng Việt,
 một bộ BDD viết bằng Gherkin, và mỗi đơn vị công việc một file task
 — tất cả được archive vào `.devtool/epic/<slug>/` khi epic đóng.
 
 **Khi nào không áp dụng.** Một thành phần đơn lẻ mà một implementation plan là đủ.
 Việc đó dùng `dev-brainstorming` rồi `writing-plans`, tức là rời khỏi lifecycle này cùng các cổng còn lại của nó.
 
 ```mermaid
 flowchart TD
     S1["Stage 1 — Khởi đầu &amp; Spec<br/>(dev-brainstorming)"]
     G1{"Cổng 1<br/>Spec được duyệt?"}
     ROUTE{"Quy mô epic?"}
     PLANS(["writing-plans<br/>(rời workflow này)"])
     S2["Stage 2 — Kiến trúc &amp; Task<br/>(dev-designer)"]
     G2{"Cổng 2<br/>HLD &amp; phân rã task được duyệt?"}
     HC{"Handoff choice<br/>package hay continue?"}
-    PKG(["Package epic<br/>handoff.md, status Packaged, dừng"])
+    PKG["Package epic<br/>handoff.md, status Packaged"]
+    PRC{"Principal Review Choice<br/>Done hay Principal Review?"}
+    PR["run_external_review.py run --kind principal<br/>triage, decisions, chỉnh sửa"]
+    PKGSTOP(["Dừng: handoff.md và Resume Prompt"])
     S3["Stage 3 — Thực thi độc lập<br/>(dev-implementation)"]
     G3{"Cổng 3<br/>Thứ tự thực thi đã xác nhận?"}
     EXEC["Phase 2-3: TDD từng task<br/>mỗi task một commit, sync doc khi lệch,<br/>tích hợp vào develop sau mỗi task"]
     RC{"Review Choice<br/>Finish, Cross-model review hay Local model review?"}
     XR["run_external_review.py run<br/>(commit review_results.md mỗi vòng)"]
     LR["run_external_review.py run --cli ollama<br/>(commit review_results.md mỗi vòng)"]
     G4{"Cổng 4<br/>audit + BDD traceability + quality_check 🟢 LGTM?"}
     REVIEW["Phase 4.1: Developer Kanban Review<br/>(Mọi task giữ ở cột DONE để kiểm tra trực quan)"]
     G5{"Cổng 5<br/>Người dùng ký duyệt &amp; cho phép finish?"}
     S4["Stage 4 — Hoàn tất nhánh &amp; Lưu trữ<br/>(finishing-a-development-branch)"]
 
     S1 --> G1
     G1 -->|chưa, chỉnh sửa| S1
     G1 -->|rồi| ROUTE
     ROUTE -->|không| PLANS
     ROUTE -->|có| S2
     S2 --> G2
     G2 -->|chưa, điều chỉnh phân rã| S2
     G2 -->|rồi| HC
     HC -->|"1. package"| PKG
     HC -->|"2. continue"| S3
-    PKG -.->|"phiên sau hoặc LLM khác"| S3
+    PKG --> PRC
+    PRC -->|"1. Done"| PKGSTOP
+    PRC -->|"2. Principal Review"| PR
+    PR -->|"revised and re-packaged"| PKG
+    PKGSTOP -.->|"phiên sau hoặc LLM khác"| S3
     S3 --> G3
     G3 -->|chưa, sắp xếp lại| G3
     G3 -->|rồi| EXEC
     EXEC --> G4
     G4 -->|"chưa, sửa bằng Fix commit"| EXEC
     G4 -->|"rồi"| RC
     RC -->|"1. Finish"| REVIEW
     RC -->|"2. Cross-model review"| XR
     XR -->|"đã ghi nhận round"| G4
     RC -->|"3. Local model review"| LR
     LR -->|"đã ghi nhận round"| G4
     REVIEW --> G5
     G5 -->|"chưa, yêu cầu đổi bằng Fix commit"| EXEC
     G5 -->|rồi| S4
 ```
 
 Vòng đời trải qua bốn giai đoạn (stage) và năm cổng phê duyệt (approval gate), cùng hai điểm lựa chọn rõ ràng:
 - **Routing & Handoff Choice**: Sau khi qua Cổng 1, công việc quy mô epic đi tới Stage 2 (`dev-designer`). Giữa Cổng 2 và Stage 3, nhà phát triển chọn **Package** (`handoff.md`, trạng thái `Packaged`, dừng để phiên sau hoặc LLM khác làm) hoặc **Continue** vào Stage 3 ngay.
+
+Khi một epic được đóng gói, nhà phát triển đối diện với **Principal Review Choice**: hoặc kết thúc việc đóng gói (**Done**) hoặc chạy **Principal Review** (một đợt rà soát chéo giữa các mô hình đánh giá tài liệu thiết kế và độ sẵn sàng với mã nguồn thông qua Claude CLI hoặc Codex CLI). Các round được ghi nhận trong `principal_review.md`, được triage cùng nhà phát triển, chỉnh sửa tại chỗ, và đóng gói lại trước khi quay lại lựa chọn.
 - **Thực thi độc lập**: Stage 3 thực thi từng task độc lập trong git worktree theo phương pháp TDD và tích hợp liên tục vào `develop`. Khi mọi task đã xong, agent chạy Cổng 4 trên SHA ứng viên.
 - **Vòng lặp Cổng 4 và Review Choice**: Cổng 4 là cổng máy duy nhất trên nhánh phát triển của kit này. Nó chỉ cấp 🟢 khi `audit_epic.py` exit 0, `check_bdd_traceability.py tests --results` exit 0, và `@quality_check` profile `epic` trả về PASS trên đúng commit SHA ứng viên. Mỗi lần PASS sẽ đưa ra **Review Choice**: **Finish** đi tới Cổng 5; **Cross-model review** (Claude CLI hoặc Codex CLI) và **Local model review** (một model do Ollama phục vụ ở máy local, review từng task) đều ghi nhận một round rồi quay lại chạy đầy đủ Cổng 4. Mỗi round review được triage cùng nhà phát triển (`run_external_review.py triage`) trước mọi lần sửa. Vòng lặp tiếp tục cho tới khi nhà phát triển chọn Finish.
 - **Ký duyệt Kanban Cổng 5**: Tất cả task hoàn tất được giữ lại ở `.devtool/features/done/` để nhà phát triển kiểm tra trực quan trên bảng Kanban trước khi Stage 4 rebase, verify theo tier, merge `--no-ff` vào `develop`, và lưu trữ task vào `.devtool/epic/<slug>/`.
 
 ### Trạng thái ngắt quãng và khôi phục (Resume)
 
 Khi công việc tạm dừng hoặc một epic được đóng gói, vòng đời khôi phục một cách tất định qua năm trạng thái vận hành:
 
 ```mermaid
 flowchart TD
     FRESH["Epic mới<br/>(Stage 1 hoặc Stage 2, chưa có task file)"]
     PKG["Epic đã đóng gói<br/>(có handoff.md, trạng thái Packaged)"]
     INTR["Epic bị ngắt quãng<br/>(đã có task file, đang dở Stage 3)"]
     DONE_EPIC["Epic hoàn thành<br/>(mọi task done, Cổng 4 PASS)"]
     INCON["Trạng thái không nhất quán<br/>(tài liệu bị sửa sau khi đóng gói)"]
 
     FRESH -->|"Hoàn tất Stage 1-2"| PKG
     FRESH -->|"Continue tại Handoff Choice"| INTR
     PKG -->|"Kiểm tra git log từ khi đóng gói"| INCON
     PKG -->|"Resume tại Stage 3 Cổng 3"| INTR
diff --git a/skills/dev-lifecycle/references/handoff-template.md b/skills/dev-lifecycle/references/handoff-template.md
index ee95614..3c5596e 100644
--- a/skills/dev-lifecycle/references/handoff-template.md
+++ b/skills/dev-lifecycle/references/handoff-template.md
@@ -15,40 +15,41 @@
 - **Packaged**: <YYYY-MM-DD>
 - **Design commit**: `<sha>` — `HEAD` before the packaging commit, or `uncommitted` when `auto_commit` is false
 - **Base branch**: `<base_branch>`
 - **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
 - **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.
 
 ## Identifiers
 
 | Placeholder | Value |
 |-------------|-------|
 | `<epic_dir>` | `<epic_dir value>` |
 | `<epic_slug>` | `<epic_slug value>` |
 
 These are usually different strings. Never derive one from the other.
 
 ## Read First
 
 1. `.devtool/epic/<epic_dir>/<epic_dir>.en.md` — the HLD. Its Kanban Tasks Breakdown lists the <N> tasks.
 2. `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` — the behavioural contract.
 3. `.devtool/epic/<epic_dir>/<source spec>.en.md` — the approved source spec.
+4. `.devtool/epic/<epic_dir>/principal_review.md`, when present — Principal Review rounds and decisions.
 
 ## Resume Prompt
 
 ```text
 Use the d3nexus:dev-implementation skill for the `<epic_slug>` epic.
 Read .devtool/epic/<epic_dir>/handoff.md first.
 Apply the Execution Guardrails for Receiving LLM before presenting Gate 3.
 Gates 1 and 2 are passed; do not re-run brainstorming or design.
 Gate 3 is pending: present the execution order to me and wait for my confirmation.
 ```
 
 ## Execution Guardrails for Receiving LLM
 
 Fast executor models and receiving agents MUST adhere to these four hard guardrails throughout implementation:
 
 1. **Bounded context protocol**:
    - Step 1: Read only the active task file (`.devtool/features/task_*.md`).
    - Step 2: Read only the exact files declared in `Allowed files` and `Read-only context`.
    - Step 3: Look up exact symbol definitions identified under `## Decisions Already Made`.
    Undirected whole-repository searches (`grep`, `find`, `list_dir`) are forbidden unless an unresolved import explicitly requires symbol lookup.

exec
/bin/zsh -lc "sed -n '60,110p' .devtool/epic/principal_review/2026-10-22-principal-review-design.en.md; sed -n '200,225p' .devtool/epic/principal_review/2026-10-22-principal-review-design.en.md; rg -n -C 3 'fixed in|decisions|Fix commit|Record .*decisions|Revise epic' skills/dev-implementation/references/review-triage.md skills/dev-implementation/SKILL.md rules/CRITICAL_RULES.md .devtool/epic/principal_review/{principal_review.en.md,task_5_principal_review_choice_and_acceptance.md}" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
  chooses Done.

### Non-Goals

- Reviewing code: the post-Gate 4 Review Choice keeps that job.
- Applying edits automatically: the reviewer only proposes.
- Making Principal Review mandatory.
- Running two reviewers in parallel and merging their findings.
- Local Ollama models as Principal Reviewers.

## 3. Decisions

| # | Decision | Reason |
|---|----------|--------|
| D1 | Principal Review is an option offered after every Package, like Review Choice: **1. Done** or **2. Principal Review**. The developer picks Claude CLI or Codex CLI; the agent never picks | The developer's choice (2026-10-22). Review costs credits and tens of minutes, so not every epic needs it |
| D2 | When the epic was designed by a different or fast model (for example an Antigravity session or a Flash-class model), judged from the HLD's `Author` line or the developer's word, the choice carries a strong recommendation for Principal Review | Mirrors the existing fast-executor recommendation in Review Choice; both reviewed epics came from Antigravity |
| D3 | `run_external_review.py` gains `--kind principal`; the default `--kind code` behaves exactly as today | Reuses CLI invocation, round recording, `check`, `triage`, the precondition banner and the tree-change guard. A separate engine would duplicate and drift |
| D4 | `check_epic_readiness.py` is a precondition of a Principal Review round. Any FAIL blocks the CLI (0 credits); its full report is passed to the reviewer as facts | The model's time goes to judgement, not to what a script can decide |
| D5 | `check_epic_readiness.py` replaces the four preflight commands in the packaging procedure | One command instead of four, and it frees words under the 2500-word ceiling of `dev-lifecycle/SKILL.md` |
| D6 | Rounds are recorded in `.devtool/epic/<epic_dir>/principal_review.md`, apart from `review_results.md` | Design findings and code findings have different subjects and different SHAs |
| D7 | A finding is a claim to verify. Every round is triaged with the developer before anything changes; a dismissal needs the developer's own words | Same discipline as `review-triage.md`; reviewers produce false positives |
| D8 | Accepted findings become an in-place revision of the epic (dev-designer edits, no re-split or renumbering), committed as `[EPIC_NAME] Revise epic after Principal Review round <n>`, followed by a full re-package | Keeps one lineage of documents; `handoff.md` stays a dated record and is regenerated, never edited |
| D9 | Done requires `run_external_review.py check --kind principal` to exit 0, when a round exists | No epic is handed over with an undecided Critical or Important finding |
| D10 | Gate 3 runs the same `check` when `principal_review.md` exists and stops on exit 1. An epic never reviewed shows `Principal Review: not run` in the Gate 3 summary | Catches a hand-over that skipped Done; never-reviewed epics stay allowed (D1) |
| D11 | The Continue path (implement now) offers no Principal Review | The developer chose to start immediately; YAGNI |
| D12 | `sync_task_status.py epic` writes only to the current checkout and to worktrees on the epic's own `epic/<epic_slug>` branch. Task-level sync keeps mirroring across every checkout | The re-package loop would otherwise rewrite other epics' worktrees on every round, leaving uncommitted changes another session may commit into the wrong epic |
| D13 | The procedure lives in `dev-lifecycle/references/principal-review.md`; `SKILL.md` keeps a short pointer and the pinned invariants | `SKILL.md` is at 2454 of 2500 words |

## 4. Flow

```mermaid
flowchart TD
    G2["Gate 2 passed"] --> HC{"Handoff Choice"}
    HC -->|"1. Package"| PKG["Package: check_epic_readiness.py, handoff.md, status Packaged"]
    HC -->|"2. Continue"| S3["Stage 3: dev-implementation"]
    PKG --> PRC{"Principal Review Choice"}
    PRC -->|"1. Done"| CHK{"check --kind principal exits 0?"}
    CHK -->|"yes, or no round"| STOP(["Stop: print handoff.md and Resume Prompt"])
    CHK -->|"no"| TRI
    PRC -->|"2. Principal Review"| CLI["Developer picks Claude CLI or Codex CLI"]
    CLI --> RDY{"check_epic_readiness.py passes?"}
    RDY -->|"no: 0 credits"| FIXR["Fix the mechanical failures"]
    FIXR --> PKG
    RDY -->|"yes"| RUN["run_external_review.py run --kind principal"]
    RUN --> TRI["Triage with the developer"]
    TRI --> DEC["Developer decides each finding"]
    DEC --> REV["Revise the epic in place, commit"]
    REV --> PKG
```

## 5. Components
- `docs/lifecycles.en.md` and `docs/lifecycles.vi.md` gain the Principal Review Choice loop in the Stage 2 diagram, and one paragraph.
- `handoff-template.md` lists `principal_review.md, when present` under Read First.

## 6. Principal Review Loop Procedure

1. After the packaging procedure prints `handoff.md`, present:
   > Packaged. 1. **Done** — stop here. 2. **Principal Review** — a cross-model review of the design against the source before implementation (Claude CLI or Codex CLI).

   Add the D2 recommendation when it applies.
2. **Done**: if `principal_review.md` exists, run `check --kind principal`. Exit 0 stops with the handoff path and the Resume Prompt; exit 1 goes to step 5.
3. **Principal Review**: ask which CLI, Claude CLI or Codex CLI, and optionally which model. Never choose for the developer.
4. Run `run_external_review.py run --kind principal --epic-dir <epic_dir> --base <base_branch> --cli <cli>`. A readiness FAIL prints the banner: fix the named failures as an epic revision, re-package, and return to step 1.
5. Present `triage --kind principal`, filled as `review-triage.md` describes: every finding is verified against the source at the round's SHA. Stop and wait for the developer's decision on each finding.
6. Apply each accepted finding as an in-place revision of the epic (D8). Write the Decision cells (`fixed in <sha>` or `dismissed: <developer's words>`) and commit `[EPIC_NAME] Revise epic after Principal Review round <n>`.
7. Re-run the packaging procedure from step 1: readiness, a regenerated `handoff.md` with the new design commit, lint, status, commit. Then return to step 1 of this procedure.

## 7. Error Handling

| Situation | Behaviour |
|---|---|
| CLI not on PATH, dirty tree, `--cli ollama` with `--kind principal` | Exit 2; no round recorded |
| `check_epic_readiness.py` FAIL | Precondition banner, CLI not invoked, exit 2; the report names each failure |
| R8 row exceeds `--row-timeout` | WARN `timeout` for that row; the other rows still run |
| Reviewer output has no Verdict line | Round recorded as incomplete, exit 2, as for code review |
| Reviewer changes a file despite read-only mode | Existing tree-change guard records the paths in the round |
| Developer chooses Done with undecided blocking findings | Done refused; triage presented (D9) |
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-93-  Given docs/lifecycles.en.md, docs/lifecycles.vi.md and skills/dev-lifecycle/references/principal-review.md
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-94-  Then both documents contain 'PKG --> PRC', 'PRC -->|"2. Principal Review"| PR' and 'PR -->|"revised and re-packaged"| PKG'
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-95-  And neither document has an edge from PR to S3 or to G3
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:96:  And the reference contains "Record Principal Review round <n>", "Revise epic after Principal Review round <n>" and "Package epic for handoff"
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-97-  And the reference states that Done runs "check --kind principal" and re-packages when the last commit touching the epic directory is not the Package commit
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-98-
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-99-Scenario: [PRV-ST-04] [Tier C - Integration] Gate 3 stops while a blocking principal finding is undecided
--
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-144-    - the sentence `Never choose for the developer.`;
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-145-    - the D2 recommendation including the words `strongly recommended`, judged from the HLD's `Author` line or the developer's word;
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-146-    - the commands `run_external_review.py run --kind principal --epic-dir <epic_dir> --base <base_branch> --cli <claude|codex>`, `triage --kind principal` and `check --kind principal`;
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:147:  - the commit titles `[EPIC_NAME] Record Principal Review round <n>`, `[EPIC_NAME] Record Principal Review decisions for round <n>` and `[EPIC_NAME] Revise epic after Principal Review round <n>` (C2);
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-148-  - the Done rule: run `check --kind principal`, which must exit 0. Then re-run the packaging procedure when `git log -1 --format=%s -- .devtool/epic/<epic_dir>` is not `[<EPIC_NAME>] Package epic for handoff` (C3). Then print the handoff path and the Resume Prompt and stop;
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-149-  - it ends by pointing at `../../dev-implementation/references/review-triage.md` for how to fill the triage.
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-150-- **`dev-implementation/SKILL.md`**:
--
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-152-  - Phase 1 step 3 (Gate 3) and Resume Procedure step 4 (Gate 3, resume) each state the Principal Review status, `not run`, `round <n>: PASS` or `round <n>: decided`, and stop with the triage when that check exits 1;
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-153-  - the file stays at 4500 words or fewer.
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-154-- **`handoff-template.md`**:
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:155:  - Read First gains `4. \`.devtool/epic/<epic_dir>/principal_review.md\`, when present — Principal Review rounds and decisions.`;
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-156-  - the staleness command `git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>` is unchanged.
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-157-- **`docs/lifecycles.en.md` and `docs/lifecycles.vi.md`, Stage 2 diagram**:
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-158-  - the terminal `PKG([...])` node becomes `PKG["Package epic<br/>handoff.md, status Packaged"]`;
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:159:  - add `PRC{"Principal Review Choice<br/>Done or Principal Review?"}` and `PR["run_external_review.py run --kind principal<br/>triage, decisions, revision"]`;
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-160-  - add the edges `PKG --> PRC`, `PRC -->|"1. Done"| PKGSTOP(["Stop: handoff.md and Resume Prompt"])`, `PRC -->|"2. Principal Review"| PR` and `PR -->|"revised and re-packaged"| PKG`;
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-161-  - add one paragraph after the Routing & Handoff Choice bullet. The Vietnamese node labels may be translated; the edge labels are kept verbatim.
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md-162-- **`scripts/test_lifecycle_document_contract.py`**:
--
.devtool/epic/principal_review/principal_review.en.md-36-The kit can already ask Claude CLI or Codex CLI for a read-only second opinion, but only on
.devtool/epic/principal_review/principal_review.en.md-37-finished code after Gate 4. This epic adds a mechanical readiness check and an optional
.devtool/epic/principal_review/principal_review.en.md-38-cross-model **Principal Review** of the design, offered after Package and looping until the
.devtool/epic/principal_review/principal_review.en.md:39:developer chooses Done. The approved spec holds the full motivation and decisions D1–D13.
.devtool/epic/principal_review/principal_review.en.md-40-
.devtool/epic/principal_review/principal_review.en.md-41-## Goals and Non-Goals
.devtool/epic/principal_review/principal_review.en.md-42-
--
.devtool/epic/principal_review/principal_review.en.md-160-    Agent->>Agent: commit Record Principal Review round n
.devtool/epic/principal_review/principal_review.en.md-161-    Agent->>Runner: triage --kind principal --epic-dir epic_dir
.devtool/epic/principal_review/principal_review.en.md-162-    Agent->>Dev: filled triage, each finding verified against the source
.devtool/epic/principal_review/principal_review.en.md:163:    Dev->>Agent: decisions
.devtool/epic/principal_review/principal_review.en.md-164-    Agent->>Agent: revise epic in place, Decision cells, commit
.devtool/epic/principal_review/principal_review.en.md-165-    Agent->>Ready: re-package from step 1
.devtool/epic/principal_review/principal_review.en.md-166-    Agent->>Dev: Principal Review Choice again
--
.devtool/epic/principal_review/principal_review.en.md-292-- **`dev-implementation/SKILL.md`**:
.devtool/epic/principal_review/principal_review.en.md-293-  - Entry-Point Detection gains `test -f .devtool/epic/<epic_dir>/principal_review.md && python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --kind principal --epic-dir <epic_dir>`;
.devtool/epic/principal_review/principal_review.en.md-294-  - Phase 1 step 3 and Resume Gate 3 both state the Principal Review status (`not run`, `round <n>: PASS` or `round <n>: decided`), and stop on exit 1.
.devtool/epic/principal_review/principal_review.en.md:295:- **`handoff-template.md`**: Read First gains `4. .devtool/epic/<epic_dir>/principal_review.md, when present — Principal Review rounds and decisions.`
.devtool/epic/principal_review/principal_review.en.md-296-- **`docs/lifecycles.en.md` and `docs/lifecycles.vi.md`**: the Stage 2 diagram gains `PRC{"Principal Review Choice"}`, `PKG --> PRC`, `PRC -->|"1. Done"| …`, `PRC -->|"2. Principal Review"| PR` and `PR -->|"revised and re-packaged"| PKG`, plus one paragraph.
.devtool/epic/principal_review/principal_review.en.md-297-
.devtool/epic/principal_review/principal_review.en.md-298-### Clarifications of the Spec
--
.devtool/epic/principal_review/principal_review.en.md-302-| # | Clarification | Why |
.devtool/epic/principal_review/principal_review.en.md-303-|---|---|---|
.devtool/epic/principal_review/principal_review.en.md-304-| C1 | R7's reverse direction accepts `In Progress` and `Done`: a resumed epic keeps its `handoff.md` | The spec's "and the reverse" would fail every resumed epic |
.devtool/epic/principal_review/principal_review.en.md:305:| C2 | Each recorded round is committed as `[EPIC_NAME] Record Principal Review round <n>`, and its decisions as `[EPIC_NAME] Record Principal Review decisions for round <n>` | `run` refuses a dirty tree, so a round must be committed before the next one |
.devtool/epic/principal_review/principal_review.en.md-306-| C3 | Done re-runs the packaging procedure when `git log -1 --format=%s -- .devtool/epic/<epic_dir>` is not `[<EPIC_NAME>] Package epic for handoff` | Keeps the handoff staleness command pinned by `test_lf_st_02` exact without changing it |
.devtool/epic/principal_review/principal_review.en.md-307-| C4 | The readiness report's first line carries the task count | The packaging step 2 token "`<N>` is the task count the preflight printed" is pinned |
.devtool/epic/principal_review/principal_review.en.md-308-| C5 | R8 evaluates rows with `run_task_checks.run_command` and `mismatch` | One definition of a row's Expect |
--
skills/dev-implementation/references/review-triage.md-27-5. Read `## Round Comparison` and `## Since Round <n>`. Fewer Critical and Important findings, and
skills/dev-implementation/references/review-triage.md-28-   fixed findings that are not re-reported, show the fixes worked. A fixed finding re-reported at the
skills/dev-implementation/references/review-triage.md-29-   same path says `check the fix`: look at it again before deciding.
skills/dev-implementation/references/review-triage.md:30:6. Replace the Next Steps line with numbered actions: the Fix commits, the decisions to record, and,
skills/dev-implementation/references/review-triage.md-31-   when blocking findings will be fixed, a confirmation round whose triage measures the improvement.
skills/dev-implementation/references/review-triage.md-32-7. Present the filled triage and stop. Wait until the developer decides each finding.
skills/dev-implementation/references/review-triage.md-33-
skills/dev-implementation/references/review-triage.md-34-## After the developer decides
skills/dev-implementation/references/review-triage.md-35-
skills/dev-implementation/references/review-triage.md-36-- Make each fix as its own commit titled `[EPIC_NAME] Fix <what>`.
skills/dev-implementation/references/review-triage.md:37:- Write each Decision cell in `review_results.md`: `fixed in <sha>`, or `dismissed: <reason>` in the
skills/dev-implementation/references/review-triage.md-38-  developer's own words. Never write a dismissal the developer did not give.
skills/dev-implementation/references/review-triage.md:39:- Commit the decisions, then run Phase 4 / Gate 4 in full on the new SHA.
--
rules/CRITICAL_RULES.md-83->    - **Option 2: Cross-model review** — invoke an independent model review using `run_external_review.py run` (prompting the developer to select Claude CLI or Codex CLI based on `command -v claude codex`).
rules/CRITICAL_RULES.md-84->    - **Option 3: Local model review** — run `ollama list`, ask the developer which model to use (never pick it), then invoke `run_external_review.py run --cli ollama --model <model>`.
rules/CRITICAL_RULES.md-85-> 2. The AI Agent **MUST NOT** auto-select an option or assume "Finish" by default.
rules/CRITICAL_RULES.md:86:> 3. **Cross-model review must return to a full Gate 4 run** after the round is recorded and all blocking findings have decisions and required Fix commits. Gate 4 PASS then presents Review Choice again. This loop repeats until the developer explicitly chooses Finish. Local model review follows the same loop. Before any Fix commit or decision, the agent presents the triage from `run_external_review.py triage` and waits for the developer's decisions.
rules/CRITICAL_RULES.md:87:> 4. A previous Gate 4 PASS cannot be reused after `review_results.md`, a finding decision, or a Fix commit changes the candidate SHA.
--
skills/dev-implementation/SKILL.md-43-   - Otherwise `<name>` is a slug, and `<epic_dir>` is the directory holding the files `grep -l -F 'epic: "<name>"' .devtool/epic/*/task_*.md` lists.
skills/dev-implementation/SKILL.md-44-   - With no name, or no match, list the epic directories whose overview Status is not `Done` and ask which one. Never guess, even when only one is listed.
skills/dev-implementation/SKILL.md-45-1. Read, in full:
skills/dev-implementation/SKILL.md:46:   - `.devtool/epic/<epic_dir>/<epic_dir>.en.md` (the canonical HLD — never `.vi.md` for decisions, that's a synced translation).
skills/dev-implementation/SKILL.md-47-   - `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` (the canonical behavioral contract across the 5 dimensions, if present; `.vi.md` is its synchronized translation).
skills/dev-implementation/SKILL.md-48-   - Every `.devtool/features/task_*.md` whose frontmatter `epic:` matches `<epic_slug>`.
skills/dev-implementation/SKILL.md-49-   - Any spec file(s) linked from the HLD's Meta Data section.
--
skills/dev-implementation/SKILL.md-249-
skills/dev-implementation/SKILL.md-250-Once every task is `done`, resolve candidate commit SHA (`git rev-parse HEAD`) with a clean tree (`git status --porcelain` prints nothing):
skills/dev-implementation/SKILL.md-251-
skills/dev-implementation/SKILL.md:252:1. **Review decisions**, only when `.devtool/epic/<epic_dir>/review_results.md` exists:
skills/dev-implementation/SKILL.md-253-   ```bash
skills/dev-implementation/SKILL.md-254-   python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --epic-dir <epic_dir>
skills/dev-implementation/SKILL.md-255-   ```
skills/dev-implementation/SKILL.md:256:   Exit 1 means unresolved finding: record decision or make Fix commit, then restart Phase 4 in full.
skills/dev-implementation/SKILL.md-257-2. **Gate 4 audit**:
skills/dev-implementation/SKILL.md-258-   ```bash
skills/dev-implementation/SKILL.md-259-   python3 "$SKILL_DIR"/resources/scripts/audit_epic.py --epic-dir <epic_dir> --base <base_ref>
--
skills/dev-implementation/SKILL.md-313-python3 "$SKILL_DIR"/resources/scripts/run_external_review.py run \
skills/dev-implementation/SKILL.md-314-  --epic-dir <epic_dir> --base <base_ref> --cli claude|codex
skills/dev-implementation/SKILL.md-315-```
skills/dev-implementation/SKILL.md:316:Commit `review_results.md` after every round (`[EPIC_NAME] Record cross-model review round N`). After every round of option 2 or 3, run `python3 "$SKILL_DIR"/resources/scripts/run_external_review.py triage --epic-dir <epic_dir>`, fill it as [review-triage.md](references/review-triage.md) says, present it, and wait for the developer's decisions before any Fix commit or Decision cell. Then make the Fix commits, record the decisions, commit, and rerun Phase 4 / Gate 4 in full.
skills/dev-implementation/SKILL.md-317-
skills/dev-implementation/SKILL.md-318-Option 3 runs `ollama list` first and asks the developer which model to use; never pick it. Then, in the epic worktree with a clean tree:
skills/dev-implementation/SKILL.md-319-```bash

exec
/bin/zsh -lc "rg -n -C 6 'Design commit|check_metadata|R7|principal_artefact_lines|run_principal|record_round|epic_checkout_roots|parse_worktree_branches' skills/dev-implementation/resources/scripts/test_check_epic_readiness.py skills/dev-implementation/resources/scripts/test_run_external_review.py skills/dev-implementation/resources/scripts/test_sync_task_status.py" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
skills/dev-implementation/resources/scripts/test_run_external_review.py-510-    def setUp(self) -> None:
skills/dev-implementation/resources/scripts/test_run_external_review.py-511-        super().setUp()
skills/dev-implementation/resources/scripts/test_run_external_review.py-512-        tcer.build_ready_epic(self.root)
skills/dev-implementation/resources/scripts/test_run_external_review.py-513-        self.commit("Ready epic")
skills/dev-implementation/resources/scripts/test_run_external_review.py-514-        self.principal_results = self.root / ".devtool" / "epic" / "demo_epic" / "principal_review.md"
skills/dev-implementation/resources/scripts/test_run_external_review.py-515-
skills/dev-implementation/resources/scripts/test_run_external_review.py:516:    def run_principal(self, *extra: str, cli: str = "claude", mode: str = "pass") -> tuple[int, str, str]:
skills/dev-implementation/resources/scripts/test_run_external_review.py-517-        out, err = io.StringIO(), io.StringIO()
skills/dev-implementation/resources/scripts/test_run_external_review.py-518-        with mock.patch.dict(os.environ, {"FAKE_MODE": mode}), \
skills/dev-implementation/resources/scripts/test_run_external_review.py-519-                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
skills/dev-implementation/resources/scripts/test_run_external_review.py-520-            code = main(["run", "--kind", "principal", "--epic-dir", "demo_epic", "--base", "main", "--cli", cli, *extra])
skills/dev-implementation/resources/scripts/test_run_external_review.py-521-        return code, out.getvalue(), err.getvalue()
skills/dev-implementation/resources/scripts/test_run_external_review.py-522-
skills/dev-implementation/resources/scripts/test_run_external_review.py-523-    def test_prv_hp_02_principal_round_recorded_in_principal_review_md(self) -> None:
skills/dev-implementation/resources/scripts/test_run_external_review.py-524-        """PRV-HP-02: A principal round is recorded in principal_review.md."""
skills/dev-implementation/resources/scripts/test_run_external_review.py-525-        self.install("claude")
skills/dev-implementation/resources/scripts/test_run_external_review.py:526:        code, out, err = self.run_principal()
skills/dev-implementation/resources/scripts/test_run_external_review.py-527-        self.assertEqual(code, 0, f"Expected 0, got {code}.\nOut:\n{out}\nErr:\n{err}")
skills/dev-implementation/resources/scripts/test_run_external_review.py-528-        prompt = self.stdin.read_text(encoding="utf-8")
skills/dev-implementation/resources/scripts/test_run_external_review.py-529-        self.assertIn("Principal Reviewer", prompt)
skills/dev-implementation/resources/scripts/test_run_external_review.py-530-        self.assertIn("Result: 0 FAIL, 0 WARN — PASS", prompt)
skills/dev-implementation/resources/scripts/test_run_external_review.py-531-        self.assertIn(".devtool/epic/demo_epic/demo_epic.en.md", prompt)
skills/dev-implementation/resources/scripts/test_run_external_review.py-532-        main_sha = git(self.root, "rev-parse", "main")
--
skills/dev-implementation/resources/scripts/test_run_external_review.py-543-        self.assertIn("- **Verdict**: PASS", text)
skills/dev-implementation/resources/scripts/test_run_external_review.py-544-        self.assertFalse((self.root / ".devtool" / "epic" / "demo_epic" / "review_results.md").exists())
skills/dev-implementation/resources/scripts/test_run_external_review.py-545-
skills/dev-implementation/resources/scripts/test_run_external_review.py-546-    def test_prv_hp_03_findings_with_proposed_edits_become_table_rows(self) -> None:
skills/dev-implementation/resources/scripts/test_run_external_review.py-547-        """PRV-HP-03: Findings with proposed edits become table rows and set exit code."""
skills/dev-implementation/resources/scripts/test_run_external_review.py-548-        self.install("codex")
skills/dev-implementation/resources/scripts/test_run_external_review.py:549:        code, out, err = self.run_principal(cli="codex", mode="principal_changes")
skills/dev-implementation/resources/scripts/test_run_external_review.py-550-        self.assertEqual(code, 1, f"Expected 1, got {code}.\nOut:\n{out}\nErr:\n{err}")
skills/dev-implementation/resources/scripts/test_run_external_review.py-551-        text = self.principal_results.read_text(encoding="utf-8")
skills/dev-implementation/resources/scripts/test_run_external_review.py-552-        self.assertIn("- **Verdict**: CHANGES REQUIRED", text)
skills/dev-implementation/resources/scripts/test_run_external_review.py-553-        self.assertIn("| Important |", text)
skills/dev-implementation/resources/scripts/test_run_external_review.py-554-        self.assertIn("task_2:Decisions Already Made", text)
skills/dev-implementation/resources/scripts/test_run_external_review.py-555-        self.assertIn("Proposed: keep TrackPersistResult.", text)
skills/dev-implementation/resources/scripts/test_run_external_review.py-556-
skills/dev-implementation/resources/scripts/test_run_external_review.py-557-    def test_prv_st_01_decisions_move_check_from_1_to_0(self) -> None:
skills/dev-implementation/resources/scripts/test_run_external_review.py-558-        """PRV-ST-01: Decisions move check --kind principal from 1 to 0, independent of code rounds."""
skills/dev-implementation/resources/scripts/test_run_external_review.py-559-        self.install("claude")
skills/dev-implementation/resources/scripts/test_run_external_review.py:560:        code, _, _ = self.run_principal(mode="principal_changes")
skills/dev-implementation/resources/scripts/test_run_external_review.py-561-        self.assertEqual(code, 1)
skills/dev-implementation/resources/scripts/test_run_external_review.py-562-
skills/dev-implementation/resources/scripts/test_run_external_review.py-563-        # Code review results with no findings (clean round)
skills/dev-implementation/resources/scripts/test_run_external_review.py-564-        code_rev_path = self.root / ".devtool" / "epic" / "demo_epic" / "review_results.md"
skills/dev-implementation/resources/scripts/test_run_external_review.py-565-        code_rev_path.write_text(
skills/dev-implementation/resources/scripts/test_run_external_review.py-566-            "# Cross-Model Review: demo_epic\n\n## Round 1\n\n- **Status**: completed\n- **Verdict**: PASS\n\n"
--
skills/dev-implementation/resources/scripts/test_run_external_review.py-636-
skills/dev-implementation/resources/scripts/test_run_external_review.py-637-    def test_prv_ar_01_second_round_before_commit_refused(self) -> None:
skills/dev-implementation/resources/scripts/test_run_external_review.py-638-        """PRV-AR-01: A second round before the first is committed is refused and rounds number in order."""
skills/dev-implementation/resources/scripts/test_run_external_review.py-639-        self.install("claude")
skills/dev-implementation/resources/scripts/test_run_external_review.py-640-        counter = self.bin.parent / "fake_counter.txt"
skills/dev-implementation/resources/scripts/test_run_external_review.py-641-        with mock.patch.dict(os.environ, {"FAKE_COUNTER": str(counter)}):
skills/dev-implementation/resources/scripts/test_run_external_review.py:642:            code1, _, _ = self.run_principal()
skills/dev-implementation/resources/scripts/test_run_external_review.py-643-            self.assertEqual(code1, 0)
skills/dev-implementation/resources/scripts/test_run_external_review.py-644-            self.assertEqual(len(counter.read_text().splitlines()), 1)
skills/dev-implementation/resources/scripts/test_run_external_review.py-645-
skills/dev-implementation/resources/scripts/test_run_external_review.py-646-            # Round 1 is written but uncommitted
skills/dev-implementation/resources/scripts/test_run_external_review.py:647:            code2, _, err2 = self.run_principal()
skills/dev-implementation/resources/scripts/test_run_external_review.py-648-            self.assertEqual(code2, 2)
skills/dev-implementation/resources/scripts/test_run_external_review.py-649-            self.assertIn("commit or stash your changes before a review", err2)
skills/dev-implementation/resources/scripts/test_run_external_review.py-650-            self.assertEqual(len(counter.read_text().splitlines()), 1)
skills/dev-implementation/resources/scripts/test_run_external_review.py-651-
skills/dev-implementation/resources/scripts/test_run_external_review.py-652-            # Commit round 1
skills/dev-implementation/resources/scripts/test_run_external_review.py-653-            self.commit("Record round 1")
skills/dev-implementation/resources/scripts/test_run_external_review.py-654-
skills/dev-implementation/resources/scripts/test_run_external_review.py-655-            # Run again
skills/dev-implementation/resources/scripts/test_run_external_review.py:656:            code3, _, _ = self.run_principal()
skills/dev-implementation/resources/scripts/test_run_external_review.py-657-            self.assertEqual(code3, 0)
skills/dev-implementation/resources/scripts/test_run_external_review.py-658-            self.assertEqual(len(counter.read_text().splitlines()), 2)
skills/dev-implementation/resources/scripts/test_run_external_review.py-659-
skills/dev-implementation/resources/scripts/test_run_external_review.py-660-            text = self.principal_results.read_text(encoding="utf-8")
skills/dev-implementation/resources/scripts/test_run_external_review.py-661-            self.assertIn("## Round 1", text)
skills/dev-implementation/resources/scripts/test_run_external_review.py-662-            self.assertIn("## Round 2", text)
--
skills/dev-implementation/resources/scripts/test_run_external_review.py-679-        )
skills/dev-implementation/resources/scripts/test_run_external_review.py-680-        self.commit("Break R5 readiness")
skills/dev-implementation/resources/scripts/test_run_external_review.py-681-
skills/dev-implementation/resources/scripts/test_run_external_review.py-682-        self.install("claude")
skills/dev-implementation/resources/scripts/test_run_external_review.py-683-        counter = self.bin.parent / "fake_counter.txt"
skills/dev-implementation/resources/scripts/test_run_external_review.py-684-        with mock.patch.dict(os.environ, {"FAKE_COUNTER": str(counter)}):
skills/dev-implementation/resources/scripts/test_run_external_review.py:685:            code, out, err = self.run_principal()
skills/dev-implementation/resources/scripts/test_run_external_review.py-686-            self.assertEqual(code, 2)
skills/dev-implementation/resources/scripts/test_run_external_review.py-687-            self.assertIn("WAS NOT INVOKED", err)
skills/dev-implementation/resources/scripts/test_run_external_review.py-688-            self.assertIn("check_epic_readiness.py", err)
skills/dev-implementation/resources/scripts/test_run_external_review.py-689-            self.assertIn("R5 FAIL", err)
skills/dev-implementation/resources/scripts/test_run_external_review.py-690-            self.assertFalse(counter.exists())
skills/dev-implementation/resources/scripts/test_run_external_review.py-691-            self.assertFalse(self.principal_results.exists())
--
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-426-            "R1 PASS",
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-427-            "R2 PASS",
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-428-            "R3 PASS",
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-429-            "R4 PASS",
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-430-            "R5 PASS",
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-431-            "R6 PASS",
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:432:            "R7 PASS",
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-433-            "R8 SKIP",
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-434-        ]
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-435-        for expected in expected_checks:
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-436-            self.assertIn(expected, stdout)
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-437-
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-438-        self.assertEqual(lines[-1], "Result: 0 FAIL, 0 WARN — PASS")
--
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-491-        self.assertTrue(
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-492-            any("task_1" in line and "Stale sentence." in line for line in r2_fails),
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-493-            f"Expected R2 FAIL containing 'task_1' and 'Stale sentence.', got:\n{stdout2}",
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-494-        )
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-495-
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-496-    def test_prv_ec_05_metadata_packaged_without_handoff_and_draft_spec(self) -> None:
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:497:        """PRV-EC-05: Packaged without a handoff fails R7 and a draft spec warns R7b."""
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-498-        hld_path = self.root / ".devtool" / "epic" / "demo_epic" / "demo_epic.en.md"
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-499-        hld_text = hld_path.read_text(encoding="utf-8").replace("- **Status**: Planned", "- **Status**: Packaged")
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-500-        hld_path.write_text(hld_text, encoding="utf-8")
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-501-
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-502-        spec_path = self.root / ".devtool" / "epic" / "demo_epic" / "2026-10-22-demo-epic-design.en.md"
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-503-        spec_text = spec_path.read_text(encoding="utf-8").replace(
--
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-505-            "- **Status**: Draft, awaiting Gate 1 review",
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-506-        )
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-507-        spec_path.write_text(spec_text, encoding="utf-8")
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-508-
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-509-        code, stdout, _stderr = self.run_check("demo_epic")
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-510-        self.assertEqual(code, 1, f"Expected 1, got {code}.\nStdout:\n{stdout}")
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:511:        self.assertTrue(any(line.startswith("R7 FAIL") and "handoff.md" in line for line in stdout.splitlines()))
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-512-        self.assertTrue(
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-513-            any(
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:514:                line.startswith("R7b WARN") and "Draft, awaiting Gate 1 review" in line
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-515-                for line in stdout.splitlines()
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-516-            )
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-517-        )
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-518-
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:519:        # Add handoff.md with Design commit: `uncommitted`
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-520-        handoff_content = """# Handoff: demo_epic
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-521-
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-522-## Table of Contents
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-523-
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-524-- [Status](#status)
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-525-
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-526-## Status
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-527-
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:528:- **Design commit**: `uncommitted`
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-529-"""
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-530-        (self.root / ".devtool" / "epic" / "demo_epic" / "handoff.md").write_text(handoff_content, encoding="utf-8")
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-531-
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-532-        code2, stdout2, _stderr2 = self.run_check("demo_epic")
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-533-        self.assertEqual(code2, 0, f"Expected 0 after adding handoff, got {code2}.\nStdout:\n{stdout2}")
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:534:        self.assertIn("R7 PASS", stdout2)
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-535-
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-536-    def test_prv_fr_02_failing_preflight_subcheck_and_missing_dir(self) -> None:
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-537-        """PRV-FR-02: A failing preflight sub-check fails R1 by name; missing dir exits 2."""
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-538-        bdd_path = self.root / ".devtool" / "epic" / "demo_epic" / "bdd_scenarios.en.md"
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-539-        bdd_text = bdd_path.read_text(encoding="utf-8")
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py-540-        extra_scenario = """
--
skills/dev-implementation/resources/scripts/test_sync_task_status.py-812-        git(self.main, "add", "-A")
skills/dev-implementation/resources/scripts/test_sync_task_status.py-813-        git(self.main, "commit", "-q", "-m", "initial commit")
skills/dev-implementation/resources/scripts/test_sync_task_status.py-814-
skills/dev-implementation/resources/scripts/test_sync_task_status.py-815-        git(self.main, "worktree", "add", "-q", "-b", "epic/demo-epic", str(self.wt_own))
skills/dev-implementation/resources/scripts/test_sync_task_status.py-816-        git(self.main, "worktree", "add", "-q", "-b", "epic/other-epic", str(self.wt_other))
skills/dev-implementation/resources/scripts/test_sync_task_status.py-817-
skills/dev-implementation/resources/scripts/test_sync_task_status.py:818:    def test_parse_worktree_branches(self) -> None:
skills/dev-implementation/resources/scripts/test_sync_task_status.py-819-        sample = f"""worktree {self.main}
skills/dev-implementation/resources/scripts/test_sync_task_status.py-820-HEAD 1111111111111111111111111111111111111111
skills/dev-implementation/resources/scripts/test_sync_task_status.py-821-branch refs/heads/main
skills/dev-implementation/resources/scripts/test_sync_task_status.py-822-
skills/dev-implementation/resources/scripts/test_sync_task_status.py-823-worktree {self.wt_own}
skills/dev-implementation/resources/scripts/test_sync_task_status.py-824-HEAD 2222222222222222222222222222222222222222
skills/dev-implementation/resources/scripts/test_sync_task_status.py-825-branch refs/heads/epic/demo-epic
skills/dev-implementation/resources/scripts/test_sync_task_status.py-826-
skills/dev-implementation/resources/scripts/test_sync_task_status.py-827-worktree {self.base / "wt_detached"}
skills/dev-implementation/resources/scripts/test_sync_task_status.py-828-HEAD 3333333333333333333333333333333333333333
skills/dev-implementation/resources/scripts/test_sync_task_status.py-829-detached
skills/dev-implementation/resources/scripts/test_sync_task_status.py-830-"""
skills/dev-implementation/resources/scripts/test_sync_task_status.py:831:        from sync_task_status import parse_worktree_branches
skills/dev-implementation/resources/scripts/test_sync_task_status.py:832:        branches = parse_worktree_branches(sample)
skills/dev-implementation/resources/scripts/test_sync_task_status.py-833-        self.assertEqual(len(branches), 3)
skills/dev-implementation/resources/scripts/test_sync_task_status.py-834-        self.assertEqual(branches[0], (self.main, "refs/heads/main"))
skills/dev-implementation/resources/scripts/test_sync_task_status.py-835-        self.assertEqual(branches[1], (self.wt_own, "refs/heads/epic/demo-epic"))
skills/dev-implementation/resources/scripts/test_sync_task_status.py-836-        self.assertEqual(branches[2], (self.base / "wt_detached", None))
skills/dev-implementation/resources/scripts/test_sync_task_status.py-837-
skills/dev-implementation/resources/scripts/test_sync_task_status.py-838-    def test_prv_hp_05_own_worktree_updated(self) -> None:

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/test_check_epic_readiness.py | sed -n '1,420p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""Tests for check_epic_readiness.py (Task 1: Readiness Check Core).
     3	
     4	Run:
     5	    python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k ReadinessCoreTest
     6	"""
     7	from __future__ import annotations
     8	
     9	import subprocess
    10	import sys
    11	import tempfile
    12	import unittest
    13	from pathlib import Path
    14	from typing import Any
    15	
    16	SCRIPTS_DIR = Path(__file__).resolve().parent
    17	SCRIPT_PATH = SCRIPTS_DIR / "check_epic_readiness.py"
    18	
    19	# Try importing the module under test
    20	try:
    21	    import check_epic_readiness
    22	except ImportError:
    23	    check_epic_readiness = None  # type: ignore[assignment]
    24	
    25	
    26	def git_cmd(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    27	    return subprocess.run(
    28	        ["git", "-C", str(root), *args],
    29	        capture_output=True,
    30	        text=True,
    31	        check=True,
    32	    )
    33	
    34	
    35	def build_ready_epic(root: Path) -> None:
    36	    """Writes the PRV-HP-01 epic demo_epic (slug demo-epic, 2 tasks) into root.
    37	
    38	    Commits nothing related to the epic.
    39	    """
    40	    # Ensure baseline repo tracked files exist and are committed
    41	    tracked = subprocess.run(
    42	        ["git", "-C", str(root), "ls-files", "tool.py"],
    43	        check=False,
    44	        capture_output=True,
    45	        text=True,
    46	    ).stdout.strip()
    47	    if not tracked:
    48	        (root / "tool.py").write_text("def run():\n    pass\n", encoding="utf-8")
    49	        (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    50	        (root / "scripts").mkdir(parents=True, exist_ok=True)
    51	        (root / "scripts" / "verify.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    52	        (root / ".gitignore").write_text("build/\n", encoding="utf-8")
    53	        git_cmd(root, "add", "tool.py", "README.md", "scripts/verify.sh", ".gitignore")
    54	        git_cmd(root, "commit", "-m", "initial commit", "-q")
    55	
    56	    epic_dir = root / ".devtool" / "epic" / "demo_epic"
    57	    features_dir = root / ".devtool" / "features"
    58	    epic_dir.mkdir(parents=True, exist_ok=True)
    59	    features_dir.mkdir(parents=True, exist_ok=True)
    60	
    61	    # 1. Spec pair
    62	    spec_en = """# Demo Epic Design
    63	
    64	## Table of Contents
    65	
    66	- [Meta Data](#meta-data)
    67	- [Overview](#overview)
    68	
    69	## Meta Data
    70	
    71	- **Status**: Approved (Gate 1)
    72	
    73	## Overview
    74	
    75	Approved spec overview text.
    76	"""
    77	    spec_vi = """# Demo Epic Design
    78	
    79	## Table of Contents
    80	
    81	- [Meta Data](#meta-data)
    82	- [Overview](#overview)
    83	
    84	## Meta Data
    85	
    86	- **Status**: Approved (Gate 1)
    87	
    88	## Overview
    89	
    90	Nội dung tổng quan thiết kế đã được phê duyệt.
    91	"""
    92	    (epic_dir / "2026-10-22-demo-epic-design.en.md").write_text(spec_en, encoding="utf-8")
    93	    (epic_dir / "2026-10-22-demo-epic-design.vi.md").write_text(spec_vi, encoding="utf-8")
    94	
    95	    # 2. HLD pair
    96	    hld_en = """# Demo Epic High-Level Design
    97	
    98	## Table of Contents
    99	
   100	- [Meta Data](#meta-data)
   101	- [Integration Test Plan](#integration-test-plan)
   102	- [Verification Environment](#verification-environment)
   103	- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)
   104	
   105	## Meta Data
   106	
   107	- **Epic name**: demo_epic
   108	- **Status**: Planned
   109	
   110	## Integration Test Plan
   111	
   112	Protected paths: scripts/verify.sh
   113	
   114	Integration test roots: tests/
   115	
   116	Integration results: python3 tool.py int -> build/test-results/int.xml
   117	
   118	## Verification Environment
   119	
   120	Tests run in temporary directories.
   121	
   122	## Kanban Tasks Breakdown
   123	
   124	1. [Task 1](task_1.md)
   125	2. [Task 2](task_2.md)
   126	"""
   127	    hld_vi = """# Demo Epic High-Level Design
   128	
   129	## Table of Contents
   130	
   131	- [Meta Data](#meta-data)
   132	- [Integration Test Plan](#integration-test-plan)
   133	- [Verification Environment](#verification-environment)
   134	- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)
   135	
   136	## Meta Data
   137	
   138	- **Epic name**: demo_epic
   139	- **Status**: Planned
   140	
   141	## Integration Test Plan
   142	
   143	Protected paths: scripts/verify.sh
   144	
   145	Integration test roots: tests/
   146	
   147	Integration results: python3 tool.py int -> build/test-results/int.xml
   148	
   149	## Verification Environment
   150	
   151	Các bài kiểm tra chạy trong thư mục tạm.
   152	
   153	## Kanban Tasks Breakdown
   154	
   155	1. [Task 1](task_1.md)
   156	2. [Task 2](task_2.md)
   157	"""
   158	    (epic_dir / "demo_epic.en.md").write_text(hld_en, encoding="utf-8")
   159	    (epic_dir / "demo_epic.vi.md").write_text(hld_vi, encoding="utf-8")
   160	
   161	    # 3. BDD Scenarios pair
   162	    bdd_en = """# Demo Epic BDD Scenarios
   163	
   164	## Table of Contents
   165	
   166	- [Coverage Matrix](#coverage-matrix)
   167	- [Scenarios](#scenarios)
   168	
   169	## Coverage Matrix
   170	
   171	| Scenario ID | Dimension | Target Component | Description |
   172	|---|---|---|---|
   173	| `[DEMO-HP-01]` | Happy Path | `tool.py` | Unit scenario description |
   174	| `[DEMO-HP-02]` | Happy Path | `tool.py` | Integration scenario description |
   175	
   176	## Scenarios
   177	
   178	### DEMO-HP-01: Unit scenario description
   179	
   180	```gherkin
   181	Scenario: [DEMO-HP-01] [Tier A - Unit] Unit scenario description
   182	  Given something
   183	  When something happens
   184	  Then it passes
   185	```
   186	
   187	### DEMO-HP-02: Integration scenario description
   188	
   189	```gherkin
   190	Scenario: [DEMO-HP-02] [Tier C - Integration] Integration scenario description
   191	  Given something
   192	  When integration happens
   193	  Then it passes
   194	```
   195	"""
   196	    bdd_vi = """# Demo Epic BDD Scenarios
   197	
   198	## Table of Contents
   199	
   200	- [Coverage Matrix](#coverage-matrix)
   201	- [Scenarios](#scenarios)
   202	
   203	## Coverage Matrix
   204	
   205	| Scenario ID | Dimension | Target Component | Description |
   206	|---|---|---|---|
   207	| `[DEMO-HP-01]` | Happy Path | `tool.py` | Unit scenario description |
   208	| `[DEMO-HP-02]` | Happy Path | `tool.py` | Integration scenario description |
   209	
   210	## Scenarios
   211	
   212	### DEMO-HP-01: Unit scenario description
   213	
   214	```gherkin
   215	Scenario: [DEMO-HP-01] [Tier A - Unit] Unit scenario description
   216	  Given something
   217	  When something happens
   218	  Then it passes
   219	```
   220	
   221	### DEMO-HP-02: Integration scenario description
   222	
   223	```gherkin
   224	Scenario: [DEMO-HP-02] [Tier C - Integration] Integration scenario description
   225	  Given something
   226	  When integration happens
   227	  Then it passes
   228	```
   229	"""
   230	    (epic_dir / "bdd_scenarios.en.md").write_text(bdd_en, encoding="utf-8")
   231	    (epic_dir / "bdd_scenarios.vi.md").write_text(bdd_vi, encoding="utf-8")
   232	
   233	    # 4. Tasks
   234	    task_1_epic = """---
   235	id: "task_1"
   236	status: "todo"
   237	priority: "high"
   238	assignee: null
   239	epic: "demo-epic"
   240	dueDate: null
   241	created: "2026-10-22T09:10:00Z"
   242	modified: "2026-10-22T09:10:00Z"
   243	completedAt: null
   244	labels: ["demo"]
   245	order: "a1"
   246	---
   247	
   248	# Task 1: First Task
   249	
   250	Epic: [demo_epic](demo_epic.en.md)
   251	
   252	Covers: DEMO-HP-01
   253	
   254	## Requirement Analysis
   255	
   256	Requirement text for task 1.
   257	
   258	## Files
   259	
   260	Allowed files:
   261	- `tool.py`
   262	
   263	Read-only context:
   264	- `README.md` — context note
   265	
   266	## Design Rationale
   267	
   268	Design rationale for task 1.
   269	
   270	## Impact Analysis & Blast Radius
   271	
   272	- **Target Files & Symbols**:
   273	  - `tool.py`: `run`
   274	
   275	### BDD SCENARIOS
   276	
   277	Covers: DEMO-HP-01
   278	
   279	```gherkin
   280	Scenario: [DEMO-HP-01] [Tier A - Unit] Unit scenario description
   281	  Given something
   282	  When something happens
   283	  Then it passes
   284	```
   285	
   286	## Verification
   287	
   288	| ID | Phase | Command | Expect | Needs |
   289	|----|-------|---------|--------|-------|
   290	| V1 | RED | `python3 tool.py red` | exit 1 | — |
   291	| V2 | GREEN | `python3 tool.py green` | exit 0 | — |
   292	| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |
   293	| V4 | TIER-B | `mypy tool.py` | exit 0 | — |
   294	| V5 | TIER-C | `python3 tool.py int` | exit 0; results build/test-results/int.xml | — |
   295	
   296	## Stop and Report If
   297	
   298	- A command fails unexpectedly.
   299	
   300	## Decisions Already Made
   301	
   302	- Real grounded decision for tool.py.
   303	
   304	## Definition of Done
   305	
   306	- All checks pass (V2, V3, V4, V5).
   307	"""
   308	
   309	    task_2_epic = """---
   310	id: "task_2"
   311	status: "todo"
   312	priority: "high"
   313	assignee: null
   314	epic: "demo-epic"
   315	dueDate: null
   316	created: "2026-10-22T09:10:00Z"
   317	modified: "2026-10-22T09:10:00Z"
   318	completedAt: null
   319	labels: ["demo"]
   320	order: "a2"
   321	---
   322	
   323	# Task 2: Second Task
   324	
   325	Epic: [demo_epic](demo_epic.en.md)
   326	
   327	Covers: DEMO-HP-02
   328	
   329	## Requirement Analysis
   330	
   331	Requirement text for task 2.
   332	
   333	## Files
   334	
   335	Allowed files:
   336	- `tool.py`
   337	
   338	Read-only context:
   339	- `README.md` — context note
   340	
   341	## Design Rationale
   342	
   343	Design rationale for task 2.
   344	
   345	## Impact Analysis & Blast Radius
   346	
   347	- **Target Files & Symbols**:
   348	  - `tool.py`: `run`
   349	
   350	### BDD SCENARIOS
   351	
   352	Covers: DEMO-HP-02
   353	
   354	```gherkin
   355	Scenario: [DEMO-HP-02] [Tier C - Integration] Integration scenario description
   356	  Given something
   357	  When integration happens
   358	  Then it passes
   359	```
   360	
   361	## Verification
   362	
   363	| ID | Phase | Command | Expect | Needs |
   364	|----|-------|---------|--------|-------|
   365	| V1 | RED | `python3 tool.py red2` | exit 1 | — |
   366	| V2 | GREEN | `python3 tool.py green2` | exit 0 | — |
   367	| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |
   368	| V4 | TIER-B | `mypy tool.py` | exit 0 | — |
   369	| V5 | TIER-C | `python3 tool.py int` | exit 0; results build/test-results/int.xml | — |
   370	
   371	## Stop and Report If
   372	
   373	- A command fails unexpectedly.
   374	
   375	## Decisions Already Made
   376	
   377	- Real grounded decision for tool.py.
   378	
   379	## Definition of Done
   380	
   381	- All checks pass (V2, V3, V4, V5).
   382	"""
   383	
   384	    (epic_dir / "task_1.md").write_text(task_1_epic, encoding="utf-8")
   385	    (epic_dir / "task_2.md").write_text(task_2_epic, encoding="utf-8")
   386	
   387	    # 5. Mirrors in .devtool/features/
   388	    task_1_feature = task_1_epic.replace("](demo_epic.en.md)", "](../epic/demo_epic/demo_epic.en.md)")
   389	    task_2_feature = task_2_epic.replace("](demo_epic.en.md)", "](../epic/demo_epic/demo_epic.en.md)")
   390	    (features_dir / "task_1.md").write_text(task_1_feature, encoding="utf-8")
   391	    (features_dir / "task_2.md").write_text(task_2_feature, encoding="utf-8")
   392	
   393	
   394	class ReadinessCoreTest(unittest.TestCase):
   395	    def setUp(self) -> None:
   396	        self.temp_dir = tempfile.TemporaryDirectory()
   397	        self.addCleanup(self.temp_dir.cleanup)
   398	        self.root = Path(self.temp_dir.name).resolve()
   399	
   400	        git_cmd(self.root, "init", "-q")
   401	        git_cmd(self.root, "config", "user.email", "tester@example.com")
   402	        git_cmd(self.root, "config", "user.name", "Tester")
   403	
   404	        build_ready_epic(self.root)
   405	
   406	    def run_check(self, *args: str, cwd: Path | None = None) -> tuple[int, str, str]:
   407	        run_cwd = cwd or self.root
   408	        proc = subprocess.run(
   409	            [sys.executable, str(SCRIPT_PATH), *args],
   410	            check=False,
   411	            cwd=run_cwd,
   412	            capture_output=True,
   413	            text=True,
   414	        )
   415	        return proc.returncode, proc.stdout, proc.stderr
   416	
   417	    def test_prv_hp_01_ready_fixture_epic_passes_every_check(self) -> None:
   418	        """PRV-HP-01: A ready fixture epic passes every check."""
   419	        code, stdout, stderr = self.run_check("demo_epic")
   420	        self.assertEqual(code, 0, f"Expected 0, got {code}.\nStdout:\n{stdout}\nStderr:\n{stderr}")

exec
/bin/zsh -lc "rg -n 'bdd_scenarios\\.vi|\\.vi\\.md|require-bilingual|bilingual' skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/task_contract.py skills/doc_quality_check/resources/scripts/check_document.py | head -n 220" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
skills/doc_quality_check/resources/scripts/check_document.py:10:  check_document.py --require-bilingual FILE ... require matching .en.md/.vi.md files
skills/doc_quality_check/resources/scripts/check_document.py:13:--require-toc and --require-bilingual apply to lifecycle deliverables. They are opt-in because
skills/doc_quality_check/resources/scripts/check_document.py:188:            counterpart = path.with_name(name[:-6] + ".vi.md")
skills/doc_quality_check/resources/scripts/check_document.py:189:        elif name.endswith(".vi.md"):
skills/doc_quality_check/resources/scripts/check_document.py:193:                             "lifecycle document must use an .en.md or .vi.md language suffix"))
skills/doc_quality_check/resources/scripts/check_document.py:233:    ap.add_argument("--require-bilingual", action="store_true",
skills/doc_quality_check/resources/scripts/check_document.py:234:                    help="require matching .en.md and .vi.md lifecycle documents")
skills/doc_quality_check/resources/scripts/check_document.py:256:    if args.require_bilingual:

exec
/bin/zsh -lc "nl -ba skills/doc_quality_check/resources/scripts/check_document.py | sed -n '175,205p'; nl -ba skills/doc_quality_check/resources/scripts/check_document.py | sed -n '245,270p'; rg -n 'bdd_scenarios|require.*vi|hld.*vi' skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/task_contract.py" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
   175	            if heading_anchor not in linked_anchors:
   176	                findings.append((path, 0,
   177	                                 f"table of contents does not link section: {heading}"))
   178	    return findings
   179	
   180	
   181	def check_language_pairs(paths: list[pathlib.Path]) -> list:
   182	    """Require every lifecycle document to have matching English and Vietnamese files."""
   183	    findings = []
   184	    normalized = {path.resolve() for path in paths}
   185	    for path in paths:
   186	        name = path.name
   187	        if name.endswith(".en.md"):
   188	            counterpart = path.with_name(name[:-6] + ".vi.md")
   189	        elif name.endswith(".vi.md"):
   190	            counterpart = path.with_name(name[:-6] + ".en.md")
   191	        else:
   192	            findings.append((path, 0,
   193	                             "lifecycle document must use an .en.md or .vi.md language suffix"))
   194	            continue
   195	        if counterpart.resolve() not in normalized:
   196	            state = "missing" if not counterpart.exists() else "not included in this check"
   197	            findings.append((path, 0, f"language counterpart {state}: {counterpart.name}"))
   198	            continue
   199	        if name.endswith(".en.md"):
   200	            english_structure = heading_structure(path)
   201	            vietnamese_structure = heading_structure(counterpart)
   202	            if english_structure != vietnamese_structure:
   203	                findings.append((path, 0,
   204	                                 "English/Vietnamese heading structure differs: "
   205	                                 f"{english_structure} != {vietnamese_structure}"))
   245	        print(f"  ok   refusal rule: none of {len(args.changed_files)} changed files ship in the build")
   246	        return 0
   247	
   248	    if not args.files:
   249	        print("  FAIL no files given — check the invocation, not the content")
   250	        return 1
   251	
   252	    findings = []
   253	    paths = [pathlib.Path(f) for f in args.files]
   254	    for path in paths:
   255	        findings += check_file(path, require_toc=args.require_toc)
   256	    if args.require_bilingual:
   257	        findings += check_language_pairs(paths)
   258	    for path, line, msg in findings:
   259	        where = f"{path}:{line}" if line else str(path)
   260	        print(f"  FAIL {where} — {msg}")
   261	    print(f"  checked {len(args.files)} documents, {len(findings)} findings")
   262	    return 1 if findings else 0
   263	
   264	
   265	if __name__ == "__main__":
   266	    sys.exit(main())
skills/dev-implementation/resources/scripts/task_contract.py:330:                      epic_dir / "bdd_scenarios.en.md", epic_dir / "evidence" / f"{path.stem}.json")
skills/dev-implementation/resources/scripts/check_task_contract.py:332:    for bdd_path in sorted(hld_path.parent.glob("bdd_scenarios*.md")):

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/SKILL.md | sed -n '35,145p'; nl -ba skills/dev-lifecycle/SKILL.md | sed -n '80,135p'; nl -ba docs/lifecycles.en.md | sed -n '35,95p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
    35	## Process
    36	
    37	This skill is **Stage 3** of the Epic Lifecycle. The surrounding stages, the five approval gates, and what each stage hands over are owned by the [`dev-lifecycle`](../dev-lifecycle/SKILL.md) skill (with diagrams preserved in `docs/lifecycles.en.md`). Gate 3 (execution order confirmed) is enforced below, in Phase 1.
    38	
    39	### Phase 0 — Context Reload & Platform Detection (once, not per task)
    40	
    41	0. **Resolve the epic.** This skill takes one epic name, in either form:
    42	   - If `.devtool/epic/<name>/` exists, `<epic_dir>` is `<name>`, and `<epic_slug>` is the `epic:` value of its task mirrors: `grep -h -m1 '^epic:' .devtool/epic/<name>/task_*.md`.
    43	   - Otherwise `<name>` is a slug, and `<epic_dir>` is the directory holding the files `grep -l -F 'epic: "<name>"' .devtool/epic/*/task_*.md` lists.
    44	   - With no name, or no match, list the epic directories whose overview Status is not `Done` and ask which one. Never guess, even when only one is listed.
    45	1. Read, in full:
    46	   - `.devtool/epic/<epic_dir>/<epic_dir>.en.md` (the canonical HLD — never `.vi.md` for decisions, that's a synced translation).
    47	   - `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` (the canonical behavioral contract across the 5 dimensions, if present; `.vi.md` is its synchronized translation).
    48	   - Every `.devtool/features/task_*.md` whose frontmatter `epic:` matches `<epic_slug>`.
    49	   - Any spec file(s) linked from the HLD's Meta Data section.
    50	   - `.devtool/epic/<epic_dir>/handoff.md`, when present — the packaging record. Use its Open Notes as context; it is never updated after packaging.
    51	
    52	#### Bounded Context Injection & Spec Fidelity
    53	
    54	Before implementing any task, the executor MUST adhere strictly to the 3-step Bounded Context Injection protocol:
    55	1. Read the active task file (`.devtool/features/task_*.md`).
    56	2. Read the Allowed files and Read-only context listed in the task file.
    57	3. Look up exact symbols and architectural choices declared in `Decisions Already Made`; do not perform undirected whole-repository searches.
    58	
    59	**Strict Spec Fidelity**: Implement strictly within the boundaries specified by the active task and its Allowed files. Do not add speculative abstractions, configurability, or adjacent refactoring not requested by the task specification.
    60	
    61	2. Resolve the three paths the rest of this skill uses. `SKILL_DIR` is the directory this `SKILL.md` was loaded from:
    62	   ```bash
    63	   SKILL_DIR=<absolute path of the directory containing this SKILL.md>
    64	   REPO_ROOT=$(git rev-parse --show-toplevel)
    65	   INTEGRATE="$SKILL_DIR/../finishing-a-development-branch/resources/scripts/integrate_branch.py"
    66	   ```
    67	3. Detect the platform:
    68	   ```bash
    69	   PROJECT_TYPE=$("$SKILL_DIR"/resources/scripts/detect_project_type.sh "$REPO_ROOT")
    70	   echo "Detected project type: $PROJECT_TYPE"
    71	   ```
    72	   Supported platforms: `flutter`, `android`, `ios`, `web`, `python`, `rust`.
    73	4. Run **Entry-Point Detection** before Phase 1. It decides whether Phase 1 starts fresh or the Resume Procedure takes over.
    74	
    75	#### Entry-Point Detection
    76	
    77	Read these signals, all read-only, from the main checkout:
    78	
    79	```bash
    80	test -f .devtool/epic/<epic_dir>/handoff.md && echo packaged-handoff
    81	test -f .devtool/epic/<epic_dir>/principal_review.md && python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --kind principal --epic-dir <epic_dir>
    82	grep -m1 -E '^- \*\*Status\*\*:' .devtool/epic/<epic_dir>/<epic_dir>.en.md
    83	git rev-parse --verify --quiet refs/heads/epic/<epic_slug>
    84	for remote in $(git remote); do git ls-remote --heads "$remote" "epic/<epic_slug>"; done
    85	git worktree list --porcelain | grep -E '^worktree .*/\.worktrees/<epic_dir>$'
    86	python3 "$SKILL_DIR"/resources/scripts/compute_execution_order.py <epic_slug> \
    87	  --features-dir .devtool/epic/<epic_dir>
    88	```
    89	
    90	`git ls-remote` asks each remote directly, so an epic branch pushed from another clone shows before any fetch; if a remote cannot be reached, fall back to `git branch -r --list '*/epic/<epic_slug>'`. The last command reads the epic's task mirrors (`sync_task_status.py` keeps them in step with `.devtool/features/` and `.devtool/features/done/`); its flattened order prints each task's status as `[priority, status]`. Evaluate the rows top-down — first match wins — and announce it: "Entry point: row N — <state>."
    91	
    92	| # | Signals | State | Entry point |
    93	|---|---------|-------|-------------|
    94	| 1 | Overview Status is `Done` | Finished, or Stage 4 interrupted | With no epic branch left, report finished and stop. With epic branch still present, Stage 4 was interrupted or its PR is still open: report and ask |
    95	| 2 | No epic branch, and any task is `backlog` | Queued behind another epic | Stop. Flipping `backlog` to `todo` is developer's call |
    96	| 3 | No epic branch locally or on remote, no worktree, every task `todo` | Not started — packaged if `handoff.md` exists | Phase 1 as written: Gate 3, then new worktree |
    97	| 4 | Epic branch exists, no worktree, some task not `done` | Interrupted, worktree removed | Resume Procedure |
    98	| 5 | Worktree exists, some task not `done` | Interrupted midway through Stage 3 | Resume Procedure |
    99	| 6 | Epic branch exists, every task `done` | Tasks finished | Recreate worktree if missing (`git worktree add .worktrees/<epic_dir> epic/<epic_slug>`, no `-b`) and bootstrap (Phase 1 step 5), run Resume Procedure preflight (step 2), then Phase 4 in full; its PASS presents Review Choice |
   100	| 7 | Anything else — branch only on remote, or tasks `in-progress` or `done` with no epic branch | Inconsistent | Stop, report signals, ask |
   101	
   102	#### Resume Procedure
   103	
   104	For rows 4 and 5. Phase 1 step 4's `git worktree add -b` never runs here.
   105	
   106	1. Row 4 only: recreate worktree from existing branch, `git worktree add .worktrees/<epic_dir> epic/<epic_slug>` with no `-b`. For rows 4 and 5, check bootstrap with Phase 1 step 5's platform checks and re-run if needed.
   107	2. In the worktree, run `python3 "$INTEGRATE" preflight --base develop`. A rebase in progress, or diverged base, is handled per Phase 2 step 7 before anything else.
   108	3. Find the interrupted task: one at `in-progress` or `review`. If worktree has uncommitted changes, collect `git status --short`.
   109	4. **Gate 3 (resume).** Check mirror scan summary against task mirror count and read Manual review advised section. State the Principal Review status (`not run`, `round <n>: PASS`, or `round <n>: decided`), and stop with the triage if that check exits 1. Run Phase 1 step 3's BDD mapping check and task contract check, including retrofit if needed. Commit any retrofit on epic branch staging only touched files (both `bdd_scenarios`, both HLD variants, task files — never `git add -A`). The interrupted task's own status fields may ride along in that commit; that is expected. Present tasks already `done` with commits (`git log --oneline develop..epic/<epic_slug>`), remaining order with `done` tasks removed, choice on uncommitted changes (keep or discard), and request permission to fast-forward `develop`. Wait for confirmation.
   110	5. If overview Status begins with `Packaged`, run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`.
   111	6. Enter Phase 2 at the interrupted task — a task at `review` re-enters at Phase 2 step 2; a task at `in-progress` resumes implementation with kept changes — or at the first remaining task.
   112	
   113	### Phase 1 — Execution Plan
   114	
   115	1. Run:
   116	   ```bash
   117	   python3 "$SKILL_DIR"/resources/scripts/compute_execution_order.py <epic_slug>
   118	   ```
   119	   Check scan summary line (`Scanned N task_*.md files; M matched epic ...`). If `M` is smaller than expected, fix broken frontmatter before proceeding.
   120	2. Read "Manual review advised" section (if any) and cross-check against Phase 0 context. Adjust flattened order by hand if a prose note should win.
   121	3. **Checkpoint (Gate 3):** present the final order to user and get confirmation before touching git.
   122	   In the same message, state the Principal Review status (`not run`, `round <n>: PASS`, or `round <n>: decided`; stop with the triage if that check exits 1), and ask once for permission to fast-forward local `develop` from its upstream for the rest of this epic (Phase 1 step 4 and Phase 2 step 7).
   123	
   124	   Before presenting order, run BDD traceability plan check:
   125	   ```bash
   126	   python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py plan \
   127	     --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md \
   128	     --tasks .devtool/epic/<epic_dir>/task_*.md
   129	   ```
   130	   If needed, add bracketed identifiers to `bdd_scenarios.*.md`, `Covers:` lines to task files, and `Integration test roots:` to HLD. Commit as `[EPIC_NAME] Add BDD scenario identifiers`.
   131	
   132	   Then check task contract:
   133	   ```bash
   134	   python3 "$SKILL_DIR"/resources/scripts/check_task_contract.py \
   135	     --hld .devtool/epic/<epic_dir>/<epic_dir>.en.md \
   136	     --tasks .devtool/epic/<epic_dir>/task_*.md
   137	   ```
   138	   Do not create worktree until both checks exit 0 and developer has confirmed the order.
   139	
   140	#### Phase 1 (continued) — Worktree Bootstrap, once the order is confirmed
   141	
   142	4. Bring local `develop` up to date with upstream, then create one worktree for whole epic (`d3nexus:using-git-worktrees`):
   143	   ```bash
   144	   python3 "$INTEGRATE" sync-base --base develop
   145	   git worktree add .worktrees/<epic_dir> -b epic/<epic_slug> develop
    80	  - **Epic-scale code** → `dev-designer` (Stage 2). Relocate spec variants to `.devtool/epic/<epic_dir>/`, update links, and enter Stage 2 with the canonical `.en.md` path.
    81	  - **Everything else** → `writing-plans`. This leaves the epic lifecycle; remaining gates do not apply.
    82	If dev-brainstorming decomposed the request into several sub-project specs, **route each one independently**. Never merge multiple specs into one epic.
    83	
    84	### Stage 2 — Architecture & Tasks → `dev-designer`
    85	
    86	**Invoke `d3nexus:dev-designer`.**
    87	- **Entry:** Gate 1 spec in `.devtool/epic/<epic_dir>/`.
    88	- **Exit (Gate 2):** user has confirmed the proposed task list and granularity.
    89	Treat the approved spec as the source of truth for scope and decisions already made.
    90	
    91	### Handoff Choice
    92	
    93	Between Gate 2 and Stage 3 the developer decides when, and by whom, the epic is implemented:
    94	
    95	> Gate 2 passed: the HLD, BDD scenarios and N task files for `<epic_slug>` are written. How do you want to proceed?
    96	>
    97	> 1. **Package** — write `handoff.md`, mark the epic `Packaged`, and stop.
    98	> 2. **Continue** — enter Stage 3 now (`dev-implementation`, starting with Gate 3: execution order).
    99	
   100	**Continue** → invoke `dev-implementation`.
   101	**Package** → run packaging procedure:
   102	1. **Preflight, read-only.** Must exit 0: `python3 "$SCRIPTS"/check_epic_readiness.py <epic_dir>` (runs `check_task_contract.py --design`). Its first line gives the task count.
   103	2. Copy `references/handoff-template.md` to `.devtool/epic/<epic_dir>/handoff.md` and fill every placeholder; `<N>` is the task count the preflight printed. Add conversation decisions and risks into Open Notes.
   104	3. Lint it: `python3 "$CHECK_DOC" --require-toc .devtool/epic/<epic_dir>/handoff.md`.
   105	4. Mark the epic packaged, then confirm both overview variants changed:
   106	   ```bash
   107	   python3 "$SCRIPTS"/sync_task_status.py epic <epic_dir> Packaged
   108	   grep -n -E '^- \*\*(Status|Trạng thái)\*\*: Packaged' \
   109	     .devtool/epic/<epic_dir>/<epic_dir>.en.md .devtool/epic/<epic_dir>/<epic_dir>.vi.md
   110	   ```
   111	   Two matching lines are required; with fewer, set the Status line by hand in both variants. If the Status read `Queued (backlog) — behind <epic>` before packaging, run the script with `"Packaged (queued behind <epic>)"` instead and copy that line into Open Notes; the `grep` still matches.
   112	5. Commit if `auto_commit: true`: `git commit -m "[<EPIC_NAME>] Package epic for handoff"`.
   113	6. Offer to push only with explicit permission.
   114	7. Print `handoff.md` path and rendered Resume Prompt.
   115	8. Present **Principal Review Choice** — follow [references/principal-review.md](references/principal-review.md).
   116	
   117	### Stage 3 — Isolated Execution → `dev-implementation`
   118	
   119	**Entry:** Gate 2 passed, HLD and `task_*.md` exist, and Continue chosen (or resuming packaged/interrupted epic).
   120	**Exit (Gate 5):** Gate 4 is 🟢 LGTM and user approves Kanban completion.
   121	
   122	- **Gate 3 (Execution Order)**: Present computed execution order and get user confirmation **before** creating worktrees or dispatching subagents.
   123	- **Execution**: One worktree, one task at a time, one commit per task, docs kept truthful. Rebase and integrate with `develop` after each task.
   124	
   125	**Review Choice loop**:
   126	After all tasks are complete, run Gate 4. On every PASS, present Review Choice:
   127	- **Option 1: Finish** -> Proceed to Gate 5 (Developer Kanban Review), then Stage 4.
   128	- **Option 2: Cross-model review** -> Invoke `run_external_review.py run` (prompting for Claude CLI or Codex CLI). Record round in `.devtool/epic/<epic_dir>/review_results.md`. Check unresolved findings with `run_external_review.py check --epic-dir <epic_dir>`. Any dismissed finding requires explicit developer instruction. Return to a full Gate 4 run on the new commit.
   129	- **Option 3: Local model review** -> Run `ollama list`, ask which model, then invoke `run_external_review.py run --cli ollama --model <model>`. A model served by the local Ollama reviews each task commit, then the epic, and one round is recorded in the same `review_results.md` under the same `check` rules. Return to a full Gate 4 run on the new commit.
   130	
   131	Every review round, option 2 or 3, is triaged before anyone acts on it: present `run_external_review.py triage --epic-dir <epic_dir>` filled as dev-implementation's `references/review-triage.md` says, and wait for the developer's decision on each finding.
   132	
   133	When an epic's tasks were executed by a fast executor model (e.g. Gemini Flash, Claude Haiku, GPT-4o-mini), the agent presents a strong recommendation in the Review Choice prompt:
   134	*"Tasks were executed by a fast executor model. Option 2: Cross-model review (Claude CLI or Codex CLI) is STRONGLY RECOMMENDED to audit test integrity and subtle regressions before finishing the branch."* Local model review does not replace it.
   135	
    35	It owns sequence and gates only; each stage's method lives in that stage's own skill.
    36	
    37	**What it produces.** A merged branch, plus a High-Level Design in English and Vietnamese,
    38	a Gherkin BDD suite, and one task file per unit of work
    39	— all archived into `.devtool/epic/<slug>/` when the epic closes.
    40	
    41	**When it does not apply.** A single component that one implementation plan covers.
    42	That work uses `dev-brainstorming` then `writing-plans`, which leaves this lifecycle and its remaining gates behind.
    43	
    44	```mermaid
    45	flowchart TD
    46	    S1["Stage 1 — Inception &amp; Spec<br/>(dev-brainstorming)"]
    47	    G1{"Gate 1<br/>Spec approved?"}
    48	    ROUTE{"Epic-scale?"}
    49	    PLANS(["writing-plans<br/>(leaves this workflow)"])
    50	    S2["Stage 2 — Architecture &amp; Tasks<br/>(dev-designer)"]
    51	    G2{"Gate 2<br/>HLD &amp; task breakdown approved?"}
    52	    HC{"Handoff choice<br/>package or continue?"}
    53	    PKG["Package epic<br/>handoff.md, status Packaged"]
    54	    PRC{"Principal Review Choice<br/>Done or Principal Review?"}
    55	    PR["run_external_review.py run --kind principal<br/>triage, decisions, revision"]
    56	    PKGSTOP(["Stop: handoff.md and Resume Prompt"])
    57	    S3["Stage 3 — Isolated Execution<br/>(dev-implementation)"]
    58	    G3{"Gate 3<br/>Execution order confirmed?"}
    59	    EXEC["Phase 2-3: task-by-task TDD<br/>one commit per task, doc sync on divergence,<br/>integrate with develop after each task"]
    60	    RC{"Review Choice<br/>Finish, Cross-model review or Local model review?"}
    61	    XR["run_external_review.py run<br/>(review_results.md committed per round)"]
    62	    LR["run_external_review.py run --cli ollama<br/>(review_results.md committed per round)"]
    63	    G4{"Gate 4<br/>audit + result-based traceability + quality_check 🟢 LGTM?"}
    64	    REVIEW["Phase 4.1: Developer Kanban Review<br/>(All tasks held in DONE column for visual inspection)"]
    65	    G5{"Gate 5<br/>User sign-off &amp; finish approved?"}
    66	    S4["Stage 4 — Finish Branch &amp; Archival<br/>(finishing-a-development-branch)"]
    67	
    68	    S1 --> G1
    69	    G1 -->|no, revise| S1
    70	    G1 -->|yes| ROUTE
    71	    ROUTE -->|no| PLANS
    72	    ROUTE -->|yes| S2
    73	    S2 --> G2
    74	    G2 -->|no, adjust breakdown| S2
    75	    G2 -->|yes| HC
    76	    HC -->|"1. package"| PKG
    77	    HC -->|"2. continue"| S3
    78	    PKG --> PRC
    79	    PRC -->|"1. Done"| PKGSTOP
    80	    PRC -->|"2. Principal Review"| PR
    81	    PR -->|"revised and re-packaged"| PKG
    82	    PKGSTOP -.->|"later session or another LLM"| S3
    83	    S3 --> G3
    84	    G3 -->|no, reorder| G3
    85	    G3 -->|yes| EXEC
    86	    EXEC --> G4
    87	    G4 -->|"no, fix findings as Fix commits"| EXEC
    88	    G4 -->|"yes"| RC
    89	    RC -->|"1. Finish"| REVIEW
    90	    RC -->|"2. Cross-model review"| XR
    91	    XR -->|"round recorded"| G4
    92	    RC -->|"3. Local model review"| LR
    93	    LR -->|"round recorded"| G4
    94	    REVIEW --> G5
    95	    G5 -->|"no, changes as Fix commits"| EXEC

exec
/bin/zsh -lc "rg -n -i 'strongest|reasoning model|fast model|Author' skills/dev-lifecycle/references/principal-review.md skills/dev-implementation/references/principal-review-prompt.md .devtool/epic/principal_review/{2026-10-22-principal-review-design.en.md,principal_review.en.md,task_5_principal_review_choice_and_acceptance.md}" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
.devtool/epic/principal_review/task_5_principal_review_choice_and_acceptance.md:145:    - the D2 recommendation including the words `strongly recommended`, judged from the HLD's `Author` line or the developer's word;
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:75:| D2 | When the epic was designed by a different or fast model (for example an Antigravity session or a Flash-class model), judged from the HLD's `Author` line or the developer's word, the choice carries a strong recommendation for Principal Review | Mirrors the existing fast-executor recommendation in Review Choice; both reviewed epics came from Antigravity |
.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md:151:- `--model` is passed through. `principal-review.md` recommends the strongest reasoning model each CLI offers.
skills/dev-lifecycle/references/principal-review.md:14:   - When the epic design was authored by a fast model or when the developer requests review, cross-model review is strongly recommended before committing to implementation.

codex
The supplied test and audit evidence is internally consistent and task-scoped, but code inspection has exposed two fail-open readiness paths and two workflow-contract mismatches that the happy-path suites do not exercise. I’m cross-checking each against the approved spec/HLD and the exact task decisions before assigning severity.
exec
/bin/zsh -lc 'for f in .devtool/epic/principal_review/evidence/task_{2_readiness_grounding_and_baseline,3_principal_review_runner_mode,4_epic_status_sync_scope,5_principal_review_choice_and_acceptance}.json; do echo "===== $f"; jq -r '"'.runs.verify.rows[] | select(.id "'!= "SCOPE") | "'"\\(.id) \\(.phase) exit=\\(.exit) outcome=\\(.outcome)\\n\" + ((.output_tail // []) | join(\"\\n\")) + (if .results then \"\\nresults=\" + (.results.digest.totals|tostring) else \"\" end)' \""'$f"; done' in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
===== .devtool/epic/principal_review/evidence/task_2_readiness_grounding_and_baseline.json
V2 GREEN exit=0 outcome=PASS
.........
----------------------------------------------------------------------
Ran 9 tests in 9.418s

OK
V3 TIER-B exit=0 outcome=PASS
All checks passed!
V4 TIER-B exit=0 outcome=PASS
Success: no issues found in 2 source files
V5 TIER-C exit=0 outcome=PASS
.........
----------------------------------------------------------------------
Ran 9 tests in 9.153s

OK
results={"passed":9,"failed":0,"skipped":0}
===== .devtool/epic/principal_review/evidence/task_3_principal_review_runner_mode.json
V2 GREEN exit=0 outcome=PASS
......................................
----------------------------------------------------------------------
Ran 38 tests in 23.051s

OK
V3 GREEN exit=0 outcome=PASS
........................................
----------------------------------------------------------------------
Ran 40 tests in 30.332s

OK
V4 TIER-B exit=0 outcome=PASS
All checks passed!
V5 TIER-B exit=0 outcome=PASS
Success: no issues found in 1 source file
V6 TIER-B exit=0 outcome=PASS
  checked 2 documents, 0 findings
V7 TIER-C exit=0 outcome=PASS
......................................
----------------------------------------------------------------------
Ran 38 tests in 26.683s

OK
........................................
----------------------------------------------------------------------
Ran 40 tests in 30.333s

OK
results={"passed":7,"failed":0,"skipped":0}
===== .devtool/epic/principal_review/evidence/task_4_epic_status_sync_scope.json
V2 GREEN exit=0 outcome=PASS
.............................................................
----------------------------------------------------------------------
Ran 61 tests in 7.309s

OK
V3 GREEN exit=0 outcome=PASS
....
----------------------------------------------------------------------
Ran 4 tests in 0.584s

OK
V4 GREEN exit=0 outcome=PASS
.
----------------------------------------------------------------------
Ran 1 test in 1.068s

OK
V5 TIER-B exit=0 outcome=PASS
All checks passed!
V6 TIER-B exit=0 outcome=PASS
Success: no issues found in 1 source file
V7 TIER-C exit=0 outcome=PASS
.............................................................
----------------------------------------------------------------------
Ran 61 tests in 7.689s

OK
....
----------------------------------------------------------------------
Ran 4 tests in 0.634s

OK
results={"passed":2,"failed":0,"skipped":0}
===== .devtool/epic/principal_review/evidence/task_5_principal_review_choice_and_acceptance.json
V2 GREEN exit=0 outcome=PASS
.................
----------------------------------------------------------------------
Ran 17 tests in 0.004s

OK
V3 GREEN exit=0 outcome=PASS
....
----------------------------------------------------------------------
Ran 4 tests in 0.635s

OK
V4 GREEN exit=0 outcome=PASS
......
----------------------------------------------------------------------
Ran 6 tests in 0.002s

OK
V5 TIER-B exit=0 outcome=PASS
  checked 2 documents, 0 findings
V6 TIER-B exit=0 outcome=PASS
  checked 4 documents, 0 findings
V7 TIER-B exit=0 outcome=PASS
All checks passed!
V8 TIER-B exit=0 outcome=PASS
Success: no issues found in 1 source file
V9 TIER-B exit=0 outcome=PASS
Ran 9 tests in 0.000s

OK
.....
----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
......
----------------------------------------------------------------------
Ran 6 tests in 0.000s

OK
......
----------------------------------------------------------------------
Ran 6 tests in 0.000s

OK
......
----------------------------------------------------------------------
Ran 6 tests in 0.000s

OK
..................
----------------------------------------------------------------------
Ran 18 tests in 0.012s

OK
...............
----------------------------------------------------------------------
Ran 15 tests in 2.455s

OK

PASS — safe to publish
V10 TIER-C exit=0 outcome=PASS
.........
----------------------------------------------------------------------
Ran 9 tests in 9.071s

OK
......................................
----------------------------------------------------------------------
Ran 38 tests in 23.613s

OK
.............................................................
----------------------------------------------------------------------
Ran 61 tests in 8.643s

OK
.................
----------------------------------------------------------------------
Ran 17 tests in 0.004s

OK
....
----------------------------------------------------------------------
Ran 4 tests in 0.712s

OK
......
----------------------------------------------------------------------
Ran 6 tests in 0.001s

OK
results={"passed":22,"failed":0,"skipped":0}

exec
/bin/zsh -lc "sed -n '15,28p' .devtool/epic/principal_review/principal_review.en.md; sed -n '15,28p' .devtool/epic/principal_review/principal_review.vi.md; git merge-base --is-ancestor 34802af c09cb95593c5908098462a0a2963f1a300d9efcb; echo ancestor_exit="'$?; git log -1 --format='"'%H %s' 34802af" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 3412ms:
## Meta Data

- **Epic name**: `principal_review`
- **Status**: In Progress
- **Target release**: Next plugin release
- **Platform**: Python tooling / agent skill kit
- **Source Spec**: [Approved Principal Review design](2026-10-22-principal-review-design.en.md)

## Background

The packaging preflight proves an epic's documents are well formed, not that they are right. A
manual review of a packaged epic in `lyrics-sync` found these, all after the preflight had passed:
- symbols and routes that do not exist;
- a wrong model of a class;
## Siêu dữ liệu

- **Tên epic**: `principal_review`
- **Trạng thái**: In Progress
- **Bản phát hành mục tiêu**: Bản phát hành plugin kế tiếp
- **Nền tảng**: Công cụ Python / bộ kit skill cho agent
- **Spec nguồn**: [Thiết kế Principal Review đã duyệt](2026-10-22-principal-review-design.vi.md)

## Bối cảnh

Preflight đóng gói chứng minh tài liệu của epic đúng định dạng, không chứng minh chúng đúng. Một
đợt review thủ công một epic đã đóng gói trong `lyrics-sync` tìm ra những lỗi sau, tất cả đều xuất
hiện sau khi preflight đã qua:
- symbol và route không tồn tại;
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-xsyjzmb6' (errno=Operation not permitted)
2026-10-23 17:46:56.415 xcodebuild[26797:2222895]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:46:56.589 xcodebuild[26797:2222893] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-Tk7Ptoqv' (errno=Operation not permitted)
2026-10-23 17:46:57.074 xcodebuild[26799:2222907]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:46:57.198 xcodebuild[26799:2222906] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
ancestor_exit=0
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-YkMl0qxk' (errno=Operation not permitted)
2026-10-23 17:46:58.216 xcodebuild[26816:2222986]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:46:58.332 xcodebuild[26816:2222985] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-jVA4a1mG' (errno=Operation not permitted)
2026-10-23 17:46:58.775 xcodebuild[26820:2223010]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-23 17:46:58.892 xcodebuild[26820:2223009] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
34802afa118bdeb42e74f1a880e07c00f3b29023 [PRINCIPAL_REVIEW] Generate epic and task breakdown

exec
/bin/zsh -lc "nl -ba /Users/danhdueexoictif/.codex/memories/rollout_summaries/2026-10-18T10-39-52-b3XU-gate4_review_choice_loop_and_external_review_streaming.md | sed -n '1,75p'; nl -ba /Users/danhdueexoictif/.codex/memories/MEMORY.md | sed -n '160,198p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/principal_review
 succeeded in 0ms:
     1	thread_id: 01a14e98-b2b9-7043-9d17-65dd8df4be46
     2	updated_at: 2026-10-18T15:23:36+00:00
     3	rollout_path: /Users/danhdueexoictif/.codex/sessions/2026/10/18/rollout-2026-10-18T17-39-52-01a14e98-b2b9-7043-9d17-65dd8df4be46.jsonl
     4	cwd: /Users/danhdueexoictif/AllProjects/ai-agent-tools
     5	git_branch: main
     6	
     7	# Review workflow loop and realtime external-review diagnostics implemented
     8	
     9	Rollout context: In `/Users/danhdueexoictif/AllProjects/ai-agent-tools`, the user requested (in Vietnamese) both a workflow change and an enhancement to `run_external_review.py`. The user clarified the desired state machine: `Gate 4 → Review Choice`; **Finish → Gate 5**, while **Cross-model review → record round/findings → rerun full Gate 4 → Review Choice**, repeating until Finish.
    10	
    11	## Task 1: Reposition Review Choice into a Gate 4 loop
    12	
    13	Outcome: success
    14	
    15	Preference signals:
    16	- The user explicitly corrected the initial interpretation: “I. Gate 4 => Review Choice: 1. Finish. 2. Cross model review. II. Sau bước này chạy lại Gate 4. => Loop cho tới khi finish.” Future lifecycle changes should preserve this exact ordering and loop, rather than placing Review Choice before Gate 4.
    17	- The user then requested “Commit and finish all tasks.” This indicates that once verification is complete, they prefer the changes committed locally and the workflow finished without pushing unless explicitly requested.
    18	
    19	Key steps:
    20	- Added the invariant `Gate 4 PASS → Review Choice; Finish → Gate 5; Cross-model review → Gate 4 in full` to `skills/dev-lifecycle/SKILL.md` and `skills/dev-implementation/SKILL.md`.
    21	- Updated `rules/CRITICAL_RULES.md`, English/Vietnamese lifecycle docs, and lifecycle-selection docs so review rounds, decisions, Fix commits, and Gate 5 changes invalidate the prior SHA-bound Gate 4 result.
    22	- Added regression assertions in `scripts/test_verifiable_handoff_text.py` for the new edges and for removal of old “before Gate 4” wording.
    23	- Corrected a documentation lint issue in `rules/CRITICAL_RULES.md` by tagging a fenced block as `text`.
    24	
    25	Reusable knowledge:
    26	- Gate 4 is SHA-bound. Any review round, review decision, Fix commit, or Gate 5-requested change that changes the candidate SHA requires a complete Gate 4 rerun.
    27	- A cross-model CLI failure/timeout or recorded round also returns to full Gate 4 before another Review Choice; it does not jump directly to Gate 5 or another choice.
    28	
    29	Failures and how to do differently:
    30	- The first regression test intentionally failed because the repository still encoded Review Choice before Gate 4. Updating only the flowchart was insufficient; normative rules, both skills, bilingual docs, lifecycle-selection docs, and negative assertions all needed alignment.
    31	
    32	References:
    33	- Commit: `df9f67af7c1f7fecd3b4a9768c0863d035ed3088`
    34	- Commit message: `[REVIEW_WORKFLOW] Loop review choice through Gate 4`
    35	- Core flow edges: `EXEC --> G4`, `G4 -- yes --> RC`, `RC -- Finish --> REVIEW`, `RC -- Cross-model review --> XR`, `XR -- round recorded --> G4`.
    36	
    37	## Task 2: Add realtime ANSI pre-check output to external review
    38	
    39	Outcome: success
    40	
    41	Key steps:
    42	- Enhanced `skills/dev-implementation/resources/scripts/run_external_review.py` with ANSI color helpers, `run_gate()`, flushed progress output, structured `PreconditionFailedError`, and a blocking banner showing the failed gate, reason, last 25 detail lines, and confirmation that the CLI was not invoked.
    43	- Routed audit, integration, and BDD traceability checks through `run_gate()` while preserving their captured output in the facts bundle.
    44	- Added/updated regression tests for PASS, failure, timeout, flushed output, and banner behavior.
    45	
    46	Reusable knowledge:
    47	- The script directly runs `audit_epic.py`, declared Integration commands, and `check_bdd_traceability.py`; `android-ui-audit` is not invoked directly by this script and may only be involved indirectly through the quality provider registry.
    48	
    49	References:
    50	- `run_gate()` streams to `stderr` with `flush=True`.
    51	- Blocking banner includes `[PRECONDITION BLOCKED]` and `<CLI> CLI WAS NOT INVOKED (0 CREDITS USED)`.
    52	- Targeted suite: `31` tests passed; final full verification also passed.
    53	
    54	Final verification:
    55	- `scripts/verify.sh`: `PASS — safe to publish`.
    56	- Worktree clean on `main`; no push performed.
   160	# Task Group: ai-agent-tools Gate 4 Review Choice loop and external-review diagnostics
   161	
   162	scope: Verified lifecycle state-machine update and streamed external-review precondition reporting.
   163	applies_to: cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools; reuse_rule=inspect current lifecycle rules/skills and candidate SHA before reuse; flow is repository policy, not a generic shortcut around gates.
   164	
   165	## Task 1: Reposition Review Choice into a Gate 4 loop, success
   166	
   167	### rollout_summary_files
   168	
   169	- rollout_summaries/2026-10-18T10-39-52-b3XU-gate4_review_choice_loop_and_external_review_streaming.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/18/rollout-2026-10-18T17-39-52-01a14e98-b2b9-7043-9d17-65dd8df4be46.jsonl, updated_at=2026-10-18T15:23:36+00:00, thread_id=01a14e98-b2b9-7043-9d17-65dd8df4be46, committed and fully verified)
   170	
   171	### keywords
   172	
   173	- Gate 4, Review Choice, Cross-model review, Gate 5, SHA-bound, rules/CRITICAL_RULES.md, test_verifiable_handoff_text.py, df9f67af7c1f7fecd3b4a9768c0863d035ed3088
   174	
   175	## Task 2: Add realtime ANSI pre-check output to external review, success
   176	
   177	### rollout_summary_files
   178	
   179	- rollout_summaries/2026-10-18T10-39-52-b3XU-gate4_review_choice_loop_and_external_review_streaming.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/18/rollout-2026-10-18T17-39-52-01a14e98-b2b9-7043-9d17-65dd8df4be46.jsonl, updated_at=2026-10-18T15:23:36+00:00, thread_id=01a14e98-b2b9-7043-9d17-65dd8df4be46, 31 targeted tests and full verification passed)
   180	
   181	### keywords
   182	
   183	- run_external_review.py, run_gate, PreconditionFailedError, [PRECONDITION BLOCKED], ANSI, flush=True, audit_epic.py, check_bdd_traceability.py, scripts/verify.sh, android-ui-audit
   184	
   185	## User preferences
   186	
   187	- The user explicitly corrected the lifecycle sequence: “Gate 4 => Review Choice”, then “Finish” or “Cross model review”, and “Sau bước này chạy lại Gate 4 ... Loop cho tới khi finish.” -> preserve this order for similar ai-agent-tools lifecycle work. [Task 1]
   188	- After verification, the user asked “Commit and finish all tasks.” -> commit locally when requested, but do not push without explicit permission. [Task 1]
   189	
   190	## Reusable knowledge
   191	
   192	- Enforced invariant: `Gate 4 PASS -> Review Choice; Finish -> Gate 5; Cross-model review -> Gate 4 in full`. A review round, decision, Fix commit, Gate 5-requested change, cross-model CLI failure, or timeout that changes/reassesses the candidate requires full Gate 4 before another Review Choice. Gate 4 is SHA-bound. [Task 1]
   193	- The policy update touched `rules/CRITICAL_RULES.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-implementation/SKILL.md`, bilingual lifecycle docs, lifecycle-selection docs, and `scripts/test_verifiable_handoff_text.py`; commit `df9f67af7c1f7fecd3b4a9768c0863d035ed3088` is `[REVIEW_WORKFLOW] Loop review choice through Gate 4`. [Task 1]
   194	- `run_gate()` emits `[Pre-check]`, `PASS`, `FAILED`, or `TIMEOUT` to stderr with `flush=True`. `PreconditionFailedError` holds `gate`, `reason`, and `details`; its banner shows the final 25 detail lines and confirms the selected CLI was not invoked. [Task 2]
   195	- Route `audit_epic.py`, declared Integration commands, and `check_bdd_traceability.py` through `run_gate()` while retaining captured output in the facts bundle. `run_external_review.py` does not directly invoke `android-ui-audit`; that is only indirect through the quality-provider registry. Targeted suite passed 31 tests and `scripts/verify.sh` reported `PASS — safe to publish`; worktree was clean on `main`, with no push. [Task 2]
   196	
   197	## Failures and how to do differently
   198	

codex
The supplied audit, 22/22 traceability result, task evidence, and protected-path changes are consistent. No grader amendments or out-of-task commits were disclosed. However, static inspection found four merge-blocking contract gaps not covered by the passing tests.

Gate 5 still requires:

- Human confirmation that the Principal Reviewer prompt is a genuine sign-off brief covering P1–P8.
- A developer-selected packaged-epic trial proving `check_epic_readiness.py` produces an accurate, useful report.

No files or Git state were changed.

Verdict: CHANGES REQUIRED
[Important] skills/dev-implementation/resources/scripts/check_epic_readiness.py:157-176 — R1 only sends already-complete language pairs to `--require-bilingual`; a missing `.en.md` or `.vi.md` counterpart is omitted entirely, allowing incomplete spec, HLD, or BDD artifacts to pass.
[Important] skills/dev-implementation/resources/scripts/check_epic_readiness.py:575-595 — R7 validates `Design commit` only when the line matches; a handoff with the field missing silently passes despite the published contract requiring `uncommitted` or an ancestor of HEAD.
[Important] skills/dev-lifecycle/references/principal-review.md:13-15 — The recommendation omits D2’s different-model trigger and required HLD `Author` grounding, and does not include the HLD’s promised recommendation to use each CLI’s strongest reasoning model.
[Important] skills/dev-lifecycle/references/principal-review.md:49-58 — The procedure records `fixed in <sha>` and commits decisions before the revision commit that would create that SHA, then requests a separate revision commit; the prescribed order cannot produce truthful decision metadata.

tokens used
167,080
````
