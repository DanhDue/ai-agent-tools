#!/usr/bin/env python3
"""Check the task files, HLD, or standalone plans against the task contract.

Usage:
  check_task_contract.py [--design] [--verbose] [--json] --hld <epic_dir>.md --tasks <task_*.md ...>
  check_task_contract.py [--verbose] [--json] --check-plan <plan.md>

Accepts `<epic_dir>.md` or legacy `<epic_dir>.en.md` for `--hld`, and resolves
`bdd_scenarios` English-only via `_epic_docs.resolve_epic_doc` (`bdd_scenarios.md`,
else legacy `bdd_scenarios.en.md`; Vietnamese `*.vi.md` mirrors are never read).
Emits a compact 1-line `Result: 0 problems — PASS` on success by default; `--verbose`
adds `Implicit protected paths: ...`; `--json` prints structured JSON; failures print
all `<task stem>:<row or section>: <problem>` or `<hld file name>: <problem>` lines,
the implicit protected paths, and the Result line. Exit codes: 0 no problem; 1 problems;
2 usage error. Python 3 standard library only.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import importlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _stack_lifecycle_registry as registry
import resolve_task_quality_plan as rtqp
from _epic_docs import resolve_epic_doc
from _stack_lifecycle_registry import TierBContractAdapter, TierCTaxonomy

tc: Any = importlib.import_module("task_contract")
cb: Any = importlib.import_module("check_bdd_traceability")
sts: Any = importlib.import_module("sync_task_status")
ceo: Any = importlib.import_module("compute_execution_order")
UsageError: type[Exception] = cb.UsageError
covers_of: Any = cb.covers_of
read_text: Any = cb.read_text

SECTIONS = (
    "Files",
    "Verification",
    "Definition of Done",
    "Stop and Report If",
    "Decisions Already Made",
)
ROW_PREFIX = re.compile(r"^Verification row [^:]+: ")
STATUS = re.compile(r'^status:\s*"?([A-Za-z_-]+)"?\s*$', re.MULTILINE)
GLOB_CHARS = re.compile(r"[*?\[]")
WEAK_ASSERTION_RE = re.compile(
    r"\b(should be truthy|is valid|should work|returns non-empty)\b", re.IGNORECASE
)
RESERVED_RUNNER_EVIDENCE = re.compile(r"^task_.*\.json$")
NON_PORTABLE_PATH_RE = re.compile(
    r"(?:/Users/|/home/|~/|\.claude/plugins/cache/|\.gemini/config/plugins/)"
)
SURGICAL_LINE_THRESHOLD = 200
LOCKFILE_NAMES = frozenset(
    {"uv.lock", "package-lock.json", "pubspec.lock", "Cargo.lock", "Podfile.lock"}
)
ANCHOR_SECTIONS = frozenset(
    {
        "files",
        "impact analysis & blast radius",
        "impact analysis and blast radius",
        "impact analysis",
        "impact & design",
        "decisions already made",
        "file anchor map",
    }
)
LINE_RANGE_RE = re.compile(r"\bL(\d+)\s*[-–:]\s*L?(\d+)\b")
NON_SYMBOL_WORDS = frozenset(
    {
        "new",
        "add",
        "update",
        "modify",
        "edit",
        "fix",
        "remove",
        "delete",
        "file",
        "files",
        "line",
        "lines",
        "section",
        "sections",
        "module",
        "test",
        "tests",
        "general",
        "todo",
        "done",
        "none",
    }
)


class Checker:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.problems: list[str] = []
        self.warnings: list[str] = []
        proc = subprocess.run(
            ["git", "ls-files", "-z"],
            check=False,
            cwd=root,
            capture_output=True,
            text=True,
        )
        self.in_git_repo = proc.returncode == 0
        self.tracked = set(proc.stdout.split("\0")) - {""}

    def ignored(self, path: str) -> bool:
        return (
            subprocess.run(
                ["git", "check-ignore", "-q", "--", path],
                check=False,
                cwd=self.root,
                capture_output=True,
            ).returncode
            == 0
        )

    def problem(self, where: str, text: str) -> None:
        self.problems.append(f"{where}: {text}")

    def is_tracked(self, path: str) -> bool:
        return path in self.tracked

    def matches_tracked(self, pattern: str) -> bool:
        return any(_glob_matches(pattern, name) for name in self.tracked)


def read_file(path: Path) -> str:
    try:
        return str(read_text(path))
    except OSError as error:
        raise UsageError(f"cannot read {path}: {error.strerror or error}") from None


def table_rows(check: Checker, stem: str, text: str) -> list[Any]:
    """Parse the Verification table row by row, reporting every bad row rather than the first."""
    body = tc.section(text, "Verification")
    if body is None:
        return []
    table = [line for line in body.splitlines() if line.lstrip().startswith("|")]
    if not table or tc.split_cells(table[0]) != tc.HEADER:
        check.problem(
            f"{stem}:Verification",
            "Verification header must be exactly: | " + " | ".join(tc.HEADER) + " |",
        )
        return []
    rows: list[Any] = []
    seen: set[str] = set()
    for line in table[2:]:
        cells = tc.split_cells(line)
        try:
            if len(cells) != len(tc.HEADER):
                raise tc.ContractError(
                    f"Verification row {cells[0]!r}: expected {len(tc.HEADER)} cells, found {len(cells)}"
                )
            rows.append(tc.parse_row(cells, seen))
            if rows[-1].phase != "TIER-C" and rows[-1].expect.results:
                check.problem(
                    f"{stem}:{cells[0]}", "results is allowed only on TIER-C rows"
                )
        except tc.ContractError as error:
            check.problem(f"{stem}:{cells[0]}", ROW_PREFIX.sub("", str(error)))
        seen.add(cells[0])
    return rows


def check_structure(
    check: Checker,
    stem: str,
    path: Path,
    text: str,
    rows: list[Any],
    *,
    design: bool = False,
    allow_historical: bool = False,
) -> None:
    for title in SECTIONS:
        if tc.section(text, title) is None:
            check.problem(f"{stem}:{title}", "section is missing")
    if tc.section(text, "Files") is not None and not tc.parse_allowed_files(text):
        check.problem(f"{stem}:Files", "Allowed files lists no entry")
    v_sec = tc.section(text, "Verification")
    if v_sec is not None:
        reason = next(
            (m.group(1) for m in map(tc.RED_NA.match, v_sec.splitlines()) if m), None
        )
        if not any(row.phase == "RED" for row in rows) and not (
            reason and reason.strip()
        ):
            check.problem(
                f"{stem}:Verification", "no RED row and no RED: n/a line with a reason"
            )
        if covers_of(path) and not any(
            row.phase == "TIER-C" and row.expect.results for row in rows
        ):
            check.problem(
                f"{stem}:Verification", "Covers line but no TIER-C row with results"
            )
    ids = {row.id for row in rows}
    task_status = _task_status(text)
    require_checkbox = (
        design
        and not allow_historical
        and task_status not in EXISTING_NEW_EXEMPT_STATUSES
    )
    for bullet in tc.dod_bullets(text):
        if require_checkbox and not (
            tc.UNCHECKED_DOD_PREFIX.match(bullet) or tc.CHECKED_DOD_PREFIX.match(bullet)
        ):
            check.problem(
                f"{stem}:Definition of Done",
                f"{bullet} must start with a '- [ ]' (or '- [x]') checkbox",
            )
        reference = tc.DOD_REFERENCE.search(bullet)
        if not reference:
            check.problem(
                f"{stem}:Definition of Done",
                f"{bullet} ends with no (V<n>) or (Gate 5) reference",
            )
            continue
        missing = [
            name
            for name in re.findall(r"V[0-9]+", reference.group(1))
            if name not in ids
        ]
        if missing:
            check.problem(
                f"{stem}:Definition of Done",
                f"{bullet} references {', '.join(missing)}, which the table lacks",
            )
    if (
        task_status == "done" or tc.has_completed_at(text)
    ) and tc.unchecked_dod_bullets(text):
        check.problem(
            f"{stem}:Definition of Done",
            "task status is 'done' (or completedAt is set) while Definition of Done still contains unchecked '- [ ]' item(s)",
        )
    has_executable = any(row.phase in ("RED", "GREEN", "REGRESSION") for row in rows)
    if has_executable:
        decisions = tc.section(text, "Decisions Already Made")
        clean_decisions = decisions.strip().lower() if decisions else ""
        if (
            not decisions
            or not clean_decisions
            or clean_decisions in ("none", "none.", "n/a")
        ):
            check.problem(
                f"{stem}:Decisions Already Made",
                "executable task requires grounded facts, cannot be empty or 'None'",
            )


EXISTING_NEW_EXEMPT_STATUSES = frozenset({"done", "review", "in-progress"})


def _task_status(text: str) -> str:
    if not text.startswith("---"):
        return ""
    match = STATUS.search(text.split("\n---", 1)[0])
    return match.group(1).strip() if match else ""


def check_allowed(
    check: Checker,
    stem: str,
    text: str,
    design: bool,
    prereq_files: set[str] | None = None,
    *,
    allow_existing_done_new: bool = False,
    task_status: str = "",
) -> None:
    skip_existing = (
        allow_existing_done_new and task_status in EXISTING_NEW_EXEMPT_STATUSES
    )
    for entry in tc.parse_allowed_files(text):
        pattern = entry.pattern
        if entry.new:
            if design:
                parent = (check.root / pattern).parent
                if (check.root / pattern).exists():
                    if not skip_existing:
                        check.problem(
                            f"{stem}:Files",
                            f"{pattern} is marked (new) but already exists",
                        )
                elif not (parent.exists() or parent.parent.exists()):
                    check.problem(
                        f"{stem}:Files",
                        f"{pattern} (new) has no parent or grandparent directory",
                    )
        elif prereq_files and any(
            tc.path_matches(p, pattern) or tc.path_matches(pattern, p)
            for p in prereq_files
        ):
            pass
        elif pattern.endswith("/") or (
            not check.is_tracked(pattern)
            and not GLOB_CHARS.search(pattern)
            and (check.root / pattern).is_dir()
        ):
            check.problem(
                f"{stem}:Files", f"{pattern} is a directory; list files or a glob"
            )
        elif not check.is_tracked(pattern) and GLOB_CHARS.search(pattern):
            if not check.matches_tracked(pattern):
                check.problem(f"{stem}:Files", f"{pattern} matches no tracked file")
        elif not check.is_tracked(pattern):
            check.problem(f"{stem}:Files", f"{pattern} is not tracked by git")


def check_evidence(
    check: Checker,
    stem: str,
    text: str,
    design: bool,
    *,
    allow_existing_done_new: bool = False,
    task_status: str = "",
) -> None:
    skip_existing = (
        allow_existing_done_new and task_status in EXISTING_NEW_EXEMPT_STATUSES
    )
    for entry in tc.parse_evidence_files(text):
        pattern = entry.pattern
        parts = Path(pattern).parts
        if (
            pattern.endswith("/")
            or ".." in parts
            or not tc.EVIDENCE_FILE_RE.match(pattern)
        ):
            check.problem(
                f"{stem}:Files",
                f"Evidence file {pattern} must reside under .devtool/epic/<epic_dir>/evidence/ without '..' segments",
            )
            continue
        if RESERVED_RUNNER_EVIDENCE.match(Path(pattern).name):
            check.problem(
                f"{stem}:Files",
                f"Evidence file {pattern} collides with reserved 'task_*.json' runner records",
            )
            continue
        if (
            design
            and entry.new
            and (check.root / pattern).exists()
            and not skip_existing
        ):
            check.problem(
                f"{stem}:Files",
                f"Evidence file {pattern} is marked (new) but already exists",
            )


def _normalize_rel_claim(pattern: str) -> str:
    """Normalize a relative claim path without corrupting leading dot-directories."""
    norm = Path(pattern).as_posix()
    while norm.startswith("./"):
        norm = norm[2:]
    return norm


def _normalize_ownership_path(raw: str) -> str:
    """Normalize an Allowed files entry by stripping annotations, symbols, backticks, and leading ./."""
    item = raw.strip()
    if item.startswith("`"):
        m = re.match(r"^`([^`]+)`", item)
        candidate = m.group(1) if m else item.replace("`", "")
    else:
        candidate = item.replace("`", "")
    candidate = re.split(
        r"\s+(?:::|—|–|-)\s+|:(?:\s+|(?=L\d+))", candidate, maxsplit=1
    )[0]
    candidate = re.sub(r"\s*\([^)]*\)\s*", " ", candidate).strip()
    candidate = candidate.replace("`", "").strip()
    if candidate:
        candidate = candidate.split()[0]
    while candidate.startswith("./"):
        candidate = candidate[2:]
    return candidate


def _allowed_ownership_paths(text: str) -> list[str]:
    body = tc.section(text, "Files") or ""
    paths: list[str] = []
    listing = False
    for line in body.splitlines():
        stripped = line.strip()
        if not listing:
            listing = stripped == "Allowed files:"
            continue
        if stripped.startswith(("- ", "* ")):
            norm = _normalize_ownership_path(stripped[2:])
            if norm and norm not in paths:
                paths.append(norm)
        elif stripped:
            break
    return paths


def _task_id_map(tasks: dict[Path, str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for path, text in tasks.items():
        stem = path.stem
        mapping[stem] = stem
        if text.startswith("---"):
            fm = text.split("\n---", 1)[0]
            m = re.search(r'^id:\s*"?([^"\n]+)"?', fm, re.MULTILINE)
            if m:
                mapping.setdefault(m.group(1).strip(), stem)
    return mapping


def _glob_matches(pattern: str, path: str) -> bool:
    """Match a POSIX path against an fnmatch-style glob respecting '/' boundaries.

    '*', '?', and '[...]' (fnmatch '[!...]' negation) match within one path segment and
    never cross '/'. A standalone '**' segment matches zero or more path segments,
    except a trailing '/**' requires at least one child segment.
    """
    if pattern.endswith("/"):
        pattern = pattern + "**"
    pat_parts = pattern.split("/")
    path_parts = path.split("/")
    trailing_double_star = len(pat_parts) > 1 and pat_parts[-1] == "**"

    @cache
    def _match(pi: int, si: int) -> bool:
        if pi == len(pat_parts):
            return si == len(path_parts)
        seg = pat_parts[pi]
        if seg == "**":
            if pi == len(pat_parts) - 1:
                return si < len(path_parts) if trailing_double_star else True
            return _match(pi + 1, si) or (si < len(path_parts) and _match(pi, si + 1))
        if si >= len(path_parts) or not fnmatch.fnmatchcase(path_parts[si], seg):
            return False
        return _match(pi + 1, si + 1)

    return _match(0, 0)


def _ownership_repo_files(check: Checker) -> set[str]:
    """Return repo-relative POSIX paths from git ls-files, or by walking root outside git."""
    in_git = getattr(check, "in_git_repo", None)
    if in_git is True:
        return set(check.tracked)
    if in_git is None:
        if check.tracked:
            return set(check.tracked)
        probe = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=False,
            cwd=check.root,
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            return set(check.tracked)
    files: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(check.root):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        for fname in sorted(filenames):
            files.add((Path(dirpath) / fname).relative_to(check.root).as_posix())
    return files


def _classify_ownership_entry(check: Checker, entry: str, repo_files: set[str]) -> str:
    """Classify a normalized ownership entry as 'glob', 'dir', or 'literal'."""
    if entry not in repo_files and GLOB_CHARS.search(entry):
        return "glob"
    if entry.endswith("/") or (check.root / entry).is_dir():
        return "dir"
    return "literal"


def _expand_ownership_entry(entry: str, kind: str, universe: list[str]) -> set[str]:
    """Expand a glob or directory entry against the sorted universe; literals keep {entry}."""
    if kind == "literal":
        return {entry}
    if kind == "dir":
        prefix = "" if entry in (".", "./") else entry.rstrip("/") + "/"
        return {p for p in universe if p.startswith(prefix)}
    return {p for p in universe if _glob_matches(entry, p)}


def _blocked_ancestors(
    tasks: dict[Path, str], ordered_paths: list[Path]
) -> dict[str, set[str]]:
    """Build transitive Blocked-by ancestor map keyed by task stem."""
    id_map = _task_id_map(tasks)
    direct_blockers: dict[str, set[str]] = {}
    for path in ordered_paths:
        dep_section = ceo.parse_dependencies_section(tasks[path])
        blockers = ceo.parse_blockers(dep_section)
        direct_blockers[path.stem] = {id_map.get(b, b) for b in blockers}
    ancestors: dict[str, set[str]] = {}
    for stem, blockers_set in direct_blockers.items():
        seen: set[str] = set()
        stack = list(blockers_set)
        while stack:
            cur = stack.pop()
            if cur in seen or cur == stem:
                continue
            seen.add(cur)
            stack.extend(direct_blockers.get(cur, ()))
        ancestors[stem] = seen
    return ancestors


def _emit_pair_ownership_problems(
    check: Checker,
    task_a: str,
    entries_a: list[tuple[str, str, set[str]]],
    task_b: str,
    entries_b: list[tuple[str, str, set[str]]],
) -> None:
    """Report R-OWN for overlapping literal or expanded entries between two parallel tasks."""
    literal_shared: list[str] = []
    expanded_conflicts: list[tuple[str, str, str]] = []
    for entry_a, kind_a, set_a in entries_a:
        for entry_b, kind_b, set_b in entries_b:
            if kind_a == "literal" and kind_b == "literal":
                if entry_a == entry_b and entry_a not in literal_shared:
                    literal_shared.append(entry_a)
                continue
            overlap = sorted(set_a & set_b)
            if overlap:
                expanded_conflicts.append((entry_a, entry_b, overlap[0]))
    if literal_shared:
        check.problem(
            f"{task_a}:Ownership",
            f"R-OWN {task_a} and {task_b} both own {', '.join(literal_shared)} with no Blocked by path between them",
        )
    for entry_a, entry_b, shared_path in expanded_conflicts:
        check.problem(
            f"{task_a}:Ownership",
            f"R-OWN {task_a} and {task_b} both own {shared_path} (via {entry_a} and {entry_b}) with no Blocked by path between them",
        )


def check_exclusive_ownership(check: Checker, tasks: dict[Path, str]) -> None:
    """Fail with R-OWN when parallel tasks without a Blocked by path claim overlapping Allowed files.

    Globs ('*', '?', '[') and directories (trailing '/' or existing repository directory)
    expand deterministically against tracked files (or walked tree outside git) plus every
    literal entry of every task. Matching respects '/' boundaries ('*' does not cross '/';
    standalone '**' segments match zero or more segments).
    """
    ordered_paths = sorted(tasks.keys(), key=lambda p: p.stem)
    ancestors = _blocked_ancestors(tasks, ordered_paths)
    repo_files = _ownership_repo_files(check)
    raw_entries = {
        path.stem: _allowed_ownership_paths(tasks[path]) for path in ordered_paths
    }
    classified = {
        stem: [
            (entry, _classify_ownership_entry(check, entry, repo_files))
            for entry in entries
        ]
        for stem, entries in raw_entries.items()
    }
    all_literals = {
        entry
        for items in classified.values()
        for entry, kind in items
        if kind == "literal"
    }
    universe = sorted(repo_files | all_literals)
    expanded = {
        stem: [
            (entry, kind, _expand_ownership_entry(entry, kind, universe))
            for entry, kind in items
        ]
        for stem, items in classified.items()
    }
    stems = [p.stem for p in ordered_paths]
    for idx, task_a in enumerate(stems):
        for task_b in stems[idx + 1 :]:
            if task_b in ancestors[task_a] or task_a in ancestors[task_b]:
                continue
            _emit_pair_ownership_problems(
                check, task_a, expanded[task_a], task_b, expanded[task_b]
            )


def check_duplicate_new_claims(check: Checker, tasks: dict[Path, str]) -> None:
    """Reject duplicate (new) Allowed or Evidence path claims across multiple tasks."""
    new_owners: dict[str, list[str]] = {}
    for path, text in tasks.items():
        stem = path.stem
        for entry in tc.parse_allowed_files(text):
            if entry.new:
                norm = _normalize_rel_claim(entry.pattern)
                owners = new_owners.setdefault(norm, [])
                if stem not in owners:
                    owners.append(stem)
        for entry in tc.parse_evidence_files(text):
            if entry.new and not Path(entry.pattern).name.startswith("task_"):
                norm = _normalize_rel_claim(entry.pattern)
                owners = new_owners.setdefault(norm, [])
                if stem not in owners:
                    owners.append(stem)
    for pattern, owners in sorted(new_owners.items()):
        if len(owners) > 1:
            check.problem(
                f"{owners[0]}:Files",
                f"duplicate (new) claim for {pattern} across multiple tasks ({', '.join(owners)})",
            )


SEARCH_PROGRAMS = {"grep", "egrep", "fgrep", "rg", "sed", "awk"}


def _split_subcommands(tokens: list[str]) -> list[list[str]]:
    subcommands: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in tc.CONTROL_TOKENS:
            if current:
                subcommands.append(current)
                current = []
        else:
            current.append(token)
    if current:
        subcommands.append(current)
    return subcommands


def command_paths(command: str) -> tuple[list[str], str | None]:
    """Path-like tokens of a command, and its executable when that is a bare name."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return [], None
    paths: list[str] = []
    subcommands = _split_subcommands(tokens)

    for sub_tokens in subcommands:
        unwrapped = tc.strip_wrappers(list(sub_tokens))
        prog = Path(unwrapped[0]).name if unwrapped else ""

        tokens_to_scan = list(sub_tokens)
        if prog in SEARCH_PROGRAMS and len(unwrapped) > 1:
            pattern_idx: int | None = None
            for idx, tok in enumerate(sub_tokens):
                if tok in ("-e", "--regexp") and idx + 1 < len(sub_tokens):
                    pattern_idx = idx + 1
                    break
            if pattern_idx is None:
                has_f = any(tok in ("-f", "--file") for tok in sub_tokens)
                if not has_f:
                    prog_idx = (
                        sub_tokens.index(unwrapped[0])
                        if unwrapped[0] in sub_tokens
                        else 0
                    )
                    for idx in range(prog_idx + 1, len(sub_tokens)):
                        tok = sub_tokens[idx]
                        if not tok.startswith("-"):
                            pattern_idx = idx
                            break
            if pattern_idx is not None:
                tokens_to_scan = [
                    t for i, t in enumerate(sub_tokens) if i != pattern_idx
                ]

        for token in tokens_to_scan:
            value = (
                token.split("=", 1)[1]
                if token.startswith("-") and "=" in token
                else token
            )
            if (
                "/" in value
                and not value.startswith("-")
                and not re.search(r"[*$]|://", value)
            ):
                clean_path = value.split("::", 1)[0]
                paths.append(clean_path.removeprefix("./"))

    program = tc.strip_wrappers([t for t in tokens if t not in tc.CONTROL_TOKENS])
    first = program[0] if program else None
    return paths, first if first and "/" not in first else None


