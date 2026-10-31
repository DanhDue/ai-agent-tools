# Review Triage Standardization BDD Scenarios

## Table of Contents

- [Meta Data](#meta-data)
- [Happy Paths](#happy-paths)
- [Edge Cases and Boundaries](#edge-cases-and-boundaries)
- [State Transitions](#state-transitions)
- [Async and Race Conditions](#async-and-race-conditions)
- [Failure and Resilience](#failure-and-resilience)

## Meta Data

- **Epic**: `review_triage_standardization`
- **Canonical language**: English
- **Scenario prefix**: `RTS`
- **Automation roots**: `skills/dev-implementation/resources/scripts/`, `scripts/`
- **Rule**: Every scenario ID is assigned to exactly one task and appears in an automated test.

## Happy Paths

```gherkin
Scenario: [RTS-HP-01] [Tier C - Integration] Triage format renders standardized 4-bullet header
  Given a completed review round in review_results.md
  When triage() formats the summary
  Then output starts with "# Review Triage: <epic>, Round <N>"
  And contains "• Candidate SHA: <sha>"
  And contains "• Reviewer: <cli> ( <model> )"
  And contains "• Thinking Level: <level>"
  And contains "• Verdict: <verdict> (<count> findings)"

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

Scenario: [RTS-HP-05] [Tier C - Integration] Claude CLI receives dangerously-skip-permissions
  When cli_command is constructed for "claude"
  Then arguments include "--dangerously-skip-permissions"
  And arguments do not include "--permission-mode plan"

Scenario: [RTS-HP-06] [Tier C - Integration] Mandatory dynamic probing rule and 5-layer senior verification rules are present in prompts
  Given review prompts and rules
  When external-review-prompt.md, principal-review-prompt.md, review-rules.md and principal-review-rules.md are checked
  Then prompt files contain "## Mandatory Dynamic Probing Rule"
  And rule files contain "5-Layer Deep Verification Checklist"
```

## Edge Cases and Boundaries

```gherkin
Scenario: [RTS-EC-01] [Tier C - Integration] Ollama requires explicit model when no previous round exists
  Given an empty workspace with no .devtool/review_config.json and no previous round
  When run_external_review.py run --cli ollama is invoked without --model
  Then command exits with error message indicating "--cli ollama needs --model"

Scenario: [RTS-EC-02] [Tier C - Integration] Missing or corrupted review_config.json falls back to canonical defaults
  Given .devtool/review_config.json contains malformed JSON
  When load_review_config() is called
  Then it logs a warning and returns canonical defaults without raising an unhandled exception

Scenario: [RTS-EC-03] [Tier C - Integration] Zero findings in review verdict displays 0 findings
  Given a review round with verdict "PASS" and zero findings
  When format_triage_header() runs
  Then verdict bullet displays "• Verdict: PASS (0 findings)"
```

## State Transitions

```gherkin
Scenario: [RTS-ST-01] [Tier C - Integration] Provider switching preserves distinct per-provider memory
  Given .devtool/review_config.json has claude model "Opus 5.5" and codex model "gpt-6.1-sol"
  When the user runs review with "--cli codex"
  Then codex model "gpt-6.1-sol" is selected
  When the user subsequently runs review with "--cli claude"
  Then claude model "Opus 5.5" is selected without colliding with the codex model name

Scenario: [RTS-ST-02] [Tier C - Integration] Incomplete review round reflects non-completed status
  Given a review round with status "failed" or "no verdict"
  When triage() renders the summary
  Then "- **Status**: <status>" is appended to the triage output
```

## Async and Race Conditions

```gherkin
Scenario: [RTS-AR-01] [Tier C - Integration] Atomic review_config.json write protects against partial writes
  When save_review_config() writes configuration
  Then it writes to temporary file .devtool/review_config.json.tmp
  And replaces the target file via atomic os.replace
```

## Failure and Resilience

```gherkin
Scenario: [RTS-FR-01] [Tier C - Integration] Tree change guard aborts if reviewer modifies working tree
  Given a reviewer CLI process that mutates or creates a file in the repository
  When tree_changes(root, before, sha) runs post-execution
  Then review execution detects modified paths and rejects the round

Scenario: [RTS-FR-02] [Tier C - Integration] Unknown thinking level gracefully defaults to high
  Given an invalid or unspecified thinking level argument
  When arguments are resolved
  Then resolve_review_settings() defaults cleanly to "high"
```
