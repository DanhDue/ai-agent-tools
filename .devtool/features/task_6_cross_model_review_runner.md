---
id: "task_6_cross_model_review_runner"
status: "todo"
priority: "high"
assignee: null
epic: "verifiable_task_handoff"
dueDate: null
created: "2026-10-16T06:53:44Z"
modified: "2026-10-16T06:53:44Z"
completedAt: null
labels: ["scripts", "review"]
order: "a6"
---

# Task 6: Cross-model review runner

Epic: [verifiable_task_handoff](../epic/verifiable_task_handoff/verifiable_task_handoff.en.md)

## Requirement Analysis

Let the developer have the finished epic reviewed by the Claude CLI or the Codex CLI, recording each
round in `review_results.md`, and block Phase 4 while a Critical or Important finding has no
decision. Authority: source spec section 12.

### run_external_review.py (new)

```bash
python3 skills/dev-implementation/resources/scripts/run_external_review.py run --epic-dir <epic_dir> \
  --base <base_ref> --cli claude|codex [--model <name>] [--timeout 1800]
python3 skills/dev-implementation/resources/scripts/run_external_review.py check --epic-dir <epic_dir>
```

`run`, in order:

1. `--cli` is required and only `claude` or `codex`; the script never picks one. Resolve it with
   `shutil.which`; if absent, exit 2 with `<cli> not found on PATH` and write nothing.
2. Require a clean tree (`git status --porcelain` prints nothing), else exit 2 with
   `commit or stash your changes before a review` and write nothing. Record `HEAD`.
3. Collect facts: run `audit_epic.py --epic-dir <epic_dir> --base <base_ref>`; run each command of the
   HLD's `Integration results:` lines, then `check_bdd_traceability.py tests` with `--scenarios`,
   the HLD's roots and `--results` over their report paths. Keep each output and exit code; failures
   are facts, not reasons to stop.
4. Build the prompt with `string.Template` from
   `skills/dev-implementation/references/external-review-prompt.md`, substituting `$sha`, `$base`,
   `$epic_dir`, `$artefacts` (one line per path: the spec pair, HLD, `bdd_scenarios.en.md`, every task
   mirror, the evidence directory), `$audit_output` and `$results_output`.
5. Run, with the prompt on stdin, `cwd=root`, the timeout, and stdout and stderr captured:
   - `claude`: `["claude", "-p", "--permission-mode", "plan"]`, plus `["--model", name]` when given;
   - `codex`: `["codex", "exec", "--sandbox", "read-only"]`, plus `["--model", name]` when given, then `"-"`.
6. Compare `HEAD` and `git status --porcelain` with step 2. Any difference gives the status
   `discarded: tree modified`, naming the changed paths; the script does not undo them.
7. Parse the output: the last line matching `^Verdict:\s*(PASS|CHANGES REQUIRED)\s*$`, and every line
   matching `^\s*[-*]?\s*\[(Critical|Important|Minor)\]\s*(\S.*?)\s+—\s+(.+)$` as severity, location,
   problem. A non-zero exit, a timeout or no Verdict line gives the status `no verdict`.
8. Append the round to `.devtool/epic/<epic_dir>/review_results.md`, creating the file with the title
   `# Cross-Model Review: <epic_dir>`. The round format is below.

Exit codes of `run`: 0 for a completed round without a Critical or Important finding; 1 for a
completed round with one; 2 for every other outcome. When the CLI ran, the round is recorded even
on exit 2.

The round format:

```markdown
## Round <n>

- **Date**: <UTC ISO-8601>
- **SHA**: <HEAD>
- **Base**: <base_ref>
- **CLI**: <claude|codex>
- **Model**: <name or default>
- **Status**: <completed | no verdict | discarded: tree modified (<paths>)>
- **Verdict**: <PASS | CHANGES REQUIRED | none>

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Critical | <location> | <problem> |  |

Raw output:

<the CLI output in a fence of backticks one longer than its longest backtick run, at least three, with the language tag text>
```

`|` in a cell is written as `\|`. Rounds are appended, never rewritten.

