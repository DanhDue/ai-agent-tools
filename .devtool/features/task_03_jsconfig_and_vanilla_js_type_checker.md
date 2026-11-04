---
id: "task_03_jsconfig_and_vanilla_js_type_checker"
status: "todo"
priority: "medium"
assignee: null
epic: "web-quality-check-and-integration-gate"
dueDate: null
created: "2026-11-04T22:52:00Z"
modified: "2026-11-04T22:52:00Z"
completedAt: null
labels: ["vanilla-js", "typecheck", "tooling"]
order: "a3"
---

# Task 03: Vanilla JS JSDoc Type-Checking Configuration

Epic: [web_quality_check_and_integration_gate](../epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md)

## Requirement Analysis

Provide in-place type checking tooling for static Vanilla JavaScript codebases (such as `lyrics-sync/src/lyrics_sync/preview/static/`) without migrating files to `.ts`. Supply a canonical `jsconfig.json` template enabling `checkJs` and strict type analysis via JSDoc annotations, accompanied by the `check_vanilla_js.py` execution wrapper for the `type_check` capability.

## Files

Allowed files:
- `skills/web-quality-check/resources/templates/jsconfig.template.json` (new)
- `skills/web-quality-check/resources/scripts/check_vanilla_js.py` (new)
- `tests/test_vanilla_js_checker.py` (new)

Read-only context:
- `skills/web-quality-check/SKILL.md` (new in Task 01)
- `docs/refresh-session-quick-guide.en.md` (documentation guide)

## Design Rationale

Vanilla JavaScript codebases often suffer from silent runtime bugs due to misspelled variable names, missing function parameters, or null reference errors on DOM nodes. Migrating these files to TypeScript involves substantial build overhead. Using TypeScript's built-in `checkJs` mode via `jsconfig.json` provides compile-time safety and catches nullability bugs without changing runtime deployment semantics.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `jsconfig.template.json`, `check_vanilla_js.py`.
- **Downstream Callers**: `web-quality-check` provider running `type_check` on static JavaScript files.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 85\%$ for `check_vanilla_js.py`.

### BDD SCENARIOS

Covers: [WQG-HP-02]

#### Scenario: [WQG-HP-02] [Tier C - Integration] Vanilla JavaScript type-checking via JSDoc configuration
Given a repository containing Vanilla JavaScript files in `preview/static/`
And a `jsconfig.json` configured with `"checkJs": true`
When `web-quality-check` executes the `type_check` capability
Then the TypeScript compiler validates all JavaScript files without emitting errors
And passes without requiring any `.ts` file renaming.

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest tests/test_vanilla_js_checker.py::test_jsconfig_discovery` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest tests/test_vanilla_js_checker.py::test_jsconfig_discovery` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check tests/test_vanilla_js_checker.py skills/web-quality-check` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/check_vanilla_js.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest tests/test_vanilla_js_checker.py -k "test_WQG_HP_02" --junitxml=build/test-results/task_03.xml` | exit 0; results build/test-results/task_03.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Compiler configuration: `compilerOptions: { "checkJs": true, "noEmit": true, "target": "ES2022", "moduleResolution": "node" }`.
- Target files: `src/**/*.js` or configured include glob.
- Execution binary: `npx tsc --project <path_to_jsconfig>`.

## Definition of Done

- `jsconfig.template.json` provides a turn-key configuration for Vanilla JS type checking. (V2)
- `check_vanilla_js.py` passes ruff linting and mypy typing. (V3, V4)
- Scenario [WQG-HP-02] fully verified and passing. (V5)
- Clean git status with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by: [Task 01](task_01_web_quality_check_skill_and_contract.md).

## References & Rollback

- Reference: [TypeScript JSDoc Reference](https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html).
- Rollback: Revert `jsconfig.template.json` and checker script.
