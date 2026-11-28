#!/usr/bin/env python3
"""Fifth Open-Closed Contract (QualityPlanResolver) and file-scoped CLI.

Reads `.agents/quality/check_quality.json`, active `*-quality.json` manifests,
`.agents/quality/coverage_floors.json`, and `_stack_lifecycle_registry.py` defaults
to emit 5-10 compact, file-scoped lines detailing canonical/forbidden test roots,
dual Web V8 LCOV + Playwright Tier C2 rules, matched coverage ratchet floors,
referencing `?v=` cache-bust templates, and `$D3NEXUS_KIT/skills`-interpolated
scoped TIER-B commands.

Python 3 standard library + `_stack_lifecycle_registry` only; zero imports from
`check_task_contract` or `manage_worker_pool`, zero subprocess calls.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import _stack_lifecycle_registry as registry

DEFAULT_CANONICAL_TEST_GLOBS: dict[str, tuple[str, ...]] = {
    "python": ("tests/unit/**/test_*.py", "tests/integration/test_*.py"),
    "web": ("tests/js/*.test.mjs", "tests/e2e/"),
    "flutter": ("test/", "test/integration/"),
    "android": ("src/test/",),
    "ios": ("Tests/",),
    "rust": ("tests/", "inline #[cfg(test)]"),
}

DEFAULT_LCOV_UNIT_TEST_GLOBS: tuple[str, ...] = (
    "tests/js/*.test.mjs",
    "*.test.mjs",
    "*.test.js",
    "*.test.ts",
)

DEFAULT_CACHE_BUST_EXTENSIONS: tuple[str, ...] = (".js", ".css")

_TEMPLATE_EXTENSIONS: tuple[str, ...] = (".html", ".astro", ".jinja", ".jinja2")

_IGNORED_WALK_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "node_modules",
        "build",
        "dist",
        ".worktrees",
        ".venv",
        "venv",
        "target",
        ".astro",
        ".dart_tool",
        ".gradle",
        "Pods",
        "coverage",
        "__pycache__",
    }
)

_PYTHON_STATIC_TOOLS: frozenset[str] = frozenset({"ruff", "mypy", "pyright", "ty"})
_PYTHON_FULL_REPO_TARGETS: frozenset[str] = frozenset({".", "src", "tests"})
_DART_FULL_REPO_TARGETS: frozenset[str] = frozenset({".", "lib", "test"})

_PYTHON_VALUE_FLAGS: frozenset[str] = registry._VALUE_TAKING_CLI_FLAGS | frozenset(
    {
        "--pyproject-toml",
        "--fixable",
        "--unfixable",
        "--python-executable",
        "--python-platform",
        "--package",
        "--module",
        "-m",
        "--follow-imports",
        "--custom-typeshed-dir",
        "--shadow-file",
        "--junit-xml",
        "--html-report",
        "--xml-report",
        "--cobertura-xml-report",
        "--txt-report",
        "--any-exprs-report",
        "--linecount-report",
        "--linecoverage-report",
        "--lineprecision-report",
        "--venvpath",
        "--typeshedpath",
        "--level",
    }
)

_RESERVED_FLOOR_KEYS: frozenset[str] = frozenset(
    {
        "python",
        "web_modules",
        "packages",
        "schema_version",
        "version",
        "description",
        "notes",
    }
)

_PATH_TRAIL_ANNOTATION_RE = re.compile(
    r"(?:\s*(?:\(new\)|\(existing\)|\(modified\)|\(deleted\)"
    r"|\(L\d+(?:\s*[-–:]\s*L?\d+)?\)"
    r"|::\s*`?[A-Za-z_][\w.]*`?"
    r"|\s+[—–-]\s+.*)"
    r"|:L?\d+(?:[-–]L?\d+)?)$"
)

_STATIC_CAP_GROUPS: tuple[tuple[str, ...], ...] = (
    ("format",),
    ("lint", "analyze", "clippy"),
    ("type_check",),
)
_BOUNDARY_CAP_KEYS: tuple[str, ...] = ("boundaries", "architecture", "bcv")


class QualityPlanError(RuntimeError):
    """Raised when quality manifests or CLI arguments are malformed."""


@dataclass(frozen=True)
class StackQualityPlan:
    """Resolved quality contract for one active stack."""

    stack_id: str
    matched_files: tuple[str, ...]
    source_files: tuple[str, ...]
    test_files: tuple[str, ...]
    canonical_test_globs: tuple[str, ...]
    forbidden_test_globs: tuple[str, ...]
    paired_source_globs: tuple[str, ...]
    paired_source_matches: tuple[str, ...]
    requires_dual_lcov: bool
    lcov_unit_test_globs: tuple[str, ...]
    e2e_test_glob: str | None
    tier_c2_needs: str | None
    coverage_floors: tuple[tuple[str, float], ...]
    scoped_tier_b_commands: tuple[str, ...]
    manifest_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "stack_id": self.stack_id,
            "matched_files": list(self.matched_files),
            "source_files": list(self.source_files),
            "test_files": list(self.test_files),
            "canonical_test_globs": list(self.canonical_test_globs),
            "forbidden_test_globs": list(self.forbidden_test_globs),
            "paired_source_globs": list(self.paired_source_globs),
            "paired_source_matches": list(self.paired_source_matches),
            "requires_dual_lcov": self.requires_dual_lcov,
            "lcov_unit_test_globs": list(self.lcov_unit_test_globs),
            "e2e_test_glob": self.e2e_test_glob,
            "tier_c2_needs": self.tier_c2_needs,
            "coverage_floors": [
                [scope, floor] for scope, floor in self.coverage_floors
            ],
            "scoped_tier_b_commands": list(self.scoped_tier_b_commands),
            "manifest_path": self.manifest_path,
        }


@dataclass(frozen=True)
class ResolvedQualityPlan:
    """File-scoped quality plan across all active stacks for one task/plan."""

    repo_root: str
    base_ref: str
    planned_files: tuple[str, ...]
    active_stacks: tuple[str, ...]
    stack_plans: tuple[StackQualityPlan, ...]
    cache_bust_templates: tuple[str, ...]
    matched_floors: tuple[tuple[str, float], ...]
    scoped_tier_b_commands: tuple[str, ...]
    has_quality_manifests: bool = False
    unmatched_files: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "base_ref": self.base_ref,
            "planned_files": list(self.planned_files),
            "active_stacks": list(self.active_stacks),
            "stack_plans": [sp.to_dict() for sp in self.stack_plans],
            "cache_bust_templates": list(self.cache_bust_templates),
            "matched_floors": [[scope, floor] for scope, floor in self.matched_floors],
            "scoped_tier_b_commands": list(self.scoped_tier_b_commands),
            "has_quality_manifests": self.has_quality_manifests,
            "unmatched_files": list(self.unmatched_files),
        }


def _normalize_planned_path(raw: str) -> str:
    """Strip annotations like `(new)`, `:L1-L2`, `(L1-L2)` and normalize to POSIX."""
    cleaned = raw.strip().strip("`").strip("'\"")
    while cleaned:
        updated = _PATH_TRAIL_ANNOTATION_RE.sub("", cleaned).strip().strip("`")
        if updated == cleaned:
            break
        cleaned = updated
    cleaned = cleaned.replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned.strip()


def _normalize_planned_files(planned_files: Sequence[str]) -> tuple[str, ...]:
    seen: list[str] = []
    for raw in planned_files:
        norm = _normalize_planned_path(str(raw))
        if norm and norm not in seen:
            seen.append(norm)
    return tuple(seen)


def _extract_cmd_tokens(raw: Any) -> list[str]:
    if isinstance(raw, list) and all(isinstance(x, str) and x.strip() for x in raw):
        return [x.strip() for x in raw]
    return []


def _extract_flag_value(tokens: Sequence[str], flag_name: str) -> str | None:
    prefix = f"{flag_name}="
    for idx, tok in enumerate(tokens):
        if tok == flag_name and idx + 1 < len(tokens):
            return tokens[idx + 1].strip()
        if tok.startswith(prefix):
            return tok[len(prefix) :].strip()
    return None


def _parse_floor_value(raw: Any) -> float | None:
    candidate: Any = raw
    if isinstance(raw, Mapping):
        for key in ("floor", "min_coverage", "threshold"):
            if key in raw:
                candidate = raw[key]
                break
        else:
            return None
    if isinstance(candidate, bool):
        return None
    if isinstance(candidate, str):
        try:
            candidate = float(candidate.strip().rstrip("%"))
        except ValueError:
            return None
    if not isinstance(candidate, (int, float)):
        return None
    val = float(candidate)
    if 0.0 <= val <= 1.0:
        return val
    if 1.0 < val <= 100.0:
        return val / 100.0
    return None


def _format_pct(floor: float) -> str:
    pct = floor * 100.0
    rounded = round(pct)
    if abs(pct - rounded) < 1e-6:
        return f"{int(rounded)}%"
    return f"{pct:.1f}%"


def _join_command_tokens(tokens: Sequence[str]) -> str:
    parts: list[str] = []
    for tok in tokens:
        if tok == "<test_files>":
            parts.append(tok)
        elif "$D3NEXUS_KIT" in tok and not any(ch in tok for ch in ('"', "`", "\\")):
            parts.append(f'"{tok}"')
        else:
            parts.append(shlex.quote(tok))
    return " ".join(parts)


def _extract_dir_wrapper(tokens: Sequence[str]) -> str | None:
    found = registry._extract_monorepo_dir_wrapper(tokens)
    if found is not None:
        return found
    for flag in ("--directory", "--project", "--prefix"):
        raw_val = _extract_flag_value(tokens, flag)
        if raw_val:
            norm = registry._normalize_dir_value(raw_val)
            if norm:
                return norm
    return None


def web_requires_lcov_unit_tests(
    web_manifest: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    """Return `(True, lcov_globs)` when web manifest enforces V8/LCOV coverage on JS/MJS."""
    if not isinstance(web_manifest, Mapping):
        return False, ()
    capabilities = web_manifest.get("capabilities")
    if not isinstance(capabilities, Mapping):
        return False, ()

    commands: list[list[str]] = []
    for key in ("diff_coverage", "test_unit"):
        toks = _extract_cmd_tokens(capabilities.get(key))
        if toks:
            commands.append(toks)

    cov_cfg = capabilities.get("coverage")
    if isinstance(cov_cfg, Mapping):
        cov_toks = _extract_cmd_tokens(cov_cfg.get("command"))
        if cov_toks:
            commands.append(cov_toks)
    else:
        cov_toks = _extract_cmd_tokens(cov_cfg)
        if cov_toks:
            commands.append(cov_toks)

    if not commands:
        return False, ()

    references_lcov = False
    source_ext_values: list[str] = []
    for cmd in commands:
        if any(
            ".info" in tok.lower() or tok == "--lcov" or tok.startswith("--lcov=")
            for tok in cmd
        ):
            references_lcov = True
        src_ext = _extract_flag_value(cmd, "--source-ext")
        if src_ext is not None:
            source_ext_values.append(src_ext)

    if not references_lcov:
        return False, ()

    if source_ext_values:
        exts = {
            part.strip().lower()
            for raw_ext in source_ext_values
            for part in raw_ext.split(",")
            if part.strip()
        }
        if not (exts & {".js", ".mjs", "js", "mjs"}):
            return False, ()

    raw_routing = web_manifest.get("test_routing")
    custom_globs: tuple[str, ...] = ()
    if isinstance(raw_routing, Mapping):
        custom_globs = registry._string_list(raw_routing.get("lcov_unit_test_globs"))

    return True, custom_globs or DEFAULT_LCOV_UNIT_TEST_GLOBS


def find_cache_bust_templates(
    repo_root: Path,
    modified_assets: Sequence[str],
    web_manifest: Mapping[str, Any] | None,
) -> list[str]:
    """Find non-ignored HTML/Astro/Jinja templates referencing modified static assets via src=/href=."""
    if not isinstance(web_manifest, Mapping):
        return []
    capabilities = web_manifest.get("capabilities")
    has_ui_review = isinstance(capabilities, Mapping) and bool(
        capabilities.get("ui_review")
    )
    raw_routing = web_manifest.get("test_routing")
    configured_exts: tuple[str, ...] = ()
    if isinstance(raw_routing, Mapping):
        configured_exts = registry._normalize_extensions(
            raw_routing.get("cache_bust_extensions")
        )
    if not has_ui_review and not configured_exts:
        return []

    asset_exts = configured_exts or DEFAULT_CACHE_BUST_EXTENSIONS
    asset_names: list[str] = []
    for raw_asset in modified_assets:
        norm = _normalize_planned_path(raw_asset)
        if not norm:
            continue
        if registry.TriageSurfaceRegistry.is_test_file(norm):
            continue
        if norm.endswith((".test.js", ".spec.js", ".fixture.ts", ".test.mjs")):
            continue
        if PurePosixPath(norm).suffix.lower() not in asset_exts:
            continue
        name = PurePosixPath(norm).name
        if name and name not in asset_names:
            asset_names.append(name)

    if not asset_names or not repo_root.is_dir():
        return []

    patterns = [
        re.compile(rf"""(?:src|href)=['"][^'"]*?{re.escape(name)}(\?[^'"]*)?['"]""")
        for name in asset_names
    ]

    matched_templates: list[str] = []
    root_str = str(repo_root)
    for dirpath, dirnames, filenames in os.walk(root_str, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in _IGNORED_WALK_DIRS]
        for fname in filenames:
            if not fname.lower().endswith(_TEMPLATE_EXTENSIONS):
                continue
            full_path = Path(dirpath) / fname
            try:
                content = full_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if any(pat.search(content) for pat in patterns):
                rel = full_path.relative_to(repo_root).as_posix()
                matched_templates.append(rel)

    return sorted(set(matched_templates))


