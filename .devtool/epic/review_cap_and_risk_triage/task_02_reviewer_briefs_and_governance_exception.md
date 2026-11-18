---
id: "task_02_reviewer_briefs_and_governance_exception"
status: "todo"
completedAt: null
priority: "high"
assignee: null
epic: "review_cap_and_risk_triage"
dueDate: null
created: "2026-11-18T06:25:00Z"
modified: "2026-11-18T06:25:00Z"
labels: ["prompts", "governance", "architecture", "contract"]
order: "a2"
review_tier: "full"
---

# Task 2: Blocker-Only Reviewer Briefs Pass 2 Delta Prompt and Role 2.2 Governance Exception

Epic: [review_cap_and_risk_triage](review_cap_and_risk_triage.md)

## Requirement Analysis

Update `Role 2.1 (task-reviewer)` prompt templates and Four-Persona governance documentation to enforce Blocker-Only rejection (`BLOCKER` vs. `NON_BLOCKING_OBSERVATION`), Pass 1 Comprehensive vs. Pass 2 Delta-Only verification, and the bounded `Role 2.2` `triage-fix` exception while respecting strict UTF-8 byte and word caps (Spec §6, §8.1; HLD Module Contracts §3, `[SE-01]`, `[SE-02]`):

1. **`scripts/resume_context.py` Reviewer Brief Emitter**:
   - Update `_BRIEF_ROLE_CONTRACTS["task-reviewer"]` to emit the structured JSON schema `'{"task_id": "...", "pass": 1, "verdict": "APPROVED|CHANGES_REQUESTED", "head_sha": "...", "done_gate": "PASS|FAIL", "blockers": [...], "observations": [...]}'` and explicitly state `BLOCKER` vs. `NON_BLOCKING_OBSERVATION` rules while keeping `"Role 2.1 AI Architect & Reviewer"`, read-only boundaries (`do NOT edit` / `forbid`), and omitting `"mark \`done\` and commit"` and `".vi.md"`.
   - Add CLI flags `--review-pass {1,2}` (default `1`), `--pass1-tree-sha <sha>`, and `--blockers-file <path>` in `build_parser()` and forward them to `emit_handoff_prompt(...)` **only** when `mode == "brief"` and `brief_role == "task-reviewer"` (`[SE-02]`: all other `--emit-prompt` modes, especially `principal-review`, stay byte-identical).
   - For `--review-pass 1`: instruct `Role 2.1` to run a single comprehensive audit against BDD scenarios, HLD/API contracts, and `Allowed files`, reporting all `BLOCKER` items upfront (`category` in `BDD_VIOLATION`, `CONTRACT_SCHEMA_VIOLATION`, `RUNTIME_SAFETY`, `OWNERSHIP_ARCHITECTURE_VIOLATION`), and logging minor refinements under `Observations (Non-Blocking)` / `"observations"` with `"verdict": "APPROVED"`.
   - For `--review-pass 2`: instruct `Role 2.1` to run **Delta-Only Verification** over `git diff <pass1_tree_sha>` (when `--pass1-tree-sha` is supplied) and the Pass 1 blockers loaded from `--blockers-file` (if supplied), strictly forbidding new non-regression findings or state-transition nitpicks (`DIRECT_REGRESSION` only).
2. **Governance & Skill Documentation**:
   - `skills/dev-lifecycle/references/orchestration-roles.md`: Update Section 1 (`Role 2.2 Orchestrator` row) to permit reading the bounded JSON output of `manage_worker_pool.py triage-fix` (`<= 30` non-test changed lines when `ELIGIBLE_FOR_SHORT_CIRCUIT`) while keeping direct `src/`/`tests/` file reads forbidden; update Section 3 (`task-reviewer` summary contract keys: `task_id`, `pass`, `verdict` (`APPROVED`/`CHANGES_REQUESTED`), `head_sha`, `done_gate` (`PASS`/`FAIL`), `blockers`, `observations`) and Section 4 (hard cap `max_task_review_passes = 2`, `max_fix_passes = 1`, Blocker-Only rubric, and Two-Tier Risk Assessment Gate).
   - `skills/dev-lifecycle/references/governance-checklists.md`: Add concise checklist rules for `BLOCKER` vs. `NON_BLOCKING_OBSERVATION` and the Two-Tier Risk Assessment Gate (`Tier 1 triage-fix` + `Tier 2 Role 2.2 RiskAssessment`).
   - `rules/CRITICAL_RULES.md` (`[SE-01]`): Keep total UTF-8 size `<= 8192` bytes and do NOT touch Rule 6 (`"APPROVED" not in rule_6`); in Rule 8.2 (`Role 2.2 Orchestrator`), note `(except triage-fix bounded output)` while trimming redundant words in Rule 8 so every token required by `tests/test_fpg_governance_text.py` and `tests/test_tto_docs_and_slimming.py` stays intact.
   - `skills/dev-implementation/SKILL.md`: Update Phase 2 (`task-reviewer`, Fix Loop, Tier 1 `triage-fix` -> Tier 2 `RiskAssessment` -> `finalize-slot` / Pass 2 Delta-Only) while keeping word count `<= 4500` words and preserving all three `MANDATORY: read [references/...](references/...) before ...` pointers.
