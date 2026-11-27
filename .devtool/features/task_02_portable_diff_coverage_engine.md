---
id: "task_02_portable_diff_coverage_engine"
status: "todo"
priority: "high"
assignee: null
epic: "polyglot_lifecycle_and_quality_architecture"
dueDate: null
created: "2026-11-27T09:18:00+07:00"
modified: "2026-11-27T09:18:00+07:00"
completedAt: null
labels: ["quality_check", "coverage", "polyglot", "cli"]
order: "a02"
review_tier: "full"
---

# Task 02: Portable Multi-Format Hunk-Level Diff-Coverage Engine

Epic: [polyglot_lifecycle_and_quality_architecture](../epic/polyglot_lifecycle_and_quality_architecture/polyglot_lifecycle_and_quality_architecture.md)

## Requirement Analysis

Port and generalize the reference stdlib hunk-level LCOV diff-coverage verifier (`/Users/danhdueexoictif/AllProjects/nexus/scripts/check_lcov_threshold.py`, read-only reference) into a shared kit CLI at `skills/quality_check/resources/scripts/check_diff_coverage.py` supporting **LCOV**, **Cobertura XML**, and **JaCoCo XML** (`--format auto|lcov|cobertura|jacoco`), workspace + per-package dual-floor checks, hunk-level git diff coverage (`--diff-base`, `--diff-files`, `--min-diff-coverage`, `--source-ext`), generated-file exclusions, untested new-file fallback line detection, and the compact one-line `PASS` stdout invariant (`--verbose` / `--json` opt-in).

## Files

Allowed files:
- `skills/quality_check/resources/scripts/check_diff_coverage.py` (new)
- `tests/test_check_diff_coverage.py` (new)

Read-only context:
- `.devtool/epic/polyglot_lifecycle_and_quality_architecture/polyglot_lifecycle_and_quality_architecture.md`
- `.devtool/epic/polyglot_lifecycle_and_quality_architecture/bdd_scenarios.md`
- `/Users/danhdueexoictif/AllProjects/nexus/scripts/check_lcov_threshold.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development` and `d3nexus:python-quality-check` (Python 3 stdlib only: `xml.etree.ElementTree`, `argparse`, `subprocess`, `json`, `pathlib`, `re`).
- Feed all three parsers (`LCOV`, `Cobertura XML`, `JaCoCo XML`) into one canonical `CoverageDataset` (`da_by_file`, `fallback_by_file`) so dual-floor calculation, generated-code exclusion, and git hunk diff-coverage share one audited code path.
- Honor the Token-Budget Invariant: default stdout on `PASS` is strictly one line starting with `PASS:`; `FAIL` (`exit 1`) and `BLOCKED` (`exit 2`) expand actionable per-package/per-file/uncovered-line diagnostics without raw Python tracebacks.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/quality_check/resources/scripts/check_diff_coverage.py` (new): `CoverageDataset`, `detect_format`, `parse_lcov`, `parse_cobertura_xml`, `parse_jacoco_xml`, `collect_git_diff_lines`, `evaluate_coverage`, `format_output`, `main`.
  - `tests/test_check_diff_coverage.py` (new): Fixture and temp-git-repo tests for all 3 formats, dual-floor checks, diff hunks, untested new-file fallback, corrupt/missing report exit code 2, and compact 1-line `PASS` / `--verbose` / `--json`.
- **Downstream Callers**: `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`, `skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`, `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py`.
- **Cross-Platform Bridges**: None.
- **Target Coverage Threshold**: >= 90% on `check_diff_coverage.py`, 100% on parser error and threshold failure branches.

### BDD SCENARIOS

Covers: PLQ-HP-02, PLQ-EC-03, PLQ-EC-04, PLQ-FR-02

```gherkin
Scenario: [PLQ-HP-02] [Tier C - Integration] Portable diff-coverage engine evaluates LCOV, Cobertura XML, and JaCoCo XML with compact one-line PASS
Given temporary repositories containing valid LCOV, Cobertura XML, and JaCoCo XML coverage reports covering >= 85% of modified source hunks and >= 80% workspace lines
When check_diff_coverage.py is executed with --format auto, --min-coverage 75, --min-package-coverage 60, --diff-files, and --min-diff-coverage 80
Then each invocation exits with code 0
And stdout contains exactly one line starting with "PASS:" and reporting both coverage percentage and diff percentage
And re-running with --json prints valid JSON containing status "PASS", coverage_pct, and diff_coverage_pct

Scenario: [PLQ-EC-03] [Tier C - Integration] Untested new source file triggers fallback executable-line diff-coverage failure
Given a git repository with a newly added untracked source file "src/new_service.py" containing 10 executable statements and 0 entries in coverage.xml
When check_diff_coverage.py runs with --diff-base HEAD --min-diff-coverage 80 --source-ext .py
Then check_diff_coverage.py exits with code 1
And stdout reports "FAIL:" along with "src/new_service.py" and its uncovered executable line count

