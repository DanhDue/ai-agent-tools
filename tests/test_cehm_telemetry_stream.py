"""Unit and concurrency tests for append-only event stream and dual-variant archival.

Covers BDD Scenarios:
- CEHM-HP-01: Untruncated append-only event stream records over 20 steps and archives dual hyphen-underscore heartbeats
- CEHM-AR-01: Concurrent update_epic_heartbeat callers write valid non-interleaved lines to events JSONL under transactional lock
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
RESUME_CONTEXT_SCRIPT = REPO_ROOT / "scripts" / "resume_context.py"


def _load_state_envelope() -> ModuleType:
    """Import `scripts/_state_envelope.py` dynamically without polluting top-level sys.path."""
    scripts_dir = str(REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    if "_state_envelope" in sys.modules:
        return sys.modules["_state_envelope"]
    module_path = REPO_ROOT / "scripts" / "_state_envelope.py"
    spec = importlib.util.spec_from_file_location("_state_envelope", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_state_envelope"] = module
    spec.loader.exec_module(module)
    return module


def _git(cwd: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _init_git_repo(tmp_path: Path, name: str = "repo") -> Path:
    """Create an isolated git repository inside `tmp_path`."""
    repo = tmp_path / name
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test Engineer")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / ".devtool" / "state").mkdir(parents=True, exist_ok=True)
    (repo / ".devtool" / "logs").mkdir(parents=True, exist_ok=True)
    (repo / "README.md").write_text("# test\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Initial fixture")
    return repo


def _isolated_env(tmp_path: Path) -> dict[str, str]:
    """Build subprocess environment isolated from host HOME and live profile stores."""
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["HOME"] = str(fake_home)
    env["WORKSPACE_ROOT"] = str(tmp_path)
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env.pop("AGY_PROFILE", None)
    return env


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return [json.loads(ln) for ln in lines]


def test_cehm_hp_01_append_only_events_and_dual_archival(tmp_path: Path) -> None:
    """[CEHM-HP-01] [Tier A - Unit] Untruncated append-only event stream records over 20 steps and archives dual hyphen-underscore heartbeats."""
    env_mod = _load_state_envelope()
    repo = _init_git_repo(tmp_path)

    for i in range(1, 26):
        env_mod.update_epic_heartbeat(
            repo,
            "alpha-epic",
            stage="Stage 3: Implementation",
            sub_step="task_run",
            sub_step_detail=f"Step {i:02d}",
            last_event=f"step-{i:02d}",
            updated_at=f"2026-11-15T01:{i:02d}:00+00:00",
            max_events=20,
        )

    hyphen_hb_path = repo / ".devtool" / "state" / "alpha-epic.heartbeat.json"
    assert hyphen_hb_path.is_file()
    hb_data = json.loads(hyphen_hb_path.read_text(encoding="utf-8"))
    assert len(hb_data["events"]) <= 20
    assert len(hb_data["events"]) == 20
    assert hb_data["events"][0]["message"] == "step-06"
    assert hb_data["events"][-1]["message"] == "step-25"

    stream_path = repo / ".devtool" / "logs" / "events_alpha-epic.jsonl"
    assert stream_path.is_file(), f"Missing append-only stream at {stream_path}"
    pre_records = _read_jsonl(stream_path)
    assert [r["message"] for r in pre_records] == [
        f"step-{i:02d}" for i in range(1, 26)
    ]
    for record in pre_records:
        assert {
            "ts",
            "stage",
            "sub_step",
            "sub_step_detail",
            "message",
            "review_state",
        } <= set(record.keys())

    # Simulate legacy/split underscore heartbeat & activity files coexisting in .devtool/
    underscore_hb_path = repo / ".devtool" / "state" / "alpha_epic.heartbeat.json"
    underscore_hb_path.write_text(
        json.dumps({"schema_version": 1, "generation": 1, "epic_slug": "alpha_epic"})
        + "\n",
        encoding="utf-8",
    )
    (repo / ".devtool" / "state" / "alpha-epic.md").write_text(
        "# Active Epic: alpha-epic\n", encoding="utf-8"
    )
    (repo / ".devtool" / "logs" / "activity_alpha_epic.log").write_text(
        "[2026-11-15] [repo/alpha_epic/task_01] Completed\n", encoding="utf-8"
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(RESUME_CONTEXT_SCRIPT),
            "--complete",
            "alpha_epic",
            "Completed alpha",
        ],
        cwd=repo,
        env=_isolated_env(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"

    archive_dir = repo / ".devtool" / "archive"
    archived_streams = sorted(archive_dir.glob("events_alpha-epic_*.jsonl"))
    assert len(archived_streams) == 1, (
        f"Expected archived events jsonl in {list(archive_dir.iterdir())}"
    )
    archived_records = _read_jsonl(archived_streams[0])
    assert [r["message"] for r in archived_records] == [
        f"step-{i:02d}" for i in range(1, 26)
    ]

    assert len(list(archive_dir.glob("heartbeat_alpha-epic_*.json"))) == 1
    assert len(list(archive_dir.glob("heartbeat_alpha_epic_*.json"))) == 1
    assert len(list(archive_dir.glob("activity_alpha_epic_*.log"))) == 1
    assert len(list(archive_dir.glob("state_alpha-epic_*.md"))) == 1

    # Zero orphan state/log files for either slug variant
    assert not hyphen_hb_path.exists()
    assert not underscore_hb_path.exists()
    assert not (repo / ".devtool" / "state" / "alpha-epic.md").exists()
    assert not stream_path.exists()
    assert not (repo / ".devtool" / "logs" / "activity_alpha_epic.log").exists()

    ledger_text = (repo / ".devtool" / "PROJECT_LEDGER.md").read_text(encoding="utf-8")
    assert "`alpha_epic`**: Completed alpha" in ledger_text


def test_cehm_ar_01_concurrent_events_jsonl_writes(tmp_path: Path) -> None:
    """[CEHM-AR-01] [Tier A - Unit] Concurrent update_epic_heartbeat callers write valid non-interleaved lines to events JSONL under transactional lock."""
    env_mod = _load_state_envelope()
    repo = _init_git_repo(tmp_path)

    wt = repo / ".worktrees" / "concurrent_epic"
    _git(repo, "worktree", "add", "-q", str(wt), "-b", "epic/concurrent_epic", "main")
    (wt / ".devtool" / "state").mkdir(parents=True, exist_ok=True)
    (wt / ".devtool" / "logs").mkdir(parents=True, exist_ok=True)
    assert (wt / ".devtool" / "state").is_dir()

    num_threads = 6
    iters_per_thread = 8
    barrier = threading.Barrier(num_threads)
    expected_events = {
        f"worker-{tid:02d}-step-{step:02d}"
        for tid in range(num_threads)
        for step in range(iters_per_thread)
    }

    def _worker(tid: int) -> None:
        barrier.wait(timeout=10)
        for step in range(iters_per_thread):
            target = wt if (tid + step) % 2 == 0 else repo
            env_mod.update_epic_heartbeat(
                target,
                "concurrent-epic",
                stage="Stage 3: Parallel",
                sub_step="worker_tick",
                sub_step_detail=f"worker {tid} iter {step}",
                last_event=f"worker-{tid:02d}-step-{step:02d}",
            )

    with ThreadPoolExecutor(max_workers=num_threads) as pool:
        futures = [pool.submit(_worker, tid) for tid in range(num_threads)]
        for fut in futures:
            fut.result()

    for base in (repo, wt):
        stream_path = base / ".devtool" / "logs" / "events_concurrent-epic.jsonl"
        assert stream_path.is_file(), f"Missing stream mirror at {stream_path}"
        raw_lines = [
            ln
            for ln in stream_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        assert len(raw_lines) == 48
        parsed = [json.loads(ln) for ln in raw_lines]
        messages = {item["message"] for item in parsed}
        assert messages == expected_events


def test_cehm_idle_tick_deduplication_and_transition_logging(tmp_path: Path) -> None:
    """Consecutive identical idle ticks update snapshot ts in-place without duplicating JSONL, while transitions append."""
    env_mod = _load_state_envelope()
    repo = _init_git_repo(tmp_path)

    # Initial event + consecutive idle ticks with identical last_event & unchanged state
    timestamps = [f"2026-11-15T02:00:0{i}+00:00" for i in range(1, 5)]
    for ts in timestamps:
        env_mod.update_epic_heartbeat(
            repo,
            "idle_epic",
            stage="Stage 3",
            sub_step="coding",
            review_state={"kind": "code", "round": 1, "phase": "reviewing"},
            last_event="wave 1 polling",
            updated_at=ts,
        )

    hb_path = repo / ".devtool" / "state" / "idle_epic.heartbeat.json"
    stream_path = repo / ".devtool" / "logs" / "events_idle_epic.jsonl"
    hb = json.loads(hb_path.read_text(encoding="utf-8"))
    assert len(hb["events"]) == 1
    assert hb["events"][0]["ts"] == timestamps[-1]
    assert hb["updated_at"] == timestamps[-1]

    records = _read_jsonl(stream_path)
    assert len(records) == 1
    assert records[0]["message"] == "wave 1 polling"
    assert records[0]["review_state"] == {
        "kind": "code",
        "round": 1,
        "phase": "reviewing",
    }

    # Changing review_state phase with identical last_event must record a transition
    env_mod.update_epic_heartbeat(
        repo,
        "idle_epic",
        stage="Stage 3",
        sub_step="coding",
        review_state={
            "kind": "code",
            "round": 1,
            "phase": "triage",
            "action": "AUTO_FIX_ELIGIBLE",
        },
        last_event="wave 1 polling",
        updated_at="2026-11-15T02:01:00+00:00",
    )
    records = _read_jsonl(stream_path)
    assert len(records) == 2
    assert records[1]["review_state"]["phase"] == "triage"

    # Repeating the exact same phase & message must NOT append
    env_mod.update_epic_heartbeat(
        repo,
        "idle_epic",
        stage="Stage 3",
        sub_step="coding",
        review_state={
            "kind": "code",
            "round": 1,
            "phase": "triage",
            "action": "AUTO_FIX_ELIGIBLE",
        },
        last_event="wave 1 polling",
        updated_at="2026-11-15T02:02:00+00:00",
    )
    assert len(_read_jsonl(stream_path)) == 2

    # Stage change without last_event still records a transition
    env_mod.update_epic_heartbeat(
        repo,
        "idle_epic",
        stage="Stage 4: Finish",
        updated_at="2026-11-15T02:03:00+00:00",
    )
    records = _read_jsonl(stream_path)
    assert len(records) == 3
    assert records[2]["stage"] == "Stage 4: Finish"

    # Distinct event followed by non-consecutive return to an earlier message appends both
    env_mod.update_epic_heartbeat(
        repo,
        "idle_epic",
        last_event="stage 4 active",
        updated_at="2026-11-15T02:04:00+00:00",
    )
    env_mod.update_epic_heartbeat(
        repo,
        "idle_epic",
        last_event="wave 1 polling",
        updated_at="2026-11-15T02:05:00+00:00",
    )
    assert len(_read_jsonl(stream_path)) == 5

    # Read-only logs directory never crashes heartbeat persistence
    logs_dir = repo / ".devtool" / "logs"
    logs_dir.chmod(0o555)
    try:
        updated = env_mod.update_epic_heartbeat(
            repo,
            "idle_epic",
            last_event="after readonly logs",
            updated_at="2026-11-15T02:05:00+00:00",
        )
        assert updated["last_event"] == "after readonly logs"
    finally:
        logs_dir.chmod(0o755)


def test_cehm_complete_archives_worktree_and_reverse_slug_variants(
    tmp_path: Path,
) -> None:
    """Completing with hyphen slug archives underscore heartbeat and events JSONL across root and worktree."""
    env_mod = _load_state_envelope()
    repo = _init_git_repo(tmp_path)
    wt = repo / ".worktrees" / "beta_epic"
    _git(repo, "worktree", "add", "-q", str(wt), "-b", "epic/beta_epic", "main")

    env_mod.update_epic_heartbeat(
        wt, "beta_epic", stage="Stage 3", last_event="wt-step-1"
    )
    env_mod.update_epic_heartbeat(
        wt, "beta_epic", stage="Stage 3", last_event="wt-step-2"
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(RESUME_CONTEXT_SCRIPT),
            "--complete",
            "beta-epic",
            "Completed beta across worktree",
        ],
        cwd=wt,
        env=_isolated_env(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"

    for base in (repo, wt):
        assert not (base / ".devtool" / "state" / "beta_epic.heartbeat.json").exists()
        assert not (base / ".devtool" / "state" / "beta-epic.heartbeat.json").exists()
        assert not (base / ".devtool" / "logs" / "events_beta_epic.jsonl").exists()
        assert not (base / ".devtool" / "logs" / "events_beta-epic.jsonl").exists()
        archive_dir = base / ".devtool" / "archive"
        archived_streams = list(archive_dir.glob("events_beta_epic_*.jsonl"))
        assert len(archived_streams) == 1
        assert [r["message"] for r in _read_jsonl(archived_streams[0])] == [
            "wt-step-1",
            "wt-step-2",
        ]
        assert len(list(archive_dir.glob("heartbeat_beta_epic_*.json"))) == 1
