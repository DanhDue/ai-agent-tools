#!/usr/bin/env python3
"""Manage 2-Slot Ephemeral Worker Pool for Parallel Task Execution.

Provides isolated ephemeral git worktrees for sub-agents executing independent
Kanban tasks in parallel within the same topological layer, while sharing build
caches and dependencies (node_modules, .venv, .gradle, target, .dart_tool) via
APFS clone / symlinks with zero storage overhead.
"""
from __future__ import annotations

import argparse
from collections.abc import Iterator, Mapping
import contextlib
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
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

_PERSONA_CONFIG: Any | None = None
try:
    import persona_config as _imported_persona_config  # noqa: E402

    _PERSONA_CONFIG = _imported_persona_config
except ImportError:
    _PERSONA_CONFIG = None

CACHE_DIR_CANDIDATES = [
    "node_modules",
    ".venv",
    ".gradle",
    "target",
    ".dart_tool",
    "Pods",
    ".build",
]

SLOT_SYNC_STATUSES = ("working", "review", "idle")
ACTIVE_SLOT_STATUSES = frozenset(("working", "review"))
HARD_CAP_EXIT_CODE: int = 2
NON_TEST_DIFF_LINE_CAP: int = 30
FINALIZE_MODES = ("pass1-approved", "tier2-short-circuit", "pass2-complete")
TIER2_RISK_LEVELS = ("LOW", "MEDIUM", "HIGH")

_FALLBACK_LOCK_GUARD = threading.Lock()
_FALLBACK_INPROC_LOCKS: dict[Path, threading.RLock] = {}
_FALLBACK_ACTIVE_FLOCKS: dict[Path, tuple[int, Any]] = {}

TIER1_TRIGGER_ORDER = (
    "NON_TEST_DIFF_OVER_30_LINES",
    "PUBLIC_SIGNATURE_CHANGED",
    "API_ROUTE_OR_SCHEMA_CHANGED",
    "DB_OR_PERSISTENCE_CHANGED",
    "CONCURRENCY_OR_LOCKING_CHANGED",
    "TEST_ASSERTION_WEAKENED",
)

_PUBLIC_SIGNATURE_RES = (
    re.compile(r"^\s*(?:async\s+)?def\s+[A-Za-z][A-Za-z0-9_]*\s*\("),
    re.compile(r"^\s*class\s+[A-Za-z]"),
    re.compile(r"^\s*export\s+(?:async\s+)?(?:function|class|interface|type)\b"),
    re.compile(r"^\s*pub\s+(?:async\s+)?(?:fn|struct|enum|trait)\b"),
)
_API_SURFACE_RES = (
    re.compile(r"@(?:router|app)\.(?:get|post|put|patch|delete|websocket)\b"),
    re.compile(r"\b(?:APIRouter|BaseModel|TypedDict|openapi|json_schema)\b"),
)
_DB_SURFACE_RES = (
    re.compile(
        r"\b(?:SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|CREATE\s+TABLE|ALTER\s+TABLE)\b"
    ),
    re.compile(r"\bsession\.(?:execute|commit|rollback|query)\b"),
    re.compile(r"\b(?:alembic|migration|sqlite3|atomic_write)\b"),
)
_CONCURRENCY_RES = (
    re.compile(r"\b(?:Lock|RLock|Semaphore|Condition|Event)\s*\("),
    re.compile(r"\b(?:asyncio|threading|multiprocessing|concurrent\.futures)\."),
    re.compile(r"\bfcntl\.flock\b"),
    re.compile(r"\bos\.(?:setpgrp|killpg)\b"),
    re.compile(r"\bcancel_event\b"),
)
_TEST_ASSERTION_RE = re.compile(
    r"(?:\bassert\b|\bself\.assert|\bpytest\.raises|\bexpect\()"
)
_TEST_SKIP_RE = re.compile(
    r"(?:pytest\.mark\.(?:skip|xfail)|@unittest\.skip|\.skip\()"
)
_COVERS_LINE_RE = re.compile(r"^\s*(?:[-*]\s+)?\**Covers\**\s*:\**\s*(.*)$")
_ID_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9-])[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]+(?![A-Za-z0-9])"
)


class HardCapExceededError(RuntimeError):
    """Raised when slot synchronization violates review/fix caps or preconditions."""

    def __init__(self, message: str, code: str | None = None) -> None:
        if code is None:
            prefix, _, _ = message.partition(":")
            code = prefix.strip() or "HARD_CAP_EXCEEDED"
        self.code = code
        super().__init__(message)


def _collect_other_active_tasks(
    existing_slots: dict[str, dict[str, Any]],
    slot: int,
    slot_key: str,
) -> set[str]:
    """Collect active task IDs held by sibling slots in working or review state."""
    excluded_keys = {slot_key, str(slot)}
    return {
        str(info["task_id"])
        for key, info in existing_slots.items()
        if key not in excluded_keys
        and isinstance(info, dict)
        and str(info.get("status") or "").strip().lower() in ACTIVE_SLOT_STATUSES
        and info.get("task_id")
    }


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
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", epic_slug.strip()).strip("-.")
    return cleaned or "general"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _heartbeat_path(repo_root: Path, epic_slug: str) -> Path:
    return repo_root / ".devtool" / "state" / f"{_safe_epic_slug(epic_slug)}.heartbeat.json"


@contextlib.contextmanager
def _devtool_memory_lock(repo_root: Path) -> Iterator[None]:
    """Acquire a reentrant thread+process exclusive flock on `<repo_root>/.devtool/.memory.lock`."""
    devtool_dir = repo_root / ".devtool"
    devtool_dir.mkdir(parents=True, exist_ok=True)
    lock_file = (devtool_dir / ".memory.lock").resolve()
    with _FALLBACK_LOCK_GUARD:
        rlock = _FALLBACK_INPROC_LOCKS.setdefault(lock_file, threading.RLock())
    rlock.acquire()
    try:
        active = _FALLBACK_ACTIVE_FLOCKS.get(lock_file)
        if active is None:
            handle = lock_file.open("a+", encoding="utf-8")
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            except BaseException:
                with contextlib.suppress(OSError):
                    handle.close()
                raise
            _FALLBACK_ACTIVE_FLOCKS[lock_file] = (1, handle)
        else:
            depth, handle = active
            _FALLBACK_ACTIVE_FLOCKS[lock_file] = (depth + 1, handle)
        try:
            yield
        finally:
            cur_depth, cur_handle = _FALLBACK_ACTIVE_FLOCKS[lock_file]
            if cur_depth > 1:
                _FALLBACK_ACTIVE_FLOCKS[lock_file] = (cur_depth - 1, cur_handle)
            else:
                _FALLBACK_ACTIVE_FLOCKS.pop(lock_file, None)
                with contextlib.suppress(OSError):
                    fcntl.flock(cur_handle.fileno(), fcntl.LOCK_UN)
                with contextlib.suppress(OSError):
                    cur_handle.close()
    finally:
        rlock.release()


@contextlib.contextmanager
def _pool_state_lock(repo_root: Path) -> Iterator[None]:
    if _STATE_ENVELOPE is not None:
        with _STATE_ENVELOPE._state_lock((repo_root / ".devtool").resolve()):
            yield
        return
    with _devtool_memory_lock(repo_root):
        yield


