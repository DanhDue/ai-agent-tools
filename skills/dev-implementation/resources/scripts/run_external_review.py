#!/usr/bin/env python3
"""Cross-model review of a finished epic through the Claude CLI or the Codex CLI.

Usage:
  run_external_review.py run --epic-dir <epic_dir> --base <base_ref> --cli claude|codex [--model <name>] [--timeout 1800] [--facts-timeout 300] [--diff-limit 1500]
  run_external_review.py check --epic-dir <epic_dir>

`run` exit codes: 0 a completed round without a Critical or Important finding; 1 a completed round with
one; 2 every other outcome, including CHANGES REQUIRED with no finding line (the round is recorded whenever
the CLI ran). `check` exit codes: 0 nothing undecided; 1 a Critical or Important finding of the latest
completed round has no decision, or a findings row cannot be read.
"""
from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from string import Template

from task_contract import ContractError, git_run, parse_integration_results

SCRIPTS = Path(__file__).resolve().parent
PROMPT = SCRIPTS.parent.parent / "references" / "external-review-prompt.md"

# Tolerates optional markdown headings, bullet prefixes, and bold markers around Verdict.
VERDICT = re.compile(
    r"^\s*(?:#+\s*|[-*+]\s*)?\*{0,2}Verdict(?:(?:\*{0,2}:)|(?::\*{0,2}))\s*\*{0,2}(PASS|CHANGES REQUIRED)\*{0,2}\s*$",
    re.IGNORECASE,
)
# Tolerates list numbering, bullets and ** around the severity, and —, –, - or : between location and problem.
FINDING = re.compile(
    r"^\s*(?:[-*+]|\d+[.)])?\s*\*{0,2}\[\*{0,2}(Critical|Important|Minor)\*{0,2}\]\*{0,2}\s*"
    r"(\S.*?)(?:\s+[—–-]|\s*:)\s+(\S.*)$",
    re.IGNORECASE,
)
# Only catch unparsed blocking tags when they appear on a list-like or tag-leading line to avoid prose false positives.
UNPARSED_BLOCKING = re.compile(
    r"^\s*(?:[-*+]|\d+[.)])?\s*\*{0,2}\[\*{0,2}(Critical|Important)\*{0,2}\]",
    re.IGNORECASE,
)
FINDING_ROW = re.compile(r"^\|\s*\d+\s*\|")
BLOCKING = ("Critical", "Important")
FENCE = re.compile(r"^(`{3,})")

MAX_DIFF_LINES = 1500
MAX_DIFF_BYTES = 60_000

EXCLUDES = (
    # 1. Common Locks, Build & Devtool
    ":(exclude)*.lock",
    ":(exclude)*-lock.*",
    ":(exclude)*.lockfile",
    ":(exclude)**/Package.resolved",
    ":(exclude)build/**",
    ":(exclude).devtool/**",
    # 2. Flutter / Dart Codegen & FFI Bridge
    ":(exclude)*.g.dart",
    ":(exclude)*.freezed.dart",
    ":(exclude)*.gr.dart",
    ":(exclude)*.config.dart",
    ":(exclude)*.mocks.dart",
    ":(exclude)*.chopper.dart",
    ":(exclude)*.pigeon.*",
    ":(exclude)*frb_generated*",
    ":(exclude)**/l10n/app_localizations*.dart",
    # 3. iOS Native (Xcode metadata, assets & UI layout XML)
    ":(exclude)*.pbxproj",
    ":(exclude)*.xcworkspacedata",
    ":(exclude)*.xcscheme",
    ":(exclude)*.storyboard",
    ":(exclude)*.xib",
    ":(exclude)**/*.xcassets/**",
    ":(exclude)*.xcstrings",
    # 4. Android Native (Gradle wrapper & Baseline profiles)
    ":(exclude)gradlew",
    ":(exclude)gradlew.bat",
    ":(exclude)**/gradle/wrapper/**",
    ":(exclude)**/baseline-prof.txt",
    # 5. Rust & Python Generated / Snapshots
    ":(exclude)*.generated.*",
    ":(exclude)*_pb2.py",
    ":(exclude)*_pb2_grpc.py",
    ":(exclude)*_pb2.pyi",
    ":(exclude)**/.sqlx/**",
    ":(exclude)**/__snapshots__/**",
    ":(exclude)*.snap",
    ":(exclude)*.ambr",
    # 6. Minified Web Assets & Source Maps
    ":(exclude)*.min.js",
    ":(exclude)*.min.css",
    ":(exclude)*.map",
)


