---
id: "task_01_polyglot_worktree_bootstrap"
status: "backlog"
priority: "high"
assignee: null
epic: "execution-and-verification-infrastructure"
dueDate: null
created: "2026-11-06T03:20:00Z"
modified: "2026-11-06T03:20:00Z"
completedAt: null
labels: ["infrastructure", "worktree", "polyglot"]
order: "b1"
---

# Task 01: Worktree Bootstrap Extras, Polyglot Detection, and JUnit Directory Creation

Epic: [execution_and_verification_infrastructure](../epic/execution_and_verification_infrastructure/execution_and_verification_infrastructure.en.md)

## Requirement Analysis

Resolve Observations #0006 and #0018:
1. `bootstrap_worktree.sh` currently runs bare `uv sync` and exits immediately after the first detected toolchain (Python, Rust, or Web), leaving worktree virtual environments missing optional extras (`--extra asr`) declared by the repository and skipping Node dependency installation (`npm install` / `pnpm install`) in polyglot Python + Web repositories.
2. `detect_project_type.sh` stops at the first matched platform and only detects `web` when a framework config file exists alongside `package.json`. Adding `--all` allows callers and bootstrap scripts to discover every platform present in a polyglot checkout (`python web`).
3. `run_task_checks.py` invokes Verification row commands before ensuring parent directories exist for JUnit report flags (`--junitxml=<path>`, `--test-reporter-destination=<path>`), causing `node --test --test-reporter=junit` to fail with exit code 7 when `build/test-results/` has not been created yet.

## Files

Allowed files:
- `skills/python-quality-check/resources/schemas/python-quality.schema.json`
- `skills/python-quality-check/resources/scripts/validate_python_quality.py`
- `skills/python-quality-check/resources/scripts/test_validate_python_quality.py`
- `skills/dev-implementation/resources/scripts/detect_project_type.sh`
- `skills/dev-implementation/resources/scripts/bootstrap_worktree.sh`
- `skills/dev-implementation/resources/scripts/test_bootstrap_worktree_validation.sh`
- `skills/dev-implementation/resources/scripts/run_task_checks.py`
- `skills/dev-implementation/resources/scripts/test_run_task_checks.py`

Read-only context:
- `.agents/quality/python-quality.json` (project Python quality manifest)
- `.devtool/epic/execution_and_verification_infrastructure/execution_and_verification_infrastructure.en.md` (HLD specification)

## Design Rationale

Applicable skills: `python-quality-check`, `using-git-worktrees`, `test-driven-development`.
1. Adding an optional top-level `"bootstrap"` array of non-empty command strings to `python-quality.schema.json` and `validate_python_quality.py` lets repositories declare exact environment sync commands (e.g., `["uv sync --extra asr"]` or `["pip install -e .[dev]"]`) in `.agents/quality/python-quality.json` while keeping existing manifests valid.
2. Removing early `exit 0` from the Python, Rust, and Web blocks in `bootstrap_worktree.sh` and tracking `BOOTSTRAPPED=0` ensures polyglot repositories run every applicable toolchain bootstrap before exiting cleanly when no mobile (`secureFiles/`) toolchain is present.
3. Adding `ensure_output_dirs(command: str, root: Path) -> None` in `run_task_checks.py` before `run_command()` guarantees parent directories for `--junitxml` and `--test-reporter-destination` exist for both `pytest` and `node --test`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/python-quality-check/resources/scripts/validate_python_quality.py`: `validate_python_config`.
  - `skills/dev-implementation/resources/scripts/run_task_checks.py`: `run_row` and new `ensure_output_dirs`.
- **Downstream Callers**: `skills/using-git-worktrees/SKILL.md` and `skills/dev-implementation/SKILL.md`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on modified validation and runner functions.

### BDD SCENARIOS

Covers: EVI-HP-01, EVI-EC-02, EVI-FR-01

```gherkin
  Scenario: [EVI-HP-01] [Tier C - Integration] Worktree bootstrap executes python-quality.json bootstrap commands and installs polyglot dependencies
    Given a polyglot git repository containing both "pyproject.toml" and "package.json"
    And ".agents/quality/python-quality.json" defines "bootstrap" as ["pip install -e .[dev]"]
    When "detect_project_type.sh --all" is executed on the repository
    Then it outputs "python web"
    And when "bootstrap_worktree.sh" runs on a worktree of the repository
    Then it executes both the Python bootstrap phase (including the "bootstrap" commands from ".agents/quality/python-quality.json") and the Web dependency installation phase

  Scenario: [EVI-EC-02] [Tier A - Unit] Task runner automatically creates parent directories for JUnit XML output flags before executing Verification rows
    Given a task Verification row containing "--junitxml=.devtool/evidence/nested/junit/report.xml" where ".devtool/evidence/nested/junit" does not exist
    When "run_task_checks.py" executes the Verification row
    Then "ensure_output_dirs()" creates ".devtool/evidence/nested/junit" prior to invoking the subprocess so the test runner writes the XML report without error

  Scenario: [EVI-FR-01] [Tier A - Unit] validate_python_quality.py rejects malformed bootstrap configurations with invalid_bootstrap_format
    Given a ".agents/quality/python-quality.json" file where "bootstrap" is not a non-empty list of non-empty strings
    When "validate_python_quality.py" validates the configuration
    Then it fails validation and emits an error with code "invalid_bootstrap_format"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest skills/python-quality-check/resources/scripts/test_validate_python_quality.py -k test_validate_python_quality.py::test_EVI_FR_01_invalid_bootstrap_format` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest skills/python-quality-check/resources/scripts/test_validate_python_quality.py skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/python-quality-check/resources/scripts/validate_python_quality.py skills/python-quality-check/resources/scripts/test_validate_python_quality.py skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent skills/python-quality-check/resources/scripts/validate_python_quality.py skills/dev-implementation/resources/scripts/run_task_checks.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest skills/python-quality-check/resources/scripts/test_validate_python_quality.py skills/dev-implementation/resources/scripts/test_run_task_checks.py --junitxml=build/test-results/task_01_polyglot.xml` | exit 0; results build/test-results/task_01_polyglot.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- In `skills/python-quality-check/resources/schemas/python-quality.schema.json`, add optional property `"bootstrap"` under root `"properties"`:
  `{"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}}`.
