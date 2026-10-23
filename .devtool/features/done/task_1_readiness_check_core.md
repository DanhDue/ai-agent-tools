---
id: "task_1_readiness_check_core"
status: "done"
priority: "high"
assignee: null
epic: "principal_review"
dueDate: null
created: "2026-10-22T09:10:00Z"
modified: "2026-10-23T09:22:42Z"
completedAt: "2026-10-23T09:22:42Z"
labels: ["readiness", "preflight", "cli"]
order: "a1"
---

# Task 1: Readiness Check Core

Epic: [principal_review](../epic/principal_review/principal_review.en.md)

## Requirement Analysis

Create `check_epic_readiness.py`, the single command that later replaces the four packaging
preflight commands and gates every Principal Review round. This task builds the frame and the
structural checks:
- the `Context`, the `Finding` record, the ordered `CHECKS` table, the report and the exit codes;
- R1 (the existing preflight scripts and the document linter);
- R2 (task mirror parity);
- R3 (scenario parity between task copies and the canonical BDD file);
- R4 (tier tags);
- R7 and R7b (metadata).

R5, R6 and R8 get their names in `CHECKS` now, and Task 2 fills them. The test module also
provides the reusable fixture builder that Task 3 imports.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py` (new)
- `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/compute_execution_order.py` — prints `Scanned <n> task_*.md files; <m> matched epic '<slug>'; …`
- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` — `scenario_ids()`, `SCENARIO_LINE`, `FENCE`, the `plan` mode
- `skills/dev-implementation/resources/scripts/check_task_contract.py` — `--design` mode, and a valid task fixture in `test_check_task_contract.py`
- `skills/dev-implementation/resources/scripts/task_contract.py` — `section()`, `parse_allowed_files()`, `parse_verification()`, `parse_integration_results()`, `git_run()`
- `skills/dev-implementation/resources/scripts/sync_task_status.py` — `TASK_STATUSES`
- `skills/doc_quality_check/resources/scripts/check_document.py` — `--require-toc`, `--require-bilingual`
- `skills/dev-lifecycle/SKILL.md` — the four preflight commands R1 folds together
- `.devtool/epic/principal_review/principal_review.en.md` — Module Contracts, `check_epic_readiness.py`

## Design Rationale

One script, many small check functions, one report: each check is a function of the `Context`
returning `Finding`s, so Task 2 adds checks without touching the frame. R1 calls the existing
scripts as subprocesses instead of importing their internals, so their exit codes keep exactly the
meaning the packaging procedure relies on today. Standard library only, like the other scripts.
Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/check_epic_readiness.py`: new `Finding`, new `Context`, new `CHECKS`, new `load_context()`, new `run_checks()`, new `render_report()`, new `main()`
- **Downstream Callers**: Task 3 (`run_external_review.py --kind principal` precondition), Task 5 (packaging procedure step 1).
- **Cross-Platform Bridges**: none.
- **Target Test Coverage Threshold**: every check function and every exit code has a named test.

### BDD SCENARIOS

Covers: PRV-HP-01, PRV-EC-02, PRV-EC-04, PRV-EC-05, PRV-FR-02

```gherkin
Scenario: [PRV-HP-01] [Tier C - Integration] A ready fixture epic passes every check
  Given a throwaway repository with epic "demo_epic" whose 2 tasks have epic "demo-epic", mirrors in .devtool/features/, canonical Gherkin copies, existing symbols, covered TIER-C paths and an approved spec
  When check_epic_readiness.py demo_epic runs
  Then the first line is "Epic: demo_epic (demo-epic), 2 tasks"
  And the output has the lines "R1 PASS" through "R7 PASS" in order, then "R8 SKIP"
  And the last line is "Result: 0 FAIL, 0 WARN — PASS"
  And the exit code is 0

Scenario: [PRV-EC-02] [Tier C - Integration] Tier drift fails R3 and a Tier B tag fails R4
  Given the PRV-HP-01 epic whose bdd_scenarios.en.md tags DEMO-HP-01 "[Tier B - Unit]" while task_1 copies it as "[Tier A - Unit]"
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R3 FAIL" containing "task_1" and "DEMO-HP-01"
  And a line starting "R4 FAIL" containing "DEMO-HP-01" and "Tier B - Unit"
  And the exit code is 1

