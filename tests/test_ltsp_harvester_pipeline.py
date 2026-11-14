"""Unit tests for check_tasks.py early Stage 1 activation, 100% task progress decoupling,
weighted 6-stage lifecycle progress, and pipeline_telemetry harvesting.

Covers BDD Scenarios:
- LTSP-HP-03: Check-Tasks harvester activates epic immediately after Gate 1 approval and extracts Stage 1-2 telemetry
- LTSP-HP-04: Harvester decouples 100% Task Implementation completion from weighted 6-stage lifecycle progress
- LTSP-EC-02: Dormant backlog and abandoned epic directories do not trigger active_epic even if abandoned epic retains Gate 1 or heartbeat
- LTSP-ST-02: Lifecycle progress percentage advances monotonically across all 6 stages and requires full Gate 4 on latest SHA before 98% Finish
- LTSP-AR-01: Multi-process concurrent heartbeat event updates preserve all distinct events under flock
"""

from __future__ import annotations

import json
import multiprocessing
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
CHECK_TASKS_DIR = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"
for _p in (SCRIPTS_DIR, CHECK_TASKS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import _state_envelope  # noqa: E402
import check_tasks  # type: ignore[import-not-found]  # noqa: E402
import resume_context  # noqa: E402


def _init_git_repo(root: Path) -> str:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "dev@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Dev"], cwd=root, check=True, capture_output=True
    )
    (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "[DEMO] Initial commit"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write_task(
    epic_dir: Path, features_dir: Path, task_id: str, epic_slug: str, status: str
) -> None:
    content = (
        f'---\nid: "{task_id}"\nstatus: "{status}"\npriority: "high"\n'
        f'epic: "{epic_slug}"\norder: "a1"\n---\n\n# {task_id}\n'
    )
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / f"{task_id}.md").write_text(content, encoding="utf-8")
    if status == "done":
        done_dir = features_dir / "done"
        done_dir.mkdir(parents=True, exist_ok=True)
        (done_dir / f"{task_id}.md").write_text(content, encoding="utf-8")
        (features_dir / f"{task_id}.md").unlink(missing_ok=True)
    else:
        features_dir.mkdir(parents=True, exist_ok=True)
        (features_dir / f"{task_id}.md").write_text(content, encoding="utf-8")


# [LTSP-HP-03] Check-Tasks harvester activates epic immediately after Gate 1 approval and extracts Stage 1-2 telemetry
def test_ltsp_hp_03_early_epic_activation_from_gate1(tmp_path: Path) -> None:
    """LTSP-HP-03: Check-Tasks activates epic immediately after Gate 1 approval and extracts Stage 1-2 telemetry."""
    repo = tmp_path / "repo_hp03"
    _init_git_repo(repo)
    epic_dir = repo / ".devtool" / "epic" / "early_epic"
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / "2026-11-14-early-epic-design.en.md").write_text(
        "# Early Epic Design Spec\n\n- **PIC**: phungthuy8901\n- **Status**: Approved\n",
        encoding="utf-8",
    )
    resume_context.record_gate_approval(
        repo,
        "early_epic",
        1,
        "Approved spec",
        by="phungthuy8901",
    )

    meta = check_tasks.scan_repo(repo)
    assert meta.active_epic == "early_epic"
    assert meta.account_id == "phungthuy8901"
    assert meta.epics_summary is not None
    ep_entry = next(e for e in meta.epics_summary.epics if e["slug"] == "early_epic")
    assert ep_entry["status"] == "in_progress"
    assert meta.pipeline_telemetry is not None
    assert 10.0 <= float(meta.pipeline_telemetry["lifecycle_progress_pct"]) <= 25.0
    stages = meta.pipeline_telemetry["stages"]
    assert len(stages) == 6
    assert stages[0]["status"] == "done"
    assert stages[1]["status"] == "running"


