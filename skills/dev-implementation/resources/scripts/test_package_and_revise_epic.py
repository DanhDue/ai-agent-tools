#!/usr/bin/env python3
"""Tests for packaged epic revision workflow and HLD Spec Errata contract.

Covers: MEO-HP-03, MEO-ST-02, MEO-FR-02
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
PACKAGE_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "dev-implementation"
    / "resources"
    / "scripts"
    / "package_epic.py"
)
READINESS_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "dev-implementation"
    / "resources"
    / "scripts"
    / "check_epic_readiness.py"
)
sys.path.insert(0, str(PACKAGE_SCRIPT.parent))
from test_check_epic_readiness import build_ready_epic


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


def setup_valid_epic(
    root: Path,
    epic_dir: str = "demo_epic",
    *,
    en_errata: list[tuple[str, str, str]] | None = None,
    vi_errata: list[tuple[str, str, str]] | None = None,
) -> Path:
    build_ready_epic(root)
    epic_path = root / ".devtool" / "epic" / epic_dir

    if en_errata is not None:
        hld_en_file = epic_path / f"{epic_dir}.en.md"
        hld_en = hld_en_file.read_text(encoding="utf-8")
        hld_en = hld_en.replace(
            "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n",
            "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n- [Spec Errata](#spec-errata)\n",
        )
        errata_sec = "\n## Spec Errata\n\n" + "\n".join(
            f"- **[{eid}] {sec}**: {desc}" for eid, sec, desc in en_errata
        ) + "\n"
        hld_en_file.write_text(hld_en + errata_sec, encoding="utf-8")

    if vi_errata is not None:
        hld_vi_file = epic_path / f"{epic_dir}.vi.md"
        hld_vi = hld_vi_file.read_text(encoding="utf-8")
        hld_vi = hld_vi.replace(
            "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n",
            "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n- [Đính chính Đặc tả (Spec Errata)](#đính-chính-đặc-tả-spec-errata)\n",
        )
        errata_sec = "\n## Đính chính Đặc tả (Spec Errata)\n\n" + "\n".join(
            f"- **[{eid}] {sec}**: {desc}" for eid, sec, desc in vi_errata
        ) + "\n"
        hld_vi_file.write_text(hld_vi + errata_sec, encoding="utf-8")

    return epic_path


def test_MEO_HP_03_package_and_revise_epic(tmp_path: Path) -> None:
    """[MEO-HP-03] [Tier C - Integration] package_epic.py packages an epic, validates bilingual Spec Errata, and re-anchors handoff.md on --revise."""
    init_git_repo(tmp_path)
    epic_path = setup_valid_epic(
        tmp_path,
        "demo_epic",
        en_errata=[("SE-01", "Design", "Initial design clarification")],
        vi_errata=[("SE-01", "Thiết kế", "Làm rõ thiết kế ban đầu")],
    )

    git_cmd(tmp_path, "add", ".")
    git_cmd(tmp_path, "commit", "-m", "Add sample epic files")
    head_1 = git_cmd(tmp_path, "rev-parse", "--short", "HEAD").stdout.strip()

    # 1. Package epic
    res_pkg = subprocess.run(
        [sys.executable, str(PACKAGE_SCRIPT), "demo_epic"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_pkg.returncode == 0, f"Error: {res_pkg.stderr}"

    handoff_file = epic_path / "handoff.md"
    assert handoff_file.is_file()
    handoff_text = handoff_file.read_text(encoding="utf-8")
    assert f"- **Design commit**: `{head_1}`" in handoff_text
    assert f"git log {head_1}..main" in handoff_text or f"git log {head_1}.." in handoff_text
    assert "## Revisions" in handoff_text

    # 2. Make post-packaging revision commit
    (epic_path / "extra_note.txt").write_text("extra note", encoding="utf-8")
    git_cmd(tmp_path, "add", ".")
    git_cmd(tmp_path, "commit", "-m", "Update extra notes")
    head_2 = git_cmd(tmp_path, "rev-parse", "--short", "HEAD").stdout.strip()

    # 3. Revise epic
    res_rev = subprocess.run(
        [
            sys.executable,
            str(PACKAGE_SCRIPT),
            "demo_epic",
            "--revise",
            "--reason",
            "Clarify SE-01 contract",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_rev.returncode == 0, f"Error: {res_rev.stderr}"

    revised_text = handoff_file.read_text(encoding="utf-8")
    assert f"- **Design commit**: `{head_2}`" in revised_text
    assert f"(`{head_1}` -> `{head_2}`)" in revised_text
    assert "Clarify SE-01 contract" in revised_text


def test_MEO_ST_02_revise_preserves_custom_open_notes(tmp_path: Path) -> None:
    """[MEO-ST-02] [Tier A - Unit] package_epic.py --revise preserves custom Open Notes while updating Design commit and Revisions."""
    init_git_repo(tmp_path)
    epic_path = setup_valid_epic(tmp_path, "demo_epic")

    git_cmd(tmp_path, "add", ".")
    git_cmd(tmp_path, "commit", "-m", "Add sample epic")
    head_1 = git_cmd(tmp_path, "rev-parse", "--short", "HEAD").stdout.strip()

    # Package initially
    subprocess.run(
        [sys.executable, str(PACKAGE_SCRIPT), "demo_epic"],
        cwd=str(tmp_path),
        check=True,
    )

    handoff_file = epic_path / "handoff.md"
    orig_text = handoff_file.read_text(encoding="utf-8")

    # Add custom Open Notes
    custom_notes = "- Custom note 1: developer alignment\n- Custom note 2: preserve this"
    customized_text = orig_text.replace(
        "## Open Notes\n",
        f"## Open Notes\n\n{custom_notes}\n",
    )
    handoff_file.write_text(customized_text, encoding="utf-8")
    git_cmd(tmp_path, "add", ".")
    git_cmd(tmp_path, "commit", "-m", "Customize open notes")
    head_2 = git_cmd(tmp_path, "rev-parse", "--short", "HEAD").stdout.strip()

    # Revise
    subprocess.run(
        [
            sys.executable,
            str(PACKAGE_SCRIPT),
            "demo_epic",
            "--revise",
            "--reason",
            "Align task 02 CLI flags",
        ],
        cwd=str(tmp_path),
        check=True,
    )

    rev_text = handoff_file.read_text(encoding="utf-8")
    assert custom_notes in rev_text
    assert f"- **Design commit**: `{head_2}`" in rev_text
    assert f"(`{head_1}` -> `{head_2}`)" in rev_text
    assert "Align task 02 CLI flags" in rev_text


def test_MEO_FR_02_spec_errata_asymmetry_and_missing_reason(tmp_path: Path) -> None:
    """[MEO-FR-02] [Tier A - Unit] R7 fails on asymmetric Spec Errata and package_epic.py fails without --reason."""
    init_git_repo(tmp_path)

    # 1. Asymmetric Spec Errata: en has SE-01, SE-02 while vi has SE-01
    setup_valid_epic(
        tmp_path,
        "demo_epic",
        en_errata=[
            ("SE-01", "Design", "First item"),
            ("SE-02", "Design", "Second item"),
        ],
        vi_errata=[
            ("SE-01", "Thiết kế", "Mục thứ nhất"),
        ],
    )

    res_readiness = subprocess.run(
        [sys.executable, str(READINESS_SCRIPT), "demo_epic"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_readiness.returncode != 0
    assert "R7" in res_readiness.stdout or "R7" in res_readiness.stderr
    assert "SE-02" in res_readiness.stdout or "SE-02" in res_readiness.stderr

    # 2. package_epic.py --revise without --reason exits 2
    res_no_reason = subprocess.run(
        [sys.executable, str(PACKAGE_SCRIPT), "demo_epic", "--revise"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_no_reason.returncode == 2
    assert "error: --reason is required when --revise is set" in res_no_reason.stderr


def test_package_epic_refuses_overwrite_without_revise(tmp_path: Path) -> None:
    """package_epic.py refuses to overwrite existing handoff.md without --revise or --force."""
    init_git_repo(tmp_path)
    epic_path = setup_valid_epic(tmp_path, "demo_epic")

    git_cmd(tmp_path, "add", ".")
    git_cmd(tmp_path, "commit", "-m", "Add sample epic")

    # Initial packaging succeeds
    res_pkg = subprocess.run(
        [sys.executable, str(PACKAGE_SCRIPT), "demo_epic"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_pkg.returncode == 0

    handoff_file = epic_path / "handoff.md"
    assert handoff_file.is_file()

    # Re-running without --revise or --force fails with code 1
    res_repeat = subprocess.run(
        [sys.executable, str(PACKAGE_SCRIPT), "demo_epic"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_repeat.returncode == 1
    assert "already exists for epic" in res_repeat.stderr

    # Re-running with --force succeeds
    res_force = subprocess.run(
        [sys.executable, str(PACKAGE_SCRIPT), "demo_epic", "--force"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res_force.returncode == 0


class Test_Integration:
    """[Tier C - Integration] Test suite with integration runner provenance."""

    def test_MEO_HP_03_integration(self, tmp_path: Path) -> None:
        test_MEO_HP_03_package_and_revise_epic(tmp_path)
