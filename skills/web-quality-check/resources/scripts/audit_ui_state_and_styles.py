"""Audit UI/UX state, styling invariants, cache-busting, and state machine consistency.

Enforces four critical UI/UX quality invariants:
1. Cache-Bust Verification: static asset changes must update template ?v= query parameters.
2. Orphaned Class & Computed Style Check: referenced classes must exist in stylesheets; no unstyled default cards/drawers/badges.
3. Text Truncation & Overflow Guard: left-aligned text in flex rows must not clip start-of-string; no consecutive duplicate words/phrases.
4. UI State Machine Consistency: terminal states (FAILED/COMPLETED) must not coexist with active running prefixes;
   failed jobs with pending steps must not show 100% progress; SSE EventSource must close on terminal states.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

TERMINAL_STATES = {"FAILED", "COMPLETED", "THẤT BẠI", "HOÀN THÀNH", "SUCCESS", "ERROR"}
ACTIVE_PREFIXES = [
    "Đang chạy:",
    "Đang xử lý:",
    "Đang cập nhật:",
    "Running:",
    "Processing:",
    "In Progress:",
]

# Standard CSS utility prefixes and keywords exempt from orphaned class alerts
STANDARD_UTILITIES = {
    "flex",
    "inline-flex",
    "grid",
    "block",
    "inline-block",
    "inline",
    "hidden",
    "relative",
    "absolute",
    "fixed",
    "sticky",
    "w-full",
    "h-full",
    "w-auto",
    "h-auto",
    "min-w-0",
    "max-w-full",
    "container",
    "row",
    "col",
    "active",
    "disabled",
    "open",
    "selected",
}


def strip_comments_preserving_strings(code: str) -> str:
    """Strip // and /* */ comments while preserving string literals (double, single, backtick)."""
    pattern = re.compile(
        r"""
        (                               # Group 1: strings
            "(?:\\.|[^"\\])*"
          | '(?:\\.|[^'\\])*'
          | `(?:\\.|[^`\\])*`
        )
      | (/\*.*?\*/)                     # Group 2: block comment
      | (//[^\n]*)                      # Group 3: line comment
    """,
        re.VERBOSE | re.DOTALL,
    )

    def replacer(m: re.Match[str]) -> str:
        if m.group(1):
            return m.group(1)
        return ""

    return pattern.sub(replacer, code)