def _read_json_file_safe(path: Path) -> dict[str, Any]:
    try:
        if not path.is_file():
            return {}
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return {}
        parsed = json.loads(raw)
        return dict(parsed) if isinstance(parsed, dict) else {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _atomic_write_json_file(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(dict(payload), indent=2, ensure_ascii=False) + "\n"
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        tmp_path = None
    finally:
        if tmp_path is not None and tmp_path.exists():
            with contextlib.suppress(OSError):
                tmp_path.unlink()


def _active_tasks_from_heartbeat(repo_root: Path, epic_slug: str) -> dict[str, dict[str, Any]]:
    hb_path = _heartbeat_path(repo_root, epic_slug)
    if _STATE_ENVELOPE is None:
        data = _read_json_file_safe(hb_path)
    else:
        fallback: dict[str, Any] = {}
        data = _STATE_ENVELOPE.read_json_safe(hb_path, fallback)
    slots = data.get("slots") if isinstance(data, dict) else None
    return dict(slots) if isinstance(slots, dict) else {}


def _emit_pool_heartbeat(
    root: Path,
    repo_root: Path,
    epic_slug: str,
    **kwargs: Any,
) -> None:
    if _STATE_ENVELOPE is not None:
        _STATE_ENVELOPE.update_epic_heartbeat(
            repo_root,
            epic_slug,
            extra_devtool_dirs=_STATE_ENVELOPE.resolve_shared_devtool_dirs(root),
            **kwargs,
        )
        return

    with _devtool_memory_lock(repo_root):
        hb_path = _heartbeat_path(repo_root, epic_slug)
        state = _read_json_file_safe(hb_path)
        if not state:
            state = {
                "schema_version": 1,
                "generation": 0,
                "epic_slug": epic_slug,
                "stage": "",
                "sub_step": "",
                "sub_step_detail": "",
                "review_state": None,
                "active_wave": None,
                "active_tasks": [],
                "slots": {},
                "last_event": "",
                "events": [],
                "updated_at": _utc_now_iso(),
            }
        state["epic_slug"] = epic_slug
        state["generation"] = int(state.get("generation") or 0) + 1
        state["updated_at"] = _utc_now_iso()
        if kwargs.get("active_wave") is not None:
            state["active_wave"] = kwargs["active_wave"]
        if kwargs.get("active_tasks") is not None:
            state["active_tasks"] = list(kwargs["active_tasks"])
        if kwargs.get("last_event") is not None:
            state["last_event"] = kwargs["last_event"]

        raw_slots = state.get("slots")
        slots: dict[str, Any] = dict(raw_slots) if isinstance(raw_slots, dict) else {}
        slot_updates = kwargs.get("slot_updates")
        if isinstance(slot_updates, Mapping):
            for k, v in slot_updates.items():
                if v is None:
                    slots.pop(str(k), None)
                else:
                    slots[str(k)] = dict(v)
        remove_slots = kwargs.get("remove_slots")
        if remove_slots:
            for k in remove_slots:
                slots.pop(str(k), None)
        state["slots"] = slots

        _atomic_write_json_file(hb_path, state)
        if (
            root.resolve() != repo_root.resolve()
            and (root / ".devtool").is_dir()
            and not (root.parent.name == ".worktrees" and re.search(r"-slot-\d+$", root.name))
        ):
            _atomic_write_json_file(_heartbeat_path(root, epic_slug), state)


def _default_slot_counters() -> dict[str, Any]:
    return {
        "review_passes_used": 0,
        "fix_passes_used": 0,
        "pass1_tree_sha": None,
        "pass1_head_sha": None,
        "pass1_blockers": [],
        "last_triage": None,
    }


def _carry_forward_slot_counters(prev_entry: Mapping[str, Any]) -> dict[str, Any]:
    raw_blockers = prev_entry.get("pass1_blockers")
    raw_triage = prev_entry.get("last_triage")
    raw_tree = prev_entry.get("pass1_tree_sha")
    raw_head = prev_entry.get("pass1_head_sha")
    return {
        "review_passes_used": int(prev_entry.get("review_passes_used") or 0),
        "fix_passes_used": int(prev_entry.get("fix_passes_used") or 0),
        "pass1_tree_sha": str(raw_tree) if raw_tree else None,
        "pass1_head_sha": str(raw_head) if raw_head else None,
        "pass1_blockers": [dict(b) for b in raw_blockers if isinstance(b, Mapping)]
        if isinstance(raw_blockers, list)
        else [],
        "last_triage": dict(raw_triage) if isinstance(raw_triage, Mapping) else None,
    }


def _resolve_task_review_limits(repo_root: Path) -> tuple[int, int]:
    if _PERSONA_CONFIG is not None and hasattr(_PERSONA_CONFIG, "resolve_task_review_limits"):
        max_rev, max_fix = _PERSONA_CONFIG.resolve_task_review_limits(repo_root)
        return int(max_rev), int(max_fix)
    return 2, 1


def _git_head_sha(cwd: Path) -> str | None:
    res = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()
    return None


def _is_non_blocking_finding(item: Any) -> bool:
    if isinstance(item, Mapping):
        for key in ("severity", "type", "category", "tag", "summary"):
            if "NON_BLOCKING_OBSERVATION" in str(item.get(key) or "").upper():
                return True
        return False
    return "NON_BLOCKING_OBSERVATION" in str(item).upper()


def _normalize_blocker_entry(item: Any, index: int) -> dict[str, Any]:
    if isinstance(item, Mapping):
        entry = dict(item)
        entry.setdefault("id", f"BLK-{index}")
        entry.setdefault("category", "LEGACY_FINDING")
        if "summary" not in entry:
            entry["summary"] = str(item)
        return entry
    return {
        "id": f"BLK-{index}",
        "category": "LEGACY_FINDING",
        "summary": str(item),
    }


def normalize_task_review_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize Pass 1/Pass 2 task-reviewer JSON and enforce the Coercion Guard."""
    if not isinstance(payload, Mapping):
        return {
            "valid": False,
            "verdict": "UNPARSEABLE",
            "done_gate": "FAIL",
            "blockers": [],
            "observations": [],
            "coerced_from_non_blocking": False,
            "task_id": None,
            "pass": None,
            "head_sha": None,
        }

    raw_verdict = payload.get("verdict")
    verdict_token = raw_verdict.strip().upper() if isinstance(raw_verdict, str) else ""
    verdict_map = {
        "APPROVED": "APPROVED",
        "PASS": "APPROVED",
        "CHANGES_REQUESTED": "CHANGES_REQUESTED",
        "FAIL": "CHANGES_REQUESTED",
    }
    normalized_verdict = verdict_map.get(verdict_token)
    if normalized_verdict is None:
        return {
            "valid": False,
            "verdict": "UNPARSEABLE",
            "done_gate": str(payload.get("done_gate") or "FAIL").strip().upper(),
            "blockers": [],
            "observations": [],
            "coerced_from_non_blocking": False,
            "task_id": payload.get("task_id"),
            "pass": payload.get("pass"),
            "head_sha": payload.get("head_sha"),
        }

    raw_done_gate = payload.get("done_gate")
    done_gate = raw_done_gate.strip().upper() if isinstance(raw_done_gate, str) else ""

    raw_observations = payload.get("observations")
    observations: list[Any] = (
        list(raw_observations) if isinstance(raw_observations, list) else []
    )

    blockers_key_present = "blockers" in payload and payload.get("blockers") is not None
    raw_blockers = payload.get("blockers")
    blockers: list[dict[str, Any]] = []
    if blockers_key_present and isinstance(raw_blockers, list):
        blockers = [
            _normalize_blocker_entry(item, idx)
            for idx, item in enumerate(raw_blockers, start=1)
        ]
    elif not blockers_key_present:
        raw_findings = payload.get("findings")
        if isinstance(raw_findings, list) and raw_findings:
            blk_idx = 1
            for item in raw_findings:
                if _is_non_blocking_finding(item):
                    observations.append(item)
                else:
                    blockers.append(_normalize_blocker_entry(item, blk_idx))
                    blk_idx += 1

    coerced = False
    if done_gate == "FAIL":
        if not blockers:
            blockers = [
                {
                    "id": "BLK-GATE",
                    "category": "RUNTIME_SAFETY",
                    "summary": "done_gate reported FAIL",
                }
            ]
        normalized_verdict = "CHANGES_REQUESTED"
    elif normalized_verdict == "APPROVED" and blockers:
        normalized_verdict = "CHANGES_REQUESTED"
    elif normalized_verdict == "CHANGES_REQUESTED" and not blockers and done_gate == "PASS":
        normalized_verdict = "APPROVED"
        coerced = True

    return {
        "valid": True,
        "verdict": normalized_verdict,
        "done_gate": done_gate,
        "blockers": blockers,
        "observations": observations,
        "coerced_from_non_blocking": coerced,
        "task_id": payload.get("task_id"),
        "pass": payload.get("pass"),
        "head_sha": payload.get("head_sha"),
    }


def capture_slot_tree_sha(slot_path: Path, epic_dir: str) -> str:
    """Snapshot the slot working tree using a temporary GIT_INDEX_FILE without mutating HEAD or index."""
    idx_res = subprocess.run(
        ["git", "rev-parse", "--git-path", "index"],
        cwd=slot_path,
        capture_output=True,
        text=True,
        check=True,
    )
    raw_index = idx_res.stdout.strip()
    real_index = Path(raw_index)
    if not real_index.is_absolute():
        real_index = slot_path / real_index

    exclude_paths = [
        *CACHE_DIR_CANDIDATES,
        f".devtool/epic/{epic_dir}/evidence",
        f".devtool/epic/{epic_dir}/review_audit_notes*",
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_index = Path(tmp_dir) / "index"
        if real_index.is_file():
            shutil.copy2(real_index, tmp_index)
        env = {**os.environ, "GIT_INDEX_FILE": str(tmp_index)}
        subprocess.run(
            ["git", "add", "-A"],
            cwd=slot_path,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        subprocess.run(
            ["git", "rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", *exclude_paths],
            cwd=slot_path,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        tree_res = subprocess.run(
            ["git", "write-tree"],
            cwd=slot_path,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        return tree_res.stdout.strip()


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
            **_default_slot_counters(),
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
    status: str = "working",
    reset_worktree: bool = True,
    review_payload: Mapping[str, Any] | None = None,
) -> bool:
    """Sync slot state, enforce review/fix hard caps, and capture Pass 1 tree snapshot."""
    normalized_status = status.strip().lower()
    if normalized_status not in SLOT_SYNC_STATUSES:
        raise ValueError(
            f"Unsupported slot sync status {status!r}; expected one of {SLOT_SYNC_STATUSES}"
        )

    repo_root = resolve_repo_root(root)
    slot_path = get_slot_path(repo_root, epic_dir, slot)
    if not slot_path.is_dir():
        return False

    normalized_review: dict[str, Any] | None = None
    if normalized_status == "working" and not reset_worktree and review_payload is not None:
        normalized_review = normalize_task_review_payload(review_payload)
        if (
            normalized_review.get("verdict") != "CHANGES_REQUESTED"
            or len(normalized_review.get("blockers") or []) == 0
        ):
            raise HardCapExceededError(
                "NO_BLOCKER_FOR_FIX_PASS: fix pass requires verdict CHANGES_REQUESTED with at least one blocker",
                code="NO_BLOCKER_FOR_FIX_PASS",
            )

    if normalized_status in ("working", "idle") and reset_worktree:
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
    with _pool_state_lock(repo_root):
        existing_slots = _active_tasks_from_heartbeat(repo_root, epic_slug)
        raw_prev = existing_slots.get(slot_key) or existing_slots.get(str(slot))
        prev_entry: Mapping[str, Any] = raw_prev if isinstance(raw_prev, Mapping) else {}
        prev_status = str(prev_entry.get("status") or "").strip().lower()
        prev_task_id = prev_entry.get("task_id")

        if normalized_status == "idle":
            effective_task_id: str | None = None
        else:
            preserve_existing_task = normalized_status == "review" or not reset_worktree
            effective_task_id = task_id or (
                str(prev_task_id) if prev_task_id and preserve_existing_task else None
            )

        counters = _carry_forward_slot_counters(prev_entry)
        prev_review = int(counters["review_passes_used"])
        prev_fix = int(counters["fix_passes_used"])
        same_task = (effective_task_id or None) == (
            str(prev_task_id) if prev_task_id else None
        )

        if normalized_status == "idle" or (normalized_status == "working" and reset_worktree):
            counters = _default_slot_counters()
        elif normalized_status == "review":
            if prev_status == "review" and same_task:
                pass
            else:
                max_review_passes, _ = _resolve_task_review_limits(repo_root)
                if prev_review >= max_review_passes:
                    raise HardCapExceededError(
                        f"HARD_REVIEW_CAP_EXCEEDED: slot {slot} already used {prev_review}/{max_review_passes} review passes",
                        code="HARD_REVIEW_CAP_EXCEEDED",
                    )
                if prev_review == 1 and prev_fix == 0:
                    raise HardCapExceededError(
                        f"NO_FIX_PASS_BEFORE_REVIEW_PASS_2: slot {slot} cannot enter Review Pass 2 with fix_passes_used == 0",
                        code="NO_FIX_PASS_BEFORE_REVIEW_PASS_2",
                    )
                new_review = prev_review + 1
                counters["review_passes_used"] = new_review
                if prev_review == 0:
                    counters["pass1_tree_sha"] = capture_slot_tree_sha(slot_path, epic_dir)
                    counters["pass1_head_sha"] = _git_head_sha(slot_path)
        elif normalized_status == "working" and not reset_worktree:
            max_review_passes, max_fix_passes = _resolve_task_review_limits(repo_root)
            if prev_review >= 1 and prev_status == "review":
                if prev_fix >= max_fix_passes:
                    raise HardCapExceededError(
                        f"HARD_FIX_CAP_EXCEEDED: slot {slot} already used {prev_fix}/{max_fix_passes} fix passes",
                        code="HARD_FIX_CAP_EXCEEDED",
                    )
                counters["fix_passes_used"] = prev_fix + 1
                if normalized_review is not None:
                    counters["pass1_blockers"] = list(normalized_review["blockers"])
            elif prev_review == 0 or (prev_status == "working" and same_task):
                if prev_fix >= max_fix_passes and prev_review >= max_review_passes:
                    raise HardCapExceededError(
                        f"HARD_FIX_CAP_EXCEEDED: slot {slot} already used {prev_fix}/{max_fix_passes} fix passes",
                        code="HARD_FIX_CAP_EXCEEDED",
                    )
                if normalized_review is not None:
                    counters["pass1_blockers"] = list(normalized_review["blockers"])
            else:
                if prev_fix >= max_fix_passes:
                    raise HardCapExceededError(
                        f"HARD_FIX_CAP_EXCEEDED: slot {slot} already used {prev_fix}/{max_fix_passes} fix passes",
                        code="HARD_FIX_CAP_EXCEEDED",
                    )
                counters["fix_passes_used"] = prev_fix + 1
                if normalized_review is not None:
                    counters["pass1_blockers"] = list(normalized_review["blockers"])

        working_tasks = _collect_other_active_tasks(existing_slots, slot, slot_key)
        if effective_task_id:
            working_tasks.add(effective_task_id)

        slot_entry: dict[str, Any] = {
            "status": normalized_status,
            "branch": get_slot_branch(epic_slug, slot),
            "path": str(slot_path),
            "task_id": effective_task_id,
            **counters,
        }
        if normalized_status == "review":
            last_event = f"Reviewing {slot_key}" + (
                f" ({effective_task_id})" if effective_task_id else ""
            )
        elif normalized_status == "idle":
            last_event = f"Reset {slot_key} to idle"
        else:
            last_event = f"Synced {slot_key}" + (
                f" for {effective_task_id}" if effective_task_id else ""
            )
        _emit_pool_heartbeat(
            root,
            repo_root,
            epic_slug,
            active_wave=active_wave,
            active_tasks=sorted(working_tasks),
            slot_updates={slot_key: slot_entry},
            last_event=last_event,
        )
    return True


def _reconcile_main_wt_devtool_mirrors(main_wt: Path, epic_dir: str) -> None:
    """Restore tracked .devtool mirrors and remove untracked .devtool/features mirrors before merge."""
    tracked_scopes = [".devtool/features", f".devtool/epic/{epic_dir}"]
    diff_res = subprocess.run(
        ["git", "-c", "core.quotePath=false", "diff", "--name-only", "-z", "--", *tracked_scopes],
        cwd=main_wt,
        capture_output=True,
        check=False,
    )
    if diff_res.returncode == 0 and diff_res.stdout:
        tracked_dirty = [
            p for p in diff_res.stdout.decode("utf-8", "surrogateescape").split("\0") if p
        ]
        if tracked_dirty:
            subprocess.run(
                ["git", "checkout", "--", *tracked_dirty],
                cwd=main_wt,
                capture_output=True,
                check=False,
            )

    untracked_res = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            ".devtool/features",
        ],
        cwd=main_wt,
        capture_output=True,
        check=False,
    )
    if untracked_res.returncode == 0 and untracked_res.stdout:
        for rel in untracked_res.stdout.decode("utf-8", "surrogateescape").split("\0"):
            if not rel:
                continue
            target = main_wt / rel
            if target.is_file() or target.is_symlink():
                with contextlib.suppress(OSError):
                    target.unlink()


def append_review_audit_note(
    repo_root: Path,
    main_wt: Path,
    epic_dir: str,
    epic_slug: str,
    task_id: str,
    entry: Mapping[str, Any],
    *,
    commit: bool = True,
) -> Path:
    """Append a structured JSONL audit note in main_wt only and optionally commit it."""
    audit_rel = Path(".devtool") / "epic" / epic_dir / "review_audit_notes.jsonl"
    audit_path = main_wt / audit_rel
    record = dict(entry)
    record.setdefault("ts", _utc_now_iso())
    record.setdefault("epic_slug", epic_slug)
    record.setdefault("task_id", task_id)
    line = json.dumps(record, ensure_ascii=False) + "\n"

    with _devtool_memory_lock(repo_root):
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        with audit_path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())

        if commit:
            rel_posix = audit_rel.as_posix()
            subprocess.run(
                ["git", "add", "--", rel_posix],
                cwd=main_wt,
                capture_output=True,
                text=True,
                check=True,
            )
            diff_cached = subprocess.run(
                ["git", "diff", "--cached", "--quiet", "--", rel_posix],
                cwd=main_wt,
                capture_output=True,
                check=False,
            )
            if diff_cached.returncode != 0:
                commit_msg = f"[{epic_slug.upper()}] Record review audit note for {task_id}"
                subprocess.run(
                    ["git", "commit", "-m", commit_msg, "--", rel_posix],
                    cwd=main_wt,
                    capture_output=True,
                    text=True,
                    check=True,
                )
    return audit_path


def _is_test_file(rel_path: str) -> bool:
    norm = rel_path.replace("\\", "/").lstrip("./")
    if "/tests/" in f"/{norm}":
        return True
    name = PurePosixPath(norm).name
    if name.startswith("test_") and name.endswith(".py"):
        return True
    return name.endswith(("_test.py", ".spec.ts", ".test.ts"))


def _extract_diff_header_path(diff_git_line: str) -> str | None:
    """Extract relative path from a `diff --git a/<p> b/<p>` header produced with --no-renames."""
    prefix = "diff --git "
    if not diff_git_line.startswith(prefix):
        return None
    rest = diff_git_line[len(prefix) :]
    mid = len(rest) // 2
    if (
        len(rest) >= 5
        and len(rest) % 2 == 1
        and rest[mid] == " "
        and rest[:mid].startswith("a/")
        and rest[mid + 1 :].startswith("b/")
        and rest[2:mid] == rest[mid + 3 :]
    ):
        return rest[2:mid]
    return None


def _classify_tier1_diff(
    numstat_raw: bytes,
    unified_text: str,
) -> tuple[list[str], int, int, list[str], str | None]:
    non_test_changed_lines = 0
    test_changed_lines = 0
    changed_files: list[str] = []
    test_stats: dict[str, list[Any]] = {}

    tokens = numstat_raw.decode("utf-8", "surrogateescape").split("\0")
    for token in tokens:
        if not token:
            continue
        parts = token.split("\t", 2)
        if len(parts) != 3:
            continue
        ins_raw, del_raw, rel_path = parts
        ins = 0 if ins_raw == "-" else int(ins_raw)
        dels = 0 if del_raw == "-" else int(del_raw)
        changed = ins + dels
        changed_files.append(rel_path)
        if _is_test_file(rel_path):
            test_changed_lines += changed
            test_stats.setdefault(rel_path, [0, 0, False])
        else:
            non_test_changed_lines += changed

    fired: set[str] = set()
    if non_test_changed_lines > NON_TEST_DIFF_LINE_CAP:
        fired.add("NON_TEST_DIFF_OVER_30_LINES")

    non_test_sections: list[str] = []
    section_lines: list[str] = []
    current_file: str | None = None
    in_hunk = False

    def _flush_section() -> None:
        if not section_lines:
            return
        if current_file is None or not _is_test_file(current_file):
            non_test_sections.append("\n".join(section_lines))

    for line in unified_text.splitlines():
        if line.startswith("diff --git "):
            _flush_section()
            section_lines = [line]
            in_hunk = False
            current_file = _extract_diff_header_path(line)
            continue

        section_lines.append(line)
        if not in_hunk:
            if line.startswith("--- "):
                raw_old = line[4:].strip()
                if raw_old != "/dev/null" and raw_old.startswith("a/"):
                    current_file = raw_old[2:]
                continue
            if line.startswith("+++ "):
                raw_new = line[4:].strip()
                if raw_new != "/dev/null" and raw_new.startswith("b/"):
                    current_file = raw_new[2:]
                continue
            if line.startswith("@@ "):
                in_hunk = True
            continue

        if line.startswith("@@ "):
            continue
        if not line.startswith(("+", "-")):
            continue

        sign = line[0]
        stripped = line[1:]
        if current_file is None:
            continue

        if _is_test_file(current_file):
            stats = test_stats.setdefault(current_file, [0, 0, False])
            if _TEST_ASSERTION_RE.search(stripped):
                if sign == "+":
                    stats[0] += 1
                else:
                    stats[1] += 1
            if sign == "+" and _TEST_SKIP_RE.search(stripped):
                stats[2] = True
            continue

        if any(p.search(stripped) for p in _PUBLIC_SIGNATURE_RES):
            fired.add("PUBLIC_SIGNATURE_CHANGED")
        if any(p.search(stripped) for p in _API_SURFACE_RES):
            fired.add("API_ROUTE_OR_SCHEMA_CHANGED")
        if any(p.search(stripped) for p in _DB_SURFACE_RES):
            fired.add("DB_OR_PERSISTENCE_CHANGED")
        if any(p.search(stripped) for p in _CONCURRENCY_RES):
            fired.add("CONCURRENCY_OR_LOCKING_CHANGED")

    _flush_section()

    for added_asserts, removed_asserts, skip_added in test_stats.values():
        if (added_asserts - removed_asserts) < 0 or skip_added:
            fired.add("TEST_ASSERTION_WEAKENED")
            break

    triggers = [code for code in TIER1_TRIGGER_ORDER if code in fired]
    bounded_diff: str | None = None
    if not triggers:
        test_summaries = [
            f"# test-summary {tf}: +{stats[0]}/-{stats[1]} assertions, skip_added={stats[2]}"
            for tf, stats in sorted(test_stats.items())
        ]
        bounded_parts = [*non_test_sections, *test_summaries]
        bounded_diff = ("\n".join(bounded_parts) + "\n") if bounded_parts else ""
    return (
        triggers,
        non_test_changed_lines,
        test_changed_lines,
        sorted(set(changed_files)),
        bounded_diff,
    )


def triage_fix_slot(
    root: Path,
    epic_dir: str,
    epic_slug: str,
    slot: int,
    *,
    task_id: str | None = None,
    record_tier2: bool = False,
    risk_level: str | None = None,
    rationale: str | None = None,
    epic_worktree_root: Path | None = None,
) -> dict[str, Any]:
    """Run Tier 1 deterministic risk triage over `<pass1_tree_sha>..<curr_tree_sha>`."""
    repo_root, default_wt = resolve_pool_roots(root, epic_dir)
    main_wt = epic_worktree_root if epic_worktree_root is not None else default_wt
    slot_path = get_slot_path(repo_root, epic_dir, slot)
    if not slot_path.is_dir():
        raise RuntimeError(f"Slot {slot} worktree does not exist at {slot_path}")

    slot_key = f"slot-{slot}"
    with _pool_state_lock(repo_root):
        existing_slots = _active_tasks_from_heartbeat(repo_root, epic_slug)
        raw_entry = existing_slots.get(slot_key) or existing_slots.get(str(slot))
        entry: Mapping[str, Any] = raw_entry if isinstance(raw_entry, Mapping) else {}
        counters = _carry_forward_slot_counters(entry)
        effective_task_id = task_id or (
            str(entry.get("task_id")) if entry.get("task_id") else None
        )
        pass1_tree_sha = counters.get("pass1_tree_sha")
        if not pass1_tree_sha:
            raise RuntimeError(
                f"Slot {slot} has no captured pass1_tree_sha; run sync --status review first"
            )
        fix_passes_used = int(counters.get("fix_passes_used", 0))
        if fix_passes_used != 1:
            raise RuntimeError(
                f"Slot {slot} requires fix_passes_used == 1 before triage-fix (got {counters.get('fix_passes_used', 0)})"
            )
        pass1_blockers = list(counters.get("pass1_blockers") or [])

    curr_tree_sha = capture_slot_tree_sha(slot_path, epic_dir)
    diff_pathspecs = [
        ".",
        *(f":(exclude){cdir}" for cdir in CACHE_DIR_CANDIDATES),
        *(f":(exclude)**/{cdir}" for cdir in CACHE_DIR_CANDIDATES),
        f":(exclude).devtool/epic/{epic_dir}/evidence",
        f":(exclude).devtool/epic/{epic_dir}/review_audit_notes*",
        ":(exclude).devtool/state",
    ]
    numstat_res = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "diff",
            "--no-ext-diff",
            "--no-color",
            "--no-renames",
            "--numstat",
            "-z",
            str(pass1_tree_sha),
            curr_tree_sha,
            "--",
            *diff_pathspecs,
        ],
        cwd=slot_path,
        capture_output=True,
        check=True,
    )
    unified_res = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "diff",
            "--no-ext-diff",
            "--no-color",
            "--no-renames",
            "--unified=0",
            str(pass1_tree_sha),
            curr_tree_sha,
            "--",
            *diff_pathspecs,
        ],
        cwd=slot_path,
        capture_output=True,
        text=True,
        check=True,
    )
    unified_text = unified_res.stdout
    triggers, non_test_lines, test_lines, changed_files, bounded_diff = _classify_tier1_diff(
        numstat_res.stdout,
        unified_text,
    )

    tier1_status = "HIGH_RISK" if triggers else "ELIGIBLE_FOR_SHORT_CIRCUIT"
    if tier1_status != "ELIGIBLE_FOR_SHORT_CIRCUIT":
        bounded_diff = None

    normalized_risk: str | None = None
    if record_tier2:
        normalized_risk = (risk_level or "").strip().upper()
        if normalized_risk not in ("MEDIUM", "HIGH"):
            raise ValueError(
                f"--record-tier2 requires --risk-level MEDIUM or HIGH, got {risk_level!r}"
            )

    last_triage_summary: dict[str, Any] = {
        "tier1_status": tier1_status,
        "triggers": triggers,
        "non_test_changed_lines": non_test_lines,
        "test_changed_lines": test_lines,
        "changed_files": changed_files,
        "curr_tree_sha": curr_tree_sha,
    }
    if normalized_risk is not None:
        last_triage_summary["tier2_risk_level"] = normalized_risk
        last_triage_summary["tier2_rationale"] = rationale or ""

    with _pool_state_lock(repo_root):
        existing_slots = _active_tasks_from_heartbeat(repo_root, epic_slug)
        raw_entry = existing_slots.get(slot_key) or existing_slots.get(str(slot))
        cur_entry: dict[str, Any] = (
            dict(raw_entry) if isinstance(raw_entry, Mapping) else {}
        )
        cur_entry["last_triage"] = last_triage_summary
        _emit_pool_heartbeat(
            root,
            repo_root,
            epic_slug,
            slot_updates={slot_key: cur_entry},
            last_event=f"Triage {slot_key} -> {tier1_status}",
        )

    if record_tier2 and normalized_risk is not None:
        if not main_wt.is_dir():
            raise RuntimeError(f"Main epic worktree does not exist at {main_wt}")
        append_review_audit_note(
            repo_root,
            main_wt,
            epic_dir,
            epic_slug,
            effective_task_id or "unknown",
            {
                "event": "tier2_risk_assessment",
                "task_id": effective_task_id,
                "slot": slot,
                "tier1_status": tier1_status,
                "risk_level": normalized_risk,
                "rationale": rationale or "",
                "pass1_tree_sha": pass1_tree_sha,
                "curr_tree_sha": curr_tree_sha,
            },
            commit=True,
        )

    result: dict[str, Any] = {
        "task_id": effective_task_id,
        "slot": slot,
        "pass1_tree_sha": pass1_tree_sha,
        "curr_tree_sha": curr_tree_sha,
        "tier1_status": tier1_status,
        "triggers": triggers,
        "non_test_changed_lines": non_test_lines,
        "test_changed_lines": test_lines,
        "changed_files": changed_files,
        "pass1_blockers": pass1_blockers,
        "bounded_diff": bounded_diff,
    }
    if normalized_risk is not None:
        result["tier2_recorded"] = True
        result["risk_level"] = normalized_risk
        result["rationale"] = rationale or ""
    return result


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
    """Reconcile main_wt .devtool mirrors, merge slot branch into epic worktree, and reset slot."""
    repo_root, default_wt = resolve_pool_roots(root, epic_dir)
    main_wt = epic_worktree_root if epic_worktree_root is not None else default_wt
    if not main_wt.is_dir():
        return False

    slot_branch = get_slot_branch(epic_slug, slot)
    slot_key = f"slot-{slot}"

    with _devtool_memory_lock(repo_root):
        _reconcile_main_wt_devtool_mirrors(main_wt, epic_dir)

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

        with _pool_state_lock(repo_root):
            existing_slots = _active_tasks_from_heartbeat(repo_root, epic_slug)
            working_tasks = sorted(_collect_other_active_tasks(existing_slots, slot, slot_key))
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
                        **_default_slot_counters(),
                    }
                },
                last_event=f"Merged {slot_key}" + (f" ({task_id})" if task_id else ""),
            )
    return True


def _resolve_dev_script(slot_path: Path, repo_root: Path, script_name: str) -> Path:
    for base in (slot_path, repo_root):
        cand = base / "skills" / "dev-implementation" / "resources" / "scripts" / script_name
        if cand.is_file():
            return cand
    return Path(__file__).resolve().parent / script_name


def _find_epic_doc(epic_root: Path, stems: list[str]) -> Path | None:
    for stem in stems:
        for suffix in (".md", ".en.md"):
            cand = epic_root / f"{stem}{suffix}"
            if cand.is_file():
                return cand
    return None


def _resolve_slot_task_mirror(
    slot_path: Path,
    epic_dir: str,
    task_id: str,
) -> tuple[Path | None, str]:
    """Resolve a task markdown mirror inside slot_path by exact name or unique prefix."""
    clean_id = task_id.strip()
    if (
        not clean_id
        or "/" in clean_id
        or "\\" in clean_id
        or clean_id in (".", "..")
    ):
        return None, task_id

    slot_epic_dir = slot_path / ".devtool" / "epic" / epic_dir
    if slot_epic_dir.is_dir():
        exact_epic = slot_epic_dir / f"{clean_id}.md"
        if exact_epic.is_file() and not exact_epic.name.endswith(".vi.md"):
            return exact_epic, exact_epic.stem
        epic_matches = [
            cand
            for cand in sorted(slot_epic_dir.glob(f"{clean_id}_*.md"))
            if cand.is_file() and not cand.name.endswith(".vi.md")
        ]
        if len(epic_matches) == 1:
            return epic_matches[0], epic_matches[0].stem
        if len(epic_matches) > 1:
            return None, task_id

    features_dir = slot_path / ".devtool" / "features"
    done_dir = features_dir / "done"
    for directory in (features_dir, done_dir):
        if not directory.is_dir():
            continue
        exact_feat = directory / f"{clean_id}.md"
        if exact_feat.is_file() and not exact_feat.name.endswith(".vi.md"):
            return exact_feat, exact_feat.stem

    prefix_matches: list[Path] = []
    for directory in (features_dir, done_dir):
        if not directory.is_dir():
            continue
        prefix_matches.extend(
            cand
            for cand in sorted(directory.glob(f"{clean_id}_*.md"))
            if cand.is_file() and not cand.name.endswith(".vi.md")
        )
    if len(prefix_matches) == 1:
        return prefix_matches[0], prefix_matches[0].stem
    return None, task_id


def _run_finalize_mechanical_gates(
    slot_path: Path,
    repo_root: Path,
    epic_dir: str,
    epic_slug: str,
    task_id: str,
) -> str | None:
    """Verify run_task_checks.py status and check_bdd_traceability.py inside slot_path."""
    slot_epic_dir = slot_path / ".devtool" / "epic" / epic_dir
    task_mirror, _ = _resolve_slot_task_mirror(slot_path, epic_dir, task_id)
    if task_mirror is None or not task_mirror.is_file():
        return f"MECHANICAL_GATE_FAILED: task file not found for {task_id}"

    rtc_script = _resolve_dev_script(slot_path, repo_root, "run_task_checks.py")
    if not rtc_script.is_file():
        return "MECHANICAL_GATE_FAILED: run_task_checks.py not found"
    rtc_res = subprocess.run(
        [sys.executable, "-B", str(rtc_script), "status", str(task_mirror)],
        cwd=slot_path,
        capture_output=True,
        text=True,
        check=False,
    )
    if rtc_res.returncode != 0 or "done gate: PASS" not in (rtc_res.stdout or ""):
        detail = (rtc_res.stdout or rtc_res.stderr or f"exit {rtc_res.returncode}").strip()
        return f"MECHANICAL_GATE_FAILED: run_task_checks.py status failed ({detail})"

    cbt_script = _resolve_dev_script(slot_path, repo_root, "check_bdd_traceability.py")
    if cbt_script.is_file():
        task_text = task_mirror.read_text(encoding="utf-8")
        covers_ids: list[str] = []
        for line in task_text.splitlines():
            m = _COVERS_LINE_RE.match(line)
            if m:
                covers_ids.extend(_ID_TOKEN_RE.findall(m.group(1)))

        scenario_file = _find_epic_doc(slot_epic_dir, ["bdd_scenarios"])
        if covers_ids and scenario_file is not None:
            hld_file = _find_epic_doc(slot_epic_dir, [epic_dir, epic_slug])
            roots: list[str] = []
            if hld_file is not None:
                for line in hld_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("Integration test roots:"):
                        raw_val = line.split(":", 1)[1]
                        roots = [
                            tok
                            for part in raw_val.split(",")
                            for tok in part.split()
                            if tok.strip()
                        ]
                        break
            if not roots and (slot_path / "tests").is_dir():
                roots = ["tests"]
            existing_roots = [r for r in roots if (slot_path / r).is_dir()]
            if existing_roots:
                cbt_res = subprocess.run(
                    [
                        sys.executable,
                        "-B",
                        str(cbt_script),
                        "tests",
                        "--scenarios",
                        str(scenario_file),
                        "--roots",
                        *existing_roots,
                        "--ids",
                        *covers_ids,
                    ],
                    cwd=slot_path,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if cbt_res.returncode != 0:
                    detail = (cbt_res.stdout or cbt_res.stderr or f"exit {cbt_res.returncode}").strip()
                    return f"MECHANICAL_GATE_FAILED: check_bdd_traceability.py failed ({detail})"
    return None


def finalize_slot(
    root: Path,
    epic_dir: str,
    epic_slug: str,
    slot: int,
    task_id: str,
    *,
    mode: str = "pass1-approved",
    risk_level: str | None = None,
    rationale: str | None = None,
    review_payload: Mapping[str, Any] | None = None,
    active_wave: int | None = None,
    epic_worktree_root: Path | None = None,
) -> dict[str, Any]:
    """Verify mechanical gates, mark task done, commit slot, merge to main_wt, and record main_wt audit notes."""
    if mode not in FINALIZE_MODES:
        raise ValueError(f"Unsupported finalize mode {mode!r}; expected one of {FINALIZE_MODES}")

    effective_risk: str | None = None
    if mode == "tier2-short-circuit":
        effective_risk = (risk_level or "LOW").strip().upper()
        if effective_risk != "LOW":
            raise ValueError(
                f"tier2-short-circuit requires risk_level LOW, got {risk_level!r}"
            )
    elif risk_level is not None:
        effective_risk = risk_level.strip().upper()

    repo_root, default_wt = resolve_pool_roots(root, epic_dir)
    main_wt = epic_worktree_root if epic_worktree_root is not None else default_wt
    slot_path = get_slot_path(repo_root, epic_dir, slot)

    if not slot_path.is_dir():
        return {"ok": False, "error": f"Slot {slot} worktree not found at {slot_path}"}
    if not main_wt.is_dir():
        return {"ok": False, "error": f"Main epic worktree not found at {main_wt}"}

    gate_error = _run_finalize_mechanical_gates(
        slot_path, repo_root, epic_dir, epic_slug, task_id
    )
    if gate_error is not None:
        return {
            "ok": False,
            "code": "MECHANICAL_GATE_FAILED",
            "error": gate_error,
            "task_id": task_id,
            "slot": slot,
            "mode": mode,
            "merged": False,
        }

    norm_review = (
        normalize_task_review_payload(review_payload)
        if review_payload is not None
        else None
    )
    if (
        mode == "pass1-approved"
        and norm_review is not None
        and (
            not norm_review.get("valid")
            or norm_review.get("verdict") != "APPROVED"
            or norm_review.get("blockers")
        )
    ):
        return {
            "ok": False,
            "code": "MECHANICAL_GATE_FAILED",
            "error": "MECHANICAL_GATE_FAILED: pass1-approved requires an APPROVED review payload with zero blockers",
            "task_id": task_id,
            "slot": slot,
            "mode": mode,
            "merged": False,
        }

    if mode == "tier2-short-circuit":
        slot_key = f"slot-{slot}"
        with _pool_state_lock(repo_root):
            existing_slots = _active_tasks_from_heartbeat(repo_root, epic_slug)
            raw_entry = existing_slots.get(slot_key) or existing_slots.get(str(slot))
            entry: Mapping[str, Any] = raw_entry if isinstance(raw_entry, Mapping) else {}
            counters = _carry_forward_slot_counters(entry)
        last_triage = counters.get("last_triage")
        triage_ok = (
            int(counters.get("fix_passes_used", 0)) == 1
            and isinstance(last_triage, Mapping)
            and last_triage.get("tier1_status") == "ELIGIBLE_FOR_SHORT_CIRCUIT"
        )
        if triage_ok and isinstance(last_triage, Mapping):
            curr_tree_sha = capture_slot_tree_sha(slot_path, epic_dir)
            triage_ok = bool(curr_tree_sha) and curr_tree_sha == last_triage.get("curr_tree_sha")
        if not triage_ok:
            return {
                "ok": False,
                "code": "TIER1_SHORT_CIRCUIT_NOT_ELIGIBLE",
                "error": "MECHANICAL_GATE_FAILED: tier2-short-circuit requires prior triage-fix ELIGIBLE_FOR_SHORT_CIRCUIT on current slot tree",
                "task_id": task_id,
                "slot": slot,
                "mode": mode,
                "merged": False,
            }

    sync_script = _resolve_dev_script(slot_path, repo_root, "sync_task_status.py")
    task_mirror, resolved_task_id = _resolve_slot_task_mirror(slot_path, epic_dir, task_id)
    if sync_script.is_file() and task_mirror is not None and task_mirror.is_file():
        sync_res = subprocess.run(
            [sys.executable, "-B", str(sync_script), "task", resolved_task_id, "done"],
            cwd=slot_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if sync_res.returncode != 0:
            detail = (sync_res.stderr or sync_res.stdout or f"exit {sync_res.returncode}").strip()
            return {
                "ok": False,
                "code": "MECHANICAL_GATE_FAILED",
                "error": f"MECHANICAL_GATE_FAILED: sync_task_status failed ({detail})",
                "task_id": task_id,
                "slot": slot,
                "mode": mode,
                "merged": False,
            }

    add_specs = [
        ".",
        f":!.devtool/epic/{epic_dir}/review_audit_notes*",
    ]
    for cdir in CACHE_DIR_CANDIDATES:
        candidate = slot_path / cdir
        if candidate.is_symlink():
            add_specs.append(f":!{cdir}")

    subprocess.run(
        ["git", "add", "-A", "--", *add_specs],
        cwd=slot_path,
        capture_output=True,
        text=True,
        check=True,
    )
    cached_check = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=slot_path,
        capture_output=True,
        check=False,
    )
    if cached_check.returncode != 0:
        commit_title = f"[{epic_slug.upper()}] Complete {task_id}"
        subprocess.run(
            ["git", "commit", "-m", commit_title],
            cwd=slot_path,
            capture_output=True,
            text=True,
            check=True,
        )

    merged = merge_slot(
        root,
        epic_dir,
        epic_slug,
        slot,
        task_id=task_id,
        epic_worktree_root=main_wt,
        active_wave=active_wave,
    )
    if not merged:
        return {
            "ok": False,
            "error": f"MERGE_FAILED: failed to merge slot {slot} into {main_wt}",
            "task_id": task_id,
            "slot": slot,
            "mode": mode,
            "merged": False,
        }

    audit_entry: dict[str, Any] | None = None
    if mode == "tier2-short-circuit":
        audit_entry = {
            "event": "tier2_short_circuit",
            "mode": mode,
            "task_id": task_id,
            "slot": slot,
            "risk_level": effective_risk or "LOW",
            "rationale": rationale or "",
        }
        if norm_review is not None and norm_review.get("observations"):
            audit_entry["observations"] = norm_review["observations"]
    elif mode == "pass2-complete":
        if norm_review is not None and (
            norm_review.get("verdict") == "CHANGES_REQUESTED" or norm_review.get("blockers")
        ):
            audit_entry = {
                "event": "pass2_residual_logged_on_cap",
                "mode": mode,
                "task_id": task_id,
                "slot": slot,
                "verdict": norm_review.get("verdict"),
                "blockers": norm_review.get("blockers", []),
                "observations": norm_review.get("observations", []),
                "rationale": rationale or "",
            }
        elif norm_review is not None and norm_review.get("observations"):
            audit_entry = {
                "event": "pass2_observations",
                "mode": mode,
                "task_id": task_id,
                "slot": slot,
                "observations": norm_review["observations"],
                "rationale": rationale or "",
            }
        elif rationale:
            audit_entry = {
                "event": "pass2_complete",
                "mode": mode,
                "task_id": task_id,
                "slot": slot,
                "rationale": rationale,
            }
    elif mode == "pass1-approved":
        if norm_review is not None and (
            norm_review.get("coerced_from_non_blocking") or norm_review.get("observations")
        ):
            audit_entry = {
                "event": (
                    "coerced_non_blocking_approval"
                    if norm_review.get("coerced_from_non_blocking")
                    else "pass1_observations"
                ),
                "mode": mode,
                "task_id": task_id,
                "slot": slot,
                "coerced_from_non_blocking": bool(
                    norm_review.get("coerced_from_non_blocking")
                ),
                "observations": norm_review.get("observations", []),
                "rationale": rationale or "",
            }
        elif rationale:
            audit_entry = {
                "event": "pass1_approved",
                "mode": mode,
                "task_id": task_id,
                "slot": slot,
                "rationale": rationale,
            }

    audit_path_str: str | None = None
    if audit_entry is not None:
        audit_path = append_review_audit_note(
            repo_root,
            main_wt,
            epic_dir,
            epic_slug,
            task_id,
            audit_entry,
            commit=True,
        )
        audit_path_str = str(audit_path)

    return {
        "ok": True,
        "task_id": task_id,
        "slot": slot,
        "mode": mode,
        "merged": True,
        "audit_note_recorded": audit_entry is not None,
        "audit_notes_path": audit_path_str,
        "head_sha": _git_head_sha(main_wt),
    }


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
            dirty = st.returncode != 0 or bool(st.stdout.strip())

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
            if not wt_exists:
                subprocess.run(
                    ["git", "worktree", "prune"],
                    cwd=repo_root,
                    capture_output=True,
                    check=False,
                )
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


def _load_sync_review_payload(
    review_file: str | None,
    blockers_file: str | None,
) -> Mapping[str, Any] | None:
    if review_file:
        raw_text = Path(review_file).read_text(encoding="utf-8")
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, Mapping) else {}
    if blockers_file:
        raw_text = Path(blockers_file).read_text(encoding="utf-8")
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, list):
            return {
                "verdict": "CHANGES_REQUESTED",
                "done_gate": "PASS",
                "blockers": parsed,
            }
        if isinstance(parsed, Mapping):
            if "verdict" in parsed:
                return parsed
            if "blockers" in parsed:
                return {
                    "verdict": "CHANGES_REQUESTED",
                    "done_gate": parsed.get("done_gate", "PASS"),
                    "blockers": parsed["blockers"],
                }
            return parsed
        return {}
    return None


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
    p_sync = subparsers.add_parser("sync", help="Reset slot or update slot heartbeat status")
    _add_epic_flags(p_sync)
    p_sync.add_argument("--slot", type=int, required=True, help="Slot number (1 or 2)")
    p_sync.add_argument("--base", default=None, help="Base ref to sync to (default: epic/<epic_slug>)")
    p_sync.add_argument("--task", default=None, help="Task ID assigned to this slot")
    p_sync.add_argument("--wave", type=int, default=None, help="Active execution wave number")
    p_sync.add_argument(
        "--status",
        choices=SLOT_SYNC_STATUSES,
        default="working",
        help="Slot heartbeat state ('working'/'idle' reset worktree by default; 'review' preserves uncommitted work)",
    )
    p_sync.add_argument(
        "--no-reset",
        action="store_false",
        dest="reset_worktree",
        default=True,
        help="Update heartbeat status/task without resetting the slot git worktree",
    )
    p_sync.add_argument("--review-file", default=None, help="Optional reviewer JSON payload file")
    p_sync.add_argument("--blockers-file", default=None, help="Optional blockers JSON file")

    # triage-fix
    p_triage = subparsers.add_parser("triage-fix", help="Run Tier 1 heuristic risk triage on Fix Pass 1")
    _add_epic_flags(p_triage)
    p_triage.add_argument("--slot", type=int, required=True, help="Slot number (1 or 2)")
    p_triage.add_argument("--task", default=None, help="Task ID assigned to this slot")
    p_triage.add_argument("--format", choices=("json",), default="json", help="Output format")
    p_triage.add_argument("--record-tier2", action="store_true", help="Record Tier 2 escalation note to main_wt")
    p_triage.add_argument("--risk-level", default=None, help="Tier 2 risk level (MEDIUM or HIGH)")
    p_triage.add_argument("--rationale", default=None, help="Tier 2 RiskAssessment rationale")

    # finalize-slot
    p_fin = subparsers.add_parser("finalize-slot", help="Verify gates, mark task done, commit, merge, and log audit notes")
    _add_epic_flags(p_fin)
    p_fin.add_argument("--slot", type=int, required=True, help="Slot number (1 or 2)")
    p_fin.add_argument("--task", required=True, help="Task ID being finalized")
    p_fin.add_argument("--wave", type=int, default=None, help="Active execution wave number")
    p_fin.add_argument(
        "--mode",
        choices=FINALIZE_MODES,
        default="pass1-approved",
        help="Finalization path",
    )
    p_fin.add_argument("--risk-level", default=None, help="Tier 2 risk level (LOW for tier2-short-circuit)")
    p_fin.add_argument("--rationale", default=None, help="Tier 2 or review rationale")
    p_fin.add_argument("--review-file", default=None, help="Optional reviewer JSON file")

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
        try:
            review_payload = _load_sync_review_payload(
                args.review_file, args.blockers_file
            )
            ok = sync_slot(
                root,
                epic_dir,
                epic_slug,
                args.slot,
                base_ref=args.base,
                task_id=args.task,
                active_wave=args.wave,
                status=args.status,
                reset_worktree=args.reset_worktree,
                review_payload=review_payload,
            )
        except HardCapExceededError as exc:
            detail = str(exc)
            line = (
                detail
                if detail.startswith(f"{exc.code}:")
                else f"{exc.code}: {detail}"
            )
            print(line, file=sys.stderr)
            return HARD_CAP_EXIT_CODE

        if ok:
            if args.status == "review":
                print(f"Slot {args.slot} heartbeat marked as review")
            elif args.status == "idle" and not args.reset_worktree:
                print(f"Slot {args.slot} heartbeat marked as idle (worktree preserved)")
            elif args.status == "idle":
                print(f"Slot {args.slot} reset to idle at {args.base or f'epic/{epic_slug}'}")
            elif not args.reset_worktree:
                print(f"Slot {args.slot} heartbeat marked as {args.status} (worktree preserved)")
            else:
                print(f"Slot {args.slot} synchronized to latest {args.base or f'epic/{epic_slug}'}")
            return 0
        print(f"Failed to sync slot {args.slot}", file=sys.stderr)
        return 1

    if args.command == "triage-fix":
        try:
            triage_report = triage_fix_slot(
                root,
                epic_dir,
                epic_slug,
                args.slot,
                task_id=args.task,
                record_tier2=args.record_tier2,
                risk_level=args.risk_level,
                rationale=args.rationale,
            )
        except (RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
            print(f"triage-fix failed: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(triage_report, indent=2))
        return 0

    if args.command == "finalize-slot":
        rev_payload: Mapping[str, Any] | None = None
        if args.review_file:
            rev_payload = _load_sync_review_payload(args.review_file, None)
        try:
            fin_report = finalize_slot(
                root,
                epic_dir,
                epic_slug,
                args.slot,
                args.task,
                mode=args.mode,
                risk_level=args.risk_level,
                rationale=args.rationale,
                review_payload=rev_payload,
                active_wave=args.wave,
            )
        except (RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
            print(f"finalize-slot failed: {exc}", file=sys.stderr)
            return 1
        if fin_report.get("ok"):
            print(json.dumps(fin_report, indent=2))
            return 0
        print(str(fin_report.get("error") or "MECHANICAL_GATE_FAILED"), file=sys.stderr)
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