- In `skills/python-quality-check/resources/scripts/validate_python_quality.py`, inside `validate_python_config()`, if `"bootstrap"` is in `config`, validate that `isinstance(bootstrap, list) and len(bootstrap) > 0 and all(isinstance(cmd, str) and bool(cmd.strip()) for cmd in bootstrap)`; otherwise append `_finding("invalid_bootstrap_format", "Optional 'bootstrap' field must be a non-empty array of non-empty command strings")`.
- In `skills/dev-implementation/resources/scripts/detect_project_type.sh`, accept `--all` as either first or second argument. When `--all` is active, evaluate all platform checks in order (`flutter`, `ios`, `android`, `python`, `web`, `rust`, where `web` matches any repo with `$TARGET_DIR/package.json` when `--all` is passed or when framework configs / `tests/js` exist) and print space-separated detected types on one line (e.g., `python web`). Without `--all`, preserve existing single-platform output and order.
- In `skills/dev-implementation/resources/scripts/bootstrap_worktree.sh`, execute Python, Rust, and Web blocks sequentially without early `exit 0`; in the Python block, if `.agents/quality/python-quality.json` defines a non-empty `"bootstrap"` array, execute each command in `$WORKTREE_PATH` via `bash -c`, otherwise fall back to `uv sync` / `poetry install` / `pip install -r requirements.txt`. After the Web block, if `BOOTSTRAPPED=1` and no mobile project markers (`pubspec.yaml`, `melos.yaml`, `Project.swift`, `Workspace.swift`, `Tuist.swift`, `settings.gradle.kts`, `settings.gradle`, `build.gradle.kts`) exist in `$WORKTREE_PATH`, print `"Worktree bootstrap complete at $WORKTREE_PATH"` and `exit 0`.
- In `skills/dev-implementation/resources/scripts/run_task_checks.py`, add `OUTPUT_DIR_FLAGS = ("--junitxml", "--junit-xml", "--test-reporter-destination")` and `ensure_output_dirs(command: str, root: Path) -> None`, called immediately before `run_command(row.command, root, timeout)` in `run_row()`.

## Definition of Done

- `python-quality.schema.json` and `validate_python_quality.py` accept valid `"bootstrap"` command arrays and reject malformed values with `invalid_bootstrap_format`. (V2, V5)
- `detect_project_type.sh --all` outputs all detected platforms (`python web`) and `bootstrap_worktree.sh` runs both Python `"bootstrap"` commands and Web dependency installation in polyglot worktrees. (V2, V5)
- `run_task_checks.py` creates missing parent directories for `--junitxml` and `--test-reporter-destination` before running Verification rows. (V2, V5)
- `ruff` and `mypy` pass with zero errors. (V3, V4)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- None (Wave 1).

## References & Rollback

- Reference: [2026-11-06-execution-and-verification-infrastructure-design.en.md](../epic/execution_and_verification_infrastructure/2026-11-06-execution-and-verification-infrastructure-design.en.md).
- Rollback: `git revert` the task commit to restore prior schema, bootstrap scripts, and runner behavior.