def _cap_ends_in_full_repo_python_target(cap: Sequence[str]) -> bool:
    tokens = [tok.strip() for tok in cap if isinstance(tok, str) and tok.strip()]
    if not tokens:
        return False

    def _norm_target(tok: str) -> str:
        cleaned = tok.replace("\\", "/")
        if cleaned in (".", "./"):
            return "."
        return cleaned.removeprefix("./").rstrip("/")

    last = _norm_target(tokens[-1])
    if last == "." and (
        len(tokens) < 2 or tokens[-2] not in registry._VALUE_TAKING_PATH_FLAGS
    ):
        return True
    if len(tokens) >= 2:
        tail_two = {_norm_target(tokens[-2]), last}
        if tail_two == {"src", "tests"} and (
            len(tokens) < 3 or tokens[-3] not in registry._VALUE_TAKING_PATH_FLAGS
        ):
            return True
    return False


def _extract_python_positional_targets(unwrapped: Sequence[str]) -> list[str]:
    if not unwrapped:
        return []
    tool = Path(unwrapped[0]).name.lower()
    idx = 1
    if idx < len(unwrapped) and (
        (tool == "ruff" and unwrapped[idx] in ("check", "format"))
        or (tool == "ty" and unwrapped[idx] == "check")
    ):
        idx += 1

    targets: list[str] = []
    in_positional = False
    while idx < len(unwrapped):
        tok = unwrapped[idx]
        if in_positional:
            targets.append(tok)
            idx += 1
            continue
        if tok == "--":
            in_positional = True
            idx += 1
            continue
        if tok in _PYTHON_VALUE_FLAGS:
            idx += 2
            continue
        if tok.startswith("-"):
            idx += 1
            continue
        targets.append(tok)
        idx += 1
    return targets


