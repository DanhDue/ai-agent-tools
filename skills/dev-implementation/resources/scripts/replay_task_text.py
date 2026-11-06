#!/usr/bin/env python3
"""Task Text Replay Engine and Static Anchor Verification.

Applies structured fenced directives (Create, Replace in, Insert in) from task markdown,
verifies edit anchors statically, and replays epics inside isolated git worktrees.
"""
from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from run_task_checks import (
    ContractError,
    detail_of,
    epic_layout,
    epic_scenario_ids,
    fingerprint,
    load_evidence,
    parse_evidence_files,
    parse_verification,
    run_command,
    run_row,
    validate_pytest_red,
)


@dataclass(frozen=True)
class CreateDirective:
    path: str
    content: str


@dataclass(frozen=True)
class ReplaceDirective:
    path: str
    target: str
    replacement: str


@dataclass(frozen=True)
class InsertDirective:
    path: str
    position: str  # "after" or "before"
    anchor: str
    content: str


Directive = CreateDirective | ReplaceDirective | InsertDirective

CREATE_RE = re.compile(
    r"^(?:Create\s+`?([^`:\s\n]+)`?\s*:|File:\s*`?([^`:\s\n]+)`?\s*:?|<!--\s*@@FILE:\s*([^\s@]+)\s*@@\s*-->)\s*$"
)
REPLACE_RE = re.compile(r"^Replace\s+in\s+`?([^`:\s\n]+)`?\s*:\s*$")
INSERT_RE = re.compile(r"^Insert\s+in\s+`?([^`:\s\n(]+)`?\s*(?:\((after|before)\)|(after|before))\s*:\s*$")
WITH_RE = re.compile(r"^With\s*:\s*$")
FENCE_START_RE = re.compile(r"^(\s*)(`{3,}|~{3,})")


def is_test_file(path_str: str) -> bool:
    p = Path(path_str)
    return p.name.startswith("test_") or p.name.endswith("_test.py") or "tests" in p.parts


def _extract_fenced_block(lines: list[str], start_idx: int) -> tuple[str, int]:
    idx = start_idx
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx >= len(lines):
        raise ContractError("Expected fenced code block, reached EOF")

    m = FENCE_START_RE.match(lines[idx])
    if not m:
        raise ContractError(f"Expected fenced code block at line {idx + 1}, got: {lines[idx]!r}")

    fence_chars = m.group(2)
    idx += 1
    content_lines: list[str] = []
    while idx < len(lines):
        line = lines[idx]
        if line.strip().startswith(fence_chars):
            return "\n".join(content_lines) + ("\n" if content_lines else ""), idx + 1
        content_lines.append(line)
        idx += 1
    raise ContractError(f"Unclosed fenced code block starting at line {start_idx + 1}")


def parse_task_directives(task_text: str) -> list[Directive]:
    """Parse Create, Replace in, and Insert in directives from task prose outside Gherkin blocks."""
    lines = task_text.splitlines()
    directives: list[Directive] = []
    idx = 0
    in_gherkin = False
    gherkin_fence = ""

    while idx < len(lines):
        line = lines[idx].strip()

        if in_gherkin:
            if line.startswith(gherkin_fence):
                in_gherkin = False
            idx += 1
            continue

        if line.startswith(("```gherkin", "~~~gherkin")):
            in_gherkin = True
            gherkin_fence = line[:3]
            idx += 1
            continue

        m_create = CREATE_RE.match(line)
        if m_create:
            path = (m_create.group(1) or m_create.group(2) or m_create.group(3)).strip()
            content, next_idx = _extract_fenced_block(lines, idx + 1)
            directives.append(CreateDirective(path=path, content=content))
            idx = next_idx
            continue

        m_replace = REPLACE_RE.match(line)
        if m_replace:
            path = m_replace.group(1).strip()
            target, next_idx = _extract_fenced_block(lines, idx + 1)
            # Find With:
            while next_idx < len(lines) and not lines[next_idx].strip():
                next_idx += 1
            if next_idx >= len(lines) or not WITH_RE.match(lines[next_idx].strip()):
                raise ContractError(f"Expected 'With:' after 'Replace in {path}' anchor at line {next_idx + 1}")
            replacement, after_with_idx = _extract_fenced_block(lines, next_idx + 1)
            directives.append(ReplaceDirective(path=path, target=target, replacement=replacement))
            idx = after_with_idx
            continue

        m_insert = INSERT_RE.match(line)
        if m_insert:
            path = m_insert.group(1).strip()
            position = (m_insert.group(2) or m_insert.group(3)).strip()
            anchor, next_idx = _extract_fenced_block(lines, idx + 1)
            # Find With:
            while next_idx < len(lines) and not lines[next_idx].strip():
                next_idx += 1
            if next_idx >= len(lines) or not WITH_RE.match(lines[next_idx].strip()):
                raise ContractError(f"Expected 'With:' after 'Insert in {path}' anchor at line {next_idx + 1}")
            content, after_with_idx = _extract_fenced_block(lines, next_idx + 1)
            directives.append(InsertDirective(path=path, position=position, anchor=anchor, content=content))
            idx = after_with_idx
            continue

        idx += 1

    return directives


