---
id: "task_05_ohk_cmr_deferred_smoke_and_contracts_dirty"
status: "todo"
priority: "high"
assignee: null
epic: "observer-hardening-2026-11"
dueDate: null
created: "2026-11-26T22:10:00Z"
modified: "2026-11-26T22:10:00Z"
completedAt: null
labels: ["architecture", "contract", "review"]
order: "a5"
review_tier: "full"
---

# Task 5: Handle Immutable `.devtool/epic/` Minor Findings in Cross-Model Review, Improve Smoke Checklist Target Inference, and Add Scoped `sync_contracts.py diff-check --allow-dirty`

Epic: [observer-hardening-2026-11](../epic/observer_hardening_2026_11/observer_hardening_2026_11.md)

## Requirement Analysis

Implement observations `#12` and `#13` in their owning scripts and review prompt:

1. **Observation `#12` (`external-review-prompt.md`, `run_external_review.py`, `generate_smoke_checklist.py`)**:
   - In `external-review-prompt.md`: explicitly state that immutable Stage 2/3 epic artefacts under `.devtool/epic/<epic_dir>/` are read-only specification context for code review — do NOT emit `Minor` prose or formatting findings against them.
   - In `run_external_review.py`:
     - Add canonical constant `DEFERRED_EPIC_DOC_DECISION = "deferred: out-of-scope epic doc (§4.4)"` and helper `_is_immutable_epic_doc_location(location: str, epic_dir: str | None = None) -> bool` matching `.devtool/epic/` paths (excluding `review_results.md` and `principal_review.md`).
     - Update `delta_round_context()` rule 4 and Anti-Ping-Pong text to honor `deferred:` alongside `dismissed:`.
     - Keep `check()` strictly rejecting `deferred:` on `Critical`/`Important` blockers (only `fixed in ` or `dismissed: ` resolves blockers).
     - Update `auto_triage_section(..., kind="code")` so when `kind == "code"`, `blocking_rows` is empty, and every remaining `Minor` row targets an immutable `.devtool/epic/` path (or already carries `deferred: `), Auto-Triage emits `AUTO_PASS_CLEAN` (noting out-of-scope `.devtool/epic/` Minor rows are deferred under §4.4) instead of `AUTO_PASS_FINAL_MINOR_SWEEP`.
     - Update `triage()` so `kind == "code"` pre-fills `Proposed action` as `deferred: out-of-scope epic doc (§4.4)` on `Minor` rows matching `_is_immutable_epic_doc_location()`.
   - In `generate_smoke_checklist.py`:
     - Improve `extract_target_from_text(text: str, default_web_target: str | None = None) -> str` so backticked CSS selectors/DOM tokens/file names (e.g. `` `.tts-save-btn` ``, `` `style.css` ``, `` `#modal` ``) are not misclassified as CLI commands, and Playwright/browser/UI scenarios infer an explicit web URL found in BDD/HLD (or `"Web Preview UI"` when no URL is declared) instead of `"CLI / Workspace Root"`.
2. **Observation `#13` (`sync_contracts.py diff-check --allow-dirty`)**:
   - Add `--allow-dirty` to the `diff-check` subparser in `sync_contracts.py`.
   - Preserve strict default `BLOCKED (2)` whenever `--allow-dirty` is omitted and `git status --porcelain --untracked-files=no` is non-empty.
   - When `--allow-dirty` is passed, parse dirty tracked paths: if ANY path is `shared-contracts`, starts with `shared-contracts/`, or equals `.agents/contract_map.json`, STILL return `BLOCKED (2)` naming those protected dirty paths; otherwise proceed with auditing committed `merge_base..HEAD`.

## Files

