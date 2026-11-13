#!/usr/bin/env python3
from __future__ import annotations

"""Mirror one epic task's Kanban status across every checkout of this repo.

`dev-implementation` runs an epic inside an isolated worktree, but the same
task files are also checked out in the main workspace -- and `dev-designer`
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
import sys
from datetime import datetime, timezone
from collections.abc import Callable, Sequence

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc  # type: ignore[attr-defined]
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_KIT_SCRIPTS_DIR = Path(__file__).resolve().parents[4] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
if str(_KIT_SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(_KIT_SCRIPTS_DIR))

import _state_envelope
from check_bdd_traceability import (
    COVERS_LINE,
    FENCE,
    ID_SHAPE,
    ID_TOKEN,
    LEADING_TAG,
    SCENARIO_LINE,
)
import resume_context
from slug_utils import parse_frontmatter, sanitize_slug
import task_contract as tc

TASK_STATUSES = ("backlog", "todo", "in-progress", "review", "done")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
TASK_FILE_PATTERN = re.compile(r"^task_[0-9]+.*\.md$")


def is_task_file(path: Path) -> bool:
    """Return True if path is a task file (e.g. task_01_name.md), excluding epic overview docs."""
    return bool(TASK_FILE_PATTERN.match(path.name)) and not path.name.endswith(
        (".en.md", ".vi.md")
    )


def task_files_in(directory: Path) -> list[Path]:
    """List sorted task files in directory matching task_[0-9]+.*.md, ignoring overview docs."""
    if not directory.is_dir():
        return []
    return [p for p in sorted(directory.glob("task_*.md")) if is_task_file(p)]


def transform_outside_code(text: str, fn: Callable[[str], str]) -> str:
    """Apply fn to text outside fenced code blocks and inline code spans."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    non_fence_chunk: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0

    fence_open_re = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})")
    fence_close_re = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})\s*$")

    def flush_non_fence() -> None:
        if non_fence_chunk:
            chunk = "".join(non_fence_chunk)
            out.append(_transform_outside_inline_spans(chunk, fn))
            non_fence_chunk.clear()

    for line in lines:
        if not in_fence:
            m = fence_open_re.match(line)
            if m:
                flush_non_fence()
                in_fence = True
                fence_char = m.group(1)[0]
                fence_len = len(m.group(1))
                out.append(line)
            else:
                non_fence_chunk.append(line)
        else:
            m = fence_close_re.match(line)
            if m and m.group(1)[0] == fence_char and len(m.group(1)) >= fence_len:
                in_fence = False
            out.append(line)

    flush_non_fence()
    return "".join(out)


def _transform_outside_inline_spans(chunk: str, fn: Callable[[str], str]) -> str:
    result: list[str] = []
    last_end = 0
    for m in re.finditer(r"(`+)([\s\S]*?)\1", chunk):
        start, end = m.span()
        if start > last_end:
            result.append(fn(chunk[last_end:start]))
        result.append(m.group(0))
        last_end = end
    if last_end < len(chunk):
        result.append(fn(chunk[last_end:]))
    return "".join(result)


