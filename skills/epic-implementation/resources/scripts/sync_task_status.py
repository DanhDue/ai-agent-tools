#!/usr/bin/env python3
"""Mirror one epic task's Kanban status across every checkout of this repo.

`epic-implementation` runs an epic inside an isolated worktree, but the same
task files are also checked out in the main workspace -- and `epic-designer`
writes each task twice, into `.devtool/features/` and into
`.devtool/epic/<epic_dir>/`. Writing a status to only one of those four copies
leaves every other Kanban board stale for the whole epic.

This script writes them all:

    sync_task_status.py task <task_id> <status>
    sync_task_status.py epic <epic_dir> <status>

`task` mode rewrites `status`, `modified`, and -- on `done` -- `completedAt` in
the frontmatter of every copy of that task, in every checkout `git worktree
list` reports. `epic` mode rewrites the Meta Data `Status` line of the Epic
Overview's `.en.md` and `.vi.md` together, so the pair can never diverge.

Only matched lines change; every other key and the whole document body survive
byte-for-byte. Frontmatter is parsed with the same hand-rolled regex idiom as
compute_execution_order.py -- deliberately no PyYAML, so this stays stdlib-only.
"""
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

TASK_STATUSES = ("backlog", "todo", "in-progress", "review", "done")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def now_iso() -> str:
    """UTC, seconds precision, Zulu suffix -- e.g. 2026-09-14T10:23:45Z."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_frontmatter(text: str) -> dict:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"')
    return fields


def set_frontmatter_field(text: str, key: str, value: str | None) -> str:
    """Set `key: "value"` or `key: null` inside the leading frontmatter block only.

    A key that is absent is inserted directly after `status:`, so task files
    written before this script existed (no `modified`, no `completedAt`) keep
    working instead of silently losing the field. Body text is never scanned.
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        return text
    block = match.group(1)
    if value is None or value == "null":
        new_line = f"{key}: null"
    else:
        new_line = f'{key}: "{value}"'
    key_re = re.compile(rf"^{re.escape(key)}\s*:.*$", re.M)
    if key_re.search(block):
        new_block = key_re.sub(lambda _m: new_line, block, count=1)
    else:
        status_re = re.compile(r"^status\s*:.*$", re.M)
        if status_re.search(block):
            new_block = status_re.sub(lambda m: m.group(0) + "\n" + new_line, block, count=1)
        else:
            new_block = block + "\n" + new_line
    return text[:match.start(1)] + new_block + text[match.end(1):]


def parse_worktree_list(output: str) -> list[Path]:
    """Extract checkout roots from `git worktree list --porcelain` output.

    Git always reports the main worktree first, and callers rely on that
    ordering -- Phase 4's main-checkout restore uses roots[0]. Paths may
    contain spaces, so take everything after the first token.
    """
    return [Path(line[len("worktree "):]) for line in output.splitlines()
            if line.startswith("worktree ")]


def checkout_roots() -> list[Path]:
    """Every checkout of this repo, main worktree first.

    The only subprocess boundary in this module -- everything else is pure and
    directly testable, which is why the test suite needs no git fixtures.
    """
    result = subprocess.run(["git", "worktree", "list", "--porcelain"],
                            capture_output=True, text=True, check=True)
    return parse_worktree_list(result.stdout)


def task_targets(root: Path, task_id: str) -> list[Path]:
    """Every copy of one task inside one checkout: features, features/done, + each epic dir."""
    candidates = [
        root / ".devtool" / "features" / f"{task_id}.md",
        root / ".devtool" / "features" / "done" / f"{task_id}.md",
    ]
    candidates.extend(sorted((root / ".devtool" / "epic").glob(f"*/{task_id}.md")))
    return [path for path in candidates if path.is_file()]


def epic_of(path: Path) -> str | None:
    return parse_frontmatter(path.read_text()).get("epic")


def expected_epic(roots: list[Path], task_id: str) -> str | None:
    """The epic this task_id belongs to, per the authoritative features copy (or epic copy if archived).

    Task ids are `task_<number>_<name>`, so a name like `task_1_setup` can
    plausibly exist under two different epics -- and `task_targets`' `*/` glob
    would match both. Callers use this value to refuse any copy whose own
    `epic:` differs. Checked main-worktree-first; mirrors cannot disagree.
    """
    for root in roots:
        for features_dir in (root / ".devtool" / "features", root / ".devtool" / "features" / "done"):
            features = features_dir / f"{task_id}.md"
            if features.is_file():
                return epic_of(features)
        for epic_copy in sorted((root / ".devtool" / "epic").glob(f"*/{task_id}.md")):
            if epic_copy.is_file():
                return epic_of(epic_copy)
    return None


