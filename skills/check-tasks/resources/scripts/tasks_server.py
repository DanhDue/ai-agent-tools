"""HTTP daemon server, port collision protection, and REST API for check-tasks.

Provides background daemon infrastructure, PID file management, and REST API endpoints:
- GET  /api/tasks: Serialized multi-repo dashboard graph
- GET  /api/review: Persisted review findings and triage table
- POST /api/launch/cli: Rule 9 sanitized interactive CLI launcher
- POST /api/launch/ide: Rule 9 sanitized Antigravity IDE launcher
- POST /api/shutdown: Graceful server termination
- GET  /: Serves web dashboard HTML
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import dataclasses
from datetime import datetime, timezone
import hashlib
import http.server
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shlex
import signal
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any
import urllib.parse
import urllib.request

# Ensure check_tasks is importable
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from check_tasks import (
        DashboardGraph,
        add_tracked_project,
        build_initial_tracked_projects,
        design_spec_paths,
        discover_antigravity_profiles,
        discover_untracked_workspace_repos,
        epic_doc_path,
        harvest_dashboard_graph,
        harvest_epic_history,
        load_tracked_projects,
        remove_tracked_project,
        resolve_projects_config_path,
        resolve_tracked_repo_dir,
        scan_repo,
    )
except ImportError:
    pass

DEFAULT_PORT = 8766
DEFAULT_QUOTA_PORT = 8765
DEFAULT_PID_FILE = Path("/tmp/agy_tasks_server.pid")
_STATE_ENVELOPE_MOD: Any | None = None
_AGY_PROFILE_POOL_SIG: tuple[str, int, int] | None = None
_AGY_PROFILE_POOL_MOD: Any | None = None


def _load_state_envelope() -> Any | None:
    """Lazily import shared `scripts/_state_envelope.py` without failing on standalone copies."""
    global _STATE_ENVELOPE_MOD
    with contextlib.suppress(Exception):
        from check_tasks import _load_kit_module

        _STATE_ENVELOPE_MOD = _load_kit_module(
            "_state_envelope", "scripts", "_state_envelope.py"
        )
        return _STATE_ENVELOPE_MOD
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
            except Exception:
                return None
    return None


def _load_agy_profile_pool() -> Any:
    """Lazily load shared `scripts/agy_profile_pool.py` via check_tasks loader or kit path."""
    global _AGY_PROFILE_POOL_MOD, _AGY_PROFILE_POOL_SIG
    with contextlib.suppress(Exception):
        from check_tasks import _AGY_POOL_REL, _load_kit_module

        _AGY_PROFILE_POOL_MOD = _load_kit_module("agy_profile_pool", *_AGY_POOL_REL)
        return _AGY_PROFILE_POOL_MOD
    for parent in [SCRIPT_DIR, *SCRIPT_DIR.parents]:
        candidate = parent / "scripts" / "agy_profile_pool.py"
        if not candidate.is_file():
            continue
        st = candidate.stat()
        sig = (str(candidate.resolve()), st.st_mtime_ns, st.st_size)
        if _AGY_PROFILE_POOL_MOD is not None and _AGY_PROFILE_POOL_SIG == sig:
            return _AGY_PROFILE_POOL_MOD
        spec = importlib.util.spec_from_file_location("agy_profile_pool", str(candidate))
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules["agy_profile_pool"] = module
        spec.loader.exec_module(module)
        _AGY_PROFILE_POOL_MOD = module
        _AGY_PROFILE_POOL_SIG = sig
        return module
    raise RuntimeError("agy_profile_pool module unavailable")


def _parse_int_field(raw: Any, field_name: str, *, min_value: int) -> int:
    if type(raw) is int:
        parsed = raw
    elif isinstance(raw, str) and raw.strip().isdigit():
        parsed = int(raw.strip())
    else:
        raise ValueError(f"{field_name} must be an integer >= {min_value}")
    if parsed < min_value:
        raise ValueError(f"{field_name} must be >= {min_value}")
    return parsed


def update_agy_profile_settings(
    profile: str,
    *,
    priority: Any = None,
    max_concurrent: Any = None,
    real_home: Path | str | None = None,
) -> dict[str, Any]:
    """Update a pool profile's priority and/or max_concurrent in agy_profiles.json safely under lock."""
    clean_profile = str(profile or "").strip()
    if not clean_profile:
        raise ValueError("Missing required field: profile")
    if priority is None and max_concurrent is None:
        raise ValueError("Specify at least one of: priority, max_concurrent")

    parsed_priority = (
        _parse_int_field(priority, "priority", min_value=1)
        if priority is not None
        else None
    )
    parsed_max_concurrent = (
        _parse_int_field(max_concurrent, "max_concurrent", min_value=0)
        if max_concurrent is not None
        else None
    )

    pool_mod = _load_agy_profile_pool()
    try:
        updated_cfg = pool_mod.update_profile(
            clean_profile,
            priority=parsed_priority,
            max_concurrent=parsed_max_concurrent,
            real_home=real_home,
        )
    except pool_mod.AgyPoolError as exc:
        raise ValueError(str(exc)) from exc

    pool_list = updated_cfg.get("pool", [])
    updated_entry = next(
        (entry for entry in pool_list if entry.get("profile") == clean_profile),
        {},
    )
    return {
        "status": "ok",
        "profile": clean_profile,
        "priority": updated_entry.get("priority", parsed_priority),
        "max_concurrent": updated_entry.get("max_concurrent", parsed_max_concurrent),
        "pool": pool_list,
    }


def update_agy_profile_priority(
    profile: str,
    priority: Any,
    *,
    real_home: Path | str | None = None,
) -> dict[str, Any]:
    """Update a pool profile's dispatch priority in global agy_profiles.json safely under lock."""
    return update_agy_profile_settings(
        profile,
        priority=priority,
        real_home=real_home,
    )


def _assert_contained(path: Path, boundary: Path, label: str) -> Path:
    """Verify resolved `path` remains inside resolved `boundary`, raising ValueError on escape."""
    resolved = path.resolve()
    bound_resolved = boundary.resolve()
    if not resolved.is_relative_to(bound_resolved):
        raise ValueError(f"{label} escapes allowed boundary: {path} -> {resolved}")
    return resolved


def get_real_home() -> str:
    """Resolve the host user's real HOME directory even when invoked inside an isolated profile."""
    current = os.path.expanduser("~")
    if "/antigravity_homes/" in current:
        return current.split("/antigravity_homes/", 1)[0]
    if current.endswith("/antigravity_homes"):
        return current[: -len("/antigravity_homes")]
    return os.environ.get("REAL_HOME") or current


def build_clean_host_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Return a clean host environment stripped of leaked IDE, Electron, and profile variables."""
    env = dict(os.environ if base_env is None else base_env)
    env["HOME"] = get_real_home()
    for exact_key in (
        "AGY_PROFILE",
        "AGY_CLI_MODE",
        "AGY_ENABLE_HUB",
        "TERM_PROGRAM",
        "TERM_PROGRAM_VERSION",
        "TERM_SESSION_ID",
        "TMPDIR",
        "ZDOTDIR",
    ):
        env.pop(exact_key, None)
    for key in list(env.keys()):
        if key.startswith(("VSCODE_", "ANTIGRAVITY_", "ELECTRON_", "CHROME_")):
            env.pop(key, None)
    return env


def pid_meta_path(pid_file: Path = DEFAULT_PID_FILE) -> Path:
    """Return the companion metadata file path used to track a daemon's code fingerprint."""
    return pid_file.with_name(f"{pid_file.name}.meta.json")


def compute_server_code_fingerprint() -> str:
    """Compute a deterministic digest of the server, harvester, kit modules, and dashboard UI."""
    hasher = hashlib.sha256()
    candidates: list[tuple[str, Path]] = [
        ("tasks_server.py", SCRIPT_DIR / "tasks_server.py"),
        ("check_tasks.py", SCRIPT_DIR / "check_tasks.py"),
        (
            "dashboard/tasks_dashboard.html",
            SCRIPT_DIR.parent / "dashboard" / "tasks_dashboard.html",
        ),
    ]
    for parent in [SCRIPT_DIR, *SCRIPT_DIR.parents]:
        cand_scripts = parent / "scripts"
        if (cand_scripts / "persona_config.py").is_file() or (
            cand_scripts / "agy_profile_pool.py"
        ).is_file():
            for rel_mod in (
                "persona_config.py",
                "personas.default.json",
                "agy_profile_pool.py",
                "_state_envelope.py",
            ):
                candidates.append((f"scripts/{rel_mod}", cand_scripts / rel_mod))
            break
    for label, src in candidates:
        hasher.update(label.encode("utf-8"))
        hasher.update(b"\0")
        if src.is_file():
            with contextlib.suppress(OSError):
                hasher.update(src.read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()[:16]


def get_running_pid(pid_file: Path = DEFAULT_PID_FILE) -> int | None:
    """Return the PID of the running server if alive; cleanup stale file if dead."""
    if not pid_file.is_file():
        return None
    try:
        content = pid_file.read_text(encoding="utf-8").strip()
        pid = int(content)
        os.kill(pid, 0)
        return pid
    except (ValueError, OSError):
        with contextlib.suppress(OSError):
            pid_file.unlink(missing_ok=True)
            pid_meta_path(pid_file).unlink(missing_ok=True)
        return None


def is_running_server_stale(
    existing_pid: int,
    pid_file: Path,
    expected_workspace: Path,
    port: int = DEFAULT_PORT,
    expected_fingerprint: str | None = None,
) -> bool:
    """Return True if the running daemon came from older code or a different workspace."""
    expected_fp = expected_fingerprint or compute_server_code_fingerprint()
    expected_ws = str(expected_workspace.resolve())

    meta_file = pid_meta_path(pid_file)
    if meta_file.is_file():
        with contextlib.suppress(OSError, ValueError, TypeError):
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            if isinstance(meta, dict) and meta.get("pid") == existing_pid:
                meta_ws = str(meta.get("workspace_root") or "")
                with contextlib.suppress(OSError):
                    meta_ws = str(Path(meta_ws).resolve())
                return (
                    meta.get("code_fingerprint") != expected_fp
                    or meta_ws != expected_ws
                )

    with contextlib.suppress(OSError, ValueError, TimeoutError):
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/status")
        with urllib.request.urlopen(req, timeout=0.8) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, dict) and data.get("pid") == existing_pid:
                    remote_fp = data.get("code_fingerprint")
                    return not remote_fp or remote_fp != expected_fp

    return True


def _wait_for_daemon_ready(port: int, timeout: float = 2.0) -> bool:
    """Poll /api/status briefly so the newly spawned daemon is accepting connections."""
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/api/status"
    while time.monotonic() < deadline:
        with (
            contextlib.suppress(OSError, ValueError, TimeoutError),
            urllib.request.urlopen(url, timeout=0.4) as resp,
        ):
            if resp.status == 200:
                return True
        time.sleep(0.05)
    return False


def find_available_port(start_port: int, max_attempts: int = 10) -> int:
    """Find an available port starting at start_port, incrementing on collision."""
    for attempt in range(max_attempts):
        candidate = start_port + attempt
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", candidate))
                return candidate
        except OSError:
            continue
    return start_port


def quote_path_for_zsh(path_str: str) -> str:
    """Format path for zsh command, allowing ~ tilde expansion while quoting special characters."""
    if path_str.startswith("~/"):
        sub_path = path_str[2:]
        quoted_sub = shlex.quote(sub_path)
        if quoted_sub.startswith("'") and quoted_sub.endswith("'"):
            return f"~/{quoted_sub[1:-1]}"
        return f"~/{quoted_sub}"
    return shlex.quote(path_str)


def sanitize_paths_to_tilde(data: Any) -> Any:
    """Recursively convert all /Users/<username> paths to ~ for relative display."""
    if dataclasses.is_dataclass(data) and not isinstance(data, type):
        return sanitize_paths_to_tilde(dataclasses.asdict(data))
    if isinstance(data, (Path, os.PathLike)):
        return re.sub(r"^/Users/[^/]+", "~", str(data))
    if isinstance(data, str):
        return re.sub(r"^/Users/[^/]+", "~", data)
    if isinstance(data, list):
        return [sanitize_paths_to_tilde(item) for item in data]
    if isinstance(data, dict):
        return {k: sanitize_paths_to_tilde(v) for k, v in data.items()}
    if hasattr(data, "__dict__"):
        return sanitize_paths_to_tilde(data.__dict__)
    return data


def build_cli_launch_command(worktree: str, profile: str) -> list[str]:
    """Build Rule 9 compliant CLI terminal launch command using profile alias."""
    quoted_worktree = quote_path_for_zsh(worktree)
    quoted_profile = shlex.quote(profile)
    inner_cmd = (
        f"cd {quoted_worktree} && {quoted_profile}-cli"
        if profile != "default"
        else f"cd {quoted_worktree} && agy"
    )
    escaped_inner = inner_cmd.replace('"', '\\"')
    script = f'tell application "Terminal" to do script "{escaped_inner}"'
    return ["osascript", "-e", script]


def build_ide_launch_command(worktree: str, profile: str) -> list[str]:
    """Build profile-based Antigravity IDE launch command (e.g. buivantrong8901 ~/AllProjects/lyrics-sync)."""
    quoted_worktree = quote_path_for_zsh(worktree)
    quoted_profile = shlex.quote(profile)
    cmd_str = (
        f"{quoted_profile} {quoted_worktree}"
        if profile != "default"
        else f"antigravity {quoted_worktree}"
    )
    return ["zsh", "-i", "-c", cmd_str]