Scenario: [PLQ-EC-04] [Tier C - Integration] Generated files and excluded packages are omitted from dual-floor enforcement
Given an LCOV report containing 0% coverage for "packages/core/lib/model.g.dart" and 45% coverage for "packages/legacy/lib/old.dart" alongside 90% coverage for "packages/core/lib/service.dart"
When check_diff_coverage.py runs with --min-coverage 75 --min-package-coverage 60 --exclude-package-floor legacy
Then generated ".g.dart" lines are excluded from coverage denominators
And "legacy" is skipped for the per-package floor while "core" passes at 90%
And check_diff_coverage.py exits with code 0

Scenario: [PLQ-FR-02] [Tier C - Integration] Malformed or missing coverage reports return exit code 2 BLOCKED cleanly
Given a missing report path and a corrupt XML file "<broken"
When check_diff_coverage.py runs against either input
Then check_diff_coverage.py exits with code 2
And output starts with "BLOCKED:" naming the offending report path without a Python traceback
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_check_diff_coverage.py::test_plq_hp_02_multiformat_compact_pass_and_json` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_check_diff_coverage.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 skills/quality_check/resources/scripts/test_validate_quality_contract.py skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py skills/quality_check/resources/scripts/test_quality_provider_acceptance.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/quality_check/resources/scripts/check_diff_coverage.py tests/test_check_diff_coverage.py && ruff format --check skills/quality_check/resources/scripts/check_diff_coverage.py tests/test_check_diff_coverage.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/quality_check/resources/scripts/check_diff_coverage.py tests/test_check_diff_coverage.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_check_diff_coverage.py --junitxml=build/test-results/task_02.xml` | exit 0; results build/test-results/task_02.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **New contract (`skills/quality_check/resources/scripts/check_diff_coverage.py`)**:
  - Format detection (`--format auto`): inspect stripped content; if starts with `<`, parse root XML tag (`coverage` -> `cobertura`, `report` -> `jacoco`; invalid XML -> exit `2` `BLOCKED:`); otherwise require LCOV marker (`SF:` or `end_of_record`) or exit `2` `BLOCKED:`.
  - Multiple report files merge via `max(old_hits, new_hits)` per normalized `(posix_rel_path, line_number)`.
  - Threshold normalization: accept both fractional `[0.0, 1.0]` (e.g., `0.80` -> `80.0%`) and percentage `(1.0, 100.0]` (e.g., `80` -> `80.0%`); reject `< 0` or `> 100` with exit `2`.
  - Default `--package-group`: `("packages", "features", "crates", "apps", "services", "modules", "libs", "src")`.
  - Default `--exclude-suffix`: `(".g.dart", ".freezed.dart", ".gen.dart", ".pb.dart", ".pb.rs", ".pb.swift", ".d.ts", "GeneratedPluginRegistrant.swift")`.
  - Default `--source-ext`: `(".py", ".dart", ".rs", ".ts", ".tsx", ".js", ".mjs", ".astro", ".kt", ".kts", ".swift")`.
  - Exit codes: `0` = `PASS`, `1` = `FAIL` (coverage/package/diff floor breach), `2` = `BLOCKED` (missing file, corrupt XML/LCOV, invalid git ref or flag).
  - Compact 1-line `PASS` stdout format: `PASS: coverage=<cov>% (floor>=<min>%), diff=<diff>% (floor>=<min_diff>%, files=<n>, lines=<m>)` (omitting `coverage=...` when `--min-coverage` is 0 and omitted, or omitting `diff=...` when `--min-diff-coverage` is not requested).
  - JSON output (`--json`): `{"status": "PASS|FAIL|BLOCKED", "coverage_pct": float, "min_coverage_pct": float, "diff_coverage_pct": float | None, "min_diff_coverage_pct": float | None, "package_results": [...], "diff_files": [...], "failures": [...]}`.
  - In TDD `RED` (`V1`), `test_plq_hp_02_multiformat_compact_pass_and_json` checks `SCRIPT.is_file()` and calls `pytest.fail(...)` when missing so `V1` deterministically exits `1` with `FAILED`.

## Definition of Done

- [ ] `skills/quality_check/resources/scripts/check_diff_coverage.py` supports LCOV, Cobertura XML, and JaCoCo XML using Python 3 stdlib only (V2, V5)
- [ ] All tests in `tests/test_check_diff_coverage.py` pass covering `PLQ-HP-02`, `PLQ-EC-03`, `PLQ-EC-04`, `PLQ-FR-02` (V2, V5)
- [ ] Downstream quality contract and scaffolder regression suites pass without regressions (V3)
- [ ] `ruff check`, `ruff format --check`, and `mypy` pass across all Allowed files (V4)
- [ ] Fresh JUnit XML report written to `build/test-results/task_02.xml` containing all 4 assigned scenario IDs (V5)

## Dependencies & Blockers

- None (Wave 1 — runs in parallel with Task 01 and Task 03).

## References & Rollback

- Reference HLD: [polyglot_lifecycle_and_quality_architecture.md](../epic/polyglot_lifecycle_and_quality_architecture/polyglot_lifecycle_and_quality_architecture.md)
- Reference implementation (read-only): `/Users/danhdueexoictif/AllProjects/nexus/scripts/check_lcov_threshold.py`
- Rollback: Delete `skills/quality_check/resources/scripts/check_diff_coverage.py` and `tests/test_check_diff_coverage.py`.