Scenario: [PRV-EC-04] [Tier C - Integration] Mirror drift fails R2 and location-only link differences pass
  Given the PRV-HP-01 epic whose .devtool/features/task_1 mirror links "../epic/demo_epic/demo_epic.en.md" where the epic copy links "demo_epic.en.md"
  When check_epic_readiness.py demo_epic runs
  Then the output has the line "R2 PASS"
  When the mirror's Requirement Analysis gains the extra line "Stale sentence."
  And check_epic_readiness.py demo_epic runs again
  Then the output has a line starting "R2 FAIL" containing "task_1" and "Stale sentence."
  And the exit code is 1

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

Scenario: [PRV-FR-02] [Tier C - Integration] A failing preflight sub-check fails R1 by name
  Given the PRV-HP-01 epic whose bdd_scenarios.en.md adds DEMO-EC-09 covered by no task
  When check_epic_readiness.py demo_epic runs
  Then the output has a line starting "R1 FAIL" containing "check_bdd_traceability.py plan"
  And the exit code is 1
  When check_epic_readiness.py runs with a directory that does not exist
  Then the exit code is 2
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k ReadinessCoreTest` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k ReadinessCoreTest` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_1.xml skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` | exit 0; results build/test-results/task_1.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- The `build_ready_epic` fixture fails `check_task_contract.py --design` or `check_bdd_traceability.py plan`: fix the fixture; the existing checkers are never edited here.

## Decisions Already Made

- **Frozen contract** (HLD, Module Contracts):
  ```python
  @dataclass(frozen=True)
  class Finding:
      check: str     # "R1" ... "R8", "R5b", "R7b"
      severity: str  # "FAIL" or "WARN"
      message: str

  CHECKS: tuple[tuple[str, Callable[[Context], list[Finding]]], ...]  # R1..R8 in order

  def load_context(root: Path, epic_dir: str) -> Context
  def run_checks(ctx: Context, *, baseline: bool = False, row_timeout: int = 600) -> list[Finding]
  def render_report(ctx: Context, findings: list[Finding]) -> str
  def main(argv: list[str] | None = None) -> int
  ```
  `Context` is a frozen dataclass holding:
  - `root`, `epic_dir` and `epic_slug` (the `epic:` value shared by the epic directory's tasks);
  - `hld_text`;
  - `tasks: dict[Path, str]` (every `.devtool/epic/<epic_dir>/task_*.md`);
  - `results: list[str]` (from `task_contract.parse_integration_results`);
  - `roots: list[str]` (the comma-separated `Integration test roots:` values);
  - `baseline: bool` and `row_timeout: int`.
- **CLI**: `check_epic_readiness.py <epic_dir> [--baseline] [--row-timeout 600]`. The root comes from `git rev-parse --show-toplevel` run in the current directory. Every subprocess runs with `cwd=root`.
- **Report**:
  - the first line is exactly `Epic: <epic_dir> (<epic_slug>), <N> tasks`;
  - then, in `CHECKS` order: `<check> PASS` for each of R1–R7 with no FAIL finding, and each finding as `<check> <severity> <message>`. R5b WARN lines follow R5, and R7b WARN lines follow R7;
  - R8 prints `R8 SKIP` without `--baseline`;
  - the last line is exactly `Result: <f> FAIL, <w> WARN — PASS` or `… — FAIL`.
- **Exit codes**: 0 when no finding is FAIL, 1 otherwise, 2 when `.devtool/epic/<epic_dir>/` or `<epic_dir>.en.md` is missing (one line on stderr naming the path).
- **R1**: run with `sys.executable`, in this order, each failure being one finding `R1 FAIL <script name and mode>: <last non-empty output line>`:
  1. `compute_execution_order.py <epic_slug>`. Its exit code must be 0, and the `<m>` in `<m> matched` must equal `len(ctx.tasks)`; a mismatch is `R1 FAIL task mirror count: <m> matched, <N> in the epic directory`.
  2. `check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks <the epic directory's task files>`.
  3. `check_task_contract.py --design --hld .devtool/epic/<epic_dir>/<epic_dir>.en.md --tasks <the same task files>`.
  4. `check_document.py --require-toc --require-bilingual` on every `*.en.md` and `*.vi.md` pair in the epic directory. Then `check_document.py --require-toc handoff.md` when it exists, then `check_document.py <task files>`. The linter path is `Path(__file__).resolve().parents[2] / "doc_quality_check/resources/scripts/check_document.py"`.
