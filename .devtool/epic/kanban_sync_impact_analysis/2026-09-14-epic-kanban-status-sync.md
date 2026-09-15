# Cross-Workspace Kanban Status Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use d3nexus:subagent-driven-development (recommended) or d3nexus:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `epic-implementation` write every task status change to all four copies of that task — `.devtool/features/` and `.devtool/epic/<epic_dir>/`, in both the main checkout and the epic worktree — with `modified` and `completedAt` maintained, and leave the main checkout clean before the epic branch merges.

**Architecture:** One new stdlib-only Python script, `sync_task_status.py`, owns every multi-copy write. It discovers checkouts via `git worktree list --porcelain` — which makes it symmetric, so it behaves identically whether invoked from the main checkout or the worktree. `SKILL.md` stops describing hand edits and calls the script instead. Two surrounding fixes make the phases consistent: base-ref resolution in Phase 1 (replacing a hardcoded `develop`) and a main-checkout restore in Phase 4.

**Tech Stack:** Python 3.10+ (stdlib only — `argparse`, `re`, `subprocess`, `pathlib`, `datetime`; **no PyYAML**), `unittest`, bash, git worktrees, Markdown.

**Spec:** [docs/superpowers/specs/2026-09-14-epic-kanban-status-sync-design.md](../specs/2026-09-14-epic-kanban-status-sync-design.md)

## Global Constraints

- **Stdlib only.** No third-party imports. Frontmatter is parsed with the hand-rolled regex idiom already used in `compute_execution_order.py`, never PyYAML.
- **Python 3.10+ syntax.** `list[str]`, `dict[str, dict]`, `str | None` — matching the existing sibling script.
- **Surgical rewrites.** Only matched lines change. Every other frontmatter key and the entire document body survive byte-for-byte. Never re-serialize YAML.
- **Status enum is exactly** `backlog | todo | in-progress | review | done`. No `blocked`, no `in-review`.
- **Timestamp format** is `datetime.now(timezone.utc).isoformat(timespec="seconds")` with `+00:00` replaced by `Z`, e.g. `2026-09-14T10:23:45Z`.
- **Commit format:** `[EPIC_IMPLEMENTATION] <title>` plus a bullet body. Per `rules/CRITICAL_RULES.md`, **never** append `Co-Authored-By`, `Generated with`, or any other trailer.
- **`SKILL.md` frontmatter is exactly `name` + `description`.** Do not add keys; `scripts/verify.sh` check 2 fails the release otherwise.
- **Links and anchors in `skills/**/*.md` are verified.** `scripts/verify.sh` checks 3 and 4 resolve every relative link and every in-page `#anchor`. New prose must satisfy both.
- **New scripts are executable** (`chmod +x`) — every existing script in that directory is `-rwxr-xr-x`.
- **Branch:** `feature/epic-kanban-status-sync`.

## File Structure

| File | Responsibility |
|------|----------------|
| `skills/epic-implementation/resources/scripts/sync_task_status.py` | **Create.** All multi-copy status writes. Pure helpers + thin subprocess boundary + argparse CLI. |
| `skills/epic-implementation/resources/scripts/test_sync_task_status.py` | **Create.** `unittest` suite, sibling-import style, no git or network required. |
| `skills/epic-implementation/SKILL.md` | **Modify.** Phase 1 base-ref resolution, Phase 2 script calls, Phase 4 close-out, Quick Reference, Common Mistakes, Red Flags. |
| `skills/epic-lifecycle/SKILL.md` | **Modify.** Two cells only — Gate 3 name and handoff artefact, plus the gate-failure row. |

**Testability boundary that drives the decomposition:** every function that touches git is split into a *pure parser* plus a *thin subprocess caller*. `parse_worktree_list(output)` is tested directly with captured text; only `checkout_roots()` shells out, and no test calls it. This is why the suite needs no git fixtures.

---

### Task 1: Frontmatter field writer

The foundation: set a key inside the leading frontmatter block without disturbing anything else.

**Files:**
- Create: `skills/epic-implementation/resources/scripts/sync_task_status.py`
- Test: `skills/epic-implementation/resources/scripts/test_sync_task_status.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `TASK_STATUSES: tuple[str, ...]`, `now_iso() -> str`, `parse_frontmatter(text: str) -> dict`, `set_frontmatter_field(text: str, key: str, value: str) -> str`.

- [ ] **Step 1: Write the failing test**

Create `skills/epic-implementation/resources/scripts/test_sync_task_status.py`:

```python
#!/usr/bin/env python3
"""Tests for sync_task_status.py.

Run: python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py -v
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sync_task_status import now_iso, parse_frontmatter, set_frontmatter_field

TASK_TEXT = '''---
id: "task_1_setup"
status: "todo"
priority: "high"
assignee: null
epic: "logging-refactor"
dueDate: null
created: "2026-09-01T09:00:00Z"
modified: "2026-09-01T09:00:00Z"
completedAt: null
labels: ["architecture"]
order: "a1"
---

# Task 1: Setup

## Dependencies & Blockers
- None.
'''


class SetFrontmatterFieldTests(unittest.TestCase):
    def test_replaces_existing_key(self):
        out = set_frontmatter_field(TASK_TEXT, "status", "in-progress")
        self.assertIn('status: "in-progress"', out)
        self.assertNotIn('status: "todo"', out)

    def test_preserves_every_other_key(self):
        out = set_frontmatter_field(TASK_TEXT, "status", "done")
        for line in ('id: "task_1_setup"', 'priority: "high"', 'assignee: null',
                     'epic: "logging-refactor"', 'labels: ["architecture"]', 'order: "a1"'):
            self.assertIn(line, out)

    def test_preserves_body_byte_for_byte(self):
        out = set_frontmatter_field(TASK_TEXT, "status", "review")
        body = out.split("---\n", 2)[2]
        self.assertEqual(body, TASK_TEXT.split("---\n", 2)[2])

    def test_inserts_missing_key_after_status(self):
        text = '---\nid: "t"\nstatus: "todo"\n---\n\n# T\n'
        out = set_frontmatter_field(text, "completedAt", "2026-09-14T10:00:00Z")
        self.assertIn('status: "todo"\ncompletedAt: "2026-09-14T10:00:00Z"', out)

    def test_file_without_frontmatter_is_untouched(self):
        text = "# Just a heading\n\nSome prose.\n"
        self.assertEqual(set_frontmatter_field(text, "status", "done"), text)

    def test_does_not_touch_body_occurrences_of_the_key(self):
        text = '---\nstatus: "todo"\n---\n\nThe status: "todo" shown above is the source of truth.\n'
        out = set_frontmatter_field(text, "status", "done")
        self.assertIn('The status: "todo" shown above', out)


class NowIsoTests(unittest.TestCase):
    def test_utc_zulu_seconds_precision(self):
        stamp = now_iso()
        self.assertTrue(stamp.endswith("Z"), stamp)
        self.assertNotIn("+00:00", stamp)
        self.assertEqual(len(stamp), 20, stamp)  # 2026-09-14T10:23:45Z


class ParseFrontmatterTests(unittest.TestCase):
    def test_reads_quoted_values(self):
        self.assertEqual(parse_frontmatter(TASK_TEXT)["epic"], "logging-refactor")

    def test_missing_frontmatter_is_empty(self):
        self.assertEqual(parse_frontmatter("# Nope\n"), {})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sync_task_status'`

- [ ] **Step 3: Write the minimal implementation**

Create `skills/epic-implementation/resources/scripts/sync_task_status.py`:

```python
#!/usr/bin/env python3
"""Mirror one epic task's Kanban status across every checkout of this repo.

