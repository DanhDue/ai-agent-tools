#!/usr/bin/env python3
"""Portable Multi-Format Hunk-Level Diff-Coverage Engine.

Parses LCOV, Cobertura XML, and JaCoCo XML coverage reports using Python 3
stdlib only, merges multiple reports by max hit count per (file, line),
enforces workspace + per-package dual-floor thresholds and git hunk-level
diff-coverage floors, detects uncovered executable lines in untested new files,
and emits a compact single-line PASS summary by default (--verbose / --json).

Exit codes:
  0 = PASS
  1 = FAIL (workspace, package, or diff coverage threshold breach)
  2 = BLOCKED (missing file, corrupt XML/LCOV, invalid git ref or flag)
"""

from __future__ import annotations

import argparse
import json
import math
import posixpath
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NoReturn

DEFAULT_PACKAGE_GROUPS: tuple[str, ...] = (
    "packages",
    "features",
    "crates",
    "apps",
    "services",
    "modules",
    "libs",
    "src",
)

DEFAULT_EXCLUDE_SUFFIXES: tuple[str, ...] = (
    ".g.dart",
    ".freezed.dart",
    ".gen.dart",
    ".pb.dart",
    ".pb.rs",
    ".pb.swift",
    ".d.ts",
    "GeneratedPluginRegistrant.swift",
)

DEFAULT_SOURCE_EXTS: tuple[str, ...] = (
    ".py",
    ".dart",
    ".rs",
    ".ts",
    ".tsx",
    ".js",
    ".mjs",
    ".astro",
    ".kt",
    ".kts",
    ".swift",
)

_JVM_COMMON_ROOTS: tuple[str, ...] = (
    "src/main/kotlin",
    "src/main/java",
    "app/src/main/kotlin",
    "app/src/main/java",
    "src",
)

_TEST_DIR_SEGMENTS: frozenset[str] = frozenset(
    {
        "test",
        "tests",
        "__tests__",
        "integration_test",
        "androidtest",
        "unittests",
        "uitests",
    }
)

_TEST_FILE_SUFFIXES: tuple[str, ...] = (
    "_test.dart",
    "_test.py",
    "_test.rs",
    "_test.go",
    ".test.ts",
    ".spec.ts",
    ".test.tsx",
    ".spec.tsx",
    ".test.js",
    ".spec.js",
    ".test.mjs",
    ".spec.mjs",
    "test.kt",
    "tests.kt",
    "spec.kt",
    "test.java",
    "tests.java",
    "test.swift",
    "tests.swift",
)

_WIN_ABS_RE = re.compile(r"^[A-Za-z]:/")
_ROOT_LIB_OR_SRC_RE = re.compile(r"^.*/((?:lib|src)/.+)$")
_HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
_LINE_SPEC_RE = re.compile(r"^(.+):(\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*)$")
_PUNCT_ONLY_RE = re.compile(r"^[\{\}\(\)\[\];,:]+$")
_RUST_MOD_DECL_RE = re.compile(r"^(?:pub\s+)?mod\s+[A-Za-z_][A-Za-z0-9_]*\s*;$")
_STRUCTURAL_KEYWORD_RE = re.compile(
    r"^(?:\}?\s*else\s*(?:\{|:)?|try\s*(?:\{|:)?|finally\s*(?:\{|:)?)$"
)
_PY_DOCSTRING_PREFIX_RE = re.compile(r'^[rRbBuUfF]{0,2}("""|\'\'\')')
_FLOAT_EPS = 1e-9
_FLOOR_METADATA_KEYS: frozenset[str] = frozenset(
    {"schema_version", "description", "default_core_floor"}
)
_FILE_FLOOR_EXTRA_EXTS: frozenset[str] = frozenset({".jsx", ".cjs", ".vue", ".svelte"})


class BlockedError(Exception):
    """Raised when execution cannot proceed cleanly (exit code 2)."""


@dataclass(frozen=True)
class CustomFloorSpec:
    """Normalized adapter/package prefix and file-level coverage ratchets."""

    prefix_floors: dict[str, float] = field(default_factory=dict)
    file_floors: dict[str, float] = field(default_factory=dict)


@dataclass
class CoverageDataset:
    """Canonical multi-format coverage representation."""

    da_by_file: dict[str, dict[int, int]] = field(default_factory=dict)
    fallback_by_file: dict[str, tuple[int, int]] = field(default_factory=dict)

    def merge(self, other: CoverageDataset) -> None:
        """Merge another dataset into this one using max hit counts per line."""
        for sf, line_hits in other.da_by_file.items():
            target = self.da_by_file.setdefault(sf, {})
            for lineno, hits in line_hits.items():
                existing = target.get(lineno)
                target[lineno] = hits if existing is None else max(existing, hits)
        for sf, (lh, lf) in other.fallback_by_file.items():
            prev_lh, prev_lf = self.fallback_by_file.get(sf, (0, 0))
            self.fallback_by_file[sf] = (max(prev_lh, lh), max(prev_lf, lf))


@dataclass(frozen=True)
class EvaluationResult:
    """Structured result of dual-floor and hunk-level diff coverage evaluation."""

    status: str
    coverage_pct: float
    min_coverage_pct: float
    coverage_checked: bool
    total_covered: int
    total_lines: int
    diff_coverage_pct: float | None
    min_diff_coverage_pct: float | None
    diff_covered: int
    diff_lines: int
    package_results: list[dict[str, Any]]
    file_results: list[dict[str, Any]]
    diff_files: list[dict[str, Any]]
    failures: list[str]
    custom_floor_results: list[dict[str, Any]] = field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        """Serialize into the canonical machine-readable JSON contract."""
        return {
            "status": self.status,
            "coverage_pct": round(self.coverage_pct, 2),
            "min_coverage_pct": round(self.min_coverage_pct, 2),
            "diff_coverage_pct": (
                round(self.diff_coverage_pct, 2)
                if self.diff_coverage_pct is not None
                else None
            ),
            "min_diff_coverage_pct": (
                round(self.min_diff_coverage_pct, 2)
                if self.min_diff_coverage_pct is not None
                else None
            ),
            "package_results": self.package_results,
            "custom_floor_results": self.custom_floor_results,
            "diff_files": self.diff_files,
            "failures": self.failures,
        }


class _BlockedArgumentParser(argparse.ArgumentParser):
    """ArgumentParser subclass converting CLI usage errors into BlockedError."""

    def error(self, message: str) -> NoReturn:
        raise BlockedError(message)


def _local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _normalize_threshold(value: float, flag_name: str) -> float:
    """Normalize [0.0, 1.0] or (1.0, 100.0] thresholds to percentage [0.0, 100.0]."""
    if math.isnan(value) or math.isinf(value) or value < 0.0 or value > 100.0:
        raise BlockedError(
            f"Invalid threshold for {flag_name}: {value} (expected 0..1 or 0..100)"
        )
    if value <= 1.0:
        return round(value * 100.0, 6)
    return float(value)


def _split_csv_args(raw_values: Sequence[str]) -> list[str]:
    items: list[str] = []
    for raw in raw_values:
        for token in raw.split(","):
            clean = token.strip()
            if clean and clean not in items:
                items.append(clean)
    return items


def _normalize_rel_path(path_str: str) -> str:
    clean = path_str.strip().replace("\\", "/")
    if not clean:
        return ""
    norm = posixpath.normpath(clean)
    while norm.startswith("./"):
        norm = norm[2:]
    if norm == ".":
        return ""
    return norm.strip("/")