- **R2**:
  - for each task, the mirror is `.devtool/features/<name>` or else `.devtool/features/done/<name>`;
  - compare `mirror.replace(f"](../epic/{epic_dir}/", "](")` with the epic copy;
  - a missing mirror is `R2 FAIL <name>: no mirror in .devtool/features/`;
  - a difference is `R2 FAIL <name>: line <k>: <the epic copy's line>`, with `<k>` the first differing 1-based line.
- **R3**:
  - a block is a line matching `check_bdd_traceability.SCENARIO_LINE` inside a `gherkin` fence, plus the following lines up to the next scenario line, a blank line or the closing fence, each `rstrip()`-ed;
  - a task block whose identifier is in the canonical file but whose text differs is `R3 FAIL <task file>: <ID> differs from bdd_scenarios.en.md`;
  - different identifier sets between the `.en.md` and `.vi.md` BDD files give `R3 FAIL bdd_scenarios.vi.md: <ID> missing or extra`.
- **R4**: on every scenario line of `bdd_scenarios.en.md`, the bracketed tag right after the identifier must be exactly `Tier A - Unit` or `Tier C - Integration`. Otherwise the finding is `R4 FAIL <ID>: tier tag "<tag or none>"`.
- **R7** (FAIL):
  - Status starts with `Packaged` and there is no `handoff.md`;
  - `handoff.md` exists and Status starts with none of `Packaged`, `In Progress` or `Done`;
  - the handoff's `- **Design commit**: \`<value>\`` is neither `uncommitted` nor a commit for which `git merge-base --is-ancestor <value> HEAD` exits 0;
  - a task's `epic:` differs from `epic_slug`, or its `status` is not in `sync_task_status.TASK_STATUSES`.

  The Status is the first `- **Status**:` line of `<epic_dir>.en.md`.
- **R7b** (WARN): the `- **Status**:` line of the epic directory's `*-design.en.md` matches `re.compile(r"draft|awaiting|under .*review|bản nháp|chờ duyệt", re.I)`. The finding is `R7b WARN spec status: <the line's value>`.
- **R5, R6, R8 in this task**: `CHECKS` already lists `("R5", check_grounding)`, `("R6", check_gate4_coverage)` and `("R8", check_baseline)`. `check_grounding` and `check_gate4_coverage` return `[]` until Task 2. `check_baseline` returns `[]`; the report prints `R8 SKIP` whenever `baseline` is false.
- **Fixture builder** (new frozen contract for Task 3), in `test_check_epic_readiness.py`:
  ```python
  def build_ready_epic(root: Path) -> None
  ```
  It writes the PRV-HP-01 epic `demo_epic` (slug `demo-epic`, 2 tasks) into an existing Git repository at `root`, and commits nothing. Every task passes the real `check_task_contract.py --design`, every scenario is assigned, both document pairs pass the linter, the spec Status is `Approved (Gate 1)`, and the HLD Status is `Planned`.

## Definition of Done

- All five covered scenarios have a `test_prv_*` method in `ReadinessCoreTest` and pass in the JUnit report. (V2, V5)
- `build_ready_epic` produces an epic for which `check_epic_readiness.py` exits 0. (V2)
- Lint and strict type checking report zero issues on both new files. (V3, V4)

## Dependencies & Blockers

- Blocked by: none.
- Blocks [Task 2](task_2_readiness_grounding_and_baseline.md).

## References & Rollback

- [Epic HLD](../epic/principal_review/principal_review.en.md), Module Contracts.
- Spec: [2026-10-22-principal-review-design.en.md](../epic/principal_review/2026-10-22-principal-review-design.en.md), §5.1.
- **Rollback**: revert the commit; the script has no caller until Task 3.
