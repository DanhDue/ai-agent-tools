#!/usr/bin/env python3
"""
Two-Tier Context Harvester & Log Compaction Tool.
- Normal run: Prints PROJECT_LEDGER.md, assistant_state.md, tail of activity_stream.log,
  git status, OPEN contract RFCs, and active task_*.md files.
- Compaction run (--complete <slug> "<summary>"): Appends milestone to PROJECT_LEDGER.md
  and rotates activity_stream.log into .devtool/archive/.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Chỉnh lại thư mục gốc chứa các repo của bác nếu khác ~/Projects
WORKSPACE_ROOT = Path.home() / "Projects"
REPOS = ["ai-agent-tools", "D3Nexus", "lyrics-sync", "nexus"]

DEFAULT_LEDGER_TEMPLATE = """# Project Architectural Ledger & Feature History (Permanent)

## 1. System Topology & Core Invariants
- **Hub (`D3Nexus`)**: Physical SSOT for `shared-contracts/`, Rust core + FastAPI engine, Flutter client.
- **Satellites (`lyrics-sync`, `nexus`)**: Outbound symlinks to `shared-contracts/`, mechanically verified by `check_contracts.py`.
- **Workflows (`ai-agent-tools`)**: Bilingual TOC (`doc-designer`), Contract-First `task_01` sequencing (`dev-designer`).

## 2. Completed Epics & Architectural Milestones
"""


def print_section(title: str):
    print(f"\n{'=' * 65}\n📌 {title}\n{'=' * 65}")


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


def scan_project_ledger(root: Path):
    print_section("0. PROJECT ARCHITECTURAL LEDGER (.devtool/PROJECT_LEDGER.md)")
    ledger_path = ensure_ledger(root)
    print(ledger_path.read_text(encoding="utf-8").strip())


def scan_assistant_state(root: Path):
    print_section("1. ACTIVE EPIC STATE (.devtool/assistant_state.md)")
    candidates = [root / ".devtool" / "assistant_state.md"] + [
        root / r / ".devtool" / "assistant_state.md" for r in REPOS
    ]
    found = False
    for path in candidates:
        if path.exists():
            print(f"[{path.relative_to(root)}]\n{path.read_text(encoding='utf-8').strip()}\n")
            found = True
    if not found:
        print("  (No active assistant_state.md found yet.)")


def scan_activity_stream(root: Path):
    print_section("2. RECENT IMPLEMENTER ACTIVITY (.devtool/activity_stream.log)")
    candidates = [root / ".devtool" / "activity_stream.log"] + [
        root / r / ".devtool" / "activity_stream.log" for r in REPOS
    ]
    found = False
    for path in candidates:
        tail_text = read_tail(path, 15)
        if tail_text.strip():
            print(f"[{path.relative_to(root)} - Last 15 entries]\n{tail_text}\n")
            found = True
    if not found:
        print("  (No activity_stream.log entries found yet.)")


def scan_git_status(root: Path):
    print_section("3. GIT WORKING TREE STATUS ACROSS REPOS")
    for repo in REPOS:
        repo_path = root / repo
        if not (repo_path / ".git").exists():
            continue
        res = subprocess.run(
            ["git", "-C", str(repo_path), "status", "-s", "-b"],
            capture_output=True,
            text=True,
        )
        print(f"🔹 {repo}:\n{res.stdout.strip()}\n")


def scan_open_rfcs(root: Path):
    print_section("4. OPEN CONTRACT GAPS & RFCS (shared-contracts/*/gaps_and_rfcs.md)")
    hub_contracts = root / "D3Nexus" / "shared-contracts"
    if not hub_contracts.exists():
        print("  (D3Nexus/shared-contracts not initialized yet.)")
        return
    for rfc_file in sorted(hub_contracts.glob("*/gaps_and_rfcs.md")):
        lines = rfc_file.read_text(encoding="utf-8").splitlines()
        open_items = [
            line for line in lines
            if "OPEN" in line or line.startswith("## ") or line.startswith("### ")
        ]
        if open_items:
            print(f"📄 {rfc_file.relative_to(root)}:")
            for item in open_items[-10:]:
                print(f"  {item}")


def scan_active_tasks(root: Path):
    print_section("5. ACTIVE TASKS (.devtool/features/task_*.md)")
    found = False
    for repo in REPOS:
        features_dir = root / repo / ".devtool" / "features"
        if not features_dir.exists():
            continue
        for task_file in sorted(features_dir.glob("task_*.md")):
            head = "\n".join(task_file.read_text(encoding="utf-8").splitlines()[:15])
            if any(st in head.lower() for st in ["in-progress", "in_progress", "review", "todo"]):
                status_line = next(
                    (l for l in head.splitlines() if "status" in l.lower()), "status: unknown"
                )
                title_line = next(
                    (l for l in head.splitlines() if l.startswith("# ")), task_file.name
                )
                print(f"  [{repo}] {task_file.name} ({status_line.strip()}) -> {title_line}")
                found = True
    if not found:
        print("  (No active todo/in-progress/review tasks found.)")


def complete_feature_and_rotate(root: Path, epic_slug: str, summary: str):
    """Compacts completed feature into PROJECT_LEDGER.md and archives activity_stream.log."""
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    # 1. Ghi cột mốc vĩnh viễn vào PROJECT_LEDGER.md (Tầng 1)
    ledger_path = ensure_ledger(root)
    milestone_entry = f"- **[{today}] `{epic_slug}`**: {summary}\n"
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(milestone_entry)
    print(f"✅ Appended milestone to {ledger_path.relative_to(root)}:\n   {milestone_entry.strip()}")

    # 2. Xoay vòng activity_stream.log sang .devtool/archive/ (Tầng 2)
    candidates = [root / ".devtool"] + [root / r / ".devtool" for r in REPOS]
    for devtool_dir in candidates:
        log_file = devtool_dir / "activity_stream.log"
        if log_file.exists() and log_file.stat().st_size > 0:
            archive_dir = devtool_dir / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            archived_path = archive_dir / f"activity_{epic_slug}_{timestamp}.log"
            log_file.rename(archived_path)
            log_file.write_text(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] [SYSTEM] Completed & archived '{epic_slug}' -> {archived_path.name}\n",
                encoding="utf-8",
            )
            print(f"📦 Archived log: {log_file.relative_to(root)} -> {archived_path.name}")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--complete":
        slug = sys.argv[2] if len(sys.argv) >= 3 else "unnamed-epic"
        summary_text = (
            " ".join(sys.argv[3:])
            if len(sys.argv) >= 4
            else "Completed feature implementation and verified contracts."
        )
        complete_feature_and_rotate(WORKSPACE_ROOT, slug, summary_text)
    else:
        scan_project_ledger(WORKSPACE_ROOT)
        scan_assistant_state(WORKSPACE_ROOT)
        scan_activity_stream(WORKSPACE_ROOT)
        scan_git_status(WORKSPACE_ROOT)
        scan_open_rfcs(WORKSPACE_ROOT)
        scan_active_tasks(WORKSPACE_ROOT)
