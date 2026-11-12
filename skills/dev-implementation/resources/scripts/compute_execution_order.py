#!/usr/bin/env python3
"""Compute a sequential execution order for one epic's Kanban tasks.

Reads every `.devtool/features/task_*.md` file whose frontmatter `epic:`
matches the given epic slug, builds a dependency graph from each task's
"## Dependencies & Blockers" section (only lines containing the literal
phrase "Blocked by" count as hard blockers -- this matches the phrasing
dev-designer's own task template prescribes), and prints:

  1. Tasks grouped into layers. Tasks in the same layer have no dependency
     on each other -- they could technically run in parallel, though
     dev-implementation runs them sequentially (see the design spec).
  2. Any soft notes found in that section -- currently lines containing
     "Recommended" or "New dependency" (see SOFT_NOTE_MARKERS). These are
     NOT treated as hard blockers, so review them manually; the computed
     layer for that task may be earlier than the note suggests.
  3. One flattened sequential order: earlier layers first, and within a
     layer, higher priority first, then lower task number first.

It also prints a scan summary (how many `task_*.md` files were seen, how
many matched the epic, how many were skipped) so a task file with broken
or missing frontmatter is never silently dropped.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from slug_utils import parse_frontmatter, sanitize_slug

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
# Soft-note markers: keyword list used to surface advisory content that isn't a hard blocker.
# These are small, documented keywords — not a general sentence parser. Phase 0 (full task text)
# in the operating skill is the actual safety net for anything these markers miss.
SOFT_NOTE_MARKERS = ("Recommended", "New dependency")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
SECTION_RE = re.compile(r"##\s*Dependencies\s*(?:&|and)\s*Blockers\s*\n(.*?)(\n##|\Z)", re.DOTALL)
FILES_SECTION_RE = re.compile(r"##\s*Files\s*\n(.*?)(\n##|\Z)", re.DOTALL)
ALLOWED_BULLET_RE = re.compile(r"^\s*-\s*`([^`]+)`(?:\s*\(new\))?\s*$")
LINK_RE = re.compile(r"\]\(([^)]+\.md)\)")
TITLE_RE = re.compile(r"^#\s*Task\s*\d+:\s*(.+)$", re.MULTILINE)
NUMBER_RE = re.compile(r"\d+")


def parse_dependencies_section(text: str) -> str:
    match = SECTION_RE.search(text)
    return match.group(1) if match else ""


def parse_allowed_files(text: str) -> list[str]:
    """Extract paths listed under the 'Allowed files:' block in the task markdown."""
    match = FILES_SECTION_RE.search(text)
    body = match.group(1) if match else text
    allowed: list[str] = []
    in_allowed = False
    for line in body.splitlines():
        trimmed = line.strip()
        if trimmed == "Allowed files:":
            in_allowed = True
            continue
        if in_allowed:
            bullet = ALLOWED_BULLET_RE.match(line)
            if bullet:
                allowed.append(bullet.group(1))
            elif trimmed.startswith("- `"):
                # Fallback pattern
                start = trimmed.find("`") + 1
                end = trimmed.find("`", start)
                if end != -1:
                    allowed.append(trimmed[start:end])
            elif trimmed and not trimmed.startswith("-"):
                break
    return allowed


def parse_blockers(section: str) -> list[str]:
    blockers = []
    for line in section.splitlines():
        if "Blocked by" not in line:
            continue
        blockers.extend(Path(link).stem for link in LINK_RE.findall(line))
    return blockers


def parse_soft_notes(section: str) -> list[str]:
    return [line.strip().lstrip("-").strip() for line in section.splitlines()
            if any(marker in line for marker in SOFT_NOTE_MARKERS)]


def extract_title(text: str) -> str:
    match = TITLE_RE.search(text)
    return match.group(1).strip() if match else "Untitled"


def scan_tasks(features_dir: Path, epic: str) -> tuple[dict[str, dict], list[Path], list[Path]]:
    """Load the epic's tasks AND report what was skipped.

    Returns (tasks, scanned_paths, skipped_paths). A file lands in
    `skipped_paths` when its frontmatter is missing/unparseable (so
    `epic:` reads as None) or names a different epic -- both look
    identical from the graph's point of view, which is exactly why the
    CLI reports the count instead of dropping them silently.
    """
    tasks: dict[str, dict] = {}
    scanned: list[Path] = []
    skipped: list[Path] = []
    target_epic = sanitize_slug(epic)
    candidate_paths = list(Path(features_dir).glob("task_*.md"))
    done_dir = Path(features_dir) / "done"
    if done_dir.is_dir():
        candidate_paths.extend(done_dir.glob("task_*.md"))
    for path in sorted(candidate_paths):
        scanned.append(path)
        text = path.read_text()
        fm = parse_frontmatter(text)
        task_epic = sanitize_slug(fm.get("epic"))
        if task_epic != target_epic:
            skipped.append(path)
            continue
        section = parse_dependencies_section(text)
        task_id = fm.get("id", path.stem)
        tasks[task_id] = {
            "id": task_id,
            "path": path,
            "priority": fm.get("priority", "medium"),
            "status": fm.get("status", "todo"),
            "blockers": parse_blockers(section),
            "soft_notes": parse_soft_notes(section),
            "allowed_files": parse_allowed_files(text),
            "title": extract_title(text),
        }
    return tasks, scanned, skipped


def load_tasks(features_dir: Path, epic: str) -> dict[str, dict]:
    tasks, _scanned, _skipped = scan_tasks(features_dir, epic)
    return tasks


def compute_layers(tasks: dict[str, dict]) -> list[list[str]]:
    # Validate that all blockers reference existing tasks
    for task_id, task in tasks.items():
        for blocker in task["blockers"]:
            if blocker not in tasks:
                raise ValueError(f"Task '{task_id}' is blocked by unknown task '{blocker}'")

    remaining = dict(tasks)
    resolved: set[str] = set()
    layers: list[list[str]] = []

    def sort_key(task_id: str) -> tuple:
        task = tasks[task_id]
        number_match = NUMBER_RE.search(task_id)
        number = int(number_match.group()) if number_match else 0
        return (PRIORITY_RANK.get(task["priority"], 1), number)

    while remaining:
        current_layer = [
            task_id
            for task_id, task in remaining.items()
            if all(b in resolved for b in task["blockers"])
        ]
        if not current_layer:
            raise ValueError(f"Cycle detected among: {sorted(remaining)}")
        current_layer.sort(key=sort_key)
        layers.append(current_layer)
        resolved.update(current_layer)
        for task_id in current_layer:
            del remaining[task_id]
    return layers


def compute_parallel_batches(
    layers: list[list[str]], tasks: dict[str, dict], pool_size: int = 2
) -> list[list[list[str]]]:
    """Group tasks within each topological layer into parallel execution batches.

    Tasks within the same layer have no dependencies, but if two tasks modify
    the same file (shared entry in 'allowed_files'), they are separated into
    subsequent batches to prevent Git / build workspace collision.
    Each batch contains at most pool_size tasks.
    """
    def sort_key(task_id: str) -> tuple:
        task = tasks.get(task_id, {})
        number_match = NUMBER_RE.search(task_id)
        number = int(number_match.group()) if number_match else 0
        return (PRIORITY_RANK.get(task.get("priority", "medium"), 1), number)

    all_layer_batches: list[list[list[str]]] = []
    for layer in layers:
        sorted_layer = sorted(layer, key=sort_key)
        layer_batches: list[list[str]] = []
        for task_id in sorted_layer:
            task = tasks.get(task_id, {})
            task_files = set(task.get("allowed_files", []))
            placed = False
            for batch in layer_batches:
                if len(batch) >= pool_size:
                    continue
                # Check collision with other tasks in this candidate batch
                has_conflict = False
                for other_id in batch:
                    other_task = tasks.get(other_id, {})
                    other_files = set(other_task.get("allowed_files", []))
                    if task_files and other_files and bool(task_files & other_files):
                        has_conflict = True
                        break
                if not has_conflict:
                    batch.append(task_id)
                    placed = True
                    break
            if not placed:
                layer_batches.append([task_id])
        all_layer_batches.append(layer_batches)
    return all_layer_batches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("epic", help="Epic slug, e.g. logging-refactor")
    parser.add_argument("--features-dir", default=".devtool/features",
                         help="Directory containing task_*.md files (default: .devtool/features)")
    parser.add_argument("--parallel", action="store_true",
                         help="Display execution plan grouped by parallel batches for worker pool")
    parser.add_argument("--pool-size", type=int, default=2,
                         help="Worker pool size for parallel batches (default: 2)")
    parser.add_argument("--json", action="store_true",
                         help="Emit machine-readable JSON output")
    args = parser.parse_args(argv)

    tasks, scanned, skipped = scan_tasks(Path(args.features_dir), args.epic)
    scan_summary = (
        f"Scanned {len(scanned)} task_*.md files; {len(tasks)} matched epic '{args.epic}'; "
        f"{len(skipped)} had no parseable frontmatter or a different epic."
    )
    if not tasks:
        if args.json:
            print(json.dumps({"error": f"No tasks found for epic '{args.epic}' in {args.features_dir}", "tasks": {}}))
        else:
            print(scan_summary, file=sys.stderr)
            print(f"No tasks found for epic '{args.epic}' in {args.features_dir}", file=sys.stderr)
        return 1

    try:
        layers = compute_layers(tasks)
        parallel_batches = compute_parallel_batches(layers, tasks, pool_size=args.pool_size)
    except ValueError as error:
        if args.json:
            print(json.dumps({"error": str(error)}))
        else:
            print(scan_summary, file=sys.stderr)
            print(f"Cannot compute an execution order: {error}", file=sys.stderr)
        return 1

    if args.json:
        payload = {
            "epic": args.epic,
            "tasks_count": len(tasks),
            "pool_size": args.pool_size,
            "layers": layers,
            "parallel_batches": parallel_batches,
            "tasks": {
                tid: {
                    "title": t["title"],
                    "priority": t["priority"],
                    "status": t["status"],
                    "blockers": t["blockers"],
                    "allowed_files": t.get("allowed_files", []),
                    "soft_notes": t.get("soft_notes", []),
                }
                for tid, t in tasks.items()
            },
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(scan_summary)
    if skipped:
        for path in skipped:
            print(f"  skipped: {path}")
    print()

    if args.parallel:
        print(f"Parallel execution plan for epic '{args.epic}' ({len(tasks)} tasks, {args.pool_size}-slot pool):\n")
        for i, layer_batches in enumerate(parallel_batches):
            layer_task_count = sum(len(b) for b in layer_batches)
            print(f"Layer {i} ({layer_task_count} tasks):")
            for j, batch in enumerate(layer_batches, start=1):
                tasks_info = ", ".join(f"{tid} [{tasks[tid]['priority']}]" for tid in batch)
                mode = f"Parallel (Slots 1-{len(batch)})" if len(batch) > 1 else "Slot 1"
                print(f"  Batch {i}.{j}: [{tasks_info}] -> {mode}")
            print()
    else:
        print(f"Execution plan for epic '{args.epic}' ({len(tasks)} tasks):\n")
        flattened: list[str] = []
        for i, layer in enumerate(layers):
            names = ", ".join(f"{tid} ({tasks[tid]['priority']})" for tid in layer)
            parallel_note = "  -- could run in parallel" if len(layer) > 1 else ""
            print(f"Layer {i}: {names}{parallel_note}")
            flattened.extend(layer)

    flattened_all: list[str] = []
    for layer in layers:
        flattened_all.extend(layer)

    print("\nFlattened sequential order:")
    for i, task_id in enumerate(flattened_all, start=1):
        task = tasks[task_id]
        print(f"  {i}. {task_id} - {task['title']} [{task['priority']}, {task['status']}]")

    soft_notes = {tid: t["soft_notes"] for tid, t in tasks.items() if t["soft_notes"]}
    if soft_notes:
        print("\nManual review advised (not parsed as hard blockers):")
        for task_id, notes in soft_notes.items():
            for note in notes:
                print(f"  {task_id}: {note}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
