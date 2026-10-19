#!/usr/bin/env python3
"""Run a task's Verification rows and record the outcome as evidence.

Usage:
  run_task_checks.py red    <task mirror> [--timeout 1800]
  run_task_checks.py verify <task mirror> [--timeout 1800]
  run_task_checks.py status <task mirror>   (read-only: print the recorded runs and the done-gate verdict)

Exit codes: 0 every row passed (status: the done gate passes); 1 a row failed (evidence still written) or
the done gate fails; 2 usage error or a task
file the parser rejects (no evidence written).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import os
import re
import shlex
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

_tc: Any = importlib.import_module("task_contract")
CONTROL_TOKENS: set[str] = _tc.CONTROL_TOKENS
ContractError: type[Exception] = _tc.ContractError
EpicLayout: Any = _tc.EpicLayout
Row: Any = _tc.Row
changed_paths: Any = _tc.changed_paths
epic_layout: Any = _tc.epic_layout
evaluate_done_gate: Any = _tc.evaluate_done_gate
fingerprint: Any = _tc.fingerprint
git_run: Any = _tc.git_run
load_evidence: Any = _tc.load_evidence
parse_allowed_files: Any = _tc.parse_allowed_files
parse_protected_paths: Any = _tc.parse_protected_paths
parse_verification: Any = _tc.parse_verification
path_matches: Any = _tc.path_matches
program_of: Any = _tc.program_of
save_evidence: Any = _tc.save_evidence
section: Any = _tc.section
strip_wrappers: Any = _tc.strip_wrappers

_rr: Any = importlib.import_module("result_reports")
ReportError: type[Exception] = _rr.ReportError
digest: Any = _rr.digest
load_files: Any = _rr.load_files
report_files: Any = _rr.report_files

_cbt: Any = importlib.import_module("check_bdd_traceability")
UsageError: type[Exception] = _cbt.UsageError
load_scenarios: Any = _cbt.load_scenarios

TAIL_LINES = 40
VERIFY_PHASES = ("GREEN", "TIER-B", "TIER-C")
STALE = "results not produced by this run"

INVALID_PYTEST_RED_REASON = (
    "Invalid pytest RED phase: must fail on a collected test (exit 1 or 2), "
    "not missing file (exit 4) or zero selected tests (exit 5)."
)

FORBIDDEN_MARKERS = (
    re.compile(r"ERROR:\s*file or directory not found", re.IGNORECASE),
    re.compile(r"collected\s+0\s+items", re.IGNORECASE),
    re.compile(r"/\s*0\s+selected\b", re.IGNORECASE),
)
POSITIVE_FAILURE_SUMMARY = re.compile(r"\b([1-9]\d*)\s+(?:failed|error|errors)\b", re.IGNORECASE)
COVERS_LINE_RE = re.compile(r"^\s*(?:[-*]\s+)?\**Covers\**\s*:\**\s*(.*)$")
ID_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9-])[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]+(?![A-Za-z0-9])")


def is_pytest_command(command: str) -> bool:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return False
    subcommands: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in CONTROL_TOKENS:
            if current:
                subcommands.append(current)
                current = []
        else:
            current.append(token)
    if current:
        subcommands.append(current)

    for sub in subcommands:
        sub = strip_wrappers(sub)
        if not sub:
            continue
        prog = Path(sub[0]).name
        if prog == "pytest":
            return True
        if (
            (prog in ("python", "python3") or prog.startswith("python3."))
            and len(sub) >= 3
            and sub[1] == "-m"
            and sub[2] == "pytest"
        ):
            return True
    return False


def validate_pytest_red(command: str, exit_code: int | None, output_text: str) -> str | None:
    """Evaluate whether a pytest RED execution is genuine.

    Returns None if valid or not a pytest command.
    Returns INVALID_PYTEST_RED_REASON if it is an invalid pytest RED run.
    """
    if not is_pytest_command(command):
        return None
    if exit_code not in (1, 2):
        return INVALID_PYTEST_RED_REASON
    for marker in FORBIDDEN_MARKERS:
        if marker.search(output_text):
            return INVALID_PYTEST_RED_REASON
    if not POSITIVE_FAILURE_SUMMARY.search(output_text):
        return INVALID_PYTEST_RED_REASON
    return None


def parse_covers(text: str) -> list[str]:
    found: list[str] = []
    for line in text.splitlines():
        match = COVERS_LINE_RE.match(line)
        if match:
            found.extend(ID_TOKEN_RE.findall(match.group(1)))
    return found


def core_sections(text: str) -> tuple[str | None, str | None, str | None, list[str]]:
    return (
        section(text, "Files"),
        section(text, "Verification"),
        section(text, "Definition of Done"),
        parse_covers(text),
    )


def check_task_tamper(task_path: Path | str, layout: EpicLayout) -> None:
    path = Path(task_path)
    features_task = layout.root / ".devtool" / "features" / path.name
    if not features_task.is_file():
        features_task = layout.root / ".devtool" / "features" / "done" / path.name

    if not features_task.is_file():
        return

    active_text = features_task.read_text(encoding="utf-8")
    active_core = core_sections(active_text)

    mirror_text = path.read_text(encoding="utf-8")
    mirror_core = core_sections(mirror_text)

    if active_core != mirror_core:
        raise ContractError(
            f"TASK_TAMPERED_ERROR: active task '{features_task.name}' core sections altered from epic mirror"
        )

    head_text = committed_text(layout.root, path)
    if head_text is not None:
        head_core = core_sections(head_text)
        if active_core != head_core or mirror_core != head_core:
            raise ContractError(
                f"TASK_TAMPERED_ERROR: task '{path.name}' core sections altered from HEAD"
            )


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def fresh_reports(path: str, root: Path, since: float) -> list[Path]:
    """The report files under a results path that were written at or after `since`; older ones never count."""
    try:
        files = report_files(path, root)
    except ReportError:
        return []
    return [file for file in files if file.stat().st_mtime >= since]


def run_command(command: str, root: Path, timeout: int) -> tuple[int | None, bytes]:
    """Run one row; the exit code is None when the process group had to be killed."""
    process = subprocess.Popen(["bash", "-o", "pipefail", "-c", command], cwd=root, start_new_session=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        output, _ = process.communicate(timeout=timeout)
        return process.returncode, output
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        output, _ = process.communicate()
        return None, output


def mismatch(row: Row, code: int, text: str) -> str | None:
    expect = row.expect
    if expect.nonzero and code == 0:
        return "exit 0, expected non-zero"
    if expect.exit_code is not None and code != expect.exit_code:
        return f"exit {code}, expected {expect.exit_code}"
    missing = next((t for t in expect.contains if t not in text), None)
    return None if missing is None else f'output lacks "{missing}"'


def epic_scenario_ids(layout: EpicLayout) -> list[str]:
    try:
        return cast(list[str], load_scenarios(layout.epic_dir / "bdd_scenarios.en.md")[0])
    except UsageError:
        return []


def attach_digest(results: dict[str, Any], files: list[Path], scenario_ids: list[str]) -> str | None:
    """Store the digest of the fresh reports; None on success, else the row's failure reason."""
    try:
        results["digest"] = digest(load_files(files), scenario_ids)
    except ReportError:
        return "results in neither format"
    return None


