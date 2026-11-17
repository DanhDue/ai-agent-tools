---
id: "task_02_checkpoints_briefs_and_handoff_prompts"
status: "todo"
priority: "high"
assignee: null
epic: "four_persona_governance"
dueDate: null
created: "2026-11-17T10:00:00Z"
modified: "2026-11-17T10:00:00Z"
labels: ["state-envelope", "concurrency", "prompts", "architecture"]
order: "a2"
review_tier: "full"
---

# Task 2: Checkpoint Record, Persona Briefs and Handoff Prompts

Epic: [four_persona_governance](../epic/four_persona_governance/four_persona_governance.en.md)

## Requirement Analysis

Give `resume_context.py` the four-persona vocabulary and the checkpoint command (spec §3.2, §3.4, §8.1).

1. **Checkpoint storage (`scripts/_state_envelope.py`)**: new `update_epic_checkpoint(primary_root,
   epic_slug, checkpoint)` that, inside `run_state_transaction()` under `_state_lock`, sets the `checkpoint`
   block on every mirrored `<safe_slug>.heartbeat.json` and appends one `{"category": "checkpoint", ...}` line
   to `.devtool/logs/events_<safe_slug>.jsonl` per mirror.
2. **`--checkpoint EVENT --epic SLUG [--next TEXT]`** in `scripts/resume_context.py::main` (`L2512-L2800`):
   builds the block (`event`, `at`, `persona`, `head_sha`, `wave`, `tasks_done`, `tasks_in_flight`,
   `next_step`, `turns_since_checkpoint` = 0, `low_quota`), calls `update_epic_checkpoint`, and refreshes
   `Next Immediate Step` via `write_epic_state` (`L849-L930`). Plain `resume_context.py` prints the latest
   checkpoint of each active epic before the activity stream.
3. **Roles**: `--role` choices become `architect`, `orchestrator`, `programmer`; `assistant` is accepted and
   stored as `architect`. `print_role_banner` (`L61-L76`) prints the four-persona names.
4. **Briefs and prompts**: `_BRIEF_ROLE_CONTRACTS` (`L2026-L2051`) gains `fix-planner`; `task-reviewer`
   moves to Role 2.1 and drops the `done`/commit duty; `review-fixer` modes become `fast-track` and
   `apply-plan`. `emit_handoff_prompt` (`L2053-L2138`) names the persona and its resolved binding (via
   `persona_config.resolve_persona` and `build_dispatch_argv`, loaded by path) and never emits a `.vi.md` path.
5. **Latent bug**: `main` calls `parser.error` at `L2576` where `parser` is undefined (ruff F821, mypy
   name-defined); make the parser reachable there.
6. **Tests**: new `tests/test_fpg_checkpoint_and_briefs.py` (FPG-HP-04, FPG-HP-05, FPG-EC-03, FPG-AR-01);
   update the existing assertions that pin the Tri-Role vocabulary.

## Files

Allowed files:
- `scripts/resume_context.py`
- `scripts/_state_envelope.py`
- `scripts/test_resume_context.py`
- `tests/test_assistant_orchestrator_handoff.py`
- `tests/test_fpg_checkpoint_and_briefs.py` (new)

Read-only context:
- `scripts/persona_config.py` (new) — `resolve_persona`, `build_dispatch_argv` from Task 1
- `.devtool/epic/four_persona_governance/four_persona_governance.en.md` — Module Contracts 3 and 4
- `skills/dev-lifecycle/references/orchestration-roles.md` — current summary contracts

## Design Rationale

Extending the heartbeat keeps one locked, mirrored state record that `resume_context.py` and check-tasks
already read; a new state file would duplicate it. Applicable skills: `d3nexus:test-driven-development`,
`d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/_state_envelope.py`: `run_state_transaction` (L388-L496), `update_epic_heartbeat` (L497-L671), new `update_epic_checkpoint`
  - `scripts/resume_context.py`: `print_role_banner` (L61-L76), `write_epic_state` (L849-L930), `_BRIEF_ROLE_CONTRACTS` (L2026-L2051), `emit_handoff_prompt` (L2053-L2138), `main` (L2512-L2800)
  - `scripts/test_resume_context.py`: `test_cmm_st_01_tri_role_banners_and_emit_prompts` (L217-L249), `test_cmm_st_02_checkpoint_non_destructive_save` (L448-L505)
  - `tests/test_assistant_orchestrator_handoff.py`: role and brief assertions