`epic-implementation` runs an epic inside an isolated worktree, but the same
task files are also checked out in the main workspace -- and `epic-designer`
writes each task twice, into `.devtool/features/` and into
`.devtool/epic/<epic_dir>/`. Writing a status to only one of those four copies
leaves every other Kanban board stale for the whole epic.

This script writes them all:

    sync_task_status.py task <task_id> <status>
    sync_task_status.py epic <epic_dir> <status>

`task` mode rewrites `status`, `modified`, and -- on `done` -- `completedAt` in
the frontmatter of every copy of that task, in every checkout `git worktree
list` reports. `epic` mode rewrites the Meta Data `Status` line of the Epic
Overview's `.en.md` and `.vi.md` together, so the pair can never diverge.

Only matched lines change; every other key and the whole document body survive
byte-for-byte. Frontmatter is parsed with the same hand-rolled regex idiom as
compute_execution_order.py -- deliberately no PyYAML, so this stays stdlib-only.
"""
import re
from datetime import datetime, timezone

TASK_STATUSES = ("backlog", "todo", "in-progress", "review", "done")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def now_iso() -> str:
    """UTC, seconds precision, Zulu suffix -- e.g. 2026-09-14T10:23:45Z."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_frontmatter(text: str) -> dict:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"')
    return fields


def set_frontmatter_field(text: str, key: str, value: str) -> str:
    """Set `key: "value"` inside the leading frontmatter block only.

    A key that is absent is inserted directly after `status:`, so task files
    written before this script existed (no `modified`, no `completedAt`) keep
    working instead of silently losing the field. Body text is never scanned.
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        return text
    block = match.group(1)
    new_line = f'{key}: "{value}"'
    key_re = re.compile(rf"^{re.escape(key)}\s*:.*$", re.M)
    if key_re.search(block):
        new_block = key_re.sub(lambda _m: new_line, block, count=1)
    else:
        status_re = re.compile(r"^status\s*:.*$", re.M)
        if status_re.search(block):
            new_block = status_re.sub(lambda m: m.group(0) + "\n" + new_line, block, count=1)
        else:
            new_block = block + "\n" + new_line
    return text[:match.start(1)] + new_block + text[match.end(1):]
```

Note the `lambda _m: new_line` in the substitution: a plain string replacement would treat a
backslash in a timestamp or label as an escape sequence. The lambda makes the replacement literal.

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py -v`
Expected: PASS — 9 tests

- [ ] **Step 5: Commit**

```bash
chmod +x skills/epic-implementation/resources/scripts/sync_task_status.py \
         skills/epic-implementation/resources/scripts/test_sync_task_status.py
git add skills/epic-implementation/resources/scripts/sync_task_status.py \
        skills/epic-implementation/resources/scripts/test_sync_task_status.py
git commit -m "[EPIC_IMPLEMENTATION] Add frontmatter field writer for status sync" -m "- Add now_iso, parse_frontmatter and set_frontmatter_field
- Insert absent keys after status so pre-existing task files keep working
- Cover replacement, key insertion and body preservation with unit tests"
```

---

### Task 2: Checkout discovery and task target resolution

Find every checkout, and every copy of a task within one — with the guard that stops a same-named task under a different epic from being clobbered.

**Files:**
- Modify: `skills/epic-implementation/resources/scripts/sync_task_status.py`
- Test: `skills/epic-implementation/resources/scripts/test_sync_task_status.py`

**Interfaces:**
- Consumes: `parse_frontmatter` (Task 1).
- Produces: `parse_worktree_list(output: str) -> list[Path]`, `checkout_roots() -> list[Path]`, `task_targets(root: Path, task_id: str) -> list[Path]`, `epic_of(path: Path) -> str | None`, `expected_epic(roots: list[Path], task_id: str) -> str | None`.

- [ ] **Step 1: Write the failing test**

Append to `test_sync_task_status.py`, above the `if __name__` block, and extend the import line at the top to:

```python
from sync_task_status import (
    epic_of, expected_epic, now_iso, parse_frontmatter, parse_worktree_list,
    set_frontmatter_field, task_targets,
)
```

```python
WORKTREE_LIST = '''worktree /Users/dev/project
HEAD 1111111111111111111111111111111111111111
branch refs/heads/develop

worktree /Users/dev/project/.worktrees/logging_refactor
HEAD 2222222222222222222222222222222222222222
branch refs/heads/epic/logging-refactor
'''


def make_task(path: Path, *, epic: str, status: str = "todo") -> None:
    """Write a minimal but realistic task file at `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'---\nid: "{path.stem}"\nstatus: "{status}"\npriority: "high"\n'
        f'epic: "{epic}"\nmodified: "2026-09-01T09:00:00Z"\ncompletedAt: null\n---\n\n'
        f"# {path.stem}\n"
    )


def make_checkout(root: Path, *, epic_dir: str, epic: str, task_id: str, status: str = "todo") -> None:
    """Create both copies of one task inside one checkout root."""
    make_task(root / ".devtool" / "features" / f"{task_id}.md", epic=epic, status=status)
    make_task(root / ".devtool" / "epic" / epic_dir / f"{task_id}.md", epic=epic, status=status)


class ParseWorktreeListTests(unittest.TestCase):
    def test_extracts_roots_in_git_order(self):
        roots = parse_worktree_list(WORKTREE_LIST)
        self.assertEqual(
            roots,
            [Path("/Users/dev/project"), Path("/Users/dev/project/.worktrees/logging_refactor")],
        )

    def test_main_worktree_is_first(self):
        self.assertEqual(parse_worktree_list(WORKTREE_LIST)[0], Path("/Users/dev/project"))

    def test_single_checkout(self):
        self.assertEqual(parse_worktree_list("worktree /solo\nHEAD abc\n"), [Path("/solo")])

    def test_empty_output(self):
        self.assertEqual(parse_worktree_list(""), [])

    def test_path_containing_spaces(self):
        self.assertEqual(parse_worktree_list("worktree /Users/dev/My Project\n"),
                         [Path("/Users/dev/My Project")])


class TaskTargetsTests(unittest.TestCase):
    def test_finds_both_copies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_checkout(root, epic_dir="logging_refactor", epic="logging-refactor", task_id="task_1_setup")
            found = task_targets(root, "task_1_setup")
            self.assertEqual(len(found), 2)
            self.assertIn(root / ".devtool" / "features" / "task_1_setup.md", found)
            self.assertIn(root / ".devtool" / "epic" / "logging_refactor" / "task_1_setup.md", found)

    def test_missing_task_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(task_targets(Path(tmp), "task_9_absent"), [])

    def test_matches_same_task_id_under_two_epics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_checkout(root, epic_dir="logging_refactor", epic="logging-refactor", task_id="task_1_setup")
            make_task(root / ".devtool" / "epic" / "payments" / "task_1_setup.md", epic="payments")
            self.assertEqual(len(task_targets(root, "task_1_setup")), 3)


class ExpectedEpicTests(unittest.TestCase):
    def test_reads_epic_from_features_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_checkout(root, epic_dir="logging_refactor", epic="logging-refactor", task_id="task_1_setup")
            self.assertEqual(expected_epic([root], "task_1_setup"), "logging-refactor")

    def test_returns_none_when_no_features_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(expected_epic([Path(tmp)], "task_1_setup"))

    def test_epic_of_reads_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task_1_setup.md"
            make_task(path, epic="payments")
            self.assertEqual(epic_of(path), "payments")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py -v`