def check_grounding(
    check: Checker,
    stem: str,
    text: str,
    rows: list[Any],
    created: set[str],
    *,
    skip_placeholder_paths: bool = False,
) -> None:
    for context in tc.parse_read_only_context(text):
        if not (check.root / context).exists() and not any(
            tc.path_matches(p, context) or tc.path_matches(context, p) for p in created
        ):
            check.problem(
                f"{stem}:Files",
                f"Read-only context {context} does not exist and is not (new) in any task",
            )
    for row in rows:
        try:
            lexer = shlex.shlex(row.command, posix=True, punctuation_chars=True)
            lexer.whitespace_split = True
            cmd_tokens = list(lexer)
        except ValueError:
            cmd_tokens = []
        for sub in _split_subcommands(cmd_tokens):
            if sub and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=.*", sub[0]):
                check.problem(
                    f"{stem}:{row.id}",
                    f"inline environment assignment '{sub[0]}' must be prefixed with 'env' (e.g. 'env {sub[0]} ...')",
                )
        paths, executable = command_paths(row.command)
        for path in paths:
            if skip_placeholder_paths and (
                "{skills_dir}" in path or "{base_ref}" in path
            ):
                continue
            if (
                not (check.root / path).exists()
                and not check.ignored(path)
                and path not in created
            ):
                check.problem(
                    f"{stem}:{row.id}",
                    f"{path} does not exist, is not ignored by git and is not (new) in any task",
                )
        if (
            executable
            and executable != "d3nexus"
            and "=" not in executable
            and shutil.which(executable) is None
        ):
            check.warnings.append(
                f"warning: {stem}:{row.id}: executable {executable} not found on PATH"
            )


