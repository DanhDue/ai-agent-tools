---
id: "task_01_diff_only_external_review_and_transcript_isolation"
status: "todo"
priority: "high"
assignee: null
epic: "token_throttling_optimization"
dueDate: null
created: "2026-11-13T02:30:00Z"
modified: "2026-11-13T02:30:00Z"
completedAt: null
labels: ["review", "token-optimization", "config"]
order: "a1"
---

# Task 1: Diff-Only External Review and Transcript Isolation

Epic: [token_throttling_optimization](token_throttling_optimization.en.md)

## Requirement Analysis

Enforce Diff-Only Review (`Rule 1`), Silent/Capped Evidence (`Rule 2`), Transcript Log Isolation (`Rule 5`), and Config-Driven Role 2.3 defaults in the external review subsystem:
1. Update `DEFAULT_REVIEW_CONFIG["providers"]` and `load_review_config()` in `skills/dev-implementation/resources/scripts/run_external_review.py`:
   - Add default `"assistant"` (`"claude-opus-5-5-high"`, `"high"`) and `"programmer"` (`"gemini-4-hydrogen-xhigh"`, `"xhigh"`) provider entries.
   - Inside `load_review_config()`, seed missing default providers and upgrade legacy programmer models (`"gemini-3.8-flash"`, `"gemini-3.8-flash-high"`) in-memory to `"gemini-4-hydrogen-xhigh"` with `"thinking_level": "xhigh"`, while leaving custom user models (e.g. `"claude-sonnet-4-6"`) untouched.
2. Enforce Diff-Only `-U5` and Round 2+ delta-only prompts:
   - Change `git diff` context from `-U10` to `-U5` in both `run_external_review.py` (`build_diff_section`, `diff_range`) and `skills/subagent-driven-development/scripts/review-package`.
   - When `build_diff_section()` or `diff_range()` truncates over `MAX_DIFF_LINES` (`1500`) or `MAX_DIFF_BYTES` (`60000`), prepend `git diff --stat` and include per-file headers + `@@ ... @@` hunk headers within budget.
   - Exclude all `*.vi.md` paths systematically across every external review diff and context path: `principal_artefact_lines()`, `collect_facts()`, `artefact_lines()`, `EXCLUDES` / `build_diff_section()`, `principal` delta paths in `delta_round_context()`, `diff_range()`, fallback diffs, and local/ad-hoc review inputs; add negative unit tests with modified `.vi.md` files both inside and outside `.devtool/epic/<epic>/`.
   - In `run()` for `round_num >= 2` when `delta_round_context()` is non-empty (and `--full` is not set), omit the cumulative `base...sha` diff section and emit a 1-line `git diff --stat` cumulative reference instead.
3. Quiet facts and raw CLI log isolation:
   - Update `fact(label, code, out, err)` so `code == 0` emits `f"PASS: {label}\n"` omitting stdout, and failure emits the label plus the last 25 non-empty lines.
   - Update `render_round()` to persist raw CLI stdout/stderr transcripts into `build/reviews/<epic>_<kind>_round<n>_<sha7>.raw.log` (scoping by review `kind` and short `sha` so `principal` vs `code` reviews and `--force` reruns never collide or overwrite) and reference that path instead of dumping multi-megabyte transcripts into `principal_review.md` or `review_results.md`, keeping the compact `Raw output:` verdict fence intact for downstream table/finding parsers (`rounds_in`, `finding_rows`, `triage`).
   - Update `skills/principal-review/references/principal-review-prompt.md` and `skills/dev-implementation/references/external-review-prompt.md` with explicit Diff-Only (`-U5`), Zero-Fluff output, and English SSOT review guidance.
