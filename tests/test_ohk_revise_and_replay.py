"""Tier C integration tests for Task 02: Post-rebase revise re-anchoring and R8 replay skip.

Covers BDD Scenarios:
- OHK-HP-02: Re-anchor handoff after rebasing an active Stage 3 epic branch
- OHK-EC-02: Check epic readiness --replay skips R8 when contract-based tasks have zero test-creation directives
- OHK-ST-02: Replay engine still enforces strict RED and GREEN checks on directive-bearing tasks
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
PACKAGE_SCRIPT = SCRIPTS_DIR / "package_epic.py"
READINESS_SCRIPT = SCRIPTS_DIR / "check_epic_readiness.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from test_check_epic_readiness import build_ready_epic  # noqa: E402


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def _isolated_env(home: Path, cwd: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["REAL_HOME"] = str(home)
    env["WORKSPACE_ROOT"] = str(cwd)
    for key in (
        "AGY_PROFILE",
        "ANTIGRAVITY_PROFILE",
        "AGY_PROGRAMMER_MODEL",
        "AGY_PROGRAMMER_EFFORT",
    ):
        env.pop(key, None)
    return env


def _run_script(
    script: Path, cwd: Path, args: list[str], *, home: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(script), *args],
        cwd=cwd,
        env=_isolated_env(home, cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def _init_repo(tmp_path: Path, *, branch: str = "main") -> tuple[Path, Path]:
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)

    _git(repo, "init", "-q", "-b", branch)
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    return repo, home


def _write_task_mirrors(repo: Path, epic_dir: str, name: str, epic_text: str) -> None:
    (repo / ".devtool" / "epic" / epic_dir / name).write_text(
        epic_text, encoding="utf-8"
    )
    feat_text = epic_text.replace(
        f"]({epic_dir}.en.md)",
        f"](../epic/{epic_dir}/{epic_dir}.en.md)",
    )
    (repo / ".devtool" / "features" / name).write_text(feat_text, encoding="utf-8")


def test_ohk_hp_02_package_revise_after_rebase(tmp_path: Path) -> None:
    """[OHK-HP-02] [Tier C - Integration] Re-anchor handoff after rebasing an active Stage 3 epic branch."""
    repo, home = _init_repo(tmp_path, branch="main")
    build_ready_epic(repo)

    # Create active epic branch from main and commit design docs
    _git(repo, "checkout", "-q", "-b", "epic/demo-epic")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Add demo epic design")
    old_sha = _git(repo, "rev-parse", "--short", "HEAD").stdout.strip()

    # Package initially on pre-rebase Design commit
    pkg = _run_script(PACKAGE_SCRIPT, repo, ["demo_epic"], home=home)
    assert pkg.returncode == 0, f"Initial package failed:\n{pkg.stdout}\n{pkg.stderr}"
    handoff_path = repo / ".devtool" / "epic" / "demo_epic" / "handoff.md"
    assert f"- **Design commit**: `{old_sha}`" in handoff_path.read_text(
        encoding="utf-8"
    )

    # Simulate active Stage 3 progress: task_1 in-progress with an already-created (new) artifact
    task_1_path = repo / ".devtool" / "epic" / "demo_epic" / "task_1.md"
    task_1_text = task_1_path.read_text(encoding="utf-8")
    task_1_text = task_1_text.replace('status: "todo"', 'status: "in-progress"', 1)
    task_1_text = task_1_text.replace(
        "Allowed files:\n- `tool.py`\n",
        "Allowed files:\n- `tool.py`\n- `stage3_artifact.py` (new)\n",
    )
    _write_task_mirrors(repo, "demo_epic", "task_1.md", task_1_text)
    (repo / "stage3_artifact.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Commit packaged handoff and Stage 3 progress")

    # Advance main and rebase epic branch onto main so old_sha is no longer an ancestor
    _git(repo, "checkout", "-q", "main")
    (repo / "base_advance.txt").write_text("base update\n", encoding="utf-8")
    _git(repo, "add", "base_advance.txt")
    _git(repo, "commit", "-q", "-m", "Advance base branch")

    _git(repo, "checkout", "-q", "epic/demo-epic")
    _git(repo, "rebase", "-q", "main")
    new_sha = _git(repo, "rev-parse", "--short", "HEAD").stdout.strip()
    assert new_sha != old_sha

    ancestor = _git(repo, "merge-base", "--is-ancestor", old_sha, "HEAD", check=False)
    assert ancestor.returncode != 0, (
        "Expected old_sha to be rewritten and non-ancestor after rebase"
    )

    # Normal readiness without --reanchoring must still fail R7 on stale non-ancestor SHA
    normal_check = _run_script(
        READINESS_SCRIPT, repo, ["--post-design", "demo_epic"], home=home
    )
    assert normal_check.returncode == 1
    assert "R7 FAIL" in normal_check.stdout
    assert "is not an ancestor of HEAD" in normal_check.stdout

    # Direct --reanchoring readiness check must skip only the ancestor check and pass R7
    reanchor_check = _run_script(
        READINESS_SCRIPT,
        repo,
        ["--post-design", "--reanchoring", "demo_epic"],
        home=home,
    )
    assert reanchor_check.returncode == 0, (
        f"Expected --reanchoring to pass:\n{reanchor_check.stdout}\n{reanchor_check.stderr}"
    )
    assert "R7 PASS" in reanchor_check.stdout

    # package_epic.py --revise must invoke check_epic_readiness.py with --reanchoring and re-anchor
    revise = _run_script(
        PACKAGE_SCRIPT,
        repo,
        ["demo_epic", "--revise", "--reason", "Rebased onto base"],
        home=home,
    )
    assert revise.returncode == 0, (
        f"package_epic.py --revise failed after rebase:\n{revise.stdout}\n{revise.stderr}"
    )

    updated_handoff = handoff_path.read_text(encoding="utf-8")
    assert f"- **Design commit**: `{new_sha}`" in updated_handoff
    assert f"(`{old_sha}` -> `{new_sha}`)" in updated_handoff
    assert "Rebased onto base" in updated_handoff

    # Subsequent standard --post-design check (without --reanchoring) passes R7 cleanly
    post_check = _run_script(
        READINESS_SCRIPT, repo, ["--post-design", "demo_epic"], home=home
    )
    assert post_check.returncode == 0, (
        f"Post-revise readiness check failed:\n{post_check.stdout}\n{post_check.stderr}"
    )
    assert "R7 PASS" in post_check.stdout


def test_ohk_ec_02_replay_skips_contract_tasks_without_test_directives(
    tmp_path: Path,
) -> None:
    """[OHK-EC-02] [Tier C - Integration] Check epic readiness --replay skips R8 when contract-based tasks have zero test-creation directives."""
    repo, home = _init_repo(tmp_path, branch="main")
    build_ready_epic(repo)

    # Convert both tasks into standard contract-based tasks with (new) pytest paths and zero directives
    for task_name, test_rel in (
        ("task_1.md", "tests/test_contract_one.py"),
        ("task_2.md", "tests/test_contract_two.py"),
    ):
        task_path = repo / ".devtool" / "epic" / "demo_epic" / task_name
        text = task_path.read_text(encoding="utf-8")
        text = text.replace(
            "Allowed files:\n- `tool.py`\n",
            f"Allowed files:\n- `tool.py`\n- `{test_rel}` (new)\n",
        )
        text = text.replace(
            "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
            f'| V1 | RED | `python3 -m pytest -q {test_rel}` | exit 1; contains "FAILED" | — |',
        )
        text = text.replace(
            "| V1 | RED | `python3 tool.py red2` | exit 1 | — |",
            f'| V1 | RED | `python3 -m pytest -q {test_rel}` | exit 1; contains "FAILED" | — |',
        )
        text = text.replace(
            "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
            f'| V2 | GREEN | `python3 -m pytest -q {test_rel}` | exit 0; contains "passed" | — |\n'
            "| V6 | REGRESSION | `python3 tool.py` | exit 0 | — |",
        )
        text = text.replace(
            "| V2 | GREEN | `python3 tool.py green2` | exit 0 | — |",
            f'| V2 | GREEN | `python3 -m pytest -q {test_rel}` | exit 0; contains "passed" | — |\n'
            "| V6 | REGRESSION | `python3 tool.py` | exit 0 | — |",
        )
        text = text.replace(
            "`ruff check tool.py`",
            f"`ruff check tool.py {test_rel}`",
        )
        text = text.replace(
            "`mypy tool.py`",
            f"`mypy tool.py {test_rel}`",
        )
        _write_task_mirrors(repo, "demo_epic", task_name, text)

    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Add contract-based epic tasks")

    res = _run_script(READINESS_SCRIPT, repo, ["demo_epic", "--replay"], home=home)
    assert res.returncode == 0, (
        f"Expected exit 0 with R8 SKIP, got {res.returncode}:\n{res.stdout}\n{res.stderr}"
    )
    assert "R8 SKIP" in res.stdout, f"Expected R8 SKIP in stdout:\n{res.stdout}"
    assert "R8 FAIL" not in res.stdout, f"Unexpected R8 FAIL in stdout:\n{res.stdout}"
    assert "R8 PASS" not in res.stdout, (
        f"Should not emit R8 PASS alongside R8 SKIP:\n{res.stdout}"
    )
    assert "Result: 0 FAIL" in res.stdout


def test_ohk_st_02_replay_enforces_strict_red_and_green_on_directive_tasks(
    tmp_path: Path,
) -> None:
    """[OHK-ST-02] [Tier C - Integration] Replay engine still enforces strict RED and GREEN checks on directive-bearing tasks."""
    repo, home = _init_repo(tmp_path, branch="main")
    build_ready_epic(repo)

    # Make tool.py clean for ruff/mypy and pass its TIER-C command
    (repo / "tool.py").write_text(
        "import pathlib\n"
        "import sys\n\n\n"
        "def run() -> None:\n"
        "    if len(sys.argv) > 1 and sys.argv[1] == 'int':\n"
        "        p = pathlib.Path('build/test-results/int.xml')\n"
        "        p.parent.mkdir(parents=True, exist_ok=True)\n"
        '        p.write_text(\'<testsuite><testcase name="int"/></testsuite>\', encoding="utf-8")\n'
        "        sys.exit(0)\n\n\n"
        "if __name__ == '__main__':\n"
        "    run()\n",
        encoding="utf-8",
    )

    def _build_directive_task(return_expr: str) -> str:
        task_path = repo / ".devtool" / "epic" / "demo_epic" / "task_1.md"
        base = task_path.read_text(encoding="utf-8")
        if "## Changes" in base:
            return base.replace("return 42", return_expr)

        text = base.replace(
            "Allowed files:\n- `tool.py`\n",
            "Allowed files:\n- `tool.py`\n- `src_replay_mod.py` (new)\n- `tests/test_sample_replay.py` (new)\n",
        )
        directives_block = (
            "## Changes\n\n"
            "Create tests/test_sample_replay.py:\n"
            "```python\n"
            "import sys\n"
            "from pathlib import Path\n\n"
            "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n\n\n"
            "def test_sample_replay() -> None:\n"
            "    from src_replay_mod import compute\n\n"
            "    assert compute() == 42\n"
            "```\n\n"
            "Create src_replay_mod.py:\n"
            "```python\n"
            "def compute() -> int:\n"
            f"    {return_expr}\n"
            "```\n\n"
        )
        text = text.replace(
            "## Requirement Analysis", directives_block + "## Requirement Analysis"
        )
        text = text.replace(
            "| V1 | RED | `python3 tool.py red` | exit 1 | — |",
            '| V1 | RED | `python3 -m pytest -q tests/test_sample_replay.py` | exit 1; contains "FAILED" | — |',
        )
        text = text.replace(
            "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
            '| V2 | GREEN | `python3 -m pytest -q tests/test_sample_replay.py` | exit 0; contains "passed" | — |\n'
            "| V6 | REGRESSION | `python3 tool.py` | exit 0 | — |",
        )
        text = text.replace(
            "| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |",
            "| V3 | TIER-B | `ruff check tool.py src_replay_mod.py tests/test_sample_replay.py` | exit 0 | — |",
        )
        text = text.replace(
            "| V4 | TIER-B | `mypy tool.py` | exit 0 | — |",
            "| V4 | TIER-B | `mypy --ignore-missing-imports tool.py src_replay_mod.py tests/test_sample_replay.py` | exit 0 | — |",
        )
        return text

    # Keep task_2 as a contract-based task without directives so mixed epic still enforces task_1 replay
    task_2_path = repo / ".devtool" / "epic" / "demo_epic" / "task_2.md"
    task_2_text = task_2_path.read_text(encoding="utf-8")
    task_2_text = task_2_text.replace(
        "Allowed files:\n- `tool.py`\n",
        "Allowed files:\n- `tool.py`\n- `tests/test_contract_sibling.py` (new)\n",
    )
    task_2_text = task_2_text.replace(
        "`ruff check tool.py`",
        "`ruff check tool.py tests/test_contract_sibling.py`",
    )
    task_2_text = task_2_text.replace(
        "`mypy tool.py`",
        "`mypy tool.py tests/test_contract_sibling.py`",
    )
    _write_task_mirrors(repo, "demo_epic", "task_2.md", task_2_text)

    good_task_1 = _build_directive_task("return 42")
    _write_task_mirrors(repo, "demo_epic", "task_1.md", good_task_1)

    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Add directive-bearing task_1")

    pass_res = _run_script(READINESS_SCRIPT, repo, ["demo_epic", "--replay"], home=home)
    assert pass_res.returncode == 0, (
        f"Expected R8 PASS on valid directives:\n{pass_res.stdout}\n{pass_res.stderr}"
    )
    assert "R8 PASS" in pass_res.stdout, f"Expected R8 PASS:\n{pass_res.stdout}"
    assert "R8 SKIP" not in pass_res.stdout

    # Now break the embedded implementation directive so GREEN fails
    broken_task_1 = _build_directive_task("return 99")
    _write_task_mirrors(repo, "demo_epic", "task_1.md", broken_task_1)

    fail_res = _run_script(READINESS_SCRIPT, repo, ["demo_epic", "--replay"], home=home)
    assert fail_res.returncode == 1, (
        f"Expected R8 FAIL when directive breaks GREEN:\n{fail_res.stdout}\n{fail_res.stderr}"
    )
    assert "R8 FAIL" in fail_res.stdout, f"Expected R8 FAIL:\n{fail_res.stdout}"


class Test_Ohk_Revise_And_Replay_Integration:
    """[Tier C - Integration] Integration runner provenance for OHK-HP-02, OHK-EC-02, and OHK-ST-02."""

    def test_ohk_hp_02_integration(self, tmp_path: Path) -> None:
        """[OHK-HP-02] [Tier C - Integration] Re-anchor handoff after rebase."""
        test_ohk_hp_02_package_revise_after_rebase(tmp_path)

    def test_ohk_ec_02_integration(self, tmp_path: Path) -> None:
        """[OHK-EC-02] [Tier C - Integration] Replay skips contract tasks without test directives."""
        test_ohk_ec_02_replay_skips_contract_tasks_without_test_directives(tmp_path)

    def test_ohk_st_02_integration(self, tmp_path: Path) -> None:
        """[OHK-ST-02] [Tier C - Integration] Replay enforces strict RED/GREEN on directive tasks."""
        test_ohk_st_02_replay_enforces_strict_red_and_green_on_directive_tasks(tmp_path)
