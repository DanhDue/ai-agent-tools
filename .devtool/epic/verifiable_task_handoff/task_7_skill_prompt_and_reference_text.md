---
id: "task_7_skill_prompt_and_reference_text"
status: "done"
priority: "high"
assignee: null
epic: "verifiable_task_handoff"
dueDate: null
created: "2026-10-16T06:53:44Z"
modified: "2026-10-16T08:21:35Z"
completedAt: "2026-10-16T08:21:35Z"
labels: ["skills", "documentation"]
order: "a7"
---

# Task 7: Skill, prompt and reference text

Epic: [verifiable_task_handoff](verifiable_task_handoff.en.md)

## Requirement Analysis

State the new contract in the skills a receiving agent reads, and lock each statement with a test
named after its scenario. Authority: source spec sections 5, 6, 12 and 13. Follow
`d3nexus:writing-skills` for every skill edit.

### skills/dev-designer/SKILL.md

- Task file structure: replace item 5 (Relevant Files & Context Pointers) with `## Files` holding
  `Allowed files:` and `Read-only context:`, and replace item 9 (Test & Verification Checklist, with
  every per-platform checkbox block) with `## Verification`: the five-column table, the Expect grammar,
  the `Needs` column and the `RED: n/a — <reason>` line. Add `## Stop and Report If` with the five
  default bullets verbatim, and `## Decisions Already Made`. Item 10 says every Definition of Done
  bullet ends with row references or `(Gate 5)`. Item 11's heading stays `Dependencies & Blockers`,
  with each `Blocked by` clause on one line.
- Integration Test Plan: add the `Protected paths:` and `Integration results:` lines beside
  `Integration test roots:`, and a `## Verification Environment` section of the HLD.
- Tier C — BDD Automation: "Each identifier is assigned to at least one task" becomes
  "Each identifier is assigned to exactly one task".
- Step 3 runs `check_task_contract.py --design` beside `check_bdd_traceability.py plan`; both must
  exit 0 before the commit.
- Red Flags: add "A Definition of Done item with neither a row reference nor `(Gate 5)`" and
  "Task files whose paths or commands were not checked with `check_task_contract.py --design`".

### skills/dev-designer/references/verification-rows.md (new)

Per platform — Python, Android, Web, iOS, Rust, Flutter — example `RED`, `GREEN`, `TIER-B` and
`TIER-C` rows, and how to produce the report for `results`: `pytest --junitxml=<path>`; Gradle's
`build/test-results/<task>/`; `node --test --test-reporter=junit`, `vitest --reporter=junit`,
Playwright `--reporter=junit`; `swift test --xunit-output <path>` (pass the directory for Swift
Testing's extra file; `.xcresult` conversion is the project's job); `cargo nextest` with JUnit in
`.config/nextest.toml`; `flutter test --file-reporter json:<path>`. Note that results paths must be
ignored by git.

### skills/dev-implementation/SKILL.md

- Phase 1 (Gate 3, fresh and on resume): run `check_task_contract.py` and `plan`; a failure means
  retrofit through dev-designer's Updating an Existing Epic, never by the receiving agent.
- Phase 2: the Gate to Done becomes `run_task_checks.py red` before implementation,
  `run_task_checks.py verify` after it, `run_task_checks.py status` before asking for `done`, then
  `sync_task_status.py task <id> done`, which refuses unless the evidence matches. The task's one
  commit stages `.devtool/epic/<epic_dir>/evidence/<task_id>.json` with the code and the task file.
- After the last task, the **Review Choice**, asked every time: 1. **Finish** (Gate 4, Gate 5, then
  `finishing-a-development-branch`); 2. **Cross-model review**, through the Claude CLI or the Codex
  CLI, which the developer picks every time, listing those on `PATH` and saying the repository's
  content goes to that provider. Option 2 runs `run_external_review.py run`; describe the flow
  table of spec section 12, including commits of `review_results.md`, decisions written only on the
  developer's words, and that a CLI that fails (for example, out of credits) lets the developer pick
  again.
- Phase 4, in this order: `run_external_review.py check` when `review_results.md` exists,
  `audit_epic.py`, the HLD's Integration results commands, `check_bdd_traceability.py tests --results`,
  then `@quality_check`. Phase 4.1 adds the audit's disclosure sections and a summary of the review
  rounds to its report.

### skills/dev-lifecycle/SKILL.md

- The sequence diagram gains the Review Choice between task execution and Gate 4.
- Gate 4's machine criteria add `audit_epic.py` and result-based traceability (`--results`).
- The packaging preflight adds `check_task_contract.py --design`.
- Red Flags add: ticking checkboxes or writing evidence by hand; changing a Verification table,
  Allowed files or a protected path without stopping to ask; running the cross-model review without
  asking; picking the review CLI for the developer; writing a `dismissed` decision without the
  developer's words.

