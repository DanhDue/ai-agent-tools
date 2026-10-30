---
id: "task_04_lifecycle_integration_and_verification"
status: "todo"
priority: "high"
assignee: null
epic: "context_memory_management"
dueDate: null
created: "2026-10-30T16:05:00Z"
modified: "2026-10-30T16:05:00Z"
completedAt: null
labels: ["lifecycle", "integration", "finish", "harness"]
order: "a4"
---

# Task 4: Dev-Lifecycle Context Hooks Integration and Release Verification Harness

Epic: [context_memory_management](../epic/context_memory_management/context_memory_management.en.md)

## Requirement Analysis

Integrate Two-Tier Project Memory (`save-context` / `resume_context.py`) and Tri-Role Persona handoff prompts across the `/dev-lifecycle` skills (`dev-brainstorming`, `dev-designer`, `dev-lifecycle`, `handoff-template.md`, `principal-review.md`, `principal-review`, `dev-implementation`, `cross-model-review`, `finishing-a-development-branch`) and register `scripts/test_resume_context.py` in `scripts/verify.sh` (`[CMM-HP-03]`):
1. **`skills/dev-brainstorming/SKILL.md` (Stage 1 — AI Assistant)**:
   - After Gate 1 spec approval, instruct the agent to persist architectural decisions via `resume_context.py --state --epic <topic_slug> --role assistant`.
2. **`skills/dev-designer/SKILL.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-lifecycle/references/handoff-template.md`, and `skills/dev-lifecycle/references/principal-review.md` (Stage 2 — AI Assistant to AI Programmer Handoff)**:
   - In `dev-designer` (Step 3) and `dev-lifecycle` (`Handoff Choice` -> `Package`), persist state via `resume_context.py --state --epic <epic_slug>` and emit both `--emit-prompt principal-review` (Scenario 1 for AI Assistant) and `--emit-prompt implement` (Scenario 2 for AI Programmer).
   - Update `skills/dev-lifecycle/references/handoff-template.md` `## Resume Prompt` to assign `[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]` and invoke `resume_context.py --role programmer --epic <epic_slug>` while preserving all existing lines required by `test_lifecycle_document_contract.py` and `test_verifiable_handoff_text.py`.
   - In `skills/dev-lifecycle/references/principal-review.md` and `skills/principal-review/SKILL.md`, after the Principal Review loop concludes, run `resume_context.py --state` and `--emit-prompt implement` (Scenario 2).
3. **`skills/dev-implementation/SKILL.md` and `skills/cross-model-review/SKILL.md` (Stage 3 — AI Programmer & Cross-Model Review Assistant)**:
   - In `dev-implementation` Phase 0, run `resume_context.py --role programmer --epic <epic_slug>`.
   - In `dev-implementation` Phase 2 (after each task commit), run `resume_context.py --log --epic <epic_slug> --task <task_id>` and `--state`.
   - In `dev-implementation` Phase 4 (after Gate 4 PASS), run `resume_context.py --state` and emit `--emit-prompt cross-review` (Scenario 3 for AI Assistant).
   - In `skills/cross-model-review/SKILL.md`, after triage decisions are recorded, run `resume_context.py --state` and emit `--emit-prompt finish` (or `--emit-prompt implement` for fixes).
4. **`skills/finishing-a-development-branch/SKILL.md` (Stage 4 `/finish`)**:
   - In the **Pre-Finish Hook** (alongside `sync_task_status.py archive-done`), invoke `resume_context.py --complete "<epic_slug>" "<milestone_summary>"` (`save-context`) to append the milestone to `.devtool/PROJECT_LEDGER.md` and rotate the epic's state/logs into `.devtool/archive/`.
5. **Release Verification Harness (`scripts/verify.sh` & `scripts/test_resume_context.py`)**:
   - Add Section 15 (`== 15. Context memory management CLI and Tri-Role governance are enforced ==`) to `scripts/verify.sh` running `python3 -m unittest scripts/test_resume_context.py`.
   - Add integration test `test_cmm_hp_03_skills_lifecycle_hooks_and_verify_harness` in `scripts/test_resume_context.py`.

## Files

Allowed files:
- `skills/dev-brainstorming/SKILL.md`
- `skills/dev-designer/SKILL.md`
- `skills/dev-lifecycle/SKILL.md`
- `skills/dev-lifecycle/references/handoff-template.md`
- `skills/dev-lifecycle/references/principal-review.md`
- `skills/principal-review/SKILL.md`
- `skills/dev-implementation/SKILL.md`
- `skills/cross-model-review/SKILL.md`
- `skills/finishing-a-development-branch/SKILL.md`
- `scripts/verify.sh`
- `scripts/test_resume_context.py` (new)

