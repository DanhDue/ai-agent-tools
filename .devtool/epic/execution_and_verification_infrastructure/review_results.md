# Cross-Model Review: execution_and_verification_infrastructure

## Round 1

- **Date**: 2026-11-06T17:40:51Z
- **SHA**: 2d235f04748682631d6cf3d45143fce83d287ff7
- **Base**: main
- **CLI**: claude
- **Model**: opus
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Critical | skills/dev-implementation/resources/scripts/record_failure_baseline.py:34 | `extract_pytest_failures()` truncates at the header's own `=` padding (`summary_text.find("===")` returns 0), returning `[]` for all real pytest output; baselines record `# 0 failures` and `compare_failure_sets.py` exits 0 on genuine new regressions, voiding the Observation #0007 deliverable | fixed in cb8a843 |
| 2 | Important | skills/dev-implementation/resources/scripts/test_failure_baseline.py:33 | every test for EVI-HP-02/EVI-EC-01/EVI-AR-02 feeds a synthetic 3-equals `=== short test summary info ===` header instead of captured runner output, altering the scenario anchor and masking the parser defect | fixed in cb8a843 |
| 3 | Important | skills/dev-implementation/resources/scripts/record_failure_baseline.py:21 | `NODE_SPEC_FAIL_RE` captures the duration parenthetical of real `node --test` spec output as the file path, yielding non-deterministic IDs like `0.483083ms::failing one` so node baselines never match across runs | fixed in cb8a843 |
| 4 | Important | skills/dev-implementation/resources/scripts/bootstrap_worktree.sh:38 | `except Exception: sys.exit(1)` swallows a failing declared `"bootstrap"` command, silently falling back to `uv sync` and reporting `Worktree bootstrap complete` with exit 0 | fixed in c029714 |
| 5 | Important | skills/dev-implementation/resources/scripts/run_external_review.py:454 | the non-live `elif reports:` path still passes the whole `build/test-results` directory to `check_bdd_traceability.py --results`, contradicting the HLD and task_03 Decisions; reverted by out-of-task commit `2795098` to preserve two pre-existing test assertions | fixed in 0957b08 |
| 6 | Important | skills/dev-designer/SKILL.md:51 | the documented `"bootstrap"` example `["uv sync", "uv run playwright install"]` is a list of strings, which `validate_python_config()` rejects with `invalid_bootstrap_format` | fixed in 5457174 |
| 7 | Minor | skills/dev-implementation/resources/scripts/replay_task_text.py:55 | only `Create <path>:` of the HLD's three full-file-write forms is implemented; `<!-- @@FILE:...@@ -->` and `File: <path>` are silent no-ops | fixed in 87a3ad7 |
| 8 | Minor | skills/dev-implementation/resources/scripts/run_task_checks.py:242 | HLD §5 documents `--timeout 0` as unbounded for `measure`, but `communicate(timeout=0)` raises `TimeoutExpired` immediately and SIGKILLs the process group | fixed in 87a3ad7 |
| 9 | Minor | tests/test_execution_infra_acceptance.py:18 | the file covers only `EVI-AR-01` while the HLD's Tier C1 strategy names five areas for it; remaining Tier C scenarios rely on thin wrappers re-calling unit tests | dismissed: Acceptance suite focuses directly on EVI-AR-01 worktree replay while dedicated Tier C integration suites validate individual components. |
| 10 | Minor | skills/dev-implementation/resources/scripts/test_replay_and_measure.py:206 | the `--resume` cache-hit assertion is only `== 0`, which a re-execution also satisfies; nothing asserts the MEASURE subprocess was skipped | fixed in 87a3ad7 |
| 11 | Minor | skills/dev-implementation/resources/scripts/replay_task_text.py:261 | MEASURE rows are evaluated by exit code alone, ignoring `expect.contains`/`expect.nonzero` unlike `run_row()` for all other phases | fixed in 87a3ad7 |
| 12 | Minor | skills/dev-implementation/resources/scripts/compare_failure_sets.py:24 | unused `typing.Any` import and unused `cand_out` at line 171 survive because `ruff check` resolves its rule set from `~/.config/ruff/ruff.toml` outside the repo | fixed in 87a3ad7 |

