---
id: "task_03_review_prompts_and_triage_prefill"
status: "backlog"
priority: "high"
assignee: null
epic: "check_quota_dynamic_models_and_review_action"
dueDate: null
created: "2026-11-18T03:11:00Z"
modified: "2026-11-18T03:11:00Z"
completedAt: null
labels: ["review-pipeline", "architecture", "contract"]
order: "a3"
review_tier: "full"
---

# Task 3: Review Prompts `. Proposed:` Contract & `run_external_review.py` Pre-Filled Triage

Epic: [check_quota_dynamic_models_and_review_action](../epic/check_quota_dynamic_models_and_review_action/check_quota_dynamic_models_and_review_action.en.md)

## Requirement Analysis

Align external and local code review prompt contracts with Principal Review by emitting `. Proposed: <edit>`, and update `run_external_review.py` so triage and Top Risk summaries pre-fill extracted proposals while preserving 5-column persisted `review_results.md` tables:

1. **Prompt Contract Alignment (`external-review-prompt.md`, `local-review-prompt.md`)**:
   - Update finding format templates in `skills/dev-implementation/references/external-review-prompt.md` and `skills/dev-implementation/references/local-review-prompt.md` from `[Critical|Important|Minor] <artefact>:<location> — <problem>` to match `skills/principal-review/references/principal-review-prompt.md`:
     `[Critical|Important|Minor] <artefact>:<location> — <problem>. Proposed: <edit>`
2. **Pre-Fill Proposals Without Breaking 5-Column `check()` (`skills/dev-implementation/resources/scripts/run_external_review.py`)**:
   - Keep `render_round()` (`L1283-L1313`), `check()` (`L2230-L2251`), and `finding_rows()` (`L2306-L2307`) enforcing strictly 5-column markdown tables (`| # | Severity | Location | Problem | Decision |`) in persisted `review_results.md`.
   - Extract `. Proposed: <edit>` via shared helper `_extract_proposed_action()` using the pinned marker regex `re.compile(r"(?:^|(?:[.;—]|\n)\s*)\b(?:Proposed(?:\s+action)?|Fix|Suggestion|Đề xuất):\s*", re.IGNORECASE)` applied to the **last** `finditer()` match, and pre-fill the `Proposed action` column cell in `top_risk_findings_section()` (`L2407-L2431`) and `triage()` (`L2515-L2624`) stdout tables (`?` only when omitted; `triage()` prints only to stdout at `L2623` and never writes `fix_plan_round<N>.md`).
   - Preserve `parse_findings()` (`L1224-L1235`) retaining full finding tuples so inline `. Proposed: <edit>` survives into the persisted 5-column `Problem` cell for downstream dashboard parsing.
3. **Unit Suite (`tests/test_cqra_external_review_proposed.py`)**:
   - Cover scenarios `CQRA-HP-04` and `CQRA-EC-04`.

## Files

Allowed files:
- `skills/dev-implementation/references/external-review-prompt.md`
- `skills/dev-implementation/references/local-review-prompt.md`
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `tests/test_cqra_external_review_proposed.py` (new)

Read-only context:
- `.devtool/epic/check_quota_dynamic_models_and_review_action/check_quota_dynamic_models_and_review_action.en.md` — Epic HLD & Contracts
- `.devtool/epic/check_quota_dynamic_models_and_review_action/bdd_scenarios.en.md` — Canonical BDD Scenarios
- `skills/principal-review/references/principal-review-prompt.md` — Canonical `. Proposed: <edit>` reference

## Design Rationale

