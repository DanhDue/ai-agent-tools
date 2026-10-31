---
id: "task_3_lifecycle_skills_docs_and_verify_harness"
status: "todo"
priority: "high"
assignee: null
epic: "contract_diff_gate"
dueDate: null
created: "2026-10-31T05:43:00Z"
modified: "2026-10-31T05:43:00Z"
completedAt: null
labels: ["lifecycle", "docs", "integration", "contracts"]
order: "a3"
---

# Task 3: Update Brainstorming, Designer, Shared-Contract Skill Docs, and Lifecycle Contract Suite

Epic: [contract_diff_gate](../epic/contract_diff_gate/contract_diff_gate.en.md)

## Requirement Analysis

Update the lifecycle and shared-contract skill instructions (`dev-brainstorming`, `dev-designer`, `setup-shared-contracts`, `sync-shared-contracts`), lock those invariants into `scripts/test_lifecycle_document_contract.py`, and run full end-to-end verification across the repository (`scripts/verify.sh` and the epic-wide JUnit report).

1. **`skills/dev-brainstorming/SKILL.md`**:
   - Refine the `shared-contracts/` startup check into a strict **check and warn only** protocol: run read-only `sync_contracts.py check --domain <domain>` and `brief` only; NEVER edit contract files, NEVER run `ack`, and NEVER modify application source code during brainstorming.
   - Require presenting contract warnings (active drift, `MISSING_IN_CODE` items, or user ideas touching routes/DTOs/schemas/pipeline states) in a dedicated message and pausing for an explicit human decision on **each** warning (`include in this epic`, `split into a named follow-up epic`, or `ignore with explicit rationale`). Silence is never consent; Gate 1 cannot pass while any warning lacks a user decision.
   - Require persisting decisions (or a one-line clean `snapshot_id` / absent-`shared-contracts/` note) under `## Shared Contract Warnings` in `.en.md` and `## Cảnh báo Shared Contract` in `.vi.md`.
2. **`skills/dev-designer/SKILL.md`**:
   - Instruct Stage 2 to read `## Shared Contract Warnings` from the approved spec when planning tasks and waivers.
   - Keep canonical Hub contract edits strictly in `task_01` (Contract-First rule).
   - Require the **final task** (running before Gate 4) to include `.agents/contract_sync.json` (for `ack`) and, when waivers are planned, `.agents/contract_map.json` in `Allowed files` so the Gate 4 commit SHA stays immutable.
3. **`skills/setup-shared-contracts/SKILL.md` & `skills/sync-shared-contracts/SKILL.md`**:
   - In `skills/setup-shared-contracts/SKILL.md`, document `resources/templates/contract_map.json.tmpl` (satisfying `scripts/verify.sh` Check 8 supporting-file reference check) and explain how target repositories configure `.agents/contract_map.json` globs manually rather than relying on guessed globs.
   - In `skills/sync-shared-contracts/SKILL.md`, document `sync_contracts.py diff-check` (`--repo-root`, `--base-ref`, `--domain`, `--json`), exit codes `0`/`1`/`2`, `.agents/contract_map.json` schema, Hub vs Satellite diff rules, immutable waiver diff semantics, and `{skills_dir}` / `{base_ref}` Gate 4 wiring.
4. **Contract Test Suite & Full Epic Integration (`scripts/test_lifecycle_document_contract.py`)**:
   - Extend `EXPECTED` / test methods (`test_cdg_hp_04_...`) in `scripts/test_lifecycle_document_contract.py` to enforce the new `dev-brainstorming`, `dev-designer`, `setup-shared-contracts`, and `sync-shared-contracts` document contracts.
   - Verify no diagram code fences exist in runtime `SKILL.md` files (`check_document.py` + `scripts/verify.sh`).

## Files

Allowed files:
- `skills/dev-brainstorming/SKILL.md`
- `skills/dev-designer/SKILL.md`
- `skills/setup-shared-contracts/SKILL.md`
- `skills/sync-shared-contracts/SKILL.md`
- `scripts/test_lifecycle_document_contract.py`

