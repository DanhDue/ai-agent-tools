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
        harvest_dashboard_graph,
    )
except ImportError:
    pass

DEFAULT_PORT = 8766
DEFAULT_PID_FILE = Path("/tmp/agy_tasks_server.pid")


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


def find_running_ide_pid(profile: str) -> int | None:
    """Return PID of running Antigravity IDE for the given profile, if any."""
    with contextlib.suppress(Exception):
        out = subprocess.check_output(["ps", "-ww", "-eo", "pid,args"], text=True)
        for line in out.splitlines():
            if (
                "Antigravity IDE.app/Contents/MacOS/Electron" in line
                and "--type=" not in line
            ):
                if f"antigravity_homes/{profile}" in line or (
                    profile == "danhdue" and "antigravity_homes" not in line
                ):
                    return int(line.strip().split()[0])
    return None


def focus_existing_ide_window(running_pid: int, worktree: str) -> bool:
    """Bring running Antigravity IDE window to front via macOS System Events AXRaise."""
    real_path = os.path.expanduser(worktree)
    folder_name = os.path.basename(real_path)
    repo_name = (
        os.path.basename(os.path.dirname(real_path))
        if ".worktrees" in real_path
        else folder_name
    )
    ascript = f"""
    tell application "System Events"
        try
            set p to (first process whose unix id is {running_pid})
            set frontmost of p to true
            set targetFound to false
            try
                set wList to (every UI element of p whose role is "AXWindow")
                repeat with w in wList
                    set wTitle to (name of w)
                    if wTitle contains "{folder_name}" or wTitle contains "{repo_name}" then
                        tell w to perform action "AXRaise"
                        set targetFound to true
                        exit repeat
                    end if
                end repeat
                if not targetFound and (count of wList) > 0 then
                    tell (first item of wList) to perform action "AXRaise"
                end if
            end try
            return "SUCCESS"
        on error
            return "ERROR"
        end try
    end tell
    """
    try:
        res = subprocess.run(
            ["osascript", "-e", ascript], capture_output=True, text=True, timeout=3
        )
        return "SUCCESS" in res.stdout
    except Exception:
        return False


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
        "findings": [],
        "raw_output": "",
    }

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

    # Detect all available rounds in the file
    round_matches = list(re.finditer(r"(?m)^##\s+Round\s+(\d+)", content))
    if round_matches:
        result["available_rounds"] = [int(m.group(1)) for m in round_matches]
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

    round_content = content
    if round_matches:
        blocks = re.split(r"(?m)^##\s+Round\s+(\d+)", content)
        # blocks: [header, round_num_1, text_1, round_num_2, text_2, ...]
        for i in range(1, len(blocks), 2):
            if int(blocks[i]) == round_to_extract:
                round_content = f"## Round {blocks[i]}\n{blocks[i + 1]}"
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

    # Parse 5-column triage table: | # | Severity | Location | Problem | Decision |
    lines = round_content.splitlines()
    in_table = False
    findings: list[dict[str, str]] = []
    for line in lines:
        s = line.strip()
        if s.startswith("|") and ("Severity" in s or "Mức độ" in s):
            in_table = True
            continue
        if in_table:
            if not s.startswith("|") or s.startswith("|---"):
                if not s.startswith("|"):
                    in_table = False
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 5:
                findings.append(
                    {
                        "id": cells[0],
                        "severity": cells[1],
                        "location": cells[2],
                        "problem": cells[3],
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


def assign_epic_pic(
    workspace_root: Path,
    repo_name: str,
    epic_slug: str,
    new_pic: str
) -> dict[str, Any]:
    """Assign or update PIC / profile across the epic HLD, handoff, tasks, and worktree settings."""
    if not re.match(r"^[a-zA-Z0-9_\-]+$", new_pic):
        return {"status": "error", "error": "Invalid profile / PIC name"}

    repo_dir = workspace_root / repo_name
    if not repo_dir.is_dir():
        return {"status": "error", "error": f"Repository '{repo_name}' not found"}

    epic_dir = repo_dir / ".devtool" / "epic" / epic_slug
    if not epic_dir.is_dir():
        return {"status": "error", "error": f"Epic '{epic_slug}' not found in {repo_name}"}

    updated_files: list[str] = []

    # 1. Update HLD markdown files in .devtool/epic/<epic_slug>/
    hld_candidates = [
        epic_dir / f"{epic_slug}.en.md",
        epic_dir / f"{epic_slug}.vi.md",
    ]
    for doc in epic_dir.glob("*.md"):
        if doc not in hld_candidates and not doc.name.startswith("task_") and doc.name != "handoff.md":
            hld_candidates.append(doc)

    for hld in hld_candidates:
        if not hld.is_file():
            continue
        try:
            content = hld.read_text(encoding="utf-8")
            pic_pattern = re.compile(
                r"^(-\s+\*\*(?:PIC|Profile|Assigned Profile|Người phụ trách(?: \(PIC\))?)\*\*:\s*)([^\n]+)$",
                re.MULTILINE | re.IGNORECASE,
            )
            if pic_pattern.search(content):
                content = pic_pattern.sub(rf"\g<1>`{new_pic}`", content)
                hld.write_text(content, encoding="utf-8")
                updated_files.append(str(hld.relative_to(repo_dir)))
            else:
                meta_pattern = re.compile(
                    r"^(-\s+\*\*(?:Epic name|Tên Epic|Epic)\*\*:[^\n]+)$",
                    re.MULTILINE | re.IGNORECASE,
                )
                m = meta_pattern.search(content)
                if m:
                    pos = m.end()
                    content = content[:pos] + f"\n- **PIC**: `{new_pic}`" + content[pos:]
                    hld.write_text(content, encoding="utf-8")
                    updated_files.append(str(hld.relative_to(repo_dir)))
                else:
                    lines = content.splitlines()
                    for idx, line in enumerate(lines):
                        if line.startswith("# "):
                            lines.insert(idx + 1, f"\n- **PIC**: `{new_pic}`")
                            content = "\n".join(lines)
                            hld.write_text(content, encoding="utf-8")
                            updated_files.append(str(hld.relative_to(repo_dir)))
                            break
        except Exception:
            pass

    # 2. Update handoff.md if present
    handoff_file = epic_dir / "handoff.md"
    if handoff_file.is_file():
        try:
            content = handoff_file.read_text(encoding="utf-8")
            pic_pattern = re.compile(
                r"^(-\s+\*\*(?:PIC|Profile|Assigned Profile|Người phụ trách(?: \(PIC\))?)\*\*:\s*)([^\n]+)$",
                re.MULTILINE | re.IGNORECASE,
            )
            if pic_pattern.search(content):
                content = pic_pattern.sub(rf"\g<1>`{new_pic}`", content)
            else:
                meta_pattern = re.compile(
                    r"^(-\s+\*\*(?:Epic name|Tên Epic|Epic)\*\*:[^\n]+)$",
                    re.MULTILINE | re.IGNORECASE,
                )
                m = meta_pattern.search(content)
                if m:
                    pos = m.end()
                    content = content[:pos] + f"\n- **PIC**: `{new_pic}`" + content[pos:]
            handoff_file.write_text(content, encoding="utf-8")
            updated_files.append(str(handoff_file.relative_to(repo_dir)))
        except Exception:
            pass

    # 3. Update task files in epic directory & worktree features directory
    task_files = list(epic_dir.glob("task_*.md"))
    wt_candidates = [
        repo_dir / ".worktrees" / epic_slug,
        repo_dir / ".worktrees" / epic_slug.replace("-", "_"),
        repo_dir / ".worktrees" / epic_slug.replace("_", "-"),
    ]
    for wt in wt_candidates:
        if wt.is_dir():
            wt_features = wt / ".devtool" / "features"
            if wt_features.is_dir():
                for tf in wt_features.glob("task_*.md"):
                    if tf not in task_files:
                        task_files.append(tf)

            # 4. Update worktree .vscode/settings.json window.title
            vscode_settings = wt / ".vscode" / "settings.json"
            if vscode_settings.is_file():
                try:
                    s_content = vscode_settings.read_text(encoding="utf-8")
                    if "[@" in s_content:
                        new_s_content = re.sub(r"\[@[a-zA-Z0-9_\-]+\]", f"[@{new_pic}]", s_content)
                        if new_s_content != s_content:
                            vscode_settings.write_text(new_s_content, encoding="utf-8")
                            updated_files.append(str(vscode_settings.relative_to(repo_dir)))
                except Exception:
                    pass
            break

    for tf in task_files:
        try:
            t_content = tf.read_text(encoding="utf-8")
            if t_content.startswith("---"):
                fm_end = t_content.find("---", 3)
                if fm_end != -1:
                    fm_text = t_content[3:fm_end]
                    body_text = t_content[fm_end:]
                    if re.search(r"^(pic|assigned):\s*.*$", fm_text, re.MULTILINE):
                        fm_text = re.sub(
                            r"^(pic|assigned):\s*.*$",
                            f'pic: "{new_pic}"',
                            fm_text,
                            flags=re.MULTILINE,
                        )
                    else:
                        fm_text = f'pic: "{new_pic}"\n' + fm_text
                    tf.write_text(f"---{fm_text}{body_text}", encoding="utf-8")
                    updated_files.append(str(tf.relative_to(repo_dir)))
        except Exception:
            pass

    # 5. Update state pipeline if present
    state_file = repo_dir / ".devtool" / "state" / f"{epic_slug}.pipeline.json"
    if state_file.is_file():
        try:
            s_data = json.loads(state_file.read_text(encoding="utf-8"))
            s_data["pic"] = new_pic
            state_file.write_text(json.dumps(s_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            updated_files.append(str(state_file.relative_to(repo_dir)))
        except Exception:
            pass

    return {
        "status": "ok",
        "repo": repo_name,
        "epic": epic_slug,
        "pic": new_pic,
        "updated_files": updated_files,
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
                self._send_json(400, {"error": "Missing required fields: repo, epic, pic"})
                return

            result = assign_epic_pic(self.server.workspace_root, repo_name, epic_slug, pic)
            if result.get("status") == "ok":
                self._send_json(200, result)
            else:
                self._send_json(400, result)
            return

        if path == "/api/launch/cli":
            worktree = payload.get("worktree", "")
            profile = payload.get("profile", "default")
            cmd = build_cli_launch_command(worktree, profile)
            try:
                subprocess.Popen(cmd)
            except Exception as e:
                self._send_json(500, {"error": str(e), "command": cmd})
                return
            self._send_json(200, {"status": "ok", "command": cmd})
            return

        if path == "/api/launch/ide":
            worktree = payload.get("worktree", "")
            profile = payload.get("profile", "default")
            if not re.match(r"^[a-zA-Z0-9_\-]+$", profile):
                self._send_json(400, {"error": "Invalid profile name"})
                return

            # Check if IDE is already running for this profile; focus instead of spawning duplicate
            running_pid = find_running_ide_pid(profile)
            if running_pid:
                focused = focus_existing_ide_window(running_pid, worktree)
                if focused:
                    self._send_json(
                        200,
                        {
                            "status": "ok",
                            "action": "focused",
                            "pid": running_pid,
                            "message": f"Focused existing Antigravity IDE window (PID {running_pid})",
                        },
                    )
                    return

            cmd = build_ide_launch_command(worktree, profile)
            try:
                subprocess.Popen(cmd)
            except Exception as e:
                self._send_json(500, {"error": str(e), "command": cmd})
                return
            self._send_json(200, {"status": "ok", "action": "launched", "command": cmd})
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
        self.workspace_root = workspace_root or Path(
            "/Users/danhdueexoictif/AllProjects"
        )
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
        default=Path("/Users/danhdueexoictif/AllProjects"),
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
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
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