Allowed files:
- `skills/dev-implementation/references/external-review-prompt.md`
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`
- `skills/dev-implementation/resources/scripts/generate_smoke_checklist.py`
- `tests/test_smoke_checklist_generator.py`
- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`
- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py`
- `tests/test_ohk_cmr_and_contracts.py` (new)

Read-only context:
- `.devtool/epic/observer_hardening_2026_11/2026-11-26-observer-hardening-design.md`
- `.devtool/epic/observer_hardening_2026_11/observer_hardening_2026_11.md`

## Design Rationale & Applicable Skills

- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:cross-model-review`, `d3nexus:sync-shared-contracts`.
- `generate_smoke_checklist.py` is checked by `ruff format --check`, `ruff check`, and `mypy` in `.agents/quality/python-quality.json`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/run_external_review.py`: `delta_round_context` (L1437-L1658), `check` (L2263-L2286), `auto_triage_section` (L2494-L2573), `triage` (L2575-L2665).
  - `skills/dev-implementation/resources/scripts/test_run_external_review.py`: delta/triage/check tests (L1200-L1511).
  - `skills/dev-implementation/resources/scripts/generate_smoke_checklist.py`: `extract_target_from_text` (L70-L85), `extract_smoke_steps` (L87-L149), `generate_smoke_checklist` (L180-L223).
  - `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`: `cmd_diff_check` (L1186-L1290), `main` (L1730-L1750).
  - `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py`: diff-check tests (L1200-L1579).
- **Downstream Callers**: `skills/dev-implementation/resources/scripts/test_run_external_review.py`, `tests/test_smoke_checklist_generator.py`, `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py`, `tests/test_tto_external_review.py`, `tests/test_cqra_external_review_proposed.py`.
- **Target Coverage**: 100% of modified branches across `run_external_review.py`, `generate_smoke_checklist.py`, and `sync_contracts.py`.

### BDD SCENARIOS

Covers: OHK-HP-05, OHK-EC-05, OHK-ST-03, OHK-FR-03

```gherkin
Scenario: [OHK-HP-05] [Tier C - Integration] Cross-Model Review auto-defers immutable epic doc Minor findings and smoke generator infers browser targets
Given a completed code-review round in "review_results.md" with 0 Critical, 0 Important, and 2 Minor findings targeting ".devtool/epic/<epic_dir>/task_01.md" and ".devtool/epic/<epic_dir>/manual_smoke_checklist.md"
When "run_external_review.py triage --epic-dir <epic_dir>" executes
Then Proposed action pre-fills "deferred: out-of-scope epic doc (§4.4)" for both Minor rows
And Auto-Triage Gate emits "AUTO_PASS_CLEAN" instead of "AUTO_PASS_FINAL_MINOR_SWEEP"
When "generate_smoke_checklist.py" parses a Playwright browser BDD scenario without an explicit CLI command
Then the generated checklist target is the inferred web URL or "Web Preview UI" rather than "CLI / Workspace Root"

Scenario: [OHK-EC-05] [Tier C - Integration] Smoke checklist generator ignores CSS selector backticks and infers web target from HLD or BDD URL
Given a BDD Happy Path scenario mentioning Playwright clicking backticked selector "`.tts-save-btn`" on page "/tts-studio" with no CLI command
And the BDD document mentions preview URL "http://127.0.0.1:8000"
When "generate_smoke_checklist.py" extracts smoke steps
Then the step target is not "`.tts-save-btn`" and not "CLI / Workspace Root"
And the step target resolves to "http://127.0.0.1:8000"

Scenario: [OHK-ST-03] [Tier C - Integration] Delta review context honors deferred epic-doc tokens across rounds while blocking deferred on Critical or Important
Given Round 1 in "review_results.md" records a Minor finding on ".devtool/epic/sample/task_01.md" with decision "deferred: out-of-scope epic doc (§4.4)"
When "delta_round_context" constructs the Round 2 prompt block
Then rule 4 explicitly instructs the reviewer not to re-raise findings marked "dismissed:" or "deferred:"
When Round 1 instead marks an Important finding with "deferred: out-of-scope epic doc (§4.4)"
Then "run_external_review.py check --epic-dir sample" exits 1 reporting that Important finding as undecided

Scenario: [OHK-FR-03] [Tier C - Integration] sync_contracts.py diff-check enforces clean tree by default and guards protected paths under --allow-dirty
Given a satellite repository with valid ".agents/contract_map.json" and "shared-contracts" symlink
And an uncommitted tracked modification exists in "src/preview/ui.js"
When "sync_contracts.py diff-check --base-ref main" runs without "--allow-dirty"
Then it exits 2 with status "BLOCKED"
When "sync_contracts.py diff-check --base-ref main --allow-dirty" runs while "shared-contracts" and ".agents/contract_map.json" are clean
Then it audits committed "merge_base..HEAD" and exits 0 with status "PASS"
When ".agents/contract_map.json" itself has an uncommitted tracked modification and "--allow-dirty" is passed
Then it still exits 2 with status "BLOCKED" naming ".agents/contract_map.json"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|---|---|---|---|---|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_cmr_and_contracts.py::test_ohk_hp_05_cmr_auto_defers_epic_doc_minors` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_cmr_and_contracts.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py && python3 -m pytest -q --tb=short --maxfail=3 tests/test_smoke_checklist_generator.py tests/test_tto_external_review.py tests/test_cqra_external_review_proposed.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py && ruff format --check skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_smoke_checklist_generator.py tests/test_ohk_cmr_and_contracts.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && mypy --ignore-missing-imports --follow-imports=silent skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py tests/test_smoke_checklist_generator.py tests/test_ohk_cmr_and_contracts.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_cmr_and_contracts.py --junitxml=build/test-results/task_05.xml` | exit 0; results build/test-results/task_05.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`run_external_review.py:1590`, `1642`, `2278`, `2494-2655`)**: `auto_triage_section(number, rounds, latest, max_rounds=MAX_REVIEW_ROUNDS)` currently treats all `minor_rows` uniformly and emits `AUTO_PASS_FINAL_MINOR_SWEEP` whenever `minor_rows` is non-empty.
  - **New contract**:
    - Define `DEFERRED_EPIC_DOC_DECISION = "deferred: out-of-scope epic doc (§4.4)"`.
    - Add `_is_immutable_epic_doc_location(location: str, epic_dir: str | None = None) -> bool` returning True when normalized `path_of(location)` starts with `.devtool/epic/` (or `.devtool/epic/{epic_dir}/`) and basename is not `review_results.md` or `principal_review.md`.
    - Add optional `kind: str = "code"` and `epic_dir: str | None = None` parameters to `auto_triage_section()` (defaults preserve all existing caller signatures). When `kind == "code"`, treat a `Minor` row as auto-deferred if `cells[4].strip().startswith("deferred:")` or `_is_immutable_epic_doc_location(cells[2], epic_dir)`. Emit `AUTO_PASS_CLEAN` when `not blocking_rows` and zero actionable `Minor` rows remain.
    - In `triage()`: pass `kind=kind, epic_dir=args.epic_dir` into `auto_triage_section()`, and for `kind == "code"` Minor rows matching `_is_immutable_epic_doc_location()`, set `action_cell = DEFERRED_EPIC_DOC_DECISION`.
    - In `delta_round_context()`: update rule 4 and Anti-Ping-Pong guidance to honor both `dismissed:` and `deferred:` decisions.
    - In `check()`: keep `cells[1] in BLOCKING and not cells[4].startswith(("fixed in ", "dismissed: "))` unchanged so `deferred:` NEVER bypasses `Critical`/`Important` findings.