Raw output:

````text
# External Review: `execution_and_verification_infrastructure`

## Scope and method

I read the HLD, BDD scenarios, handoff, all five task files and the evidence JSONs, then inspected each changed file's diff against `main` and ran read-only dynamic probes against the new regex/parsing/exception paths in throwaway directories under `/tmp`. The repository working tree is unchanged.

## What holds up

- **`R5b` parameterized route matching (`EVI-EC-03`)** is correct. I probed `route_matches_codebase()` with `{job_id}`, `<user_id>` and `:item_id` templates — all three match their concrete literals, and a genuinely absent route (`/api/other/unmatched`) still returns `False`. The `^...$` anchoring keeps segment counts honest.
- **`MEASURE` phase and replay engine (Task 04)** are genuinely implemented and genuinely tested. `test_replay_and_measure.py` builds real git repos, runs real `pytest` RED/GREEN rows, and asserts on the real evidence JSON — no reconstructed logic, no mock harness standing in for production code. `evaluate_done_gate()`, `row_problems()` and `audit_epic.audit_evidence()` enforce `runs.measure` tree, row contracts and SHA-256 evidence digests as specified.
- **`EVI-AR-01`** is a real subcutaneous test: it runs `check_epic_readiness.py --replay` as a subprocess and asserts `git status --porcelain == ""`, exactly one worktree remaining, and no leaked `helper.py`.
- **`validate_python_quality.py` / schema** match the task's `Decisions Already Made` verbatim.
- **No regressions on the existing corpus.** I ran the new `verify_task_edit_anchors()` across all 26 epics in `.devtool/epic/` (0 findings) and diffed old-vs-new `parse_integration_results()` across every epic HLD (identical). The widened regex and the new blocking `R5` check do not break packaged epics.
- **Gate 5 scope is clean**: working tree empty, and every one of the 22 non-`.devtool` changed files falls inside a declared `Allowed files` entry.
- `mypy --follow-imports=silent` and `ruff check` pass on the new modules, as claimed.

## Audit disclosures

The grader amendments are justified. All five tasks' Verification-table edits trace to `de7cc60` (the branch's first commit) and to the pre-branch Principal Review rounds — i.e. before implementation. The implementation commits touched task files only to flip `status`/`completedAt` frontmatter. The amendments themselves are mechanical: a broken `-k test_file.py::test_name` selector replaced with a real `::Class::test` node ID, and `--follow-imports=silent` moved to the end of the mypy argv.

Of the two commits outside tasks, `2d235f0` (one `sys.path.insert` in a test) is benign. `2795098` is not — see the fourth finding.

## Findings

### The failure-set baseline tooling never sees a real failure

`extract_pytest_failures()` locates the summary with `rfind("=== short test summary info ===")`, then truncates at `summary_text.find("===")`. Real pytest pads that header to terminal width, so after consuming the 31-character marker there are ~25 leftover `=` characters — `find("===")` returns `0` and the summary is truncated to the empty string. Probed against real output at `COLUMNS` 40/80/120/200: `[]` every time.

End to end, on a suite with two genuine failures: `record_failure_baseline.py --cmd "python3 -m pytest test_demo.py"` writes `# 0 failures`. Then adding a brand-new failing test and running `compare_failure_sets.py --baseline baseline.txt -- python3 -m pytest ...` prints `No new test regressions detected.` and exits `0`. Both sides of the comparison are empty, so the tool is vacuously green — it cannot detect any regression. This is the entire deliverable of Observation `#0007` and Task 02.