def _normalize_source_exts(raw_exts: Sequence[str]) -> tuple[str, ...]:
    tokens = _split_csv_args(raw_exts)
    if not tokens:
        return DEFAULT_SOURCE_EXTS
    normalized: list[str] = []
    for tok in tokens:
        low = tok.lower()
        if not low.startswith("."):
            low = f".{low}"
        if low not in normalized:
            normalized.append(low)
    return tuple(normalized)


def _normalize_exclude_suffixes(raw_suffixes: Sequence[str]) -> tuple[str, ...]:
    merged = list(DEFAULT_EXCLUDE_SUFFIXES)
    for tok in _split_csv_args(raw_suffixes):
        if tok not in merged:
            merged.append(tok)
    return tuple(merged)


def _normalize_package_groups(raw_groups: Sequence[str]) -> tuple[str, ...]:
    tokens = [_normalize_rel_path(t) for t in _split_csv_args(raw_groups)]
    filtered = [t for t in tokens if t]
    return tuple(filtered) if filtered else DEFAULT_PACKAGE_GROUPS


def _is_excluded_source(
    canonical_sf: str,
    exclude_suffixes: tuple[str, ...] = DEFAULT_EXCLUDE_SUFFIXES,
) -> bool:
    return (
        canonical_sf.endswith(exclude_suffixes)
        or "/generated/" in canonical_sf
        or canonical_sf.startswith("generated/")
    )


def _is_test_file_path(canonical_path: str) -> bool:
    parts = Path(canonical_path).parts
    name_lower = Path(canonical_path).name.lower()
    if any(seg.lower() in _TEST_DIR_SEGMENTS for seg in parts[:-1]):
        return True
    if name_lower.startswith("test_"):
        return True
    return name_lower.endswith(_TEST_FILE_SUFFIXES)


def _infer_subpackage_prefix(
    report_file: Path,
    repo_root: Path,
    package_groups: tuple[str, ...],
) -> str:
    for rep_cand, root_cand in (
        (report_file.resolve(), repo_root.resolve()),
        (report_file.absolute(), repo_root.absolute()),
    ):
        try:
            rel = rep_cand.relative_to(root_cand).as_posix()
        except ValueError:
            continue
        parts = rel.split("/")
        if len(parts) >= 3 and parts[0] in package_groups:
            return f"{parts[0]}/{parts[1]}"
    return ""


def _match_package_group_tail(raw_path: str, package_groups: tuple[str, ...]) -> str:
    escaped = "|".join(re.escape(g) for g in package_groups)
    pattern = re.compile(rf"^.*/((?:{escaped})/[^/]+/.+)$")
    match = pattern.match(raw_path)
    if match:
        return posixpath.normpath(match.group(1))
    return ""


def _probe_jvm_path(
    rel_path: str,
    repo_root: Path,
    package_groups: tuple[str, ...],
) -> str:
    for root in _JVM_COMMON_ROOTS:
        cand = posixpath.normpath(f"{root}/{rel_path}")
        if (repo_root / cand).is_file():
            return cand

    matches: list[str] = []
    for group in package_groups:
        group_dir = repo_root / group
        if not group_dir.is_dir():
            continue
        for child in sorted(group_dir.iterdir()):
            if not child.is_dir():
                continue
            for lang in ("kotlin", "java"):
                cand = posixpath.normpath(
                    f"{group}/{child.name}/src/main/{lang}/{rel_path}"
                )
                if (repo_root / cand).is_file():
                    matches.append(cand)
    if len(matches) == 1:
        return matches[0]
    return ""


def _normalize_source_path(
    raw_path: str,
    repo_root: Path,
    *,
    package_groups: tuple[str, ...] = DEFAULT_PACKAGE_GROUPS,
    subpackage_prefix: str = "",
    source_roots: tuple[str, ...] = (),
    probe_jvm_roots: bool = False,
) -> str:
    raw = raw_path.strip().replace("\\", "/")
    if not raw:
        return ""

    is_win_abs = bool(_WIN_ABS_RE.match(raw)) or raw.startswith("//")
    if is_win_abs:
        repo_norm = str(repo_root).strip().replace("\\", "/").rstrip("/")
        repo_is_win_abs = bool(_WIN_ABS_RE.match(repo_norm)) or repo_norm.startswith(
            "//"
        )
        if repo_is_win_abs and raw.lower().startswith(f"{repo_norm.lower()}/"):
            return _normalize_rel_path(raw[len(repo_norm) + 1 :])
        pkg_tail = _match_package_group_tail(raw, package_groups)
        if pkg_tail:
            return pkg_tail
        root_match = _ROOT_LIB_OR_SRC_RE.match(raw)
        if root_match:
            return posixpath.normpath(root_match.group(1))
        return posixpath.normpath(re.sub(r"^[A-Za-z]:", "", raw))

    is_posix_abs = raw.startswith("/") or Path(raw).is_absolute()
    if is_posix_abs:
        candidate = Path(raw)
        for base in (repo_root.resolve(), repo_root.absolute()):
            try:
                return candidate.resolve().relative_to(base).as_posix()
            except ValueError:
                pass
            try:
                return candidate.relative_to(base).as_posix()
            except ValueError:
                pass
        pkg_tail = _match_package_group_tail(raw, package_groups)
        if pkg_tail:
            return pkg_tail
        root_match = _ROOT_LIB_OR_SRC_RE.match(raw)
        if root_match:
            return posixpath.normpath(root_match.group(1))
        return posixpath.normpath(raw)

    normalized = _normalize_rel_path(raw)
    if not normalized:
        return ""

    if (repo_root / normalized).is_file():
        return normalized

    for sr in source_roots:
        clean_sr = _normalize_rel_path(sr)
        if not clean_sr:
            continue
        prefixed = posixpath.normpath(f"{clean_sr}/{normalized}")
        if (repo_root / prefixed).is_file():
            return prefixed

    group_prefixes = tuple(f"{g}/" for g in package_groups)
    if subpackage_prefix and not normalized.startswith(group_prefixes):
        prefixed = posixpath.normpath(f"{subpackage_prefix}/{normalized}")
        if (repo_root / prefixed).is_file() or not (repo_root / normalized).exists():
            return prefixed

    if probe_jvm_roots and not normalized.startswith(group_prefixes):
        probed = _probe_jvm_path(normalized, repo_root, package_groups)
        if probed:
            return probed

    if source_roots and not normalized.startswith(group_prefixes):
        first_sr = _normalize_rel_path(source_roots[0])
        if first_sr and not normalized.startswith(f"{first_sr}/"):
            return posixpath.normpath(f"{first_sr}/{normalized}")

    return normalized


def _bucket_for_path(canonical_sf: str, package_groups: tuple[str, ...]) -> str:
    parts = canonical_sf.split("/")
    if len(parts) >= 3 and parts[0] in package_groups:
        return f"{parts[0]}/{parts[1]}"
    if len(parts) == 2 and parts[0] in package_groups:
        return parts[0]
    return "root"


def detect_format(text: str, source_name: str = "<input>") -> str:
    """Auto-detect coverage report format: 'cobertura', 'jacoco', or 'lcov'."""
    stripped = text.lstrip("\ufeff \t\r\n")
    if not stripped:
        raise BlockedError(f"Empty coverage report '{source_name}'")

    if stripped.startswith("<"):
        try:
            root = ET.fromstring(stripped)
        except ET.ParseError as exc:
            raise BlockedError(
                f"Malformed XML coverage report '{source_name}': {exc}"
            ) from None
        root_tag = _local_tag(root.tag)
        if root_tag == "coverage":
            return "cobertura"
        if root_tag == "report":
            return "jacoco"
        raise BlockedError(
            f"Unsupported XML coverage root <{root.tag}> in '{source_name}' "
            "(expected <coverage> or <report>)"
        )

    for raw_line in stripped.splitlines():
        line = raw_line.strip()
        if line.startswith("SF:") or line == "end_of_record":
            return "lcov"

    raise BlockedError(
        f"Unrecognized coverage report format in '{source_name}' "
        "(expected LCOV, Cobertura XML, or JaCoCo XML)"
    )