4. Add `tests/test_tto_external_review.py` covering `TTO-HP-01`, `TTO-EC-01`, `TTO-ST-01`, and `TTO-FR-01`.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`
- `skills/subagent-driven-development/scripts/review-package`
- `skills/dev-implementation/references/external-review-prompt.md`
- `skills/principal-review/references/principal-review-prompt.md`
- `tests/test_tto_external_review.py` (new)

Read-only context:
- `.devtool/epic/token_throttling_optimization/token_throttling_optimization.en.md` — HLD Module Contracts and Integration Plan
- `.devtool/epic/token_throttling_optimization/bdd_scenarios.en.md` — Canonical BDD Scenarios
- `.agents/quality/python-quality.json` — Registered lint and type_check commands

## Design Rationale

External review rounds dominate token burn because every Round 2+ re-transmits full `base...sha` diffs, `.vi.md` duplicates, verbose passing command logs, and raw CLI stderr back into markdown artifacts that later stages reload. Enforcing `-U5`, structural `--stat` + `@@` truncation, Round 2 delta isolation, 1-line passing facts, and raw log offloading eliminates quadratic bloat without losing any parser fidelity. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/run_external_review.py`: `load_review_config` (L103-L129), `principal_artefact_lines` (L317-L352), `fact` (L507-L508), `collect_facts` (L511-L640), `build_diff_section` (L652-L683), `diff_range` (L686-L719), `render_round` (L896-L902), `delta_round_context` (L972-L1118), `run` (L1230-L1320)
  - `skills/dev-implementation/resources/scripts/test_run_external_review.py`: `ReviewCase` (L81-L174), `RunExternalReviewTest` (L175-L566), `PrincipalReviewTest` (L567-L772), `TestReviewConfigAndHeader` (L950-L1508)
  - `skills/subagent-driven-development/scripts/review-package`: diff context lines (L1-L77)
  - `tests/test_tto_external_review.py`: new unit and integration tests for `TTO-HP-01`, `TTO-EC-01`, `TTO-ST-01`, `TTO-FR-01`
- **Downstream Callers**: `scripts/resume_context.py` (`--emit-prompt`), `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (`load_review_config`, `run_external_review.py` subprocess), `skills/dev-implementation/resources/scripts/test_run_external_review.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% of new config migration, diff truncation, fact formatting, and raw log offloading branches.

### BDD SCENARIOS

Covers: TTO-HP-01, TTO-EC-01, TTO-ST-01, TTO-FR-01

