"""Multi-repo harvester engine and data models for check-tasks dashboard.

Provides high-performance multi-repo discovery, git worktree parsing,
.vscode styling extraction, task progress aggregation, and two-tier project memory inspection.
"""

from __future__ import annotations

from collections.abc import Iterator
import concurrent.futures
import contextlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import threading
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
_STATE_ENVELOPE_MOD: Any | None = None
_SCAN_CTX = threading.local()
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

_KIT_LOAD_LOCK = threading.Lock()
_EPIC_DOCS_REL = (
    "skills",
    "dev-implementation",
    "resources",
    "scripts",
    "_epic_docs.py",
)
_PERSONA_CONFIG_REL = ("scripts", "persona_config.py")
_AGY_POOL_REL = ("scripts", "agy_profile_pool.py")


def _load_kit_module(name: str, *rel_parts: str) -> Any:
    """Load a kit module by file path (never via sys.path); raise RuntimeError when absent."""
    with _KIT_LOAD_LOCK:
        cached = sys.modules.get(name)
        if cached is not None:
            return cached
        for parent in [SCRIPT_DIR, *SCRIPT_DIR.parents]:
            candidate = parent.joinpath(*rel_parts)
            if not candidate.is_file():
                continue
            spec = importlib.util.spec_from_file_location(name, str(candidate))
            if spec is None or spec.loader is None:
                raise RuntimeError(f"Failed to create module spec for {candidate}")
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            try:
                spec.loader.exec_module(module)
            except Exception:
                sys.modules.pop(name, None)
                raise
            return module
    raise RuntimeError(f"Required kit module not found: {'/'.join(rel_parts)}")


def epic_doc_path(directory: Path, stem: str) -> Path | None:
    """Resolve `<stem>.md`, else legacy `<stem>.en.md`; never a `.vi.md` mirror."""
    try:
        return _load_kit_module("_epic_docs", *_EPIC_DOCS_REL).resolve_epic_doc(
            directory, stem
        )
    except (RuntimeError, ImportError, SyntaxError):
        for ext in (".md", ".en.md"):
            candidate = Path(directory) / f"{stem}{ext}"
            if candidate.is_file():
                return candidate
        return None


def design_spec_paths(directory: Path) -> list[Path]:
    """Return `*-design.md` then legacy `*-design.en.md` specs in `directory`, never `.vi.md`."""
    try:
        return list(
            _load_kit_module("_epic_docs", *_EPIC_DOCS_REL).resolve_design_specs(
                directory
            )
        )
    except (RuntimeError, ImportError, SyntaxError):
        found: list[Path] = []
        if Path(directory).is_dir():
            for pattern in ("*-design.md", "*-design.en.md"):
                found.extend(sorted(Path(directory).glob(pattern)))
        return found


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
    completed_tasks: list[dict[str, Any]] = field(default_factory=list)


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
    doing_count: int = 0
    pending_count: int = 0
    cancelled_count: int = 0
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
    action_blockers: list[dict[str, str]] = field(default_factory=list)
    persona_bindings: list[dict[str, Any]] = field(default_factory=list)
    persona_config_error: str | None = None
    checkpoint: dict[str, Any] | None = None
    low_quota: dict[str, Any] | None = None
    agy_pool: dict[str, Any] | None = None
    agy_profiles: list[dict[str, Any]] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)


