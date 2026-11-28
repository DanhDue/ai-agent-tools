---
id: "task_05_lean_skills_verify_registry_and_acceptance"
status: "done"
priority: "high"
assignee: null
epic: "shift_left_quality_resolver"
dueDate: null
created: "2026-11-28T10:10:00+07:00"
modified: "2026-11-28T05:24:07Z"
completedAt: "2026-11-28T05:24:07Z"
labels: ["architecture", "contract", "skills", "acceptance"]
order: "a05"
review_tier: "full"
---

# Task 05: Lean Skill Integration, Legacy Row Cleanup, verify.sh Registration, and Five-Repo Acceptance

Epic: [shift_left_quality_resolver](../../epic/shift_left_quality_resolver/shift_left_quality_resolver.md)

## Requirement Analysis

Wire the mechanical Shift-Left quality resolver (`d3nexus resolve-quality --files <planned_files>`) and standalone plan checker (`check_task_contract.py --check-plan <plan.md>`) into `dev-designer` and `writing-plans` in 2–3 compact lines (zero prose matrices), remove retired repository-specific script names from `dev-designer/SKILL.md` and `dev-designer/references/verification-rows.md` (`#0020`), document `gate4_receipt.json` clean-tree preconditions and `--package-floors` / `test_routing` in `finishing-a-development-branch`, `quality_check`, and `setup_quality_check`, register all five `SLQR` test suites in `scripts/verify.sh`, and prove end-to-end clean-shell Pre-Flight execution plus synthetic 5-repo fixtures and optional `SLQR_ECOSYSTEM_ROOT` profile validations (all discovered profiles PASS).

## Files

Allowed files:
- `skills/dev-designer/SKILL.md`
- `skills/dev-designer/references/verification-rows.md`
- `skills/writing-plans/SKILL.md`
- `skills/writing-plans/plan-document-reviewer-prompt.md`
- `skills/finishing-a-development-branch/SKILL.md`
- `skills/quality_check/SKILL.md`
- `skills/setup_quality_check/SKILL.md`
- `scripts/verify.sh`
- `tests/test_slqr_end_to_end_acceptance.py` (new)

