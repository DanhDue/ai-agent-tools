#!/usr/bin/env python3
"""Deterministic rule-based workload duration and heartbeat cadence estimator.

Evaluates task count, file count, epic/wave scope, quality profile, and E2E
flags with zero LLM or network calls, mapping workloads into light (<60s),
medium (60..240s), or heavy (>240s) cadence tiers.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

BASE_SEC = 5
PER_TASK_SEC = 25
PER_FILE_SEC = 5
E2E_BONUS_SEC = 240

PROFILE_BASELINES: dict[str, int] = {
    "fast": 15,
    "pr": 120,
    "epic": 210,
    "release": 245,
    "full": 245,
}

COMPLETED_STATUSES = {"done", "completed", "cancelled", "skipped"}

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
FILES_SECTION_RE = re.compile(r"##\s*Files\s*\n(.*?)(\n##|\Z)", re.DOTALL)
DEPS_SECTION_RE = re.compile(
    r"##\s*Dependencies\s*(?:&|and)\s*Blockers\s*\n(.*?)(\n##|\Z)", re.DOTALL
)
ALLOWED_BULLET_RE = re.compile(r"^\s*-\s*`([^`]+)`(?:\s*\(new\))?\s*$")
LINK_RE = re.compile(r"\]\(([^)]+\.md)\)")
NUMBER_RE = re.compile(r"\d+")


def _normalize_slug(value: str) -> str:
    return re.sub(r"[-_]+", "_", value.strip().lower())


def _parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, raw_val = line.split(":", 1)
        val = raw_val.strip().strip('"').strip("'")
        result[key.strip()] = val
    return result


def _parse_allowed_files(text: str) -> list[str]:
    section_match = FILES_SECTION_RE.search(text)
    body = section_match.group(1) if section_match else ""
    files: list[str] = []
    in_allowed = False
    for line in body.splitlines():
        stripped = line.strip()
        if not in_allowed:
            if stripped == "Allowed files:":
                in_allowed = True
            continue
        bullet = ALLOWED_BULLET_RE.match(line)
        if bullet:
            files.append(bullet.group(1))
        elif stripped.startswith("- `"):
            start = stripped.find("`") + 1
            end = stripped.find("`", start)
            if end != -1:
                files.append(stripped[start:end])
        elif stripped and not stripped.startswith("-"):
            break
    return files


def _parse_blockers(text: str) -> list[str]:
    section_match = DEPS_SECTION_RE.search(text)
    if not section_match:
        return []
    blockers: list[str] = []
    for line in section_match.group(1).splitlines():
        if "Blocked by" not in line:
            continue
        blockers.extend(Path(link).stem for link in LINK_RE.findall(line))
    return blockers


def _task_sort_key(task_id: str) -> tuple[int, str]:
    match = NUMBER_RE.search(task_id)
    return (int(match.group()) if match else 0, task_id)


def _compute_layers(tasks: dict[str, dict[str, Any]]) -> list[list[str]]:
    remaining = dict(tasks)
    resolved: set[str] = set()
    layers: list[list[str]] = []
    known_ids = set(tasks)

    while remaining:
        layer = [
            tid
            for tid, task in remaining.items()
            if all(b not in known_ids or b in resolved for b in task["blockers"])
        ]
        if not layer:
            layer = sorted(remaining, key=_task_sort_key)
            layers.append(layer)
            break
        layer.sort(key=_task_sort_key)
        layers.append(layer)
        resolved.update(layer)
        for tid in layer:
            del remaining[tid]
    return layers


def _load_task_entry(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = _parse_frontmatter(text)
    task_id = fm.get("id") or path.stem
    wave_raw = fm.get("wave", "")
    wave_num: int | None = None
    if wave_raw.isdigit():
        wave_num = int(wave_raw)
    return {
        "id": task_id,
        "stem": path.stem,
        "epic": fm.get("epic", ""),
        "status": (fm.get("status") or "todo").strip().lower(),
        "wave": wave_num,
        "blockers": _parse_blockers(text),
        "allowed_files": _parse_allowed_files(text),
    }


def _find_epic_and_features_dirs(
    epic_dir: str | Path,
) -> tuple[Path | None, Path | None, str]:
    raw = Path(epic_dir)
    if raw.is_dir():
        resolved = raw.resolve()
        devtool_root = (
            resolved.parent.parent if resolved.parent.name == "epic" else None
        )
        features = (devtool_root / "features") if devtool_root else None
        return resolved, features, resolved.name

    cwd = Path.cwd()
    devtool_dir = cwd / ".devtool"
    epic_parent = devtool_dir / "epic"
    target_norm = _normalize_slug(str(epic_dir))
    matched_epic: Path | None = None
    if epic_parent.is_dir():
        direct = epic_parent / str(epic_dir)
        if direct.is_dir():
            matched_epic = direct
        else:
            for candidate in sorted(epic_parent.iterdir()):
                if (
                    candidate.is_dir()
                    and _normalize_slug(candidate.name) == target_norm
                ):
                    matched_epic = candidate
                    break
    features_dir = devtool_dir / "features"
    return (
        matched_epic,
        (features_dir if features_dir.is_dir() else None),
        str(epic_dir),
    )


def _resolve_epic_counts(epic_dir: str | Path, wave: int | None) -> tuple[int, int]:
    epic_path, features_dir, slug_hint = _find_epic_and_features_dirs(epic_dir)
    target_norm = _normalize_slug(slug_hint)

    tasks: dict[str, dict[str, Any]] = {}
    if epic_path is not None:
        for task_file in sorted(epic_path.glob("task_*.md")):
            entry = _load_task_entry(task_file)
            tasks[entry["id"]] = entry

    if features_dir is not None and features_dir.is_dir():
        feature_files = sorted(features_dir.glob("task_*.md"))
        done_dir = features_dir / "done"
        if done_dir.is_dir():
            feature_files.extend(sorted(done_dir.glob("task_*.md")))
        for feat_file in feature_files:
            entry = _load_task_entry(feat_file)
            epic_norm = _normalize_slug(entry["epic"]) if entry["epic"] else ""
            if epic_norm == target_norm or entry["id"] in tasks:
                tasks[entry["id"]] = entry

    if not tasks:
        return 0, 0

    selected_ids: list[str]
    if wave is None:
        selected_ids = list(tasks)
    elif any(task["wave"] is not None for task in tasks.values()):
        selected_ids = [tid for tid, task in tasks.items() if task["wave"] == wave]
    else:
        layers = _compute_layers(tasks)
        if wave < 0:
            selected_ids = []
        elif wave == 0:
            selected_ids = layers[0] if layers else []
        elif wave <= len(layers):
            selected_ids = layers[wave - 1]
        else:
            selected_ids = []

    pending_tasks = [
        tasks[tid]
        for tid in selected_ids
        if tasks[tid]["status"] not in COMPLETED_STATUSES
    ]
    unique_files: set[str] = set()
    for task in pending_tasks:
        unique_files.update(task["allowed_files"])
    return len(pending_tasks), len(unique_files)


def estimate_workload(
    tasks_count: int | None = None,
    files_count: int | None = None,
    *,
    epic_dir: str | Path | None = None,
    wave: int | None = None,
    quality_profile: str | None = None,
    has_e2e: bool = False,
) -> dict[str, Any]:
    """Compute deterministic workload duration estimate and heartbeat tier."""
    if quality_profile is not None and quality_profile not in PROFILE_BASELINES:
        valid = ", ".join(sorted(PROFILE_BASELINES))
        raise ValueError(
            f"Unsupported quality_profile '{quality_profile}'; expected one of: {valid}"
        )

    derived_tasks = 0
    derived_files = 0
    if epic_dir is not None and (tasks_count is None or files_count is None):
        derived_tasks, derived_files = _resolve_epic_counts(epic_dir, wave)

    resolved_tasks = max(0, int(derived_tasks if tasks_count is None else tasks_count))
    resolved_files = max(0, int(derived_files if files_count is None else files_count))
    profile_sec = PROFILE_BASELINES[quality_profile] if quality_profile else 0
    e2e_sec = E2E_BONUS_SEC if has_e2e else 0

    estimated_sec = (
        BASE_SEC
        + (PER_TASK_SEC * resolved_tasks)
        + (PER_FILE_SEC * resolved_files)
        + profile_sec
        + e2e_sec
    )

    if estimated_sec < 60:
        tier = "light"
        recommended_interval_sec: int | None = None
    elif estimated_sec <= 240:
        tier = "medium"
        recommended_interval_sec = 180
    else:
        tier = "heavy"
        recommended_interval_sec = 300 if has_e2e else 240

    reason = (
        f"base={BASE_SEC}s + tasks={resolved_tasks}*{PER_TASK_SEC}s "
        f"+ files={resolved_files}*{PER_FILE_SEC}s "
        f"+ profile={quality_profile or 'none'}({profile_sec}s) "
        f"+ e2e={e2e_sec}s -> {estimated_sec}s ({tier})"
    )
    return {
        "estimated_sec": estimated_sec,
        "tier": tier,
        "recommended_interval_sec": recommended_interval_sec,
        "tasks_count": resolved_tasks,
        "files_count": resolved_files,
        "quality_profile": quality_profile,
        "has_e2e": has_e2e,
        "reason": reason,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for heartbeat estimation."""
    parser = argparse.ArgumentParser(
        description="Deterministic zero-LLM workload duration and heartbeat estimator."
    )
    parser.add_argument(
        "--tasks-count",
        type=int,
        default=None,
        help="Explicit pending tasks count (clamped to >= 0)",
    )
    parser.add_argument(
        "--files-count",
        type=int,
        default=None,
        help="Explicit modified files count (clamped to >= 0)",
    )
    parser.add_argument(
        "--epic-dir",
        default=None,
        help="Epic slug or directory path to derive pending tasks/files when counts omitted",
    )
    parser.add_argument(
        "--wave",
        type=int,
        default=None,
        help="Optional wave number when inspecting --epic-dir",
    )
    parser.add_argument(
        "--quality-profile",
        choices=("fast", "pr", "epic", "release", "full"),
        default=None,
        help="Quality profile baseline duration",
    )
    parser.add_argument(
        "--has-e2e",
        action="store_true",
        help="Include E2E test suite baseline and escalate heavy cadence to 300s",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for estimate_heartbeat.py."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = estimate_workload(
            tasks_count=args.tasks_count,
            files_count=args.files_count,
            epic_dir=args.epic_dir,
            wave=args.wave,
            quality_profile=args.quality_profile,
            has_e2e=args.has_e2e,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        interval = (
            f"{result['recommended_interval_sec']}s"
            if result["recommended_interval_sec"] is not None
            else "none"
        )
        print(
            f"tier={result['tier']} estimated_sec={result['estimated_sec']}s "
            f"recommended_interval={interval} ({result['reason']})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