def check_portable_command(check: Checker, stem: str, row: Any) -> None:
    m = NON_PORTABLE_PATH_RE.search(row.command)
    if m:
        check.problem(
            f"{stem}:{row.id}",
            f"non-portable path '{m.group(0)}' in command; use 'd3nexus <subcommand>' or '$D3NEXUS_KIT/...'",
        )


def check_pytest_k(check: Checker, stem: str, row: Any) -> None:
    try:
        tokens = shlex.split(row.command)
    except ValueError:
        tokens = row.command.split()
    program = tc.strip_wrappers([t for t in tokens if t not in tc.CONTROL_TOKENS])
    if not program or "pytest" not in program[0]:
        return
    for i, token in enumerate(tokens):
        val: str | None = None
        if token == "-k" and i + 1 < len(tokens):
            val = tokens[i + 1]
        elif token.startswith("-k="):
            val = token.split("=", 1)[1]
        elif token.startswith("-k") and len(token) > 2:
            val = token[2:]
        if val is not None and (
            "::" not in val or not val.split("::", 1)[0].endswith(".py")
        ):
            check.problem(
                f"{stem}:{row.id}",
                f"pytest -k expression must use an exact node ID (<file>::<test>), found: {val!r}",
            )


def is_python_task(text: str, rows: list[Any]) -> bool:
    entries = tc.parse_allowed_files(text)
    for entry in entries:
        pat = entry.pattern.lower()
        if pat.endswith(".py") or pat in (
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "pipfile",
        ):
            return True
    tier_b_rows = [r for r in rows if r.phase == "TIER-B"]
    for row in tier_b_rows:
        try:
            tokens = shlex.split(row.command)
        except ValueError:
            tokens = row.command.split()
        if "ruff" in tokens or any("ruff" in t for t in tokens):
            return True
    return False


_PY_TOOL_NAMES = frozenset({"ruff", "mypy", "pyright", "ty", "flake8", "pylint"})
_PY_WRAPPER_VALUE_FLAGS = frozenset(
    {
        "--directory",
        "--project",
        "--python",
        "--config-file",
        "--cache-dir",
        "-C",
        "--extra",
        "--group",
        "--with",
        "-p",
        "--package",
        "-u",
        "--unset",
        "-S",
        "--split-string",
    }
)
_PY_CAP_VALUE_FLAGS = frozenset(
    {
        "--extend-select",
        "--select",
        "--ignore",
        "--extend-ignore",
        "--per-file-ignores",
        "--config",
        "--config-file",
        "-c",
        "--target-version",
        "--line-length",
        "--python-version",
        "--pyproject-toml",
        "--exclude",
        "--extend-exclude",
        "--output-format",
        "--format",
        "--cache-dir",
        "--follow-imports",
        "--python-executable",
        "--python-platform",
        "--package",
        "--module",
        "-m",
        "--custom-typeshed-dir",
        "--venvpath",
        "--typeshedpath",
    }
)


def _cap_tool_prefix(cap: Sequence[str]) -> list[str]:
    """Return runner wrappers, Python tool binary, subcommand, and flags before positional targets."""
    idx = 0
    while idx < len(cap):
        tok = cap[idx]
        if tok in _PY_WRAPPER_VALUE_FLAGS and idx + 1 < len(cap):
            idx += 2
            continue
        tool = Path(tok).name
        if tool not in _PY_TOOL_NAMES:
            idx += 1
            continue
        end = idx + 1
        if (tool == "ruff" and end < len(cap) and cap[end] in ("check", "format")) or (
            tool == "ty" and end < len(cap) and cap[end] == "check"
        ):
            end += 1
        while end < len(cap):
            cur = cap[end]
            if cur == "--":
                break
            if cur in _PY_CAP_VALUE_FLAGS:
                end += 2 if end + 1 < len(cap) else 1
                continue
            if cur.startswith("-"):
                end += 1
                continue
            break
        return list(cap[:end])
    return list(cap[:-1]) if len(cap) > 1 else list(cap)


def _extract_py_positional_targets(tail: Sequence[str]) -> list[str]:
    """Extract non-flag positional path arguments from Python tool arguments."""
    targets: list[str] = []
    idx = 0
    in_positional = False
    while idx < len(tail):
        tok = tail[idx]
        if in_positional:
            targets.append(tok)
            idx += 1
            continue
        if tok == "--":
            in_positional = True
            idx += 1
            continue
        if tok in _PY_CAP_VALUE_FLAGS:
            idx += 2
            continue
        if tok.startswith("-"):
            idx += 1
            continue
        targets.append(tok)
        idx += 1
    return targets


def _resolve_target_with_wrapper_dir(target: str, wrapper_dir: str | None) -> str:
    clean = target.strip().replace("\\", "/").removeprefix("./").rstrip("/")
    if not wrapper_dir:
        return clean or "."
    if clean in ("", "."):
        return wrapper_dir
    if clean == wrapper_dir or clean.startswith(wrapper_dir + "/"):
        return clean
    return f"{wrapper_dir}/{clean}"


def _is_test_path(path: str) -> bool:
    norm = path.strip().strip("`").removeprefix("./")
    parts = Path(norm).parts
    name = Path(norm).name.lower()
    return (
        "tests" in parts
        or "test" in parts
        or "integration_test" in parts
        or name.startswith("test_")
        or name.endswith(
            (
                "_test.py",
                "_test.dart",
                "_test.go",
                "_test.rs",
                ".test.ts",
                ".spec.ts",
                ".test.js",
                ".spec.js",
                "test.kt",
                "tests.swift",
            )
        )
    )


def _target_covers_path(target_tok: str, file_path: str) -> bool:
    clean_tok = target_tok.split("::", 1)[0].strip().removeprefix("./").rstrip("/")
    clean_file = file_path.strip().removeprefix("./")
    if not clean_tok or clean_tok.startswith("-"):
        return False
    if clean_tok in (".", clean_file):
        return True
    if GLOB_CHARS.search(clean_tok) and _glob_matches(clean_tok, clean_file):
        return True
    return clean_file.startswith(clean_tok + "/")


def _extract_downstream_caller_tests(text: str) -> list[str]:
    impact_body: str | None = None
    for heading in (
        "Impact Analysis & Blast Radius",
        "Impact Analysis and Blast Radius",
        "Impact analysis & blast radius",
        "Impact Analysis",
    ):
        impact_body = tc.section(text, heading)
        if impact_body:
            break
    if not impact_body:
        return []
    caller_header = re.compile(
        r"^\s*(?:(?:[-*]|\d+[.)])\s*)?(?:#{3,6}\s*)?\*{0,2}Downstream Callers\*{0,2}\s*:?\s*(.*)$",
        re.IGNORECASE,
    )
    in_callers = False
    caller_chunks: list[str] = []
    for line in impact_body.splitlines():
        m = caller_header.match(line)
        if m:
            in_callers = True
            caller_chunks.append(m.group(1))
            continue
        if in_callers:
            if (
                re.match(r"^\s*#{2,6}\s+", line)
                or re.match(r"^\s*(?:[-*]|\d+[.)])\s+\*\*", line)
                or (
                    line.startswith(("- ", "* "))
                    and not line.startswith(("  - ", "  * "))
                )
            ):
                break
            caller_chunks.append(line)
    caller_tests: list[str] = []
    for chunk in caller_chunks:
        for span in tc.CODE_SPAN.findall(chunk):
            cand = span.split("::", 1)[0].strip().removeprefix("./")
            if (
                cand
                and not GLOB_CHARS.search(cand)
                and _is_test_path(cand)
                and cand not in caller_tests
            ):
                caller_tests.append(cand)
    return caller_tests


def _caller_test_exists(check: Checker, caller_test: str) -> bool:
    if (check.root / caller_test).exists() or check.is_tracked(caller_test):
        return True
    if "/" not in caller_test:
        return any(Path(t).name == caller_test for t in check.tracked)
    return False


def _token_covers_caller_test(tok: str, caller_test: str) -> bool:
    if _target_covers_path(tok, caller_test):
        return True
    if "/" not in caller_test:
        clean_tok = tok.split("::", 1)[0].strip().removeprefix("./").rstrip("/")
        return Path(clean_tok).name == caller_test
    return False


def check_regression_coverage(
    check: Checker, stem: str, text: str, rows: list[Any]
) -> None:
    """Enforce regression coverage for touched modules and Downstream Callers in Verification."""
    test_rows = [r for r in rows if r.phase in ("GREEN", "REGRESSION", "TIER-C")]
    if not test_rows:
        return

    row_tokens: list[str] = []
    for r in test_rows:
        try:
            toks = shlex.split(r.command)
        except ValueError:
            toks = r.command.split()
        for tok in toks:
            val = tok.split("=", 1)[1] if tok.startswith("-") and "=" in tok else tok
            row_tokens.append(val)

    # 1. Every test file explicitly listed under Downstream Callers must be executed
    for caller_test in _extract_downstream_caller_tests(text):
        if _caller_test_exists(check, caller_test):
            if not any(
                _token_covers_caller_test(tok, caller_test) for tok in row_tokens
            ):
                check.problem(
                    f"{stem}:Verification",
                    f"Downstream caller test {caller_test} listed in Impact Analysis is not executed in any REGRESSION, GREEN, or TIER-C row",
                )

    # 2. Forbid running ONLY newly created unit test files when existing non-test modules are modified
    allowed = tc.parse_allowed_files(text)
    modifies_existing_prod = any(
        not entry.new and not _is_test_path(entry.pattern) for entry in allowed
    )
    new_test_files = {
        entry.pattern.removeprefix("./")
        for entry in allowed
        if entry.new and _is_test_path(entry.pattern)
    }
    if not modifies_existing_prod or not new_test_files:
        return

    has_regression_phase = any(r.phase == "REGRESSION" for r in rows)
    referenced_test_targets: list[str] = []
    for r in test_rows:
        paths, _ = command_paths(r.command)
        for p in paths:
            if p == (r.expect.results or ""):
                continue
            if _is_test_path(p):
                referenced_test_targets.append(p)
        try:
            toks = shlex.split(r.command)
        except ValueError:
            toks = r.command.split()
        for tok in toks:
            clean = tok.split("::", 1)[0].strip().removeprefix("./").rstrip("/")
            if clean in ("tests", "test", "integration_test") or (
                _is_test_path(clean) and clean not in referenced_test_targets
            ):
                referenced_test_targets.append(clean)

    if (
        referenced_test_targets
        and all(t in new_test_files for t in referenced_test_targets)
        and not has_regression_phase
    ):
        check.problem(
            f"{stem}:Verification",
            "Verification only runs newly created test file(s); add a REGRESSION row (or expand GREEN/TIER-C) covering existing module and Downstream Caller tests",
        )


_SEQUENTIAL_CHAIN_TOKENS = frozenset({"&&", ";"})
_CONDITIONAL_OR_PIPE_TOKENS = frozenset({"||", "|"})


def _split_sequential_subcommands(command: str) -> list[list[str]]:
    """Split a shell command into unconditionally sequenced subcommands (`&&` / `;`).

    Subcommands following `||` (failure-only fallback) or `|` (pipe consumer) are
    excluded until the next `&&` or `;` so conditional/piped tails cannot satisfy
    required static verification gates.
    """
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()

    subcommands: list[list[str]] = []
    current: list[str] = []
    skip_until_seq = False
    for token in tokens:
        if token in _SEQUENTIAL_CHAIN_TOKENS:
            if current and not skip_until_seq:
                subcommands.append(current)
            current = []
            skip_until_seq = False
        elif token in _CONDITIONAL_OR_PIPE_TOKENS:
            if current and not skip_until_seq:
                subcommands.append(current)
            current = []
            skip_until_seq = True
        elif not skip_until_seq:
            current.append(token)
    if current and not skip_until_seq:
        subcommands.append(current)
    return subcommands


@dataclass(frozen=True)
class _AllowedPyEntry:
    pattern: str
    root: str
    kind: str  # "glob" or "dir"


