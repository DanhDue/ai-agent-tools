---
id: "task_02_receipt_hygiene_diff_coverage_and_scaffolder"
status: "todo"
priority: "high"
assignee: null
epic: "shift_left_quality_resolver"
dueDate: null
created: "2026-11-28T10:10:00+07:00"
modified: "2026-11-28T10:10:00+07:00"
completedAt: null
labels: ["security", "architecture", "quality-check", "coverage"]
order: "a02"
review_tier: "full"
---

# Task 02: Gate 4 Receipt Hygiene, Adapter/Module Floor Ratchets, and Scaffolder Deduplication

Epic: [shift_left_quality_resolver](../epic/shift_left_quality_resolver/shift_left_quality_resolver.md)

## Requirement Analysis

Close Observation `#0023` and align the shared kit engines with the post-rollout five-repository architecture: (1) unlink stale `build/quality/gate4_receipt.json` whenever an `epic` or `release` run in `verify_polyglot_registry.py` finishes with `status != "PASS"`; (2) emit an explicit dirty-worktree warning in `integrate_branch.py verify-tier` so uncommitted changes never silently ride a `noop` receipt; (3) add `--package-floors <coverage_floors.json>` monotonic adapter/module ratchet enforcement to `check_diff_coverage.py`; and (4) deduplicate `epic`/`release` audit and impact capabilities, remove online `cargo audit` from offline `pr`/`epic` profiles, enforce `npx --no-install`, and set `mypy --strict src tests` in `scaffold_quality_manifest.py`.

## Files

Allowed files:
- `skills/quality_check/resources/scripts/verify_polyglot_registry.py`
- `skills/quality_check/resources/scripts/check_diff_coverage.py`
- `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`
- `skills/finishing-a-development-branch/resources/scripts/integrate_branch.py`
- `tests/test_slqr_receipt_coverage_and_scaffolder.py` (new)

Read-only context:
- `.devtool/epic/shift_left_quality_resolver/shift_left_quality_resolver.md`
- `.devtool/epic/shift_left_quality_resolver/bdd_scenarios.md`
- `tests/test_check_diff_coverage.py`
- `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py`
- `tests/test_polyglot_gate4.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development`, `d3nexus:quality_check`, and `d3nexus:python-quality-check` (Python 3 stdlib only, strict `0 / 1 / 2` exit codes).
- Any certification receipt consumed downstream to bypass re-verification must be invalidated on every non-passing `epic`/`release` run (`#0023`), while leaving `pr` runs side-effect-free on `gate4_receipt.json`.
- Supporting `--package-floors` in `check_diff_coverage.py` lets repositories pin monotonic adapter/module baselines (`coverage_floors.json`) without maintaining custom coverage wrappers.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/quality_check/resources/scripts/verify_polyglot_registry.py` (`L1576-L1601`): `verify_polyglot_execution()` `else` branch unlinking `build/quality/gate4_receipt.json` (`missing_ok=True`) when `requested_profile in ("epic", "release")` and `out_res.get("status") != "PASS"`.
  - `skills/finishing-a-development-branch/resources/scripts/integrate_branch.py` (`L409-L426`): `cmd_verify_tier()` checks `dirty_files(untracked=False)` and appends `"the worktree has uncommitted changes"` to `warnings` (matching `cmd_preflight` `L338-L339`).
  - `skills/quality_check/resources/scripts/check_diff_coverage.py` (`L1050-L1245`, `L1297-L1555`): `_load_package_floors()`, `evaluate_coverage(..., custom_floors=...)`, and CLI `--package-floors <path>` flag.
  - `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py` (`L101-L950`): deduplicate `epic`/`release` (`workspace_audit` + `workspace_impact`, keeping `epic.issubset(release)`), set Rust `security` to `["./scripts/check_security.sh"]` (`cargo audit` stays in `security_deps`), use `npx --no-install` in Web, drop `test_e2e` from Web `scheduled`, and set Python `type_check` to `["uv", "run", "mypy", "--strict", "src", "tests"]`.
  - `tests/test_slqr_receipt_coverage_and_scaffolder.py` (new): unit and subcutaneous integration tests covering `SLQR-HP-02`, `SLQR-EC-02`, `SLQR-ST-01`, `SLQR-ST-02`, `SLQR-FR-02`.
- **Downstream Callers**: `tests/test_check_diff_coverage.py`, `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py`, `tests/test_plq_quality_contracts_and_scaffolder.py`, `tests/test_polyglot_gate4.py`.
- **Cross-Platform Bridges**: None.
- **Target Coverage Threshold**: >= 90% across modified functions, 100% on `exit 2` (`BLOCKED`) and receipt unlink branches.

### BDD SCENARIOS

Covers: SLQR-HP-02, SLQR-EC-02, SLQR-ST-01, SLQR-ST-02, SLQR-FR-02

```gherkin
Scenario: [SLQR-HP-02] [Tier C - Integration] Scaffolder generates deduplicated offline-safe 4-profile manifests and check_diff_coverage enforces package_floors ratchets
Given a polyglot temporary repository containing markers for all 6 stacks and a ".agents/quality/coverage_floors.json" defining adapter floor "src/pkg/align": 0.88 and module floor "src/web/studio.js": 0.50
When scaffold_quality_manifest.py runs and check_diff_coverage.py evaluates LCOV/Cobertura reports with "--package-floors .agents/quality/coverage_floors.json"
Then every generated stack manifest has 0 duplicate audit or impact invocations per profile ("pr_diff_audit" and "pr_impact" in "pr" only; "workspace_audit" and "workspace_impact" in "epic", "scheduled", and "release")
And generated Web capabilities use "npx --no-install", generated Rust "pr" and "epic" profiles omit "cargo audit", and generated Python "type_check" targets ["uv", "run", "mypy", "--strict", "src", "tests"]
And check_diff_coverage.py returns exit code 0 when "src/pkg/align" is at 90.0% and "src/web/studio.js" is at 55.0%, and returns exit code 1 naming the breached ratchet when either drops below its floor

