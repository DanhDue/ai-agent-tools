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
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from check_bdd_traceability import UsageError, load_scenarios
from result_reports import ReportError, digest, load_reports
from task_contract import (ContractError, Row, changed_paths, epic_layout, evaluate_done_gate, fingerprint, git_run,
                           load_evidence, parse_allowed_files, parse_protected_paths,
                           parse_verification, path_matches, program_of, save_evidence)

TAIL_LINES = 40
VERIFY_PHASES = ("GREEN", "TIER-B", "TIER-C")
STALE = "results not produced by this run"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def newest_result_time(target: Path) -> float | None:
    if target.is_file():
        return target.stat().st_mtime
    if target.is_dir():
        times = [p.stat().st_mtime for pattern in ("*.xml", "*.json") for p in target.rglob(pattern)]
        return max(times, default=None)
    return None


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


def epic_scenario_ids(layout) -> list[str]:
    try:
        return load_scenarios(layout.epic_dir / "bdd_scenarios.en.md")[0]
    except UsageError:
        return []


def attach_digest(results: dict, path: str, root: Path, scenario_ids: list[str]) -> str | None:
    """Store the digest of a fresh report; None on success, else the row's failure reason."""
    try:
        results["digest"] = digest(load_reports([path], root), scenario_ids)
    except ReportError:
        return "results in neither format"
    return None


def run_row(row: Row, root: Path, timeout: int, scenario_ids: list[str]) -> dict:
    record = {"id": row.id, "phase": row.phase, "command": row.command, "expect": row.expect_text,
              "needs": list(row.needs), "exit": None, "outcome": "PASS", "reason": None,
              "started": utc_now(), "finished": None, "output_tail": [],
              "output_sha256": hashlib.sha256(b"").hexdigest()}
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
        if row.expect.results:
            newest = newest_result_time(root / row.expect.results)
            fresh = newest is not None and newest >= started
            record["results"] = {"path": row.expect.results, "fresh": fresh}
            reason = reason or (None if fresh else STALE)
            if fresh:
                reason = reason or attach_digest(record["results"], row.expect.results, root, scenario_ids)
        if reason:
            record.update(outcome="FAIL", reason=reason)
    record["finished"] = utc_now()
    return record


def protected_patterns(layout, root: Path) -> tuple[list[str], set[str]]:
    """Explicit HLD patterns, and the tracked programs every parseable task row in the epic runs."""
    explicit = parse_protected_paths(layout.hld.read_text(encoding="utf-8")) if layout.hld.is_file() else []
    programs: set[str] = set()
    for sibling in sorted(layout.epic_dir.glob("task_*.md")):
        try:
            rows, _ = parse_verification(sibling.read_text(encoding="utf-8"))
        except ContractError:
            continue
        programs.update(p for p in (program_of(row.command, root) for row in rows) if p)
    return explicit, programs


def scope_row(layout, allowed_patterns: list[str]) -> dict:
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


def detail_of(record: dict) -> str:
    if record["id"] == "SCOPE":
        return "; ".join(record["violations"]) or f"{len(record['changed'])} changed path(s) in scope"
    return record["reason"] or f"exit {record['exit']}"


def run(args: argparse.Namespace) -> int:
    layout = epic_layout(args.task)
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
