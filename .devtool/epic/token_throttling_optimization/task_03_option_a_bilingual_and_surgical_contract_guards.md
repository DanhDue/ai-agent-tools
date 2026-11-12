---
id: "task_03_option_a_bilingual_and_surgical_contract_guards"
status: "todo"
priority: "high"
assignee: null
epic: "token_throttling_optimization"
dueDate: null
created: "2026-11-13T02:30:00Z"
modified: "2026-11-13T02:30:00Z"
completedAt: null
labels: ["bilingual", "contract", "memory", "token-optimization"]
order: "a3"
---

# Task 3: Option A Bilingual Guards, Surgical Contracts, and Compact Memory

Epic: [token_throttling_optimization](token_throttling_optimization.en.md)

## Requirement Analysis

Implement Option A Bilingual Workflow guards, Surgical Target Line Range enforcement (`Rule 3`), and Scoped/Compact Memory (`--compact` + dynamic programmer prompt):
1. **Option A Bilingual Readiness & Traceability Guards**:
   - Add `--strict-bilingual` (default `False`) to `skills/dev-implementation/resources/scripts/check_epic_readiness.py` (`main`, `run_checks`, `check_preflight`, `check_bdd_scenarios`, `check_metadata`).
   - Add `--strict-bilingual` (default `False`) to `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` (`main`, `load_scenarios`, `check_plan`).
   - In default in-flight mode (`--strict-bilingual` unset):
     - Tolerate in-flight `.vi.md` drift on `R1` (`check_document.py`), `R3` (`check_bdd_scenarios`), and `R7` (`check_metadata` when checking `.vi.md` parity), and tolerate an absent `bdd_scenarios.vi.md` during Stage 2/3 development while still enforcing `.vi.md` pairing on present documents where existing parity tests require strict checks or gating under `--strict-bilingual`.
     - When `bdd_scenarios.vi.md` is present during active runs, default `check_epic_readiness` only enforces `.vi.md` strict parity when `--strict-bilingual` is passed (and preserves `test_check_bdd_traceability` / `test_check_epic_readiness` assertions explicitly testing `--strict-bilingual` or existing `.en.md` invariants).
   - Under `--strict-bilingual` (Stage 4 Pre-Finish): require complete `.en.md`/`.vi.md` parity across spec, HLD, metadata, ToC, and `bdd_scenarios.vi.md`.
2. **Exclude `.vi.md` from AI Coder Handoffs**:
   - Update `skills/dev-implementation/resources/scripts/package_epic.py` (`render_initial_handoff`, `revise_handoff_text`) and `skills/dev-lifecycle/references/handoff-template.md` so `Read First` contains strictly English SSOT paths (`<epic_dir>.en.md`, `bdd_scenarios.en.md`, `principal_review.md`) and zero `*.vi.md` files, while preserving all contract guardrails required by `scripts/test_lifecycle_document_contract.py` and `scripts/test_resume_context.py` (`resume_context.py`, `[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]`, 4 Execution Guardrails, `principal_review.md`).
3. **Surgical File Reading Gate (`check_task_contract.py --design`)**:
   - Inspect non-new tracked source/script files exceeding `200` lines listed under `Allowed files:` when `--design` is passed.
   - Require explicit symbol and/or `(L<start>-L<end>)` line-range anchors for each such `> 200`-line file inside `## Impact Analysis & Blast Radius` or `## Files`.
4. **Scoped `--compact` Context Restoration & Dynamic Programmer Prompt (`scripts/resume_context.py`)**:
   - Add `--compact` (auto-scoped when `--epic <slug>` is passed) emitting `<= 4096` bytes containing only active epic snapshot, current repo git status, matching epic tasks, and relevant open RFCs.
   - Update `emit_handoff_prompt()` to resolve Role 2.3's recommended model and effort dynamically from `.devtool/review_config.json["providers"]["programmer"]` with fallback `gemini-4-hydrogen-xhigh` (`xhigh`) instead of hardcoded `Gemini Flash 3.8`.
5. Add `tests/test_tto_bilingual_and_surgical.py` covering `TTO-HP-03`, `TTO-HP-06`, `TTO-EC-03`, `TTO-ST-02`, and `TTO-ST-03`, updating paired script test files as needed.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
- `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py`
- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`
- `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
- `skills/dev-implementation/resources/scripts/package_epic.py`
- `skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py`
- `skills/dev-lifecycle/references/handoff-template.md`
- `scripts/resume_context.py`
- `scripts/test_resume_context.py`
- `tests/test_tto_bilingual_and_surgical.py` (new)

