#!/usr/bin/env python3
"""Record full-suite failure baselines from pytest or node --test.

Usage:
  record_failure_baseline.py --output|--out <baseline_file>
                             [--cmd <shell_cmd>]
                             [--in <raw_output_file>]
                             [--runner auto|pytest|node]
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

PYTEST_LINE_RE = re.compile(r"^(?:FAILED|ERROR)\s+([^\[\s]+(?:\[[^\]]*\])?)(?:\s+-\s+.*)?$")
NODE_SPEC_FAIL_RE = re.compile(r"^[✖✕]\s+(.*?)\s+\((.*?)(?::\d+(?::\d+)?)?\)$")
NODE_TAP_SUBTEST_RE = re.compile(r"^\s*#\s*Subtest:\s*(.+)$")
NODE_TAP_NOT_OK_RE = re.compile(r"^\s*not\s+ok\s+\d+\s+-\s+(.+?)(?:\s+#.*)?$")


def extract_pytest_failures(output_text: str) -> list[str]:
    """Extract failed and errored node IDs strictly from pytest's terminal summary block."""
    marker = "=== short test summary info ==="
    idx = output_text.rfind(marker)
    if idx == -1:
        return []

    summary_text = output_text[idx + len(marker):]
    footer_idx = summary_text.find("===")
    if footer_idx != -1:
        summary_text = summary_text[:footer_idx]

    failures: set[str] = set()
    for line in summary_text.splitlines():
        line = line.strip()
        match = PYTEST_LINE_RE.match(line)
        if match:
            node_id = match.group(1).strip()
            if node_id:
                failures.add(node_id)

    return sorted(failures)


def extract_node_failures(output_text: str) -> list[str]:
    """Extract failed test identifiers from node --test output as <file>::<test_name>."""
    failures: set[str] = set()
    current_file: str | None = None

    for line in output_text.splitlines():
        stripped = line.strip()

        # Check spec reporter failure: ✖ test name (tests/test_foo.mjs:12:3)
        spec_match = NODE_SPEC_FAIL_RE.match(stripped)
        if spec_match:
            test_name = spec_match.group(1).strip()
            file_path = spec_match.group(2).strip()
            failures.add(f"{file_path}::{test_name}")
            continue

        # Check TAP subtest file context
        tap_subtest = NODE_TAP_SUBTEST_RE.match(line)
        if tap_subtest:
            candidate = tap_subtest.group(1).strip()
            # If candidate looks like a file path
            if candidate.endswith((".js", ".mjs", ".cjs", ".ts", ".mts")):
                current_file = candidate
            continue

        # Check TAP not ok line
        tap_not_ok = NODE_TAP_NOT_OK_RE.match(line)
        if tap_not_ok:
            test_name = tap_not_ok.group(1).strip()
            # Ignore outer subtest completion line
            if current_file and test_name == current_file:
                current_file = None
                continue
            if current_file:
                failures.add(f"{current_file}::{test_name}")
            else:
                failures.add(test_name)

    return sorted(failures)


def record_baseline(output_path: Path, failures: list[str]) -> None:
    """Write failure list or non-empty '# 0 failures' sentinel to output_path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if failures:
        content = "\n".join(failures) + "\n"
    else:
        content = "# 0 failures\n"
    output_path.write_text(content, encoding="utf-8")


def detect_runner(command_str: str) -> str:
    if "node" in command_str:
        return "node"
    return "pytest"


def run_command_with_restore(
    cmd_str: str,
    runner: str,
    restore_paths: list[str],
    cwd: Path | None,
) -> tuple[int, str]:
    """Execute command, ensuring restore paths are checked out in finally block."""
    if runner == "pytest" and "--continue-on-collection-errors" not in cmd_str:
        cmd_str = f"{cmd_str} --continue-on-collection-errors"

    try:
        proc = subprocess.run(
            ["bash", "-o", "pipefail", "-c", cmd_str],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return proc.returncode, proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
    finally:
        for p in restore_paths:
            subprocess.run(["git", "checkout", "--", p], cwd=cwd, capture_output=True)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record full-suite failure baselines.")
    parser.add_argument("--output", "--out", dest="output", required=True, help="Baseline output file")
    parser.add_argument("--cmd", dest="cmd", default=None, help="Shell command to run")
    parser.add_argument("--in", dest="input_file", default=None, help="Raw output file to read from")
    parser.add_argument("--runner", choices=("auto", "pytest", "node"), default="auto")
    parser.add_argument("--restore", dest="restore", action="append", default=[], help="Tracked file to restore")
    parser.add_argument("--cwd", dest="cwd", default=None, help="Working directory")
    parser.add_argument("command_tail", nargs="*", help="Command after --")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    cwd = Path(args.cwd).resolve() if args.cwd else Path.cwd()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = cwd / output_path

    command_to_run = args.cmd
    if not command_to_run and args.command_tail:
        command_to_run = " ".join(shlex.quote(c) for c in args.command_tail)

    runner = args.runner
    if runner == "auto":
        runner = detect_runner(command_to_run or "")

    output_text = ""
    exit_code = 0

    if command_to_run:
        exit_code, output_text = run_command_with_restore(command_to_run, runner, args.restore, cwd)
        # Validate runner execution
        if runner == "pytest":
            has_summary_footer = bool(re.search(r"===\s*.*(?:passed|skipped|warnings|failed|error).*\s*===", output_text))
            has_short_summary = "=== short test summary info ===" in output_text
            if exit_code == 0:
                if not has_summary_footer:
                    print("error: pytest exited 0 but lacked summary footer", file=sys.stderr)
                    return 2
            elif exit_code in (1, 2):
                if not has_short_summary and not has_summary_footer:
                    print(f"error: pytest exited {exit_code} without summary", file=sys.stderr)
                    return 2
            else:
                print(f"error: pytest failed with unexpected exit code {exit_code}", file=sys.stderr)
                return 2
        elif runner == "node":
            if not ("# tests" in output_text or "ℹ tests" in output_text or "# pass" in output_text):
                print("error: node test runner missing summary lines", file=sys.stderr)
                return 2
    elif args.input_file:
        in_path = Path(args.input_file)
        if not in_path.is_absolute():
            in_path = cwd / in_path
        if not in_path.is_file():
            print(f"error: input file {in_path} not found", file=sys.stderr)
            return 2
        output_text = in_path.read_text(encoding="utf-8")
    else:
        output_text = sys.stdin.read()

    if runner == "node":
        failures = extract_node_failures(output_text)
    else:
        failures = extract_pytest_failures(output_text)

    record_baseline(output_path, failures)
    return 0


if __name__ == "__main__":
    sys.exit(main())