def now_iso() -> str:
    """UTC, seconds precision, Zulu suffix -- e.g. 2026-09-14T10:23:45Z."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


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
    key_re = re.compile(rf"^{re.escape(key)}\s*:.*$", re.MULTILINE)
    if key_re.search(block):
        new_block = key_re.sub(lambda _m: new_line, block, count=1)
    else:
        status_re = re.compile(r"^status\s*:.*$", re.MULTILINE)
        if status_re.search(block):
            new_block = status_re.sub(
                lambda m: m.group(0) + "\n" + new_line, block, count=1
            )
        else:
            new_block = block + "\n" + new_line
    return text[: match.start(1)] + new_block + text[match.end(1) :]


def parse_worktree_list(output: str) -> list[Path]:
    """Extract checkout roots from `git worktree list --porcelain` output.

    Git always reports the main worktree first, and callers rely on that
    ordering -- Phase 4's main-checkout restore uses roots[0]. Paths may
    contain spaces, so take everything after the first token.
    """
    return [
        Path(line[len("worktree ") :])
        for line in output.splitlines()
        if line.startswith("worktree ")
    ]


def parse_worktree_branches(output: str) -> list[tuple[Path, str | None]]:
    """Extract (path, branch) pairs from `git worktree list --porcelain` output.

    Branch is the full ref string (e.g. 'refs/heads/epic/name') or None if detached.
    """
    entries: list[tuple[Path, str | None]] = []
    current_path: Path | None = None
    current_branch: str | None = None

    for line in output.splitlines():
        if line.startswith("worktree "):
            if current_path is not None:
                entries.append((current_path, current_branch))
            current_path = Path(line[len("worktree ") :])
            current_branch = None
        elif line.startswith("branch "):
            current_branch = line[len("branch ") :]
        elif line == "detached":
            current_branch = None

    if current_path is not None:
        entries.append((current_path, current_branch))

    return entries


_SLOT_WORKTREE_RE = re.compile(r"-slot-\d+$")


def _is_slot_worktree(path: Path) -> bool:
    """Return True if path is an ephemeral parallel worker pool slot worktree."""
    return path.parent.name == ".worktrees" and bool(_SLOT_WORKTREE_RE.search(path.name))


def _current_checkout_root() -> Path | None:
    """Return current git top-level checkout path, or None if unavailable."""
    res = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode == 0 and res.stdout.strip():
        return Path(res.stdout.strip())
    return None


def checkout_roots() -> list[Path]:
    """Every non-slot checkout of this repo, main worktree first."""
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [p for p in parse_worktree_list(result.stdout) if not _is_slot_worktree(p)]


def epic_checkout_roots(epic_dir: str) -> list[Path]:
    """Return the current checkout root plus every worktree on branch refs/heads/epic/<epic_slug>.

    Current checkout is always first. Other worktrees are included only if their branch
    matches this epic's slug.
    """
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    current_root = Path(top.stdout.strip())

    wt_result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    entries = parse_worktree_branches(wt_result.stdout)

    slug = find_epic_slug(current_root, epic_dir) or epic_dir
    target_branch = f"refs/heads/epic/{slug}"

    roots: list[Path] = [current_root]
    seen = {current_root.resolve()}

    for path, branch in entries:
        if branch == target_branch:
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                roots.append(path)

    return roots


def task_targets(root: Path, task_id: str) -> list[Path]:
    """Every copy of one task inside one checkout: features, features/done, + each epic dir."""
    candidates = [
        root / ".devtool" / "features" / f"{task_id}.md",
        root / ".devtool" / "features" / "done" / f"{task_id}.md",
    ]
    candidates.extend(sorted((root / ".devtool" / "epic").glob(f"*/{task_id}.md")))
    return [path for path in candidates if path.is_file()]


def epic_of(path: Path) -> str | None:
    val = parse_frontmatter(path.read_text()).get("epic")
    return sanitize_slug(val) if val else None


def expected_epic(roots: list[Path], task_id: str) -> str | None:
    """The epic this task_id belongs to, per the authoritative features copy (or epic copy if archived).

    Task ids are `task_<number>_<name>`, so a name like `task_1_setup` can
    plausibly exist under two different epics -- and `task_targets`' `*/` glob
    would match both. Callers use this value to refuse any copy whose own
    `epic:` differs. Checked main-worktree-first; mirrors cannot disagree.
    """
    for root in roots:
        for features_dir in (
            root / ".devtool" / "features",
            root / ".devtool" / "features" / "done",
        ):
            features = features_dir / f"{task_id}.md"
            if features.is_file():
                return epic_of(features)
        for epic_copy in sorted((root / ".devtool" / "epic").glob(f"*/{task_id}.md")):
            if epic_copy.is_file():
                return epic_of(epic_copy)
    return None


def _collect_epic_task_summary(
    roots: Sequence[Path], epic_slug: str
) -> tuple[dict[str, int], list[str], str | None]:
    """Return `(tally, active_task_ids, next_todo_id)` across `roots` for `epic_slug`."""
    tally = board_tally(list(roots), epic_slug)
    active_tasks: list[str] = []
    next_todo: str | None = None
    seen_tasks: set[str] = set()
    for root in roots:
        search_dirs = [
            root / ".devtool" / "features",
            root / ".devtool" / "features" / "done",
        ]
        search_dirs.extend(sorted((root / ".devtool" / "epic").glob("*")))
        for directory in search_dirs:
            if not directory.is_dir():
                continue
            for path in task_files_in(directory):
                task_id = path.stem
                if task_id in seen_tasks:
                    continue
                fm = parse_frontmatter(path.read_text(encoding="utf-8"))
                if fm.get("epic") != epic_slug:
                    continue
                seen_tasks.add(task_id)
                status = fm.get("status")
                if status in ("in-progress", "review"):
                    active_tasks.append(task_id)
                elif status == "todo" and next_todo is None:
                    next_todo = task_id
    return tally, active_tasks, next_todo


def _extract_existing_decisions(state_md: Path) -> str:
    """Extract existing locked decision bullets from `.devtool/state/<epic>.md`."""
    if not state_md.is_file():
        return ""
    lines = state_md.read_text(encoding="utf-8").splitlines()
    captured: list[str] = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped == "## Recent Decisions Locked:":
            in_section = True
            continue
        if in_section:
            if stripped.startswith("## "):
                break
            if stripped and stripped != "- Initialized state snapshot":
                captured.append(stripped)
    return "\n".join(captured)


def _sync_runtime_envelope_and_memory(
    active_roots: Sequence[Path],
    epic_slug: str,
    *,
    stage: str,
    last_event: str,
    clear_decision: bool,
) -> None:
    """Atomically refresh heartbeat JSON, clear owned decision, and sync Two-Tier Memory."""
    if not active_roots or not epic_slug:
        return
    anchor = active_roots[0]
    safe_slug = _state_envelope._sanitize_epic_slug(epic_slug)
    hb_filename = f"{safe_slug}.heartbeat.json"

    target_devtool_dirs: list[Path] = []
    seen_dt: set[Path] = set()

    def _add_dt(devtool_dir: Path) -> None:
        resolved = devtool_dir.resolve()
        if resolved not in seen_dt:
            seen_dt.add(resolved)
            target_devtool_dirs.append(resolved)

    if (anchor / ".git").exists():
        for shared_dt in _state_envelope.resolve_shared_devtool_dirs(anchor):
            _add_dt(shared_dt)
        primary_root = target_devtool_dirs[0].parent
        for mirror_dt in _state_envelope._discover_active_mirror_dirs(
            primary_root, hb_filename
        ):
            _add_dt(mirror_dt)
    for root in active_roots:
        if (root / ".devtool").is_dir():
            _add_dt(root / ".devtool")
    if not target_devtool_dirs:
        _add_dt(anchor / ".devtool")

    summary_roots = list(dict.fromkeys([d.parent for d in target_devtool_dirs] + list(active_roots)))
    tally, active_tasks, next_todo = _collect_epic_task_summary(summary_roots, epic_slug)

    _state_envelope.update_epic_heartbeat(
        anchor,
        epic_slug,
        stage=stage,
        active_tasks=active_tasks,
        last_event=last_event,
        tally=tally,
        extra_devtool_dirs=target_devtool_dirs,
    )
    if clear_decision:
        _state_envelope.clear_pending_decision(
            anchor,
            epic_slug,
            extra_devtool_dirs=target_devtool_dirs,
        )

    tally_str = ", ".join(f"{k}: {v}" for k, v in tally.items() if v > 0) or "empty"
    status_line = f"{stage} [{tally_str}]"
    if active_tasks:
        next_step = f"Continue {active_tasks[0]}"
    elif next_todo:
        next_step = f"Start {next_todo}"
    else:
        next_step = "Verify epic completion"

    decisions_text = ""
    for dt_dir in target_devtool_dirs:
        decisions_text = _extract_existing_decisions(dt_dir / "state" / f"{epic_slug}.md")
        if decisions_text:
            break
    if not decisions_text:
        decisions_text = f"- {last_event}"

    resume_context.write_epic_state(
        target_devtool_dirs[0].parent,
        epic_slug,
        decisions=decisions_text,
        status=status_line,
        next_step=next_step,
        refresh_heartbeat=False,
        sync_title=False,
        mirror_roots=[d.parent for d in target_devtool_dirs],
    )


def sync_task(
    roots: list[Path], task_id: str, new_status: str
) -> tuple[list[Path], list[str]]:
    """Synchronize a task's status across all checkout roots."""
    exp_epic = expected_epic(roots, task_id)
    written: list[Path] = []
    notes: list[str] = []
    touched_roots: list[Path] = []
    now = now_iso()

    for root in roots:
        targets = task_targets(root, task_id)
        root_wrote = False
        for path in targets:
            file_epic = epic_of(path)
            if exp_epic and file_epic and file_epic != exp_epic:
                notes.append(
                    f"Skipped {path}: belongs to epic '{file_epic}', expected '{exp_epic}'"
                )
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
            written.append(board_location(root, path, new_status))
            root_wrote = True
        if root_wrote:
            touched_roots.append(root)

    if written and exp_epic and touched_roots:
        _sync_runtime_envelope_and_memory(
            touched_roots,
            exp_epic,
            stage=f"Stage 3 ({new_status}: {task_id})",
            last_event=f"sync_task {task_id} -> {new_status}",
            clear_decision=new_status in ("in-progress", "done"),
        )

    return written, notes