def sync_task(roots: list[Path], task_id: str, new_status: str) -> tuple[list[Path], list[str]]:
    """Synchronize a task's status across all checkout roots."""
    exp_epic = expected_epic(roots, task_id)
    written: list[Path] = []
    notes: list[str] = []
    now = now_iso()

    for root in roots:
        targets = task_targets(root, task_id)
        for path in targets:
            file_epic = epic_of(path)
            if exp_epic and file_epic and file_epic != exp_epic:
                notes.append(f"Skipped {path}: belongs to epic '{file_epic}', expected '{exp_epic}'")
                continue
            text = path.read_text()
            text = set_frontmatter_field(text, "status", new_status)
            text = set_frontmatter_field(text, "modified", now)
            if new_status == "done":
                text = set_frontmatter_field(text, "completedAt", now)
            else:
                fm = parse_frontmatter(text)
                if "completedAt" in fm and fm["completedAt"] != "null":
                    text = set_frontmatter_field(text, "completedAt", "null")
            path.write_text(text)
            written.append(path)

    return written, notes


def board_tally(roots: list[Path], epic_slug: str) -> dict[str, int]:
    """Tally task counts per status for the given epic, counting each task once."""
    tally = {status: 0 for status in TASK_STATUSES}
    seen_tasks: set[str] = set()
    for root in roots:
        search_dirs = [
            root / ".devtool" / "features",
            root / ".devtool" / "features" / "done",
        ]
        search_dirs.extend(sorted((root / ".devtool" / "epic").glob("*")))
        for features_dir in search_dirs:
            if not features_dir.is_dir():
                continue
            for path in sorted(features_dir.glob("task_*.md")):
                task_id = path.stem
                if task_id in seen_tasks:
                    continue
                fm = parse_frontmatter(path.read_text())
                if fm.get("epic") == epic_slug:
                    seen_tasks.add(task_id)
                    status = fm.get("status")
                    if status in tally:
                        tally[status] += 1
    return tally


def find_epic_slug(root: Path, epic_dir: str) -> str | None:
    """Find the epic slug from the epic's HLD overview or contained tasks."""
    epic_path = root / ".devtool" / "epic" / epic_dir
    if not epic_path.is_dir():
        return None
    for ext in (".en.md", ".vi.md"):
        doc = epic_path / f"{epic_dir}{ext}"
        if doc.is_file():
            match = re.search(r"^-\s*\*\*(?:Epic)\*\*:\s*(.+)$", doc.read_text(), re.M)
            if match:
                return match.group(1).strip()
    for task_file in sorted(epic_path.glob("task_*.md")):
        slug = epic_of(task_file)
        if slug:
            return slug
    return None


def find_epic_dir_for_slug(root: Path, epic_slug: str) -> str | None:
    """Find the epic directory name matching the given epic slug."""
    epics_parent = root / ".devtool" / "epic"
    if not epics_parent.is_dir():
        return None
    for sub in sorted(epics_parent.iterdir()):
        if not sub.is_dir():
            continue
        slug = find_epic_slug(root, sub.name)
        if slug == epic_slug:
            return sub.name
    # Fallback to name heuristic: replace hyphens with underscores
    candidate = epic_slug.replace("-", "_")
    if (epics_parent / candidate).is_dir():
        return candidate
    return None



def fix_task_markdown_links(text: str, epic_dir: str) -> str:
    """Rewrite task links when relocated into .devtool/epic/<epic_dir>/."""
    text = re.sub(rf"\]\(\.\./epic/{re.escape(epic_dir)}/([^)]+)\)", r"](\1)", text)
    text = re.sub(r"\]\(\.\./\.\./features/(?:done/)?(task_[^)]+\.md)\)", r"](\1)", text)
    return text


def fix_epic_overview_links(text: str) -> str:
    """Rewrite Section 8 links in <epic_dir>.en.md / .vi.md to local task_*.md."""
    return re.sub(r"\]\(\.\./\.\./features/(?:done/)?(task_[^)]+\.md)\)", r"](\1)", text)