# [LTSP-HP-04] Harvester decouples 100% Task Implementation completion from weighted 6-stage lifecycle progress
def test_ltsp_hp_04_decoupled_100_task_progress_vs_weighted_lifecycle(
    tmp_path: Path,
) -> None:
    """LTSP-HP-04: Harvester decouples 100% Task Implementation completion from weighted 6-stage lifecycle progress."""
    repo = tmp_path / "repo_hp04"
    _init_git_repo(repo)
    slug = "full_tasks_epic"
    epic_dir = repo / ".devtool" / "epic" / slug
    features_dir = repo / ".devtool" / "features"
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / "2026-11-14-full-tasks-design.en.md").write_text(
        "# Spec\n- **PIC**: duedd\n", encoding="utf-8"
    )
    (epic_dir / f"{slug}.en.md").write_text(
        "# Epic: Full Tasks Epic\n\n- **Status**: In-progress\n", encoding="utf-8"
    )
    (epic_dir / "bdd_scenarios.en.md").write_text("# BDD\n", encoding="utf-8")
    (epic_dir / "handoff.md").write_text(
        "# Handoff\n- **PIC**: duedd\n", encoding="utf-8"
    )

    for idx in range(1, 10):
        _write_task(epic_dir, features_dir, f"task_0{idx}_demo", slug, "done")

    for gate_num in (1, 2, 3):
        resume_context.record_gate_approval(
            repo, slug, gate_num, f"Gate {gate_num} approved"
        )

    meta = check_tasks.scan_repo(repo)
    assert meta.task_progress.done_tasks == 9
    assert meta.task_progress.total_tasks == 9
    assert meta.task_progress.task_completion_pct == 100.0
    assert meta.pipeline_telemetry is not None
    assert meta.pipeline_telemetry["task_completion_pct"] == 100.0
    stages = meta.pipeline_telemetry["stages"]
    assert stages[2]["status"] == "done"
    assert "9/9 (100%)" in stages[2]["summary"]
    assert 80.0 <= float(meta.pipeline_telemetry["lifecycle_progress_pct"]) <= 96.0


# [LTSP-EC-02] Dormant backlog and abandoned epic directories do not trigger active_epic
def test_ltsp_ec_02_dormant_and_abandoned_epics_not_activated(tmp_path: Path) -> None:
    """LTSP-EC-02: Dormant backlog and abandoned epic directories do not trigger active_epic even if abandoned epic retains Gate 1 or heartbeat."""
    repo = tmp_path / "repo_ec02"
    _init_git_repo(repo)
    dormant = repo / ".devtool" / "epic" / "dormant_backlog"
    dormant.mkdir(parents=True, exist_ok=True)
    (dormant / "dormant_backlog.en.md").write_text(
        "# Epic: Dormant Backlog\n\n- **Status**: Backlog\n",
        encoding="utf-8",
    )

    abandoned = repo / ".devtool" / "epic" / "abandoned_old"
    abandoned.mkdir(parents=True, exist_ok=True)
    (abandoned / "abandoned_old.en.md").write_text(
        "# Epic: Abandoned Old\n\n- **Status**: Abandoned\n",
        encoding="utf-8",
    )
    resume_context.record_gate_approval(repo, "abandoned_old", 1, "Old gate 1")
    _state_envelope.update_epic_heartbeat(
        repo,
        "abandoned_old",
        stage="Stage 1",
        last_event="old heartbeat",
    )

    assert check_tasks.resolve_active_epic(repo) is None
    # Even if an abandoned epic has an active worktree branch, resolve_active_epic must ignore it
    wt_abandoned = repo / ".worktrees" / "abandoned_old"
    wt_abandoned.mkdir(parents=True, exist_ok=True)
    assert check_tasks.resolve_active_epic(repo) is None
    summary = check_tasks.harvest_epics_overview(repo)
    by_slug = {e["slug"]: e for e in summary.epics}
    assert by_slug["dormant_backlog"]["status"] == "unstarted"
    assert by_slug["abandoned_old"]["status"] in ("abandon", "abandoned")


