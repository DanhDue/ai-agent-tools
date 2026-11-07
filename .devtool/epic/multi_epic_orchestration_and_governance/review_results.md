# Cross-Model Review: multi_epic_orchestration_and_governance

## Round 1

- **Date**: 2026-11-07T00:13:52Z
- **SHA**: 7b9573e0e81372ed2f8bf1f634c7f80aeae8eedd
- **Base**: main
- **CLI**: claude
- **Model**: sonnet
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | scripts/verify.sh:258 | `python3 -m unittest test_inter_epic_dependencies.py 2>/dev/null \|\| python3 -m pytest ... \|\| FAILED=1` (and the identical lines 259–260 for `test_concurrent_epic_backlog.py` and `test_package_and_revise_epic.py`) relies on `unittest` exiting non-zero when it discovers zero `TestCase` classes in these pytest-fixture-style files; that only holds on Python ≥3.12. On a clean Python 3.11.14 venv with `pytest` installed (the floor this repo targets per the HLD's stdlib-only, "Python 3.11+" non-goal), `python3 -m unittest test_inter_epic_dependencies.py` prints "Ran 0 tests ... OK" and exits 0, so the `\|\|` pytest fallback never fires and the suite silently never runs, yet `bash scripts/verify.sh` still reports success. This is exactly the "no standing regression coverage" gap Principal Review finding #7 flagged and task_05's V6 row/DoD bullet was written to close — on the stated minimum Python version it reopens that gap without any visible failure. Fix: invoke `python3 -m pytest <file> -q \|\| FAILED=1` directly for these three files instead of probing `unittest` first, or convert them to `unittest.TestCase` subclasses to match the rest of the directory's convention. | fixed in f58aea7 |
| 2 | Minor | skills/dev-implementation/resources/scripts/task_contract.py:resolve_prerequisite_epic_dirs | `check_task_contract.py` main() discards the `(ordered_dirs, errors)` second element from `resolve_prerequisite_epic_dirs()` when building `created`/`prereq_files` for Gate 2's design-time check, so a cyclic or missing `Depends on epic:` declaration is silently absorbed into a partial prerequisite set at that checkpoint; the cycle is still caught later by `check_epic_readiness.py`'s R7, so this is not a path to an undetected cycle, just an earlier, quieter miss. | fixed in 9254384 |

Raw output:

```text
Verdict: CHANGES REQUIRED
[Important] scripts/verify.sh:258 — `python3 -m unittest test_inter_epic_dependencies.py 2>/dev/null || python3 -m pytest ... || FAILED=1` (and the identical lines 259–260 for `test_concurrent_epic_backlog.py` and `test_package_and_revise_epic.py`) relies on `unittest` exiting non-zero when it discovers zero `TestCase` classes in these pytest-fixture-style files; that only holds on Python ≥3.12. On a clean Python 3.11.14 venv with `pytest` installed (the floor this repo targets per the HLD's stdlib-only, "Python 3.11+" non-goal), `python3 -m unittest test_inter_epic_dependencies.py` prints "Ran 0 tests ... OK" and exits 0, so the `||` pytest fallback never fires and the suite silently never runs, yet `bash scripts/verify.sh` still reports success. This is exactly the "no standing regression coverage" gap Principal Review finding #7 flagged and task_05's V6 row/DoD bullet was written to close — on the stated minimum Python version it reopens that gap without any visible failure. Fix: invoke `python3 -m pytest <file> -q || FAILED=1` directly for these three files instead of probing `unittest` first, or convert them to `unittest.TestCase` subclasses to match the rest of the directory's convention.
[Minor] skills/dev-implementation/resources/scripts/task_contract.py:resolve_prerequisite_epic_dirs — `check_task_contract.py` main() discards the `(ordered_dirs, errors)` second element from `resolve_prerequisite_epic_dirs()` when building `created`/`prereq_files` for Gate 2's design-time check, so a cyclic or missing `Depends on epic:` declaration is silently absorbed into a partial prerequisite set at that checkpoint; the cycle is still caught later by `check_epic_readiness.py`'s R7, so this is not a path to an undetected cycle, just an earlier, quieter miss.
```

## Round 2

- **Date**: 2026-11-07T06:05:07Z
- **SHA**: 4271010d18eebcd563ed332c9593ea5f2d995083
- **Base**: main
- **CLI**: claude
- **Model**: sonnet
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | skills/dev-implementation/resources/scripts/package_epic.py:266 | Calling `package_epic.py <epic_dir>` without `--revise` when `handoff.md` already exists silently overwrites it via `render_initial_handoff`, discarding custom `Open Notes` and the entire `## Revisions` history (reproduced in a scratch repo); no test exercises this reachable operator-error path, and it directly undermines the preservation guarantee `MEO-ST-02` and task_03's Definition of Done require of `--revise`. | fixed in 3263146 |
| 2 | Minor | .devtool/epic/multi_epic_orchestration_and_governance/2026-11-06-multi-epic-orchestration-and-governance-design.en.md:Architecture and Component Design (section 3) | The design spec's CLI signature still lists `[--status "<hld_status>"]`, but task_03's Decisions and the shipped `package_epic.py` drop that flag entirely; the design spec was never updated to match the task-level contract that superseded it. | fixed in 74289b5 |

Raw output:

```text
Confirmed — matches Principal Review fix #13. This completes my review.

## Review

I read all required artefacts, the full HLD/design spec, `principal_review.md`, `handoff.md`, BDD scenarios, all 5 task files, and the key implementation diffs (`task_contract.py`, `check_epic_readiness.py`, `sync_task_status.py`, `package_epic.py`, `resume_context.py`, `handoff-template.md`, `dev-implementation/SKILL.md`, `scripts/verify.sh`), plus the two "commits outside tasks."

**Principal Review closure.** All 15 round-1 findings (8 Important, 7 Minor) are genuinely fixed in `9a9205f`, and I independently verified the code for each: `re.MULTILINE` is present on `SPEC_ERRATA_ITEM_RE`; `en_errata`/`vi_errata` are initialized before the `try` and the function returns immediately after a `ContractError`, eliminating the prior `UnboundLocalError`; `replay_with_prerequisites`/`--replay-prereqs` is wired into `main()` and imports `replay_epic_in_worktree` with the documented fallback message; `.gitignore` tracks `GATE_LEDGER.md` while `.devtool/state/` stays ignored; `handoff-template.md` carries the `## Revisions` section and the corrected line 71; `verify.sh` step 11 now runs all three new suites via direct `pytest` (further corrected post-review in `f58aea7` after the original `unittest || pytest` fallback was fragile); `dev-implementation/SKILL.md` Phase 0 now hard-gates on `check-prereqs`; prerequisite file matching uses `path_matches` glob comparison, not exact set membership; `promote_epic_tasks` no longer clobbers an existing `Packaged (...)` status; `record_gate_approval` resolves the SHA with `cwd=root`; `collect_harvest_data` carries the `gate_approvals` key. The two "commits outside tasks" (`f58aea7`, `9254384`) are small, justified post-Gate-4 fixups, not scope creep.

**New defect found by dynamic probing.** `package_epic.py`'s non-`--revise` branch has no guard against being invoked a second time on an epic that is already packaged. I reproduced this in a scratch git repo: after an initial `package_epic.py demo_epic` followed by a developer editing `handoff.md` (adding a custom `Open Notes` bullet and, separately, a prior `--revise` entry under `## Revisions`), a second call to `package_epic.py demo_epic` *without* `--revise` silently overwrites the entire file via `render_initial_handoff`, discarding both the custom note and the revision history. This is precisely the data this epic (`#0015`) exists to protect — `MEO-ST-02` and the task_03 DoD explicitly require `--revise` to preserve `Open Notes` — but nothing stops the no-`--revise` path from running again and wiping it. `test_package_and_revise_epic.py` and the Tier-C acceptance test only exercise the correct call sequence (`package` then `--revise`); neither tests re-invoking without `--revise` after `handoff.md` already exists, so the gap has zero coverage. It is reachable by a plausible operator mistake (forgetting `--revise` on a later re-packaging), not just a contrived input.

**Other checks.** The design-spec's `--status` CLI flag (section 3) was dropped from task_03's actual `Decisions Already Made` and never implemented — task_03 is the authoritative contract and is internally consistent, so this is just stale documentation in the earlier spec, not a functional defect. No `shared-contracts/` directory exists in this repo, matching the HLD's explicit statement. BDD-to-test traceability is 13/13 covered with real symbol/exit-code assertions, not reconstructed logic. Gate 5 "clean working tree restricted to Allowed files" holds for all five tasks per the audit.

Verdict: CHANGES REQUIRED
[Important] skills/dev-implementation/resources/scripts/package_epic.py:266 — Calling `package_epic.py <epic_dir>` without `--revise` when `handoff.md` already exists silently overwrites it via `render_initial_handoff`, discarding custom `Open Notes` and the entire `## Revisions` history (reproduced in a scratch repo); no test exercises this reachable operator-error path, and it directly undermines the preservation guarantee `MEO-ST-02` and task_03's Definition of Done require of `--revise`.
[Minor] .devtool/epic/multi_epic_orchestration_and_governance/2026-11-06-multi-epic-orchestration-and-governance-design.en.md:Architecture and Component Design (section 3) — The design spec's CLI signature still lists `[--status "<hld_status>"]`, but task_03's Decisions and the shipped `package_epic.py` drop that flag entirely; the design spec was never updated to match the task-level contract that superseded it.
```

## Round 3

- **Date**: 2026-11-07T06:46:04Z
- **SHA**: fbbfcb3bcba3bb70a066f2011fb90f9dc323a84c
- **Base**: main
- **CLI**: claude
- **Model**: opus
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | scripts/resume_context.py:273 | `render_gate_ledger_markdown` rebuilds the tracked permanent `.devtool/GATE_LEDGER.md` solely from the gitignored ephemeral `.devtool/state/gate_ledger.jsonl`, so on any clone where `state/` is absent the first `--gate` recording truncates the committed ledger to that single row (reproduced via the CLI: Gates 1–2 deleted, `git diff --numstat` `1 2`, `--check-gate 1` flips exit 0 → exit 1), defeating the permanence guarantee observation #0020 and task_04 exist to provide; `scan_gate_ledger` already implements the Markdown fallback for exactly this case but the writer never merges existing rows, and `test_MEO_HP_04_fallback_to_markdown_and_harvest` only reads in that state so the path has zero coverage. | fixed in 745b647 |
| 2 | Minor | scripts/resume_context.py:294 | the Markdown ledger does not escape field contents and the fallback reader skips rows containing `---`: `--approved 'HLD \| 5 tasks \| SE-01 approved'` round-trips as `approved="HLD"`, `deviations="5 tasks"`, `by="SE-01 approved"`, and `--approved 'Execution order --- wave 1-3'` is dropped entirely on read. | fixed in 745b647 |
| 3 | Minor | .devtool/epic/multi_epic_orchestration_and_governance/task_03_package_revise_and_spec_errata.md:Decisions Already Made | the shipped `package_epic.py` CLI has `--force` and refuses to overwrite an existing `handoff.md` (exit 1), but task_03's frozen Decisions and the HLD Goals line still describe only `<epic_dir> [--revise] [--reason] [--base-branch] [--open-note]`; only the design spec was realigned in `74289b5`. | fixed in 6896e97 |
| 4 | Minor | skills/dev-implementation/resources/scripts/check_epic_readiness.py:27 | the `replay_task_text` import became a module-level `try/except ImportError` that sets `verify_task_edit_anchors = None`, and `check_grounding` then skips the R5 edit-anchor verification entirely when it is `None`, so an import failure would silently remove a readiness check while the report still prints PASS (the `--replay` call site at line 754 is left unguarded and would instead raise on `None`); latent only, since the module imports cleanly today. | fixed in 713ca6f |
| 5 | Minor | skills/dev-lifecycle/SKILL.md:45 | the commit also compresses prose unrelated to multi-epic orchestration (the Markdown Formatting bullets, Gate 4 condition names "Normalized Invocation Contract"/"Deterministic Aggregation" → "Contract"/"Aggregation", and the review-CLI prohibition bullet); `check_document.py` enforces no length or density rule, so these edits are outside the epic's scope. | dismissed: Required by scripts/test_lifecycle_document_contract.py 2500-word budget |

Raw output:

```text
## Review

I read all required artefacts (design spec en/vi, HLD en, `handoff.md`, `bdd_scenarios.en.md`, all 5 task files, `principal_review.md`, `review_results.md`, `manual_smoke_checklist.md`, evidence JSONs) and inspected every source file in the diff. I independently re-ran the quality gates and ran dynamic probes against the parsing, exception and ledger-persistence paths.

**Verification re-run.** `ruff` clean across all changed modules and the three new suites; `mypy --follow-imports=silent` → "no issues found in 6 source files"; `check_document.py` on the five updated `SKILL.md` files → "0 findings". These match the task tables' V3/V4/V5 rows and the provided 461-passed / 13-of-13-traceability facts.

**Audit disclosures are justified.** Every grader amendment that touched a Verification table, Definition of Done or Allowed-files list came from `9a9205f` ("Revise epic after Principal Review round 1"), which is already merged into `main` — i.e. applied at Gate 2, before any task executed. I diffed each of the five implementation commits (`5fe89e8`, `6686f01`, `261c58d`, `f5327e1`, `5fd7fc7`) against the task files: they change only frontmatter `status`/`modified`/`completedAt`. No executor repaired its own contract. `5461359` is a pre-execution alignment of the `--follow-imports=silent` position across all five mypy rows. The protected-path entries (`scripts/verify.sh` in `5fd7fc7`, `f58aea7`) are covered by task_05's Allowed files and are not in the HLD's declared protected set. The three commits outside tasks each trace to a recorded review finding.

**Prior rounds genuinely closed.** `verify.sh` step 11 now invokes `pytest` directly for the three new suites; `check_task_contract.main()` surfaces `prereq_errors` via `check.problem`; `package_epic` refuses to overwrite an existing `handoff.md` without `--revise`/`--force` and has a dedicated regression test; the design spec's `--status` flag was replaced with `--force` symmetrically in en and vi (I checked both Error Handling sections — all five bullets present in each).

**Dynamic probing.** `check_metadata`'s `en_errata`/`vi_errata` are bound before the `try`, and both the en-raises and vi-raises paths return a clean finding with no `UnboundLocalError`. The `new <symbol>` extractor respects word boundaries (`renew_token`, `news feed` → no symbols) and strips `()` correctly. `resolve_prerequisite_epic_dirs` terminates on a self-dependency with a deterministic cycle error rather than recursing. No `shared-contracts/` exists in this repo, matching the HLD's "None". Tests invoke production CLIs and symbols directly and reuse the real `build_ready_epic` fixture — no reconstructed logic, no synthetic anchor substitution.

**One defect found by probing the persistence path.** `render_gate_ledger_markdown` rebuilds the *tracked permanent* `.devtool/GATE_LEDGER.md` purely from the *gitignored ephemeral* `.devtool/state/gate_ledger.jsonl`. `scan_gate_ledger` deliberately falls back to the Markdown table "on fresh clones or worktrees", so the authors recognised the JSONL can be absent while the Markdown exists — but the writer does not. I reproduced it end-to-end with the real CLI: a clone with Gates 1–2 committed in `GATE_LEDGER.md` and no `state/` directory loses both rows the moment `--gate 4` is recorded (`git diff --numstat` → `1 2`), and `--check-gate 1` flips from exit 0 to exit 1. Observation `#0020` exists specifically to make these approvals durable, so this reopens the gap it closed. (Git worktrees are safe — `resolve_primary_repo_root` centralises on `--git-common-dir` — but a second clone is not.) `test_MEO_HP_04_fallback_to_markdown_and_harvest` writes the Markdown-only state and then only *reads* it, which is why the gap has no coverage.

Two smaller Markdown round-trip issues compound it: a `|` inside `--approved` shifts every subsequent column on read (`approved` became `"HLD"`, `deviations` `"5 tasks"`, `by` `"SE-01 approved"`), and any row containing `---` is silently dropped by the fallback's skip filter.

**Gate 5 items for you to confirm**, restated — all five tasks carry the identical item:

- `task_01_inter_epic_dependencies` — clean git working tree with changes restricted to Allowed files.
- `task_02_conflict_aware_epic_promotion` — same.
- `task_03_package_revise_and_spec_errata` — same.
- `task_04_gate_approval_ledger` — same.
- `task_05_multi_epic_governance_e2e_acceptance` — same.

Verdict: CHANGES REQUIRED
[Important] scripts/resume_context.py:273 — `render_gate_ledger_markdown` rebuilds the tracked permanent `.devtool/GATE_LEDGER.md` solely from the gitignored ephemeral `.devtool/state/gate_ledger.jsonl`, so on any clone where `state/` is absent the first `--gate` recording truncates the committed ledger to that single row (reproduced via the CLI: Gates 1–2 deleted, `git diff --numstat` `1 2`, `--check-gate 1` flips exit 0 → exit 1), defeating the permanence guarantee observation #0020 and task_04 exist to provide; `scan_gate_ledger` already implements the Markdown fallback for exactly this case but the writer never merges existing rows, and `test_MEO_HP_04_fallback_to_markdown_and_harvest` only reads in that state so the path has zero coverage.
[Minor] scripts/resume_context.py:294 — the Markdown ledger does not escape field contents and the fallback reader skips rows containing `---`: `--approved 'HLD | 5 tasks | SE-01 approved'` round-trips as `approved="HLD"`, `deviations="5 tasks"`, `by="SE-01 approved"`, and `--approved 'Execution order --- wave 1-3'` is dropped entirely on read.
[Minor] .devtool/epic/multi_epic_orchestration_and_governance/task_03_package_revise_and_spec_errata.md:Decisions Already Made — the shipped `package_epic.py` CLI has `--force` and refuses to overwrite an existing `handoff.md` (exit 1), but task_03's frozen Decisions and the HLD Goals line still describe only `<epic_dir> [--revise] [--reason] [--base-branch] [--open-note]`; only the design spec was realigned in `74289b5`.
[Minor] skills/dev-implementation/resources/scripts/check_epic_readiness.py:27 — the `replay_task_text` import became a module-level `try/except ImportError` that sets `verify_task_edit_anchors = None`, and `check_grounding` then skips the R5 edit-anchor verification entirely when it is `None`, so an import failure would silently remove a readiness check while the report still prints PASS (the `--replay` call site at line 754 is left unguarded and would instead raise on `None`); latent only, since the module imports cleanly today.
[Minor] skills/dev-lifecycle/SKILL.md:45 — the commit also compresses prose unrelated to multi-epic orchestration (the Markdown Formatting bullets, Gate 4 condition names "Normalized Invocation Contract"/"Deterministic Aggregation" → "Contract"/"Aggregation", and the review-CLI prohibition bullet); `check_document.py` enforces no length or density rule, so these edits are outside the epic's scope.
```
