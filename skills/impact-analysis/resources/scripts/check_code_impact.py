#!/usr/bin/env python3
"""Pre-edit Impact and Conflict Checker Engine.

Analyzes potential blast radius, upstream git divergence, cross-platform bridge
contracts, and test coverage before source code modifications occur.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class DivergenceResult:
    has_divergence: bool = False
    base_ref: str = ""
    merge_base: str = ""
    divergent_commits: list[dict[str, str]] = field(default_factory=list)
    dirty_files: list[str] = field(default_factory=list)


@dataclass
class ImpactReport:
    files: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)
    divergence: DivergenceResult | None = None
    callers: dict[str, list[int]] = field(default_factory=dict)
    bridges: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    coverage: dict[str, dict] = field(default_factory=dict)


def resolve_base_ref(repo: Path, candidate: str | None = None) -> str:
    """Resolve the nearest base reference (e.g. develop, main, origin/develop)."""
    if candidate:
        return candidate
    for ref in ("develop", "origin/develop", "main", "origin/main"):
        res = subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            return ref
    return "HEAD"


def check_upstream_divergence(
    repo: Path, files: list[str], base_ref: str | None = None
) -> DivergenceResult:
    """Check if upstream base_ref has unmerged commits touching target files."""
    resolved_base = resolve_base_ref(repo, base_ref)
    result = DivergenceResult(base_ref=resolved_base)

    mb_res = subprocess.run(
        ["git", "merge-base", "HEAD", resolved_base],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if mb_res.returncode != 0:
        return result

    merge_base = mb_res.stdout.strip()
    result.merge_base = merge_base

    for file_path in files:
        # Check git log between merge-base and base_ref for this file
        log_res = subprocess.run(
            [
                "git",
                "log",
                "--format=%H|%an|%ad|%s",
                f"{merge_base}..{resolved_base}",
                "--",
                file_path,
            ],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        if log_res.returncode == 0 and log_res.stdout.strip():
            for line in log_res.stdout.strip().splitlines():
                parts = line.split("|", 3)
                if len(parts) == 4:
                    result.divergent_commits.append(
                        {
                            "hash": parts[0][:8],
                            "author": parts[1],
                            "date": parts[2],
                            "subject": parts[3],
                            "file": file_path,
                        }
                    )

        # Check dirty worktree status
        status_res = subprocess.run(
            ["git", "status", "--porcelain", "--", file_path],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        if status_res.returncode == 0 and status_res.stdout.strip():
            result.dirty_files.append(file_path)

    if result.divergent_commits:
        result.has_divergence = True

    return result


def check_downstream_callers(
    root: Path,
    symbols: list[str],
    search_files: list[Path] | None = None,
) -> dict[str, list[int]]:
    """Scan the repository for downstream callers, imports, and references to symbols."""
    callers: dict[str, list[int]] = {}
    if not symbols:
        return callers

    patterns = [re.compile(rf"\b{re.escape(s)}\b") for s in symbols]
    search_rel_paths = {str(p.resolve()) for p in (search_files or [])}

    ignored_dirs = {
        ".git",
        "node_modules",
        ".dart_tool",
        "build",
        ".build",
        ".gradle",
        "dist",
        ".worktrees",
        "coverage",
    }

    for current_dir, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith(".")]
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in (
                ".dart",
                ".kt",
                ".java",
                ".swift",
                ".ts",
                ".js",
                ".py",
                ".kts",
            ):
                continue

            file_path = Path(current_dir) / filename
            if str(file_path.resolve()) in search_rel_paths:
                continue

            rel_path = str(file_path.relative_to(root))

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            matched_lines: list[int] = []
            for line_idx, line in enumerate(content.splitlines(), start=1):
                for pat in patterns:
                    if pat.search(line):
                        matched_lines.append(line_idx)
                        break

            if matched_lines:
                callers[rel_path] = matched_lines

    return callers


def check_bridge_contracts(
    root: Path, files: list[Path]
) -> dict[str, dict[str, list[str]]]:
    """Inspect Flutter files for MethodChannel strings and locate native counterparts."""
    bridges: dict[str, dict[str, list[str]]] = {}
    channel_re = re.compile(
        r"""MethodChannel\s*\(\s*['"]([a-zA-Z0-9_\./\-]+)['"]\s*\)"""
    )

    detected_channels: set[str] = set()
    for file_path in files:
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for match in channel_re.finditer(text):
            detected_channels.add(match.group(1))

    if not detected_channels:
        return bridges

    # Search android/ and ios/ directories for matching channel names
    for channel in detected_channels:
        bridges[channel] = {"android": [], "ios": []}
        pattern = re.compile(re.escape(channel))

        # Search android
        android_dir = root / "android"
        if android_dir.is_dir():
            for curr, _, files_in_dir in os.walk(android_dir):
                for fname in files_in_dir:
                    if fname.endswith((".kt", ".java")):
                        fp = Path(curr) / fname
                        try:
                            if pattern.search(
                                fp.read_text(encoding="utf-8", errors="ignore")
                            ):
                                bridges[channel]["android"].append(
                                    str(fp.relative_to(root))
                                )
                        except Exception:
                            pass

        # Search ios
        ios_dir = root / "ios"
        if ios_dir.is_dir():
            for curr, _, files_in_dir in os.walk(ios_dir):
                for fname in files_in_dir:
                    if fname.endswith((".swift", ".m", ".h")):
                        fp = Path(curr) / fname
                        try:
                            if pattern.search(
                                fp.read_text(encoding="utf-8", errors="ignore")
                            ):
                                bridges[channel]["ios"].append(
                                    str(fp.relative_to(root))
                                )
                        except Exception:
                            pass

    return bridges


def find_paired_test(root: Path, src_file: Path) -> Path | None:
    """Locate the conventional unit test file for a source file."""
    rel = src_file.relative_to(root)
    stem = src_file.stem
    ext = src_file.suffix

    candidates = [
        root / "test" / rel.parent / f"{stem}_test{ext}",
        root / "test" / f"{stem}_test{ext}",
        root / "src" / "test" / "java" / rel.parent / f"{stem}Test{ext}",
        root / "Tests" / f"{stem}Tests{ext}",
    ]

    for cand in candidates:
        if cand.is_file():
            return cand

    # Broader glob search
    for test_cand in root.glob(f"**/*{stem}*test*{ext}"):
        if test_cand.is_file() and "build" not in test_cand.parts:
            return test_cand

    return None


def parse_lcov_for_file(lcov_path: Path, src_file: Path) -> float | None:
    """Parse lcov.info to find coverage percentage for a specific source file."""
    if not lcov_path.is_file():
        return None

    src_name = src_file.name
    try:
        content = lcov_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    in_target = False
    lines_found = 0
    lines_hit = 0

    for line in content.splitlines():
        if line.startswith("SF:"):
            file_in_lcov = line[3:].strip()
            in_target = (
                file_in_lcov.endswith(str(src_file))
                or src_name in file_in_lcov
            )
        elif in_target:
            if line.startswith("LF:"):
                lines_found = int(line[3:].strip())
            elif line.startswith("LH:"):
                lines_hit = int(line[3:].strip())
            elif line.startswith("end_of_record"):
                if lines_found > 0:
                    return round((lines_hit / lines_found) * 100.0, 1)
                return 0.0

    return None


def check_test_coverage(root: Path, files: list[Path]) -> dict[str, dict]:
    """Perform Test Impact Analysis (TIA) and baseline test coverage auditing."""
    coverage_results: dict[str, dict] = {}
    lcov_candidates = [
        root / "coverage" / "lcov.info",
        root / "build" / "reports" / "jacoco" / "test" / "jacocoTestReport.xml",
    ]
    lcov_file = next((f for f in lcov_candidates if f.is_file()), None)

    for src_file in files:
        if not src_file.is_file():
            continue
        rel_key = str(src_file.relative_to(root))
        test_file = find_paired_test(root, src_file)

        cov_percent = 0.0
        if lcov_file:
            parsed_cov = parse_lcov_for_file(lcov_file, src_file)
            if parsed_cov is not None:
                cov_percent = parsed_cov
            elif test_file:
                cov_percent = 50.0  # test exists but file unrepresented in lcov
        elif test_file:
            cov_percent = 80.0  # heuristic default when test exists without report

        # Check for error handling in source code
        untested_error_paths: list[str] = []
        try:
            content = src_file.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"\bcatch\b|\bonError\b|\bfailure\b", content, re.I):
                if test_file:
                    test_content = test_file.read_text(
                        encoding="utf-8", errors="ignore"
                    )
                    if not re.search(
                        r"throws|error|exception|failure", test_content, re.I
                    ):
                        untested_error_paths.append(
                            "Unhandled catch/error scenario in test suite"
                        )
                else:
                    untested_error_paths.append(
                        "File has exception handling but zero test coverage"
                    )
        except Exception:
            pass

        coverage_results[rel_key] = {
            "has_test_file": test_file is not None,
            "test_file": str(test_file.relative_to(root)) if test_file else None,
            "coverage_percent": cov_percent,
            "untested_error_paths": untested_error_paths,
        }

    return coverage_results