# [LTSP-ST-02] Lifecycle progress percentage advances monotonically across all 6 stages
def test_ltsp_st_02_monotonic_6_stage_progress_and_gate4_sha_requirement(
    tmp_path: Path,
) -> None:
    """LTSP-ST-02: Lifecycle progress percentage advances monotonically across all 6 stages and requires full Gate 4 on latest SHA before 98% Finish."""
    repo = tmp_path / "repo_st02"
    sha1 = _init_git_repo(repo)
    slug = "mono_epic"
    epic_dir = repo / ".devtool" / "epic" / slug
    features_dir = repo / ".devtool" / "features"
    epic_dir.mkdir(parents=True, exist_ok=True)

    # State 1: Stage 1 Spec approved (Gate 1)
    (epic_dir / "2026-11-14-mono-design.en.md").write_text(
        "# Spec\n- **PIC**: duedd\n", encoding="utf-8"
    )
    resume_context.record_gate_approval(repo, slug, 1, "Gate 1")
    meta1 = check_tasks.scan_repo(repo)
    assert meta1.pipeline_telemetry is not None
    p1 = float(meta1.pipeline_telemetry["lifecycle_progress_pct"])
    t1 = float(meta1.pipeline_telemetry["task_completion_pct"])
    assert t1 == 0.0
    assert p1 == 10.0

    # State 2: Stage 2 HLD + tasks + Principal Review Round 1
    (epic_dir / f"{slug}.en.md").write_text(
        "# Epic: Mono Epic\n\n- **Status**: In-progress\n", encoding="utf-8"
    )
    (epic_dir / "bdd_scenarios.en.md").write_text("# BDD\n", encoding="utf-8")
    for idx in range(1, 5):
        _write_task(epic_dir, features_dir, f"task_0{idx}_part", slug, "todo")
    resume_context.record_gate_approval(repo, slug, 2, "Gate 2")
    _state_envelope.update_epic_heartbeat(
        repo,
        slug,
        stage="Stage 2: Principal Review",
        sub_step="reviewing",
        review_state={
            "kind": "principal",
            "round": 1,
            "max_rounds": 3,
            "cli": "codex",
            "model": "gpt-6.1-sol",
            "phase": "reviewing",
        },
        last_event="Principal Review Round 1/3: codex reviewing",
    )
    meta2 = check_tasks.scan_repo(repo)
    assert meta2.pipeline_telemetry is not None
    p2 = float(meta2.pipeline_telemetry["lifecycle_progress_pct"])
    t2 = float(meta2.pipeline_telemetry["task_completion_pct"])
    assert t2 == 0.0
    assert p2 > p1

    # State 3: Packaged + Gate 3 + Tasks 2/4 Done
    (epic_dir / "handoff.md").write_text("# Handoff\n", encoding="utf-8")
    resume_context.record_gate_approval(repo, slug, 3, "Gate 3")
    _write_task(epic_dir, features_dir, "task_01_part", slug, "done")
    _write_task(epic_dir, features_dir, "task_02_part", slug, "done")
    _state_envelope.update_epic_heartbeat(
        repo,
        slug,
        stage="Stage 3 Phase 2: Execution",
        active_wave=1,
        sub_step="wave_1",
        last_event="Wave 1 running",
    )
    meta3 = check_tasks.scan_repo(repo)
    assert meta3.pipeline_telemetry is not None
    p3 = float(meta3.pipeline_telemetry["lifecycle_progress_pct"])
    t3 = float(meta3.pipeline_telemetry["task_completion_pct"])
    assert t3 == 50.0
    assert p3 > p2

    # State 4: Tasks 4/4 Done + quality_check capabilities passed WITHOUT Epic Audit / BDD (capped at 87%)
    _write_task(epic_dir, features_dir, "task_03_part", slug, "done")
    _write_task(epic_dir, features_dir, "task_04_part", slug, "done")
    _state_envelope.update_quality_run(
        repo,
        run_id="qa-1",
        epic_slug=slug,
        provider="python-qa",
        capability="e2e",
        step_index=3,
        step_total=3,
        status="passed",
    )
    meta4 = check_tasks.scan_repo(repo)
    assert meta4.pipeline_telemetry is not None
    p4 = float(meta4.pipeline_telemetry["lifecycle_progress_pct"])
    t4 = float(meta4.pipeline_telemetry["task_completion_pct"])
    assert t4 == 100.0
    assert p4 == 87.0
    assert p4 > p3

    # State 5: Full Gate 4 PASS (88%) + Cross-Model Review Round 2 + post-review Gate 4 re-verification running (96%)
    resume_context.record_gate_approval(repo, slug, 4, "Gate 4 PASS")
    (epic_dir / "review_results.md").write_text(
        f"# Code Review: {slug}\n\n## Round 1\n\n- **SHA**: {sha1}\n- **CLI**: codex\n- **Model**: gpt-6.1-sol\n"
        f"- **Status**: completed\n- **Verdict**: PASS\n\n### Findings\n\nNone.\n",
        encoding="utf-8",
    )
    # Advance git HEAD to sha2 so post-review Gate 4 on sha2 is not yet passed
    (repo / "README.md").write_text("# Demo v2\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"], cwd=repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "[MONO] Post-review sweep"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    sha2 = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _state_envelope.update_quality_run(
        repo,
        run_id="qa-2",
        epic_slug=slug,
        provider="python-qa",
        capability="pycore",
        step_index=2,
        step_total=3,
        status="running",
    )
    meta5 = check_tasks.scan_repo(repo)
    assert meta5.pipeline_telemetry is not None
    p5 = float(meta5.pipeline_telemetry["lifecycle_progress_pct"])
    t5 = float(meta5.pipeline_telemetry["task_completion_pct"])
    assert t5 == 100.0
    assert p5 == 96.0
    assert p5 > p4

    # State 6: Review Converged AND Gate 4 PASS on latest HEAD SHA sha2 -> 98% Waiting Finish
    (epic_dir / "review_results.md").write_text(
        f"# Code Review: {slug}\n\n## Round 1\n\n- **SHA**: {sha2}\n- **CLI**: codex\n- **Model**: gpt-6.1-sol\n"
        f"- **Status**: completed\n- **Verdict**: PASS\n\n### Findings\n\nNone.\n",
        encoding="utf-8",
    )
    _state_envelope.update_quality_run(
        repo,
        run_id="qa-2",
        epic_slug=slug,
        provider="python-qa",
        capability="e2e",
        step_index=3,
        step_total=3,
        status="passed",
    )
    resume_context.record_gate_approval(repo, slug, 4, "Final Gate 4 PASS on sha2")
    meta6 = check_tasks.scan_repo(repo)
    assert meta6.pipeline_telemetry is not None
    p6 = float(meta6.pipeline_telemetry["lifecycle_progress_pct"])
    t6 = float(meta6.pipeline_telemetry["task_completion_pct"])
    assert t6 == 100.0
    assert p6 == 98.0
    assert p6 > p5

    # State 7: Gate 5 Done -> 100%
    resume_context.record_gate_approval(repo, slug, 5, "Gate 5 Finish")
    (epic_dir / f"{slug}.en.md").write_text(
        "# Epic: Mono Epic\n\n- **Status**: Done\n", encoding="utf-8"
    )
    meta7 = check_tasks.build_epic_pipeline_telemetry(
        repo,
        slug,
        done_tasks=4,
        total_tasks=4,
        is_completed=True,
    )
    p7 = float(meta7["lifecycle_progress_pct"])
    t7 = float(meta7["task_completion_pct"])
    assert t7 == 100.0
    assert p7 == 100.0
    assert p1 < p2 < p3 < p4 < p5 < p6 < p7 == 100.0


