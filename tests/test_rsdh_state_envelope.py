"""Tests for atomic runtime state envelope and mechanical Two-Tier Memory sync.

Covers BDD Scenarios:
- RSDH-HP-01: Atomic runtime state envelope syncs worktree, primary repo, and Two-Tier Memory
- RSDH-EC-01: Envelope reader tolerates missing, empty, or truncated state JSON without failing
- RSDH-AR-01: Canonical transaction lock serializes interleaved slot RMW updates and versioned mirrors
- RSDH-FR-01: Stale heartbeat metadata never blocks subsequent task status synchronization
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType
from typing import Any
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
RESUME_CONTEXT_SCRIPT = REPO_ROOT / "scripts" / "resume_context.py"
SYNC_TASK_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "dev-implementation"
    / "resources"
    / "scripts"
    / "sync_task_status.py"
)


def _import_envelope() -> ModuleType:
    """Import scripts/_state_envelope lazily inside test functions for TDD RED."""
    scripts_dir = REPO_ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import _state_envelope

    return _state_envelope


def _import_resume_context() -> ModuleType:
    """Import scripts/resume_context lazily inside test functions."""
    scripts_dir = REPO_ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import resume_context

    return resume_context


def _git(cwd: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _init_git_repo_with_worktree(
    tmp_path: Path,
    *,
    epic_dir: str = "demo_sync",
    epic_slug: str = "demo-sync",
    task_id: str = "task_01_demo",
) -> tuple[Path, Path]:
    """Create a real git repository and an isolated epic worktree with Kanban fixtures."""
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test Engineer")
    _git(repo, "config", "user.email", "test@example.com")

    epic_path = repo / ".devtool" / "epic" / epic_dir
    features_path = repo / ".devtool" / "features"
    epic_path.mkdir(parents=True, exist_ok=True)
    features_path.mkdir(parents=True, exist_ok=True)

    (epic_path / f"{epic_dir}.en.md").write_text(
        f"# Demo Epic\n\n- **Epic**: `{epic_slug}`\n- **Status**: Stage 3\n",
        encoding="utf-8",
    )
    (epic_path / f"{epic_dir}.vi.md").write_text(
        f"# Epic Demo\n\n- **Epic**: `{epic_slug}`\n- **Trạng thái**: Giai đoạn 3\n",
        encoding="utf-8",
    )
    task_content = (
        "---\n"
        f'id: "{task_id}"\n'
        'status: "todo"\n'
        f'epic: "{epic_slug}"\n'
        'modified: "2026-11-12T00:00:00Z"\n'
        "completedAt: null\n"
        "---\n\n"
        f"# {task_id}\n"
    )
    (epic_path / f"{task_id}.md").write_text(task_content, encoding="utf-8")
    (features_path / f"{task_id}.md").write_text(task_content, encoding="utf-8")

    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Initial epic fixture")

    wt = repo / ".worktrees" / epic_dir
    _git(repo, "worktree", "add", "-q", str(wt), "-b", f"epic/{epic_slug}", "main")
    return repo, wt


def _parallel_slot_worker(args: tuple[str, str, int]) -> dict[str, Any]:
    """Top-level picklable worker executing a concurrent slot RMW transaction."""
    target_path_str, epic_slug, idx = args
    scripts_dir = REPO_ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import _state_envelope

    return _state_envelope.update_epic_heartbeat(
        Path(target_path_str),
        epic_slug,
        slots={
            f"slot_{idx}": {
                "task_id": f"task_{idx:02d}",
                "status": "working",
                "worker": idx,
            }
        },
        last_event=f"worker {idx} claimed slot_{idx}",
    )


def _find_dead_pid() -> int:
    """Return a high PID guaranteed not to exist on the local machine."""
    candidate = 400_000
    while candidate < 4_000_000:
        try:
            os.kill(candidate, 0)
        except ProcessLookupError:
            return candidate
        except PermissionError:
            candidate += 1
            continue
        candidate += 1
    return 999_999


def _verify_rsdh_hp_01(tmp_path: Path) -> None:
    """Execute RSDH-HP-01 end-to-end dual-root envelope and Two-Tier Memory sync."""
    env = _import_envelope()
    repo, wt = _init_git_repo_with_worktree(tmp_path)

    shared = env.resolve_shared_devtool_dirs(wt)
    assert shared == [(repo / ".devtool").resolve(), (wt / ".devtool").resolve()]
    assert env.resolve_shared_devtool_dirs(repo) == [(repo / ".devtool").resolve()]

    env.record_pending_decision(
        wt,
        "demo-sync",
        "Confirm Gate 3 wave order",
        kind="gate_3_choice",
        decision_id="dec-demo-1",
    )
    env.record_pending_decision(
        wt,
        "sibling-epic",
        "Keep sibling paused",
        kind="gate_2_choice",
        decision_id="dec-sib-1",
    )

    replace_targets: list[Path] = []
    real_replace = os.replace

    def spying_replace(src: Any, dst: Any) -> None:
        replace_targets.append(Path(dst).resolve())
        real_replace(src, dst)

    with patch("os.replace", side_effect=spying_replace):
        hb = env.update_epic_heartbeat(
            wt,
            "demo-sync",
            stage="Stage 3 Phase 2 (TDD)",
            active_wave=1,
            active_tasks=["task_01_demo"],
            last_event="wave 1 started",
        )

    primary_hb = (repo / ".devtool" / "state" / "demo-sync.heartbeat.json").resolve()
    wt_hb = (wt / ".devtool" / "state" / "demo-sync.heartbeat.json").resolve()
    assert primary_hb in replace_targets
    assert wt_hb in replace_targets
    assert hb["generation"] == 1

    sync_res = subprocess.run(
        [sys.executable, str(SYNC_TASK_SCRIPT), "task", "task_01_demo", "in-progress"],
        cwd=wt,
        capture_output=True,
        text=True,
        check=False,
    )
    assert sync_res.returncode == 0, (
        f"stderr: {sync_res.stderr}\nstdout: {sync_res.stdout}"
    )

    primary_hb_data = json.loads(primary_hb.read_text(encoding="utf-8"))
    wt_hb_data = json.loads(wt_hb.read_text(encoding="utf-8"))
    assert primary_hb_data == wt_hb_data
    assert primary_hb_data["generation"] >= 2
    assert "task_01_demo" in primary_hb_data["active_tasks"]
    assert primary_hb_data["active_wave"] == 1
    assert "in-progress" in primary_hb_data["last_event"]

    for base in (repo, wt):
        state_md = base / ".devtool" / "state" / "demo-sync.md"
        rollup_md = base / ".devtool" / "assistant_state.md"
        assert state_md.is_file(), f"Missing {state_md}"
        assert rollup_md.is_file(), f"Missing {rollup_md}"
        state_text = state_md.read_text(encoding="utf-8")
        rollup_text = rollup_md.read_text(encoding="utf-8")
        assert "Active Epic: demo-sync" in state_text
        assert "in-progress" in state_text.lower()
        assert "Updated:" in state_text
        assert "Active Epic: demo-sync" in rollup_text

    # Ownership-scoped clear removes demo-sync decision without clearing sibling-epic
    pdec = json.loads(
        (repo / ".devtool" / "state" / "pending_decision.json").read_text(
            encoding="utf-8"
        )
    )
    assert "demo-sync" not in pdec.get("decisions", {})
    assert "sibling-epic" in pdec.get("decisions", {})
    assert pdec["active"] is True
    assert pdec["epic"] == "sibling-epic"


def test_rsdh_hp_01_dual_root_envelope_and_sync(tmp_path: Path) -> None:
    """[RSDH-HP-01] [Tier C - Integration] Atomic runtime state envelope syncs worktree, primary repo, and Two-Tier Memory."""
    _verify_rsdh_hp_01(tmp_path)


def test_rsdh_ec_01_corrupt_and_missing_state_fallback(tmp_path: Path) -> None:
    """[RSDH-EC-01] [Tier A - Unit] Envelope reader tolerates missing, empty, or truncated state JSON without failing."""
    env = _import_envelope()
    broken = tmp_path / ".devtool" / "state" / "broken.heartbeat.json"
    default_payload: dict[str, Any] = {
        "schema_version": 1,
        "generation": 0,
        "slots": {},
    }

    # Nonexistent file
    res_missing = env.read_json_safe(broken, default_payload)
    assert res_missing == default_payload
    res_missing["slots"]["mutated"] = True
    assert default_payload["slots"] == {}

    # Zero-byte file
    broken.parent.mkdir(parents=True, exist_ok=True)
    broken.write_text("", encoding="utf-8")
    assert env.read_json_safe(broken, default_payload) == default_payload

    # Truncated malformed JSON
    broken.write_text('{"schema_version": 1, "generation": ', encoding="utf-8")
    assert env.read_json_safe(broken, default_payload) == default_payload

    # Wrong JSON root type when default expects dict
    broken.write_text("[1, 2, 3]", encoding="utf-8")
    assert env.read_json_safe(broken, default_payload) == default_payload


class TestStateEnvelope_Integration:
    """Integration runner suite verifying Tier C git-worktree and concurrency scenarios."""

    def test_rsdh_hp_01_dual_root_envelope_and_sync(self, tmp_path: Path) -> None:
        """[RSDH-HP-01] [Tier C - Integration] Dual-root envelope and Two-Tier Memory sync integration check."""
        _verify_rsdh_hp_01(tmp_path)

    def test_rsdh_ar_01_canonical_transaction_flock_and_mirrors(
        self, tmp_path: Path
    ) -> None:
        """[RSDH-AR-01] [Tier C - Integration] Canonical transaction lock serializes interleaved slot RMW updates and versioned mirrors."""
        _import_envelope()
        repo, wt = _init_git_repo_with_worktree(
            tmp_path,
            epic_dir="demo_ar",
            epic_slug="demo-ar",
            task_id="task_01_ar",
        )

        jobs: list[tuple[str, str, int]] = []
        for idx in range(16):
            target = str(wt if idx % 2 == 0 else repo)
            jobs.append((target, "demo-ar", idx))

        with ProcessPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(_parallel_slot_worker, jobs))

        assert len(results) == 16
        assert sorted(r["generation"] for r in results) == list(range(1, 17))

        primary_data = json.loads(
            (repo / ".devtool" / "state" / "demo-ar.heartbeat.json").read_text(
                encoding="utf-8"
            )
        )
        wt_data = json.loads(
            (wt / ".devtool" / "state" / "demo-ar.heartbeat.json").read_text(
                encoding="utf-8"
            )
        )
        assert primary_data == wt_data
        assert primary_data["generation"] == 16
        assert set(primary_data["slots"].keys()) == {f"slot_{i}" for i in range(16)}

    def test_rsdh_fr_01_stale_heartbeat_recovery(self, tmp_path: Path) -> None:
        """[RSDH-FR-01] [Tier C - Integration] Stale heartbeat metadata never blocks subsequent task status synchronization."""
        _import_envelope()
        repo, wt = _init_git_repo_with_worktree(
            tmp_path,
            epic_dir="demo_recovery",
            epic_slug="demo-recovery",
            task_id="task_01_recover",
        )

        stale_payload = {
            "schema_version": 1,
            "generation": 7,
            "epic_slug": "demo-recovery",
            "stage": "aborted wave",
            "active_wave": 9,
            "active_tasks": ["ghost_task"],
            "slots": {
                "1": {
                    "task_id": "ghost_task",
                    "path": str(tmp_path / "missing-slot-dir"),
                    "status": "working",
                }
            },
            "last_event": "aborted wave 9",
            "updated_at": "2025-01-01T00:00:00+00:00",
        }
        for base in (repo, wt):
            hb_path = base / ".devtool" / "state" / "demo-recovery.heartbeat.json"
            hb_path.parent.mkdir(parents=True, exist_ok=True)
            hb_path.write_text(json.dumps(stale_payload), encoding="utf-8")

        sync_res = subprocess.run(
            [
                sys.executable,
                str(SYNC_TASK_SCRIPT),
                "task",
                "task_01_recover",
                "in-progress",
            ],
            cwd=wt,
            capture_output=True,
            text=True,
            check=False,
        )
        assert sync_res.returncode == 0, f"stderr: {sync_res.stderr}"

        primary_hb = json.loads(
            (repo / ".devtool" / "state" / "demo-recovery.heartbeat.json").read_text(
                encoding="utf-8"
            )
        )
        wt_hb = json.loads(
            (wt / ".devtool" / "state" / "demo-recovery.heartbeat.json").read_text(
                encoding="utf-8"
            )
        )
        assert primary_hb == wt_hb
        assert primary_hb["generation"] == 8
        assert primary_hb["active_tasks"] == ["task_01_recover"]
        assert not primary_hb["updated_at"].startswith("2025-01-01")

        rc_env = os.environ.copy()
        rc_env["WORKSPACE_ROOT"] = str(tmp_path)
        rc_res = subprocess.run(
            [
                sys.executable,
                str(RESUME_CONTEXT_SCRIPT),
                "--state",
                "--epic",
                "demo-recovery",
                "--decisions",
                "Recovered from aborted wave",
                "--status",
                "Stage 3 Phase 2 (TDD)",
                "--next",
                "Verify task_01_recover",
            ],
            cwd=wt,
            env=rc_env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert rc_res.returncode == 0, f"stderr: {rc_res.stderr}"

        after_rc = json.loads(
            (repo / ".devtool" / "state" / "demo-recovery.heartbeat.json").read_text(
                encoding="utf-8"
            )
        )
        assert after_rc["generation"] == 9
        assert after_rc["stage"] == "Stage 3 Phase 2 (TDD)"
        assert (
            json.loads(
                (wt / ".devtool" / "state" / "demo-recovery.heartbeat.json").read_text(
                    encoding="utf-8"
                )
            )
            == after_rc
        )


def test_rsdh_state_envelope_namespaced_pending_decision_isolation(
    tmp_path: Path,
) -> None:
    """Verify multi-epic pending_decision namespacing and decision_id ownership guards."""
    env = _import_envelope()
    repo, wt = _init_git_repo_with_worktree(tmp_path)

    env.record_pending_decision(
        wt,
        "epic-a",
        "Approve Gate 1",
        kind="gate_1_spec",
        decision_id="dec-a",
        stage="Stage 1",
    )
    env.record_pending_decision(
        wt,
        "epic-b",
        "Approve Gate 2",
        kind="gate_2_choice",
        decision_id="dec-b",
        stage="Stage 2",
    )

    # Wrong decision_id must NOT clear epic-b
    after_mismatch = env.clear_pending_decision(wt, "epic-b", decision_id="wrong-id")
    assert "epic-b" in after_mismatch["decisions"]
    assert "epic-a" in after_mismatch["decisions"]

    # Matching decision_id clears only epic-b
    after_clear_b = env.clear_pending_decision(wt, "epic-b", decision_id="dec-b")
    assert "epic-b" not in after_clear_b["decisions"]
    assert "epic-a" in after_clear_b["decisions"]
    assert after_clear_b["active"] is True
    assert after_clear_b["epic"] == "epic-a"
    assert after_clear_b["decision_id"] == "dec-a"

    # Clearing epic-a leaves empty decisions and inactive compatibility summary
    after_clear_a = env.clear_pending_decision(wt, "epic-a")
    assert after_clear_a["decisions"] == {}
    assert after_clear_a["active"] is False
    assert after_clear_a["epic"] is None
    assert after_clear_a["decision_id"] is None

    primary_pdec = json.loads(
        (repo / ".devtool" / "state" / "pending_decision.json").read_text(
            encoding="utf-8"
        )
    )
    wt_pdec = json.loads(
        (wt / ".devtool" / "state" / "pending_decision.json").read_text(
            encoding="utf-8"
        )
    )
    assert primary_pdec == wt_pdec


def test_rsdh_state_envelope_quality_active_isolation_and_stale_expiry(
    tmp_path: Path,
) -> None:
    """Verify runs[run_id] isolation and local dead-PID / overdue TTL expiry to stale."""
    env = _import_envelope()
    repo, wt = _init_git_repo_with_worktree(tmp_path)

    now = datetime.now(timezone.utc)
    fresh_iso = now.isoformat(timespec="seconds")
    expired_iso = (now - timedelta(seconds=600)).isoformat(timespec="seconds")
    dead_pid = _find_dead_pid()

    env.update_quality_run(
        wt,
        "run-live",
        epic_slug="demo-sync",
        profile="epic",
        status="running",
        provider="python-qa",
        capability="test",
        step_index=1,
        step_total=3,
        pid=os.getpid(),
        ttl_sec=300,
        started_at=fresh_iso,
        updated_at=fresh_iso,
    )
    env.update_quality_run(
        repo,
        "run-dead-pid",
        epic_slug="demo-sync",
        profile="pr",
        status="running",
        provider="python-qa",
        capability="lint",
        pid=dead_pid,
        ttl_sec=300,
        started_at=fresh_iso,
        updated_at=fresh_iso,
    )
    env.update_quality_run(
        wt,
        "run-expired-ttl",
        epic_slug="other-epic",
        profile="full",
        status="running",
        provider="python-qa",
        capability="type_check",
        pid=os.getpid(),
        ttl_sec=60,
        started_at=expired_iso,
        updated_at=expired_iso,
    )
    env.update_quality_run(
        wt,
        "run-remote-live",
        epic_slug="other-epic",
        profile="pr",
        status="running",
        provider="python-qa",
        capability="format",
        pid=dead_pid,
        host="remote-worker.example.invalid",
        ttl_sec=300,
        started_at=fresh_iso,
        updated_at=fresh_iso,
    )

    runs = env.read_quality_runs(repo, now_ts=now)
    assert runs["run-live"]["status"] == "running"
    assert runs["run-remote-live"]["status"] == "running"
    assert runs["run-dead-pid"]["status"] == "stale"
    assert runs["run-expired-ttl"]["status"] == "stale"

    # Finalizing one run preserves sibling live runs
    env.update_quality_run(wt, "run-live", status="passed", elapsed_sec=12.5)
    runs_after = env.read_quality_runs(wt, now_ts=now)
    assert runs_after["run-live"]["status"] == "passed"
    assert runs_after["run-live"]["finished_at"] is not None
    assert runs_after["run-remote-live"]["status"] == "running"


def test_rsdh_state_envelope_stale_lower_generation_rejected(tmp_path: Path) -> None:
    """Verify run_state_transaction rejects stale lower-generation overwrites cleanly."""
    import pytest

    env = _import_envelope()
    repo, wt = _init_git_repo_with_worktree(tmp_path)

    for step in range(3):
        state = env.run_state_transaction(
            wt,
            "custom.json",
            lambda data, s=step: {**data, "step": s},
            default={"generation": 0},
        )
    assert state["generation"] == 3

    with pytest.raises(ValueError, match="generation"):
        env.run_state_transaction(
            wt,
            "custom.json",
            lambda _data: {"generation": 1, "step": 999},
            default={"generation": 0},
        )

    primary_custom = json.loads(
        (repo / ".devtool" / "state" / "custom.json").read_text(encoding="utf-8")
    )
    wt_custom = json.loads(
        (wt / ".devtool" / "state" / "custom.json").read_text(encoding="utf-8")
    )
    assert primary_custom["generation"] == 3
    assert primary_custom["step"] == 2
    assert wt_custom == primary_custom


def test_rsdh_state_envelope_resume_context_complete_cleanup_no_duplicate_ledger(
    tmp_path: Path,
) -> None:
    """Verify complete_feature_and_rotate archives state+heartbeat across primary+worktree without duplicating PROJECT_LEDGER.md."""
    env = _import_envelope()
    rc = _import_resume_context()
    repo, wt = _init_git_repo_with_worktree(tmp_path)

    rc.write_epic_state(
        wt,
        "demo-sync",
        decisions="- Locked decision",
        status="Stage 3 done",
        next_step="Complete epic",
    )
    assert (repo / ".devtool" / "state" / "demo-sync.heartbeat.json").is_file()
    assert (wt / ".devtool" / "state" / "demo-sync.heartbeat.json").is_file()
    assert (repo / ".devtool" / "state" / "demo-sync.md").is_file()
    assert (wt / ".devtool" / "state" / "demo-sync.md").is_file()

    env.record_pending_decision(wt, "demo-sync", "Final sign-off")

    rc.complete_feature_and_rotate(wt, "demo-sync", "Shipped dual-root sync")
    rc.complete_feature_and_rotate(repo, "demo-sync", "Shipped dual-root sync")

    ledger_text = (repo / ".devtool" / "PROJECT_LEDGER.md").read_text(encoding="utf-8")
    assert ledger_text.count("`demo-sync`**:") == 1

    for base in (repo, wt):
        assert not (base / ".devtool" / "state" / "demo-sync.md").exists()
        assert not (base / ".devtool" / "state" / "demo-sync.heartbeat.json").exists()
        rollup = (base / ".devtool" / "assistant_state.md").read_text(encoding="utf-8")
        assert "Active Epic: demo-sync" not in rollup

    pdec = json.loads(
        (repo / ".devtool" / "state" / "pending_decision.json").read_text(
            encoding="utf-8"
        )
    )
    assert "demo-sync" not in pdec.get("decisions", {})


def test_rsdh_state_envelope_sync_epic_and_decision_clear(tmp_path: Path) -> None:
    """Verify sync_task_status epic command refreshes heartbeat, Two-Tier Memory, and epic-scoped pending decision."""
    env = _import_envelope()
    repo, wt = _init_git_repo_with_worktree(tmp_path)

    env.record_pending_decision(
        wt, "demo-sync", "Resume Stage 3", decision_id="dec-demo"
    )
    env.record_pending_decision(
        wt, "other-epic", "Keep waiting", decision_id="dec-other"
    )

    res = subprocess.run(
        [sys.executable, str(SYNC_TASK_SCRIPT), "epic", "demo_sync", "In Progress"],
        cwd=wt,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"stderr: {res.stderr}"

    for base in (repo, wt):
        hb = json.loads(
            (base / ".devtool" / "state" / "demo-sync.heartbeat.json").read_text(
                encoding="utf-8"
            )
        )
        assert hb["stage"] == "In Progress"
        assert "sync_epic" in hb["last_event"]
        assert "Active Epic: demo-sync" in (
            base / ".devtool" / "state" / "demo-sync.md"
        ).read_text(encoding="utf-8")
        assert "Active Epic: demo-sync" in (
            base / ".devtool" / "assistant_state.md"
        ).read_text(encoding="utf-8")

    pdec = json.loads(
        (repo / ".devtool" / "state" / "pending_decision.json").read_text(
            encoding="utf-8"
        )
    )
    assert "demo-sync" not in pdec.get("decisions", {})
    assert "other-epic" in pdec.get("decisions", {})


def test_round1_concurrent_multiroot_write_epic_state_stays_consistent(
    tmp_path: Path,
) -> None:
    """Concurrent multi-root write_epic_state invocations keep markdown, rollups, and heartbeat synchronized."""
    repo, wt = _init_git_repo_with_worktree(tmp_path)

    procs: list[subprocess.Popen[str]] = []
    for idx in range(6):
        cwd = wt if idx % 2 == 0 else repo
        label = f"Stage 3 Worker {idx}"
        procs.append(
            subprocess.Popen(
                [
                    sys.executable,
                    str(RESUME_CONTEXT_SCRIPT),
                    "--epic",
                    "demo-sync",
                    "--state",
                    "--role",
                    "programmer",
                    "--status",
                    label,
                    "--next",
                    f"step-{idx}",
                ],
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        )

    for proc in procs:
        stdout, stderr = proc.communicate(timeout=20)
        assert proc.returncode == 0, f"stdout={stdout}\nstderr={stderr}"

    repo_md = (repo / ".devtool" / "state" / "demo-sync.md").read_text(encoding="utf-8")
    wt_md = (wt / ".devtool" / "state" / "demo-sync.md").read_text(encoding="utf-8")
    assert repo_md == wt_md

    repo_rollup = (repo / ".devtool" / "assistant_state.md").read_text(encoding="utf-8")
    wt_rollup = (wt / ".devtool" / "assistant_state.md").read_text(encoding="utf-8")
    assert repo_rollup == wt_rollup

    repo_hb = json.loads(
        (repo / ".devtool" / "state" / "demo-sync.heartbeat.json").read_text(
            encoding="utf-8"
        )
    )
    wt_hb = json.loads(
        (wt / ".devtool" / "state" / "demo-sync.heartbeat.json").read_text(
            encoding="utf-8"
        )
    )
    assert repo_hb == wt_hb
    assert repo_hb["generation"] == 6
    assert repo_hb["stage"] in repo_md
