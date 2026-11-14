"""Multi-repo harvester engine and data models for check-tasks dashboard.

Provides high-performance multi-repo discovery, git worktree parsing,
.vscode styling extraction, task progress aggregation, and two-tier project memory inspection.
"""

from __future__ import annotations

import concurrent.futures
import contextlib
from dataclasses import dataclass, field
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
    return (
        Path(home.split("/antigravity_homes")[0])
        if "/antigravity_homes" in home
        else Path(home)
    )


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
        with contextlib.suppress(Exception):
            agy_quota: Any = importlib.import_module("agy_quota")

            if hasattr(agy_quota, "get_all_profiles"):
                q_profiles = agy_quota.get_all_profiles()
                if q_profiles and isinstance(q_profiles, list):
                    allowed = [
                        p
                        for p in q_profiles
                        if p not in ("claude", "codex", "kiro", "anthropic", "openai")
                    ]
                    if allowed:
                        return sorted(set(allowed))

    # 2. Direct discovery matching check-quota's exact rules (supports custom real_home for tests/profiles)
    r_home = Path(real_home) if real_home is not None else _real_home()
    homes_dir = r_home / "antigravity_homes"
    profiles: list[str] = []
    reserved_non_profiles = {
        "Library",
        "System",
        "Shared",
        "AllProjects",
        "Projects",
        "fvm",
        "claude",
        "codex",
        "kiro",
        "anthropic",
        "openai",
        ".gemini",
        ".antigravity",
        ".antigravity-ide",
        "bin",
        "etc",
        "var",
        "tmp",
        "opt",
        ".Trash",
    }

    if homes_dir.is_dir():
        for entry in sorted(homes_dir.iterdir()):
            if (
                entry.name.startswith(".")
                or entry.name.startswith("-")
                or entry.is_symlink()
                or not entry.is_dir()
            ):
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
        with contextlib.suppress(Exception):
            content = zshrc_path.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r"antigravity_homes/([a-zA-Z0-9_\-]+)", content):
                p = m.group(1)
                if (
                    (homes_dir / p).is_dir()
                    and p not in reserved_non_profiles
                    and p not in profiles
                ):
                    profiles.append(p)
            for m2 in re.finditer(
                r"^alias\s+([a-zA-Z0-9_\-]+)='ag_run\s+([a-zA-Z0-9_\-]+)'",
                content,
                re.MULTILINE,
            ):
                p2 = m2.group(2)
                if (
                    (homes_dir / p2).is_dir()
                    and p2 not in reserved_non_profiles
                    and p2 not in profiles
                ):
                    profiles.append(p2)

    return sorted(set(profiles))


def _build_clean_host_env() -> dict[str, str]:
    """Environment for launching the daemon: real HOME, no leaked IDE/Electron/profile variables.

    Kept local on purpose: scripts/tasks_server.py is a thin wrapper that shadows the real
    tasks_server module on sys.path, so importing it from here is unreliable.
    """
    env = dict(os.environ)
    env["HOME"] = str(_real_home())
    for key in (
        "AGY_PROFILE",
        "AGY_CLI_MODE",
        "AGY_ENABLE_HUB",
        "TERM_PROGRAM",
        "TERM_PROGRAM_VERSION",
        "TERM_SESSION_ID",
        "TMPDIR",
        "ZDOTDIR",
    ):
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
    task_completion_pct: float = 0.0
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
    pipeline_telemetry: dict[str, Any] | None = None


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


_HLD_STATUS_PATTERNS = (
    re.compile(
        r"^(?:>\s*)?(?:-\s*)?\*\*(?:Status|Trạng\s*thái)(?:\*\*\s*:|\s*:\*\*)\s*([^\n\r]+)$",
        re.MULTILINE | re.IGNORECASE,
    ),
    re.compile(
        r"^\|\s*\*{0,2}(?:Status|Trạng\s*thái)\*{0,2}\s*\|\s*([^|\n\r]+?)\s*\|",
        re.MULTILINE | re.IGNORECASE,
    ),
    re.compile(
        r"^(?:Status|Trạng\s*thái)\s*:\s*([^\n\r]+)$",
        re.MULTILINE | re.IGNORECASE,
    ),
    re.compile(
        r"^#{2,3}\s+(?:Status|Trạng\s*thái)\s*\n+\s*([^\n\r#|]+)$",
        re.MULTILINE | re.IGNORECASE,
    ),
)


def _classify_hld_status_value(raw: str) -> str | None:
    """Normalize a raw HLD Status value string into a canonical lifecycle state."""
    val = re.sub(r"[*_`]+", "", raw).strip().lower()
    if not val:
        return None
    if any(
        neg in val
        for neg in ("not done", "incomplete", "chưa hoàn thành", "chưa hoàn tất")
    ):
        return None
    if (
        re.match(r"^(?:done|completed?|finished)\b", val)
        or "hoàn thành" in val
        or "hoàn tất" in val
    ):
        return "done"
    if any(k in val for k in ("discard", "abandon", "cancel", "superseded", "hủy")):
        return "abandon"
    if any(
        k in val
        for k in ("progress", "đang thực hiện", "đang triển khai", "đang thi công")
    ):
        return "in_progress"
    if any(k in val for k in ("package", "đã đóng gói")):
        return "packaged"
    if any(
        k in val
        for k in (
            "todo",
            "backlog",
            "planned",
            "đã lên kế hoạch",
            "design",
            "thiết kế",
            "draft",
            "planning",
            "queued",
            "ready",
            "sẵn sàng",
            "inception",
            "chờ",
            "unstarted",
        )
    ):
        return "unstarted"
    return None


