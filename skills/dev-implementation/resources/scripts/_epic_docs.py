#!/usr/bin/env python3
"""English-only epic document resolution helpers.

Resolution order for epic artefacts: ``<stem>.md`` first, then legacy
``<stem>.en.md``, and ``None`` when neither exists. Vietnamese mirrors
(``*.vi.md``) are never resolved or read.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def resolve_epic_doc(directory: Path, stem: str) -> Path | None:
    """Resolve ``<stem>.md``, else ``<stem>.en.md``, else None; never ``.vi.md``."""
    base = Path(directory)
    for ext in (".md", ".en.md"):
        candidate = base / f"{stem}{ext}"
        if candidate.is_file() and not candidate.name.endswith(".vi.md"):
            return candidate
    return None


def resolve_design_specs(directory: Path) -> list[Path]:
    """Return ``*-design.md`` then ``*-design.en.md`` files in ``directory``, never ``.vi.md``."""
    base = Path(directory)
    if not base.is_dir():
        return []
    plain = sorted(
        p
        for p in base.glob("*-design.md")
        if p.is_file() and not p.name.endswith(".vi.md")
    )
    legacy = sorted(
        p
        for p in base.glob("*-design.en.md")
        if p.is_file() and not p.name.endswith(".vi.md")
    )
    return [*plain, *legacy]


def resolve_epic_doc_at(
    root: Path, rev: str, epic_rel: str, stem: str
) -> str | None:
    """Resolve ``<epic_rel>/<stem>.md``, else ``.en.md``, at git ``rev`` without reading the working tree."""
    rel = Path(epic_rel).as_posix().strip("/")
    for ext in (".md", ".en.md"):
        candidate = f"{rel}/{stem}{ext}"
        if candidate.endswith(".vi.md"):
            continue
        res = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-e", f"{rev}:{candidate}"],
            capture_output=True,
            check=False,
        )
        if res.returncode == 0:
            return candidate
    return None


def is_task_markdown(path: str | Path) -> bool:
    """Return True when ``path`` names a ``task_*.md`` file and not a ``.vi.md`` mirror."""
    name = Path(path).name
    return (
        name.startswith("task_")
        and name.endswith(".md")
        and not name.endswith(".vi.md")
    )


def iter_task_files(directory: Path) -> list[Path]:
    """Return sorted ``task_*.md`` files in ``directory``, excluding ``*.vi.md``."""
    base = Path(directory)
    if not base.is_dir():
        return []
    return sorted(
        p for p in base.glob("task_*.md") if p.is_file() and is_task_markdown(p)
    )
