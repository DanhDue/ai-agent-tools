---
id: "task_02_reviewer_briefs_and_governance_exception"
status: "todo"
completedAt: null
priority: "high"
assignee: null
epic: "review_cap_and_risk_triage"
dueDate: null
created: "2026-11-18T06:25:00Z"
modified: "2026-11-18T06:45:00Z"
labels: ["prompts", "governance", "architecture", "contract"]
order: "a2"
review_tier: "full"
---

# Task 2: Blocker-Only Reviewer Briefs Pass 2 Delta Prompt and Role 2.2 Governance Exception

Epic: [review_cap_and_risk_triage](review_cap_and_risk_triage.md)

## Requirement Analysis

Update `Role 2.1 (task-reviewer)` prompt templates, downstream skill/handoff callers, and Four-Persona governance documentation to enforce Blocker-Only rejection (`BLOCKER` vs. `NON_BLOCKING_OBSERVATION`), Pass 1 Comprehensive vs. Pass 2 Delta-Only verification, and the bounded `Role 2.2` `triage-fix` / `finalize-slot` exceptions while respecting strict UTF-8 byte and word caps (Spec §6, §8.1; HLD Module Contracts §3, `[SE-01]`, `[SE-02]`):

1. **`scripts/resume_context.py` Reviewer Brief & Implement Prompt Emitter**:
   - Update `_BRIEF_ROLE_CONTRACTS["task-reviewer"]` to emit `'{"task_id": "...", "pass": 1, "verdict": "APPROVED|CHANGES_REQUESTED", "head_sha": "...", "done_gate": "PASS|FAIL", "blockers": [...], "observations": [...]}'` and state `BLOCKER` vs. `NON_BLOCKING_OBSERVATION` rules while keeping `"Role 2.1 AI Architect & Reviewer"`, read-only boundaries (`do NOT edit` / `forbid`), and omitting `"mark \`done\` and commit"` and `".vi.md"`.
   - Add CLI flags `--review-pass {1,2}` (default `1`), `--pass1-tree-sha <sha>`, and `--blockers-file <path>` in `build_parser()` and forward them to `emit_handoff_prompt(...)` when `mode == "brief"` and `brief_role == "task-reviewer"`.
   - For `--review-pass 1`: instruct `Role 2.1` to run a single comprehensive audit against BDD scenarios, HLD/API contracts, and `Allowed files`, reporting all `BLOCKER` items upfront (`category` in `BDD_VIOLATION`, `CONTRACT_SCHEMA_VIOLATION`, `RUNTIME_SAFETY`, `OWNERSHIP_ARCHITECTURE_VIOLATION`), and logging minor refinements under `Observations (Non-Blocking)` / `"observations"` with `"verdict": "APPROVED"`.
   - For `--review-pass 2`: instruct `Role 2.1` to run **Delta-Only Verification** over `git diff <pass1_tree_sha>` and Pass 1 blockers loaded from `--blockers-file` (when supplied), strictly forbidding new non-regression findings or state-transition nitpicks (`DIRECT_REGRESSION` only).
   - Update `mode == "implement"` (`L2410-L2420`) pool guidance to mention `triage-fix` and `finalize-slot` alongside `sync`/`merge`/`cleanup`, while keeping `mode == "principal-review"` byte-identical (`[SE-02]`).