def get_git_diff_files(repo_root: Path, base_ref: str = "main") -> list[str]:
    """Retrieve list of modified or added files compared to base_ref."""
    try:
        # Check if base_ref exists
        rev_check = subprocess.run(
            ["git", "rev-parse", "--verify", base_ref],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if rev_check.returncode != 0:
            # Fallback to HEAD~1 or empty if fresh repo
            return []

        diff_proc = subprocess.run(
            ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if diff_proc.returncode == 0:
            lines = [
                line.strip() for line in diff_proc.stdout.splitlines() if line.strip()
            ]
            if lines:
                return lines

        # Try 2-dot diff if 3-dot produced nothing or failed
        diff_proc2 = subprocess.run(
            ["git", "diff", "--name-only", base_ref],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if diff_proc2.returncode == 0:
            return [
                line.strip() for line in diff_proc2.stdout.splitlines() if line.strip()
            ]

    except (subprocess.SubprocessError, OSError):
        pass
    return []


def _is_excluded(p: Path, repo_root: Path) -> bool:
    try:
        rel_parts = p.relative_to(repo_root).parts
    except ValueError:
        rel_parts = p.parts
    return (
        "node_modules" in rel_parts
        or "build" in rel_parts
        or ".worktrees" in rel_parts
        or ".git" in rel_parts
    )


def _get_base_file_content(repo_root: Path, base_ref: str, rel_path: str) -> str | None:
    try:
        res = subprocess.run(
            ["git", "show", f"{base_ref}:{rel_path}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return res.stdout
    except (subprocess.SubprocessError, OSError):
        pass
    return None


def audit_cache_busting(
    repo_root: Path,
    modified_files: list[str],
    base_ref: str = "main",
) -> list[dict[str, Any]]:
    """Invariant 1: Verify static asset changes update ?v= parameter in referencing templates."""
    findings: list[dict[str, Any]] = []

    # Find modified static .js or .css files
    static_mods = [
        f
        for f in modified_files
        if f.endswith((".js", ".css"))
        and not f.endswith((".test.js", ".spec.js", ".fixture.ts"))
    ]

    if not static_mods:
        return findings

    # Template extensions to inspect
    template_files = (
        list(repo_root.rglob("*.html"))
        + list(repo_root.rglob("*.astro"))
        + list(repo_root.rglob("*.jinja"))
        + list(repo_root.rglob("*.jinja2"))
    )
    # Exclude build, node_modules, and nested worktrees
    template_files = [t for t in template_files if not _is_excluded(t, repo_root)]

    for static_rel in static_mods:
        static_filename = Path(static_rel).name
        for tpl in template_files:
            try:
                content = tpl.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            # Look for references to this static filename in script/link tags
            pattern = re.compile(
                rf"""(?:src|href)=['"][^'"]*?{re.escape(static_filename)}(\?[^'"]*)?['"]"""
            )
            matches = list(pattern.finditer(content))
            for match in matches:
                query_string = match.group(1) or ""
                rel_tpl = str(tpl.relative_to(repo_root))
                v_match = re.search(r"[?&]v=([^&'\"]*)", query_string)
                current_v = v_match.group(1) if v_match else ""

                if not current_v:
                    findings.append(
                        {
                            "category": "cache_bust",
                            "severity": "FAIL",
                            "file": rel_tpl,
                            "asset": static_rel,
                            "message": (
                                f"Static asset '{static_rel}' modified in git diff but referenced in template "
                                f"'{rel_tpl}' without a version query parameter (?v=...)."
                            ),
                        }
                    )
                else:
                    base_content = _get_base_file_content(repo_root, base_ref, rel_tpl)
                    if base_content is not None:
                        base_match = pattern.search(base_content)
                        if base_match:
                            base_q = base_match.group(1) or ""
                            base_v_m = re.search(r"[?&]v=([^&'\"]*)", base_q)
                            base_v = base_v_m.group(1) if base_v_m else ""
                            if current_v == base_v:
                                findings.append(
                                    {
                                        "category": "cache_bust",
                                        "severity": "FAIL",
                                        "file": rel_tpl,
                                        "asset": static_rel,
                                        "message": (
                                            f"Static asset '{static_rel}' was modified in git diff, but referencing template "
                                            f"'{rel_tpl}' has unchanged cache-bust parameter '?v={current_v}' (identical to {base_ref})."
                                        ),
                                    }
                                )
                    elif rel_tpl not in modified_files:
                        findings.append(
                            {
                                "category": "cache_bust",
                                "severity": "FAIL",
                                "file": rel_tpl,
                                "asset": static_rel,
                                "message": (
                                    f"Static asset '{static_rel}' was modified in git diff, but referencing template "
                                    f"'{rel_tpl}' was not updated with a new cache-bust version parameter."
                                ),
                            }
                        )

    return findings


def audit_orphaned_classes_and_styles(
    repo_root: Path,
    target_files: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Invariant 2: Verify CSS classes exist and cards/drawers/badges have styled definitions."""
    findings: list[dict[str, Any]] = []

    # 1. Collect all declared CSS classes from stylesheets
    css_files = [f for f in repo_root.rglob("*.css") if not _is_excluded(f, repo_root)]
    defined_classes: set[str] = set()
    class_def_pattern = re.compile(r"\.([A-Za-z0-9_-]+)(?=[^\{]*\{)")

    for cf in css_files:
        try:
            css_text = cf.read_text(encoding="utf-8")
            for m in class_def_pattern.finditer(css_text):
                defined_classes.add(m.group(1))
        except (OSError, UnicodeDecodeError):
            continue

    # Also collect declared CSS classes from component-scoped <style> blocks (*.astro, *.html, *.vue, etc.)
    style_block_pattern = re.compile(
        r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE
    )
    component_files = []
    for ext in ("*.astro", "*.html", "*.jinja", "*.vue", "*.svelte"):
        component_files.extend(
            f for f in repo_root.rglob(ext) if not _is_excluded(f, repo_root)
        )

    for comp in component_files:
        try:
            comp_text = comp.read_text(encoding="utf-8")
            for sm in style_block_pattern.finditer(comp_text):
                style_content = sm.group(1)
                for m in class_def_pattern.finditer(style_content):
                    defined_classes.add(m.group(1))
        except (OSError, UnicodeDecodeError):
            continue

    # 2. Check candidate templates and DOM builder scripts
    candidate_files = []
    if target_files:
        candidate_files = [
            repo_root / f for f in target_files if (repo_root / f).is_file()
        ]
    else:
        for ext in ("*.html", "*.astro", "*.jinja", "*.jsx", "*.tsx"):
            candidate_files.extend(repo_root.rglob(ext))

    candidate_files = [f for f in candidate_files if not _is_excluded(f, repo_root)]

    class_ref_pattern = re.compile(r"""(?:class|className)=['"]([^'"]+)['"]""")
    unstyled_card_pattern = re.compile(
        r"""<(?:div|section|aside|span)[^>]*class=['"][^'"]*?\b(card|drawer|badge|panel|modal)\b[^'"]*?['"][^>]*style=['"][^'"]*?(?:background:\s*(?:transparent|none)|border:\s*0|padding:\s*0)[^'"]*?['"]""",
        re.IGNORECASE,
    )

    for cf in candidate_files:
        try:
            content = cf.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        rel_path = str(cf.relative_to(repo_root))

        # Check for unstyled default component anti-pattern
        unstyled_matches = unstyled_card_pattern.finditer(content)
        for um in unstyled_matches:
            comp_type = um.group(1)
            findings.append(
                {
                    "category": "unstyled_default",
                    "severity": "FAIL",
                    "file": rel_path,
                    "message": (
                        f"Component '{comp_type}' in '{rel_path}' renders with unstyled default geometry "
                        f"(transparent background, 0px border, or 0px padding)."
                    ),
                }
            )

        # Check class references
        for cm in class_ref_pattern.finditer(content):
            classes = cm.group(1).split()
            for cls in classes:
                # Skip template interpolation tokens like ${...} or {{...}}
                if "{" in cls or "$" in cls or "%" in cls:
                    continue
                if cls in STANDARD_UTILITIES or cls.startswith(
                    ("w-", "h-", "m-", "p-", "text-", "bg-", "border-")
                ):
                    continue
                if defined_classes and cls not in defined_classes:
                    findings.append(
                        {
                            "category": "orphaned_class",
                            "severity": "FAIL",
                            "file": rel_path,
                            "class": cls,
                            "message": f"Referenced CSS class '{cls}' in '{rel_path}' is not defined in any loaded stylesheet.",
                        }
                    )

    return findings


def audit_text_truncation_and_overflow(
    repo_root: Path,
    target_files: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Invariant 3: Guard against text clipping at start of flex rows and consecutive duplicate text."""
    findings: list[dict[str, Any]] = []

    candidate_files = []
    if target_files:
        candidate_files = [
            repo_root / f for f in target_files if (repo_root / f).is_file()
        ]
    else:
        for ext in ("*.html", "*.astro", "*.jinja", "*.js", "*.ts", "*.jsx", "*.tsx"):
            candidate_files.extend(repo_root.rglob(ext))

    candidate_files = [f for f in candidate_files if not _is_excluded(f, repo_root)]

    # Regex for consecutive duplicate word or phrase with token boundaries: "Tiến độ Tiến độ" or "Word Word"
    duplicate_phrase_pattern = re.compile(
        r"""(?:^|[\s"'>])([A-Za-zÀ-ỹ0-9_]{2,}(?:\s+[A-Za-zÀ-ỹ0-9_]{2,})*)\s+\1(?=$|[\s<"'\.,;!?:])""",
        re.IGNORECASE | re.UNICODE,
    )

    # Improper flex alignment causing left-clipping
    left_clip_pattern = re.compile(
        r"""display:\s*flex[^;]*;[^}]*justify-content:\s*(?:flex-end|end|right)[^}]*text-overflow:\s*ellipsis""",
        re.IGNORECASE,
    )

    for cf in candidate_files:
        try:
            content = cf.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        rel_path = str(cf.relative_to(repo_root))

        # Check for left-clipping flex styles
        if left_clip_pattern.search(content):
            findings.append(
                {
                    "category": "text_clipping",
                    "severity": "FAIL",
                    "file": rel_path,
                    "message": (
                        f"Flex row in '{rel_path}' pairs right-aligned justify-content with text-overflow: ellipsis, "
                        f"risking start-of-string left-side clipping."
                    ),
                }
            )

        # Check headings and titles for consecutive duplicate words/phrases
        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            # Only inspect text inside tags or string literals, skip pure comments or repetitive tests
            if "test_" in rel_path or "mock" in rel_path.lower():
                continue
            dup_match = duplicate_phrase_pattern.search(line)
            if dup_match:
                phrase = dup_match.group(1)
                # Filter benign repetitions like "1 1" or common code syntax
                if len(phrase) >= 4 and not phrase.startswith(("//", "/*", "#")):
                    findings.append(
                        {
                            "category": "duplicate_text",
                            "severity": "FAIL",
                            "file": rel_path,
                            "line": idx,
                            "duplicate_phrase": phrase,
                            "message": (
                                f"Consecutive duplicate phrase '{phrase} {phrase}' detected in '{rel_path}:{idx}'."
                            ),
                        }
                    )

    return findings


def audit_ui_state_machine_consistency(
    repo_root: Path,
    target_files: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Invariant 4: Validate state machine consistency, progress limits, and EventSource teardown."""
    findings: list[dict[str, Any]] = []

    candidate_files = []
    if target_files:
        candidate_files = [
            repo_root / f for f in target_files if (repo_root / f).is_file()
        ]
    else:
        for ext in ("*.html", "*.astro", "*.jinja", "*.js", "*.ts"):
            candidate_files.extend(repo_root.rglob(ext))

    candidate_files = [
        f
        for f in candidate_files
        if not _is_excluded(f, repo_root) and "test_" not in f.name
    ]

    for cf in candidate_files:
        try:
            content = cf.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        rel_path = str(cf.relative_to(repo_root))

        # 1. Contradictory terminal state + running prefix in static strings
        for prefix in ACTIVE_PREFIXES:
            for term in TERMINAL_STATES:
                contradiction = f"{prefix} {term}"
                if contradiction in content:
                    findings.append(
                        {
                            "category": "state_machine_contradiction",
                            "severity": "FAIL",
                            "file": rel_path,
                            "message": (
                                f"Contradictory state string '{contradiction}' found in '{rel_path}'. "
                                f"Active running prefix cannot coexist with terminal state."
                            ),
                        }
                    )

        # Strip single-line and multi-line comments for logic checks, preserving string literals
        code_no_comments = strip_comments_preserving_strings(content)

        # 2. SSE EventSource connection closure verification
        if "new EventSource(" in code_no_comments:
            # Must contain close() call on terminal state completion
            has_close = bool(
                re.search(r"\.close\s*\(", code_no_comments)
                or "closeConnection" in code_no_comments
            )
            handles_terminal = any(
                term in code_no_comments
                for term in ("FAILED", "COMPLETED", "done", "close")
            )
            if not has_close or not handles_terminal:
                findings.append(
                    {
                        "category": "sse_leak",
                        "severity": "FAIL",
                        "file": rel_path,
                        "message": (
                            f"SSE EventSource initialized in '{rel_path}' lacks explicit .close() handling "
                            f"upon reaching terminal task states, causing infinite reconnection attempts."
                        ),
                    }
                )

        # 3. 100% progress display on FAILED job guard
        # Look for hardcoded or fall-through progress: 100% when error or failed
        if re.search(
            r"""(?:status\s*===?\s*['"]FAILED['"][^;}]*progress\s*=\s*100)""",
            content,
            re.IGNORECASE,
        ):
            findings.append(
                {
                    "category": "invalid_progress_state",
                    "severity": "FAIL",
                    "file": rel_path,
                    "message": (
                        f"Job status 'FAILED' sets progress to 100% in '{rel_path}'. "
                        f"Failed jobs must preserve incomplete progress state."
                    ),
                }
            )

    return findings


def run_all_ui_reviews(
    repo_root: Path | str = ".",
    base_ref: str = "main",
) -> dict[str, Any]:
    """Execute all four UI review invariant checks and aggregate findings."""
    root = Path(repo_root).resolve()
    modified_files = get_git_diff_files(root, base_ref=base_ref)

    all_findings: list[dict[str, Any]] = []

    # Invariant 1
    all_findings.extend(audit_cache_busting(root, modified_files, base_ref=base_ref))

    # Invariant 2
    all_findings.extend(audit_orphaned_classes_and_styles(root))

    # Invariant 3
    all_findings.extend(audit_text_truncation_and_overflow(root))

    # Invariant 4
    all_findings.extend(audit_ui_state_machine_consistency(root))

    status = "PASS" if len(all_findings) == 0 else "FAIL"
    return {
        "status": status,
        "base_ref": base_ref,
        "modified_files_count": len(modified_files),
        "total_findings": len(all_findings),
        "findings": all_findings,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for audit_ui_state_and_styles."""
    parser = argparse.ArgumentParser(
        description="Audit UI/UX state, styling invariants, cache-busting, and state machine consistency."
    )
    parser.add_argument(
        "--base-ref",
        default="main",
        help="Git base branch or reference for diff analysis (default: main).",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Root path of the project to audit (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output findings as JSON.",
    )

    args = parser.parse_args(argv)
    res = run_all_ui_reviews(repo_root=args.project_root, base_ref=args.base_ref)

    if args.json:
        print(json.dumps(res, indent=2))
    else:
        if res["status"] == "PASS":
            print(
                f"UI Review: PASS ({res['total_findings']} findings across {res['modified_files_count']} modified files)"
            )
        else:
            print(
                f"UI Review: FAIL ({res['total_findings']} findings)", file=sys.stderr
            )
            for f in res["findings"]:
                loc = f.get("file", "unknown")
                msg = f.get("message", "")
                cat = f.get("category", "")
                print(f"  • [{cat}] {loc}: {msg}", file=sys.stderr)

    return 0 if res["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
