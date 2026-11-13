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
import dataclasses
from datetime import datetime, timezone
import http.server
import json
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
from typing import Any
import urllib.parse

# Ensure check_tasks is importable
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from check_tasks import (
        DashboardGraph,
        discover_antigravity_profiles,
        harvest_dashboard_graph,
    )
except ImportError:
    pass

DEFAULT_PORT = 8766
DEFAULT_QUOTA_PORT = 8765
DEFAULT_PID_FILE = Path("/tmp/agy_tasks_server.pid")


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
        return None


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

        req = urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/status", timeout=1.0
        )
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


def parse_review_results(
    repo_dir: Path,
    active_epic: str | None = None,
    target_round: int | None = None,
    kind: str | None = None,
) -> dict[str, Any]:
    """Parse persisted review findings and triage table for a repository and round."""
    result: dict[str, Any] = {
        "repo": repo_dir.name,
        "epic": active_epic,
        "round": target_round or 1,
        "available_rounds": [1],
        "kind": kind or "review",
        "verdict": "UNKNOWN",
        "sha": None,
        "reviewer": None,
        "model": None,
        "thinking": None,
        "theme_color": None,
        "findings": [],
        "raw_output": "",
    }

    # Extract repo theme color from .vscode/settings.json if present
    vscode_settings = repo_dir / ".vscode" / "settings.json"
    if vscode_settings.is_file():
        try:
            settings_json = json.loads(vscode_settings.read_text(encoding="utf-8"))
            color_customizations = settings_json.get("workbench.colorCustomizations", {})
            result["theme_color"] = (
                color_customizations.get("titleBar.activeBackground")
                or color_customizations.get("statusBar.background")
            )
        except Exception:
            pass

    candidates: list[Path] = []

    # Check dedicated worktree first, then repo_dir
    roots: list[Path] = []
    if active_epic:
        roots.extend(
            [
                repo_dir / ".worktrees" / active_epic,
                repo_dir / ".worktrees" / active_epic.replace("-", "_"),
                repo_dir / ".worktrees" / active_epic.replace("_", "-"),
            ]
        )
    roots.append(repo_dir)

    for root in [r for r in roots if r.is_dir()]:
        dt = root / ".devtool"
        if active_epic:
            epic_dir = dt / "epic" / active_epic
            if kind == "principal":
                if target_round:
                    candidates.append(
                        epic_dir / f"principal_review_round_{target_round}.md"
                    )
                candidates.extend(
                    [
                        epic_dir / "principal_review.md",
                        dt / "principal_review.md",
                    ]
                )
            elif kind == "cross-model":
                if target_round:
                    candidates.extend(
                        [
                            epic_dir / f"review_results_round_{target_round}.md",
                            epic_dir / f"review_round_{target_round}.md",
                        ]
                    )
                candidates.extend(
                    [
                        epic_dir / "review_results.md",
                        dt / "review_results.md",
                    ]
                )
            else:
                if target_round:
                    candidates.extend(
                        [
                            epic_dir / f"review_results_round_{target_round}.md",
                            epic_dir / f"review_round_{target_round}.md",
                            epic_dir / f"principal_review_round_{target_round}.md",
                        ]
                    )
                candidates.extend(
                    [
                        epic_dir / "review_results.md",
                        epic_dir / "principal_review.md",
                        dt / "review_results.md",
                        dt / "principal_review.md",
                    ]
                )
        else:
            if kind == "principal":
                if target_round:
                    candidates.append(dt / f"principal_review_round_{target_round}.md")
                candidates.append(dt / "principal_review.md")
            else:
                if target_round:
                    candidates.extend(
                        [
                            dt / f"review_results_round_{target_round}.md",
                            dt / f"review_round_{target_round}.md",
                        ]
                    )
                candidates.extend(
                    [
                        dt / "review_results.md",
                        dt / "features" / "review_results.md",
                    ]
                )

    review_file: Path | None = next((c for c in candidates if c and c.is_file()), None)
    if not review_file:
        return result

    content = review_file.read_text(encoding="utf-8")

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

    # Detect all available rounds in the file using fence-aware scanner (ignoring markdown headings inside code blocks)
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
        elif (heading_match := re.fullmatch(r"##\s+Round\s+(\d+)", line.strip())):
            parsed_rounds.append((int(heading_match.group(1)), []))
        elif parsed_rounds:
            parsed_rounds[-1][1].append(line)

    unique_rounds = sorted(list({r[0] for r in parsed_rounds}))
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
    m_raw_split = re.search(r"(?m)^(?:Raw output:|### Earlier Rounds|```)", round_content)
    table_section = round_content[:m_raw_split.start()] if m_raw_split else round_content

    # Parse 5-column triage table: | # | Severity | Location | Problem | Decision |
    lines = table_section.splitlines()
    in_table = False
    findings: list[dict[str, str]] = []
    for line in lines:
        s = line.strip()
        if s.startswith("|") and ("Severity" in s or "Mức độ" in s or "Sev" in s):
            in_table = True
            continue
        if in_table:
            if not s.startswith("|") or s.startswith("|---"):
                if not s.startswith("|"):
                    in_table = False
                continue
            raw_cells = re.split(r"(?<!\\)\|", s)
            cells = [c.strip().replace(r"\|", "|") for c in raw_cells]
            if cells and cells[0] == "":
                cells.pop(0)
            if cells and cells[-1] == "":
                cells.pop()
            if len(cells) >= 5:
                problem_full = cells[3]
                problem_text = problem_full
                proposed_action = ""
                m_prop = re.search(
                    r"(?:Proposed(?:\s+Action)?|Đề xuất):\s*(.+)$",
                    problem_full,
                    re.IGNORECASE | re.DOTALL,
                )
                if m_prop:
                    proposed_action = m_prop.group(1).strip()
                    problem_text = problem_full[:m_prop.start()].strip()

                findings.append(
                    {
                        "id": cells[0],
                        "severity": cells[1],
                        "location": cells[2],
                        "problem": problem_text,
                        "proposed_action": proposed_action,
                        "decision": cells[4],
                    }
                )
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
        result["raw_output"] = m_raw.group(1).strip()

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


