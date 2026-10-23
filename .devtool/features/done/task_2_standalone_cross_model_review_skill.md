---
id: "task_2_standalone_cross_model_review_skill"
status: "done"
priority: "high"
assignee: null
epic: "split_review_skills"
dueDate: null
created: "2026-10-23T11:40:00Z"
modified: "2026-10-23T12:51:17Z"
completedAt: "2026-10-23T12:51:17Z"
labels: ["skill", "cross-model-review", "code-review", "ollama", "cli"]
order: "a2"
---

# Task 2: Standalone Cross-Model Review Skill and Ad-Hoc Diff Support

Epic: [split_review_skills](../epic/split_review_skills/split_review_skills.en.md)

## Requirement Analysis

Create the standalone skill `skills/cross-model-review/SKILL.md` and its dedicated references (`review-triage.md`, `local-review-setup.md`).
Update `run_external_review.py` to support reviewing arbitrary git diffs via `--base <base>` and `--commits <range>` without requiring an epic directory, supporting both External CLI (Claude CLI, Codex CLI) and Local Ollama models.

Key deliverables:
1. `skills/cross-model-review/SKILL.md` with valid YAML frontmatter (`name: cross-model-review`, `description`), documenting both In-Lifecycle (called from `dev-implementation` Review Choice after Gate 4) and Ad-hoc (`/cross-model-review [--base <base>] [--commits <range>]`) usage.
2. Supporting references in `skills/cross-model-review/references/`:
   - `review-triage.md`: Evidence verification discipline, refusal of performative agreement, and decision cell standards.
   - `local-review-setup.md`: Setup and context configuration guide for local Ollama models.
3. Update `run_external_review.py` to allow ad-hoc branch and commit diff evaluation when `--epic-dir` is not provided, extracting commit log and diff against `--base`.
4. Unit tests in `test_run_external_review.py` verifying ad-hoc diff evaluation, clean tree enforcement, timeout handling, and Ollama parameter forwarding.

## Files

Allowed files:
- `skills/cross-model-review/SKILL.md` (new)
- `skills/cross-model-review/references/review-triage.md` (new)
- `skills/cross-model-review/references/local-review-setup.md` (new)
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`

Read-only context:
- `skills/dev-implementation/references/review-triage.md`
- `skills/dev-implementation/references/local-review-setup.md`
- `.devtool/epic/split_review_skills/split_review_skills.en.md`
- `.devtool/epic/split_review_skills/bdd_scenarios.en.md`

## Design Rationale

Extracting Cross-Model Review into an independent skill allows developers to trigger multi-model and local-model reviews on any pull request, branch diff, or commit range on demand.
The triage protocol remains rigorous and evidence-grounded, ensuring that reviewer claims are validated against actual source code before any fix or decision is recorded.
Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/run_external_review.py`: `run()`, `main()`, new `diff_range()`, `record_round()`, `check()`, `triage()`
  - `skills/dev-implementation/resources/scripts/test_run_external_review.py`: new `TestCrossModelReviewAdhoc`
- **Downstream Callers**: `dev-implementation` (Task 3), direct user invocations (`/cross-model-review`).
- **Cross-Platform Bridges**: none.
- **Target Test Coverage Threshold**: 100% test pass on new test methods in `test_run_external_review.py`.

### BDD SCENARIOS

Covers: SRS-HP-03, SRS-HP-04, SRS-HP-05, SRS-EC-02, SRS-EC-03, SRS-ST-02, SRS-AR-01, SRS-AR-02, SRS-FR-02