Read-only context:
- `.devtool/epic/context_memory_management/context_memory_management.en.md` — HLD specifications
- `scripts/resume_context.py` (new)
- `skills/resume-context/SKILL.md` (new)
- `skills/save-context/SKILL.md` (new)
- `scripts/test_lifecycle_document_contract.py` — lifecycle contract test suite
- `scripts/test_verifiable_handoff_text.py` — handoff text test suite

## Design Rationale

- Embedding `resume_context.py` hooks directly into Stage 1, Stage 2, Principal Review, Stage 3, Cross-Model Review, and Stage 4 (`/finish`) ensures context is saved automatically without relying on agent memory.
- Applicable skills: `d3nexus:writing-skills`, `d3nexus:verification-before-completion`, `d3nexus:test-driven-development`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: Lifecycle `SKILL.md` files, `handoff-template.md`, `principal-review.md`, `scripts/verify.sh`, and `scripts/test_resume_context.py`.
- **Downstream Callers**: All epics orchestrated by `d3nexus:dev-lifecycle` and release checks in `scripts/verify.sh`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% integration test coverage and full `scripts/verify.sh` green pass.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: CMM-HP-03

```gherkin
Scenario: [CMM-HP-03] [Tier C - Integration] End-to-End Skill Definitions, Dev-Lifecycle Hooks, and Release Verification Harness
  Given the completed resume-context and save-context skills, CRITICAL_RULES.md Rule 7, dev-lifecycle stage skill hooks, and scripts/verify.sh registration
  When the engineer runs the verification suite for context_memory_management
  Then skills/resume-context/SKILL.md and skills/save-context/SKILL.md pass YAML frontmatter and relative link checks
  And dev-brainstorming, dev-designer, dev-lifecycle, principal-review, dev-implementation, cross-model-review, and finishing-a-development-branch contain the required resume_context.py integration hooks
  And scripts/verify.sh executes scripts/test_resume_context.py with exit code 0
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_hp_03` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_hp_03` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check scripts/resume_context.py docs/architecture/resume_context.py scripts/test_resume_context.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict --follow-imports=silent scripts/resume_context.py scripts/test_resume_context.py` | exit 0 | — |
| V5 | TIER-B | `python3 scripts/test_lifecycle_document_contract.py` | exit 0; contains "OK" | — |
| V6 | TIER-B | `python3 -m unittest scripts/test_verifiable_handoff_text.py scripts/test_lifecycle_signals.py` | exit 0; contains "OK" | — |
| V7 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
| V8 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/context-memory-management.xml scripts/test_resume_context.py` | exit 0; results build/test-results/context-memory-management.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Word counts in `skills/dev-lifecycle/SKILL.md` ($>2500$ words) or `skills/dev-implementation/SKILL.md` ($>4500$ words) exceed contract limits.

## Decisions Already Made

- Runtime skills `skills/dev-lifecycle/SKILL.md` and `skills/dev-implementation/SKILL.md` must never contain Mermaid or Graphviz DOT fences and must stay within their word-count ceilings ($\le 2500$ and $\le 4500$ words respectively).
- `skills/dev-lifecycle/references/handoff-template.md` retains all 4 Execution Guardrails (`Bounded context protocol`, `Strict spec fidelity`, `Zero test fakery`, `No contract repair by the executor`) and adds the `[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]` role header and `resume_context.py --role programmer --epic <epic_slug>` instruction in `## Resume Prompt`.
- `skills/finishing-a-development-branch/SKILL.md` executes `resume_context.py --complete "<epic_slug>" "<milestone_summary>"` in its Pre-Finish Hook when archiving completed epic tasks.
- `scripts/verify.sh` Section 15 executes `python3 -m unittest scripts/test_resume_context.py`.

## Definition of Done

- All `/dev-lifecycle` skills (`dev-brainstorming`, `dev-designer`, `dev-lifecycle`, `handoff-template.md`, `principal-review.md`, `principal-review`, `dev-implementation`, `cross-model-review`, `finishing-a-development-branch`) integrate `resume_context.py` hooks and pass `test_cmm_hp_03` (V2).
- Ruff linting and Mypy strict type checks pass cleanly (V3, V4).
- Existing lifecycle document contract and signal tests pass without regression (V5, V6).
- `scripts/verify.sh` runs `scripts/test_resume_context.py` in Section 15 and exits 0 with "PASS — safe to publish" (V7).
- Full JUnit XML report `build/test-results/context-memory-management.xml` is generated and all 12 BDD scenarios pass (V8).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 3](task_03_resume_and_save_skills.md) — requires `skills/resume-context/SKILL.md`, `skills/save-context/SKILL.md`, and `scripts/resume_context.py` to be in place.

## References & Rollback

- Spec: `.devtool/epic/context_memory_management/2026-10-30-context-memory-management-design.en.md`
- HLD: `.devtool/epic/context_memory_management/context_memory_management.en.md`
- Rollback: Revert modified lifecycle `SKILL.md` files and `scripts/verify.sh`.
