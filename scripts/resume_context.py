#!/usr/bin/env python3
"""
Two-Tier Context Harvester, Multi-Epic Partitioning & Handoff Telemetry Tool.
- Harvest Mode (Default): Prints PROJECT_LEDGER.md, active epic state, implementer activity,
  git status across repositories, open contract RFCs, and active Kanban tasks.
- State Mode (--state): Writes epic state to .devtool/state/<epic_slug>.md (<= 20 lines)
  and renders .devtool/assistant_state.md rollup under fcntl.flock concurrency protection.
- Log Mode (--log): Appends structured programmer activity to .devtool/logs/activity_<epic_slug>.log
  and refreshes .devtool/activity_stream.log rollup under fcntl.flock concurrency protection.
- Compaction Mode (--complete <slug> "<summary>"): Appends permanent milestone to PROJECT_LEDGER.md,
  archives epic state and activity log to .devtool/archive/, and refreshes rollups.
- Prompt Mode (--emit-prompt <mode>): Emits deterministic handoff prompts across the four-persona roles.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import importlib.util
import json
import os
import re
import shlex
import sqlite3
import subprocess
import sys
import tempfile
from collections.abc import Iterator, Sequence
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any

_KIT_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_KIT_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_KIT_SCRIPTS_DIR))

import _state_envelope

WORKSPACE_ROOT = Path.home() / "Projects"
REPOS = ["ai-agent-tools", "D3Nexus", "lyrics-sync", "nexus"]
MAX_STATE_LINES = 20
COMPACT_MAX_BYTES = 4096
DEFAULT_PROGRAMMER_MODEL = "gemini-4-hydrogen-xhigh"
DEFAULT_PROGRAMMER_EFFORT = "xhigh"
LEGACY_PROGRAMMER_MODELS = frozenset({"gemini-3.8-flash", "gemini-3.8-flash-high"})
EXTRA_EFFORT_ALIASES = frozenset({"extra", "extra-high", "extra_high", "xhigh"})
CHECKPOINT_EVENTS: tuple[str, ...] = (
    "gate2_tasks_locked",
    "subagent_returned",
    "wave_merged",
    "model_unavailable",
    "turn_budget",
    "low_quota_stop",
    "quota_low",
)
ROLE_CHOICES: tuple[str, ...] = (
    "architect",
    "orchestrator",
    "programmer",
    "assistant",
)

DEFAULT_LEDGER_TEMPLATE = """# Project Architectural Ledger & Feature History (Permanent)

## 1. System Topology & Core Invariants
- **Hub (`D3Nexus`)**: Physical SSOT for `shared-contracts/`, Rust core + FastAPI engine, Flutter client.
- **Satellites (`lyrics-sync`, `nexus`)**: Outbound symlinks to `shared-contracts/`, mechanically verified by `check_contracts.py`.
- **Workflows (`ai-agent-tools`)**: Bilingual TOC (`doc-designer`), Contract-First `task_01` sequencing (`dev-designer`).

## 2. Completed Epics & Architectural Milestones
"""


def _load_module_by_path(module_name: str, module_path: Path) -> Any:
    """Load a kit helper module by path and register it in sys.modules."""
    existing = sys.modules.get(module_name)
    if existing is not None and getattr(existing, "__file__", None):
        if Path(str(existing.__file__)).resolve() == module_path.resolve():
            return existing
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module '{module_name}' from {module_path}")
    module: ModuleType = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_persona_config() -> Any:
    """Load scripts/persona_config.py by explicit path."""
    return _load_module_by_path("persona_config", _KIT_SCRIPTS_DIR / "persona_config.py")


def _load_epic_docs() -> Any:
    """Load skills/dev-implementation/resources/scripts/_epic_docs.py by explicit path."""
    return _load_module_by_path(
        "_epic_docs",
        _KIT_SCRIPTS_DIR.parent
        / "skills"
        / "dev-implementation"
        / "resources"
        / "scripts"
        / "_epic_docs.py",
    )


def normalize_role(role: str) -> str:
    """Normalize legacy 'assistant' role alias to 'architect'."""
    cleaned = role.lower().strip()
    return "architect" if cleaned == "assistant" else cleaned


def print_section(title: str) -> None:
    print(f"\n{'=' * 65}\n📌 {title}\n{'=' * 65}")


def print_role_banner(role: str) -> None:
    norm_role = normalize_role(role)
    if norm_role == "architect":
        print("=" * 65)
        print("🏛️ [PERSONA: Role 2.1 AI Architect & Reviewer]")
        print("⛔ READ-ONLY DESIGN & REVIEW: Author specs, plans, and reviews only.")
        print(
            "   Strictly prohibited from editing src/ or tests/ or executing code edits."
        )
        print("=" * 65)
    elif norm_role == "orchestrator":
        print("=" * 65)
        print("🎭 [PERSONA: Role 2.2 Orchestrator]")
        print("⛔ NO IMPLEMENTATION: Strictly prohibited from reading/editing src/ or tests/")
        print(
            "   or running test suites in main session. Coordinates & verifies Role 2.1/2.3."
        )
        print("=" * 65)
    elif norm_role in ("programmer", "implementer", "worker"):
        print("=" * 65)
        print("💻 [PERSONA: Role 2.3 Programmer — Senior TDD Software Engineer]")
        print("🎯 STRICT TDD & FIDELITY: Enforcing Red-Green-Refactor, Clean Code,")
        print("   Allowed files boundaries, and zero test fakery.")
        print("=" * 65)


def resolve_primary_repo_root(cwd: Path | None = None) -> Path:
    target_cwd = cwd or Path.cwd()
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=target_cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        common_dir = Path(res.stdout.strip())
        if not common_dir.is_absolute():
            common_dir = (target_cwd / common_dir).resolve()
        return common_dir.parent
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return target_cwd


def resolve_current_worktree_root(cwd: Path | None = None) -> Path:
    target_cwd = cwd or Path.cwd()
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=target_cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        top = Path(res.stdout.strip())
        if not top.is_absolute():
            top = (target_cwd / top).resolve()
        return top
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return target_cwd


def resolve_workspace_root(explicit_root: str | None = None) -> Path:
    if explicit_root:
        return Path(explicit_root).resolve()
    env_root = os.environ.get("WORKSPACE_ROOT")
    if env_root:
        return Path(env_root).resolve()
    primary = resolve_primary_repo_root()
    if primary.name in REPOS:
        return primary.parent
    for candidate in [Path.home() / "Projects", Path.home() / "AllProjects"]:
        if candidate.exists():
            return candidate.resolve()
    return primary


def resolve_current_epic_slug(cwd: Path | None = None) -> str:
    target_cwd = cwd or Path.cwd()
    try:
        res = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=target_cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        branch = res.stdout.strip()
        if branch.startswith("epic/"):
            return branch[5:]
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "general"
    return "general"


def _atomic_write_text(path: Path, content: str) -> None:
    """Atomically write UTF-8 text via sibling temporary file, fsync, and os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
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
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        tmp_path = None
    finally:
        if tmp_path is not None and tmp_path.exists():
            with contextlib.suppress(OSError):
                tmp_path.unlink()


