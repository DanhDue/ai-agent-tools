"""Unit and concurrency tests for Task 02: checkpoints, persona briefs, and English-only prompts.

Covers BDD scenarios:
- FPG-HP-04: Checkpoint writes heartbeat block, epic state file, and one JSONL event
- FPG-HP-05: Briefs and implement prompt name resolved persona binding and never emit .vi.md
- FPG-EC-03: Legacy --role assistant maps to architect; invalid roles rejected by argparse
- FPG-AR-01: Concurrent checkpoints across primary root and worktree stay consistent under lock
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
RESUME_SCRIPT = SCRIPTS_DIR / "resume_context.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import _state_envelope  # noqa: E402
import persona_config  # noqa: E402
import resume_context  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_host_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Isolate HOME, REAL_HOME, WORKSPACE_ROOT, USER, and profile vars from the host."""
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("REAL_HOME", str(home))
    monkeypatch.setenv("WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("USER", "testuser")
    monkeypatch.delenv("AGY_PROFILE", raising=False)
    monkeypatch.delenv("ANTIGRAVITY_PROFILE", raising=False)
    return home


def _init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=repo, capture_output=True, check=True
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
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo,
        capture_output=True,
        check=True,
    )


def _run_resume_cli(
    cwd: Path,
    args: list[str],
    *,
    home_dir: Path,
    workspace_root: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    home_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.pop("AGY_PROFILE", None)
    env.pop("ANTIGRAVITY_PROFILE", None)
    env["HOME"] = str(home_dir)
    env["REAL_HOME"] = str(home_dir)
    env["WORKSPACE_ROOT"] = str(workspace_root or cwd)
    env["USER"] = "testuser"
    return subprocess.run(
        [sys.executable, str(RESUME_SCRIPT), *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_fpg_hp_04_checkpoint_writes_heartbeat_state_and_event(tmp_path: Path) -> None:
    """[FPG-HP-04] Checkpoint updates heartbeat, state Next Immediate Step, JSONL stream, and harvest."""
    repo = tmp_path / "repo"
    home_dir = tmp_path / "home"
    _init_git_repo(repo)
    _state_envelope.update_epic_heartbeat(
        repo,
        "fpg_epic",
        stage="Stage 3",
        active_wave=2,
        active_tasks=["task_03"],
        last_event="seed",
    )
    safe_slug = _state_envelope._sanitize_epic_slug("fpg_epic")
    events_path = repo / ".devtool" / "logs" / f"events_{safe_slug}.jsonl"
    before_lines = (
        events_path.read_text(encoding="utf-8").splitlines()
        if events_path.exists()
        else []
    )

    proc = _run_resume_cli(
        repo,
        [
            "--checkpoint",
            "subagent_returned",
            "--epic",
            "fpg_epic",
            "--next",
            "dispatch task_03 reviewer",
        ],
        home_dir=home_dir,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"

    hb_path = repo / ".devtool" / "state" / f"{safe_slug}.heartbeat.json"
    hb_data = json.loads(hb_path.read_text(encoding="utf-8"))
    cp = hb_data.get("checkpoint")
    assert isinstance(cp, dict)
    assert cp["event"] == "subagent_returned"
    assert cp["next_step"] == "dispatch task_03 reviewer"
    assert cp["turns_since_checkpoint"] == 0
    assert cp["persona"] == "orchestrator"
    assert cp["wave"] == 2
    assert isinstance(cp["head_sha"], str) and len(cp["head_sha"]) >= 7
    assert isinstance(cp["at"], str) and "T" in cp["at"]
    assert cp["low_quota"] is False

    state_text = (repo / ".devtool" / "state" / "fpg_epic.md").read_text(
        encoding="utf-8"
    )
    assert "## Next Immediate Step:" in state_text
    next_section = state_text.split("## Next Immediate Step:", 1)[1]
    assert "dispatch task_03 reviewer" in next_section

    after_lines = events_path.read_text(encoding="utf-8").splitlines()
    new_lines = after_lines[len(before_lines) :]
    assert len(new_lines) == 1
    event_record = json.loads(new_lines[0])
    assert event_record["category"] == "checkpoint"
    assert event_record["event"] == "subagent_returned"

    harvest = _run_resume_cli(repo, [], home_dir=home_dir)
    assert harvest.returncode == 0, harvest.stderr
    assert "subagent_returned" in harvest.stdout
    assert "RECENT PROGRAMMER ACTIVITY" in harvest.stdout
    assert harvest.stdout.index("subagent_returned") < harvest.stdout.index(
        "RECENT PROGRAMMER ACTIVITY"
    )


def test_fpg_hp_05_briefs_and_implement_prompt_persona_binding_no_vi(
    tmp_path: Path,
) -> None:
    """[FPG-HP-05] Briefs and implement prompt name resolved persona bindings and omit .vi.md."""
    repo = tmp_path / "repo"
    home_dir = tmp_path / "home"
    _init_git_repo(repo)

    cfg_dir = repo / ".agents" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "personas.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "active_preset": "default",
                "overrides": {
                    "ai_architect_reviewer": {"model": "argon", "effort": "high"},
                    "orchestrator": {"model": "hydrogen", "effort": "high"},
                },
            }
        ),
        encoding="utf-8",
    )

    epic_dir = repo / ".devtool" / "epic" / "fpg_epic"
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / "fpg_epic.en.md").write_text(
        "# Epic: FPG Governance\n", encoding="utf-8"
    )
    (epic_dir / "fpg_epic.vi.md").write_text(
        "# Epic: Ban tieng Viet\n", encoding="utf-8"
    )
    (epic_dir / "bdd_scenarios.en.md").write_text("# BDD Scenarios\n", encoding="utf-8")
    (epic_dir / "bdd_scenarios.vi.md").write_text("# Kich ban BDD\n", encoding="utf-8")

    arch_binding = persona_config.resolve_persona(
        "ai_architect_reviewer", repo, real_home=home_dir
    )
    expected_ro_argv = shlex.join(
        persona_config.build_dispatch_argv(arch_binding, "read-only")
    )

    rev_proc = _run_resume_cli(
        repo,
        [
            "--emit-prompt",
            "brief",
            "--brief-role",
            "task-reviewer",
            "--epic",
            "fpg_epic",
        ],
        home_dir=home_dir,
    )
    assert rev_proc.returncode == 0, rev_proc.stderr
    assert "Role 2.1 AI Architect & Reviewer" in rev_proc.stdout
    assert expected_ro_argv in rev_proc.stdout
    assert "--model gemini-4-argon-high --effort high" in rev_proc.stdout
    assert (
        "forbid" in rev_proc.stdout.lower() or "do not edit" in rev_proc.stdout.lower()
    )
    assert "mark `done` and commit" not in rev_proc.stdout
    assert ".vi.md" not in rev_proc.stdout

    plan_proc = _run_resume_cli(
        repo,
        ["--emit-prompt", "brief", "--brief-role", "fix-planner", "--epic", "fpg_epic"],
        home_dir=home_dir,
    )
    assert plan_proc.returncode == 0, plan_proc.stderr
    assert "Role 2.1 AI Architect & Reviewer" in plan_proc.stdout
    assert expected_ro_argv in plan_proc.stdout
    assert "--model gemini-4-argon-high --effort high" in plan_proc.stdout
    assert "PLANNED|ESCALATE" in plan_proc.stdout
    assert "halt_criteria" in plan_proc.stdout
    assert "plan_markdown" in plan_proc.stdout
    assert ".vi.md" not in plan_proc.stdout

    impl_proc = _run_resume_cli(
        repo,
        ["--emit-prompt", "implement", "--epic", "fpg_epic"],
        home_dir=home_dir,
    )
    assert impl_proc.returncode == 0, impl_proc.stderr
    assert "Role 2.2 Orchestrator" in impl_proc.stdout
    assert "gemini-4-hydrogen-high" in impl_proc.stdout
    assert "high" in impl_proc.stdout
    assert ".vi.md" not in impl_proc.stdout