def _glob_static_root(pattern: str) -> str:
    norm = pattern.strip().replace("\\", "/").removeprefix("./").rstrip("/")
    if not norm:
        return "."
    parts: list[str] = []
    for seg in norm.split("/"):
        if GLOB_CHARS.search(seg):
            break
        parts.append(seg)
    return "/".join(parts) if parts else "."


def _dir_contains_python(
    repo_root: Path | None,
    rel_dir: str,
    raw_pattern: str = "",
) -> bool:
    pattern_is_py = raw_pattern.strip().lower().endswith(".py")
    if repo_root is None:
        return pattern_is_py
    target = repo_root if rel_dir in ("", ".") else repo_root / rel_dir
    if not target.is_dir():
        return pattern_is_py
    for _, dirnames, filenames in os.walk(target):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in (".git", "__pycache__", ".venv", "venv", "node_modules")
        ]
        for fname in filenames:
            if fname.lower().endswith(".py"):
                return True
    return pattern_is_py


def _collect_allowed_py_entries(
    entries: Sequence[Any], repo_root: Path | None = None
) -> tuple[list[str], list[_AllowedPyEntry]]:
    """Return concrete allowed `.py` paths plus glob/directory Python coverage roots."""
    concrete: list[str] = []
    globs_and_dirs: list[_AllowedPyEntry] = []
    seen_roots: set[tuple[str, str]] = set()
    for entry in entries:
        raw = (
            str(getattr(entry, "pattern", entry))
            .strip()
            .replace("\\", "/")
            .removeprefix("./")
        )
        if not raw:
            continue
        if GLOB_CHARS.search(raw):
            suffix = Path(raw).suffix.lower()
            if raw.lower().endswith(".py") or (
                not suffix
                and _dir_contains_python(repo_root, _glob_static_root(raw), raw)
            ):
                root = _glob_static_root(raw)
                key = (raw, "glob")
                if key not in seen_roots:
                    seen_roots.add(key)
                    globs_and_dirs.append(
                        _AllowedPyEntry(pattern=raw, root=root, kind="glob")
                    )
            continue
        if raw.lower().endswith(".py"):
            if raw not in concrete:
                concrete.append(raw)
            continue
        norm_dir = raw.rstrip("/")
        is_dir = raw.endswith("/") or (
            repo_root is not None and bool(norm_dir) and (repo_root / norm_dir).is_dir()
        )
        if is_dir and _dir_contains_python(repo_root, norm_dir or ".", raw):
            dir_root = norm_dir or "."
            key = (dir_root, "dir")
            if key not in seen_roots:
                seen_roots.add(key)
                globs_and_dirs.append(
                    _AllowedPyEntry(pattern=dir_root, root=dir_root, kind="dir")
                )
    return concrete, globs_and_dirs


def _target_matches_allowed_py_root(target_tok: str, entry: _AllowedPyEntry) -> bool:
    clean_tok = (
        target_tok.split("::", 1)[0]
        .strip()
        .replace("\\", "/")
        .removeprefix("./")
        .rstrip("/")
    )
    if not clean_tok or clean_tok.startswith("-"):
        return False
    if clean_tok == entry.pattern or _target_covers_path(clean_tok, entry.root):
        return True
    if entry.kind == "dir":
        return _target_covers_path(entry.root, clean_tok)
    if _glob_matches(entry.pattern, clean_tok):
        return True
    return "**" in entry.pattern and _target_covers_path(entry.root, clean_tok)


def _matches_python_cap(
    cap: list[str],
    command: str,
    *,
    allowed_py: Sequence[str],
    allowed_py_roots: Sequence[_AllowedPyEntry] = (),
    allow_historical_prefix: bool,
) -> bool:
    """Match a Python static capability against sequential subcommands, supporting scoped Allowed files."""
    prefix = _cap_tool_prefix(cap)
    cap_tail = cap[len(prefix) :] if prefix else []
    cap_tail_norm = {
        tok.strip().replace("\\", "/").removeprefix("./").rstrip("/") or "."
        for tok in _extract_py_positional_targets(cap_tail)
    }
    cap_tail_raw = set(cap_tail)
    for sub in _split_sequential_subcommands(command):
        if sub == cap:
            return True
        if len(sub) >= len(cap) and sub[: len(cap)] == cap:
            return True
        if prefix and len(sub) > len(prefix) and sub[: len(prefix)] == prefix:
            if allow_historical_prefix:
                return True
            if not allowed_py and not allowed_py_roots:
                continue
            wrapper_dir = registry._extract_monorepo_dir_wrapper(sub)
            pos_targets = _extract_py_positional_targets(sub[len(prefix) :])
            if not pos_targets:
                continue
            resolved_targets = [
                _resolve_target_with_wrapper_dir(t, wrapper_dir) for t in pos_targets
            ]
            if not all(
                any(_target_covers_path(rt, p) for rt in resolved_targets)
                for p in allowed_py
            ):
                continue
            if not all(
                any(
                    _target_matches_allowed_py_root(rt, entry)
                    for rt in resolved_targets
                )
                for entry in allowed_py_roots
            ):
                continue
            if all(
                any(_target_covers_path(rt, p) for p in allowed_py)
                or any(
                    _target_matches_allowed_py_root(rt, entry)
                    for entry in allowed_py_roots
                )
                or (
                    (t.strip().replace("\\", "/").removeprefix("./").rstrip("/") or ".")
                    in cap_tail_norm
                )
                or t in cap_tail_raw
                for t, rt in zip(pos_targets, resolved_targets)
            ):
                return True
    return False


def check_python_tier_b(
    check: Checker,
    stem: str,
    rows: list[Any],
    *,
    text: str = "",
    allow_historical_prefix: bool = False,
) -> None:
    tier_b_rows = [r for r in rows if r.phase == "TIER-B"]
    allowed_py, allowed_py_roots = (
        _collect_allowed_py_entries(tc.parse_allowed_files(text), check.root)
        if text
        else ([], [])
    )
    manifest_path = check.root / ".agents" / "quality" / "python-quality.json"
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            check.problem(
                f"{stem}:Verification",
                "malformed .agents/quality/python-quality.json manifest",
            )
            return
        if not isinstance(data, dict):
            check.problem(
                f"{stem}:Verification",
                "invalid python-quality.json manifest: root must be an object",
            )
            return
        capabilities = data.get("capabilities")
        if not isinstance(capabilities, dict):
            check.problem(
                f"{stem}:Verification",
                "invalid python-quality.json manifest: capabilities must be an object",
            )
            return
        lint_cmd = capabilities.get("lint")
        type_check_cmd = capabilities.get("type_check")
        if (
            not isinstance(lint_cmd, list)
            or not lint_cmd
            or not all(isinstance(x, str) for x in lint_cmd)
        ):
            check.problem(
                f"{stem}:Verification",
                "invalid python-quality.json manifest: lint capability missing or invalid",
            )
            return
        if (
            not isinstance(type_check_cmd, list)
            or not type_check_cmd
            or not all(isinstance(x, str) for x in type_check_cmd)
        ):
            check.problem(
                f"{stem}:Verification",
                "invalid python-quality.json manifest: type_check capability missing or invalid",
            )
            return

        has_lint = any(
            _matches_python_cap(
                lint_cmd,
                r.command,
                allowed_py=allowed_py,
                allowed_py_roots=allowed_py_roots,
                allow_historical_prefix=allow_historical_prefix,
            )
            for r in tier_b_rows
        )
        has_type = any(
            _matches_python_cap(
                type_check_cmd,
                r.command,
                allowed_py=allowed_py,
                allowed_py_roots=allowed_py_roots,
                allow_historical_prefix=allow_historical_prefix,
            )
            for r in tier_b_rows
        )
        if not has_lint:
            check.problem(
                f"{stem}:Verification",
                f"Python task missing registered lint capability ({' '.join(lint_cmd)})",
            )
        if not has_type:
            check.problem(
                f"{stem}:Verification",
                f"Python task missing registered type_check capability ({' '.join(type_check_cmd)})",
            )
        if tier_b_rows and text and not allow_historical_prefix:
            _check_python_tier_b_allowed_coverage(check, stem, text, tier_b_rows)
        return

    # Fallback tooling: ruff + (mypy / pyright / ty) across sequential subcommands
    has_ruff = False
    has_type_checker = False
    for r in tier_b_rows:
        for sub in _split_sequential_subcommands(r.command):
            prog = tc.strip_wrappers(list(sub))
            first = Path(prog[0]).name if prog else ""
            if first == "ruff":
                has_ruff = True
            if first in ("mypy", "pyright", "ty"):
                has_type_checker = True

    if not has_ruff or not has_type_checker:
        missing_tools: list[str] = []
        if not has_ruff:
            missing_tools.append("lint (ruff)")
        if not has_type_checker:
            missing_tools.append("type-check (mypy/pyright/ty)")
        check.problem(
            f"{stem}:Verification",
            f"Python task requires TIER-B direct {', '.join(missing_tools)}",
        )
        return

    if text and not allow_historical_prefix:
        _check_python_tier_b_allowed_coverage(check, stem, text, tier_b_rows)


def _check_python_tier_b_allowed_coverage(
    check: Checker,
    stem: str,
    text: str,
    tier_b_rows: list[Any],
) -> None:
    """When Allowed files includes production and test Python files (or multiple production files), ensure TIER-B lint and type-check cover all Allowed .py files."""
    allowed_entries = tc.parse_allowed_files(text)
    allowed_py = [
        entry.pattern.removeprefix("./")
        for entry in allowed_entries
        if entry.pattern.lower().endswith(".py")
        and not GLOB_CHARS.search(entry.pattern)
    ]
    has_test_py = any(_is_test_path(p) for p in allowed_py)
    prod_py = [p for p in allowed_py if not _is_test_path(p)]
    has_new_test_py = any(
        entry.new
        and entry.pattern.lower().endswith(".py")
        and _is_test_path(entry.pattern)
        for entry in allowed_entries
    )
    has_strict_or_format = any(
        "--strict" in r.command or "ruff format" in r.command for r in tier_b_rows
    )
    if not (
        prod_py
        and has_test_py
        and (has_new_test_py or len(prod_py) > 1 or has_strict_or_format)
    ):
        return

    lint_targets: list[str] = []
    type_targets: list[str] = []
    for r in tier_b_rows:
        for sub in _split_sequential_subcommands(r.command):
            wrapper_dir = registry._extract_monorepo_dir_wrapper(sub)
            unwrapped = registry._strip_command_wrappers(sub)
            if not unwrapped:
                continue
            tool = Path(unwrapped[0]).name
            if tool == "ruff":
                tail = (
                    unwrapped[2:]
                    if len(unwrapped) > 1 and unwrapped[1] in ("check", "format")
                    else unwrapped[1:]
                )
                pos = _extract_py_positional_targets(tail)
                resolved = [
                    _resolve_target_with_wrapper_dir(t, wrapper_dir) for t in pos
                ]
                lint_targets.extend(resolved or [wrapper_dir or "."])
            elif tool in ("mypy", "pyright", "ty"):
                tail = (
                    unwrapped[2:]
                    if tool == "ty" and len(unwrapped) > 1 and unwrapped[1] == "check"
                    else unwrapped[1:]
                )
                pos = _extract_py_positional_targets(tail)
                resolved = [
                    _resolve_target_with_wrapper_dir(t, wrapper_dir) for t in pos
                ]
                type_targets.extend(resolved or [wrapper_dir or "."])

    if lint_targets:
        missing_lint = [
            p
            for p in allowed_py
            if not any(_target_covers_path(t, p) for t in lint_targets)
        ]
        if missing_lint:
            check.problem(
                f"{stem}:Verification",
                f"Python task TIER-B lint must cover all Allowed Python files (including test files); missing: {', '.join(missing_lint)}",
            )
    if type_targets:
        missing_type = [
            p
            for p in allowed_py
            if not any(_target_covers_path(t, p) for t in type_targets)
        ]
        if missing_type:
            check.problem(
                f"{stem}:Verification",
                f"Python task TIER-B type-check must cover all Allowed Python files (including test files); missing: {', '.join(missing_type)}",
            )


def check_weak_bdd(check: Checker, source_name: str, text: str) -> None:
    for line_num, line in enumerate(text.splitlines(), start=1):
        m = WEAK_ASSERTION_RE.search(line)
        if m:
            check.problem(
                f"{source_name}:{line_num}", f"weak BDD assertion found: {m.group(0)!r}"
            )


