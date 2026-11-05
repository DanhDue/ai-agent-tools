---
id: "task_04_verification_grammar_and_docs"
status: "todo"
priority: "high"
assignee: null
epic: "contract-and-authoring-ergonomics"
dueDate: null
created: "2026-11-06T01:50:00Z"
modified: "2026-11-06T01:50:00Z"
completedAt: null
labels: ["architecture", "grammar", "documentation"]
order: "a4"
---

# Task 04: Verification Row Grammar Diagnostics and Reference Documentation

Epic: [contract_and_authoring_ergonomics](contract_and_authoring_ergonomics.en.md)

## Requirement Analysis

Resolve Observation #0019: authors and reviewers repeatedly encounter undocumented grammar rules in Verification tables:
1. `task_contract.py` unescapes `\|` to `|` in table cells, which caused a Principal Review round to falsely flag valid rows as broken.
2. Inline `VAR=value cmd` without `env` is parsed as an executable named `VAR=value`.
3. Search patterns in `grep`, `rg`, `sed`, and `awk` containing `/` (such as `grep -E 'foo/bar' file.txt`) are misclassified by `command_paths()` as missing file paths.
4. Tracked scripts executed by a row become implicit protected paths without reporting which task/row triggered them.

This task improves `check_task_contract.py` diagnostics, creates the canonical `skills/dev-designer/references/verification-row-grammar.md` reference, and updates `skills/dev-designer/SKILL.md` and `skills/principal-review/SKILL.md`.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
- `skills/dev-designer/references/verification-row-grammar.md` (new)
- `skills/dev-designer/SKILL.md`
- `skills/principal-review/SKILL.md`

Read-only context:
- `skills/dev-designer/references/verification-rows.md` (existing per-platform example rows)
- `.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md` (HLD specification)

## Design Rationale

Applicable skills: `python-quality-check`, `doc_quality_check`, `test-driven-development`.
Centralizing all Verification table grammar rules in `skills/dev-designer/references/verification-row-grammar.md` and aligning `check_task_contract.py` diagnostics with `principal-review` eliminates false positives in both automated checks and AI reviews.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `command_paths`, `check_grounding`, `main`.
- **Downstream Callers**: `skills/dev-implementation/resources/scripts/check_epic_readiness.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on `command_paths` and grammar diagnostics in `check_task_contract.py`.

### BDD SCENARIOS

Covers: TCAE-HP-04, TCAE-EC-03

```gherkin
Scenario: [TCAE-HP-04] [Tier A - Unit] Verification row grammar with escaped pipes, env assignments, and implicit protected path provenance
  Given a Verification row command using "env MODE=strict python3 scripts/tool.py \| grep -c ok"
  When "check_task_contract.py --design" evaluates the task
  Then "task_contract.py" unescapes "\|" to "|" in the parsed command without raising a contract problem
  And "check_task_contract.py" reports "scripts/tool.py (task_01:V1)" in the "Implicit protected paths:" line

Scenario: [TCAE-EC-03] [Tier A - Unit] Search patterns containing slashes in grep, rg, sed, and awk are not flagged as missing paths
  Given a Verification row command "grep -E 'foo/bar/baz' README.md" where "foo/bar/baz" is not a file on disk
  When "check_task_contract.py --design" inspects the command tokens
  Then "command_paths()" excludes the search pattern "foo/bar/baz" from path existence checks
  And "check_task_contract.py" exits 0 without reporting "foo/bar/baz does not exist"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py::test_TCAE_EC_03_grep_slash_pattern_excluded` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent skills/dev-implementation/resources/scripts/check_task_contract.py` | exit 0 | — |
| V5 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc skills/dev-designer/references/verification-row-grammar.md` | exit 0; contains "0 findings" | — |
| V6 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py --junitxml=build/test-results/task_04.xml` | exit 0; results build/test-results/task_04.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- In `skills/dev-implementation/resources/scripts/check_task_contract.py`, `command_paths(command: str)` splits subcommands on `tc.CONTROL_TOKENS` (`&&`, `||`, `;`, `|`). For any subcommand whose unwrapped program is `grep`, `egrep`, `fgrep`, `rg`, `sed`, or `awk`, the pattern argument (the token after `-e`/`--regexp` or the first non-flag positional argument when no `-e`/`-f` flag is present) is skipped before collecting path tokens.
- When the first token of a subcommand (before `env`) matches `^[A-Za-z_][A-Za-z0-9_]*=.*`, `check_grounding` records a problem: `"inline environment assignment '<token>' must be prefixed with 'env' (e.g. 'env <token> ...')"`.
- `Implicit protected paths:` in `check_task_contract.py` formats each entry as `<path> (<task_stem>:<row_id>, ...)`.
- `skills/dev-designer/references/verification-row-grammar.md` includes a `## Table of Contents` and documents all 6 rules (`\|` unescaping, `env VAR=val`, grep pattern rules, `Evidence files:`, `d3nexus` / `$D3NEXUS_KIT`, and dynamic `max(4, max_inner_backtick_run + 1)` outer code fences).

## Definition of Done

- `command_paths()` excludes `grep`/`rg`/`sed`/`awk` pattern arguments from missing-path errors and reports bare `VAR=val` assignments and implicit protected path provenance. (V2)
- `skills/dev-designer/references/verification-row-grammar.md`, `skills/dev-designer/SKILL.md`, and `skills/principal-review/SKILL.md` are updated and pass document linting. (V5)
- `ruff` and `mypy` pass with zero errors. (V3, V4)
- Automated tests for `TCAE-HP-04` and `TCAE-EC-03` pass and write JUnit XML results. (V6)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 03](task_03_portable_d3nexus_cli_and_env.md)

## References & Rollback

- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](2026-11-06-contract-and-authoring-ergonomics-design.en.md).
- Rollback: `git revert` the task commit to restore `check_task_contract.py` and skill documentation.