def test_fpg_ec_03_legacy_assistant_role_maps_to_architect(tmp_path: Path) -> None:
    """[FPG-EC-03] --role assistant normalizes to architect and invalid role exits non-zero."""
    repo = tmp_path / "repo"
    home_dir = tmp_path / "home"
    _init_git_repo(repo)

    proc = _run_resume_cli(
        repo,
        ["--state", "--epic", "fpg_epic", "--role", "assistant", "--status", "Stage 2"],
        home_dir=home_dir,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"

    state_text = (repo / ".devtool" / "state" / "fpg_epic.md").read_text(
        encoding="utf-8"
    )
    assert "Role: architect" in state_text
    assert "Role: assistant" not in state_text

    bad_proc = _run_resume_cli(repo, ["--role", "reviewer"], home_dir=home_dir)
    assert bad_proc.returncode != 0
    assert "invalid choice" in bad_proc.stderr.lower()


def test_fpg_ar_01_concurrent_checkpoints_root_and_worktree_lock(
    tmp_path: Path,
) -> None:
    """[FPG-AR-01] Concurrent checkpoint updates across root and worktree stay consistent under lock."""
    repo = tmp_path / "repo"
    _init_git_repo(repo)

    wt = repo / ".worktrees" / "conc_epic"
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "worktree",
            "add",
            str(wt),
            "-b",
            "epic/conc_epic",
            "main",
        ],
        capture_output=True,
        check=True,
    )
    (repo / ".devtool" / "state").mkdir(parents=True, exist_ok=True)
    (wt / ".devtool" / "state").mkdir(parents=True, exist_ok=True)
    _state_envelope.update_epic_heartbeat(repo, "conc_epic", stage="Stage 3")

    def _worker(tid: int) -> None:
        target = repo if tid % 2 == 0 else wt
        for idx in range(5):
            stored = _state_envelope.update_epic_checkpoint(
                target,
                "conc_epic",
                {
                    "event": "subagent_returned",
                    "persona": "orchestrator",
                    "head_sha": "abc1234",
                    "wave": 1,
                    "tasks_done": ["task_01"],
                    "tasks_in_flight": ["task_02"],
                    "next_step": f"thread-{tid}-step-{idx}",
                    "turns_since_checkpoint": 0,
                    "low_quota": False,
                },
            )
            assert stored["next_step"] == f"thread-{tid}-step-{idx}"

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(_worker, tid) for tid in range(6)]
        for fut in futures:
            fut.result()

    safe_slug = _state_envelope._sanitize_epic_slug("conc_epic")
    repo_hb = json.loads(
        (repo / ".devtool" / "state" / f"{safe_slug}.heartbeat.json").read_text(
            encoding="utf-8"
        )
    )
    wt_hb = json.loads(
        (wt / ".devtool" / "state" / f"{safe_slug}.heartbeat.json").read_text(
            encoding="utf-8"
        )
    )
    assert repo_hb["checkpoint"] == wt_hb["checkpoint"]

    expected_steps = {
        f"thread-{tid}-step-{idx}" for tid in range(6) for idx in range(5)
    }
    for base in (repo, wt):
        events_file = base / ".devtool" / "logs" / f"events_{safe_slug}.jsonl"
        parsed = [
            json.loads(line)
            for line in events_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        cp_events = [entry for entry in parsed if entry.get("category") == "checkpoint"]
        assert len(cp_events) == 30
        assert {entry.get("next_step") for entry in cp_events} == expected_steps


@pytest.mark.parametrize(
    "event_name",
    [
        "gate2_tasks_locked",
        "subagent_returned",
        "wave_merged",
        "model_unavailable",
        "turn_budget",
        "low_quota_stop",
        "quota_low",
    ],
)
def test_all_checkpoint_events_accepted_and_invalid_rejected(
    tmp_path: Path, event_name: str
) -> None:
    """Every CHECKPOINT_EVENTS choice succeeds and unknown event fails argparse."""
    repo = tmp_path / "repo"
    home_dir = tmp_path / "home"
    _init_git_repo(repo)

    proc = _run_resume_cli(
        repo,
        [
            "--checkpoint",
            event_name,
            "--epic",
            "ev_epic",
            "--next",
            f"handle {event_name}",
        ],
        home_dir=home_dir,
    )
    assert proc.returncode == 0, proc.stderr
    safe_slug = _state_envelope._sanitize_epic_slug("ev_epic")
    hb = json.loads(
        (repo / ".devtool" / "state" / f"{safe_slug}.heartbeat.json").read_text(
            encoding="utf-8"
        )
    )
    assert hb["checkpoint"]["event"] == event_name

    bad = _run_resume_cli(
        repo,
        ["--checkpoint", "unknown_event", "--epic", "ev_epic"],
        home_dir=home_dir,
    )
    assert bad.returncode != 0
    assert "invalid choice" in bad.stderr.lower()


def test_checkpoint_records_low_quota_and_optional_warning(tmp_path: Path) -> None:
    """Checkpoint reflects active low_quota and surfaces legacy review_config warning."""
    repo = tmp_path / "repo"
    home_dir = tmp_path / "home"
    _init_git_repo(repo)

    d3_dir = home_dir / ".d3nexus"
    d3_dir.mkdir(parents=True, exist_ok=True)
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(
        timespec="seconds"
    )
    (d3_dir / "personas.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "low_quota": {"testuser": {"enabled": True, "expires_at": future}},
            }
        ),
        encoding="utf-8",
    )
    devtool = repo / ".devtool"
    devtool.mkdir(parents=True, exist_ok=True)
    (devtool / "review_config.json").write_text(
        json.dumps({"providers": {"programmer": {"model": "gemini-4-hydrogen-xhigh"}}}),
        encoding="utf-8",
    )

    proc = _run_resume_cli(
        repo,
        [
            "--checkpoint",
            "low_quota_stop",
            "--epic",
            "lq_epic",
            "--next",
            "wait for quota",
        ],
        home_dir=home_dir,
    )
    assert proc.returncode == 0, proc.stderr
    safe_slug = _state_envelope._sanitize_epic_slug("lq_epic")
    hb = json.loads(
        (repo / ".devtool" / "state" / f"{safe_slug}.heartbeat.json").read_text(
            encoding="utf-8"
        )
    )
    assert hb["checkpoint"]["low_quota"] is True
    assert "review_config.json" in hb["checkpoint"]["warning"]