def _read_text_if_not_binary(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw[:8192]:
        return None
    return raw.decode("utf-8", errors="replace")


def _python_symbols(content: str) -> set[str]:
    symbols: set[str] = set()
    try:
        tree = ast.parse(content)
    except SyntaxError:
        for m in re.finditer(
            r"^\s*(?:async\s+def|def|class)\s+([A-Za-z_][A-Za-z0-9_]*)",
            content,
            re.MULTILINE,
        ):
            symbols.add(m.group(1))
        return symbols

    def _visit(node: ast.AST, prefix: str = "") -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(node.name)
            qual = f"{prefix}.{node.name}" if prefix else node.name
            symbols.add(qual)
            for child in node.body:
                _visit(child, qual)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbols.add(target.id)
                    if prefix:
                        symbols.add(f"{prefix}.{target.id}")
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            symbols.add(node.target.id)
            if prefix:
                symbols.add(f"{prefix}.{node.target.id}")
        elif isinstance(node, (ast.If, ast.Try, ast.With)):
            for subnode in ast.iter_child_nodes(node):
                _visit(subnode, prefix)

    for top_node in tree.body:
        _visit(top_node)
    return symbols


def _collect_anchor_section_bodies(text: str) -> list[str]:
    bodies: list[str] = []
    current_lines: list[str] | None = None
    fence: str | None = None
    for line in text.splitlines():
        marker = tc.FENCE.match(line)
        if marker:
            if fence is None:
                fence = marker.group(1)
            elif marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                fence = None
        elif fence is None and line.startswith("## "):
            if current_lines is not None:
                bodies.append("\n".join(current_lines))
            heading = line[3:].strip().lower()
            current_lines = [] if heading in ANCHOR_SECTIONS else None
            continue
        if current_lines is not None:
            current_lines.append(line)
    if current_lines is not None:
        bodies.append("\n".join(current_lines))
    return bodies


def _strip_matched_path(line: str, pattern: str) -> tuple[bool, str]:
    full_re = re.compile(rf"(?<![\w/.-]){re.escape(pattern)}(?![\w/.-])")
    base_name = Path(pattern).name
    base_re = re.compile(rf"(?<![\w/.-]){re.escape(base_name)}(?![\w/.-])")
    if full_re.search(line):
        cleaned = line.replace(f"`{pattern}`", "")
        cleaned = full_re.sub("", cleaned)
        return True, cleaned
    if base_re.search(line):
        cleaned = line.replace(f"`{base_name}`", "")
        cleaned = base_re.sub("", cleaned)
        return True, cleaned
    return False, line


def _iter_file_anchor_chunks(
    section_bodies: list[str], pattern: str
) -> list[tuple[str, str]]:
    chunks: list[tuple[str, str]] = []
    for body in section_bodies:
        lines = body.splitlines()
        idx = 0
        while idx < len(lines):
            line = lines[idx]
            matched, cleaned_head = _strip_matched_path(line, pattern)
            if not matched:
                idx += 1
                continue
            raw_parts = [line]
            clean_parts = [cleaned_head]
            if re.match(r"^\s*[-*]\s+", line):
                base_indent = len(line) - len(line.lstrip())
                next_idx = idx + 1
                while next_idx < len(lines):
                    nxt = lines[next_idx]
                    if not nxt.strip():
                        break
                    if (len(nxt) - len(nxt.lstrip())) <= base_indent:
                        break
                    raw_parts.append(nxt)
                    _, cleaned_nxt = _strip_matched_path(nxt, pattern)
                    clean_parts.append(cleaned_nxt)
                    next_idx += 1
            chunks.append(("\n".join(raw_parts), "\n".join(clean_parts)))
            idx += 1
    return chunks


def _extract_symbol_candidates(raw_chunk: str, cleaned_chunk: str) -> list[str]:
    candidates: list[str] = []
    for span in tc.CODE_SPAN.findall(cleaned_chunk):
        cand = span.strip().removesuffix("()").split("[", 1)[0]
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", cand) and not re.fullmatch(
            r"L\d+", cand
        ):
            candidates.append(cand)
    for m in re.finditer(r"::\s*`?([A-Za-z_][A-Za-z0-9_.]*)`?", raw_chunk):
        cand = m.group(1)
        if not re.fullmatch(r"L\d+", cand):
            candidates.append(cand)
    for line in cleaned_chunk.splitlines():
        if ":" not in line:
            continue
        after_colon = line.split(":", 1)[1]
        for tok in re.findall(r"\b([A-Za-z_][A-Za-z0-9_.]*)\b", after_colon):
            if not re.fullmatch(r"L\d+", tok) and tok.lower() not in NON_SYMBOL_WORDS:
                candidates.append(tok)
    return candidates


def _symbol_present_in_file(
    cand: str, is_python: bool, py_symbols: set[str], content: str
) -> bool:
    if is_python:
        return cand in py_symbols or cand.split(".")[-1] in py_symbols
    leaf = cand.split(".")[-1]
    if len(leaf) < 2 or leaf.lower() in NON_SYMBOL_WORDS:
        return False
    return bool(re.search(rf"\b{re.escape(leaf)}\b", content))


def _has_valid_anchor(
    pattern: str, content: str, line_count: int, section_bodies: list[str]
) -> bool:
    is_python = pattern.endswith(".py")
    py_symbols: set[str] | None = None
    for raw_chunk, cleaned_chunk in _iter_file_anchor_chunks(section_bodies, pattern):
        for m in LINE_RANGE_RE.finditer(cleaned_chunk):
            start, end = int(m.group(1)), int(m.group(2))
            if 1 <= start <= end <= line_count:
                return True
        candidates = _extract_symbol_candidates(raw_chunk, cleaned_chunk)
        if candidates:
            if is_python and py_symbols is None:
                py_symbols = _python_symbols(content)
            for cand in candidates:
                if _symbol_present_in_file(
                    cand, is_python, py_symbols or set(), content
                ):
                    return True
    return False


def check_surgical_anchors(check: Checker, stem: str, text: str) -> None:
    """Require symbol or (L<start>-L<end>) anchors for >200-line tracked Allowed files."""
    section_bodies = _collect_anchor_section_bodies(text)
    for entry in tc.parse_allowed_files(text):
        pattern = entry.pattern
        if (
            entry.new
            or (not check.is_tracked(pattern) and GLOB_CHARS.search(pattern))
            or pattern.endswith("/")
        ):
            continue
        if not check.is_tracked(pattern):
            continue
        target_path = check.root / pattern
        if (
            not target_path.is_file()
            or target_path.name in LOCKFILE_NAMES
            or target_path.suffix.lower() == ".lock"
        ):
            continue
        content = _read_text_if_not_binary(target_path)
        if content is None:
            continue
        lines = content.splitlines()
        if len(lines) <= SURGICAL_LINE_THRESHOLD:
            continue
        if not _has_valid_anchor(pattern, content, len(lines), section_bodies):
            check.problem(
                f"{stem}:Files",
                f"{pattern} ({len(lines)} lines > {SURGICAL_LINE_THRESHOLD}) lacks a target symbol or (L<start>-L<end>) line-range anchor",
            )


_NPX_VALUE_FLAGS = frozenset(
    {
        "-p",
        "--package",
        "-c",
        "--call",
        "--node-arg",
        "--userconfig",
        "--cache",
        "--prefix",
        "-C",
    }
)
_PLAN_TASK_HEADING_RE = re.compile(r"^###\s+Task\s+(\d+)\b(.*)$")
_PLAN_FILE_LINE_RE = re.compile(
    r"^\s*[-*]\s+\*{0,2}(Create|Modify|Test)\*{0,2}\s*:\s*(.*)$",
    re.IGNORECASE,
)
_PLAN_SUB_BULLET_RE = re.compile(r"^\s+[-*]\s+(.+)$")
_PLAN_RUN_LINE_RE = re.compile(
    r"^\s*(?:[-*]\s+)?\*{0,2}Run\*{0,2}\s*:\s*(.+)$",
    re.IGNORECASE,
)
_PLAN_SHELL_FENCE_LANGS = frozenset({"bash", "sh", "zsh", "shell"})
_PLAN_LINE_RANGE_SUFFIX_RE = re.compile(r":L?\d+(?:[-–]L?\d+)?$")


@dataclass(frozen=True)
class _PlanFileEntry:
    pattern: str
    new: bool
    kind: str


@dataclass(frozen=True)
class _PlanTask:
    number: int
    index: int
    heading: str
    files: tuple[_PlanFileEntry, ...]
    commands: tuple[str, ...]


def _glob_matches_path_or_basename(pattern: str, path: str) -> bool:
    norm_pat = pattern.strip().replace("\\", "/").removeprefix("./")
    norm_path = path.strip().replace("\\", "/").removeprefix("./")
    if not norm_pat or not norm_path:
        return False
    if norm_pat.endswith("/"):
        return norm_path.startswith(norm_pat)
    if registry._glob_matches(norm_pat, norm_path):
        return True
    if "/" not in norm_pat:
        return registry._glob_matches(norm_pat, Path(norm_path).name)
    return False


def _is_stack_test_path(path: str, desc: registry.StackDescriptor) -> bool:
    if registry.TriageSurfaceRegistry.is_test_file(path) or _is_test_path(path):
        return True
    tr = desc.test_routing
    return any(
        _glob_matches_path_or_basename(pat, path)
        for pat in (
            *tr.canonical_test_globs,
            *tr.forbidden_test_globs,
            *tr.lcov_unit_test_globs,
        )
    )


_TEST_ROUTING_KEYS = frozenset(
    {
        "canonical_test_globs",
        "forbidden_test_globs",
        "paired_source_globs",
        "lcov_unit_test_globs",
        "cache_bust_extensions",
    }
)
_WEB_TOUCHED_EXTENSIONS = frozenset(
    {
        ".js",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".jsx",
        ".css",
        ".html",
        ".astro",
        ".jinja",
        ".jinja2",
    }
)
_EXT_PATTERN_RE = re.compile(r"^\.[a-z0-9]+$")


def _read_manifest_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"malformed {path.name}: {exc}"
    if not isinstance(raw, dict):
        return None, f"invalid {path.name}: root must be a JSON object"
    return raw, None


def _validate_manifest_test_routing(
    manifest: Mapping[str, Any], manifest_name: str
) -> str | None:
    if "test_routing" not in manifest:
        return None
    routing = manifest["test_routing"]
    if not isinstance(routing, dict):
        return f"malformed {manifest_name}: 'test_routing' must be an object"
    for key, val in sorted(routing.items()):
        if key not in _TEST_ROUTING_KEYS:
            return f"malformed {manifest_name}: unknown test_routing field '{key}'"
        if not isinstance(val, list) or not val:
            return f"malformed {manifest_name}: test_routing.{key} must be a non-empty array of strings"
        if key == "cache_bust_extensions":
            for ext in val:
                if not isinstance(ext, str) or not _EXT_PATTERN_RE.match(ext):
                    return (
                        f"malformed {manifest_name}: test_routing.cache_bust_extensions "
                        f"entry {ext!r} must match ^\\.[a-z0-9]+$"
                    )
        else:
            for pat in val:
                if (
                    not isinstance(pat, str)
                    or not pat.strip()
                    or pat.strip().startswith(("/", "\\", "~"))
                    or ".." in pat.replace("\\", "/").split("/")
                ):
                    return (
                        f"malformed {manifest_name}: test_routing.{key} "
                        f"contains invalid relative glob {pat!r}"
                    )
    return None


def _stack_touched_by_files(
    sid: str,
    file_patterns: Sequence[str],
    desc: registry.StackDescriptor | None,
) -> bool:
    if desc is not None and any(
        registry._path_matches_stack(p, desc) for p in file_patterns
    ):
        return True
    if sid == "web":
        for pat in file_patterns:
            norm = pat.strip().replace("\\", "/").removeprefix("./")
            if Path(norm).suffix.lower() in _WEB_TOUCHED_EXTENSIONS:
                return True
    if sid == "python":
        for pat in file_patterns:
            norm = pat.strip().replace("\\", "/").removeprefix("./")
            if norm.lower().endswith(".py") or Path(norm).name in (
                "pyproject.toml",
                "setup.py",
                "requirements.txt",
                "Pipfile",
            ):
                return True
    return False


