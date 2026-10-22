# Principal Review BDD Scenarios

## Table of Contents

- [Coverage Matrix](#coverage-matrix)
- [Use Case 1: Mechanical Readiness Check](#use-case-1-mechanical-readiness-check)
- [Use Case 2: Principal Review Round](#use-case-2-principal-review-round)
- [Use Case 3: Epic Status Sync Scope](#use-case-3-epic-status-sync-scope)
- [Use Case 4: Lifecycle Workflow](#use-case-4-lifecycle-workflow)

## Coverage Matrix

| Scenario ID | Dimension | Target Component | Description |
|---|---|---|---|
| `[PRV-HP-01]` | Happy Path | `check_epic_readiness.py` | A ready fixture epic passes every check |
| `[PRV-HP-02]` | Happy Path | `run_external_review.py` | A principal round is recorded in `principal_review.md` |
| `[PRV-HP-03]` | Happy Path | `run_external_review.py` | Findings with proposed edits become table rows and set the exit code |
| `[PRV-HP-04]` | Happy Path | `dev-lifecycle` | Packaging runs one readiness command and offers Principal Review Choice |
| `[PRV-HP-05]` | Happy Path | `sync_task_status.py` | `epic` updates the main checkout and the epic's own worktree |
| `[PRV-EC-01]` | Edge Case | `check_epic_readiness.py` | A symbol missing from its file fails R5 |
| `[PRV-EC-02]` | Edge Case | `check_epic_readiness.py` | Tier drift fails R3 and a Tier B tag fails R4 |
| `[PRV-EC-03]` | Edge Case | `check_epic_readiness.py` | A TIER-C test outside every Integration results command fails R6 |
| `[PRV-EC-04]` | Edge Case | `check_epic_readiness.py` | Mirror drift fails R2; location-only link differences pass |
| `[PRV-EC-05]` | Edge Case | `check_epic_readiness.py` | Packaged without a handoff fails R7; a draft spec warns R7b |
| `[PRV-EC-06]` | Edge Case | `check_epic_readiness.py` | A route found in no source file warns R5b without failing |
| `[PRV-EC-07]` | Edge Case | `handoff-template.md` | Read First lists `principal_review.md` |
| `[PRV-ST-01]` | State Transition | `run_external_review.py` | Decisions move `check --kind principal` from 1 to 0, independent of code rounds |
| `[PRV-ST-02]` | State Transition | `run_external_review.py` | `triage` reads the file `--kind` selects |
| `[PRV-ST-03]` | State Transition | `dev-lifecycle`, lifecycle docs | The loop returns to Package and Done re-packages after a round |
| `[PRV-ST-04]` | State Transition | `dev-implementation` | Gate 3 stops while a blocking principal finding is undecided |
| `[PRV-AR-01]` | Async / Race | `run_external_review.py` | A second round before the first is committed is refused; rounds number in order |
| `[PRV-FR-01]` | Failure & Resilience | `check_epic_readiness.py` | Baseline failures and timeouts warn and the other rows still run |
| `[PRV-FR-02]` | Failure & Resilience | `check_epic_readiness.py` | A failing preflight sub-check fails R1 by name |
| `[PRV-FR-03]` | Failure & Resilience | `run_external_review.py` | A readiness FAIL blocks the CLI and records nothing |
| `[PRV-FR-04]` | Failure & Resilience | `run_external_review.py` | `--kind principal --cli ollama` is rejected before any work |
| `[PRV-FR-05]` | Failure & Resilience | `sync_task_status.py` | Another epic's worktree stays byte-identical; `task` sync still mirrors everywhere |

## Use Case 1: Mechanical Readiness Check

### PRV-HP-01: A Ready Epic Passes

```gherkin
Scenario: [PRV-HP-01] [Tier C - Integration] A ready fixture epic passes every check
  Given a throwaway repository with epic "demo_epic" whose 2 tasks have epic "demo-epic", mirrors in .devtool/features/, canonical Gherkin copies, existing symbols, covered TIER-C paths and an approved spec
  When check_epic_readiness.py demo_epic runs
  Then the first line is "Epic: demo_epic (demo-epic), 2 tasks"
  And the output has the lines "R1 PASS" through "R7 PASS" in order, then "R8 SKIP"
  And the last line is "Result: 0 FAIL, 0 WARN — PASS"
  And the exit code is 0
```

### PRV-EC-01: Missing Symbol

```gherkin
Scenario: [PRV-EC-01] [Tier C - Integration] A symbol missing from its file fails R5
  Given the PRV-HP-01 epic whose task_2 lists "- `src/app.py`: `build_payload()`, new `render()`" under Target Files & Symbols
  And src/app.py exists without the text "build_payload"
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R5 FAIL" that contains "task_2", "build_payload" and "src/app.py"
  And no R5 line mentions "render"
  And the last line ends "— FAIL" and the exit code is 1
```

### PRV-EC-02: Tier Drift

```gherkin
Scenario: [PRV-EC-02] [Tier C - Integration] Tier drift fails R3 and a Tier B tag fails R4
  Given the PRV-HP-01 epic whose bdd_scenarios.en.md tags DEMO-HP-01 "[Tier B - Unit]" while task_1 copies it as "[Tier A - Unit]"
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R3 FAIL" containing "task_1" and "DEMO-HP-01"
  And a line starting "R4 FAIL" containing "DEMO-HP-01" and "Tier B - Unit"
  And the exit code is 1
```

### PRV-EC-03: Uncovered Gate 4 Path

```gherkin
Scenario: [PRV-EC-03] [Tier C - Integration] A TIER-C test outside every Integration results command fails R6
  Given the PRV-HP-01 epic whose task_2 TIER-C row runs "python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml tests/test_extra.py"
  And the HLD's only Integration results command names "tests/test_core.py"
  And "tests/" is an Integration test roots directory
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R6 FAIL" containing "task_2" and "tests/test_extra.py"
  And the exit code is 1
```

### PRV-EC-04: Mirror Drift

```gherkin
Scenario: [PRV-EC-04] [Tier C - Integration] Mirror drift fails R2 and location-only link differences pass
  Given the PRV-HP-01 epic whose .devtool/features/task_1 mirror links "../epic/demo_epic/demo_epic.en.md" where the epic copy links "demo_epic.en.md"
  When check_epic_readiness.py demo_epic runs
  Then the output has the line "R2 PASS"
  When the mirror's Requirement Analysis gains the extra line "Stale sentence."
  And check_epic_readiness.py demo_epic runs again
  Then the output has a line starting "R2 FAIL" containing "task_1" and "Stale sentence."
  And the exit code is 1
```

### PRV-EC-05: Metadata

```gherkin
Scenario: [PRV-EC-05] [Tier C - Integration] Packaged without a handoff fails R7 and a draft spec warns R7b
  Given the PRV-HP-01 epic whose HLD Status is "Packaged" and whose directory has no handoff.md
  And whose spec Status is "Draft, awaiting Gate 1 review"
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R7 FAIL" containing "handoff.md"
  And a line starting "R7b WARN" containing "Draft, awaiting Gate 1 review"
  And the exit code is 1
  When handoff.md is added with "- **Design commit**: `uncommitted`" and the spec Status stays a draft
  And check_epic_readiness.py demo_epic runs again
  Then the output has the line "R7 PASS" and the exit code is 0
```

### PRV-EC-06: Unknown Route

```gherkin
Scenario: [PRV-EC-06] [Tier C - Integration] A route found in no source file warns R5b without failing
  Given the PRV-HP-01 epic whose task_1 names "/api/tts/ocr-upload" and whose only tracked source names "/api/studio/extract/start"
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R5b WARN" containing "/api/tts/ocr-upload"
  And no line mentions "/api/studio/extract/start"
  And the last line is "Result: 0 FAIL, 1 WARN — PASS" and the exit code is 0
```

### PRV-FR-01: Baseline Failures

```gherkin
Scenario: [PRV-FR-01] [Tier C - Integration] Baseline failures and timeouts warn and the other rows still run
  Given the PRV-HP-01 epic in a clean tree whose task_1 has rows V2 GREEN "python3 -c 'raise SystemExit(1)'" expecting "exit 0", V3 TIER-B "sleep 5" expecting "exit 0", and V4 GREEN "python3 -c 'print(1)'" expecting "exit 0"
  And task_2 has a GREEN row whose command names a path marked (new)
  When check_epic_readiness.py demo_epic --baseline --row-timeout 2 runs
  Then the output has a line starting "R8 WARN" containing "task_1:V2"
  And a line starting "R8 WARN" containing "task_1:V3" and "timeout"
  And no R8 line mentions "task_1:V4" or task_2's row
  And the exit code is 0
  When the tree has an uncommitted change and the same command runs
  Then the output has the line "R8 WARN baseline skipped: dirty tree"
```

### PRV-FR-02: Failing Preflight Sub-check

```gherkin
Scenario: [PRV-FR-02] [Tier C - Integration] A failing preflight sub-check fails R1 by name
  Given the PRV-HP-01 epic whose bdd_scenarios.en.md adds DEMO-EC-09 covered by no task
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R1 FAIL" containing "check_bdd_traceability.py plan"
  And the exit code is 1
  When check_epic_readiness.py runs with a directory that does not exist
  Then the exit code is 2
```

## Use Case 2: Principal Review Round

### PRV-HP-02: A Principal Round Is Recorded

```gherkin
Scenario: [PRV-HP-02] [Tier C - Integration] A principal round is recorded in principal_review.md
  Given the PRV-HP-01 epic committed in a clean tree and a fake "claude" on PATH that saves its stdin and prints "Verdict: PASS"
  When run_external_review.py run --kind principal --epic-dir demo_epic --base main --cli claude runs
  Then the saved prompt contains "Principal Reviewer", "Result: 0 FAIL, 0 WARN — PASS", ".devtool/epic/demo_epic/demo_epic.en.md" and the SHA of main
  And the saved prompt does not contain "audit_epic.py"
  And principal_review.md starts with "# Principal Review: demo_epic" and has "## Round 1" with "- **Kind**: principal", "- **CLI**: claude", "- **Status**: completed" and "- **Verdict**: PASS"
  And review_results.md does not exist
  And the exit code is 0
```

### PRV-HP-03: Findings With Proposed Edits

```gherkin
Scenario: [PRV-HP-03] [Tier C - Integration] Findings with proposed edits become table rows and set the exit code
  Given a fake "codex" that prints "Verdict: CHANGES REQUIRED" and "[Important] task_2:Decisions Already Made — persist_track returns a dict. Proposed: keep TrackPersistResult."
  When run --kind principal --cli codex runs
  Then principal_review.md has a findings row with "Important", "task_2:Decisions Already Made" and "Proposed: keep TrackPersistResult."
  And the round's "- **Verdict**: CHANGES REQUIRED"
  And the exit code is 1
```

### PRV-ST-01: Decisions Gate Check

```gherkin
Scenario: [PRV-ST-01] [Tier C - Integration] Decisions move check --kind principal from 1 to 0, independent of code rounds
  Given principal_review.md whose latest completed round has one Important finding with an empty Decision cell
  And review_results.md whose latest round has no finding
  When run_external_review.py check --kind principal --epic-dir demo_epic runs
  Then it prints "undecided: #1 Important" and exits 1
  And check --epic-dir demo_epic without --kind exits 0
  When the Decision cell becomes "fixed in abc1234"
  Then check --kind principal exits 0
```

### PRV-ST-02: Triage Reads the Selected File

```gherkin
Scenario: [PRV-ST-02] [Tier C - Integration] triage reads the file --kind selects
  Given principal_review.md with 2 rounds and review_results.md with 1 round
  When run_external_review.py triage --kind principal --epic-dir demo_epic runs
  Then the output starts "# Review Triage: demo_epic, Round 2"
  And triage without --kind prints "Round 1"
  When principal_review.md does not exist
  Then triage --kind principal prints "no review round recorded for demo_epic" and exits 2
```

### PRV-AR-01: Rounds in Order

```gherkin
Scenario: [PRV-AR-01] [Tier C - Integration] A second round before the first is committed is refused and rounds number in order
  Given a completed principal round 1 written but not committed
  When run --kind principal runs again
  Then it prints "commit or stash your changes before a review" and exits 2
  And the fake CLI is called exactly once in total
  When round 1 is committed and run --kind principal runs again
  Then principal_review.md has "## Round 1" followed by "## Round 2"
```

### PRV-FR-03: Readiness Blocks the CLI

```gherkin
Scenario: [PRV-FR-03] [Tier C - Integration] A readiness FAIL blocks the CLI and records nothing
  Given the PRV-EC-01 epic committed in a clean tree and a fake "claude" that records every call
  When run --kind principal --cli claude runs
  Then stderr shows "WAS NOT INVOKED" and "check_epic_readiness.py"
  And stderr shows the line containing "R5 FAIL"
  And the fake CLI was never called
  And principal_review.md does not exist and the exit code is 2
```

### PRV-FR-04: Ollama Rejected

```gherkin
Scenario: [PRV-FR-04] [Tier C - Integration] --kind principal --cli ollama is rejected before any work
  Given a throwaway epic repository with an uncommitted change
  When run --kind principal --cli ollama --model m runs
  Then stderr shows "--kind principal supports --cli claude or codex"
  And stderr never shows "[Pre-check]"
  And the exit code is 2 and no principal_review.md exists
```

## Use Case 3: Epic Status Sync Scope

### PRV-HP-05: Own Worktree Updated

```gherkin
Scenario: [PRV-HP-05] [Tier C - Integration] epic updates the main checkout and the epic's own worktree
  Given a throwaway repository with epic "demo_epic" (slug "demo-epic") and a worktree on branch "epic/demo-epic"
  When sync_task_status.py epic demo_epic Packaged runs in the main checkout
  Then demo_epic.en.md and demo_epic.vi.md read "Packaged" in both checkouts
```

### PRV-FR-05: Other Epics Untouched

```gherkin
Scenario: [PRV-FR-05] [Tier C - Integration] Another epic's worktree stays byte-identical and task sync still mirrors everywhere
  Given the PRV-HP-05 repository plus a worktree on branch "epic/other-epic" that also contains .devtool/epic/demo_epic/
  When sync_task_status.py epic demo_epic Packaged runs in the main checkout
  Then git status in the "epic/other-epic" worktree is empty
  When sync_task_status.py task task_1_demo in-progress runs
  Then task_1_demo reads "in-progress" in all three checkouts
```

## Use Case 4: Lifecycle Workflow

### PRV-HP-04: Packaging Offers the Choice

```gherkin
Scenario: [PRV-HP-04] [Tier C - Integration] Packaging runs one readiness command and offers Principal Review Choice
  Given skills/dev-lifecycle/SKILL.md and skills/dev-lifecycle/references/principal-review.md
  Then the skill contains "check_epic_readiness.py <epic_dir>", "Principal Review Choice" and "references/principal-review.md"
  And the skill no longer contains "check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks"
  And the skill has at most 2500 words and keeps every pinned dev-lifecycle token
  And the reference contains "1. **Done**", "2. **Principal Review**", "Claude CLI", "Codex CLI", "Never choose for the developer" and "strongly recommended"
```

### PRV-EC-07: Handoff Read First

```gherkin
Scenario: [PRV-EC-07] [Tier C - Integration] Read First lists principal_review.md
  Given skills/dev-lifecycle/references/handoff-template.md
  Then its Read First section contains ".devtool/epic/<epic_dir>/principal_review.md, when present"
  And it keeps "`git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>`" unchanged
```

### PRV-ST-03: The Loop Returns to Package

```gherkin
Scenario: [PRV-ST-03] [Tier C - Integration] The loop returns to Package and Done re-packages after a round
  Given docs/lifecycles.en.md, docs/lifecycles.vi.md and skills/dev-lifecycle/references/principal-review.md
  Then both documents contain 'PKG --> PRC', 'PRC -->|"2. Principal Review"| PR' and 'PR -->|"revised and re-packaged"| PKG'
  And neither document has an edge from PR to S3 or to G3
  And the reference contains "Record Principal Review round <n>", "Revise epic after Principal Review round <n>" and "Package epic for handoff"
  And the reference states that Done runs "check --kind principal" and re-packages when the last commit touching the epic directory is not the Package commit
```

### PRV-ST-04: Gate 3 Stops on Undecided Findings

```gherkin
Scenario: [PRV-ST-04] [Tier C - Integration] Gate 3 stops while a blocking principal finding is undecided
  Given skills/dev-implementation/SKILL.md
  Then Entry-Point Detection contains "run_external_review.py check --kind principal --epic-dir <epic_dir>"
  And Phase 1 step 3 and Resume Gate 3 both mention "Principal Review" with "not run", "round <n>: PASS" and "round <n>: decided"
  And the skill has at most 4500 words
```
