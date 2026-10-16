---
id: "task_5_gate_4_epic_audit"
status: "todo"
priority: "high"
assignee: null
epic: "verifiable_task_handoff"
dueDate: null
created: "2026-10-16T06:53:44Z"
modified: "2026-10-16T06:53:44Z"
completedAt: null
labels: ["scripts", "audit"]
order: "a5"
---

# Task 5: Gate 4 epic audit

Epic: [verifiable_task_handoff](../epic/verifiable_task_handoff/verifiable_task_handoff.en.md)

## Requirement Analysis

Audit every `done` task of an epic branch at Gate 4 and disclose every change to a grader.
Authority: source spec section 11.

### audit_epic.py (new)

```bash
python3 skills/dev-implementation/resources/scripts/audit_epic.py --epic-dir <epic_dir> --base <base_ref>
```

Root is `git rev-parse --show-toplevel`. `<base_ref>` must resolve with
`git rev-parse --verify <base_ref>^{commit}`; otherwise exit 2 naming it. The commits examined are
`git rev-list --reverse <base>..HEAD`. A **task commit** is a commit that changed a file under
`.devtool/epic/<epic_dir>/evidence/`.

The report prints these sections as `### <name>` headings, each with its items or `None`, then
`Result: PASS` or `Result: FAIL`. Exit 0 when nothing fails, 1 otherwise.

| Section | Content | Fails |
|---|---|---|
| Evidence | For every task mirror whose `status` is `done` and whose HEAD version has `## Verification`: the evidence file exists at HEAD and every recorded row is `PASS` (`missing evidence` or `row V3 not PASS`). Its task commit is the last commit in `<base>..HEAD` that changed that evidence file; `git diff <c>^ <c> -- . ':(exclude).devtool'` piped into `git patch-id --stable` is compared with the `verify` run's `patch_id`, and a difference prints `patch changed after verify` | missing evidence, or a row not PASS |
| Legacy tasks | `done` tasks whose HEAD mirror has no `## Verification`, labelled `legacy — no evidence` | no |
| Protected paths | Paths changed in each commit (`git diff-tree --no-commit-id --name-only -r <c>`) that are protected — the HLD's `Protected paths:` entries, or the `program_of` any row of any task — listed with the commit. A change outside `.devtool/` that no task's Allowed files names exactly is `unauthorised` | an unauthorised change outside `.devtool/` |
| Grader amendments | For each task mirror, the Verification table, Definition of Done, Allowed files and `Covers:` line at HEAD compared with the commit that created the mirror (`git log --diff-filter=A --format=%H -- <mirror>`, oldest), shown as a unified diff with the titles of the commits that changed the mirror since. Scenario identifiers added to or removed from `bdd_scenarios.en.md` between `<base>` and HEAD | no |
| Commits outside tasks | Commits in `<base>..HEAD` that are not task commits and change a file outside `.devtool/`, as `<short sha> <title>` | no |
| Gate 5 items | Every Definition of Done bullet ending `(Gate 5)`, with its task | no |

Use `task_contract.py` for every parse. The report is printed only; it is never written to a file.

### Also

`scripts/verify.sh`, section 11: add
`python3 -m unittest skills/dev-implementation/resources/scripts/test_audit_epic.py || FAILED=1`.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/audit_epic.py` (new)
- `skills/dev-implementation/resources/scripts/test_audit_epic.py` (new)
- `skills/dev-implementation/resources/scripts/task_contract.py`
- `scripts/verify.sh`

Read-only context:
- `skills/dev-implementation/resources/scripts/run_task_checks.py` — how `patch_id` is computed
- `.devtool/epic/verifiable_task_handoff/2026-10-16-verifiable-task-handoff-design.en.md` — section 11

## Design Rationale

- `patch-id` survives the rebase onto `develop` that `dev-implementation` performs after every task;
  `tree` does not.
- Disclosures never fail the audit; the developer judges them at Gate 5.
- Tests build an epic branch in a throwaway repository, record evidence with the real recorder,
  commit, then move or rebase the base branch as each scenario needs.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `audit_epic.py`; parsing helpers in `task_contract.py`.
- **Downstream callers**: `dev-implementation` Phase 4 (Task 7) and `run_external_review.py` (Task 6).
- **Cross-platform bridges**: none.
- **Target test coverage threshold**: every section produced with and without items.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: VTH-HP-05, VTH-HP-10, VTH-ST-08, VTH-ST-09, VTH-AR-01, VTH-FR-03

Test methods `test_vth_hp_05_…`, `test_vth_hp_10_…`, `test_vth_st_08_…`, `test_vth_st_09_…`,
`test_vth_ar_01_…` and `test_vth_fr_03_…` go in `test_audit_epic.py`.

```gherkin
Scenario: [VTH-HP-05] [Tier C - Integration] A clean epic passes the audit
  Given an epic branch whose done tasks each committed passing evidence with their code
  When audit_epic.py runs against the base branch
  Then every task's commit patch-id equals its verify patch_id
  And the audit exits 0