def _check_unexpanded_placeholders(check: Checker, where: str, command: str) -> None:
    if "{skills_dir}" in command:
        check.problem(
            where,
            "unexpanded manifest placeholder '{skills_dir}'; use \"$D3NEXUS_KIT/skills\"",
        )
    if "{base_ref}" in command:
        check.problem(
            where,
            "unexpanded manifest placeholder '{base_ref}'; expand to an explicit git ref",
        )


def _check_bare_npx(check: Checker, where: str, command: str) -> None:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()
    for sub in _split_subcommands(tokens):
        unwrapped = registry._strip_version_manager_wrappers(sub)
        if not unwrapped or Path(unwrapped[0]).name != "npx":
            continue
        has_no_install = False
        has_yes = False
        has_package = False
        has_positional = False
        idx = 1
        while idx < len(unwrapped):
            tok = unwrapped[idx]
            if tok == "--":
                if idx + 1 < len(unwrapped):
                    has_positional = True
                break
            if tok == "--no-install":
                has_no_install = True
                idx += 1
                continue
            if tok in ("-y", "--yes"):
                has_yes = True
                idx += 1
                continue
            if tok in ("-p", "--package"):
                has_package = True
                idx += 2 if idx + 1 < len(unwrapped) else 1
                continue
            if tok.startswith(("--package=", "-p=")):
                has_package = True
                idx += 1
                continue
            if tok in _NPX_VALUE_FLAGS:
                idx += 2 if idx + 1 < len(unwrapped) else 1
                continue
            if tok.startswith("-"):
                idx += 1
                continue
            has_positional = True
            break
        if has_positional and not has_no_install and not (has_yes and has_package):
            check.problem(
                where,
                "bare 'npx' invocation; use 'npx --no-install <bin>' or 'npx --yes --package <pkg> <bin>'",
            )


def _extract_cap_tokens(caps: Mapping[str, Any] | None, key: str) -> list[str] | None:
    if not isinstance(caps, Mapping):
        return None
    val = caps.get(key)
    if isinstance(val, list) and val and all(isinstance(x, str) for x in val):
        return list(val)
    return None


def _check_intermediate_python_full_repo(
    check: Checker,
    task_label: str,
    cmd_items: Sequence[tuple[str, str]],
    allowed_patterns: Sequence[str],
    py_manifest: Mapping[str, Any] | None,
) -> None:
    touches_py_config = any(
        (
            (norm := pat.strip().replace("\\", "/").removeprefix("./"))
            == "pyproject.toml"
            or norm.endswith("/pyproject.toml")
            or norm == ".agents/quality"
            or norm.startswith(".agents/quality/")
        )
        for pat in allowed_patterns
    )
    if touches_py_config:
        return
    caps = (
        py_manifest.get("capabilities")
        if isinstance(py_manifest, Mapping)
        and isinstance(py_manifest.get("capabilities"), Mapping)
        else None
    )
    lint_cap = _extract_cap_tokens(caps, "lint")
    format_cap = _extract_cap_tokens(caps, "format")
    type_cap = _extract_cap_tokens(caps, "type_check")

    for where, cmd in cmd_items:
        for sub in _split_sequential_subcommands(cmd):
            unwrapped = registry._strip_command_wrappers(sub)
            if not unwrapped:
                continue
            tool = Path(unwrapped[0]).name.lower()
            if tool not in ("ruff", "mypy", "pyright", "ty"):
                continue
            cap: list[str] | None
            if py_manifest is None:
                cap = None
            elif tool == "ruff":
                if len(unwrapped) >= 2 and unwrapped[1] == "format":
                    cap = format_cap if format_cap is not None else lint_cap
                else:
                    cap = lint_cap
            else:
                cap = type_cap
            if rtqp.is_full_repo_python_tier_b_subcommand(sub, cap):
                check.problem(
                    where,
                    f"intermediate task ({task_label}) must scope Python TIER-B '{tool}' to Allowed files instead of full-repo target ('.' or 'src tests')",
                )


def _command_runs_web_lcov_unit_test(command: str, lcov_globs: Sequence[str]) -> bool:
    for sub in _split_sequential_subcommands(command):
        unwrapped = registry._strip_command_wrappers(sub)
        if not unwrapped:
            continue
        if Path(unwrapped[0]).name.lower() == "playwright" or any(
            "playwright" in tok.lower() for tok in unwrapped[:2]
        ):
            continue
        for tok in sub:
            val = tok.split("=", 1)[1] if tok.startswith("-") and "=" in tok else tok
            clean = val.strip().replace("\\", "/").removeprefix("./")
            if not clean or clean.startswith("-"):
                continue
            if any(
                _glob_matches_path_or_basename(g, clean)
                or clean == g.strip().replace("\\", "/").removeprefix("./")
                for g in lcov_globs
            ):
                return True
            dir_prefix = clean.rstrip("/") + "/"
            if dir_prefix != "/" and any(
                g.strip().replace("\\", "/").removeprefix("./").startswith(dir_prefix)
                for g in lcov_globs
            ):
                return True
    return False


def _check_web_lcov_unit_tests(
    check: Checker,
    where: str,
    allowed_entries: Sequence[Any],
    test_commands: Sequence[str],
    web_manifest: Mapping[str, Any] | None,
) -> None:
    if web_manifest is None:
        return
    requires_lcov, lcov_globs = rtqp.web_requires_lcov_unit_tests(web_manifest)
    if not requires_lcov:
        return

    web_prod_js: list[str] = []
    has_lcov_in_allowed = False
    for entry in allowed_entries:
        norm = str(entry.pattern).strip().replace("\\", "/").removeprefix("./")
        if not norm or GLOB_CHARS.search(norm):
            continue
        if any(_glob_matches_path_or_basename(g, norm) for g in lcov_globs):
            has_lcov_in_allowed = True
            continue
        if (
            Path(norm).suffix.lower() in (".js", ".mjs")
            and not registry.TriageSurfaceRegistry.is_test_file(norm)
            and not _is_test_path(norm)
        ):
            web_prod_js.append(norm)

    if not web_prod_js or has_lcov_in_allowed:
        return
    if any(_command_runs_web_lcov_unit_test(cmd, lcov_globs) for cmd in test_commands):
        return
    check.problem(
        where,
        f"Web task touches production JS/MJS ({', '.join(web_prod_js)}) under LCOV diff_coverage "
        f"without a JS unit test matching ({', '.join(lcov_globs)}) in Allowed files or GREEN/REGRESSION rows",
    )


def _check_test_routing_rules(
    check: Checker,
    where: str,
    allowed_entries: Sequence[Any],
    loaded_descriptors: Mapping[str, registry.StackDescriptor],
) -> None:
    for sid, desc in sorted(loaded_descriptors.items()):
        tr = desc.test_routing
        if not (
            tr.canonical_test_globs or tr.forbidden_test_globs or tr.paired_source_globs
        ):
            continue
        allowed_canon = tr.canonical_test_globs + tr.lcov_unit_test_globs
        paired_new_sources: list[str] = []
        has_valid_stack_test = False

        for entry in allowed_entries:
            norm = str(entry.pattern).strip().replace("\\", "/").removeprefix("./")
            if not norm or GLOB_CHARS.search(norm):
                continue
            if not registry._path_matches_stack(norm, desc):
                continue
            is_test = _is_stack_test_path(norm, desc)
            matched_forbidden = next(
                (
                    g
                    for g in tr.forbidden_test_globs
                    if _glob_matches_path_or_basename(g, norm)
                ),
                None,
            )
            if is_test:
                if entry.new and matched_forbidden is not None:
                    hint = (
                        f"; place under canonical_test_globs ({', '.join(tr.canonical_test_globs)})"
                        if tr.canonical_test_globs
                        else ""
                    )
                    check.problem(
                        where,
                        f"test_routing violation: (new) test file '{norm}' matches forbidden_test_globs '{matched_forbidden}'{hint}",
                    )
                elif (
                    entry.new
                    and tr.canonical_test_globs
                    and not any(
                        _glob_matches_path_or_basename(g, norm) for g in allowed_canon
                    )
                ):
                    check.problem(
                        where,
                        f"test_routing violation: (new) test file '{norm}' is outside canonical_test_globs ({', '.join(tr.canonical_test_globs)})",
                    )
                if matched_forbidden is None:
                    has_valid_stack_test = True
            elif (
                entry.new
                and tr.paired_source_globs
                and any(
                    _glob_matches_path_or_basename(g, norm)
                    for g in tr.paired_source_globs
                )
            ):
                paired_new_sources.append(norm)

        if paired_new_sources and not has_valid_stack_test:
            check.problem(
                where,
                f"test_routing violation: (new) source file(s) ({', '.join(paired_new_sources)}) "
                f"match paired_source_globs ({', '.join(tr.paired_source_globs)}) "
                f"without a paired {sid} unit test in Allowed files",
            )


def _check_cache_bust_templates(
    check: Checker,
    where: str,
    allowed_entries: Sequence[Any],
    web_manifest: Mapping[str, Any] | None,
) -> None:
    if web_manifest is None:
        return
    modified_assets = [
        norm
        for entry in allowed_entries
        if not entry.new
        and (norm := str(entry.pattern).strip().replace("\\", "/").removeprefix("./"))
        and not GLOB_CHARS.search(norm)
    ]
    if not modified_assets:
        return
    matched_templates = rtqp.find_cache_bust_templates(
        check.root, modified_assets, web_manifest
    )
    tracked_templates = [
        tpl
        for tpl in matched_templates
        if (not check.in_git_repo) or check.is_tracked(tpl)
    ]
    missing_templates = [
        tpl
        for tpl in tracked_templates
        if not any(
            _target_covers_path(str(entry.pattern), tpl) for entry in allowed_entries
        )
    ]
    if missing_templates:
        check.problem(
            where,
            "cache-bust (?v=) template violation: modifying static asset(s) requires updating "
            f"referencing template(s) in Allowed files; missing: {', '.join(missing_templates)}",
        )


def check_shift_left_quality_guards(
    check: Checker,
    stem: str,
    allowed_entries: Sequence[Any],
    rows: Sequence[Any],
    *,
    is_intermediate_task: bool = False,
) -> None:
    """Enforce fail-closed Shift-Left quality-layer guards on active design tasks."""
    for row in rows:
        _check_unexpanded_placeholders(check, f"{stem}:{row.id}", row.command)

    quality_dir = check.root / ".agents" / "quality"
    py_manifest, _ = _read_manifest_json(quality_dir / "python-quality.json")
    web_manifest, _ = _read_manifest_json(quality_dir / "web-quality.json")
    file_patterns = [str(entry.pattern) for entry in allowed_entries]

    if is_intermediate_task:
        tier_b_items = [
            (f"{stem}:{row.id}", row.command) for row in rows if row.phase == "TIER-B"
        ]
        _check_intermediate_python_full_repo(
            check,
            stem,
            tier_b_items,
            file_patterns,
            py_manifest,
        )

    if not quality_dir.is_dir():
        return

    loaded_descs, manifest_paths, manifest_errors = registry._load_repo_manifests(
        check.root
    )
    reported_manifests: set[str] = set()

    def _already_reported(manifest_name: str) -> bool:
        return manifest_name in reported_manifests or any(
            p.startswith(f"{stem}:") and manifest_name in p for p in check.problems
        )

    for sid, mpath in sorted(manifest_paths.items()):
        desc_for_match = loaded_descs.get(sid) or registry.BUILTIN_STACKS.get(sid)
        if not _stack_touched_by_files(sid, file_patterns, desc_for_match):
            continue
        m_data, m_err = _read_manifest_json(mpath)
        if m_err is not None:
            if not _already_reported(mpath.name):
                check.problem(f"{stem}:Files", f"invalid .agents/quality/{m_err}")
                reported_manifests.add(mpath.name)
            continue
        matching_reg_err = next((e for e in manifest_errors if mpath.name in e), None)
        if matching_reg_err is not None and not _already_reported(mpath.name):
            check.problem(
                f"{stem}:Files", f"invalid .agents/quality/{matching_reg_err}"
            )
            reported_manifests.add(mpath.name)
        if m_data is not None:
            tr_err = _validate_manifest_test_routing(m_data, mpath.name)
            if tr_err is not None:
                check.problem(f"{stem}:Files", f"invalid .agents/quality/{tr_err}")
                reported_manifests.add(mpath.name)

    green_reg_cmds = [
        row.command for row in rows if row.phase in ("GREEN", "REGRESSION")
    ]
    _check_web_lcov_unit_tests(
        check, f"{stem}:Verification", allowed_entries, green_reg_cmds, web_manifest
    )

    if loaded_descs:
        _check_test_routing_rules(check, f"{stem}:Files", allowed_entries, loaded_descs)

    _check_cache_bust_templates(check, f"{stem}:Files", allowed_entries, web_manifest)


