---
id: "task_03_ohk_python_uv_bootstrap_and_doc_refusal"
status: "done"
priority: "high"
assignee: null
epic: "observer-hardening-2026-11"
dueDate: null
created: "2026-11-26T22:10:00Z"
modified: "2026-11-26T16:45:17Z"
completedAt: "2026-11-26T16:45:17Z"
labels: ["architecture", "python-env", "verification-hygiene"]
order: "a3"
review_tier: "full"
---

# Task 3: Bootstrap Python `uv` Optional Extras with `UV_NO_SYNC=1` Preservation and Fix Newline Splitting in `check_document.py`

Epic: [observer-hardening-2026-11](../../epic/observer_hardening_2026_11/observer_hardening_2026_11.md)

## Requirement Analysis

Fix two verification-environment and refusal-gate defects:

1. **Observation `#11` Kit Portion (`bootstrap_worktree.sh` & `verify_polyglot_registry.py`)**:
   - In `bootstrap_worktree.sh`, the fallback `uv sync` omits `[project.optional-dependencies]` extras required by `epic` quality profiles. Inspect `pyproject.toml` via Python `tomllib` (falling back safely on missing/invalid TOML): include `--all-extras` when `[project.optional-dependencies]` is non-empty, and `--group dev` when `[dependency-groups].dev` is declared.
   - In `verify_polyglot_registry.py` (`_run_capability_subprocess`), whenever a capability command invokes `uv run ...`, inject `UV_NO_SYNC=1` via `env.setdefault("UV_NO_SYNC", "1")` so `uv run` does not silently prune optional extras mid-Gate 4 while still respecting explicit caller `UV_NO_SYNC` overrides.
2. **Observation `#9` (`check_document.py` `refusal()` & `main()`)**:
   - In zsh (where `SH_WORD_SPLIT` is off), unquoted `--changed-files $(git diff --name-only ...)` passes a single newline-joined string, allowing a leading build-shipping file (e.g. `src/app.py\ndocs/guide.en.md`) to evade `refusal()` by matching `.md` on the trailing line.
   - Flatten `changed` on `\r\n`/`\n` (ignoring blank lines) inside `refusal()` and use the flattened count in `main()`'s summary output.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/bootstrap_worktree.sh`
- `skills/quality_check/resources/scripts/verify_polyglot_registry.py`
- `skills/doc_quality_check/resources/scripts/check_document.py`
- `tests/test_polyglot_gate4.py`
- `tests/test_ohk_python_env_and_doc_refusal.py` (new)

Read-only context:
- `.devtool/epic/observer_hardening_2026_11/2026-11-26-observer-hardening-design.md`
- `.devtool/epic/observer_hardening_2026_11/observer_hardening_2026_11.md`

## Design Rationale & Applicable Skills

- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.
- Strictly standard-library Python (`tomllib`) with safe fallback; zero modifications to any external repository's `.agents/quality/python-quality.json`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/bootstrap_worktree.sh`: Python fallback bootstrap block (L103-L116).
  - `skills/quality_check/resources/scripts/verify_polyglot_registry.py`: `_run_capability_subprocess` (L881-L962).
  - `skills/doc_quality_check/resources/scripts/check_document.py`: `refusal` (L217-L226), `main` (L228-L248).
  - `tests/test_polyglot_gate4.py`: capability execution tests (L1-L576).
- **Downstream Callers**: `skills/doc_quality_check/resources/scripts/test_check_document.py`, `tests/test_polyglot_gate4.py`, `skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`.
- **Target Coverage**: 100% of modified branches in `bootstrap_worktree.sh`, `verify_polyglot_registry.py`, and `check_document.py`.

### BDD SCENARIOS

Covers: OHK-HP-03, OHK-EC-03, OHK-FR-02

```gherkin
Scenario: [OHK-HP-03] [Tier C - Integration] Bootstrap Python worktree with optional extras and preserve them with UV_NO_SYNC
Given a Python repository worktree whose pyproject.toml declares "[project.optional-dependencies]" and "[dependency-groups].dev"
And no custom "bootstrap" command is configured in ".agents/quality/python-quality.json"
When "bootstrap_worktree.sh" runs against the worktree with a recording fake "uv" binary on PATH
Then the invoked uv command includes "sync", "--all-extras", and "--group", "dev"
When verify_polyglot_registry.py executes a capability command starting with ["uv", "run", ...]
Then the child process receives "UV_NO_SYNC=1" in its environment

Scenario: [OHK-EC-03] [Tier C - Integration] Document refusal gate catches build-shipping file hidden inside newline-joined zsh argument
Given "--changed-files" receives a single newline-joined string "src/app.py\ndocs/guide.en.md\n" simulating zsh unquoted command substitution
When "check_document.py --changed-files" runs refusal evaluation
Then it exits 1 and reports "ships in the build: src/app.py"
When "--changed-files" receives a newline-joined string of three documentation files "docs/a.md\ndocs/b.md\nCHANGELOG.md"
Then it exits 0 and reports "none of 3 changed files ship in the build"

Scenario: [OHK-FR-02] [Tier C - Integration] Respect explicit caller UV_NO_SYNC override and fallback cleanly on malformed pyproject.toml
Given a Python repository whose pyproject.toml has no "[project.optional-dependencies]" table
When "bootstrap_worktree.sh" runs with a recording fake "uv" binary on PATH
Then it invokes bare "uv sync" without "--all-extras"
When verify_polyglot_registry.py runs a "uv run" capability while caller environment explicitly sets "UV_NO_SYNC=0"
Then the child process inherits "UV_NO_SYNC=0" without being clobbered
```