2. **Governance, Lifecycle & Subagent Skill Alignment**:
   - `skills/dev-lifecycle/references/orchestration-roles.md`:
     - Section 1 (`Role 2.2 Orchestrator` row): permit running `manage_worker_pool.py triage-fix` (reading its bounded `<= 30` non-test line diff when `ELIGIBLE_FOR_SHORT_CIRCUIT`) and `manage_worker_pool.py finalize-slot` (whose internal read-only `run_task_checks.py status` and `check_bdd_traceability.py` status gates verify mechanical completion without running test suites), while keeping direct `src/`/`tests/` file reads and direct `run_task_checks.py` execution forbidden.
     - Section 3: update `task-reviewer` required keys (`task_id`, `pass`, `verdict` (`APPROVED`/`CHANGES_REQUESTED`), `head_sha`, `done_gate` (`PASS`/`FAIL`), `blockers`, `observations`).
     - Section 4: document `max_task_review_passes = 2`, `max_fix_passes = 1`, the Blocker-Only rubric, and the Two-Tier Risk Assessment Gate, stating explicitly that Tier 2 `RiskAssessment` is the single permitted Role 2.2 semantic ruling (strictly bounded to `ELIGIBLE_FOR_SHORT_CIRCUIT` `bounded_diff` against `pass1_blockers`, whereas `fix-planner` plans remain governed by halt criteria).
   - `skills/dev-lifecycle/references/governance-checklists.md`: Add concise checklist rules for `BLOCKER` vs. `NON_BLOCKING_OBSERVATION` and the Two-Tier Risk Assessment Gate.
   - `rules/CRITICAL_RULES.md` (`[SE-01]`): Keep total UTF-8 size `<= 8192` bytes and do NOT touch Rule 6 (`"APPROVED" not in rule_6`); in Rule 8.2 (`Role 2.2 Orchestrator`), note `(except triage-fix/finalize-slot)` while trimming redundant words in Rule 8 so every token required by existing contract tests remains intact.
   - `skills/dev-implementation/SKILL.md`: Update Phase 2 (`task-reviewer`, Fix Loop, Tier 1 `triage-fix` -> Tier 2 `RiskAssessment` -> `finalize-slot` / Pass 2 Delta-Only) while keeping word count `<= 4500` words and preserving all three `MANDATORY: read [references/...](references/...) before ...` pointers.
   - `skills/dev-lifecycle/SKILL.md` (kept `<= 2500` words) and `skills/dev-lifecycle/references/handoff-template.md`: include `triage-fix` and `finalize-slot` in Orchestrator `manage_worker_pool.py` command lists and note the 2-pass task review cap.
   - `skills/subagent-driven-development/SKILL.md`, `skills/subagent-driven-development/task-reviewer-prompt.md`, and `skills/subagent-driven-development/re-review-prompt.md`: cap the task fix/review loop at `max_task_review_passes = 2` / `max_fix_passes = 1`, align the reviewer output rubric with `BLOCKER` vs. `NON_BLOCKING_OBSERVATION` (`APPROVED` / `CHANGES_REQUESTED`) and Pass 2 Delta-Only scope while retaining `"Critical"`, `"run_task_checks.py status"`, `"Role 2.1 AI Architect & Reviewer"`, and `"check_bdd_traceability.py"` in `task-reviewer-prompt.md` (`scripts/test_verifiable_handoff_text.py`).
3. **Tests (`tests/test_trc_reviewer_briefs_and_governance.py`)**: Verify `TRC-HP-02` and `TRC-AR-01`.

## Files

Allowed files:
- `scripts/resume_context.py`
- `skills/dev-implementation/SKILL.md`
- `skills/dev-lifecycle/SKILL.md`
- `skills/dev-lifecycle/references/orchestration-roles.md`
- `skills/dev-lifecycle/references/governance-checklists.md`
- `skills/dev-lifecycle/references/handoff-template.md`
- `skills/subagent-driven-development/SKILL.md`
- `skills/subagent-driven-development/task-reviewer-prompt.md`
- `skills/subagent-driven-development/re-review-prompt.md`
- `rules/CRITICAL_RULES.md`
- `tests/test_trc_reviewer_briefs_and_governance.py` (new)

Read-only context:
- `.devtool/epic/review_cap_and_risk_triage/review_cap_and_risk_triage.md` — HLD Module Contracts §3, `[SE-01]`, `[SE-02]`
- `tests/test_fpg_governance_text.py` — existing Four-Persona governance assertions `(L104-L234, L481-L690)`
- `tests/test_fpg_checkpoint_and_briefs.py` — existing brief contract assertions `(L174-L263)`
- `tests/test_tto_docs_and_slimming.py` — byte/word cap assertions `(L31-L167)`
- `scripts/test_verifiable_handoff_text.py` — handoff and SDD prompt assertions `(L45-L125)`

## Design Rationale

Updating all downstream skill/prompt templates (`dev-implementation`, `dev-lifecycle`, `handoff-template`, and `subagent-driven-development`) in one atomic task eliminates stale uncapped review instructions across the kit while keeping every existing governance text test green. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/resume_context.py`: `_BRIEF_ROLE_CONTRACTS` `(L2238-L2274)`, `emit_handoff_prompt` (`mode == "implement"` and `mode == "brief"`) `(L2410-L2474)`, `build_parser` `(L2945-L2998)`, `main` `(L3094-L3107)`
  - `skills/dev-implementation/SKILL.md`: `<HARD-GATE>` & `#### 2-Slot Ephemeral Worker Pool & Layer Workflow` `(L145-L210)`
  - `skills/dev-lifecycle/SKILL.md`: `### Stage 3 — Isolated Execution` `(L105-L115)`
  - `skills/dev-lifecycle/references/orchestration-roles.md`: `## 1. Boundaries`, `## 3. Summary Contracts`, `## 4. Independent Verification` `(L15-L92)`
  - `skills/dev-lifecycle/references/governance-checklists.md`: `## 2.2` `(L48-L66)`
  - `skills/dev-lifecycle/references/handoff-template.md`: Orchestrator prompt & `## Rules for the Receiving Agent` `(L40-L80)`
  - `skills/subagent-driven-development/SKILL.md`: `### 3. Review the task` `(L332-L365)`
  - `skills/subagent-driven-development/task-reviewer-prompt.md`: `## Output Format` `(L180-L230)`
  - `skills/subagent-driven-development/re-review-prompt.md`: `## Scope` & `## Output Format` `(L55-L116)`
  - `rules/CRITICAL_RULES.md`: `## 8.` Role 2.2 bullet `(L59-L71)`
