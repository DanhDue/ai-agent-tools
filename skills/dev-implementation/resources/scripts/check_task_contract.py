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
import importlib
import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
tc: Any = importlib.import_module("task_contract")
cb: Any = importlib.import_module("check_bdd_traceability")
sts: Any = importlib.import_module("sync_task_status")
UsageError: type[Exception] = cb.UsageError
covers_of: Any = cb.covers_of
read_text: Any = cb.read_text

SECTIONS = ("Files", "Verification", "Definition of Done", "Stop and Report If", "Decisions Already Made")
ROW_PREFIX = re.compile(r"^Verification row [^:]+: ")
STATUS = re.compile(r'^status:\s*"?([A-Za-z_-]+)"?\s*$', re.MULTILINE)
GLOB_CHARS = re.compile(r"[*?]")
WEAK_ASSERTION_RE = re.compile(r"\b(should be truthy|is valid|should work|returns non-empty)\b", re.IGNORECASE)
RESERVED_RUNNER_EVIDENCE = re.compile(r"^task_.*\.json$")
NON_PORTABLE_PATH_RE = re.compile(r"(?:/Users/|/home/|~/|\.claude/plugins/cache/|\.gemini/config/plugins/)")


class Checker:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.problems: list[str] = []
        self.warnings: list[str] = []
        listed = subprocess.run(["git", "ls-files", "-z"], check=False, cwd=root, capture_output=True, text=True).stdout
        self.tracked = set(listed.split("\0")) - {""}

    def ignored(self, path: str) -> bool:
        return subprocess.run(["git", "check-ignore", "-q", "--", path], check=False, cwd=self.root,
                              capture_output=True).returncode == 0

    def problem(self, where: str, text: str) -> None:
        self.problems.append(f"{where}: {text}")

    def is_tracked(self, path: str) -> bool:
        return path in self.tracked

    def matches_tracked(self, pattern: str) -> bool:
        return any(tc.path_matches(pattern, name) for name in self.tracked)


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
        check.problem(f"{stem}:Verification", "Verification header must be exactly: | " + " | ".join(tc.HEADER) + " |")
        return []
    rows: list[Any] = []
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


def check_structure(check: Checker, stem: str, path: Path, text: str, rows: list[Any]) -> None:
    for title in SECTIONS:
        if tc.section(text, title) is None:
            check.problem(f"{stem}:{title}", "section is missing")
    if tc.section(text, "Files") is not None and not tc.parse_allowed_files(text):
        check.problem(f"{stem}:Files", "Allowed files lists no entry")
    v_sec = tc.section(text, "Verification")
    if v_sec is not None:
        reason = next((m.group(1) for m in map(tc.RED_NA.match, v_sec.splitlines()) if m), None)
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
    has_executable = any(row.phase in ("RED", "GREEN") for row in rows)
    if has_executable:
        decisions = tc.section(text, "Decisions Already Made")
        clean_decisions = decisions.strip().lower() if decisions else ""
        if not decisions or not clean_decisions or clean_decisions in ("none", "none.", "n/a"):
            check.problem(f"{stem}:Decisions Already Made",
                          "executable task requires grounded facts, cannot be empty or 'None'")


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


def check_evidence(check: Checker, stem: str, text: str, design: bool) -> None:
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
        if design and entry.new and (check.root / pattern).exists():
            check.problem(f"{stem}:Files", f"Evidence file {pattern} is marked (new) but already exists")


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
                    prog_idx = sub_tokens.index(unwrapped[0]) if unwrapped[0] in sub_tokens else 0
                    for idx in range(prog_idx + 1, len(sub_tokens)):
                        tok = sub_tokens[idx]
                        if not tok.startswith("-"):
                            pattern_idx = idx
                            break
            if pattern_idx is not None:
                tokens_to_scan = [t for i, t in enumerate(sub_tokens) if i != pattern_idx]

        for token in tokens_to_scan:
            value = token.split("=", 1)[1] if token.startswith("-") and "=" in token else token
            if "/" in value and not value.startswith("-") and not re.search(r"[*$]|://", value):
                clean_path = value.split("::", 1)[0]
                paths.append(clean_path.removeprefix("./"))

    program = tc.strip_wrappers([t for t in tokens if t not in tc.CONTROL_TOKENS])
    first = program[0] if program else None
    return paths, first if first and "/" not in first else None