def extract_epic_hld_status(epic_dir: Path, slug: str) -> str | None:
    """Extract epic lifecycle status from HLD design documents (.en.md, .vi.md, or *.md)."""
    candidates = [epic_dir / f"{slug}.en.md", epic_dir / f"{slug}.vi.md"]
    with contextlib.suppress(OSError):
        for f in sorted(epic_dir.glob("*.md")):
            if (
                f not in candidates
                and not f.name.startswith("task_")
                and f.name != "handoff.md"
            ):
                candidates.append(f)

    for hld in candidates:
        if not hld.is_file():
            continue
        with contextlib.suppress(OSError):
            text = hld.read_text(encoding="utf-8")
            matches: list[tuple[int, str]] = []
            for pat in _HLD_STATUS_PATTERNS:
                m = pat.search(text)
                if m:
                    matches.append((m.start(), m.group(1)))
            for _, raw_val in sorted(matches, key=lambda item: item[0]):
                classified = _classify_hld_status_value(raw_val)
                if classified is not None:
                    return classified
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
                m_arch = re.match(
                    r"(?:state|activity)_([a-zA-Z0-9_\-]+)_\d{8}_\d{4}\.", f.name
                )
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


def get_abandoned_epic_slugs(repo_path: Path) -> set[str]:
    """Harvest abandoned epic slugs from .devtool/epic/<slug>/ HLD design documents."""
    abandoned: set[str] = set()
    epic_dir = repo_path / ".devtool" / "epic"
    if epic_dir.is_dir():
        with contextlib.suppress(OSError):
            for d in epic_dir.iterdir():
                if not d.is_dir() or d.name.startswith("."):
                    continue
                if extract_epic_hld_status(d, d.name) in ("abandon", "abandoned"):
                    abandoned.add(d.name)
    return abandoned


