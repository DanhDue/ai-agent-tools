---
id: "task_03_live_integration_and_route_matching"
status: "backlog"
priority: "high"
assignee: null
epic: "execution-and-verification-infrastructure"
dueDate: null
created: "2026-11-06T03:20:00Z"
modified: "2026-11-06T03:20:00Z"
completedAt: null
labels: ["infrastructure", "readiness", "integration"]
order: "b3"
---

# Task 03: Opt-In Live Integration Results and R5b Parameterized Route Matching

Epic: [execution_and_verification_infrastructure](../epic/execution_and_verification_infrastructure/execution_and_verification_infrastructure.en.md)

## Requirement Analysis

Resolve Observation #0010:
1. `check_epic_readiness.py` (`R6`) requires every Tier C test file in a task's `TIER-C` row to appear in an HLD `Integration results:` line, while `run_external_review.py` (`collect_facts()`) runs every `Integration results:` command unconditionally at Gate 4. Epics with opt-in live integration tests (such as `-m live_llm` tests requiring `PLT_LIVE_OLLAMA_MODEL` or `EVI_LIVE_MODEL`) have no way to declare conditional live integration commands that satisfy `R6` and skip cleanly at Gate 4 when the environment variable is unset.
2. `check_epic_readiness.py` (`R5b`) extracts `/api/...` route strings from task files and checks for exact literal substring matches in tracked source files, emitting false-positive `R5b WARN` findings when a task uses a concrete route argument (such as `http://localhost/api/align/stream/job_plt`) while the backend defines a parameterized route template (`http://localhost/api/align/stream/{job_id}`, `<job_id>`, or `:job_id`).

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/task_contract.py`
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
- `skills/dev-implementation/resources/scripts/audit_epic.py`
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py`
- `skills/dev-implementation/resources/scripts/test_audit_epic.py`

Read-only context:
- `.devtool/epic/execution_and_verification_infrastructure/execution_and_verification_infrastructure.en.md` (HLD specification)

## Design Rationale

Applicable skills: `python-quality-check`, `test-driven-development`.
1. Introducing `IntegrationResultSpec(command: str, report: str, live: bool = False, needs: tuple[str, ...] = ())` and `parse_integration_result_specs(hld_text: str) -> list[IntegrationResultSpec]` in `task_contract.py` allows HLDs to declare:
   `Integration results (live, needs: VAR1, VAR2): <command> -> <report_path>`
   By having `parse_integration_results(hld_text)` return `"<command> -> <report>"` for both standard and live lines, `check_epic_readiness.py` (`R6`) and `check_task_contract.py` automatically validate report gitignore rules and Tier C file coverage, while `collect_facts()` in `run_external_review.py` inspects `spec.live` and `spec.needs` to either execute the command (when all `needs` variables are set in `os.environ`) or record `SKIPPED (missing env: ...)` without failing Gate 4.
2. Adding `route_matches_codebase(route: str, tracked_contents: list[str]) -> bool` in `check_epic_readiness.py` (`R5b`) preserves fast literal substring checks and adds template regex matching for `{param}`, `<param>`, and `:param` route placeholders in tracked source files.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/task_contract.py`: `parse_integration_results`, new `IntegrationResultSpec`, and new `parse_integration_result_specs`.
  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `check_hld`.
  - `skills/dev-implementation/resources/scripts/check_epic_readiness.py`: `check_grounding`, `check_gate4_coverage`, and new `route_matches_codebase`.
  - `skills/dev-implementation/resources/scripts/audit_epic.py`: `GRADER_LINES`, `hld_amendments`.
  - `skills/dev-implementation/resources/scripts/run_external_review.py`: `collect_facts`.
- **Downstream Callers**: `check_epic_readiness.py`, `audit_epic.py`, `run_external_review.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on new parsing, route matching, and Gate 4 live-skip functions.

### BDD SCENARIOS

Covers: EVI-HP-03, EVI-EC-03