This shipped because every test feeds a hand-written 3-equals header (`"=== short test summary info ===\n"`, at `test_failure_baseline.py:33`, `:71`, `:164`, `:183`) rather than captured runner output. The scenario anchor for `EVI-HP-02`/`EVI-EC-01`/`EVI-AR-02` is pytest's *terminal summary block*; the synthetic fixture alters that anchor and masks the defect. Ironically, the task's own RED evidence JSON contains a real padded header that the parser would reject.

### Node failure identifiers are durations, not files

`NODE_SPEC_FAIL_RE` expects `✖ <name> (<file>:<line>)`, but real `node --test` spec output — the default when stdout is redirected on Node 25 — is `✖ failing one (0.521042ms)`. The duration is captured as the file path:

```
run1: ['0.483083ms::failing one', '4.085292ms::failing two']
run2: ['0.513ms::failing one',    '4.016708ms::failing two']
```

Baselines are non-deterministic, so every comparison reports all failures as new *and* all baseline entries as fixed. `--rerun-new --runner node` would then pass `0.483083ms` as the test file path. (The TAP fallback degrades to unqualified names, which the HLD does permit.)

### Declared bootstrap failures are swallowed

In `bootstrap_worktree.sh`, the embedded Python wraps `subprocess.run(cmd, check=True)` in `except Exception: sys.exit(1)`. A failing declared bootstrap command is therefore indistinguishable from "no bootstrap configured": `EXECUTED_CUSTOM_BOOTSTRAP` stays `0`, the script falls back to `uv sync`, and prints `Worktree bootstrap complete` with exit 0. Probed with a bootstrap command that exits 1 — confirmed. That is precisely the Observation `#0006` failure mode: the worktree lacks the optional extras while bootstrap reports success, so `mypy`/`pytest` fail later with confusing import errors. (`except Exception as e` also binds an unused `e`, invisible to `ruff` inside the heredoc.)

### Stale-XML prevention was reverted out of task scope

Both the HLD and task_03's `Decisions Already Made` require passing "the exact list of executed reports … never the whole `build/test-results` directory, preventing stale XML pickup". The `skipped_live_commands` branch does this; the `elif reports:` branch — the common path, taken whenever no live spec is skipped — restores `results_paths = ["build/test-results"] if (root / "build/test-results").is_dir() else ...`.

Commit `2795098`, attributed to no task, made this revert to keep two pre-existing tests green (`test_rwe_ec_04` asserts exactly four `execute` calls; `test_rwe_hp_04` asserts `err.count("PASS") == 3`), which the two-pass design would have broken. Under the handoff's guardrail 4 ("No contract repair by the executor") this warranted a stop-and-report rather than a silent contract reduction. The effect is live in this epic's own Gate 4 facts, which ran `--results build/test-results` over a directory holding four stale per-task XMLs from earlier SHAs alongside `pytest.xml`.

### The shipped bootstrap example is rejected by the validator

`skills/dev-designer/SKILL.md:51` documents the new field as a "command list (e.g. `["uv sync", "uv run playwright install"]`)" — a list of strings. The schema and `validate_python_config()` require a list of argv arrays. Probed:

```
{"status": "BLOCKED", "findings": [{"code": "invalid_bootstrap_format", ...}]}
```

A designer following the shipped documentation produces a manifest that blocks the Python quality provider; and `bootstrap_worktree.sh` would call `subprocess.run("uv sync", ...)` without a shell, raising `FileNotFoundError` straight into the swallowing handler above. `check_document.py` reported "0 findings" because it does not check semantics.

### Smaller items