3. **Tests (`tests/test_trc_reviewer_briefs_and_governance.py`)**: Verify `TRC-HP-02` and `TRC-AR-01`.

## Files

Allowed files:
- `scripts/resume_context.py`
- `skills/dev-implementation/SKILL.md`
- `skills/dev-lifecycle/references/orchestration-roles.md`
- `skills/dev-lifecycle/references/governance-checklists.md`
- `rules/CRITICAL_RULES.md`
- `tests/test_trc_reviewer_briefs_and_governance.py` (new)

Read-only context:
- `.devtool/epic/review_cap_and_risk_triage/review_cap_and_risk_triage.md` — HLD Module Contracts §3, `[SE-01]`, `[SE-02]`
- `tests/test_fpg_governance_text.py` — existing Four-Persona governance assertions `(L104-L234, L481-L690)`
- `tests/test_fpg_checkpoint_and_briefs.py` — existing brief contract assertions `(L174-L263)`
- `tests/test_tto_docs_and_slimming.py` — byte/word cap assertions `(L31-L167)`

## Design Rationale

Aligning the emitted `task-reviewer` prompt, `dev-implementation` workflow steps, and `orchestration-roles.md` in one atomic task prevents contradiction between subagent instructions and Orchestrator rules while keeping existing governance contract tests green. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/resume_context.py`: `_BRIEF_ROLE_CONTRACTS` `(L2238-L2274)`, `emit_handoff_prompt` (`mode == "brief"` branch) `(L2448-L2474)`, `build_parser` `(L2945-L2998)`, `main` `(L3094-L3107)`
  - `skills/dev-implementation/SKILL.md`: `<HARD-GATE>` & `#### 2-Slot Ephemeral Worker Pool & Layer Workflow` `(L145-L210)`
  - `skills/dev-lifecycle/references/orchestration-roles.md`: `## 1. Boundaries`, `## 3. Summary Contracts`, `## 4. Independent Verification` `(L15-L92)`
  - `skills/dev-lifecycle/references/governance-checklists.md`: `## 2.2` / new task-review triage subsection `(L48-L66)`
  - `rules/CRITICAL_RULES.md`: `## 8.` Role 2.2 bullet `(L59-L71)`
