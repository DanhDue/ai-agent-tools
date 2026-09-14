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
import subprocess
from datetime import datetime, timezone
from pathlib import Path

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