def board_location(root: Path, path: Path, status: str) -> Path:
    """Move a features copy into features/done when it becomes done, and back when it leaves done.

    Epic mirrors stay put. A copy already at the target is replaced by the one just written.
    """
    features = root / ".devtool" / "features"
    content = path.read_text(encoding="utf-8")
    if status == "done" and path.parent == features:
        target = features / "done" / path.name
        content = transform_outside_code(
            content,
            lambda t: re.sub(r"\]\(\.\./epic/", r"](../../epic/", t),
        )
    elif status != "done" and path.parent == features / "done":
        target = features / path.name
        content = transform_outside_code(
            content,
            lambda t: re.sub(r"\]\(\.\./\.\./epic/", r"](../epic/", t),
        )
    else:
        return path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    if path != target and path.exists():
        path.unlink()
    return target


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
            for path in task_files_in(features_dir):
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
            match = re.search(
                r"^-\s*\*\*(?:Epic)\*\*:\s*(.+)$", doc.read_text(), re.MULTILINE
            )
            if match:
                slug = sanitize_slug(match.group(1))
                if slug:
                    return slug
    for task_file in task_files_in(epic_path):
        slug = epic_of(task_file)
        if slug:
            return slug
    return sanitize_slug(epic_dir)


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

    def _fix(t: str) -> str:
        t = re.sub(
            r"\]\((?:\.\./)+epic/" + re.escape(epic_dir) + r"/([^)]+)\)", r"](\1)", t
        )
        t = re.sub(r"\]\(\.\./\.\./features/(?:done/)?(task_[^)]+\.md)\)", r"](\1)", t)
        return t

    return transform_outside_code(text, _fix)


