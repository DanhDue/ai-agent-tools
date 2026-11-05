---
id: "task_02_single_source_render_engine"
status: "todo"
priority: "high"
assignee: null
epic: "contract-and-authoring-ergonomics"
dueDate: null
created: "2026-11-06T01:50:00Z"
modified: "2026-11-06T01:50:00Z"
completedAt: null
labels: ["architecture", "authoring", "python"]
order: "a2"
---

# Task 02: Single-Source Task Render Engine and Shift-Left R2/R3 Checks

Epic: [contract_and_authoring_ergonomics](contract_and_authoring_ergonomics.en.md)

## Requirement Analysis

Resolve Observations #0009 and #0012:
1. Authors currently maintain two copies of every task file (`.devtool/epic/<epic_dir>/task_*.md` and `.devtool/features/task_*.md`), and manually copy Gherkin blocks from `bdd_scenarios.en.md` and code blocks from source files.
2. `check_epic_readiness.py` checks R2 (mirror parity) and R3 (verbatim BDD scenario parity), but `check_task_contract.py --design` does not run R2 or R3, so mismatches are discovered late.

This task adds `sync_task_status.py render <epic_dir> [--source-root <dir>]` and integrates R2/R3 checks into `check_task_contract.py --design`:
1. `render_epic_tasks(root: Path, epic_dir: str, source_root: Path | None = None)` in `sync_task_status.py`:
   - Reads `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` and injects the verbatim Gherkin scenario blocks matching each task's `Covers:` line into the task's `### BDD SCENARIOS` section.
   - Expands `<!-- @@FILE:<relative_path>@@ -->` directives by replacing the immediately following fenced code block with the contents of `<source_root>/<relative_path>`, promoting the outer fence to 4 backticks (` ```` `) when the embedded file contains triple backticks.
   - Generates `.devtool/features/task_*.md` (or `.devtool/features/done/task_*.md` when `status: "done"`), rewriting relative links `](< sibling >.md)` / `](./< sibling >.md)` to `](../epic/<epic_dir>/< sibling >.md)` and removing orphan mirrors for the same epic slug.
2. `check_task_contract.py --design` validates R3 (task Gherkin blocks match `bdd_scenarios.en.md` verbatim) and R2 (when a `.devtool/features/` mirror exists, its normalized content matches the epic task).

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/sync_task_status.py`
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- `skills/dev-implementation/resources/scripts/test_sync_task_status.py`
- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`

Read-only context:
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py` (reference for R2 and R3 extraction and normalization rules)
- `.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md` (HLD specification)

## Design Rationale

Applicable skills: `python-quality-check`, `test-driven-development`.
Placing `render` inside `sync_task_status.py` keeps all task-mirror and frontmatter synchronization logic in one stdlib-only module while eliminating manual dual-file editing.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/sync_task_status.py`: `main`, `board_location`, and new `render_epic_tasks`.
  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `check_task`, `check_hld`, and new `check_r2_r3_parity`.
- **Downstream Callers**: `skills/dev-implementation/resources/scripts/check_epic_readiness.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on `render_epic_tasks` and `check_r2_r3_parity`.

### BDD SCENARIOS

Covers: TCAE-HP-02, TCAE-EC-02, TCAE-ST-01

```gherkin
Scenario: [TCAE-HP-02] [Tier C - Integration] Single-source task rendering injects verbatim BDD, embeds code, and writes mirror
  Given a single-source task ".devtool/epic/sample_epic/task_01_setup.md" with "Covers: TCAE-HP-01" and a "<!-- @@FILE:src/helper.py@@ -->" directive
  And ".devtool/epic/sample_epic/bdd_scenarios.en.md" defining scenario "[TCAE-HP-01]"
  When "sync_task_status.py render sample_epic" executes
  Then ".devtool/epic/sample_epic/task_01_setup.md" contains the exact verbatim Gherkin block for "[TCAE-HP-01]" and the exact contents of "src/helper.py"
  And ".devtool/features/task_01_setup.md" is generated with relative links rewritten to "../epic/sample_epic/"
  And "check_task_contract.py --design" exits 0 with zero R2 or R3 findings

