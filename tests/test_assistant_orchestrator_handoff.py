"""Role 2.1/2.2/2.3 handoff and brief contract tests.

Guards the four-persona handoff contract emitted by `resume_context.py --emit-prompt` and the
packaged `handoff-template.md`.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RESUME_SCRIPT = REPO_ROOT / "scripts" / "resume_context.py"
HANDOFF_TEMPLATE = REPO_ROOT / "skills" / "dev-lifecycle" / "references" / "handoff-template.md"

ASSISTANT_BANNER = "[PERSONA: AI ASSISTANT — ORCHESTRATOR]"
ORCHESTRATOR_BANNER = "[PERSONA: Role 2.2 Orchestrator]"
ARCHITECT_BANNER = "[PERSONA: Role 2.1 AI Architect & Reviewer]"
PROGRAMMER_BANNER = "[PERSONA: Role 2.3 Programmer — Senior TDD Software Engineer]"


@pytest.fixture(autouse=True)
def _isolated_host_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Isolate HOME, REAL_HOME, WORKSPACE_ROOT, USER, and profile vars from the host."""
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("REAL_HOME", str(home))
    monkeypatch.setenv("WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("USER", "nobody")
    monkeypatch.delenv("AGY_PROFILE", raising=False)
    monkeypatch.delenv("ANTIGRAVITY_PROFILE", raising=False)
    return home


def _emit(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {
        **os.environ,
        "HOME": str(home),
        "REAL_HOME": str(home),
        "WORKSPACE_ROOT": str(tmp_path),
        "USER": "nobody",
    }
    env.pop("AGY_PROFILE", None)
    env.pop("ANTIGRAVITY_PROFILE", None)
    return subprocess.run(
        [sys.executable, str(RESUME_SCRIPT), *args],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("mode", ["principal-review", "implement", "cross-review", "finish"])
def test_session_handoff_prompts_bind_orchestrator(tmp_path: Path, mode: str) -> None:
    proc = _emit(tmp_path, "--emit-prompt", mode, "--epic", "demo-epic")
    assert proc.returncode == 0, proc.stderr
    assert ORCHESTRATOR_BANNER in proc.stdout
    assert "--role orchestrator" in proc.stdout
    assert "--role programmer" not in proc.stdout
    assert PROGRAMMER_BANNER not in proc.stdout


def test_assistant_handoff_prompt_binds_architect_reviewer(tmp_path: Path) -> None:
    proc = _emit(tmp_path, "--emit-prompt", "assistant", "--epic", "demo-epic")
    assert proc.returncode == 0, proc.stderr
    assert ARCHITECT_BANNER in proc.stdout
    assert "--role architect" in proc.stdout
    assert "--role programmer" not in proc.stdout
    assert PROGRAMMER_BANNER not in proc.stdout


@pytest.mark.parametrize("mode", ["implement", "cross-review", "finish"])
def test_orchestrating_prompts_dispatch_programmer_via_agy(tmp_path: Path, mode: str) -> None:
    proc = _emit(tmp_path, "--emit-prompt", mode, "--epic", "demo-epic")
    assert proc.returncode == 0, proc.stderr
    assert "agy --model gemini-4-hydrogen-xhigh --effort xhigh --mode auto" in proc.stdout
    assert "orchestration-roles.md" in proc.stdout
    assert "--emit-prompt brief" in proc.stdout


@pytest.mark.parametrize(
    ("brief_role", "summary_key"),
    [
        ("task-implementer", "non_test_modules_changed"),
        ("review-fixer", "fix_shas"),
        ("gate4-verifier", "candidate_sha"),
    ],
)
def test_brief_prompt_binds_programmer_subagent(tmp_path: Path, brief_role: str, summary_key: str) -> None:
    proc = _emit(
        tmp_path, "--emit-prompt", "brief", "--brief-role", brief_role, "--epic", "demo-epic"
    )
    assert proc.returncode == 0, proc.stderr
    assert PROGRAMMER_BANNER in proc.stdout
    assert "--role programmer" in proc.stdout
    assert brief_role in proc.stdout
    assert summary_key in proc.stdout
    assert "Never call `manage_worker_pool.py`" in proc.stdout
    assert ARCHITECT_BANNER not in proc.stdout


@pytest.mark.parametrize(
    ("brief_role", "summary_key"),
    [
        ("task-reviewer", "done_gate"),
        ("fix-planner", "plan_markdown"),
    ],
)
def test_brief_prompt_binds_architect_reviewer_subagent(
    tmp_path: Path, brief_role: str, summary_key: str
) -> None:
    proc = _emit(
        tmp_path, "--emit-prompt", "brief", "--brief-role", brief_role, "--epic", "demo-epic"
    )
    assert proc.returncode == 0, proc.stderr
    assert ARCHITECT_BANNER in proc.stdout
    assert "--role architect" in proc.stdout
    assert brief_role in proc.stdout
    assert summary_key in proc.stdout
    assert "agy --sandbox --mode plan --model gemini-4-argon-high --effort high" in proc.stdout
    assert "do NOT edit files" in proc.stdout
    assert PROGRAMMER_BANNER not in proc.stdout


def test_brief_prompt_requires_brief_role(tmp_path: Path) -> None:
    proc = _emit(tmp_path, "--emit-prompt", "brief", "--epic", "demo-epic")
    assert proc.returncode == 2
    assert "usage:" in proc.stderr
    assert "--brief-role" in proc.stderr
    assert "Traceback" not in proc.stderr
    assert "NameError" not in proc.stderr


def test_role_banners_declare_four_persona_roles(tmp_path: Path) -> None:
    orch = _emit(tmp_path, "--role", "orchestrator", "--epic", "demo-epic", "--compact")
    assert "Role 2.2 Orchestrator" in orch.stdout
    arch = _emit(tmp_path, "--role", "architect", "--epic", "demo-epic", "--compact")
    assert "Role 2.1 AI Architect & Reviewer" in arch.stdout
    asst = _emit(tmp_path, "--role", "assistant", "--epic", "demo-epic", "--compact")
    assert "Role 2.1 AI Architect & Reviewer" in asst.stdout


def test_handoff_template_resume_prompt_binds_assistant_orchestrator() -> None:
    text = HANDOFF_TEMPLATE.read_text(encoding="utf-8")
    resume_block = text.split("## Resume Prompt", 1)[1].split("## Execution Guardrails", 1)[0]
    assert ASSISTANT_BANNER in resume_block
    assert "--role assistant" in resume_block
    assert "--role programmer" not in resume_block
    assert "orchestration-roles.md" in resume_block