def fix_epic_overview_links(text: str) -> str:
    """Rewrite Section 8 links in <epic_dir>.en.md / .vi.md to local task_*.md."""
    return re.sub(
        r"\]\(\.\./\.\./features/(?:done/)?(task_[^)]+\.md)\)", r"](\1)", text
    )


def archive_superpowers_docs(
    root: Path, epic_dir: str, epic_slug: str | None
) -> list[Path]:
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


def archive_epic_tasks(
    roots: list[Path], epic_dir: str
) -> tuple[list[Path], list[Path]]:
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
        for fdir in (
            root / ".devtool" / "features",
            root / ".devtool" / "features" / "done",
        ):
            if not fdir.is_dir():
                continue
            for task_file in task_files_in(fdir):
                file_epic = epic_of(task_file)
                target_slug = epic_slug or sanitize_slug(epic_dir) or epic_dir
                target_slugs = {
                    target_slug,
                    target_slug.replace("-", "_"),
                    target_slug.replace("_", "-"),
                }
                if file_epic and file_epic not in target_slugs:
                    continue
                dest_file = dest_dir / task_file.name
                if dest_file.exists():
                    mirror_fm = parse_frontmatter(task_file.read_text(encoding="utf-8"))
                    canonical_text = dest_file.read_text(encoding="utf-8")
                    for field in ("status", "modified", "completedAt"):
                        if field in mirror_fm:
                            canonical_text = set_frontmatter_field(
                                canonical_text, field, str(mirror_fm[field])
                            )
                    canonical_text = fix_task_markdown_links(canonical_text, epic_dir)
                    dest_file.write_text(canonical_text, encoding="utf-8")
                else:
                    content = task_file.read_text(encoding="utf-8")
                    content = fix_task_markdown_links(content, epic_dir)
                    dest_file.write_text(content, encoding="utf-8")
                archived.append(dest_file)
                task_file.unlink()
                cleaned.append(task_file)

        # 2. Ensure existing tasks in dest_dir have clean links
        for task_file in task_files_in(dest_dir):
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


def sync_epic(
    roots: list[Path], epic_dir: str, new_status: str
) -> tuple[list[Path], list[Path]]:
    """Update Status line in Meta Data for both .en.md and .vi.md across all checkouts.

    Returns (matched_docs, written_docs).
    """
    matched: list[Path] = []
    written: list[Path] = []
    touched_roots: list[Path] = []
    status_re = re.compile(
        r"^(-\s*\*\*(?:Status|Trạng thái)(?:\*\*:\s*|:\*\*\s*)).*$", re.MULTILINE
    )
    for root in roots:
        epic_path = root / ".devtool" / "epic" / epic_dir
        if not epic_path.is_dir():
            continue
        root_matched = False
        for ext in (".en.md", ".vi.md"):
            doc = epic_path / f"{epic_dir}{ext}"
            if not doc.is_file():
                continue
            matched.append(doc)
            root_matched = True
            text = doc.read_text()
            if status_re.search(text):
                new_text = status_re.sub(rf"\g<1>{new_status}", text)
                if new_text != text:
                    doc.write_text(new_text)
                written.append(doc)
        if root_matched:
            touched_roots.append(root)

    if new_status.strip().lower() in ("done", "hoàn thành"):
        archive_epic_tasks(roots, epic_dir)

    if matched and touched_roots:
        epic_slug = next(
            (slug for r in touched_roots if (slug := find_epic_slug(r, epic_dir))),
            None,
        )
        if epic_slug:
            norm_status = new_status.strip().lower()
            _sync_runtime_envelope_and_memory(
                touched_roots,
                epic_slug,
                stage=new_status,
                last_event=f"sync_epic {epic_dir} -> {new_status}",
                clear_decision=norm_status
                in ("in progress", "in-progress", "đang thực hiện", "done", "hoàn thành"),
            )

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
        for task_file in task_files_in(done_dir):
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


def code_epic_dir(root: Path, task_id: str) -> str | None:
    """The epic directory of this checkout's copy of the task when that epic is a code epic, else None."""
    from task_contract import is_code_epic

    for features in (
        root / ".devtool" / "features",
        root / ".devtool" / "features" / "done",
    ):
        if (features / f"{task_id}.md").is_file():
            slug = epic_of(features / f"{task_id}.md")
            epic_dir = find_epic_dir_for_slug(root, slug) if slug else None
            if epic_dir and is_code_epic(
                root / ".devtool" / "epic" / epic_dir / f"{epic_dir}.en.md"
            ):
                return epic_dir
            return None
    return None


def done_gate_failures(task_id: str) -> list[str]:
    """Messages refusing `task <id> done` for a code epic's task; empty when the gate does not apply or passes."""
    from task_contract import ContractError, evaluate_done_gate, section

    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if top.returncode != 0:
        return []
    root = Path(top.stdout.strip())
    epic_dir = code_epic_dir(root, task_id)
    if epic_dir is None:
        if any(
            code_epic_dir(other, task_id)
            for other in checkout_roots()
            if other.resolve() != root.resolve()
        ) and not task_targets(root, task_id):
            return [
                "run the done gate in the checkout that holds the task and its evidence (the epic worktree)"
            ]
        return []
    mirror = root / ".devtool" / "epic" / epic_dir / f"{task_id}.md"
    if (
        not mirror.is_file()
        or section(mirror.read_text(encoding="utf-8"), "Verification") is None
    ):
        return [
            (
                f"retrofit required: {mirror} has no Verification section — retrofit it through "
                "dev-designer's Updating an Existing Epic"
            )
        ]
    try:
        return evaluate_done_gate(mirror)
    except ContractError as error:
        return [f"condition 1: {error}"]