Scenario: [TCAE-EC-02] [Tier A - Unit] Embedded file containing triple backticks promotes outer fence to four backticks
  Given a source file "docs/snippet.md" containing a fenced code block delimited by three backticks
  And a task containing "<!-- @@FILE:docs/snippet.md@@ -->" immediately above a three-backtick code fence
  When "sync_task_status.py render sample_epic" executes
  Then the rendered code block in both the epic task and the ".devtool/features/" mirror uses a four-backtick outer fence

Scenario: [TCAE-ST-01] [Tier A - Unit] Rendering cleans up orphan mirrors and preserves done board location
  Given ".devtool/features/task_99_obsolete.md" with frontmatter "epic: sample-epic" whose source file was deleted from ".devtool/epic/sample_epic/"
  And ".devtool/epic/sample_epic/task_01_done.md" with frontmatter "status: \"done\""
  When "sync_task_status.py render sample_epic" executes
  Then ".devtool/features/task_99_obsolete.md" is removed from disk
  And the mirror for "task_01_done.md" is written at ".devtool/features/done/task_01_done.md"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_sync_task_status.py::test_TCAE_HP_02_render_single_source` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_sync_task_status.py skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/sync_task_status.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/test_sync_task_status.py skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent skills/dev-implementation/resources/scripts/sync_task_status.py skills/dev-implementation/resources/scripts/check_task_contract.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_sync_task_status.py skills/dev-implementation/resources/scripts/test_check_task_contract.py --junitxml=build/test-results/task_02.xml` | exit 0; results build/test-results/task_02.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- CLI interface in `skills/dev-implementation/resources/scripts/sync_task_status.py`: `sync_task_status.py render <epic_dir> [--source-root <path>]`.
- When rendering BDD scenarios: if a task has a `Covers:` line with scenario IDs, `render_epic_tasks` extracts the matching scenario blocks from `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` and replaces the ` ```gherkin ... ``` ` block under `### BDD SCENARIOS` (or inserts one immediately after the `Covers:` line). If any covered ID is missing from `bdd_scenarios.en.md`, `render_epic_tasks` raises ValueError / exits 1 without writing partial mirrors.
- When expanding `<!-- @@FILE:<rel_path>@@ -->`: `<rel_path>` must be relative without `..` segments; if the target file content contains ` ``` `, the outer code fence uses ` ```` ` (4 backticks).
- Mirror link rewriting: links targeting files inside `.devtool/epic/<epic_dir>/` (such as `](<epic_dir>.en.md)` or `](./task_01_foo.md)`) are rewritten to `](../epic/<epic_dir>/<target>)` in `.devtool/features/<task>.md`, matching `check_epic_readiness.py` R2 normalization `mirror_text.replace(f"](../epic/{epic_dir}/", "](") == epic_text`.

## Definition of Done

- `sync_task_status.py render <epic_dir>` injects verbatim Gherkin blocks, expands `@@FILE:...@@` fences, writes `.devtool/features/` mirrors, and removes orphan mirrors. (V2)
- `check_task_contract.py --design` checks R3 verbatim scenario parity and R2 mirror parity when mirrors exist. (V2)
- `ruff` and `mypy` pass with zero errors. (V3, V4)
- Automated tests for `TCAE-HP-02`, `TCAE-EC-02`, and `TCAE-ST-01` pass and write JUnit XML results. (V5)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 01](task_01_evidence_files_contract.md)

## References & Rollback

- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](2026-11-06-contract-and-authoring-ergonomics-design.en.md).
- Rollback: `git revert` the task commit to restore `sync_task_status.py` and `check_task_contract.py`.