def apply_task_directives(root: Path, directives: list[Directive]) -> None:
    """Apply parsed directives to files in root."""
    for d in directives:
        target_path = root / d.path
        if isinstance(d, CreateDirective):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(d.content, encoding="utf-8")
        elif isinstance(d, ReplaceDirective):
            if not target_path.is_file():
                raise ContractError(f"Target file for Replace in does not exist: {d.path}")
            text = target_path.read_text(encoding="utf-8")
            if d.target not in text:
                raise ContractError(f"Anchor not found in {d.path}: {d.target!r}")
            new_text = text.replace(d.target, d.replacement, 1)
            target_path.write_text(new_text, encoding="utf-8")
        elif isinstance(d, InsertDirective):
            if not target_path.is_file():
                raise ContractError(f"Target file for Insert in does not exist: {d.path}")
            text = target_path.read_text(encoding="utf-8")
            if d.anchor not in text:
                raise ContractError(f"Anchor not found in {d.path}: {d.anchor!r}")
            if d.position == "after":
                idx = text.find(d.anchor) + len(d.anchor)
                new_text = text[:idx] + d.content + text[idx:]
            else:
                idx = text.find(d.anchor)
                new_text = text[:idx] + d.content + text[idx:]
            target_path.write_text(new_text, encoding="utf-8")


def verify_task_edit_anchors(
    root: Path,
    task_path: Path,
    task_text: str,
    prior_modified: set[str] | None = None,
) -> list[str]:
    """Verify that every Replace in or Insert in anchor occurs exactly once in tracked files."""
    if prior_modified is None:
        prior_modified = set()

    try:
        directives = parse_task_directives(task_text)
    except ContractError as err:
        return [f"{task_path.name}: {err}"]

    errors: list[str] = []
    for d in directives:
        if isinstance(d, CreateDirective):
            prior_modified.add(d.path)
            continue

        path = d.path
        anchor = d.target if isinstance(d, ReplaceDirective) else d.anchor
        first_line = anchor.splitlines()[0] if anchor.splitlines() else ""

        if path not in prior_modified:
            target_file = root / path
            if not target_file.is_file():
                errors.append(f"{task_path.name}: missing edit anchor in {path}: {first_line!r}")
            else:
                try:
                    content = target_file.read_text(encoding="utf-8", errors="ignore")
                    count = content.count(anchor)
                    if count == 0:
                        errors.append(f"{task_path.name}: missing edit anchor in {path}: {first_line!r}")
                    elif count >= 2:
                        errors.append(f"{task_path.name}: ambiguous edit anchor ({count} matches) in {path}: {first_line!r}")
                except OSError as err:
                    errors.append(f"{task_path.name}: cannot read {path}: {err}")
        prior_modified.add(path)

    return errors


