#!/usr/bin/env python3
"""Manage 2-Slot Ephemeral Worker Pool for Parallel Task Execution.

Provides isolated ephemeral git worktrees for sub-agents executing independent
Kanban tasks in parallel within the same topological layer, while sharing build
caches and dependencies (node_modules, .venv, .gradle, target, .dart_tool) via
APFS clone / symlinks with zero storage overhead.
"""
from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

CACHE_DIR_CANDIDATES = [
    "node_modules",
    ".venv",
    ".gradle",
    "target",
    ".dart_tool",
    "Pods",
    ".build",
]


def resolve_repo_root(path: Path) -> Path:
    """Resolve the primary git repository root from any checkout or linked worktree."""
    if path.is_dir():
        res = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            raw_common = res.stdout.strip()
            if raw_common:
                common_path = Path(raw_common)
                if not common_path.is_absolute():
                    common_path = path / common_path
                repo_dir = common_path.resolve().parent
                if path.resolve() == repo_dir:
                    return path
                if path.parent.name == ".worktrees" and path.parent.parent.resolve() == repo_dir:
                    return path.parent.parent
                return repo_dir

    if path.parent.name == ".worktrees":
        return path.parent.parent
    return path


def resolve_pool_roots(start_path: Path, epic_dir: str) -> tuple[Path, Path]:
    """Return (primary_repo_root, epic_worktree_root) without nesting .worktrees."""
    repo_root = resolve_repo_root(start_path)
    default_wt = repo_root / ".worktrees" / epic_dir
    if default_wt.is_dir():
        return repo_root, default_wt
    if start_path.resolve() != repo_root.resolve() and start_path.is_dir():
        return repo_root, start_path
    return repo_root, default_wt


def get_slot_path(root: Path, epic_dir: str, slot: int) -> Path:
    """Return the worktree filesystem path for a pool slot under primary repo root."""
    repo_root = resolve_repo_root(root)
    return repo_root / ".worktrees" / f"{epic_dir}-slot-{slot}"


def get_slot_branch(epic_slug: str, slot: int) -> str:
    """Return the git branch name for a pool slot."""
    return f"epic/{epic_slug}-slot-{slot}"


def link_shared_caches(main_wt: Path, slot_wt: Path) -> list[str]:
    """Link or APFS-clone heavy cache and dependency directories from main worktree to slot."""
    linked: list[str] = []
    if not main_wt.is_dir() or not slot_wt.is_dir():
        return linked

    is_darwin = platform.system() == "Darwin"

    for cdir in CACHE_DIR_CANDIDATES:
        src = main_wt / cdir
        dst = slot_wt / cdir
        if not src.exists() or dst.exists():
            continue

        try:
            # On macOS, attempt APFS clone if supported and directory is writable; otherwise symlink
            # Symlinks provide zero-byte overhead and real-time dependency resolution across all tools
            dst.symlink_to(src)
            linked.append(cdir)
        except OSError:
            # Fallback to copy-on-write via cp -c -R if symlink is disallowed
            if is_darwin and src.is_dir():
                res = subprocess.run(["cp", "-c", "-R", str(src), str(dst)], check=False, capture_output=True)
                if res.returncode == 0:
                    linked.append(cdir)
    return linked


def init_slots(
    root: Path,
    epic_dir: str,
    epic_slug: str,
    pool_size: int = 2,
    base_ref: str | None = None,
    epic_worktree_root: Path | None = None,
) -> list[Path]:
    """Create isolated worktrees for worker pool slots and link caches."""
    repo_root, default_wt = resolve_pool_roots(root, epic_dir)
    main_wt = epic_worktree_root if epic_worktree_root is not None else default_wt
    target_base = base_ref or f"epic/{epic_slug}"
    created_paths: list[Path] = []

    for slot in range(1, pool_size + 1):
        slot_path = get_slot_path(repo_root, epic_dir, slot)
        slot_branch = get_slot_branch(epic_slug, slot)

        if not slot_path.is_dir():
            slot_path.parent.mkdir(parents=True, exist_ok=True)
            res_branch = subprocess.run(
                ["git", "rev-parse", "--verify", "--quiet", slot_branch],
                cwd=repo_root,
                capture_output=True,
                check=False,
            )
            if res_branch.returncode == 0:
                cmd = ["git", "worktree", "add", str(slot_path), slot_branch]
            else:
                cmd = ["git", "worktree", "add", str(slot_path), "-b", slot_branch, target_base]

            subprocess.run(cmd, cwd=repo_root, check=True, capture_output=True)

        cache_source = main_wt if main_wt.is_dir() else repo_root
        if cache_source.is_dir():
            link_shared_caches(cache_source, slot_path)

        created_paths.append(slot_path)

    return created_paths