Scenario: [SLQR-EC-02] [Tier C - Integration] check_diff_coverage handles missing or malformed package_floors file as exit 2 BLOCKED and exempts unmeasured files cleanly
Given a valid LCOV report covering "src/core/service.py" at 95.0%
When check_diff_coverage.py runs with "--package-floors missing_floors.json" or a corrupt JSON file
Then check_diff_coverage.py exits with code 2 and status "BLOCKED" without an unhandled Python traceback

Scenario: [SLQR-ST-01] [Tier C - Integration] Non-passing epic or release quality run unlinks stale gate4_receipt.json while pr run preserves isolation
Given a repository where a prior "verify_polyglot_registry.py --profile epic --execute" run succeeded and wrote "build/quality/gate4_receipt.json" with status "PASS"
When a subsequent "--profile epic --execute" (or "--profile release --execute") run finishes with status "FAIL" or "BLOCKED"
Then "build/quality/gate4_receipt.json" is immediately unlinked and no longer exists on disk

Scenario: [SLQR-ST-02] [Tier C - Integration] integrate_branch verify-tier surfaces dirty working tree warning when uncommitted edits exist on a noop branch
Given a feature branch whose HEAD matches its backup ref ("tier == noop") but contains uncommitted modifications to a tracked source file
When "integrate_branch.py verify-tier --base main --format json" executes
Then the JSON report includes a non-empty warning stating that the worktree has uncommitted changes so callers do not blindly reuse a clean-SHA receipt

