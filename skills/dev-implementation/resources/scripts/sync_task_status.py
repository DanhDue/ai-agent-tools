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

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc  # type: ignore[attr-defined]
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from slug_utils import parse_frontmatter, sanitize_slug

TASK_STATUSES = ("backlog", "todo", "in-progress", "review", "done")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


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
            current_path = Path(line[len("worktree "):])
            current_branch = None
        elif line.startswith("branch "):
            current_branch = line[len("branch "):]
        elif line == "detached":
            current_branch = None

    if current_path is not None:
        entries.append((current_path, current_branch))

    return entries


def checkout_roots() -> list[Path]:
    """Every checkout of this repo, main worktree first.

    The only subprocess boundary in this module -- everything else is pure and
    directly testable, which is why the test suite needs no git fixtures.
    """
    result = subprocess.run(["git", "worktree", "list", "--porcelain"],
                            capture_output=True, text=True, check=True)
    return parse_worktree_list(result.stdout)


def epic_checkout_roots(epic_dir: str) -> list[Path]:
    """Return the current checkout root plus every worktree on branch refs/heads/epic/<epic_slug>.

    Current checkout is always first. Other worktrees are included only if their branch
    matches this epic's slug.
    """
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True, check=True)
    current_root = Path(top.stdout.strip())

    wt_result = subprocess.run(["git", "worktree", "list", "--porcelain"],
                               capture_output=True, text=True, check=True)
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
            written.append(board_location(root, path, new_status))

    return written, notes


def board_location(root: Path, path: Path, status: str) -> Path:
    """Move a features copy into features/done when it becomes done, and back when it leaves done.

    Epic mirrors stay put. A copy already at the target is replaced by the one just written.
    """
    features = root / ".devtool" / "features"
    content = path.read_text(encoding="utf-8")
    if status == "done" and path.parent == features:
        target = features / "done" / path.name
        content = content.replace("](../epic/", "](../../epic/")
    elif status != "done" and path.parent == features / "done":
        target = features / path.name
        content = content.replace("](../../epic/", "](../epic/")
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
            match = re.search(r"^-\s*\*\*(?:Epic)\*\*:\s*(.+)$", doc.read_text(), re.MULTILINE)
            if match:
                slug = sanitize_slug(match.group(1))
                if slug:
                    return slug
    for task_file in sorted(epic_path.glob("task_*.md")):
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
    text = re.sub(r"\]\((?:\.\./)+epic/" + re.escape(epic_dir) + r"/([^)]+)\)", r"](\1)", text)
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
                target_slug = epic_slug or sanitize_slug(epic_dir) or epic_dir
                target_slugs = {target_slug, target_slug.replace("-", "_"), target_slug.replace("_", "-")}
                if file_epic and file_epic not in target_slugs:
                    continue
                dest_file = dest_dir / task_file.name
                if dest_file.exists():
                    mirror_fm = parse_frontmatter(task_file.read_text(encoding="utf-8"))
                    canonical_text = dest_file.read_text(encoding="utf-8")
                    for field in ("status", "modified", "completedAt"):
                        if field in mirror_fm:
                            canonical_text = set_frontmatter_field(canonical_text, field, str(mirror_fm[field]))
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
    status_re = re.compile(r"^(-\s*\*\*(?:Status|Trạng thái)(?:\*\*:\s*|:\*\*\s*)).*$", re.MULTILINE)
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


def code_epic_dir(root: Path, task_id: str) -> str | None:
    """The epic directory of this checkout's copy of the task when that epic is a code epic, else None."""
    from task_contract import is_code_epic

    for features in (root / ".devtool" / "features", root / ".devtool" / "features" / "done"):
        if (features / f"{task_id}.md").is_file():
            slug = epic_of(features / f"{task_id}.md")
            epic_dir = find_epic_dir_for_slug(root, slug) if slug else None
            if epic_dir and is_code_epic(root / ".devtool" / "epic" / epic_dir / f"{epic_dir}.en.md"):
                return epic_dir
            return None
    return None


def done_gate_failures(task_id: str) -> list[str]:
    """Messages refusing `task <id> done` for a code epic's task; empty when the gate does not apply or passes."""
    from task_contract import ContractError, evaluate_done_gate, section

    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=False, capture_output=True, text=True)
    if top.returncode != 0:
        return []
    root = Path(top.stdout.strip())
    epic_dir = code_epic_dir(root, task_id)
    if epic_dir is None:
        if (any(code_epic_dir(other, task_id) for other in checkout_roots() if other.resolve() != root.resolve())
                and not task_targets(root, task_id)):
            return ["run the done gate in the checkout that holds the task and its evidence (the epic worktree)"]
        return []
    mirror = root / ".devtool" / "epic" / epic_dir / f"{task_id}.md"
    if not mirror.is_file() or section(mirror.read_text(encoding="utf-8"), "Verification") is None:
        return [(f"retrofit required: {mirror} has no Verification section — retrofit it through "
                "dev-designer's Updating an Existing Epic")]
    try:
        return evaluate_done_gate(mirror)
    except ContractError as error:
        return [f"condition 1: {error}"]