def archive_superpowers_docs(root: Path, epic_dir: str, epic_slug: str | None) -> list[Path]:
    """Relocate any specs or plans matching this epic from docs/superpowers/ to the epic dir."""
    moved: list[Path] = []
    dest_dir = root / ".devtool" / "epic" / epic_dir
    if not dest_dir.is_dir():
        return moved
    patterns = {epic_dir}
    if epic_slug:
        patterns.add(epic_slug)
        patterns.add(epic_slug.replace("-", "_"))
        patterns.add(epic_slug.replace("_", "-"))

    for sub in ("plans", "specs"):
        sp_dir = root / "docs" / "superpowers" / sub
        if not sp_dir.is_dir():
            continue
        for f in sorted(sp_dir.glob("*.md")):
            if any(pat in f.name for pat in patterns):
                dest_file = dest_dir / f.name
                if not dest_file.exists():
                    f.rename(dest_file)
                    moved.append(dest_file)
                else:
                    f.unlink()
                    moved.append(dest_file)
        non_keep = [f for f in sp_dir.iterdir() if f.name != ".gitkeep"]
        if not non_keep:
            (sp_dir / ".gitkeep").touch()
    return moved


def archive_epic_tasks(roots: list[Path], epic_dir: str) -> tuple[list[Path], list[Path]]:
    """Move all done tasks of an epic from features/done into .devtool/epic/<epic_dir>/,

    clean up source files, rewrite links to local format, and retain .gitkeep.
    Returns (archived_files, cleaned_source_files).
    """
    archived: list[Path] = []
    cleaned: list[Path] = []

    for root in roots:
        dest_dir = root / ".devtool" / "epic" / epic_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        epic_slug = find_epic_slug(root, epic_dir)

        # 1. Relocate task files from features and features/done
        for fdir in (root / ".devtool" / "features", root / ".devtool" / "features" / "done"):
            if not fdir.is_dir():
                continue
            for task_file in sorted(fdir.glob("task_*.md")):
                file_epic = epic_of(task_file)
                if epic_slug and file_epic and file_epic != epic_slug:
                    continue
                dest_file = dest_dir / task_file.name
                content = task_file.read_text()
                content = fix_task_markdown_links(content, epic_dir)
                dest_file.write_text(content)
                archived.append(dest_file)
                task_file.unlink()
                cleaned.append(task_file)

        # 2. Ensure existing tasks in dest_dir have clean links
        for task_file in sorted(dest_dir.glob("task_*.md")):
            content = task_file.read_text()
            fixed = fix_task_markdown_links(content, epic_dir)
            if fixed != content:
                task_file.write_text(fixed)
                if task_file not in archived:
                    archived.append(task_file)

        # 3. Fix Section 8 links in epic overview documents (.en.md and .vi.md)
        for ext in (".en.md", ".vi.md"):
            doc = dest_dir / f"{epic_dir}{ext}"
            if doc.is_file():
                doc_content = doc.read_text()
                fixed_doc = fix_epic_overview_links(doc_content)
                if fixed_doc != doc_content:
                    doc.write_text(fixed_doc)

        # 4. Relocate superpowers specs & plans if any exist for this epic
        archive_superpowers_docs(root, epic_dir, epic_slug)

        # 5. Ensure .gitkeep exists in features/done if directory is empty
        done_dir = root / ".devtool" / "features" / "done"
        if done_dir.is_dir():
            non_keep = [f for f in done_dir.iterdir() if f.name != ".gitkeep"]
            if not non_keep:
                (done_dir / ".gitkeep").touch()

    return archived, cleaned


def sync_epic(roots: list[Path], epic_dir: str, new_status: str) -> tuple[list[Path], list[Path]]:
    """Update Status line in Meta Data for both .en.md and .vi.md across all checkouts.

    Returns (matched_docs, written_docs).
    """
    matched: list[Path] = []
    written: list[Path] = []
    status_re = re.compile(r"^(-\s*\*\*(?:Status|Trạng thái)\*\*:\s*).*$", re.M)
    for root in roots:
        epic_path = root / ".devtool" / "epic" / epic_dir
        if not epic_path.is_dir():
            continue
        for ext in (".en.md", ".vi.md"):
            doc = epic_path / f"{epic_dir}{ext}"
            if not doc.is_file():
                continue
            matched.append(doc)
            text = doc.read_text()
            if status_re.search(text):
                new_text = status_re.sub(rf"\g<1>{new_status}", text)
                if new_text != text:
                    doc.write_text(new_text)
                written.append(doc)

    if new_status.strip().lower() in ("done", "hoàn thành"):
        archive_epic_tasks(roots, epic_dir)

    return matched, written