def is_full_repo_python_tier_b_subcommand(
    sub: Sequence[str],
    cap: Sequence[str] | None = None,
) -> bool:
    """Return True if `sub` runs ruff/mypy/pyright/ty against `.` or `src`+`tests`."""
    unwrapped = registry._strip_command_wrappers(sub)
    if not unwrapped:
        return False
    tool = Path(unwrapped[0]).name.lower()
    if tool not in _PYTHON_STATIC_TOOLS:
        return False
    if cap is not None and not _cap_ends_in_full_repo_python_target(cap):
        return False

    pos_targets = _extract_python_positional_targets(unwrapped)
    normalized: set[str] = set()
    for tok in pos_targets:
        cleaned = tok.strip().replace("\\", "/")
        if cleaned in (".", "./"):
            normalized.add(".")
        else:
            normalized.add(cleaned.removeprefix("./").rstrip("/"))

    return "." in normalized or {"src", "tests"}.issubset(normalized)


def _is_file_scoping_tool(tokens: Sequence[str]) -> tuple[bool, frozenset[str]]:
    unwrapped = registry._strip_command_wrappers(tokens)
    if not unwrapped:
        return False, frozenset()
    tool = Path(unwrapped[0]).name.lower()
    if tool in _PYTHON_STATIC_TOOLS:
        return True, _PYTHON_FULL_REPO_TARGETS
    if tool == "dart" and len(unwrapped) >= 2 and unwrapped[1] == "format":
        return True, _DART_FULL_REPO_TARGETS
    return False, frozenset()