- `replay_task_text.py` implements only `Create <path>:` of the three full-file-write forms the HLD §4 enumerates; `<!-- @@FILE:<rel_path>@@ -->` and `File: <rel_path>` are silent no-ops. Task 04's Decisions only required `Create`, so the task contract is narrower than the HLD.
- HLD §5 documents `--timeout 0` as unbounded for `measure`. `run_command()` calls `process.communicate(timeout=0)`, which raises `TimeoutExpired` in ~2 ms and `SIGKILL`s the process group — the opposite of unbounded. Not advertised in the SKILL.md, so only HLD readers are exposed.
- `tests/test_execution_infra_acceptance.py` covers only `EVI-AR-01`, while the HLD's Tier C1 strategy names five areas for that file. The other Tier C scenarios are satisfied by thin `Test_*_Integration` wrappers that re-call the unit test function — which is how the synthetic-fixture problem above reached Gate 4 unchallenged.
- `EVI-ST-02`'s cache-hit assertion is only `run(args_resume) == 0`, which a re-execution would also satisfy; nothing asserts `"MEASURE resumed (cached PASS)"` or a skipped side effect. The implementation does short-circuit correctly, so this is assertion strength, not a defect. (The invalidation half is properly proven.)
- `replay_task()` evaluates MEASURE rows with a bare exit-code comparison, ignoring `expect.contains` and `expect.nonzero`, unlike `run_row()`/`mismatch()` for every other phase.
- `compare_failure_sets.py:24` imports `typing.Any` unused, and `cand_out` at `:171` is assigned and never read. `ruff check` missed both because it resolves its rule set from `~/.config/ruff/ruff.toml` — outside the repository — so the TIER-B rows are not reproducible across machines. That config gap is pre-existing, not introduced here.
- HLD §1's heading names `scaffold_quality_manifest.py` for secondary platform detection, but no task touches it and its body describes only `detect_project_type.sh`.
- `verify_task_edit_anchors()` reads anchors from the working tree (`root / path`); HLD §4 specifies files "that already exists at `HEAD`".

## Gate 5 items for the developer

Each task carries one, identically worded, and all five are satisfied as of `2d235f0`:

1. `task_01_polyglot_worktree_bootstrap` — clean git working tree with changes restricted to Allowed files.
2. `task_02_failure_baseline_and_comparison` — same.
3. `task_03_live_integration_and_route_matching` — same.
4. `task_04_task_replay_and_measure_phase` — same.
5. `task_05_execution_infra_e2e_acceptance` — same.

`git status --porcelain` is empty and no changed file falls outside the declared Allowed files, so these need only your confirmation, not rework.

## Shared contracts

No `shared-contracts/` directory exists in `ai-agent-tools`, matching the HLD's `## Shared Contract Warnings`. Nothing in the diff touches a symlinked contract path, so the Non-Breaking Schema Guarantee is not engaged.

Verdict: CHANGES REQUIRED
[Critical] skills/dev-implementation/resources/scripts/record_failure_baseline.py:34 — `extract_pytest_failures()` truncates at the header's own `=` padding (`summary_text.find("===")` returns 0), returning `[]` for all real pytest output; baselines record `# 0 failures` and `compare_failure_sets.py` exits 0 on genuine new regressions, voiding the Observation #0007 deliverable
[Important] skills/dev-implementation/resources/scripts/test_failure_baseline.py:33 — every test for EVI-HP-02/EVI-EC-01/EVI-AR-02 feeds a synthetic 3-equals `=== short test summary info ===` header instead of captured runner output, altering the scenario anchor and masking the parser defect
[Important] skills/dev-implementation/resources/scripts/record_failure_baseline.py:21 — `NODE_SPEC_FAIL_RE` captures the duration parenthetical of real `node --test` spec output as the file path, yielding non-deterministic IDs like `0.483083ms::failing one` so node baselines never match across runs
[Important] skills/dev-implementation/resources/scripts/bootstrap_worktree.sh:38 — `except Exception: sys.exit(1)` swallows a failing declared `"bootstrap"` command, silently falling back to `uv sync` and reporting `Worktree bootstrap complete` with exit 0
[Important] skills/dev-implementation/resources/scripts/run_external_review.py:454 — the non-live `elif reports:` path still passes the whole `build/test-results` directory to `check_bdd_traceability.py --results`, contradicting the HLD and task_03 Decisions; reverted by out-of-task commit `2795098` to preserve two pre-existing test assertions
[Important] skills/dev-designer/SKILL.md:51 — the documented `"bootstrap"` example `["uv sync", "uv run playwright install"]` is a list of strings, which `validate_python_config()` rejects with `invalid_bootstrap_format`
[Minor] skills/dev-implementation/resources/scripts/replay_task_text.py:55 — only `Create <path>:` of the HLD's three full-file-write forms is implemented; `<!-- @@FILE:...@@ -->` and `File: <path>` are silent no-ops
[Minor] skills/dev-implementation/resources/scripts/run_task_checks.py:242 — HLD §5 documents `--timeout 0` as unbounded for `measure`, but `communicate(timeout=0)` raises `TimeoutExpired` immediately and SIGKILLs the process group
[Minor] tests/test_execution_infra_acceptance.py:18 — the file covers only `EVI-AR-01` while the HLD's Tier C1 strategy names five areas for it; remaining Tier C scenarios rely on thin wrappers re-calling unit tests
[Minor] skills/dev-implementation/resources/scripts/test_replay_and_measure.py:206 — the `--resume` cache-hit assertion is only `== 0`, which a re-execution also satisfies; nothing asserts the MEASURE subprocess was skipped
[Minor] skills/dev-implementation/resources/scripts/replay_task_text.py:261 — MEASURE rows are evaluated by exit code alone, ignoring `expect.contains`/`expect.nonzero` unlike `run_row()` for all other phases
[Minor] skills/dev-implementation/resources/scripts/compare_failure_sets.py:24 — unused `typing.Any` import and unused `cand_out` at line 171 survive because `ruff check` resolves its rule set from `~/.config/ruff/ruff.toml` outside the repo
````

