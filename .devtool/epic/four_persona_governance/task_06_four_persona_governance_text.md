---
id: "task_06_four_persona_governance_text"
status: "todo"
priority: "high"
assignee: null
epic: "four_persona_governance"
dueDate: null
created: "2026-11-17T10:00:00Z"
modified: "2026-11-17T10:00:00Z"
labels: ["governance", "architecture", "docs"]
order: "a6"
review_tier: "full"
---

# Task 6: Four-Persona Governance and Checkpoint Rules in Rules and Skills

Epic: [four_persona_governance](four_persona_governance.en.md)

## Requirement Analysis

Rewrite the governance text so agents follow the four-persona model, checkpoints and the dev-config skill
(spec §3, §4, §5.5, §8).

1. **`rules/CRITICAL_RULES.md`**: §5 and §6 use Role 2.1 for fix plans and the halt criteria; §8 becomes the
   four-persona rule with the persona table, the session map and the dev-config pointer; add the mandatory
   checkpoint events, the turn budget, low-quota mode and the quota gate to §8; Rule §10 keeps its scope; §9 gains one rule: `ag_run` and any `<profile>-cli` alias are launched through `zsh -ic`
   and never from an agent runtime's own shell.
2. **`skills/dev-lifecycle/`**: `SKILL.md` (Sequence, HARD-GATE, Autonomous Mode, Handoff Choice, Stage 3,
   Red Flags) and references `orchestration-roles.md` (boundaries matrix, old-to-new mapping table, brief roles
   including `fix-planner`, dispatch via `dev_config.py dispatch` (agy profile pool, lease file
   `agy_profile_leases.json`) and `dev_config.py resolve`, unavailable-model stop, pool-exhausted stop),
   `autonomous-mode.md`, `governance-checklists.md`, `handoff-template.md`, `principal-review.md`.
3. **Stage skills**: `dev-implementation/SKILL.md` (Overview, Phase 2 pool workflow, Phase 4, cross-model
   transition), `subagent-driven-development/SKILL.md` (Model Selection, review step, fix loop),
   `subagent-driven-development/task-reviewer-prompt.md`, `cross-model-review/SKILL.md`,
   `principal-review/SKILL.md`, `principal-review/references/document-triage.md`, `resume-context/SKILL.md`,
   `save-context/SKILL.md` (document `--checkpoint`).
4. **Emitted strings**: `run_external_review.py` triage text that names "Role 2.2" for design revisions names
   "Role 2.1 AI Architect & Reviewer".
5. **Tests**: new `tests/test_fpg_governance_text.py` (FPG-AR-03); update contract tests that pin Tri-Role
   wording.

## Files

Allowed files:
- `rules/CRITICAL_RULES.md`
- `skills/dev-lifecycle/SKILL.md`
- `skills/dev-lifecycle/references/orchestration-roles.md`
- `skills/dev-lifecycle/references/autonomous-mode.md`
- `skills/dev-lifecycle/references/governance-checklists.md`
- `skills/dev-lifecycle/references/handoff-template.md`
- `skills/dev-lifecycle/references/principal-review.md`
- `skills/dev-implementation/SKILL.md`
- `skills/subagent-driven-development/SKILL.md`
- `skills/subagent-driven-development/task-reviewer-prompt.md`
- `skills/cross-model-review/SKILL.md`
- `skills/principal-review/SKILL.md`
- `skills/principal-review/references/document-triage.md`
- `skills/resume-context/SKILL.md`
- `skills/save-context/SKILL.md`
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`
- `scripts/test_lifecycle_document_contract.py`
- `scripts/test_verifiable_handoff_text.py`
- `tests/test_tto_docs_and_slimming.py`
- `tests/test_assistant_orchestrator_handoff.py`
- `tests/test_fpg_governance_text.py` (new)

Read-only context:
- `.devtool/epic/four_persona_governance/2026-11-17-four-persona-governance-design.en.md` — spec §3, §4, §8
- `skills/dev-config/SKILL.md` (new) — command names to reference
- `scripts/resume_context.py` — final `--role`, `--checkpoint`, `--brief-role` choices from Task 2

## Design Rationale

Text is what interactive agents execute; a rule left on the old numbering makes the kit contradict
itself, so every reference moves in one task with a test that forbids the old vocabulary. Applicable
skills: `d3nexus:writing-skills`, `d3nexus:doc_quality_check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/SKILL.md`: `## Overview` (L8-L15), `### Phase 2 — Parallel Task Execution (Orchestrator + Programmer Subagents)` (L176-L278), `### Phase 4 — End of Epic Verification (Fresh `gate4-verifier` Subagent)` (L293-L338), `### Automated Transition to Cross-Model Review (Zero Intermediate Confirmation)` (L339-L363)
  - `skills/subagent-driven-development/SKILL.md`: `## Model Selection` (L187-L223), `### 3. Review the task` (L330-L382), `### 4. The fix loop` (L383-L464)
  - `skills/subagent-driven-development/task-reviewer-prompt.md`: `# Task Reviewer Prompt Template` (L1-L20), `[MODEL]` placeholder (L200-L210)
  - `skills/dev-implementation/resources/scripts/run_external_review.py`: triage halt and revision text (L2470-L2495)
  - `skills/dev-implementation/resources/scripts/test_run_external_review.py`: `test_auto_triage_gate_classifications` (L1199-L1356)
  - `scripts/test_lifecycle_document_contract.py`: `test_prv_hp_04_packaging_readiness_and_principal_review_choice` (L330-L358)
  - `tests/test_tto_docs_and_slimming.py`: `test_tto_hp_05_slimmed_rules_and_skills_caps` (L31-L86), `test_tto_hp_05_lifecycle_word_caps` (L89-L143), `test_tto_ec_05_selective_task_reviewer_and_prompt_rules` (L146-L221)
  - `scripts/test_verifiable_handoff_text.py`: `test_vth_hp_09_sdd_prompts_treat_evidence_as_proof` (L74-L83)