def replay_task(
    root: Path,
    task_path: Path,
    task_text: str,
    run_rows: bool = False,
    timeout: int = 600,
) -> tuple[int, list[str]]:
    """Replay directives and rows for a single task."""
    directives = parse_task_directives(task_text)
    test_directives = [d for d in directives if is_test_file(d.path)]
    prod_directives = [d for d in directives if not is_test_file(d.path)]

    # 1. Apply test directives
    apply_task_directives(root, test_directives)

    if not run_rows:
        apply_task_directives(root, prod_directives)
        return 0, []

    rows, red_na = parse_verification(task_text)

    # If task has RED rows, verify failure
    red_rows = [r for r in rows if r.phase == "RED"]
    if red_na is None and red_rows:
        for r in red_rows:
            code, raw_output = run_command(r.command, root, timeout)
            out_tail = raw_output.decode("utf-8", errors="replace")
            err = validate_pytest_red(r.command, code, out_tail)
            if err:
                return 1, [f"{task_path.name}:{r.id} RED did not fail as expected: {err}"]

    # 2. Apply prod directives
    apply_task_directives(root, prod_directives)

    layout = epic_layout(task_path)
    scenario_ids = epic_scenario_ids(layout)

    # 3. Execute MEASURE rows first
    measure_rows = [r for r in rows if r.phase == "MEASURE"]
    for r in measure_rows:
        record = run_row(r, root, timeout, scenario_ids)
        if record["outcome"] != "PASS":
            return 1, [f"{task_path.name}:{r.id} MEASURE {record['outcome']} {detail_of(record)}"]

    # Verify declared Evidence files
    for entry in parse_evidence_files(task_text):
        ev_file = root / entry.pattern
        if not ev_file.is_file() or ev_file.stat().st_size == 0:
            return 1, [f"{task_path.name}: Evidence file {entry.pattern} missing or empty after MEASURE"]

    # 4. Execute GREEN, TIER-B, and TIER-C rows
    verify_rows = [r for r in rows if r.phase in ("GREEN", "TIER-B", "TIER-C")]
    for r in verify_rows:
        record = run_row(r, root, timeout, scenario_ids)
        if record["outcome"] != "PASS":
            return 1, [f"{task_path.name}:{r.id} {r.phase} {record['outcome']} {detail_of(record)}"]

    return 0, []


def replay_epic_in_worktree(
    root: Path,
    epic_dir: str,
    timeout: int = 600,
) -> tuple[int, list[str]]:
    """Replay all tasks of an epic inside an isolated temporary git worktree."""
    temp_worktree_dir = tempfile.TemporaryDirectory()
    worktree_path = Path(temp_worktree_dir.name) / "replay_worktree"

    try:
        # Create detached worktree at HEAD
        res = subprocess.run(
            ["git", "-C", str(root), "worktree", "add", "--detach", str(worktree_path), "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            return 1, [f"Failed to create temporary git worktree: {res.stderr.strip()}"]

        # Find task files
        epic_tasks_dir = worktree_path / ".devtool" / "epic" / epic_dir
        if not epic_tasks_dir.is_dir():
            return 1, [f"Epic directory not found in worktree: {epic_tasks_dir}"]

        task_files = sorted(epic_tasks_dir.glob("task_*.md"))
        errors: list[str] = []
        for task_path in task_files:
            text = task_path.read_text(encoding="utf-8")
            code, msgs = replay_task(worktree_path, task_path, text, run_rows=True, timeout=timeout)
            if code != 0:
                errors.extend(msgs)
                return code, errors

        return 0, []

    finally:
        subprocess.run(
            ["git", "-C", str(root), "worktree", "remove", "--force", str(worktree_path)],
            check=False,
            capture_output=True,
        )
        temp_worktree_dir.cleanup()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("task", type=Path)
    parser.add_argument("--worktree", type=Path, default=None)
    parser.add_argument("--run-rows", action="store_true")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args(argv)

    if not args.task.is_file():
        print(f"error: task file not found: {args.task}", file=sys.stderr)
        return 2

    root = args.worktree.resolve() if args.worktree else Path.cwd().resolve()
    text = args.task.read_text(encoding="utf-8")
    try:
        code, msgs = replay_task(root, args.task, text, run_rows=args.run_rows, timeout=args.timeout)
        for msg in msgs:
            print(msg, file=sys.stderr)
        return code
    except ContractError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