DIRECTIVE_RE = re.compile(
    r"(<!--\s*@@FILE:([^@\s>]+)@@\s*-->)\s*\n+(```+)([a-zA-Z0-9_-]*)\n[\s\S]*?\n\3",
    flags=re.MULTILINE,
)


def extract_scenario_blocks(text: str) -> dict[str, list[str]]:
    """Extract individual Gherkin scenario lines keyed by scenario ID."""
    blocks: dict[str, list[str]] = {}
    in_gherkin = False
    fence_marker: str | None = None
    current_id: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_id, current_lines
        if current_id is not None:
            while current_lines and not current_lines[-1].strip():
                current_lines.pop()
            if current_lines:
                blocks[current_id] = current_lines
            current_id = None
            current_lines = []

    for line in text.splitlines():
        fence_match = FENCE.match(line)
        if fence_match and fence_marker is None:
            fence_marker = fence_match.group(1)
            in_gherkin = fence_match.group(2).lower() == "gherkin"
            if not in_gherkin:
                flush()
            continue
        if (
            fence_match
            and fence_marker
            and fence_match.group(1)[0] == fence_marker[0]
            and len(fence_match.group(1)) >= len(fence_marker)
            and not fence_match.group(2)
        ):
            fence_marker = None
            in_gherkin = False
            flush()
            continue

        if not in_gherkin:
            continue

        sc_match = SCENARIO_LINE.match(line)
        if sc_match:
            flush()
            rest = sc_match.group(1).strip()
            tag = LEADING_TAG.match(rest)
            if tag and ID_SHAPE.fullmatch(tag.group(1)):
                current_id = tag.group(1)
                current_lines = [line.rstrip()]
            else:
                id_match = ID_TOKEN.search(rest)
                if id_match:
                    current_id = id_match.group(0)
                    current_lines = [line.rstrip()]
        elif current_id is not None:
            current_lines.append(line.rstrip())

    flush()
    return blocks


def inject_bdd_scenarios(task_text: str, canonical_blocks: dict[str, list[str]]) -> str:
    """Inject verbatim Gherkin scenario blocks matching Covers: into ### BDD SCENARIOS."""
    covers: list[str] = []
    for line in task_text.splitlines():
        m = COVERS_LINE.match(line)
        if m:
            covers.extend(ID_TOKEN.findall(m.group(1)))
    if not covers:
        return task_text

    missing = [c for c in covers if c not in canonical_blocks]
    if missing:
        raise ValueError(
            f"Covered scenario(s) missing from bdd_scenarios.en.md: {', '.join(missing)}"
        )

    scenario_blocks = ["\n".join(canonical_blocks[c]) for c in covers]
    gherkin_block = "```gherkin\n" + "\n\n".join(scenario_blocks) + "\n```"

    m_block = re.search(
        r"(### BDD SCENARIOS[\s\S]*?^Covers:[^\n]*\n+)(```[a-zA-Z0-9_-]*\n[\s\S]*?\n```)",
        task_text,
        flags=re.MULTILINE,
    )
    if m_block:
        start, end = m_block.span(2)
        return task_text[:start] + gherkin_block + task_text[end:]

    m_block2 = re.search(
        r"(^Covers:[^\n]*\n+)(```[a-zA-Z0-9_-]*\n[\s\S]*?\n```)",
        task_text,
        flags=re.MULTILINE,
    )
    if m_block2:
        start, end = m_block2.span(2)
        return task_text[:start] + gherkin_block + task_text[end:]

    m_covers = re.search(r"(^Covers:[^\n]*)(\n|$)", task_text, flags=re.MULTILINE)
    if m_covers:
        end = m_covers.end()
        return task_text[:end] + "\n\n" + gherkin_block + "\n" + task_text[end:]

    return task_text


def expand_embedded_files(text: str, source_root: Path) -> str:
    """Expand <!-- @@FILE:<rel_path>@@ --> by replacing the following fenced code block with file contents."""

    def replacer(m: re.Match[str]) -> str:
        directive = m.group(1)
        rel_path_str = m.group(2).strip()
        lang = m.group(4) or ""

        rel_path = Path(rel_path_str)
        if rel_path_str.startswith("/") or ".." in rel_path.parts:
            raise ValueError(
                f"Invalid embedded file path: {rel_path_str} (must be relative without '..')"
            )

        target = source_root / rel_path
        if not target.is_file():
            raise ValueError(
                f"Embedded file not found: {rel_path_str} (looked in {target})"
            )

        content = target.read_text(encoding="utf-8")
        runs = [len(run.group(0)) for run in re.finditer(r"`+", content)]
        max_inner = max(runs, default=0)
        fence_len = max(4, max_inner + 1) if max_inner >= 3 else 3
        fence_str = "`" * fence_len

        return f"{directive}\n{fence_str}{lang}\n{content.rstrip(chr(10))}\n{fence_str}"

    return DIRECTIVE_RE.sub(replacer, text)


