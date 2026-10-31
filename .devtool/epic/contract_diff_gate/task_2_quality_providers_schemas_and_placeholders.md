---
id: "task_2_quality_providers_schemas_and_placeholders"
status: "todo"
priority: "high"
assignee: null
epic: "contract_diff_gate"
dueDate: null
created: "2026-10-31T05:43:00Z"
modified: "2026-10-31T05:43:00Z"
completedAt: null
labels: ["quality-check", "schemas", "providers"]
order: "a2"
---

# Task 2: Align Quality Provider Schemas, {skills_dir} and {base_ref} Placeholders, and BLOCKED Exit Mapping

Epic: [contract_diff_gate](contract_diff_gate.en.md)

## Requirement Analysis

Update the JSON schemas, provider skill instructions, capability contract references, and validator unit tests across all five quality providers (`rust`, `python`, `flutter`, `android`, `ios`) so every platform supports `contracts`, `contracts_<domain>`, `contract_diff`, `{skills_dir}` and `{base_ref}` argument expansion, and exit-code `2` -> `BLOCKED` mapping.

1. **JSON Schemas (`resources/schemas/*-quality.schema.json` across `rust`, `python`, `flutter`, `android`, `ios`)**:
   - In `properties.capabilities.properties`, add string-array command definitions (`{"type": "array", "items": {"type": "string"}, "minItems": 1}`) for `"contracts"` and `"contract_diff"`.
   - In `properties.capabilities`, add `"patternProperties": {"^contracts_[a-z0-9_]+$": {"type": "array", "items": {"type": "string"}, "minItems": 1}}` while keeping `"additionalProperties": false` so multi-domain Hub capabilities (`contracts_lyrics_sync`, `contracts_nexus`) conform to JSON Schema Draft-07 / 2020-12.
   - In `skills/rust-quality-check/resources/schemas/rust-quality.schema.json`, also add `"db_hygiene"` (`{"type": "array", "items": {"type": "string"}, "minItems": 1}`) so `D3Nexus`'s existing `rust-quality.json` conforms cleanly.
