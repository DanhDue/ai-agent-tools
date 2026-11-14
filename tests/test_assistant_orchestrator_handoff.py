"""AI Assistant (Role 2.2) is the Orchestrator; AI Programmer (Role 2.3) runs as dispatched subagents.

Guards the two-tier handoff contract emitted by `resume_context.py --emit-prompt` and the
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
PROGRAMMER_BANNER = "[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]"


def _emit(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {**os.environ, "HOME": str(home), "USER": "nobody"}
    return subprocess.run(
        [sys.executable, str(RESUME_SCRIPT), *args],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("mode", ["principal-review", "implement", "cross-review", "finish", "assistant"])
def test_session_handoff_prompts_bind_assistant_orchestrator(tmp_path: Path, mode: str) -> None:
    proc = _emit(tmp_path, "--emit-prompt", mode, "--epic", "demo-epic")
    assert proc.returncode == 0, proc.stderr
    assert ASSISTANT_BANNER in proc.stdout
    assert "--role assistant" in proc.stdout
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
        ("task-reviewer", "done_gate"),
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
    assert ASSISTANT_BANNER not in proc.stdout


def test_brief_prompt_requires_brief_role(tmp_path: Path) -> None:
    proc = _emit(tmp_path, "--emit-prompt", "brief", "--epic", "demo-epic")
    assert proc.returncode != 0
    assert "--brief-role" in proc.stderr


def test_assistant_role_banner_declares_orchestration(tmp_path: Path) -> None:
    proc = _emit(tmp_path, "--role", "assistant", "--epic", "demo-epic", "--compact")
    assert "ORCHESTRATOR" in proc.stdout


def test_handoff_template_resume_prompt_binds_assistant_orchestrator() -> None:
    text = HANDOFF_TEMPLATE.read_text(encoding="utf-8")
    resume_block = text.split("## Resume Prompt", 1)[1].split("## Execution Guardrails", 1)[0]
    assert ASSISTANT_BANNER in resume_block
    assert "--role assistant" in resume_block
    assert "--role programmer" not in resume_block
    assert "orchestration-roles.md" in resume_block