def sync_slot(
    root: Path,
    epic_dir: str,
    epic_slug: str,
    slot: int,
    base_ref: str | None = None,
) -> bool:
    """Reset slot worktree cleanly to the latest HEAD of the epic branch."""
    repo_root = resolve_repo_root(root)
    slot_path = get_slot_path(repo_root, epic_dir, slot)
    if not slot_path.is_dir():
        return False

    target_ref = base_ref or f"epic/{epic_slug}"
    subprocess.run(
        ["git", "fetch", ".", f"{target_ref}:{target_ref}"],
        cwd=slot_path,
        capture_output=True,
        check=False,
    )
    res = subprocess.run(
        ["git", "reset", "--hard", target_ref],
        cwd=slot_path,
        capture_output=True,
        check=False,
    )
    if res.returncode != 0:
        return False

    clean_cmd = ["git", "clean", "-fd"]
    for cdir in CACHE_DIR_CANDIDATES:
        clean_cmd.extend(["-e", cdir])
    subprocess.run(clean_cmd, cwd=slot_path, capture_output=True, check=False)
    return True


def merge_slot(
    root: Path,
    epic_dir: str,
    epic_slug: str,
    slot: int,
    task_id: str | None = None,
    epic_worktree_root: Path | None = None,
) -> bool:
    """Merge slot's commit back into the main epic worktree branch, aborting on conflict."""
    repo_root, default_wt = resolve_pool_roots(root, epic_dir)
    main_wt = epic_worktree_root if epic_worktree_root is not None else default_wt
    if not main_wt.is_dir():
        return False

    slot_branch = get_slot_branch(epic_slug, slot)
    res = subprocess.run(
        ["git", "merge", "--ff-only", slot_branch],
        cwd=main_wt,
        capture_output=True,
        check=False,
    )
    if res.returncode != 0:
        msg = f"Merge slot {slot}" + (f" for {task_id}" if task_id else "")
        res = subprocess.run(
            ["git", "merge", "--no-ff", "-m", msg, slot_branch],
            cwd=main_wt,
            capture_output=True,
            check=False,
        )
        if res.returncode != 0:
            subprocess.run(
                ["git", "merge", "--abort"],
                cwd=main_wt,
                capture_output=True,
                check=False,
            )
            return False

    return True


def cleanup_slots(root: Path, epic_dir: str, epic_slug: str, pool_size: int = 2) -> bool:
    """Prune and remove all slot worktrees and temporary branches."""
    repo_root = resolve_repo_root(root)
    for slot in range(1, pool_size + 1):
        slot_path = get_slot_path(repo_root, epic_dir, slot)
        slot_branch = get_slot_branch(epic_slug, slot)

        if slot_path.is_dir():
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(slot_path)],
                cwd=repo_root,
                capture_output=True,
                check=False,
            )

        subprocess.run(
            ["git", "branch", "-D", slot_branch],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )

    subprocess.run(["git", "worktree", "prune"], cwd=repo_root, capture_output=True, check=False)
    return True