Scenario: [VTH-HP-10] [Tier C - Integration] Disclosures are listed without failing the audit
  Given a task whose Verification row was amended after the task file was created
  And a commit on the epic branch that belongs to no task and touches a file outside .devtool
  And a Definition of Done bullet marked "(Gate 5)"
  And a done task whose task commit has no Verification section
  When audit_epic.py runs
  Then the report lists the amendment with its commit title, the commit outside tasks, the Gate 5 item and the legacy task
  And the audit exits 0

Scenario: [VTH-ST-08] [Tier C - Integration] A done status written by hand fails the audit
  Given a task with a Verification section whose status was set to done by editing its frontmatter
  And no evidence file for it on the epic branch
  When audit_epic.py runs
  Then it exits 1 naming the task's missing evidence

Scenario: [VTH-ST-09] [Tier C - Integration] Protected changes outside tasks fail outside .devtool and are disclosed inside it
  Given a commit outside any task that changes "scripts/verify.sh", a protected path
  And a doc-sync commit that adds a scenario identifier to bdd_scenarios.en.md
  When audit_epic.py runs
  Then it exits 1 naming the scripts/verify.sh change
  And it lists the added identifier as a disclosure

Scenario: [VTH-AR-01] [Tier C - Integration] A moved base branch changes trees but not the verdict
  Given an epic branch rebased onto a base branch that moved after its tasks were verified
  When the rebase had no conflicts and audit_epic.py runs
  Then every patch-id still matches and the audit exits 0
  When a conflict resolution changed one task's patch and audit_epic.py runs
  Then that task is listed as "patch changed after verify" and the audit still exits 0

Scenario: [VTH-FR-03] [Tier C - Integration] An unknown base reference is a usage error
  Given a base reference that git cannot resolve
  When audit_epic.py runs
  Then it exits 2 naming the reference
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_audit_epic.py` | exit 1; contains "ModuleNotFoundError" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_audit_epic.py` | exit 0; contains "OK" | — |
| V3 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
| V4 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_5.xml skills/dev-implementation/resources/scripts/test_audit_epic.py` | exit 0; results build/test-results/task_5.xml | — |
| V5 | TIER-C | `python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py tests --scenarios .devtool/epic/verifiable_task_handoff/bdd_scenarios.en.md --roots skills/dev-implementation/resources/scripts/ --results build/test-results/task_5.xml --ids VTH-HP-05 VTH-HP-10 VTH-ST-08 VTH-ST-09 VTH-AR-01 VTH-FR-03` | exit 0; contains "Result: 6/6 covered — PASS" | — |
| V6 | TIER-C | `python3 skills/dev-implementation/resources/scripts/audit_epic.py --epic-dir verifiable_task_handoff --base main` | exit 0; contains "Result: PASS" | — |

## Definition of Done

- `audit_epic.py` produces all six sections, fails only on missing evidence, rows not PASS and unauthorised protected changes outside `.devtool/`, and the six covered scenarios pass (V2, V4, V5).
- The audit of this epic's own branch, Tasks 1 to 4, passes (V6).
- `scripts/verify.sh` passes with the new test file wired in (V3).

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- V6 fails on a real finding in Tasks 1 to 4; report the audit output instead of changing the audit.

## Decisions Already Made

- An unauthorised protected change fails only outside `.devtool/`; inside it, it is disclosed.
- A protected change is authorised when any task's Allowed files names the path exactly.
- Scenario identifier changes are compared between `<base>` and HEAD.
- Test fixtures use identifiers with the `DEMO-` prefix; only test method names carry `VTH-` identifiers.

## Dependencies & Blockers

- Blocked by [Task 1](task_1_verification_table_parser_and_evidence_recorder.md), [Task 3](task_3_design_time_task_contract_check.md)

## References & Rollback

- Source spec section 11.
- Rollback: revert this task's commit; nothing in Phase 2 depends on the audit.