def _discover_pic_worktrees(repo_dir: Path, epic_slug: str) -> list[Path]:
    """Discover all matching git worktrees and `.worktrees/<slug>*` directories for epic_slug."""
    target_norm = _norm_epic_slug(epic_slug)
    repo_resolved = repo_dir.resolve()
    worktrees: list[Path] = []
    seen: set[Path] = set()

    def _add_if_matches(candidate: Path, branch_name: str | None = None) -> None:
        if not candidate.is_dir():
            return
        resolved = candidate.resolve()
        if resolved == repo_resolved or resolved in seen:
            return
        dir_base = _PIC_SLOT_SUFFIX_RE.sub("", candidate.name.strip())
        dir_match = _norm_epic_slug(dir_base) == target_norm
        branch_match = False
        if branch_name:
            clean_branch = branch_name.removeprefix("refs/heads/")
            m_br = re.match(r"(?:epic|feat)/([a-zA-Z0-9_\-]+)", clean_branch)
            if m_br:
                br_base = _PIC_SLOT_SUFFIX_RE.sub("", m_br.group(1))
                branch_match = _norm_epic_slug(br_base) == target_norm
        if dir_match or branch_match:
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

    wt_dir = repo_dir / ".worktrees"
    if wt_dir.is_dir():
        with contextlib.suppress(OSError):
            for entry in sorted(wt_dir.iterdir()):
                if entry.is_dir() and not entry.name.startswith("."):
                    _add_if_matches(entry)

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
                re.compile(r"^(-\s+\*\*Base branch\*\*:[^\n]+)$", re.MULTILINE | re.IGNORECASE),
                re.compile(r"^(-\s+\*\*Packaged\*\*:[^\n]+)$", re.MULTILINE | re.IGNORECASE),
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
    if any(lower_name.startswith(prefix) for prefix in _PIC_SKIP_PREFIXES):
        return False
    if lower_name == "handoff.md" or "evidence" in lower_name:
        return False
    return (
        lower_name in (f"{epic_slug.lower()}.en.md", f"{epic_slug.lower()}.vi.md")
        or "design" in lower_name
    )