### skills/dev-lifecycle/references/handoff-template.md

Rules for the Receiving Agent gains:
"Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report."

### skills/subagent-driven-development/implementer-prompt.md

Replace "your report is the test evidence" with: run `run_task_checks.py red` before implementing
and `run_task_checks.py verify` after; the evidence file is the test evidence; cite its path and
never paste or summarise test output as evidence. A `Stop and Report If` condition is reported as
`BLOCKED`, naming it.

### skills/subagent-driven-development/task-reviewer-prompt.md

The Tests section reads the evidence file and runs `run_task_checks.py status`; a missing evidence
file, a row not `PASS`, or a `tree` mismatch is Critical; the implementer's account of its tests is a
claim. The reviewer still does not re-run the suite.

### scripts/test_verifiable_handoff_text.py (new)

One `unittest` method per identifier, each asserting these exact phrases in these files:

| Method | File | Phrases present | Phrases absent |
|---|---|---|---|
| `test_vth_hp_06_dev_designer_states_the_task_contract` | `skills/dev-designer/SKILL.md` | `Stop and Report If`, `Decisions Already Made`, `Allowed files:`, `RED: n/a`, `(Gate 5)`, `exactly one task`, `check_task_contract.py --design`, `Protected paths:`, `Integration results:`, `Verification Environment`, `references/verification-rows.md` | `Test & Verification Checklist` |
| same method | `skills/dev-designer/references/verification-rows.md` | `Python`, `Android`, `Web`, `iOS`, `Rust`, `Flutter`, `--junitxml`, `--file-reporter json:`, `--xunit-output`, `nextest` | — |
| `test_vth_hp_07_dev_implementation_states_recorder_and_gate` | `skills/dev-implementation/SKILL.md` | `run_task_checks.py red`, `run_task_checks.py verify`, `run_task_checks.py status`, `evidence/<task_id>.json`, `check_task_contract.py`; and within `### Phase 4` up to `### Phase 4.1`, the positions of `audit_epic.py`, `Integration results`, `tests --results` and `@quality_check` increase in that order | — |
| `test_vth_hp_08_dev_lifecycle_and_handoff_state_the_rules` | `skills/dev-lifecycle/SKILL.md`; `skills/dev-lifecycle/references/handoff-template.md` | `audit_epic.py`, `result-based traceability`, `check_task_contract.py --design`; `Never edit a task's Verification table` | — |
| `test_vth_hp_09_sdd_prompts_treat_evidence_as_proof` | `implementer-prompt.md`; `task-reviewer-prompt.md` (both in `skills/subagent-driven-development/`) | `run_task_checks.py red`, `run_task_checks.py verify`, `the evidence file is the test evidence`; `run_task_checks.py status`, `Critical` | `your report is the test evidence` (implementer) |
| `test_vth_hp_13_review_choice_is_stated` | `skills/dev-implementation/SKILL.md`; `skills/dev-lifecycle/SKILL.md` | `Review Choice`, `Finish`, `Cross-model review`, `Claude CLI`, `Codex CLI`, `run_external_review.py run`, `run_external_review.py check`, `review_results.md`; `picking the review CLI for the developer` | — |

`scripts/verify.sh`, section 11: add `python3 -m unittest scripts/test_verifiable_handoff_text.py || FAILED=1`.

## Files

Allowed files:
- `skills/dev-designer/SKILL.md`
- `skills/dev-designer/references/verification-rows.md` (new)
- `skills/dev-implementation/SKILL.md`
- `skills/dev-lifecycle/SKILL.md`
- `skills/dev-lifecycle/references/handoff-template.md`
- `skills/subagent-driven-development/implementer-prompt.md`
- `skills/subagent-driven-development/task-reviewer-prompt.md`
- `scripts/test_verifiable_handoff_text.py` (new)
- `scripts/verify.sh`

Read-only context:
- `.devtool/epic/verifiable_task_handoff/2026-10-16-verifiable-task-handoff-design.en.md` — sections 5, 6, 12 and 13
- `scripts/test_lifecycle_document_contract.py` — phrases that must survive every edit
- `skills/writing-skills/SKILL.md` — how to edit a skill

## Design Rationale

- Each statement a receiving agent relies on is locked by a test method named after its scenario, so
  result-based traceability can prove it (HLD section 4.5 item 3).
- The per-platform checklists move out of `dev-designer` into a reference, which keeps `SKILL.md`
  concise as this repository's CLAUDE.md asks.
