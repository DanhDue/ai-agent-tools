# Cross-Model Review: contract_and_authoring_ergonomics

## Round 1

- **Date**: 2026-11-06T09:00:45Z
- **SHA**: 1c46d27e17f65a1fe30366d48319b3ee2e8ca9a8
- **Base**: main
- **CLI**: claude
- **Model**: sonnet
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | skills/dev-implementation/resources/scripts/sync_task_status.py:714 | render_epic_tasks() is not atomic across multiple tasks: a later task's failure (unknown Covers ID or missing embed file) leaves earlier tasks' canonical files and `.devtool/features/` mirrors already mutated on disk, contradicting Task 02's frozen "Decisions Already Made" clause and the HLD's stated error-handling guarantee. The TCAE-FR-03 test only covers a single-task epic, so this gap is untested. | fixed in 459540b |

Raw output:

```text
Verdict: CHANGES REQUIRED
[Important] skills/dev-implementation/resources/scripts/sync_task_status.py:714 — render_epic_tasks() is not atomic across multiple tasks: a later task's failure (unknown Covers ID or missing embed file) leaves earlier tasks' canonical files and `.devtool/features/` mirrors already mutated on disk, contradicting Task 02's frozen "Decisions Already Made" clause and the HLD's stated error-handling guarantee. The TCAE-FR-03 test only covers a single-task epic, so this gap is untested.

Everything else checked out: `bin/d3nexus`, `kit_env()` injection in `run_task_checks.py`/`check_epic_readiness.py`, `parse_evidence_files`/`check_evidence`/`evaluate_done_gate` condition 8, the grep/rg/sed/awk pattern exclusion in `command_paths()`, bare `VAR=val` detection, non-portable path rejection, `program_of()` d3nexus resolution, R2/R3 shift-left checks, and the grammar reference doc all match the HLD and task specs, and dynamic probing confirmed correct behavior for those paths. All grader amendments in the audit are legitimate corrections (narrowing scenario coverage claims to match reality), and the one commit outside tasks is a pure ruff-formatting diff.
```

## Round 2

