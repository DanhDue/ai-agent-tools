#!/usr/bin/env python3
"""Gate 4 audit of an epic branch: check every done task's evidence and disclose every change to a grader.

Usage:
  audit_epic.py --epic-dir <epic_dir> --base <base_ref>

The report is printed, never written. Exit codes: 0 nothing fails; 1 missing evidence, a row that is not
PASS, or an unauthorised protected change outside .devtool/; 2 usage error (unknown base, no epic).
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from check_bdd_traceability import COVERS_LINE, scenario_ids
from task_contract import (DIFF_PLAIN, DOD_REFERENCE, EXCLUDE_DEVTOOL, ContractError, dod_bullets, git_run,
                           parse_allowed_files, parse_protected_paths, parse_verification, path_matches,
                           program_of, row_problems, section)

STATUS = re.compile(r"""^status:\s*["'`]?([\w-]+)["'`]?\s*(?:#.*)?$""", re.M)
GRADER_LINES = ("Protected paths:", "Integration results:")


@dataclass(frozen=True)
class Commit:
    sha: str
    short: str
    title: str
    paths: tuple[str, ...]


def git_lines(root: Path, *args: str) -> list[str]:
    return git_run(root, *args).decode("utf-8", "replace").splitlines()


def show(root: Path, rev: str, path: str) -> str | None:
    try:
        return git_run(root, "show", f"{rev}:{path}").decode("utf-8")
    except ContractError:
        return None


def status_of(text: str) -> str | None:
    """The frontmatter status, quoted or not, with any trailing comment dropped."""
    head = re.match(r"---\n(.*?)\n---", text, re.S)
    found = STATUS.search(head.group(1)) if head else None
    return found.group(1) if found else None


def marked_done(root: Path, mirror: str, text: str) -> bool:
    """True when the mirror or the task's features copy at HEAD says done."""
    stem = Path(mirror).stem
    copies = [text] + [show(root, "HEAD", f".devtool/features/{folder}{stem}.md") or "" for folder in ("", "done/")]
    return any(status_of(copy) == "done" for copy in copies)


def patch_id(root: Path, commit: str) -> str | None:
    diff = git_run(root, "diff", *DIFF_PLAIN, f"{commit}^", commit, "--", ".", EXCLUDE_DEVTOOL)
    found = git_run(root, "patch-id", "--stable", stdin=diff).decode().split() if diff else []
    return found[0] if found else None


def load_commits(root: Path, base: str) -> list[Commit]:
    commits: list[Commit] = []
    for line in git_lines(root, "log", "--reverse", "--format=%H%x09%h%x09%s", f"{base}..HEAD"):
        sha, short, title = line.split("\t", 2)
        paths = git_run(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", sha)
        commits.append(Commit(sha, short, title, tuple(p for p in paths.decode("utf-8", "replace").split("\0") if p)))
    return commits


def well_formed(data: object) -> bool:
    runs = data.get("runs") if isinstance(data, dict) else None
    return isinstance(runs, dict) and all(
        isinstance(run, dict) and isinstance(run.get("rows"), list)
        and all(isinstance(r, dict) and "id" in r and "outcome" in r for r in run["rows"])
        for run in runs.values())


def audit_evidence(root: Path, epic_path: str, base: str, stem: str, text: str) -> tuple[list[str], bool]:
    evidence_path = f"{epic_path}/evidence/{stem}.json"
    raw = show(root, "HEAD", evidence_path)
    if raw is None:
        return [f"{stem}: missing evidence"], True
    try:
        data = json.loads(raw)
        rows, red_na = parse_verification(text)
    except ValueError:
        return [f"{stem}: malformed evidence"], True
    except ContractError as error:
        return [f"{stem}: task table unreadable ({error})"], True
    if not well_formed(data):
        return [f"{stem}: malformed evidence"], True
    runs = data["runs"]
    needed = ["verify"] + (["red"] if red_na is None and any(r.phase == "RED" for r in rows) else [])
    absent = [f"{stem}: missing evidence ({kind} run)" for kind in needed if kind not in runs]
    if absent:
        return absent, True
    try:
        problems = [f"{stem}: {p}" for p in row_problems(rows, runs)]
    except (KeyError, TypeError):
        return [f"{stem}: malformed evidence"], True
    problems += [f"{stem}: row {record['id']} not PASS" for run in runs.values() for record in run["rows"]
                 if record["outcome"] != "PASS"]
    commit = next(iter(git_lines(root, "log", "-1", "--format=%H", f"{base}..HEAD", "--", evidence_path)), None)
    if commit and patch_id(root, commit) != runs["verify"].get("patch_id"):
        return problems + [f"{stem}: patch changed after verify"], bool(problems)
    return problems or [f"{stem}: PASS"], bool(problems)


def audit_protected(root: Path, epic_path: str, commits: list[Commit], texts: dict[str, str]) -> tuple[list[str], bool]:
    explicit = parse_protected_paths(show(root, "HEAD", f"{epic_path}/{Path(epic_path).name}.en.md") or "")
    programs: set[str] = set()
    allowed: set[str] = set()
    for text in texts.values():
        allowed.update(entry.pattern for entry in parse_allowed_files(text))
        try:
            programs.update(p for p in (program_of(row.command, root) for row in parse_verification(text)[0]) if p)
        except ContractError:
            continue
    items: list[str] = []
    failed = False
    for commit in commits:
        for path in commit.paths:
            if path not in programs and not any(path_matches(pattern, path) for pattern in explicit):
                continue
            unauthorised = not path.startswith(".devtool/") and path not in allowed
            items.append(f"{commit.short} {path}" + (" — unauthorised" if unauthorised else ""))
            failed = failed or unauthorised
    return items, failed


def grader_text(text: str) -> list[str]:
    covers = [line for line in text.splitlines() if COVERS_LINE.match(line)]
    allowed = [f"`{entry.pattern}`" + (" (new)" if entry.new else "") for entry in parse_allowed_files(text)]
    return (["# Verification"] + (section(text, "Verification") or "").splitlines()
            + ["# Definition of Done"] + (section(text, "Definition of Done") or "").splitlines()
            + ["# Allowed files"] + allowed + ["# Covers"] + covers)


def scenario_ids_at(root: Path, rev: str, path: str) -> set[str]:
    text = show(root, rev, path)
    if text is None:
        return set()
    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / "scenarios.md"
        copy.write_text(text, encoding="utf-8")
        return set(scenario_ids(copy)[0])


def audit_amendments(root: Path, epic_path: str, base: str, texts: dict[str, str]) -> list[str]:
    items: list[str] = []
    for path, text in texts.items():
        created = git_lines(root, "log", "--diff-filter=A", "--format=%H", "--", path)
        original = show(root, created[-1], path) if created else None
        if original is None or grader_text(original) == grader_text(text):
            continue
        diff = difflib.unified_diff(grader_text(original), grader_text(text), f"{Path(path).stem} at creation",
                                    f"{Path(path).stem} at HEAD", lineterm="", n=1)
        since = git_lines(root, "log", "--format=%h %s", f"{created[-1]}..HEAD", "--", path)
        items.append("\n  ".join([f"{Path(path).stem}: amended since creation", *diff,
                                  *(f"changed by {entry}" for entry in since)]))
    scenarios = f"{epic_path}/bdd_scenarios.en.md"
    before, after = scenario_ids_at(root, base, scenarios), scenario_ids_at(root, "HEAD", scenarios)
    items += [f"scenario {i} added" for i in sorted(after - before)]
    items += [f"scenario {i} removed" for i in sorted(before - after)]
    return items + hld_amendments(root, epic_path, base)


def hld_amendments(root: Path, epic_path: str, base: str) -> list[str]:
    """The HLD's Protected paths: and Integration results: lines, diffed between <base> and HEAD."""
    hld = f"{epic_path}/{Path(epic_path).name}.en.md"
    lines = {rev: [line for line in (show(root, rev, hld) or "").splitlines() if line.startswith(GRADER_LINES)]
             for rev in (base, "HEAD")}
    if lines[base] == lines["HEAD"]:
        return []
    diff = difflib.unified_diff(lines[base], lines["HEAD"], f"{Path(hld).name} at base", f"{Path(hld).name} at HEAD",
                                lineterm="", n=0)
    since = git_lines(root, "log", "--format=%h %s", f"{base}..HEAD", "--", hld)
    return ["\n  ".join([f"{Path(hld).name}: Protected paths or Integration results changed since base", *diff,
                         *(f"changed by {entry}" for entry in since)])]


def build_report(root: Path, epic_dir: str, base: str) -> tuple[list[tuple[str, list[str]]], bool]:
    epic_path = f".devtool/epic/{epic_dir}"
    mirrors = [p for p in git_lines(root, "ls-tree", "--name-only", "HEAD", "--", f"{epic_path}/")
               if re.fullmatch(r"task_.*\.md", Path(p).name)]
    if not mirrors:
        raise ContractError(f"no task mirrors for epic {epic_dir} at HEAD under {epic_path}/")
    texts = {path: show(root, "HEAD", path) or "" for path in mirrors}
    commits = load_commits(root, base)
    task_commits = {c.sha for c in commits if any(p.startswith(f"{epic_path}/evidence/") for p in c.paths)}
    evidence: list[str] = []
    legacy: list[str] = []
    failed = False
    for path, text in texts.items():
        if not marked_done(root, path, text):
            continue
        if section(text, "Verification") is None:
            legacy.append(f"{Path(path).stem}: legacy — no evidence")
        else:
            items, bad = audit_evidence(root, epic_path, base, Path(path).stem, text)
            evidence += items
            failed = failed or bad
    protected, bad = audit_protected(root, epic_path, commits, texts)
    outside = [f"{c.short} {c.title}" for c in commits
               if c.sha not in task_commits and any(not p.startswith(".devtool/") for p in c.paths)]
    gate5 = [f"{Path(path).stem}: {bullet}" for path, text in texts.items() for bullet in dod_bullets(text)
             if (reference := DOD_REFERENCE.search(bullet)) and reference.group(1) == "Gate 5"]
    sections = [("Evidence", evidence), ("Legacy tasks", legacy), ("Protected paths", protected),
                ("Grader amendments", audit_amendments(root, epic_path, base, texts)),
                ("Commits outside tasks", outside), ("Gate 5 items", gate5)]
    return sections, failed or bad


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--epic-dir", required=True)
    parser.add_argument("--base", required=True)
    args = parser.parse_args(argv)
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if top.returncode != 0:
            raise ContractError("not inside a git repository")
        root = Path(top.stdout.strip())
        base = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{args.base}^{{commit}}"], cwd=root,
                              capture_output=True, text=True)
        if base.returncode != 0 or args.base.startswith("-"):
            raise ContractError(f"unknown base reference: {args.base}")
        sections, failed = build_report(root, args.epic_dir, base.stdout.strip())
    except ContractError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for name, items in sections:
        print(f"### {name}")
        print("\n".join(f"- {item}" for item in items) if items else "None")
        print()
    print(f"Result: {'FAIL' if failed else 'PASS'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