```gherkin
Scenario: [SRS-HP-03] [Tier C - Integration] In-lifecycle Cross-Model Review invocation from dev-implementation
  Given all tasks in epic "sample_epic" are marked done and Gate 4 returns PASS
  When the developer selects option 2 "Cross-model review" with "claude" CLI
  Then the "d3nexus:cross-model-review" skill is invoked
  And "run_external_review.py run --kind epic" evaluates task commits and diffs against base
  And round 1 is recorded into ".devtool/epic/sample_epic/review_results.md"

Scenario: [SRS-HP-04] [Tier C - Integration] Ad-hoc Cross-Model Review invocation on git branch
  Given a feature branch "feature/payment-flow" has commits diverging from "main"
  When the developer invokes "/cross-model-review --base main"
  Then the "cross-model-review" skill computes the commit range and diff against "main"
  And executes external model review across the diff
  And emits a formatted triage report with proposed fixes

Scenario: [SRS-HP-05] [Tier C - Integration] Local model review invocation through cross-model-review skill
  Given local Ollama server is running and exposes model "qwen2.5-coder:32b"
  When the developer selects option 3 "Local model review" specifying model "qwen2.5-coder:32b"
  Then the "cross-model-review" skill invokes the runner with "--cli ollama --model qwen2.5-coder:32b"
  And records the evaluation round into "review_results.md"

Scenario: [SRS-EC-02] [Tier A - Unit] Cross-model review refuses execution on dirty working tree
  Given the repository working tree has unstaged or untracked changes
  When "cross-model-review" initiates runner execution
  Then the runner refuses execution with a clean tree precondition error
  And reminds the user to commit or stash modifications before review

Scenario: [SRS-EC-03] [Tier A - Unit] Missing external CLI tool triggers actionable guidance
  Given neither "claude" nor "codex" binary is installed on the user PATH
  When an external review round is requested
  Then the skill detects missing CLI binaries
  And prints installation instructions for Claude Code CLI and OpenAI Codex CLI without crashing

Scenario: [SRS-ST-02] [Tier C - Integration] Cross-Model Review fix loop enforces Gate 4 re-verification
  Given round 1 of cross-model review reported Important findings
  When code fixes are committed and decisions are recorded in "review_results.md"
  Then Gate 4 machine acceptance must be re-run in full on the new candidate SHA
  And Review Choice is presented again only after Gate 4 returns PASS

Scenario: [SRS-AR-01] [Tier A - Unit] Streaming timeout handling during model execution
  Given an external CLI invocation exceeds the configured process timeout
  When the timeout trigger fires
  Then the runner terminates the child process cleanly
  And reports a descriptive timeout finding without leaving orphaned background processes

Scenario: [SRS-AR-02] [Tier A - Unit] Sequential round numbering prevents collision
  Given an epic already has round 1 recorded in its review log
  When a subsequent review round completes
  Then the new round is strictly assigned round number 2
  And previous round history and decisions are immutably preserved

Scenario: [SRS-FR-02] [Tier A - Unit] Triage parser isolates malformed model responses
  Given an external reviewer outputs text that omits valid verdict or severity anchors
  When "run_external_review.py triage" processes the round output
  Then the parser isolates the parse failure into a visible warning
  And prompts the developer to inspect raw log without crashing the lifecycle
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k TestCrossModelReviewAdhoc` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k TestCrossModelReviewAdhoc` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; results build/test-results/task_2.xml | — |

## Stop and Report If

- A command, path, symbol, or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files, or Covers line.

## Decisions Already Made

- Skill name is exactly `cross-model-review`.
- The CLI runner engine `run_external_review.py` remains in `skills/dev-implementation/resources/scripts/`.
- Local model review through Ollama and External model review through Claude/Codex CLI are both governed by this skill.
- For ad-hoc review when `--epic-dir` is absent (e.g. `--base` and `--commits`), review output and findings table stream directly to stdout without requiring an epic directory or writing `review_results.md`; ephemeral pass logs go under `build/` (git-ignored).

## Definition of Done

- `skills/cross-model-review/SKILL.md` exists with frontmatter and instructions for in-lifecycle and ad-hoc modes. (V2, V5)
- Supporting references `review-triage.md` and `local-review-setup.md` exist and validate cleanly. (V2, V5)
- `run_external_review.py` supports ad-hoc review with `--base` and `--commits`. (V2, V5)
- All lint, type checks, and verification rows V1–V5 pass. (V3, V4, V5)

## Dependencies & Blockers

- Blocked by: none.
- Blocks [Task 3](task_3_orchestrators_delegation_refactor.md).

## References & Rollback

- [Epic HLD](../epic/split_review_skills/split_review_skills.en.md), Module Contracts.
- **Rollback**: Revert task commit.
