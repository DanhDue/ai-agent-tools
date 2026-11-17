---
id: "task_08_kit_guides_verify_registration_and_acceptance"
status: "todo"
priority: "high"
assignee: null
epic: "four_persona_governance"
dueDate: null
created: "2026-11-17T10:00:00Z"
modified: "2026-11-17T10:00:00Z"
labels: ["docs", "integration", "acceptance"]
order: "a8"
review_tier: "full"
---

# Task 8: Kit Guides, verify.sh Registration and End-to-End Acceptance

Epic: [four_persona_governance](../epic/four_persona_governance/four_persona_governance.en.md)

## Requirement Analysis

Close the epic: human guides, suite registration and one end-to-end test across every task.

1. **Guides (bilingual, spec §6.4)**: `docs/lifecycles.en.md` and `docs/lifecycles.vi.md` (dev-lifecycle
   section, Skills Catalog, Role and Model Matrix) and `docs/context-memory-quick-guide.en.md` /
   `.vi.md` (persona section, workflow diagram, scenario headings) describe the four personas,
   `/d3nexus:dev-config` (including the `--provider` shortcut and the agy profile pool with its lease file, and `set` with `--provider`, `--model`, `--effort` and `--profile`),
   checkpoints, low-quota mode and the quota gate (5-hour and weekly windows). Both variants keep identical
   structure; English is written first.
2. **`scripts/verify.sh`**: register `tests/test_fpg_persona_config.py`, `tests/test_fpg_dispatch_and_quota.py`,
   `tests/test_fpg_provider_shortcut.py`, `tests/test_fpg_agy_profile_pool.py`, `tests/test_fpg_agy_dispatch.py`, `tests/test_fpg_set_provider_model_profile.py`,
   `tests/test_fpg_checkpoint_and_briefs.py`, `tests/test_fpg_runner_personas.py`,
   `tests/test_fpg_english_only_and_ownership.py`, `tests/test_fpg_dashboard_sync.py`,
   `tests/test_fpg_governance_text.py`, `tests/test_fpg_english_only_text.py` and `tests/test_fpg_acceptance.py` in `SUITES` (section 11, mode
   `pytest`).
3. **Acceptance (`tests/test_fpg_acceptance.py`)**: FPG-HP-08 end to end with stub CLIs, plus a check that
   every `tests/test_fpg_*.py` file is registered in `scripts/verify.sh`.

## Files

Allowed files:
- `docs/lifecycles.en.md`
- `docs/lifecycles.vi.md`
- `docs/context-memory-quick-guide.en.md`
- `docs/context-memory-quick-guide.vi.md`
- `scripts/verify.sh`
- `tests/test_token_throttling_acceptance.py`
- `tests/test_fpg_acceptance.py` (new)

Read-only context:
- `.devtool/epic/four_persona_governance/2026-11-17-four-persona-governance-design.en.md` — full spec
- `skills/dev-lifecycle/references/orchestration-roles.md` — final persona matrix from Task 6
- `rules/CRITICAL_RULES.md` — final §8 and §11

## Design Rationale

The guides are documents, so they stay bilingual under the doc-lifecycle contract; the acceptance test is
the single place that proves the pieces of Tasks 1–7 work together. Applicable skills:
`d3nexus:test-driven-development`, `d3nexus:doc_quality_check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `docs/lifecycles.en.md`: `## dev-lifecycle` (L32-L105), `### dev-lifecycle Skills Catalog & Autonomous Convergence Architecture` (L129-L154), `### Role and Model Matrix` (L155-L178)
  - `docs/lifecycles.vi.md`: `## dev-lifecycle` (L35-L108), `### Danh mục Skill của dev-lifecycle & Kiến trúc Hội tụ Tự động` (L132-L157), `### Ma trận Role và Model` (L158-L181)
  - `docs/context-memory-quick-guide.en.md`: `## 1. Tri-Role Governance and 10-Second Command Cheat-Sheet` (L25-L48), `## 2. End-to-End Save and Resume Workflow Diagram` (L49-L132), scenario sections (L133-L315)
  - `docs/context-memory-quick-guide.vi.md`: `## 1. Quản trị Ba Vai trò và Bảng Cheat-Sheet Lệnh 10 Giây` (L25-L48), `## 2. Sơ đồ Luồng Lưu và Khôi phục Ngữ cảnh Toàn trình` (L49-L132), scenario sections (L133-L315)
  - `scripts/verify.sh`: `SUITES = [` (L362-L420)
  - `tests/test_token_throttling_acceptance.py`: `test_tto_ec_06_verify_suite_registration` (L711-L805)
