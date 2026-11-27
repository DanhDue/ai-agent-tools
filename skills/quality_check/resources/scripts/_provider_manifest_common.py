"""Shared additive v1 quality manifest validation and compact CLI output helpers.

Used by validate_quality_contract.py and all 6 stack provider validators
(flutter, rust, web, python, android, ios) to enforce uniform additive v1
contract validation and compact single-line PASS CLI output with Python 3
stdlib only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

ALLOWED_PROFILES: tuple[str, ...] = ("pr", "epic", "scheduled", "release")
POOL_MOUNT_MODES: tuple[str, ...] = ("symlink", "cow_copy")
TRIAGE_SURFACE_CATEGORIES: tuple[str, ...] = (
    "signature",
    "api_wire",
    "persistence",
    "concurrency",
    "test_weakening",
)
UNIFIED_CAPABILITIES: tuple[str, ...] = (
    "anti_stub",
    "security",
    "security_deps",
    "pr_diff_audit",
    "workspace_audit",
    "pr_impact",
    "workspace_impact",
    "license",
)
EXTENSION_PATTERN = re.compile(r"^\.[a-z0-9]+$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")

TASK_TIER_B_LIST_KEYS: tuple[str, ...] = (
    "format_prefixes",
    "lint_prefixes",
    "typecheck_prefixes",
    "boundary_prefixes",
    "boundary_triggers",
)
TASK_TIER_B_ALLOWED_KEYS: frozenset[str] = frozenset(
    (*TASK_TIER_B_LIST_KEYS, "require_all_allowed_files_in_format")
)
COVERAGE_PATH_KEYS: tuple[str, ...] = ("lcov_path", "report_path", "profdata_path")


def _finding(code: str, message: str, **extra: Any) -> dict[str, Any]:
    finding: dict[str, Any] = {"code": code, "message": message}
    finding.update(extra)
    return finding


def is_safe_relative_path(raw: Any) -> bool:
    """Return True if raw is a non-empty relative path without '..' traversal."""
    if not isinstance(raw, str):
        return False
    stripped = raw.strip()
    if not stripped or "\x00" in stripped:
        return False
    if stripped.startswith(("/", "\\")) or _WINDOWS_DRIVE_RE.match(stripped):
        return False
    if Path(stripped).is_absolute() or PurePosixPath(stripped).is_absolute():
        return False
    segments = re.split(r"[/\\]+", stripped)
    return ".." not in segments


def validate_pool_mounts(pool_mounts: Any) -> list[dict[str, Any]]:
    """Validate optional top-level 'pool_mounts' array in check_quality.json."""
    findings: list[dict[str, Any]] = []
    if not isinstance(pool_mounts, list):
        findings.append(
            _finding(
                "invalid_pool_mounts_format",
                "Optional 'pool_mounts' must be an array of {path, mode} objects",
                field="pool_mounts",
            )
        )
        return findings

    allowed_entry_keys = {"path", "mode"}
    for idx, entry in enumerate(pool_mounts):
        if not isinstance(entry, dict):
            findings.append(
                _finding(
                    "invalid_pool_mounts_format",
                    f"pool_mounts[{idx}] must be an object with 'path' and 'mode'",
                    field=f"pool_mounts[{idx}]",
                )
            )
            continue

        for key in sorted(entry.keys()):
            if key not in allowed_entry_keys:
                findings.append(
                    _finding(
                        "unknown_field",
                        f"Unknown field '{key}' in pool_mounts[{idx}]",
                        field=f"pool_mounts[{idx}].{key}",
                    )
                )

        mount_path = entry.get("path")
        if not is_safe_relative_path(mount_path):
            findings.append(
                _finding(
                    "invalid_pool_mount_path",
                    f"pool_mounts[{idx}].path '{mount_path}' must be a non-empty relative path without '..' traversal",
                    field=f"pool_mounts[{idx}].path",
                )
            )

        mount_mode = entry.get("mode")
        if not isinstance(mount_mode, str) or mount_mode not in POOL_MOUNT_MODES:
            findings.append(
                _finding(
                    "invalid_pool_mount_mode",
                    f"pool_mounts[{idx}].mode '{mount_mode}' must be one of {list(POOL_MOUNT_MODES)}",
                    field=f"pool_mounts[{idx}].mode",
                )
            )

    return findings


def validate_dual_floor_coverage(
    coverage_val: Any,
    *,
    capability: str = "coverage",
) -> list[dict[str, Any]]:
    """Validate optional additive dual-floor fields inside capabilities.coverage."""
    if not isinstance(coverage_val, dict):
        return []

    findings: list[dict[str, Any]] = []

    for fraction_key in ("min_package_coverage", "min_diff_coverage"):
        if fraction_key in coverage_val:
            val = coverage_val[fraction_key]
            if (
                isinstance(val, bool)
                or not isinstance(val, (int, float))
                or val < 0
                or val > 1.0
            ):
                findings.append(
                    _finding(
                        "invalid_coverage_threshold",
                        f"Coverage '{fraction_key}' must be a number between 0.0 and 1.0",
                        capability=capability,
                        field=f"coverage.{fraction_key}",
                    )
                )

    if "exclude_package_floor" in coverage_val:
        excl = coverage_val["exclude_package_floor"]
        if not isinstance(excl, list) or not all(
            isinstance(item, str) and bool(item.strip()) for item in excl
        ):
            findings.append(
                _finding(
                    "invalid_coverage_config",
                    "Coverage 'exclude_package_floor' must be an array of non-empty strings",
                    capability=capability,
                    field="coverage.exclude_package_floor",
                )
            )

    for str_key in ("diff_base", *COVERAGE_PATH_KEYS):
        if str_key in coverage_val:
            sval = coverage_val[str_key]
            if not isinstance(sval, str) or not sval.strip():
                findings.append(
                    _finding(
                        "invalid_coverage_config",
                        f"Coverage '{str_key}' must be a non-empty string",
                        capability=capability,
                        field=f"coverage.{str_key}",
                    )
                )

    return findings


def validate_additive_provider_fields(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate optional additive v1 top-level keys on any stack provider manifest."""
    findings: list[dict[str, Any]] = []

    if "standards_catalog" in config:
        catalog_path = config["standards_catalog"]
        if not is_safe_relative_path(catalog_path):
            findings.append(
                _finding(
                    "invalid_standards_catalog_path",
                    f"Optional 'standards_catalog' path '{catalog_path}' must be a non-empty relative path without '..' traversal",
                    field="standards_catalog",
                )
            )

    if "extensions" in config:
        exts = config["extensions"]
        if (
            not isinstance(exts, list)
            or len(exts) == 0
            or not all(
                isinstance(ext, str) and bool(EXTENSION_PATTERN.match(ext))
                for ext in exts
            )
        ):
            findings.append(
                _finding(
                    "invalid_extensions",
                    "Optional 'extensions' must be a non-empty array of lowercase dot-prefixed extensions matching ^\\.[a-z0-9]+$",
                    field="extensions",
                )
            )

    if "task_tier_b" in config:
        ttb = config["task_tier_b"]
        if not isinstance(ttb, dict):
            findings.append(
                _finding(
                    "invalid_task_tier_b",
                    "Optional 'task_tier_b' must be an object",
                    field="task_tier_b",
                )
            )
        else:
            for key in sorted(ttb.keys()):
                if key not in TASK_TIER_B_ALLOWED_KEYS:
                    findings.append(
                        _finding(
                            "invalid_task_tier_b",
                            f"Unknown field '{key}' in 'task_tier_b'",
                            field=f"task_tier_b.{key}",
                        )
                    )
            for list_key in TASK_TIER_B_LIST_KEYS:
                if list_key in ttb:
                    val = ttb[list_key]
                    if not isinstance(val, list) or not all(
                        isinstance(item, str) and bool(item.strip()) for item in val
                    ):
                        findings.append(
                            _finding(
                                "invalid_task_tier_b",
                                f"task_tier_b.{list_key} must be an array of non-empty strings",
                                field=f"task_tier_b.{list_key}",
                            )
                        )
            if "require_all_allowed_files_in_format" in ttb and not isinstance(
                ttb["require_all_allowed_files_in_format"], bool
            ):
                findings.append(
                    _finding(
                        "invalid_task_tier_b",
                        "task_tier_b.require_all_allowed_files_in_format must be a boolean",
                        field="task_tier_b.require_all_allowed_files_in_format",
                    )
                )

    if "triage_surfaces" in config:
        surfaces = config["triage_surfaces"]
        if not isinstance(surfaces, dict):
            findings.append(
                _finding(
                    "invalid_triage_surfaces_format",
                    "Optional 'triage_surfaces' must be an object mapping category names to regex string arrays",
                    field="triage_surfaces",
                )
            )
        else:
            for category in sorted(surfaces.keys()):
                if category not in TRIAGE_SURFACE_CATEGORIES:
                    findings.append(
                        _finding(
                            "unknown_triage_surface_category",
                            f"Unknown triage_surfaces category '{category}'; allowed: {', '.join(TRIAGE_SURFACE_CATEGORIES)}",
                            field=f"triage_surfaces.{category}",
                        )
                    )
                    continue
                patterns = surfaces[category]
                if not isinstance(patterns, list):
                    findings.append(
                        _finding(
                            "invalid_triage_surfaces_format",
                            f"triage_surfaces.{category} must be an array of regex strings",
                            field=f"triage_surfaces.{category}",
                        )
                    )
                    continue
                for idx, pattern in enumerate(patterns):
                    if not isinstance(pattern, str) or not pattern:
                        findings.append(
                            _finding(
                                "invalid_triage_surface_regex",
                                f"triage_surfaces.{category}[{idx}] must be a non-empty regex string",
                                field=f"triage_surfaces.{category}[{idx}]",
                            )
                        )
                        continue
                    try:
                        re.compile(pattern)
                    except re.error as err:
                        findings.append(
                            _finding(
                                "invalid_triage_surface_regex",
                                f"Invalid regex in triage_surfaces.{category}[{idx}] ('{pattern}'): {err}",
                                field=f"triage_surfaces.{category}[{idx}]",
                            )
                        )

    return findings