- Applicable skills: `d3nexus:writing-skills`, `d3nexus:test-driven-development`,
  `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: the seven skill and prompt files above.
- **Downstream callers**: every project with the plugin installed reads these skills.
- **Cross-platform bridges**: none.
- **Target test coverage threshold**: every phrase of the table asserted.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: VTH-HP-06, VTH-HP-07, VTH-HP-08, VTH-HP-09, VTH-HP-13

```gherkin
Scenario: [VTH-HP-06] [Tier C - Integration] dev-designer states the task contract
  Given skills/dev-designer/SKILL.md and its references/verification-rows.md
  When the text is read
  Then the task template names Files, Verification, Definition of Done, Stop and Report If and Decisions Already Made
  And it requires each identifier on exactly one task's Covers line
  And Step 3 runs check_task_contract.py --design beside plan
  And verification-rows.md gives report commands for Python, Android, Web, iOS, Rust and Flutter

Scenario: [VTH-HP-07] [Tier C - Integration] dev-implementation states the recorder and the gate
  Given skills/dev-implementation/SKILL.md
  When the text is read
  Then Phase 2 runs run_task_checks.py red before implementation and verify after it
  And the task commit stages the evidence file
  And Phase 4 runs audit_epic.py, the Integration results commands, tests --results and quality_check in that order

Scenario: [VTH-HP-08] [Tier C - Integration] dev-lifecycle and the handoff template state the rules
  Given skills/dev-lifecycle/SKILL.md and its references/handoff-template.md
  When the text is read
  Then Gate 4 names the audit and result-based traceability
  And the packaging preflight runs check_task_contract.py --design
  And the handoff rules forbid editing a Verification table, Allowed files or a protected path

Scenario: [VTH-HP-09] [Tier C - Integration] The SDD prompts treat evidence, not prose, as proof
  Given the implementer and task reviewer prompts of subagent-driven-development
  When the text is read
  Then the implementer runs the recorder and cites the evidence file
  And the reviewer runs run_task_checks.py status and treats missing evidence as Critical

Scenario: [VTH-HP-13] [Tier C - Integration] The Review Choice is stated where it is asked
  Given skills/dev-implementation/SKILL.md and skills/dev-lifecycle/SKILL.md
  When the text is read
  Then dev-implementation asks the Review Choice, "Finish" or "Cross-model review", after the last task
  And the developer picks the Claude CLI or the Codex CLI
  And Phase 4 starts with run_external_review.py check when review_results.md exists
  And dev-lifecycle's Red Flags name picking the review CLI for the developer
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest scripts/test_verifiable_handoff_text.py` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest scripts/test_verifiable_handoff_text.py` | exit 0; contains "OK" | — |
| V3 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-designer/SKILL.md skills/dev-designer/references/verification-rows.md skills/dev-implementation/SKILL.md skills/dev-lifecycle/SKILL.md` | exit 0; contains "0 findings" | — |
| V4 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc skills/dev-lifecycle/references/handoff-template.md` | exit 0; contains "0 findings" | — |
| V5 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_7.xml scripts/test_verifiable_handoff_text.py` | exit 0; results build/test-results/task_7.xml | — |
| V7 | TIER-C | `python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py tests --scenarios .devtool/epic/verifiable_task_handoff/bdd_scenarios.en.md --roots scripts/ --results build/test-results/task_7.xml --ids VTH-HP-06 VTH-HP-07 VTH-HP-08 VTH-HP-09 VTH-HP-13` | exit 0; contains "Result: 5/5 covered — PASS" | — |

## Definition of Done

- Every phrase of the table is present or absent as listed, and the five covered scenarios pass (V2, V6, V7).
- The edited skills and the new reference pass the document checks (V3, V4).
- `scripts/verify.sh` passes, including the lifecycle document contract and the new text test (V5).
- The rewritten skills read clearly to a receiving agent that has seen none of this conversation (Gate 5).

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- An edit would remove a phrase that `scripts/test_lifecycle_document_contract.py` requires.

## Decisions Already Made

- The two SDD prompts have bare code fences at lines 5 and 10 that `check_document.py` reports
  (MD040); they predate this epic, stay as they are, and are left out of V3.
- `scripts/test_lifecycle_document_contract.py` is not edited; its required phrases stay in the skills.
- `doc-implementation` is not edited; the `done` gate does not apply to document epics.
- Duplicated Python blocks elsewhere in `dev-designer` (Tier list, Design Rationale, parallel rules)
  are left as they are; only the checklist blocks this task replaces go.

## Dependencies & Blockers

- Blocked by [Task 1](task_1_verification_table_parser_and_evidence_recorder.md), [Task 2](task_2_test_result_reports_and_result_based_traceability.md), [Task 3](task_3_design_time_task_contract_check.md), [Task 4](task_4_done_gate_and_evidence_status.md), [Task 5](task_5_gate_4_epic_audit.md), [Task 6](task_6_cross_model_review_runner.md)

## References & Rollback

- Source spec sections 5, 6, 12 and 13.
- Rollback: revert this task's commit; the scripts keep working, and the skills describe the old flow.
