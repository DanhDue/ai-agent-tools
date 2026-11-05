# BDD Test Scenarios: Task Contract and Authoring Ergonomics

## Table of Contents

- [Dimension 1: Happy Paths](#dimension-1-happy-paths)
- [Dimension 2: Edge Cases and Boundaries](#dimension-2-edge-cases-and-boundaries)
- [Dimension 3: State Transitions](#dimension-3-state-transitions)
- [Dimension 4: Async and Concurrency](#dimension-4-async-and-concurrency)
- [Dimension 5: Failures and Resilience](#dimension-5-failures-and-resilience)

## Dimension 1: Happy Paths

```gherkin
Scenario: [TCAE-HP-01] [Tier C - Integration] Evidence files declaration passes design contract and Done-Gate verification
  Given a task declaring ".devtool/epic/sample_epic/evidence/baseline.txt (new)" under "Evidence files:" in "## Files"
  And a Verification row referencing ".devtool/epic/sample_epic/evidence/baseline.txt"
  When check_task_contract.py runs with "--design"
  Then it exits 0 with 0 problems and grounds the new evidence path across the epic
  And when run_task_checks.py verify executes the row that writes ".devtool/epic/sample_epic/evidence/baseline.txt"
  Then evaluate_done_gate confirms the evidence file exists on disk and passes all Done-Gate conditions

Scenario: [TCAE-HP-02] [Tier C - Integration] Single-source task rendering injects verbatim BDD, embeds code, and writes mirror
  Given a single-source task ".devtool/epic/sample_epic/task_01_setup.md" with "Covers: TCAE-HP-01" and a "<!-- @@FILE:src/helper.py@@ -->" directive
  And ".devtool/epic/sample_epic/bdd_scenarios.en.md" defining scenario "[TCAE-HP-01]"
  When "sync_task_status.py render sample_epic" executes
  Then ".devtool/epic/sample_epic/task_01_setup.md" contains the exact verbatim Gherkin block for "[TCAE-HP-01]" and the exact contents of "src/helper.py"
  And ".devtool/features/task_01_setup.md" is generated with relative links rewritten to "../epic/sample_epic/"
  And "check_task_contract.py --design" exits 0 with zero R2 or R3 findings

Scenario: [TCAE-HP-03] [Tier C - Integration] Zero-setup d3nexus CLI execution inside Verification rows
  Given a task Verification row invoking "d3nexus check-doc --require-toc .devtool/epic/sample_epic/sample_epic.en.md"
  When "run_task_checks.py verify" executes the task in a temporary git repository without pre-configured shell exports
  Then "run_task_checks.py" automatically injects "D3NEXUS_KIT" and prepends "<kit_root>/bin" to "PATH"
  And "d3nexus check-doc" dispatches to "check_document.py" and exits 0

Scenario: [TCAE-HP-04] [Tier A - Unit] Verification row grammar with escaped pipes, env assignments, and implicit protected path provenance
  Given a Verification row command using "env MODE=strict python3 scripts/tool.py \| grep -c ok"
  When "check_task_contract.py --design" evaluates the task
  Then "task_contract.py" unescapes "\|" to "|" in the parsed command without raising a contract problem
  And "check_task_contract.py" reports "scripts/tool.py (task_01:V1)" in the "Implicit protected paths:" line
```

## Dimension 2: Edge Cases and Boundaries

```gherkin
Scenario: [TCAE-EC-01] [Tier A - Unit] Task without Evidence files or Covers line remains backward-compatible
  Given a legacy task file that omits the "Evidence files:" subsection and omits the "Covers:" line
  When "sync_task_status.py render" and "check_task_contract.py --design" run on the epic
  Then "sync_task_status.py render" generates the ".devtool/features/" mirror without modifying the task's BDD section
  And "check_task_contract.py --design" exits 0 with 0 problems

Scenario: [TCAE-EC-02] [Tier A - Unit] Embedded file containing triple backticks promotes outer fence to four backticks
  Given a source file "docs/snippet.md" containing a fenced code block delimited by three backticks
  And a task containing "<!-- @@FILE:docs/snippet.md@@ -->" immediately above a three-backtick code fence
  When "sync_task_status.py render sample_epic" executes
  Then the rendered code block in both the epic task and the ".devtool/features/" mirror uses a four-backtick outer fence

Scenario: [TCAE-EC-03] [Tier A - Unit] Search patterns containing slashes in grep, rg, sed, and awk are not flagged as missing paths
  Given a Verification row command "grep -E 'foo/bar/baz' README.md" where "foo/bar/baz" is not a file on disk
  When "check_task_contract.py --design" inspects the command tokens
  Then "command_paths()" excludes the search pattern "foo/bar/baz" from path existence checks
  And "check_task_contract.py" exits 0 without reporting "foo/bar/baz does not exist"
```

## Dimension 3: State Transitions

```gherkin
Scenario: [TCAE-ST-01] [Tier A - Unit] Rendering cleans up orphan mirrors and preserves done board location
  Given ".devtool/features/task_99_obsolete.md" with frontmatter "epic: sample-epic" whose source file was deleted from ".devtool/epic/sample_epic/"
  And ".devtool/epic/sample_epic/task_01_done.md" with frontmatter "status: \"done\""
  When "sync_task_status.py render sample_epic" executes
  Then ".devtool/features/task_99_obsolete.md" is removed from disk
  And the mirror for "task_01_done.md" is written at ".devtool/features/done/task_01_done.md"

Scenario: [TCAE-ST-02] [Tier C - Integration] Done Gate transitions from FAIL to PASS once declared Evidence file is written
  Given a task declaring ".devtool/epic/sample_epic/evidence/summary.json (new)" under "Evidence files:"
  When "evaluate_done_gate" runs before ".devtool/epic/sample_epic/evidence/summary.json" is created on disk
  Then "evaluate_done_gate" returns a condition failure naming ".devtool/epic/sample_epic/evidence/summary.json"
  And when the verification run writes non-empty JSON to ".devtool/epic/sample_epic/evidence/summary.json"
  Then "evaluate_done_gate" returns an empty problem list
```

## Dimension 4: Async and Concurrency

```gherkin
Scenario: [TCAE-AR-01] [Tier A - Unit] Isolated subprocess environment injection across concurrent row executions
  Given two concurrent invocations of "run_task_checks.py" running in separate temporary git worktrees
  When each invocation executes a Verification row printing "$D3NEXUS_KIT" and "$(which d3nexus)"
  Then both subprocesses resolve the exact kit root path without mutating "os.environ" of the parent Python process

Scenario: [TCAE-AR-02] [Tier C - Integration] Deterministic idempotent re-rendering across repeated render calls
  Given an epic directory with multiple tasks covering multiple scenarios and file embeds
  When "sync_task_status.py render sample_epic" is executed twice in succession without intermediate edits
  Then the second run produces byte-for-byte identical files in ".devtool/epic/sample_epic/" and ".devtool/features/"
```

## Dimension 5: Failures and Resilience

```gherkin
Scenario: [TCAE-FR-01] [Tier A - Unit] Reject invalid Evidence files path outside epic evidence directory or with path traversal
  Given a task listing ".devtool/epic/sample_epic/../secret.txt (new)" or "src/output.json (new)" under "Evidence files:"
  When "check_task_contract.py --design" evaluates the task
  Then it exits 1 and reports that every "Evidence files:" entry must reside under ".devtool/epic/<epic_dir>/evidence/" without ".." segments

Scenario: [TCAE-FR-02] [Tier A - Unit] Reject hardcoded user home or plugin cache paths and bare VAR=value in Verification rows
  Given a task with row V1 calling "/Users/alice/antigravity_homes/tess/.claude/plugins/cache/check_document.py"
  And row V2 calling "FOO=bar pytest tests/unit/test_sample.py::test_ok" without "env"
  When "check_task_contract.py --design" evaluates the task
  Then it exits 1 reporting a non-portable absolute path on V1 and an unprefixed inline environment assignment on V2

Scenario: [TCAE-FR-03] [Tier C - Integration] Render aborts cleanly when Covers references an unknown scenario ID or missing embed file
  Given a task in ".devtool/epic/sample_epic/" whose "Covers:" line names "TCAE-HP-99" which is absent from "bdd_scenarios.en.md"
  When "sync_task_status.py render sample_epic" executes
  Then it exits 1 naming the unknown scenario ID "TCAE-HP-99" and leaves existing ".devtool/features/" files untouched
```

