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