Preserving 5 columns (`len(cells) == 5`) inside persisted `review_results.md` maintains full backward compatibility with `run_external_review.py check()`, `lifecycle_runner.py`, and existing test suites while ensuring future reviews supply concrete edit proposals in both `review_results.md` and stdout triage tables (`top_risk_findings_section()` and `triage()` `## Findings`). Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/references/external-review-prompt.md`: finding output specification
  - `skills/dev-implementation/references/local-review-prompt.md`: finding output specification
  - `skills/dev-implementation/resources/scripts/run_external_review.py`: `parse_findings` (L1224-L1235), `render_round` (L1283-L1313), `check` (L2230-L2251), `finding_rows` (L2306-L2307), `top_risk_findings_section` (L2407-L2431), `triage` (L2515-L2624), new _extract_proposed_action
  - `tests/test_cqra_external_review_proposed.py`: new unit test suite
- **Downstream Callers**: Task 05 (`tasks_server.py`), `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`, `skills/dev-implementation/resources/scripts/test_run_external_review.py`, `skills/dev-implementation/resources/scripts/test_local_review.py`, `tests/test_tto_external_review.py`.
- **Cross-Platform Bridges**: Markdown table / `. Proposed: <edit>` wire contract consumed by `tasks_server.py::parse_review_results`.
- **Target Test Coverage Threshold**: 100% of prompt format check, 5-column persistence, proposal pre-fill, and `?` fallback branches.

### BDD SCENARIOS

Covers: CQRA-HP-04, CQRA-EC-04

```gherkin
Scenario: [CQRA-HP-04] [Tier A - Unit] Review prompts mandate Proposed suffix while run_external_review preserves 5-column tables and pre-fills triage stdout
Given `skills/dev-implementation/references/external-review-prompt.md` and `skills/dev-implementation/references/local-review-prompt.md` alongside raw reviewer output containing `- [Important] scripts/app.py:42 — Stale cache key omits round id. Proposed: include round_num in cache key`
When `run_external_review.py` renders `review_results.md` via `render_round()`, validates it via `check()`, and prints triage tables via `top_risk_findings_section()` and `triage()` stdout
Then every row in `review_results.md` contains strictly 5 pipe-delimited columns (`| # | Severity | Location | Problem | Decision |`) passing `check()` with exit code `0`
And both `top_risk_findings_section()` output and the 7-column `## Findings` table printed by `triage()` to stdout pre-fill `include round_num in cache key` in the `Proposed action` column instead of `?`

Scenario: [CQRA-EC-04] [Tier A - Unit] External review triage falls back to question mark only for findings omitting Proposed suffix
Given two parsed findings in one review round where Finding #1 includes `. Proposed: clamp negative fraction` in its Problem cell and Finding #2 omits any `. Proposed:` suffix
When `triage()` prints the round's triage skeleton to stdout
Then Finding #1 pre-fills `clamp negative fraction` in the `Proposed action` column while Finding #2 emits `?` in the `Proposed action` column
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cqra_external_review_proposed.py::test_cqra_hp_04_prompts_and_triage_prefill` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_cqra_external_review_proposed.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py skills/dev-implementation/resources/scripts/test_local_review.py && python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_external_review.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py tests/test_cqra_external_review_proposed.py && ruff check --select E9,F63,F7,F821,F841,B007,B904 skills/dev-implementation/resources/scripts/run_external_review.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && mypy tests/test_cqra_external_review_proposed.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/cqra_task_03.xml tests/test_cqra_external_review_proposed.py` | exit 0; results build/test-results/cqra_task_03.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Persisted `review_results.md` tables keep strictly 5 columns (`#`, `Severity`, `Location`, `Problem`, `Decision`) as emitted by `render_round()` (`L1307`) so `check()` (`L2230-L2251`) continues passing unchanged.
- `external-review-prompt.md` and `local-review-prompt.md` adopt the exact finding suffix `. Proposed: <edit>` used by `skills/principal-review/references/principal-review-prompt.md`.
- `triage()` (`L2515-L2624`) prints the triage skeleton only to stdout (`L2623`) and never writes `fix_plan_round<N>.md`; `top_risk_findings_section()` and `triage()` extract inline proposal clauses into the `Proposed action` column cell in stdout tables and emit `?` only when no proposal suffix is present.
- Shared proposal marker extraction regex (matching Task 05): `re.compile(r"(?:^|(?:[.;—]|\n)\s*)\b(?:Proposed(?:\s+action)?|Fix|Suggestion|Đề xuất):\s*", re.IGNORECASE)` applied to the **last** `finditer()` match (`problem_text = text[:m.start()].strip()`, `proposed_action = text[m.end():].strip()`).

## Definition of Done

- Scenarios CQRA-HP-04 and CQRA-EC-04 pass cleanly. (V2, V6)
- Existing review unit suites (`test_run_external_review.py`, `test_local_review.py`, `test_tto_external_review.py`) pass with zero regressions. (V3, V6)
- Ruff lint and mypy typecheck pass cleanly. (V4, V5)

## Dependencies & Blockers

None.

Downstream dependents (blocked by Task 3): `task_05`.

## References & Rollback

- [Epic HLD](../epic/check_quota_dynamic_models_and_review_action/check_quota_dynamic_models_and_review_action.en.md)
- **Rollback**: Revert task commit to restore prompt files and `skills/dev-implementation/resources/scripts/run_external_review.py`.
