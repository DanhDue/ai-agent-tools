#!/usr/bin/env python3
"""Tests for inter-epic dependencies, readiness resolution, and prerequisite replay.

Covers: MEO-HP-01, MEO-EC-01, MEO-FR-01
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import task_contract as tc
import check_task_contract
import check_epic_readiness


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


def test_MEO_EC_01_transitive_dependencies(tmp_path: Path) -> None:
    """[MEO-EC-01] [Tier A - Unit] Transitive Depends on epic chain resolves in topological order."""
    init_git_repo(tmp_path)
    epic_dir = tmp_path / ".devtool" / "epic"

    # Setup epic_a
    dir_a = epic_dir / "epic_a"
    dir_a.mkdir(parents=True)
    (dir_a / "epic_a.en.md").write_text(
        "# Epic A\n\n- **Status**: Packaged\n- **Depends on epic**: none\n",
        encoding="utf-8",
    )
    (dir_a / "task_01_a.md").write_text(
        "---\n"
        "id: \"task_01_a\"\n"
        "epic: \"epic-a\"\n"
        "status: \"todo\"\n"
        "---\n\n"
        "## Files\n\n"
        "Allowed files:\n"
        "- `src/a.py` (new)\n\n"
        "## Impact Analysis & Blast Radius\n\n"
        "- **Target Files & Symbols**:\n"
        "  - `src/a.py`: new `alpha_func`, new `AlphaClass`\n",
        encoding="utf-8",
    )

    # Setup epic_b (depends on epic-a)
    dir_b = epic_dir / "epic_b"
    dir_b.mkdir(parents=True)
    (dir_b / "epic_b.en.md").write_text(
        "# Epic B\n\n- **Status**: Packaged\n- **Depends on epic**: epic-a\n",
        encoding="utf-8",
    )
    (dir_b / "task_01_b.md").write_text(
        "---\n"
        "id: \"task_01_b\"\n"
        "epic: \"epic-b\"\n"
        "status: \"todo\"\n"
        "---\n\n"
        "## Files\n\n"
        "Allowed files:\n"
        "- `src/b.py` (new)\n\n"
        "## Impact Analysis & Blast Radius\n\n"
        "- **Target Files & Symbols**:\n"
        "  - `src/b.py`: new `beta_func`\n",
        encoding="utf-8",
    )

    # Setup epic_c (depends on epic_b)
    dir_c = epic_dir / "epic_c"
    dir_c.mkdir(parents=True)
    hld_c = (
        "# Epic C\n\n"
        "- **Status**: Packaged\n"
        "- **Depends on epic**: epic_b\n"
    )
    (dir_c / "epic_c.en.md").write_text(hld_c, encoding="utf-8")

    # Topological resolution
    prereq_dirs, errors = tc.resolve_prerequisite_epic_dirs(tmp_path, hld_c, "epic_c")
    assert errors == []
    assert prereq_dirs == ["epic_a", "epic_b"]

    # Artifact collection
    prereq_files, prereq_symbols = tc.collect_prerequisite_artifacts(tmp_path, prereq_dirs)
    assert "src/a.py" in prereq_files
    assert "src/b.py" in prereq_files
    assert prereq_symbols.get("src/a.py") == {"alpha_func", "AlphaClass"}
    assert prereq_symbols.get("src/b.py") == {"beta_func"}


def test_MEO_FR_01_missing_or_cyclic_dependencies(tmp_path: Path) -> None:
    """[MEO-FR-01] [Tier A - Unit] R7 fails when Depends on epic references a missing epic or forms a cycle."""
    init_git_repo(tmp_path)
    epic_dir = tmp_path / ".devtool" / "epic"

    # Missing epic
    dir_missing = epic_dir / "epic_missing"
    dir_missing.mkdir(parents=True)
    hld_missing = (
        "# Epic Missing\n\n"
        "- **Status**: Packaged\n"
        "- **Depends on epic**: non-existent-epic\n"
    )
    (dir_missing / "epic_missing.en.md").write_text(hld_missing, encoding="utf-8")
    (dir_missing / "handoff.md").write_text(
        "# Handoff\n\n- **Design commit**: uncommitted\n", encoding="utf-8"
    )

    ctx_missing = check_epic_readiness.Context(
        root=tmp_path,
        epic_dir="epic_missing",
        epic_slug="epic-missing",
        hld_text=hld_missing,
        tasks={},
        results=[],
        roots=[],
    )
    findings = check_epic_readiness.check_metadata(ctx_missing)
    r7_fails = [f for f in findings if f.check == "R7" and f.severity == "FAIL"]
    assert any("does not exist" in f.message for f in r7_fails)

    # Cyclic dependency: epic_1 -> epic_2 -> epic_1
    dir_1 = epic_dir / "epic_1"
    dir_2 = epic_dir / "epic_2"
    dir_1.mkdir(parents=True)
    dir_2.mkdir(parents=True)

    hld_1 = "# Epic 1\n\n- **Status**: Packaged\n- **Depends on epic**: epic_2\n"
    hld_2 = "# Epic 2\n\n- **Status**: Packaged\n- **Depends on epic**: epic_1\n"
    (dir_1 / "epic_1.en.md").write_text(hld_1, encoding="utf-8")
    (dir_1 / "handoff.md").write_text("# Handoff\n\n- **Design commit**: uncommitted\n", encoding="utf-8")
    (dir_2 / "epic_2.en.md").write_text(hld_2, encoding="utf-8")
    (dir_2 / "handoff.md").write_text("# Handoff\n\n- **Design commit**: uncommitted\n", encoding="utf-8")

    ctx_cyclic = check_epic_readiness.Context(
        root=tmp_path,
        epic_dir="epic_1",
        epic_slug="epic-1",
        hld_text=hld_1,
        tasks={},
        results=[],
        roots=[],
    )
    findings_cyclic = check_epic_readiness.check_metadata(ctx_cyclic)
    r7_cyclic = [f for f in findings_cyclic if f.check == "R7" and f.severity == "FAIL"]
    assert any("cycle detected" in f.message for f in r7_cyclic)


def test_MEO_HP_01_dependent_epic_readiness_and_replay(tmp_path: Path) -> None:
    """[MEO-HP-01] [Tier C - Integration] Dependent epic passes design-time contract and R5 checks."""
    init_git_repo(tmp_path)
    epic_dir = tmp_path / ".devtool" / "epic"

    # Setup epic_alpha
    dir_alpha = epic_dir / "epic_alpha"
    dir_alpha.mkdir(parents=True)
    (dir_alpha / "epic_alpha.en.md").write_text(
        "# Epic Alpha\n\n- **Status**: Packaged\n- **Depends on epic**: none\n",
        encoding="utf-8",
    )
    (dir_alpha / "handoff.md").write_text(
        "# Handoff\n\n- **Design commit**: uncommitted\n", encoding="utf-8"
    )
    (dir_alpha / "task_01_alpha.md").write_text(
        "---\n"
        "id: \"task_01_alpha\"\n"
        "epic: \"epic-alpha\"\n"
        "status: \"todo\"\n"
        "---\n\n"
        "## Files\n\n"
        "Allowed files:\n"
        "- `src/alpha_helper.py` (new)\n\n"
        "## Impact Analysis & Blast Radius\n\n"
        "- **Target Files & Symbols**:\n"
        "  - `src/alpha_helper.py`: new `compute_alpha`\n",
        encoding="utf-8",
    )

    # Setup epic_beta (depends on epic-alpha)
    dir_beta = epic_dir / "epic_beta"
    dir_beta.mkdir(parents=True)
    hld_beta = (
        "# Epic Beta\n\n"
        "- **Status**: Packaged\n"
        "- **Depends on epic**: epic-alpha\n"
    )
    (dir_beta / "epic_beta.en.md").write_text(hld_beta, encoding="utf-8")
    (dir_beta / "handoff.md").write_text(
        "# Handoff\n\n- **Design commit**: uncommitted\n", encoding="utf-8"
    )

    task_beta_content = (
        "---\n"
        "id: \"task_01_beta\"\n"
        "epic: \"epic-beta\"\n"
        "status: \"todo\"\n"
        "---\n\n"
        "## Files\n\n"
        "Allowed files:\n"
        "- `src/beta_service.py` (new)\n\n"
        "Read-only context:\n"
        "- `src/alpha_helper.py`\n\n"
        "## Impact Analysis & Blast Radius\n\n"
        "- **Target Files & Symbols**:\n"
        "  - `src/alpha_helper.py`: `compute_alpha`\n"
        "  - `src/beta_service.py`: new `run_beta`\n"
    )
    (dir_beta / "task_01_beta.md").write_text(task_beta_content, encoding="utf-8")

    ctx_beta = check_epic_readiness.Context(
        root=tmp_path,
        epic_dir="epic_beta",
        epic_slug="epic-beta",
        hld_text=hld_beta,
        tasks={dir_beta / "task_01_beta.md": task_beta_content},
        results=[],
        roots=[],
    )

    # Check R5 & R7
    findings_r5 = check_epic_readiness.check_grounding(ctx_beta)
    r5_failures = [f for f in findings_r5 if f.check == "R5" and f.severity == "FAIL"]
    assert r5_failures == []

    findings_r7 = check_epic_readiness.check_metadata(ctx_beta)
    r7_failures = [f for f in findings_r7 if f.check == "R7" and f.severity == "FAIL"]
    assert r7_failures == []

    # Replay with prerequisites
    replayed: list[str] = []

    def mock_replay(root: Path, epic: str, timeout: int = 600) -> tuple[int, list[str]]:
        replayed.append(epic)
        return 0, []

    with patch("check_epic_readiness.replay_epic_in_worktree", side_effect=mock_replay):
        errors = check_epic_readiness.replay_with_prerequisites(tmp_path, "epic_beta")
        assert errors == []
        assert replayed == ["epic_alpha", "epic_beta"]


class Test_Integration:
    """[Tier C - Integration] Test suite with integration runner provenance."""

    def test_MEO_HP_01_integration(self, tmp_path: Path) -> None:
        test_MEO_HP_01_dependent_epic_readiness_and_replay(tmp_path)


def test_replay_prereqs_cli_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """[V6] CLI --replay-prereqs flag dispatches to replay_with_prerequisites."""
    init_git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    epic_dir = tmp_path / ".devtool" / "epic" / "epic_simple"
    epic_dir.mkdir(parents=True)
    (epic_dir / "epic_simple.en.md").write_text(
        "# Epic Simple\n\n- **Status**: Packaged\n- **Depends on epic**: none\n",
        encoding="utf-8",
    )
    (epic_dir / "handoff.md").write_text(
        "# Handoff\n\n- **Design commit**: uncommitted\n", encoding="utf-8"
    )

    with patch("check_epic_readiness.replay_with_prerequisites", return_value=[]) as mock_call:
        exit_code = check_epic_readiness.main(["--replay-prereqs", "epic_simple"])
        assert exit_code == 0
        mock_call.assert_called_once()