## Round 2

- **Date**: 2026-11-06T18:56:40Z
- **SHA**: 86703e14b0e9d1e5f4945c5c8c26552d830311d9
- **Base**: main
- **CLI**: claude
- **Model**: opus
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | skills/dev-implementation/resources/scripts/replay_task_text.py:305 | `replay_epic_in_worktree()` pins the scratch worktree to `HEAD`, so `check_epic_readiness.py --replay` validates committed task text instead of the uncommitted text it is documented to check before packaging (dev-designer/SKILL.md:462); an uncommitted epic fails with "Epic directory not found in worktree", and an amended one returns `R8 PASS` while a working-tree GREEN row that exits 3 is never executed | fixed in 21fc644 |
| 2 | Important | skills/dev-implementation/resources/scripts/record_failure_baseline.py:84 | real `node --test` output carries no `▶ <file>` header for top-level tests, so same-named failures in different files collapse to one unqualified identifier (masking regressions), node's `✖ failing tests:` section header is recorded as a failing test, and `--rerun-new --runner node` always exits 2 for lack of a `<file>::` prefix | fixed in 6f066c2 |
| 3 | Important | skills/dev-implementation/resources/scripts/test_failure_baseline.py:212 | the node fixture asserts file-qualified IDs against a `▶ tests/foo.test.mjs` spec format `node --test` never emits for top-level tests, altering the scenario anchor and concealing the collapse above | fixed in 6f066c2 |
| 4 | Minor | skills/dev-implementation/resources/scripts/check_epic_readiness.py:675 | `check_baseline()` returns on `ctx.replay` before the `ctx.baseline` branch, so `--baseline --replay` silently skips all baseline row verification | fixed in af15cd4 |
| 5 | Minor | .devtool/epic/execution_and_verification_infrastructure/2026-11-06-execution-and-verification-infrastructure-design.en.md:142 | HLD §1 names `scaffold_quality_manifest.py` and `static/` `.js` module detection, neither of which any task implements or touches | dismissed: HLD design exploration in overview document; implementation follows finalized task scopes. |
| 6 | Minor | skills/dev-implementation/resources/scripts/replay_task_text.py:196 | `verify_task_edit_anchors()` reads anchors from the working tree, while HLD §4 specifies files that already exist at `HEAD` | fixed in af15cd4 |
| 7 | Minor | skills/dev-implementation/resources/scripts/bootstrap_worktree.sh:47 | `except Exception as e` binds an unused `e` and swallows a malformed `"bootstrap"` array into a silent `uv sync` fallback; only `CalledProcessError` aborts the bootstrap | fixed in 098dfe0 |