Expected: FAIL — `ImportError: cannot import name 'parse_worktree_list'`

- [ ] **Step 3: Write the minimal implementation**

Add to the imports at the top of `sync_task_status.py`:

```python
import subprocess
from pathlib import Path
```

Append these functions:

```python
def parse_worktree_list(output: str) -> list[Path]:
    """Extract checkout roots from `git worktree list --porcelain` output.

    Git always reports the main worktree first, and callers rely on that
    ordering -- Phase 4's main-checkout restore uses roots[0]. Paths may
    contain spaces, so take everything after the first token.
    """
    return [Path(line[len("worktree "):]) for line in output.splitlines()
            if line.startswith("worktree ")]


def checkout_roots() -> list[Path]:
    """Every checkout of this repo, main worktree first.

    The only subprocess boundary in this module -- everything else is pure and
    directly testable, which is why the test suite needs no git fixtures.
    """
    result = subprocess.run(["git", "worktree", "list", "--porcelain"],
                            capture_output=True, text=True, check=True)
    return parse_worktree_list(result.stdout)


def task_targets(root: Path, task_id: str) -> list[Path]:
    """Every copy of one task inside one checkout: features + each epic dir."""
    candidates = [root / ".devtool" / "features" / f"{task_id}.md"]
    candidates.extend(sorted((root / ".devtool" / "epic").glob(f"*/{task_id}.md")))
    return [path for path in candidates if path.is_file()]


def epic_of(path: Path) -> str | None:
    return parse_frontmatter(path.read_text()).get("epic")


def expected_epic(roots: list[Path], task_id: str) -> str | None:
    """The epic this task_id belongs to, per the authoritative features copy.

    Task ids are `task_<number>_<name>`, so a name like `task_1_setup` can
    plausibly exist under two different epics -- and `task_targets`' `*/` glob
    would match both. Callers use this value to refuse any copy whose own
    `epic:` differs. Checked main-worktree-first; mirrors cannot disagree.
    """
    for root in roots:
        features = root / ".devtool" / "features" / f"{task_id}.md"
        if features.is_file():
            return epic_of(features)
    return None
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py -v`
Expected: PASS — 20 tests

- [ ] **Step 5: Commit**

```bash
git add skills/epic-implementation/resources/scripts/sync_task_status.py \
        skills/epic-implementation/resources/scripts/test_sync_task_status.py
git commit -m "[EPIC_IMPLEMENTATION] Add checkout discovery and task target resolution" -m "- Parse git worktree list porcelain output into checkout roots, main first
- Resolve both copies of a task within one checkout
- Derive the owning epic from the features copy to guard against task id collisions"
```

---

### Task 3: Task-mode sync and board tally

Fan one status change out across every copy in every checkout, then report the board.

**Files:**
- Modify: `skills/epic-implementation/resources/scripts/sync_task_status.py`
- Test: `skills/epic-implementation/resources/scripts/test_sync_task_status.py`

**Interfaces:**
- Consumes: `set_frontmatter_field`, `now_iso`, `parse_frontmatter` (Task 1); `task_targets`, `expected_epic`, `epic_of` (Task 2).
- Produces: `sync_task(roots: list[Path], task_id: str, status: str) -> tuple[list[Path], list[str]]` and `board_tally(roots: list[Path], epic: str) -> dict[str, int]`. Both return values are `(written_paths, skip_notes)` and a status→count mapping respectively; the CLI in Task 5 prints them.

- [ ] **Step 1: Write the failing test**

Extend the import line to add `board_tally, sync_task`, then append:

```python
class SyncTaskTests(unittest.TestCase):
    def _two_checkouts(self, tmp: str) -> list[Path]:
        main, wt = Path(tmp) / "main", Path(tmp) / "wt"
        for root in (main, wt):
            make_checkout(root, epic_dir="logging_refactor", epic="logging-refactor",
                          task_id="task_1_setup")
        return [main, wt]

    def test_writes_all_four_copies(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._two_checkouts(tmp)
            written, notes = sync_task(roots, "task_1_setup", "in-progress")
            self.assertEqual(len(written), 4)
            self.assertEqual(notes, [])
            for path in written:
                self.assertIn('status: "in-progress"', path.read_text())

    def test_modified_advances_on_every_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._two_checkouts(tmp)
            written, _ = sync_task(roots, "task_1_setup", "review")
            for path in written:
                self.assertNotIn('modified: "2026-09-01T09:00:00Z"', path.read_text())
                self.assertIn("modified:", path.read_text())

    def test_completed_at_only_on_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._two_checkouts(tmp)
            sync_task(roots, "task_1_setup", "review")
            self.assertIn("completedAt: null",
                          (roots[0] / ".devtool/features/task_1_setup.md").read_text())
            sync_task(roots, "task_1_setup", "done")
            text = (roots[0] / ".devtool/features/task_1_setup.md").read_text()
            self.assertNotIn("completedAt: null", text)
            self.assertIn('completedAt: "20', text)

    def test_skips_same_task_id_under_a_different_epic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_checkout(root, epic_dir="logging_refactor", epic="logging-refactor",
                          task_id="task_1_setup")
            intruder = root / ".devtool" / "epic" / "payments" / "task_1_setup.md"
            make_task(intruder, epic="payments")
            written, notes = sync_task([root], "task_1_setup", "done")
            self.assertEqual(len(written), 2)
            self.assertNotIn(intruder, written)
            self.assertEqual(len(notes), 1)
            self.assertIn("payments", notes[0])
            self.assertIn('status: "todo"', intruder.read_text())

    def test_checkout_missing_the_task_is_skipped_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            main = Path(tmp) / "main"
            make_checkout(main, epic_dir="logging_refactor", epic="logging-refactor",
                          task_id="task_1_setup")
            written, _ = sync_task([main, Path(tmp) / "empty"], "task_1_setup", "done")
            self.assertEqual(len(written), 2)

    def test_no_copies_anywhere_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            written, notes = sync_task([Path(tmp)], "task_9_absent", "done")
            self.assertEqual(written, [])
            self.assertEqual(notes, [])


class BoardTallyTests(unittest.TestCase):
    def test_counts_by_status_for_one_epic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            features = root / ".devtool" / "features"
            make_task(features / "task_1_a.md", epic="logging-refactor", status="done")
            make_task(features / "task_2_b.md", epic="logging-refactor", status="done")
            make_task(features / "task_3_c.md", epic="logging-refactor", status="in-progress")
            make_task(features / "task_4_d.md", epic="logging-refactor", status="todo")
            make_task(features / "task_5_e.md", epic="payments", status="todo")
            counts = board_tally([root], "logging-refactor")
            self.assertEqual(counts["done"], 2)
            self.assertEqual(counts["in-progress"], 1)
            self.assertEqual(counts["todo"], 1)
            self.assertEqual(counts["backlog"], 0)
            self.assertEqual(counts["review"], 0)

    def test_counts_once_not_per_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = [Path(tmp) / "main", Path(tmp) / "wt"]
            for root in roots:
                make_task(root / ".devtool" / "features" / "task_1_a.md",
                          epic="logging-refactor", status="done")
            self.assertEqual(board_tally(roots, "logging-refactor")["done"], 1)

    def test_unknown_status_value_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_task(root / ".devtool" / "features" / "task_1_a.md",
                      epic="logging-refactor", status="blocked")
            self.assertEqual(sum(board_tally([root], "logging-refactor").values()), 0)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py -v`