@dataclass
class DashboardGraph:
    """Unified graph data model representing all harvested repositories."""

    workspace_root: str
    scanned_at: str
    repos: list[RepoMetadata]
    metrics_row: dict[str, Any] = field(default_factory=dict)
    available_profiles: list[str] = field(default_factory=list)
    tracked_projects: list[dict[str, str]] | None = None


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
    """Discover all git worktrees and detect uncommitted modifications in parallel."""
    cache = getattr(_SCAN_CTX, "cache", None)
    cache_key = ("worktrees", str(repo_path))
    if isinstance(cache, dict) and cache_key in cache:
        return list(cache[cache_key])

    worktrees: list[WorktreeMetadata] = []
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_path), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        if isinstance(cache, dict):
            cache[cache_key] = worktrees
        return worktrees

    parsed_entries: list[tuple[str, str | None, str, bool]] = []
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
        if wt_path:
            parsed_entries.append((wt_path, branch, head_sha, is_detached))
            if isinstance(cache, dict) and head_sha:
                cache[("head_sha", str(Path(wt_path)))] = head_sha

    def _probe_dirty(wt_p: str) -> tuple[bool, int, str]:
        if "/.gemini/antigravity/worktrees/" in wt_p or not Path(wt_p).is_dir():
            return False, 0, ""
        with contextlib.suppress(subprocess.SubprocessError, OSError):
            st = subprocess.run(
                ["git", "-C", wt_p, "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            stdout = st.stdout or ""
            dirty_lines = [l for l in stdout.splitlines() if l.strip()]
            return len(dirty_lines) > 0, len(dirty_lines), stdout
        return False, 0, ""

    dirty_results: dict[str, tuple[bool, int, str]] = {}
    if len(parsed_entries) > 1:
        pool_size = min(8, len(parsed_entries))
        with concurrent.futures.ThreadPoolExecutor(max_workers=pool_size) as pool:
            futs = {
                pool.submit(_probe_dirty, wt_p): wt_p
                for wt_p, _, _, _ in parsed_entries
            }
            for fut in concurrent.futures.as_completed(futs):
                wt_p = futs[fut]
                dirty_results[wt_p] = fut.result()
    elif len(parsed_entries) == 1:
        wt_p = parsed_entries[0][0]
        dirty_results[wt_p] = _probe_dirty(wt_p)

    for wt_path, branch, head_sha, is_detached in parsed_entries:
        is_dirty, dirty_file_count, porcelain_stdout = dirty_results.get(
            wt_path, (False, 0, "")
        )
        if isinstance(cache, dict):
            cache[("git_status_porcelain", str(Path(wt_path)))] = porcelain_stdout
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

    if isinstance(cache, dict):
        cache[cache_key] = list(worktrees)
    return worktrees


_HLD_STATUS_PATTERNS = (
    re.compile(
        r"^(?:>\s*)?(?:-\s*)?\*\*Status(?:\*\*\s*:|\s*:\*\*)\s*([^\n\r]+)$",
        re.MULTILINE | re.IGNORECASE,
    ),
    re.compile(
        r"^\|\s*\*{0,2}Status\*{0,2}\s*\|\s*([^|\n\r]+?)\s*\|",
        re.MULTILINE | re.IGNORECASE,
    ),
    re.compile(
        r"^Status\s*:\s*([^\n\r]+)$",
        re.MULTILINE | re.IGNORECASE,
    ),
    re.compile(
        r"^#{2,3}\s+Status\s*\n+\s*([^\n\r#|]+)$",
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
    """Extract epic lifecycle status from the English HLD (`<slug>.md`, legacy `.en.md`) or other `*.md` files."""
    cache = getattr(_SCAN_CTX, "cache", None)
    cache_key = ("hld_status", str(epic_dir), slug)
    if isinstance(cache, dict) and cache_key in cache:
        return cache[cache_key]

    result: str | None = None
    primary = epic_doc_path(epic_dir, slug)
    candidates: list[Path] = [primary] if primary is not None else []
    with contextlib.suppress(OSError):
        for f in sorted(epic_dir.glob("*.md")):
            if (
                f not in candidates
                and not f.name.endswith(".vi.md")
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
                    result = classified
                    break
        if result is not None:
            break

    if isinstance(cache, dict):
        cache[cache_key] = result
    return result


def get_completed_epic_slugs(repo_path: Path) -> set[str]:
    """Harvest completed epic slugs from PROJECT_LEDGER.md, archive, and HLD design documents."""
    cache = getattr(_SCAN_CTX, "cache", None)
    cache_key = ("completed_slugs", str(repo_path))
    if isinstance(cache, dict) and cache_key in cache:
        return _NormalizedSlugSet(cache[cache_key])

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

    if isinstance(cache, dict):
        cache[cache_key] = _NormalizedSlugSet(completed)
    return _NormalizedSlugSet(completed)


def get_abandoned_epic_slugs(repo_path: Path) -> set[str]:
    """Harvest abandoned epic slugs from .devtool/epic/<slug>/ HLD design documents."""
    cache = getattr(_SCAN_CTX, "cache", None)
    cache_key = ("abandoned_slugs", str(repo_path))
    if isinstance(cache, dict) and cache_key in cache:
        return _NormalizedSlugSet(cache[cache_key])

    abandoned: set[str] = set()
    epic_dir = repo_path / ".devtool" / "epic"
    if epic_dir.is_dir():
        with contextlib.suppress(OSError):
            for d in epic_dir.iterdir():
                if not d.is_dir() or d.name.startswith("."):
                    continue
                if extract_epic_hld_status(d, d.name) in ("abandon", "abandoned"):
                    abandoned.add(d.name)

    if isinstance(cache, dict):
        cache[cache_key] = _NormalizedSlugSet(abandoned)
    return _NormalizedSlugSet(abandoned)


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


class _NormalizedSlugSet(set[str]):
    """set[str] maintaining a synchronized normalized slug index for O(1) lookup."""

    def __init__(self, items: Any = ()) -> None:
        super().__init__(items)
        if isinstance(items, _NormalizedSlugSet):
            self._norm: set[str] = set(items._norm)
        else:
            self._norm = {_normalize_slug(s) for s in self}

    def add(self, element: str) -> None:
        super().add(element)
        self._norm.add(_normalize_slug(element))

    def update(self, *others: Any) -> None:
        super().update(*others)
        self._norm = {_normalize_slug(s) for s in self}

    def discard(self, element: str) -> None:
        super().discard(element)
        self._norm = {_normalize_slug(s) for s in self}

    def remove(self, element: str) -> None:
        super().remove(element)
        self._norm = {_normalize_slug(s) for s in self}

    def clear(self) -> None:
        super().clear()
        self._norm.clear()


def _is_completed_epic(slug: str, completed_slugs: set[str]) -> bool:
    """Return True if slug matches any completed epic across dash/underscore forms."""
    if not slug or not completed_slugs:
        return False
    if slug in completed_slugs:
        return True
    norm = _normalize_slug(slug)
    if isinstance(completed_slugs, _NormalizedSlugSet):
        return norm in completed_slugs._norm
    return any(_normalize_slug(c) == norm for c in completed_slugs)


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


def _worktree_matches_slug(
    candidate_path: Path, target_norm: str, branch_name: str | None = None
) -> bool:
    """Return True if worktree directory name or epic/feat branch matches `target_norm`."""
    if _normalize_slug(_strip_slot_suffix(candidate_path.name)) == target_norm:
        return True
    if branch_name:
        m_br = re.match(r"(?:epic|feat)/([a-zA-Z0-9_\-]+)", branch_name)
        if m_br:
            return _normalize_slug(_strip_slot_suffix(m_br.group(1))) == target_norm
    return False


def _collect_matching_worktrees_with_branches(
    repo_path: Path, epic_slug: str | None = None
) -> list[tuple[Path, str | None]]:
    """Discover unique non-root worktrees (with git branch if known) matching `epic_slug`."""
    target_norm = _normalize_slug(_strip_slot_suffix(epic_slug)) if epic_slug else None
    cache = getattr(_SCAN_CTX, "cache", None)
    match_key = ("matching_wt", str(repo_path), target_norm)
    if isinstance(cache, dict) and match_key in cache:
        return list(cache[match_key])

    all_key = ("all_nonroot_wt", str(repo_path))
    if isinstance(cache, dict) and all_key in cache:
        all_worktrees: list[tuple[Path, str | None]] = cache[all_key]
    else:
        all_worktrees = []
        seen: set[Path] = set()
        root_resolved = repo_path.resolve()

        def _maybe_add(candidate_path: Path, branch_name: str | None = None) -> None:
            if not candidate_path.is_dir():
                return
            resolved = candidate_path.resolve()
            if resolved == root_resolved or resolved in seen:
                return
            seen.add(resolved)
            all_worktrees.append((candidate_path, branch_name))

        for wt in scan_worktrees(repo_path):
            _maybe_add(Path(wt.path), wt.branch)

        wt_dir = repo_path / ".worktrees"
        if wt_dir.is_dir():
            with contextlib.suppress(OSError):
                for d in sorted(wt_dir.iterdir()):
                    if not d.is_dir() or d.name.startswith("."):
                        continue
                    _maybe_add(d)

        if isinstance(cache, dict):
            cache[all_key] = list(all_worktrees)

    if target_norm is None:
        results = list(all_worktrees)
    else:
        results = [
            (candidate_path, branch_name)
            for candidate_path, branch_name in all_worktrees
            if _worktree_matches_slug(candidate_path, target_norm, branch_name)
        ]

    if isinstance(cache, dict):
        cache[match_key] = list(results)
    return results


def _collect_matching_worktrees(
    repo_path: Path, epic_slug: str | None = None
) -> list[Path]:
    """Discover unique non-root worktrees matching `epic_slug` (or all worktrees when None)."""
    return [
        wt_path
        for wt_path, _ in _collect_matching_worktrees_with_branches(
            repo_path, epic_slug
        )
    ]


def _collect_devtool_dirs(
    repo_path: Path, active_epic: str | None = None
) -> list[Path]:
    """Collect unique `.devtool` directories across root, worktrees, and git common dir."""
    cache = getattr(_SCAN_CTX, "cache", None)
    cache_key = ("devtool_dirs", str(repo_path), active_epic)
    if isinstance(cache, dict) and cache_key in cache:
        return list(cache[cache_key])

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
        shared_key = ("shared_devtool_dirs", str(repo_path))
        if isinstance(cache, dict) and shared_key in cache:
            shared_dirs = cache[shared_key]
        else:
            shared_dirs = []
            with contextlib.suppress(Exception):
                shared_dirs = list(state_env.resolve_shared_devtool_dirs(repo_path))
            if isinstance(cache, dict):
                cache[shared_key] = shared_dirs
        for shared_dir in shared_dirs:
            _add_dir(shared_dir)

    if isinstance(cache, dict):
        cache[cache_key] = list(dirs)
    return dirs


def _get_cached_target_devtool_dirs(
    state_env: Any, repo_path: Path, filename: str
) -> list[Path]:
    cache = getattr(_SCAN_CTX, "cache", None)
    key = ("target_devtool_dirs", str(repo_path))
    if isinstance(cache, dict) and key in cache:
        return list(cache[key])
    extras: list[Path] = []
    with contextlib.suppress(Exception):
        extras = list(state_env._collect_target_devtool_dirs(repo_path, filename))
    if isinstance(cache, dict):
        cache[key] = list(extras)
    return extras


def _read_state_snapshot(
    repo_path: Path,
    filename: str,
    default: dict[str, Any],
    active_epic: str | None = None,
) -> dict[str, Any]:
    """Select the highest-generation state snapshot across root, worktrees, and common dir."""
    cache = getattr(_SCAN_CTX, "cache", None)
    cache_key = ("state_snapshot", str(repo_path), filename, active_epic)
    if isinstance(cache, dict) and cache_key in cache:
        cached = cache[cache_key]
        if cached is None:
            return dict(default)
        merged_cached = dict(default)
        merged_cached.update(cached)
        return merged_cached

    state_env = _load_state_envelope()
    collected_dirs = _collect_devtool_dirs(repo_path, active_epic)
    if state_env is not None:
        seen = {d.resolve() for d in collected_dirs if d.is_dir()}
        for extra in _get_cached_target_devtool_dirs(state_env, repo_path, filename):
            if extra.is_dir() and extra.resolve() not in seen:
                seen.add(extra.resolve())
                collected_dirs.append(extra)
        if not collected_dirs:
            if isinstance(cache, dict):
                cache[cache_key] = None
            return dict(default)
        snapshot, _ = state_env._read_highest_snapshot(
            collected_dirs, filename, default
        )
        res = dict(snapshot)
        if isinstance(cache, dict):
            cache[cache_key] = dict(res)
        return res

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
    if isinstance(cache, dict):
        cache[cache_key] = dict(best_snapshot) if best_snapshot else None
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
    repo_path: Path, completed_slugs: set[str], abandoned_slugs: set[str] | None = None
) -> str | None:
    """Resolve an active non-completed epic recorded in `pending_decision.json`."""
    snapshot = _read_state_snapshot(repo_path, "pending_decision.json", {})
    if not snapshot:
        return None
    abandoned = abandoned_slugs or set()

    decisions = snapshot.get("decisions")
    if isinstance(decisions, dict) and decisions:
        candidates: list[tuple[str, str]] = []
        for key, entry in decisions.items():
            if not isinstance(entry, dict) or entry.get("active", True) is not True:
                continue
            ep = str(entry.get("epic") or key).strip()
            if not ep or not _is_epic_eligible_for_active(
                ep, completed_slugs, abandoned
            ):
                continue
            stamp = str(entry.get("updated_at") or entry.get("created_at") or "")
            candidates.append((stamp, ep))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return _resolve_canonical_epic_slug(repo_path, candidates[0][1])

    if snapshot.get("active") is True and snapshot.get("epic"):
        ep = str(snapshot["epic"]).strip()
        if ep and _is_epic_eligible_for_active(ep, completed_slugs, abandoned):
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
                if raw_slug and _is_epic_eligible_for_active(
                    raw_slug, completed_slugs, abandoned_slugs
                ):
                    return _resolve_canonical_epic_slug(repo_path, raw_slug)

    # 2. Check active worktrees under .worktrees/ (prioritize worktrees with git changes,
    #    matching/in-progress tasks, or verified .devtool/epic/<slug> directories)
    unrelated_wt_feature_fallback: str | None = None
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
                        if _is_epic_eligible_for_active(
                            slug, completed_slugs, abandoned_slugs
                        ):
                            return _resolve_canonical_epic_slug(repo_path, slug)

            # Check tasks inside worktree features (immediate return only when task epic
            # matches worktree directory name or task is actively in-progress)
            wt_norm = _normalize_slug(_strip_slot_suffix(d.name))
            wt_feat = d / ".devtool" / "features"
            if wt_feat.is_dir():
                for tf in sorted(wt_feat.glob("task_*.md")):
                    with contextlib.suppress(OSError, UnicodeDecodeError):
                        fm = parse_frontmatter(tf.read_text(encoding="utf-8"))
                        ep = fm.get("epic")
                        if ep and _is_epic_eligible_for_active(
                            ep, completed_slugs, abandoned_slugs
                        ):
                            canonical_ep = _resolve_canonical_epic_slug(repo_path, ep)
                            if (
                                _normalize_slug(ep) == wt_norm
                                or normalize_task_status(fm.get("status"))
                                == "in-progress"
                            ):
                                return canonical_ep
                            if unrelated_wt_feature_fallback is None:
                                unrelated_wt_feature_fallback = canonical_ep

            # Check if directory name (stripped of slot suffix) matches an epic
            base_name = _strip_slot_suffix(d.name)
            canonical = _resolve_canonical_epic_slug(repo_path, base_name)
            if (repo_path / ".devtool" / "epic" / canonical).is_dir():
                if _is_epic_eligible_for_active(
                    canonical, completed_slugs, abandoned_slugs
                ):
                    return canonical

    # 3. Check assistant_state.md, skipping placeholder "general" and completed epics
    state_file = repo_path / ".devtool" / "assistant_state.md"
    if state_file.is_file():
        with contextlib.suppress(OSError):
            content = state_file.read_text(encoding="utf-8")
            for m in re.finditer(r"#\s*Active Epic:\s*([a-zA-Z0-9_\-]+)", content):
                slug = m.group(1).strip()
                if slug and _is_epic_eligible_for_active(
                    slug, completed_slugs, abandoned_slugs
                ):
                    return _resolve_canonical_epic_slug(repo_path, slug)

    # 4. Check state folder for non-general state files in deterministic order
    state_dir = repo_path / ".devtool" / "state"
    if state_dir.is_dir():
        for sf in sorted(state_dir.glob("*.md")):
            if _is_epic_eligible_for_active(sf.stem, completed_slugs, abandoned_slugs):
                return _resolve_canonical_epic_slug(repo_path, sf.stem)

    # 5.5 Check explicit active pending_decision.json entries
    pending_epic = _resolve_active_epic_from_pending_decision(
        repo_path, completed_slugs, abandoned_slugs
    )
    if pending_epic:
        return pending_epic

    # 7. Check Gate 1+ ledger entries, active .heartbeat.json files, and active in_progress epics
    stage12_candidates: list[tuple[str, str]] = []
    for row in parse_gate_ledger_entries(repo_path):
        ep = str(row.get("epic", "")).strip()
        if not ep or int(row.get("gate", 0)) < 1:
            continue
        canonical = _resolve_canonical_epic_slug(repo_path, ep)
        ep_dir = repo_path / ".devtool" / "epic" / canonical
        hld_st = extract_epic_hld_status(ep_dir, canonical) if ep_dir.is_dir() else None
        gate_num = _safe_int_val(row.get("gate"), 0)
        if hld_st == "packaged" and gate_num < 3:
            continue
        if _is_epic_eligible_for_active(
            canonical, completed_slugs, abandoned_slugs, hld_st
        ):
            stage12_candidates.append((str(row.get("timestamp", "")), canonical))

    for dt in _collect_devtool_dirs(repo_path):
        st_dir = dt / "state"
        if not st_dir.is_dir():
            continue
        with contextlib.suppress(OSError):
            for hb_file in sorted(st_dir.glob("*.heartbeat.json")):
                with contextlib.suppress(
                    OSError, json.JSONDecodeError, UnicodeDecodeError
                ):
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

    epic_root = repo_path / ".devtool" / "epic"
    if epic_root.is_dir():
        with contextlib.suppress(OSError):
            for ep_dir in sorted(epic_root.iterdir()):
                if not ep_dir.is_dir() or ep_dir.name.startswith("."):
                    continue
                canonical = ep_dir.name
                hld_st = extract_epic_hld_status(ep_dir, canonical)
                if hld_st == "in_progress" and _is_epic_eligible_for_active(
                    canonical, completed_slugs, abandoned_slugs, hld_st
                ):
                    stage12_candidates.append(("", canonical))

    if stage12_candidates:
        stage12_candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return stage12_candidates[0][1]

    # 5. Fallback: check unverified .worktrees directory names (where .devtool/epic/<name> does not exist)
    if wt_dir.is_dir():
        for d in sorted(wt_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                base_name = _strip_slot_suffix(d.name)
                if base_name and _is_epic_eligible_for_active(
                    base_name, completed_slugs, abandoned_slugs
                ):
                    return _resolve_canonical_epic_slug(repo_path, base_name)

    if unrelated_wt_feature_fallback:
        return unrelated_wt_feature_fallback

    # 6. Check .devtool/features/*.md for epic frontmatter
    features_dir = repo_path / ".devtool" / "features"
    if features_dir.is_dir():
        for tf in sorted(features_dir.glob("task_*.md")):
            with contextlib.suppress(OSError, UnicodeDecodeError):
                fm = parse_frontmatter(tf.read_text(encoding="utf-8"))
                ep = fm.get("epic")
                if ep and _is_epic_eligible_for_active(
                    ep, completed_slugs, abandoned_slugs
                ):
                    return _resolve_canonical_epic_slug(repo_path, ep)

    return None


def find_epic_worktree_path(repo_path: Path, active_epic: str | None) -> Path:
    """Locate dedicated worktree directory (.worktrees/<epic_name>) for the active epic, falling back to repo root."""
    if not active_epic:
        return repo_path

    cache = getattr(_SCAN_CTX, "cache", None)
    cache_key = ("epic_wt_path", str(repo_path), active_epic)
    if isinstance(cache, dict) and cache_key in cache:
        return cache[cache_key]

    resolved: Path = repo_path
    candidates = [
        repo_path / ".worktrees" / active_epic,
        repo_path / ".worktrees" / active_epic.replace("-", "_"),
        repo_path / ".worktrees" / active_epic.replace("_", "-"),
    ]
    matched_direct = False
    for c in candidates:
        if c.is_dir():
            resolved = c
            matched_direct = True
            break

    if not matched_direct:
        for wt in scan_worktrees(repo_path):
            wp = Path(wt.path)
            if wp.name in (
                active_epic,
                active_epic.replace("-", "_"),
                active_epic.replace("_", "-"),
            ):
                resolved = wp
                break
            if wt.branch and (
                f"epic/{active_epic}" in wt.branch
                or f"feat/{active_epic}" in wt.branch
                or active_epic in wt.branch
            ):
                resolved = wp
                break

            if not wt.is_dirty:
                continue

            # Check if dirty worktree has active changes in .devtool/epic/<active_epic>
            porcelain_key = ("git_status_porcelain", str(wp))
            if isinstance(cache, dict) and porcelain_key in cache:
                porcelain_out = str(cache[porcelain_key])
            else:
                porcelain_out = ""
                with contextlib.suppress(Exception):
                    res = subprocess.run(
                        ["git", "-C", str(wp), "status", "--porcelain"],
                        capture_output=True,
                        text=True,
                        timeout=2,
                        check=False,
                    )
                    porcelain_out = res.stdout or ""
                if isinstance(cache, dict):
                    cache[porcelain_key] = porcelain_out
            if f".devtool/epic/{active_epic}" in porcelain_out:
                resolved = wp
                break

    if isinstance(cache, dict):
        cache[cache_key] = resolved
    return resolved


def _has_epic_active_tasks(repo_path: Path, slug: str) -> bool:
    """Return True if any task file for this epic has active status (in-progress, review, done)."""
    variants = _collect_slug_variants(slug)
    task_dirs = [repo_path / ".devtool" / "epic" / v for v in variants]
    wt_root = repo_path / ".worktrees"
    if wt_root.is_dir():
        with contextlib.suppress(OSError):
            for wt in wt_root.iterdir():
                if wt.is_dir() and _normalize_slug(wt.name) == _normalize_slug(slug):
                    task_dirs.extend(
                        [
                            wt / ".devtool" / "features",
                            wt / ".devtool" / "features" / "done",
                            *[wt / ".devtool" / "epic" / v for v in variants],
                        ]
                    )
    for td in task_dirs:
        if not td.is_dir():
            continue
        with contextlib.suppress(OSError):
            for tf in td.glob("task_*.md"):
                with contextlib.suppress(OSError, UnicodeDecodeError):
                    fm = parse_frontmatter(tf.read_text(encoding="utf-8"))
                    if fm.get("status") in ("in-progress", "review", "done"):
                        return True
    return False


def _has_epic_stream_events(repo_path: Path, slug: str) -> bool:
    """Return True if any append-only event stream file exists for this epic."""
    variants = _collect_slug_variants(slug)
    variants_set = set(variants)
    norm_target = _normalize_slug(slug)
    devtool_dirs = _collect_devtool_dirs(repo_path, active_epic=slug)
    for dt_dir in devtool_dirs:
        for subdir in ("logs", "archive"):
            td = dt_dir / subdir
            if not td.is_dir():
                continue
            with contextlib.suppress(OSError):
                for entry in td.glob("events_*.jsonl"):
                    if _matches_epic_artifact_filename(
                        entry.name, "events_", ".jsonl", variants_set, norm_target
                    ):
                        return True
    return False


def _is_packaged_epic_promoted(
    repo_path: Path,
    slug: str,
    *,
    has_wt: bool = False,
    has_gate3_or_more: bool = False,
    has_active_telemetry: bool = False,
    has_active_tasks: bool | None = None,
) -> bool:
    """Return True if a packaged epic has started implementation (Stage 3+)."""
    if has_wt or has_gate3_or_more or has_active_telemetry:
        return True
    if has_active_tasks is None:
        has_active_tasks = _has_epic_active_tasks(repo_path, slug)
    return bool(has_active_tasks)


_RECENTLY_COMPLETED_LIMIT = 10
_LEDGER_MILESTONE_RE = re.compile(
    r"^\s*-\s+\*\*\[(\d{4}-\d{2}-\d{2})\]\s+`?([a-zA-Z0-9_\-]+)`?\*\*:\s*(.+?)\s*$"
)
_PLAN_DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")
_PLAN_TASK_HEADING_RE = re.compile(r"^###\s+Task\s+(\d+)\s*:\s*(.+?)\s*$")
_SDD_TASK_COMPLETE_RE = re.compile(r"^Task\s+(\d+)\s*:\s*complete\b", re.IGNORECASE)
_SDD_TASK_FIX_RE = re.compile(r"^Task\s+(\d+)\s*:\s*fix\s+round\b", re.IGNORECASE)


def _parse_project_ledger_milestones(repo_path: Path) -> dict[str, dict[str, Any]]:
    """Parse `.devtool/PROJECT_LEDGER.md` milestone rows into a dict keyed by normalized slug."""
    ledger_file = repo_path / ".devtool" / "PROJECT_LEDGER.md"
    if not ledger_file.is_file():
        return {}

    milestones: dict[str, dict[str, Any]] = {}
    with contextlib.suppress(OSError, UnicodeDecodeError):
        for idx, line in enumerate(
            ledger_file.read_text(encoding="utf-8").splitlines()
        ):
            m = _LEDGER_MILESTONE_RE.match(line)
            if not m:
                continue
            date_str, slug, summary = (
                m.group(1).strip(),
                m.group(2).strip(),
                m.group(3).strip(),
            )
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                continue
            epoch = dt.timestamp() + idx * 0.001
            iso_str = dt.isoformat()
            norm_slug = _normalize_slug(slug)
            existing = milestones.get(norm_slug)
            if existing is None or epoch >= float(existing.get("mtime", 0.0)):
                milestones[norm_slug] = {
                    "slug": slug,
                    "completed_date": date_str,
                    "milestone_summary": summary,
                    "mtime": epoch,
                    "last_updated": iso_str,
                    "last_updated_human": format_relative_time(iso_str),
                }
    return milestones


def _parse_sdd_progress(
    repo_path: Path, plan_stem: str, extra_roots: list[Path]
) -> tuple[bool, dict[int, str]]:
    """Parse `.superpowers/sdd/<plan_stem>/progress.md` across worktrees and root repo."""
    candidates: list[tuple[float, Path]] = []
    seen_paths: set[Path] = set()
    for root in [*extra_roots, repo_path]:
        p = root / ".superpowers" / "sdd" / plan_stem / "progress.md"
        if p.is_file():
            with contextlib.suppress(OSError):
                resolved = p.resolve()
                if resolved not in seen_paths:
                    mtime = p.stat().st_mtime
                    seen_paths.add(resolved)
                    candidates.append((mtime, p))
    if not candidates:
        return False, {}

    best = max(candidates, key=lambda item: item[0])[1]
    statuses: dict[int, str] = {}
    with contextlib.suppress(OSError, UnicodeDecodeError):
        for raw_line in best.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip().lstrip("-*").strip()
            m_done = _SDD_TASK_COMPLETE_RE.match(line)
            if m_done:
                statuses[int(m_done.group(1))] = "done"
                continue
            m_fix = _SDD_TASK_FIX_RE.match(line)
            if m_fix:
                statuses[int(m_fix.group(1))] = "in-progress"
    return True, statuses


def _discover_standalone_plans(repo_path: Path) -> list[dict[str, Any]]:
    """Discover standalone plans under `docs/superpowers/plans/` across root and worktrees.

    Strictly excludes dotfiles and `*.vi.md` mirrors (Rule 11).
    """
    cache = getattr(_SCAN_CTX, "cache", None)
    cache_key = ("standalone_plans", str(repo_path))
    if isinstance(cache, dict) and cache_key in cache:
        return [dict(p) for p in cache[cache_key]]

    worktree_entries = _collect_matching_worktrees_with_branches(repo_path, None)
    worktrees = [wt_path for wt_path, _ in worktree_entries]
    ledger_milestones = _parse_project_ledger_milestones(repo_path)

    root_candidates: dict[str, tuple[Path, bool, float]] = {}
    wt_candidates: dict[str, tuple[Path, bool, bool, float, Path]] = {}

    def _scan_plans_dir(
        root: Path, is_worktree: bool, branch_name: str | None = None
    ) -> None:
        plans_dir = root / "docs" / "superpowers" / "plans"
        if not plans_dir.is_dir():
            return
        with contextlib.suppress(OSError):
            for f in sorted(plans_dir.glob("*.md")):
                if (
                    not f.is_file()
                    or f.name.startswith(".")
                    or f.name.lower().endswith(".vi.md")
                ):
                    continue
                if f.name.lower().endswith(".en.md"):
                    plan_stem = f.name[:-6]
                    is_legacy_en = True
                else:
                    plan_stem = f.stem
                    is_legacy_en = False
                if not plan_stem:
                    continue
                try:
                    f_mtime = f.stat().st_mtime
                except OSError:
                    continue
                if not is_worktree:
                    prev = root_candidates.get(plan_stem)
                    if (
                        prev is None
                        or (prev[1] and not is_legacy_en)
                        or (prev[1] == is_legacy_en and f_mtime > prev[2])
                    ):
                        root_candidates[plan_stem] = (f, is_legacy_en, f_mtime)
                else:
                    m_stem_date = _PLAN_DATE_PREFIX_RE.match(plan_stem)
                    norm_stem_slug = _normalize_slug(
                        m_stem_date.group(2) if m_stem_date else plan_stem
                    )
                    wt_matches_slug = _worktree_matches_slug(
                        root, norm_stem_slug, branch_name
                    )
                    cand_rank = (not is_legacy_en, wt_matches_slug, f_mtime)
                    prev_wt = wt_candidates.get(plan_stem)
                    if prev_wt is None or cand_rank > (
                        not prev_wt[1],
                        prev_wt[2],
                        prev_wt[3],
                    ):
                        wt_candidates[plan_stem] = (
                            f,
                            is_legacy_en,
                            wt_matches_slug,
                            f_mtime,
                            root,
                        )

    _scan_plans_dir(repo_path, False)
    for wt, wt_branch in worktree_entries:
        _scan_plans_dir(wt, True, wt_branch)

    selected_by_norm_slug: dict[str, dict[str, Any]] = {}
    all_stems = sorted(set(root_candidates) | set(wt_candidates))
    for plan_stem in all_stems:
        m_date = _PLAN_DATE_PREFIX_RE.match(plan_stem)
        slug = m_date.group(2) if m_date else plan_stem
        norm_slug = _normalize_slug(slug)

        root_cand = root_candidates.get(plan_stem)
        wt_cand = wt_candidates.get(plan_stem)

        chosen_file: Path
        chosen_mtime: float
        from_worktree: bool

        if root_cand is None and wt_cand is not None:
            chosen_file, _, _, chosen_mtime, _ = wt_cand
            from_worktree = True
        elif wt_cand is None and root_cand is not None:
            chosen_file, _, chosen_mtime = root_cand
            from_worktree = False
        else:
            assert root_cand is not None and wt_cand is not None
            r_file, r_legacy, r_mtime = root_cand
            w_file, w_legacy, w_matches_slug, w_mtime, _ = wt_cand
            if r_legacy and not w_legacy:
                chosen_file, chosen_mtime, from_worktree = w_file, w_mtime, True
            elif not r_legacy and w_legacy:
                chosen_file, chosen_mtime, from_worktree = r_file, r_mtime, False
            else:
                content_differs = False
                if w_mtime > r_mtime and not w_matches_slug:
                    with contextlib.suppress(OSError, UnicodeDecodeError):
                        content_differs = w_file.read_text(
                            encoding="utf-8"
                        ) != r_file.read_text(encoding="utf-8")
                if (w_matches_slug and w_mtime >= r_mtime) or (
                    w_mtime > r_mtime and content_differs
                ):
                    chosen_file, chosen_mtime, from_worktree = w_file, w_mtime, True
                else:
                    chosen_file, chosen_mtime, from_worktree = r_file, r_mtime, False

        content = ""
        with contextlib.suppress(OSError, UnicodeDecodeError):
            content = chosen_file.read_text(encoding="utf-8")

        title = slug
        raw_tasks: list[tuple[int, str]] = []
        found_title = False
        for line in content.splitlines():
            stripped = line.strip()
            if not found_title and stripped.startswith("# "):
                raw_title = stripped.lstrip("#").strip()
                if raw_title.endswith(" Implementation Plan"):
                    raw_title = raw_title[: -len(" Implementation Plan")].strip()
                if raw_title:
                    title = raw_title
                found_title = True
                continue
            m_task = _PLAN_TASK_HEADING_RE.match(stripped)
            if m_task:
                raw_tasks.append((int(m_task.group(1)), m_task.group(2).strip()))

        has_sdd_progress, sdd_statuses = _parse_sdd_progress(
            repo_path, plan_stem, worktrees
        )

        effective_mtime = chosen_mtime
        for root in [*worktrees, repo_path]:
            prog_file = root / ".superpowers" / "sdd" / plan_stem / "progress.md"
            if prog_file.is_file():
                with contextlib.suppress(OSError):
                    effective_mtime = max(effective_mtime, prog_file.stat().st_mtime)

        ledger_entry = ledger_milestones.get(norm_slug)
        if ledger_entry is not None:
            effective_mtime = float(ledger_entry["mtime"])

        last_updated_iso = datetime.fromtimestamp(
            effective_mtime, tz=timezone.utc
        ).isoformat()
        last_updated_human = format_relative_time(last_updated_iso)

        tasks = [
            {
                "num": t_num,
                "id": f"task_{t_num:02d}",
                "title": f"Task {t_num}: {t_title}",
                "status": sdd_statuses.get(t_num, "todo"),
            }
            for t_num, t_title in raw_tasks
        ]

        try:
            rel_plan_path = str(chosen_file.relative_to(repo_path))
        except ValueError:
            rel_plan_path = str(chosen_file)

        plan_record: dict[str, Any] = {
            "slug": slug,
            "plan_stem": plan_stem,
            "title": title,
            "plan_path": rel_plan_path,
            "tasks": tasks,
            "mtime": effective_mtime,
            "last_updated": last_updated_iso,
            "last_updated_human": last_updated_human,
            "has_sdd_progress": has_sdd_progress,
            "from_worktree": from_worktree,
        }

        existing = selected_by_norm_slug.get(norm_slug)
        if existing is None or (effective_mtime, plan_stem) >= (
            float(existing["mtime"]),
            str(existing["plan_stem"]),
        ):
            selected_by_norm_slug[norm_slug] = plan_record

    plans_result = list(selected_by_norm_slug.values())
    if isinstance(cache, dict):
        cache[cache_key] = [dict(p) for p in plans_result]
    return plans_result


def _clone_epics_summary(summary: EpicsSummary) -> EpicsSummary:
    """Fast shallow copy of EpicsSummary and its flat per-epic dicts."""
    return EpicsSummary(
        total=summary.total,
        completed=summary.completed,
        in_progress=summary.in_progress,
        unstarted=summary.unstarted,
        abandoned=summary.abandoned,
        epics=[dict(e) for e in summary.epics],
        doing_count=summary.doing_count,
        pending_count=summary.pending_count,
        cancelled_count=summary.cancelled_count,
    )


def harvest_epics_overview(repo_path: Path) -> EpicsSummary:
    """Harvest high-level project epics summary and status breakdown from the root repository."""
    cache = getattr(_SCAN_CTX, "cache", None)
    cache_key = ("epics_overview", str(repo_path))
    if isinstance(cache, dict) and cache_key in cache:
        return _clone_epics_summary(cache[cache_key])

    epic_dir = repo_path / ".devtool" / "epic"
    completed_slugs = get_completed_epic_slugs(repo_path)
    abandoned_slugs = get_abandoned_epic_slugs(repo_path)
    all_gates = parse_gate_ledger_entries(repo_path)
    ledger_milestones = _parse_project_ledger_milestones(repo_path)

    epics: list[dict[str, Any]] = []
    seen_norm_slugs: set[str] = set()
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
            seen_norm_slugs.add(norm_slug)
            has_gate3_or_more = any(
                _normalize_slug(str(g.get("epic", ""))) == norm_slug
                and int(g.get("gate", 0)) >= 3
                for g in all_gates
            )
            has_gate1_or_more = any(
                _normalize_slug(str(g.get("epic", ""))) == norm_slug
                and int(g.get("gate", 0)) >= 1
                for g in all_gates
            )
            has_active_hb = (
                _read_epic_heartbeat(repo_path, slug) is not None
                or (repo_path / ".devtool" / "state" / f"{slug}.md").is_file()
            )
            has_active_telemetry = has_active_hb or _has_epic_stream_events(
                repo_path, slug
            )

            # Status determination (HLD status is SSOT for Done/Abandon)
            if hld_status == "done" or _is_completed_epic(slug, completed_slugs):
                status = "done"
            elif hld_status in ("abandon", "abandoned") or _is_completed_epic(
                slug, abandoned_slugs
            ):
                status = (
                    hld_status
                    if hld_status in ("abandon", "abandoned")
                    else "abandoned"
                )
            elif hld_status == "packaged":
                if _is_packaged_epic_promoted(
                    repo_path,
                    slug,
                    has_wt=has_wt,
                    has_gate3_or_more=has_gate3_or_more,
                    has_active_telemetry=has_active_telemetry,
                ):
                    status = "in_progress"
                else:
                    status = "packaged"
            elif (
                has_wt
                or hld_status == "in_progress"
                or (
                    _is_epic_eligible_for_active(
                        slug, completed_slugs, abandoned_slugs, hld_status
                    )
                    and (has_gate1_or_more or has_active_telemetry)
                )
            ):
                status = "in_progress"
            else:
                status = "unstarted"

            # Title
            title = slug
            hld = epic_doc_path(d, slug)
            if hld is not None:
                with contextlib.suppress(OSError, UnicodeDecodeError):
                    for line in hld.read_text(encoding="utf-8").splitlines():
                        if line.startswith("# "):
                            raw = line.lstrip("#").strip()
                            if raw.lower().startswith("epic:"):
                                raw = raw[5:].strip()
                            title = raw
                            break

            task_count = len(list(d.glob("task_*.md")))
            for wt_path in _collect_matching_worktrees(repo_path, slug):
                for ed in _find_epic_dirs_for_checkout(wt_path, slug):
                    with contextlib.suppress(OSError):
                        task_count = max(task_count, len(list(ed.glob("task_*.md"))))
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

            ledger_entry = ledger_milestones.get(norm_slug)
            if status == "done" and ledger_entry is not None:
                max_mtime = float(ledger_entry["mtime"])

            last_updated_dt = datetime.fromtimestamp(max_mtime, tz=timezone.utc)
            last_updated_iso = last_updated_dt.isoformat()
            last_updated_human = format_relative_time(last_updated_iso)

            epic_entry: dict[str, Any] = {
                "slug": slug,
                "title": title,
                "status": status,
                "source_kind": "epic",
                "has_worktree": has_wt,
                "task_count": task_count,
                "pic": pic,
                "mtime": max_mtime,
                "last_updated": last_updated_iso,
                "last_updated_human": last_updated_human,
            }
            if ledger_entry is not None:
                epic_entry["completed_date"] = ledger_entry["completed_date"]
                epic_entry["milestone_summary"] = ledger_entry["milestone_summary"]
            epics.append(epic_entry)

    # Standalone plans under docs/superpowers/plans/ (deduplicated against .devtool/epic/)
    for plan in _discover_standalone_plans(repo_path):
        slug = str(plan["slug"])
        norm_slug = _normalize_slug(slug)
        if norm_slug in seen_norm_slugs:
            continue
        seen_norm_slugs.add(norm_slug)

        ledger_entry = ledger_milestones.get(norm_slug)
        has_wt = bool(plan["from_worktree"]) or bool(
            _collect_matching_worktrees(repo_path, slug)
        )
        has_state_md = (repo_path / ".devtool" / "state" / f"{slug}.md").is_file()
        has_sdd_progress = bool(plan["has_sdd_progress"])

        if _is_completed_epic(slug, completed_slugs) or ledger_entry is not None:
            status = "done"
        elif _is_completed_epic(slug, abandoned_slugs):
            status = "abandoned"
        elif has_wt or has_sdd_progress or has_state_md:
            status = "in_progress"
        else:
            status = "unstarted"

        plan_mtime = (
            float(ledger_entry["mtime"])
            if (status == "done" and ledger_entry is not None)
            else float(plan["mtime"])
        )
        plan_iso = datetime.fromtimestamp(plan_mtime, tz=timezone.utc).isoformat()
        plan_human = format_relative_time(plan_iso)

        plan_entry: dict[str, Any] = {
            "slug": slug,
            "title": str(plan["title"]),
            "status": status,
            "source_kind": "plan",
            "plan_path": str(plan["plan_path"]),
            "has_worktree": has_wt,
            "task_count": len(plan["tasks"]),
            "pic": extract_epic_pic(repo_path, slug),
            "mtime": plan_mtime,
            "last_updated": plan_iso,
            "last_updated_human": plan_human,
        }
        if ledger_entry is not None:
            plan_entry["completed_date"] = ledger_entry["completed_date"]
            plan_entry["milestone_summary"] = ledger_entry["milestone_summary"]
        epics.append(plan_entry)

    # Ledger-only milestones not represented by an epic dir or standalone plan
    for norm_slug, lm in ledger_milestones.items():
        if norm_slug in seen_norm_slugs:
            continue
        seen_norm_slugs.add(norm_slug)
        lm_slug = str(lm["slug"])
        epics.append(
            {
                "slug": lm_slug,
                "title": str(lm["milestone_summary"] or lm_slug),
                "status": "done",
                "source_kind": "ledger",
                "has_worktree": False,
                "task_count": 0,
                "pic": extract_epic_pic(repo_path, lm_slug),
                "completed_date": str(lm["completed_date"]),
                "milestone_summary": str(lm["milestone_summary"]),
                "mtime": float(lm["mtime"]),
                "last_updated": str(lm["last_updated"]),
                "last_updated_human": str(lm["last_updated_human"]),
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
    summary = EpicsSummary(
        total=total,
        completed=completed,
        in_progress=in_prog,
        unstarted=unstarted,
        abandoned=abandoned,
        epics=epics,
    )
    if isinstance(cache, dict):
        cache[cache_key] = _clone_epics_summary(summary)
    return summary


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
            t for t in all_tasks if _normalize_slug(str(t.get("epic") or "")) == norm_ep
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


def extract_task_progress(
    repo_path: Path,
    active_epic: str | None,
    *,
    include_completed_tasks: bool = True,
) -> TaskProgress:
    """Harvest comprehensive Kanban tasks across active and backlog epics according to 2-tier governance.

    1. Scan epics in .devtool/epic/ in root repo (backlog, todo, in_progress).
    2. For backlog epics: keep root task information.
    3. For active epic in worktree: fetch latest detailed tasks from worktree.
    """
    epic_dir = repo_path / ".devtool" / "epic"
    completed_slugs = get_completed_epic_slugs(repo_path)
    abandoned_slugs = get_abandoned_epic_slugs(repo_path)

    candidate_epics: list[str] = []
    if active_epic:
        candidate_epics.append(active_epic)

    if epic_dir.is_dir():
        for d in sorted(epic_dir.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            slug = d.name
            if (
                _is_completed_epic(slug, completed_slugs)
                or _is_completed_epic(slug, abandoned_slugs)
            ) and _normalize_slug(slug) != _normalize_slug(active_epic or ""):
                continue
            if slug not in candidate_epics:
                candidate_epics.append(slug)

    features_dir = repo_path / ".devtool" / "features"
    if features_dir.is_dir():
        norm_candidates = {_normalize_slug(c) for c in candidate_epics}
        for tf in sorted(features_dir.glob("task_*.md"), key=natural_sort_key):
            with contextlib.suppress(Exception):
                fm = parse_frontmatter(tf.read_text(encoding="utf-8"))
                ep = str(fm.get("epic") or "").strip()
                if (
                    ep
                    and not _is_completed_epic(ep, completed_slugs)
                    and not _is_completed_epic(ep, abandoned_slugs)
                    and _normalize_slug(ep) not in norm_candidates
                ):
                    candidate_epics.append(ep)
                    norm_candidates.add(_normalize_slug(ep))

    seen_tasks: set[tuple[str, str]] = set()
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
                    seen_key = (_normalize_slug(ep), task_id)
                    if seen_key in seen_tasks:
                        continue
                    with contextlib.suppress(OSError, UnicodeDecodeError):
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

                        seen_tasks.add(seen_key)
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
            with contextlib.suppress(OSError, UnicodeDecodeError):
                content = tf.read_text(encoding="utf-8")
                fm = parse_frontmatter(content)
                task_epic = fm.get("epic") or "backlog"
                seen_key = (_normalize_slug(str(task_epic)), task_id)
                if seen_key in seen_tasks:
                    continue
                is_active_match = bool(
                    active_epic
                    and _normalize_slug(str(task_epic)) == _normalize_slug(active_epic)
                )
                if not is_active_match and (
                    _is_completed_epic(str(task_epic), completed_slugs)
                    or _is_completed_epic(str(task_epic), abandoned_slugs)
                ):
                    continue
                if candidate_epics:
                    norm_candidates = {_normalize_slug(e) for e in candidate_epics}
                    if _normalize_slug(str(task_epic)) not in norm_candidates:
                        continue

                seen_tasks.add(seen_key)
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

    # Standalone plan tasks for active (non-completed, non-abandoned) plans
    epic_dir_norm_slugs: set[str] = set()
    if epic_dir.is_dir():
        with contextlib.suppress(OSError):
            epic_dir_norm_slugs = {
                _normalize_slug(d.name)
                for d in epic_dir.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            }
    discovered_plans = _discover_standalone_plans(repo_path)
    for plan in discovered_plans:
        plan_slug = str(plan["slug"])
        norm_plan_slug = _normalize_slug(plan_slug)
        if (
            norm_plan_slug in epic_dir_norm_slugs
            or _is_completed_epic(plan_slug, completed_slugs)
            or _is_completed_epic(plan_slug, abandoned_slugs)
        ):
            continue
        plan_source = "worktree" if plan["from_worktree"] else "plan"
        for pt in plan["tasks"]:
            task_id = str(pt["id"])
            seen_key = (norm_plan_slug, task_id)
            if seen_key in seen_tasks:
                continue
            seen_tasks.add(seen_key)
            all_tasks.append(
                {
                    "id": task_id,
                    "title": str(pt["title"]),
                    "status": str(pt["status"]),
                    "priority": "medium",
                    "epic": plan_slug,
                    "labels": ["plan"],
                    "time": str(plan["last_updated_human"]),
                    "source": plan_source,
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

    completed_tasks: list[dict[str, Any]] = []
    if include_completed_tasks:
        # Collect completed_tasks for top _RECENTLY_COMPLETED_LIMIT newest completed epics/plans
        overview = harvest_epics_overview(repo_path)
        completed_entries = [
            ep
            for ep in overview.epics
            if str(ep.get("status") or "").strip().lower() == "done"
        ]
        completed_entries.sort(
            key=lambda ep: (-float(ep.get("mtime", 0.0)), str(ep.get("slug") or ""))
        )
        top_completed = completed_entries[:_RECENTLY_COMPLETED_LIMIT]
        plans_by_norm = {_normalize_slug(str(p["slug"])): p for p in discovered_plans}
        for ep in top_completed:
            ep_slug = str(ep.get("slug") or "")
            source_kind = str(ep.get("source_kind") or "epic")
            comp_time = str(
                ep.get("completed_date") or ep.get("last_updated_human") or ""
            )
            if source_kind == "plan":
                plan = plans_by_norm.get(_normalize_slug(ep_slug))
                if plan:
                    for pt in plan["tasks"]:
                        completed_tasks.append(
                            {
                                "id": str(pt["id"]),
                                "title": str(pt["title"]),
                                "status": "done",
                                "priority": "medium",
                                "epic": ep_slug,
                                "labels": ["plan"],
                                "time": comp_time,
                                "source": "plan",
                            }
                        )
            elif source_kind == "epic":
                ep_dir = epic_dir / ep_slug
                if ep_dir.is_dir():
                    for tf in sorted(ep_dir.glob("task_*.md"), key=natural_sort_key):
                        if tf.name.lower().endswith(".vi.md"):
                            continue
                        task_id = tf.stem
                        with contextlib.suppress(OSError, UnicodeDecodeError):
                            content = tf.read_text(encoding="utf-8")
                            fm = parse_frontmatter(content)
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
                            time_val = (
                                format_relative_time(
                                    fm.get("completedAt")
                                    or fm.get("modified")
                                    or fm.get("created")
                                )
                                or comp_time
                            )
                            completed_tasks.append(
                                {
                                    "id": task_id,
                                    "title": title,
                                    "status": "done",
                                    "priority": fm.get("priority", "medium"),
                                    "epic": ep_slug,
                                    "labels": labels,
                                    "time": time_val,
                                    "source": "root",
                                }
                            )

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
        completed_tasks=completed_tasks,
    )


_LEGACY_MEMORY_ROLES = {"assistant": "architect"}


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
                role = _LEGACY_MEMORY_ROLES.get(role.lower(), role)

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
    norm_active = _normalize_slug(active_epic) if active_epic else None
    cache = getattr(_SCAN_CTX, "cache", None)
    all_key = ("gate_ledger_all", str(repo_path))
    if isinstance(cache, dict) and all_key in cache:
        all_rows: list[dict[str, Any]] = cache[all_key]
        if norm_active is None:
            return [dict(r) for r in all_rows]
        return [
            dict(r)
            for r in all_rows
            if _normalize_slug(str(r.get("epic", ""))) == norm_active
        ]

    devtool_dirs = _collect_devtool_dirs(repo_path, active_epic=None)
    if not devtool_dirs:
        if isinstance(cache, dict):
            cache[all_key] = []
        return []

    merged: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, int, str]] = set()
    read_filter = None if isinstance(cache, dict) else norm_active

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
                devtool_dir / "state" / "gate_ledger.jsonl", read_filter
            )
        )
    for devtool_dir in devtool_dirs:
        _append_unique(
            _read_markdown_ledger_file(devtool_dir / "GATE_LEDGER.md", read_filter)
        )

    merged.sort(key=lambda e: (str(e.get("timestamp", "")), int(e.get("gate", 0))))
    if isinstance(cache, dict):
        cache[all_key] = [dict(r) for r in merged]
        if norm_active is not None:
            return [
                dict(r)
                for r in merged
                if _normalize_slug(str(r.get("epic", ""))) == norm_active
            ]
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
        for extra in _get_cached_target_devtool_dirs(
            state_env, repo_path, "quality_active.json"
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


_PAUSED_STAGE_TOKENS = (
    "waiting",
    "paused",
    "halted",
    "blocked",
    "awaiting",
    "circuit_breaker",
    "choice a",
    "dừng",
)


def _derive_active_auto_decision(
    repo_path: Path,
    active_epic: str,
) -> LifecycleDecision | None:
    """Detect active non-paused AUTO execution from quality_active.json or epic heartbeat."""
    active_quality, _ = _read_quality_state(repo_path, active_epic)
    if isinstance(active_quality, dict):
        q_status = str(active_quality.get("status") or "").strip().lower()
        if q_status not in ("passed", "failed", "completed", "error", "idle"):
            return LifecycleDecision(
                stage_name=LifecycleStage.STAGE_3_PHASE_4_REVIEW.value,
                gate_status="Quality Check Running",
                prompt="Đang thực thi kiểm thử tự động (quality_check)",
                is_human_action_required=False,
            )

    hb = _read_epic_heartbeat(repo_path, active_epic)
    if not isinstance(hb, dict):
        return None

    stage_raw = str(hb.get("stage") or "").strip()
    stage_low = stage_raw.lower()
    sub_step_low = str(hb.get("sub_step") or "").strip().lower()
    last_event = str(hb.get("last_event") or "").strip()

    if any(tok in stage_low for tok in _PAUSED_STAGE_TOKENS):
        return None

    rev_state = hb.get("review_state")
    if isinstance(rev_state, dict):
        rev_phase = str(rev_state.get("phase") or "").strip().lower()
        rev_action = str(rev_state.get("action") or "").strip()
        if rev_phase in ("reviewing", "triage", "fixing", "verifying") and not rev_action.startswith(
            "CIRCUIT_BREAKER_HALT"
        ):
            rev_kind = str(rev_state.get("kind") or "").strip().lower()
            label = str(rev_state.get("label") or last_event or "").strip()
            if rev_kind == "principal":
                return LifecycleDecision(
                    stage_name="Stage 2 (Principal Review)",
                    gate_status="Gate 2 PASS (Principal Review)",
                    prompt=label or "Đang chạy /principal-review tự động",
                    is_human_action_required=False,
                )
            return LifecycleDecision(
                stage_name=LifecycleStage.STAGE_3_PHASE_4_REVIEW.value,
                gate_status="Cross-Model Review Running",
                prompt=label or "Đang chạy /cross-model-review tự động",
                is_human_action_required=False,
            )

    slots = hb.get("slots")
    has_active_slot = isinstance(slots, dict) and any(
        isinstance(s, dict)
        and str(s.get("status") or "").strip().lower() in ("working", "review")
        for s in slots.values()
    )
    has_active_tasks = bool(hb.get("active_tasks"))
    is_active_stage = (
        stage_low.startswith("in progress")
        or "principal review" in stage_low
        or "cross-model review" in stage_low
        or "stage 3" in stage_low
        or "wave " in stage_low
        or "implement" in stage_low
        or "tdd" in stage_low
        or sub_step_low in ("working", "review", "resumed", "running", "fixing", "verifying")
    )
    if has_active_slot or has_active_tasks or is_active_stage:
        return LifecycleDecision(
            stage_name=stage_raw or LifecycleStage.STAGE_3_PHASE_2_TDD.value,
            gate_status="AUTO MODE Running",
            prompt=last_event or "AI Agent đang thực thi tự động (AUTO MODE)",
            is_human_action_required=False,
        )
    return None


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
    task_progress = extract_task_progress(
        repo_path, active_epic, include_completed_tasks=False
    )

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
        packaged_dir_task_count = 0
        for checkout in [
            find_epic_worktree_path(repo_path, active_epic),
            *_collect_matching_worktrees(repo_path, active_epic),
            repo_path,
        ]:
            for ed in _find_epic_dirs_for_checkout(checkout, active_epic):
                with contextlib.suppress(OSError):
                    packaged_dir_task_count = max(
                        packaged_dir_task_count, len(list(ed.glob("task_*.md")))
                    )
        active_total = max(len(active_tasks), packaged_dir_task_count)
        active_done = sum(1 for t in active_tasks if t.get("status") == "done")
        if active_total > 0 and active_done >= active_total:
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
        active_auto = _derive_active_auto_decision(repo_path, active_epic)
        if active_auto is not None:
            return active_auto

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
    target_norm = _normalize_slug(active_epic)
    cache = getattr(_SCAN_CTX, "cache", None)
    idx_key = ("checkout_epic_idx", str(checkout_root))
    if isinstance(cache, dict):
        idx = cache.get(idx_key)
        if idx is None:
            idx = {}
            if epic_base.is_dir():
                with contextlib.suppress(OSError):
                    for entry in sorted(epic_base.iterdir()):
                        if entry.is_dir():
                            idx.setdefault(_normalize_slug(entry.name), []).append(entry)
            cache[idx_key] = idx
        candidates = idx.get(target_norm)
        if not candidates:
            return []
        exact = epic_base / active_epic
        if exact in candidates and candidates[0] != exact:
            return [exact, *[c for c in candidates if c != exact]]
        return list(candidates)

    if not epic_base.is_dir():
        return []
    matches: list[Path] = []
    exact = epic_base / active_epic
    if exact.is_dir():
        matches.append(exact)
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
            for stem in (epic_dir.name, active_epic):
                hld_doc = epic_doc_path(epic_dir, stem)
                if hld_doc is not None:
                    _add_candidate(hld_doc)
            for spec_doc in design_spec_paths(epic_dir):
                _add_candidate(spec_doc)
            with contextlib.suppress(OSError):
                for doc in sorted(epic_dir.glob("*.md")):
                    if (
                        "design" in doc.name.lower()
                        and not doc.name.startswith("task_")
                        and not doc.name.endswith(".vi.md")
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
    cache = getattr(_SCAN_CTX, "cache", None)
    cache_key = ("head_sha", str(checkout_path))
    if isinstance(cache, dict) and cache_key in cache:
        return str(cache[cache_key])
    sha = ""
    with contextlib.suppress(Exception):
        res = subprocess.run(
            ["git", "-C", str(checkout_path), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            sha = res.stdout.strip()
    if isinstance(cache, dict):
        cache[cache_key] = sha
    return sha


def _safe_int_val(val: Any, default: int = 0) -> int:
    """Safely convert val to int, returning default on failure."""
    if isinstance(val, bool):
        return default
    if isinstance(val, int):
        return val
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return default


def _shas_match(sha_a: str, sha_b: str) -> bool:
    """Return True if two non-empty git SHA prefixes match."""
    a = str(sha_a or "").strip().lower()
    b = str(sha_b or "").strip().lower()
    if not a or not b:
        return False
    return a.startswith(b) or b.startswith(a)


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
                r_num = _safe_int_val(parts[idx], 1)
                body = parts[idx + 1] if idx + 1 < len(parts) else ""
                meta: dict[str, str] = {}
                for m in re.finditer(
                    r"^-\s+\*\*([^*]+)\*\*:\s*(.+)$", body, re.MULTILINE
                ):
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
                    if (
                        not stripped.startswith("|")
                        or stripped.startswith("|---")
                        or "Severity" in stripped
                    ):
                        continue
                    cells = [c.strip() for c in stripped.strip("|").split("|")]
                    if len(cells) >= 2:
                        sev = cells[1]
                        dec = cells[4].lower() if len(cells) >= 5 else ""
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
                        "date": meta.get("Date", ""),
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
        summary["round"] = _safe_int_val(last["round"], 1)
        summary["cli"] = str(last["cli"])
        summary["model"] = str(last["model"])
        summary["verdict"] = str(last["verdict"])
        summary["latest_sha"] = str(last["sha"])
        r_sha = str(last["sha"])
        has_fix_commit = bool(
            last["has_fixed"]
            or (r_sha and head_sha and not _shas_match(head_sha, r_sha))
        )
        summary["has_fix_commit"] = has_fix_commit
        verdict_upper = str(last["verdict"] or "").strip().upper()
        verdict_requires_changes = any(
            k in verdict_upper for k in ("CHANGES REQUIRED", "BLOCKED", "FAIL")
        )
        if (
            verdict_upper == "PASS"
            or (
                not verdict_requires_changes
                and last["crit"] == 0
                and last["imp"] == 0
                and last["undecided_blocking"] == 0
            )
            or (
                _safe_int_val(last["round"], 1) >= 3
                and last["crit"] == 0
                and last["undecided_blocking"] == 0
                and (last["imp"] + last["minor"] > 0 or not verdict_requires_changes)
            )
        ):
            summary["converged"] = True
            summary["phase"] = "converged"
        elif has_fix_commit:
            hb_sub = str((heartbeat or {}).get("sub_step") or "")
            hb_phase = (
                str(rs.get("phase") or "")
                if hb_matches_kind and isinstance(rs, dict)
                else ""
            )
            hb_rev_sha = (
                str(rs.get("sha") or "")
                if hb_matches_kind and isinstance(rs, dict)
                else ""
            )
            hb_head_sha = (
                str(rs.get("head_sha") or "")
                if hb_matches_kind and isinstance(rs, dict)
                else ""
            )
            hb_updated_at = str((heartbeat or {}).get("updated_at") or "")
            round_date = str(last.get("date") or "")
            hb_is_fresh = (
                not round_date or not hb_updated_at or hb_updated_at >= round_date
            )
            qa_sha = str((quality_active or {}).get("head_sha") or "")
            qa_status_cur = str((quality_active or {}).get("status") or "")
            qa_is_post_fix = bool(
                quality_active
                and (
                    (
                        qa_status_cur == "running"
                        and (not qa_sha or not r_sha or not _shas_match(qa_sha, r_sha))
                    )
                    or (
                        head_sha
                        and qa_sha
                        and _shas_match(qa_sha, head_sha)
                        and (not r_sha or not _shas_match(qa_sha, r_sha))
                    )
                )
            )
            hb_sub_is_post_fix = bool(
                hb_phase != "reviewing"
                and hb_is_fresh
                and (
                    not hb_head_sha or not r_sha or not _shas_match(hb_head_sha, r_sha)
                )
                and (
                    hb_sub.startswith("task_")
                    or hb_sub in ("quality_check", "audit_epic", "bdd_tests")
                )
            )
            hb_explicit_verifying = bool(
                hb_phase == "verifying"
                and (not round_date or not hb_updated_at or hb_is_fresh)
                and (
                    not hb_head_sha or not r_sha or not _shas_match(hb_head_sha, r_sha)
                )
                and (
                    not hb_rev_sha
                    or bool(hb_head_sha)
                    or not r_sha
                    or not _shas_match(hb_rev_sha, r_sha)
                )
            )
            if hb_explicit_verifying or hb_sub_is_post_fix or qa_is_post_fix:
                summary["phase"] = "verifying"
            else:
                summary["phase"] = "fixing"
        else:
            summary["phase"] = "triage"

    if hb_matches_kind and isinstance(rs, dict):
        summary["active"] = True
        hb_round = _safe_int_val(
            rs.get("round"), _safe_int_val(summary["round"], 1) or 1
        )
        summary["max_rounds"] = _safe_int_val(rs.get("max_rounds"), 3) or 3
        if rs.get("cli"):
            summary["cli"] = str(rs["cli"])
        if rs.get("model"):
            summary["model"] = str(rs["model"])
        if rs.get("action"):
            summary["action"] = str(rs["action"])
        if rs.get("verdict"):
            summary["verdict"] = str(rs["verdict"])
        hb_phase = str(rs.get("phase") or "")
        if hb_round > _safe_int_val(summary["round"], 0) or not rounds_data:
            summary["round"] = hb_round
            if hb_phase:
                summary["phase"] = hb_phase
                summary["converged"] = hb_phase == "converged"
        elif hb_phase in ("fixing", "verifying", "converged"):
            if not (
                hb_phase == "fixing" and summary["phase"] in ("verifying", "converged")
            ):
                summary["phase"] = hb_phase
            if hb_phase == "converged":
                summary["converged"] = True
        elif (
            hb_phase == "triage"
            and not summary["has_fix_commit"]
            and not summary["converged"]
        ):
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
                st = (
                    "failed"
                    if summary.get("action") == "CIRCUIT_BREAKER_HALT"
                    else "running"
                )
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


_STAGE_INDEX_PREFIX_RE = re.compile(r"^\d+\.\s*")


def _strip_stage_index_prefix(label: str) -> str:
    """Strip leading stage index prefix (e.g. '3. Tasks' -> 'Tasks') for summary strings."""
    return _STAGE_INDEX_PREFIX_RE.sub("", str(label or "").strip())


def build_epic_pipeline_telemetry(
    repo_path: Path,
    epic_slug: str,
    *,
    done_tasks: int = 0,
    total_tasks: int = 0,
    task_progress: TaskProgress | None = None,
    decision: LifecycleDecision | None = None,
    heartbeat: dict[str, Any] | None = None,
    quality_active: dict[str, Any] | None = None,
    quality_runs: list[dict[str, Any]] | None = None,
    pending_decision: dict[str, Any] | None = None,
    active_stage: str | None = None,
    is_completed: bool = False,
) -> dict[str, Any]:
    """Synthesize deterministic 6-stage /dev-lifecycle progress, sub-steps, and rolling events."""
    if task_progress is not None:
        if done_tasks == 0 and task_progress.done_tasks > 0:
            done_tasks = int(task_progress.done_tasks)
        if total_tasks == 0 and task_progress.total_tasks > 0:
            total_tasks = int(task_progress.total_tasks)
    if decision is not None and active_stage is None:
        active_stage = decision.stage_name
    if heartbeat is None:
        heartbeat = _read_epic_heartbeat(repo_path, epic_slug)
    if quality_active is None:
        quality_active, _ = _read_quality_state(repo_path, epic_slug)

    wt_path = find_epic_worktree_path(repo_path, epic_slug)
    head_sha = _get_short_head_sha(wt_path)
    epic_dirs: list[Path] = []
    for checkout in [
        wt_path,
        *_collect_matching_worktrees(repo_path, epic_slug),
        repo_path,
    ]:
        for ed_candidate in _find_epic_dirs_for_checkout(checkout, epic_slug):
            if ed_candidate not in epic_dirs:
                epic_dirs.append(ed_candidate)
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
            if any(epic_doc_path(ed, stem) for stem in (epic_slug, ed.name, "hld")):
                has_hld = True
            for f in ed.iterdir():
                if not f.is_file() or f.name.endswith(".vi.md"):
                    continue
                low = f.name.lower()
                if "design" in low or "spec" in low:
                    has_spec = True
                if low.startswith("bdd_scenarios"):
                    has_bdd = True
                if f.name == "handoff.md":
                    has_handoff = True
                if f.name == "principal_review.md" and principal_file is None:
                    principal_file = f
                if f.name == "review_results.md" and code_review_file is None:
                    code_review_file = f
            dir_task_count = max(dir_task_count, len(list(ed.glob("task_*.md"))))

    total_tasks = max(total_tasks, dir_task_count)

    has_wt = (repo_path / ".worktrees" / epic_slug).is_dir() or bool(
        _collect_matching_worktrees(repo_path, epic_slug)
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
    hb_sub_detail_upper = str((heartbeat or {}).get("sub_step_detail") or "").upper()
    hb_last_event_upper = str((heartbeat or {}).get("last_event") or "").upper()
    has_completed_code_round = _safe_int_val(code_rev.get("round"), 0) >= 1
    hb_audit_passed = (
        hb_sub_step == "audit_epic"
        and "FAIL" not in hb_sub_detail_upper
        and "FAIL" not in hb_last_event_upper
        and ("PASS" in hb_sub_detail_upper or "PASS" in hb_last_event_upper)
    )
    hb_bdd_passed = (
        hb_sub_step == "bdd_tests"
        and "FAIL" not in hb_sub_detail_upper
        and "FAIL" not in hb_last_event_upper
        and ("PASS" in hb_sub_detail_upper or "PASS" in hb_last_event_upper)
    )

    audit_done = (
        4 in approved_gates
        or 5 in approved_gates
        or is_completed
        or has_completed_code_round
        or hb_audit_passed
        or any(
            "audit_epic" in str(ev.get("message", ""))
            and "PASS" in str(ev.get("message", ""))
            for ev in events
        )
    )
    bdd_done = (
        4 in approved_gates
        or 5 in approved_gates
        or is_completed
        or has_completed_code_round
        or hb_bdd_passed
        or any(
            "check_bdd_traceability tests" in str(ev.get("message", ""))
            and "PASS" in str(ev.get("message", ""))
            for ev in events
        )
    )
    qa_status = str((quality_active or {}).get("status") or "")
    qa_sha = str((quality_active or {}).get("head_sha") or "")
    qa_failed_or_running = qa_status in ("running", "failed", "aborted")
    qa_passed = bool(
        is_completed
        or 5 in approved_gates
        or (not qa_failed_or_running and (qa_status == "passed" or 4 in approved_gates))
    )
    gate4_full_pass = bool(
        is_completed
        or 5 in approved_gates
        or (
            not qa_failed_or_running
            and (4 in approved_gates or (audit_done and bdd_done and qa_passed))
        )
    )

    gate4_pass_on_current_sha = False
    if is_completed or 5 in approved_gates:
        gate4_pass_on_current_sha = True
    elif gate4_full_pass and not qa_failed_or_running and head_sha:
        gate4_sha_bound = bool(
            latest_gate4_sha and _shas_match(head_sha, latest_gate4_sha)
        )
        qa_sha_bound = bool(
            qa_status == "passed" and qa_sha and _shas_match(head_sha, qa_sha)
        )
        gate4_pass_on_current_sha = gate4_sha_bound or qa_sha_bound

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
        and (
            code_rev["converged"]
            or _has_review_converged_hint(repo_path, epic_slug, pending_decision)
        )
        and gate4_pass_on_current_sha
    ):
        lifecycle_progress_pct = 98.0
        current_stage_index = 6
    elif all_tasks_done and (
        code_rev["active"] or code_rev["round"] >= 1 or gate4_full_pass
    ):
        if not code_rev["active"] and code_rev["round"] == 0:
            lifecycle_progress_pct = 88.0
            current_stage_index = 4
        elif code_rev["converged"]:
            lifecycle_progress_pct = 96.0
            current_stage_index = 4 if qa_status == "running" else 5
        else:
            r_num = max(1, _safe_int_val(code_rev["round"], 1))
            phase = str(code_rev["phase"])
            if r_num == 1:
                band = {
                    "reviewing": 89.0,
                    "triage": 90.0,
                    "fixing": 91.0,
                    "verifying": 92.0,
                }
                lifecycle_progress_pct = band.get(phase, 90.0)
            elif r_num == 2:
                band = {
                    "reviewing": 93.0,
                    "triage": 93.8,
                    "fixing": 94.5,
                    "verifying": 95.2,
                }
                lifecycle_progress_pct = band.get(phase, 93.8)
            else:
                band = {
                    "reviewing": 95.5,
                    "triage": 95.7,
                    "fixing": 95.9,
                    "verifying": 96.0,
                }
                lifecycle_progress_pct = min(96.0, band.get(phase, 95.7))
            current_stage_index = 5
    elif all_tasks_done:
        if qa_status == "passed":
            lifecycle_progress_pct = 87.0
            current_stage_index = 4
        elif qa_status in ("running", "failed", "aborted"):
            s_idx = _safe_int_val((quality_active or {}).get("step_index"), 1) or 1
            s_tot = max(
                1, _safe_int_val((quality_active or {}).get("step_total"), 1) or 1
            )
            lifecycle_progress_pct = round(81.0 + min(1.0, s_idx / s_tot) * 5.0, 1)
            current_stage_index = 4
        else:
            lifecycle_progress_pct = 80.0
            current_stage_index = (
                4 if hb_sub_step in ("audit_epic", "bdd_tests", "quality_check") else 3
            )
    elif 3 in approved_gates or has_wt or done_tasks > 0:
        ratio = (done_tasks / total_tasks) if total_tasks > 0 else 0.0
        lifecycle_progress_pct = min(79.0, round(25.0 + ratio * 55.0, 1))
        current_stage_index = 3
    elif has_handoff:
        lifecycle_progress_pct = 25.0
        current_stage_index = 2
    elif principal_rev["active"] or principal_rev["round"] >= 1:
        r_num = max(1, _safe_int_val(principal_rev["round"], 1))
        lifecycle_progress_pct = float(min(23, 20 + min(3, r_num)))
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
        {
            "id": "spec_doc",
            "label": "Design Spec",
            "status": "done" if (has_spec or s1_done) else "running",
            "detail": "",
        },
        {
            "id": "gate_1",
            "label": "Gate 1 Sign-Off",
            "status": "done" if s1_done else "pending",
            "detail": "",
        },
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
        {
            "id": "hld_bdd",
            "label": "HLD & BDD",
            "status": "done"
            if (has_hld and has_bdd) or s2_done
            else ("running" if s1_done else "pending"),
            "detail": "",
        },
        {
            "id": "gate_2",
            "label": "Gate 2 & Tasks",
            "status": "done"
            if (2 in approved_gates or s2_done)
            else ("running" if has_hld else "pending"),
            "detail": f"{total_tasks} tasks" if total_tasks else "",
        },
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
        {
            "id": "package",
            "label": "Package handoff.md",
            "status": "done" if (has_handoff or s2_done) else "pending",
            "detail": "",
        }
    )

    s3_done = all_tasks_done or is_completed or lifecycle_progress_pct >= 80.0
    s3_status = (
        "done"
        if s3_done
        else (
            "running"
            if (3 in approved_gates or has_wt or done_tasks > 0)
            else "pending"
        )
    )
    s3_sub: list[dict[str, str]] = []
    active_wave = (heartbeat or {}).get("active_wave")
    if active_wave is not None and str(active_wave) != "":
        s3_sub.append(
            {
                "id": "wave",
                "label": f"Wave {active_wave}",
                "status": "done" if s3_done else "running",
                "detail": f"{done_tasks}/{total_tasks} ({int(task_completion_pct)}%)",
            }
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
                        "status": "done"
                        if s3_done
                        else (
                            "running" if sl_st in ("working", "review") else "pending"
                        ),
                        "detail": sl_st,
                    }
                )
    s3_sub.append(
        {
            "id": "tasks_tally",
            "label": f"Tasks {done_tasks}/{total_tasks}",
            "status": "done"
            if s3_done
            else ("running" if done_tasks > 0 else "pending"),
            "detail": f"{int(task_completion_pct)}%",
        }
    )

    s4_done = gate4_full_pass and qa_status != "running"
    s4_status = (
        "failed"
        if qa_status in ("failed", "aborted")
        else (
            "running"
            if (qa_status == "running" or current_stage_index == 4)
            else ("done" if s4_done else "pending")
        )
    )
    s4_sub: list[dict[str, str]] = [
        {
            "id": "audit_epic",
            "label": "Epic Audit",
            "status": "done"
            if audit_done
            else ("running" if s3_done and current_stage_index == 4 else "pending"),
            "detail": "",
        },
        {
            "id": "bdd_traceability",
            "label": "BDD Traceability",
            "status": "done" if bdd_done else "pending",
            "detail": "",
        },
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
                    "label": str(
                        st_item.get("label")
                        or st_item.get("capability")
                        or "Quality Step"
                    ),
                    "status": mapped_st,
                    "detail": el_detail,
                }
            )
    elif quality_active:
        cap_lbl = str(
            quality_active.get("capability_label")
            or quality_active.get("capability")
            or "Quality Check"
        )
        s_idx = _safe_int_val(quality_active.get("step_index"), 0)
        s_tot = _safe_int_val(quality_active.get("step_total"), 0)
        s4_sub.append(
            {
                "id": "qa_active",
                "label": cap_lbl,
                "status": "done" if qa_status == "passed" else (qa_status or "pending"),
                "detail": f"{s_idx}/{s_tot}" if s_tot else "",
            }
        )

    s5_done = bool(
        is_completed
        or 5 in approved_gates
        or (code_rev["converged"] and gate4_pass_on_current_sha)
    )
    s5_status = (
        "done"
        if s5_done
        else (
            "failed"
            if code_rev.get("action") == "CIRCUIT_BREAKER_HALT"
            else (
                "running"
                if (code_rev["active"] or current_stage_index == 5)
                else "pending"
            )
        )
    )
    s5_sub = list(code_rev["sub_steps"])

    s6_done = bool(is_completed or 5 in approved_gates)
    s6_status = (
        "done"
        if s6_done
        else ("action_required" if lifecycle_progress_pct >= 98.0 else "pending")
    )
    s6_sub = [
        {
            "id": "gate_5",
            "label": "Gate 5 Sign-Off & Merge",
            "status": "done"
            if s6_done
            else ("running" if lifecycle_progress_pct >= 98.0 else "pending"),
            "detail": "",
        },
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
            "done_tasks": done_tasks,
            "total_tasks": total_tasks,
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
                    str(
                        (quality_active or {}).get("capability_label")
                        or (quality_active or {}).get("capability")
                        or "Running QA"
                    )
                    if qa_status == "running"
                    else (
                        "QA Passed (87%)" if qa_status == "passed" else "Pending Gate 4"
                    )
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
            "summary": "Merged & Archived"
            if s6_done
            else (
                "Waiting /finish (Gate 5)"
                if lifecycle_progress_pct >= 98.0
                else "Pending Gate 5"
            ),
            "sub_steps": s6_sub,
        },
    ]

    cur_stage_obj = stages[max(0, min(5, current_stage_index - 1))]
    active_sub_summary = f"{_strip_stage_index_prefix(str(cur_stage_obj['label']))} · {cur_stage_obj['summary']}"

    return {
        "epic_slug": epic_slug,
        "done_tasks": done_tasks,
        "total_tasks": total_tasks,
        "task_completion_pct": task_completion_pct,
        "lifecycle_progress_pct": lifecycle_progress_pct,
        "current_stage_index": current_stage_index,
        "active_sub_step_summary": active_sub_summary,
        "stages": stages,
        "events": events,
    }


MAX_EVIDENCE_TAIL_LINES = 8
_ARCHIVE_SUFFIX_RE = re.compile(
    r"^(.+?)_(\d{8}_\d{4}(?:_\d+)?|\d{4}-\d{2}-\d{2}"
    r"(?:[T_]\d{2}[:_-]?\d{2}(?:[:_-]?\d{2})?)?)$"
)
_BRACKET_TS_RE = re.compile(r"^\s*(?:[-*]\s+)?\[([^\]]+)\]\s*(.+?)\s*$")
_GATE_STAGE_MAP: dict[int, str] = {
    1: "spec",
    2: "hld_principal",
    3: "tasks",
    4: "gate4_quality",
    5: "finish",
}


def _collect_slug_variants(epic_slug: str) -> list[str]:
    """Return ordered unique slug variants across hyphen and underscore forms."""
    raw = epic_slug.strip()
    if not raw:
        return []
    candidates = [raw, raw.replace("_", "-"), raw.replace("-", "_")]
    if not re.fullmatch(r"[a-zA-Z0-9_\-]+", raw):
        state_env = _load_state_envelope()
        if state_env is not None:
            with contextlib.suppress(Exception):
                sanitized = str(state_env._sanitize_epic_slug(raw)).strip()
                if sanitized:
                    candidates.append(sanitized)
    return list(dict.fromkeys(c for c in candidates if c))


def _parse_utc_datetime(raw_ts: Any) -> datetime | None:
    """Parse an ISO-8601 or bracketed log timestamp into a UTC-aware datetime."""
    text = str(raw_ts or "").strip()
    if not text:
        return None
    normalized = f"{text[:-1]}+00:00" if text.endswith("Z") else text
    with contextlib.suppress(ValueError):
        dt = datetime.fromisoformat(normalized)
        return (
            dt.astimezone(timezone.utc)
            if dt.tzinfo is not None
            else dt.replace(tzinfo=timezone.utc)
        )
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        with contextlib.suppress(ValueError):
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
    return None


def _normalize_utc_iso(raw_ts: Any) -> str:
    """Normalize parseable timestamps to UTC ISO-8601 `Z` form for timeline ordering."""
    dt = _parse_utc_datetime(raw_ts)
    if dt is None:
        return str(raw_ts or "").strip()
    iso = dt.isoformat()
    return f"{iso[:-6]}Z" if iso.endswith("+00:00") else iso


def _timestamp_sort_key(raw_ts: Any) -> tuple[int, float, str]:
    """Build deterministic chronological sort key handling mixed fractional seconds."""
    dt = _parse_utc_datetime(raw_ts)
    if dt is None:
        return (1, 0.0, str(raw_ts or ""))
    return (0, dt.timestamp(), _normalize_utc_iso(dt.isoformat()))


def _matches_epic_artifact_filename(
    filename: str,
    prefix: str,
    ext: str,
    variants: set[str],
    norm_target: str,
) -> bool:
    """Match active or timestamp-archived artifact names without prefix collisions."""
    if not (filename.startswith(prefix) and filename.endswith(ext)):
        return False
    body = filename[len(prefix) : len(filename) - len(ext)]
    if not body:
        return False
    if body in variants or _normalize_slug(body) == norm_target:
        return True
    m_arch = _ARCHIVE_SUFFIX_RE.match(body)
    if not m_arch:
        return False
    candidate = m_arch.group(1)
    return candidate in variants or _normalize_slug(candidate) == norm_target


def _read_json_dict(path: Path) -> dict[str, Any] | None:
    """Read a JSON object from disk, returning None on IO or parse failure."""
    if not path.is_file():
        return None
    with contextlib.suppress(OSError, json.JSONDecodeError, UnicodeDecodeError):
        parsed = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(parsed, dict):
            return parsed
    return None


def _extract_event_epic(record: dict[str, Any]) -> str:
    return str(record.get("epic") or record.get("epic_slug") or "").strip()


def _review_state_key(rev: Any) -> str:
    """Deterministic string key representing review_state identity for deduplication."""
    if not rev:
        return ""
    if isinstance(rev, dict):
        return json.dumps(rev, sort_keys=True, separators=(",", ":"))
    return str(rev)


def _normalize_step_event(record: dict[str, Any], source: str) -> dict[str, Any] | None:
    """Normalize a JSONL or heartbeat event dict into a timeline step item."""
    message = str(
        record.get("message")
        or record.get("last_event")
        or record.get("sub_step_detail")
        or record.get("sub_step")
        or ""
    ).strip()
    if not message:
        return None
    normalized: dict[str, Any] = {
        "ts": _normalize_utc_iso(record.get("ts") or record.get("timestamp")),
        "category": "step",
        "stage": str(record.get("stage") or "").strip(),
        "sub_step": str(record.get("sub_step") or "").strip(),
        "detail": str(record.get("sub_step_detail") or "").strip(),
        "message": message,
        "source": source,
    }
    if record.get("review_state") is not None:
        normalized["review_state"] = record.get("review_state")
    return normalized


def _read_stream_events(
    stream_path: Path, norm_target: str, source: str
) -> list[dict[str, Any]]:
    """Parse append-only JSONL stream events safely, skipping corrupt lines."""
    items: list[dict[str, Any]] = []
    if not stream_path.is_file():
        return items
    with contextlib.suppress(OSError, UnicodeDecodeError):
        for raw_line in stream_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            with contextlib.suppress(json.JSONDecodeError):
                parsed = json.loads(line)
                if not isinstance(parsed, dict):
                    continue
                ev_epic = _extract_event_epic(parsed)
                if ev_epic and _normalize_slug(ev_epic) != norm_target:
                    continue
                normalized = _normalize_step_event(parsed, source)
                if normalized is not None:
                    items.append(normalized)
    return items


def _collect_matching_epic_files(
    devtool_dirs: list[Path],
    subdir: str,
    prefix: str,
    ext: str,
    variants: set[str],
    norm_target: str,
) -> list[Path]:
    """Collect unique files inside `dt/<subdir>` matching epic slug variants."""
    found: list[Path] = []
    seen_paths: set[Path] = set()
    for dt_dir in devtool_dirs:
        target_dir = dt_dir / subdir
        if not target_dir.is_dir():
            continue
        with contextlib.suppress(OSError):
            for entry in sorted(target_dir.iterdir()):
                if not entry.is_file():
                    continue
                if not _matches_epic_artifact_filename(
                    entry.name, prefix, ext, variants, norm_target
                ):
                    continue
                resolved = entry.resolve()
                if resolved not in seen_paths:
                    seen_paths.add(resolved)
                    found.append(entry)
    return found


def _merge_epic_heartbeats(repo_path: Path, epic_slug: str) -> dict[str, Any]:
    """Stitch active and archived heartbeats plus append-only event streams."""
    variants = _collect_slug_variants(epic_slug)
    variants_set = set(variants)
    norm_target = _normalize_slug(epic_slug)
    devtool_dirs = _collect_devtool_dirs(repo_path, active_epic=epic_slug)

    stream_files = [
        *_collect_matching_epic_files(
            devtool_dirs, "archive", "events_", ".jsonl", variants_set, norm_target
        ),
        *_collect_matching_epic_files(
            devtool_dirs, "logs", "events_", ".jsonl", variants_set, norm_target
        ),
    ]
    hb_files = [
        *_collect_matching_epic_files(
            devtool_dirs, "archive", "heartbeat_", ".json", variants_set, norm_target
        ),
        *_collect_matching_epic_files(
            devtool_dirs, "state", "", ".heartbeat.json", variants_set, norm_target
        ),
    ]

    step_events: list[dict[str, Any]] = []
    seen_exact: set[tuple[str, str, str, str, str]] = set()
    stream_msg_keys: set[tuple[str, str, str, str]] = set()
    stream_base_msg_keys: set[tuple[str, str, str]] = set()
    stream_base_exact_keys: set[tuple[str, str, str, str]] = set()
    has_stream = False

    for s_path in stream_files:
        src = "archive_stream" if s_path.parent.name == "archive" else "stream"
        for ev in _read_stream_events(s_path, norm_target, src):
            has_stream = True
            rev_key = _review_state_key(ev.get("review_state"))
            exact_key = (ev["ts"], ev["stage"], ev["sub_step"], ev["message"], rev_key)
            if exact_key in seen_exact:
                continue
            seen_exact.add(exact_key)
            stream_msg_keys.add((ev["stage"], ev["sub_step"], ev["message"], rev_key))
            stream_base_msg_keys.add((ev["stage"], ev["sub_step"], ev["message"]))
            stream_base_exact_keys.add(
                (ev["ts"], ev["stage"], ev["sub_step"], ev["message"])
            )
            step_events.append(ev)

    best_hb: dict[str, Any] | None = None
    best_rank: tuple[int, float, int] = (-1, -1.0, -1)
    snapshots_found = 0

    for hb_path in hb_files:
        snap = _read_json_dict(hb_path)
        if not snap:
            continue
        snap_epic = _extract_event_epic(snap)
        if snap_epic and _normalize_slug(snap_epic) != norm_target:
            continue
        snapshots_found += 1
        is_live = 1 if hb_path.parent.name == "state" else 0
        gen = _safe_int_val(snap.get("generation"), 0)
        upd = _timestamp_sort_key(snap.get("updated_at"))[1]
        rank = (gen, upd, is_live)
        if rank > best_rank:
            best_rank = rank
            best_hb = dict(snap)

        src = "archive_heartbeat" if not is_live else "heartbeat"
        raw_events = snap.get("events")
        if not isinstance(raw_events, list):
            continue
        for item in raw_events:
            if not isinstance(item, dict):
                continue
            hb_ev = _normalize_step_event(item, src)
            if hb_ev is None:
                continue
            rev_key = _review_state_key(hb_ev.get("review_state"))
            exact_key = (
                hb_ev["ts"],
                hb_ev["stage"],
                hb_ev["sub_step"],
                hb_ev["message"],
                rev_key,
            )
            msg_key = (
                hb_ev["stage"],
                hb_ev["sub_step"],
                hb_ev["message"],
                rev_key,
            )
            base_exact = (
                hb_ev["ts"],
                hb_ev["stage"],
                hb_ev["sub_step"],
                hb_ev["message"],
            )
            base_msg = (
                hb_ev["stage"],
                hb_ev["sub_step"],
                hb_ev["message"],
            )
            # If heartbeat event omits review_state and stream already contains this event, drop it as duplicate
            if (
                not rev_key
                and has_stream
                and (
                    base_exact in stream_base_exact_keys
                    or base_msg in stream_base_msg_keys
                )
            ):
                continue

            if exact_key in seen_exact or msg_key in stream_msg_keys:
                continue
            seen_exact.add(exact_key)
            step_events.append(hb_ev)

    step_events.sort(key=lambda e: _timestamp_sort_key(e.get("ts")))
    if best_hb is not None:
        best_hb["events"] = [
            {
                "ts": ev["ts"],
                "stage": ev["stage"],
                "sub_step": ev["sub_step"],
                "message": ev["message"],
                **(
                    {"review_state": ev["review_state"]}
                    if ev.get("review_state") is not None
                    else {}
                ),
            }
            for ev in step_events
        ]

    return {
        "heartbeat": best_hb,
        "step_events": step_events,
        "has_stream": has_stream,
        "has_heartbeat": snapshots_found > 0 or bool(step_events),
    }


def _parse_activity_log_events(
    log_path: Path, variants: set[str] | None = None, *, shared_log: bool = False
) -> list[dict[str, Any]]:
    """Extract normalized timestamped entries from an activity log file."""
    events: list[dict[str, Any]] = []
    if not log_path.is_file():
        return events
    shared_re: re.Pattern[str] | None = None
    if shared_log and variants:
        pattern = "|".join(
            re.escape(v) for v in sorted(variants, key=len, reverse=True)
        )
        shared_re = re.compile(
            rf"(?<![a-zA-Z0-9_-])(?:{pattern})(?![a-zA-Z0-9_-])",
            re.IGNORECASE,
        )
    with contextlib.suppress(OSError, UnicodeDecodeError):
        for raw_line in log_path.read_text(encoding="utf-8").splitlines():
            m = _BRACKET_TS_RE.match(raw_line)
            if not m:
                continue
            ts_str, msg = m.group(1).strip(), m.group(2).strip()
            if not msg:
                continue
            if shared_re is not None and not shared_re.search(raw_line):
                continue
            events.append(
                {
                    "ts": _normalize_utc_iso(ts_str),
                    "category": "activity",
                    "stage": "",
                    "sub_step": "",
                    "detail": log_path.name,
                    "message": msg,
                    "source": "activity_log",
                }
            )
    return events


def _collect_epic_activity_events(
    repo_path: Path, epic_slug: str
) -> tuple[list[dict[str, Any]], bool]:
    """Collect archived and active activity log events scoped to `epic_slug`."""
    variants = _collect_slug_variants(epic_slug)
    variants_set = set(variants)
    norm_target = _normalize_slug(epic_slug)
    devtool_dirs = _collect_devtool_dirs(repo_path, active_epic=epic_slug)

    log_files = [
        *_collect_matching_epic_files(
            devtool_dirs, "archive", "activity_", ".log", variants_set, norm_target
        ),
        *_collect_matching_epic_files(
            devtool_dirs, "logs", "activity_", ".log", variants_set, norm_target
        ),
    ]
    has_epic_activity_file = bool(log_files)
    events: list[dict[str, Any]] = []
    for path_obj in log_files:
        events.extend(_parse_activity_log_events(path_obj))

    seen_shared: set[Path] = set()
    for dt_dir in devtool_dirs:
        shared = dt_dir / "logs" / "activity.log"
        if shared.is_file() and shared.resolve() not in seen_shared:
            seen_shared.add(shared.resolve())
            events.extend(
                _parse_activity_log_events(
                    shared, variants=variants_set, shared_log=True
                )
            )
    return events, has_epic_activity_file or bool(events)


def _select_evidence_run(runs: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    """Select the primary verification run (`verify` > `red` > latest timestamp)."""
    for preferred in ("verify", "red"):
        cand = runs.get(preferred)
        if isinstance(cand, dict):
            return preferred, cand
    best: tuple[str, dict[str, Any]] | None = None
    best_ts: tuple[int, float, str] = (-1, 0.0, "")
    for key, cand in runs.items():
        if not isinstance(cand, dict):
            continue
        ts_key = _timestamp_sort_key(cand.get("finished") or cand.get("started"))
        if best is None or ts_key > best_ts:
            best_ts = ts_key
            best = (str(key), cand)
    return best


def _load_task_evidence_summary(evidence_path: Path) -> dict[str, Any] | None:
    """Read task verification evidence JSON with `output_tail` bounded to <= 8 lines."""
    data = _read_json_dict(evidence_path)
    if not data:
        return None
    runs = data.get("runs")
    if not isinstance(runs, dict) or not runs:
        return None
    selected = _select_evidence_run(runs)
    if selected is None:
        return None
    run_phase, run_obj = selected
    raw_rows = run_obj.get("rows")
    rows: list[dict[str, Any]] = []
    if isinstance(raw_rows, list):
        for row in raw_rows:
            if not isinstance(row, dict):
                continue
            raw_tail = row.get("output_tail")
            if isinstance(raw_tail, list):
                tail = [str(line) for line in raw_tail[-MAX_EVIDENCE_TAIL_LINES:]]
            elif isinstance(raw_tail, str):
                tail = raw_tail.splitlines()[-MAX_EVIDENCE_TAIL_LINES:]
            else:
                tail = []
            rows.append(
                {
                    "id": str(row.get("id") or ""),
                    "phase": str(row.get("phase") or run_phase),
                    "command": str(row.get("command") or ""),
                    "outcome": str(row.get("outcome") or ""),
                    "reason": str(row.get("reason") or ""),
                    "started": _normalize_utc_iso(row.get("started")),
                    "finished": _normalize_utc_iso(row.get("finished")),
                    "output_tail": tail,
                }
            )
    passed = sum(1 for r in rows if r["outcome"].upper() == "PASS")
    return {
        "phase": run_phase,
        "status": str(data.get("status") or ""),
        "head": str(run_obj.get("head") or ""),
        "started": _normalize_utc_iso(run_obj.get("started")),
        "finished": _normalize_utc_iso(run_obj.get("finished")),
        "passed_rows": passed,
        "total_rows": len(rows),
        "rows": rows,
    }


def _find_task_evidence(
    task_id: str, checkouts: list[Path], variants: list[str]
) -> dict[str, Any] | None:
    """Locate `<task_id>.json` across candidate checkouts; return None if corrupt."""
    candidates: list[Path] = []
    for co in checkouts:
        for variant in variants:
            candidates.append(
                co / ".devtool" / "epic" / variant / "evidence" / f"{task_id}.json"
            )
        candidates.append(co / ".devtool" / "evidence" / f"{task_id}.json")
    for cand in candidates:
        if cand.is_file():
            return _load_task_evidence_summary(cand)
    return None


def _parse_task_card(
    tf: Path, epic_slug: str, variants: set[str], norm_target: str, source: str
) -> dict[str, Any] | None:
    """Parse a single `task_*.md` card if it belongs to `epic_slug`."""
    with contextlib.suppress(OSError, UnicodeDecodeError):
        content = tf.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        task_epic = str(fm.get("epic") or "").strip()
        dir_match = (
            tf.parent.name in variants or _normalize_slug(tf.parent.name) == norm_target
        )
        if task_epic:
            if _normalize_slug(task_epic) != norm_target:
                return None
        elif not dir_match:
            return None

        title = tf.stem
        for line in content.splitlines():
            if line.strip().startswith("# "):
                title = line.strip().lstrip("# ").strip()
                break

        raw_labels = fm.get("labels", [])
        if isinstance(raw_labels, str):
            try:
                parsed_labels = json.loads(raw_labels)
                labels = (
                    [str(x) for x in parsed_labels]
                    if isinstance(parsed_labels, list)
                    else [raw_labels]
                )
            except Exception:
                labels = [raw_labels]
        elif isinstance(raw_labels, list):
            labels = [str(x) for x in raw_labels]
        else:
            labels = []

        return {
            "id": tf.stem,
            "title": title,
            "status": normalize_task_status(fm.get("status")),
            "priority": str(fm.get("priority") or "medium"),
            "epic": task_epic or epic_slug,
            "labels": labels,
            "time": format_relative_time(
                fm.get("completedAt") or fm.get("modified") or fm.get("created")
            ),
            "source": source,
        }
    return None


def _collect_epic_tasks_with_evidence(
    repo_path: Path, epic_slug: str, status: str, matching_wts: list[Path]
) -> list[dict[str, Any]]:
    """Harvest epic tasks (worktree-first when in_progress) and attach evidence."""
    variants = _collect_slug_variants(epic_slug)
    variants_set = set(variants)
    norm_target = _normalize_slug(epic_slug)

    wt_sources: list[tuple[Path, str]] = []
    for wt in matching_wts:
        wt_sources.extend(
            [
                (wt / ".devtool" / "features", "worktree"),
                (wt / ".devtool" / "features" / "done", "worktree"),
                *[(wt / ".devtool" / "epic" / v, "worktree") for v in variants],
            ]
        )
    root_sources: list[tuple[Path, str]] = [
        *[(repo_path / ".devtool" / "epic" / v, "root") for v in variants],
        (repo_path / ".devtool" / "features", "root"),
        (repo_path / ".devtool" / "features" / "done", "root"),
    ]
    ordered_dirs = (
        [*wt_sources, *root_sources]
        if status == "in_progress" and matching_wts
        else [*root_sources, *wt_sources]
    )
    evidence_checkouts = (
        [*matching_wts, repo_path]
        if status == "in_progress" and matching_wts
        else [repo_path, *matching_wts]
    )

    seen_ids: set[str] = set()
    tasks: list[dict[str, Any]] = []
    for task_dir, source in ordered_dirs:
        if not task_dir.is_dir():
            continue
        for tf in sorted(task_dir.glob("task_*.md"), key=natural_sort_key):
            if tf.stem in seen_ids:
                continue
            card = _parse_task_card(tf, epic_slug, variants_set, norm_target, source)
            if card is None:
                continue
            seen_ids.add(tf.stem)
            card["evidence"] = _find_task_evidence(
                tf.stem, evidence_checkouts, variants
            )
            tasks.append(card)

    tasks.sort(key=lambda t: natural_sort_key(t.get("id", "")))
    return tasks


def _build_unified_timeline(
    repo_path: Path,
    epic_slug: str,
    step_events: list[dict[str, Any]],
    gate_entries: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    activity_events: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Combine step, gate, activity, and evidence events into sorted UTC order."""
    if activity_events is None:
        activity_events, _ = _collect_epic_activity_events(repo_path, epic_slug)

    raw_items: list[dict[str, Any]] = [*step_events, *activity_events]

    for g in gate_entries:
        gate_num = _safe_int_val(g.get("gate"), 0)
        summary = str(g.get("summary") or g.get("approved") or "").strip()
        approver = str(g.get("approver") or g.get("by") or "").strip()
        commit = str(g.get("commit") or "").strip()
        detail = (
            f"{approver} ({commit})" if approver and commit else (approver or commit)
        )
        msg = f"Gate {gate_num}: {summary}" if summary else f"Gate {gate_num} approved"
        raw_items.append(
            {
                "ts": _normalize_utc_iso(g.get("timestamp")),
                "category": "gate",
                "stage": _GATE_STAGE_MAP.get(gate_num, ""),
                "sub_step": f"gate_{gate_num}" if gate_num else "gate",
                "detail": detail,
                "message": msg,
                "source": "gate_ledger",
            }
        )

    for task in tasks:
        ev = task.get("evidence")
        if not isinstance(ev, dict):
            continue
        ts_val = str(ev.get("finished") or ev.get("started") or "").strip()
        if not ts_val:
            continue
        phase = str(ev.get("phase") or "verify")
        passed = _safe_int_val(ev.get("passed_rows"), 0)
        total = _safe_int_val(ev.get("total_rows"), 0)
        raw_items.append(
            {
                "ts": ts_val,
                "category": "evidence",
                "stage": "tasks",
                "sub_step": str(task.get("id") or ""),
                "detail": str(ev.get("head") or ""),
                "message": f"{task.get('id')} ({phase}): {passed}/{total} rows PASS",
                "source": "evidence",
            }
        )

    # First pass: collect which (ts, category, sub_step, message) tuples have at least one non-empty review_state
    has_nonempty_rev: set[tuple[str, str, str, str]] = set()
    for item in raw_items:
        rev_k = _review_state_key(item.get("review_state"))
        if rev_k:
            b_key = (
                str(item.get("ts") or ""),
                str(item.get("category") or ""),
                str(item.get("sub_step") or ""),
                str(item.get("message") or ""),
            )
            has_nonempty_rev.add(b_key)

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for item in raw_items:
        rev_key = _review_state_key(item.get("review_state"))
        base_key = (
            str(item.get("ts") or ""),
            str(item.get("category") or ""),
            str(item.get("sub_step") or ""),
            str(item.get("message") or ""),
        )
        if not rev_key and base_key in has_nonempty_rev:
            continue
        key = (*base_key, rev_key)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    deduped.sort(
        key=lambda item: (
            _timestamp_sort_key(item.get("ts")),
            str(item.get("category") or ""),
            str(item.get("message") or ""),
        )
    )
    return deduped


def _extract_epic_title(
    epic_dirs: list[Path], epic_slug: str, variants: list[str]
) -> str:
    """Extract display title from HLD or design markdown headings."""
    candidates: list[Path] = []
    for ed in epic_dirs:
        for v in variants:
            variant_doc = epic_doc_path(ed, v)
            if variant_doc is not None and variant_doc not in candidates:
                candidates.append(variant_doc)
        with contextlib.suppress(OSError):
            for doc in sorted(ed.glob("*.md")):
                if (
                    doc not in candidates
                    and not doc.name.endswith(".vi.md")
                    and not doc.name.startswith("task_")
                    and doc.name != "handoff.md"
                ):
                    candidates.append(doc)
    for doc in candidates:
        if not doc.is_file():
            continue
        with contextlib.suppress(OSError, UnicodeDecodeError):
            for line in doc.read_text(encoding="utf-8").splitlines():
                if line.startswith("# "):
                    raw = line.lstrip("#").strip()
                    if raw.lower().startswith("epic:"):
                        raw = raw[5:].strip()
                    if raw:
                        return raw
    return epic_slug


def _compute_last_updated_iso(
    timeline: list[dict[str, Any]],
    heartbeat: dict[str, Any] | None,
    epic_dirs: list[Path],
) -> str:
    """Resolve most recent UTC ISO timestamp across timeline, heartbeat, and files."""
    candidates: list[str] = []
    if timeline and timeline[-1].get("ts"):
        candidates.append(str(timeline[-1]["ts"]))
    if heartbeat and heartbeat.get("updated_at"):
        candidates.append(_normalize_utc_iso(heartbeat.get("updated_at")))
    mtimes: list[float] = []
    for ed in epic_dirs:
        if ed.is_dir():
            with contextlib.suppress(OSError):
                mtimes.append(ed.stat().st_mtime)
                for child in ed.iterdir():
                    if child.is_file():
                        mtimes.append(child.stat().st_mtime)
    if mtimes:
        candidates.append(
            _normalize_utc_iso(
                datetime.fromtimestamp(max(mtimes), tz=timezone.utc).isoformat()
            )
        )
    valid = [c for c in candidates if _parse_utc_datetime(c) is not None]
    if not valid:
        return ""
    valid.sort(key=_timestamp_sort_key)
    return valid[-1]


def harvest_epic_history(repo_path: Path, epic_slug: str) -> dict[str, Any]:
    """Harvest full per-epic history payload for `/api/epic/history` without mutating `/api/tasks`."""
    with _scan_cache_scope():
        return _harvest_epic_history_impl(repo_path, epic_slug)


def _harvest_epic_history_impl(repo_path: Path, epic_slug: str) -> dict[str, Any]:
    variants = _collect_slug_variants(epic_slug)
    matching_wts = _collect_matching_worktrees(repo_path, epic_slug)
    epic_dirs: list[Path] = []
    for checkout in [*matching_wts, repo_path]:
        epic_dirs.extend(_find_epic_dirs_for_checkout(checkout, epic_slug))

    completed_slugs = get_completed_epic_slugs(repo_path)
    abandoned_slugs = get_abandoned_epic_slugs(repo_path)
    gate_entries = parse_gate_ledger_entries(repo_path, epic_slug)
    merged_hb = _merge_epic_heartbeats(repo_path, epic_slug)
    activity_events, has_activity = _collect_epic_activity_events(repo_path, epic_slug)

    hld_status: str | None = None
    for ed in epic_dirs:
        hld_status = extract_epic_hld_status(ed, ed.name) or extract_epic_hld_status(
            ed, epic_slug
        )
        if hld_status is not None:
            break

    has_gate5 = any(_safe_int_val(g.get("gate"), 0) == 5 for g in gate_entries)
    has_gate3_or_more = any(_safe_int_val(g.get("gate"), 0) >= 3 for g in gate_entries)
    if (
        hld_status == "done"
        or _is_completed_epic(epic_slug, completed_slugs)
        or has_gate5
    ):
        status = "done"
    elif hld_status in ("abandon", "abandoned") or _is_completed_epic(
        epic_slug, abandoned_slugs
    ):
        status = hld_status if hld_status in ("abandon", "abandoned") else "abandoned"
    elif hld_status == "packaged":
        if _is_packaged_epic_promoted(
            repo_path,
            epic_slug,
            has_wt=bool(matching_wts),
            has_gate3_or_more=has_gate3_or_more,
            has_active_telemetry=merged_hb["has_heartbeat"] or merged_hb["has_stream"],
            has_active_tasks=False,  # Checked below when tasks are collected
        ):
            status = "in_progress"
        else:
            status = "packaged"
    elif (
        matching_wts
        or hld_status == "in_progress"
        or gate_entries
        or merged_hb["has_heartbeat"]
        or merged_hb["has_stream"]
    ):
        status = "in_progress"
    else:
        status = "unstarted"

    tasks = _collect_epic_tasks_with_evidence(
        repo_path, epic_slug, status, matching_wts
    )
    if status in ("unstarted", "packaged") and any(
        t.get("status") in ("in-progress", "review", "done") for t in tasks
    ):
        status = "in_progress"

    exists = bool(
        epic_dirs
        or matching_wts
        or _is_completed_epic(epic_slug, completed_slugs)
        or _is_completed_epic(epic_slug, abandoned_slugs)
        or gate_entries
        or merged_hb["has_stream"]
        or merged_hb["has_heartbeat"]
        or tasks
        or has_activity
    )

    timeline = _build_unified_timeline(
        repo_path,
        epic_slug,
        list(merged_hb["step_events"]),
        gate_entries,
        tasks,
        activity_events=activity_events,
    )
    if merged_hb["has_stream"]:
        log_completeness = "full_stream"
    elif timeline or merged_hb["has_heartbeat"] or gate_entries:
        log_completeness = "snapshot_and_ledger"
    else:
        log_completeness = "none"

    is_completed = status == "done"
    done_tasks = sum(1 for t in tasks if t.get("status") == "done")
    total_tasks = len(tasks)
    pending_snap = _read_state_snapshot(
        repo_path, "pending_decision.json", {}, active_epic=epic_slug
    )
    pending_decision = _match_pending_decision_for_epic(pending_snap, epic_slug)
    pipeline_telemetry = build_epic_pipeline_telemetry(
        repo_path,
        epic_slug,
        done_tasks=done_tasks,
        total_tasks=total_tasks,
        heartbeat=merged_hb["heartbeat"],
        pending_decision=pending_decision,
        is_completed=is_completed,
    )

    hb_dict = merged_hb["heartbeat"]
    pic = extract_epic_pic(repo_path, epic_slug) or (
        str(hb_dict.get("pic")).strip()
        if isinstance(hb_dict, dict) and hb_dict.get("pic")
        else None
    )
    last_updated_iso = _compute_last_updated_iso(timeline, hb_dict, epic_dirs)

    return {
        "exists": exists,
        "epic": {
            "slug": epic_slug,
            "title": _extract_epic_title(epic_dirs, epic_slug, variants),
            "status": status,
            "pic": pic,
            "has_worktree": bool(matching_wts),
            "worktree_path": str(matching_wts[0]) if matching_wts else None,
            "done_tasks": done_tasks,
            "total_tasks": total_tasks,
            "last_updated": last_updated_iso,
            "last_updated_human": (
                format_relative_time(last_updated_iso) if last_updated_iso else ""
            ),
        },
        "pipeline_telemetry": pipeline_telemetry,
        "tasks": tasks,
        "timeline": timeline,
        "log_completeness": log_completeness,
    }


@contextlib.contextmanager
def _scan_cache_scope() -> Iterator[None]:
    """Enable per-request `_SCAN_CTX.cache` across nested repository/epic scans."""
    depth = getattr(_SCAN_CTX, "depth", 0)
    if depth == 0:
        _SCAN_CTX.cache = {}
    _SCAN_CTX.depth = depth + 1
    try:
        yield
    finally:
        _SCAN_CTX.depth = max(0, getattr(_SCAN_CTX, "depth", 1) - 1)
        if _SCAN_CTX.depth == 0:
            _SCAN_CTX.cache = None


_HUMAN_HALT_TOKENS: tuple[str, ...] = (
    "MODEL_UNAVAILABLE",
    "QUOTA_LOW",
    "LOW_QUOTA_STOP",
    "FIX_PLAN_ESCALATE",
)
_HALT_TOKEN_RE = re.compile(r"\b(" + "|".join(_HUMAN_HALT_TOKENS) + r")\b")
_HUMAN_DECISION_KINDS = frozenset({"quota", "blocker"})


@dataclass
class _AgyPoolView:
    """Dashboard view of the global agy profile pool for one scan."""

    summary: dict[str, Any] | None = None
    profiles: list[dict[str, Any]] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)
    exhaustion_lines: list[str] = field(default_factory=list)


@dataclass
class _OrchestratorSignals:
    """Persona, checkpoint, quota, halt and pool signals added to a repository payload."""

    persona_bindings: list[dict[str, Any]] = field(default_factory=list)
    persona_config_error: str | None = None
    checkpoint: dict[str, Any] | None = None
    low_quota: dict[str, Any] | None = None
    pool: _AgyPoolView = field(default_factory=_AgyPoolView)
    blockers: list[dict[str, str]] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)


def _parse_utc_iso(raw: Any) -> datetime | None:
    """Parse an ISO-8601 timestamp (with optional trailing Z) as aware UTC, else None."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _dict_or_none(value: Any) -> dict[str, Any] | None:
    return dict(value) if isinstance(value, dict) else None


def _resolve_persona_bindings(
    repo_path: Path,
) -> tuple[list[dict[str, Any]], str | None]:
    """Return the resolved persona bindings, or an empty list and the configuration error."""
    try:
        persona_mod = _load_kit_module("persona_config", *_PERSONA_CONFIG_REL)
        resolved = persona_mod.resolve_all_personas(repo_path)
        bindings = [
            {
                "persona": str(binding.persona),
                "alias": str(binding.alias),
                "cli": str(binding.cli),
                "model_id": str(binding.model_id),
                "effort": str(binding.effort),
                "fallback_alias": binding.fallback_alias,
                "sources": dict(binding.sources),
            }
            for binding in resolved.values()
        ]
    except Exception as exc:  # noqa: BLE001 - the dashboard degrades instead of raising
        return [], str(exc) or exc.__class__.__name__
    return bindings, None


def _detect_dashboard_profile(account_id: str | None) -> str:
    """Return the PIC profile, else the profile named by the environment, else `default`."""
    if account_id:
        return account_id
    env_profile = (
        os.environ.get("AGY_PROFILE", "") or os.environ.get("ANTIGRAVITY_PROFILE", "")
    ).strip()
    if env_profile.lstrip("@"):
        return env_profile.lstrip("@")
    home = os.environ.get("HOME", "")
    if "/antigravity_homes/" in home:
        candidate = home.split("/antigravity_homes/", 1)[1].split("/", 1)[0].strip()
        if candidate:
            return candidate
    return "default"


def _resolve_low_quota(repo_path: Path, profile: str) -> dict[str, Any] | None:
    """Return the active low-quota state for `profile`, or None when off, expired or unreadable."""
    try:
        persona_mod = _load_kit_module("persona_config", *_PERSONA_CONFIG_REL)
        return _dict_or_none(persona_mod.low_quota_state(repo_path, profile))
    except Exception:  # noqa: BLE001 - invalid configuration is reported by the bindings
        return None


def _agy_holder_notice(profile: str, holder: dict[str, Any]) -> str:
    owner_parts = [str(holder[key]) for key in ("epic", "task") if holder.get(key)]
    if holder.get("slot") is not None:
        owner_parts.append(f"slot {holder['slot']}")
    detail = ", ".join(
        f"{label} {holder[key]}"
        for label, key in (("role", "role"), ("repository", "repo"))
        if holder.get(key)
    )
    owner = "/".join(owner_parts) or "an unnamed owner"
    return f"agy profile {profile} is in use by {owner}" + (
        f" ({detail})" if detail else ""
    )


def _agy_profile_entry(entry: dict[str, Any], now: datetime) -> dict[str, Any]:
    quota = _dict_or_none(entry.get("quota"))
    exhausted_until = _parse_utc_iso(entry.get("exhausted_until"))
    return {
        "profile": str(entry.get("profile") or ""),
        "priority": entry.get("priority"),
        "max_concurrent": entry.get("max_concurrent"),
        "leased_by": [
            dict(holder)
            for holder in entry.get("leased_by") or []
            if isinstance(holder, dict)
        ],
        "exhausted_until": entry.get("exhausted_until"),
        "exhausted_reason": entry.get("exhausted_reason"),
        "is_exhausted": exhausted_until is not None and exhausted_until > now,
        "quota": quota,
        "quota_5h": _dict_or_none((quota or {}).get("gemini5h")),
        "quota_weekly": _dict_or_none((quota or {}).get("geminiWeekly")),
    }


def _agy_exhaustion_lines(
    pool_mod: Any, repo_path: Path, status: dict[str, Any]
) -> list[str]:
    """Print `agy_profile_pool.exhaustion_report` for the programmer binding of `repo_path`."""
    persona_mod = _load_kit_module("persona_config", *_PERSONA_CONFIG_REL)
    try:
        catalogue = persona_mod.load_persona_config(repo_path)["models"]
        binding = persona_mod.resolve_persona("programmer", repo_path)
    except Exception:  # noqa: BLE001 - report without switch commands when invalid
        catalogue = {}
        binding = persona_mod.PersonaBinding(
            persona="programmer",
            alias="",
            cli="",
            model_id="",
            effort="",
            quota_pool="provider",
            fallback_alias=None,
            sources={},
        )
    return list(
        pool_mod.exhaustion_report(
            status, catalogue=catalogue, programmer_binding=binding, fetcher=None
        )
    )


def _build_agy_pool_view(repo_path: Path) -> _AgyPoolView:
    """Read the global agy profile pool; any failure becomes a notice, never an exception."""
    try:
        pool_mod = _load_kit_module("agy_profile_pool", *_AGY_POOL_REL)
        status = pool_mod.pool_status()
        now = datetime.now(timezone.utc)
        state = str(status.get("state") or "")
        view = _AgyPoolView(
            summary={"state": state, "earliest_reset": status.get("earliest_reset")},
            profiles=[
                _agy_profile_entry(entry, now)
                for entry in status.get("profiles") or []
                if isinstance(entry, dict)
            ],
        )
        for entry in view.profiles:
            view.notices.extend(
                _agy_holder_notice(entry["profile"], holder)
                for holder in entry["leased_by"]
            )
        if state == "busy":
            view.notices.append(
                "agy profile pool is busy: every profile that still has quota is in use"
            )
        if state == "exhausted":
            view.exhaustion_lines = _agy_exhaustion_lines(pool_mod, repo_path, status)
        return view
    except Exception as exc:  # noqa: BLE001 - missing or invalid pool files must not break a scan
        return _AgyPoolView(
            notices=[
                f"agy profile pool unavailable: {str(exc) or exc.__class__.__name__}"
            ]
        )


def _find_halt_tokens(heartbeat: dict[str, Any] | None, state_text: str) -> list[str]:
    """Return recognised halt reasons (case-sensitive) from heartbeat `halt_reason` or state text."""
    sources: list[Any] = [state_text]
    if heartbeat:
        sources.insert(0, heartbeat.get("halt_reason"))
    found: list[str] = []
    for source in sources:
        if not isinstance(source, str):
            continue
        for token in _HALT_TOKEN_RE.findall(source):
            if token not in found:
                found.append(token)
    return found


def _checkpoint_warning_notices(checkpoint: dict[str, Any] | None) -> list[str]:
    raw = (checkpoint or {}).get("warning")
    items = raw if isinstance(raw, (list, tuple)) else [raw]
    return [
        f"Checkpoint warning: {item.strip()}"
        for item in items
        if isinstance(item, str) and item.strip()
    ]


def _iter_active_decisions(
    snapshot: dict[str, Any],
) -> Iterator[tuple[str, dict[str, Any]]]:
    decisions = snapshot.get("decisions")
    if isinstance(decisions, dict) and decisions:
        for key, entry in decisions.items():
            if isinstance(entry, dict) and entry.get("active", True) is True:
                yield str(entry.get("epic") or key), entry
    elif snapshot.get("active") is True and snapshot.get("epic"):
        yield str(snapshot["epic"]), snapshot


def _unseen_decision_blockers(
    snapshot: dict[str, Any],
    seen_blockers: set[str],
    closed_slugs: set[str],
) -> list[dict[str, str]]:
    """Alert on active quota or blocker decisions for epics that have no blocker yet."""
    blockers: list[dict[str, str]] = []
    for epic, entry in _iter_active_decisions(snapshot):
        norm = _normalize_slug(epic)
        if (
            str(entry.get("kind") or "").lower() not in _HUMAN_DECISION_KINDS
            or not norm
            or norm in seen_blockers
            or _is_completed_epic(epic, closed_slugs)
        ):
            continue
        seen_blockers.add(norm)
        blockers.append(
            {
                "epic": epic,
                "stage": str(entry.get("stage") or "Pending decision"),
                "reason": str(entry.get("reason") or "Confirmation required"),
            }
        )
    return blockers


def _collect_orchestrator_signals(
    repo_path: Path,
    active_epic: str | None,
    account_id: str | None,
    heartbeat: dict[str, Any] | None,
    *,
    decisions_snapshot: dict[str, Any],
    stage_name: str,
    seen_blockers: set[str],
    closed_slugs: set[str],
) -> _OrchestratorSignals:
    """Gather persona bindings, checkpoint, low-quota, halt and agy pool signals for one repo."""
    signals = _OrchestratorSignals()
    signals.persona_bindings, signals.persona_config_error = _resolve_persona_bindings(
        repo_path
    )
    signals.low_quota = _resolve_low_quota(
        repo_path, _detect_dashboard_profile(account_id)
    )
    signals.checkpoint = _dict_or_none((heartbeat or {}).get("checkpoint"))
    signals.pool = _build_agy_pool_view(repo_path)
    signals.notices = [
        *signals.pool.notices,
        *_checkpoint_warning_notices(signals.checkpoint),
    ]

    hb_epic = str((heartbeat or {}).get("epic_slug") or "").strip()
    active_closed = bool(active_epic and _is_completed_epic(active_epic, closed_slugs))
    hb_closed = bool(hb_epic and _is_completed_epic(hb_epic, closed_slugs))
    if not active_closed:
        state_text = (
            _read_combined_state_text(repo_path, active_epic) if active_epic else ""
        )
        effective_hb = None if hb_closed else heartbeat
        signals.blockers.extend(
            {
                "epic": active_epic or repo_path.name,
                "stage": stage_name,
                "reason": f"Orchestrator halted: {token}",
                "kind": "halt",
            }
            for token in _find_halt_tokens(effective_hb, state_text)
        )
    signals.blockers.extend(
        _unseen_decision_blockers(decisions_snapshot, seen_blockers, closed_slugs)
    )
    if signals.pool.exhaustion_lines:
        signals.blockers.append(
            {
                "epic": "agy profile pool",
                "stage": "Out of quota",
                "reason": "\n".join(signals.pool.exhaustion_lines),
                "kind": "agy_pool",
            }
        )
    return signals


def scan_repo(repo_path: Path) -> RepoMetadata:
    """Harvest complete metadata and telemetry for a single repository."""
    with _scan_cache_scope():
        return _scan_repo_impl(repo_path)


def _scan_repo_impl(repo_path: Path) -> RepoMetadata:
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
    exec_state_snapshot = _read_state_snapshot(
        repo_path, "epic_execution_state.json", {}
    )
    raw_exec_states = (
        exec_state_snapshot.get("states")
        if isinstance(exec_state_snapshot, dict)
        else {}
    )
    exec_states_by_norm: dict[str, dict[str, str]] = {}
    if isinstance(raw_exec_states, dict):
        for raw_slug, raw_entry in raw_exec_states.items():
            if not isinstance(raw_entry, dict):
                continue
            st_val = str(raw_entry.get("state") or "").strip().lower()
            if st_val in ("pending", "cancelled"):
                exec_states_by_norm[_normalize_slug(str(raw_slug))] = {
                    "state": st_val,
                    "reason": str(raw_entry.get("reason") or "").strip(),
                    "updated_at": str(raw_entry.get("updated_at") or "").strip(),
                }
    heartbeat = _read_epic_heartbeat(repo_path, active_epic)
    quality_active, quality_runs = _read_quality_state(repo_path, active_epic)

    decision = derive_lifecycle_state(
        repo_path, active_epic, pending_decision=matched_pending
    )
    if active_epic and _normalize_slug(active_epic) in exec_states_by_norm:
        active_exec = exec_states_by_norm[_normalize_slug(active_epic)]
        decision = LifecycleDecision(
            stage_name=decision.stage_name,
            gate_status=active_exec["state"].capitalize(),
            prompt=active_exec["reason"] or f"Epic marked as {active_exec['state']}",
            is_human_action_required=False,
            is_blocked=False,
        )
    active_stage = decision.stage_name

    # Propagate deterministic action requirements and pipeline_telemetry to each epic in epics_summary
    completed_slugs = get_completed_epic_slugs(repo_path)
    abandoned_slugs = get_abandoned_epic_slugs(repo_path)
    active_done_tasks = 0
    active_total_tasks = 0
    if active_epic:
        norm_active = _normalize_slug(active_epic)
        scoped_active_tasks = [
            t
            for t in task_progress.tasks
            if _normalize_slug(str(t.get("epic") or "")) == norm_active
        ]
        if scoped_active_tasks:
            active_done_tasks = sum(
                1 for t in scoped_active_tasks if t.get("status") == "done"
            )
            active_total_tasks = len(scoped_active_tasks)
        else:
            distinct_epics = {
                _normalize_slug(str(t.get("epic") or ""))
                for t in task_progress.tasks
                if str(t.get("epic") or "").strip()
            }
            known_other_epics = {
                _normalize_slug(str(ep.get("slug") or ""))
                for ep in (epics_summary.epics if epics_summary else [])
                if _normalize_slug(str(ep.get("slug") or "")) != norm_active
            }
            if len(distinct_epics) <= 1 and not (distinct_epics & known_other_epics):
                active_done_tasks = task_progress.done_tasks
                active_total_tasks = task_progress.total_tasks

    pipeline_telemetry = (
        build_epic_pipeline_telemetry(
            repo_path,
            active_epic,
            done_tasks=active_done_tasks,
            total_tasks=active_total_tasks,
            heartbeat=heartbeat,
            quality_active=quality_active,
            pending_decision=matched_pending,
            active_stage=active_stage,
            is_completed=bool(
                active_epic and _is_completed_epic(active_epic, completed_slugs)
            ),
        )
        if active_epic
        else None
    )
    action_blockers: list[dict[str, str]] = []
    seen_blockers: set[str] = set()
    if decision.is_human_action_required and active_epic:
        primary_reason = (
            str(matched_pending.get("reason"))
            if (
                matched_pending
                and matched_pending.get("active", True) is True
                and matched_pending.get("reason")
            )
            else decision.prompt
        )
        action_blockers.append(
            {
                "epic": active_epic,
                "stage": decision.stage_name,
                "reason": primary_reason,
            }
        )
        seen_blockers.add(_normalize_slug(active_epic))

    if epics_summary and epics_summary.epics:
        doing_count = 0
        pending_count = 0
        cancelled_count = 0
        base_abandoned_count = 0
        for ep in epics_summary.epics:
            slug = str(ep.get("slug") or "")
            norm_ep_slug = _normalize_slug(slug)
            exec_entry = exec_states_by_norm.get(norm_ep_slug)
            if ep.get("status") == "done" or _is_completed_epic(slug, completed_slugs):
                ep["execution_state"] = "doing"
                ep["execution_state_reason"] = ""
                ep["execution_state_updated_at"] = ""
                ep["is_action_required"] = False
                ep["action_prompt"] = ""
                ep["is_review_converged"] = True
                ep["active_stage"] = ""
                continue
            if ep.get("status") in (
                "abandon",
                "abandoned",
                "discarded",
                "cancelled",
            ) or _is_completed_epic(slug, abandoned_slugs):
                base_abandoned_count += 1
                ep["execution_state"] = (
                    exec_entry["state"] if exec_entry else "cancelled"
                )
                ep["execution_state_reason"] = (
                    exec_entry["reason"] if exec_entry else ""
                )
                ep["execution_state_updated_at"] = (
                    exec_entry["updated_at"] if exec_entry else ""
                )
                ep["is_action_required"] = False
                ep["action_prompt"] = ""
                ep["is_review_converged"] = False
                ep["active_stage"] = ""
                continue
            ep_exec_state = exec_entry["state"] if exec_entry else "doing"
            ep["execution_state"] = ep_exec_state
            ep["execution_state_reason"] = exec_entry["reason"] if exec_entry else ""
            ep["execution_state_updated_at"] = (
                exec_entry["updated_at"] if exec_entry else ""
            )
            if ep_exec_state == "pending":
                pending_count += 1
            elif ep_exec_state == "cancelled":
                cancelled_count += 1
            elif ep.get("status") == "in_progress" or (
                active_epic and norm_ep_slug == _normalize_slug(active_epic)
            ):
                doing_count += 1
            if active_epic and _normalize_slug(slug) == _normalize_slug(active_epic):
                ep["active_stage"] = decision.stage_name
                ep["is_action_required"] = decision.is_human_action_required
                ep["action_prompt"] = (
                    decision.prompt if decision.is_human_action_required else ""
                )
                ep["is_review_converged"] = (
                    decision.stage_name
                    == LifecycleStage.STAGE_3_PHASE_4_1_SIGNOFF.value
                    or bool(
                        pipeline_telemetry
                        and float(pipeline_telemetry.get("lifecycle_progress_pct", 0.0))
                        >= 98.0
                    )
                )
                ep["pipeline_telemetry"] = pipeline_telemetry
                if pipeline_telemetry is not None:
                    ep["task_count"] = max(
                        int(ep.get("task_count") or 0),
                        int(pipeline_telemetry.get("total_tasks") or 0),
                    )
            else:
                ep_pd = _match_pending_decision_for_epic(pd_snapshot, slug)
                ep_decision = derive_lifecycle_state(
                    repo_path, slug, pending_decision=ep_pd
                )
                ep["active_stage"] = ep_decision.stage_name
                ep_act = (
                    bool(ep_pd and ep_pd.get("active", True) is True)
                    or ep_decision.is_human_action_required
                )
                ep_prompt = (
                    str(ep_pd.get("reason", ""))
                    if (ep_pd and ep_pd.get("active", True) is True)
                    else ""
                )
                ep_conv = (
                    ep_decision.stage_name
                    == LifecycleStage.STAGE_3_PHASE_4_1_SIGNOFF.value
                )
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
                if ep_act:
                    resolved_ep_prompt = (
                        ep_prompt
                        or str(ep.get("action_prompt") or "")
                        or ep_decision.prompt
                    )
                    if resolved_ep_prompt:
                        ep["action_prompt"] = resolved_ep_prompt
                else:
                    ep["action_prompt"] = ""
                ep["is_review_converged"] = ep_conv
                if ep.get("status") == "in_progress" or _normalize_slug(
                    slug
                ) == _normalize_slug(active_epic or ""):
                    ep_tasks = [
                        t
                        for t in task_progress.tasks
                        if _normalize_slug(str(t.get("epic") or ""))
                        == _normalize_slug(slug)
                    ]
                    ep_done = sum(1 for t in ep_tasks if t.get("status") == "done")
                    ep_tot = max(len(ep_tasks), int(ep.get("task_count") or 0))
                    ep["pipeline_telemetry"] = build_epic_pipeline_telemetry(
                        repo_path,
                        slug,
                        done_tasks=ep_done,
                        total_tasks=ep_tot,
                        pending_decision=ep_pd,
                    )
                    ep["task_count"] = max(
                        int(ep.get("task_count") or 0),
                        int(ep["pipeline_telemetry"].get("total_tasks") or 0),
                    )

            if ep.get("execution_state") in ("pending", "cancelled"):
                ep["is_action_required"] = False
                ep["action_prompt"] = ""

            norm_slug = _normalize_slug(slug)
            if (
                slug
                and ep.get("is_action_required") is True
                and norm_slug not in seen_blockers
            ):
                action_blockers.append(
                    {
                        "epic": slug,
                        "stage": str(ep.get("active_stage") or "Stage 1 (Inception)"),
                        "reason": str(
                            ep.get("action_prompt") or "Confirmation required"
                        ),
                    }
                )
                seen_blockers.add(norm_slug)

        epics_summary.doing_count = doing_count
        epics_summary.pending_count = pending_count
        epics_summary.cancelled_count = cancelled_count
        epics_summary.in_progress = doing_count
        epics_summary.abandoned = base_abandoned_count + cancelled_count

    signals = _collect_orchestrator_signals(
        repo_path,
        active_epic,
        account_id,
        heartbeat,
        decisions_snapshot=pd_snapshot,
        stage_name=decision.stage_name,
        seen_blockers=seen_blockers,
        closed_slugs=completed_slugs | abandoned_slugs,
    )
    action_blockers.extend(signals.blockers)

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
        is_human_action_required=decision.is_human_action_required
        or bool(signals.blockers),
        is_blocked=decision.is_blocked,
        pending_decision=matched_pending,
        heartbeat=heartbeat,
        quality_active=quality_active,
        quality_runs=quality_runs,
        pipeline_telemetry=pipeline_telemetry,
        action_blockers=action_blockers,
        persona_bindings=signals.persona_bindings,
        persona_config_error=signals.persona_config_error,
        checkpoint=signals.checkpoint,
        low_quota=signals.low_quota,
        agy_pool=signals.pool.summary,
        agy_profiles=signals.pool.profiles,
        notices=signals.notices,
    )


DEFAULT_TRACKED_ORDER: tuple[str, ...] = (
    "D3Nexus",
    "lyrics-sync",
    "nexus",
    "ai-agent-tools",
)
PROJECTS_CONFIG_ENV = "CHECK_TASKS_PROJECTS_CONFIG"


def _expand_host_path(raw_path: str) -> Path:
    """Expand leading `~` against the real host HOME rather than an isolated profile HOME."""
    text = str(raw_path or "").strip()
    if not text:
        return Path("")
    if text == "~":
        return _real_home()
    if text.startswith("~/"):
        return _real_home() / text[2:]
    return Path(text)


def resolve_projects_config_path(
    workspace_root: Path, explicit_path: Path | None = None
) -> Path:
    """Resolve tracked-projects JSON path while keeping non-default test workspaces isolated."""
    if explicit_path is not None:
        return explicit_path
    env_override = os.environ.get(PROJECTS_CONFIG_ENV, "").strip()
    if env_override:
        return _expand_host_path(env_override)
    default_ws = _real_home() / "AllProjects"
    try:
        if workspace_root.resolve() == default_ws.resolve():
            return _real_home() / ".d3nexus" / "check_tasks_projects.json"
    except OSError:
        pass
    return workspace_root / ".check_tasks_projects.json"


def _sanitize_project_name(
    raw_name: str, existing_names: set[str], parent_name: str = ""
) -> str:
    """Derive a safe, unique display identifier for a tracked repository."""
    base = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(raw_name or "").strip()).strip("-")
    if not base or base in (".", ".."):
        base = "project"
    if base not in existing_names:
        return base
    clean_parent = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(parent_name or "").strip()).strip("-")
    if clean_parent and clean_parent not in (".", ".."):
        prefixed = f"{clean_parent}-{base}"
        if prefixed not in existing_names:
            return prefixed
    idx = 2
    while f"{base}-{idx}" in existing_names:
        idx += 1
    return f"{base}-{idx}"


def build_initial_tracked_projects(workspace_root: Path) -> list[dict[str, str]]:
    """Seed initial tracked project entries matching the default dashboard tab order."""
    if not workspace_root.is_dir():
        return []
    discovered: dict[str, Path] = {}
    with contextlib.suppress(OSError):
        for entry in sorted(workspace_root.iterdir(), key=lambda p: p.name.lower()):
            if entry.is_dir() and not entry.name.startswith(".") and (entry / ".git").exists():
                discovered[entry.name] = entry.resolve()
    seeded: list[dict[str, str]] = [
        {"name": name, "path": str(discovered[name])}
        for name in DEFAULT_TRACKED_ORDER
        if name in discovered
    ]
    if seeded:
        return seeded
    return [{"name": name, "path": str(path)} for name, path in discovered.items()]


def load_tracked_projects(
    workspace_root: Path, config_path: Path | None = None
) -> list[dict[str, str]] | None:
    """Load persisted tracked projects list, or return None when unconfigured."""
    cfg = resolve_projects_config_path(workspace_root, config_path)
    if not cfg.is_file():
        return None
    try:
        raw = json.loads(cfg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None
    items = raw.get("projects") if isinstance(raw, dict) else None
    if not isinstance(items, list):
        return None
    projects: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    seen_names: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        raw_p = str(item.get("path") or "").strip()
        if not raw_p:
            continue
        expanded = _expand_host_path(raw_p)
        try:
            resolved_str = str(expanded.resolve())
        except OSError:
            resolved_str = str(expanded)
        if resolved_str in seen_paths:
            continue
        raw_name = str(item.get("name") or expanded.name).strip()
        name = _sanitize_project_name(raw_name, seen_names, expanded.parent.name)
        seen_paths.add(resolved_str)
        seen_names.add(name)
        projects.append({"name": name, "path": resolved_str})
    return projects


def save_tracked_projects(
    projects: list[dict[str, str]],
    workspace_root: Path,
    config_path: Path | None = None,
) -> Path:
    """Atomically write the tracked projects JSON configuration file."""
    cfg = resolve_projects_config_path(workspace_root, config_path)
    cfg.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "projects": [
            {"name": str(p["name"]), "path": str(p["path"])}
            for p in projects
            if isinstance(p, dict) and p.get("name") and p.get("path")
        ],
    }
    tmp_path = cfg.with_name(f".{cfg.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_path, cfg)
    return cfg


def discover_untracked_workspace_repos(
    workspace_root: Path, tracked: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Return git repositories directly under workspace_root not currently tracked."""
    if not workspace_root.is_dir():
        return []
    tracked_paths: set[str] = set()
    for item in tracked:
        raw_p = str(item.get("path") or "").strip()
        if not raw_p:
            continue
        with contextlib.suppress(OSError):
            tracked_paths.add(str(_expand_host_path(raw_p).resolve()))
    suggestions: list[dict[str, str]] = []
    with contextlib.suppress(OSError):
        for entry in sorted(workspace_root.iterdir(), key=lambda p: p.name.lower()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            if not (entry / ".git").exists():
                continue
            resolved = str(entry.resolve())
            if resolved in tracked_paths:
                continue
            suggestions.append({"name": entry.name, "path": resolved})
    return suggestions


def add_tracked_project(
    workspace_root: Path,
    raw_path: str,
    *,
    config_path: Path | None = None,
    index: int | None = None,
) -> dict[str, Any]:
    """Validate a repository directory and persist it into the tracked projects list."""
    clean_raw = str(raw_path or "").strip()
    if not clean_raw:
        raise ValueError("Project folder path is required.")
    candidate = _expand_host_path(clean_raw)
    try:
        resolved = candidate.resolve()
    except OSError as exc:
        raise ValueError(f"Invalid folder path: {clean_raw}") from exc
    if not resolved.is_dir():
        raise ValueError(f"Folder does not exist: {clean_raw}")
    if not ((resolved / ".git").exists() or (resolved / ".devtool").is_dir()):
        raise ValueError(
            "Selected folder is not a Git repository (missing .git) or .devtool project."
        )

    tracked = load_tracked_projects(workspace_root, config_path)
    if tracked is None:
        tracked = build_initial_tracked_projects(workspace_root)

    resolved_str = str(resolved)
    for existing in tracked:
        if existing["path"] == resolved_str:
            raise ValueError(f"Project '{existing['name']}' is already tracked.")

    existing_names = {p["name"] for p in tracked}
    name = _sanitize_project_name(resolved.name, existing_names, resolved.parent.name)
    entry = {"name": name, "path": resolved_str}
    if isinstance(index, int):
        clamped = max(0, min(index, len(tracked)))
        tracked.insert(clamped, entry)
    else:
        tracked.append(entry)
    save_tracked_projects(tracked, workspace_root, config_path)
    return {"status": "ok", "project": entry, "projects": tracked}


def remove_tracked_project(
    workspace_root: Path,
    *,
    name: str = "",
    path: str = "",
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Remove a project from the tracked list without modifying files on disk."""
    target_name = str(name or "").strip()
    target_path = ""
    if path:
        with contextlib.suppress(OSError):
            target_path = str(_expand_host_path(path).resolve())
    if not target_name and not target_path:
        raise ValueError("Either 'name' or 'path' is required to remove a project.")

    tracked = load_tracked_projects(workspace_root, config_path)
    if tracked is None:
        tracked = build_initial_tracked_projects(workspace_root)

    match_idx: int | None = None
    for idx, entry in enumerate(tracked):
        if (target_name and entry["name"] == target_name) or (
            target_path and entry["path"] == target_path
        ):
            match_idx = idx
            break
    if match_idx is None:
        raise ValueError(f"Tracked project not found: {target_name or path}")

    removed = tracked.pop(match_idx)
    save_tracked_projects(tracked, workspace_root, config_path)
    return {
        "status": "ok",
        "removed": {**removed, "index": match_idx},
        "projects": tracked,
    }


def resolve_tracked_repo_dir(
    workspace_root: Path,
    repo_name: str,
    *,
    config_path: Path | None = None,
) -> tuple[Path, Path]:
    """Resolve `repo_name` to `(repo_dir, containment_boundary)`, supporting external tracked repos."""
    tracked = load_tracked_projects(workspace_root, config_path)
    if tracked is not None:
        for entry in tracked:
            if entry["name"] == repo_name:
                repo_resolved = Path(entry["path"]).resolve()
                return repo_resolved, repo_resolved
    ws_resolved = workspace_root.resolve()
    return ws_resolved / repo_name, ws_resolved


def harvest_dashboard_graph(
    root_path: Path,
    max_workers: int = 8,
    *,
    projects_config_path: Path | None = None,
) -> DashboardGraph:
    """Discover all repositories under workspace root in parallel and aggregate metrics."""
    repos: list[RepoMetadata] = []
    tracked = load_tracked_projects(root_path, projects_config_path)

    # Prioritize canonical order
    canonical_order = [
        "ai-agent-tools",
        "lyrics-sync",
        "nexus",
        "D3Nexus",
        "digital_wallet",
    ]

    if tracked is not None:
        ordered_specs: list[tuple[str, Path]] = []
        for entry in tracked:
            repo_dir = Path(entry["path"])
            if repo_dir.is_dir():
                ordered_specs.append((entry["name"], repo_dir))
        order_index = {name: idx for idx, (name, _) in enumerate(ordered_specs)}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(scan_repo, repo_dir): name
                for name, repo_dir in ordered_specs
            }
            for future in concurrent.futures.as_completed(futures):
                display_name = futures[future]
                with contextlib.suppress(Exception):
                    meta = future.result()
                    meta.name = display_name
                    repos.append(meta)
        repos.sort(key=lambda r: order_index.get(r.name, 9999))
    else:
        repo_dirs: list[Path] = []
        if root_path.is_dir():
            for entry in root_path.iterdir():
                if entry.is_dir() and not entry.name.startswith("."):
                    # Must be a git repo or have .git directory/file
                    if (entry / ".git").exists():
                        repo_dirs.append(entry)

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
        tracked_projects=tracked,
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

            target_port = 8766
            meta_file = Path("/tmp/agy_tasks_server.pid.meta.json")
            if meta_file.is_file():
                with contextlib.suppress(OSError, ValueError, TypeError):
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    if isinstance(meta, dict) and isinstance(meta.get("port"), int):
                        target_port = meta["port"]
            webbrowser.open(f"http://localhost:{target_port}/")
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