Read-only context:
- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Module Contracts (§3)
- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios
- `scripts/test_lifecycle_document_contract.py` — Contract strings asserted on `handoff-template.md`

## Design Rationale

Decoupling in-flight `.vi.md` translation synchronization until Stage 4 prevents double rework during Principal Review rounds, while `--compact` context restoration and `> 200`-line target range validation eliminate cold-start and whole-file reading bloat in Stage 3. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/check_epic_readiness.py`: `check_preflight` (L110-L203), `check_bdd_scenarios` (L314-L343), `check_metadata` (L645-L752), `run_checks` (L830-L852), `main` (L952-L1016)
  - `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`: `load_scenarios` (L82-L100), `check_plan` (L113-L127), `main` (L228-L261)
  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `check_allowed` (L127-L154), `check_task` (L394-L417), `main` (L507-L562)
  - `skills/dev-implementation/resources/scripts/package_epic.py`: `render_initial_handoff` (L78-L116), `revise_handoff_text` (L119-L183), `package_epic` (L211-L300)
  - `scripts/resume_context.py`: `collect_harvest_data` (L1133-L1261), `emit_handoff_prompt` (L1271-L1337), `parse_args` (L1510-L1662), `main` (L1665-L1842)
  - `tests/test_tto_bilingual_and_surgical.py`: new unit and integration tests for `TTO-HP-03`, `TTO-HP-06`, `TTO-EC-03`, `TTO-ST-02`, `TTO-ST-03`
- **Downstream Callers**: `skills/dev-implementation/resources/scripts/run_external_review.py` (`check_epic_readiness.py` preflight), `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`--compact` resume, `package_epic.py`), `skills/finishing-a-development-branch/SKILL.md` (`--strict-bilingual` Stage 4 gate).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of default vs `--strict-bilingual` mode branches, `> 200`-line surgical check paths, and `--compact` byte-budget bounds.

### BDD SCENARIOS

Covers: TTO-HP-03, TTO-HP-06, TTO-EC-03, TTO-ST-02, TTO-ST-03

