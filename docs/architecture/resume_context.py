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
- Prompt Mode (--emit-prompt <mode>): Emits deterministic handoff prompts across Tri-Role personas.
"""

import argparse
import contextlib
import fcntl
import json
import os
import re
import subprocess
import sys
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

WORKSPACE_ROOT = Path.home() / "Projects"
REPOS = ["ai-agent-tools", "D3Nexus", "lyrics-sync", "nexus"]
MAX_STATE_LINES = 20

DEFAULT_LEDGER_TEMPLATE = """# Project Architectural Ledger & Feature History (Permanent)

## 1. System Topology & Core Invariants
- **Hub (`D3Nexus`)**: Physical SSOT for `shared-contracts/`, Rust core + FastAPI engine, Flutter client.
- **Satellites (`lyrics-sync`, `nexus`)**: Outbound symlinks to `shared-contracts/`, mechanically verified by `check_contracts.py`.
- **Workflows (`ai-agent-tools`)**: Bilingual TOC (`doc-designer`), Contract-First `task_01` sequencing (`dev-designer`).

## 2. Completed Epics & Architectural Milestones
"""


def print_section(title: str) -> None:
    print(f"\n{'=' * 65}\n📌 {title}\n{'=' * 65}")


def print_role_banner(role: str) -> None:
    norm_role = role.lower().strip()
    if norm_role == "assistant":
        print("=" * 65)
        print("🎭 [PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]")
        print("⛔ NO IMPLEMENTATION: Strictly prohibited from modifying production")
        print("   source code or application tests. Only design docs and reviews allowed.")
        print("=" * 65)
    elif norm_role in ("programmer", "implementer", "worker"):
        print("=" * 65)
        print("💻 [PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]")
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
            gen_state.write_text(legacy_state.read_text(encoding="utf-8"), encoding="utf-8")

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
        rollup.write_text("\n\n---\n\n".join(parts) + "\n", encoding="utf-8")
    elif rollup.exists():
        rollup.write_text("No active epic state.\n", encoding="utf-8")


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
    rollup.write_text("\n".join(recent) + ("\n" if recent else ""), encoding="utf-8")


def resolve_target_devtool_dir(root: Path, repo: str | None = None) -> Path:
    if not repo or repo == "workspace" or root.name == repo:
        return root / ".devtool"
    candidate = root / repo
    if (candidate / ".git").exists() or (candidate / ".devtool").exists():
        return candidate / ".devtool"
    sibling = root.parent / repo
    if root.name in REPOS and ((sibling / ".git").exists() or (sibling / ".devtool").exists()):
        return sibling / ".devtool"
    if not (root / ".git").exists():
        return candidate / ".devtool"
    return root / ".devtool"


def write_epic_state(
    root: Path,
    epic_slug: str,
    decisions: str = "",
    status: str = "",
    next_step: str = "",
    prompt: str = "",
    role: str = "programmer",
    repo: str | None = None,
) -> None:
    devtool_dir = resolve_target_devtool_dir(root, repo)
    with file_lock(devtool_dir):
        migrate_legacy_storage(devtool_dir)
        state_dir = devtool_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        content = enforce_state_line_limit(epic_slug, role, decisions, status, next_step, prompt)
        (state_dir / f"{epic_slug}.md").write_text(content + "\n", encoding="utf-8")
        render_assistant_state_rollup(devtool_dir)


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


def complete_feature_and_rotate(
    root: Path,
    epic_slug: str,
    summary: str,
    repo: str | None = None,
    checkpoint: bool = False,
) -> None:
    if checkpoint:
        write_epic_state(root, epic_slug, status="Checkpoint saved", next_step="Resume development", prompt=summary, repo=repo)
        append_activity_log(root, epic_slug, repo or "workspace", "checkpoint", summary, "Saved context checkpoint", note="None")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    milestone = f"- **[{today}] `{epic_slug}`**: {summary}\n"

    ledger_path = ensure_ledger(root)
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(milestone)
    print(f"✅ Appended milestone to {ledger_path.relative_to(root)}:\n   {milestone.strip()}")

    candidates = [root / ".devtool"] + [root / r / ".devtool" for r in REPOS]
    for devtool_dir in candidates:
        if not devtool_dir.exists():
            continue
        with file_lock(devtool_dir):
            archive_dir = devtool_dir / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)

            state_file = devtool_dir / "state" / f"{epic_slug}.md"
            if state_file.exists():
                dest_state = archive_dir / f"state_{epic_slug}_{timestamp}.md"
                state_file.rename(dest_state)

            log_file = devtool_dir / "logs" / f"activity_{epic_slug}.log"
            if log_file.exists():
                dest_log = archive_dir / f"activity_{epic_slug}_{timestamp}.log"
                log_file.rename(dest_log)

            render_assistant_state_rollup(devtool_dir)
            refresh_activity_stream_rollup(devtool_dir)


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
                    print(f"[{lf.relative_to(root)} - Last {tail_lines} entries]\n{text}\n")
                    found = True
        elif (d_dir / "activity_stream.log").exists():
            text = read_tail(d_dir / "activity_stream.log", tail_lines).strip()
            if text:
                print(f"[{d_dir.relative_to(root)}/activity_stream.log - Last {tail_lines} entries]\n{text}\n")
                found = True
    if not found:
        print("  (No activity_stream.log entries found yet.)")


def scan_git_status(root: Path) -> None:
    print_section("3. GIT WORKING TREE STATUS ACROSS REPOS")
    ws_base = root.parent if root.name in REPOS else root
    target_repos = [ws_base / r for r in REPOS] if ws_base != root or not (root / ".git").exists() else [root]
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
            line for line in lines
            if "OPEN" in line or line.startswith(("## ", "### "))
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

        for tf in sorted(features_dir.glob("task_*.md")):
            lines = tf.read_text(encoding="utf-8").splitlines()[:15]
            if epic_filter:
                epic_line = next((l for l in lines if l.startswith("epic:")), "")
                if epic_filter not in epic_line:
                    continue
            status_line = next((l for l in lines if "status:" in l.lower()), "status: unknown")
            st_val = status_line.replace("status:", "").strip().strip('"').strip("'").lower()
            if st_val == "done":
                done_count += 1
                total_count += 1
            elif any(s in st_val for s in ["todo", "in-progress", "in_progress", "review", "backlog"]):
                total_count += 1
                title_line = next((l for l in lines if l.startswith("# ")), tf.name)
                active_tasks.append((tf.name, status_line.strip(), title_line.strip()))

        done_dir = features_dir / "done"
        if done_dir.exists():
            for tf in sorted(done_dir.glob("task_*.md")):
                lines = tf.read_text(encoding="utf-8").splitlines()[:15]
                if epic_filter:
                    epic_line = next((l for l in lines if l.startswith("epic:")), "")
                    if epic_filter not in epic_line:
                        continue
                done_count += 1
                total_count += 1

        if total_count > 0:
            print(f"📊 [{repo_name}] Progress: {done_count}/{total_count} done")
            for t_name, t_status, t_title in active_tasks:
                print(f"  [{repo_name}] {t_name} ({t_status}) -> {t_title}")
                found = True
        elif active_tasks:
            for t_name, t_status, t_title in active_tasks:
                print(f"  [{repo_name}] {t_name} ({t_status}) -> {t_title}")
                found = True

    if not found:
        print("  (No active todo/in-progress/review tasks found.)")


def collect_harvest_data(root: Path, tail_lines: int = 15, epic_filter: str | None = None) -> dict[str, object]:
    ledger_path = ensure_ledger(root)
    ledger_text = ledger_path.read_text(encoding="utf-8").strip() if ledger_path.exists() else ""

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
                lines = [l.strip() for l in read_tail(lf, tail_lines).splitlines() if l.strip()]
                activity_entries.extend(lines)
        elif (d_dir / "activity_stream.log").exists():
            lines = [l.strip() for l in read_tail(d_dir / "activity_stream.log", tail_lines).splitlines() if l.strip()]
            activity_entries.extend(lines)

    ws_base = root.parent if root.name in REPOS else root
    git_status: dict[str, str] = {}
    target_repos = [ws_base / r for r in REPOS] if ws_base != root or not (root / ".git").exists() else [root]
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
                line for line in lines
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
        for tf in sorted(features_dir.glob("task_*.md")):
            lines = tf.read_text(encoding="utf-8").splitlines()[:15]
            epic_line = next((l for l in lines if l.startswith("epic:")), "")
            epic_val = epic_line.replace("epic:", "").strip().strip('"').strip("'")
            if epic_filter and epic_filter != epic_val and epic_filter not in epic_line:
                continue
            status_line = next((l for l in lines if "status:" in l.lower()), "status: unknown")
            st_val = status_line.replace("status:", "").strip().strip('"').strip("'").lower()
            if any(s in st_val for s in ["todo", "in-progress", "in_progress", "review", "backlog"]):
                title_line = next((l for l in lines if l.startswith("# ")), tf.name)
                active_tasks_list.append({
                    "repo": repo_name,
                    "task": tf.name,
                    "status": st_val,
                    "title": title_line.lstrip("# ").strip(),
                    "epic": epic_val,
                })

    return {
        "ledger": ledger_text,
        "state": state_map,
        "activity": activity_entries,
        "git_status": git_status,
        "rfcs": rfcs,
        "active_tasks": active_tasks_list,
    }


def harvest_json(root: Path, tail_lines: int = 15, epic_filter: str | None = None) -> None:
    data = collect_harvest_data(root, tail_lines=tail_lines, epic_filter=epic_filter)
    print(json.dumps(data, indent=2))


def emit_handoff_prompt(
    mode: str,
    epic_slug: str,
    epic_dir: str | None = None,
    custom_prompt: str | None = None,
) -> None:
    target_dir = epic_dir or epic_slug
    prompt_note = f"\nNote: {custom_prompt}\n" if custom_prompt else ""

    if mode == "principal-review":
        banner = "[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]"
        print(f"""{banner}
