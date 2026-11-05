---
id: "task_03_package_revise_and_spec_errata"
status: "backlog"
priority: "high"
assignee: null
epic: "multi-epic-orchestration-and-governance"
dueDate: null
created: "2026-11-06T04:25:00Z"
modified: "2026-11-06T04:25:00Z"
completedAt: null
labels: ["packaging", "governance", "errata"]
order: "c3"
---

# Task 03: Packaged Epic Revision Workflow and HLD Spec Errata Contract

Epic: [multi_epic_orchestration_and_governance](multi_epic_orchestration_and_governance.en.md)

## Requirement Analysis

Resolve Observation #0015:
1. Post-packaging reviews and cross-epic alignments require revising a packaged epic and re-anchoring `Design commit` in `handoff.md`, yet previously there was no formal CLI tool to package or revise an epic while preserving custom `Open Notes` and recording a `## Revisions` history table.
2. When Stage 2 HLD design intentionally refines or amends a Stage 1 specification detail, there was no structured `## Spec Errata` (`[SE-NN]`) contract in the HLD validated for bilingual symmetry in `check_epic_readiness.py` (`R7`).

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/package_epic.py` (new)
- `skills/dev-implementation/resources/scripts/task_contract.py`
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
- `skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py` (new)

Read-only context:
- `skills/dev-lifecycle/references/handoff-template.md` (canonical handoff structure)
- `.devtool/epic/multi_epic_orchestration_and_governance/multi_epic_orchestration_and_governance.en.md` (HLD specification)

## Design Rationale

Applicable skills: `python-quality-check`, `test-driven-development`.
1. `parse_spec_errata(hld_text: str) -> list[tuple[str, str]]` in `task_contract.py` parses `- **[SE-01] <Section>**: <Description>` items from `## Spec Errata` (or `## Đính chính Đặc tả (Spec Errata)`). `check_epic_readiness.py` (`check_metadata()` `R7`) verifies that whenever either `.en.md` or `.vi.md` declares `Spec Errata`, both files declare the exact same `[SE-NN]` IDs in order, emitting `Finding("R7", "FAIL", ...)` on any mismatch.
2. `package_epic.py <epic_dir> [--revise --reason "<text>"]` runs `check_epic_readiness.py <epic_dir>` first, resolves `HEAD` SHA, and either writes a fresh `.devtool/epic/<epic_dir>/handoff.md` (when `--revise` is not set) or updates `Design commit`, the staleness `git log <sha>..<base>` command, and the `## Revisions` section while preserving `## Open Notes` verbatim (when `--revise --reason "<text>"` is passed).

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/package_epic.py`: new `render_initial_handoff`, new `revise_handoff_text`, new `package_epic`, and new `main`.
  - `skills/dev-implementation/resources/scripts/task_contract.py`: new `SPEC_ERRATA_ITEM_RE` and new `parse_spec_errata`.
  - `skills/dev-implementation/resources/scripts/check_epic_readiness.py`: `check_metadata`.
- **Downstream Callers**: `dev-designer` Stage 2 packaging and post-review revision workflow.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on `package_epic.py` and `parse_spec_errata`.

### BDD SCENARIOS

Covers: MEO-HP-03, MEO-ST-02, MEO-FR-02

```gherkin
  Scenario: [MEO-HP-03] [Tier C - Integration] package_epic.py packages an epic, validates bilingual Spec Errata, and re-anchors handoff.md on --revise
    Given an epic whose ".en.md" and ".vi.md" HLD files declare matching "## Spec Errata" entries "[SE-01]"
    When "package_epic.py <epic_dir>" runs on a passing readiness check
    Then it writes ".devtool/epic/<epic_dir>/handoff.md" anchored to the current HEAD commit
    And when a post-packaging revision commit is made and "package_epic.py <epic_dir> --revise --reason 'Clarify SE-01 contract'" runs
    Then "handoff.md" updates "Design commit" to the new HEAD SHA and appends the revision entry under "## Revisions"

  Scenario: [MEO-ST-02] [Tier A - Unit] package_epic.py --revise preserves custom Open Notes while updating Design commit, staleness git log SHA, and Revisions section
    Given an existing "handoff.md" with custom bullets under "## Open Notes" and "Design commit: `aaa1111`"
    When "package_epic.py <epic_dir> --revise --reason 'Align task 02 CLI flags'" runs at commit "bbb2222"
    Then "## Open Notes" retains all custom bullets verbatim
    And "Design commit" and the "git log" staleness check command are updated to "bbb2222"
    And "## Revisions" lists "`aaa1111` -> `bbb2222`" with reason "Align task 02 CLI flags"

  Scenario: [MEO-FR-02] [Tier A - Unit] R7 and package_epic.py fail when Spec Errata IDs mismatch between .en.md and .vi.md or --revise omits --reason
    Given an epic where ".en.md" declares "[SE-01]" and "[SE-02]" under "## Spec Errata" while ".vi.md" declares only "[SE-01]"
    When "check_epic_readiness.py" evaluates R7
    Then R7 fails reporting the asymmetric Spec Errata ID "[SE-02]"
    And when "package_epic.py <epic_dir> --revise" is invoked without "--reason"
    Then it exits with code 2 and reports that "--reason" is required for "--revise"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py::test_MEO_HP_03_package_and_revise_epic` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/package_epic.py skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent skills/dev-implementation/resources/scripts/package_epic.py skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/check_epic_readiness.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py --junitxml=build/test-results/task_03_package_revise.xml` | exit 0; results build/test-results/task_03_package_revise.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- In `skills/dev-implementation/resources/scripts/task_contract.py`:
  - `SPEC_ERRATA_ITEM_RE = re.compile(r"^-\s*\*\*\[(SE-\d+)\]\s*([^*]*)\*\*:\s*(.+)$")`
  - `parse_spec_errata(hld_text: str) -> list[tuple[str, str]]`: extracts `(errata_id, description)` tuples from `section(hld_text, "Spec Errata") or section(hld_text, "Đính chính Đặc tả (Spec Errata)")`. If the section exists and contains non-empty bullet lines that do not match `SPEC_ERRATA_ITEM_RE`, raises `ContractError("Spec Errata bullet must match '- **[SE-NN] <Section>**: <description>'")`.
