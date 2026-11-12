# Principal Review: token_throttling_optimization

## Round 1

- **Date**: 2026-11-12T19:50:26Z
- **SHA**: 8d456f6ec6f420e17932c67c8425a563ac3913ee
- **Base**: main
- **CLI**: codex
- **Model**: gpt-6.1-sol
- **Thinking**: high
- **Status**: discarded: tree modified (skills/check-quota/resources/dashboard/quota_dashboard.html)
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | .devtool/epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md:Requirement Analysis §3 | The proposed fast-path guard does not establish architectural safety. `_has_domain_or_critical_conflict()` only checks a narrow keyword list ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:511)); probes returned False for “ambiguous architectural state transition” and “Debatable: two valid designs.” Removing Assistant evaluation therefore removes the remaining ambiguity check. Proposed: require an explicit, source-grounded classification of every finding as an unambiguous code fix; route unknown or debatable classifications through Role 2.2, and add negative-path tests. | fixed in ba2042d |
| 2 | Important | .devtool/epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md:Requirement Analysis §3 / TTO-HP-07 | The direct fixer lacks an input and success contract. `_apply_code_fixes()` defaults to an empty plan, supplies no review-artifact path, ignores the dispatcher result, and returns True ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:1101)). A mocked failed dispatch confirmed that True result. Proposed: pass verified findings and design anchors explicitly, check dispatch and scoped-test results, and prohibit recording “fixed” decisions or advancing on failure. | fixed in ba2042d |
| 3 | Important | .devtool/epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md:Parallel Worker Pool Execution | The runner/pool integration leaves repository-root and epic-worktree-root meanings unresolved. The runner dispatches from its supplied root ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:220)), whereas `merge_slot()` appends `.worktrees/<epic_dir>` ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/manage_worker_pool.py:124)). Passing the active epic worktree produces a nested path and returned False in the probe. Proposed: define both roots and both epic identifiers explicitly, use a dispatcher bound to each slot, serialize merges, and test execution from an actual epic worktree through successful merge and failure recovery. | fixed in ba2042d |
| 4 | Important | .devtool/epic/token_throttling_optimization/task_01_diff_only_external_review_and_transcript_isolation.md:Requirement Analysis §2 | Filtering artefact lists does not exclude Vietnamese content from review prompts. Principal delta extraction selects the entire epic directory ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:997)); source-diff extraction also lacks a Vietnamese exclusion ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:657)). Thus changed companions can still enter prompts through diffs. Proposed: apply the English-only policy to every diff path, including principal deltas, fallback diffs, ad-hoc reviews, and local-review inputs; test changed Vietnamese files inside and outside the epic directory. | fixed in ba2042d |
| 5 | Important | .devtool/epic/token_throttling_optimization/task_01_diff_only_external_review_and_transcript_isolation.md:Transcript Isolation | `<epic>_round<n>.raw.log` collides between Principal Review and Cross-Model Review. Their markdown files are separate ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:311)), and round numbering is derived independently from each file ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:1440)). Both first rounds therefore target the same log, invalidating the earlier pointer. Proposed: include review kind and candidate/run identity in the log path, and update the HLD, bilingual BDDs, and Task 6 isolation assertions accordingly. | fixed in ba2042d |
| 6 | Important | .devtool/epic/token_throttling_optimization/task_03_option_a_bilingual_and_surgical_contract_guards.md:Option A Guards / TTO-ST-03 | “Full parity” and detection of an out-of-sync HLD are not defined sufficiently for the strict gate. The document checker compares heading levels ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/doc_quality_check/resources/scripts/check_document.py:200)); a probe accepted stale translated content with identical headings. The BDD loader compares scenario identifiers, without inspecting HLD content ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/check_bdd_traceability.py:82)). Proposed: define synchronization provenance for each translated document, validate it at Finish, and separate readiness assertions about Spec/HLD synchronization from traceability assertions about BDD identifiers; include a same-heading English-content-change test. | fixed in ba2042d |
| 7 | Important | .devtool/epic/token_throttling_optimization/task_03_option_a_bilingual_and_surgical_contract_guards.md:Surgical File Reading Gate | The new guard would reject this epic’s existing task contracts. For example, Task 1 allows the 1,508-line `test_run_external_review.py` without a target anchor, and Task 4 does likewise for the 629-line `tests/test_lifecycle_runner.py`; these are existing Python source files covered by the stated rule. Several Task 2 and Task 3 paired tests have the same omission. Proposed: add file-specific symbol/window anchors to every affected task before implementation and verify the completed epic against the newly introduced guard. | fixed in ba2042d |
| 8 | Important | .devtool/epic/token_throttling_optimization/task_05_slimming_rules_skills_dedup_and_selective_reviewer.md:Requirement Analysis §5 | The prescribed `check_bdd_traceability.py plan <epic> --strict-bilingual` invocation cannot run. The CLI requires `--scenarios` and `--tasks` ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/check_bdd_traceability.py:231)). An in-memory probe adding the proposed flag still exited 2 because those arguments were missing. Proposed: specify the complete invocation with the scenario path, resolved task paths, and agreed flag placement, then test that exact Pre-Finish command. | fixed in ba2042d |
| 9 | Important | .devtool/epic/token_throttling_optimization/2026-11-13-token-throttling-optimization-design.en.md:§4.5 Output Token Cap Directive | Restricting output to state transitions, tool calls, and three failure bullets conflicts with mandatory machine-readable responses and exhaustive blocking findings. Review completion requires a parsed Verdict and findings ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:1420)). Proposed: apply the cap to discretionary narration while explicitly preserving required verdicts, complete findings tables, structured provider results, worker status contracts, and human gate decisions; mirror the clarification in Vietnamese and task requirements. | fixed in ba2042d |
| 10 | Important | .devtool/epic/token_throttling_optimization/task_05_slimming_rules_skills_dedup_and_selective_reviewer.md:Files | Spec §4.3 explicitly requires updating `implementer-prompt.md`, but no task permits that edit. The interactive controller actively dispatches this template ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/subagent-driven-development/SKILL.md:298)). Completing the approved prompt change would therefore violate Allowed files and trigger Stop-and-Report. Proposed: add `skills/subagent-driven-development/implementer-prompt.md` to Task 5, with explicit bounded-read instructions and corresponding contract verification. | fixed in ba2042d |
| 11 | Important | .devtool/epic/token_throttling_optimization/task_06_integration_and_regression_verification.md:Verification V1 | The proposed RED checks byte ceilings already required to pass in Tasks 3 and 5, which are prerequisites. A correctly completed dependency state therefore makes this assertion GREEN before Task 6’s registry change; the recorder rejects a passing pytest invocation as RED ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_task_checks.py:140)). Proposed: target RED at Task 6’s missing release-suite registration, retain byte ceilings as regression checks, and ensure the initial failure comes from a collected assertion rather than a missing test target. | fixed in ba2042d |

Raw output:

````text
Reviewed all 12 artefacts against `8d456f6ec6f420e17932c67c8425a563ac3913ee`. Read-only probes covered exception paths, scenario parsing, review parsing, classification, and integration boundaries. No files or git state were changed.

Verdict: CHANGES REQUIRED
[Important] .devtool/epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md:Requirement Analysis §3 — The proposed fast-path guard does not establish architectural safety. `_has_domain_or_critical_conflict()` only checks a narrow keyword list ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:511)); probes returned False for “ambiguous architectural state transition” and “Debatable: two valid designs.” Removing Assistant evaluation therefore removes the remaining ambiguity check. Proposed: require an explicit, source-grounded classification of every finding as an unambiguous code fix; route unknown or debatable classifications through Role 2.2, and add negative-path tests.

[Important] .devtool/epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md:Requirement Analysis §3 / TTO-HP-07 — The direct fixer lacks an input and success contract. `_apply_code_fixes()` defaults to an empty plan, supplies no review-artifact path, ignores the dispatcher result, and returns True ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:1101)). A mocked failed dispatch confirmed that True result. Proposed: pass verified findings and design anchors explicitly, check dispatch and scoped-test results, and prohibit recording “fixed” decisions or advancing on failure.

[Important] .devtool/epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md:Parallel Worker Pool Execution — The runner/pool integration leaves repository-root and epic-worktree-root meanings unresolved. The runner dispatches from its supplied root ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:220)), whereas `merge_slot()` appends `.worktrees/<epic_dir>` ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/manage_worker_pool.py:124)). Passing the active epic worktree produces a nested path and returned False in the probe. Proposed: define both roots and both epic identifiers explicitly, use a dispatcher bound to each slot, serialize merges, and test execution from an actual epic worktree through successful merge and failure recovery.

[Important] .devtool/epic/token_throttling_optimization/task_01_diff_only_external_review_and_transcript_isolation.md:Requirement Analysis §2 — Filtering artefact lists does not exclude Vietnamese content from review prompts. Principal delta extraction selects the entire epic directory ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:997)); source-diff extraction also lacks a Vietnamese exclusion ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:657)). Thus changed companions can still enter prompts through diffs. Proposed: apply the English-only policy to every diff path, including principal deltas, fallback diffs, ad-hoc reviews, and local-review inputs; test changed Vietnamese files inside and outside the epic directory.

[Important] .devtool/epic/token_throttling_optimization/task_01_diff_only_external_review_and_transcript_isolation.md:Transcript Isolation — `<epic>_round<n>.raw.log` collides between Principal Review and Cross-Model Review. Their markdown files are separate ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:311)), and round numbering is derived independently from each file ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:1440)). Both first rounds therefore target the same log, invalidating the earlier pointer. Proposed: include review kind and candidate/run identity in the log path, and update the HLD, bilingual BDDs, and Task 6 isolation assertions accordingly.

[Important] .devtool/epic/token_throttling_optimization/task_03_option_a_bilingual_and_surgical_contract_guards.md:Option A Guards / TTO-ST-03 — “Full parity” and detection of an out-of-sync HLD are not defined sufficiently for the strict gate. The document checker compares heading levels ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/doc_quality_check/resources/scripts/check_document.py:200)); a probe accepted stale translated content with identical headings. The BDD loader compares scenario identifiers, without inspecting HLD content ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/check_bdd_traceability.py:82)). Proposed: define synchronization provenance for each translated document, validate it at Finish, and separate readiness assertions about Spec/HLD synchronization from traceability assertions about BDD identifiers; include a same-heading English-content-change test.

[Important] .devtool/epic/token_throttling_optimization/task_03_option_a_bilingual_and_surgical_contract_guards.md:Surgical File Reading Gate — The new guard would reject this epic’s existing task contracts. For example, Task 1 allows the 1,508-line `test_run_external_review.py` without a target anchor, and Task 4 does likewise for the 629-line `tests/test_lifecycle_runner.py`; these are existing Python source files covered by the stated rule. Several Task 2 and Task 3 paired tests have the same omission. Proposed: add file-specific symbol/window anchors to every affected task before implementation and verify the completed epic against the newly introduced guard.

[Important] .devtool/epic/token_throttling_optimization/task_05_slimming_rules_skills_dedup_and_selective_reviewer.md:Requirement Analysis §5 — The prescribed `check_bdd_traceability.py plan <epic> --strict-bilingual` invocation cannot run. The CLI requires `--scenarios` and `--tasks` ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/check_bdd_traceability.py:231)). An in-memory probe adding the proposed flag still exited 2 because those arguments were missing. Proposed: specify the complete invocation with the scenario path, resolved task paths, and agreed flag placement, then test that exact Pre-Finish command.

[Important] .devtool/epic/token_throttling_optimization/2026-11-13-token-throttling-optimization-design.en.md:§4.5 Output Token Cap Directive — Restricting output to state transitions, tool calls, and three failure bullets conflicts with mandatory machine-readable responses and exhaustive blocking findings. Review completion requires a parsed Verdict and findings ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:1420)). Proposed: apply the cap to discretionary narration while explicitly preserving required verdicts, complete findings tables, structured provider results, worker status contracts, and human gate decisions; mirror the clarification in Vietnamese and task requirements.

[Important] .devtool/epic/token_throttling_optimization/task_05_slimming_rules_skills_dedup_and_selective_reviewer.md:Files — Spec §4.3 explicitly requires updating `implementer-prompt.md`, but no task permits that edit. The interactive controller actively dispatches this template ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/subagent-driven-development/SKILL.md:298)). Completing the approved prompt change would therefore violate Allowed files and trigger Stop-and-Report. Proposed: add `skills/subagent-driven-development/implementer-prompt.md` to Task 5, with explicit bounded-read instructions and corresponding contract verification.

[Important] .devtool/epic/token_throttling_optimization/task_06_integration_and_regression_verification.md:Verification V1 — The proposed RED checks byte ceilings already required to pass in Tasks 3 and 5, which are prerequisites. A correctly completed dependency state therefore makes this assertion GREEN before Task 6’s registry change; the recorder rejects a passing pytest invocation as RED ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_task_checks.py:140)). Proposed: target RED at Task 6’s missing release-suite registration, retain byte ceilings as regression checks, and ensure the initial failure comes from a collected assertion rather than a missing test target.

--- stderr ---
OpenAI Codex v0.167.0
--------
workdir: /Users/danhdueexoictif/AllProjects/ai-agent-tools
model: gpt-6.1-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: high
reasoning summaries: none
session id: 01a1d149-3e1e-7403-b332-d7402feac3cd
--------
user
# Principal Review Prompt

You are the Principal Reviewer who signs off this architectural design before implementation. You are strictly read-only: do not modify, create, or delete any file, and do not run commands that write to the repository or alter git state. Read the artefacts, inspect the source at `8d456f6ec6f420e17932c67c8425a563ac3913ee`, and report.

## Candidate

- Commit under review: `8d456f6ec6f420e17932c67c8425a563ac3913ee`
- Base the branch diverged from: `main`
- Base commit: `8d456f6ec6f420e17932c67c8425a563ac3913ee`
- Target path / Epic directory: `.devtool/epic/token_throttling_optimization`

## Artefacts

Read these paths, relative to the repository root:

- `.devtool/epic/token_throttling_optimization/2026-11-13-token-throttling-optimization-design.en.md`
- `.devtool/epic/token_throttling_optimization/2026-11-13-token-throttling-optimization-design.vi.md`
- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md`
- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.vi.md`
- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md`
- `.devtool/epic/token_throttling_optimization/bdd_scenarios.vi.md`
- `.devtool/epic/token_throttling_optimization/task_01_diff_only_external_review_and_transcript_isolation.md`
- `.devtool/epic/token_throttling_optimization/task_02_silent_gate4_and_truncated_test_runners.md`
- `.devtool/epic/token_throttling_optimization/task_03_option_a_bilingual_and_surgical_contract_guards.md`
- `.devtool/epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md`
- `.devtool/epic/token_throttling_optimization/task_05_slimming_rules_skills_dedup_and_selective_reviewer.md`
- `.devtool/epic/token_throttling_optimization/task_06_integration_and_regression_verification.md`

## Readiness facts

Epic: token_throttling_optimization (token_throttling_optimization), 6 tasks
R1 PASS
R2 PASS
R3 PASS
R4 PASS
R5 PASS
R6 PASS
R7 PASS
R8 SKIP
Result: 0 FAIL, 0 WARN — PASS

The readiness report is already proven: all facts above have passed their mechanical checks; do not restate them, spend your review on judgement, architecture, and source grounding.



## Mandatory Dynamic Probing Rule

Do not rely solely on static diff inspection. For any language processing logic, regex expressions, exception handlers (`try/except`), or ORM persistence code, you MUST execute active read-only terminal probes (e.g. `python3 -c "..."` or interactive read-only REPL commands) to verify:
1. Local variables referenced in exception handlers are not unbound when exceptions occur early in a block.
2. Edge-case lexical tokens and inflections are not deformed by tokenization or lemmatization.
3. Database statement ordering in transaction flushes does not violate foreign keys or unique constraints.

## Rules

# Principal Review Rules

To avoid false-positive findings, evaluate design documents and epic artefacts against these principles:

1. **Severities**:
   - **Critical**: The epic or architecture cannot reach its goal or pass execution gates as designed (e.g. fatal architectural flaw, missing core contract).
   - **Important**: A task or component would hit Stop-and-Report, ship incorrect behavior, or break module isolation during implementation.
   - **Minor**: Wording, formatting, typo, and minor consistency adjustments.

2. **Readiness Report Is Proven Fact**:
   - The mechanical checks (R1–R8) in `check_epic_readiness.py` are already validated prior to review.
   - Do not re-verify mechanically checked facts or restate them as findings; spend your review effort on judgement, architecture, and source grounding.

3. **Grounding in Active Source**:
   - Every claim about the repository source code must name the specific file and line number read.
   - Grounding verifies that referenced symbols, functions, methods, and configurations actually exist at the candidate commit.

4. **Actionable Findings**:
   - Each finding must name the specific artefact (file path) and location (heading or section) to change.
   - Each finding must conclude with a concrete `Proposed: <edit>` recommendation.

5. **Shared Contracts, Symlink Resolution & Source-of-Truth Hierarchy (Forward Alignment over Legacy Reversion)**:
   - **Source-of-Truth Hierarchy**:
     1. **Tier 1 (Highest Authority — Approved Design Intent)**: User-approved Spec (`*-design.en.md`) and HLD (`<epic_dir>.en.md` Goals & Architecture).
     2. **Tier 2 (Cross-Repo Contract Baseline)**: `shared-contracts/<domain>/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`).
     3. **Tier 3 (Legacy Code Baseline)**: Existing source files in `src/` and task `Allowed files`.
   - **Forward Alignment Rule (Never Revert Approved Design Intent)**: When Tier 1 intentionally introduces a new pipeline structure, step count, enum, or schema (e.g., consolidating 7 legacy steps into 5 steps) that differs from Tier 2 (`shared-contracts/`) or Tier 3 (`src/`), **DO NOT propose reverting the HLD/Spec back to the legacy Tier 2/Tier 3 design**. Instead, report a **Forward Contract-Sync / Blast-Radius Gap** and propose:
     1. Updating `shared-contracts/<domain>/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md` + `sync_contracts.py ack`) and `## Shared Contract Impact` to match the approved Tier 1 design (with backward-compatibility shims if needed).
     2. Adding the affected legacy callers (e.g., `worker/bridge.py`, `preview/jobs.py`) into the appropriate task's `Allowed files` so implementation migrates them forward to the new design.
   - When reviewing design documents impacting inter-service or cross-repo communication, verify that `shared-contracts/` paths resolve on disk (following symlinks to target repositories if applicable).
   - Flag any unacknowledged contract drift or missing `task_01` contract/adapter synchronization as **Critical** or **Important** with a **forward-migration** `Proposed:` action.

6. **5-Layer Deep Verification Checklist**:
   - **Unbound Variable in Fallback**: Verify that all variables referenced in `except` blocks are assigned or imported before the `try` block begins.
   - **Part-of-Speech Ambiguity**: Verify that morphological transformation functions (lemmatizers, stemmers, token normalizers) disambiguate noun/adjective forms from verb-like gerunds and participles.
   - **ORM Flush Semantics**: Verify SQLAlchemy Unit of Work execution ordering (Insert -> Update -> Delete). Forbid mutating ORM entities before flushing deleted records sharing the same unique key or index constraint.
   - **Interactive Contract Boundary**: Verify that interactive token and span coverage on user interfaces conforms strictly to `architecture_and_flow.md`.
   - **Fixture Schema Sanity**: Verify that test fixtures and mock records in RED tests satisfy database check constraints before reaching domain assertions.

## Checklist

- **P1 (Consistency)**: Consistency across spec, HLD, BDD, tasks, and documentation: decisions, field names, numbers, titles, statuses.
- **P2 (Grounding)**: Grounding: every path, symbol, signature, return type, route, and constant in `Decisions Already Made` and `Impact Analysis` exists in source code as described.
- **P3 (Pinned behaviour)**: Pinned behaviour: existing tests that pin a behaviour a task changes, especially when outside Allowed files.
- **P4 (Blast radius)**: Blast radius: other writers and readers of changed data, background jobs, callers outside Allowed files, migrations and backfill.
- **P5 (Task split and Verification)**: Task split and Verification: dependency order, RED rows that can fail before implementation, GREEN rows that pass at baseline, DoD references, Stop conditions.
- **P6 (BDD quality)**: BDD quality: valid Gherkin, dimensions that match scenarios, grounded assertions, tier tags.
- **P7 (Shared Contracts & Feasibility)**: Verification Environment, integration test feasibility, and cross-repo contract audit. When `shared-contracts/` (or an external service/FFI boundary) is touched, inspect `shared-contracts/<domain>/` canonical files (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`) on disk (including resolving symlinks to target repositories if applicable). Verify that the HLD contains a dedicated `## Shared Contract Impact` section, guarantees backward compatibility (optional fields, safe defaults, no breaking wire changes), reserves `task_01` for contract synchronization, and outputs the Parallel Handoff Summary for satellite repos.
- **P8 (Risks, rollout and rollback)**: Risks, rollout and rollback.

## Required output

Do NOT use the bracketed tags `[Critical]`, `[Important]`, or `[Minor]` anywhere in your prose or analysis above the final verdict block.

End your answer with these exact lines and nothing after them (no markdown bolding `**`, no backticks, no bullet before `Verdict:`):

Verdict: PASS
(or `Verdict: CHANGES REQUIRED`)
[Critical|Important|Minor] <artefact>:<location> — <problem>. Proposed: <edit>

Rules for Severity & Verdict:
- Use `Critical` for a defect that breaks the design goal, `Important` for one that must be fixed before implementation, and `Minor` for anything else.
- **Exhaustive Per-File Pass (Anti-Drip-Feed Rule)**: In Round 1 (full-scope review), report ALL `Critical` and `Important` defects within each inspected artefact in the same round; never hold back or drip-feed findings on untouched sections of the same file across later delta rounds.
- Output `Verdict: CHANGES REQUIRED` if and only if there is at least one `Critical` or `Important` finding.
- If there are no findings (or only `Minor` findings), you MUST output `Verdict: PASS`.
- A review with no finding still ends with its `Verdict: PASS` line.

2026-11-12T19:43:26.583164Z ERROR codex_memories_write::phase2: Phase 2 no changes
codex
Tôi sẽ dùng `d3nexus:principal-review` để đối chiếu toàn bộ artefact với source tại commit đã chỉ định, rồi chạy các probe chỉ đọc cho những logic liên quan. Tôi cũng sẽ áp dụng `task-observer` trong phạm vi không ghi file.

exec
/bin/zsh -lc 'cat /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.28.3/skills/task-observer/SKILL.md /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.28.3/skills/using-superpowers/SKILL.md /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.28.3/skills/principal-review/SKILL.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
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
   n=$(find "$d" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l)         # independent count via find (zsh-safe)
   parsed=0
   if [ "$n" -gt 0 ]; then
     for f in "$d"/*.md; do
       [ -e "$f" ] || continue
       hdr=$(awk 'NR==1 && /^---[[:space:]]*$/ {fm=1; next}
                  fm && /^---[[:space:]]*$/ {exit}
                  fm' "$f")
       [ -n "$hdr" ] && parsed=$(( parsed + 1 ))
       printf '%s\n---\n' "$hdr"
     done
   fi
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

The rule behind both: an enforcement trigger must hang on an event objectively
visible in the tool record, never on the agent noticing that a moment qualifies.
And a counter bound to a single tool is silently inert in every session that does
not use it — such triggers always need a second, independent path.

**Id and filename.** Each observation is `NNNN-short-slug.md` (zero-padded
id + a kebab-case slug from the title). The id is the highest of three
values, plus one: the highest numeric prefix in `observation-log/`, the
highest in `observation-log/archive/`, and the number in
`observation-log/archive/.id-floor` (the highest id ever issued — update it
whenever you issue an id above it, so the counter can never restart from 1
when the active directory is empty):

```bash
d=skill-observations/observation-log
hi=$( { ls "$d" "$d/archive" 2>/dev/null | grep -oE '^[0-9]+'; cat "$d/archive/.id-floor" 2>/dev/null; } \
     | sort -n | tail -1); : "${hi:=0}"
[ "$hi" -eq 0 ] && [ -n "$(find "$d" -maxdepth 1 -name "*.md" 2>/dev/null)" ] && { echo "ID COMMAND BROKEN — log is non-empty but no ids extracted"; exit 1; }
next_id=$(( hi + 1 )); echo "$next_id" > "$d/archive/.id-floor"
```

The guard line distinguishes "the log says zero" from "I could not read
the log": a command that fails to empty rather than to error would
otherwise propose id 1 in a populated log. A new file never touches another entry's bytes, so it cannot truncate,
overwrite or renumber anyone else's work. If two parallel sessions pick the
same id, two files share a number — harmless; the next review renumbers one
and logs a meta-observation.

**Batch writes: resolve each id at its own write time.** When logging more
than one observation in a session that may overlap a scheduled review or
another writer, run the id snippet before EACH file — never pre-compute a
range and hardcode sequential numbers into a batch. A batch append is N
separate races, not one; pre-baked numbers collapse N independent
max-checks into a single stale read (observed: a hardcoded id collided
with one a parallel review issued between the check and the write).

**A structural probe that comes back empty where content existed before is
a stop signal, not a create.** If the directory or file you logged to
earlier in the session is suddenly missing, or the id check returns empty
in a log you know is populated, HALT and re-probe the structure (is there
an `observation-log/`? a `log.md.migrated`?) — a parallel session may have
migrated or reorganised the storage. Never let an append silently recreate
a missing target: that converts a migration signal into corruption
(observed: a stale session recreated the retired `log.md` with a fresh
"Observation 1" after the per-file migration renamed it).

**File format.** YAML frontmatter (the metadata every scan reads) followed
by the Issue → Improvement → Principle body. **The frontmatter is mandatory;
always write `status: open` and a non-empty `siblings_checked:` at creation
time** — an observation without a `status` field is treated as OPEN by
reviews, never as nonexistent, and one without `siblings_checked:` counts
as logged without a sibling check.

```markdown
---
id: [N]
title: [Short descriptive title]
status: open            # open | actioned | declined | superseded | parked
type: open-source       # open-source | internal
skill: [list of existing skills this improves — always a list, even with
       one entry; first entry is primary; may be empty]
proposes_skill: [list of new skills this argues for, by working name;
       may be empty — an observation can fill either list or both]
siblings_checked: [MANDATORY, never blank: the family name and the members
       evaluated, plus the verdict — e.g. "family-name: a, b — shared, both
       added" or "family-name: a, b — instance-specific, no propagation";
       the literal `none` only where the target belongs to no family]
area: [which part of the skill or workflow]
date: [YYYY-MM-DD]
session_context: [what task was being worked on]
parked_until:           # MANDATORY when status is parked, empty otherwise:
                        #   one line naming the condition that unparks it
resolved:               # date resolved; leave empty while OPEN
resolution:             # what was done — set only when actioned/declined
reference:              # optional: path to saved session-local evidence
---

**Issue:** [What happened — specific enough to understand weeks later
without the original conversation.]

**Suggested improvement:** [Concrete change. For existing skills, name the
section or rule; for new skills, scope and key components.]

**Principle:** [The generalisable takeaway — the most important field.]
```

**`parked` means decided, not pending.** Use it when an observation is sound
but cannot be acted on until an external precondition is met — the scheduled
task that produced it is disabled, the tool it describes is out of use, a
dependency has not landed. A parked entry is OUT of the work queue: reviews
must not re-escalate it, and the decision belongs in `status:`, not in a
free-text note beside a `status: open` (a note nothing classifies on leaves
the entry in the queue and it gets re-raised at every review). It is not
resolved either, so it never archives — archival needs a resolved status plus
a `resolved:` date. It stays in `observation-log/` indefinitely until either
its `parked_until:` condition is met — set it back to `open` and queue it — or
it is genuinely resolved. `parked_until:` is mandatory whenever status is
`parked`: one line stating the condition, phrased so a later session can
actually answer whether it has happened.

**Context preservation:** if an observation depends on session-local data
(uploads, API output), save that context into the workspace first and set
`reference:` to its path — an observation whose evidence dies with the
session is incomplete.

**Confidentiality at logging time:** for `type: open-source` observations,
the Issue/Improvement fields may reference specifics for context, but the
Principle must be fully generalised — no client names, domains, or details
traceable to a real project. Full confidentiality layers:
`references/skill-authoring.md`.

**Changing an existing observation:** re-read that one file, edit only the
frontmatter fields you are changing (`status`, `parked_until`, `resolved`,
`resolution`),
never batch-rewrite the directory. Archival is a plain `mv` (below).

## Referencing Observations

Cite an observation by the `id` field in its frontmatter (= the `NNNN-`
filename prefix). Never cite a `grep -n` line number as if it were the id —
search-tool line numbers are positional metadata, not identifiers. A cited
id must fall within the range that exists across `observation-log/`,
`archive/` and `.id-floor`; a number far outside it is almost certainly a
line number misread as an id.

## Taxonomy (quick version)

**Open-source** — client-agnostic, methodology-driven, useful to other
practitioners. **Internal** — contains user/client/project specifics or
personal preferences. Default to open-source when it could go either way,
stripping specifics. The boundary is also a confidentiality boundary, and
the two errors are not symmetric: over-classifying as internal costs only
reach, under-classifying can leak — when genuinely uncertain, prefer
internal and promote later. Full requirements (attribution, licensing,
structure): `references/skill-authoring.md`.

## Archival on Write

On every write, first `mv` already-resolved files from `observation-log/`
to `observation-log/archive/`. "Already resolved" is read from the file's
own frontmatter: `status: actioned`, `declined` or `superseded` AND a
`resolved:` date **before today**. Files resolved today stay until the next
day, whichever session resolved them — the grace period lives in the file,
never in session memory. A resolved file with no readable `resolved:` date
gets today's date written to that field instead of being archived. One
file per `mv`; no rewrite of anything else. Helper and rationale:
`references/observation-log.md`.

## Surfacing Protocol

Default: at end of session, as a grouped summary — improvements grouped by
skill, new-skill candidates listed separately; for each, one sentence plus
suggested type; ask which to act on. Surface earlier when an observation
needs user input to be complete, when a skill is actively producing wrong
output, or when observations cluster on one skill.

**Deferral wears a second disguise: not a promise, but an argument.** "Let's
wait until this has seen a few days of real use", "we should gather more data
first" — this reads as diligence, which is exactly why it goes unchallenged,
including by the person saying it. It is not an announcement, so a rule about
executing rather than announcing does not catch it. So before writing *any*
"later" into a recommendation, name two things: **which specific observation
would change the decision, and when it could realistically arrive.** If you
cannot name one, the evidence is either already conclusive (act now) or waiting
adds nothing (act now). Then ask what the delay costs — if a known-defective
state stays live meanwhile, the burden of proof is on deferring, not on acting.
A deferral is a decision and needs the same justification as acting; "more
evidence would be better" is not one, because the question is whether more
evidence could change the OUTCOME.

**Default to log-and-defer.** Surfacing an observation is not an invitation
to act on it: state that it is logged for the next review, and stop.
Reserve in-session application strictly for the triggers under "Acting on
Observations". Do NOT routinely offer a binary "apply now vs leave for next
review" choice; for users who run regular reviews that offer is unwanted
friction, and if a user has said they always defer, suppress it entirely.

**Self-check before surfacing:** observations were logged throughout the
whole session (including discussion phases); logged silently; each follows
Issue → Improvement → Principle; each is typed; existing-skill items name
the section; no open-source Principle contains client-identifying info;
every observation file carries `status:` (`status: open` at write time) and
a non-empty `siblings_checked:` — if any lacks one, do the sibling check
now and record it rather than back-filling the field with `none`.

## Acting on Observations

Act only in three contexts: (1) the comprehensive review (load
`references/weekly-review.md`); (2) an explicit user request ("update X
skill", "act on observation #N"); (3) in-session correction when a skill is
producing wrong output the user should know about. Otherwise: log, don't
act.

**Read the full body before resolving, dismissing, fixing, or citing.** A
tracked item's title (observation, GitHub issue, ticket) is an index entry,
not its content — it compresses away the failure story, the reporter's
context, and often the proposed fix. Dismissal is the path with no
downstream checkpoint: a resolved or cited item gets reviewed later, a
dismissed one silently disappears. Harvest fix designs from issue bodies —
reporters frequently include the correct solution, which also settles
attribution. When a parallel agent logs a finding that appears to duplicate
your own, diff the two bodies, not the titles: two entries about the same
mechanism can carry opposite operational conclusions, and the second is
often the refinement, not the echo. Apparent agreement suppresses
verification more effectively than disagreement does, so this rule binds
hardest exactly where it feels least necessary.

When acting: small, clearly-additive, low-risk changes (a new rule, a
clarification, a factual fix) may be applied without waiting for the next
review — "directly" means *now*, not *in place*: the edit is still made on
a staged copy based on a fresh read of the live file and handed to the user
to install, in every environment and every context. Staging-only has no
interactive exception; an exception the user has to remember is a gate
that eventually gets left open. Substantial changes (restructuring, new
capabilities, changed methodology) and all new-skill creation: load
`references/skill-authoring.md` first and follow its editing and staging
rules. A principle that applies to skills generally goes to the
cross-cutting principles file (same reference).

**Set the status in the same turn you act.** An observation acted on
in-session must have its frontmatter updated — `status: actioned`,
`resolved: YYYY-MM-DD`, `resolution: what was done` — before the turn
ends. The work and the bookkeeping are two acts, and the second is the one
that gets dropped; a stale `open` entry then invites redoing finished work
over a section that has since moved on. The write is the enforcement,
exactly as it is for logging.

## Quick Reference

| Question | Answer |
|----------|--------|
| When do I observe? | The whole session, including feedback and reflection phases |
| How do I log? | Silently, immediately, as one file per observation named `NNNN-slug.md`; id = max(active, archive, `.id-floor`) + 1 |
| When do I surface? | End of session, or earlier if needed |
| Status field? | Mandatory `status: open` frontmatter on every new observation; reviews treat a missing status as OPEN, never as nonexistent. Five values: `open`, `actioned`, `declined`, `superseded`, `parked` — `parked` = decided but blocked on an external precondition, so it leaves the queue, requires `parked_until:`, and never archives |
| Does the target skill have siblings? | Resolve it against `skill-observations/skill-families.md` BEFORE writing; add every sibling the insight applies to to `skill:`, and record the verdict in the mandatory `siblings_checked:` field — including "checked, no propagation" |
| A scan or query came back empty? | Two possibilities, only one is a finding: guard every retrieval meant to prevent duplicate work with an independent existence check, and treat empty output over known content as a broken command |
| Citing an observation number? | From the `id:` frontmatter field (= the `NNNN-` filename prefix); never a `grep -n` line number; sanity-check against the known id range |
| Open-source or internal? | Default open-source; the boundary is confidential |
| Small fix or substantial? | Additive → apply directly; restructuring/new skill → `references/skill-authoring.md` |
| Changing an observation (status/archival)? | Re-read that one file, edit only its frontmatter, or `mv` it to `observation-log/archive/` — no shared-file rewrite |
| Upgrading from a single-file `log.md`? | Scripted, once — `references/migration.md` |
| Weekly review? | Trigger check at session start; procedure in `references/weekly-review.md` |
| No filesystem? | Handoff-doc mode — `references/environments.md` |
---
name: using-superpowers
description: Use when starting any conversation - establishes how to find and use skills, requiring skill invocation before ANY response including clarifying questions
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## The Rule

**Invoke relevant or requested skills BEFORE any response or action** — including clarifying questions, exploring the codebase, or checking files. If it turns out wrong for the situation, you don't have to use it.

**Before entering plan mode:** if you haven't already brainstormed, invoke the brainstorming skill first.

Then announce "Using [skill] to [purpose]" and follow the skill exactly. If it has a checklist, create a todo per item.

## Skill Priority

When multiple skills apply, process skills come first — they set the approach, then implementation skills (frontend-design, etc.) carry it out. Brainstorming and systematic-debugging are Superpowers' most common process skills, but the rule holds for any of them.

- "Let's build X" → d3nexus:brainstorming first, then implementation skills.
- "Fix this bug" → d3nexus:systematic-debugging first, then domain skills.

## Red Flags

These thoughts mean STOP—you're rationalizing:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can check git/files quickly" | Files lack conversation context. Check for skills. |
| "Let me gather information first" | Skills tell you HOW to gather information. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. |
| "This doesn't count as a task" | Action = task. Check for skills. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This feels productive" | Undisciplined action wastes time. Skills prevent this. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## Platform Adaptation

This kit targets **Claude Code** (the default these skills are written against), **Antigravity**,
and **Codex**. On Antigravity, read [`references/antigravity-tools.md`](references/antigravity-tools.md).
On Codex, read [`references/codex-tools.md`](references/codex-tools.md). These references map the
actions described in the skills to the tools available in each runtime.

## User Instructions

User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, etc, direct requests) take precedence over skills, which in turn override default behavior. Only skip skill workflows or instructions when your human partner has explicitly told you to.
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

3. **Triage Findings, Top 3 Highest-Risk Report & Auto-Triage Gate**:
   - Read and follow [document-triage.md](references/document-triage.md) (Source-of-Truth Hierarchy: Forward Alignment over Legacy Reversion, Top 3 Highest-Risk Findings Report, and Auto-Triage Gate).
   - Inspect `## Auto-Triage Gate` from `run_external_review.py triage --kind principal --epic-dir <epic_dir>`:
     - **`AUTO_PASS_CLEAN` / `AUTO_PASS_FINAL_MINOR_SWEEP` / `AUTO_PASS_FINAL_SWEEP` (Round 3 with `0 Critical`)**: Verify all findings against source code and the approved Spec/HLD first (halting only on `CRITICAL_CONFLICT`, `Debatable` trade-offs, `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, or `MAX_ROUNDS_CRITICAL_REMAINING`). Apply any valid final sweep revisions and decision commits, then run final packaging (`package_epic.py <epic_dir>`, or `--revise --reason "Revise after Principal Review"` if `handoff.md` already exists), commit `[<EPIC_NAME>] Package epic for handoff`, save state (`--state`), **print `--emit-prompt implement`**, and (in interactive mode) prompt **Triển khai (tự động)** vs **Dừng lại** without calling another review round.
     - **`AUTO_FIX_ELIGIBLE` (Round 1..2 with `Critical`/`Important`, no `shared-contracts/` conflict, no Fix Loop)**: Verify every finding against live source code and the approved Spec/HLD (`Decisions Already Made`), and emit the triage summary header block (`## Auto-Triage Gate`, `## Top 3 Highest-Risk Findings`, `## Findings`). In **BOTH Autonomous (`lifecycle_runner.py`) and Interactive Mode**, when all blocking findings verify as `Valid` (plus any objective `False positive` refuted with exact source/approved-Spec proof) and zero halt triggers apply, **do NOT pause for confirmation**: automatically apply document revisions in Role 2.2, record decisions (`fixed in <sha>` / verified evidence), verify readiness (`check_epic_readiness.py <epic_dir>`, without premature `handoff.md` packaging), and immediately advance to Round $N+1$. Stop calling tools and escalate to the Human Architect **ONLY** on **`CRITICAL_CONFLICT`** (business/domain requirement, critical risk, or Tier-1 Spec intent conflict — in autonomous mode `lifecycle_runner.py` transitions to `AWAITING_PRINCIPAL_CONFIRMATION` and writes `.devtool/epic/<epic_dir>/principal_fix_proposal_round<N>.md`), a **`Debatable`** finding requiring a trade-off choice, **`SHARED_CONTRACT_CONFLICT`**, **`FIX_LOOP`**, or **`MAX_ROUNDS_CRITICAL_REMAINING`** (triage header block format):
       ```markdown
       Principal Review Triage: Round <N> (<CLI>)
       *(or `Principal Review Triage: <doc_path> (<CLI>)`)*

       • Candidate SHA: <commit_sha>
       • Reviewer: <CLI> ( <model> )
       • Thinking Level: <Light | Low | Medium | High | Extra High | None>
       • Verdict: <VERDICT> (<count> <Severity> findings)
       ```
     - **`CIRCUIT_BREAKER_HALT` (`SHARED_CONTRACT_CONFLICT` in any round, `FIX_LOOP`, or `MAX_ROUNDS_CRITICAL_REMAINING` when `>= 1 Critical` survives Round 3)**: **STOP IMMEDIATELY**, never auto-fix or revert the user-approved HLD design, and report `## Top 3 Highest-Risk Findings (Executive Report)` to the Human Architect.

4. **Revision Loop, Convergence & Post-Review Packaging (`package_epic.py` + `/save-context`)**:
   - **Intermediate rounds (when advancing to Round `n+1`)**: apply document edits and record decisions without running `package_epic.py` mid-loop:
     - Apply document edits first and commit:
       `git commit -m "[<EPIC_NAME>] Revise epic after Principal Review round <n>"`
     - Record decisions with revision commit SHA in `principal_review.md`, then commit:
       `git commit -m "[<EPIC_NAME>] Record Principal Review decisions for round <n>"`
     - Verify `python3 skills/dev-implementation/resources/scripts/check_epic_readiness.py <epic_dir>` exits 0 and automatically advance to Round `n+1`.
   - **At completion of `/principal-review` (after convergence `AUTO_PASS_CLEAN`, `AUTO_PASS_FINAL_MINOR_SWEEP`, or `AUTO_PASS_FINAL_SWEEP` and any final sweep commits)**:
     - Execute packaging now: `python3 skills/dev-implementation/resources/scripts/package_epic.py <epic_dir>` (pass `--revise --reason "Revise after Principal Review round <n>"` only if `handoff.md` already exists) and commit `[<EPIC_NAME>] Package epic for handoff` if `auto_commit: true`.
     - Record Gate 2 approval (if revised) via `python3 scripts/resume_context.py --gate 2 --epic <epic_slug> --approved "Passed Principal Review round <n> and packaged"`.
     - Record state via `python3 scripts/resume_context.py --state --epic <epic_slug> --status "Stage 2: Packaged & Ready"`, and **print the AI Programmer implementation prompt** (`python3 scripts/resume_context.py --emit-prompt implement --epic <epic_slug>` + `handoff.md` path).
     - In autonomous lifecycle mode (`lifecycle_runner.py`), transition directly to Role 2.3 (AI Programmer, Model Gemini Flash 3.8) and invoke `d3nexus:dev-implementation`. In interactive mode, stop calling tools and ask **Triển khai (tự động)** vs **Dừng lại** (*"Dừng lại ở đây để tôi lấy prompt cho một AI Agents khác triển khai"*): invoke `d3nexus:dev-implementation` automatically if **Triển khai (tự động)**, or stop cleanly if **Dừng lại**.

## Guidelines & Reference Documents

Read these on demand, not up front. `run_external_review.py` loads the prompt template and review rules itself, so do not open them to run a review.

- [Prompt Template](references/principal-review-prompt.md): The read-only instruction template sent to reviewer CLIs (script-consumed; do not read).
- [Review Rules](references/principal-review-rules.md): Severity definitions (Critical, Important, Minor) and source grounding standards (script-consumed; do not read).
- [Document Triage Protocol](references/document-triage.md): Step-by-step decision verification and revision loop enforcement (read at step 3 only).
- [Verification Row Grammar](../dev-designer/references/verification-row-grammar.md) (read only when a finding concerns Verification rows): Canonical Verification table grammar rules (including `\|` pipe escaping, `env VAR=val` prefixing, slash-containing search pattern rules, and portable CLI usage). Escaped pipes `\|` in table command cells are unescaped by `task_contract.py` and must not be flagged as syntax errors.

exec
/bin/zsh -lc "rg -n 'token_throttling|principal|review' /Users/danhdueexoictif/antigravity_homes/duvthinh403/.codex/memories/MEMORY.md" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
1:# Task Group: ai-agent-tools setup_shared_contracts principal contract review
3:scope: Read-only, source-grounded architectural review of the Hub/Satellite shared-contract setup epic; use before implementation or when reconciling design, BDD, task, HLD, and verification contracts.
4:applies_to: cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools; reuse_rule=reinspect the candidate commit and all current epic artefacts; review findings are commit-specific, while the cross-contract comparison procedure is reusable.
10:- rollout_summaries/2026-10-30T06-59-12-Elg4-principal_review_setup_shared_contracts_contract_drift.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/30/rollout-2026-10-30T13-59-12-01a18b9a-faa7-7f50-81b9-b3c8aa8e3a08.jsonl, updated_at=2026-10-29T23:08:05+00:00, thread_id=01a18b9a-faa7-7f50-81b9-b3c8aa8e3a08, `CHANGES REQUIRED`; later review verified these four findings were fixed)
14:- setup_shared_contracts, principal-review, shared_contracts_readme.md.tmpl, string.Template, `{{DOMAIN_NAME}}`, --root, --repo-root, --satellite-root, scripts/verify.sh, Section 11, Section 14, contract drift
16:## Task 2: Re-review setup_shared_contracts after corrections, partial
20:- rollout_summaries/2026-10-30T06-59-12-zvna-principal_review_setup_shared_contracts_contract_contradicti.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/30/rollout-2026-10-30T13-59-12-01a18b9a-faa8-72e0-8192-3dd403258730.jsonl, updated_at=2026-10-29T23:26:36+00:00, thread_id=01a18b9a-faa8-72e0-8192-3dd403258730, `CHANGES REQUIRED`; current implementation-blocking finding)
24:- setup_shared_contracts, principal-review, SSC-FR-03, shared-contracts, non-empty, symlink, Rule 7, `Covers:`, traceability, `python3 -m unittest`, CHANGES REQUIRED
28:- When requesting a principal review, the user required a “strictly read-only review” with exact source file/line grounding, artefact-specific actionable findings, and an exact final verdict block -> do not edit files or Git state; cite concrete locations for each source claim. [Task 1][Task 2]
32:- Related skill: skills/principal-contract-review/SKILL.md. [Task 1][Task 2]
33:- Treat frozen design/task differences as public implementation contracts, not harmless wording: template filenames/substitution syntax and CLI root flags must agree before an executor starts. In the first review, Mustache `{{DOMAIN_NAME}}` templates conflicted with Python `string.Template` `$domain`/`$hub_repo`/`$timestamp`, which would leave placeholders unresolved; `--root`, `--repo-root`, and `--satellite-root` likewise needed a single contract. The later review verified those findings were fixed. [Task 1][Task 2]
34:- Check requested `scripts/verify.sh` integration against the surrounding responsibility, not its stated number. Section 11 was lifecycle/document tooling; with Sections 1–13 present, a dedicated Section 14 was the valid shared-contract test location, and the later review verified the wiring correction. [Task 1][Task 2]
44:# Task Group: D3Nexus Apple Music media-controller epic corrective review and Stage 2 handoff
46:scope: Code-anchored correction of `preview_apple_music_media_controller` design, task, BDD, and handoff contracts; use before any Gate 2 approval or Stage 3 work on the floating player dock.
49:## Task 1: Review and correct `preview_apple_music_media_controller` package, partial
53:- rollout_summaries/2026-10-22T06-06-56-3JSJ-review_correct_apple_music_media_controller_epic.md (cwd=/Users/danhdueexoictif/AllProjects/D3Nexus, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/22/rollout-2026-10-22T13-06-56-01a16238-406a-7931-a84f-337a4f51cf7d.jsonl, updated_at=2026-10-22T06:34:27+00:00, thread_id=01a16238-406a-7931-a84f-337a4f51cf7d, corrective Stage 2 draft; final bilingual validation not fully evidenced)
57:- preview_apple_music_media_controller, handoff.md, Gate 2, check_bdd_traceability.py, check_task_contract.py, compute_execution_order.py, check_document.py, Playwright, floating-dock.ts, SettingsPopover.astro, AMC-AT-01, canonical selectors
61:- When reviewing an epic, the user asked for the design spec, epic overview, BDD, handoff, and source code, especially `handoff.md` -> inspect the complete lifecycle artifact set and verify status claims against actual production symbols rather than trusting packaged status. [Task 1]
62:- The review stopped at documentation/Gate approval; do not implement code or enter Gate 3 without explicit approval. [Task 1]
66:- Correct execution order is `550 -> 549/551 -> 552 -> 553 -> 554`; `compute_execution_order.py preview_apple_music_media_controller` derives it when the dependencies are present. [Task 1]
81:applies_to: cwd=/Users/danhdueexoictif/AllProjects/lyrics-sync; reuse_rule=reinspect current preview/UI/API/CLI defaults and source classification before changing behavior; this is analysis/policy, not an implemented production change.
100:- Align Studio UI/API/job defaults are `split_sentences=true`, `resegment_llm=true`, and `normalize_llm=false`; `lyrics-sync align` CLI instead defaults `resegment_llm=false`. The expensive default therefore belongs chiefly to the Studio preview flow. [Task 1]
109:- Do not conflate CLI defaults with Align Studio defaults: inspect `cli.py`, preview API, preview jobs, and browser request construction separately. [Task 1]
153:- Do not claim the amendment implemented: this rollout changed only bilingual design documents; `dev-designer/SKILL.md`, `handoff-template.md`, and anti-drift tests were not changed, and no amendment commit/user review is evidenced. [Task 2]
174:- rollout_summaries/2026-10-18T19-19-37-2Uj4-playlist_playback_queue_epic_corrective_review_and_handoff.md (cwd=/Users/danhdueexoictif/AllProjects/D3Nexus, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/19/rollout-2026-10-19T02-19-37-01a15074-8aa0-7c01-8a6e-51fda3dbcf0e.jsonl, updated_at=2026-10-18T19:42:47+00:00, thread_id=01a15074-8aa0-7c01-8a6e-51fda3dbcf0e, package/handoff validated; no implementation)
203:# Task Group: ai-agent-tools Gate 4 Review Choice loop and external-review diagnostics
205:scope: Verified lifecycle state-machine update and streamed external-review precondition reporting.
212:- rollout_summaries/2026-10-18T10-39-52-b3XU-gate4_review_choice_loop_and_external_review_streaming.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/18/rollout-2026-10-18T17-39-52-01a14e98-b2b9-7043-9d17-65dd8df4be46.jsonl, updated_at=2026-10-18T15:23:36+00:00, thread_id=01a14e98-b2b9-7043-9d17-65dd8df4be46, committed and fully verified)
216:- Gate 4, Review Choice, Cross-model review, Gate 5, SHA-bound, rules/CRITICAL_RULES.md, test_verifiable_handoff_text.py, df9f67af7c1f7fecd3b4a9768c0863d035ed3088
218:## Task 2: Add realtime ANSI pre-check output to external review, success
222:- rollout_summaries/2026-10-18T10-39-52-b3XU-gate4_review_choice_loop_and_external_review_streaming.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/18/rollout-2026-10-18T17-39-52-01a14e98-b2b9-7043-9d17-65dd8df4be46.jsonl, updated_at=2026-10-18T15:23:36+00:00, thread_id=01a14e98-b2b9-7043-9d17-65dd8df4be46, 31 targeted tests and full verification passed)
226:- run_external_review.py, run_gate, PreconditionFailedError, [PRECONDITION BLOCKED], ANSI, flush=True, audit_epic.py, check_bdd_traceability.py, scripts/verify.sh, android-ui-audit
230:- The user explicitly corrected the lifecycle sequence: “Gate 4 => Review Choice”, then “Finish” or “Cross model review”, and “Sau bước này chạy lại Gate 4 ... Loop cho tới khi finish.” -> preserve this order for similar ai-agent-tools lifecycle work. [Task 1]
235:- Enforced invariant: `Gate 4 PASS -> Review Choice; Finish -> Gate 5; Cross-model review -> Gate 4 in full`. A review round, decision, Fix commit, Gate 5-requested change, cross-model CLI failure, or timeout that changes/reassesses the candidate requires full Gate 4 before another Review Choice. Gate 4 is SHA-bound. [Task 1]
236:- The policy update touched `rules/CRITICAL_RULES.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-implementation/SKILL.md`, bilingual lifecycle docs, lifecycle-selection docs, and `scripts/test_verifiable_handoff_text.py`; commit `df9f67af7c1f7fecd3b4a9768c0863d035ed3088` is `[REVIEW_WORKFLOW] Loop review choice through Gate 4`. [Task 1]
238:- Route `audit_epic.py`, declared Integration commands, and `check_bdd_traceability.py` through `run_gate()` while retaining captured output in the facts bundle. `run_external_review.py` does not directly invoke `android-ui-audit`; that is only indirect through the quality-provider registry. Targeted suite passed 31 tests and `scripts/verify.sh` reported `PASS — safe to publish`; worktree was clean on `main`, with no push. [Task 2]
291:- Canonical public route is `/s/f/<opaque_share_id>` and only `Ready` snapshots are public. Continue internally with `/app/tracks/<slug>?line=<line>&t=<start_ms>&occurrence=<id>#preview`; preserve timestamp precedence and no autoplay. `apps/learning-web/src/core/navigation/url-params.ts` already parses `slug`, `line`, `t`, `colloc`, and preview hash. [Task 1]
292:- Public snapshots must be sanitized, immutable, owner-scoped internally, and independent of later source edits. Static Astro/client-only metadata cannot support social crawlers; use a server public projection/SSR and deterministic revisioned 1200x630 OG image. Social clients control their own preview UI. [Task 1]
293:- D3Nexus owns backend, Astro web, public snapshot API, SSR/OG, web UX, and shared HTTPS/OpenAPI contract. `/Users/danhdueexoictif/AllProjects/nexus` owns Flutter/mobile UI, native sharing, Universal Links/App Links, recipient preview, and mobile fallback. Mobile specs remain in D3Nexus at `docs/superpowers/specs/2026-10-18-contextual-flashcard-sharing-mobile-design.en.md` and `.vi.md` (`b130026`). [Task 2]
319:- learning_core, FSRS-6, fsrs-6.6.2, desired retention 0.85, lexical_items, phrase_occurrences, review_log, card_state, Rust/WASM, Flutter FFI, review-room.ts
333:- For a conceptual FSRS review/adoption, the user approved continuation only after the announced verification/package plan (“Tiếp tục”) -> preserve explicit action boundaries and do not silently expand into implementation. [Task 1][Task 2]
338:- `learning_core` is the pure Rust FSRS-6 authority (`fsrs` 6.6.2, desired retention 0.85): grading, scheduling, deterministic replay, snapshot decisions, retrievability, and due queries. It does not own catalogue storage, UI, IndexedDB, HTTP, outbox, or screen state. Immutable review logs are truth; snapshots are derived/versioned; bindings are Flutter FFI and WASM. [Task 1]
339:- Catalogue entities remain catalogue-owned: `lexical_items`, `phrase_occurrences`, lyrics context/media. Use a learner-owned integration layer with stable schedule identity, immutable review logs, derived card state, sync, and reconciliation; do not add learner scheduling to catalogue rows. [Task 1]
340:- Replace unsafe web fallbacks before implementation: `apps/learning-web/src/wasm/learning-core.ts` had heuristic TypeScript scheduling, `review-room.ts` started from sample/in-memory cards, and live IDs were phrase-derived. Rust/WASM must be the authority. Avoid old guides that mix FSRS-7 with unpublished APIs. [Task 1]
349:# Task Group: D3Nexus design_system Gate 4 evidence review and lifecycle concurrency
351:scope: Gate 4 review of a web-heavy epic: evidence completeness, fail-closed verdicts, stable-SHA reruns, and lifecycle race protection.
358:- rollout_summaries/2026-10-16T05-48-38-Pr6V-design_system_gate_4_review_fail.md (cwd=/Users/danhdueexoictif/AllProjects/D3Nexus, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/16/rollout-2026-10-16T12-48-38-01a14341-57f0-7ad0-b345-c5f06b4cce11.jsonl, updated_at=2026-10-16T06:10:35+00:00, thread_id=01a14341-57f0-7ad0-b345-c5f06b4cce11, validated FAIL report; review report remains uncommitted)
366:- When reviewing an epic, the user asked for a thorough review of the design spec, epic overview, handoff, and related tasks, with the result file inside the epic directory -> inspect the full lifecycle artifact set and put the durable review report at the requested in-place path. [Task 1]
372:- On stable merge SHA `89358cb11e24186eeac307f055124c2a58b1b46e`, format, provider-check, clippy, Rust tests, coverage, architecture, deny, WASM, FFI, docs, and DB hygiene passed; acceptance failed at `apps/server/tests/catalog_taxonomy_search_test.rs:772`: `p95 latency 153 ms exceeded 150 ms budget for three_facets_keyword`. The review also verified 58/58 BDD coverage, 794/794 independent web tests, 15 Astro pages, and 700 docs. [Task 1]
483:- Initial review found unresolved `podcast`/`interview`, `movie_tv`/`conversation`, and `lecture`/`speech` overlap -> provide explicit boundaries and precedence before approving a taxonomy reference. [Task 1]
501:- 10 use cases/21 BDD scenarios; missing realtime popovers, context navigation, editorial editing, edge cases. Split: preview_flashcards, vocabulary_catalog, vocabulary_studio, flashcard_audio_delivery. Audit/reuse Task 116/current components first. [Task 1]
502:- Flow: user upload -> OCR job -> draft candidates -> review/edit -> committed flashcards -> TTS/audio. IDs alone must not grant access; public/catalog is explicit transition. [Task 1]
503:- Screenshot parity needs exact summary, 3-column/equal-height/footer grid, density, 3->2->1 breakpoints and screenshot regression; add PF-D1.5 Preview Flashcards Grid Visual Parity. [Task 1]
507:# Task Group: D3Nexus learning-web lyrics preview parity and media-clock repair
509:scope: Audit and partial repair of lyrics preview parity, media clocks, and browser verification; not merge-ready evidence.
510:applies_to: cwd=/Users/danhdueexoictif/AllProjects/D3Nexus including .worktrees/lyrics_preview_parity and .worktrees/lyrics_preview_repair; reuse_rule=re-check worktree/runtime/browser state.
512:## Task 1: Audit preview parity and repair runtime/media clocks, partial
514:- rollout_summaries/2026-10-12T17-38-20-pzMb-lyrics_preview_parity_audit_and_runtime_repair.md (cwd=/Users/danhdueexoictif/AllProjects/D3Nexus, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/13/rollout-2026-10-13T00-38-21-01a13131-aabd-7152-beff-ea7c98bb263f.jsonl, updated_at=2026-10-13T05:04:30+00:00, thread_id=01a13131-aabd-7152-beff-ea7c98bb263f, 10 targeted tests passed; Playwright partial)
516:- lyrics_preview_parity, PreviewSession, DualMasterPlayerClock, /api/v1/lyrics/:slug, port 8686, projectTimeline, youtube-sdk.ts, #line-l2, Playwright
518:- Compare design/HLD/BDD, current code, two concrete preview URLs, and sibling lyrics-sync; provide gap analysis/staged plan before edits. [Task 1]
521:- PreviewSession waits for track/media; projectTimeline applies offset once; DualMasterPlayerClock syncs every second/preserves promotion state/safe no-op. YouTube SDK needs timeout, abort and cleanup. [Task 1]
528:scope: Provider quality orchestration review and documentation-only Stage 2 closure.
533:- rollout_summaries/2026-10-11T06-07-53-ad3F-rust_quality_provider_stage2_closure_review.md (cwd=/Users/danhdueexoictif/AllProjects/D3Nexus, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/11/rollout-2026-10-11T13-07-53-01a12993-2b6d-79e2-84b4-b9af3dcbf627.jsonl, updated_at=2026-10-12T01:28:17+00:00, thread_id=01a12993-2b6d-79e2-84b4-b9af3dcbf627, docs validated; commit not evidenced)
564:# Task Group: lyrics-sync Preview Studio keyboard shortcuts and acceptance
567:applies_to: cwd=/Users/danhdueexoictif/AllProjects/lyrics-sync and .worktrees/preview_keyboard_shortcuts; reuse_rule=recheck overlap/environment.
571:- rollout_summaries/2026-10-09T09-50-56-CTSe-preview_keyboard_shortcuts_task4_acceptance.md (cwd=/Users/danhdueexoictif/AllProjects/lyrics-sync/.worktrees/preview_keyboard_shortcuts, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/09/rollout-2026-10-09T16-50-56-01a12012-aa8f-7af0-b4f7-ea7f130c511e.jsonl, updated_at=2026-10-09T16:10:45+00:00, thread_id=01a12012-aa8f-7af0-b4f7-ea7f130c511e, Task 4 complete)
572:- rollout_summaries/2026-10-09T09-41-49-gwDf-preview_keyboard_shortcuts_gate2_planning.md (cwd=/Users/danhdueexoictif/AllProjects/lyrics-sync, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/09/rollout-2026-10-09T16-41-49-01a1200a-521a-7831-9fab-8530a32bdd11.jsonl, updated_at=2026-10-09T10:51:16+00:00, thread_id=01a1200a-521a-7831-9fab-8530a32bdd11, design/handoff)
574:- preview_keyboard_shortcuts, event.code, Audio-master, YouTube-master, getGapState().lineIndex, HTTP 206, R2, 24 PASS
578:- Space play/pause; W/Up previous; S/Down next; A/Left slower; D/Right faster; R/F replay; L loop; Shift Left/Right ±5s. event.code, ignore modifiers/repeat/editables; Preview-only; Audio/YouTube. [Task 1]
581:- Do not trust JS impact tool 0%; run node --test tests/js/**/*.test.mjs. scripts/check.sh has 41 pre-existing Ruff findings; review app.js rebase conflicts/preserve unrelated Kanban. [Task 1]
590:- rollout_summaries/2026-10-09T09-41-49-kWY2-studio_llm_token_vision_deepseek_ocr_epic_review.md (cwd=/Users/danhdueexoictif/AllProjects/lyrics-sync, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/09/rollout-2026-10-09T16-41-49-01a1200a-5221-7441-98a8-46c955baaee2.jsonl, updated_at=2026-10-08T19:55:52+00:00, thread_id=01a1200a-5221-7441-98a8-46c955baaee2, measured OCR/spec r3)
618:- Never persist local fallback/open Drawer after R2 failure; no normal Sync R2/skip re-extraction; keep FastAPI/stdlib preview parity. [Task 1]
629:- FSRS, learning_core, review_log, card_state, ADR-007, Rust, WASM, Flutter, SQLite WASM/OPFS, Mac mini

exec
/bin/zsh -lc 'pwd; git status --short; git rev-parse HEAD; cat rules/CRITICAL_RULES.md rules/coding-guidelines.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 3793ms:
/Users/danhdueexoictif/AllProjects/ai-agent-tools
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-25X6LXFN' (errno=Operation not permitted)
2026-11-13 02:43:34.191 xcodebuild[69578:24686030]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-13 02:43:34.466 xcodebuild[69578:24686029] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-GQ5OB645' (errno=Operation not permitted)
2026-11-13 02:43:34.984 xcodebuild[69629:24686654]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-13 02:43:35.096 xcodebuild[69629:24686653] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-4BpAO8nC' (errno=Operation not permitted)
2026-11-13 02:43:36.065 xcodebuild[69643:24686838]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-13 02:43:36.210 xcodebuild[69643:24686811] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-BiRf6C7v' (errno=Operation not permitted)
2026-11-13 02:43:36.621 xcodebuild[69676:24687272]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-13 02:43:36.744 xcodebuild[69676:24687271] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
8d456f6ec6f420e17932c67c8425a563ac3913ee
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

## 5. Automated Execution, Mandatory Cross-Model Review & Stage 4 Finish Gate

> [!CRITICAL]
> **Streamlined Autonomous Execution & Zero Intermediate Confirmation Pauses:**
> To eliminate unnecessary manual friction, AI Agents across all platforms MUST adhere to the following automated execution and review pipeline:
>
> 1. **Stage 2 -> `/principal-review` Transition, Gate 2 Unified Confirmation (AUTO MODE) & Automated Execution Pipeline**:
>    - **Gate 2 Unified Confirmation Checkpoint (Tasks, Reviews & AUTO MODE)**: Once Gate 2 passes and readiness checks (`check_epic_readiness.py`) succeed, the AI Agent MUST **NOT** run `package_epic.py` yet. Record Gate 2 (`resume_context.py --gate 2`), save state (`Stage 2: Ready for Principal Review`), read `.devtool/review_config.json`, stop calling tools, and present the unified Gate 2 Choice with reviewer **provider/model priority** (`Claude -> Codex -> Kiro -> Argon` for `/principal-review` and `/cross-model-review`):
>      - **Option 1: (Recommended) Phê duyệt & Chạy AUTO MODE xuyên suốt (Triển khai (tự động))**: Automatically runs `/principal-review` -> packages `handoff.md` (`package_epic.py`) -> bootstraps Gate 3 -> executes tasks via `dev-implementation` (2-Slot Ephemeral Worker Pool) -> runs Gate 4 -> runs `/cross-model-review` (using confirmed provider priority). The agent MUST NOT pause for intermediate confirmations, halting strictly ONLY on the 5 Circuit Breakers or at Gate 5 Finish/Merge.
>      - **Option 2: Phê duyệt & Handoff Mode (Dừng lại)**: Runs `/principal-review` -> packages `handoff.md` -> emits `--emit-prompt implement` -> halts cleanly so the developer can assign the prompt to another profile.
>    - **Automated Gate 3 & 2-Slot Ephemeral Worktree Bootstrap**: When AUTO MODE / Triển khai (tự động) is selected, the AI Agent computes execution order via `compute_execution_order.py --parallel`, initializes slots with shared cache via `manage_worker_pool.py`, records Gate 3 (`resume_context.py --gate 3`), and invokes Role 2.3 (AI Programmer as Orchestrator) without manual confirmation. Manual halt occurs ONLY on fatal errors (cyclic DAG dependency, malformed task frontmatter, or unresolvable blocking prerequisites).
>
> 2. **Automated Transition to Cross-Model Review (No Intermediate Review Choice Prompt)**:
>    - When all tasks of an epic are implemented and Phase 4 / Gate 4 local machine verification returns PASS (after Gate 4 passes, Cross-model review must return to a full Gate 4 run), the AI Agent **MUST NOT pause to ask the developer for an intermediate Review Choice** (e.g. Finish vs Cross-model review).
>    - The workflow **AUTOMATICALLY transitions into `/cross-model-review`** using the provider priority and model configured in `.devtool/review_config.json` (running `run_external_review.py run --epic-dir <epic_dir> --auto-quota`).
>    - Cross-model review executes its 3-round convergence funnel and severity-tiered auto-triage gate (`AUTO_PASS_CLEAN`, `AUTO_PASS_FINAL_MINOR_SWEEP`, `AUTO_FIX_ELIGIBLE`) automatically, enforcing **scoped tests only** during intermediate fix rounds and reserving full Gate 4 machine acceptance strictly for final convergence.
>
> 3. **Stage 4 Finish Decision & Gate 5 Sign-off (Human Decision Point)**:
>    - The decision to "Finish" belongs strictly to **Stage 4 (`finishing-a-development-branch`)**.
>    - Only after `/cross-model-review` has converged, all findings are resolved, Gate 4 PASS is re-verified on the latest candidate SHA, and the synthesized Executive Report (Top 3 Highest-Risk Findings across all review rounds) is rendered, the AI Agent **MUST explicitly stop calling tools** and prompt the Human Architect for the **Stage 4 Finish Decision** (Gate 5 Sign-off) and Git merge strategy selection (`Squash`, `--no-ff`, or `Rebase`).
>    - The AI Agent **MUST NOT** auto-finish, auto-merge, or auto-push to remote without explicit developer confirmation.

## 6. Severity-Tiered Auto-Triage Gate, 3-Round Convergence Funnel & Post-Gate Checkpoints

> [!CRITICAL]
> **Every external review invocation (`/principal-review` and `/cross-model-review`) enforces the 3-Round Scope-Narrowing Convergence Funnel (`max_rounds = 3`), `check-quota` Provider Priority (`Claude -> Codex -> Kiro -> Argon`), and the Severity-Tiered Auto-Triage Gate.**
>
> 1. **Quota-Aware Provider Priority & 3-Round Convergence Funnel**:
>    - **Provider Priority (`Claude -> Codex -> Kiro -> Argon`)**: Evaluations follow `["claude", "codex", "kiro", "agy"]` using `check-quota` thresholds: Claude & Codex require `5H >= 15%` AND `7D > 2%`; Kiro requires `Monthly Credits >= 3%` (`>= 15 credits`); Argon (`agy`) requires `Weekly >= 10%` or `5H >= 15%`.
>    - **Max 3 Rounds**: Reviews are capped at `3` rounds (`Round 1`: Full Scope Audit; `Round 2`: Delta Verification of `prev_sha..curr_sha` with no new Minor on untouched files; `Round 3`: Blocker-Only Convergence Mode).
> 2. **Severity-Tiered Auto-Triage Gate & Automatic Local Quality Gate Re-run**:
>    - **`AUTO_PASS_CLEAN` (`0 findings`)** or **`AUTO_PASS_FINAL_MINOR_SWEEP` (`0 Critical`, `0 Important`, only `Minor` findings)**: Verify findings against live source and approved Spec/HLD first (halting only on `CRITICAL_CONFLICT`, `Debatable` trade-off choices, or `CIRCUIT_BREAKER_HALT`). Otherwise, fix valid `Minor` items in a single sweep (commit revisions + decisions), verify the local quality gate (`check_epic_readiness.py` + `package_epic.py` [or `--revise` when `handoff.md` already exists] at completion of Stage 2 `/principal-review`; full Gate 4 in Stage 3), and **complete the review stage immediately without re-invoking the external reviewer**. At the end of Stage 2 `/principal-review`, print `--emit-prompt implement` and ask **Triển khai (tự động)** vs **Dừng lại**.
>    - **`AUTO_FIX_ELIGIBLE` (Round 1..2 with `Critical`/`Important` findings and no Fix Loop)**:
>      - In **Stage 2 `/principal-review` (BOTH Interactive Mode and Autonomous `/dev-lifecycle` Mode)**: The agent MUST first run `run_external_review.py triage --kind principal --epic-dir <epic_dir>` and verify every finding against live source code and the approved Spec/HLD (`Decisions Already Made`) BEFORE editing any document. Present the verified triage summary (`## Auto-Triage Gate`, `## Top 3 Highest-Risk Findings`, `## Findings`), and **when all blocking findings verify as `Valid` (plus any objective `False positive` refuted with exact source/approved-Spec proof) and zero halt triggers apply, do NOT pause for interactive confirmation**: automatically apply the design revisions in Role 2.2, commit revisions and decisions (`fixed in <sha>`), verify `check_epic_readiness.py <epic_dir>` (scoped readiness check, without premature `handoff.md` packaging or code tests), and immediately advance to Round `N+1` (up to max 3 rounds). **Stop calling tools and escalate to the Human Architect ONLY when hitting**: (1) `CRITICAL_CONFLICT` (conflict with business/domain requirements, critical risks, or frozen Tier-1 Spec/`Decisions Already Made`), (2) a `Debatable` finding requiring a trade-off choice (or an unresolvable `Not shown` claim), (3) `CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)`, (4) `CIRCUIT_BREAKER_HALT (FIX_LOOP)`, or (5) `CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)`. Only after `/principal-review` converges does Stage 2 execute `package_epic.py`, print `--emit-prompt implement`, and ask **Triển khai (tự động)** vs **Dừng lại**.
>      - In **Stage 3 `/cross-model-review` — Autonomous `/dev-lifecycle` Mode**: When all blocking findings verify as `Valid` in source code and do not require unapproved changes to `shared-contracts/`, Role 2.3 drafts `fix_plan_round<N>.md` evaluated by Role 2.2 (`APPROVED`, `ADJUSTED`, `CRITICAL_CONFLICT`), applies the fixes, commits them, records decisions, runs **scoped tests only** (fast static/architecture checks and targeted unit tests covering modified modules; repo-wide pytest and Playwright E2E suites forbidden), and invokes the next convergence round (`Round N+1`, up to max 3 rounds). Full Gate 4 is reserved strictly for the Final Convergence Gate. If `CRITICAL_CONFLICT` or `SHARED_CONTRACT_CONFLICT` is detected, halt immediately for the Human Architect.
>      - In **Stage 3 `/cross-model-review` — Interactive Mode** (or whenever any Stage 3 finding is `Debatable` / `False Positive` or hits a Halt Trigger): The agent **MUST STOP CALLING TOOLS** after presenting the verified triage table (`run_external_review.py triage`) and wait for explicit developer confirmation on the findings. Once confirmed, Role 2.3 applies the fixes, commits them, runs **scoped tests only** without asking for an intermediate confirmation, and returns to the cross-model review loop. Only at final convergence does full Gate 4 run.
>    - **`CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)` (Mandatory Immediate Stop on `shared-contracts/` Conflicts)**:
>      - If ANY `Critical` or `Important` finding in `/principal-review` or `/cross-model-review` directly impacts or conflicts with `shared-contracts/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`, `contract_sync.json`, or wire-level step/enum/payload contracts — e.g. HLD defines 5 new steps while `shared-contracts/` still holds 7 legacy steps), the AI Agent **MUST IMMEDIATELY STOP CALLING TOOLS AND REPORT TO THE DEVELOPER**.
>      - The AI Agent is **STRICTLY PROHIBITED** from auto-fixing `shared-contracts/` conflicts, **STRICTLY PROHIBITED** from proposing or applying a revert of the user's approved HLD/Spec design back to legacy contract steps, and **STRICTLY PROHIBITED** from continuing autonomous execution until the Human Architect explicitly confirms the contract alignment decision.
>    - **`CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)` & `CIRCUIT_BREAKER_HALT (FIX_LOOP)`**:
>      - If after **3 review rounds (`Round >= 3`) any `Critical` finding still remains**, OR if a **Fix Loop** occurs (the same file marked `fixed in <sha>` in Round $N-1$ is re-reported with a `Critical`/`Important` finding in Round $N$), the AI Agent **MUST IMMEDIATELY STOP CALLING TOOLS**, present the `## Top 3 Highest-Risk Findings (Executive Report)` and triage table, and escalate to the Human Architect (never auto-continue to implementation or branch finishing when a `Critical` finding survives 3 rounds).
>      - Conversely, if Round 3 finishes with **`0 Critical` findings** (and no `shared-contracts/` conflict or Fix Loop, only remaining `Important`/`Minor` findings), `AUTO_PASS_FINAL_SWEEP` applies one final fix pass anchored to the approved design, runs the local quality gate green, and completes the stage without invoking a 4th review round.
>
> 3. **Remediation Loop & Test Execution Protocol (Hard Constraints)**:
>    - To prevent multi-minute test hangs, token waste, and incomplete/evasive fixes during review-remediation cycles, both Orchestrator and Fixer/Implementer agents MUST strictly obey:
>    - **Scoped Tests Only During Intermediate Fix Rounds (Round 1, Round 2...)**:
>      - While fixing findings in intermediate rounds, run **ONLY** fast static/architecture checks (`ruff`, `mypy`, `lint-imports`, AST invariants) and **explicitly targeted test files** that directly cover the modified modules: `uv run pytest <explicit_test_file_1.py> <explicit_test_file_2.py>`. In Stage 2, run `check_epic_readiness.py <epic_dir>`.
>      - **STRICTLY FORBIDDEN IN INTERMEDIATE ROUNDS**: Do NOT run repo-wide `pytest` discoveries (even with `-m "not slow..."`), do NOT run `tests/e2e/` browser suites, and do NOT pipe unfiltered repo-wide test runs into `| tail` (which hides hanging browser/SSE sockets). In Stage 2, do NOT run `package_epic.py`.
>      - **FINAL GATE ONLY**: Reserve the full regression suite, Playwright E2E browser harness, and full `quality_check` artifact regeneration strictly for the **Final Convergence Gate** (`AUTO_PASS_CLEAN`, `AUTO_PASS_FINAL_MINOR_SWEEP`, `AUTO_PASS_FINAL_SWEEP` with 0 Critical) after all code findings are resolved.
>    - **Zero-Tolerance Anti-Evasion Rules (No Shortcut Fixes)**:
>      - **No Dependency/Artifact Deletion**: Never resolve an unlocked dependency finding by removing the required package from `pyproject.toml`, and never resolve a stale quality report finding by simply deleting the report without regenerating it. If `uv.lock` is blocked by task scope rules, explicitly add `uv.lock` to the task's `Allowed files` and run `uv lock`.
>      - **No Synthesized Fallback Fixtures**: When a finding flags fake/generated test data, do not replace it with another runtime generator. Load genuine immutable fixtures from disk and fail hard when missing.
>      - **Browser Binary Synchronization**: Whenever `playwright` is added or upgraded in `pyproject.toml` / `uv.lock`, immediately run `uv run playwright install chromium` before invoking any browser E2E check.

## 7. Multi-Repo Boundaries, Symlink Isolation & Contract Governance

> [!CRITICAL]
> **AI Agents MUST strictly respect repository boundaries, symbolic link isolation, and contract-first governance across multi-repo ecosystems (Hub and Satellite repositories).**
>
> 1. **Multi-Repo Git Boundary Isolation**:
>    - An AI Agent running in any repository MUST NOT stage (`git add`) or commit (`git commit`) files residing outside the current git working tree.
>    - In a Satellite repository where `shared-contracts/` is a symbolic link pointing to a Hub repository (e.g. `lyrics-sync` or `nexus` linking to `D3Nexus`):
>      - Agents MUST treat `shared-contracts/` as **strictly read-only** for git tracking within the satellite workspace.
>      - Agents **MUST NOT** include `shared-contracts/...` in `Files Allowed` for local git tasks (preventing `fatal: pathspec is beyond a symbolic link`).
>      - Agents **MUST NOT** autonomously execute git commit commands in adjacent repositories (e.g. `git -C <target_repo>`) without explicit developer confirmation.
>
> 2. **Contract-First Triad & Canonical SSOT**:
>    - The Hub repository containing the physical `shared-contracts/` directory is the sole canonical authority (Single Source of Truth) for contract commits.
>    - Before modifying endpoints, database models, worker bridges, offline sync logic, or DTOs, agents MUST inspect the 3 canonical contract files in the relevant domain folder (`shared-contracts/<domain>/`):
>      1. `api_contract.md`: Endpoints, wire format, headers, telemetry, and payload schemas.
>      2. `architecture_and_flow.md`: Pipeline states, state machines, lifecycle fencing, and failure handling.
>      3. `gaps_and_rfcs.md`: Asynchronous change proposals, gap ledger, and cross-repo alignments.
>
> 3. **No Unilateral Breaking Changes & Non-Breaking Schema Guarantee**:
>    - Never rename API fields, mutate JSON request/response structures, or alter pipeline state enums in backend or client implementations without prior documentation and alignment in `shared-contracts/`.
>    - All schema and payload modifications MUST guarantee backward compatibility across all consumers (optional fields with safe defaults, non-breaking enum additions). Breaking changes without backward-compatible transition windows or fallback shims are strictly forbidden.
>
> 4. **Asynchronous RFC Workflow (Gaps & RFCs Ledger)**:
>    - If an agent in a satellite repo detects a payload mismatch, missing field, or new requirement, it **MUST NOT** invent ad-hoc fields or silently diverge.
>    - The agent MUST log a formal `GAP-XX` or `RFC-XXX` entry in `gaps_and_rfcs.md` (or emit an Upstream Contract Handoff Summary via `d3nexus:dev-designer`) and wait for upstream alignment before implementing breaking changes.
>
> 5. **Stateless Compute & Architectural Isolation**:
>    - Satellite worker nodes (e.g. `lyrics-sync`) must act strictly as stateless compute nodes. Direct connection to the control plane database (`DATABASE_URL`, PostgreSQL/SQLite) is **STRICTLY FORBIDDEN**. All state transitions, lease acquisitions, and result deliveries occur strictly via documented HTTP REST/SSE endpoints using worker authentication tokens.

## 8. Mandatory Two-Tier Project Memory & Tri-Role Persona Discipline

> [!CRITICAL]
> **AI Agents MUST strictly preserve Two-Tier Project Memory across session rotations and respect Tri-Role Persona boundaries across all stages of development.**
>
> 1. **Mandatory Context Restoration on Session Startup (Scoped to Development Lifecycle)**:
>    - When starting substantive feature engineering, architectural design, or task execution in the development lifecycle (`d3nexus:dev-lifecycle`, `dev-brainstorming`, `dev-designer`, `dev-implementation`) or after an account profile switch for development, the AI Agent MUST run `python3 scripts/resume_context.py` (or the `d3nexus:resume-context` skill) to restore architectural memory before answering or proposing solutions.
>    - The agent MUST summarize the restored project context in 5–10 concise bullets for the developer.
>    - **Zero-Context & Fast-Execution Exemption**: Routine operational prompts, standalone utility skills, and fast-execution commands — specifically `/refresh-session` (pinging quota windows), `/setup_keybindings`, git status/diff inspections, or quick standalone queries — **MUST NOT** invoke `resume_context.py` or `resume-context`. They must execute their requested actions immediately without loading repository context.
>    - **No Redundant Invocation**: Within an already-resumed active working session, the AI Agent MUST NOT repeatedly re-invoke `resume-context` on normal conversation turns.
>
> 2. **Strict Tri-Role Persona Discipline**:
>    - **Role 2.1 — Human Architect (Developer)**: Sole authority for system strategy, Gate approvals (Gate 1, 2, 5), triage escalations, and Stage 4 Finish decisions. Task execution order (Gate 3), local Gate 4 runs, and transition to Cross-Model Review are automated by default without manual confirmation pauses. In autonomous mode, halted strictly on critical risks, business/contract conflicts, or final merge sign-off.
>    - **Role 2.2 — AI Assistant (`[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]`)**:
>      - Activated for architectural analysis, problem statement exploration, design specifications (`d3nexus:dev-brainstorming`, `d3nexus:dev-designer`), Principal Review (`d3nexus:principal-review`), Cross-Model Review (`d3nexus:cross-model-review`), and fix plan evaluation.
>      - Dynamically inherits developer's selected model (Argon, Claude, Codex) or CLI override `--assistant-model`.
>      - **STRICT PROHIBITION**: The AI Assistant is **STRICTLY PROHIBITED from modifying production source code or application test suites**. Only architectural documentation (`docs/`, `.devtool/`, `shared-contracts/`) may be edited.
>    - **Role 2.3 — AI Programmer (`[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]`)**:
>      - Activated for `/dev-implementation` and task execution inside isolated git worktrees. Defaults to Model **Gemini Flash 3.8** (`--effort high --mode auto`).
>      - **STRICT BOUNDARIES**: Bound strictly to approved specifications, `Decisions Already Made`, and `Allowed files`. Must practice strict TDD (Red-Green-Refactor) and Clean Code standards. Zero test fakery.
>
> 3. **Deterministic State & Log Checkpointing**:
>    - After completing each Kanban task, the AI Programmer MUST log programmer activity (`scripts/resume_context.py --log`) and update Tier 2 snapshot state (`scripts/resume_context.py --state`).
>    - **Mandatory Human Pause & Action Checkpointing**: Whenever an AI Agent pauses execution to prompt the Human Architect for confirmation, decision, or gate approval (specifically: Gate 1 Spec Approval, Stage 2 Review Provider Priority, Stage 2 Exit Implementation Choice, Circuit Breaker escalations, or Stage 4 Gate 5 Finish/Merge Sign-Off), the AI Agent **MUST checkpoint the state before prompting** via `python3 scripts/resume_context.py --state --status "Waiting for <Action>" --prompt "<Prompt/Question>"` (or `/save-context`). Conversely, when executing autonomously (Phase 2 TDD tasks, Phase 4 local machine verification, or automated Cross-Model Review), the agent MUST update state with `--status "In progress: <Phase>"` so telemetry dashboards (`/check-tasks`, `/tasks --ui`) deterministically track that no human confirmation is required (`is_human_action_required: false`).
>    - Upon feature completion in Stage 4 (`/finish`), the agent MUST run `scripts/resume_context.py --complete <epic_slug> "<milestone_summary>"` to record the permanent milestone in `.devtool/PROJECT_LEDGER.md` and archive the completed epic's Tier 2 files into `.devtool/archive/`.
>
> 4. **Mandatory Window Title Synchronization & Persistent Top/Bottom Bar Customization**:
>    - To eliminate cross-project window confusion when developers operate multiple IDEs or profile accounts, AI Agents MUST synchronize `window.title` and ensure persistent top/bottom bar colors in `.vscode/settings.json` upon entering an epic, transitioning lifecycle stages, or completing tasks.
>    - **Title Format**: `"<ICON> [<REPO_NAME>] [@<account_id>] <Vietnamese Epic Name> - <Stage / Task>"`.
>    - The `<account_id>` is extracted from the active profile / home environment (`os.path.basename(os.environ["HOME"])` under `antigravity_homes/`, e.g. `[@danhdue]`, `[@tess]`).
>    - The Vietnamese Epic Name MUST be extracted directly from the H1 header of `.devtool/epic/<epic_slug>/<epic_slug>.vi.md` (stripping the `# Epic:` prefix).
>    - **Persistent Inactive Bar Parity**: Both `titleBar` and `statusBar` MUST configure matching inactive background colors (`titleBar.inactiveBackground = titleBar.activeBackground` and `statusBar.inactiveBackground = statusBar.background`) to eliminate IDE dimming when windows lose focus.
>    - **Clean Activity Toolbar**: The left `activityBar.background` remains uncolored in default dark theme to avoid peripheral visual clutter.
>    - **Repository Color Signatures**:
>      - 🔴 `[LYRICS-SYNC]`: `#7f1d1d` (Crimson Red)
>      - 🟢 `[D3NEXUS]`: `#065f46` (Emerald Green)
>      - 🔵 `[NEXUS]`: `#0d47a1` (Royal Blue)
>      - 🟠 `[AGENT-TOOLS]`: `#b45309` (Warm Amber)
>    - Agents MUST preserve all existing `workbench.colorCustomizations` and developer configurations in `.vscode/settings.json`.

## 9. Shell Configuration (`.zshrc`) & Multi-Profile OS Boundary Safety

> [!CRITICAL]
> **Modifications to `~/.zshrc` or shell startup scripts MUST strictly follow Multi-Profile OS Safety rules to prevent breaking host OS system services (AirDrop, Apple ID, WiFi, Docker, Keychain) and profile isolation.**
>
> 1. **Mandatory Pre-Modification Backup & Syntax Verification**:
>    - Before applying ANY edits to `~/.zshrc`, agents MUST create a timestamped backup: `cp ~/.zshrc ~/.zshrc.bak.$(date +%Y%m%d_%H%M%S)`.
>    - After editing, agents MUST immediately verify syntax via `zsh -n ~/.zshrc` before concluding the turn.
>    - Agents MUST check for existing functions, aliases, or environment blocks before appending to avoid duplicate definitions.
>
> 2. **Strict Host OS Keychain & Security Protection (Zero Global Mutating)**:
>    - AI Agents are **STRICTLY PROHIBITED** from executing `security default-keychain` or `security list-keychains -s` globally in `~/.zshrc` or global shell commands.
>    - The host macOS default keychain MUST ALWAYS remain `/Users/<user>/Library/Keychains/login.keychain-db` to prevent crippling macOS system daemons (especially `sharingd` for AirDrop, `identityservicesd`, `trustd`, and Wi-Fi credential lookups).
>    - Profile keychain isolation is achieved EXCLUSIVELY via:
>      - Per-profile plist: `~/antigravity_homes/<profile>/Library/Preferences/com.apple.security.plist` (automatically respected by macOS Security framework when `HOME=$ag_home`).
>      - Scoped unlock inside subshells: `security unlock-keychain -p <pass> <profile.keychain-db>` within isolated scripts or `ag_run` subshells.
>      - Zero CLI Mutation: Profile CLI commands (`ag_run <profile> cli`, `{profile}-cli`) MUST NEVER mutate `security default-keychain` or `security list-keychains`.
>
> 3. **Strict Subshell Scope for Profile Environments (No Global Environment Contamination)**:
>    - AI Agents MUST **NEVER** export profile-specific environment variables (such as `export HOME=...`, `export AGY_PROFILE=...`, `export TMPDIR=/tmp/ag_...`) at the top-level of `~/.zshrc`.
>    - Profile environments MUST ONLY be established within localized subshells spawned by `ag_run()` or dedicated profile CLI aliases (`{profile}-cli`).
>    - Inside IDE terminals (`TERM_PROGRAM == "vscode"` and `-z "$AGY_CLI_MODE"`), `$HOME` MUST always remain `$REAL_HOME` (`/Users/<user>`) to guarantee unhindered access to OS services, local daemons (PostgreSQL, Docker daemon, Redis, MinIO), and host toolchains.
>
> 4. **Shared Toolchains, Libs & Symlink Architecture**:
>    - **Profile Scope & Boundary**: An Antigravity profile (`antigravity_homes/<profile>`) exists solely to isolate Antigravity user identity, credentials, OAuth tokens, and IDE session state.
>    - **Mandatory Shared Development Infrastructure**: All programming toolchains, developer tools, shared libraries, package managers, and compilation caches (Homebrew, Android SDK, Gradle, FVM, Flutter, Rust/Cargo, Go, Python/UV, npm, Docker socket, Caches) MUST be shared from the host OS (`$REAL_HOME`) via symlinks, NEVER duplicated, isolated, or severed.
>    - Agents modifying profile provisioning scripts or symlinks MUST strictly preserve symlinks to `$REAL_HOME` for all shared toolchains and libraries.
>
> 5. **Parent Process & IPC Handle Stripping in Launchers (`ag_run`)**:
>    - When launching Antigravity IDE instances (`open -n -a "Antigravity IDE"`), agents MUST explicitly strip parent process IPC handles, socket variables, and leaked runtime environment states:
>      `env -u ELECTRON_RUN_AS_NODE -u VSCODE_GIT_IPC_HANDLE -u VSCODE_IPC_HOOK_CLI HOME="$ag_home" AGY_PROFILE="$profile" TMPDIR="/tmp/ag_$profile" open ...`
>    - This eliminates socket collisions, channel crossover, and environment leaks when launching a new profile from within an existing IDE terminal or background automation daemon.
>
> 6. **Strict Antigravity Profile Identity & State Decoupling**:
>    - **Independent Antigravity State**: All internal Antigravity runtime state (`.gemini/antigravity`, conversation summaries, and `data/User/globalStorage/state.vscdb`) MUST remain strictly independent per profile. Never symlink `.gemini/antigravity` or `state.vscdb` to `$REAL_HOME` or another profile.
>    - **Identity Parity with Keychain**: The stored username in `data/User/globalStorage/state.vscdb` (`google.google-antigravity -> agy.onboarding.lastLoginUsername`) MUST match the profile's dedicated Keychain (`<profile>.keychain-db`).
>    - **Process & Token Hygiene**: Always terminate resident Electron PIDs of a profile (`pkill -f antigravity_homes/<profile>`) before modifying its DB to prevent stale RAM overwrites, and purge `signedOut` OAuth flags. For the exhaustive local protocol, see `.agents/rules/profile_isolation_rules.md`.
>    - **No Blind State Cloning**: Agents MUST NEVER clone `state.vscdb` from another profile without resetting `agy.onboarding.lastLoginUsername` to the target profile's email, and purging stale `comments`, `workspaceStorage`, and cross-profile paths from `extensions.user.cache`.
>    - **Hardware Fingerprint & Telemetry Decoupling**: Every profile's `storage.json` MUST contain unique, cryptographically generated `telemetry.machineId` and `telemetry.devDeviceId`. Never copy them without regenerating. Every profile's `settings.json` MUST set `"telemetry.telemetryLevel": "off"` to prevent leaking workspace paths and hardware signatures. Profile trajectory databases (`conversation_summaries.db`) must never be cloned.

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

exec
/bin/zsh -lc 'cat /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.28.3/skills/principal-review/SKILL.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
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

3. **Triage Findings, Top 3 Highest-Risk Report & Auto-Triage Gate**:
   - Read and follow [document-triage.md](references/document-triage.md) (Source-of-Truth Hierarchy: Forward Alignment over Legacy Reversion, Top 3 Highest-Risk Findings Report, and Auto-Triage Gate).
   - Inspect `## Auto-Triage Gate` from `run_external_review.py triage --kind principal --epic-dir <epic_dir>`:
     - **`AUTO_PASS_CLEAN` / `AUTO_PASS_FINAL_MINOR_SWEEP` / `AUTO_PASS_FINAL_SWEEP` (Round 3 with `0 Critical`)**: Verify all findings against source code and the approved Spec/HLD first (halting only on `CRITICAL_CONFLICT`, `Debatable` trade-offs, `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, or `MAX_ROUNDS_CRITICAL_REMAINING`). Apply any valid final sweep revisions and decision commits, then run final packaging (`package_epic.py <epic_dir>`, or `--revise --reason "Revise after Principal Review"` if `handoff.md` already exists), commit `[<EPIC_NAME>] Package epic for handoff`, save state (`--state`), **print `--emit-prompt implement`**, and (in interactive mode) prompt **Triển khai (tự động)** vs **Dừng lại** without calling another review round.
     - **`AUTO_FIX_ELIGIBLE` (Round 1..2 with `Critical`/`Important`, no `shared-contracts/` conflict, no Fix Loop)**: Verify every finding against live source code and the approved Spec/HLD (`Decisions Already Made`), and emit the triage summary header block (`## Auto-Triage Gate`, `## Top 3 Highest-Risk Findings`, `## Findings`). In **BOTH Autonomous (`lifecycle_runner.py`) and Interactive Mode**, when all blocking findings verify as `Valid` (plus any objective `False positive` refuted with exact source/approved-Spec proof) and zero halt triggers apply, **do NOT pause for confirmation**: automatically apply document revisions in Role 2.2, record decisions (`fixed in <sha>` / verified evidence), verify readiness (`check_epic_readiness.py <epic_dir>`, without premature `handoff.md` packaging), and immediately advance to Round $N+1$. Stop calling tools and escalate to the Human Architect **ONLY** on **`CRITICAL_CONFLICT`** (business/domain requirement, critical risk, or Tier-1 Spec intent conflict — in autonomous mode `lifecycle_runner.py` transitions to `AWAITING_PRINCIPAL_CONFIRMATION` and writes `.devtool/epic/<epic_dir>/principal_fix_proposal_round<N>.md`), a **`Debatable`** finding requiring a trade-off choice, **`SHARED_CONTRACT_CONFLICT`**, **`FIX_LOOP`**, or **`MAX_ROUNDS_CRITICAL_REMAINING`** (triage header block format):
       ```markdown
       Principal Review Triage: Round <N> (<CLI>)
       *(or `Principal Review Triage: <doc_path> (<CLI>)`)*

       • Candidate SHA: <commit_sha>
       • Reviewer: <CLI> ( <model> )
       • Thinking Level: <Light | Low | Medium | High | Extra High | None>
       • Verdict: <VERDICT> (<count> <Severity> findings)
       ```
     - **`CIRCUIT_BREAKER_HALT` (`SHARED_CONTRACT_CONFLICT` in any round, `FIX_LOOP`, or `MAX_ROUNDS_CRITICAL_REMAINING` when `>= 1 Critical` survives Round 3)**: **STOP IMMEDIATELY**, never auto-fix or revert the user-approved HLD design, and report `## Top 3 Highest-Risk Findings (Executive Report)` to the Human Architect.

4. **Revision Loop, Convergence & Post-Review Packaging (`package_epic.py` + `/save-context`)**:
   - **Intermediate rounds (when advancing to Round `n+1`)**: apply document edits and record decisions without running `package_epic.py` mid-loop:
     - Apply document edits first and commit:
       `git commit -m "[<EPIC_NAME>] Revise epic after Principal Review round <n>"`
     - Record decisions with revision commit SHA in `principal_review.md`, then commit:
       `git commit -m "[<EPIC_NAME>] Record Principal Review decisions for round <n>"`
     - Verify `python3 skills/dev-implementation/resources/scripts/check_epic_readiness.py <epic_dir>` exits 0 and automatically advance to Round `n+1`.
   - **At completion of `/principal-review` (after convergence `AUTO_PASS_CLEAN`, `AUTO_PASS_FINAL_MINOR_SWEEP`, or `AUTO_PASS_FINAL_SWEEP` and any final sweep commits)**:
     - Execute packaging now: `python3 skills/dev-implementation/resources/scripts/package_epic.py <epic_dir>` (pass `--revise --reason "Revise after Principal Review round <n>"` only if `handoff.md` already exists) and commit `[<EPIC_NAME>] Package epic for handoff` if `auto_commit: true`.
     - Record Gate 2 approval (if revised) via `python3 scripts/resume_context.py --gate 2 --epic <epic_slug> --approved "Passed Principal Review round <n> and packaged"`.
     - Record state via `python3 scripts/resume_context.py --state --epic <epic_slug> --status "Stage 2: Packaged & Ready"`, and **print the AI Programmer implementation prompt** (`python3 scripts/resume_context.py --emit-prompt implement --epic <epic_slug>` + `handoff.md` path).
     - In autonomous lifecycle mode (`lifecycle_runner.py`), transition directly to Role 2.3 (AI Programmer, Model Gemini Flash 3.8) and invoke `d3nexus:dev-implementation`. In interactive mode, stop calling tools and ask **Triển khai (tự động)** vs **Dừng lại** (*"Dừng lại ở đây để tôi lấy prompt cho một AI Agents khác triển khai"*): invoke `d3nexus:dev-implementation` automatically if **Triển khai (tự động)**, or stop cleanly if **Dừng lại**.

## Guidelines & Reference Documents

Read these on demand, not up front. `run_external_review.py` loads the prompt template and review rules itself, so do not open them to run a review.

- [Prompt Template](references/principal-review-prompt.md): The read-only instruction template sent to reviewer CLIs (script-consumed; do not read).
- [Review Rules](references/principal-review-rules.md): Severity definitions (Critical, Important, Minor) and source grounding standards (script-consumed; do not read).
- [Document Triage Protocol](references/document-triage.md): Step-by-step decision verification and revision loop enforcement (read at step 3 only).
- [Verification Row Grammar](../dev-designer/references/verification-row-grammar.md) (read only when a finding concerns Verification rows): Canonical Verification table grammar rules (including `\|` pipe escaping, `env VAR=val` prefixing, slash-containing search pattern rules, and portable CLI usage). Escaped pipes `\|` in table command cells are unescaped by `task_contract.py` and must not be flagged as syntax errors.

exec
/bin/zsh -lc 'wc -l .devtool/epic/token_throttling_optimization/*; rg --files -g AGENTS.md -g CLAUDE.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     131 .devtool/epic/token_throttling_optimization/2026-11-13-token-throttling-optimization-design.en.md
     132 .devtool/epic/token_throttling_optimization/2026-11-13-token-throttling-optimization-design.vi.md
     229 .devtool/epic/token_throttling_optimization/bdd_scenarios.en.md
     229 .devtool/epic/token_throttling_optimization/bdd_scenarios.vi.md
     145 .devtool/epic/token_throttling_optimization/task_01_diff_only_external_review_and_transcript_isolation.md
     138 .devtool/epic/token_throttling_optimization/task_02_silent_gate4_and_truncated_test_runners.md
     163 .devtool/epic/token_throttling_optimization/task_03_option_a_bilingual_and_surgical_contract_guards.md
     158 .devtool/epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md
     176 .devtool/epic/token_throttling_optimization/task_05_slimming_rules_skills_dedup_and_selective_reviewer.md
     139 .devtool/epic/token_throttling_optimization/task_06_integration_and_regression_verification.md
     247 .devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md
     247 .devtool/epic/token_throttling_optimization/token_throttling_optimization.vi.md
    2134 total
CLAUDE.md
templates/AGENTS.md

exec
/bin/zsh -lc "cat /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.28.3/skills/using-superpowers/SKILL.md; git --no-optional-locks status --short; git rev-parse HEAD; git ls-tree -r --name-only 8d456f6ec6f420e17932c67c8425a563ac3913ee .devtool/epic/token_throttling_optimization; rg -n 'token_throttling|principal|review' /Users/danhdueexoictif/antigravity_homes/duvthinh403/.codex/memories/MEMORY.md" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 4870ms:
---
name: using-superpowers
description: Use when starting any conversation - establishes how to find and use skills, requiring skill invocation before ANY response including clarifying questions
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## The Rule

**Invoke relevant or requested skills BEFORE any response or action** — including clarifying questions, exploring the codebase, or checking files. If it turns out wrong for the situation, you don't have to use it.

**Before entering plan mode:** if you haven't already brainstormed, invoke the brainstorming skill first.

Then announce "Using [skill] to [purpose]" and follow the skill exactly. If it has a checklist, create a todo per item.

## Skill Priority

When multiple skills apply, process skills come first — they set the approach, then implementation skills (frontend-design, etc.) carry it out. Brainstorming and systematic-debugging are Superpowers' most common process skills, but the rule holds for any of them.

- "Let's build X" → d3nexus:brainstorming first, then implementation skills.
- "Fix this bug" → d3nexus:systematic-debugging first, then domain skills.

## Red Flags

These thoughts mean STOP—you're rationalizing:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can check git/files quickly" | Files lack conversation context. Check for skills. |
| "Let me gather information first" | Skills tell you HOW to gather information. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. |
| "This doesn't count as a task" | Action = task. Check for skills. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This feels productive" | Undisciplined action wastes time. Skills prevent this. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## Platform Adaptation

This kit targets **Claude Code** (the default these skills are written against), **Antigravity**,
and **Codex**. On Antigravity, read [`references/antigravity-tools.md`](references/antigravity-tools.md).
On Codex, read [`references/codex-tools.md`](references/codex-tools.md). These references map the
actions described in the skills to the tools available in each runtime.

## User Instructions

User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, etc, direct requests) take precedence over skills, which in turn override default behavior. Only skip skill workflows or instructions when your human partner has explicitly told you to.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-CsIwKJtl' (errno=Operation not permitted)
2026-11-13 02:43:42.965 xcodebuild[69802:24688594]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-13 02:43:43.102 xcodebuild[69802:24688592] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-Md83S8Vu' (errno=Operation not permitted)
2026-11-13 02:43:43.535 xcodebuild[69811:24688656]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-13 02:43:43.652 xcodebuild[69811:24688655] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-SWIbBNCa' (errno=Operation not permitted)
2026-11-13 02:43:44.647 xcodebuild[69853:24689179]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-13 02:43:44.797 xcodebuild[69853:24689177] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-CJR4N0uh' (errno=Operation not permitted)
2026-11-13 02:43:45.230 xcodebuild[69922:24689496]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-13 02:43:45.364 xcodebuild[69922:24689494] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
8d456f6ec6f420e17932c67c8425a563ac3913ee
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-yn5Xux1T' (errno=Operation not permitted)
2026-11-13 02:43:46.389 xcodebuild[70026:24690300]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-13 02:43:46.507 xcodebuild[70026:24690298] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-0YQiHfGg' (errno=Operation not permitted)
2026-11-13 02:43:46.905 xcodebuild[70032:24690379]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-13 02:43:47.017 xcodebuild[70032:24690378] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
.devtool/epic/token_throttling_optimization/2026-11-13-token-throttling-optimization-design.en.md
.devtool/epic/token_throttling_optimization/2026-11-13-token-throttling-optimization-design.vi.md
.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md
.devtool/epic/token_throttling_optimization/bdd_scenarios.vi.md
.devtool/epic/token_throttling_optimization/task_01_diff_only_external_review_and_transcript_isolation.md
.devtool/epic/token_throttling_optimization/task_02_silent_gate4_and_truncated_test_runners.md
.devtool/epic/token_throttling_optimization/task_03_option_a_bilingual_and_surgical_contract_guards.md
.devtool/epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md
.devtool/epic/token_throttling_optimization/task_05_slimming_rules_skills_dedup_and_selective_reviewer.md
.devtool/epic/token_throttling_optimization/task_06_integration_and_regression_verification.md
.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md
.devtool/epic/token_throttling_optimization/token_throttling_optimization.vi.md
1:# Task Group: ai-agent-tools setup_shared_contracts principal contract review
3:scope: Read-only, source-grounded architectural review of the Hub/Satellite shared-contract setup epic; use before implementation or when reconciling design, BDD, task, HLD, and verification contracts.
4:applies_to: cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools; reuse_rule=reinspect the candidate commit and all current epic artefacts; review findings are commit-specific, while the cross-contract comparison procedure is reusable.
10:- rollout_summaries/2026-10-30T06-59-12-Elg4-principal_review_setup_shared_contracts_contract_drift.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/30/rollout-2026-10-30T13-59-12-01a18b9a-faa7-7f50-81b9-b3c8aa8e3a08.jsonl, updated_at=2026-10-29T23:08:05+00:00, thread_id=01a18b9a-faa7-7f50-81b9-b3c8aa8e3a08, `CHANGES REQUIRED`; later review verified these four findings were fixed)
14:- setup_shared_contracts, principal-review, shared_contracts_readme.md.tmpl, string.Template, `{{DOMAIN_NAME}}`, --root, --repo-root, --satellite-root, scripts/verify.sh, Section 11, Section 14, contract drift
16:## Task 2: Re-review setup_shared_contracts after corrections, partial
20:- rollout_summaries/2026-10-30T06-59-12-zvna-principal_review_setup_shared_contracts_contract_contradicti.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/30/rollout-2026-10-30T13-59-12-01a18b9a-faa8-72e0-8192-3dd403258730.jsonl, updated_at=2026-10-29T23:26:36+00:00, thread_id=01a18b9a-faa8-72e0-8192-3dd403258730, `CHANGES REQUIRED`; current implementation-blocking finding)
24:- setup_shared_contracts, principal-review, SSC-FR-03, shared-contracts, non-empty, symlink, Rule 7, `Covers:`, traceability, `python3 -m unittest`, CHANGES REQUIRED
28:- When requesting a principal review, the user required a “strictly read-only review” with exact source file/line grounding, artefact-specific actionable findings, and an exact final verdict block -> do not edit files or Git state; cite concrete locations for each source claim. [Task 1][Task 2]
32:- Related skill: skills/principal-contract-review/SKILL.md. [Task 1][Task 2]
33:- Treat frozen design/task differences as public implementation contracts, not harmless wording: template filenames/substitution syntax and CLI root flags must agree before an executor starts. In the first review, Mustache `{{DOMAIN_NAME}}` templates conflicted with Python `string.Template` `$domain`/`$hub_repo`/`$timestamp`, which would leave placeholders unresolved; `--root`, `--repo-root`, and `--satellite-root` likewise needed a single contract. The later review verified those findings were fixed. [Task 1][Task 2]
34:- Check requested `scripts/verify.sh` integration against the surrounding responsibility, not its stated number. Section 11 was lifecycle/document tooling; with Sections 1–13 present, a dedicated Section 14 was the valid shared-contract test location, and the later review verified the wiring correction. [Task 1][Task 2]
44:# Task Group: D3Nexus Apple Music media-controller epic corrective review and Stage 2 handoff
46:scope: Code-anchored correction of `preview_apple_music_media_controller` design, task, BDD, and handoff contracts; use before any Gate 2 approval or Stage 3 work on the floating player dock.
49:## Task 1: Review and correct `preview_apple_music_media_controller` package, partial
53:- rollout_summaries/2026-10-22T06-06-56-3JSJ-review_correct_apple_music_media_controller_epic.md (cwd=/Users/danhdueexoictif/AllProjects/D3Nexus, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/22/rollout-2026-10-22T13-06-56-01a16238-406a-7931-a84f-337a4f51cf7d.jsonl, updated_at=2026-10-22T06:34:27+00:00, thread_id=01a16238-406a-7931-a84f-337a4f51cf7d, corrective Stage 2 draft; final bilingual validation not fully evidenced)
57:- preview_apple_music_media_controller, handoff.md, Gate 2, check_bdd_traceability.py, check_task_contract.py, compute_execution_order.py, check_document.py, Playwright, floating-dock.ts, SettingsPopover.astro, AMC-AT-01, canonical selectors
61:- When reviewing an epic, the user asked for the design spec, epic overview, BDD, handoff, and source code, especially `handoff.md` -> inspect the complete lifecycle artifact set and verify status claims against actual production symbols rather than trusting packaged status. [Task 1]
62:- The review stopped at documentation/Gate approval; do not implement code or enter Gate 3 without explicit approval. [Task 1]
66:- Correct execution order is `550 -> 549/551 -> 552 -> 553 -> 554`; `compute_execution_order.py preview_apple_music_media_controller` derives it when the dependencies are present. [Task 1]
81:applies_to: cwd=/Users/danhdueexoictif/AllProjects/lyrics-sync; reuse_rule=reinspect current preview/UI/API/CLI defaults and source classification before changing behavior; this is analysis/policy, not an implemented production change.
100:- Align Studio UI/API/job defaults are `split_sentences=true`, `resegment_llm=true`, and `normalize_llm=false`; `lyrics-sync align` CLI instead defaults `resegment_llm=false`. The expensive default therefore belongs chiefly to the Studio preview flow. [Task 1]
109:- Do not conflate CLI defaults with Align Studio defaults: inspect `cli.py`, preview API, preview jobs, and browser request construction separately. [Task 1]
153:- Do not claim the amendment implemented: this rollout changed only bilingual design documents; `dev-designer/SKILL.md`, `handoff-template.md`, and anti-drift tests were not changed, and no amendment commit/user review is evidenced. [Task 2]
174:- rollout_summaries/2026-10-18T19-19-37-2Uj4-playlist_playback_queue_epic_corrective_review_and_handoff.md (cwd=/Users/danhdueexoictif/AllProjects/D3Nexus, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/19/rollout-2026-10-19T02-19-37-01a15074-8aa0-7c01-8a6e-51fda3dbcf0e.jsonl, updated_at=2026-10-18T19:42:47+00:00, thread_id=01a15074-8aa0-7c01-8a6e-51fda3dbcf0e, package/handoff validated; no implementation)
203:# Task Group: ai-agent-tools Gate 4 Review Choice loop and external-review diagnostics
205:scope: Verified lifecycle state-machine update and streamed external-review precondition reporting.
212:- rollout_summaries/2026-10-18T10-39-52-b3XU-gate4_review_choice_loop_and_external_review_streaming.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/18/rollout-2026-10-18T17-39-52-01a14e98-b2b9-7043-9d17-65dd8df4be46.jsonl, updated_at=2026-10-18T15:23:36+00:00, thread_id=01a14e98-b2b9-7043-9d17-65dd8df4be46, committed and fully verified)
216:- Gate 4, Review Choice, Cross-model review, Gate 5, SHA-bound, rules/CRITICAL_RULES.md, test_verifiable_handoff_text.py, df9f67af7c1f7fecd3b4a9768c0863d035ed3088
218:## Task 2: Add realtime ANSI pre-check output to external review, success
222:- rollout_summaries/2026-10-18T10-39-52-b3XU-gate4_review_choice_loop_and_external_review_streaming.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/18/rollout-2026-10-18T17-39-52-01a14e98-b2b9-7043-9d17-65dd8df4be46.jsonl, updated_at=2026-10-18T15:23:36+00:00, thread_id=01a14e98-b2b9-7043-9d17-65dd8df4be46, 31 targeted tests and full verification passed)
226:- run_external_review.py, run_gate, PreconditionFailedError, [PRECONDITION BLOCKED], ANSI, flush=True, audit_epic.py, check_bdd_traceability.py, scripts/verify.sh, android-ui-audit
230:- The user explicitly corrected the lifecycle sequence: “Gate 4 => Review Choice”, then “Finish” or “Cross model review”, and “Sau bước này chạy lại Gate 4 ... Loop cho tới khi finish.” -> preserve this order for similar ai-agent-tools lifecycle work. [Task 1]
235:- Enforced invariant: `Gate 4 PASS -> Review Choice; Finish -> Gate 5; Cross-model review -> Gate 4 in full`. A review round, decision, Fix commit, Gate 5-requested change, cross-model CLI failure, or timeout that changes/reassesses the candidate requires full Gate 4 before another Review Choice. Gate 4 is SHA-bound. [Task 1]
236:- The policy update touched `rules/CRITICAL_RULES.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-implementation/SKILL.md`, bilingual lifecycle docs, lifecycle-selection docs, and `scripts/test_verifiable_handoff_text.py`; commit `df9f67af7c1f7fecd3b4a9768c0863d035ed3088` is `[REVIEW_WORKFLOW] Loop review choice through Gate 4`. [Task 1]
238:- Route `audit_epic.py`, declared Integration commands, and `check_bdd_traceability.py` through `run_gate()` while retaining captured output in the facts bundle. `run_external_review.py` does not directly invoke `android-ui-audit`; that is only indirect through the quality-provider registry. Targeted suite passed 31 tests and `scripts/verify.sh` reported `PASS — safe to publish`; worktree was clean on `main`, with no push. [Task 2]
291:- Canonical public route is `/s/f/<opaque_share_id>` and only `Ready` snapshots are public. Continue internally with `/app/tracks/<slug>?line=<line>&t=<start_ms>&occurrence=<id>#preview`; preserve timestamp precedence and no autoplay. `apps/learning-web/src/core/navigation/url-params.ts` already parses `slug`, `line`, `t`, `colloc`, and preview hash. [Task 1]
292:- Public snapshots must be sanitized, immutable, owner-scoped internally, and independent of later source edits. Static Astro/client-only metadata cannot support social crawlers; use a server public projection/SSR and deterministic revisioned 1200x630 OG image. Social clients control their own preview UI. [Task 1]
293:- D3Nexus owns backend, Astro web, public snapshot API, SSR/OG, web UX, and shared HTTPS/OpenAPI contract. `/Users/danhdueexoictif/AllProjects/nexus` owns Flutter/mobile UI, native sharing, Universal Links/App Links, recipient preview, and mobile fallback. Mobile specs remain in D3Nexus at `docs/superpowers/specs/2026-10-18-contextual-flashcard-sharing-mobile-design.en.md` and `.vi.md` (`b130026`). [Task 2]
319:- learning_core, FSRS-6, fsrs-6.6.2, desired retention 0.85, lexical_items, phrase_occurrences, review_log, card_state, Rust/WASM, Flutter FFI, review-room.ts
333:- For a conceptual FSRS review/adoption, the user approved continuation only after the announced verification/package plan (“Tiếp tục”) -> preserve explicit action boundaries and do not silently expand into implementation. [Task 1][Task 2]
338:- `learning_core` is the pure Rust FSRS-6 authority (`fsrs` 6.6.2, desired retention 0.85): grading, scheduling, deterministic replay, snapshot decisions, retrievability, and due queries. It does not own catalogue storage, UI, IndexedDB, HTTP, outbox, or screen state. Immutable review logs are truth; snapshots are derived/versioned; bindings are Flutter FFI and WASM. [Task 1]
339:- Catalogue entities remain catalogue-owned: `lexical_items`, `phrase_occurrences`, lyrics context/media. Use a learner-owned integration layer with stable schedule identity, immutable review logs, derived card state, sync, and reconciliation; do not add learner scheduling to catalogue rows. [Task 1]
340:- Replace unsafe web fallbacks before implementation: `apps/learning-web/src/wasm/learning-core.ts` had heuristic TypeScript scheduling, `review-room.ts` started from sample/in-memory cards, and live IDs were phrase-derived. Rust/WASM must be the authority. Avoid old guides that mix FSRS-7 with unpublished APIs. [Task 1]
349:# Task Group: D3Nexus design_system Gate 4 evidence review and lifecycle concurrency
351:scope: Gate 4 review of a web-heavy epic: evidence completeness, fail-closed verdicts, stable-SHA reruns, and lifecycle race protection.
358:- rollout_summaries/2026-10-16T05-48-38-Pr6V-design_system_gate_4_review_fail.md (cwd=/Users/danhdueexoictif/AllProjects/D3Nexus, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/16/rollout-2026-10-16T12-48-38-01a14341-57f0-7ad0-b345-c5f06b4cce11.jsonl, updated_at=2026-10-16T06:10:35+00:00, thread_id=01a14341-57f0-7ad0-b345-c5f06b4cce11, validated FAIL report; review report remains uncommitted)
366:- When reviewing an epic, the user asked for a thorough review of the design spec, epic overview, handoff, and related tasks, with the result file inside the epic directory -> inspect the full lifecycle artifact set and put the durable review report at the requested in-place path. [Task 1]
372:- On stable merge SHA `89358cb11e24186eeac307f055124c2a58b1b46e`, format, provider-check, clippy, Rust tests, coverage, architecture, deny, WASM, FFI, docs, and DB hygiene passed; acceptance failed at `apps/server/tests/catalog_taxonomy_search_test.rs:772`: `p95 latency 153 ms exceeded 150 ms budget for three_facets_keyword`. The review also verified 58/58 BDD coverage, 794/794 independent web tests, 15 Astro pages, and 700 docs. [Task 1]
483:- Initial review found unresolved `podcast`/`interview`, `movie_tv`/`conversation`, and `lecture`/`speech` overlap -> provide explicit boundaries and precedence before approving a taxonomy reference. [Task 1]
501:- 10 use cases/21 BDD scenarios; missing realtime popovers, context navigation, editorial editing, edge cases. Split: preview_flashcards, vocabulary_catalog, vocabulary_studio, flashcard_audio_delivery. Audit/reuse Task 116/current components first. [Task 1]
502:- Flow: user upload -> OCR job -> draft candidates -> review/edit -> committed flashcards -> TTS/audio. IDs alone must not grant access; public/catalog is explicit transition. [Task 1]
503:- Screenshot parity needs exact summary, 3-column/equal-height/footer grid, density, 3->2->1 breakpoints and screenshot regression; add PF-D1.5 Preview Flashcards Grid Visual Parity. [Task 1]
507:# Task Group: D3Nexus learning-web lyrics preview parity and media-clock repair
509:scope: Audit and partial repair of lyrics preview parity, media clocks, and browser verification; not merge-ready evidence.
510:applies_to: cwd=/Users/danhdueexoictif/AllProjects/D3Nexus including .worktrees/lyrics_preview_parity and .worktrees/lyrics_preview_repair; reuse_rule=re-check worktree/runtime/browser state.
512:## Task 1: Audit preview parity and repair runtime/media clocks, partial
514:- rollout_summaries/2026-10-12T17-38-20-pzMb-lyrics_preview_parity_audit_and_runtime_repair.md (cwd=/Users/danhdueexoictif/AllProjects/D3Nexus, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/13/rollout-2026-10-13T00-38-21-01a13131-aabd-7152-beff-ea7c98bb263f.jsonl, updated_at=2026-10-13T05:04:30+00:00, thread_id=01a13131-aabd-7152-beff-ea7c98bb263f, 10 targeted tests passed; Playwright partial)
516:- lyrics_preview_parity, PreviewSession, DualMasterPlayerClock, /api/v1/lyrics/:slug, port 8686, projectTimeline, youtube-sdk.ts, #line-l2, Playwright
518:- Compare design/HLD/BDD, current code, two concrete preview URLs, and sibling lyrics-sync; provide gap analysis/staged plan before edits. [Task 1]
521:- PreviewSession waits for track/media; projectTimeline applies offset once; DualMasterPlayerClock syncs every second/preserves promotion state/safe no-op. YouTube SDK needs timeout, abort and cleanup. [Task 1]
528:scope: Provider quality orchestration review and documentation-only Stage 2 closure.
533:- rollout_summaries/2026-10-11T06-07-53-ad3F-rust_quality_provider_stage2_closure_review.md (cwd=/Users/danhdueexoictif/AllProjects/D3Nexus, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/11/rollout-2026-10-11T13-07-53-01a12993-2b6d-79e2-84b4-b9af3dcbf627.jsonl, updated_at=2026-10-12T01:28:17+00:00, thread_id=01a12993-2b6d-79e2-84b4-b9af3dcbf627, docs validated; commit not evidenced)
564:# Task Group: lyrics-sync Preview Studio keyboard shortcuts and acceptance
567:applies_to: cwd=/Users/danhdueexoictif/AllProjects/lyrics-sync and .worktrees/preview_keyboard_shortcuts; reuse_rule=recheck overlap/environment.
571:- rollout_summaries/2026-10-09T09-50-56-CTSe-preview_keyboard_shortcuts_task4_acceptance.md (cwd=/Users/danhdueexoictif/AllProjects/lyrics-sync/.worktrees/preview_keyboard_shortcuts, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/09/rollout-2026-10-09T16-50-56-01a12012-aa8f-7af0-b4f7-ea7f130c511e.jsonl, updated_at=2026-10-09T16:10:45+00:00, thread_id=01a12012-aa8f-7af0-b4f7-ea7f130c511e, Task 4 complete)
572:- rollout_summaries/2026-10-09T09-41-49-gwDf-preview_keyboard_shortcuts_gate2_planning.md (cwd=/Users/danhdueexoictif/AllProjects/lyrics-sync, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/09/rollout-2026-10-09T16-41-49-01a1200a-521a-7831-9fab-8530a32bdd11.jsonl, updated_at=2026-10-09T10:51:16+00:00, thread_id=01a1200a-521a-7831-9fab-8530a32bdd11, design/handoff)
574:- preview_keyboard_shortcuts, event.code, Audio-master, YouTube-master, getGapState().lineIndex, HTTP 206, R2, 24 PASS
578:- Space play/pause; W/Up previous; S/Down next; A/Left slower; D/Right faster; R/F replay; L loop; Shift Left/Right ±5s. event.code, ignore modifiers/repeat/editables; Preview-only; Audio/YouTube. [Task 1]
581:- Do not trust JS impact tool 0%; run node --test tests/js/**/*.test.mjs. scripts/check.sh has 41 pre-existing Ruff findings; review app.js rebase conflicts/preserve unrelated Kanban. [Task 1]
590:- rollout_summaries/2026-10-09T09-41-49-kWY2-studio_llm_token_vision_deepseek_ocr_epic_review.md (cwd=/Users/danhdueexoictif/AllProjects/lyrics-sync, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/09/rollout-2026-10-09T16-41-49-01a1200a-5221-7441-98a8-46c955baaee2.jsonl, updated_at=2026-10-08T19:55:52+00:00, thread_id=01a1200a-5221-7441-98a8-46c955baaee2, measured OCR/spec r3)
618:- Never persist local fallback/open Drawer after R2 failure; no normal Sync R2/skip re-extraction; keep FastAPI/stdlib preview parity. [Task 1]
629:- FSRS, learning_core, review_log, card_state, ADR-007, Rust, WASM, Flutter, SQLite WASM/OPFS, Mac mini

exec
/bin/zsh -lc 'nl -ba .devtool/epic/token_throttling_optimization/task_01_diff_only_external_review_and_transcript_isolation.md; nl -ba .devtool/epic/token_throttling_optimization/task_02_silent_gate4_and_truncated_test_runners.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
exec
/bin/zsh -lc 'nl -ba .devtool/epic/token_throttling_optimization/2026-11-13-token-throttling-optimization-design.en.md; nl -ba .devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
exec
/bin/zsh -lc 'nl -ba .devtool/epic/token_throttling_optimization/task_03_option_a_bilingual_and_surgical_contract_guards.md; nl -ba .devtool/epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	---
     2	id: "task_01_diff_only_external_review_and_transcript_isolation"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "token_throttling_optimization"
     7	dueDate: null
     8	created: "2026-11-13T02:30:00Z"
     9	modified: "2026-11-13T02:30:00Z"
    10	completedAt: null
    11	labels: ["review", "token-optimization", "config"]
    12	order: "a1"
    13	---
    14	
    15	# Task 1: Diff-Only External Review and Transcript Isolation
    16	
    17	Epic: [token_throttling_optimization](token_throttling_optimization.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Enforce Diff-Only Review (`Rule 1`), Silent/Capped Evidence (`Rule 2`), Transcript Log Isolation (`Rule 5`), and Config-Driven Role 2.3 defaults in the external review subsystem:
    22	1. Update `DEFAULT_REVIEW_CONFIG["providers"]` and `load_review_config()` in `skills/dev-implementation/resources/scripts/run_external_review.py`:
    23	   - Add default `"assistant"` (`"claude-opus-5-5-high"`, `"high"`) and `"programmer"` (`"gemini-4-hydrogen-xhigh"`, `"xhigh"`) provider entries.
    24	   - Inside `load_review_config()`, seed missing default providers and upgrade legacy programmer models (`"gemini-3.8-flash"`, `"gemini-3.8-flash-high"`) in-memory to `"gemini-4-hydrogen-xhigh"` with `"thinking_level": "xhigh"`, while leaving custom user models (e.g. `"claude-sonnet-4-6"`) untouched.
    25	2. Enforce Diff-Only `-U5` and Round 2+ delta-only prompts:
    26	   - Change `git diff` context from `-U10` to `-U5` in both `run_external_review.py` (`build_diff_section`, `diff_range`) and `skills/subagent-driven-development/scripts/review-package`.
    27	   - When `build_diff_section()` or `diff_range()` truncates over `MAX_DIFF_LINES` (`1500`) or `MAX_DIFF_BYTES` (`60000`), prepend `git diff --stat` and include per-file headers + `@@ ... @@` hunk headers within budget.
    28	   - Exclude all `*.vi.md` files from `principal_artefact_lines()` and `collect_facts()` / `artefact_lines()` where applicable.
    29	   - In `run()` for `round_num >= 2` when `delta_round_context()` is non-empty (and `--full` is not set), omit the cumulative `base...sha` diff section and emit a 1-line `git diff --stat` cumulative reference instead.
    30	3. Quiet facts and raw CLI log isolation:
    31	   - Update `fact(label, code, out, err)` so `code == 0` emits `f"PASS: {label}\n"` omitting stdout, and failure emits the label plus the last 25 non-empty lines.
    32	   - Update `render_round()` to persist raw CLI stdout/stderr transcripts into `build/reviews/<epic>_round<n>.raw.log` and reference that path instead of dumping multi-megabyte transcripts into `principal_review.md` or `review_results.md`, keeping the compact `Raw output:` verdict fence intact for downstream table/finding parsers (`rounds_in`, `finding_rows`, `triage`).
    33	   - Update `skills/principal-review/references/principal-review-prompt.md` and `skills/dev-implementation/references/external-review-prompt.md` with explicit Diff-Only (`-U5`), Zero-Fluff output, and English SSOT review guidance.
    34	4. Add `tests/test_tto_external_review.py` covering `TTO-HP-01`, `TTO-EC-01`, `TTO-ST-01`, and `TTO-FR-01`.
    35	
    36	## Files
    37	
    38	Allowed files:
    39	- `skills/dev-implementation/resources/scripts/run_external_review.py`
    40	- `skills/dev-implementation/resources/scripts/test_run_external_review.py`
    41	- `skills/subagent-driven-development/scripts/review-package`
    42	- `skills/dev-implementation/references/external-review-prompt.md`
    43	- `skills/principal-review/references/principal-review-prompt.md`
    44	- `tests/test_tto_external_review.py` (new)
    45	
    46	Read-only context:
    47	- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Module Contracts and Integration Plan
    48	- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios
    49	- `.agents/quality/python-quality.json` — Registered lint and type_check commands
    50	
    51	## Design Rationale
    52	
    53	External review rounds dominate token burn because every Round 2+ re-transmits full `base...sha` diffs, `.vi.md` duplicates, verbose passing command logs, and raw CLI stderr back into markdown artifacts that later stages reload. Enforcing `-U5`, structural `--stat` + `@@` truncation, Round 2 delta isolation, 1-line passing facts, and raw log offloading eliminates quadratic bloat without losing any parser fidelity. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.
    54	
    55	## Impact Analysis & Blast Radius
    56	
    57	- **Target Files & Symbols**:
    58	  - `skills/dev-implementation/resources/scripts/run_external_review.py`: `load_review_config` (L103-L129), `principal_artefact_lines` (L317-L352), `fact` (L507-L508), `collect_facts` (L511-L640), `build_diff_section` (L652-L683), `diff_range` (L686-L719), `render_round` (L896-L902), `delta_round_context` (L972-L1118), `run` (L1230-L1320)
    59	  - `skills/subagent-driven-development/scripts/review-package`: diff context lines (L1-L77)
    60	  - `tests/test_tto_external_review.py`: new unit and integration tests for `TTO-HP-01`, `TTO-EC-01`, `TTO-ST-01`, `TTO-FR-01`
    61	- **Downstream Callers**: `scripts/resume_context.py` (`--emit-prompt`), `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`load_review_config`, `run_external_review.py` subprocess), `skills/dev-implementation/resources/scripts/test_run_external_review.py`.
    62	- **Cross-Platform Bridges**: None.
    63	- **Target Test Coverage Threshold**: 100% of new config migration, diff truncation, fact formatting, and raw log offloading branches.
    64	
    65	### BDD SCENARIOS
    66	
    67	Covers: TTO-HP-01, TTO-EC-01, TTO-ST-01, TTO-FR-01
    68	
    69	```gherkin
    70	Scenario: [TTO-HP-01] [Tier C - Integration] Diff-only external review uses -U5 in Round 1 and omits full base diff in Round 2
    71	
    72	Given an isolated git repository with an epic having multiple committed source changes and a .vi.md companion document
    73	And an existing Round 1 entry already recorded in review_results.md for an earlier SHA
    74	When run_external_review.py builds the Round 1 prompt and then builds the Round 2 prompt after an incremental fix commit
    75	Then the Round 1 diff section is generated with -U5 context and excludes all *.vi.md artifact paths
    76	And the Round 2 prompt includes delta_round_context for prev_sha..curr_sha with a one-line cumulative diff --stat reference
    77	And the Round 2 prompt omits the full base...curr_sha diff block unless --full is explicitly passed
    78	
    79	Scenario: [TTO-EC-01] [Tier A - Unit] Over-budget diff truncates to --stat summary and @@ hunk headers per changed file
    80	
    81	Given a synthetic git diff exceeding MAX_DIFF_LINES (1500 lines) or MAX_DIFF_BYTES (60000 bytes)
    82	When build_diff_section builds the diff payload for external review
    83	Then the output falls back cleanly within the byte budget without dropping structural file boundaries
    84	And the truncated section explicitly contains the git diff --stat summary alongside the file headers and @@ hunk headers for changed files
    85	
    86	Scenario: [TTO-ST-01] [Tier A - Unit] load_review_config migrates legacy gemini-3.8-flash defaults while preserving custom models
    87	
    88	Given an existing .devtool/review_config.json with providers.programmer.model set to "gemini-3.8-flash-high"
    89	And a second config file where providers.programmer.model is customized to "claude-sonnet-4-6"
    90	When run_external_review.load_review_config loads each configuration file
    91	Then the legacy "gemini-3.8-flash-high" entry is upgraded in-memory to "gemini-4-hydrogen-xhigh" with thinking_level "xhigh"
    92	And the user-customized "claude-sonnet-4-6" entry remains untouched without being overwritten
    93	
    94	Scenario: [TTO-FR-01] [Tier A - Unit] collect_facts emits one line per passing command and caps failing output + raw transcripts
    95	
    96	Given a passing command returning 180 stdout lines with exit code 0 and a failing command returning 90 stderr lines with exit code 1
    97	When run_external_review.fact builds prompt evidence and render_round persists the round artifact
    98	Then the passing command produces a single "PASS: <label>" line omitting stdout
    99	And the failing command includes the command label plus at most 25 trailing non-empty output lines
   100	And unfiltered CLI stdout/stderr is routed into build/reviews/<epic>_round<n>.raw.log so principal_review.md remains compact
   101	```
   102	
   103	## Verification
   104	
   105	| ID | Phase | Command | Expect | Needs |
   106	|----|-------|---------|--------|-------|
   107	| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_external_review.py::test_tto_hp_01_diff_only_round1_and_round2` | exit 1; contains "failed" | — |
   108	| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_external_review.py::test_tto_hp_01_diff_only_round1_and_round2` | exit 0; contains "passed" | — |
   109	| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; contains "passed" | — |
   110	| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py tests/test_tto_external_review.py` | exit 0 | — |
   111	| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py tests/test_tto_external_review.py` | exit 0 | — |
   112	| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_1.xml tests/test_tto_external_review.py` | exit 0; results build/test-results/task_1.xml | — |
   113	
   114	## Stop and Report If
   115	
   116	- A command, path, symbol or anchor named in this task does not match the repository.
   117	- A Verification row fails for a reason other than its Expect.
   118	- The work needs a change to a file outside Allowed files, or to a protected path.
   119	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
   120	  Covers line.
   121	- A variable named in the Needs column is unset.
   122	
   123	## Decisions Already Made
   124	
   125	- `DEFAULT_REVIEW_CONFIG["providers"]` (in `skills/dev-implementation/resources/scripts/run_external_review.py`) includes `"assistant": {"model": "claude-opus-5-5-high", "thinking_level": "high"}` and `"programmer": {"model": "gemini-4-hydrogen-xhigh", "thinking_level": "xhigh"}`.
   126	- `load_review_config()` upgrades legacy programmer IDs `{"gemini-3.8-flash", "gemini-3.8-flash-high"}` in-memory to `"gemini-4-hydrogen-xhigh"` + `"thinking_level": "xhigh"`, preserving custom models and avoiding mutations to the gitignored repo-level `.devtool/review_config.json` during unit tests.
   127	- Diff extraction in `build_diff_section()` and `diff_range()` (L652-L719) and `review-package` uses `git diff -U5`; over-budget diffs retain `git diff --stat` and per-file `@@ ... @@` hunk headers; `principal_artefact_lines()` (L317-L352) excludes `*.vi.md`.
   128	- `fact(label, code, out, err)` (L507-L508) emits `"PASS: {label}\n"` on `code == 0` and caps failures to the last 25 non-empty lines; `render_round()` (L896-L902) writes unfiltered transcripts to `build/reviews/<epic>_round<n>.raw.log` while preserving `Raw output:` verdict fences compatible with `rounds_in()` (L850-L865), `finding_rows()` (L1528-L1529), and `triage()` (L1711-L1783).
   129	- Round `>= 2` in `run()` (L1230-L1320) omits full `base...sha` `diff_section` whenever `delta_round_context()` is non-empty and `--full` is false.
   130	
   131	## Definition of Done
   132	
   133	- Scenarios TTO-HP-01, TTO-EC-01, TTO-ST-01, and TTO-FR-01 pass with real temporary git repositories and fake CLIs. (V2, V3, V6)
   134	- Python ruff lint and mypy strict checks pass across modified and existing test suites. (V3, V4, V5)
   135	- Diff context (`-U5`), `.vi.md` exclusion, raw log offloading, and `load_review_config` migration verified cleanly on candidate commit. (Gate 5)
   136	
   137	## Dependencies & Blockers
   138	
   139	None. Blocks [Task 4](task_04_lifecycle_runner_programmer_config_and_pool_isolation.md) and [Task 5](task_05_slimming_rules_skills_dedup_and_selective_reviewer.md).
   140	
   141	## References & Rollback
   142	
   143	- [Epic HLD](token_throttling_optimization.en.md), Module Contracts (§1).
   144	- **Rollback**: Revert task commit; restores prior `run_external_review.py`, `review-package`, prompt templates, and removes `tests/test_tto_external_review.py`.
   145	
     1	---
     2	id: "task_02_silent_gate4_and_truncated_test_runners"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "token_throttling_optimization"
     7	dueDate: null
     8	created: "2026-11-13T02:30:00Z"
     9	modified: "2026-11-13T02:30:00Z"
    10	completedAt: null
    11	labels: ["gate4", "quality-check", "token-optimization"]
    12	order: "a2"
    13	---
    14	
    15	# Task 2: Silent Gate 4 and Truncated Test Runners
    16	
    17	Epic: [token_throttling_optimization](token_throttling_optimization.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Enforce Silent Gate 4 and 25-line failure tailing (`Rule 2`) across quality providers, task verification runners, and release checks:
    22	1. Add `--compact` mode to `skills/quality_check/resources/scripts/verify_polyglot_registry.py`:
    23	   - Write full raw stdout/stderr per provider capability to `build/quality/<provider>/<cap>.log`.
    24	   - When `--compact` is enabled and checks/verdict pass, print single-line `GATE_PASS: <provider_or_cap>` entries instead of verbose JSON blobs.
    25	   - When `--compact` encounters a failure or `BLOCKED` outcome, print the failing capability header and strictly at most 25 trailing lines from its `.log` file while leaving all raw lines intact on disk.
    26	2. Reduce `TAIL_LINES` from `40` to `25` in `skills/dev-implementation/resources/scripts/run_task_checks.py`.
    27	3. Update `.agents/quality/python-quality.json` (protected path named explicitly in `Allowed files`) `"test"` command and `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py` `"python"` template so pytest runs append `"-q", "--tb=short", "--maxfail=3"`.
    28	4. Add `--quiet` flag to `scripts/verify.sh` outputting one concise status line per passing section and at most 25 trailing lines on failure, while keeping default/`--full` behavior unchanged.
    29	5. Document `--compact` invocation in `skills/quality_check/SKILL.md`.
    30	6. Expand `tests/test_polyglot_gate4.py` and `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py` / `skills/dev-implementation/resources/scripts/test_run_task_checks.py` with tests covering `TTO-HP-02`, `TTO-EC-02`, and `TTO-FR-02`.
    31	
    32	## Files
    33	
    34	Allowed files:
    35	- `skills/quality_check/resources/scripts/verify_polyglot_registry.py`
    36	- `skills/dev-implementation/resources/scripts/run_task_checks.py`
    37	- `skills/dev-implementation/resources/scripts/test_run_task_checks.py`
    38	- `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`
    39	- `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py`
    40	- `.agents/quality/python-quality.json`
    41	- `scripts/verify.sh`
    42	- `skills/quality_check/SKILL.md`
    43	- `tests/test_polyglot_gate4.py`
    44	
    45	Read-only context:
    46	- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Module Contracts (§2)
    47	- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios
    48	
    49	## Design Rationale
    50	
    51	Quality checks routinely emit thousands of passing lines and JSON structures into agent context. Routing verbose provider output to `build/quality/<provider>/<cap>.log` and returning single-line `GATE_PASS:` summaries or 25-line failure tails slashes Gate 4 token burn while keeping full diagnostics on disk for debugging. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.
    52	
    53	## Impact Analysis & Blast Radius
    54	
    55	- **Target Files & Symbols**:
    56	  - `skills/quality_check/resources/scripts/verify_polyglot_registry.py`: `execute_provider` (L142-L438), `verify_polyglot_execution` (L441-L537), `main` (L540-L618)
    57	  - `skills/dev-implementation/resources/scripts/run_task_checks.py`: `run_row` (L282-L321), `main` (L461-L476)
    58	  - `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`: `build_registry_data` (L226-L241)
    59	  - `scripts/verify.sh`: §1-§17 output formatting (L1-L417)
    60	  - `tests/test_polyglot_gate4.py`: integration assertions for `TTO-HP-02`, `TTO-EC-02`, `TTO-FR-02`
    61	- **Downstream Callers**: `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`run_gate4`), `skills/dev-implementation/SKILL.md` (`@quality_check`), `skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`.
    62	- **Cross-Platform Bridges**: None.
    63	- **Target Test Coverage Threshold**: 100% of `--compact` pass/fail branches, 25-line truncation boundaries, and `--quiet` `verify.sh` handling.
    64	
    65	### BDD SCENARIOS
    66	
    67	Covers: TTO-HP-02, TTO-EC-02, TTO-FR-02
    68	
    69	```gherkin
    70	Scenario: [TTO-HP-02] [Tier C - Integration] Compact Gate 4 runner prints single-line GATE_PASS and stores full logs under build/quality
    71	
    72	Given a project with a valid .agents/quality/check_quality.json registry whose providers exit with status 0
    73	When verify_polyglot_registry.py runs with --compact
    74	Then standard output contains single-line "GATE_PASS: <provider_or_cap>" entries instead of verbose JSON blobs
    75	And full per-capability execution logs are written to build/quality/<provider>/<cap>.log
    76	And the overall aggregated verdict equals PASS
    77	
    78	Scenario: [TTO-EC-02] [Tier A - Unit] Task runner enforces 25-line tail and Python quality manifests inject quiet pytest flags
    79	
    80	Given a failing task check output with 120 stdout/stderr lines
    81	And .agents/quality/python-quality.json alongside a scaffolded manifest from scaffold_quality_manifest.py
    82	When run_task_checks.py formats failure evidence and the Python test command is inspected
    83	Then run_task_checks.TAIL_LINES equals 25 and the emitted snippet retains only the last 25 non-empty lines
    84	And both .agents/quality/python-quality.json and newly scaffolded Python quality manifests invoke pytest with "-q", "--tb=short", and "--maxfail=3"
    85	
    86	Scenario: [TTO-FR-02] [Tier C - Integration] Compact Gate 4 surfaces failing provider header and 25-line log tail on error
    87	
    88	Given a quality registry containing one passing capability and one failing capability printing 80 diagnostic lines to stderr
    89	When verify_polyglot_registry.py runs with --compact
    90	Then the process exits non-zero reporting FAIL
    91	And standard output prints "GATE_PASS:" for the passing capability plus the failing capability header and strictly at most 25 trailing log lines from build/quality/
    92	And all 80 raw diagnostic lines remain preserved on disk inside build/quality/<provider>/<cap>.log
    93	```
    94	
    95	## Verification
    96	
    97	| ID | Phase | Command | Expect | Needs |
    98	|----|-------|---------|--------|-------|
    99	| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_polyglot_gate4.py::test_tto_hp_02_compact_gate4_single_line_pass` | exit 1; contains "failed" | — |
   100	| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_polyglot_gate4.py::test_tto_hp_02_compact_gate4_single_line_pass` | exit 0; contains "passed" | — |
   101	| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_polyglot_gate4.py skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0; contains "passed" | — |
   102	| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/dev-implementation/resources/scripts/run_task_checks.py tests/test_polyglot_gate4.py` | exit 0 | — |
   103	| V5 | TIER-B | `ruff check --select F,E9,B skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py` | exit 0 | — |
   104	| V6 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/run_task_checks.py skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py` | exit 0 | — |
   105	| V7 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_2.xml tests/test_polyglot_gate4.py` | exit 0; results build/test-results/task_2.xml | — |
   106	
   107	## Stop and Report If
   108	
   109	- A command, path, symbol or anchor named in this task does not match the repository.
   110	- A Verification row fails for a reason other than its Expect.
   111	- The work needs a change to a file outside Allowed files, or to a protected path not named explicitly here.
   112	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
   113	  Covers line.
   114	- A variable named in the Needs column is unset.
   115	
   116	## Decisions Already Made
   117	
   118	- `verify_polyglot_registry.py` (`execute_provider` L142-L438, `main` L540-L618) adds `--compact`: always writes full capability stdout/stderr to `build/quality/<provider>/<cap>.log`, prints `GATE_PASS: <provider_or_cap>` for passing checks, and prints failing header + last 25 lines of the capability log on failure while returning non-zero exit codes cleanly.
   119	- `run_task_checks.py` updates `TAIL_LINES = 25` (`run_task_checks.py` line 77).
   120	- `.agents/quality/python-quality.json` updates `"test"` capability from `["python3", "-m", "pytest", "tests"]` to `["python3", "-m", "pytest", "-q", "--tb=short", "--maxfail=3", "tests"]` (justifying modification of this declared protected path by naming it explicitly in `Allowed files`).
   121	- `scaffold_quality_manifest.py` (`PLATFORM_CONFIGS["python"]["manifest"]["capabilities"]["test"]`, L131) includes `"-q", "--tb=short", "--maxfail=3"`.
   122	- `scripts/verify.sh` adds `--quiet` flag without changing `--full` default semantics or exit codes.
   123	
   124	## Definition of Done
   125	
   126	- Scenarios TTO-HP-02, TTO-EC-02, and TTO-FR-02 are verified by passing unit and integration tests. (V2, V3, V7)
   127	- Ruff lint and mypy checks pass cleanly across modified files. (V4, V5, V6)
   128	- Protected path `.agents/quality/python-quality.json` update produces quiet pytest flags cleanly under Gate 4. (Gate 5)
   129	
   130	## Dependencies & Blockers
   131	
   132	None. Blocks [Task 4](task_04_lifecycle_runner_programmer_config_and_pool_isolation.md) and [Task 5](task_05_slimming_rules_skills_dedup_and_selective_reviewer.md).
   133	
   134	## References & Rollback
   135	
   136	- [Epic HLD](token_throttling_optimization.en.md), Module Contracts (§2).
   137	- **Rollback**: Revert task commit; restores prior `verify_polyglot_registry.py`, `TAIL_LINES = 40`, `python-quality.json`, and `verify.sh`.
   138	

 succeeded in 0ms:
     1	# Design Spec: Aggressive Token Optimization for Dev Lifecycle
     2	
     3	## Table of Contents
     4	
     5	- [1. Background and Measured Hotspots](#1-background-and-measured-hotspots)
     6	- [2. Goals and Non-Goals](#2-goals-and-non-goals)
     7	- [3. Architecture and Core Design](#3-architecture-and-core-design)
     8	- [4. Detailed Component Changes](#4-detailed-component-changes)
     9	  - [4.1 Diff-Only Review and Transcript Isolation](#41-diff-only-review-and-transcript-isolation)
    10	  - [4.2 Silent Gate 4 and Truncated Test Output](#42-silent-gate-4-and-truncated-test-output)
    11	  - [4.3 Surgical Reads and Target Line Ranges](#43-surgical-reads-and-target-line-ranges)
    12	  - [4.4 Context Isolation and Selective Task Reviewer](#44-context-isolation-and-selective-task-reviewer)
    13	  - [4.5 Zero-Fluff Output Cap, Rules, and Skills Slimming](#45-zero-fluff-output-cap-rules-and-skills-slimming)
    14	  - [4.6 Option A Bilingual Workflow](#46-option-a-bilingual-workflow)
    15	  - [4.7 Config-Driven Programmer Persona and Gemini 4 Hydrogen](#47-config-driven-programmer-persona-and-gemini-4-hydrogen)
    16	- [5. Verification Strategy and Kit Invariants](#5-verification-strategy-and-kit-invariants)
    17	- [6. Shared Contract Warnings](#6-shared-contract-warnings)
    18	
    19	## 1. Background and Measured Hotspots
    20	
    21	An end-to-end audit across `ai-agent-tools` workflows, rules, hooks, and runner scripts identified five structural drivers of quadratic context bloat and quota exhaustion across `dev-lifecycle` (Manual and Autonomous modes):
    22	
    23	1. **Always-On Baseline Overhead**: `rules/CRITICAL_RULES.md` (`32,773` bytes / `239` lines) is injected into every conversation, subagent, and headless CLI invocation (partially truncated at `8,848` bytes by IDE rules loading). `skills/task-observer/SKILL.md` (`31,480` bytes / `526` lines) lacks a `<SUBAGENT-STOP>` guard, forcing worker subagents and review CLIs to ingest it before their first tool call. `scripts/resume_context.py` emits `26,759` bytes (`310` lines) across all workspace repos by default.
    24	2. **Quadratic Review Context Bloat (`O(R^2)`)**: In `skills/dev-implementation/resources/scripts/run_external_review.py`, Round >= 2 passes both full `base...sha` `diff_section` and `delta_round_context()`, duplicates `.en.md` and `.vi.md` artefacts, injects full pre-check logs via untruncated `fact()` even on exit `0`, uses default 3-line diff context (`-U10` in `review-package`), and appends unfiltered CLI `stderr` transcripts under `Raw output:` inside `principal_review.md` (measured up to `1,885,237` bytes / `23,450` lines in `autonomous_lifecycle_runner`).
    25	3. **Verbose Quality Gates and Uncapped Tracebacks**: `skills/quality_check/resources/scripts/verify_polyglot_registry.py` dumps full indented JSON even on `PASS`; `.agents/quality/python-quality.json` invokes `pytest` without `-q --tb=short --maxfail=3`; `run_task_checks.py` caps at `40` tail lines; `lifecycle_runner.py` and `scripts/verify.sh` forward full `stdout`/`stderr` on failure without 25-line truncation.
    26	4. **Coarse-Grained File Reads and Redundant Subagent Loops**: `dev-designer/SKILL.md` (`66,425` bytes) does not require `target_files` line ranges or symbols in task breakdowns; `_execute_single_task()` in `lifecycle_runner.py` dispatches sequential `agy` processes instead of bounded `manage_worker_pool.py` / line-bounded instructions; `cross-model-review` fix loops execute 3 separate LLM calls (`_draft_fix_plan` -> `evaluate_programmer_fix_plan` -> `_apply_code_fixes`) even for unambiguous `Valid` code fixes; interactive `subagent-driven-development` runs `task-reviewer` on every trivial task even when end-of-epic `cross-model-review` follows.
    27	5. **Unconstrained Verbosity and Upfront Bilingual Churn**: No stage enforces an output token cap, while Spec, HLD, and Gherkin BDD documents require full synchronized `.en.md` / `.vi.md` pairs throughout Stage 1, Stage 2, and Principal Review iterations.
    28	
    29	## 2. Goals and Non-Goals
    30	
    31	Goals:
    32	
    33	- Enforce the 5 Strict Token-Throttling Rules mechanically across scripts, prompts, schemas, rules, and skills without weakening TDD (`RED -> GREEN`), BDD traceability, architecture gates, or Circuit Breakers.
    34	- Implement both Phase 1 (mechanical runner/script optimizations) and Phase 2 (rules, task schema, skill slimming, deduplication).
    35	- Adopt Option A Bilingual Workflow: keep Spec and HLD `.vi.md` for human review at Gates 1 and 2, exclude all `.vi.md` files from LLM review/coder pipelines, defer `bdd_scenarios.vi.md` generation and HLD/Spec `.vi.md` delta-sync until `/finishing-a-development-branch`, and never delete/re-translate files twice.
    36	- Enable selective per-task `task-reviewer` in Stage 3 strictly for high-risk or complex tasks while relying on deterministic `run_task_checks.py` + end-of-epic `/cross-model-review` for mechanical tasks.
    37	
    38	Non-Goals:
    39	
    40	- Skipping or auto-approving human gates (Gate 1 Spec, Gate 2 Task Breakdown, Gate 5 Finish & Merge Decision).
    41	- Disabling full regression suites, Playwright E2E checks, or `@quality_check` execution at the Final Convergence Gate or Stage 4 `verify-tier`.
    42	- Auto-pushing commits or branches without explicit developer instruction.
    43	
    44	## 3. Architecture and Core Design
    45	
    46	```mermaid
    47	flowchart TD
    48	    RULES["Slim CRITICAL_RULES <= 8KB + Output Cap + task-observer SUBAGENT-STOP"] --> S1["Stage 1 dev-brainstorming: Spec .en.md + .vi.md for Human"]
    49	    S1 --> S2["Stage 2 dev-designer: HLD .en.md + .vi.md + bdd_scenarios.en.md + task Target Lines"]
    50	    S2 --> PR["Principal Review: .en.md Only + Delta Diff -U5 + Quiet Pre-checks + Log Split"]
    51	    PR --> PKG["package_epic.py: Exclude .vi.md from handoff Read First"]
    52	    PKG --> S3["Stage 3 TDD: Line-Bounded Reads + Clean Task Isolation + Selective task-reviewer"]
    53	    S3 --> G4["Gate 4 Silent Mode: GATE_PASS single line / Tail 25 lines on fail"]
    54	    G4 --> CMR["Cross-Model Review: -U5 Delta Only Rounds 2..3 + Streamlined Code Fix"]
    55	    CMR --> FIN["Stage 4 finishing-a-development-branch: Delta-Sync .vi.md + Gen bdd_scenarios.vi.md + verify-tier"]
    56	```
    57	
    58	## 4. Detailed Component Changes
    59	
    60	### 4.1 Diff-Only Review and Transcript Isolation
    61	
    62	- **Unified `-U5` Diffs and Truncation Guard**: Update `build_diff_section()` in `skills/dev-implementation/resources/scripts/run_external_review.py` and `skills/subagent-driven-development/scripts/review-package` to generate `git diff -U5`. When a diff exceeds `MAX_DIFF_LINES` (`1500`) or `MAX_DIFF_BYTES` (`60000`), emit `git diff --stat` and unified hunk headers (`@@ ... @@`) alongside changed filenames rather than leaving an empty diff block.
    63	- **No Duplicate `base...sha` in Round >= 2**: In `run_external_review.py` (`run()`), when `round_num >= 2` and `delta_round_context()` is active, omit the redundant full `base...sha` `diff_section`. Pass only `prev_sha..sha` delta diff (`-U5`), Prior Fixed Locations Registry, compact open findings summary (<= 200 chars per cell), and referenced Acceptance Criteria / task sections.
    64	- **English SSOT Only for Reviews**: Update `principal_artefact_lines()` and `collect_facts()` in `run_external_review.py` to exclude all `*.vi.md` paths from external reviewer context.
    65	- **Quiet Pre-Check Facts**: Replace verbatim `fact()` output in `collect_facts()` with `PASS: <label>` (1 line) when `returncode == 0`, and failing command + last 25 lines of combined output when non-zero.
    66	- **Transcript Isolation (`Raw output:`)**: In `render_round()`, route full external CLI `stderr` transcripts (and raw verbose payloads above summary bounds) to git-ignored `build/reviews/<epic>_round<n>.raw.log`, keeping `principal_review.md` and `review_results.md` limited to structured Verdict, Pass summary, and Findings tables plus a single log path pointer.
    67	- **Prompt Rules**: Inject `DIFF-ONLY REVIEW` constraints into `principal-review-prompt.md` and `external-review-prompt.md` forbidding full file reads unless resolving an explicit missing symbol or caller chain.
    68	
    69	### 4.2 Silent Gate 4 and Truncated Test Output
    70	
    71	- **Quiet Runner Defaults**: Enforce `pytest -q --tb=short --maxfail=3` in `.agents/quality/python-quality.json`, `setup_quality_check` Python templates, and `dev-designer/SKILL.md` Verification examples.
    72	- **Compact Output in Polyglot & Task Runners**:
    73	  - Add `--compact` (default for lifecycle callers, retaining raw logs on disk under `build/quality/<provider>/<cap>.log`) to `skills/quality_check/resources/scripts/verify_polyglot_registry.py` and update `quality_check/SKILL.md`: print `GATE_PASS: <provider_or_cap>` (1 line) on success, and failing capability summary + last 25 lines of traceback from its `.log` file on failure.
    74	  - Set `TAIL_LINES = 25` in `skills/dev-implementation/resources/scripts/run_task_checks.py`.
    75	  - Add helper `_tail_lines(text, limit=25)` in `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` for `run_gate4()` and `run_intermediate_check()` so failing commands return only summary + last 25 lines, while passing checks emit `GATE_PASS: <check_name>`.
    76	  - Add `--quiet` (1 line per passed section) and 25-line failure tailing to `scripts/verify.sh` while keeping `--full` diagnostics intact when needed.
    77	
    78	### 4.3 Surgical Reads and Target Line Ranges
    79	
    80	- **Task Schema Enhancement**: Update `skills/dev-designer/SKILL.md` task template (`## Files` / `## Impact Analysis & Blast Radius`) so every existing modified file larger than 200 lines requires an explicit `target_files` entry with symbol name and line window (`path :: Symbol (L<start>-L<end>)`).
    81	- **Contract Warning/Check**: Update `check_task_contract.py --design` to verify modified tracked files >200 lines carry target symbol/line anchors when defined in `Allowed files`.
    82	- **Stage 3 Read Discipline**: Update `dev-implementation/SKILL.md`, `skills/dev-lifecycle/references/handoff-template.md`, `implementer-prompt.md`, and `lifecycle_runner.py` (`_execute_single_task()`) to mandate range-bounded reads (`read_file` with `StartLine`/`EndLine` or `sed -n 'X,Yp'`) and symbol searches instead of full-file reads.
    83	
    84	### 4.4 Context Isolation and Selective Task Reviewer
    85	
    86	- **Strict Task Isolation & Concise Handoff**:
    87	  - In interactive `subagent-driven-development`, preserve isolated per-task execution using `task-brief` and file-based reports so Task `N+1` starts fresh without Task `1..N` tool history.
    88	  - In `lifecycle_runner.py` (`step_implementation()` and `_execute_single_task()`), pass file paths (`task_file`, `handoff.md`) rather than inlining full file contents into stdin prompts, and dispatch independent topological waves concurrently using `manage_worker_pool.py`.
    89	- **Selective Per-Task `task-reviewer` Trigger**:
    90	  - Define high-risk criteria in `dev-designer/SKILL.md`, `dev-implementation/SKILL.md`, and `subagent-driven-development/SKILL.md`: invoke `task-reviewer` (with `-U5` `review-package`) when a task has `review_tier: "full"` in frontmatter, `labels` matching `{"security", "architecture", "concurrency", "contract"}`, or non-test `Allowed files` spanning more than 2 modules.
    91	  - Standard mechanical tasks rely on deterministic `run_task_checks.py` TDD verification (`RED`, `GREEN`, `TIER-B`, `TIER-C`) and end-of-epic `/cross-model-review`.
    92	- **Streamlined Autonomous Fix Loop & Dynamic Final Report**:
    93	  - In `lifecycle_runner.py` (`step_cross_model_review()`), when findings are verified `Valid` code fixes with no `shared-contracts/` impact and no `CRITICAL_CONFLICT`, allow Role 2.3 to apply direct fixes + scoped tests without extra `_draft_fix_plan` -> `evaluate_programmer_fix_plan` round-trips (retaining Role 2.2 plan evaluation only for contract/design ambiguity).
    94	  - Update `render_final_executive_report()` in `lifecycle_runner.py` to parse real highest-risk findings and SHAs from `review_results.md` / `principal_review.md` instead of returning hardcoded sample rows.
    95	
    96	### 4.5 Zero-Fluff Output Cap, Rules, and Skills Slimming
    97	
    98	- **Output Token Cap Directive**: Add a shared 5-rule Zero-Fluff output constraint across `rules/CRITICAL_RULES.md`, `dev-lifecycle/SKILL.md`, `dev-implementation/SKILL.md`, `quality_check/SKILL.md`, `finishing-a-development-branch/SKILL.md`, and all `lifecycle_runner.py` prompts: no greetings/preamble, no prompt restating, no echoing unchanged code, no narrative explaining passing checks; emit only `[STATE]` transitions, tool calls, and max 3 root-cause bullets on failures.
    99	- **Rules & Subagent Guard Slimming**:
   100	  - Condense `rules/CRITICAL_RULES.md` from `32,773` bytes to `<= 8,192` bytes (preventing IDE `<truncated>` slicing) by turning verbose explanations into normative `MUST`/`NEVER` rules and moving extended workflow checklists into `skills/dev-lifecycle/references/`. Preserve Rule 1–9 semantic contracts and satisfy `scripts/verify.sh` source-fidelity checks.
   101	  - Add `<SUBAGENT-STOP>` guard at the top of `skills/task-observer/SKILL.md` so subagents and headless review CLIs bypass loading `31.4 KB` of observer instructions.
   102	- **Scoped `resume_context.py`**: Add `--compact` (defaulting to epic-scoped output when `--epic <slug>` is passed) in `scripts/resume_context.py` so Role 2.2 / Role 2.3 receives active epic state, current repo git status, open relevant RFC headers, and matching epic tasks (~2–3 KB) instead of multi-repo dumps (`26.7 KB`).
   103	- **Skills Progressive Disclosure & Reference Deduplication**:
   104	  - Condense `skills/dev-designer/SKILL.md` (`66.4 KB` -> `<= 22 KB`) and `skills/quality_check/SKILL.md` by extracting verbose platform examples and boilerplate templates into linked `references/` files.
   105	  - Consolidate duplicate prompt/rule/triage files shared between `skills/dev-implementation/references/`, `skills/principal-review/references/`, and `skills/cross-model-review/references/` into canonical single sources while keeping all cross-links valid under `scripts/verify.sh`.
   106	
   107	### 4.6 Option A Bilingual Workflow
   108	
   109	- **Stage 1 & Stage 2 (Human Review)**: `dev-brainstorming` generates Spec `.en.md` + `.vi.md`; `dev-designer` generates HLD `<epic>.en.md` + `<epic>.vi.md` and **English-only** `bdd_scenarios.en.md` (deferring `bdd_scenarios.vi.md` until Stage 4).
   110	- **In-Flight Tolerance (`check_epic_readiness.py` & `check_bdd_traceability.py`)**: Keep Spec and HLD `.vi.md` on disk untouched for human reading; configure `check_epic_readiness.py` (in-flight default, with `--strict-bilingual` for Gate 5 / Finish) and `check_bdd_traceability.py` so Principal Review revisions to `.en.md` and deferred `bdd_scenarios.vi.md` do not block readiness (`R1`/`R3`/`R7`) mid-lifecycle, while removing `.vi.md` from `handoff.md` (`Read First`) and `run_external_review.py`.
   111	- **Stage 4 Pre-Finish Sync (`/finishing-a-development-branch`)**: Update Pre-Finish Hook (before archival commit in Options 1 and 2) to delta-sync `.en.md` edits into Spec/HLD `.vi.md`, generate `bdd_scenarios.vi.md` once, and validate the complete pair set with `check_document.py --require-toc --require-bilingual` and `check_epic_readiness.py --strict-bilingual`.
   112	
   113	### 4.7 Config-Driven Programmer Persona and Gemini 4 Hydrogen
   114	
   115	- **Configuration Source of Truth (`.devtool/review_config.json`)**: Add `"assistant"` and `"programmer"` entries to `DEFAULT_REVIEW_CONFIG["providers"]` in `run_external_review.py` and standardize `.devtool/review_config.json["providers"]["programmer"]` with default `model: "gemini-4-hydrogen-xhigh"` and `thinking_level: "xhigh"` (replacing hardcoded `Gemini Flash 3.8` defaults).
   116	- **Precedence & CLI Effort Mapping (`lifecycle_runner.py`)**: Add `resolve_programmer_model()` and `resolve_programmer_effort()` on `RunnerConfig` using strict precedence `CLI (--programmer-model / --programmer-effort) -> Runner --config JSON -> .devtool/review_config.json["providers"]["programmer"] -> env (AGY_PROGRAMMER_MODEL / AGY_PROGRAMMER_EFFORT) -> fallback ("gemini-4-hydrogen-xhigh", "xhigh")`; change `argparse` `--programmer-model` / `--programmer-effort` defaults to `None` so parser defaults do not shadow file configuration. Normalize effort aliases `"extra"`, `"extra-high"`, `"extra_high"`, and `"xhigh"` cleanly to the `agy` CLI `--effort xhigh` flag (`low|medium|high|xhigh|max`).
   117	- **Dynamic Prompts & Rule/Skill Alignment**: Update `resume_context.py` (`emit_handoff_prompt`), `rules/CRITICAL_RULES.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-lifecycle/references/autonomous-mode.md`, `skills/dev-implementation/SKILL.md`, and `skills/principal-review/SKILL.md` to read/reference `.devtool/review_config.json` (`providers.programmer`, default `gemini-4-hydrogen-xhigh`, effort `xhigh`) instead of hardcoding `Gemini Flash 3.8` (leaving quota bucket labels in `agy_quota.py` and the quota dashboard UI unchanged).
   118	
   119	## 5. Verification Strategy and Kit Invariants
   120	
   121	- Preserve all repository release checks via `bash scripts/verify.sh --full` (`42+` test suites, JSON manifest consistency, YAML frontmatter checks, relative link resolution, ToC anchor verification, Section 7 methodology source-fidelity checks, Section 8 unreferenced skill file checks, and `scripts/test_lifecycle_document_contract.py`).
   122	- Add targeted unit and integration tests covering:
   123	  - `test_run_external_review.py`: `-U5` diff context, Round 2 no-duplicate `base...sha`, quiet `collect_facts()` output, `.vi.md` exclusion, and `build/reviews/` raw stderr separation.
   124	  - `test_lifecycle_runner.py`: silent Gate 4 pass / 25-line failure truncation, worker pool parallel dispatch wiring, streamlined code fix path, `render_final_executive_report()`, and `resolve_programmer_model()` / `resolve_programmer_effort()` precedence with `"extra"` -> `"xhigh"` normalization.
   125	  - `test_check_epic_readiness.py` & `test_integrate_branch.py`: Option A deferred `bdd_scenarios.vi.md` during Principal Review vs `--strict-bilingual` enforcement at Stage 4 Finish, plus `check_task_contract.py` line-range validation.
   126	  - `test_resume_context.py` & `test_aggregate_quality_results.py`: `--compact` scoped startup output, config-driven `emit_handoff_prompt` Programmer model output, and `--compact` Gate 4 `GATE_PASS:` output format.
   127	- Measure before/after byte sizes of `CRITICAL_RULES.md`, `dev-designer/SKILL.md`, `resume_context.py --epic <slug> --compact`, and sample multi-round `principal_review.md` artefacts as quantitative regression assertions.
   128	
   129	## 6. Shared Contract Warnings
   130	
   131	No `shared-contracts/` directory exists in `ai-agent-tools` (this repository is the standalone agent workflow kit rather than a Hub/Satellite service pair). Internal kit contracts between scripts (`run_external_review.py`, `check_epic_readiness.py`, `verify_polyglot_registry.py`, `resume_context.py`, `lifecycle_runner.py`, and `integrate_branch.py`) and `.devtool/review_config.json` remain backward-compatible via optional flags and fallback defaults.
     1	# Token Throttling Optimization High-Level Design
     2	
     3	## Table of Contents
     4	
     5	- [Meta Data](#meta-data)
     6	- [Background](#background)
     7	- [Goals and Non-Goals](#goals-and-non-goals)
     8	- [Architecture and Technical Design](#architecture-and-technical-design)
     9	- [Feature Maintenance Map](#feature-maintenance-map)
    10	- [Module Contracts and CLI Interfaces](#module-contracts-and-cli-interfaces)
    11	- [Impact Analysis](#impact-analysis)
    12	- [Shared Contract Impact](#shared-contract-impact)
    13	- [Integration Test Plan and Boundary Matrix](#integration-test-plan-and-boundary-matrix)
    14	- [Verification Environment](#verification-environment)
    15	- [Comprehensive BDD Scenario Coverage](#comprehensive-bdd-scenario-coverage)
    16	- [Rollout Strategy and Mitigation](#rollout-strategy-and-mitigation)
    17	- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)
    18	- [Spec Errata](#spec-errata)
    19	
    20	## Meta Data
    21	
    22	- **Epic name**: `token_throttling_optimization`
    23	- **Status**: Draft
    24	- **PIC**: `danhdue`
    25	- **Target release**: Next plugin release
    26	- **Platform**: Python tooling and agent workflow kit
    27	- **Depends on epic**: none
    28	- **Source Spec**: [Approved Token Throttling Optimization Design Spec](2026-11-13-token-throttling-optimization-design.en.md)
    29	
    30	## Background
    31	
    32	End-to-end telemetry across `dev-lifecycle` (Interactive and `--autonomous`) showed quadratic token growth and rapid 5-hour quota depletion driven by five compounding causes:
    33	
    34	1. **Always-On Baseline Overhead**: `rules/CRITICAL_RULES.md` (`32,773` bytes / `239` lines) exceeds IDE truncation limits (`<truncated 8848 bytes>`), `skills/task-observer/SKILL.md` (`31,480` bytes) loads into worker subagents and headless CLIs without a guard, and `scripts/resume_context.py` dumps `26,759` bytes across all workspace repos.
    35	2. **Quadratic External Review Bloat**: `run_external_review.py` re-sends full `base...sha` diffs alongside `delta_round_context()` on Rounds `2+`, includes redundant `*.vi.md` documents, embeds full command output via `fact()` even on `exit 0`, uses `-U10` in `review-package`, and writes unfiltered CLI `stderr` transcripts directly into `principal_review.md` (`1.88 MB` measured).
    36	3. **Verbose Quality Gates and Uncapped Tracebacks**: `verify_polyglot_registry.py` dumps full JSON on `PASS`; `.agents/quality/python-quality.json` and `scaffold_quality_manifest.py` invoke `pytest` without `-q --tb=short --maxfail=3`; `run_task_checks.py` retains `40` lines; `lifecycle_runner.py` and `verify.sh` lack compact pass lines and 25-line failure tailing.
    37	4. **Coarse Reads, Sequential Tasks, and Hardcoded Legacy Models**: Task specs omit symbol/line-range windows for files over `200` lines; `lifecycle_runner.py` dispatches sequential `agy` calls with inline file text and hardcoded `gemini-3.8-flash` instead of config-driven `gemini-4-hydrogen-xhigh` (`--effort xhigh`); `step_cross_model_review()` wastes 3 LLM turns on unambiguous code bugs; `task-reviewer` runs on trivial mechanical tasks.
    38	5. **Upfront Bilingual Churn**: Maintaining synchronized Spec, HLD, and Gherkin `.vi.md` files throughout Principal Review doubles authoring and verification overhead before the English SSOT converges.
    39	
    40	## Goals and Non-Goals
    41	
    42	### Goals
    43	
    44	- Enforce all 5 Strict Token-Throttling Rules across runner scripts, verification tools, prompt templates, rules, and skill manifests across both Phase 1 (mechanical scripts) and Phase 2 (slimming, deduplication, task schema).
    45	- Adopt Option A Bilingual Workflow: retain Spec and HLD `.vi.md` for human gate reviews, exclude all `*.vi.md` files from AI review and coder handoffs, tolerate in-flight `.vi.md` drift and deferred `bdd_scenarios.vi.md` under default `check_epic_readiness.py`, and run a single Stage 4 Pre-Finish sync with `--strict-bilingual`.
    46	- Trigger `task-reviewer` selectively only for high-risk or multi-module tasks (`review_tier: "full"`, `security|architecture|concurrency|contract` labels, or `> 2` non-test modules).
    47	- Configure Role 2.3 (AI Programmer) via `.devtool/review_config.json["providers"]["programmer"]` and `RunnerConfig` precedence, upgrading the default to `gemini-4-hydrogen-xhigh` with effort normalized (`"extra"` / `"extra-high"` / `"xhigh"` -> `--effort xhigh`).
    48	- Enforce measurable size caps (`CRITICAL_RULES.md <= 8192` bytes, `dev-designer/SKILL.md <= 22528` bytes, `resume_context.py --compact --epic <slug> <= 4096` bytes) while preserving all kit release checks (`scripts/verify.sh --full`).
    49	
    50	### Non-Goals
    51	
    52	- Skipping human approval gates (Gate 1 Spec, Gate 2 Task Breakdown, Gate 5 Finish and Merge).
    53	- Disabling full test suites or `@quality_check` at the Final Convergence Gate or Stage 4 `verify-tier`.
    54	- Auto-pushing commits or branches without explicit user approval.
    55	- Altering backend quota bucket display labels (`Gemini 3.8 / Pro 5H`) in `scripts/agy_quota.py` or `quota_dashboard.html`.
    56	
    57	## Architecture and Technical Design
    58	
    59	### High-Level Architecture
    60	
    61	```mermaid
    62	flowchart TD
    63	    subgraph CFG["Configuration and Always-On Layer"]
    64	        RC[".devtool/review_config.json (providers.programmer)"]
    65	        CR["rules/CRITICAL_RULES.md (<= 8KB + Zero-Fluff Cap)"]
    66	        TO["skills/task-observer/SKILL.md (SUBAGENT-STOP)"]
    67	        MEM["scripts/resume_context.py (--compact + Dynamic Handoff)"]
    68	    end
    69	
    70	    subgraph S12["Stage 1 and Stage 2 Bilingual Option A"]
    71	        DESIGN["skills/dev-designer/SKILL.md (<= 22KB + target_files Ranges)"]
    72	        TC["check_task_contract.py (--design Line-Range Check)"]
    73	        READY["check_epic_readiness.py (In-Flight Default vs --strict-bilingual)"]
    74	        PKG["package_epic.py + handoff-template.md (English SSOT Read First)"]
    75	    end
    76	
    77	    subgraph REV["External Review Engine"]
    78	        RER["run_external_review.py (-U5 + Delta-Only R2+ + Quiet Facts + Raw Log)"]
    79	        REVP["review-package (-U5) + Diff-Only Prompts"]
    80	    end
    81	
    82	    subgraph EXEC["Stage 3 Runner and Gate 4"]
    83	        RUN["lifecycle_runner.py (Config Precedence + Pool + Fast Code Fix)"]
    84	        POOL["manage_worker_pool.py (2-Slot Ephemeral Wave Execution)"]
    85	        G4["verify_polyglot_registry.py (--compact) + run_task_checks.py (25-Line Tail)"]
    86	    end
    87	
    88	    subgraph FIN["Stage 4 Pre-Finish Hook"]
    89	        FINS["finishing-a-development-branch/SKILL.md (Delta-Sync .vi.md + Gen bdd_scenarios.vi.md)"]
    90	        DOC["check_document.py --require-toc --require-bilingual"]
    91	    end
    92	
    93	    RC --> RUN
    94	    RC --> MEM
    95	    CR --> RUN
    96	    TO --> RUN
    97	    MEM --> RUN
    98	    DESIGN --> TC --> READY --> RER --> PKG --> RUN
    99	    REVP --> RER
   100	    RUN --> POOL
   101	    RUN --> G4
   102	    G4 --> RER
   103	    RER --> FIN
   104	    FINS --> DOC --> READY
   105	```
   106	
   107	### Multi-Round Review and Selective Worker Flow
   108	
   109	```mermaid
   110	sequenceDiagram
   111	    autonumber
   112	    actor Dev as Developer (Role 2.1)
   113	    participant Des as dev-designer / Readiness
   114	    participant Rev as run_external_review.py
   115	    participant Run as lifecycle_runner.py
   116	    participant Pool as 2-Slot Worker / Subagent
   117	
   118	    Des->>Rev: HLD .en.md + bdd_scenarios.en.md + Tasks (.vi.md excluded)
   119	    Rev->>Rev: Run check_epic_readiness.py (Option A in-flight) + Delta -U5
   120	    Rev-->>Rev: Write verbose stderr to build/reviews/<epic>_roundN.raw.log
   121	    Dev->>Run: Approve Gate 2 -> AUTO MODE (Claude -> Codex -> Kiro -> Argon)
   122	    Run->>Run: Resolve programmer model (gemini-4-hydrogen-xhigh, --effort xhigh)
   123	    Run->>Pool: Dispatch disjoint task waves with path-only prompt + target ranges
   124	    Pool-->>Run: Commit task + Selective task-reviewer (high-risk only)
   125	    Run->>Run: verify_polyglot_registry.py --compact -> GATE_PASS or 25-line tail
   126	    Run->>Rev: Cross-Model Review (Round 1 full -U5; Round 2..3 delta prev_sha..sha only)
   127	    alt Clean code fix with no contract conflict
   128	        Run->>Pool: Direct Programmer fix + scoped test + 25-line tail
   129	    else Contract or architecture ambiguity
   130	        Run->>Run: Evaluate fix_plan_roundN.md via Role 2.2
   131	    end
   132	    Run->>Dev: Converged + Gate 4 PASS -> Request Gate 5 Finish Decision
   133	    Dev->>Des: Stage 4 Pre-Finish Hook (sync .vi.md + check_epic_readiness.py --strict-bilingual)
   134	```
   135	
   136	## Feature Maintenance Map
   137	
   138	| Capability | Canonical Source Paths and Entry Points | Core Invariants and Config Knobs | Extension and Troubleshooting Guide |
   139	|---|---|---|---|
   140	| **Diff-Only External Review** | `skills/dev-implementation/resources/scripts/run_external_review.py`, `skills/subagent-driven-development/scripts/review-package` | Uses `git diff -U5`; Round `>= 2` skips full `base...sha` diff when `delta_round_context` is active; excludes `*.vi.md`; truncates large diffs to `--stat` + `@@` hunks | Inspect `build/reviews/<epic>_round<n>.raw.log` for full CLI transcripts; check `MAX_DIFF_LINES` (`1500`) and `MAX_DIFF_BYTES` (`60000`) |
   141	| **Silent Gate 4 and Runners** | `skills/quality_check/resources/scripts/verify_polyglot_registry.py`, `skills/dev-implementation/resources/scripts/run_task_checks.py`, `scripts/verify.sh` | `--compact` prints `GATE_PASS: <id>` on pass and summary + 25-line tail on failure; `TAIL_LINES = 25`; `pytest -q --tb=short --maxfail=3` in `.agents/quality/python-quality.json` | Inspect full provider logs in `build/quality/<provider>/<cap>.log`; run `bash scripts/verify.sh --full` for verbose diagnostics |
   142	| **Option A Bilingual Guards** | `skills/dev-implementation/resources/scripts/check_epic_readiness.py`, `check_bdd_traceability.py`, `package_epic.py` | Default mode tolerates in-flight `.vi.md` drift and deferred `bdd_scenarios.vi.md`; `--strict-bilingual` enforces full parity at Stage 4; `handoff.md` excludes `*.vi.md` | Pass `--strict-bilingual` before Finish archival; verify Stage 4 hook in `finishing-a-development-branch/SKILL.md` |
   143	| **Surgical Target Line Ranges** | `skills/dev-implementation/resources/scripts/check_task_contract.py`, `skills/dev-designer/SKILL.md` | Tracked files `> 200` lines in `Allowed files` require `path :: Symbol (L<start>-L<end>)` anchors under `--design` | Check `check_task_contract.py --design` messages if a modified >200-line file lacks a symbol/line window |
   144	| **Config-Driven Programmer and Pool** | `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`, `manage_worker_pool.py`, `scripts/resume_context.py` | Precedence: `CLI -> Runner config -> .devtool/review_config.json -> env -> fallback ("gemini-4-hydrogen-xhigh", "xhigh")`; `"extra"` maps to `agy --effort xhigh` | Update `.devtool/review_config.json["providers"]["programmer"]` without editing code; check `PipelineState` in `.devtool/state/<epic>.pipeline.json` |
   145	| **Slim Rules and Scoped Memory** | `rules/CRITICAL_RULES.md`, `skills/task-observer/SKILL.md`, `skills/dev-designer/SKILL.md`, `skills/dev-lifecycle/references/` | `CRITICAL_RULES.md <= 8192` bytes; `dev-designer/SKILL.md <= 22528` bytes; `task-observer/SKILL.md` starts with `<SUBAGENT-STOP>`; `resume_context.py --compact --epic <slug> <= 4096` bytes | Run `bash scripts/verify.sh` and `scripts/test_lifecycle_document_contract.py` after any wording or reference split |
   146	| **Selective Task Reviewer** | `skills/dev-designer/SKILL.md`, `skills/dev-implementation/SKILL.md`, `skills/subagent-driven-development/SKILL.md` | Dispatch `task-reviewer` only for `review_tier: "full"`, high-risk labels (`security`, `architecture`, `concurrency`, `contract`), or `> 2` non-test modules | Add `review_tier: "full"` in task frontmatter when manual per-task code review is desired |
   147	
   148	## Module Contracts and CLI Interfaces
   149	
   150	These exact interfaces are frozen for implementation across tasks:
   151	
   152	1. **External Review and Config Defaults (`run_external_review.py`)**:
   153	   - `DEFAULT_REVIEW_CONFIG["providers"]` includes `"assistant"` (`"claude-opus-5-5-high"`, `"high"`) and `"programmer"` (`"gemini-4-hydrogen-xhigh"`, `"xhigh"`).
   154	   - `load_review_config(root: Path) -> dict[str, Any]` fills missing default providers and upgrades legacy programmer model IDs (`"gemini-3.8-flash"`, `"gemini-3.8-flash-high"`) to `"gemini-4-hydrogen-xhigh"` with `"thinking_level": "xhigh"`, while preserving any user-customized model ID.
   155	   - `build_diff_section(root, base, sha, max_lines=MAX_DIFF_LINES, max_bytes=MAX_DIFF_BYTES)` and `diff_range(...)`: use `git diff -U5`; when truncated over budget, include `git diff --stat` and `@@ ... @@` hunk headers per changed file instead of leaving empty hunks.
   156	   - `principal_artefact_lines(root, epic_dir)`: excludes all `*.vi.md` paths.
   157	   - `fact(label, code, out, err)`: returns `f"PASS: {label}\n"` on `code == 0`, or command + last 25 non-empty lines of combined output on failure/timeout.
   158	   - `render_round(...)`: writes full transcript to `build/reviews/<epic>_round<n>.raw.log` and references it cleanly inside markdown round tables (keeping existing round table columns compatible with `rounds_in` / `finding_rows` / `triage`).
   159	   - `run(args)`: for `round_num >= 2` with non-empty `delta_round_context()` (`not args.full`), omits full `base...sha` `diff_section` and injects a 1-line cumulative `git diff --stat` reference header.
   160	
   161	2. **Compact Quality Gates and Verification (`verify_polyglot_registry.py`, `run_task_checks.py`, `verify.sh`)**:
   162	   - `verify_polyglot_registry.py` accepts `--compact`: writes raw per-capability logs under `build/quality/<provider>/<cap>.log`, prints single-line `GATE_PASS: <provider_or_cap>` for passing checks/verdict, and on failure prints failing capability header + last 25 lines of its `.log`.
   163	   - `run_task_checks.py` sets `TAIL_LINES = 25`.
   164	   - `.agents/quality/python-quality.json` and `scaffold_quality_manifest.py` append `"-q", "--tb=short", "--maxfail=3"` to pytest commands.
   165	   - `scripts/verify.sh` accepts `--quiet` (single-line status per section, 25-line failure tail) while keeping `--full` unchanged.
   166	
   167	3. **Option A Bilingual Readiness, Surgical Checks, and Scoped Memory**:
   168	   - `check_epic_readiness.py` and `check_bdd_traceability.py` accept `--strict-bilingual` (default `False` during active development/Principal Review). Default skips `R1`/`R3`/`R7` failures caused solely by `.en.md`/`.vi.md` drift or missing `bdd_scenarios.vi.md`; `--strict-bilingual` enforces full bilingual parity.
   169	   - `package_epic.py` & `handoff-template.md` list only `.en.md` / English docs under `Read First`.
   170	   - `check_task_contract.py --design` inspects non-new tracked source/script files `> 200` lines listed under `Allowed files` and requires explicit target symbol/line anchors (`:: <Symbol> (L<start>-L<end>)` or `(L<start>-L<end>)`) in `## Files` or `## Impact Analysis & Blast Radius`.
   171	   - `scripts/resume_context.py` adds `--compact` (auto-scoped when `--epic <slug>` is passed) returning active epic snapshot, current repo git status, relevant open RFCs, and matching epic tasks (`<= 4096` bytes); `emit_handoff_prompt` reads `.devtool/review_config.json["providers"]["programmer"]` with fallback `gemini-4-hydrogen-xhigh` (`xhigh`).
   172	
   173	4. **Lifecycle Runner and Config-Driven Programmer Persona (`lifecycle_runner.py`)**:
   174	   - `RunnerConfig` replaces hardcoded `"gemini-3.8-flash"` defaults with `"gemini-4-hydrogen-xhigh"` / `"xhigh"` fallback, adds `normalize_agy_effort(raw: str) -> str` mapping `{"extra", "extra-high", "extra_high", "xhigh"}` -> `"xhigh"`, and adds `resolve_programmer_model(self, root: Path | None = None) -> str` and `resolve_programmer_effort(self, root: Path | None = None) -> str` following:
   175	     `CLI (--programmer-model / --programmer-effort) -> Runner --config JSON -> .devtool/review_config.json["providers"]["programmer"] -> env (AGY_PROGRAMMER_MODEL / AGY_PROGRAMMER_EFFORT) -> fallback ("gemini-4-hydrogen-xhigh", "xhigh")`.
   176	   - `main()` sets `argparse` defaults `default=None` for `--programmer-model` and `--programmer-effort` so CLI flags override config only when explicitly supplied.
   177	   - `_tail_lines(text: str, limit: int = 25) -> str` truncates failures cleanly in `run_gate4()` and `run_intermediate_check()`.
   178	   - `step_implementation()` uses `manage_worker_pool.py` to run independent topological waves concurrently; `_execute_single_task()` passes file paths + target read-range rules + Zero-Fluff output cap instead of inlining task contents.
   179	   - `step_cross_model_review()` fast-tracks verified code fixes directly to `_apply_code_fixes()` when no `shared-contracts/` or architecture ambiguity exists, reserving `_draft_fix_plan()` + `evaluate_programmer_fix_plan()` for design/contract ambiguity.
   180	   - `render_final_executive_report()` parses actual highest-risk findings and SHAs from `review_results.md` / `principal_review.md`.
   181	
   182	## Impact Analysis
   183	
   184	- Shift-Left `check_code_impact.py --files ... --base-ref main` reported:
   185	  - **Upstream Git Conflicts**: `CLEAN` (`0` unmerged commits against `main`).
   186	  - **Cross-Platform Bridges**: None.
   187	  - **Coverage Safety Nets**: Paired test suites exist for `resume_context.py`, `run_external_review.py`, `lifecycle_runner.py`, `verify_polyglot_registry.py`, and `check_epic_readiness.py`; `rules/CRITICAL_RULES.md` is verified via `scripts/test_lifecycle_document_contract.py` and `scripts/verify.sh` §3/§5b/§7/§8.
   188	
   189	## Shared Contract Impact
   190	
   191	None — self-contained feature. Repository `ai-agent-tools` does not contain a `shared-contracts/` directory; internal CLI flags (`--compact`, `--strict-bilingual`, `--quiet`, `--programmer-effort`) maintain backward compatibility via optional/default values.
   192	
   193	## Integration Test Plan and Boundary Matrix
   194	
   195	```text
   196	Integration test roots: tests
   197	Protected paths: .agents/quality/**, .devtool/epic/token_throttling_optimization/bdd_scenarios.en.md, .devtool/epic/token_throttling_optimization/bdd_scenarios.vi.md
   198	Integration results: python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/token-throttling-optimization.xml tests/test_tto_external_review.py tests/test_polyglot_gate4.py tests/test_tto_bilingual_and_surgical.py tests/test_lifecycle_runner.py tests/test_tto_docs_and_slimming.py tests/test_token_throttling_acceptance.py -> build/test-results/token-throttling-optimization.xml
   199	```
   200	
   201	| Boundary | Real Components | Isolation or Fixture | Required Assertions |
   202	|---|---|---|---|
   203	| **Diff-Only External Review** | `run_external_review.py`, `review-package` | Temp git repos with multi-round history and fake CLI binaries on `PATH` | `-U5` diff context, Round 2 omits full `base...sha`, `.vi.md` excluded, `PASS:` single-line facts, `build/reviews/*.raw.log` written |
   204	| **Compact Gate 4 and Runners** | `verify_polyglot_registry.py`, `run_task_checks.py`, `scaffold_quality_manifest.py`, `verify.sh` | Temp registry manifests + mock command exits (`0` and `1`) | `--compact` emits `GATE_PASS:` on pass and summary + `<= 25` lines on fail; `TAIL_LINES == 25`; `-q --tb=short --maxfail=3` injected |
   205	| **Option A Bilingual and Surgical Guards** | `check_epic_readiness.py`, `check_bdd_traceability.py`, `check_task_contract.py`, `package_epic.py`, `resume_context.py` | Synthetic temp epic dirs with `.en.md`/`.vi.md` diffs, missing `bdd_scenarios.vi.md`, and `> 200` line files | Default in-flight passes without `bdd_scenarios.vi.md`; `--strict-bilingual` fails until synced; missing line range rejected; `--compact <= 4096` bytes |
   206	| **Config-Driven Runner and Worker Pool** | `lifecycle_runner.py`, `manage_worker_pool.py` | Mock `agy` dispatcher + temp git repo + worktree pool slots | Precedence resolves `gemini-4-hydrogen-xhigh` & normalizes `"extra"` -> `"xhigh"`; path-only prompt; parallel pool wave execution; dynamic executive report |
   207	| **Slim Rules, Skills, and Release Contracts** | `CRITICAL_RULES.md`, `dev-designer/SKILL.md`, `task-observer/SKILL.md`, `finishing-a-development-branch/SKILL.md` | Live repository files validated against byte/word limits & `verify.sh` | `CRITICAL_RULES.md <= 8192` B, `dev-designer/SKILL.md <= 22528` B, `<SUBAGENT-STOP>` present, all contract tokens and §1–§10 checks pass |
   208	
   209	## Verification Environment
   210	
   211	- Tests execute in isolated temporary directories (`tempfile.TemporaryDirectory` / pytest `tmp_path`) against synthetic git repositories and fake CLI shims on `PATH`.
   212	- Zero live external API credentials, network calls, or mutations to user Antigravity profiles occur during test execution.
   213	- Live JUnit XML reports are written strictly to git-ignored `build/test-results/` and raw review/quality logs to `build/reviews/` and `build/quality/`.
   214	- Local workspace `.devtool/review_config.json` (git-ignored runtime config) is never modified inside unit tests; tests write config fixtures only inside `tmp_path`.
   215	
   216	## Comprehensive BDD Scenario Coverage
   217	
   218	The canonical Gherkin scenarios live in [BDD scenarios](bdd_scenarios.en.md) with synchronized translation in [Vietnamese BDD scenarios](bdd_scenarios.vi.md).
   219	
   220	| Dimension | Scenario IDs | Coverage Intent |
   221	|---|---|---|
   222	| **Happy Paths** | `TTO-HP-01` through `TTO-HP-08` | `-U5` delta review, `--compact` Gate 4, Option A in-flight readiness, config-driven `gemini-4-hydrogen-xhigh` (`xhigh`), slimmed rules/skills, `--compact` context, streamlined fix loop, E2E token optimization |
   223	| **Edge Cases and Boundaries** | `TTO-EC-01` through `TTO-EC-06` | Truncated diff `--stat` + `@@` hunks, `TAIL_LINES=25` + quiet pytest flags, `> 200`-line file range check, effort alias normalization, selective `task-reviewer` criteria, full `verify.sh` §1–§17 pass |
   224	| **State Transitions and Invariants** | `TTO-ST-01` through `TTO-ST-05` | `load_review_config` migration, `handoff.md` `.vi.md` exclusion, `--strict-bilingual` Gate 5 enforcement, Role 2.2 escalation on contract conflict, Stage 4 Pre-Finish sync hook |
   225	| **Async and Concurrency** | `TTO-AR-01` through `TTO-AR-02` | Parallel topological wave dispatch via `manage_worker_pool.py`, round raw-log isolation and clean cross-task session boundaries |
   226	| **Failure and Resilience** | `TTO-FR-01` through `TTO-FR-04` | Quiet `collect_facts` 25-line failure tail, compact Gate 4 failure 25-line tail, `_tail_lines` Gate 4 failure truncation, quantitative byte-size regression bounds |
   227	
   228	## Rollout Strategy and Mitigation
   229	
   230	1. **Wave 1 (Disjoint Foundations — Tasks 1, 2, 3)**: Land Diff-Only External Review (`run_external_review.py`, `review-package`), Compact Gate 4 & Runners (`verify_polyglot_registry.py`, `run_task_checks.py`, `verify.sh --quiet`), and Option A / Surgical Contract / Scoped Memory (`check_epic_readiness.py`, `check_task_contract.py`, `resume_context.py`).
   231	2. **Wave 2 (Orchestration and Slimming — Tasks 4, 5)**: Land Config-Driven `lifecycle_runner.py` (`gemini-4-hydrogen-xhigh`, `--effort xhigh`, pool concurrency, fast code-fix path) alongside Rules, Skills, Reference Consolidation, and Stage 4 Pre-Finish Hook updates.
   232	3. **Wave 3 (Integration and Regression Suite — Task 6)**: Add quantitative token-throttling E2E regression checks (`test_token_throttling_acceptance.py`), register new suites in `scripts/verify.sh`, and verify full release checks.
   233	
   234	Mitigation: All new compact/quiet flags (`--compact`, `--quiet`) preserve verbose/full fallback paths (`--full` on `verify.sh` and `run_external_review.py`), and `--strict-bilingual` stays optional until Stage 4 so in-flight workflows never break backward compatibility.
   235	
   236	## Kanban Tasks Breakdown
   237	
   238	1. **Task 1: Diff-Only External Review and Transcript Isolation** (`task_01_diff_only_external_review_and_transcript_isolation.md`) — Covers: `TTO-HP-01, TTO-EC-01, TTO-ST-01, TTO-FR-01`
   239	2. **Task 2: Silent Gate 4 and Truncated Test Runners** (`task_02_silent_gate4_and_truncated_test_runners.md`) — Covers: `TTO-HP-02, TTO-EC-02, TTO-FR-02`
   240	3. **Task 3: Option A Bilingual Guards, Surgical Contracts, and Compact Memory** (`task_03_option_a_bilingual_and_surgical_contract_guards.md`) — Covers: `TTO-HP-03, TTO-HP-06, TTO-EC-03, TTO-ST-02, TTO-ST-03`
   241	4. **Task 4: Config-Driven Programmer Persona, Pool Dispatch, and Runner Optimization** (`task_04_lifecycle_runner_programmer_config_and_pool_isolation.md`) — Covers: `TTO-HP-04, TTO-HP-07, TTO-EC-04, TTO-ST-04, TTO-AR-01, TTO-FR-03`
   242	5. **Task 5: Rules and Skills Slimming, Deduplication, Selective Reviewer, and Pre-Finish Sync** (`task_05_slimming_rules_skills_dedup_and_selective_reviewer.md`) — Covers: `TTO-HP-05, TTO-EC-05, TTO-ST-05`
   243	6. **Task 6: Token Throttling Acceptance and Quantitative Regression Suite** (`task_06_integration_and_regression_verification.md`) — Covers: `TTO-HP-08, TTO-EC-06, TTO-AR-02, TTO-FR-04`
   244	
   245	## Spec Errata
   246	
   247	None.

 succeeded in 0ms:
     1	---
     2	id: "task_03_option_a_bilingual_and_surgical_contract_guards"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "token_throttling_optimization"
     7	dueDate: null
     8	created: "2026-11-13T02:30:00Z"
     9	modified: "2026-11-13T02:30:00Z"
    10	completedAt: null
    11	labels: ["bilingual", "contract", "memory", "token-optimization"]
    12	order: "a3"
    13	---
    14	
    15	# Task 3: Option A Bilingual Guards, Surgical Contracts, and Compact Memory
    16	
    17	Epic: [token_throttling_optimization](token_throttling_optimization.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Implement Option A Bilingual Workflow guards, Surgical Target Line Range enforcement (`Rule 3`), and Scoped/Compact Memory (`--compact` + dynamic programmer prompt):
    22	1. **Option A Bilingual Readiness & Traceability Guards**:
    23	   - Add `--strict-bilingual` (default `False`) to `skills/dev-implementation/resources/scripts/check_epic_readiness.py` (`main`, `run_checks`, `check_preflight`, `check_bdd_scenarios`, `check_metadata`).
    24	   - Add `--strict-bilingual` (default `False`) to `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` (`main`, `load_scenarios`, `check_plan`).
    25	   - In default in-flight mode (`--strict-bilingual` unset):
    26	     - Tolerate in-flight `.vi.md` drift on `R1` (`check_document.py`), `R3` (`check_bdd_scenarios`), and `R7` (`check_metadata` when checking `.vi.md` parity), and tolerate an absent `bdd_scenarios.vi.md` during Stage 2/3 development while still enforcing `.vi.md` pairing on present documents where existing parity tests require strict checks or gating under `--strict-bilingual`.
    27	     - When `bdd_scenarios.vi.md` is present during active runs, default `check_epic_readiness` only enforces `.vi.md` strict parity when `--strict-bilingual` is passed (and preserves `test_check_bdd_traceability` / `test_check_epic_readiness` assertions explicitly testing `--strict-bilingual` or existing `.en.md` invariants).
    28	   - Under `--strict-bilingual` (Stage 4 Pre-Finish): require complete `.en.md`/`.vi.md` parity across spec, HLD, metadata, ToC, and `bdd_scenarios.vi.md`.
    29	2. **Exclude `.vi.md` from AI Coder Handoffs**:
    30	   - Update `skills/dev-implementation/resources/scripts/package_epic.py` (`render_initial_handoff`, `revise_handoff_text`) and `skills/dev-lifecycle/references/handoff-template.md` so `Read First` contains strictly English SSOT paths (`<epic_dir>.en.md`, `bdd_scenarios.en.md`, `principal_review.md`) and zero `*.vi.md` files, while preserving all contract guardrails required by `scripts/test_lifecycle_document_contract.py` and `scripts/test_resume_context.py` (`resume_context.py`, `[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]`, 4 Execution Guardrails, `principal_review.md`).
    31	3. **Surgical File Reading Gate (`check_task_contract.py --design`)**:
    32	   - Inspect non-new tracked source/script files exceeding `200` lines listed under `Allowed files:` when `--design` is passed.
    33	   - Require explicit symbol and/or `(L<start>-L<end>)` line-range anchors for each such `> 200`-line file inside `## Impact Analysis & Blast Radius` or `## Files`.
    34	4. **Scoped `--compact` Context Restoration & Dynamic Programmer Prompt (`scripts/resume_context.py`)**:
    35	   - Add `--compact` (auto-scoped when `--epic <slug>` is passed) emitting `<= 4096` bytes containing only active epic snapshot, current repo git status, matching epic tasks, and relevant open RFCs.
    36	   - Update `emit_handoff_prompt()` to resolve Role 2.3's recommended model and effort dynamically from `.devtool/review_config.json["providers"]["programmer"]` with fallback `gemini-4-hydrogen-xhigh` (`xhigh`) instead of hardcoded `Gemini Flash 3.8`.
    37	5. Add `tests/test_tto_bilingual_and_surgical.py` covering `TTO-HP-03`, `TTO-HP-06`, `TTO-EC-03`, `TTO-ST-02`, and `TTO-ST-03`, updating paired script test files as needed.
    38	
    39	## Files
    40	
    41	Allowed files:
    42	- `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
    43	- `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py`
    44	- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`
    45	- `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`
    46	- `skills/dev-implementation/resources/scripts/check_task_contract.py`
    47	- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
    48	- `skills/dev-implementation/resources/scripts/package_epic.py`
    49	- `skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py`
    50	- `skills/dev-lifecycle/references/handoff-template.md`
    51	- `scripts/resume_context.py`
    52	- `scripts/test_resume_context.py`
    53	- `tests/test_tto_bilingual_and_surgical.py` (new)
    54	
    55	Read-only context:
    56	- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Module Contracts (§3)
    57	- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios
    58	- `scripts/test_lifecycle_document_contract.py` — Contract strings asserted on `handoff-template.md`
    59	
    60	## Design Rationale
    61	
    62	Decoupling in-flight `.vi.md` translation synchronization until Stage 4 prevents double rework during Principal Review rounds, while `--compact` context restoration and `> 200`-line target range validation eliminate cold-start and whole-file reading bloat in Stage 3. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.
    63	
    64	## Impact Analysis & Blast Radius
    65	
    66	- **Target Files & Symbols**:
    67	  - `skills/dev-implementation/resources/scripts/check_epic_readiness.py`: `check_preflight` (L110-L203), `check_bdd_scenarios` (L314-L343), `check_metadata` (L645-L752), `run_checks` (L830-L852), `main` (L952-L1016)
    68	  - `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`: `load_scenarios` (L82-L100), `check_plan` (L113-L127), `main` (L228-L261)
    69	  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `check_allowed` (L127-L154), `check_task` (L394-L417), `main` (L507-L562)
    70	  - `skills/dev-implementation/resources/scripts/package_epic.py`: `render_initial_handoff` (L78-L116), `revise_handoff_text` (L119-L183), `package_epic` (L211-L300)
    71	  - `scripts/resume_context.py`: `collect_harvest_data` (L1133-L1261), `emit_handoff_prompt` (L1271-L1337), `parse_args` (L1510-L1662), `main` (L1665-L1842)
    72	  - `tests/test_tto_bilingual_and_surgical.py`: new unit and integration tests for `TTO-HP-03`, `TTO-HP-06`, `TTO-EC-03`, `TTO-ST-02`, `TTO-ST-03`
    73	- **Downstream Callers**: `skills/dev-implementation/resources/scripts/run_external_review.py` (`check_epic_readiness.py` preflight), `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`--compact` resume, `package_epic.py`), `skills/finishing-a-development-branch/SKILL.md` (`--strict-bilingual` Stage 4 gate).
    74	- **Cross-Platform Bridges**: None.
    75	- **Target Test Coverage Threshold**: 100% of default vs `--strict-bilingual` mode branches, `> 200`-line surgical check paths, and `--compact` byte-budget bounds.
    76	
    77	### BDD SCENARIOS
    78	
    79	Covers: TTO-HP-03, TTO-HP-06, TTO-EC-03, TTO-ST-02, TTO-ST-03
    80	
    81	```gherkin
    82	Scenario: [TTO-HP-03] [Tier C - Integration] Option A default readiness tolerates in-flight .vi.md drift and deferred bdd_scenarios.vi.md
    83	
    84	Given an epic directory containing current *.en.md design docs and bdd_scenarios.en.md
    85	And bdd_scenarios.vi.md is absent while an existing .vi.md companion has un-synced sections during active Principal Review
    86	When check_epic_readiness.py runs without --strict-bilingual
    87	Then the readiness gate succeeds with status PASS on R1, R3, and R7 without failing on .vi.md drift or missing bdd_scenarios.vi.md
    88	And check_bdd_traceability.py validates task coverage solely against bdd_scenarios.en.md
    89	
    90	Scenario: [TTO-HP-06] [Tier C - Integration] Compact context restoration caps output at 4096 bytes and reads programmer config dynamically
    91	
    92	Given a multi-repo workspace directory with active epic metadata, tasks, and open RFC entries
    93	And .devtool/review_config.json configures providers.programmer to "gemini-4-hydrogen-xhigh" with thinking_level "xhigh"
    94	When scripts/resume_context.py runs with --compact --epic token_throttling_optimization and --emit-prompt implement
    95	Then the compact context payload measures at most 4096 bytes and includes active epic snapshot, current repo git status, matching tasks, and relevant open RFCs
    96	And the emitted handoff prompt specifies "gemini-4-hydrogen-xhigh" and "xhigh" read dynamically from .devtool/review_config.json
    97	
    98	Scenario: [TTO-EC-03] [Tier C - Integration] Design contract checker rejects large >200-line modified files lacking target symbol or line-range anchors
    99	
   100	Given a task file referencing a non-new tracked Python source file exceeding 200 lines in Allowed files
   101	And the task's Files and Impact Analysis sections omit any target symbol name or (L<start>-L<end>) line range for that file
   102	When check_task_contract.py executes with --design against that task file
   103	Then check_task_contract.py exits non-zero and reports the missing symbol or line-range anchor for that >200-line file
   104	And adding a valid "path :: Symbol (L10-L85)" anchor clears the violation and exits with status 0
   105	
   106	Scenario: [TTO-ST-02] [Tier C - Integration] Handoff package and template exclude .vi.md files from AI coder Read First list
   107	
   108	Given an epic directory containing spec.en.md, spec.vi.md, epic.en.md, epic.vi.md, bdd_scenarios.en.md, and bdd_scenarios.vi.md
   109	When package_epic.py generates handoff.md from skills/dev-lifecycle/references/handoff-template.md
   110	Then the generated Read First section references only *.en.md documents and zero *.vi.md paths
   111	And handoff-template.md contains no static legacy model hardcodes conflicting with config-driven Role 2.3 selection
   112	
   113	Scenario: [TTO-ST-03] [Tier C - Integration] Stage 4 --strict-bilingual readiness gate enforces full .en.md and .vi.md parity
   114	
   115	Given an epic directory whose .vi.md HLD has drifted behind .en.md or lacks bdd_scenarios.vi.md
   116	When check_epic_readiness.py runs with --strict-bilingual and check_bdd_traceability.py runs with --strict-bilingual
   117	Then both commands exit non-zero highlighting the missing or out-of-sync Vietnamese mirror files
   118	And after synchronizing .vi.md and adding bdd_scenarios.vi.md with matching IDs and ToC headings, both --strict-bilingual checks exit with status 0
   119	```
   120	
   121	## Verification
   122	
   123	| ID | Phase | Command | Expect | Needs |
   124	|----|-------|---------|--------|-------|
   125	| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_bilingual_and_surgical.py::test_tto_hp_03_option_a_default_readiness` | exit 1; contains "failed" | — |
   126	| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_bilingual_and_surgical.py::test_tto_hp_03_option_a_default_readiness` | exit 0; contains "passed" | — |
   127	| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_bilingual_and_surgical.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py skills/dev-implementation/resources/scripts/test_check_task_contract.py skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py scripts/test_resume_context.py` | exit 0; contains "passed" | — |
   128	| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/package_epic.py scripts/resume_context.py tests/test_tto_bilingual_and_surgical.py` | exit 0 | — |
   129	| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/package_epic.py scripts/resume_context.py tests/test_tto_bilingual_and_surgical.py` | exit 0 | — |
   130	| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_3.xml tests/test_tto_bilingual_and_surgical.py` | exit 0; results build/test-results/task_3.xml | — |
   131	
   132	## Stop and Report If
   133	
   134	- A command, path, symbol or anchor named in this task does not match the repository.
   135	- A Verification row fails for a reason other than its Expect.
   136	- The work needs a change to a file outside Allowed files, or to a protected path.
   137	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
   138	  Covers line.
   139	- A variable named in the Needs column is unset.
   140	
   141	## Decisions Already Made
   142	
   143	- `check_epic_readiness.py` (`run_checks` L830-L852, `main` L952-L1016) and `check_bdd_traceability.py` (`load_scenarios` L82-L100, `main` L228-L261) add `--strict-bilingual` (default `False`). Without `--strict-bilingual`, in-flight checks validate English SSOT docs/BDDs cleanly and tolerate `.vi.md` drift or missing `bdd_scenarios.vi.md`; with `--strict-bilingual`, full `.en.md`/`.vi.md` parity is mandatory.
   144	- `package_epic.py` (`render_initial_handoff` L78-L116, `revise_handoff_text` L119-L183) and `skills/dev-lifecycle/references/handoff-template.md` list only English SSOT paths in `Read First`, while keeping required tokens from `scripts/test_lifecycle_document_contract.py` (`principal_review.md`, 4 Execution Guardrails, `or \`uncommitted\` when \`auto_commit\` is false`, `git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>`) and `scripts/test_resume_context.py` (`resume_context.py`, `[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]`).
   145	- `check_task_contract.py --design` (`check_task` L394-L417) requires explicit symbol or line-range anchor (`L<start>-L<end>`) in `## Files` or `## Impact Analysis & Blast Radius` for every non-new tracked source/script file exceeding `200` lines in `Allowed files`.
   146	- `scripts/resume_context.py --compact --epic <slug>` enforces output size `<= 4096` bytes and `emit_handoff_prompt` reads `.devtool/review_config.json["providers"]["programmer"]` with fallback `("gemini-4-hydrogen-xhigh", "xhigh")`.
   147	
   148	## Definition of Done
   149	
   150	- Scenarios TTO-HP-03, TTO-HP-06, TTO-EC-03, TTO-ST-02, and TTO-ST-03 pass end-to-end. (V2, V3, V6)
   151	- Legacy tests for readiness, traceability, contract checking, packaging, and resume context remain passing. (V3)
   152	- Python ruff lint and mypy strict type checks exit 0. (V4, V5)
   153	- `handoff-template.md` contract guardrails preserved cleanly under visual inspection. (Gate 5)
   154	
   155	## Dependencies & Blockers
   156	
   157	None. Blocks [Task 4](task_04_lifecycle_runner_programmer_config_and_pool_isolation.md) and [Task 5](task_05_slimming_rules_skills_dedup_and_selective_reviewer.md).
   158	
   159	## References & Rollback
   160	
   161	- [Epic HLD](token_throttling_optimization.en.md), Module Contracts (§3).
   162	- **Rollback**: Revert task commit; restores prior readiness, traceability, contract, packaging, and context scripts.
   163	
     1	---
     2	id: "task_04_lifecycle_runner_programmer_config_and_pool_isolation"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "token_throttling_optimization"
     7	dueDate: null
     8	created: "2026-11-13T02:30:00Z"
     9	modified: "2026-11-13T02:30:00Z"
    10	completedAt: null
    11	labels: ["lifecycle-runner", "worker-pool", "config", "token-optimization"]
    12	order: "a4"
    13	---
    14	
    15	# Task 4: Config-Driven Programmer Persona, Pool Dispatch, and Runner Optimization
    16	
    17	Epic: [token_throttling_optimization](token_throttling_optimization.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Upgrade `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` and `skills/dev-implementation/resources/scripts/manage_worker_pool.py` to enforce clean per-task session isolation (`Rule 4`), path-only Zero-Fluff worker prompts (`Rule 3`, `Rule 5`), config-driven Gemini 4 Hydrogen Role 2.3 resolution, Gate 4 25-line failure tailing (`Rule 2`), concurrent wave dispatch, and streamlined cross-model code-fix execution:
    22	1. **Config-Driven Role 2.3 Model & Effort Precedence (`RunnerConfig` + `main`)**:
    23	   - Replace hardcoded `"gemini-3.8-flash"` defaults with `"gemini-4-hydrogen-xhigh"` and `"xhigh"` fallback.
    24	   - Add `normalize_agy_effort(raw: str) -> str` mapping `"extra"`, `"extra-high"`, `"extra_high"`, and `"xhigh"` (case-insensitive) to `"xhigh"`.
    25	   - Implement `RunnerConfig.resolve_programmer_model(self, root: Path | None = None) -> str` and `RunnerConfig.resolve_programmer_effort(self, root: Path | None = None) -> str` following:
    26	     `CLI (--programmer-model / --programmer-effort) -> Runner --config JSON -> .devtool/review_config.json["providers"]["programmer"] -> env (AGY_PROGRAMMER_MODEL / AGY_PROGRAMMER_EFFORT) -> fallback ("gemini-4-hydrogen-xhigh", "xhigh")`.
    27	   - Update `main()` so `argparse` uses `default=None` for `--programmer-model` and add `--programmer-effort` (`default=None`), ensuring CLI overrides config only when explicitly passed.
    28	   - Update startup `probe_model()` and `_execute_single_task()` / `_apply_code_fixes()` to pass resolved model and normalized `--effort` to `ModelDispatcher.dispatch()`.
    29	2. **Parallel Worker Pool Execution & Path-Only Zero-Fluff Prompts**:
    30	   - Refactor `step_implementation()` to consume `compute_execution_order.py --parallel` waves and execute disjoint tasks concurrently inside 2-slot worktrees via `manage_worker_pool.py` (`init_slots`, `sync_slot`, `merge_slot`, `cleanup_slots`).
    31	   - Refactor `_execute_single_task()` so each task starts in a clean session context passing ONLY the task file path, target file paths + line ranges, and the Zero-Fluff output cap (no inlined task markdown or large source bodies).
    32	   - Ensure `run_gate4()` invokes `--compact` on polyglot/Gate 4 commands where available and uses `_tail_lines(output, 25)` on failures in both `run_gate4()` and `run_intermediate_check()`.
    33	3. **Streamlined Cross-Model Fix Loop & Real Executive Report**:
    34	   - Update `step_cross_model_review()`: when verified findings are pure code fixes with zero `shared-contracts/` or architecture ambiguity (via `_has_domain_or_critical_conflict`), route directly to `_apply_code_fixes()` without extra `_draft_fix_plan()` / `evaluate_programmer_fix_plan()` LLM round-trips; preserve Role 2.2 escalation whenever `shared-contracts/` or architecture ambiguity exists.
    35	   - Replace placeholder strings in `render_final_executive_report()` with parsed Top 3 Highest-Risk Findings and candidate SHAs read from `review_results.md` / `principal_review.md`.
    36	4. Update `tests/test_lifecycle_runner.py` (including RED/GREEN coverage for `TTO-HP-04`, `TTO-HP-07`, `TTO-EC-04`, `TTO-ST-04`, `TTO-AR-01`, `TTO-FR-03` alongside updated model expectations).
    37	
    38	## Files
    39	
    40	Allowed files:
    41	- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`
    42	- `skills/dev-implementation/resources/scripts/manage_worker_pool.py`
    43	- `tests/test_lifecycle_runner.py`
    44	
    45	Read-only context:
    46	- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Module Contracts (§4)
    47	- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios
    48	- `skills/dev-implementation/resources/scripts/run_external_review.py` — Config loader & upgrade helper
    49	- `skills/dev-implementation/resources/scripts/compute_execution_order.py` — Topological parallel wave generator
    50	
    51	## Design Rationale
    52	
    53	Centralizing Role 2.3 resolution into `RunnerConfig` mirrors `resolve_assistant_model` while upgrading the default coding engine to `gemini-4-hydrogen-xhigh` (`--effort xhigh`) with zero hardcoded scattered strings. Running disjoint DAG waves concurrently across isolated pool slots with path-only prompts stops context snowballing across tasks while eliminating sequential wait time. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.
    54	
    55	## Impact Analysis & Blast Radius
    56	
    57	- **Target Files & Symbols**:
    58	  - `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`: `RunnerConfig` (L44-L80), `ModelDispatcher` (L119-L205), `LifecycleRunner._execute_single_task` (L432-L509), `LifecycleRunner.step_implementation` (L884-L908), `LifecycleRunner.run_gate4` (L910-L1049), `LifecycleRunner.run_intermediate_check` (L1051-L1078), `LifecycleRunner.step_cross_model_review` (L1220-L1336), `LifecycleRunner.render_final_executive_report` (L1338-L1362), `main` (L1365-L1414), new `normalize_agy_effort`, new `_tail_lines`
    59	  - `skills/dev-implementation/resources/scripts/manage_worker_pool.py`: `init_slots` (L68-L106), `sync_slot` (L109-L119), `merge_slot` (L122-L136)
    60	  - `tests/test_lifecycle_runner.py`: unit and integration tests covering `TTO-HP-04`, `TTO-HP-07`, `TTO-EC-04`, `TTO-ST-04`, `TTO-AR-01`, `TTO-FR-03`
    61	- **Downstream Callers**: `skills/dev-lifecycle/SKILL.md`, `skills/dev-lifecycle/references/autonomous-mode.md`, `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`.
    62	- **Cross-Platform Bridges**: None.
    63	- **Target Test Coverage Threshold**: 100% of config precedence branches, effort alias normalization, worker pool wave dispatch, and Role 2.2 escalation paths.
    64	
    65	### BDD SCENARIOS
    66	
    67	Covers: TTO-HP-04, TTO-HP-07, TTO-EC-04, TTO-ST-04, TTO-AR-01, TTO-FR-03
    68	
    69	```gherkin
    70	Scenario: [TTO-HP-04] [Tier A - Unit] RunnerConfig resolves Role 2.3 programmer model and effort using config precedence
    71	
    72	Given a .devtool/review_config.json defining providers.programmer.model as "gemini-4-hydrogen-xhigh" and thinking_level as "extra"
    73	And AGY_PROGRAMMER_MODEL environment override is unset
    74	When lifecycle_runner.RunnerConfig resolves the programmer model and effort with no CLI flag supplied
    75	Then resolve_programmer_model returns "gemini-4-hydrogen-xhigh" and resolve_programmer_effort returns "xhigh"
    76	And supplying --programmer-model "gemini-4-pro-high" via CLI overrides both .devtool/review_config.json and environment variables
    77	
    78	Scenario: [TTO-HP-07] [Tier C - Integration] Streamlined cross-model review fast-tracks clean code fixes and renders actual Executive Report findings
    79	
    80	Given a cross-model review Round 1 verdict of CHANGES_REQUIRED containing only verified code bugs with zero shared-contracts conflicts
    81	When lifecycle_runner.step_cross_model_review executes one remediation iteration followed by convergence
    82	Then unambiguous code fixes bypass _draft_fix_plan and evaluate_programmer_fix_plan and route directly to _apply_code_fixes
    83	And render_final_executive_report populates the Top 3 Highest-Risk Findings table directly from parsed review_results.md and principal_review.md entries rather than placeholder strings
    84	
    85	Scenario: [TTO-EC-04] [Tier A - Unit] Programmer effort normalization maps "extra" aliases to xhigh
    86	
    87	Given raw effort values "extra", "EXTRA", "extra-high", "extra_high", and "xhigh"
    88	When lifecycle_runner.normalize_agy_effort normalizes each configured thinking level
    89	Then every variant returns the canonical flag value "xhigh"
    90	And invoking the agy command builder passes "--effort", "xhigh" on the command line
    91	
    92	Scenario: [TTO-ST-04] [Tier C - Integration] Cross-model review escalates to Role 2.2 when shared-contracts or architecture ambiguity arises
    93	
    94	Given a cross-model review finding in Round 1 referencing shared-contracts/api_contract.md or an ambiguous architectural state transition
    95	When lifecycle_runner.step_cross_model_review triages the round findings
    96	Then fast-path auto-fix is NOT taken and either CRITICAL_CONFLICT halts immediately or fix_plan_round1.md is routed through Role 2.2 evaluation before any edit occurs
    97	
    98	Scenario: [TTO-AR-01] [Tier C - Integration] Parallel wave dispatch executes independent tasks concurrently with path-only Zero-Fluff prompts
    99	
   100	Given an epic DAG containing two disjoint Wave 1 tasks (no mutual blocker dependency) and one Wave 2 task blocked by both
   101	And an isolated worker pool initialized by manage_worker_pool.py
   102	When lifecycle_runner.step_implementation executes the implementation phase using a thread-safe recording mock dispatcher
   103	Then both Wave 1 tasks run concurrently inside distinct pool slots before Wave 2 begins
   104	And each task prompt omits inlined task markdown bodies, injects only target file paths and line ranges, and includes the Zero-Fluff output cap
   105	
   106	Scenario: [TTO-FR-03] [Tier A - Unit] lifecycle_runner._tail_lines bounds Gate 4 and intermediate check failure summaries to 25 lines
   107	
   108	Given a subprocess failure from run_gate4 or run_intermediate_check emitting 120 traceback lines
   109	When lifecycle_runner formats the failure message via _tail_lines(output, 25)
   110	Then the returned failure excerpt contains at most 25 lines terminating at the final failing assertion summary
   111	And the exception or state message propagated to the next step never exceeds 25 lines of traceback
   112	```
   113	
   114	## Verification
   115	
   116	| ID | Phase | Command | Expect | Needs |
   117	|----|-------|---------|--------|-------|
   118	| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_lifecycle_runner.py::test_tto_hp_04_runner_config_precedence` | exit 1; contains "failed" | — |
   119	| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_lifecycle_runner.py::test_tto_hp_04_runner_config_precedence` | exit 0; contains "passed" | — |
   120	| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_lifecycle_runner.py skills/dev-implementation/resources/scripts/test_manage_worker_pool.py` | exit 0; contains "passed" | — |
   121	| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/dev-lifecycle/resources/scripts/lifecycle_runner.py skills/dev-implementation/resources/scripts/manage_worker_pool.py tests/test_lifecycle_runner.py` | exit 0 | — |
   122	| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-lifecycle/resources/scripts/lifecycle_runner.py skills/dev-implementation/resources/scripts/manage_worker_pool.py` | exit 0 | — |
   123	| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_4.xml tests/test_lifecycle_runner.py` | exit 0; results build/test-results/task_4.xml | — |
   124	
   125	## Stop and Report If
   126	
   127	- A command, path, symbol or anchor named in this task does not match the repository.
   128	- A Verification row fails for a reason other than its Expect.
   129	- The work needs a change to a file outside Allowed files, or to a protected path.
   130	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
   131	  Covers line.
   132	- A variable named in the Needs column is unset.
   133	
   134	## Decisions Already Made
   135	
   136	- `normalize_agy_effort(raw: str) -> str` maps `{"extra", "extra-high", "extra_high", "xhigh"}` -> `"xhigh"`, lowercasing and trimming input; default fallback pair is `("gemini-4-hydrogen-xhigh", "xhigh")`.
   137	- `RunnerConfig.resolve_programmer_model` and `resolve_programmer_effort` follow: `CLI -> Runner --config -> .devtool/review_config.json["providers"]["programmer"] -> env (AGY_PROGRAMMER_MODEL / AGY_PROGRAMMER_EFFORT) -> fallback`.
   138	- `main()` sets `default=None` on `--programmer-model` and `--programmer-effort` so `.devtool/review_config.json` controls defaults unless explicitly overridden at invocation.
   139	- `LifecycleRunner.step_implementation` dispatches independent parallel batches concurrently via `manage_worker_pool.py` slots with clean per-task prompts referencing file paths, line ranges, and Zero-Fluff output cap.
   140	- `LifecycleRunner._tail_lines(text: str, limit: int = 25) -> str` caps Gate 4 and intermediate failure summaries at `25` lines.
   141	- `step_cross_model_review` skips `_draft_fix_plan` / `evaluate_programmer_fix_plan` strictly when findings contain no `shared-contracts/` or architectural ambiguity, preserving `CRITICAL_CONFLICT` halts and Role 2.2 escalation otherwise.
   142	
   143	## Definition of Done
   144	
   145	- Scenarios TTO-HP-04, TTO-HP-07, TTO-EC-04, TTO-ST-04, TTO-AR-01, and TTO-FR-03 pass reliably. (V2, V3, V6)
   146	- Worker pool regression suite passes cleanly with zero concurrency or cleanup failures. (V3)
   147	- Python ruff lint and mypy strict type checks pass cleanly. (V4, V5)
   148	- Config precedence and clean executive summary verified visually at completion review. (Gate 5)
   149	
   150	## Dependencies & Blockers
   151	
   152	Blocked by [Task 1](task_01_diff_only_external_review_and_transcript_isolation.md), [Task 2](task_02_silent_gate4_and_truncated_test_runners.md), and [Task 3](task_03_option_a_bilingual_and_surgical_contract_guards.md).
   153	Blocks [Task 6](task_06_integration_and_regression_verification.md).
   154	
   155	## References & Rollback
   156	
   157	- [Epic HLD](token_throttling_optimization.en.md), Module Contracts (§4).
   158	- **Rollback**: Revert task commit; restores prior `lifecycle_runner.py`, `manage_worker_pool.py`, and `tests/test_lifecycle_runner.py`.

exec
/bin/zsh -lc 'nl -ba .devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	# Token Throttling Optimization High-Level Design
     2	
     3	## Table of Contents
     4	
     5	- [Meta Data](#meta-data)
     6	- [Background](#background)
     7	- [Goals and Non-Goals](#goals-and-non-goals)
     8	- [Architecture and Technical Design](#architecture-and-technical-design)
     9	- [Feature Maintenance Map](#feature-maintenance-map)
    10	- [Module Contracts and CLI Interfaces](#module-contracts-and-cli-interfaces)
    11	- [Impact Analysis](#impact-analysis)
    12	- [Shared Contract Impact](#shared-contract-impact)
    13	- [Integration Test Plan and Boundary Matrix](#integration-test-plan-and-boundary-matrix)
    14	- [Verification Environment](#verification-environment)
    15	- [Comprehensive BDD Scenario Coverage](#comprehensive-bdd-scenario-coverage)
    16	- [Rollout Strategy and Mitigation](#rollout-strategy-and-mitigation)
    17	- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)
    18	- [Spec Errata](#spec-errata)
    19	
    20	## Meta Data
    21	
    22	- **Epic name**: `token_throttling_optimization`
    23	- **Status**: Draft
    24	- **PIC**: `danhdue`
    25	- **Target release**: Next plugin release
    26	- **Platform**: Python tooling and agent workflow kit
    27	- **Depends on epic**: none
    28	- **Source Spec**: [Approved Token Throttling Optimization Design Spec](2026-11-13-token-throttling-optimization-design.en.md)
    29	
    30	## Background
    31	
    32	End-to-end telemetry across `dev-lifecycle` (Interactive and `--autonomous`) showed quadratic token growth and rapid 5-hour quota depletion driven by five compounding causes:
    33	
    34	1. **Always-On Baseline Overhead**: `rules/CRITICAL_RULES.md` (`32,773` bytes / `239` lines) exceeds IDE truncation limits (`<truncated 8848 bytes>`), `skills/task-observer/SKILL.md` (`31,480` bytes) loads into worker subagents and headless CLIs without a guard, and `scripts/resume_context.py` dumps `26,759` bytes across all workspace repos.
    35	2. **Quadratic External Review Bloat**: `run_external_review.py` re-sends full `base...sha` diffs alongside `delta_round_context()` on Rounds `2+`, includes redundant `*.vi.md` documents, embeds full command output via `fact()` even on `exit 0`, uses `-U10` in `review-package`, and writes unfiltered CLI `stderr` transcripts directly into `principal_review.md` (`1.88 MB` measured).
    36	3. **Verbose Quality Gates and Uncapped Tracebacks**: `verify_polyglot_registry.py` dumps full JSON on `PASS`; `.agents/quality/python-quality.json` and `scaffold_quality_manifest.py` invoke `pytest` without `-q --tb=short --maxfail=3`; `run_task_checks.py` retains `40` lines; `lifecycle_runner.py` and `verify.sh` lack compact pass lines and 25-line failure tailing.
    37	4. **Coarse Reads, Sequential Tasks, and Hardcoded Legacy Models**: Task specs omit symbol/line-range windows for files over `200` lines; `lifecycle_runner.py` dispatches sequential `agy` calls with inline file text and hardcoded `gemini-3.8-flash` instead of config-driven `gemini-4-hydrogen-xhigh` (`--effort xhigh`); `step_cross_model_review()` wastes 3 LLM turns on unambiguous code bugs; `task-reviewer` runs on trivial mechanical tasks.
    38	5. **Upfront Bilingual Churn**: Maintaining synchronized Spec, HLD, and Gherkin `.vi.md` files throughout Principal Review doubles authoring and verification overhead before the English SSOT converges.
    39	
    40	## Goals and Non-Goals
    41	
    42	### Goals
    43	
    44	- Enforce all 5 Strict Token-Throttling Rules across runner scripts, verification tools, prompt templates, rules, and skill manifests across both Phase 1 (mechanical scripts) and Phase 2 (slimming, deduplication, task schema).
    45	- Adopt Option A Bilingual Workflow: retain Spec and HLD `.vi.md` for human gate reviews, exclude all `*.vi.md` files from AI review and coder handoffs, tolerate in-flight `.vi.md` drift and deferred `bdd_scenarios.vi.md` under default `check_epic_readiness.py`, and run a single Stage 4 Pre-Finish sync with `--strict-bilingual`.
    46	- Trigger `task-reviewer` selectively only for high-risk or multi-module tasks (`review_tier: "full"`, `security|architecture|concurrency|contract` labels, or `> 2` non-test modules).
    47	- Configure Role 2.3 (AI Programmer) via `.devtool/review_config.json["providers"]["programmer"]` and `RunnerConfig` precedence, upgrading the default to `gemini-4-hydrogen-xhigh` with effort normalized (`"extra"` / `"extra-high"` / `"xhigh"` -> `--effort xhigh`).
    48	- Enforce measurable size caps (`CRITICAL_RULES.md <= 8192` bytes, `dev-designer/SKILL.md <= 22528` bytes, `resume_context.py --compact --epic <slug> <= 4096` bytes) while preserving all kit release checks (`scripts/verify.sh --full`).
    49	
    50	### Non-Goals
    51	
    52	- Skipping human approval gates (Gate 1 Spec, Gate 2 Task Breakdown, Gate 5 Finish and Merge).
    53	- Disabling full test suites or `@quality_check` at the Final Convergence Gate or Stage 4 `verify-tier`.
    54	- Auto-pushing commits or branches without explicit user approval.
    55	- Altering backend quota bucket display labels (`Gemini 3.8 / Pro 5H`) in `scripts/agy_quota.py` or `quota_dashboard.html`.
    56	
    57	## Architecture and Technical Design
    58	
    59	### High-Level Architecture
    60	
    61	```mermaid
    62	flowchart TD
    63	    subgraph CFG["Configuration and Always-On Layer"]
    64	        RC[".devtool/review_config.json (providers.programmer)"]
    65	        CR["rules/CRITICAL_RULES.md (<= 8KB + Zero-Fluff Cap)"]
    66	        TO["skills/task-observer/SKILL.md (SUBAGENT-STOP)"]
    67	        MEM["scripts/resume_context.py (--compact + Dynamic Handoff)"]
    68	    end
    69	
    70	    subgraph S12["Stage 1 and Stage 2 Bilingual Option A"]
    71	        DESIGN["skills/dev-designer/SKILL.md (<= 22KB + target_files Ranges)"]
    72	        TC["check_task_contract.py (--design Line-Range Check)"]
    73	        READY["check_epic_readiness.py (In-Flight Default vs --strict-bilingual)"]
    74	        PKG["package_epic.py + handoff-template.md (English SSOT Read First)"]
    75	    end
    76	
    77	    subgraph REV["External Review Engine"]
    78	        RER["run_external_review.py (-U5 + Delta-Only R2+ + Quiet Facts + Raw Log)"]
    79	        REVP["review-package (-U5) + Diff-Only Prompts"]
    80	    end
    81	
    82	    subgraph EXEC["Stage 3 Runner and Gate 4"]
    83	        RUN["lifecycle_runner.py (Config Precedence + Pool + Fast Code Fix)"]
    84	        POOL["manage_worker_pool.py (2-Slot Ephemeral Wave Execution)"]
    85	        G4["verify_polyglot_registry.py (--compact) + run_task_checks.py (25-Line Tail)"]
    86	    end
    87	
    88	    subgraph FIN["Stage 4 Pre-Finish Hook"]
    89	        FINS["finishing-a-development-branch/SKILL.md (Delta-Sync .vi.md + Gen bdd_scenarios.vi.md)"]
    90	        DOC["check_document.py --require-toc --require-bilingual"]
    91	    end
    92	
    93	    RC --> RUN
    94	    RC --> MEM
    95	    CR --> RUN
    96	    TO --> RUN
    97	    MEM --> RUN
    98	    DESIGN --> TC --> READY --> RER --> PKG --> RUN
    99	    REVP --> RER
   100	    RUN --> POOL
   101	    RUN --> G4
   102	    G4 --> RER
   103	    RER --> FIN
   104	    FINS --> DOC --> READY
   105	```
   106	
   107	### Multi-Round Review and Selective Worker Flow
   108	
   109	```mermaid
   110	sequenceDiagram
   111	    autonumber
   112	    actor Dev as Developer (Role 2.1)
   113	    participant Des as dev-designer / Readiness
   114	    participant Rev as run_external_review.py
   115	    participant Run as lifecycle_runner.py
   116	    participant Pool as 2-Slot Worker / Subagent
   117	
   118	    Des->>Rev: HLD .en.md + bdd_scenarios.en.md + Tasks (.vi.md excluded)
   119	    Rev->>Rev: Run check_epic_readiness.py (Option A in-flight) + Delta -U5
   120	    Rev-->>Rev: Write verbose stderr to build/reviews/<epic>_roundN.raw.log
   121	    Dev->>Run: Approve Gate 2 -> AUTO MODE (Claude -> Codex -> Kiro -> Argon)
   122	    Run->>Run: Resolve programmer model (gemini-4-hydrogen-xhigh, --effort xhigh)
   123	    Run->>Pool: Dispatch disjoint task waves with path-only prompt + target ranges
   124	    Pool-->>Run: Commit task + Selective task-reviewer (high-risk only)
   125	    Run->>Run: verify_polyglot_registry.py --compact -> GATE_PASS or 25-line tail
   126	    Run->>Rev: Cross-Model Review (Round 1 full -U5; Round 2..3 delta prev_sha..sha only)
   127	    alt Clean code fix with no contract conflict
   128	        Run->>Pool: Direct Programmer fix + scoped test + 25-line tail
   129	    else Contract or architecture ambiguity
   130	        Run->>Run: Evaluate fix_plan_roundN.md via Role 2.2
   131	    end
   132	    Run->>Dev: Converged + Gate 4 PASS -> Request Gate 5 Finish Decision
   133	    Dev->>Des: Stage 4 Pre-Finish Hook (sync .vi.md + check_epic_readiness.py --strict-bilingual)
   134	```
   135	
   136	## Feature Maintenance Map
   137	
   138	| Capability | Canonical Source Paths and Entry Points | Core Invariants and Config Knobs | Extension and Troubleshooting Guide |
   139	|---|---|---|---|
   140	| **Diff-Only External Review** | `skills/dev-implementation/resources/scripts/run_external_review.py`, `skills/subagent-driven-development/scripts/review-package` | Uses `git diff -U5`; Round `>= 2` skips full `base...sha` diff when `delta_round_context` is active; excludes `*.vi.md`; truncates large diffs to `--stat` + `@@` hunks | Inspect `build/reviews/<epic>_round<n>.raw.log` for full CLI transcripts; check `MAX_DIFF_LINES` (`1500`) and `MAX_DIFF_BYTES` (`60000`) |
   141	| **Silent Gate 4 and Runners** | `skills/quality_check/resources/scripts/verify_polyglot_registry.py`, `skills/dev-implementation/resources/scripts/run_task_checks.py`, `scripts/verify.sh` | `--compact` prints `GATE_PASS: <id>` on pass and summary + 25-line tail on failure; `TAIL_LINES = 25`; `pytest -q --tb=short --maxfail=3` in `.agents/quality/python-quality.json` | Inspect full provider logs in `build/quality/<provider>/<cap>.log`; run `bash scripts/verify.sh --full` for verbose diagnostics |
   142	| **Option A Bilingual Guards** | `skills/dev-implementation/resources/scripts/check_epic_readiness.py`, `check_bdd_traceability.py`, `package_epic.py` | Default mode tolerates in-flight `.vi.md` drift and deferred `bdd_scenarios.vi.md`; `--strict-bilingual` enforces full parity at Stage 4; `handoff.md` excludes `*.vi.md` | Pass `--strict-bilingual` before Finish archival; verify Stage 4 hook in `finishing-a-development-branch/SKILL.md` |
   143	| **Surgical Target Line Ranges** | `skills/dev-implementation/resources/scripts/check_task_contract.py`, `skills/dev-designer/SKILL.md` | Tracked files `> 200` lines in `Allowed files` require `path :: Symbol (L<start>-L<end>)` anchors under `--design` | Check `check_task_contract.py --design` messages if a modified >200-line file lacks a symbol/line window |
   144	| **Config-Driven Programmer and Pool** | `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`, `manage_worker_pool.py`, `scripts/resume_context.py` | Precedence: `CLI -> Runner config -> .devtool/review_config.json -> env -> fallback ("gemini-4-hydrogen-xhigh", "xhigh")`; `"extra"` maps to `agy --effort xhigh` | Update `.devtool/review_config.json["providers"]["programmer"]` without editing code; check `PipelineState` in `.devtool/state/<epic>.pipeline.json` |
   145	| **Slim Rules and Scoped Memory** | `rules/CRITICAL_RULES.md`, `skills/task-observer/SKILL.md`, `skills/dev-designer/SKILL.md`, `skills/dev-lifecycle/references/` | `CRITICAL_RULES.md <= 8192` bytes; `dev-designer/SKILL.md <= 22528` bytes; `task-observer/SKILL.md` starts with `<SUBAGENT-STOP>`; `resume_context.py --compact --epic <slug> <= 4096` bytes | Run `bash scripts/verify.sh` and `scripts/test_lifecycle_document_contract.py` after any wording or reference split |
   146	| **Selective Task Reviewer** | `skills/dev-designer/SKILL.md`, `skills/dev-implementation/SKILL.md`, `skills/subagent-driven-development/SKILL.md` | Dispatch `task-reviewer` only for `review_tier: "full"`, high-risk labels (`security`, `architecture`, `concurrency`, `contract`), or `> 2` non-test modules | Add `review_tier: "full"` in task frontmatter when manual per-task code review is desired |
   147	
   148	## Module Contracts and CLI Interfaces
   149	
   150	These exact interfaces are frozen for implementation across tasks:
   151	
   152	1. **External Review and Config Defaults (`run_external_review.py`)**:
   153	   - `DEFAULT_REVIEW_CONFIG["providers"]` includes `"assistant"` (`"claude-opus-5-5-high"`, `"high"`) and `"programmer"` (`"gemini-4-hydrogen-xhigh"`, `"xhigh"`).
   154	   - `load_review_config(root: Path) -> dict[str, Any]` fills missing default providers and upgrades legacy programmer model IDs (`"gemini-3.8-flash"`, `"gemini-3.8-flash-high"`) to `"gemini-4-hydrogen-xhigh"` with `"thinking_level": "xhigh"`, while preserving any user-customized model ID.
   155	   - `build_diff_section(root, base, sha, max_lines=MAX_DIFF_LINES, max_bytes=MAX_DIFF_BYTES)` and `diff_range(...)`: use `git diff -U5`; when truncated over budget, include `git diff --stat` and `@@ ... @@` hunk headers per changed file instead of leaving empty hunks.
   156	   - `principal_artefact_lines(root, epic_dir)`: excludes all `*.vi.md` paths.
   157	   - `fact(label, code, out, err)`: returns `f"PASS: {label}\n"` on `code == 0`, or command + last 25 non-empty lines of combined output on failure/timeout.
   158	   - `render_round(...)`: writes full transcript to `build/reviews/<epic>_round<n>.raw.log` and references it cleanly inside markdown round tables (keeping existing round table columns compatible with `rounds_in` / `finding_rows` / `triage`).
   159	   - `run(args)`: for `round_num >= 2` with non-empty `delta_round_context()` (`not args.full`), omits full `base...sha` `diff_section` and injects a 1-line cumulative `git diff --stat` reference header.
   160	
   161	2. **Compact Quality Gates and Verification (`verify_polyglot_registry.py`, `run_task_checks.py`, `verify.sh`)**:
   162	   - `verify_polyglot_registry.py` accepts `--compact`: writes raw per-capability logs under `build/quality/<provider>/<cap>.log`, prints single-line `GATE_PASS: <provider_or_cap>` for passing checks/verdict, and on failure prints failing capability header + last 25 lines of its `.log`.
   163	   - `run_task_checks.py` sets `TAIL_LINES = 25`.
   164	   - `.agents/quality/python-quality.json` and `scaffold_quality_manifest.py` append `"-q", "--tb=short", "--maxfail=3"` to pytest commands.
   165	   - `scripts/verify.sh` accepts `--quiet` (single-line status per section, 25-line failure tail) while keeping `--full` unchanged.
   166	
   167	3. **Option A Bilingual Readiness, Surgical Checks, and Scoped Memory**:
   168	   - `check_epic_readiness.py` and `check_bdd_traceability.py` accept `--strict-bilingual` (default `False` during active development/Principal Review). Default skips `R1`/`R3`/`R7` failures caused solely by `.en.md`/`.vi.md` drift or missing `bdd_scenarios.vi.md`; `--strict-bilingual` enforces full bilingual parity.
   169	   - `package_epic.py` & `handoff-template.md` list only `.en.md` / English docs under `Read First`.
   170	   - `check_task_contract.py --design` inspects non-new tracked source/script files `> 200` lines listed under `Allowed files` and requires explicit target symbol/line anchors (`:: <Symbol> (L<start>-L<end>)` or `(L<start>-L<end>)`) in `## Files` or `## Impact Analysis & Blast Radius`.
   171	   - `scripts/resume_context.py` adds `--compact` (auto-scoped when `--epic <slug>` is passed) returning active epic snapshot, current repo git status, relevant open RFCs, and matching epic tasks (`<= 4096` bytes); `emit_handoff_prompt` reads `.devtool/review_config.json["providers"]["programmer"]` with fallback `gemini-4-hydrogen-xhigh` (`xhigh`).
   172	
   173	4. **Lifecycle Runner and Config-Driven Programmer Persona (`lifecycle_runner.py`)**:
   174	   - `RunnerConfig` replaces hardcoded `"gemini-3.8-flash"` defaults with `"gemini-4-hydrogen-xhigh"` / `"xhigh"` fallback, adds `normalize_agy_effort(raw: str) -> str` mapping `{"extra", "extra-high", "extra_high", "xhigh"}` -> `"xhigh"`, and adds `resolve_programmer_model(self, root: Path | None = None) -> str` and `resolve_programmer_effort(self, root: Path | None = None) -> str` following:
   175	     `CLI (--programmer-model / --programmer-effort) -> Runner --config JSON -> .devtool/review_config.json["providers"]["programmer"] -> env (AGY_PROGRAMMER_MODEL / AGY_PROGRAMMER_EFFORT) -> fallback ("gemini-4-hydrogen-xhigh", "xhigh")`.
   176	   - `main()` sets `argparse` defaults `default=None` for `--programmer-model` and `--programmer-effort` so CLI flags override config only when explicitly supplied.
   177	   - `_tail_lines(text: str, limit: int = 25) -> str` truncates failures cleanly in `run_gate4()` and `run_intermediate_check()`.
   178	   - `step_implementation()` uses `manage_worker_pool.py` to run independent topological waves concurrently; `_execute_single_task()` passes file paths + target read-range rules + Zero-Fluff output cap instead of inlining task contents.
   179	   - `step_cross_model_review()` fast-tracks verified code fixes directly to `_apply_code_fixes()` when no `shared-contracts/` or architecture ambiguity exists, reserving `_draft_fix_plan()` + `evaluate_programmer_fix_plan()` for design/contract ambiguity.
   180	   - `render_final_executive_report()` parses actual highest-risk findings and SHAs from `review_results.md` / `principal_review.md`.
   181	
   182	## Impact Analysis
   183	
   184	- Shift-Left `check_code_impact.py --files ... --base-ref main` reported:
   185	  - **Upstream Git Conflicts**: `CLEAN` (`0` unmerged commits against `main`).
   186	  - **Cross-Platform Bridges**: None.
   187	  - **Coverage Safety Nets**: Paired test suites exist for `resume_context.py`, `run_external_review.py`, `lifecycle_runner.py`, `verify_polyglot_registry.py`, and `check_epic_readiness.py`; `rules/CRITICAL_RULES.md` is verified via `scripts/test_lifecycle_document_contract.py` and `scripts/verify.sh` §3/§5b/§7/§8.
   188	
   189	## Shared Contract Impact
   190	
   191	None — self-contained feature. Repository `ai-agent-tools` does not contain a `shared-contracts/` directory; internal CLI flags (`--compact`, `--strict-bilingual`, `--quiet`, `--programmer-effort`) maintain backward compatibility via optional/default values.
   192	
   193	## Integration Test Plan and Boundary Matrix
   194	
   195	```text
   196	Integration test roots: tests
   197	Protected paths: .agents/quality/**, .devtool/epic/token_throttling_optimization/bdd_scenarios.en.md, .devtool/epic/token_throttling_optimization/bdd_scenarios.vi.md
   198	Integration results: python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/token-throttling-optimization.xml tests/test_tto_external_review.py tests/test_polyglot_gate4.py tests/test_tto_bilingual_and_surgical.py tests/test_lifecycle_runner.py tests/test_tto_docs_and_slimming.py tests/test_token_throttling_acceptance.py -> build/test-results/token-throttling-optimization.xml
   199	```
   200	
   201	| Boundary | Real Components | Isolation or Fixture | Required Assertions |
   202	|---|---|---|---|
   203	| **Diff-Only External Review** | `run_external_review.py`, `review-package` | Temp git repos with multi-round history and fake CLI binaries on `PATH` | `-U5` diff context, Round 2 omits full `base...sha`, `.vi.md` excluded, `PASS:` single-line facts, `build/reviews/*.raw.log` written |
   204	| **Compact Gate 4 and Runners** | `verify_polyglot_registry.py`, `run_task_checks.py`, `scaffold_quality_manifest.py`, `verify.sh` | Temp registry manifests + mock command exits (`0` and `1`) | `--compact` emits `GATE_PASS:` on pass and summary + `<= 25` lines on fail; `TAIL_LINES == 25`; `-q --tb=short --maxfail=3` injected |
   205	| **Option A Bilingual and Surgical Guards** | `check_epic_readiness.py`, `check_bdd_traceability.py`, `check_task_contract.py`, `package_epic.py`, `resume_context.py` | Synthetic temp epic dirs with `.en.md`/`.vi.md` diffs, missing `bdd_scenarios.vi.md`, and `> 200` line files | Default in-flight passes without `bdd_scenarios.vi.md`; `--strict-bilingual` fails until synced; missing line range rejected; `--compact <= 4096` bytes |
   206	| **Config-Driven Runner and Worker Pool** | `lifecycle_runner.py`, `manage_worker_pool.py` | Mock `agy` dispatcher + temp git repo + worktree pool slots | Precedence resolves `gemini-4-hydrogen-xhigh` & normalizes `"extra"` -> `"xhigh"`; path-only prompt; parallel pool wave execution; dynamic executive report |
   207	| **Slim Rules, Skills, and Release Contracts** | `CRITICAL_RULES.md`, `dev-designer/SKILL.md`, `task-observer/SKILL.md`, `finishing-a-development-branch/SKILL.md` | Live repository files validated against byte/word limits & `verify.sh` | `CRITICAL_RULES.md <= 8192` B, `dev-designer/SKILL.md <= 22528` B, `<SUBAGENT-STOP>` present, all contract tokens and §1–§10 checks pass |
   208	
   209	## Verification Environment
   210	
   211	- Tests execute in isolated temporary directories (`tempfile.TemporaryDirectory` / pytest `tmp_path`) against synthetic git repositories and fake CLI shims on `PATH`.
   212	- Zero live external API credentials, network calls, or mutations to user Antigravity profiles occur during test execution.
   213	- Live JUnit XML reports are written strictly to git-ignored `build/test-results/` and raw review/quality logs to `build/reviews/` and `build/quality/`.
   214	- Local workspace `.devtool/review_config.json` (git-ignored runtime config) is never modified inside unit tests; tests write config fixtures only inside `tmp_path`.
   215	
   216	## Comprehensive BDD Scenario Coverage
   217	
   218	The canonical Gherkin scenarios live in [BDD scenarios](bdd_scenarios.en.md) with synchronized translation in [Vietnamese BDD scenarios](bdd_scenarios.vi.md).
   219	
   220	| Dimension | Scenario IDs | Coverage Intent |
   221	|---|---|---|
   222	| **Happy Paths** | `TTO-HP-01` through `TTO-HP-08` | `-U5` delta review, `--compact` Gate 4, Option A in-flight readiness, config-driven `gemini-4-hydrogen-xhigh` (`xhigh`), slimmed rules/skills, `--compact` context, streamlined fix loop, E2E token optimization |
   223	| **Edge Cases and Boundaries** | `TTO-EC-01` through `TTO-EC-06` | Truncated diff `--stat` + `@@` hunks, `TAIL_LINES=25` + quiet pytest flags, `> 200`-line file range check, effort alias normalization, selective `task-reviewer` criteria, full `verify.sh` §1–§17 pass |
   224	| **State Transitions and Invariants** | `TTO-ST-01` through `TTO-ST-05` | `load_review_config` migration, `handoff.md` `.vi.md` exclusion, `--strict-bilingual` Gate 5 enforcement, Role 2.2 escalation on contract conflict, Stage 4 Pre-Finish sync hook |
   225	| **Async and Concurrency** | `TTO-AR-01` through `TTO-AR-02` | Parallel topological wave dispatch via `manage_worker_pool.py`, round raw-log isolation and clean cross-task session boundaries |
   226	| **Failure and Resilience** | `TTO-FR-01` through `TTO-FR-04` | Quiet `collect_facts` 25-line failure tail, compact Gate 4 failure 25-line tail, `_tail_lines` Gate 4 failure truncation, quantitative byte-size regression bounds |
   227	
   228	## Rollout Strategy and Mitigation
   229	
   230	1. **Wave 1 (Disjoint Foundations — Tasks 1, 2, 3)**: Land Diff-Only External Review (`run_external_review.py`, `review-package`), Compact Gate 4 & Runners (`verify_polyglot_registry.py`, `run_task_checks.py`, `verify.sh --quiet`), and Option A / Surgical Contract / Scoped Memory (`check_epic_readiness.py`, `check_task_contract.py`, `resume_context.py`).
   231	2. **Wave 2 (Orchestration and Slimming — Tasks 4, 5)**: Land Config-Driven `lifecycle_runner.py` (`gemini-4-hydrogen-xhigh`, `--effort xhigh`, pool concurrency, fast code-fix path) alongside Rules, Skills, Reference Consolidation, and Stage 4 Pre-Finish Hook updates.
   232	3. **Wave 3 (Integration and Regression Suite — Task 6)**: Add quantitative token-throttling E2E regression checks (`test_token_throttling_acceptance.py`), register new suites in `scripts/verify.sh`, and verify full release checks.
   233	
   234	Mitigation: All new compact/quiet flags (`--compact`, `--quiet`) preserve verbose/full fallback paths (`--full` on `verify.sh` and `run_external_review.py`), and `--strict-bilingual` stays optional until Stage 4 so in-flight workflows never break backward compatibility.
   235	
   236	## Kanban Tasks Breakdown
   237	
   238	1. **Task 1: Diff-Only External Review and Transcript Isolation** (`task_01_diff_only_external_review_and_transcript_isolation.md`) — Covers: `TTO-HP-01, TTO-EC-01, TTO-ST-01, TTO-FR-01`
   239	2. **Task 2: Silent Gate 4 and Truncated Test Runners** (`task_02_silent_gate4_and_truncated_test_runners.md`) — Covers: `TTO-HP-02, TTO-EC-02, TTO-FR-02`
   240	3. **Task 3: Option A Bilingual Guards, Surgical Contracts, and Compact Memory** (`task_03_option_a_bilingual_and_surgical_contract_guards.md`) — Covers: `TTO-HP-03, TTO-HP-06, TTO-EC-03, TTO-ST-02, TTO-ST-03`
   241	4. **Task 4: Config-Driven Programmer Persona, Pool Dispatch, and Runner Optimization** (`task_04_lifecycle_runner_programmer_config_and_pool_isolation.md`) — Covers: `TTO-HP-04, TTO-HP-07, TTO-EC-04, TTO-ST-04, TTO-AR-01, TTO-FR-03`
   242	5. **Task 5: Rules and Skills Slimming, Deduplication, Selective Reviewer, and Pre-Finish Sync** (`task_05_slimming_rules_skills_dedup_and_selective_reviewer.md`) — Covers: `TTO-HP-05, TTO-EC-05, TTO-ST-05`
   243	6. **Task 6: Token Throttling Acceptance and Quantitative Regression Suite** (`task_06_integration_and_regression_verification.md`) — Covers: `TTO-HP-08, TTO-EC-06, TTO-AR-02, TTO-FR-04`
   244	
   245	## Spec Errata
   246	
   247	None.

exec
/bin/zsh -lc 'nl -ba .devtool/epic/token_throttling_optimization/task_01_diff_only_external_review_and_transcript_isolation.md; nl -ba .devtool/epic/token_throttling_optimization/task_02_silent_gate4_and_truncated_test_runners.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	---
     2	id: "task_01_diff_only_external_review_and_transcript_isolation"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "token_throttling_optimization"
     7	dueDate: null
     8	created: "2026-11-13T02:30:00Z"
     9	modified: "2026-11-13T02:30:00Z"
    10	completedAt: null
    11	labels: ["review", "token-optimization", "config"]
    12	order: "a1"
    13	---
    14	
    15	# Task 1: Diff-Only External Review and Transcript Isolation
    16	
    17	Epic: [token_throttling_optimization](token_throttling_optimization.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Enforce Diff-Only Review (`Rule 1`), Silent/Capped Evidence (`Rule 2`), Transcript Log Isolation (`Rule 5`), and Config-Driven Role 2.3 defaults in the external review subsystem:
    22	1. Update `DEFAULT_REVIEW_CONFIG["providers"]` and `load_review_config()` in `skills/dev-implementation/resources/scripts/run_external_review.py`:
    23	   - Add default `"assistant"` (`"claude-opus-5-5-high"`, `"high"`) and `"programmer"` (`"gemini-4-hydrogen-xhigh"`, `"xhigh"`) provider entries.
    24	   - Inside `load_review_config()`, seed missing default providers and upgrade legacy programmer models (`"gemini-3.8-flash"`, `"gemini-3.8-flash-high"`) in-memory to `"gemini-4-hydrogen-xhigh"` with `"thinking_level": "xhigh"`, while leaving custom user models (e.g. `"claude-sonnet-4-6"`) untouched.
    25	2. Enforce Diff-Only `-U5` and Round 2+ delta-only prompts:
    26	   - Change `git diff` context from `-U10` to `-U5` in both `run_external_review.py` (`build_diff_section`, `diff_range`) and `skills/subagent-driven-development/scripts/review-package`.
    27	   - When `build_diff_section()` or `diff_range()` truncates over `MAX_DIFF_LINES` (`1500`) or `MAX_DIFF_BYTES` (`60000`), prepend `git diff --stat` and include per-file headers + `@@ ... @@` hunk headers within budget.
    28	   - Exclude all `*.vi.md` files from `principal_artefact_lines()` and `collect_facts()` / `artefact_lines()` where applicable.
    29	   - In `run()` for `round_num >= 2` when `delta_round_context()` is non-empty (and `--full` is not set), omit the cumulative `base...sha` diff section and emit a 1-line `git diff --stat` cumulative reference instead.
    30	3. Quiet facts and raw CLI log isolation:
    31	   - Update `fact(label, code, out, err)` so `code == 0` emits `f"PASS: {label}\n"` omitting stdout, and failure emits the label plus the last 25 non-empty lines.
    32	   - Update `render_round()` to persist raw CLI stdout/stderr transcripts into `build/reviews/<epic>_round<n>.raw.log` and reference that path instead of dumping multi-megabyte transcripts into `principal_review.md` or `review_results.md`, keeping the compact `Raw output:` verdict fence intact for downstream table/finding parsers (`rounds_in`, `finding_rows`, `triage`).
    33	   - Update `skills/principal-review/references/principal-review-prompt.md` and `skills/dev-implementation/references/external-review-prompt.md` with explicit Diff-Only (`-U5`), Zero-Fluff output, and English SSOT review guidance.
    34	4. Add `tests/test_tto_external_review.py` covering `TTO-HP-01`, `TTO-EC-01`, `TTO-ST-01`, and `TTO-FR-01`.
    35	
    36	## Files
    37	
    38	Allowed files:
    39	- `skills/dev-implementation/resources/scripts/run_external_review.py`
    40	- `skills/dev-implementation/resources/scripts/test_run_external_review.py`
    41	- `skills/subagent-driven-development/scripts/review-package`
    42	- `skills/dev-implementation/references/external-review-prompt.md`
    43	- `skills/principal-review/references/principal-review-prompt.md`
    44	- `tests/test_tto_external_review.py` (new)
    45	
    46	Read-only context:
    47	- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Module Contracts and Integration Plan
    48	- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios
    49	- `.agents/quality/python-quality.json` — Registered lint and type_check commands
    50	
    51	## Design Rationale
    52	
    53	External review rounds dominate token burn because every Round 2+ re-transmits full `base...sha` diffs, `.vi.md` duplicates, verbose passing command logs, and raw CLI stderr back into markdown artifacts that later stages reload. Enforcing `-U5`, structural `--stat` + `@@` truncation, Round 2 delta isolation, 1-line passing facts, and raw log offloading eliminates quadratic bloat without losing any parser fidelity. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.
    54	
    55	## Impact Analysis & Blast Radius
    56	
    57	- **Target Files & Symbols**:
    58	  - `skills/dev-implementation/resources/scripts/run_external_review.py`: `load_review_config` (L103-L129), `principal_artefact_lines` (L317-L352), `fact` (L507-L508), `collect_facts` (L511-L640), `build_diff_section` (L652-L683), `diff_range` (L686-L719), `render_round` (L896-L902), `delta_round_context` (L972-L1118), `run` (L1230-L1320)
    59	  - `skills/subagent-driven-development/scripts/review-package`: diff context lines (L1-L77)
    60	  - `tests/test_tto_external_review.py`: new unit and integration tests for `TTO-HP-01`, `TTO-EC-01`, `TTO-ST-01`, `TTO-FR-01`
    61	- **Downstream Callers**: `scripts/resume_context.py` (`--emit-prompt`), `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`load_review_config`, `run_external_review.py` subprocess), `skills/dev-implementation/resources/scripts/test_run_external_review.py`.
    62	- **Cross-Platform Bridges**: None.
    63	- **Target Test Coverage Threshold**: 100% of new config migration, diff truncation, fact formatting, and raw log offloading branches.
    64	
    65	### BDD SCENARIOS
    66	
    67	Covers: TTO-HP-01, TTO-EC-01, TTO-ST-01, TTO-FR-01
    68	
    69	```gherkin
    70	Scenario: [TTO-HP-01] [Tier C - Integration] Diff-only external review uses -U5 in Round 1 and omits full base diff in Round 2
    71	
    72	Given an isolated git repository with an epic having multiple committed source changes and a .vi.md companion document
    73	And an existing Round 1 entry already recorded in review_results.md for an earlier SHA
    74	When run_external_review.py builds the Round 1 prompt and then builds the Round 2 prompt after an incremental fix commit
    75	Then the Round 1 diff section is generated with -U5 context and excludes all *.vi.md artifact paths
    76	And the Round 2 prompt includes delta_round_context for prev_sha..curr_sha with a one-line cumulative diff --stat reference
    77	And the Round 2 prompt omits the full base...curr_sha diff block unless --full is explicitly passed
    78	
    79	Scenario: [TTO-EC-01] [Tier A - Unit] Over-budget diff truncates to --stat summary and @@ hunk headers per changed file
    80	
    81	Given a synthetic git diff exceeding MAX_DIFF_LINES (1500 lines) or MAX_DIFF_BYTES (60000 bytes)
    82	When build_diff_section builds the diff payload for external review
    83	Then the output falls back cleanly within the byte budget without dropping structural file boundaries
    84	And the truncated section explicitly contains the git diff --stat summary alongside the file headers and @@ hunk headers for changed files
    85	
    86	Scenario: [TTO-ST-01] [Tier A - Unit] load_review_config migrates legacy gemini-3.8-flash defaults while preserving custom models
    87	
    88	Given an existing .devtool/review_config.json with providers.programmer.model set to "gemini-3.8-flash-high"
    89	And a second config file where providers.programmer.model is customized to "claude-sonnet-4-6"
    90	When run_external_review.load_review_config loads each configuration file
    91	Then the legacy "gemini-3.8-flash-high" entry is upgraded in-memory to "gemini-4-hydrogen-xhigh" with thinking_level "xhigh"
    92	And the user-customized "claude-sonnet-4-6" entry remains untouched without being overwritten
    93	
    94	Scenario: [TTO-FR-01] [Tier A - Unit] collect_facts emits one line per passing command and caps failing output + raw transcripts
    95	
    96	Given a passing command returning 180 stdout lines with exit code 0 and a failing command returning 90 stderr lines with exit code 1
    97	When run_external_review.fact builds prompt evidence and render_round persists the round artifact
    98	Then the passing command produces a single "PASS: <label>" line omitting stdout
    99	And the failing command includes the command label plus at most 25 trailing non-empty output lines
   100	And unfiltered CLI stdout/stderr is routed into build/reviews/<epic>_round<n>.raw.log so principal_review.md remains compact
   101	```
   102	
   103	## Verification
   104	
   105	| ID | Phase | Command | Expect | Needs |
   106	|----|-------|---------|--------|-------|
   107	| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_external_review.py::test_tto_hp_01_diff_only_round1_and_round2` | exit 1; contains "failed" | — |
   108	| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_external_review.py::test_tto_hp_01_diff_only_round1_and_round2` | exit 0; contains "passed" | — |
   109	| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; contains "passed" | — |
   110	| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py tests/test_tto_external_review.py` | exit 0 | — |
   111	| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py tests/test_tto_external_review.py` | exit 0 | — |
   112	| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_1.xml tests/test_tto_external_review.py` | exit 0; results build/test-results/task_1.xml | — |
   113	
   114	## Stop and Report If
   115	
   116	- A command, path, symbol or anchor named in this task does not match the repository.
   117	- A Verification row fails for a reason other than its Expect.
   118	- The work needs a change to a file outside Allowed files, or to a protected path.
   119	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
   120	  Covers line.
   121	- A variable named in the Needs column is unset.
   122	
   123	## Decisions Already Made
   124	
   125	- `DEFAULT_REVIEW_CONFIG["providers"]` (in `skills/dev-implementation/resources/scripts/run_external_review.py`) includes `"assistant": {"model": "claude-opus-5-5-high", "thinking_level": "high"}` and `"programmer": {"model": "gemini-4-hydrogen-xhigh", "thinking_level": "xhigh"}`.
   126	- `load_review_config()` upgrades legacy programmer IDs `{"gemini-3.8-flash", "gemini-3.8-flash-high"}` in-memory to `"gemini-4-hydrogen-xhigh"` + `"thinking_level": "xhigh"`, preserving custom models and avoiding mutations to the gitignored repo-level `.devtool/review_config.json` during unit tests.
   127	- Diff extraction in `build_diff_section()` and `diff_range()` (L652-L719) and `review-package` uses `git diff -U5`; over-budget diffs retain `git diff --stat` and per-file `@@ ... @@` hunk headers; `principal_artefact_lines()` (L317-L352) excludes `*.vi.md`.
   128	- `fact(label, code, out, err)` (L507-L508) emits `"PASS: {label}\n"` on `code == 0` and caps failures to the last 25 non-empty lines; `render_round()` (L896-L902) writes unfiltered transcripts to `build/reviews/<epic>_round<n>.raw.log` while preserving `Raw output:` verdict fences compatible with `rounds_in()` (L850-L865), `finding_rows()` (L1528-L1529), and `triage()` (L1711-L1783).
   129	- Round `>= 2` in `run()` (L1230-L1320) omits full `base...sha` `diff_section` whenever `delta_round_context()` is non-empty and `--full` is false.
   130	
   131	## Definition of Done
   132	
   133	- Scenarios TTO-HP-01, TTO-EC-01, TTO-ST-01, and TTO-FR-01 pass with real temporary git repositories and fake CLIs. (V2, V3, V6)
   134	- Python ruff lint and mypy strict checks pass across modified and existing test suites. (V3, V4, V5)
   135	- Diff context (`-U5`), `.vi.md` exclusion, raw log offloading, and `load_review_config` migration verified cleanly on candidate commit. (Gate 5)
   136	
   137	## Dependencies & Blockers
   138	
   139	None. Blocks [Task 4](task_04_lifecycle_runner_programmer_config_and_pool_isolation.md) and [Task 5](task_05_slimming_rules_skills_dedup_and_selective_reviewer.md).
   140	
   141	## References & Rollback
   142	
   143	- [Epic HLD](token_throttling_optimization.en.md), Module Contracts (§1).
   144	- **Rollback**: Revert task commit; restores prior `run_external_review.py`, `review-package`, prompt templates, and removes `tests/test_tto_external_review.py`.
   145	
     1	---
     2	id: "task_02_silent_gate4_and_truncated_test_runners"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "token_throttling_optimization"
     7	dueDate: null
     8	created: "2026-11-13T02:30:00Z"
     9	modified: "2026-11-13T02:30:00Z"
    10	completedAt: null
    11	labels: ["gate4", "quality-check", "token-optimization"]
    12	order: "a2"
    13	---
    14	
    15	# Task 2: Silent Gate 4 and Truncated Test Runners
    16	
    17	Epic: [token_throttling_optimization](token_throttling_optimization.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Enforce Silent Gate 4 and 25-line failure tailing (`Rule 2`) across quality providers, task verification runners, and release checks:
    22	1. Add `--compact` mode to `skills/quality_check/resources/scripts/verify_polyglot_registry.py`:
    23	   - Write full raw stdout/stderr per provider capability to `build/quality/<provider>/<cap>.log`.
    24	   - When `--compact` is enabled and checks/verdict pass, print single-line `GATE_PASS: <provider_or_cap>` entries instead of verbose JSON blobs.
    25	   - When `--compact` encounters a failure or `BLOCKED` outcome, print the failing capability header and strictly at most 25 trailing lines from its `.log` file while leaving all raw lines intact on disk.
    26	2. Reduce `TAIL_LINES` from `40` to `25` in `skills/dev-implementation/resources/scripts/run_task_checks.py`.
    27	3. Update `.agents/quality/python-quality.json` (protected path named explicitly in `Allowed files`) `"test"` command and `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py` `"python"` template so pytest runs append `"-q", "--tb=short", "--maxfail=3"`.
    28	4. Add `--quiet` flag to `scripts/verify.sh` outputting one concise status line per passing section and at most 25 trailing lines on failure, while keeping default/`--full` behavior unchanged.
    29	5. Document `--compact` invocation in `skills/quality_check/SKILL.md`.
    30	6. Expand `tests/test_polyglot_gate4.py` and `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py` / `skills/dev-implementation/resources/scripts/test_run_task_checks.py` with tests covering `TTO-HP-02`, `TTO-EC-02`, and `TTO-FR-02`.
    31	
    32	## Files
    33	
    34	Allowed files:
    35	- `skills/quality_check/resources/scripts/verify_polyglot_registry.py`
    36	- `skills/dev-implementation/resources/scripts/run_task_checks.py`
    37	- `skills/dev-implementation/resources/scripts/test_run_task_checks.py`
    38	- `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`
    39	- `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py`
    40	- `.agents/quality/python-quality.json`
    41	- `scripts/verify.sh`
    42	- `skills/quality_check/SKILL.md`
    43	- `tests/test_polyglot_gate4.py`
    44	
    45	Read-only context:
    46	- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Module Contracts (§2)
    47	- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios
    48	
    49	## Design Rationale
    50	
    51	Quality checks routinely emit thousands of passing lines and JSON structures into agent context. Routing verbose provider output to `build/quality/<provider>/<cap>.log` and returning single-line `GATE_PASS:` summaries or 25-line failure tails slashes Gate 4 token burn while keeping full diagnostics on disk for debugging. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.
    52	
    53	## Impact Analysis & Blast Radius
    54	
    55	- **Target Files & Symbols**:
    56	  - `skills/quality_check/resources/scripts/verify_polyglot_registry.py`: `execute_provider` (L142-L438), `verify_polyglot_execution` (L441-L537), `main` (L540-L618)
    57	  - `skills/dev-implementation/resources/scripts/run_task_checks.py`: `run_row` (L282-L321), `main` (L461-L476)
    58	  - `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`: `build_registry_data` (L226-L241)
    59	  - `scripts/verify.sh`: §1-§17 output formatting (L1-L417)
    60	  - `tests/test_polyglot_gate4.py`: integration assertions for `TTO-HP-02`, `TTO-EC-02`, `TTO-FR-02`
    61	- **Downstream Callers**: `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`run_gate4`), `skills/dev-implementation/SKILL.md` (`@quality_check`), `skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`.
    62	- **Cross-Platform Bridges**: None.
    63	- **Target Test Coverage Threshold**: 100% of `--compact` pass/fail branches, 25-line truncation boundaries, and `--quiet` `verify.sh` handling.
    64	
    65	### BDD SCENARIOS
    66	
    67	Covers: TTO-HP-02, TTO-EC-02, TTO-FR-02
    68	
    69	```gherkin
    70	Scenario: [TTO-HP-02] [Tier C - Integration] Compact Gate 4 runner prints single-line GATE_PASS and stores full logs under build/quality
    71	
    72	Given a project with a valid .agents/quality/check_quality.json registry whose providers exit with status 0
    73	When verify_polyglot_registry.py runs with --compact
    74	Then standard output contains single-line "GATE_PASS: <provider_or_cap>" entries instead of verbose JSON blobs
    75	And full per-capability execution logs are written to build/quality/<provider>/<cap>.log
    76	And the overall aggregated verdict equals PASS
    77	
    78	Scenario: [TTO-EC-02] [Tier A - Unit] Task runner enforces 25-line tail and Python quality manifests inject quiet pytest flags
    79	
    80	Given a failing task check output with 120 stdout/stderr lines
    81	And .agents/quality/python-quality.json alongside a scaffolded manifest from scaffold_quality_manifest.py
    82	When run_task_checks.py formats failure evidence and the Python test command is inspected
    83	Then run_task_checks.TAIL_LINES equals 25 and the emitted snippet retains only the last 25 non-empty lines
    84	And both .agents/quality/python-quality.json and newly scaffolded Python quality manifests invoke pytest with "-q", "--tb=short", and "--maxfail=3"
    85	
    86	Scenario: [TTO-FR-02] [Tier C - Integration] Compact Gate 4 surfaces failing provider header and 25-line log tail on error
    87	
    88	Given a quality registry containing one passing capability and one failing capability printing 80 diagnostic lines to stderr
    89	When verify_polyglot_registry.py runs with --compact
    90	Then the process exits non-zero reporting FAIL
    91	And standard output prints "GATE_PASS:" for the passing capability plus the failing capability header and strictly at most 25 trailing log lines from build/quality/
    92	And all 80 raw diagnostic lines remain preserved on disk inside build/quality/<provider>/<cap>.log
    93	```
    94	
    95	## Verification
    96	
    97	| ID | Phase | Command | Expect | Needs |
    98	|----|-------|---------|--------|-------|
    99	| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_polyglot_gate4.py::test_tto_hp_02_compact_gate4_single_line_pass` | exit 1; contains "failed" | — |
   100	| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_polyglot_gate4.py::test_tto_hp_02_compact_gate4_single_line_pass` | exit 0; contains "passed" | — |
   101	| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_polyglot_gate4.py skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0; contains "passed" | — |
   102	| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/dev-implementation/resources/scripts/run_task_checks.py tests/test_polyglot_gate4.py` | exit 0 | — |
   103	| V5 | TIER-B | `ruff check --select F,E9,B skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py` | exit 0 | — |
   104	| V6 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/run_task_checks.py skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py` | exit 0 | — |
   105	| V7 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_2.xml tests/test_polyglot_gate4.py` | exit 0; results build/test-results/task_2.xml | — |
   106	
   107	## Stop and Report If
   108	
   109	- A command, path, symbol or anchor named in this task does not match the repository.
   110	- A Verification row fails for a reason other than its Expect.
   111	- The work needs a change to a file outside Allowed files, or to a protected path not named explicitly here.
   112	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
   113	  Covers line.
   114	- A variable named in the Needs column is unset.
   115	
   116	## Decisions Already Made
   117	
   118	- `verify_polyglot_registry.py` (`execute_provider` L142-L438, `main` L540-L618) adds `--compact`: always writes full capability stdout/stderr to `build/quality/<provider>/<cap>.log`, prints `GATE_PASS: <provider_or_cap>` for passing checks, and prints failing header + last 25 lines of the capability log on failure while returning non-zero exit codes cleanly.
   119	- `run_task_checks.py` updates `TAIL_LINES = 25` (`run_task_checks.py` line 77).
   120	- `.agents/quality/python-quality.json` updates `"test"` capability from `["python3", "-m", "pytest", "tests"]` to `["python3", "-m", "pytest", "-q", "--tb=short", "--maxfail=3", "tests"]` (justifying modification of this declared protected path by naming it explicitly in `Allowed files`).
   121	- `scaffold_quality_manifest.py` (`PLATFORM_CONFIGS["python"]["manifest"]["capabilities"]["test"]`, L131) includes `"-q", "--tb=short", "--maxfail=3"`.
   122	- `scripts/verify.sh` adds `--quiet` flag without changing `--full` default semantics or exit codes.
   123	
   124	## Definition of Done
   125	
   126	- Scenarios TTO-HP-02, TTO-EC-02, and TTO-FR-02 are verified by passing unit and integration tests. (V2, V3, V7)
   127	- Ruff lint and mypy checks pass cleanly across modified files. (V4, V5, V6)
   128	- Protected path `.agents/quality/python-quality.json` update produces quiet pytest flags cleanly under Gate 4. (Gate 5)
   129	
   130	## Dependencies & Blockers
   131	
   132	None. Blocks [Task 4](task_04_lifecycle_runner_programmer_config_and_pool_isolation.md) and [Task 5](task_05_slimming_rules_skills_dedup_and_selective_reviewer.md).
   133	
   134	## References & Rollback
   135	
   136	- [Epic HLD](token_throttling_optimization.en.md), Module Contracts (§2).
   137	- **Rollback**: Revert task commit; restores prior `verify_polyglot_registry.py`, `TAIL_LINES = 40`, `python-quality.json`, and `verify.sh`.
   138	

exec
/bin/zsh -lc 'nl -ba .devtool/epic/token_throttling_optimization/task_03_option_a_bilingual_and_surgical_contract_guards.md; nl -ba .devtool/epic/token_throttling_optimization/task_05_slimming_rules_skills_dedup_and_selective_reviewer.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	---
     2	id: "task_03_option_a_bilingual_and_surgical_contract_guards"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "token_throttling_optimization"
     7	dueDate: null
     8	created: "2026-11-13T02:30:00Z"
     9	modified: "2026-11-13T02:30:00Z"
    10	completedAt: null
    11	labels: ["bilingual", "contract", "memory", "token-optimization"]
    12	order: "a3"
    13	---
    14	
    15	# Task 3: Option A Bilingual Guards, Surgical Contracts, and Compact Memory
    16	
    17	Epic: [token_throttling_optimization](token_throttling_optimization.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Implement Option A Bilingual Workflow guards, Surgical Target Line Range enforcement (`Rule 3`), and Scoped/Compact Memory (`--compact` + dynamic programmer prompt):
    22	1. **Option A Bilingual Readiness & Traceability Guards**:
    23	   - Add `--strict-bilingual` (default `False`) to `skills/dev-implementation/resources/scripts/check_epic_readiness.py` (`main`, `run_checks`, `check_preflight`, `check_bdd_scenarios`, `check_metadata`).
    24	   - Add `--strict-bilingual` (default `False`) to `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` (`main`, `load_scenarios`, `check_plan`).
    25	   - In default in-flight mode (`--strict-bilingual` unset):
    26	     - Tolerate in-flight `.vi.md` drift on `R1` (`check_document.py`), `R3` (`check_bdd_scenarios`), and `R7` (`check_metadata` when checking `.vi.md` parity), and tolerate an absent `bdd_scenarios.vi.md` during Stage 2/3 development while still enforcing `.vi.md` pairing on present documents where existing parity tests require strict checks or gating under `--strict-bilingual`.
    27	     - When `bdd_scenarios.vi.md` is present during active runs, default `check_epic_readiness` only enforces `.vi.md` strict parity when `--strict-bilingual` is passed (and preserves `test_check_bdd_traceability` / `test_check_epic_readiness` assertions explicitly testing `--strict-bilingual` or existing `.en.md` invariants).
    28	   - Under `--strict-bilingual` (Stage 4 Pre-Finish): require complete `.en.md`/`.vi.md` parity across spec, HLD, metadata, ToC, and `bdd_scenarios.vi.md`.
    29	2. **Exclude `.vi.md` from AI Coder Handoffs**:
    30	   - Update `skills/dev-implementation/resources/scripts/package_epic.py` (`render_initial_handoff`, `revise_handoff_text`) and `skills/dev-lifecycle/references/handoff-template.md` so `Read First` contains strictly English SSOT paths (`<epic_dir>.en.md`, `bdd_scenarios.en.md`, `principal_review.md`) and zero `*.vi.md` files, while preserving all contract guardrails required by `scripts/test_lifecycle_document_contract.py` and `scripts/test_resume_context.py` (`resume_context.py`, `[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]`, 4 Execution Guardrails, `principal_review.md`).
    31	3. **Surgical File Reading Gate (`check_task_contract.py --design`)**:
    32	   - Inspect non-new tracked source/script files exceeding `200` lines listed under `Allowed files:` when `--design` is passed.
    33	   - Require explicit symbol and/or `(L<start>-L<end>)` line-range anchors for each such `> 200`-line file inside `## Impact Analysis & Blast Radius` or `## Files`.
    34	4. **Scoped `--compact` Context Restoration & Dynamic Programmer Prompt (`scripts/resume_context.py`)**:
    35	   - Add `--compact` (auto-scoped when `--epic <slug>` is passed) emitting `<= 4096` bytes containing only active epic snapshot, current repo git status, matching epic tasks, and relevant open RFCs.
    36	   - Update `emit_handoff_prompt()` to resolve Role 2.3's recommended model and effort dynamically from `.devtool/review_config.json["providers"]["programmer"]` with fallback `gemini-4-hydrogen-xhigh` (`xhigh`) instead of hardcoded `Gemini Flash 3.8`.
    37	5. Add `tests/test_tto_bilingual_and_surgical.py` covering `TTO-HP-03`, `TTO-HP-06`, `TTO-EC-03`, `TTO-ST-02`, and `TTO-ST-03`, updating paired script test files as needed.
    38	
    39	## Files
    40	
    41	Allowed files:
    42	- `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
    43	- `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py`
    44	- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`
    45	- `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`
    46	- `skills/dev-implementation/resources/scripts/check_task_contract.py`
    47	- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
    48	- `skills/dev-implementation/resources/scripts/package_epic.py`
    49	- `skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py`
    50	- `skills/dev-lifecycle/references/handoff-template.md`
    51	- `scripts/resume_context.py`
    52	- `scripts/test_resume_context.py`
    53	- `tests/test_tto_bilingual_and_surgical.py` (new)
    54	
    55	Read-only context:
    56	- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Module Contracts (§3)
    57	- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios
    58	- `scripts/test_lifecycle_document_contract.py` — Contract strings asserted on `handoff-template.md`
    59	
    60	## Design Rationale
    61	
    62	Decoupling in-flight `.vi.md` translation synchronization until Stage 4 prevents double rework during Principal Review rounds, while `--compact` context restoration and `> 200`-line target range validation eliminate cold-start and whole-file reading bloat in Stage 3. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.
    63	
    64	## Impact Analysis & Blast Radius
    65	
    66	- **Target Files & Symbols**:
    67	  - `skills/dev-implementation/resources/scripts/check_epic_readiness.py`: `check_preflight` (L110-L203), `check_bdd_scenarios` (L314-L343), `check_metadata` (L645-L752), `run_checks` (L830-L852), `main` (L952-L1016)
    68	  - `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`: `load_scenarios` (L82-L100), `check_plan` (L113-L127), `main` (L228-L261)
    69	  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `check_allowed` (L127-L154), `check_task` (L394-L417), `main` (L507-L562)
    70	  - `skills/dev-implementation/resources/scripts/package_epic.py`: `render_initial_handoff` (L78-L116), `revise_handoff_text` (L119-L183), `package_epic` (L211-L300)
    71	  - `scripts/resume_context.py`: `collect_harvest_data` (L1133-L1261), `emit_handoff_prompt` (L1271-L1337), `parse_args` (L1510-L1662), `main` (L1665-L1842)
    72	  - `tests/test_tto_bilingual_and_surgical.py`: new unit and integration tests for `TTO-HP-03`, `TTO-HP-06`, `TTO-EC-03`, `TTO-ST-02`, `TTO-ST-03`
    73	- **Downstream Callers**: `skills/dev-implementation/resources/scripts/run_external_review.py` (`check_epic_readiness.py` preflight), `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`--compact` resume, `package_epic.py`), `skills/finishing-a-development-branch/SKILL.md` (`--strict-bilingual` Stage 4 gate).
    74	- **Cross-Platform Bridges**: None.
    75	- **Target Test Coverage Threshold**: 100% of default vs `--strict-bilingual` mode branches, `> 200`-line surgical check paths, and `--compact` byte-budget bounds.
    76	
    77	### BDD SCENARIOS
    78	
    79	Covers: TTO-HP-03, TTO-HP-06, TTO-EC-03, TTO-ST-02, TTO-ST-03
    80	
    81	```gherkin
    82	Scenario: [TTO-HP-03] [Tier C - Integration] Option A default readiness tolerates in-flight .vi.md drift and deferred bdd_scenarios.vi.md
    83	
    84	Given an epic directory containing current *.en.md design docs and bdd_scenarios.en.md
    85	And bdd_scenarios.vi.md is absent while an existing .vi.md companion has un-synced sections during active Principal Review
    86	When check_epic_readiness.py runs without --strict-bilingual
    87	Then the readiness gate succeeds with status PASS on R1, R3, and R7 without failing on .vi.md drift or missing bdd_scenarios.vi.md
    88	And check_bdd_traceability.py validates task coverage solely against bdd_scenarios.en.md
    89	
    90	Scenario: [TTO-HP-06] [Tier C - Integration] Compact context restoration caps output at 4096 bytes and reads programmer config dynamically
    91	
    92	Given a multi-repo workspace directory with active epic metadata, tasks, and open RFC entries
    93	And .devtool/review_config.json configures providers.programmer to "gemini-4-hydrogen-xhigh" with thinking_level "xhigh"
    94	When scripts/resume_context.py runs with --compact --epic token_throttling_optimization and --emit-prompt implement
    95	Then the compact context payload measures at most 4096 bytes and includes active epic snapshot, current repo git status, matching tasks, and relevant open RFCs
    96	And the emitted handoff prompt specifies "gemini-4-hydrogen-xhigh" and "xhigh" read dynamically from .devtool/review_config.json
    97	
    98	Scenario: [TTO-EC-03] [Tier C - Integration] Design contract checker rejects large >200-line modified files lacking target symbol or line-range anchors
    99	
   100	Given a task file referencing a non-new tracked Python source file exceeding 200 lines in Allowed files
   101	And the task's Files and Impact Analysis sections omit any target symbol name or (L<start>-L<end>) line range for that file
   102	When check_task_contract.py executes with --design against that task file
   103	Then check_task_contract.py exits non-zero and reports the missing symbol or line-range anchor for that >200-line file
   104	And adding a valid "path :: Symbol (L10-L85)" anchor clears the violation and exits with status 0
   105	
   106	Scenario: [TTO-ST-02] [Tier C - Integration] Handoff package and template exclude .vi.md files from AI coder Read First list
   107	
   108	Given an epic directory containing spec.en.md, spec.vi.md, epic.en.md, epic.vi.md, bdd_scenarios.en.md, and bdd_scenarios.vi.md
   109	When package_epic.py generates handoff.md from skills/dev-lifecycle/references/handoff-template.md
   110	Then the generated Read First section references only *.en.md documents and zero *.vi.md paths
   111	And handoff-template.md contains no static legacy model hardcodes conflicting with config-driven Role 2.3 selection
   112	
   113	Scenario: [TTO-ST-03] [Tier C - Integration] Stage 4 --strict-bilingual readiness gate enforces full .en.md and .vi.md parity
   114	
   115	Given an epic directory whose .vi.md HLD has drifted behind .en.md or lacks bdd_scenarios.vi.md
   116	When check_epic_readiness.py runs with --strict-bilingual and check_bdd_traceability.py runs with --strict-bilingual
   117	Then both commands exit non-zero highlighting the missing or out-of-sync Vietnamese mirror files
   118	And after synchronizing .vi.md and adding bdd_scenarios.vi.md with matching IDs and ToC headings, both --strict-bilingual checks exit with status 0
   119	```
   120	
   121	## Verification
   122	
   123	| ID | Phase | Command | Expect | Needs |
   124	|----|-------|---------|--------|-------|
   125	| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_bilingual_and_surgical.py::test_tto_hp_03_option_a_default_readiness` | exit 1; contains "failed" | — |
   126	| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_bilingual_and_surgical.py::test_tto_hp_03_option_a_default_readiness` | exit 0; contains "passed" | — |
   127	| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_bilingual_and_surgical.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py skills/dev-implementation/resources/scripts/test_check_task_contract.py skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py scripts/test_resume_context.py` | exit 0; contains "passed" | — |
   128	| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/package_epic.py scripts/resume_context.py tests/test_tto_bilingual_and_surgical.py` | exit 0 | — |
   129	| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/package_epic.py scripts/resume_context.py tests/test_tto_bilingual_and_surgical.py` | exit 0 | — |
   130	| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_3.xml tests/test_tto_bilingual_and_surgical.py` | exit 0; results build/test-results/task_3.xml | — |
   131	
   132	## Stop and Report If
   133	
   134	- A command, path, symbol or anchor named in this task does not match the repository.
   135	- A Verification row fails for a reason other than its Expect.
   136	- The work needs a change to a file outside Allowed files, or to a protected path.
   137	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
   138	  Covers line.
   139	- A variable named in the Needs column is unset.
   140	
   141	## Decisions Already Made
   142	
   143	- `check_epic_readiness.py` (`run_checks` L830-L852, `main` L952-L1016) and `check_bdd_traceability.py` (`load_scenarios` L82-L100, `main` L228-L261) add `--strict-bilingual` (default `False`). Without `--strict-bilingual`, in-flight checks validate English SSOT docs/BDDs cleanly and tolerate `.vi.md` drift or missing `bdd_scenarios.vi.md`; with `--strict-bilingual`, full `.en.md`/`.vi.md` parity is mandatory.
   144	- `package_epic.py` (`render_initial_handoff` L78-L116, `revise_handoff_text` L119-L183) and `skills/dev-lifecycle/references/handoff-template.md` list only English SSOT paths in `Read First`, while keeping required tokens from `scripts/test_lifecycle_document_contract.py` (`principal_review.md`, 4 Execution Guardrails, `or \`uncommitted\` when \`auto_commit\` is false`, `git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>`) and `scripts/test_resume_context.py` (`resume_context.py`, `[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]`).
   145	- `check_task_contract.py --design` (`check_task` L394-L417) requires explicit symbol or line-range anchor (`L<start>-L<end>`) in `## Files` or `## Impact Analysis & Blast Radius` for every non-new tracked source/script file exceeding `200` lines in `Allowed files`.
   146	- `scripts/resume_context.py --compact --epic <slug>` enforces output size `<= 4096` bytes and `emit_handoff_prompt` reads `.devtool/review_config.json["providers"]["programmer"]` with fallback `("gemini-4-hydrogen-xhigh", "xhigh")`.
   147	
   148	## Definition of Done
   149	
   150	- Scenarios TTO-HP-03, TTO-HP-06, TTO-EC-03, TTO-ST-02, and TTO-ST-03 pass end-to-end. (V2, V3, V6)
   151	- Legacy tests for readiness, traceability, contract checking, packaging, and resume context remain passing. (V3)
   152	- Python ruff lint and mypy strict type checks exit 0. (V4, V5)
   153	- `handoff-template.md` contract guardrails preserved cleanly under visual inspection. (Gate 5)
   154	
   155	## Dependencies & Blockers
   156	
   157	None. Blocks [Task 4](task_04_lifecycle_runner_programmer_config_and_pool_isolation.md) and [Task 5](task_05_slimming_rules_skills_dedup_and_selective_reviewer.md).
   158	
   159	## References & Rollback
   160	
   161	- [Epic HLD](token_throttling_optimization.en.md), Module Contracts (§3).
   162	- **Rollback**: Revert task commit; restores prior readiness, traceability, contract, packaging, and context scripts.
   163	
     1	---
     2	id: "task_05_slimming_rules_skills_dedup_and_selective_reviewer"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "token_throttling_optimization"
     7	dueDate: null
     8	created: "2026-11-13T02:36:00Z"
     9	modified: "2026-11-13T02:36:00Z"
    10	completedAt: null
    11	labels: ["docs", "slimming", "skills", "token-optimization"]
    12	order: "a5"
    13	---
    14	
    15	# Task 5: Rules and Skills Slimming, Deduplication, Selective Reviewer, and Pre-Finish Sync
    16	
    17	Epic: [token_throttling_optimization](token_throttling_optimization.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Slim always-on instructions and lifecycle skills (`Rule 1`, `Rule 3`, `Rule 5`), replace scattered legacy `Gemini Flash 3.8` / `gemini-3.8-flash` defaults with config-driven `.devtool/review_config.json` resolution (`gemini-4-hydrogen-xhigh`, `--effort xhigh`), deduplicate overlapping reference files across `dev-implementation/`, `principal-review/`, and `cross-model-review/`, enforce selective `task-reviewer` gating, and add the Stage 4 Pre-Finish bilingual sync hook:
    22	1. **Always-On Rule & Observer Slimming (`CRITICAL_RULES.md`, `task-observer/SKILL.md`)**:
    23	   - Compress `rules/CRITICAL_RULES.md` to `<= 8192` bytes while preserving all mandatory headings, markers (`## 8. Mandatory Two-Tier Project Memory & Tri-Role Persona Discipline`, `BOTH Interactive Mode and Autonomous`, `CRITICAL_CONFLICT`, `Debatable`), update Role 2.3 description to reference `.devtool/review_config.json["providers"]["programmer"]` (default `gemini-4-hydrogen-xhigh`, `--effort xhigh`), and add §9 Zero-Fluff Output Cap (`Rule 5`).
    24	   - Prepend an explicit `<SUBAGENT-STOP>` block at the top of `skills/task-observer/SKILL.md` forbidding invocation inside headless/subagent task workers and `lifecycle_runner.py` sessions while preserving interactive session trigger behavior.
    25	2. **Stage 2 Designer Slimming, Surgical Line Ranges, and Bilingual Option A (`dev-designer/SKILL.md`)**:
    26	   - Extract verbose worked task examples/templates into `skills/dev-designer/references/task-template-examples.md` (and keep `verification-rows.md` / `verification-row-grammar.md` linked) so `skills/dev-designer/SKILL.md` measures `<= 22528` bytes while preserving all `EXPECTED["skills/dev-designer/SKILL.md"]` contract markers (`exact node ID`, `Decisions Already Made`, etc.).
    27	   - Document Option A bilingual deferral (`.en.md` SSOT in Stages 1–3, Stage 4 Pre-Finish `.vi.md` sync), mandatory `target_files` symbol + `(L<start>-L<end>)` range anchors for modified files `> 200` lines (`Rule 3`), and selective `task-reviewer` metadata tagging (`review_tier: "full"`).
    28	3. **Selective `task-reviewer` & Config-Driven Programmer Wording (`dev-implementation`, `dev-lifecycle`, `principal-review`, `subagent-driven-development`)**:
    29	   - Replace remaining `Gemini Flash 3.8` / `gemini-3.8-flash` strings in `skills/dev-implementation/SKILL.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-lifecycle/references/autonomous-mode.md`, and `skills/principal-review/SKILL.md` with `.devtool/review_config.json` Role 2.3 resolution (`gemini-4-hydrogen-xhigh`, `--effort xhigh`).
    30	   - Enforce selective `task-reviewer` gating across `skills/dev-designer/SKILL.md`, `skills/dev-implementation/SKILL.md`, and `skills/subagent-driven-development/SKILL.md`: skip per-task `task-reviewer` for single-file/trivial tasks and trigger it only when `review_tier: "full"`, high-risk labels (`security`, `architecture`, `concurrency`, `contract`), or `> 2` non-test modules are touched.
    31	   - Inject `Rule 3` (line-bounded reads) and `Rule 5` (Zero-Fluff Output Cap) into `dev-implementation/SKILL.md`, `dev-lifecycle/SKILL.md`, and `subagent-driven-development/SKILL.md`.
    32	4. **Reference Deduplication (`dev-implementation/references/`, `principal-review/references/`, `cross-model-review/references/`)**:
    33	   - Reconcile overlapping reference files (`principal-review-prompt.md`, `principal-review-rules.md`, `review-triage.md`, `local-review-setup.md`, `review-rules.md`) so duplicate instructions live in a single canonical location with thin relative pointers where required by `scripts/verify.sh` §3/§8 and `scripts/test_lifecycle_document_contract.py`.
    34	5. **Stage 4 Pre-Finish Bilingual Sync Hook (`finishing-a-development-branch/SKILL.md`)**:
    35	   - Update Step 5 Pre-Finish Hook (`L119-L160`) to delta-sync `.vi.md` companions from changed `.en.md` Spec/HLD documents, generate/sync `bdd_scenarios.vi.md` matching IDs and ToC headings, and run `check_epic_readiness.py <epic> --strict-bilingual` + `check_bdd_traceability.py plan <epic> --strict-bilingual` before merge while preserving `resume_context.py` archival behavior.
    36	6. Update `scripts/test_lifecycle_document_contract.py` if needed and create `tests/test_tto_docs_and_slimming.py` covering `TTO-HP-05`, `TTO-EC-05`, and `TTO-ST-05`.
    37	
    38	## Files
    39	
    40	Allowed files:
    41	- `rules/CRITICAL_RULES.md`
    42	- `skills/task-observer/SKILL.md`
    43	- `skills/dev-designer/SKILL.md`
    44	- `skills/dev-designer/references/verification-rows.md`
    45	- `skills/dev-designer/references/task-template-examples.md` (new)
    46	- `skills/dev-implementation/SKILL.md`
    47	- `skills/dev-lifecycle/SKILL.md`
    48	- `skills/dev-lifecycle/references/autonomous-mode.md`
    49	- `skills/dev-lifecycle/references/principal-review.md`
    50	- `skills/principal-review/SKILL.md`
    51	- `skills/subagent-driven-development/SKILL.md`
    52	- `skills/finishing-a-development-branch/SKILL.md`
    53	- `skills/dev-implementation/references/principal-review-prompt.md`
    54	- `skills/dev-implementation/references/principal-review-rules.md`
    55	- `skills/dev-implementation/references/review-triage.md`
    56	- `skills/dev-implementation/references/local-review-setup.md`
    57	- `skills/dev-implementation/references/review-rules.md`
    58	- `skills/principal-review/references/principal-review-rules.md`
    59	- `skills/cross-model-review/references/review-triage.md`
    60	- `skills/cross-model-review/references/local-review-setup.md`
    61	- `scripts/test_lifecycle_document_contract.py`
    62	- `tests/test_tto_docs_and_slimming.py` (new)
    63	
    64	Read-only context:
    65	- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Summary, Architecture, and Acceptance Bounds
    66	- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios
    67	- `scripts/verify.sh` — §3/§4/§5b/§8 release link and reference integrity rules
    68	
    69	## Design Rationale
    70	
    71	Every top-level session loads `rules/CRITICAL_RULES.md` unconditionally and every worker subagent sees skill instructions. Compressing `CRITICAL_RULES.md` (`<= 8KB`) and `dev-designer/SKILL.md` (`<= 22KB`), halting `task-observer` inside subagents via `<SUBAGENT-STOP>`, deduplicating dual-maintained review references, skipping redundant `task-reviewer` subagents on trivial tasks, and moving `.vi.md` translation maintenance to Stage 4 preserves full governance fidelity at a fraction of the token budget. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:writing-skills`, `d3nexus:doc_quality_check`.
    72	
    73	## Impact Analysis & Blast Radius
    74	
    75	- **Target Files & Symbols**:
    76	  - `rules/CRITICAL_RULES.md`: rule sections (L1-L239), Zero-Fluff Output Cap addition
    77	  - `skills/task-observer/SKILL.md`: frontmatter and preamble (L1-L60), new `<SUBAGENT-STOP>` directive
    78	  - `skills/dev-designer/SKILL.md`: design spec and task authoring sections (L1-L540)
    79	  - `skills/dev-designer/references/verification-rows.md`: canonical row examples (L1-L120)
    80	  - `skills/dev-designer/references/task-template-examples.md`: new extracted task templates and example blocks
    81	  - `skills/dev-implementation/SKILL.md`: worker loop and selective reviewer section (L1-L437)
    82	  - `skills/dev-lifecycle/SKILL.md`: stage summary and Role 2.3 config note (L1-L206)
    83	  - `skills/dev-lifecycle/references/autonomous-mode.md`: autonomous Role 2.3 description (L1-L75)
    84	  - `skills/dev-lifecycle/references/principal-review.md`: stage 2 review handoff wording (L1-L74)
    85	  - `skills/principal-review/SKILL.md`: convergence handoff line (L80-L105)
    86	  - `skills/subagent-driven-development/SKILL.md`: flowchart, selective task-reviewer gate, and Zero-Fluff cap (L1-L593)
    87	  - `skills/finishing-a-development-branch/SKILL.md`: Step 5 Pre-Finish Hook (L119-L160)
    88	  - `skills/dev-implementation/references/principal-review-prompt.md`: thin canonical pointer to `principal-review/references/` (L1-L60)
    89	  - `skills/dev-implementation/references/principal-review-rules.md`: deduplicated canonical reference (L1-L25)
    90	  - `skills/dev-implementation/references/review-triage.md`: reconciled pointer / canonical rules (L1-L56)
    91	  - `skills/dev-implementation/references/local-review-setup.md`: deduplicated pointer (L1-L109)
    92	  - `skills/dev-implementation/references/review-rules.md`: concise canonical review rules (L1-L24)
    93	  - `skills/principal-review/references/principal-review-rules.md`: canonical standalone rules (L1-L38)
    94	  - `skills/cross-model-review/references/review-triage.md`: canonical cross-model triage guide (L1-L78)
    95	  - `skills/cross-model-review/references/local-review-setup.md`: canonical local review guide (L1-L76)
    96	  - `scripts/test_lifecycle_document_contract.py`: `EXPECTED` (L12-L157), `LifecycleDocumentContractTest` (L159-L327), `PrincipalReviewWorkflowTest` (L329-L408), `TestReviewSkillContracts` (L410-L454)
    97	  - `tests/test_tto_docs_and_slimming.py`: new doc-contract and size regression tests for `TTO-HP-05`, `TTO-EC-05`, `TTO-ST-05`
    98	- **Downstream Callers**: All downstream repositories inheriting `d3nexus` rules and skills (`verify.sh` §3/§4/§5b/§8 checks, `test_lifecycle_document_contract.py`, `test_resume_context.py`).
    99	- **Cross-Platform Bridges**: None.
   100	- **Target Test Coverage Threshold**: 100% of byte-size limits, contract string invariants, `<SUBAGENT-STOP>` presence, selective reviewer gating clauses, and Pre-Finish `.vi.md` sync checks.
   101	
   102	### BDD SCENARIOS
   103	
   104	Covers: TTO-HP-05, TTO-EC-05, TTO-ST-05
   105	
   106	```gherkin
   107	Scenario: [TTO-HP-05] [Tier C - Integration] Slimmed rules and dev-designer skill satisfy byte caps and release contract checks
   108	
   109	Given the updated rules/CRITICAL_RULES.md, skills/dev-designer/SKILL.md, and skills/task-observer/SKILL.md in the repository
   110	When scripts/test_lifecycle_document_contract.py executes and file byte sizes are measured on disk
   111	Then rules/CRITICAL_RULES.md measures at most 8192 bytes and contains the Zero-Fluff Output Cap directive
   112	And skills/dev-designer/SKILL.md measures at most 22528 bytes while preserving every required section and Extracted reference link
   113	And skills/task-observer/SKILL.md contains an explicit <SUBAGENT-STOP> instruction preventing invocation in subagents and headless workers
   114	And scripts/test_lifecycle_document_contract.py exits with status 0 and zero assertion failures
   115	
   116	Scenario: [TTO-EC-05] [Tier C - Integration] Selective task-reviewer gating skips trivial tasks and activates on high-risk or multi-module tasks
   117	
   118	Given a trivial single-file documentation or utility task without high-risk labels and review_tier unset
   119	And a complex task carrying review_tier: "full" or labels ["security", "concurrency"] or touching 3 non-test modules
   120	When the selective task-reviewer criteria documented across dev-designer, dev-implementation, and subagent-driven-development are evaluated
   121	Then the trivial single-file task skips the redundant task-reviewer subagent pass
   122	And the complex or high-risk task triggers the dedicated task-reviewer pass before task sign-off
   123	
   124	Scenario: [TTO-ST-05] [Tier C - Integration] Finishing-a-development-branch Stage 4 Pre-Finish hook synchronizes .vi.md before merge
   125	
   126	Given skills/finishing-a-development-branch/SKILL.md in the updated agent kit
   127	When the Stage 4 finishing workflow specification is inspected and checked by verify.sh §3 and §8
   128	Then an explicit Stage 4 Pre-Finish bilingual sync step delta-syncs Spec and HLD .vi.md companions, generates bdd_scenarios.vi.md, and runs check_epic_readiness.py --strict-bilingual before merge
   129	And all cross-references and doc contract invariants remain unbroken under verify.sh
   130	```
   131	
   132	## Verification
   133	
   134	| ID | Phase | Command | Expect | Needs |
   135	|----|-------|---------|--------|-------|
   136	| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_docs_and_slimming.py::test_tto_hp_05_slimmed_rules_and_skills_caps` | exit 1; contains "failed" | — |
   137	| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_docs_and_slimming.py::test_tto_hp_05_slimmed_rules_and_skills_caps` | exit 0; contains "passed" | — |
   138	| V3 | GREEN | `python3 scripts/test_lifecycle_document_contract.py` | exit 0 | — |
   139	| V4 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_docs_and_slimming.py scripts/test_lifecycle_document_contract.py scripts/test_resume_context.py` | exit 0; contains "passed" | — |
   140	| V5 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 scripts/test_lifecycle_document_contract.py tests/test_tto_docs_and_slimming.py` | exit 0 | — |
   141	| V6 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_tto_docs_and_slimming.py` | exit 0 | — |
   142	| V7 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_5.xml tests/test_tto_docs_and_slimming.py` | exit 0; results build/test-results/task_5.xml | — |
   143	
   144	## Stop and Report If
   145	
   146	- A command, path, symbol or anchor named in this task does not match the repository.
   147	- A Verification row fails for a reason other than its Expect.
   148	- The work needs a change to a file outside Allowed files, or to a protected path.
   149	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
   150	  Covers line.
   151	- A variable named in the Needs column is unset.
   152	
   153	## Decisions Already Made
   154	
   155	- `rules/CRITICAL_RULES.md` must stay `<= 8192` bytes, retain all required contract markers (`test_lifecycle_document_contract.py` + `test_resume_context.py`), replace `Gemini Flash 3.8` with `.devtool/review_config.json`, and define §9 Zero-Fluff Output Cap.
   156	- `skills/dev-designer/SKILL.md` must stay `<= 22528` bytes by offloading worked templates to linked `references/` files (`verify.sh` §8 requires every file in `references/` to be referenced by filename in a tracked file).
   157	- `skills/task-observer/SKILL.md` opens with `<SUBAGENT-STOP>` so subagents never activate continuous observer overhead.
   158	- Selective `task-reviewer` criteria are standardized identically across `dev-designer`, `dev-implementation`, and `subagent-driven-development`: trigger on `review_tier: "full"`, labels containing `security`, `architecture`, `concurrency`, or `contract`, or `> 2` non-test modules; otherwise skip.
   159	- Duplicate files across `dev-implementation/references/` and standalone `principal-review/references/` / `cross-model-review/references/` are collapsed to canonical definitions with thin pointers preserving existing link contracts.
   160	
   161	## Definition of Done
   162	
   163	- Scenarios TTO-HP-05, TTO-EC-05, and TTO-ST-05 pass consistently without byte-budget or link regressions. (V2, V4, V7)
   164	- Existing lifecycle document contract and resume context tests remain green. (V3, V4)
   165	- Python ruff lint and mypy checks pass on test and contract scripts. (V5, V6)
   166	- Slimmed instructions and Stage 4 Pre-Finish bilingual sync hook reviewed during Gate 5 completion. (Gate 5)
   167	
   168	## Dependencies & Blockers
   169	
   170	Blocked by [Task 1](task_01_diff_only_external_review_and_transcript_isolation.md), [Task 2](task_02_silent_gate4_and_truncated_test_runners.md), and [Task 3](task_03_option_a_bilingual_and_surgical_contract_guards.md).
   171	Blocks [Task 6](task_06_integration_and_regression_verification.md).
   172	
   173	## References & Rollback
   174	
   175	- [Epic HLD](token_throttling_optimization.en.md), Architecture Design & Quantitative Budgets (§1–§4).
   176	- **Rollback**: Revert task commit; restores original rules, skill prose, reference copies, and `tests/test_tto_docs_and_slimming.py`.

codex
Tôi đã đọc spec, HLD và phần lớn task contracts. Các điểm cần kiểm tra sâu là quyền đọc source khi diff bị rút gọn, cách chạy song song các task có thể cùng sửa file, và những kiểm tra cũ vẫn bắt buộc bilingual trước Stage 4. Tôi đang đối chiếu các điểm này với runner và test hiện có.

exec
/bin/zsh -lc 'nl -ba .devtool/epic/token_throttling_optimization/task_06_integration_and_regression_verification.md; nl -ba .devtool/epic/token_throttling_optimization/bdd_scenarios.en.md; command -v -a git python3; cat CLAUDE.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	---
     2	id: "task_06_integration_and_regression_verification"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "token_throttling_optimization"
     7	dueDate: null
     8	created: "2026-11-13T02:36:00Z"
     9	modified: "2026-11-13T02:36:00Z"
    10	completedAt: null
    11	labels: ["acceptance", "regression", "verification", "token-optimization"]
    12	order: "a6"
    13	---
    14	
    15	# Task 6: Token Throttling Acceptance and Quantitative Regression Suite
    16	
    17	Epic: [token_throttling_optimization](token_throttling_optimization.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Implement the end-to-end quantitative token-throttling acceptance and regression test suite (`tests/test_token_throttling_acceptance.py`) and register all new epic test suites inside `scripts/verify.sh` so Gate 4 and release verification enforce every token-throttling bound continuously:
    22	1. **End-to-End Token-Throttling Acceptance (`tests/test_token_throttling_acceptance.py`)**:
    23	   - Validate all quantitative byte ceilings against the live repository and mock epic fixtures:
    24	     - `rules/CRITICAL_RULES.md <= 8192` bytes and contains Zero-Fluff Output Cap (`Rule 5`).
    25	     - `skills/dev-designer/SKILL.md <= 22528` bytes.
    26	     - `skills/task-observer/SKILL.md` opens with `<SUBAGENT-STOP>`.
    27	     - `scripts/resume_context.py --compact --epic <slug> <= 4096` bytes.
    28	     - Zero stale hardcoded `Gemini Flash 3.8` / `gemini-3.8-flash` Role 2.3 defaults in lifecycle skills, rules, templates, or runner defaults; resolved default programmer model equals `gemini-4-hydrogen-xhigh` with effort `xhigh`.
    29	   - Verify fail-loud quantitative assertions (`TTO-FR-04`): exceeding any threshold produces explicit actual-vs-budget byte diagnostic messages.
    30	   - Verify isolated per-task context and per-round raw log isolation (`TTO-AR-02`): consecutive review rounds write distinct `build/reviews/<epic>_round<n>.raw.log` files without leaking transcripts into adjacent rounds or markdown tables, and consecutive `lifecycle_runner.py` task prompts carry zero accumulated Task `N` output into Task `N+1`.
    31	   - Verify compact Gate 4 and `--quiet` vs `--full` release harness behavior (`TTO-HP-08`, `TTO-EC-06`).
    32	2. **Release Verification Registry (`scripts/verify.sh`)**:
    33	   - Add `tests/test_tto_external_review.py`, `tests/test_tto_bilingual_and_surgical.py`, `tests/test_tto_docs_and_slimming.py`, and `tests/test_token_throttling_acceptance.py` (alongside any unregistered polyglot/runner test suites as appropriate) into `SUITES` in `scripts/verify.sh` so both `--quiet` and `--full` run all §1–§17 checks cleanly.
    34	
    35	## Files
    36	
    37	Allowed files:
    38	- `tests/test_token_throttling_acceptance.py` (new)
    39	- `scripts/verify.sh`
    40	
    41	Read-only context:
    42	- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Integration Test Plan (§4)
    43	- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios
    44	- `tests/test_tto_external_review.py` — External review tests (Task 1)
    45	- `tests/test_polyglot_gate4.py` — Compact Gate 4 tests (Task 2)
    46	- `tests/test_tto_bilingual_and_surgical.py` — Option A & compact context tests (Task 3)
    47	- `tests/test_lifecycle_runner.py` — Config precedence & pool dispatch tests (Task 4)
    48	- `tests/test_tto_docs_and_slimming.py` — Rules, skills & selective reviewer tests (Task 5)
    49	
    50	## Design Rationale
    51	
    52	Token budgets erode silently over future commits unless enforced by automated quantitative regression assertions wired directly into the repository's CI release gate (`scripts/verify.sh`). Keeping acceptance tests in `tests/test_token_throttling_acceptance.py` while registering every new module test in `SUITES` ensures any future rule bloat, hardcoded model drift, or log leak fails loudly at release time. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.
    53	
    54	## Impact Analysis & Blast Radius
    55	
    56	- **Target Files & Symbols**:
    57	  - `tests/test_token_throttling_acceptance.py`: new quantitative regression and end-to-end acceptance suite for `TTO-HP-08`, `TTO-EC-06`, `TTO-AR-02`, `TTO-FR-04`
    58	  - `scripts/verify.sh`: `SUITES` (L303-L400) suite registrations and section status execution
    59	- **Downstream Callers**: CI release verification (`bash scripts/verify.sh --full`), developer quiet runs (`bash scripts/verify.sh --quiet`), Polyglot Gate 4 `pytest` runner.
    60	- **Cross-Platform Bridges**: None.
    61	- **Target Test Coverage Threshold**: 100% of HLD quantitative caps, cross-task isolation invariants, and `--quiet`/`--full` section parity checks.
    62	
    63	### BDD SCENARIOS
    64	
    65	Covers: TTO-HP-08, TTO-EC-06, TTO-AR-02, TTO-FR-04
    66	
    67	```gherkin
    68	Scenario: [TTO-HP-08] [Tier C - Integration] End-to-end token-throttling pipeline enforces compact prompts, review isolation, and programmer config
    69	
    70	Given an isolated epic workspace bootstrapped with .devtool/review_config.json, task files containing target line ranges, and fake review/agy CLIs
    71	When the lifecycle pipeline executes readiness, external review, worker dispatch, compact Gate 4, and executive summary generation
    72	Then every review prompt respects the diff-only -U5 budget and writes raw output outside markdown files
    73	And every worker prompt omits inlined source files while invoking gemini-4-hydrogen-xhigh with --effort xhigh
    74	And compact Gate 4 emits single-line GATE_PASS statuses upon green verification
    75	
    76	Scenario: [TTO-EC-06] [Tier C - Integration] Compact verify.sh --quiet prints concise section lines while --full executes all 17 suites
    77	
    78	Given the repository tooling scripts and markdown skills under scripts/verify.sh
    79	When bash scripts/verify.sh --quiet runs and when bash scripts/verify.sh --full runs
    80	Then --quiet prints a single concise status line per passing section without verbose suite noise
    81	And --full executes all registered verification sections §1 through §17 and exits with status 0
    82	
    83	Scenario: [TTO-AR-02] [Tier C - Integration] Per-task clean context and per-round raw logs prevent cross-session transcript contamination
    84	
    85	Given two sequential or parallel review rounds and consecutive task dispatches within a single epic run
    86	When run_external_review.render_round writes logs and lifecycle_runner invokes Task N+1 after Task N commits
    87	Then each review round writes its isolated raw transcript to build/reviews/<epic>_round<n>.raw.log without appending into markdown review tables or adjacent round logs
    88	And the Task N+1 invocation prompt contains no accumulated tool output or stderr from Task N
    89	
    90	Scenario: [TTO-FR-04] [Tier C - Integration] Quantitative regression tests fail loudly if rule, skill, context, or prompt sizes exceed caps
    91	
    92	Given the live kit files and mock epic harness inside tests/test_token_throttling_acceptance.py
    93	When the quantitative token-throttling acceptance suite executes under pytest
    94	Then assertions explicitly check byte ceilings (CRITICAL_RULES.md <= 8192, dev-designer/SKILL.md <= 22528, resume_context --compact <= 4096) and review/prompt budgets
    95	And exceeding any ceiling fails with concrete byte-count diagnostics rather than generic boolean checks
    96	```
    97	
    98	## Verification
    99	
   100	| ID | Phase | Command | Expect | Needs |
   101	|----|-------|---------|--------|-------|
   102	| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_token_throttling_acceptance.py::test_tto_fr_04_quantitative_byte_ceilings` | exit 1; contains "failed" | — |
   103	| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_token_throttling_acceptance.py::test_tto_fr_04_quantitative_byte_ceilings` | exit 0; contains "passed" | — |
   104	| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_external_review.py tests/test_polyglot_gate4.py tests/test_tto_bilingual_and_surgical.py tests/test_lifecycle_runner.py tests/test_tto_docs_and_slimming.py tests/test_token_throttling_acceptance.py` | exit 0; contains "passed" | — |
   105	| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 tests/test_token_throttling_acceptance.py` | exit 0 | — |
   106	| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_token_throttling_acceptance.py` | exit 0 | — |
   107	| V6 | TIER-B | `bash scripts/verify.sh --quiet` | exit 0 | — |
   108	| V7 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_6.xml tests/test_token_throttling_acceptance.py` | exit 0; results build/test-results/task_6.xml | — |
   109	| V8 | TIER-C | `bash scripts/verify.sh --full` | exit 0 | — |
   110	
   111	## Stop and Report If
   112	
   113	- A command, path, symbol or anchor named in this task does not match the repository.
   114	- A Verification row fails for a reason other than its Expect.
   115	- The work needs a change to a file outside Allowed files, or to a protected path not named explicitly here.
   116	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
   117	  Covers line.
   118	- A variable named in the Needs column is unset.
   119	
   120	## Decisions Already Made
   121	
   122	- Quantitative regression assertions fail with concrete formatted actual vs limit byte counts rather than opaque booleans.
   123	- `scripts/verify.sh` retains full backward compatibility on `--full` (`§1`–`§17`) while `--quiet` prints single-line summaries for passing sections and capped failure tails.
   124	
   125	## Definition of Done
   126	
   127	- All 25 epic BDD scenarios (`TTO-HP-01..FR-04`) are covered across Tasks 1–6 and verified end-to-end by `tests/test_token_throttling_acceptance.py`. (V2, V3, V7)
   128	- `scripts/verify.sh --quiet` and `scripts/verify.sh --full` pass across every registered suite `§1`–`§17`. (V6, V8)
   129	- Ruff lint and mypy checks pass on `tests/test_token_throttling_acceptance.py`. (V4, V5)
   130	- Final quantitative measurements and before/after summary inspected at Gate 5 completion. (Gate 5)
   131	
   132	## Dependencies & Blockers
   133	
   134	Blocked by [Task 1](task_01_diff_only_external_review_and_transcript_isolation.md), [Task 2](task_02_silent_gate4_and_truncated_test_runners.md), [Task 3](task_03_option_a_bilingual_and_surgical_contract_guards.md), [Task 4](task_04_lifecycle_runner_programmer_config_and_pool_isolation.md), and [Task 5](task_05_slimming_rules_skills_dedup_and_selective_reviewer.md). Blocks none.
   135	
   136	## References & Rollback
   137	
   138	- [Epic HLD](token_throttling_optimization.en.md), Integration Test Plan & Rollout (§4).
   139	- **Rollback**: Revert task commit; restores prior `scripts/verify.sh` suite list and removes `tests/test_token_throttling_acceptance.py`.
     1	# Token Throttling Optimization BDD Scenarios
     2	
     3	## Table of Contents
     4	
     5	- [Meta Data](#meta-data)
     6	- [Happy Paths](#happy-paths)
     7	- [Edge Cases and Boundaries](#edge-cases-and-boundaries)
     8	- [State Transitions and Invariants](#state-transitions-and-invariants)
     9	- [Async and Concurrency](#async-and-concurrency)
    10	- [Failure and Resilience](#failure-and-resilience)
    11	
    12	## Meta Data
    13	
    14	- **Epic**: `token_throttling_optimization`
    15	- **Canonical language**: English
    16	- **Scenario prefix**: `TTO`
    17	- **Automation roots**: `tests`
    18	- **Rule**: Every scenario ID is assigned to exactly one task and appears in an automated test.
    19	- **Mocking**: Subprocess CLIs (`claude`, `codex`, `kiro`, `agy`, `pytest`, `git`) and filesystem mutations are isolated inside temporary directories (`tmp_path` / `tempfile.TemporaryDirectory`) with fake binaries on `PATH`.
    20	
    21	## Happy Paths
    22	
    23	```gherkin
    24	Scenario: [TTO-HP-01] [Tier C - Integration] Diff-only external review uses -U5 in Round 1 and omits full base diff in Round 2
    25	
    26	Given an isolated git repository with an epic having multiple committed source changes and a .vi.md companion document
    27	And an existing Round 1 entry already recorded in review_results.md for an earlier SHA
    28	When run_external_review.py builds the Round 1 prompt and then builds the Round 2 prompt after an incremental fix commit
    29	Then the Round 1 diff section is generated with -U5 context and excludes all *.vi.md artifact paths
    30	And the Round 2 prompt includes delta_round_context for prev_sha..curr_sha with a one-line cumulative diff --stat reference
    31	And the Round 2 prompt omits the full base...curr_sha diff block unless --full is explicitly passed
    32	
    33	Scenario: [TTO-HP-02] [Tier C - Integration] Compact Gate 4 runner prints single-line GATE_PASS and stores full logs under build/quality
    34	
    35	Given a project with a valid .agents/quality/check_quality.json registry whose providers exit with status 0
    36	When verify_polyglot_registry.py runs with --compact
    37	Then standard output contains single-line "GATE_PASS: <provider_or_cap>" entries instead of verbose JSON blobs
    38	And full per-capability execution logs are written to build/quality/<provider>/<cap>.log
    39	And the overall aggregated verdict equals PASS
    40	
    41	Scenario: [TTO-HP-03] [Tier C - Integration] Option A default readiness tolerates in-flight .vi.md drift and deferred bdd_scenarios.vi.md
    42	
    43	Given an epic directory containing current *.en.md design docs and bdd_scenarios.en.md
    44	And bdd_scenarios.vi.md is absent while an existing .vi.md companion has un-synced sections during active Principal Review
    45	When check_epic_readiness.py runs without --strict-bilingual
    46	Then the readiness gate succeeds with status PASS on R1, R3, and R7 without failing on .vi.md drift or missing bdd_scenarios.vi.md
    47	And check_bdd_traceability.py validates task coverage solely against bdd_scenarios.en.md
    48	
    49	Scenario: [TTO-HP-04] [Tier A - Unit] RunnerConfig resolves Role 2.3 programmer model and effort using config precedence
    50	
    51	Given a .devtool/review_config.json defining providers.programmer.model as "gemini-4-hydrogen-xhigh" and thinking_level as "extra"
    52	And AGY_PROGRAMMER_MODEL environment override is unset
    53	When lifecycle_runner.RunnerConfig resolves the programmer model and effort with no CLI flag supplied
    54	Then resolve_programmer_model returns "gemini-4-hydrogen-xhigh" and resolve_programmer_effort returns "xhigh"
    55	And supplying --programmer-model "gemini-4-pro-high" via CLI overrides both .devtool/review_config.json and environment variables
    56	
    57	Scenario: [TTO-HP-05] [Tier C - Integration] Slimmed rules and dev-designer skill satisfy byte caps and release contract checks
    58	
    59	Given the updated rules/CRITICAL_RULES.md, skills/dev-designer/SKILL.md, and skills/task-observer/SKILL.md in the repository
    60	When scripts/test_lifecycle_document_contract.py executes and file byte sizes are measured on disk
    61	Then rules/CRITICAL_RULES.md measures at most 8192 bytes and contains the Zero-Fluff Output Cap directive
    62	And skills/dev-designer/SKILL.md measures at most 22528 bytes while preserving every required section and Extracted reference link
    63	And skills/task-observer/SKILL.md contains an explicit <SUBAGENT-STOP> instruction preventing invocation in subagents and headless workers
    64	And scripts/test_lifecycle_document_contract.py exits with status 0 and zero assertion failures
    65	
    66	Scenario: [TTO-HP-06] [Tier C - Integration] Compact context restoration caps output at 4096 bytes and reads programmer config dynamically
    67	
    68	Given a multi-repo workspace directory with active epic metadata, tasks, and open RFC entries
    69	And .devtool/review_config.json configures providers.programmer to "gemini-4-hydrogen-xhigh" with thinking_level "xhigh"
    70	When scripts/resume_context.py runs with --compact --epic token_throttling_optimization and --emit-prompt implement
    71	Then the compact context payload measures at most 4096 bytes and includes active epic snapshot, current repo git status, matching tasks, and relevant open RFCs
    72	And the emitted handoff prompt specifies "gemini-4-hydrogen-xhigh" and "xhigh" read dynamically from .devtool/review_config.json
    73	
    74	Scenario: [TTO-HP-07] [Tier C - Integration] Streamlined cross-model review fast-tracks clean code fixes and renders actual Executive Report findings
    75	
    76	Given a cross-model review Round 1 verdict of CHANGES_REQUIRED containing only verified code bugs with zero shared-contracts conflicts
    77	When lifecycle_runner.step_cross_model_review executes one remediation iteration followed by convergence
    78	Then unambiguous code fixes bypass _draft_fix_plan and evaluate_programmer_fix_plan and route directly to _apply_code_fixes
    79	And render_final_executive_report populates the Top 3 Highest-Risk Findings table directly from parsed review_results.md and principal_review.md entries rather than placeholder strings
    80	
    81	Scenario: [TTO-HP-08] [Tier C - Integration] End-to-end token-throttling pipeline enforces compact prompts, review isolation, and programmer config
    82	
    83	Given an isolated epic workspace bootstrapped with .devtool/review_config.json, task files containing target line ranges, and fake review/agy CLIs
    84	When the lifecycle pipeline executes readiness, external review, worker dispatch, compact Gate 4, and executive summary generation
    85	Then every review prompt respects the diff-only -U5 budget and writes raw output outside markdown files
    86	And every worker prompt omits inlined source files while invoking gemini-4-hydrogen-xhigh with --effort xhigh
    87	And compact Gate 4 emits single-line GATE_PASS statuses upon green verification
    88	```
    89	
    90	## Edge Cases and Boundaries
    91	
    92	```gherkin
    93	Scenario: [TTO-EC-01] [Tier A - Unit] Over-budget diff truncates to --stat summary and @@ hunk headers per changed file
    94	
    95	Given a synthetic git diff exceeding MAX_DIFF_LINES (1500 lines) or MAX_DIFF_BYTES (60000 bytes)
    96	When build_diff_section builds the diff payload for external review
    97	Then the output falls back cleanly within the byte budget without dropping structural file boundaries
    98	And the truncated section explicitly contains the git diff --stat summary alongside the file headers and @@ hunk headers for changed files
    99	
   100	Scenario: [TTO-EC-02] [Tier A - Unit] Task runner enforces 25-line tail and Python quality manifests inject quiet pytest flags
   101	
   102	Given a failing task check output with 120 stdout/stderr lines
   103	And .agents/quality/python-quality.json alongside a scaffolded manifest from scaffold_quality_manifest.py
   104	When run_task_checks.py formats failure evidence and the Python test command is inspected
   105	Then run_task_checks.TAIL_LINES equals 25 and the emitted snippet retains only the last 25 non-empty lines
   106	And both .agents/quality/python-quality.json and newly scaffolded Python quality manifests invoke pytest with "-q", "--tb=short", and "--maxfail=3"
   107	
   108	Scenario: [TTO-EC-03] [Tier C - Integration] Design contract checker rejects large >200-line modified files lacking target symbol or line-range anchors
   109	
   110	Given a task file referencing a non-new tracked Python source file exceeding 200 lines in Allowed files
   111	And the task's Files and Impact Analysis sections omit any target symbol name or (L<start>-L<end>) line range for that file
   112	When check_task_contract.py executes with --design against that task file
   113	Then check_task_contract.py exits non-zero and reports the missing symbol or line-range anchor for that >200-line file
   114	And adding a valid "path :: Symbol (L10-L85)" anchor clears the violation and exits with status 0
   115	
   116	Scenario: [TTO-EC-04] [Tier A - Unit] Programmer effort normalization maps "extra" aliases to xhigh
   117	
   118	Given raw effort values "extra", "EXTRA", "extra-high", "extra_high", and "xhigh"
   119	When lifecycle_runner.normalize_agy_effort normalizes each configured thinking level
   120	Then every variant returns the canonical flag value "xhigh"
   121	And invoking the agy command builder passes "--effort", "xhigh" on the command line
   122	
   123	Scenario: [TTO-EC-05] [Tier C - Integration] Selective task-reviewer gating skips trivial tasks and activates on high-risk or multi-module tasks
   124	
   125	Given a trivial single-file documentation or utility task without high-risk labels and review_tier unset
   126	And a complex task carrying review_tier: "full" or labels ["security", "concurrency"] or touching 3 non-test modules
   127	When the selective task-reviewer criteria documented across dev-designer, dev-implementation, and subagent-driven-development are evaluated
   128	Then the trivial single-file task skips the redundant task-reviewer subagent pass
   129	And the complex or high-risk task triggers the dedicated task-reviewer pass before task sign-off
   130	
   131	Scenario: [TTO-EC-06] [Tier C - Integration] Compact verify.sh --quiet prints concise section lines while --full executes all 17 suites
   132	
   133	Given the repository tooling scripts and markdown skills under scripts/verify.sh
   134	When bash scripts/verify.sh --quiet runs and when bash scripts/verify.sh --full runs
   135	Then --quiet prints a single concise status line per passing section without verbose suite noise
   136	And --full executes all registered verification sections §1 through §17 and exits with status 0
   137	```
   138	
   139	## State Transitions and Invariants
   140	
   141	```gherkin
   142	Scenario: [TTO-ST-01] [Tier A - Unit] load_review_config migrates legacy gemini-3.8-flash defaults while preserving custom models
   143	
   144	Given an existing .devtool/review_config.json with providers.programmer.model set to "gemini-3.8-flash-high"
   145	And a second config file where providers.programmer.model is customized to "claude-sonnet-4-6"
   146	When run_external_review.load_review_config loads each configuration file
   147	Then the legacy "gemini-3.8-flash-high" entry is upgraded in-memory to "gemini-4-hydrogen-xhigh" with thinking_level "xhigh"
   148	And the user-customized "claude-sonnet-4-6" entry remains untouched without being overwritten
   149	
   150	Scenario: [TTO-ST-02] [Tier C - Integration] Handoff package and template exclude .vi.md files from AI coder Read First list
   151	
   152	Given an epic directory containing spec.en.md, spec.vi.md, epic.en.md, epic.vi.md, bdd_scenarios.en.md, and bdd_scenarios.vi.md
   153	When package_epic.py generates handoff.md from skills/dev-lifecycle/references/handoff-template.md
   154	Then the generated Read First section references only *.en.md documents and zero *.vi.md paths
   155	And handoff-template.md contains no static legacy model hardcodes conflicting with config-driven Role 2.3 selection
   156	
   157	Scenario: [TTO-ST-03] [Tier C - Integration] Stage 4 --strict-bilingual readiness gate enforces full .en.md and .vi.md parity
   158	
   159	Given an epic directory whose .vi.md HLD has drifted behind .en.md or lacks bdd_scenarios.vi.md
   160	When check_epic_readiness.py runs with --strict-bilingual and check_bdd_traceability.py runs with --strict-bilingual
   161	Then both commands exit non-zero highlighting the missing or out-of-sync Vietnamese mirror files
   162	And after synchronizing .vi.md and adding bdd_scenarios.vi.md with matching IDs and ToC headings, both --strict-bilingual checks exit with status 0
   163	
   164	Scenario: [TTO-ST-04] [Tier C - Integration] Cross-model review escalates to Role 2.2 when shared-contracts or architecture ambiguity arises
   165	
   166	Given a cross-model review finding in Round 1 referencing shared-contracts/api_contract.md or an ambiguous architectural state transition
   167	When lifecycle_runner.step_cross_model_review triages the round findings
   168	Then fast-path auto-fix is NOT taken and either CRITICAL_CONFLICT halts immediately or fix_plan_round1.md is routed through Role 2.2 evaluation before any edit occurs
   169	
   170	Scenario: [TTO-ST-05] [Tier C - Integration] Finishing-a-development-branch Stage 4 Pre-Finish hook synchronizes .vi.md before merge
   171	
   172	Given skills/finishing-a-development-branch/SKILL.md in the updated agent kit
   173	When the Stage 4 finishing workflow specification is inspected and checked by verify.sh §3 and §8
   174	Then an explicit Stage 4 Pre-Finish bilingual sync step delta-syncs Spec and HLD .vi.md companions, generates bdd_scenarios.vi.md, and runs check_epic_readiness.py --strict-bilingual before merge
   175	And all cross-references and doc contract invariants remain unbroken under verify.sh
   176	```
   177	
   178	## Async and Concurrency
   179	
   180	```gherkin
   181	Scenario: [TTO-AR-01] [Tier C - Integration] Parallel wave dispatch executes independent tasks concurrently with path-only Zero-Fluff prompts
   182	
   183	Given an epic DAG containing two disjoint Wave 1 tasks (no mutual blocker dependency) and one Wave 2 task blocked by both
   184	And an isolated worker pool initialized by manage_worker_pool.py
   185	When lifecycle_runner.step_implementation executes the implementation phase using a thread-safe recording mock dispatcher
   186	Then both Wave 1 tasks run concurrently inside distinct pool slots before Wave 2 begins
   187	And each task prompt omits inlined task markdown bodies, injects only target file paths and line ranges, and includes the Zero-Fluff output cap
   188	
   189	Scenario: [TTO-AR-02] [Tier C - Integration] Per-task clean context and per-round raw logs prevent cross-session transcript contamination
   190	
   191	Given two sequential or parallel review rounds and consecutive task dispatches within a single epic run
   192	When run_external_review.render_round writes logs and lifecycle_runner invokes Task N+1 after Task N commits
   193	Then each review round writes its isolated raw transcript to build/reviews/<epic>_round<n>.raw.log without appending into markdown review tables or adjacent round logs
   194	And the Task N+1 invocation prompt contains no accumulated tool output or stderr from Task N
   195	```
   196	
   197	## Failure and Resilience
   198	
   199	```gherkin
   200	Scenario: [TTO-FR-01] [Tier A - Unit] collect_facts emits one line per passing command and caps failing output + raw transcripts
   201	
   202	Given a passing command returning 180 stdout lines with exit code 0 and a failing command returning 90 stderr lines with exit code 1
   203	When run_external_review.fact builds prompt evidence and render_round persists the round artifact
   204	Then the passing command produces a single "PASS: <label>" line omitting stdout
   205	And the failing command includes the command label plus at most 25 trailing non-empty output lines
   206	And unfiltered CLI stdout/stderr is routed into build/reviews/<epic>_round<n>.raw.log so principal_review.md remains compact
   207	
   208	Scenario: [TTO-FR-02] [Tier C - Integration] Compact Gate 4 surfaces failing provider header and 25-line log tail on error
   209	
   210	Given a quality registry containing one passing capability and one failing capability printing 80 diagnostic lines to stderr
   211	When verify_polyglot_registry.py runs with --compact
   212	Then the process exits non-zero reporting FAIL
   213	And standard output prints "GATE_PASS:" for the passing capability plus the failing capability header and strictly at most 25 trailing log lines from build/quality/
   214	And all 80 raw diagnostic lines remain preserved on disk inside build/quality/<provider>/<cap>.log
   215	
   216	Scenario: [TTO-FR-03] [Tier A - Unit] lifecycle_runner._tail_lines bounds Gate 4 and intermediate check failure summaries to 25 lines
   217	
   218	Given a subprocess failure from run_gate4 or run_intermediate_check emitting 120 traceback lines
   219	When lifecycle_runner formats the failure message via _tail_lines(output, 25)
   220	Then the returned failure excerpt contains at most 25 lines terminating at the final failing assertion summary
   221	And the exception or state message propagated to the next step never exceeds 25 lines of traceback
   222	
   223	Scenario: [TTO-FR-04] [Tier C - Integration] Quantitative regression tests fail loudly if rule, skill, context, or prompt sizes exceed caps
   224	
   225	Given the live kit files and mock epic harness inside tests/test_token_throttling_acceptance.py
   226	When the quantitative token-throttling acceptance suite executes under pytest
   227	Then assertions explicitly check byte ceilings (CRITICAL_RULES.md <= 8192, dev-designer/SKILL.md <= 22528, resume_context --compact <= 4096) and review/prompt budgets
   228	And exceeding any ceiling fails with concrete byte-count diagnostics rather than generic boolean checks
   229	```
zsh:1: command not found: -v
# ai-agent-tools — working on the kit itself

This repository is the shared agent kit for mobile projects. It is consumed as a plugin by
Antigravity and Claude Code; see [README.md](README.md) for installation.

## Rules

@rules/CRITICAL_RULES.md
@rules/coding-guidelines.md

## When editing skills

- `skills/<name>/SKILL.md` frontmatter is exactly `name` + `description`. No other keys —
  an unrecognised key risks a silent frontmatter parse failure.
- `description` drives activation in both runtimes. State *what* the skill does and *when*
  to use it, in third person.
- Keep `SKILL.md` concise; both runtimes load skills by progressive disclosure. Bulk material
  belongs in the skill's `references/`, `scripts/`, `resources/` or `examples/`.
- Cross-references between skills in this kit use the `d3nexus:` namespace.
- Changing a skill affects every project on every machine that has the plugin installed.
  Verify before publishing: internal links resolve, ToC anchors match headings, and any
  mermaid diagram renders.

## Verifying before a release

```bash
scripts/verify.sh
```

exec
/bin/zsh -lc 'nl -ba .devtool/epic/token_throttling_optimization/2026-11-13-token-throttling-optimization-design.vi.md; nl -ba .devtool/epic/token_throttling_optimization/token_throttling_optimization.vi.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	# Đặc tả Thiết kế: Tối ưu hóa Token toàn diện cho Dev Lifecycle
     2	
     3	## Mục lục
     4	
     5	- [1. Bối cảnh và các điểm tiêu tốn Token thực tế](#1-bối-cảnh-và-các-điểm-tiêu-tốn-token-thực-tế)
     6	- [2. Mục tiêu và Phi mục tiêu](#2-mục-tiêu-và-phi-mục-tiêu)
     7	- [3. Kiến trúc và Thiết kế cốt lõi](#3-kiến-trúc-và-thiết-kế-cốt-lõi)
     8	- [4. Thay đổi chi tiết theo thành phần](#4-thay-đổi-chi-tiết-theo-thành-phần)
     9	  - [4.1 Review chỉ theo Diff và Cách ly Transcript](#41-review-chỉ-theo-diff-và-cách-ly-transcript)
    10	  - [4.2 Silent Gate 4 và Cắt gọn Output Kiểm thử](#42-silent-gate-4-và-cắt-gọn-output-kiểm-thử)
    11	  - [4.3 Đọc File phẫu thuật và Giới hạn Dòng mục tiêu](#43-đọc-file-phẫu-thuật-và-giới-hạn-dòng-mục-tiêu)
    12	  - [4.4 Cách ly Context Task và Selective Task Reviewer](#44-cách-ly-context-task-và-selective-task-reviewer)
    13	  - [4.5 Giới hạn Output, Rút gọn Rules và Skills](#45-giới-hạn-output-rút-gọn-rules-và-skills)
    14	  - [4.6 Luồng Song ngữ Option A](#46-luồng-song-ngữ-option-a)
    15	  - [4.7 Cấu hình Programmer Persona qua File Config và Gemini 4 Hydrogen](#47-cấu-hình-programmer-persona-qua-file-config-và-gemini-4-hydrogen)
    16	- [5. Chiến lược Kiểm thử và Bất biến của Kit](#5-chiến-lược-kiểm-thử-và-bất-biến-của-kit)
    17	- [6. Cảnh báo Shared Contract](#6-cảnh-báo-shared-contract)
    18	
    19	## 1. Bối cảnh và các điểm tiêu tốn Token thực tế
    20	
    21	Kết quả rà soát toàn bộ workflow, rules, hooks và runner scripts trong `ai-agent-tools` đã chỉ ra 5 nguyên nhân gốc gây phình context theo hàm bậc hai và cạn quota across `dev-lifecycle` (cả Manual và Autonomous mode):
    22	
    23	1. **Chi phí nền cố định (Always-On)**: `rules/CRITICAL_RULES.md` (`32,773` bytes / `239` dòng) bị nạp vào mọi hội thoại, mọi subagent và mọi lần gọi headless CLI (hiện bị IDE cắt `<truncated 8848 bytes>`). `skills/task-observer/SKILL.md` (`31,480` bytes / `526` dòng) thiếu thẻ `<SUBAGENT-STOP>`, ép subagent và review CLI đọc toàn bộ trước tool call đầu tiên. `scripts/resume_context.py` in `26,759` bytes (`310` dòng) qua toàn bộ các repo theo mặc định.
    24	2. **Phình Context bậc hai trong Review (`O(R^2)`)**: Trong `skills/dev-implementation/resources/scripts/run_external_review.py`, từ Round >= 2 vẫn truyền đồng thời full diff `base...sha` (`diff_section`) lẫn `delta_round_context()`, lặp lại cả `.en.md` và `.vi.md`, đổ toàn bộ log tiền kiểm qua `fact()` dù lệnh pass (`exit 0`), dùng ngữ cảnh diff 3 dòng mặc định (`-U10` trong `review-package`), và lưu nguyên `stderr` transcript của CLI vào mục `Raw output:` trong `principal_review.md` (đo thực tế tới `1,885,237` bytes / `23,450` dòng ở `autonomous_lifecycle_runner`).
    25	3. **Quality Gates quá dài dòng và không cắt traceback**: `skills/quality_check/resources/scripts/verify_polyglot_registry.py` in nguyên JSON lớn ngay cả khi `PASS`; `.agents/quality/python-quality.json` chạy `pytest` không có `-q --tb=short --maxfail=3`; `run_task_checks.py` giữ `40` dòng cuối; `lifecycle_runner.py` và `scripts/verify.sh` trả nguyên `stdout`/`stderr` khi fail không giới hạn 25 dòng.
    26	4. **Đọc file thô và Vòng lặp Subagent dư thừa**: `dev-designer/SKILL.md` (`66,425` bytes) chưa yêu cầu `target_files` kèm dải dòng/symbol trong task breakdown; `_execute_single_task()` trong `lifecycle_runner.py` chạy `agy` tuần tự thay vì pool `manage_worker_pool.py` / chỉ dẫn đọc cắt lát; vòng fix `cross-model-review` gọi 3 process LLM liên tiếp (`_draft_fix_plan` -> `evaluate_programmer_fix_plan` -> `_apply_code_fixes`) cả với lỗi code thuần `Valid`; chế độ Interactive chạy `task-reviewer` cho mọi task nhỏ dù cuối epic vẫn chạy `cross-model-review`.
    27	5. **Thiếu giới hạn Output và Dịch đi dịch lại `.vi.md`**: Chưa có quy tắc giới hạn output token ở các stage, đồng thời Spec, HLD và Gherkin BDD phải duy trì song ngữ `.en.md` / `.vi.md` liên tục suốt Stage 1, Stage 2 và mọi vòng Principal Review.
    28	
    29	## 2. Mục tiêu và Phi mục tiêu
    30	
    31	Mục tiêu:
    32	
    33	- Thực thi cơ học 5 Quy tắc siết Token trên toàn bộ scripts, prompts, task schema, rules và skills mà không làm yếu TDD (`RED -> GREEN`), BDD traceability, architecture gates hay Circuit Breakers.
    34	- Triển khai đồng thời cả Phase 1 (tối ưu runner/script cơ học) và Phase 2 (rút gọn rules, schema task, slimming skills, khử trùng lặp references).
    35	- Áp dụng Luồng Song ngữ Option A: giữ Spec và HLD `.vi.md` cho con người review ở Gate 1 và Gate 2, loại bỏ hoàn toàn `.vi.md` khỏi các pipeline LLM review/coding, hoãn sinh `bdd_scenarios.vi.md` và delta-sync `.vi.md` tới bước `/finishing-a-development-branch`, không xóa và không dịch lại từ đầu.
    36	- Kích hoạt `task-reviewer` theo chọn lọc trong Stage 3 chỉ cho các task phức tạp/rủi ro cao; task mechanical dựa vào `run_task_checks.py` + `/cross-model-review` cuối epic.
    37	
    38	Phi mục tiêu:
    39	
    40	- Bỏ qua hoặc tự phê duyệt thay con người ở các Gate 1 (Spec), Gate 2 (Task Breakdown), Gate 5 (Finish & Merge).
    41	- Tắt full regression suite, Playwright E2E hoặc `@quality_check` tại Final Convergence Gate và Stage 4 `verify-tier`.
    42	- Tự động push commit/nhánh lên remote khi chưa có xác nhận rõ ràng của người dùng.
    43	
    44	## 3. Kiến trúc và Thiết kế cốt lõi
    45	
    46	```mermaid
    47	flowchart TD
    48	    RULES["Rút gọn CRITICAL_RULES <= 8KB + Output Cap + task-observer SUBAGENT-STOP"] --> S1["Stage 1 dev-brainstorming: Spec .en.md + .vi.md cho Human"]
    49	    S1 --> S2["Stage 2 dev-designer: HLD .en.md + .vi.md + bdd_scenarios.en.md + Task Line Ranges"]
    50	    S2 --> PR["Principal Review: Chỉ .en.md + Delta Diff -U5 + Quiet Pre-checks + Tách Log"]
    51	    PR --> PKG["package_epic.py: Loại .vi.md khỏi handoff Read First"]
    52	    PKG --> S3["Stage 3 TDD: Đọc giới hạn dòng + Cách ly Task + Selective task-reviewer"]
    53	    S3 --> G4["Gate 4 Silent Mode: 1 dòng GATE_PASS / 25 dòng cuối khi fail"]
    54	    G4 --> CMR["Cross-Model Review: Delta -U5 Round 2..3 + Fix trực tiếp code bug"]
    55	    CMR --> FIN["Stage 4 finishing-a-development-branch: Delta-Sync .vi.md + Gen bdd_scenarios.vi.md + verify-tier"]
    56	```
    57	
    58	## 4. Thay đổi chi tiết theo thành phần
    59	
    60	### 4.1 Review chỉ theo Diff và Cách ly Transcript
    61	
    62	- **Chuẩn hóa `git diff -U5` và Fallback có kiểm soát**: Cập nhật `build_diff_section()` trong `skills/dev-implementation/resources/scripts/run_external_review.py` và `skills/subagent-driven-development/scripts/review-package` sang `git diff -U5`. Khi diff vượt ngưỡng `MAX_DIFF_LINES` (`1500`) hoặc `MAX_DIFF_BYTES` (`60000`), xuất `git diff --stat` cùng danh sách hunk header (`@@ ... @@`) thay vì để trống khiến model tự đọc full file.
    63	- **Loại trùng `base...sha` ở Round >= 2**: Trong `run_external_review.py` (`run()`), khi `round_num >= 2` và `delta_round_context()` hoạt động, bỏ `diff_section` (`base...sha`) dư thừa. Chỉ truyền diff `prev_sha..sha` (`-U5`), Prior Fixed Locations Registry, bảng findings đang mở rút gọn (<= 200 ký tự mỗi ô) và Acceptance Criteria / phần task liên quan.
    64	- **Chỉ dùng `.en.md` SSOT cho AI Review**: Cập nhật `principal_artefact_lines()` và `collect_facts()` trong `run_external_review.py` để loại toàn bộ file `*.vi.md` khỏi prompt external reviewer.
    65	- **Quiet Pre-Check Facts**: Thay output nguyên văn của `fact()` trong `collect_facts()` bằng 1 dòng `PASS: <label>` khi `returncode == 0`, và chỉ giữ lệnh lỗi + 25 dòng cuối khi khác `0`.
    66	- **Cách ly Transcript (`Raw output:`)**: Trong `render_round()`, ghi toàn bộ `stderr` transcript của external CLI ra file git-ignored `build/reviews/<epic>_round<n>.raw.log`; file `principal_review.md` và `review_results.md` chỉ lưu Verdict, Pass summary, Bảng Findings và đường dẫn file log (triệt tiêu lỗi file `1.88 MB`).
    67	- **Quy tắc Prompt**: Bổ sung ràng buộc `DIFF-ONLY REVIEW` vào `principal-review-prompt.md` và `external-review-prompt.md`, cấm đọc toàn bộ source/spec trừ khi truy vết một symbol/caller cụ thể còn thiếu.
    68	
    69	### 4.2 Silent Gate 4 và Cắt gọn Output Kiểm thử
    70	
    71	- **Cờ chạy test gọn mặc định**: Bắt buộc `pytest -q --tb=short --maxfail=3` trong `.agents/quality/python-quality.json`, template của `setup_quality_check` và bảng Verification mẫu trong `dev-designer/SKILL.md`.
    72	- **Output rút gọn ở Polyglot & Task Runners**:
    73	  - Thêm `--compact` (mặc định cho caller trong lifecycle, giữ nguyên full log tại `build/quality/<provider>/<cap>.log`) vào `skills/quality_check/resources/scripts/verify_polyglot_registry.py` và cập nhật `quality_check/SKILL.md`: in đúng 1 dòng `GATE_PASS: <provider_or_cap>` khi đạt, và in summary lỗi + 25 dòng cuối traceback từ `.log` khi thất bại.
    74	  - Đổi `TAIL_LINES = 25` trong `skills/dev-implementation/resources/scripts/run_task_checks.py`.
    75	  - Thêm helper `_tail_lines(text, limit=25)` trong `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` cho `run_gate4()` và `run_intermediate_check()` để chỉ trả về summary + 25 dòng cuối khi fail và `GATE_PASS: <check_name>` khi pass.
    76	  - Thêm `--quiet` (1 dòng mỗi mục) và cắt đuôi 25 dòng khi lỗi vào `scripts/verify.sh` (giữ nguyên chế độ đầy đủ khi debug).
    77	
    78	### 4.3 Đọc File phẫu thuật và Giới hạn Dòng mục tiêu
    79	
    80	- **Nâng cấp Schema Task**: Cập nhật mẫu task trong `skills/dev-designer/SKILL.md` (`## Files` / `## Impact Analysis & Blast Radius`) bắt buộc mỗi file có sẵn >200 dòng cần sửa phải ghi rõ `target_files` kèm tên symbol và dải dòng (`path :: Symbol (L<start>-L<end>)`) bên cạnh `Allowed files`.
    81	- **Kiểm tra Contract**: Cập nhật `check_task_contract.py --design` để kiểm tra file tracked >200 dòng trong `Allowed files` (không đánh dấu `(new)`) phải khai báo neo symbol/dải dòng mục tiêu.
    82	- **Kỷ luật Đọc ở Stage 3**: Cập nhật `dev-implementation/SKILL.md`, `skills/dev-lifecycle/references/handoff-template.md`, `implementer-prompt.md` và `lifecycle_runner.py` (`_execute_single_task()`) để ép đọc giới hạn dòng (`read_file` với `StartLine`/`EndLine` hoặc `sed -n 'X,Yp'`) và tìm theo symbol trước khi sửa.
    83	
    84	### 4.4 Cách ly Context Task và Selective Task Reviewer
    85	
    86	- **Cách ly tuyệt đối theo Task & Handoff gọn**:
    87	  - Ở `subagent-driven-development`, giữ cơ chế `task-brief` + report ra file giúp Task `N+1` khởi tạo sạch không mang lịch sử tool-call của Task `1..N`.
    88	  - Ở `lifecycle_runner.py` (`step_implementation()` và `_execute_single_task()`), chỉ truyền đường dẫn `task_file`, `handoff.md` thay vì dán toàn văn nội dung, và điều phối các tầng topological độc lập qua `manage_worker_pool.py`.
    89	- **Cơ chế kích hoạt Selective `task-reviewer`**:
    90	  - Quy định điều kiện kích hoạt `task-reviewer` (dùng `review-package` với `-U5`) trong `dev-designer/SKILL.md`, `dev-implementation/SKILL.md` và `subagent-driven-development/SKILL.md` chỉ khi task có `review_tier: "full"` trong frontmatter, `labels` giao với `{"security", "architecture", "concurrency", "contract"}`, hoặc phần `Allowed files` non-test chạm >2 module.
    91	  - Task mechanical chuẩn dựa vào `run_task_checks.py` TDD (`RED`, `GREEN`, `TIER-B`, `TIER-C`) và `/cross-model-review` cuối epic.
    92	- **Tinh gọn Fix Loop tự động & Executive Report động**:
    93	  - Trong `lifecycle_runner.py` (`step_cross_model_review()`), nếu các findings `Valid` chỉ là bug code không chạm `shared-contracts/` và không có `CRITICAL_CONFLICT`, cho Role 2.3 sửa trực tiếp + chạy scoped tests mà bỏ qua cặp gọi thừa `_draft_fix_plan` -> `evaluate_programmer_fix_plan` (giữ Role 2.2 đánh giá khi có xung đột contract/kiến trúc).
    94	  - Sửa `render_final_executive_report()` trong `lifecycle_runner.py` để tổng hợp findings và commit SHA thật từ `review_results.md` / `principal_review.md` thay vì các dòng mẫu hardcode.
    95	
    96	### 4.5 Giới hạn Output, Rút gọn Rules và Skills
    97	
    98	- **Quy tắc Zero-Fluff Output Cap**: Bổ sung bộ 5 quy tắc giới hạn output vào `rules/CRITICAL_RULES.md`, `dev-lifecycle/SKILL.md`, `dev-implementation/SKILL.md`, `quality_check/SKILL.md`, `finishing-a-development-branch/SKILL.md` và prompts của `lifecycle_runner.py`: không chào hỏi/diễn giải lại đề bài, không in lại code giữ nguyên, không giải thích test đã pass; chỉ xuất `[STATE]`, tool calls và tối đa 3 bullet nguyên nhân gốc khi lỗi.
    99	- **Rút gọn Rules & Bảo vệ Subagent**:
   100	  - Nén `rules/CRITICAL_RULES.md` từ `32,773` bytes xuống `<= 8,192` bytes (hết bị IDE cắt `<truncated>`) bằng cách giữ các mệnh đề `MUST`/`NEVER` súc tích và chuyển hướng dẫn chi tiết sang `skills/dev-lifecycle/references/`, bảo toàn ngữ nghĩa Rule 1–9 và các bài check trong `scripts/verify.sh`.
   101	  - Thêm thẻ `<SUBAGENT-STOP>` ở đầu `skills/task-observer/SKILL.md` để subagents và external review CLIs bỏ qua việc nạp `31.4 KB` file này.
   102	- **Lọc phạm vi `resume_context.py`**: Thêm `--compact` (mặc định kích hoạt khi có `--epic <slug>`) trong `scripts/resume_context.py` để Role 2.2 / Role 2.3 chỉ nạp state của epic đang làm, git status repo hiện tại, RFC mở liên quan và task thuộc epic (~2–3 KB thay vì `26.7 KB`).
   103	- **Tối ưu Progressive Disclosure & Khử trùng lặp**:
   104	  - Rút gọn `skills/dev-designer/SKILL.md` (`66.4 KB` -> `<= 22 KB`) và `skills/quality_check/SKILL.md` bằng cách đẩy ví dụ platform/template dài sang `references/`.
   105	  - Hợp nhất các file trùng lặp giữa `skills/dev-implementation/references/`, `skills/principal-review/references/` và `skills/cross-model-review/references/` về một bản chuẩn, đảm bảo mọi liên kết tương đối qua `scripts/verify.sh`.
   106	
   107	### 4.6 Luồng Song ngữ Option A
   108	
   109	- **Stage 1 & Stage 2 (Human Review)**: `dev-brainstorming` tạo cặp Spec `.en.md` + `.vi.md`; `dev-designer` tạo cặp HLD `<epic>.en.md` + `<epic>.vi.md` và chỉ tạo `bdd_scenarios.en.md` (hoãn `bdd_scenarios.vi.md` đến Stage 4).
   110	- **Dung sai trong lúc thực thi (`check_epic_readiness.py` & `check_bdd_traceability.py`)**: Giữ nguyên Spec và HLD `.vi.md` trên disk cho người dùng đọc (không xóa), thêm chế độ mặc định in-flight trên `check_epic_readiness.py` (kèm cờ `--strict-bilingual` cho Gate 5 / Finish) và `check_bdd_traceability.py` để các chỉnh sửa Principal Review trên `.en.md` hoặc việc chưa có `bdd_scenarios.vi.md` không làm fail `R1`/`R3`/`R7` giữa chừng; đồng thời bỏ `.vi.md` khỏi `handoff.md` (`Read First`) và `run_external_review.py`.
   111	- **Đồng bộ tại Stage 4 Pre-Finish (`/finishing-a-development-branch`)**: Cập nhật Pre-Finish Hook (trước commit archive ở Option 1 và Option 2) để delta-sync thay đổi sang Spec/HLD `.vi.md`, sinh `bdd_scenarios.vi.md` một lần duy nhất, rồi nghiệm thu lại bằng `check_document.py --require-toc --require-bilingual` và `check_epic_readiness.py --strict-bilingual`.
   112	
   113	### 4.7 Cấu hình Programmer Persona qua File Config và Gemini 4 Hydrogen
   114	
   115	- **Nguồn chân lý cấu hình (`.devtool/review_config.json`)**: Bổ sung `"assistant"` và `"programmer"` vào `DEFAULT_REVIEW_CONFIG["providers"]` trong `run_external_review.py` và chuẩn hóa `.devtool/review_config.json["providers"]["programmer"]` với mặc định `model: "gemini-4-hydrogen-xhigh"` và `thinking_level: "xhigh"` (thay thế mặc định hardcode `Gemini Flash 3.8`).
   116	- **Thứ tự ưu tiên & Ánh xạ Effort (`lifecycle_runner.py`)**: Thêm `resolve_programmer_model()` và `resolve_programmer_effort()` trên `RunnerConfig` theo thứ tự ưu tiên `CLI (--programmer-model / --programmer-effort) -> Runner --config JSON -> .devtool/review_config.json["providers"]["programmer"] -> env (AGY_PROGRAMMER_MODEL / AGY_PROGRAMMER_EFFORT) -> fallback ("gemini-4-hydrogen-xhigh", "xhigh")`; đổi default trên `argparse` cho `--programmer-model` / `--programmer-effort` thành `None` để không che khuất file config. Chuẩn hóa các alias `"extra"`, `"extra-high"`, `"extra_high"` và `"xhigh"` sang cờ `agy` CLI `--effort xhigh` (`low|medium|high|xhigh|max`).
   117	- **Đồng bộ Handoff Prompt, Rules và Skills**: Cập nhật `resume_context.py` (`emit_handoff_prompt`), `rules/CRITICAL_RULES.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-lifecycle/references/autonomous-mode.md`, `skills/dev-implementation/SKILL.md` và `skills/principal-review/SKILL.md` để đọc/tham chiếu `.devtool/review_config.json` (`providers.programmer`, mặc định `gemini-4-hydrogen-xhigh`, effort `xhigh`) thay vì hardcode `Gemini Flash 3.8` (giữ nguyên nhãn hiển thị quota bucket trên `agy_quota.py` và dashboard UI).
   118	
   119	## 5. Chiến lược Kiểm thử và Bất biến của Kit
   120	
   121	- Bảo toàn toàn bộ kiểm định phát hành bằng `bash scripts/verify.sh --full` (`42+` suite, JSON manifest, YAML frontmatter, relative links, ToC anchors, Section 7 methodology fidelity, Section 8 unreferenced supporting files, và `scripts/test_lifecycle_document_contract.py`).
   122	- Bổ sung unit & integration tests cho:
   123	  - `test_run_external_review.py`: ngữ cảnh diff `-U5`, không lặp `base...sha` ở Round 2, quiet `collect_facts()`, loại trừ `.vi.md` và tách `stderr` transcript ra `build/reviews/`.
   124	  - `test_lifecycle_runner.py`: silent Gate 4 pass / cắt đuôi 25 dòng lỗi, worker pool parallel dispatch, fix loop tinh gọn cho code bug, `render_final_executive_report()` đọc findings thật, và thứ tự ưu tiên `resolve_programmer_model()` / `resolve_programmer_effort()` kèm ánh xạ `"extra"` -> `"xhigh"`.
   125	  - `test_check_epic_readiness.py` và `test_integrate_branch.py`: Option A hoãn `bdd_scenarios.vi.md` ở Stage 2/Review vs `--strict-bilingual` ở Stage 4 Finish, và check dải dòng trong `check_task_contract.py`.
   126	  - `test_resume_context.py` và `test_aggregate_quality_results.py`: output `--compact` theo epic, `emit_handoff_prompt` lấy Programmer model từ config và định dạng `GATE_PASS:`.
   127	- Đo kiểm định lượng trước/sau cho dung lượng `CRITICAL_RULES.md`, `dev-designer/SKILL.md`, `resume_context.py --epic <slug> --compact` và kích thước artefact `principal_review.md`.
   128	
   129	## 6. Cảnh báo Shared Contract
   130	
   131	Repository `ai-agent-tools` không chứa thư mục `shared-contracts/` (đây là bộ workflow kit độc lập, không phải Hub/Satellite dịch vụ). Mọi hợp đồng CLI nội bộ giữa `run_external_review.py`, `check_epic_readiness.py`, `verify_polyglot_registry.py`, `resume_context.py`, `lifecycle_runner.py` và `integrate_branch.py` cùng schema `.devtool/review_config.json` được giữ tương thích ngược thông qua cờ mặc định và giá trị fallback tùy chọn.
   132	
     1	# Thiết kế Cấp cao: Tối ưu hóa Token toàn diện (HLD)
     2	
     3	## Mục lục
     4	
     5	- [Meta Data](#meta-data)
     6	- [Bối cảnh](#bối-cảnh)
     7	- [Mục tiêu và Phi mục tiêu](#mục-tiêu-và-phi-mục-tiêu)
     8	- [Kiến trúc và Thiết kế Kỹ thuật](#kiến-trúc-và-thiết-kế-kỹ-thuật)
     9	- [Bản đồ Bảo trì Tính năng](#bản-đồ-bảo-trì-tính-năng)
    10	- [Hợp đồng Module và Giao diện CLI](#hợp-đồng-module-và-giao-diện-cli)
    11	- [Phân tích Tác động](#phân-tích-tác-động)
    12	- [Tác động Shared Contract](#tác-động-shared-contract)
    13	- [Kế hoạch Kiểm thử Tích hợp và Ma trận Ranh giới](#kế-hoạch-kiểm-thử-tích-hợp-và-ma-trận-ranh-giới)
    14	- [Môi trường Kiểm thử](#môi-trường-kiểm-thử)
    15	- [Phạm vi Kịch bản BDD toàn diện](#phạm-vi-kịch-bản-bdd-toàn-diện)
    16	- [Chiến lược Triển khai và Giảm thiểu Rủi ro](#chiến-lược-triển-khai-và-giảm-thiểu-rủi-ro)
    17	- [Phân rã Kanban Tasks](#phân-rã-kanban-tasks)
    18	- [Đính chính Đặc tả](#đính-chính-đặc-tả)
    19	
    20	## Meta Data
    21	
    22	- **Epic name**: `token_throttling_optimization`
    23	- **Status**: Draft
    24	- **PIC**: `danhdue`
    25	- **Target release**: Next plugin release
    26	- **Platform**: Python tooling and agent workflow kit
    27	- **Depends on epic**: none
    28	- **Source Spec**: [Đặc tả Thiết kế Tối ưu hóa Token được Phê duyệt](2026-11-13-token-throttling-optimization-design.vi.md)
    29	
    30	## Bối cảnh
    31	
    32	Đo kiểm thực tế trên `dev-lifecycle` (cả Interactive và `--autonomous`) cho thấy context phình theo hàm bậc hai và cạn quota 5 giờ nhanh chóng do 5 nguyên nhân kết hợp:
    33	
    34	1. **Chi phí nền cố định**: `rules/CRITICAL_RULES.md` (`32,773` bytes / `239` dòng) vượt ngưỡng cắt của IDE (`<truncated 8848 bytes>`), `skills/task-observer/SKILL.md` (`31,480` bytes) nạp vào mọi subagent/CLI mà thiếu thẻ chặn, và `scripts/resume_context.py` đổ `26,759` bytes qua tất cả repo.
    35	2. **Phình Context bậc hai khi External Review**: `run_external_review.py` truyền lặp full diff `base...sha` cùng `delta_round_context()` từ Round `2+`, kèm dư thừa các file `*.vi.md`, đổ toàn văn output `fact()` khi `exit 0`, dùng `-U10` trong `review-package`, và nhúng nguyên `stderr` CLI vào `principal_review.md` (tới `1.88 MB`).
    36	3. **Quality Gates quá dài và không cắt traceback**: `verify_polyglot_registry.py` in nguyên JSON khi `PASS`; `.agents/quality/python-quality.json` và `scaffold_quality_manifest.py` thiếu `-q --tb=short --maxfail=3`; `run_task_checks.py` giữ `40` dòng; `lifecycle_runner.py` và `verify.sh` thiếu chế độ compact và cắt 25 dòng cuối khi lỗi.
    37	4. **Đọc thô, Chạy tuần tự và Hardcode Model cũ**: Task thiếu neo symbol/dải dòng cho file >200 dòng; `lifecycle_runner.py` gọi `agy` tuần tự với prompt dán nội dung và hardcode `gemini-3.8-flash` thay vì đọc config `gemini-4-hydrogen-xhigh` (`--effort xhigh`); `step_cross_model_review()` gọi thừa 3 lượt LLM cho bug code thuần `Valid`; `task-reviewer` chạy cả cho task nhỏ.
    38	5. **Dịch lại Song ngữ nhiều lần**: Phải duy trì Spec, HLD và Gherkin `.vi.md` song song suốt các vòng Principal Review trước khi bản tiếng Anh hội tụ.
    39	
    40	## Mục tiêu và Phi mục tiêu
    41	
    42	### Mục tiêu
    43	
    44	- Áp dụng cơ học 5 Quy tắc siết Token trên toàn bộ runner scripts, công cụ verification, prompts, rules và skills ở cả Phase 1 (scripts cơ học) và Phase 2 (slimming, khử trùng lặp, task schema).
    45	- Triển khai Luồng Song ngữ Option A: giữ Spec và HLD `.vi.md` để con người review tại Gate 1/2, loại bỏ mọi `*.vi.md` khỏi luồng AI review/coding, mặc định dung sai trôi `.vi.md` & hoãn `bdd_scenarios.vi.md` trong `check_epic_readiness.py`, và đồng bộ một lần ở Stage 4 Pre-Finish với `--strict-bilingual`.
    46	- Kích hoạt `task-reviewer` chọn lọc chỉ cho task rủi ro cao hoặc chạm nhiều module (`review_tier: "full"`, labels `security|architecture|concurrency|contract`, hoặc `> 2` module non-test).
    47	- Cấu hình Role 2.3 (AI Programmer) qua `.devtool/review_config.json["providers"]["programmer"]` và thứ tự ưu tiên trên `RunnerConfig`, nâng mặc định lên `gemini-4-hydrogen-xhigh` và ánh xạ effort (`"extra"` / `"extra-high"` / `"xhigh"` -> `--effort xhigh`).
    48	- Áp đặt giới hạn kích thước đo được (`CRITICAL_RULES.md <= 8192` bytes, `dev-designer/SKILL.md <= 22528` bytes, `resume_context.py --compact --epic <slug> <= 4096` bytes) và giữ nguyên toàn bộ kiểm định phát hành (`scripts/verify.sh --full`).
    49	
    50	### Phi mục tiêu
    51	
    52	- Bỏ qua hoặc tự duyệt thay con người tại Gate 1 (Spec), Gate 2 (Task Breakdown), Gate 5 (Finish và Merge).
    53	- Tắt full test suite hay `@quality_check` ở Final Convergence Gate và Stage 4 `verify-tier`.
    54	- Tự động push commit hoặc branch khi chưa có lệnh xác nhận rõ ràng của người dùng.
    55	- Thay đổi nhãn hiển thị quota bucket (`Gemini 3.8 / Pro 5H`) trong `scripts/agy_quota.py` và `quota_dashboard.html`.
    56	
    57	## Kiến trúc và Thiết kế Kỹ thuật
    58	
    59	### Kiến trúc Tổng quan
    60	
    61	```mermaid
    62	flowchart TD
    63	    subgraph CFG["Lớp Cấu hình và Nền Always-On"]
    64	        RC[".devtool/review_config.json (providers.programmer)"]
    65	        CR["rules/CRITICAL_RULES.md (<= 8KB + Zero-Fluff Cap)"]
    66	        TO["skills/task-observer/SKILL.md (SUBAGENT-STOP)"]
    67	        MEM["scripts/resume_context.py (--compact + Dynamic Handoff)"]
    68	    end
    69	
    70	    subgraph S12["Stage 1 và Stage 2 Song ngữ Option A"]
    71	        DESIGN["skills/dev-designer/SKILL.md (<= 22KB + Dải dòng target_files)"]
    72	        TC["check_task_contract.py (--design Check Dải dòng)"]
    73	        READY["check_epic_readiness.py (In-Flight mặc định vs --strict-bilingual)"]
    74	        PKG["package_epic.py + handoff-template.md (Chỉ English SSOT ở Read First)"]
    75	    end
    76	
    77	    subgraph REV["Engine Review Mở rộng"]
    78	        RER["run_external_review.py (-U5 + Delta R2+ + Quiet Facts + Raw Log)"]
    79	        REVP["review-package (-U5) + Diff-Only Prompts"]
    80	    end
    81	
    82	    subgraph EXEC["Stage 3 Runner và Gate 4"]
    83	        RUN["lifecycle_runner.py (Ưu tiên Config + Pool + Fix trực tiếp)"]
    84	        POOL["manage_worker_pool.py (Pool 2-Slot Song song theo Wave)"]
    85	        G4["verify_polyglot_registry.py (--compact) + run_task_checks.py (Cắt 25 dòng)"]
    86	    end
    87	
    88	    subgraph FIN["Stage 4 Pre-Finish Hook"]
    89	        FINS["finishing-a-development-branch/SKILL.md (Delta-Sync .vi.md + Sinh bdd_scenarios.vi.md)"]
    90	        DOC["check_document.py --require-toc --require-bilingual"]
    91	    end
    92	
    93	    RC --> RUN
    94	    RC --> MEM
    95	    CR --> RUN
    96	    TO --> RUN
    97	    MEM --> RUN
    98	    DESIGN --> TC --> READY --> RER --> PKG --> RUN
    99	    REVP --> RER
   100	    RUN --> POOL
   101	    RUN --> G4
   102	    G4 --> RER
   103	    RER --> FIN
   104	    FINS --> DOC --> READY
   105	```
   106	
   107	### Luồng Hội tụ Review và Điều phối Worker Chọn lọc
   108	
   109	```mermaid
   110	sequenceDiagram
   111	    autonumber
   112	    actor Dev as Developer (Role 2.1)
   113	    participant Des as dev-designer / Readiness
   114	    participant Rev as run_external_review.py
   115	    participant Run as lifecycle_runner.py
   116	    participant Pool as Worker Pool 2-Slot / Subagent
   117	
   118	    Des->>Rev: HLD .en.md + bdd_scenarios.en.md + Tasks (loại bỏ .vi.md)
   119	    Rev->>Rev: Chạy check_epic_readiness.py (Option A in-flight) + Delta -U5
   120	    Rev-->>Rev: Tách transcript stderr sang build/reviews/<epic>_roundN.raw.log
   121	    Dev->>Run: Chốt Gate 2 -> AUTO MODE (Claude -> Codex -> Kiro -> Argon)
   122	    Run->>Run: Lấy model Programmer (gemini-4-hydrogen-xhigh, --effort xhigh)
   123	    Run->>Pool: Điều phối wave task độc lập chỉ truyền path + dải dòng mục tiêu
   124	    Pool-->>Run: Commit task + Selective task-reviewer (chỉ task rủi ro cao)
   125	    Run->>Run: verify_polyglot_registry.py --compact -> GATE_PASS hoặc 25 dòng lỗi
   126	    Run->>Rev: Cross-Model Review (Round 1 -U5; Round 2..3 chỉ delta prev_sha..sha)
   127	    alt Lỗi code rõ ràng không chạm contract
   128	        Run->>Pool: Programmer sửa trực tiếp + scoped test + đuôi 25 dòng
   129	    else Nghi ngờ contract hoặc kiến trúc
   130	        Run->>Run: Đánh giá fix_plan_roundN.md qua Role 2.2
   131	    end
   132	    Run->>Dev: Hội tụ + Gate 4 PASS -> Mời chọn Gate 5 Finish Decision
   133	    Dev->>Des: Stage 4 Pre-Finish Hook (sync .vi.md + check_epic_readiness.py --strict-bilingual)
   134	```
   135	
   136	## Bản đồ Bảo trì Tính năng
   137	
   138	| Tính năng | Đường dẫn Chuẩn và Entry Points | Bất biến Cốt lõi và Núm Cấu hình | Hướng dẫn Mở rộng và Gỡ lỗi |
   139	|---|---|---|---|
   140	| **Diff-Only External Review** | `skills/dev-implementation/resources/scripts/run_external_review.py`, `skills/subagent-driven-development/scripts/review-package` | Dùng `git diff -U5`; Round `>= 2` bỏ full diff `base...sha` khi có `delta_round_context`; loại `*.vi.md`; diff lớn vẫn xuất `--stat` + `@@` hunks | Xem full transcript CLI tại `build/reviews/<epic>_round<n>.raw.log`; kiểm tra `MAX_DIFF_LINES` (`1500`) và `MAX_DIFF_BYTES` (`60000`) |
   141	| **Silent Gate 4 và Runners** | `skills/quality_check/resources/scripts/verify_polyglot_registry.py`, `skills/dev-implementation/resources/scripts/run_task_checks.py`, `scripts/verify.sh` | `--compact` in 1 dòng `GATE_PASS: <id>` khi pass và summary + 25 dòng cuối khi fail; `TAIL_LINES = 25`; `pytest -q --tb=short --maxfail=3` trong `python-quality.json` | Đọc full log tại `build/quality/<provider>/<cap>.log`; chạy `bash scripts/verify.sh --full` khi cần log đầy đủ |
   142	| **Bộ bảo vệ Option A Song ngữ** | `skills/dev-implementation/resources/scripts/check_epic_readiness.py`, `check_bdd_traceability.py`, `package_epic.py` | Mặc định dung sai sai lệch `.vi.md` in-flight và hoãn `bdd_scenarios.vi.md`; `--strict-bilingual` kiểm chặt tại Stage 4; `handoff.md` bỏ `*.vi.md` | Truyền `--strict-bilingual` trước khi archive Finish; xem Pre-Finish Hook trong `finishing-a-development-branch/SKILL.md` |
   143	| **Kiểm tra Dải dòng Phẫu thuật** | `skills/dev-implementation/resources/scripts/check_task_contract.py`, `skills/dev-designer/SKILL.md` | File tracked >200 dòng trong `Allowed files` (không gắn `(new)`) phải có neo `path :: Symbol (L<start>-L<end>)` dưới `--design` | Xem thông báo lỗi `check_task_contract.py --design` khi thêm file >200 dòng thiếu vùng đọc mục tiêu |
   144	| **Programmer Config và Pool** | `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`, `manage_worker_pool.py`, `scripts/resume_context.py` | Thứ tự `CLI -> Runner config -> .devtool/review_config.json -> env -> fallback ("gemini-4-hydrogen-xhigh", "xhigh")`; `"extra"` ánh xạ thành `--effort xhigh` | Chỉnh `.devtool/review_config.json["providers"]["programmer"]` mà không sửa code; xem `PipelineState` tại `.devtool/state/<epic>.pipeline.json` |
   145	| **Rút gọn Rules và Memory** | `rules/CRITICAL_RULES.md`, `skills/task-observer/SKILL.md`, `skills/dev-designer/SKILL.md`, `skills/dev-lifecycle/references/` | `CRITICAL_RULES.md <= 8192` bytes; `dev-designer/SKILL.md <= 22528` bytes; `task-observer/SKILL.md` có `<SUBAGENT-STOP>`; `resume_context.py --compact --epic <slug> <= 4096` bytes | Chạy `bash scripts/verify.sh` và `scripts/test_lifecycle_document_contract.py` sau khi sửa tài liệu/tách reference |
   146	| **Selective Task Reviewer** | `skills/dev-designer/SKILL.md`, `skills/dev-implementation/SKILL.md`, `skills/subagent-driven-development/SKILL.md` | Chỉ kích hoạt `task-reviewer` khi `review_tier: "full"`, nhãn `security|architecture|concurrency|contract`, hoặc `> 2` module non-test | Gắn `review_tier: "full"` trong frontmatter task khi cần review riêng từng task |
   147	
   148	## Hợp đồng Module và Giao diện CLI
   149	
   150	Các giao diện và hợp đồng hành vi sau được cố định cho giai đoạn triển khai:
   151	
   152	1. **External Review và Cấu hình Mặc định (`run_external_review.py`)**:
   153	   - `DEFAULT_REVIEW_CONFIG["providers"]` bổ sung `"assistant"` (`"claude-opus-5-5-high"`, `"high"`) và `"programmer"` (`"gemini-4-hydrogen-xhigh"`, `"xhigh"`).
   154	   - `load_review_config(root: Path) -> dict[str, Any]` bổ sung provider còn thiếu và nâng cấp các giá trị mặc định cũ của programmer (`"gemini-3.8-flash"`, `"gemini-3.8-flash-high"`) sang `"gemini-4-hydrogen-xhigh"` với `"thinking_level": "xhigh"`, nhưng giữ nguyên mọi model do người dùng tự đặt.
   155	   - `build_diff_section(...)` và `diff_range(...)`: dùng `git diff -U5`; khi vượt ngưỡng dung lượng/số dòng, xuất `git diff --stat` kèm danh sách hunk headers (`@@ ... @@`) cho từng file sửa thay vì để rỗng.
   156	   - `principal_artefact_lines(root, epic_dir)`: loại bỏ toàn bộ `*.vi.md`.
   157	   - `fact(label, code, out, err)`: trả `f"PASS: {label}\n"` khi `code == 0`, hoặc lệnh và 25 dòng cuối output khi khác `0`/timeout.
   158	   - `render_round(...)`: tách transcript đầy đủ ra `build/reviews/<epic>_round<n>.raw.log` và chèn một dòng trỏ file log trong markdown (giữ nguyên cột bảng tương thích `rounds_in` / `finding_rows` / `triage`).
   159	   - `run(args)`: khi `round_num >= 2` và `delta_round_context()` hoạt động (`not args.full`), bỏ `diff_section` (`base...sha`) và chỉ giữ 1 dòng tham chiếu thống kê lũy kế.
   160	
   161	2. **Compact Quality Gates và Runners (`verify_polyglot_registry.py`, `run_task_checks.py`, `verify.sh`)**:
   162	   - `verify_polyglot_registry.py` nhận cờ `--compact`: lưu log chi tiết vào `build/quality/<provider>/<cap>.log`, in 1 dòng `GATE_PASS: <id>` khi pass, hoặc in tên capability lỗi + 25 dòng cuối từ `.log` khi fail.
   163	   - `run_task_checks.py` đặt `TAIL_LINES = 25`.
   164	   - `.agents/quality/python-quality.json` và `scaffold_quality_manifest.py` bổ sung `"-q", "--tb=short", "--maxfail=3"` cho pytest.
   165	   - `scripts/verify.sh` thêm `--quiet` (1 dòng/mục, cắt đuôi 25 dòng khi lỗi) mà vẫn giữ nguyên `--full`.
   166	
   167	3. **Kiểm tra Option A, Dải dòng Phẫu thuật và Memory gọn**:
   168	   - `check_epic_readiness.py` và `check_bdd_traceability.py` thêm `--strict-bilingual` (mặc định `False` trong vòng lặp Stage 2/3, bỏ qua sai lệch `.vi.md` và `bdd_scenarios.vi.md`; `--strict-bilingual` ép đồng bộ đầy đủ ở Stage 4).
   169	   - `package_epic.py` và `handoff-template.md` chỉ liệt kê `.en.md` / tài liệu tiếng Anh trong `Read First`.
   170	   - `check_task_contract.py --design` kiểm tra file tracked >200 dòng (không gắn `(new)`) trong `Allowed files` phải có neo symbol/dải dòng (`:: <Symbol> (L<start>-L<end>)` hoặc `(L<start>-L<end>)`).
   171	   - `scripts/resume_context.py` bổ sung `--compact` (mặc định kích hoạt khi truyền `--epic <slug>`), chỉ xuất state epic đang chạy, git status repo hiện tại, RFC liên quan và task thuộc epic (`<= 4096` bytes); `emit_handoff_prompt` đọc `.devtool/review_config.json["providers"]["programmer"]` với fallback `gemini-4-hydrogen-xhigh` (`xhigh`).
   172	
   173	4. **Lifecycle Runner và Programmer Config (`lifecycle_runner.py`)**:
   174	   - `RunnerConfig` đổi fallback sang `"gemini-4-hydrogen-xhigh"` / `"xhigh"`, thêm `normalize_agy_effort(raw: str) -> str` ánh xạ `{"extra", "extra-high", "extra_high", "xhigh"}` -> `"xhigh"`, và thêm `resolve_programmer_model()` cùng `resolve_programmer_effort()` theo thứ tự:
   175	     `CLI (--programmer-model / --programmer-effort) -> Runner --config JSON -> .devtool/review_config.json["providers"]["programmer"] -> env (AGY_PROGRAMMER_MODEL / AGY_PROGRAMMER_EFFORT) -> fallback ("gemini-4-hydrogen-xhigh", "xhigh")`.
   176	   - `main()` đặt default `None` cho `--programmer-model` và `--programmer-effort` trên `argparse` để không ghi đè file config.
   177	   - `_tail_lines(text: str, limit: int = 25) -> str` cắt gọn output lỗi cho `run_gate4()` và `run_intermediate_check()`.
   178	   - `step_implementation()` dùng `manage_worker_pool.py` chạy song song các wave độc lập; `_execute_single_task()` chỉ truyền path + kỷ luật đọc giới hạn dòng + Zero-Fluff output cap.
   179	   - `step_cross_model_review()` cho phép sửa trực tiếp qua `_apply_code_fixes()` với lỗi code rõ ràng không chạm contract/kiến trúc, chỉ gọi `_draft_fix_plan()` + `evaluate_programmer_fix_plan()` khi có xung đột thiết kế.
   180	   - `render_final_executive_report()` phân tích findings rủi ro cao và SHA thực từ `review_results.md` / `principal_review.md`.
   181	
   182	## Phân tích Tác động
   183	
   184	- Kết quả `check_code_impact.py --files ... --base-ref main`:
   185	  - **Xung đột Git Upstream**: `CLEAN` (`0` commit chưa merge so với `main`).
   186	  - **Cross-Platform Bridges**: Không có.
   187	  - **Lưới an toàn Test**: Đã có bộ unit/integration tests cho `resume_context.py`, `run_external_review.py`, `lifecycle_runner.py`, `verify_polyglot_registry.py` và `check_epic_readiness.py`; `rules/CRITICAL_RULES.md` và skill docs được bảo vệ bởi `scripts/test_lifecycle_document_contract.py` cùng `scripts/verify.sh` §3/§5b/§7/§8.
   188	
   189	## Tác động Shared Contract
   190	
   191	None — self-contained feature. Kho mã `ai-agent-tools` không dùng thư mục `shared-contracts/`; mọi cờ CLI nội bộ mới (`--compact`, `--strict-bilingual`, `--quiet`, `--programmer-effort`) tương thích ngược hoàn toàn qua giá trị mặc định.
   192	
   193	## Kế hoạch Kiểm thử Tích hợp và Ma trận Ranh giới
   194	
   195	```text
   196	Integration test roots: tests
   197	Protected paths: .agents/quality/**, .devtool/epic/token_throttling_optimization/bdd_scenarios.en.md, .devtool/epic/token_throttling_optimization/bdd_scenarios.vi.md
   198	Integration results: python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/token-throttling-optimization.xml tests/test_tto_external_review.py tests/test_polyglot_gate4.py tests/test_tto_bilingual_and_surgical.py tests/test_lifecycle_runner.py tests/test_tto_docs_and_slimming.py tests/test_token_throttling_acceptance.py -> build/test-results/token-throttling-optimization.xml
   199	```
   200	
   201	| Ranh giới | Thành phần Thực | Cách ly hoặc Fixture | Khẳng định Bắt buộc |
   202	|---|---|---|---|
   203	| **Diff-Only External Review** | `run_external_review.py`, `review-package` | Repo git tạm nhiều vòng review và binary CLI giả lập trên `PATH` | Diff `-U5`, Round 2 bỏ full `base...sha`, loại `.vi.md`, fact `PASS:` 1 dòng, ghi `build/reviews/*.raw.log` |
   204	| **Compact Gate 4 và Runners** | `verify_polyglot_registry.py`, `run_task_checks.py`, `scaffold_quality_manifest.py`, `verify.sh` | Manifest tạm + mã thoát giả lập (`0` và `1`) | `--compact` in `GATE_PASS:` khi đạt và summary + `<= 25` dòng khi lỗi; `TAIL_LINES == 25`; cờ pytest chuẩn |
   205	| **Option A và Kiểm tra Dải dòng** | `check_epic_readiness.py`, `check_bdd_traceability.py`, `check_task_contract.py`, `package_epic.py`, `resume_context.py` | Thư mục epic tạm với `.en.md`/`.vi.md` lệch, thiếu `bdd_scenarios.vi.md`, file >200 dòng | Mặc định in-flight pass khi thiếu `bdd_scenarios.vi.md`; `--strict-bilingual` fail khi chưa sync; check neo dòng; `--compact <= 4096` B |
   206	| **Programmer Config và Pool** | `lifecycle_runner.py`, `manage_worker_pool.py` | `agy` giả lập + repo git tạm + pool worktree 2-slot | Phân giải `gemini-4-hydrogen-xhigh`, chuẩn hóa `"extra"` -> `"xhigh"`, prompt chỉ truyền path, wave song song, report động |
   207	| **Rút gọn Docs và Contracts** | `CRITICAL_RULES.md`, `dev-designer/SKILL.md`, `task-observer/SKILL.md`, `finishing-a-development-branch/SKILL.md` | Các file thật trong repo qua `verify.sh` | `CRITICAL_RULES.md <= 8192` B, `dev-designer/SKILL.md <= 22528` B, `<SUBAGENT-STOP>`, pass đủ `verify.sh` §1–§10 |
   208	
   209	## Môi trường Kiểm thử
   210	
   211	- Mọi unit và integration tests chạy trong thư mục tạm cô lập (`tempfile.TemporaryDirectory` / pytest `tmp_path`) cùng repo git ảo và CLI giả trên `PATH`.
   212	- Không dùng API key thật, không gọi mạng ngoài và không sửa hồ sơ Antigravity thật của người dùng.
   213	- File JUnit XML chỉ ghi vào `build/test-results/` và log thô vào `build/reviews/`, `build/quality/` (đã git-ignore).
   214	- `.devtool/review_config.json` cục bộ của workspace không bị ghi đè bởi test; test chỉ thao tác trên bản trong `tmp_path`.
   215	
   216	## Phạm vi Kịch bản BDD toàn diện
   217	
   218	Định nghĩa Gherkin chuẩn nằm tại [BDD scenarios](bdd_scenarios.en.md) cùng bản dịch đồng bộ tại [Kịch bản BDD tiếng Việt](bdd_scenarios.vi.md).
   219	
   220	| Chiều kiểm thử | Mã kịch bản | Mục tiêu bao phủ |
   221	|---|---|---|
   222	| **Happy Paths** | `TTO-HP-01` đến `TTO-HP-08` | Review delta `-U5`, Gate 4 `--compact`, Option A in-flight, Programmer config `gemini-4-hydrogen-xhigh` (`xhigh`), slimming rules/skills, `--compact` memory, fast code-fix, kiểm thử E2E |
   223	| **Edge Cases và Boundaries** | `TTO-EC-01` đến `TTO-EC-06` | Truncated diff kèm `--stat` + `@@` hunks, `TAIL_LINES=25` + pytest flags, check dải dòng file >200 dòng, chuẩn hóa effort alias, điều kiện `task-reviewer`, full `verify.sh` §1–§17 |
   224	| **State Transitions và Invariants** | `TTO-ST-01` đến `TTO-ST-05` | Di trú `load_review_config`, loại `.vi.md` khỏi `handoff.md`, `--strict-bilingual` Gate 5, leo thang Role 2.2 khi đụng contract, Pre-Finish sync hook ở Stage 4 |
   225	| **Async và Concurrency** | `TTO-AR-01` đến `TTO-AR-02` | Chạy song song theo wave trên `manage_worker_pool.py`, cách ly `.raw.log` theo round và sạch context giữa các task |
   226	| **Failure và Resilience** | `TTO-FR-01` đến `TTO-FR-04` | Đuôi 25 dòng lỗi trong `collect_facts`, `--compact` Gate 4 fail 25 dòng, `_tail_lines` fail, ngưỡng byte-size chống phình hồi quy |
   227	
   228	## Chiến lược Triển khai và Giảm thiểu Rủi ro
   229	
   230	1. **Wave 1 (Nền tảng Độc lập — Task 1, 2, 3)**: Triển khai Diff-Only External Review (`run_external_review.py`, `review-package`), Compact Gate 4 & Runners (`verify_polyglot_registry.py`, `run_task_checks.py`, `verify.sh --quiet`), và Option A / Surgical Contract / Scoped Memory (`check_epic_readiness.py`, `check_task_contract.py`, `resume_context.py`).
   231	2. **Wave 2 (Điều phối và Slimming — Task 4, 5)**: Triển khai Config-Driven `lifecycle_runner.py` (`gemini-4-hydrogen-xhigh`, `--effort xhigh`, wave song song, fast code-fix) song song với Rút gọn Rules/Skills, Khử trùng lặp Reference và Stage 4 Pre-Finish Hook.
   232	3. **Wave 3 (Tích hợp và Đo kiểm — Task 6)**: Bổ sung regression suite định lượng (`test_token_throttling_acceptance.py`), đăng ký các suite mới vào `scripts/verify.sh`, chạy toàn bộ kiểm định phát hành.
   233	
   234	Giảm thiểu rủi ro: Mọi cờ rút gọn (`--compact`, `--quiet`) đều giữ đường fallback đầy đủ (`--full`), và `--strict-bilingual` là opt-in ở Stage 4 nên hoàn toàn tương thích ngược với các workflow đang chạy.
   235	
   236	## Phân rã Kanban Tasks
   237	
   238	1. **Task 1: Review Mở rộng chỉ theo Diff và Cách ly Transcript** (`task_01_diff_only_external_review_and_transcript_isolation.md`) — Bao phủ: `TTO-HP-01, TTO-EC-01, TTO-ST-01, TTO-FR-01`
   239	2. **Task 2: Gate 4 Im lặng và Cắt gọn Output Bộ chạy Kiểm thử** (`task_02_silent_gate4_and_truncated_test_runners.md`) — Bao phủ: `TTO-HP-02, TTO-EC-02, TTO-FR-02`
   240	3. **Task 3: Bảo vệ Song ngữ Option A, Kiểm tra Phẫu thuật và Bộ nhớ Gọn** (`task_03_option_a_bilingual_and_surgical_contract_guards.md`) — Bao phủ: `TTO-HP-03, TTO-HP-06, TTO-EC-03, TTO-ST-02, TTO-ST-03`
   241	4. **Task 4: Programmer Persona qua Config, Worker Pool và Tối ưu Runner** (`task_04_lifecycle_runner_programmer_config_and_pool_isolation.md`) — Bao phủ: `TTO-HP-04, TTO-HP-07, TTO-EC-04, TTO-ST-04, TTO-AR-01, TTO-FR-03`
   242	5. **Task 5: Rút gọn Rules và Skills, Khử trùng lặp, Selective Reviewer và Sync Stage 4** (`task_05_slimming_rules_skills_dedup_and_selective_reviewer.md`) — Bao phủ: `TTO-HP-05, TTO-EC-05, TTO-ST-05`
   243	6. **Task 6: Bộ Kiểm thử Chấp nhận và Hồi quy Định lượng Token Throttling** (`task_06_integration_and_regression_verification.md`) — Bao phủ: `TTO-HP-08, TTO-EC-06, TTO-AR-02, TTO-FR-04`
   244	
   245	## Đính chính Đặc tả
   246	
   247	Chưa có.

exec
/bin/zsh -lc "nl -ba skills/dev-lifecycle/resources/scripts/lifecycle_runner.py | sed -n '1,215p;380,520p;870,1090p;1180,1420p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""Autonomous Lifecycle Runner: Headless state machine orchestrator for multi-actor development lifecycles."""
     3	from __future__ import annotations
     4	
     5	import argparse
     6	import copy
     7	import fcntl
     8	import json
     9	import os
    10	import re
    11	import shutil
    12	import signal
    13	import subprocess
    14	import sys
    15	import time
    16	from dataclasses import asdict, dataclass, field
    17	from enum import Enum
    18	from pathlib import Path
    19	from typing import Any, Optional
    20	
    21	
    22	class StageName(str, Enum):
    23	    """Lifecycle runner state machine stage names."""
    24	
    25	    INITIALIZED = "initialized"
    26	    PRINCIPAL_REVIEW = "principal_review"
    27	    AWAITING_PRINCIPAL_CONFIRMATION = "awaiting_principal_confirmation"
    28	    IMPLEMENTATION = "implementation"
    29	    CROSS_MODEL_REVIEW = "cross_model_review"
    30	    AWAITING_FINISH = "awaiting_finish"
    31	    COMPLETED = "completed"
    32	    HALTED = "halted"
    33	
    34	
    35	class FixPlanVerdict(str, Enum):
    36	    """AI Assistant fix plan evaluation verdicts."""
    37	
    38	    APPROVED = "APPROVED"
    39	    ADJUSTED = "ADJUSTED"
    40	    CRITICAL_CONFLICT = "CRITICAL_CONFLICT"
    41	
    42	
    43	@dataclass
    44	class RunnerConfig:
    45	    """Configuration settings for the Autonomous Lifecycle Runner."""
    46	
    47	    programmer_model: str = "gemini-3.8-flash"
    48	    programmer_effort: str = "high"
    49	    assistant_model: str | None = None
    50	    assistant_effort: str = "high"
    51	    timeout_seconds: int = 1800
    52	    max_review_rounds: int = 3
    53	    provider_priority: list[str] | None = None
    54	    base_branch: str = "main"
    55	
    56	    def resolve_assistant_model(self, root: Path | None = None) -> str:
    57	        """Resolve Assistant model following precedence: CLI -> review_config.json -> profile -> fallback."""
    58	        if self.assistant_model:
    59	            return self.assistant_model
    60	
    61	        if root:
    62	            review_config_file = root / ".devtool" / "review_config.json"
    63	            if review_config_file.is_file():
    64	                try:
    65	                    data = json.loads(review_config_file.read_text(encoding="utf-8"))
    66	                    model = (
    67	                        data.get("providers", {})
    68	                        .get("assistant", {})
    69	                        .get("model")
    70	                    )
    71	                    if model and isinstance(model, str):
    72	                        return model
    73	                except (json.JSONDecodeError, OSError):
    74	                    pass
    75	
    76	        profile_model = os.environ.get("AGY_ASSISTANT_MODEL")
    77	        if profile_model:
    78	            return profile_model
    79	
    80	        return "claude-sonnet-5-5-high"
    81	
    82	
    83	@dataclass
    84	class PipelineState:
    85	    """Persistent state tracking epic execution progress."""
    86	
    87	    epic_slug: str
    88	    active_stage: str = StageName.INITIALIZED.value
    89	    principal_round: int = 0
    90	    cross_model_round: int = 0
    91	    last_commit_sha: str | None = None
    92	    last_verdict: str | None = None
    93	    halt_reason: str | None = None
    94	    last_error: str | None = None
    95	    task_order: list[str] = field(default_factory=list)
    96	    completed_tasks: list[str] = field(default_factory=list)
    97	
    98	    def to_dict(self) -> dict[str, Any]:
    99	        """Convert state to dictionary."""
   100	        return asdict(self)
   101	
   102	    @classmethod
   103	    def from_dict(cls, data: dict[str, Any]) -> PipelineState:
   104	        """Construct state from dictionary."""
   105	        return cls(
   106	            epic_slug=data.get("epic_slug", ""),
   107	            active_stage=data.get("active_stage", StageName.INITIALIZED.value),
   108	            principal_round=int(data.get("principal_round", 0)),
   109	            cross_model_round=int(data.get("cross_model_round", 0)),
   110	            last_commit_sha=data.get("last_commit_sha"),
   111	            last_verdict=data.get("last_verdict"),
   112	            halt_reason=data.get("halt_reason"),
   113	            last_error=data.get("last_error"),
   114	            task_order=list(data.get("task_order", [])),
   115	            completed_tasks=list(data.get("completed_tasks", [])),
   116	        )
   117	
   118	
   119	class ModelDispatcher:
   120	    """Supervises and dispatches headless model processes in isolated process groups."""
   121	
   122	    def __init__(self, worktree_dir: Path, timeout_seconds: int = 1800) -> None:
   123	        self.worktree_dir = worktree_dir
   124	        self.timeout_seconds = timeout_seconds
   125	
   126	    def probe_model(self, cli: str, model: str) -> tuple[bool, str]:
   127	        """Verify model capabilities via headless CLI before state initialization."""
   128	        if cli == "agy":
   129	            cmd = [cli, "models"]
   130	        else:
   131	            cmd = [cli, "--version"]
   132	        try:
   133	            res = subprocess.run(
   134	                cmd,
   135	                cwd=self.worktree_dir,
   136	                capture_output=True,
   137	                text=True,
   138	                check=False,
   139	            )
   140	            if res.returncode != 0:
   141	                err = res.stderr.strip() or res.stdout.strip() or f"Exit code {res.returncode}"
   142	                return False, err
   143	
   144	            if cli == "agy":
   145	                clean_target = model.strip().lower()
   146	                clean_output = res.stdout.lower()
   147	                if (
   148	                    clean_target in clean_output
   149	                    or "model probe successful" in clean_output
   150	                    or any(clean_target in line for line in clean_output.splitlines())
   151	                ):
   152	                    return True, "OK"
   153	                return False, f"Model '{model}' is not supported by agy."
   154	
   155	            return True, "OK"
   156	        except FileNotFoundError:
   157	            return False, f"CLI binary '{cli}' not found on PATH"
   158	        except Exception as exc:
   159	            return False, f"Probing exception: {exc}"
   160	
   161	    def dispatch(self, cli: str, args: list[str], prompt: str) -> tuple[int, str, str]:
   162	        """Dispatch headless process with process group isolation and timeout supervision."""
   163	        cmd = [cli] + args
   164	        try:
   165	            proc = subprocess.Popen(
   166	                cmd,
   167	                cwd=self.worktree_dir,
   168	                stdin=subprocess.PIPE,
   169	                stdout=subprocess.PIPE,
   170	                stderr=subprocess.PIPE,
   171	                text=True,
   172	                start_new_session=True,
   173	            )
   174	        except FileNotFoundError:
   175	            return 1, "", f"CLI binary '{cli}' not found on PATH"
   176	        except Exception as exc:
   177	            return 1, "", f"Failed to spawn process: {exc}"
   178	
   179	        try:
   180	            stdout, stderr = proc.communicate(input=prompt, timeout=self.timeout_seconds)
   181	            return proc.returncode, stdout, stderr
   182	        except subprocess.TimeoutExpired:
   183	            pgid = proc.pid
   184	            try:
   185	                os.killpg(pgid, signal.SIGTERM)
   186	            except ProcessLookupError:
   187	                pass
   188	
   189	            alive = True
   190	            start_time = time.time()
   191	            while time.time() - start_time < 1.0:
   192	                if proc.poll() is not None:
   193	                    alive = False
   194	                    break
   195	                time.sleep(0.05)
   196	
   197	            if alive:
   198	                try:
   199	                    os.killpg(pgid, signal.SIGKILL)
   200	                except ProcessLookupError:
   201	                    pass
   202	
   203	            return 124, "", f"Process timeout: execution timed out after {self.timeout_seconds}s"
   204	        except Exception as exc:
   205	            return 1, "", f"Process execution error: {exc}"
   206	
   207	
   208	class LifecycleRunner:
   209	    """Main state machine orchestrator for autonomous epic execution."""
   210	
   211	    def __init__(
   212	        self,
   213	        root: Path,
   214	        epic_slug: str,
   215	        config: RunnerConfig | None = None,
   380	            / "scripts"
   381	            / "compute_execution_order.py"
   382	        )
   383	        cmd = [sys.executable, str(script), self.epic_slug]
   384	        res = subprocess.run(
   385	            cmd,
   386	            cwd=self.root,
   387	            capture_output=True,
   388	            text=True,
   389	            check=False,
   390	        )
   391	        if res.returncode != 0:
   392	            return []
   393	
   394	        lines = res.stdout.splitlines()
   395	        order: list[str] = []
   396	        in_order_section = False
   397	        task_re = re.compile(r"^\s*\d+\.\s+([a-zA-Z0-9_\-]+)\s+-")
   398	
   399	        for line in lines:
   400	            if "Flattened sequential order:" in line:
   401	                in_order_section = True
   402	                continue
   403	            if in_order_section:
   404	                match = task_re.search(line)
   405	                if match:
   406	                    order.append(match.group(1))
   407	                elif line.strip() and not line.startswith(" "):
   408	                    break
   409	
   410	        if order:
   411	            self.state.task_order = order
   412	            self.sync_gate_ledger(
   413	                3,
   414	                f"Topological execution order computed and confirmed: {' -> '.join(order)}",
   415	            )
   416	            self.save_state()
   417	
   418	        return order
   419	
   420	    def _find_task_file(self, task_slug: str) -> Path | None:
   421	        """Locate the task markdown file across known directories."""
   422	        candidates = [
   423	            self.root / ".devtool" / "features" / f"{task_slug}.md",
   424	            self.root / ".devtool" / "features" / "done" / f"{task_slug}.md",
   425	            self.root / ".devtool" / "epic" / self.epic_slug / f"{task_slug}.md",
   426	        ]
   427	        for c in candidates:
   428	            if c.is_file():
   429	                return c
   430	        return None
   431	
   432	    def _execute_single_task(self, task_slug: str) -> bool:
   433	        """Dispatch headless programmer subprocess for a single task."""
   434	        task_file = self._find_task_file(task_slug)
   435	        prompt = f"Implement task {task_slug}"
   436	        if task_file:
   437	            try:
   438	                content = task_file.read_text(encoding="utf-8")
   439	                prompt = (
   440	                    f"Implement task {task_slug} from {task_file.name}:\n\n"
   441	                    f"{content}\n"
   442	                )
   443	            except OSError:
   444	                pass
   445	
   446	        args = [
   447	            "--model",
   448	            self.config.programmer_model,
   449	            "--effort",
   450	            self.config.programmer_effort,
   451	            "--mode",
   452	            "auto",
   453	        ]
   454	        exit_code, stdout, stderr = self.dispatcher.dispatch(
   455	            cli="agy",
   456	            args=args,
   457	            prompt=prompt,
   458	        )
   459	
   460	        log_dir = self.root / ".devtool" / "logs" / "tasks"
   461	        log_dir.mkdir(parents=True, exist_ok=True)
   462	        log_file = log_dir / f"{task_slug}.log"
   463	        try:
   464	            log_file.write_text(
   465	                f"=== STDOUT ===\n{stdout}\n=== STDERR ===\n{stderr}\n",
   466	                encoding="utf-8",
   467	            )
   468	        except OSError:
   469	            pass
   470	
   471	        if exit_code != 0:
   472	            return False
   473	
   474	        # Mark task done via sync_task_status.py if available
   475	        sync_script = (
   476	            self.root
   477	            / "skills"
   478	            / "dev-implementation"
   479	            / "resources"
   480	            / "scripts"
   481	            / "sync_task_status.py"
   482	        )
   483	        if sync_script.is_file():
   484	            subprocess.run(
   485	                [sys.executable, str(sync_script), "task", task_slug, "done"],
   486	                cwd=self.root,
   487	                capture_output=True,
   488	                check=False,
   489	            )
   490	
   491	        # Commit task changes if any
   492	        status_res = subprocess.run(
   493	            ["git", "status", "--porcelain"],
   494	            cwd=self.root,
   495	            capture_output=True,
   496	            text=True,
   497	            check=False,
   498	        )
   499	        if status_res.returncode == 0 and status_res.stdout.strip():
   500	            subprocess.run(["git", "add", "-A"], cwd=self.root, check=False)
   501	            commit_title = f"[{self.epic_slug.upper()}] Execute {task_slug}"
   502	            subprocess.run(
   503	                ["git", "commit", "-m", commit_title],
   504	                cwd=self.root,
   505	                capture_output=True,
   506	                check=False,
   507	            )
   508	
   509	        return True
   510	
   511	    def _has_domain_or_critical_conflict(self, text: str) -> bool:
   512	        """Check if review triage indicates critical risks or business/domain conflicts."""
   513	        markers = [
   514	            "domain conflict",
   515	            "business requirement conflict",
   516	            "critical risk",
   517	            "shared_contract_conflict",
   518	            "conflict with shared-contracts",
   519	        ]
   520	        low = text.lower()
   870	                    self.save_state()
   871	                    confirmed = self.prompt_human_principal_fixes(triage_stdout)
   872	                    if not confirmed:
   873	                        return False
   874	                    self.state.active_stage = StageName.PRINCIPAL_REVIEW.value
   875	                    self.save_state()
   876	
   877	                self._apply_aligned_fixes(round_num)
   878	
   879	        self.state.active_stage = StageName.HALTED.value
   880	        self.state.halt_reason = "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
   881	        self.save_state()
   882	        return False
   883	
   884	    def step_implementation(self) -> bool:
   885	        """Execute Stage 3 autonomous task execution loop."""
   886	        self.state.active_stage = StageName.IMPLEMENTATION.value
   887	        if not self.state.task_order:
   888	            order = self.resolve_gate3_order()
   889	            if not order:
   890	                self.state.last_error = "Failed to resolve Gate 3 execution order"
   891	                self.save_state()
   892	                return False
   893	
   894	        for task_slug in self.state.task_order:
   895	            if task_slug in self.state.completed_tasks:
   896	                continue
   897	
   898	            success = self._execute_single_task(task_slug)
   899	            if not success:
   900	                self.state.last_error = f"Task execution failed: {task_slug}"
   901	                self.save_state()
   902	                return False
   903	
   904	            if task_slug not in self.state.completed_tasks:
   905	                self.state.completed_tasks.append(task_slug)
   906	            self.save_state()
   907	
   908	        return True
   909	
   910	    def run_gate4(self) -> tuple[bool, str]:
   911	        """Execute complete Stage 3 Gate 4 verification sequence on candidate SHA."""
   912	        # 1. Smoke checklist generation
   913	        smoke_script = (
   914	            self.root
   915	            / "skills"
   916	            / "dev-implementation"
   917	            / "resources"
   918	            / "scripts"
   919	            / "generate_smoke_checklist.py"
   920	        )
   921	        if smoke_script.is_file():
   922	            res = subprocess.run(
   923	                [sys.executable, str(smoke_script), "--epic-dir", self.epic_slug],
   924	                cwd=self.root,
   925	                capture_output=True,
   926	                text=True,
   927	                check=False,
   928	            )
   929	            if res.returncode != 0:
   930	                err = res.stderr.strip() or res.stdout.strip() or f"exit code {res.returncode}"
   931	                return False, f"Smoke checklist generation failed: {err}"
   932	
   933	        # 2. Review decisions check
   934	        review_script = (
   935	            self.root
   936	            / "skills"
   937	            / "dev-implementation"
   938	            / "resources"
   939	            / "scripts"
   940	            / "run_external_review.py"
   941	        )
   942	        if review_script.is_file():
   943	            chk_res = subprocess.run(
   944	                [sys.executable, str(review_script), "check", "--epic-dir", self.epic_slug, "--kind", "code"],
   945	                cwd=self.root,
   946	                capture_output=True,
   947	                text=True,
   948	                check=False,
   949	            )
   950	            if chk_res.returncode != 0:
   951	                err = chk_res.stderr.strip() or chk_res.stdout.strip() or f"exit code {chk_res.returncode}"
   952	                return False, f"Review decisions check failed: {err}"
   953	
   954	        # 3. Code and security audit checks via audit_epic.py
   955	        audit_script = (
   956	            self.root
   957	            / "skills"
   958	            / "dev-implementation"
   959	            / "resources"
   960	            / "scripts"
   961	            / "audit_epic.py"
   962	        )
   963	        if audit_script.is_file():
   964	            audit_res = subprocess.run(
   965	                [sys.executable, str(audit_script), "--epic-dir", self.epic_slug, "--base", self.config.base_branch],
   966	                cwd=self.root,
   967	                capture_output=True,
   968	                text=True,
   969	                check=False,
   970	            )
   971	            if audit_res.returncode != 0:
   972	                err = audit_res.stderr.strip() or audit_res.stdout.strip() or f"exit code {audit_res.returncode}"
   973	                return False, f"Epic audit failed: {err}"
   974	
   975	        # 4. HLD Integration results and result-based BDD traceability
   976	        hld_file = self.root / ".devtool" / "epic" / self.epic_slug / f"{self.epic_slug}.en.md"
   977	        if hld_file.is_file():
   978	            content = hld_file.read_text(encoding="utf-8")
   979	            for line in content.splitlines():
   980	                if line.startswith("Integration results:"):
   981	                    cmd_part = line[len("Integration results:"):].strip()
   982	                    cmd_str = cmd_part.split("->")[0].strip() if "->" in cmd_part else cmd_part
   983	                    if cmd_str:
   984	                        integ_res = subprocess.run(
   985	                            cmd_str,
   986	                            shell=True,
   987	                            cwd=self.root,
   988	                            capture_output=True,
   989	                            text=True,
   990	                            check=False,
   991	                        )
   992	                        if integ_res.returncode != 0:
   993	                            err = integ_res.stderr.strip() or integ_res.stdout.strip() or f"exit code {integ_res.returncode}"
   994	                            return False, f"Integration test execution failed: {err}"
   995	
   996	        bdd_script = (
   997	            self.root
   998	            / "skills"
   999	            / "dev-implementation"
  1000	            / "resources"
  1001	            / "scripts"
  1002	            / "check_bdd_traceability.py"
  1003	        )
  1004	        if bdd_script.is_file():
  1005	            scenarios_file = self.root / ".devtool" / "epic" / self.epic_slug / "bdd_scenarios.en.md"
  1006	            bdd_cmd = [sys.executable, str(bdd_script), "tests", "--roots", "tests"]
  1007	            if scenarios_file.is_file():
  1008	                bdd_cmd.extend(["--scenarios", str(scenarios_file)])
  1009	            report_file = self.root / "build" / "test-results" / "autonomous-lifecycle-runner.xml"
  1010	            if report_file.is_file():
  1011	                bdd_cmd.extend(["--results", str(report_file)])
  1012	            bdd_res = subprocess.run(
  1013	                bdd_cmd,
  1014	                cwd=self.root,
  1015	                capture_output=True,
  1016	                text=True,
  1017	                check=False,
  1018	            )
  1019	            if bdd_res.returncode != 0:
  1020	                err = bdd_res.stderr.strip() or bdd_res.stdout.strip() or f"exit code {bdd_res.returncode}"
  1021	                return False, f"BDD traceability check failed: {err}"
  1022	
  1023	        # 5. Quality check verification
  1024	        verify_script = self.root / "scripts" / "verify.sh"
  1025	        if verify_script.is_file():
  1026	            q_res = subprocess.run(
  1027	                ["bash", str(verify_script)],
  1028	                cwd=self.root,
  1029	                capture_output=True,
  1030	                text=True,
  1031	                check=False,
  1032	            )
  1033	            if q_res.returncode != 0:
  1034	                err = q_res.stderr.strip() or q_res.stdout.strip() or f"exit code {q_res.returncode}"
  1035	                return False, f"Quality check verification failed: {err}"
  1036	
  1037	        rev_res = subprocess.run(
  1038	            ["git", "rev-parse", "HEAD"],
  1039	            cwd=self.root,
  1040	            capture_output=True,
  1041	            text=True,
  1042	            check=False,
  1043	        )
  1044	        candidate_sha = rev_res.stdout.strip() if rev_res.returncode == 0 else "HEAD"
  1045	        self.state.last_commit_sha = candidate_sha
  1046	        self.sync_gate_ledger(4, f"Gate 4 verification passed for candidate SHA {candidate_sha}")
  1047	        self.save_state()
  1048	
  1049	        return True, "Gate 4 PASS"
  1050	
  1051	    def run_intermediate_check(self) -> tuple[bool, str]:
  1052	        """Execute fast scoped checks during intermediate review-remediation rounds.
  1053	
  1054	        Enforces Scoped Tests Protocol:
  1055	        - Only fast static checks and review decisions check.
  1056	        - Strictly forbids full Gate 4, repo-wide pytest discoveries, and Playwright E2E suites.
  1057	        - Full regression and machine acceptance run strictly at Final Convergence Gate.
  1058	        """
  1059	        review_script = (
  1060	            self.root
  1061	            / "skills"
  1062	            / "dev-implementation"
  1063	            / "resources"
  1064	            / "scripts"
  1065	            / "run_external_review.py"
  1066	        )
  1067	        if review_script.is_file():
  1068	            chk_res = subprocess.run(
  1069	                [sys.executable, str(review_script), "check", "--epic-dir", self.epic_slug, "--kind", "code"],
  1070	                cwd=self.root,
  1071	                capture_output=True,
  1072	                text=True,
  1073	                check=False,
  1074	            )
  1075	            if chk_res.returncode != 0:
  1076	                err = chk_res.stderr.strip() or chk_res.stdout.strip() or f"exit code {chk_res.returncode}"
  1077	                return False, f"Review decisions check failed: {err}"
  1078	        return True, "Intermediate scoped check PASS"
  1079	
  1080	    def _draft_fix_plan(self, round_num: int, triage_stdout: str) -> str:
  1081	        """Draft fix plan markdown file for the given review round via AI Programmer dispatch."""
  1082	        file = self.root / ".devtool" / "epic" / self.epic_slug / f"fix_plan_round{round_num}.md"
  1083	        file.parent.mkdir(parents=True, exist_ok=True)
  1084	        prompt = (
  1085	            f"You are the AI Programmer (Role 2.3). Draft an actionable fix plan for Cross-Model Review Round {round_num}.\n"
  1086	            f"Triage Findings:\n\n{triage_stdout}\n\n"
  1087	            f"Specify exact file modifications, functions, and unit tests to add/update.\n"
  1088	        )
  1089	        code, stdout, _ = self.dispatcher.dispatch(
  1090	            cli="agy",
  1180	                check=False,
  1181	            )
  1182	        return True
  1183	
  1184	    def evaluate_programmer_fix_plan(self, round_num: int) -> tuple[FixPlanVerdict, str]:
  1185	        """Evaluate AI Programmer fix plan against approved HLD."""
  1186	        file = self.root / ".devtool" / "epic" / self.epic_slug / f"fix_plan_round{round_num}.md"
  1187	        plan_text = file.read_text(encoding="utf-8") if file.is_file() else ""
  1188	        prompt = (
  1189	            f"Evaluate the following fix plan for round {round_num} against the approved HLD and BDD scenarios.\n"
  1190	            f"Emit on the FIRST line one of: APPROVED, ADJUSTED, or CRITICAL_CONFLICT, followed by your rationale.\n\n"
  1191	            f"{plan_text}\n"
  1192	        )
  1193	        assistant_model = self.config.resolve_assistant_model(self.root)
  1194	        code, stdout, stderr = self.dispatcher.dispatch(
  1195	            cli="agy",
  1196	            args=["--model", assistant_model, "--effort", self.config.assistant_effort, "--mode", "auto"],
  1197	            prompt=prompt,
  1198	        )
  1199	        if code != 0 or not stdout.strip():
  1200	            err_msg = stderr.strip() or f"Assistant dispatch failed with exit code {code}"
  1201	            return FixPlanVerdict.CRITICAL_CONFLICT, f"Fix plan evaluation failed: {err_msg}"
  1202	
  1203	        first_line = stdout.strip().splitlines()[0].strip().upper()
  1204	        rationale = (
  1205	            "\n".join(stdout.strip().splitlines()[1:]).strip()
  1206	            if "\n" in stdout.strip()
  1207	            else stdout.strip()
  1208	        )
  1209	        if "CRITICAL_CONFLICT" in first_line:
  1210	            return FixPlanVerdict.CRITICAL_CONFLICT, rationale
  1211	        if "ADJUSTED" in first_line:
  1212	            return FixPlanVerdict.ADJUSTED, rationale
  1213	        if "APPROVED" in first_line:
  1214	            return FixPlanVerdict.APPROVED, rationale
  1215	        return (
  1216	            FixPlanVerdict.CRITICAL_CONFLICT,
  1217	            f"Unparseable fix plan verdict from Assistant (expected APPROVED, ADJUSTED, or CRITICAL_CONFLICT): {first_line}\n{rationale}",
  1218	        )
  1219	
  1220	    def step_cross_model_review(self) -> bool:
  1221	        """Execute Stage 3 Cross-Model Review fix plan evaluation loop."""
  1222	        self.state.active_stage = StageName.CROSS_MODEL_REVIEW.value
  1223	        review_script = (
  1224	            self.root
  1225	            / "skills"
  1226	            / "dev-implementation"
  1227	            / "resources"
  1228	            / "scripts"
  1229	            / "run_external_review.py"
  1230	        )
  1231	
  1232	        while self.state.cross_model_round < self.config.max_review_rounds:
  1233	            self.state.cross_model_round += 1
  1234	            round_num = self.state.cross_model_round
  1235	            self.save_state()
  1236	
  1237	            cmd = [
  1238	                sys.executable,
  1239	                str(review_script),
  1240	                "run",
  1241	                "--kind",
  1242	                "code",
  1243	                "--epic-dir",
  1244	                self.epic_slug,
  1245	                "--auto-quota",
  1246	            ]
  1247	            if self.config.provider_priority:
  1248	                cmd.extend(["--provider-priority", ",".join(self.config.provider_priority)])
  1249	            subprocess.run(cmd, cwd=self.root, capture_output=True, text=True, check=False)
  1250	
  1251	            triage_cmd = [
  1252	                sys.executable,
  1253	                str(review_script),
  1254	                "triage",
  1255	                "--kind",
  1256	                "code",
  1257	                "--epic-dir",
  1258	                self.epic_slug,
  1259	                "--max-rounds",
  1260	                str(self.config.max_review_rounds),
  1261	            ]
  1262	            triage_res = subprocess.run(triage_cmd, cwd=self.root, capture_output=True, text=True, check=False)
  1263	            triage_stdout = triage_res.stdout
  1264	
  1265	            cb = self.evaluate_circuit_breakers("code", round_num, triage_stdout=triage_stdout)
  1266	            if cb:
  1267	                self.state.active_stage = StageName.HALTED.value
  1268	                self.state.halt_reason = cb
  1269	                self.save_state()
  1270	                print(f"\n🛑 {cb}\n")
  1271	                return False
  1272	
  1273	            action_match = re.search(r"-\s+\*\*Action\*\*:\s*([^\n]+)", triage_stdout)
  1274	            action = action_match.group(1).strip() if action_match else ""
  1275	
  1276	            if action == "AUTO_PASS_CLEAN":
  1277	                print("AUTO_PASS_CLEAN: 0 findings. Running Gate 4...")
  1278	                gate4_ok, _ = self.run_gate4()
  1279	                if gate4_ok:
  1280	                    self.state.active_stage = StageName.AWAITING_FINISH.value
  1281	                    self.save_state()
  1282	                    return True
  1283	                return False
  1284	
  1285	            if action == "AUTO_PASS_FINAL_MINOR_SWEEP":
  1286	                print("AUTO_PASS_FINAL_MINOR_SWEEP: Sweeping minor findings in single pass...")
  1287	                self._apply_code_fixes(round_num)
  1288	                self._record_review_decisions(round_num)
  1289	                gate4_ok, _ = self.run_gate4()
  1290	                if gate4_ok:
  1291	                    self.state.active_stage = StageName.AWAITING_FINISH.value
  1292	                    self.save_state()
  1293	                    return True
  1294	                return False
  1295	
  1296	            if action == "AUTO_PASS_FINAL_SWEEP":
  1297	                print("AUTO_PASS_FINAL_SWEEP: Final review round sweep...")
  1298	                self._apply_code_fixes(round_num)
  1299	                self._record_review_decisions(round_num)
  1300	                gate4_ok, _ = self.run_gate4()
  1301	                if gate4_ok:
  1302	                    self.state.active_stage = StageName.AWAITING_FINISH.value
  1303	                    self.save_state()
  1304	                    return True
  1305	                return False
  1306	
  1307	            if action == "AUTO_FIX_ELIGIBLE":
  1308	                self._draft_fix_plan(round_num, triage_stdout)
  1309	                verdict, rationale = self.evaluate_programmer_fix_plan(round_num)
  1310	                self.state.last_verdict = verdict.value
  1311	                self.save_state()
  1312	
  1313	                if verdict == FixPlanVerdict.CRITICAL_CONFLICT:
  1314	                    self.state.active_stage = StageName.HALTED.value
  1315	                    self.state.halt_reason = f"CRITICAL_CONFLICT: {rationale}"
  1316	                    self.save_state()
  1317	                    print(f"\n🛑 CRITICAL_CONFLICT in fix plan: {rationale}\n")
  1318	                    return False
  1319	
  1320	                # Apply code fixes (passing amended plan_text if ADJUSTED)
  1321	                self._apply_code_fixes(
  1322	                    round_num,
  1323	                    plan_text=rationale if verdict == FixPlanVerdict.ADJUSTED else "",
  1324	                )
  1325	                self._record_review_decisions(round_num)
  1326	
  1327	                # Run intermediate scoped verification (reserve full Gate 4 for final convergence)
  1328	                scoped_ok, msg = self.run_intermediate_check()
  1329	                if not scoped_ok:
  1330	                    self.state.last_error = f"Intermediate scoped check failed after round {round_num} fixes: {msg}"
  1331	                    self.save_state()
  1332	
  1333	        self.state.active_stage = StageName.HALTED.value
  1334	        self.state.halt_reason = "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
  1335	        self.save_state()
  1336	        return False
  1337	
  1338	    def render_final_executive_report(self) -> str:
  1339	        """Render final executive markdown report synthesizing findings across all rounds."""
  1340	        lines = [
  1341	            f"# Executive Review Report: Epic '{self.epic_slug}'",
  1342	            "",
  1343	            "## Review Lifecycle Summary",
  1344	            f"- **Principal Review Rounds**: {self.state.principal_round} / {self.config.max_review_rounds}",
  1345	            f"- **Cross-Model Review Rounds**: {self.state.cross_model_round} / {self.config.max_review_rounds}",
  1346	            f"- **Candidate SHA**: `{self.state.last_commit_sha or 'HEAD'}`",
  1347	            "- **Gate 4 Status**: PASS (Candidate certified)",
  1348	            f"- **Completed Tasks ({len(self.state.completed_tasks)})**: {', '.join(self.state.completed_tasks)}",
  1349	            "",
  1350	            "## Top 3 Highest-Risk Findings (Synthesized Across All Rounds)",
  1351	            "",
  1352	            "| # | Round | Area / Path | Risk / Severity | Resolution / Status |",
  1353	            "|---|-------|-------------|-----------------|---------------------|",
  1354	            "| 1 | Round 1 | State Machine & Process Supervision | Critical (Process Leak Risk) | Resolved in POSIX group isolation |",
  1355	            "| 2 | Round 1 | Gate 4 Candidate Certification | Important (Decision Check) | Resolved in run_external_review check |",
  1356	            "| 3 | Round 2 | Assistant Model Config Precedence | Minor (CLI Override Precedence) | Resolved in RunnerConfig precedence |",
  1357	            "",
  1358	            "## Gate 5 Candidate Readiness",
  1359	            "- Pipeline State: `AWAITING_FINISH`",
  1360	            "- Next Action: Proceed to `/finishing-a-development-branch` to review, squash/merge to local base branch, and archive epic.",
  1361	        ]
  1362	        return "\n".join(lines)
  1363	
  1364	
  1365	def main() -> int:
  1366	    """CLI entrypoint for autonomous lifecycle runner."""
  1367	    parser = argparse.ArgumentParser(description="Autonomous Lifecycle Runner CLI")
  1368	    parser.add_argument("--epic", required=True, help="Epic slug identifier")
  1369	    parser.add_argument("--resume", action="store_true", help="Resume from interrupted state")
  1370	    parser.add_argument("--config", type=Path, default=None, help="Path to config JSON")
  1371	    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Workspace root directory")
  1372	    parser.add_argument(
  1373	        "--reset-stage",
  1374	        choices=[s.value for s in StageName],
  1375	        default=None,
  1376	        help="Reset to specific stage",
  1377	    )
  1378	    parser.add_argument("--confirm-fixes", action="store_true", help="Confirm Principal Review fixes")
  1379	    parser.add_argument("--reject-fixes", action="store_true", help="Reject Principal Review fixes")
  1380	    parser.add_argument("--base", default="main", help="Base branch name (default: main)")
  1381	    parser.add_argument("--programmer-model", default="gemini-3.8-flash", help="Model for Programmer")
  1382	    parser.add_argument("--assistant-model", default=None, help="Model override for Assistant")
  1383	    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without running subprocesses")
  1384	    args = parser.parse_args()
  1385	
  1386	    cfg = RunnerConfig(
  1387	        programmer_model=args.programmer_model,
  1388	        assistant_model=args.assistant_model,
  1389	        base_branch=args.base,
  1390	    )
  1391	    if args.config and args.config.is_file():
  1392	        try:
  1393	            cdata = json.loads(args.config.read_text(encoding="utf-8"))
  1394	            if "programmer_model" in cdata:
  1395	                cfg.programmer_model = cdata["programmer_model"]
  1396	            if "assistant_model" in cdata:
  1397	                cfg.assistant_model = cdata["assistant_model"]
  1398	            if "timeout_seconds" in cdata:
  1399	                cfg.timeout_seconds = int(cdata["timeout_seconds"])
  1400	            if "max_review_rounds" in cdata:
  1401	                cfg.max_review_rounds = int(cdata["max_review_rounds"])
  1402	            if "provider_priority" in cdata:
  1403	                cfg.provider_priority = list(cdata["provider_priority"])
  1404	        except (json.JSONDecodeError, OSError):
  1405	            pass
  1406	
  1407	    runner = LifecycleRunner(root=args.root, epic_slug=args.epic, config=cfg)
  1408	    return runner.run(
  1409	        resume=args.resume,
  1410	        confirm_fixes=args.confirm_fixes,
  1411	        reject_fixes=args.reject_fixes,
  1412	        reset_stage=args.reset_stage,
  1413	        dry_run=args.dry_run,
  1414	    )
  1415	
  1416	
  1417	if __name__ == "__main__":
  1418	    sys.exit(main())

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/manage_worker_pool.py; nl -ba skills/dev-implementation/resources/scripts/compute_execution_order.py | sed -n '1,270p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""Manage 2-Slot Ephemeral Worker Pool for Parallel Task Execution.
     3	
     4	Provides isolated ephemeral git worktrees for sub-agents executing independent
     5	Kanban tasks in parallel within the same topological layer, while sharing build
     6	caches and dependencies (node_modules, .venv, .gradle, target, .dart_tool) via
     7	APFS clone / symlinks with zero storage overhead.
     8	"""
     9	from __future__ import annotations
    10	
    11	import argparse
    12	import os
    13	import platform
    14	import subprocess
    15	import sys
    16	from pathlib import Path
    17	from typing import Any
    18	
    19	CACHE_DIR_CANDIDATES = [
    20	    "node_modules",
    21	    ".venv",
    22	    ".gradle",
    23	    "target",
    24	    ".dart_tool",
    25	    "Pods",
    26	    ".build",
    27	]
    28	
    29	
    30	def get_slot_path(root: Path, epic_dir: str, slot: int) -> Path:
    31	    """Return the worktree filesystem path for a pool slot."""
    32	    return root / ".worktrees" / f"{epic_dir}-slot-{slot}"
    33	
    34	
    35	def get_slot_branch(epic_slug: str, slot: int) -> str:
    36	    """Return the git branch name for a pool slot."""
    37	    return f"epic/{epic_slug}-slot-{slot}"
    38	
    39	
    40	def link_shared_caches(main_wt: Path, slot_wt: Path) -> list[str]:
    41	    """Link or APFS-clone heavy cache and dependency directories from main worktree to slot."""
    42	    linked: list[str] = []
    43	    if not main_wt.is_dir() or not slot_wt.is_dir():
    44	        return linked
    45	
    46	    is_darwin = platform.system() == "Darwin"
    47	
    48	    for cdir in CACHE_DIR_CANDIDATES:
    49	        src = main_wt / cdir
    50	        dst = slot_wt / cdir
    51	        if not src.exists() or dst.exists():
    52	            continue
    53	
    54	        try:
    55	            # On macOS, attempt APFS clone if supported and directory is writable; otherwise symlink
    56	            # Symlinks provide zero-byte overhead and real-time dependency resolution across all tools
    57	            dst.symlink_to(src)
    58	            linked.append(cdir)
    59	        except OSError:
    60	            # Fallback to copy-on-write via cp -c -R if symlink is disallowed
    61	            if is_darwin and src.is_dir():
    62	                res = subprocess.run(["cp", "-c", "-R", str(src), str(dst)], check=False, capture_output=True)
    63	                if res.returncode == 0:
    64	                    linked.append(cdir)
    65	    return linked
    66	
    67	
    68	def init_slots(
    69	    root: Path,
    70	    epic_dir: str,
    71	    epic_slug: str,
    72	    pool_size: int = 2,
    73	    base_ref: str | None = None,
    74	) -> list[Path]:
    75	    """Create isolated worktrees for worker pool slots and link caches."""
    76	    main_wt = root / ".worktrees" / epic_dir
    77	    target_base = base_ref or f"epic/{epic_slug}"
    78	    created_paths: list[Path] = []
    79	
    80	    for slot in range(1, pool_size + 1):
    81	        slot_path = get_slot_path(root, epic_dir, slot)
    82	        slot_branch = get_slot_branch(epic_slug, slot)
    83	
    84	        if not slot_path.is_dir():
    85	            slot_path.parent.mkdir(parents=True, exist_ok=True)
    86	            # Check if branch already exists
    87	            res_branch = subprocess.run(
    88	                ["git", "rev-parse", "--verify", "--quiet", slot_branch],
    89	                cwd=root,
    90	                capture_output=True,
    91	                check=False,
    92	            )
    93	            if res_branch.returncode == 0:
    94	                cmd = ["git", "worktree", "add", str(slot_path), slot_branch]
    95	            else:
    96	                cmd = ["git", "worktree", "add", str(slot_path), "-b", slot_branch, target_base]
    97	
    98	            subprocess.run(cmd, cwd=root, check=True, capture_output=True)
    99	
   100	        # Link caches from main worktree
   101	        if main_wt.is_dir():
   102	            link_shared_caches(main_wt, slot_path)
   103	
   104	        created_paths.append(slot_path)
   105	
   106	    return created_paths
   107	
   108	
   109	def sync_slot(root: Path, epic_dir: str, epic_slug: str, slot: int) -> bool:
   110	    """Reset slot worktree to the latest HEAD of the epic branch."""
   111	    slot_path = get_slot_path(root, epic_dir, slot)
   112	    if not slot_path.is_dir():
   113	        return False
   114	
   115	    epic_branch = f"epic/{epic_slug}"
   116	    # Fetch local branch state and reset slot working copy
   117	    subprocess.run(["git", "fetch", ".", f"{epic_branch}:{epic_branch}"], cwd=slot_path, capture_output=True, check=False)
   118	    res = subprocess.run(["git", "reset", "--hard", epic_branch], cwd=slot_path, capture_output=True, check=False)
   119	    return res.returncode == 0
   120	
   121	
   122	def merge_slot(root: Path, epic_dir: str, epic_slug: str, slot: int, task_id: str | None = None) -> bool:
   123	    """Merge slot's commit back into the main epic worktree branch."""
   124	    main_wt = root / ".worktrees" / epic_dir
   125	    if not main_wt.is_dir():
   126	        return False
   127	
   128	    slot_branch = get_slot_branch(epic_slug, slot)
   129	    # Merge slot branch into main worktree
   130	    res = subprocess.run(["git", "merge", "--ff-only", slot_branch], cwd=main_wt, capture_output=True, check=False)
   131	    if res.returncode != 0:
   132	        # Fallback to standard merge with clear message if non-ff
   133	        msg = f"Merge slot {slot}" + (f" for {task_id}" if task_id else "")
   134	        res = subprocess.run(["git", "merge", "--no-ff", "-m", msg, slot_branch], cwd=main_wt, capture_output=True, check=False)
   135	
   136	    return res.returncode == 0
   137	
   138	
   139	def cleanup_slots(root: Path, epic_dir: str, epic_slug: str, pool_size: int = 2) -> bool:
   140	    """Prune and remove all slot worktrees and temporary branches."""
   141	    for slot in range(1, pool_size + 1):
   142	        slot_path = get_slot_path(root, epic_dir, slot)
   143	        slot_branch = get_slot_branch(epic_slug, slot)
   144	
   145	        if slot_path.is_dir():
   146	            subprocess.run(["git", "worktree", "remove", "--force", str(slot_path)], cwd=root, capture_output=True, check=False)
   147	
   148	        subprocess.run(["git", "branch", "-D", slot_branch], cwd=root, capture_output=True, check=False)
   149	
   150	    subprocess.run(["git", "worktree", "prune"], cwd=root, capture_output=True, check=False)
   151	    return True
   152	
   153	
   154	def get_pool_status(root: Path, epic_dir: str, pool_size: int = 2) -> dict[int, dict[str, Any]]:
   155	    """Inspect presence, branch, and status of worker pool slots."""
   156	    status: dict[int, dict[str, Any]] = {}
   157	    for slot in range(1, pool_size + 1):
   158	        slot_path = get_slot_path(root, epic_dir, slot)
   159	        slot_branch = get_slot_branch(epic_slug=epic_dir, slot=slot)
   160	        exists = slot_path.is_dir()
   161	        head = None
   162	        dirty = False
   163	        if exists:
   164	            h_res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=slot_path, capture_output=True, text=True, check=False)
   165	            if h_res.returncode == 0:
   166	                head = h_res.stdout.strip()
   167	            s_res = subprocess.run(["git", "status", "--porcelain"], cwd=slot_path, capture_output=True, text=True, check=False)
   168	            if s_res.returncode == 0 and s_res.stdout.strip():
   169	                dirty = True
   170	
   171	        status[slot] = {
   172	            "path": str(slot_path),
   173	            "branch": slot_branch,
   174	            "exists": exists,
   175	            "head": head,
   176	            "dirty": dirty,
   177	        }
   178	    return status
   179	
   180	
   181	def main(argv: list[str] | None = None) -> int:
   182	    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
   183	    subparsers = parser.add_subparsers(dest="command", required=True)
   184	
   185	    # init
   186	    p_init = subparsers.add_parser("init", help="Initialize worker pool slots")
   187	    p_init.add_argument("--epic-dir", required=True, help="Epic directory name")
   188	    p_init.add_argument("--epic-slug", required=True, help="Epic slug")
   189	    p_init.add_argument("--pool-size", type=int, default=2, help="Number of slots (default: 2)")
   190	    p_init.add_argument("--base", default=None, help="Base ref for slots (default: epic/<epic_slug>)")
   191	
   192	    # sync
   193	    p_sync = subparsers.add_parser("sync", help="Reset slot to latest epic HEAD")
   194	    p_sync.add_argument("--epic-dir", required=True, help="Epic directory name")
   195	    p_sync.add_argument("--epic-slug", required=True, help="Epic slug")
   196	    p_sync.add_argument("--slot", type=int, required=True, help="Slot number (1 or 2)")
   197	
   198	    # merge
   199	    p_merge = subparsers.add_parser("merge", help="Merge slot back to main worktree")
   200	    p_merge.add_argument("--epic-dir", required=True, help="Epic directory name")
   201	    p_merge.add_argument("--epic-slug", required=True, help="Epic slug")
   202	    p_merge.add_argument("--slot", type=int, required=True, help="Slot number (1 or 2)")
   203	    p_merge.add_argument("--task", default=None, help="Task ID being merged")
   204	
   205	    # cleanup
   206	    p_clean = subparsers.add_parser("cleanup", help="Remove all slots and delete branches")
   207	    p_clean.add_argument("--epic-dir", required=True, help="Epic directory name")
   208	    p_clean.add_argument("--epic-slug", required=True, help="Epic slug")
   209	    p_clean.add_argument("--pool-size", type=int, default=2, help="Number of slots (default: 2)")
   210	
   211	    # status
   212	    p_status = subparsers.add_parser("status", help="Show pool status")
   213	    p_status.add_argument("--epic-dir", required=True, help="Epic directory name")
   214	    p_status.add_argument("--pool-size", type=int, default=2, help="Number of slots (default: 2)")
   215	
   216	    args = parser.parse_args(argv)
   217	    root = Path.cwd()
   218	
   219	    if args.command == "init":
   220	        paths = init_slots(root, args.epic_dir, args.epic_slug, pool_size=args.pool_size, base_ref=args.base)
   221	        print(f"Initialized {len(paths)} worker pool slots:")
   222	        for p in paths:
   223	            print(f"  {p}")
   224	        return 0
   225	
   226	    if args.command == "sync":
   227	        ok = sync_slot(root, args.epic_dir, args.epic_slug, args.slot)
   228	        if ok:
   229	            print(f"Slot {args.slot} synchronized to latest epic/{args.epic_slug}")
   230	            return 0
   231	        print(f"Failed to sync slot {args.slot}", file=sys.stderr)
   232	        return 1
   233	
   234	    if args.command == "merge":
   235	        ok = merge_slot(root, args.epic_dir, args.epic_slug, args.slot, task_id=args.task)
   236	        if ok:
   237	            print(f"Slot {args.slot} merged successfully into .worktrees/{args.epic_dir}")
   238	            return 0
   239	        print(f"Failed to merge slot {args.slot}", file=sys.stderr)
   240	        return 1
   241	
   242	    if args.command == "cleanup":
   243	        cleanup_slots(root, args.epic_dir, args.epic_slug, pool_size=args.pool_size)
   244	        print(f"Cleaned up worker pool slots for {args.epic_dir}")
   245	        return 0
   246	
   247	    if args.command == "status":
   248	        status = get_pool_status(root, args.epic_dir, pool_size=args.pool_size)
   249	        print(f"Worker Pool Status for {args.epic_dir}:")
   250	        for slot, info in status.items():
   251	            st = "Active" if info["exists"] else "Not created"
   252	            extra = f" (HEAD: {info['head']}, Dirty: {info['dirty']})" if info["exists"] else ""
   253	            print(f"  Slot {slot}: {st}{extra} at {info['path']}")
   254	        return 0
   255	
   256	    return 0
   257	
   258	
   259	if __name__ == "__main__":
   260	    sys.exit(main())
   261	
     1	#!/usr/bin/env python3
     2	"""Compute a sequential execution order for one epic's Kanban tasks.
     3	
     4	Reads every `.devtool/features/task_*.md` file whose frontmatter `epic:`
     5	matches the given epic slug, builds a dependency graph from each task's
     6	"## Dependencies & Blockers" section (only lines containing the literal
     7	phrase "Blocked by" count as hard blockers -- this matches the phrasing
     8	dev-designer's own task template prescribes), and prints:
     9	
    10	  1. Tasks grouped into layers. Tasks in the same layer have no dependency
    11	     on each other -- they could technically run in parallel, though
    12	     dev-implementation runs them sequentially (see the design spec).
    13	  2. Any soft notes found in that section -- currently lines containing
    14	     "Recommended" or "New dependency" (see SOFT_NOTE_MARKERS). These are
    15	     NOT treated as hard blockers, so review them manually; the computed
    16	     layer for that task may be earlier than the note suggests.
    17	  3. One flattened sequential order: earlier layers first, and within a
    18	     layer, higher priority first, then lower task number first.
    19	
    20	It also prints a scan summary (how many `task_*.md` files were seen, how
    21	many matched the epic, how many were skipped) so a task file with broken
    22	or missing frontmatter is never silently dropped.
    23	"""
    24	from __future__ import annotations
    25	import argparse
    26	import json
    27	import re
    28	import sys
    29	from pathlib import Path
    30	
    31	sys.path.insert(0, str(Path(__file__).parent))
    32	from slug_utils import parse_frontmatter, sanitize_slug
    33	
    34	PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
    35	# Soft-note markers: keyword list used to surface advisory content that isn't a hard blocker.
    36	# These are small, documented keywords — not a general sentence parser. Phase 0 (full task text)
    37	# in the operating skill is the actual safety net for anything these markers miss.
    38	SOFT_NOTE_MARKERS = ("Recommended", "New dependency")
    39	FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
    40	SECTION_RE = re.compile(r"##\s*Dependencies\s*(?:&|and)\s*Blockers\s*\n(.*?)(\n##|\Z)", re.DOTALL)
    41	FILES_SECTION_RE = re.compile(r"##\s*Files\s*\n(.*?)(\n##|\Z)", re.DOTALL)
    42	ALLOWED_BULLET_RE = re.compile(r"^\s*-\s*`([^`]+)`(?:\s*\(new\))?\s*$")
    43	LINK_RE = re.compile(r"\]\(([^)]+\.md)\)")
    44	TITLE_RE = re.compile(r"^#\s*Task\s*\d+:\s*(.+)$", re.MULTILINE)
    45	NUMBER_RE = re.compile(r"\d+")
    46	
    47	
    48	def parse_dependencies_section(text: str) -> str:
    49	    match = SECTION_RE.search(text)
    50	    return match.group(1) if match else ""
    51	
    52	
    53	def parse_allowed_files(text: str) -> list[str]:
    54	    """Extract paths listed under the 'Allowed files:' block in the task markdown."""
    55	    match = FILES_SECTION_RE.search(text)
    56	    body = match.group(1) if match else text
    57	    allowed: list[str] = []
    58	    in_allowed = False
    59	    for line in body.splitlines():
    60	        trimmed = line.strip()
    61	        if trimmed == "Allowed files:":
    62	            in_allowed = True
    63	            continue
    64	        if in_allowed:
    65	            bullet = ALLOWED_BULLET_RE.match(line)
    66	            if bullet:
    67	                allowed.append(bullet.group(1))
    68	            elif trimmed.startswith("- `"):
    69	                # Fallback pattern
    70	                start = trimmed.find("`") + 1
    71	                end = trimmed.find("`", start)
    72	                if end != -1:
    73	                    allowed.append(trimmed[start:end])
    74	            elif trimmed and not trimmed.startswith("-"):
    75	                break
    76	    return allowed
    77	
    78	
    79	def parse_blockers(section: str) -> list[str]:
    80	    blockers = []
    81	    for line in section.splitlines():
    82	        if "Blocked by" not in line:
    83	            continue
    84	        blockers.extend(Path(link).stem for link in LINK_RE.findall(line))
    85	    return blockers
    86	
    87	
    88	def parse_soft_notes(section: str) -> list[str]:
    89	    return [line.strip().lstrip("-").strip() for line in section.splitlines()
    90	            if any(marker in line for marker in SOFT_NOTE_MARKERS)]
    91	
    92	
    93	def extract_title(text: str) -> str:
    94	    match = TITLE_RE.search(text)
    95	    return match.group(1).strip() if match else "Untitled"
    96	
    97	
    98	def scan_tasks(features_dir: Path, epic: str) -> tuple[dict[str, dict], list[Path], list[Path]]:
    99	    """Load the epic's tasks AND report what was skipped.
   100	
   101	    Returns (tasks, scanned_paths, skipped_paths). A file lands in
   102	    `skipped_paths` when its frontmatter is missing/unparseable (so
   103	    `epic:` reads as None) or names a different epic -- both look
   104	    identical from the graph's point of view, which is exactly why the
   105	    CLI reports the count instead of dropping them silently.
   106	    """
   107	    tasks: dict[str, dict] = {}
   108	    scanned: list[Path] = []
   109	    skipped: list[Path] = []
   110	    target_epic = sanitize_slug(epic)
   111	    candidate_paths = list(Path(features_dir).glob("task_*.md"))
   112	    done_dir = Path(features_dir) / "done"
   113	    if done_dir.is_dir():
   114	        candidate_paths.extend(done_dir.glob("task_*.md"))
   115	    for path in sorted(candidate_paths):
   116	        scanned.append(path)
   117	        text = path.read_text()
   118	        fm = parse_frontmatter(text)
   119	        task_epic = sanitize_slug(fm.get("epic"))
   120	        if task_epic != target_epic:
   121	            skipped.append(path)
   122	            continue
   123	        section = parse_dependencies_section(text)
   124	        task_id = fm.get("id", path.stem)
   125	        tasks[task_id] = {
   126	            "id": task_id,
   127	            "path": path,
   128	            "priority": fm.get("priority", "medium"),
   129	            "status": fm.get("status", "todo"),
   130	            "blockers": parse_blockers(section),
   131	            "soft_notes": parse_soft_notes(section),
   132	            "allowed_files": parse_allowed_files(text),
   133	            "title": extract_title(text),
   134	        }
   135	    return tasks, scanned, skipped
   136	
   137	
   138	def load_tasks(features_dir: Path, epic: str) -> dict[str, dict]:
   139	    tasks, _scanned, _skipped = scan_tasks(features_dir, epic)
   140	    return tasks
   141	
   142	
   143	def compute_layers(tasks: dict[str, dict]) -> list[list[str]]:
   144	    # Validate that all blockers reference existing tasks
   145	    for task_id, task in tasks.items():
   146	        for blocker in task["blockers"]:
   147	            if blocker not in tasks:
   148	                raise ValueError(f"Task '{task_id}' is blocked by unknown task '{blocker}'")
   149	
   150	    remaining = dict(tasks)
   151	    resolved: set[str] = set()
   152	    layers: list[list[str]] = []
   153	
   154	    def sort_key(task_id: str) -> tuple:
   155	        task = tasks[task_id]
   156	        number_match = NUMBER_RE.search(task_id)
   157	        number = int(number_match.group()) if number_match else 0
   158	        return (PRIORITY_RANK.get(task["priority"], 1), number)
   159	
   160	    while remaining:
   161	        current_layer = [
   162	            task_id
   163	            for task_id, task in remaining.items()
   164	            if all(b in resolved for b in task["blockers"])
   165	        ]
   166	        if not current_layer:
   167	            raise ValueError(f"Cycle detected among: {sorted(remaining)}")
   168	        current_layer.sort(key=sort_key)
   169	        layers.append(current_layer)
   170	        resolved.update(current_layer)
   171	        for task_id in current_layer:
   172	            del remaining[task_id]
   173	    return layers
   174	
   175	
   176	def compute_parallel_batches(
   177	    layers: list[list[str]], tasks: dict[str, dict], pool_size: int = 2
   178	) -> list[list[list[str]]]:
   179	    """Group tasks within each topological layer into parallel execution batches.
   180	
   181	    Tasks within the same layer have no dependencies, but if two tasks modify
   182	    the same file (shared entry in 'allowed_files'), they are separated into
   183	    subsequent batches to prevent Git / build workspace collision.
   184	    Each batch contains at most pool_size tasks.
   185	    """
   186	    def sort_key(task_id: str) -> tuple:
   187	        task = tasks.get(task_id, {})
   188	        number_match = NUMBER_RE.search(task_id)
   189	        number = int(number_match.group()) if number_match else 0
   190	        return (PRIORITY_RANK.get(task.get("priority", "medium"), 1), number)
   191	
   192	    all_layer_batches: list[list[list[str]]] = []
   193	    for layer in layers:
   194	        sorted_layer = sorted(layer, key=sort_key)
   195	        layer_batches: list[list[str]] = []
   196	        for task_id in sorted_layer:
   197	            task = tasks.get(task_id, {})
   198	            task_files = set(task.get("allowed_files", []))
   199	            placed = False
   200	            for batch in layer_batches:
   201	                if len(batch) >= pool_size:
   202	                    continue
   203	                # Check collision with other tasks in this candidate batch
   204	                has_conflict = False
   205	                for other_id in batch:
   206	                    other_task = tasks.get(other_id, {})
   207	                    other_files = set(other_task.get("allowed_files", []))
   208	                    if task_files and other_files and bool(task_files & other_files):
   209	                        has_conflict = True
   210	                        break
   211	                if not has_conflict:
   212	                    batch.append(task_id)
   213	                    placed = True
   214	                    break
   215	            if not placed:
   216	                layer_batches.append([task_id])
   217	        all_layer_batches.append(layer_batches)
   218	    return all_layer_batches
   219	
   220	
   221	def main(argv: list[str] | None = None) -> int:
   222	    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
   223	    parser.add_argument("epic", help="Epic slug, e.g. logging-refactor")
   224	    parser.add_argument("--features-dir", default=".devtool/features",
   225	                         help="Directory containing task_*.md files (default: .devtool/features)")
   226	    parser.add_argument("--parallel", action="store_true",
   227	                         help="Display execution plan grouped by parallel batches for worker pool")
   228	    parser.add_argument("--pool-size", type=int, default=2,
   229	                         help="Worker pool size for parallel batches (default: 2)")
   230	    parser.add_argument("--json", action="store_true",
   231	                         help="Emit machine-readable JSON output")
   232	    args = parser.parse_args(argv)
   233	
   234	    tasks, scanned, skipped = scan_tasks(Path(args.features_dir), args.epic)
   235	    scan_summary = (
   236	        f"Scanned {len(scanned)} task_*.md files; {len(tasks)} matched epic '{args.epic}'; "
   237	        f"{len(skipped)} had no parseable frontmatter or a different epic."
   238	    )
   239	    if not tasks:
   240	        if args.json:
   241	            print(json.dumps({"error": f"No tasks found for epic '{args.epic}' in {args.features_dir}", "tasks": {}}))
   242	        else:
   243	            print(scan_summary, file=sys.stderr)
   244	            print(f"No tasks found for epic '{args.epic}' in {args.features_dir}", file=sys.stderr)
   245	        return 1
   246	
   247	    try:
   248	        layers = compute_layers(tasks)
   249	        parallel_batches = compute_parallel_batches(layers, tasks, pool_size=args.pool_size)
   250	    except ValueError as error:
   251	        if args.json:
   252	            print(json.dumps({"error": str(error)}))
   253	        else:
   254	            print(scan_summary, file=sys.stderr)
   255	            print(f"Cannot compute an execution order: {error}", file=sys.stderr)
   256	        return 1
   257	
   258	    if args.json:
   259	        payload = {
   260	            "epic": args.epic,
   261	            "tasks_count": len(tasks),
   262	            "pool_size": args.pool_size,
   263	            "layers": layers,
   264	            "parallel_batches": parallel_batches,
   265	            "tasks": {
   266	                tid: {
   267	                    "title": t["title"],
   268	                    "priority": t["priority"],
   269	                    "status": t["status"],
   270	                    "blockers": t["blockers"],

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/run_external_review.py | sed -n '35,135p;290,360p;500,735p;815,920p;972,1120p;1230,1350p;1520,1570p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
    35	    UTC = timezone.utc  # type: ignore[attr-defined]
    36	from pathlib import Path
    37	from string import Template
    38	from typing import Any
    39	
    40	import local_review
    41	from check_bdd_traceability import load_scenarios
    42	from task_contract import ContractError, git_run, parse_integration_results, parse_integration_result_specs
    43	
    44	SCRIPTS = Path(__file__).resolve().parent
    45	PROMPT = SCRIPTS.parent.parent / "references" / "external-review-prompt.md"
    46	RULES = SCRIPTS.parent.parent / "references" / "review-rules.md"
    47	KINDS = ("code", "principal", "epic")
    48	REVIEW_CONFIG_FILE = ".devtool/review_config.json"
    49	THINKING_LEVELS = ("none", "light", "low", "medium", "high", "extra-high")
    50	PROVIDER_PRIORITY: tuple[str, ...] = ("claude", "codex", "kiro", "agy")
    51	MAX_REVIEW_ROUNDS = 3
    52	QUOTA_THRESHOLDS: dict[str, float] = {
    53	    "5h_min_fraction": 0.15,
    54	    "7d_min_fraction": 0.02,
    55	    "kiro_min_fraction": 0.03,
    56	    "kiro_min_credits": 15.0,
    57	    "agy_argon_min_fraction": 0.10,
    58	}
    59	DEFAULT_REVIEW_CONFIG: dict[str, Any] = {
    60	    "last_used_provider": "claude",
    61	    "provider_priority": list(PROVIDER_PRIORITY),
    62	    "max_rounds": MAX_REVIEW_ROUNDS,
    63	    "quota_thresholds": dict(QUOTA_THRESHOLDS),
    64	    "providers": {
    65	        "claude": {
    66	            "model": "Opus 5.5",
    67	            "thinking_level": "high",
    68	        },
    69	        "codex": {
    70	            "model": "gpt-6.1-sol",
    71	            "thinking_level": "high",
    72	        },
    73	        "kiro": {
    74	            "model": "claude-opus-5.5",
    75	            "thinking_level": "high",
    76	        },
    77	        "agy": {
    78	            "model": "Gemini 4 Argon (Medium)",
    79	            "thinking_level": "medium",
    80	        },
    81	        "ollama": {
    82	            "model": "qwen38-fast:latest",
    83	            "thinking_level": "high",
    84	            "host": "http://localhost:11434",
    85	        },
    86	    },
    87	}
    88	
    89	
    90	def _is_git_tracked(root: Path, rel_path: str) -> bool:
    91	    try:
    92	        res = subprocess.run(
    93	            ["git", "ls-files", "--error-unmatch", rel_path],
    94	            cwd=root,
    95	            capture_output=True,
    96	            check=False,
    97	        )
    98	        return res.returncode == 0
    99	    except OSError:
   100	        return False
   101	
   102	
   103	def load_review_config(root: Path) -> dict[str, Any]:
   104	    path = root / REVIEW_CONFIG_FILE
   105	    if not path.is_file():
   106	        return copy.deepcopy(DEFAULT_REVIEW_CONFIG)
   107	    try:
   108	        data = json.loads(path.read_text(encoding="utf-8"))
   109	        if not isinstance(data, dict):
   110	            return copy.deepcopy(DEFAULT_REVIEW_CONFIG)
   111	        cfg: dict[str, Any] = copy.deepcopy(DEFAULT_REVIEW_CONFIG)
   112	        if "last_used_provider" in data and isinstance(data["last_used_provider"], str):
   113	            cfg["last_used_provider"] = data["last_used_provider"]
   114	        if "provider_priority" in data and isinstance(data["provider_priority"], list):
   115	            cfg["provider_priority"] = [str(x) for x in data["provider_priority"] if isinstance(x, str)]
   116	        existing_providers = data.get("providers")
   117	        missing_default_provider = not isinstance(existing_providers, dict) or any(
   118	            p not in existing_providers for p in DEFAULT_REVIEW_CONFIG["providers"]
   119	        )
   120	        if isinstance(existing_providers, dict):
   121	            for p, pdata in existing_providers.items():
   122	                if isinstance(pdata, dict):
   123	                    cfg["providers"].setdefault(p, {})
   124	                    cfg["providers"][p].update(pdata)
   125	        if missing_default_provider and not _is_git_tracked(root, REVIEW_CONFIG_FILE):
   126	            save_review_config(root, cfg)
   127	        return cfg
   128	    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
   129	        return copy.deepcopy(DEFAULT_REVIEW_CONFIG)
   130	
   131	
   132	def save_review_config(root: Path, config: dict[str, Any]) -> None:
   133	    path = root / REVIEW_CONFIG_FILE
   134	    path.parent.mkdir(parents=True, exist_ok=True)
   135	    tmp_path = path.with_name(f"{path.name}.tmp")
   290	    if thinking_level not in THINKING_LEVELS:
   291	        thinking_level = default_thinking if default_thinking in THINKING_LEVELS else "high"
   292	
   293	    return cli, model, thinking_level
   294	
   295	
   296	def principal_prompt_path() -> Path:
   297	    standalone = SCRIPTS.parent.parent.parent / "principal-review" / "references" / "principal-review-prompt.md"
   298	    if standalone.is_file():
   299	        return standalone
   300	    return SCRIPTS.parent.parent / "references" / "principal-review-prompt.md"
   301	
   302	
   303	def principal_rules_path() -> Path:
   304	    standalone = SCRIPTS.parent.parent.parent / "principal-review" / "references" / "principal-review-rules.md"
   305	    if standalone.is_file():
   306	        return standalone
   307	    return SCRIPTS.parent.parent / "references" / "principal-review-rules.md"
   308	
   309	
   310	
   311	def review_file(kind: str) -> tuple[str, str]:
   312	    if kind == "principal":
   313	        return ("principal_review.md", "Principal Review")
   314	    return ("review_results.md", "Cross-Model Review")
   315	
   316	
   317	def principal_artefact_lines(root: Path, epic_dir: str) -> str:
   318	    epic_path = root / ".devtool" / "epic" / epic_dir
   319	    lines: list[str] = []
   320	
   321	    # 1. *-design.en.md and *-design.vi.md
   322	    for f in sorted(epic_path.glob("*-design.en.md")):
   323	        lines.append(f"- `.devtool/epic/{epic_dir}/{f.name}`")
   324	    for f in sorted(epic_path.glob("*-design.vi.md")):
   325	        lines.append(f"- `.devtool/epic/{epic_dir}/{f.name}`")
   326	
   327	    # 2. <epic_dir>.en.md and <epic_dir>.vi.md
   328	    for ext in (".en.md", ".vi.md"):
   329	        doc = epic_path / f"{epic_dir}{ext}"
   330	        if doc.is_file():
   331	            line = f"- `.devtool/epic/{epic_dir}/{doc.name}`"
   332	            if line not in lines:
   333	                lines.append(line)
   334	
   335	    # 3. bdd_scenarios.en.md and bdd_scenarios.vi.md
   336	    for ext in (".en.md", ".vi.md"):
   337	        doc = epic_path / f"bdd_scenarios{ext}"
   338	        if doc.is_file():
   339	            line = f"- `.devtool/epic/{epic_dir}/{doc.name}`"
   340	            if line not in lines:
   341	                lines.append(line)
   342	
   343	    # 4. every task_*.md, sorted
   344	    for t in sorted(epic_path.glob("task_*.md")):
   345	        lines.append(f"- `.devtool/epic/{epic_dir}/{t.name}`")
   346	
   347	    # 5. handoff.md when present
   348	    handoff = epic_path / "handoff.md"
   349	    if handoff.is_file():
   350	        lines.append(f"- `.devtool/epic/{epic_dir}/handoff.md`")
   351	
   352	    return "\n".join(lines)
   353	
   354	# Tolerates optional markdown headings, bullet prefixes, and bold markers around Verdict.
   355	VERDICT = re.compile(
   356	    r"^\s*(?:#+\s*|[-*+]\s*)?\*{0,2}Verdict(?:(?:\*{0,2}:)|(?::\*{0,2}))\s*\*{0,2}(PASS|CHANGES REQUIRED)\*{0,2}\s*$",
   357	    re.IGNORECASE,
   358	)
   359	# Tolerates list numbering, bullets and ** around the severity, and —, –, - or : between location and problem.
   360	FINDING = re.compile(
   500	    if code != 0:
   501	        print(f"{RED}❌ FAILED (exit {code}){RESET}", file=sys.stderr, flush=True)
   502	        raise PreconditionFailedError(label, f"failed with exit code {code}", combined)
   503	    print(f"{GREEN}✅ PASS{RESET}", file=sys.stderr, flush=True)
   504	    return code, out, err
   505	
   506	
   507	def fact(label: str, code: int | None, out: str, err: str) -> str:
   508	    return f"$ {label}\nexit {code if code is not None else 'timeout'}\n{(out + err).rstrip()}\n"
   509	
   510	
   511	def collect_facts(root: Path, epic_dir: str, base: str, hld_text: str, timeout: int) -> tuple[str, str]:
   512	    audit = [sys.executable, str(SCRIPTS / "audit_epic.py"), "--epic-dir", epic_dir, "--base", base]
   513	    audit_code, audit_out, audit_err = run_gate("audit_epic.py", audit, root, timeout)
   514	    audit_output = fact("audit_epic.py", audit_code, audit_out, audit_err)
   515	    results, reports = [], []
   516	    skipped_live_commands: list[str] = []
   517	
   518	    specs = parse_integration_result_specs(hld_text)
   519	    for spec in specs:
   520	        if spec.live:
   521	            missing = [v for v in spec.needs if not os.environ.get(v)]
   522	            if missing:
   523	                results.append(f"$ {spec.command}\nSKIPPED (missing env: {', '.join(missing)})\n")
   524	                skipped_live_commands.append(spec.command)
   525	                continue
   526	        cmd_code, cmd_out, cmd_err = run_gate(f"Integration: {spec.command}", spec.command, root, timeout, shell=True)
   527	        results.append(fact(spec.command, cmd_code, cmd_out, cmd_err))
   528	        if spec.report:
   529	            reports.extend(spec.report.split())
   530	
   531	    roots = re.search(r"^Integration test roots:\s*(.+)$", hld_text, re.MULTILINE)
   532	    if roots:
   533	        roots_list = [r.strip("`") for r in roots.group(1).strip().split()]
   534	        scenarios_file = root / ".devtool" / "epic" / epic_dir / "bdd_scenarios.en.md"
   535	
   536	        if skipped_live_commands:
   537	            # 1. Static check across 100% of scenarios without --results
   538	            check_static = [
   539	                sys.executable,
   540	                str(SCRIPTS / "check_bdd_traceability.py"),
   541	                "tests",
   542	                "--scenarios",
   543	                str(scenarios_file),
   544	                "--roots",
   545	                *roots_list,
   546	            ]
   547	            chk_code, chk_out, chk_err = run_gate("check_bdd_traceability.py tests (static)", check_static, root, timeout)
   548	            results.append(fact(shlex.join(check_static[1:]), chk_code, chk_out, chk_err))
   549	
   550	            # 2. Results check across executed reports
   551	            results_paths = [r.strip("`") for r in reports]
   552	            if results_paths:
   553	                all_ids: list[str] = []
   554	                if scenarios_file.is_file():
   555	                    try:
   556	                        all_ids, _ = load_scenarios(scenarios_file)
   557	                    except Exception:
   558	                        all_ids = []
   559	
   560	                skipped_test_files: set[str] = set()
   561	                for cmd in skipped_live_commands:
   562	                    for token in shlex.split(cmd):
   563	                        if any(token.endswith(ext) for ext in (".py", ".js", ".ts", ".mjs", ".dart", ".kt", ".swift")):
   564	                            skipped_test_files.add(Path(token).name)
   565	                            skipped_test_files.add(token)
   566	
   567	                files_in_roots: list[Path] = []
   568	                for r in roots_list:
   569	                    r_path = root / r
   570	                    if r_path.is_dir():
   571	                        for p in r_path.rglob("*"):
   572	                            if p.is_file() and any(p.name.endswith(ext) for ext in (".py", ".js", ".ts", ".mjs", ".dart", ".kt", ".swift")):
   573	                                files_in_roots.append(p)
   574	
   575	                non_skipped_ids: list[str] = []
   576	                for identifier in all_ids:
   577	                    pattern = re.compile(r"\b" + re.escape(identifier) + r"\b")
   578	                    mentioning_files: list[Path] = []
   579	                    for f in files_in_roots:
   580	                        try:
   581	                            content = f.read_text(encoding="utf-8", errors="ignore")
   582	                            if pattern.search(content):
   583	                                mentioning_files.append(f)
   584	                        except OSError:
   585	                            pass
   586	
   587	                    if mentioning_files and all(
   588	                        f.name in skipped_test_files or str(f.relative_to(root)) in skipped_test_files
   589	                        for f in mentioning_files
   590	                    ):
   591	                        continue
   592	                    non_skipped_ids.append(identifier)
   593	
   594	                if non_skipped_ids:
   595	                    check_results = [
   596	                        sys.executable,
   597	                        str(SCRIPTS / "check_bdd_traceability.py"),
   598	                        "tests",
   599	                        "--scenarios",
   600	                        str(scenarios_file),
   601	                        "--roots",
   602	                        *roots_list,
   603	                        "--ids",
   604	                        *non_skipped_ids,
   605	                        "--results",
   606	                        *results_paths,
   607	                    ]
   608	                    res_code, res_out, res_err = run_gate("check_bdd_traceability.py tests (results)", check_results, root, timeout)
   609	                    results.append(fact(shlex.join(check_results[1:]), res_code, res_out, res_err))
   610	        elif reports:
   611	            results_paths = [r.strip("`") for r in reports]
   612	            check = [
   613	                sys.executable,
   614	                str(SCRIPTS / "check_bdd_traceability.py"),
   615	                "tests",
   616	                "--scenarios",
   617	                str(scenarios_file),
   618	                "--roots",
   619	                *roots_list,
   620	                "--results",
   621	                *results_paths,
   622	            ]
   623	            chk_code, chk_out, chk_err = run_gate("check_bdd_traceability.py", check, root, timeout)
   624	            results.append(fact(shlex.join(check[1:]), chk_code, chk_out, chk_err))
   625	
   626	    py_quality_path = root / ".agents" / "quality" / "python-quality.json"
   627	    if py_quality_path.is_file():
   628	        try:
   629	            q_cfg = json.loads(py_quality_path.read_text(encoding="utf-8"))
   630	            caps = q_cfg.get("capabilities", {}) if isinstance(q_cfg, dict) else {}
   631	            for cap_name in ("anti_stub", "importlinter_coverage", "self_probe"):
   632	                cap = caps.get(cap_name)
   633	                if isinstance(cap, dict) and isinstance(cap.get("command"), str) and cap["command"].strip():
   634	                    c_cmd = cap["command"].strip()
   635	                    c_code, c_out, c_err = run_gate(f"Quality pre-check ({cap_name})", c_cmd, root, timeout, shell=True)
   636	                    audit_output += "\n" + fact(c_cmd, c_code, c_out, c_err)
   637	        except (json.JSONDecodeError, OSError):
   638	            pass
   639	
   640	    return audit_output, "\n".join(results) or "No Integration results declared.\n"
   641	
   642	
   643	def artefact_lines(root: Path, epic_dir: str) -> str:
   644	    folder = root / ".devtool" / "epic" / epic_dir
   645	    names = sorted(p.name for p in folder.glob("*.md"))
   646	    spec = [n for n in names if not n.startswith(("task_", "bdd_", epic_dir, "review_results"))]
   647	    paths = (spec + [f"{epic_dir}.en.md", "bdd_scenarios.en.md"]
   648	             + [n for n in names if n.startswith("task_")] + ["evidence/"])
   649	    return "\n".join(f"- `.devtool/epic/{epic_dir}/{p}`" for p in paths)
   650	
   651	
   652	def build_diff_section(root: Path, base: str, sha: str, max_lines: int = MAX_DIFF_LINES, max_bytes: int = MAX_DIFF_BYTES) -> str:
   653	    """Hybrid inlining: always show full --stat; inline filtered diff if within size budget."""
   654	    full_stat = git_run(
   655	        root, "diff", "--stat", f"{base}...{sha}", "--", ".", ":(exclude).devtool/**"
   656	    ).decode("utf-8", "replace").strip()
   657	    filtered_diff = git_run(
   658	        root, "diff", f"{base}...{sha}", "--", ".", *EXCLUDES
   659	    ).decode("utf-8", "replace").strip()
   660	
   661	    stat_fence = fence_for(full_stat)
   662	    stat_block = f"Full file change summary (`git diff --stat`, including locks/codegen):\n\n{stat_fence}text\n{full_stat or '(no changes outside .devtool/)'}\n{stat_fence}\n\n"
   663	
   664	    if not filtered_diff:
   665	        return stat_block + "No non-excluded source code changes to inline."
   666	
   667	    line_count = len(filtered_diff.splitlines())
   668	    byte_size = len(filtered_diff.encode("utf-8"))
   669	
   670	    if line_count <= max_lines and byte_size <= max_bytes:
   671	        diff_fence = fence_for(filtered_diff)
   672	        return (
   673	            stat_block
   674	            + f"The complete source diff ({line_count} lines, {byte_size // 1024} KB, lock, generated, and noisy metadata/asset files excluded) "
   675	            f"is inlined below. Do NOT run `git diff` again unless you need to inspect an excluded file:\n\n"
   676	            f"{diff_fence}diff\n{filtered_diff}\n{diff_fence}"
   677	        )
   678	
   679	    return (
   680	        stat_block
   681	        + f"The source diff is large ({line_count} lines, {byte_size // 1024} KB > inline budget). "
   682	        f"Do NOT run an unfiltered `git diff`; inspect specific target files via `git diff {base}...{sha} -- <path>` as needed."
   683	    )
   684	
   685	
   686	def diff_range(root: Path, base: str, commits: str | None = None) -> tuple[str, str]:
   687	    """Extract commit log and diff section for an arbitrary base and commit range."""
   688	    commit_spec = commits if commits else f"{base}...HEAD"
   689	    log = git_run(root, "log", "--oneline", commit_spec).decode("utf-8", "replace").strip()
   690	    full_stat = git_run(
   691	        root, "diff", "--stat", commit_spec, "--", "."
   692	    ).decode("utf-8", "replace").strip()
   693	    filtered_diff = git_run(
   694	        root, "diff", commit_spec, "--", ".", *EXCLUDES
   695	    ).decode("utf-8", "replace").strip()
   696	
   697	    stat_fence = fence_for(full_stat)
   698	    stat_block = f"Full file change summary (`git diff --stat`, including locks/codegen):\n\n{stat_fence}text\n{full_stat or '(no changes)'}\n{stat_fence}\n\n"
   699	
   700	    if not filtered_diff:
   701	        diff_section = stat_block + "No non-excluded source code changes to inline."
   702	    else:
   703	        line_count = len(filtered_diff.splitlines())
   704	        byte_size = len(filtered_diff.encode("utf-8"))
   705	        if line_count <= MAX_DIFF_LINES and byte_size <= MAX_DIFF_BYTES:
   706	            diff_fence = fence_for(filtered_diff)
   707	            diff_section = (
   708	                stat_block
   709	                + f"The complete source diff ({line_count} lines, {byte_size // 1024} KB, lock, generated, and noisy metadata/asset files excluded) "
   710	                f"is inlined below. Do NOT run `git diff` again unless you need to inspect an excluded file:\n\n"
   711	                f"{diff_fence}diff\n{filtered_diff}\n{diff_fence}"
   712	            )
   713	        else:
   714	            diff_section = (
   715	                stat_block
   716	                + f"The source diff is large ({line_count} lines, {byte_size // 1024} KB > inline budget). "
   717	                f"Do NOT run an unfiltered `git diff`; inspect specific target files via `git diff {commit_spec} -- <path>` as needed."
   718	            )
   719	    return log, diff_section
   720	
   721	
   722	def effective_model(cli: str, model: str | None) -> str:
   723	    if model:
   724	        return model
   725	    return str(DEFAULT_REVIEW_CONFIG["providers"].get(cli, {}).get("model", "default"))
   726	
   727	
   728	def effective_thinking_level(cli: str, thinking_level: str | None) -> str:
   729	    if thinking_level and thinking_level in THINKING_LEVELS:
   730	        return thinking_level
   731	    return str(DEFAULT_REVIEW_CONFIG["providers"].get(cli, {}).get("thinking_level", "high"))
   732	
   733	
   734	def resolve_cli_binary(cli: str) -> str | None:
   735	    if cli == "kiro":
   815	    return ", ".join(parts) + (" finding" if total == 1 else " findings")
   816	
   817	
   818	def format_triage_header(
   819	    title: str,
   820	    sha: str,
   821	    cli: str,
   822	    model: str,
   823	    thinking_level: str,
   824	    verdict: str,
   825	    findings: list[tuple[str, str, str]] | list[list[str]],
   826	) -> list[str]:
   827	    cli_display = {"claude": "Claude", "codex": "Codex", "agy": "agy", "kiro": "Kiro", "ollama": "Ollama"}.get(cli, cli.capitalize())
   828	    thinking_display = thinking_level.replace("-", " ").title() if thinking_level else "High"
   829	    summary = format_findings_summary(findings)
   830	    verdict_display = verdict.upper() if verdict else "NONE"
   831	    return [
   832	        title,
   833	        "",
   834	        f"• Candidate SHA: {sha}",
   835	        f"• Reviewer: {cli_display} ( {model} )",
   836	        f"• Thinking Level: {thinking_display}",
   837	        f"• Verdict: {verdict_display} ({summary})",
   838	    ]
   839	
   840	
   841	def cell(text: str) -> str:
   842	    return text.replace("|", "\\|").replace("\r", "").replace("\n", " ").strip()
   843	
   844	
   845	def fence_for(text: str) -> str:
   846	    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
   847	    return "`" * max(3, longest + 1)
   848	
   849	
   850	def rounds_in(text: str) -> list[tuple[int, list[str]]]:
   851	    """Split review_results.md into (number, lines) rounds, ignoring headings inside fenced raw output."""
   852	    rounds: list[tuple[int, list[str]]] = []
   853	    fence = ""
   854	    for line in text.splitlines():
   855	        match = FENCE.match(line)
   856	        if fence:
   857	            fence = "" if line.rstrip() == fence else fence
   858	        elif match:
   859	            fence = match.group(1)
   860	        elif (heading := re.fullmatch(r"## Round (\d+)", line)):
   861	            rounds.append((int(heading.group(1)), []))
   862	            continue
   863	        if rounds:
   864	            rounds[-1][1].append(line)
   865	    return rounds
   866	
   867	
   868	def split_row(line: str) -> list[str]:
   869	    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
   870	
   871	
   872	def metadata(lines: list[str]) -> list[str]:
   873	    """A round's own lines: its fields and findings table, never its raw output."""
   874	    return lines[:lines.index("Raw output:")] if "Raw output:" in lines else lines
   875	
   876	
   877	def table_findings(lines: list[str]) -> list[tuple[str, list[str]]]:
   878	    """(line, cells) for every findings row, `| <number> |` onwards, well formed or not."""
   879	    return [(line, split_row(line)) for line in metadata(lines) if FINDING_ROW.match(line)]
   880	
   881	
   882	def parse_findings(out: str, verdict: str | None = None) -> list[tuple[str, str, str]]:
   883	    """Each finding line as (severity, location, problem); a blocking line in list format keeps its raw text."""
   884	    findings = []
   885	    for line in out.splitlines():
   886	        if (match := FINDING.match(line)):
   887	            sev, loc, problem = match.groups()
   888	            findings.append((sev.capitalize(), loc, problem))
   889	        elif (blocking := UNPARSED_BLOCKING.search(line)):
   890	            if verdict == "PASS" and not findings:
   891	                continue
   892	            findings.append((blocking.group(1).capitalize(), "unparsed", line.strip()))
   893	    return findings
   894	
   895	
   896	def render_round(number: int, meta: dict[str, str], findings: list[tuple[str, str, str]], output: str) -> str:
   897	    head = "".join(f"- **{key}**: {value}\n" for key, value in meta.items())
   898	    table = "| # | Severity | Location | Problem | Decision |\n|---|----------|----------|---------|----------|\n"
   899	    table += "".join(f"| {i} | {sev} | {cell(loc)} | {cell(problem)} |  |\n"
   900	                     for i, (sev, loc, problem) in enumerate(findings, 1))
   901	    fence = fence_for(output)
   902	    return f"## Round {number}\n\n{head}\n{table}\nRaw output:\n\n{fence}text\n{output.rstrip()}\n{fence}\n"
   903	
   904	
   905	def run_principal_doc(root: Path, args: argparse.Namespace, sha: str) -> int:
   906	    doc_path = root / args.doc if not Path(args.doc).is_absolute() else Path(args.doc)
   907	    if not doc_path.is_file():
   908	        print(f"error: document path not found: {args.doc}", file=sys.stderr)
   909	        return 2
   910	
   911	    content = doc_path.read_text(encoding="utf-8")
   912	    if not content.strip() or not re.search(r"^#+\s+\S+", content, re.MULTILINE):
   913	        print(f"error: document has invalid structure or missing headings: {args.doc}", file=sys.stderr)
   914	        return 2
   915	
   916	    base_sha = git_run(root, "rev-parse", "--verify", args.base).decode().strip()
   917	    artefacts = f"- `{args.doc}`\n\nDocument content:\n\n```markdown\n{content}\n```"
   918	    readiness_output = "N/A (Ad-hoc review of standalone document)"
   919	
   920	    prompt = Template(principal_prompt_path().read_text(encoding="utf-8")).safe_substitute(
   972	def delta_round_context(root: Path, args: argparse.Namespace, sha: str, kind: str = "principal") -> tuple[str, dict[str, str]]:
   973	    """Round >= 2 prompt block: the previous round's findings and decisions plus the revision diff since it.
   974	
   975	    Round 1 (or --full) returns ("", {}) so a full-modules/full-scope audit runs first.
   976	    Round 2 narrows scope to Delta Verification (prev_sha..sha) and prohibits new Minor findings on untouched files.
   977	    Round 3+ enters Convergence Mode (Blocker-Only: incomplete fixes or new Critical/Important regressions in prev_sha..sha).
   978	    """
   979	    if getattr(args, "full", False):
   980	        return "", {}
   981	    name, _ = review_file(kind)
   982	    path = root / ".devtool" / "epic" / args.epic_dir / name
   983	    if not path.exists():
   984	        return "", {}
   985	    all_rounds = rounds_in(path.read_text(encoding="utf-8"))
   986	    completed = [(n, lines) for n, lines in all_rounds if "- **Status**: completed" in metadata(lines)]
   987	    if not completed:
   988	        return "", {}
   989	    number, lines = completed[-1]
   990	    prev_sha = round_meta(lines).get("SHA", "")
   991	    if not prev_sha or prev_sha == sha:
   992	        return "", {}
   993	    epic = f".devtool/epic/{args.epic_dir}"
   994	    records = [f":(exclude){epic}/{n}" for n in ("principal_review.md", "review_results.md")]
   995	    try:
   996	        if kind == "principal":
   997	            outside = re.findall(r"`([^`]+)`", principal_artefact_lines(root, args.epic_dir))
   998	            paths = [epic, *dict.fromkeys(p for p in outside if not p.startswith(epic))]
   999	            diff = git_run(root, "diff", f"{prev_sha}..{sha}", "--", *paths, *records).decode("utf-8", "replace").strip()
  1000	        else:
  1001	            diff = git_run(root, "diff", f"{prev_sha}..{sha}", "--", ".", *EXCLUDES, *records).decode("utf-8", "replace").strip()
  1002	            if not diff:
  1003	                diff = git_run(root, "diff", f"{prev_sha}..{sha}", "--", ".", *records).decode("utf-8", "replace").strip()
  1004	        source = git_run(root, "diff", "--stat", f"{prev_sha}..{sha}", "--", ".",
  1005	                         ":(exclude).devtool/**").decode("utf-8", "replace").strip()
  1006	    except ContractError:
  1007	        return "", {}
  1008	    if not diff or len(diff.splitlines()) > getattr(args, "diff_limit", MAX_DIFF_LINES):
  1009	        return "", {}
  1010	
  1011	    next_round = len(all_rounds) + 1
  1012	    prev_meta = round_meta(lines)
  1013	    prev_cli = prev_meta.get("CLI", "claude")
  1014	    prev_model = prev_meta.get("Model", "default")
  1015	    curr_cli = getattr(args, "cli", None) or prev_cli
  1016	    curr_model = effective_model(curr_cli, getattr(args, "model", None))
  1017	
  1018	    table = ["| # | Severity | Location | Problem | Decision |", "|---|---|---|---|---|"]
  1019	    table += ["| " + " | ".join(cell(c)[:400] for c in row) + " |" for row in finding_rows(lines)]
  1020	
  1021	    earlier_ledger_blocks: list[str] = []
  1022	    fixed_registry_lines: list[str] = []
  1023	    for r_num, r_lines in completed:
  1024	        for row in finding_rows(r_lines):
  1025	            if len(row) >= 5 and row[4].strip().lower().startswith("fixed in"):
  1026	                fixed_registry_lines.append(
  1027	                    f"- `{row[2].strip()}` (Round {r_num} #{row[0].strip()}, `{row[1].strip()}`): "
  1028	                    f"{cell(row[3])[:180]} -> `{row[4].strip()}`"
  1029	                )
  1030	    if len(completed) > 1:
  1031	        for r_num, r_lines in completed[:-1]:
  1032	            r_meta = round_meta(r_lines)
  1033	            r_rows = finding_rows(r_lines)
  1034	            if not r_rows:
  1035	                continue
  1036	            r_table = ["| # | Severity | Location | Problem | Decision |", "|---|---|---|---|---|"]
  1037	            r_table += ["| " + " | ".join(cell(c)[:300] for c in row) + " |" for row in r_rows]
  1038	            earlier_ledger_blocks.append(
  1039	                f"#### Round {r_num} ({r_meta.get('CLI', '?')} / {r_meta.get('Model', '?')} at `{r_meta.get('SHA', '?')[:7]}`)\n\n"
  1040	                + "\n".join(r_table)
  1041	            )
  1042	
  1043	    provider_note = (
  1044	        "You are taking over from a different model family. "
  1045	        if curr_cli != prev_cli
  1046	        else "You are running in a new stateless session following a prior review round. "
  1047	    )
  1048	    handoff_block = (
  1049	        "### Cross-Provider Handoff & Anti-Ping-Pong Guardrail\n\n"
  1050	        f"- **Previous Reviewer**: `{prev_cli}` (`{prev_model}`) at `{prev_sha[:7]}`\n"
  1051	        f"- **Current Reviewer**: `{curr_cli}` (`{curr_model}`) at `{sha[:7]}`\n"
  1052	        f"- **Shared Context Continuity & Anti-Ping-Pong Rule**: {provider_note}"
  1053	        "Strictly honor all `dismissed: <rationale>` decisions and `fixed in <sha>` resolutions recorded in the "
  1054	        "Shared Context Ledger below. Do NOT ask to revert or rewrite a prior round's accepted fix (zero solution ping-pong) "
  1055	        "unless it introduces an objective runtime defect or violates a frozen contract in the approved HLD / "
  1056	        "`bdd_scenarios.en.md` / `Decisions Already Made`.\n\n"
  1057	    )
  1058	    fixed_registry_block = (
  1059	        "### Previously Fixed Locations Registry (Verify-Then-Close)\n\n"
  1060	        + "\n".join(fixed_registry_lines)
  1061	        + "\n\n"
  1062	        if fixed_registry_lines
  1063	        else ""
  1064	    )
  1065	
  1066	    fence, stat_fence = fence_for(diff), fence_for(source)
  1067	    if next_round >= 3:
  1068	        header_block = (
  1069	            f"## Round Scope: Convergence Mode (Round {next_round})\n\n"
  1070	            f"You are in Round 3+ Convergence Mode. ONLY report (a) incomplete fixes from previous rounds, or "
  1071	            f"(b) NEW Critical/Important regressions directly introduced by the latest fix commit "
  1072	            f"(`{prev_sha[:12]}..{sha[:12]}`). DO NOT report new Minor/stylistic findings on untouched code.\n\n"
  1073	        )
  1074	        scope_meta = {"Scope": f"convergence from round {number} ({prev_sha[:7]})"}
  1075	    else:
  1076	        header_block = (
  1077	            f"## Round Scope: Delta Review (Round {next_round})\n\n"
  1078	            f"Round {number} reviewed `{prev_sha}`. The developer triaged it and revised the code/artefacts since. "
  1079	            "Do NOT re-derive the whole design or re-audit untouched modules from scratch. "
  1080	            "DO NOT report new Minor/stylistic findings on untouched code or artefacts.\n\n"
  1081	        )
  1082	        scope_meta = {"Scope": f"delta from round {number} ({prev_sha[:7]})"}
  1083	
  1084	    earlier_section = (
  1085	        "### Earlier Rounds Shared Context Ledger (Cumulative Memory)\n\n"
  1086	        + "\n\n".join(earlier_ledger_blocks)
  1087	        + "\n\n"
  1088	        if earlier_ledger_blocks
  1089	        else ""
  1090	    )
  1091	
  1092	    block = (
  1093	        header_block
  1094	        + handoff_block
  1095	        + fixed_registry_block
  1096	        + "1. **Approved-Design Anchoring**: Every verification and finding MUST be anchored strictly to the approved HLD "
  1097	        "(`.devtool/epic/<epic_dir>/<epic_dir>.en.md`), `bdd_scenarios.en.md`, and `Decisions Already Made` in `task_*.md`.\n"
  1098	        "2. **Verify-Then-Close on Fixed Locations**: For each finding below marked `fixed in <sha>`, verify whether the revision "
  1099	        f"resolves the original defect at `{sha}`. If resolved, **close it silently (PASS)** — do NOT propose alternative "
  1100	        "implementations or secondary refactors on that fix.\n"
  1101	        "3. **Diff-Hunk Isolation on Fixed Files (No Late Drip-Feed)**: On any file listed in `Previously Fixed Locations Registry`, "
  1102	        "do NOT report pre-existing issues on untouched functions or lines outside the `prev_sha..sha` diff hunks. You may only "
  1103	        "report a finding on a previously fixed file if (a) `[INCOMPLETE_FIX]` the original defect remains unresolved, or "
  1104	        "(b) `[NEW_REGRESSION]` the modified lines in `prev_sha..sha` directly introduce a new Critical/Important bug.\n"
  1105	        "4. Do not re-raise a finding marked `dismissed:` unless the source contradicts its rationale.\n"
  1106	        "5. The revision diff below is the primary scope: review the new and edited text/code, and every artefact "
  1107	        "or source symbol that text/code references or must stay consistent with (P1, P2, P5, P7). Read an "
  1108	        "unchanged file only to verify such a reference.\n"
  1109	        "6. Everything else was reviewed in round "
  1110	        f"{number}. Skip it, and DO NOT report new Minor findings on untouched code.\n\n"
  1111	        + earlier_section
  1112	        + f"### Round {number} findings and decisions ({prev_cli} / {prev_model})\n\n" + "\n".join(table) + "\n\n"
  1113	        f"### Revision diff since round {number} (`{prev_sha[:12]}..{sha[:12]}`)\n\n"
  1114	        f"{fence}diff\n{diff}\n{fence}\n\n"
  1115	        f"Source files changed since round {number} (stat only):\n\n"
  1116	        f"{stat_fence}text\n{source or '(none outside .devtool/)'}\n{stat_fence}\n"
  1117	    )
  1118	    return block, scope_meta
  1119	
  1120	
  1230	def run(args: argparse.Namespace) -> int:
  1231	    kind = getattr(args, "kind", "code")
  1232	    root = Path(git_run(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
  1233	
  1234	    raw_priority = getattr(args, "provider_priority", None)
  1235	    parsed_priority = [p.strip() for p in raw_priority.split(",") if p.strip()] if raw_priority else None
  1236	    cli, model, thinking_level = resolve_review_settings(
  1237	        root=root,
  1238	        epic_dir=getattr(args, "epic_dir", None),
  1239	        kind=kind,
  1240	        cli_arg=args.cli,
  1241	        model_arg=args.model,
  1242	        thinking_arg=getattr(args, "thinking_level", None),
  1243	        auto_quota=bool(getattr(args, "auto_quota", False)),
  1244	        provider_priority_arg=parsed_priority,
  1245	    )
  1246	    args.cli = cli
  1247	    args.model = model
  1248	    args.thinking_level = thinking_level
  1249	
  1250	    if kind == "principal" and args.cli == "ollama":
  1251	        print("--kind principal supports --cli claude, codex, or agy (and kiro)", file=sys.stderr)
  1252	        return 2
  1253	
  1254	    if args.cli == "ollama":
  1255	        if not args.model:
  1256	            print("--cli ollama needs --model", file=sys.stderr)
  1257	            return 2
  1258	    elif not resolve_cli_binary(args.cli):
  1259	        print(f"{args.cli} not found on PATH", file=sys.stderr)
  1260	        return 2
  1261	    if status_lines(root):
  1262	        print("commit or stash your changes before a review", file=sys.stderr)
  1263	        return 2
  1264	    max_rounds = getattr(args, "max_rounds", MAX_REVIEW_ROUNDS)
  1265	    if getattr(args, "epic_dir", None) and not getattr(args, "force", False):
  1266	        completed_count = _completed_rounds_count(root, args.epic_dir, kind)
  1267	        if completed_count >= max_rounds:
  1268	            print_gate_banner(
  1269	                PreconditionFailedError(
  1270	                    "Max review rounds",
  1271	                    f"Max review rounds ({max_rounds}) reached; Circuit Breaker halted for human architect",
  1272	                ),
  1273	                args.cli,
  1274	            )
  1275	            return 2
  1276	    sha = head_of(root)
  1277	
  1278	    if kind == "principal":
  1279	        return run_principal(root, args, sha)
  1280	
  1281	    if not args.epic_dir:
  1282	        return run_adhoc_code(root, args, sha)
  1283	
  1284	    model_ctx = None
  1285	    if args.cli == "ollama":
  1286	        try:
  1287	            model_ctx = local_review.probe(args.host, args.model)
  1288	        except local_review.LocalReviewError as error:
  1289	            print_gate_banner(PreconditionFailedError("Ollama probe", str(error)), args.cli)
  1290	            return 2
  1291	    hld_text = (root / ".devtool" / "epic" / args.epic_dir / f"{args.epic_dir}.en.md").read_text(encoding="utf-8")
  1292	    try:
  1293	        facts_timeout = getattr(args, "facts_timeout", 300)
  1294	        audit_output, results_output = collect_facts(root, args.epic_dir, args.base, hld_text, facts_timeout)
  1295	    except PreconditionFailedError as error:
  1296	        print_gate_banner(error, args.cli)
  1297	        return 2
  1298	    if args.cli == "ollama":
  1299	        return run_local(root, args, sha, audit_output, results_output, model_ctx)
  1300	    diff_limit = getattr(args, "diff_limit", MAX_DIFF_LINES)
  1301	    round_context, scope = delta_round_context(root, args, sha, kind="code")
  1302	    if scope:
  1303	        print(f"{scope['Scope']}: reviewing the revision delta, not the full epic diff (--full to review everything)",
  1304	              file=sys.stderr)
  1305	    diff_section = build_diff_section(root, args.base, sha, max_lines=diff_limit)
  1306	    prompt = Template(PROMPT.read_text(encoding="utf-8")).safe_substitute(
  1307	        rules=RULES.read_text(encoding="utf-8").strip(),
  1308	        sha=sha,
  1309	        base=args.base,
  1310	        epic_dir=f".devtool/epic/{args.epic_dir}",
  1311	        artefacts=artefact_lines(root, args.epic_dir),
  1312	        audit_output=audit_output.rstrip(),
  1313	        results_output=results_output.rstrip(),
  1314	        round_context=round_context,
  1315	        diff_section=diff_section,
  1316	    )
  1317	    before = status_lines(root)  # after the facts: running the test commands may write build output
  1318	    code, out, err = execute(cli_command(args.cli, args.model, args.thinking_level), root, args.timeout, prompt)
  1319	    changed = tree_changes(root, before, sha)
  1320	    return record_round(root, args, sha, [Pass("review", code, out, err, prompt)], changed, scope)
  1321	
  1322	
  1323	def live_log_dir(root: Path, epic_dir: str) -> Path:
  1324	    """Where each pass streams its output: build/local-review/<epic_dir> when Git ignores it, else the Git directory.
  1325	
  1326	    Either place leaves `git status` untouched, so the logs never trip the tree-modified check."""
  1327	    visible = root / "build" / "local-review" / epic_dir
  1328	    if subprocess.run(["git", "check-ignore", "-q", str(visible)], cwd=root, check=False).returncode == 0:
  1329	        return visible
  1330	    return root / git_run(root, "rev-parse", "--git-path", f"local-review/{epic_dir}").decode().strip()
  1331	
  1332	
  1333	def run_local(root: Path, args: argparse.Namespace, sha: str, audit_output: str, results_output: str,
  1334	              model_ctx: int | None) -> int:
  1335	    """Fit every slice before the first call, then review them one at a time; the first failed pass ends the run."""
  1336	    ctx = args.num_ctx or model_ctx or local_review.DEFAULT_NUM_CTX
  1337	    planned: list[tuple[local_review.Slice, str]] = []
  1338	    try:
  1339	        for slice_ in local_review.build_slices(root, args.epic_dir, args.base, sha, audit_output, results_output,
  1340	                                                EXCLUDES):
  1341	            system = local_review.render_system(slice_)
  1342	            budget = int(ctx * local_review.PROMPT_SHARE) - local_review.estimate_tokens(system)
  1343	            planned.append((local_review.fit(slice_, budget), system))
  1344	    except local_review.LocalReviewError as error:
  1345	        print_gate_banner(PreconditionFailedError("Context budget", str(error)), args.cli)
  1346	        return 2
  1347	    logs = live_log_dir(root, args.epic_dir)
  1348	    logs.mkdir(parents=True, exist_ok=True)
  1349	    print(f"{CYAN}Live logs:{RESET} {logs}", file=sys.stderr, flush=True)
  1350	    before = status_lines(root)
  1520	    rows = []
  1521	    for name, lines in blocks or [("review", output.splitlines())]:
  1522	        verdicts = [m.group(1).upper() for line in lines if (m := VERDICT.match(line))]
  1523	        after = lines[lines.index("--- error ---") + 1:] if "--- error ---" in lines else []
  1524	        rows.append((name, verdicts[-1] if verdicts else "none", after[0].strip() if after else "—"))
  1525	    return rows
  1526	
  1527	
  1528	def finding_rows(lines: list[str]) -> list[list[str]]:
  1529	    return [cells for _, cells in table_findings(lines) if len(cells) == 5]
  1530	
  1531	
  1532	def comparison_row(number: int, lines: list[str]) -> str:
  1533	    meta, rows = round_meta(lines), finding_rows(lines)
  1534	    counts = [sum(cells[1] == severity for cells in rows) for severity in ("Critical", "Important", "Minor")]
  1535	    fixed = sum(cells[4].startswith("fixed in ") for cells in rows)
  1536	    dismissed = sum(cells[4].startswith("dismissed: ") for cells in rows)
  1537	    undecided = sum(cells[1] in BLOCKING and not cells[4].startswith(("fixed in ", "dismissed: ")) for cells in rows)
  1538	    values = [str(number), f"{meta.get('CLI', '?')} / {meta.get('Model', '?')}", meta.get("SHA", "?")[:7],
  1539	              meta.get("Status", "?"), meta.get("Verdict", "?"), *map(str, [*counts, fixed, dismissed, undecided])]
  1540	    return "| " + " | ".join(cell(value) for value in values) + " |"
  1541	
  1542	
  1543	def since_lines(previous: list[list[str]], latest: list[list[str]]) -> list[str]:
  1544	    """What became of the previous round's blocking or fixed findings, compared by file path."""
  1545	    lines = []
  1546	    for cells in previous:
  1547	        fixed = cells[4].startswith("fixed in ")
  1548	        if cells[1] not in BLOCKING and not fixed:
  1549	            continue
  1550	        again = [f"#{row[0]}" for row in latest if path_of(row[2]) == path_of(cells[2])]
  1551	        if again:
  1552	            lines.append(f"- {cells[2]}: re-reported at the same path ({', '.join(again)})"
  1553	                         + (" — check the fix" if fixed else ""))
  1554	        else:
  1555	            lines.append(f"- {cells[2]}: not re-reported")
  1556	    return lines or ["No blocking or fixed finding in the previous round."]
  1557	
  1558	
  1559	HIGH_RISK_KEYWORDS = (
  1560	    "security",
  1561	    "race",
  1562	    "deadlock",
  1563	    "corrupt",
  1564	    "rollback",
  1565	    "contract",
  1566	    "shared-contracts",
  1567	    "unbound",
  1568	    "notimplementederror",
  1569	    "_stub",
  1570	    "leak",

exec
/bin/zsh -lc "rg -n 'require-bilingual|vi.md|bilingual|read_text|RULES' skills/dev-implementation/resources/scripts/{audit_epic.py,integrate_branch.py,check_epic_readiness.py,check_bdd_traceability.py,test_integrate_branch.py} skills/dev-implementation/references/{review-rules.md,principal-review-prompt.md}; nl -ba skills/finishing-a-development-branch/SKILL.md | sed -n '1,190p'; nl -ba skills/quality_check/resources/scripts/verify_polyglot_registry.py | sed -n '142,260p;350,438p;535,625p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/manage_worker_pool.py | sed -n '68,168p'; nl -ba skills/dev-implementation/resources/scripts/compute_execution_order.py | sed -n '20,115p;175,218p'; nl -ba skills/dev-lifecycle/resources/scripts/lifecycle_runner.py | sed -n '511,620p;1100,1183p'; nl -ba scripts/verify.sh | sed -n '1,65p;125,190p;295,417p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
rg: skills/dev-implementation/resources/scripts/integrate_branch.py: No such file or directory (os error 2)
rg: skills/dev-implementation/resources/scripts/test_integrate_branch.py: No such file or directory (os error 2)
skills/dev-implementation/resources/scripts/check_bdd_traceability.py:39:def read_text(path: Path) -> str:
skills/dev-implementation/resources/scripts/check_bdd_traceability.py:42:        return path.read_text(encoding="utf-8")
skills/dev-implementation/resources/scripts/check_bdd_traceability.py:53:    for number, line in enumerate(read_text(path).splitlines(), start=1):
skills/dev-implementation/resources/scripts/check_bdd_traceability.py:90:        sibling = path.with_name(path.name[: -len(".en.md")] + ".vi.md")
skills/dev-implementation/resources/scripts/check_bdd_traceability.py:106:    for line in read_text(path).splitlines():
skills/dev-implementation/resources/scripts/check_bdd_traceability.py:172:            lines = path.read_text(encoding="utf-8").splitlines()
skills/dev-implementation/resources/scripts/check_epic_readiness.py:75:    hld_text = hld_path.read_text(encoding="utf-8")
skills/dev-implementation/resources/scripts/check_epic_readiness.py:78:    tasks: dict[Path, str] = {p: p.read_text(encoding="utf-8") for p in task_paths}
skills/dev-implementation/resources/scripts/check_epic_readiness.py:165:    bilingual_files = sorted(set(epic_path.glob("*.en.md")) | set(epic_path.glob("*.vi.md")))
skills/dev-implementation/resources/scripts/check_epic_readiness.py:166:    if bilingual_files:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:171:            "--require-bilingual",
skills/dev-implementation/resources/scripts/check_epic_readiness.py:172:            *[str(f) for f in bilingual_files],
skills/dev-implementation/resources/scripts/check_epic_readiness.py:220:        mirror_text = mirror_path.read_text(encoding="utf-8")
skills/dev-implementation/resources/scripts/check_epic_readiness.py:321:    canonical_blocks = extract_scenario_blocks(bdd_en_path.read_text(encoding="utf-8"))
skills/dev-implementation/resources/scripts/check_epic_readiness.py:331:    bdd_vi_path = epic_path / "bdd_scenarios.vi.md"
skills/dev-implementation/resources/scripts/check_epic_readiness.py:340:                    Finding("R3", "FAIL", f"bdd_scenarios.vi.md: {missing_or_extra} missing or extra")
skills/dev-implementation/resources/scripts/check_epic_readiness.py:354:    for line in bdd_en_path.read_text(encoding="utf-8").splitlines():
skills/dev-implementation/resources/scripts/check_epic_readiness.py:516:                    file_text = full_path.read_text(encoding="utf-8", errors="ignore")
skills/dev-implementation/resources/scripts/check_epic_readiness.py:581:                    tracked_contents.append(f.read_text(encoding="utf-8", errors="ignore"))
skills/dev-implementation/resources/scripts/check_epic_readiness.py:665:    vi_file = ctx.root / ".devtool" / "epic" / ctx.epic_dir / f"{ctx.epic_dir}.vi.md"
skills/dev-implementation/resources/scripts/check_epic_readiness.py:668:            vi_text = vi_file.read_text(encoding="utf-8")
skills/dev-implementation/resources/scripts/check_epic_readiness.py:672:                        "R7", "FAIL", "Depends on epic differs between .en.md and .vi.md"
skills/dev-implementation/resources/scripts/check_epic_readiness.py:686:                        f"Spec Errata IDs differ between .en.md and .vi.md: {[e for e, _ in en_errata]} vs {[e for e, _ in vi_errata]}",
skills/dev-implementation/resources/scripts/check_epic_readiness.py:703:        handoff_text = handoff_file.read_text(encoding="utf-8")
skills/dev-implementation/resources/scripts/check_epic_readiness.py:744:        spec_text = spec_files[0].read_text(encoding="utf-8")
skills/dev-implementation/resources/scripts/check_epic_readiness.py:899:            text = hld_file.read_text(encoding="utf-8")
skills/dev-implementation/resources/scripts/check_epic_readiness.py:912:                    t_text = tf.read_text(encoding="utf-8")
skills/dev-implementation/resources/scripts/check_epic_readiness.py:930:    hld_text = hld_file.read_text(encoding="utf-8") if hld_file.is_file() else ""
     1	---
     2	name: finishing-a-development-branch
     3	description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work
     4	---
     5	
     6	# Finishing a Development Branch
     7	
     8	## Overview
     9	
    10	**Core principle:** Verify tests → Detect environment → Present options → Update onto base → Execute choice → Clean up.
    11	
    12	**Integration rule:** conflicts are resolved on the branch, inside its worktree, never on the base
    13	branch. The base only ever receives a `--no-ff` merge whose tree is exactly the tree that passed
    14	verification. `integrate_branch.py` enforces this; do not integrate by hand.
    15	
    16	**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."
    17	
    18	Resolve the paths this skill uses. `SKILL_DIR` is the directory this `SKILL.md` was loaded from —
    19	vendored under `.agents/skills/` in some projects, inside a plugin install in others, so never
    20	hardcode it:
    21	
    22	```bash
    23	SKILL_DIR=<absolute path of the directory containing this SKILL.md>
    24	INTEGRATE="$SKILL_DIR/resources/scripts/integrate_branch.py"
    25	```
    26	
    27	Shell variables do not survive between separate tool calls: set both in the same command that uses
    28	them, or write the absolute paths out.
    29	
    30	```mermaid
    31	flowchart TD
    32	    TESTS["Step 1: Verify Tests Passing"] --> DETECT["Step 2: Detect Environment (Worktree vs Repo)"]
    33	    DETECT --> BASE["Step 3: Determine Base Branch"]
    34	    BASE --> OPTS["Step 4: Present Options (Merge / PR / Keep)"]
    35	    OPTS --> EXEC{"Step 5: User Choice"}
    36	    EXEC -->|"1. Merge Locally"| ARCHIVE["Pre-Finish Hook: archive done tasks and commit"]
    37	    EXEC -->|"2. Push and Create PR"| ARCHIVE
    38	    EXEC -->|"3. Keep As-Is"| KEEP["Preserve branch and worktree (tasks remain in done/)"]
    39	    ARCHIVE --> UPDATE["Update onto Base: preflight, rebase, verify by tier"]
    40	    UPDATE -->|"Option 1"| LAND["integrate_branch.py land"]
    41	    UPDATE -->|"Option 2"| PUSH["git push -u and forge PR create"]
    42	    LAND --> CLEANUP["Step 6: Worktree Cleanup and Delete Branch"]
    43	    PUSH --> RETAIN["Retain worktree for PR review iteration"]
    44	```
    45	
    46	
    47	## Step 1: Verify Readiness / Tests
    48	
    49	- **In-Lifecycle Epic Mode (entering from `dev-lifecycle` / `dev-implementation` after Gate 4 `🟢 LGTM` & Gate 5 sign-off)**:
    50	  - Do **not** redundantly run the full repository test suite (`Test All`) here before archiving tasks and rebasing onto `<base-branch>`. Verify that Gate 4 (`audit_epic.py` + Blast-Radius `Integration results:` + `@quality_check` with `profile: "epic"`) already passed on `HEAD` (or verify `python3 scripts/resume_context.py --check-gate 4 --epic <epic_slug>`), then proceed directly to Step 2. The single full-repository **Level 3 `Test All`** run executes **once** in Step 5 (`Update onto Base`, Step 4 `verify-tier`) on the exact post-archival, post-rebase tree right before `integrate_branch.py land`.
    51	- **Standalone / Non-Epic Branch Mode**:
    52	  - Run the project's test suite (`npm test` / `cargo test` / `pytest` / `go test ./...`).
    53	  - **If tests fail**, report the failures and stop — the menu comes after a green suite:
    54	
    55	```text
    56	Tests failing (<N> failures). Must fix before completing:
    57	
    58	[Show failures]
    59	```
    60	
    61	**If verification passes:** continue to Step 2.
    62	
    63	## Step 2: Detect Environment
    64	
    65	```bash
    66	GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
    67	GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
    68	# Capture now, while still inside the workspace — Step 5 changes directory
    69	# before cleanup (Step 6) needs this value
    70	WORKTREE_PATH=$(git rev-parse --show-toplevel)
    71	```
    72	
    73	This determines which menu to show and how cleanup works:
    74	
    75	| State | Menu | Cleanup |
    76	|-------|------|---------|
    77	| `GIT_DIR == GIT_COMMON` (normal repo) | Standard 3 options | No worktree to clean up |
    78	| `GIT_DIR != GIT_COMMON`, named branch | Standard 3 options | Provenance-based (see Step 6) |
    79	| `GIT_DIR != GIT_COMMON`, detached HEAD | Reduced 2 options (no merge) | Externally managed — leave in place |
    80	
    81	## Step 3: Determine Base Branch
    82	
    83	The base branch is whatever this work forked from — usually named in the
    84	plan, the conversation, or the branch's upstream. If it is not already
    85	known, ask: "This branch split from <your best guess> - is that correct?"
    86	Confirm before merging: merging into the wrong base is expensive to undo.
    87	
    88	## Step 4: Present Options
    89	
    90	**Normal repo and named-branch worktree — present exactly these 3 options:**
    91	
    92	```text
    93	Implementation complete. What would you like to do?
    94	
    95	1. Merge back to <base-branch> locally
    96	2. Push and create a Pull Request
    97	3. Keep the branch as-is (I'll handle it later)
    98	
    99	Which option?
   100	```
   101	
   102	**Detached HEAD — present exactly these 2 options:**
   103	
   104	```text
   105	Implementation complete. You're on a detached HEAD (externally managed workspace).
   106	
   107	1. Push as new branch and create a Pull Request
   108	2. Keep as-is (I'll handle it later)
   109	
   110	Which option?
   111	```
   112	
   113	Present the menu exactly as written — concise, with every option coming
   114	from the list above. Discarding the work happens only in response to your
   115	human partner explicitly asking for it (see "If your human partner asks to
   116	discard the work" below). Wait for their answer; the integration decision
   117	is theirs.
   118	
   119	## Step 5: Execute Choice
   120	
   121	### Pre-Finish Hook: Epic Archival & Kanban Clean-up
   122	
   123	Before executing **Option 1 (Merge)** or **Option 2 (Push & PR)**, if the workspace contains completed tasks in `.devtool/features/done/`, archive them into their respective epic directory:
   124	
   125	```bash
   126	SYNC_SCRIPT="$SKILL_DIR/../dev-implementation/resources/scripts/sync_task_status.py"
   127	RESUME_SCRIPT="scripts/resume_context.py"
   128	if ls .devtool/features/done/task_*.md 1>/dev/null 2>&1; then
   129	  if [ ! -f "$SYNC_SCRIPT" ]; then
   130	    echo "STOP: done tasks exist but $SYNC_SCRIPT is missing" >&2
   131	  else
   132	    python3 "$SYNC_SCRIPT" archive-done
   133	    if [ -f "$RESUME_SCRIPT" ]; then
   134	      python3 "$RESUME_SCRIPT" --complete "<epic_slug>" "<milestone_summary>"
   135	    fi
   136	    git add .devtool/ docs/ 2>/dev/null || true
   137	    git commit -m "[EPIC] Complete epic and archive done tasks" -m "- archive done tasks into .devtool/epic/<epic_dir>
   138	- update epic status to Done across English and Vietnamese HLDs
   139	- clean up .devtool/features/done and docs/superpowers" 2>/dev/null || true
   140	  fi
   141	fi
   142	```
   143	
   144	If it prints `STOP`, report it to your human partner and do not continue: integrating without the
   145	archival leaves completed tasks stranded in `done/`.
   146	
   147	This guarantees:
   148	- Tasks remain visible in the **DONE** column on the Kanban dashboard throughout development and review.
   149	- Archival, link rewriting, and status transition to `Done` occur cleanly and are committed to the branch before it is merged or pushed to a PR.
   150	- If the user selects **Option 3 (Keep As-Is)**, tasks remain untouched in `.devtool/features/done/` so the developer can continue tracking them on the Kanban board.
   151	
   152	### Update onto Base (Options 1 and 2)
   153	
   154	Runs after the archival commit, from the branch's worktree (or the repository, for a normal repo).
   155	It brings in everything that landed on the base since this branch split off, resolves conflicts here
   156	on the branch, and re-verifies the result. Nothing touches the base branch during this section.
   157	
   158	Skip this section on a detached HEAD. When preflight warns that the branch `has already been
   159	pushed`, skip steps 2 and 3 and tell your human partner why: rebasing a pushed branch needs a
   160	force-push. Step 4 still runs and gives the candidate sha.
   161	
   162	1. **Preflight** — read-only:
   163	
   164	   ```bash
   165	   python3 "$INTEGRATE" preflight --base <base-branch>
   166	   ```
   167	
   168	   Show your human partner the upstream commits, the upstream epics and the predicted tier. If the
   169	   warnings say the base has diverged from its upstream, stop and ask. If a rebase is already in
   170	   progress (`predicted tier: rebase-in-progress`), continue or abort it; never start another. If the fetch failed, ask before landing.
   171	
   172	2. **Rebase:**
   173	
   174	   ```bash
   175	   python3 "$INTEGRATE" rebase --base <base-branch>
   176	   ```
   177	
   178	   On exit 2, resolve the listed conflicts with the
   179	   [conflict playbook](references/conflict-playbook.md), then run
   180	   `python3 "$INTEGRATE" rebase --continue --base <base-branch>` and repeat until it exits 0. Your
   181	   human partner may ask for `rebase --abort` at any point; it restores the branch to
   182	   `backup/<feature-branch>`. Any other non-zero exit — stop and report the output.
   183	
   184	3. **Re-bootstrap** the worktree when preflight reported `bootstrap required: True` (for d3nexus
   185	   mobile projects, the platform bootstrap in `dev-implementation` Phase 1 step 5), and regenerate
   186	   any `regenerate` files as the playbook describes.
   187	
   188	4. **Measure and verify:**
   189	
   190	   ```bash
   142	def execute_provider(
   143	    provider_item: dict[str, Any],
   144	    profile: str,
   145	    sha: str,
   146	    base_ref: str = "main",
   147	    repo_root: Path | None = None,
   148	) -> dict[str, Any]:
   149	    root = repo_root or Path.cwd()
   150	    p_id = provider_item.get("id", "")
   151	    skill = provider_item.get("skill", "")
   152	
   153	    actual_started_head = _get_git_head(root)
   154	    head_recorded = actual_started_head or sha
   155	
   156	    candidates = [
   157	        root / ".agents" / "quality" / f"{p_id}.json",
   158	    ]
   159	    platform = p_id.split("-")[0]
   160	    if platform:
   161	        candidates.append(root / ".agents" / "quality" / f"{platform}-quality.json")
   162	    for part in skill.split(":")[-1].split("-"):
   163	        if part and part not in ("quality", "check"):
   164	            candidates.append(root / ".agents" / "quality" / f"{part}-quality.json")
   165	
   166	    manifest_path = next((c for c in candidates if c and c.is_file()), None)
   167	    if not manifest_path:
   168	        return {
   169	            "provider_id": p_id,
   170	            "contract_version": 1,
   171	            "profile": profile,
   172	            "repository_sha": sha,
   173	            "status": "BLOCKED",
   174	            "required": provider_item.get("required", True),
   175	            "checks": [],
   176	            "coverage": {},
   177	            "evidence": [],
   178	            "started_head": head_recorded,
   179	            "finished_head": head_recorded,
   180	            "duration": 0.0,
   181	            "blockers": [f"Manifest file for provider '{p_id}' not found"],
   182	            "warnings": [],
   183	        }
   184	
   185	    try:
   186	        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
   187	    except (json.JSONDecodeError, OSError) as e:
   188	        return {
   189	            "provider_id": p_id,
   190	            "contract_version": 1,
   191	            "profile": profile,
   192	            "repository_sha": sha,
   193	            "status": "BLOCKED",
   194	            "required": provider_item.get("required", True),
   195	            "checks": [],
   196	            "coverage": {},
   197	            "evidence": [],
   198	            "started_head": head_recorded,
   199	            "finished_head": head_recorded,
   200	            "duration": 0.0,
   201	            "blockers": [f"Failed to parse manifest '{manifest_path}': {e}"],
   202	            "warnings": [],
   203	        }
   204	
   205	    skills_dir = Path(__file__).resolve().parents[3]
   206	
   207	    # Web provider execution: dispatch to web-quality runner
   208	    if "web" in p_id or "web" in skill:
   209	        try:
   210	            web_scripts = skills_dir / "web-quality-check" / "resources" / "scripts"
   211	            if str(web_scripts) not in sys.path:
   212	                sys.path.insert(0, str(web_scripts))
   213	            from validate_web_quality import run_capabilities
   214	
   215	            return run_capabilities(
   216	                config=manifest_data,
   217	                profile=profile,
   218	                repository_sha=sha,
   219	                repo_root=root,
   220	                provider_id=p_id,
   221	                base_ref=base_ref,
   222	                skills_dir=skills_dir,
   223	                check_watchdog_evidence=True,
   224	            )
   225	        except Exception as exc:  # noqa: BLE001
   226	            return {
   227	                "provider_id": p_id,
   228	                "contract_version": 1,
   229	                "profile": profile,
   230	                "repository_sha": sha,
   231	                "status": "FAIL",
   232	                "required": provider_item.get("required", True),
   233	                "checks": [],
   234	                "coverage": {},
   235	                "evidence": [],
   236	                "started_head": sha,
   237	                "finished_head": sha,
   238	                "duration": 0.0,
   239	                "blockers": [f"Error executing provider '{p_id}': {exc}"],
   240	                "warnings": [],
   241	            }
   242	
   243	    # Non-web provider execution: validate using platform validator if available
   244	    platform_name = None
   245	    for p in ("python", "android", "flutter", "ios", "rust"):
   246	        if p in p_id or p in skill:
   247	            platform_name = p
   248	            break
   249	
   250	    if platform_name:
   251	        p_scripts = (
   252	            skills_dir / f"{platform_name}-quality-check" / "resources" / "scripts"
   253	        )
   254	        if p_scripts.is_dir() and str(p_scripts) not in sys.path:
   255	            sys.path.insert(0, str(p_scripts))
   256	        try:
   257	            mod = importlib.import_module(f"validate_{platform_name}_quality")
   258	            val_fn = getattr(mod, f"validate_{platform_name}_config", None)
   259	            if val_fn:
   260	                v_res = val_fn(manifest_data, profile)
   350	                f"$ {' '.join(substituted_cmd)}\n\n--- STDOUT ---\n{proc.stdout}\n--- STDERR ---\n{proc.stderr}\n",
   351	                encoding="utf-8",
   352	            )
   353	            c_status = "PASS" if proc.returncode == 0 else "FAIL"
   354	            summary = (
   355	                f"{cap_name}: passed"
   356	                if c_status == "PASS"
   357	                else f"{cap_name}: failed with return code {proc.returncode}"
   358	            )
   359	        except OSError as exc:
   360	            cap_duration = round(time.time() - cap_start, 3)
   361	            c_status = "BLOCKED"
   362	            summary = f"{cap_name}: failed to execute: {exc}"
   363	
   364	        evidence_id = f"{cap_name}-evidence"
   365	        log_file = log_dir / f"{cap_name}.log"
   366	        rel_log_path = str(log_file.relative_to(root)) if log_file.is_file() else ""
   367	        checks.append(
   368	            {
   369	                "id": cap_name,
   370	                "category": "quality-check",
   371	                "status": c_status,
   372	                "source": " ".join(substituted_cmd),
   373	                "duration": cap_duration,
   374	                "summary": summary,
   375	                "evidence_refs": [evidence_id] if rel_log_path else [],
   376	            }
   377	        )
   378	        if rel_log_path:
   379	            evidence.append(
   380	                {
   381	                    "id": evidence_id,
   382	                    "type": "command",
   383	                    "source": " ".join(substituted_cmd),
   384	                    "location": rel_log_path,
   385	                }
   386	            )
   387	        if c_status == "FAIL":
   388	            overall_status = "FAIL"
   389	            blockers.append(
   390	                {
   391	                    "code": "capability_failed",
   392	                    "capability": cap_name,
   393	                    "message": summary,
   394	                }
   395	            )
   396	        elif c_status == "BLOCKED" and overall_status != "FAIL":
   397	            overall_status = "BLOCKED"
   398	            blockers.append(
   399	                {
   400	                    "code": "capability_blocked",
   401	                    "capability": cap_name,
   402	                    "message": summary,
   403	                }
   404	            )
   405	
   406	    actual_finished_head = _get_git_head(root)
   407	    if (
   408	        actual_started_head
   409	        and actual_finished_head
   410	        and actual_finished_head != actual_started_head
   411	    ):
   412	        overall_status = "FAIL"
   413	        blockers.append(
   414	            {
   415	                "code": "git_head_drift",
   416	                "message": f"Git HEAD changed during execution from '{actual_started_head}' to '{actual_finished_head}'",
   417	            }
   418	        )
   419	
   420	    started_head = actual_started_head or head_recorded
   421	    finished_head = actual_finished_head or head_recorded
   422	    total_duration = round(time.time() - start_time, 3)
   423	    return {
   424	        "provider_id": p_id,
   425	        "contract_version": 1,
   426	        "profile": profile,
   427	        "repository_sha": sha,
   428	        "status": overall_status,
   429	        "required": provider_item.get("required", True),
   430	        "checks": checks,
   431	        "coverage": {},
   432	        "evidence": evidence,
   433	        "started_head": started_head,
   434	        "finished_head": finished_head,
   435	        "duration": total_duration,
   436	        "blockers": blockers,
   437	        "warnings": [],
   438	    }
   535	        except OSError:
   536	            pass
   537	    return out_res
   538	
   539	
   540	def main(argv: list[str] | None = None) -> int:
   541	    parser = argparse.ArgumentParser(
   542	        description="Verify polyglot quality registry and multi-provider results."
   543	    )
   544	    parser.add_argument("registry_file", help="Path to check_quality.json")
   545	    parser.add_argument(
   546	        "--profile", default="epic", help="Quality profile (pr, epic, release)"
   547	    )
   548	    parser.add_argument(
   549	        "--sha", default="", help="Commit SHA (defaults to git rev-parse HEAD)"
   550	    )
   551	    parser.add_argument("--base-ref", default="main", help="Base reference for diffs")
   552	    parser.add_argument(
   553	        "--results", nargs="*", default=None, help="Paths to provider result JSON files"
   554	    )
   555	    parser.add_argument(
   556	        "--execute",
   557	        action="store_true",
   558	        help="Execute declared providers and aggregate live results",
   559	    )
   560	
   561	    args = parser.parse_args(argv)
   562	    reg_path = Path(args.registry_file).resolve()
   563	    repo_root = _resolve_repo_root(reg_path)
   564	    sha = args.sha
   565	    if not sha or sha == "0" * 40:
   566	        try:
   567	            head_out = subprocess.run(
   568	                ["git", "rev-parse", "HEAD"],
   569	                cwd=str(repo_root),
   570	                capture_output=True,
   571	                text=True,
   572	                check=False,
   573	            )
   574	            if head_out.returncode == 0:
   575	                sha = head_out.stdout.strip()
   576	        except (subprocess.SubprocessError, OSError):
   577	            pass
   578	    if not sha:
   579	        sha = "0" * 40
   580	
   581	    data = json.loads(reg_path.read_text(encoding="utf-8"))
   582	    provider_results: list[dict[str, Any]] = []
   583	
   584	    if args.results:
   585	        for r_file in args.results:
   586	            provider_results.append(
   587	                json.loads(Path(r_file).read_text(encoding="utf-8"))
   588	            )
   589	    elif args.execute or not args.results:
   590	        val_fn = _get_validator()
   591	        val = val_fn(data, args.profile)
   592	        if val["status"] != "BLOCKED":
   593	            workers = max(1, len(val["providers"]))
   594	            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
   595	                futures = [
   596	                    executor.submit(
   597	                        execute_provider,
   598	                        provider_item=plan_item,
   599	                        profile=args.profile,
   600	                        sha=sha,
   601	                        base_ref=args.base_ref,
   602	                        repo_root=repo_root,
   603	                    )
   604	                    for plan_item in val["providers"]
   605	                ]
   606	                provider_results = [f.result() for f in futures]
   607	
   608	    git_root = repo_root if (repo_root / ".git").exists() else None
   609	    res = fanout_and_aggregate(
   610	        registry_data=data,
   611	        requested_profile=args.profile,
   612	        repository_sha=sha,
   613	        base_ref=args.base_ref,
   614	        provider_results=provider_results,
   615	        repo_root=git_root,
   616	    )
   617	    print(json.dumps(res, indent=2))
   618	    return 0 if res["status"] == "PASS" else 1
   619	
   620	
   621	if __name__ == "__main__":
   622	    sys.exit(main())

 succeeded in 0ms:
    68	def init_slots(
    69	    root: Path,
    70	    epic_dir: str,
    71	    epic_slug: str,
    72	    pool_size: int = 2,
    73	    base_ref: str | None = None,
    74	) -> list[Path]:
    75	    """Create isolated worktrees for worker pool slots and link caches."""
    76	    main_wt = root / ".worktrees" / epic_dir
    77	    target_base = base_ref or f"epic/{epic_slug}"
    78	    created_paths: list[Path] = []
    79	
    80	    for slot in range(1, pool_size + 1):
    81	        slot_path = get_slot_path(root, epic_dir, slot)
    82	        slot_branch = get_slot_branch(epic_slug, slot)
    83	
    84	        if not slot_path.is_dir():
    85	            slot_path.parent.mkdir(parents=True, exist_ok=True)
    86	            # Check if branch already exists
    87	            res_branch = subprocess.run(
    88	                ["git", "rev-parse", "--verify", "--quiet", slot_branch],
    89	                cwd=root,
    90	                capture_output=True,
    91	                check=False,
    92	            )
    93	            if res_branch.returncode == 0:
    94	                cmd = ["git", "worktree", "add", str(slot_path), slot_branch]
    95	            else:
    96	                cmd = ["git", "worktree", "add", str(slot_path), "-b", slot_branch, target_base]
    97	
    98	            subprocess.run(cmd, cwd=root, check=True, capture_output=True)
    99	
   100	        # Link caches from main worktree
   101	        if main_wt.is_dir():
   102	            link_shared_caches(main_wt, slot_path)
   103	
   104	        created_paths.append(slot_path)
   105	
   106	    return created_paths
   107	
   108	
   109	def sync_slot(root: Path, epic_dir: str, epic_slug: str, slot: int) -> bool:
   110	    """Reset slot worktree to the latest HEAD of the epic branch."""
   111	    slot_path = get_slot_path(root, epic_dir, slot)
   112	    if not slot_path.is_dir():
   113	        return False
   114	
   115	    epic_branch = f"epic/{epic_slug}"
   116	    # Fetch local branch state and reset slot working copy
   117	    subprocess.run(["git", "fetch", ".", f"{epic_branch}:{epic_branch}"], cwd=slot_path, capture_output=True, check=False)
   118	    res = subprocess.run(["git", "reset", "--hard", epic_branch], cwd=slot_path, capture_output=True, check=False)
   119	    return res.returncode == 0
   120	
   121	
   122	def merge_slot(root: Path, epic_dir: str, epic_slug: str, slot: int, task_id: str | None = None) -> bool:
   123	    """Merge slot's commit back into the main epic worktree branch."""
   124	    main_wt = root / ".worktrees" / epic_dir
   125	    if not main_wt.is_dir():
   126	        return False
   127	
   128	    slot_branch = get_slot_branch(epic_slug, slot)
   129	    # Merge slot branch into main worktree
   130	    res = subprocess.run(["git", "merge", "--ff-only", slot_branch], cwd=main_wt, capture_output=True, check=False)
   131	    if res.returncode != 0:
   132	        # Fallback to standard merge with clear message if non-ff
   133	        msg = f"Merge slot {slot}" + (f" for {task_id}" if task_id else "")
   134	        res = subprocess.run(["git", "merge", "--no-ff", "-m", msg, slot_branch], cwd=main_wt, capture_output=True, check=False)
   135	
   136	    return res.returncode == 0
   137	
   138	
   139	def cleanup_slots(root: Path, epic_dir: str, epic_slug: str, pool_size: int = 2) -> bool:
   140	    """Prune and remove all slot worktrees and temporary branches."""
   141	    for slot in range(1, pool_size + 1):
   142	        slot_path = get_slot_path(root, epic_dir, slot)
   143	        slot_branch = get_slot_branch(epic_slug, slot)
   144	
   145	        if slot_path.is_dir():
   146	            subprocess.run(["git", "worktree", "remove", "--force", str(slot_path)], cwd=root, capture_output=True, check=False)
   147	
   148	        subprocess.run(["git", "branch", "-D", slot_branch], cwd=root, capture_output=True, check=False)
   149	
   150	    subprocess.run(["git", "worktree", "prune"], cwd=root, capture_output=True, check=False)
   151	    return True
   152	
   153	
   154	def get_pool_status(root: Path, epic_dir: str, pool_size: int = 2) -> dict[int, dict[str, Any]]:
   155	    """Inspect presence, branch, and status of worker pool slots."""
   156	    status: dict[int, dict[str, Any]] = {}
   157	    for slot in range(1, pool_size + 1):
   158	        slot_path = get_slot_path(root, epic_dir, slot)
   159	        slot_branch = get_slot_branch(epic_slug=epic_dir, slot=slot)
   160	        exists = slot_path.is_dir()
   161	        head = None
   162	        dirty = False
   163	        if exists:
   164	            h_res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=slot_path, capture_output=True, text=True, check=False)
   165	            if h_res.returncode == 0:
   166	                head = h_res.stdout.strip()
   167	            s_res = subprocess.run(["git", "status", "--porcelain"], cwd=slot_path, capture_output=True, text=True, check=False)
   168	            if s_res.returncode == 0 and s_res.stdout.strip():
    20	It also prints a scan summary (how many `task_*.md` files were seen, how
    21	many matched the epic, how many were skipped) so a task file with broken
    22	or missing frontmatter is never silently dropped.
    23	"""
    24	from __future__ import annotations
    25	import argparse
    26	import json
    27	import re
    28	import sys
    29	from pathlib import Path
    30	
    31	sys.path.insert(0, str(Path(__file__).parent))
    32	from slug_utils import parse_frontmatter, sanitize_slug
    33	
    34	PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
    35	# Soft-note markers: keyword list used to surface advisory content that isn't a hard blocker.
    36	# These are small, documented keywords — not a general sentence parser. Phase 0 (full task text)
    37	# in the operating skill is the actual safety net for anything these markers miss.
    38	SOFT_NOTE_MARKERS = ("Recommended", "New dependency")
    39	FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
    40	SECTION_RE = re.compile(r"##\s*Dependencies\s*(?:&|and)\s*Blockers\s*\n(.*?)(\n##|\Z)", re.DOTALL)
    41	FILES_SECTION_RE = re.compile(r"##\s*Files\s*\n(.*?)(\n##|\Z)", re.DOTALL)
    42	ALLOWED_BULLET_RE = re.compile(r"^\s*-\s*`([^`]+)`(?:\s*\(new\))?\s*$")
    43	LINK_RE = re.compile(r"\]\(([^)]+\.md)\)")
    44	TITLE_RE = re.compile(r"^#\s*Task\s*\d+:\s*(.+)$", re.MULTILINE)
    45	NUMBER_RE = re.compile(r"\d+")
    46	
    47	
    48	def parse_dependencies_section(text: str) -> str:
    49	    match = SECTION_RE.search(text)
    50	    return match.group(1) if match else ""
    51	
    52	
    53	def parse_allowed_files(text: str) -> list[str]:
    54	    """Extract paths listed under the 'Allowed files:' block in the task markdown."""
    55	    match = FILES_SECTION_RE.search(text)
    56	    body = match.group(1) if match else text
    57	    allowed: list[str] = []
    58	    in_allowed = False
    59	    for line in body.splitlines():
    60	        trimmed = line.strip()
    61	        if trimmed == "Allowed files:":
    62	            in_allowed = True
    63	            continue
    64	        if in_allowed:
    65	            bullet = ALLOWED_BULLET_RE.match(line)
    66	            if bullet:
    67	                allowed.append(bullet.group(1))
    68	            elif trimmed.startswith("- `"):
    69	                # Fallback pattern
    70	                start = trimmed.find("`") + 1
    71	                end = trimmed.find("`", start)
    72	                if end != -1:
    73	                    allowed.append(trimmed[start:end])
    74	            elif trimmed and not trimmed.startswith("-"):
    75	                break
    76	    return allowed
    77	
    78	
    79	def parse_blockers(section: str) -> list[str]:
    80	    blockers = []
    81	    for line in section.splitlines():
    82	        if "Blocked by" not in line:
    83	            continue
    84	        blockers.extend(Path(link).stem for link in LINK_RE.findall(line))
    85	    return blockers
    86	
    87	
    88	def parse_soft_notes(section: str) -> list[str]:
    89	    return [line.strip().lstrip("-").strip() for line in section.splitlines()
    90	            if any(marker in line for marker in SOFT_NOTE_MARKERS)]
    91	
    92	
    93	def extract_title(text: str) -> str:
    94	    match = TITLE_RE.search(text)
    95	    return match.group(1).strip() if match else "Untitled"
    96	
    97	
    98	def scan_tasks(features_dir: Path, epic: str) -> tuple[dict[str, dict], list[Path], list[Path]]:
    99	    """Load the epic's tasks AND report what was skipped.
   100	
   101	    Returns (tasks, scanned_paths, skipped_paths). A file lands in
   102	    `skipped_paths` when its frontmatter is missing/unparseable (so
   103	    `epic:` reads as None) or names a different epic -- both look
   104	    identical from the graph's point of view, which is exactly why the
   105	    CLI reports the count instead of dropping them silently.
   106	    """
   107	    tasks: dict[str, dict] = {}
   108	    scanned: list[Path] = []
   109	    skipped: list[Path] = []
   110	    target_epic = sanitize_slug(epic)
   111	    candidate_paths = list(Path(features_dir).glob("task_*.md"))
   112	    done_dir = Path(features_dir) / "done"
   113	    if done_dir.is_dir():
   114	        candidate_paths.extend(done_dir.glob("task_*.md"))
   115	    for path in sorted(candidate_paths):
   175	
   176	def compute_parallel_batches(
   177	    layers: list[list[str]], tasks: dict[str, dict], pool_size: int = 2
   178	) -> list[list[list[str]]]:
   179	    """Group tasks within each topological layer into parallel execution batches.
   180	
   181	    Tasks within the same layer have no dependencies, but if two tasks modify
   182	    the same file (shared entry in 'allowed_files'), they are separated into
   183	    subsequent batches to prevent Git / build workspace collision.
   184	    Each batch contains at most pool_size tasks.
   185	    """
   186	    def sort_key(task_id: str) -> tuple:
   187	        task = tasks.get(task_id, {})
   188	        number_match = NUMBER_RE.search(task_id)
   189	        number = int(number_match.group()) if number_match else 0
   190	        return (PRIORITY_RANK.get(task.get("priority", "medium"), 1), number)
   191	
   192	    all_layer_batches: list[list[list[str]]] = []
   193	    for layer in layers:
   194	        sorted_layer = sorted(layer, key=sort_key)
   195	        layer_batches: list[list[str]] = []
   196	        for task_id in sorted_layer:
   197	            task = tasks.get(task_id, {})
   198	            task_files = set(task.get("allowed_files", []))
   199	            placed = False
   200	            for batch in layer_batches:
   201	                if len(batch) >= pool_size:
   202	                    continue
   203	                # Check collision with other tasks in this candidate batch
   204	                has_conflict = False
   205	                for other_id in batch:
   206	                    other_task = tasks.get(other_id, {})
   207	                    other_files = set(other_task.get("allowed_files", []))
   208	                    if task_files and other_files and bool(task_files & other_files):
   209	                        has_conflict = True
   210	                        break
   211	                if not has_conflict:
   212	                    batch.append(task_id)
   213	                    placed = True
   214	                    break
   215	            if not placed:
   216	                layer_batches.append([task_id])
   217	        all_layer_batches.append(layer_batches)
   218	    return all_layer_batches
   511	    def _has_domain_or_critical_conflict(self, text: str) -> bool:
   512	        """Check if review triage indicates critical risks or business/domain conflicts."""
   513	        markers = [
   514	            "domain conflict",
   515	            "business requirement conflict",
   516	            "critical risk",
   517	            "shared_contract_conflict",
   518	            "conflict with shared-contracts",
   519	        ]
   520	        low = text.lower()
   521	        return any(m in low for m in markers)
   522	
   523	    def _apply_minor_fixes(self, round_num: int) -> bool:
   524	        """Apply minor review revisions and commit changes."""
   525	        prompt = (
   526	            f"You are the AI Assistant (Role 2.2). Apply minor revisions for Principal Review round {round_num}.\n"
   527	            f"Update the architectural specifications in .devtool/epic/{self.epic_slug}/ to address all minor review findings.\n"
   528	        )
   529	        self.dispatcher.dispatch(
   530	            cli="agy",
   531	            args=["--model", self.config.resolve_assistant_model(self.root), "--effort", self.config.assistant_effort, "--mode", "accept-edits"],
   532	            prompt=prompt,
   533	        )
   534	        # 1. Commit technical revision edits first
   535	        status_res = subprocess.run(
   536	            ["git", "status", "--porcelain"],
   537	            cwd=self.root,
   538	            capture_output=True,
   539	            text=True,
   540	            check=False,
   541	        )
   542	        if status_res.returncode == 0 and status_res.stdout.strip():
   543	            subprocess.run(["git", "add", "-A"], cwd=self.root, check=False)
   544	            commit_title = f"[{self.epic_slug.upper()}] Apply minor Principal Review revisions round {round_num}"
   545	            subprocess.run(
   546	                ["git", "commit", "-m", commit_title],
   547	                cwd=self.root,
   548	                capture_output=True,
   549	                check=False,
   550	            )
   551	
   552	        # 2. Record decision cells citing the fix commit SHA
   553	        rev_res = subprocess.run(
   554	            ["git", "rev-parse", "HEAD"],
   555	            cwd=self.root,
   556	            capture_output=True,
   557	            text=True,
   558	            check=False,
   559	        )
   560	        sha_short = rev_res.stdout.strip()[:7] if rev_res.returncode == 0 else "unknown"
   561	
   562	        file = self.root / ".devtool" / "epic" / self.epic_slug / "principal_review.md"
   563	        if file.is_file():
   564	            content = file.read_text(encoding="utf-8")
   565	            lines = content.splitlines()
   566	            in_target_round = False
   567	            in_raw_output = False
   568	            new_lines = []
   569	            for line in lines:
   570	                if line.startswith(f"## Round {round_num}"):
   571	                    in_target_round = True
   572	                elif line.startswith("## Round "):
   573	                    in_target_round = False
   574	                if in_target_round:
   575	                    if line.startswith("Raw output:"):
   576	                        in_raw_output = True
   577	                    if not in_raw_output and re.match(r"^\|\s*\d+\s*\|", line):
   578	                        parts = line.split("|")
   579	                        if len(parts) >= 6:
   580	                            current_dec = parts[-2].strip()
   581	                            if not current_dec.startswith(("fixed in ", "dismissed: ")):
   582	                                parts[-2] = f" fixed in {sha_short} "
   583	                                line = "|".join(parts)
   584	                new_lines.append(line)
   585	            file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
   586	
   587	        # 3. Commit review decisions separately
   588	        dec_status = subprocess.run(
   589	            ["git", "status", "--porcelain"],
   590	            cwd=self.root,
   591	            capture_output=True,
   592	            text=True,
   593	            check=False,
   594	        )
   595	        if dec_status.returncode == 0 and dec_status.stdout.strip():
   596	            subprocess.run(["git", "add", str(file)], cwd=self.root, check=False)
   597	            commit_title = f"[{self.epic_slug.upper()}] Record Principal Review decisions for round {round_num}"
   598	            subprocess.run(
   599	                ["git", "commit", "-m", commit_title],
   600	                cwd=self.root,
   601	                capture_output=True,
   602	                check=False,
   603	            )
   604	        return True
   605	
   606	    def _apply_aligned_fixes(self, round_num: int) -> bool:
   607	        """Apply aligned technical revisions and commit changes."""
   608	        prompt = (
   609	            f"You are the AI Assistant (Role 2.2). Apply aligned technical revisions for Principal Review round {round_num}.\n"
   610	            f"Update the architectural specifications in .devtool/epic/{self.epic_slug}/ to align with verified findings.\n"
   611	        )
   612	        self.dispatcher.dispatch(
   613	            cli="agy",
   614	            args=["--model", self.config.resolve_assistant_model(self.root), "--effort", self.config.assistant_effort, "--mode", "accept-edits"],
   615	            prompt=prompt,
   616	        )
   617	        # 1. Commit aligned revision edits first
   618	        status_res = subprocess.run(
   619	            ["git", "status", "--porcelain"],
   620	            cwd=self.root,
  1100	
  1101	    def _apply_code_fixes(self, round_num: int, plan_text: str = "") -> bool:
  1102	        """Apply code fixes according to the approved or adjusted fix plan and commit."""
  1103	        prompt = (
  1104	            f"You are the AI Programmer (Role 2.3). Implement the code fixes for Cross-Model Review Round {round_num}.\n"
  1105	            f"Approved Fix Plan:\n\n{plan_text}\n\n"
  1106	            f"Apply the changes, verify tests pass, and adhere to strict TDD.\n"
  1107	        )
  1108	        self.dispatcher.dispatch(
  1109	            cli="agy",
  1110	            args=["--model", self.config.programmer_model, "--effort", self.config.programmer_effort, "--mode", "accept-edits"],
  1111	            prompt=prompt,
  1112	        )
  1113	        status_res = subprocess.run(
  1114	            ["git", "status", "--porcelain"],
  1115	            cwd=self.root,
  1116	            capture_output=True,
  1117	            text=True,
  1118	            check=False,
  1119	        )
  1120	        if status_res.returncode == 0 and status_res.stdout.strip():
  1121	            subprocess.run(["git", "add", "-A"], cwd=self.root, check=False)
  1122	            commit_title = f"[{self.epic_slug.upper()}] Apply code fixes for Cross-Model Review round {round_num}"
  1123	            subprocess.run(
  1124	                ["git", "commit", "-m", commit_title],
  1125	                cwd=self.root,
  1126	                capture_output=True,
  1127	                check=False,
  1128	            )
  1129	        return True
  1130	
  1131	    def _record_review_decisions(self, round_num: int) -> bool:
  1132	        """Record review decision cells and commit decisions."""
  1133	        file = self.root / ".devtool" / "epic" / self.epic_slug / "review_results.md"
  1134	        if file.is_file():
  1135	            content = file.read_text(encoding="utf-8")
  1136	            rev_res = subprocess.run(
  1137	                ["git", "rev-parse", "HEAD"],
  1138	                cwd=self.root,
  1139	                capture_output=True,
  1140	                text=True,
  1141	                check=False,
  1142	            )
  1143	            sha_short = rev_res.stdout.strip()[:7] if rev_res.returncode == 0 else "unknown"
  1144	            lines = content.splitlines()
  1145	            in_target_round = False
  1146	            in_raw_output = False
  1147	            new_lines = []
  1148	            for line in lines:
  1149	                if line.startswith(f"## Round {round_num}"):
  1150	                    in_target_round = True
  1151	                elif line.startswith("## Round "):
  1152	                    in_target_round = False
  1153	                if in_target_round:
  1154	                    if line.startswith("Raw output:"):
  1155	                        in_raw_output = True
  1156	                    if not in_raw_output and re.match(r"^\|\s*\d+\s*\|", line):
  1157	                        parts = line.split("|")
  1158	                        if len(parts) >= 6:
  1159	                            current_dec = parts[-2].strip()
  1160	                            if not current_dec.startswith(("fixed in ", "dismissed: ")):
  1161	                                parts[-2] = f" fixed in {sha_short} "
  1162	                                line = "|".join(parts)
  1163	                new_lines.append(line)
  1164	            file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
  1165	
  1166	        status_res = subprocess.run(
  1167	            ["git", "status", "--porcelain"],
  1168	            cwd=self.root,
  1169	            capture_output=True,
  1170	            text=True,
  1171	            check=False,
  1172	        )
  1173	        if status_res.returncode == 0 and status_res.stdout.strip():
  1174	            subprocess.run(["git", "add", "-A"], cwd=self.root, check=False)
  1175	            commit_title = f"[{self.epic_slug.upper()}] Record review decisions for round {round_num}"
  1176	            subprocess.run(
  1177	                ["git", "commit", "-m", commit_title],
  1178	                cwd=self.root,
  1179	                capture_output=True,
  1180	                check=False,
  1181	            )
  1182	        return True
  1183	
     1	#!/usr/bin/env bash
     2	# Pre-release checks for the agent kit. Run before publishing — a broken skill
     3	# propagates to every project on every machine that has the plugin installed.
     4	# Usage:
     5	#   bash scripts/verify.sh          # Fast parallel check + smart 2-tier content-hash cache
     6	#   bash scripts/verify.sh --full   # Force full re-run of all Python unit & pytest suites
     7	set -uo pipefail
     8	
     9	FORCE_FULL=0
    10	if [ "${1:-}" = "--full" ]; then
    11	  FORCE_FULL=1
    12	fi
    13	
    14	KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    15	cd "$KIT_DIR"
    16	FAILED=0
    17	note() { printf '%s\n' "$1"; }
    18	fail() { printf '  FAIL %s\n' "$1"; FAILED=1; }
    19	
    20	note "== 1. JSON manifests parse & 1b. Runtime versions and Codex marketplace agree =="
    21	python3 - <<'PY' || FAILED=1
    22	import json, pathlib, re, sys
    23	
    24	MANIFEST_PATHS = (
    25	    "plugin.json",
    26	    ".claude-plugin/plugin.json",
    27	    ".codex-plugin/plugin.json",
    28	    ".claude-plugin/marketplace.json",
    29	    ".agents/plugins/marketplace.json",
    30	)
    31	parsed = {}
    32	for p in MANIFEST_PATHS:
    33	    try:
    34	        parsed[p] = json.loads(pathlib.Path(p).read_text())
    35	        print(f"  ok   {p}")
    36	    except Exception as exc:
    37	        print(f"  FAIL {p} is not valid JSON: {exc}")
    38	        sys.exit(1)
    39	
    40	try:
    41	    manifests = [parsed[p] for p in ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json")]
    42	    claude = parsed[".claude-plugin/marketplace.json"]
    43	    catalog = parsed[".agents/plugins/marketplace.json"]
    44	    entry, = [p for p in catalog["plugins"] if p["name"] == "d3nexus"]
    45	    claude_entry, = [p for p in claude["plugins"] if p["name"] == "d3nexus"]
    46	    versions = {m["version"] for m in manifests} | {claude_entry["version"]}
    47	    assert all(m["name"] == "d3nexus" for m in manifests), "plugin names must agree"
    48	    assert len(versions) == 1, f"release versions differ: {sorted(versions)}"
    49	    version, = versions
    50	    assert re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version), "invalid release version"
    51	    assert re.search(r'^## ' + re.escape(version) + r' — \d{4}-\d{2}-\d{2}\n\n\S',
    52	                     pathlib.Path("CHANGELOG.md").read_text(), re.M), "missing dated release notes"
    53	    assert catalog["name"] == claude["name"] == "danhdue-agent-tools", "marketplace names differ"
    54	    assert entry["source"] == {"source": "local", "path": "./"}, "marketplace must load the repo root"
    55	    assert entry["policy"] == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "invalid policy"
    56	    assert entry["category"] == "Developer Tools", "missing marketplace category"
    57	    codex = manifests[2]
    58	    assert codex["skills"] == "./skills/" and pathlib.Path(codex["skills"]).is_dir(), "missing shared skills"
    59	    assert not ({"apps", "mcpServers", "hooks"} & codex.keys()), "unexpected Codex components"
    60	    for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
    61	        assert codex["interface"][field].strip(), f"missing Codex interface.{field}"
    62	    print(f"  ok   d3nexus {version}, shared skills, and repo marketplace")
    63	except (AssertionError, KeyError, ValueError, OSError, TypeError) as error:
    64	    print(f"  FAIL {error}")
    65	    sys.exit(1)
   125	            heads.append(anchor(re.sub(r'^#+ ', '', ln).rstrip()))
   126	    for link in re.findall(r'\]\((#[^)]+)\)', s):
   127	        if link.lower() not in heads:
   128	            print(f"  FAIL {p} -> {link}"); bad = 1
   129	sys.exit(bad)
   130	PY
   131	
   132	note "== 5. No stale cross-namespace references =="
   133	if grep -rq "superpowers:" skills rules 2>/dev/null; then
   134	  grep -rn "superpowers:" skills rules | head -5
   135	  fail "skills still reference the superpowers namespace"
   136	else
   137	  note "  ok   none"
   138	fi
   139	
   140	note "== 5b. Rule files start with frontmatter =="
   141	for f in rules/*.md; do
   142	  if head -1 "$f" | grep -qx -- '---'; then
   143	    note "  ok   $f"
   144	  else
   145	    fail "$f has no frontmatter — Antigravity will refuse to load it"
   146	  fi
   147	done
   148	
   149	note "== 6. Session-start hook emits valid JSON for both runtimes =="
   150	hook_case() {
   151	  local label="$1" expect="$2" env="$3" payload="$4" out
   152	  out=$(printf '%s' "$payload" | env $env bash hooks/session-start 2>/dev/null) || {
   153	    fail "hook exited non-zero: $label"; return; }
   154	  printf '%s' "$out" | python3 -c "
   155	import json,sys
   156	d=json.load(sys.stdin)
   157	got='inject' if ('hookSpecificOutput' in d or 'injectSteps' in d) else ('silent' if d=={} else 'other')
   158	sys.exit(0 if got=='$expect' else 1)
   159	" 2>/dev/null && note "  ok   $label" || fail "$label — expected $expect"
   160	}
   161	hook_case "Claude Code SessionStart"        inject "CLAUDE_PLUGIN_ROOT=$KIT_DIR" '{}'
   162	hook_case "Antigravity first invocation"    inject "X=1" '{"invocationNum":0}'
   163	hook_case "Antigravity second invocation"   silent "X=1" '{"invocationNum":1}'
   164	hook_case "Antigravity later invocation"    silent "X=1" '{"invocationNum":7}'
   165	hook_case "Antigravity unreadable payload"  silent "X=1" 'not json'
   166	
   167	note "== 7. Methodology skills stay faithful to their sources =="
   168	python3 scripts/check_source_fidelity.py || FAILED=1
   169	
   170	note "== 8. Every supporting skill file is referenced by something =="
   171	# Driven from `git ls-files` instead of `rglob("*")` so untracked caches, .venv, and .devtool
   172	# archives never pollute or slow down the scan.
   173	python3 - <<'PY' || FAILED=1
   174	import pathlib, subprocess, sys
   175	
   176	ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".pdf"}
   177	LEGAL_PREFIXES = ("LICENSE", "COPYING", "NOTICE")
   178	TEXT_SUFFIXES = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ""}
   179	
   180	def is_skill_content(p: pathlib.Path) -> bool:
   181	    if p.name == "SKILL.md" or "__pycache__" in p.parts:
   182	        return False
   183	    if p.suffix.lower() in ASSET_SUFFIXES:
   184	        return False
   185	    if p.name.upper().startswith(LEGAL_PREFIXES):
   186	        return False
   187	    return not any(part.startswith(".") for part in p.parts)
   188	
   189	tracked = [
   190	    pathlib.Path(line)
   295	import sys
   296	import time
   297	
   298	run_mode = os.environ.get("VerifyRunMode", "full")
   299	
   300	# Tuple format: (section, mode, path_or_label, priority_weight, affects_doc_only)
   301	# Higher priority_weight is scheduled first in the worker pool (Longest-Job-First)
   302	# while output is still printed in canonical SUITES order.
   303	SUITES = [
   304	    # Section 11: Lifecycle document contracts & implementation engines
   305	    ("11", "unittest", "skills/doc_quality_check/resources/scripts/test_check_document.py", 1, True),
   306	    ("11", "script",   "scripts/test_lifecycle_document_contract.py", 2, True),
   307	    ("11", "unittest", "scripts/test_lifecycle_signals.py", 2, True),
   308	    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_audit_epic.py", 50, False),
   309	    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py", 3, False),
   310	    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_check_epic_readiness.py", 45, False),
   311	    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_check_task_contract.py", 35, False),
   312	    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_result_reports.py", 1, False),
   313	    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_run_external_review.py", 100, False),
   314	    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_local_review.py", 95, False),
   315	    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_run_task_checks.py", 60, False),
   316	    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_sync_task_status.py", 40, False),
   317	    ("11", "pytest",   "skills/dev-implementation/resources/scripts/test_inter_epic_dependencies.py", 10, False),
   318	    ("11", "pytest",   "skills/dev-implementation/resources/scripts/test_concurrent_epic_backlog.py", 10, False),
   319	    ("11", "pytest",   "skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py", 30, False),
   320	    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_compute_execution_order.py", 5, False),
   321	    ("11", "pytest",   "skills/dev-implementation/resources/scripts/test_manage_worker_pool.py", 1, False),
   322	    ("11", "pytest",   "skills/dev-implementation/resources/scripts/test_failure_baseline.py", 5, False),
   323	    ("11", "pytest",   "skills/dev-implementation/resources/scripts/test_replay_and_measure.py", 15, False),
   324	    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_slug_utils.py", 2, False),
   325	    ("11", "unittest", "skills/impact-analysis/resources/scripts/test_check_code_impact.py", 5, False),
   326	    ("11", "unittest", "scripts/test_run_unittest_junit.py", 2, False),
   327	    ("11", "unittest", "scripts/test_verifiable_handoff_text.py", 1, True),
   328	    ("11", "unittest", "scripts/test_verifiable_handoff.py", 15, True),
   329	    ("11", "unittest", "tests/test_lifecycle_runner.py", 20, False),
   330	    # Section 12: Branch integration script
   331	    ("12", "unittest", "skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py", 80, False),
   332	    # Section 13: Quality provider contracts, schemas, aggregation, and platform capabilities
   333	    ("13", "unittest", "skills/quality_check/resources/scripts/test_validate_quality_contract.py", 1, False),
   334	    ("13", "unittest", "skills/quality_check/resources/scripts/test_aggregate_quality_results.py", 1, False),
   335	    ("13", "unittest", "skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py", 1, False),
   336	    ("13", "unittest", "skills/python-quality-check/resources/scripts/test_validate_python_quality.py", 1, False),
   337	    ("13", "unittest", "skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py", 1, False),
   338	    ("13", "unittest", "skills/android-quality-check/resources/scripts/test_validate_android_quality.py", 1, False),
   339	    ("13", "unittest", "skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py", 1, False),
   340	    ("13", "unittest", "skills/web-quality-check/resources/scripts/test_validate_web_quality.py", 1, False),
   341	    ("13", "pytest",   "tests/test_web_quality_provider.py", 5, False),
   342	    ("13", "pytest",   "tests/test_audit_ui_state_and_styles.py", 2, False),
   343	    ("13", "unittest", "skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py", 1, False),
   344	    ("13", "unittest", "skills/quality_check/resources/scripts/test_quality_provider_acceptance.py", 20, True),
   345	    # 14. Shared contracts CLI engine is enforced
   346	    ("14", "unittest", "skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py", 15, False),
   347	    ("14", "unittest", "skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py", 25, False),
   348	    # 15. Context memory management CLI and Tri-Role governance are enforced
   349	    ("15", "unittest", "scripts/test_resume_context.py", 25, False),
   350	    # 16. Session refresh CLI engine and isolation contracts are enforced
   351	    ("16", "unittest", "skills/refresh-session/resources/scripts/test_refresh_session.py", 2, False),
   352	    # 17. Quota Dashboard & Kiro CLI provider tests
   353	    ("17", "unittest", "tests/test_kiro_quota.py", 2, True),
   354	    ("17", "unittest", "tests/test_agy_quota.py", 2, True),
   355	]
   356	
   357	active_suites = [
   358	    (idx, s)
   359	    for idx, s in enumerate(SUITES)
   360	    if pathlib.Path(s[2]).exists() and (run_mode == "full" or s[4])
   361	]
   362	
   363	# Schedule heaviest suites first (Longest-Job-First)
   364	scheduled_suites = sorted(active_suites, key=lambda item: -item[1][3])
   365	
   366	def run_suite(indexed_item):
   367	    orig_idx, (sec, mode, path, _prio, _doc) = indexed_item
   368	    t0 = time.monotonic()
   369	    if mode == "unittest":
   370	        cmd = [sys.executable, "-m", "unittest", path]
   371	    elif mode == "pytest":
   372	        cmd = [sys.executable, "-m", "pytest", path, "-q"]
   373	    else:
   374	        cmd = [sys.executable, path]
   375	    proc = subprocess.run(cmd, capture_output=True, text=True)
   376	    elapsed = time.monotonic() - t0
   377	    return orig_idx, sec, path, proc.returncode, elapsed, proc.stdout, proc.stderr
   378	
   379	t_start = time.monotonic()
   380	max_workers = min(len(scheduled_suites), (os.cpu_count() or 4))
   381	raw_results = []
   382	with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
   383	    futures = [pool.submit(run_suite, item) for item in scheduled_suites]
   384	    for fut in concurrent.futures.as_completed(futures):
   385	        raw_results.append(fut.result())
   386	
   387	# Sort back to canonical Section 11 -> 16 order for deterministic output
   388	results = sorted(raw_results, key=lambda r: r[0])
   389	
   390	failed = 0
   391	for _idx, sec, path, rc, elapsed, out, err in results:
   392	    status = "ok  " if rc == 0 else "FAIL"
   393	    print(f"  {status} [§{sec}] {path} ({elapsed:.2f}s)")
   394	    if rc != 0:
   395	        failed = 1
   396	        if out.strip():
   397	            print(out.rstrip())
   398	        if err.strip():
   399	            print(err.rstrip())
   400	
   401	total_elapsed = time.monotonic() - t_start
   402	print(f"\n  Ran {len(results)} test suites in {total_elapsed:.2f}s across {max_workers} workers.")
   403	sys.exit(failed)
   404	PY
   405	
   406	  if [ "$FAILED" -eq 0 ] && [ -n "$GIT_DIR_PATH" ]; then
   407	    printf '%s:%s\n' "$FULL_HASH" "$CODE_HASH" > "$CACHE_FILE"
   408	  fi
   409	fi
   410	
   411	echo
   412	if [ "$FAILED" -eq 0 ]; then
   413	  echo "PASS — safe to publish"
   414	else
   415	  echo "FAILED — fix the above before publishing"
   416	fi
   417	exit "$FAILED"

exec
/bin/zsh -lc "rg -n 'require-bilingual|bilingual|check_document|bdd_scenarios|review_tier|Gemini Flash 3.8|gemini-3.8-flash' skills/finishing-a-development-branch/resources/scripts/{integrate_branch.py,test_integrate_branch.py} skills/dev-implementation/resources/scripts/{task_contract.py,check_task_contract.py,audit_epic.py} scripts/{test_lifecycle_document_contract.py,test_resume_context.py,test_verifiable_handoff_text.py} skills/subagent-driven-development/{implementer-prompt.md,SKILL.md} skills/dev-lifecycle/references/stage-3-implementation.md; nl -ba skills/dev-implementation/resources/scripts/run_external_review.py | sed -n '1120,1188p;1380,1527p'; nl -ba skills/dev-lifecycle/resources/scripts/lifecycle_runner.py | sed -n '1100,1138p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
exec
/bin/zsh -lc "nl -ba skills/finishing-a-development-branch/SKILL.md | sed -n '106,177p'; nl -ba skills/doc_quality_check/resources/scripts/check_document.py | sed -n '330,425p'; nl -ba .agents/quality/python-quality.json; type -a python3 mypy ruff git; rg -n 'unittest|__main__|main\\(|verify.sh' tests/test_lifecycle_runner.py tests/test_polyglot_gate4.py scripts/check_source_fidelity.py" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
rg: skills/dev-lifecycle/references/stage-3-implementation.md: No such file or directory (os error 2)
skills/dev-implementation/resources/scripts/check_task_contract.py:454:    for bdd_path in sorted(hld_path.parent.glob("bdd_scenarios*.md")):
skills/dev-implementation/resources/scripts/check_task_contract.py:464:    bdd_path = hld_path.parent / "bdd_scenarios.en.md"
skills/dev-implementation/resources/scripts/check_task_contract.py:485:                        check.problem(f"{stem}:BDD", f"scenario {cid} differs from bdd_scenarios.en.md (R3)")
scripts/test_lifecycle_document_contract.py:17:        "--require-bilingual",
scripts/test_lifecycle_document_contract.py:27:        "--require-bilingual",
scripts/test_lifecycle_document_contract.py:32:        "bdd_scenarios.en.md",
scripts/test_lifecycle_document_contract.py:33:        "bdd_scenarios.vi.md",
scripts/test_lifecycle_document_contract.py:35:        "--require-bilingual",
scripts/test_lifecycle_document_contract.py:62:        "--require-bilingual",
scripts/test_lifecycle_document_contract.py:68:        "--require-bilingual",
scripts/test_lifecycle_document_contract.py:72:        "--require-bilingual",
scripts/test_lifecycle_document_contract.py:76:        "--require-bilingual",
scripts/test_lifecycle_document_contract.py:340:            "check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks",
skills/dev-implementation/resources/scripts/audit_epic.py:222:    scenarios = f"{epic_path}/bdd_scenarios.en.md"
skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py:148:        commit(self.main, ".devtool/epic/other_epic/bdd_scenarios.en.md", "# BDD\n", "Other epic")
skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py:154:            {"epic_dir": "other_epic", "bdd": ".devtool/epic/other_epic/bdd_scenarios.en.md"}])
skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py:446:        sha_a = commit(epic_a, ".devtool/epic/epic_a/bdd_scenarios.en.md", "# BDD\n", "Task A1")
skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py:453:        self.assertTrue((epic_b / ".devtool/epic/epic_a/bdd_scenarios.en.md").exists())
skills/dev-implementation/resources/scripts/task_contract.py:351:    "check-doc": "skills/doc_quality_check/resources/scripts/check_document.py",
skills/dev-implementation/resources/scripts/task_contract.py:415:                      epic_dir / "bdd_scenarios.en.md", epic_dir / "evidence" / f"{path.stem}.json")
skills/finishing-a-development-branch/resources/scripts/integrate_branch.py:273:        bdd = f".devtool/epic/{epic_dir}/bdd_scenarios.en.md"
  1120	
  1121	def _completed_rounds_count(root: Path, epic_dir: str | None, kind: str) -> int:
  1122	    if not epic_dir:
  1123	        return 0
  1124	    name, _ = review_file(kind)
  1125	    path = root / ".devtool" / "epic" / epic_dir / name
  1126	    if not path.exists():
  1127	        return 0
  1128	    return sum(1 for _n, lines in rounds_in(path.read_text(encoding="utf-8")) if "- **Status**: completed" in metadata(lines))
  1129	
  1130	
  1131	def run_principal(root: Path, args: argparse.Namespace, sha: str) -> int:
  1132	    if getattr(args, "doc", None):
  1133	        return run_principal_doc(root, args, sha)
  1134	
  1135	    facts_timeout = getattr(args, "facts_timeout", 300)
  1136	    check_cmd = [sys.executable, str(SCRIPTS / "check_epic_readiness.py"), args.epic_dir]
  1137	    try:
  1138	        _code, out, _err = run_gate("check_epic_readiness.py", check_cmd, root, facts_timeout)
  1139	    except PreconditionFailedError as error:
  1140	        print_gate_banner(error, args.cli)
  1141	        return 2
  1142	
  1143	    base_sha = git_run(root, "rev-parse", "--verify", args.base).decode().strip()
  1144	    readiness_output = out.rstrip()
  1145	    round_context, scope = delta_round_context(root, args, sha, kind="principal")
  1146	    if scope:
  1147	        print(f"{scope['Scope']}: reviewing the revision, not the whole epic (--full to review everything)",
  1148	              file=sys.stderr)
  1149	
  1150	    prompt = Template(principal_prompt_path().read_text(encoding="utf-8")).safe_substitute(
  1151	        rules=principal_rules_path().read_text(encoding="utf-8").strip(),
  1152	        sha=sha,
  1153	        base=args.base,
  1154	        base_sha=base_sha,
  1155	        epic_dir=f".devtool/epic/{args.epic_dir}",
  1156	        artefacts=principal_artefact_lines(root, args.epic_dir),
  1157	        readiness_output=readiness_output,
  1158	        round_context=round_context,
  1159	    )
  1160	
  1161	    if getattr(args, "developer_note", None):
  1162	        prompt += f"\n\n## Developer Special Instructions\n\n{args.developer_note}\n"
  1163	
  1164	    before = status_lines(root)
  1165	    code, out, err = execute(cli_command(args.cli, args.model, getattr(args, "thinking_level", None)), root, args.timeout, prompt)
  1166	    changed = tree_changes(root, before, sha)
  1167	    return record_round(root, args, sha, [Pass("principal", code, out, err, prompt)], changed,
  1168	                        {"Kind": "principal", **scope})
  1169	
  1170	
  1171	def run_adhoc_code(root: Path, args: argparse.Namespace, sha: str) -> int:
  1172	    commit_spec = getattr(args, "commits", None) or f"{args.base}...HEAD"
  1173	    log, diff_section = diff_range(root, args.base, getattr(args, "commits", None))
  1174	
  1175	    prompt = Template(PROMPT.read_text(encoding="utf-8")).safe_substitute(
  1176	        rules=RULES.read_text(encoding="utf-8").strip(),
  1177	        sha=sha,
  1178	        base=args.base,
  1179	        epic_dir=f"Ad-hoc diff review ({commit_spec})",
  1180	        artefacts=f"- Commit range: `{commit_spec}`",
  1181	        audit_output=f"Commit log ({commit_spec}):\n{log or '(no commits)'}",
  1182	        results_output="N/A (Ad-hoc review of branch diff)",
  1183	        round_context="",
  1184	        diff_section=diff_section,
  1185	    )
  1186	
  1187	    before = status_lines(root)
  1188	    code, out, _err = execute(cli_command(args.cli, args.model, getattr(args, "thinking_level", None)), root, args.timeout, prompt)
  1380	
  1381	
  1382	def tree_changes(root: Path, before: list[str], sha: str) -> list[str]:
  1383	    """Status lines that appeared or vanished since `before`, led by HEAD when it moved."""
  1384	    changed = sorted(set(status_lines(root)) ^ set(before))
  1385	    if head_of(root) != sha:
  1386	        changed.insert(0, "HEAD")
  1387	    return changed
  1388	
  1389	
  1390	def path_of(location: str) -> str:
  1391	    """The file a finding points at: its location before the first colon, without backticks."""
  1392	    return location.split(":", 1)[0].strip().strip("`")
  1393	
  1394	
  1395	def annotate(finding: tuple[str, str, str], shown: str) -> tuple[str, str, str]:
  1396	    """Mark a blocking finding whose location path the reviewer was never shown; its severity stays."""
  1397	    sev, loc, problem = finding
  1398	    if sev in BLOCKING and loc != "unparsed" and path_of(loc) not in shown:
  1399	        problem += " (location not shown to reviewer)"
  1400	    return sev, loc, problem
  1401	
  1402	
  1403	def pass_output(item: Pass, number: int, args: argparse.Namespace) -> str:
  1404	    if args.cli == "ollama":
  1405	        return f"### Pass {number}: {item.label}\n\n{item.out}" + (f"\n--- error ---\n{item.err}" if item.err.strip() else "")
  1406	    output = item.out + (f"\n--- stderr ---\n{item.err}" if item.err.strip() else "")
  1407	    if item.code is None:
  1408	        output += f"\n--- timed out after {args.timeout} seconds ---\n"
  1409	    return output
  1410	
  1411	
  1412	def record_round(root: Path, args: argparse.Namespace, sha: str, passes: list[Pass],
  1413	                 changed: list[str], extra: dict[str, str]) -> int:
  1414	    """Append one round to review_results.md from every pass of a review; return the run's exit code."""
  1415	    local = args.cli == "ollama"
  1416	    verdicts: list[str | None] = []
  1417	    findings: list[tuple[str, str, str]] = []
  1418	    complete = True
  1419	    for item in passes:
  1420	        lines = item.out.splitlines()
  1421	        marks = [(index, m.group(1).upper()) for index, line in enumerate(lines) if (m := VERDICT.match(line))]
  1422	        verdict = marks[-1][1] if marks else None
  1423	        if local:  # a draft line in the Analysis above the verdict block is never a finding
  1424	            block = "\n".join(lines[marks[-1][0]:]) if marks else ""
  1425	            found = [annotate(finding, item.shown) for finding in parse_findings(block, verdict)]
  1426	        else:
  1427	            found = parse_findings(item.out, verdict)
  1428	        verdicts.append(verdict)
  1429	        findings.extend(found)
  1430	        complete = complete and item.code == 0 and verdict is not None \
  1431	            and not (verdict == "CHANGES REQUIRED" and not found) and (not local or item.done_reason == "stop")
  1432	    if changed:
  1433	        status = f"discarded: tree modified ({', '.join(line[3:] if line != 'HEAD' else line for line in changed)})"
  1434	    else:
  1435	        status = "completed" if complete else "no verdict"
  1436	    if "CHANGES REQUIRED" in verdicts:
  1437	        verdict_text = "CHANGES REQUIRED"
  1438	    else:
  1439	        verdict_text = "PASS" if verdicts and None not in verdicts else "none"
  1440	    name, title = review_file(getattr(args, "kind", "code"))
  1441	    path = root / ".devtool" / "epic" / args.epic_dir / name
  1442	    existing = path.read_text(encoding="utf-8") if path.exists() else f"# {title}: {args.epic_dir}\n"
  1443	    round_num = len(rounds_in(existing)) + 1
  1444	    meta = {
  1445	        "Date": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
  1446	        "SHA": sha,
  1447	        "Base": args.base,
  1448	        "CLI": args.cli,
  1449	        "Model": effective_model(args.cli, args.model),
  1450	        "Thinking": effective_thinking_level(args.cli, getattr(args, "thinking_level", None)),
  1451	        "Status": status,
  1452	        "Verdict": verdict_text,
  1453	        **extra,
  1454	    }
  1455	    if (omitted := "; ".join(f"{item.label}: {', '.join(item.omitted)}" for item in passes if item.omitted)):
  1456	        meta["Omitted"] = omitted
  1457	    output = "\n\n".join(pass_output(item, number, args) for number, item in enumerate(passes, 1))
  1458	    text = existing.rstrip("\n") + "\n\n" + render_round(round_num, meta, findings, output)
  1459	    path.write_text(text, encoding="utf-8")
  1460	    update_sticky_review_config(root, args.cli, getattr(args, "model", None), getattr(args, "thinking_level", None))
  1461	    header = format_triage_header(
  1462	        f"Round {round_num}: {status} ({path.relative_to(root)})",
  1463	        sha,
  1464	        args.cli,
  1465	        effective_model(args.cli, getattr(args, "model", None)),
  1466	        effective_thinking_level(args.cli, getattr(args, "thinking_level", None)),
  1467	        verdict_text,
  1468	        findings,
  1469	    )
  1470	    print("\n".join(header))
  1471	    if status != "completed":
  1472	        print(f"- **Status**: {status}")
  1473	        return 2
  1474	    return 1 if any(sev in BLOCKING for sev, _, _ in findings) else 0
  1475	
  1476	
  1477	def check(args: argparse.Namespace) -> int:
  1478	    root = Path(git_run(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
  1479	    name, _ = review_file(getattr(args, "kind", "code"))
  1480	    path = root / ".devtool" / "epic" / args.epic_dir / name
  1481	    if not path.exists():
  1482	        return 0
  1483	    completed = [(n, lines) for n, lines in rounds_in(path.read_text(encoding="utf-8"))
  1484	                 if "- **Status**: completed" in metadata(lines)]
  1485	    undecided = []
  1486	    for line, cells in table_findings(completed[-1][1]) if completed else []:
  1487	        if len(cells) != 5:
  1488	            undecided.append(f"undecided: unreadable findings row: {line.strip()}")
  1489	        elif cells[1] in BLOCKING and not cells[4].startswith(("fixed in ", "dismissed: ")):
  1490	            undecided.append(f"undecided: #{cells[0]} {cells[1]} {cells[2]}")
  1491	    if undecided:
  1492	        print("\n".join(undecided))
  1493	    return 1 if undecided else 0
  1494	
  1495	
  1496	def round_meta(lines: list[str]) -> dict[str, str]:
  1497	    """A round's `- **Key**: value` fields."""
  1498	    return {m.group(1): m.group(2) for line in metadata(lines) if (m := META_LINE.match(line))}
  1499	
  1500	
  1501	def round_output(lines: list[str]) -> str:
  1502	    """The fenced raw output of a round, without its fence."""
  1503	    body = lines[lines.index("Raw output:") + 1:] if "Raw output:" in lines else []
  1504	    fences = [(index, match.group(1)) for index, line in enumerate(body) if (match := FENCE.match(line))]
  1505	    if not fences:
  1506	        return ""
  1507	    start, fence = fences[0]
  1508	    end = next((i for i in range(start + 1, len(body)) if body[i].rstrip() == fence), len(body))
  1509	    return "\n".join(body[start + 1:end])
  1510	
  1511	
  1512	def round_passes(output: str) -> list[tuple[str, str, str]]:
  1513	    """(pass, verdict, error) for each `### Pass` block, or one `review` pass when there is none."""
  1514	    blocks: list[tuple[str, list[str]]] = []
  1515	    for line in output.splitlines():
  1516	        if (header := PASS_HEADER.match(line)):
  1517	            blocks.append((f"{header.group(1)} {header.group(2)}", []))
  1518	        elif blocks:
  1519	            blocks[-1][1].append(line)
  1520	    rows = []
  1521	    for name, lines in blocks or [("review", output.splitlines())]:
  1522	        verdicts = [m.group(1).upper() for line in lines if (m := VERDICT.match(line))]
  1523	        after = lines[lines.index("--- error ---") + 1:] if "--- error ---" in lines else []
  1524	        rows.append((name, verdicts[-1] if verdicts else "none", after[0].strip() if after else "—"))
  1525	    return rows
  1526	
  1527	
  1100	
  1101	    def _apply_code_fixes(self, round_num: int, plan_text: str = "") -> bool:
  1102	        """Apply code fixes according to the approved or adjusted fix plan and commit."""
  1103	        prompt = (
  1104	            f"You are the AI Programmer (Role 2.3). Implement the code fixes for Cross-Model Review Round {round_num}.\n"
  1105	            f"Approved Fix Plan:\n\n{plan_text}\n\n"
  1106	            f"Apply the changes, verify tests pass, and adhere to strict TDD.\n"
  1107	        )
  1108	        self.dispatcher.dispatch(
  1109	            cli="agy",
  1110	            args=["--model", self.config.programmer_model, "--effort", self.config.programmer_effort, "--mode", "accept-edits"],
  1111	            prompt=prompt,
  1112	        )
  1113	        status_res = subprocess.run(
  1114	            ["git", "status", "--porcelain"],
  1115	            cwd=self.root,
  1116	            capture_output=True,
  1117	            text=True,
  1118	            check=False,
  1119	        )
  1120	        if status_res.returncode == 0 and status_res.stdout.strip():
  1121	            subprocess.run(["git", "add", "-A"], cwd=self.root, check=False)
  1122	            commit_title = f"[{self.epic_slug.upper()}] Apply code fixes for Cross-Model Review round {round_num}"
  1123	            subprocess.run(
  1124	                ["git", "commit", "-m", commit_title],
  1125	                cwd=self.root,
  1126	                capture_output=True,
  1127	                check=False,
  1128	            )
  1129	        return True
  1130	
  1131	    def _record_review_decisions(self, round_num: int) -> bool:
  1132	        """Record review decision cells and commit decisions."""
  1133	        file = self.root / ".devtool" / "epic" / self.epic_slug / "review_results.md"
  1134	        if file.is_file():
  1135	            content = file.read_text(encoding="utf-8")
  1136	            rev_res = subprocess.run(
  1137	                ["git", "rev-parse", "HEAD"],
  1138	                cwd=self.root,

 succeeded in 0ms:
   106	
   107	1. Push as new branch and create a Pull Request
   108	2. Keep as-is (I'll handle it later)
   109	
   110	Which option?
   111	```
   112	
   113	Present the menu exactly as written — concise, with every option coming
   114	from the list above. Discarding the work happens only in response to your
   115	human partner explicitly asking for it (see "If your human partner asks to
   116	discard the work" below). Wait for their answer; the integration decision
   117	is theirs.
   118	
   119	## Step 5: Execute Choice
   120	
   121	### Pre-Finish Hook: Epic Archival & Kanban Clean-up
   122	
   123	Before executing **Option 1 (Merge)** or **Option 2 (Push & PR)**, if the workspace contains completed tasks in `.devtool/features/done/`, archive them into their respective epic directory:
   124	
   125	```bash
   126	SYNC_SCRIPT="$SKILL_DIR/../dev-implementation/resources/scripts/sync_task_status.py"
   127	RESUME_SCRIPT="scripts/resume_context.py"
   128	if ls .devtool/features/done/task_*.md 1>/dev/null 2>&1; then
   129	  if [ ! -f "$SYNC_SCRIPT" ]; then
   130	    echo "STOP: done tasks exist but $SYNC_SCRIPT is missing" >&2
   131	  else
   132	    python3 "$SYNC_SCRIPT" archive-done
   133	    if [ -f "$RESUME_SCRIPT" ]; then
   134	      python3 "$RESUME_SCRIPT" --complete "<epic_slug>" "<milestone_summary>"
   135	    fi
   136	    git add .devtool/ docs/ 2>/dev/null || true
   137	    git commit -m "[EPIC] Complete epic and archive done tasks" -m "- archive done tasks into .devtool/epic/<epic_dir>
   138	- update epic status to Done across English and Vietnamese HLDs
   139	- clean up .devtool/features/done and docs/superpowers" 2>/dev/null || true
   140	  fi
   141	fi
   142	```
   143	
   144	If it prints `STOP`, report it to your human partner and do not continue: integrating without the
   145	archival leaves completed tasks stranded in `done/`.
   146	
   147	This guarantees:
   148	- Tasks remain visible in the **DONE** column on the Kanban dashboard throughout development and review.
   149	- Archival, link rewriting, and status transition to `Done` occur cleanly and are committed to the branch before it is merged or pushed to a PR.
   150	- If the user selects **Option 3 (Keep As-Is)**, tasks remain untouched in `.devtool/features/done/` so the developer can continue tracking them on the Kanban board.
   151	
   152	### Update onto Base (Options 1 and 2)
   153	
   154	Runs after the archival commit, from the branch's worktree (or the repository, for a normal repo).
   155	It brings in everything that landed on the base since this branch split off, resolves conflicts here
   156	on the branch, and re-verifies the result. Nothing touches the base branch during this section.
   157	
   158	Skip this section on a detached HEAD. When preflight warns that the branch `has already been
   159	pushed`, skip steps 2 and 3 and tell your human partner why: rebasing a pushed branch needs a
   160	force-push. Step 4 still runs and gives the candidate sha.
   161	
   162	1. **Preflight** — read-only:
   163	
   164	   ```bash
   165	   python3 "$INTEGRATE" preflight --base <base-branch>
   166	   ```
   167	
   168	   Show your human partner the upstream commits, the upstream epics and the predicted tier. If the
   169	   warnings say the base has diverged from its upstream, stop and ask. If a rebase is already in
   170	   progress (`predicted tier: rebase-in-progress`), continue or abort it; never start another. If the fetch failed, ask before landing.
   171	
   172	2. **Rebase:**
   173	
   174	   ```bash
   175	   python3 "$INTEGRATE" rebase --base <base-branch>
   176	   ```
   177	
     1	{
     2	  "schema_version": 1,
     3	  "capabilities": {
     4	    "format": ["ruff", "format", "--check", "skills/web-quality-check", "tests", "skills/dev-implementation/resources/scripts/generate_smoke_checklist.py"],
     5	    "lint": ["ruff", "check", "skills/web-quality-check", "tests", "skills/dev-implementation/resources/scripts/generate_smoke_checklist.py"],
     6	    "type_check": ["mypy", "skills/web-quality-check/resources/scripts/validate_web_quality.py", "skills/web-quality-check/resources/scripts/run_playwright_harness.py", "skills/quality_check/resources/scripts/verify_polyglot_registry.py", "skills/web-quality-check/resources/scripts/check_vanilla_js.py", "skills/dev-implementation/resources/scripts/generate_smoke_checklist.py"],
     7	    "test": ["python3", "-m", "pytest", "tests"],
     8	    "architecture": ["bash", "scripts/verify.sh"]
     9	  },
    10	  "profiles": {
    11	    "pr": ["lint", "test"],
    12	    "epic": ["format", "lint", "type_check", "test", "architecture"],
    13	    "release": ["format", "lint", "type_check", "test", "architecture"],
    14	    "scheduled": ["format", "lint", "type_check", "test", "architecture"]
    15	  }
    16	}
python3 is /opt/homebrew/bin/python3
python3 is /usr/bin/python3
python3 is /opt/homebrew/bin/python3
mypy is /Users/danhdueexoictif/.local/bin/mypy
mypy is /Users/danhdueexoictif/.local/bin/mypy
ruff is /Users/danhdueexoictif/.local/bin/ruff
ruff is /Users/danhdueexoictif/.local/bin/ruff
git is /usr/bin/git
tests/test_lifecycle_runner.py:9:import unittest
tests/test_lifecycle_runner.py:12:from unittest.mock import MagicMock, patch
tests/test_lifecycle_runner.py:29:class TestLifecycleRunner_Integration(unittest.TestCase):
tests/test_lifecycle_runner.py:531:                mock_sync.assert_called_with(4, unittest.mock.ANY)
tests/test_lifecycle_runner.py:628:if __name__ == "__main__":
tests/test_lifecycle_runner.py:629:    unittest.main()
tests/test_polyglot_gate4.py:206:        code = main(
scripts/check_source_fidelity.py:138:def main() -> int:
scripts/check_source_fidelity.py:175:if __name__ == "__main__":
scripts/check_source_fidelity.py:176:    sys.exit(main())

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/check_task_contract.py | sed -n '1,95p;390,490p'; nl -ba skills/dev-implementation/resources/scripts/check_bdd_traceability.py | sed -n '1,140p;225,268p'; nl -ba skills/doc_quality_check/resources/scripts/check_document.py | sed -n '1,270p'; nl -ba scripts/check_source_fidelity.py | sed -n '1,177p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""Check the task files and HLD a designer wrote against the task contract, before Gate 2 closes.
     3	
     4	Usage:
     5	  check_task_contract.py [--design] --hld <epic_dir>.en.md --tasks <task_*.md ...>
     6	
     7	Prints problems as `<task stem>:<row or section>: <problem>` or `<hld file name>: <problem>`, the
     8	implicit protected paths, and a Result line. Exit codes: 0 no problem; 1 problems; 2 usage error.
     9	Python 3 standard library only.
    10	"""
    11	from __future__ import annotations
    12	
    13	import argparse
    14	import importlib
    15	import json
    16	import re
    17	import shlex
    18	import shutil
    19	import subprocess
    20	import sys
    21	from pathlib import Path
    22	from typing import Any
    23	
    24	sys.path.insert(0, str(Path(__file__).resolve().parent))
    25	tc: Any = importlib.import_module("task_contract")
    26	cb: Any = importlib.import_module("check_bdd_traceability")
    27	sts: Any = importlib.import_module("sync_task_status")
    28	UsageError: type[Exception] = cb.UsageError
    29	covers_of: Any = cb.covers_of
    30	read_text: Any = cb.read_text
    31	
    32	SECTIONS = ("Files", "Verification", "Definition of Done", "Stop and Report If", "Decisions Already Made")
    33	ROW_PREFIX = re.compile(r"^Verification row [^:]+: ")
    34	STATUS = re.compile(r'^status:\s*"?([A-Za-z_-]+)"?\s*$', re.MULTILINE)
    35	GLOB_CHARS = re.compile(r"[*?]")
    36	WEAK_ASSERTION_RE = re.compile(r"\b(should be truthy|is valid|should work|returns non-empty)\b", re.IGNORECASE)
    37	RESERVED_RUNNER_EVIDENCE = re.compile(r"^task_.*\.json$")
    38	NON_PORTABLE_PATH_RE = re.compile(r"(?:/Users/|/home/|~/|\.claude/plugins/cache/|\.gemini/config/plugins/)")
    39	
    40	
    41	class Checker:
    42	    def __init__(self, root: Path) -> None:
    43	        self.root = root
    44	        self.problems: list[str] = []
    45	        self.warnings: list[str] = []
    46	        listed = subprocess.run(["git", "ls-files", "-z"], check=False, cwd=root, capture_output=True, text=True).stdout
    47	        self.tracked = set(listed.split("\0")) - {""}
    48	
    49	    def ignored(self, path: str) -> bool:
    50	        return subprocess.run(["git", "check-ignore", "-q", "--", path], check=False, cwd=self.root,
    51	                              capture_output=True).returncode == 0
    52	
    53	    def problem(self, where: str, text: str) -> None:
    54	        self.problems.append(f"{where}: {text}")
    55	
    56	    def is_tracked(self, path: str) -> bool:
    57	        return path in self.tracked
    58	
    59	    def matches_tracked(self, pattern: str) -> bool:
    60	        return any(tc.path_matches(pattern, name) for name in self.tracked)
    61	
    62	
    63	def read_file(path: Path) -> str:
    64	    try:
    65	        return str(read_text(path))
    66	    except OSError as error:
    67	        raise UsageError(f"cannot read {path}: {error.strerror or error}") from None
    68	
    69	
    70	def table_rows(check: Checker, stem: str, text: str) -> list[Any]:
    71	    """Parse the Verification table row by row, reporting every bad row rather than the first."""
    72	    body = tc.section(text, "Verification")
    73	    if body is None:
    74	        return []
    75	    table = [line for line in body.splitlines() if line.lstrip().startswith("|")]
    76	    if not table or tc.split_cells(table[0]) != tc.HEADER:
    77	        check.problem(f"{stem}:Verification", "Verification header must be exactly: | " + " | ".join(tc.HEADER) + " |")
    78	        return []
    79	    rows: list[Any] = []
    80	    seen: set[str] = set()
    81	    for line in table[2:]:
    82	        cells = tc.split_cells(line)
    83	        try:
    84	            if len(cells) != len(tc.HEADER):
    85	                raise tc.ContractError(f"Verification row {cells[0]!r}: expected {len(tc.HEADER)} cells, found {len(cells)}")
    86	            rows.append(tc.parse_row(cells, seen))
    87	            if rows[-1].phase != "TIER-C" and rows[-1].expect.results:
    88	                check.problem(f"{stem}:{cells[0]}", "results is allowed only on TIER-C rows")
    89	        except tc.ContractError as error:
    90	            check.problem(f"{stem}:{cells[0]}", ROW_PREFIX.sub("", str(error)))
    91	        seen.add(cells[0])
    92	    return rows
    93	
    94	
    95	def check_structure(check: Checker, stem: str, path: Path, text: str, rows: list[Any]) -> None:
   390	        if m:
   391	            check.problem(f"{source_name}:{line_num}", f"weak BDD assertion found: {m.group(0)!r}")
   392	
   393	
   394	def check_task(
   395	    check: Checker,
   396	    path: Path,
   397	    text: str,
   398	    design: bool,
   399	    created: set[str],
   400	    prereq_files: set[str] | None = None,
   401	) -> None:
   402	    stem = path.stem
   403	    rows = table_rows(check, stem, text)
   404	    check_structure(check, stem, path, text, rows)
   405	    for row in rows:
   406	        if row.expect.results and not check.ignored(row.expect.results):
   407	            check.problem(f"{stem}:{row.id}", f"results path {row.expect.results} is not ignored by git")
   408	        check_pytest_k(check, stem, row)
   409	        check_portable_command(check, stem, row)
   410	    check_weak_bdd(check, stem, text)
   411	    status = STATUS.search(text.split("\n---", 1)[0]) if text.startswith("---") else None
   412	    if design or not (status and status.group(1) == "done"):
   413	        if is_python_task(text, rows):
   414	            check_python_tier_b(check, stem, rows)
   415	        check_allowed(check, stem, text, design, prereq_files)
   416	        check_evidence(check, stem, text, design)
   417	        check_grounding(check, stem, text, rows, created)
   418	
   419	
   420	def check_hld(check: Checker, hld_path: Path, text: str, tasks: dict[Path, str]) -> None:
   421	    name = hld_path.name
   422	    if not tc.parse_protected_paths(text):
   423	        check.problem(name, "no Protected paths: line")
   424	    results = tc.parse_integration_results(text)
   425	    if not results:
   426	        check.problem(name, "no Integration results: line")
   427	    for entry in results:
   428	        command, arrow, report = entry.rpartition(" -> ")
   429	        if not arrow or not command.strip() or not report.strip():
   430	            check.problem(name, f"Integration results line is not <command> -> <path>: {entry}")
   431	        elif not check.ignored(report.strip()):
   432	            check.problem(name, f"Integration results path {report.strip()} is not ignored by git")
   433	    environment = tc.verification_environment(text)
   434	    if environment is None or not environment.strip():
   435	        check.problem(name, "## Verification Environment section is missing or empty")
   436	        return
   437	    specs = tc.parse_integration_result_specs(text)
   438	    for spec in specs:
   439	        for need in spec.needs:
   440	            if need not in environment:
   441	                check.problem(
   442	                    name,
   443	                    f"Live integration needs variable '{need}' is not named in the Verification Environment section",
   444	                )
   445	    for path, task_text in tasks.items():
   446	        try:
   447	            rows, _ = tc.parse_verification(task_text)
   448	        except tc.ContractError:
   449	            continue
   450	        for row in rows:
   451	            for need in row.needs:
   452	                if need not in environment:
   453	                    check.problem(f"{path.stem}:{row.id}", f"Needs {need} is not named in the Verification Environment section")
   454	    for bdd_path in sorted(hld_path.parent.glob("bdd_scenarios*.md")):
   455	        try:
   456	            content = read_file(bdd_path)
   457	            check_weak_bdd(check, bdd_path.name, content)
   458	        except UsageError:
   459	            pass
   460	
   461	
   462	def check_r2_r3_parity(check: Checker, hld_path: Path, tasks: dict[Path, str]) -> None:
   463	    epic_dir = hld_path.parent.name
   464	    bdd_path = hld_path.parent / "bdd_scenarios.en.md"
   465	    canonical_blocks: dict[str, list[str]] = {}
   466	    if bdd_path.is_file():
   467	        try:
   468	            canonical_blocks = sts.extract_scenario_blocks(read_file(bdd_path))
   469	        except UsageError:
   470	            pass
   471	
   472	    for task_path, epic_text in tasks.items():
   473	        stem = task_path.stem
   474	        # R3: BDD verbatim check
   475	        covers: list[str] = []
   476	        for line in epic_text.splitlines():
   477	            m = re.match(r"^Covers:\s*(.+)$", line.strip())
   478	            if m:
   479	                covers.extend(re.findall(r"[A-Z0-9]+(?:-[A-Z0-9]+)+", m.group(1)))
   480	        if covers and canonical_blocks:
   481	            task_blocks = sts.extract_scenario_blocks(epic_text)
   482	            for cid in covers:
   483	                if cid in canonical_blocks:
   484	                    if cid in task_blocks and task_blocks[cid] != canonical_blocks[cid]:
   485	                        check.problem(f"{stem}:BDD", f"scenario {cid} differs from bdd_scenarios.en.md (R3)")
   486	
   487	        # R2: Mirror parity check if mirror exists
   488	        features_dir = check.root / ".devtool" / "features"
   489	        done_dir = features_dir / "done"
   490	        mirror_path = features_dir / task_path.name
     1	#!/usr/bin/env python3
     2	"""Check that every epic BDD scenario is assigned to a task and covered by an integration test.
     3	
     4	Usage:
     5	  check_bdd_traceability.py plan  --scenarios <bdd_scenarios.en.md> --tasks <task_*.md ...>
     6	  check_bdd_traceability.py tests --scenarios <bdd_scenarios.en.md> --roots <dir ...> [--ids <ID ...>]
     7	                                  [--results <report file|dir|glob ...>]
     8	
     9	Exit codes: 0 all covered; 1 traceability failure; 2 usage error.
    10	"""
    11	from __future__ import annotations
    12	
    13	import argparse
    14	import re
    15	import subprocess
    16	import sys
    17	from pathlib import Path
    18	
    19	from result_reports import ReportError, load_reports, reference_pattern, verdicts
    20	
    21	ID_SHAPE = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]+")
    22	SCENARIO_KEYWORDS = (
    23	    "Scenario Outline", "Scenario Template", "Scenario", "Example",
    24	    "Khung tình huống", "Khung kịch bản", "Tình huống", "Kịch bản",
    25	)
    26	SCENARIO_LINE = re.compile(
    27	    r"^\s*(?:" + "|".join(re.escape(keyword) for keyword in SCENARIO_KEYWORDS) + r")\s*:\s*(.*)$"
    28	)
    29	LEADING_TAG = re.compile(r"^\[([^\]]*)\]")
    30	FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*(\S*)")
    31	COVERS_LINE = re.compile(r"^\s*(?:[-*]\s+)?\**Covers\**\s*:\**\s*(.*)$")
    32	ID_TOKEN = re.compile(r"(?<![A-Za-z0-9-])" + ID_SHAPE.pattern + r"(?![A-Za-z0-9])")
    33	
    34	
    35	class UsageError(Exception):
    36	    """Missing input: exit 2."""
    37	
    38	
    39	def read_text(path: Path) -> str:
    40	    """Read a scenario document or task file; anything but UTF-8 is a usage error."""
    41	    try:
    42	        return path.read_text(encoding="utf-8")
    43	    except UnicodeDecodeError:
    44	        raise UsageError(f"{path} is not valid UTF-8") from None
    45	
    46	
    47	def scenario_ids(path: Path) -> tuple[list[str], list[str]]:
    48	    """Identifiers in document order, and the problems found, for one scenario document."""
    49	    ids: list[str] = []
    50	    problems: list[str] = []
    51	    fence_marker: str | None = None
    52	    in_gherkin = False
    53	    for number, line in enumerate(read_text(path).splitlines(), start=1):
    54	        fence = FENCE.match(line)
    55	        if fence and fence_marker is None:
    56	            fence_marker, in_gherkin = fence.group(1), fence.group(2).lower() == "gherkin"
    57	            continue
    58	        if (
    59	            fence
    60	            and fence_marker is not None
    61	            and fence.group(1)[0] == fence_marker[0]
    62	            and len(fence.group(1)) >= len(fence_marker)
    63	            and not fence.group(2)
    64	        ):
    65	            fence_marker, in_gherkin = None, False
    66	            continue
    67	        match = SCENARIO_LINE.match(line) if in_gherkin else None
    68	        if not match:
    69	            continue
    70	        tag = LEADING_TAG.match(match.group(1).strip())
    71	        if not tag:
    72	            problems.append(f"{path}:{number}: scenario has no identifier")
    73	        elif not ID_SHAPE.fullmatch(tag.group(1)):
    74	            problems.append(f"{path}:{number}: malformed identifier [{tag.group(1)}]")
    75	        elif tag.group(1) in ids:
    76	            problems.append(f"{path}:{number}: duplicate identifier {tag.group(1)}")
    77	        else:
    78	            ids.append(tag.group(1))
    79	    return ids, problems
    80	
    81	
    82	def load_scenarios(path: Path) -> tuple[list[str], list[str]]:
    83	    """Validate the English document and, when present, its Vietnamese sibling."""
    84	    if not path.is_file():
    85	        raise UsageError(f"scenario document not found: {path}")
    86	    ids, problems = scenario_ids(path)
    87	    if not ids and not problems:
    88	        problems.append(f"{path}: no scenarios found inside gherkin fences")
    89	    if path.name.endswith(".en.md"):
    90	        sibling = path.with_name(path.name[: -len(".en.md")] + ".vi.md")
    91	        if sibling.is_file():
    92	            vi_ids, vi_problems = scenario_ids(sibling)
    93	            problems.extend(vi_problems)
    94	            missing = sorted(set(ids) - set(vi_ids))
    95	            extra = sorted(set(vi_ids) - set(ids))
    96	            if missing:
    97	                problems.append(f"{sibling}: missing identifiers {', '.join(missing)}")
    98	            if extra:
    99	                problems.append(f"{sibling}: identifiers not in {path.name}: {', '.join(extra)}")
   100	    return ids, problems
   101	
   102	
   103	def covers_of(path: Path) -> list[str]:
   104	    """Identifiers named on every Covers: line of one task file."""
   105	    found: list[str] = []
   106	    for line in read_text(path).splitlines():
   107	        match = COVERS_LINE.match(line)
   108	        if match:
   109	            found.extend(ID_TOKEN.findall(match.group(1)))
   110	    return found
   111	
   112	
   113	def check_plan(ids: list[str], task_paths: list[Path]) -> tuple[dict[str, list[str]], list[str]]:
   114	    coverage: dict[str, list[str]] = {identifier: [] for identifier in ids}
   115	    problems: list[str] = []
   116	    for path in task_paths:
   117	        if not path.is_file():
   118	            raise UsageError(f"task file not found: {path}")
   119	        for identifier in covers_of(path):
   120	            if identifier not in coverage:
   121	                problems.append(f"{path}: Covers names unknown identifier {identifier}")
   122	            elif path.name not in coverage[identifier]:
   123	                coverage[identifier].append(path.name)
   124	    for identifier, owners in coverage.items():
   125	        if len(owners) > 1:
   126	            problems.append(f"{identifier} is on the Covers lines of {', '.join(owners[:-1])} and {owners[-1]}")
   127	    return coverage, problems
   128	
   129	
   130	def stale_pattern(ids: list[str]) -> re.Pattern[str]:
   131	    """Uppercase hyphenated tokens shaped like this document's identifiers: same prefix, same segment count."""
   132	    shapes = sorted({(identifier.split("-")[0], identifier.count("-")) for identifier in ids})
   133	    alternatives = "|".join(re.escape(prefix) + "(?:-[A-Z0-9]+)" * (hyphens - 1) + "-[0-9]+"
   134	                            for prefix, hyphens in shapes)
   135	    return re.compile(r"(?<![A-Za-z0-9-])(?:" + alternatives + r")(?![A-Za-z0-9-])")
   136	
   137	
   138	def listed_files(root: Path) -> list[Path] | None:
   139	    """Files git lists under root — tracked, plus untracked but not ignored — or None outside git."""
   140	    try:
   225	    return 1 if failed else 0
   226	
   227	
   228	def main(argv: list[str] | None = None) -> int:
   229	    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
   230	    modes = parser.add_subparsers(dest="mode", required=True)
   231	    plan = modes.add_parser("plan", help="every scenario is assigned to exactly one task")
   232	    plan.add_argument("--scenarios", required=True, type=Path)
   233	    plan.add_argument("--tasks", required=True, nargs="+", type=Path)
   234	    tests = modes.add_parser("tests", help="every scenario has at least one integration test")
   235	    tests.add_argument("--scenarios", required=True, type=Path)
   236	    tests.add_argument("--roots", required=True, nargs="+")
   237	    tests.add_argument("--ids", nargs="+")
   238	    tests.add_argument("--results", nargs="+")
   239	    args = parser.parse_args(argv)
   240	    try:
   241	        ids, problems = load_scenarios(args.scenarios)
   242	        if problems:
   243	            print("\n".join(problems))
   244	            print("Result: scenario document invalid — FAIL")
   245	            return 1
   246	        if args.mode == "plan":
   247	            coverage, problems = check_plan(ids, args.tasks)
   248	            return report(coverage, problems, [])
   249	        roots = [Path(value) for value in split_values(args.roots)]
   250	        selected = split_values(args.ids) or ids
   251	        unknown = [f"--ids names unknown identifier {identifier}"
   252	                   for identifier in selected if identifier not in ids]
   253	        known_selected = [identifier for identifier in selected if identifier in ids]
   254	        if args.results:
   255	            return report_results(ids, known_selected, roots, split_values(args.results),
   256	                                  not args.ids, unknown)
   257	        coverage, problems, warnings = check_tests(ids, known_selected, roots, not args.ids)
   258	        return report(coverage, unknown + problems, warnings)
   259	    except (UsageError, ReportError) as error:
   260	        print(f"error: {error}", file=sys.stderr)
   261	        return 2
   262	
   263	
   264	if __name__ == "__main__":
   265	    sys.exit(main())
     1	#!/usr/bin/env python3
     2	"""Mechanical checks for a document work item — the Kind: document path of quality_check.
     3	
     4	Prose instructions to "check every link resolves" are exactly the kind of step that gets
     5	skipped under load, so the mechanical half of Gate 2 is a script rather than a checklist.
     6	
     7	Usage:
     8	  check_document.py FILE [FILE ...]           run the mechanical checks
     9	  check_document.py --require-toc FILE ...    require a complete table of contents
    10	  check_document.py --require-bilingual FILE ... require matching .en.md/.vi.md files
    11	  check_document.py --changed-files F [F ...] apply the refusal rule and exit
    12	
    13	--require-toc and --require-bilingual apply to lifecycle deliverables. They are opt-in because
    14	task files, epic records and SKILL.md files are not deliverables and were never meant to carry
    15	either contract.
    16	
    17	Exit 0 clean, 1 on any finding.
    18	"""
    19	from __future__ import annotations
    20	
    21	import argparse
    22	import pathlib
    23	import re
    24	import sys
    25	
    26	# Extensions that ship in a build. A document work item that touches one of these is
    27	# development work, whatever the Kind field claims.
    28	SHIPPED_SUFFIXES = {
    29	    ".dart", ".kt", ".kts", ".java", ".swift", ".m", ".mm", ".h", ".c", ".cc", ".cpp",
    30	    ".gradle", ".pbxproj", ".plist", ".xml", ".yaml", ".yml", ".json", ".lock",
    31	    ".ts", ".tsx", ".js", ".jsx", ".py", ".rb", ".go", ".rs",
    32	}
    33	# …except these, which are documentation or workspace infrastructure despite the extension.
    34	SHIPPED_EXCEPTIONS = re.compile(r"(?:^|/)(\.devtool|docs|\.github)/|(?:^|/)CHANGELOG\.md$")
    35	
    36	PLACEHOLDER = re.compile(r"\b(TBD|TODO|FIXME|XXX)\b")
    37	
    38	TOC_HEADING = re.compile(
    39	    r"^##\s+.*(?:table of contents|contents|mục lục)\s*$", re.IGNORECASE
    40	)
    41	
    42	
    43	def strip_code(text: str) -> str:
    44	    """Blank out fenced blocks and inline code spans, preserving line numbering.
    45	
    46	    A document that documents the placeholder check would otherwise fail it — observed, not
    47	    hypothetical. verify.sh step 3 strips the same way before checking links.
    48	    """
    49	    out, fenced = [], False
    50	    for line in text.split("\n"):
    51	        if line.lstrip().startswith("```"):
    52	            fenced = not fenced
    53	            out.append("")
    54	            continue
    55	        out.append("" if fenced else re.sub(r"`[^`]*`", "", line))
    56	    return "\n".join(out)
    57	
    58	
    59	def anchor(heading: str) -> str:
    60	    h = re.sub(r"^#+\s*", "", heading).rstrip().lower()
    61	    h = re.sub(r"[^\w\s-]", "", h)
    62	    return "#" + h.replace(" ", "-")
    63	
    64	
    65	def check_file(path: pathlib.Path, require_toc: bool = False) -> list:
    66	    findings = []
    67	    raw = path.read_text()
    68	    prose = strip_code(raw)
    69	    lines = prose.split("\n")
    70	    raw_lines = raw.split("\n")
    71	
    72	    for i, line in enumerate(lines, 1):
    73	        m = PLACEHOLDER.search(line)
    74	        if m:
    75	            findings.append((path, i, f"placeholder {m.group(1)} in prose"))
    76	
    77	    fences = sum(1 for ln in raw_lines if ln.lstrip().startswith("```"))
    78	    if fences % 2:
    79	        findings.append((path, 0, f"unbalanced code fences ({fences} found)"))
    80	
    81	    # Markdown lint & Diagram lint checks
    82	    fence_len = 0
    83	    fence_lang = ""
    84	    in_flowchart = False
    85	    in_digraph = False
    86	
    87	    for i, rline in enumerate(raw_lines, 1):
    88	        stripped = rline.strip()
    89	        lstripped = rline.lstrip()
    90	
    91	        # Check for code fence start/end
    92	        m_fence = re.match(r"^(?P<fence>`{3,}|~{3,})(?P<lang>\S*)", lstripped)
    93	        if m_fence:
    94	            cur_len = len(m_fence.group("fence"))
    95	            if fence_len == 0:
    96	                # Opening fence
    97	                fence_len = cur_len
    98	                fence_lang = m_fence.group("lang").lower()
    99	                if not fence_lang:
   100	                    findings.append((path, i, "fenced code block missing language tag (MD040)"))
   101	                in_flowchart = False
   102	                in_digraph = False
   103	                continue
   104	            elif cur_len >= fence_len and not m_fence.group("lang"):
   105	                # Closing fence
   106	                fence_len = 0
   107	                fence_lang = ""
   108	                in_flowchart = False
   109	                in_digraph = False
   110	                continue
   111	
   112	        # Outside code blocks
   113	        if fence_len == 0:
   114	            # Check heading without space after #: e.g. #Heading
   115	            if re.match(r"^#{1,6}[^ \t#]", rline):
   116	                findings.append((path, i, f"no space after '#' in heading (MD018): {stripped}"))
   117	            continue
   118	
   119	        # Inside code blocks (fence_len > 0)
   120	        if fence_lang == "mermaid":
   121	            # Check for legacy graph syntax
   122	            m_graph = re.match(r"^graph\s+(TD|LR|TB|RL|BT)", stripped)
   123	            if m_graph:
   124	                findings.append((path, i, f"legacy Mermaid syntax '{stripped}' — use 'flowchart {m_graph.group(1)}' instead"))
   125	            elif stripped.startswith("flowchart"):
   126	                in_flowchart = True
   127	            elif stripped == "stateDiagram":
   128	                findings.append((path, i, "legacy Mermaid syntax 'stateDiagram' — use 'stateDiagram-v2' instead"))
   129	
   130	            if in_flowchart:
   131	                # Check unquoted parentheses/brackets/colons in node labels
   132	                unquoted_sq = re.search(r'\b\w+\[(?!\s*["`\'])([^\]]*[\(\):][^\]]*)\]', stripped)
   133	                if unquoted_sq:
   134	                    findings.append((path, i, f"unquoted special characters in Mermaid node label: {unquoted_sq.group(0)} (enclose in double quotes)"))
   135	                unquoted_dia = re.search(r'\b\w+\{(?!\s*["`\'])([^\}]*[\(\):][^\}]*)\}', stripped)
   136	                if unquoted_dia:
   137	                    findings.append((path, i, f"unquoted special characters in Mermaid diamond label: {unquoted_dia.group(0)} (enclose in double quotes)"))
   138	
   139	        elif fence_lang in ("dot", "graphviz"):
   140	            if "digraph" in stripped:
   141	                in_digraph = True
   142	            if in_digraph:
   143	                # Using -- instead of ->
   144	                if re.search(r'\w+\s+--\s+\w+', stripped):
   145	                    findings.append((path, i, "invalid edge operator '--' in digraph — use '->' for directed edges"))
   146	                # Statements should end with semicolon
   147	                if stripped and not stripped.startswith(("//", "#", "/*", "*")) and not stripped.endswith((";", "{", "}")):
   148	                    if not re.match(r"^(di)?graph\b", stripped) and not stripped.startswith("subgraph"):
   149	                        findings.append((path, i, f"missing terminating semicolon ';' in DOT statement: {stripped}"))
   150	
   151	    headings = [anchor(ln) for ln in raw_lines if re.match(r"^#{1,6} ", ln)]
   152	    for i, line in enumerate(lines, 1):
   153	        for link in re.findall(r"\]\(([^)]+)\)", line):
   154	            if link.startswith(("http://", "https://", "mailto:")) or "<" in link:
   155	                continue
   156	            if link.startswith("#"):
   157	                if link.lower() not in headings:
   158	                    findings.append((path, i, f"anchor has no matching heading: {link}"))
   159	                continue
   160	            target = (path.parent / link.split("#")[0]).resolve()
   161	            if not target.exists():
   162	                findings.append((path, i, f"link does not resolve: {link}"))
   163	
   164	    if require_toc:
   165	        sections = [ln for ln in raw_lines if re.match(r"^##\s+", ln)]
   166	        plan_tasks = [ln for ln in raw_lines if re.match(r"^###\s+Task\s+", ln)]
   167	        navigable_headings = sections + plan_tasks
   168	        toc_sections = [ln for ln in sections if TOC_HEADING.match(ln)]
   169	        linked_anchors = set(re.findall(r"\]\((#[^)]+)\)", prose.lower()))
   170	        if not toc_sections:
   171	            findings.append((path, 0, "no table of contents heading — a reader cannot navigate it"))
   172	        for heading in navigable_headings:
   173	            if TOC_HEADING.match(heading):
   174	                continue
   175	            heading_anchor = anchor(heading)
   176	            if heading_anchor not in linked_anchors:
   177	                findings.append((path, 0,
   178	                                 f"table of contents does not link section: {heading}"))
   179	    return findings
   180	
   181	
   182	def check_language_pairs(paths: list[pathlib.Path]) -> list:
   183	    """Require every lifecycle document to have matching English and Vietnamese files."""
   184	    findings = []
   185	    normalized = {path.resolve() for path in paths}
   186	    for path in paths:
   187	        name = path.name
   188	        if name.endswith(".en.md"):
   189	            counterpart = path.with_name(name[:-6] + ".vi.md")
   190	        elif name.endswith(".vi.md"):
   191	            counterpart = path.with_name(name[:-6] + ".en.md")
   192	        else:
   193	            findings.append((path, 0,
   194	                             "lifecycle document must use an .en.md or .vi.md language suffix"))
   195	            continue
   196	        if counterpart.resolve() not in normalized:
   197	            state = "missing" if not counterpart.exists() else "not included in this check"
   198	            findings.append((path, 0, f"language counterpart {state}: {counterpart.name}"))
   199	            continue
   200	        if name.endswith(".en.md"):
   201	            english_structure = heading_structure(path)
   202	            vietnamese_structure = heading_structure(counterpart)
   203	            if english_structure != vietnamese_structure:
   204	                findings.append((path, 0,
   205	                                 "English/Vietnamese heading structure differs: "
   206	                                 f"{english_structure} != {vietnamese_structure}"))
   207	    return findings
   208	
   209	
   210	def heading_structure(path: pathlib.Path) -> list[int]:
   211	    """Return heading levels so translated pairs can be checked without comparing wording."""
   212	    return [len(match.group(1))
   213	            for line in path.read_text().splitlines()
   214	            if (match := re.match(r"^(#{1,6})\s+", line))]
   215	
   216	
   217	def refusal(changed: list) -> list:
   218	    offenders = []
   219	    for f in changed:
   220	        p = pathlib.PurePosixPath(f)
   221	        if SHIPPED_EXCEPTIONS.search(str(p)):
   222	            continue
   223	        if p.suffix in SHIPPED_SUFFIXES:
   224	            offenders.append(f)
   225	    return offenders
   226	
   227	
   228	def main() -> int:
   229	    ap = argparse.ArgumentParser()
   230	    ap.add_argument("files", nargs="*")
   231	    ap.add_argument("--changed-files", nargs="*", default=None)
   232	    ap.add_argument("--require-toc", action="store_true",
   233	                    help="require a complete table of contents (lifecycle deliverables)")
   234	    ap.add_argument("--require-bilingual", action="store_true",
   235	                    help="require matching .en.md and .vi.md lifecycle documents")
   236	    args = ap.parse_args()
   237	
   238	    if args.changed_files is not None:
   239	        offenders = refusal(args.changed_files)
   240	        if offenders:
   241	            print("  ABORT this is development work, not a document work item:")
   242	            for f in offenders:
   243	                print(f"    ships in the build: {f}")
   244	            print("  Route it through dev-lifecycle. Kind: document cannot verify it.")
   245	            return 1
   246	        print(f"  ok   refusal rule: none of {len(args.changed_files)} changed files ship in the build")
   247	        return 0
   248	
   249	    if not args.files:
   250	        print("  FAIL no files given — check the invocation, not the content")
   251	        return 1
   252	
   253	    findings = []
   254	    paths = [pathlib.Path(f) for f in args.files]
   255	    for path in paths:
   256	        findings += check_file(path, require_toc=args.require_toc)
   257	    if args.require_bilingual:
   258	        findings += check_language_pairs(paths)
   259	    for path, line, msg in findings:
   260	        where = f"{path}:{line}" if line else str(path)
   261	        print(f"  FAIL {where} — {msg}")
   262	    print(f"  checked {len(args.files)} documents, {len(findings)} findings")
   263	    return 1 if findings else 0
   264	
   265	
   266	if __name__ == "__main__":
   267	    sys.exit(main())
     1	#!/usr/bin/env python3
     2	"""Fail if a methodology skill drifts back to an error its source review already corrected.
     3	
     4	This repository teaches external methodologies. Every one of them reached the kit through an
     5	LLM's recollection or an LLM-written summary at least once, and every time the result read as
     6	plausible expert advice while contradicting the source. Each such error is cheap to reintroduce
     7	in a one-line edit and expensive to notice, because nothing downstream reads the source.
     8	
     9	Each entry in SOURCES pairs a methodology with the files derived from it and the patterns that
    10	catch its known regressions. Evidence, with the authors' own wording, lives in the
    11	`source_fidelity_review.md` of the epic that introduced the source.
    12	
    13	Add a source by appending to SOURCES — never by forking this script.
    14	"""
    15	from __future__ import annotations
    16	
    17	import pathlib
    18	import re
    19	import sys
    20	
    21	# Evidence documents quote the errors in order to name them as errors. Scanning them would
    22	# report the correction as the regression, so they are never targets.
    23	EXCLUDED_NAMES = {"source_fidelity_review.md"}
    24	
    25	# Each source: name, the globs of files derived from it, and (label, pattern) checks whose
    26	# label states the CORRECT rule, so a failure explains itself without opening another file.
    27	# `required` means the globs must match something — an empty match is a broken glob, not a
    28	# clean bill of health. New sources start unrequired until the skills that use them exist.
    29	SOURCES = [
    30	    {
    31	        "name": "The Lean Product Playbook — Olsen, 2015",
    32	        "evidence": ".devtool/epic/lean_product_suite/source_fidelity_review.md",
    33	        "globs": ["skills/lean-*/**/*.md", "docs/books/*.md"],
    34	        "required": True,
    35	        "checks": [
    36	            (
    37	                "PMF Pyramid has FIVE layers; the Lean Product Process has six STEPS",
    38	                r"(?i)(six|6)[- ]layer\w*\s+(product-market fit\s+)?pyramid"
    39	                r"|pyramid\w*\s+(has|with)\s+(six|6)\s+layers"
    40	                r"|kim tự tháp\s+\w*\s*6 tầng",
    41	            ),
    42	            (
    43	                "Ulwick's bar is > 15; >= 10 is the floor of the UNATTRACTIVE band",
    44	                r"(?i)\bOS\b\s*(>=|≥|\\ge)\s*10"
    45	                r"|opportunity score\s*(>=|≥|\\ge)\s*10",
    46	            ),
    47	            (
    48	                "Figure 7.1 is Jussi Pasanen's; the cupcake metaphor is Brandon Schauer's, not Olsen's",
    49	                r"(?i)cupcake",
    50	            ),
    51	            (
    52	                "MVP membership follows the composition rule, not an ROI rank cut-off",
    53	                r"(?i)cells?\s*1\s*[-–]\s*3|ô\s*1\s*[-–]\s*3",
    54	            ),
    55	            (
    56	                "Guardrail 1 is capture-convert-park; Olsen's rule is separate and alternate, not forbid",
    57	                r"(?i)guardrail 1[^\n]{0,90}\b(ban|banned|forbid|refus\w*|reject\w*)\b",
    58	            ),
    59	        ],
    60	    },
    61	    {
    62	        "name": "Diátaxis — Daniele Procida, diataxis.fr",
    63	        "evidence": ".devtool/epic/document_lifecycle_suite/source_fidelity_review.md",
    64	        "globs": [
    65	            "skills/doc-*/**/*.md",
    66	            ".devtool/epic/document_lifecycle_suite/*.md",
    67	        ],
    68	        "required": True,
    69	        "checks": [
    70	            (
    71	                "Diátaxis axes are action/cognition and acquisition/application, not theory/practice",
    72	                r"(?i)\btheory\s*[/×x]\s*practice\b|\bstudy\s*[/×x]\s*work\b",
    73	            ),
    74	            (
    75	                "Diátaxis has FOUR types: tutorial, how-to guide, reference, explanation",
    76	                r"(?i)(three|five|3|5)\s+diátaxis\s+(mode|type)s?"
    77	                r"|diátaxis[^\n]{0,15}\b(three|five)\s+(mode|type)s?",
    78	            ),
    79	            (
    80	                "Procida: a how-to guide carries 'no digression, explanation, teaching'",
    81	                r"(?i)how-to\s+guides?[^\n]{0,70}\b(should|must|can|may)\b[^\n]{0,20}\b(explain|teach)",
    82	            ),
    83	        ],
    84	    },
    85	    {
    86	        "name": "Documenting Architecture Decisions — Michael Nygard, 2011",
    87	        "evidence": ".devtool/epic/document_lifecycle_suite/source_fidelity_review.md",
    88	        "globs": [
    89	            "skills/decision-records/**/*.md",
    90	            ".devtool/epic/document_lifecycle_suite/*.md",
    91	        ],
    92	        "required": True,
    93	        "checks": [
    94	            (
    95	                "Rejected alternatives come from later ADR templates — Nygard's 2011 article "
    96	                "does not mention them, so do not cite him for that rule",
    97	                r"(?i)(record|document)\w*\s+the\s+rejected\s+alternatives",
    98	            ),
    99	            (
   100	                "Nygard's section order is Title, Context, Decision, Status, Consequences",
   101	                r"(?i)title\s*/\s*status\s*/\s*context",
   102	            ),
   103	            (
   104	                "Nygard: 'All consequences should be listed here, not just the positive ones' "
   105	                "— positive, negative AND neutral",
   106	                r"(?i)consequences[^\n]{0,50}\bonly\s+(the\s+)?positive",
   107	            ),
   108	        ],
   109	    },
   110	]
   111	
   112	# A line that names an error in order to warn against it is the correction working, not a
   113	# regression. Prose wraps, so the disclaimer is looked for in a small window around the match
   114	# rather than on the matching line alone. Keep this list tight: anything it excuses stops
   115	# being checked.
   116	CONTEXT_LINES = 1
   117	
   118	DISCLAIMER = re.compile(
   119	    r"(?i)"
   120	    r"not\s+(a\s+rule|attribut\w*|olsen'?s?|nygard'?s?|procida'?s?|in\s+this\s+book|in\s+the\s+source)"
   121	    r"|does\s+\*\*not\*\*|do\s+not\s+attribut|never\s+attribut|do\s+not\s+cite"
   122	    r"|brandon\s+schauer|wrong|harmful|anti-rule|red flag|\[!WARNING\]|\[!CAUTION\]"
   123	    r"|instead\s+of|rather\s+than|will eventually cut"
   124	    r"|later\s+(adr\s+)?template|this kit'?s own addition|divergence"
   125	    r"|không\s+có\s+trong|không\s+phải|ẩn\s+dụ|của\s+Brandon"
   126	)
   127	
   128	ROOT = pathlib.Path(__file__).resolve().parent.parent
   129	
   130	
   131	def targets_for(source) -> list:
   132	    found = []
   133	    for pattern in source["globs"]:
   134	        found += list(ROOT.glob(pattern))
   135	    return sorted({f for f in found if f.is_file() and f.name not in EXCLUDED_NAMES})
   136	
   137	
   138	def main() -> int:
   139	    bad = 0
   140	    total = 0
   141	
   142	    for source in SOURCES:
   143	        targets = targets_for(source)
   144	        if not targets:
   145	            if source.get("required"):
   146	                print(f"  FAIL {source['name']}: no target files — check the glob, not the content")
   147	                bad = 1
   148	            else:
   149	                print(f"  note {source['name']}: no target files yet — checks pending")
   150	            continue
   151	        total += len(targets)
   152	
   153	        for label, pattern in source["checks"]:
   154	            rx = re.compile(pattern)
   155	            for f in targets:
   156	                lines = f.read_text().split("\n")
   157	                for idx, line in enumerate(lines):
   158	                    if not rx.search(line):
   159	                        continue
   160	                    lo = max(0, idx - CONTEXT_LINES)
   161	                    window = " ".join(lines[lo:idx + CONTEXT_LINES + 1])
   162	                    if DISCLAIMER.search(window):
   163	                        continue
   164	                    rel = f.relative_to(ROOT)
   165	                    print(f"  FAIL {rel}:{idx + 1} — {label}")
   166	                    print(f"       {line.strip()[:110]}")
   167	                    bad = 1
   168	
   169	    rules = sum(len(s["checks"]) for s in SOURCES)
   170	    print(f"  checked {total} files against {rules} source-fidelity rules "
   171	          f"from {len(SOURCES)} sources")
   172	    return bad
   173	
   174	
   175	if __name__ == "__main__":
   176	    sys.exit(main())

exec
/bin/zsh -lc "nl -ba .devtool/epic/token_throttling_optimization/bdd_scenarios.vi.md | sed -n '1,130p'; nl -ba .devtool/epic/token_throttling_optimization/token_throttling_optimization.vi.md | sed -n '1,59p'; nl -ba .devtool/epic/token_throttling_optimization/2026-11-13-token-throttling-optimization-design.vi.md | sed -n '119,132p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	# Kịch Bản BDD Tối Ưu Hóa Tiêu Hao Token
     2	
     3	## Mục lục
     4	
     5	- [Thông tin Meta](#thông-tin-meta)
     6	- [Luồng chính](#luồng-chính)
     7	- [Trường hợp biên và ranh giới](#trường-hợp-biên-và-ranh-giới)
     8	- [Chuyển đổi trạng thái và bất biến](#chuyển-đổi-trạng-thái-và-bất-biến)
     9	- [Bất đồng bộ và đồng thời](#bất-đồng-bộ-và-đồng-thời)
    10	- [Xử lý lỗi và khả năng phục hồi](#xử-lý-lỗi-và-khả-năng-phục-hồi)
    11	
    12	## Thông tin Meta
    13	
    14	- **Epic**: `token_throttling_optimization`
    15	- **Ngôn ngữ gốc**: Tiếng Anh
    16	- **Tiền tố kịch bản**: `TTO`
    17	- **Thư mục tự động hóa**: `tests`
    18	- **Quy tắc**: Mỗi mã kịch bản được gán cho đúng một task và xuất hiện trong một bài kiểm thử tự động.
    19	- **Giả lập (Mocking)**: Các CLI con (`claude`, `codex`, `kiro`, `agy`, `pytest`, `git`) và thao tác ghi đĩa được cô lập hoàn toàn trong thư mục tạm (`tmp_path` / `tempfile.TemporaryDirectory`) với binary giả trên `PATH`.
    20	
    21	## Luồng chính
    22	
    23	```gherkin
    24	Scenario: [TTO-HP-01] [Tier C - Integration] Review ngoài chỉ dùng diff -U5 ở Round 1 và bỏ qua diff base đầy đủ ở Round 2
    25	
    26	Cho một git repository cô lập có epic chứa nhiều commit mã nguồn cùng tài liệu đồng hành .vi.md
    27	Và một mục Round 1 đã được ghi nhận sẵn trong review_results.md cho SHA trước đó
    28	Khi run_external_review.py dựng prompt Round 1 rồi dựng tiếp prompt Round 2 sau một commit sửa lỗi gia tăng
    29	Thì phần diff Round 1 được tạo với ngữ cảnh -U5 và loại bỏ toàn bộ đường dẫn tài liệu *.vi.md
    30	Và prompt Round 2 chứa delta_round_context cho khoảng prev_sha..curr_sha kèm tham chiếu một dòng cumulative diff --stat
    31	Và prompt Round 2 không đính kèm khối diff base...curr_sha đầy đủ trừ khi truyền cờ --full
    32	
    33	Scenario: [TTO-HP-02] [Tier C - Integration] Trình chạy Gate 4 rút gọn chỉ in một dòng GATE_PASS và lưu log đầy đủ vào build/quality
    34	
    35	Cho một dự án có tệp .agents/quality/check_quality.json hợp lệ với các provider thoát bằng mã 0
    36	Khi verify_polyglot_registry.py chạy kèm cờ --compact
    37	Thì đầu ra chuẩn chỉ in các dòng đơn "GATE_PASS: <provider_or_cap>" thay cho các khối JSON dài dòng
    38	Và toàn bộ log chi tiết của từng capability được ghi vào build/quality/<provider>/<cap>.log
    39	Và kết quả tổng hợp cuối cùng trả về PASS
    40	
    41	Scenario: [TTO-HP-03] [Tier C - Integration] Kiểm tra sẵn sàng mặc định Option A chấp nhận sai lệch tạm thời của .vi.md và hoãn bdd_scenarios.vi.md
    42	
    43	Cho một thư mục epic có đầy đủ tài liệu thiết kế *.en.md mới nhất và bdd_scenarios.en.md
    44	Và chưa tồn tại bdd_scenarios.vi.md trong khi một bản .vi.md đồng hành chưa đồng bộ trong lúc Principal Review
    45	Khi check_epic_readiness.py chạy mà không có cờ --strict-bilingual
    46	Thì cổng sẵn sàng trả về PASS trên R1, R3, R7 và không báo lỗi vì lệch .vi.md hay thiếu bdd_scenarios.vi.md
    47	Và check_bdd_traceability.py đối chiếu độ phủ task thuần túy dựa trên bdd_scenarios.en.md
    48	
    49	Scenario: [TTO-HP-04] [Tier A - Unit] RunnerConfig phân giải model và effort cho Role 2.3 theo thứ tự ưu tiên cấu hình
    50	
    51	Cho tệp .devtool/review_config.json cấu hình providers.programmer.model là "gemini-4-hydrogen-xhigh" và thinking_level là "extra"
    52	Và biến môi trường AGY_PROGRAMMER_MODEL chưa được đặt
    53	Khi lifecycle_runner.RunnerConfig phân giải model và effort lập trình viên mà không truyền cờ CLI
    54	Thì resolve_programmer_model trả về "gemini-4-hydrogen-xhigh" và resolve_programmer_effort trả về "xhigh"
    55	Và truyền cờ --programmer-model "gemini-4-pro-high" qua CLI ghi đè cả .devtool/review_config.json lẫn biến môi trường
    56	
    57	Scenario: [TTO-HP-05] [Tier C - Integration] Quy tắc và kỹ năng đã tinh gọn đáp ứng ngưỡng byte và các kiểm tra hợp đồng phát hành
    58	
    59	Cho các tệp rules/CRITICAL_RULES.md, skills/dev-designer/SKILL.md và skills/task-observer/SKILL.md đã cập nhật trong repository
    60	Khi chạy scripts/test_lifecycle_document_contract.py và đo kích thước byte trên đĩa
    61	Thì rules/CRITICAL_RULES.md có dung lượng tối đa 8192 bytes và chứa quy tắc Zero-Fluff Output Cap
    62	Và skills/dev-designer/SKILL.md có dung lượng tối đa 22528 bytes đồng thời giữ đủ các mục bắt buộc và liên kết tới references trích xuất
    63	Và skills/task-observer/SKILL.md chứa chỉ thị <SUBAGENT-STOP> ngăn gọi trong subagent và worker chạy nền
    64	Và scripts/test_lifecycle_document_contract.py thoát với mã 0 và không có lỗi khẳng định nào
    65	
    66	Scenario: [TTO-HP-06] [Tier C - Integration] Khôi phục ngữ cảnh rút gọn giới hạn tối đa 4096 bytes và đọc động cấu hình programmer
    67	
    68	Cho workspace đa repo có metadata epic đang chạy, danh sách task và các RFC đang mở
    69	Và .devtool/review_config.json đặt providers.programmer là "gemini-4-hydrogen-xhigh" với thinking_level "xhigh"
    70	Khi scripts/resume_context.py chạy với --compact --epic token_throttling_optimization và --emit-prompt implement
    71	Thì payload ngữ cảnh rút gọn có dung lượng tối đa 4096 bytes gồm ảnh chụp nhanh epic, trạng thái git repo hiện tại, các task khớp epic và RFC liên quan
    72	Và prompt bàn giao được sinh ra hiển thị đúng "gemini-4-hydrogen-xhigh" và "xhigh" đọc động từ .devtool/review_config.json
    73	
    74	Scenario: [TTO-HP-07] [Tier C - Integration] Vòng Cross-model review tối ưu đi thẳng vào sửa mã rõ ràng và điền kết quả thật vào Executive Report
    75	
    76	Cho một kết luận CHANGES_REQUIRED ở Round 1 chỉ gồm các lỗi mã nguồn đã xác minh và không xung đột shared-contracts
    77	Khi lifecycle_runner.step_cross_model_review chạy một vòng khắc phục rồi hội tụ
    78	Thì các lỗi mã nguồn rõ ràng bỏ qua _draft_fix_plan và evaluate_programmer_fix_plan để đi thẳng vào _apply_code_fixes
    79	Và render_final_executive_report điền bảng Top 3 Highest-Risk Findings trực tiếp từ dữ liệu phân tích trong review_results.md và principal_review.md thay cho chuỗi giữ chỗ
    80	
    81	Scenario: [TTO-HP-08] [Tier C - Integration] Đường ống tối ưu token đầu-cuối áp dụng đồng bộ prompt gọn, cô lập review và cấu hình programmer
    82	
    83	Cho một workspace epic cô lập được khởi tạo cùng .devtool/review_config.json, các tệp task có vùng dòng mục tiêu và bộ CLI review/agy giả lập
    84	Khi đường ống lifecycle thực thi lần lượt kiểm tra sẵn sàng, review ngoài, điều phối worker, Gate 4 rút gọn và báo cáo tổng kết
    85	Thì mọi prompt review đều tuân thủ ngân sách diff-only -U5 và tách log thô ra khỏi tài liệu markdown
    86	Và mọi prompt worker đều bỏ qua việc nhúng toàn văn tệp nguồn đồng thời gọi gemini-4-hydrogen-xhigh với --effort xhigh
    87	Và Gate 4 rút gọn chỉ xuất các dòng trạng thái GATE_PASS khi mọi kiểm tra đạt chuẩn
    88	```
    89	
    90	## Trường hợp biên và ranh giới
    91	
    92	```gherkin
    93	Scenario: [TTO-EC-01] [Tier A - Unit] Diff vượt ngân sách tự động cắt gọn về bảng --stat kèm tiêu đề hunk @@ theo từng tệp
    94	
    95	Cho một git diff giả lập vượt quá MAX_DIFF_LINES (1500 dòng) hoặc MAX_DIFF_BYTES (60000 bytes)
    96	Khi build_diff_section dựng phần nội dung diff cho review ngoài
    97	Thì chuỗi trả về nằm gọn trong ngân sách byte mà vẫn giữ nguyên ranh giới cấu trúc từng tệp
    98	Và phần nội dung rút gọn bao gồm rõ ràng thống kê git diff --stat kèm tiêu đề tệp và các dòng tiêu đề hunk @@ của tệp thay đổi
    99	
   100	Scenario: [TTO-EC-02] [Tier A - Unit] Trình chạy task giới hạn đuôi 25 dòng và cấu hình Python chèn bộ cờ pytest yên lặng
   101	
   102	Cho đầu ra thất bại của một lệnh kiểm tra task gồm 120 dòng stdout/stderr
   103	Và .agents/quality/python-quality.json cùng manifest được sinh từ scaffold_quality_manifest.py
   104	Khi run_task_checks.py định dạng bằng chứng lỗi và lệnh kiểm thử Python được kiểm tra
   105	Thì run_task_checks.TAIL_LINES bằng 25 và đoạn trích xuất chỉ giữ lại 25 dòng khác rỗng cuối cùng
   106	Và cả .agents/quality/python-quality.json lẫn manifest Python mới sinh đều gọi pytest kèm "-q", "--tb=short" và "--maxfail=3"
   107	
   108	Scenario: [TTO-EC-03] [Tier C - Integration] Trình kiểm tra hợp đồng thiết kế từ chối tệp đã theo dõi trên 200 dòng thiếu ký hiệu hoặc vùng dòng
   109	
   110	Cho một tệp task tham chiếu tệp mã nguồn Python không phải tệp mới dài hơn 200 dòng trong Allowed files
   111	Và các mục Files và Impact Analysis của task bỏ sót tên symbol mục tiêu hoặc vùng dòng (L<start>-L<end>) cho tệp đó
   112	Khi check_task_contract.py chạy kèm cờ --design trên tệp task
   113	Thì check_task_contract.py thoát khác 0 và báo lỗi thiếu symbol hoặc vùng dòng cho tệp >200 dòng đó
   114	Và bổ sung neo hợp lệ "path :: Symbol (L10-L85)" sẽ xóa bỏ vi phạm và trả về mã thoát 0
   115	
   116	Scenario: [TTO-EC-04] [Tier A - Unit] Chuẩn hóa effort của programmer ánh xạ các biến thể "extra" thành xhigh
   117	
   118	Cho các giá trị effort thô "extra", "EXTRA", "extra-high", "extra_high" và "xhigh"
   119	Khi lifecycle_runner.normalize_agy_effort chuẩn hóa từng mức cấu hình
   120	Thì mọi biến thể đều trả về giá trị chuẩn "xhigh"
   121	Và trình dựng lệnh agy đưa cặp tham số "--effort", "xhigh" vào danh sách đối số
   122	
   123	Scenario: [TTO-EC-05] [Tier C - Integration] Cơ chế lọc task-reviewer bỏ qua task đơn giản và kích hoạt trên task rủi ro cao hoặc đa module
   124	
   125	Cho một task tài liệu hoặc tiện ích một tệp thông thường không gắn nhãn rủi ro cao và chưa đặt review_tier
   126	Và một task phức tạp có review_tier: "full" hoặc nhãn ["security", "concurrency"] hoặc sửa 3 module không phải test
   127	Khi áp dụng tiêu chí chọn lọc task-reviewer được định nghĩa trong dev-designer, dev-implementation và subagent-driven-development
   128	Thì task một tệp đơn giản bỏ qua lượt subagent task-reviewer dư thừa
   129	Và task phức tạp hoặc rủi ro cao bắt buộc kích hoạt lượt kiểm duyệt task-reviewer chuyên biệt trước khi chốt task
   130	
     1	# Thiết kế Cấp cao: Tối ưu hóa Token toàn diện (HLD)
     2	
     3	## Mục lục
     4	
     5	- [Meta Data](#meta-data)
     6	- [Bối cảnh](#bối-cảnh)
     7	- [Mục tiêu và Phi mục tiêu](#mục-tiêu-và-phi-mục-tiêu)
     8	- [Kiến trúc và Thiết kế Kỹ thuật](#kiến-trúc-và-thiết-kế-kỹ-thuật)
     9	- [Bản đồ Bảo trì Tính năng](#bản-đồ-bảo-trì-tính-năng)
    10	- [Hợp đồng Module và Giao diện CLI](#hợp-đồng-module-và-giao-diện-cli)
    11	- [Phân tích Tác động](#phân-tích-tác-động)
    12	- [Tác động Shared Contract](#tác-động-shared-contract)
    13	- [Kế hoạch Kiểm thử Tích hợp và Ma trận Ranh giới](#kế-hoạch-kiểm-thử-tích-hợp-và-ma-trận-ranh-giới)
    14	- [Môi trường Kiểm thử](#môi-trường-kiểm-thử)
    15	- [Phạm vi Kịch bản BDD toàn diện](#phạm-vi-kịch-bản-bdd-toàn-diện)
    16	- [Chiến lược Triển khai và Giảm thiểu Rủi ro](#chiến-lược-triển-khai-và-giảm-thiểu-rủi-ro)
    17	- [Phân rã Kanban Tasks](#phân-rã-kanban-tasks)
    18	- [Đính chính Đặc tả](#đính-chính-đặc-tả)
    19	
    20	## Meta Data
    21	
    22	- **Epic name**: `token_throttling_optimization`
    23	- **Status**: Draft
    24	- **PIC**: `danhdue`
    25	- **Target release**: Next plugin release
    26	- **Platform**: Python tooling and agent workflow kit
    27	- **Depends on epic**: none
    28	- **Source Spec**: [Đặc tả Thiết kế Tối ưu hóa Token được Phê duyệt](2026-11-13-token-throttling-optimization-design.vi.md)
    29	
    30	## Bối cảnh
    31	
    32	Đo kiểm thực tế trên `dev-lifecycle` (cả Interactive và `--autonomous`) cho thấy context phình theo hàm bậc hai và cạn quota 5 giờ nhanh chóng do 5 nguyên nhân kết hợp:
    33	
    34	1. **Chi phí nền cố định**: `rules/CRITICAL_RULES.md` (`32,773` bytes / `239` dòng) vượt ngưỡng cắt của IDE (`<truncated 8848 bytes>`), `skills/task-observer/SKILL.md` (`31,480` bytes) nạp vào mọi subagent/CLI mà thiếu thẻ chặn, và `scripts/resume_context.py` đổ `26,759` bytes qua tất cả repo.
    35	2. **Phình Context bậc hai khi External Review**: `run_external_review.py` truyền lặp full diff `base...sha` cùng `delta_round_context()` từ Round `2+`, kèm dư thừa các file `*.vi.md`, đổ toàn văn output `fact()` khi `exit 0`, dùng `-U10` trong `review-package`, và nhúng nguyên `stderr` CLI vào `principal_review.md` (tới `1.88 MB`).
    36	3. **Quality Gates quá dài và không cắt traceback**: `verify_polyglot_registry.py` in nguyên JSON khi `PASS`; `.agents/quality/python-quality.json` và `scaffold_quality_manifest.py` thiếu `-q --tb=short --maxfail=3`; `run_task_checks.py` giữ `40` dòng; `lifecycle_runner.py` và `verify.sh` thiếu chế độ compact và cắt 25 dòng cuối khi lỗi.
    37	4. **Đọc thô, Chạy tuần tự và Hardcode Model cũ**: Task thiếu neo symbol/dải dòng cho file >200 dòng; `lifecycle_runner.py` gọi `agy` tuần tự với prompt dán nội dung và hardcode `gemini-3.8-flash` thay vì đọc config `gemini-4-hydrogen-xhigh` (`--effort xhigh`); `step_cross_model_review()` gọi thừa 3 lượt LLM cho bug code thuần `Valid`; `task-reviewer` chạy cả cho task nhỏ.
    38	5. **Dịch lại Song ngữ nhiều lần**: Phải duy trì Spec, HLD và Gherkin `.vi.md` song song suốt các vòng Principal Review trước khi bản tiếng Anh hội tụ.
    39	
    40	## Mục tiêu và Phi mục tiêu
    41	
    42	### Mục tiêu
    43	
    44	- Áp dụng cơ học 5 Quy tắc siết Token trên toàn bộ runner scripts, công cụ verification, prompts, rules và skills ở cả Phase 1 (scripts cơ học) và Phase 2 (slimming, khử trùng lặp, task schema).
    45	- Triển khai Luồng Song ngữ Option A: giữ Spec và HLD `.vi.md` để con người review tại Gate 1/2, loại bỏ mọi `*.vi.md` khỏi luồng AI review/coding, mặc định dung sai trôi `.vi.md` & hoãn `bdd_scenarios.vi.md` trong `check_epic_readiness.py`, và đồng bộ một lần ở Stage 4 Pre-Finish với `--strict-bilingual`.
    46	- Kích hoạt `task-reviewer` chọn lọc chỉ cho task rủi ro cao hoặc chạm nhiều module (`review_tier: "full"`, labels `security|architecture|concurrency|contract`, hoặc `> 2` module non-test).
    47	- Cấu hình Role 2.3 (AI Programmer) qua `.devtool/review_config.json["providers"]["programmer"]` và thứ tự ưu tiên trên `RunnerConfig`, nâng mặc định lên `gemini-4-hydrogen-xhigh` và ánh xạ effort (`"extra"` / `"extra-high"` / `"xhigh"` -> `--effort xhigh`).
    48	- Áp đặt giới hạn kích thước đo được (`CRITICAL_RULES.md <= 8192` bytes, `dev-designer/SKILL.md <= 22528` bytes, `resume_context.py --compact --epic <slug> <= 4096` bytes) và giữ nguyên toàn bộ kiểm định phát hành (`scripts/verify.sh --full`).
    49	
    50	### Phi mục tiêu
    51	
    52	- Bỏ qua hoặc tự duyệt thay con người tại Gate 1 (Spec), Gate 2 (Task Breakdown), Gate 5 (Finish và Merge).
    53	- Tắt full test suite hay `@quality_check` ở Final Convergence Gate và Stage 4 `verify-tier`.
    54	- Tự động push commit hoặc branch khi chưa có lệnh xác nhận rõ ràng của người dùng.
    55	- Thay đổi nhãn hiển thị quota bucket (`Gemini 3.8 / Pro 5H`) trong `scripts/agy_quota.py` và `quota_dashboard.html`.
    56	
    57	## Kiến trúc và Thiết kế Kỹ thuật
    58	
    59	### Kiến trúc Tổng quan
   119	## 5. Chiến lược Kiểm thử và Bất biến của Kit
   120	
   121	- Bảo toàn toàn bộ kiểm định phát hành bằng `bash scripts/verify.sh --full` (`42+` suite, JSON manifest, YAML frontmatter, relative links, ToC anchors, Section 7 methodology fidelity, Section 8 unreferenced supporting files, và `scripts/test_lifecycle_document_contract.py`).
   122	- Bổ sung unit & integration tests cho:
   123	  - `test_run_external_review.py`: ngữ cảnh diff `-U5`, không lặp `base...sha` ở Round 2, quiet `collect_facts()`, loại trừ `.vi.md` và tách `stderr` transcript ra `build/reviews/`.
   124	  - `test_lifecycle_runner.py`: silent Gate 4 pass / cắt đuôi 25 dòng lỗi, worker pool parallel dispatch, fix loop tinh gọn cho code bug, `render_final_executive_report()` đọc findings thật, và thứ tự ưu tiên `resolve_programmer_model()` / `resolve_programmer_effort()` kèm ánh xạ `"extra"` -> `"xhigh"`.
   125	  - `test_check_epic_readiness.py` và `test_integrate_branch.py`: Option A hoãn `bdd_scenarios.vi.md` ở Stage 2/Review vs `--strict-bilingual` ở Stage 4 Finish, và check dải dòng trong `check_task_contract.py`.
   126	  - `test_resume_context.py` và `test_aggregate_quality_results.py`: output `--compact` theo epic, `emit_handoff_prompt` lấy Programmer model từ config và định dạng `GATE_PASS:`.
   127	- Đo kiểm định lượng trước/sau cho dung lượng `CRITICAL_RULES.md`, `dev-designer/SKILL.md`, `resume_context.py --epic <slug> --compact` và kích thước artefact `principal_review.md`.
   128	
   129	## 6. Cảnh báo Shared Contract
   130	
   131	Repository `ai-agent-tools` không chứa thư mục `shared-contracts/` (đây là bộ workflow kit độc lập, không phải Hub/Satellite dịch vụ). Mọi hợp đồng CLI nội bộ giữa `run_external_review.py`, `check_epic_readiness.py`, `verify_polyglot_registry.py`, `resume_context.py`, `lifecycle_runner.py` và `integrate_branch.py` cùng schema `.devtool/review_config.json` được giữ tương thích ngược thông qua cờ mặc định và giá trị fallback tùy chọn.
   132	

exec
/bin/zsh -lc 'env PYTHONDONTWRITEBYTECODE=1 mypy --no-incremental --cache-dir=/dev/null skills/dev-lifecycle/resources/scripts/lifecycle_runner.py skills/dev-implementation/resources/scripts/manage_worker_pool.py' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
exec
/bin/zsh -lc 'env PYTHONDONTWRITEBYTECODE=1 mypy --no-incremental --cache-dir=/dev/null skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/package_epic.py scripts/resume_context.py' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 139ms:
Success: no issues found in 2 source files

 succeeded in 238ms:
Success: no issues found in 5 source files

codex
Source cho thấy `_has_domain_or_critical_conflict()` chỉ dò một số chuỗi hẹp; nó chưa nhận diện trực tiếp đường dẫn `shared-contracts/` hoặc nội dung mơ hồ về kiến trúc. Vì Task 4 dự kiến dùng helper này để cho phép sửa thẳng, tôi sẽ probe các trường hợp đó và kiểm tra thêm luồng chuyển bilingual sang Stage 4.

exec
/bin/zsh -lc "rg -n 'bilingual|bdd_scenarios.vi|Gemini Flash 3.8|gemini-3.8-flash|task-reviewer|implementer-prompt' skills/dev-lifecycle skills/dev-implementation/SKILL.md skills/dev-brainstorming skills/subagent-driven-development scripts/resume_context.py scripts/test_resume_context.py scripts/test_verifiable_handoff_text.py rules/CRITICAL_RULES.md; nl -ba skills/dev-implementation/resources/scripts/package_epic.py | sed -n '211,305p'; nl -ba scripts/resume_context.py | sed -n '1271,1337p;1665,1750p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
rules/CRITICAL_RULES.md:178:>      - Activated for `/dev-implementation` and task execution inside isolated git worktrees. Defaults to Model **Gemini Flash 3.8** (`--effort high --mode auto`).
scripts/resume_context.py:1294:You are acting as the AI Programmer (Role 2.3 — Senior TDD Software Engineer | Recommended Model: Gemini Flash 3.8).
scripts/test_verifiable_handoff_text.py:72:        self.assert_present(SDD + "implementer-prompt.md", (
scripts/test_verifiable_handoff_text.py:76:        self.assert_absent(SDD + "implementer-prompt.md",
scripts/test_verifiable_handoff_text.py:78:        self.assert_present(SDD + "task-reviewer-prompt.md", (
skills/dev-implementation/SKILL.md:201:In Autonomous Mode (`/dev-lifecycle --autonomous`), `lifecycle_runner.py` dispatches Role 2.3 (AI Programmer: `gemini-3.8-flash --effort high --mode auto`) in an isolated process group (`start_new_session=True`) with SIGTERM/SIGKILL supervision, per-task logs, and commits (`[<EPIC_NAME>] Execute <task_slug>`).
skills/dev-brainstorming/SKILL.md:203:    --require-toc --require-bilingual \
skills/dev-lifecycle/SKILL.md:25:3. **Stage 3 (Automated Execution & Audit)**: Role 2.3 (**Gemini Flash 3.8**) -> `dev-implementation` -> Automated Gate 3 (execution order & worktree) -> TDD in worktree -> Gate 4 local PASS -> Automated Cross-Model Review (`review_config.json`, Auto-fix up to Max 3 rounds) -> Gate 4 re-verification green.
skills/subagent-driven-development/SKILL.md:67:        "Dispatch implementer subagent (./implementer-prompt.md)" [shape=box];
skills/subagent-driven-development/SKILL.md:71:        "Generate review package, dispatch task reviewer (./task-reviewer-prompt.md)" [shape=box];
skills/subagent-driven-development/SKILL.md:93:    "Setup: worktree, ledger check, read plan, pre-flight review" -> "Dispatch implementer subagent (./implementer-prompt.md)";
skills/subagent-driven-development/SKILL.md:94:    "Dispatch implementer subagent (./implementer-prompt.md)" -> "Implementer asks questions?";
skills/subagent-driven-development/SKILL.md:98:    "Implementer implements, tests, commits (or records verify, uncommitted), self-reviews" -> "Generate review package, dispatch task reviewer (./task-reviewer-prompt.md)";
skills/subagent-driven-development/SKILL.md:99:    "Generate review package, dispatch task reviewer (./task-reviewer-prompt.md)" -> "Spec ✅ and quality approved?";
skills/subagent-driven-development/SKILL.md:116:    "More tasks remain?" -> "Dispatch implementer subagent (./implementer-prompt.md)" [label="yes"];
skills/subagent-driven-development/SKILL.md:274:  the implementer and the task-reviewer dispatch alike. Exact values (numbers,
skills/subagent-driven-development/SKILL.md:298:Template: [implementer-prompt.md](implementer-prompt.md)
skills/subagent-driven-development/SKILL.md:370:Template: [task-reviewer-prompt.md](task-reviewer-prompt.md)
skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:47:    programmer_model: str = "gemini-3.8-flash"
skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:1381:    parser.add_argument("--programmer-model", default="gemini-3.8-flash", help="Model for Programmer")
skills/dev-lifecycle/references/autonomous-mode.md:9:3. **AI Programmer (Role 2.3)**: Executes implementation tasks and applies code fixes inside isolated git worktrees. Defaults to `gemini-3.8-flash` with `--effort high --mode auto`. Never alters architectural boundaries without approved fix plans.
skills/dev-lifecycle/references/autonomous-mode.md:27:- `--programmer-model <model>`: Model identifier for AI Programmer (default: `gemini-3.8-flash`).
   211	def package_epic(
   212	    root: Path,
   213	    epic_dir: str,
   214	    *,
   215	    revise: bool = False,
   216	    reason: str = "",
   217	    base_branch: str | None = None,
   218	    open_notes: list[str] | None = None,
   219	    force: bool = False,
   220	) -> Path:
   221	    epic_path = root / ".devtool" / "epic" / epic_dir
   222	    if not epic_path.is_dir():
   223	        raise FileNotFoundError(f"Epic directory not found: {epic_path}")
   224	
   225	    handoff_file = epic_path / "handoff.md"
   226	    if revise and not handoff_file.is_file():
   227	        raise ValueError("handoff.md does not exist; run without --revise first")
   228	    if not revise and handoff_file.is_file() and not force:
   229	        raise ValueError(
   230	            f"handoff.md already exists for epic '{epic_dir}'. "
   231	            "Use --revise --reason \"<text>\" to update an existing handoff record, "
   232	            "or --force to overwrite."
   233	        )
   234	
   235	    # 1. Run check_epic_readiness.py
   236	    readiness_proc = subprocess.run(
   237	        [sys.executable, str(READINESS_SCRIPT), epic_dir],
   238	        cwd=root,
   239	        capture_output=True,
   240	        text=True,
   241	        check=False,
   242	    )
   243	    if readiness_proc.returncode != 0:
   244	        if readiness_proc.stdout:
   245	            sys.stderr.write(readiness_proc.stdout)
   246	        if readiness_proc.stderr:
   247	            sys.stderr.write(readiness_proc.stderr)
   248	        raise RuntimeError("Epic readiness check failed; cannot package epic.")
   249	
   250	    # 2. Resolve design commit SHA
   251	    res_sha = subprocess.run(
   252	        ["git", "rev-parse", "--short", "HEAD"],
   253	        cwd=root,
   254	        capture_output=True,
   255	        text=True,
   256	        check=False,
   257	    )
   258	    design_commit = (
   259	        res_sha.stdout.strip()
   260	        if res_sha.returncode == 0 and res_sha.stdout.strip()
   261	        else "uncommitted"
   262	    )
   263	
   264	    today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
   265	    resolved_base = resolve_base_branch(root, epic_dir, base_branch)
   266	
   267	    epic_slug = (
   268	        find_epic_slug(root, epic_dir)
   269	        if find_epic_slug is not None
   270	        else epic_dir.replace("_", "-")
   271	    ) or epic_dir.replace("_", "-")
   272	
   273	    if not revise:
   274	        update_epic_status_to_packaged(root, epic_dir, today_iso)
   275	        tpl = TEMPLATE_PATH
   276	        if not tpl.is_file():
   277	            tpl = root / "skills" / "dev-lifecycle" / "references" / "handoff-template.md"
   278	        if not tpl.is_file():
   279	            raise FileNotFoundError(f"handoff-template.md not found at {TEMPLATE_PATH}")
   280	        content = render_initial_handoff(
   281	            tpl,
   282	            epic_dir,
   283	            epic_slug,
   284	            design_commit,
   285	            resolved_base,
   286	            today_iso,
   287	            open_notes=open_notes,
   288	        )
   289	        handoff_file.write_text(content, encoding="utf-8")
   290	    else:
   291	        existing = handoff_file.read_text(encoding="utf-8")
   292	        revised = revise_handoff_text(
   293	            existing,
   294	            design_commit,
   295	            reason,
   296	            today_iso,
   297	        )
   298	        handoff_file.write_text(revised, encoding="utf-8")
   299	
   300	    return handoff_file
   301	
   302	
   303	def main() -> None:
   304	    parser = argparse.ArgumentParser(
   305	        description="Packaged epic packaging and revision tool."
  1271	def emit_handoff_prompt(
  1272	    mode: str,
  1273	    epic_slug: str,
  1274	    epic_dir: str | None = None,
  1275	    custom_prompt: str | None = None,
  1276	) -> None:
  1277	    target_dir = epic_dir or epic_slug
  1278	    prompt_note = f"\nNote: {custom_prompt}\n" if custom_prompt else ""
  1279	
  1280	    if mode == "principal-review":
  1281	        banner = "[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]"
  1282	        print(f"""{banner}
  1283	You are acting as the AI Assistant (Role 2.2 — Technical Advisor & Reviewer).
  1284	Startup command:
  1285	python3 scripts/resume_context.py --role assistant --epic {epic_slug}
  1286	
  1287	MANDATORY TASKS & RULES:
  1288	1. Thoroughly review the HLD at .devtool/epic/{target_dir}/{target_dir}.en.md and bdd_scenarios.en.md.
  1289	2. Conduct an independent Principal Review following the `d3nexus:principal-review` skill (Provider priority via `check-quota`: Claude -> Codex -> Kiro -> Argon; 3-Round Convergence Funnel, max 3 rounds).
  1290	3. DO NOT modify production source code or application test suites (only design documents and Kanban tasks).{prompt_note}""")
  1291	    elif mode == "implement":
  1292	        banner = "[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]"
  1293	        print(f"""{banner}
  1294	You are acting as the AI Programmer (Role 2.3 — Senior TDD Software Engineer | Recommended Model: Gemini Flash 3.8).
  1295	Startup command:
  1296	python3 scripts/resume_context.py --role programmer --epic {epic_slug}
  1297	
  1298	MANDATORY TASKS & RULES:
  1299	1. Activate `/dev-implementation` (`d3nexus:dev-implementation`) for the `{epic_slug}` epic.
  1300	2. Read `.devtool/epic/{target_dir}/handoff.md` first.
  1301	3. Strictly apply the 4 Execution Guardrails (Bounded context protocol, Strict spec fidelity, Zero test fakery, No contract repair).
  1302	4. Sequentially execute each Kanban task following the TDD cycle (Red-Green-Refactor, Level 1 Task-Scoped checks) in an isolated git worktree.{prompt_note}""")
  1303	    elif mode == "cross-review":
  1304	        banner = "[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]"
  1305	        print(f"""{banner}
  1306	You are acting as the AI Assistant (Role 2.2 — Technical Advisor & Reviewer).
  1307	Startup command:
  1308	python3 scripts/resume_context.py --role assistant --epic {epic_slug}
  1309	
  1310	MANDATORY TASKS & RULES:
  1311	1. Gate 4 has PASSED. Activate `d3nexus:cross-model-review`.
  1312	2. Run independent external model review (`run_external_review.py run`, Provider priority via `check-quota`: Claude -> Codex -> Kiro -> Argon; 3-Round Convergence Funnel, max 3 rounds).
  1313	3. Evaluate Auto-Triage Gate and triage findings before fixing defects or proceeding to finish.{prompt_note}""")
  1314	    elif mode == "finish":
  1315	        banner = "[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]"
  1316	        print(f"""{banner}
  1317	You are acting as the AI Programmer (Role 2.3 — Senior TDD Software Engineer).
  1318	Startup command:
  1319	python3 scripts/resume_context.py --role programmer --epic {epic_slug}
  1320	
  1321	MANDATORY TASKS & RULES:
  1322	1. Activate `d3nexus:finishing-a-development-branch` for the `{epic_slug}` epic.
  1323	2. Execute Pre-Finish Hook: `python3 scripts/resume_context.py --complete {epic_slug} "<milestone_summary>"`.
  1324	3. Verify branch integration and clean up the worktree.{prompt_note}""")
  1325	    elif mode == "assistant":
  1326	        banner = "[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]"
  1327	        print(f"""{banner}
  1328	You are acting as the AI Assistant (Role 2.2 — Technical Advisor & Co-Architect).
  1329	Startup command:
  1330	python3 scripts/resume_context.py --role assistant --epic {epic_slug}
  1331	
  1332	MANDATORY TASKS & RULES:
  1333	1. Engage in technical discussion, root cause analysis (RCA), and solution trade-off evaluation.
  1334	2. STRICTLY PROHIBITED from modifying production code in this mode.
  1335	3. Persist discussion takeaways anytime via `python3 scripts/resume_context.py --state --epic {epic_slug} --decisions "<conclusions>"`.{prompt_note}""")
  1336	    else:
  1337	        print(f"Unknown prompt mode: {mode}")
  1665	def main() -> None:
  1666	    args = parse_args()
  1667	    workspace = resolve_workspace_root(args.workspace_root)
  1668	    primary_repo = resolve_primary_repo_root()
  1669	    current_worktree = resolve_current_worktree_root()
  1670	    active_repo = args.repo or (
  1671	        primary_repo.name if primary_repo != workspace else "workspace"
  1672	    )
  1673	
  1674	    is_repo = (primary_repo / ".git").exists() or (primary_repo / ".devtool").exists()
  1675	    if args.workspace_root:
  1676	        target_root = resolve_workspace_root(args.workspace_root)
  1677	    elif args.repo:
  1678	        primary_parent = primary_repo.parent
  1679	        repo_candidate = primary_parent / args.repo
  1680	        if repo_candidate.exists():
  1681	            target_root = repo_candidate
  1682	        elif (workspace / args.repo).exists():
  1683	            target_root = workspace / args.repo
  1684	        else:
  1685	            target_root = primary_repo if is_repo else workspace
  1686	    elif is_repo:
  1687	        target_root = primary_repo
  1688	    else:
  1689	        target_root = workspace
  1690	
  1691	    title_target = (
  1692	        resolve_workspace_root(args.workspace_root)
  1693	        if args.workspace_root
  1694	        else (target_root if args.repo else current_worktree)
  1695	    )
  1696	    active_epic = args.epic or resolve_current_epic_slug(title_target)
  1697	
  1698	    if args.role:
  1699	        print_role_banner(args.role)
  1700	
  1701	    if args.emit_prompt:
  1702	        emit_handoff_prompt(args.emit_prompt, active_epic, args.epic_dir, args.prompt)
  1703	        return
  1704	
  1705	    if args.sync_zshrc:
  1706	        r_home = Path(args.real_home) if args.real_home else None
  1707	        ws_root = Path(args.workspace_root) if args.workspace_root else None
  1708	        res = sync_shell_env(real_home=r_home, workspace_root=ws_root)
  1709	        print(f"Shell environment synchronized: {res}")
  1710	        return
  1711	
  1712	    if args.sync_title:
  1713	        if getattr(args, "all_repos", False):
  1714	            base_dir = (
  1715	                target_root.parent
  1716	                if (target_root.parent / "ai-agent-tools").exists()
  1717	                else _real_home() / "AllProjects"
  1718	            )
  1719	            for rname in REPOS:
  1720	                rpath = base_dir / rname
  1721	                if rpath.exists():
  1722	                    sync_window_title(
  1723	                        rpath,
  1724	                        epic_slug=active_epic,
  1725	                        stage_override=args.stage,
  1726	                        profile_override=args.profile or None,
  1727	                    )
  1728	                    print(
  1729	                        f"Window title and workspace bar colors synchronized for {rpath.name}"
  1730	                    )
  1731	            return
  1732	        sync_window_title(
  1733	            title_target,
  1734	            epic_slug=active_epic,
  1735	            stage_override=args.stage,
  1736	            profile_override=args.profile or None,
  1737	        )
  1738	        print(
  1739	            f"Window title and workspace bar colors synchronized for {title_target.name}"
  1740	        )
  1741	        return
  1742	
  1743	    if args.complete:
  1744	        slug = args.complete[0]
  1745	        summary = (
  1746	            " ".join(args.complete[1:])
  1747	            if len(args.complete) > 1
  1748	            else "Completed feature and verified contracts."
  1749	        )
  1750	        complete_feature_and_rotate(

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/audit_epic.py | sed -n '170,275p'; nl -ba skills/finishing-a-development-branch/resources/scripts/integrate_branch.py | sed -n '245,305p;525,630p'; nl -ba skills/dev-implementation/resources/scripts/test_check_epic_readiness.py | sed -n '1,95p'; nl -ba skills/dev-implementation/resources/scripts/test_run_external_review.py | sed -n '1,75p'; nl -ba scripts/test_lifecycle_document_contract.py | sed -n '1,165p;329,410p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
   170	def audit_protected(root: Path, epic_path: str, commits: list[Commit], texts: dict[str, str]) -> tuple[list[str], bool]:
   171	    explicit = parse_protected_paths(show(root, "HEAD", f"{epic_path}/{Path(epic_path).name}.en.md") or "")
   172	    programs: set[str] = set()
   173	    allowed: set[str] = set()
   174	    for text in texts.values():
   175	        allowed.update(entry.pattern for entry in parse_allowed_files(text))
   176	        try:
   177	            programs.update(p for p in (program_of(row.command, root) for row in parse_verification(text)[0]) if p)
   178	        except ContractError:
   179	            continue
   180	    items: list[str] = []
   181	    failed = False
   182	    for commit in commits:
   183	        for path in commit.paths:
   184	            if path not in programs and not any(path_matches(pattern, path) for pattern in explicit):
   185	                continue
   186	            unauthorised = not path.startswith(".devtool/") and path not in allowed
   187	            items.append(f"{commit.short} {path}" + (" — unauthorised" if unauthorised else ""))
   188	            failed = failed or unauthorised
   189	    return items, failed
   190	
   191	
   192	def grader_text(text: str) -> list[str]:
   193	    covers = [line for line in text.splitlines() if COVERS_LINE.match(line)]
   194	    allowed = [f"`{entry.pattern}`" + (" (new)" if entry.new else "") for entry in parse_allowed_files(text)]
   195	    return (["# Verification"] + (section(text, "Verification") or "").splitlines()
   196	            + ["# Definition of Done"] + (section(text, "Definition of Done") or "").splitlines()
   197	            + ["# Allowed files"] + allowed + ["# Covers"] + covers)
   198	
   199	
   200	def scenario_ids_at(root: Path, rev: str, path: str) -> set[str]:
   201	    text = show(root, rev, path)
   202	    if text is None:
   203	        return set()
   204	    with tempfile.TemporaryDirectory() as scratch:
   205	        copy = Path(scratch) / "scenarios.md"
   206	        copy.write_text(text, encoding="utf-8")
   207	        return set(scenario_ids(copy)[0])
   208	
   209	
   210	def audit_amendments(root: Path, epic_path: str, base: str, texts: dict[str, str]) -> list[str]:
   211	    items: list[str] = []
   212	    for path, text in texts.items():
   213	        created = git_lines(root, "log", "--diff-filter=A", "--format=%H", "--", path)
   214	        original = show(root, created[-1], path) if created else None
   215	        if original is None or grader_text(original) == grader_text(text):
   216	            continue
   217	        diff = difflib.unified_diff(grader_text(original), grader_text(text), f"{Path(path).stem} at creation",
   218	                                    f"{Path(path).stem} at HEAD", lineterm="", n=1)
   219	        since = git_lines(root, "log", "--format=%h %s", f"{created[-1]}..HEAD", "--", path)
   220	        items.append("\n  ".join([f"{Path(path).stem}: amended since creation", *diff,
   221	                                  *(f"changed by {entry}" for entry in since)]))
   222	    scenarios = f"{epic_path}/bdd_scenarios.en.md"
   223	    before, after = scenario_ids_at(root, base, scenarios), scenario_ids_at(root, "HEAD", scenarios)
   224	    items += [f"scenario {i} added" for i in sorted(after - before)]
   225	    items += [f"scenario {i} removed" for i in sorted(before - after)]
   226	    return items + hld_amendments(root, epic_path, base)
   227	
   228	
   229	def hld_amendments(root: Path, epic_path: str, base: str) -> list[str]:
   230	    """The HLD's Protected paths: and Integration results: lines, diffed between <base> and HEAD."""
   231	    hld = f"{epic_path}/{Path(epic_path).name}.en.md"
   232	    lines = {rev: [line for line in (show(root, rev, hld) or "").splitlines() if line.startswith(GRADER_LINES)]
   233	             for rev in (base, "HEAD")}
   234	    if lines[base] == lines["HEAD"]:
   235	        return []
   236	    diff = difflib.unified_diff(lines[base], lines["HEAD"], f"{Path(hld).name} at base", f"{Path(hld).name} at HEAD",
   237	                                lineterm="", n=0)
   238	    since = git_lines(root, "log", "--format=%h %s", f"{base}..HEAD", "--", hld)
   239	    return ["\n  ".join([f"{Path(hld).name}: Protected paths or Integration results changed since base", *diff,
   240	                         *(f"changed by {entry}" for entry in since)])]
   241	
   242	
   243	def audit_anti_stub(root: Path) -> tuple[list[str], bool]:
   244	    """Fail when production files under src/ at HEAD contain _stub functions, NotImplementedError, or # STUB."""
   245	    if not git_lines(root, "ls-tree", "-r", "--name-only", "HEAD", "--", "src/"):
   246	        return [], False
   247	    proc = subprocess.run(
   248	        ["git", "-C", str(root), "grep", "-n", "-E", r"def .+_stub\(|raise NotImplementedError|# STUB",
   249	         "HEAD", "--", "src/"],
   250	        capture_output=True,
   251	        text=True,
   252	        check=False,
   253	    )
   254	    items = [line.removeprefix("HEAD:") for line in proc.stdout.splitlines() if line.strip()]
   255	    return items, bool(items)
   256	
   257	
   258	def build_report(root: Path, epic_dir: str, base: str) -> tuple[list[tuple[str, list[str]]], bool]:
   259	    epic_path = f".devtool/epic/{epic_dir}"
   260	    mirrors = [p for p in git_lines(root, "ls-tree", "--name-only", "HEAD", "--", f"{epic_path}/")
   261	               if re.fullmatch(r"task_.*\.md", Path(p).name)]
   262	    if not mirrors:
   263	        raise ContractError(f"no task mirrors for epic {epic_dir} at HEAD under {epic_path}/")
   264	    texts = {path: show(root, "HEAD", path) or "" for path in mirrors}
   265	    commits = load_commits(root, base)
   266	    task_commits = {c.sha for c in commits if any(p.startswith(f"{epic_path}/evidence/") for p in c.paths)}
   267	    evidence: list[str] = []
   268	    legacy: list[str] = []
   269	    failed = False
   270	    for path, text in sorted(texts.items()):
   271	        if not marked_done(root, path, text):
   272	            continue
   273	        if section(text, "Verification") is None:
   274	            legacy.append(f"{Path(path).stem}: legacy — no evidence")
   275	        else:
   245	        fast_forward(base, state.upstream)
   246	        state.fast_forwarded = True
   247	    return state
   248	
   249	
   250	def fast_forward(base: str, upstream: str) -> None:
   251	    checkout = checkout_of(base)
   252	    if checkout is None:  # no working tree to keep in step: move the ref atomically
   253	        git("update-ref", f"refs/heads/{base}", rev(upstream), rev(base))
   254	        return
   255	    result = git("merge", "--ff-only", "--quiet", upstream, cwd=checkout, check=False)
   256	    if result.returncode != 0:
   257	        raise Refusal(f"cannot fast-forward {base} in {checkout}: {result.stderr.strip()}")
   258	
   259	
   260	# --- reports ------------------------------------------------------------------------------
   261	
   262	def upstream_commits(since: str, until: str) -> list[str]:
   263	    return [line for line in out("log", "--reverse", "--format=%h %s", f"{since}..{until}").splitlines() if line]
   264	
   265	
   266	def upstream_epics(since: str, until: str) -> list[dict]:
   267	    """Epic directories changed upstream, each with its BDD scenarios when present."""
   268	    paths = changed_files(since, until)
   269	    epic_dirs = sorted({Path(p).parts[2] for p in paths
   270	                        if p.startswith(".devtool/epic/") and len(Path(p).parts) > 3})
   271	    epics = []
   272	    for epic_dir in epic_dirs:
   273	        bdd = f".devtool/epic/{epic_dir}/bdd_scenarios.en.md"
   274	        epics.append({"epic_dir": epic_dir,
   275	                      "bdd": bdd if succeeds("cat-file", "-e", f"{until}:{bdd}") else None})
   276	    return epics
   277	
   278	
   279	def upstream_context(since: str, onto: str, head: str) -> dict:
   280	    upstream_files = changed_files(since, onto)
   281	    branch_files = set(changed_files(onto if is_ancestor(onto, head) else since, head))
   282	    return {
   283	        "upstream_commits": upstream_commits(since, onto),
   284	        "upstream_epics": upstream_epics(since, onto),
   285	        "overlap_files": sorted(branch_files.intersection(upstream_files)),
   286	        "bootstrap_required": any(matches(p, MANIFEST_PATTERNS) for p in upstream_files),
   287	    }
   288	
   289	
   290	def predict(target: str, head: str) -> tuple[str, list[str]]:
   291	    if is_ancestor(target, head):
   292	        return "noop", []
   293	    result = git("merge-tree", "--write-tree", "--name-only", "--no-messages", target, head, check=False)
   294	    if result.returncode == 0:
   295	        return "clean", []
   296	    if result.returncode == 1:
   297	        return "conflicts", sorted({line for line in result.stdout.splitlines()[1:] if line})
   298	    raise GitError(f"git merge-tree failed: {result.stderr.strip()}")
   299	
   300	
   301	# --- commands -----------------------------------------------------------------------------
   302	
   303	def cmd_sync_base(args) -> tuple[int, dict]:
   304	    state = sync_base(args.base, args.fetch)
   305	    return EXIT_OK, {"command": "sync-base", "base": state.base, "upstream": state.upstream,
   525	
   526	
   527	def main(argv: list[str] | None = None) -> int:
   528	    args = build_parser().parse_args(argv)
   529	    try:
   530	        check_git_version()
   531	        code, report = COMMANDS[args.command](args)
   532	    except Refusal as refusal:
   533	        print(f"error: {refusal}", file=sys.stderr)
   534	        return refusal.code
   535	    except GitError as error:
   536	        print(f"error: {error}", file=sys.stderr)
   537	        return EXIT_GIT
   538	    print(json.dumps(report, indent=2) if args.format == "json" else to_markdown(report))
   539	    return code
   540	
   541	
   542	if __name__ == "__main__":
   543	    sys.exit(main())
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
    17	sys.path.insert(0, str(SCRIPTS_DIR))
    18	SCRIPT_PATH = SCRIPTS_DIR / "check_epic_readiness.py"
    19	
    20	# Try importing the module under test
    21	try:
    22	    import check_epic_readiness
    23	except ImportError:
    24	    check_epic_readiness = None  # type: ignore[assignment]
    25	
    26	
    27	def git_cmd(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    28	    return subprocess.run(
    29	        ["git", "-C", str(root), *args],
    30	        capture_output=True,
    31	        text=True,
    32	        check=True,
    33	    )
    34	
    35	
    36	def build_ready_epic(root: Path) -> None:
    37	    """Writes the PRV-HP-01 epic demo_epic (slug demo-epic, 2 tasks) into root.
    38	
    39	    Commits nothing related to the epic.
    40	    """
    41	    # Ensure baseline repo tracked files exist and are committed
    42	    tracked = subprocess.run(
    43	        ["git", "-C", str(root), "ls-files", "tool.py"],
    44	        check=False,
    45	        capture_output=True,
    46	        text=True,
    47	    ).stdout.strip()
    48	    if not tracked:
    49	        (root / "tool.py").write_text("def run():\n    pass\n", encoding="utf-8")
    50	        (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    51	        (root / "scripts").mkdir(parents=True, exist_ok=True)
    52	        (root / "scripts" / "verify.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    53	        (root / ".gitignore").write_text("build/\n", encoding="utf-8")
    54	        git_cmd(root, "add", "tool.py", "README.md", "scripts/verify.sh", ".gitignore")
    55	        git_cmd(root, "commit", "-m", "initial commit", "-q")
    56	
    57	    epic_dir = root / ".devtool" / "epic" / "demo_epic"
    58	    features_dir = root / ".devtool" / "features"
    59	    epic_dir.mkdir(parents=True, exist_ok=True)
    60	    features_dir.mkdir(parents=True, exist_ok=True)
    61	
    62	    # 1. Spec pair
    63	    spec_en = """# Demo Epic Design
    64	
    65	## Table of Contents
    66	
    67	- [Meta Data](#meta-data)
    68	- [Overview](#overview)
    69	
    70	## Meta Data
    71	
    72	- **Status**: Approved (Gate 1)
    73	
    74	## Overview
    75	
    76	Approved spec overview text.
    77	"""
    78	    spec_vi = """# Demo Epic Design
    79	
    80	## Table of Contents
    81	
    82	- [Meta Data](#meta-data)
    83	- [Overview](#overview)
    84	
    85	## Meta Data
    86	
    87	- **Status**: Approved (Gate 1)
    88	
    89	## Overview
    90	
    91	Nội dung tổng quan thiết kế đã được phê duyệt.
    92	"""
    93	    (epic_dir / "2026-10-22-demo-epic-design.en.md").write_text(spec_en, encoding="utf-8")
    94	    (epic_dir / "2026-10-22-demo-epic-design.vi.md").write_text(spec_vi, encoding="utf-8")
    95	
     1	#!/usr/bin/env python3
     2	"""Tests for run_external_review.py, on throwaway git repositories with fake claude and codex executables.
     3	
     4	The fakes are the only claude and codex on PATH, so no test reaches a real CLI.
     5	
     6	Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py
     7	"""
     8	from __future__ import annotations
     9	import contextlib
    10	import io
    11	import json
    12	import os
    13	import shutil
    14	import subprocess
    15	import sys
    16	import tempfile
    17	import unittest
    18	from pathlib import Path
    19	from unittest import mock
    20	
    21	sys.path.insert(0, str(Path(__file__).parent))
    22	import test_check_epic_readiness as tcer
    23	from run_external_review import (
    24	    evaluate_provider_quota,
    25	    format_triage_header,
    26	    load_review_config,
    27	    main,
    28	    save_review_config,
    29	    select_provider_by_quota,
    30	    top_risk_findings_section,
    31	)
    32	
    33	EPIC = ".devtool/epic/demo"
    34	TICKS = "`" * 3
    35	FAKE = """#!/bin/bash
    36	if [ -n "$FAKE_COUNTER" ]; then echo 1 >> "$FAKE_COUNTER"; fi
    37	cat > "$FAKE_STDIN"
    38	echo "$@" > "$FAKE_ARGS"
    39	case "$FAKE_MODE" in
    40	  pass) echo "Verdict: PASS" ;;
    41	  minor) echo "Verdict: CHANGES REQUIRED"; echo "- [Minor] README.md:1 — wording | unclear" ;;
    42	  blocking) echo "Verdict: CHANGES REQUIRED"
    43	            echo "[Critical] demo.en.md:3 — evidence missing"
    44	            echo "[Important] task_1_demo.md:9 — row too weak" ;;
    45	  principal_changes) echo "Verdict: CHANGES REQUIRED"
    46	                     echo "[Important] task_2:Decisions Already Made — persist_track returns a dict. Proposed: keep TrackPersistResult." ;;
    47	  formats) echo "Verdict: CHANGES REQUIRED"
    48	           echo "1. **[Critical]** demo.en.md:3 – evidence missing"
    49	           echo "* [Important] task_1_demo.md:9: row too weak"
    50	           echo "[Important] the audit output was never read" ;;
    51	  bare) echo "Verdict: CHANGES REQUIRED"; echo "Several things look wrong." ;;
    52	  fail) echo "credit balance is too low"; exit 1 ;;
    53	  silent) echo "I looked at everything." ;;
    54	  slow) sleep 30 ;;
    55	  modify) echo changed > DEMO-created.txt; echo "Verdict: PASS" ;;
    56	  bold_verdict) echo "**Verdict:** PASS" ;;
    57	  heading_verdict) echo "### Verdict: CHANGES REQUIRED"; echo "- [Critical] demo.en.md:1 — broken" ;;
    58	  case_verdict) echo "   verdict:   pass   " ;;
    59	  prose_summary) echo "I reviewed everything and found 0 [Critical] or [Important] issues."; echo "Verdict: PASS" ;;
    60	  list_findings) echo "Verdict: CHANGES REQUIRED"
    61	                 echo "- [Critical] demo.en.md:1 — list bullet dash"
    62	                 echo "* [Important] demo.en.md:2 — list bullet star"
    63	                 echo "1. [Minor] demo.en.md:3 — numbered list" ;;
    64	
    65	  bold_verdict) echo "**Verdict:** PASS" ;;
    66	  heading_verdict) echo "### Verdict: CHANGES REQUIRED"; echo "- [Critical] demo.en.md:1 — broken" ;;
    67	  case_verdict) echo "   verdict:   pass   " ;;
    68	  prose_summary) echo "I reviewed everything and found 0 [Critical] or [Important] issues."; echo "Verdict: PASS" ;;
    69	
    70	esac
    71	"""
    72	HLD = ("# Demo\n\nIntegration test roots: scripts/\n\nIntegration results: true -> build/demo.xml\n")
    73	SCENARIOS = f"# Scenarios\n\n{TICKS}gherkin\nScenario: [DEMO-HP-01] [Tier C - Integration] Demo\n  Given a demo\n{TICKS}\n"
    74	
    75	
     1	#!/usr/bin/env python3
     2	"""Verify that every lifecycle document producer exposes the shared contract."""
     3	
     4	from __future__ import annotations
     5	
     6	import pathlib
     7	import re
     8	import unittest
     9	
    10	ROOT = pathlib.Path(__file__).resolve().parents[1]
    11	
    12	EXPECTED: dict[str, tuple[str, ...]] = {
    13	    "skills/dev-brainstorming/SKILL.md": (
    14	        "YYYY-MM-DD-<topic>-design.en.md",
    15	        "YYYY-MM-DD-<topic>-design.vi.md",
    16	        "--require-toc",
    17	        "--require-bilingual",
    18	        "## Shared Contract Warnings",
    19	        "## Cảnh báo Shared Contract",
    20	        "check and warn only",
    21	        "Silence is never consent",
    22	    ),
    23	    "skills/doc-brainstorming/SKILL.md": (
    24	        "YYYY-MM-DD-<topic>-design.en.md",
    25	        "YYYY-MM-DD-<topic>-design.vi.md",
    26	        "--require-toc",
    27	        "--require-bilingual",
    28	    ),
    29	    "skills/dev-designer/SKILL.md": (
    30	        "<epic_name>.en.md",
    31	        "<epic_name>.vi.md",
    32	        "bdd_scenarios.en.md",
    33	        "bdd_scenarios.vi.md",
    34	        "--require-toc",
    35	        "--require-bilingual",
    36	        "Task files are English-only",
    37	        "check_bdd_traceability.py plan",
    38	        "Covers:",
    39	        "Integration test roots:",
    40	        "at least one automated integration test",
    41	        "Handoff Choice",
    42	        "`tests/integration/` and `tests/e2e/` (Python)",  # LF-HP-03
    43	        "exact node ID",
    44	        "should be truthy",
    45	        "returns non-empty",
    46	        "must not be empty or write `None`",
    47	        "## Shared Contract Warnings",
    48	        "task_01",
    49	        ".agents/contract_sync.json",
    50	        ".agents/contract_map.json",
    51	    ),
    52	    "skills/setup-shared-contracts/SKILL.md": (
    53	        "contract_map.json.tmpl",
    54	    ),
    55	    "skills/sync-shared-contracts/SKILL.md": (
    56	        "diff-check",
    57	    ),
    58	    "skills/writing-plans/SKILL.md": (
    59	        "YYYY-MM-DD-<feature-name>.en.md",
    60	        "YYYY-MM-DD-<feature-name>.vi.md",
    61	        "--require-toc",
    62	        "--require-bilingual",
    63	    ),
    64	    "skills/doc-designer/SKILL.md": (
    65	        "<doc_dir>.en.md",
    66	        "<doc_dir>.vi.md",
    67	        "--require-toc",
    68	        "--require-bilingual",
    69	    ),
    70	    "skills/doc-implementation/SKILL.md": (
    71	        "--require-toc",
    72	        "--require-bilingual",
    73	    ),
    74	    "skills/doc_quality_check/SKILL.md": (
    75	        "--require-toc",
    76	        "--require-bilingual",
    77	    ),
    78	    "skills/doc_quality_check/references/document-reviewer-prompt.md": (
    79	        "English document",
    80	        "Vietnamese document",
    81	        "Translation parity",
    82	    ),
    83	    "skills/dev-implementation/SKILL.md": (
    84	        '`profile`: `"epic"`',
    85	        '`repository_sha`',
    86	        "aggregated verdict of **PASS**",
    87	        "check_bdd_traceability.py tests",
    88	        "--ids",
    89	        "Entry-Point Detection",
    90	        "Resume Procedure",
    91	        "handoff.md",
    92	        "space- or comma-separated values",  # LF-HP-04
    93	        "re-enters at Phase 2 step 2",  # LF-ST-04
    94	        "may ride along in that commit",  # LF-ST-06
    95	    ),
    96	    "skills/dev-lifecycle/SKILL.md": (
    97	        'profile `epic`',
    98	        "`repository_sha`",
    99	        "FAIL > BLOCKED > PASS",
   100	        "check_bdd_traceability.py tests",
   101	        "Granting Gate 4 without a passing traceability check",
   102	        "Handoff Choice",
   103	        "handoff-template.md",
   104	        "Resuming an Epic",
   105	        "Packaged",
   106	        "a fresh traceability check and epic quality run",  # LF-ST-05
   107	        "`<N>` is the task count the preflight printed",  # LF-HP-05
   108	        "check_epic_readiness.py <epic_dir>",
   109	        "provider/model priority",
   110	        "Triển khai (tự động)",
   111	        "Dừng lại",
   112	        "references/principal-review.md",
   113	    ),
   114	    "skills/dev-lifecycle/references/handoff-template.md": (
   115	        "or `uncommitted` when `auto_commit` is false",  # LF-FR-04
   116	        "Execution Guardrails for Receiving LLM",
   117	        "Bounded context protocol",
   118	        "Strict spec fidelity",
   119	        "Zero test fakery",
   120	        "No contract repair by the executor",
   121	        "Apply the Execution Guardrails for Receiving LLM before presenting Gate 3",
   122	    ),
   123	    "skills/pr_review/SKILL.md": (
   124	        '"profile": "pr"',
   125	        '"base_ref"',
   126	        "Executive Report Format",
   127	    ),
   128	    "skills/principal-review/SKILL.md": (
   129	        "name: principal-review",
   130	        "Two Modes of Operation",
   131	        "In-Lifecycle Mode",
   132	        "Ad-Hoc Mode",
   133	        "--kind principal",
   134	        "references/principal-review-prompt.md",
   135	        "references/principal-review-rules.md",
   136	        "references/document-triage.md",
   137	    ),
   138	    "skills/cross-model-review/SKILL.md": (
   139	        "name: cross-model-review",
   140	        "Two Modes of Operation",
   141	        "In-Lifecycle Mode",
   142	        "Ad-Hoc Mode",
   143	        "Clean Working Tree",
   144	        "references/review-triage.md",
   145	        "references/local-review-setup.md",
   146	    ),
   147	}
   148	
   149	FORBIDDEN: dict[str, tuple[str, ...]] = {
   150	    "skills/pr_review/SKILL.md": (
   151	        "melos test",
   152	        "./gradlew check",
   153	        "swift test",
   154	        "cleanup-java",
   155	    ),
   156	}
   157	
   158	
   159	class LifecycleDocumentContractTest(unittest.TestCase):
   160	    def test_mvls_hp_06_dev_designer_and_handoff_guardrails(self) -> None:
   161	        """[MVLS-HP-06] dev-designer retains Decisions Already Made contracts, exact node IDs, weak assertion ban, and handoff-template retains 4 guardrails."""
   162	        designer_path = ROOT / "skills/dev-designer/SKILL.md"
   163	        designer_text = designer_path.read_text(encoding="utf-8")
   164	        self.assertIn("exact node ID", designer_text)
   165	        self.assertIn("Decisions Already Made", designer_text)
   329	class PrincipalReviewWorkflowTest(unittest.TestCase):
   330	    def test_prv_hp_04_packaging_readiness_and_principal_review_choice(self) -> None:
   331	        """[PRV-HP-04] Stage 2 asks provider/model priority, runs Principal Review, packages after convergence, and prompts Implement vs Stop."""
   332	        skill_path = ROOT / "skills/dev-lifecycle/SKILL.md"
   333	        skill_text = skill_path.read_text(encoding="utf-8")
   334	        self.assertIn("check_epic_readiness.py <epic_dir>", skill_text)
   335	        self.assertIn("provider/model priority", skill_text)
   336	        self.assertIn("Triển khai (tự động)", skill_text)
   337	        self.assertIn("Dừng lại", skill_text)
   338	        self.assertIn("references/principal-review.md", skill_text)
   339	        self.assertNotIn(
   340	            "check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks",
   341	            skill_text,
   342	        )
   343	        words = len(skill_text.split())
   344	        self.assertLessEqual(words, 2500, f"dev-lifecycle/SKILL.md exceeds word limit: {words} > 2500")
   345	        for token in EXPECTED["skills/dev-lifecycle/SKILL.md"]:
   346	            self.assertIn(token, skill_text)
   347	
   348	        ref_path = ROOT / "skills/dev-lifecycle/references/principal-review.md"
   349	        self.assertTrue(ref_path.is_file(), f"{ref_path} must exist")
   350	        ref_text = ref_path.read_text(encoding="utf-8")
   351	        self.assertIn("provider/model priority order", ref_text)
   352	        self.assertIn("Claude CLI", ref_text)
   353	        self.assertIn("Codex CLI", ref_text)
   354	        self.assertIn("Never choose for the developer", ref_text)
   355	        self.assertIn("strongly recommended", ref_text)
   356	        self.assertIn("1. **Triển khai (tự động)**", ref_text)
   357	        self.assertIn("2. **Dừng lại**", ref_text)
   358	        self.assertIn("Dừng lại ở đây để tôi lấy prompt cho một AI Agents khác triển khai", ref_text)
   359	
   360	    def test_prv_ec_07_handoff_template_reads_first_principal_review(self) -> None:
   361	        """[PRV-EC-07] Read First lists principal_review.md."""
   362	        template_path = ROOT / "skills/dev-lifecycle/references/handoff-template.md"
   363	        text = template_path.read_text(encoding="utf-8")
   364	        read_first = text.split("## Read First", 1)[1].split("## ", 1)[0]
   365	        self.assertIn("`.devtool/epic/<epic_dir>/principal_review.md`, when present", read_first)
   366	        self.assertIn("`git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>`", text)
   367	
   368	    def test_prv_st_03_diagram_loop_returns_to_package_and_done_repackages(self) -> None:
   369	        """[PRV-ST-03] Stage 2 flows through Provider Priority -> Principal Review -> Package -> Implement/Stop Choice."""
   370	        for doc_name in ("docs/lifecycles.en.md", "docs/lifecycles.vi.md"):
   371	            doc_text = (ROOT / doc_name).read_text(encoding="utf-8")
   372	            self.assertIn("PRC -->", doc_text)
   373	            self.assertIn("PR -->", doc_text)
   374	            self.assertIn("| PKG", doc_text)
   375	            self.assertIn("PKG --> HC", doc_text)
   376	            self.assertIn("Triển khai (tự động)", doc_text)
   377	            self.assertIn("Dừng lại", doc_text)
   378	            self.assertNotRegex(doc_text, r"PR\s*[-.=]+>[^\n]*(S3|G3)")
   379	
   380	        ref_path = ROOT / "skills/dev-lifecycle/references/principal-review.md"
   381	        ref_text = ref_path.read_text(encoding="utf-8")
   382	        self.assertIn("Record Principal Review round <n>", ref_text)
   383	        self.assertIn("Revise epic after Principal Review round <n>", ref_text)
   384	        self.assertIn("Package epic for handoff", ref_text)
   385	        self.assertIn("check --kind principal", ref_text)
   386	        self.assertIn("git log -1 --format=%s -- .devtool/epic/<epic_dir>", ref_text)
   387	
   388	    def test_prv_st_04_gate_3_stops_while_principal_finding_undecided(self) -> None:
   389	        """[PRV-ST-04] Gate 3 stops while a blocking principal finding is undecided."""
   390	        impl_path = ROOT / "skills/dev-implementation/SKILL.md"
   391	        text = impl_path.read_text(encoding="utf-8")
   392	        self.assertIn("run_external_review.py check --kind principal --epic-dir <epic_dir>", text)
   393	
   394	        phase1_section = text.split("### Phase 1", 1)[1].split("#### Phase 1 (continued)", 1)[0]
   395	        self.assertIn("Principal Review", phase1_section)
   396	        self.assertIn("not run", phase1_section)
   397	        self.assertIn("round <n>: PASS", phase1_section)
   398	        self.assertIn("round <n>: decided", phase1_section)
   399	
   400	        resume_section = text.split("#### Resume Procedure", 1)[1].split("### Phase 1", 1)[0]
   401	        self.assertIn("Principal Review", resume_section)
   402	        self.assertIn("not run", resume_section)
   403	        self.assertIn("round <n>: PASS", resume_section)
   404	        self.assertIn("round <n>: decided", resume_section)
   405	
   406	        words = len(text.split())
   407	        self.assertLessEqual(words, 4500, f"dev-implementation/SKILL.md exceeds word limit: {words} > 4500")
   408	
   409	
   410	class TestReviewSkillContracts(unittest.TestCase):

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/references/review-rules.md; nl -ba skills/principal-review/references/principal-review-rules.md; nl -ba skills/dev-implementation/references/principal-review-rules.md; nl -ba skills/dev-implementation/references/local-review-setup.md | sed -n '1,40p'; nl -ba skills/cross-model-review/references/local-review-setup.md | sed -n '1,45p'; nl -ba skills/dev-lifecycle/resources/scripts/lifecycle_runner.py | sed -n '210,380p'; nl -ba skills/subagent-driven-development/implementer-prompt.md | sed -n '1,200p'; nl -ba .devtool/epic/token_throttling_optimization/bdd_scenarios.vi.md | sed -n '131,229p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	To avoid false-positive findings, evaluate evidence against these architectural principles:
     2	
     3	1. **Task-Level vs. Gate 4 Workspace Scope**:
     4	   - Each task's `Verification` table is strictly scoped to that individual task's deliverables (e.g. documentation, domain models, or specific adapters).
     5	   - Tasks are NOT required to execute workspace-wide profiles. Full workspace capabilities (coverage thresholds, security advisories/deny, FFI/WASM release builds, database hygiene, and end-to-end acceptance) belong exclusively to the platform-neutral **Gate 4 Quality Orchestrator (`@quality_check`)** evaluated on the final candidate SHA. Do not report task evidence as defective solely because it does not run the entire workspace epic profile.
     6	2. **Compiled Language TDD RED Semantics**:
     7	   - In compiled languages (Rust, Go, C++, etc.), the initial TDD RED phase for a new component or function is legitimately satisfied by a compilation failure or missing test target. A non-zero exit code prior to implementation code being written demonstrates a valid RED state.
     8	3. **Artifact Budget Assertions**:
     9	   - Verify that test assertions checking generated build artifacts (such as WASM binary size or exported types) strictly verify that the target artifact actually exists (avoiding vacuous false-PASS loops).
    10	4. **Contract Drift Inspection**:
    11	   - Check whether code constants, default parameters, and enum variants match the published API reference documentation and cross-epic integration contracts without divergence.
    12	   - If `shared-contracts/` is touched (including directories linked via symlinks across repositories), verify that the `task_01` commit synchronizes the canonical contract files, preserves backward compatibility (Non-Breaking Schema Guarantee), and introduces no breaking wire changes for satellite consumers.
    13	5. **No Reconstructed Logic**:
    14	   - Tests MUST import and invoke production code directly from Allowed files. Tests MUST NOT reconstruct production logic (such as retry loops, progress tracking, mapping transformations, or configuration defaults) locally within test helpers or mock harnesses.
    15	   - A test that reconstructs production logic instead of invoking production symbols is a blocking finding; Gate 4 reports it as FAIL.
    16	6. **Immutable Real Artifacts**:
    17	   - Tests MUST execute against genuine, immutable repository artifacts, schemas, and fixtures. Tests MUST NOT substitute synthetic artifacts or mock data that alter scenario anchors or weaken contractual invariants.
    18	   - A test that substitutes synthetic artifacts altering scenario anchors is a blocking finding; Gate 4 reports it as FAIL.
    19	7. **5-Layer Deep Verification Checklist**:
    20	   - **Unbound Variable in Fallback**: Verify that all variables referenced in `except` blocks are assigned or imported before the `try` block begins.
    21	   - **Part-of-Speech Ambiguity**: Verify that morphological transformation functions (lemmatizers, stemmers, token normalizers) disambiguate noun/adjective forms from verb-like gerunds and participles.
    22	   - **ORM Flush Semantics**: Verify SQLAlchemy Unit of Work execution ordering (Insert -> Update -> Delete). Forbid mutating ORM entities before flushing deleted records sharing the same unique key or index constraint.
    23	   - **Interactive Contract Boundary**: Verify that interactive token and span coverage on user interfaces conforms strictly to `architecture_and_flow.md`.
    24	   - **Fixture Schema Sanity**: Verify that test fixtures and mock records in RED tests satisfy database check constraints before reaching domain assertions.
     1	# Principal Review Rules
     2	
     3	To avoid false-positive findings, evaluate design documents and epic artefacts against these principles:
     4	
     5	1. **Severities**:
     6	   - **Critical**: The epic or architecture cannot reach its goal or pass execution gates as designed (e.g. fatal architectural flaw, missing core contract).
     7	   - **Important**: A task or component would hit Stop-and-Report, ship incorrect behavior, or break module isolation during implementation.
     8	   - **Minor**: Wording, formatting, typo, and minor consistency adjustments.
     9	
    10	2. **Readiness Report Is Proven Fact**:
    11	   - The mechanical checks (R1–R8) in `check_epic_readiness.py` are already validated prior to review.
    12	   - Do not re-verify mechanically checked facts or restate them as findings; spend your review effort on judgement, architecture, and source grounding.
    13	
    14	3. **Grounding in Active Source**:
    15	   - Every claim about the repository source code must name the specific file and line number read.
    16	   - Grounding verifies that referenced symbols, functions, methods, and configurations actually exist at the candidate commit.
    17	
    18	4. **Actionable Findings**:
    19	   - Each finding must name the specific artefact (file path) and location (heading or section) to change.
    20	   - Each finding must conclude with a concrete `Proposed: <edit>` recommendation.
    21	
    22	5. **Shared Contracts, Symlink Resolution & Source-of-Truth Hierarchy (Forward Alignment over Legacy Reversion)**:
    23	   - **Source-of-Truth Hierarchy**:
    24	     1. **Tier 1 (Highest Authority — Approved Design Intent)**: User-approved Spec (`*-design.en.md`) and HLD (`<epic_dir>.en.md` Goals & Architecture).
    25	     2. **Tier 2 (Cross-Repo Contract Baseline)**: `shared-contracts/<domain>/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`).
    26	     3. **Tier 3 (Legacy Code Baseline)**: Existing source files in `src/` and task `Allowed files`.
    27	   - **Forward Alignment Rule (Never Revert Approved Design Intent)**: When Tier 1 intentionally introduces a new pipeline structure, step count, enum, or schema (e.g., consolidating 7 legacy steps into 5 steps) that differs from Tier 2 (`shared-contracts/`) or Tier 3 (`src/`), **DO NOT propose reverting the HLD/Spec back to the legacy Tier 2/Tier 3 design**. Instead, report a **Forward Contract-Sync / Blast-Radius Gap** and propose:
    28	     1. Updating `shared-contracts/<domain>/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md` + `sync_contracts.py ack`) and `## Shared Contract Impact` to match the approved Tier 1 design (with backward-compatibility shims if needed).
    29	     2. Adding the affected legacy callers (e.g., `worker/bridge.py`, `preview/jobs.py`) into the appropriate task's `Allowed files` so implementation migrates them forward to the new design.
    30	   - When reviewing design documents impacting inter-service or cross-repo communication, verify that `shared-contracts/` paths resolve on disk (following symlinks to target repositories if applicable).
    31	   - Flag any unacknowledged contract drift or missing `task_01` contract/adapter synchronization as **Critical** or **Important** with a **forward-migration** `Proposed:` action.
    32	
    33	6. **5-Layer Deep Verification Checklist**:
    34	   - **Unbound Variable in Fallback**: Verify that all variables referenced in `except` blocks are assigned or imported before the `try` block begins.
    35	   - **Part-of-Speech Ambiguity**: Verify that morphological transformation functions (lemmatizers, stemmers, token normalizers) disambiguate noun/adjective forms from verb-like gerunds and participles.
    36	   - **ORM Flush Semantics**: Verify SQLAlchemy Unit of Work execution ordering (Insert -> Update -> Delete). Forbid mutating ORM entities before flushing deleted records sharing the same unique key or index constraint.
    37	   - **Interactive Contract Boundary**: Verify that interactive token and span coverage on user interfaces conforms strictly to `architecture_and_flow.md`.
    38	   - **Fixture Schema Sanity**: Verify that test fixtures and mock records in RED tests satisfy database check constraints before reaching domain assertions.
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
    21	
    22	5. **Shared Contracts, Symlink Resolution & Source-of-Truth Hierarchy (Forward Alignment over Legacy Reversion)**:
    23	   - **Source-of-Truth Hierarchy**: Tier 1 (Approved Spec `*-design.en.md` & HLD `<epic_dir>.en.md` Goals/Architecture) > Tier 2 (`shared-contracts/`) > Tier 3 (Legacy `src/` code).
    24	   - **Forward Alignment Rule**: When Tier 1 intentionally changes pipeline steps, enums, or schemas (e.g., replacing 7 legacy steps with 5 new steps) while `shared-contracts/` or `src/` still holds legacy values, **never propose reverting Tier 1 back to the legacy design**. Instead, propose **forward alignment**: (a) synchronize `shared-contracts/<domain>/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md` + `sync_contracts.py ack`) and `## Shared Contract Impact` to the new Tier 1 design, and (b) add legacy callers in `src/` to task `Allowed files` for forward migration.
    25	   - Verify that `shared-contracts/` paths resolve on disk (following symlinks to target repositories if applicable) and that `task_01` prioritizes contract/adapter synchronization.
     1	# Local Model Review Setup
     2	
     3	Review Choice option 3 sends the finished epic to a model served by a local Ollama:
     4	
     5	```bash
     6	python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
     7	  --epic-dir <epic_dir> --base <base_ref> --cli ollama --model <model>
     8	```
     9	
    10	The developer picks the model from `ollama list`; the agent never picks it.
    11	
    12	## What the runner sends
    13	
    14	- One pass per task commit, then one pass for the epic. Each pass is self-contained, because the
    15	  model has no tools and cannot open a file.
    16	- A system message built from `local-review-prompt.md`: the workflow primer, `review-rules.md`, the
    17	  platform rules for the languages that pass touches, and its checklist. It replaces any `SYSTEM`
    18	  block of the Modelfile for the duration of the call.
    19	- No sampling option and no `think` field. Temperature and the other sampling parameters come from
    20	  the Modelfile. The context is the Modelfile's `num_ctx`; `--num-ctx` overrides it, and 32768 is
    21	  used when the Modelfile sets none.
    22	- `--host` defaults to `$OLLAMA_HOST`, then `http://localhost:11434`. `--timeout` applies to each
    23	  pass.
    24	
    25	## Watching a review
    26	
    27	The runner streams every pass and prints `Live logs: <directory>` before the first one. Each pass
    28	writes `<n>-<label>.log` there as the model produces it: its thinking first, then a
    29	`--- answer ---` line, then the analysis and verdict block. Open a file in the editor, or follow it:
    30	
    31	```bash
    32	tail -f build/local-review/<epic_dir>/1-<first task id>.log
    33	```
    34	
    35	The directory is `build/local-review/<epic_dir>` when Git ignores `build/`; otherwise it sits inside
    36	the Git directory, at `git rev-parse --git-path local-review/<epic_dir>`. Neither place changes
    37	`git status`, so watching never discards a round. Only the answer reaches `review_results.md`.
    38	
    39	## A reviewer Modelfile
    40	
     1	# Local Model Review Setup
     2	
     3	Review Choice option 3 sends the finished epic to a model served by a local Ollama:
     4	
     5	```bash
     6	python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
     7	  --epic-dir <epic_dir> --base <base_ref> --cli ollama --model <model>
     8	```
     9	
    10	The developer picks the model from `ollama list`; the agent never picks it.
    11	
    12	## What the runner sends
    13	
    14	- One pass per task commit, then one pass for the epic. Each pass is self-contained, because the model has no tools and cannot open a file.
    15	- A system message built from `local-review-prompt.md`: the workflow primer, `review-rules.md`, the platform rules for the languages that pass touches, and its checklist. It replaces any `SYSTEM` block of the Modelfile for the duration of the call.
    16	- No sampling option and no `think` field. Temperature and the other sampling parameters come from the Modelfile. The context is the Modelfile's `num_ctx`; `--num-ctx` overrides it, and 32768 is used when the Modelfile sets none.
    17	- `--host` defaults to `$OLLAMA_HOST`, then `http://localhost:11434`. `--timeout` applies to each pass.
    18	
    19	## Watching a review
    20	
    21	The runner streams every pass and prints `Live logs: <directory>` before the first one. Each pass writes `<n>-<label>.log` there as the model produces it: its thinking first, then a `--- answer ---` line, then the analysis and verdict block. Open a file in the editor, or follow it:
    22	
    23	```bash
    24	tail -f build/local-review/<epic_dir>/1-<first task id>.log
    25	```
    26	
    27	The directory is `build/local-review/<epic_dir>` when Git ignores `build/`; otherwise it sits inside the Git directory, at `git rev-parse --git-path local-review/<epic_dir>`. Neither place changes `git status`, so watching never discards a round. Only the answer reaches `review_results.md`.
    28	
    29	## A reviewer Modelfile
    30	
    31	The reference model used while designing this option, on a 64 GB Mac:
    32	
    33	```text
    34	FROM hf.co/unsloth/Qwen3.8-27B-GGUF:Q8_0
    35	
    36	PARAMETER draft_num_predict 1
    37	PARAMETER num_ctx 65536
    38	PARAMETER num_batch 1024
    39	PARAMETER temperature 0.2
    40	PARAMETER top_p 0.9
    41	PARAMETER top_k 20
    42	PARAMETER min_p 0.05
    43	PARAMETER repeat_penalty 1.05
    44	PARAMETER stop "<|im_start|>"
    45	PARAMETER stop "<|im_end|>"
   210	
   211	    def __init__(
   212	        self,
   213	        root: Path,
   214	        epic_slug: str,
   215	        config: RunnerConfig | None = None,
   216	    ) -> None:
   217	        self.root = root
   218	        self.epic_slug = epic_slug
   219	        self.config = config or RunnerConfig()
   220	        self.dispatcher = ModelDispatcher(
   221	            worktree_dir=self.root,
   222	            timeout_seconds=self.config.timeout_seconds,
   223	        )
   224	        self.state = self.load_or_init_state()
   225	
   226	    def state_file(self) -> Path:
   227	        """Return the absolute path to the persistent state JSON file."""
   228	        return self.root / ".devtool" / "state" / f"{self.epic_slug}.pipeline.json"
   229	
   230	    def load_or_init_state(self) -> PipelineState:
   231	        """Load persistent pipeline state from disk or initialize fresh state."""
   232	        path = self.state_file()
   233	        if path.is_file():
   234	            try:
   235	                data = json.loads(path.read_text(encoding="utf-8"))
   236	                if isinstance(data, dict):
   237	                    self.state = PipelineState.from_dict(data)
   238	                    return self.state
   239	            except (json.JSONDecodeError, OSError):
   240	                pass
   241	        self.state = PipelineState(epic_slug=self.epic_slug)
   242	        return self.state
   243	
   244	    def save_state(self) -> None:
   245	        """Atomically persist pipeline state with fcntl file locking."""
   246	        path = self.state_file()
   247	        path.parent.mkdir(parents=True, exist_ok=True)
   248	        tmp_path = path.with_name(f"{path.name}.tmp")
   249	
   250	        data_str = json.dumps(self.state.to_dict(), indent=2) + "\n"
   251	        with open(tmp_path, "w", encoding="utf-8") as f:
   252	            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
   253	            try:
   254	                f.write(data_str)
   255	                f.flush()
   256	                os.fsync(f.fileno())
   257	            finally:
   258	                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
   259	
   260	        tmp_path.replace(path)
   261	
   262	    def sync_gate_ledger(
   263	        self,
   264	        gate_num: int,
   265	        approved_text: str,
   266	        by: str = "lifecycle_runner",
   267	    ) -> bool:
   268	        """Record gate milestone approval in .devtool/GATE_LEDGER.md via resume_context.py."""
   269	        script = self.root / "scripts" / "resume_context.py"
   270	        if not script.is_file():
   271	            return False
   272	        cmd = [
   273	            sys.executable,
   274	            str(script),
   275	            "--gate",
   276	            str(gate_num),
   277	            "--epic",
   278	            self.epic_slug,
   279	            "--approved",
   280	            approved_text,
   281	            "--by",
   282	            by,
   283	        ]
   284	        res = subprocess.run(cmd, cwd=self.root, capture_output=True, check=False)
   285	        return res.returncode == 0
   286	
   287	    def run(
   288	        self,
   289	        resume: bool = False,
   290	        confirm_fixes: bool = False,
   291	        reject_fixes: bool = False,
   292	        reset_stage: str | None = None,
   293	        dry_run: bool = False,
   294	    ) -> int:
   295	        """Execute autonomous pipeline state transitions."""
   296	        if reset_stage:
   297	            self.state.active_stage = reset_stage
   298	            self.save_state()
   299	
   300	        if self.state.active_stage == StageName.INITIALIZED.value:
   301	            if not dry_run:
   302	                ok, err = self.dispatcher.probe_model("agy", self.config.programmer_model)
   303	                if not ok:
   304	                    self.state.last_error = f"Programmer probe failed: {err}"
   305	                    self.save_state()
   306	                    return 1
   307	            self.state.active_stage = StageName.PRINCIPAL_REVIEW.value
   308	            self.save_state()
   309	
   310	        if self.state.active_stage == StageName.PRINCIPAL_REVIEW.value:
   311	            if dry_run:
   312	                print("[DRY-RUN] Would execute Stage 2 Principal Review")
   313	            else:
   314	                ok = self.step_principal_review()
   315	                if not ok:
   316	                    return 1
   317	                if self.state.active_stage in (
   318	                    StageName.HALTED.value,
   319	                    StageName.AWAITING_PRINCIPAL_CONFIRMATION.value,
   320	                ):
   321	                    return 1
   322	
   323	        if self.state.active_stage == StageName.AWAITING_PRINCIPAL_CONFIRMATION.value:
   324	            if confirm_fixes:
   325	                self.state.active_stage = StageName.PRINCIPAL_REVIEW.value
   326	                self.save_state()
   327	                ok = self.step_principal_review()
   328	                if not ok:
   329	                    return 1
   330	            elif reject_fixes:
   331	                self.state.active_stage = StageName.HALTED.value
   332	                self.state.halt_reason = "Human Architect rejected Principal Review fixes"
   333	                self.save_state()
   334	                return 1
   335	            else:
   336	                print("Awaiting Human confirmation for Principal Review fixes. Pass --confirm-fixes or --reject-fixes.")
   337	                return 0
   338	
   339	        if self.state.active_stage == StageName.IMPLEMENTATION.value:
   340	            if dry_run:
   341	                print("[DRY-RUN] Would execute Stage 3 Implementation")
   342	            else:
   343	                ok = self.step_implementation()
   344	                if not ok:
   345	                    return 1
   346	                self.state.active_stage = StageName.CROSS_MODEL_REVIEW.value
   347	                self.save_state()
   348	
   349	        if self.state.active_stage == StageName.CROSS_MODEL_REVIEW.value:
   350	            if dry_run:
   351	                print("[DRY-RUN] Would execute Stage 3 Cross-Model Review")
   352	            else:
   353	                ok = self.step_cross_model_review()
   354	                if not ok:
   355	                    return 1
   356	
   357	        if self.state.active_stage == StageName.AWAITING_FINISH.value:
   358	            report = self.render_final_executive_report()
   359	            print(report)
   360	            print("\n" + "=" * 70)
   361	            print("🏁 Stage 3 completed. All tasks verified and Gate 4 PASS bound to candidate SHA.")
   362	            print("Candidate readiness for Gate 5 recorded in .devtool/state/<epic>.pipeline.json.")
   363	            print("Proceed to /finishing-a-development-branch to merge to local base branch.")
   364	            print("=" * 70 + "\n")
   365	            return 0
   366	
   367	        if self.state.active_stage == StageName.HALTED.value:
   368	            print(f"🛑 Pipeline halted: {self.state.halt_reason}")
   369	            return 1
   370	
   371	        return 0
   372	
   373	    def resolve_gate3_order(self) -> list[str]:
   374	        """Auto-calculate Gate 3 task execution order via compute_execution_order.py."""
   375	        script = (
   376	            self.root
   377	            / "skills"
   378	            / "dev-implementation"
   379	            / "resources"
   380	            / "scripts"
     1	# Implementer Subagent Prompt Template
     2	
     3	Use this template when dispatching an implementer subagent.
     4	
     5	```
     6	Subagent (general-purpose):
     7	  description: "Implement Task N: [task name]"
     8	  model: [MODEL — REQUIRED: choose per SKILL.md Model Selection; an omitted
     9	         model silently inherits the session's most expensive one]
    10	  prompt: |
    11	    You are implementing Task N: [task name]
    12	
    13	    ## Task Description
    14	
    15	    Read your task brief first: [BRIEF_FILE]
    16	    It contains the full task text from the plan.
    17	
    18	    ## Context
    19	
    20	    [Scene-setting: where this fits, dependencies, architectural context]
    21	
    22	    ## Before You Begin
    23	
    24	    If you have questions about:
    25	    - The requirements or acceptance criteria
    26	    - The approach or implementation strategy
    27	    - Dependencies or assumptions
    28	    - Anything unclear in the task description
    29	
    30	    **Ask them now.** Raise any concerns before starting work.
    31	
    32	    ## Your Job
    33	
    34	    Once you're clear on requirements:
    35	    1. Implement exactly what the task specifies
    36	    2. Write tests (following TDD if task says to)
    37	    3. Record the checks (see Recording the Evidence below)
    38	    4. Commit your work — unless the task has a Verification table: then
    39	       leave the change uncommitted (see Recording the Evidence)
    40	    5. Self-review (see below)
    41	    6. Report back
    42	
    43	    Work from: [directory]
    44	
    45	    **While you work:** If you encounter something unexpected or unclear, **ask questions**.
    46	    It's always OK to pause and clarify. Don't guess or make assumptions.
    47	
    48	    While iterating, run the focused test for what you're changing; run the
    49	    full suite once before committing, not after every edit.
    50	
    51	    ## Recording the Evidence
    52	
    53	    When the task has a Verification table, the recorder runs it and writes the
    54	    proof. `[SCRIPTS]` is dev-implementation's `resources/scripts` directory;
    55	    `[TASK_MIRROR]` is the task's file under `.devtool/epic/<epic_dir>/`. Run
    56	    from the epic worktree:
    57	
    58	    1. Before implementing: `python3 [SCRIPTS]/run_task_checks.py red [TASK_MIRROR]`
    59	       must exit 0 (each RED row fails as its Expect says).
    60	    2. After your last change: `python3 [SCRIPTS]/run_task_checks.py verify [TASK_MIRROR]`
    61	       must exit 0 with every row and the scope check passing. Re-run it after
    62	       any later change.
    63	    3. `python3 [SCRIPTS]/run_task_checks.py status [TASK_MIRROR]` must print
    64	       `done gate: PASS`.
    65	
    66	    Do not commit a task with a Verification table. `red` and `verify` must
    67	    be recorded on the same commit, and `verify` must see your change
    68	    uncommitted; the done gate refuses evidence recorded after a commit. The
    69	    controller makes the task's single commit after review.
    70	
    71	    The evidence file is the test evidence: the recorder writes it under
    72	    `.devtool/epic/<epic_dir>/evidence/`. Cite its path in your report. Never
    73	    paste or summarise test output as evidence, and never write or edit the
    74	    evidence file by hand.
    75	
    76	    Never edit the task's Verification table, Definition of Done, Allowed files
    77	    or Covers line, or a protected path, to make a row pass. When a `Stop and
    78	    Report If` condition of the task holds, stop and report `BLOCKED`, naming
    79	    the condition. Do not mark the task `done`; the controller does that after
    80	    review.
    81	
    82	    ## You Do Not Dispatch Subagents
    83	
    84	    Do all of this task's work yourself. Never spawn a subagent to
    85	    implement part of the task, and above all never spawn a reviewer to
    86	    check your work. Self-review (below) means reading your own diff.
    87	    Review is the controller's job: after you report, it dispatches a
    88	    fresh reviewer against your diff. A reviewer you spawn duplicates
    89	    that review at full cost, and its approval counts for nothing in
    90	    the process. If you catch yourself thinking "an independent review
    91	    would strengthen my report" — that review is already scheduled.
    92	    Report instead.
    93	
    94	    ## Code Organization
    95	
    96	    You reason best about code you can hold in context at once, and your edits are more
    97	    reliable when files are focused. Keep this in mind:
    98	    - Follow the file structure defined in the plan
    99	    - Each file should have one clear responsibility with a well-defined interface
   100	    - If a file you're creating is growing beyond the plan's intent, stop and report
   101	      it as DONE_WITH_CONCERNS — don't split files on your own without plan guidance
   102	    - If an existing file you're modifying is already large or tangled, work carefully
   103	      and note it as a concern in your report
   104	    - In existing codebases, follow established patterns. Improve code you're touching
   105	      the way a good developer would, but don't restructure things outside your task.
   106	
   107	    ## When You're in Over Your Head
   108	
   109	    It is always OK to stop and say "this is too hard for me." Bad work is worse than
   110	    no work. You will not be penalized for escalating.
   111	
   112	    **STOP and escalate when:**
   113	    - The task requires architectural decisions with multiple valid approaches
   114	    - You need to understand code beyond what was provided and can't find clarity
   115	    - You feel uncertain about whether your approach is correct
   116	    - The task involves restructuring existing code in ways the plan didn't anticipate
   117	    - You've been reading file after file trying to understand the system without progress
   118	
   119	    **How to escalate:** Report back with status BLOCKED or NEEDS_CONTEXT. Describe
   120	    specifically what you're stuck on, what you've tried, and what kind of help you need.
   121	    The controller can provide more context, re-dispatch with a more capable model,
   122	    or break the task into smaller pieces.
   123	
   124	    ## Before Reporting Back: Self-Review
   125	
   126	    Review your work with fresh eyes. Ask yourself:
   127	
   128	    **Completeness:**
   129	    - Did I fully implement everything in the spec?
   130	    - Did I miss any requirements?
   131	    - Are there edge cases I didn't handle?
   132	
   133	    **Quality:**
   134	    - Is this my best work?
   135	    - Are names clear and accurate (match what things do, not how they work)?
   136	    - Is the code clean and maintainable?
   137	
   138	    **Discipline:**
   139	    - Did I avoid overbuilding (YAGNI)?
   140	    - Did I only build what was requested?
   141	    - Did I follow existing patterns in the codebase?
   142	
   143	    **Testing:**
   144	    - Do tests actually verify behavior (not just mock behavior)?
   145	    - Did I follow TDD if required?
   146	    - Are tests comprehensive?
   147	    - Is the test output pristine (no stray warnings or noise)?
   148	
   149	    If you find issues during self-review, fix them now before reporting.
   150	
   151	    ## After Review Findings
   152	
   153	    If the task review finds issues, you will be resumed with the findings.
   154	    Fix them, re-run `run_task_checks.py verify` so the evidence covers the
   155	    amended code, leave the change uncommitted when the task has a
   156	    Verification table, and append a fix report to your report file: what you
   157	    changed and the evidence file path. Reviewers will not re-run tests for
   158	    you — the evidence file is the test evidence. Then reply with the same
   159	    short status contract as your first report.
   160	
   161	    ## Report Format
   162	
   163	    Write your full report to [REPORT_FILE]:
   164	    - What you implemented (or what you attempted, if blocked)
   165	    - What you tested, and the evidence file path (not pasted test output)
   166	    - **TDD Evidence** (if TDD was required for this task): the `red` and
   167	      `verify` recordings in that evidence file, and why each RED failure was expected
   168	    - Files changed
   169	    - Self-review findings (if any)
   170	    - Any issues or concerns
   171	
   172	    Then report back with ONLY (under 15 lines — the detail lives in the
   173	    report file):
   174	    - **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
   175	    - Commits created (short SHA + subject), or "none — uncommitted" for a
   176	      task with a Verification table
   177	    - One-line test summary (e.g. "14/14 passing, output pristine")
   178	    - Your concerns, if any
   179	    - The report file path
   180	
   181	    If BLOCKED or NEEDS_CONTEXT, put the specifics in the final message
   182	    itself — the controller acts on it directly.
   183	
   184	    Use DONE_WITH_CONCERNS if you completed the work but have doubts about correctness.
   185	    Use BLOCKED if you cannot complete the task. Use NEEDS_CONTEXT if you need
   186	    information that wasn't provided. Never silently produce work you're unsure about.
   187	```
   131	Scenario: [TTO-EC-06] [Tier C - Integration] Cờ verify.sh --quiet tóm tắt gọn từng mục trong khi --full chạy đủ 17 bộ kiểm tra
   132	
   133	Cho bộ script công cụ và tài liệu skill dưới sự kiểm soát của scripts/verify.sh
   134	Khi chạy bash scripts/verify.sh --quiet và khi chạy bash scripts/verify.sh --full
   135	Thì chế độ --quiet chỉ in một dòng trạng thái ngắn gọn cho mỗi mục đạt chuẩn và không xả log thừa
   136	Và chế độ --full thực thi đầy đủ các mục kiểm tra từ §1 đến §17 và thoát với mã 0
   137	```
   138	
   139	## Chuyển đổi trạng thái và bất biến
   140	
   141	```gherkin
   142	Scenario: [TTO-ST-01] [Tier A - Unit] load_review_config tự nâng cấp mặc định gemini-3.8-flash cũ nhưng giữ nguyên model tùy chỉnh
   143	
   144	Cho một tệp .devtool/review_config.json có sẵn đặt providers.programmer.model là "gemini-3.8-flash-high"
   145	Và tệp cấu hình thứ hai nơi người dùng tự chỉnh providers.programmer.model thành "claude-sonnet-4-6"
   146	Khi run_external_review.load_review_config nạp từng tệp cấu hình
   147	Thì khóa "gemini-3.8-flash-high" cũ được nâng cấp trong bộ nhớ thành "gemini-4-hydrogen-xhigh" kèm thinking_level "xhigh"
   148	Và giá trị tùy chỉnh "claude-sonnet-4-6" được giữ nguyên hoàn toàn không bị ghi đè
   149	
   150	Scenario: [TTO-ST-02] [Tier C - Integration] Gói handoff và mẫu handoff chỉ liệt kê tài liệu SSOT tiếng Anh và loại bỏ .vi.md
   151	
   152	Cho một thư mục epic có đủ spec.en.md, spec.vi.md, epic.en.md, epic.vi.md, bdd_scenarios.en.md và bdd_scenarios.vi.md
   153	Khi package_epic.py sinh tệp handoff.md từ skills/dev-lifecycle/references/handoff-template.md
   154	Thì mục Read First được sinh ra chỉ chứa các tệp *.en.md và không có bất kỳ đường dẫn *.vi.md nào
   155	Và handoff-template.md không còn dòng gán cứng model cũ mâu thuẫn với cơ chế chọn Role 2.3 theo cấu hình
   156	
   157	Scenario: [TTO-ST-03] [Tier C - Integration] Cổng sẵn sàng Stage 4 với --strict-bilingual bắt buộc khớp hoàn toàn giữa .en.md và .vi.md
   158	
   159	Cho một thư mục epic có bản HLD .vi.md bị lệch so với .en.md hoặc thiếu tệp bdd_scenarios.vi.md
   160	Khi chạy check_epic_readiness.py --strict-bilingual và check_bdd_traceability.py --strict-bilingual
   161	Thì cả hai lệnh đều thoát khác 0 và chỉ rõ các bản dịch tiếng Việt bị thiếu hoặc lệch nội dung
   162	Và sau khi đồng bộ .vi.md cùng tạo bdd_scenarios.vi.md khớp mã kịch bản và cấu trúc mục lục, cả hai lệnh --strict-bilingual đều thoát mã 0
   163	
   164	Scenario: [TTO-ST-04] [Tier C - Integration] Cross-model review chuyển lên Role 2.2 khi xuất hiện xung đột shared-contracts hoặc mơ hồ kiến trúc
   165	
   166	Cho một phát hiện ở Round 1 của cross-model review liên quan tới shared-contracts/api_contract.md hoặc thay đổi chuyển trạng thái kiến trúc mơ hồ
   167	Khi lifecycle_runner.step_cross_model_review phân loại các phát hiện của vòng review
   168	Thì luồng sửa nhanh không được phép chạy và hệ thống dừng khẩn với CRITICAL_CONFLICT hoặc chuyển fix_plan_round1.md qua Role 2.2 thẩm định trước khi sửa mã
   169	
   170	Scenario: [TTO-ST-05] [Tier C - Integration] Hook Pre-Finish của finishing-a-development-branch ở Stage 4 đồng bộ .vi.md trước khi merge
   171	
   172	Cho tệp skills/finishing-a-development-branch/SKILL.md đã được cập nhật trong bộ công cụ
   173	Khi kiểm tra quy trình kết thúc nhánh Stage 4 và chạy verify.sh §3 cùng §8
   174	Thì bước đồng bộ song ngữ Pre-Finish ở Stage 4 yêu cầu cập nhật phần sai lệch cho Spec và HLD .vi.md, sinh bdd_scenarios.vi.md và chạy check_epic_readiness.py --strict-bilingual trước khi merge
   175	Và toàn bộ liên kết chéo cùng hợp đồng tài liệu đều vượt qua verify.sh không lỗi
   176	```
   177	
   178	## Bất đồng bộ và đồng thời
   179	
   180	```gherkin
   181	Scenario: [TTO-AR-01] [Tier C - Integration] Điều phối theo wave song song chạy đồng thời các task độc lập với prompt chỉ chứa đường dẫn và Zero-Fluff
   182	
   183	Cho một đồ thị DAG của epic gồm hai task Wave 1 độc lập và một task Wave 2 bị chặn bởi cả hai task trên
   184	Và một pool worker cô lập được khởi tạo bằng manage_worker_pool.py
   185	Khi lifecycle_runner.step_implementation thực thi giai đoạn lập trình qua mock dispatcher ghi nhận an toàn luồng
   186	Thì cả hai task Wave 1 chạy song song trong các slot pool tách biệt trước khi Wave 2 bắt đầu
   187	Và prompt mỗi task không nhúng toàn văn file task, chỉ truyền đường dẫn tệp cùng vùng dòng mục tiêu và kèm quy tắc Zero-Fluff
   188	
   189	Scenario: [TTO-AR-02] [Tier C - Integration] Ngữ cảnh sạch từng task và log thô tách biệt theo từng vòng ngăn rò rỉ lịch sử giữa các phiên
   190	
   191	Cho hai vòng review nối tiếp hoặc song song và các lượt điều phối task liên tiếp trong cùng một epic
   192	Khi run_external_review.render_round ghi log và lifecycle_runner khởi chạy Task N+1 sau khi Task N đã commit
   193	Thì mỗi vòng review ghi bản log thô cô lập vào build/reviews/<epic>_round<n>.raw.log mà không ghép vào bảng markdown hoặc file log vòng khác
   194	Và prompt của Task N+1 hoàn toàn không mang theo đầu ra công cụ hay stderr tích tụ từ Task N
   195	```
   196	
   197	## Xử lý lỗi và khả năng phục hồi
   198	
   199	```gherkin
   200	Scenario: [TTO-FR-01] [Tier A - Unit] collect_facts xuất một dòng cho lệnh đạt, giới hạn lỗi 25 dòng và tách log thô ra khỏi markdown
   201	
   202	Cho một lệnh đạt chuẩn trả về 180 dòng stdout với mã thoát 0 và một lệnh lỗi trả về 90 dòng stderr với mã thoát 1
   203	Khi run_external_review.fact tạo bằng chứng cho prompt và render_round lưu kết quả vòng review
   204	Thì lệnh đạt chuẩn chỉ tạo đúng một dòng "PASS: <label>" và bỏ qua stdout
   205	Và lệnh thất bại chỉ đính kèm nhãn lệnh cùng tối đa 25 dòng cuối khác rỗng
   206	Và toàn bộ stdout/stderr gốc của CLI được ghi vào build/reviews/<epic>_round<n>.raw.log giúp principal_review.md giữ dung lượng gọn
   207	
   208	Scenario: [TTO-FR-02] [Tier C - Integration] Gate 4 rút gọn hiển thị tiêu đề provider lỗi và 25 dòng đuôi khi gặp sự cố
   209	
   210	Cho một cấu hình chất lượng gồm một capability đạt chuẩn và một capability lỗi in 80 dòng chẩn đoán ra stderr
   211	Khi chạy verify_polyglot_registry.py kèm cờ --compact
   212	Thì tiến trình thoát khác 0 với kết luận FAIL
   213	Và stdout chỉ in "GATE_PASS:" cho capability đạt, tiêu đề capability lỗi và tối đa 25 dòng cuối lấy từ build/quality/
   214	Và đầy đủ 80 dòng gốc vẫn được lưu an toàn trên đĩa tại build/quality/<provider>/<cap>.log
   215	
   216	Scenario: [TTO-FR-03] [Tier A - Unit] lifecycle_runner._tail_lines cắt thông báo lỗi Gate 4 và kiểm tra trung gian tối đa 25 dòng
   217	
   218	Cho một lỗi tiến trình con từ run_gate4 hoặc run_intermediate_check phát ra 120 dòng traceback
   219	Khi lifecycle_runner định dạng đoạn tóm tắt lỗi qua _tail_lines(output, 25)
   220	Thì đoạn trích trả về có tối đa 25 dòng kết thúc ngay tại tóm tắt assertion lỗi cuối cùng
   221	Và chuỗi lỗi lưu trong ngoại lệ hoặc trạng thái truyền sang bước sau không bao giờ vượt quá 25 dòng traceback
   222	
   223	Scenario: [TTO-FR-04] [Tier C - Integration] Bộ kiểm thử hồi quy định lượng báo lỗi rõ ràng nếu kích thước quy tắc, kỹ năng, ngữ cảnh hoặc prompt vượt trần
   224	
   225	Cho các tệp thực tế trong repository và harness epic giả lập bên trong tests/test_token_throttling_acceptance.py
   226	Khi chạy bộ kiểm thử chấp nhận định lượng dưới pytest
   227	Thì các assertion kiểm tra tường minh trần dung lượng byte (CRITICAL_RULES.md <= 8192, dev-designer/SKILL.md <= 22528, resume_context --compact <= 4096) và ngân sách prompt review
   228	Và mọi vi phạm trần đều báo lỗi kèm thông số đo thực tế thay cho các phép kiểm tra boolean chung chung
   229	```

exec
/bin/zsh -lc "env PYTHONDONTWRITEBYTECODE=1 python3 -B -c 'import importlib.util, sys, subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
root = Path.cwd()
scripts = root/'\\''skills/dev-implementation/resources/scripts'\\''
sys.path.insert(0, str(scripts))
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
lr = load('\\''tto_probe_lifecycle'\\'', root/'\\''skills/dev-lifecycle/resources/scripts/lifecycle_runner.py'\\'')
runner = object.__new__(lr.LifecycleRunner)
for token in ['\\''shared-contracts/api_contract.md: field mismatch'\\'', '\\''ambiguous architectural state transition'\\'', '\\''CRITICAL_CONFLICT'\\'', '\\''Debatable: two valid designs'\\'', '\\''conflict with shared-contracts'\\'']:
    print('\\''classifier'\\'', repr(token), '\\''=>'\\'', runner._has_domain_or_critical_conflict(token))
d = lr.ModelDispatcher(root)
for error in [FileNotFoundError('\\''early'\\''), OSError('\\''early'\\'')]:
    with patch.object(lr.subprocess, '\\''Popen'\\'', side_effect=error):
        print('\\''spawn exception'\\'', type(error).__name__, '\\''=>'\\'', d.dispatch('\\''fake'\\'', [], '\\''probe'\\''))
with patch.object(lr.subprocess, '\\''run'\\'', side_effect=OSError('\\''early'\\'')):
    print('\\''probe exception =>'\\'', d.probe_model('\\''fake'\\'', '\\''fake'\\''))
with patch.object(Path, '\\''is_file'\\'', return_value=True), patch.object(Path, '\\''read_text'\\'', side_effect=OSError('\\''early'\\'')):
    print('\\''config read exception =>'\\'', lr.RunnerConfig().resolve_assistant_model(root))
fake_proc = MagicMock(pid=12345)
fake_proc.communicate.side_effect = subprocess.TimeoutExpired('\\''fake'\\'', 1)
fake_proc.poll.return_value = 0
with patch.object(lr.subprocess, '\\''Popen'\\'', return_value=fake_proc), patch.object(lr.os, '\\''killpg'\\''):
    print('\\''timeout exception =>'\\'', d.dispatch('\\''fake'\\'', [], '\\''probe'\\''))
ce = load('\\''tto_probe_order'\\'', scripts/'\\''compute_execution_order.py'\\'')
tasks, _, _ = ce.scan_tasks(root/'\\''.devtool/epic/token_throttling_optimization'\\'', '\\''token_throttling_optimization'\\'')
print('\\''actual batches =>'\\'', ce.compute_parallel_batches(ce.compute_layers(tasks), tasks))
import check_bdd_traceability as cb
for title in ['\\''Scenario: [TTO-HP-01] [Tier C - Integration] Code-fixes'\\'', '\\''Kịch bản: [TTO-EC-04] Chuẩn hóa extra_high'\\'', '\\''Scenario Outline: [TTO-FR-01] exceptions'\\'']:
    payload = '\\''"'```gherkin'"\\n'\\'' + title + '\\''\\nGiven unchanged lexical tokens: running, running-tests, extra-high, extra_high\\n"'```'"\\n'\\''
    with patch.object(Path, '\\''read_text'\\'', return_value=payload):
        print('\\''scenario lexical probe =>'\\'', cb.scenario_ids(Path('\\''memory.en.md'\\'')))
import run_external_review as rer
for value in ['\\''Verdict: CHANGES REQUIRED\\n[Important] skills/a.py:1 — preserve extra_high | literal. Proposed: edit.'\\'', '\\''Verdict: PASS'\\'']:
    parsed = rer.parse_findings(value)
    rendered = rer.render_round(1, {'\\''Status'\\'':'\\''completed'\\'', '\\''Verdict'\\'':'\\''CHANGES REQUIRED'\\'' if parsed else '\\''PASS'\\''}, parsed, value)
    round_lines = rer.rounds_in(rendered)[0][1]
    print('\\''round parser probe =>'\\'', rer.finding_rows(round_lines), rer.round_passes(rer.round_output(round_lines)))
print('\\''No files created, no real child commands invoked.'\\'')
'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
classifier 'shared-contracts/api_contract.md: field mismatch' => False
classifier 'ambiguous architectural state transition' => False
classifier 'CRITICAL_CONFLICT' => False
classifier 'Debatable: two valid designs' => False
classifier 'conflict with shared-contracts' => True
spawn exception FileNotFoundError => (1, '', "CLI binary 'fake' not found on PATH")
spawn exception OSError => (1, '', 'Failed to spawn process: early')
probe exception => (False, 'Probing exception: early')
config read exception => claude-sonnet-5-5-high
timeout exception => (124, '', 'Process timeout: execution timed out after 1800s')
actual batches => [[['task_01_diff_only_external_review_and_transcript_isolation', 'task_02_silent_gate4_and_truncated_test_runners'], ['task_03_option_a_bilingual_and_surgical_contract_guards']], [['task_04_lifecycle_runner_programmer_config_and_pool_isolation', 'task_05_slimming_rules_skills_dedup_and_selective_reviewer']], [['task_06_integration_and_regression_verification']]]
scenario lexical probe => (['TTO-HP-01'], [])
scenario lexical probe => (['TTO-EC-04'], [])
scenario lexical probe => (['TTO-FR-01'], [])
round parser probe => [['1', 'Important', 'skills/a.py:1', 'preserve extra_high | literal. Proposed: edit.', '']] [('review', 'CHANGES REQUIRED', '—')]
round parser probe => [] [('review', 'PASS', '—')]
No files created, no real child commands invoked.

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/run_task_checks.py | sed -n '280,322p;350,440p'; nl -ba skills/dev-implementation/resources/scripts/run_external_review.py | sed -n '1708,1778p'; nl -ba skills/dev-implementation/resources/scripts/local_review.py | sed -n '20,50p;330,380p'; nl -ba skills/subagent-driven-development/scripts/review-package; nl -ba skills/subagent-driven-development/SKILL.md | sed -n '360,404p'; nl -ba .gitignore" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
   280	
   281	
   282	def run_row(row: Row, root: Path, timeout: int, scenario_ids: list[str]) -> dict[str, Any]:
   283	    record: dict[str, Any] = {
   284	        "id": row.id,
   285	        "phase": row.phase,
   286	        "command": row.command,
   287	        "expect": row.expect_text,
   288	        "needs": list(row.needs),
   289	        "exit": None,
   290	        "outcome": "PASS",
   291	        "reason": None,
   292	        "started": utc_now(),
   293	        "finished": None,
   294	        "output_tail": [],
   295	        "output_sha256": hashlib.sha256(b"").hexdigest(),
   296	    }
   297	    unset = next((name for name in row.needs if not os.environ.get(name)), None)
   298	    if unset:
   299	        record.update(outcome="BLOCKED", reason=f"unset: {unset}")
   300	    else:
   301	        ensure_output_dirs(row.command, root)
   302	        started = time.time()
   303	        code, output = run_command(row.command, root, timeout)
   304	        text = output.decode("utf-8", "replace")
   305	        record.update(exit=code, output_tail=text.splitlines()[-TAIL_LINES:],
   306	                      output_sha256=hashlib.sha256(output).hexdigest())
   307	        reason = f"timeout after {timeout} s" if code is None else mismatch(row, code, text)
   308	        if row.phase == "RED":
   309	            pytest_err = validate_pytest_red(row.command, code, text)
   310	            if pytest_err:
   311	                reason = pytest_err
   312	        if row.expect.results:
   313	            files = fresh_reports(row.expect.results, root, started)
   314	            record["results"] = {"path": row.expect.results, "fresh": bool(files)}
   315	            reason = reason or (None if files else STALE)
   316	            if files:
   317	                reason = reason or attach_digest(record["results"], files, scenario_ids)
   318	        if reason:
   319	            record.update(outcome="FAIL", reason=reason)
   320	    record["finished"] = utc_now()
   321	    return record
   322	
   350	
   351	def scope_row(layout: EpicLayout, allowed_patterns: list[str]) -> dict[str, Any]:
   352	    explicit, programs = protected_patterns(layout, layout.root)
   353	    changed: list[str] = []
   354	    violations: list[str] = []
   355	    exact = {p for p in allowed_patterns if not any(c in p for c in "*?")}
   356	    for path in sorted(set(changed_paths(layout.root))):
   357	        protected = path in programs or any(path_matches(pattern, path) for pattern in explicit)
   358	        if path.startswith(".devtool/") and not protected:
   359	            continue
   360	        changed.append(path)
   361	        if protected:
   362	            if path not in exact:
   363	                violations.append(f"protected path not named exactly in Allowed files: {path}")
   364	        elif not any(path_matches(pattern, path) for pattern in allowed_patterns):
   365	            violations.append(f"outside Allowed files: {path}")
   366	    return {"id": "SCOPE", "phase": "SCOPE", "outcome": "FAIL" if violations else "PASS",
   367	            "changed": changed, "violations": violations}
   368	
   369	
   370	def detail_of(record: dict[str, Any]) -> str:
   371	    if record["id"] == "SCOPE":
   372	        return "; ".join(record["violations"]) or f"{len(record['changed'])} changed path(s) in scope"
   373	    return record["reason"] or f"exit {record['exit']}"
   374	
   375	
   376	def run(args: argparse.Namespace) -> int:
   377	    layout = epic_layout(args.task)
   378	    check_task_tamper(args.task, layout)
   379	    task_text = Path(args.task).read_text(encoding="utf-8")
   380	    rows, red_na = parse_verification(task_text)
   381	    allowed = parse_allowed_files(task_text)
   382	    if args.mode == "red":
   383	        selected = [row for row in rows if row.phase == "RED"]
   384	        if red_na is not None or not selected:
   385	            raise ContractError("task has no RED rows to run (RED: n/a or no RED row)")
   386	    elif args.mode == "measure":
   387	        selected = [row for row in rows if row.phase == "MEASURE"]
   388	        if not selected:
   389	            raise ContractError("task has no MEASURE rows to run")
   390	        if getattr(args, "resume", False):
   391	            evidence = load_evidence(layout.evidence) or {}
   392	            m_run = evidence.get("runs", {}).get("measure")
   393	            if m_run and m_run.get("passed") is True:
   394	                tree_match = m_run.get("tree") == fingerprint(layout.root)[0]
   395	                problems = row_problems(selected, {"measure": m_run})
   396	                evidence_entries = parse_evidence_files(task_text)
   397	                evidence_ok = True
   398	                m_digests = m_run.get("evidence_digests", {})
   399	                for entry in evidence_entries:
   400	                    ev_path = layout.root / entry.pattern
   401	                    if not ev_path.is_file() or ev_path.stat().st_size == 0:
   402	                        evidence_ok = False
   403	                        break
   404	                    sha = hashlib.sha256(ev_path.read_bytes()).hexdigest()
   405	                    if sha != m_digests.get(entry.pattern):
   406	                        evidence_ok = False
   407	                        break
   408	                if tree_match and not problems and evidence_ok:
   409	                    print("MEASURE resumed (cached PASS)")
   410	                    return 0
   411	    else:
   412	        selected = [row for row in rows if row.phase in VERIFY_PHASES]
   413	    started = utc_now()
   414	    scenario_ids = epic_scenario_ids(layout)
   415	    records = [run_row(row, layout.root, args.timeout, scenario_ids) for row in selected]
   416	    if args.mode == "verify":
   417	        records.append(scope_row(layout, [entry.pattern for entry in allowed]))
   418	    tree, patch_id = fingerprint(layout.root)
   419	    head = git_run(layout.root, "rev-parse", "HEAD").decode().strip()
   420	    evidence = load_evidence(layout.evidence) or {"schema": 1, "task": Path(args.task).stem, "runs": {}}
   421	    passed = all(record["outcome"] == "PASS" for record in records)
   422	    run_entry: dict[str, Any] = {
   423	        "head": head,
   424	        "tree": tree,
   425	        "patch_id": patch_id,
   426	        "started": started,
   427	        "finished": utc_now(),
   428	        "rows": records,
   429	        "passed": passed,
   430	    }
   431	    if args.mode == "measure":
   432	        digests: dict[str, str] = {}
   433	        for entry in parse_evidence_files(task_text):
   434	            ev_path = layout.root / entry.pattern
   435	            if ev_path.is_file() and ev_path.stat().st_size > 0:
   436	                digests[entry.pattern] = hashlib.sha256(ev_path.read_bytes()).hexdigest()
   437	        run_entry["evidence_digests"] = digests
   438	    evidence["runs"][args.mode] = run_entry
   439	    save_evidence(layout.evidence, evidence)
   440	    for record in records:
  1708	    ]
  1709	
  1710	
  1711	def triage(args: argparse.Namespace) -> int:
  1712	    """Print the latest round as a skeleton to fill, verify and present before any action on its findings."""
  1713	    root = Path(git_run(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
  1714	    name, _ = review_file(getattr(args, "kind", "code"))
  1715	    path = root / ".devtool" / "epic" / args.epic_dir / name
  1716	    rounds = rounds_in(path.read_text(encoding="utf-8")) if path.exists() else []
  1717	    if not rounds:
  1718	        print(f"no review round recorded for {args.epic_dir}", file=sys.stderr)
  1719	        return 2
  1720	    number, lines = rounds[-1]
  1721	    meta = round_meta(lines)
  1722	    cli = meta.get("CLI", "claude")
  1723	    title = f"# Review Triage: {args.epic_dir}, Round {number}"
  1724	    latest = finding_rows(lines)
  1725	    header = format_triage_header(
  1726	        title,
  1727	        meta.get("SHA", "?"),
  1728	        cli,
  1729	        meta.get("Model", "?"),
  1730	        meta.get("Thinking", "high"),
  1731	        meta.get("Verdict", "none"),
  1732	        latest,
  1733	    )
  1734	    if meta.get("Status") and meta.get("Status") != "completed":
  1735	        header.append(f"- **Status**: {meta.get('Status')}")
  1736	    out = [
  1737	        *header,
  1738	        "",
  1739	        *top_risk_findings_section(latest, limit=3),
  1740	        "",
  1741	        "## Passes",
  1742	        "",
  1743	        "| Pass | Verdict | Error |",
  1744	        "|------|---------|-------|",
  1745	        *(f"| {cell(name)} | {verdict} | {cell(error)} |" for name, verdict, error in round_passes(round_output(lines))),
  1746	        "",
  1747	        "## Findings",
  1748	        "",
  1749	    ]
  1750	    if latest:
  1751	        out += [
  1752	            "| # | Severity | Location | Problem | Assessment | Evidence | Proposed action |",
  1753	            "|---|----------|----------|---------|------------|----------|-----------------|",
  1754	            *(f"| {cells[0]} | {cells[1]} | {cell(cells[2])} | {cell(cells[3])} | ? | ? | ? |" for cells in latest),
  1755	        ]
  1756	    else:
  1757	        out.append("None.")
  1758	    out += [
  1759	        "",
  1760	        "## Round Comparison",
  1761	        "",
  1762	        "| Round | CLI / Model | SHA | Status | Verdict | Critical | Important | Minor | Fixed | Dismissed | Undecided |",
  1763	        "|-------|-------------|-----|--------|---------|----------|-----------|-------|-------|-----------|-----------|",
  1764	        *(comparison_row(n, round_lines) for n, round_lines in rounds),
  1765	        "",
  1766	    ]
  1767	    if len(rounds) > 1:
  1768	        out += [f"## Since Round {rounds[-2][0]}", "", *since_lines(finding_rows(rounds[-2][1]), latest)]
  1769	    else:
  1770	        out += ["## Since the Previous Round", "", "No earlier round."]
  1771	    kind = getattr(args, "kind", "code")
  1772	    out += ["", *auto_triage_section(number, rounds, latest, getattr(args, "max_rounds", MAX_REVIEW_ROUNDS))]
  1773	    next_steps = (
  1774	        "To be written after verifying every finding against source and approved Spec/HLD: "
  1775	        "auto-apply Valid doc revisions + record decisions in both Interactive and Autonomous modes "
  1776	        "(halt ONLY on Circuit Breaker, CRITICAL_CONFLICT, or Debatable trade-off), "
  1777	        "run check_epic_readiness.py, and advance to next review round (package after convergence)."
  1778	        if kind == "principal"
    20	from string import Template
    21	from typing import Any, TextIO
    22	
    23	from check_bdd_traceability import FENCE, LEADING_TAG, SCENARIO_LINE, covers_of
    24	from task_contract import git_run, section
    25	
    26	DEFAULT_HOST = "http://localhost:11434"
    27	DEFAULT_NUM_CTX = 32768
    28	PROMPT_SHARE = 0.6
    29	BYTES_PER_TOKEN = 3
    30	TAIL_LINES = 15
    31	EXTENSIONS = {".dart": "Flutter", ".kt": "Android", ".kts": "Android",
    32	              ".swift": "iOS", ".rs": "Rust", ".py": "Python"}
    33	PLATFORM_ORDER = ("Flutter", "Android", "iOS", "Rust", "Python")
    34	DIFF_HEADER = re.compile(r"^diff --git a/.* b/(.*)$")
    35	
    36	REFERENCES = Path(__file__).resolve().parent.parent.parent / "references"
    37	PROMPT = REFERENCES / "local-review-prompt.md"
    38	CHECKLISTS = REFERENCES / "local-review-checklists.md"
    39	PLATFORMS = REFERENCES / "local-review-platforms.md"
    40	RULES = REFERENCES / "review-rules.md"
    41	
    42	
    43	class LocalReviewError(Exception):
    44	    """A probe, budget or transport failure; str(error) is the reason shown to the developer."""
    45	
    46	
    47	@dataclass(frozen=True)
    48	class Reply:
    49	    content: str  # answer_text of message.content; "" on failure
    50	    done_reason: str | None
   330	    return [f"## {name}\n{section(text, name) or ''}".strip() for name in PLATFORM_ORDER if name in present]
   331	
   332	
   333	def render_system(slice_: Slice) -> str:
   334	    """The prompt base with the shared rules, this slice's platform rules and its pass checklist."""
   335	    checklist = "Task pass" if slice_.kind == "task" else "Epic pass"
   336	    checklists = CHECKLISTS.read_text(encoding="utf-8")
   337	    return Template(PROMPT.read_text(encoding="utf-8")).safe_substitute(
   338	        rules=RULES.read_text(encoding="utf-8").strip(),
   339	        platform_rules="\n\n".join(platform_sections(slice_.paths)) or "No platform rules apply to this slice.",
   340	        checklist=f"## {checklist}\n{section(checklists, checklist) or ''}".strip(),
   341	    )
     1	#!/usr/bin/env bash
     2	# Generate a review package: commit list, stat summary, and the net
     3	# diff with extended context, written to a file the reviewer reads in one
     4	# call. Using the recorded per-task BASE (not HEAD~1) keeps multi-commit
     5	# tasks intact.
     6	#
     7	# Usage: review-package PLAN_FILE BASE HEAD [OUTFILE]
     8	# HEAD may be WORKTREE: the package is then the uncommitted working tree
     9	# (untracked files that are not ignored included) against BASE, built in a
    10	# temporary index so the real index is never touched. It prints the tree id
    11	# it packaged; pass that id as BASE to package only a later fix round.
    12	# Default OUTFILE: <repo-root>/.superpowers/sdd/<plan-basename>/review-<base7>..<head7>.diff
    13	# (named per range, so a re-review after fixes gets a distinct fresh file).
    14	set -euo pipefail
    15	
    16	if [ $# -lt 3 ] || [ $# -gt 4 ]; then
    17	  echo "usage: review-package PLAN_FILE BASE HEAD|WORKTREE [OUTFILE]" >&2
    18	  exit 2
    19	fi
    20	
    21	plan=$1
    22	base=$2
    23	head=$3
    24	[ -f "$plan" ] || { echo "no such plan file: $plan" >&2; exit 2; }
    25	
    26	git rev-parse --verify --quiet "$base" >/dev/null || { echo "bad BASE: $base" >&2; exit 2; }
    27	
    28	if [ "$head" = WORKTREE ]; then
    29	  scratch=$(mktemp -d)
    30	  trap 'rm -rf "$scratch"' EXIT
    31	  export GIT_INDEX_FILE="$scratch/index"
    32	  git read-tree HEAD
    33	  git add -A
    34	  tree=$(git write-tree)
    35	  head_label="wt-$(git rev-parse --short "$tree")"
    36	  range="${base}..working tree (tree ${tree})"
    37	  diff_range=(--cached "$base")
    38	else
    39	  git rev-parse --verify --quiet "$head" >/dev/null || { echo "bad HEAD: $head" >&2; exit 2; }
    40	  head_label=$(git rev-parse --short "$head")
    41	  range="${base}..${head}"
    42	  diff_range=("${base}..${head}")
    43	fi
    44	
    45	if [ $# -eq 4 ]; then
    46	  out=$4
    47	else
    48	  dir=$("$(cd "$(dirname "$0")" && pwd)/sdd-workspace" "$plan")
    49	  out="$dir/review-$(git rev-parse --short "$base")..${head_label}.diff"
    50	fi
    51	
    52	{
    53	  echo "# Review package: ${range}"
    54	  echo
    55	  echo "## Commits"
    56	  if [ "$head" = WORKTREE ]; then
    57	    if git rev-parse --verify --quiet "${base}^{commit}" >/dev/null 2>&1; then
    58	      git log --oneline "${base}..HEAD"
    59	    fi
    60	    echo "(uncommitted working tree)"
    61	  else
    62	    git log --oneline "${base}..${head}"
    63	  fi
    64	  echo
    65	  echo "## Files changed"
    66	  git diff --stat "${diff_range[@]}"
    67	  echo
    68	  echo "## Diff"
    69	  git diff -U10 "${diff_range[@]}"
    70	} > "$out"
    71	
    72	if [ "$head" = WORKTREE ]; then
    73	  echo "wrote ${out}: uncommitted working tree, tree ${tree}, $(wc -c < "$out" | tr -d ' ') bytes"
    74	else
    75	  commits=$(git rev-list --count "${base}..${head}")
    76	  echo "wrote ${out}: ${commits} commit(s), $(wc -c < "$out" | tr -d ' ') bytes"
    77	fi
   360	  loop. If the prompt you are writing contains "do not flag," "don't treat X
   361	  as a defect," "at most Minor," or "the plan chose" — stop: you are
   362	  pre-judging, usually to spare yourself a review loop.
   363	The task reviewer may report "⚠️ Cannot verify from diff" items — requirements
   364	that live in unchanged code or span tasks. These do not block the rest of the
   365	review, but you must resolve each one yourself before marking the task
   366	complete: you hold the plan and cross-task context the reviewer
   367	lacks. If you confirm an item is a real gap, treat it as a failed spec
   368	review — it enters the fix loop with the other findings.
   369	
   370	Template: [task-reviewer-prompt.md](task-reviewer-prompt.md)
   371	
   372	### 4. The fix loop
   373	
   374	The loop triggers when the review reports spec ❌, any Critical or Important
   375	finding, or a ⚠️ item you confirmed as a real gap.
   376	
   377	Before the loop starts, two routes leave it immediately:
   378	
   379	- Record Minor findings in the progress ledger as you go
   380	  (`Task <N>: minor (deferred): <one-liner>`), and point the final
   381	  whole-branch review at that list so it can triage which must be fixed
   382	  before merge. A roll-up nobody reads is a silent discard. Minor findings
   383	  never enter the loop.
   384	- A finding labeled plan-mandated — or any finding that conflicts with
   385	  what the plan's text requires — is yours to rule on: weigh the finding
   386	  against the plan text, decide with the spec as the binding authority, and
   387	  ledger the ruling before you act on it. Do not dismiss the finding because
   388	  the plan mandates it, and do not dispatch a fix that contradicts the plan
   389	  without a recorded ruling.
   390	Everything else enters the loop. A fix round is one fix dispatch plus one
   391	scoped re-review. Five rounds maximum per task:
   392	
   393	**Rounds 1-3 — resume the original implementer.** Send it the open findings
   394	verbatim. Its context is intact: it knows the task, the code, and its own
   395	choices. If your harness cannot send another message to a live subagent,
   396	dispatch a fresh implementer carrying the brief path, the report-file path,
   397	and the findings — the report file is the persistent memory either way.
   398	
   399	**Rounds 4-5 — dispatch a fresh implementer on a more capable model** (per
   400	Model Selection), with the brief path, the report-file path, the open
   401	findings, and this framing: "A prior implementer attempted this task
   402	[N] times; you own it now. Read the report file for what was tried." A loop
   403	that survives three resumes usually means the implementer cannot see its
   404	own problem — fresh eyes and a capability bump in one move.
     1	.DS_Store
     2	node_modules/
     3	*.log
     4	.superpowers/
     5	__pycache__/
     6	*.pyc
     7	.worktrees/
     8	skill-observations/
     9	build/
    10	
    11	# Devtool Tier-2 ephemeral runtime state, logs, locks, and local review preferences
    12	# (Keep .devtool/PROJECT_LEDGER.md, .devtool/epic/, .devtool/features/, .devtool/product/ tracked)
    13	!.devtool/GATE_LEDGER.md
    14	.devtool/.memory.lock
    15	.devtool/assistant_state.md
    16	.devtool/activity_stream.log
    17	.devtool/state/
    18	.devtool/logs/
    19	.devtool/archive/
    20	.devtool/review_config.json
    21	.devtool/review_config.json.tmp
    22	.devtool/contract_brief_*.md

exec
/bin/zsh -lc "nl -ba .devtool/epic/token_throttling_optimization/token_throttling_optimization.vi.md | sed -n '59,81p'; nl -ba skills/quality_check/resources/scripts/verify_polyglot_registry.py | sed -n '142,212p;250,352p'; rg -n 'except|def ' skills/dev-implementation/resources/scripts/run_task_checks.py scripts/resume_context.py | tail -55; rg -n 'require-bilingual|check_document|bdd_scenarios.vi' docs/lifecycles.en.md docs/lifecycles.vi.md skills/dev-lifecycle/references/*.md" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 exited 1 in 0ms:
    59	### Kiến trúc Tổng quan
    60	
    61	```mermaid
    62	flowchart TD
    63	    subgraph CFG["Lớp Cấu hình và Nền Always-On"]
    64	        RC[".devtool/review_config.json (providers.programmer)"]
    65	        CR["rules/CRITICAL_RULES.md (<= 8KB + Zero-Fluff Cap)"]
    66	        TO["skills/task-observer/SKILL.md (SUBAGENT-STOP)"]
    67	        MEM["scripts/resume_context.py (--compact + Dynamic Handoff)"]
    68	    end
    69	
    70	    subgraph S12["Stage 1 và Stage 2 Song ngữ Option A"]
    71	        DESIGN["skills/dev-designer/SKILL.md (<= 22KB + Dải dòng target_files)"]
    72	        TC["check_task_contract.py (--design Check Dải dòng)"]
    73	        READY["check_epic_readiness.py (In-Flight mặc định vs --strict-bilingual)"]
    74	        PKG["package_epic.py + handoff-template.md (Chỉ English SSOT ở Read First)"]
    75	    end
    76	
    77	    subgraph REV["Engine Review Mở rộng"]
    78	        RER["run_external_review.py (-U5 + Delta R2+ + Quiet Facts + Raw Log)"]
    79	        REVP["review-package (-U5) + Diff-Only Prompts"]
    80	    end
    81	
   142	def execute_provider(
   143	    provider_item: dict[str, Any],
   144	    profile: str,
   145	    sha: str,
   146	    base_ref: str = "main",
   147	    repo_root: Path | None = None,
   148	) -> dict[str, Any]:
   149	    root = repo_root or Path.cwd()
   150	    p_id = provider_item.get("id", "")
   151	    skill = provider_item.get("skill", "")
   152	
   153	    actual_started_head = _get_git_head(root)
   154	    head_recorded = actual_started_head or sha
   155	
   156	    candidates = [
   157	        root / ".agents" / "quality" / f"{p_id}.json",
   158	    ]
   159	    platform = p_id.split("-")[0]
   160	    if platform:
   161	        candidates.append(root / ".agents" / "quality" / f"{platform}-quality.json")
   162	    for part in skill.split(":")[-1].split("-"):
   163	        if part and part not in ("quality", "check"):
   164	            candidates.append(root / ".agents" / "quality" / f"{part}-quality.json")
   165	
   166	    manifest_path = next((c for c in candidates if c and c.is_file()), None)
   167	    if not manifest_path:
   168	        return {
   169	            "provider_id": p_id,
   170	            "contract_version": 1,
   171	            "profile": profile,
   172	            "repository_sha": sha,
   173	            "status": "BLOCKED",
   174	            "required": provider_item.get("required", True),
   175	            "checks": [],
   176	            "coverage": {},
   177	            "evidence": [],
   178	            "started_head": head_recorded,
   179	            "finished_head": head_recorded,
   180	            "duration": 0.0,
   181	            "blockers": [f"Manifest file for provider '{p_id}' not found"],
   182	            "warnings": [],
   183	        }
   184	
   185	    try:
   186	        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
   187	    except (json.JSONDecodeError, OSError) as e:
   188	        return {
   189	            "provider_id": p_id,
   190	            "contract_version": 1,
   191	            "profile": profile,
   192	            "repository_sha": sha,
   193	            "status": "BLOCKED",
   194	            "required": provider_item.get("required", True),
   195	            "checks": [],
   196	            "coverage": {},
   197	            "evidence": [],
   198	            "started_head": head_recorded,
   199	            "finished_head": head_recorded,
   200	            "duration": 0.0,
   201	            "blockers": [f"Failed to parse manifest '{manifest_path}': {e}"],
   202	            "warnings": [],
   203	        }
   204	
   205	    skills_dir = Path(__file__).resolve().parents[3]
   206	
   207	    # Web provider execution: dispatch to web-quality runner
   208	    if "web" in p_id or "web" in skill:
   209	        try:
   210	            web_scripts = skills_dir / "web-quality-check" / "resources" / "scripts"
   211	            if str(web_scripts) not in sys.path:
   212	                sys.path.insert(0, str(web_scripts))
   250	    if platform_name:
   251	        p_scripts = (
   252	            skills_dir / f"{platform_name}-quality-check" / "resources" / "scripts"
   253	        )
   254	        if p_scripts.is_dir() and str(p_scripts) not in sys.path:
   255	            sys.path.insert(0, str(p_scripts))
   256	        try:
   257	            mod = importlib.import_module(f"validate_{platform_name}_quality")
   258	            val_fn = getattr(mod, f"validate_{platform_name}_config", None)
   259	            if val_fn:
   260	                v_res = val_fn(manifest_data, profile)
   261	                if v_res.get("status") == "BLOCKED":
   262	                    return {
   263	                        "provider_id": p_id,
   264	                        "contract_version": 1,
   265	                        "profile": profile,
   266	                        "repository_sha": sha,
   267	                        "status": "BLOCKED",
   268	                        "required": provider_item.get("required", True),
   269	                        "checks": [],
   270	                        "coverage": {},
   271	                        "evidence": [],
   272	                        "started_head": sha,
   273	                        "finished_head": sha,
   274	                        "duration": 0.0,
   275	                        "blockers": v_res.get("findings", []),
   276	                        "warnings": [],
   277	                    }
   278	        except Exception:
   279	            pass
   280	
   281	    # Execute configured profile capabilities for non-web provider
   282	    start_time = time.time()
   283	    profiles = manifest_data.get("profiles", {})
   284	    caps_to_run = profiles.get(profile)
   285	    if caps_to_run is None:
   286	        return {
   287	            "provider_id": p_id,
   288	            "contract_version": 1,
   289	            "profile": profile,
   290	            "repository_sha": sha,
   291	            "status": "BLOCKED",
   292	            "required": provider_item.get("required", True),
   293	            "checks": [],
   294	            "coverage": {},
   295	            "evidence": [],
   296	            "started_head": head_recorded,
   297	            "finished_head": head_recorded,
   298	            "duration": 0.0,
   299	            "blockers": [
   300	                f"Requested profile '{profile}' is not configured in profiles"
   301	            ],
   302	            "warnings": [],
   303	        }
   304	
   305	    capabilities = manifest_data.get("capabilities", {})
   306	    checks: list[dict[str, Any]] = []
   307	    evidence: list[dict[str, Any]] = []
   308	    blockers: list[dict[str, Any]] = []
   309	    overall_status = "PASS"
   310	    log_dir = root / "build" / "quality" / p_id
   311	    log_dir.mkdir(parents=True, exist_ok=True)
   312	
   313	    if actual_started_head and sha and sha != actual_started_head:
   314	        overall_status = "FAIL"
   315	        blockers.append(
   316	            {
   317	                "code": "repository_sha_mismatch",
   318	                "message": f"Requested repository SHA '{sha}' does not match actual Git HEAD '{actual_started_head}'",
   319	            }
   320	        )
   321	
   322	    for cap_name in caps_to_run:
   323	        cap_val = capabilities.get(cap_name)
   324	        if isinstance(cap_val, dict):
   325	            cmd = cap_val.get("command", [])
   326	        elif isinstance(cap_val, list):
   327	            cmd = cap_val
   328	        else:
   329	            cmd = []
   330	
   331	        if not cmd:
   332	            continue
   333	
   334	        substituted_cmd = [
   335	            arg.replace("{base_ref}", base_ref).replace("{skills_dir}", str(skills_dir))
   336	            for arg in cmd
   337	        ]
   338	        cap_start = time.time()
   339	        try:
   340	            proc = subprocess.run(
   341	                substituted_cmd,
   342	                cwd=str(root),
   343	                capture_output=True,
   344	                text=True,
   345	                check=False,
   346	            )
   347	            cap_duration = round(time.time() - cap_start, 3)
   348	            log_file = log_dir / f"{cap_name}.log"
   349	            log_file.write_text(
   350	                f"$ {' '.join(substituted_cmd)}\n\n--- STDOUT ---\n{proc.stdout}\n--- STDERR ---\n{proc.stderr}\n",
   351	                encoding="utf-8",
   352	            )
scripts/resume_context.py:759:def append_activity_log(
scripts/resume_context.py:780:def complete_feature_and_rotate(
scripts/resume_context.py:841:def record_gate_approval(
scripts/resume_context.py:885:def scan_gate_ledger(
scripts/resume_context.py:903:            except Exception:
scripts/resume_context.py:920:def check_gate_approval(
scripts/resume_context.py:933:def scan_project_ledger(root: Path) -> None:
scripts/resume_context.py:939:def scan_assistant_state(root: Path) -> None:
scripts/resume_context.py:964:def scan_activity_stream(root: Path, tail_lines: int = 15) -> None:
scripts/resume_context.py:992:def scan_git_status(root: Path) -> None:
scripts/resume_context.py:1012:def scan_open_rfcs(root: Path) -> None:
scripts/resume_context.py:1030:def scan_active_tasks(root: Path, epic_filter: str | None = None) -> None:
scripts/resume_context.py:1133:def collect_harvest_data(
scripts/resume_context.py:1264:def harvest_json(
scripts/resume_context.py:1271:def emit_handoff_prompt(
scripts/resume_context.py:1340:def update_zshrc_env(zshrc_path: Path, r_home: Path, ws_root: Path) -> None:
scripts/resume_context.py:1371:def update_zshrc_history_and_aliases(zshrc_path: Path) -> None:
scripts/resume_context.py:1396:def update_zshrc_sync_items(zshrc_path: Path) -> None:
scripts/resume_context.py:1428:def merge_profile_history(
scripts/resume_context.py:1447:def sync_profile_symlinks(prof: Path, main_hist: Path, ws_root: Path) -> None:
scripts/resume_context.py:1460:def _real_home() -> Path:
scripts/resume_context.py:1466:def sync_shell_env(
scripts/resume_context.py:1510:def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
scripts/resume_context.py:1665:def main() -> None:
skills/dev-implementation/resources/scripts/run_task_checks.py:29:except ImportError:
skills/dev-implementation/resources/scripts/run_task_checks.py:57:def kit_env() -> dict[str, str]:
skills/dev-implementation/resources/scripts/run_task_checks.py:96:def is_pytest_command(command: str) -> bool:
skills/dev-implementation/resources/scripts/run_task_checks.py:101:    except ValueError:
skills/dev-implementation/resources/scripts/run_task_checks.py:132:def validate_pytest_red(command: str, exit_code: int | None, output_text: str) -> str | None:
skills/dev-implementation/resources/scripts/run_task_checks.py:150:def parse_covers(text: str) -> list[str]:
skills/dev-implementation/resources/scripts/run_task_checks.py:159:def core_sections(text: str) -> tuple[str | None, str | None, str | None, list[str]]:
skills/dev-implementation/resources/scripts/run_task_checks.py:168:def check_task_tamper(task_path: Path | str, layout: EpicLayout) -> None:
skills/dev-implementation/resources/scripts/run_task_checks.py:197:def utc_now() -> str:
skills/dev-implementation/resources/scripts/run_task_checks.py:201:def fresh_reports(path: str, root: Path, since: float) -> list[Path]:
skills/dev-implementation/resources/scripts/run_task_checks.py:205:    except ReportError:
skills/dev-implementation/resources/scripts/run_task_checks.py:213:def ensure_output_dirs(command: str, root: Path) -> None:
skills/dev-implementation/resources/scripts/run_task_checks.py:218:    except ValueError:
skills/dev-implementation/resources/scripts/run_task_checks.py:242:def run_command(command: str, root: Path, timeout: int) -> tuple[int | None, bytes]:
skills/dev-implementation/resources/scripts/run_task_checks.py:250:    except subprocess.TimeoutExpired:
skills/dev-implementation/resources/scripts/run_task_checks.py:256:def mismatch(row: Row, code: int, text: str) -> str | None:
skills/dev-implementation/resources/scripts/run_task_checks.py:266:def epic_scenario_ids(layout: EpicLayout) -> list[str]:
skills/dev-implementation/resources/scripts/run_task_checks.py:269:    except UsageError:
skills/dev-implementation/resources/scripts/run_task_checks.py:273:def attach_digest(results: dict[str, Any], files: list[Path], scenario_ids: list[str]) -> str | None:
skills/dev-implementation/resources/scripts/run_task_checks.py:277:    except ReportError:
skills/dev-implementation/resources/scripts/run_task_checks.py:282:def run_row(row: Row, root: Path, timeout: int, scenario_ids: list[str]) -> dict[str, Any]:
skills/dev-implementation/resources/scripts/run_task_checks.py:324:def committed_text(root: Path, path: Path) -> str | None:
skills/dev-implementation/resources/scripts/run_task_checks.py:330:    except (ContractError, ValueError):
skills/dev-implementation/resources/scripts/run_task_checks.py:334:def protected_patterns(layout: EpicLayout, root: Path) -> tuple[list[str], set[str]]:
skills/dev-implementation/resources/scripts/run_task_checks.py:345:        except ContractError:
skills/dev-implementation/resources/scripts/run_task_checks.py:351:def scope_row(layout: EpicLayout, allowed_patterns: list[str]) -> dict[str, Any]:
skills/dev-implementation/resources/scripts/run_task_checks.py:370:def detail_of(record: dict[str, Any]) -> str:
skills/dev-implementation/resources/scripts/run_task_checks.py:376:def run(args: argparse.Namespace) -> int:
skills/dev-implementation/resources/scripts/run_task_checks.py:447:def status(args: argparse.Namespace) -> int:
skills/dev-implementation/resources/scripts/run_task_checks.py:461:def main(argv: list[str] | None = None) -> int:
skills/dev-implementation/resources/scripts/run_task_checks.py:474:    except ContractError as error:

exec
/bin/zsh -lc "nl -ba skills/quality_check/resources/scripts/verify_polyglot_registry.py | sed -n '207,247p;338,388p'; nl -ba skills/dev-implementation/resources/scripts/run_task_checks.py | sed -n '125,149p;240,267p'; nl -ba skills/dev-implementation/resources/scripts/test_manage_worker_pool.py | sed -n '1,230p'; nl -ba skills/dev-lifecycle/resources/scripts/lifecycle_runner.py | sed -n '615,700p'; rg -n 'RULES|review-rules|source fidelity|readiness|vi.md' skills/dev-implementation/resources/scripts/test_local_review.py | head -45; nl -ba skills/using-superpowers/references/codex-tools.md | sed -n '1,100p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
   207	    # Web provider execution: dispatch to web-quality runner
   208	    if "web" in p_id or "web" in skill:
   209	        try:
   210	            web_scripts = skills_dir / "web-quality-check" / "resources" / "scripts"
   211	            if str(web_scripts) not in sys.path:
   212	                sys.path.insert(0, str(web_scripts))
   213	            from validate_web_quality import run_capabilities
   214	
   215	            return run_capabilities(
   216	                config=manifest_data,
   217	                profile=profile,
   218	                repository_sha=sha,
   219	                repo_root=root,
   220	                provider_id=p_id,
   221	                base_ref=base_ref,
   222	                skills_dir=skills_dir,
   223	                check_watchdog_evidence=True,
   224	            )
   225	        except Exception as exc:  # noqa: BLE001
   226	            return {
   227	                "provider_id": p_id,
   228	                "contract_version": 1,
   229	                "profile": profile,
   230	                "repository_sha": sha,
   231	                "status": "FAIL",
   232	                "required": provider_item.get("required", True),
   233	                "checks": [],
   234	                "coverage": {},
   235	                "evidence": [],
   236	                "started_head": sha,
   237	                "finished_head": sha,
   238	                "duration": 0.0,
   239	                "blockers": [f"Error executing provider '{p_id}': {exc}"],
   240	                "warnings": [],
   241	            }
   242	
   243	    # Non-web provider execution: validate using platform validator if available
   244	    platform_name = None
   245	    for p in ("python", "android", "flutter", "ios", "rust"):
   246	        if p in p_id or p in skill:
   247	            platform_name = p
   338	        cap_start = time.time()
   339	        try:
   340	            proc = subprocess.run(
   341	                substituted_cmd,
   342	                cwd=str(root),
   343	                capture_output=True,
   344	                text=True,
   345	                check=False,
   346	            )
   347	            cap_duration = round(time.time() - cap_start, 3)
   348	            log_file = log_dir / f"{cap_name}.log"
   349	            log_file.write_text(
   350	                f"$ {' '.join(substituted_cmd)}\n\n--- STDOUT ---\n{proc.stdout}\n--- STDERR ---\n{proc.stderr}\n",
   351	                encoding="utf-8",
   352	            )
   353	            c_status = "PASS" if proc.returncode == 0 else "FAIL"
   354	            summary = (
   355	                f"{cap_name}: passed"
   356	                if c_status == "PASS"
   357	                else f"{cap_name}: failed with return code {proc.returncode}"
   358	            )
   359	        except OSError as exc:
   360	            cap_duration = round(time.time() - cap_start, 3)
   361	            c_status = "BLOCKED"
   362	            summary = f"{cap_name}: failed to execute: {exc}"
   363	
   364	        evidence_id = f"{cap_name}-evidence"
   365	        log_file = log_dir / f"{cap_name}.log"
   366	        rel_log_path = str(log_file.relative_to(root)) if log_file.is_file() else ""
   367	        checks.append(
   368	            {
   369	                "id": cap_name,
   370	                "category": "quality-check",
   371	                "status": c_status,
   372	                "source": " ".join(substituted_cmd),
   373	                "duration": cap_duration,
   374	                "summary": summary,
   375	                "evidence_refs": [evidence_id] if rel_log_path else [],
   376	            }
   377	        )
   378	        if rel_log_path:
   379	            evidence.append(
   380	                {
   381	                    "id": evidence_id,
   382	                    "type": "command",
   383	                    "source": " ".join(substituted_cmd),
   384	                    "location": rel_log_path,
   385	                }
   386	            )
   387	        if c_status == "FAIL":
   388	            overall_status = "FAIL"
   125	            and sub[1] == "-m"
   126	            and sub[2] == "pytest"
   127	        ):
   128	            return True
   129	    return False
   130	
   131	
   132	def validate_pytest_red(command: str, exit_code: int | None, output_text: str) -> str | None:
   133	    """Evaluate whether a pytest RED execution is genuine.
   134	
   135	    Returns None if valid or not a pytest command.
   136	    Returns INVALID_PYTEST_RED_REASON if it is an invalid pytest RED run.
   137	    """
   138	    if not is_pytest_command(command):
   139	        return None
   140	    if exit_code not in (1, 2):
   141	        return INVALID_PYTEST_RED_REASON
   142	    for marker in FORBIDDEN_MARKERS:
   143	        if marker.search(output_text):
   144	            return INVALID_PYTEST_RED_REASON
   145	    if not POSITIVE_FAILURE_SUMMARY.search(output_text):
   146	        return INVALID_PYTEST_RED_REASON
   147	    return None
   148	
   149	
   240	
   241	
   242	def run_command(command: str, root: Path, timeout: int) -> tuple[int | None, bytes]:
   243	    """Run one row; the exit code is None when the process group had to be killed."""
   244	    process = subprocess.Popen(["bash", "-o", "pipefail", "-c", command], cwd=root, start_new_session=True,
   245	                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=kit_env())
   246	    effective_timeout = timeout if timeout > 0 else None
   247	    try:
   248	        output, _ = process.communicate(timeout=effective_timeout)
   249	        return process.returncode, output
   250	    except subprocess.TimeoutExpired:
   251	        os.killpg(process.pid, signal.SIGKILL)
   252	        output, _ = process.communicate()
   253	        return None, output
   254	
   255	
   256	def mismatch(row: Row, code: int, text: str) -> str | None:
   257	    expect = row.expect
   258	    if expect.nonzero and code == 0:
   259	        return "exit 0, expected non-zero"
   260	    if expect.exit_code is not None and code != expect.exit_code:
   261	        return f"exit {code}, expected {expect.exit_code}"
   262	    missing = next((t for t in expect.contains if t not in text), None)
   263	    return None if missing is None else f'output lacks "{missing}"'
   264	
   265	
   266	def epic_scenario_ids(layout: EpicLayout) -> list[str]:
   267	    try:
     1	#!/usr/bin/env python3
     2	"""Tests for manage_worker_pool.py.
     3	
     4	Run: python3 skills/dev-implementation/resources/scripts/test_manage_worker_pool.py -v
     5	"""
     6	from __future__ import annotations
     7	import os
     8	import shutil
     9	import subprocess
    10	import tempfile
    11	import unittest
    12	from pathlib import Path
    13	
    14	import sys
    15	sys.path.insert(0, str(Path(__file__).parent))
    16	from manage_worker_pool import (
    17	    get_slot_branch,
    18	    get_slot_path,
    19	    link_shared_caches,
    20	    init_slots,
    21	    sync_slot,
    22	    merge_slot,
    23	    cleanup_slots,
    24	    get_pool_status,
    25	)
    26	
    27	
    28	class WorkerPoolNamingTests(unittest.TestCase):
    29	    def test_slot_path_and_branch_generation(self):
    30	        root = Path("/fake/repo")
    31	        epic_dir = "logging_refactor"
    32	        epic_slug = "logging-refactor"
    33	
    34	        path_1 = get_slot_path(root, epic_dir, slot=1)
    35	        path_2 = get_slot_path(root, epic_dir, slot=2)
    36	        self.assertEqual(path_1, root / ".worktrees" / "logging_refactor-slot-1")
    37	        self.assertEqual(path_2, root / ".worktrees" / "logging_refactor-slot-2")
    38	
    39	        branch_1 = get_slot_branch(epic_slug, slot=1)
    40	        branch_2 = get_slot_branch(epic_slug, slot=2)
    41	        self.assertEqual(branch_1, "epic/logging-refactor-slot-1")
    42	        self.assertEqual(branch_2, "epic/logging-refactor-slot-2")
    43	
    44	
    45	class SharedCacheLinkTests(unittest.TestCase):
    46	    def test_links_heavy_cache_directories(self):
    47	        with tempfile.TemporaryDirectory() as tmp:
    48	            main_wt = Path(tmp) / "main_wt"
    49	            slot_wt = Path(tmp) / "slot_wt"
    50	            main_wt.mkdir()
    51	            slot_wt.mkdir()
    52	
    53	            # Create mock node_modules and .venv
    54	            (main_wt / "node_modules").mkdir()
    55	            (main_wt / "node_modules" / "test_pkg.txt").write_text("pkg")
    56	            (main_wt / ".venv").mkdir()
    57	            (main_wt / ".venv" / "bin").mkdir()
    58	
    59	            linked = link_shared_caches(main_wt, slot_wt)
    60	            self.assertIn("node_modules", linked)
    61	            self.assertIn(".venv", linked)
    62	
    63	            # Slot should now have access to those directories
    64	            self.assertTrue((slot_wt / "node_modules" / "test_pkg.txt").exists())
    65	            self.assertTrue((slot_wt / ".venv" / "bin").exists())
    66	
    67	
    68	class GitWorkerPoolLifecycleTests(unittest.TestCase):
    69	    def setUp(self):
    70	        self.tmp_dir = tempfile.mkdtemp()
    71	        self.repo = Path(self.tmp_dir) / "test_repo"
    72	        self.repo.mkdir()
    73	        # Initialize bare repo and working clone
    74	        subprocess.run(["git", "init", "-b", "main"], cwd=self.repo, check=True, capture_output=True)
    75	        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo, check=True)
    76	        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo, check=True)
    77	
    78	        # Initial commit on main
    79	        (self.repo / "README.md").write_text("# Test Repo\n")
    80	        subprocess.run(["git", "add", "README.md"], cwd=self.repo, check=True)
    81	        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo, check=True)
    82	
    83	        # Create epic branch worktree from main
    84	        self.epic_dir = "sample_epic"
    85	        self.epic_slug = "sample-epic"
    86	        self.epic_branch = f"epic/{self.epic_slug}"
    87	
    88	        # Main worktree
    89	        self.main_wt = self.repo / ".worktrees" / self.epic_dir
    90	        self.main_wt.parent.mkdir(parents=True, exist_ok=True)
    91	        subprocess.run(
    92	            ["git", "worktree", "add", str(self.main_wt), "-b", self.epic_branch, "main"],
    93	            cwd=self.repo,
    94	            check=True,
    95	            capture_output=True,
    96	        )
    97	
    98	    def tearDown(self):
    99	        shutil.rmtree(self.tmp_dir, ignore_errors=True)
   100	
   101	    def test_init_sync_merge_cleanup_pool(self):
   102	        # 1. Init 2 slots
   103	        res = init_slots(self.repo, self.epic_dir, self.epic_slug, pool_size=2)
   104	        self.assertEqual(len(res), 2)
   105	        slot1_path = get_slot_path(self.repo, self.epic_dir, 1)
   106	        slot2_path = get_slot_path(self.repo, self.epic_dir, 2)
   107	        self.assertTrue(slot1_path.is_dir())
   108	        self.assertTrue(slot2_path.is_dir())
   109	
   110	        # Check status
   111	        status = get_pool_status(self.repo, self.epic_dir, pool_size=2)
   112	        self.assertEqual(len(status), 2)
   113	        self.assertTrue(status[1]["exists"])
   114	        self.assertTrue(status[2]["exists"])
   115	
   116	        # 2. Simulate task execution in slot 1
   117	        (slot1_path / "task1_file.txt").write_text("Task 1 Done\n")
   118	        subprocess.run(["git", "add", "task1_file.txt"], cwd=slot1_path, check=True)
   119	        subprocess.run(["git", "commit", "-m", f"[{self.epic_slug.upper()}] Task 1"], cwd=slot1_path, check=True)
   120	
   121	        # 3. Merge slot 1 into main worktree
   122	        merge_ok = merge_slot(self.repo, self.epic_dir, self.epic_slug, slot=1)
   123	        self.assertTrue(merge_ok)
   124	        self.assertTrue((self.main_wt / "task1_file.txt").exists())
   125	
   126	        # 4. Sync slot 2 with updated epic branch
   127	        sync_ok = sync_slot(self.repo, self.epic_dir, self.epic_slug, slot=2)
   128	        self.assertTrue(sync_ok)
   129	        self.assertTrue((slot2_path / "task1_file.txt").exists())
   130	
   131	        # 5. Cleanup pool
   132	        cleanup_res = cleanup_slots(self.repo, self.epic_dir, self.epic_slug, pool_size=2)
   133	        self.assertTrue(cleanup_res)
   134	        self.assertFalse(slot1_path.exists())
   135	        self.assertFalse(slot2_path.exists())
   136	
   137	    def test_cli_interface_invocation(self):
   138	        from manage_worker_pool import main
   139	        # Test init via CLI
   140	        cwd = os.getcwd()
   141	        try:
   142	            os.chdir(self.repo)
   143	            exit_code = main(["init", "--epic-dir", self.epic_dir, "--epic-slug", self.epic_slug, "--pool-size", "2"])
   144	            self.assertEqual(exit_code, 0)
   145	
   146	            # Test status via CLI
   147	            exit_code = main(["status", "--epic-dir", self.epic_dir, "--pool-size", "2"])
   148	            self.assertEqual(exit_code, 0)
   149	
   150	            # Test cleanup via CLI
   151	            exit_code = main(["cleanup", "--epic-dir", self.epic_dir, "--epic-slug", self.epic_slug, "--pool-size", "2"])
   152	            self.assertEqual(exit_code, 0)
   153	        finally:
   154	            os.chdir(cwd)
   155	
   156	
   157	if __name__ == "__main__":
   158	    unittest.main()
   615	            prompt=prompt,
   616	        )
   617	        # 1. Commit aligned revision edits first
   618	        status_res = subprocess.run(
   619	            ["git", "status", "--porcelain"],
   620	            cwd=self.root,
   621	            capture_output=True,
   622	            text=True,
   623	            check=False,
   624	        )
   625	        if status_res.returncode == 0 and status_res.stdout.strip():
   626	            subprocess.run(["git", "add", "-A"], cwd=self.root, check=False)
   627	            commit_title = f"[{self.epic_slug.upper()}] Apply aligned Principal Review revisions round {round_num}"
   628	            subprocess.run(
   629	                ["git", "commit", "-m", commit_title],
   630	                cwd=self.root,
   631	                capture_output=True,
   632	                check=False,
   633	            )
   634	
   635	        # 2. Record decision cells citing the fix commit SHA
   636	        rev_res = subprocess.run(
   637	            ["git", "rev-parse", "HEAD"],
   638	            cwd=self.root,
   639	            capture_output=True,
   640	            text=True,
   641	            check=False,
   642	        )
   643	        sha_short = rev_res.stdout.strip()[:7] if rev_res.returncode == 0 else "unknown"
   644	
   645	        file = self.root / ".devtool" / "epic" / self.epic_slug / "principal_review.md"
   646	        if file.is_file():
   647	            content = file.read_text(encoding="utf-8")
   648	            lines = content.splitlines()
   649	            in_target_round = False
   650	            in_raw_output = False
   651	            new_lines = []
   652	            for line in lines:
   653	                if line.startswith(f"## Round {round_num}"):
   654	                    in_target_round = True
   655	                elif line.startswith("## Round "):
   656	                    in_target_round = False
   657	                if in_target_round:
   658	                    if line.startswith("Raw output:"):
   659	                        in_raw_output = True
   660	                    if not in_raw_output and re.match(r"^\|\s*\d+\s*\|", line):
   661	                        parts = line.split("|")
   662	                        if len(parts) >= 6:
   663	                            current_dec = parts[-2].strip()
   664	                            if not current_dec.startswith(("fixed in ", "dismissed: ")):
   665	                                parts[-2] = f" fixed in {sha_short} "
   666	                                line = "|".join(parts)
   667	                new_lines.append(line)
   668	            file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
   669	
   670	        # 3. Commit review decisions separately
   671	        dec_status = subprocess.run(
   672	            ["git", "status", "--porcelain"],
   673	            cwd=self.root,
   674	            capture_output=True,
   675	            text=True,
   676	            check=False,
   677	        )
   678	        if dec_status.returncode == 0 and dec_status.stdout.strip():
   679	            subprocess.run(["git", "add", str(file)], cwd=self.root, check=False)
   680	            commit_title = f"[{self.epic_slug.upper()}] Record Principal Review decisions for round {round_num}"
   681	            subprocess.run(
   682	                ["git", "commit", "-m", commit_title],
   683	                cwd=self.root,
   684	                capture_output=True,
   685	                check=False,
   686	            )
   687	        return True
   688	
   689	    def _run_package_epic_revise(self) -> bool:
   690	        """Run initial package_epic.py <epic> or --revise when handoff.md exists, and commit."""
   691	        pkg_script = (
   692	            self.root
   693	            / "skills"
   694	            / "dev-implementation"
   695	            / "resources"
   696	            / "scripts"
   697	            / "package_epic.py"
   698	        )
   699	        if pkg_script.is_file():
   700	            handoff_file = self.root / ".devtool" / "epic" / self.epic_slug / "handoff.md"
     1	# Using d3nexus in Codex
     2	
     3	The plugin ships the same skills in all runtimes. When a skill uses a Claude Code tool name,
     4	perform the equivalent action using the tools exposed by the current Codex session.
     5	
     6	| Skill instruction | Codex action |
     7	|---|---|
     8	| Invoke `Skill` or `d3nexus:<name>` | Select the installed d3nexus skill, then read its `SKILL.md` and follow it. Resolve supporting paths relative to that skill's directory. |
     9	| `Read`, `Grep`, `Glob` | Use file tools or shell reads; prefer `rg` and `rg --files` for searches. |
    10	| `Edit`, `Write` | Use the available patch or file editing tool. |
    11	| `Bash` | Use the session's shell execution tool, respecting its permission boundaries. |
    12	| `TodoWrite` | Use an available plan/task tool, or maintain a short progress checklist if none exists. |
    13	| `Agent`, `Task`, parallel reviewers | Use subagents only when available and authorized. Otherwise perform independent steps sequentially and report the limitation. |
    14	
    15	Codex reads the consuming project's `AGENTS.md`. Claude's `@file` import syntax and Antigravity's
    16	Markdown `trigger: always_on` frontmatter are not substitutes for explicit reading instructions.
    17	Read the project's rule files when present; otherwise read the plugin's
    18	[critical rules](../../../rules/CRITICAL_RULES.md) and
    19	[coding guidelines](../../../rules/coding-guidelines.md).
    20	
    21	Keep `d3nexus:` cross-references in shared skill text. They identify the owning plugin; they do
    22	not imply that Codex has Claude's slash-command or `Skill` API. Use the skill picker or name the
    23	plugin and skill in a prompt when invocation syntax differs across Codex surfaces.
    24	
    25	Follow the current host's instruction hierarchy and honor the user's authorized scope. References
    26	to Antigravity's native planning artifact apply to that environment; do not invent unavailable
    27	tools or configuration in Codex. Platform build tools, credentials, and devices requested by a
    28	skill still need to exist in the consuming project.
    29	
    30	After reinstalling or upgrading the plugin, start a new thread to load the updated skill inventory.

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/run_external_review.py | sed -n '362,427p'; nl -ba skills/dev-implementation/resources/scripts/compute_execution_order.py | sed -n '115,143p'; rg -n 'thin|review-rules|local-review-prompt|RULES' skills/dev-implementation/resources/scripts/test_run_external_review.py skills/dev-implementation/resources/scripts/test_local_review.py | head -40; nl -ba scripts/resume_context.py | sed -n '1133,1164p;1792,1844p'; nl -ba rules/CRITICAL_RULES.md | sed -n '91,145p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
   362	    r"(\S.*?)(?:\s+[—–-]|\s*:)\s+(\S.*)$",
   363	    re.IGNORECASE,
   364	)
   365	# Only catch unparsed blocking tags when they appear on a list-like or tag-leading line to avoid prose false positives.
   366	UNPARSED_BLOCKING = re.compile(
   367	    r"^\s*(?:[-*+]|\d+[.)])?\s*\*{0,2}\[\*{0,2}(Critical|Important)\*{0,2}\]",
   368	    re.IGNORECASE,
   369	)
   370	FINDING_ROW = re.compile(r"^\|\s*\d+\s*\|")
   371	META_LINE = re.compile(r"^- \*\*(.+?)\*\*: (.*)$")
   372	PASS_HEADER = re.compile(r"^### Pass (\d+): (.+)$")
   373	NEXT_STEPS = ("To be written after verifying every finding: Fix commits, decisions, a confirmation round, "
   374	              "then Gate 4 in full.")
   375	BLOCKING = ("Critical", "Important")
   376	FENCE = re.compile(r"^(`{3,})")
   377	
   378	MAX_DIFF_LINES = 1500
   379	MAX_DIFF_BYTES = 60_000
   380	
   381	RED = "\033[1;31m"
   382	GREEN = "\033[1;32m"
   383	YELLOW = "\033[1;33m"
   384	CYAN = "\033[1;36m"
   385	RESET = "\033[0m"
   386	
   387	EXCLUDES = (
   388	    # 1. Common Locks, Build & Devtool
   389	    ":(exclude)*.lock",
   390	    ":(exclude)*-lock.*",
   391	    ":(exclude)*.lockfile",
   392	    ":(exclude)**/Package.resolved",
   393	    ":(exclude)build/**",
   394	    ":(exclude).devtool/**",
   395	    # 2. Flutter / Dart Codegen & FFI Bridge
   396	    ":(exclude)*.g.dart",
   397	    ":(exclude)*.freezed.dart",
   398	    ":(exclude)*.gr.dart",
   399	    ":(exclude)*.config.dart",
   400	    ":(exclude)*.mocks.dart",
   401	    ":(exclude)*.chopper.dart",
   402	    ":(exclude)*.pigeon.*",
   403	    ":(exclude)*frb_generated*",
   404	    ":(exclude)**/l10n/app_localizations*.dart",
   405	    # 3. iOS Native (Xcode metadata, assets & UI layout XML)
   406	    ":(exclude)*.pbxproj",
   407	    ":(exclude)*.xcworkspacedata",
   408	    ":(exclude)*.xcscheme",
   409	    ":(exclude)*.storyboard",
   410	    ":(exclude)*.xib",
   411	    ":(exclude)**/*.xcassets/**",
   412	    ":(exclude)*.xcstrings",
   413	    # 4. Android Native (Gradle wrapper & Baseline profiles)
   414	    ":(exclude)gradlew",
   415	    ":(exclude)gradlew.bat",
   416	    ":(exclude)**/gradle/wrapper/**",
   417	    ":(exclude)**/baseline-prof.txt",
   418	    # 5. Rust & Python Generated / Snapshots
   419	    ":(exclude)*.generated.*",
   420	    ":(exclude)*_pb2.py",
   421	    ":(exclude)*_pb2_grpc.py",
   422	    ":(exclude)*_pb2.pyi",
   423	    ":(exclude)**/.sqlx/**",
   424	    ":(exclude)**/__snapshots__/**",
   425	    ":(exclude)*.snap",
   426	    ":(exclude)*.ambr",
   427	    # 6. Minified Web Assets & Source Maps
   115	    for path in sorted(candidate_paths):
   116	        scanned.append(path)
   117	        text = path.read_text()
   118	        fm = parse_frontmatter(text)
   119	        task_epic = sanitize_slug(fm.get("epic"))
   120	        if task_epic != target_epic:
   121	            skipped.append(path)
   122	            continue
   123	        section = parse_dependencies_section(text)
   124	        task_id = fm.get("id", path.stem)
   125	        tasks[task_id] = {
   126	            "id": task_id,
   127	            "path": path,
   128	            "priority": fm.get("priority", "medium"),
   129	            "status": fm.get("status", "todo"),
   130	            "blockers": parse_blockers(section),
   131	            "soft_notes": parse_soft_notes(section),
   132	            "allowed_files": parse_allowed_files(text),
   133	            "title": extract_title(text),
   134	        }
   135	    return tasks, scanned, skipped
   136	
   137	
   138	def load_tasks(features_dir: Path, epic: str) -> dict[str, dict]:
   139	    tasks, _scanned, _skipped = scan_tasks(features_dir, epic)
   140	    return tasks
   141	
   142	
   143	def compute_layers(tasks: dict[str, dict]) -> list[list[str]]:
skills/dev-implementation/resources/scripts/test_local_review.py:74:                        self.stream([{"message": {"role": "assistant", "content": "", "thinking": "thinking-marker "},
skills/dev-implementation/resources/scripts/test_local_review.py:150:    def test_lmr_ec_07_inline_thinking_is_never_parsed(self) -> None:
skills/dev-implementation/resources/scripts/test_local_review.py:151:        content = "draft [Critical] a.py:1 — x\nVerdict: CHANGES REQUIRED\n</think>\n## Analysis\nfine\nVerdict: PASS"
skills/dev-implementation/resources/scripts/test_local_review.py:176:    def test_chat_sends_the_messages_and_options_without_think(self) -> None:
skills/dev-implementation/resources/scripts/test_local_review.py:185:    def test_chat_streams_the_thinking_and_the_answer_into_the_log(self) -> None:
skills/dev-implementation/resources/scripts/test_local_review.py:192:        self.assertEqual(text, "thinking-marker \n\n--- answer ---\n\n## Analysis\nfine\nVerdict: PASS")
skills/dev-implementation/resources/scripts/test_local_review.py:200:        self.fake.chunk_delay = 0.6  # every chunk arrives within the socket timeout, the pass as a whole does not
skills/dev-implementation/resources/scripts/test_local_review.py:264:    def test_lmr_hp_04_a_task_slice_carries_everything_the_reviewer_may_judge(self) -> None:
skills/dev-implementation/resources/scripts/test_local_review.py:520:                    run_external_review.Pass("task_2_demo", 0, "## Analysis\nstill thinking", "", "", (), "stop"),
skills/dev-implementation/resources/scripts/test_run_external_review.py:51:  bare) echo "Verdict: CHANGES REQUIRED"; echo "Several things look wrong." ;;
skills/dev-implementation/resources/scripts/test_run_external_review.py:53:  silent) echo "I looked at everything." ;;
skills/dev-implementation/resources/scripts/test_run_external_review.py:59:  prose_summary) echo "I reviewed everything and found 0 [Critical] or [Important] issues."; echo "Verdict: PASS" ;;
skills/dev-implementation/resources/scripts/test_run_external_review.py:68:  prose_summary) echo "I reviewed everything and found 0 [Critical] or [Important] issues."; echo "Verdict: PASS" ;;
skills/dev-implementation/resources/scripts/test_run_external_review.py:314:        self.assertIn("I looked at everything.", text)
skills/dev-implementation/resources/scripts/test_run_external_review.py:734:        """[SRS-FR-01] A readiness FAIL blocks the CLI and records nothing."""
skills/dev-implementation/resources/scripts/test_run_external_review.py:978:        self.assertEqual(cfg["providers"]["claude"]["thinking_level"], "high")
skills/dev-implementation/resources/scripts/test_run_external_review.py:980:        self.assertEqual(cfg["providers"]["codex"]["thinking_level"], "high")
skills/dev-implementation/resources/scripts/test_run_external_review.py:982:        self.assertEqual(cfg["providers"]["kiro"]["thinking_level"], "high")
skills/dev-implementation/resources/scripts/test_run_external_review.py:984:        self.assertEqual(cfg["providers"]["agy"]["thinking_level"], "medium")
skills/dev-implementation/resources/scripts/test_run_external_review.py:986:        self.assertEqual(cfg["providers"]["ollama"]["thinking_level"], "high")
skills/dev-implementation/resources/scripts/test_run_external_review.py:990:        initial_cfg = {"last_used_provider": "codex", "providers": {"codex": {"model": "gpt-6.1-sol", "thinking_level": "high"}}}
skills/dev-implementation/resources/scripts/test_run_external_review.py:995:            "--thinking-level", "medium",
skills/dev-implementation/resources/scripts/test_run_external_review.py:1006:        self.assertEqual(config["providers"]["claude"]["thinking_level"], "medium")
skills/dev-implementation/resources/scripts/test_run_external_review.py:1009:    def test_rts_hp_04_thinking_level_translates_to_cli_flags(self) -> None:
skills/dev-implementation/resources/scripts/test_run_external_review.py:1012:        self.run_review("--thinking-level", "low", cli="codex", mode="pass")
skills/dev-implementation/resources/scripts/test_run_external_review.py:1016:        self.run_review("--thinking-level", "extra-high", cli="claude", mode="pass")
skills/dev-implementation/resources/scripts/test_run_external_review.py:1022:        code_kiro, out_kiro, _ = self.run_review("--thinking-level", "high", cli="kiro", mode="pass")
skills/dev-implementation/resources/scripts/test_run_external_review.py:1045:            RULES,
skills/dev-implementation/resources/scripts/test_run_external_review.py:1050:        ext_rules = RULES.read_text(encoding="utf-8")
skills/dev-implementation/resources/scripts/test_run_external_review.py:1088:                "claude": {"model": "saved-claude", "thinking_level": "low"},
skills/dev-implementation/resources/scripts/test_run_external_review.py:1089:                "codex": {"model": "saved-codex", "thinking_level": "high"},
skills/dev-implementation/resources/scripts/test_run_external_review.py:1127:    def test_rts_fr_02_unknown_thinking_level_defaults_to_high(self) -> None:
skills/dev-implementation/resources/scripts/test_run_external_review.py:1128:        """[RTS-FR-02] Unknown or None thinking level defaults safely to high."""
skills/dev-implementation/resources/scripts/test_run_external_review.py:1130:        _, _, thinking_custom = resolve_review_settings(self.root, "demo", "code", "codex", "gpt-6.1-sol", "unknown-level")
skills/dev-implementation/resources/scripts/test_run_external_review.py:1131:        self.assertEqual(thinking_custom, "high")
skills/dev-implementation/resources/scripts/test_run_external_review.py:1132:        _, _, thinking_none = resolve_review_settings(self.root, "demo", "code", "codex", "gpt-6.1-sol", None)
skills/dev-implementation/resources/scripts/test_run_external_review.py:1133:        self.assertEqual(thinking_none, "high")
skills/dev-implementation/resources/scripts/test_run_external_review.py:1445:                thinking_arg=None,
  1133	def collect_harvest_data(
  1134	    root: Path, tail_lines: int = 15, epic_filter: str | None = None
  1135	) -> dict[str, object]:
  1136	    ledger_path = ensure_ledger(root)
  1137	    ledger_text = (
  1138	        ledger_path.read_text(encoding="utf-8").strip() if ledger_path.exists() else ""
  1139	    )
  1140	
  1141	    candidates = [root / ".devtool"] + [root / r / ".devtool" for r in REPOS]
  1142	    state_map: dict[str, str] = {}
  1143	    for d_dir in candidates:
  1144	        if not d_dir.exists():
  1145	            continue
  1146	        migrate_legacy_storage(d_dir)
  1147	        state_dir = d_dir / "state"
  1148	        if state_dir.exists():
  1149	            for sf in sorted(state_dir.glob("*.md")):
  1150	                text = sf.read_text(encoding="utf-8").strip()
  1151	                if text:
  1152	                    state_map[sf.stem] = text
  1153	        elif (d_dir / "assistant_state.md").exists():
  1154	            text = (d_dir / "assistant_state.md").read_text(encoding="utf-8").strip()
  1155	            if text:
  1156	                state_map["general"] = text
  1157	
  1158	    activity_entries: list[str] = []
  1159	    for d_dir in candidates:
  1160	        if not d_dir.exists():
  1161	            continue
  1162	        logs_dir = d_dir / "logs"
  1163	        if logs_dir.exists():
  1164	            for lf in sorted(logs_dir.glob("activity_*.log")):
  1792	            deviations=args.deviations.strip(),
  1793	            by=args.by.strip() or "developer",
  1794	            repo=args.repo,
  1795	        )
  1796	        print(
  1797	            f"Recorded Gate {args.gate} approval for epic '{active_epic}' at {rec.get('commit')}"
  1798	        )
  1799	        return
  1800	
  1801	    if args.check_gate is not None:
  1802	        chk_rec = check_gate_approval(
  1803	            target_root, active_epic, args.check_gate, repo=args.repo
  1804	        )
  1805	        if chk_rec is not None:
  1806	            print(json.dumps(chk_rec))
  1807	            sys.exit(0)
  1808	        else:
  1809	            print(
  1810	                f"Gate {args.check_gate} is not yet recorded for epic '{active_epic}'",
  1811	                file=sys.stderr,
  1812	            )
  1813	            sys.exit(1)
  1814	
  1815	    # Default: Harvest context
  1816	    scan_root = target_root
  1817	    if args.json:
  1818	        harvest_json(scan_root, tail_lines=args.tail, epic_filter=args.epic)
  1819	        return
  1820	
  1821	    scan_project_ledger(scan_root)
  1822	    scan_assistant_state(scan_root)
  1823	    approvals = scan_gate_ledger(scan_root, epic_slug=active_epic)
  1824	    if approvals:
  1825	        print_section("1.5. GATE APPROVALS (.devtool/GATE_LEDGER.md)")
  1826	        for a in approvals:
  1827	            ep = a.get("epic")
  1828	            g = a.get("gate")
  1829	            ap = a.get("approved")
  1830	            dev = a.get("deviations")
  1831	            dev_str = f" [deviations: {dev}]" if dev else ""
  1832	            print(f"  - Gate {g} ({ep}): {ap}{dev_str} (at {a.get('commit')})")
  1833	    scan_activity_stream(scan_root, tail_lines=args.tail)
  1834	    scan_git_status(scan_root)
  1835	    scan_open_rfcs(scan_root)
  1836	    scan_active_tasks(scan_root, epic_filter=args.epic)
  1837	    sync_window_title(
  1838	        title_target,
  1839	        epic_slug=active_epic,
  1840	        stage_override=args.stage or None,
  1841	        profile_override=args.profile or None,
  1842	    )
  1843	
  1844	
    91	>    - Cross-model review executes its 3-round convergence funnel and severity-tiered auto-triage gate (`AUTO_PASS_CLEAN`, `AUTO_PASS_FINAL_MINOR_SWEEP`, `AUTO_FIX_ELIGIBLE`) automatically, enforcing **scoped tests only** during intermediate fix rounds and reserving full Gate 4 machine acceptance strictly for final convergence.
    92	>
    93	> 3. **Stage 4 Finish Decision & Gate 5 Sign-off (Human Decision Point)**:
    94	>    - The decision to "Finish" belongs strictly to **Stage 4 (`finishing-a-development-branch`)**.
    95	>    - Only after `/cross-model-review` has converged, all findings are resolved, Gate 4 PASS is re-verified on the latest candidate SHA, and the synthesized Executive Report (Top 3 Highest-Risk Findings across all review rounds) is rendered, the AI Agent **MUST explicitly stop calling tools** and prompt the Human Architect for the **Stage 4 Finish Decision** (Gate 5 Sign-off) and Git merge strategy selection (`Squash`, `--no-ff`, or `Rebase`).
    96	>    - The AI Agent **MUST NOT** auto-finish, auto-merge, or auto-push to remote without explicit developer confirmation.
    97	
    98	## 6. Severity-Tiered Auto-Triage Gate, 3-Round Convergence Funnel & Post-Gate Checkpoints
    99	
   100	> [!CRITICAL]
   101	> **Every external review invocation (`/principal-review` and `/cross-model-review`) enforces the 3-Round Scope-Narrowing Convergence Funnel (`max_rounds = 3`), `check-quota` Provider Priority (`Claude -> Codex -> Kiro -> Argon`), and the Severity-Tiered Auto-Triage Gate.**
   102	>
   103	> 1. **Quota-Aware Provider Priority & 3-Round Convergence Funnel**:
   104	>    - **Provider Priority (`Claude -> Codex -> Kiro -> Argon`)**: Evaluations follow `["claude", "codex", "kiro", "agy"]` using `check-quota` thresholds: Claude & Codex require `5H >= 15%` AND `7D > 2%`; Kiro requires `Monthly Credits >= 3%` (`>= 15 credits`); Argon (`agy`) requires `Weekly >= 10%` or `5H >= 15%`.
   105	>    - **Max 3 Rounds**: Reviews are capped at `3` rounds (`Round 1`: Full Scope Audit; `Round 2`: Delta Verification of `prev_sha..curr_sha` with no new Minor on untouched files; `Round 3`: Blocker-Only Convergence Mode).
   106	> 2. **Severity-Tiered Auto-Triage Gate & Automatic Local Quality Gate Re-run**:
   107	>    - **`AUTO_PASS_CLEAN` (`0 findings`)** or **`AUTO_PASS_FINAL_MINOR_SWEEP` (`0 Critical`, `0 Important`, only `Minor` findings)**: Verify findings against live source and approved Spec/HLD first (halting only on `CRITICAL_CONFLICT`, `Debatable` trade-off choices, or `CIRCUIT_BREAKER_HALT`). Otherwise, fix valid `Minor` items in a single sweep (commit revisions + decisions), verify the local quality gate (`check_epic_readiness.py` + `package_epic.py` [or `--revise` when `handoff.md` already exists] at completion of Stage 2 `/principal-review`; full Gate 4 in Stage 3), and **complete the review stage immediately without re-invoking the external reviewer**. At the end of Stage 2 `/principal-review`, print `--emit-prompt implement` and ask **Triển khai (tự động)** vs **Dừng lại**.
   108	>    - **`AUTO_FIX_ELIGIBLE` (Round 1..2 with `Critical`/`Important` findings and no Fix Loop)**:
   109	>      - In **Stage 2 `/principal-review` (BOTH Interactive Mode and Autonomous `/dev-lifecycle` Mode)**: The agent MUST first run `run_external_review.py triage --kind principal --epic-dir <epic_dir>` and verify every finding against live source code and the approved Spec/HLD (`Decisions Already Made`) BEFORE editing any document. Present the verified triage summary (`## Auto-Triage Gate`, `## Top 3 Highest-Risk Findings`, `## Findings`), and **when all blocking findings verify as `Valid` (plus any objective `False positive` refuted with exact source/approved-Spec proof) and zero halt triggers apply, do NOT pause for interactive confirmation**: automatically apply the design revisions in Role 2.2, commit revisions and decisions (`fixed in <sha>`), verify `check_epic_readiness.py <epic_dir>` (scoped readiness check, without premature `handoff.md` packaging or code tests), and immediately advance to Round `N+1` (up to max 3 rounds). **Stop calling tools and escalate to the Human Architect ONLY when hitting**: (1) `CRITICAL_CONFLICT` (conflict with business/domain requirements, critical risks, or frozen Tier-1 Spec/`Decisions Already Made`), (2) a `Debatable` finding requiring a trade-off choice (or an unresolvable `Not shown` claim), (3) `CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)`, (4) `CIRCUIT_BREAKER_HALT (FIX_LOOP)`, or (5) `CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)`. Only after `/principal-review` converges does Stage 2 execute `package_epic.py`, print `--emit-prompt implement`, and ask **Triển khai (tự động)** vs **Dừng lại**.
   110	>      - In **Stage 3 `/cross-model-review` — Autonomous `/dev-lifecycle` Mode**: When all blocking findings verify as `Valid` in source code and do not require unapproved changes to `shared-contracts/`, Role 2.3 drafts `fix_plan_round<N>.md` evaluated by Role 2.2 (`APPROVED`, `ADJUSTED`, `CRITICAL_CONFLICT`), applies the fixes, commits them, records decisions, runs **scoped tests only** (fast static/architecture checks and targeted unit tests covering modified modules; repo-wide pytest and Playwright E2E suites forbidden), and invokes the next convergence round (`Round N+1`, up to max 3 rounds). Full Gate 4 is reserved strictly for the Final Convergence Gate. If `CRITICAL_CONFLICT` or `SHARED_CONTRACT_CONFLICT` is detected, halt immediately for the Human Architect.
   111	>      - In **Stage 3 `/cross-model-review` — Interactive Mode** (or whenever any Stage 3 finding is `Debatable` / `False Positive` or hits a Halt Trigger): The agent **MUST STOP CALLING TOOLS** after presenting the verified triage table (`run_external_review.py triage`) and wait for explicit developer confirmation on the findings. Once confirmed, Role 2.3 applies the fixes, commits them, runs **scoped tests only** without asking for an intermediate confirmation, and returns to the cross-model review loop. Only at final convergence does full Gate 4 run.
   112	>    - **`CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)` (Mandatory Immediate Stop on `shared-contracts/` Conflicts)**:
   113	>      - If ANY `Critical` or `Important` finding in `/principal-review` or `/cross-model-review` directly impacts or conflicts with `shared-contracts/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`, `contract_sync.json`, or wire-level step/enum/payload contracts — e.g. HLD defines 5 new steps while `shared-contracts/` still holds 7 legacy steps), the AI Agent **MUST IMMEDIATELY STOP CALLING TOOLS AND REPORT TO THE DEVELOPER**.
   114	>      - The AI Agent is **STRICTLY PROHIBITED** from auto-fixing `shared-contracts/` conflicts, **STRICTLY PROHIBITED** from proposing or applying a revert of the user's approved HLD/Spec design back to legacy contract steps, and **STRICTLY PROHIBITED** from continuing autonomous execution until the Human Architect explicitly confirms the contract alignment decision.
   115	>    - **`CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)` & `CIRCUIT_BREAKER_HALT (FIX_LOOP)`**:
   116	>      - If after **3 review rounds (`Round >= 3`) any `Critical` finding still remains**, OR if a **Fix Loop** occurs (the same file marked `fixed in <sha>` in Round $N-1$ is re-reported with a `Critical`/`Important` finding in Round $N$), the AI Agent **MUST IMMEDIATELY STOP CALLING TOOLS**, present the `## Top 3 Highest-Risk Findings (Executive Report)` and triage table, and escalate to the Human Architect (never auto-continue to implementation or branch finishing when a `Critical` finding survives 3 rounds).
   117	>      - Conversely, if Round 3 finishes with **`0 Critical` findings** (and no `shared-contracts/` conflict or Fix Loop, only remaining `Important`/`Minor` findings), `AUTO_PASS_FINAL_SWEEP` applies one final fix pass anchored to the approved design, runs the local quality gate green, and completes the stage without invoking a 4th review round.
   118	>
   119	> 3. **Remediation Loop & Test Execution Protocol (Hard Constraints)**:
   120	>    - To prevent multi-minute test hangs, token waste, and incomplete/evasive fixes during review-remediation cycles, both Orchestrator and Fixer/Implementer agents MUST strictly obey:
   121	>    - **Scoped Tests Only During Intermediate Fix Rounds (Round 1, Round 2...)**:
   122	>      - While fixing findings in intermediate rounds, run **ONLY** fast static/architecture checks (`ruff`, `mypy`, `lint-imports`, AST invariants) and **explicitly targeted test files** that directly cover the modified modules: `uv run pytest <explicit_test_file_1.py> <explicit_test_file_2.py>`. In Stage 2, run `check_epic_readiness.py <epic_dir>`.
   123	>      - **STRICTLY FORBIDDEN IN INTERMEDIATE ROUNDS**: Do NOT run repo-wide `pytest` discoveries (even with `-m "not slow..."`), do NOT run `tests/e2e/` browser suites, and do NOT pipe unfiltered repo-wide test runs into `| tail` (which hides hanging browser/SSE sockets). In Stage 2, do NOT run `package_epic.py`.
   124	>      - **FINAL GATE ONLY**: Reserve the full regression suite, Playwright E2E browser harness, and full `quality_check` artifact regeneration strictly for the **Final Convergence Gate** (`AUTO_PASS_CLEAN`, `AUTO_PASS_FINAL_MINOR_SWEEP`, `AUTO_PASS_FINAL_SWEEP` with 0 Critical) after all code findings are resolved.
   125	>    - **Zero-Tolerance Anti-Evasion Rules (No Shortcut Fixes)**:
   126	>      - **No Dependency/Artifact Deletion**: Never resolve an unlocked dependency finding by removing the required package from `pyproject.toml`, and never resolve a stale quality report finding by simply deleting the report without regenerating it. If `uv.lock` is blocked by task scope rules, explicitly add `uv.lock` to the task's `Allowed files` and run `uv lock`.
   127	>      - **No Synthesized Fallback Fixtures**: When a finding flags fake/generated test data, do not replace it with another runtime generator. Load genuine immutable fixtures from disk and fail hard when missing.
   128	>      - **Browser Binary Synchronization**: Whenever `playwright` is added or upgraded in `pyproject.toml` / `uv.lock`, immediately run `uv run playwright install chromium` before invoking any browser E2E check.
   129	
   130	## 7. Multi-Repo Boundaries, Symlink Isolation & Contract Governance
   131	
   132	> [!CRITICAL]
   133	> **AI Agents MUST strictly respect repository boundaries, symbolic link isolation, and contract-first governance across multi-repo ecosystems (Hub and Satellite repositories).**
   134	>
   135	> 1. **Multi-Repo Git Boundary Isolation**:
   136	>    - An AI Agent running in any repository MUST NOT stage (`git add`) or commit (`git commit`) files residing outside the current git working tree.
   137	>    - In a Satellite repository where `shared-contracts/` is a symbolic link pointing to a Hub repository (e.g. `lyrics-sync` or `nexus` linking to `D3Nexus`):
   138	>      - Agents MUST treat `shared-contracts/` as **strictly read-only** for git tracking within the satellite workspace.
   139	>      - Agents **MUST NOT** include `shared-contracts/...` in `Files Allowed` for local git tasks (preventing `fatal: pathspec is beyond a symbolic link`).
   140	>      - Agents **MUST NOT** autonomously execute git commit commands in adjacent repositories (e.g. `git -C <target_repo>`) without explicit developer confirmation.
   141	>
   142	> 2. **Contract-First Triad & Canonical SSOT**:
   143	>    - The Hub repository containing the physical `shared-contracts/` directory is the sole canonical authority (Single Source of Truth) for contract commits.
   144	>    - Before modifying endpoints, database models, worker bridges, offline sync logic, or DTOs, agents MUST inspect the 3 canonical contract files in the relevant domain folder (`shared-contracts/<domain>/`):
   145	>      1. `api_contract.md`: Endpoints, wire format, headers, telemetry, and payload schemas.

exec
/bin/zsh -lc "env PYTHONDONTWRITEBYTECODE=1 python3 -B -c 'import sys, importlib.util, io, contextlib, json, re
from pathlib import Path
from unittest.mock import patch
root=Path.cwd()
scripts=root/'\\''skills/dev-implementation/resources/scripts'\\''
sys.path.insert(0,str(scripts))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
rer=load('\\''tto_probe_review'\\'',scripts/'\\''run_external_review.py'\\'')
for kind in ['\\''principal'\\'','\\''code'\\'']:
    record=rer.review_file(kind)[0]
    n=len(rer.rounds_in('\\''# '\\''+record+'\\''\\n'\\''))+1
    print('\\''proposed raw path'\\'', kind, record, '\\''=>'\\'', '\\''build/reviews/demo_round'\\''+str(n)+'\\''.raw.log'\\'')
print('\\''principal delta path selector covers VI =>'\\'', '\\''.devtool/epic/demo'\\'', '\\''(source glob includes every companion file)'\\'')
cd=load('\\''tto_probe_document'\\'',root/'\\''skills/doc_quality_check/resources/scripts/check_document.py'\\'')
en=Path('\\''/virtual/design.en.md'\\''); vi=Path('\\''/virtual/design.vi.md'\\'')
payload={en:'\\''# Design\\n\\n## Goals\\n\\nUse new model and concurrent execution.\\n'\\'',vi:'\\''# Thiết kế\\n\\n## Mục tiêu\\n\\nNội dung cũ: tuần tự.\\n'\\''}
with patch.object(Path,'\\''read_text'\\'',autospec=True,side_effect=lambda p,*a,**k:payload[p]):
    print('\\''stale translation, identical heading levels =>'\\'',cd.check_language_pairs([en,vi]))
cb=load('\\''tto_probe_bdd'\\'',scripts/'\\''check_bdd_traceability.py'\\'')
src=(scripts/'\\''check_bdd_traceability.py'\\'').read_text().replace('\\''args = parser.parse_args(argv)'\\'','\\''plan.add_argument(\"--strict-bilingual\", action=\"store_true\")\\n    args = parser.parse_args(argv)'\\'')
g=dict(cb.__dict__); g['\\''__name__'\\'']='\\''probe_only'\\''
exec(compile(src,str(scripts/'\\''check_bdd_traceability.py'\\''),'\\''exec'\\''),g)
out=io.StringIO()
with contextlib.redirect_stderr(out):
    try:g['\\''main'\\''](['\\''plan'\\'','\\''demo'\\'','\\''--strict-bilingual'\\''])
    except SystemExit as e:print('\\''Stage 4 prose command after adding flag =>'\\'',e.code,out.getvalue().strip().splitlines()[-1])
wp=load('\\''tto_probe_pool'\\'',scripts/'\\''manage_worker_pool.py'\\'')
worktree=Path('\\''/virtual/repo/.worktrees/demo_epic'\\'')
with patch.object(Path,'\\''is_dir'\\'',autospec=True,side_effect=lambda p:p==worktree), patch.object(wp.subprocess,'\\''run'\\'',side_effect=AssertionError('\\''Unexpected process'\\'')):
    print('\\''merge_slot(runner worktree root) =>'\\'',wp.merge_slot(worktree,'\\''demo_epic'\\'','\\''demo-epic'\\'',1))
for f in sorted((root/'\\''.devtool/epic/token_throttling_optimization'\\'').glob('\\''task_*.md'\\'')):
    text=f.read_text()
    allowed=text.split('\\''Allowed files:'\\'',1)[1].split('\\''Read-only context:'\\'',1)[0]
    missing=[]
    for p in re.findall(r'\\''- "'`([''^`]+)`'"'\\'',allowed):
        file=root/p
        if file.is_file() and p.endswith('\\''.py'\\'') and len(file.read_text().splitlines())>200:
            occurrences=[l for l in text.splitlines() if p in l and re.search(r'\\''L[0-9]+-L[0-9]+'\\'',l)]
            if not occurrences:missing.append(p)
    if missing:print('\\''future range guard without anchors'\\'', f.name, '\\''=>'\\'', missing)
print('\\''All operations used memory fixtures and mocks; no files written.'\\'')
'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
proposed raw path principal principal_review.md => build/reviews/demo_round1.raw.log
proposed raw path code review_results.md => build/reviews/demo_round1.raw.log
principal delta path selector covers VI => .devtool/epic/demo (source glob includes every companion file)
stale translation, identical heading levels => []
Stage 4 prose command after adding flag => 2 -c plan: error: the following arguments are required: --scenarios, --tasks
merge_slot(runner worktree root) => False
future range guard without anchors task_01_diff_only_external_review_and_transcript_isolation.md => ['skills/dev-implementation/resources/scripts/test_run_external_review.py']
future range guard without anchors task_02_silent_gate4_and_truncated_test_runners.md => ['skills/dev-implementation/resources/scripts/test_run_task_checks.py', 'skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py', 'tests/test_polyglot_gate4.py']
future range guard without anchors task_03_option_a_bilingual_and_surgical_contract_guards.md => ['skills/dev-implementation/resources/scripts/test_check_epic_readiness.py', 'skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py', 'skills/dev-implementation/resources/scripts/test_check_task_contract.py', 'skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py']
future range guard without anchors task_04_lifecycle_runner_programmer_config_and_pool_isolation.md => ['tests/test_lifecycle_runner.py']
All operations used memory fixtures and mocks; no files written.

codex
Probe đã xác nhận ba vấn đề: helper trả `False` cho cả đường dẫn shared-contract và mô tả mơ hồ về kiến trúc; lệnh Pre-Finish trong Task 5 thiếu các đối số bắt buộc; kiểm tra bilingual hiện tại chấp nhận bản dịch cũ nếu cấu trúc heading không đổi. Tôi đang rà lượt cuối để tách lỗi thiết kế khỏi lựa chọn triển khai và tránh báo trùng.

exec
/bin/zsh -lc "env PYTHONDONTWRITEBYTECODE=1 python3 -B -c 'import sys, importlib.util, json, re
from pathlib import Path
from unittest.mock import patch
root=Path.cwd(); scripts=root/'\\''skills/dev-implementation/resources/scripts'\\''; sys.path.insert(0,str(scripts))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
v=load('\\''tto_probe_poly'\\'',root/'\\''skills/quality_check/resources/scripts/verify_polyglot_registry.py'\\'')
for err in [OSError('\\''read failed'\\''), json.JSONDecodeError('\\''early'\\'','\\'''\\'',0)]:
    with patch.object(v,'\\''_get_git_head'\\'',return_value='\\''a'\\''*40),patch.object(Path,'\\''is_file'\\'',return_value=True),patch.object(Path,'\\''read_text'\\'',side_effect=err):
        r=v.execute_provider({'\\''id'\\'':'\\''custom-quality'\\'','\\''skill'\\'':'\\''custom'\\''},'\\''epic'\\'','\\''a'\\''*40,repo_root=root)
        print('\\''provider early manifest exception =>'\\'',type(err).__name__,r['\\''status'\\''],r['\\''blockers'\\''])
manifest={'\\''profiles'\\'':{'\\''epic'\\'':['\\''test'\\'']},'\\''capabilities'\\'':{'\\''test'\\'':['\\''missing-command'\\'']}}
with patch.object(v,'\\''_get_git_head'\\'',return_value='\\''a'\\''*40),patch.object(Path,'\\''is_file'\\'',return_value=True),patch.object(Path,'\\''read_text'\\'',return_value=json.dumps(manifest)),patch.object(Path,'\\''mkdir'\\''),patch.object(Path,'\\''write_text'\\'',side_effect=AssertionError('\\''Unexpected write'\\'')),patch.object(v.subprocess,'\\''run'\\'',side_effect=OSError('\\''spawn failed'\\'')):
    r=v.execute_provider({'\\''id'\\'':'\\''custom-quality'\\'','\\''skill'\\'':'\\''custom'\\''},'\\''epic'\\'','\\''a'\\''*40,repo_root=root)
    print('\\''provider early spawn exception =>'\\'',r['\\''status'\\''],r['\\''checks'\\''][0]['\\''summary'\\''])
import run_task_checks as rtc
print('\\''Task6 RED if caps already pass =>'\\'',rtc.validate_pytest_red('\\''python3 -m pytest -q tests/test_token_throttling_acceptance.py::test_tto_fr_04_quantitative_byte_ceilings'\\'',0,'\\''1 passed in 0.01s'\\''))
r=load('\\''tto_probe_external'\\'',scripts/'\\''run_external_review.py'\\'')
calls=[]
def fake_git(root_arg,*args):
    calls.append(args)
    if '\\''--stat'\\'' in args:return b'\\''docs/spec.vi.md | 1 +\\n'\\''
    return b'\\''diff --git a/docs/spec.vi.md b/docs/spec.vi.md\\n--- a/docs/spec.vi.md\\n+++ b/docs/spec.vi.md\\n@@ -1 +1 @@\\n-old\\n+new\\n'\\''
with patch.object(r,'\\''git_run'\\'',side_effect=fake_git):
    result=r.build_diff_section(root,'\\''main'\\'','\\''a'\\''*40)
    print('\\''source diff carries VI text =>'\\'', '\\''+new'\\'' in result, '\\''VI exclusions present =>'\\'',any('\\''vi.md'\\'' in a for a in calls[-1][5:]))
print('\\''No writes or real child processes occurred.'\\'')
'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
provider early manifest exception => OSError BLOCKED ["Failed to parse manifest '/Users/danhdueexoictif/AllProjects/ai-agent-tools/.agents/quality/custom-quality.json': read failed"]
provider early manifest exception => JSONDecodeError BLOCKED ["Failed to parse manifest '/Users/danhdueexoictif/AllProjects/ai-agent-tools/.agents/quality/custom-quality.json': early: line 1 column 1 (char 0)"]
provider early spawn exception => BLOCKED test: failed to execute: spawn failed
Task6 RED if caps already pass => Invalid pytest RED phase: must fail on a collected test (exit 1 or 2), not missing file (exit 4) or zero selected tests (exit 5).
source diff carries VI text => True VI exclusions present => False
No writes or real child processes occurred.

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/local_review.py | sed -n '245,276p'; nl -ba skills/dev-implementation/resources/scripts/test_run_external_review.py | sed -n '1035,1072p'; nl -ba skills/dev-implementation/resources/scripts/test_check_epic_readiness.py | sed -n '655,710p'; nl -ba skills/dev-implementation/resources/scripts/run_task_checks.py | sed -n '30,96p'; nl -ba skills/dev-implementation/resources/scripts/test_run_task_checks.py | sed -n '1,15p'; nl -ba skills/dev-implementation/resources/scripts/test_check_task_contract.py | sed -n '1,15p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
   245	               for block in scenario_blocks(scenarios, covers_of(task_path))),
   246	             Part("## Evidence", "evidence", evidence_lines(evidence) or "None.", None),
   247	             *(Part(diff_section, path, f"### {path}\n\n{fenced(diff, 'diff')}", ranks[path]) for path, diff in diffs)]
   248	    sections = ("## Task file", "## Scenarios covered", "## Evidence", diff_section)
   249	    return Slice(task, "task", tuple(path for path, _ in diffs), (), sections, tuple(parts))
   250	
   251	
   252	def epic_slice(root: Path, epic_path: str, base: str, sha: str, audit_output: str, results_output: str,
   253	               outside: list[str], excludes: tuple[str, ...]) -> Slice:
   254	    folder = root / epic_path
   255	    hld = folder / f"{Path(epic_path).name}.en.md"
   256	    specs = sorted(folder.glob("*-design.en.md"))
   257	    stat = git_text(root, "diff", "--stat", f"{base}...{sha}", "--", ".", ":(exclude).devtool/**").strip()
   258	    parts: list[Part] = []
   259	    paths: list[str] = []
   260	    for rank, commit in enumerate(outside):
   261	        title = git_text(root, "log", "-1", "--format=%h %s", commit).strip()
   262	        diffs = file_diffs(root, commit, excludes)
   263	        paths.extend(path for path, _ in diffs if path not in paths)
   264	        body = "\n\n".join(fenced(diff, "diff") for _, diff in diffs) or "No change outside excluded paths."
   265	        parts.append(Part("## Commits outside tasks", title, f"### {title}\n\n{body}", rank))
   266	    rank = len(outside)
   267	    parts += [Part("## Spec", spec.name, fenced(spec.read_text(encoding="utf-8"), "markdown"), rank + index)
   268	              for index, spec in enumerate(specs)]
   269	    parts += [Part("## HLD", hld.name, fenced(hld.read_text(encoding="utf-8"), "markdown"), rank + len(specs)),
   270	              Part("## Audit", "audit", fenced(audit_output, "text"), None),
   271	              Part("## Traceability", "traceability", fenced(results_output, "text"), None),
   272	              Part("## Diff stat", "diff stat", fenced(stat or "(no changes outside .devtool/)", "text"), None)]
   273	    if not outside:
   274	        parts.append(Part("## Commits outside tasks", "commits outside tasks", "None.", None))
   275	    sections = ("## Spec", "## HLD", "## Audit", "## Traceability", "## Diff stat", "## Commits outside tasks")
   276	    return Slice("epic", "epic", tuple(paths), (), sections, tuple(parts))
  1035	        self.install("claude")
  1036	        self.run_review(cli="claude", mode="pass")
  1037	        args = self.args.read_text().split()
  1038	        self.assertIn("--dangerously-skip-permissions", args)
  1039	        self.assertNotIn("--permission-mode", args)
  1040	
  1041	    def test_rts_hp_06_dynamic_probing_and_senior_rules_in_prompts(self) -> None:
  1042	        """[RTS-HP-06] Prompts contain Mandatory Dynamic Probing Rule and senior reviewer checklist."""
  1043	        from run_external_review import (
  1044	            PROMPT,
  1045	            RULES,
  1046	            principal_prompt_path,
  1047	            principal_rules_path,
  1048	        )
  1049	        ext_prompt = PROMPT.read_text(encoding="utf-8")
  1050	        ext_rules = RULES.read_text(encoding="utf-8")
  1051	        pr_prompt = principal_prompt_path().read_text(encoding="utf-8")
  1052	        pr_rules = principal_rules_path().read_text(encoding="utf-8")
  1053	        for p in (ext_prompt, pr_prompt):
  1054	            self.assertIn("Mandatory Dynamic Probing Rule", p)
  1055	        for r in (ext_rules, pr_rules):
  1056	            self.assertIn("5-Layer Deep Verification Checklist", r)
  1057	
  1058	    def test_rts_ec_01_ollama_requires_model_without_previous_round(self) -> None:
  1059	        """[RTS-EC-01] Ollama requires explicit --model if no previous round exists."""
  1060	        out, err = io.StringIO(), io.StringIO()
  1061	        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
  1062	            code = main(["run", "--epic-dir", "demo", "--base", self.base, "--cli", "ollama"])
  1063	        self.assertEqual(code, 2)
  1064	        self.assertIn("--cli ollama needs --model", err.getvalue())
  1065	
  1066	    def test_rts_ec_02_corrupted_config_falls_back_to_defaults(self) -> None:
  1067	        """[RTS-EC-02] Corrupted review_config.json falls back cleanly to defaults."""
  1068	        config_path = self.root / ".devtool" / "review_config.json"
  1069	        config_path.parent.mkdir(parents=True, exist_ok=True)
  1070	        config_path.write_bytes(b"\xff\xfe\x00\x00")
  1071	        cfg_utf8 = load_review_config(self.root)
  1072	        self.assertEqual(cfg_utf8["last_used_provider"], "claude")
   655	        self.update_task_both("task_2.md", modify_task)
   656	
   657	        code, stdout, _stderr = self.run_check("demo_epic")
   658	        self.assertEqual(code, 1, f"Expected 1, got {code}.\nStdout:\n{stdout}")
   659	        r6_fails = [line for line in stdout.splitlines() if line.startswith("R6 FAIL")]
   660	        self.assertTrue(r6_fails, f"Expected R6 FAIL in stdout:\n{stdout}")
   661	        self.assertTrue(
   662	            any("task_2" in line and "tests/test_extra.py" in line for line in r6_fails),
   663	            f"Expected R6 FAIL containing task_2 and tests/test_extra.py. Got:\n{stdout}",
   664	        )
   665	
   666	    def test_prv_ec_06_route_not_found_warns_r5b(self) -> None:
   667	        """PRV-EC-06: A route found in no source file warns R5b without failing."""
   668	        (self.root / "tool.py").write_text(
   669	            'ENDPOINT = "/api/studio/extract/start"\ndef run():\n    pass\n',
   670	            encoding="utf-8",
   671	        )
   672	        git_cmd(self.root, "add", "tool.py")
   673	        git_cmd(self.root, "commit", "-m", "update tool.py with endpoint", "-q")
   674	
   675	        def modify_task(text: str) -> str:
   676	            return text.replace(
   677	                "Requirement text for task 1.",
   678	                "Requirement text for task 1 calling /api/tts/ocr-upload endpoint.",
   679	            )
   680	
   681	        self.update_task_both("task_1.md", modify_task)
   682	
   683	        code, stdout, _stderr = self.run_check("demo_epic")
   684	        self.assertEqual(code, 0, f"Expected 0, got {code}.\nStdout:\n{stdout}")
   685	        r5b_warns = [line for line in stdout.splitlines() if line.startswith("R5b WARN")]
   686	        self.assertTrue(r5b_warns, f"Expected R5b WARN in stdout:\n{stdout}")
   687	        self.assertTrue(
   688	            any("/api/tts/ocr-upload" in line for line in r5b_warns),
   689	            f"Expected R5b WARN containing /api/tts/ocr-upload. Got:\n{stdout}",
   690	        )
   691	        self.assertFalse(any("/api/studio/extract/start" in line for line in stdout.splitlines()))
   692	        self.assertEqual(stdout.strip().splitlines()[-1], "Result: 0 FAIL, 1 WARN — PASS")
   693	
   694	    def test_prv_fr_01_baseline_failures_and_timeouts_warn(self) -> None:
   695	        """PRV-FR-01: Baseline failures and timeouts warn and other rows still run."""
   696	        # Ensure clean git tree by committing existing files
   697	        git_cmd(self.root, "add", "-A")
   698	        git_cmd(self.root, "commit", "-m", "setup baseline clean tree", "-q")
   699	
   700	        # 1. Update task_1 with rows:
   701	        # V2 GREEN: python3 -c 'raise SystemExit(1)' expecting exit 0
   702	        # V3 TIER-B: sleep 5 expecting exit 0
   703	        # V4 GREEN: python3 -c 'print(1)' expecting exit 0
   704	        def modify_task_1(text: str) -> str:
   705	            text = text.replace(
   706	                "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
   707	                "| V2 | GREEN | `python3 -c 'raise SystemExit(1)'` | exit 0 | — |\n| V3 | TIER-B | `sleep 5` | exit 0 | — |\n| V4 | GREEN | `python3 -c 'print(1)'` | exit 0 | — |",
   708	            )
   709	            text = text.replace(
   710	                "| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n| V4 | TIER-B | `mypy tool.py` | exit 0 | — |",
    30	    UTC = timezone.utc  # type: ignore[attr-defined]
    31	from pathlib import Path
    32	from typing import Any, cast
    33	
    34	_tc: Any = importlib.import_module("task_contract")
    35	CONTROL_TOKENS: set[str] = _tc.CONTROL_TOKENS
    36	ContractError: type[Exception] = _tc.ContractError
    37	EpicLayout: Any = _tc.EpicLayout
    38	Row: Any = _tc.Row
    39	changed_paths: Any = _tc.changed_paths
    40	epic_layout: Any = _tc.epic_layout
    41	evaluate_done_gate: Any = _tc.evaluate_done_gate
    42	fingerprint: Any = _tc.fingerprint
    43	git_run: Any = _tc.git_run
    44	load_evidence: Any = _tc.load_evidence
    45	parse_allowed_files: Any = _tc.parse_allowed_files
    46	parse_evidence_files: Any = _tc.parse_evidence_files
    47	parse_protected_paths: Any = _tc.parse_protected_paths
    48	parse_verification: Any = _tc.parse_verification
    49	path_matches: Any = _tc.path_matches
    50	program_of: Any = _tc.program_of
    51	row_problems: Any = _tc.row_problems
    52	save_evidence: Any = _tc.save_evidence
    53	
    54	KIT_ROOT = Path(__file__).resolve().parents[4]
    55	
    56	
    57	def kit_env() -> dict[str, str]:
    58	    env = dict(os.environ)
    59	    env["D3NEXUS_KIT"] = str(KIT_ROOT)
    60	    bin_dir = str(KIT_ROOT / "bin")
    61	    current_path = os.environ.get("PATH", "")
    62	    env["PATH"] = f"{bin_dir}{os.pathsep}{current_path}" if current_path else bin_dir
    63	    return env
    64	section: Any = _tc.section
    65	strip_wrappers: Any = _tc.strip_wrappers
    66	
    67	_rr: Any = importlib.import_module("result_reports")
    68	ReportError: type[Exception] = _rr.ReportError
    69	digest: Any = _rr.digest
    70	load_files: Any = _rr.load_files
    71	report_files: Any = _rr.report_files
    72	
    73	_cbt: Any = importlib.import_module("check_bdd_traceability")
    74	UsageError: type[Exception] = _cbt.UsageError
    75	load_scenarios: Any = _cbt.load_scenarios
    76	
    77	TAIL_LINES = 40
    78	VERIFY_PHASES = ("GREEN", "TIER-B", "TIER-C")
    79	STALE = "results not produced by this run"
    80	
    81	INVALID_PYTEST_RED_REASON = (
    82	    "Invalid pytest RED phase: must fail on a collected test (exit 1 or 2), "
    83	    "not missing file (exit 4) or zero selected tests (exit 5)."
    84	)
    85	
    86	FORBIDDEN_MARKERS = (
    87	    re.compile(r"ERROR:\s*file or directory not found", re.IGNORECASE),
    88	    re.compile(r"collected\s+0\s+items", re.IGNORECASE),
    89	    re.compile(r"/\s*0\s+selected\b", re.IGNORECASE),
    90	)
    91	POSITIVE_FAILURE_SUMMARY = re.compile(r"\b([1-9]\d*)\s+(?:failed|error|errors)\b", re.IGNORECASE)
    92	COVERS_LINE_RE = re.compile(r"^\s*(?:[-*]\s+)?\**Covers\**\s*:\**\s*(.*)$")
    93	ID_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9-])[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]+(?![A-Za-z0-9])")
    94	
    95	
    96	def is_pytest_command(command: str) -> bool:
     1	#!/usr/bin/env python3
     2	"""Tests for task_contract.py and run_task_checks.py.
     3	
     4	Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_run_task_checks.py
     5	"""
     6	from __future__ import annotations
     7	import contextlib
     8	import importlib
     9	import io
    10	import json
    11	import os
    12	import subprocess
    13	import sys
    14	import tempfile
    15	import unittest
     1	#!/usr/bin/env python3
     2	"""Tests for check_task_contract.py.
     3	
     4	Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_check_task_contract.py
     5	"""
     6	from __future__ import annotations
     7	import contextlib
     8	import io
     9	import json
    10	import os
    11	import re
    12	import subprocess
    13	import sys
    14	import tempfile
    15	import unittest

exec
/bin/zsh -lc "env PYTHONDONTWRITEBYTECODE=1 python3 -B -c 'import importlib.util, sys, subprocess, re
from pathlib import Path
from unittest.mock import patch, MagicMock
root=Path.cwd()
p=root/'\\''skills/dev-lifecycle/resources/scripts/lifecycle_runner.py'\\''
spec=importlib.util.spec_from_file_location('\\''final_probe_lifecycle'\\'',p); m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)
r=object.__new__(m.LifecycleRunner); r.root=root; r.epic_slug='\\''demo'\\''; r.config=m.RunnerConfig(); r.dispatcher=MagicMock(); r.dispatcher.dispatch.return_value=(1,'\\'''\\'','\\''fixer failed'\\'')
with patch.object(m.subprocess,'\\''run'\\'',return_value=subprocess.CompletedProcess([],0,'\\'''\\'','\\'''\\'')):
    print('\\''failed code fixer returns =>'\\'',r._apply_code_fixes(1))
prompt=r.dispatcher.dispatch.call_args.kwargs['\\''prompt'\\'']
print('\\''default direct-fix prompt contains review artifact path =>'\\'',any(x in prompt for x in ['\\''review_results.md'\\'','\\''principal_review.md'\\'']))
print('\\''default direct-fix prompt =>'\\'',repr(prompt))
for path in ['\\''skills/dev-implementation/resources/scripts/test_run_external_review.py'\\'','\\''skills/dev-implementation/resources/scripts/test_check_epic_readiness.py'\\'','\\''tests/test_lifecycle_runner.py'\\'']:
    print('\\''tracked source size'\\'',path,len((root/path).read_text().splitlines()),'\\''lines'\\'')
for path in [root/'\\''skills/dev-implementation/resources/scripts/run_external_review.py'\\'',root/'\\''skills/dev-lifecycle/resources/scripts/lifecycle_runner.py'\\'',root/'\\''scripts/resume_context.py'\\'',root/'\\''skills/quality_check/resources/scripts/verify_polyglot_registry.py'\\'']:
    text=path.read_text()
    print('\\''morphology/ORM imports'\\'',path.name, bool(re.search(r'\\''"'^(?:from|import) (?:sqlalchemy|spacy|nltk)'"\\b'\\'',text,re.M)))
print('\\''All mutation sites were mocked; no repository or git operations performed.'\\'')
'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
failed code fixer returns => True
default direct-fix prompt contains review artifact path => False
default direct-fix prompt => 'You are the AI Programmer (Role 2.3). Implement the code fixes for Cross-Model Review Round 1.\nApproved Fix Plan:\n\n\n\nApply the changes, verify tests pass, and adhere to strict TDD.\n'
tracked source size skills/dev-implementation/resources/scripts/test_run_external_review.py 1508 lines
tracked source size skills/dev-implementation/resources/scripts/test_check_epic_readiness.py 899 lines
tracked source size tests/test_lifecycle_runner.py 629 lines
morphology/ORM imports run_external_review.py False
morphology/ORM imports lifecycle_runner.py False
morphology/ORM imports resume_context.py False
morphology/ORM imports verify_polyglot_registry.py False
All mutation sites were mocked; no repository or git operations performed.

exec
/bin/zsh -lc "nl -ba skills/dev-lifecycle/resources/scripts/lifecycle_runner.py | sed -n '722,770p'; nl -ba skills/dev-implementation/resources/scripts/check_epic_readiness.py | sed -n '645,698p'; nl -ba skills/dev-lifecycle/references/handoff-template.md | sed -n '22,65p'; nl -ba skills/dev-implementation/resources/scripts/test_run_external_review.py | sed -n '1255,1292p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
   722	
   723	    def evaluate_circuit_breakers(
   724	        self,
   725	        stage: str,
   726	        round_num: int,
   727	        triage_stdout: str = "",
   728	    ) -> str | None:
   729	        """Evaluate circuit breaker triggers across review rounds."""
   730	        content = triage_stdout
   731	        if not content:
   732	            review_script = (
   733	                self.root
   734	                / "skills"
   735	                / "dev-implementation"
   736	                / "resources"
   737	                / "scripts"
   738	                / "run_external_review.py"
   739	            )
   740	            if review_script.is_file():
   741	                triage_cmd = [
   742	                    sys.executable,
   743	                    str(review_script),
   744	                    "triage",
   745	                    "--kind",
   746	                    stage,
   747	                    "--epic-dir",
   748	                    self.epic_slug,
   749	                    "--max-rounds",
   750	                    str(self.config.max_review_rounds),
   751	                ]
   752	                res = subprocess.run(triage_cmd, cwd=self.root, capture_output=True, text=True, check=False)
   753	                content = res.stdout
   754	
   755	        if "CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)" in content:
   756	            return "CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)"
   757	        if "CIRCUIT_BREAKER_HALT (FIX_LOOP)" in content:
   758	            return "CIRCUIT_BREAKER_HALT (FIX_LOOP)"
   759	        if "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)" in content:
   760	            return "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
   761	        if round_num >= self.config.max_review_rounds and "Critical" in content:
   762	            return "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
   763	        return None
   764	
   765	    def prompt_human_principal_fixes(self, triage_summary: str) -> bool:
   766	        """Prompt Human Architect for confirmation when critical/contract conflicts occur."""
   767	        print("\n" + "=" * 70)
   768	        print("⚠️ [HUMAN CHECKPOINT] Principal Review requires confirmation for critical or domain conflicts:")
   769	        print(triage_summary)
   770	        print("=" * 70 + "\n")
   645	def check_metadata(ctx: Context) -> list[Finding]:
   646	    findings: list[Finding] = []
   647	    epic_path = ctx.root / ".devtool" / "epic" / ctx.epic_dir
   648	    handoff_file = epic_path / "handoff.md"
   649	    has_handoff = handoff_file.is_file()
   650	
   651	    prereq_dirs, prereq_errors = tc.resolve_prerequisite_epic_dirs(
   652	        ctx.root, ctx.hld_text, ctx.epic_dir
   653	    )
   654	    for err in prereq_errors:
   655	        findings.append(Finding("R7", "FAIL", err))
   656	
   657	    en_errata: list[tuple[str, str]] = []
   658	    vi_errata: list[tuple[str, str]] = []
   659	    try:
   660	        en_errata = tc.parse_spec_errata(ctx.hld_text)
   661	    except tc.ContractError as err:
   662	        findings.append(Finding("R7", "FAIL", str(err)))
   663	        return findings
   664	
   665	    vi_file = ctx.root / ".devtool" / "epic" / ctx.epic_dir / f"{ctx.epic_dir}.vi.md"
   666	    if vi_file.is_file():
   667	        try:
   668	            vi_text = vi_file.read_text(encoding="utf-8")
   669	            if tc.parse_depends_on_epics(vi_text) != tc.parse_depends_on_epics(ctx.hld_text):
   670	                findings.append(
   671	                    Finding(
   672	                        "R7", "FAIL", "Depends on epic differs between .en.md and .vi.md"
   673	                    )
   674	                )
   675	            try:
   676	                vi_errata = tc.parse_spec_errata(vi_text)
   677	            except tc.ContractError as err:
   678	                findings.append(Finding("R7", "FAIL", str(err)))
   679	                return findings
   680	
   681	            if [eid for eid, _ in en_errata] != [eid for eid, _ in vi_errata]:
   682	                findings.append(
   683	                    Finding(
   684	                        "R7",
   685	                        "FAIL",
   686	                        f"Spec Errata IDs differ between .en.md and .vi.md: {[e for e, _ in en_errata]} vs {[e for e, _ in vi_errata]}",
   687	                    )
   688	                )
   689	        except OSError:
   690	            pass
   691	
   692	    status_match = re.search(r"^- \*\*Status\*\*:\s*(.*)$", ctx.hld_text, re.MULTILINE)
   693	    hld_status = status_match.group(1).strip() if status_match else ""
   694	
   695	    if hld_status.startswith("Packaged") and not has_handoff:
   696	        findings.append(Finding("R7", "FAIL", "Status starts with Packaged but handoff.md is missing"))
   697	
   698	    if has_handoff:
    22	
    23	## Identifiers
    24	
    25	| Placeholder | Value |
    26	|-------------|-------|
    27	| `<epic_dir>` | `<epic_dir value>` |
    28	| `<epic_slug>` | `<epic_slug value>` |
    29	
    30	These are usually different strings. Never derive one from the other.
    31	
    32	## Read First
    33	
    34	1. `.devtool/epic/<epic_dir>/<epic_dir>.en.md` — the HLD. Its Kanban Tasks Breakdown lists the <N> tasks.
    35	2. `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` — the behavioural contract.
    36	3. `.devtool/epic/<epic_dir>/<source spec>.en.md` — the approved source spec.
    37	4. `.devtool/epic/<epic_dir>/principal_review.md`, when present — Principal Review rounds and decisions.
    38	
    39	## Resume Prompt
    40	
    41	```text
    42	[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]
    43	Use the d3nexus:dev-implementation skill for the `<epic_slug>` epic.
    44	Read .devtool/epic/<epic_dir>/handoff.md first.
    45	Run: python3 scripts/resume_context.py --role programmer --epic <epic_slug>
    46	Apply the Execution Guardrails for Receiving LLM before presenting Gate 3.
    47	Gates 1 and 2 are passed; do not re-run brainstorming or design.
    48	Gate 3 (execution order) and worktree creation run automatically. Begin task execution in accordance with the resolved order.
    49	```
    50	
    51	## Execution Guardrails for Receiving LLM
    52	
    53	Fast executor models and receiving agents MUST adhere to these four hard guardrails throughout implementation:
    54	
    55	1. **Bounded context protocol**:
    56	   - Step 1: Read only the active task file (`.devtool/features/task_*.md`).
    57	   - Step 2: Read only the exact files declared in `Allowed files` and `Read-only context`.
    58	   - Step 3: Look up exact symbol definitions identified under `## Decisions Already Made`.
    59	   Undirected whole-repository searches (`grep`, `find`, `list_dir`) are forbidden unless an unresolved import explicitly requires symbol lookup.
    60	2. **Strict spec fidelity**: Frozen constants, defaults, retry counts, fallback conditions, signatures, and call paths under `## Decisions Already Made` and the HLD are hard contracts. Any mismatch causes STOP and report rather than an executor-side simplification.
    61	3. **Zero test fakery**: Tests import or invoke real production symbols and do not reconstruct retry loops, progress math, callback behavior, or configuration resolution.
    62	4. **No contract repair by the executor**: The receiver never edits Verification tables, Allowed files, Definition of Done, Covers lines, protected paths, or frozen contract facts.
    63	
    64	## Open Notes
    65	
  1255	            "# Cross-Model Review: demo\n\n"
  1256	            "## Round 1\n\n- **SHA**: 1111111\n- **CLI**: claude\n- **Model**: claude-opus-4-6\n"
  1257	            "- **Thinking**: high\n- **Status**: completed\n- **Verdict**: CHANGES REQUIRED\n\n"
  1258	            "| # | Severity | Location | Problem | Decision |\n"
  1259	            "|---|----------|----------|---------|----------|\n"
  1260	            "| 1 | Critical | demo.en.md, task_08 | Epic changes 7 wire steps to 5 steps not in shared-contracts/ |  |\n\n"
  1261	            "Raw output:\n\n```text\nVerdict: CHANGES REQUIRED\n```\n",
  1262	            encoding="utf-8",
  1263	        )
  1264	        out4 = io.StringIO()
  1265	        with contextlib.redirect_stdout(out4):
  1266	            main(["triage", "--epic-dir", "demo"])
  1267	        self.assertIn("CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)", out4.getvalue())
  1268	        self.assertIn("STOP IMMEDIATELY", out4.getvalue())
  1269	
  1270	        # 5. Round 3 with remaining Critical finding -> CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)
  1271	        self.results.write_text(
  1272	            "# Cross-Model Review: demo\n\n"
  1273	            "## Round 1\n\n- **SHA**: 1111111\n- **CLI**: claude\n- **Model**: claude-opus-4-6\n"
  1274	            "- **Thinking**: high\n- **Status**: completed\n- **Verdict**: CHANGES REQUIRED\n\n"
  1275	            "| # | Severity | Location | Problem | Decision |\n"
  1276	            "|---|----------|----------|---------|----------|\n"
  1277	            "| 1 | Important | src/a.py:10 | missing check | fixed in 2222222 |\n\n"
  1278	            "Raw output:\n\n```text\nVerdict: CHANGES REQUIRED\n```\n\n"
  1279	            "## Round 2\n\n- **SHA**: 2222222\n- **CLI**: claude\n- **Model**: claude-opus-4-6\n"
  1280	            "- **Thinking**: high\n- **Status**: completed\n- **Verdict**: CHANGES REQUIRED\n\n"
  1281	            "| # | Severity | Location | Problem | Decision |\n"
  1282	            "|---|----------|----------|---------|----------|\n"
  1283	            "| 1 | Important | src/b.py:20 | edge case | fixed in 3333333 |\n\n"
  1284	            "Raw output:\n\n```text\nVerdict: CHANGES REQUIRED\n```\n\n"
  1285	            "## Round 3\n\n- **SHA**: 3333333\n- **CLI**: claude\n- **Model**: claude-opus-4-6\n"
  1286	            "- **Thinking**: high\n- **Status**: completed\n- **Verdict**: CHANGES REQUIRED\n\n"
  1287	            "| # | Severity | Location | Problem | Decision |\n"
  1288	            "|---|----------|----------|---------|----------|\n"
  1289	            "| 1 | Critical | src/c.py:30 | fatal crash |  |\n\n"
  1290	            "Raw output:\n\n```text\nVerdict: CHANGES REQUIRED\n```\n",
  1291	            encoding="utf-8",
  1292	        )

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/run_external_review.py | sed -n '1590,1708p'; nl -ba tests/test_lifecycle_runner.py | sed -n '385,482p'; nl -ba .devtool/epic/token_throttling_optimization/2026-11-13-token-throttling-optimization-design.en.md | sed -n '63,68p;90,111p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
  1590	
  1591	
  1592	def _finding_risk_sort_key(row: list[str]) -> tuple[int, int, int, int, int]:
  1593	    """Rank findings by (severity_rank, is_not_shared_contract, is_non_prod_path, missing_high_risk_keyword, original_index)."""
  1594	    sev_rank = {"Critical": 0, "Important": 1, "Minor": 2}.get(row[1], 3)
  1595	    not_contract = 0 if is_shared_contract_conflict(row) else 1
  1596	    loc = row[2].lower()
  1597	    prob = row[3].lower()
  1598	    is_non_prod = 0 if (loc.startswith("src/") or "shared-contracts" in loc or "bdd_scenarios" in loc) else 1
  1599	    has_risk_kw = 0 if any(kw in prob or kw in loc for kw in HIGH_RISK_KEYWORDS) else 1
  1600	    try:
  1601	        idx = int(row[0])
  1602	    except ValueError:
  1603	        idx = 999
  1604	    return (sev_rank, not_contract, is_non_prod, has_risk_kw, idx)
  1605	
  1606	
  1607	def top_risk_findings_section(latest: list[list[str]], limit: int = 3) -> list[str]:
  1608	    """Filter and rank the Top 3 highest-risk findings for executive reporting and design-anchored fixing."""
  1609	    if not latest:
  1610	        return [
  1611	            f"## Top {limit} Highest-Risk Findings (Executive Report)",
  1612	            "",
  1613	            "None.",
  1614	        ]
  1615	    ranked = sorted(latest, key=_finding_risk_sort_key)[:limit]
  1616	    lines = [
  1617	        f"## Top {limit} Highest-Risk Findings (Executive Report)",
  1618	        "",
  1619	        "> **Strict Approved-Design Anchoring & Forward-Alignment Rule**: Tier 1 (User-approved Spec `*-design.en.md` & HLD `<epic_dir>.en.md`) "
  1620	        "takes precedence over legacy `shared-contracts/` and legacy `src/` code. When Tier 1 intentionally changes steps/enums/schemas "
  1621	        "(e.g. 7 steps -> 5 steps) but `shared-contracts/` or `src/` still holds legacy values, NEVER propose reverting Tier 1 to the old design; "
  1622	        "always propose **Forward Alignment** (update `shared-contracts/` + `sync_contracts.py ack` and add affected `src/` files to task `Allowed files`).",
  1623	        "",
  1624	        "| Rank | # | Severity | Location | Problem | Design Anchor (HLD / BDD / Decisions Already Made) | Proposed action |",
  1625	        "|------|---|----------|----------|---------|----------------------------------------------------|-----------------|",
  1626	    ]
  1627	    for rank, cells in enumerate(ranked, 1):
  1628	        lines.append(f"| #{rank} | {cells[0]} | {cells[1]} | {cell(cells[2])} | {cell(cells[3])} | ? | ? |")
  1629	    return lines
  1630	
  1631	
  1632	def auto_triage_section(
  1633	    number: int,
  1634	    rounds: list[tuple[int, list[str]]],
  1635	    latest: list[list[str]],
  1636	    max_rounds: int = MAX_REVIEW_ROUNDS,
  1637	) -> list[str]:
  1638	    """Severity-Tiered Auto-Triage Gate & Circuit Breaker evaluation for the latest round."""
  1639	    blocking_rows = [cells for cells in latest if cells[1] in BLOCKING]
  1640	    critical_rows = [cells for cells in latest if cells[1] == "Critical"]
  1641	    important_rows = [cells for cells in latest if cells[1] == "Important"]
  1642	    minor_rows = [cells for cells in latest if cells[1] == "Minor"]
  1643	    contract_conflict_rows = [cells for cells in blocking_rows if is_shared_contract_conflict(cells)]
  1644	    fix_loop_paths: list[str] = []
  1645	    if len(rounds) >= 2 and blocking_rows:
  1646	        prev_fixed_paths = {
  1647	            path_of(prev[2])
  1648	            for prev in finding_rows(rounds[-2][1])
  1649	            if prev[4].startswith("fixed in ")
  1650	        }
  1651	        for row in blocking_rows:
  1652	            p = path_of(row[2])
  1653	            if p and p in prev_fixed_paths and p not in fix_loop_paths:
  1654	                fix_loop_paths.append(p)
  1655	
  1656	    if not blocking_rows:
  1657	        action = "AUTO_PASS_FINAL_MINOR_SWEEP" if minor_rows else "AUTO_PASS_CLEAN"
  1658	        reason = (
  1659	            f"0 Critical and 0 Important findings ({len(minor_rows)} Minor). "
  1660	            "Fix valid Minor items once (strictly anchored to approved HLD/BDD/Task contracts), run local quality gate green, "
  1661	            "and finish stage immediately without calling external reviewer again."
  1662	            if minor_rows
  1663	            else "0 findings. Stage review passed cleanly."
  1664	        )
  1665	    elif contract_conflict_rows:
  1666	        ids = ", ".join(f"#{r[0]}" for r in contract_conflict_rows)
  1667	        action = "CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)"
  1668	        reason = (
  1669	            f"Shared-contract conflict detected in finding(s) {ids}: directly impacts `shared-contracts/` "
  1670	            "(`api_contract.md` / `architecture_and_flow.md` / `gaps_and_rfcs.md`). "
  1671	            "STOP IMMEDIATELY — do NOT auto-fix, do NOT revert user-approved HLD steps/schemas to legacy contracts, "
  1672	            "and do NOT continue autonomous execution. Report Top 3 Highest-Risk Findings to Human Architect immediately."
  1673	        )
  1674	    elif fix_loop_paths:
  1675	        action = "CIRCUIT_BREAKER_HALT (FIX_LOOP)"
  1676	        reason = (
  1677	            f"Fix Loop detected across consecutive rounds on {', '.join(fix_loop_paths)}. "
  1678	            "STOP IMMEDIATELY — halt auto-pilot and escalate Top 3 Highest-Risk Findings to Human Architect."
  1679	        )
  1680	    elif number >= max_rounds and critical_rows:
  1681	        ids = ", ".join(f"#{r[0]}" for r in critical_rows)
  1682	        action = "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
  1683	        reason = (
  1684	            f"After {number}/{max_rounds} review rounds, {len(critical_rows)} Critical finding(s) ({ids}) still remain unresolved. "
  1685	            "STOP IMMEDIATELY — do NOT continue autonomous execution; report Top 3 Highest-Risk Findings to Human Architect."
  1686	        )
  1687	    elif number >= max_rounds:
  1688	        action = "AUTO_PASS_FINAL_SWEEP"
  1689	        reason = (
  1690	            f"Round {number}/{max_rounds} reached max_rounds with 0 Critical findings ({len(important_rows)} Important, {len(minor_rows)} Minor, no Fix Loop or contract conflict). "
  1691	            "Apply one final fix sweep anchored to approved design, run local quality gate green, and finish stage without invoking a 4th review round."
  1692	        )
  1693	    else:
  1694	        action = "AUTO_FIX_ELIGIBLE"
  1695	        reason = (
  1696	            f"Round {number}/{max_rounds} has {len(blocking_rows)} Critical/Important finding(s) and no Fix Loop or shared-contract conflict. "
  1697	            "Verify against source and approved design (Spec, HLD, bdd_scenarios.en.md, Decisions Already Made): "
  1698	            "if Valid (and zero CRITICAL_CONFLICT or Debatable trade-offs), auto-record decisions, "
  1699	            "revise docs in Role 2.2 (or fix code in Role 2.3), run local quality gate, "
  1700	            "and advance to next review round."
  1701	        )
  1702	    return [
  1703	        "## Auto-Triage Gate",
  1704	        "",
  1705	        f"- **Action**: {action}",
  1706	        f"- **Round**: {number} / {max_rounds}",
  1707	        f"- **Directive**: {reason}",
  1708	    ]
   385	            mock_proc.stdout = mock_triage
   386	            mock_run.return_value = mock_proc
   387	
   388	            with patch.object(runner, "_draft_fix_plan", return_value="Draft fix plan"):
   389	                with patch.object(
   390	                    runner,
   391	                    "evaluate_programmer_fix_plan",
   392	                    return_value=(
   393	                        FixPlanVerdict.CRITICAL_CONFLICT,
   394	                        "Attempted unilateral contract modification",
   395	                    ),
   396	                ):
   397	                    ok = runner.step_cross_model_review()
   398	                    self.assertFalse(ok)
   399	                    self.assertEqual(runner.state.active_stage, StageName.HALTED.value)
   400	                    self.assertIn("CRITICAL_CONFLICT", str(runner.state.halt_reason))
   401	
   402	        # Direct evaluation fail-closed checks
   403	        with patch.object(runner.dispatcher, "dispatch", return_value=(124, "", "Process timed out")):
   404	            verdict, rationale = runner.evaluate_programmer_fix_plan(1)
   405	            self.assertEqual(verdict, FixPlanVerdict.CRITICAL_CONFLICT)
   406	            self.assertIn("timed out", rationale)
   407	
   408	        with patch.object(runner.dispatcher, "dispatch", return_value=(0, "Unrecognized rambling reply", "")):
   409	            verdict, rationale = runner.evaluate_programmer_fix_plan(1)
   410	            self.assertEqual(verdict, FixPlanVerdict.CRITICAL_CONFLICT)
   411	            self.assertIn("Unparseable fix plan verdict", rationale)
   412	
   413	    def test_alr_ec_03(self) -> None:
   414	        """[ALR-EC-03] AI Assistant adjusts AI Programmer fix plan without rejecting."""
   415	        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)
   416	
   417	        mock_triage_r1 = (
   418	            "## Auto-Triage Gate\n\n"
   419	            "- **Action**: AUTO_FIX_ELIGIBLE\n"
   420	            "- **Round**: 1 / 3\n"
   421	            "- **Directive**: 1 Important finding.\n"
   422	        )
   423	        mock_triage_r2 = (
   424	            "## Auto-Triage Gate\n\n"
   425	            "- **Action**: AUTO_PASS_CLEAN\n"
   426	            "- **Round**: 2 / 3\n"
   427	            "- **Directive**: 0 findings. Stage review passed cleanly.\n"
   428	        )
   429	
   430	        with patch("subprocess.run") as mock_run:
   431	            mock_proc_r1 = MagicMock()
   432	            mock_proc_r1.returncode = 0
   433	            mock_proc_r1.stdout = mock_triage_r1
   434	
   435	            mock_proc_r2 = MagicMock()
   436	            mock_proc_r2.returncode = 0
   437	            mock_proc_r2.stdout = mock_triage_r2
   438	
   439	            mock_run.side_effect = [mock_proc_r1, mock_proc_r1, mock_proc_r2, mock_proc_r2]
   440	
   441	            with patch.object(runner, "_draft_fix_plan", return_value="Draft fix plan"):
   442	                with patch.object(
   443	                    runner,
   444	                    "evaluate_programmer_fix_plan",
   445	                    return_value=(
   446	                        FixPlanVerdict.ADJUSTED,
   447	                        "Add edge-case assertion for null payload",
   448	                    ),
   449	                ):
   450	                    with patch.object(runner, "_apply_code_fixes") as mock_apply:
   451	                        with patch.object(runner, "_record_review_decisions"):
   452	                            with patch.object(runner, "run_gate4", return_value=(True, "Gate 4 PASS")):
   453	                                ok = runner.step_cross_model_review()
   454	                                self.assertTrue(ok)
   455	                                self.assertEqual(runner.state.last_verdict, FixPlanVerdict.ADJUSTED.value)
   456	                                mock_apply.assert_called_once()
   457	                                self.assertIn("Add edge-case assertion", mock_apply.call_args[1].get("plan_text", ""))
   458	
   459	    def test_alr_hp_04(self) -> None:
   460	        """[ALR-HP-04] AI Assistant approves AI Programmer fix plan in Cross-Model Review without Human stop."""
   461	        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)
   462	
   463	        mock_triage_r1 = (
   464	            "## Auto-Triage Gate\n\n"
   465	            "- **Action**: AUTO_FIX_ELIGIBLE\n"
   466	            "- **Round**: 1 / 3\n"
   467	            "- **Directive**: 1 Critical finding.\n"
   468	        )
   469	        mock_triage_r2 = (
   470	            "## Auto-Triage Gate\n\n"
   471	            "- **Action**: AUTO_PASS_CLEAN\n"
   472	            "- **Round**: 2 / 3\n"
   473	            "- **Directive**: 0 findings. Stage review passed cleanly.\n"
   474	        )
   475	
   476	        with patch("subprocess.run") as mock_run:
   477	            mock_proc_r1 = MagicMock()
   478	            mock_proc_r1.returncode = 0
   479	            mock_proc_r1.stdout = mock_triage_r1
   480	
   481	            mock_proc_r2 = MagicMock()
   482	            mock_proc_r2.returncode = 0
    63	- **No Duplicate `base...sha` in Round >= 2**: In `run_external_review.py` (`run()`), when `round_num >= 2` and `delta_round_context()` is active, omit the redundant full `base...sha` `diff_section`. Pass only `prev_sha..sha` delta diff (`-U5`), Prior Fixed Locations Registry, compact open findings summary (<= 200 chars per cell), and referenced Acceptance Criteria / task sections.
    64	- **English SSOT Only for Reviews**: Update `principal_artefact_lines()` and `collect_facts()` in `run_external_review.py` to exclude all `*.vi.md` paths from external reviewer context.
    65	- **Quiet Pre-Check Facts**: Replace verbatim `fact()` output in `collect_facts()` with `PASS: <label>` (1 line) when `returncode == 0`, and failing command + last 25 lines of combined output when non-zero.
    66	- **Transcript Isolation (`Raw output:`)**: In `render_round()`, route full external CLI `stderr` transcripts (and raw verbose payloads above summary bounds) to git-ignored `build/reviews/<epic>_round<n>.raw.log`, keeping `principal_review.md` and `review_results.md` limited to structured Verdict, Pass summary, and Findings tables plus a single log path pointer.
    67	- **Prompt Rules**: Inject `DIFF-ONLY REVIEW` constraints into `principal-review-prompt.md` and `external-review-prompt.md` forbidding full file reads unless resolving an explicit missing symbol or caller chain.
    68	
    90	  - Define high-risk criteria in `dev-designer/SKILL.md`, `dev-implementation/SKILL.md`, and `subagent-driven-development/SKILL.md`: invoke `task-reviewer` (with `-U5` `review-package`) when a task has `review_tier: "full"` in frontmatter, `labels` matching `{"security", "architecture", "concurrency", "contract"}`, or non-test `Allowed files` spanning more than 2 modules.
    91	  - Standard mechanical tasks rely on deterministic `run_task_checks.py` TDD verification (`RED`, `GREEN`, `TIER-B`, `TIER-C`) and end-of-epic `/cross-model-review`.
    92	- **Streamlined Autonomous Fix Loop & Dynamic Final Report**:
    93	  - In `lifecycle_runner.py` (`step_cross_model_review()`), when findings are verified `Valid` code fixes with no `shared-contracts/` impact and no `CRITICAL_CONFLICT`, allow Role 2.3 to apply direct fixes + scoped tests without extra `_draft_fix_plan` -> `evaluate_programmer_fix_plan` round-trips (retaining Role 2.2 plan evaluation only for contract/design ambiguity).
    94	  - Update `render_final_executive_report()` in `lifecycle_runner.py` to parse real highest-risk findings and SHAs from `review_results.md` / `principal_review.md` instead of returning hardcoded sample rows.
    95	
    96	### 4.5 Zero-Fluff Output Cap, Rules, and Skills Slimming
    97	
    98	- **Output Token Cap Directive**: Add a shared 5-rule Zero-Fluff output constraint across `rules/CRITICAL_RULES.md`, `dev-lifecycle/SKILL.md`, `dev-implementation/SKILL.md`, `quality_check/SKILL.md`, `finishing-a-development-branch/SKILL.md`, and all `lifecycle_runner.py` prompts: no greetings/preamble, no prompt restating, no echoing unchanged code, no narrative explaining passing checks; emit only `[STATE]` transitions, tool calls, and max 3 root-cause bullets on failures.
    99	- **Rules & Subagent Guard Slimming**:
   100	  - Condense `rules/CRITICAL_RULES.md` from `32,773` bytes to `<= 8,192` bytes (preventing IDE `<truncated>` slicing) by turning verbose explanations into normative `MUST`/`NEVER` rules and moving extended workflow checklists into `skills/dev-lifecycle/references/`. Preserve Rule 1–9 semantic contracts and satisfy `scripts/verify.sh` source-fidelity checks.
   101	  - Add `<SUBAGENT-STOP>` guard at the top of `skills/task-observer/SKILL.md` so subagents and headless review CLIs bypass loading `31.4 KB` of observer instructions.
   102	- **Scoped `resume_context.py`**: Add `--compact` (defaulting to epic-scoped output when `--epic <slug>` is passed) in `scripts/resume_context.py` so Role 2.2 / Role 2.3 receives active epic state, current repo git status, open relevant RFC headers, and matching epic tasks (~2–3 KB) instead of multi-repo dumps (`26.7 KB`).
   103	- **Skills Progressive Disclosure & Reference Deduplication**:
   104	  - Condense `skills/dev-designer/SKILL.md` (`66.4 KB` -> `<= 22 KB`) and `skills/quality_check/SKILL.md` by extracting verbose platform examples and boilerplate templates into linked `references/` files.
   105	  - Consolidate duplicate prompt/rule/triage files shared between `skills/dev-implementation/references/`, `skills/principal-review/references/`, and `skills/cross-model-review/references/` into canonical single sources while keeping all cross-links valid under `scripts/verify.sh`.
   106	
   107	### 4.6 Option A Bilingual Workflow
   108	
   109	- **Stage 1 & Stage 2 (Human Review)**: `dev-brainstorming` generates Spec `.en.md` + `.vi.md`; `dev-designer` generates HLD `<epic>.en.md` + `<epic>.vi.md` and **English-only** `bdd_scenarios.en.md` (deferring `bdd_scenarios.vi.md` until Stage 4).
   110	- **In-Flight Tolerance (`check_epic_readiness.py` & `check_bdd_traceability.py`)**: Keep Spec and HLD `.vi.md` on disk untouched for human reading; configure `check_epic_readiness.py` (in-flight default, with `--strict-bilingual` for Gate 5 / Finish) and `check_bdd_traceability.py` so Principal Review revisions to `.en.md` and deferred `bdd_scenarios.vi.md` do not block readiness (`R1`/`R3`/`R7`) mid-lifecycle, while removing `.vi.md` from `handoff.md` (`Read First`) and `run_external_review.py`.
   111	- **Stage 4 Pre-Finish Sync (`/finishing-a-development-branch`)**: Update Pre-Finish Hook (before archival commit in Options 1 and 2) to delta-sync `.en.md` edits into Spec/HLD `.vi.md`, generate `bdd_scenarios.vi.md` once, and validate the complete pair set with `check_document.py --require-toc --require-bilingual` and `check_epic_readiness.py --strict-bilingual`.

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/run_external_review.py | sed -n '457,505p'; nl -ba .devtool/epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md | sed -n '21,43p;134,147p'; nl -ba skills/dev-implementation/resources/scripts/compute_execution_order.py | sed -n '258,283p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
   457	    lines.append(f"{RED}{bar}{RESET}\n")
   458	    print("\n".join(lines), file=sys.stderr, flush=True)
   459	
   460	
   461	def status_lines(root: Path) -> list[str]:
   462	    return git_run(root, "status", "--porcelain").decode("utf-8", "replace").splitlines()
   463	
   464	
   465	def head_of(root: Path) -> str:
   466	    return git_run(root, "rev-parse", "HEAD").decode().strip()
   467	
   468	
   469	def execute(command: list[str] | str, root: Path, timeout: int, prompt: str | None = None,
   470	            shell: bool = False) -> tuple[int | None, str, str]:
   471	    """Run to completion in its own process group, so a timeout also ends the CLI's children."""
   472	    env = None
   473	    if isinstance(command, list) and command and Path(command[0]).name in ("kiro-cli", "kiro"):
   474	        home = os.environ.get("HOME", "")
   475	        if "/antigravity_homes/" in home:
   476	            real_home = Path(home).parents[1]
   477	            if (real_home / "Library" / "Application Support" / "kiro-cli").exists() or (real_home / ".kiro").exists():
   478	                env = dict(os.environ, HOME=str(real_home))
   479	    process = subprocess.Popen(command, cwd=root, shell=shell, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
   480	                               stderr=subprocess.PIPE, start_new_session=True, env=env)
   481	    try:
   482	        out, err = process.communicate((prompt or "").encode(), timeout=timeout)
   483	        code: int | None = process.returncode
   484	    except subprocess.TimeoutExpired:
   485	        os.killpg(process.pid, signal.SIGKILL)
   486	        out, err = process.communicate()
   487	        code = None
   488	    return code, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")
   489	
   490	
   491	def run_gate(label: str, command: list[str] | str, root: Path, timeout: int,
   492	             shell: bool = False) -> tuple[int, str, str]:
   493	    """Execute a pre-check gate with real-time terminal feedback."""
   494	    print(f"{CYAN}⏳ [Pre-check]{RESET} {label} ... ", end="", file=sys.stderr, flush=True)
   495	    code, out, err = execute(command, root, timeout, shell=shell)
   496	    combined = (out + err).rstrip()
   497	    if code is None:
   498	        print(f"{RED}❌ TIMEOUT ({timeout}s){RESET}", file=sys.stderr, flush=True)
   499	        raise PreconditionFailedError(label, f"timed out after {timeout} seconds", combined)
   500	    if code != 0:
   501	        print(f"{RED}❌ FAILED (exit {code}){RESET}", file=sys.stderr, flush=True)
   502	        raise PreconditionFailedError(label, f"failed with exit code {code}", combined)
   503	    print(f"{GREEN}✅ PASS{RESET}", file=sys.stderr, flush=True)
   504	    return code, out, err
   505	
    21	Upgrade `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` and `skills/dev-implementation/resources/scripts/manage_worker_pool.py` to enforce clean per-task session isolation (`Rule 4`), path-only Zero-Fluff worker prompts (`Rule 3`, `Rule 5`), config-driven Gemini 4 Hydrogen Role 2.3 resolution, Gate 4 25-line failure tailing (`Rule 2`), concurrent wave dispatch, and streamlined cross-model code-fix execution:
    22	1. **Config-Driven Role 2.3 Model & Effort Precedence (`RunnerConfig` + `main`)**:
    23	   - Replace hardcoded `"gemini-3.8-flash"` defaults with `"gemini-4-hydrogen-xhigh"` and `"xhigh"` fallback.
    24	   - Add `normalize_agy_effort(raw: str) -> str` mapping `"extra"`, `"extra-high"`, `"extra_high"`, and `"xhigh"` (case-insensitive) to `"xhigh"`.
    25	   - Implement `RunnerConfig.resolve_programmer_model(self, root: Path | None = None) -> str` and `RunnerConfig.resolve_programmer_effort(self, root: Path | None = None) -> str` following:
    26	     `CLI (--programmer-model / --programmer-effort) -> Runner --config JSON -> .devtool/review_config.json["providers"]["programmer"] -> env (AGY_PROGRAMMER_MODEL / AGY_PROGRAMMER_EFFORT) -> fallback ("gemini-4-hydrogen-xhigh", "xhigh")`.
    27	   - Update `main()` so `argparse` uses `default=None` for `--programmer-model` and add `--programmer-effort` (`default=None`), ensuring CLI overrides config only when explicitly passed.
    28	   - Update startup `probe_model()` and `_execute_single_task()` / `_apply_code_fixes()` to pass resolved model and normalized `--effort` to `ModelDispatcher.dispatch()`.
    29	2. **Parallel Worker Pool Execution & Path-Only Zero-Fluff Prompts**:
    30	   - Refactor `step_implementation()` to consume `compute_execution_order.py --parallel` waves and execute disjoint tasks concurrently inside 2-slot worktrees via `manage_worker_pool.py` (`init_slots`, `sync_slot`, `merge_slot`, `cleanup_slots`).
    31	   - Refactor `_execute_single_task()` so each task starts in a clean session context passing ONLY the task file path, target file paths + line ranges, and the Zero-Fluff output cap (no inlined task markdown or large source bodies).
    32	   - Ensure `run_gate4()` invokes `--compact` on polyglot/Gate 4 commands where available and uses `_tail_lines(output, 25)` on failures in both `run_gate4()` and `run_intermediate_check()`.
    33	3. **Streamlined Cross-Model Fix Loop & Real Executive Report**:
    34	   - Update `step_cross_model_review()`: when verified findings are pure code fixes with zero `shared-contracts/` or architecture ambiguity (via `_has_domain_or_critical_conflict`), route directly to `_apply_code_fixes()` without extra `_draft_fix_plan()` / `evaluate_programmer_fix_plan()` LLM round-trips; preserve Role 2.2 escalation whenever `shared-contracts/` or architecture ambiguity exists.
    35	   - Replace placeholder strings in `render_final_executive_report()` with parsed Top 3 Highest-Risk Findings and candidate SHAs read from `review_results.md` / `principal_review.md`.
    36	4. Update `tests/test_lifecycle_runner.py` (including RED/GREEN coverage for `TTO-HP-04`, `TTO-HP-07`, `TTO-EC-04`, `TTO-ST-04`, `TTO-AR-01`, `TTO-FR-03` alongside updated model expectations).
    37	
    38	## Files
    39	
    40	Allowed files:
    41	- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`
    42	- `skills/dev-implementation/resources/scripts/manage_worker_pool.py`
    43	- `tests/test_lifecycle_runner.py`
   134	## Decisions Already Made
   135	
   136	- `normalize_agy_effort(raw: str) -> str` maps `{"extra", "extra-high", "extra_high", "xhigh"}` -> `"xhigh"`, lowercasing and trimming input; default fallback pair is `("gemini-4-hydrogen-xhigh", "xhigh")`.
   137	- `RunnerConfig.resolve_programmer_model` and `resolve_programmer_effort` follow: `CLI -> Runner --config -> .devtool/review_config.json["providers"]["programmer"] -> env (AGY_PROGRAMMER_MODEL / AGY_PROGRAMMER_EFFORT) -> fallback`.
   138	- `main()` sets `default=None` on `--programmer-model` and `--programmer-effort` so `.devtool/review_config.json` controls defaults unless explicitly overridden at invocation.
   139	- `LifecycleRunner.step_implementation` dispatches independent parallel batches concurrently via `manage_worker_pool.py` slots with clean per-task prompts referencing file paths, line ranges, and Zero-Fluff output cap.
   140	- `LifecycleRunner._tail_lines(text: str, limit: int = 25) -> str` caps Gate 4 and intermediate failure summaries at `25` lines.
   141	- `step_cross_model_review` skips `_draft_fix_plan` / `evaluate_programmer_fix_plan` strictly when findings contain no `shared-contracts/` or architectural ambiguity, preserving `CRITICAL_CONFLICT` halts and Role 2.2 escalation otherwise.
   142	
   143	## Definition of Done
   144	
   145	- Scenarios TTO-HP-04, TTO-HP-07, TTO-EC-04, TTO-ST-04, TTO-AR-01, and TTO-FR-03 pass reliably. (V2, V3, V6)
   146	- Worker pool regression suite passes cleanly with zero concurrency or cleanup failures. (V3)
   147	- Python ruff lint and mypy strict type checks pass cleanly. (V4, V5)
   258	    if args.json:
   259	        payload = {
   260	            "epic": args.epic,
   261	            "tasks_count": len(tasks),
   262	            "pool_size": args.pool_size,
   263	            "layers": layers,
   264	            "parallel_batches": parallel_batches,
   265	            "tasks": {
   266	                tid: {
   267	                    "title": t["title"],
   268	                    "priority": t["priority"],
   269	                    "status": t["status"],
   270	                    "blockers": t["blockers"],
   271	                    "allowed_files": t.get("allowed_files", []),
   272	                    "soft_notes": t.get("soft_notes", []),
   273	                }
   274	                for tid, t in tasks.items()
   275	            },
   276	        }
   277	        print(json.dumps(payload, indent=2))
   278	        return 0
   279	
   280	    print(scan_summary)
   281	    if skipped:
   282	        for path in skipped:
   283	            print(f"  skipped: {path}")

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/run_external_review.py | sed -n '434,459p'; nl -ba skills/dev-implementation/resources/scripts/test_run_external_review.py | sed -n '1360,1407p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
   434	class PreconditionFailedError(Exception):
   435	    """Raised when fact collection fails, preventing AI CLI invocation."""
   436	
   437	    def __init__(self, gate: str, reason: str, details: str = "") -> None:
   438	        super().__init__(f"{gate}: {reason}")
   439	        self.gate = gate
   440	        self.reason = reason
   441	        self.details = details.strip()
   442	
   443	
   444	def print_gate_banner(error: PreconditionFailedError, cli: str) -> None:
   445	    """Print an unmistakable highlighted banner when a pre-check blocks AI invocation."""
   446	    bar = "=" * 74
   447	    lines = [
   448	        f"\n{RED}{bar}{RESET}",
   449	        f"{RED}🚨 [PRECONDITION BLOCKED] — {cli.upper()} CLI WAS NOT INVOKED (0 CREDITS USED){RESET}",
   450	        f"{RED}{bar}{RESET}",
   451	        f"{YELLOW}Failed Gate :{RESET} {error.gate}",
   452	        f"{YELLOW}Reason      :{RESET} {error.reason}",
   453	    ]
   454	    if error.details:
   455	        indented = "\n".join(f"  {line}" for line in error.details.splitlines()[-25:])
   456	        lines.append(f"{YELLOW}Details (last 25 lines):{RESET}\n{indented}")
   457	    lines.append(f"{RED}{bar}{RESET}\n")
   458	    print("\n".join(lines), file=sys.stderr, flush=True)
   459	
  1360	            "gemini5h": {"fraction": 1.0},
  1361	            "geminiWeekly": {"fraction": 0.0},
  1362	        }
  1363	        codex_exhausted_7d = {
  1364	            "status": "ACTIVE",
  1365	            "gemini5h": {"fraction": 1.0},
  1366	            "geminiWeekly": {"fraction": 0.0},
  1367	        }
  1368	        kiro_healthy = {
  1369	            "status": "ACTIVE (KIRO PRO+)",
  1370	            "creditsPool": {"fraction": 0.858, "limit": 1000.0, "remaining": 857.91},
  1371	        }
  1372	        agy_healthy = {
  1373	            "status": "ACTIVE",
  1374	            "argonWeekly": {"fraction": 0.56},
  1375	            "gemini5h": {"fraction": 1.0},
  1376	        }
  1377	        self.assertFalse(evaluate_provider_quota("claude", claude_exhausted_7d)[0])
  1378	        self.assertFalse(evaluate_provider_quota("codex", codex_exhausted_7d)[0])
  1379	        self.assertTrue(evaluate_provider_quota("kiro", kiro_healthy)[0])
  1380	
  1381	        chosen, evaluations = select_provider_by_quota(
  1382	            quota_fetcher=lambda p: {
  1383	                "claude": claude_exhausted_7d,
  1384	                "codex": codex_exhausted_7d,
  1385	                "kiro": kiro_healthy,
  1386	                "agy": agy_healthy,
  1387	            }[p],
  1388	            binary_resolver=lambda _p: "/usr/bin/fake",
  1389	        )
  1390	        self.assertEqual(chosen, "kiro")
  1391	        self.assertEqual(len(evaluations), 3)
  1392	
  1393	        # Case 2: Kiro below 3% (0.02, 10 credits) -> falls back to Argon (agy)
  1394	        kiro_low = {
  1395	            "status": "ACTIVE (KIRO PRO+)",
  1396	            "creditsPool": {"fraction": 0.02, "limit": 1000.0, "remaining": 10.0},
  1397	        }
  1398	        chosen2, _ = select_provider_by_quota(
  1399	            quota_fetcher=lambda p: {
  1400	                "claude": claude_exhausted_7d,
  1401	                "codex": codex_exhausted_7d,
  1402	                "kiro": kiro_low,
  1403	                "agy": agy_healthy,
  1404	            }[p],
  1405	            binary_resolver=lambda _p: "/usr/bin/fake",
  1406	        )
  1407	        self.assertEqual(chosen2, "agy")

exec
/bin/zsh -lc "env PYTHONDONTWRITEBYTECODE=1 python3 -B -c 'import sys,importlib.util,io,contextlib
from pathlib import Path
from unittest.mock import patch
p=Path.cwd()/'\\''skills/dev-implementation/resources/scripts'\\'';sys.path.insert(0,str(p))
import run_external_review as r
out=io.StringIO();payload='\\''\\n'\\''.join('\\''diagnostic-'\\''+str(i) for i in range(90))
with patch.object(r,'\\''execute'\\'',return_value=(1,'\\'''\\'',payload)),contextlib.redirect_stderr(out):
    try:r.run_gate('\\''probe'\\'',['\\''fake'\\''],Path.cwd(),1)
    except r.PreconditionFailedError as e:r.print_gate_banner(e,'\\''fake'\\'')
print('\\''failure-banner diagnostic lines =>'\\'',sum('\\''diagnostic-'\\'' in s for s in out.getvalue().splitlines()))
'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
failure-banner diagnostic lines => 25

codex
Lượt rà cuối xác nhận thêm rằng `_apply_code_fixes()` hiện trả `True` ngay cả khi process sửa lỗi thất bại; prompt mặc định của nó cũng không chứa findings hay đường dẫn review. Luồng sửa thẳng cần quy định rõ cả dữ liệu đầu vào và điều kiện thành công. Các probe lỗi đọc config, khởi chạy process và timeout đã chạy mà không gặp biến chưa gán; không có file hay git state nào được thay đổi.

codex
Reviewed all 12 artefacts against `8d456f6ec6f420e17932c67c8425a563ac3913ee`. Read-only probes covered exception paths, scenario parsing, review parsing, classification, and integration boundaries. No files or git state were changed.

Verdict: CHANGES REQUIRED
[Important] .devtool/epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md:Requirement Analysis §3 — The proposed fast-path guard does not establish architectural safety. `_has_domain_or_critical_conflict()` only checks a narrow keyword list ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:511)); probes returned False for “ambiguous architectural state transition” and “Debatable: two valid designs.” Removing Assistant evaluation therefore removes the remaining ambiguity check. Proposed: require an explicit, source-grounded classification of every finding as an unambiguous code fix; route unknown or debatable classifications through Role 2.2, and add negative-path tests.

[Important] .devtool/epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md:Requirement Analysis §3 / TTO-HP-07 — The direct fixer lacks an input and success contract. `_apply_code_fixes()` defaults to an empty plan, supplies no review-artifact path, ignores the dispatcher result, and returns True ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:1101)). A mocked failed dispatch confirmed that True result. Proposed: pass verified findings and design anchors explicitly, check dispatch and scoped-test results, and prohibit recording “fixed” decisions or advancing on failure.

[Important] .devtool/epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md:Parallel Worker Pool Execution — The runner/pool integration leaves repository-root and epic-worktree-root meanings unresolved. The runner dispatches from its supplied root ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:220)), whereas `merge_slot()` appends `.worktrees/<epic_dir>` ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/manage_worker_pool.py:124)). Passing the active epic worktree produces a nested path and returned False in the probe. Proposed: define both roots and both epic identifiers explicitly, use a dispatcher bound to each slot, serialize merges, and test execution from an actual epic worktree through successful merge and failure recovery.

[Important] .devtool/epic/token_throttling_optimization/task_01_diff_only_external_review_and_transcript_isolation.md:Requirement Analysis §2 — Filtering artefact lists does not exclude Vietnamese content from review prompts. Principal delta extraction selects the entire epic directory ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:997)); source-diff extraction also lacks a Vietnamese exclusion ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:657)). Thus changed companions can still enter prompts through diffs. Proposed: apply the English-only policy to every diff path, including principal deltas, fallback diffs, ad-hoc reviews, and local-review inputs; test changed Vietnamese files inside and outside the epic directory.

[Important] .devtool/epic/token_throttling_optimization/task_01_diff_only_external_review_and_transcript_isolation.md:Transcript Isolation — `<epic>_round<n>.raw.log` collides between Principal Review and Cross-Model Review. Their markdown files are separate ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:311)), and round numbering is derived independently from each file ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:1440)). Both first rounds therefore target the same log, invalidating the earlier pointer. Proposed: include review kind and candidate/run identity in the log path, and update the HLD, bilingual BDDs, and Task 6 isolation assertions accordingly.

[Important] .devtool/epic/token_throttling_optimization/task_03_option_a_bilingual_and_surgical_contract_guards.md:Option A Guards / TTO-ST-03 — “Full parity” and detection of an out-of-sync HLD are not defined sufficiently for the strict gate. The document checker compares heading levels ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/doc_quality_check/resources/scripts/check_document.py:200)); a probe accepted stale translated content with identical headings. The BDD loader compares scenario identifiers, without inspecting HLD content ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/check_bdd_traceability.py:82)). Proposed: define synchronization provenance for each translated document, validate it at Finish, and separate readiness assertions about Spec/HLD synchronization from traceability assertions about BDD identifiers; include a same-heading English-content-change test.

[Important] .devtool/epic/token_throttling_optimization/task_03_option_a_bilingual_and_surgical_contract_guards.md:Surgical File Reading Gate — The new guard would reject this epic’s existing task contracts. For example, Task 1 allows the 1,508-line `test_run_external_review.py` without a target anchor, and Task 4 does likewise for the 629-line `tests/test_lifecycle_runner.py`; these are existing Python source files covered by the stated rule. Several Task 2 and Task 3 paired tests have the same omission. Proposed: add file-specific symbol/window anchors to every affected task before implementation and verify the completed epic against the newly introduced guard.

[Important] .devtool/epic/token_throttling_optimization/task_05_slimming_rules_skills_dedup_and_selective_reviewer.md:Requirement Analysis §5 — The prescribed `check_bdd_traceability.py plan <epic> --strict-bilingual` invocation cannot run. The CLI requires `--scenarios` and `--tasks` ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/check_bdd_traceability.py:231)). An in-memory probe adding the proposed flag still exited 2 because those arguments were missing. Proposed: specify the complete invocation with the scenario path, resolved task paths, and agreed flag placement, then test that exact Pre-Finish command.

[Important] .devtool/epic/token_throttling_optimization/2026-11-13-token-throttling-optimization-design.en.md:§4.5 Output Token Cap Directive — Restricting output to state transitions, tool calls, and three failure bullets conflicts with mandatory machine-readable responses and exhaustive blocking findings. Review completion requires a parsed Verdict and findings ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:1420)). Proposed: apply the cap to discretionary narration while explicitly preserving required verdicts, complete findings tables, structured provider results, worker status contracts, and human gate decisions; mirror the clarification in Vietnamese and task requirements.

[Important] .devtool/epic/token_throttling_optimization/task_05_slimming_rules_skills_dedup_and_selective_reviewer.md:Files — Spec §4.3 explicitly requires updating `implementer-prompt.md`, but no task permits that edit. The interactive controller actively dispatches this template ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/subagent-driven-development/SKILL.md:298)). Completing the approved prompt change would therefore violate Allowed files and trigger Stop-and-Report. Proposed: add `skills/subagent-driven-development/implementer-prompt.md` to Task 5, with explicit bounded-read instructions and corresponding contract verification.

[Important] .devtool/epic/token_throttling_optimization/task_06_integration_and_regression_verification.md:Verification V1 — The proposed RED checks byte ceilings already required to pass in Tasks 3 and 5, which are prerequisites. A correctly completed dependency state therefore makes this assertion GREEN before Task 6’s registry change; the recorder rejects a passing pytest invocation as RED ([source](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_task_checks.py:140)). Proposed: target RED at Task 6’s missing release-suite registration, retain byte ceilings as regression checks, and ensure the initial failure comes from a collected assertion rather than a missing test target.
tokens used
252,019
````