def _task_order_key(path: Path, text: str) -> tuple[int, str, int, str]:
    m_stem = re.match(r"^task[_-]?0*(\d+)(?=[_-]|$)", path.stem, re.IGNORECASE)
    if m_stem:
        return (2, "", int(m_stem.group(1)), path.stem)
    if text.startswith("---"):
        fm = text.split("\n---", 1)[0]
        m_ord = re.search(r'^order:\s*"?([A-Za-z0-9_-]+)"?\s*$', fm, re.MULTILINE)
        if m_ord:
            val = m_ord.group(1)
            m_parts = re.match(r"^([A-Za-z_-]*?)(\d+)$", val)
            if m_parts:
                return (1, m_parts.group(1), int(m_parts.group(2)), path.stem)
            return (1, val, -1, path.stem)
    return (0, path.stem, 0, path.stem)


def _extract_plan_paths(raw_rest: str) -> list[str]:
    before_dash = re.split(r"\s+[—–]\s+", raw_rest.strip(), maxsplit=1)[0].strip()
    if not before_dash:
        return []
    paths: list[str] = []
    for chunk in before_dash.split(","):
        item = chunk.strip()
        if not item:
            continue
        if item.startswith("`"):
            m = re.match(r"^`([^`]+)`", item)
            cand = m.group(1) if m else item.replace("`", "")
        else:
            cand = item.replace("`", "")
        cand = re.sub(r"\s*\([^)]*\)\s*", " ", cand).strip()
        if not cand:
            continue
        cand = cand.split()[0]
        cand = _PLAN_LINE_RANGE_SUFFIX_RE.sub("", cand)
        cand = cand.replace("\\", "/").removeprefix("./").strip()
        if cand and ("/" in cand or "." in cand):
            paths.append(cand)
    return paths


def _flush_plan_fence_commands(lines: Sequence[str], target: list[str]) -> None:
    pending = ""
    for raw_line in lines:
        stripped = raw_line.strip()
        if not pending and (not stripped or stripped.startswith("#")):
            continue
        if stripped.endswith("\\"):
            part = stripped[:-1].rstrip()
            pending = f"{pending} {part}".strip() if pending else part
            continue
        combined = f"{pending} {stripped}".strip() if pending else stripped
        pending = ""
        if combined and not combined.startswith("#"):
            target.append(combined)
    if pending and not pending.startswith("#"):
        target.append(pending)


def _parse_standalone_plan(root: Path, text: str) -> list[_PlanTask]:
    tasks: list[_PlanTask] = []
    cur_num: int | None = None
    cur_heading = ""
    cur_files: list[_PlanFileEntry] = []
    cur_cmds: list[str] = []
    active_file_kind: str | None = None

    fence: str | None = None
    fence_lang = ""
    fence_lines: list[str] = []

    def _finish_task() -> None:
        nonlocal cur_num, cur_heading, cur_files, cur_cmds, active_file_kind
        if cur_num is not None:
            tasks.append(
                _PlanTask(
                    number=cur_num,
                    index=len(tasks),
                    heading=cur_heading,
                    files=tuple(cur_files),
                    commands=tuple(cur_cmds),
                )
            )
        cur_num = None
        cur_heading = ""
        cur_files = []
        cur_cmds = []
        active_file_kind = None

    def _append_plan_files(kind: str, raw_rest: str) -> None:
        for path in _extract_plan_paths(raw_rest):
            is_new = (
                True
                if kind == "create"
                else (False if kind == "modify" else not (root / path).exists())
            )
            entry = _PlanFileEntry(pattern=path, new=is_new, kind=kind)
            if not any(
                existing.pattern == entry.pattern and existing.new == entry.new
                for existing in cur_files
            ):
                cur_files.append(entry)

    for line in text.splitlines():
        marker = tc.FENCE.match(line)
        if marker:
            if fence is None:
                fence = marker.group(1)
                fence_lang = (
                    line[marker.end() :].strip().split()[0].lower()
                    if line[marker.end() :].strip()
                    else ""
                )
                fence_lines = []
            elif marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                if cur_num is not None and fence_lang in _PLAN_SHELL_FENCE_LANGS:
                    _flush_plan_fence_commands(fence_lines, cur_cmds)
                fence = None
                fence_lang = ""
                fence_lines = []
            continue

        if fence is not None:
            if cur_num is not None and fence_lang in _PLAN_SHELL_FENCE_LANGS:
                fence_lines.append(line)
            continue

        m_heading = _PLAN_TASK_HEADING_RE.match(line)
        if m_heading:
            _finish_task()
            cur_num = int(m_heading.group(1))
            cur_heading = line.strip()
            continue

        if cur_num is None:
            continue

        m_file = _PLAN_FILE_LINE_RE.match(line)
        if m_file:
            kind = m_file.group(1).lower()
            rest = m_file.group(2).strip()
            if rest:
                _append_plan_files(kind, rest)
                active_file_kind = None
            else:
                active_file_kind = kind
            continue

        if active_file_kind is not None:
            m_sub = _PLAN_SUB_BULLET_RE.match(line)
            if m_sub:
                _append_plan_files(active_file_kind, m_sub.group(1))
                continue
            if line.strip():
                active_file_kind = None

        m_run = _PLAN_RUN_LINE_RE.match(line)
        if m_run:
            rest = m_run.group(1).strip()
            spans = tc.CODE_SPAN.findall(rest)
            if spans:
                for span in spans:
                    if span.strip():
                        cur_cmds.append(span.strip())
            elif rest:
                cur_cmds.append(rest)

    _finish_task()
    return tasks


def check_standalone_plan(
    check: Checker, plan_path: Path, text: str
) -> dict[str, list[str]]:
    """Validate a standalone `/writing-plans` Markdown document against Shift-Left quality contracts."""
    plan_name = plan_path.name
    plan_tasks = _parse_standalone_plan(check.root, text)
    if not plan_tasks:
        check.problem(f"{plan_name}:Plan", "no '### Task N' sections found in plan")
        return {}

    quality_dir = check.root / ".agents" / "quality"
    loaded_descs, manifest_paths, manifest_errors = registry._load_repo_manifests(
        check.root
    )
    raw_manifests: dict[str, dict[str, Any]] = {}
    raw_manifest_errs: dict[str, str] = {}
    for sid, mpath in manifest_paths.items():
        data, err = _read_manifest_json(mpath)
        if data is not None:
            raw_manifests[sid] = data
        elif err is not None:
            raw_manifest_errs[sid] = err

    py_manifest_path = quality_dir / "python-quality.json"
    py_manifest = raw_manifests.get("python")
    web_manifest = raw_manifests.get("web")

    final_task = max(plan_tasks, key=lambda t: (t.number, t.index))
    final_py_files, final_py_roots = _collect_allowed_py_entries(
        final_task.files, check.root
    )
    program_provenance: dict[str, list[str]] = {}

    for pt in plan_tasks:
        where = f"{plan_name}:Task {pt.number}"
        for cmd in pt.commands:
            prog = tc.program_of(cmd, check.root)
            if prog:
                if where not in program_provenance.setdefault(prog, []):
                    program_provenance[prog].append(where)
            _check_unexpanded_placeholders(check, where, cmd)
            _check_bare_npx(check, where, cmd)

        if len(plan_tasks) >= 2 and pt is not final_task:
            _check_intermediate_python_full_repo(
                check,
                f"Task {pt.number}",
                [(where, cmd) for cmd in pt.commands],
                [f.pattern for f in pt.files],
                py_manifest,
            )

        if quality_dir.is_dir():
            candidate_cmds = list(pt.commands) + (
                list(final_task.commands) if pt is not final_task else []
            )
            task_py_files, task_py_roots = _collect_allowed_py_entries(
                pt.files, check.root
            )
            touches_python = (
                bool(task_py_files)
                or bool(task_py_roots)
                or any(Path(f.pattern).name == "pyproject.toml" for f in pt.files)
            )
            if touches_python and py_manifest_path.is_file():
                if py_manifest is None:
                    check.problem(
                        where, "malformed .agents/quality/python-quality.json manifest"
                    )
                else:
                    py_tr_err = _validate_manifest_test_routing(
                        py_manifest, "python-quality.json"
                    )
                    if py_tr_err is not None:
                        check.problem(where, f"invalid .agents/quality/{py_tr_err}")
                    caps = (
                        py_manifest.get("capabilities")
                        if isinstance(py_manifest.get("capabilities"), Mapping)
                        else None
                    )
                    lint_cap = _extract_cap_tokens(caps, "lint")
                    type_cap = _extract_cap_tokens(caps, "type_check")
                    union_py = list(dict.fromkeys([*task_py_files, *final_py_files]))
                    union_py_roots = list(
                        dict.fromkeys([*task_py_roots, *final_py_roots])
                    )
                    if lint_cap is not None:
                        has_lint = any(
                            _matches_python_cap(
                                lint_cap,
                                cmd,
                                allowed_py=task_py_files,
                                allowed_py_roots=task_py_roots,
                                allow_historical_prefix=False,
                            )
                            for cmd in pt.commands
                        ) or (
                            pt is not final_task
                            and any(
                                _matches_python_cap(
                                    lint_cap,
                                    cmd,
                                    allowed_py=union_py,
                                    allowed_py_roots=union_py_roots,
                                    allow_historical_prefix=False,
                                )
                                for cmd in final_task.commands
                            )
                        )
                        if not has_lint:
                            check.problem(
                                where,
                                f"Python plan task missing registered lint capability ({' '.join(lint_cap)})",
                            )
                    if type_cap is not None:
                        has_type = any(
                            _matches_python_cap(
                                type_cap,
                                cmd,
                                allowed_py=task_py_files,
                                allowed_py_roots=task_py_roots,
                                allow_historical_prefix=False,
                            )
                            for cmd in pt.commands
                        ) or (
                            pt is not final_task
                            and any(
                                _matches_python_cap(
                                    type_cap,
                                    cmd,
                                    allowed_py=union_py,
                                    allowed_py_roots=union_py_roots,
                                    allow_historical_prefix=False,
                                )
                                for cmd in final_task.commands
                            )
                        )
                        if not has_type:
                            check.problem(
                                where,
                                f"Python plan task missing registered type_check capability ({' '.join(type_cap)})",
                            )

            # Surface malformed non-Python manifests or invalid test_routing if touched
            file_patterns = [f.pattern for f in pt.files]
            for sid, mpath in sorted(manifest_paths.items()):
                if sid == "python":
                    continue
                desc_for_match = loaded_descs.get(sid) or registry.BUILTIN_STACKS.get(
                    sid
                )
                if not _stack_touched_by_files(sid, file_patterns, desc_for_match):
                    continue
                if sid in raw_manifest_errs:
                    check.problem(
                        where, f"invalid .agents/quality/{raw_manifest_errs[sid]}"
                    )
                    continue
                err = next((e for e in manifest_errors if mpath.name in e), None)
                if err:
                    check.problem(where, f"invalid .agents/quality/{err}")
                raw_m_data = raw_manifests.get(sid)
                if raw_m_data is not None:
                    tr_err = _validate_manifest_test_routing(raw_m_data, mpath.name)
                    if tr_err is not None:
                        check.problem(where, f"invalid .agents/quality/{tr_err}")

            # Non-Python active stack lint / type_check presence
            subcommands = [
                sub
                for cmd in candidate_cmds
                for sub in _split_sequential_subcommands(cmd)
            ]
            for sid, desc in sorted(loaded_descs.items()):
                if sid == "python":
                    continue
                if not any(
                    registry._path_matches_stack(p, desc) for p in file_patterns
                ):
                    continue
                raw_m = raw_manifests.get(sid, {})
                raw_caps = raw_m.get("capabilities")
                stack_caps: Mapping[str, Any] = (
                    raw_caps if isinstance(raw_caps, Mapping) else {}
                )
                raw_override = raw_m.get("task_tier_b")
                stack_override: Mapping[str, Any] = (
                    raw_override if isinstance(raw_override, Mapping) else {}
                )
                lint_cap_cmds = registry._cap_command_str(
                    stack_caps, "lint", "analyze", "clippy"
                )
                if lint_cap_cmds or "lint_prefixes" in stack_override:
                    lint_prefixes = (
                        desc.default_tier_b.lint_prefixes
                        if "lint_prefixes" in stack_override
                        else lint_cap_cmds
                    )
                    if lint_prefixes and not any(
                        registry._subcommand_matches_prefix(sub, pref)[0]
                        for sub in subcommands
                        for pref in lint_prefixes
                    ):
                        check.problem(
                            where,
                            f"{sid} plan task missing registered lint check (expected one of: {', '.join(lint_prefixes)})",
                        )
                type_cap_cmds = registry._cap_command_str(stack_caps, "type_check")
                if type_cap_cmds or "typecheck_prefixes" in stack_override:
                    type_prefixes = (
                        desc.default_tier_b.typecheck_prefixes
                        if "typecheck_prefixes" in stack_override
                        else type_cap_cmds
                    )
                    if type_prefixes and not any(
                        registry._subcommand_matches_prefix(sub, pref)[0]
                        for sub in subcommands
                        for pref in type_prefixes
                    ):
                        check.problem(
                            where,
                            f"{sid} plan task missing registered type_check check (expected one of: {', '.join(type_prefixes)})",
                        )

            _check_web_lcov_unit_tests(
                check, where, pt.files, pt.commands, web_manifest
            )
            if loaded_descs:
                _check_test_routing_rules(check, where, pt.files, loaded_descs)
            _check_cache_bust_templates(check, where, pt.files, web_manifest)

    return program_provenance