- **Downstream Callers**: `scripts/verify.sh` (Gate 4 `architecture` capability); readers of the kit guides.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: one end-to-end pass through readiness, packaging, prompts, runner, checkpoints and dashboard.

### BDD SCENARIOS

Covers: FPG-HP-08


```gherkin
Scenario: [FPG-HP-08] [Tier C - Integration] End-to-end English-only epic flows from readiness to dashboard with persona stubs
Given a temporary repository with an English-only epic of two tasks, a project persona config and stub "agy" executables that return valid summary contracts
When readiness, packaging, "--emit-prompt implement", the runner's implementation step and "scan_repo" run in sequence
Then every dispatch argv was built from the configured bindings
And the heartbeat holds checkpoints "gate2_tasks_locked", "subagent_returned" and "wave_merged" in that order
And the dashboard payload shows both tasks done, the latest checkpoint "wave_merged" and no human-action alert
```

```gherkin
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_acceptance.py::test_fpg_hp_08_end_to_end_english_only_epic_with_persona_stubs` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_acceptance.py tests/test_token_throttling_acceptance.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc --require-bilingual docs/lifecycles.en.md docs/lifecycles.vi.md docs/context-memory-quick-guide.en.md docs/context-memory-quick-guide.vi.md` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_fpg_acceptance.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_fpg_acceptance.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/fpg_task_08.xml tests/test_fpg_acceptance.py tests/test_fpg_persona_config.py tests/test_fpg_dispatch_and_quota.py tests/test_fpg_provider_shortcut.py tests/test_fpg_agy_profile_pool.py tests/test_fpg_agy_dispatch.py tests/test_fpg_set_provider_model_profile.py tests/test_fpg_checkpoint_and_briefs.py tests/test_fpg_runner_personas.py tests/test_fpg_english_only_and_ownership.py tests/test_fpg_dashboard_sync.py tests/test_fpg_governance_text.py tests/test_fpg_english_only_text.py` | exit 0; results build/test-results/fpg_task_08.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Source: `scripts/verify.sh` `SUITES` tuples are `(section, mode, path, priority_weight, affects_doc_only)`
  (`L357-L362`); the thirteen `tests/test_fpg_*.py` suites go in section `"11"` with mode `"pytest"`,
  `affects_doc_only=False`, and the two text suites with `affects_doc_only=True`.
- Source: the kit guides are doc-lifecycle documents; `check_document.py --require-bilingual` stays their
  gate, and the English variant is written first.
- New contract: the acceptance test replaces `agy` with a stub executable on a temporary `PATH` that prints
  a valid `task-implementer` summary contract, and uses an injected quota gate returning sufficient.
- `scripts/verify.sh` is not run inside this task's Verification rows (it would become an implicit protected
  path); it runs once at Gate 4 through the `architecture` quality capability.

## Definition of Done

- FPG-HP-08 passes, and every `tests/test_fpg_*.py` suite passes together. (V2, V6)
- Both kit guides pass the bilingual ToC check. (V3)
- Ruff and mypy pass on the acceptance test. (V4, V5)
- The guides explain the four personas and dev-config clearly to the Human Architect. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 7](../epic/four_persona_governance/task_07_english_only_skill_text_and_mirror_isolation.md), [Task 9](../epic/four_persona_governance/task_09_provider_quick_setup.md), [Task 10](../epic/four_persona_governance/task_10_agy_profile_pool_and_leases.md) and [Task 11](../epic/four_persona_governance/task_11_set_provider_model_effort_profile.md).

Downstream dependents (blocked by Task 8): none.

## References & Rollback

- [Epic HLD](../epic/four_persona_governance/four_persona_governance.en.md)
- **Rollback**: Revert the task commit.