- **Downstream Callers**: All 11 text/brief contract test suites executed in Verification rows `V2..V6`, plus Task 4 (`lifecycle_runner.py`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% coverage of Pass 1 vs. Pass 2 `task-reviewer` brief branches, `--blockers-file` loading, Role 2.2 exception text, and byte/word caps.

### BDD SCENARIOS

Covers: TRC-HP-02, TRC-AR-01

```gherkin
Scenario: [TRC-HP-02] [Tier A - Unit] Task-reviewer brief emitter renders Pass 1 comprehensive rubric and Pass 2 delta-only rubric without Vietnamese mirror paths
Given an isolated git repository with epic "trc_epic" holding "trc_epic.md", "bdd_scenarios.md", and an ignored "trc_epic.vi.md"
And a blockers file "pass1_blockers.json" containing [{"id": "BLK-1", "category": "BDD_VIOLATION", "file": "src/app.py", "summary": "Missing null guard"}]
When "resume_context.py --emit-prompt brief --brief-role task-reviewer --epic trc_epic" runs for Pass 1
Then stdout exits 0, names "Role 2.1 AI Architect & Reviewer", includes '"verdict": "APPROVED|CHANGES_REQUESTED"', defines "BLOCKER" versus "NON_BLOCKING_OBSERVATION", and omits ".vi.md"
When "resume_context.py --emit-prompt brief --brief-role task-reviewer --epic trc_epic --review-pass 2 --pass1-tree-sha 4b825dc642cb --blockers-file pass1_blockers.json" runs
Then stdout exits 0, includes "git diff 4b825dc642cb", embeds "BLK-1", forbids introducing new non-regression findings in Pass 2, and omits ".vi.md"

Scenario: [TRC-AR-01] [Tier A - Unit] Governance rules and skills document bounded Role 2.2 triage-fix and finalize-slot exceptions within strict byte and word caps
Given the repository governance files "rules/CRITICAL_RULES.md", "skills/dev-lifecycle/references/orchestration-roles.md", "skills/dev-lifecycle/references/governance-checklists.md", "skills/dev-lifecycle/SKILL.md", "skills/dev-lifecycle/references/handoff-template.md", "skills/dev-implementation/SKILL.md", and "skills/subagent-driven-development/SKILL.md"
When governance text contract checks execute
Then UTF-8 byte length of "rules/CRITICAL_RULES.md" is <= 8192 and Rule 6 does not contain "APPROVED"
And word count of "skills/dev-lifecycle/SKILL.md" is <= 2500, word count of "skills/dev-implementation/SKILL.md" is <= 4500, and all three "MANDATORY: read [references/...]" pointers remain intact
And "orchestration-roles.md" and "dev-implementation/SKILL.md" document "triage-fix", "finalize-slot" (including its internal read-only mechanical status gates), "BLOCKER", "NON_BLOCKING_OBSERVATION", and the bounded "<= 30" non-test line Role 2.2 Tier 2 RiskAssessment exception while still forbidding direct reading/editing of "src/" and "tests/"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_trc_reviewer_briefs_and_governance.py::test_trc_hp_02_task_reviewer_pass1_and_pass2_briefs` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_trc_reviewer_briefs_and_governance.py tests/test_fpg_governance_text.py tests/test_fpg_checkpoint_and_briefs.py tests/test_tto_docs_and_slimming.py tests/test_rsdh_orchestration.py tests/test_runtime_sync_and_dashboard_hardening.py tests/test_fpg_english_only_text.py tests/test_workflow_anti_rationalization.py tests/test_token_throttling_acceptance.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m unittest scripts/test_resume_context.py scripts/test_verifiable_handoff_text.py` | exit 0 | — |
| V4 | GREEN | `python3 scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V5 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_trc_reviewer_briefs_and_governance.py` | exit 0 | — |
| V6 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_trc_reviewer_briefs_and_governance.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V7 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/trc_task_02.xml tests/test_trc_reviewer_briefs_and_governance.py tests/test_fpg_governance_text.py tests/test_fpg_checkpoint_and_briefs.py tests/test_tto_docs_and_slimming.py tests/test_rsdh_orchestration.py tests/test_runtime_sync_and_dashboard_hardening.py tests/test_fpg_english_only_text.py tests/test_workflow_anti_rationalization.py` | exit 0; results build/test-results/trc_task_02.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Source (`[SE-01]`): `rules/CRITICAL_RULES.md` is capped at `8192` UTF-8 bytes (`tests/test_tto_docs_and_slimming.py:35`), and Rule 6 must never contain `"APPROVED"` (`tests/test_fpg_governance_text.py:164`). Keep Rule 6 unchanged; update Rule 8.2 (`Role 2.2 Orchestrator`) to allow `triage-fix`/`finalize-slot` while tightening ~35 bytes in Rule 8 without removing any required token (`ai_architect_reviewer`, `orchestrator`, `programmer`, `dev-config`, `--checkpoint`, `gate2_tasks_locked`, `subagent_returned`, `wave_merged`, `model_unavailable`, `turn_budget`, `low_quota_stop`, `quota_low`, `low-quota`, `quota-check`, `session map`).
- Source (`[SE-02]`): `emit_handoff_prompt("principal-review", ...)` must remain byte-for-byte identical to `docs/context-memory-quick-guide.en.md` Scenario 1 Step 2 (`tests/test_fpg_governance_text.py:690`). Only `mode == "brief"` (`brief_role == "task-reviewer"`) and `mode == "implement"` change.
- Source: `skills/dev-lifecycle/SKILL.md` must stay `<= 2500` words and `skills/dev-implementation/SKILL.md` must stay `<= 4500` words while preserving all three `MANDATORY: read [references/...](references/...) before ...` pointers and all tokens checked by `test_verifiable_handoff_text.py`, `test_tto_docs_and_slimming.py`, `test_fpg_governance_text.py`, `test_rsdh_orchestration.py`, and `test_workflow_anti_rationalization.py`.
- Source: `skills/subagent-driven-development/SKILL.md` must keep `"-U5"`, `"Zero-Fluff"`, `"StartLine"`/`"EndLine"`, `"review_tier"`, `"security"`, `"architecture"`, `"concurrency"`, `"contract"`, `"> 2"`, and `"skip"`, and `task-reviewer-prompt.md` must keep `"run_task_checks.py status"`, `"Critical"`, `"Role 2.1 AI Architect & Reviewer"`, and `"check_bdd_traceability.py"` (`scripts/test_verifiable_handoff_text.py:81-84`).
- New contract: `emit_handoff_prompt` accepts keyword-only defaults `review_pass: int = 1`, `pass1_tree_sha: str | None = None`, and `blockers_file: Path | str | None = None`. When `review_pass == 2`, the `task-reviewer` JSON schema shows `"pass": 2` and appends a `PASS 2 DELTA-ONLY VERIFICATION RULES` block naming `git diff <pass1_tree_sha>`, inlining parsed JSON from `blockers_file` when provided, and forbidding any new non-regression findings.

## Definition of Done

- `TRC-HP-02` and `TRC-AR-01` pass alongside all 10 existing governance, brief, handoff, and document contract test suites. (V2, V3, V4, V7)
- `rules/CRITICAL_RULES.md` stays `<= 8192` UTF-8 bytes, `dev-lifecycle/SKILL.md` stays `<= 2500` words, and `dev-implementation/SKILL.md` stays `<= 4500` words with all relative links valid. (V2, V7)
- `ruff check` and `mypy` pass on `tests/test_trc_reviewer_briefs_and_governance.py`. (V5, V6)
- Prompt rubrics and governance matrix clearly distinguish `BLOCKER` from `NON_BLOCKING_OBSERVATION` and bound the Role 2.2 `triage-fix` and `finalize-slot` exceptions. (Gate 5)

## Dependencies & Blockers

None.

Downstream dependents (blocked by Task 2): [Task 4](task_04_runner_parity_and_acceptance.md).

## References & Rollback

- [Epic HLD](review_cap_and_risk_triage.md)
- **Rollback**: Revert `scripts/resume_context.py`, `skills/dev-implementation/SKILL.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-lifecycle/references/orchestration-roles.md`, `skills/dev-lifecycle/references/governance-checklists.md`, `skills/dev-lifecycle/references/handoff-template.md`, `skills/subagent-driven-development/SKILL.md`, `skills/subagent-driven-development/task-reviewer-prompt.md`, `skills/subagent-driven-development/re-review-prompt.md`, and `rules/CRITICAL_RULES.md`, and delete `tests/test_trc_reviewer_briefs_and_governance.py`.