```gherkin
Scenario: [TTO-HP-01] [Tier C - Integration] Diff-only external review uses -U5 in Round 1 and omits full base diff in Round 2

Given an isolated git repository with an epic having multiple committed source changes and a .vi.md companion document
And an existing Round 1 entry already recorded in review_results.md for an earlier SHA
When run_external_review.py builds the Round 1 prompt and then builds the Round 2 prompt after an incremental fix commit
Then the Round 1 diff section is generated with -U5 context and excludes all *.vi.md artifact paths
And the Round 2 prompt includes delta_round_context for prev_sha..curr_sha with a one-line cumulative diff --stat reference
And the Round 2 prompt omits the full base...curr_sha diff block unless --full is explicitly passed

Scenario: [TTO-EC-01] [Tier A - Unit] Over-budget diff truncates to --stat summary and @@ hunk headers per changed file

Given a synthetic git diff exceeding MAX_DIFF_LINES (1500 lines) or MAX_DIFF_BYTES (60000 bytes)
When build_diff_section builds the diff payload for external review
Then the output falls back cleanly within the byte budget without dropping structural file boundaries
And the truncated section explicitly contains the git diff --stat summary alongside the file headers and @@ hunk headers for changed files

Scenario: [TTO-ST-01] [Tier A - Unit] load_review_config migrates legacy gemini-3.8-flash defaults while preserving custom models

Given an existing .devtool/review_config.json with providers.programmer.model set to "gemini-3.8-flash-high"
And a second config file where providers.programmer.model is customized to "claude-sonnet-4-6"
When run_external_review.load_review_config loads each configuration file
Then the legacy "gemini-3.8-flash-high" entry is upgraded in-memory to "gemini-4-hydrogen-xhigh" with thinking_level "xhigh"
And the user-customized "claude-sonnet-4-6" entry remains untouched without being overwritten

Scenario: [TTO-FR-01] [Tier A - Unit] collect_facts emits one line per passing command and caps failing output + raw transcripts

Given a passing command returning 180 stdout lines with exit code 0 and a failing command returning 90 stderr lines with exit code 1
When run_external_review.fact builds prompt evidence and render_round persists the round artifact
Then the passing command produces a single "PASS: <label>" line omitting stdout
And the failing command includes the command label plus at most 25 trailing non-empty output lines
And unfiltered CLI stdout/stderr is routed into build/reviews/<epic>_<kind>_round<n>_<sha7>.raw.log so principal_review.md remains compact
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_external_review.py::test_tto_hp_01_diff_only_round1_and_round2` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_external_review.py::test_tto_hp_01_diff_only_round1_and_round2` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --ignore SIM117 skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py tests/test_tto_external_review.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py tests/test_tto_external_review.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/task_1.xml tests/test_tto_external_review.py` | exit 0; results build/test-results/task_1.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `DEFAULT_REVIEW_CONFIG["providers"]` (in `skills/dev-implementation/resources/scripts/run_external_review.py`) includes `"assistant": {"model": "claude-opus-5-5-high", "thinking_level": "high"}` and `"programmer": {"model": "gemini-4-hydrogen-xhigh", "thinking_level": "xhigh"}`.
- `load_review_config()` upgrades legacy programmer IDs `{"gemini-3.8-flash", "gemini-3.8-flash-high"}` in-memory to `"gemini-4-hydrogen-xhigh"` + `"thinking_level": "xhigh"`, preserving custom models and avoiding mutations to the gitignored repo-level `.devtool/review_config.json` during unit tests.
- Diff extraction in `build_diff_section()` and `diff_range()` (L652-L719), `EXCLUDES`, `delta_round_context()` (`principal` delta paths L996-L1005), fallback/ad-hoc diffs, `principal_artefact_lines()` (L317-L352), `artefact_lines()`, and `review-package` uses `git diff -U5` and excludes all `*.vi.md` paths unconditionally; over-budget diffs retain `git diff --stat` and per-file `@@ ... @@` hunk headers.
- `fact(label, code, out, err)` (L507-L508) emits `"PASS: {label}\n"` on `code == 0` and caps failures to the last 25 non-empty lines; `render_round()` (L896-L902) writes unfiltered transcripts to `build/reviews/<epic>_<kind>_round<n>_<sha7>.raw.log` while preserving `Raw output:` verdict fences compatible with `rounds_in()` (L850-L865), `finding_rows()` (L1528-L1529), and `triage()` (L1711-L1783).
- Round `>= 2` in `run()` (L1230-L1320) omits full `base...sha` `diff_section` whenever `delta_round_context()` is non-empty and `--full` is false.

## Definition of Done

- Scenarios TTO-HP-01, TTO-EC-01, TTO-ST-01, and TTO-FR-01 pass with real temporary git repositories and fake CLIs. (V2, V3, V6)
- Python ruff lint and mypy strict checks pass across modified and existing test suites. (V3, V4, V5)
- Diff context (`-U5`), `.vi.md` exclusion, raw log offloading, and `load_review_config` migration verified cleanly on candidate commit. (Gate 5)

## Dependencies & Blockers

None. Blocks [Task 4](task_04_lifecycle_runner_programmer_config_and_pool_isolation.md) and [Task 5](task_05_slimming_rules_skills_dedup_and_selective_reviewer.md).

## References & Rollback

- [Epic HLD](token_throttling_optimization.en.md), Module Contracts (§1).
- **Rollback**: Revert task commit; restores prior `run_external_review.py`, `review-package`, prompt templates, and removes `tests/test_tto_external_review.py`.

