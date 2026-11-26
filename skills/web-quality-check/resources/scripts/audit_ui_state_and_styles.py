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
from collections import Counter
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

EXCLUDED_DIRS = frozenset(
    {
        "node_modules",
        "build",
        ".worktrees",
        ".git",
        "dist",
        ".astro",
        ".devtool",
        "docs",
        "target",
        "tests",
    }
)

STYLESHEET_EXTENSIONS = frozenset({".css", ".scss"})
COMPONENT_STYLE_EXTENSIONS = frozenset(
    {".astro", ".html", ".jinja", ".jinja2", ".vue", ".svelte"}
)

CLASS_DEF_PATTERN = re.compile(r"\.([A-Za-z0-9_-]+)(?=[^\{]*\{)")
STYLE_BLOCK_PATTERN = re.compile(
    r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE
)
CLASS_REF_PATTERN = re.compile(r"""(?:class|className)=['"]([^'"]+)['"]""")
UNSTYLED_CARD_PATTERN = re.compile(
    r"""<(?:div|section|aside|span)[^>]*class=['"][^'"]*?\b(card|drawer|badge|panel|modal)\b[^'"]*?['"][^>]*style=['"][^'"]*?(?:background:\s*(?:transparent|none)|border:\s*0|padding:\s*0)[^'"]*?['"]""",
    re.IGNORECASE,
)
DUPLICATE_PHRASE_PATTERN = re.compile(
    r"""(?:^|[\s"'>])([A-Za-zÀ-ỹ0-9_]{2,}(?:\s+[A-Za-zÀ-ỹ0-9_]{2,})*)\s+\1(?=$|[\s<"'\.,;!?:])""",
    re.IGNORECASE | re.UNICODE,
)
LEFT_CLIP_PATTERN = re.compile(
    r"""display:\s*flex[^;]*;[^}]*justify-content:\s*(?:flex-end|end|right)[^}]*text-overflow:\s*ellipsis""",
    re.IGNORECASE,
)
INVALID_PROGRESS_PATTERN = re.compile(
    r"""(?:status\s*===?\s*['"]FAILED['"][^;}]*progress\s*=\s*100)""",
    re.IGNORECASE,
)

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
    """Retrieve ordered unique modified/added files (committed + working-tree/staged/untracked) vs base_ref."""
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
            return []

        top_proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        resolved_root = repo_root.resolve()
        top_level = (
            Path(top_proc.stdout.strip()).resolve()
            if top_proc.returncode == 0 and top_proc.stdout.strip()
            else resolved_root
        )

        def normalize_diff_lines(lines: list[str]) -> list[str]:
            res: list[str] = []
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                p = Path(stripped)
                if top_level != resolved_root:
                    try:
                        rel_from_top = resolved_root.relative_to(top_level)
                        if p.is_relative_to(rel_from_top):
                            res.append(p.relative_to(rel_from_top).as_posix())
                    except ValueError:
                        pass
                else:
                    res.append(p.as_posix())
            return res

        merged: list[str] = []
        seen: set[str] = set()

        def add_unique(paths: list[str]) -> None:
            for item in paths:
                if item and item not in seen:
                    seen.add(item)
                    merged.append(item)

        # 1. Committed branch diff (3-dot, falling back to 2-dot if 3-dot fails)
        diff_proc = subprocess.run(
            ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if diff_proc.returncode == 0:
            add_unique(normalize_diff_lines(diff_proc.stdout.splitlines()))
        else:
            diff_proc2 = subprocess.run(
                ["git", "diff", "--name-only", base_ref],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if diff_proc2.returncode == 0:
                add_unique(normalize_diff_lines(diff_proc2.stdout.splitlines()))

        # 2. Working-tree tracked modifications against HEAD
        wt_proc = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if wt_proc.returncode == 0:
            add_unique(normalize_diff_lines(wt_proc.stdout.splitlines()))

        # 3. Staged changes
        cached_proc = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if cached_proc.returncode == 0:
            add_unique(normalize_diff_lines(cached_proc.stdout.splitlines()))

        # 4. Non-ignored untracked files under repo_root (git ls-files emits paths relative to cwd)
        untracked_proc = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if untracked_proc.returncode == 0:
            untracked_paths = [
                Path(line.strip()).as_posix()
                for line in untracked_proc.stdout.splitlines()
                if line.strip()
            ]
            add_unique(untracked_paths)

        return merged

    except (subprocess.SubprocessError, OSError):
        pass
    return []


def _is_excluded(p: Path, repo_root: Path) -> bool:
    try:
        rel_parts = p.relative_to(repo_root).parts
    except ValueError:
        try:
            rel_parts = p.resolve().relative_to(repo_root.resolve()).parts
        except ValueError:
            rel_parts = p.parts
    return any(part in EXCLUDED_DIRS for part in rel_parts)


def _normalize_repo_rel_path(rel_path: str) -> str | None:
    """Normalize a repo-relative path to POSIX form, preserving dot-prefixed dirs and rejecting traversal."""
    if not rel_path or not rel_path.strip():
        return None
    if rel_path.startswith("/") or Path(rel_path).is_absolute():
        return None
    raw_posix = Path(rel_path.replace("\\", "/")).as_posix()
    if raw_posix.startswith("/"):
        return None
    norm_rel = raw_posix
    while norm_rel.startswith("./"):
        norm_rel = norm_rel[2:]
    if not norm_rel or norm_rel in (".", ".."):
        return None
    if ".." in Path(norm_rel).parts:
        return None
    return norm_rel


def _get_base_file_content(repo_root: Path, base_ref: str, rel_path: str) -> str | None:
    norm_rel = _normalize_repo_rel_path(rel_path)
    if norm_rel is None:
        return None
    try:
        res = subprocess.run(
            ["git", "show", f"{base_ref}:./{norm_rel}"],
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

    # Find modified static .js or .css files (excluding build/test/docs directories)
    static_mods = [
        f
        for f in modified_files
        if f.endswith((".js", ".css"))
        and not f.endswith((".test.js", ".spec.js", ".fixture.ts"))
        and not _is_excluded(repo_root / f, repo_root)
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
                rel_tpl = tpl.relative_to(repo_root).as_posix()
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


def _extract_defined_classes_from_css(css_text: str) -> set[str]:
    return {m.group(1) for m in CLASS_DEF_PATTERN.finditer(css_text)}


def _extract_defined_classes_from_component(comp_text: str) -> set[str]:
    classes: set[str] = set()
    for sm in STYLE_BLOCK_PATTERN.finditer(comp_text):
        for m in CLASS_DEF_PATTERN.finditer(sm.group(1)):
            classes.add(m.group(1))
    return classes


def _extract_referenced_classes(content: str) -> set[str]:
    classes: set[str] = set()
    for cm in CLASS_REF_PATTERN.finditer(content):
        classes.update(cm.group(1).split())
    return classes


def _unstyled_default_messages(content: str, rel_path: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for um in UNSTYLED_CARD_PATTERN.finditer(content):
        comp_type = um.group(1)
        msg = (
            f"Component '{comp_type}' in '{rel_path}' renders with unstyled default geometry "
            f"(transparent background, 0px border, or 0px padding)."
        )
        counts[msg] += 1
    return counts


def _duplicate_phrase_counts(content: str, rel_path: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    if "test_" in rel_path or "mock" in rel_path.lower():
        return counts
    for line in content.splitlines():
        dup_match = DUPLICATE_PHRASE_PATTERN.search(line)
        if dup_match:
            phrase = dup_match.group(1)
            if len(phrase) >= 4 and not phrase.startswith(("//", "/*", "#")):
                counts[phrase.lower()] += 1
    return counts


def _state_machine_contradiction_messages(content: str, rel_path: str) -> set[str]:
    msgs: set[str] = set()
    for prefix in ACTIVE_PREFIXES:
        for term in TERMINAL_STATES:
            contradiction = f"{prefix} {term}"
            if contradiction in content:
                msgs.add(
                    f"Contradictory state string '{contradiction}' found in '{rel_path}'. "
                    f"Active running prefix cannot coexist with terminal state."
                )
    return msgs


def _has_sse_leak(content: str) -> bool:
    code_no_comments = strip_comments_preserving_strings(content)
    if "new EventSource(" not in code_no_comments:
        return False
    has_close = bool(
        re.search(r"\.close\s*\(", code_no_comments)
        or "closeConnection" in code_no_comments
    )
    handles_terminal = any(
        term in code_no_comments for term in ("FAILED", "COMPLETED", "done", "close")
    )
    return not has_close or not handles_terminal


def _collect_base_defined_classes(repo_root: Path, base_ref: str) -> set[str]:
    """Collect CSS classes defined in all non-excluded stylesheets and component <style> blocks at base_ref."""
    candidate_rels: list[str] = []
    try:
        ls_proc = subprocess.run(
            ["git", "ls-tree", "-r", "-z", "--name-only", base_ref],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if ls_proc.returncode == 0:
            candidate_rels = [
                Path(entry).as_posix() for entry in ls_proc.stdout.split("\0") if entry
            ]
    except (subprocess.SubprocessError, OSError):
        pass

    if not candidate_rels:
        for pattern in (
            "*.css",
            "*.scss",
            "*.astro",
            "*.html",
            "*.jinja",
            "*.jinja2",
            "*.vue",
            "*.svelte",
        ):
            for f in repo_root.rglob(pattern):
                if not _is_excluded(f, repo_root):
                    candidate_rels.append(f.relative_to(repo_root).as_posix())

    base_defined: set[str] = set()
    seen: set[str] = set()
    for rel_f in candidate_rels:
        if rel_f in seen or _is_excluded(repo_root / rel_f, repo_root):
            continue
        seen.add(rel_f)
        suffix = Path(rel_f).suffix.lower()
        if suffix in STYLESHEET_EXTENSIONS:
            base_text = _get_base_file_content(repo_root, base_ref, rel_f)
            if base_text is not None:
                base_defined.update(_extract_defined_classes_from_css(base_text))
        elif suffix in COMPONENT_STYLE_EXTENSIONS:
            base_text = _get_base_file_content(repo_root, base_ref, rel_f)
            if base_text is not None:
                base_defined.update(_extract_defined_classes_from_component(base_text))
    return base_defined


def _filter_preexisting_base_findings(
    repo_root: Path,
    base_ref: str,
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Suppress findings that were already present on base_ref while preserving newly introduced regressions."""
    if not findings:
        return []

    reported_files: list[str] = []
    seen_files: set[str] = set()
    for f in findings:
        rel_f = str(f.get("file", ""))
        if rel_f and rel_f not in seen_files:
            seen_files.add(rel_f)
            reported_files.append(rel_f)

    base_contents: dict[str, str | None] = {
        rel_f: _get_base_file_content(repo_root, base_ref, rel_f)
        for rel_f in reported_files
    }

    categories_present = {str(f.get("category", "")) for f in findings}
    base_defined_classes: set[str] = (
        _collect_base_defined_classes(repo_root, base_ref)
        if "orphaned_class" in categories_present
        else set()
    )
    base_ref_classes_by_file: dict[str, set[str]] = {}
    base_unstyled_by_file: dict[str, Counter[str]] = {}
    base_duplicates_by_file: dict[str, Counter[str]] = {}
    base_contradictions_by_file: dict[str, set[str]] = {}
    base_clipping_by_file: dict[str, bool] = {}
    base_sse_leak_by_file: dict[str, bool] = {}
    base_invalid_progress_by_file: dict[str, bool] = {}

    for rel_f, base_text in base_contents.items():
        if base_text is None:
            continue
        if "orphaned_class" in categories_present:
            base_ref_classes_by_file[rel_f] = _extract_referenced_classes(base_text)
        if "unstyled_default" in categories_present:
            base_unstyled_by_file[rel_f] = _unstyled_default_messages(base_text, rel_f)
        if "duplicate_text" in categories_present:
            base_duplicates_by_file[rel_f] = _duplicate_phrase_counts(base_text, rel_f)
        if "state_machine_contradiction" in categories_present:
            base_contradictions_by_file[rel_f] = _state_machine_contradiction_messages(
                base_text, rel_f
            )
        if "text_clipping" in categories_present:
            base_clipping_by_file[rel_f] = bool(LEFT_CLIP_PATTERN.search(base_text))
        if "sse_leak" in categories_present:
            base_sse_leak_by_file[rel_f] = _has_sse_leak(base_text)
        if "invalid_progress_state" in categories_present:
            base_invalid_progress_by_file[rel_f] = bool(
                INVALID_PROGRESS_PATTERN.search(base_text)
            )

    filtered: list[dict[str, Any]] = []
    for finding in findings:
        rel_f = str(finding.get("file", ""))
        base_text = base_contents.get(rel_f)
        if base_text is None:
            filtered.append(finding)
            continue

        cat = str(finding.get("category", ""))
        if cat == "orphaned_class":
            cls = str(finding.get("class", ""))
            if (
                cls in base_ref_classes_by_file.get(rel_f, set())
                and cls not in base_defined_classes
            ):
                continue
        elif cat == "unstyled_default":
            msg = str(finding.get("message", ""))
            counts = base_unstyled_by_file.get(rel_f)
            if counts and counts[msg] > 0:
                counts[msg] -= 1
                continue
        elif cat == "text_clipping":
            if base_clipping_by_file.get(rel_f, False):
                continue
        elif cat == "duplicate_text":
            phrase_key = str(finding.get("duplicate_phrase", "")).lower()
            dup_counts = base_duplicates_by_file.get(rel_f)
            if dup_counts and dup_counts[phrase_key] > 0:
                dup_counts[phrase_key] -= 1
                continue
        elif cat == "state_machine_contradiction":
            msg = str(finding.get("message", ""))
            if msg in base_contradictions_by_file.get(rel_f, set()):
                continue
        elif cat == "sse_leak":
            if base_sse_leak_by_file.get(rel_f, False):
                continue
        elif cat == "invalid_progress_state":
            if base_invalid_progress_by_file.get(rel_f, False):
                continue

        filtered.append(finding)

    return filtered


def audit_orphaned_classes_and_styles(
    repo_root: Path,
    target_files: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Invariant 2: Verify CSS classes exist and cards/drawers/badges have styled definitions."""
    findings: list[dict[str, Any]] = []

    # 1. Collect all declared CSS classes from stylesheets
    css_files: list[Path] = []
    for css_ext in ("*.css", "*.scss"):
        css_files.extend(
            f for f in repo_root.rglob(css_ext) if not _is_excluded(f, repo_root)
        )
    defined_classes: set[str] = set()

    for cf in css_files:
        try:
            css_text = cf.read_text(encoding="utf-8")
            defined_classes.update(_extract_defined_classes_from_css(css_text))
        except (OSError, UnicodeDecodeError):
            continue

    # Also collect declared CSS classes from component-scoped <style> blocks (*.astro, *.html, *.vue, etc.)
    component_files: list[Path] = []
    for ext in ("*.astro", "*.html", "*.jinja", "*.jinja2", "*.vue", "*.svelte"):
        component_files.extend(
            f for f in repo_root.rglob(ext) if not _is_excluded(f, repo_root)
        )

    for comp in component_files:
        try:
            comp_text = comp.read_text(encoding="utf-8")
            defined_classes.update(_extract_defined_classes_from_component(comp_text))
        except (OSError, UnicodeDecodeError):
            continue

    # 2. Check candidate templates and DOM builder scripts
    candidate_files: list[Path] = []
    if target_files:
        candidate_files = [
            repo_root / f for f in target_files if (repo_root / f).is_file()
        ]
    else:
        for ext in ("*.html", "*.astro", "*.jinja", "*.jinja2", "*.jsx", "*.tsx"):
            candidate_files.extend(repo_root.rglob(ext))

    candidate_files = [f for f in candidate_files if not _is_excluded(f, repo_root)]

    for cf in candidate_files:
        try:
            content = cf.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        rel_path = cf.relative_to(repo_root).as_posix()

        # Check for unstyled default component anti-pattern
        unstyled_matches = UNSTYLED_CARD_PATTERN.finditer(content)
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
        for cm in CLASS_REF_PATTERN.finditer(content):
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

    candidate_files: list[Path] = []
    if target_files:
        candidate_files = [
            repo_root / f for f in target_files if (repo_root / f).is_file()
        ]
    else:
        for ext in (
            "*.html",
            "*.astro",
            "*.jinja",
            "*.jinja2",
            "*.js",
            "*.ts",
            "*.jsx",
            "*.tsx",
        ):
            candidate_files.extend(repo_root.rglob(ext))

    candidate_files = [f for f in candidate_files if not _is_excluded(f, repo_root)]

    for cf in candidate_files:
        try:
            content = cf.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        rel_path = cf.relative_to(repo_root).as_posix()

        # Check for left-clipping flex styles
        if LEFT_CLIP_PATTERN.search(content):
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
            dup_match = DUPLICATE_PHRASE_PATTERN.search(line)
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

    candidate_files: list[Path] = []
    if target_files:
        candidate_files = [
            repo_root / f for f in target_files if (repo_root / f).is_file()
        ]
    else:
        for ext in ("*.html", "*.astro", "*.jinja", "*.jinja2", "*.js", "*.ts"):
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

        rel_path = cf.relative_to(repo_root).as_posix()

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

        # 2. SSE EventSource connection closure verification
        if _has_sse_leak(content):
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
        if INVALID_PROGRESS_PATTERN.search(content):
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


UI_FILE_EXTENSIONS = {
    ".html",
    ".htm",
    ".astro",
    ".jinja",
    ".jinja2",
    ".css",
    ".scss",
    ".js",
    ".mjs",
    ".ts",
    ".tsx",
    ".jsx",
    ".vue",
    ".svelte",
}


def _git_base_ref_exists(repo_root: Path, base_ref: str) -> bool:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--verify", base_ref],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        return res.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def run_all_ui_reviews(
    repo_root: Path | str = ".",
    base_ref: str = "main",
) -> dict[str, Any]:
    """Execute all four UI review invariant checks and aggregate findings."""
    root = Path(repo_root).resolve()
    modified_files = get_git_diff_files(root, base_ref=base_ref)
    base_ref_exists = _git_base_ref_exists(root, base_ref)
    ui_modified: list[str] = []

    # Scope-aware short-circuit: if inside a git repo with a valid base_ref and
    # diff against base_ref contains changes with zero non-excluded UI files,
    # skip UI review with NOT_APPLICABLE (scope_unmodified).
    if base_ref_exists:
        ui_modified = [
            f
            for f in modified_files
            if Path(f).suffix.lower() in UI_FILE_EXTENSIONS
            and not _is_excluded(root / f, root)
        ]
        if len(modified_files) > 0 and len(ui_modified) == 0:
            return {
                "status": "NOT_APPLICABLE",
                "not_applicable_reason": {
                    "code": "scope_unmodified",
                    "detail": f"No UI/frontend files were modified in {len(modified_files)} changed file(s) against '{base_ref}'.",
                },
                "base_ref": base_ref,
                "modified_files_count": len(modified_files),
                "ui_modified_files_count": 0,
                "total_findings": 0,
                "findings": [],
            }

    all_findings: list[dict[str, Any]] = []

    # Invariant 1
    all_findings.extend(audit_cache_busting(root, modified_files, base_ref=base_ref))

    # Invariants 2, 3, and 4
    scoped_mode = base_ref_exists and len(ui_modified) > 0
    if scoped_mode:
        has_css_change = any(
            Path(f).suffix.lower() in STYLESHEET_EXTENSIONS for f in ui_modified
        )
        inv2_targets: list[str] | None = None if has_css_change else ui_modified
        inv34_targets: list[str] | None = ui_modified
    else:
        inv2_targets = None
        inv34_targets = None

    inv234: list[dict[str, Any]] = []
    inv234.extend(audit_orphaned_classes_and_styles(root, target_files=inv2_targets))
    inv234.extend(audit_text_truncation_and_overflow(root, target_files=inv34_targets))
    inv234.extend(audit_ui_state_machine_consistency(root, target_files=inv34_targets))

    if scoped_mode and inv234:
        inv234 = _filter_preexisting_base_findings(root, base_ref, inv234)

    all_findings.extend(inv234)

    status = "PASS" if len(all_findings) == 0 else "FAIL"
    return {
        "status": status,
        "base_ref": base_ref,
        "modified_files_count": len(modified_files),
        "ui_modified_files_count": len(ui_modified),
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
        if res["status"] == "NOT_APPLICABLE":
            reason = res.get("not_applicable_reason", {}).get(
                "detail", "scope_unmodified"
            )
            print(f"UI Review: NOT_APPLICABLE ({reason})")
        elif res["status"] == "PASS":
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

    return 0 if res["status"] in ("PASS", "NOT_APPLICABLE") else 1


if __name__ == "__main__":
    sys.exit(main())
