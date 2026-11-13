"""Multi-repo harvester engine and data models for check-tasks dashboard.

Provides high-performance multi-repo discovery, git worktree parsing,
.vscode styling extraction, task progress aggregation, and two-tier project memory inspection.
"""

from __future__ import annotations

import concurrent.futures
import contextlib
from dataclasses import dataclass, field
import datetime
from datetime import datetime, timezone
from enum import Enum
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
_STATE_ENVELOPE_MOD: Any | None = None
_SLOT_SUFFIX_RE = re.compile(r"-slot-\d+$")
_PIC_PLACEHOLDERS = frozenset(
    {
        "",
        "none",
        "null",
        "unassigned",
        "unknown",
        "profile_account_id",
        "n/a",
        "tbd",
        "pending",
    }
)


def _load_state_envelope() -> Any | None:
    """Lazily import shared `scripts/_state_envelope.py` without failing on standalone copies."""
    global _STATE_ENVELOPE_MOD
    if _STATE_ENVELOPE_MOD is not None:
        return _STATE_ENVELOPE_MOD
    for parent in [SCRIPT_DIR, *SCRIPT_DIR.parents]:
        cand_scripts = parent / "scripts"
        if (cand_scripts / "_state_envelope.py").is_file():
            if str(cand_scripts) not in sys.path:
                sys.path.insert(0, str(cand_scripts))
            try:
                _STATE_ENVELOPE_MOD = importlib.import_module("_state_envelope")
                return _STATE_ENVELOPE_MOD
            except Exception:  # noqa: S110
                return None
    return None

def _real_home() -> Path:
    """Host user's real HOME, derived (never hard-coded); strips /antigravity_homes/<profile> when inside a profile."""
    home = str(Path.home())
    return Path(home.split("/antigravity_homes")[0]) if "/antigravity_homes" in home else Path(home)


get_real_home = _real_home


def discover_antigravity_profiles(real_home: str | Path | None = None) -> list[str]:
    """Discover all actual Antigravity profile accounts following /check-quota mechanism."""
    # 1. Try delegating to scripts/agy_quota.py (check-quota Single Source of Truth) if on default host home
    if real_home is None:
        for parent in [SCRIPT_DIR] + list(SCRIPT_DIR.parents):
            cand_scripts = parent / "scripts"
            if (cand_scripts / "agy_quota.py").is_file():
                if str(cand_scripts) not in sys.path:
                    sys.path.insert(0, str(cand_scripts))
                break
        try:
            import agy_quota  # type: ignore

            if hasattr(agy_quota, "get_all_profiles"):
                q_profiles = agy_quota.get_all_profiles()
                if q_profiles and isinstance(q_profiles, list):
                    allowed = [
                        p
                        for p in q_profiles
                        if p not in ("claude", "codex", "kiro", "anthropic", "openai")
                    ]
                    if allowed:
                        return sorted(list(set(allowed)))
        except Exception:
            pass

    # 2. Direct discovery matching check-quota's exact rules (supports custom real_home for tests/profiles)
    r_home = Path(real_home) if real_home is not None else _real_home()
    homes_dir = r_home / "antigravity_homes"
    profiles: list[str] = []
    reserved_non_profiles = {
        "Library", "System", "Shared", "AllProjects", "Projects", "fvm",
        "claude", "codex", "kiro", "anthropic", "openai", ".gemini", ".antigravity",
        ".antigravity-ide", "bin", "etc", "var", "tmp", "opt", ".Trash"
    }

    if homes_dir.is_dir():
        for entry in sorted(homes_dir.iterdir()):
            if entry.name.startswith(".") or entry.name.startswith("-") or entry.is_symlink() or not entry.is_dir():
                continue
            if entry.name in reserved_non_profiles:
                continue
            if not re.match(r"^[a-zA-Z0-9_\-]+$", entry.name):
                continue
            if (
                (entry / ".gemini").exists()
                or (entry / ".antigravity").exists()
                or (entry / "data").exists()
                or (entry / "Library" / "Keychains").exists()
            ):
                profiles.append(entry.name)

    zshrc_path = r_home / ".zshrc"
    if zshrc_path.is_file():
        try:
            content = zshrc_path.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r"antigravity_homes/([a-zA-Z0-9_\-]+)", content):
                p = m.group(1)
                if (homes_dir / p).is_dir() and p not in reserved_non_profiles and p not in profiles:
                    profiles.append(p)
            for m2 in re.finditer(r"^alias\s+([a-zA-Z0-9_\-]+)='ag_run\s+([a-zA-Z0-9_\-]+)'", content, re.MULTILINE):
                p2 = m2.group(2)
                if (homes_dir / p2).is_dir() and p2 not in reserved_non_profiles and p2 not in profiles:
                    profiles.append(p2)
        except Exception:
            pass

    return sorted(list(set(profiles)))


def _build_clean_host_env() -> dict[str, str]:
    """Environment for launching the daemon: real HOME, no leaked IDE/Electron/profile variables.

    Kept local on purpose: scripts/tasks_server.py is a thin wrapper that shadows the real
    tasks_server module on sys.path, so importing it from here is unreliable.
    """
    env = dict(os.environ)
    env["HOME"] = str(_real_home())
    for key in ("AGY_PROFILE", "AGY_CLI_MODE", "AGY_ENABLE_HUB", "TERM_PROGRAM",
                "TERM_PROGRAM_VERSION", "TERM_SESSION_ID", "TMPDIR", "ZDOTDIR"):
        env.pop(key, None)
    for key in list(env):
        if key.startswith(("VSCODE_", "ANTIGRAVITY_", "ELECTRON_", "CHROME_")):
            env.pop(key, None)
    return env


CANONICAL_SIGNATURES: dict[str, str] = {
    "ai-agent-tools": "#b45309",
    "lyrics-sync": "#7f1d1d",
    "nexus": "#0d47a1",
    "D3Nexus": "#065f46",
}

VALID_STATUSES: set[str] = {"backlog", "todo", "in-progress", "review", "done"}


@dataclass
class WorktreeMetadata:
    """Metadata representing a single Git working tree."""

    path: str
    branch: str | None
    head_sha: str
    is_dirty: bool
    dirty_file_count: int
    is_detached: bool


@dataclass
class TaskProgress:
    """Aggregated Kanban task progress for a repository or active epic."""

    total_tasks: int
    done_tasks: int
    in_progress_tasks: int
    todo_tasks: int
    backlog_tasks: int = 0
    review_tasks: int = 0
    percentage: float = 0.0
    active_task_name: str | None = None
    tasks: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TwoTierMemory:
    """Two-tier project memory snapshot for cross-session continuity."""

    project_ledger_path: str | None
    total_milestones: int
    last_milestone: str | None
    assistant_state_role: str | None
    assistant_state_status: str | None


@dataclass
class EpicsSummary:
    """High-level summary of all epics belonging to the repository."""

    total: int = 0
    completed: int = 0
    in_progress: int = 0
    unstarted: int = 0
    abandoned: int = 0
    epics: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RepoMetadata:
    """Complete metadata and state snapshot for a single repository."""

    name: str
    path: str
    theme_color: str
    window_title: str
    active_epic: str | None
    active_stage: str | None
    worktrees: list[WorktreeMetadata]
    task_progress: TaskProgress
    memory: TwoTierMemory | None = None
    contract_status: str | None = None
    account_id: str | None = None
    quick_note: str | None = None
    prompt: str | None = None
    epics_summary: EpicsSummary | None = None
    is_human_action_required: bool = False
    is_blocked: bool = False
    pending_decision: dict[str, Any] | None = None
    heartbeat: dict[str, Any] | None = None
    quality_active: dict[str, Any] | None = None
    quality_runs: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DashboardGraph:
    """Unified graph data model representing all harvested repositories."""

    workspace_root: str
    scanned_at: str
    repos: list[RepoMetadata]
    metrics_row: dict[str, Any] = field(default_factory=dict)
    available_profiles: list[str] = field(default_factory=list)


class LifecycleStage(str, Enum):
    """Canonical lifecycle stages across the 5-approval-gate dev-lifecycle state machine."""

    STAGE_1_INCEPTION = "Stage 1 (Inception)"
    STAGE_2_ARCHITECTURE = "Stage 2 (Architecture)"
    STAGE_2_EXIT_HANDOFF = "Stage 2 Exit (Handoff)"
    STAGE_2_REVIEW_TRIAGE = "Stage 2 (Review Triage)"
    STAGE_3_PHASE_1_ORDER = "Stage 3 Phase 1 (Order & Worktree)"
    STAGE_3_PHASE_2_TDD = "Stage 3 Phase 2 (TDD)"
    STAGE_3_PHASE_4_REVIEW = "Stage 3 Phase 4 (Review)"
    STAGE_3_PHASE_4_1_SIGNOFF = "Stage 3 Phase 4.1 (Sign-off)"
    IDLE = "Idle"


@dataclass
class LifecycleDecision:
    """Deterministic lifecycle decision derived for human-agent collaboration."""

    stage_name: str
    gate_status: str
    prompt: str
    is_human_action_required: bool
    is_blocked: bool = False


def normalize_task_status(status: str | None) -> str:
    """Normalize task status to canonical hyphenated lowercase format."""
    if not status:
        return "backlog"
    normalized = status.strip().lower().replace("_", "-")
    if normalized in VALID_STATUSES:
        return normalized
    return "backlog"


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse YAML frontmatter between triple dashes without external YAML libraries."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fm: dict[str, Any] = {}
    for line in lines[1:]:
        line_s = line.strip()
        if line_s == "---":
            break
        if not line_s or line_s.startswith("#") or ":" not in line_s:
            continue
        key, val = line_s.split(":", 1)
        k = key.strip()
        v = val.strip().strip("'\"")
        fm[k] = v
    return fm