def _parse_int(raw: str, label: str, source_name: str) -> int:
    try:
        return int(raw.strip())
    except ValueError:
        raise BlockedError(
            f"Malformed integer for {label} in '{source_name}': {raw!r}"
        ) from None


def parse_lcov(
    text: str,
    repo_root: Path,
    *,
    subpackage_prefix: str = "",
    source_roots: tuple[str, ...] = (),
    package_groups: tuple[str, ...] = DEFAULT_PACKAGE_GROUPS,
    exclude_suffixes: tuple[str, ...] = DEFAULT_EXCLUDE_SUFFIXES,
    source_name: str = "<lcov>",
) -> CoverageDataset:
    """Parse LCOV text into a canonical CoverageDataset."""
    has_marker = any(
        ln.strip().startswith("SF:") or ln.strip() == "end_of_record"
        for ln in text.splitlines()
    )
    if not has_marker:
        raise BlockedError(
            f"Invalid LCOV report '{source_name}': missing SF: or end_of_record markers"
        )

    dataset = CoverageDataset()
    current_sf = ""
    skip = True
    section_has_da = False
    section_lf: int | None = None
    section_lh: int | None = None
    section_da_hits: dict[int, int] = {}

    def flush_section() -> None:
        nonlocal section_has_da, section_lf, section_lh
        if not skip and current_sf:
            if not section_has_da and (
                section_lf is not None or section_lh is not None
            ):
                lf = max(section_lf or 0, 0)
                lh = max(min(section_lh or 0, lf), 0)
                prev_lh, prev_lf = dataset.fallback_by_file.get(current_sf, (0, 0))
                dataset.fallback_by_file[current_sf] = (
                    max(prev_lh, lh),
                    max(prev_lf, lf),
                )
            elif (
                section_has_da
                and section_lf is not None
                and section_lf > len(section_da_hits)
            ):
                lf = max(section_lf, 0)
                da_sec_lh = sum(1 for v in section_da_hits.values() if v > 0)
                lh = max(
                    min(section_lh if section_lh is not None else da_sec_lh, lf),
                    da_sec_lh,
                )
                prev_lh, prev_lf = dataset.fallback_by_file.get(current_sf, (0, 0))
                dataset.fallback_by_file[current_sf] = (
                    max(prev_lh, lh),
                    max(prev_lf, lf),
                )
        section_has_da = False
        section_lf = None
        section_lh = None
        section_da_hits.clear()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("SF:"):
            flush_section()
            current_sf = _normalize_source_path(
                line[3:],
                repo_root,
                package_groups=package_groups,
                subpackage_prefix=subpackage_prefix,
                source_roots=source_roots,
            )
            skip = not current_sf or _is_excluded_source(current_sf, exclude_suffixes)
        elif line == "end_of_record":
            flush_section()
            current_sf = ""
            skip = True
        elif skip:
            continue
        elif line.startswith("DA:"):
            da_parts = line[3:].split(",")
            if len(da_parts) < 2:
                raise BlockedError(f"Malformed LCOV DA line in '{source_name}': {line}")
            line_no = _parse_int(da_parts[0], "DA line", source_name)
            hits = _parse_int(da_parts[1], "DA hits", source_name)
            file_lines = dataset.da_by_file.setdefault(current_sf, {})
            existing = file_lines.get(line_no)
            file_lines[line_no] = hits if existing is None else max(existing, hits)
            sec_existing = section_da_hits.get(line_no)
            section_da_hits[line_no] = (
                hits if sec_existing is None else max(sec_existing, hits)
            )
            section_has_da = True
        elif line.startswith("LF:"):
            section_lf = _parse_int(line[3:] or "0", "LF", source_name)
        elif line.startswith("LH:"):
            section_lh = _parse_int(line[3:] or "0", "LH", source_name)

    flush_section()
    return dataset


def _extract_cobertura_source_roots(root: ET.Element, repo_root: Path) -> list[str]:
    extracted: list[str] = []
    for elem in root.iter():
        if _local_tag(elem.tag) != "source" or not elem.text:
            continue
        raw_src = elem.text.strip().replace("\\", "/")
        if not raw_src:
            continue
        cand = Path(raw_src)
        rel_prefix = ""
        if cand.is_absolute() or raw_src.startswith("/"):
            for base in (repo_root.resolve(), repo_root.absolute()):
                try:
                    rel = cand.resolve().relative_to(base).as_posix()
                    rel_prefix = "" if rel == "." else rel
                    break
                except ValueError:
                    pass
                try:
                    rel = cand.relative_to(base).as_posix()
                    rel_prefix = "" if rel == "." else rel
                    break
                except ValueError:
                    pass
        else:
            rel_prefix = _normalize_rel_path(raw_src)
        if rel_prefix and rel_prefix not in extracted:
            extracted.append(rel_prefix)
    return extracted


def parse_cobertura_xml(
    text: str,
    repo_root: Path,
    *,
    subpackage_prefix: str = "",
    source_roots: tuple[str, ...] = (),
    package_groups: tuple[str, ...] = DEFAULT_PACKAGE_GROUPS,
    exclude_suffixes: tuple[str, ...] = DEFAULT_EXCLUDE_SUFFIXES,
    source_name: str = "<cobertura>",
) -> CoverageDataset:
    """Parse Cobertura XML into a canonical CoverageDataset."""
    try:
        root = ET.fromstring(text.lstrip("\ufeff \t\r\n"))
    except ET.ParseError as exc:
        raise BlockedError(f"Malformed Cobertura XML '{source_name}': {exc}") from None

    if _local_tag(root.tag) != "coverage":
        raise BlockedError(
            f"Invalid Cobertura XML '{source_name}': root tag is <{root.tag}>, expected <coverage>"
        )

    xml_roots = _extract_cobertura_source_roots(root, repo_root)
    merged_roots = tuple(dict.fromkeys([*source_roots, *xml_roots]))

    dataset = CoverageDataset()
    for elem in root.iter():
        if _local_tag(elem.tag) != "class":
            continue
        filename = elem.get("filename", "").strip()
        if not filename:
            continue
        canonical_sf = _normalize_source_path(
            filename,
            repo_root,
            package_groups=package_groups,
            subpackage_prefix=subpackage_prefix,
            source_roots=merged_roots,
        )
        if not canonical_sf or _is_excluded_source(canonical_sf, exclude_suffixes):
            continue

        file_lines = dataset.da_by_file.setdefault(canonical_sf, {})
        for child in elem.iter():
            if _local_tag(child.tag) != "line":
                continue
            num_raw = child.get("number")
            hits_raw = child.get("hits")
            if num_raw is None or hits_raw is None:
                continue
            line_no = _parse_int(num_raw, "line number", source_name)
            hits = _parse_int(hits_raw, "line hits", source_name)
            existing = file_lines.get(line_no)
            file_lines[line_no] = hits if existing is None else max(existing, hits)
        if not file_lines:
            dataset.da_by_file.pop(canonical_sf, None)

    return dataset


