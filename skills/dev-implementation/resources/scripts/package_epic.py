#!/usr/bin/env python3
"""Packaged epic packaging and revision tool.

Usage:
  package_epic.py <epic_dir> [--revise] [--reason <text>] [--base-branch <branch>] [--open-note <note> ...]

Validates epic readiness with check_epic_readiness.py, anchors handoff.md
to the current HEAD commit, and preserves Open Notes while recording a
re-anchoring history under ## Revisions.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
TEMPLATE_PATH = (
    REPO_ROOT / "skills" / "dev-lifecycle" / "references" / "handoff-template.md"
)
READINESS_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "dev-implementation"
    / "resources"
    / "scripts"
    / "check_epic_readiness.py"
)
SYNC_STATUS_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "dev-implementation"
    / "resources"
    / "scripts"
    / "sync_task_status.py"
)

sys.path.insert(0, str(Path(__file__).parent))
try:
    from sync_task_status import find_epic_slug
except ImportError:
    find_epic_slug = None  # type: ignore[assignment]


def resolve_root() -> Path:
    res = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode == 0 and res.stdout.strip():
        return Path(res.stdout.strip())
    return Path.cwd()


def resolve_base_branch(root: Path, epic_dir: str, cli_base: str | None) -> str:
    if cli_base:
        return cli_base
    epic_path = root / ".devtool" / "epic" / epic_dir
    for ext in (".en.md", ".vi.md"):
        doc = epic_path / f"{epic_dir}{ext}"
        if doc.is_file():
            m = re.search(
                r"^-\s*\*\*(?:Base Branch|Nhánh cơ sở)\*\*:\s*`?([^`\s\n]+)`?",
                doc.read_text(encoding="utf-8"),
                re.MULTILINE,
            )
            if m:
                return m.group(1).strip()
    return "main"


def render_initial_handoff(
    template_path: Path,
    epic_dir: str,
    epic_slug: str,
    design_commit: str,
    base_branch: str,
    today_iso: str,
    open_notes: list[str] | None = None,
) -> str:
    template = template_path.read_text(encoding="utf-8")
    text = template.replace("<epic_slug>", epic_slug)
    text = text.replace("<epic_dir>", epic_dir)
    text = text.replace("<epic_slug value>", epic_slug)
    text = text.replace("<epic_dir value>", epic_dir)
    text = text.replace("<YYYY-MM-DD>", today_iso)
    text = text.replace("<sha>", design_commit)
    text = text.replace("<base_branch>", base_branch)

    if open_notes:
        notes_str = "\n".join(f"- {n}" for n in open_notes)
        text = re.sub(
            r"<What the design session knows[^>]+>",
            notes_str,
            text,
        )
    else:
        text = re.sub(
            r"<What the design session knows[^>]+>",
            "None",
            text,
        )

    rev_init = f"- **{today_iso} (`{design_commit}`)**: Initial Stage 2 packaging"
    text = text.replace(
        "- **<YYYY-MM-DD> (`<sha>`)**: Initial Stage 2 packaging",
        rev_init,
    )

    return text


def revise_handoff_text(
    handoff_text: str,
    design_commit: str,
    reason: str,
    today_iso: str,
) -> str:
    old_sha_match = re.search(
        r"^-\s*\*\*Design commit\*\*:\s*`?([^`\s\n]+)`?", handoff_text, re.MULTILINE
    )
    old_sha = old_sha_match.group(1).strip() if old_sha_match else "unknown"

    text = re.sub(
        r"^(-\s*\*\*Packaged\*\*:\s*)(.*)$",
        rf"\g<1>{today_iso}",
        handoff_text,
        flags=re.MULTILINE,
    )

    text = re.sub(
        r"^(-\s*\*\*Design commit\*\*:\s*)(.*)$",
        rf"\g<1>`{design_commit}`",
        text,
        flags=re.MULTILINE,
    )

    text = re.sub(
        r"git log \S+\.\.",
        f"git log {design_commit}..",
        text,
    )

    if "[Revisions](#revisions)" not in text:
        text = text.replace(
            "- [Open Notes](#open-notes)\n",
            "- [Open Notes](#open-notes)\n- [Revisions](#revisions)\n",
        )

    rev_bullet = f"- **{today_iso} (`{old_sha}` -> `{design_commit}`)**: {reason}"
    if "## Revisions\n" in text:
        m_rev = re.search(r"## Revisions\n", text)
        if m_rev:
            idx = m_rev.end()
            m_next = re.search(r"\n## ", text[idx:])
            if m_next:
                sec_end = idx + m_next.start()
                rev_body = text[idx:sec_end].rstrip()
                text = (
                    text[:idx]
                    + (rev_body + "\n" if rev_body.strip() else "\n")
                    + rev_bullet
                    + "\n"
                    + text[sec_end:]
                )
            else:
                text = text.rstrip() + "\n" + rev_bullet + "\n"
    else:
        if "## Rules for the Receiving Agent" in text:
            text = text.replace(
                "## Rules for the Receiving Agent",
                f"## Revisions\n\n{rev_bullet}\n\n## Rules for the Receiving Agent",
            )
        else:
            text = text.rstrip() + f"\n\n## Revisions\n\n{rev_bullet}\n"

    return text


def update_epic_status_to_packaged(root: Path, epic_dir: str, today_iso: str) -> None:
    epic_path = root / ".devtool" / "epic" / epic_dir
    for ext in (".en.md", ".vi.md"):
        doc_path = epic_path / f"{epic_dir}{ext}"
        if not doc_path.is_file():
            continue
        content = doc_path.read_text(encoding="utf-8")
        m = re.search(
            r"^(-\s*\*\*(?:Status|Trạng thái)\*\*:\s*)(.*)$",
            content,
            re.MULTILINE,
        )
        if m:
            cur_status = m.group(2).strip().strip("`").strip('"')
            prefixes = ("packaged", "queued", "in progress", "done", "hoàn thành")
            if not any(cur_status.lower().startswith(p) for p in prefixes):
                new_status = (
                    f"Packaged ({today_iso})"
                    if ext == ".en.md"
                    else f"Đã đóng gói ({today_iso})"
                )
                content = content[: m.start(2)] + new_status + content[m.end(2) :]
                doc_path.write_text(content, encoding="utf-8")


def package_epic(
    root: Path,
    epic_dir: str,
    *,
    revise: bool = False,
    reason: str = "",
    base_branch: str | None = None,
    open_notes: list[str] | None = None,
) -> Path:
    epic_path = root / ".devtool" / "epic" / epic_dir
    if not epic_path.is_dir():
        raise FileNotFoundError(f"Epic directory not found: {epic_path}")

    handoff_file = epic_path / "handoff.md"
    if revise and not handoff_file.is_file():
        raise ValueError("handoff.md does not exist; run without --revise first")

    # 1. Run check_epic_readiness.py
    readiness_proc = subprocess.run(
        [sys.executable, str(READINESS_SCRIPT), epic_dir],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if readiness_proc.returncode != 0:
        if readiness_proc.stdout:
            sys.stderr.write(readiness_proc.stdout)
        if readiness_proc.stderr:
            sys.stderr.write(readiness_proc.stderr)
        raise RuntimeError("Epic readiness check failed; cannot package epic.")

    # 2. Resolve design commit SHA
    res_sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    design_commit = (
        res_sha.stdout.strip()
        if res_sha.returncode == 0 and res_sha.stdout.strip()
        else "uncommitted"
    )

    today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    resolved_base = resolve_base_branch(root, epic_dir, base_branch)

    epic_slug = (
        find_epic_slug(root, epic_dir)
        if find_epic_slug is not None
        else epic_dir.replace("_", "-")
    ) or epic_dir.replace("_", "-")

    if not revise:
        update_epic_status_to_packaged(root, epic_dir, today_iso)
        tpl = TEMPLATE_PATH
        if not tpl.is_file():
            tpl = root / "skills" / "dev-lifecycle" / "references" / "handoff-template.md"
        if not tpl.is_file():
            raise FileNotFoundError(f"handoff-template.md not found at {TEMPLATE_PATH}")
        content = render_initial_handoff(
            tpl,
            epic_dir,
            epic_slug,
            design_commit,
            resolved_base,
            today_iso,
            open_notes=open_notes,
        )
        handoff_file.write_text(content, encoding="utf-8")
    else:
        existing = handoff_file.read_text(encoding="utf-8")
        revised = revise_handoff_text(
            existing,
            design_commit,
            reason,
            today_iso,
        )
        handoff_file.write_text(revised, encoding="utf-8")

    return handoff_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Packaged epic packaging and revision tool."
    )
    parser.add_argument("epic_dir", help="Epic directory under .devtool/epic/")
    parser.add_argument(
        "--revise", action="store_true", help="Re-anchor handoff.md to current HEAD"
    )
    parser.add_argument(
        "--reason", type=str, default="", help="Reason for re-anchoring (--revise)"
    )
    parser.add_argument(
        "--base-branch", type=str, default=None, help="Base branch name"
    )
    parser.add_argument(
        "--open-note", action="append", help="Custom notes to add under ## Open Notes"
    )

    args = parser.parse_args()

    if args.revise and not args.reason.strip():
        sys.stderr.write("error: --reason is required when --revise is set\n")
        sys.exit(2)

    root = resolve_root()
    handoff_file = root / ".devtool" / "epic" / args.epic_dir / "handoff.md"
    if args.revise and not handoff_file.is_file():
        sys.stderr.write("error: handoff.md does not exist; run without --revise first\n")
        sys.exit(2)

    try:
        out = package_epic(
            root,
            args.epic_dir,
            revise=args.revise,
            reason=args.reason.strip(),
            base_branch=args.base_branch,
            open_notes=args.open_note,
        )
        action = "Revised" if args.revise else "Packaged"
        print(f"{action} epic '{args.epic_dir}' -> {out}")
    except (RuntimeError, FileNotFoundError, ValueError) as err:
        sys.stderr.write(f"error: {err}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
