#!/usr/bin/env python3
"""Check the task files and HLD a designer wrote against the task contract, before Gate 2 closes.

Usage:
  check_task_contract.py [--design] --hld <epic_dir>.en.md --tasks <task_*.md ...>

Prints problems as `<task stem>:<row or section>: <problem>` or `<hld file name>: <problem>`, the
implicit protected paths, and a Result line. Exit codes: 0 no problem; 1 problems; 2 usage error.
Python 3 standard library only.
"""
from __future__ import annotations

import argparse
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import task_contract as tc
from check_bdd_traceability import UsageError, covers_of, read_text

SECTIONS = ("Files", "Verification", "Definition of Done", "Stop and Report If", "Decisions Already Made")
ROW_PREFIX = re.compile(r"^Verification row [^:]+: ")
STATUS = re.compile(r'^status:\s*"?([A-Za-z_-]+)"?\s*$', re.M)
GLOB_CHARS = re.compile(r"[*?]")


class Checker:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.problems: list[str] = []
        self.warnings: list[str] = []
        listed = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, text=True).stdout
        self.tracked = set(listed.split("\0")) - {""}

    def ignored(self, path: str) -> bool:
        return subprocess.run(["git", "check-ignore", "-q", "--", path], cwd=self.root,
                              capture_output=True).returncode == 0

    def problem(self, where: str, text: str) -> None:
        self.problems.append(f"{where}: {text}")

    def is_tracked(self, path: str) -> bool:
        return path in self.tracked

    def matches_tracked(self, pattern: str) -> bool:
        return any(tc.path_matches(pattern, name) for name in self.tracked)


def read_file(path: Path) -> str:
    try:
        return read_text(path)
    except OSError as error:
        raise UsageError(f"cannot read {path}: {error.strerror or error}") from None


def table_rows(check: Checker, stem: str, text: str) -> list[tc.Row]:
    """Parse the Verification table row by row, reporting every bad row rather than the first."""
    body = tc.section(text, "Verification")
    if body is None:
        return []
    table = [line for line in body.splitlines() if line.lstrip().startswith("|")]
    if not table or tc.split_cells(table[0]) != tc.HEADER:
        check.problem(f"{stem}:Verification", "Verification header must be exactly: | " + " | ".join(tc.HEADER) + " |")
        return []
    rows: list[tc.Row] = []
    seen: set[str] = set()
    for line in table[2:]:
        cells = tc.split_cells(line)
        try:
            if len(cells) != len(tc.HEADER):
                raise tc.ContractError(f"Verification row {cells[0]!r}: expected {len(tc.HEADER)} cells, found {len(cells)}")
            rows.append(tc.parse_row(cells, seen))
            if rows[-1].phase != "TIER-C" and rows[-1].expect.results:
                check.problem(f"{stem}:{cells[0]}", "results is allowed only on TIER-C rows")
        except tc.ContractError as error:
            check.problem(f"{stem}:{cells[0]}", ROW_PREFIX.sub("", str(error)))
        seen.add(cells[0])
    return rows


def check_structure(check: Checker, stem: str, path: Path, text: str, rows: list[tc.Row]) -> None:
    for title in SECTIONS:
        if tc.section(text, title) is None:
            check.problem(f"{stem}:{title}", "section is missing")
    if tc.section(text, "Files") is not None and not tc.parse_allowed_files(text):
        check.problem(f"{stem}:Files", "Allowed files lists no entry")
    if tc.section(text, "Verification") is not None:
        reason = next((m.group(1) for m in map(tc.RED_NA.match, tc.section(text, "Verification").splitlines()) if m), None)
        if not any(row.phase == "RED" for row in rows) and not (reason and reason.strip()):
            check.problem(f"{stem}:Verification", "no RED row and no RED: n/a line with a reason")
        if covers_of(path) and not any(row.phase == "TIER-C" and row.expect.results for row in rows):
            check.problem(f"{stem}:Verification", "Covers line but no TIER-C row with results")
    ids = {row.id for row in rows}
    for bullet in tc.dod_bullets(text):
        reference = tc.DOD_REFERENCE.search(bullet)
        if not reference:
            check.problem(f"{stem}:Definition of Done", f"{bullet} ends with no (V<n>) or (Gate 5) reference")
            continue
        missing = [name for name in re.findall(r"V[0-9]+", reference.group(1)) if name not in ids]
        if missing:
            check.problem(f"{stem}:Definition of Done",
                          f"{bullet} references {', '.join(missing)}, which the table lacks")