def archive_all_done_epics(roots: list[Path]) -> list[str]:
    """Find all completed tasks in .devtool/features/done/ and archive them into their epics.

    Returns the list of epic_dirs that were archived and marked Done.
    """
    epics_to_archive: set[str] = set()
    for root in roots:
        done_dir = root / ".devtool" / "features" / "done"
        if not done_dir.is_dir():
            continue
        for task_file in sorted(done_dir.glob("task_*.md")):
            slug = epic_of(task_file)
            if slug:
                epic_dir = find_epic_dir_for_slug(root, slug)
                if epic_dir:
                    epics_to_archive.add(epic_dir)

    archived_dirs: list[str] = []
    for epic_dir in sorted(epics_to_archive):
        sync_epic(roots, epic_dir, "Done")
        archived_dirs.append(epic_dir)

    return archived_dirs


def main() -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Mirror one epic task's Kanban status across every checkout of this repo."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    task_parser = subparsers.add_parser("task", help="Sync task status")
    task_parser.add_argument("task_id", help="Task ID (e.g. task_1_setup)")
    task_parser.add_argument("status", help=f"New status ({', '.join(TASK_STATUSES)})")

    epic_parser = subparsers.add_parser("epic", help="Sync epic overview status")
    epic_parser.add_argument("epic_dir", help="Epic directory name (e.g. logging_refactor)")
    epic_parser.add_argument("status", help="New status string (e.g. 'In Progress')")

    archive_parser = subparsers.add_parser(
        "archive-epic", help="Archive done tasks of an epic into .devtool/epic/<epic_dir>/"
    )
    archive_parser.add_argument("epic_dir", help="Epic directory name (e.g. logging_refactor)")

    archive_done_parser = subparsers.add_parser(
        "archive-done",
        help="Find all completed tasks in .devtool/features/done/ and archive them into their respective epic directories",
    )

    args = parser.parse_args()

    if args.command == "task":
        if args.status not in TASK_STATUSES:
            sys.stderr.write(
                f"Invalid status '{args.status}'. Expected one of: {', '.join(TASK_STATUSES)}\n"
            )
            sys.exit(2)

        roots = checkout_roots()
        written, notes = sync_task(roots, args.task_id, args.status)
        for note in notes:
            sys.stderr.write(f"Note: {note}\n")

        if not written:
            sys.stderr.write(f"Warning: No copies of task '{args.task_id}' found in any checkout.\n")
            sys.exit(1)

        exp_epic = expected_epic(roots, args.task_id)
        if exp_epic:
            tally = board_tally(roots, exp_epic)
            tally_str = ", ".join(f"{k}: {v}" for k, v in tally.items())
            print(
                f"Updated {len(written)} copies of {args.task_id} -> '{args.status}' "
                f"[Epic '{exp_epic}': {tally_str}]"
            )
        else:
            print(f"Updated {len(written)} copies of {args.task_id} -> '{args.status}'")

    elif args.command == "epic":
        roots = checkout_roots()
        matched, written = sync_epic(roots, args.epic_dir, args.status)
        if not matched:
            sys.stderr.write(f"Warning: No epic docs found for '{args.epic_dir}'.\n")
            sys.exit(1)
        print(f"Synchronized {len(matched)} epic docs for '{args.epic_dir}' -> '{args.status}'")

    elif args.command == "archive-epic":
        roots = checkout_roots()
        archived, cleaned = archive_epic_tasks(roots, args.epic_dir)
        print(
            f"Archived {len(archived)} tasks into .devtool/epic/{args.epic_dir} "
            f"(cleaned {len(cleaned)} from features)"
        )

    elif args.command == "archive-done":
        roots = checkout_roots()
        archived = archive_all_done_epics(roots)
        if archived:
            print(f"Archived {len(archived)} epic(s) into .devtool/epic/: {', '.join(archived)}")
        else:
            print("No completed tasks to archive.")



if __name__ == "__main__":
    main()