def _is_epic_eligible_for_active(
    slug: str,
    completed_slugs: set[str],
    abandoned_slugs: set[str] | None = None,
    hld_status: str | None = None,
) -> bool:
    """Return True if epic is eligible to be active or in_progress (not completed, archived, or abandoned)."""
    if not slug or slug == "general":
        return False
    if _is_completed_epic(slug, completed_slugs):
        return False
    if abandoned_slugs and _is_completed_epic(slug, abandoned_slugs):
        return False
    return hld_status not in ("done", "abandon", "abandoned")


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
    return slug in completed_slugs or any(
        _normalize_slug(c) == norm for c in completed_slugs
    )


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
        snapshot, _ = state_env._read_highest_snapshot(
            collected_dirs, filename, default
        )
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
                gen_num = (
                    gen if isinstance(gen, int) and not isinstance(gen, bool) else 0
                )
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
            return (
                dict(exact_match) if exact_match.get("active", True) is True else None
            )
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
    abandoned_slugs = get_abandoned_epic_slugs(repo_path)

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
                        if (
                            ep
                            and ep != "general"
                            and not _is_completed_epic(ep, completed_slugs)
                        ):
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
                if (
                    slug
                    and slug != "general"
                    and not _is_completed_epic(slug, completed_slugs)
                ):
                    return _resolve_canonical_epic_slug(repo_path, slug)

    # 4. Check state folder for non-general state files in deterministic order
    state_dir = repo_path / ".devtool" / "state"
    if state_dir.is_dir():
        for sf in sorted(state_dir.glob("*.md")):
            if sf.stem != "general" and not _is_completed_epic(
                sf.stem, completed_slugs
            ):
                return _resolve_canonical_epic_slug(repo_path, sf.stem)

    # 5. Check .worktrees directory in deterministic order (any worktree not completed)
    if wt_dir.is_dir():
        for d in sorted(wt_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                base_name = _strip_slot_suffix(d.name)
                if base_name and not _is_completed_epic(base_name, completed_slugs):
                    return _resolve_canonical_epic_slug(repo_path, base_name)

    # 5.5 Check explicit active pending_decision.json entries
    pending_epic = _resolve_active_epic_from_pending_decision(
        repo_path, completed_slugs
    )
    if pending_epic:
        return pending_epic

    # 6. Check .devtool/features/*.md for epic frontmatter
    features_dir = repo_path / ".devtool" / "features"
    if features_dir.is_dir():
        for tf in sorted(features_dir.glob("task_*.md")):
            with contextlib.suppress(OSError):
                fm = parse_frontmatter(tf.read_text(encoding="utf-8"))
                ep = fm.get("epic")
                if ep and _is_epic_eligible_for_active(
                    ep, completed_slugs, abandoned_slugs
                ):
                    return _resolve_canonical_epic_slug(repo_path, ep)

    # 7. Check Gate 1+ ledger entries and active .heartbeat.json files for Stage 1-2 epics
    stage12_candidates: list[tuple[str, str]] = []
    for row in parse_gate_ledger_entries(repo_path):
        ep = str(row.get("epic", "")).strip()
        if not ep or int(row.get("gate", 0)) < 1:
            continue
        canonical = _resolve_canonical_epic_slug(repo_path, ep)
        ep_dir = repo_path / ".devtool" / "epic" / canonical
        hld_st = extract_epic_hld_status(ep_dir, canonical) if ep_dir.is_dir() else None
        if _is_epic_eligible_for_active(canonical, completed_slugs, abandoned_slugs, hld_st):
            stage12_candidates.append((str(row.get("timestamp", "")), canonical))

    for dt in _collect_devtool_dirs(repo_path):
        st_dir = dt / "state"
        if not st_dir.is_dir():
            continue
        with contextlib.suppress(OSError):
            for hb_file in sorted(st_dir.glob("*.heartbeat.json")):
                with contextlib.suppress(OSError, json.JSONDecodeError, UnicodeDecodeError):
                    parsed = json.loads(hb_file.read_text(encoding="utf-8"))
                    if not isinstance(parsed, dict):
                        continue
                    raw_ep = str(
                        parsed.get("epic_slug")
                        or hb_file.name[: -len(".heartbeat.json")]
                    ).strip()
                    canonical = _resolve_canonical_epic_slug(repo_path, raw_ep)
                    ep_dir = repo_path / ".devtool" / "epic" / canonical
                    hld_st = (
                        extract_epic_hld_status(ep_dir, canonical)
                        if ep_dir.is_dir()
                        else None
                    )
                    if _is_epic_eligible_for_active(
                        canonical, completed_slugs, abandoned_slugs, hld_st
                    ):
                        stage12_candidates.append(
                            (str(parsed.get("updated_at", "")), canonical)
                        )

    if stage12_candidates:
        stage12_candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return stage12_candidates[0][1]

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
    abandoned_slugs = get_abandoned_epic_slugs(repo_path)
    all_gates = parse_gate_ledger_entries(repo_path)

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
            norm_slug = _normalize_slug(slug)
            has_gate1_or_more = any(
                _normalize_slug(str(g.get("epic", ""))) == norm_slug
                and int(g.get("gate", 0)) >= 1
                for g in all_gates
            )
            has_active_hb = (
                _read_epic_heartbeat(repo_path, slug) is not None
                or (repo_path / ".devtool" / "state" / f"{slug}.md").is_file()
            )

            # Status determination (HLD status is SSOT for Done/Abandon)
            if hld_status == "done" or _is_completed_epic(slug, completed_slugs):
                status = "done"
            elif hld_status in ("abandon", "abandoned") or _is_completed_epic(
                slug, abandoned_slugs
            ):
                status = hld_status if hld_status in ("abandon", "abandoned") else "abandoned"
            elif (
                has_wt
                or hld_status == "in_progress"
                or (
                    _is_epic_eligible_for_active(
                        slug, completed_slugs, abandoned_slugs, hld_status
                    )
                    and (has_gate1_or_more or has_active_hb)
                )
            ):
                status = "in_progress"
            elif hld_status == "packaged":
                status = "packaged"
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
                        wt_mtimes = [
                            f.stat().st_mtime for f in features_dir.glob("task_*.md")
                        ]
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
    abandoned = sum(
        1 for e in epics if e["status"] in ("abandon", "abandoned", "discarded")
    )
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
        dt = datetime.fromisoformat(str(iso_str))
        now = datetime.now(timezone.utc)
        diff = now - dt
        secs = max(int(diff.total_seconds()), 0)
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


_SLOT_ACTIVE_STATUS_MAP: dict[str, str] = {
    "working": "in-progress",
    "in-progress": "in-progress",
    "in_progress": "in-progress",
    "running": "in-progress",
    "review": "review",
}
_TASK_NUM_RE = re.compile(r"^task_?0*(\d+)$")


def _slot_task_match_rank(task_id: str, slot_task_id: str) -> int:
    """Return match rank (3 exact, 2 bounded prefix, 1 strict task_N number, 0 none)."""
    norm_task = re.sub(r"\.md$", "", task_id.strip(), flags=re.IGNORECASE).lower()
    norm_slot = re.sub(r"\.md$", "", slot_task_id.strip(), flags=re.IGNORECASE).lower()
    if not norm_task or not norm_slot:
        return 0
    if norm_task == norm_slot:
        return 3
    if norm_task.startswith(f"{norm_slot}_"):
        return 2
    m_slot = _TASK_NUM_RE.match(norm_slot)
    if m_slot:
        num = int(m_slot.group(1))
        if re.match(rf"^task_?0*{num}(?:_|$)", norm_task):
            return 1
    return 0


def _apply_heartbeat_slot_statuses(
    repo_path: Path,
    all_tasks: list[dict[str, Any]],
    completed_slugs: set[str],
) -> None:
    """Overlay active heartbeat slot statuses (`working`/`review`) onto non-done tasks."""
    if not all_tasks:
        return
    hb_cache: dict[str, dict[str, Any] | None] = {}
    for task in all_tasks:
        ep = str(task.get("epic") or "").strip()
        if not ep or ep == "backlog" or _is_completed_epic(ep, completed_slugs):
            continue
        norm_ep = _normalize_slug(ep)
        if norm_ep not in hb_cache:
            hb_cache[norm_ep] = _read_epic_heartbeat(repo_path, ep)

    for norm_ep, hb in hb_cache.items():
        if not isinstance(hb, dict):
            continue
        hb_slug = hb.get("epic_slug")
        if hb_slug and _normalize_slug(str(hb_slug)) != norm_ep:
            continue
        slots = hb.get("slots")
        if not isinstance(slots, dict):
            continue
        ep_tasks = [
            t
            for t in all_tasks
            if _normalize_slug(str(t.get("epic") or "")) == norm_ep
        ]
        if not ep_tasks:
            continue
        for slot_key, slot_meta in slots.items():
            if not isinstance(slot_meta, dict):
                continue
            raw_slot_status = str(slot_meta.get("status") or "").strip().lower()
            mapped_status = _SLOT_ACTIVE_STATUS_MAP.get(raw_slot_status)
            slot_task_id = str(slot_meta.get("task_id") or "").strip()
            if not mapped_status or not slot_task_id:
                continue
            best_rank = 0
            matched: list[dict[str, Any]] = []
            for task in ep_tasks:
                rank = _slot_task_match_rank(str(task.get("id") or ""), slot_task_id)
                if rank > best_rank:
                    best_rank = rank
                    matched = [task]
                elif rank > 0 and rank == best_rank:
                    matched.append(task)
            for task in matched:
                if task.get("status") == "done":
                    continue
                task["status"] = mapped_status
                task["slot"] = str(slot_key)
                task["slot_status"] = raw_slot_status


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
                        if (
                            task_epic
                            and task_epic
                            not in (
                                ep,
                                ep.replace("_", "-"),
                                ep.replace("-", "_"),
                            )
                        ) or (not task_epic and d.name != ep and ep not in str(d)):
                            continue

                        seen_tasks.add(task_id)
                        status = normalize_task_status(fm.get("status"))

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
                            fm.get("completedAt")
                            or fm.get("modified")
                            or fm.get("created")
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

    _apply_heartbeat_slot_statuses(repo_path, all_tasks, completed_slugs)

    for t in all_tasks:
        st = str(t.get("status") or "todo")
        tally[st] = tally.get(st, 0) + 1

    # Sort all_tasks in natural numerical count order (e.g. Task 1, 2, ..., 9, 10, 11)
    def task_compare_key(t: dict[str, Any]) -> tuple[str, list[int | str]]:
        epic_name = str(t.get("epic") or "").lower()
        task_str = str(t.get("id") or t.get("title") or "")
        return (epic_name, natural_sort_key(task_str))

    all_tasks.sort(key=task_compare_key)

    # Re-derive active_task as the first in-progress (or review) task in natural numerical order
    active_task = None
    for target_status in ("in-progress", "review"):
        for t in all_tasks:
            if t.get("status") == target_status:
                active_task = t.get("title")
                break
        if active_task:
            break

    total = len(seen_tasks)
    done = tally["done"]
    in_prog = tally["in-progress"]
    todo = tally["todo"]
    backlog = tally["backlog"]
    review = tally["review"]
    if total <= 0:
        pct = 0.0
        task_completion_pct = 0.0
    elif done >= total:
        pct = 100.0 if _is_epic_converged_or_done(repo_path, active_epic) else 96.0
        task_completion_pct = 100.0
    else:
        pct = min(95.0, round((done / total * 100), 1))
        task_completion_pct = round((done / total * 100.0), 1)

    return TaskProgress(
        total_tasks=total,
        done_tasks=done,
        in_progress_tasks=in_prog,
        todo_tasks=todo,
        backlog_tasks=backlog,
        review_tasks=review,
        percentage=pct,
        task_completion_pct=task_completion_pct,
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
            _read_jsonl_ledger_file(
                devtool_dir / "state" / "gate_ledger.jsonl", norm_active
            )
        )
    for devtool_dir in devtool_dirs:
        _append_unique(
            _read_markdown_ledger_file(devtool_dir / "GATE_LEDGER.md", norm_active)
        )

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
    quality_runs = [
        entry for entry in sorted_entries if entry.get("status") == "running"
    ]

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
            unscoped = [
                e for e in sorted_entries if not str(e.get("epic_slug", "")).strip()
            ]
            live_unscoped = [e for e in unscoped if e.get("status") == "running"]
            quality_active = (
                live_unscoped[0]
                if live_unscoped
                else (unscoped[0] if unscoped else None)
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
            matched_pd.get("blocked", False) or "circuit_breaker" in pd_kind.lower()
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
                    if "design" in doc.name.lower() and not doc.name.startswith(
                        "task_"
                    ):
                        _add_candidate(doc)

    for candidate in candidates:
        with contextlib.suppress(OSError, UnicodeDecodeError):
            text = candidate.read_text(encoding="utf-8")
            for m in _PIC_LINE_RE.finditer(text):
                cleaned = _clean_pic_candidate(m.group(1))
                if cleaned:
                    return cleaned
    return None


def _get_short_head_sha(checkout_path: Path) -> str:
    """Return short HEAD SHA for a git checkout, or empty string on error."""
    with contextlib.suppress(Exception):
        res = subprocess.run(
            ["git", "-C", str(checkout_path), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    return ""


def _parse_review_rounds_summary(
    review_path: Path | None,
    head_sha: str,
    heartbeat: dict[str, Any] | None,
    quality_active: dict[str, Any] | None,
    kind: str,
) -> dict[str, Any]:
    """Parse principal_review.md or review_results.md and heartbeat into a review micro-step summary."""
    summary: dict[str, Any] = {
        "active": False,
        "round": 0,
        "max_rounds": 3,
        "cli": "",
        "model": "",
        "phase": "pending",
        "verdict": "",
        "action": "",
        "latest_sha": "",
        "converged": False,
        "has_fix_commit": False,
        "sub_steps": [],
    }
    rounds_data: list[dict[str, Any]] = []
    if review_path is not None and review_path.is_file():
        with contextlib.suppress(OSError, UnicodeDecodeError):
            text = review_path.read_text(encoding="utf-8")
            parts = re.split(r"(?m)^##\s+Round\s+(\d+)\b", text)
            for idx in range(1, len(parts), 2):
                r_num = int(parts[idx])
                body = parts[idx + 1] if idx + 1 < len(parts) else ""
                meta: dict[str, str] = {}
                for m in re.finditer(r"^-\s+\*\*([^*]+)\*\*:\s*(.+)$", body, re.MULTILINE):
                    meta[m.group(1).strip()] = m.group(2).strip()
                if meta.get("Status") and meta["Status"] != "completed":
                    continue
                crit = 0
                imp = 0
                minor = 0
                undecided_blocking = 0
                has_fixed = False
                for line in body.splitlines():
                    stripped = line.strip()
                    if not stripped.startswith("|") or stripped.startswith("|---") or "Severity" in stripped:
                        continue
                    cells = [c.strip() for c in stripped.strip("|").split("|")]
                    if len(cells) >= 5:
                        sev = cells[1]
                        dec = cells[4].lower()
                        if sev == "Critical":
                            crit += 1
                        elif sev == "Important":
                            imp += 1
                        elif sev == "Minor":
                            minor += 1
                        if dec.startswith("fixed in"):
                            has_fixed = True
                        if sev in ("Critical", "Important") and not dec.startswith(
                            ("fixed in", "dismissed:")
                        ):
                            undecided_blocking += 1
                rounds_data.append(
                    {
                        "round": r_num,
                        "sha": meta.get("SHA", ""),
                        "cli": meta.get("CLI", ""),
                        "model": meta.get("Model", ""),
                        "verdict": meta.get("Verdict", ""),
                        "crit": crit,
                        "imp": imp,
                        "minor": minor,
                        "undecided_blocking": undecided_blocking,
                        "has_fixed": has_fixed,
                    }
                )

    rs = (heartbeat or {}).get("review_state")
    hb_matches_kind = isinstance(rs, dict) and str(rs.get("kind") or "code") == kind

    if rounds_data:
        last = rounds_data[-1]
        summary["active"] = True
        summary["round"] = int(last["round"])
        summary["cli"] = str(last["cli"])
        summary["model"] = str(last["model"])
        summary["verdict"] = str(last["verdict"])
        summary["latest_sha"] = str(last["sha"])
        r_sha = str(last["sha"])
        has_fix_commit = bool(
            last["has_fixed"]
            or (
                r_sha
                and head_sha
                and not head_sha.startswith(r_sha)
                and not r_sha.startswith(head_sha)
            )
        )
        summary["has_fix_commit"] = has_fix_commit
        if (
            last["verdict"] == "PASS"
            or (last["crit"] == 0 and last["imp"] == 0)
            or (int(last["round"]) >= 3 and last["crit"] == 0 and last["undecided_blocking"] == 0)
        ):
            summary["converged"] = True
            summary["phase"] = "converged"
        elif has_fix_commit:
            hb_sub = str((heartbeat or {}).get("sub_step") or "")
            hb_phase = str(rs.get("phase") or "") if hb_matches_kind and isinstance(rs, dict) else ""
            qa_running_or_on_sha = bool(
                quality_active
                and (
                    quality_active.get("status") == "running"
                    or (head_sha and str(quality_active.get("head_sha") or "") == head_sha)
                )
            )
            if (
                hb_phase == "verifying"
                or hb_sub.startswith("task_")
                or hb_sub in ("quality_check", "audit_epic", "bdd_tests")
                or qa_running_or_on_sha
            ):
                summary["phase"] = "verifying"
            else:
                summary["phase"] = "fixing"
        else:
            summary["phase"] = "triage"

    if hb_matches_kind and isinstance(rs, dict):
        summary["active"] = True
        hb_round = int(rs.get("round") or summary["round"] or 1)
        summary["max_rounds"] = int(rs.get("max_rounds") or 3)
        if rs.get("cli"):
            summary["cli"] = str(rs["cli"])
        if rs.get("model"):
            summary["model"] = str(rs["model"])
        if rs.get("action"):
            summary["action"] = str(rs["action"])
        if rs.get("verdict"):
            summary["verdict"] = str(rs["verdict"])
        hb_phase = str(rs.get("phase") or "")
        if hb_round > int(summary["round"]) or not rounds_data:
            summary["round"] = hb_round
            if hb_phase:
                summary["phase"] = hb_phase
                summary["converged"] = hb_phase == "converged"
        elif hb_phase in ("fixing", "verifying", "converged"):
            summary["phase"] = hb_phase
            if hb_phase == "converged":
                summary["converged"] = True
        elif hb_phase == "triage" and not summary["has_fix_commit"] and not summary["converged"]:
            summary["phase"] = "triage"

    phase_order = ["reviewing", "triage", "fixing", "verifying"]
    cur_phase = str(summary["phase"])
    cli_label = summary["cli"] or "reviewer"
    if summary["model"]:
        cli_label = f"{cli_label} ({summary['model']})"
    for p_id, p_label in (
        ("reviewing", "Reviewing"),
        ("triage", "Lập bảng triage"),
        ("fixing", "Fix findings"),
        ("verifying", "Verifying"),
    ):
        if cur_phase == "converged":
            st = "done"
        elif cur_phase in phase_order:
            c_idx = phase_order.index(cur_phase)
            p_idx = phase_order.index(p_id)
            if p_idx < c_idx:
                st = "done"
            elif p_idx == c_idx:
                st = "failed" if summary.get("action") == "CIRCUIT_BREAKER_HALT" else "running"
            else:
                st = "pending"
        else:
            st = "pending"
        detail = ""
        if p_id == "reviewing":
            detail = cli_label if summary["active"] else ""
        elif p_id == "triage" and summary["verdict"]:
            detail = summary["verdict"]
            if summary["action"]:
                detail = f"{detail} ({summary['action']})"
        summary["sub_steps"].append(
            {
                "id": p_id,
                "label": p_label,
                "status": st,
                "detail": detail,
            }
        )
    return summary


def build_epic_pipeline_telemetry(
    repo_path: Path,
    epic_slug: str,
    *,
    done_tasks: int = 0,
    total_tasks: int = 0,
    heartbeat: dict[str, Any] | None = None,
    quality_active: dict[str, Any] | None = None,
    pending_decision: dict[str, Any] | None = None,
    active_stage: str | None = None,
    is_completed: bool = False,
) -> dict[str, Any]:
    """Synthesize deterministic 6-stage /dev-lifecycle progress, sub-steps, and rolling events."""
    if heartbeat is None:
        heartbeat = _read_epic_heartbeat(repo_path, epic_slug)
    if quality_active is None:
        quality_active, _ = _read_quality_state(repo_path, epic_slug)

    wt_path = find_epic_worktree_path(repo_path, epic_slug)
    head_sha = _get_short_head_sha(wt_path)
    epic_dirs = [
        *_find_epic_dirs_for_checkout(wt_path, epic_slug),
        *_find_epic_dirs_for_checkout(repo_path, epic_slug),
    ]
    has_spec = False
    has_hld = False
    has_bdd = False
    has_handoff = False
    principal_file: Path | None = None
    code_review_file: Path | None = None
    dir_task_count = 0

    for ed in epic_dirs:
        if not ed.is_dir():
            continue
        with contextlib.suppress(OSError):
            for f in ed.iterdir():
                if not f.is_file():
                    continue
                low = f.name.lower()
                if "design" in low or "spec" in low:
                    has_spec = True
                if f.name in (f"{epic_slug}.en.md", f"{epic_slug}.vi.md", f"{ed.name}.en.md", "hld.en.md"):
                    has_hld = True
                if low.startswith("bdd_scenarios"):
                    has_bdd = True
                if f.name == "handoff.md":
                    has_handoff = True
                if f.name == "principal_review.md" and principal_file is None:
                    principal_file = f
                if f.name == "review_results.md" and code_review_file is None:
                    code_review_file = f
            dir_task_count = max(dir_task_count, len(list(ed.glob("task_*.md"))))

    if total_tasks == 0 and dir_task_count > 0:
        total_tasks = dir_task_count

    has_wt = (
        (repo_path / ".worktrees" / epic_slug).is_dir()
        or bool(_collect_matching_worktrees(repo_path, epic_slug))
    )
    gate_entries = parse_gate_ledger_entries(repo_path, epic_slug)
    approved_gates = {int(g["gate"]) for g in gate_entries if "gate" in g}
    gate4_commits = [
        str(g.get("commit", "")).strip()
        for g in gate_entries
        if int(g.get("gate", 0)) == 4 and str(g.get("commit", "")).strip()
    ]
    latest_gate4_sha = gate4_commits[-1] if gate4_commits else ""

    principal_rev = _parse_review_rounds_summary(
        principal_file, head_sha, heartbeat, quality_active, "principal"
    )
    code_rev = _parse_review_rounds_summary(
        code_review_file, head_sha, heartbeat, quality_active, "code"
    )

    events_raw = (heartbeat or {}).get("events")
    events: list[dict[str, str]] = (
        [dict(e) for e in events_raw if isinstance(e, dict)]
        if isinstance(events_raw, list)
        else []
    )
    hb_sub_step = str((heartbeat or {}).get("sub_step") or "")

    audit_done = (
        4 in approved_gates
        or 5 in approved_gates
        or is_completed
        or code_review_file is not None
        or hb_sub_step == "audit_epic"
        or any("audit_epic" in str(ev.get("message", "")) and "PASS" in str(ev.get("message", "")) for ev in events)
    )
    bdd_done = (
        4 in approved_gates
        or 5 in approved_gates
        or is_completed
        or code_review_file is not None
        or hb_sub_step == "bdd_tests"
        or any("check_bdd_traceability tests" in str(ev.get("message", "")) and "PASS" in str(ev.get("message", "")) for ev in events)
    )
    qa_status = str((quality_active or {}).get("status") or "")
    qa_passed = 4 in approved_gates or 5 in approved_gates or is_completed or qa_status == "passed"
    gate4_full_pass = bool(
        is_completed
        or 4 in approved_gates
        or 5 in approved_gates
        or (audit_done and bdd_done and qa_passed)
    )

    gate4_pass_on_current_sha = False
    if is_completed or 5 in approved_gates:
        gate4_pass_on_current_sha = True
    elif gate4_full_pass and qa_status != "running":
        rev_sha = str(code_rev.get("latest_sha") or "")
        qa_sha = str((quality_active or {}).get("head_sha") or "")
        if rev_sha and head_sha and not head_sha.startswith(rev_sha) and not rev_sha.startswith(head_sha):
            gate4_pass_on_current_sha = bool(
                (latest_gate4_sha and (head_sha.startswith(latest_gate4_sha) or latest_gate4_sha.startswith(head_sha)))
                or (qa_status == "passed" and qa_sha and (head_sha.startswith(qa_sha) or qa_sha.startswith(head_sha)))
            )
        elif qa_sha and head_sha and not head_sha.startswith(qa_sha) and not qa_sha.startswith(head_sha):
            gate4_pass_on_current_sha = bool(
                latest_gate4_sha and (head_sha.startswith(latest_gate4_sha) or latest_gate4_sha.startswith(head_sha))
            )
        else:
            gate4_pass_on_current_sha = True

    if is_completed and total_tasks == 0:
        task_completion_pct = 100.0
    elif total_tasks <= 0:
        task_completion_pct = 0.0
    else:
        task_completion_pct = min(100.0, round((done_tasks / total_tasks) * 100.0, 1))

    all_tasks_done = total_tasks > 0 and done_tasks >= total_tasks

    # Monotonic weighted lifecycle_progress_pct & current_stage_index (1..6)
    if is_completed or 5 in approved_gates:
        lifecycle_progress_pct = 100.0
        current_stage_index = 6
    elif (
        all_tasks_done
        and (code_rev["converged"] or _has_review_converged_hint(repo_path, epic_slug, pending_decision))
        and gate4_pass_on_current_sha
    ):
        lifecycle_progress_pct = 98.0
        current_stage_index = 6
    elif all_tasks_done and (code_rev["active"] or code_rev["round"] >= 1 or gate4_full_pass):
        if not code_rev["active"] and code_rev["round"] == 0:
            lifecycle_progress_pct = 88.0
            current_stage_index = 4
        elif code_rev["converged"] or not gate4_pass_on_current_sha:
            lifecycle_progress_pct = 96.0
            current_stage_index = 4 if qa_status == "running" else 5
        else:
            r_num = max(1, int(code_rev["round"]))
            phase = str(code_rev["phase"])
            phase_offsets = {"reviewing": 0.0, "triage": 1.0, "fixing": 1.8, "verifying": 2.4}
            base_r = 89.0 + (r_num - 1) * 2.5
            lifecycle_progress_pct = min(96.0, round(base_r + phase_offsets.get(phase, 0.5), 1))
            current_stage_index = 5
    elif all_tasks_done:
        if qa_status == "passed":
            lifecycle_progress_pct = 87.0
            current_stage_index = 4
        elif qa_status in ("running", "failed", "aborted"):
            s_idx = int((quality_active or {}).get("step_index") or 1)
            s_tot = max(1, int((quality_active or {}).get("step_total") or 1))
            lifecycle_progress_pct = round(81.0 + min(1.0, s_idx / s_tot) * 5.0, 1)
            current_stage_index = 4
        else:
            lifecycle_progress_pct = 80.0
            current_stage_index = 4 if hb_sub_step in ("audit_epic", "bdd_tests", "quality_check") else 3
    elif 3 in approved_gates or has_wt or done_tasks > 0:
        ratio = (done_tasks / total_tasks) if total_tasks > 0 else 0.0
        lifecycle_progress_pct = min(79.0, round(25.0 + ratio * 55.0, 1))
        current_stage_index = 3
    elif has_handoff:
        lifecycle_progress_pct = 25.0
        current_stage_index = 2
    elif principal_rev["active"] or principal_rev["round"] >= 1:
        r_num = max(1, int(principal_rev["round"]))
        lifecycle_progress_pct = min(24.0, round(19.0 + r_num * 1.5, 1))
        current_stage_index = 2
    elif 2 in approved_gates or total_tasks > 0:
        lifecycle_progress_pct = 18.0
        current_stage_index = 2
    elif has_hld or has_bdd:
        lifecycle_progress_pct = 14.0
        current_stage_index = 2
    elif 1 in approved_gates:
        lifecycle_progress_pct = 10.0
        current_stage_index = 2
    else:
        lifecycle_progress_pct = 5.0 if has_spec else 0.0
        current_stage_index = 1

    # Build 6 stages with sub_steps
    s1_done = 1 in approved_gates or lifecycle_progress_pct >= 10.0
    s1_status = "done" if s1_done else ("running" if has_spec else "pending")
    s1_sub = [
        {"id": "spec_doc", "label": "Design Spec", "status": "done" if (has_spec or s1_done) else "running", "detail": ""},
        {"id": "gate_1", "label": "Gate 1 Sign-Off", "status": "done" if s1_done else "pending", "detail": ""},
    ]

    s2_done = has_handoff or 3 in approved_gates or lifecycle_progress_pct > 25.0
    s2_status = (
        "done"
        if s2_done
        else (
            "failed"
            if principal_rev.get("action") == "CIRCUIT_BREAKER_HALT"
            else ("running" if s1_done or has_hld else "pending")
        )
    )
    s2_sub: list[dict[str, str]] = [
        {"id": "hld_bdd", "label": "HLD & BDD", "status": "done" if (has_hld and has_bdd) or s2_done else ("running" if s1_done else "pending"), "detail": ""},
        {"id": "gate_2", "label": "Gate 2 & Tasks", "status": "done" if (2 in approved_gates or s2_done) else ("running" if has_hld else "pending"), "detail": f"{total_tasks} tasks" if total_tasks else ""},
    ]
    if principal_rev["active"] or s2_done:
        for sub in principal_rev["sub_steps"]:
            s2_sub.append(
                {
                    "id": f"principal_{sub['id']}",
                    "label": f"Principal: {sub['label']}",
                    "status": "done" if s2_done else sub["status"],
                    "detail": sub["detail"],
                }
            )
    s2_sub.append(
        {"id": "package", "label": "Package handoff.md", "status": "done" if (has_handoff or s2_done) else "pending", "detail": ""}
    )

    s3_done = all_tasks_done or is_completed or lifecycle_progress_pct >= 80.0
    s3_status = "done" if s3_done else ("running" if (3 in approved_gates or has_wt or done_tasks > 0) else "pending")
    s3_sub: list[dict[str, str]] = []
    active_wave = (heartbeat or {}).get("active_wave")
    if active_wave is not None and str(active_wave) != "":
        s3_sub.append(
            {"id": "wave", "label": f"Wave {active_wave}", "status": "done" if s3_done else "running", "detail": f"{done_tasks}/{total_tasks} ({int(task_completion_pct)}%)"}
        )
    slots_map = (heartbeat or {}).get("slots")
    if isinstance(slots_map, dict):
        for slot_k, slot_v in sorted(slots_map.items()):
            if isinstance(slot_v, dict):
                t_id = str(slot_v.get("task_id") or "idle")
                sl_st = str(slot_v.get("status") or "idle")
                s3_sub.append(
                    {
                        "id": f"slot_{slot_k}",
                        "label": f"Slot {slot_k}: {t_id}",
                        "status": "done" if s3_done else ("running" if sl_st in ("working", "review") else "pending"),
                        "detail": sl_st,
                    }
                )
    s3_sub.append(
        {
            "id": "tasks_tally",
            "label": f"Tasks {done_tasks}/{total_tasks}",
            "status": "done" if s3_done else ("running" if done_tasks > 0 else "pending"),
            "detail": f"{int(task_completion_pct)}%",
        }
    )

    s4_done = gate4_full_pass and qa_status != "running"
    s4_status = (
        "failed"
        if qa_status in ("failed", "aborted")
        else ("running" if (qa_status == "running" or current_stage_index == 4) else ("done" if s4_done else "pending"))
    )
    s4_sub: list[dict[str, str]] = [
        {"id": "audit_epic", "label": "Epic Audit", "status": "done" if audit_done else ("running" if s3_done and current_stage_index == 4 else "pending"), "detail": ""},
        {"id": "bdd_traceability", "label": "BDD Traceability", "status": "done" if bdd_done else "pending", "detail": ""},
    ]
    qa_steps = (quality_active or {}).get("steps")
    if isinstance(qa_steps, list) and qa_steps:
        for st_item in qa_steps:
            if not isinstance(st_item, dict):
                continue
            raw_st = str(st_item.get("status") or "pending")
            mapped_st = "done" if raw_st == "passed" else raw_st
            el = st_item.get("elapsed_sec")
            el_detail = f"{float(el):.1f}s" if isinstance(el, (int, float)) else ""
            s4_sub.append(
                {
                    "id": f"qa_{st_item.get('capability', '')}",
                    "label": str(st_item.get("label") or st_item.get("capability") or "Quality Step"),
                    "status": mapped_st,
                    "detail": el_detail,
                }
            )
    elif quality_active:
        cap_lbl = str(quality_active.get("capability_label") or quality_active.get("capability") or "Quality Check")
        s_idx = int(quality_active.get("step_index") or 0)
        s_tot = int(quality_active.get("step_total") or 0)
        s4_sub.append(
            {
                "id": "qa_active",
                "label": cap_lbl,
                "status": "done" if qa_status == "passed" else (qa_status or "pending"),
                "detail": f"{s_idx}/{s_tot}" if s_tot else "",
            }
        )

    s5_done = bool(is_completed or 5 in approved_gates or (code_rev["converged"] and gate4_pass_on_current_sha))
    s5_status = (
        "done"
        if s5_done
        else (
            "failed"
            if code_rev.get("action") == "CIRCUIT_BREAKER_HALT"
            else ("running" if (code_rev["active"] or current_stage_index == 5) else "pending")
        )
    )
    s5_sub = list(code_rev["sub_steps"])

    s6_done = bool(is_completed or 5 in approved_gates)
    s6_status = "done" if s6_done else ("action_required" if lifecycle_progress_pct >= 98.0 else "pending")
    s6_sub = [
        {"id": "gate_5", "label": "Gate 5 Sign-Off & Merge", "status": "done" if s6_done else ("running" if lifecycle_progress_pct >= 98.0 else "pending"), "detail": ""},
    ]

    stages = [
        {
            "id": "spec",
            "index": 1,
            "label": "1. Spec",
            "status": s1_status,
            "summary": "Gate 1 PASS" if s1_done else "Brainstorming Spec",
            "sub_steps": s1_sub,
        },
        {
            "id": "hld_principal",
            "index": 2,
            "label": "2. HLD & Principal",
            "status": s2_status,
            "summary": (
                "Packaged & Ready"
                if s2_done
                else (
                    f"Principal R{principal_rev['round']}/{principal_rev['max_rounds']} · {principal_rev['phase']}"
                    if principal_rev["active"]
                    else "HLD, BDD & Tasks"
                )
            ),
            "sub_steps": s2_sub,
        },
        {
            "id": "tasks",
            "index": 3,
            "label": "3. Tasks",
            "status": s3_status,
            "summary": f"{done_tasks}/{total_tasks} ({int(task_completion_pct)}%)",
            "sub_steps": s3_sub,
        },
        {
            "id": "gate4_quality",
            "index": 4,
            "label": "4. Gate 4 QA",
            "status": s4_status,
            "summary": (
                "Audit + BDD + QA PASS"
                if s4_done
                else (
                    str((quality_active or {}).get("capability_label") or (quality_active or {}).get("capability") or "Running QA")
                    if qa_status == "running"
                    else ("QA Passed (87%)" if qa_status == "passed" else "Pending Gate 4")
                )
            ),
            "sub_steps": s4_sub,
        },
        {
            "id": "cross_review",
            "index": 5,
            "label": "5. Cross-Review",
            "status": s5_status,
            "summary": (
                f"Converged (R{max(1, int(code_rev['round']))} PASS)"
                if s5_done
                else (
                    f"Round {code_rev['round']}/{code_rev['max_rounds']} · {code_rev['cli'] or 'reviewer'} · {code_rev['phase']}"
                    if code_rev["active"]
                    else "Pending Review"
                )
            ),
            "sub_steps": s5_sub,
        },
        {
            "id": "finish",
            "index": 6,
            "label": "6. Finish",
            "status": s6_status,
            "summary": "Merged & Archived" if s6_done else ("Waiting /finish (Gate 5)" if lifecycle_progress_pct >= 98.0 else "Pending Gate 5"),
            "sub_steps": s6_sub,
        },
    ]

    cur_stage_obj = stages[max(0, min(5, current_stage_index - 1))]
    active_sub_summary = f"{cur_stage_obj['label']} · {cur_stage_obj['summary']}"

    return {
        "epic_slug": epic_slug,
        "task_completion_pct": task_completion_pct,
        "lifecycle_progress_pct": lifecycle_progress_pct,
        "current_stage_index": current_stage_index,
        "active_sub_step_summary": active_sub_summary,
        "stages": stages,
        "events": events,
    }


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

    # Propagate deterministic action requirements and pipeline_telemetry to each epic in epics_summary
    completed_slugs = get_completed_epic_slugs(repo_path)
    pipeline_telemetry = (
        build_epic_pipeline_telemetry(
            repo_path,
            active_epic,
            done_tasks=task_progress.done_tasks,
            total_tasks=task_progress.total_tasks,
            heartbeat=heartbeat,
            quality_active=quality_active,
            pending_decision=matched_pending,
            active_stage=active_stage,
            is_completed=bool(active_epic and _is_completed_epic(active_epic, completed_slugs)),
        )
        if active_epic
        else None
    )
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
                    decision.stage_name
                    == LifecycleStage.STAGE_3_PHASE_4_1_SIGNOFF.value
                    or bool(
                        pipeline_telemetry
                        and float(pipeline_telemetry.get("lifecycle_progress_pct", 0.0)) >= 98.0
                    )
                )
                ep["pipeline_telemetry"] = pipeline_telemetry
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
                            for k in (
                                "review converged",
                                "gate 5",
                                "sign-off",
                                "finish",
                            )
                        ):
                            ep_conv = True
                ep["is_action_required"] = ep_act
                if ep_prompt and not ep.get("action_prompt"):
                    ep["action_prompt"] = ep_prompt
                ep["is_review_converged"] = ep_conv
                if ep.get("status") == "in_progress":
                    ep_tasks = [
                        t
                        for t in task_progress.tasks
                        if _normalize_slug(str(t.get("epic") or "")) == _normalize_slug(slug)
                    ]
                    ep_done = sum(1 for t in ep_tasks if t.get("status") == "done")
                    ep_tot = len(ep_tasks) or int(ep.get("task_count") or 0)
                    ep["pipeline_telemetry"] = build_epic_pipeline_telemetry(
                        repo_path,
                        slug,
                        done_tasks=ep_done,
                        total_tasks=ep_tot,
                        pending_decision=ep_pd,
                    )

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
        pipeline_telemetry=pipeline_telemetry,
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
    review_str = (
        f", {repo.task_progress.review_tasks} review"
        if repo.task_progress.review_tasks > 0
        else ""
    )
    lines.append(
        f"Tasks: {bar} {int(pct)}% "
        f"({repo.task_progress.done_tasks}/{repo.task_progress.total_tasks} done, "
        f"{repo.task_progress.in_progress_tasks} in-progress"
        f"{review_str}, "
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
        "--restart",
        action="store_true",
        help="Restart background HTTP dashboard server",
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

    if args.ui or args.stop or args.status or args.restart:
        server_script = Path(__file__).resolve().parent / "tasks_server.py"
        if not server_script.is_file():
            sys.stderr.write(f"Error: tasks_server.py not found at {server_script}\n")
            return 1
        cmd = [sys.executable, str(server_script)]
        cmd.extend(["--workspace-root", str(args.workspace_root)])
        if args.restart:
            cmd.append("--restart")
        if args.ui or args.restart:
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
