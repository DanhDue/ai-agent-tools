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
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
KIT_SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(KIT_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(KIT_SCRIPTS_DIR))

_STATE_ENVELOPE: Any | None = None
try:
    import _state_envelope as _imported_state_envelope  # noqa: E402

    _STATE_ENVELOPE = _imported_state_envelope
except ImportError:
    _STATE_ENVELOPE = None

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


def _safe_epic_slug(epic_slug: str) -> str:
    if _STATE_ENVELOPE is not None:
        return str(_STATE_ENVELOPE._sanitize_epic_slug(epic_slug))
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", epic_slug.strip()).strip("_.")
    return cleaned or "unknown"


def _heartbeat_path(repo_root: Path, epic_slug: str) -> Path:
    return repo_root / ".devtool" / "state" / f"{_safe_epic_slug(epic_slug)}.heartbeat.json"


def _active_tasks_from_heartbeat(repo_root: Path, epic_slug: str) -> dict[str, dict[str, Any]]:
    if _STATE_ENVELOPE is None:
        return {}
    fallback: dict[str, Any] = {}
    data = _STATE_ENVELOPE.read_json_safe(_heartbeat_path(repo_root, epic_slug), fallback)
    slots = data.get("slots") if isinstance(data, dict) else None
    return dict(slots) if isinstance(slots, dict) else {}


def _emit_pool_heartbeat(
    root: Path,
    repo_root: Path,
    epic_slug: str,
    **kwargs: Any,
) -> None:
    if _STATE_ENVELOPE is None:
        return
    _STATE_ENVELOPE.update_epic_heartbeat(
        repo_root,
        epic_slug,
        extra_devtool_dirs=_STATE_ENVELOPE.resolve_shared_devtool_dirs(root),
        **kwargs,
    )