Raw output:

````text
# External Review: `execution_and_verification_infrastructure`

## Scope and method

I read the HLD, BDD scenarios, handoff, all five task files, the evidence JSONs and `review_results.md`, then inspected each changed file's diff against `main`. Because round 1 recorded eleven fixes, I re-verified each claimed fix by dynamic probe rather than reading the commit messages — real `pytest` output at several terminal widths, real `node --test` output from Node v25.6.0, real git repositories under `/tmp`. The repository working tree is unchanged and I ran no writing command against it.

## What holds up

Round 1's Critical is genuinely fixed. `extract_pytest_failures()` now returns the right node IDs against real padded output at `COLUMNS` 40 and 200, and the end-to-end chain works: recording a baseline on a two-failure suite, then adding a third failure, yields `Candidate new failures: 1` and exit 1. Parameterized IDs survive intact, including `test_param[hello - world]` with both a space and a ` - ` inside the brackets.

`EVI-ST-01` is real. I built an actual order-dependent state-pollution pair; `--rerun-new` classified the victim `ISOLATED_PASS` and exited 1, and only `--allow-isolated-pass` dropped it to 0, exactly as the HLD specifies.

`EVI-EC-02` is solid. I probed `ensure_output_dirs()` with six command shapes — `--junitxml=`, space-separated `--junitxml`, `--test-reporter-destination=`, two flags joined by `&&`, a shell redirect, and a quoted path containing a space — and every parent directory was created with no tokenizer error.

`EVI-HP-01` works. On a polyglot fixture, `detect_project_type.sh --all` printed `python web`, and `bootstrap_worktree.sh` ran the declared `python-quality.json` bootstrap command *and* the npm phase before exiting 0. The single-platform order (`flutter, ios, android, web, python, rust`) is preserved from `main`, so existing callers are unaffected.

`EVI-EC-03` is correct across all three template syntaxes — `{job_id}`, `<user_id>` and `:item_id` all match their concrete literals, and `/api/other/unmatched` still returns `False`.

Round 1's findings 5, 6, 8 and 10 are all genuinely fixed: `collect_facts` now passes the exact executed report list on the common path (visible in this review's own facts as `--results build/test-results/pytest.xml`); the shipped `"bootstrap"` example is now `[["uv", "sync"], ...]`; `--timeout 0` maps to `communicate(timeout=None)`; and the resume test now asserts `mock_run_cmd.assert_not_called()` with the invalidation half proven by the re-written `{"score": 42}`.

`MEASURE` is wired correctly. `VERIFY_PHASES` excludes it, so `verify` does not re-run expensive rows, and `evaluate_done_gate()` enforces the separate `measure` run's `passed`, `tree` and SHA-256 evidence digests. `EVI-AR-01` is a genuine subcutaneous test: real repo, real subprocess, real worktree, asserting an empty `git status --porcelain` and no leaked `helper.py`.