def run_row(row: Row, root: Path, timeout: int, scenario_ids: list[str]) -> dict[str, Any]:
    record: dict[str, Any] = {
        "id": row.id,
        "phase": row.phase,
        "command": row.command,
        "expect": row.expect_text,
        "needs": list(row.needs),
        "exit": None,
        "outcome": "PASS",
        "reason": None,
        "started": utc_now(),
        "finished": None,
        "output_tail": [],
        "output_sha256": hashlib.sha256(b"").hexdigest(),
    }
    unset = next((name for name in row.needs if not os.environ.get(name)), None)
    if unset:
        record.update(outcome="BLOCKED", reason=f"unset: {unset}")
    else:
        started = time.time()
        code, output = run_command(row.command, root, timeout)
        text = output.decode("utf-8", "replace")
        record.update(exit=code, output_tail=text.splitlines()[-TAIL_LINES:],
                      output_sha256=hashlib.sha256(output).hexdigest())
        reason = f"timeout after {timeout} s" if code is None else mismatch(row, code, text)
        if row.phase == "RED":
            pytest_err = validate_pytest_red(row.command, code, text)
            if pytest_err:
                reason = pytest_err
        if row.expect.results:
            files = fresh_reports(row.expect.results, root, started)
            record["results"] = {"path": row.expect.results, "fresh": bool(files)}
            reason = reason or (None if files else STALE)
            if files:
                reason = reason or attach_digest(record["results"], files, scenario_ids)
        if reason:
            record.update(outcome="FAIL", reason=reason)
    record["finished"] = utc_now()
    return record


def committed_text(root: Path, path: Path) -> str | None:
    """The file as HEAD has it, so a task cannot weaken its own protection; the working copy only when new."""
    try:
        abs_path = path if path.is_absolute() else (root / path)
        rel_posix = abs_path.resolve().relative_to(root.resolve()).as_posix()
        return cast(str, git_run(root, "show", f"HEAD:{rel_posix}").decode("utf-8"))
    except (ContractError, ValueError):
        return path.read_text(encoding="utf-8") if path.is_file() else None