def check_task(
    check: Checker,
    path: Path,
    text: str,
    design: bool,
    created: set[str],
    prereq_files: set[str] | None = None,
    *,
    allow_existing_done_new: bool = False,
    is_intermediate_task: bool = False,
) -> None:
    stem = path.stem
    rows = table_rows(check, stem, text)
    task_status = _task_status(text)
    allow_hist = task_status == "done" or (
        allow_existing_done_new and task_status in EXISTING_NEW_EXEMPT_STATUSES
    )
    check_structure(
        check,
        stem,
        path,
        text,
        rows,
        design=design,
        allow_historical=allow_hist,
    )
    for row in rows:
        if row.expect.results and not check.ignored(row.expect.results):
            check.problem(
                f"{stem}:{row.id}",
                f"results path {row.expect.results} is not ignored by git",
            )
        check_pytest_k(check, stem, row)
        check_portable_command(check, stem, row)
    check_weak_bdd(check, stem, text)
    if design or task_status != "done":
        allowed_entries = tc.parse_allowed_files(text)
        if is_python_task(text, rows):
            check_python_tier_b(
                check, stem, rows, text=text, allow_historical_prefix=allow_hist
            )
        for where, msg in TierBContractAdapter.validate_tier_b(
            check.root,
            stem,
            allowed_entries,
            rows,
            allow_historical_prefix=allow_hist,
        ):
            check.problem(where, msg)
        active_stacks = TierBContractAdapter.resolve_active_stacks(
            check.root,
            [entry.pattern for entry in allowed_entries],
        )
        tier_c_problems, tier_c_warnings = TierCTaxonomy.check_tier_c_rows(
            stem,
            rows,
            active_stacks,
        )
        for where, msg in tier_c_problems:
            check.problem(where, msg)
        check.warnings.extend(tier_c_warnings)
        if design and not allow_hist:
            check_regression_coverage(check, stem, text, rows)
            check_shift_left_quality_guards(
                check,
                stem,
                allowed_entries,
                rows,
                is_intermediate_task=is_intermediate_task,
            )
        check_allowed(
            check,
            stem,
            text,
            design,
            prereq_files,
            allow_existing_done_new=allow_existing_done_new,
            task_status=task_status,
        )
        if design:
            check_surgical_anchors(check, stem, text)
        check_evidence(
            check,
            stem,
            text,
            design,
            allow_existing_done_new=allow_existing_done_new,
            task_status=task_status,
        )
        check_grounding(
            check,
            stem,
            text,
            rows,
            created,
            skip_placeholder_paths=design and not allow_hist,
        )


def check_hld(
    check: Checker,
    hld_path: Path,
    text: str,
    tasks: dict[Path, str],
    created: set[str] | None = None,
) -> None:
    name = hld_path.name
    if not tc.parse_protected_paths(text):
        check.problem(name, "no Protected paths: line")
    integration_roots = tc.parse_integration_test_roots(text)
    if integration_roots:
        for msg in TierCTaxonomy.validate_integration_test_roots(
            check.root,
            integration_roots,
            check.tracked,
            created or set(),
        ):
            check.problem(name, msg)
    results = tc.parse_integration_results(text)
    if not results:
        check.problem(name, "no Integration results: line")
    for entry in results:
        command, arrow, report = entry.rpartition(" -> ")
        if not arrow or not command.strip() or not report.strip():
            check.problem(
                name, f"Integration results line is not <command> -> <path>: {entry}"
            )
        elif not check.ignored(report.strip()):
            check.problem(
                name, f"Integration results path {report.strip()} is not ignored by git"
            )
    environment = tc.verification_environment(text)
    if environment is None or not environment.strip():
        check.problem(name, "## Verification Environment section is missing or empty")
        return
    specs = tc.parse_integration_result_specs(text)
    for spec in specs:
        for need in spec.needs:
            if need not in environment:
                check.problem(
                    name,
                    f"Live integration needs variable '{need}' is not named in the Verification Environment section",
                )
    for path, task_text in tasks.items():
        try:
            rows, _ = tc.parse_verification(task_text)
        except tc.ContractError:
            continue
        for row in rows:
            for need in row.needs:
                if need not in environment:
                    check.problem(
                        f"{path.stem}:{row.id}",
                        f"Needs {need} is not named in the Verification Environment section",
                    )
    bdd_path = resolve_epic_doc(hld_path.parent, "bdd_scenarios")
    if bdd_path is not None:
        try:
            content = read_file(bdd_path)
            check_weak_bdd(check, bdd_path.name, content)
        except UsageError:
            pass


def check_r2_r3_parity(check: Checker, hld_path: Path, tasks: dict[Path, str]) -> None:
    epic_dir = hld_path.parent.name
    bdd_path = resolve_epic_doc(hld_path.parent, "bdd_scenarios")
    canonical_blocks: dict[str, list[str]] = {}
    if bdd_path is not None and bdd_path.is_file():
        try:
            canonical_blocks = sts.extract_scenario_blocks(read_file(bdd_path))
        except UsageError:
            pass

    for task_path, epic_text in tasks.items():
        stem = task_path.stem
        # R3: BDD verbatim check
        covers: list[str] = []
        for line in epic_text.splitlines():
            m = re.match(r"^Covers:\s*(.+)$", line.strip())
            if m:
                covers.extend(re.findall(r"[A-Z0-9]+(?:-[A-Z0-9]+)+", m.group(1)))
        if covers and canonical_blocks:
            task_blocks = sts.extract_scenario_blocks(epic_text)
            for cid in covers:
                if cid in canonical_blocks:
                    if cid in task_blocks and task_blocks[cid] != canonical_blocks[cid]:
                        assert bdd_path is not None
                        check.problem(
                            f"{stem}:BDD",
                            f"scenario {cid} differs from {bdd_path.name} (R3)",
                        )

        # R2: Mirror parity check if mirror exists
        features_dir = check.root / ".devtool" / "features"
        done_dir = features_dir / "done"
        mirror_path = features_dir / task_path.name
        if not mirror_path.is_file():
            mirror_path = done_dir / task_path.name
        if mirror_path.is_file():
            prefix = (
                f"](../../epic/{epic_dir}/"
                if mirror_path.parent == done_dir
                else f"](../epic/{epic_dir}/"
            )
            norm_mirror = read_file(mirror_path).replace(prefix, "](")
            if norm_mirror != epic_text:
                check.problem(
                    f"{stem}:Mirror",
                    "features mirror content differs from epic task (R2)",
                )


def repository_root() -> Path:
    done = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if done.returncode != 0:
        raise UsageError("not inside a git repository")
    return Path(done.stdout.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--design", action="store_true")
    parser.add_argument("--allow-existing-done-new", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json", dest="as_json", action="store_true")
    parser.add_argument("--hld", type=Path, default=None)
    parser.add_argument("--tasks", nargs="+", type=Path, default=None)
    parser.add_argument("--check-plan", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.check_plan is not None:
        if args.hld is not None or args.tasks is not None:
            print(
                "error: --check-plan cannot be combined with --hld or --tasks",
                file=sys.stderr,
            )
            return 2
    else:
        if args.hld is None and not args.tasks:
            parser.error("either --check-plan or both --hld and --tasks are required")
        if args.hld is None:
            parser.error("the following arguments are required: --hld")
        if not args.tasks:
            parser.error("the following arguments are required: --tasks")

    program_provenance: dict[str, list[str]] = {}
    try:
        check = Checker(repository_root())
        if args.check_plan is not None:
            plan_text = read_file(args.check_plan)
            program_provenance = check_standalone_plan(
                check, args.check_plan, plan_text
            )
        else:
            assert args.hld is not None and args.tasks is not None
            hld_text = read_file(args.hld)
            tasks = {path: read_file(path) for path in args.tasks}
            prereq_dirs, prereq_errors = tc.resolve_prerequisite_epic_dirs(
                check.root, hld_text, args.hld.parent.name
            )
            for err in prereq_errors:
                check.problem(str(args.hld), err)
            prereq_files, _ = tc.collect_prerequisite_artifacts(check.root, prereq_dirs)
            created = {
                entry.pattern
                for text in tasks.values()
                for entry in tc.parse_allowed_files(text)
                if entry.new
            } | prereq_files
            created |= {
                entry.pattern
                for text in tasks.values()
                for entry in tc.parse_evidence_files(text)
                if entry.new and not Path(entry.pattern).name.startswith("task_")
            }
            check_duplicate_new_claims(check, tasks)
            final_task_path = (
                max(tasks.keys(), key=lambda p: _task_order_key(p, tasks[p]))
                if len(tasks) >= 2
                else None
            )
            for path, text in tasks.items():
                check_task(
                    check,
                    path,
                    text,
                    args.design,
                    created,
                    prereq_files,
                    allow_existing_done_new=args.allow_existing_done_new,
                    is_intermediate_task=(
                        final_task_path is not None and path != final_task_path
                    ),
                )
            check_hld(check, args.hld, hld_text, tasks, created)
            if args.design:
                check_exclusive_ownership(check, tasks)
                check_r2_r3_parity(check, args.hld, tasks)
            for path, text in tasks.items():
                for row in _rows(text):
                    prog = tc.program_of(row.command, check.root)
                    if prog:
                        prov = f"{path.stem}:{row.id}"
                        if prov not in program_provenance.setdefault(prog, []):
                            program_provenance[prog].append(prov)
    except UsageError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    formatted_programs = [
        f"{prog} ({', '.join(program_provenance[prog])})"
        for prog in sorted(program_provenance.keys())
    ]
    if args.as_json:
        payload = {
            "status": "FAIL" if check.problems else "PASS",
            "problems": list(check.problems),
            "warnings": list(check.warnings),
            "implicit_protected_paths": formatted_programs,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 1 if check.problems else 0

    for warning in check.warnings:
        print(warning, file=sys.stderr)
    if check.problems:
        for problem in check.problems:
            print(problem)
        print(
            f"Implicit protected paths: {', '.join(formatted_programs) if formatted_programs else 'none'}"
        )
        print(f"Result: {len(check.problems)} problems — FAIL")
        return 1

    if args.verbose:
        print(
            f"Implicit protected paths: {', '.join(formatted_programs) if formatted_programs else 'none'}"
        )
    print("Result: 0 problems — PASS")
    return 0


def _rows(text: str) -> list[Any]:
    try:
        parsed: tuple[list[Any], Any] = tc.parse_verification(text)
        return list(parsed[0])
    except tc.ContractError:
        return []


if __name__ == "__main__":
    sys.exit(main())
