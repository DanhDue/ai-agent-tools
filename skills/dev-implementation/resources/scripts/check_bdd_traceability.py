#!/usr/bin/env python3
"""Check that every epic BDD scenario is assigned to a task and covered by an integration test.

Usage:
  check_bdd_traceability.py plan  --scenarios <bdd_scenarios.en.md> --tasks <task_*.md ...>
  check_bdd_traceability.py tests --scenarios <bdd_scenarios.en.md> --roots <dir ...> [--ids <ID ...>]

Exit codes: 0 all covered; 1 traceability failure; 2 usage error.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ID_SHAPE = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]+")
SCENARIO_KEYWORDS = (
    "Scenario Outline", "Scenario Template", "Scenario", "Example",
    "Khung tình huống", "Khung kịch bản", "Tình huống", "Kịch bản",
)
SCENARIO_LINE = re.compile(
    r"^\s*(?:" + "|".join(re.escape(keyword) for keyword in SCENARIO_KEYWORDS) + r")\s*:\s*(.*)$"
)
LEADING_TAG = re.compile(r"^\[([^\]]*)\]")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*(\S*)")
COVERS_LINE = re.compile(r"^\s*(?:[-*]\s+)?\**Covers\**\s*:\**\s*(.*)$")
ID_TOKEN = re.compile(r"(?<![A-Za-z0-9-])" + ID_SHAPE.pattern + r"(?![A-Za-z0-9])")


class UsageError(Exception):
    """Missing input: exit 2."""


def read_text(path: Path) -> str:
    """Read a scenario document or task file; anything but UTF-8 is a usage error."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise UsageError(f"{path} is not valid UTF-8") from None


def scenario_ids(path: Path) -> tuple[list[str], list[str]]:
    """Identifiers in document order, and the problems found, for one scenario document."""
    ids: list[str] = []
    problems: list[str] = []
    fence_marker: str | None = None
    in_gherkin = False
    for number, line in enumerate(read_text(path).splitlines(), start=1):
        fence = FENCE.match(line)
        if fence and fence_marker is None:
            fence_marker, in_gherkin = fence.group(1), fence.group(2).lower() == "gherkin"
            continue
        if (fence and fence.group(1)[0] == fence_marker[0]
                and len(fence.group(1)) >= len(fence_marker) and not fence.group(2)):
            fence_marker, in_gherkin = None, False
            continue
        match = SCENARIO_LINE.match(line) if in_gherkin else None
        if not match:
            continue
        tag = LEADING_TAG.match(match.group(1).strip())
        if not tag:
            problems.append(f"{path}:{number}: scenario has no identifier")
        elif not ID_SHAPE.fullmatch(tag.group(1)):
            problems.append(f"{path}:{number}: malformed identifier [{tag.group(1)}]")
        elif tag.group(1) in ids:
            problems.append(f"{path}:{number}: duplicate identifier {tag.group(1)}")
        else:
            ids.append(tag.group(1))
    return ids, problems


def load_scenarios(path: Path) -> tuple[list[str], list[str]]:
    """Validate the English document and, when present, its Vietnamese sibling."""
    if not path.is_file():
        raise UsageError(f"scenario document not found: {path}")
    ids, problems = scenario_ids(path)
    if not ids and not problems:
        problems.append(f"{path}: no scenarios found inside gherkin fences")
    if path.name.endswith(".en.md"):
        sibling = path.with_name(path.name[: -len(".en.md")] + ".vi.md")
        if sibling.is_file():
            vi_ids, vi_problems = scenario_ids(sibling)
            problems.extend(vi_problems)
            missing = sorted(set(ids) - set(vi_ids))
            extra = sorted(set(vi_ids) - set(ids))
            if missing:
                problems.append(f"{sibling}: missing identifiers {', '.join(missing)}")
            if extra:
                problems.append(f"{sibling}: identifiers not in {path.name}: {', '.join(extra)}")
    return ids, problems


def covers_of(path: Path) -> list[str]:
    """Identifiers named on every Covers: line of one task file."""
    found: list[str] = []
    for line in read_text(path).splitlines():
        match = COVERS_LINE.match(line)
        if match:
            found.extend(ID_TOKEN.findall(match.group(1)))
    return found


def check_plan(ids: list[str], task_paths: list[Path]) -> tuple[dict[str, list[str]], list[str]]:
    coverage: dict[str, list[str]] = {identifier: [] for identifier in ids}
    problems: list[str] = []
    for path in task_paths:
        if not path.is_file():
            raise UsageError(f"task file not found: {path}")
        for identifier in covers_of(path):
            if identifier not in coverage:
                problems.append(f"{path}: Covers names unknown identifier {identifier}")
            elif path.name not in coverage[identifier]:
                coverage[identifier].append(path.name)
    return coverage, problems