Read-only context:
- `.devtool/epic/contract_diff_gate/contract_diff_gate.en.md` — HLD specifications
- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` — implemented `diff-check` CLI
- `skills/setup-shared-contracts/resources/templates/contract_map.json.tmpl` (new) — reference contract map template created in Task 1
- `scripts/verify.sh` — pre-release verification suite (Check 8 supporting files, Check 11–15 unit/integration tests)

## Design Rationale

- Locking the read-only brainstorming warning + human confirmation gate and final-task `Allowed files` rule into `scripts/test_lifecycle_document_contract.py` prevents future edits from accidentally regressing these governance rules.
- Runtime `SKILL.md` files use prose/tables/CLI examples without Mermaid diagram fences so they continue passing `test_lifecycle_document_contract.py`'s runtime-skill diagram prohibition.
- Applicable skills: `d3nexus:writing-skills`, `d3nexus:doc_quality_check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `skills/dev-brainstorming/SKILL.md`, `skills/dev-designer/SKILL.md`, `skills/setup-shared-contracts/SKILL.md`, `skills/sync-shared-contracts/SKILL.md`, and `scripts/test_lifecycle_document_contract.py` (`EXPECTED`, `test_cdg_hp_04_contract_diff_gate_lifecycle_docs`).
- **Downstream Callers**: All future epics across `D3Nexus`, `lyrics-sync`, `nexus`, and `ai-agent-tools` invoking `dev-brainstorming`, `dev-designer`, `setup-shared-contracts`, or `sync-shared-contracts`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% assertion coverage of lifecycle document contract invariants and 100% pass across `scripts/verify.sh`.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: CDG-HP-04

```gherkin
Scenario: [CDG-HP-04] [Tier C - Integration] Lifecycle Document Contracts, Template Reference, and Verify Harness Pass
  Given the contract_map.json.tmpl template in setup-shared-contracts and the updated SKILL.md files in setup-shared-contracts, sync-shared-contracts, dev-brainstorming, and dev-designer
  When the engineer executes scripts/test_lifecycle_document_contract.py and scripts/verify.sh
  Then dev-brainstorming enforces read-only contract check/brief warnings, mandatory per-warning human confirmation, and bilingual "## Shared Contract Warnings" / "## Cảnh báo Shared Contract" persistence
  And dev-designer enforces reading "## Shared Contract Warnings", Hub task_01 Contract-First ordering, and final-task Allowed files entries for .agents/contract_sync.json and .agents/contract_map.json
  And setup-shared-contracts documents contract_map.json.tmpl and scripts/verify.sh exits with code 0
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest scripts/test_lifecycle_document_contract.py -k test_cdg_hp_04` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest scripts/test_lifecycle_document_contract.py` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V4 | TIER-B | `mypy --follow-imports=silent scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V5 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-brainstorming/SKILL.md skills/dev-designer/SKILL.md skills/setup-shared-contracts/SKILL.md skills/sync-shared-contracts/SKILL.md` | exit 0; contains "0 findings" | — |
| V6 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
| V7 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/contract-diff-gate.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py skills/python-quality-check/resources/scripts/test_validate_python_quality.py skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py skills/android-quality-check/resources/scripts/test_validate_android_quality.py skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py scripts/test_lifecycle_document_contract.py` | exit 0; results build/test-results/contract-diff-gate.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Any runtime `SKILL.md` introduces a Mermaid or Graphviz diagram fence (prohibited in runtime skills by `test_lifecycle_document_contract.py`).

## Decisions Already Made

- Grounded test contract in `scripts/test_lifecycle_document_contract.py`: extend `EXPECTED` entries for `skills/dev-brainstorming/SKILL.md` and `skills/dev-designer/SKILL.md` and add `test_cdg_hp_04_...` asserting `contract_map.json.tmpl` reference in `skills/setup-shared-contracts/SKILL.md` and `diff-check` documentation in `skills/sync-shared-contracts/SKILL.md`.
- Do NOT touch `skills/principal-review/` or `skills/cross-model-review/` (explicitly excluded from this epic's scope).
- `skills/setup-shared-contracts/SKILL.md` must explicitly name `contract_map.json.tmpl` in prose/code so `scripts/verify.sh` Check 8 (`supporting files are referenced`) passes.

## Definition of Done

- `dev-brainstorming/SKILL.md`, `dev-designer/SKILL.md`, `setup-shared-contracts/SKILL.md`, and `sync-shared-contracts/SKILL.md` are updated and pass `check_document.py` with zero findings (V5).
- `scripts/test_lifecycle_document_contract.py` passes including `test_cdg_hp_04` and passes `ruff check` and `mypy` (V2, V3, V4).
- `bash scripts/verify.sh` exits `0` with `"PASS — safe to publish"` across all 15 verification checks (V6).
- Unified JUnit XML report `build/test-results/contract-diff-gate.xml` passes all 15 `CDG-*` scenarios across the epic (V7).
- Skill clarity and scope boundaries reviewed at Kanban sign-off (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 1](task_1_contract_map_and_diff_check_cli.md)
- Blocked by [Task 2](task_2_quality_providers_schemas_and_placeholders.md)

## References & Rollback

- Spec: `.devtool/epic/contract_diff_gate/2026-10-31-contract-diff-gate-design.en.md`
- HLD: `.devtool/epic/contract_diff_gate/contract_diff_gate.en.md`
- Rollback: Revert edits to the 4 `SKILL.md` files and `scripts/test_lifecycle_document_contract.py`.