def _worker_emit_event(args: tuple[str, str, str]) -> None:
    repo_str, slug, msg = args
    repo_p = Path(repo_str)
    _state_envelope.update_epic_heartbeat(
        repo_p,
        slug,
        stage="Stage 3",
        sub_step="wave_1",
        last_event=msg,
        extra_devtool_dirs=[repo_p / ".worktrees" / slug / ".devtool"],
    )


# [LTSP-AR-01] Multi-process concurrent heartbeat event updates preserve all distinct events under flock
def test_ltsp_ar_01_multiprocess_concurrent_heartbeat_events(tmp_path: Path) -> None:
    """LTSP-AR-01: Multi-process concurrent heartbeat event updates preserve all distinct events under flock."""
    repo = tmp_path / "repo_ar01"
    _init_git_repo(repo)
    wt = repo / ".worktrees" / "conc_epic"
    (wt / ".devtool" / "state").mkdir(parents=True, exist_ok=True)
    (repo / ".devtool" / "state").mkdir(parents=True, exist_ok=True)

    ctx = multiprocessing.get_context("spawn")
    payloads = [(str(repo), "conc_epic", f"worker-event-{idx}") for idx in range(1, 5)]
    with ctx.Pool(4) as pool:
        pool.map(_worker_emit_event, payloads)

    root_hb = json.loads(
        (repo / ".devtool" / "state" / "conc_epic.heartbeat.json").read_text(
            encoding="utf-8"
        )
    )
    wt_hb = json.loads(
        (wt / ".devtool" / "state" / "conc_epic.heartbeat.json").read_text(
            encoding="utf-8"
        )
    )
    assert root_hb["generation"] == wt_hb["generation"]
    assert root_hb["events"] == wt_hb["events"]
    messages = {entry["message"] for entry in root_hb["events"]}
    assert messages == {
        "worker-event-1",
        "worker-event-2",
        "worker-event-3",
        "worker-event-4",
    }