I re-ran the new blocking `verify_task_edit_anchors()` across all 137 task files in `.devtool/epic/` at HEAD — zero findings, so the broadened `CREATE_RE` (which gained the `File:` and `<!-- @@FILE:…@@ -->` forms after round 1's probe) introduces no false positives on the existing corpus.

## Audit disclosures

The disclosures are justified. I verified that each of the five implementation commits (`04108d5`, `dc96dff`, `ab5abd5`, `21fee3f`, `471f083`) touched exactly 3 lines of its own task file and changed no `| V<n> |` row — those are `status`/`modified`/`completedAt` frontmatter flips. Every Verification-table amendment traces to `de7cc60`, `effa296` or `2c827d0`, all before the corresponding implementation. The amendments are mechanical: a broken `-k file.py::test` selector replaced with a real `::Class::test` node ID, and `--follow-imports=silent` moved to the end of the mypy argv.

Of the seven commits outside tasks, five are round-1 fix commits, which the review loop expects. `2d235f0` is a single `sys.path.insert` in a test. `2795098` was the contract-reducing revert round 1 flagged; `0957b08` has since restored the specified behaviour, so it is resolved.

## Findings

### `--replay` validates committed task text, not the task text being checked

`replay_epic_in_worktree()` creates its scratch worktree at `HEAD` (`replay_task_text.py:305`) and then reads task files from inside that worktree. But `skills/dev-designer/SKILL.md:462` documents `--replay` among the checks that "must exit 0 **before the commit**", and HLD §4 states the purpose is replay "before packaging". At that moment the task text being validated is uncommitted, so replay never sees it.

Both failure modes are reproducible. With a new, uncommitted epic — the normal designer state — the gate dies with a misleading message:

```
R8 FAIL Epic directory not found in worktree: …/replay_worktree/.devtool/epic/demo_epic
Result: 1 FAIL, 0 WARN — FAIL
```

The worse case is a silent false pass. I committed a fully passing epic (`R8 PASS`), then edited only the working-tree copy of `task_1.md` so its GREEN row became `python3 -c "import sys; sys.exit(3)"` — a row that cannot pass — and left it uncommitted. The gate still reports:

```
R8 PASS
Result: 0 FAIL, 0 WARN — PASS
```

The stale `python3 tool.py green` was executed instead. Any amendment to a packaged epic's directives or rows is therefore replayed from the previous commit, and the gate certifies text it never ran. The static anchor half of Observation `#0011` does work (R5 reads the working tree), but the execution-replay half does not deliver its stated pre-packaging purpose, and a verification gate that returns PASS on unvalidated input is worse than one that is absent.

### Node failure identifiers collapse on real `node --test` output

The HLD requires node IDs to be file-qualified "so tests with identical names in different files never collide". Real output cannot satisfy this. I ran two files that each define a test named `failing one`; Node v25.6.0's default reporter emits no `▶ <file>` suite header for top-level tests:

```
✖ failing one (3.853875ms)
✖ failing one (4.039958ms)
```

Round 1's duration fix is present and correct — `DURATION_RE` now rejects `3.853875ms` as a file path — but with no file context `current_file` stays `None` and both lines fall through to `failures.add(test_name)` (`record_failure_baseline.py:84`). Two genuinely distinct failures become one identifier:

```
extracted: ['failing one', 'failing tests:']
```

Three consequences. The collapse is a false negative: if `a.test.mjs::failing one` is in the baseline and `b.test.mjs::failing one` later regresses, both sides contain the single token `failing one`, so the comparison reports no new failures. Second, node's section header `✖ failing tests:` is itself parsed as a failing test and written into every node baseline. Third, `--rerun-new --runner node` cannot run at all, because no identifier carries the required `::`:

```
error: Node failure identifier 'failing one' missing '<file>::' prefix required for isolated rerun
exit=2
```

The TAP reporter is no better — `node --test --test-reporter=tap` yields the same `['failing one']`, because node's `# Subtest:` lines carry no file name for top-level tests. The file name *is* present in the trailing `test at jt/a.test.mjs:4:1` lines, which the parser ignores.

### The node test asserts against a format `node --test` never emits

`test_failure_baseline.py:212` feeds `extract_node_failures()` a hand-written spec stream beginning `▶ tests/foo.test.mjs` and asserts file-qualified results. Node emits that header only for `describe()` suites, never for the top-level `test()` calls the fixture models, so the test passes on a format that does not occur and hides the collapse above. This is the same altered-scenario-anchor pattern round 1 raised for the pytest fixtures; it was corrected on the pytest side (`test_real_pytest_summary_padding_extraction` now uses realistic padding) but left in place for node, which is why the node defect survived into round 2.

### Smaller items

`--replay` silently supersedes `--baseline`: `check_baseline()` returns immediately on `ctx.replay`, so `--baseline --replay` runs no baseline rows and reports only replay results.

HLD §1's heading still names `scaffold_quality_manifest.py` for secondary platform detection, but no task touches it and the file is absent from the diff; the section body describes only `detect_project_type.sh`. The same section specifies recognizing `web` via `static/` `.js` modules, which `is_web()` does not implement.

`verify_task_edit_anchors()` reads anchors from the working tree (`root / path`), while HLD §4 specifies files "that already exists at `HEAD`".

In the `bootstrap_worktree.sh` heredoc, `except Exception as e` still binds an unused `e` and still swallows a malformed `"bootstrap"` array into a silent `uv sync` fallback; only `CalledProcessError` aborts. A list-of-strings manifest (the shape round 1's documentation example produced) raises `FileNotFoundError` into that handler. `validate_python_quality.py` would flag such a manifest separately, so this is a robustness gap rather than a live break.

## Gate 5 items for the developer

All five tasks carry one identically worded item, and all five are satisfied at `86703e1`: `git status --porcelain` is empty and every changed file falls inside a declared `Allowed files` entry.

1. `task_01_polyglot_worktree_bootstrap` — clean git working tree with changes restricted to Allowed files.
2. `task_02_failure_baseline_and_comparison` — same.
3. `task_03_live_integration_and_route_matching` — same.
4. `task_04_task_replay_and_measure_phase` — same.
5. `task_05_execution_infra_e2e_acceptance` — same.

These need your confirmation, not rework.

## Shared contracts

No `shared-contracts/` directory exists in `ai-agent-tools`, matching the HLD's `## Shared Contract Warnings`. Nothing in the diff touches a symlinked contract path, so the Non-Breaking Schema Guarantee is not engaged.

Verdict: CHANGES REQUIRED
[Important] skills/dev-implementation/resources/scripts/replay_task_text.py:305 — `replay_epic_in_worktree()` pins the scratch worktree to `HEAD`, so `check_epic_readiness.py --replay` validates committed task text instead of the uncommitted text it is documented to check before packaging (dev-designer/SKILL.md:462); an uncommitted epic fails with "Epic directory not found in worktree", and an amended one returns `R8 PASS` while a working-tree GREEN row that exits 3 is never executed
[Important] skills/dev-implementation/resources/scripts/record_failure_baseline.py:84 — real `node --test` output carries no `▶ <file>` header for top-level tests, so same-named failures in different files collapse to one unqualified identifier (masking regressions), node's `✖ failing tests:` section header is recorded as a failing test, and `--rerun-new --runner node` always exits 2 for lack of a `<file>::` prefix
[Important] skills/dev-implementation/resources/scripts/test_failure_baseline.py:212 — the node fixture asserts file-qualified IDs against a `▶ tests/foo.test.mjs` spec format `node --test` never emits for top-level tests, altering the scenario anchor and concealing the collapse above
[Minor] skills/dev-implementation/resources/scripts/check_epic_readiness.py:675 — `check_baseline()` returns on `ctx.replay` before the `ctx.baseline` branch, so `--baseline --replay` silently skips all baseline row verification
[Minor] .devtool/epic/execution_and_verification_infrastructure/2026-11-06-execution-and-verification-infrastructure-design.en.md:142 — HLD §1 names `scaffold_quality_manifest.py` and `static/` `.js` module detection, neither of which any task implements or touches
[Minor] skills/dev-implementation/resources/scripts/replay_task_text.py:196 — `verify_task_edit_anchors()` reads anchors from the working tree, while HLD §4 specifies files that already exist at `HEAD`
[Minor] skills/dev-implementation/resources/scripts/bootstrap_worktree.sh:47 — `except Exception as e` binds an unused `e` and swallows a malformed `"bootstrap"` array into a silent `uv sync` fallback; only `CalledProcessError` aborts the bootstrap
````
