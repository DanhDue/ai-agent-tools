---
id: "task_1_traceability_script_reads_coverage_faithfully"
status: "done"
priority: "high"
assignee: null
epic: "lifecycle-followups"
dueDate: null
created: "2026-10-15T15:57:47Z"
modified: "2026-10-15T16:16:44Z"
completedAt: "2026-10-15T16:16:44Z"
labels: ["tooling", "bdd-traceability"]
order: "a1"
---

# Task 1: Traceability script reads coverage faithfully

Epic: [lifecycle-followups](../epic/lifecycle_followups/lifecycle_followups.en.md)

## Requirement Analysis

Spec items B1, B3 and B4 in `check_bdd_traceability.py`:

- **B1** — read `Covers:` identifiers by their shape, so prose and trailing punctuation no longer
  produce "unknown identifier" failures.
- **B3** — a scenario document, its Vietnamese sibling or a task file that is not valid UTF-8 is a
  usage error: exit 2, `error: <path> is not valid UTF-8`.
- **B4** — list integration test files with `git -C <root> ls-files --cached --others --exclude-standard -z`,
  so ignored, vendored and generated files never count; outside git, fall back to the current walk.

### Exact changes

These were applied to a copy of `main` before this task was written: the tests fail first
(`FAILED (failures=2, errors=2)`), and all 32 tests pass after the script changes.

**Tests first** — `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`:

1. `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py` (T1) — replace the current text:

```python
import contextlib
import io
import sys
```

with:

```python
import contextlib
import io
import subprocess
import sys
```

2. `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py` (T1) — replace the current text:

```python
    def test_document_without_scenarios_fails(self) -> None:
```

with:

```python
    def test_lf_fr_02_non_utf8_scenario_document_exits_2(self) -> None:
        scenarios = self.root / "epic/bdd_scenarios.en.md"
        scenarios.parent.mkdir(parents=True, exist_ok=True)
        scenarios.write_bytes(b"\xff\xfe# BDD Scenarios\n")
        code, _, err = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 2)
        self.assertIn("is not valid UTF-8", err)

    def test_document_without_scenarios_fails(self) -> None:
```

3. `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py` (T1) — replace the current text:

```python
    def test_missing_task_file_exits_2(self) -> None:
```

with:

```python
    def test_lf_hp_01_prose_and_trailing_punctuation_in_covers_are_ignored(self) -> None:
        task = self.write("epic/task_1_all.md", "Covers: PY-HP-01 (happy path), PY-EC-02.\n")
        code, out, _ = self.plan(self.scenarios(*TWO), task)
        self.assertEqual(code, 0, out)
        self.assertIn("Result: 2/2 covered — PASS", out)

    def test_lf_fr_01_non_utf8_task_file_exits_2(self) -> None:
        task = self.root / "epic/task_1_all.md"
        task.parent.mkdir(parents=True, exist_ok=True)
        task.write_bytes(b"\xff\xfeCovers: PY-HP-01\n")
        code, _, err = self.plan(self.scenarios(*TWO), task)
        self.assertEqual(code, 2)
        self.assertIn("is not valid UTF-8", err)

    def test_missing_task_file_exits_2(self) -> None:
```

4. `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py` (T1) — replace the current text:

```python
    def test_unknown_identifier_in_ids_fails(self) -> None:
```

with:

```python
    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def test_lf_ec_01_gitignored_files_do_not_cover(self) -> None:
        self.git("init", "-q")
        self.write(".gitignore", "playwright-report/\n")
        self.write("tests/integration/playwright-report/index.html", "<li>[PY-HP-01] [PY-EC-02]</li>\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 1)
        self.assertIn("Result: 0/2 covered — FAIL", out)

    def test_lf_hp_02_tracked_and_untracked_unignored_files_cover(self) -> None:
        self.git("init", "-q")
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-01] first', () => {});\n")
        self.git("add", "tests/integration/flow_test.ts")
        self.write("tests/integration/new_test.ts", "test('[PY-EC-02] second', () => {});\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 0, out)

    def test_lf_ec_02_roots_outside_git_fall_back_to_the_directory_walk(self) -> None:
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-01] [PY-EC-02] all', () => {});\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 0, out)

    def test_unknown_identifier_in_ids_fails(self) -> None:
```

**Then the script** — `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`:

1. `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` (S1) — replace the current text:

```python
import argparse
import re
import sys
```

with:

```python
import argparse
import re
import subprocess
import sys
```

2. `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` (S1) — replace the current text:

```python
COVERS_LINE = re.compile(r"^\s*(?:[-*]\s+)?\**Covers\**\s*:\**\s*(.*)$")
```

with:

```python
COVERS_LINE = re.compile(r"^\s*(?:[-*]\s+)?\**Covers\**\s*:\**\s*(.*)$")
ID_TOKEN = re.compile(r"(?<![A-Za-z0-9-])" + ID_SHAPE.pattern + r"(?![A-Za-z0-9])")
```

3. `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` (S1) — replace the current text:

```python
class UsageError(Exception):
    """Missing input: exit 2."""
```

with:

```python
class UsageError(Exception):
    """Missing input: exit 2."""


def read_text(path: Path) -> str:
    """Read a scenario document or task file; anything but UTF-8 is a usage error."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise UsageError(f"{path} is not valid UTF-8") from None
```

4. `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` (S1) — replace the current text:

```python
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        fence = FENCE.match(line)
```

with:

```python
    for number, line in enumerate(read_text(path).splitlines(), start=1):
        fence = FENCE.match(line)
```

5. `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` (S1) — replace the current text:

```python
    for line in path.read_text(encoding="utf-8").splitlines():
        match = COVERS_LINE.match(line)
        if match:
            tokens = (token.strip("`[]*") for token in re.split(r"[,\s]+", match.group(1)))
            found.extend(token for token in tokens if token)
