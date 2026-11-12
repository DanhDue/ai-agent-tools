---
id: "task_02_silent_gate4_and_truncated_test_runners"
status: "todo"
priority: "high"
assignee: null
epic: "token_throttling_optimization"
dueDate: null
created: "2026-11-13T02:30:00Z"
modified: "2026-11-13T02:30:00Z"
completedAt: null
labels: ["gate4", "quality-check", "token-optimization"]
order: "a2"
---

# Task 2: Silent Gate 4 and Truncated Test Runners

Epic: [token_throttling_optimization](../epic/token_throttling_optimization/token_throttling_optimization.en.md)

## Requirement Analysis

Enforce Silent Gate 4 and 25-line failure tailing (`Rule 2`) across quality providers, task verification runners, and release checks:
1. Add `--compact` mode to `skills/quality_check/resources/scripts/verify_polyglot_registry.py`:
   - Write full raw stdout/stderr per provider capability to `build/quality/<provider>/<cap>.log`.
   - When `--compact` is enabled and checks/verdict pass, print single-line `GATE_PASS: <provider_or_cap>` entries instead of verbose JSON blobs.
   - When `--compact` encounters a failure or `BLOCKED` outcome, print the failing capability header and strictly at most 25 trailing lines from its `.log` file while leaving all raw lines intact on disk.
2. Reduce `TAIL_LINES` from `40` to `25` in `skills/dev-implementation/resources/scripts/run_task_checks.py`.
3. Update `.agents/quality/python-quality.json` (protected path named explicitly in `Allowed files`) `"test"` command and `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py` `"python"` template so pytest runs append `"-q", "--tb=short", "--maxfail=3"`.
4. Add `--quiet` flag to `scripts/verify.sh` outputting one concise status line per passing section and at most 25 trailing lines on failure, while keeping default/`--full` behavior unchanged.
5. Document `--compact` invocation in `skills/quality_check/SKILL.md`.
6. Expand `tests/test_polyglot_gate4.py` and `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py` / `skills/dev-implementation/resources/scripts/test_run_task_checks.py` with tests covering `TTO-HP-02`, `TTO-EC-02`, and `TTO-FR-02`.

## Files

Allowed files:
- `skills/quality_check/resources/scripts/verify_polyglot_registry.py`
- `skills/dev-implementation/resources/scripts/run_task_checks.py`
- `skills/dev-implementation/resources/scripts/test_run_task_checks.py`
- `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`
- `skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py`
- `.agents/quality/python-quality.json`
- `scripts/verify.sh`
- `skills/quality_check/SKILL.md`
- `tests/test_polyglot_gate4.py`

Read-only context:
- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Module Contracts (§2)
- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios

## Design Rationale

Quality checks routinely emit thousands of passing lines and JSON structures into agent context. Routing verbose provider output to `build/quality/<provider>/<cap>.log` and returning single-line `GATE_PASS:` summaries or 25-line failure tails slashes Gate 4 token burn while keeping full diagnostics on disk for debugging. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/quality_check/resources/scripts/verify_polyglot_registry.py`: `execute_provider` (L142-L438), `verify_polyglot_execution` (L441-L537), `main` (L540-L618)
  - `skills/dev-implementation/resources/scripts/run_task_checks.py`: `run_row` (L282-L321), `main` (L461-L476)
  - `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`: `build_registry_data` (L226-L241)
  - `scripts/verify.sh`: §1-§17 output formatting (L1-L417)
  - `tests/test_polyglot_gate4.py`: integration assertions for `TTO-HP-02`, `TTO-EC-02`, `TTO-FR-02`
- **Downstream Callers**: `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`run_gate4`), `skills/dev-implementation/SKILL.md` (`@quality_check`), `skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of `--compact` pass/fail branches, 25-line truncation boundaries, and `--quiet` `verify.sh` handling.

### BDD SCENARIOS

Covers: TTO-HP-02, TTO-EC-02, TTO-FR-02

```gherkin
Scenario: [TTO-HP-02] [Tier C - Integration] Compact Gate 4 runner prints single-line GATE_PASS and stores full logs under build/quality