Scenario: [SLQR-FR-02] [Tier C - Integration] verify_polyglot_registry handles missing or read-only receipt cleanup gracefully without masking FAIL verdict
Given a repository with no pre-existing "build/quality/gate4_receipt.json"
When "verify_polyglot_registry.py --profile epic --execute" finishes with a provider "FAIL"
Then verify_polyglot_registry returns overall status "FAIL" cleanly without raising FileNotFoundError during receipt cleanup
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_receipt_coverage_and_scaffolder.py::test_slqr_st_01_non_passing_epic_or_release_unlinks_stale_gate4_receipt` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_receipt_coverage_and_scaffolder.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_check_diff_coverage.py skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py tests/test_plq_quality_contracts_and_scaffolder.py tests/test_polyglot_gate4.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/quality_check/resources/scripts/check_diff_coverage.py skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py skills/finishing-a-development-branch/resources/scripts/integrate_branch.py tests/test_slqr_receipt_coverage_and_scaffolder.py && ruff format --check skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/quality_check/resources/scripts/check_diff_coverage.py skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py skills/finishing-a-development-branch/resources/scripts/integrate_branch.py tests/test_slqr_receipt_coverage_and_scaffolder.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/quality_check/resources/scripts/check_diff_coverage.py skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py skills/finishing-a-development-branch/resources/scripts/integrate_branch.py tests/test_slqr_receipt_coverage_and_scaffolder.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_receipt_coverage_and_scaffolder.py --junitxml=build/test-results/slqr_task_02.xml` | exit 0; results build/test-results/slqr_task_02.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`verify_polyglot_registry.py` `L1576-L1600`, `integrate_branch.py` `L338-L339` & `L409-L425`, `check_diff_coverage.py` `L1050-L1555`, `scaffold_quality_manifest.py` `L177-L228`, `L571-L648`, `L661`, `L747-L790`, `L801-L946`)**: `verify_polyglot_execution` currently writes `gate4_receipt.json` only on `status == "PASS"`; `cmd_verify_tier` omits `dirty_files(untracked=False)` warnings; `scaffold_quality_manifest.py` puts `pr_diff_audit`+`pr_impact` in `epic` and both `pr_*`+`workspace_*` in `release`.
- **New contract**:
  - `verify_polyglot_execution`: when `repo_root is not None` and `requested_profile in ("epic", "release")`, if `out_res.get("status") == "PASS"` write `gate4_receipt.json`, else unlink `repo_root / "build" / "quality" / "gate4_receipt.json"` (`missing_ok=True`) inside `try ... except OSError: pass`. Never touch `gate4_receipt.json` when `requested_profile == "pr"` or `"scheduled"`.
  - `check_diff_coverage.py --package-floors <path>`: parses JSON object supporting `python.adapters` (dict of `<dir_prefix>: <num | {"floor": num}>`), `web_modules` (dict of `<file_path>: <num | {"floor": num}>`), `packages` (dict of `<prefix>: <num | {"floor": num}>`), and flat `<path_or_prefix>: <num | {"floor": num}>` (ignoring metadata keys `schema_version`, `description`, `default_core_floor`). Normalizes thresholds via `_normalize_threshold()`. For directory/adapter prefixes, aggregates covered/total lines across all measured files under that prefix (and overrides default `--min-package-coverage` for matching package buckets so low-baseline DOM/adapter floors below `min_package_coverage` can also be explicitly configured without double-failing, while failing closed if measured coverage `< floor`); for file entries (`web_modules` or exact file match), checks that file's measured line coverage `>= floor`. Raises `BlockedError` (`exit 2`) if `--package-floors` file does not exist or is invalid JSON.
  - `scaffold_quality_manifest.py`: across all 6 stacks, `epic` uses `workspace_audit` + `workspace_impact` (dropping `pr_diff_audit` + `pr_impact`) and `release` is `epic` + `security_deps` (+ `acceptance` where configured, dropping `pr_diff_audit` + `pr_impact`), preserving `set(epic).issubset(set(release))` in `test_plq_quality_contracts_and_scaffolder.py`.

## Definition of Done

- [ ] `verify_polyglot_registry.py` unlinks stale `build/quality/gate4_receipt.json` on non-passing `epic`/`release` runs while preserving `pr` isolation, and `integrate_branch.py verify-tier` warns on dirty worktrees (V2, V5)
- [ ] `check_diff_coverage.py` supports `--package-floors <coverage_floors.json>` with `0 / 1 / 2` exit semantics across adapter prefixes and module paths (V2, V5)
- [ ] `scaffold_quality_manifest.py` emits deduplicated 4-profile manifests (`0` duplicate `pr_*`+`workspace_*`), offline `rust` `security`, `npx --no-install`, and `mypy --strict src tests` (V2, V3, V5)
- [ ] All 5 assigned scenarios (`SLQR-HP-02`, `SLQR-EC-02`, `SLQR-ST-01`, `SLQR-ST-02`, `SLQR-FR-02`) and existing regression suites pass with JUnit XML at `build/test-results/slqr_task_02.xml` (V2, V3, V5)
- [ ] `ruff check`, `ruff format --check`, and `mypy` pass across all Allowed Python files (V4)

## Dependencies & Blockers

- None (Wave 1 root task, parallel with Task 01).

## References & Rollback

- Reference HLD: [shift_left_quality_resolver.md](../epic/shift_left_quality_resolver/shift_left_quality_resolver.md)
- Rollback: Revert changes to `verify_polyglot_registry.py`, `check_diff_coverage.py`, `scaffold_quality_manifest.py`, and `integrate_branch.py`, and delete `tests/test_slqr_receipt_coverage_and_scaffolder.py`.