- **Downstream Callers**: `check_tasks.py` heartbeat readers (Task 5), `lifecycle_runner.py` (Task 3), `package_epic.py` (imports `resume_context`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: every checkpoint event value, the role alias, every brief role.

### BDD SCENARIOS

Covers: FPG-HP-04, FPG-HP-05, FPG-EC-03, FPG-AR-01


```gherkin
Scenario: [FPG-HP-04] [Tier A - Unit] A checkpoint writes the heartbeat block, the state file and one event
Given an isolated git repository with epic "fpg_epic" and an existing heartbeat
When "resume_context.py --checkpoint subagent_returned --epic fpg_epic --next 'dispatch task_03 reviewer'" runs
Then ".devtool/state/fpg-epic.heartbeat.json" has checkpoint["event"] == "subagent_returned", checkpoint["next_step"] == "dispatch task_03 reviewer" and checkpoint["turns_since_checkpoint"] == 0
And ".devtool/state/fpg_epic.md" contains "dispatch task_03 reviewer" under "Next Immediate Step"
And ".devtool/logs/events_fpg-epic.jsonl" gains exactly one line whose "category" is "checkpoint"
And running "resume_context.py" with no arguments prints the "subagent_returned" checkpoint before the activity stream

Scenario: [FPG-HP-05] [Tier A - Unit] Briefs and the implement prompt name the persona binding and never a Vietnamese file
Given a project whose persona config binds "ai_architect_reviewer" to "argon" "high" and "orchestrator" to "hydrogen" "high"
And epic "fpg_epic" whose directory holds "fpg_epic.en.md", "fpg_epic.vi.md", "bdd_scenarios.en.md" and "bdd_scenarios.vi.md"
When "--emit-prompt brief --brief-role task-reviewer", "--emit-prompt brief --brief-role fix-planner" and "--emit-prompt implement" run for "fpg_epic"
Then the task-reviewer and fix-planner briefs name "Role 2.1 AI Architect & Reviewer" and the argv "agy --model gemini-4-argon-high --effort high"
And the implement prompt names "Role 2.2 Orchestrator" with model "gemini-4-hydrogen-high" and effort "high"
And none of the three outputs contains the substring ".vi.md"

Scenario: [FPG-EC-03] [Tier A - Unit] The legacy role name maps to the AI Architect
Given an isolated repository with epic "fpg_epic"
When "resume_context.py --state --epic fpg_epic --role assistant --status 'Stage 2'" runs
Then ".devtool/state/fpg_epic.md" records "Role: architect"
And "resume_context.py --role reviewer" exits non-zero with an argparse "invalid choice" message

Scenario: [FPG-AR-01] [Tier A - Unit] Concurrent checkpoints from root and worktree stay consistent under the lock
Given an isolated repository with epic "conc_epic" mirrored in the root and one worktree ".devtool"
When 6 threads each write 5 checkpoints with distinct "next_step" values through "update_epic_checkpoint"
Then both mirrored heartbeat files parse with json.loads and carry identical "checkpoint" blocks
And "events_conc-epic.jsonl" in each mirror holds exactly 30 "checkpoint" lines that all parse
```

```gherkin
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_checkpoint_and_briefs.py::test_fpg_hp_04_checkpoint_writes_heartbeat_state_and_event` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_checkpoint_and_briefs.py tests/test_assistant_orchestrator_handoff.py tests/test_rsdh_state_envelope.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m unittest scripts/test_resume_context.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/resume_context.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/resume_context.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/fpg_task_02.xml tests/test_fpg_checkpoint_and_briefs.py tests/test_rsdh_state_envelope.py` | exit 0; results build/test-results/fpg_task_02.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Source: `update_epic_heartbeat(...)` (`scripts/_state_envelope.py` `L497-L671`) keeps its signature and
  schema; the checkpoint block is written by the new function in the same transaction pattern.
- New contract: `update_epic_checkpoint(primary_root: Path, epic_slug: str, checkpoint: Mapping[str, Any])
  -> dict[str, Any]` returns the stored block; keys `event`, `at` (ISO-8601 UTC), `persona`, `head_sha`,
  `wave`, `tasks_done`, `tasks_in_flight`, `next_step`, `turns_since_checkpoint`, `low_quota`, optional
  `warning`.
- New contract: `CHECKPOINT_EVENTS = ("gate2_tasks_locked", "subagent_returned", "wave_merged",
  "model_unavailable", "turn_budget", "low_quota_stop", "quota_low")`; argparse `choices` enforce it.
- New contract: `--role` choices `("architect", "orchestrator", "programmer", "assistant")`; `assistant` is
  normalised to `architect` before writing `Role: architect`.
- New contract: `_BRIEF_ROLE_CONTRACTS` keys `task-implementer`, `task-reviewer`, `review-fixer`,
  `gate4-verifier`, `fix-planner`. `task-reviewer` schema `{"task_id", "verdict", "head_sha", "done_gate",
  "findings"}` with objective text that forbids edits and commits; `fix-planner` schema `{"round", "status":
  "PLANNED|ESCALATE", "plan_path", "halt_criteria": [...], "decision_sha"}`; `review-fixer` mode
  `"fast-track|apply-plan"`.
- New contract: brief and prompt persona labels are `Role 2.1 AI Architect & Reviewer`, `Role 2.2
  Orchestrator`, `Role 2.3 Programmer`; each brief prints `shlex.join(build_dispatch_argv(binding, mode))`
  with mode `read-only` for `task-reviewer` and `fix-planner`, else `write`.
- Emitted prompts list epic documents through a filter that drops every path ending in `.vi.md`.
- `parser` becomes reachable in `main` (module-level builder function or local variable), fixing F821.

## Definition of Done

- FPG-HP-04, FPG-HP-05, FPG-EC-03 and FPG-AR-01 pass. (V2, V6)
- Existing `resume_context.py` and state envelope suites pass after their role assertions are updated. (V2, V3)
- Ruff (including F821 at the old `L2576`) and mypy pass. (V4, V5)

## Dependencies & Blockers

Blocked by [Task 1](../epic/four_persona_governance/task_01_persona_config_and_dev_config_cli.md).

Downstream dependents (blocked by Task 2): `task_03`, `task_05`.

## References & Rollback

- [Epic HLD](../epic/four_persona_governance/four_persona_governance.en.md)
- **Rollback**: Revert the task commit; heartbeats written with a `checkpoint` block remain readable because
  readers ignore unknown keys.
