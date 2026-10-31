# Refresh Session Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use d3nexus:subagent-driven-development (recommended) or d3nexus:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide the `/refresh-session` skill and an underlying standalone utility (`refresh_session.py`) to send a minimal single-token ping to Claude Code CLI and Codex CLI to pre-initialize or refresh the rolling 5-hour quota window with near-zero tokens and zero skill/plugin/MCP initialization.

**Architecture:** A standalone Python script (`skills/refresh-session/resources/scripts/refresh_session.py`) creates an isolated temporary directory outside repository roots, executes sandboxed CLI commands with aggressive flag suppression, parses token counts and latency, and reports clean execution metrics. A standardized skill wrapper (`skills/refresh-session/SKILL.md`) routes `/refresh-session [claude|codex|all]` to the engine.

**Tech Stack:** Python 3.10+ (Standard Library: `argparse`, `shutil`, `subprocess`, `tempfile`, `time`, `json`, `unittest`), bash, markdown.

**Spec:** [2026-11-01-refresh-session-design.en.md](../specs/2026-11-01-refresh-session-design.en.md)

## Table of Contents

- [Global Constraints](#global-constraints)
- [File Structure](#file-structure)
- [Tasks](#tasks)
  - [Task 1: Core Python Engine and Comprehensive Unit Tests](#task-1-core-python-engine-and-comprehensive-unit-tests)
  - [Task 2: Skill Definition and Verification Harness Integration](#task-2-skill-definition-and-verification-harness-integration)
- [Final Verification](#final-verification)

---

## Global Constraints

- **Strict Isolation**: Both `claude` and `codex` must always run inside an ephemeral temporary directory (`tempfile.TemporaryDirectory`) to avoid scanning workspace files or `.rules`.
- **Zero Skill/Plugin/MCP Initialization**:
  - Claude: `--safe-mode --disable-slash-commands --tools "" --model haiku -p "1"`. Never use `--bare` as it bypasses keychain OAuth authentication.
  - Codex: `--disable plugins --disable apps --disable hooks --ephemeral --skip-git-repo-check --ignore-user-config --ignore-rules -c model_reasoning_effort=low "1"`.
- **Coding Standards**:
  - Python standard library only for the script engine (zero third-party dependencies).
  - Strict type hints passing `mypy --strict --follow-imports=silent`.
  - Zero lint violations passing `ruff check`.
- **SKILL.md Frontmatter Standard**:
  - Exactly two keys: `name` and `description` (no extra keys).
  - `name`: `refresh-session`.
  - `description`: Third-person, stating what it does and when to use it.
- **Commit Formatting**:
  - Commit message format: `[REFRESH_SESSION] <title>` with a bullet list of changes.
  - Never append trailer lines or tool attributions (`Co-Authored-By:`, `Generated with`).
- **Verification Gate**:
  - All tests must pass via `scripts/verify.sh`.

---

## File Structure

| File | Responsibility |
|---|---|
| `skills/refresh-session/resources/scripts/refresh_session.py` | Create. Standalone CLI engine executing sandboxed pings against Claude and Codex. |
| `skills/refresh-session/resources/scripts/test_refresh_session.py` | Create. Comprehensive unit tests covering argument parsing, command assembly, sandboxing, token extraction, and timeout handling. |
| `skills/refresh-session/SKILL.md` | Create. Standardized skill documentation with 2-key YAML frontmatter. |
| `scripts/verify.sh` | Modify. Wire `test_refresh_session.py` into test suite section 11. |

---

## Tasks

### Task 1: Core Python Engine and Comprehensive Unit Tests

**Files:**
- Create: `skills/refresh-session/resources/scripts/refresh_session.py`
- Create: `skills/refresh-session/resources/scripts/test_refresh_session.py`

- [ ] **Step 1: Write the failing unit tests (RED)**
  Create `skills/refresh-session/resources/scripts/test_refresh_session.py` with test cases:
  - `test_parse_arguments_default`: Verifies target defaults to `"all"`, timeout defaults to `60`, json is `False`.
  - `test_parse_arguments_targets`: Verifies `"claude"`, `"codex"`, and `"all"` target parsing.
  - `test_parse_arguments_invalid_target`: Verifies error exit code on invalid target choice.
  - `test_build_claude_command`: Asserts exact command flags: `["claude", "--safe-mode", "--disable-slash-commands", "--tools", "", "--model", "haiku", "-p", "1"]`.
  - `test_build_codex_command`: Asserts exact command flags: `["codex", "exec", "--disable", "plugins", "--disable", "apps", "--disable", "hooks", "--ephemeral", "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules", "-c", "model_reasoning_effort=low", "1"]`.
  - `test_extract_token_usage`: Verifies regex extraction of tokens from both stdout patterns (`tokens used <N>`, `Tokens: <N>`).
  - `test_run_ping_missing_cli`: Mock `shutil.which` returning `None`; verifies graceful skip status without exception.
  - `test_run_ping_success_mocked`: Mock `subprocess.run` inside temporary directory; verify execution, latency measurement, and result dictionary.
  - `test_run_ping_timeout_mocked`: Mock `subprocess.TimeoutExpired`; verify timeout error reporting.
  - `test_main_json_output`: Verify `--json` outputs well-formed JSON report.

- [ ] **Step 2: Run tests to confirm RED state**
  Run: `python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py`
  Expected: ModuleNotFoundError or failure because `refresh_session.py` does not exist yet.

- [ ] **Step 3: Implement `refresh_session.py` (GREEN)**
  Create `skills/refresh-session/resources/scripts/refresh_session.py`:
  - `build_claude_command(prompt: str = "1", model: str = "haiku") -> list[str]`
  - `build_codex_command(prompt: str = "1", reasoning_effort: str = "low") -> list[str]`
  - `extract_tokens(output: str) -> int | None`
  - `ping_cli(cli_name: str, timeout: int = 60) -> dict[str, Any]` executing in `tempfile.TemporaryDirectory()`
  - `main(argv: list[str] | None = None) -> int` with `argparse`, formatted console summary, and JSON output support.

- [ ] **Step 4: Run unit tests to confirm GREEN state**
  Run: `python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py`
  Expected: All tests PASS.

- [ ] **Step 5: Code hygiene and type check**
  Run:
  - `ruff check skills/refresh-session/resources/scripts/`
  - `mypy --strict --follow-imports=silent skills/refresh-session/resources/scripts/refresh_session.py skills/refresh-session/resources/scripts/test_refresh_session.py`
  Expected: Clean exit code 0.

- [ ] **Step 6: Commit Task 1**
  Stage and commit:
  ```bash
  git add skills/refresh-session/resources/scripts/
  git commit -m "[REFRESH_SESSION] Implement refresh_session.py engine and unit tests" -m "- Add sandboxed CLI command builders for Claude and Codex
  - Add TemporaryDirectory isolation ensuring zero repository context scan
  - Add comprehensive unit test suite covering argument parsing and mocking"
  ```

---

### Task 2: Skill Definition and Verification Harness Integration

**Files:**
- Create: `skills/refresh-session/SKILL.md`
- Modify: `scripts/verify.sh`

- [ ] **Step 1: Create `skills/refresh-session/SKILL.md`**
  Author `skills/refresh-session/SKILL.md`:
  - Frontmatter:
    ```yaml
    ---
    name: refresh-session
    description: Ping Claude Code and Codex CLIs to refresh 5-hour rolling session windows with minimum token consumption and zero skill initialization.
    ---
    ```
  - Sections:
    - Overview and purpose of session pre-warming.
    - Usage instructions for `/refresh-session`, `/refresh-session claude`, `/refresh-session codex`, and `/refresh-session all`.
    - Instructions directing the agent to run `python3 skills/refresh-session/resources/scripts/refresh_session.py <target>`.
    - Explanation of the isolation guarantees.

- [ ] **Step 2: Wire into `scripts/verify.sh`**
  Modify `scripts/verify.sh` under Section 11 (or Section 14) to include running `test_refresh_session.py`:
  ```bash
  python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py
  ```

- [ ] **Step 3: Run full verification harness**
  Run: `bash scripts/verify.sh`
  Expected: All 15 verification gates pass with `PASS — safe to publish`.

- [ ] **Step 4: Commit Task 2**
  Stage and commit:
  ```bash
  git add skills/refresh-session/SKILL.md scripts/verify.sh
  git commit -m "[REFRESH_SESSION] Add refresh-session skill and wire into verify.sh" -m "- Author refresh-session/SKILL.md with standardized 2-key frontmatter
  - Register test_refresh_session.py in scripts/verify.sh test suite"
  ```

---

## Final Verification

- [ ] **Live CLI Execution Test**:
  Run: `python3 skills/refresh-session/resources/scripts/refresh_session.py all`
  Verify both Claude and Codex respond successfully in isolated temporary directories.
- [ ] **JSON Output Verification**:
  Run: `python3 skills/refresh-session/resources/scripts/refresh_session.py all --json`
  Verify output parses as valid JSON with `status: "PASS"` and latency/token fields.
- [ ] **Document Quality Check**:
  Run: `python3 skills/doc_quality_check/resources/scripts/check_document.py docs/superpowers/plans/2026-11-01-refresh-session.en.md docs/superpowers/plans/2026-11-01-refresh-session.vi.md`
  Verify 0 findings.
- [ ] **Final Repository Gate**:
  Run: `bash scripts/verify.sh`
  Ensure clean exit 0.