def assign_epic_pic(
    workspace_root: Path,
    repo_name: str,
    epic_slug: str,
    new_pic: str,
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

    ws_resolved = workspace_root.resolve()
    repo_dir = (workspace_root / repo_name).resolve()
    if not str(repo_dir).startswith(str(ws_resolved) + os.sep) and repo_dir != ws_resolved:
        raise ValueError(f"Repository path escapes workspace boundary: {repo_name!r}")
    if not repo_dir.is_dir():
        return {"status": "error", "error": f"Repository '{repo_name}' not found"}

    matched_worktrees = _discover_pic_worktrees(repo_dir, epic_slug)
    checkouts: list[Path] = [repo_dir, *matched_worktrees]

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

    def _record_write(target: Path, new_content: str) -> None:
        resolved = target.resolve()
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

    for checkout in checkouts:
        checkout_epic_dir = checkout / ".devtool" / "epic" / epic_slug
        if checkout_epic_dir.is_dir():
            # 1. HLD & design spec files (excluding BDD/review/fix-plan/smoke prose)
            hld_candidates: list[Path] = [
                checkout_epic_dir / f"{epic_slug}.en.md",
                checkout_epic_dir / f"{epic_slug}.vi.md",
            ]
            with contextlib.suppress(OSError):
                for doc in sorted(checkout_epic_dir.glob("*.md")):
                    if doc not in hld_candidates and _is_pic_hld_or_spec(doc, epic_slug):
                        hld_candidates.append(doc)

            for hld in hld_candidates:
                if not hld.is_file():
                    continue
                try:
                    content = hld.read_text(encoding="utf-8")
                except OSError as exc:
                    warnings.append(f"{_format_updated_path(hld, repo_dir)}: {exc}")
                    continue
                updated = _update_markdown_pic(content, new_pic, is_handoff=False)
                if updated is not None:
                    _record_write(hld, updated)

            # 2. handoff.md
            handoff_file = checkout_epic_dir / "handoff.md"
            if handoff_file.is_file():
                try:
                    content = handoff_file.read_text(encoding="utf-8")
                except OSError as exc:
                    warnings.append(
                        f"{_format_updated_path(handoff_file, repo_dir)}: {exc}"
                    )
                else:
                    updated = _update_markdown_pic(content, new_pic, is_handoff=True)
                    if updated is not None:
                        _record_write(handoff_file, updated)

            # 3a. Epic task files inside .devtool/epic/<epic_slug>/
            with contextlib.suppress(OSError):
                for tf in sorted(checkout_epic_dir.glob("task_*.md")):
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
                        _record_write(tf, updated_task)

        # 3b. Task files in .devtool/features/ filtered strictly by matching epic frontmatter
        for feat_dir in (
            checkout / ".devtool" / "features",
            checkout / ".devtool" / "features" / "done",
        ):
            if not feat_dir.is_dir():
                continue
            with contextlib.suppress(OSError):
                for tf in sorted(feat_dir.glob("task_*.md")):
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
                        _record_write(tf, updated_task)

        # 4. State pipeline & heartbeat JSON files in checkout/.devtool/state/
        state_dir = checkout / ".devtool" / "state"
        if state_dir.is_dir():
            pipeline_file = state_dir / f"{epic_slug}.pipeline.json"
            if pipeline_file.is_file():
                try:
                    s_data = json.loads(pipeline_file.read_text(encoding="utf-8"))
                    if isinstance(s_data, dict):
                        s_data["pic"] = new_pic
                        _record_write(
                            pipeline_file,
                            json.dumps(s_data, indent=2, ensure_ascii=False) + "\n",
                        )
                except (OSError, json.JSONDecodeError) as exc:
                    warnings.append(
                        f"{_format_updated_path(pipeline_file, repo_dir)}: {exc}"
                    )

            hb_candidates: list[Path] = []
            for slug_var in dict.fromkeys(
                (epic_slug, epic_slug.replace("_", "-"), epic_slug.replace("-", "_"))
            ):
                hb_path = state_dir / f"{slug_var}.heartbeat.json"
                if hb_path.is_file():
                    hb_candidates.append(hb_path)
            for hb_file in hb_candidates:
                try:
                    hb_data = json.loads(hb_file.read_text(encoding="utf-8"))
                    if isinstance(hb_data, dict):
                        hb_data["pic"] = new_pic
                        if "generation" in hb_data and isinstance(
                            hb_data["generation"], int
                        ):
                            hb_data["generation"] += 1
                        hb_data["updated_at"] = datetime.now(timezone.utc).isoformat(
                            timespec="seconds"
                        )
                        _record_write(
                            hb_file,
                            json.dumps(hb_data, indent=2, ensure_ascii=False) + "\n",
                        )
                except (OSError, json.JSONDecodeError) as exc:
                    warnings.append(
                        f"{_format_updated_path(hb_file, repo_dir)}: {exc}"
                    )

        # 5. Worktree-only .vscode/settings.json window.title (never root .vscode/settings.json)
        if checkout.resolve() in wt_resolved_set:
            vscode_settings = checkout / ".vscode" / "settings.json"
            if vscode_settings.is_file():
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
                            _record_write(vscode_settings, new_s_content)

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
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/tasks":
            graph = harvest_dashboard_graph(self.server.workspace_root)
            self._send_json(200, sanitize_paths_to_tilde(graph))
            return

        if path == "/api/review":
            query = urllib.parse.parse_qs(parsed.query)
            repo_name = query.get("repo", [""])[0]
            repo_dir = self.server.workspace_root / repo_name
            active_epic = query.get("epic", [None])[0]
            kind = query.get("kind", [None])[0]
            target_round_str = query.get("round", [None])[0]
            target_round: int | None = None
            if target_round_str:
                with contextlib.suppress(ValueError):
                    target_round = int(target_round_str)
            data = parse_review_results(repo_dir, active_epic, target_round, kind)
            self._send_json(200, sanitize_paths_to_tilde(data))
            return

        if path == "/api/profiles":
            profiles: list[str] = []
            try:
                profiles = discover_antigravity_profiles(get_real_home())
            except Exception:
                pass
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
                    self.server.workspace_root, repo_name, epic_slug, pic
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
    ) -> None:
        self.workspace_root = workspace_root or Path(get_real_home()) / "AllProjects"
        self.pid_file = pid_file
        available_port = find_available_port(port)
        super().__init__((host, available_port), TasksHandler)

    def serve_forever(self, poll_interval: float = 0.5) -> None:
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
            super().serve_forever(poll_interval)
        finally:
            with contextlib.suppress(OSError):
                self.pid_file.unlink(missing_ok=True)

    def server_close(self) -> None:
        with contextlib.suppress(OSError):
            self.pid_file.unlink(missing_ok=True)
        super().server_close()


