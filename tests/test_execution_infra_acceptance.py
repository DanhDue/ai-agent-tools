"""End-to-End Acceptance Verification for Execution and Verification Infrastructure."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from test_check_epic_readiness import build_ready_epic, git_cmd

READINESS_SCRIPT = SCRIPTS_DIR / "check_epic_readiness.py"


def test_EVI_AR_01_readiness_replay_isolated_worktree(tmp_path: Path) -> None:
    """[EVI-AR-01] [Tier C - Integration] check_epic_readiness.py --replay executes task text in an isolated scratch worktree and cleans up without mutating the main tree."""
    repo = tmp_path / "repo"
    repo.mkdir()

    git_cmd(repo, "init", "-q")
    git_cmd(repo, "config", "user.email", "tester@example.com")
    git_cmd(repo, "config", "user.name", "Tester")

    build_ready_epic(repo)

    # 1. Update tool.py with CLI handling so verification rows pass during replay
    tool_content = """import sys, pathlib

if len(sys.argv) > 1:
    cmd = sys.argv[1]
    if cmd == "red":
        print("RED FAIL expected")
        sys.exit(1)
    elif cmd == "green":
        print("GREEN PASS")
        sys.exit(0)
    elif cmd == "int":
        p = pathlib.Path("build/test-results/int.xml")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("<testsuite><testcase name='int' status='passed'/></testsuite>")
        print("INT PASS")
        sys.exit(0)

def run():
    return 1
"""
    (repo / "tool.py").write_text(tool_content, encoding="utf-8")
    git_cmd(repo, "add", "tool.py")
    git_cmd(repo, "commit", "-m", "update tool.py CLI", "-q")

    # 2. Add Create and Replace in directives to task_1
    task_1_path = repo / ".devtool" / "epic" / "demo_epic" / "task_1.md"
    task_1_text = task_1_path.read_text(encoding="utf-8")
    task_1_text = task_1_text.replace(
        "Allowed files:\n- `tool.py`\n",
        "Allowed files:\n- `tool.py`\n- `helper.py` (new)\n",
    )
    task_1_directive = """
## Changes

Create helper.py:
```python
def extra():
    return 123
```

Replace in tool.py:
```python
def run():
    return 1
```
With:
```python
def run():
    return 2
```
"""
    task_1_text = task_1_text.replace(
        "## Requirement Analysis", task_1_directive + "\n## Requirement Analysis"
    )
    task_1_path.write_text(task_1_text, encoding="utf-8")
    (repo / ".devtool" / "features" / "task_1.md").write_text(
        task_1_text.replace(
            "](demo_epic.en.md)", "](../epic/demo_epic/demo_epic.en.md)"
        ),
        encoding="utf-8",
    )

    # 3. Add Insert in directive to task_2
    task_2_path = repo / ".devtool" / "epic" / "demo_epic" / "task_2.md"
    task_2_text = task_2_path.read_text(encoding="utf-8")
    task_2_directive = """
## Changes

Insert in tool.py (after):
```python
def run():
    return 2
```
With:
```python


def helper():
    return "ok"
```
"""
    task_2_text = task_2_text.replace(
        "## Requirement Analysis", task_2_directive + "\n## Requirement Analysis"
    )
    task_2_path.write_text(task_2_text, encoding="utf-8")
    (repo / ".devtool" / "features" / "task_2.md").write_text(
        task_2_text.replace(
            "](demo_epic.en.md)", "](../epic/demo_epic/demo_epic.en.md)"
        ),
        encoding="utf-8",
    )

    # Commit all epic files so git status in main tree is clean
    git_cmd(repo, "add", "-A")
    git_cmd(repo, "commit", "-m", "add epic files", "-q")

    # Run check_epic_readiness.py demo_epic --replay
    proc = subprocess.run(
        [sys.executable, str(READINESS_SCRIPT), "demo_epic", "--replay"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"check_epic_readiness --replay failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    assert "R8 PASS" in proc.stdout, f"Expected R8 PASS in stdout:\n{proc.stdout}"

    # Verify main repository is completely clean and untouched
    status_proc = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert status_proc.stdout.strip() == "", (
        f"Main repository has uncommitted changes:\n{status_proc.stdout}"
    )

    # Verify temporary worktree was removed
    worktrees_proc = subprocess.run(
        ["git", "-C", str(repo), "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    worktree_lines = [
        line
        for line in worktrees_proc.stdout.splitlines()
        if line.startswith("worktree ")
    ]
    assert len(worktree_lines) == 1, (
        f"Expected exactly 1 worktree (main), got:\n{worktrees_proc.stdout}"
    )

    # Verify files created inside worktree were not leaked to main repository
    assert not (repo / "helper.py").exists(), (
        "helper.py was leaked into main repository tree"
    )


class Test_Execution_Infra_Acceptance_Integration:
    def test_EVI_AR_01_integration_runner(self, tmp_path: Path) -> None:
        """[EVI-AR-01] [Tier C - Integration] Isolated scratch worktree execution runner."""
        test_EVI_AR_01_readiness_replay_isolated_worktree(tmp_path)