- In `skills/dev-implementation/resources/scripts/check_epic_readiness.py`:
  - In `check_metadata(ctx)` (`R7`): parses `en_errata = tc.parse_spec_errata(ctx.hld_text)` and (when `<epic_dir>.vi.md` exists) `vi_errata = tc.parse_spec_errata(vi_text)` (catching `tc.ContractError` as `Finding("R7", "FAIL", str(err))`). If `[eid for eid, _ in en_errata] != [eid for eid, _ in vi_errata]`, appends `Finding("R7", "FAIL", f"Spec Errata IDs differ between .en.md and .vi.md: {[e for e, _ in en_errata]} vs {[e for e, _ in vi_errata]}")`.
- In `skills/dev-implementation/resources/scripts/package_epic.py`:
  - CLI interface: `package_epic.py <epic_dir> [--revise] [--reason <text>] [--base-branch <branch>] [--open-note <note> ...]`.
  - Validates CLI usage first: if `--revise` is passed without a non-empty `--reason`, prints `"error: --reason is required when --revise is set"` to `stderr` and exits `2`. If `--revise` is passed when `.devtool/epic/<epic_dir>/handoff.md` does not exist, prints `"error: handoff.md does not exist; run without --revise first"` to `stderr` and exits `2`.
  - Runs `check_epic_readiness.py <epic_dir>` (before writing `handoff.md`): if readiness returns any `FAIL` finding, prints the readiness report and exits `1`.
  - Resolves `design_commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], ...).stdout.strip()`.
  - When `--revise` is False: updates `<epic_dir>.{en,vi}.md` `Status` to `f"Packaged ({today_iso})"` if not already starting with `Packaged`, `In Progress`, or `Done`, and writes `.devtool/epic/<epic_dir>/handoff.md` with valid ToC and sections (`Status`, `Identifiers`, `Read First`, `Resume Prompt`, `Execution Guardrails for Receiving LLM`, `Open Notes`, `Rules for the Receiving Agent`).
  - When `--revise` is True: reads existing `handoff.md`, extracts old `Design commit` (`old_sha`), replaces `- **Packaged**: ...` with `today_iso`, replaces `- **Design commit**: `<old_sha>`` with `` `<design_commit>` ``, updates `git log <old_sha>..` to `git log <design_commit>..`, preserves `## Open Notes` verbatim, and inserts/appends `- **<today_iso> (`<old_sha>` -> `<design_commit>`)**: <reason>` under `## Revisions` (adding `- [Revisions](#revisions)` to `## Table of Contents` if absent).

## Definition of Done

- `task_contract.py` and `check_epic_readiness.py` (`R7`) parse and validate bilingual `## Spec Errata` (`[SE-NN]`) symmetry (`MEO-HP-03`, `MEO-FR-02`). (V2, V5)
- `package_epic.py` supports initial packaging and `--revise --reason` re-anchoring while preserving `Open Notes` and appending to `## Revisions` (`MEO-HP-03`, `MEO-ST-02`, `MEO-FR-02`). (V2, V5)
- `ruff` and `mypy` pass with zero errors. (V3, V4)
- Automated tests pass and write JUnit XML results. (V5)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 01](task_01_inter_epic_dependencies.md)

## References & Rollback

- Reference: [2026-11-06-multi-epic-orchestration-and-governance-design.en.md](2026-11-06-multi-epic-orchestration-and-governance-design.en.md).
- Rollback: `git revert` the task commit to remove `package_epic.py` and `Spec Errata` checks.