class PreconditionFailedError(Exception):
    """Raised when fact collection fails, preventing AI CLI invocation."""


def status_lines(root: Path) -> list[str]:
    return git_run(root, "status", "--porcelain").decode("utf-8", "replace").splitlines()


def head_of(root: Path) -> str:
    return git_run(root, "rev-parse", "HEAD").decode().strip()


def execute(command: list[str] | str, root: Path, timeout: int, prompt: str | None = None,
            shell: bool = False) -> tuple[int | None, str, str]:
    """Run to completion in its own process group, so a timeout also ends the CLI's children."""
    process = subprocess.Popen(command, cwd=root, shell=shell, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    try:
        out, err = process.communicate((prompt or "").encode(), timeout=timeout)
        code: int | None = process.returncode
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        out, err = process.communicate()
        code = None
    return code, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


def fact(label: str, code: int | None, out: str, err: str) -> str:
    return f"$ {label}\nexit {code if code is not None else 'timeout'}\n{(out + err).rstrip()}\n"


def collect_facts(root: Path, epic_dir: str, base: str, hld_text: str, timeout: int) -> tuple[str, str]:
    audit = [sys.executable, str(SCRIPTS / "audit_epic.py"), "--epic-dir", epic_dir, "--base", base]
    audit_code, audit_out, audit_err = execute(audit, root, timeout)
    if audit_code is None:
        raise PreconditionFailedError(f"audit_epic.py timed out after {timeout} seconds")
    if audit_code != 0:
        raise PreconditionFailedError(f"audit_epic.py failed with exit {audit_code}:\n{(audit_out + audit_err).rstrip()}")
    audit_output = fact("audit_epic.py", audit_code, audit_out, audit_err)
    results, reports = [], []
    for line in parse_integration_results(hld_text):
        command, _, report = line.partition(" -> ")
        cmd = command.strip()
        cmd_code, cmd_out, cmd_err = execute(cmd, root, timeout, shell=True)
        if cmd_code is None:
            raise PreconditionFailedError(f"integration test '{cmd}' timed out after {timeout} seconds")
        if cmd_code != 0:
            raise PreconditionFailedError(f"integration test '{cmd}' failed with exit {cmd_code}:\n{(cmd_out + cmd_err).rstrip()}")
        results.append(fact(cmd, cmd_code, cmd_out, cmd_err))
        reports.extend(report.split())
    roots = re.search(r"^Integration test roots:\s*(.+)$", hld_text, re.M)
    if roots and reports:
        check = [sys.executable, str(SCRIPTS / "check_bdd_traceability.py"), "tests", "--scenarios",
                 f".devtool/epic/{epic_dir}/bdd_scenarios.en.md", "--roots", roots.group(1).strip(),
                 "--results", *reports]
        chk_code, chk_out, chk_err = execute(check, root, timeout)
        if chk_code is None:
            raise PreconditionFailedError(f"check_bdd_traceability.py timed out after {timeout} seconds")
        if chk_code != 0:
            raise PreconditionFailedError(f"check_bdd_traceability.py failed with exit {chk_code}:\n{(chk_out + chk_err).rstrip()}")
        results.append(fact(shlex.join(check[1:]), chk_code, chk_out, chk_err))
    return audit_output, "\n".join(results) or "No Integration results declared.\n"


def artefact_lines(root: Path, epic_dir: str) -> str:
    folder = root / ".devtool" / "epic" / epic_dir
    names = sorted(p.name for p in folder.glob("*.md"))
    spec = [n for n in names if not n.startswith(("task_", "bdd_", epic_dir, "review_results"))]
    paths = (spec + [f"{epic_dir}.en.md", "bdd_scenarios.en.md"]
             + [n for n in names if n.startswith("task_")] + ["evidence/"])
    return "\n".join(f"- `.devtool/epic/{epic_dir}/{p}`" for p in paths)


def build_diff_section(root: Path, base: str, sha: str, max_lines: int = MAX_DIFF_LINES, max_bytes: int = MAX_DIFF_BYTES) -> str:
    """Hybrid inlining: always show full --stat; inline filtered diff if within size budget."""
    full_stat = git_run(
        root, "diff", "--stat", f"{base}...{sha}", "--", ".", ":(exclude).devtool/**"
    ).decode("utf-8", "replace").strip()
    filtered_diff = git_run(
        root, "diff", f"{base}...{sha}", "--", ".", *EXCLUDES
    ).decode("utf-8", "replace").strip()

    stat_fence = fence_for(full_stat)
    stat_block = f"Full file change summary (`git diff --stat`, including locks/codegen):\n\n{stat_fence}text\n{full_stat or '(no changes outside .devtool/)'}\n{stat_fence}\n\n"

    if not filtered_diff:
        return stat_block + "No non-excluded source code changes to inline."

    line_count = len(filtered_diff.splitlines())
    byte_size = len(filtered_diff.encode("utf-8"))

    if line_count <= max_lines and byte_size <= max_bytes:
        diff_fence = fence_for(filtered_diff)
        return (
            stat_block
            + f"The complete source diff ({line_count} lines, {byte_size // 1024} KB, lock, generated, and noisy metadata/asset files excluded) "
            f"is inlined below. Do NOT run `git diff` again unless you need to inspect an excluded file:\n\n"
            f"{diff_fence}diff\n{filtered_diff}\n{diff_fence}"
        )

    return (
        stat_block
        + f"The source diff is large ({line_count} lines, {byte_size // 1024} KB > inline budget). "
        f"Do NOT run an unfiltered `git diff`; inspect specific target files via `git diff {base}...{sha} -- <path>` as needed."
    )


def cli_command(cli: str, model: str | None) -> list[str]:
    extra = ["--model", model] if model else []
    if cli == "claude":
        return ["claude", "-p", "--permission-mode", "plan", *extra]
    return ["codex", "exec", "--sandbox", "read-only", *extra, "-"]


def cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\r", "").replace("\n", " ").strip()


def fence_for(text: str) -> str:
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def rounds_in(text: str) -> list[tuple[int, list[str]]]:
    """Split review_results.md into (number, lines) rounds, ignoring headings inside fenced raw output."""
    rounds: list[tuple[int, list[str]]] = []
    fence = ""
    for line in text.splitlines():
        match = FENCE.match(line)
        if fence:
            fence = "" if line.rstrip() == fence else fence
        elif match:
            fence = match.group(1)
        elif (heading := re.fullmatch(r"## Round (\d+)", line)):
            rounds.append((int(heading.group(1)), []))
            continue
        if rounds:
            rounds[-1][1].append(line)
    return rounds


def split_row(line: str) -> list[str]:
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]