def canonicalize_intra_epic_links(text: str, epic_path: Path) -> str:
    """Canonicalize [text](./sibling.md) -> [text](sibling.md) for files within epic_path."""

    def replacer(m: re.Match[str]) -> str:
        label = m.group(1)
        target = m.group(2)
        base_target = target.split("#", 1)[0].split("?", 1)[0]
        if (
            (epic_path / base_target).is_file()
            or (epic_path / f"{base_target}.md").is_file()
            or base_target.startswith("task_")
        ):
            return f"[{label}]({target})"
        return m.group(0)

    return transform_outside_code(
        text, lambda t: re.sub(r"\[([^\]]+)\]\(\./([^)]+)\)", replacer, t)
    )


def rewrite_mirror_links(
    text: str, epic_dir: str, is_done: bool, epic_path: Path
) -> str:
    """Rewrite local intra-epic links to cross-directory links for features/ or features/done/ mirrors."""
    prefix = f"../../epic/{epic_dir}/" if is_done else f"../epic/{epic_dir}/"
    canonical = fix_task_markdown_links(text, epic_dir)

    def replacer(m: re.Match[str]) -> str:
        label = m.group(1)
        target = m.group(2)
        if target.startswith(("http://", "https://", "/", "#", "mailto:", "../", "./")):
            return m.group(0)
        base_target = target.split("#", 1)[0].split("?", 1)[0]
        if (
            (epic_path / base_target).is_file()
            or (epic_path / f"{base_target}.md").is_file()
            or base_target.startswith("task_")
        ):
            return f"[{label}]({prefix}{target})"
        return m.group(0)

    return transform_outside_code(
        canonical, lambda t: re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replacer, t)
    )


def check_epic_prerequisites(root: Path, epic_dir: str) -> list[str]:
    """Check whether all prerequisite epics declared in HLD are Done."""
    hld_path = root / ".devtool" / "epic" / epic_dir / f"{epic_dir}.en.md"
    if not hld_path.is_file():
        hld_path = root / ".devtool" / "epic" / epic_dir / f"{epic_dir}.vi.md"
    if not hld_path.is_file():
        return [f"HLD overview not found for '{epic_dir}'"]

    hld_text = hld_path.read_text(encoding="utf-8")
    prereq_dirs, errors = tc.resolve_prerequisite_epic_dirs(root, hld_text, epic_dir)
    if errors:
        return list(errors)

    blockers: list[str] = []
    for p_dir in prereq_dirs:
        p_hld_path = root / ".devtool" / "epic" / p_dir / f"{p_dir}.en.md"
        if not p_hld_path.is_file():
            p_hld_path = root / ".devtool" / "epic" / p_dir / f"{p_dir}.vi.md"
        is_done = False
        if p_hld_path.is_file():
            p_hld_text = p_hld_path.read_text(encoding="utf-8")
            match = re.search(
                r"^-\s*\*\*(?:Status|Trạng thái)\*\*:\s*(.+)$",
                p_hld_text,
                re.MULTILINE,
            )
            if match:
                status_str = match.group(1).strip().strip("`").strip('"')
                if status_str.lower().startswith(("done", "hoàn thành")):
                    is_done = True
        if not is_done:
            p_tasks = task_files_in(root / ".devtool" / "epic" / p_dir)
            if p_tasks and all(
                parse_frontmatter(t.read_text(encoding="utf-8")).get("status") == "done"
                for t in p_tasks
            ):
                is_done = True
        if not is_done:
            blockers.append(f"prerequisite epic '{p_dir}' is not Done")

    return blockers


def check_epic_file_conflicts(root: Path, epic_dir: str) -> dict[str, list[str]]:
    """Check Allowed files overlaps between epic_dir and active tasks of other epics."""
    tasks = task_files_in(root / ".devtool" / "epic" / epic_dir)
    target_patterns: list[str] = []
    for t in tasks:
        t_text = t.read_text(encoding="utf-8")
        for entry in tc.parse_allowed_files(t_text):
            if entry.pattern not in target_patterns:
                target_patterns.append(entry.pattern)

    target_slug = find_epic_slug(root, epic_dir)
    features_dir = root / ".devtool" / "features"
    conflicts: dict[str, set[str]] = {}

    if features_dir.is_dir():
        for other_task in task_files_in(features_dir):
            other_text = other_task.read_text(encoding="utf-8")
            fm = parse_frontmatter(other_text)
            status = fm.get("status", "").lower()
            other_epic = fm.get("epic")
            if (
                status in ("todo", "in-progress", "in_progress", "review")
                and other_epic != target_slug
            ):
                for o_entry in tc.parse_allowed_files(other_text):
                    o_pat = o_entry.pattern
                    for t_pat in target_patterns:
                        if tc.path_matches(t_pat, o_pat) or tc.path_matches(
                            o_pat, t_pat
                        ):
                            conflicts.setdefault(
                                other_epic or "unknown", set()
                            ).add(t_pat)

    return {ep: sorted(pats) for ep, pats in sorted(conflicts.items())}