## Verification

| ID | Phase | Command | Expect | Needs |
|---|---|---|---|---|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_python_env_and_doc_refusal.py::test_ohk_ec_03_newline_joined_refusal` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_python_env_and_doc_refusal.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m unittest skills/doc_quality_check/resources/scripts/test_check_document.py skills/quality_check/resources/scripts/test_quality_provider_acceptance.py && python3 -m pytest -q --tb=short --maxfail=3 tests/test_polyglot_gate4.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/doc_quality_check/resources/scripts/check_document.py && ruff format --check skills/quality_check/resources/scripts/verify_polyglot_registry.py tests/test_polyglot_gate4.py tests/test_ohk_python_env_and_doc_refusal.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && mypy --ignore-missing-imports --follow-imports=silent skills/doc_quality_check/resources/scripts/check_document.py tests/test_polyglot_gate4.py tests/test_ohk_python_env_and_doc_refusal.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_python_env_and_doc_refusal.py --junitxml=build/test-results/task_03.xml` | exit 0; results build/test-results/task_03.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`bootstrap_worktree.sh:103-115`)**: Runs `(cd "$WORKTREE_PATH" && uv sync)` when no custom `bootstrap` array exists.
  - **New contract**: Parse `$WORKTREE_PATH/pyproject.toml` with Python `tomllib` (falling back silently on `ImportError`, `OSError`, or TOML decode error). Emit `--all-extras` when `bool(data.get("project", {}).get("optional-dependencies"))` is True, and `--group dev` when `"dev" in (data.get("dependency-groups") or {})` (only when `optional-dependencies` is non-empty, or whenever declared; keep bare `uv sync` when neither optional-dependencies nor explicit extra flags are needed).
- **Source (`verify_polyglot_registry.py:881-915`)**: `_run_capability_subprocess` spawns `subprocess.Popen(substituted_cmd, cwd=str(root), stdout=log_fh, stderr=subprocess.STDOUT, start_new_session=True)` without injecting `UV_NO_SYNC`.
  - **New contract**: Add helper `_build_capability_env(substituted_cmd: list[str], base_env: Mapping[str, str] | None = None) -> dict[str, str] | None`. When `len(substituted_cmd) >= 2 and Path(substituted_cmd[0]).name == "uv" and substituted_cmd[1] == "run"`, return a copy of `base_env or os.environ` with `env.setdefault("UV_NO_SYNC", "1")`. Pass `env=child_env` to `subprocess.Popen`.
- **Source (`check_document.py:217-248`)**: `refusal(changed)` iterates `for f in changed:` directly without splitting `\n`, and `main()` prints `len(args.changed_files)`.
  - **New contract**: Add `_flatten_changed(changed: list[str]) -> list[str]` splitting each item via `.splitlines()` and stripping empty strings. Use `_flatten_changed(changed)` in `refusal()` and in `main()`'s `none of {len(flattened)} changed files ship in the build` print line.

## Definition of Done

- [x] `bootstrap_worktree.sh` selects `uv sync --all-extras [--group dev]` when `[project.optional-dependencies]` exists and falls back to bare `uv sync` otherwise (V2, V4, V6) — exit 0, 6 passed
- [x] `verify_polyglot_registry.py` sets `UV_NO_SYNC=1` (via `setdefault`) on `uv run` capabilities without clobbering caller overrides (V2, V3, V4, V5, V6) — exit 0, 6 + 28 + 9 passed
- [x] `check_document.py` splits newline-joined `--changed-files` arguments in `refusal()` and reports accurate flattened counts (V2, V3, V4, V5, V6) — exit 0, 6 + 28 + 9 passed
- [x] Assigned BDD integration scenarios (`OHK-HP-03`, `OHK-EC-03`, `OHK-FR-02`) pass with JUnit XML evidence (V6) — exit 0, 3/3 covered in build/test-results/task_03.xml

## Dependencies & Blockers

None.

## References & Rollback

- Spec: [2026-11-26-observer-hardening-design.md](../../epic/observer_hardening_2026_11/2026-11-26-observer-hardening-design.md)
- HLD: [observer_hardening_2026_11.md](../../epic/observer_hardening_2026_11/observer_hardening_2026_11.md)
- BDD: [bdd_scenarios.md](../../epic/observer_hardening_2026_11/bdd_scenarios.md)
- Rollback: Revert this task's commit on `epic/observer-hardening-2026-11`.