Expected: FAIL — `ImportError: cannot import name 'sync_task'`

- [ ] **Step 3: Write the minimal implementation**

Append to `sync_task_status.py`:

```python
def sync_task(roots: list[Path], task_id: str, status: str) -> tuple[list[Path], list[str]]:
    """Write `status` to every copy of `task_id` across every checkout.

    Returns (written_paths, skip_notes). A checkout that does not have the file
    is skipped silently -- a checkout predating the task file is normal. A copy
    whose `epic:` disagrees with the features copy is skipped *and noted*,
    because that is a genuine collision the operator should see.
    """
    epic = expected_epic(roots, task_id)
    stamp = now_iso()
    written: list[Path] = []
    notes: list[str] = []
    for root in roots:
        for path in task_targets(root, task_id):
            found = epic_of(path)
            if epic is not None and found != epic:
                notes.append(f"skipped (epic '{found}' != '{epic}'): {path}")
                continue
            text = path.read_text()
            text = set_frontmatter_field(text, "status", status)
            text = set_frontmatter_field(text, "modified", stamp)
            if status == "done":
                text = set_frontmatter_field(text, "completedAt", stamp)
            path.write_text(text)
            written.append(path)
    return written, notes


def board_tally(roots: list[Path], epic: str) -> dict[str, int]:
    """Count this epic's tasks by status, from the first checkout that has them.

    Only one checkout is counted: they are mirrors, so counting all of them
    would multiply every column by the number of worktrees. A status outside
    the five-column enum is ignored rather than silently inflating a column.
    """
    counts = {status: 0 for status in TASK_STATUSES}
    for root in roots:
        features = root / ".devtool" / "features"
        if not features.is_dir():
            continue
        for path in sorted(features.glob("task_*.md")):
            fields = parse_frontmatter(path.read_text())
            if fields.get("epic") != epic:
                continue
            if fields.get("status") in counts:
                counts[fields["status"]] += 1
        break
    return counts
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py -v`
Expected: PASS — 29 tests

- [ ] **Step 5: Commit**

```bash
git add skills/epic-implementation/resources/scripts/sync_task_status.py \
        skills/epic-implementation/resources/scripts/test_sync_task_status.py
git commit -m "[EPIC_IMPLEMENTATION] Add task status fan-out and board tally" -m "- Write status, modified and completedAt across all four copies of a task
- Skip and report copies belonging to a different epic
- Count the epic board from a single checkout so mirrors do not inflate columns"
```

---

### Task 4: Epic Overview status mode

Rewrite the Meta Data `Status` line in the `.en.md` / `.vi.md` pair — tolerantly, and refusing to guess.

**Files:**
- Modify: `skills/epic-implementation/resources/scripts/sync_task_status.py`
- Test: `skills/epic-implementation/resources/scripts/test_sync_task_status.py`

**Interfaces:**
- Consumes: nothing from earlier tasks (pure text functions).
- Produces: `set_epic_status(text: str, status: str) -> tuple[str, str | None]` returning `(new_text, error_or_none)`, and `sync_epic(roots: list[Path], epic_dir: str, status: str) -> tuple[list[Path], list[str]]` matching `sync_task`'s return shape.

**Why this is fussy:** `epic-designer` prescribes **no line format** for this field — only the example `Status: Queued (backlog) — behind logging-refactor`. Real HLDs may render it as `- **Status**: X`, `**Status:** X`, plain `Status: X`, or a table row. Guessing wrong corrupts an HLD, so the rule is: match tolerantly, scope the search to the Meta Data section, and **fail loud** on zero or multiple hits rather than write.

- [ ] **Step 1: Write the failing test**

Extend the import line to add `set_epic_status, sync_epic`, then append:

```python
EPIC_DOC = '''# Logging Refactor

## 1. Meta Data

- **Epic**: logging-refactor
- **Status**: Queued (backlog) — behind payments
- **Platform**: Flutter

## 2. Background

Status: this word must never be rewritten, it is prose in another section.
'''


class SetEpicStatusTests(unittest.TestCase):
    def test_replaces_bulleted_bold_status(self):
        out, error = set_epic_status(EPIC_DOC, "In Progress")
        self.assertIsNone(error)
        self.assertIn("- **Status**: In Progress", out)
        self.assertNotIn("Queued (backlog)", out)

    def test_leaves_status_word_in_other_sections_alone(self):
        out, _ = set_epic_status(EPIC_DOC, "Done")
        self.assertIn("Status: this word must never be rewritten", out)

    def test_preserves_surrounding_lines(self):
        out, _ = set_epic_status(EPIC_DOC, "Done")
        self.assertIn("- **Epic**: logging-refactor", out)
        self.assertIn("- **Platform**: Flutter", out)

    def test_replaces_bold_colon_inside_rendering(self):
        doc = "## Meta Data\n\n**Status:** Planned\n\n## Background\n"
        out, error = set_epic_status(doc, "Done")
        self.assertIsNone(error)
        self.assertIn("**Status:** Done", out)

    def test_replaces_plain_status(self):
        doc = "## Meta Data\n\nStatus: Planned\n\n## Background\n"
        out, error = set_epic_status(doc, "Done")
        self.assertIsNone(error)
        self.assertIn("Status: Done", out)

    def test_ambiguous_two_status_lines_is_refused(self):
        doc = "## Meta Data\n\n- **Status**: A\n- **Status**: B\n\n## Background\n"
        out, error = set_epic_status(doc, "Done")
        self.assertEqual(out, doc)
        self.assertIn("found 2", error)

    def test_table_rendering_is_refused_not_guessed(self):
        doc = "## Meta Data\n\n| Field | Value |\n|---|---|\n| Status | Planned |\n\n## Background\n"
        out, error = set_epic_status(doc, "Done")
        self.assertEqual(out, doc)
        self.assertIn("found 0", error)

    def test_missing_meta_data_section_is_refused(self):
        doc = "# Epic\n\n## Background\n\nNo meta data here.\n"
        out, error = set_epic_status(doc, "Done")
        self.assertEqual(out, doc)
        self.assertIn("Meta Data", error)


class SyncEpicTests(unittest.TestCase):
    def test_writes_en_and_vi_in_every_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = [Path(tmp) / "main", Path(tmp) / "wt"]
            for root in roots:
                epic_dir = root / ".devtool" / "epic" / "logging_refactor"
                epic_dir.mkdir(parents=True)
                (epic_dir / "logging_refactor.en.md").write_text(EPIC_DOC)
                (epic_dir / "logging_refactor.vi.md").write_text(EPIC_DOC)
            written, notes = sync_epic(roots, "logging_refactor", "In Progress")
            self.assertEqual(len(written), 4)
            self.assertEqual(notes, [])
            for path in written:
                self.assertIn("In Progress", path.read_text())

    def test_missing_vi_variant_is_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            epic_dir = root / ".devtool" / "epic" / "logging_refactor"
            epic_dir.mkdir(parents=True)
            (epic_dir / "logging_refactor.en.md").write_text(EPIC_DOC)
            written, notes = sync_epic([root], "logging_refactor", "Done")
            self.assertEqual(len(written), 1)
            self.assertEqual(notes, [])

    def test_unwritable_shape_is_reported_not_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            epic_dir = root / ".devtool" / "epic" / "logging_refactor"
            epic_dir.mkdir(parents=True)
            (epic_dir / "logging_refactor.en.md").write_text("# Epic\n\n## Background\n")
            written, notes = sync_epic([root], "logging_refactor", "Done")
            self.assertEqual(written, [])
            self.assertEqual(len(notes), 1)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py -v`
Expected: FAIL — `ImportError: cannot import name 'set_epic_status'`

- [ ] **Step 3: Write the minimal implementation**

Add these two constants below `FRONTMATTER_RE` in `sync_task_status.py`:

```python
# The Epic Overview's Meta Data section: its heading through to the next heading.
# Scoping the Status search to this block is what stops the word "Status"
# appearing in later prose from being rewritten.
META_SECTION_RE = re.compile(r"^#{1,6}[^\n]*?Meta\s*Data[^\n]*$\n(.*?)(?=^#{1,6}\s|\Z)", re.M | re.S)
# A Status line in any of the renderings epic-designer permits: optionally
# bulleted, optionally bold-wrapped, with the bold marker on either side of the
# colon. Group 1 is the whole prefix through the colon and is preserved verbatim;
# only group 2, the value, is replaced.
EPIC_STATUS_RE = re.compile(r"^(\s*(?:[-*+]\s+)?(?:\*\*)?Status(?:\*\*)?\s*:\s*(?:\*\*)?\s*)(.*)$", re.M)
```

Append these functions:

```python
def set_epic_status(text: str, status: str) -> tuple[str, str | None]:
    """Replace the Meta Data Status value. Returns (new_text, error_or_none).

    Refuses to write on anything ambiguous -- zero matches (a table rendering,
    say) or more than one. Corrupting an HLD is strictly worse than skipping it
    and telling the operator to edit by hand.
    """
    section = META_SECTION_RE.search(text)
    if not section:
        return text, "no Meta Data section found"
    body = section.group(1)
    hits = EPIC_STATUS_RE.findall(body)
    if len(hits) != 1:
        return text, f"expected exactly one Status line in Meta Data, found {len(hits)}"
    new_body = EPIC_STATUS_RE.sub(lambda m: m.group(1) + status, body, count=1)
    return text[:section.start(1)] + new_body + text[section.end(1):], None


def sync_epic(roots: list[Path], epic_dir: str, status: str) -> tuple[list[Path], list[str]]:
    """Set the Epic Overview Status in both language variants, every checkout.

    `.en.md` and `.vi.md` are written in the same call so the pair epic-designer
    requires to stay in sync can never diverge. A missing `.vi.md` is normal and
    not an error; an unparseable document is reported.
    """
    written: list[Path] = []
    notes: list[str] = []
    for root in roots:
        for variant in ("en", "vi"):
            path = root / ".devtool" / "epic" / epic_dir / f"{epic_dir}.{variant}.md"
            if not path.is_file():
                continue
            new_text, error = set_epic_status(path.read_text(), status)
            if error:
                notes.append(f"skipped ({error}): {path}")
                continue
            path.write_text(new_text)
            written.append(path)
    return written, notes
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py -v`
Expected: PASS — 40 tests

- [ ] **Step 5: Commit**

```bash
git add skills/epic-implementation/resources/scripts/sync_task_status.py \
        skills/epic-implementation/resources/scripts/test_sync_task_status.py
git commit -m "[EPIC_IMPLEMENTATION] Add Epic Overview status rewriting" -m "- Scope the Status search to the Meta Data section so later prose is safe
- Accept bulleted, bold and plain renderings, preserving the original prefix
- Refuse to write on zero or multiple matches instead of guessing
- Write the en and vi variants together so the pair cannot diverge"
```

---

### Task 5: Command-line interface

Make the script usable, with the exit codes the skill relies on.