- **Date**: 2026-11-06T09:56:03Z
- **SHA**: 47f6b4fb69632be18104dd82b7663ba2e32d8336
- **Base**: main
- **CLI**: claude
- **Model**: opus
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | .devtool/features/done/task_01_evidence_files_contract.md:17 | Mirror still uses `](../epic/contract_and_authoring_ergonomics/…)` while located in `features/done/`, so both board links are broken and `check_task_contract.py --design` and `check_epic_readiness` R2 both FAIL on the candidate SHA; `task_02`'s mirror is likewise not reproducible from `sync-status render` (prefix injected inside inline code spans at lines 29, 119, 120, 122). Re-render and re-commit both mirrors. | fixed in 73d5828 |
| 2 | Important | skills/dev-implementation/resources/scripts/sync_task_status.py:225 | `board_location()` applies a document-wide `str.replace("](../epic/", "](../../epic/")` (and its inverse at :228) with no code-span or fence awareness; probed on this epic's own `task_02`, a `done` transition rewrote four documentation lines and broke R2 parity for a mirror the engine itself produced. | fixed in 73d5828 |
| 3 | Important | skills/dev-implementation/resources/scripts/sync_task_status.py:511 | `SCENARIO_LINE`/`ID_SHAPE`/`FENCE` are a third, narrower copy of the Gherkin extractor regexes instead of reusing `check_bdd_traceability`'s as the HLD prescribed; probed, `render` aborts with "Covered scenario(s) missing from bdd_scenarios.en.md" for `Example:`, `Scenario Template:`, Vietnamese-keyword and indented-fence scenarios that `check_bdd_traceability.py plan` reports as 1/1 covered. | fixed in 73d5828 |
| 4 | Important | skills/dev-implementation/resources/scripts/sync_task_status.py:702 | `epic_path.glob("task_*.md")` ignores handoff Observation #0021's explicit directive; probed with an epic directory named `task_replay`, the HLD `task_replay.en.md` was rendered in place as a task and mirrored to `.devtool/features/task_replay.en.md`. | fixed in 73d5828 |
| 5 | Important | skills/dev-implementation/resources/scripts/test_sync_task_status.py:259 | `test_TCAE_ST_01_orphan_mirrors_and_location_aware_links` never runs an archive transition, so the scenario's third clause and the `dest_file.exists()` canonical-preservation branch at `sync_task_status.py:371` — the fix the Principal Review required regression tests for — are untested; the four existing archive tests all take the `else` branch. | fixed in 73d5828 |
| 6 | Minor | skills/dev-implementation/resources/scripts/sync_task_status.py:675 | `base_target.endswith(".md")` rewrites any markdown target into `../epic/<epic_dir>/`; probed, `[guide](docs/guide.md)` becomes `../epic/sample_epic/docs/guide.md` in the mirror, and the R2 normalizer strips the prefix back so the broken link is invisible to the gate. | fixed in 73d5828 |
| 7 | Minor | tests/test_task_contract_ergonomics_e2e.py:1 | Task 05's frozen Decisions and the HLD's Tier C1 strategy require the suite to drive `bin/d3nexus sync-status render`, `check-contract --design` and `run-checks verify`; the suite calls the modules and scripts directly and never invokes `bin/d3nexus`. | fixed in 73d5828 |
| 8 | Minor | skills/dev-implementation/resources/scripts/test_run_task_checks.py:674 | `test_TCAE_AR_01_concurrent_env_isolation` runs a single invocation, not the "two concurrent invocations in separate temporary git worktrees" the scenario specifies. | dismissed: safe-isolation |
| 9 | Minor | scripts/resume_context.py:945 | `kit_root = ws_root / "ai-agent-tools"` guesses the clone's name and location instead of deriving it from `Path(__file__).resolve().parents[1]`, and the `if "D3NEXUS_KIT" not in content` guard means a wrong exported value is never corrected. | fixed in 73d5828 |
| 10 | Minor | .devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md:60 | TCAE-ST-01 names an `archive-tasks` subcommand that does not exist; `sync_task_status.py` exposes `archive-epic` and `archive-done`. | dismissed: spec-verbiage |

Raw output:

````text
I reviewed the artefacts, inspected the diff file by file, and ran read-only dynamic probes against the render engine, the contract checkers, the `d3nexus` dispatcher and the archive path. Nothing in the repository or git state was modified (`git status --porcelain` is empty before and after; all probe writes went to `/tmp`).

## What holds up

- **Evidence files contract** (Task 01) is sound. `parse_evidence_files` / `EVIDENCE_FILE_RE` / `check_evidence` reject traversal, out-of-directory paths and `task_*.json` runner-record collisions; `evaluate_done_gate` condition 8 enforces existence and non-emptiness. The reserved-record collision the Principal Review raised is genuinely closed.
- **`bin/d3nexus`** dispatches all five subcommands (probed: all exit 0; unknown subcommand exits 2; mode `0755`). `program_of()` resolves `d3nexus <subcmd>` and `python3 bin/d3nexus <subcmd>` back to the dispatched script, preserving implicit checker protection — the second Principal Review finding is closed.
- **`kit_env()`** returns a copy; `os.environ` is provably unmutated, and `KIT_ROOT = parents[4]` resolves correctly from `skills/dev-implementation/resources/scripts/`.
- **Grammar diagnostics** behave as documented. Probed `command_paths()`: `grep -E 'foo/bar/baz' README.md` → no paths; `-e`/`--regexp` handled; `-f patterns/list.txt` correctly *kept* as a path; `sed`/`awk` pattern arguments excluded; bare `FOO=bar` flagged while `env A=1` is not; `&&`/`;`/`|` subcommand splitting is correct.
- **Fence promotion** is exact: a file whose longest inner run is 4 backticks produced a 5-backtick outer fence, and re-rendering was byte-identical.
- **Multi-task atomicity** (review round 1, fixed in 459540b) is real: a later task with an unknown `Covers:` ID aborts with exit 1 and leaves earlier canonical files and existing mirrors untouched.
- **`archive_epic_tasks` canonical preservation** works — probed with a rich canonical body and a divergent mirror: only `status`/`modified`/`completedAt` were lifted, the canonical body and links survived.
- **E2E suite** imports and invokes real production symbols against real temp git repos, with no reconstructed logic and no synthetic anchors. It passes in 0.47s with no repository mutation.
- **Shared contracts**: no `shared-contracts/` directory exists; the HLD's `## Shared Contract Impact: None` is accurate. No Rule 7 concern.