def find_quota_script(workspace_root: Path) -> Path | None:
    """Locate scripts/agy_quota.py across workspace roots and repositories."""
    candidates = [
        workspace_root / "scripts" / "agy_quota.py",
        workspace_root / "ai-agent-tools" / "scripts" / "agy_quota.py",
    ]
    for c in candidates:
        if c.is_file():
            return c

    for parent in SCRIPT_DIR.parents:
        cand = parent / "scripts" / "agy_quota.py"
        if cand.is_file():
            return cand

    real_home = get_real_home()
    cand_home = (
        Path(real_home) / "AllProjects" / "ai-agent-tools" / "scripts" / "agy_quota.py"
    )
    if cand_home.is_file():
        return cand_home

    return None


def is_quota_server_alive(port: int = DEFAULT_QUOTA_PORT) -> bool:
    """Check if the Quota Web Server daemon is active and responding."""
    try:
        import urllib.request

        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status", timeout=1.0)
        return req.status == 200
    except Exception:
        return False


def launch_quota_server(
    workspace_root: Path, port: int = DEFAULT_QUOTA_PORT
) -> dict[str, Any]:
    """Launch the Quota Web Server daemon in background if not already alive."""
    url = f"http://127.0.0.1:{port}"
    if is_quota_server_alive(port):
        return {"status": "ok", "action": "already_running", "url": url}

    quota_script = find_quota_script(workspace_root)
    if not quota_script or not quota_script.is_file():
        return {
            "status": "error",
            "error": "scripts/agy_quota.py not found",
            "url": url,
        }

    cmd = [sys.executable, str(quota_script), "--ui", "--no-open"]
    try:
        subprocess.Popen(
            cmd,
            cwd=str(quota_script.parent.parent),
            env=build_clean_host_env(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
        return {"status": "ok", "action": "launched", "url": url}
    except Exception as e:
        return {"status": "error", "error": str(e), "url": url}


def _epic_slug_variants(active_epic: str) -> list[str]:
    """Return ordered unique slug variants across hyphen and underscore forms."""
    return list(
        dict.fromkeys(
            [
                active_epic,
                active_epic.replace("-", "_"),
                active_epic.replace("_", "-"),
            ]
        )
    )


def _discover_round_files(
    review_dir: Path, detected_kind: str
) -> list[tuple[int, Path]]:
    """Discover per-round review files inside `review_dir` sorted by round number."""
    if not review_dir.is_dir():
        return []
    pattern = (
        re.compile(r"^principal_review_round_(\d+)\.md$", re.IGNORECASE)
        if detected_kind == "principal"
        else re.compile(r"^(?:review_results|review)_round_(\d+)\.md$", re.IGNORECASE)
    )
    found: list[tuple[int, Path]] = []
    with contextlib.suppress(OSError):
        for entry in sorted(review_dir.iterdir()):
            if not entry.is_file():
                continue
            m = pattern.match(entry.name)
            if m:
                found.append((int(m.group(1)), entry))
    found.sort(key=lambda item: (item[0], item[1].name))
    return found


def _build_epic_review_roots(repo_dir: Path, active_epic: str | None) -> list[Path]:
    """Build ordered candidate checkout roots (matching worktrees before root repo)."""
    roots: list[Path] = []
    if active_epic:
        roots.extend(
            repo_dir / ".worktrees" / v for v in _epic_slug_variants(active_epic)
        )
    roots.append(repo_dir)
    seen: set[Path] = set()
    ordered: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        resolved = root.resolve()
        if resolved not in seen:
            seen.add(resolved)
            ordered.append(root)
    return ordered


def _append_kind_review_files(
    candidates: list[Path], base_dir: Path, target_round: int | None, kind: str | None
) -> None:
    """Append ordered review markdown candidates under an epic or root .devtool dir."""
    if kind == "principal":
        if target_round:
            candidates.append(base_dir / f"principal_review_round_{target_round}.md")
        candidates.append(base_dir / "principal_review.md")
        if target_round is None:
            candidates.extend(
                p for _, p in _discover_round_files(base_dir, "principal")
            )
    elif kind == "cross-model":
        if target_round:
            candidates.extend(
                [
                    base_dir / f"review_results_round_{target_round}.md",
                    base_dir / f"review_round_{target_round}.md",
                ]
            )
        candidates.append(base_dir / "review_results.md")
        if target_round is None:
            candidates.extend(
                p for _, p in _discover_round_files(base_dir, "cross-model")
            )
    else:
        if target_round:
            candidates.extend(
                [
                    base_dir / f"review_results_round_{target_round}.md",
                    base_dir / f"review_round_{target_round}.md",
                    base_dir / f"principal_review_round_{target_round}.md",
                ]
            )
        candidates.extend(
            [base_dir / "review_results.md", base_dir / "principal_review.md"]
        )
        if target_round is None:
            candidates.extend(
                p for _, p in _discover_round_files(base_dir, "cross-model")
            )
            candidates.extend(
                p for _, p in _discover_round_files(base_dir, "principal")
            )


def _collect_review_candidates(
    repo_dir: Path,
    active_epic: str | None,
    target_round: int | None,
    kind: str | None,
    strict_epic: bool,
) -> list[Path]:
    """Collect ordered review markdown paths honoring `strict_epic` scoping."""
    roots = _build_epic_review_roots(repo_dir, active_epic)
    candidates: list[Path] = []
    if active_epic:
        variants = _epic_slug_variants(active_epic)
        for root in roots:
            dt = root / ".devtool"
            for variant in variants:
                _append_kind_review_files(
                    candidates, dt / "epic" / variant, target_round, kind
                )
        if not strict_epic:
            for root in roots:
                dt = root / ".devtool"
                if kind == "principal":
                    candidates.append(dt / "principal_review.md")
                elif kind == "cross-model":
                    candidates.append(dt / "review_results.md")
                else:
                    candidates.extend(
                        [dt / "review_results.md", dt / "principal_review.md"]
                    )
        return candidates

    for root in roots:
        dt = root / ".devtool"
        if kind == "principal":
            _append_kind_review_files(candidates, dt, target_round, kind)
        else:
            _append_kind_review_files(candidates, dt, target_round, "cross-model")
            candidates.append(dt / "features" / "review_results.md")
    return candidates


def _discover_round_file_numbers(review_dir: Path, detected_kind: str) -> list[int]:
    """Discover sibling per-round review files so multi-file rounds list accurately."""
    return [r for r, _ in _discover_round_files(review_dir, detected_kind)]


def _scan_round_headings(content: str) -> list[tuple[int, list[str]]]:
    """Scan `## Round N` sections using a fence-aware parser."""
    fence_pattern = re.compile(r"^(`{3,}|~{3,})")
    parsed_rounds: list[tuple[int, list[str]]] = []
    current_fence = ""
    for line in content.splitlines():
        fence_match = fence_pattern.match(line)
        if current_fence:
            if line.rstrip() == current_fence:
                current_fence = ""
        elif fence_match:
            current_fence = fence_match.group(1)
        elif heading_match := re.fullmatch(r"##\s+Round\s+(\d+)", line.strip()):
            parsed_rounds.append((int(heading_match.group(1)), []))
        elif parsed_rounds:
            parsed_rounds[-1][1].append(line)
    return parsed_rounds


_REVIEW_PARSE_CACHE_LOCK = threading.Lock()
_REVIEW_PARSE_CACHE: dict[
    tuple[str, str | None, int | None, str | None, bool, bool],
    tuple[tuple[tuple[Path, tuple[int, int] | None], ...], dict[str, Any]],
] = {}
_REVIEW_PARSE_CACHE_MAX = 128


def _file_stat_sig(path: Path) -> tuple[int, int] | None:
    """Return `(st_mtime_ns, st_size)` for cache invalidation, or None if missing."""
    try:
        st = path.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


_INLINE_PROPOSAL_RE = re.compile(
    r"(?:^|(?:[.;—]|\n)\s*)\b(?:Proposed(?:\s+action)?|Fix|Suggestion|Đề xuất):\s*",
    re.IGNORECASE,
)
_FIX_PLAN_ACTION_KEY_RE = re.compile(
    r"^(\s*)(?:[-*]\s+)?\*\*(?:Proposed\s+Action(?:\s*\([^*\n]*\))?|Planned\s+Surgical\s+Fix|Surgical\s+Fix|Action|Fix)\s*(?::\*\*\s*|\*\*:\s*)(.*)$",
    re.IGNORECASE,
)
_FIX_PLAN_SIBLING_KEY_RE = re.compile(
    r"^(\s*)(?:[-*]\s+)?\*\*[A-Za-z0-9_][^`*\n]*?(?::\*\*|\*\*:)",
)
_PLACEHOLDER_ACTIONS = {"", "?", "—", "-", "n/a", "none"}


def _extract_inline_proposal(problem_full: str) -> tuple[str, str]:
    """Extract trailing proposal text outside inline backtick code spans."""
    masked = re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), problem_full)
    last_match: re.Match[str] | None = None
    for match in _INLINE_PROPOSAL_RE.finditer(masked):
        last_match = match
    if last_match is None:
        return problem_full, ""
    return (
        problem_full[: last_match.start()].strip(),
        problem_full[last_match.end() :].strip(),
    )


def _split_md_table_row(line: str) -> list[str]:
    """Split a markdown pipe-delimited row while honoring escaped pipes."""
    raw_cells = re.split(r"(?<!\\)\|", line.strip())
    cells = [c.strip().replace(r"\|", "|") for c in raw_cells]
    if cells and cells[0] == "":
        cells.pop(0)
    if cells and cells[-1] == "":
        cells.pop()
    return cells


def _is_md_separator_row(cells: list[str]) -> bool:
    """Return True when all non-empty cells are markdown alignment dashes."""
    non_empty = [c for c in cells if c]
    return bool(non_empty) and all(
        re.fullmatch(r":?-{2,}:?", c) is not None for c in non_empty
    )


def _norm_header_cell(cell: str) -> str:
    """Normalize a markdown table header cell for case-insensitive matching."""
    cleaned = cell.strip().strip("*_`").strip()
    return re.sub(r"\s+", " ", cleaned.lower())


def _is_review_table_header(cells: list[str]) -> bool:
    """Return True when `cells` represent a review triage table header row."""
    if len(cells) < 4 or re.fullmatch(r"#?\d+", cells[0].strip()):
        return False
    norms = [_norm_header_cell(c) for c in cells]
    return any(n in {"severity", "mức độ", "sev"} for n in norms)


def _map_review_table_columns(header_cells: list[str]) -> dict[str, int]:
    """Map review table header cells to semantic keys with canonical 5-col fallback."""
    col_map: dict[str, int] = {}
    for idx, raw_col in enumerate(header_cells):
        norm = _norm_header_cell(raw_col)
        if "id" not in col_map and norm in {"#", "id", "no", "no.", "finding", "finding #"}:
            col_map["id"] = idx
        elif "severity" not in col_map and norm in {"severity", "mức độ", "sev"}:
            col_map["severity"] = idx
        elif "location" not in col_map and norm in {
            "location",
            "file / target",
            "file/target",
            "target",
            "file",
            "artefact",
            "artifact",
            "vị trí",
        }:
            col_map["location"] = idx
        elif "problem" not in col_map and (
            norm in {"problem", "issue", "finding / problem", "description", "vấn đề"}
            or "problem" in norm
        ):
            col_map["problem"] = idx
        elif "proposed_action" not in col_map and (
            norm
            in {
                "proposed action",
                "action",
                "proposed",
                "proposed fix",
                "planned surgical fix",
                "surgical fix",
                "đề xuất",
                "hành động đề xuất",
            }
            or "proposed action" in norm
        ):
            col_map["proposed_action"] = idx
        elif "decision" not in col_map and (
            norm
            in {
                "decision",
                "status",
                "fixed in(commit)",
                "fixed in (commit)",
                "fixed in",
                "triage",
                "quyết định",
            }
            or "decision" in norm
            or "fixed in" in norm
        ):
            col_map["decision"] = idx

    claimed = set(col_map.values())
    for key, default_idx in (("id", 0), ("severity", 1), ("location", 2), ("problem", 3)):
        if key not in col_map and default_idx not in claimed and default_idx < len(header_cells):
            col_map[key] = default_idx
            claimed.add(default_idx)
    if "decision" not in col_map:
        if 4 not in claimed and len(header_cells) >= 5:
            col_map["decision"] = 4
        elif 5 not in claimed and len(header_cells) >= 6:
            col_map["decision"] = 5
    return col_map


def _extract_numeric_id(raw: str) -> str | None:
    """Extract normalized integer ID string from `#1` / `1` / `Finding #1`, or None."""
    m = re.search(r"(\d+)", raw.strip())
    return str(int(m.group(1))) if m else None


def _format_action_parts(first_val: str, cont: list[str]) -> str:
    """Join lead inline action text and continuation bullets cleanly."""
    if first_val and not cont:
        return first_val
    if not first_val and len(cont) == 1:
        return re.sub(r"^[-*]\s+", "", cont[0]).strip()
    parts = ([first_val] if first_val else []) + cont
    return "\n".join(parts).strip()