@contextlib.contextmanager
def file_lock(devtool_dir: Path) -> Iterator[None]:
    devtool_dir.mkdir(parents=True, exist_ok=True)
    lock_file = devtool_dir / ".memory.lock"
    with lock_file.open("a+", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass


def migrate_legacy_storage(devtool_dir: Path) -> None:
    state_dir = devtool_dir / "state"
    logs_dir = devtool_dir / "logs"
    legacy_state = devtool_dir / "assistant_state.md"
    legacy_log = devtool_dir / "activity_stream.log"

    if legacy_state.exists() and not state_dir.exists():
        state_dir.mkdir(parents=True, exist_ok=True)
        gen_state = state_dir / "general.md"
        if not gen_state.exists():
            gen_state.write_text(
                legacy_state.read_text(encoding="utf-8"), encoding="utf-8"
            )

    if legacy_log.exists() and not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
        gen_log = logs_dir / "activity_general.log"
        if not gen_log.exists():
            gen_log.write_text(legacy_log.read_text(encoding="utf-8"), encoding="utf-8")


def ensure_ledger(root: Path) -> Path:
    devtool_dir = root / ".devtool"
    devtool_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = devtool_dir / "PROJECT_LEDGER.md"
    if not ledger_path.exists():
        ledger_path.write_text(DEFAULT_LEDGER_TEMPLATE, encoding="utf-8")
    return ledger_path


def read_tail(file_path: Path, lines: int = 15) -> str:
    if not file_path.exists():
        return ""
    content = file_path.read_text(encoding="utf-8").splitlines()
    return "\n".join(content[-lines:])


def enforce_state_line_limit(
    epic_slug: str,
    role: str,
    decisions: str,
    status: str,
    next_step: str,
    prompt: str,
) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    base_headers = [
        f"# Active Epic: {epic_slug}",
        f"- Role: {role} | Updated: {timestamp}",
        "",
        "## Recent Decisions Locked:",
    ]
    middle_headers = [
        "",
        "## Repo/Task Status:",
        f"- {status}" if status else "- In progress",
        "",
        "## Next Immediate Step:",
        f"- {next_step}" if next_step else "- Continue task execution",
    ]

    dec_lines = [l.strip() for l in decisions.splitlines() if l.strip()]
    if not dec_lines:
        dec_lines = ["- Initialized state snapshot"]

    prompt_lines: list[str] = []
    if prompt:
        prompt_lines = ["", "## Custom Prompt / Notes:"]
        prompt_lines.extend([l.strip() for l in prompt.splitlines() if l.strip()])

    total_lines = base_headers + dec_lines + middle_headers + prompt_lines
    if len(total_lines) <= MAX_STATE_LINES:
        return "\n".join(total_lines)

    # Budget lines to keep total <= MAX_STATE_LINES while preserving all 4 fields
    overhead = len(base_headers) + len(middle_headers)
    remaining_budget = MAX_STATE_LINES - overhead
    if remaining_budget <= 2:
        return "\n".join(base_headers + dec_lines[:1] + middle_headers)

    dec_budget = min(len(dec_lines), max(2, remaining_budget - 3))
    trimmed_dec = dec_lines[:dec_budget]
    lines_so_far = base_headers + trimmed_dec + middle_headers
    room_for_prompt = MAX_STATE_LINES - len(lines_so_far)

    if room_for_prompt >= 2 and prompt_lines:
        trimmed_prompt = prompt_lines[:room_for_prompt]
        return "\n".join(lines_so_far + trimmed_prompt)
    return "\n".join(lines_so_far)


def render_assistant_state_rollup(devtool_dir: Path) -> None:
    state_dir = devtool_dir / "state"
    if not state_dir.exists():
        return
    state_files = sorted(state_dir.glob("*.md"))
    parts: list[str] = []
    for sf in state_files:
        content = sf.read_text(encoding="utf-8").strip()
        if content:
            parts.append(content)
    rollup = devtool_dir / "assistant_state.md"
    if parts:
        _atomic_write_text(rollup, "\n\n---\n\n".join(parts) + "\n")
    elif rollup.exists():
        _atomic_write_text(rollup, "No active epic state.\n")


def refresh_activity_stream_rollup(devtool_dir: Path) -> None:
    logs_dir = devtool_dir / "logs"
    if not logs_dir.exists():
        return
    all_entries: list[str] = []
    for lf in sorted(logs_dir.glob("activity_*.log")):
        lines = [l for l in lf.read_text(encoding="utf-8").splitlines() if l.strip()]
        all_entries.extend(lines)
    all_entries.sort()
    recent = all_entries[-50:]
    rollup = devtool_dir / "activity_stream.log"
    _atomic_write_text(rollup, "\n".join(recent) + ("\n" if recent else ""))


def parse_markdown_gate_row(line_str: str) -> dict[str, object] | None:
    line = line_str.strip()
    if not line.startswith("|") or not line.endswith("|"):
        return None
    if re.match(r"^\|(?:\s*:?-+:?\s*\|)+$", line):
        return None
    inner = line[1:-1]
    raw_cells = re.split(r"(?<!\\)\|", inner)
    if len(raw_cells) < 7:
        return None
    cells = [c.strip().replace(r"\|", "|") for c in raw_cells]
    if cells[0].lower() == "timestamp":
        return None
    try:
        gate_num = int(cells[2])
    except (ValueError, TypeError):
        return None
    return {
        "timestamp": cells[0],
        "epic": cells[1],
        "gate": gate_num,
        "commit": cells[3],
        "approved": cells[4],
        "deviations": cells[5],
        "by": cells[6],
    }


def parse_gate_ledger_markdown(md_path: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    if not md_path.exists():
        return entries
    for line in md_path.read_text(encoding="utf-8").splitlines():
        parsed = parse_markdown_gate_row(line)
        if parsed is not None:
            entries.append(parsed)
    return entries


def hydrate_gate_ledger_jsonl_if_needed(devtool_dir: Path) -> None:
    state_dir = devtool_dir / "state"
    jsonl_path = state_dir / "gate_ledger.jsonl"
    md_path = devtool_dir / "GATE_LEDGER.md"
    if not md_path.exists():
        return
    existing_md_entries = parse_gate_ledger_markdown(md_path)
    if not existing_md_entries:
        return

    jsonl_entries: list[dict[str, object]] = []
    if jsonl_path.exists():
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
                if isinstance(data, dict):
                    jsonl_entries.append(data)
            except Exception:
                continue

    if not jsonl_path.exists() or len(jsonl_entries) < len(existing_md_entries):
        seen = {
            (
                str(e.get("timestamp")),
                str(e.get("epic")),
                str(e.get("gate")),
                str(e.get("commit")),
            )
            for e in jsonl_entries
        }
        missing = [
            e
            for e in existing_md_entries
            if (
                str(e.get("timestamp")),
                str(e.get("epic")),
                str(e.get("gate")),
                str(e.get("commit")),
            )
            not in seen
        ]
        if missing or not jsonl_path.exists():
            state_dir.mkdir(parents=True, exist_ok=True)
            with jsonl_path.open("a", encoding="utf-8") as f:
                for entry in missing:
                    f.write(json.dumps(entry) + "\n")


def render_gate_ledger_markdown(devtool_dir: Path) -> Path:
    hydrate_gate_ledger_jsonl_if_needed(devtool_dir)
    state_dir = devtool_dir / "state"
    jsonl_path = state_dir / "gate_ledger.jsonl"
    md_path = devtool_dir / "GATE_LEDGER.md"

    entries: list[dict[str, object]] = []
    if jsonl_path.exists():
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
                if isinstance(data, dict):
                    entries.append(data)
            except Exception:
                continue

    lines = [
        "# Gate Approval Ledger (Permanent)",
        "",
        "| Timestamp | Epic | Gate | Commit | Approved Scope | Deviations | By |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in entries:
        ts = str(e.get("timestamp", "")).replace("|", r"\|")
        ep = str(e.get("epic", "")).replace("|", r"\|")
        gt = str(e.get("gate", "")).replace("|", r"\|")
        cm = str(e.get("commit", "")).replace("|", r"\|")
        ap = str(e.get("approved", "")).replace("|", r"\|")
        dev = str(e.get("deviations", "")).replace("|", r"\|")
        by_user = str(e.get("by", "")).replace("|", r"\|")
        lines.append(f"| {ts} | {ep} | {gt} | {cm} | {ap} | {dev} | {by_user} |")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def resolve_target_devtool_dir(root: Path, repo: str | None = None) -> Path:
    if not repo or repo == "workspace" or root.name == repo:
        return root / ".devtool"
    candidate = root / repo
    if (candidate / ".git").exists() or (candidate / ".devtool").exists():
        return candidate / ".devtool"
    sibling = root.parent / repo
    if root.name in REPOS and (
        (sibling / ".git").exists() or (sibling / ".devtool").exists()
    ):
        return sibling / ".devtool"
    if not (root / ".git").exists():
        return candidate / ".devtool"
    return root / ".devtool"


def _profile_folder_from_path(path_value: str | Path) -> str:
    parts = Path(path_value).expanduser().parts
    for idx, part in enumerate(parts):
        if part == "antigravity_homes" and idx + 1 < len(parts):
            candidate = parts[idx + 1].strip().lstrip("@")
            if candidate and candidate not in (".", ".."):
                return candidate
    return ""


def detect_current_profile(
    root: Path | None = None,
    *,
    real_home: str | Path | None = None,
) -> str:
    """Resolve active profile identifier prioritizing env and folder names before email or fallback."""
    env_profile = (
        os.environ.get("AGY_PROFILE", "")
        or os.environ.get("ANTIGRAVITY_PROFILE", "")
    ).strip().lstrip("@")
    if env_profile:
        return env_profile

    home_str = os.environ.get("HOME", "")
    folder_profile = _profile_folder_from_path(home_str) if home_str else ""
    if folder_profile:
        return folder_profile

    target_root = root.resolve() if root is not None else None
    if target_root is not None:
        try:
            ps_out = subprocess.check_output(["ps", "-eo", "command"], text=True)
            for line in ps_out.splitlines():
                if (
                    ("agy" in line or "Antigravity IDE" in line)
                    and "antigravity_homes" in line
                    and (
                        f"--add-dir={target_root}" in line
                        or str(target_root) in line
                    )
                ):
                    m = re.search(r"antigravity_homes/([^/\s]+)", line)
                    if m:
                        return m.group(1).strip().lstrip("@")
        except Exception:  # noqa: S110
            pass

    base_home = Path(real_home).expanduser() if real_home else Path(os.path.expanduser("~"))
    homes_dir = (
        base_home
        if base_home.parent.name == "antigravity_homes"
        else base_home / "antigravity_homes"
    )
    if homes_dir.name == "antigravity_homes" and homes_dir.is_dir() and target_root is not None:
        try:
            target_uri = f"file://{target_root}"
            matching: list[tuple[float, Path]] = []
            for h in sorted(homes_dir.iterdir()):
                if not h.is_dir():
                    continue
                ws_storage = h / "data" / "User" / "workspaceStorage"
                if not ws_storage.is_dir():
                    continue
                entries = sorted(
                    ws_storage.iterdir(),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True,
                )
                for ws_entry in entries:
                    ws_json = ws_entry / "workspace.json"
                    if ws_json.is_file():
                        try:
                            ws_data = json.loads(ws_json.read_text(encoding="utf-8"))
                            if ws_data.get("folder") == target_uri:
                                matching.append((ws_entry.stat().st_mtime, h))
                                break
                        except Exception:  # noqa: S110
                            pass
            if matching:
                matching.sort(key=lambda x: x[0], reverse=True)
                return matching[0][1].name
        except Exception:  # noqa: S110
            pass

    if target_root is not None:
        settings_file = target_root / ".vscode" / "settings.json"
        if settings_file.is_file():
            try:
                s_data = json.loads(settings_file.read_text(encoding="utf-8"))
                title_val = s_data.get("window.title", "")
                if isinstance(title_val, str):
                    m_existing = re.search(r"\[@([a-zA-Z0-9_\-\.]+)\]", title_val)
                    if m_existing:
                        return m_existing.group(1)
            except Exception:  # noqa: S110
                pass

    if home_str and (Path(home_str) / "data").is_dir():
        email_id = extract_email_id_from_profile(Path(home_str))
        if email_id:
            return email_id

    return os.environ.get("USER", "").strip()


def extract_email_id_from_profile(profile_dir: Path) -> str | None:
    db_path = profile_dir / "data" / "User" / "globalStorage" / "state.vscdb"
    if not db_path.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value FROM ItemTable WHERE key = 'google.google-antigravity'"
        )
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            data = json.loads(row[0])
            storage = data.get("antigravity-storage", {})
            username = storage.get("agy.onboarding.lastLoginUsername")
            if username:
                return username.split("@")[0] if "@" in username else username
    except Exception:  # noqa: S110
        pass
    return None


def sync_window_title(
    root: Path,
    epic_slug: str | None = None,
    stage_override: str | None = None,
    profile_override: str | None = None,
) -> None:
    vscode_dir = root / ".vscode"
    settings_file = vscode_dir / "settings.json"
    vscode_dir.mkdir(parents=True, exist_ok=True)

    primary_for_root = resolve_primary_repo_root(root)
    if not settings_file.exists():
        primary_settings = primary_for_root / ".vscode" / "settings.json"
        if primary_for_root != root and primary_settings.exists():
            try:
                settings_file.write_text(
                    primary_settings.read_text(encoding="utf-8"), encoding="utf-8"
                )
            except Exception:
                settings_file.write_text("{}\n", encoding="utf-8")
        else:
            settings_file.write_text("{}\n", encoding="utf-8")

    REPO_SIGNATURES = {
        "lyrics-sync": ("🔴", "LYRICS-SYNC", "#7f1d1d"),
        "D3Nexus": ("🟢", "D3NEXUS", "#065f46"),
        "nexus": ("🔵", "NEXUS", "#0d47a1"),
        "ai-agent-tools": ("🟠", "AGENT-TOOLS", "#b45309"),
    }
    repo_name = (
        primary_for_root.name
        if primary_for_root.name in REPO_SIGNATURES
        else root.name
    )
    icon, tag, theme_color = REPO_SIGNATURES.get(
        repo_name, ("📁", repo_name.upper(), None)
    )

    account_id = (profile_override or "").strip().lstrip("@")

    epic_slug = epic_slug or resolve_current_epic_slug(root)

    # 1. Active Epic PIC / Profile metadata is authoritative SSOT (normalizing -/_)
    epic_docs = _load_epic_docs()
    if not account_id and epic_slug and epic_slug != "general":
        slug_variants = list(
            dict.fromkeys(
                [epic_slug, epic_slug.replace("-", "_"), epic_slug.replace("_", "-")]
            )
        )
        epic_candidates: list[Path] = []
        for variant in slug_variants:
            for base_r in (root, primary_for_root):
                ep_dir = base_r / ".devtool" / "epic" / variant
                if not ep_dir.is_dir():
                    continue
                for stem in ("handoff", variant):
                    resolved_doc = epic_docs.resolve_epic_doc(ep_dir, stem)
                    if resolved_doc is not None and not resolved_doc.name.endswith(".vi.md"):
                        epic_candidates.append(resolved_doc)
        for cand_f in epic_candidates:
            if cand_f.is_file():
                try:
                    m = re.search(
                        r"-\s+\*\*(?:PIC(?:\s*/\s*Assigned\s+Profile)?|Profile|Assigned Profile)\*\*:\s*`?@?([a-zA-Z0-9_.\-]+)`?",
                        cand_f.read_text(encoding="utf-8"),
                        re.IGNORECASE,
                    )
                    if m:
                        cand_id = m.group(1).strip().lstrip("@")
                        if cand_id and cand_id != "profile_account_id":
                            account_id = cand_id
                            break
                except Exception:  # noqa: S110
                    pass

    if not account_id:
        account_id = detect_current_profile(root, real_home=_real_home())

    if not account_id:
        account_id = os.environ.get("USER", "")

    profile_tag = f"[@{account_id}]" if account_id else ""

    epic_title = ""
    stage_text = stage_override or ""
    if epic_slug and epic_slug != "general":
        devtool_dir = root / ".devtool"
        if not devtool_dir.exists():
            primary = resolve_primary_repo_root(root)
            devtool_dir = primary / ".devtool"
        epic_dir = devtool_dir / "epic" / epic_slug
        if not epic_dir.exists():
            epic_dir = devtool_dir / "epic" / epic_slug.replace("-", "_")
        if not epic_dir.exists():
            epic_dir = devtool_dir / "epic" / epic_slug.replace("_", "-")
        if epic_dir.exists():
            title_docs: list[Path] = []
            for stem in dict.fromkeys(
                [
                    epic_dir.name,
                    epic_slug,
                    epic_slug.replace("-", "_"),
                    epic_slug.replace("_", "-"),
                ]
            ):
                resolved_doc = epic_docs.resolve_epic_doc(epic_dir, stem)
                if resolved_doc is not None and resolved_doc not in title_docs:
                    title_docs.append(resolved_doc)
            for spec_doc in epic_docs.resolve_design_specs(epic_dir):
                if spec_doc not in title_docs:
                    title_docs.append(spec_doc)
            for doc_file in title_docs:
                if doc_file.name.endswith(".vi.md"):
                    continue
                try:
                    for line in doc_file.read_text(encoding="utf-8").splitlines():
                        if line.startswith("# "):
                            raw = line.lstrip("#").strip()
                            if raw.lower().startswith("epic:"):
                                raw = raw[5:].strip()
                            epic_title = raw
                            break
                    if epic_title:
                        break
                except Exception:  # noqa: S110
                    pass

        if not stage_text:
            state_file = devtool_dir / "state" / f"{epic_slug}.md"
            if state_file.exists():
                try:
                    lines = state_file.read_text(encoding="utf-8").splitlines()
                    for i, l in enumerate(lines):
                        if "## Repo/Task Status:" in l and i + 1 < len(lines):
                            stage_text = lines[i + 1].lstrip("- ").strip()
                            break
                except Exception:  # noqa: S110
                    pass

    parts = [p for p in [icon, f"[{tag}]", profile_tag] if p]
    prefix = " ".join(parts)
    if epic_title:
        title_str = f"{prefix} {epic_title}"
        if stage_text:
            title_str += f" - {stage_text}"
    elif stage_text:
        title_str = f"{prefix} {stage_text}"
    else:
        title_str = f"{prefix} ${{activeEditorMedium}}${{separator}}${{rootName}}"

    try:
        content = settings_file.read_text(encoding="utf-8")
        settings = json.loads(content)
        dirty = False
        if settings.get("window.title") != title_str:
            settings["window.title"] = title_str
            dirty = True

        if theme_color:
            if "workbench.colorCustomizations" not in settings:
                settings["workbench.colorCustomizations"] = {}
                dirty = True
            colors = settings["workbench.colorCustomizations"]
            color_keys = {
                "titleBar.activeBackground": theme_color,
                "titleBar.inactiveBackground": theme_color,
                "statusBar.background": theme_color,
                "statusBar.inactiveBackground": theme_color,
                "titleBar.activeForeground": "#ffffff",
                "titleBar.inactiveForeground": "#ffffffcc",
                "statusBar.foreground": "#ffffff",
                "statusBar.inactiveForeground": "#ffffffcc",
            }
            for k, v in color_keys.items():
                if colors.get(k) != v:
                    colors[k] = v
                    dirty = True
        else:
            colors = settings.get("workbench.colorCustomizations")
            if isinstance(colors, dict):
                # Enforce inactive background parity for titleBar and statusBar
                title_active = colors.get("titleBar.activeBackground")
                if (
                    title_active
                    and colors.get("titleBar.inactiveBackground") != title_active
                ):
                    colors["titleBar.inactiveBackground"] = title_active
                    dirty = True
                status_active = colors.get("statusBar.background")
                if (
                    status_active
                    and colors.get("statusBar.inactiveBackground") != status_active
                ):
                    colors["statusBar.inactiveBackground"] = status_active
                    dirty = True

        if dirty:
            settings_file.write_text(
                json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
    except Exception:  # noqa: S110
        pass


def _matching_epic_worktrees(root: Path, epic_slug: str) -> list[Path]:
    """Return linked non-slot worktrees matching `epic_slug` or active worktree."""
    matches: list[Path] = []
    seen: set[Path] = set()
    root_resolved = root.resolve()

    def _consider(candidate: Path) -> None:
        resolved = candidate.resolve()
        if resolved != root_resolved and resolved not in seen and candidate.is_dir():
            seen.add(resolved)
            matches.append(candidate)

    current_wt = resolve_current_worktree_root()
    if (
        current_wt.resolve() != root_resolved
        and resolve_primary_repo_root(current_wt).resolve() == root_resolved
    ):
        _consider(current_wt)

    for wt_cand in (
        root / ".worktrees" / epic_slug,
        root / ".worktrees" / epic_slug.replace("-", "_"),
        root / ".worktrees" / epic_slug.replace("_", "-"),
    ):
        _consider(wt_cand)

    try:
        wt_res = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if wt_res.returncode == 0 and wt_res.stdout:
            target_branch = f"refs/heads/epic/{epic_slug}"
            for wt_path, branch in _state_envelope._parse_worktree_branches(wt_res.stdout):
                if branch == target_branch and not _state_envelope._is_slot_worktree(wt_path):
                    _consider(wt_path)
    except OSError:
        pass
    return matches


def _safe_archive_move(src: Path, archive_dir: Path, stem: str, suffix: str) -> None:
    """Move `src` into `archive_dir` without colliding on existing archive filenames."""
    if not src.exists():
        return
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / f"{stem}{suffix}"
    counter = 1
    while dest.exists():
        dest = archive_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    src.rename(dest)


def _is_paused_status(status: str) -> bool:
    lowered = status.strip().lower()
    if not lowered:
        return False
    paused_markers = (
        "waiting",
        "paused",
        "pending",
        "halt",
        "blocked",
        "choice a",
        "human action",
        "circuit breaker",
        "awaiting",
    )
    if any(marker in lowered for marker in paused_markers):
        return True
    return bool(re.search(r"\bgate\s*[125]\b.*(?:approval|review|sign)", lowered))


def _read_existing_epic_state_fields(
    devtool_dir: Path, epic_slug: str
) -> tuple[str, str, str, str, str]:
    """Read `(role, decisions, status, next_step, prompt)` from existing epic state file."""
    state_file = devtool_dir / "state" / f"{epic_slug}.md"
    if not state_file.is_file():
        return ("", "", "", "", "")
    role = ""
    section = ""
    sections: dict[str, list[str]] = {
        "decisions": [],
        "status": [],
        "next_step": [],
        "prompt": [],
    }
    for raw_line in state_file.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = raw_line.strip()
        role_match = re.match(r"^-\s*Role:\s*([^|\n]+)", stripped)
        if role_match:
            role = normalize_role(role_match.group(1).strip())
            continue
        if stripped.startswith("## Recent Decisions Locked"):
            section = "decisions"
            continue
        if stripped.startswith("## Repo/Task Status"):
            section = "status"
            continue
        if stripped.startswith("## Next Immediate Step"):
            section = "next_step"
            continue
        if stripped.startswith("## Custom Prompt / Notes"):
            section = "prompt"
            continue
        if stripped.startswith("## "):
            section = ""
            continue
        if section and stripped:
            sections[section].append(stripped)
    decisions = "\n".join(sections["decisions"])
    status = " ".join(ln.lstrip("- ").strip() for ln in sections["status"]).strip()
    next_step = " ".join(ln.lstrip("- ").strip() for ln in sections["next_step"]).strip()
    prompt = "\n".join(sections["prompt"])
    return (role, decisions, status, next_step, prompt)


def write_epic_state(
    root: Path,
    epic_slug: str,
    decisions: str = "",
    status: str = "",
    next_step: str = "",
    prompt: str = "",
    role: str = "programmer",
    repo: str | None = None,
    *,
    refresh_heartbeat: bool = True,
    clear_pending: bool = True,
    sync_title: bool = True,
    mirror_roots: Sequence[Path] | None = None,
    active_wave: int | None = None,
) -> None:
    norm_role = normalize_role(role)
    devtool_dir = resolve_target_devtool_dir(root, repo)
    primary_root = (
        resolve_primary_repo_root(devtool_dir.parent)
        if repo is None and (devtool_dir.parent / ".git").exists()
        else devtool_dir.parent
    )

    target_devtool_dirs: list[Path] = []
    seen_dirs: set[Path] = set()

    def _add_devtool_dir(candidate: Path) -> None:
        resolved = candidate.resolve()
        if resolved not in seen_dirs:
            seen_dirs.add(resolved)
            target_devtool_dirs.append(resolved)

    _add_devtool_dir(devtool_dir)
    matching_wts: list[Path] = []
    if mirror_roots is not None:
        for mr in mirror_roots:
            _add_devtool_dir(mr if mr.name == ".devtool" else mr / ".devtool")
    elif repo is None:
        if primary_root.resolve() != devtool_dir.parent.resolve() and (
            primary_root / ".devtool"
        ).is_dir():
            _add_devtool_dir(primary_root / ".devtool")
        matching_wts = _matching_epic_worktrees(primary_root, epic_slug)
        for wt in matching_wts:
            if (wt / ".devtool").is_dir():
                _add_devtool_dir(wt / ".devtool")

    content = enforce_state_line_limit(
        epic_slug, norm_role, decisions, status, next_step, prompt
    )
    canonical_lock_dt = (primary_root / ".devtool").resolve()
    with _state_envelope._state_lock(canonical_lock_dt):
        for target_dt in target_devtool_dirs:
            with file_lock(target_dt):
                migrate_legacy_storage(target_dt)
                state_dir = target_dt / "state"
                state_dir.mkdir(parents=True, exist_ok=True)
                _atomic_write_text(state_dir / f"{epic_slug}.md", content + "\n")
                render_assistant_state_rollup(target_dt)

        if refresh_heartbeat:
            _state_envelope.update_epic_heartbeat(
                primary_root,
                epic_slug,
                stage=status if status else None,
                active_wave=active_wave,
                last_event=next_step or status or "resume_context --state",
                extra_devtool_dirs=target_devtool_dirs,
            )

        if clear_pending and status.strip() and not _is_paused_status(status):
            _state_envelope.clear_pending_decision(
                primary_root,
                epic_slug,
                extra_devtool_dirs=target_devtool_dirs,
            )

    if sync_title:
        sync_window_title(root, epic_slug=epic_slug, stage_override=status)
        if not matching_wts:
            matching_wts = _matching_epic_worktrees(root, epic_slug)
        for wt_cand in matching_wts:
            sync_window_title(wt_cand, epic_slug=epic_slug, stage_override=status)


def append_activity_log(
    root: Path,
    epic_slug: str,
    repo: str,
    task_id: str,
    request: str,
    action: str,
    note: str = "None",
) -> None:
    devtool_dir = resolve_target_devtool_dir(root, repo)
    with file_lock(devtool_dir):
        migrate_legacy_storage(devtool_dir)
        logs_dir = devtool_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        line = f"[{timestamp}] [{repo}/{epic_slug}/{task_id}] Request: {request} | Action: {action} | Note: {note}\n"
        with (logs_dir / f"activity_{epic_slug}.log").open("a", encoding="utf-8") as f:
            f.write(line)
        refresh_activity_stream_rollup(devtool_dir)


def _epic_slug_variants(epic_slug: str) -> list[str]:
    """Return deduplicated hyphen/underscore variants of `epic_slug` and its safe slug."""
    safe_slug = _state_envelope._sanitize_epic_slug(epic_slug)
    candidates = (
        safe_slug,
        epic_slug,
        safe_slug.replace("_", "-"),
        safe_slug.replace("-", "_"),
        epic_slug.replace("_", "-"),
        epic_slug.replace("-", "_"),
    )
    variants: list[str] = []
    seen: set[str] = set()
    for cand in candidates:
        cleaned = cand.strip()
        if (
            not cleaned
            or cleaned in {".", ".."}
            or Path(cleaned).name != cleaned
            or cleaned in seen
        ):
            continue
        seen.add(cleaned)
        variants.append(cleaned)
    return variants


def complete_feature_and_rotate(
    root: Path,
    epic_slug: str,
    summary: str,
    repo: str | None = None,
    checkpoint: bool = False,
) -> None:
    if checkpoint:
        write_epic_state(
            root,
            epic_slug,
            status="Checkpoint saved",
            next_step="Resume development",
            prompt=summary,
            repo=repo,
        )
        append_activity_log(
            root,
            epic_slug,
            repo or "workspace",
            "checkpoint",
            summary,
            "Saved context checkpoint",
            note="None",
        )
        return

    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    milestone = f"- **[{today}] `{epic_slug}`**: {summary}\n"

    primary_root = (
        resolve_primary_repo_root(root)
        if repo is None and (root / ".git").exists()
        else root
    )
    with _state_envelope._state_lock((primary_root / ".devtool").resolve()):
        ledger_path = ensure_ledger(primary_root)
        dup_pattern = re.compile(
            rf"^\s*-\s+\*\*\[[^\]]+\]\s+`{re.escape(epic_slug)}`\*\*:",
            re.MULTILINE,
        )
        with file_lock(ledger_path.parent):
            existing_ledger = ledger_path.read_text(encoding="utf-8")
            if dup_pattern.search(existing_ledger):
                print(
                    f"ℹ️ Milestone for `{epic_slug}` already exists in {ledger_path.relative_to(primary_root)}; skipped duplicate entry."
                )
            else:
                with ledger_path.open("a", encoding="utf-8") as f:
                    f.write(milestone)
                print(
                    f"✅ Appended milestone to {ledger_path.relative_to(primary_root)}:\n   {milestone.strip()}"
                )

        slug_variants = _epic_slug_variants(epic_slug)
        raw_candidates: list[Path] = (
            [root / ".devtool", primary_root / ".devtool"]
            + [root / r / ".devtool" for r in REPOS]
            + [wt / ".devtool" for wt in _matching_epic_worktrees(primary_root, epic_slug)]
        )
        if (primary_root / ".git").exists():
            wt_out = _state_envelope._run_git(primary_root, "worktree", "list", "--porcelain")
            if wt_out:
                for wt_path, _branch in _state_envelope._parse_worktree_branches(wt_out):
                    if _state_envelope._is_slot_worktree(wt_path):
                        continue
                    wt_dt = wt_path / ".devtool"
                    if any(
                        (wt_dt / "state" / f"{variant}.md").exists()
                        or (wt_dt / "state" / f"{variant}.heartbeat.json").exists()
                        or (wt_dt / "logs" / f"events_{variant}.jsonl").exists()
                        for variant in slug_variants
                    ):
                        raw_candidates.append(wt_dt)

        deduped_dirs: list[Path] = []
        seen_dt: set[Path] = set()
        for cand in raw_candidates:
            if not cand.exists():
                continue
            resolved = cand.resolve()
            if resolved not in seen_dt:
                seen_dt.add(resolved)
                deduped_dirs.append(resolved)

        for devtool_dir in deduped_dirs:
            with file_lock(devtool_dir):
                archive_dir = devtool_dir / "archive"
                for variant in slug_variants:
                    _safe_archive_move(
                        devtool_dir / "state" / f"{variant}.md",
                        archive_dir,
                        f"state_{variant}_{timestamp}",
                        ".md",
                    )
                    _safe_archive_move(
                        devtool_dir / "state" / f"{variant}.heartbeat.json",
                        archive_dir,
                        f"heartbeat_{variant}_{timestamp}",
                        ".json",
                    )
                    _safe_archive_move(
                        devtool_dir / "logs" / f"activity_{variant}.log",
                        archive_dir,
                        f"activity_{variant}_{timestamp}",
                        ".log",
                    )
                    _safe_archive_move(
                        devtool_dir / "logs" / f"events_{variant}.jsonl",
                        archive_dir,
                        f"events_{variant}_{timestamp}",
                        ".jsonl",
                    )
                render_assistant_state_rollup(devtool_dir)
                refresh_activity_stream_rollup(devtool_dir)

        _state_envelope.clear_pending_decision(
            primary_root,
            epic_slug,
            extra_devtool_dirs=deduped_dirs,
        )
    sync_window_title(primary_root, epic_slug=epic_slug, stage_override="Completed")
    if root.resolve() != primary_root.resolve():
        sync_window_title(root, epic_slug=epic_slug, stage_override="Completed")


def record_gate_approval(
    root: Path,
    epic_slug: str,
    gate: int,
    approved: str,
    *,
    deviations: str = "",
    by: str = "developer",
    repo: str | None = None,
) -> dict[str, object]:
    devtool_dir = resolve_target_devtool_dir(root, repo)
    with file_lock(devtool_dir):
        hydrate_gate_ledger_jsonl_if_needed(devtool_dir)
        state_dir = devtool_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        commit_sha = (
            res.stdout.strip()
            if res.returncode == 0 and res.stdout.strip()
            else "unknown"
        )
        now_utc = datetime.now(timezone.utc).isoformat()
        entry: dict[str, object] = {
            "timestamp": now_utc,
            "epic": epic_slug,
            "gate": gate,
            "commit": commit_sha,
            "approved": approved,
            "deviations": deviations,
            "by": by,
        }
        jsonl_path = state_dir / "gate_ledger.jsonl"
        with jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        render_gate_ledger_markdown(devtool_dir)
        shared_dt = list(dict.fromkeys([devtool_dir, *_state_envelope.resolve_shared_devtool_dirs(root)]))
        _state_envelope.clear_pending_decision(
            root,
            epic_slug,
            extra_devtool_dirs=shared_dt,
        )
        with contextlib.suppress(Exception):
            _state_envelope.update_epic_heartbeat(
                root,
                epic_slug,
                sub_step=f"gate_{gate}",
                sub_step_detail=f"Gate {gate} Approved ({commit_sha})",
                last_event=f"Gate {gate} approved: {approved}",
                extra_devtool_dirs=shared_dt,
            )
        return entry


def scan_gate_ledger(
    root: Path, epic_slug: str | None = None
) -> list[dict[str, object]]:
    devtool_dir = root if root.name == ".devtool" else root / ".devtool"
    hydrate_gate_ledger_jsonl_if_needed(devtool_dir)
    jsonl_path = devtool_dir / "state" / "gate_ledger.jsonl"
    md_path = devtool_dir / "GATE_LEDGER.md"
    entries: list[dict[str, object]] = []

    if jsonl_path.exists():
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
                if isinstance(data, dict):
                    entries.append(data)
            except Exception:
                continue
    elif md_path.exists():
        entries = parse_gate_ledger_markdown(md_path)

    if epic_slug:
        norm_filter = epic_slug.replace("_", "-")
        return [
            e
            for e in entries
            if str(e.get("epic", "")) == epic_slug
            or str(e.get("epic", "")).replace("_", "-") == norm_filter
        ]

    return entries


def check_gate_approval(
    root: Path,
    epic_slug: str,
    gate: int,
    *,
    repo: str | None = None,
) -> dict[str, object] | None:
    devtool_dir = resolve_target_devtool_dir(root, repo)
    entries = scan_gate_ledger(devtool_dir, epic_slug=epic_slug)
    matching = [e for e in entries if e.get("gate") == gate]
    return matching[-1] if matching else None


def scan_project_ledger(root: Path) -> None:
    print_section("0. PROJECT ARCHITECTURAL LEDGER (.devtool/PROJECT_LEDGER.md)")
    ledger_path = ensure_ledger(root)
    print(ledger_path.read_text(encoding="utf-8").strip())


def scan_assistant_state(root: Path) -> None:
    print_section("1. ACTIVE EPIC STATE (.devtool/assistant_state.md)")
    candidates = [root / ".devtool"] + [root / r / ".devtool" for r in REPOS]
    found = False
    for d_dir in candidates:
        if not d_dir.exists():
            continue
        migrate_legacy_storage(d_dir)
        state_dir = d_dir / "state"
        if state_dir.exists():
            for sf in sorted(state_dir.glob("*.md")):
                text = sf.read_text(encoding="utf-8").strip()
                if text:
                    rel = sf.relative_to(root)
                    print(f"[{rel}]\n{text}\n")
                    found = True
        elif (d_dir / "assistant_state.md").exists():
            text = (d_dir / "assistant_state.md").read_text(encoding="utf-8").strip()
            if text:
                print(f"[{d_dir.relative_to(root)}/assistant_state.md]\n{text}\n")
                found = True
    if not found:
        print("  (No active assistant_state.md found yet.)")


def _collect_epic_checkpoints(root: Path) -> list[tuple[str, dict[str, Any]]]:
    """Collect latest non-empty checkpoint blocks keyed by epic across devtool candidates."""
    candidates = [root / ".devtool"] + [root / r / ".devtool" for r in REPOS]
    best_by_epic: dict[str, tuple[int, str, dict[str, Any]]] = {}
    seen_dirs: set[Path] = set()
    for d_dir in candidates:
        if not d_dir.exists():
            continue
        resolved_dir = d_dir.resolve()
        if resolved_dir in seen_dirs:
            continue
        seen_dirs.add(resolved_dir)
        state_dir = d_dir / "state"
        if not state_dir.is_dir():
            continue
        for hb_path in sorted(state_dir.glob("*.heartbeat.json")):
            empty_hb: dict[str, Any] = {}
            hb = _state_envelope.read_json_safe(hb_path, empty_hb)
            if not hb:
                continue
            cp = hb.get("checkpoint")
            if not isinstance(cp, dict) or not cp.get("event"):
                continue
            epic_name = str(
                hb.get("epic_slug") or hb_path.stem.removesuffix(".heartbeat")
            )
            gen = _state_envelope._safe_int(hb.get("generation"), 0)
            norm_key = _normalize_epic(epic_name)
            prev = best_by_epic.get(norm_key)
            if prev is None or gen >= prev[0]:
                best_by_epic[norm_key] = (gen, epic_name, cp)
    return [(epic_name, cp) for _, epic_name, cp in best_by_epic.values()]


def scan_epic_checkpoints(root: Path) -> None:
    """Print the latest checkpoint block for each active epic before the activity stream."""
    checkpoints = _collect_epic_checkpoints(root)
    if not checkpoints:
        return
    print_section("1.6. LATEST CHECKPOINTS (.devtool/state/*.heartbeat.json)")
    for epic_name, cp in checkpoints:
        parts = [f"event={cp.get('event', '')}"]
        if cp.get("persona"):
            parts.append(f"persona={cp['persona']}")
        if cp.get("wave") is not None:
            parts.append(f"wave={cp['wave']}")
        if cp.get("head_sha"):
            parts.append(f"sha={str(cp['head_sha'])[:8]}")
        if cp.get("next_step"):
            parts.append(f"next={cp['next_step']}")
        parts.append(f"turns={cp.get('turns_since_checkpoint', 0)}")
        parts.append(f"low_quota={bool(cp.get('low_quota', False))}")
        if cp.get("at"):
            parts.append(f"at={cp['at']}")
        if cp.get("warning"):
            parts.append(f"warning={cp['warning']}")
        print(f"  - [{epic_name}] " + " | ".join(parts))


def scan_activity_stream(root: Path, tail_lines: int = 15) -> None:
    print_section("2. RECENT PROGRAMMER ACTIVITY (.devtool/activity_stream.log)")
    candidates = [root / ".devtool"] + [root / r / ".devtool" for r in REPOS]
    found = False
    for d_dir in candidates:
        if not d_dir.exists():
            continue
        migrate_legacy_storage(d_dir)
        logs_dir = d_dir / "logs"
        if logs_dir.exists():
            for lf in sorted(logs_dir.glob("activity_*.log")):
                text = read_tail(lf, tail_lines).strip()
                if text:
                    print(
                        f"[{lf.relative_to(root)} - Last {tail_lines} entries]\n{text}\n"
                    )
                    found = True
        elif (d_dir / "activity_stream.log").exists():
            text = read_tail(d_dir / "activity_stream.log", tail_lines).strip()
            if text:
                print(
                    f"[{d_dir.relative_to(root)}/activity_stream.log - Last {tail_lines} entries]\n{text}\n"
                )
                found = True
    if not found:
        print("  (No activity_stream.log entries found yet.)")


def scan_git_status(root: Path) -> None:
    print_section("3. GIT WORKING TREE STATUS ACROSS REPOS")
    ws_base = root.parent if root.name in REPOS else root
    target_repos = (
        [ws_base / r for r in REPOS]
        if ws_base != root or not (root / ".git").exists()
        else [root]
    )
    for repo_path in target_repos:
        if not (repo_path / ".git").exists():
            continue
        res = subprocess.run(
            ["git", "-C", str(repo_path), "status", "-s", "-b"],
            capture_output=True,
            text=True,
            check=False,
        )
        print(f"🔹 {repo_path.name}:\n{res.stdout.strip()}\n")


def scan_open_rfcs(root: Path) -> None:
    print_section("4. OPEN CONTRACT GAPS & RFCS (shared-contracts/*/gaps_and_rfcs.md)")
    ws_base = root.parent if root.name in REPOS else root
    hub_contracts = ws_base / "D3Nexus" / "shared-contracts"
    if not hub_contracts.exists():
        print("  (D3Nexus/shared-contracts not initialized yet.)")
        return
    for rfc_file in sorted(hub_contracts.glob("*/gaps_and_rfcs.md")):
        lines = rfc_file.read_text(encoding="utf-8").splitlines()
        open_items = [
            line for line in lines if "OPEN" in line or line.startswith(("## ", "### "))
        ]
        if open_items:
            print(f"📄 {rfc_file.relative_to(ws_base)}:")
            for item in open_items[-10:]:
                print(f"  {item}")


def scan_active_tasks(root: Path, epic_filter: str | None = None) -> None:
    print_section("5. ACTIVE TASKS (.devtool/features/task_*.md)")
    ws_base = root.parent if root.name in REPOS else root
    candidates = [root] + [ws_base / r for r in REPOS]
    found = False
    seen_dirs: set[Path] = set()

    for r_path in candidates:
        if r_path in seen_dirs:
            continue
        seen_dirs.add(r_path)
        features_dir = r_path / ".devtool" / "features"
        if not features_dir.exists():
            continue

        repo_name = r_path.name
        active_tasks: list[tuple[str, str, str]] = []
        done_count = 0
        total_count = 0

        epic_docs = _load_epic_docs()
        for tf in epic_docs.iter_task_files(features_dir):
            lines = tf.read_text(encoding="utf-8").splitlines()[:15]
            if epic_filter:
                epic_line = next((l for l in lines if l.startswith("epic:")), "")
                normalized_filter = epic_filter.replace("_", "-")
                normalized_epic_line = epic_line.replace("_", "-")
                if normalized_filter not in normalized_epic_line:
                    continue
            status_line = next(
                (l for l in lines if "status:" in l.lower()), "status: unknown"
            )
            st_val = (
                status_line.replace("status:", "").strip().strip('"').strip("'").lower()
            )
            if st_val == "done":
                done_count += 1
                total_count += 1
            elif any(
                s in st_val
                for s in ["todo", "in-progress", "in_progress", "review", "backlog"]
            ):
                total_count += 1
                title_line = next((l for l in lines if l.startswith("# ")), tf.name)
                active_tasks.append((tf.name, status_line.strip(), title_line.strip()))

        done_dir = features_dir / "done"
        if done_dir.exists():
            for tf in epic_docs.iter_task_files(done_dir):
                lines = tf.read_text(encoding="utf-8").splitlines()[:15]
                if epic_filter:
                    epic_line = next((l for l in lines if l.startswith("epic:")), "")
                    normalized_filter = epic_filter.replace("_", "-")
                    normalized_epic_line = epic_line.replace("_", "-")
                    if normalized_filter not in normalized_epic_line:
                        continue
                done_count += 1
                total_count += 1

        if total_count > 0:
            print(f"📊 [{repo_name} (base branch)] Progress: {done_count}/{total_count} done")
            for t_name, t_status, t_title in active_tasks:
                print(f"  [{repo_name}] {t_name} ({t_status}) -> {t_title}")
                found = True
        elif active_tasks:
            for t_name, t_status, t_title in active_tasks:
                print(f"  [{repo_name}] {t_name} ({t_status}) -> {t_title}")
                found = True

        worktrees_dir = r_path / ".worktrees"
        if worktrees_dir.is_dir():
            for wt_dir in sorted(worktrees_dir.iterdir()):
                wt_features = wt_dir / ".devtool" / "features"
                if not wt_dir.is_dir() or not wt_features.is_dir():
                    continue
                wt_done = (
                    len(epic_docs.iter_task_files(wt_features / "done"))
                    if (wt_features / "done").is_dir()
                    else 0
                )
                wt_todo = 0
                for tf in epic_docs.iter_task_files(wt_features):
                    lines = tf.read_text(encoding="utf-8").splitlines()[:15]
                    st_line = next((l for l in lines if "status:" in l.lower()), "")
                    st_val = st_line.replace("status:", "").strip().strip('"').strip("'").lower()
                    if st_val == "done":
                        wt_done += 1
                    else:
                        wt_todo += 1
                wt_total = wt_done + wt_todo
                dirty_res = subprocess.run(
                    ["git", "-C", str(wt_dir), "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                dirty_lines = [l for l in dirty_res.stdout.splitlines() if l.strip()]
                dirty_tag = f", uncommitted dirty: {len(dirty_lines)} files" if dirty_lines else ", clean worktree"
                if wt_total > 0 or dirty_lines:
                    print(
                        f"🌿 [{repo_name} worktree:{wt_dir.name}] Branch progress: {wt_done}/{wt_total} done{dirty_tag}"
                    )
                    found = True

    if not found:
        print("  (No active todo/in-progress/review tasks found.)")


def collect_harvest_data(
    root: Path, tail_lines: int = 15, epic_filter: str | None = None
) -> dict[str, object]:
    ledger_path = ensure_ledger(root)
    ledger_text = (
        ledger_path.read_text(encoding="utf-8").strip() if ledger_path.exists() else ""
    )

    candidates = [root / ".devtool"] + [root / r / ".devtool" for r in REPOS]
    state_map: dict[str, str] = {}
    for d_dir in candidates:
        if not d_dir.exists():
            continue
        migrate_legacy_storage(d_dir)
        state_dir = d_dir / "state"
        if state_dir.exists():
            for sf in sorted(state_dir.glob("*.md")):
                text = sf.read_text(encoding="utf-8").strip()
                if text:
                    state_map[sf.stem] = text
        elif (d_dir / "assistant_state.md").exists():
            text = (d_dir / "assistant_state.md").read_text(encoding="utf-8").strip()
            if text:
                state_map["general"] = text

    activity_entries: list[str] = []
    for d_dir in candidates:
        if not d_dir.exists():
            continue
        logs_dir = d_dir / "logs"
        if logs_dir.exists():
            for lf in sorted(logs_dir.glob("activity_*.log")):
                lines = [
                    l.strip()
                    for l in read_tail(lf, tail_lines).splitlines()
                    if l.strip()
                ]
                activity_entries.extend(lines)
        elif (d_dir / "activity_stream.log").exists():
            lines = [
                l.strip()
                for l in read_tail(
                    d_dir / "activity_stream.log", tail_lines
                ).splitlines()
                if l.strip()
            ]
            activity_entries.extend(lines)

    ws_base = root.parent if root.name in REPOS else root
    git_status: dict[str, str] = {}
    target_repos = (
        [ws_base / r for r in REPOS]
        if ws_base != root or not (root / ".git").exists()
        else [root]
    )
    for repo_path in target_repos:
        if not (repo_path / ".git").exists():
            continue
        res = subprocess.run(
            ["git", "-C", str(repo_path), "status", "-s", "-b"],
            capture_output=True,
            text=True,
            check=False,
        )
        git_status[repo_path.name] = res.stdout.strip()

    rfcs: list[str] = []
    hub_contracts = ws_base / "D3Nexus" / "shared-contracts"
    if hub_contracts.exists():
        for rfc_file in sorted(hub_contracts.glob("*/gaps_and_rfcs.md")):
            lines = rfc_file.read_text(encoding="utf-8").splitlines()
            open_items = [
                line
                for line in lines
                if "OPEN" in line or line.startswith(("## ", "### "))
            ]
            if open_items:
                rfcs.extend(open_items[-10:])

    task_candidates = [root] + [ws_base / r for r in REPOS]
    active_tasks_list: list[dict[str, object]] = []
    seen_tasks: set[Path] = set()
    for r_path in task_candidates:
        if r_path in seen_tasks:
            continue
        seen_tasks.add(r_path)
        features_dir = r_path / ".devtool" / "features"
        if not features_dir.exists():
            continue

        repo_name = r_path.name
        epic_docs = _load_epic_docs()
        for tf in epic_docs.iter_task_files(features_dir):
            lines = tf.read_text(encoding="utf-8").splitlines()[:15]
            epic_line = next((l for l in lines if l.startswith("epic:")), "")
            epic_val = epic_line.replace("epic:", "").strip().strip('"').strip("'")
            if epic_filter and epic_filter != epic_val and epic_filter not in epic_line:
                continue
            status_line = next(
                (l for l in lines if "status:" in l.lower()), "status: unknown"
            )
            st_val = (
                status_line.replace("status:", "").strip().strip('"').strip("'").lower()
            )
            if any(
                s in st_val
                for s in ["todo", "in-progress", "in_progress", "review", "backlog"]
            ):
                title_line = next((l for l in lines if l.startswith("# ")), tf.name)
                active_tasks_list.append(
                    {
                        "repo": repo_name,
                        "task": tf.name,
                        "status": st_val,
                        "title": title_line.lstrip("# ").strip(),
                        "epic": epic_val,
                    }
                )

    gate_approvals = scan_gate_ledger(root, epic_slug=epic_filter)
    checkpoints = {
        epic_name: cp for epic_name, cp in _collect_epic_checkpoints(root)
    }

    return {
        "ledger": ledger_text,
        "state": state_map,
        "checkpoints": checkpoints,
        "activity": activity_entries,
        "git_status": git_status,
        "rfcs": rfcs,
        "active_tasks": active_tasks_list,
        "gate_approvals": gate_approvals,
    }


def harvest_json(
    root: Path, tail_lines: int = 15, epic_filter: str | None = None
) -> None:
    data = collect_harvest_data(root, tail_lines=tail_lines, epic_filter=epic_filter)
    print(json.dumps(data, indent=2))


def normalize_programmer_effort(raw: str | None) -> str:
    """Normalize thinking/effort aliases (including 'extra') to canonical CLI values."""
    cleaned = (raw or "").strip()
    if not cleaned or cleaned.lower() in EXTRA_EFFORT_ALIASES:
        return DEFAULT_PROGRAMMER_EFFORT
    return cleaned


def upgrade_legacy_programmer_provider(pdata: dict[str, object]) -> tuple[str, str]:
    """Upgrade deprecated Role 2.3 models in memory while preserving custom entries."""
    raw_model = str(pdata.get("model") or "").strip()
    raw_level = str(pdata.get("thinking_level") or pdata.get("effort") or "").strip()
    if not raw_model or raw_model.lower() in LEGACY_PROGRAMMER_MODELS:
        return DEFAULT_PROGRAMMER_MODEL, DEFAULT_PROGRAMMER_EFFORT
    return raw_model, normalize_programmer_effort(raw_level)


def resolve_programmer_model_config(root: Path | None = None) -> tuple[str, str]:
    """Read Role 2.3 model and effort from .devtool/review_config.json with safe fallback."""
    candidates: list[Path] = []
    seen: set[Path] = set()
    for base in (root, Path.cwd(), resolve_primary_repo_root(root or Path.cwd())):
        if base is None:
            continue
        resolved = base.resolve()
        if resolved not in seen:
            seen.add(resolved)
            candidates.append(base)
    for cand in candidates:
        cfg_path = cand / ".devtool" / "review_config.json"
        if not cfg_path.is_file():
            continue
        try:
            data: object = json.loads(cfg_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            break
        if isinstance(data, dict):
            providers = data.get("providers")
            if isinstance(providers, dict):
                prog = providers.get("programmer")
                if isinstance(prog, dict):
                    return upgrade_legacy_programmer_provider(prog)
        break
    return DEFAULT_PROGRAMMER_MODEL, DEFAULT_PROGRAMMER_EFFORT


def _normalize_epic(slug: str) -> str:
    return slug.strip().lower().replace("_", "-")


def _truncate_utf8(text: str, max_bytes: int) -> str:
    raw = text.encode("utf-8")
    if len(raw) <= max_bytes:
        return text
    suffix = "\n...[truncated]"
    budget = max(0, max_bytes - len(suffix.encode("utf-8")))
    cut = raw[:budget].decode("utf-8", errors="ignore").rstrip()
    result = (cut + suffix) if cut else raw[:max_bytes].decode("utf-8", errors="ignore")
    while len(result.encode("utf-8")) > max_bytes:
        result = result[:-1]
    return result


def _compact_candidate_roots(
    root: Path,
    workspace_base: Path | None,
    worktree_root: Path | None,
) -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()
    ws_dir = workspace_base or (root.parent if root.name in REPOS else root)
    raw_list: list[Path | None] = [worktree_root, root]
    raw_list.extend(ws_dir / r for r in REPOS)
    for item in raw_list:
        if item is None or not item.exists():
            continue
        resolved = item.resolve()
        if resolved not in seen:
            seen.add(resolved)
            candidates.append(item)
    return candidates


def _collect_compact_snapshot(
    roots: list[Path],
    primary_root: Path,
    epic_slug: str | None,
    tail_lines: int,
) -> list[str]:
    lines: list[str] = []
    norm_epic = _normalize_epic(epic_slug) if epic_slug and epic_slug != "general" else None

    state_found = False
    for r in roots:
        state_dir = r / ".devtool" / "state"
        if not state_dir.is_dir():
            continue
        for sf in sorted(state_dir.glob("*.md")):
            if norm_epic and _normalize_epic(sf.stem) != norm_epic:
                continue
            raw_lines = [ln.strip() for ln in sf.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
            if raw_lines:
                lines.extend(ln[:160] for ln in raw_lines[:8])
                state_found = True
                break
        if state_found:
            break

    if not state_found:
        for r in roots:
            active_state = r / ".devtool" / "ACTIVE_STATE.md"
            if active_state.is_file():
                raw_lines = [
                    ln.strip()
                    for ln in active_state.read_text(encoding="utf-8", errors="replace").splitlines()
                    if ln.strip()
                ]
                filtered = [
                    ln[:160]
                    for ln in raw_lines[:10]
                    if not ln.startswith("#") and "old log entry" not in ln.lower()
                ]
                if filtered:
                    lines.append("State: " + " | ".join(filtered[:4]))
                    state_found = True
                    break

    if norm_epic:
        epic_docs = _load_epic_docs()
        hld_found = False
        for r in roots:
            epic_root = r / ".devtool" / "epic"
            if not epic_root.is_dir():
                continue
            for ep_dir in sorted(epic_root.iterdir()):
                if not ep_dir.is_dir() or _normalize_epic(ep_dir.name) != norm_epic:
                    continue
                hld_path = epic_docs.resolve_epic_doc(ep_dir, ep_dir.name)
                if hld_path is None and epic_slug:
                    hld_path = epic_docs.resolve_epic_doc(ep_dir, epic_slug)
                if hld_path is not None and not hld_path.name.endswith(".vi.md"):
                    meta = [
                        ln.strip()[:140]
                        for ln in hld_path.read_text(encoding="utf-8", errors="replace").splitlines()[:35]
                        if ln.strip().startswith(("# ", "- **Epic", "- **Status", "- **Depends"))
                    ]
                    if meta:
                        lines.append(f"HLD ({hld_path.relative_to(r)}): " + " | ".join(meta[:4]))
                        hld_found = True
                break
            if hld_found:
                break

        for ep_name, cp in _collect_epic_checkpoints(primary_root):
            if _normalize_epic(ep_name) == norm_epic:
                cp_ev = str(cp.get("event") or "")
                cp_next = str(cp.get("next_step") or "")
                cp_line = f"Checkpoint: {cp_ev}" + (f" -> {cp_next}" if cp_next else "")
                lines.append(cp_line[:160])
                break

        for r in roots:
            approvals = scan_gate_ledger(r, epic_slug=epic_slug)
            if approvals:
                summary = ", ".join(
                    f"G{a.get('gate')}@{a.get('commit')}" for a in approvals[-5:]
                )
                lines.append(f"Gates: {summary}")
                break

        log_limit = min(max(tail_lines, 1), 3)
        for r in roots:
            logs_dir = r / ".devtool" / "logs"
            if not logs_dir.is_dir():
                continue
            for lf in sorted(logs_dir.glob("activity_*.log")):
                slug_part = lf.stem.removeprefix("activity_")
                if _normalize_epic(slug_part) != norm_epic:
                    continue
                tail = [ln.strip()[:140] for ln in read_tail(lf, log_limit).splitlines() if ln.strip()]
                if tail:
                    lines.extend(f"Log: {ln}" for ln in tail)
                    break

    ledger = primary_root / ".devtool" / "PROJECT_LEDGER.md"
    if ledger.is_file():
        ledger_lines = ledger.read_text(encoding="utf-8", errors="replace").splitlines()
        matched_ledger = (
            [ln.strip()[:140] for ln in ledger_lines if norm_epic and norm_epic in _normalize_epic(ln)][:2]
            if norm_epic
            else []
        )
        if matched_ledger:
            lines.extend(f"Ledger: {ln}" for ln in matched_ledger)
        else:
            lines.append("Ledger: .devtool/PROJECT_LEDGER.md (historical milestones omitted)")
    return lines


def _collect_compact_git_status(
    root: Path,
    workspace_base: Path | None,
    worktree_root: Path | None,
) -> list[str]:
    targets: list[Path] = []
    seen: set[Path] = set()
    for cand in (worktree_root, root):
        if cand is not None and (cand / ".git").exists():
            res_p = cand.resolve()
            if res_p not in seen:
                seen.add(res_p)
                targets.append(cand)
    if not targets:
        ws = workspace_base or root
        for r in REPOS:
            cand = ws / r
            if (cand / ".git").exists():
                targets.append(cand)
    status_lines: list[str] = []
    for repo_path in targets:
        res = subprocess.run(
            ["git", "-C", str(repo_path), "status", "-s", "-b"],
            capture_output=True,
            text=True,
            check=False,
        )
        raw = [ln.rstrip() for ln in res.stdout.splitlines() if ln.strip()]
        if not raw:
            continue
        branch = raw[0]
        dirty = raw[1:]
        if dirty:
            shown = "; ".join(d.strip() for d in dirty[:5])
            extra = f" (+{len(dirty) - 5} more)" if len(dirty) > 5 else ""
            status_lines.append(f"- {repo_path.name}: {branch} | {shown}{extra}")
        else:
            status_lines.append(f"- {repo_path.name}: {branch} (clean)")
    return status_lines


def _collect_compact_tasks(
    roots: list[Path],
    epic_slug: str | None,
) -> tuple[int, int, list[str]]:
    norm_filter = _normalize_epic(epic_slug) if epic_slug and epic_slug != "general" else None
    done_count = 0
    total_count = 0
    active_lines: list[str] = []
    seen_files: set[tuple[str, str]] = set()

    epic_docs = _load_epic_docs()

    def _scan_dir(task_dir: Path, repo_label: str, *, force_done: bool) -> None:
        nonlocal done_count, total_count
        if not task_dir.is_dir():
            return
        for tf in epic_docs.iter_task_files(task_dir):
            key = (repo_label, tf.name)
            if key in seen_files:
                continue
            head = tf.read_text(encoding="utf-8", errors="replace").splitlines()[:20]
            epic_line = next((ln for ln in head if ln.startswith("epic:")), "")
            epic_val = epic_line.split(":", 1)[1].strip().strip('"').strip("'") if ":" in epic_line else ""
            if norm_filter and _normalize_epic(epic_val) != norm_filter:
                continue
            seen_files.add(key)
            if force_done:
                done_count += 1
                total_count += 1
                continue
            status_line = next((ln for ln in head if "status:" in ln.lower()), "status: todo")
            st_val = status_line.split(":", 1)[1].strip().strip('"').strip("'").lower() if ":" in status_line else "todo"
            total_count += 1
            if st_val == "done":
                done_count += 1
            else:
                title_line = next((ln for ln in head if ln.startswith("# ")), tf.name)
                title = title_line.lstrip("# ").strip()[:90]
                active_lines.append(f"- [{repo_label}] {tf.name} ({st_val}): {title}")

    for r in roots:
        features_dir = r / ".devtool" / "features"
        if features_dir.is_dir():
            repo_label = resolve_primary_repo_root(r).name
            _scan_dir(features_dir, repo_label, force_done=False)
            _scan_dir(features_dir / "done", repo_label, force_done=True)

    if total_count == 0 and norm_filter:
        for r in roots:
            epic_root = r / ".devtool" / "epic"
            if not epic_root.is_dir():
                continue
            repo_label = resolve_primary_repo_root(r).name
            for ep_dir in sorted(epic_root.iterdir()):
                if ep_dir.is_dir() and _normalize_epic(ep_dir.name) == norm_filter:
                    _scan_dir(ep_dir, repo_label, force_done=False)

    return done_count, total_count, active_lines


def _collect_compact_rfcs(
    roots: list[Path],
    workspace_base: Path | None,
    epic_slug: str | None,
) -> list[str]:
    norm_epic = _normalize_epic(epic_slug) if epic_slug and epic_slug != "general" else None
    contract_dirs: list[Path] = []
    seen_dirs: set[Path] = set()
    candidates = [r / "shared-contracts" for r in roots]
    if workspace_base is not None:
        candidates.append(workspace_base / "D3Nexus" / "shared-contracts")
    for cdir in candidates:
        if cdir.is_dir():
            res_c = cdir.resolve()
            if res_c not in seen_dirs:
                seen_dirs.add(res_c)
                contract_dirs.append(cdir)

    matched_rfcs: list[str] = []
    generic_rfcs: list[str] = []
    for cdir in contract_dirs:
        rfc_files = sorted(set(cdir.glob("*/gaps_and_rfcs.md")) | set(cdir.glob("gaps_and_rfcs.md")))
        for rfc_file in rfc_files:
            rel = str(rfc_file.relative_to(cdir))
            text = rfc_file.read_text(encoding="utf-8", errors="replace")
            sections: list[list[str]] = []
            current: list[str] = []
            for ln in text.splitlines():
                if ln.startswith(("## ", "### ")):
                    if current:
                        sections.append(current)
                    current = [ln.strip()]
                elif current:
                    current.append(ln.strip())
            if current:
                sections.append(current)

            for sec in sections:
                sec_text = "\n".join(sec)
                if "OPEN" not in sec_text.upper():
                    continue
                if "STATUS: CLOSED" in sec_text.upper() or "STATUS: RESOLVED" in sec_text.upper():
                    continue
                epic_line = next((ln for ln in sec if ln.lower().startswith(("- epic:", "epic:"))), "")
                sec_epic = epic_line.split(":", 1)[1].strip() if ":" in epic_line else ""
                if norm_epic and sec_epic and _normalize_epic(sec_epic) != norm_epic:
                    continue
                heading = sec[0][:100]
                meta = [ln for ln in sec[1:] if ln.startswith(("- Status:", "Status:", "- Epic:", "Epic:"))][:2]
                entry = f"- [{rel}] {heading}" + (f" | {' | '.join(meta)}" if meta else "")
                if norm_epic and norm_epic in _normalize_epic(sec_text):
                    matched_rfcs.append(entry[:180])
                else:
                    generic_rfcs.append(entry[:180])

    return matched_rfcs if matched_rfcs else generic_rfcs[:3]


def _render_compact_sections(
    epic_label: str,
    repo_label: str,
    snapshot_lines: list[str],
    git_lines: list[str],
    done_count: int,
    total_count: int,
    task_lines: list[str],
    rfc_lines: list[str],
    *,
    max_tasks: int | None = None,
    max_rfcs: int | None = None,
    max_snap: int | None = None,
    max_git: int | None = None,
) -> str:
    snap_slice = snapshot_lines[:max_snap] if max_snap is not None else snapshot_lines
    git_slice = git_lines[:max_git] if max_git is not None else git_lines
    rfc_slice = rfc_lines[:max_rfcs] if max_rfcs is not None else rfc_lines
    if max_tasks is not None and len(task_lines) > max_tasks:
        shown_tasks = task_lines[:max_tasks] + [f"- ... (+{len(task_lines) - max_tasks} more tasks)"]
    else:
        shown_tasks = task_lines

    parts = [
        f"# Compact Context | Epic: {epic_label} | Repo: {repo_label}",
        *snap_slice,
        "",
        "## Git Status",
        *(git_slice or ["- (no git repo detected)"]),
        "",
        f"## Tasks ({done_count}/{total_count} done)",
        *(shown_tasks or ["- (no active tasks)"]),
    ]
    if rfc_slice:
        parts.extend(["", "## Open RFCs", *rfc_slice])
    return "\n".join(parts)


def build_compact_context(
    root: Path,
    *,
    workspace_base: Path | None = None,
    worktree_root: Path | None = None,
    epic_slug: str | None = None,
    tail_lines: int = 5,
    max_bytes: int = COMPACT_MAX_BYTES,
) -> str:
    """Build an epic-scoped context snapshot strictly bounded to <= max_bytes UTF-8 bytes."""
    roots = _compact_candidate_roots(root, workspace_base, worktree_root)
    snapshot_lines = _collect_compact_snapshot(roots, root, epic_slug, tail_lines)
    git_lines = _collect_compact_git_status(root, workspace_base, worktree_root)
    done_count, total_count, task_lines = _collect_compact_tasks(roots, epic_slug)
    rfc_lines = _collect_compact_rfcs(roots, workspace_base, epic_slug)

    epic_label = epic_slug or "general"
    repo_label = root.name
    budgets: list[tuple[int | None, int | None, int | None, int | None]] = [
        (None, None, None, None),
        (8, 4, 6, 6),
        (4, 2, 4, 3),
        (2, 1, 3, 2),
    ]
    for max_t, max_r, max_s, max_g in budgets:
        rendered = _render_compact_sections(
            epic_label,
            repo_label,
            snapshot_lines,
            git_lines,
            done_count,
            total_count,
            task_lines,
            rfc_lines,
            max_tasks=max_t,
            max_rfcs=max_r,
            max_snap=max_s,
            max_git=max_g,
        )
        if len(rendered.encode("utf-8")) <= max_bytes:
            return rendered

    return _truncate_utf8(rendered, max_bytes)


def build_compact_json(
    root: Path,
    *,
    workspace_base: Path | None = None,
    worktree_root: Path | None = None,
    epic_slug: str | None = None,
    tail_lines: int = 5,
    max_bytes: int = COMPACT_MAX_BYTES,
) -> str:
    """Build an epic-scoped JSON snapshot strictly bounded to <= max_bytes UTF-8 bytes."""
    roots = _compact_candidate_roots(root, workspace_base, worktree_root)
    snapshot_lines = _collect_compact_snapshot(roots, root, epic_slug, tail_lines)
    git_lines = _collect_compact_git_status(root, workspace_base, worktree_root)
    done_count, total_count, task_lines = _collect_compact_tasks(roots, epic_slug)
    rfc_lines = _collect_compact_rfcs(roots, workspace_base, epic_slug)

    for limit in (20, 8, 4, 2, 1):
        payload = {
            "epic": epic_slug or "general",
            "repo": root.name,
            "snapshot": snapshot_lines[:limit],
            "git_status": git_lines[:limit],
            "task_progress": {"done": done_count, "total": total_count},
            "active_tasks": task_lines[:limit],
            "rfcs": rfc_lines[:limit],
        }
        rendered = json.dumps(payload, indent=2, ensure_ascii=False)
        if len(rendered.encode("utf-8")) <= max_bytes:
            return rendered
        compact_rendered = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        if len(compact_rendered.encode("utf-8")) <= max_bytes:
            return compact_rendered

    minimal = json.dumps(
        {
            "epic": epic_slug or "general",
            "repo": root.name,
            "task_progress": {"done": done_count, "total": total_count},
        },
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return minimal if len(minimal.encode("utf-8")) <= max_bytes else "{}"


_BRIEF_ROLE_CONTRACTS: dict[str, tuple[str, str]] = {
    "task-implementer": (
        "Implement assigned Kanban task in isolated slot worktree using strict Red-Green-Refactor TDD, "
        "execute and pass all mechanical Verification rows (RED -> GREEN -> REGRESSION -> TIER-B -> TIER-C), "
        "and tick all `- [x]` checkboxes in `## Definition of Done` with brief mechanical result notes "
        "(e.g. `exit 0, 42 passed`) before marking `done` or returning.",
        '{"task_id": "...", "slot": 1, "status": "DONE|BLOCKED|NEEDS_CONTEXT", '
        '"head_sha": "...", "verify": "PASS|FAIL", "changed_files": [...], '
        '"non_test_modules_changed": 0, "review_tier": "standard|full", '
        '"labels": [...], "finalized": false}',
    ),
    "task-reviewer": (
        "Run a comprehensive Pass 1 audit of the slot diff against BDD scenarios, HLD/API contracts, "
        "`Allowed files`, AST, Zero Fakery, `run_task_checks.py status` (`done gate: PASS`), "
        "and `check_bdd_traceability.py` as read-only Role 2.1 AI Architect & Reviewer; "
        "do NOT edit files, mark tasks done, or commit (Orchestrator finalizes via `finalize-slot`). "
        "Report all BLOCKER defects upfront (`category` in `BDD_VIOLATION`, "
        "`CONTRACT_SCHEMA_VIOLATION`, `RUNTIME_SAFETY`, `OWNERSHIP_ARCHITECTURE_VIOLATION`) to return "
        "`CHANGES_REQUESTED`; log minor refinements/style nits as `NON_BLOCKING_OBSERVATION` under "
        "`Observations (Non-Blocking)` / `\"observations\"` with `\"verdict\": \"APPROVED\"`.",
        '{"task_id": "...", "pass": 1, "verdict": "APPROVED|CHANGES_REQUESTED", "head_sha": "...", '
        '"done_gate": "PASS|FAIL", "blockers": [...], "observations": [...]}',
    ),
    "fix-planner": (
        "Perform read-only root-cause analysis and draft the fix plan for high-risk findings "
        "or halt criteria; do NOT edit files or commit — return the plan body in JSON so the "
        "Orchestrator writes `fix_plan_round<N>.md` and commits.",
        '{"round": 1, "status": "PLANNED|ESCALATE", "halt_criteria": [...], '
        '"plan_markdown": "..."}',
    ),
    "review-fixer": (
        "Apply Cross-Model Review fixes in `fast-track` or `apply-plan` "
        "(from Orchestrator-written `fix_plan_round<N>.md`) mode with Tier 1 scoped tests only.",
        '{"round": 1, "mode": "fast-track|apply-plan", '
        '"status": "FIXED|BLOCKED", "fix_shas": [...], '
        '"decision_sha": "...", "changed_files": [...], "tier1": "PASS|FAIL"}',
    ),
    "gate4-verifier": (
        "Execute full Gate 4 verification (`generate_smoke_checklist.py`, `audit_epic.py`, "
        "HLD integration results, `check_bdd_traceability.py`, `@quality_check --profile epic`) "
        "without editing code.",
        '{"candidate_sha": "...", "verdict": "PASS|FAIL", "audit_exit": 0, '
        '"quality_check_report": "...", "failures": [...]}',
    ),
}

_BRIEF_ROLE_PERSONA: dict[str, tuple[str, str]] = {
    "task-implementer": ("programmer", "write"),
    "task-reviewer": ("ai_architect_reviewer", "read-only"),
    "fix-planner": ("ai_architect_reviewer", "read-only"),
    "review-fixer": ("programmer", "write"),
    "gate4-verifier": ("programmer", "write"),
}

_PERSONA_DISPLAY: dict[str, tuple[str, str, str, str]] = {
    "ai_architect_reviewer": (
        "Role 2.1 AI Architect & Reviewer",
        "[PERSONA: Role 2.1 AI Architect & Reviewer]",
        "architect",
        "Stay strictly within read-only design/review boundaries. "
        "Never edit production or test files, never mark tasks done, and never commit.",
    ),
    "orchestrator": (
        "Role 2.2 Orchestrator",
        "[PERSONA: Role 2.2 Orchestrator]",
        "orchestrator",
        "NEVER read/edit `src/` or `tests/`, and NEVER run test suites or `run_task_checks.py` "
        "in the main session.",
    ),
    "programmer": (
        "Role 2.3 Programmer",
        "[PERSONA: Role 2.3 Programmer — Senior TDD Software Engineer]",
        "programmer",
        "Stay strictly within task `Allowed files`, `Decisions Already Made`, and approved HLD. "
        "Never call `manage_worker_pool.py` (pool state is Orchestrator-only). "
        "Never edit task Verification tables, DoD, `Allowed files`, or `shared-contracts/`.",
    ),
}


def _filter_english_doc_paths(paths: Sequence[str]) -> list[str]:
    """Filter out any Vietnamese mirror document path (`*.vi.md`)."""
    return [p for p in paths if p and not p.endswith(".vi.md")]


def _resolve_prompt_epic_docs(
    project_root: Path, target_dir: str, epic_slug: str
) -> dict[str, Any]:
    """Resolve English-only HLD, BDD, handoff, and design spec paths for prompts."""
    epic_docs = _load_epic_docs()
    primary_root = resolve_primary_repo_root(project_root)
    epic_path: Path | None = None
    for base in dict.fromkeys([project_root, primary_root]):
        for cand_name in dict.fromkeys([target_dir, epic_slug]):
            cand = base / ".devtool" / "epic" / cand_name
            if cand.is_dir():
                epic_path = cand
                break
        if epic_path is not None:
            break

    hld_rel = f".devtool/epic/{target_dir}/{target_dir}.md"
    bdd_rel = f".devtool/epic/{target_dir}/bdd_scenarios.md"
    handoff_rel = f".devtool/epic/{target_dir}/handoff.md"
    design_rels: list[str] = []

    if epic_path is not None:
        hld_doc = epic_docs.resolve_epic_doc(epic_path, epic_path.name)
        if hld_doc is None:
            hld_doc = epic_docs.resolve_epic_doc(epic_path, target_dir)
        if hld_doc is not None and not hld_doc.name.endswith(".vi.md"):
            hld_rel = f".devtool/epic/{target_dir}/{hld_doc.name}"

        bdd_doc = epic_docs.resolve_epic_doc(epic_path, "bdd_scenarios")
        if bdd_doc is not None and not bdd_doc.name.endswith(".vi.md"):
            bdd_rel = f".devtool/epic/{target_dir}/{bdd_doc.name}"

        handoff_doc = epic_docs.resolve_epic_doc(epic_path, "handoff")
        if handoff_doc is not None and not handoff_doc.name.endswith(".vi.md"):
            handoff_rel = f".devtool/epic/{target_dir}/{handoff_doc.name}"

        design_rels = _filter_english_doc_paths(
            [
                f".devtool/epic/{target_dir}/{p.name}"
                for p in epic_docs.resolve_design_specs(epic_path)
            ]
        )

    doc_list = _filter_english_doc_paths(
        list(dict.fromkeys([hld_rel, bdd_rel, *design_rels]))
    )
    return {
        "hld": _filter_english_doc_paths([hld_rel])[0],
        "bdd": _filter_english_doc_paths([bdd_rel])[0],
        "handoff": _filter_english_doc_paths([handoff_rel])[0],
        "docs": doc_list,
    }


def _load_pass1_blockers(
    blockers_file: Path | str | None,
    project_root: Path,
) -> Any | None:
    """Load and parse Pass 1 blockers JSON for Pass 2 task-reviewer delta briefs."""
    if blockers_file is None:
        return None
    raw_path = Path(blockers_file)
    candidate = raw_path
    if not candidate.is_absolute() and not candidate.exists():
        alt = project_root / raw_path
        if alt.exists():
            candidate = alt
    if not candidate.is_file():
        raise ValueError(f"Blockers file not found: {blockers_file}")
    try:
        return json.loads(candidate.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in blockers file {candidate}: {exc}") from exc


def emit_handoff_prompt(
    mode: str,
    epic_slug: str,
    epic_dir: str | None = None,
    custom_prompt: str | None = None,
    root: Path | None = None,
    brief_role: str | None = None,
    real_home: Path | None = None,
    *,
    review_pass: int = 1,
    pass1_tree_sha: str | None = None,
    blockers_file: Path | str | None = None,
) -> None:
    if review_pass not in (1, 2):
        raise ValueError(f"review_pass must be 1 or 2, got {review_pass!r}")
    target_dir = epic_dir or epic_slug
    project_root = Path(root) if root is not None else Path.cwd()
    prompt_note = f"\nNote: {custom_prompt}\n" if custom_prompt else ""

    pc = _load_persona_config()
    arch_binding = pc.resolve_persona("ai_architect_reviewer", project_root, real_home=real_home)
    orch_binding = pc.resolve_persona("orchestrator", project_root, real_home=real_home)
    prog_binding = pc.resolve_persona("programmer", project_root, real_home=real_home)

    docs = _resolve_prompt_epic_docs(project_root, target_dir, epic_slug)
    hld_rel = docs["hld"]
    bdd_rel = docs["bdd"]
    handoff_rel = docs["handoff"]
    docs_summary = ", ".join(docs["docs"])

    orch_banner = _PERSONA_DISPLAY["orchestrator"][1]
    arch_banner = _PERSONA_DISPLAY["ai_architect_reviewer"][1]

    if mode == "principal-review":
        print(f"""{arch_banner}
You are acting as Role 2.1 AI Architect & Reviewer (Model: {arch_binding.model_id}, Thinking/Effort: {arch_binding.effort}).
Startup command:
python3 scripts/resume_context.py --role architect --epic {epic_slug}

MANDATORY TASKS & RULES:
1. Review the English SSOT docs: {docs_summary} (HLD at {hld_rel}, BDD at {bdd_rel}).
2. Run `d3nexus:principal-review` (`Claude -> Codex -> Kiro -> Argon`, max 3 rounds). Run `principal-reviser` inline in this Role 2.1 Stage 2 session or as a same-model subagent (`python3 scripts/dev_config.py resolve ai_architect_reviewer --format argv --mode write`), then run `check_epic_readiness.py {target_dir}` in the main session.
3. DO NOT read/edit `src/` or `tests/` or modify production code.{prompt_note}""")
    elif mode == "implement":
        print(f"""{orch_banner}
You are acting as Role 2.2 Orchestrator (Model: {orch_binding.model_id}, Thinking/Effort: {orch_binding.effort}).
Startup command:
python3 scripts/resume_context.py --role orchestrator --epic {epic_slug}

MANDATORY TASKS & RULES:
1. Activate `/dev-implementation` (`d3nexus:dev-implementation`) for the `{epic_slug}` epic, following `skills/dev-lifecycle/references/orchestration-roles.md`.
2. Read `{handoff_rel}` and English SSOT epic docs ({docs_summary}) first (author all internal orchestration, plans, code comments, and commits strictly in English).
3. Orchestrator boundary: NEVER read/edit `src/` or `tests/`, and NEVER run test suites or `run_task_checks.py` in the main session.
4. Compute waves via `python3 skills/dev-implementation/resources/scripts/compute_execution_order.py {epic_slug} --parallel`, monitor `python3 scripts/estimate_heartbeat.py`, and own every `manage_worker_pool.py` call (`init`, `sync --slot <1|2> --task <task_id> [--wave <k>] --status working|review`, `triage-fix`, `finalize-slot`, `merge`, `cleanup`).
5. Dispatch Role 2.3 Programmer subagents (`task-implementer`, `gate4-verifier`) via `python3 scripts/dev_config.py dispatch --persona programmer --mode write --prompt-file <file> --cwd <worktree> --log <log> --epic {epic_slug}` (resolved: {prog_binding.cli}, model: {prog_binding.model_id}, effort: {prog_binding.effort}) and Role 2.1 AI Architect & Reviewer (`task-reviewer`) via `python3 scripts/dev_config.py dispatch --persona ai_architect_reviewer --mode read-only --prompt-file <file> --cwd <worktree> --log <log> --epic {epic_slug}` (resolved: {arch_binding.cli}, model: {arch_binding.model_id}, effort: {arch_binding.effort}) using briefs from `python3 scripts/resume_context.py --emit-prompt brief --brief-role <role> --epic {epic_slug}`, verify gating/SHAs independently, then run Cross-Model Review.{prompt_note}""")
    elif mode == "cross-review":
        print(f"""{orch_banner}
You are acting as Role 2.2 Orchestrator (Model: {orch_binding.model_id}, Thinking/Effort: {orch_binding.effort}).
Startup command:
python3 scripts/resume_context.py --role orchestrator --epic {epic_slug}

MANDATORY TASKS & RULES:
1. Gate 4 has PASSED. Activate `d3nexus:cross-model-review` following `skills/dev-lifecycle/references/orchestration-roles.md`.
2. Run external review (`run_external_review.py run`, priority `Claude -> Codex -> Kiro -> Argon`, max 3 rounds) and `triage`. NEVER read/edit `src/` or `tests/` in the main session.
3. Choose `fast-track` (Role 2.3 `review-fixer` via `python3 scripts/dev_config.py dispatch --persona programmer --mode write --prompt-file <file> --cwd <worktree> --log <log> --epic {epic_slug}`, resolved: {prog_binding.cli}, model: {prog_binding.model_id}, effort: {prog_binding.effort}) or high-risk `fix-planner` (Role 2.1 AI Architect & Reviewer via `python3 scripts/dev_config.py dispatch --persona ai_architect_reviewer --mode read-only --prompt-file <file> --cwd <worktree> --log <log> --epic {epic_slug}`, resolved: {arch_binding.cli}, model: {arch_binding.model_id}, effort: {arch_binding.effort} -> `apply-plan` via `python3 scripts/dev_config.py dispatch --persona programmer --mode write --prompt-file <file> --cwd <worktree> --log <log> --epic {epic_slug}`) using `--emit-prompt brief --brief-role <role>`, scope-check `git diff --name-only`, and dispatch a fresh `gate4-verifier` on convergence.{prompt_note}""")
    elif mode == "finish":
        print(f"""{orch_banner}
You are acting as Role 2.2 Orchestrator (Model: {orch_binding.model_id}, Thinking/Effort: {orch_binding.effort}).
Startup command:
python3 scripts/resume_context.py --role orchestrator --epic {epic_slug}

MANDATORY TASKS & RULES:
1. Activate `d3nexus:finishing-a-development-branch` for the `{epic_slug}` epic, following `skills/dev-lifecycle/references/orchestration-roles.md`.
2. Execute Pre-Finish Hook: `python3 scripts/resume_context.py --complete {epic_slug} "<milestone_summary>"`.
3. Dispatch Role 2.3 via `python3 scripts/dev_config.py dispatch --persona programmer --mode write --prompt-file <file> --cwd <worktree> --log <log> --epic {epic_slug}` (resolved: {prog_binding.cli}, model: {prog_binding.model_id}, effort: {prog_binding.effort}; `--emit-prompt brief --brief-role <role>`) if rebase/conflict resolution/`verify-tier` is needed, then land and clean up the worktree.{prompt_note}""")
    elif mode == "assistant":
        print(f"""{arch_banner}
You are acting as Role 2.1 AI Architect & Reviewer (Model: {arch_binding.model_id}, Thinking/Effort: {arch_binding.effort}).
Startup command:
python3 scripts/resume_context.py --role architect --epic {epic_slug}

MANDATORY TASKS & RULES:
1. Engage in technical discussion, root cause analysis (RCA), architecture design, and solution trade-off evaluation over English SSOT docs ({docs_summary}).
2. STRICTLY PROHIBITED from modifying production/test code or committing changes.
3. Persist discussion takeaways anytime via `python3 scripts/resume_context.py --state --role architect --epic {epic_slug} --decisions "<conclusions>"`.{prompt_note}""")
    elif mode == "brief":
        role_key = brief_role or ""
        if role_key not in _BRIEF_ROLE_CONTRACTS:
            print(f"Unknown brief role: {role_key}")
            return
        objective, schema = _BRIEF_ROLE_CONTRACTS[role_key]
        extra_block = ""
        if role_key == "task-reviewer" and review_pass == 2:
            sha_ref = (pass1_tree_sha or "").strip() or "<pass1_tree_sha>"
            loaded_blockers = _load_pass1_blockers(blockers_file, project_root)
            objective = (
                f"Run Pass 2 Delta-Only Verification over the Fix Pass 1 diff (`git diff {sha_ref}`), "
                "Pass 1 blockers, `run_task_checks.py status` (`done gate: PASS`), and "
                "`check_bdd_traceability.py` as read-only Role 2.1 AI Architect & Reviewer; "
                "do NOT edit files, mark tasks done, or commit."
            )
            schema = (
                '{"task_id": "...", "pass": 2, "verdict": "APPROVED|CHANGES_REQUESTED", '
                '"head_sha": "...", "done_gate": "PASS|FAIL", "blockers": [...], "observations": [...]}'
            )
            blockers_section = (
                f"\nPass 1 blockers: {json.dumps(loaded_blockers, ensure_ascii=False)}"
                if loaded_blockers is not None
                else ""
            )
            extra_block = (
                "\n\nPASS 2 DELTA-ONLY VERIFICATION RULES:\n"
                f"- Inspect ONLY `git diff {sha_ref}` (`pass1_tree_sha`), Pass 1 blockers, "
                "`run_task_checks.py status`, and `check_bdd_traceability.py`.\n"
                "- Strictly forbidden: introducing new non-regression findings, new edge cases, "
                "or state-transition nitpicks in Pass 2.\n"
                "- Only direct syntax or runtime regressions introduced by Fix Pass 1 "
                '(`category: "DIRECT_REGRESSION"`) or unresolved Pass 1 blockers may appear in `blockers`.'
                f"{blockers_section}"
            )
        persona_key, dispatch_mode = _BRIEF_ROLE_PERSONA[role_key]
        binding = pc.resolve_persona(persona_key, project_root, real_home=real_home)
        dispatch_argv = shlex.join(pc.build_dispatch_argv(binding, dispatch_mode))
        persona_label, banner, startup_role, boundaries = _PERSONA_DISPLAY[persona_key]
        print(f"""{banner}
You are acting as {persona_label} (`{role_key}` | Model: {binding.model_id}, Thinking/Effort: {binding.effort}).
Dispatch argv: {dispatch_argv}
Startup command:
python3 scripts/resume_context.py --role {startup_role} --epic {epic_slug}

SUBAGENT BRIEF & BOUNDARIES:
1. Objective: {objective}
2. Epic docs (English SSOT): {docs_summary}
3. Boundaries: {boundaries}
4. End your response with exactly one fenced `json` block matching:
```json
{schema}
```{extra_block}{prompt_note}""")
    else:
        print(f"Unknown prompt mode: {mode}")


def update_zshrc_env(zshrc_path: Path, r_home: Path, ws_root: Path) -> None:
    if not zshrc_path.exists():
        zshrc_path.write_text("", encoding="utf-8")
    content = zshrc_path.read_text(encoding="utf-8")
    lines_to_add: list[str] = []
    if "REAL_HOME" not in content:
        lines_to_add.append(f'export REAL_HOME="{r_home}"')
    if "WORKSPACE_ROOT" not in content:
        lines_to_add.append(f'export WORKSPACE_ROOT="{ws_root}"')
    kit_root = Path(__file__).resolve().parents[1]
    m_kit = re.search(r'export\s+D3NEXUS_KIT="([^"]*)"', content)
    if m_kit:
        if m_kit.group(1) != str(kit_root):
            content = (
                content[: m_kit.start()]
                + f'export D3NEXUS_KIT="{kit_root}"'
                + content[m_kit.end() :]
            )
    else:
        lines_to_add.append(f'export D3NEXUS_KIT="{kit_root}"')
    if (
        'PATH="$D3NEXUS_KIT/bin:$PATH"' not in content
        and 'export PATH="$D3NEXUS_KIT/bin:$PATH"' not in content
    ):
        lines_to_add.append('export PATH="$D3NEXUS_KIT/bin:$PATH"')
    updated_kit = bool(m_kit and m_kit.group(1) != str(kit_root))
    if lines_to_add or updated_kit:
        prefix = ("\n".join(lines_to_add) + "\n") if lines_to_add else ""
        zshrc_path.write_text(prefix + content, encoding="utf-8")


def update_zshrc_history_and_aliases(zshrc_path: Path) -> None:
    content = zshrc_path.read_text(encoding="utf-8")
    if 'HISTFILE="$REAL_HOME/.zsh_history"' not in content:
        hist_block = (
            "\n# Shared real-time zsh history across accounts\n"
            'export HISTFILE="$REAL_HOME/.zsh_history"\n'
            "export HISTSIZE=50000\n"
            "export SAVEHIST=50000\n"
            "setopt INC_APPEND_HISTORY\n"
            "setopt SHARE_HISTORY\n"
            "setopt HIST_IGNORE_DUPS\n"
        )
        if "source $ZSH/oh-my-zsh.sh" in content:
            parts = content.split("source $ZSH/oh-my-zsh.sh", 1)
            content = parts[0] + "source $ZSH/oh-my-zsh.sh" + hist_block + parts[1]
        else:
            content += hist_block

    if "alias resume=" not in content:
        content += "\nalias resume='python3 $HOME/Projects/ai-agent-tools/scripts/resume_context.py'\n"
    if "alias save-context=" not in content:
        content += "alias save-context='python3 $HOME/Projects/ai-agent-tools/scripts/resume_context.py --complete'\n"
    zshrc_path.write_text(content, encoding="utf-8")


def update_zshrc_sync_items(zshrc_path: Path) -> None:
    content = zshrc_path.read_text(encoding="utf-8")
    m = (
        re.search(r"sync_items=\((.*?)\)", content, re.DOTALL)
        if "ag_run()" in content
        else None
    )
    if not m:
        return
    body = m.group(1)
    tokens = [
        t
        for ln in body.splitlines()
        if not ln.strip().startswith("#")
        for t in ln.split()
    ]
    missing = [
        k for k in ("AllProjects", "Projects", ".zsh_history") if k not in tokens
    ]
    if not missing:
        return
    suffix = (
        f"\n    {' '.join(missing)}\n  " if "\n" in body else f" {' '.join(missing)}"
    )
    new_decl = (
        f"sync_items=({body.rstrip() if chr(10) in body else body.strip()}{suffix})"
    )
    zshrc_path.write_text(
        content[: m.start()] + new_decl + content[m.end() :], encoding="utf-8"
    )


def merge_profile_history(
    prof_hist: Path, main_hist: Path, seen_cmds: set[str]
) -> None:
    if not prof_hist.exists():
        return
    if prof_hist.is_symlink():
        return
    raw_text = prof_hist.read_text(encoding="utf-8", errors="replace")
    prof_lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    new_lines = [l for l in prof_lines if l not in seen_cmds]
    if new_lines:
        with main_hist.open("a", encoding="utf-8") as f:
            for nl in new_lines:
                f.write(nl + "\n")
                seen_cmds.add(nl)
    prof_hist.unlink()
    prof_hist.symlink_to(main_hist)


def sync_profile_symlinks(prof: Path, main_hist: Path, ws_root: Path) -> None:
    prof_hist = prof / ".zsh_history"
    if not prof_hist.exists() and not prof_hist.is_symlink():
        prof_hist.symlink_to(main_hist)
    for name in ["Projects", "AllProjects"]:
        p_link = prof / name
        if not p_link.exists() and not p_link.is_symlink():
            p_link.symlink_to(ws_root)
        elif p_link.is_symlink() and p_link.resolve() != ws_root.resolve():
            p_link.unlink()
            p_link.symlink_to(ws_root)


def _real_home() -> Path:
    """Host user's real HOME, derived (never hard-coded); strips /antigravity_homes/<profile> when inside a profile."""
    home = os.environ.get("REAL_HOME") or str(Path.home())
    return Path(home.split("/antigravity_homes")[0]) if "/antigravity_homes" in home else Path(home)


def sync_shell_env(
    real_home: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, object]:
    r_home = real_home or _real_home()
    ws_root = workspace_root or _real_home() / "AllProjects"
    zshrc_path = r_home / ".zshrc"
    main_hist = r_home / ".zsh_history"

    update_zshrc_env(zshrc_path, r_home, ws_root)
    update_zshrc_history_and_aliases(zshrc_path)
    update_zshrc_sync_items(zshrc_path)

    projects_link = r_home / "Projects"
    if not projects_link.exists() and not projects_link.is_symlink():
        projects_link.symlink_to(ws_root)

    if not main_hist.exists():
        main_hist.write_text("", encoding="utf-8")
    main_text = main_hist.read_text(encoding="utf-8", errors="replace")
    seen_cmds = {l.strip() for l in main_text.splitlines() if l.strip()}

    synced_profiles: list[str] = []
    profiles_dir = r_home / "antigravity_homes"
    if profiles_dir.exists():
        for prof in sorted(profiles_dir.iterdir()):
            if (
                prof.is_dir()
                and not prof.is_symlink()
                and not prof.name.startswith(".")
                and not prof.name.startswith("-")
                and prof.name not in {"Library", "System", "Shared", "AllProjects", "Projects", "fvm", "claude", "codex", "kiro"}
            ):
                merge_profile_history(prof / ".zsh_history", main_hist, seen_cmds)
                sync_profile_symlinks(prof, main_hist, ws_root)
                synced_profiles.append(prof.name)

    return {
        "real_home": str(r_home),
        "workspace_root": str(ws_root),
        "synced_profiles": synced_profiles,
    }


def _current_head_sha(cwd: Path) -> str:
    """Return full HEAD SHA for `cwd`, or empty string when unavailable."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    return res.stdout.strip() if res.returncode == 0 else ""


def _parse_task_id_epic_status(tf: Path) -> tuple[str, str, str]:
    """Read `(task_id, epic, status)` from task frontmatter without reading .vi.md."""
    lines = tf.read_text(encoding="utf-8", errors="replace").splitlines()[:25]
    task_id = tf.stem
    epic_val = ""
    status_val = "todo"
    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("id:"):
            task_id = stripped.split(":", 1)[1].strip().strip('"').strip("'") or task_id
        elif stripped.startswith("epic:"):
            epic_val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
        elif stripped.startswith("status:"):
            status_val = (
                stripped.split(":", 1)[1].strip().strip('"').strip("'").lower()
            )
    return task_id, epic_val, status_val


def _collect_checkpoint_task_lists(
    target_root: Path,
    epic_slug: str,
    existing_hb: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Collect deduplicated `(tasks_done, tasks_in_flight)` for `epic_slug`."""
    epic_docs = _load_epic_docs()
    norm_epic = _normalize_epic(epic_slug)
    done_list: list[str] = []
    in_flight_list: list[str] = []

    def _scan(task_dir: Path, *, force_done: bool) -> None:
        if not task_dir.is_dir():
            return
        for tf in epic_docs.iter_task_files(task_dir):
            task_id, epic_val, status_val = _parse_task_id_epic_status(tf)
            if norm_epic and norm_epic != "general" and _normalize_epic(epic_val) != norm_epic:
                continue
            if force_done or status_val == "done":
                done_list.append(task_id)
            elif status_val in ("in-progress", "in_progress", "review"):
                in_flight_list.append(task_id)

    features_dir = target_root / ".devtool" / "features"
    _scan(features_dir, force_done=False)
    _scan(features_dir / "done", force_done=True)

    hb_active = existing_hb.get("active_tasks")
    if isinstance(hb_active, list):
        for t in hb_active:
            if str(t):
                in_flight_list.append(str(t))
    hb_slots = existing_hb.get("slots")
    if isinstance(hb_slots, dict):
        for slot_val in hb_slots.values():
            if not isinstance(slot_val, dict):
                continue
            slot_status = str(slot_val.get("status") or "").lower()
            task_id = str(slot_val.get("task_id") or "")
            if task_id and slot_status in ("working", "review", "in-progress", "in_progress"):
                in_flight_list.append(task_id)

    tasks_done = list(dict.fromkeys(done_list))
    done_set = set(tasks_done)
    tasks_in_flight = [t for t in dict.fromkeys(in_flight_list) if t not in done_set]
    return tasks_done, tasks_in_flight


def record_checkpoint_event(
    target_root: Path,
    repo_root: Path,
    current_worktree: Path,
    title_target: Path,
    active_epic: str,
    *,
    event: str,
    next_step: str = "",
    role: str | None = None,
    repo: str | None = None,
    wave: int | None = None,
    real_home: str | None = None,
) -> dict[str, Any]:
    """Build and persist a structured checkpoint block and refresh Next Immediate Step."""
    devtool_dir = resolve_target_devtool_dir(target_root, repo)
    hb_root = devtool_dir.parent
    existing_hb = _state_envelope.read_epic_heartbeat(hb_root, active_epic)
    wave_val = wave if wave is not None else existing_hb.get("active_wave")
    if not (isinstance(wave_val, int) and not isinstance(wave_val, bool)):
        wave_val = None
    tasks_done, tasks_in_flight = _collect_checkpoint_task_lists(
        hb_root, active_epic, existing_hb
    )
    sha_target = (
        current_worktree
        if resolve_primary_repo_root(current_worktree).resolve() == hb_root.resolve()
        else hb_root
    )
    head_sha = _current_head_sha(sha_target)
    persona_name = normalize_role(role) if role else "orchestrator"

    pc = _load_persona_config()
    profile = detect_current_profile(title_target, real_home=real_home) or "default"
    real_home_path = Path(real_home) if real_home else None
    is_low_quota = (
        pc.low_quota_state(repo_root, profile, real_home=real_home_path) is not None
    )
    legacy_warnings = pc.detect_legacy_warnings(repo_root, real_home=real_home_path)

    checkpoint_payload: dict[str, Any] = {
        "event": event,
        "at": _state_envelope._utc_now_iso(),
        "persona": persona_name,
        "head_sha": head_sha,
        "wave": wave_val,
        "tasks_done": tasks_done,
        "tasks_in_flight": tasks_in_flight,
        "next_step": next_step,
        "turns_since_checkpoint": 0,
        "low_quota": is_low_quota,
    }
    if legacy_warnings:
        checkpoint_payload["warning"] = "; ".join(legacy_warnings)

    stored = _state_envelope.update_epic_checkpoint(
        hb_root, active_epic, checkpoint_payload
    )

    ex_role, ex_decisions, ex_status, ex_next, ex_prompt = (
        _read_existing_epic_state_fields(devtool_dir, active_epic)
    )
    effective_next = next_step or ex_next or event
    state_role = normalize_role(role) if role else (ex_role or persona_name)
    write_epic_state(
        target_root,
        active_epic,
        decisions=ex_decisions,
        status=ex_status,
        next_step=effective_next,
        prompt=ex_prompt,
        role=state_role,
        repo=repo,
        refresh_heartbeat=False,
        clear_pending=False,
        active_wave=wave_val,
    )
    return stored


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI ArgumentParser for resume_context.py."""
    parser = argparse.ArgumentParser(
        description="Two-Tier Context Harvester & Multi-Epic Memory Tool"
    )
    parser.add_argument(
        "--workspace-root", type=str, help="Workspace root containing repositories"
    )
    parser.add_argument(
        "--real-home", type=str, help="Real home directory for shell environment sync"
    )
    parser.add_argument("--repo", type=str, help="Target repository name")
    parser.add_argument("--epic", type=str, help="Active epic slug")
    parser.add_argument(
        "--role",
        type=str,
        choices=list(ROLE_CHOICES),
        help="Active persona role (assistant maps to architect)",
    )
    parser.add_argument(
        "--tail", type=int, default=15, help="Number of activity log lines to show"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output harvest in JSON format"
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit epic-scoped compact context bounded to <= 4096 UTF-8 bytes",
    )

    parser.add_argument(
        "--state", action="store_true", help="Record active epic state snapshot"
    )
    parser.add_argument(
        "--decisions", type=str, default="", help="Decisions text for --state"
    )
    parser.add_argument(
        "--status", type=str, default="", help="Status text for --state"
    )
    parser.add_argument(
        "--next", type=str, default="", help="Next immediate step for --state"
    )
    parser.add_argument(
        "--prompt", type=str, default="", help="Custom prompt or notes for --state"
    )

    parser.add_argument(
        "--log", action="store_true", help="Record programmer activity entry"
    )
    parser.add_argument("--task", type=str, default="general", help="Task ID for --log")
    parser.add_argument(
        "--request", type=str, default="", help="Request summary for --log"
    )
    parser.add_argument("--action", type=str, default="", help="Action taken for --log")
    parser.add_argument(
        "--note", type=str, default="None", help="Deviations or notes for --log"
    )

    parser.add_argument(
        "--complete", nargs="+", help="Complete feature: <slug> <summary>"
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        choices=list(CHECKPOINT_EVENTS),
        help="Record a structured lifecycle checkpoint event",
    )
    parser.add_argument(
        "--complete-checkpoint",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--emit-prompt",
        type=str,
        choices=[
            "principal-review",
            "implement",
            "cross-review",
            "finish",
            "assistant",
            "brief",
        ],
        help="Emit handoff prompt",
    )
    parser.add_argument(
        "--brief-role",
        type=str,
        choices=list(_BRIEF_ROLE_CONTRACTS.keys()),
        help="Subagent role for --emit-prompt brief",
    )
    parser.add_argument(
        "--review-pass",
        type=int,
        choices=[1, 2],
        default=1,
        help="Task-reviewer pass number (1: comprehensive audit, 2: delta-only verification)",
    )
    parser.add_argument(
        "--pass1-tree-sha",
        type=str,
        default=None,
        help="Pre-fix Pass 1 tree SHA for Pass 2 task-reviewer delta-only brief",
    )
    parser.add_argument(
        "--blockers-file",
        type=str,
        default=None,
        help="JSON file of Pass 1 blockers for Pass 2 task-reviewer delta-only brief",
    )
    parser.add_argument(
        "--epic-dir", type=str, help="Epic directory name for --emit-prompt"
    )

    parser.add_argument(
        "--sync-zshrc",
        action="store_true",
        help="Synchronize shell environment and history",
    )
    parser.add_argument(
        "--sync-title",
        action="store_true",
        help="Synchronize window.title and bar colors in .vscode/settings.json",
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="",
        help="Stage or task override string for window title",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="",
        help="Profile / account ID override for window title (e.g. duvthinh403, danhdue)",
    )
    parser.add_argument(
        "--all-repos",
        action="store_true",
        help="Synchronize window.title and bar colors across all known repositories",
    )

    parser.add_argument(
        "--gate",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Record gate approval (1..5)",
    )
    parser.add_argument(
        "--approved",
        type=str,
        default="",
        help="Approved scope description for --gate",
    )
    parser.add_argument(
        "--deviations",
        type=str,
        default="",
        help="Approved deviations or Spec Errata IDs for --gate",
    )
    parser.add_argument(
        "--by",
        type=str,
        default="developer",
        help="Approver identity for --gate",
    )
    parser.add_argument(
        "--check-gate",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Check if gate (1..5) is approved for --epic",
    )
    parser.add_argument(
        "--detect-profile",
        action="store_true",
        help="Resolve and print the active profile identifier",
    )
    parser.add_argument(
        "--pending-decision",
        type=str,
        default=None,
        help="Record a pending Choice A human decision for --epic",
    )
    parser.add_argument(
        "--decision-kind",
        type=str,
        default="approval",
        help="Decision kind metadata for --pending-decision",
    )
    parser.add_argument(
        "--decision-id",
        type=str,
        default=None,
        help="Explicit decision identifier for --pending-decision or --clear-decision",
    )
    parser.add_argument(
        "--clear-decision",
        action="store_true",
        help="Clear pending Choice A decision for --epic (and optional --decision-id)",
    )
    parser.add_argument(
        "--wave",
        type=int,
        default=None,
        help="Active execution wave number for per-epic heartbeat updates",
    )
    return parser


def parse_args(
    argv: list[str] | None = None,
    parser: argparse.ArgumentParser | None = None,
) -> argparse.Namespace:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    normalized_args: list[str] = []
    has_complete = "--complete" in raw_args
    i = 0
    while i < len(raw_args):
        if (
            raw_args[i] == "--complete"
            and i + 1 < len(raw_args)
            and raw_args[i + 1] == "--checkpoint"
        ):
            normalized_args.extend(["--complete-checkpoint", "--complete"])
            i += 2
        elif (
            has_complete
            and raw_args[i] == "--checkpoint"
            and (i + 1 >= len(raw_args) or raw_args[i + 1] not in CHECKPOINT_EVENTS)
        ):
            normalized_args.append("--complete-checkpoint")
            i += 1
        else:
            normalized_args.append(raw_args[i])
            i += 1

    active_parser = parser or build_parser()
    return active_parser.parse_args(normalized_args)


def main() -> None:
    parser = build_parser()
    args = parse_args(parser=parser)
    workspace = resolve_workspace_root(args.workspace_root)
    primary_repo = resolve_primary_repo_root()
    current_worktree = resolve_current_worktree_root()
    active_repo = args.repo or (
        primary_repo.name if primary_repo != workspace else "workspace"
    )

    is_repo = (primary_repo / ".git").exists() or (primary_repo / ".devtool").exists()
    if args.workspace_root:
        target_root = resolve_workspace_root(args.workspace_root)
    elif args.repo:
        primary_parent = primary_repo.parent
        repo_candidate = primary_parent / args.repo
        if repo_candidate.exists():
            target_root = repo_candidate
        elif (workspace / args.repo).exists():
            target_root = workspace / args.repo
        else:
            target_root = primary_repo if is_repo else workspace
    elif is_repo:
        target_root = primary_repo
    else:
        target_root = workspace

    title_target = (
        resolve_workspace_root(args.workspace_root)
        if args.workspace_root
        else (target_root if args.repo else current_worktree)
    )
    ws_arg = Path(args.workspace_root).resolve() if args.workspace_root else None
    if args.repo:
        if ws_arg is not None and (ws_arg / args.repo).exists():
            repo_root = ws_arg / args.repo
        elif (primary_repo.parent / args.repo).exists():
            repo_root = primary_repo.parent / args.repo
        elif (workspace / args.repo).exists():
            repo_root = workspace / args.repo
        elif primary_repo.name == args.repo:
            repo_root = primary_repo
        else:
            repo_root = target_root
    elif ws_arg is not None:
        if (ws_arg / ".git").exists() or (ws_arg / ".devtool").exists():
            repo_root = ws_arg
        elif (current_worktree / ".git").exists() and current_worktree.parent == ws_arg:
            repo_root = current_worktree
        else:
            repo_root = ws_arg
    else:
        repo_root = target_root

    active_epic = args.epic or resolve_current_epic_slug(repo_root if args.repo else title_target)

    if args.detect_profile:
        print(detect_current_profile(title_target, real_home=args.real_home))
        return

    if args.role:
        print_role_banner(args.role)

    if args.emit_prompt:
        if args.emit_prompt == "brief" and not args.brief_role:
            parser.error("--brief-role is required when --emit-prompt brief is used")
        try:
            emit_handoff_prompt(
                args.emit_prompt,
                active_epic,
                args.epic_dir,
                args.prompt,
                root=repo_root,
                brief_role=args.brief_role,
                real_home=Path(args.real_home) if args.real_home else None,
                review_pass=args.review_pass,
                pass1_tree_sha=args.pass1_tree_sha,
                blockers_file=args.blockers_file,
            )
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(2)
        return

    if args.sync_zshrc:
        r_home = Path(args.real_home) if args.real_home else None
        ws_root = Path(args.workspace_root) if args.workspace_root else None
        res = sync_shell_env(real_home=r_home, workspace_root=ws_root)
        print(f"Shell environment synchronized: {res}")
        return

    if args.sync_title:
        if getattr(args, "all_repos", False):
            base_dir = (
                target_root.parent
                if (target_root.parent / "ai-agent-tools").exists()
                else _real_home() / "AllProjects"
            )
            for rname in REPOS:
                rpath = base_dir / rname
                if rpath.exists():
                    sync_window_title(
                        rpath,
                        epic_slug=active_epic,
                        stage_override=args.stage,
                        profile_override=args.profile or None,
                    )
                    print(
                        f"Window title and workspace bar colors synchronized for {rpath.name}"
                    )
            return
        sync_window_title(
            title_target,
            epic_slug=active_epic,
            stage_override=args.stage,
            profile_override=args.profile or None,
        )
        print(
            f"Window title and workspace bar colors synchronized for {title_target.name}"
        )
        return

    if args.complete:
        slug = args.complete[0]
        summary = (
            " ".join(args.complete[1:])
            if len(args.complete) > 1
            else "Completed feature and verified contracts."
        )
        complete_feature_and_rotate(
            target_root,
            slug,
            summary,
            repo=args.repo,
            checkpoint=bool(args.complete_checkpoint or args.checkpoint),
        )
        return

    if args.checkpoint:
        record_checkpoint_event(
            target_root,
            repo_root,
            current_worktree,
            title_target,
            active_epic,
            event=args.checkpoint,
            next_step=args.next,
            role=args.role,
            repo=args.repo,
            wave=args.wave,
            real_home=args.real_home,
        )
        print(f"Recorded checkpoint '{args.checkpoint}' for epic '{active_epic}'")
        return

    if args.clear_decision:
        _state_envelope.clear_pending_decision(
            target_root,
            active_epic,
            decision_id=(args.decision_id.strip() if args.decision_id else None),
        )
        _state_envelope.update_epic_heartbeat(
            target_root,
            active_epic,
            stage=args.status.strip() or "In progress: Resumed AUTO MODE",
            sub_step="resumed",
            last_event=args.next.strip() or "Human confirmed — resumed AUTO MODE",
        )
        print(f"Cleared pending decision for epic '{active_epic}'")
        return

    if args.pending_decision is not None:
        reason_text = args.pending_decision.strip()
        if not reason_text:
            print(
                "error: --pending-decision must be non-empty",
                file=sys.stderr,
            )
            sys.exit(2)
        _state_envelope.record_pending_decision(
            target_root,
            active_epic,
            reason_text,
            kind=(args.decision_kind.strip() or "approval"),
            decision_id=(args.decision_id.strip() if args.decision_id else None),
            stage=args.status.strip() or args.stage.strip(),
            worktree=current_worktree,
        )
        if args.wave is not None:
            _state_envelope.update_epic_heartbeat(
                target_root,
                active_epic,
                active_wave=args.wave,
                last_event=f"Pending decision recorded: {reason_text}",
            )
        print(f"Recorded pending decision for epic '{active_epic}'")
        return

    if args.state:
        write_epic_state(
            target_root,
            active_epic,
            decisions=args.decisions,
            status=args.status,
            next_step=args.next,
            prompt=args.prompt,
            role=normalize_role(args.role) if args.role else "programmer",
            repo=args.repo,
            active_wave=args.wave,
        )
        return

    if args.wave is not None:
        _state_envelope.update_epic_heartbeat(
            target_root,
            active_epic,
            active_wave=args.wave,
            last_event=f"Active wave set to {args.wave}",
        )
        print(f"Updated active wave to {args.wave} for epic '{active_epic}'")
        return

    if args.log:
        append_activity_log(
            target_root,
            active_epic,
            active_repo,
            args.task,
            args.request,
            args.action,
            note=args.note,
        )
        return

    if args.gate is not None:
        if not args.approved.strip():
            print(
                "error: --approved must be non-empty when recording --gate",
                file=sys.stderr,
            )
            sys.exit(2)
        rec = record_gate_approval(
            target_root,
            active_epic,
            args.gate,
            args.approved.strip(),
            deviations=args.deviations.strip(),
            by=args.by.strip() or "developer",
            repo=args.repo,
        )
        print(
            f"Recorded Gate {args.gate} approval for epic '{active_epic}' at {rec.get('commit')}"
        )
        return

    if args.check_gate is not None:
        chk_rec = check_gate_approval(
            target_root, active_epic, args.check_gate, repo=args.repo
        )
        if chk_rec is not None:
            print(json.dumps(chk_rec))
            sys.exit(0)
        else:
            print(
                f"Gate {args.check_gate} is not yet recorded for epic '{active_epic}'",
                file=sys.stderr,
            )
            sys.exit(1)

    # Default: Harvest context
    if args.compact:
        wt_for_compact: Path | None = None
        if (args.workspace_root is None and args.repo is None) or (
            resolve_primary_repo_root(current_worktree).resolve() == repo_root.resolve()
        ):
            wt_for_compact = current_worktree
        scoped_epic = args.epic or (active_epic if active_epic != "general" else None)
        if args.json:
            print(
                build_compact_json(
                    repo_root,
                    workspace_base=workspace,
                    worktree_root=wt_for_compact,
                    epic_slug=scoped_epic,
                    tail_lines=args.tail,
                )
            )
        else:
            print(
                build_compact_context(
                    repo_root,
                    workspace_base=workspace,
                    worktree_root=wt_for_compact,
                    epic_slug=scoped_epic,
                    tail_lines=args.tail,
                )
            )
        return

    scan_root = target_root
    if args.json:
        harvest_json(scan_root, tail_lines=args.tail, epic_filter=args.epic)
        return

    scan_project_ledger(scan_root)
    scan_assistant_state(scan_root)
    approvals = scan_gate_ledger(scan_root, epic_slug=active_epic)
    if approvals:
        print_section("1.5. GATE APPROVALS (.devtool/GATE_LEDGER.md)")
        for a in approvals:
            ep = a.get("epic")
            g = a.get("gate")
            ap = a.get("approved")
            dev = a.get("deviations")
            dev_str = f" [deviations: {dev}]" if dev else ""
            print(f"  - Gate {g} ({ep}): {ap}{dev_str} (at {a.get('commit')})")
    scan_epic_checkpoints(scan_root)
    scan_activity_stream(scan_root, tail_lines=args.tail)
    scan_git_status(scan_root)
    scan_open_rfcs(scan_root)
    scan_active_tasks(scan_root, epic_filter=args.epic)
    sync_window_title(
        title_target,
        epic_slug=active_epic,
        stage_override=args.stage or None,
        profile_override=args.profile or None,
    )


if __name__ == "__main__":
    main()