- **Downstream Callers**: every runtime that loads these skills; `scripts/verify.sh` link and ToC checks.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: zero old-vocabulary hits in `rules/` and `skills/`.

### BDD SCENARIOS

Covers: FPG-AR-03, FPG-AR-07


```gherkin
Scenario: [FPG-AR-03] [Tier A - Unit] Governance text uses the four-persona model everywhere
Given the tracked files under "rules/" and "skills/" excluding historical ".devtool" content
When the governance contract test scans them, excluding only the "Old-to-New Role Mapping" table in "skills/dev-lifecycle/references/orchestration-roles.md"
Then no scanned line contains "Tri-Role" or "Role 2.1 Human Architect" or "Role 2.3 AI Programmer"
And "rules/CRITICAL_RULES.md" contains "Role 1.0 Human Architect", "Role 2.1 AI Architect & Reviewer", "Role 2.2 Orchestrator" and "Role 2.3 Programmer"
And "skills/dev-lifecycle/references/orchestration-roles.md" contains a table under the heading "Old-to-New Role Mapping" and the brief role "fix-planner"

Scenario: [FPG-AR-07] [Tier A - Unit] Governance text routes agy dispatch through the pool and keeps ag_run out of agent shells
Given the kit rules and skills after Task 06
When the contract test reads "orchestration-roles.md", "dev-implementation/SKILL.md" and "CRITICAL_RULES.md"
Then the Programmer dispatch instructions name "dev_config.py dispatch" and the lease file "agy_profile_leases.json"
And they state that an exit code of 2 means "record a quota pending decision with the printed report and stop"
And "CRITICAL_RULES.md" Rule 9 states that "ag_run" and any "<profile>-cli" alias are launched through "zsh -ic" and never from an agent runtime's own shell
And no dev-lifecycle skill tells an agent to launch agy with a hand-built HOME or AGY_PROFILE
```

```gherkin
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_governance_text.py::test_fpg_ar_03_governance_text_uses_four_personas` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_governance_text.py tests/test_tto_docs_and_slimming.py tests/test_assistant_orchestrator_handoff.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 scripts/test_lifecycle_document_contract.py scripts/test_verifiable_handoff_text.py skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0 | — |
| V4 | GREEN | `python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc skills/dev-lifecycle/references/orchestration-roles.md skills/dev-lifecycle/references/handoff-template.md` | exit 0 | — |
| V5 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/run_external_review.py` | exit 0 | — |
| V6 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/run_external_review.py --ignore-missing-imports` | exit 0 | — |
| V7 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/fpg_task_06.xml tests/test_fpg_governance_text.py` | exit 0; results build/test-results/fpg_task_06.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- New contract: canonical labels `Role 1.0 Human Architect`, `Role 2.1 AI Architect & Reviewer`,
  `Role 2.2 Orchestrator`, `Role 2.3 Programmer`; config keys `ai_architect_reviewer`, `orchestrator`,
  `programmer`.
- New contract: the old-to-new mapping table appears once, in `orchestration-roles.md`, under the heading
  `## Old-to-New Role Mapping`; it is the only place old labels may appear, and the FPG-AR-03 test skips
  exactly the lines of that section. Other files use only the new labels.
- Source: `CRITICAL_RULES.md` keeps its frontmatter (`scripts/verify.sh` `sec_5b` fails without it) and Rule
  §10 wording; Rule numbering §1–§10 is preserved so cross-references stay valid. Task 7 adds §11.
- Source: the selective review gating condition (spec §3.4) is unchanged; only the persona that reviews moves.
- New contract: dispatch instructions read `python3 scripts/dev_config.py resolve
  <persona> --format argv --mode <read-only|write>` instead of naming `review_config.json` providers.
- New contract: the unavailable-model rule says "no automatic fallback, no retry: checkpoint, record a blocker
  with the fallback command, stop".
- New contract: the Programmer dispatch instructions read `python3 scripts/dev_config.py dispatch --persona programmer
  --mode write --prompt-file <file> --cwd <slot> --log <log> --epic <slug> --task <id> --slot <n>`. They state that
  the lease file `agy_profile_leases.json` records which profile is in use, that an exit code of `2` means "record a
  quota pending decision with the printed report and stop", and that the Orchestrator never launches `agy` with a
  hand-built `HOME` or `AGY_PROFILE`.
- New contract: Rule 9 of `CRITICAL_RULES.md` gains the sentence "`ag_run` and any `<profile>-cli` alias must be
  launched through `zsh -ic` and never from an agent runtime's own shell, because `ag_run` deletes a profile's
  symlinks when its underscore helper functions are missing".
- Skill frontmatter stays exactly `name` + `description`.

## Definition of Done

- FPG-AR-03 passes. (V2, V7)
- Updated contract and review suites pass. (V2, V3)
- Edited references keep a complete linked ToC where they have one. (V4)
- Ruff and mypy pass on `run_external_review.py`. (V5, V6)
- The rules read coherently end to end for the Human Architect. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 3](task_03_runner_personas_risk_routing_and_quota_stops.md) and [Task 5](task_05_check_tasks_dashboard_persona_and_quota_sync.md).

Downstream dependents (blocked by Task 6): `task_07`.

## References & Rollback

- [Epic HLD](four_persona_governance.en.md)
- **Rollback**: Revert the task commit to restore the Tri-Role text.