def metadata(lines: list[str]) -> list[str]:
    """A round's own lines: its fields and findings table, never its raw output."""
    return lines[:lines.index("Raw output:")] if "Raw output:" in lines else lines


def table_findings(lines: list[str]) -> list[tuple[str, list[str]]]:
    """(line, cells) for every findings row, `| <number> |` onwards, well formed or not."""
    return [(line, split_row(line)) for line in metadata(lines) if FINDING_ROW.match(line)]


def parse_findings(out: str, verdict: str | None = None) -> list[tuple[str, str, str]]:
    """Each finding line as (severity, location, problem); a blocking line in list format keeps its raw text."""
    findings = []
    for line in out.splitlines():
        if (match := FINDING.match(line)):
            sev, loc, problem = match.groups()
            findings.append((sev.capitalize(), loc, problem))
        elif (blocking := UNPARSED_BLOCKING.search(line)):
            if verdict == "PASS" and not findings:
                continue
            findings.append((blocking.group(1).capitalize(), "unparsed", line.strip()))
    return findings


def render_round(number: int, meta: dict[str, str], findings: list[tuple[str, str, str]], output: str) -> str:
    head = "".join(f"- **{key}**: {value}\n" for key, value in meta.items())
    table = "| # | Severity | Location | Problem | Decision |\n|---|----------|----------|---------|----------|\n"
    table += "".join(f"| {i} | {sev} | {cell(loc)} | {cell(problem)} |  |\n"
                     for i, (sev, loc, problem) in enumerate(findings, 1))
    fence = fence_for(output)
    return f"## Round {number}\n\n{head}\n{table}\nRaw output:\n\n{fence}text\n{output.rstrip()}\n{fence}\n"