You are acting as the AI Assistant (Role 2.2 — Technical Advisor & Reviewer).
Startup command:
python3 scripts/resume_context.py --role assistant --epic {epic_slug}

MANDATORY TASKS & RULES:
1. Thoroughly review the HLD at .devtool/epic/{target_dir}/{target_dir}.en.md and bdd_scenarios.en.md.
2. Conduct an independent Principal Review following the `d3nexus:principal-review` skill.
3. DO NOT modify production source code or application test suites (only design documents and Kanban tasks).{prompt_note}""")
    elif mode == "implement":
        banner = "[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]"
        print(f"""{banner}
You are acting as the AI Programmer (Role 2.3 — Senior TDD Software Engineer).
Startup command:
python3 scripts/resume_context.py --role programmer --epic {epic_slug}

MANDATORY TASKS & RULES:
1. Activate `/dev-implementation` (`d3nexus:dev-implementation`) for the `{epic_slug}` epic.
2. Read `.devtool/epic/{target_dir}/handoff.md` first.
3. Strictly apply the 4 Execution Guardrails (Bounded context protocol, Strict spec fidelity, Zero test fakery, No contract repair).
4. Sequentially execute each Kanban task following the TDD cycle (Red-Green-Refactor) in an isolated git worktree.{prompt_note}""")
    elif mode == "cross-review":
        banner = "[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]"
        print(f"""{banner}