SCENARIO_LINE = re.compile(r"^\s*Scenario(?:\s+Outline)?:\s*(.+)$")
ID_SHAPE = re.compile(r"[A-Z0-9]+(?:-[A-Z0-9]+)+")
FENCE = re.compile(r"^(`{3,}|~{3,})(.*)$")
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

    for line in text.splitlines():
        fence_match = FENCE.match(line)
        if fence_match and fence_marker is None:
            fence_marker = fence_match.group(1)
            in_gherkin = fence_match.group(2).lower() == "gherkin"
            if not in_gherkin and current_id is not None:
                blocks[current_id] = current_lines
                current_id = None
                current_lines = []
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
            if current_id is not None:
                blocks[current_id] = current_lines
                current_id = None
                current_lines = []
            continue

        if not in_gherkin:
            continue

        sc_match = SCENARIO_LINE.match(line)
        if sc_match:
            if current_id is not None:
                blocks[current_id] = current_lines
                current_lines = []
            rest = sc_match.group(1).strip()
            id_match = ID_SHAPE.search(rest)
            if id_match:
                current_id = id_match.group(0)
                current_lines = [line.rstrip()]
            else:
                current_id = None
        elif current_id is not None:
            if not line.strip():
                blocks[current_id] = current_lines
                current_id = None
                current_lines = []
            else:
                current_lines.append(line.rstrip())

    if current_id is not None:
        blocks[current_id] = current_lines

    return blocks


def inject_bdd_scenarios(task_text: str, canonical_blocks: dict[str, list[str]]) -> str:
    """Inject verbatim Gherkin scenario blocks matching Covers: into ### BDD SCENARIOS."""
    covers: list[str] = []
    for line in task_text.splitlines():
        m = re.match(r"^Covers:\s*(.+)$", line.strip())
        if m:
            covers.extend(re.findall(r"[A-Z0-9]+(?:-[A-Z0-9]+)+", m.group(1)))
    if not covers:
        return task_text

    missing = [c for c in covers if c not in canonical_blocks]
    if missing:
        raise ValueError(f"Covered scenario(s) missing from bdd_scenarios.en.md: {', '.join(missing)}")

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

    m_block2 = re.search(r"(^Covers:[^\n]*\n+)(```[a-zA-Z0-9_-]*\n[\s\S]*?\n```)", task_text, flags=re.MULTILINE)
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
            raise ValueError(f"Invalid embedded file path: {rel_path_str} (must be relative without '..')")

        target = source_root / rel_path
        if not target.is_file():
            raise ValueError(f"Embedded file not found: {rel_path_str} (looked in {target})")

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
        if (epic_path / base_target).is_file() or (epic_path / f"{base_target}.md").is_file() or base_target.startswith("task_"):
            return f"[{label}]({target})"
        return m.group(0)

    return re.sub(r"\[([^\]]+)\]\(\./([^)]+)\)", replacer, text)


def rewrite_mirror_links(text: str, epic_dir: str, is_done: bool, epic_path: Path) -> str:
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
            or base_target.startswith(("task_", epic_dir))
            or base_target.endswith(".md")
        ):
            return f"[{label}]({prefix}{target})"
        return m.group(0)

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replacer, canonical)


def render_epic_tasks(root: Path, epic_dir: str, source_root: Path | None = None) -> list[Path]:
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
    target_slugs = {epic_slug, epic_slug.replace("-", "_"), epic_slug.replace("_", "-"), sanitize_slug(epic_dir)}

    # Phase 1: Validate and render in-memory across all tasks.
    # If any task fails validation (unknown scenario ID or missing embed file),
    # the function raises before mutating any canonical or mirror task file on disk.
    render_plan: list[tuple[Path, str, Path, Path, str]] = []
    for task_file in sorted(epic_path.glob("task_*.md")):
        task_text = task_file.read_text(encoding="utf-8")
        task_text = canonicalize_intra_epic_links(task_text, epic_path)
        task_text = expand_embedded_files(task_text, source_root)
        task_text = inject_bdd_scenarios(task_text, canonical_blocks)

        fm = parse_frontmatter(task_text)
        is_done = fm.get("status") == "done"

        mirror_dir = root / ".devtool" / "features" / "done" if is_done else root / ".devtool" / "features"
        other_dir = root / ".devtool" / "features" if is_done else root / ".devtool" / "features" / "done"

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
    for fdir in (root / ".devtool" / "features", root / ".devtool" / "features" / "done"):
        if not fdir.is_dir():
            continue
        for mfile in sorted(fdir.glob("task_*.md")):
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
    epic_parser.add_argument("epic_dir", help="Epic directory name (e.g. logging_refactor)")
    epic_parser.add_argument("status", help="New status string (e.g. 'In Progress')")

    archive_parser = subparsers.add_parser(
        "archive-epic", help="Archive done tasks of an epic into .devtool/epic/<epic_dir>/"
    )
    archive_parser.add_argument("epic_dir", help="Epic directory name (e.g. logging_refactor)")

    subparsers.add_parser(
        "archive-done",
        help="Find all completed tasks in .devtool/features/done/ and archive them into their respective epic directories",
    )

    render_parser = subparsers.add_parser(
        "render", help="Render single-source epic tasks into features mirrors"
    )
    render_parser.add_argument("epic_dir", help="Epic directory name (e.g. logging_refactor)")
    render_parser.add_argument("--source-root", type=Path, default=None, help="Root directory for embedded files")

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
        roots = epic_checkout_roots(args.epic_dir)
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
        done_epics = archive_all_done_epics(roots)
        if done_epics:
            print(f"Archived {len(done_epics)} epic(s) into .devtool/epic/: {', '.join(done_epics)}")
        else:
            print("No completed tasks to archive.")

    elif args.command == "render":
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=False, capture_output=True, text=True)
        root = Path(top.stdout.strip()) if top.returncode == 0 else Path.cwd()
        try:
            rendered = render_epic_tasks(root, args.epic_dir, args.source_root)
            print(f"Rendered {len(rendered)} tasks for epic '{args.epic_dir}'")
        except (ValueError, FileNotFoundError) as error:
            sys.stderr.write(f"error: {error}\n")
            sys.exit(1)



if __name__ == "__main__":
    main()