```gherkin
Scenario: [TTO-HP-03] [Tier C - Integration] Option A default readiness tolerates in-flight .vi.md drift and deferred bdd_scenarios.vi.md

Given an epic directory containing current *.en.md design docs and bdd_scenarios.en.md
And bdd_scenarios.vi.md is absent while an existing .vi.md companion has un-synced sections during active Principal Review
When check_epic_readiness.py runs without --strict-bilingual
Then the readiness gate succeeds with status PASS on R1, R3, and R7 without failing on .vi.md drift or missing bdd_scenarios.vi.md
And check_bdd_traceability.py validates task coverage solely against bdd_scenarios.en.md

Scenario: [TTO-HP-06] [Tier C - Integration] Compact context restoration caps output at 4096 bytes and reads programmer config dynamically

Given a multi-repo workspace directory with active epic metadata, tasks, and open RFC entries
And .devtool/review_config.json configures providers.programmer to "gemini-4-hydrogen-xhigh" with thinking_level "xhigh"
When scripts/resume_context.py runs with --compact --epic token_throttling_optimization and --emit-prompt implement
Then the compact context payload measures at most 4096 bytes and includes active epic snapshot, current repo git status, matching tasks, and relevant open RFCs
And the emitted handoff prompt specifies "gemini-4-hydrogen-xhigh" and "xhigh" read dynamically from .devtool/review_config.json

Scenario: [TTO-EC-03] [Tier C - Integration] Design contract checker rejects large >200-line modified files lacking target symbol or line-range anchors

Given a task file referencing a non-new tracked Python source file exceeding 200 lines in Allowed files
And the task's Files and Impact Analysis sections omit any target symbol name or (L<start>-L<end>) line range for that file
When check_task_contract.py executes with --design against that task file
Then check_task_contract.py exits non-zero and reports the missing symbol or line-range anchor for that >200-line file
And adding a valid "path :: Symbol (L10-L85)" anchor clears the violation and exits with status 0

Scenario: [TTO-ST-02] [Tier C - Integration] Handoff package and template exclude .vi.md files from AI coder Read First list

Given an epic directory containing spec.en.md, spec.vi.md, epic.en.md, epic.vi.md, bdd_scenarios.en.md, and bdd_scenarios.vi.md
When package_epic.py generates handoff.md from skills/dev-lifecycle/references/handoff-template.md
Then the generated Read First section references only *.en.md documents and zero *.vi.md paths
And handoff-template.md contains no static legacy model hardcodes conflicting with config-driven Role 2.3 selection

Scenario: [TTO-ST-03] [Tier C - Integration] Stage 4 --strict-bilingual readiness gate enforces full .en.md and .vi.md parity

Given an epic directory whose .vi.md HLD has drifted behind .en.md or lacks bdd_scenarios.vi.md
When check_epic_readiness.py runs with --strict-bilingual and check_bdd_traceability.py runs with --strict-bilingual
Then both commands exit non-zero highlighting the missing or out-of-sync Vietnamese mirror files
And after synchronizing .vi.md and adding bdd_scenarios.vi.md with matching IDs and ToC headings, both --strict-bilingual checks exit with status 0
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_bilingual_and_surgical.py::test_tto_hp_03_option_a_default_readiness` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_bilingual_and_surgical.py::test_tto_hp_03_option_a_default_readiness` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_bilingual_and_surgical.py skills/dev-implementation/resources/scripts/test_check_epic_readiness.py skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py skills/dev-implementation/resources/scripts/test_check_task_contract.py skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py scripts/test_resume_context.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/package_epic.py scripts/resume_context.py tests/test_tto_bilingual_and_surgical.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/package_epic.py scripts/resume_context.py tests/test_tto_bilingual_and_surgical.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_3.xml tests/test_tto_bilingual_and_surgical.py` | exit 0; results build/test-results/task_3.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `check_epic_readiness.py` (`run_checks` L830-L852, `main` L952-L1016) and `check_bdd_traceability.py` (`load_scenarios` L82-L100, `main` L228-L261) add `--strict-bilingual` (default `False`). Without `--strict-bilingual`, in-flight checks validate English SSOT docs/BDDs cleanly and tolerate `.vi.md` drift or missing `bdd_scenarios.vi.md`; with `--strict-bilingual`, full `.en.md`/`.vi.md` parity is mandatory.
- `package_epic.py` (`render_initial_handoff` L78-L116, `revise_handoff_text` L119-L183) and `skills/dev-lifecycle/references/handoff-template.md` list only English SSOT paths in `Read First`, while keeping required tokens from `scripts/test_lifecycle_document_contract.py` (`principal_review.md`, 4 Execution Guardrails, `or \`uncommitted\` when \`auto_commit\` is false`, `git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>`) and `scripts/test_resume_context.py` (`resume_context.py`, `[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]`).
- `check_task_contract.py --design` (`check_task` L394-L417) requires explicit symbol or line-range anchor (`L<start>-L<end>`) in `## Files` or `## Impact Analysis & Blast Radius` for every non-new tracked source/script file exceeding `200` lines in `Allowed files`.
- `scripts/resume_context.py --compact --epic <slug>` enforces output size `<= 4096` bytes and `emit_handoff_prompt` reads `.devtool/review_config.json["providers"]["programmer"]` with fallback `("gemini-4-hydrogen-xhigh", "xhigh")`.

## Definition of Done

- Scenarios TTO-HP-03, TTO-HP-06, TTO-EC-03, TTO-ST-02, and TTO-ST-03 pass end-to-end. (V2, V3, V6)
- Legacy tests for readiness, traceability, contract checking, packaging, and resume context remain passing. (V3)
- Python ruff lint and mypy strict type checks exit 0. (V4, V5)
- `handoff-template.md` contract guardrails preserved cleanly under visual inspection. (Gate 5)

## Dependencies & Blockers

None. Blocks [Task 4](task_04_lifecycle_runner_programmer_config_and_pool_isolation.md) and [Task 5](task_05_slimming_rules_skills_dedup_and_selective_reviewer.md).

## References & Rollback

- [Epic HLD](token_throttling_optimization.en.md), Module Contracts (§3).
- **Rollback**: Revert task commit; restores prior readiness, traceability, contract, packaging, and context scripts.

