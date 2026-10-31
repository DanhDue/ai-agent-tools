# Release Notes: d3nexus v1.19.0

**Release Date:** November 01, 2026  
**Version:** `1.19.0`  
**Git Tag:** `v1.19.0`, `d3nexus--v1.19.0`

---

## Executive Summary

`v1.19.0` introduces the **Zero-Token Session Refresh Engine** (`refresh-session`), allowing developers to pre-warm rolling 5-hour quota windows for Claude Code CLI and OpenAI Codex CLI with minimal token footprint (~50 tokens on Claude, 1,645 tokens on Codex) and absolute isolation from skills, plugins, or MCP servers. This release also formalizes **Standardized Review Triage & Sticky Review Preferences** across external review workflows, and strengthens multi-repo context memory and task observation resilience.

---

## Key Highlights

### 1. Zero-Token Session Pre-Warming Engine (`skills/refresh-session/`)
- **Minimal Token Consumption**: Designed specifically to pre-warm 5-hour rolling session windows without wasting quota:
  - Claude Code (`claude`): Uses `haiku` model, `--safe-mode`, empty tools (`--tools ""`), and disabled slash commands, consuming only ~50 total tokens.
  - OpenAI Codex (`codex`): Executes `gpt-6.1-sol` with `model_reasoning_effort=low`, bypassing local sandbox restrictions with `--ephemeral` and consuming only 1,645 base tokens.
- **Hermetic Sandbox Isolation**: Runs CLI invocations in an ephemeral temporary directory (`tempfile.TemporaryDirectory()`) to prevent accidental loading of repository configs, skills, MCP servers, or project files.
- **Unit Tested & Release Hardened**: Includes 13 isolated unit tests (`test_refresh_session.py`) testing execution pathways, flag constructions, and error handling.

### 2. Standardized Review Triage & Sticky Review Preferences
- **Unified 4-Bullet Triage Header**: Standardizes the review results header across all reviewers (Claude, Codex, Antigravity, Ollama) to strictly include `Candidate SHA`, `Reviewer`, `Thinking Level`, and `Verdict`.
- **Sticky Preferences**: Remembers developer choices per provider (e.g. effort levels, selected models) in `.devtool/review_config.json` across sessions.
- **Dynamic Claude Probing**: Safely probes Claude CLI for `--effort` and `--thinking` flag availability, gracefully falling back to supported options.
- **Senior 5-Layer Reviewer Guidelines**: Embeds mandatory 5-layer reviewer verification instructions (Architecture, Clean Code, Security, Correctness, Testing) directly into external review runner prompts.

### 3. Context Memory & Task Observer Resilience
- **Status Check Sanitization**: Filters out ephemeral Tier 2 runtime state files from working tree status reports in `scripts/resume_context.py`.
- **Nested Repo Path Resolution**: Ensures `.devtool` directories resolve correctly from any nested or sibling repository workspace.
- **Task Observer Glob Safety**: Guards zsh session-start glob expressions against `no matches found` errors in non-standard shell environments.

### 4. Release Verification Harness Section 16 (`scripts/verify.sh`)
- Automated verification in Section 16 enforces the `refresh-session` CLI contract, verifying argument parsing, hermetic sandboxing, isolation flag compliance, and test suite execution.

---

## Verifications & Quality Gates Passed

- `skills/refresh-session/resources/scripts/test_refresh_session.py`: 🟢 **PASS** (13/13 tests green)
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`: 🟢 **PASS** (61/61 tests green)
- `scripts/test_resume_context.py`: 🟢 **PASS** (14/14 tests green)
- `scripts/verify.sh`: 🟢 **PASS — safe to publish** (16/16 sections green)
