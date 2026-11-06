# Verification Row Grammar and Diagnostics Reference

This document provides the canonical grammar rules, command syntax, and diagnostic behavior enforced by `check_task_contract.py`, `task_contract.py`, and `run_task_checks.py` for task `## Verification` tables.

## Table of Contents

- [Overview](#overview)
- [Rule 1: Escaped Pipes in Table Cells](#rule-1-escaped-pipes-in-table-cells)
- [Rule 2: Environment Variable Prefixing](#rule-2-environment-variable-prefixing)
- [Rule 3: Search Patterns Containing Slashes](#rule-3-search-patterns-containing-slashes)
- [Rule 4: Evidence Files Declarations](#rule-4-evidence-files-declarations)
- [Rule 5: Portable CLI and Kit Runtime Injection](#rule-5-portable-cli-and-kit-runtime-injection)
- [Rule 6: Dynamic Code Fencing for Embedded Tasks](#rule-6-dynamic-code-fencing-for-embedded-tasks)
- [Implicit Protected Paths Provenance](#implicit-protected-paths-provenance)

## Overview

Task contracts enforce strict validation over Verification tables to guarantee reproducible automated test execution across machines, platforms, and AI agent runtimes. This reference outlines the syntactic and semantic rules enforced during static design checks (`check_task_contract.py --design`) and task execution (`run_task_checks.py verify`).

## Rule 1: Escaped Pipes in Table Cells

Markdown tables use the pipe character (`|`) to delimit columns. When a shell command inside a table cell contains a pipeline operator or logical OR (`|` or `||`), it must be escaped with a backslash (`\|`).

- **Authoring syntax**: Write `\|` inside table command cells, for example: `env MODE=strict python3 tool.py \| grep -c ok`.
- **Parser unescaping**: `task_contract.py` unescapes `\|` back to `|` when parsing table rows. Reviewers and automated tools must treat `\|` as valid escaped syntax rather than broken command formatting.

## Rule 2: Environment Variable Prefixing

Inline shell environment variable assignments must always be explicitly prefixed with `env`.

- **Forbidden syntax**: `FOO=bar pytest tests/unit/test_sample.py`
  - *Diagnostic*: `check_grounding` reports `"inline environment assignment 'FOO=bar' must be prefixed with 'env' (e.g. 'env FOO=bar ...')"` because shlex parses bare `FOO=bar` as an executable name rather than an assignment.
- **Allowed syntax**: `env FOO=bar pytest tests/unit/test_sample.py`
  - The `env` prefix allows POSIX argument parsing and wrapper stripping across all supported shell runners.

## Rule 3: Search Patterns Containing Slashes

Subcommands invoking search utilities (`grep`, `egrep`, `fgrep`, `rg`, `sed`, `awk`) frequently use regex patterns containing slashes (such as `grep -E 'foo/bar/baz' README.md` or `sed 's/foo/bar/g' file.txt`).

- **Diagnostic behavior**: `command_paths()` automatically skips the pattern argument (the token following `-e`/`--regexp`, or the first non-flag positional argument when no `-e`/`-f` flag is present).
- **Result**: The search pattern is excluded from path extraction so patterns with slashes are not falsely flagged as missing repository files.

## Rule 4: Evidence Files Declarations

Tasks that produce persistent verification artifacts (such as baseline comparisons, diff outputs, or contract snapshots) must declare them in an explicit `Evidence files:` subsection under `## Files`.

- **Declaration syntax**:
  ```markdown
  ## Files

  Allowed files:
  - `src/feature.py`

  Evidence files:
  - `.devtool/epic/my_epic/evidence/baseline.txt` (new)
  ```
- **Done gate enforcement**: `evaluate_done_gate()` verifies that every declared evidence file exists on disk and is non-empty (> 0 bytes) upon task completion.

## Rule 5: Portable CLI and Kit Runtime Injection

Verification rows must be portable across machines, accounts, profiles, and environments.

- **Forbidden paths**: Hardcoded user directories or cache roots (`/Users/`, `/home/`, `~/`, `.claude/plugins/cache/`, `.gemini/config/plugins/`) are strictly rejected with a contract error.
- **Portable execution**:
  - Use `d3nexus <subcommand>` (e.g. `d3nexus check-doc --require-toc README.md`).
  - Or use `$D3NEXUS_KIT/<path>` when referencing kit resources.
- **Runtime injection**: `run_task_checks.py` and `check_epic_readiness.py` automatically inject `D3NEXUS_KIT` and prepend `<kit_root>/bin` to child process `PATH` without mutating parent process environment variables.

## Rule 6: Dynamic Code Fencing for Embedded Tasks

When task contracts or BDD scenarios embed code blocks, task mirrors or HLD sections must use dynamic outer fence calculation:

- **Fence rule**: The outer fence must have length `N = max(4, max_inner_backtick_run + 1)`.
- **Rendering engine**: `sync_task_status.py render` automatically calculates the maximum internal backtick run and promotes outer fences to guarantee parseable markdown across nested code snippets.

## Implicit Protected Paths Provenance

When verification rows execute tracked scripts (such as `scripts/verify.sh` or `python3 scripts/tool.py`), those scripts become implicit protected paths to prevent accidental modification during implementation tasks.

- **Provenance reporting**: `check_task_contract.py` outputs full provenance for each implicit protected path:
  `Implicit protected paths: scripts/tool.py (task_01:V1), scripts/verify.sh (task_02:V3)`
- This enables authors and reviewers to identify exactly which task and row established protection over a given file.