def check_grounding(check: Checker, stem: str, text: str, rows: list[Any], created: set[str]) -> None:
    for context in tc.parse_read_only_context(text):
        if not (check.root / context).exists() and context not in created:
            check.problem(f"{stem}:Files", f"Read-only context {context} does not exist and is not (new) in any task")
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
            if not (check.root / path).exists() and not check.ignored(path) and path not in created:
                check.problem(f"{stem}:{row.id}",
                              f"{path} does not exist, is not ignored by git and is not (new) in any task")
        if executable and executable != "d3nexus" and "=" not in executable and shutil.which(executable) is None:
            check.warnings.append(f"warning: {stem}:{row.id}: executable {executable} not found on PATH")


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
        if val is not None and ("::" not in val or not val.split("::", 1)[0].endswith(".py")):
            check.problem(f"{stem}:{row.id}",
                          f"pytest -k expression must use an exact node ID (<file>::<test>), found: {val!r}")


def is_python_task(text: str, rows: list[Any]) -> bool:
    entries = tc.parse_allowed_files(text)
    for entry in entries:
        pat = entry.pattern.lower()
        if pat.endswith(".py") or pat in ("pyproject.toml", "setup.py", "requirements.txt", "pipfile"):
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


def check_python_tier_b(check: Checker, stem: str, rows: list[Any]) -> None:
    tier_b_rows = [r for r in rows if r.phase == "TIER-B"]
    manifest_path = check.root / ".agents" / "quality" / "python-quality.json"
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            check.problem(f"{stem}:Verification", "malformed .agents/quality/python-quality.json manifest")
            return
        if not isinstance(data, dict):
            check.problem(f"{stem}:Verification", "invalid python-quality.json manifest: root must be an object")
            return
        capabilities = data.get("capabilities")
        if not isinstance(capabilities, dict):
            check.problem(f"{stem}:Verification", "invalid python-quality.json manifest: capabilities must be an object")
            return
        lint_cmd = capabilities.get("lint")
        type_check_cmd = capabilities.get("type_check")
        if not isinstance(lint_cmd, list) or not lint_cmd or not all(isinstance(x, str) for x in lint_cmd):
            check.problem(f"{stem}:Verification", "invalid python-quality.json manifest: lint capability missing or invalid")
            return
        if not isinstance(type_check_cmd, list) or not type_check_cmd or not all(isinstance(x, str) for x in type_check_cmd):
            check.problem(f"{stem}:Verification", "invalid python-quality.json manifest: type_check capability missing or invalid")
            return

        def matches_cap(cap: list[str], command: str) -> bool:
            try:
                row_toks = shlex.split(command)
            except ValueError:
                row_toks = command.split()
            if row_toks == cap:
                return True
            if len(cap) > 1 and row_toks[:len(cap) - 1] == cap[:-1]:
                return True
            return bool(len(row_toks) >= len(cap) and row_toks[:len(cap)] == cap)

        has_lint = any(matches_cap(lint_cmd, r.command) for r in tier_b_rows)
        has_type = any(matches_cap(type_check_cmd, r.command) for r in tier_b_rows)
        if not has_lint:
            check.problem(f"{stem}:Verification", f"Python task missing registered lint capability ({' '.join(lint_cmd)})")
        if not has_type:
            check.problem(f"{stem}:Verification", f"Python task missing registered type_check capability ({' '.join(type_check_cmd)})")
        return

    # Fallback tooling: ruff + (mypy / pyright / ty)
    has_ruff = False
    has_type_checker = False
    for r in tier_b_rows:
        try:
            tokens = shlex.split(r.command)
        except ValueError:
            tokens = r.command.split()
        prog = tc.strip_wrappers([t for t in tokens if t not in tc.CONTROL_TOKENS])
        first = prog[0] if prog else ""
        if first == "ruff" or "ruff" in tokens:
            has_ruff = True
        if first in ("mypy", "pyright", "ty") or any(t in ("mypy", "pyright", "ty") for t in tokens):
            has_type_checker = True

    if not has_ruff or not has_type_checker:
        missing_tools: list[str] = []
        if not has_ruff:
            missing_tools.append("lint (ruff)")
        if not has_type_checker:
            missing_tools.append("type-check (mypy/pyright/ty)")
        check.problem(f"{stem}:Verification", f"Python task requires TIER-B direct {', '.join(missing_tools)}")