def test_brief_roles_contracts_and_missing_brief_role_argparse_error(
    tmp_path: Path,
) -> None:
    """All five brief roles render valid persona contracts and missing --brief-role uses parser.error."""
    repo = tmp_path / "repo"
    home_dir = tmp_path / "home"
    _init_git_repo(repo)

    fixer = _run_resume_cli(
        repo,
        ["--emit-prompt", "brief", "--brief-role", "review-fixer", "--epic", "demo"],
        home_dir=home_dir,
    )
    assert fixer.returncode == 0, fixer.stderr
    assert "Role 2.3 Programmer" in fixer.stdout
    assert "fast-track|apply-plan" in fixer.stdout
    assert "plan-first" not in fixer.stdout

    verifier = _run_resume_cli(
        repo,
        ["--emit-prompt", "brief", "--brief-role", "gate4-verifier", "--epic", "demo"],
        home_dir=home_dir,
    )
    assert verifier.returncode == 0, verifier.stderr
    assert "Role 2.3 Programmer" in verifier.stdout
    assert "candidate_sha" in verifier.stdout

    impl = _run_resume_cli(
        repo,
        [
            "--emit-prompt",
            "brief",
            "--brief-role",
            "task-implementer",
            "--epic",
            "demo",
        ],
        home_dir=home_dir,
    )
    assert impl.returncode == 0, impl.stderr
    assert "Role 2.3 Programmer" in impl.stdout
    assert "non_test_modules_changed" in impl.stdout

    missing = _run_resume_cli(
        repo,
        ["--emit-prompt", "brief", "--epic", "demo"],
        home_dir=home_dir,
    )
    assert missing.returncode == 2
    assert "--brief-role" in missing.stderr
    assert "Traceback" not in missing.stderr
    assert "NameError" not in missing.stderr