def _rewrite_for_wrapper_dir(path: str, wrapper_dir: str | None) -> str:
    if not wrapper_dir:
        return path
    prefix = wrapper_dir.rstrip("/") + "/"
    if path.startswith(prefix):
        return path[len(prefix) :]
    if path == wrapper_dir.rstrip("/"):
        return "."
    return path


def _synthesize_scoped_command(
    raw_tokens: Sequence[str],
    *,
    base_ref: str,
    stack_files: Sequence[str],
    has_test_files: bool,
) -> str:
    interpolated = [
        tok.replace("{skills_dir}", "$D3NEXUS_KIT/skills").replace(
            "{base_ref}", base_ref
        )
        for tok in raw_tokens
    ]
    is_scoping, strip_targets = _is_file_scoping_tool(interpolated)
    if not is_scoping:
        return _join_command_tokens(interpolated)

    cmd = list(interpolated)
    while (
        len(cmd) > 1
        and cmd[-1] in strip_targets
        and cmd[-2] not in registry._VALUE_TAKING_PATH_FLAGS
    ):
        cmd.pop()

    wrapper_dir = _extract_dir_wrapper(cmd)
    scoped_targets = [_rewrite_for_wrapper_dir(p, wrapper_dir) for p in stack_files]
    if not has_test_files:
        scoped_targets.append("<test_files>")

    cmd.extend(scoped_targets)
    return _join_command_tokens(cmd)


def _extract_e2e_glob(capabilities: Mapping[str, Any]) -> str:
    e2e_cmd = _extract_cmd_tokens(capabilities.get("test_e2e"))
    if e2e_cmd:
        unwrapped = registry._strip_command_wrappers(e2e_cmd)
        for idx, tok in enumerate(unwrapped):
            if tok == "test" and idx + 1 < len(unwrapped):
                for arg in unwrapped[idx + 1 :]:
                    if not arg.startswith("-") and ("/" in arg or "e2e" in arg.lower()):
                        return arg
    return "tests/e2e/"


def _build_descriptor_from_manifest(
    sid: str,
    data: Mapping[str, Any],
) -> registry.StackDescriptor | None:
    builtin = registry.BUILTIN_STACKS.get(sid)
    declared_exts = registry._normalize_extensions(data.get("extensions"))
    if builtin is None and not declared_exts:
        return None
    caps = (
        data.get("capabilities")
        if isinstance(data.get("capabilities"), Mapping)
        else None
    )
    merged_exts = (
        tuple(dict.fromkeys((*builtin.extensions, *declared_exts)))
        if builtin is not None
        else declared_exts
    )
    return registry.StackDescriptor(
        stack_id=sid,
        extensions=merged_exts,
        test_path_patterns=builtin.test_path_patterns if builtin is not None else (),
        default_tier_b=registry._merge_tier_b_policy(
            builtin.default_tier_b if builtin is not None else registry.TierBPolicy(),
            data.get("task_tier_b"),
            caps,
        ),
        default_surfaces=(
            builtin.default_surfaces
            if builtin is not None
            else registry.SurfaceRuleSet()
        ),
        tier_c_policy=(
            builtin.tier_c_policy if builtin is not None else registry.TierCPolicy()
        ),
        test_routing=registry._parse_test_routing_policy(
            data.get("test_routing"),
            builtin.test_routing
            if builtin is not None
            else registry.TestRoutingPolicy(),
        ),
    )