def format_validator_cli_output(
    label: str,
    profile: str | None,
    result: dict[str, Any],
    *,
    verbose: bool = False,
    as_json: bool = False,
    item_count: int | None = None,
    item_label: str = "caps",
    details: list[str] | None = None,
) -> str:
    """Format validator CLI stdout according to the compact 1-line PASS contract."""
    if as_json:
        return json.dumps(result, indent=2)

    status = str(result.get("status", "BLOCKED"))
    raw_findings = result.get("findings")
    findings: list[dict[str, Any]] = (
        raw_findings if isinstance(raw_findings, list) else []
    )

    meta_parts: list[str] = []
    if profile:
        meta_parts.append(f"profile={profile}")
    if item_count is not None:
        meta_parts.append(f"{item_label}={item_count}")
    if status != "PASS":
        meta_parts.append(f"findings={len(findings)}")
    meta_suffix = f" ({', '.join(meta_parts)})" if meta_parts else ""
    summary = f"{status}: {label}{meta_suffix}"

    if status == "PASS" and not verbose:
        return summary

    lines = [summary]
    if status != "PASS":
        for finding in findings:
            code = finding.get("code", "unknown")
            message = finding.get("message", "")
            ctx_parts = [
                f"{key}={finding[key]}"
                for key in ("provider_id", "capability", "field", "profile", "location")
                if finding.get(key)
            ]
            ctx = f" [{', '.join(ctx_parts)}]" if ctx_parts else ""
            lines.append(f"  - {code}: {message}{ctx}")
    elif details:
        for item in details:
            lines.append(f"  - {item}")
    else:
        lines.append("  findings: 0")

    return "\n".join(lines)