def parse_jacoco_xml(
    text: str,
    repo_root: Path,
    *,
    subpackage_prefix: str = "",
    source_roots: tuple[str, ...] = (),
    package_groups: tuple[str, ...] = DEFAULT_PACKAGE_GROUPS,
    exclude_suffixes: tuple[str, ...] = DEFAULT_EXCLUDE_SUFFIXES,
    source_name: str = "<jacoco>",
) -> CoverageDataset:
    """Parse JaCoCo XML into a canonical CoverageDataset."""
    try:
        root = ET.fromstring(text.lstrip("\ufeff \t\r\n"))
    except ET.ParseError as exc:
        raise BlockedError(f"Malformed JaCoCo XML '{source_name}': {exc}") from None

    if _local_tag(root.tag) != "report":
        raise BlockedError(
            f"Invalid JaCoCo XML '{source_name}': root tag is <{root.tag}>, expected <report>"
        )

    dataset = CoverageDataset()
    for pkg in root.iter():
        if _local_tag(pkg.tag) != "package":
            continue
        pkg_name = pkg.get("name", "").strip().strip("/")
        for sf_elem in pkg:
            if _local_tag(sf_elem.tag) != "sourcefile":
                continue
            sf_name = sf_elem.get("name", "").strip()
            if not sf_name:
                continue
            raw_rel = f"{pkg_name}/{sf_name}" if pkg_name else sf_name
            canonical_sf = _normalize_source_path(
                raw_rel,
                repo_root,
                package_groups=package_groups,
                subpackage_prefix=subpackage_prefix,
                source_roots=source_roots,
                probe_jvm_roots=True,
            )
            if not canonical_sf or _is_excluded_source(canonical_sf, exclude_suffixes):
                continue

            has_lines = False
            line_counter: tuple[int, int] | None = None
            for child in sf_elem:
                tag = _local_tag(child.tag)
                if tag == "line":
                    nr_raw = child.get("nr")
                    if nr_raw is None:
                        continue
                    line_no = _parse_int(nr_raw, "line nr", source_name)
                    ci = _parse_int(child.get("ci") or "0", "line ci", source_name)
                    mi = _parse_int(child.get("mi") or "0", "line mi", source_name)
                    cb = _parse_int(child.get("cb") or "0", "line cb", source_name)
                    _ = mi
                    hits = 1 if (ci > 0 or (ci == 0 and mi == 0 and cb > 0)) else 0
                    file_lines = dataset.da_by_file.setdefault(canonical_sf, {})
                    existing = file_lines.get(line_no)
                    file_lines[line_no] = (
                        hits if existing is None else max(existing, hits)
                    )
                    has_lines = True
                elif tag == "counter" and (child.get("type") or "").upper() == "LINE":
                    missed = _parse_int(
                        child.get("missed") or "0", "LINE missed", source_name
                    )
                    covered = _parse_int(
                        child.get("covered") or "0", "LINE covered", source_name
                    )
                    line_counter = (max(covered, 0), max(covered + missed, 0))

            if not has_lines and line_counter is not None:
                prev_lh, prev_lf = dataset.fallback_by_file.get(canonical_sf, (0, 0))
                dataset.fallback_by_file[canonical_sf] = (
                    max(prev_lh, line_counter[0]),
                    max(prev_lf, line_counter[1]),
                )

    return dataset


def _in_diff_scope(
    rel_path: str,
    repo_root: Path,
    source_exts: tuple[str, ...],
    exclude_suffixes: tuple[str, ...],
    subpackage_prefix: str,
    explicit_files: set[str],
    *,
    require_on_disk: bool = True,
) -> bool:
    if not rel_path or not rel_path.lower().endswith(source_exts):
        return False
    if _is_excluded_source(rel_path, exclude_suffixes) or _is_test_file_path(rel_path):
        return False
    if require_on_disk and not (repo_root / rel_path).is_file():
        return False
    if explicit_files:
        return any(
            rel_path == exp or rel_path.startswith(f"{exp}/") for exp in explicit_files
        )
    if subpackage_prefix:
        return rel_path.startswith(f"{subpackage_prefix}/")
    return True