def test_english_only_resolution_prefers_md_then_en_and_never_reads_vi(
    tmp_path: Path,
) -> None:
    """sync_window_title, build_compact_context, and emit_handoff_prompt resolve .md before .en.md and skip .vi.md."""
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    epic_dir = repo / ".devtool" / "epic" / "eng_epic"
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / "eng_epic.vi.md").write_text(
        "# Epic: Vietnamese Ignored\n", encoding="utf-8"
    )
    (epic_dir / "eng_epic.en.md").write_text(
        "# Epic: Legacy English Title\n- **Epic**: eng_epic\n- **Status**: Legacy Status\n",
        encoding="utf-8",
    )
    (epic_dir / "eng_epic.md").write_text(
        "# Epic: Canonical English Title\n- **Epic**: eng_epic\n- **Status**: Canonical Status\n",
        encoding="utf-8",
    )

    resume_context.sync_window_title(
        repo, epic_slug="eng_epic", stage_override="Stage 3"
    )
    settings = json.loads(
        (repo / ".vscode" / "settings.json").read_text(encoding="utf-8")
    )
    assert "Canonical English Title" in settings["window.title"]
    assert "Vietnamese Ignored" not in settings["window.title"]

    compact = resume_context.build_compact_context(repo, epic_slug="eng_epic")
    assert "Canonical Status" in compact
    assert "eng_epic.md" in compact
    assert ".vi.md" not in compact

    (epic_dir / "eng_epic.md").unlink()
    resume_context.sync_window_title(
        repo, epic_slug="eng_epic", stage_override="Stage 3"
    )
    settings_en = json.loads(
        (repo / ".vscode" / "settings.json").read_text(encoding="utf-8")
    )
    assert "Legacy English Title" in settings_en["window.title"]
    assert "Vietnamese Ignored" not in settings_en["window.title"]


