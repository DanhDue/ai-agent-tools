---
id: "task_1_review_config_and_sticky_defaults"
status: "done"
priority: "high"
assignee: null
epic: "review_triage_standardization"
dueDate: null
created: "2026-10-31T06:00:00Z"
modified: "2026-10-31T06:30:00Z"
completedAt: "2026-10-31T06:30:00Z"
labels: ["review", "config", "defaults"]
order: "a1"
---

# Task 1: Review Config Persistence and Sticky Defaults

Epic: [review_triage_standardization](review_triage_standardization.en.md)

## Requirement Analysis

Currently, review executions require specifying `--cli`, `--model`, and `--thinking-level` repeatedly, and previous settings are not persisted on a per-provider basis. This causes model name collisions when switching between providers (e.g. Codex model flags colliding with Claude) and forces developers to re-enter provider preferences across session rotations.

Implement persistent per-provider configuration stored in `.devtool/review_config.json` with sticky memory. Seed canonical defaults:
- Claude: `Opus 5.5` (thinking: `high`)
- Codex: `gpt-6.1-sol` (thinking: `high`)
- agy: `Gemini 4 Argon (Medium)` (thinking: `medium`)
- ollama: `qwen38-fast:latest` (thinking: `high`)
- Default provider: `codex`

Translate `--thinking-level` arguments (`none`, `light`, `low`, `medium`, `high`, `extra-high`) to CLI execution flags (`--effort` for Claude, `-c model_reasoning_effort="<level>"` for Codex). Persist the used thinking level in round metadata (`- **Thinking**: <level>`).

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`

Read-only context:
- `.devtool/epic/review_triage_standardization/review_triage_standardization.en.md`
- `.devtool/epic/review_triage_standardization/bdd_scenarios.en.md`

## Design Rationale

Per-provider configuration isolation ensures that switching between Claude, Codex, agy, or Ollama preserves each provider's distinct model and thinking level preferences without cross-contamination. Atomic write operations (`.tmp` file and `os.replace`) prevent race conditions or corrupted JSON files on disk.

### BDD SCENARIOS

Covers: RTS-HP-02, RTS-HP-03, RTS-HP-04, RTS-EC-01, RTS-EC-02, RTS-ST-01, RTS-AR-01, RTS-FR-02

```gherkin
Scenario: [RTS-HP-02] [Tier C - Integration] Canonical provider defaults are automatically seeded
  Given no .devtool/review_config.json exists
  When load_review_config() is executed
  Then .devtool/review_config.json is created with defaults:
  | Provider | Model                   | Thinking Level |
  | codex    | gpt-6.1-sol             | high           |
  | claude   | Opus 5.5                | high           |
  | agy      | Gemini 4 Argon (Medium) | medium         |
  | ollama   | qwen38-fast:latest      | high           |
  And default_provider is set to "codex"

Scenario: [RTS-HP-03] [Tier C - Integration] Sticky memory updates on subsequent runs
  Given an existing .devtool/review_config.json
  When a review runs with "--cli claude --model custom-claude --thinking-level medium"
  Then .devtool/review_config.json updates default_provider to "claude"
  And providers.claude.model updates to "custom-claude"
  And providers.claude.thinking_level updates to "medium"
  And other providers remain untouched

Scenario: [RTS-HP-04] [Tier C - Integration] Thinking level translates to provider-specific CLI flags
  Given provider settings with thinking level "high"
  When cli_command is constructed for "claude"
  Then "--effort high" is included in arguments
  When cli_command is constructed for "codex"
  Then "-c model_reasoning_effort=high" is included in arguments

Scenario: [RTS-EC-01] [Tier C - Integration] Ollama requires explicit model when no previous round exists
  Given an empty workspace with no .devtool/review_config.json and no previous round
  When run_external_review.py run --cli ollama is invoked without --model
  Then command exits with error message indicating "--cli ollama needs --model"

Scenario: [RTS-EC-02] [Tier C - Integration] Missing or corrupted review_config.json falls back to canonical defaults
  Given .devtool/review_config.json contains malformed JSON
  When load_review_config() is called
  Then it logs a warning and returns canonical defaults without raising an unhandled exception

Scenario: [RTS-ST-01] [Tier C - Integration] Provider switching preserves distinct per-provider memory
  Given .devtool/review_config.json has claude model "Opus 5.5" and codex model "gpt-6.1-sol"
  When the user runs review with "--cli codex"
  Then codex model "gpt-6.1-sol" is selected
  When the user subsequently runs review with "--cli claude"
  Then claude model "Opus 5.5" is selected without colliding with the codex model name

Scenario: [RTS-AR-01] [Tier C - Integration] Atomic review_config.json write protects against partial writes
  When save_review_config() writes configuration
  Then it writes to temporary file .devtool/review_config.json.tmp
  And replaces the target file via atomic os.replace

Scenario: [RTS-FR-02] [Tier C - Integration] Unknown thinking level gracefully defaults to high
  Given an invalid or unspecified thinking level argument
  When arguments are resolved
  Then resolve_review_settings() defaults cleanly to "high"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k test_default_config_resolution_and_persistence` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k test_default_config_resolution_and_persistence` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k test_codex_thinking_level_arguments` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/run-external-review.xml skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; results build/test-results/run-external-review.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- Defined `DEFAULT_REVIEW_CONFIG` containing canonical defaults: `codex`: `gpt-6.1-sol` (high), `claude`: `Opus 5.5` (high), `agy`: `Gemini 4 Argon (Medium)` (medium), `ollama`: `qwen38-fast:latest` (high), with `default_provider: "codex"`.
- Configuration is loaded via `load_review_config(root)` and saved via `save_review_config(root, config)`.
- Saving writes to `.devtool/review_config.json.tmp` and executes `os.replace` to ensure atomicity.
- Thinking levels map to `--effort` for Claude (`extra-high` -> `xhigh`) and `-c model_reasoning_effort="<level>"` for Codex.
- Ollama requires an explicit `--model` if no previous round and no custom model are specified.

## Definition of Done

- `DEFAULT_REVIEW_CONFIG` and sticky configuration persistence in `.devtool/review_config.json` function properly and tests pass. (V2)
- Thinking level arguments translate correctly to CLI options for Codex and Claude. (V3)
- Linting and static type checking pass cleanly with zero warnings or errors. (V4, V5)
- JUnit test report `build/test-results/run-external-review.xml` is successfully generated with passing tests. (V6)
- Review configuration cleanly preserves per-provider settings without cross-provider bleed. (Gate 5)

## Dependencies & Blockers

None. Blocks [Task 3](task_3_standardize_4_bullet_triage_header.md).

## References & Rollback

- [Epic HLD](review_triage_standardization.en.md)
- **Rollback**: Revert changes in `run_external_review.py` and remove `.devtool/review_config.json`.