def check_weak_bdd(check: Checker, source_name: str, text: str) -> None:
    for line_num, line in enumerate(text.splitlines(), start=1):
        m = WEAK_ASSERTION_RE.search(line)
        if m:
            check.problem(f"{source_name}:{line_num}", f"weak BDD assertion found: {m.group(0)!r}")


def check_task(check: Checker, path: Path, text: str, design: bool, created: set[str]) -> None:
    stem = path.stem
    rows = table_rows(check, stem, text)
    check_structure(check, stem, path, text, rows)
    for row in rows:
        if row.expect.results and not check.ignored(row.expect.results):
            check.problem(f"{stem}:{row.id}", f"results path {row.expect.results} is not ignored by git")
        check_pytest_k(check, stem, row)
        check_portable_command(check, stem, row)
    check_weak_bdd(check, stem, text)
    status = STATUS.search(text.split("\n---", 1)[0]) if text.startswith("---") else None
    if design or not (status and status.group(1) == "done"):
        if is_python_task(text, rows):
            check_python_tier_b(check, stem, rows)
        check_allowed(check, stem, text, design)
        check_evidence(check, stem, text, design)
        check_grounding(check, stem, text, rows, created)


def check_hld(check: Checker, hld_path: Path, text: str, tasks: dict[Path, str]) -> None:
    name = hld_path.name
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
    for bdd_path in sorted(hld_path.parent.glob("bdd_scenarios*.md")):
        try:
            content = read_file(bdd_path)
            check_weak_bdd(check, bdd_path.name, content)
        except UsageError:
            pass


def check_r2_r3_parity(check: Checker, hld_path: Path, tasks: dict[Path, str]) -> None:
    epic_dir = hld_path.parent.name
    bdd_path = hld_path.parent / "bdd_scenarios.en.md"
    canonical_blocks: dict[str, list[str]] = {}
    if bdd_path.is_file():
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
                    if cid not in task_blocks or task_blocks[cid] != canonical_blocks[cid]:
                        check.problem(f"{stem}:BDD", f"scenario {cid} differs from bdd_scenarios.en.md (R3)")

        # R2: Mirror parity check if mirror exists
        features_dir = check.root / ".devtool" / "features"
        done_dir = features_dir / "done"
        mirror_path = features_dir / task_path.name
        if not mirror_path.is_file():
            mirror_path = done_dir / task_path.name
        if mirror_path.is_file():
            prefix = f"](../../epic/{epic_dir}/" if mirror_path.parent == done_dir else f"](../epic/{epic_dir}/"
            norm_mirror = read_file(mirror_path).replace(prefix, "](")
            if norm_mirror != epic_text:
                check.problem(f"{stem}:Mirror", "features mirror content differs from epic task (R2)")


def repository_root() -> Path:
    done = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=False, capture_output=True, text=True)
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
        created |= {
            entry.pattern
            for text in tasks.values()
            for entry in tc.parse_evidence_files(text)
            if entry.new and not Path(entry.pattern).name.startswith("task_")
        }
        for path, text in tasks.items():
            check_task(check, path, text, args.design, created)
        check_hld(check, args.hld, hld_text, tasks)
        if args.design:
            check_r2_r3_parity(check, args.hld, tasks)
    except UsageError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    program_provenance: dict[str, list[str]] = {}
    for path, text in tasks.items():
        for row in _rows(text):
            prog = tc.program_of(row.command, check.root)
            if prog:
                prov = f"{path.stem}:{row.id}"
                if prov not in program_provenance.setdefault(prog, []):
                    program_provenance[prog].append(prov)

    formatted_programs = [
        f"{prog} ({', '.join(program_provenance[prog])})"
        for prog in sorted(program_provenance.keys())
    ]
    for warning in check.warnings:
        print(warning, file=sys.stderr)
    for problem in check.problems:
        print(problem)
    print(f"Implicit protected paths: {', '.join(formatted_programs) if formatted_programs else 'none'}")
    print(f"Result: {len(check.problems)} problems — {'FAIL' if check.problems else 'PASS'}")
    return 1 if check.problems else 0


def _rows(text: str) -> list[Any]:
    try:
        parsed: tuple[list[Any], Any] = tc.parse_verification(text)
        return list(parsed[0])
    except tc.ContractError:
        return []


if __name__ == "__main__":
    sys.exit(main())