`check`: read `review_results.md`; a missing file exits 0. Take the latest round whose Status is
`completed`. Every Critical or Important finding whose Decision starts neither with `fixed in ` nor
with `dismissed: ` is listed as `undecided: #<n> <severity> <location>`, and `check` exits 1; else 0.

### external-review-prompt.md (new)

`skills/dev-implementation/references/external-review-prompt.md`: a Markdown template that tells the
reviewer it is read-only and must not modify any file; states `$sha`, `$base` and `$epic_dir`; lists
`$artefacts`; includes `$audit_output` and `$results_output` in fenced blocks; gives this checklist
verbatim:

- Each done task's evidence against its Verification table, and rows too weak for the Definition of
  Done item they back.
- Whether each identifier's test exercises its Gherkin scenario, or merely passes.
- Each audit disclosure — grader amendments, protected path changes, commits outside tasks — and
  whether it is justified.
- Whether the code respects the spec, the HLD and each task's Decisions Already Made.
- The `(Gate 5)` items, restated for the developer.

It ends with the required output: one line `Verdict: PASS` or `Verdict: CHANGES REQUIRED`, and one
line per finding, `[Critical|Important|Minor] <artefact>:<location> — <problem>`.

### Also

`scripts/verify.sh`, section 11: add
`python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py || FAILED=1`.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/run_external_review.py` (new)
- `skills/dev-implementation/resources/scripts/test_run_external_review.py` (new)
- `skills/dev-implementation/references/external-review-prompt.md` (new)
- `scripts/verify.sh`

Read-only context:
- `skills/dev-implementation/resources/scripts/audit_epic.py` — the audit run for facts
- `skills/dev-implementation/resources/scripts/task_contract.py` — `parse_integration_results`
- `.devtool/epic/verifiable_task_handoff/2026-10-16-verifiable-task-handoff-design.en.md` — section 12

## Design Rationale

- The script writes `review_results.md` from the CLI's output, so the reviewer needs no write access,
  and the tree comparison proves it used none.
- The developer picks the CLI because only they know which still has credits.
- Tests put fake `claude` and `codex` executables in a temporary directory placed first on `PATH`
  (with the directories of `git`, `bash` and `sys.executable` after it), so no test reaches a real CLI.
  The fakes save their stdin and print a canned review, exit 1, sleep past the timeout, or create a
  file in the repository.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: `run_external_review.py`; the new `references/` directory of
  `dev-implementation`.
- **Downstream callers**: `dev-implementation`'s Review Choice and Phase 4 (Task 7).
- **Cross-platform bridges**: none. The real CLIs send repository content to their provider only when
  the developer chooses option 2.
- **Target test coverage threshold**: every status and both CLIs exercised.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: VTH-HP-12, VTH-EC-07, VTH-ST-10, VTH-ST-11, VTH-FR-06, VTH-FR-07, VTH-FR-08

Test methods `test_vth_hp_12_…`, `test_vth_ec_07_…`, `test_vth_st_10_…`, `test_vth_st_11_…` and
`test_vth_fr_06_…` to `test_vth_fr_08_…` go in `test_run_external_review.py`.

```gherkin
Scenario: [VTH-HP-12] [Tier C - Integration] A clean review round is recorded
  Given a clean epic worktree whose tasks are all done
  And a fake "codex" on PATH that saves its stdin and prints "Verdict: PASS"
  When run_external_review.py run runs with --cli codex --model gpt-test
  Then it exits 0
  And the prompt it sent names the candidate SHA, the base, the evidence directory and the review checklist
  And review_results.md gains "## Round 1" with status completed, CLI codex, model gpt-test and verdict PASS

Scenario: [VTH-EC-07] [Tier C - Integration] Minor findings alone do not block
  Given a fake "claude" that prints "Verdict: CHANGES REQUIRED" and one "[Minor]" finding
  When run_external_review.py run runs with --cli claude
  Then it exits 0
  And the Minor finding is listed in the round's findings table