## Problems found

### The branch ships board mirrors its own new R2 gate rejects

Running the epic's own new checker on the candidate SHA:

```
$ check_task_contract.py --design --hld <hld> --tasks task_0*.md
task_01_evidence_files_contract:Mirror: features mirror content differs from epic task (R2)
```

and `check_epic_readiness.check_task_mirrors` agrees:

```
Finding(check='R2', severity='FAIL', message='task_01_evidence_files_contract.md: line 17: ... != Epic: [...](../epic/contract_and_authoring_ergonomics/...)')
```

`.devtool/features/done/task_01_evidence_files_contract.md` still carries single-`../` links (lines 17 and 114) while sitting in `features/done/`, so both links are broken on the board. Tasks 03–05's mirrors are byte-identical to what `render` produces; task_01's and task_02's are not — task_02's mirror additionally has the epic-path prefix injected *inside inline code spans* (lines 29, 119, 120, 122), e.g. `` `](../../epic/contract_and_authoring_ergonomics/../epic/<epic_dir>/<sibling>.md)` `` where the source says `` `](../epic/<epic_dir>/<sibling>.md)` ``. That one round-trips through the normalizer, so R2 stays green while the prose is wrong.

### `board_location()` corrupts code spans and then breaks parity

`sync_task_status.py:225` and `:228` apply a document-wide `str.replace("](../epic/", "](../../epic/")` with no awareness of inline code or fenced blocks. Probed by rendering this epic's own `task_02` to a mirror and calling `board_location(..., "done")`: four documentation lines were rewritten, including the self-referential one, which became `` rewrites `](../../epic/` $\rightarrow$ `](../../epic/` ``. The normalized mirror then no longer equals the epic source, so R2 fails for a mirror the engine itself just produced. Any task that documents these link prefixes literally — which Task 02 does — is corrupted by its own `done` transition.

### `render` falsely aborts on Gherkin keywords the rest of the kit accepts

`sync_task_status.py:511-513` declares a *third* copy of the Gherkin extractor's regexes instead of reusing `check_bdd_traceability`'s, which the HLD prescribed ("reusing the Gherkin extraction logic from `check_epic_readiness.py`"). They diverge:

| | `check_bdd_traceability` | `sync_task_status` |
|---|---|---|
| `SCENARIO_LINE` | `Scenario`, `Scenario Outline`, `Scenario Template`, `Example`, Vietnamese keywords | `Scenario`, `Scenario Outline` only |
| `FENCE` | `^\s*(` + backticks + `)\s*(\S*)` — indentation tolerated | `^(` + backticks + `)(.*)` — column 0 only |
| `ID_SHAPE` | must end in `-<digits>` | any uppercase hyphenated run |

Probed end to end with a scenario written as `Example: [AB-HP-01] ...`:

```
$ check_bdd_traceability.py plan ...   → Result: 1/1 covered — PASS   (exit 0)
$ sync_task_status.py render se        → error: Covered scenario(s) missing
                                         from bdd_scenarios.en.md: AB-HP-01   (exit 1)
```

An indented gherkin fence behaves the same way (`sts` extracts nothing, readiness extracts the scenario). So the single-source engine refuses to render epics that pass the kit's own traceability and R3 gates.

### `render_epic_tasks` ignores the handoff's Observation #0021

`handoff.md` Open Notes records it explicitly: *"Logged during Stage 2 when an epic directory starting with `task_` collided with `task_*.md` globs; Task 02 (`render_epic_tasks`) should match task files with `re.fullmatch(r"task_[0-9]+_.*\.md", path.name)` (or exclude `*.en.md`/`*.vi.md`)."* The implementation at `sync_task_status.py:702` is a plain `epic_path.glob("task_*.md")`. Probed with an epic directory named `task_replay`:

```
Rendered 2 tasks for epic 'task_replay'
.devtool/features/: task_01_a.md  task_replay.en.md
```

The HLD itself was rewritten in place as if it were a task, and a bogus `.devtool/features/task_replay.en.md` mirror was created.

### TCAE-ST-01's archive clause is never exercised

The scenario asserts three transitions, ending with *"`archive-tasks` preserves canonical `.devtool/epic/sample_epic/` links"*. `test_TCAE_ST_01_orphan_mirrors_and_location_aware_links` runs `render` and a reopen, and never calls archive. The `dest_file.exists()` canonical-preservation branch at `sync_task_status.py:371-378` — the exact fix the Principal Review demanded, with "regression tests for each" — has no test: the four existing archive tests all hit the `else` branch (no canonical file present). The behaviour is correct (I probed it), but the regression that would silently overwrite the single source of truth is unguarded. The scenario also names `archive-tasks`, which is not a subcommand (`archive-epic` / `archive-done` are).

### Smaller items

- `rewrite_mirror_links` (`sync_task_status.py:675`) rewrites any target merely because it ends in `.md`. Probed: `[grammar guide](docs/guide.md)` became `[grammar guide](../epic/sample_epic/docs/guide.md)` in the mirror — a broken link that R2 cannot see, because the normalizer strips the prefix back.
- Task 05's frozen Decisions and the HLD's Tier C1 strategy require the e2e suite to drive `bin/d3nexus sync-status render`, `bin/d3nexus check-contract --design` and `bin/d3nexus run-checks verify`. `tests/test_task_contract_ergonomics_e2e.py` calls the modules and scripts directly and never invokes `bin/d3nexus`; only `d3nexus check-doc` is exercised, from `test_run_task_checks.py`.
- TCAE-AR-01 specifies "two concurrent invocations ... in separate temporary git worktrees"; the test runs one invocation and asserts `os.environ` is unchanged. The isolation claim follows from not mutating `os.environ`, but concurrency is not exercised.
- `scripts/resume_context.py:945` sets `kit_root = ws_root / "ai-agent-tools"` rather than `Path(__file__).resolve().parents[1]`, so the `D3NEXUS_KIT` export written into `~/.zshrc` is a guess at the clone's name and location — the same class of layout assumption Observation #0016 set out to remove. The `if "D3NEXUS_KIT" not in content` guard also means a wrong value is never corrected.

## Audit disclosures

- **Grader amendments** — all five tasks were amended. The `--follow-imports=silent` reorderings (12071d2, 8a3b4a0) are cosmetic and functionally identical. The `Covers:` moves are legitimate corrections traceable to Principal Review round 2 (TCAE-EC-01 from Task 01 to Task 02; TCAE-FR-02 from Task 03 to Task 04, exactly as the reviewer proposed), and all 14 identifiers remain covered. Task 05's RED→GREEN restructure carries a `RED: n/a` justification, which is defensible for an acceptance-only suite.
- **Allowed-files widening mid-epic** — `2c2ea19` and `573a4fb` expanded Task 05's Allowed files *after* Task 04 shipped and before Task 05 was implemented, adding `check_task_contract.py`, `test_check_task_contract.py` and `scripts/test_verifiable_handoff.py`. The underlying cause is real: Task 03's non-portable-path ban broke `scripts/test_verifiable_handoff.py`, whose generated rows used `ROOT / "scripts/run_unittest_junit.py"`. But each task's "Stop and Report If" names a change to its own Allowed files as a stop condition, so the governance path was a stop-and-report, not a self-authorised amendment.
- **Commits outside tasks** — `1c46d27` is a pure ruff-format diff on a Task 05 allowed file. `459540b` fixes `render_epic_tasks` (a Task 02 allowed file) in response to review round 1. Both are justified, but note that Task 02's recorded Gate 5 SCOPE evidence predates `459540b`.
- **Protected paths** — none changed, consistent with the HLD's declared set.