def test_ltsp_review_edge_cases_sha_validation_and_builder_signature(
    tmp_path: Path,
) -> None:
    """Verify Gate 4 SHA strict matching, truncated CHANGES REQUIRED non-convergence, and builder signature."""
    repo = tmp_path / "repo_edges"
    sha1 = _init_git_repo(repo)
    slug = "edge_epic"
    epic_dir = repo / ".devtool" / "epic" / slug
    features_dir = repo / ".devtool" / "features"
    epic_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(1, 5):
        _write_task(epic_dir, features_dir, f"task_0{idx}_edge", slug, "done")

    # 1. Signature accepts frozen HLD kwargs (task_progress, decision, quality_runs)
    tp = check_tasks.TaskProgress(
        total_tasks=4,
        done_tasks=4,
        in_progress_tasks=0,
        todo_tasks=0,
        task_completion_pct=100.0,
    )
    dec = check_tasks.LifecycleDecision(
        stage_name="Stage 3 Phase 4 (Review)",
        gate_status="Pending",
        prompt="Review",
        is_human_action_required=False,
    )
    tel_sig = check_tasks.build_epic_pipeline_telemetry(
        repo,
        slug,
        task_progress=tp,
        decision=dec,
        heartbeat={},
        quality_active={},
        quality_runs=[],
    )
    assert tel_sig["task_completion_pct"] == 100.0

    # 2. Failed audit_epic or empty review_results.md must not promote 87% QA-only to 88%
    (epic_dir / "review_results.md").write_text("", encoding="utf-8")
    tel_fail_audit = check_tasks.build_epic_pipeline_telemetry(
        repo,
        slug,
        done_tasks=4,
        total_tasks=4,
        heartbeat={
            "sub_step": "audit_epic",
            "sub_step_detail": "audit_epic: FAIL",
            "last_event": "audit_epic -> FAIL",
        },
        quality_active={"status": "passed", "step_index": 3, "step_total": 3},
    )
    assert tel_fail_audit["lifecycle_progress_pct"] == 87.0

    # 3. Truncated finding table under CHANGES REQUIRED must NOT be marked converged
    (epic_dir / "review_results.md").write_text(
        f"## Round 1\n- **Status**: completed\n- **SHA**: {sha1}\n- **Verdict**: CHANGES REQUIRED\n"
        "| F1 | Important\n",
        encoding="utf-8",
    )
    rev_trunc = check_tasks._parse_review_rounds_summary(
        epic_dir / "review_results.md",
        sha1,
        {"review_state": {"kind": "code", "round": "broken"}},
        None,
        "code",
    )
    assert rev_trunc["converged"] is False

    # 4. Stale Gate 4 commit SHA or failed quality_active must NOT allow 98% Stage 6 Finish
    (repo / "README.md").write_text("# v2\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"], cwd=repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "[EDGE] Advance HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    # Record Gate 4 on older sha1 manually via ledger
    ledger_dir = repo / ".devtool" / "state"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    (ledger_dir / "gate_ledger.jsonl").write_text(
        json.dumps(
            {
                "epic": slug,
                "gate": 4,
                "commit": sha1,
                "timestamp": "2026-11-14T00:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    tel_stale_g4 = check_tasks.build_epic_pipeline_telemetry(
        repo,
        slug,
        done_tasks=4,
        total_tasks=4,
        heartbeat={"review_state": {"kind": "code", "round": 1, "phase": "converged"}},
        quality_active={},
    )
    assert tel_stale_g4["lifecycle_progress_pct"] < 98.0
    assert tel_stale_g4["current_stage_index"] == 5