def _collect_action_continuation(
    lines: list[str], key_indent: int | None
) -> list[str]:
    """Collect multi-line continuation bullets/prose until next sibling key or table."""
    cont: list[str] = []
    base_indent = 0 if key_indent is None else key_indent
    for sub_line in lines:
        stripped = sub_line.strip()
        if not stripped:
            continue
        if stripped.startswith("|") or re.match(r"^(?:`{3,}|~{3,})", stripped):
            break
        m_sib = _FIX_PLAN_SIBLING_KEY_RE.match(sub_line)
        if m_sib and (key_indent is None or len(m_sib.group(1)) <= key_indent):
            break
        sub_indent = len(sub_line) - len(sub_line.lstrip())
        if cont and sub_indent <= base_indent and not stripped.startswith(("-", "*")):
            break
        cont.append(stripped)
    return cont


def _extract_block_action(
    block_lines: list[str], numbered_head: str | None
) -> str:
    """Extract proposed action prose from a per-finding heading or numbered block."""
    for idx, b_line in enumerate(block_lines):
        m_act = _FIX_PLAN_ACTION_KEY_RE.match(b_line)
        if m_act:
            cont = _collect_action_continuation(
                block_lines[idx + 1 :], len(m_act.group(1))
            )
            return _format_action_parts(m_act.group(2).strip(), cont)
    if numbered_head is not None:
        cont = _collect_action_continuation(block_lines, None)
        return _format_action_parts(numbered_head, cont)
    return ""


def _parse_fix_plan_summary_tables(non_fenced_lines: list[str]) -> dict[str, str]:
    """Extract best-effort `# -> Action` mappings from summary markdown tables."""
    summary: dict[str, str] = {}
    table_cols: tuple[int, int] | None = None
    for line in non_fenced_lines:
        s = line.strip()
        if not s.startswith("|"):
            table_cols = None
            continue
        cells = _split_md_table_row(s)
        if _is_md_separator_row(cells):
            continue
        norms = [_norm_header_cell(c) for c in cells]
        id_col = next(
            (
                i
                for i, n in enumerate(norms)
                if n in {"#", "id", "no", "no.", "finding", "finding #", "item"}
            ),
            None,
        )
        act_col = next(
            (
                i
                for i, n in enumerate(norms)
                if i != id_col
                and (
                    n
                    in {
                        "action",
                        "proposed action",
                        "planned surgical fix",
                        "surgical fix",
                        "proposed fix",
                        "fix",
                        "planned fix",
                        "remediation",
                        "đề xuất",
                    }
                    or "proposed action" in n
                    or "surgical fix" in n
                )
            ),
            None,
        )
        if (
            id_col is not None
            and act_col is not None
            and not re.fullmatch(r"#?\d+", cells[id_col].strip())
        ):
            table_cols = (id_col, act_col)
            continue
        if table_cols is not None:
            c_id, c_act = table_cols
            if c_id < len(cells) and c_act < len(cells):
                fid = _extract_numeric_id(cells[c_id])
                act = cells[c_act].strip()
                if fid and act.lower() not in _PLACEHOLDER_ACTIONS:
                    summary.setdefault(fid, act)
    return summary


def _parse_fix_plan_actions(
    fix_plan_path: Path, expected_round: int | None = None
) -> dict[str, str]:
    """Best-effort parse of per-finding actions from `fix_plan_roundN.md` / `fix_plan.md`."""
    if not fix_plan_path.is_file():
        return {}
    try:
        content = fix_plan_path.read_text(encoding="utf-8", errors="replace")
        fence_re = re.compile(r"^\s*(`{3,}|~{3,})")
        current_fence = ""
        clean_lines: list[str] = []
        for raw_line in content.splitlines():
            m_fence = fence_re.match(raw_line)
            if current_fence:
                if raw_line.strip().startswith(current_fence):
                    current_fence = ""
                continue
            if m_fence:
                current_fence = m_fence.group(1)
                continue
            clean_lines.append(raw_line)

        if expected_round is not None:
            for hdr_line in clean_lines[:10]:
                if re.match(r"^\s*#{2,6}\s+", hdr_line):
                    break
                m_decl = re.search(
                    r"(?:^#\s+.*?\bRound\s+(\d+)\b|\*\*Round\*\*\s*:\s*(\d+))",
                    hdr_line,
                    re.IGNORECASE,
                )
                if m_decl:
                    decl_num = int(m_decl.group(1) or m_decl.group(2))
                    if decl_num != expected_round:
                        return {}
                    break

        summary_actions = _parse_fix_plan_summary_tables(clean_lines)
        detailed_actions: dict[str, str] = {}
        blocks: list[tuple[list[str], list[str], str | None]] = []

        for line in clean_lines:
            stripped = line.strip()
            m_finding_h = re.match(
                r"^\s*#{2,4}\s+(?:\[[^\]\n]+\]\s*)?(?:Finding\s+#?(\d+)|#(\d+))\b",
                line,
                re.IGNORECASE,
            )
            m_fix_h = re.match(
                r"^\s*#{2,4}\s+Fix\s+(\d+)\b(.*)$", line, re.IGNORECASE
            )
            m_num_item = re.match(
                r"^\s*\d+\.\s+\*\*(?:Finding\s*)?#(\d+)(?:\b[^*\n]*)?(?::\*\*\s*|\*\*:\s*|\*\*\s*[—–-]\s*)(.*)$",
                line,
                re.IGNORECASE,
            )
            if m_finding_h:
                primary_id = str(int(m_finding_h.group(1) or m_finding_h.group(2)))
                extra = [str(int(x)) for x in re.findall(r"#(\d+)", line)]
                ids = list(dict.fromkeys([primary_id, *extra]))
                blocks.append((ids, [], None))
            elif m_fix_h:
                hash_ids = [str(int(x)) for x in re.findall(r"#(\d+)", m_fix_h.group(2))]
                ids = list(dict.fromkeys(hash_ids)) or [str(int(m_fix_h.group(1)))]
                blocks.append((ids, [], None))
            elif m_num_item:
                blocks.append(
                    ([str(int(m_num_item.group(1)))], [], m_num_item.group(2).strip())
                )
            elif re.match(r"^\s*#{1,6}\s+", line) or re.match(
                r"^\d+\.\s+", line
            ) or re.match(r"^\s*(?:---+|\*\*\*+|___+)\s*$", stripped):
                blocks.append(([], [], None))
            elif blocks and blocks[-1][0]:
                blocks[-1][1].append(line)

        for target_ids, b_lines, num_head in blocks:
            if not target_ids:
                continue
            act_text = _extract_block_action(b_lines, num_head)
            if act_text and act_text.lower() not in _PLACEHOLDER_ACTIONS:
                for fid in target_ids:
                    detailed_actions[fid] = act_text

        merged = dict(summary_actions)
        merged.update(detailed_actions)
        return merged
    except Exception:
        return {}


def parse_review_results(
    repo_dir: Path,
    active_epic: str | None = None,
    target_round: int | None = None,
    kind: str | None = None,
    *,
    strict_epic: bool = False,
    include_raw: bool = True,
) -> dict[str, Any]:
    """Parse persisted review findings and triage table for a repository and round."""
    cache_key = (
        str(repo_dir),
        active_epic,
        target_round,
        kind,
        strict_epic,
        include_raw,
    )
    with _REVIEW_PARSE_CACHE_LOCK:
        cached_entry = _REVIEW_PARSE_CACHE.get(cache_key)
    if cached_entry is not None:
        watch_sigs, cached_result = cached_entry
        if all(_file_stat_sig(p) == sig for p, sig in watch_sigs):
            return copy.deepcopy(cached_result)

    result: dict[str, Any] = {
        "repo": repo_dir.name,
        "epic": active_epic,
        "round": target_round or 1,
        "available_rounds": [1],
        "kind": kind or "review",
        "present": False,
        "verdict": "UNKNOWN",
        "sha": None,
        "reviewer": None,
        "model": None,
        "thinking": None,
        "theme_color": None,
        "findings": [],
        "raw_output": "",
        "has_raw_output": False,
        "raw_output_bytes": 0,
    }

    # Extract repo theme color from .vscode/settings.json if present
    vscode_settings = repo_dir / ".vscode" / "settings.json"
    if vscode_settings.is_file():
        with contextlib.suppress(Exception):
            settings_json = json.loads(vscode_settings.read_text(encoding="utf-8"))
            color_customizations = settings_json.get(
                "workbench.colorCustomizations", {}
            )
            result["theme_color"] = color_customizations.get(
                "titleBar.activeBackground"
            ) or color_customizations.get("statusBar.background")

    candidates = _collect_review_candidates(
        repo_dir, active_epic, target_round, kind, strict_epic
    )

    review_file: Path | None = next((c for c in candidates if c and c.is_file()), None)
    if not review_file:
        return result

    try:
        content = review_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return result

    result["present"] = True

    # Detect kind from filename if not specified
    if "principal" in review_file.name.lower():
        result["kind"] = "principal"
    elif (
        "review_results" in review_file.name.lower()
        or "cross" in review_file.name.lower()
    ):
        result["kind"] = "cross-model"

    # Check if filename specifies round
    m_file_round = re.search(r"round_(\d+)", review_file.name, re.IGNORECASE)

    parsed_rounds = _scan_round_headings(content)
    sibling_rounds = _discover_round_file_numbers(
        review_file.parent, str(result["kind"])
    )
    unnumbered_rounds: set[int] = set()
    if m_file_round is not None:
        sibling_name = (
            "principal_review.md"
            if result["kind"] == "principal"
            else "review_results.md"
        )
        unnumbered_path = review_file.parent / sibling_name
        if unnumbered_path.is_file():
            with contextlib.suppress(OSError, UnicodeDecodeError):
                sib_parsed = _scan_round_headings(
                    unnumbered_path.read_text(encoding="utf-8")
                )
                if sib_parsed:
                    unnumbered_rounds.update(r[0] for r in sib_parsed)
                else:
                    unnumbered_rounds.add(1)

    unique_rounds = sorted(
        {r[0] for r in parsed_rounds} | set(sibling_rounds) | unnumbered_rounds
    )
    if unique_rounds:
        result["available_rounds"] = unique_rounds
    elif m_file_round:
        result["available_rounds"] = [int(m_file_round.group(1))]
    else:
        result["available_rounds"] = [1]

    # Select round section
    if m_file_round:
        round_to_extract = int(m_file_round.group(1))
    elif target_round and target_round in result["available_rounds"]:
        round_to_extract = target_round
    else:
        round_to_extract = (
            result["available_rounds"][0] if result["available_rounds"] else 1
        )

    result["round"] = round_to_extract

    # Extract round content
    round_content = content
    if parsed_rounds:
        for r_num, r_lines in parsed_rounds:
            if r_num == round_to_extract:
                round_content = f"## Round {r_num}\n" + "\n".join(r_lines)
                break
    elif not m_file_round:
        m_r = re.search(r"(?:Round\s+(\d+)|Round\*\*:\s*(\d+))", content, re.IGNORECASE)
        if m_r:
            with contextlib.suppress(ValueError):
                result["round"] = int(m_r.group(1) or m_r.group(2))

    # Parse metadata from round_content
    m_verdict = re.search(
        r"(?:Overall Verdict|\*\*Overall Verdict\*\*|- \*\*Overall Verdict\*\*|\*\*Verdict\*\*|- \*\*Verdict\*\*):\s*([^\n\r]+)",
        round_content,
    )
    if m_verdict:
        result["verdict"] = m_verdict.group(1).strip()

    m_sha = re.search(
        r"(?:Candidate Commit SHA|\*\*Candidate Commit SHA\*\*|- \*\*Candidate Commit SHA\*\*|\*\*SHA\*\*|- \*\*SHA\*\*):\s*`?([0-9a-fA-F]+)`?",
        round_content,
    )
    if m_sha:
        result["sha"] = m_sha.group(1)

    m_reviewer = re.search(
        r"(?:Reviewer / Provider|\*\*Reviewer / Provider\*\*|- \*\*Reviewer / Provider\*\*|\*\*Reviewer\*\*|\*\*CLI\*\*|- \*\*Reviewer\*\*|- \*\*CLI\*\*):\s*([^\n]+)",
        round_content,
    )
    if m_reviewer:
        result["reviewer"] = m_reviewer.group(1).strip()

    m_model = re.search(
        r"(?:\*\*Model\*\*|- \*\*Model\*\*|Model\*\*):\s*([^\n]+)", round_content
    )
    if m_model:
        result["model"] = m_model.group(1).strip()

    m_thinking = re.search(
        r"(?:\*\*Thinking\*\*|- \*\*Thinking\*\*):\s*([^\n]+)", round_content
    )
    if m_thinking:
        result["thinking"] = m_thinking.group(1).strip()

    m_kind = re.search(r"(?:\*\*Kind\*\*|- \*\*Kind\*\*):\s*([^\n]+)", round_content)
    if m_kind:
        result["kind"] = m_kind.group(1).strip()

    # Clean active round section to isolate only its immediate table before Raw Output or prompt logs
    m_raw_split = re.search(
        r"(?m)^(?:Raw output:|### Earlier Rounds|```)", round_content
    )
    table_section = (
        round_content[: m_raw_split.start()] if m_raw_split else round_content
    )

    # Parse 5/6-column triage tables with header-aware column detection
    lines = table_section.splitlines()
    in_table = False
    col_map: dict[str, int] = {
        "id": 0,
        "severity": 1,
        "location": 2,
        "problem": 3,
        "decision": 4,
    }
    findings: list[dict[str, str]] = []
    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            if in_table:
                in_table = False
            continue
        cells = _split_md_table_row(s)
        if _is_review_table_header(cells):
            in_table = True
            col_map = _map_review_table_columns(cells)
            continue
        if in_table:
            if s.startswith("|---") or _is_md_separator_row(cells):
                continue
            if len(cells) >= 5:
                id_idx = col_map.get("id", 0)
                sev_idx = col_map.get("severity", 1)
                loc_idx = col_map.get("location", 2)
                prob_idx = col_map.get("problem", 3)
                prop_idx = col_map.get("proposed_action")
                dec_idx = col_map.get("decision")

                problem_full = cells[prob_idx] if prob_idx < len(cells) else ""
                problem_text, inline_action = _extract_inline_proposal(problem_full)
                explicit_action = (
                    cells[prop_idx].strip()
                    if prop_idx is not None and prop_idx < len(cells)
                    else ""
                )
                if explicit_action.lower() in _PLACEHOLDER_ACTIONS:
                    explicit_action = ""

                findings.append(
                    {
                        "id": cells[id_idx] if id_idx < len(cells) else "",
                        "severity": cells[sev_idx] if sev_idx < len(cells) else "",
                        "location": cells[loc_idx] if loc_idx < len(cells) else "",
                        "problem": problem_text,
                        "proposed_action": explicit_action or inline_action,
                        "decision": (
                            cells[dec_idx]
                            if dec_idx is not None and dec_idx < len(cells)
                            else ""
                        ),
                    }
                )

    if str(result.get("kind") or "").strip().lower() != "principal" and any(
        not f["proposed_action"] for f in findings
    ):
        fallback_maps = [
            _parse_fix_plan_actions(
                review_file.parent / f"fix_plan_round{round_to_extract}.md"
            ),
            _parse_fix_plan_actions(
                review_file.parent / f"fix_plan_round_{round_to_extract}.md"
            ),
            _parse_fix_plan_actions(
                review_file.parent / "fix_plan.md", expected_round=round_to_extract
            ),
        ]
        for finding in findings:
            if finding["proposed_action"]:
                continue
            fid = _extract_numeric_id(finding["id"]) or finding["id"].strip()
            for fb_map in fallback_maps:
                if fid in fb_map and fb_map[fid]:
                    finding["proposed_action"] = fb_map[fid]
                    break

    result["findings"] = findings

    # Parse raw output
    m_raw = re.search(
        r"Raw output:\s*\n+```(?:text)?\s*\n(.*?)\n```",
        round_content,
        re.DOTALL,
    )
    if not m_raw:
        m_raw = re.search(r"```(?:text)?\s*\n(.*?)\n```", round_content, re.DOTALL)
    if m_raw:
        raw_text = m_raw.group(1).strip()
        result["has_raw_output"] = bool(raw_text)
        result["raw_output_bytes"] = len(raw_text.encode("utf-8"))
        result["raw_output"] = raw_text if include_raw else ""

    watch_paths: list[Path] = [vscode_settings, review_file]
    if m_file_round is not None:
        sibling_name = (
            "principal_review.md"
            if result["kind"] == "principal"
            else "review_results.md"
        )
        watch_paths.append(review_file.parent / sibling_name)
    watch_paths.extend(
        [
            review_file.parent / f"fix_plan_round{round_to_extract}.md",
            review_file.parent / f"fix_plan_round_{round_to_extract}.md",
            review_file.parent / "fix_plan.md",
        ]
    )
    with contextlib.suppress(OSError):
        watch_paths.extend(sorted(review_file.parent.glob("fix_plan_round*.md")))
    deduped_watch_paths = list(dict.fromkeys(watch_paths))
    watch_sigs = tuple((p, _file_stat_sig(p)) for p in deduped_watch_paths)
    with _REVIEW_PARSE_CACHE_LOCK:
        if len(_REVIEW_PARSE_CACHE) >= _REVIEW_PARSE_CACHE_MAX:
            _REVIEW_PARSE_CACHE.pop(next(iter(_REVIEW_PARSE_CACHE)), None)
        _REVIEW_PARSE_CACHE[cache_key] = (watch_sigs, copy.deepcopy(result))

    return result