def promote_epic_tasks(
    roots: list[Path], epic_dir: str, *, force: bool = False
) -> tuple[list[Path], list[str]]:
    """Promote all backlog tasks of an epic across checkouts to todo."""
    if not roots:
        return ([], ["No repository roots found"])
    root = roots[0]

    if not force:
        prereq_blockers = check_epic_prerequisites(root, epic_dir)
        conflicts = check_epic_file_conflicts(root, epic_dir)
        if prereq_blockers or conflicts:
            errors: list[str] = list(prereq_blockers)
            for ep, pats in conflicts.items():
                errors.append(f"conflict with {ep}: {', '.join(pats)}")
            return ([], errors)

    epic_path = root / ".devtool" / "epic" / epic_dir
    if not epic_path.is_dir():
        return ([], [f"Epic directory not found: {epic_path}"])

    promoted_paths: list[Path] = []
    for t_file in task_files_in(epic_path):
        fm = parse_frontmatter(t_file.read_text(encoding="utf-8"))
        if fm.get("status") == "backlog":
            written, _ = sync_task(roots, t_file.stem, "todo")
            promoted_paths.extend(written)

    # Check and update HLD status if queued/backlog
    hld_file = epic_path / f"{epic_dir}.en.md"
    if not hld_file.is_file():
        hld_file = epic_path / f"{epic_dir}.vi.md"
    if hld_file.is_file():
        m = re.search(
            r"^-\s*\*\*(?:Status|Trạng thái)\*\*:\s*(.+)$",
            hld_file.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        if m:
            st_val = m.group(1).strip().strip("`").strip('"')
            if "backlog" in st_val.lower() or st_val.lower().startswith("queued"):
                today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                sync_epic(roots, epic_dir, f"Packaged ({today_iso})")

    return (promoted_paths, [])


def render_epic_tasks(
    root: Path, epic_dir: str, source_root: Path | None = None
) -> list[Path]:
    """Single-source task render engine: injects BDD, embeds files, and generates features mirrors."""
    epic_path = root / ".devtool" / "epic" / epic_dir
    if not epic_path.is_dir():
        raise ValueError(f"Epic directory not found: {epic_path}")

    source_root = source_root or root
    bdd_file = epic_path / "bdd_scenarios.en.md"
    canonical_blocks: dict[str, list[str]] = {}
    if bdd_file.is_file():
        canonical_blocks = extract_scenario_blocks(bdd_file.read_text(encoding="utf-8"))

    epic_slug = find_epic_slug(root, epic_dir) or sanitize_slug(epic_dir) or epic_dir
    target_slugs = {
        epic_slug,
        epic_slug.replace("-", "_"),
        epic_slug.replace("_", "-"),
        sanitize_slug(epic_dir),
    }

    # Phase 1: Validate and render in-memory across all tasks.
    # If any task fails validation (unknown scenario ID or missing embed file),
    # the function raises before mutating any canonical or mirror task file on disk.
    render_plan: list[tuple[Path, str, Path, Path, str]] = []
    for task_file in task_files_in(epic_path):
        task_text = task_file.read_text(encoding="utf-8")
        task_text = canonicalize_intra_epic_links(task_text, epic_path)
        task_text = expand_embedded_files(task_text, source_root)
        task_text = inject_bdd_scenarios(task_text, canonical_blocks)

        fm = parse_frontmatter(task_text)
        is_done = fm.get("status") == "done"

        mirror_dir = (
            root / ".devtool" / "features" / "done"
            if is_done
            else root / ".devtool" / "features"
        )
        other_dir = (
            root / ".devtool" / "features"
            if is_done
            else root / ".devtool" / "features" / "done"
        )

        mirror_path = mirror_dir / task_file.name
        other_path = other_dir / task_file.name
        mirror_text = rewrite_mirror_links(task_text, epic_dir, is_done, epic_path)
        render_plan.append((task_file, task_text, mirror_path, other_path, mirror_text))

    # Phase 2: Atomic write to disk only after all tasks pass Phase 1 validation.
    written_mirrors: list[Path] = []
    for task_file, task_text, mirror_path, other_path, mirror_text in render_plan:
        task_file.write_text(task_text, encoding="utf-8")
        if other_path.is_file():
            other_path.unlink()
        mirror_path.parent.mkdir(parents=True, exist_ok=True)
        mirror_path.write_text(mirror_text, encoding="utf-8")
        written_mirrors.append(mirror_path)

    # Clean up orphan mirrors
    for fdir in (
        root / ".devtool" / "features",
        root / ".devtool" / "features" / "done",
    ):
        if not fdir.is_dir():
            continue
        for mfile in task_files_in(fdir):
            m_fm = parse_frontmatter(mfile.read_text(encoding="utf-8"))
            m_epic = m_fm.get("epic")
            if m_epic and m_epic in target_slugs:
                if not (epic_path / mfile.name).is_file():
                    mfile.unlink()

    return written_mirrors


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
    epic_parser.add_argument(
        "epic_dir", help="Epic directory name (e.g. logging_refactor)"
    )
    epic_parser.add_argument("status", help="New status string (e.g. 'In Progress')")

    archive_parser = subparsers.add_parser(
        "archive-epic",
        help="Archive done tasks of an epic into .devtool/epic/<epic_dir>/",
    )
    archive_parser.add_argument(
        "epic_dir", help="Epic directory name (e.g. logging_refactor)"
    )

    subparsers.add_parser(
        "archive-done",
        help="Find all completed tasks in .devtool/features/done/ and archive them into their respective epic directories",
    )

    render_parser = subparsers.add_parser(
        "render", help="Render single-source epic tasks into features mirrors"
    )
    render_parser.add_argument(
        "epic_dir", help="Epic directory name (e.g. logging_refactor)"
    )
    render_parser.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help="Root directory for embedded files",
    )

    prereqs_parser = subparsers.add_parser(
        "check-prereqs", help="Check prerequisite epics for an epic"
    )
    prereqs_parser.add_argument("epic_dir", help="Epic directory name")

    conflicts_parser = subparsers.add_parser(
        "check-conflicts", help="Check file pattern conflicts with active epics"
    )
    conflicts_parser.add_argument("epic_dir", help="Epic directory name")

    promote_parser = subparsers.add_parser(
        "promote", help="Promote backlog tasks of an epic to todo"
    )
    promote_parser.add_argument("epic_dir", help="Epic directory name")
    promote_parser.add_argument(
        "--force", action="store_true", help="Bypass prerequisite and conflict checks"
    )

    args = parser.parse_args()

    if args.command == "task":
        if args.status not in TASK_STATUSES:
            sys.stderr.write(
                f"Invalid status '{args.status}'. Expected one of: {', '.join(TASK_STATUSES)}\n"
            )
            sys.exit(2)

        failures = done_gate_failures(args.task_id) if args.status == "done" else []
        if failures:
            sys.stderr.write(f"refused: {args.task_id} cannot be marked done\n")
            for failure in failures:
                sys.stderr.write(f"  {failure}\n")
            sys.exit(1)

        current_root = _current_checkout_root()
        roots = (
            [current_root]
            if current_root is not None and _is_slot_worktree(current_root)
            else checkout_roots()
        )
        written, notes = sync_task(roots, args.task_id, args.status)
        for note in notes:
            sys.stderr.write(f"Note: {note}\n")

        if not written:
            sys.stderr.write(
                f"Warning: No copies of task '{args.task_id}' found in any checkout.\n"
            )
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
        roots = epic_checkout_roots(args.epic_dir)
        matched, written = sync_epic(roots, args.epic_dir, args.status)
        if not matched:
            sys.stderr.write(f"Warning: No epic docs found for '{args.epic_dir}'.\n")
            sys.exit(1)
        print(
            f"Synchronized {len(matched)} epic docs for '{args.epic_dir}' -> '{args.status}'"
        )

    elif args.command == "archive-epic":
        roots = checkout_roots()
        archived, cleaned = archive_epic_tasks(roots, args.epic_dir)
        print(
            f"Archived {len(archived)} tasks into .devtool/epic/{args.epic_dir} "
            f"(cleaned {len(cleaned)} from features)"
        )

    elif args.command == "archive-done":
        roots = checkout_roots()
        done_epics = archive_all_done_epics(roots)
        if done_epics:
            print(
                f"Archived {len(done_epics)} epic(s) into .devtool/epic/: {', '.join(done_epics)}"
            )
        else:
            print("No completed tasks to archive.")

    elif args.command == "render":
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
        root = Path(top.stdout.strip()) if top.returncode == 0 else Path.cwd()
        try:
            rendered = render_epic_tasks(root, args.epic_dir, args.source_root)
            print(f"Rendered {len(rendered)} tasks for epic '{args.epic_dir}'")
        except (ValueError, FileNotFoundError) as error:
            sys.stderr.write(f"error: {error}\n")
            sys.exit(1)

    elif args.command == "check-prereqs":
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
        root = Path(top.stdout.strip()) if top.returncode == 0 else Path.cwd()
        blockers = check_epic_prerequisites(root, args.epic_dir)
        if blockers:
            for b in blockers:
                sys.stderr.write(f"error: {b}\n")
            sys.exit(1)
        else:
            print("0 unfinished prerequisites")

    elif args.command == "check-conflicts":
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
        root = Path(top.stdout.strip()) if top.returncode == 0 else Path.cwd()
        conflicts = check_epic_file_conflicts(root, args.epic_dir)
        if conflicts:
            for ep, pats in conflicts.items():
                sys.stderr.write(f"conflict with {ep}: {', '.join(pats)}\n")
            sys.exit(1)
        else:
            print("0 conflicts — safe for concurrent execution")

    elif args.command == "promote":
        roots = checkout_roots()
        promoted, blockers = promote_epic_tasks(
            roots, args.epic_dir, force=args.force
        )
        if blockers:
            for b in blockers:
                sys.stderr.write(f"error: {b}\n")
            sys.exit(1)
        else:
            print(
                f"Promoted {len(promoted)} task copies of epic '{args.epic_dir}' to todo"
            )


if __name__ == "__main__":
    main()
