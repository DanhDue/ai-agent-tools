#!/usr/bin/env python3
"""Tests for Structured Gate Approval Ledger in Project Memory.

Covers: MEO-HP-04, MEO-AR-01, MEO-FR-03
"""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RESUME_SCRIPT = REPO_ROOT / "scripts" / "resume_context.py"


def git_cmd(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def init_git_repo(root: Path) -> None:
    git_cmd(root, "init")
    git_cmd(root, "config", "user.email", "test@example.com")
    git_cmd(root, "config", "user.name", "Test Runner")
    (root / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    git_cmd(root, "add", "README.md")
    git_cmd(root, "commit", "-m", "Initial commit")
    (root / ".devtool").mkdir(exist_ok=True)


def _run_gate_subprocess(args_tuple: tuple[str, str, int, str]) -> int:
    root_str, script_str, gate, scope = args_tuple
    cmd = [
        sys.executable,
        script_str,
        "--gate",
        str(gate),
        "--epic",
        "concurrent-epic",
        "--approved",
        scope,
    ]
    res = subprocess.run(cmd, cwd=root_str, capture_output=True, text=True)
    return res.returncode


def test_MEO_HP_04_record_and_check_gate_approval(tmp_path: Path) -> None:
    """[MEO-HP-04] [Tier C - Integration] Gate approval ledger records structured Gate 1-5 approvals and answers --check-gate queries."""
    init_git_repo(tmp_path)

    # 1. Record Gate 2 approval
    cmd_record = [
        sys.executable,
        str(RESUME_SCRIPT),
        "--gate",
        "2",
        "--epic",
        "sample-epic",
        "--approved",
        "HLD and 5 Kanban tasks",
        "--deviations",
        "SE-01",
    ]
    res_rec = subprocess.run(
        cmd_record, cwd=str(tmp_path), capture_output=True, text=True
    )
    assert res_rec.returncode == 0, f"Error: {res_rec.stderr}"

    # Verify JSONL
    jsonl_file = tmp_path / ".devtool" / "state" / "gate_ledger.jsonl"
    assert jsonl_file.is_file()
    lines = jsonl_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["epic"] == "sample-epic"
    assert entry["gate"] == 2
    assert entry["approved"] == "HLD and 5 Kanban tasks"
    assert entry["deviations"] == "SE-01"
    assert "commit" in entry
    assert "timestamp" in entry

    # Verify GATE_LEDGER.md
    md_file = tmp_path / ".devtool" / "GATE_LEDGER.md"
    assert md_file.is_file()
    md_content = md_file.read_text(encoding="utf-8")
    assert "sample-epic" in md_content
    assert "HLD and 5 Kanban tasks" in md_content
    assert "SE-01" in md_content

    # 2. Query Gate 2 approval
    cmd_check = [
        sys.executable,
        str(RESUME_SCRIPT),
        "--check-gate",
        "2",
        "--epic",
        "sample-epic",
    ]
    res_check = subprocess.run(
        cmd_check, cwd=str(tmp_path), capture_output=True, text=True
    )
    assert res_check.returncode == 0
    checked_entry = json.loads(res_check.stdout.strip())
    assert checked_entry["gate"] == 2
    assert checked_entry["approved"] == "HLD and 5 Kanban tasks"


def test_MEO_AR_01_concurrent_gate_approvals(tmp_path: Path) -> None:
    """[MEO-AR-01] [Tier A - Unit] Concurrent resume_context.py --gate invocations serialize under fcntl.flock."""
    init_git_repo(tmp_path)

    tasks = [
        (str(tmp_path), str(RESUME_SCRIPT), 1, "Gate 1 scope"),
        (str(tmp_path), str(RESUME_SCRIPT), 2, "Gate 2 scope"),
        (str(tmp_path), str(RESUME_SCRIPT), 3, "Gate 3 scope"),
        (str(tmp_path), str(RESUME_SCRIPT), 4, "Gate 4 scope"),
    ]

    with ProcessPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(_run_gate_subprocess, tasks))

    assert all(code == 0 for code in results)

    jsonl_file = tmp_path / ".devtool" / "state" / "gate_ledger.jsonl"
    assert jsonl_file.is_file()
    lines = jsonl_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 4

    parsed_entries = [json.loads(line) for line in lines]
    gates_recorded = {entry["gate"] for entry in parsed_entries}
    assert gates_recorded == {1, 2, 3, 4}

    md_file = tmp_path / ".devtool" / "GATE_LEDGER.md"
    assert md_file.is_file()
    md_content = md_file.read_text(encoding="utf-8")
    for g in (1, 2, 3, 4):
        assert f"Gate {g} scope" in md_content


def test_MEO_FR_03_rejections_and_unapproved_gates(tmp_path: Path) -> None:
    """[MEO-FR-03] [Tier A - Unit] Reject empty approved text and exit 1 on unapproved gates."""
    init_git_repo(tmp_path)

    # 1. Unapproved gate check exits 1
    cmd_check = [
        sys.executable,
        str(RESUME_SCRIPT),
        "--check-gate",
        "3",
        "--epic",
        "sample-epic",
    ]
    res_check = subprocess.run(
        cmd_check, cwd=str(tmp_path), capture_output=True, text=True
    )
    assert res_check.returncode == 1
    assert "Gate 3 is not yet recorded for epic 'sample-epic'" in res_check.stderr

    # 2. Empty approved text exits 2 without modifying jsonl
    cmd_empty = [
        sys.executable,
        str(RESUME_SCRIPT),
        "--gate",
        "3",
        "--epic",
        "sample-epic",
        "--approved",
        "",
    ]
    res_empty = subprocess.run(
        cmd_empty, cwd=str(tmp_path), capture_output=True, text=True
    )
    assert res_empty.returncode == 2
    assert "error: --approved must be non-empty" in res_empty.stderr

    jsonl_file = tmp_path / ".devtool" / "state" / "gate_ledger.jsonl"
    assert not jsonl_file.exists()


def test_MEO_HP_04_fallback_to_markdown_and_harvest(tmp_path: Path) -> None:
    """[MEO-HP-04] [Tier A - Unit] scan_gate_ledger falls back to GATE_LEDGER.md when JSONL is absent and collect_harvest_data includes gate approvals."""
    init_git_repo(tmp_path)

    # 1. Manually write GATE_LEDGER.md without state/gate_ledger.jsonl
    md_file = tmp_path / ".devtool" / "GATE_LEDGER.md"
    md_content = """# Gate Approval Ledger (Permanent)

| Timestamp | Epic | Gate | Commit | Approved Scope | Deviations | By |
|---|---|---|---|---|---|---|
| 2026-11-06T12:00:00Z | sample-epic | 1 | abc1234 | Approved Scope Gate 1 | None | developer |
| 2026-11-06T14:00:00Z | sample-epic | 2 | def5678 | Approved Scope Gate 2 | SE-02 | reviewer |
"""
    md_file.write_text(md_content, encoding="utf-8")

    # 2. Check query using fallback
    cmd_check = [
        sys.executable,
        str(RESUME_SCRIPT),
        "--check-gate",
        "2",
        "--epic",
        "sample-epic",
    ]
    res_check = subprocess.run(
        cmd_check, cwd=str(tmp_path), capture_output=True, text=True
    )
    assert res_check.returncode == 0
    checked = json.loads(res_check.stdout.strip())
    assert checked["gate"] == 2
    assert checked["approved"] == "Approved Scope Gate 2"
    assert checked["deviations"] == "SE-02"

    # 3. Check JSON harvest includes gate_approvals
    cmd_harvest = [
        sys.executable,
        str(RESUME_SCRIPT),
        "--json",
        "--epic",
        "sample-epic",
    ]
    res_harvest = subprocess.run(
        cmd_harvest, cwd=str(tmp_path), capture_output=True, text=True
    )
    assert res_harvest.returncode == 0
    harvest_data = json.loads(res_harvest.stdout.strip())
    assert "gate_approvals" in harvest_data
    approvals = harvest_data["gate_approvals"]
    assert len(approvals) == 2
    assert approvals[0]["gate"] == 1
    assert approvals[1]["gate"] == 2


def test_record_gate_preserves_markdown_ledger_on_absent_state_and_escapes_pipes(
    tmp_path: Path,
) -> None:
    """Recording a gate when state/ is absent preserves committed GATE_LEDGER.md entries and handles escaped pipes and dashes."""
    init_git_repo(tmp_path)

    # 1. Simulate a cloned repository where state/ is absent but GATE_LEDGER.md is committed
    md_file = tmp_path / ".devtool" / "GATE_LEDGER.md"
    md_content = (
        "# Gate Approval Ledger (Permanent)\n\n"
        "| Timestamp | Epic | Gate | Commit | Approved Scope | Deviations | By |\n"
        "|---|---|---|---|---|---|---|\n"
        "| 2026-11-06T12:00:00Z | sample-epic | 1 | abc1234 | HLD \\| 5 tasks \\| SE-01 approved | None | developer |\n"
        "| 2026-11-06T14:00:00Z | sample-epic | 2 | def5678 | Execution order --- wave 1-3 | None | reviewer |\n"
    )
    md_file.write_text(md_content, encoding="utf-8")

    # Verify query works on both entries before state/ exists
    res_cg1 = subprocess.run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--check-gate",
            "1",
            "--epic",
            "sample-epic",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_cg1.returncode == 0
    data_g1 = json.loads(res_cg1.stdout.strip())
    assert data_g1["approved"] == "HLD | 5 tasks | SE-01 approved"

    res_cg2 = subprocess.run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--check-gate",
            "2",
            "--epic",
            "sample-epic",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_cg2.returncode == 0
    data_g2 = json.loads(res_cg2.stdout.strip())
    assert data_g2["approved"] == "Execution order --- wave 1-3"

    # 2. Record Gate 3 when state/ is completely absent
    res_rec = subprocess.run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--gate",
            "3",
            "--epic",
            "sample-epic",
            "--approved",
            "Task execution | wave 1-5 | complete",
            "--deviations",
            "none",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_rec.returncode == 0, f"Error: {res_rec.stderr}"

    # 3. Verify that GATE_LEDGER.md retains Gates 1, 2, AND 3 (no truncation)
    new_md = md_file.read_text(encoding="utf-8")
    assert "HLD \\| 5 tasks \\| SE-01 approved" in new_md
    assert "Execution order --- wave 1-3" in new_md
    assert "Task execution \\| wave 1-5 \\| complete" in new_md

    # Verify all 3 gates can be queried
    for g_num in (1, 2, 3):
        res_chk = subprocess.run(
            [
                sys.executable,
                str(RESUME_SCRIPT),
                "--check-gate",
                str(g_num),
                "--epic",
                "sample-epic",
            ],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )
        assert res_chk.returncode == 0
        chk_data = json.loads(res_chk.stdout.strip())
        assert chk_data["gate"] == g_num

    # Verify JSONL was hydrated and contains all 3 entries
    jsonl_file = tmp_path / ".devtool" / "state" / "gate_ledger.jsonl"
    assert jsonl_file.is_file()
    lines = [
        l for l in jsonl_file.read_text(encoding="utf-8").splitlines() if l.strip()
    ]
    assert len(lines) == 3


class Test_Integration:
    """[Tier C - Integration] Test suite with integration runner provenance."""

    def test_MEO_HP_04_integration(self, tmp_path: Path) -> None:
        test_MEO_HP_04_record_and_check_gate_approval(tmp_path)