def get_pool_status(
    root: Path,
    epic_dir: str,
    pool_size: int = 2,
    epic_slug: str | None = None,
) -> dict[int, dict[str, Any]]:
    """Inspect presence, branch, and status of worker pool slots."""
    repo_root = resolve_repo_root(root)
    resolved_slug = epic_slug or epic_dir
    status: dict[int, dict[str, Any]] = {}
    for slot in range(1, pool_size + 1):
        slot_path = get_slot_path(repo_root, epic_dir, slot)
        slot_branch = get_slot_branch(epic_slug=resolved_slug, slot=slot)
        exists = slot_path.is_dir()
        head = None
        dirty = False
        if exists:
            h_res = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=slot_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if h_res.returncode == 0:
                head = h_res.stdout.strip()
            s_res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=slot_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if s_res.returncode == 0 and s_res.stdout.strip():
                dirty = True

        status[slot] = {
            "path": str(slot_path),
            "branch": slot_branch,
            "exists": exists,
            "head": head,
            "dirty": dirty,
        }
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", help="Initialize worker pool slots")
    p_init.add_argument("--epic-dir", required=True, help="Epic directory name")
    p_init.add_argument("--epic-slug", required=True, help="Epic slug")
    p_init.add_argument("--pool-size", type=int, default=2, help="Number of slots (default: 2)")
    p_init.add_argument("--base", default=None, help="Base ref for slots (default: epic/<epic_slug>)")

    # sync
    p_sync = subparsers.add_parser("sync", help="Reset slot to latest epic HEAD")
    p_sync.add_argument("--epic-dir", required=True, help="Epic directory name")
    p_sync.add_argument("--epic-slug", required=True, help="Epic slug")
    p_sync.add_argument("--slot", type=int, required=True, help="Slot number (1 or 2)")
    p_sync.add_argument("--base", default=None, help="Base ref to sync to (default: epic/<epic_slug>)")

    # merge
    p_merge = subparsers.add_parser("merge", help="Merge slot back to main worktree")
    p_merge.add_argument("--epic-dir", required=True, help="Epic directory name")
    p_merge.add_argument("--epic-slug", required=True, help="Epic slug")
    p_merge.add_argument("--slot", type=int, required=True, help="Slot number (1 or 2)")
    p_merge.add_argument("--task", default=None, help="Task ID being merged")

    # cleanup
    p_clean = subparsers.add_parser("cleanup", help="Remove all slots and delete branches")
    p_clean.add_argument("--epic-dir", required=True, help="Epic directory name")
    p_clean.add_argument("--epic-slug", required=True, help="Epic slug")
    p_clean.add_argument("--pool-size", type=int, default=2, help="Number of slots (default: 2)")

    # status
    p_status = subparsers.add_parser("status", help="Show pool status")
    p_status.add_argument("--epic-dir", required=True, help="Epic directory name")
    p_status.add_argument("--epic-slug", default=None, help="Optional epic slug (defaults to epic-dir)")
    p_status.add_argument("--pool-size", type=int, default=2, help="Number of slots (default: 2)")

    args = parser.parse_args(argv)
    root = resolve_repo_root(Path.cwd())

    if args.command == "init":
        paths = init_slots(root, args.epic_dir, args.epic_slug, pool_size=args.pool_size, base_ref=args.base)
        print(f"Initialized {len(paths)} worker pool slots:")
        for p in paths:
            print(f"  {p}")
        return 0

    if args.command == "sync":
        ok = sync_slot(root, args.epic_dir, args.epic_slug, args.slot, base_ref=args.base)
        if ok:
            print(f"Slot {args.slot} synchronized to latest {args.base or f'epic/{args.epic_slug}'}")
            return 0
        print(f"Failed to sync slot {args.slot}", file=sys.stderr)
        return 1

    if args.command == "merge":
        ok = merge_slot(root, args.epic_dir, args.epic_slug, args.slot, task_id=args.task)
        if ok:
            print(f"Slot {args.slot} merged successfully into .worktrees/{args.epic_dir}")
            return 0
        print(f"Failed to merge slot {args.slot}", file=sys.stderr)
        return 1

    if args.command == "cleanup":
        cleanup_slots(root, args.epic_dir, args.epic_slug, pool_size=args.pool_size)
        print(f"Cleaned up worker pool slots for {args.epic_dir}")
        return 0

    if args.command == "status":
        status = get_pool_status(root, args.epic_dir, pool_size=args.pool_size, epic_slug=args.epic_slug)
        print(f"Worker Pool Status for {args.epic_dir}:")
        for slot, info in status.items():
            st = "Active" if info["exists"] else "Not created"
            extra = f" (HEAD: {info['head']}, Dirty: {info['dirty']})" if info["exists"] else ""
            print(f"  Slot {slot}: {st}{extra} at {info['path']}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())