def run(args: argparse.Namespace) -> int:
    if not shutil.which(args.cli):
        print(f"{args.cli} not found on PATH", file=sys.stderr)
        return 2
    root = Path(git_run(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
    if status_lines(root):
        print("commit or stash your changes before a review", file=sys.stderr)
        return 2
    sha = head_of(root)
    hld_text = (root / ".devtool" / "epic" / args.epic_dir / f"{args.epic_dir}.en.md").read_text(encoding="utf-8")
    try:
        facts_timeout = getattr(args, "facts_timeout", 300)
        audit_output, results_output = collect_facts(root, args.epic_dir, args.base, hld_text, facts_timeout)
    except PreconditionFailedError as error:
        print(f"precondition failed: {error}", file=sys.stderr)
        return 2
    diff_limit = getattr(args, "diff_limit", MAX_DIFF_LINES)
    diff_section = build_diff_section(root, args.base, sha, max_lines=diff_limit)
    prompt = Template(PROMPT.read_text(encoding="utf-8")).safe_substitute(
        sha=sha,
        base=args.base,
        epic_dir=f".devtool/epic/{args.epic_dir}",
        artefacts=artefact_lines(root, args.epic_dir),
        audit_output=audit_output.rstrip(),
        results_output=results_output.rstrip(),
        diff_section=diff_section,
    )
    before = status_lines(root)  # after the facts: running the test commands may write build output
    code, out, err = execute(cli_command(args.cli, args.model), root, args.timeout, prompt)
    after = status_lines(root)
    output = out + (f"\n--- stderr ---\n{err}" if err.strip() else "")
    if code is None:
        output += f"\n--- timed out after {args.timeout} seconds ---\n"
    changed = sorted(set(after) ^ set(before))
    if head_of(root) != sha:
        changed.insert(0, "HEAD")
    verdicts = [m.group(1).upper() for line in out.splitlines() if (m := VERDICT.match(line))]
    final_verdict = verdicts[-1] if verdicts else None
    findings = parse_findings(out, final_verdict)
    if changed:
        status = f"discarded: tree modified ({', '.join(line[3:] if line != 'HEAD' else line for line in changed)})"
    elif code != 0 or not verdicts or (verdicts[-1] == "CHANGES REQUIRED" and not findings):
        status = "no verdict"
    else:
        status = "completed"
    path = root / ".devtool" / "epic" / args.epic_dir / "review_results.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else f"# Cross-Model Review: {args.epic_dir}\n"
    round_num = len(rounds_in(existing)) + 1
    meta = {
        "Date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "SHA": sha,
        "Base": args.base,
        "CLI": args.cli,
        "Model": args.model or "default",
        "Status": status,
        "Verdict": verdicts[-1] if verdicts else "none",
    }
    text = existing.rstrip("\n") + "\n\n" + render_round(round_num, meta, findings, output)
    path.write_text(text, encoding="utf-8")
    print(f"Round {round_num}: {status} ({path.relative_to(root)})")
    if status != "completed":
        return 2
    return 1 if any(sev in BLOCKING for sev, _, _ in findings) else 0


def check(args: argparse.Namespace) -> int:
    root = Path(git_run(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
    path = root / ".devtool" / "epic" / args.epic_dir / "review_results.md"
    if not path.exists():
        return 0
    completed = [(n, lines) for n, lines in rounds_in(path.read_text(encoding="utf-8"))
                 if "- **Status**: completed" in metadata(lines)]
    undecided = []
    for line, cells in table_findings(completed[-1][1]) if completed else []:
        if len(cells) != 5:
            undecided.append(f"undecided: unreadable findings row: {line.strip()}")
        elif cells[1] in BLOCKING and not cells[4].startswith(("fixed in ", "dismissed: ")):
            undecided.append(f"undecided: #{cells[0]} {cells[1]} {cells[2]}")
    if undecided:
        print("\n".join(undecided))
    return 1 if undecided else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    modes = parser.add_subparsers(dest="mode", required=True)
    runner = modes.add_parser("run", help="have the CLI review the epic and record a round")
    runner.add_argument("--epic-dir", required=True)
    runner.add_argument("--base", required=True)
    runner.add_argument("--cli", required=True, choices=("claude", "codex"))
    runner.add_argument("--model")
    runner.add_argument("--timeout", type=int, default=1800)
    runner.add_argument("--facts-timeout", type=int, default=300)
    runner.add_argument("--diff-limit", type=int, default=MAX_DIFF_LINES)
    checker = modes.add_parser("check", help="list undecided blocking findings of the latest completed round")
    checker.add_argument("--epic-dir", required=True)
    args = parser.parse_args(argv)
    try:
        return run(args) if args.mode == "run" else check(args)
    except (ContractError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
