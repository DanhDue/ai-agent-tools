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

Epic: [four_persona_governance](four_persona_governance.en.md)

## Requirement Analysis

Close the epic: human guides, suite registration and one end-to-end test across every task.

1. **Guides (bilingual, spec §6.4)**: `docs/lifecycles.en.md` and `docs/lifecycles.vi.md` (dev-lifecycle
   section, Skills Catalog, Role and Model Matrix) and `docs/context-memory-quick-guide.en.md` /
   `.vi.md` (persona section, workflow diagram, scenario headings) describe the four personas,
   `/d3nexus:dev-config` (including the `--provider` shortcut and the agy profile pool with its lease file, and `set` with `--provider`, `--model`, `--effort` and `--profile`),
   checkpoints, low-quota mode and the quota gate (5-hour and weekly windows). Both variants keep identical
   structure; English is written first.
1a. **dev-config quick guide (bilingual, [SE-11](four_persona_governance.en.md#spec-errata))**: new
   `docs/dev-config-quick-guide.en.md` (written first) and `.vi.md`, in the shape of the existing quick guides: title, a
   Vietnamese-translation pointer, Table of Contents, a Meta Data block (Kind `document`, Audience Human Architect,
   Diátaxis `how-to`, Non-goals, Acceptance, Source Spec) and numbered sections: (1) a ten-second cheat sheet, a table
   of goal to exact command; (2) where settings live and which layer wins, read with `status`; (3) choose a
   provider, a model and an effort with `set` (positional and flag forms, the `--provider` shortcut, presets, the Kiro
   Sonnet example, the effort rules); (4) use several agy profiles (`profiles add|list|remove|release|clear|probe`,
   priority, `--profile` as prefer-then-rotate, leases, the 5-hour and weekly windows and their thresholds, and only
   profiles you own); (5) when quota runs out (low-quota mode, `quota-check`, the stop report, the commands it offers,
   and that the kit never switches model by itself); (6) a troubleshooting table of symptom, cause and command; (7) a
   command reference with exit codes. Every command is a real example with concrete values (profile names such as
   `profile_a` and `profile_b`, never a real account name, e-mail address or password) so a test can parse it, and no
   option that `dev_config.py --help` does not list may appear. The guide describes the behaviour after Tasks 1, 9, 10
   and 11. Add one line to `skills/dev-config/SKILL.md` that points to the guide.
2. **`scripts/verify.sh`**: register `tests/test_fpg_persona_config.py`, `tests/test_fpg_dispatch_and_quota.py`,
   `tests/test_fpg_provider_shortcut.py`, `tests/test_fpg_agy_profile_pool.py`, `tests/test_fpg_agy_dispatch.py`, `tests/test_fpg_set_provider_model_profile.py`,
   `tests/test_fpg_checkpoint_and_briefs.py`, `tests/test_fpg_runner_personas.py`,
   `tests/test_fpg_english_only_and_ownership.py`, `tests/test_fpg_dashboard_sync.py`,
   `tests/test_fpg_governance_text.py`, `tests/test_fpg_english_only_text.py` and `tests/test_fpg_acceptance.py` in `SUITES` (section 11, mode
   `pytest`).
3. **Acceptance (`tests/test_fpg_acceptance.py`)**: FPG-HP-08 end to end with stub CLIs, FPG-HP-16 (the quick
   guide documents only commands the real CLI parses), plus a check that every `tests/test_fpg_*.py` file is registered in
   `scripts/verify.sh`.

## Files

Allowed files:
- `docs/lifecycles.en.md`
- `docs/lifecycles.vi.md`
- `docs/context-memory-quick-guide.en.md`
- `docs/context-memory-quick-guide.vi.md`
- `docs/dev-config-quick-guide.en.md` (new)
- `docs/dev-config-quick-guide.vi.md` (new)
- `skills/dev-config/SKILL.md`
- `scripts/verify.sh`
- `tests/test_token_throttling_acceptance.py`
- `tests/test_fpg_acceptance.py` (new)

Read-only context:
- `.devtool/epic/four_persona_governance/2026-11-17-four-persona-governance-design.en.md` — full spec
- `skills/dev-lifecycle/references/orchestration-roles.md` — final persona matrix from Task 6
- `rules/CRITICAL_RULES.md` — final §8 and §11
- `scripts/dev_config.py` — `_build_parser` and the real option list the guide must match

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

Covers: FPG-HP-08, FPG-HP-16


```gherkin
Scenario: [FPG-HP-08] [Tier C - Integration] End-to-end English-only epic flows from readiness to dashboard with persona stubs
Given a temporary repository with an English-only epic of two tasks, a project persona config and stub "agy" executables that return valid summary contracts
When readiness, packaging, "--emit-prompt implement", the runner's implementation step and "scan_repo" run in sequence
Then every dispatch argv was built from the configured bindings
And the heartbeat holds checkpoints "gate2_tasks_locked", "subagent_returned" and "wave_merged" in that order
And the dashboard payload shows both tasks done, the latest checkpoint "wave_merged" and no human-action alert

Scenario: [FPG-HP-16] [Tier A - Unit] The dev-config quick guide documents only commands the real CLI accepts and keeps both language variants in step
Given the files "docs/dev-config-quick-guide.en.md" and "docs/dev-config-quick-guide.vi.md"
When the contract test extracts every command that begins with "/d3nexus:dev-config" or "python3 scripts/dev_config.py" from the fenced code blocks of the English guide and parses each one with the argument parser of "dev_config.py"
Then every command parses without a usage error
And the guide shows the subcommands "status", "models", "set", "preset", "reset", "low-quota", "checkpoint", "quota-check", "resolve", "profiles" and "dispatch", the options "--provider", "--model", "--effort" and "--profile", and the line "/d3nexus:dev-config set programmer kiro-sonnet high"
And the Vietnamese variant has the same number of headings and the same commands in the same order
And neither variant contains an e-mail address or the word "password"
```

```gherkin
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_acceptance.py::test_fpg_hp_08_end_to_end_english_only_epic_with_persona_stubs` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_acceptance.py tests/test_token_throttling_acceptance.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc --require-bilingual docs/lifecycles.en.md docs/lifecycles.vi.md docs/context-memory-quick-guide.en.md docs/context-memory-quick-guide.vi.md docs/dev-config-quick-guide.en.md docs/dev-config-quick-guide.vi.md` | exit 0 | — |
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
- New contract: the contract test `test_fpg_hp_16_quick_guide_commands_parse_with_the_real_cli` reads the fenced code
  blocks of the English guide, takes every line that starts with `/d3nexus:dev-config` or `python3 scripts/dev_config.py`,
  rewrites the first form to `dev_config.py` arguments with `shlex.split`, and parses each with the parser that
  `dev_config._build_parser` returns, loaded by path. A line that is a command must contain no `<placeholder>`; use real
  example values. The test also compares the heading count and the ordered command list of the Vietnamese variant, and
  rejects an e-mail address or the word `password` in either. The guide is a document: English first, then the Vietnamese
  variant; neither names a real profile.
- `scripts/verify.sh` is not run inside this task's Verification rows (it would become an implicit protected
  path); it runs once at Gate 4 through the `architecture` quality capability.

## Definition of Done

- FPG-HP-08 passes, and every `tests/test_fpg_*.py` suite passes together. (V2, V6)
- The kit guides and the dev-config quick guide pass the bilingual ToC check. (V3)
- Every `/d3nexus:dev-config` command in the quick guide parses with the real CLI, and both variants keep the same
  headings and commands. (V2, V6)
- Ruff and mypy pass on the acceptance test. (V4, V5)
- The guides explain the four personas and dev-config clearly to the Human Architect. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 7](task_07_english_only_skill_text_and_mirror_isolation.md), [Task 9](task_09_provider_quick_setup.md), [Task 10](task_10_agy_profile_pool_and_leases.md) and [Task 11](task_11_set_provider_model_effort_profile.md).

Downstream dependents (blocked by Task 8): none.

## References & Rollback

- [Epic HLD](four_persona_governance.en.md)
- **Rollback**: Revert the task commit.
