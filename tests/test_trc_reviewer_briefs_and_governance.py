"""Unit tests for Task 2: Blocker-only task-reviewer briefs and Role 2.2 governance exceptions.

Covers BDD Scenarios:
- TRC-HP-02: Task-reviewer brief emitter renders Pass 1 comprehensive rubric and Pass 2 delta-only rubric without Vietnamese mirror paths
- TRC-AR-01: Governance rules and skills document bounded Role 2.2 triage-fix and finalize-slot exceptions within strict byte and word caps
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
RESUME_SCRIPT = SCRIPTS_DIR / "resume_context.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import persona_config  # noqa: E402


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _section(text: str, heading_prefix: str) -> str:
    match = re.search(
        rf"^{re.escape(heading_prefix)}.*?(?=^## |\Z)",
        text,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match is not None, f"Missing section {heading_prefix!r}"
    return match.group(0)


def _init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-q", "-b", "main"], cwd=repo, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"], cwd=repo, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "Initial commit"],
        cwd=repo,
        capture_output=True,
        check=True,
    )


def _run_resume_cli(
    cwd: Path,
    args: list[str],
    *,
    home_dir: Path,
) -> subprocess.CompletedProcess[str]:
    home_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.pop("AGY_PROFILE", None)
    env.pop("ANTIGRAVITY_PROFILE", None)
    env["HOME"] = str(home_dir)
    env["REAL_HOME"] = str(home_dir)
    env["WORKSPACE_ROOT"] = str(cwd)
    env["USER"] = "testuser"
    return subprocess.run(
        [sys.executable, str(RESUME_SCRIPT), *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _seed_trc_epic(repo: Path) -> Path:
    epic_dir = repo / ".devtool" / "epic" / "trc_epic"
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / "trc_epic.md").write_text("# HLD: TRC Epic\n", encoding="utf-8")
    (epic_dir / "bdd_scenarios.md").write_text("# BDD Scenarios\n", encoding="utf-8")
    (epic_dir / "trc_epic.vi.md").write_text(
        "# HLD: Ban tieng Viet\n", encoding="utf-8"
    )
    return epic_dir


def test_trc_hp_02_task_reviewer_pass1_and_pass2_briefs(tmp_path: Path) -> None:
    """[TRC-HP-02] [Tier A - Unit] Task-reviewer brief emitter renders Pass 1 comprehensive and Pass 2 delta-only rubrics without .vi.md."""
    repo = tmp_path / "repo"
    home_dir = tmp_path / "home"
    _init_git_repo(repo)
    _seed_trc_epic(repo)

    blockers_payload = [
        {
            "id": "BLK-1",
            "category": "BDD_VIOLATION",
            "file": "src/app.py",
            "summary": "Missing null guard",
        }
    ]
    blockers_file = repo / "pass1_blockers.json"
    blockers_file.write_text(json.dumps(blockers_payload), encoding="utf-8")

    arch_binding = persona_config.resolve_persona(
        "ai_architect_reviewer", repo, real_home=home_dir
    )
    expected_ro_argv = shlex.join(
        persona_config.build_dispatch_argv(arch_binding, "read-only")
    )

    pass1_proc = _run_resume_cli(
        repo,
        [
            "--emit-prompt",
            "brief",
            "--brief-role",
            "task-reviewer",
            "--epic",
            "trc_epic",
        ],
        home_dir=home_dir,
    )
    assert pass1_proc.returncode == 0, pass1_proc.stderr
    p1_out = pass1_proc.stdout
    assert "Role 2.1 AI Architect & Reviewer" in p1_out
    assert expected_ro_argv in p1_out
    assert '"pass": 1' in p1_out
    assert '"verdict": "APPROVED|CHANGES_REQUESTED"' in p1_out
    assert '"blockers":' in p1_out
    assert '"observations":' in p1_out
    assert "BLOCKER" in p1_out
    assert "NON_BLOCKING_OBSERVATION" in p1_out
    assert "Observations (Non-Blocking)" in p1_out
    for category in (
        "BDD_VIOLATION",
        "CONTRACT_SCHEMA_VIOLATION",
        "RUNTIME_SAFETY",
        "OWNERSHIP_ARCHITECTURE_VIOLATION",
    ):
        assert category in p1_out
    assert "do not edit" in p1_out.lower() or "forbid" in p1_out.lower()
    assert "mark `done` and commit" not in p1_out
    assert ".vi.md" not in p1_out

    pass2_proc = _run_resume_cli(
        repo,
        [
            "--emit-prompt",
            "brief",
            "--brief-role",
            "task-reviewer",
            "--epic",
            "trc_epic",
            "--review-pass",
            "2",
            "--pass1-tree-sha",
            "4b825dc642cb",
            "--blockers-file",
            str(blockers_file),
        ],
        home_dir=home_dir,
    )
    assert pass2_proc.returncode == 0, pass2_proc.stderr
    p2_out = pass2_proc.stdout
    assert "Role 2.1 AI Architect & Reviewer" in p2_out
    assert '"pass": 2' in p2_out
    assert '"verdict": "APPROVED|CHANGES_REQUESTED"' in p2_out
    assert "PASS 2 DELTA-ONLY VERIFICATION RULES" in p2_out
    assert "git diff 4b825dc642cb" in p2_out
    assert "BLK-1" in p2_out
    assert "Missing null guard" in p2_out
    assert "DIRECT_REGRESSION" in p2_out
    assert "strictly forbidden" in p2_out.lower() or "forbid" in p2_out.lower()
    assert ".vi.md" not in p2_out

    impl_proc = _run_resume_cli(
        repo,
        ["--emit-prompt", "implement", "--epic", "trc_epic"],
        home_dir=home_dir,
    )
    assert impl_proc.returncode == 0, impl_proc.stderr
    assert "triage-fix" in impl_proc.stdout
    assert "finalize-slot" in impl_proc.stdout
    assert ".vi.md" not in impl_proc.stdout


def test_trc_hp_02_python_api_and_se02_principal_review_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[TRC-HP-02] emit_handoff_prompt honors keyword-only Pass 2 defaults while keeping principal-review byte-identical [SE-02]."""
    repo = tmp_path / "repo_api"
    home_dir = tmp_path / "home_api"
    _init_git_repo(repo)
    _seed_trc_epic(repo)
    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.setenv("REAL_HOME", str(home_dir))

    blockers_file = repo / "blockers.json"
    blockers_file.write_text(
        json.dumps(
            [
                {
                    "id": "BLK-9",
                    "category": "RUNTIME_SAFETY",
                    "file": "src/worker.py",
                    "summary": "Unchecked None",
                }
            ]
        ),
        encoding="utf-8",
    )

    spec = importlib.util.spec_from_file_location("_trc_resume_probe", RESUME_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    buf_p2 = io.StringIO()
    with contextlib.redirect_stdout(buf_p2):
        mod.emit_handoff_prompt(
            "brief",
            "trc_epic",
            root=repo,
            brief_role="task-reviewer",
            real_home=home_dir,
            review_pass=2,
            pass1_tree_sha="deadbeef1234",
            blockers_file=blockers_file,
        )
    out_p2 = buf_p2.getvalue()
    assert '"pass": 2' in out_p2
    assert "git diff deadbeef1234" in out_p2
    assert "BLK-9" in out_p2
    assert ".vi.md" not in out_p2

    buf_pr = io.StringIO()
    with contextlib.redirect_stdout(buf_pr):
        mod.emit_handoff_prompt(
            "principal-review",
            "<epic_slug>",
            epic_dir="<epic_dir>",
            root=tmp_path / "empty_repo",
            real_home=home_dir,
        )
    emitted_pr = buf_pr.getvalue().strip()
    guide = _read("docs/context-memory-quick-guide.en.md")
    scenario_1 = _section(guide, "## 3. Scenario 1")
    step_2 = scenario_1.split("### Step 2:", 1)[1].split("### Step 3:", 1)[0]
    match = re.search(r"```text\n(.*?)\n```", step_2, flags=re.DOTALL)
    assert match is not None
    assert match.group(1).strip() == emitted_pr


@pytest.mark.parametrize(
    ("extra_args", "expect_exit_non_zero"),
    [
        (["--review-pass", "3"], True),
        (["--review-pass", "0"], True),
        (["--review-pass", "2", "--blockers-file", "does_not_exist.json"], True),
        (["--review-pass", "2", "--pass1-tree-sha", "abc1234def"], False),
    ],
)
def test_trc_hp_02_brief_edge_cases(
    tmp_path: Path,
    extra_args: list[str],
    expect_exit_non_zero: bool,
) -> None:
    """[TRC-HP-02] CLI validates --review-pass choices, rejects missing blockers file, and handles Pass 2 without blockers file."""
    repo = tmp_path / "repo_edge"
    home_dir = tmp_path / "home_edge"
    _init_git_repo(repo)
    _seed_trc_epic(repo)

    proc = _run_resume_cli(
        repo,
        [
            "--emit-prompt",
            "brief",
            "--brief-role",
            "task-reviewer",
            "--epic",
            "trc_epic",
            *extra_args,
        ],
        home_dir=home_dir,
    )
    if expect_exit_non_zero:
        assert proc.returncode != 0
        assert "Traceback" not in proc.stderr
    else:
        assert proc.returncode == 0, proc.stderr
        assert "PASS 2 DELTA-ONLY VERIFICATION RULES" in proc.stdout
        assert "git diff abc1234def" in proc.stdout
        assert ".vi.md" not in proc.stdout


def test_trc_ar_01_governance_exceptions_and_caps() -> None:
    """[TRC-AR-01] [Tier A - Unit] Governance rules and skills document bounded Role 2.2 triage-fix/finalize-slot exceptions within byte/word caps."""
    critical_rules = _read("rules/CRITICAL_RULES.md")
    cr_bytes = len(critical_rules.encode("utf-8"))
    assert cr_bytes <= 8192, f"CRITICAL_RULES.md byte cap exceeded: {cr_bytes} > 8192"

    rule_6 = _section(critical_rules, "## 6. ")
    assert "APPROVED" not in rule_6, "Rule 6 must never contain 'APPROVED' ([SE-01])"

    rule_8 = _section(critical_rules, "## 8. ")
    for token in (
        "ai_architect_reviewer",
        "orchestrator",
        "programmer",
        "dev-config",
        "--checkpoint",
        "gate2_tasks_locked",
        "subagent_returned",
        "wave_merged",
        "model_unavailable",
        "turn_budget",
        "low_quota_stop",
        "quota_low",
        "low-quota",
        "quota-check",
        "triage-fix",
        "finalize-slot",
    ):
        assert token in rule_8, f"Rule 8 missing required token {token!r}"
    assert "session map" in rule_8.lower()

    dev_lifecycle = _read("skills/dev-lifecycle/SKILL.md")
    lc_words = len(dev_lifecycle.split())
    assert lc_words <= 2500, f"dev-lifecycle/SKILL.md exceeded 2500 words: {lc_words}"
    assert "triage-fix" in dev_lifecycle
    assert "finalize-slot" in dev_lifecycle
    assert "2" in dev_lifecycle and "review" in dev_lifecycle.lower()

    dev_impl = _read("skills/dev-implementation/SKILL.md")
    impl_words = len(dev_impl.split())
    assert impl_words <= 4500, (
        f"dev-implementation/SKILL.md exceeded 4500 words: {impl_words}"
    )
    for mandatory_ref in (
        "MANDATORY: read [references/entry-point-and-resume.md](references/entry-point-and-resume.md",
        "MANDATORY: read [references/worker-execution-rules.md](references/worker-execution-rules.md)",
        "MANDATORY: read [references/gate4-semantic-integrity.md](references/gate4-semantic-integrity.md)",
    ):
        assert mandatory_ref in dev_impl, (
            f"dev-implementation/SKILL.md missing pointer {mandatory_ref!r}"
        )

    roles = _read("skills/dev-lifecycle/references/orchestration-roles.md")
    for text_name, text in (
        ("orchestration-roles.md", roles),
        ("dev-implementation/SKILL.md", dev_impl),
    ):
        for token in (
            "triage-fix",
            "finalize-slot",
            "BLOCKER",
            "NON_BLOCKING_OBSERVATION",
            "RiskAssessment",
            "<= 30",
        ):
            assert token in text, f"{text_name} missing {token!r}"
        assert "read-only" in text.lower() or "mechanical" in text.lower()
        assert "src/" in text and "tests/" in text

    assert "direct reading or editing of `src/` / `tests/`" in roles.lower()
    assert "direct `run_task_checks.py` execution" in roles.lower()
    assert "ELIGIBLE_FOR_SHORT_CIRCUIT" in roles
    assert "bounded_diff" in roles
    assert "pass1_blockers" in roles
    assert "single permitted role 2.2 semantic ruling" in roles.lower()
    assert "never reads/edits `src/`/`tests/`" in dev_impl
    assert "max_task_review_passes" in roles
    assert "max_fix_passes" in roles

    summary_section = _section(roles, "## 3. Summary Contracts")
    reviewer_row = next(
        line
        for line in summary_section.splitlines()
        if line.lstrip().startswith("| `task-reviewer`")
    )
    for key in (
        "`task_id`",
        "`pass`",
        "`verdict`",
        "`APPROVED`",
        "`CHANGES_REQUESTED`",
        "`head_sha`",
        "`done_gate`",
        "`blockers`",
        "`observations`",
    ):
        assert key in reviewer_row, f"task-reviewer summary row missing {key!r}"

    checklists = _read("skills/dev-lifecycle/references/governance-checklists.md")
    for token in ("BLOCKER", "NON_BLOCKING_OBSERVATION", "Two-Tier Risk Assessment"):
        assert token in checklists, f"governance-checklists.md missing {token!r}"

    handoff = _read("skills/dev-lifecycle/references/handoff-template.md")
    for token in ("triage-fix", "finalize-slot"):
        assert token in handoff, f"handoff-template.md missing {token!r}"

    sdd_skill = _read("skills/subagent-driven-development/SKILL.md")
    for token in (
        "max_task_review_passes = 2",
        "max_fix_passes = 1",
        "BLOCKER",
        "NON_BLOCKING_OBSERVATION",
        "APPROVED",
        "CHANGES_REQUESTED",
        "-U5",
        "Zero-Fluff",
        "StartLine",
        "EndLine",
        "review_tier",
        "security",
        "architecture",
        "concurrency",
        "contract",
        "> 2",
        "skip",
    ):
        assert token in sdd_skill, (
            f"subagent-driven-development/SKILL.md missing {token!r}"
        )

    tr_prompt = _read("skills/subagent-driven-development/task-reviewer-prompt.md")
    for token in (
        "BLOCKER",
        "NON_BLOCKING_OBSERVATION",
        "APPROVED",
        "CHANGES_REQUESTED",
        "Critical",
        "run_task_checks.py status",
        "Role 2.1 AI Architect & Reviewer",
        "check_bdd_traceability.py",
    ):
        assert token in tr_prompt, f"task-reviewer-prompt.md missing {token!r}"

    rr_prompt = _read("skills/subagent-driven-development/re-review-prompt.md")
    for token in (
        "Delta-Only",
        "DIRECT_REGRESSION",
        "APPROVED",
        "CHANGES_REQUESTED",
    ):
        assert token in rr_prompt, f"re-review-prompt.md missing {token!r}"