def check_allowed(check: Checker, stem: str, text: str, design: bool) -> None:
    for entry in tc.parse_allowed_files(text):
        pattern = entry.pattern
        if entry.new:
            if design:
                parent = (check.root / pattern).parent
                if (check.root / pattern).exists():
                    check.problem(f"{stem}:Files", f"{pattern} is marked (new) but already exists")
                elif not (parent.exists() or parent.parent.exists()):
                    check.problem(f"{stem}:Files", f"{pattern} (new) has no parent or grandparent directory")
        elif pattern.endswith("/") or (not GLOB_CHARS.search(pattern) and (check.root / pattern).is_dir()):
            check.problem(f"{stem}:Files", f"{pattern} is a directory; list files or a glob")
        elif GLOB_CHARS.search(pattern):
            if not check.matches_tracked(pattern):
                check.problem(f"{stem}:Files", f"{pattern} matches no tracked file")
        elif not check.is_tracked(pattern):
            check.problem(f"{stem}:Files", f"{pattern} is not tracked by git")


def command_paths(command: str) -> tuple[list[str], str | None]:
    """Path-like tokens of a command, and its executable when that is a bare name."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return [], None
    paths: list[str] = []
    for token in tokens:
        value = token.split("=", 1)[1] if token.startswith("-") and "=" in token else token
        if "/" in value and not value.startswith("-") and not re.search(r"[*$]|://", value):
            paths.append(value[2:] if value.startswith("./") else value)
    program = tc.strip_wrappers([t for t in tokens if t not in tc.CONTROL_TOKENS])
    first = program[0] if program else None
    return paths, first if first and "/" not in first else None


def check_grounding(check: Checker, stem: str, text: str, rows: list[tc.Row], created: set[str]) -> None:
    for context in tc.parse_read_only_context(text):
        if not (check.root / context).exists() and context not in created:
            check.problem(f"{stem}:Files", f"Read-only context {context} does not exist and is not (new) in any task")
    for row in rows:
        paths, executable = command_paths(row.command)
        for path in paths:
            if not (check.root / path).exists() and not check.ignored(path) and path not in created:
                check.problem(f"{stem}:{row.id}",
                              f"{path} does not exist, is not ignored by git and is not (new) in any task")
        if executable and shutil.which(executable) is None:
            check.warnings.append(f"warning: {stem}:{row.id}: executable {executable} not found on PATH")


def check_task(check: Checker, path: Path, text: str, design: bool, created: set[str]) -> None:
    stem = path.stem
    rows = table_rows(check, stem, text)
    check_structure(check, stem, path, text, rows)
    for row in rows:
        if row.expect.results and not check.ignored(row.expect.results):
            check.problem(f"{stem}:{row.id}", f"results path {row.expect.results} is not ignored by git")
    status = STATUS.search(text.split("\n---", 1)[0]) if text.startswith("---") else None
    if design or not (status and status.group(1) == "done"):
        check_allowed(check, stem, text, design)
        check_grounding(check, stem, text, rows, created)


def check_hld(check: Checker, name: str, text: str, tasks: dict[Path, str]) -> None:
    if not tc.parse_protected_paths(text):
        check.problem(name, "no Protected paths: line")
    results = tc.parse_integration_results(text)
    if not results:
        check.problem(name, "no Integration results: line")
    for entry in results:
        command, arrow, report = entry.rpartition(" -> ")
        if not arrow or not command.strip() or not report.strip():
            check.problem(name, f"Integration results line is not <command> -> <path>: {entry}")
        elif not check.ignored(report.strip()):
            check.problem(name, f"Integration results path {report.strip()} is not ignored by git")
    environment = tc.verification_environment(text)
    if environment is None or not environment.strip():
        check.problem(name, "## Verification Environment section is missing or empty")
        return
    for path, task_text in tasks.items():
        try:
            rows, _ = tc.parse_verification(task_text)
        except tc.ContractError:
            continue
        for row in rows:
            for need in row.needs:
                if need not in environment:
                    check.problem(f"{path.stem}:{row.id}", f"Needs {need} is not named in the Verification Environment section")


def repository_root() -> Path:
    done = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if done.returncode != 0:
        raise UsageError("not inside a git repository")
    return Path(done.stdout.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--design", action="store_true")
    parser.add_argument("--hld", required=True, type=Path)
    parser.add_argument("--tasks", required=True, nargs="+", type=Path)
    args = parser.parse_args(argv)
    try:
        check = Checker(repository_root())
        hld_text = read_file(args.hld)
        tasks = {path: read_file(path) for path in args.tasks}
        created = {entry.pattern for text in tasks.values() for entry in tc.parse_allowed_files(text) if entry.new}
        for path, text in tasks.items():
            check_task(check, path, text, args.design, created)
        check_hld(check, args.hld.name, hld_text, tasks)
    except UsageError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    programs = sorted({program for text in tasks.values() for row in _rows(text)
                       if (program := tc.program_of(row.command, check.root))})
    for warning in check.warnings:
        print(warning, file=sys.stderr)
    for problem in check.problems:
        print(problem)
    print(f"Implicit protected paths: {', '.join(programs) if programs else 'none'}")
    print(f"Result: {len(check.problems)} problems — {'FAIL' if check.problems else 'PASS'}")
    return 1 if check.problems else 0


def _rows(text: str) -> list[tc.Row]:
    try:
        return tc.parse_verification(text)[0]
    except tc.ContractError:
        return []


if __name__ == "__main__":
    sys.exit(main())
