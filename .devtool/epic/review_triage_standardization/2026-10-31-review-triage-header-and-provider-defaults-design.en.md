# Review Triage Header and Provider Defaults Design

## Table of Contents

- [Summary](#summary)
- [Goals and Non-Goals](#goals-and-non-goals)
- [Shared Contract Warnings](#shared-contract-warnings)
- [Decisions Already Made](#decisions-already-made)
- [Design](#design)
  - [Review Configuration File Schema](#review-configuration-file-schema)
  - [Standardized Header Format Specification](#standardized-header-format-specification)
  - [Thinking Level Mapping Matrix and CLI Invocation](#thinking-level-mapping-matrix-and-cli-invocation)
  - [Resolution and Persistence Algorithm in run_external_review.py](#resolution-and-persistence-algorithm-in-run_external_reviewpy)
  - [Skills and Protocol Integration](#skills-and-protocol-integration)
- [Testing Strategy](#testing-strategy)
- [Files Changed](#files-changed)
- [Risks and Mitigations](#risks-and-mitigations)

## Summary

This design standardizes the presentation of review triage summaries across both **Principal Review** (Shift-Left design verification) and **Cross-Model Review** (Shift-Right code verification), enforcing a consistent 4-bullet header containing Candidate SHA, Reviewer (`CLI ( Model )`), Thinking Level, and Verdict with finding counts. Additionally, it introduces persistent per-provider configuration in `.devtool/review_config.json` with sticky memory, defaulting to `Opus 5.5` (high) for Claude, `gpt-6.1-sol` (high) for Codex, `Gemini 4 Argon (Medium)` (medium) for Antigravity (`agy`), and `qwen38-fast:latest` (high) for Ollama.

## Goals and Non-Goals

### Goals

- Enforce a standard 4-bullet header across all review modes (`triage`, `run`, `run_adhoc_code`, and conversational AI Assistant reports).
- Store per-provider default configurations (`model`, `thinking_level`, `last_used_provider`) in `.devtool/review_config.json` with atomic updates and automatic fallback.
- Support `--thinking-level` (`none`, `light`, `low`, `medium`, `high`, `extra-high`) with transparent CLI flag translation:
  - Codex: `-c model_reasoning_effort="<level>"`
  - Claude: `--thinking` budget flags
  - Antigravity: `--model` / reasoning profiles
  - Ollama: token and context budget mapping
- Retain sticky memory: explicit CLI flags update the provider's stored preferences for all future runs.
- Persist `- **Thinking**: <level>` in markdown review records (`principal_review.md` and `review_results.md`).

### Non-Goals

- Bypassing human review choice checkpoints or automating approval gates.
- Overwriting non-review configuration files in `.devtool/` or `.agents/`.
- Restricting manual CLI model overrides on the command line.

## Shared Contract Warnings

No shared-contract warnings (`ai-agent-tools` is the plugin kit repository and has no `shared-contracts/` directory; inspected at session start).

## Decisions Already Made

| # | Decision | Rationale |
|---|---|---|
| 1 | Standardize header format to exactly 4 bullet items: Candidate SHA, Reviewer, Thinking Level, Verdict. | Eliminates inconsistencies between CLI output, triage tables, and chat messages. |
| 2 | Store review defaults per provider under `providers.<cli>` with a top-level `last_used_provider` in `.devtool/review_config.json`. | Prevents model name collisions when switching between providers (e.g. Codex model names clashing with Claude). |
| 3 | Seed baseline defaults: Claude: `Opus 5.5` (high), Codex: `gpt-6.1-sol` (high), agy: `Gemini 4 Argon (Medium)` (medium), Ollama: `qwen38-fast:latest` (high). | Codifies user-specified production defaults for all four supported review engines. |
| 4 | Adopt sticky preference resolution: Explicit CLI argument > Previous round in current epic > `review_config.json` provider preference > Global baseline fallback. | Enables zero-friction reruns without re-typing verbose model and thinking arguments. |
| 5 | Persist thinking level in review round markdown files under `- **Thinking**: <level>`. | Preserves auditability and historical traceability across successive review rounds. |

## Design

### Review Configuration File Schema

The repository-level configuration file is stored at `.devtool/review_config.json`:

```json
{
  "last_used_provider": "codex",
  "providers": {
    "claude": {
      "model": "Opus 5.5",
      "thinking_level": "high"
    },
    "codex": {
      "model": "gpt-6.1-sol",
      "thinking_level": "high"
    },
    "agy": {
      "model": "Gemini 4 Argon (Medium)",
      "thinking_level": "medium"
    },
    "ollama": {
      "model": "qwen38-fast:latest",
      "thinking_level": "high",
      "host": "http://localhost:11434"
    }
  }
}
```

### Standardized Header Format Specification

Every review triage summary (whether rendered by `run_external_review.py triage`, streamed by `run_adhoc_code`, or presented by the AI Assistant in chat) MUST begin with the standardized header block:

```markdown
Cross-Model Review Triage: Round <N> (<CLI>)
*(or `Principal Review Triage: Round <N> (<CLI>)`)*

• Candidate SHA: <commit_sha>
• Reviewer: <CLI> ( <model> )
• Thinking Level: <Light | Low | Medium | High | Extra High | None>
• Verdict: <VERDICT> (<count> <Severity> findings)
```

### Thinking Level Mapping Matrix and CLI Invocation

The `--thinking-level` argument accepts: `none`, `light`, `low`, `medium`, `high`, `extra-high`. The runner maps each level to the underlying engine's CLI syntax:

| Thinking Level | Codex (`codex exec`) | Claude (`claude -p`) | Antigravity (`agy`) | Ollama (`local_review`) |
|---|---|---|---|---|
| **none** | `-c model_reasoning_effort="none"` | *(thinking omitted)* | *(standard)* | *(non-reasoning)* |
| **light / low** | `-c model_reasoning_effort="low"` | `--thinking` (short) | Flash / Low | Low token budget |
| **medium** | `-c model_reasoning_effort="medium"` | `--thinking` (default) | Argon Balanced | Balanced tokens |
| **high** | `-c model_reasoning_effort="high"` | `--thinking` (extended) | Argon High | Extended reasoning |
| **extra-high** | `-c model_reasoning_effort="extra-high"` | `--thinking` (max) | Max reasoning | Maximum tokens |

### Resolution and Persistence Algorithm in run_external_review.py

1. **Resolution Phase**:
   - If `--cli` is omitted, read `last_used_provider` from `.devtool/review_config.json` (defaults to `"codex"` if file is absent).
   - If `--model` is omitted, read `providers[cli].model` from config (falls back to baseline defaults).
   - If `--thinking-level` is omitted, check the latest round in `review_results.md` / `principal_review.md`; if absent, read `providers[cli].thinking_level` from config (falls back to baseline defaults).
2. **Execution Phase**:
   - Construct CLI invocation arguments including thinking/reasoning flags.
   - Record `- **Thinking**: <level>` in round metadata.
3. **Persistence Phase**:
   - Write updated provider preferences and `last_used_provider` back to `.devtool/review_config.json` using atomic write semantics (`.tmp` file rename).

### Skills and Protocol Integration

- **`principal-review` & `cross-model-review` Skills**:
  - Update skill instructions to mandate printing the standardized 4-bullet header block whenever presenting review triage to the developer.
- **`dev-lifecycle` Packaging & Gate 4 Choice Prompts**:
  - Display the current sticky defaults in review choice prompts (e.g. `Option 2: Cross-model review (Current default: Codex / gpt-6.1-sol / Thinking: High)`).

## Testing Strategy

- **Unit Tests (`test_run_external_review.py`)**:
  - Verify initialization of `.devtool/review_config.json` with canonical 4-provider defaults.
  - Verify resolution hierarchy (CLI flag > previous round metadata > config file > baseline defaults).
  - Verify sticky updates when CLI arguments are explicitly supplied.
  - Verify header output format in `triage`, `run_adhoc_code`, and recorded rounds.
- **Harness Integration (`scripts/verify.sh`)**:
  - Ensure all 15 verification sections pass cleanly without regressions.

## Files Changed

- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`
- `skills/principal-review/SKILL.md`
- `skills/principal-review/references/document-triage.md`
- `skills/cross-model-review/SKILL.md`
- `skills/cross-model-review/references/review-triage.md`
- `skills/dev-implementation/references/review-triage.md`
- `skills/dev-lifecycle/references/principal-review.md`

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Model does not support requested reasoning effort level. | Codex CLI degrades gracefully; runner logs warning and proceeds with provider default. |
| Configuration file corrupted by concurrent writes. | Write to `.tmp` file and rename atomically; catch parse errors and revert to baseline defaults. |
