#!/usr/bin/env python3
"""Parse a task file's Verification contract, and fingerprint the worktree it is checked in.

Shared by run_task_checks.py and the other scripts that read task files, so every one of them reads a
task identically. Python 3 standard library only.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

PHASES = ("RED", "GREEN", "TIER-B", "TIER-C")
HEADER = ["ID", "Phase", "Command", "Expect", "Needs"]
NONE_CELL = ("—", "-")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
EXIT_CLAUSE = re.compile(r"exit (?:(\d+)|non-zero)")
CLAUSE = re.compile(r'; (?:contains "([^"]*)"|results (\S+))')
NEEDS_NAME = re.compile(r"[A-Z_][A-Z0-9_]*")
ROW_ID = re.compile(r"V[0-9]+")
CODE_SPAN = re.compile(r"`([^`]+)`")
RED_NA = re.compile(r"^RED:\s*n/a\s*[—-]\s*(.+?)\s*$")
ALLOWED_BULLET = re.compile(r"^- `([^`]+)`( \(new\))?\s*$")
ENVIRONMENT_HEADING = re.compile(r"^## (?:\d+\.\s*)?Verification Environment\s*$")
INTERPRETERS = {"python", "python3", "bash", "sh", "zsh", "node", "deno", "ruby", "perl"}
CONTROL_TOKENS = {"&&", "||", ";", "|"}
EXCLUDE_DEVTOOL = ":(exclude).devtool"


class ContractError(Exception):
    """A task file or HLD the parser cannot accept; the message names the row or section."""


@dataclass(frozen=True)
class Expect:
    exit_code: int | None
    nonzero: bool
    contains: tuple[str, ...]
    results: str | None


@dataclass(frozen=True)
class Row:
    id: str
    phase: str
    command: str
    expect_text: str
    expect: Expect
    needs: tuple[str, ...]


@dataclass(frozen=True)
class AllowedPath:
    pattern: str
    new: bool


@dataclass(frozen=True)
class EpicLayout:
    root: Path
    epic_dir: Path
    hld: Path
    scenarios: Path
    evidence: Path


def section(text: str, title: str) -> str | None:
    """Body under `## <title>` up to the next `## ` heading; fenced lines never count as headings."""
    body: list[str] = []
    found = False
    fence: str | None = None
    for line in text.splitlines():
        marker = FENCE.match(line)
        if marker:
            if fence is None:
                fence = marker.group(1)
            elif marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                fence = None
        elif fence is None and line.startswith("## "):
            if found:
                break
            found = line[3:].strip() == title
            continue
        if found:
            body.append(line)
    return "\n".join(body) if found else None


def parse_expect(text: str) -> Expect:
    head = EXIT_CLAUSE.match(text)
    if not head:
        raise ContractError(f'Expect must start with "exit <n>" or "exit non-zero": {text!r}')
    position = head.end()
    contains: list[str] = []
    results: str | None = None
    while position < len(text):
        clause = CLAUSE.match(text, position)
        if not clause:
            raise ContractError(f"Expect has an unknown clause: {text!r}")
        if clause.group(1) is not None:
            contains.append(clause.group(1))
        elif results is not None:
            raise ContractError(f"Expect has more than one results clause: {text!r}")
        else:
            results = clause.group(2)
        position = clause.end()
    exit_code = int(head.group(1)) if head.group(1) is not None else None
    return Expect(exit_code, exit_code is None, tuple(contains), results)


def split_cells(line: str) -> list[str]:
    inner = line.strip()
    inner = inner[1:] if inner.startswith("|") else inner
    inner = inner[:-1] if inner.endswith("|") and not inner.endswith("\\|") else inner
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", inner)]


def parse_row(cells: list[str], seen: set[str]) -> Row:
    row_id = cells[0]
    if not ROW_ID.fullmatch(row_id):
        raise ContractError(f"Verification row {row_id!r}: ID must look like V1")
    if row_id in seen:
        raise ContractError(f"Verification row {row_id}: duplicate ID")
    phase, command_cell, expect_text, needs_cell = cells[1:]
    if phase not in PHASES:
        raise ContractError(f"Verification row {row_id}: Phase must be one of {', '.join(PHASES)}")
    span = CODE_SPAN.fullmatch(command_cell)
    if not span:
        raise ContractError(f"Verification row {row_id}: Command must be exactly one inline code span")
    try:
        expect = parse_expect(expect_text)
    except ContractError as error:
        raise ContractError(f"Verification row {row_id}: {error}") from None
    needs: tuple[str, ...] = ()
    if needs_cell not in NONE_CELL:
        needs = tuple(name.strip() for name in needs_cell.split(","))
        if not all(NEEDS_NAME.fullmatch(name) for name in needs):
            raise ContractError(f"Verification row {row_id}: Needs must be — or names like TEST_DATABASE_URL")
    return Row(row_id, phase, span.group(1).replace("\\|", "|"), expect_text, expect, needs)


def parse_verification(task_text: str) -> tuple[list[Row], str | None]:
    body = section(task_text, "Verification")
    if body is None:
        raise ContractError("task has no ## Verification section")
    lines = body.splitlines()
    table = [line for line in lines if line.lstrip().startswith("|")]
    if not table or split_cells(table[0]) != HEADER:
        raise ContractError("Verification header must be exactly: " + "| " + " | ".join(HEADER) + " |")
    rows: list[Row] = []
    seen: set[str] = set()
    for line in table[2:]:
        cells = split_cells(line)
        if len(cells) != len(HEADER):
            raise ContractError(f"Verification row {cells[0]!r}: expected {len(HEADER)} cells, found {len(cells)}")
        rows.append(parse_row(cells, seen))
        seen.add(rows[-1].id)
    reason = next((m.group(1) for m in map(RED_NA.match, lines) if m), None)
    return rows, reason


def parse_allowed_files(task_text: str) -> list[AllowedPath]:
    body = section(task_text, "Files") or ""
    allowed: list[AllowedPath] = []
    listing = False
    for line in body.splitlines():
        if not listing:
            listing = line.strip() == "Allowed files:"
            continue
        bullet = ALLOWED_BULLET.match(line)
        if not bullet:
            break
        allowed.append(AllowedPath(bullet.group(1), bool(bullet.group(2))))
    return allowed


def parse_protected_paths(hld_text: str) -> list[str]:
    for line in hld_text.splitlines():
        if line.startswith("Protected paths:"):
            return [entry.strip() for entry in line.split(":", 1)[1].split(",") if entry.strip()]
    return []


def parse_read_only_context(task_text: str) -> list[str]:
    """The first inline code span of each bullet under `Read-only context:` in `## Files`."""
    paths: list[str] = []
    listing = False
    for line in (section(task_text, "Files") or "").splitlines():
        if not listing:
            listing = line.strip() == "Read-only context:"
        elif line.startswith("- "):
            span = CODE_SPAN.search(line)
            if span:
                paths.append(span.group(1))
        elif line.strip():
            break
    return paths


def dod_bullets(task_text: str) -> list[str]:
    """Each `## Definition of Done` bullet as one line, wrapped continuation lines joined."""
    bullets: list[str] = []
    for line in (section(task_text, "Definition of Done") or "").splitlines():
        if line.startswith("- "):
            bullets.append(line[2:].strip())
        elif line.strip() and bullets and line[0] in " \t":
            bullets[-1] += " " + line.strip()
    return bullets


def parse_integration_results(hld_text: str) -> list[str]:
    """The text after `Integration results:` on each such line, as written."""
    return [line.split(":", 1)[1].strip() for line in hld_text.splitlines()
            if line.startswith("Integration results:")]


def verification_environment(hld_text: str) -> str | None:
    """Body of the `## Verification Environment` section, numbered or not; None when the heading is absent."""
    body: list[str] = []
    found = False
    fence: str | None = None
    for line in hld_text.splitlines():
        marker = FENCE.match(line)
        if marker:
            fence = marker.group(1) if fence is None else (None if marker.group(1)[0] == fence[0] else fence)
        elif fence is None and line.startswith("## "):
            if found:
                break
            found = bool(ENVIRONMENT_HEADING.match(line))
            continue
        if found:
            body.append(line)
    return "\n".join(body) if found else None


def path_matches(pattern: str, path: str) -> bool:
    regex, index = "", 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            regex, index = regex + "(?:.*/)?", index + 3
        elif pattern.startswith("**", index):
            regex, index = regex + ".*", index + 2
        elif pattern[index] == "*":
            regex, index = regex + "[^/]*", index + 1
        elif pattern[index] == "?":
            regex, index = regex + "[^/]", index + 1
        else:
            regex, index = regex + re.escape(pattern[index]), index + 1
    return re.fullmatch(regex, path) is not None


def git_run(root: Path, *args: str, env: dict[str, str] | None = None, stdin: bytes | None = None) -> bytes:
    done = subprocess.run(["git", *args], cwd=root, env=env, input=stdin, capture_output=True)
    if done.returncode != 0:
        raise ContractError(f"git {' '.join(args)} failed: {done.stderr.decode(errors='replace').strip()}")
    return done.stdout


def strip_wrappers(tokens: list[str]) -> list[str]:
    while tokens:
        if tokens[:2] in (["uv", "run"], ["poetry", "run"]):
            tokens = tokens[2:]
        elif tokens[0] in ("npx", "fvm"):
            tokens = tokens[1:]
        elif tokens[0] == "env":
            tokens = tokens[1:]
            while tokens and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[0]):
                tokens = tokens[1:]
        else:
            break
    return tokens


def program_of(command: str, root: Path) -> str | None:
    """The tracked file a command runs, or None when it runs something else."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return None
    for index, token in enumerate(tokens):
        if token in CONTROL_TOKENS:
            tokens = tokens[:index]
            break
    tokens = strip_wrappers(tokens)
    if not tokens:
        return None
    candidate: str | None
    if tokens[0] in INTERPRETERS:
        candidate = None
        for argument in tokens[1:]:
            if argument in ("-m", "-c"):
                break
            if not argument.startswith("-"):
                candidate = argument
                break
    else:
        candidate = tokens[0]
    if not candidate:
        return None
    candidate = candidate[2:] if candidate.startswith("./") else candidate
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", candidate], cwd=root,
                             capture_output=True).returncode == 0
    return candidate if tracked else None