def stop_server(pid_file: Path = DEFAULT_PID_FILE) -> bool:
    """Stop the running background server by sending SIGTERM."""
    pid = get_running_pid(pid_file)
    if not pid:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(20):
            time_val = 0.1
            threading.Event().wait(time_val)
            try:
                os.kill(pid, 0)
            except OSError:
                break
        with contextlib.suppress(OSError):
            pid_file.unlink(missing_ok=True)
        return True
    except OSError:
        with contextlib.suppress(OSError):
            pid_file.unlink(missing_ok=True)
        return False


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
        stopped = stop_server(pid_file)
        if stopped:
            print("Tasks server stopped.")
            return 0
        print("Tasks server is not running.")
        return 1

    if args.status:
        pid = get_running_pid(pid_file)
        if pid:
            print(f"Tasks server running (PID {pid}).")
            return 0
        print("Tasks server is stopped.")
        return 1

    existing_pid = get_running_pid(pid_file)
    if existing_pid:
        print(f"Tasks server already running (PID {existing_pid}).")
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
        print(f"Tasks server started in background (PID {proc.pid}, port {args.port}).")
        return 0

    server = TasksServer(
        host="127.0.0.1",
        port=args.port,
        workspace_root=args.workspace_root,
        pid_file=pid_file,
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