Scenario: [VTH-ST-10] [Tier C - Integration] Blocking findings hold Phase 4 until each has a decision
  Given a fake CLI that prints "Verdict: CHANGES REQUIRED" with one "[Critical]" and one "[Important]" finding
  When run_external_review.py run runs
  Then it exits 1 and the round lists both findings with an empty Decision
  When run_external_review.py check runs
  Then it exits 1 naming both findings
  When the Decision column reads "fixed in <sha>" for one and "dismissed: <reason>" for the other
  And run_external_review.py check runs
  Then it exits 0

Scenario: [VTH-ST-11] [Tier C - Integration] The latest completed round governs check
  Given review_results.md whose round 1 has an undecided Critical finding
  And a round 2, completed with no blocking finding
  And a round 3 recorded as "no verdict"
  When run_external_review.py check runs
  Then it exits 0 because round 2 is the latest completed round
  And rounds 1 and 3 are still present and unchanged

Scenario: [VTH-FR-06] [Tier C - Integration] A missing CLI or a dirty tree stops the review before it runs
  Given no "claude" on PATH
  When run_external_review.py run runs with --cli claude
  Then it exits 2 naming the missing CLI
  And review_results.md is not created
  Given instead an uncommitted change in the worktree
  When run_external_review.py run runs
  Then it exits 2 asking for a clean tree and writes nothing

Scenario: [VTH-FR-07] [Tier C - Integration] A reviewer that modifies the tree is discarded
  Given a fake CLI that creates a file in the repository and prints "Verdict: PASS"
  When run_external_review.py run runs
  Then it exits 2
  And the round is recorded as "discarded: tree modified", naming the created file

Scenario: [VTH-FR-08] [Tier C - Integration] A failing, silent or slow CLI records no verdict
  Given a fake CLI that exits 1 printing "credit balance is too low"
  When run_external_review.py run runs
  Then it exits 2 and records the round as "no verdict" with the CLI's output
  And the same holds for a CLI whose output has no Verdict line, and for one that outlives --timeout
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 1; contains "ModuleNotFoundError" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; contains "OK" | — |
| V3 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-implementation/references/external-review-prompt.md` | exit 0; contains "0 findings" | — |
| V4 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_6.xml skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; results build/test-results/task_6.xml | — |
| V6 | TIER-C | `python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py tests --scenarios .devtool/epic/verifiable_task_handoff/bdd_scenarios.en.md --roots skills/dev-implementation/resources/scripts/ --results build/test-results/task_6.xml --ids VTH-HP-12 VTH-EC-07 VTH-ST-10 VTH-ST-11 VTH-FR-06 VTH-FR-07 VTH-FR-08` | exit 0; contains "Result: 7/7 covered — PASS" | — |

## Definition of Done

- `run` and `check` behave as specified for both CLIs, and the seven covered scenarios pass with fake CLIs (V2, V5, V6).
- The prompt template passes the document check and carries the checklist and output format verbatim (V2, V3).
- `scripts/verify.sh` passes with the new test file wired in (V4).
- The two invocations were checked against `claude --help` and `codex exec --help` on the developer's machine (Gate 5).

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `claude --help` lacks `--print` or `--permission-mode`, or `codex exec --help` lacks `--sandbox` or
  reading the prompt from stdin.
- A test would call a real `claude` or `codex`.

## Decisions Already Made

- The developer always picks the CLI; there is no default and no automatic fallback.
- The reviewer is read-only; any change to the tree discards the round.
- Only Critical and Important findings block; Minor findings are listed.
- A `dismissed` decision is written only on the developer's explicit words; this script never writes a decision.
- Test fixtures use identifiers with the `DEMO-` prefix; only test method names carry `VTH-` identifiers.

## Dependencies & Blockers

- Blocked by [Task 2](task_2_test_result_reports_and_result_based_traceability.md), [Task 5](task_5_gate_4_epic_audit.md)

## References & Rollback

- Source spec section 12.
- Rollback: revert this task's commit; the Review Choice text of Task 7 would then name a missing script, so revert Task 7 with it.