def test_checkpoint_preserves_prior_state_and_collects_tasks(tmp_path: Path) -> None:
    """--checkpoint preserves existing decisions/status and populates tasks_done and tasks_in_flight."""
    repo = tmp_path / "repo"
    home_dir = tmp_path / "home"
    _init_git_repo(repo)

    features = repo / ".devtool" / "features"
    done_dir = features / "done"
    features.mkdir(parents=True, exist_ok=True)
    done_dir.mkdir(parents=True, exist_ok=True)
    (done_dir / "task_01_alpha.md").write_text(
        '---\nid: "task_01_alpha"\nstatus: "done"\nepic: "cp_epic"\n---\n# Task 1\n',
        encoding="utf-8",
    )
    (features / "task_02_beta.md").write_text(
        '---\nid: "task_02_beta"\nstatus: "in-progress"\nepic: "cp_epic"\n---\n# Task 2\n',
        encoding="utf-8",
    )
    (features / "task_03_decoy.vi.md").write_text(
        '---\nid: "task_03_decoy"\nstatus: "done"\nepic: "cp_epic"\n---\n# Decoy\n',
        encoding="utf-8",
    )

    state_res = _run_resume_cli(
        repo,
        [
            "--state",
            "--epic",
            "cp_epic",
            "--role",
            "orchestrator",
            "--decisions",
            "Locked Gate 2 scope",
            "--status",
            "Stage 3 Wave 1",
            "--next",
            "Old step",
        ],
        home_dir=home_dir,
    )
    assert state_res.returncode == 0, state_res.stderr

    cp_res = _run_resume_cli(
        repo,
        [
            "--checkpoint",
            "wave_merged",
            "--epic",
            "cp_epic",
            "--wave",
            "1",
            "--next",
            "Start wave 2",
        ],
        home_dir=home_dir,
    )
    assert cp_res.returncode == 0, cp_res.stderr

    safe_slug = _state_envelope._sanitize_epic_slug("cp_epic")
    hb = json.loads(
        (repo / ".devtool" / "state" / f"{safe_slug}.heartbeat.json").read_text(
            encoding="utf-8"
        )
    )
    cp = hb["checkpoint"]
    assert cp["tasks_done"] == ["task_01_alpha"]
    assert cp["tasks_in_flight"] == ["task_02_beta"]
    assert cp["wave"] == 1
    assert cp["next_step"] == "Start wave 2"

    state_text = (repo / ".devtool" / "state" / "cp_epic.md").read_text(
        encoding="utf-8"
    )
    assert "Locked Gate 2 scope" in state_text
    assert "Stage 3 Wave 1" in state_text
    assert "Start wave 2" in state_text
    assert "Role: orchestrator" in state_text


def test_filter_english_doc_paths_drops_vi_mirrors() -> None:
    """_filter_english_doc_paths drops every path ending in .vi.md."""
    filtered = resume_context._filter_english_doc_paths(
        ["a.md", "b.en.md", "c.vi.md", "dir/d.vi.md", "dir/e-design.md"]
    )
    assert filtered == ["a.md", "b.en.md", "dir/e-design.md"]