Read-only context:
- `.devtool/epic/shift_left_quality_resolver/shift_left_quality_resolver.md`
- `.devtool/epic/shift_left_quality_resolver/bdd_scenarios.md`
- `skills/task-observer/references/skill-authoring.md`
- `tests/test_tto_docs_and_slimming.py`
- `tests/test_ohk2_skill_docs.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:writing-skills`, `d3nexus:doc_quality_check`, and `task-observer/references/skill-authoring.md` (Progressive Disclosure + Pre-Flight Principle: execute every embedded CLI command verbatim from a clean subprocess environment).
- Keep `skills/dev-designer/SKILL.md` strictly `<= 22528` UTF-8 bytes (`tests/test_tto_docs_and_slimming.py:L61`) and preserve `-q --tb=short --maxfail=3` in `verification-rows.md` (`L77`).

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-designer/SKILL.md` (`L31`, `L54`, `L60`): add `d3nexus resolve-quality --files <planned_files>` in Step 1.3 & Step 2.5, replace "copy `type_check`/`lint` verbatim" with `$D3NEXUS_KIT/skills`-interpolated scoped `TIER-B` resolution, and replace retired script names (`verify_importlinter_coverage.py`, `verify_bdd_coverage.py`, `pre_review_self_probe.py`) in Step 2.3 with manifest-registered `boundaries`/`architecture`/`check` gates.
  - `skills/dev-designer/references/verification-rows.md` (`L30-L35`, `L79`): document `d3nexus resolve-quality --files ...` and replace retired scripts in Python `Task N` `V4 | TIER-B`.
  - `skills/writing-plans/SKILL.md` (`L58-L61`, `L175-L180`, `L223-L229`) & `skills/writing-plans/plan-document-reviewer-prompt.md` (`L20-L28`): replace "copy verbatim" with `d3nexus resolve-quality --files <planned_files>` and add `check_task_contract.py --check-plan <plan.md>` to Self-Review and Reviewer checks.
  - `skills/finishing-a-development-branch/SKILL.md` (`L196-L202`), `skills/quality_check/SKILL.md` (`L77`, `L137-L140`), `skills/setup_quality_check/SKILL.md` (`L16`): document clean working-tree requirement for `noop` receipt reuse, non-PASS `gate4_receipt.json` invalidation, `--package-floors`, `test_routing`, and deduplicated `epic`/`release` scaffolding.
  - `scripts/verify.sh` (`L360-L569`): register all 5 `tests/test_slqr_*.py` suites.
  - `tests/test_slqr_end_to_end_acceptance.py` (new): clean-shell Pre-Flight CLI tests, UTF-8 byte/word cap checks, `check_document.py --require-toc` checks, and synthetic 5-repo fixtures plus optional `SLQR_ECOSYSTEM_ROOT` profiles (all discovered profiles PASS) schema+validator parity tests covering `SLQR-HP-05` and `SLQR-AR-04`.
- **Downstream Callers**: `tests/test_tto_docs_and_slimming.py`, `tests/test_ohk2_skill_docs.py`, `scripts/test_lifecycle_document_contract.py`.
- **Cross-Platform Bridges**: None.
- **Target Coverage Threshold**: 100% pass across all 5 `SLQR` suites and `scripts/verify.sh`.

### BDD SCENARIOS

Covers: SLQR-HP-05, SLQR-AR-04

```gherkin
Scenario: [SLQR-HP-05] [Tier C - Integration] Updated skills pass byte/word caps, clean-shell Pre-Flight execution, and multi-stack ecosystem profile validations
Given the updated skill files ("dev-designer/SKILL.md", "dev-designer/references/verification-rows.md", "writing-plans/SKILL.md", "writing-plans/plan-document-reviewer-prompt.md", "finishing-a-development-branch/SKILL.md") and "scripts/verify.sh"
When clean-shell Pre-Flight commands, check_document.py --require-toc, UTF-8 byte/word cap checks, and 5-repo ecosystem manifest validations (via optional SLQR_ECOSYSTEM_ROOT or synthetic 5-repo polyglot fixtures) execute
Then "skills/dev-designer/SKILL.md" stays <= 22528 UTF-8 bytes, retired script names ("verify_importlinter_coverage.py", "pre_review_self_probe.py", "verify_bdd_coverage.py") do not appear in "dev-designer", all discovered ecosystem profiles return "PASS" with zero personal-path leaks in tracked files, and embedded CLI commands exit 0 in a clean env shell