2. **Provider Skill Instructions & References**:
   - Update `SKILL.md` in all five providers (`rust-quality-check`, `python-quality-check`, `flutter-quality-check`, `android-quality-check`, `ios-quality-check`) and `references/{rust,python}-capability-contract.md` in the two providers that maintain separate contract reference files:
     - Document `{skills_dir}/...` prefix substitution (resolving `{skills_dir}` to the parent `skills/` directory of the active quality provider skill).
     - Document `{base_ref}` argument placeholder substitution (expanding `{base_ref}` from `quality_check`'s normalized `base_ref` invocation parameter, falling back to `develop` or repository default only when `base_ref` was not supplied).
     - Document exit-code `2` (or JSON `"status": "BLOCKED"`) -> check status `BLOCKED` mapping (`0` -> `PASS`, `1` -> `FAIL`, `2` -> `BLOCKED`) for governance/contract capabilities such as `contract_diff`.
3. **Validator & Schema Unit Tests (`test_validate_*_quality.py`)**:
   - Add test cases covering `[CDG-HP-03]` across all five `test_validate_*_quality.py` suites verifying both `validate_*_config()` acceptance of `contracts`, `contracts_lyrics_sync`, `contract_diff` (with `{skills_dir}` and `{base_ref}` arguments), and `db_hygiene` (for Rust), and structural assertions on `*-quality.schema.json` (`contracts`, `contract_diff`, `patternProperties["^contracts_[a-z0-9_]+$"]`, and `db_hygiene`).
   - Clean up any unused `# noqa: E402` directives in `test_validate_*_quality.py` so `ruff check` exits `0`.

## Files

Allowed files:
- `skills/rust-quality-check/SKILL.md`
- `skills/rust-quality-check/references/rust-capability-contract.md`
- `skills/rust-quality-check/resources/schemas/rust-quality.schema.json`
- `skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py`
- `skills/python-quality-check/SKILL.md`
- `skills/python-quality-check/references/python-capability-contract.md`
- `skills/python-quality-check/resources/schemas/python-quality.schema.json`
- `skills/python-quality-check/resources/scripts/test_validate_python_quality.py`
- `skills/flutter-quality-check/SKILL.md`
- `skills/flutter-quality-check/resources/schemas/flutter-quality.schema.json`
- `skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py`
- `skills/android-quality-check/SKILL.md`
- `skills/android-quality-check/resources/schemas/android-quality.schema.json`
- `skills/android-quality-check/resources/scripts/test_validate_android_quality.py`
- `skills/ios-quality-check/SKILL.md`
- `skills/ios-quality-check/resources/schemas/ios-quality.schema.json`
- `skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py`

Read-only context:
- `.devtool/epic/contract_diff_gate/contract_diff_gate.en.md` — HLD specifications
- `skills/quality_check/SKILL.md` — common quality orchestrator contract (`base_ref`, `BLOCKED` aggregation)
- `skills/rust-quality-check/resources/scripts/validate_rust_quality.py` — Rust config validator
- `skills/python-quality-check/resources/scripts/validate_python_quality.py` — Python config validator
- `skills/flutter-quality-check/resources/scripts/validate_flutter_quality.py` — Flutter config validator
- `skills/android-quality-check/resources/scripts/validate_android_quality.py` — Android config validator
- `skills/ios-quality-check/resources/scripts/validate_ios_quality.py` — iOS config validator

## Design Rationale

- Keeping `"additionalProperties": false` while explicitly adding `"contracts"`, `"contract_diff"`, and `"patternProperties": {"^contracts_[a-z0-9_]+$": ...}` preserves strict typo detection in `.agents/quality/*-quality.json` while supporting single-domain Satellites and multi-domain Hubs.
- Propagating `{skills_dir}`, `{base_ref}`, and `2 -> BLOCKED` uniformly across all five `*-quality-check` sibling skills prevents skill-family divergence across Rust, Python, Flutter, Android, and iOS repositories.
- Applicable skills: `d3nexus:writing-skills`, `d3nexus:test-driven-development`, `d3nexus:doc_quality_check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: Five `*-quality.schema.json` files, five `*-quality-check/SKILL.md` files, two `references/*-capability-contract.md` files, and five `test_validate_*_quality.py` suites.
- **Downstream Callers**: `quality_check` orchestrator and downstream repositories (`D3Nexus`, `lyrics-sync`, `nexus`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% coverage of new schema properties, patternProperties, and placeholder capability array validation across all five providers.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: CDG-HP-03

```gherkin
Scenario: [CDG-HP-03] [Tier C - Integration] Quality Provider Schemas, Placeholders, and Exit Code 2 Mapping Verification
  Given the updated *-quality.schema.json files and SKILL.md contracts across rust, python, flutter, android, and ios quality providers
  When the engineer runs the five test_validate_*_quality.py test suites
  Then every provider schema permits capabilities "contracts", "contract_diff", and pattern "^contracts_[a-z0-9_]+$" (and rust-quality.schema.json permits "db_hygiene")
  And every provider validator accepts capability arrays using "{skills_dir}" and "{base_ref}" placeholders and documents exit code 2 mapping to status "BLOCKED"
  And all five validator test suites exit with code 0
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py -k test_cdg_hp_03` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py skills/python-quality-check/resources/scripts/test_validate_python_quality.py skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py skills/android-quality-check/resources/scripts/test_validate_android_quality.py skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py skills/python-quality-check/resources/scripts/test_validate_python_quality.py skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py skills/android-quality-check/resources/scripts/test_validate_android_quality.py skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py` | exit 0 | — |
| V4 | TIER-B | `mypy --follow-imports=silent skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py skills/python-quality-check/resources/scripts/test_validate_python_quality.py skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py skills/android-quality-check/resources/scripts/test_validate_android_quality.py skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py` | exit 0 | — |
| V5 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/rust-quality-check/SKILL.md skills/rust-quality-check/references/rust-capability-contract.md skills/python-quality-check/SKILL.md skills/python-quality-check/references/python-capability-contract.md skills/flutter-quality-check/SKILL.md skills/android-quality-check/SKILL.md skills/ios-quality-check/SKILL.md` | exit 0; contains "0 findings" | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py skills/python-quality-check/resources/scripts/test_validate_python_quality.py skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py skills/android-quality-check/resources/scripts/test_validate_android_quality.py skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py` | exit 0; results build/test-results/task_2.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Any `SKILL.md` frontmatter is altered to include keys other than `name` and `description`.

## Decisions Already Made

- All five `resources/schemas/*-quality.schema.json` retain `"additionalProperties": false` on `properties.capabilities` and add `"contracts"`, `"contract_diff"`, and `"patternProperties": {"^contracts_[a-z0-9_]+$": {"type": "array", "items": {"type": "string"}, "minItems": 1}}`; `rust-quality.schema.json` additionally defines `"db_hygiene"`.
- Only `rust-quality-check` and `python-quality-check` maintain `references/{rust,python}-capability-contract.md`; `flutter-quality-check`, `android-quality-check`, and `ios-quality-check` document `{skills_dir}`, `{base_ref}`, and `2 -> BLOCKED` directly inside their `SKILL.md` files (do not create unreferenced `references/` files).
- Grounded validators (`validate_rust_config`, `validate_python_config`, `validate_flutter_config`, `validate_android_config`, `validate_ios_config`) remain untouched because they already validate arbitrary string-array capabilities.

## Definition of Done

- All five `*-quality.schema.json` manifests define `contracts`, `contract_diff`, and `^contracts_[a-z0-9_]+$` (plus `db_hygiene` on Rust) and pass all five `test_validate_*_quality.py` suites (V2).
- All five provider `SKILL.md` files and the two `*-capability-contract.md` files document `{skills_dir}`, `{base_ref}`, and exit code `2` -> `BLOCKED` with zero `check_document.py` findings (V5).
- `ruff check` and `mypy` pass cleanly across all five test suites (V3, V4).
- JUnit XML report `build/test-results/task_2.xml` passes `CDG-HP-03` (V6).
- Provider parity across all five platforms verified at Kanban sign-off (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 1](task_1_contract_map_and_diff_check_cli.md)

## References & Rollback

- Spec: `.devtool/epic/contract_diff_gate/2026-10-31-contract-diff-gate-design.en.md`
- HLD: `.devtool/epic/contract_diff_gate/contract_diff_gate.en.md`
- Rollback: Revert the 17 quality provider schema, skill, reference, and test files.