- **Source (`generate_smoke_checklist.py:70-150`, `180-223`)**: `extract_target_from_text(text)` accepts any backticked token and falls back to `"CLI / Workspace Root"`.
  - **New contract**: Add optional `default_web_target: str | None = None` parameter to `extract_target_from_text()` and `extract_smoke_steps()`. Accept backticked tokens as commands only when they look like shell/CLI commands (matching known CLI executables, `./` scripts, `--flags`, or multi-word commands — rejecting CSS selectors `.foo`/`#bar`, routes `/foo`, single identifiers, or `.css`/`.html`/`.json` filenames). Detect browser/Playwright/UI keywords (`playwright`, `browser`, `viewport`, `preview`, `modal`, `dom`, `page`, `click`, `render`, `.html`) and return `default_web_target or "Web Preview UI"`. In `generate_smoke_checklist()`, extract any first `http(s)://` URL from `bdd_scenarios.md` (or HLD `<epic_dir>.md`) as `default_web_target` for browser scenarios.
- **Source (`sync_contracts.py:1242-1254`, `1730-1735`)**: `cmd_diff_check()` fails with exit `2` (`BLOCKED`) on any non-empty `git status --porcelain --untracked-files=no`.
  - **New contract**: Add `--allow-dirty` flag to `p_diff`. When `getattr(args, "allow_dirty", False)` is True, extract the path from each porcelain status line (`line[3:].strip()`, handling rename `old -> new` by checking both sides). If any dirty path equals `shared-contracts`, starts with `shared-contracts/`, or equals `.agents/contract_map.json`, return `emit_blocked([...])` (exit 2); otherwise continue auditing `merge_base..HEAD`.

## Definition of Done

- [ ] `external-review-prompt.md` and `run_external_review.py` exclude/auto-defer `.devtool/epic/` Minor rows to `AUTO_PASS_CLEAN` while preserving strict `check()` on `Critical`/`Important` (V2, V3, V6)
- [ ] `generate_smoke_checklist.py` ignores backticked CSS selectors and infers web URL / `"Web Preview UI"` for browser/Playwright BDD scenarios (V2, V3, V4, V5, V6)
- [ ] `sync_contracts.py diff-check` preserves strict default clean-tree `BLOCKED` and supports scoped `--allow-dirty` guarding `shared-contracts` and `.agents/contract_map.json` (V2, V3, V4, V5, V6)
- [ ] Assigned BDD integration scenarios (`OHK-HP-05`, `OHK-EC-05`, `OHK-ST-03`, `OHK-FR-03`) pass with JUnit XML evidence (V6)

## Dependencies & Blockers

None.

## References & Rollback

- Spec: [2026-11-26-observer-hardening-design.md](../epic/observer_hardening_2026_11/2026-11-26-observer-hardening-design.md)
- HLD: [observer_hardening_2026_11.md](../epic/observer_hardening_2026_11/observer_hardening_2026_11.md)
- BDD: [bdd_scenarios.md](../epic/observer_hardening_2026_11/bdd_scenarios.md)
- Rollback: Revert this task's commit on `epic/observer-hardening-2026-11`.