```

with:

```python
    for line in read_text(path).splitlines():
        match = COVERS_LINE.match(line)
        if match:
            found.extend(ID_TOKEN.findall(match.group(1)))
```

6. `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` (S1) — replace the current text:

```python
def integration_files(roots: list[Path]) -> tuple[list[Path], list[str]]:
```

with:

```python
def listed_files(root: Path) -> list[Path] | None:
    """Files git lists under root — tracked, plus untracked but not ignored — or None outside git."""
    try:
        listed = subprocess.run(["git", "-C", str(root), "ls-files", "--cached", "--others",
                                 "--exclude-standard", "-z"], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return [root / name for name in listed.stdout.decode("utf-8", "surrogateescape").split("\0") if name]


def integration_files(roots: list[Path]) -> tuple[list[Path], list[str]]:
```

7. `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` (S1) — replace the current text:

```python
    files = [path for root in existing for path in sorted(root.rglob("*"))
             if path.is_file() and path.suffix.lower() != ".md"]
```

with:

```python
    files: list[Path] = []
    for root in existing:
        listed = listed_files(root)
        candidates = sorted(listed) if listed is not None else sorted(root.rglob("*"))
        files.extend(path for path in candidates if path.is_file() and path.suffix.lower() != ".md")
```

## Relevant Files & Context Pointers

- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`
- `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`
- `.devtool/epic/lifecycle_followups/2026-10-15-lifecycle-followups-design.en.md` — §4 Script Changes

## Design Rationale

- One helper, `read_text`, owns the UTF-8 rule for scenario and task files; integration test files
  keep skipping undecodable content, because a binary fixture under a test root is normal.
- `listed_files` asks git per root, with `-C`, so the result does not depend on the working directory,
  and returns `None` outside git so the fallback stays explicit.
- Applicable skills: `test-driven-development` (tests first), `verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target symbols**: `covers_of`, `scenario_ids`, `integration_files`; new `read_text`, `listed_files`,
  `ID_TOKEN`.
- **Downstream callers**: the CLI only; dev-designer, dev-implementation and dev-lifecycle invoke it by
  path.
- **Behaviour change**: files matched by `.gitignore` under a root stop counting as coverage.
- **Coverage threshold**: every new branch covered by the six `test_lf_*` tests.

## BDD Scenarios & Acceptance Criteria

### BDD SCENARIOS

Covers: LF-HP-01, LF-HP-02, LF-EC-01, LF-EC-02, LF-FR-01, LF-FR-02

```gherkin
Feature: lifecycle follow-ups

  Scenario: [LF-HP-01] [Tier C - Integration] A Covers line with prose and trailing punctuation is accepted
    Given a scenario document with PY-HP-01 and PY-EC-02
    And a task file whose line reads "Covers: PY-HP-01 (happy path), PY-EC-02."
    When the plan mode runs
    Then both identifiers are assigned to the task
    And no identifier is reported as unknown

  Scenario: [LF-HP-02] [Tier C - Integration] Tracked and new, unignored test files count as coverage
    Given an integration test root inside a git repository
    And one tracked test naming PY-HP-01 and one untracked, unignored test naming PY-EC-02
    When the tests mode runs
    Then both identifiers are covered

  Scenario: [LF-EC-01] [Tier C - Integration] A gitignored generated report does not count as coverage
    Given an integration test root inside a git repository that ignores "playwright-report/"
    And an ignored report file under that root naming PY-HP-01 and PY-EC-02
    When the tests mode runs
    Then neither identifier is covered and the run exits 1

  Scenario: [LF-EC-02] [Tier C - Integration] A root outside any git repository falls back to the directory walk
    Given an integration test root that is not inside a git repository
    And a test file under it naming PY-HP-01 and PY-EC-02
    When the tests mode runs
    Then both identifiers are covered

  Scenario: [LF-FR-01] [Tier C - Integration] A task file that is not valid UTF-8 is a usage error
    Given a task file whose bytes are not valid UTF-8
    When the plan mode runs
    Then the run exits 2 with "is not valid UTF-8" on stderr

  Scenario: [LF-FR-02] [Tier C - Integration] A scenario document that is not valid UTF-8 is a usage error
    Given a scenario document whose bytes are not valid UTF-8
    When the plan mode runs
    Then the run exits 2 with "is not valid UTF-8" on stderr
```

## Test & Verification Checklist

- [ ] **RED**: apply the test changes only, run
  `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`,
  and see `FAILED (failures=2, errors=2)`.
- [ ] **GREEN**: apply the script changes; the same command prints `Ran 32 tests` and `OK`, also under
  `python3 -W error`.
- [ ] **REFACTOR**: none expected; keep the file's existing style.
- [ ] **Tier C**: `python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py tests --scenarios .devtool/epic/lifecycle_followups/bdd_scenarios.en.md --roots skills/dev-implementation/resources/scripts/ --ids LF-HP-01 LF-HP-02 LF-EC-01 LF-EC-02 LF-FR-01 LF-FR-02`
  exits 0, and `scripts/verify.sh` prints `PASS — safe to publish`.

## Definition of Done

All six identifiers above are covered by passing `test_lf_*` tests, the per-task traceability check
exits 0, `scripts/verify.sh` passes, and the task lands as one commit
`[LIFECYCLE_FOLLOWUPS] Traceability script reads coverage faithfully` with no trailer.

## Dependencies & Blockers

- None.

## References & Rollback

- Spec: `.devtool/epic/lifecycle_followups/2026-10-15-lifecycle-followups-design.en.md`
- Rollback: revert this task's commit; the script returns to the directory walk and the old `Covers:` parsing.
