"""Unit tests for Task 01: State Envelope Rolling Events and Stage Sub-Step Producers.

Covers: LTSP-HP-01, LTSP-HP-02, LTSP-EC-01, LTSP-ST-01, LTSP-FR-01
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
if (
    str(REPO_ROOT / "skills" / "quality_check" / "resources" / "scripts")
    not in sys.path
):
    sys.path.insert(
        0, str(REPO_ROOT / "skills" / "quality_check" / "resources" / "scripts")
    )
if (
    str(REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts")
    not in sys.path
):
    sys.path.insert(
        0, str(REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts")
    )


def _init_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / ".devtool" / "state").mkdir(parents=True, exist_ok=True)
    (repo / "README.md").write_text("# test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    return repo


def test_ltsp_hp_01_events_ring_buffer_and_review_state(tmp_path: Path) -> None:
    """[LTSP-HP-01] Heartbeat envelope maintains a bounded 20-entry rolling event log and structured review_state."""
    import _state_envelope

    repo = _init_git_repo(tmp_path)
    review_state = {
        "kind": "code",
        "round": 1,
        "max_rounds": 3,
        "cli": "codex",
        "model": "gpt-6.1-sol",
        "phase": "reviewing",
    }
    state: dict[str, Any] = {}
    for i in range(1, 26):
        state = _state_envelope.update_epic_heartbeat(
            repo,
            "demo_epic",
            stage="Stage 3 (Review)",
            sub_step="reviewing",
            sub_step_detail="Round 1/3: codex reviewing",
            review_state=review_state,
            last_event=f"event-{i:02d}",
            max_events=20,
        )

    hb_path = repo / ".devtool" / "state" / "demo_epic.heartbeat.json"
    assert hb_path.is_file()
    persisted = json.loads(hb_path.read_text(encoding="utf-8"))
    events = persisted.get("events")
    assert isinstance(events, list)
    assert len(events) == 20
    assert events[0]["message"] == "event-06"
    assert events[-1]["message"] == "event-25"
    assert persisted.get("sub_step") == "reviewing"
    assert persisted.get("sub_step_detail") == "Round 1/3: codex reviewing"
    assert persisted.get("review_state", {}).get("phase") == "reviewing"
    assert persisted.get("review_state", {}).get("cli") == "codex"
    assert state["events"][-1]["message"] == "event-25"


@pytest.mark.parametrize(
    ("capability", "expected_label"),
    [
        ("lint", "Static Lint"),
        ("typecheck", "Typecheck"),
        ("type_check", "Typecheck"),
        ("pycore", "PyCore / Unit Test"),
        ("unit_test", "PyCore / Unit Test"),
        ("pytest", "Unit & Integration Test"),
        ("pytest_unit", "PyCore / Unit Test"),
        ("integration", "Integration Test"),
        ("e2e", "UI / E2E Test"),
        ("playwright", "UI / E2E Test"),
        ("architecture", "Architecture Gate"),
        ("import_linter", "Architecture Gate"),
        ("build", "Build"),
    ],
)
def test_ltsp_hp_02_format_capability_labels(
    capability: str, expected_label: str
) -> None:
    """[LTSP-HP-02] format_capability_label maps capability names to canonical human labels."""
    import verify_polyglot_registry as vpr

    assert hasattr(vpr, "format_capability_label")
    assert vpr.format_capability_label("python-qa", capability) == expected_label


def test_ltsp_hp_02_coordinator_steps_and_distinct_events(tmp_path: Path) -> None:
    """[LTSP-HP-02] Polyglot quality runner records per-step status and distinct start/completion events."""
    import verify_polyglot_registry as vpr

    repo = _init_git_repo(tmp_path)
    planned_steps = [
        ("python-qa", "lint"),
        ("python-qa", "typecheck"),
        ("python-qa", "pycore"),
        ("python-qa", "integration"),
        ("python-qa", "e2e"),
    ]
    coord = vpr._QualityRunCoordinator(
        run_id="run-ltsp-02",
        repo_root=repo,
        profile="full",
        epic_slug="demo_epic",
        heartbeat_interval=15.0,
        step_total=5,
        ttl_sec=300,
        planned_steps=planned_steps,
    )
    step1 = coord.start_step("python-qa", "lint")
    assert step1 == 1
    coord.complete_step("python-qa", "lint", status="passed", elapsed_sec=1.2)
    step3 = coord.start_step("python-qa", "pycore")
    assert step3 == 2 or step3 == 3

    qa_path = repo / ".devtool" / "state" / "quality_active.json"
    assert qa_path.is_file()
    qa_data = json.loads(qa_path.read_text(encoding="utf-8"))
    run_entry = qa_data["runs"]["run-ltsp-02"]
    steps = run_entry.get("steps")
    assert isinstance(steps, list)
    assert len(steps) == 5
    by_cap = {s["capability"]: s for s in steps}
    assert by_cap["lint"]["status"] == "passed"
    assert by_cap["lint"]["label"] == "Static Lint"
    assert by_cap["pycore"]["status"] == "running"
    assert by_cap["pycore"]["label"] == "PyCore / Unit Test"
    assert run_entry.get("capability_label") == "PyCore / Unit Test"
    assert isinstance(run_entry.get("head_sha"), str)

    hb_path = repo / ".devtool" / "state" / "demo_epic.heartbeat.json"
    assert hb_path.is_file()
    hb_data = json.loads(hb_path.read_text(encoding="utf-8"))
    messages = [e["message"] for e in hb_data.get("events", [])]
    assert any("Static Lint" in m and "running" in m for m in messages)
    assert any("Static Lint" in m and "passed" in m for m in messages)


def test_ltsp_ec_01_consecutive_identical_events_deduplicated(tmp_path: Path) -> None:
    """[LTSP-EC-01] Consecutive identical heartbeat events are deduplicated in the events ring buffer."""
    import _state_envelope

    repo = _init_git_repo(tmp_path)
    timestamps = [f"2026-11-14T09:00:0{i}+00:00" for i in range(1, 6)]
    for ts in timestamps:
        _state_envelope.update_epic_heartbeat(
            repo,
            "dedup_epic",
            stage="Stage 3",
            last_event="wave 1 polling",
            updated_at=ts,
        )

    hb_path = repo / ".devtool" / "state" / "dedup_epic.heartbeat.json"
    persisted = json.loads(hb_path.read_text(encoding="utf-8"))
    events = persisted.get("events")
    assert isinstance(events, list)
    assert len(events) == 1
    assert events[0]["message"] == "wave 1 polling"
    assert events[0]["ts"] == timestamps[-1]


def test_ltsp_st_01_external_review_runner_transitions_review_state(
    tmp_path: Path,
) -> None:
    """[LTSP-ST-01] External review runner transitions review_state through reviewing, triage, fixing, and verifying phases."""
    import run_external_review as rer

    repo = _init_git_repo(tmp_path)
    epic_dir = repo / ".devtool" / "epic" / "rev_epic"
    epic_dir.mkdir(parents=True, exist_ok=True)
    review_md = epic_dir / "review_results.md"
    review_md.write_text(
        "# Cross-Model Review: rev_epic\n\n"
        "## Round 1\n\n"
        "- **Date**: 2026-11-14T09:00:00Z\n"
        "- **SHA**: a1b2c3d\n"
        "- **Base**: main\n"
        "- **CLI**: codex\n"
        "- **Model**: gpt-6.1-sol\n"
        "- **Thinking**: high\n"
        "- **Status**: completed\n"
        "- **Verdict**: CHANGES REQUIRED\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "|---|----------|----------|---------|----------|\n"
        "| 1 | Important | src/app.py:10 | Missing validation |  |\n\n"
        "Raw output:\n\n```text\nVerdict: CHANGES REQUIRED\n```\n",
        encoding="utf-8",
    )

    old_cwd = Path.cwd()
    try:
        os.chdir(repo)
        rc_triage = rer.main(["triage", "--epic-dir", "rev_epic"])
        assert rc_triage == 0
        hb_path = repo / ".devtool" / "state" / "rev_epic.heartbeat.json"
        hb1 = json.loads(hb_path.read_text(encoding="utf-8"))
        assert hb1.get("review_state", {}).get("phase") == "triage"
        assert hb1.get("review_state", {}).get("action") == "AUTO_FIX_ELIGIBLE"

        rc_fix = rer.main(["status", "--epic-dir", "rev_epic", "--phase", "fixing"])
        assert rc_fix == 0
        hb2 = json.loads(hb_path.read_text(encoding="utf-8"))
        assert hb2.get("review_state", {}).get("phase") == "fixing"

        rc_ver = rer.main(["status", "--epic-dir", "rev_epic", "--phase", "verifying"])
        assert rc_ver == 0
        hb3 = json.loads(hb_path.read_text(encoding="utf-8"))
        assert hb3.get("review_state", {}).get("phase") == "verifying"
        assert hb3.get("review_state", {}).get("sha") == "a1b2c3d"
        assert hb3.get("review_state", {}).get("head_sha")
        events = hb3.get("events", [])
        assert len(events) >= 3
        phases_logged = [e.get("sub_step") for e in events[-3:]]
        assert phases_logged == ["triage", "fixing", "verifying"]

        # Transitioning to a new round or new review kind must clear stale verdicts/actions/counts
        rer._emit_review_heartbeat(
            repo,
            "rev_epic",
            kind="code",
            phase="reviewing",
            round_num=2,
            cli="codex",
            model="gpt-6.1-sol",
        )
        hb4 = json.loads(hb_path.read_text(encoding="utf-8"))
        rev4 = hb4.get("review_state", {})
        assert rev4.get("round") == 2
        assert rev4.get("phase") == "reviewing"
        assert "verdict" not in rev4
        assert "action" not in rev4
        assert "important" not in rev4
    finally:
        os.chdir(old_cwd)


def test_ltsp_fr_01_readonly_state_dir_never_aborts_cli(tmp_path: Path) -> None:
    """[LTSP-FR-01] Telemetry write errors inside run_external_review.py or audit_epic.py never abort the underlying CLI command."""
    import run_external_review as rer

    repo = _init_git_repo(tmp_path)
    epic_dir = repo / ".devtool" / "epic" / "ro_epic"
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / "review_results.md").write_text(
        "# Cross-Model Review: ro_epic\n\n"
        "## Round 1\n\n"
        "- **Date**: 2026-11-14T09:00:00Z\n"
        "- **SHA**: a1b2c3d\n"
        "- **Base**: main\n"
        "- **CLI**: codex\n"
        "- **Model**: gpt-6.1-sol\n"
        "- **Thinking**: high\n"
        "- **Status**: completed\n"
        "- **Verdict**: PASS\n\n"
        "No findings.\n\n"
        "Raw output:\n\n```text\nVerdict: PASS\n```\n",
        encoding="utf-8",
    )
    state_dir = repo / ".devtool" / "state"
    state_dir.chmod(0o555)
    old_cwd = Path.cwd()
    try:
        os.chdir(repo)
        rc = rer.main(["triage", "--epic-dir", "ro_epic"])
        assert rc == 0
    finally:
        state_dir.chmod(0o755)
        os.chdir(old_cwd)