You are acting as the AI Assistant (Role 2.2 — Technical Advisor & Reviewer).
Startup command:
python3 scripts/resume_context.py --role assistant --epic {epic_slug}

MANDATORY TASKS & RULES:
1. Gate 4 has PASSED. Activate `d3nexus:cross-model-review`.
2. Run independent external model review (`run_external_review.py run`).
3. Triage findings with the Human Architect before fixing defects or proceeding to finish.{prompt_note}""")
    elif mode == "finish":
        banner = "[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]"
        print(f"""{banner}
You are acting as the AI Programmer (Role 2.3 — Senior TDD Software Engineer).
Startup command:
python3 scripts/resume_context.py --role programmer --epic {epic_slug}

MANDATORY TASKS & RULES:
1. Activate `d3nexus:finishing-a-development-branch` for the `{epic_slug}` epic.
2. Execute Pre-Finish Hook: `python3 scripts/resume_context.py --complete {epic_slug} "<milestone_summary>"`.
3. Verify branch integration and clean up the worktree.{prompt_note}""")
    elif mode == "assistant":
        banner = "[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]"
        print(f"""{banner}
You are acting as the AI Assistant (Role 2.2 — Technical Advisor & Co-Architect).
Startup command:
python3 scripts/resume_context.py --role assistant --epic {epic_slug}