def epic_layout(task_file: Path) -> EpicLayout:
    path = Path(task_file).resolve()
    try:
        top = git_run(path.parent, "rev-parse", "--show-toplevel").decode().strip()
    except (ContractError, OSError):
        raise ContractError(f"{task_file} is not inside a git repository") from None
    root = Path(top).resolve()
    parts = path.relative_to(root).parts if path.is_relative_to(root) else ()
    if not (len(parts) == 4 and parts[:2] == (".devtool", "epic") and re.fullmatch(r"task_.*\.md", parts[3])):
        raise ContractError("pass the task's mirror under .devtool/epic/<epic_dir>/")
    epic_dir = path.parent
    return EpicLayout(root, epic_dir, epic_dir / f"{epic_dir.name}.en.md",
                      epic_dir / "bdd_scenarios.en.md", epic_dir / "evidence" / f"{path.stem}.json")


def fingerprint(root: Path) -> tuple[str, str | None]:
    """Tree id and stable patch id of the worktree against HEAD, ignoring .devtool/."""
    with tempfile.TemporaryDirectory() as scratch:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(scratch) / "index")}
        git_run(root, "read-tree", "HEAD", env=env)
        git_run(root, "add", "-A", "--", ".", EXCLUDE_DEVTOOL, env=env)
        tree = git_run(root, "write-tree", env=env).decode().strip()
        diff = git_run(root, "diff", "--cached", "HEAD", "--", ".", EXCLUDE_DEVTOOL, env=env)
        patch = git_run(root, "patch-id", "--stable", stdin=diff).decode().split() if diff else []
    return tree, patch[0] if patch else None


def changed_paths(root: Path) -> list[str]:
    raw = git_run(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = raw.decode("utf-8", "surrogateescape").split("\0")
    paths: list[str] = []
    index = 0
    while index < len(entries) and entries[index]:
        status, path = entries[index][:2], entries[index][3:]
        paths.append(path)
        index += 1
        if "R" in status or "C" in status:
            paths.append(entries[index])
            index += 1
    return paths


def load_evidence(path: Path) -> dict | None:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def save_evidence(path: Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