**Files:**
- Modify: `skills/epic-implementation/resources/scripts/sync_task_status.py`
- Test: `skills/epic-implementation/resources/scripts/test_sync_task_status.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `main(argv: list[str] | None = None) -> int`. Exit codes: `0` at least one file written, `1` nothing matched, `2` invalid status or arguments.

- [ ] **Step 1: Write the failing test**

Add `import io`, `import contextlib` and `import sync_task_status as sts` to the test file's imports, extend the `from sync_task_status import ...` line to add `main`, then append:

```python
class MainTests(unittest.TestCase):
    def setUp(self):
        self._real_roots = sts.checkout_roots
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        make_checkout(self.root, epic_dir="logging_refactor", epic="logging-refactor",
                      task_id="task_1_setup")
        sts.checkout_roots = lambda: [self.root]

    def tearDown(self):
        sts.checkout_roots = self._real_roots
        self._tmp.cleanup()

    def _run(self, argv: list[str]) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = main(argv)
        return code, out.getvalue()

    def test_invalid_status_exits_2_and_writes_nothing(self):
        code, output = self._run(["task", "task_1_setup", "blocked"])
        self.assertEqual(code, 2)
        self.assertIn("blocked", output)
        self.assertIn('status: "todo"',
                      (self.root / ".devtool/features/task_1_setup.md").read_text())

    def test_every_enum_value_is_accepted(self):
        for status in ("backlog", "todo", "in-progress", "review", "done"):
            self.assertEqual(self._run(["task", "task_1_setup", status])[0], 0, status)

    def test_unknown_task_exits_1(self):
        self.assertEqual(self._run(["task", "task_9_absent", "done"])[0], 1)

    def test_success_exits_0_and_prints_written_paths(self):
        code, output = self._run(["task", "task_1_setup", "in-progress"])
        self.assertEqual(code, 0)
        self.assertIn("task_1_setup.md", output)

    def test_success_prints_board_tally(self):
        _, output = self._run(["task", "task_1_setup", "done"])
        self.assertIn("backlog 0", output)
        self.assertIn("done 1", output)
        self.assertIn("in-progress 0", output)

    def test_epic_mode_does_not_enforce_the_task_enum(self):
        epic_dir = self.root / ".devtool" / "epic" / "logging_refactor"
        (epic_dir / "logging_refactor.en.md").write_text(EPIC_DOC)
        code, _ = self._run(["epic", "logging_refactor", "In Progress"])
        self.assertEqual(code, 0)
        self.assertIn("In Progress", (epic_dir / "logging_refactor.en.md").read_text())

    def test_epic_mode_with_no_overview_exits_1(self):
        self.assertEqual(self._run(["epic", "no_such_epic", "Done"])[0], 1)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py -v`
Expected: FAIL — `ImportError: cannot import name 'main'`

- [ ] **Step 3: Write the minimal implementation**

Add `import argparse` and `import sys` to the top of `sync_task_status.py`, then append:

```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_subparsers(dest="mode", required=True)
    task_mode = modes.add_parser("task", help="Set one task's status in every checkout")
    task_mode.add_argument("task_id", help="Task id, e.g. task_1_setup")
    task_mode.add_argument("status", help=f"One of: {', '.join(TASK_STATUSES)}")
    epic_mode = modes.add_parser("epic", help="Set the Epic Overview's Meta Data Status")
    epic_mode.add_argument("epic_dir", help="Epic directory name, e.g. logging_refactor")
    epic_mode.add_argument("status", help="Free-form, e.g. 'In Progress' or 'Done'")
    args = parser.parse_args(argv)

    # Validate before the subprocess: a typo'd status should not depend on being
    # inside a git repo to report itself.
    if args.mode == "task" and args.status not in TASK_STATUSES:
        print(f"Invalid status '{args.status}'. Expected one of: {', '.join(TASK_STATUSES)}",
              file=sys.stderr)
        return 2

    roots = checkout_roots()
    if args.mode == "task":
        epic = expected_epic(roots, args.task_id)
        written, notes = sync_task(roots, args.task_id, args.status)
        target = args.task_id
    else:
        epic = None
        written, notes = sync_epic(roots, args.epic_dir, args.status)
        target = args.epic_dir

    for path in written:
        print(f"  wrote {path}")
    for note in notes:
        print(f"  {note}")
    if not written:
        print(f"No files updated for '{target}'.", file=sys.stderr)
        return 1
    if epic:
        counts = board_tally(roots, epic)
        print("  " + " | ".join(f"{status} {counts[status]}" for status in TASK_STATUSES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py -v`
Expected: PASS — 47 tests

Then confirm the CLI is wired up for real:

Run: `python3 skills/epic-implementation/resources/scripts/sync_task_status.py --help`
Expected: usage text listing the `task` and `epic` subcommands.

Run: `python3 skills/epic-implementation/resources/scripts/sync_task_status.py task task_1_x blocked; echo "exit=$?"`
Expected: `Invalid status 'blocked'...` and `exit=2`

- [ ] **Step 5: Commit**

```bash
git add skills/epic-implementation/resources/scripts/sync_task_status.py \
        skills/epic-implementation/resources/scripts/test_sync_task_status.py
git commit -m "[EPIC_IMPLEMENTATION] Add sync_task_status command-line interface" -m "- Add task and epic subcommands over the existing sync functions
- Reject statuses outside the five-column enum with exit code 2
- Print written paths, skip notes and a board tally on success"
```

---

### Task 6: Phase 1 base-ref resolution

Replace the hardcoded `develop` with a check that the ref actually carries the epic's documents.

**Files:**
- Modify: `skills/epic-implementation/SKILL.md:89-104` (Phase 1)

**Interfaces:**
- Consumes: `<epic_dir>`, `<epic_slug>`, and the task file list from Phase 0.
- Produces: `<base_ref>` — a placeholder the rest of the skill (Phase 4, Quick Reference) refers to by that exact name.

**Why:** `epic-designer` has no branch discipline, so the epic docs land on whatever branch that session was on. A worktree cut from `develop` when the docs live elsewhere has no HLD and no `task_*.md` files at all — Phase 0 has nothing to read and the mirror has nothing to write to.

- [ ] **Step 1: Replace Phase 1 step 3 with two steps**

Find this line in `skills/epic-implementation/SKILL.md`:

```markdown
3. **Checkpoint:** present the final order (with any manual adjustment explained) to the user and get confirmation before creating any worktree or dispatching any subagent.
```

Replace it with:

````markdown
3. **Resolve the worktree's base ref.** Phase 0 already read this epic's exact set of task files, so "this ref carries the epic" is an exact check rather than a guess: the HLD **and every one of those task paths** must exist at the ref.
   ```bash
   git cat-file -e <ref>:.devtool/epic/<epic_dir>/<epic_dir>.en.md   # HLD present at that ref?
   git ls-tree --name-only <ref> -- .devtool/features/               # which task files are there?
   ```
   Try `develop` first, then the current `HEAD`, and take the first ref where the HLD resolves and every Phase 0 task path appears. If neither qualifies, find where the docs actually live:
   ```bash
   SHA=$(git log --all --format=%H --diff-filter=A -1 -- .devtool/epic/<epic_dir>/<epic_dir>.en.md)
   git branch --all --contains "$SHA"
   ```
   Present that branch list at the checkpoint and let the user choose. **An empty list means the epic docs were never committed** — almost always `auto_commit: false` in `.agents/config.json`. Stop and say exactly that; do not create a worktree against a ref that lacks the epic.

   Record the chosen ref as `<base_ref>`. The rest of this skill refers to it by that name.
4. **Checkpoint (Gate 3):** present three things and get confirmation before creating any worktree or dispatching any subagent:
   - the final execution order, with any manual adjustment explained;
   - the resolved `<base_ref>`;
   - **if `<base_ref>` is not `develop`**, the output of `git log --oneline develop..<base_ref>`. That is precisely the unrelated work the epic branch would carry into `develop` at Phase 4, so confirm the inheritance explicitly — not just the order.
````

- [ ] **Step 2: Renumber the continuation steps and use the resolved ref**

In the `#### Phase 1 (continued) — Worktree Bootstrap` section, renumber `4.` → `5.`, `5.` → `6.`, `6.` → `7.`, and change the worktree command. The step that currently reads:

```markdown
4. Create one worktree for the whole epic, following `d3nexus:using-git-worktrees`. Spell the base ref out explicitly:
   ```bash
   git worktree add .worktrees/<epic_dir> -b epic/<epic_slug> develop
   ```
```

becomes:

```markdown
5. Create one worktree for the whole epic, following `d3nexus:using-git-worktrees`. Spell the base ref out explicitly — `d3nexus:using-git-worktrees` branches from current HEAD otherwise:
   ```bash
   git worktree add .worktrees/<epic_dir> -b epic/<epic_slug> <base_ref>
   ```
```

- [ ] **Step 3: Verify the numbering is contiguous**

Run: `sed -n '89,130p' skills/epic-implementation/SKILL.md`
Expected: Phase 1 reads `1.` `2.` `3.` `4.`, and the continuation reads `5.` `6.` `7.` with no repeats or gaps.

- [ ] **Step 4: Verify the kit still passes**

Run: `bash scripts/verify.sh`
Expected: `PASS — safe to publish`

- [ ] **Step 5: Commit**

```bash
git add skills/epic-implementation/SKILL.md
git commit -m "[EPIC_IMPLEMENTATION] Resolve the worktree base ref instead of hardcoding develop" -m "- Verify a candidate ref carries the HLD and every Phase 0 task path
- Fall back to listing branches that contain the epic docs and let the user pick
- Stop with a specific message when the docs were never committed
- Confirm the base ref and any inherited commits at the Gate 3 checkpoint"
```

---

### Task 7: Phase 2 and Phase 4 wiring

Replace hand edits with script calls, and clear the main checkout before the merge.

**Files:**
- Modify: `skills/epic-implementation/SKILL.md:126-135` (Phase 2 steps 1-5), `skills/epic-implementation/SKILL.md:211-220` (Phase 4)

**Interfaces:**
- Consumes: `sync_task_status.py` (Tasks 1-5), `<base_ref>` (Task 6), `SKILL_DIR` (already resolved in Phase 0 step 2).
- Produces: nothing further.

- [ ] **Step 1: Replace Phase 2 step 1**

Find:

```markdown
1. **Live Kanban Status**: Before dispatching, edit — **do not commit** — that task's frontmatter in `.devtool/features/task_<n>.md` to `status: "in-progress"`.
```

Replace with:

````markdown
1. **Live Kanban Status**: Before dispatching, flip the task in every checkout — **do not commit**:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py task <task_id> in-progress
   ```
   This writes `status` and `modified` to all four copies of the task — `.devtool/features/` and `.devtool/epic/<epic_dir>/`, in both this worktree and the main checkout — so the Kanban board is accurate in whichever workspace you are watching. It prints every file it wrote plus a board tally. Never hand-edit a single copy; that is how the four drift apart.

   **Before the first task of the epic only**, also flip the Epic Overview:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"
   ```
````

- [ ] **Step 2: Replace Phase 2 steps 2-4**

Find:

```markdown
2. Once the implementer reports `DONE`, edit frontmatter to `status: "review"` before dispatching reviewers.
3. If review finds issues, cycle between `status: "in-progress"` and `status: "review"` through the fix loop.
4. Only once both reviews pass, update frontmatter: `status: "done"`, `completedAt: "<ISO-8601 now>"`.
```

Replace with:

```markdown
2. Once the implementer reports `DONE`, run `sync_task_status.py task <task_id> review` before dispatching reviewers.
3. If review finds issues, cycle between `in-progress` and `review` through the fix loop — one script call per flip, so `modified` keeps tracking reality.
4. Only once both reviews pass, run `sync_task_status.py task <task_id> done`. The script sets `completedAt` itself; never write that field by hand.
```

- [ ] **Step 3: Update the Phase 2 step 5 commit block**

Find the comment line:

```markdown
   git add -A                                    # code changes + .devtool/features/task_<n>.md
```

Replace with:

```markdown
   git add -A                                    # code + .devtool/features/ + .devtool/epic/<epic_dir>/ copies
```

And immediately after the sentence "The body lists the subtasks this task actually contained — drop it if there was only one.", add:

```markdown
   Only this worktree's copies are committed. The main checkout's mirrored copies are deliberately never staged — they are a live view for the board, and Phase 4 clears them.
```

- [ ] **Step 4: Replace the Phase 4 closing line**

Find:

```markdown
Only when `@quality_check` reports **🟢 LGTM (All checks passing)**, use `d3nexus:finishing-a-development-branch` on the epic branch (base = `develop`).
```

Replace with:

````markdown
Only when `@quality_check` reports **🟢 LGTM (All checks passing)**, close the epic out in this order:

1. Flip the Epic Overview to done:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "Done"
   ```
2. Resolve `<main_root>` — the **first** entry of `git worktree list --porcelain`, which git always reports as the main worktree. Never assume it is the current directory; this phase can run from either checkout.
   ```bash
   MAIN_ROOT=$(git worktree list --porcelain | awk '/^worktree /{print substr($0,10); exit}')
   ```
3. Clear the main checkout's mirrored copies — they were a live view, never history:
   ```bash
   git -C "$MAIN_ROOT" restore -- .devtool/features/ .devtool/epic/<epic_dir>/
   git -C "$MAIN_ROOT" status --porcelain -- .devtool/features/ .devtool/epic/<epic_dir>/
   ```
   Report what was reverted. The restore is worktree-only — no `--staged` — so anything a person staged by hand survives it. The second command is the proof step and should print nothing; **if it prints, stop** and surface it rather than forcing the merge.
4. Use `d3nexus:finishing-a-development-branch` on the epic branch with **base = `<base_ref>`** as recorded in Phase 1 — not a hardcoded `develop`.
````

- [ ] **Step 5: Verify and commit**

Run: `bash scripts/verify.sh`
Expected: `PASS — safe to publish`

```bash
git add skills/epic-implementation/SKILL.md
git commit -m "[EPIC_IMPLEMENTATION] Drive task status through sync_task_status in Phases 2 and 4" -m "- Replace per-copy hand edits with sync_task_status calls on every transition
- Flip the Epic Overview status at the first task and at LGTM
- Restore the main checkout mirrored copies before finishing the branch
- Finish the epic branch against the Phase 1 base ref"
```

---

### Task 8: Supporting sections and the lifecycle gate

Make the reference tables, the mistake list, and the gate owner tell the same story as the phases.

**Files:**
- Modify: `skills/epic-implementation/SKILL.md` (Quick Reference, Common Mistakes, Red Flags)
- Modify: `skills/epic-lifecycle/SKILL.md:61`, `skills/epic-lifecycle/SKILL.md:118`

**Interfaces:**
- Consumes: everything above.
- Produces: nothing further.

- [ ] **Step 1: Update the Quick Reference table**

After the `| Compute execution order | ... |` row, insert:

```markdown
| Sync task status | `sync_task_status.py task <task_id> <status>` | Same | Same |
```

And change the worktree row from `... -b epic/<epic_slug> develop` to `... -b epic/<epic_slug> <base_ref>`.

- [ ] **Step 2: Rewrite the base-ref Common Mistake**

Find:

```markdown
**Creating the epic worktree without an explicit base ref** — `d3nexus:using-git-worktrees` branches from current HEAD. Always pass `develop` explicitly.
```

Replace with:

```markdown
**Creating the epic worktree from a ref that lacks the epic docs** — `develop` is the usual answer but not an automatic one: `epic-designer` has no branch discipline, so the HLD and `task_*.md` files land on whatever branch that session was on. A worktree cut from a ref without them leaves Phase 0 with nothing to read, `compute_execution_order.py` scanning zero tasks, and the status mirror with no files to write. Resolve `<base_ref>` per Phase 1 step 3 and pass it explicitly — `d3nexus:using-git-worktrees` branches from current HEAD otherwise.
```

- [ ] **Step 3: Update the stale-status Common Mistake**

Find the mistake beginning `**Leaving `status` at `todo` while a task is actually running**` and replace its body with:

```markdown
**Leaving `status` at `todo` while a task is actually running** — the board should show `in-progress` the moment you dispatch the implementer and `review` the moment reviewers are dispatched, cycling between the two through any fix rounds. Every flip goes through `sync_task_status.py`, which updates all four copies live on disk with no commit of their own; only the final `done` flip rides along with the task's single commit. The board's real columns are `backlog | todo | in-progress | review | done` — the script rejects anything else with exit code 2, so a stalled task just stays at `in-progress`.
```

- [ ] **Step 4: Add two Common Mistakes**

Append to the Common Mistakes section:

```markdown
**Hand-editing one copy of a task file** — each task exists four times: `.devtool/features/` and `.devtool/epic/<epic_dir>/`, in both the worktree and the main checkout. Editing one leaves three stale and the boards disagree. Always go through `sync_task_status.py`, which also maintains `modified` and `completedAt` for you.

**Leaving the main checkout dirty at merge time** — the mirrored copies there are tracked files, so an un-cleared mirror makes the epic merge fail with "your local changes would be overwritten by merge". Phase 4 step 3 clears them. The same one-liner is the recovery if an epic is abandoned mid-run: `git -C "$MAIN_ROOT" restore -- .devtool/features/ .devtool/epic/<epic_dir>/`.
```

- [ ] **Step 5: Add a Red Flag**

Append to the Red Flags list:

```markdown
- Merging the epic branch while the main checkout's mirrored task copies are still dirty.
```

- [ ] **Step 6: Update the two epic-lifecycle Gate 3 cells**

In `skills/epic-lifecycle/SKILL.md`, find:

```markdown
| **3** | Execution Order | User | `epic-implementation` Phase 1 checkpoint | confirmed order + bootstrapped worktree |
```

Replace with:

```markdown
| **3** | Execution Plan | User | `epic-implementation` Phase 1 checkpoint | confirmed order + base ref + bootstrapped worktree |
```

Then find:

```markdown
| 3 | Stage 3 Phase 1 — reorder by hand; prose notes in task files outrank the calculator |
```

Replace with:

```markdown
| 3 | Stage 3 Phase 1 — reorder by hand, or re-pick the base ref; prose notes in task files outrank the calculator |
```

- [ ] **Step 7: Run the full verification**

Run: `python3 skills/epic-implementation/resources/scripts/test_sync_task_status.py -v`
Expected: PASS — 47 tests

Run: `python3 skills/epic-implementation/resources/scripts/test_compute_execution_order.py -v`
Expected: PASS — the existing suite is unaffected by this change.

Run: `bash scripts/verify.sh`
Expected: `PASS — safe to publish`

Run: `grep -n "develop" skills/epic-implementation/SKILL.md`
Expected: every remaining hit is prose about the *default* or the merge target — no surviving `-b epic/<epic_slug> develop` command and no `base = \`develop\`` claim.

- [ ] **Step 8: Commit**

```bash
git add skills/epic-implementation/SKILL.md skills/epic-lifecycle/SKILL.md
git commit -m "[EPIC_IMPLEMENTATION] Align reference tables and lifecycle gate with status sync" -m "- Add a sync task status row and the base ref placeholder to Quick Reference
- Rewrite the base ref mistake and add mirror drift and dirty checkout mistakes
- Flag merging with the main checkout still dirty
- Widen epic-lifecycle Gate 3 to cover the base ref"
```

---

## Plan Self-Review

**1. Spec coverage.** Every section of the spec maps to a task:

| Spec section | Task |
|---|---|
| §5.1 CLI | 5 |
| §5.2 Checkout discovery | 2 |
| §5.3 `task` mode, enum guard, collision guard | 1, 2, 3 |
| §5.4 `epic` mode, fail-loud on ambiguity | 4 |
| §5.5 Output and exit codes | 3, 5 |
| §6 Test coverage | 1-5 (tests are written first in each) |
| §7.1 Base-ref resolution | 6 |
| §7.2 Phase 2 transitions | 7 |
| §7.3 Phase 4 close-out | 7 |
| §7.4 Supporting sections | 8 |
| §8 epic-lifecycle Gate 3 | 8 |

**2. Placeholder scan.** No `TBD`, no "add appropriate error handling", no "similar to Task N". Every code step carries the actual code; every verification step carries the actual command and its expected output.

**3. Type consistency.** `sync_task` and `sync_epic` deliberately share the return shape `tuple[list[Path], list[str]]` so `main` handles both through one code path. `board_tally` returns `dict[str, int]` keyed by `TASK_STATUSES`, which is what `main` iterates to print the tally. `set_epic_status` is the one function returning `(text, error)` rather than raising — `sync_epic` turns that error into a skip note, matching how `sync_task` reports collisions.

**One deliberate refinement against the spec.** §5.3 says the epic value is read from the features copy "in the invoking checkout". `expected_epic` instead takes the first checkout that has the file, main worktree first. This satisfies the spec's intent — the features copy is the authority for which epic a task id belongs to — while removing a needless `git rev-parse --show-toplevel` call, and mirrors cannot disagree about a task's `epic:` field. Noted here so the difference is a decision on the record rather than a drift.