def test_checkpoint_with_workspace_root_and_repo_targets_repo_devtool(
    tmp_path: Path,
) -> None:
    """--checkpoint with both --workspace-root and --repo writes heartbeat, events, tasks, and state to the target repo."""
    ws = tmp_path / "ws"
    target_repo = ws / "D3Nexus"
    other_repo = ws / "ai-agent-tools"
    home_dir = tmp_path / "home"
    _init_git_repo(target_repo)
    _init_git_repo(other_repo)

    features = target_repo / ".devtool" / "features"
    done_dir = features / "done"
    features.mkdir(parents=True, exist_ok=True)
    done_dir.mkdir(parents=True, exist_ok=True)
    (done_dir / "task_01_init.md").write_text(
        '---\nid: "task_01_init"\nstatus: "done"\nepic: "dual_flag_epic"\n---\n# Task 1\n',
        encoding="utf-8",
    )
    (features / "task_02_work.md").write_text(
        '---\nid: "task_02_work"\nstatus: "in-progress"\nepic: "dual_flag_epic"\n---\n# Task 2\n',
        encoding="utf-8",
    )
    _state_envelope.update_epic_heartbeat(
        target_repo,
        "dual_flag_epic",
        stage="Stage 3",
        active_wave=2,
        last_event="seed",
    )
    state_res = _run_resume_cli(
        other_repo,
        [
            "--workspace-root",
            str(ws),
            "--repo",
            "D3Nexus",
            "--state",
            "--epic",
            "dual_flag_epic",
            "--role",
            "orchestrator",
            "--decisions",
            "Keep wave 2",
            "--status",
            "Stage 3 Wave 2",
            "--next",
            "Old next",
        ],
        home_dir=home_dir,
        workspace_root=ws,
    )
    assert state_res.returncode == 0, state_res.stderr

    cp_res = _run_resume_cli(
        other_repo,
        [
            "--workspace-root",
            str(ws),
            "--repo",
            "D3Nexus",
            "--checkpoint",
            "subagent_returned",
            "--epic",
            "dual_flag_epic",
            "--next",
            "review task_02",
        ],
        home_dir=home_dir,
        workspace_root=ws,
    )
    assert cp_res.returncode == 0, cp_res.stderr

    safe_slug = _state_envelope._sanitize_epic_slug("dual_flag_epic")
    repo_hb_path = target_repo / ".devtool" / "state" / f"{safe_slug}.heartbeat.json"
    repo_events_path = target_repo / ".devtool" / "logs" / f"events_{safe_slug}.jsonl"
    repo_state_path = target_repo / ".devtool" / "state" / "dual_flag_epic.md"

    assert repo_hb_path.is_file()
    hb = json.loads(repo_hb_path.read_text(encoding="utf-8"))
    cp = hb["checkpoint"]
    assert cp["event"] == "subagent_returned"
    assert cp["wave"] == 2
    assert cp["tasks_done"] == ["task_01_init"]
    assert cp["tasks_in_flight"] == ["task_02_work"]
    assert cp["next_step"] == "review task_02"

    assert repo_events_path.is_file()
    cp_events = [
        json.loads(line)
        for line in repo_events_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line).get("category") == "checkpoint"
    ]
    assert len(cp_events) == 1
    assert cp_events[0]["next_step"] == "review task_02"

    assert repo_state_path.is_file()
    state_text = repo_state_path.read_text(encoding="utf-8")
    assert "Keep wave 2" in state_text
    assert "review task_02" in state_text.split("## Next Immediate Step:", 1)[1]

    assert not (ws / ".devtool" / "state" / f"{safe_slug}.heartbeat.json").exists()
    assert not (ws / ".devtool" / "logs" / f"events_{safe_slug}.jsonl").exists()
    assert not (ws / ".devtool" / "state" / "dual_flag_epic.md").exists()