def collect_git_diff_lines(
    repo_root: Path,
    diff_base: str,
    *,
    source_exts: tuple[str, ...] = DEFAULT_SOURCE_EXTS,
    exclude_suffixes: tuple[str, ...] = DEFAULT_EXCLUDE_SUFFIXES,
    subpackage_prefix: str = "",
    explicit_files: set[str] | None = None,
) -> dict[str, set[int]]:
    """Collect modified and untracked source line numbers relative to a git ref."""
    explicit = explicit_files or set()
    try:
        verify = subprocess.run(
            ["git", "rev-parse", "--verify", diff_base],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise BlockedError(f"Unable to run git in '{repo_root}': {exc}") from None

    if verify.returncode != 0:
        detail = verify.stderr.strip() or verify.stdout.strip() or diff_base
        raise BlockedError(f"Invalid --diff-base git ref '{diff_base}': {detail}")

    mb_proc = subprocess.run(
        ["git", "merge-base", diff_base, "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    target_ref = (
        mb_proc.stdout.strip()
        if mb_proc.returncode == 0 and mb_proc.stdout.strip()
        else diff_base
    )

    diff_proc = subprocess.run(
        ["git", "diff", "--no-color", "--no-ext-diff", "-U0", target_ref],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if diff_proc.returncode != 0:
        detail = diff_proc.stderr.strip() or f"exit {diff_proc.returncode}"
        raise BlockedError(f"git diff failed against '{target_ref}': {detail}")

    changed_by_file: dict[str, set[int]] = defaultdict(set)
    current_file = ""
    for raw_line in diff_proc.stdout.splitlines():
        if raw_line.startswith("+++ "):
            target = raw_line[4:].strip().strip('"')
            if target == "/dev/null":
                current_file = ""
                continue
            if target.startswith("b/"):
                target = target[2:]
            norm = _normalize_rel_path(target)
            current_file = (
                norm
                if _in_diff_scope(
                    norm,
                    repo_root,
                    source_exts,
                    exclude_suffixes,
                    subpackage_prefix,
                    explicit,
                )
                else ""
            )
            continue
        if not current_file:
            continue
        hunk_match = _HUNK_HEADER_RE.match(raw_line)
        if hunk_match:
            start_line = int(hunk_match.group(1))
            count_raw = hunk_match.group(2)
            line_count = int(count_raw) if count_raw is not None else 1
            if line_count > 0:
                changed_by_file[current_file].update(
                    range(start_line, start_line + line_count)
                )

    untracked_proc = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if untracked_proc.returncode == 0:
        for entry in untracked_proc.stdout.split("\0"):
            norm = _normalize_rel_path(entry) if entry.strip() else ""
            if not _in_diff_scope(
                norm,
                repo_root,
                source_exts,
                exclude_suffixes,
                subpackage_prefix,
                explicit,
            ):
                continue
            line_total = len(
                (repo_root / norm)
                .read_text(encoding="utf-8", errors="replace")
                .splitlines()
            )
            if line_total > 0:
                changed_by_file[norm].update(range(1, line_total + 1))

    return dict(changed_by_file)


def _parse_line_spec(spec: str) -> set[int]:
    lines: set[int] = set()
    for part in spec.split(","):
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start, end = int(start_s), int(end_s)
            if end >= start:
                lines.update(range(start, end + 1))
        else:
            lines.add(int(part))
    return lines


def _collect_explicit_diff_lines(
    repo_root: Path,
    diff_files_raw: Sequence[str],
    dataset: CoverageDataset,
    *,
    source_exts: tuple[str, ...],
    exclude_suffixes: tuple[str, ...],
) -> dict[str, set[int]]:
    """Resolve --diff-files directly without requiring git."""
    changed_by_file: dict[str, set[int]] = defaultdict(set)
    for raw_entry in _split_csv_args(diff_files_raw):
        explicit_lines: set[int] | None = None
        path_part = raw_entry
        spec_match = _LINE_SPEC_RE.match(raw_entry)
        if spec_match and not _WIN_ABS_RE.match(raw_entry):
            path_part = spec_match.group(1)
            explicit_lines = _parse_line_spec(spec_match.group(2))

        norm = _normalize_rel_path(path_part)
        if not norm:
            continue

        disk_path = repo_root / norm
        if disk_path.is_dir():
            candidates: set[str] = {
                sf for sf in dataset.da_by_file if sf.startswith(f"{norm}/")
            }
            for child in disk_path.rglob("*"):
                if child.is_file():
                    candidates.add(child.relative_to(repo_root).as_posix())
            for cand in sorted(candidates):
                if not _in_diff_scope(
                    cand,
                    repo_root,
                    source_exts,
                    exclude_suffixes,
                    "",
                    set(),
                    require_on_disk=False,
                ):
                    continue
                if cand in dataset.da_by_file:
                    changed_by_file[cand].update(dataset.da_by_file[cand].keys())
                elif (repo_root / cand).is_file():
                    total = len(
                        (repo_root / cand)
                        .read_text(encoding="utf-8", errors="replace")
                        .splitlines()
                    )
                    if total > 0:
                        changed_by_file[cand].update(range(1, total + 1))
            continue

        if not _in_diff_scope(
            norm,
            repo_root,
            source_exts,
            exclude_suffixes,
            "",
            set(),
            require_on_disk=False,
        ):
            continue

        if explicit_lines is not None:
            changed_by_file[norm].update(explicit_lines)
        elif norm in dataset.da_by_file:
            changed_by_file[norm].update(dataset.da_by_file[norm].keys())
        elif disk_path.is_file():
            total = len(
                disk_path.read_text(encoding="utf-8", errors="replace").splitlines()
            )
            if total > 0:
                changed_by_file[norm].update(range(1, total + 1))

    return dict(changed_by_file)


def _fallback_executable_lines(file_path: Path, candidate_lines: set[int]) -> list[int]:
    """Conservatively detect executable lines in a source file absent from reports."""
    lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    is_python = file_path.suffix.lower() == ".py"
    detected: list[int] = []
    in_block_comment = False
    in_docstring_delim: str | None = None

    for lineno, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()

        if is_python and in_docstring_delim is not None:
            if in_docstring_delim in stripped:
                in_docstring_delim = None
            continue

        if not is_python and in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue

        if not stripped:
            continue

        if is_python:
            doc_match = _PY_DOCSTRING_PREFIX_RE.match(stripped)
            if doc_match:
                delim = doc_match.group(1)
                if stripped.count(delim) == 1:
                    in_docstring_delim = delim
                continue
            if stripped.startswith("#"):
                continue
        else:
            if stripped.startswith("/*"):
                if "*/" not in stripped[2:]:
                    in_block_comment = True
                continue
            if stripped.startswith("//"):
                continue

        if stripped.startswith(("@", "#[", "#![")):
            continue
        if _PUNCT_ONLY_RE.match(stripped):
            continue
        if _STRUCTURAL_KEYWORD_RE.match(stripped):
            continue
        if stripped.startswith(
            (
                "import ",
                "export ",
                "part ",
                "library ",
                "package ",
                "use ",
                "extern crate ",
            )
        ):
            continue
        if is_python and stripped.startswith("from ") and " import " in stripped:
            continue
        if _RUST_MOD_DECL_RE.match(stripped):
            continue

        if lineno in candidate_lines:
            detected.append(lineno)

    return detected


def _is_file_floor_key(norm_key: str) -> bool:
    suffix = Path(norm_key).suffix.lower()
    return suffix in DEFAULT_SOURCE_EXTS or suffix in _FILE_FLOOR_EXTRA_EXTS


def _normalize_floor_key(raw_key: Any, section: str, source: Path | str) -> str:
    if not isinstance(raw_key, str) or not raw_key.strip():
        raise BlockedError(
            f"Invalid empty or non-string floor key in '{section}' of '{source}'"
        )
    cleaned = raw_key.strip().replace("\\", "/")
    if cleaned.startswith("/") or ".." in cleaned.split("/"):
        raise BlockedError(f"Unsafe floor key '{raw_key}' in '{section}' of '{source}'")
    norm = _normalize_rel_path(cleaned)
    if not norm or norm.startswith(".."):
        raise BlockedError(
            f"Invalid floor key '{raw_key}' in '{section}' of '{source}'"
        )
    return norm


def _extract_floor_pct(raw_val: Any, label: str) -> float:
    if isinstance(raw_val, dict):
        if "floor" not in raw_val:
            raise BlockedError(f"Missing 'floor' key for {label}")
        val = raw_val["floor"]
    else:
        val = raw_val
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise BlockedError(
            f"Invalid floor value for {label}: {val!r} (expected numeric 0..1 or 0..100)"
        )
    return _normalize_threshold(float(val), label)


def _load_package_floors(path: Path) -> CustomFloorSpec:
    """Load adapter/package prefix and web module coverage ratchets from JSON."""
    if not path.is_file():
        raise BlockedError(f"Package floors file not found: {path}")
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BlockedError(
            f"Unable to read package floors file '{path}': {exc}"
        ) from None
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise BlockedError(
            f"Malformed JSON in package floors file '{path}': {exc}"
        ) from None
    if not isinstance(data, dict):
        raise BlockedError(f"Package floors file '{path}' must contain a JSON object")

    prefix_floors: dict[str, float] = {}
    file_floors: dict[str, float] = {}

    for key, val in data.items():
        if key in _FLOOR_METADATA_KEYS:
            continue
        if key == "python":
            if not isinstance(val, dict):
                raise BlockedError(
                    f"'python' section in '{path}' must be a JSON object"
                )
            for py_key, py_val in val.items():
                if py_key in _FLOOR_METADATA_KEYS:
                    continue
                if py_key == "adapters":
                    if not isinstance(py_val, dict):
                        raise BlockedError(
                            f"'python.adapters' in '{path}' must be a JSON object"
                        )
                    for adapter_key, adapter_val in py_val.items():
                        norm = _normalize_floor_key(
                            adapter_key, "python.adapters", path
                        )
                        pct = _extract_floor_pct(adapter_val, f"python.adapters.{norm}")
                        if _is_file_floor_key(norm):
                            file_floors[norm] = pct
                        else:
                            prefix_floors[norm] = pct
                else:
                    raise BlockedError(
                        f"Unsupported key '{py_key}' in 'python' section of '{path}'"
                    )
        elif key == "web_modules":
            if not isinstance(val, dict):
                raise BlockedError(
                    f"'web_modules' section in '{path}' must be a JSON object"
                )
            for mod_key, mod_val in val.items():
                norm = _normalize_floor_key(mod_key, "web_modules", path)
                file_floors[norm] = _extract_floor_pct(mod_val, f"web_modules.{norm}")
        elif key == "packages":
            if not isinstance(val, dict):
                raise BlockedError(
                    f"'packages' section in '{path}' must be a JSON object"
                )
            for pkg_key, pkg_val in val.items():
                norm = _normalize_floor_key(pkg_key, "packages", path)
                pct = _extract_floor_pct(pkg_val, f"packages.{norm}")
                if _is_file_floor_key(norm):
                    file_floors[norm] = pct
                else:
                    prefix_floors[norm] = pct
        else:
            norm = _normalize_floor_key(key, "package_floors", path)
            pct = _extract_floor_pct(val, f"package_floors.{norm}")
            if _is_file_floor_key(norm):
                file_floors[norm] = pct
            else:
                prefix_floors[norm] = pct

    return CustomFloorSpec(prefix_floors=prefix_floors, file_floors=file_floors)


def _coerce_custom_floors(
    custom_floors: CustomFloorSpec | Mapping[str, float] | None,
) -> CustomFloorSpec:
    if custom_floors is None:
        return CustomFloorSpec()
    if isinstance(custom_floors, CustomFloorSpec):
        return custom_floors
    prefix_floors: dict[str, float] = {}
    file_floors: dict[str, float] = {}
    for raw_key, raw_val in custom_floors.items():
        norm = _normalize_floor_key(raw_key, "custom_floors", "<in-memory>")
        pct = _extract_floor_pct(raw_val, f"custom_floors.{norm}")
        if _is_file_floor_key(norm):
            file_floors[norm] = pct
        else:
            prefix_floors[norm] = pct
    return CustomFloorSpec(prefix_floors=prefix_floors, file_floors=file_floors)


def evaluate_coverage(
    dataset: CoverageDataset,
    repo_root: Path,
    *,
    min_coverage_pct: float = 0.0,
    coverage_checked: bool = True,
    min_package_coverage_pct: float = 0.0,
    excluded_package_floors: set[str] | None = None,
    package_groups: tuple[str, ...] = DEFAULT_PACKAGE_GROUPS,
    changed_by_file: dict[str, set[int]] | None = None,
    min_diff_coverage_pct: float | None = None,
    custom_floors: CustomFloorSpec | Mapping[str, float] | None = None,
) -> EvaluationResult:
    """Evaluate workspace, per-package, custom ratchet, and hunk-level diff coverage floors."""
    excluded = excluded_package_floors or set()
    floor_spec = _coerce_custom_floors(custom_floors)
    module_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    file_stats: dict[str, tuple[int, int]] = {}
    file_bucket_by_sf: dict[str, str] = {}
    file_results: list[dict[str, Any]] = []
    total_lh = 0
    total_lf = 0

    all_files = sorted(
        set(dataset.da_by_file.keys()) | set(dataset.fallback_by_file.keys())
    )
    for canonical_sf in all_files:
        if (
            canonical_sf in dataset.da_by_file
            and canonical_sf in dataset.fallback_by_file
        ):
            hits_by_line = dataset.da_by_file[canonical_sf]
            da_lf = len(hits_by_line)
            da_lh = sum(1 for hits in hits_by_line.values() if hits > 0)
            summary_lh, summary_lf = dataset.fallback_by_file[canonical_sf]
            lf = max(da_lf, summary_lf)
            lh = min(lf, max(da_lh, summary_lh))
        elif canonical_sf in dataset.da_by_file:
            hits_by_line = dataset.da_by_file[canonical_sf]
            lf = len(hits_by_line)
            lh = sum(1 for hits in hits_by_line.values() if hits > 0)
        else:
            lh, lf = dataset.fallback_by_file[canonical_sf]

        bucket = _bucket_for_path(canonical_sf, package_groups)
        module_stats[bucket][0] += lh
        module_stats[bucket][1] += lf
        file_stats[canonical_sf] = (lh, lf)
        file_bucket_by_sf[canonical_sf] = bucket
        total_lh += lh
        total_lf += lf
        file_pct = (lh / lf * 100.0) if lf > 0 else 0.0
        file_results.append(
            {
                "file": canonical_sf,
                "package": bucket,
                "covered": lh,
                "total": lf,
                "coverage_pct": round(file_pct, 2),
            }
        )

    coverage_pct = (total_lh / total_lf * 100.0) if total_lf > 0 else 0.0
    failures: list[str] = []

    if min_coverage_pct > 0.0:
        if total_lf == 0:
            failures.append(
                "Coverage report contains 0 measurable non-generated lines."
            )
        elif coverage_pct + _FLOAT_EPS < min_coverage_pct:
            failures.append(
                f"Workspace line coverage {coverage_pct:.1f}% is below floor "
                f"{min_coverage_pct:.1f}%."
            )

    custom_floor_results: list[dict[str, Any]] = []
    custom_floor_failures: list[str] = []
    custom_governed_files: set[str] = set()

    for prefix, floor_pct in sorted(floor_spec.prefix_floors.items()):
        matched = [
            sf for sf in all_files if sf == prefix or sf.startswith(f"{prefix}/")
        ]
        if not matched and "/" not in prefix:
            matched = [
                sf
                for sf in all_files
                if file_bucket_by_sf[sf] == prefix
                or file_bucket_by_sf[sf].rsplit("/", 1)[-1] == prefix
            ]
        agg_lh = sum(file_stats[sf][0] for sf in matched)
        agg_lf = sum(file_stats[sf][1] for sf in matched)
        if agg_lf == 0:
            custom_floor_results.append(
                {
                    "target": prefix,
                    "kind": "prefix",
                    "matched_files": matched,
                    "covered": 0,
                    "total": 0,
                    "coverage_pct": None,
                    "floor_pct": round(floor_pct, 2),
                    "measured": False,
                    "passed": True,
                }
            )
            continue
        custom_governed_files.update(matched)
        agg_pct = agg_lh / agg_lf * 100.0
        passed = not (floor_pct > 0.0 and agg_pct + _FLOAT_EPS < floor_pct)
        if not passed:
            custom_floor_failures.append(
                f"Adapter/package floor '{prefix}' coverage {agg_pct:.1f}% is below "
                f"floor {floor_pct:.1f}%."
            )
        custom_floor_results.append(
            {
                "target": prefix,
                "kind": "prefix",
                "matched_files": matched,
                "covered": agg_lh,
                "total": agg_lf,
                "coverage_pct": round(agg_pct, 2),
                "floor_pct": round(floor_pct, 2),
                "measured": True,
                "passed": passed,
            }
        )

    for file_key, floor_pct in sorted(floor_spec.file_floors.items()):
        matched_sf: str | None = None
        if file_key in file_stats:
            matched_sf = file_key
        else:
            suffix_matches = [sf for sf in all_files if sf.endswith(f"/{file_key}")]
            if len(suffix_matches) == 1:
                matched_sf = suffix_matches[0]
        if matched_sf is None or file_stats[matched_sf][1] == 0:
            custom_floor_results.append(
                {
                    "target": file_key,
                    "kind": "file",
                    "matched_files": [matched_sf] if matched_sf is not None else [],
                    "covered": 0,
                    "total": 0,
                    "coverage_pct": None,
                    "floor_pct": round(floor_pct, 2),
                    "measured": False,
                    "passed": True,
                }
            )
            continue
        custom_governed_files.add(matched_sf)
        flh, flf = file_stats[matched_sf]
        fpct = flh / flf * 100.0
        passed = not (floor_pct > 0.0 and fpct + _FLOAT_EPS < floor_pct)
        if not passed:
            label = (
                f"'{file_key}'"
                if file_key == matched_sf
                else f"'{file_key}' ({matched_sf})"
            )
            custom_floor_failures.append(
                f"Module floor {label} coverage {fpct:.1f}% is below "
                f"floor {floor_pct:.1f}%."
            )
        custom_floor_results.append(
            {
                "target": file_key,
                "kind": "file",
                "matched_files": [matched_sf],
                "covered": flh,
                "total": flf,
                "coverage_pct": round(fpct, 2),
                "floor_pct": round(floor_pct, 2),
                "measured": True,
                "passed": passed,
            }
        )

    unmatched_module_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for canonical_sf, (lh, lf) in file_stats.items():
        if canonical_sf not in custom_governed_files:
            bucket = file_bucket_by_sf[canonical_sf]
            unmatched_module_stats[bucket][0] += lh
            unmatched_module_stats[bucket][1] += lf

    package_results: list[dict[str, Any]] = []
    for bucket in sorted(module_stats.keys()):
        if bucket == "root":
            continue
        lh, lf = module_stats[bucket]
        un_lh, un_lf = unmatched_module_stats[bucket]
        short_name = bucket.rsplit("/", 1)[-1]
        is_excluded = bucket in excluded or short_name in excluded
        pkg_pct = (lh / lf * 100.0) if lf > 0 else 0.0
        enforced_pct: float | None = (
            round(un_lh / un_lf * 100.0, 2) if un_lf > 0 else None
        )
        pkg_passed = True
        if min_package_coverage_pct > 0.0 and not is_excluded and un_lf > 0:
            check_pct = un_lh / un_lf * 100.0
            if check_pct + _FLOAT_EPS < min_package_coverage_pct:
                pkg_passed = False
                failures.append(
                    f"Package {bucket} coverage {check_pct:.1f}% is below floor "
                    f"{min_package_coverage_pct:.1f}%."
                )
        package_results.append(
            {
                "package": bucket,
                "name": short_name,
                "covered": lh,
                "total": lf,
                "coverage_pct": round(pkg_pct, 2),
                "enforced_coverage_pct": enforced_pct,
                "excluded_from_floor": is_excluded,
                "passed": pkg_passed,
            }
        )

    failures.extend(custom_floor_failures)

    diff_files: list[dict[str, Any]] = []
    diff_lh = 0
    diff_lf = 0
    diff_coverage_pct: float | None = None

    if min_diff_coverage_pct is not None:
        changes = changed_by_file or {}
        for rel_path in sorted(changes.keys()):
            changed_lines = changes[rel_path]
            if rel_path in dataset.da_by_file:
                da_map = dataset.da_by_file[rel_path]
                measurable = sorted(ln for ln in changed_lines if ln in da_map)
                hit_count = sum(1 for ln in measurable if da_map[ln] > 0)
                missed = [ln for ln in measurable if da_map[ln] <= 0]
                is_fallback = False
            else:
                file_path = repo_root / rel_path
                missed = (
                    _fallback_executable_lines(file_path, changed_lines)
                    if file_path.is_file()
                    else []
                )
                measurable = missed
                hit_count = 0
                is_fallback = True

            if not measurable:
                continue

            file_lf = len(measurable)
            file_pct = hit_count / file_lf * 100.0
            diff_files.append(
                {
                    "file": rel_path,
                    "covered": hit_count,
                    "total": file_lf,
                    "uncovered": len(missed),
                    "coverage_pct": round(file_pct, 2),
                    "missed_lines": missed,
                    "fallback": is_fallback,
                }
            )
            diff_lh += hit_count
            diff_lf += file_lf

        diff_coverage_pct = (diff_lh / diff_lf * 100.0) if diff_lf > 0 else 100.0
        if diff_lf > 0 and diff_coverage_pct + _FLOAT_EPS < min_diff_coverage_pct:
            failures.append(
                f"Diff line coverage {diff_coverage_pct:.1f}% is below floor "
                f"{min_diff_coverage_pct:.1f}%."
            )

    status = "FAIL" if failures else "PASS"
    return EvaluationResult(
        status=status,
        coverage_pct=coverage_pct,
        min_coverage_pct=min_coverage_pct,
        coverage_checked=coverage_checked,
        total_covered=total_lh,
        total_lines=total_lf,
        diff_coverage_pct=diff_coverage_pct,
        min_diff_coverage_pct=min_diff_coverage_pct,
        diff_covered=diff_lh,
        diff_lines=diff_lf,
        package_results=package_results,
        file_results=file_results,
        diff_files=diff_files,
        failures=failures,
        custom_floor_results=custom_floor_results,
    )


def format_output(
    result: EvaluationResult,
    *,
    verbose: bool = False,
    as_json: bool = False,
) -> str:
    """Format an EvaluationResult according to the Token-Budget CLI contract."""
    if as_json:
        return json.dumps(result.to_json_dict(), indent=2)

    if result.status == "BLOCKED":
        reason = "; ".join(result.failures) or "Coverage evaluation blocked"
        return f"BLOCKED: {reason}"

    parts: list[str] = []
    if result.coverage_checked or result.diff_coverage_pct is None:
        parts.append(
            f"coverage={result.coverage_pct:.1f}% (floor>={result.min_coverage_pct:.1f}%)"
        )
    if (
        result.diff_coverage_pct is not None
        and result.min_diff_coverage_pct is not None
    ):
        parts.append(
            f"diff={result.diff_coverage_pct:.1f}% "
            f"(floor>={result.min_diff_coverage_pct:.1f}%, "
            f"files={len(result.diff_files)}, lines={result.diff_lines})"
        )
    summary_line = f"{result.status}: " + ", ".join(parts)

    if result.status == "PASS" and not verbose:
        return summary_line

    lines = [summary_line]
    if result.failures:
        lines.append("Failures:")
        for failure in result.failures:
            lines.append(f"  - {failure}")

    if result.package_results:
        lines.append("Package Coverage:")
        for pkg in result.package_results:
            note = ""
            if pkg["excluded_from_floor"]:
                note = " [excluded from floor]"
            elif not pkg["passed"]:
                note = " [BELOW FLOOR]"
            lines.append(
                f"  {pkg['package']:<32} {pkg['covered']:>5}/{pkg['total']:<5} "
                f"({pkg['coverage_pct']:5.1f}%){note}"
            )

    if result.custom_floor_results:
        lines.append("Custom Floor Ratchets:")
        for item in result.custom_floor_results:
            if not item["measured"]:
                lines.append(
                    f"  {item['target']:<40}     0/0     (  n/a) "
                    f"[floor>={item['floor_pct']:.1f}%, unmeasured]"
                )
            else:
                note = "" if item["passed"] else " [BELOW FLOOR]"
                lines.append(
                    f"  {item['target']:<40} {item['covered']:>5}/{item['total']:<5} "
                    f"({item['coverage_pct']:5.1f}%, floor>={item['floor_pct']:.1f}%){note}"
                )

    if verbose and result.file_results:
        lines.append("File Coverage:")
        for item in result.file_results:
            lines.append(
                f"  {item['file']:<40} {item['covered']:>5}/{item['total']:<5} "
                f"({item['coverage_pct']:5.1f}%)"
            )

    if result.diff_files:
        lines.append("Diff Coverage:")
        for item in result.diff_files:
            missed = item["missed_lines"]
            missed_note = ""
            if missed:
                preview = ", ".join(f"L{ln}" for ln in missed[:12])
                if len(missed) > 12:
                    preview += f", ... (+{len(missed) - 12} more)"
                missed_note = f" [missed: {preview}]"
            lines.append(
                f"  {item['file']:<40} {item['covered']:>5}/{item['total']:<5} "
                f"({item['coverage_pct']:5.1f}%, uncovered={item['uncovered']}){missed_note}"
            )

    return "\n".join(lines)


def _build_parser() -> _BlockedArgumentParser:
    parser = _BlockedArgumentParser(
        description=(
            "Verify LCOV, Cobertura XML, and JaCoCo XML line and hunk-level "
            "diff coverage against dual-floor thresholds."
        )
    )
    parser.add_argument(
        "report_files",
        nargs="+",
        type=Path,
        help="One or more coverage report paths (merged via max hit count).",
    )
    parser.add_argument(
        "--format",
        choices=("auto", "lcov", "cobertura", "jacoco"),
        default="auto",
        help="Coverage report format (default: auto).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root directory (default: .).",
    )
    parser.add_argument(
        "--source-root",
        action="append",
        default=[],
        help="Repeatable source root prefix for resolving relative XML paths.",
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=None,
        help="Workspace line coverage floor in 0..1 or 0..100 (default: 0.0).",
    )
    parser.add_argument(
        "--min-package-coverage",
        type=float,
        default=0.0,
        help="Per-package line coverage floor in 0..1 or 0..100 (default: 0.0).",
    )
    parser.add_argument(
        "--exclude-package-floor",
        action="append",
        default=[],
        help="Repeatable package bucket or leaf name exempt from --min-package-coverage.",
    )
    parser.add_argument(
        "--package-group",
        action="append",
        default=[],
        help="Repeatable top-level package group directory name.",
    )
    parser.add_argument(
        "--package-floors",
        type=Path,
        default=None,
        help="Optional JSON file defining adapter prefix and module coverage floor ratchets.",
    )
    parser.add_argument(
        "--diff-base",
        type=str,
        default="",
        help="Git base ref for unified zero-context hunk diff (e.g. HEAD or main).",
    )
    parser.add_argument(
        "--diff-files",
        action="append",
        default=[],
        help="Repeatable repo-relative file or directory path for diff coverage.",
    )
    parser.add_argument(
        "--min-diff-coverage",
        type=float,
        default=None,
        help="Hunk-level diff coverage floor in 0..1 or 0..100.",
    )
    parser.add_argument(
        "--source-ext",
        action="append",
        default=[],
        help="Repeatable source file extension filter for diff coverage.",
    )
    parser.add_argument(
        "--exclude-suffix",
        action="append",
        default=[],
        help="Repeatable generated-code filename suffix to exclude.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Expand package, file, and diff coverage tables even on PASS.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit machine-readable JSON output.",
    )
    return parser


def _parse_report_file(
    report_path: Path,
    fmt: str,
    repo_root: Path,
    *,
    source_roots: tuple[str, ...],
    package_groups: tuple[str, ...],
    exclude_suffixes: tuple[str, ...],
) -> tuple[CoverageDataset, str]:
    if not report_path.is_file():
        raise BlockedError(f"Coverage report not found: {report_path}")
    try:
        text = report_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise BlockedError(
            f"Unable to read coverage report '{report_path}': {exc}"
        ) from None

    source_name = str(report_path)
    resolved_fmt = detect_format(text, source_name) if fmt == "auto" else fmt
    subpkg = _infer_subpackage_prefix(report_path, repo_root, package_groups)

    if resolved_fmt == "lcov":
        ds = parse_lcov(
            text,
            repo_root,
            subpackage_prefix=subpkg,
            source_roots=source_roots,
            package_groups=package_groups,
            exclude_suffixes=exclude_suffixes,
            source_name=source_name,
        )
    elif resolved_fmt == "cobertura":
        ds = parse_cobertura_xml(
            text,
            repo_root,
            subpackage_prefix=subpkg,
            source_roots=source_roots,
            package_groups=package_groups,
            exclude_suffixes=exclude_suffixes,
            source_name=source_name,
        )
    else:
        ds = parse_jacoco_xml(
            text,
            repo_root,
            subpackage_prefix=subpkg,
            source_roots=source_roots,
            package_groups=package_groups,
            exclude_suffixes=exclude_suffixes,
            source_name=source_name,
        )
    return ds, subpkg


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point returning exit code 0 (PASS), 1 (FAIL), or 2 (BLOCKED)."""
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    as_json_hint = "--json" in raw_argv
    parser = _build_parser()

    try:
        args = parser.parse_args(raw_argv)
        as_json = bool(args.as_json)

        min_cov_pct = (
            _normalize_threshold(args.min_coverage, "--min-coverage")
            if args.min_coverage is not None
            else 0.0
        )
        min_pkg_pct = _normalize_threshold(
            args.min_package_coverage, "--min-package-coverage"
        )
        min_diff_pct = (
            _normalize_threshold(args.min_diff_coverage, "--min-diff-coverage")
            if args.min_diff_coverage is not None
            else None
        )

        diff_base = args.diff_base.strip()
        diff_files_raw = _split_csv_args(args.diff_files)
        if min_diff_pct is not None and not diff_base and not diff_files_raw:
            raise BlockedError(
                "--diff-base or --diff-files is required when --min-diff-coverage is set"
            )

        repo_root: Path = args.repo_root
        source_roots = tuple(_split_csv_args(args.source_root))
        package_groups = _normalize_package_groups(args.package_group)
        exclude_suffixes = _normalize_exclude_suffixes(args.exclude_suffix)
        source_exts = _normalize_source_exts(args.source_ext)
        excluded_floors = {
            _normalize_rel_path(e)
            for e in _split_csv_args(args.exclude_package_floor)
            if _normalize_rel_path(e)
        }
        custom_floors: CustomFloorSpec | None = None
        if args.package_floors is not None:
            floors_path: Path = args.package_floors
            if not floors_path.is_file() and not floors_path.is_absolute():
                repo_candidate = repo_root / floors_path
                if repo_candidate.is_file():
                    floors_path = repo_candidate
            custom_floors = _load_package_floors(floors_path)

        merged = CoverageDataset()
        inferred_subpkgs: set[str] = set()
        for report_path in args.report_files:
            ds, subpkg = _parse_report_file(
                report_path,
                args.format,
                repo_root,
                source_roots=source_roots,
                package_groups=package_groups,
                exclude_suffixes=exclude_suffixes,
            )
            merged.merge(ds)
            if subpkg:
                inferred_subpkgs.add(subpkg)

        shared_subpkg = (
            next(iter(inferred_subpkgs))
            if len(inferred_subpkgs) == 1 and len(args.report_files) == 1
            else ""
        )

        changed_by_file: dict[str, set[int]] | None = None
        if min_diff_pct is not None:
            if diff_base:
                explicit_set = {
                    _normalize_rel_path(p)
                    for p in diff_files_raw
                    if _normalize_rel_path(p)
                }
                changed_by_file = collect_git_diff_lines(
                    repo_root,
                    diff_base,
                    source_exts=source_exts,
                    exclude_suffixes=exclude_suffixes,
                    subpackage_prefix=shared_subpkg,
                    explicit_files=explicit_set,
                )
            else:
                changed_by_file = _collect_explicit_diff_lines(
                    repo_root,
                    diff_files_raw,
                    merged,
                    source_exts=source_exts,
                    exclude_suffixes=exclude_suffixes,
                )

        coverage_checked = args.min_coverage is not None and min_cov_pct > 0.0
        result = evaluate_coverage(
            merged,
            repo_root,
            min_coverage_pct=min_cov_pct,
            coverage_checked=coverage_checked,
            min_package_coverage_pct=min_pkg_pct,
            excluded_package_floors=excluded_floors,
            package_groups=package_groups,
            changed_by_file=changed_by_file,
            min_diff_coverage_pct=min_diff_pct,
            custom_floors=custom_floors,
        )
        print(format_output(result, verbose=bool(args.verbose), as_json=as_json))
        return 0 if result.status == "PASS" else 1

    except BlockedError as exc:
        blocked = EvaluationResult(
            status="BLOCKED",
            coverage_pct=0.0,
            min_coverage_pct=0.0,
            coverage_checked=False,
            total_covered=0,
            total_lines=0,
            diff_coverage_pct=None,
            min_diff_coverage_pct=None,
            diff_covered=0,
            diff_lines=0,
            package_results=[],
            file_results=[],
            diff_files=[],
            failures=[str(exc)],
        )
        print(format_output(blocked, as_json=as_json_hint))
        return 2


if __name__ == "__main__":
    sys.exit(main())