- **Downstream Callers**: `tests/test_fpg_governance_text.py`, `tests/test_fpg_checkpoint_and_briefs.py`, `tests/test_tto_docs_and_slimming.py`, `scripts/test_resume_context.py`, Task 4 (`lifecycle_runner.py`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% coverage of Pass 1 vs. Pass 2 `task-reviewer` brief branches, `--blockers-file` loading, and governance byte/word cap invariants.

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

Scenario: [TRC-AR-01] [Tier A - Unit] Governance rules and skills document bounded Role 2.2 triage-fix exception within strict byte and word caps
Given the repository governance files "rules/CRITICAL_RULES.md", "skills/dev-lifecycle/references/orchestration-roles.md", "skills/dev-lifecycle/references/governance-checklists.md", and "skills/dev-implementation/SKILL.md"
When governance text contract checks execute
Then UTF-8 byte length of "rules/CRITICAL_RULES.md" is <= 8192 and Rule 6 does not contain "APPROVED"
And word count of "skills/dev-implementation/SKILL.md" is <= 4500 and all three "MANDATORY: read [references/...]" pointers remain intact
And "orchestration-roles.md" and "dev-implementation/SKILL.md" document "triage-fix", "finalize-slot", "BLOCKER", "NON_BLOCKING_OBSERVATION", and the bounded "<= 30" non-test line Role 2.2 exception while still forbidding direct reading/editing of "src/" and "tests/"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_trc_reviewer_briefs_and_governance.py::test_trc_hp_02_task_reviewer_pass1_and_pass2_briefs` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_trc_reviewer_briefs_and_governance.py tests/test_fpg_governance_text.py tests/test_fpg_checkpoint_and_briefs.py tests/test_tto_docs_and_slimming.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m unittest scripts/test_resume_context.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_trc_reviewer_briefs_and_governance.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_trc_reviewer_briefs_and_governance.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/trc_task_02.xml tests/test_trc_reviewer_briefs_and_governance.py tests/test_fpg_governance_text.py tests/test_fpg_checkpoint_and_briefs.py tests/test_tto_docs_and_slimming.py` | exit 0; results build/test-results/trc_task_02.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Source (`[SE-01]`): `rules/CRITICAL_RULES.md` is capped at `8192` UTF-8 bytes (`tests/test_tto_docs_and_slimming.py:35`), and Rule 6 must never contain `"APPROVED"` (`tests/test_fpg_governance_text.py:164`). Keep Rule 6 unchanged; update Rule 8.2 (`Role 2.2 Orchestrator`) to allow `triage-fix` bounded output while tightening ~30 bytes in Rule 8 without removing any required token (`ai_architect_reviewer`, `orchestrator`, `programmer`, `dev-config`, `--checkpoint`, `gate2_tasks_locked`, `subagent_returned`, `wave_merged`, `model_unavailable`, `turn_budget`, `low_quota_stop`, `quota_low`, `low-quota`, `quota-check`, `session map`).
- Source (`[SE-02]`): `emit_handoff_prompt("principal-review", ...)` must remain byte-for-byte identical to `docs/context-memory-quick-guide.en.md` Scenario 1 Step 2 (`tests/test_fpg_governance_text.py:690`). Only the `mode == "brief"` and `brief_role == "task-reviewer"` code path changes.
- Source: `skills/dev-implementation/SKILL.md` must keep all three `MANDATORY: read [references/...](references/...) before ...` pointers in their exact sections (`tests/test_fpg_governance_text.py:481-540`), keep `review_tier`, `security`, `architecture`, `concurrency`, `contract`, `> 2`, `skip`, `Zero-Fluff`, `StartLine`/`EndLine`, `dev_config.py dispatch`, `--persona programmer`, `--mode write --prompt-file`, `record a quota pending decision with the printed report and stop`, and `agy_profile_leases.json`, and stay `<= 4500` words.
- New contract: `emit_handoff_prompt` accepts keyword-only defaults `review_pass: int = 1`, `pass1_tree_sha: str | None = None`, and `blockers_file: Path | str | None = None`. When `review_pass == 2`, the `task-reviewer` JSON schema shows `"pass": 2` and appends a `PASS 2 DELTA-ONLY VERIFICATION RULES` block naming `git diff <pass1_tree_sha>`, inlining parsed JSON from `blockers_file` when provided, and forbidding any new non-regression findings.

## Definition of Done

- `TRC-HP-02` and `TRC-AR-01` pass alongside `test_fpg_governance_text.py`, `test_fpg_checkpoint_and_briefs.py`, `test_tto_docs_and_slimming.py`, and `scripts/test_resume_context.py`. (V2, V3, V6)
- `rules/CRITICAL_RULES.md` stays `<= 8192` UTF-8 bytes and `skills/dev-implementation/SKILL.md` stays `<= 4500` words with all relative links valid. (V2, V6)
- `ruff check` and `mypy` pass on `tests/test_trc_reviewer_briefs_and_governance.py`. (V4, V5)
- Prompt rubrics and governance matrix clearly distinguish `BLOCKER` from `NON_BLOCKING_OBSERVATION` and bound the Role 2.2 exception. (Gate 5)

## Dependencies & Blockers

None.

Downstream dependents (blocked by Task 2): [Task 4](task_04_runner_parity_and_acceptance.md).

## References & Rollback

- [Epic HLD](review_cap_and_risk_triage.md)
- **Rollback**: Revert `scripts/resume_context.py`, `skills/dev-implementation/SKILL.md`, `skills/dev-lifecycle/references/orchestration-roles.md`, `skills/dev-lifecycle/references/governance-checklists.md`, and `rules/CRITICAL_RULES.md`, and delete `tests/test_trc_reviewer_briefs_and_governance.py`.