```gherkin
  Scenario: [EVI-HP-03] [Tier C - Integration] Opt-in live integration results satisfy R6 coverage, skip cleanly when env is unset, and execute when env is set
    Given an epic HLD containing both "Integration results:" and "Integration results (live, needs: EVI_LIVE_MODEL):"
    And "bdd_scenarios.en.md" declares a "[Tier C - Integration]" scenario whose test file appears in the live integration command
    When "check_epic_readiness.py" evaluates R6 coverage for the epic
    Then R6 passes with 0 missing Tier C test files
    And when "collect_facts()" in "run_external_review.py" runs with "EVI_LIVE_MODEL" unset in the environment
    Then the live integration row is recorded as "SKIPPED (missing env: EVI_LIVE_MODEL)" without failing Gate 4
    And when "collect_facts()" in "run_external_review.py" runs with "EVI_LIVE_MODEL=1" set in the environment
    Then the live integration row is executed and its exit status is enforced

  Scenario: [EVI-EC-03] [Tier A - Unit] R5b route drift check matches concrete route literals against parameterized route templates without false-positive warnings
    Given a task file referencing a concrete route literal "http://localhost/api/align/stream/job_plt"
    And the target codebase defines the parameterized route "http://localhost/api/align/stream/{job_id}" (or "<job_id>" or ":job_id")
    When "check_epic_readiness.py" runs the R5b route drift check
    Then "route_matches_codebase()" matches the concrete route against the parameterized template and emits 0 R5b warnings
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k test_check_epic_readiness.py::test_EVI_HP_03_live_integration_results_and_gate4` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py skills/dev-implementation/resources/scripts/test_audit_epic.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/audit_epic.py skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py skills/dev-implementation/resources/scripts/test_audit_epic.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/audit_epic.py skills/dev-implementation/resources/scripts/run_external_review.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py skills/dev-implementation/resources/scripts/test_audit_epic.py --junitxml=build/test-results/task_03_live_int.xml` | exit 0; results build/test-results/task_03_live_int.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- In `skills/dev-implementation/resources/scripts/task_contract.py`:
  - Define `@dataclass(frozen=True) class IntegrationResultSpec: command: str; report: str; live: bool = False; needs: tuple[str, ...] = ()` and `INTEGRATION_RESULTS_RE = re.compile(r"^Integration results(?:\s*\(live,\s*needs:\s*([^)]+)\))?:\s*(.+)$")`.
  - `parse_integration_result_specs(hld_text: str) -> list[IntegrationResultSpec]` parses both `Integration results: <cmd> -> <report>` and `Integration results (live, needs: VAR1, VAR2): <cmd> -> <report>`.
  - `parse_integration_results(hld_text: str) -> list[str]` returns the `<cmd> -> <report>` body for every matched line (both standard and live) so existing callers (`check_epic_readiness.py` `R6` and `check_task_contract.py`) include live integration commands seamlessly.
- In `skills/dev-implementation/resources/scripts/check_task_contract.py`, `check_hld()` also checks `tc.parse_integration_result_specs(text)` and verifies that every variable in `spec.needs` is mentioned in `## Verification Environment`.
- In `skills/dev-implementation/resources/scripts/audit_epic.py`, update `GRADER_LINES = ("Protected paths:", "Integration results:", "Integration results (live")` so `hld_amendments()` detects changes to live integration lines as well.
- In `skills/dev-implementation/resources/scripts/run_external_review.py`, `collect_facts()` iterates over `parse_integration_result_specs(hld_text)`: when `spec.live` is True and any variable in `spec.needs` is unset or empty in `os.environ`, it appends `f"$ {spec.command}\nSKIPPED (missing env: {', '.join(missing)})\n"` to `results` without calling `run_gate()` and without adding `spec.report` to `reports`.
- In `skills/dev-implementation/resources/scripts/check_epic_readiness.py`, `route_matches_codebase(route: str, tracked_contents: list[str]) -> bool` returns `True` if `route` appears literally in any tracked file or if `route` matches a parameterized route template in `tracked_contents` where `{param}`, `<param>`, or `:param` segments are replaced by `[^/\s"'\`]+`.

## Definition of Done

- `task_contract.py`, `check_task_contract.py`, `check_epic_readiness.py`, `audit_epic.py`, and `run_external_review.py` support `Integration results (live, needs: VAR):` (`EVI-HP-03`). (V2, V5)
- `route_matches_codebase()` in `check_epic_readiness.py` matches concrete routes against `{id}`, `<id>`, and `:id` parameterized templates (`EVI-EC-03`). (V2, V5)
- `ruff` and `mypy` pass with zero errors. (V3, V4)
- Automated tests emit JUnit XML results covering `EVI-HP-03` and `EVI-EC-03`. (V5)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- None (Wave 1).

## References & Rollback

- Reference: [2026-11-06-execution-and-verification-infrastructure-design.en.md](../epic/execution_and_verification_infrastructure/2026-11-06-execution-and-verification-infrastructure-design.en.md).
- Rollback: `git revert` the task commit to restore prior `Integration results:` and `R5b` behavior.