def reference_pattern(identifier: str) -> re.Pattern[str]:
    """Match an identifier in any case, with - and _ interchangeable, not inside a longer token."""
    body = "[-_]".join(re.escape(part) for part in identifier.split("-"))
    return re.compile(r"(?<![A-Za-z0-9])" + body + r"(?![A-Za-z0-9])", re.IGNORECASE)


def stale_pattern(ids: list[str]) -> re.Pattern[str]:
    """Uppercase hyphenated tokens shaped like this document's identifiers: same prefix, same segment count."""
    shapes = sorted({(identifier.split("-")[0], identifier.count("-")) for identifier in ids})
    alternatives = "|".join(re.escape(prefix) + "(?:-[A-Z0-9]+)" * (hyphens - 1) + "-[0-9]+"
                            for prefix, hyphens in shapes)
    return re.compile(r"(?<![A-Za-z0-9-])(?:" + alternatives + r")(?![A-Za-z0-9-])")


def listed_files(root: Path) -> list[Path] | None:
    """Files git lists under root — tracked, plus untracked but not ignored — or None outside git."""
    try:
        listed = subprocess.run(["git", "-C", str(root), "ls-files", "--cached", "--others",
                                 "--exclude-standard", "-z"], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return [root / name for name in listed.stdout.decode("utf-8", "surrogateescape").split("\0") if name]


def integration_files(roots: list[Path]) -> tuple[list[Path], list[str]]:
    existing = [root for root in roots if root.is_dir()]
    warnings = [f"warning: integration test root not found, skipped: {root}"
                for root in roots if not root.is_dir()]
    if not existing:
        raise UsageError("none of the integration test roots exists: " + ", ".join(map(str, roots)))
    files: list[Path] = []
    for root in existing:
        listed = listed_files(root)
        candidates = sorted(listed) if listed is not None else sorted(root.rglob("*"))
        files.extend(path for path in candidates if path.is_file() and path.suffix.lower() != ".md")
    return files, warnings


def check_tests(ids: list[str], selected: list[str], roots: list[Path],
                check_stale: bool) -> tuple[dict[str, list[str]], list[str], list[str]]:
    patterns = {identifier: reference_pattern(identifier) for identifier in selected}
    coverage: dict[str, list[str]] = {identifier: [] for identifier in selected}
    stale = stale_pattern(ids)
    known = set(ids)
    problems: list[str] = []
    files, warnings = integration_files(roots)
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, start=1):
            for identifier, pattern in patterns.items():
                if pattern.search(line):
                    coverage[identifier].append(f"{path}:{number}")
            if check_stale:
                problems.extend(f"{path}:{number}: stale reference {token}"
                                for token in stale.findall(line) if token not in known)
    return coverage, problems, warnings


def split_values(values: list[str] | None) -> list[str]:
    """Accept space- or comma-separated values, as copied from an HLD or Covers: line."""
    return [part.strip() for value in values or [] for part in value.split(",") if part.strip()]


def report(coverage: dict[str, list[str]], problems: list[str], warnings: list[str]) -> int:
    width = max((len(identifier) for identifier in coverage), default=0)
    for identifier, places in coverage.items():
        print(f"{identifier.ljust(width)}    {', '.join(places) if places else '(none)'}")
    for warning in warnings:
        print(warning, file=sys.stderr)
    for problem in problems:
        print(problem)
    covered = sum(1 for places in coverage.values() if places)
    failed = bool(problems) or covered < len(coverage)
    print(f"Result: {covered}/{len(coverage)} covered — {'FAIL' if failed else 'PASS'}")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    modes = parser.add_subparsers(dest="mode", required=True)
    plan = modes.add_parser("plan", help="every scenario is assigned to at least one task")
    plan.add_argument("--scenarios", required=True, type=Path)
    plan.add_argument("--tasks", required=True, nargs="+", type=Path)
    tests = modes.add_parser("tests", help="every scenario has at least one integration test")
    tests.add_argument("--scenarios", required=True, type=Path)
    tests.add_argument("--roots", required=True, nargs="+")
    tests.add_argument("--ids", nargs="+")
    args = parser.parse_args(argv)
    try:
        ids, problems = load_scenarios(args.scenarios)
        if problems:
            print("\n".join(problems))
            print("Result: scenario document invalid — FAIL")
            return 1
        if args.mode == "plan":
            coverage, problems = check_plan(ids, args.tasks)
            return report(coverage, problems, [])
        roots = [Path(value) for value in split_values(args.roots)]
        selected = split_values(args.ids) or ids
        unknown = [f"--ids names unknown identifier {identifier}"
                   for identifier in selected if identifier not in ids]
        known_selected = [identifier for identifier in selected if identifier in ids]
        coverage, problems, warnings = check_tests(ids, known_selected, roots, not args.ids)
        return report(coverage, unknown + problems, warnings)
    except UsageError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
