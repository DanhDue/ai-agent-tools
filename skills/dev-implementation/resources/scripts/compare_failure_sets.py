#!/usr/bin/env python3
"""Compare failure sets against a recorded baseline to detect regressions.

Usage:
  compare_failure_sets.py --baseline <file>
                          [--current <file>]
                          [--output|--out <report_file>]
                          [--runner auto|pytest|node]
                          [--rerun-new]
                          [--allow-isolated-pass]
                          [--rerun-cmd <cmd_prefix>]
                          [--restore <path> ...]
                          [--cwd <dir>]
                          [-- <command...>]
"""
from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
from pathlib import Path

from record_failure_baseline import (
    detect_runner,
    extract_node_failures,
    extract_pytest_failures,
    run_command_with_restore,
)


def load_failure_set(path: Path) -> set[str]:
    """Load failure identifiers from a baseline or current failure set file."""
    path = Path(path)
    if not path.is_file():
        return set()
    failures: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            failures.add(line)
    return failures


def compare_failure_sets(
    baseline_path: Path,
    current_path: Path | None = None,
    current_failures: set[str] | None = None,
) -> tuple[int, list[str]]:
    """Compare baseline and current failure sets. Returns (exit_code, new_failures)."""
    baseline_set = load_failure_set(baseline_path)
    if current_failures is not None:
        current_set = set(current_failures)
    elif current_path is not None:
        current_set = load_failure_set(current_path)
    else:
        current_set = set()

    new_failures = sorted(current_set - baseline_set)
    exit_code = 0 if not new_failures else 1
    return exit_code, new_failures


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare failure sets against a baseline.")
    parser.add_argument("--baseline", required=True, help="Path to baseline failures file")
    parser.add_argument("--current", default=None, help="Path to current failures file")
    parser.add_argument("--output", "--out", dest="output", default=None, help="Path to output report")
    parser.add_argument("--runner", choices=("auto", "pytest", "node"), default="auto")
    parser.add_argument("--rerun-new", action="store_true", help="Re-run new failure candidates in isolation")
    parser.add_argument("--allow-isolated-pass", action="store_true", help="Treat candidates that pass in isolation as non-regressions")
    parser.add_argument("--rerun-cmd", default=None, help="Command prefix for rerun (default: python3 -m pytest or node --test)")
    parser.add_argument("--restore", dest="restore", action="append", default=[], help="Tracked file to restore")
    parser.add_argument("--cwd", dest="cwd", default=None, help="Working directory")
    parser.add_argument("command_tail", nargs="*", help="Command to run after -- to generate current failures")
    return parser.parse_args(argv)


def rerun_candidate(
    node_id: str,
    runner: str,
    rerun_cmd_prefix: str,
    cwd: Path,
) -> tuple[int, str]:
    """Run candidate failure in isolation using subprocess without shell=True."""
    cmd_tokens = shlex.split(rerun_cmd_prefix)
    if runner == "node":
        if "::" not in node_id:
            raise ValueError(f"Node failure identifier '{node_id}' missing '<file>::' prefix required for isolated rerun")
        file_path, test_name = node_id.split("::", 1)
        full_cmd = [*cmd_tokens, f"--test-name-pattern=^{re.escape(test_name)}$", file_path]
    else:
        full_cmd = [*cmd_tokens, node_id]

    proc = subprocess.run(
        full_cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + ("\n" + proc.stderr if proc.stderr else "")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    cwd = Path(args.cwd).resolve() if args.cwd else Path.cwd()
    baseline_path = Path(args.baseline)
    if not baseline_path.is_absolute():
        baseline_path = cwd / baseline_path

    if not baseline_path.is_file():
        print(f"error: baseline file {baseline_path} not found", file=sys.stderr)
        return 2

    command_to_run = " ".join(shlex.quote(c) for c in args.command_tail) if args.command_tail else None
    runner = args.runner
    if runner == "auto":
        if args.rerun_cmd and args.rerun_cmd.startswith("node"):
            runner = "node"
        elif command_to_run:
            runner = detect_runner(command_to_run)
        else:
            runner = "pytest"

    current_set: set[str] = set()

    if command_to_run:
        exit_code, output_text = run_command_with_restore(command_to_run, runner, args.restore, cwd)
        if runner == "node":
            current_set = set(extract_node_failures(output_text))
        else:
            current_set = set(extract_pytest_failures(output_text))
    elif args.current:
        current_path = Path(args.current)
        if not current_path.is_absolute():
            current_path = cwd / current_path
        current_set = load_failure_set(current_path)
    else:
        print("error: either --current or command after -- must be provided", file=sys.stderr)
        return 2

    baseline_set = load_failure_set(baseline_path)
    new_failures = sorted(current_set - baseline_set)

    report_lines: list[str] = []
    report_lines.append(f"Baseline failures: {len(baseline_set)}")
    report_lines.append(f"Current failures: {len(current_set)}")
    report_lines.append(f"Candidate new failures: {len(new_failures)}")

    exit_code = 0

    if not new_failures:
        report_lines.append("No new test regressions detected.")
    elif not args.rerun_new:
        report_lines.append("Regressions detected:")
        for f in new_failures:
            report_lines.append(f"  FAILED: {f}")
        exit_code = 1
    else:
        rerun_cmd = args.rerun_cmd
        if not rerun_cmd:
            rerun_cmd = "node --test" if runner == "node" else "python3 -m pytest"

        isolated_passes: list[str] = []
        persistent_failures: list[str] = []

        for candidate in new_failures:
            try:
                cand_exit, _ = rerun_candidate(candidate, runner, rerun_cmd, cwd)
            except ValueError as err:
                print(f"error: {err}", file=sys.stderr)
                return 2

            if cand_exit == 0:
                isolated_passes.append(candidate)
                report_lines.append(f"  ISOLATED_PASS: {candidate}")
            else:
                persistent_failures.append(candidate)
                report_lines.append(f"  PERSISTENT_FAILURE: {candidate}")

        if persistent_failures:
            report_lines.append(f"Regressions confirmed ({len(persistent_failures)} persistent failures).")
            exit_code = 1
        elif isolated_passes:
            if args.allow_isolated_pass:
                report_lines.append(f"All {len(isolated_passes)} candidate failures passed in isolation (--allow-isolated-pass enabled).")
                exit_code = 0
            else:
                report_lines.append(
                    f"{len(isolated_passes)} failures passed in isolation but indicate state-pollution regressions (use --allow-isolated-pass to ignore)."
                )
                exit_code = 1

    report_output = "\n".join(report_lines) + "\n"
    print(report_output.strip())

    if args.output:
        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = cwd / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report_output, encoding="utf-8")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