Scenario: [SLQR-AR-04] [Tier C - Integration] Authoring skills integrate CLI resolver in 2-3 lines without embedding multi-stack prose matrices
Given "skills/dev-designer/SKILL.md" and "skills/writing-plans/SKILL.md"
When their diff and content are audited
Then both files reference "resolve-quality" (or "resolve_task_quality_plan.py"), "writing-plans/SKILL.md" and "plan-document-reviewer-prompt.md" reference "--check-plan", and neither skill embeds a multi-stack coverage floor table
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_end_to_end_acceptance.py::test_slqr_hp_05_skills_pass_caps_preflight_and_ecosystem_parity` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_end_to_end_acceptance.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_docs_and_slimming.py tests/test_ohk2_skill_docs.py scripts/test_lifecycle_document_contract.py tests/test_slqr_registry_and_schemas.py tests/test_slqr_receipt_coverage_and_scaffolder.py tests/test_slqr_quality_plan_resolver.py tests/test_slqr_task_and_plan_contracts.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_slqr_end_to_end_acceptance.py && ruff format --check tests/test_slqr_end_to_end_acceptance.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_slqr_end_to_end_acceptance.py --ignore-missing-imports --follow-imports=silent && python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-designer/SKILL.md skills/dev-designer/references/verification-rows.md skills/writing-plans/SKILL.md skills/writing-plans/plan-document-reviewer-prompt.md skills/finishing-a-development-branch/SKILL.md skills/quality_check/SKILL.md skills/setup_quality_check/SKILL.md && bash scripts/verify.sh --quiet` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_slqr_registry_and_schemas.py tests/test_slqr_receipt_coverage_and_scaffolder.py tests/test_slqr_quality_plan_resolver.py tests/test_slqr_task_and_plan_contracts.py tests/test_slqr_end_to_end_acceptance.py --junitxml=build/test-results/shift-left-quality-resolver.xml` | exit 0; results build/test-results/shift-left-quality-resolver.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`tests/test_tto_docs_and_slimming.py` `L60-L78`, `tests/test_ohk2_skill_docs.py` `L1-L91`, `scripts/verify.sh` `L100-L165` & `L360-L569`)**: `dev-designer/SKILL.md` must stay `<= 22528` UTF-8 bytes with frontmatter keys `["name", "description"]`; `verification-rows.md` must retain `-q --tb=short --maxfail=3`; `test_ohk2_skill_docs.py` checks Playwright / `DevToolsActivePort` & sequential `TIER-B` wording — preserve all asserted substrings intact.
- **New contract**:
  - **Zero Personal-Path Leaks (`tests/test_plq_end_to_end_acceptance.py:115-119`)**: Never hard-code `/Users/...` or personal usernames in `tests/test_slqr_end_to_end_acceptance.py` or any tracked file! Instead, build a comprehensive 5-repo polyglot synthetic fixture suite inside `tmp_path` (`rust+web+python` monorepo, `python+vanilla-js` LCOV repo, `flutter+python` workspace, `android` Gradle repo, `ios` Tuist/mise repo) validating `PASS` across every profile (`> 0` profiles asserted), AND optionally scan `os.environ.get("SLQR_ECOSYSTEM_ROOT")` when set in the environment (asserting every discovered `.agents/quality/check_quality.json` profile returns `PASS`).
  - Clean-shell Pre-Flight executes literal commands with `env={"PATH": os.environ["PATH"], "HOME": str(tmp_path), "D3NEXUS_KIT": str(REPO_ROOT)}` to verify zero reliance on ambient shell state.

## Definition of Done

- [x] `dev-designer/SKILL.md`, `verification-rows.md` (`#0020`), `writing-plans/SKILL.md`, `plan-document-reviewer-prompt.md`, `finishing-a-development-branch/SKILL.md`, `quality_check/SKILL.md`, and `setup_quality_check/SKILL.md` are updated concisely within byte/word caps and pass `check_document.py` (V2, V3, V4) — exit 0, `dev-designer/SKILL.md` <= 22528 UTF-8 bytes, `check_document.py` + `--require-toc` PASS
- [x] `scripts/verify.sh` registers all 5 `tests/test_slqr_*.py` suites and `bash scripts/verify.sh --quiet` exits `0` (V4) — exit 0, Section 27 registered and all verify.sh suites PASS
- [x] Clean-shell Pre-Flight execution and 6-stack schema-vs-validator parity pass across `SLQR-HP-05` and `SLQR-AR-04` with JUnit XML written to `build/test-results/shift-left-quality-resolver.xml` (V2, V5) — exit 0, 5/5 acceptance tests & 2/2 BDD traceability PASS
- [x] All regression and SLQR suites pass without regressions (V3, V5) — exit 0, 139 regression tests + all 5 SLQR suites PASS

## Dependencies & Blockers

- Blocked by [Task 01](../../epic/shift_left_quality_resolver/task_01_registry_prefix_wrappers_and_provider_schemas.md), [Task 02](../../epic/shift_left_quality_resolver/task_02_receipt_hygiene_diff_coverage_and_scaffolder.md), [Task 03](../../epic/shift_left_quality_resolver/task_03_on_demand_quality_plan_resolver_cli.md), [Task 04](../../epic/shift_left_quality_resolver/task_04_fail_closed_task_and_plan_contract_guards.md)

## References & Rollback

- Reference HLD: [shift_left_quality_resolver.md](../../epic/shift_left_quality_resolver/shift_left_quality_resolver.md)
- Rollback: Revert modified `SKILL.md` / `references/` files and `scripts/verify.sh`, and delete `tests/test_slqr_end_to_end_acceptance.py`.