MANDATORY TASKS & RULES:
1. Engage in technical discussion, root cause analysis (RCA), and solution trade-off evaluation.
2. STRICTLY PROHIBITED from modifying production code in this mode.
3. Persist discussion takeaways anytime via `python3 scripts/resume_context.py --state --epic {epic_slug} --decisions "<conclusions>"`.{prompt_note}""")
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
    if lines_to_add:
        zshrc_path.write_text("\n".join(lines_to_add) + "\n" + content, encoding="utf-8")


def update_zshrc_history_and_aliases(zshrc_path: Path) -> None:
    content = zshrc_path.read_text(encoding="utf-8")
    if 'HISTFILE="$REAL_HOME/.zsh_history"' not in content:
        hist_block = (
            '\n# Shared real-time zsh history across accounts\n'
            'export HISTFILE="$REAL_HOME/.zsh_history"\n'
            'export HISTSIZE=50000\n'
            'export SAVEHIST=50000\n'
            'setopt INC_APPEND_HISTORY\n'
            'setopt SHARE_HISTORY\n'
            'setopt HIST_IGNORE_DUPS\n'
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
    m = re.search(r"sync_items=\((.*?)\)", content, re.DOTALL) if "ag_run()" in content else None
    if not m:
        return
    body = m.group(1)
    tokens = [t for ln in body.splitlines() if not ln.strip().startswith("#") for t in ln.split()]
    missing = [k for k in ("AllProjects", "Projects", ".zsh_history") if k not in tokens]
    if not missing:
        return
    suffix = f"\n    {' '.join(missing)}\n  " if "\n" in body else f" {' '.join(missing)}"
    new_decl = f"sync_items=({body.rstrip() if chr(10) in body else body.strip()}{suffix})"
    zshrc_path.write_text(content[:m.start()] + new_decl + content[m.end():], encoding="utf-8")


def merge_profile_history(prof_hist: Path, main_hist: Path, seen_cmds: set[str]) -> None:
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


def sync_shell_env(
    real_home: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, object]:
    r_home = real_home or Path("/Users/danhdueexoictif")
    ws_root = workspace_root or Path("/Users/danhdueexoictif/AllProjects")
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
            if prof.is_dir():
                merge_profile_history(prof / ".zsh_history", main_hist, seen_cmds)
                sync_profile_symlinks(prof, main_hist, ws_root)
                synced_profiles.append(prof.name)

    return {"real_home": str(r_home), "workspace_root": str(ws_root), "synced_profiles": synced_profiles}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    normalized_args: list[str] = []
    i = 0
    while i < len(raw_args):
        if raw_args[i] == "--complete" and i + 1 < len(raw_args) and raw_args[i + 1] == "--checkpoint":
            normalized_args.extend(["--checkpoint", "--complete"])
            i += 2
        else:
            normalized_args.append(raw_args[i])
            i += 1

    parser = argparse.ArgumentParser(description="Two-Tier Context Harvester & Multi-Epic Memory Tool")
    parser.add_argument("--workspace-root", type=str, help="Workspace root containing repositories")
    parser.add_argument("--real-home", type=str, help="Real home directory for shell environment sync")
    parser.add_argument("--repo", type=str, help="Target repository name")
    parser.add_argument("--epic", type=str, help="Active epic slug")
    parser.add_argument("--role", type=str, choices=["assistant", "programmer", "implementer", "worker"], help="Active persona role")
    parser.add_argument("--tail", type=int, default=15, help="Number of activity log lines to show")
    parser.add_argument("--json", action="store_true", help="Output harvest in JSON format")

    parser.add_argument("--state", action="store_true", help="Record active epic state snapshot")
    parser.add_argument("--decisions", type=str, default="", help="Decisions text for --state")
    parser.add_argument("--status", type=str, default="", help="Status text for --state")
    parser.add_argument("--next", type=str, default="", help="Next immediate step for --state")
    parser.add_argument("--prompt", type=str, default="", help="Custom prompt or notes for --state")

    parser.add_argument("--log", action="store_true", help="Record programmer activity entry")
    parser.add_argument("--task", type=str, default="general", help="Task ID for --log")
    parser.add_argument("--request", type=str, default="", help="Request summary for --log")
    parser.add_argument("--action", type=str, default="", help="Action taken for --log")
    parser.add_argument("--note", type=str, default="None", help="Deviations or notes for --log")

    parser.add_argument("--complete", nargs="+", help="Complete feature: <slug> <summary>")
    parser.add_argument("--checkpoint", action="store_true", help="Save checkpoint without archiving during --complete")

    parser.add_argument("--emit-prompt", type=str, choices=["principal-review", "implement", "cross-review", "finish", "assistant"], help="Emit handoff prompt")
    parser.add_argument("--epic-dir", type=str, help="Epic directory name for --emit-prompt")

    parser.add_argument("--sync-zshrc", action="store_true", help="Synchronize shell environment and history")

    return parser.parse_args(normalized_args)


def main() -> None:
    args = parse_args()
    workspace = resolve_workspace_root(args.workspace_root)
    primary_repo = resolve_primary_repo_root()
    active_epic = args.epic or resolve_current_epic_slug()
    active_repo = args.repo or (primary_repo.name if primary_repo != workspace else "workspace")

    if args.role:
        print_role_banner(args.role)

    if args.emit_prompt:
        emit_handoff_prompt(args.emit_prompt, active_epic, args.epic_dir, args.prompt)
        return

    if args.sync_zshrc:
        r_home = Path(args.real_home) if args.real_home else None
        ws_root = Path(args.workspace_root) if args.workspace_root else None
        res = sync_shell_env(real_home=r_home, workspace_root=ws_root)
        print(f"Shell environment synchronized: {res}")
        return

    is_repo = (primary_repo / ".git").exists() or (primary_repo / ".devtool").exists()
    target_root = primary_repo if is_repo else workspace

    if args.complete:
        slug = args.complete[0]
        summary = " ".join(args.complete[1:]) if len(args.complete) > 1 else "Completed feature and verified contracts."
        complete_feature_and_rotate(target_root, slug, summary, repo=args.repo, checkpoint=args.checkpoint)
        return

    if args.state:
        write_epic_state(
            target_root,
            active_epic,
            decisions=args.decisions,
            status=args.status,
            next_step=args.next,
            prompt=args.prompt,
            role=args.role or "programmer",
            repo=args.repo,
        )
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

    # Default: Harvest context
    scan_root = target_root
    if args.json:
        harvest_json(scan_root, tail_lines=args.tail, epic_filter=args.epic)
        return

    scan_project_ledger(scan_root)
    scan_assistant_state(scan_root)
    scan_activity_stream(scan_root, tail_lines=args.tail)
    scan_git_status(scan_root)
    scan_open_rfcs(scan_root)
    scan_active_tasks(scan_root, epic_filter=args.epic)


if __name__ == "__main__":
    main()