def _ref_exists(repo_root: Path, ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=repo_root,
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


def _is_ancestor(repo_root: Path, branch: str, target_ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", branch, target_ref],
            cwd=repo_root,
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


def _list_worktrees_by_branch(repo_root: Path) -> dict[str, Path]:
    res = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        return {}
    mapping: dict[str, Path] = {}
    current: dict[str, str] = {}
    for line in res.stdout.splitlines() + [""]:
        if line:
            key, _, val = line.partition(" ")
            current[key] = val
            continue
        br = current.get("branch", "")
        wt = current.get("worktree", "")
        if br.startswith("refs/heads/") and wt:
            mapping[br.removeprefix("refs/heads/")] = Path(wt)
        current = {}
    return mapping


def _discover_epic_slot_branches(repo_root: Path, epic_dir: str, epic_slug: str) -> list[str]:
    res = subprocess.run(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads/"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        return []
    slug_variants = list(
        dict.fromkeys([epic_slug, epic_dir, epic_slug.replace("-", "_"), epic_slug.replace("_", "-")])
    )
    prefixes = tuple(
        prefix
        for s in slug_variants
        if s
        for prefix in (f"epic/{s}-slot-", f"worker/{s}/slot-")
    )
    return sorted(
        line.strip()
        for line in res.stdout.splitlines()
        if line.strip() and line.strip().startswith(prefixes)
    )


def _resolve_integration_target(repo_root: Path, epic_slug: str, base_ref: str | None = None) -> str:
    candidates = [
        c
        for c in (
            base_ref,
            f"epic/{epic_slug}",
            f"epic/{epic_slug.replace('_', '-')}",
            "develop",
            "main",
            "HEAD",
        )
        if c
    ]
    for cand in candidates:
        if _ref_exists(repo_root, cand):
            return cand
    return "HEAD"


def init_slots(
    root: Path,
    epic_dir: str,
    epic_slug: str,
    pool_size: int = 2,
    base_ref: str | None = None,
    epic_worktree_root: Path | None = None,
    *,
    active_wave: int | None = None,
) -> list[Path]:
    """Create isolated worktrees for worker pool slots, link caches, and seed heartbeat."""
    repo_root, default_wt = resolve_pool_roots(root, epic_dir)
    main_wt = epic_worktree_root if epic_worktree_root is not None else default_wt
    target_base = base_ref or f"epic/{epic_slug}"
    created_paths: list[Path] = []
    slot_updates: dict[str, dict[str, Any]] = {}

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

        slot_updates[f"slot-{slot}"] = {
            "status": "idle",
            "branch": slot_branch,
            "path": str(slot_path),
            "task_id": None,
        }
        created_paths.append(slot_path)

    _emit_pool_heartbeat(
        root,
        repo_root,
        epic_slug,
        active_wave=active_wave,
        slot_updates=slot_updates,
        last_event=f"Initialized {pool_size} worker slots",
    )
    return created_paths


def sync_slot(
    root: Path,
    epic_dir: str,
    epic_slug: str,
    slot: int,
    base_ref: str | None = None,
    *,
    task_id: str | None = None,
    active_wave: int | None = None,
) -> bool:
    """Reset slot worktree cleanly to epic HEAD and update worker heartbeat state."""
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

    slot_key = f"slot-{slot}"
    existing_slots = _active_tasks_from_heartbeat(repo_root, epic_slug)
    working_tasks: set[str] = {
        str(info["task_id"])
        for key, info in existing_slots.items()
        if key != slot_key
        and isinstance(info, dict)
        and info.get("status") == "working"
        and info.get("task_id")
    }
    if task_id:
        working_tasks.add(task_id)

    slot_entry: dict[str, Any] = {
        "status": "working",
        "branch": get_slot_branch(epic_slug, slot),
        "path": str(slot_path),
        "task_id": task_id,
    }
    _emit_pool_heartbeat(
        root,
        repo_root,
        epic_slug,
        active_wave=active_wave,
        active_tasks=sorted(working_tasks),
        slot_updates={slot_key: slot_entry},
        last_event=f"Synced {slot_key}" + (f" for {task_id}" if task_id else ""),
    )
    return True


def merge_slot(
    root: Path,
    epic_dir: str,
    epic_slug: str,
    slot: int,
    task_id: str | None = None,
    epic_worktree_root: Path | None = None,
    *,
    active_wave: int | None = None,
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

    slot_key = f"slot-{slot}"
    existing_slots = _active_tasks_from_heartbeat(repo_root, epic_slug)
    working_tasks = sorted(
        str(info["task_id"])
        for key, info in existing_slots.items()
        if key != slot_key
        and isinstance(info, dict)
        and info.get("status") == "working"
        and info.get("task_id")
    )
    _emit_pool_heartbeat(
        root,
        repo_root,
        epic_slug,
        active_wave=active_wave,
        active_tasks=working_tasks,
        slot_updates={
            slot_key: {
                "status": "idle",
                "branch": slot_branch,
                "path": str(get_slot_path(repo_root, epic_dir, slot)),
                "task_id": None,
            }
        },
        last_event=f"Merged {slot_key}" + (f" ({task_id})" if task_id else ""),
    )
    return True


def cleanup_slots_report(
    root: Path,
    epic_dir: str,
    epic_slug: str,
    pool_size: int = 2,
    *,
    base_ref: str | None = None,
    discard_unmerged: bool = False,
    stale_only: bool = False,
) -> dict[str, Any]:
    """Safely remove clean/integrated slot worktrees and orphan branches while preserving dirty/unmerged work."""
    repo_root = resolve_repo_root(root)
    integration_ref = _resolve_integration_target(repo_root, epic_slug, base_ref)
    wt_by_branch = _list_worktrees_by_branch(repo_root)

    candidates: dict[str, tuple[str | None, str, Path | None]] = {}
    for slot in range(1, pool_size + 1):
        fixed_slot_key: str = f"slot-{slot}"
        slot_branch = get_slot_branch(epic_slug, slot)
        slot_path = get_slot_path(repo_root, epic_dir, slot)
        candidates[slot_branch] = (fixed_slot_key, slot_branch, slot_path)

    for branch in _discover_epic_slot_branches(repo_root, epic_dir, epic_slug):
        if branch not in candidates:
            slot_m = branch.rsplit("slot-", 1)[-1]
            orphan_slot_key: str | None = f"slot-{slot_m}" if slot_m.isdigit() else None
            candidates[branch] = (orphan_slot_key, branch, wt_by_branch.get(branch))

    removed: list[str] = []
    removed_slots: list[str] = []
    preserved_dirty: list[str] = []
    preserved_unmerged: list[str] = []

    for branch, (slot_key, _, default_path) in candidates.items():
        wt_path = wt_by_branch.get(branch, default_path)
        wt_exists = wt_path is not None and wt_path.is_dir()
        branch_exists = _ref_exists(repo_root, branch)

        if not wt_exists and not branch_exists:
            if slot_key:
                removed_slots.append(slot_key)
            continue

        if stale_only and wt_exists:
            # Stale-only mode leaves live slot worktrees intact.
            continue

        dirty = False
        if wt_exists:
            st = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=wt_path,
                capture_output=True,
                text=True,
                check=False,
            )
            dirty = st.returncode == 0 and bool(st.stdout.strip())

        unmerged = branch_exists and not _is_ancestor(repo_root, branch, integration_ref)

        if (dirty or unmerged) and not discard_unmerged:
            if dirty:
                preserved_dirty.append(branch)
            if unmerged:
                preserved_unmerged.append(branch)
            continue

        if wt_exists and wt_path is not None:
            rm_res = subprocess.run(
                ["git", "worktree", "remove", "--force", str(wt_path)],
                cwd=repo_root,
                capture_output=True,
                check=False,
            )
            if rm_res.returncode != 0:
                preserved_dirty.append(branch)
                continue

        if branch_exists:
            # Ancestor check against integration_ref already guarded safety unless discard_unmerged is True.
            br_res = subprocess.run(
                ["git", "branch", "-D", branch],
                cwd=repo_root,
                capture_output=True,
                check=False,
            )
            if br_res.returncode != 0:
                preserved_unmerged.append(branch)
                continue

        removed.append(branch)
        if slot_key:
            removed_slots.append(slot_key)

    subprocess.run(["git", "worktree", "prune"], cwd=repo_root, capture_output=True, check=False)

    if removed_slots:
        _emit_pool_heartbeat(
            root,
            repo_root,
            epic_slug,
            remove_slots=removed_slots,
            last_event=f"Cleaned {len(removed)} worker slot(s); preserved {len(preserved_dirty) + len(preserved_unmerged)}",
        )

    clean_ok = not preserved_dirty and not preserved_unmerged
    return {
        "ok": clean_ok,
        "removed": removed,
        "preserved_dirty": sorted(set(preserved_dirty)),
        "preserved_unmerged": sorted(set(preserved_unmerged)),
    }


def cleanup_slots(
    root: Path,
    epic_dir: str,
    epic_slug: str,
    pool_size: int = 2,
    *,
    base_ref: str | None = None,
    discard_unmerged: bool = False,
    stale_only: bool = False,
) -> bool:
    """Prune and safely remove clean/integrated slot worktrees and temporary branches."""
    report = cleanup_slots_report(
        root,
        epic_dir,
        epic_slug,
        pool_size=pool_size,
        base_ref=base_ref,
        discard_unmerged=discard_unmerged,
        stale_only=stale_only,
    )
    return bool(report["ok"])


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


def _resolve_cli_epic(parser: argparse.ArgumentParser, args: argparse.Namespace) -> tuple[str, str]:
    raw_epic = getattr(args, "epic", None)
    epic_dir = args.epic_dir or (raw_epic.replace("-", "_") if raw_epic else None)
    epic_slug = args.epic_slug or (epic_dir.replace("_", "-") if epic_dir else None)
    if not epic_dir or not epic_slug:
        parser.error("either --epic-dir (with --epic-slug) or positional <epic> is required")
    return epic_dir, epic_slug


def _add_epic_flags(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("epic", nargs="?", default=None, help="Optional epic directory or slug")
    sub.add_argument("--epic-dir", default=None, help="Epic directory name")
    sub.add_argument("--epic-slug", default=None, help="Epic slug")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", help="Initialize worker pool slots")
    _add_epic_flags(p_init)
    p_init.add_argument("--pool-size", type=int, default=2, help="Number of slots (default: 2)")
    p_init.add_argument("--base", default=None, help="Base ref for slots (default: epic/<epic_slug>)")
    p_init.add_argument("--wave", type=int, default=None, help="Active execution wave number")

    # sync
    p_sync = subparsers.add_parser("sync", help="Reset slot to latest epic HEAD")
    _add_epic_flags(p_sync)
    p_sync.add_argument("--slot", type=int, required=True, help="Slot number (1 or 2)")
    p_sync.add_argument("--base", default=None, help="Base ref to sync to (default: epic/<epic_slug>)")
    p_sync.add_argument("--task", default=None, help="Task ID assigned to this slot")
    p_sync.add_argument("--wave", type=int, default=None, help="Active execution wave number")

    # merge
    p_merge = subparsers.add_parser("merge", help="Merge slot back to main worktree")
    _add_epic_flags(p_merge)
    p_merge.add_argument("--slot", type=int, required=True, help="Slot number (1 or 2)")
    p_merge.add_argument("--task", default=None, help="Task ID being merged")
    p_merge.add_argument("--wave", type=int, default=None, help="Active execution wave number")

    # cleanup
    p_clean = subparsers.add_parser("cleanup", help="Safely remove clean/integrated slots and branches")
    _add_epic_flags(p_clean)
    p_clean.add_argument("--pool-size", type=int, default=2, help="Number of slots (default: 2)")
    p_clean.add_argument("--base", default=None, help="Base ref used to verify branch integration")
    p_clean.add_argument(
        "--discard-unmerged",
        "--force",
        action="store_true",
        dest="discard_unmerged",
        help="Force deletion of dirty worktrees or unmerged slot branches",
    )
    p_clean.add_argument(
        "--stale-only",
        action="store_true",
        help="Clean only missing-worktree stale entries and merged orphan branches",
    )

    # status
    p_status = subparsers.add_parser("status", help="Show pool status")
    _add_epic_flags(p_status)
    p_status.add_argument("--pool-size", type=int, default=2, help="Number of slots (default: 2)")

    args = parser.parse_args(argv)
    epic_dir, epic_slug = _resolve_cli_epic(parser, args)
    root = resolve_repo_root(Path.cwd())

    if args.command == "init":
        paths = init_slots(
            root,
            epic_dir,
            epic_slug,
            pool_size=args.pool_size,
            base_ref=args.base,
            active_wave=args.wave,
        )
        print(f"Initialized {len(paths)} worker pool slots:")
        for p in paths:
            print(f"  {p}")
        return 0

    if args.command == "sync":
        ok = sync_slot(
            root,
            epic_dir,
            epic_slug,
            args.slot,
            base_ref=args.base,
            task_id=args.task,
            active_wave=args.wave,
        )
        if ok:
            print(f"Slot {args.slot} synchronized to latest {args.base or f'epic/{epic_slug}'}")
            return 0
        print(f"Failed to sync slot {args.slot}", file=sys.stderr)
        return 1

    if args.command == "merge":
        ok = merge_slot(
            root,
            epic_dir,
            epic_slug,
            args.slot,
            task_id=args.task,
            active_wave=args.wave,
        )
        if ok:
            print(f"Slot {args.slot} merged successfully into .worktrees/{epic_dir}")
            return 0
        print(f"Failed to merge slot {args.slot}", file=sys.stderr)
        return 1

    if args.command == "cleanup":
        report = cleanup_slots_report(
            root,
            epic_dir,
            epic_slug,
            pool_size=args.pool_size,
            base_ref=args.base,
            discard_unmerged=args.discard_unmerged,
            stale_only=args.stale_only,
        )
        print(f"Cleaned {len(report['removed'])} worker pool entry/entries for {epic_dir}")
        if report["preserved_dirty"]:
            print(
                f"Preserved dirty slot(s): {', '.join(report['preserved_dirty'])}",
                file=sys.stderr,
            )
        if report["preserved_unmerged"]:
            print(
                f"Preserved unmerged slot(s): {', '.join(report['preserved_unmerged'])}",
                file=sys.stderr,
            )
        return 0 if report["ok"] else 1

    if args.command == "status":
        status = get_pool_status(root, epic_dir, pool_size=args.pool_size, epic_slug=epic_slug)
        print(f"Worker Pool Status for {epic_dir}:")
        for slot, info in status.items():
            st = "Active" if info["exists"] else "Not created"
            extra = f" (HEAD: {info['head']}, Dirty: {info['dirty']})" if info["exists"] else ""
            print(f"  Slot {slot}: {st}{extra} at {info['path']}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())

