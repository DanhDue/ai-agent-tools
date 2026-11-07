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