_PIC_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")
_EPIC_SLUG_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")
_PIC_SLOT_SUFFIX_RE = re.compile(r"-slot-\d+$")
_PIC_LINE_RE = re.compile(
    r"^(-\s+\*\*(?:PIC(?:\s*/\s*Assigned\s+Profile)?|Profile|Assigned Profile|Người phụ trách(?: \(PIC\))?)\*\*:\s*)([^\n]+)$",
    re.MULTILINE | re.IGNORECASE,
)
_PIC_SKIP_PREFIXES = (
    "task_",
    "bdd_scenarios",
    "principal_review",
    "review_results",
    "review_round_",
    "fix_plan_",
    "manual_smoke_checklist",
)


def _norm_epic_slug(slug: str) -> str:
    """Normalize epic slug for cross-convention dash/underscore matching."""
    return slug.strip().lower().replace("_", "-")


def _atomic_write_text(target: Path, content: str) -> None:
    """Atomically write UTF-8 text via sibling temporary file, fsync, and os.replace."""
    if target.exists() and not os.access(target, os.W_OK):
        raise PermissionError(f"Permission denied: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target)
        tmp_path = None
    finally:
        if tmp_path is not None and tmp_path.exists():
            with contextlib.suppress(OSError):
                tmp_path.unlink()


def _format_updated_path(target: Path, repo_dir: Path) -> str:
    """Format updated file path relative to repo_dir when contained, else absolute."""
    try:
        return str(target.resolve().relative_to(repo_dir.resolve()))
    except ValueError:
        return str(target.resolve())


def _discover_pic_worktrees(
    repo_dir: Path,
    epic_slug: str,
    workspace_root: Path | None = None,
) -> list[Path]:
    """Discover all matching git worktrees and `.worktrees/<slug>*` directories for epic_slug."""
    target_norm = _norm_epic_slug(epic_slug)
    repo_resolved = repo_dir.resolve()
    ws_resolved = (
        workspace_root.resolve() if workspace_root is not None else repo_resolved
    )
    wt_root = repo_dir / ".worktrees"
    worktrees: list[Path] = []
    seen: set[Path] = set()

    def _add_if_matches(
        candidate: Path,
        branch_name: str | None = None,
        *,
        is_dot_worktree: bool = False,
    ) -> None:
        dir_base = _PIC_SLOT_SUFFIX_RE.sub("", candidate.name.strip())
        dir_match = _norm_epic_slug(dir_base) == target_norm
        branch_match = False
        if branch_name:
            clean_branch = branch_name.removeprefix("refs/heads/")
            m_br = re.match(r"(?:epic|feat)/([a-zA-Z0-9_\-]+)", clean_branch)
            if m_br:
                br_base = _PIC_SLOT_SUFFIX_RE.sub("", m_br.group(1))
                branch_match = _norm_epic_slug(br_base) == target_norm

        is_in_dot_wt = is_dot_worktree or (
            candidate == wt_root or wt_root in candidate.parents
        )
        if not dir_match and not branch_match:
            if (
                is_in_dot_wt
                and candidate.is_symlink()
                and not candidate.resolve().is_relative_to(repo_resolved)
            ):
                if (candidate.resolve() / ".devtool" / "epic" / epic_slug).exists():
                    raise ValueError(
                        f"Worktree symlink escapes repository boundary: {candidate}"
                    )
            return

        if not (candidate.exists() or candidate.is_symlink()):
            return
        boundary = repo_resolved if is_in_dot_wt else ws_resolved
        resolved = _assert_contained(candidate, boundary, "Worktree")
        if not candidate.is_dir() or resolved == repo_resolved or resolved in seen:
            return
        seen.add(resolved)
        worktrees.append(candidate)

    with contextlib.suppress(OSError, subprocess.SubprocessError):
        proc = subprocess.run(
            ["git", "-C", str(repo_dir), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0:
            for block in proc.stdout.strip().split("\n\n"):
                wt_line = ""
                branch_line: str | None = None
                for raw in block.splitlines():
                    stripped = raw.strip()
                    if stripped.startswith("worktree "):
                        wt_line = stripped[9:].strip()
                    elif stripped.startswith("branch "):
                        branch_line = stripped[7:].strip()
                if wt_line:
                    _add_if_matches(Path(wt_line), branch_line)

    if wt_root.exists() or wt_root.is_symlink():
        _assert_contained(wt_root, repo_resolved, ".worktrees directory")
    if wt_root.is_dir():
        with contextlib.suppress(OSError):
            for entry in sorted(wt_root.iterdir()):
                if not entry.name.startswith(".") and (
                    entry.is_dir() or entry.is_symlink()
                ):
                    _add_if_matches(entry, is_dot_worktree=True)

    return worktrees


def _extract_task_frontmatter_epic(content: str) -> str | None:
    """Extract optional `epic` field from YAML frontmatter without external dependencies."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        s = line.strip()
        if s == "---":
            break
        if s.lower().startswith("epic:"):
            return s.split(":", 1)[1].strip().strip("'\"")
    return None


def _update_markdown_pic(content: str, new_pic: str, *, is_handoff: bool) -> str | None:
    """Return updated markdown with PIC replaced or inserted, or None if unchanged."""
    if _PIC_LINE_RE.search(content):
        return _PIC_LINE_RE.sub(rf"\g<1>`{new_pic}`", content)

    anchor_patterns: list[re.Pattern[str]] = [
        re.compile(
            r"^(-\s+\*\*(?:Epic name|Tên Epic|Epic|Epic Directory)\*\*:[^\n]+)$",
            re.MULTILINE | re.IGNORECASE,
        )
    ]
    if is_handoff:
        anchor_patterns.extend(
            [
                re.compile(
                    r"^(-\s+\*\*Base branch\*\*:[^\n]+)$", re.MULTILINE | re.IGNORECASE
                ),
                re.compile(
                    r"^(-\s+\*\*Packaged\*\*:[^\n]+)$", re.MULTILINE | re.IGNORECASE
                ),
                re.compile(r"^(##\s+Status\s*)$", re.MULTILINE | re.IGNORECASE),
            ]
        )
    for pattern in anchor_patterns:
        m = pattern.search(content)
        if m:
            pos = m.end()
            return content[:pos] + f"\n- **PIC**: `{new_pic}`" + content[pos:]

    lines = content.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith("# "):
            lines.insert(idx + 1, f"\n- **PIC**: `{new_pic}`")
            trailing = "\n" if content.endswith("\n") else ""
            return "\n".join(lines) + trailing
    return None


def _update_task_frontmatter_pic(content: str, new_pic: str) -> str | None:
    """Update `pic:`/`assigned:` frontmatter in a task file, or insert `pic:`."""
    if not content.startswith("---"):
        return None
    fm_end = content.find("---", 3)
    if fm_end == -1:
        return None
    fm_text = content[3:fm_end]
    body_text = content[fm_end:]
    if re.search(r"^(pic|assigned):\s*.*$", fm_text, re.MULTILINE):
        new_fm = re.sub(
            r"^(pic|assigned):\s*.*$",
            f'pic: "{new_pic}"',
            fm_text,
            flags=re.MULTILINE,
        )
    elif fm_text.startswith("\n"):
        new_fm = f'\npic: "{new_pic}"' + fm_text
    else:
        new_fm = f'\npic: "{new_pic}"\n' + fm_text
    return f"---{new_fm}{body_text}"


def _is_pic_hld_or_spec(doc: Path, epic_slug: str) -> bool:
    """Return True if doc is the epic HLD or design spec (never review/BDD/smoke prose)."""
    lower_name = doc.name.lower()
    if lower_name.endswith(".vi.md"):
        return False
    if any(lower_name.startswith(prefix) for prefix in _PIC_SKIP_PREFIXES):
        return False
    if lower_name == "handoff.md" or "evidence" in lower_name:
        return False
    return (
        lower_name in (f"{epic_slug.lower()}.md", f"{epic_slug.lower()}.en.md")
        or "design" in lower_name
    )


def _normalize_wt_slug(slug: str) -> str:
    return re.sub(r"[-_]+", "_", str(slug or "").strip().lower()).strip("_")


def _cleanup_epic_worktrees_if_clean(
    repo_path: Path,
    epic_slug: str,
) -> dict[str, Any]:
    """Safely remove clean epic worktrees (and worker slots) while preserving git branches and dirty worktrees."""
    result: dict[str, Any] = {"removed": [], "skipped_dirty": [], "errors": []}
    repo_resolved = repo_path.resolve()
    allowed_wt_roots = (
        (repo_resolved / ".worktrees").resolve(),
        (repo_resolved / "worktrees").resolve(),
    )
    norm_slug = _normalize_wt_slug(epic_slug)
    if not norm_slug:
        return result

    wt_list_proc = subprocess.run(
        ["git", "-C", str(repo_resolved), "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    if wt_list_proc.returncode != 0:
        return result

    candidates: list[Path] = []
    for line in wt_list_proc.stdout.splitlines():
        if not line.startswith("worktree "):
            continue
        raw_wt = line[len("worktree ") :].strip()
        if not raw_wt:
            continue
        wt_path = Path(raw_wt).resolve()
        if wt_path == repo_resolved:
            continue
        if not any(wt_path.is_relative_to(wt_root) for wt_root in allowed_wt_roots):
            continue
        norm_name = _normalize_wt_slug(wt_path.name)
        if norm_name == norm_slug or norm_name.startswith(f"{norm_slug}_slot_"):
            candidates.append(wt_path)

    # Remove ephemeral slot worktrees before the primary epic worktree
    candidates.sort(
        key=lambda p: (
            0 if "_slot_" in _normalize_wt_slug(p.name) else 1,
            p.name,
        )
    )

    for wt_path in candidates:
        if not wt_path.exists():
            continue
        status_proc = subprocess.run(
            ["git", "-C", str(wt_path), "status", "--porcelain", "-uall"],
            capture_output=True,
            text=True,
            check=False,
        )
        dirty_lines = [ln for ln in status_proc.stdout.splitlines() if ln.strip()]
        if status_proc.returncode != 0 or dirty_lines:
            result["skipped_dirty"].append(
                {
                    "path": str(wt_path),
                    "dirty_files": len(dirty_lines),
                }
            )
            continue

        rm_proc = subprocess.run(
            ["git", "-C", str(repo_resolved), "worktree", "remove", str(wt_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if rm_proc.returncode == 0:
            result["removed"].append(str(wt_path))
        else:
            err_msg = (rm_proc.stderr or rm_proc.stdout or "git worktree remove failed").strip()
            result["errors"].append({"path": str(wt_path), "error": err_msg})

    if result["removed"]:
        subprocess.run(
            ["git", "-C", str(repo_resolved), "worktree", "prune"],
            capture_output=True,
            text=True,
            check=False,
        )
    return result


_ACTIVE_FOLDER_PICKER_LOCK = threading.Lock()
_ACTIVE_FOLDER_PICKER_PROC: subprocess.Popen[str] | None = None
_ACTIVE_FOLDER_PICKER_CANCELLED: set[int] = set()


def _parse_window_bounds(raw: Any) -> dict[str, float] | None:
    """Validate optional browser windowBounds payload ({x, y, width, height})."""
    if not isinstance(raw, dict):
        return None
    parsed: dict[str, float] = {}
    for key in ("x", "y", "width", "height"):
        val = raw.get(key)
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            return None
        fval = float(val)
        if not math.isfinite(fval):
            return None
        parsed[key] = fval
    if parsed["width"] <= 0 or parsed["height"] <= 0:
        return None
    return parsed


def cancel_active_folder_picker() -> bool:
    """Terminate any currently open macOS folder picker subprocess."""
    global _ACTIVE_FOLDER_PICKER_PROC
    with _ACTIVE_FOLDER_PICKER_LOCK:
        proc = _ACTIVE_FOLDER_PICKER_PROC
        if proc is None:
            return False
        _ACTIVE_FOLDER_PICKER_CANCELLED.add(id(proc))
        _ACTIVE_FOLDER_PICKER_PROC = None
    if proc.poll() is not None:
        return False
    with contextlib.suppress(Exception):
        proc.terminate()
    try:
        proc.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(Exception):
            proc.kill()
        with contextlib.suppress(Exception):
            proc.wait(timeout=0.5)
    return True


def pick_folder_macos(
    prompt: str = "Select Git Repository Folder to Track",
    *,
    default_dir: Path | str | None = None,
    window_bounds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Open the native macOS NSOpenPanel folder chooser directly via JXA (fast, foreground)."""
    global _ACTIVE_FOLDER_PICKER_PROC
    if sys.platform != "darwin":
        return {
            "status": "error",
            "error": "Native Finder folder picker is only supported on macOS. Enter the folder path manually.",
        }
    default_path_str = ""
    if default_dir is not None:
        cand = Path(default_dir).expanduser()
        if cand.is_dir():
            default_path_str = str(cand.resolve())

    bounds = _parse_window_bounds(window_bounds)
    prompt_js = json.dumps(prompt)
    default_dir_js = json.dumps(default_path_str)
    bounds_js = json.dumps(bounds)
    jxa_script = (
        'ObjC.import("AppKit");\n'
        "const app = $.NSApplication.sharedApplication;\n"
        "app.setActivationPolicy($.NSApplicationActivationPolicyAccessory);\n"
        "const panel = $.NSOpenPanel.openPanel;\n"
        "panel.canChooseDirectories = true;\n"
        "panel.canChooseFiles = false;\n"
        "panel.allowsMultipleSelection = false;\n"
        "panel.canCreateDirectories = false;\n"
        'panel.prompt = "Select";\n'
        f"panel.message = {prompt_js};\n"
        f"const defaultDir = {default_dir_js};\n"
        f"const winBounds = {bounds_js};\n"
        "if (defaultDir) { panel.directoryURL = $.NSURL.fileURLWithPath(defaultDir); }\n"
        "panel.center;\n"
        "const screens = $.NSScreen.screens;\n"
        "const screenCount = Number(screens.count);\n"
        "let anchorX = null;\n"
        "let anchorY = null;\n"
        "if (winBounds && screenCount > 0) {\n"
        "  const primaryFrame = screens.objectAtIndex(0).frame;\n"
        "  const primaryTop = primaryFrame.origin.y + primaryFrame.size.height;\n"
        "  anchorX = winBounds.x + winBounds.width / 2;\n"
        "  anchorY = primaryTop - (winBounds.y + winBounds.height / 2);\n"
        "}\n"
        "const lookupPt = anchorX !== null && anchorY !== null ? { x: anchorX, y: anchorY } : $.NSEvent.mouseLocation;\n"
        "let targetFrame = null;\n"
        "for (let i = 0; i < screenCount; i++) {\n"
        "  const scr = screens.objectAtIndex(i);\n"
        "  const sf = scr.frame;\n"
        "  if (lookupPt.x >= sf.origin.x && lookupPt.x <= sf.origin.x + sf.size.width && "
        "lookupPt.y >= sf.origin.y && lookupPt.y <= sf.origin.y + sf.size.height) {\n"
        "    targetFrame = scr.visibleFrame;\n"
        "    break;\n"
        "  }\n"
        "}\n"
        "if (!targetFrame && screenCount > 0) { targetFrame = screens.objectAtIndex(0).visibleFrame; }\n"
        "if (targetFrame) {\n"
        "  const pf = panel.frame;\n"
        "  let cx = anchorX !== null ? Math.round(anchorX - pf.size.width / 2) : Math.round(targetFrame.origin.x + (targetFrame.size.width - pf.size.width) / 2);\n"
        "  let cy = anchorY !== null ? Math.round(anchorY - pf.size.height / 2) : Math.round(targetFrame.origin.y + (targetFrame.size.height - pf.size.height) / 2);\n"
        "  const maxX = Math.round(targetFrame.origin.x + targetFrame.size.width - pf.size.width);\n"
        "  const maxY = Math.round(targetFrame.origin.y + targetFrame.size.height - pf.size.height);\n"
        "  if (maxX >= targetFrame.origin.x) { cx = Math.max(Math.round(targetFrame.origin.x), Math.min(cx, maxX)); }\n"
        "  if (maxY >= targetFrame.origin.y) { cy = Math.max(Math.round(targetFrame.origin.y), Math.min(cy, maxY)); }\n"
        "  panel.setFrameOrigin($.NSMakePoint(cx, cy));\n"
        "}\n"
        "app.activateIgnoringOtherApps(true);\n"
        "panel.orderFrontRegardless;\n"
        "const resp = Number(panel.runModal);\n"
        'resp === Number($.NSModalResponseOK) && panel.URL && !panel.URL.isNil() ? ObjC.unwrap(panel.URL.path) : "";\n'
    )
    cancel_active_folder_picker()
    proc: subprocess.Popen[str] | None = None
    try:
        proc = subprocess.Popen(
            ["osascript", "-l", "JavaScript", "-e", jxa_script],
            env=build_clean_host_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        with _ACTIVE_FOLDER_PICKER_LOCK:
            _ACTIVE_FOLDER_PICKER_PROC = proc
        stdout_text, stderr_text_raw = proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        if proc is not None:
            with contextlib.suppress(Exception):
                proc.kill()
            with contextlib.suppress(Exception):
                proc.communicate(timeout=2)
        return {"status": "cancelled", "error": "Folder picker timed out."}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    finally:
        was_cancelled = False
        if proc is not None:
            with _ACTIVE_FOLDER_PICKER_LOCK:
                if _ACTIVE_FOLDER_PICKER_PROC is proc:
                    _ACTIVE_FOLDER_PICKER_PROC = None
                was_cancelled = id(proc) in _ACTIVE_FOLDER_PICKER_CANCELLED
                _ACTIVE_FOLDER_PICKER_CANCELLED.discard(id(proc))

    if was_cancelled:
        return {"status": "cancelled"}

    if proc.returncode != 0:
        stderr_text = (stderr_text_raw or "").strip()
        if "-128" in stderr_text or "user canceled" in stderr_text.lower():
            return {"status": "cancelled"}
        return {
            "status": "error",
            "error": stderr_text or "Failed to open Finder folder picker.",
        }

    chosen = (stdout_text or "").strip()
    if len(chosen) > 1 and chosen.endswith("/"):
        chosen = chosen.rstrip("/")
    if not chosen:
        return {"status": "cancelled"}
    return {"status": "ok", "path": chosen}


def set_epic_execution_state_for_repo(
    workspace_root: Path,
    repo_name: str,
    epic_slug: str,
    state: str,
    reason: str = "",
    *,
    remove_worktree: bool = False,
    projects_config_path: Path | None = None,
) -> dict[str, Any]:
    """Validate and persist an epic's UI execution state (`doing`, `pending`, or `cancelled`)."""
    if not isinstance(epic_slug, str) or not _EPIC_SLUG_RE.fullmatch(epic_slug):
        raise ValueError(f"Invalid epic slug: {epic_slug!r}")
    if (
        not isinstance(repo_name, str)
        or not repo_name
        or "/" in repo_name
        or "\\" in repo_name
        or ".." in repo_name
    ):
        raise ValueError(f"Invalid repository name: {repo_name!r}")
    norm_state = str(state or "").strip().lower()
    if norm_state not in ("doing", "pending", "cancelled"):
        raise ValueError(
            f"Invalid execution state: {state!r} (expected doing, pending, or cancelled)"
        )
    clean_reason = str(reason or "").strip()
    if norm_state in ("pending", "cancelled") and not clean_reason:
        raise ValueError(f"Reason is required when setting epic state to '{norm_state}'")

    candidate_path, boundary_root = resolve_tracked_repo_dir(
        workspace_root, repo_name, config_path=projects_config_path
    )
    repo_path = candidate_path.resolve()
    bound_resolved = boundary_root.resolve()
    try:
        repo_path.relative_to(bound_resolved)
    except ValueError as exc:
        raise ValueError(f"Repository path escapes workspace root: {repo_name!r}") from exc
    if not repo_path.is_dir():
        raise ValueError(f"Repository not found: {repo_name!r}")

    state_env = _load_state_envelope()
    if state_env is None:
        raise RuntimeError("_state_envelope module is unavailable")

    worktree_cleanup: dict[str, Any] = {
        "removed": [],
        "skipped_dirty": [],
        "errors": [],
    }
    if remove_worktree and norm_state in ("pending", "cancelled"):
        worktree_cleanup = _cleanup_epic_worktrees_if_clean(repo_path, epic_slug)

    state_env.set_epic_execution_state(
        repo_path,
        epic_slug,
        norm_state,
        reason=clean_reason,
    )
    return {
        "status": "ok",
        "repo": repo_name,
        "epic": epic_slug,
        "state": norm_state,
        "reason": clean_reason,
        "worktree_cleanup": worktree_cleanup,
    }


def assign_epic_pic(
    workspace_root: Path,
    repo_name: str,
    epic_slug: str,
    new_pic: str,
    *,
    projects_config_path: Path | None = None,
) -> dict[str, Any]:
    """Validate and atomically synchronize PIC across root and all matching worktree checkouts."""
    if not isinstance(new_pic, str) or not _PIC_NAME_RE.fullmatch(new_pic):
        raise ValueError("Invalid profile / PIC name: must match ^[a-zA-Z0-9_\\-]+$")
    if not isinstance(epic_slug, str) or not _EPIC_SLUG_RE.fullmatch(epic_slug):
        raise ValueError(f"Invalid epic slug: {epic_slug!r}")
    if (
        not isinstance(repo_name, str)
        or not repo_name
        or "/" in repo_name
        or "\\" in repo_name
        or ".." in repo_name
    ):
        raise ValueError(f"Invalid repository name: {repo_name!r}")

    candidate_path, boundary_root = resolve_tracked_repo_dir(
        workspace_root, repo_name, config_path=projects_config_path
    )
    ws_resolved = boundary_root.resolve()
    repo_dir = _assert_contained(
        candidate_path, ws_resolved, f"Repository {repo_name!r}"
    )
    if ws_resolved == workspace_root.resolve() and repo_dir == ws_resolved:
        raise ValueError(f"Repository path escapes workspace boundary: {repo_name!r}")
    if not repo_dir.is_dir():
        return {"status": "error", "error": f"Repository '{repo_name}' not found"}

    matched_worktrees = _discover_pic_worktrees(
        repo_dir, epic_slug, workspace_root=ws_resolved
    )
    checkouts: list[Path] = [repo_dir, *matched_worktrees]
    wt_root_dir = repo_dir / ".worktrees"
    slug_variants = tuple(
        dict.fromkeys(
            (epic_slug, epic_slug.replace("_", "-"), epic_slug.replace("-", "_"))
        )
    )

    # Pre-validate symlink containment across all checkouts before reading or mutating any file
    checkout_boundaries: dict[Path, Path] = {}
    for checkout in checkouts:
        in_dot_wt = checkout != repo_dir and (
            checkout.parent == wt_root_dir or wt_root_dir in checkout.parents
        )
        co_bound = _assert_contained(
            checkout,
            repo_dir if in_dot_wt else ws_resolved,
            "Checkout",
        )
        checkout_boundaries[checkout] = co_bound
        devtool_dir = checkout / ".devtool"
        epic_root = devtool_dir / "epic"
        co_epic_dir = epic_root / epic_slug
        features_dir = devtool_dir / "features"
        done_dir = features_dir / "done"
        state_dir = devtool_dir / "state"
        vscode_dir = checkout / ".vscode"
        for sub_dir, label in (
            (devtool_dir, ".devtool directory"),
            (epic_root, ".devtool/epic directory"),
            (co_epic_dir, "Epic directory"),
            (features_dir, "Features directory"),
            (done_dir, "Done features directory"),
            (state_dir, "State directory"),
            (vscode_dir, ".vscode directory"),
            (vscode_dir / "settings.json", ".vscode/settings.json"),
        ):
            if sub_dir.exists() or sub_dir.is_symlink():
                _assert_contained(sub_dir, co_bound, label)
        if co_epic_dir.is_dir():
            for md_cand in sorted(co_epic_dir.glob("*.md")):
                if md_cand.exists() or md_cand.is_symlink():
                    _assert_contained(md_cand, co_bound, "Epic markdown target")
        for fdir in (features_dir, done_dir):
            if fdir.is_dir():
                for tf_cand in sorted(fdir.glob("task_*.md")):
                    if tf_cand.exists() or tf_cand.is_symlink():
                        _assert_contained(tf_cand, co_bound, "Feature task target")
        if state_dir.is_dir():
            p_cand = state_dir / f"{epic_slug}.pipeline.json"
            if p_cand.exists() or p_cand.is_symlink():
                _assert_contained(p_cand, co_bound, "Pipeline state target")
            for sv in slug_variants:
                hb_cand = state_dir / f"{sv}.heartbeat.json"
                if hb_cand.exists() or hb_cand.is_symlink():
                    _assert_contained(hb_cand, co_bound, "Heartbeat state target")

    has_epic_anywhere = any(
        (co / ".devtool" / "epic" / epic_slug).is_dir() for co in checkouts
    )
    if not has_epic_anywhere:
        return {
            "status": "error",
            "error": f"Epic '{epic_slug}' not found in {repo_name}",
        }

    updated_files: list[str] = []
    warnings: list[str] = []
    seen_targets: set[Path] = set()
    target_norm = _norm_epic_slug(epic_slug)

    def _record_write(target: Path, new_content: str, *, boundary: Path) -> None:
        resolved = _assert_contained(target, boundary, "PIC target file")
        if resolved in seen_targets:
            return
        seen_targets.add(resolved)
        rel = _format_updated_path(target, repo_dir)
        try:
            _atomic_write_text(target, new_content)
            updated_files.append(rel)
        except OSError as exc:
            warnings.append(f"{rel}: {exc}")

    wt_resolved_set = {wt.resolve() for wt in matched_worktrees}
    hb_entries_by_slug: dict[str, list[tuple[Path, Path]]] = {}

    for checkout in checkouts:
        co_bound = checkout_boundaries[checkout]
        checkout_epic_dir = checkout / ".devtool" / "epic" / epic_slug
        if checkout_epic_dir.is_dir():
            # 1. HLD & design spec files (excluding BDD/review/fix-plan/smoke prose)
            hld_candidates: list[Path] = []
            primary_hld = epic_doc_path(checkout_epic_dir, epic_slug)
            if primary_hld is not None:
                hld_candidates.append(primary_hld)
            hld_candidates.extend(
                spec
                for spec in design_spec_paths(checkout_epic_dir)
                if spec not in hld_candidates
            )
            with contextlib.suppress(OSError):
                for doc in sorted(checkout_epic_dir.glob("*.md")):
                    if doc not in hld_candidates and _is_pic_hld_or_spec(
                        doc, epic_slug
                    ):
                        hld_candidates.append(doc)

            for hld in hld_candidates:
                if not hld.is_file():
                    continue
                _assert_contained(hld, co_bound, "HLD target")
                try:
                    content = hld.read_text(encoding="utf-8")
                except OSError as exc:
                    warnings.append(f"{_format_updated_path(hld, repo_dir)}: {exc}")
                    continue
                updated = _update_markdown_pic(content, new_pic, is_handoff=False)
                if updated is not None:
                    _record_write(hld, updated, boundary=co_bound)

            # 2. handoff.md
            handoff_file = checkout_epic_dir / "handoff.md"
            if handoff_file.is_file():
                _assert_contained(handoff_file, co_bound, "Handoff target")
                try:
                    content = handoff_file.read_text(encoding="utf-8")
                except OSError as exc:
                    warnings.append(
                        f"{_format_updated_path(handoff_file, repo_dir)}: {exc}"
                    )
                else:
                    updated = _update_markdown_pic(content, new_pic, is_handoff=True)
                    if updated is not None:
                        _record_write(handoff_file, updated, boundary=co_bound)

            # 3a. Epic task files inside .devtool/epic/<epic_slug>/
            with contextlib.suppress(OSError):
                for tf in sorted(checkout_epic_dir.glob("task_*.md")):
                    _assert_contained(tf, co_bound, "Epic task target")
                    try:
                        t_content = tf.read_text(encoding="utf-8")
                    except OSError as exc:
                        warnings.append(f"{_format_updated_path(tf, repo_dir)}: {exc}")
                        continue
                    fm_epic = _extract_task_frontmatter_epic(t_content)
                    if fm_epic and _norm_epic_slug(fm_epic) != target_norm:
                        continue
                    updated_task = _update_task_frontmatter_pic(t_content, new_pic)
                    if updated_task is not None:
                        _record_write(tf, updated_task, boundary=co_bound)

        # 3b. Task files in .devtool/features/ filtered strictly by matching epic frontmatter
        for feat_dir in (
            checkout / ".devtool" / "features",
            checkout / ".devtool" / "features" / "done",
        ):
            if not feat_dir.is_dir():
                continue
            with contextlib.suppress(OSError):
                for tf in sorted(feat_dir.glob("task_*.md")):
                    _assert_contained(tf, co_bound, "Feature task target")
                    try:
                        t_content = tf.read_text(encoding="utf-8")
                    except OSError as exc:
                        warnings.append(f"{_format_updated_path(tf, repo_dir)}: {exc}")
                        continue
                    fm_epic = _extract_task_frontmatter_epic(t_content)
                    if not fm_epic or _norm_epic_slug(fm_epic) != target_norm:
                        continue
                    updated_task = _update_task_frontmatter_pic(t_content, new_pic)
                    if updated_task is not None:
                        _record_write(tf, updated_task, boundary=co_bound)

        # 4. State pipeline JSON & collect heartbeat JSON mirrors in checkout/.devtool/state/
        state_dir = checkout / ".devtool" / "state"
        if state_dir.is_dir():
            pipeline_file = state_dir / f"{epic_slug}.pipeline.json"
            if pipeline_file.is_file():
                _assert_contained(pipeline_file, co_bound, "Pipeline state target")
                try:
                    s_data = json.loads(pipeline_file.read_text(encoding="utf-8"))
                    if isinstance(s_data, dict):
                        s_data["pic"] = new_pic
                        _record_write(
                            pipeline_file,
                            json.dumps(s_data, indent=2, ensure_ascii=False) + "\n",
                            boundary=co_bound,
                        )
                except (OSError, json.JSONDecodeError) as exc:
                    warnings.append(
                        f"{_format_updated_path(pipeline_file, repo_dir)}: {exc}"
                    )

            for slug_var in slug_variants:
                hb_path = state_dir / f"{slug_var}.heartbeat.json"
                if hb_path.is_file():
                    hb_entries_by_slug.setdefault(slug_var, []).append(
                        (co_bound, hb_path)
                    )

        # 5. Worktree-only .vscode/settings.json window.title (never root .vscode/settings.json)
        if co_bound in wt_resolved_set:
            vscode_settings = checkout / ".vscode" / "settings.json"
            if vscode_settings.is_file():
                _assert_contained(vscode_settings, co_bound, "Worktree settings target")
                try:
                    s_content = vscode_settings.read_text(encoding="utf-8")
                except OSError as exc:
                    warnings.append(
                        f"{_format_updated_path(vscode_settings, repo_dir)}: {exc}"
                    )
                else:
                    if "[@" in s_content:
                        new_s_content = re.sub(
                            r"\[@[a-zA-Z0-9_\-]+\]", f"[@{new_pic}]", s_content
                        )
                        if new_s_content != s_content:
                            _record_write(
                                vscode_settings, new_s_content, boundary=co_bound
                            )

    # Synchronize all existing heartbeat mirrors atomically under canonical state lock
    if hb_entries_by_slug:
        state_env = _load_state_envelope()
        lock_ctx = (
            state_env._state_lock(repo_dir / ".devtool")
            if state_env is not None
            else contextlib.nullcontext()
        )
        with lock_ctx:
            for slug_var, items in hb_entries_by_slug.items():
                filename = f"{slug_var}.heartbeat.json"
                max_gen = 0
                best_data: dict[str, Any] | None = None
                bad_paths: set[Path] = set()

                if state_env is not None:
                    with contextlib.suppress(Exception):
                        mirror_dts = state_env._collect_target_devtool_dirs(
                            repo_dir, filename
                        )
                        snap, snap_gen = state_env._read_highest_snapshot(
                            mirror_dts, filename, {}
                        )
                        if snap and snap_gen >= max_gen:
                            max_gen = snap_gen
                            best_data = snap

                for _co_bound, hb_file in items:
                    try:
                        parsed = json.loads(hb_file.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError) as exc:
                        warnings.append(
                            f"{_format_updated_path(hb_file, repo_dir)}: {exc}"
                        )
                        bad_paths.add(hb_file)
                        continue
                    if not isinstance(parsed, dict):
                        continue
                    raw_gen = parsed.get("generation")
                    gen = (
                        raw_gen
                        if isinstance(raw_gen, int) and not isinstance(raw_gen, bool)
                        else 0
                    )
                    if best_data is None or gen >= max_gen:
                        max_gen = max(max_gen, gen)
                        best_data = parsed

                if best_data is None:
                    continue
                next_hb = dict(best_data)
                next_hb["pic"] = new_pic
                next_hb["generation"] = max_gen + 1
                next_hb["updated_at"] = datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                )
                serialized_hb = json.dumps(next_hb, indent=2, ensure_ascii=False) + "\n"
                for co_bound, hb_file in items:
                    if hb_file in bad_paths:
                        continue
                    _record_write(hb_file, serialized_hb, boundary=co_bound)

    return {
        "status": "ok",
        "repo": repo_name,
        "epic": epic_slug,
        "pic": new_pic,
        "updated_files": updated_files,
        "updated_count": len(updated_files),
        "warnings": warnings,
    }


class TasksHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler providing REST API and dashboard serving."""

    server: TasksServer

    def _send_json(self, status_code: int, data: Any) -> None:
        raw = json.dumps(data, default=lambda o: getattr(o, "__dict__", str(o))).encode(
            "utf-8"
        )
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header(
            "Cache-Control", "no-cache, no-store, must-revalidate, max-age=0"
        )
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Focus-Repo")
        self.end_headers()

    def _resolve_repo_for_query(
        self, repo_name: str
    ) -> tuple[Path | None, tuple[int, str] | None]:
        """Validate `repo` query param syntax and containment boundary (supporting tracked external repos)."""
        if not repo_name:
            return None, (400, "Missing required 'repo' query parameter.")
        if repo_name in (".", "..") or "/" in repo_name or "\\" in repo_name:
            return None, (400, f"Invalid repository name: {repo_name}")
        ws_root = self.server.workspace_root
        cfg_path = getattr(self.server, "projects_config_path", None)
        candidate, boundary = resolve_tracked_repo_dir(
            ws_root, repo_name, config_path=cfg_path
        )
        try:
            resolved_repo = _assert_contained(candidate, boundary, "repo")
        except ValueError as exc:
            return None, (400, str(exc))
        if boundary.resolve() == ws_root.resolve() and resolved_repo == ws_root.resolve():
            return None, (400, f"Invalid repository name: {repo_name}")
        return resolved_repo, None

    @staticmethod
    def _parse_optional_positive_int(
        query: dict[str, list[str]], param: str
    ) -> tuple[int | None, str | None]:
        raw = query.get(param, [""])[0].strip()
        if not raw:
            return None, None
        try:
            val = int(raw)
        except ValueError:
            return None, f"Invalid integer for '{param}': {raw}"
        if val < 1:
            return None, f"Parameter '{param}' must be >= 1: {raw}"
        return val, None

    def _handle_epic_history(self, query: dict[str, list[str]]) -> None:
        """Serve `GET /api/epic/history` for a single repository and epic slug."""
        repo_name = query.get("repo", [""])[0].strip()
        epic_slug = query.get("epic", [""])[0].strip()
        repo_dir, repo_err = self._resolve_repo_for_query(repo_name)
        if repo_err is not None or repo_dir is None:
            status_code, msg = repo_err or (400, "Invalid repository")
            self._send_json(status_code, {"success": False, "error": msg})
            return

        if not epic_slug:
            self._send_json(
                400,
                {"success": False, "error": "Missing required 'epic' query parameter."},
            )
            return
        if not _EPIC_SLUG_RE.fullmatch(epic_slug):
            self._send_json(
                400, {"success": False, "error": f"Invalid epic slug: {epic_slug}"}
            )
            return

        round_principal, err_p = self._parse_optional_positive_int(
            query, "round_principal"
        )
        if err_p:
            self._send_json(400, {"success": False, "error": err_p})
            return
        round_cross, err_c = self._parse_optional_positive_int(query, "round_cross")
        if err_c:
            self._send_json(400, {"success": False, "error": err_c})
            return

        if not repo_dir.is_dir():
            self._send_json(
                404, {"success": False, "error": f"Repository not found: {repo_name}"}
            )
            return

        history = harvest_epic_history(repo_dir, epic_slug)
        if not history.get("exists"):
            self._send_json(
                404, {"success": False, "error": f"Epic not found: {epic_slug}"}
            )
            return

        include_raw = query.get("include_raw", ["1"])[0].strip().lower() not in (
            "0",
            "false",
            "no",
        )

        try:
            principal_rev = parse_review_results(
                repo_dir,
                active_epic=epic_slug,
                target_round=round_principal,
                kind="principal",
                strict_epic=True,
                include_raw=include_raw,
            )
        except Exception:
            principal_rev = {
                "repo": repo_dir.name,
                "epic": epic_slug,
                "round": round_principal or 1,
                "available_rounds": [1],
                "kind": "principal",
                "present": False,
                "verdict": "UNKNOWN",
                "sha": None,
                "reviewer": None,
                "model": None,
                "thinking": None,
                "theme_color": None,
                "findings": [],
                "raw_output": "",
                "has_raw_output": False,
                "raw_output_bytes": 0,
            }

        try:
            cross_rev = parse_review_results(
                repo_dir,
                active_epic=epic_slug,
                target_round=round_cross,
                kind="cross-model",
                strict_epic=True,
                include_raw=include_raw,
            )
        except Exception:
            cross_rev = {
                "repo": repo_dir.name,
                "epic": epic_slug,
                "round": round_cross or 1,
                "available_rounds": [1],
                "kind": "cross-model",
                "present": False,
                "verdict": "UNKNOWN",
                "sha": None,
                "reviewer": None,
                "model": None,
                "thinking": None,
                "theme_color": None,
                "findings": [],
                "raw_output": "",
                "has_raw_output": False,
                "raw_output_bytes": 0,
            }
        payload = {
            "success": True,
            "epic": history["epic"],
            "pipeline_telemetry": history["pipeline_telemetry"],
            "tasks": history["tasks"],
            "timeline": history["timeline"],
            "reviews": {
                "principal": principal_rev,
                "cross_model": cross_rev,
            },
            "log_completeness": history["log_completeness"],
        }
        self._send_json(200, sanitize_paths_to_tilde(payload))

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/tasks":
            query = urllib.parse.parse_qs(parsed.query)
            focus_repo = (
                query.get("repo", [""])[0].strip()
                or str(self.headers.get("X-Focus-Repo") or "").strip()
            )
            if focus_repo:
                payload = self.server.get_focus_repo_tasks_payload(focus_repo)
            else:
                payload = self.server.get_coalesced_tasks_payload()
            self._send_json(200, payload)
            return

        if path == "/api/projects":
            cfg_path = getattr(self.server, "projects_config_path", None)
            tracked = load_tracked_projects(self.server.workspace_root, cfg_path)
            config_exists = tracked is not None
            effective_projects = (
                tracked
                if tracked is not None
                else build_initial_tracked_projects(self.server.workspace_root)
            )
            suggestions = discover_untracked_workspace_repos(
                self.server.workspace_root, effective_projects
            )
            projects_payload = [
                {
                    "name": p["name"],
                    "path": p["path"],
                    "exists": Path(p["path"]).is_dir(),
                }
                for p in effective_projects
            ]
            self._send_json(
                200,
                sanitize_paths_to_tilde(
                    {
                        "status": "ok",
                        "config_exists": config_exists,
                        "workspace_root": str(self.server.workspace_root.resolve()),
                        "projects": projects_payload,
                        "suggestions": suggestions,
                    }
                ),
            )
            return

        if path == "/api/epic/history":
            self._handle_epic_history(urllib.parse.parse_qs(parsed.query))
            return

        if path == "/api/review":
            query = urllib.parse.parse_qs(parsed.query)
            repo_name = query.get("repo", [""])[0]
            repo_dir, repo_err = self._resolve_repo_for_query(repo_name)
            if repo_err is not None or repo_dir is None:
                status_code, msg = repo_err or (400, "Invalid repository")
                self._send_json(status_code, {"success": False, "error": msg})
                return
            active_epic = query.get("epic", [None])[0]
            kind = query.get("kind", [None])[0]
            strict_epic = query.get("strict", [""])[0].strip().lower() in (
                "1",
                "true",
                "yes",
            )
            include_raw = query.get("include_raw", ["1"])[0].strip().lower() not in (
                "0",
                "false",
                "no",
            )
            target_round_str = query.get("round", [None])[0]
            target_round: int | None = None
            if target_round_str:
                with contextlib.suppress(ValueError):
                    target_round = int(target_round_str)
            data = parse_review_results(
                repo_dir,
                active_epic,
                target_round,
                kind,
                strict_epic=strict_epic,
                include_raw=include_raw,
            )
            self._send_json(200, sanitize_paths_to_tilde(data))
            return

        if path == "/api/profiles":
            profiles: list[str] = []
            with contextlib.suppress(Exception):
                profiles = discover_antigravity_profiles(get_real_home())
            self._send_json(200, {"profiles": profiles})
            return

        if path == "/api/status":
            self._send_json(
                200,
                {
                    "status": "running",
                    "pid": os.getpid(),
                    "port": self.server.server_port,
                    "workspace_root": sanitize_paths_to_tilde(
                        str(self.server.workspace_root)
                    ),
                    "code_fingerprint": getattr(
                        self.server,
                        "code_fingerprint",
                        compute_server_code_fingerprint(),
                    ),
                },
            )
            return

        if path == "/":
            dashboard_html = (
                Path(__file__).resolve().parent.parent
                / "dashboard"
                / "tasks_dashboard.html"
            )
            if dashboard_html.is_file():
                content = dashboard_html.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header(
                    "Cache-Control", "no-cache, no-store, must-revalidate, max-age=0"
                )
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                self.end_headers()
                self.wfile.write(content)
                return

            fallback = b"<!DOCTYPE html><html><body><h1>Check Tasks Server Running</h1></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(fallback)))
            self.end_headers()
            self.wfile.write(fallback)
            return

        self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            payload = {}

        if path == "/api/projects/browse/cancel":
            cancelled = cancel_active_folder_picker()
            with contextlib.suppress(BrokenPipeError, ConnectionResetError):
                self._send_json(200, {"status": "ok", "cancelled": cancelled})
            return

        if path == "/api/projects/browse":
            prompt = str(
                payload.get("prompt") or "Select Git Repository Folder to Track"
            )
            window_bounds = _parse_window_bounds(payload.get("windowBounds"))
            result = pick_folder_macos(
                prompt,
                default_dir=self.server.workspace_root,
                window_bounds=window_bounds,
            )
            status_code = 200 if result.get("status") in ("ok", "cancelled") else 500
            with contextlib.suppress(BrokenPipeError, ConnectionResetError):
                self._send_json(status_code, sanitize_paths_to_tilde(result))
            return

        if path == "/api/projects/add":
            raw_path = str(payload.get("path") or "").strip()
            raw_index = payload.get("index")
            idx_val: int | None = None
            if isinstance(raw_index, int) and not isinstance(raw_index, bool):
                idx_val = raw_index
            cfg_path = getattr(self.server, "projects_config_path", None)
            try:
                result = add_tracked_project(
                    self.server.workspace_root,
                    raw_path,
                    config_path=cfg_path,
                    index=idx_val,
                )
            except ValueError as exc:
                msg = str(exc)
                code = 409 if "already tracked" in msg.lower() else 400
                self._send_json(code, {"status": "error", "error": msg})
                return
            self.server.invalidate_warmup_cache()
            self._send_json(200, sanitize_paths_to_tilde(result))
            return

        if path == "/api/projects/remove":
            repo_name = str(payload.get("name") or "").strip()
            raw_path = str(payload.get("path") or "").strip()
            cfg_path = getattr(self.server, "projects_config_path", None)
            try:
                result = remove_tracked_project(
                    self.server.workspace_root,
                    name=repo_name,
                    path=raw_path,
                    config_path=cfg_path,
                )
            except ValueError as exc:
                msg = str(exc)
                code = 404 if "not found" in msg.lower() else 400
                self._send_json(code, {"status": "error", "error": msg})
                return
            self.server.invalidate_warmup_cache()
            self._send_json(200, sanitize_paths_to_tilde(result))
            return

        if path in ("/api/agy-pool/priority", "/api/agy-pool/settings"):
            profile_name = str(payload.get("profile") or "").strip()
            raw_priority = payload.get("priority")
            raw_max_concurrent = payload.get("max_concurrent")
            if path == "/api/agy-pool/priority" and (
                not profile_name or raw_priority is None
            ):
                self._send_json(
                    400,
                    {
                        "status": "error",
                        "error": "Missing required fields: profile, priority",
                    },
                )
                return
            if not profile_name or (
                raw_priority is None and raw_max_concurrent is None
            ):
                self._send_json(
                    400,
                    {
                        "status": "error",
                        "error": "Missing required fields: profile and priority or max_concurrent",
                    },
                )
                return
            try:
                result = update_agy_profile_settings(
                    profile_name,
                    priority=raw_priority,
                    max_concurrent=raw_max_concurrent,
                    real_home=getattr(self.server, "agy_pool_real_home", None),
                )
            except ValueError as exc:
                msg = str(exc)
                code = 404 if "not in the pool" in msg.lower() else 400
                self._send_json(code, {"status": "error", "error": msg})
                return
            except RuntimeError as exc:
                self._send_json(500, {"status": "error", "error": str(exc)})
                return
            self.server.invalidate_warmup_cache()
            self._send_json(200, result)
            return

        if path == "/api/epic/execution-state":
            repo_name = payload.get("repo", "")
            epic_slug = payload.get("epic", "")
            state = payload.get("state", "")
            reason = payload.get("reason", "")
            remove_worktree = bool(payload.get("remove_worktree", False))

            if not repo_name or not epic_slug or not state:
                self._send_json(
                    400,
                    {
                        "status": "error",
                        "error": "Missing required fields: repo, epic, state",
                    },
                )
                return

            try:
                result = set_epic_execution_state_for_repo(
                    self.server.workspace_root,
                    repo_name,
                    epic_slug,
                    state,
                    reason=reason,
                    remove_worktree=remove_worktree,
                    projects_config_path=getattr(
                        self.server, "projects_config_path", None
                    ),
                )
            except (ValueError, RuntimeError) as exc:
                self._send_json(400, {"status": "error", "error": str(exc)})
                return

            self._send_json(200, result)
            return

        if path == "/api/epic/pic":
            repo_name = payload.get("repo", "")
            epic_slug = payload.get("epic", "")
            pic = payload.get("pic", "")

            if not repo_name or not epic_slug or not pic:
                self._send_json(
                    400,
                    {
                        "status": "error",
                        "error": "Missing required fields: repo, epic, pic",
                    },
                )
                return

            try:
                result = assign_epic_pic(
                    self.server.workspace_root,
                    repo_name,
                    epic_slug,
                    pic,
                    projects_config_path=getattr(
                        self.server, "projects_config_path", None
                    ),
                )
            except ValueError as exc:
                self._send_json(400, {"status": "error", "error": str(exc)})
                return

            if result.get("status") == "ok":
                self._send_json(200, result)
            else:
                self._send_json(400, result)
            return

        if path == "/api/launch/cli":
            worktree = payload.get("worktree", "")
            profile = payload.get("profile") or "danhdue"
            if not re.match(r"^[a-zA-Z0-9_\-]+$", profile):
                self._send_json(400, {"error": "Invalid profile name"})
                return
            cmd = build_cli_launch_command(worktree, profile)
            try:
                subprocess.Popen(
                    cmd,
                    env=build_clean_host_env(),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                    close_fds=True,
                )
            except Exception as e:
                self._send_json(500, {"error": str(e), "command": cmd})
                return
            self._send_json(200, {"status": "ok", "command": cmd})
            return

        if path == "/api/launch/ide":
            worktree = payload.get("worktree", "")
            profile = payload.get("profile") or "danhdue"
            if not re.match(r"^[a-zA-Z0-9_\-]+$", profile):
                self._send_json(400, {"error": "Invalid profile name"})
                return

            cmd = build_ide_launch_command(worktree, profile)
            try:
                subprocess.Popen(
                    cmd,
                    env=build_clean_host_env(),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                    close_fds=True,
                )
            except Exception as e:
                self._send_json(500, {"error": str(e), "command": cmd})
                return
            self._send_json(200, {"status": "ok", "action": "launched", "command": cmd})
            return

        if path == "/api/launch/quota":
            port = payload.get("port") or DEFAULT_QUOTA_PORT
            try:
                port = int(port)
            except (ValueError, TypeError):
                port = DEFAULT_QUOTA_PORT
            res = launch_quota_server(self.server.workspace_root, port=port)
            status_code = 200 if res.get("status") == "ok" else 500
            self._send_json(status_code, res)
            return

        if path == "/api/shutdown":
            self._send_json(200, {"status": "shutting_down"})

            def _shutdown_server() -> None:
                self.server.shutdown()
                with contextlib.suppress(OSError):
                    self.server.pid_file.unlink(missing_ok=True)

            threading.Thread(target=_shutdown_server, daemon=True).start()
            return

        self.send_error(404, "Not Found")

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress standard HTTP server access logs to keep output clean."""


class TasksServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Threaded HTTP daemon server with port collision detection and PID tracking."""

    daemon_threads = True

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = DEFAULT_PORT,
        workspace_root: Path | None = None,
        pid_file: Path = DEFAULT_PID_FILE,
        projects_config_path: Path | None = None,
        warmup_on_start: bool = False,
        agy_pool_real_home: Path | None = None,
    ) -> None:
        self.workspace_root = workspace_root or Path(get_real_home()) / "AllProjects"
        self.projects_config_path = resolve_projects_config_path(
            self.workspace_root, projects_config_path
        )
        self.agy_pool_real_home = agy_pool_real_home
        self.pid_file = pid_file
        self.code_fingerprint = compute_server_code_fingerprint()
        self.warmup_on_start = warmup_on_start
        self._tasks_inflight_lock = threading.Lock()
        self._tasks_inflight_event: threading.Event | None = None
        self._tasks_inflight_result: Any = None
        self._tasks_inflight_error: BaseException | None = None
        self._warmup_payload: Any = None
        self._warmup_expires_at: float = 0.0
        available_port = find_available_port(port)
        super().__init__((host, available_port), TasksHandler)

    def invalidate_warmup_cache(self) -> None:
        """Clear any startup warmup snapshot immediately after a mutating API call."""
        with self._tasks_inflight_lock:
            self._warmup_payload = None
            self._warmup_expires_at = 0.0

    def get_focus_repo_tasks_payload(self, repo_name: str) -> Any:
        """Fast single-repo cold-start scan for the active tab, triggering background full warmup."""
        with self._tasks_inflight_lock:
            if (
                self._warmup_payload is not None
                and time.monotonic() < self._warmup_expires_at
            ):
                cached = self._warmup_payload
                self._warmup_payload = None
                self._warmup_expires_at = 0.0
                return cached

        clean_name = str(repo_name or "").strip()
        if (
            not clean_name
            or clean_name in (".", "..")
            or "/" in clean_name
            or "\\" in clean_name
        ):
            return self.get_coalesced_tasks_payload()

        candidate, boundary = resolve_tracked_repo_dir(
            self.workspace_root, clean_name, config_path=self.projects_config_path
        )
        try:
            resolved_repo = _assert_contained(candidate, boundary, "repo")
        except ValueError:
            return self.get_coalesced_tasks_payload()
        if not resolved_repo.is_dir() or not (
            (resolved_repo / ".git").exists() or (resolved_repo / ".devtool").is_dir()
        ):
            return self.get_coalesced_tasks_payload()

        tracked = load_tracked_projects(self.workspace_root, self.projects_config_path)
        if tracked is not None and not any(p["name"] == clean_name for p in tracked):
            return self.get_coalesced_tasks_payload()

        meta = scan_repo(resolved_repo)
        meta.name = clean_name
        total_tasks = meta.task_progress.total_tasks
        total_done = meta.task_progress.done_tasks
        dirty_wt = sum(1 for wt in meta.worktrees if wt.is_dirty)
        graph = DashboardGraph(
            workspace_root=str(self.workspace_root.resolve()),
            scanned_at=datetime.now().isoformat(),
            repos=[meta],
            metrics_row={
                "total_repos": len(tracked) if tracked is not None else 1,
                "active_epics": 1 if meta.active_epic else 0,
                "dirty_worktrees": dirty_wt,
                "total_tasks": total_tasks,
                "done_tasks": total_done,
                "overall_percentage": round((total_done / total_tasks * 100), 1)
                if total_tasks > 0
                else 0.0,
            },
            available_profiles=discover_antigravity_profiles(),
            tracked_projects=tracked,
        )
        payload = sanitize_paths_to_tilde(graph)
        if isinstance(payload, dict):
            payload["partial"] = True
            payload["focus_repo"] = clean_name

        # Warm the full multi-repo snapshot in background so the follow-up hydration is instant
        if self.warmup_on_start:
            threading.Thread(target=self._run_startup_warmup, daemon=True).start()
        return payload

    def get_coalesced_tasks_payload(self, *, store_warmup_ttl: float = 0.0) -> Any:
        """Coalesce concurrent /api/tasks requests into a single in-flight harvest."""
        with self._tasks_inflight_lock:
            if (
                store_warmup_ttl <= 0.0
                and self._warmup_payload is not None
                and time.monotonic() < self._warmup_expires_at
            ):
                cached = self._warmup_payload
                self._warmup_payload = None
                self._warmup_expires_at = 0.0
                return cached
            existing_event = self._tasks_inflight_event
            if existing_event is None:
                my_event = threading.Event()
                self._tasks_inflight_event = my_event
                self._tasks_inflight_result = None
                self._tasks_inflight_error = None
                is_leader = True
            else:
                my_event = existing_event
                is_leader = False

        if not is_leader:
            my_event.wait()
            if self._tasks_inflight_error is not None:
                raise self._tasks_inflight_error
            return self._tasks_inflight_result

        try:
            graph = harvest_dashboard_graph(
                self.workspace_root,
                projects_config_path=self.projects_config_path,
            )
            payload = sanitize_paths_to_tilde(graph)
            with self._tasks_inflight_lock:
                self._tasks_inflight_result = payload
                if store_warmup_ttl > 0.0:
                    self._warmup_payload = payload
                    self._warmup_expires_at = time.monotonic() + store_warmup_ttl
            return payload
        except BaseException as exc:
            self._tasks_inflight_error = exc
            raise
        finally:
            with self._tasks_inflight_lock:
                if self._tasks_inflight_event is my_event:
                    self._tasks_inflight_event = None
            my_event.set()

    def serve_forever(self, poll_interval: float = 0.5) -> None:
        meta_file = pid_meta_path(self.pid_file)
        try:
            self.pid_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                fd = os.open(
                    str(self.pid_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644
                )
                with open(fd, "w", encoding="utf-8") as f:
                    f.write(f"{os.getpid()}\n")
            except FileExistsError:
                self.pid_file.write_text(f"{os.getpid()}\n", encoding="utf-8")
            with contextlib.suppress(OSError):
                meta_file.write_text(
                    json.dumps(
                        {
                            "pid": os.getpid(),
                            "port": self.server_port,
                            "workspace_root": str(self.workspace_root.resolve()),
                            "code_fingerprint": self.code_fingerprint,
                        }
                    ),
                    encoding="utf-8",
                )
            if self.warmup_on_start:
                threading.Thread(
                    target=self._run_startup_warmup,
                    daemon=True,
                ).start()
            super().serve_forever(poll_interval)
        finally:
            with contextlib.suppress(OSError):
                self.pid_file.unlink(missing_ok=True)
                meta_file.unlink(missing_ok=True)

    def _run_startup_warmup(self) -> None:
        with contextlib.suppress(Exception):
            self.get_coalesced_tasks_payload(store_warmup_ttl=5.0)

    def server_close(self) -> None:
        with contextlib.suppress(OSError):
            self.pid_file.unlink(missing_ok=True)
            pid_meta_path(self.pid_file).unlink(missing_ok=True)
        super().server_close()


def _terminate_pid(pid: int) -> bool:
    """Terminate a local process by PID using SIGTERM with SIGKILL fallback."""
    if pid <= 0 or pid == os.getpid():
        return False
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return False
    terminated = False
    for _ in range(20):
        threading.Event().wait(0.1)
        try:
            os.kill(pid, 0)
        except OSError:
            terminated = True
            break
    if not terminated:
        with contextlib.suppress(OSError):
            os.kill(pid, signal.SIGKILL)
            threading.Event().wait(0.2)
    return True


def probe_running_server_on_port(port: int) -> dict[str, Any] | None:
    """Query /api/status on localhost:port; return status dict if a check-tasks daemon responds."""
    with contextlib.suppress(OSError, ValueError, TimeoutError):
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/status")
        with urllib.request.urlopen(req, timeout=0.6) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                if (
                    isinstance(data, dict)
                    and data.get("status") == "running"
                    and isinstance(data.get("pid"), int)
                ):
                    return data
    return None


def _is_status_payload_stale(
    status_data: dict[str, Any],
    expected_workspace: Path,
    expected_fingerprint: str | None = None,
) -> bool:
    """Return True when a live /api/status response comes from older code or another workspace."""
    expected_fp = expected_fingerprint or compute_server_code_fingerprint()
    remote_fp = status_data.get("code_fingerprint")
    if not remote_fp or remote_fp != expected_fp:
        return True
    remote_ws = str(status_data.get("workspace_root") or "").strip()
    if remote_ws:
        expanded = (
            Path(get_real_home()) / remote_ws[2:]
            if remote_ws.startswith("~/")
            else (Path(get_real_home()) if remote_ws == "~" else Path(remote_ws))
        )
        with contextlib.suppress(OSError):
            if expanded.resolve() != expected_workspace.resolve():
                return True
    return False


def stop_server_on_port(port: int) -> bool:
    """Stop an orphan check-tasks daemon listening on localhost:port even if its PID file is missing."""
    info = probe_running_server_on_port(port)
    if not info:
        return False
    remote_pid = int(info["pid"])
    with contextlib.suppress(OSError, ValueError, TimeoutError):
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/shutdown",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=0.8):
            pass
    for _ in range(10):
        try:
            os.kill(remote_pid, 0)
        except OSError:
            return True
        threading.Event().wait(0.05)
    return _terminate_pid(remote_pid)


def stop_server(
    pid_file: Path = DEFAULT_PID_FILE, port: int | None = None
) -> bool:
    """Stop the running background server by PID file and optionally reclaim an orphan on port."""
    stopped = False
    pid = get_running_pid(pid_file)
    meta_file = pid_meta_path(pid_file)
    if pid:
        stopped = _terminate_pid(pid)
    with contextlib.suppress(OSError):
        pid_file.unlink(missing_ok=True)
        meta_file.unlink(missing_ok=True)
    if port is not None and stop_server_on_port(port):
        stopped = True
    return stopped


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for managing the tasks server daemon."""
    parser = argparse.ArgumentParser(
        description="Check-Tasks HTTP daemon server and REST API."
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="Port to listen on"
    )
    parser.add_argument(
        "--daemon", action="store_true", help="Run as background daemon"
    )
    parser.add_argument(
        "--restart", action="store_true", help="Restart running server daemon"
    )
    parser.add_argument(
        "--stop", action="store_true", help="Stop running server daemon"
    )
    parser.add_argument(
        "--status", action="store_true", help="Check running server status"
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(get_real_home()) / "AllProjects",
        help="Root workspace containing repositories",
    )
    args = parser.parse_args(argv)

    pid_file = DEFAULT_PID_FILE

    if args.stop:
        stopped_pid = stop_server(pid_file)
        stopped_port = stop_server_on_port(args.port)
        if stopped_pid or stopped_port:
            print("Tasks server stopped.")
            return 0
        print("Tasks server is not running.")
        return 1

    if args.status:
        pid = get_running_pid(pid_file)
        if pid:
            print(f"Tasks server running (PID {pid}).")
            return 0
        port_info = probe_running_server_on_port(args.port)
        if port_info:
            print(
                f"Tasks server running on port {args.port} (PID {port_info['pid']}, untracked PID file)."
            )
            return 0
        print("Tasks server is stopped.")
        return 1

    existing_pid = get_running_pid(pid_file)
    if existing_pid:
        if args.restart or is_running_server_stale(
            existing_pid, pid_file, args.workspace_root, args.port
        ):
            print(f"Restarting stale tasks server (PID {existing_pid})...")
            stop_server(pid_file)
            stop_server_on_port(args.port)
        else:
            port_info = probe_running_server_on_port(args.port)
            if port_info and int(port_info["pid"]) != existing_pid:
                print(
                    f"Reclaiming orphan tasks server on port {args.port} (PID {port_info['pid']})..."
                )
                stop_server(pid_file)
                stop_server_on_port(args.port)
            else:
                print(f"Tasks server already running (PID {existing_pid}).")
                return 0
    else:
        port_info = probe_running_server_on_port(args.port)
        if port_info:
            if args.restart or _is_status_payload_stale(port_info, args.workspace_root):
                print(
                    f"Reclaiming stale orphan tasks server on port {args.port} (PID {port_info['pid']})..."
                )
                stop_server_on_port(args.port)
            else:
                print(
                    f"Tasks server already running on port {args.port} (PID {port_info['pid']})."
                )
                return 0

    if args.daemon:
        # Spawn child process in background
        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--port",
            str(args.port),
            "--workspace-root",
            str(args.workspace_root),
        ]
        proc = subprocess.Popen(
            cmd,
            env=build_clean_host_env(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
        _wait_for_daemon_ready(args.port)
        print(f"Tasks server started in background (PID {proc.pid}, port {args.port}).")
        return 0

    server = TasksServer(
        host="127.0.0.1",
        port=args.port,
        workspace_root=args.workspace_root,
        pid_file=pid_file,
        warmup_on_start=True,
    )
    print(f"Tasks server listening on http://127.0.0.1:{server.server_port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down tasks server...")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