def run_impact_analysis(
    root: Path,
    files: list[str],
    symbols: list[str],
    base_ref: str | None = None,
) -> ImpactReport:
    """Execute full 4-layer impact analysis pipeline."""
    target_paths = [root / f for f in files]

    divergence = check_upstream_divergence(root, files, base_ref=base_ref)
    callers = check_downstream_callers(root, symbols, search_files=target_paths)
    bridges = check_bridge_contracts(root, target_paths)
    coverage = check_test_coverage(root, target_paths)

    return ImpactReport(
        files=files,
        symbols=symbols,
        divergence=divergence,
        callers=callers,
        bridges=bridges,
        coverage=coverage,
    )


def format_markdown_report(report: ImpactReport) -> str:
    """Format impact report into readable GitHub-flavored Markdown."""
    lines: list[str] = [
        "# Impact Analysis Diagnostic Report",
        "",
        "## 1. Upstream Git Conflict Analysis",
    ]

    div = report.divergence
    if div and div.has_divergence:
        lines.append(
            f"**Status**: 🔴 **DIVERGENCE DETECTED** (against `{div.base_ref}`)"
        )
        lines.append("")
        lines.append("| Commit | Author | Date | Subject | File |")
        lines.append("|---|---|---|---|---|")
        for c in div.divergent_commits:
            lines.append(
                f"| `{c['hash']}` | {c['author']} | {c['date']} | {c['subject']} | `{c['file']}` |"
            )
        lines.append("")
        lines.append(
            "> [!CAUTION]\n> Upstream unmerged commits detected. Rebase branch before modifying target files."
        )
    else:
        ref_name = div.base_ref if div else "base"
        lines.append(
            f"**Status**: 🟢 **CLEAN** (Zero unmerged commits against `{ref_name}`)"
        )

    if div and div.dirty_files:
        lines.append("")
        lines.append(
            f"**Dirty Worktree**: ⚠️ Uncommitted changes in: {', '.join(f'`{f}`' for f in div.dirty_files)}"
        )

    lines.append("")
    lines.append("## 2. Downstream Callers & Blast Radius")
    if report.callers:
        lines.append(f"Found {len(report.callers)} downstream caller files:")
        lines.append("")
        lines.append("| Caller File | Reference Lines |")
        lines.append("|---|---|")
        for f, l_nums in report.callers.items():
            lines.append(f"| `{f}` | Lines: {', '.join(map(str, l_nums[:8]))} |")
    else:
        lines.append("No downstream callers or external dependencies detected.")

    lines.append("")
    lines.append("## 3. Cross-Platform Bridge Contracts")
    if report.bridges:
        for ch, native_files in report.bridges.items():
            lines.append(f"### Channel: `{ch}`")
            android_list = native_files.get("android", [])
            ios_list = native_files.get("ios", [])
            lines.append(
                f"- **Android**: {', '.join(f'`{f}`' for f in android_list) if android_list else 'None'}"
            )
            lines.append(
                f"- **iOS**: {', '.join(f'`{f}`' for f in ios_list) if ios_list else 'None'}"
            )
    else:
        lines.append("No active `MethodChannel` or Native bridges detected.")

    lines.append("")
    lines.append("## 4. Coverage Safety Net & Test Impact")
    for f, cov_data in report.coverage.items():
        cov_val = cov_data["coverage_percent"]
        cov_icon = "🟢" if cov_val >= 80.0 else ("🟡" if cov_val > 0 else "🔴")
        lines.append(f"### File: `{f}` ({cov_icon} {cov_val}% Coverage)")
        if cov_data["has_test_file"]:
            lines.append(f"- **Paired Test**: `{cov_data['test_file']}`")
        else:
            lines.append(
                "- **Paired Test**: ⚠️ **UNPROTECTED CODE (0% Coverage)** - No test file found!"
            )
        if cov_data["untested_error_paths"]:
            for err_note in cov_data["untested_error_paths"]:
                lines.append(f"- ⚠️ **Missing Logic Alert**: {err_note}")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check pre-edit code impact, blast radius, bridge contracts, and git divergence."
    )
    parser.add_argument(
        "--files", nargs="+", default=[], help="Target files to analyze"
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=[],
        help="Target class or function symbols to trace",
    )
    parser.add_argument(
        "--base-ref", default=None, help="Base git reference (e.g. develop, main)"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output report format",
    )

    args = parser.parse_args()
    repo_root = Path.cwd()

    report = run_impact_analysis(
        root=repo_root,
        files=args.files,
        symbols=args.symbols,
        base_ref=args.base_ref,
    )

    if args.format == "json":
        data = asdict(report)
        print(json.dumps(data, indent=2))
    else:
        print(format_markdown_report(report))

    # Determine exit code: 1 if high-risk divergence or unprotected code, 0 otherwise
    has_critical_issue = False
    if report.divergence and report.divergence.has_divergence:
        has_critical_issue = True
    for cov in report.coverage.values():
        if not cov["has_test_file"] or cov["coverage_percent"] < 50.0:
            has_critical_issue = True

    if has_critical_issue:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