## Gate 5 items, restated

All five tasks carry the identical condition: **"Clean git working tree with changes restricted to Allowed files."** At `47f6b4f` the working tree is clean. Two caveats for your sign-off: (1) Task 02's and Task 05's Gate 5 evidence was recorded before `459540b` and `1c46d27` touched their allowed files, so neither task's SCOPE row covers its final content; (2) Task 05's "restricted to Allowed files" is satisfied only because its Allowed files were widened in `2c2ea19`/`573a4fb` after the task was packaged.

Verdict: CHANGES REQUIRED
[Important] .devtool/features/done/task_01_evidence_files_contract.md:17 — Mirror still uses `](../epic/contract_and_authoring_ergonomics/…)` while located in `features/done/`, so both board links are broken and `check_task_contract.py --design` and `check_epic_readiness` R2 both FAIL on the candidate SHA; `task_02`'s mirror is likewise not reproducible from `sync-status render` (prefix injected inside inline code spans at lines 29, 119, 120, 122). Re-render and re-commit both mirrors.
[Important] skills/dev-implementation/resources/scripts/sync_task_status.py:225 — `board_location()` applies a document-wide `str.replace("](../epic/", "](../../epic/")` (and its inverse at :228) with no code-span or fence awareness; probed on this epic's own `task_02`, a `done` transition rewrote four documentation lines and broke R2 parity for a mirror the engine itself produced.
[Important] skills/dev-implementation/resources/scripts/sync_task_status.py:511 — `SCENARIO_LINE`/`ID_SHAPE`/`FENCE` are a third, narrower copy of the Gherkin extractor regexes instead of reusing `check_bdd_traceability`'s as the HLD prescribed; probed, `render` aborts with "Covered scenario(s) missing from bdd_scenarios.en.md" for `Example:`, `Scenario Template:`, Vietnamese-keyword and indented-fence scenarios that `check_bdd_traceability.py plan` reports as 1/1 covered.
[Important] skills/dev-implementation/resources/scripts/sync_task_status.py:702 — `epic_path.glob("task_*.md")` ignores handoff Observation #0021's explicit directive; probed with an epic directory named `task_replay`, the HLD `task_replay.en.md` was rendered in place as a task and mirrored to `.devtool/features/task_replay.en.md`.
[Important] skills/dev-implementation/resources/scripts/test_sync_task_status.py:259 — `test_TCAE_ST_01_orphan_mirrors_and_location_aware_links` never runs an archive transition, so the scenario's third clause and the `dest_file.exists()` canonical-preservation branch at `sync_task_status.py:371` — the fix the Principal Review required regression tests for — are untested; the four existing archive tests all take the `else` branch.
[Minor] skills/dev-implementation/resources/scripts/sync_task_status.py:675 — `base_target.endswith(".md")` rewrites any markdown target into `../epic/<epic_dir>/`; probed, `[guide](docs/guide.md)` becomes `../epic/sample_epic/docs/guide.md` in the mirror, and the R2 normalizer strips the prefix back so the broken link is invisible to the gate.
[Minor] tests/test_task_contract_ergonomics_e2e.py:1 — Task 05's frozen Decisions and the HLD's Tier C1 strategy require the suite to drive `bin/d3nexus sync-status render`, `check-contract --design` and `run-checks verify`; the suite calls the modules and scripts directly and never invokes `bin/d3nexus`.
[Minor] skills/dev-implementation/resources/scripts/test_run_task_checks.py:674 — `test_TCAE_AR_01_concurrent_env_isolation` runs a single invocation, not the "two concurrent invocations in separate temporary git worktrees" the scenario specifies.
[Minor] scripts/resume_context.py:945 — `kit_root = ws_root / "ai-agent-tools"` guesses the clone's name and location instead of deriving it from `Path(__file__).resolve().parents[1]`, and the `if "D3NEXUS_KIT" not in content` guard means a wrong exported value is never corrected.
[Minor] .devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md:60 — TCAE-ST-01 names an `archive-tasks` subcommand that does not exist; `sync_task_status.py` exposes `archive-epic` and `archive-done`.
````