def test_checkpoint_cross_repo_and_worktree_head_sha(tmp_path: Path) -> None:
    """--checkpoint records target repo HEAD across repos and worktree HEAD within the same repo."""
    ws = tmp_path / "ws"
    target_repo = ws / "D3Nexus"
    caller_repo = ws / "ai-agent-tools"
    home_dir = tmp_path / "home"
    _init_git_repo(target_repo)
    _init_git_repo(caller_repo)

    (target_repo / "target.txt").write_text("target commit\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "target.txt"], cwd=target_repo, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Target commit"],
        cwd=target_repo,
        capture_output=True,
        check=True,
    )

    target_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=target_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    caller_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=caller_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert target_sha != caller_sha

    cross_res = _run_resume_cli(
        caller_repo,
        [
            "--workspace-root",
            str(ws),
            "--repo",
            "D3Nexus",
            "--checkpoint",
            "subagent_returned",
            "--epic",
            "cross_sha_epic",
            "--next",
            "verify target sha",
        ],
        home_dir=home_dir,
        workspace_root=ws,
    )
    assert cross_res.returncode == 0, cross_res.stderr
    cross_slug = _state_envelope._sanitize_epic_slug("cross_sha_epic")
    cross_hb = json.loads(
        (target_repo / ".devtool" / "state" / f"{cross_slug}.heartbeat.json").read_text(
            encoding="utf-8"
        )
    )
    assert cross_hb["checkpoint"]["head_sha"] == target_sha
    assert cross_hb["checkpoint"]["head_sha"] != caller_sha

    wt = target_repo / ".worktrees" / "wt_sha_epic"
    subprocess.run(
        [
            "git",
            "-C",
            str(target_repo),
            "worktree",
            "add",
            str(wt),
            "-b",
            "epic/wt_sha_epic",
            "main",
        ],
        capture_output=True,
        check=True,
    )
    (wt / "wt.txt").write_text("worktree commit\n", encoding="utf-8")
    subprocess.run(["git", "add", "wt.txt"], cwd=wt, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Worktree commit"],
        cwd=wt,
        capture_output=True,
        check=True,
    )
    wt_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=wt,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert wt_sha != target_sha

    wt_res = _run_resume_cli(
        wt,
        [
            "--checkpoint",
            "wave_merged",
            "--epic",
            "wt_sha_epic",
            "--next",
            "verify worktree sha",
        ],
        home_dir=home_dir,
        workspace_root=ws,
    )
    assert wt_res.returncode == 0, wt_res.stderr
    wt_slug = _state_envelope._sanitize_epic_slug("wt_sha_epic")
    wt_hb = json.loads(
        (target_repo / ".devtool" / "state" / f"{wt_slug}.heartbeat.json").read_text(
            encoding="utf-8"
        )
    )
    assert wt_hb["checkpoint"]["head_sha"] == wt_sha
    assert wt_hb["checkpoint"]["head_sha"] != target_sha


@pytest.mark.parametrize(
    ("extra_fields", "expect_present"),
    [
        ({}, False),
        ({"brief_role": "", "model": "   ", "effort": None}, False),
        (
            {
                "brief_role": "task-implementer",
                "model": "gemini-4-hydrogen-xhigh",
                "effort": "xhigh",
            },
            True,
        ),
    ],
    ids=["omitted", "blank_or_none", "non_empty"],
)
def test_update_epic_checkpoint_keeps_optional_telemetry_fields(
    tmp_path: Path,
    extra_fields: dict[str, object],
    expect_present: bool,
) -> None:
    """Spec §9: brief_role, model, and effort are stored on block and event only when non-empty."""
    repo = tmp_path / "repo"
    (repo / ".devtool").mkdir(parents=True, exist_ok=True)
    epic_slug = "telemetry_epic"
    safe_slug = _state_envelope._sanitize_epic_slug(epic_slug)
    payload: dict[str, object] = {
        "event": "subagent_returned",
        "persona": "programmer",
        "next_step": "task-implementer:t1 profile=p2",
        **extra_fields,
    }
    cp = _state_envelope.update_epic_checkpoint(repo, epic_slug, payload)
    frozen_ten = [
        "event",
        "at",
        "persona",
        "head_sha",
        "wave",
        "tasks_done",
        "tasks_in_flight",
        "next_step",
        "turns_since_checkpoint",
        "low_quota",
    ]
    assert list(cp.keys())[:10] == frozen_ten

    events_path = repo / ".devtool" / "logs" / f"events_{safe_slug}.jsonl"
    rec = json.loads(events_path.read_text(encoding="utf-8").splitlines()[-1])

    if expect_present:
        assert cp["brief_role"] == "task-implementer"
        assert cp["model"] == "gemini-4-hydrogen-xhigh"
        assert cp["effort"] == "xhigh"
        assert rec["brief_role"] == "task-implementer"
        assert rec["model"] == "gemini-4-hydrogen-xhigh"
        assert rec["effort"] == "xhigh"
        assert rec["checkpoint"]["brief_role"] == "task-implementer"
        assert rec["checkpoint"]["model"] == "gemini-4-hydrogen-xhigh"
        assert rec["checkpoint"]["effort"] == "xhigh"
    else:
        assert list(cp.keys()) == frozen_ten
        for key in ("brief_role", "model", "effort"):
            assert key not in cp
            assert key not in rec
            assert key not in rec["checkpoint"]
