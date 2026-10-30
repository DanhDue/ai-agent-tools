---
id: "task_03_resume_and_save_skills"
status: "done"
priority: "high"
assignee: null
epic: "context_memory_management"
dueDate: null
created: "2026-10-30T16:05:00Z"
modified: "2026-10-30T17:30:17Z"
completedAt: "2026-10-30T17:30:17Z"
labels: ["skills", "rules", "persona", "governance"]
order: "a3"
---

# Task 3: Resume-Context and Save-Context Skills and Tri-Role Critical Rules

Epic: [context_memory_management](context_memory_management.en.md)

## Requirement Analysis

Create the two new skills `skills/resume-context/SKILL.md` and `skills/save-context/SKILL.md`, update `rules/CRITICAL_RULES.md` with Rule 8, and verify non-destructive checkpoint saving (`[CMM-ST-02]`):
1. Author `skills/resume-context/SKILL.md`:
   - YAML frontmatter containing strictly `name: resume-context` and `description`.
   - Instructions for running `scripts/resume_context.py` on session start or account switch (`resume` / `python3 $HOME/Projects/ai-agent-tools/scripts/resume_context.py`).
   - Explicit **Tri-Role Governance Model** enforcement:
     - **2.1 Human Architect**: owns strategy, gate approvals, and triage decisions.
     - **2.2 AI Assistant (`--role assistant`)**: default persona for technical discussions, architectural analysis, solution evaluation, Principal Review, and Cross-Model Review. Strictly prohibited from modifying production code or application tests.
     - **2.3 AI Programmer (`--role programmer`)**: activated when receiving an implementation prompt or `/dev-implementation`. Executes tasks in git worktrees with TDD, Clean Code, and strict `Allowed files` boundaries.
   - Concise 5–10 bullet project state summary protocol before answering the user's request.
2. Author `skills/save-context/SKILL.md`:
   - YAML frontmatter containing strictly `name: save-context` and `description`.
   - Instructions for saving context with custom prompts (`--state --prompt "<custom_note>"`, `--log`, or `save-context --checkpoint <epic_slug> "<custom_note>"` for mid-flight saves, and `--complete <epic_slug> "<milestone_summary>"` on feature completion in `/finish`).
   - Instructions for emitting role-bound handoff prompts (`--emit-prompt principal-review|implement|cross-review|finish|assistant`) across all 4 operational scenarios.
3. Update `rules/CRITICAL_RULES.md`:
   - Add Section `## 8. Mandatory Two-Tier Project Memory & Tri-Role Persona Discipline` (preserving existing Sections 1–7) enforcing automatic context persistence across projects and strict separation between `AI Assistant` and `AI Programmer`.
4. Add unit and integration tests in `scripts/test_resume_context.py` covering `CMM-ST-02` (`--complete --checkpoint` non-destructive save with custom prompt and skill/rule validation).

## Files

Allowed files:
- `skills/resume-context/SKILL.md` (new)
- `skills/save-context/SKILL.md` (new)
- `rules/CRITICAL_RULES.md`
- `scripts/resume_context.py` (new)
- `docs/architecture/resume_context.py`
- `scripts/test_resume_context.py` (new)

Read-only context:
- `.devtool/epic/context_memory_management/context_memory_management.en.md` — HLD specifications
- `docs/architecture/save_resume_rules.md` — baseline architecture rules
- `skills/session_init/SKILL.md` — legacy session initialization reference

## Design Rationale

- Separating `resume-context` and `save-context` into dedicated skills with `d3nexus:` cross-references and Rule 8 in `rules/CRITICAL_RULES.md` guarantees that every agent session across all repositories respects Two-Tier Project Memory and the AI Assistant vs AI Programmer boundary.
- Applicable skills: `d3nexus:writing-skills`, `d3nexus:test-driven-development`, `d3nexus:doc_quality_check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `skills/resume-context/SKILL.md`, `skills/save-context/SKILL.md`, `rules/CRITICAL_RULES.md`, and `test_cmm_st_02` in `scripts/test_resume_context.py`.
- **Downstream Callers**: Task 4 lifecycle skills and all agent sessions loading `CRITICAL_RULES.md`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% coverage of `--checkpoint` non-destructive saves and skill/rule document lint checks.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: CMM-ST-02

```gherkin
Scenario: [CMM-ST-02] [Tier A - Unit] Non-Destructive Checkpoint Save via --complete --checkpoint With Custom Prompt
  Given an in-flight epic context_memory_management with existing entries in .devtool/logs/activity_context_memory_management.log
  When the engineer or agent runs save-context --checkpoint context_memory_management "Locked multi-epic storage model; next write task_01"
  Then .devtool/state/context_memory_management.md and .devtool/logs/activity_context_memory_management.log are updated with the custom prompt note
  And .devtool/PROJECT_LEDGER.md is not modified and .devtool/logs/activity_context_memory_management.log is not moved to .devtool/archive/
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_st_02` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest scripts/test_resume_context.py -k test_cmm_st_02` | exit 0; contains "OK" | — |
| V3 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/resume-context/SKILL.md skills/save-context/SKILL.md` | exit 0; contains "0 findings" | — |
| V4 | TIER-B | `ruff check scripts/resume_context.py docs/architecture/resume_context.py scripts/test_resume_context.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent scripts/resume_context.py scripts/test_resume_context.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_03.xml scripts/test_resume_context.py` | exit 0; results build/test-results/task_03.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `rules/CRITICAL_RULES.md` frontmatter is removed or corrupted.

## Decisions Already Made

- `skills/resume-context/SKILL.md` and `skills/save-context/SKILL.md` frontmatter contains only `name` and `description`.
- `save-context --checkpoint <epic_slug> "<custom_prompt>"` (i.e. `resume_context.py --complete --checkpoint <epic_slug> "<custom_prompt>"`) updates `.devtool/state/<epic_slug>.md` and `.devtool/logs/activity_<epic_slug>.log` without appending to `PROJECT_LEDGER.md` or moving logs to `.devtool/archive/`.
- `rules/CRITICAL_RULES.md` preserves its YAML frontmatter (`---`) at line 1 and existing Sections 1–7, and adds Section `## 8. Mandatory Two-Tier Project Memory & Tri-Role Persona Discipline`.

## Definition of Done

- `skills/resume-context/SKILL.md`, `skills/save-context/SKILL.md`, and `rules/CRITICAL_RULES.md` Rule 8 are authored and pass document checks (V3).
- `--complete --checkpoint` non-destructive checkpoint save passes unit and integration tests (V2).
- Ruff linting and Mypy strict type checks pass cleanly (V4, V5).
- JUnit XML report is generated and `CMM-ST-02` passes (V6).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 2](task_02_zshrc_and_environment_sync.md) — builds upon `scripts/resume_context.py` and `scripts/test_resume_context.py`.

## References & Rollback

- Spec: `.devtool/epic/context_memory_management/2026-10-30-context-memory-management-design.en.md`
- HLD: `.devtool/epic/context_memory_management/context_memory_management.en.md`
- Rollback: Remove `skills/resume-context/`, `skills/save-context/`, and revert `rules/CRITICAL_RULES.md`.