def _load_quality_environment(
    repo_root: Path,
) -> tuple[
    dict[str, registry.StackDescriptor],
    dict[str, dict[str, Any]],
    dict[str, Path],
    bool,
]:
    """Load `.agents/quality/` manifests strictly (fail-closed via QualityPlanError)."""
    quality_dir = repo_root / ".agents" / "quality"
    if not quality_dir.is_dir():
        return dict(registry.BUILTIN_STACKS), {}, {}, False

    check_quality_path = quality_dir / "check_quality.json"
    extra_manifest_paths: list[tuple[str, Path]] = []
    if check_quality_path.is_file():
        cq_data, cq_err = registry._read_json_dict(check_quality_path)
        if cq_err is not None or cq_data is None:
            raise QualityPlanError(cq_err or "malformed check_quality.json")
        providers = cq_data.get("providers")
        if isinstance(providers, Mapping):
            for prov_id, prov_cfg in providers.items():
                if not isinstance(prov_id, str) or not isinstance(prov_cfg, Mapping):
                    continue
                rel_cfg = prov_cfg.get("config") or prov_cfg.get("config_path")
                if isinstance(rel_cfg, str) and registry._is_safe_relative_path(
                    rel_cfg, repo_root
                ):
                    cand = repo_root / rel_cfg
                    if cand.is_file():
                        extra_manifest_paths.append((prov_id, cand))

    manifest_files: dict[str, Path] = {}
    for path in sorted(quality_dir.glob("*-quality.json")):
        if path.is_file():
            sid = path.name.removesuffix("-quality.json")
            if sid:
                manifest_files[sid] = path
    for prov_id, cand in extra_manifest_paths:
        sid = (
            cand.name.removesuffix("-quality.json")
            if cand.name.endswith("-quality.json")
            else prov_id
        )
        manifest_files.setdefault(sid, cand)

    if not manifest_files:
        return dict(registry.BUILTIN_STACKS), {}, {}, False

    raw_manifests: dict[str, dict[str, Any]] = {}
    for sid, path in manifest_files.items():
        data, err = registry._read_json_dict(path)
        if err is not None or data is None:
            raise QualityPlanError(err or f"malformed {path.name}")
        raw_manifests[sid] = data

    loaded_descs, _, reg_errors = registry._load_repo_manifests(repo_root)
    if reg_errors:
        raise QualityPlanError("; ".join(reg_errors))

    descriptors: dict[str, registry.StackDescriptor] = {}
    for sid, data in raw_manifests.items():
        desc = loaded_descs.get(sid) or _build_descriptor_from_manifest(sid, data)
        if desc is not None:
            descriptors[sid] = desc

    return descriptors, raw_manifests, manifest_files, True