def extract_vscode_styling(repo_path: Path) -> tuple[str, str]:
    """Extract theme color and window title from .vscode/settings.json or fallback defaults."""
    settings_file = repo_path / ".vscode" / "settings.json"
    color: str | None = None
    title: str | None = None

    if settings_file.is_file():
        with contextlib.suppress(OSError, json.JSONDecodeError):
            data = json.loads(settings_file.read_text(encoding="utf-8"))
            customizations = data.get("workbench.colorCustomizations", {})
            color = customizations.get(
                "titleBar.activeBackground"
            ) or customizations.get("statusBar.background")
            title = data.get("window.title")

    if not color:
        color = CANONICAL_SIGNATURES.get(repo_path.name)
        if not color:
            # Deterministic color generation based on repo name
            h = hashlib.md5(repo_path.name.encode("utf-8")).hexdigest()
            color = f"#{h[:6]}"

    if not title:
        title = repo_path.name

    return color, title


def scan_worktrees(repo_path: Path) -> list[WorktreeMetadata]:
    """Discover all git worktrees and detect uncommitted modifications."""
    worktrees: list[WorktreeMetadata] = []
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_path), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return worktrees

    raw_blocks = proc.stdout.strip().split("\n\n")
    for block in raw_blocks:
        if not block.strip():
            continue
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        wt_path: str = ""
        head_sha: str = ""
        branch: str | None = None
        is_detached: bool = False

        for line in lines:
            if line.startswith("worktree "):
                wt_path = line.split("worktree ", 1)[1].strip()
            elif line.startswith("HEAD "):
                head_sha = line.split("HEAD ", 1)[1].strip()[:7]
            elif line.startswith("branch "):
                ref = line.split("branch ", 1)[1].strip()
                branch = ref.replace("refs/heads/", "")
            elif line == "detached":
                is_detached = True

        if not branch:
            is_detached = True

        # Check dirty status
        is_dirty = False
        dirty_file_count = 0
        if wt_path and Path(wt_path).is_dir():
            with contextlib.suppress(subprocess.SubprocessError, OSError):
                st = subprocess.run(
                    ["git", "-C", wt_path, "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                dirty_lines = [l for l in st.stdout.splitlines() if l.strip()]
                is_dirty = len(dirty_lines) > 0
                dirty_file_count = len(dirty_lines)

        if wt_path:
            worktrees.append(
                WorktreeMetadata(
                    path=wt_path,
                    branch=branch,
                    head_sha=head_sha,
                    is_dirty=is_dirty,
                    dirty_file_count=dirty_file_count,
                    is_detached=is_detached,
                )
            )

    return worktrees


def extract_epic_hld_status(epic_dir: Path, slug: str) -> str | None:
    """Extract epic lifecycle status from HLD design documents (.en.md, .vi.md, or *.md)."""
    candidates = [epic_dir / f"{slug}.en.md", epic_dir / f"{slug}.vi.md"]
    with contextlib.suppress(OSError):
        for f in epic_dir.glob("*.md"):
            if f not in candidates and not f.name.startswith("task_") and f.name != "handoff.md":
                candidates.append(f)

    for hld in candidates:
        if not hld.is_file():
            continue
        with contextlib.suppress(OSError):
            text = hld.read_text(encoding="utf-8")
            m = re.search(
                r"-\s+\*\*(?:Status|Trạng thái)\*\*:\s*`?([^\n\r`]+)",
                text,
                re.IGNORECASE,
            )
            if m:
                val = m.group(1).strip().lower()
                if val.startswith("done") or val.startswith("completed") or "hoàn thành" in val:
                    return "done"
                if any(k in val for k in ("discard", "abandon", "cancel", "hủy")):
                    return "abandon"
                if "progress" in val:
                    return "in_progress"
                if "package" in val:
                    return "packaged"
                if any(k in val for k in ("todo", "backlog", "chờ", "unstarted")):
                    return "unstarted"
    return None


def get_completed_epic_slugs(repo_path: Path) -> set[str]:
    """Harvest completed epic slugs from PROJECT_LEDGER.md, archive, and HLD design documents."""
    completed: set[str] = set()

    # 1. Check .devtool/PROJECT_LEDGER.md
    ledger_file = repo_path / ".devtool" / "PROJECT_LEDGER.md"
    if ledger_file.is_file():
        with contextlib.suppress(OSError):
            content = ledger_file.read_text(encoding="utf-8")
            for m in re.finditer(
                r"-\s+\*\*\[\d{4}-\d{2}-\d{2}\]\s+`?([a-zA-Z0-9_\-]+)`?\*\*:",
                content,
            ):
                completed.add(m.group(1).strip())

    # 2. Check .devtool/archive/ for archived state/activity/epic records
    archive_dir = repo_path / ".devtool" / "archive"
    if archive_dir.is_dir():
        with contextlib.suppress(OSError):
            for f in archive_dir.iterdir():
                m_arch = re.match(r"(?:state|activity)_([a-zA-Z0-9_\-]+)_\d{8}_\d{4}\.", f.name)
                if m_arch:
                    completed.add(m_arch.group(1).strip())

    # 3. Check HLD design documents in .devtool/epic/<slug>/ (Status: Done)
    epic_dir = repo_path / ".devtool" / "epic"
    if epic_dir.is_dir():
        with contextlib.suppress(OSError):
            for d in epic_dir.iterdir():
                if not d.is_dir() or d.name.startswith("."):
                    continue
                if extract_epic_hld_status(d, d.name) == "done":
                    completed.add(d.name)

    return completed


def _normalize_slug(slug: str) -> str:
    """Normalize epic slugs for robust comparison across dash/underscore conventions."""
    return slug.strip().lower().replace("_", "-")


def _strip_slot_suffix(name: str) -> str:
    """Strip ephemeral slot suffixes (e.g. '-slot-1') from branch or worktree names."""
    return _SLOT_SUFFIX_RE.sub("", name.strip())


def _is_completed_epic(slug: str, completed_slugs: set[str]) -> bool:
    """Return True if slug matches any completed epic across dash/underscore forms."""
    if not slug:
        return False
    norm = _normalize_slug(slug)
    return slug in completed_slugs or any(_normalize_slug(c) == norm for c in completed_slugs)


def _resolve_canonical_epic_slug(repo_path: Path, candidate: str) -> str:
    """Resolve a stripped slug to the canonical `.devtool/epic/` directory name if present."""
    clean = _strip_slot_suffix(candidate)
    if not clean:
        return clean
    epic_root = repo_path / ".devtool" / "epic"
    if not epic_root.is_dir():
        return clean
    if (epic_root / clean).is_dir():
        return clean
    target_norm = _normalize_slug(clean)
    with contextlib.suppress(OSError):
        for entry in sorted(epic_root.iterdir()):
            if (
                entry.is_dir()
                and not entry.name.startswith(".")
                and _normalize_slug(entry.name) == target_norm
            ):
                return entry.name
    return clean


def _collect_matching_worktrees(
    repo_path: Path, epic_slug: str | None = None
) -> list[Path]:
    """Discover unique non-root worktrees matching `epic_slug` (or all worktrees when None)."""
    results: list[Path] = []
    seen: set[Path] = set()
    root_resolved = repo_path.resolve()
    target_norm = _normalize_slug(_strip_slot_suffix(epic_slug)) if epic_slug else None

    def _maybe_add(candidate_path: Path, branch_name: str | None = None) -> None:
        if not candidate_path.is_dir():
            return
        resolved = candidate_path.resolve()
        if resolved == root_resolved or resolved in seen:
            return
        if target_norm is not None:
            dir_norm = _normalize_slug(_strip_slot_suffix(candidate_path.name))
            branch_match = False
            if branch_name:
                m_br = re.match(r"(?:epic|feat)/([a-zA-Z0-9_\-]+)", branch_name)
                if m_br:
                    branch_match = (
                        _normalize_slug(_strip_slot_suffix(m_br.group(1)))
                        == target_norm
                    )
            if dir_norm != target_norm and not branch_match:
                return
        seen.add(resolved)
        results.append(candidate_path)

    for wt in scan_worktrees(repo_path):
        _maybe_add(Path(wt.path), wt.branch)

    wt_dir = repo_path / ".worktrees"
    if wt_dir.is_dir():
        with contextlib.suppress(OSError):
            for d in sorted(wt_dir.iterdir()):
                if not d.is_dir() or d.name.startswith("."):
                    continue
                _maybe_add(d)

    return results


def _collect_devtool_dirs(
    repo_path: Path, active_epic: str | None = None
) -> list[Path]:
    """Collect unique `.devtool` directories across root, worktrees, and git common dir."""
    dirs: list[Path] = []
    seen: set[Path] = set()

    def _add_dir(devtool_dir: Path) -> None:
        if not devtool_dir.is_dir():
            return
        resolved = devtool_dir.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        dirs.append(devtool_dir)

    _add_dir(repo_path / ".devtool")
    for wt_path in _collect_matching_worktrees(repo_path, active_epic):
        _add_dir(wt_path / ".devtool")

    state_env = _load_state_envelope()
    if state_env is not None:
        with contextlib.suppress(Exception):
            for shared_dir in state_env.resolve_shared_devtool_dirs(repo_path):
                _add_dir(shared_dir)

    return dirs


def _read_state_snapshot(
    repo_path: Path,
    filename: str,
    default: dict[str, Any],
    active_epic: str | None = None,
) -> dict[str, Any]:
    """Select the highest-generation state snapshot across root, worktrees, and common dir."""
    state_env = _load_state_envelope()
    collected_dirs = _collect_devtool_dirs(repo_path, active_epic)
    if state_env is not None:
        seen = {d.resolve() for d in collected_dirs if d.is_dir()}
        with contextlib.suppress(Exception):
            for extra in state_env._collect_target_devtool_dirs(repo_path, filename):
                if extra.is_dir() and extra.resolve() not in seen:
                    seen.add(extra.resolve())
                    collected_dirs.append(extra)
        if not collected_dirs:
            return dict(default)
        snapshot, _ = state_env._read_highest_snapshot(collected_dirs, filename, default)
        return dict(snapshot)

    best_snapshot: dict[str, Any] = {}
    best_gen = -1
    for devtool_dir in collected_dirs:
        candidate_path = devtool_dir / "state" / filename
        if not candidate_path.is_file():
            continue
        with contextlib.suppress(OSError, json.JSONDecodeError, UnicodeDecodeError):
            parsed = json.loads(candidate_path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict) and parsed:
                gen = parsed.get("generation", 0)
                gen_num = gen if isinstance(gen, int) and not isinstance(gen, bool) else 0
                if gen_num > best_gen:
                    best_gen = gen_num
                    best_snapshot = parsed
    merged = dict(default)
    merged.update(best_snapshot)
    return merged


def _match_pending_decision_for_epic(
    snapshot: dict[str, Any], epic_slug: str | None
) -> dict[str, Any] | None:
    """Return the active pending decision matching `epic_slug`, ignoring sibling epics."""
    if not snapshot or not epic_slug:
        return None

    target_norm = _normalize_slug(epic_slug)
    decisions = snapshot.get("decisions")
    if isinstance(decisions, dict) and decisions:
        exact_match = decisions.get(epic_slug)
        if isinstance(exact_match, dict):
            return dict(exact_match) if exact_match.get("active", True) is True else None
        for key, entry in decisions.items():
            if not isinstance(entry, dict):
                continue
            entry_epic = str(entry.get("epic") or key)
            if _normalize_slug(entry_epic) == target_norm:
                return dict(entry) if entry.get("active", True) is True else None
        return None

    # Legacy single-record fallback when no namespaced decisions exist
    if snapshot.get("active") is True:
        legacy_epic = snapshot.get("epic")
        if not legacy_epic or _normalize_slug(str(legacy_epic)) == target_norm:
            return dict(snapshot)
    return None


def _resolve_active_epic_from_pending_decision(
    repo_path: Path, completed_slugs: set[str]
) -> str | None:
    """Resolve an active non-completed epic recorded in `pending_decision.json`."""
    snapshot = _read_state_snapshot(repo_path, "pending_decision.json", {})
    if not snapshot:
        return None

    decisions = snapshot.get("decisions")
    if isinstance(decisions, dict) and decisions:
        candidates: list[tuple[str, str]] = []
        for key, entry in decisions.items():
            if not isinstance(entry, dict) or entry.get("active", True) is not True:
                continue
            ep = str(entry.get("epic") or key).strip()
            if not ep or _is_completed_epic(ep, completed_slugs):
                continue
            stamp = str(entry.get("updated_at") or entry.get("created_at") or "")
            candidates.append((stamp, ep))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return _resolve_canonical_epic_slug(repo_path, candidates[0][1])

    if snapshot.get("active") is True and snapshot.get("epic"):
        ep = str(snapshot["epic"]).strip()
        if ep and not _is_completed_epic(ep, completed_slugs):
            return _resolve_canonical_epic_slug(repo_path, ep)
    return None


def resolve_active_epic(repo_path: Path) -> str | None:
    """Derive active epic from worktrees, branches, active snapshots, pending decisions, or features."""
    # 0. Get completed slugs from PROJECT_LEDGER.md, archive, and HLD Status: Done
    completed_slugs = get_completed_epic_slugs(repo_path)

    # 1. Check current branch or worktree branches for epic/<slug> or feat/<slug>
    for wt in scan_worktrees(repo_path):
        if wt.branch:
            m_br = re.match(r"(?:epic|feat)/([a-zA-Z0-9_\-]+)", wt.branch)
            if m_br:
                raw_slug = _strip_slot_suffix(m_br.group(1))
                if raw_slug and not _is_completed_epic(raw_slug, completed_slugs):
                    return _resolve_canonical_epic_slug(repo_path, raw_slug)

    # 2. Check active worktrees under .worktrees/ (prioritize worktrees with git changes or tasks)
    wt_dir = repo_path / ".worktrees"
    if wt_dir.is_dir():
        for d in sorted(wt_dir.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue

            # Check git status for modified files in .devtool/epic/<slug>
            with contextlib.suppress(Exception):
                res = subprocess.run(
                    ["git", "-C", str(d), "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    check=False,
                )
                for line in res.stdout.splitlines():
                    m_epic = re.search(r"\.devtool/epic/([a-zA-Z0-9_\-]+)/", line)
                    if m_epic:
                        slug = m_epic.group(1).strip()
                        if not _is_completed_epic(slug, completed_slugs):
                            return _resolve_canonical_epic_slug(repo_path, slug)

            # Check tasks inside worktree features
            wt_feat = d / ".devtool" / "features"
            if wt_feat.is_dir():
                for tf in sorted(wt_feat.glob("task_*.md")):
                    with contextlib.suppress(OSError):
                        fm = parse_frontmatter(tf.read_text(encoding="utf-8"))
                        ep = fm.get("epic")
                        if ep and ep != "general" and not _is_completed_epic(ep, completed_slugs):
                            return _resolve_canonical_epic_slug(repo_path, ep)

            # Check if directory name (stripped of slot suffix) matches an epic
            base_name = _strip_slot_suffix(d.name)
            canonical = _resolve_canonical_epic_slug(repo_path, base_name)
            if (repo_path / ".devtool" / "epic" / canonical).is_dir():
                if not _is_completed_epic(canonical, completed_slugs):
                    return canonical

    # 3. Check assistant_state.md, skipping placeholder "general" and completed epics
    state_file = repo_path / ".devtool" / "assistant_state.md"
    if state_file.is_file():
        with contextlib.suppress(OSError):
            content = state_file.read_text(encoding="utf-8")
            for m in re.finditer(r"#\s*Active Epic:\s*([a-zA-Z0-9_\-]+)", content):
                slug = m.group(1).strip()
                if slug and slug != "general" and not _is_completed_epic(slug, completed_slugs):
                    return _resolve_canonical_epic_slug(repo_path, slug)

    # 4. Check state folder for non-general state files in deterministic order
    state_dir = repo_path / ".devtool" / "state"
    if state_dir.is_dir():
        for sf in sorted(state_dir.glob("*.md")):
            if sf.stem != "general" and not _is_completed_epic(sf.stem, completed_slugs):
                return _resolve_canonical_epic_slug(repo_path, sf.stem)

    # 5. Check .worktrees directory in deterministic order (any worktree not completed)
    if wt_dir.is_dir():
        for d in sorted(wt_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                base_name = _strip_slot_suffix(d.name)
                if base_name and not _is_completed_epic(base_name, completed_slugs):
                    return _resolve_canonical_epic_slug(repo_path, base_name)

    # 5.5 Check explicit active pending_decision.json entries
    pending_epic = _resolve_active_epic_from_pending_decision(repo_path, completed_slugs)
    if pending_epic:
        return pending_epic

    # 6. Check .devtool/features/*.md for epic frontmatter
    features_dir = repo_path / ".devtool" / "features"
    if features_dir.is_dir():
        for tf in sorted(features_dir.glob("task_*.md")):
            with contextlib.suppress(OSError):
                fm = parse_frontmatter(tf.read_text(encoding="utf-8"))
                ep = fm.get("epic")
                if ep and ep != "general" and not _is_completed_epic(ep, completed_slugs):
                    return _resolve_canonical_epic_slug(repo_path, ep)

    return None


def find_epic_worktree_path(repo_path: Path, active_epic: str | None) -> Path:
    """Locate dedicated worktree directory (.worktrees/<epic_name>) for the active epic, falling back to repo root."""
    if not active_epic:
        return repo_path

    candidates = [
        repo_path / ".worktrees" / active_epic,
        repo_path / ".worktrees" / active_epic.replace("-", "_"),
        repo_path / ".worktrees" / active_epic.replace("_", "-"),
    ]
    for c in candidates:
        if c.is_dir():
            return c

    for wt in scan_worktrees(repo_path):
        wp = Path(wt.path)
        if wp.name in (
            active_epic,
            active_epic.replace("-", "_"),
            active_epic.replace("_", "-"),
        ):
            return wp
        if wt.branch and (
            f"epic/{active_epic}" in wt.branch
            or f"feat/{active_epic}" in wt.branch
            or active_epic in wt.branch
        ):
            return wp

        # Check if worktree has active changes in .devtool/epic/<active_epic>
        with contextlib.suppress(Exception):
            res = subprocess.run(
                ["git", "-C", str(wp), "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if f".devtool/epic/{active_epic}" in res.stdout:
                return wp

    return repo_path


def harvest_epics_overview(repo_path: Path) -> EpicsSummary:
    """Harvest high-level project epics summary and status breakdown from the root repository."""
    epic_dir = repo_path / ".devtool" / "epic"
    completed_slugs = get_completed_epic_slugs(repo_path)

    epics: list[dict[str, Any]] = []
    if epic_dir.is_dir():
        for d in sorted(epic_dir.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            slug = d.name
            hld_status = extract_epic_hld_status(d, slug)
            has_wt = (
                (repo_path / ".worktrees" / slug).is_dir()
                or (repo_path / ".worktrees" / slug.replace("-", "_")).is_dir()
                or (repo_path / ".worktrees" / slug.replace("_", "-")).is_dir()
            )

            # Status determination (HLD status is SSOT for Done/Abandon)
            if hld_status == "done" or slug in completed_slugs:
                status = "done"
            elif hld_status in ("abandon", "packaged"):
                status = hld_status
            elif has_wt:
                status = "in_progress"
            elif hld_status == "in_progress":
                status = "in_progress"
            else:
                status = "unstarted"

            # Title
            title = slug
            for hld in [d / f"{slug}.vi.md", d / f"{slug}.en.md"]:
                if hld.is_file():
                    with contextlib.suppress(OSError):
                        for line in hld.read_text(encoding="utf-8").splitlines():
                            if line.startswith("# "):
                                raw = line.lstrip("#").strip()
                                if raw.lower().startswith("epic:"):
                                    raw = raw[5:].strip()
                                title = raw
                                break
                        if title != slug:
                            break

            task_count = len(list(d.glob("task_*.md")))
            pic = extract_epic_pic(repo_path, slug)

            # Last updated mtime calculation
            mtimes = [f.stat().st_mtime for f in d.iterdir() if f.is_file()]
            max_mtime = max(mtimes) if mtimes else d.stat().st_mtime
            for wt_candidate in [
                repo_path / ".worktrees" / slug,
                repo_path / ".worktrees" / slug.replace("-", "_"),
                repo_path / ".worktrees" / slug.replace("_", "-"),
            ]:
                if wt_candidate.is_dir():
                    features_dir = wt_candidate / ".devtool" / "features"
                    if features_dir.is_dir():
                        wt_mtimes = [f.stat().st_mtime for f in features_dir.glob("task_*.md")]
                        if wt_mtimes:
                            max_mtime = max(max_mtime, max(wt_mtimes))
                    break

            last_updated_dt = datetime.fromtimestamp(max_mtime, tz=timezone.utc)
            last_updated_iso = last_updated_dt.isoformat()
            last_updated_human = format_relative_time(last_updated_iso)

            epics.append(
                {
                    "slug": slug,
                    "title": title,
                    "status": status,
                    "has_worktree": has_wt,
                    "task_count": task_count,
                    "pic": pic,
                    "mtime": max_mtime,
                    "last_updated": last_updated_iso,
                    "last_updated_human": last_updated_human,
                }
            )

    # Sort epics: 1. In-progress, 2. Backlog, 3. Done, 4. Abandon
    # Secondary: Last updated mtime descending (newest first)
    def epic_sort_key(e: dict[str, Any]) -> tuple[int, float, str]:
        st = e.get("status", "").lower()
        if "progress" in st:
            rank = 1
        elif st in ("abandon", "abandoned", "discarded", "cancelled"):
            rank = 4
        elif st in ("done", "completed"):
            rank = 3
        else:  # backlog / unstarted / packaged / draft
            rank = 2
        return (rank, -float(e.get("mtime", 0.0)), e.get("slug", ""))

    epics.sort(key=epic_sort_key)

    total = len(epics)
    completed = sum(1 for e in epics if e["status"] == "done")
    in_prog = sum(1 for e in epics if e["status"] == "in_progress")
    abandoned = sum(1 for e in epics if e["status"] in ("abandon", "abandoned", "discarded"))
    unstarted = total - completed - in_prog - abandoned
    return EpicsSummary(
        total=total,
        completed=completed,
        in_progress=in_prog,
        unstarted=unstarted,
        abandoned=abandoned,
        epics=epics,
    )

def format_relative_time(iso_str: str | None) -> str:
    """Format ISO timestamp to compact days and hours without ago (e.g. 1d3h, 5d, 12h, 45m)."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(str(iso_str).replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        secs = int(diff.total_seconds())
        if secs < 0:
            secs = 0
        if secs < 60:
            return "just now"
        if secs < 3600:
            return f"{secs // 60}m"
        if secs < 86400:
            hours = secs // 3600
            mins = (secs % 3600) // 60
            if mins > 0 and hours < 6:
                return f"{hours}h{mins}m"
            return f"{hours}h"
        days = secs // 86400
        hours = (secs % 86400) // 3600
        if hours > 0:
            return f"{days}d{hours}h"
        return f"{days}d"
    except Exception:
        return str(iso_str)[:10]


def natural_sort_key(val: Any) -> list[int | str]:
    """Natural sort key ensuring numbers sort numerically (e.g. 1, 2, ..., 9, 10, 11)."""
    s = val.name if hasattr(val, "name") else str(val)
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def extract_task_progress(repo_path: Path, active_epic: str | None) -> TaskProgress:
    """Harvest comprehensive Kanban tasks across active and backlog epics according to 2-tier governance.

    1. Scan epics in .devtool/epic/ in root repo (backlog, todo, in_progress).
    2. For backlog epics: keep root task information.
    3. For active epic in worktree: fetch latest detailed tasks from worktree.
    """
    epic_dir = repo_path / ".devtool" / "epic"
    completed_slugs = get_completed_epic_slugs(repo_path)

    candidate_epics: list[str] = []
    if active_epic:
        candidate_epics.append(active_epic)

    if epic_dir.is_dir():
        for d in sorted(epic_dir.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            slug = d.name
            if slug in completed_slugs and slug != active_epic:
                continue
            if slug not in candidate_epics:
                candidate_epics.append(slug)

    # Fallback if no .devtool/epic exists (e.g. unit test mocks)
    if not candidate_epics:
        if active_epic:
            candidate_epics.append(active_epic)
        else:
            features_dir = repo_path / ".devtool" / "features"
            if features_dir.is_dir():
                for tf in sorted(features_dir.glob("task_*.md"), key=natural_sort_key):
                    with contextlib.suppress(Exception):
                        fm = parse_frontmatter(tf.read_text(encoding="utf-8"))
                        ep = fm.get("epic")
                        if ep and ep not in candidate_epics:
                            candidate_epics.append(ep)

    seen_tasks: set[str] = set()
    tally = {"backlog": 0, "todo": 0, "in-progress": 0, "review": 0, "done": 0}
    active_task: str | None = None
    all_tasks: list[dict[str, Any]] = []

    # Build fast worktree lookup table supporting slot suffixes and linked worktrees
    known_wts: dict[str, list[Path]] = {}
    wt_seen: dict[str, set[Path]] = {}

    def _register_wt(key_raw: str, wt_path_obj: Path) -> None:
        if not wt_path_obj.is_dir():
            return
        resolved = wt_path_obj.resolve()
        for k in (
            key_raw,
            _strip_slot_suffix(key_raw),
            _normalize_slug(_strip_slot_suffix(key_raw)),
        ):
            if not k:
                continue
            bucket_seen = wt_seen.setdefault(k, set())
            if resolved not in bucket_seen:
                bucket_seen.add(resolved)
                known_wts.setdefault(k, []).append(wt_path_obj)

    wt_dir = repo_path / ".worktrees"
    if wt_dir.is_dir():
        for item in sorted(wt_dir.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                _register_wt(item.name, item)

    for wt_meta in scan_worktrees(repo_path):
        wt_p = Path(wt_meta.path)
        if wt_p.is_dir() and wt_p.resolve() != repo_path.resolve():
            _register_wt(wt_p.name, wt_p)
            if wt_meta.branch:
                m_br = re.match(r"(?:epic|feat)/([a-zA-Z0-9_\-]+)", wt_meta.branch)
                if m_br:
                    _register_wt(m_br.group(1), wt_p)

    # Rule 3: For active epic(s) with dedicated worktrees, fetch detailed tasks from worktree
    for ep in candidate_epics:
        ep_wts = known_wts.get(ep) or known_wts.get(_normalize_slug(ep)) or []
        for ep_wt in ep_wts:
            if not ep_wt.is_dir():
                continue
            for d in [
                ep_wt / ".devtool" / "features",
                ep_wt / ".devtool" / "features" / "done",
                ep_wt / ".devtool" / "epic" / ep,
            ]:
                if not d.is_dir():
                    continue
                for tf in sorted(d.glob("task_*.md"), key=natural_sort_key):
                    task_id = tf.stem
                    if task_id in seen_tasks:
                        continue
                    with contextlib.suppress(OSError):
                        content = tf.read_text(encoding="utf-8")
                        fm = parse_frontmatter(content)
                        task_epic = fm.get("epic")
                        if task_epic and task_epic not in (
                            ep,
                            ep.replace("_", "-"),
                            ep.replace("-", "_"),
                        ):
                            continue
                        elif not task_epic and d.name != ep and ep not in str(d):
                            continue

                        seen_tasks.add(task_id)
                        status = normalize_task_status(fm.get("status"))
                        tally[status] = tally.get(status, 0) + 1

                        title = task_id
                        for line in content.splitlines():
                            if line.strip().startswith("# "):
                                title = line.strip().lstrip("# ").strip()
                                break

                        labels = fm.get("labels", [])
                        if isinstance(labels, str):
                            try:
                                labels = json.loads(labels)
                            except Exception:
                                labels = [labels]

                        time_val = format_relative_time(
                            fm.get("completedAt") or fm.get("modified") or fm.get("created")
                        )

                        all_tasks.append(
                            {
                                "id": task_id,
                                "title": title,
                                "status": status,
                                "priority": fm.get("priority", "medium"),
                                "epic": ep,
                                "labels": labels,
                                "time": time_val,
                                "source": "worktree",
                            }
                        )

                        if status == "in-progress" and not active_task:
                            active_task = title

    # Rule 2: For backlog epics, keep root task information
    root_dirs = [
        repo_path / ".devtool" / "features",
        repo_path / ".devtool" / "features" / "done",
    ]
    for d in root_dirs:
        if not d.is_dir():
            continue
        for tf in sorted(d.glob("task_*.md"), key=natural_sort_key):
            task_id = tf.stem
            if task_id in seen_tasks:
                continue
            with contextlib.suppress(OSError):
                content = tf.read_text(encoding="utf-8")
                fm = parse_frontmatter(content)
                task_epic = fm.get("epic") or "backlog"
                if candidate_epics:
                    norm_candidates = {_normalize_slug(e) for e in candidate_epics}
                    if _normalize_slug(task_epic) not in norm_candidates:
                        continue

                seen_tasks.add(task_id)
                status = normalize_task_status(fm.get("status"))
                tally[status] = tally.get(status, 0) + 1

                title = task_id
                for line in content.splitlines():
                    if line.strip().startswith("# "):
                        title = line.strip().lstrip("# ").strip()
                        break

                labels = fm.get("labels", [])
                if isinstance(labels, str):
                    try:
                        labels = json.loads(labels)
                    except Exception:
                        labels = [labels]

                time_val = format_relative_time(
                    fm.get("completedAt") or fm.get("modified") or fm.get("created")
                )

                all_tasks.append(
                    {
                        "id": task_id,
                        "title": title,
                        "status": status,
                        "priority": fm.get("priority", "medium"),
                        "epic": task_epic,
                        "labels": labels,
                        "time": time_val,
                        "source": "root",
                    }
                )

                if status == "in-progress" and not active_task:
                    active_task = title

    # Sort all_tasks in natural numerical count order (e.g. Task 1, 2, ..., 9, 10, 11)
    def task_compare_key(t: dict[str, Any]) -> tuple[str, list[int | str]]:
        epic_name = str(t.get("epic") or "").lower()
        task_str = str(t.get("id") or t.get("title") or "")
        return (epic_name, natural_sort_key(task_str))

    all_tasks.sort(key=task_compare_key)

    # Re-derive active_task as the first in-progress task in natural numerical order
    active_task = None
    for t in all_tasks:
        if t.get("status") == "in-progress":
            active_task = t.get("title")
            break

    total = len(seen_tasks)
    done = tally["done"]
    in_prog = tally["in-progress"]
    todo = tally["todo"]
    backlog = tally["backlog"]
    review = tally["review"]
    if total <= 0:
        pct = 0.0
    elif done >= total:
        pct = 100.0 if _is_epic_converged_or_done(repo_path, active_epic) else 96.0
    else:
        pct = min(95.0, round((done / total * 100), 1))

    return TaskProgress(
        total_tasks=total,
        done_tasks=done,
        in_progress_tasks=in_prog,
        todo_tasks=todo,
        backlog_tasks=backlog,
        review_tasks=review,
        percentage=pct,
        active_task_name=active_task,
        tasks=all_tasks,
    )


def extract_two_tier_memory(repo_path: Path) -> TwoTierMemory:
    """Inspect Two-Tier memory files (.devtool/PROJECT_LEDGER.md and assistant_state.md)."""
    ledger_file = repo_path / ".devtool" / "PROJECT_LEDGER.md"
    total_milestones = 0
    last_milestone: str | None = None

    if ledger_file.is_file():
        with contextlib.suppress(OSError):
            content = ledger_file.read_text(encoding="utf-8")
            milestones = [
                l.strip() for l in content.splitlines() if l.strip().startswith("- **[")
            ]
            total_milestones = len(milestones)
            if milestones:
                last_milestone = milestones[-1]

    state_file = repo_path / ".devtool" / "assistant_state.md"
    role: str | None = None
    status: str | None = None

    if state_file.is_file():
        with contextlib.suppress(OSError):
            content = state_file.read_text(encoding="utf-8")
            m_role = re.search(r"Role:\s*([a-zA-Z0-9_\-]+)", content)
            if m_role:
                role = m_role.group(1).strip()

            lines = content.splitlines()
            for i, line in enumerate(lines):
                if line.strip() == "## Repo/Task Status:":
                    if i + 1 < len(lines):
                        status = lines[i + 1].strip().lstrip("- ").strip()
                    break

    return TwoTierMemory(
        project_ledger_path=str(ledger_file) if ledger_file.is_file() else None,
        total_milestones=total_milestones,
        last_milestone=last_milestone,
        assistant_state_role=role,
        assistant_state_status=status,
    )


def extract_repo_note(repo_path: Path) -> str | None:
    """Extract persistent idea/notes scratchpad from .devtool/IDEAS.md if available."""
    note_file = repo_path / ".devtool" / "IDEAS.md"
    if note_file.is_file():
        with contextlib.suppress(OSError):
            lines = [
                l.strip()
                for l in note_file.read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.strip().startswith("#")
            ]
            if lines:
                return "\n".join(lines)
    return None


_UNSET: Any = object()


_ACTIVE_EPIC_SECTION_RE = re.compile(r"(?im)^#\s*Active Epic\s*:\s*([^\n]+)")


def _filter_rollup_state_for_epic(text: str, active_epic: str | None) -> str:
    """Scope rollup `assistant_state.md` text to sections matching active_epic."""
    if not active_epic:
        return text
    matches = list(_ACTIVE_EPIC_SECTION_RE.finditer(text))
    if not matches:
        return text
    target_norm = re.sub(r"[-_]+", "_", active_epic.strip().lower())
    selected: list[str] = []
    for idx, match in enumerate(matches):
        raw_header = match.group(1).strip().strip("`").strip()
        slug_token = raw_header.split()[0].strip("`") if raw_header else ""
        header_norm = re.sub(r"[-_]+", "_", slug_token.lower())
        if header_norm != target_norm:
            continue
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        block = re.sub(r"(?:\n---\s*)+\Z", "", block).strip()
        if block:
            selected.append(block)
    return "\n".join(selected)


def _read_combined_state_text(repo_path: Path, active_epic: str | None) -> str:
    """Combine `assistant_state.md` and epic state markdown across root and worktrees."""
    chunks: list[str] = []
    seen_files: set[Path] = set()
    state_names = ["assistant_state.md"]
    epic_variants: list[str] = []
    if active_epic:
        for candidate in (
            active_epic,
            active_epic.replace("-", "_"),
            active_epic.replace("_", "-"),
        ):
            if candidate not in epic_variants:
                epic_variants.append(candidate)

    for devtool_dir in _collect_devtool_dirs(repo_path, active_epic):
        cand_files: list[Path] = [devtool_dir / name for name in state_names]
        for variant in epic_variants:
            cand_files.append(devtool_dir / "state" / f"{variant}.md")
        for sf in cand_files:
            if not sf.is_file():
                continue
            resolved = sf.resolve()
            if resolved in seen_files:
                continue
            seen_files.add(resolved)
            with contextlib.suppress(OSError, UnicodeDecodeError):
                content = sf.read_text(encoding="utf-8")
                if sf.name == "assistant_state.md":
                    content = _filter_rollup_state_for_epic(content, active_epic)
                if content:
                    chunks.append(content)
    return "\n".join(chunks)


def _has_review_converged_hint(
    repo_path: Path,
    active_epic: str | None,
    pending_decision: dict[str, Any] | None = None,
) -> bool:
    """Return True if runtime state or matching pending decision signals Stage 4 readiness."""
    lower_state = _read_combined_state_text(repo_path, active_epic).lower()
    markers = ("review converged", "gate 5", "sign-off", "stage 4", "finish")
    if any(marker in lower_state for marker in markers):
        return True
    if pending_decision and pending_decision.get("active", True) is True:
        pd_text = " ".join(
            str(pending_decision.get(k, "")).lower()
            for k in ("kind", "stage", "reason")
        )
        if any(m in pd_text for m in ("gate 5", "sign-off", "stage 4", "finish")):
            return True
    return False


def _is_epic_converged_or_done(repo_path: Path, active_epic: str | None) -> bool:
    """Return True only when active_epic is completed or Gate 4+ converged / Gate 5 passed."""
    if not active_epic:
        return False
    completed_slugs = get_completed_epic_slugs(repo_path)
    if _is_completed_epic(active_epic, completed_slugs):
        return True
    gates = parse_gate_ledger_entries(repo_path, active_epic)
    approved = {int(g["gate"]) for g in gates if "gate" in g}
    if 5 in approved:
        return True
    if 4 in approved:
        pd_snapshot = _read_state_snapshot(repo_path, "pending_decision.json", {})
        matched_pd = _match_pending_decision_for_epic(pd_snapshot, active_epic)
        return _has_review_converged_hint(repo_path, active_epic, matched_pd)
    return False


def _read_jsonl_ledger_file(
    jsonl_path: Path, norm_active: str | None
) -> list[dict[str, Any]]:
    """Read matching gate ledger records from a `gate_ledger.jsonl` file."""
    rows: list[dict[str, Any]] = []
    if not jsonl_path.is_file():
        return rows
    with contextlib.suppress(OSError, UnicodeDecodeError):
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            with contextlib.suppress(json.JSONDecodeError, TypeError, ValueError):
                data = json.loads(line_str)
                if not isinstance(data, dict) or "gate" not in data:
                    continue
                int(data["gate"])
                epic = str(data.get("epic", "")).strip()
                if not norm_active or not epic or _normalize_slug(epic) == norm_active:
                    rows.append(data)
    return rows


def _read_markdown_ledger_file(
    md_path: Path, norm_active: str | None
) -> list[dict[str, Any]]:
    """Read matching gate ledger records from a markdown `GATE_LEDGER.md` table."""
    rows: list[dict[str, Any]] = []
    if not md_path.is_file():
        return rows
    with contextlib.suppress(OSError, UnicodeDecodeError):
        for line in md_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if (
                not stripped.startswith("|")
                or stripped.startswith("|---")
                or "timestamp" in stripped.lower()
            ):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) < 3:
                continue
            try:
                gate_num = int(cells[2])
            except ValueError:
                continue
            epic = cells[1].strip()
            if not norm_active or not epic or _normalize_slug(epic) == norm_active:
                rows.append(
                    {
                        "timestamp": cells[0],
                        "epic": epic,
                        "gate": gate_num,
                        "commit": cells[3] if len(cells) > 3 else "",
                        "approved": cells[4] if len(cells) > 4 else "",
                        "deviations": cells[5] if len(cells) > 5 else "",
                        "by": cells[6] if len(cells) > 6 else "",
                    }
                )
    return rows


def parse_gate_ledger_entries(
    repo_path: Path, active_epic: str | None = None
) -> list[dict[str, Any]]:
    """Merge gate approval entries from `state/gate_ledger.jsonl` and `GATE_LEDGER.md` across root and worktrees."""
    devtool_dirs = _collect_devtool_dirs(repo_path, active_epic=None)
    if not devtool_dirs:
        return []

    norm_active = _normalize_slug(active_epic) if active_epic else None
    merged: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, int, str]] = set()

    def _append_unique(rows: list[dict[str, Any]]) -> None:
        for row in rows:
            with contextlib.suppress(TypeError, ValueError):
                gate_num = int(row["gate"])
                row["gate"] = gate_num
                epic_key = _normalize_slug(str(row.get("epic", "")))
                ts_key = str(row.get("timestamp", "")).strip()
                dedup_key = (epic_key, gate_num, ts_key)
                if dedup_key not in seen_keys:
                    seen_keys.add(dedup_key)
                    merged.append(row)

    # Read JSONL sources first (preserving structured metadata), then Markdown tables (no short-circuit)
    for devtool_dir in devtool_dirs:
        _append_unique(
            _read_jsonl_ledger_file(devtool_dir / "state" / "gate_ledger.jsonl", norm_active)
        )
    for devtool_dir in devtool_dirs:
        _append_unique(_read_markdown_ledger_file(devtool_dir / "GATE_LEDGER.md", norm_active))

    merged.sort(key=lambda e: (str(e.get("timestamp", "")), int(e.get("gate", 0))))
    return merged


def _read_epic_heartbeat(
    repo_path: Path, active_epic: str | None
) -> dict[str, Any] | None:
    """Read the highest-generation `<epic_slug>.heartbeat.json` across root and worktrees."""
    if not active_epic:
        return None
    state_env = _load_state_envelope()
    slug_candidates: list[str] = [
        active_epic,
        active_epic.replace("_", "-"),
        active_epic.replace("-", "_"),
    ]
    if state_env is not None:
        with contextlib.suppress(Exception):
            slug_candidates.append(state_env._sanitize_epic_slug(active_epic))

    filenames: list[str] = []
    for slug in slug_candidates:
        fname = f"{slug}.heartbeat.json"
        if fname not in filenames:
            filenames.append(fname)

    best_hb: dict[str, Any] | None = None
    best_key = (-1, "")
    for fname in filenames:
        snap = _read_state_snapshot(repo_path, fname, {}, active_epic=active_epic)
        if not snap:
            continue
        if "epic_slug" not in snap and "slots" not in snap and "stage" not in snap:
            continue
        gen = snap.get("generation", 0)
        gen_num = gen if isinstance(gen, int) and not isinstance(gen, bool) else 0
        key = (gen_num, str(snap.get("updated_at", "")))
        if key > best_key:
            best_key = key
            best_hb = snap
    return best_hb


def _read_quality_state(
    repo_path: Path, active_epic: str | None
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Read `quality_active.json`, expire dead-PID / TTL runs, and isolate active epic vs live concurrent runs."""
    state_env = _load_state_envelope()
    devtool_dirs = _collect_devtool_dirs(repo_path, active_epic=None)
    if state_env is not None:
        seen = {d.resolve() for d in devtool_dirs if d.is_dir()}
        with contextlib.suppress(Exception):
            for extra in state_env._collect_target_devtool_dirs(
                repo_path, "quality_active.json"
            ):
                if extra.is_dir() and extra.resolve() not in seen:
                    seen.add(extra.resolve())
                    devtool_dirs.append(extra)
        snapshot, _ = state_env._read_highest_snapshot(
            devtool_dirs, "quality_active.json", {}
        )
    else:
        snapshot = _read_state_snapshot(repo_path, "quality_active.json", {})

    if not snapshot:
        return None, []

    runs_map: dict[str, dict[str, Any]] = {}
    raw_runs = snapshot.get("runs")
    if isinstance(raw_runs, dict):
        for run_id, entry in raw_runs.items():
            if isinstance(entry, dict):
                runs_map[str(run_id)] = dict(entry)
    elif isinstance(snapshot.get("run_id"), str) and snapshot["run_id"]:
        runs_map[snapshot["run_id"]] = dict(snapshot)

    if not runs_map:
        return None, []

    now_utc = datetime.now(timezone.utc)
    local_host = socket.gethostname()
    expired_runs: dict[str, dict[str, Any]] = {}
    for run_id, entry in runs_map.items():
        if state_env is not None:
            expired_runs[run_id] = state_env._expire_stale_quality_entry(
                entry, now=now_utc, local_host=local_host
            )
        else:
            expired_runs[run_id] = dict(entry)

    sorted_entries = sorted(
        expired_runs.values(),
        key=lambda e: (str(e.get("updated_at", "")), str(e.get("run_id", ""))),
        reverse=True,
    )
    quality_runs = [entry for entry in sorted_entries if entry.get("status") == "running"]

    quality_active: dict[str, Any] | None = None
    if active_epic:
        norm_epic = _normalize_slug(active_epic)
        epic_matches = [
            entry
            for entry in sorted_entries
            if _normalize_slug(str(entry.get("epic_slug", ""))) == norm_epic
        ]
        if epic_matches:
            live_epic = [e for e in epic_matches if e.get("status") == "running"]
            quality_active = live_epic[0] if live_epic else epic_matches[0]
        else:
            unscoped = [e for e in sorted_entries if not str(e.get("epic_slug", "")).strip()]
            live_unscoped = [e for e in unscoped if e.get("status") == "running"]
            quality_active = (
                live_unscoped[0] if live_unscoped else (unscoped[0] if unscoped else None)
            )
    else:
        quality_active = quality_runs[0] if quality_runs else sorted_entries[0]

    return quality_active, quality_runs


def derive_lifecycle_state(
    repo_path: Path,
    active_epic: str | None,
    *,
    pending_decision: Any = _UNSET,
) -> LifecycleDecision:
    """Derive deterministic lifecycle state and human action prompt for a repository."""
    if not active_epic:
        return LifecycleDecision(
            stage_name=LifecycleStage.IDLE.value,
            gate_status="Idle",
            prompt="Kho lưu trữ đang ở trạng thái nghỉ (Idle)",
            is_human_action_required=False,
            is_blocked=False,
        )

    gates = parse_gate_ledger_entries(repo_path, active_epic)
    approved_gate_nums = {int(g["gate"]) for g in gates if "gate" in g}

    assistant_state_text = _read_combined_state_text(repo_path, active_epic)
    task_progress = extract_task_progress(repo_path, active_epic)

    matched_pd: dict[str, Any] | None
    if pending_decision is _UNSET:
        pd_snapshot = _read_state_snapshot(repo_path, "pending_decision.json", {})
        matched_pd = _match_pending_decision_for_epic(pd_snapshot, active_epic)
    else:
        matched_pd = (
            dict(pending_decision) if isinstance(pending_decision, dict) else None
        )

    # Gate 5 PASS -> Completed / Idle
    if 5 in approved_gate_nums:
        return LifecycleDecision(
            stage_name=LifecycleStage.IDLE.value,
            gate_status="Gate 5 PASS (Completed)",
            prompt="Epic hoàn thành và lưu trữ vào sổ cái (Completed)",
            is_human_action_required=False,
        )

    lower_state = assistant_state_text.lower()

    # Check for Circuit Breaker / conflict halts first across any stage
    has_cb_halt = (
        "circuit_breaker_halt (" in lower_state
        or "circuit_breaker_halt:" in lower_state
        or "[circuit_breaker_halt]" in lower_state
        or "status: circuit_breaker_halt" in lower_state
        or "status: halted" in lower_state
    )
    if has_cb_halt:
        return LifecycleDecision(
            stage_name="Stage 3: Circuit Breaker Halt",
            gate_status="Halted on Conflict",
            prompt="Dừng khẩn cấp: Xung đột kiến trúc hoặc contract cần Human Architect giải quyết",
            is_human_action_required=True,
            is_blocked=True,
        )

    # Explicit runtime pending_decision matching active_epic drives human action visibility
    if matched_pd and matched_pd.get("active", True) is True:
        pd_stage = str(
            matched_pd.get("stage") or LifecycleStage.STAGE_1_INCEPTION.value
        )
        pd_reason = str(matched_pd.get("reason") or "Approve Pending Decision")
        pd_kind = str(matched_pd.get("kind") or "Pending Decision")
        pd_blocked = bool(
            matched_pd.get("blocked", False)
            or "circuit_breaker" in pd_kind.lower()
        )
        return LifecycleDecision(
            stage_name=pd_stage,
            gate_status=pd_kind,
            prompt=pd_reason,
            is_human_action_required=True,
            is_blocked=pd_blocked,
        )

    # Gate 4 PASS
    if 4 in approved_gate_nums:
        if (
            "review converged" in lower_state
            or "gate 5" in lower_state
            or "sign-off" in lower_state
            or "stage 4" in lower_state
            or "finish" in lower_state
        ):
            return LifecycleDecision(
                stage_name=LifecycleStage.STAGE_3_PHASE_4_1_SIGNOFF.value,
                gate_status="Gate 4 PASS (Review Converged)",
                prompt="Phê duyệt Gate 5 (Kanban Sign-off) và kết thúc nhánh (/finish)",
                is_human_action_required=True,
            )
        # In automated pipeline, Gate 4 PASS automatically runs Cross-Model Review
        return LifecycleDecision(
            stage_name=LifecycleStage.STAGE_3_PHASE_4_REVIEW.value,
            gate_status="Gate 4 PASS (Cross-Model Review)",
            prompt="Đang chạy Cross-Model Review tự động (3 rounds auto-triage)",
            is_human_action_required=False,
        )

    # Gate 3 PASS
    if 3 in approved_gate_nums:
        norm_active = _normalize_slug(active_epic)
        active_tasks = [
            t
            for t in task_progress.tasks
            if _normalize_slug(str(t.get("epic") or "")) == norm_active
        ]
        active_total = len(active_tasks)
        active_done = sum(1 for t in active_tasks if t.get("status") == "done")
        if active_total > 0 and active_done == active_total:
            # All tasks done -> automatically run Gate 4 local verification
            return LifecycleDecision(
                stage_name=LifecycleStage.STAGE_3_PHASE_4_REVIEW.value,
                gate_status="Tasks Done (Running Gate 4 Verification)",
                prompt="Đang thực thi kiểm thử tự động Gate 4 (quality_check + audit_epic)",
                is_human_action_required=False,
            )
        active_task_str = (
            f" ({task_progress.active_task_name})"
            if task_progress.active_task_name
            else ""
        )
        return LifecycleDecision(
            stage_name=LifecycleStage.STAGE_3_PHASE_2_TDD.value,
            gate_status="Gate 3 PASS",
            prompt=f"AI Programmer autonomously executing TDD{active_task_str}",
            is_human_action_required=False,
        )

    # Gate 2 PASS
    if 2 in approved_gate_nums:
        matching_wts = _collect_matching_worktrees(repo_path, active_epic)
        has_worktree = (repo_path / ".worktrees" / active_epic).is_dir() or bool(
            matching_wts
        )

        # If an active worktree exists, Stage 3 Phase 1 (Order) wins
        if has_worktree:
            return LifecycleDecision(
                stage_name=LifecycleStage.STAGE_3_PHASE_1_ORDER.value,
                gate_status="Gate 2 PASS",
                prompt="Phê duyệt Gate 3: Xác nhận thứ tự thực thi Kanban tasks và phân lập worktree",
                is_human_action_required=True,
            )

        epic_dirs = [wt / ".devtool" / "epic" / active_epic for wt in matching_wts]
        epic_dirs.append(repo_path / ".devtool" / "epic" / active_epic)
        handoff_file = next(
            (d / "handoff.md" for d in epic_dirs if (d / "handoff.md").is_file()),
            repo_path / ".devtool" / "epic" / active_epic / "handoff.md",
        )
        if handoff_file.is_file():
            principal_review_file = next(
                (
                    d / "principal_review.md"
                    for d in epic_dirs
                    if (d / "principal_review.md").is_file()
                ),
                repo_path / ".devtool" / "epic" / active_epic / "principal_review.md",
            )
            if (
                principal_review_file.is_file()
                and "unconfirmed"
                in principal_review_file.read_text(encoding="utf-8").lower()
            ):
                return LifecycleDecision(
                    stage_name=LifecycleStage.STAGE_2_REVIEW_TRIAGE.value,
                    gate_status="Gate 2 PASS (Review Triage)",
                    prompt="Approve Triage Decisions",
                    is_human_action_required=True,
                )
            return LifecycleDecision(
                stage_name=LifecycleStage.STAGE_2_EXIT_HANDOFF.value,
                gate_status="Gate 2 PASS (Review Passed)",
                prompt="Lựa chọn triển khai: Triển khai (tự động) hoặc Dừng lại lấy prompt",
                is_human_action_required=True,
            )
        return LifecycleDecision(
            stage_name=LifecycleStage.STAGE_2_EXIT_HANDOFF.value,
            gate_status="Gate 2 PASS (Ready for Review)",
            prompt="Xác nhận thứ tự ưu tiên provider/model cho /principal-review",
            is_human_action_required=True,
        )

    # Gate 1 PASS
    if 1 in approved_gate_nums:
        return LifecycleDecision(
            stage_name=LifecycleStage.STAGE_2_ARCHITECTURE.value,
            gate_status="Gate 1 PASS",
            prompt="AI Assistant authoring HLD & Task Breakdown",
            is_human_action_required=False,
        )

    # No gates approved and no active pending_decision -> Idle
    return LifecycleDecision(
        stage_name=LifecycleStage.IDLE.value,
        gate_status="Idle",
        prompt="Kho lưu trữ đang ở trạng thái nghỉ (Idle)",
        is_human_action_required=False,
    )


_PIC_LINE_RE = re.compile(
    r"-\s+\*\*(?:PIC(?:\s*/\s*Assigned\s+Profile)?|Profile|Assigned Profile|Người phụ trách(?: \(PIC\))?)\*\*:\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)


def _clean_pic_candidate(raw_value: str) -> str | None:
    """Validate and extract a PIC profile identifier, rejecting template placeholders."""
    stripped = raw_value.strip()
    if not stripped:
        return None
    token = stripped.split()[0].strip("`*_\"'")
    if token.startswith("<") and token.endswith(">"):
        return None
    token = token.lstrip("@").strip("`*_\"',.")
    if token.lower() in _PIC_PLACEHOLDERS:
        return None
    if not re.fullmatch(r"[a-zA-Z0-9_\-]+", token):
        return None
    return token


def _find_epic_dirs_for_checkout(checkout_root: Path, active_epic: str) -> list[Path]:
    """Locate matching `.devtool/epic/<epic>` directories inside a single checkout."""
    epic_base = checkout_root / ".devtool" / "epic"
    if not epic_base.is_dir():
        return []
    matches: list[Path] = []
    exact = epic_base / active_epic
    if exact.is_dir():
        matches.append(exact)
    target_norm = _normalize_slug(active_epic)
    with contextlib.suppress(OSError):
        for entry in sorted(epic_base.iterdir()):
            if (
                entry.is_dir()
                and entry not in matches
                and _normalize_slug(entry.name) == target_norm
            ):
                matches.append(entry)
    return matches


def extract_epic_pic(repo_path: Path, active_epic: str | None) -> str | None:
    """Extract assigned PIC / profile from worktree and root handoff, HLD, or design docs."""
    if not active_epic:
        return None

    checkouts = [*_collect_matching_worktrees(repo_path, active_epic), repo_path]
    candidates: list[Path] = []
    seen_paths: set[Path] = set()

    def _add_candidate(path_obj: Path) -> None:
        if not path_obj.is_file():
            return
        resolved = path_obj.resolve()
        if resolved not in seen_paths:
            seen_paths.add(resolved)
            candidates.append(path_obj)

    for checkout in checkouts:
        for epic_dir in _find_epic_dirs_for_checkout(checkout, active_epic):
            _add_candidate(epic_dir / "handoff.md")
            _add_candidate(epic_dir / f"{epic_dir.name}.en.md")
            _add_candidate(epic_dir / f"{active_epic}.en.md")
            _add_candidate(epic_dir / f"{epic_dir.name}.vi.md")
            _add_candidate(epic_dir / f"{active_epic}.vi.md")
            with contextlib.suppress(OSError):
                for doc in sorted(epic_dir.glob("*.md")):
                    if "design" in doc.name.lower() and not doc.name.startswith("task_"):
                        _add_candidate(doc)

    for candidate in candidates:
        with contextlib.suppress(OSError, UnicodeDecodeError):
            text = candidate.read_text(encoding="utf-8")
            for m in _PIC_LINE_RE.finditer(text):
                cleaned = _clean_pic_candidate(m.group(1))
                if cleaned:
                    return cleaned
    return None


def scan_repo(repo_path: Path) -> RepoMetadata:
    """Harvest complete metadata and telemetry for a single repository."""
    # 1. Project-level: styling, memory, notes, and epics overview from root repo
    theme_color, window_title = extract_vscode_styling(repo_path)
    worktrees = scan_worktrees(repo_path)
    memory = extract_two_tier_memory(repo_path)
    quick_note = extract_repo_note(repo_path)
    epics_summary = harvest_epics_overview(repo_path)

    # 2. Epic-level: active epic, state envelopes, task progress, and PIC
    active_epic = resolve_active_epic(repo_path)
    task_progress = extract_task_progress(repo_path, active_epic)

    # First priority: PIC directly from active epic metadata (worktree + root)
    account_id = extract_epic_pic(repo_path, active_epic)

    # Second priority: Extract account ID from window_title if available
    if not account_id:
        m_acc = re.search(r"\[@([a-zA-Z0-9_\-]+)\]", window_title)
        if m_acc:
            account_id = m_acc.group(1)

    pd_snapshot = _read_state_snapshot(repo_path, "pending_decision.json", {})
    matched_pending = _match_pending_decision_for_epic(pd_snapshot, active_epic)
    heartbeat = _read_epic_heartbeat(repo_path, active_epic)
    quality_active, quality_runs = _read_quality_state(repo_path, active_epic)

    decision = derive_lifecycle_state(
        repo_path, active_epic, pending_decision=matched_pending
    )
    active_stage = decision.stage_name

    # Propagate deterministic action requirements to each epic in epics_summary
    completed_slugs = get_completed_epic_slugs(repo_path)
    if epics_summary and epics_summary.epics:
        for ep in epics_summary.epics:
            slug = ep.get("slug", "")
            if ep.get("status") == "done" or _is_completed_epic(slug, completed_slugs):
                ep["is_action_required"] = False
                ep["action_prompt"] = ""
                ep["is_review_converged"] = True
                continue
            if active_epic and _normalize_slug(slug) == _normalize_slug(active_epic):
                ep["is_action_required"] = decision.is_human_action_required
                ep["action_prompt"] = (
                    decision.prompt if decision.is_human_action_required else ""
                )
                ep["is_review_converged"] = (
                    decision.stage_name == LifecycleStage.STAGE_3_PHASE_4_1_SIGNOFF.value
                )
            else:
                ep_pd = _match_pending_decision_for_epic(pd_snapshot, slug)
                ep_act = bool(ep_pd and ep_pd.get("active", True) is True)
                ep_prompt = str(ep_pd.get("reason", "")) if ep_act and ep_pd else ""
                ep_conv = False
                state_f = repo_path / ".devtool" / "state" / f"{slug}.md"
                if state_f.is_file():
                    with contextlib.suppress(Exception):
                        st_lower = state_f.read_text(encoding="utf-8").lower()
                        if not ep_act and any(
                            k in st_lower
                            for k in (
                                "action required",
                                "cần bạn xác nhận",
                                "waiting for user",
                            )
                        ):
                            ep_act = True
                        if any(
                            k in st_lower
                            for k in ("review converged", "gate 5", "sign-off", "finish")
                        ):
                            ep_conv = True
                ep["is_action_required"] = ep_act
                if ep_prompt and not ep.get("action_prompt"):
                    ep["action_prompt"] = ep_prompt
                ep["is_review_converged"] = ep_conv

    return RepoMetadata(
        name=repo_path.name,
        path=str(repo_path.resolve()),
        theme_color=theme_color,
        window_title=window_title,
        active_epic=active_epic,
        active_stage=active_stage,
        worktrees=worktrees,
        task_progress=task_progress,
        memory=memory,
        account_id=account_id,
        quick_note=quick_note,
        prompt=decision.prompt,
        epics_summary=epics_summary,
        is_human_action_required=decision.is_human_action_required,
        is_blocked=decision.is_blocked,
        pending_decision=matched_pending,
        heartbeat=heartbeat,
        quality_active=quality_active,
        quality_runs=quality_runs,
    )


def harvest_dashboard_graph(root_path: Path, max_workers: int = 4) -> DashboardGraph:
    """Discover all repositories under workspace root in parallel and aggregate metrics."""
    repos: list[RepoMetadata] = []
    repo_dirs: list[Path] = []

    if root_path.is_dir():
        for entry in root_path.iterdir():
            if entry.is_dir() and not entry.name.startswith("."):
                # Must be a git repo or have .git directory/file
                if (entry / ".git").exists():
                    repo_dirs.append(entry)

    # Prioritize canonical order
    canonical_order = [
        "ai-agent-tools",
        "lyrics-sync",
        "nexus",
        "D3Nexus",
        "digital_wallet",
    ]
    repo_dirs.sort(
        key=lambda d: (
            canonical_order.index(d.name) if d.name in canonical_order else 999
        )
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_repo, d): d for d in repo_dirs}
        for future in concurrent.futures.as_completed(futures):
            with contextlib.suppress(Exception):
                meta = future.result()
                repos.append(meta)

    # Keep canonical sorting in output
    repos.sort(
        key=lambda r: (
            canonical_order.index(r.name) if r.name in canonical_order else 999
        )
    )

    total_tasks = sum(r.task_progress.total_tasks for r in repos)
    total_done = sum(r.task_progress.done_tasks for r in repos)
    dirty_wt = sum(1 for r in repos for wt in r.worktrees if wt.is_dirty)
    active_epics = sum(1 for r in repos if r.active_epic)

    metrics_row = {
        "total_repos": len(repos),
        "active_epics": active_epics,
        "dirty_worktrees": dirty_wt,
        "total_tasks": total_tasks,
        "done_tasks": total_done,
        "overall_percentage": round((total_done / total_tasks * 100), 1)
        if total_tasks > 0
        else 0.0,
    }

    available_profiles = discover_antigravity_profiles()

    return DashboardGraph(
        workspace_root=str(root_path.resolve()),
        scanned_at=datetime.now().isoformat(),
        repos=repos,
        metrics_row=metrics_row,
        available_profiles=available_profiles,
    )


ANSI_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Strip all ANSI escape sequences from text for plain output."""
    return ANSI_REGEX.sub("", text)


def hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
    """Convert hex color string #rrggbb to RGB tuple."""
    hex_clean = hex_code.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join(2 * c for c in hex_clean)
    if len(hex_clean) >= 6:
        return (
            int(hex_clean[0:2], 16),
            int(hex_clean[2:4], 16),
            int(hex_clean[4:6], 16),
        )
    return (200, 200, 200)


def colorize(text: str, hex_color: str, use_color: bool = True) -> str:
    """Format text with truecolor ANSI foreground escape code."""
    if not use_color:
        return text
    r, g, b = hex_to_rgb(hex_color)
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


def render_progress_bar(
    percentage: float, width: int = 10, use_color: bool = True
) -> str:
    """Render a visual ascii/ansi progress bar."""
    pct = max(0.0, min(100.0, percentage))
    filled = round(width * pct / 100.0)
    filled = max(0, min(width, filled))
    empty = width - filled
    if use_color:
        return f"[\033[32m{'█' * filled}\033[90m{'░' * empty}\033[0m]"
    return f"[{'█' * filled}{'░' * empty}]"


def pad_ansi(text: str, width: int) -> str:
    """Pad text to target visible width taking ANSI escape codes into account."""
    visible_len = len(strip_ansi(text))
    pad = max(0, width - visible_len)
    return text + (" " * pad)


def render_terminal_table(graph: DashboardGraph, use_color: bool = True) -> str:
    """Render rich ANSI formatted multi-repo overview table."""
    lines: list[str] = []
    header_title = "=== CHECK-TASKS MULTI-REPO OVERVIEW ==="
    lines.append(colorize(header_title, "#38bdf8", use_color))
    lines.append(
        f"Workspace: {graph.workspace_root} | Scanned: {graph.scanned_at[:19]}"
    )
    lines.append("-" * 88)

    header = f"{'Repository':<18} {'Branch / Worktree':<26} {'Active Epic':<22} {'Tasks Progress':<20}"
    lines.append(header)
    lines.append("-" * 88)

    for repo in graph.repos:
        badge = colorize(f"[{repo.name}]", repo.theme_color, use_color)

        branch_name = "-"
        if repo.worktrees:
            b = repo.worktrees[0].branch
            if b:
                branch_name = b.replace("refs/heads/", "")

        epic_name = repo.active_epic or "-"
        pct = repo.task_progress.percentage
        bar = render_progress_bar(pct, width=8, use_color=use_color)
        tally = f"{bar} {int(pct)}% ({repo.task_progress.done_tasks}/{repo.task_progress.total_tasks})"

        col1 = pad_ansi(badge, 18)
        col2 = pad_ansi(branch_name, 26)
        col3 = pad_ansi(epic_name, 22)
        line_str = f"{col1} {col2} {col3} {tally}"
        lines.append(line_str)

        if repo.prompt:
            step_str = f"  ↳ Next Step: {repo.prompt}"
            lines.append(colorize(step_str, "#fbbf24", use_color))
        elif repo.active_stage and repo.active_stage != "Idle":
            step_str = f"  ↳ Stage: {repo.active_stage}"
            lines.append(colorize(step_str, "#94a3b8", use_color))

    lines.append("-" * 88)
    metrics = graph.metrics_row
    footer = (
        f"Repos: {metrics.get('total_repos', len(graph.repos))} | "
        f"Active Epics: {metrics.get('active_epics', 0)} | "
        f"Tasks: {metrics.get('done_tasks', 0)}/{metrics.get('total_tasks', 0)} Done "
        f"({metrics.get('overall_percentage', 0)}%)"
    )
    lines.append(colorize(footer, "#10b981", use_color))
    return "\n".join(lines)


def render_single_repo(repo: RepoMetadata, use_color: bool = True) -> str:
    """Render deep terminal inspection card for a single repository."""
    lines: list[str] = []
    title = f"=== REPOSITORY: {repo.name.upper()} ==="
    lines.append(colorize(title, repo.theme_color, use_color))
    lines.append(f"Path: {repo.path}")
    if repo.account_id:
        lines.append(f"Account: @{repo.account_id}")
    if repo.active_epic:
        lines.append(f"Active Epic: {repo.active_epic}")
    lines.append(f"Stage: {repo.active_stage or 'Idle'}")

    if repo.prompt:
        lines.append(
            colorize(f"Next Action / Decision: {repo.prompt}", "#fbbf24", use_color)
        )

    pct = repo.task_progress.percentage
    bar = render_progress_bar(pct, width=12, use_color=use_color)
    lines.append(
        f"Tasks: {bar} {int(pct)}% "
        f"({repo.task_progress.done_tasks}/{repo.task_progress.total_tasks} done, "
        f"{repo.task_progress.in_progress_tasks} in-progress, "
        f"{repo.task_progress.todo_tasks} todo)"
    )

    if repo.worktrees:
        lines.append("Worktrees:")
        for wt in repo.worktrees:
            dirty_str = (
                f" [DIRTY: {wt.dirty_file_count} files]" if wt.is_dirty else " [clean]"
            )
            lines.append(
                f"  - {wt.branch or 'detached'} ({wt.head_sha[:7]}){dirty_str} -> {wt.path}"
            )

    if repo.memory:
        lines.append(f"Memory: {repo.memory.total_milestones} milestones recorded")
        if repo.memory.last_milestone:
            lines.append(f"  Last Milestone: {repo.memory.last_milestone}")

    if repo.quick_note:
        lines.append(f"Notes:\n  {repo.quick_note}")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for check-tasks."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Check-Tasks terminal dashboard and multi-repo inspector."
    )
    parser.add_argument(
        "target", nargs="?", default=None, help="Target: 'all' or specific repo name"
    )
    parser.add_argument(
        "--all", action="store_true", help="Scan and display all repositories"
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON graph")
    parser.add_argument(
        "--no-color", action="store_true", help="Disable ANSI color codes"
    )
    parser.add_argument(
        "--ui",
        "--web",
        action="store_true",
        dest="ui",
        help="Launch HTTP dashboard server and open in browser",
    )
    parser.add_argument(
        "-f",
        "--foreground",
        action="store_true",
        help="Run dashboard server in foreground mode",
    )
    parser.add_argument(
        "--stop", action="store_true", help="Stop background HTTP dashboard server"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check background HTTP dashboard server status",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=_real_home() / "AllProjects",
        help="Workspace root containing repositories",
    )
    args = parser.parse_args(argv)

    use_color = not args.no_color and sys.stdout.isatty()

    if args.ui or args.stop or args.status:
        server_script = Path(__file__).resolve().parent / "tasks_server.py"
        if not server_script.is_file():
            sys.stderr.write(f"Error: tasks_server.py not found at {server_script}\n")
            return 1
        cmd = [sys.executable, str(server_script)]
        cmd.extend(["--workspace-root", str(args.workspace_root)])
        if args.ui:
            if not args.foreground:
                cmd.append("--daemon")
        elif args.stop:
            cmd.append("--stop")
        elif args.status:
            cmd.append("--status")
        ret = subprocess.call(cmd, env=_build_clean_host_env())
        if args.ui and ret == 0 and not args.foreground:
            import webbrowser

            webbrowser.open("http://localhost:8766/")
        return ret

    target = args.target or ("all" if args.all else None)

    if args.json:
        graph = harvest_dashboard_graph(args.workspace_root)
        print(
            json.dumps(
                graph, default=lambda o: getattr(o, "__dict__", str(o)), indent=2
            )
        )
        return 0

    if target == "all":
        graph = harvest_dashboard_graph(args.workspace_root)
        print(render_terminal_table(graph, use_color=use_color))
        return 0

    if target:
        repo_dir = args.workspace_root / target
        if not repo_dir.is_dir():
            print(
                f"Error: Repository '{target}' not found under {args.workspace_root}",
                file=sys.stderr,
            )
            return 1
        repo = scan_repo(repo_dir)
        print(render_single_repo(repo, use_color=use_color))
        return 0

    cwd = Path.cwd()
    if (cwd / ".git").exists() or (cwd / ".." / ".git").exists():
        repo = scan_repo(cwd)
        print(render_single_repo(repo, use_color=use_color))
        return 0

    graph = harvest_dashboard_graph(args.workspace_root)
    print(render_terminal_table(graph, use_color=use_color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
