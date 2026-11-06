---
id: "task_03_portable_d3nexus_cli_and_env"
status: "done"
priority: "high"
assignee: null
epic: "contract-and-authoring-ergonomics"
dueDate: null
created: "2026-11-06T01:50:00Z"
modified: "2026-11-06T03:23:59Z"
completedAt: "2026-11-06T03:23:59Z"
labels: ["architecture", "portability", "cli"]
order: "a3"
---

# Task 03: Portable d3nexus CLI and Zero-Setup Runtime Environment Injection

Epic: [contract_and_authoring_ergonomics](../../epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md)

## Requirement Analysis

Resolve Observation #0016: task Verification rows invoke kit scripts (`check_document.py`) using machine- and profile-specific absolute paths (`/Users/.../antigravity_homes/tess/.claude/plugins/cache/...`), which fail when run on another machine, OS user, account profile, or plugin version.

This task provides a zero-setup portable CLI entrypoint and bans hardcoded user/plugin paths in Verification rows:
1. Create executable `bin/d3nexus` dispatching subcommands (`check-doc`, `check-contract`, `check-readiness`, `sync-status`, `run-checks`) to the kit's scripts relative to `Path(__file__).resolve().parent.parent`.
2. In `run_task_checks.py` (`run_command()`) and `check_epic_readiness.py`, automatically compute `KIT_ROOT = Path(__file__).resolve().parents[4]` and inject `D3NEXUS_KIT=str(KIT_ROOT)` and `PATH="<kit_root>/bin:$PATH"` into the child process environment without mutating `os.environ` of the parent process.
3. Update `scripts/resume_context.py` (`--sync-zshrc`) so interactive terminal shells also export `D3NEXUS_KIT` and prepend `<kit_root>/bin` to `PATH`.
4. In `check_task_contract.py` and `task_contract.py`, reject any Verification row command containing hardcoded user home or plugin cache paths (`/Users/`, `/home/`, `~/`, `.claude/plugins/cache/`, `.gemini/config/plugins/`), recognize `d3nexus` as a built-in kit executable, and resolve `d3nexus <subcommand>` in `program_of(command, root)` to the dispatched kit script path when tracked in `root` so implicit checker protection is preserved.

## Files

Allowed files:
- `bin/d3nexus` (new)
- `skills/dev-implementation/resources/scripts/run_task_checks.py`
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- `skills/dev-implementation/resources/scripts/task_contract.py`
- `scripts/resume_context.py`
- `skills/dev-implementation/resources/scripts/test_run_task_checks.py`
- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`

Read-only context:
- `skills/doc_quality_check/resources/scripts/check_document.py` (target of `d3nexus check-doc`)
- `.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md` (HLD specification)

## Design Rationale

Applicable skills: `python-quality-check`, `test-driven-development`.
Deriving `KIT_ROOT` dynamically from `Path(__file__).resolve().parents[4]` inside `run_task_checks.py` guarantees zero manual setup when switching machines, accounts, or plugin cache versions.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/run_task_checks.py`: `run_command` and new `kit_env`.
  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `command_paths`, `check_grounding`, and new `check_portable_command`.
  - `skills/dev-implementation/resources/scripts/task_contract.py`: `strip_wrappers`, `program_of`.
- **Downstream Callers**: `skills/dev-implementation/resources/scripts/check_epic_readiness.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on `bin/d3nexus`, `kit_env`, and `check_portable_command`.

### BDD SCENARIOS

Covers: TCAE-HP-03, TCAE-AR-01

```gherkin
Scenario: [TCAE-HP-03] [Tier C - Integration] Zero-setup d3nexus CLI execution inside Verification rows
  Given a task Verification row invoking "d3nexus check-doc --require-toc .devtool/epic/sample_epic/sample_epic.en.md"
  When "run_task_checks.py verify" executes the task in a temporary git repository without pre-configured shell exports
  Then "run_task_checks.py" automatically injects "D3NEXUS_KIT" and prepends "<kit_root>/bin" to "PATH"
  And "d3nexus check-doc" dispatches to "check_document.py" and exits 0

Scenario: [TCAE-AR-01] [Tier A - Unit] Isolated subprocess environment injection across concurrent row executions
  Given two concurrent invocations of "run_task_checks.py" running in separate temporary git worktrees
  When each invocation executes a Verification row printing "$D3NEXUS_KIT" and "$(which d3nexus)"
  Then both subprocesses resolve the exact kit root path without mutating "os.environ" of the parent Python process
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_run_task_checks.py::test_TCAE_HP_03_d3nexus_zero_setup_env` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_run_task_checks.py skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py bin/d3nexus skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/task_contract.py scripts/resume_context.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/task_contract.py --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_run_task_checks.py skills/dev-implementation/resources/scripts/test_check_task_contract.py --junitxml=build/test-results/task_03.xml` | exit 0; results build/test-results/task_03.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- `KIT_ROOT` in `skills/dev-implementation/resources/scripts/run_task_checks.py` is `Path(__file__).resolve().parents[4]`.
- `kit_env() -> dict[str, str]` returns a copy of `os.environ` with `D3NEXUS_KIT=str(KIT_ROOT)` and `PATH=f"{KIT_ROOT / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"`.
- `bin/d3nexus` is an executable Python 3 script (`0o755`) supporting subcommands:
  - `check-doc` -> `skills/doc_quality_check/resources/scripts/check_document.py`
  - `check-contract` -> `skills/dev-implementation/resources/scripts/check_task_contract.py`
  - `check-readiness` -> `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
  - `sync-status` -> `skills/dev-implementation/resources/scripts/sync_task_status.py`
  - `run-checks` -> `skills/dev-implementation/resources/scripts/run_task_checks.py`
- `NON_PORTABLE_PATH_RE` in `check_task_contract.py` matches `(?:/Users/|/home/|~/|\.claude/plugins/cache/|\.gemini/config/plugins/)` and reports `"non-portable path '<match>' in command; use 'd3nexus <subcommand>' or '$D3NEXUS_KIT/...'"`.
- In `skills/dev-implementation/resources/scripts/task_contract.py`, `program_of(command: str, root: Path)` resolves `d3nexus <subcommand>` (and `bin/d3nexus <subcommand>`) via `D3NEXUS_SUBCOMMANDS` to the dispatched script path (e.g. `skills/doc_quality_check/resources/scripts/check_document.py`) when that target is git-tracked in `root`, so `protected_patterns()` in `run_task_checks.py:300` and `check_task_contract.py` preserve implicit checker protection when rows invoke `d3nexus`.

## Definition of Done

- `bin/d3nexus` dispatches kit subcommands, is automatically placed on `PATH` with `D3NEXUS_KIT` by `run_task_checks.py` and `check_epic_readiness.py`, and preserves implicit checker protection in `program_of(command, root)`. (V2, V5)
- `check_task_contract.py` rejects hardcoded user home and plugin cache paths in Verification rows. (V2)
- `ruff` and `mypy` pass with zero errors. (V3, V4)
- Automated tests for `TCAE-HP-03`, `TCAE-AR-01`, and non-portable path rejection pass and write JUnit XML results. (V5)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 02](../../epic/contract_and_authoring_ergonomics/task_02_single_source_render_engine.md)

## References & Rollback

- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](../../epic/contract_and_authoring_ergonomics/2026-11-06-contract-and-authoring-ergonomics-design.en.md).
- Rollback: `git revert` the task commit to remove `bin/d3nexus` and restore runtime scripts.