def _load_coverage_floors_files(
    repo_root: Path,
    active_manifests: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    candidate_paths: list[Path] = []
    default_floors = repo_root / ".agents" / "quality" / "coverage_floors.json"
    if default_floors.is_file():
        candidate_paths.append(default_floors)

    for manifest in active_manifests.values():
        caps = manifest.get("capabilities")
        if not isinstance(caps, Mapping):
            continue
        cov = caps.get("coverage")
        if not isinstance(cov, Mapping):
            continue
        rel_floors = cov.get("package_floors")
        if isinstance(rel_floors, str) and registry._is_safe_relative_path(
            rel_floors, repo_root
        ):
            path = repo_root / rel_floors
            if path.is_file() and path not in candidate_paths:
                candidate_paths.append(path)

    loaded: list[dict[str, Any]] = []
    for path in candidate_paths:
        data, err = registry._read_json_dict(path)
        if err is not None or data is None:
            raise QualityPlanError(err or f"malformed {path.name}")
        loaded.append(data)
    return loaded


def _match_longest_prefix(
    file_path: str,
    prefix_floors: Mapping[str, float],
    *,
    allow_src_strip: bool = False,
) -> tuple[str, float] | None:
    best_key: str | None = None
    best_score: tuple[int, int] = (-1, -1)
    best_val: float = 0.0

    for orig_key, floor in prefix_floors.items():
        norm_key = orig_key.replace("\\", "/").removeprefix("./").rstrip("/")
        if not norm_key:
            continue
        if file_path == norm_key or file_path.startswith(norm_key + "/"):
            score = (len(norm_key), 1)
            if score > best_score:
                best_score = score
                best_key = orig_key
                best_val = floor
        elif (
            allow_src_strip
            and file_path.startswith("src/")
            and not norm_key.startswith("src/")
        ):
            stripped = file_path[4:]
            if stripped == norm_key or stripped.startswith(norm_key + "/"):
                score = (len(norm_key), 0)
                if score > best_score:
                    best_score = score
                    best_key = orig_key
                    best_val = floor

    if best_key is None:
        return None
    return best_key, best_val


def _extract_floor_map(
    raw: Any, *, exclude_keys: frozenset[str] = frozenset()
) -> dict[str, float]:
    if not isinstance(raw, Mapping):
        return {}
    result: dict[str, float] = {}
    for key, val in raw.items():
        if not isinstance(key, str) or key in exclude_keys:
            continue
        parsed = _parse_floor_value(val)
        if parsed is not None:
            result[key] = parsed
    return result


def _collect_stack_floors(
    stack_id: str,
    manifest: Mapping[str, Any] | None,
    stack_files: Sequence[str],
    floors_docs: Sequence[Mapping[str, Any]],
) -> tuple[tuple[str, float], ...]:
    floors: dict[str, float] = {}

    if isinstance(manifest, Mapping):
        caps = manifest.get("capabilities")
        if isinstance(caps, Mapping):
            cov = caps.get("coverage")
            if isinstance(cov, Mapping):
                for key in ("threshold", "min_package_coverage", "min_diff_coverage"):
                    parsed = _parse_floor_value(cov.get(key))
                    if parsed is not None:
                        floors[key] = parsed
            diff_cov_toks = _extract_cmd_tokens(caps.get("diff_coverage"))
            if diff_cov_toks:
                parsed_diff = _parse_floor_value(
                    _extract_flag_value(diff_cov_toks, "--min-diff-coverage")
                )
                if parsed_diff is not None and "min_diff_coverage" not in floors:
                    floors["min_diff_coverage"] = parsed_diff

    for doc in floors_docs:
        if stack_id == "python":
            py_block = doc.get("python")
            adapters = (
                _extract_floor_map(py_block.get("adapters"))
                if isinstance(py_block, Mapping)
                else {}
            )
            for fpath in stack_files:
                hit = _match_longest_prefix(fpath, adapters, allow_src_strip=True)
                if hit is not None:
                    floors[hit[0]] = hit[1]

        if stack_id == "web":
            raw_wm = _extract_floor_map(doc.get("web_modules"))
            if raw_wm:
                norm_to_orig = {
                    k.replace("\\", "/").removeprefix("./"): (k, v)
                    for k, v in raw_wm.items()
                }
                basename_counts = Counter(PurePosixPath(nk).name for nk in norm_to_orig)
                for fpath in stack_files:
                    if fpath in norm_to_orig:
                        orig_k, val = norm_to_orig[fpath]
                        floors[orig_k] = val
                        continue
                    if registry.TriageSurfaceRegistry.is_test_file(fpath):
                        continue
                    suffix_hits = [
                        item
                        for nk, item in norm_to_orig.items()
                        if fpath.endswith("/" + nk)
                    ]
                    if len(suffix_hits) == 1:
                        floors[suffix_hits[0][0]] = suffix_hits[0][1]
                        continue
                    fname = PurePosixPath(fpath).name
                    if basename_counts.get(fname) == 1:
                        for nk, item in norm_to_orig.items():
                            if PurePosixPath(nk).name == fname:
                                floors[item[0]] = item[1]
                                break

        generic_prefixes = _extract_floor_map(doc.get("packages"))
        generic_prefixes.update(
            _extract_floor_map(doc, exclude_keys=_RESERVED_FLOOR_KEYS)
        )
        if generic_prefixes:
            for fpath in stack_files:
                hit = _match_longest_prefix(fpath, generic_prefixes)
                if hit is not None:
                    floors[hit[0]] = hit[1]

    return tuple(floors.items())


def _is_stack_test_file(rel_path: str, desc: registry.StackDescriptor) -> bool:
    if registry.TriageSurfaceRegistry.is_test_file(rel_path):
        return True
    tr = desc.test_routing
    return any(
        registry._glob_matches(pat, rel_path)
        for pat in (*tr.canonical_test_globs, *tr.lcov_unit_test_globs)
    )


def _path_matches_stack_extended(
    rel_path: str,
    desc: registry.StackDescriptor,
    raw_manifest: Mapping[str, Any] | None,
) -> bool:
    if registry._path_matches_stack(rel_path, desc):
        return True
    if desc.stack_id == "web" and isinstance(raw_manifest, Mapping):
        caps = raw_manifest.get("capabilities")
        has_ui = isinstance(caps, Mapping) and bool(caps.get("ui_review"))
        cb_exts = desc.test_routing.cache_bust_extensions or (
            DEFAULT_CACHE_BUST_EXTENSIONS if has_ui else ()
        )
        if cb_exts and PurePosixPath(rel_path).suffix.lower() in cb_exts:
            return True
    return False


def _synthesize_stack_tier_b_commands(
    desc: registry.StackDescriptor,
    raw_manifest: Mapping[str, Any] | None,
    *,
    base_ref: str,
    stack_files: Sequence[str],
    all_planned_files: Sequence[str],
    has_test_files: bool,
) -> tuple[str, ...]:
    commands: list[str] = []
    boundary_triggered = any(
        registry._path_matches_boundary_trigger(fpath, trigger)
        for fpath in stack_files
        for trigger in desc.default_tier_b.boundary_triggers
    ) or any(
        PurePosixPath(fpath).name == trigger
        for fpath in all_planned_files
        for trigger in desc.default_tier_b.boundary_triggers
        if not trigger.endswith("/") and not trigger.startswith(".")
    )

    if isinstance(raw_manifest, Mapping) and isinstance(
        raw_manifest.get("capabilities"), Mapping
    ):
        caps = raw_manifest["capabilities"]
        cap_groups: list[tuple[str, ...]] = list(_STATIC_CAP_GROUPS)
        if boundary_triggered:
            cap_groups.append(_BOUNDARY_CAP_KEYS)
        for group in cap_groups:
            for key in group:
                toks = _extract_cmd_tokens(caps.get(key))
                if not toks:
                    continue
                cmd_str = _synthesize_scoped_command(
                    toks,
                    base_ref=base_ref,
                    stack_files=stack_files,
                    has_test_files=has_test_files,
                )
                if cmd_str and cmd_str not in commands:
                    commands.append(cmd_str)
                    break
        return tuple(commands)

    # Fallback defaults when `.agents/quality/` has no manifest for this stack
    tb = desc.default_tier_b
    default_prefixes: list[str] = []
    if tb.format_prefixes:
        default_prefixes.append(tb.format_prefixes[0])
    if tb.lint_prefixes:
        default_prefixes.append(tb.lint_prefixes[0])
    if tb.typecheck_prefixes:
        default_prefixes.append(tb.typecheck_prefixes[0])
    if boundary_triggered and tb.boundary_prefixes:
        default_prefixes.append(tb.boundary_prefixes[0])

    for prefix in default_prefixes:
        try:
            toks = shlex.split(prefix)
        except ValueError:
            toks = prefix.split()
        if not toks:
            continue
        cmd_str = _synthesize_scoped_command(
            toks,
            base_ref=base_ref,
            stack_files=stack_files,
            has_test_files=has_test_files,
        )
        if cmd_str and cmd_str not in commands:
            commands.append(cmd_str)
    return tuple(commands)


def resolve_quality_plan(
    repo_root: Path,
    planned_files: Sequence[str],
    *,
    base_ref: str = "develop",
) -> ResolvedQualityPlan:
    """Resolve file-scoped quality requirements across active stacks in <0.10s."""
    root = repo_root.resolve()
    normalized_files = _normalize_planned_files(planned_files)
    descriptors, raw_manifests, manifest_paths, has_manifests = (
        _load_quality_environment(root)
    )

    stack_file_buckets: dict[str, list[str]] = {}
    matched_any: set[str] = set()
    for sid, desc in descriptors.items():
        raw_m = raw_manifests.get(sid)
        matched = [
            fpath
            for fpath in normalized_files
            if _path_matches_stack_extended(fpath, desc, raw_m)
        ]
        if matched:
            stack_file_buckets[sid] = matched
            matched_any.update(matched)

    unmatched = tuple(f for f in normalized_files if f not in matched_any)
    active_stacks = tuple(stack_file_buckets.keys())
    active_manifests = {
        sid: raw_manifests[sid] for sid in active_stacks if sid in raw_manifests
    }
    floors_docs = _load_coverage_floors_files(root, active_manifests)

    stack_plans: list[StackQualityPlan] = []
    all_floors: list[tuple[str, float]] = []
    all_tier_b: list[str] = []

    for sid in active_stacks:
        desc = descriptors[sid]
        raw_m = raw_manifests.get(sid)
        matched_files = tuple(stack_file_buckets[sid])
        test_files = tuple(f for f in matched_files if _is_stack_test_file(f, desc))
        source_files = tuple(f for f in matched_files if f not in test_files)

        canonical = (
            desc.test_routing.canonical_test_globs
            or DEFAULT_CANONICAL_TEST_GLOBS.get(sid, desc.test_path_patterns)
        )
        forbidden = desc.test_routing.forbidden_test_globs
        paired_globs = desc.test_routing.paired_source_globs
        paired_matches = tuple(
            f
            for f in source_files
            if any(registry._glob_matches(pat, f) for pat in paired_globs)
        )

        requires_dual_lcov = False
        lcov_globs: tuple[str, ...] = ()
        e2e_glob: str | None = None
        tier_c2_needs: str | None = None
        if sid == "web" and isinstance(raw_m, Mapping):
            has_lcov, detected_globs = web_requires_lcov_unit_tests(raw_m)
            has_non_test_js = any(
                PurePosixPath(f).suffix.lower() in (".js", ".mjs") for f in source_files
            )
            if has_lcov and has_non_test_js:
                requires_dual_lcov = True
                lcov_globs = detected_globs
                caps = raw_m.get("capabilities")
                e2e_glob = _extract_e2e_glob(caps if isinstance(caps, Mapping) else {})
                tier_c2_needs = "PLAYWRIGHT_BROWSER"

        stack_floors = _collect_stack_floors(sid, raw_m, matched_files, floors_docs)
        for scope, val in stack_floors:
            pair = (f"{sid}:{scope}", val)
            if pair not in all_floors:
                all_floors.append(pair)

        scoped_cmds = _synthesize_stack_tier_b_commands(
            desc,
            raw_m,
            base_ref=base_ref,
            stack_files=matched_files,
            all_planned_files=normalized_files,
            has_test_files=bool(test_files),
        )
        for cmd in scoped_cmds:
            if cmd not in all_tier_b:
                all_tier_b.append(cmd)

        m_path = manifest_paths.get(sid)
        rel_m_path = m_path.relative_to(root).as_posix() if m_path is not None else None
        stack_plans.append(
            StackQualityPlan(
                stack_id=sid,
                matched_files=matched_files,
                source_files=source_files,
                test_files=test_files,
                canonical_test_globs=canonical,
                forbidden_test_globs=forbidden,
                paired_source_globs=paired_globs,
                paired_source_matches=paired_matches,
                requires_dual_lcov=requires_dual_lcov,
                lcov_unit_test_globs=lcov_globs,
                e2e_test_glob=e2e_glob,
                tier_c2_needs=tier_c2_needs,
                coverage_floors=stack_floors,
                scoped_tier_b_commands=scoped_cmds,
                manifest_path=rel_m_path,
            )
        )

    cache_bust_templates: tuple[str, ...] = ()
    if "web" in active_stacks and "web" in raw_manifests:
        cache_bust_templates = tuple(
            find_cache_bust_templates(
                root, stack_file_buckets["web"], raw_manifests["web"]
            )
        )

    return ResolvedQualityPlan(
        repo_root=str(root),
        base_ref=base_ref,
        planned_files=normalized_files,
        active_stacks=active_stacks,
        stack_plans=tuple(stack_plans),
        cache_bust_templates=cache_bust_templates,
        matched_floors=tuple(all_floors),
        scoped_tier_b_commands=tuple(all_tier_b),
        has_quality_manifests=has_manifests,
        unmatched_files=unmatched,
    )


def _format_stack_tests_line(sp: StackQualityPlan) -> str:
    parts: list[str] = []
    if sp.requires_dual_lcov:
        primary_lcov = (
            sp.lcov_unit_test_globs[0]
            if sp.lcov_unit_test_globs
            else DEFAULT_LCOV_UNIT_TEST_GLOBS[0]
        )
        e2e_glob = sp.e2e_test_glob or "tests/e2e/"
        needs = sp.tier_c2_needs or "PLAYWRIGHT_BROWSER"
        parts.append(
            f"DUAL REQUIRED -> unit LCOV in {primary_lcov} + UI E2E in {e2e_glob} "
            f"(# tier: C2, Needs: {needs})"
        )
    elif (
        sp.stack_id == "python"
        and sp.canonical_test_globs == DEFAULT_CANONICAL_TEST_GLOBS["python"]
    ):
        parts.append(
            "canonical=tests/unit/**/test_*.py (Tier A), "
            "tests/integration/test_*.py (Tier C1)"
        )
    elif sp.canonical_test_globs:
        parts.append(f"canonical={', '.join(sp.canonical_test_globs)}")
    else:
        parts.append("canonical=project default")

    if sp.forbidden_test_globs:
        parts.append(f"forbidden={', '.join(sp.forbidden_test_globs)}")
    if sp.paired_source_matches:
        parts.append(f"paired-unit={', '.join(sp.paired_source_matches)}")
    return f"TESTS [{sp.stack_id}]: {'; '.join(parts)}"


def format_compact_plan(plan: ResolvedQualityPlan) -> str:
    """Format a ResolvedQualityPlan into 5-10 compact lines for typical 1-2 stack tasks."""
    if not plan.stack_plans:
        unmatched_str = ", ".join(plan.unmatched_files) or "none"
        return "\n".join(
            [
                f"QUALITY PLAN | stacks: none | files: {len(plan.planned_files)} | base-ref: {plan.base_ref}",
                f"UNMATCHED: {unmatched_str}",
                "VERIFY: no configured stack extensions matched planned files",
            ]
        )

    lines: list[str] = [
        f"QUALITY PLAN | stacks: {', '.join(plan.active_stacks)} "
        f"| files: {len(plan.planned_files)} | base-ref: {plan.base_ref}"
    ]

    for sp in plan.stack_plans:
        lines.append(_format_stack_tests_line(sp))

    floor_segments: list[str] = []
    for sp in plan.stack_plans:
        if sp.coverage_floors:
            rendered = ", ".join(
                f"{scope}={_format_pct(val)}" for scope, val in sp.coverage_floors
            )
            floor_segments.append(f"{sp.stack_id}({rendered})")
    lines.append(
        f"FLOORS: {'; '.join(floor_segments)}"
        if floor_segments
        else "FLOORS: none configured"
    )

    if plan.cache_bust_templates:
        lines.append(f"CACHE-BUST (?v=): {', '.join(plan.cache_bust_templates)}")

    for sp in plan.stack_plans:
        joined_cmds = " && ".join(sp.scoped_tier_b_commands) or "none configured"
        lines.append(f"TIER-B [{sp.stack_id}]: {joined_cmds}")

    lines.append(
        "VERIFY: scope intermediate TIER-B to Allowed files; "
        "keep $D3NEXUS_KIT/skills and base-ref expanded"
    )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resolve_task_quality_plan.py",
        description="Emit a compact file-scoped quality plan from .agents/quality/ manifests.",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Planned file paths (supports `(new)` and `:L1-L2`/`(L1-L2)` annotations).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root directory (defaults to current working directory).",
    )
    parser.add_argument(
        "--base-ref",
        default="develop",
        help="Git base ref substituted for `{base_ref}` placeholders (default: develop).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit machine-readable JSON instead of compact text lines.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 2
        return code

    cleaned_files = _normalize_planned_files(args.files)
    if not cleaned_files:
        sys.stderr.write(
            "resolve-quality error: --files must include at least one non-empty path\n"
        )
        return 2

    repo_root = args.repo_root if args.repo_root is not None else Path.cwd()
    try:
        plan = resolve_quality_plan(
            repo_root, cleaned_files, base_ref=str(args.base_ref)
        )
    except QualityPlanError as exc:
        sys.stderr.write(f"resolve-quality error: {exc}\n")
        return 2

    if args.as_json:
        print(json.dumps(plan.to_dict(), indent=2))
    else:
        print(format_compact_plan(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
