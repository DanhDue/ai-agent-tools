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
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent

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


def resolve_active_epic(repo_path: Path) -> str | None:
    """Derive active epic from branch name, active worktrees, state snapshot files, or git worktree directories."""
    # 0. Get completed slugs from PROJECT_LEDGER.md, archive, and HLD Status: Done
    completed_slugs = get_completed_epic_slugs(repo_path)

    # 1. Check current branch or worktree branches for epic/<slug> or feat/<slug>
    for wt in scan_worktrees(repo_path):
        if wt.branch:
            m_br = re.match(r"(?:epic|feat)/([a-zA-Z0-9_\-]+)", wt.branch)
            if m_br:
                slug = m_br.group(1).strip()
                if slug not in completed_slugs:
                    return slug

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
                        if slug not in completed_slugs:
                            return slug

            # Check tasks inside worktree features
            wt_feat = d / ".devtool" / "features"
            if wt_feat.is_dir():
                for tf in sorted(wt_feat.glob("task_*.md")):
                    with contextlib.suppress(OSError):
                        fm = parse_frontmatter(tf.read_text(encoding="utf-8"))
                        ep = fm.get("epic")
                        if ep and ep != "general" and ep not in completed_slugs:
                            return ep

            # Check if directory name matches an epic
            if (repo_path / ".devtool" / "epic" / d.name).is_dir():
                if d.name not in completed_slugs:
                    return d.name

    # 3. Check assistant_state.md, skipping placeholder "general" and completed epics
    state_file = repo_path / ".devtool" / "assistant_state.md"
    if state_file.is_file():
        with contextlib.suppress(OSError):
            content = state_file.read_text(encoding="utf-8")
            for m in re.finditer(r"#\s*Active Epic:\s*([a-zA-Z0-9_\-]+)", content):
                slug = m.group(1).strip()
                if slug and slug != "general" and slug not in completed_slugs:
                    return slug

    # 4. Check state folder for non-general state files in deterministic order
    state_dir = repo_path / ".devtool" / "state"
    if state_dir.is_dir():
        for sf in sorted(state_dir.glob("*.md")):
            if sf.stem != "general" and sf.stem not in completed_slugs:
                return sf.stem

    # 5. Check .worktrees directory in deterministic order (any worktree not completed)
    if wt_dir.is_dir():
        for d in sorted(wt_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                if d.name not in completed_slugs:
                    return d.name

    # 6. Check .devtool/features/*.md for epic frontmatter
    features_dir = repo_path / ".devtool" / "features"
    if features_dir.is_dir():
        for tf in sorted(features_dir.glob("task_*.md")):
            with contextlib.suppress(OSError):
                fm = parse_frontmatter(tf.read_text(encoding="utf-8"))
                ep = fm.get("epic")
                if ep and ep != "general" and ep not in completed_slugs:
                    return ep

    # 7. Check epic folder in deterministic order for uncompleted epics
    epic_dir = repo_path / ".devtool" / "epic"
    if epic_dir.is_dir():
        epics = sorted(
            [
                d.name
                for d in epic_dir.iterdir()
                if d.is_dir()
                and not d.name.startswith(".")
                and d.name not in completed_slugs
            ]
        )
        if epics:
            return epics[0]

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

    # Build fast worktree lookup table (O(1) filesystem check)
    wt_dir = repo_path / ".worktrees"
    known_wts: dict[str, Path] = {}
    if wt_dir.is_dir():
        for item in wt_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                known_wts[item.name] = item
                known_wts[item.name.replace("-", "_")] = item
                known_wts[item.name.replace("_", "-")] = item

    # Rule 3: For active epic(s) with dedicated worktrees, fetch detailed tasks from worktree
    for ep in candidate_epics:
        ep_wt = known_wts.get(ep)
        if ep_wt and ep_wt.is_dir():
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
                if (
                    candidate_epics
                    and task_epic not in candidate_epics
                    and task_epic not in [e.replace("_", "-") for e in candidate_epics]
                ):
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
    pct = round((done / total * 100), 1) if total > 0 else 0.0

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


def _normalize_slug(slug: str) -> str:
    """Normalize epic slugs for robust comparison across dash/underscore conventions."""
    return slug.strip().lower().replace("_", "-")


def parse_gate_ledger_entries(
    repo_path: Path, active_epic: str | None = None
) -> list[dict[str, Any]]:
    """Parse gate approval entries from state/gate_ledger.jsonl or GATE_LEDGER.md."""
    entries: list[dict[str, Any]] = []
    devtool_dir = repo_path / ".devtool"
    if not devtool_dir.is_dir():
        return entries

    norm_active = _normalize_slug(active_epic) if active_epic else None

    jsonl_path = devtool_dir / "state" / "gate_ledger.jsonl"
    if jsonl_path.is_file():
        with contextlib.suppress(Exception):
            for line in jsonl_path.read_text(encoding="utf-8").splitlines():
                line_str = line.strip()
                if not line_str:
                    continue
                with contextlib.suppress(Exception):
                    data = json.loads(line_str)
                    if isinstance(data, dict):
                        epic = str(data.get("epic", ""))
                        if (
                            not norm_active
                            or _normalize_slug(epic) == norm_active
                            or not epic
                        ):
                            entries.append(data)
            if entries:
                return entries

    md_path = devtool_dir / "GATE_LEDGER.md"
    if md_path.is_file():
        with contextlib.suppress(Exception):
            for line in md_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if (
                    not stripped.startswith("|")
                    or stripped.startswith("|---")
                    or "timestamp" in stripped.lower()
                ):
                    continue
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if len(cells) >= 3:
                    try:
                        gate_num = int(cells[2])
                        epic = cells[1]
                        if (
                            not norm_active
                            or _normalize_slug(epic) == norm_active
                            or not epic
                        ):
                            entries.append(
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
                    except (ValueError, IndexError):
                        continue

    return entries


def derive_lifecycle_state(
    repo_path: Path, active_epic: str | None
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

    # Inspect assistant_state.md and epic-specific state for explicit state hints
    assistant_state_text = ""
    assistant_state_file = repo_path / ".devtool" / "assistant_state.md"
    if assistant_state_file.is_file():
        with contextlib.suppress(Exception):
            assistant_state_text = assistant_state_file.read_text(encoding="utf-8")

    epic_state_file = repo_path / ".devtool" / "state" / f"{active_epic}.md"
    if epic_state_file.is_file():
        with contextlib.suppress(Exception):
            assistant_state_text += "\n" + epic_state_file.read_text(encoding="utf-8")

    task_progress = extract_task_progress(repo_path, active_epic)

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
        active_tasks = [
            t for t in task_progress.tasks
            if t.get("epic") in (active_epic, active_epic.replace("-", "_"), active_epic.replace("_", "-"))
        ] if active_epic else task_progress.tasks
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
        epic_dir = repo_path / ".devtool" / "epic" / active_epic
        handoff_file = epic_dir / "handoff.md"
        worktree_dir = repo_path / ".worktrees" / active_epic
        has_worktree = worktree_dir.is_dir() or any(
            (wt.branch and _normalize_slug(active_epic) in _normalize_slug(wt.branch))
            or (Path(wt.path).name == active_epic)
            for wt in scan_worktrees(repo_path)
        )

        # If an active worktree exists, Stage 3 Phase 1 (Order) wins
        if has_worktree:
            return LifecycleDecision(
                stage_name=LifecycleStage.STAGE_3_PHASE_1_ORDER.value,
                gate_status="Gate 2 PASS",
                prompt="Phê duyệt Gate 3: Xác nhận thứ tự thực thi Kanban tasks và phân lập worktree",
                is_human_action_required=True,
            )

        if handoff_file.is_file():
            principal_review_file = epic_dir / "principal_review.md"
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

    # No gates approved yet
    epic_dir = repo_path / ".devtool" / "epic" / active_epic
    has_spec = False
    if epic_dir.is_dir():
        for f in epic_dir.iterdir():
            if (
                f.suffix == ".md"
                and not f.name.startswith("task_")
                and "evidence" not in f.name
            ):
                has_spec = True
                break
    if has_spec:
        return LifecycleDecision(
            stage_name=LifecycleStage.STAGE_1_INCEPTION.value,
            gate_status="Inception",
            prompt="Approve Gate 1 (Design Spec)",
            is_human_action_required=True,
        )

    return LifecycleDecision(
        stage_name=LifecycleStage.IDLE.value,
        gate_status="Idle",
        prompt="Kho lưu trữ đang ở trạng thái nghỉ (Idle)",
        is_human_action_required=False,
    )


def extract_epic_pic(repo_path: Path, active_epic: str | None) -> str | None:
    """Extract assigned PIC / profile from active epic HLD or handoff.md if present."""
    if not active_epic:
        return None
    epic_dir = repo_path / ".devtool" / "epic" / active_epic
    if not epic_dir.is_dir():
        return None
    candidates = [
        epic_dir / "handoff.md",
        epic_dir / f"{active_epic}.en.md",
        epic_dir / f"{active_epic}.vi.md",
    ]
    for c in candidates:
        if c.is_file():
            try:
                text = c.read_text(encoding="utf-8")
                m = re.search(
                    r"-\s+\*\*(?:PIC|Profile|Assigned Profile|Người phụ trách(?: \(PIC\))?)\*\*:\s*`?([a-zA-Z0-9_\-]+)`?",
                    text,
                    re.IGNORECASE,
                )
                if m:
                    return m.group(1).strip()
            except Exception:  # noqa: S110
                pass
    return None


def scan_repo(repo_path: Path) -> RepoMetadata:
    """Harvest complete metadata and telemetry for a single repository."""
    # 1. Project-level: styling, memory, notes, and epics overview from root repo
    theme_color, window_title = extract_vscode_styling(repo_path)
    worktrees = scan_worktrees(repo_path)
    memory = extract_two_tier_memory(repo_path)
    quick_note = extract_repo_note(repo_path)
    epics_summary = harvest_epics_overview(repo_path)

    # 2. Epic-level: detailed task progress & lifecycle from .worktrees/<active_epic>
    active_epic = resolve_active_epic(repo_path)
    task_progress = extract_task_progress(repo_path, active_epic)

    # 1. First priority: Extract account ID / PIC directly from active epic metadata (SSOT)
    account_id = extract_epic_pic(repo_path, active_epic)

    # 2. Second priority: Extract account ID from window_title if available
    if not account_id:
        m_acc = re.search(r"\[@([a-zA-Z0-9_\-]+)\]", window_title)
        if m_acc:
            account_id = m_acc.group(1)

    decision = derive_lifecycle_state(repo_path, active_epic)
    active_stage = decision.stage_name

    # Propagate deterministic action requirements to each epic in epics_summary
    completed_slugs = get_completed_epic_slugs(repo_path)
    if epics_summary and epics_summary.epics:
        for ep in epics_summary.epics:
            slug = ep.get("slug", "")
            if ep.get("status") == "done" or slug in completed_slugs:
                ep["is_action_required"] = False
                ep["action_prompt"] = ""
                ep["is_review_converged"] = True
                continue
            if active_epic and _normalize_slug(slug) == _normalize_slug(active_epic):
                ep["is_action_required"] = decision.is_human_action_required
                ep["action_prompt"] = decision.prompt if decision.is_human_action_required else ""
                ep["is_review_converged"] = (decision.stage_name == LifecycleStage.STAGE_3_PHASE_4_1_SIGNOFF.value)
            else:
                state_f = repo_path / ".devtool" / "state" / f"{slug}.md"
                ep_act = False
                ep_conv = False
                if state_f.is_file():
                    with contextlib.suppress(Exception):
                        st_lower = state_f.read_text(encoding="utf-8").lower()
                        if any(k in st_lower for k in ("action required", "cần bạn xác nhận", "waiting for user")):
                            ep_act = True
                        if any(k in st_lower for k in ("review converged", "gate 5", "sign-off", "finish")):
                            ep_conv = True
                ep["is_action_required"] = ep_act
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