Given a project with a valid .agents/quality/check_quality.json registry whose providers exit with status 0
When verify_polyglot_registry.py runs with --compact
Then standard output contains single-line "GATE_PASS: <provider_or_cap>" entries instead of verbose JSON blobs
And full per-capability execution logs are written to build/quality/<provider>/<cap>.log
And the overall aggregated verdict equals PASS

Scenario: [TTO-EC-02] [Tier A - Unit] Task runner enforces 25-line tail and Python quality manifests inject quiet pytest flags

Given a failing task check output with 120 stdout/stderr lines
And .agents/quality/python-quality.json alongside a scaffolded manifest from scaffold_quality_manifest.py
When run_task_checks.py formats failure evidence and the Python test command is inspected
Then run_task_checks.TAIL_LINES equals 25 and the emitted snippet retains only the last 25 non-empty lines
And both .agents/quality/python-quality.json and newly scaffolded Python quality manifests invoke pytest with "-q", "--tb=short", and "--maxfail=3"

Scenario: [TTO-FR-02] [Tier C - Integration] Compact Gate 4 surfaces failing provider header and 25-line log tail on error

Given a quality registry containing one passing capability and one failing capability printing 80 diagnostic lines to stderr
When verify_polyglot_registry.py runs with --compact
Then the process exits non-zero reporting FAIL
And standard output prints "GATE_PASS:" for the passing capability plus the failing capability header and strictly at most 25 trailing log lines from build/quality/
And all 80 raw diagnostic lines remain preserved on disk inside build/quality/<provider>/<cap>.log
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_polyglot_gate4.py::test_tto_hp_02_compact_gate4_single_line_pass` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_polyglot_gate4.py::test_tto_hp_02_compact_gate4_single_line_pass` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_polyglot_gate4.py skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/dev-implementation/resources/scripts/run_task_checks.py tests/test_polyglot_gate4.py` | exit 0 | — |
| V5 | TIER-B | `ruff check --select F,E9,B skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py` | exit 0 | — |
| V6 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/run_task_checks.py skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py` | exit 0 | — |
| V7 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_2.xml tests/test_polyglot_gate4.py` | exit 0; results build/test-results/task_2.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path not named explicitly here.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `verify_polyglot_registry.py` (`execute_provider` L142-L438, `main` L540-L618) adds `--compact`: always writes full capability stdout/stderr to `build/quality/<provider>/<cap>.log`, prints `GATE_PASS: <provider_or_cap>` for passing checks, and prints failing header + last 25 lines of the capability log on failure while returning non-zero exit codes cleanly.
- `run_task_checks.py` updates `TAIL_LINES = 25` (`run_task_checks.py` line 77).
- `.agents/quality/python-quality.json` updates `"test"` capability from `["python3", "-m", "pytest", "tests"]` to `["python3", "-m", "pytest", "-q", "--tb=short", "--maxfail=3", "tests"]` (justifying modification of this declared protected path by naming it explicitly in `Allowed files`).
- `scaffold_quality_manifest.py` (`PLATFORM_CONFIGS["python"]["manifest"]["capabilities"]["test"]`, L131) includes `"-q", "--tb=short", "--maxfail=3"`.
- `scripts/verify.sh` adds `--quiet` flag without changing `--full` default semantics or exit codes.

## Definition of Done

- Scenarios TTO-HP-02, TTO-EC-02, and TTO-FR-02 are verified by passing unit and integration tests. (V2, V3, V7)
- Ruff lint and mypy checks pass cleanly across modified files. (V4, V5, V6)
- Protected path `.agents/quality/python-quality.json` update produces quiet pytest flags cleanly under Gate 4. (Gate 5)

## Dependencies & Blockers

None. Blocks [Task 4](../epic/token_throttling_optimization/task_04_lifecycle_runner_programmer_config_and_pool_isolation.md) and [Task 5](../epic/token_throttling_optimization/task_05_slimming_rules_skills_dedup_and_selective_reviewer.md).

## References & Rollback

- [Epic HLD](../epic/token_throttling_optimization/token_throttling_optimization.en.md), Module Contracts (§2).
- **Rollback**: Revert task commit; restores prior `verify_polyglot_registry.py`, `TAIL_LINES = 40`, `python-quality.json`, and `verify.sh`.