def protected_patterns(layout: EpicLayout, root: Path) -> tuple[list[str], set[str]]:
    """Explicit HLD patterns, and the tracked programs every parseable task row in the epic runs, read from HEAD."""
    hld = committed_text(root, layout.hld)
    explicit = parse_protected_paths(hld) if hld else []
    folder = layout.epic_dir.relative_to(root).as_posix()
    committed = git_run(root, "ls-tree", "-z", "--name-only", "HEAD", "--", f"{folder}/").decode().split("\0")
    names = {Path(p).name for p in committed if p} | {p.name for p in layout.epic_dir.glob("task_*.md")}
    programs: set[str] = set()
    for name in sorted(n for n in names if re.fullmatch(r"task_.*\.md", n)):
        try:
            rows, _ = parse_verification(committed_text(root, layout.epic_dir / name) or "")
        except ContractError:
            continue
        programs.update(p for p in (program_of(row.command, root) for row in rows) if p)
    return explicit, programs


def scope_row(layout: EpicLayout, allowed_patterns: list[str]) -> dict[str, Any]:
    explicit, programs = protected_patterns(layout, layout.root)
    changed: list[str] = []
    violations: list[str] = []
    exact = {p for p in allowed_patterns if not any(c in p for c in "*?")}
    for path in sorted(set(changed_paths(layout.root))):
        protected = path in programs or any(path_matches(pattern, path) for pattern in explicit)
        if path.startswith(".devtool/") and not protected:
            continue
        changed.append(path)
        if protected:
            if path not in exact:
                violations.append(f"protected path not named exactly in Allowed files: {path}")
        elif not any(path_matches(pattern, path) for pattern in allowed_patterns):
            violations.append(f"outside Allowed files: {path}")
    return {"id": "SCOPE", "phase": "SCOPE", "outcome": "FAIL" if violations else "PASS",
            "changed": changed, "violations": violations}


def detail_of(record: dict[str, Any]) -> str:
    if record["id"] == "SCOPE":
        return "; ".join(record["violations"]) or f"{len(record['changed'])} changed path(s) in scope"
    return record["reason"] or f"exit {record['exit']}"


def run(args: argparse.Namespace) -> int:
    layout = epic_layout(args.task)
    check_task_tamper(args.task, layout)
    task_text = Path(args.task).read_text(encoding="utf-8")
    rows, red_na = parse_verification(task_text)
    allowed = parse_allowed_files(task_text)
    if args.mode == "red":
        selected = [row for row in rows if row.phase == "RED"]
        if red_na is not None or not selected:
            raise ContractError("task has no RED rows to run (RED: n/a or no RED row)")
    else:
        selected = [row for row in rows if row.phase in VERIFY_PHASES]
    started = utc_now()
    scenario_ids = epic_scenario_ids(layout)
    records = [run_row(row, layout.root, args.timeout, scenario_ids) for row in selected]
    if args.mode == "verify":
        records.append(scope_row(layout, [entry.pattern for entry in allowed]))
    tree, patch_id = fingerprint(layout.root)
    head = git_run(layout.root, "rev-parse", "HEAD").decode().strip()
    evidence = load_evidence(layout.evidence) or {"schema": 1, "task": Path(args.task).stem, "runs": {}}
    evidence["runs"][args.mode] = {"head": head, "tree": tree, "patch_id": patch_id, "started": started,
                                   "finished": utc_now(), "rows": records}
    save_evidence(layout.evidence, evidence)
    for record in records:
        print(f"{record['id']} {record['phase']} {record['outcome']} {detail_of(record)}")
    passed = all(record["outcome"] == "PASS" for record in records)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    print(f"Evidence: {layout.evidence}")
    return 0 if passed else 1


def status(args: argparse.Namespace) -> int:
    layout = epic_layout(args.task)
    evidence = load_evidence(layout.evidence) or {}
    for kind, run in evidence.get("runs", {}).items():
        print(f"{kind}: head {run['head']} tree {run['tree']}")
        for record in run["rows"]:
            print(f"  {record['id']} {record['phase']} {record['outcome']}")
    failures = evaluate_done_gate(args.task)
    print("done gate: " + ("FAIL" if failures else "PASS"))
    for failure in failures:
        print(f"  {failure}")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("red", "verify", "status"))
    parser.add_argument("task", type=Path)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args(argv)
    try:
        if not args.task.is_file():
            raise ContractError(f"task file not found: {args.task}")
        return status(args) if args.mode == "status" else run(args)
    except ContractError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
